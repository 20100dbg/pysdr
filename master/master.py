import sx126x
import time
import RPi.GPIO as GPIO
from signal import signal, SIGINT

def handler(signal_received, frame):
    GPIO.cleanup()
    exit(0)

def activer_relais(on):
    global pin_relais    
    GPIO.output(pin_relais, on)

def listener():

    timeout = 3
    lastAlert = 0

    while True:
        currentTime = time.time()
        data = lora.receive()

        if data and len(data) == 5:
            print(data)
            addr = int.from_bytes(data[0:1])
            frq = int.from_bytes(data[1:5])

            print(f'From {addr}, frq : {frq}')

            activer_relais(True)
            lastAlert = currentTime

        if currentTime > lastAlert + timeout:
            activer_relais(False)

        time.sleep(0.01)


def main():
    signal(SIGINT, handler)
    
    global pin_relais
    pin_relais = 17

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(pin_relais, GPIO.OUT, initial=GPIO.LOW)

    #initialize lora
    global lora

    lora = sx126x.sx126x(channel=18,address=254,network=0, txPower='22', airDataRate='9.6', packetSize='32')
    listener()


if __name__ == '__main__':
    main()
