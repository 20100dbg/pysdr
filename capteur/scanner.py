import threading
import time
from rtlsdr import RtlSdr
import math

class scanner:

    def __init__(self, frq_start, frq_end, callback, debug=False):
        self.running = True
        self.frq_start = frq_start
        self.frq_end = frq_end
        self.new_conf = False
        self.callback = callback
        self.debug = debug


    def activate(self, blocking=False):
        """ Init RtlSdr and start scanning """
        try:
            self.sdr = RtlSdr()
        except Exception as e:
            return False

        if blocking:
            self.thread = None
            self.scanner()
        else:
            self.thread = threading.Thread(target=self.scanner)
            self.thread.start()
        return True


    def set_threshold(self, threshold):
        self.threshold = threshold


    def set_frq(self, frq_start, frq_end):
        self.frq_start = frq_start * 10**6
        self.frq_end = frq_end * 10**6
        self.new_conf = True

    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

    def arr_abs(self, arr):
        return [abs(x) for x in arr]

    def arr_mean(self, arr):
        return sum(arr) / len(arr)

    def arr_pow(self, arr, p):
        return [x ** p for x in arr]

    def get_frq_power(self, sdr, frq):
        """ compute average power from a sample """

        self.sdr.center_freq = frq # Hz
        x = self.sdr.read_samples(self.nb_samples)
        x = self.arr_mean(self.arr_pow(self.arr_abs(x),2))
        x = 10*math.log10(x)
        return x


    def pretty_frq(self, frq):
        """ return frequency in XXX.YYYM format """
        strfrq = str(frq/1000000)
        strfrq = strfrq.ljust(7, '0')
        return strfrq + 'M'


    def scan_zone(self, frq_start, frq_end, hop_width):
        """ Scan a given a range and return highest power found """
        max_frq = 0
        max_pwr = 0

        frq = frq_start
        while frq <= frq_end:

            avg_pwr = self.get_frq_power(self.sdr, frq)

            if avg_pwr > max_pwr:
                max_frq = frq
                max_pwr = avg_pwr
            frq += hop_width

        return (max_frq, max_pwr)


    def scanner(self):
        """ Main loop """
        x = 0

        self.frq_start = 400*10**6
        self.frq_end = 440*10**6


        self.nb_samples = 1024 * 4
        self.sdr.bandwith = 12.5e3 #0 = auto
        #self.sdr.sample_rate = 2.048e6 # Hz
        self.sdr.sample_rate = 3.2e6 # Hz
        self.sdr.freq_correction = 60  # PPM
        self.sdr.gain = 49.6

        self.threshold = 0.8
        frq = self.frq_start

        #smaller hops = slower and more precise
        #bigger hops = faster and less precise
        hop_width = 800 * 1000 

        while self.running:

            avg_pwr = self.get_frq_power(self.sdr, frq)

            if self.debug:
                print(f"\rScanning {self.pretty_frq(frq)} {avg_pwr}", end='')

            if avg_pwr >= self.threshold:

                frq_start_detection = frq

                #trying to get a more precise frequency
                (max_frq, max_pwr) = self.scan_zone(frq - 1_000_000, frq, 200_000)
                (max_frq, max_pwr) = self.scan_zone(max_frq - 100_000, max_frq + 25_000, 25_000)

                if self.debug:
                    print(f"\nFound activity on {self.pretty_frq(max_frq)} / start {frq_start_detection}")
                
                self.callback(max_frq)

                #Hop one more time to avoid another detection too close 
                frq += hop_width

            frq += hop_width

            if self.new_conf:
                frq = self.frq_start
                self.new_conf = False

            if frq > self.frq_end:
                frq = self.frq_start

        self.sdr.close()

