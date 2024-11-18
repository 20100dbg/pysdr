import sx126x
import threading
import time

class lora:

    def __init__(self, channel, address, callback):
        self.running = True
        self.thread = threading.Thread(target=self.receive)
        self.channel = channel
        self.address = address
        self.callback = callback

    def receive(self):
        while self.running:
            data = self.mylora.receive()
            if data:
                self.callback(data)

            time.sleep(0.01)

    def send(self, msg):
        self.mylora.sendraw(msg)
 

    def activate(self):
        self.mylora = sx126x.sx126x(channel=self.channel,address=self.address,network=0, txPower='22', airDataRate='9.6', packetSize='32')
        self.thread.start()

    def stop(self):
        self.running = False
        self.thread.join()

