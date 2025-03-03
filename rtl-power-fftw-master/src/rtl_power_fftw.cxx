/*
* rtl_power_fftw, program for calculating power spectrum from rtl-sdr reciever.
* Copyright (C) 2015 Klemen Blokar <klemen.blokar@ad-vega.si>
*                    Andrej Lajovic <andrej.lajovic@ad-vega.si>
*
*                    Additions by: Mario Cannistra <mariocannistra@gmail.com>
*                                 (added -e param for session duration)
*                                 (added -q flag to limit verbosity)
*                                 (added -m param to produce binary matrix output
*                                                 with separate metadata file)
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
#include <iostream>
#include <fstream>
#include <rtl-sdr.h>

#include "acquisition.h"
#include "datastore.h"
#include "device.h"
#include "exceptions.h"
#include "interrupts.h"
#include "params.h"
#include "metadata.h"

#include <time.h>

std::ofstream binfile, metafile;
int metaRows = 1;
int metaCols = 0;
float avgScanDur = 0.0;
float sumScanDur = 0.0;
time_t scanEnd, scanBeg;
int tunfreq;
int startFreq, endFreq, stepFreq;
std::string firstAcqTimestamp, lastAcqTimestamp;
int cntTimeStamps;

int main(int argc, char **argv)
{
  bool do_exit = false;

  ReturnValue final_retval = ReturnValue::Success;

  try {
    // Parse command line arguments.
    Params params(argc, argv);

    params.endless = true;
    params.repeats = 64;

    // Set up RTL-SDR device.
    Rtlsdr rtldev(params.dev_index);

    // Print the available gains and select the one nearest to the requested gain.
    //rtldev.print_gains();
    int gain = rtldev.nearest_gain(params.gain);
    rtldev.set_gain(gain);

    // Temporarily set the frequency to params.cfreq, just so that the device does not
    // complain upon setting the sample rate. If this fails, it's not a big deal:
    // the sample rate will be read out just fine, but librtlsdr _might_ print an
    // error message to stderr.
    try {
      rtldev.set_frequency(params.cfreq);
    }
    catch (RPFexception&) {}

    // Set frequency correction
    if (params.ppm_error != 0) {
      rtldev.set_freq_correction(params.ppm_error);
    }

    // Set sample rate
    rtldev.set_sample_rate(params.sample_rate);
    int actual_samplerate = rtldev.sample_rate();

    // Create a plan of the operation. This will calculate the number of repeats,
    // adjust the buffer size for optimal performance and create a list of frequency
    // hops.
    Plan plan(params, actual_samplerate);

    //Begin the work: prepare data buffers
    Datastore data(params); //, auxData.window_values);

    set_CtrlC_handler(true);

    std::cout << "!start scanning..." << std::endl;

    params.finalfreq = plan.freqs_to_tune.back();

    //Read from device and do FFT
    do {
      for (auto iter = plan.freqs_to_tune.begin(); iter != plan.freqs_to_tune.end();) {
        // Begin a new data acquisition.
        Acquisition acquisition(params, rtldev, data, actual_samplerate, *iter);
        try {
          // Read the required amount of data and process it.
          acquisition.run();
          iter++;
        }
        catch (TuneError &e) {
          // The receiver was unable to tune to this frequency. It might be just a "dead"
          // spot of the receiver. Remove this frequency from the list and continue.
          std::cerr << "Unable to tune to " << e.frequency() << ". Dropping from frequency list." << std::endl;
          iter = plan.freqs_to_tune.erase(iter);
          continue;
        }

        // Write the gathered data to stdout.
        acquisition.write_data();

        // Check for interrupts.
        if (checkInterrupt(InterruptState::FinishNow))
          break;
      }

      if(params.endless) do_exit = false;   // exactly ! will force to never exit

      // unless you hit ctrl-c :
      if(checkInterrupt(InterruptState::FinishPass)) do_exit = true;

    } while ( !do_exit );

    std::cout << "Ended scan" << std::endl;

  }
  catch (RPFexception &exception) {
    std::cerr << exception.what() << std::endl;
    final_retval = exception.returnValue();
  }

  return (int)final_retval;
}
