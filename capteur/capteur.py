import sys
from lora import *
from scanner import *
from signal import signal, SIGINT

def handler(signal_received, frame):
    global running
    print("\n\nCaught Ctrl+C, stopping...")
    running = False


def getmsgkey(msgvalue):
    idx = list(dict_msg.values()).index(msgvalue)
    return list(dict_msg.keys())[idx]

## type MSG
# frequence active
# config gamme + seuil
# ACK config

## format MSG
# type msg (1)
# ID capteur (1)
# data (X)


def callback_lora(data):

    print(f"Received {data}")

    msg_type = int.from_bytes(data[0:1])
    msg_to = int.from_bytes(data[1:2])

    #print(f"to : {msg_to} - MSG : {getmsgkey(msg_type)}")
    if msg_to != local_addr:
        return

    if dict_msg["CONF"] == msg_type:
        frq_start = int.from_bytes(data[2:4])
        frq_end = int.from_bytes(data[4:6])
        threshold = int.from_bytes(data[6:7])

        if frq_start == 0 or frq_end == 0 or threshold == 0:
            return

        new_threshold = (threshold / 10) + 0.4

        scanner.set_threshold(new_threshold)
        scanner.set_frq(frq_start, frq_end)

        print(f"new conf : {frq_start} - {frq_end} / {new_threshold}")

        send(dict_msg["CONF_ACK"], local_addr, b'')



def callback_scanner(frq):
    send(dict_msg["FRQ"], local_addr, frq.to_bytes(4, 'big'))


def send(msg_type, addr, data):
    msg = b''
    msg += msg_type.to_bytes(1, 'big')
    msg += addr.to_bytes(1, 'big')
    msg += data

    print(f"Sending {msg}")
    lora.send(msg)
    

signal(SIGINT, handler)

local_addr = int(sys.argv[1])
dict_msg = {"FRQ": 0, "CONF": 1, "CONF_ACK": 2 }


global running
running = True

lora = lora(channel=18, address=local_addr, callback=callback_lora)
lora.activate()

frq_start = 400e6
frq_end = 415e6

scanner = scanner(frq_start, frq_end, callback_scanner)
scanner.activate()

while running:
    time.sleep(0.01)


lora.stop()
scanner.stop()
