/*
* rtl_power_fftw, program for calculating power spectrum from rtl-sdr reciever.
* Copyright (C) 2015 Klemen Blokar <klemen.blokar@ad-vega.si>
*                    Andrej Lajovic <andrej.lajovic@ad-vega.si>
*
* This program is free software: you can redistribute it and/or modify
* it under the terms of the GNU General Public License as published by
* the Free Software Foundation, either version 3 of the License, or
* (at your option) any later version.
*
* This program is distributed in the hope that it will be useful,
* but WITHOUT ANY WARRANTY; without even the implied warranty of
* MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
* GNU General Public License for more details.
*
* You should have received a copy of the GNU General Public License
* along with this program. If not, see <http://www.gnu.org/licenses/>.
*/

#include <chrono>
#include <fstream>
#include <iomanip>
#include <iostream>
#include <thread>

#include "acquisition.h"
#include "datastore.h"
#include "device.h"
#include "interrupts.h"
#include "metadata.h"

template <typename T>
std::vector<T> read_inputfile(std::istream* stream) {
  // Parse baseline input line by line.
  std::vector<T> values;
  std::string line;
  while (std::getline(*stream, line)) {
    std::istringstream lineStream(line);

    if ((lineStream >> std::ws).peek() == '#') {
      // Commented lines don't count.
      continue;
    }
    // The strategy is: we read as much doubles from the line as we can,
    // and use the last one. Accomodates one column, two columns (the first
    // one being, for example, frequency), three columns, N columns;
    // anything goes.
    T value;
    unsigned int valuesRead = 0;
    while (lineStream >> value)
      valuesRead++;

    // We are being very relaxed here. No doubles in the line? Skip it.
    // As long as we end up with the right number of values, we're game.
    if (valuesRead > 0)
      values.push_back(value);
  }
  return values;
}


Plan::Plan(Params& params_, int actual_samplerate_) :
  actual_samplerate(actual_samplerate_), params(params_)
{
  // Calculate the number of repeats according to the true sample rate.

  // Adjust buffer size
  if (!params.buf_length_isSet) {
    int64_t base_buf_multiplier = ceil((2.0 * params.N * params.repeats) / base_buf);
    // If less than approximately 1.6 MB of data is needed, make the buffer the
    // smallest possible while still keeping the size to a multiple of
    // base_buf. Otherwise, set it to 100 * base_buf.
    // If you know what should fit your purposes well, feel free to use the
    // command line options to override this.
    if (base_buf_multiplier <= default_buf_multiplier) {
      params.buf_length = base_buf * ((base_buf_multiplier == 0 ) ? 1 : base_buf_multiplier);
    }
  }

  // Make a plan of frequency hopping.
  // We're stuffing a vector full of frequencies that we wish to eventually tune to.
  if (params.freq_hopping_isSet) {
    double min_overhang = actual_samplerate*params.min_overlap/100;
    int hops = ceil((double(params.stopfreq - params.startfreq) - min_overhang) / (double(actual_samplerate) - min_overhang));
    if (hops > 1) {
      int overhang = (int64_t(hops)*actual_samplerate - (params.stopfreq - params.startfreq)) / (hops - 1);
      freqs_to_tune.push_back(params.startfreq + actual_samplerate/2.0);

      //Mmmm, thirsty? waah-waaah...
      for (int hop = 1; hop < hops; hop++) {
        freqs_to_tune.push_back(freqs_to_tune.back() + actual_samplerate - overhang);
      }
    }
    else
      freqs_to_tune.push_back((params.startfreq + params.stopfreq)/2);
  }
  // If there is only one hop, no problem.
  else {
    freqs_to_tune.push_back(params.cfreq);
  }
}


Acquisition::Acquisition(const Params& params_,
                         Rtlsdr& rtldev_,
                         Datastore& data_,
                         int actual_samplerate_,
                         int64_t freq_) :
  params(params_), rtldev(rtldev_), data(data_),
  actual_samplerate(actual_samplerate_), freq(freq_)
{ }


void Acquisition::run() {
  // Set center frequency.
  // There have been accounts of hardware being stubborn and refusing to
  // tune to the desired frequency on random occasions despite being able
  // to tune to that same frequency at other times. Such hiccups seem to
  // be rare. We handle them by a naive and stupid, but seemingly effective
  // method of persuasion.
  
  const int max_tune_tries = 3;
  bool success = false;
  for (int tune_try = 0; !success && tune_try < max_tune_tries; tune_try++)
  {
    try {
      rtldev.set_frequency(freq);
      tuned_freq = rtldev.frequency();
      if (tuned_freq != 0)
        success = true;
    }
    catch (const RPFexception&) {}
  }

  // Check if the frequency was actually successfully set.
  if (!success) {
    //Warning: librtlsdr does not tell you of all cases when tuner cannot lock PLL, despite clearly writing so to the stderr!
    //TODO: Fix librtlsdr.
    throw TuneError(freq);
  }

  std::fill(data.pwr.begin(), data.pwr.end(), 0);
  data.acquisition_finished = false;
  data.repeats_done = 0;

  std::thread t(&Datastore::fftThread, &data);

  std::unique_lock<std::mutex>
  status_lock(data.status_mutex, std::defer_lock);
  int64_t dataTotal = 2 * params.N * params.repeats;
  int64_t dataRead = 0;

  while (dataRead < dataTotal) {
    // Wait until a buffer is empty
    status_lock.lock();
    data.queue_histogram[data.empty_buffers.size()]++;
    while (data.empty_buffers.empty())
      data.status_change.wait(status_lock);

    Buffer& buffer(*data.empty_buffers.front());
    data.empty_buffers.pop_front();
    status_lock.unlock();

    // Figure out how much data to read.
    int64_t dataNeeded = dataTotal - dataRead;
    if (dataNeeded >= params.buf_length)
      // More than one bufferful of data needed. Leave the rest for later.
      dataNeeded = params.buf_length;
    else {
      // Less than one whole buffer needed. Round the number of (real)
      // samples upwards to the next multiple of base_buf.
      dataNeeded = base_buf * ceil((double)dataNeeded / base_buf);
      if (dataNeeded > params.buf_length) {
        // Nope, too much. We'll still have to do this in two readouts.
        dataNeeded = params.buf_length;
      }
    }

    // Resize the buffer to match the needed amount of data.
    buffer.resize(dataNeeded);

    bool read_success = rtldev.read(buffer);
    deviceReadouts++;

    if (!read_success) {
      std::cerr << "Error: dropped samples." << std::endl;
      // There is effectively no data in this buffer - consider it empty.
      status_lock.lock();
      // Push the buffer to the front of the queue because it already has
      // the correct size and we'll just pop it again on next iteration.
      data.empty_buffers.push_front(&buffer);
      status_lock.unlock();
      // No need to notify the worker thread in this case.
    }
    else {
      successfulReadouts++;
      dataRead += dataNeeded;
      status_lock.lock();
      data.occupied_buffers.push_back(&buffer);
      data.status_change.notify_all();
      status_lock.unlock();
    }

    // See if we have been instructed to conclude this measurement immediately.
    if (interrupts && checkInterrupt(InterruptState::FinishNow))
        break;
  }

  status_lock.lock();
  data.acquisition_finished = true;
  data.status_change.notify_all();
  status_lock.unlock();
  t.join();
}


void Acquisition::write_data() const {

  std::ofstream binfile;
  double pwrdb = 0.0;
  float fpwrdb = 0.0;
  double freq = 0.0;

  //Interpolate the central point, to cancel DC bias.
  data.pwr[params.N/2] = (data.pwr[params.N/2 - 1] + data.pwr[params.N/2+1]) / 2;

  for (int i = 0; i < params.N; i++) {
    freq = tuned_freq + (i - params.N/2.0) * actual_samplerate / params.N;
    if( params.linear ) {
      pwrdb = (data.pwr[i] / data.repeats_done / params.N / actual_samplerate);
    }
    else {
      pwrdb = 10*log10(data.pwr[i] / data.repeats_done / params.N / actual_samplerate);
    }

      if (pwrdb > params.threshold) {
        std::cout << "~" << freq / 1000000 << "|" << pwrdb << std::endl;
      }

  }

}

// Get current date/time, format is "YYYY-MM-DD HH:mm:ss UTC"
std::string Acquisition::currentDateTime() {
  time_t now = std::time(0);
  char buf[80];
  std::strftime(buf, sizeof(buf), "%Y-%m-%d %X UTC", std::gmtime(&now));
  return buf;
}
