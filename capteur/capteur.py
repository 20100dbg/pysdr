import sys
from lora import *
from scanner import *
from enum import Enum
from gps import VMA430
import struct


class MsgType(Enum):
    PING = 1
    FRQ = 2
    CONF = 3
    ACK = 4
    ERROR = 5

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
    
    return (data[0], #msg_type
            bytes_to_int(data[1:2]), #msg_id
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
    payload = data[HEADER_SIZE:]

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



def callback_lora(data):
    """ Handles every message received from LoRa """

    #print(f"Received {data}")

    if len(data) >= HEADER_SIZE:
        (msg_type, msg_id, msg_from) = extract_header(data)
        payload = data[HEADER_SIZE:]

        #Local node is not recipient, lets re-send it 
        if msg_from != local_addr:
            relay_message(data)
            return

        #New scanner conf received
        if msg_type == MsgType.CONF.value and len(payload) == 5:
            
            frq_start = int.from_bytes(payload[0:2])
            frq_end = int.from_bytes(data[2:4])
            threshold = int.from_bytes(data[4:5]) * -1
            
            scanner.set_threshold(new_threshold)
            scanner.set_frq(frq_start, frq_end)

            print(f"new conf : {frq_start} - {frq_end} / {new_threshold}")
            lora.send_bytes(build_message(MsgType.ACK.value, msg_id, local_addr))


        #PING received
        elif msg_type == MsgType.PING.value:

            lora.send_bytes(build_message(MsgType.ACK.value, msg_id, local_addr))



def callback_scanner(frq):
    """ Handles frequencies detection from scanner """

    data = int_to_bytes(frq, 4)
    lora.send_bytes(build_message(MsgType.FRQ.value, local_msg_id, local_addr, data))
    increment_msg_id()


    
def save_config():
    """ Save config as JSON in a file """
    config = {'frq_start': frq_start, 'frq_end': frq_end, 'threshold': threshold}
    with open('config.json', 'w') as f:
        json.dump(config, f)


def load_config():
    """ Load config from a file and set parameters """
    with open('config.json', 'r') as f:
        config = json.loads(f.read())

    frq_start = config['frq_start']
    frq_end = config['frq_end']
    threshold = config['threshold']
    scanner.set_threshold(new_threshold)
    scanner.set_frq(frq_start, frq_end)


#Entry point

if len(sys.argv) != 2:
    print(f"Usage : python {sys.argv[0]} <ID CAPTEUR>")
    exit(1)


#LoRa init
local_addr = int(sys.argv[1])
channel = 18
local_msg_id = 0

lora = lora(channel=channel, address=local_addr, callback=callback_lora)
lora.activate()

frq_start = 400*10**6
frq_end = 420*10**6
current_lat = None
current_lng = None


#Scanner init
nb_sdr = len(RtlSdr.get_device_serial_addresses())
scanners = []

"""
for _ in range(nb_sdr):
    s = scanner(frq_start, frq_end, callback_scanner)
    s.activate()
    scanners.append(s)
"""

scanner = scanner(frq_start, frq_end, callback_scanner)
scanner.activate()


#GPS init
gps = VMA430()
gps.begin(9600)
gps.setUBXNav()

while True:

    gps.getUBX_packet()
    #print(f"date : {gps.utc_time.to_string()}")
    #print(f"lat {gps.location.latitude}")
    #print(f"lng {gps.location.longitude}")
    
    if gps.location.latitude and gps.location.longitude:
        current_lat = struct.pack("d", gps.location.latitude)
        current_lng = struct.pack("d", gps.location.longitude)

    time.sleep(0.5)


lora.stop()
scanner.stop()

"""
for s in scanners:
    s.stop()
"""