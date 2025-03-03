import os
import signal
import subprocess
import threading
import time

class scanner:

    def __init__(self, callback, debug=False):
        self.callback = callback
        self.debug = debug
        self.process = None

        #default conf is applied
        self.set_config()

    def set_config(self, frq_start=400, frq_end=420, gain=49, sample_rate=2000000, ppm=0, 
                            repeats=64, threshold=-10, bins=512, dev_index=0):
        """ Set scanner parameters. Needs to re-activate in order to apply changes """
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
        """ Init rtlsdr and start rtl_power_fftw process """
        self.running = True
        self.scanning = False

        #Starting rtl_power_fftw process
        
        #do NOT check for exact string
        errors = ["Could not open rtl_sdr", "[R82XX] PLL not locked!", "No RTL-SDR compatible devices found.", "usb_claim_interface error"]

        cmd = [os.getcwd() + "/rtl_power_fftw", "-f", str(self.frq_start) + "M:" + str(self.frq_end) + "M", 
                "-g", str(self.gain), "-r", str(self.sample_rate), "-p", str(self.ppm), "-n", str(self.repeats), 
                "-t", str(self.threshold), "-b", str(self.bins), "-d", str(self.dev_index)]

        print(f"cmd : {' '.join(cmd)}")

        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True)

        #headers
        for _ in range(4):
            line = self.process.stdout.readline().strip()
            print(line)
            if "!start scanning" in line:
                self.scanning = True

                if self.debug:
                    print("Start scanning")


            for err in errors:
                if err in line:
                    msg = f"[-] Error : {line}"
                    self.log(msg)

        if blocking:
            self.thread = None
            self.scanner()
        else:
            self.thread = threading.Thread(target=self.scanner)
            self.thread.start()

        return True


    def stop(self):
        self.running = False
        self.scanning = False
        self.process.send_signal(signal.SIGINT)
        time.sleep(1)


    def log(self, data):
        with open("log", "a") as f:
            f.write(data + "\n")


    def clean_frq(self, frq, step=5):
        if not isinstance(frq, float): frq = float(frq)
        frq = frq * 1000
        reminder = frq % step

        if reminder < (step // 2): frq = frq - reminder
        else: frq = frq + (step - reminder) 
        
        return "{0:.3f}".format(frq / 1000)


    def clean_frq(self, frq):
        if not isinstance(frq, float): frq = float(frq)
        frq = frq * 1000
        reminder = frq % step

        if reminder < (step // 2): frq = frq - reminder
        else: frq = frq + (step - reminder) 
        
        return "{0:.3f}".format(frq / 1000)


    def scanner(self):

        while self.running:
            try:
                data = self.process.stdout.readline().strip()
            except KeyboardInterrupt:
                break
            
            if data:
                if self.debug:
                    print(data)

                if data[0] == "~":
                    frq, pwr = data[1:].split("|")
                    frq = int(float(frq) * 1000)
                    pwr = float(pwr)
                    self.callback(frq, pwr)
                else:
                    self.log(data)
