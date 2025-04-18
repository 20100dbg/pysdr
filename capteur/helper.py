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

    DETECT = 7 #tester envoi frq + timestamp
    REQUEST_GPS = 8
    REQUEST_CONF = 9


class Packet(object):
    """ Define a packet to send/receive with LoRa """

    TYPE_SIZE = 1
    NUM_SIZE = 1
    FROM_TO_SIZE = 1
    PAYLOAD_SIZE_SIZE = 1
    SYNC_WORD = b"\xB5\x62"

    IDX_PAYLOAD_SIZE = len(SYNC_WORD) + TYPE_SIZE + NUM_SIZE + FROM_TO_SIZE
    HEADER_SIZE = len(SYNC_WORD) + TYPE_SIZE + NUM_SIZE + FROM_TO_SIZE + PAYLOAD_SIZE_SIZE
    FOOTER_SIZE = 2


    def __init__(self, type, num, from_to, payload=b""):
        self.type = type
        self.num = num
        self.from_to = from_to
        self.payload = payload

        data = self.build()
        self.checksum = data[-2:]
        self.valid = True

    @staticmethod
    def read(data):

        idx = len(Packet.SYNC_WORD)
        type = bytes_to_int(data[idx:idx+Packet.TYPE_SIZE])
        
        idx += Packet.TYPE_SIZE
        num = bytes_to_int(data[idx:idx+Packet.NUM_SIZE])
        
        idx += Packet.NUM_SIZE
        from_to = bytes_to_int(data[idx:idx+Packet.FROM_TO_SIZE])
        
        idx += Packet.FROM_TO_SIZE
        payload_size = bytes_to_int(data[idx:idx+Packet.PAYLOAD_SIZE_SIZE])
        
        idx += Packet.PAYLOAD_SIZE_SIZE
        payload = data[idx:idx+payload_size]
        checksum = data[-2:]

        pkt = Packet(type, num, from_to, payload)
        pkt.valid = pkt.checksum == checksum

        return pkt

    def to_string(self):

        type_name = "UNKNOWN"
        for type in MsgType:
            if self.type == type.value:
                type_name = type.name

        return f"""type={type_name} - {self.type}  num={self.num} from_to={self.from_to}
payload={self.payload}
checksum={self.checksum} valid={self.valid}"""
    

    def build(self):
        """ Create a byte array with specified header data """
        msg = self.SYNC_WORD
        msg += int_to_bytes(self.type, Packet.TYPE_SIZE)
        msg += int_to_bytes(self.num, Packet.NUM_SIZE)
        msg += int_to_bytes(self.from_to, Packet.FROM_TO_SIZE)
        msg += int_to_bytes(len(self.payload), Packet.PAYLOAD_SIZE_SIZE)
        msg += self.payload
        checksum = self.calculate_checksum(msg[2:])
        msg += int_to_bytes(checksum[0], 1) + int_to_bytes(checksum[1], 1)
        return msg


    def calculate_checksum(self, data):
        """Checksum. data needs to be all the packet, except SYNC_WORD, """
        CK_A, CK_B = 0, 0

        for i in range(len(data)):
            CK_A = CK_A + data[i]
            CK_B = CK_B + CK_A

        return [CK_A & 0xFF, CK_B & 0xFF]


class Parameters(object):
    """docstring for Parameters"""

    def __init__(self, debug=False):

        #General
        self.debug = debug
        #
        self.detection_history = {}
        self.receive_history = []
        self.start_time = time.time()
        self.time_set = False

        #LoRa
        self.channel = 18
        self.air_data_rate = 2.4
        self.sub_packet_size = 32
        self.idx_payload_size = 5
        self.header_size = 6
        self.footer_size = 2

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
    for idx in range(idx_start, len(data)):
        if data[idx:idx+len(sync_word)] == sync_word:
            return idx

    return -1


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



