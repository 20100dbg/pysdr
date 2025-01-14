import sys
from lora import *
from scanner import *


## debug helpers

from signal import signal, SIGINT
def handler(signal_received, frame):
    print("\n\nCaught Ctrl+C, stopping...")
    scanner.stop()
    #lora.stop()

def getmsgkey(msgvalue):
    idx = list(dict_msg.values()).index(msgvalue)
    return list(dict_msg.keys())[idx]

#signal(SIGINT, handler)

##


def callback_lora(data):

    #print(f"Received {data}")

    if len(data) >= 2:
        msg_type = int.from_bytes(data[0:1])
        msg_to = int.from_bytes(data[1:2])

        #print(f"to : {msg_to} - MSG : {getmsgkey(msg_type)}")
        if msg_to != local_addr:
            return

        if dict_msg["CONF"] == msg_type and len(data) == 7:
            frq_start = int.from_bytes(data[2:4])
            frq_end = int.from_bytes(data[4:6])
            threshold = int.from_bytes(data[6:7])
            
            #new_threshold = (threshold / 10) + 0.4
            new_threshold = threshold / 10

            scanner.set_threshold(new_threshold)
            scanner.set_frq(frq_start, frq_end)

            print(f"new conf : {frq_start} - {frq_end} / {new_threshold}")

            send(dict_msg["CONF_ACK"], local_addr, data[2:7])

        elif dict_msg["PING"] == msg_type:


            print(f"got PING")
            send(dict_msg["PONG"], local_addr, b'')



def callback_scanner(frq):
    send(dict_msg["FRQ"], local_addr, frq.to_bytes(4, 'big'))


def send(msg_type, addr, data):
    msg = b''
    msg += msg_type.to_bytes(1, 'big')
    msg += addr.to_bytes(1, 'big')
    msg += data

    print(f"Sending {msg}")
    lora.send(msg)
    
def save_config():
    with open('config.json', 'w') as f:
        json.dump(config, f)

def load_config():
    pass


if len(sys.argv) != 2:
    print(f"Usage : python {sys.argv[0]} <ID CAPTEUR>")
    exit(1)

local_addr = int(sys.argv[1])
dict_msg = {"FRQ": 0, "CONF": 1, "CONF_ACK": 2, "PING": 3, "PONG": 4 }


lora = lora(channel=18, address=local_addr, callback=callback_lora)
lora.activate()

frq_start = 400*10**6
frq_end = 420*10**6

nb_sdr = len(RtlSdr.get_device_serial_addresses())
scanners = []

"""
for _ in range(nb_sdr):
    s = scanner(frq_start, frq_end, callback_scanner)
    s.activate()
    scanners.append(s)
"""

scanner = scanner(frq_start, frq_end, callback_scanner, debug=True)
scanner.activate(blocking=True)

if lora.running:
    lora.stop()
#scanner.stop()

"""
for s in scanners:
    s.stop()
"""