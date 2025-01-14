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
        self.mylora.send_bytes(msg)
 

    def activate(self, blocking=False):
        self.mylora = sx126x.sx126x(channel=self.channel,address=self.address,network=0, tx_power=22, air_data_rate=9.6, sub_packet_size=32)

        if blocking:
            self.receive()
        else:
            self.thread = threading.Thread(target=self.receive)
            self.thread.start()


    def stop(self):
        self.running = False
        self.thread.join()

