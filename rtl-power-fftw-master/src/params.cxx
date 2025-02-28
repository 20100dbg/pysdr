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

#include <iostream>
#include <list>
#include <math.h>
#include <string>
#include <tclap/CmdLine.h>

#include "params.h"
#include "exceptions.h"

int64_t parse_frequency(std::string s) {
  std::istringstream ss(s);
  double f;
  std::string multiplier;
  ss >> f >> multiplier;
  if (multiplier == "k")
    f *= 1e3;
  else if (multiplier == "M")
    f *= 1e6;
  else if (multiplier == "G")
    f *= 1e9;
  else if (multiplier != "")
    return -1;
  return (int64_t)f;
}

double parse_time(std::string s) {
  // The string should end with an unit. If no unit is present, we assume that
  // the last number is in seconds.
  std::string permitted_units = "dhms";
  if (permitted_units.find(s.back()) == std::string::npos)
    s.push_back('s');

  std::stringstream ss(s);
  double value;
  char unit;
  double t = 0;
  // We'll use these to prevent the same unit from being used twice (as it is
  // most likely a user mistake).
  bool days_consumed, hours_consumed, minutes_consumed, seconds_consumed;
  days_consumed = hours_consumed = minutes_consumed = seconds_consumed = false;

  while (ss >> value && ss.get(unit)) {
    if (unit == 'd' && !days_consumed) {
      t += value*86400;
      days_consumed = true;
    }
    else if (unit == 'h' && !hours_consumed) {
      t += value*3600;
      hours_consumed = true;
    }
    else if (unit == 'm' && !minutes_consumed) {
      t += value*60;
      minutes_consumed = true;
    }
    else if (unit == 's' && !seconds_consumed) {
      t += value;
      seconds_consumed = true;
    }
    else
      return -1;
  }

  if (ss.eof())
    return t;
  else {
    // Unconsumed input left - this indicates a parse error.
    return -1;
  }
}

template <typename T>
void ensure_positive_arg(std::list<TCLAP::ValueArg<T>*> list) {
  for (auto arg : list) {
    if (arg->isSet() && arg->getValue() < 0) {
      throw RPFexception(
        "Argument to '"  + arg->getName() + "' must be a positive number.",
        ReturnValue::InvalidArgument);
    }
  }
}

Params::Params(int argc, char** argv) {
  try {
    TCLAP::CmdLine cmd("Obtain power spectrum from RTL device using FFTW library.", ' ', "1.0-beta2");

    TCLAP::ValueArg<int> arg_rate("r","rate","Sample rate of the receiver.",false,sample_rate,"samples/s");
    cmd.add( arg_rate );
    TCLAP::ValueArg<int> arg_ppm("p","ppm","Set custom ppm error in RTL-SDR device.", false, ppm_error, "ppm");
    cmd.add( arg_ppm );
    TCLAP::ValueArg<int64_t> arg_repeats("n","repeats","Number of scans for averaging (incompatible with -t).",false,repeats,"repeats");
    cmd.add( arg_repeats );
    TCLAP::ValueArg<float> arg_gain("g","gain","Receiver gain.",false, gain, "37.2, 49.6");
    cmd.add( arg_gain );
    TCLAP::ValueArg<int> arg_threshold("t","threshold","Threshold trigger",false, threshold, "dbm");
    cmd.add( arg_threshold );
    TCLAP::ValueArg<std::string> arg_freq("f","freq","Center frequency of the receiver or frequency range to scan.",false,"","Hz | Hz:Hz");
    cmd.add( arg_freq );
    TCLAP::ValueArg<int> arg_index("d","device","RTL-SDR device index.",false,dev_index,"device index");
    cmd.add( arg_index );
    TCLAP::ValueArg<int> arg_bins("b","bins","Number of bins in FFT spectrum (must be even number)",false,N,"bins in FFT spectrum");
    cmd.add( arg_bins );

    cmd.parse(argc, argv);

    // Ain't this C++11 f**** magic? Watch this:
    ensure_positive_arg<int>({&arg_bins, &arg_rate, &arg_index});
    ensure_positive_arg<int64_t>({&arg_repeats});

    dev_index = arg_index.getValue();
    N = arg_bins.getValue();
    if (N % 2 != 0) N++;

    gain = arg_gain.getValue() * 10;
    sample_rate = arg_rate.getValue();
    threshold = arg_threshold.getValue();

    // Due to USB specifics, buffer length for reading rtl_sdr device
    // must be a multiple of 16384. We have to keep it that way.
    // For performance reasons, the actual buffer length should be in the
    // MB range.
    if (buf_length % base_buf != 0) {
      buf_length = floor((double)buf_length/base_buf + 0.5) * base_buf;
      std::cerr << "Buffer length should be multiple of " << base_buf
                << ", changing to " << buf_length << "." << std::endl;
    }

    ppm_error = arg_ppm.getValue();
    if (arg_freq.isSet()) {
      std::string a_freq = arg_freq.getValue();
      std::size_t colon_position = a_freq.find(":");
      std::istringstream opt(a_freq);
      if (colon_position != std::string::npos) {
        std::string startFreqString, stopFreqString;
        if (getline(opt, startFreqString, ':') && getline(opt, stopFreqString)) {
          startfreq = parse_frequency(startFreqString);
          stopfreq = parse_frequency(stopFreqString);
          if (startfreq < 0 || stopfreq < 0 || stopfreq < startfreq) {
            throw RPFexception(
              "Invalid frequency range given to --freq: " + a_freq + ".\n"
              + "Expecting positive numbers in ascending order, allowing the k,M,G multipliers. Exiting.",
              ReturnValue::InvalidArgument);
          }
          else {
            freq_hopping_isSet = true;
            cfreq = (startfreq + stopfreq)/2;
          }
        }
        else {
          throw RPFexception(
            "Could not parse frequency range given to --freq: " + a_freq + ".\n"
            + "Expecting form startfreq:stopfreq. Exiting.",
            ReturnValue::InvalidArgument);
        }
      }
      else {
        cfreq = parse_frequency(a_freq);
        if (cfreq < 0) {
          throw RPFexception(
            "Invalid frequency given to --freq: " + std::to_string(cfreq) + ".\n"
            + "Expecting a positive number, allowing the k,M,G multipliers. Exiting.",
            ReturnValue::InvalidArgument);
        }
      }
    }

    if (arg_repeats.isSet())
      repeats = arg_repeats.getValue();
    else
      repeats = buf_length/(2*N);
    
  }
  catch (TCLAP::ArgException &e) {
    throw RPFexception(
      "Error: " + e.error() + " for arg " + e.argId(),
      ReturnValue::TCLAPerror);
  }
}
