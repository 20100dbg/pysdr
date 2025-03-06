import json
import os.path
import struct
import sx126x
import sys
import threading
import time
from enum import Enum
from scanner import *
from gps import VMA430

class MsgType(Enum):
    PING = 1
    FRQ = 2
    CONF_SCAN = 3
    CONF_LORA = 4
    ACK = 5
    ERROR = 6

HEADER_SIZE = 3


def clean_frq(frq, step=5):
    """ From a float mHz frequency, return a XXXYYY int, rounded, frequency  """
    
    if not isinstance(frq, float): frq = float(frq)
    reminder = frq % step

    if reminder < (step // 2): frq = frq - reminder
    else: frq = frq + (step - reminder) 
    
    #return "{0:.3f}".format(frq / 1000)
    return int(frq)


def int_to_bytes(x, bytes_count=1):
    return x.to_bytes(bytes_count, 'big')


def bytes_to_int(b):
    return int.from_bytes(b)


def build_key_history(msg):
    """ Create a dictionnary key based on header data """

    msg_type, msg_id, msg_to = extract_header(msg)
    return str(msg_to) + '-' + str(msg_id)


def extract_header(data):
    """ Extract header fields from message """
    
    return (data[0],                 #msg_type
            bytes_to_int(data[1:2]), #msg_id
            bytes_to_int(data[2:3])) #msg_to


def build_message(msg_type, msg_id, msg_to, data=b''):
    """ Create a byte array with specified header data """

    msg = b''
    msg += int_to_bytes(msg_type, 1)
    msg += int_to_bytes(msg_id, 1)
    msg += int_to_bytes(msg_to, 1)
    msg += data

    #Fill to sub_packet_size
    msg += b'\x00' * (sub_packet_size - len(msg))
    return msg


def btohex(b):
    """ Get bytes to proper hex notation """
    return ' '.join(['{:02X}'.format(x) for x in b])


def relay_message(data):
    """ Anytime we need to send back a message """

    (msg_type, msg_id, msg_to) = extract_header(data)

    #Check for duplicates
    key = build_key_history(data)

    if key not in msg_history:
        msg_history[key] = {"time": time.time()} #, "data": data}
        lora.send_bytes(data)


def increment_msg_id():
    global local_msg_id
    local_msg_id += 1
    if local_msg_id == 256:
        local_msg_id = 0


def callback_lora(data):
    """ Handles every message received from LoRa """
   
    global frq_start, frq_end, threshold
    #print(f"Received {data}")

    (msg_type, msg_id, msg_to) = extract_header(data)
    payload = data[HEADER_SIZE:]

    #Local node is not recipient, lets re-send it 
    if msg_to != local_addr and msg_to != 255:
        relay_message(data)
        return

    #Update scanner config
    if msg_type == MsgType.CONF_SCAN.value:
        
        #Update local vars
        frq_start = bytes_to_int(payload[0:2])
        frq_end = bytes_to_int(payload[2:4])
        threshold = payload[4] * -1
        
        #stop, set config, and start again scanner
        scanner.stop()
        scanner.set_config(frq_start=frq_start, frq_end=frq_end, threshold=threshold)
        scanner.activate()

        #Save config in file
        save_config()

        #Send back ACK + config
        data = int_to_bytes(frq_start, 2) + int_to_bytes(frq_end, 2) + int_to_bytes(payload[4], 1)
        lora.send_bytes(build_message(MsgType.ACK.value, msg_id, local_addr, data))

    #Update LoRa config
    elif msg_type == MsgType.CONF_LORA.value:

        #Not used right now
        channel = payload[0]
        air_data_rate = bytes_to_int(payload[1:3]) / 10

        lora.set_config(channel=channel,air_data_rate=air_data_rate)        
        lora.send_bytes(build_message(MsgType.ACK.value, msg_id, local_addr))

    elif msg_type == MsgType.PING.value:

        #receive broadcast PING (proabably from tester)
        if msg_to == 255:
            lora.send_bytes(build_message(MsgType.ACK.value, msg_id, local_addr))
        
        else:
            is_scanning = 1 if scanner.scanning else 0

            data = b''
            data += struct.pack("d", current_lat)
            data += struct.pack("d", current_lng)
            data += int_to_bytes(is_scanning, 1)
            data += int_to_bytes(frq_start, 2) 
            data += int_to_bytes(frq_end, 2)
            data += int_to_bytes(abs(threshold), 1)

            lora.send_bytes(build_message(MsgType.ACK.value, msg_id, local_addr, data))


def callback_scanner(frequency, power):
    """ Handles frequencies detection from scanner """
    frq = clean_frq(frequency, step=5)
    detection_history[frq] = {'time': time.time(), 'power': power}

    
def save_config():
    """ Save config as JSON in a file """
    config = {'frq_start': frq_start, 'frq_end': frq_end, 'threshold': threshold}
    with open('config.json', 'w') as f:
        json.dump(config, f)

    if debug:
        print(f"Save config : {frq_start} {frq_end} {threshold}")


def load_config():
    """ Load config from a file and set parameters """
    global frq_start, frq, threshold

    with open('config.json', 'r') as f:
        config = json.loads(f.read())

    frq_start = config['frq_start']
    frq_end = config['frq_end']
    threshold = config['threshold']

    if debug:
        print(f"Load config : {frq_start} {frq_end} {threshold}")



#Entry point

if len(sys.argv) != 2:
    print(f"Usage : python {sys.argv[0]} <ID CAPTEUR>")
    exit(1)

#General
debug = False

#LoRa
local_addr = int(sys.argv[1])
local_msg_id = 0
msg_history = {}
channel = 18
air_data_rate = 2.4
sub_packet_size = 32

#scanner
global frq_start, frq_end, threshold, detection_history
frq_start, frq_end, threshold = 400, 420, -10
detection_history = {} #detection_history[frq] = {'time': time.time(), 'power': power}
delay_detection = 0.1

#gps
current_lat, current_lng = 0, 0
delay_gps = 5

if os.path.isfile("config.json"):
    load_config()
else:
    save_config()

lora = sx126x.sx126x(port="/dev/ttyS0", debug=debug)
lora.set_config(channel=channel,logical_address=local_addr,network=0, tx_power=22, 
                air_data_rate=air_data_rate, sub_packet_size=sub_packet_size)
lora.listen(callback=callback_lora, expected_size=sub_packet_size)


#Scanner init
scanner = scanner(callback=callback_scanner, debug=debug)

#frq_start=400, frq_end=420, gain=49, sample_rate=2000000, ppm=0, repeats=64, threshold=-10, bins=512, dev_index=0
scanner.set_config(frq_start=frq_start, frq_end=frq_end, threshold=threshold)
scanner.activate(blocking=False)


#GPS init

gps = VMA430()
gps.begin(port="/dev/ttyAMA2", baudrate=9600, debug=debug)

last_gps = 0
gps_online = False

#Main loop, requesting GPS location
while True:

    #gps
    if time.time() - last_gps > delay_gps:
        
        #keep trying to set it online
        if not gps_online:
            gps_online = gps.setUBXNav()

        else:
            #when online, get position
            gps.getUBX_packet()

            if gps.location.latitude and gps.location.longitude:
                current_lat = gps.location.latitude
                current_lng = gps.location.longitude

                if debug:
                    print(f"lat : {current_lat} / lng {current_lng}")

        last_gps = time.time()


    #filter out detections
    frq_max, pwr_max = 0,-120

    for frq, val in detection_history.copy().items():
        if time.time() - val["time"] > delay_detection:
            if val["power"] > pwr_max:
                frq_max = frq
                pwr_max = val["power"]
            del detection_history[frq]

    #send detections
    if frq_max != 0 and pwr_max != -120:
        data = b''
        data += int_to_bytes(frq_max, 4)
        pwr = abs(int(pwr_max * 100))
        data += int_to_bytes(pwr, 2)

        print(f"sending {frq_max} / {pwr_max}")

        lora.send_bytes(build_message(MsgType.FRQ.value, local_msg_id, local_addr, data))
        increment_msg_id()

    #clean msg_history queue
    for key, val in msg_history.copy().items():
        if time.time() - val["time"] > 60: 
            del msg_history[key]

    time.sleep(delay_detection)


scanner.stop()
lora.stop()
thread_lora.join()
