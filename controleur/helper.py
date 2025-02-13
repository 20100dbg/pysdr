class MsgType(Enum):
    PING = 1
    FRQ = 2
    CONF = 3
    ACK = 4
    ERROR = 5

HEADER_SIZE = 3


def pretty_frq(frq):
    strfrq = str(frq/1000000)
    strfrq = strfrq.ljust(7, '0')
    return strfrq + 'M'


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


def increment_msg_id():
    global local_msg_id
    local_msg_id += 1
    if local_msg_id == 256:
        local_msg_id = 0
