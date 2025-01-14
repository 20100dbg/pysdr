import threading
import time
from rtlsdr import RtlSdr

class scanner:

    def __init__(self, frq_start, frq_end, callback, debug=False):
        self.running = True
        self.frq_start = frq_start
        self.frq_end = frq_end
        self.new_conf = False
        self.callback = callback
        self.debug = debug


    def activate(self, blocking=False):
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
        self.sdr.center_freq = frq # Hz
        x = self.sdr.read_samples(self.nb_samples)
        return self.arr_mean(self.arr_pow(self.arr_abs(x),2))


    def pretty_frq(self, frq):
        strfrq = str(frq/1000000)
        strfrq = strfrq.ljust(7, '0')
        return strfrq + 'M'


    def scan_zone(self, frq_start, frq_end, hop_width):

        max_frq = 0
        max_pwr = 0

        frq = frq_start
        while frq <= frq_end:

            avg_pwr = self.get_frq_power(self.sdr, frq)

            #if self.debug:
            #    print(f"\rScanning {self.pretty_frq(frq)} {avg_pwr}", end='')

            if avg_pwr > max_pwr:
                max_frq = frq
                max_pwr = avg_pwr
            frq += hop_width

        return (max_frq, max_pwr)


    def scanner(self):
        x = 0

        self.frq_start = 400*10**6
        self.frq_end = 440*10**6


        self.nb_samples = 1024 * 4
        self.sdr.bandwith = 12.5e3 #0 = auto
        self.sdr.sample_rate = 2.048e6 # Hz
        self.sdr.freq_correction = 60  # PPM
        self.sdr.gain = 49

        self.threshold = 0.8
        frq = self.frq_start
        hop_width = 800 * 1000 #meilleur compromis vitesse / précision

        time_start_loop = time.time()
        time_start_detection = time.time()

        while self.running:

            avg_pwr = self.get_frq_power(self.sdr, frq)

            if self.debug:
                print(f"\rScanning {self.pretty_frq(frq)} {avg_pwr}", end='')

            if avg_pwr >= self.threshold:

                time_start_detection = time.time()
                frq_start_detection = frq

                #nouvelle detection
                (max_frq, max_pwr) = self.scan_zone(frq - 1_000_000, frq, 200_000)
                #if self.debug:
                #    print(f"\nIntermediate : {self.pretty_frq(max_frq)}")
                (max_frq, max_pwr) = self.scan_zone(max_frq - 100_000, max_frq + 25_000, 25_000)

                if self.debug:
                    print(f"\nFound activity on {self.pretty_frq(max_frq)} / start {frq_start_detection} (in {time.time() - time_start_detection}s)")
                #self.callback(max_frq)

                frq += hop_width #distance de sécurité pour éviter une double détection

            frq += hop_width

            if self.new_conf:
                frq = self.frq_start
                #print("Set up new frq_start / frq_end")
                self.new_conf = False

            if frq > self.frq_end:
                frq = self.frq_start
                print(f"Time to loop : {time.time() - time_start_loop}")
                time_start_loop = time.time()

        self.sdr.close()

