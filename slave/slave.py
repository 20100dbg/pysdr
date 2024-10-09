import sx126x
import sys
import time
from rtlsdr import RtlSdr


def send(addr, frq):
    global lora
    addr = addr.to_bytes(1, 'big')
    frq = frq.to_bytes(4)

    lora.sendraw(addr + frq)

def arr_abs(arr):
    return [abs(x) for x in arr]

def arr_mean(arr):
    return sum(arr) / len(arr)

def arr_pow(arr, p):
    return [x ** p for x in arr]


def main():

    global addr_local
    addr_local = int(sys.argv[1])

    global lora
    lora = sx126x.sx126x(channel=18,address=addr_local,network=0, txPower='22', airDataRate='9.6', packetSize='32')


    frq = 449300

    global sdr
    sdr = RtlSdr()
    sdr.sample_rate = 2.048e6 # Hz
    sdr.center_freq = frq * 1000   # Hz
    sdr.freq_correction = 60  # PPM
    sdr.gain = 'auto'

    threshold = 1
    lastAlert = 0
    timeout = 5
    avg_pwr = 0

    while True:
        x = sdr.read_samples(4096)

        #avec numpy
        #avg_pwr = np.mean(np.abs(x)**2)
        avg_pwr = arr_mean(arr_pow(arr_abs(x),2))
        print("\r", avg_pwr,  end='')

        currentTime = time.time()

        if avg_pwr > threshold:

            if currentTime > lastAlert + timeout:
                print("send alert")
                send(addr_local, frq)
                lastAlert = currentTime

        time.sleep(0.1)

    sdr.close()


if __name__ == '__main__':
    
    if len(sys.argv) != 2:
        print('Usage :', sys.argv[0], "<local address>")
    else:
        main()
