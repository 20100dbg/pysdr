import signal
import subprocess
import threading
import time

class scanner:

    def __init__(self, callback, debug=False):
        self.callback = callback
        self.debug = debug

        #default conf
        self.set_config()

    def set_config(self, frq_start=400, frq_end=420, gain=49, sample_rate=2000000, ppm=0, 
                            repeats=64, threshold=-10, bins=512, dev_index=0):
        self.frq_start = frq_start
        self.frq_end = frq_end
        self.gain = gain
        self.sample_rate = sample_rate
        self.ppm = ppm
        self.repeats = repeats
        self.threshold = threshold
        self.bins = bins
        self.dev_index = dev_index


    def activate(self, blocking=False):
        self.running = True

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


def log(self, data):
    with open("log", "a") as f:
        f.write(data)


def clean_frq(self, frq, step=5):
    if not isinstance(frq, float): frq = float(frq)
    frq = frq * 1000
    reminder = frq % step

    if reminder < (step // 2): frq = frq - reminder
    else: frq = frq + (step - reminder) 
    
    return "{0:.3f}".format(frq / 1000)


def scanner(self):

    errors = ["Could not open rtl_sdr device"]

    cmd = ["/home/rpi/scanner/build/rtl_power_fftw", "-f", str(self.frq_start) + "M:" + str(self.frq_end) + "M", 
            "-g", str(self.gain), "-r", str(self.sample_rate), "-p", str(self.ppm), "-n", str(self.repeats), 
            "-t", str(self.threshold), "-b", str(self.bins), "-d", str(self.dev_index)]

    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True)

    #headers
    for x in range(4):
        data = p.stdout.readline().strip()

    while True:

        try:
            data = p.stdout.readline().strip()
        except KeyboardInterrupt:
            print("Quitting...")
            break
        
        if data:
            if data[0] == "~":
                frq, pwr = data[1:].split("|")
                print(self.clean_frq(frq), pwr)
            else:
                self.log(data)

    p.send_signal(signal.SIGINT)
    time.sleep(1)
