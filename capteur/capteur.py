import struct
import sx126x
import sys
import threading
import time
from enum import Enum
from scanner import *



#####from gps import VMA430




class MsgType(Enum):
    PING = 1
    FRQ = 2
    CONF_SCAN = 3
    CONF_LORA = 4
    ACK = 5
    ERROR = 6

HEADER_SIZE = 3


def int_to_bytes(x, bytes_count=1):
    return x.to_bytes(bytes_count, 'big')


def bytes_to_int(b):
    return int.from_bytes(b)


def build_key_history(msg):
    """ Create a dictionnary key based on header data """

    (msg_type, msg_id, msg_from) = extract_header(msg)
    return str(msg_from) + '-' + str(msg_id)


def extract_header(data):
    """ Extract header fields from message """
    
    return (data[0],                  #msg_type
            bytes_to_int(data[1:2]),  #msg_id
            bytes_to_int(data[2:3])), #msg_from


def build_message(msg_type, msg_id, msg_from, data=b''):
    """ Create a byte array with specified header data """

    msg = b''
    msg += int_to_bytes(msg_type, 1)
    msg += int_to_bytes(msg_id, 1)
    msg += int_to_bytes(msg_from, 1)
    msg += data
    return msg


def btohex(b):
    """ Get bytes to proper hex notation """
    return ' '.join(['{:02X}'.format(x) for x in b])


def relay_message(data):
    """ Anytime we need to send back a message """

    (msg_type, msg_id, msg_from) = extract_header(data)

    #Check for duplicates
    key = build_key_history(data)

    if key not in msg_history:
        msg_history.append(key)
        lora.send_bytes(data)


def increment_msg_id():
    global local_msg_id
    local_msg_id += 1
    if local_msg_id == 256:
        local_msg_id = 0


def receive_lora():
    """ Handles every message received from LoRa """
   
    while True:
        data = lora.receive()
        #print(f"Received {data}")

        if data and len(data) >= HEADER_SIZE:
            (msg_type, msg_id, msg_from) = extract_header(data)
            payload = data[HEADER_SIZE:]

            #Local node is not recipient, lets re-send it 
            if msg_from != local_addr:
                relay_message(data)
                return

            #Update scanner config
            if msg_type == MsgType.CONF_SCAN.value:
                
                frq_start = int.from_bytes(payload[0:2])
                frq_end = int.from_bytes(data[2:4])
                threshold = int.from_bytes(data[4:5]) * -1
                
                scanner.set_config(self, frq_start=frq_start, frq_end=frq_end, threshold=threshold)

                print(f"new conf : {frq_start} - {frq_end} / {new_threshold}")
                lora.send_bytes(build_message(MsgType.ACK.value, msg_id, local_addr))

            #Update LoRa config
            elif msg_type == MsgType.CONF_LORA.value:
                #channel
                #air_data_rate
                #lora.set_config(air_data_rate=0.3)
                lora.send_bytes(build_message(MsgType.ACK.value, msg_id, local_addr))
                pass

            elif msg_type == MsgType.PING.value:
                lora.send_bytes(build_message(MsgType.ACK.value, msg_id, local_addr))

        time.sleep(0.01)


def callback_scanner(frq, pwr):
    """ Handles frequencies detection from scanner """

    print(f"got activity ! {frq} / {pwr}")

    data = b''
    data += int_to_bytes(frq, 4) 
    data += struct.pack("f", pwr)

    lora.send_bytes(build_message(MsgType.FRQ.value, local_msg_id, local_addr, data))
    increment_msg_id()


    
def save_config():
    """ [NOT USED FOR NOW] Save config as JSON in a file """
    config = {'frq_start': frq_start, 'frq_end': frq_end, 'threshold': threshold}
    with open('config.json', 'w') as f:
        json.dump(config, f)


def load_config():
    """ [NOT USED FOR NOW] Load config from a file and set parameters """
    with open('config.json', 'r') as f:
        config = json.loads(f.read())

    frq_start = config['frq_start']
    frq_end = config['frq_end']
    threshold = config['threshold']



#Entry point

if len(sys.argv) != 2:
    print(f"Usage : python {sys.argv[0]} <ID CAPTEUR>")
    exit(1)

local_addr = int(sys.argv[1])
local_msg_id = 0

#LoRa init
channel = 18
air_data_rate = 0.3


lora = sx126x.sx126x()
lora.set_config(channel=channel,logical_address=local_addr,network=0, tx_power=22, 
                air_data_rate=air_data_rate, sub_packet_size=32)

thread_lora = threading.Thread(target=receive_lora)
thread_lora.start()


frq_start, frq_end = 400*10**6, 420*10**6
current_lat, current_lng = None, None


#Scanner init
scanner = scanner(callback=callback_scanner, debug=True)

#frq_start=400, frq_end=420, gain=49, sample_rate=2000000, ppm=0, repeats=64, threshold=-10, bins=512, dev_index=0
scanner.set_config(frq_start=400, frq_end=420, threshold=-10)
scanner.activate(blocking=False)



while True:
    try:
        input()
    except KeyboardInterrupt:
        scanner.stop()
        break



"""
#GPS init
gps = VMA430()
gps.begin(9600)
gps.setUBXNav()

#Main loop, requesting GPS location
while True:

    gps.getUBX_packet()
    
    if gps.location.latitude and gps.location.longitude:
        current_lat = struct.pack("d", gps.location.latitude)
        current_lng = struct.pack("d", gps.location.longitude)

    time.sleep(5)


lora.stop()
scanner.stop()

"""