import time
from rtlsdr import RtlSdr
from signal import signal, SIGINT

def arr_abs(arr):
    return [abs(x) for x in arr]

def arr_mean(arr):
    return sum(arr) / len(arr)

def arr_pow(arr, p):
    return [x ** p for x in arr]

def handler(signal_received, frame):
    global running
    print("\n\nCaught Ctrl+C, stopping...")
    running = False

def get_frq_power(sdr, frq, nb_samples):    
    sdr.center_freq = frq # Hz
    x = sdr.read_samples(nb_samples)
    return arr_mean(arr_pow(arr_abs(x),2))

def pretty_frq(frq):
    strfrq = str(frq/1000000)
    strfrq = strfrq.ljust(7, '0')
    return strfrq + 'M'

signal(SIGINT, handler)

frq_start = 400*1000*1000
frq_end = 430*1000*1000

global running
running = True

global sdr
sdr = RtlSdr()

nb_samples = 1024 * 4
sdr.bandwith = 0 #0 = auto
sdr.sample_rate = 2.048e6 # Hz
sdr.freq_correction = 30  # PPM
sdr.gain = 48

threshold = 0.9
frq = frq_start
frq_start_detection = 0
hop_width = 500000

while True:
    if not running:
        break

    avg_pwr = get_frq_power(sdr, frq, nb_samples)
    print(f"\rScanning {pretty_frq(sdr.center_freq)} {avg_pwr}", end='')
    
    if avg_pwr >= threshold:
    
        if frq_start_detection == 0:
            frq -= 250000
            frq_start_detection = sdr.center_freq
            old_hop_width = hop_width
            hop_width = 25000
            max_pwr = 0
            max_frq = 0
        
        if avg_pwr > max_pwr:
            max_pwr = avg_pwr
            max_frq = sdr.center_freq
    
    elif frq_start_detection != 0:
        print(f"\nFound activity on {pretty_frq(max_frq)} / start {frq_start_detection}")
        frq_start_detection = 0
        hop_width = old_hop_width
    
    #elif frq_start_detection != 0:

    frq += hop_width

    if frq > frq_end:
        frq = frq_start

sdr.close()