import sx126x
import time
from enum import Enum
from gpiozero import LED, Button, InputDevice
#import RPi.GPIO as GPIO

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
    msg += b'\x00' * (sub_packet_size - len(msg))
    return msg


def btohex(b):
    """ Get bytes to proper hex notation """
    return ' '.join(['{:02X}'.format(x) for x in b])


def callback_lora(data):
    """ Handles every message received from LoRa """

    #print(f"Received {data}")

    (msg_type, msg_id, msg_to) = extract_header(data)
    payload = data[HEADER_SIZE:]

    if msg_type == MsgType.ACK.value:
        led.on()
        time.sleep(2)
        led.off()


def on_button():    
    global last_push_time

    print("on_button !")

    if time.time() - last_push_time > 2:
        lora.send_bytes(build_message(MsgType.PING.value, local_msg_id, local_addr))
        last_push_time = time.time()



#General
global last_push_time
debug = True
last_push_time = 0

#LoRa
local_addr = 255
local_msg_id = 255
channel = 18
air_data_rate = 2.4
sub_packet_size = 32


#gpiozero
led = LED("GPIO26")
button = InputDevice(17, pull_up=False)


"""
#Rpi.GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(17, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #Button
GPIO.setup(26, GPIO.OUT) #LED
"""

lora = sx126x.sx126x(port="/dev/ttyS0", debug=debug)
lora.set_config(channel=channel,logical_address=local_addr,network=0, tx_power=22,
                air_data_rate=air_data_rate, sub_packet_size=sub_packet_size)
lora.listen(callback=callback_lora, expected_size=sub_packet_size)

while True:

    if button.value:
        on_button()

    time.sleep(0.1)

lora.close()