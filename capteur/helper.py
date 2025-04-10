import json
import time
import os
from enum import Enum


class MsgType(Enum):
    PING = 1
    FRQ = 2
    CONF_SCAN = 3
    CONF_LORA = 4
    ACK = 5
    ERROR = 6

class Parameters(object):
    """docstring for Parameters"""

    def __init__(self, debug=False):

        #General
        self.debug = debug
        #
        self.detection_history = {}
        self.receive_history = {}
        self.start_time = time.time()
        self.time_set = False

        #LoRa
        self.channel = 18
        self.air_data_rate = 2.4
        self.sub_packet_size = 32
        self.idx_payload_size = 3
        self.headers_size = 6
        self.sync_word = b"\xB5\x62"
        #
        self.local_addr = None
        self.local_msg_id = 0
        self.relay_history = {}


        #scanner
        self.frq_start = 400
        self.frq_end = 420
        self.threshold = -10
        self.delay_detection = 0.1
        self.delay_duplicate = 30
        self.range_duplicate = 0.5
        self.delay_receive = 5
        self.send_history = {}

        #gps
        self.current_lat = 0
        self.current_lng = 0
        self.delay_gps = 5


    def save_config(self):
        """ Save config as JSON in a file """
        config = {'frq_start': self.frq_start, 'frq_end': self.frq_end, 'threshold': self.threshold}
        with open('config.json', 'w') as f:
            json.dump(config, f)

        if self.debug:
            print(f"Save config : {self.frq_start} {self.frq_end} {self.threshold}")
            log(f"Save config : {self.frq_start} {self.frq_end} {self.threshold}")


    def load_config(self):
        """ Load config from a file and set parameters """

        with open('config.json', 'r') as f:
            config = json.loads(f.read())

        self.frq_start = config['frq_start']
        self.frq_end = config['frq_end']
        self.threshold = config['threshold']
        
        if self.debug:
            print(f"Load config : {config}")
            log(f"Load config : {config}")



def find_sync(data, sync_word, idx_start=0):
    if not data:
        return -1

    for idx in range(idx_start, len(data)):
        if data[idx:idx+len(sync_word)] == sync_word:
            return idx

    return -1


def calculate_checksum(data):
    CK_A, CK_B = 0, 0

    for i in range(len(data)):
        CK_A = CK_A + data[i]
        CK_B = CK_B + CK_A

    return (CK_A & 0xFF, CK_B & 0xFF)


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
    
    return (data[0], #msg_type
            data[1], #msg_id
            data[2], #msg_to
            data[3]) #msg_size


def build_message(msg_type, msg_id, msg_to, data=b''):
    """ Create a byte array with specified header data """

    msg = b''
    msg += int_to_bytes(msg_type, 1)
    msg += int_to_bytes(msg_id, 1)
    msg += int_to_bytes(msg_to, 1)
    msg += int_to_bytes(len(data), 1)
    msg += data
    return msg


def bytes_to_hex(b):
    """ Get bytes to proper hex notation """
    return ' '.join(['{:02X}'.format(x) for x in b])



def log(data):
    with open("log", "a") as f:
        f.write(str(round(time.time(),3)) + " : " + str(data) + "\n")


# backup
def set_system_timestamp(timestamp):
    os.system(f'sudo date -s @{timestamp}')

def set_system_date(date):
    os.system(f'sudo date -s "{date}"')



