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

    def set_config(self, frq_start=400, frq_end=420, threshold=-10, gain=49, sample_rate=2000000, 
                            ppm=0, repeats=64, bins=512, dev_index=0):
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

        #do NOT check for exact string, these are partial error messages
        errors = ["Could not open rtl_sdr", "[R82XX] PLL not locked!", "No RTL-SDR compatible devices found.", "usb_claim_interface error"]

        cmd = [os.getcwd() + "/rtl_power_fftw", "-f", str(self.frq_start) + "M:" + str(self.frq_end) + "M", 
                "-g", str(self.gain), "-r", str(self.sample_rate), "-p", str(self.ppm), "-n", str(self.repeats), 
                "-t", str(self.threshold), "-b", str(self.bins), "-d", str(self.dev_index)]

        if self.debug:
            print(f"cmd : {' '.join(cmd)}")

        #Starting rtl_power_fftw process
        self.process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, stdin=subprocess.PIPE, text=True)

        #headers
        for _ in range(4):
            line = self.process.stdout.readline().strip()
            
            #waiting for program finish loading
            if "!start scanning" in line:
                self.scanning = True
                if self.debug:
                    print("Start scanning")

            #Check for errors
            for err in errors:
                if err in line:
                    self.log(f"[-] Error : {line}")

        if blocking:
            self.thread = None
            self.scanner()
        else:
            self.thread = threading.Thread(target=self.scanner)
            self.thread.start()

        return True


    def stop(self):
        """ Stop scanner, kill process """
        self.running = False
        self.scanning = False
        self.process.send_signal(signal.SIGINT)
        time.sleep(1)


    def log(self, data):
        with open("log", "a") as f:
            f.write(data + "\n")


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
