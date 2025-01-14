import threading
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

    def get_frq_power(self, sdr, frq, nb_samples):    
        self.sdr.center_freq = frq # Hz
        x = self.sdr.read_samples(nb_samples)
        return self.arr_mean(self.arr_pow(self.arr_abs(x),2))


    def pretty_frq(self, frq):
        strfrq = str(frq/1000000)
        strfrq = strfrq.ljust(7, '0')
        return strfrq + 'M'


    def scanner(self):
        x = 0
        
        nb_samples = 1024 * 4
        self.sdr.bandwith = 12.5e3 #0 = auto
        self.sdr.sample_rate = 2.048e6 # Hz
        self.sdr.freq_correction = 60  # PPM
        self.sdr.gain = 49

        self.threshold = 1
        frq = self.frq_start
        frq_start_detection = 0
        hop_width = 500 * 1000
        original_hop_width = hop_width
        max_hop_detection = 5

        while self.running:

            avg_pwr = self.get_frq_power(self.sdr, frq, nb_samples)
            
            if self.debug:
                print(f"\rScanning {self.pretty_frq(self.sdr.center_freq)} {avg_pwr}", end='')
            
            if avg_pwr >= self.threshold:
            
                #nouvelle detection
                if frq_start_detection == 0:
                    frq -= 200000
                    frq_start_detection = self.sdr.center_freq
                    hop_width = 50000
                    max_pwr = 0
                    max_frq = 0
                    hop_detection = 0
                
                if avg_pwr > max_pwr:
                    max_pwr = avg_pwr
                    max_frq = self.sdr.center_freq
                    hop_detection += 1

                if hop_detection >= max_hop_detection:

                    if self.debug:
                        print(f"\nFound activity on {self.pretty_frq(max_frq)} / start {frq_start_detection}")
                    self.callback(max_frq)
                    
                    hop_width = original_hop_width
                    frq = frq_start_detection + original_hop_width
                    frq_start_detection = 0
            
            #fin de detection/recherche
            elif frq_start_detection != 0:
                
                if self.debug:
                    print(f"\nFound activity on {self.pretty_frq(max_frq)} / start {frq_start_detection}")
                self.callback(max_frq)

                frq_start_detection = 0
                hop_width = original_hop_width
            
            frq += hop_width

            if self.new_conf:
                frq = self.frq_start
                #print("Set up new frq_start / frq_end")
                self.new_conf = False

            if frq > self.frq_end:
                frq = self.frq_start

        self.sdr.close()

