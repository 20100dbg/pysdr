######################
# GPS - RPI Wiring
# VCC - 3V ou 5V
# GND - GND
# TX - UART RX / GPIO 1 / PIN 28
# RX - UART TX / GPIO 0 / PIN 27
######################

import datetime
import serial
import struct
import threading
import time

class Time_UTC(object):
    def __init__(self):
        super(Time_UTC, self).__init__()
        self.valid = False
        self.datetime = None

    def to_string(self):
        return self.datetime


class Location(object):
    def __init__(self):
        super(Location, self).__init__()
        self.longitude = None
        self.latitude = None
        self.valid = None

    def to_string(self):
        return f"{self.latitude}-{self.longitude}"


class UBX(object):
    def __init__(self, data):
        """ Create an UBX packet from a payload """

        self.valid = False
        self.class_byte = None
        self.id_byte = None
        self.payload_length = None
        self.payload = None
        self.checksum = None
        self.obj = None
        self.size = 0

        if data and len(data) > 6 and data[0:2] == UBX_SYNC:
            payload_length = int.from_bytes(data[4:6], byteorder='little')

            if len(data) >= payload_length + 8:
                self.class_byte = data[2]
                self.id_byte = data[3]
                self.payload_length = payload_length
                self.payload = data[6:self.payload_length+6]
                self.checksum = data[self.payload_length+6:self.payload_length+8]
                self.obj = data[:payload_length + 8]
                self.size = payload_length + 8
                CK_A, CK_B = VMA430.calculate_checksum(data[2:self.payload_length+6])

                if CK_A == self.checksum[0] and CK_B == self.checksum[1]:
                    self.valid = True


    def to_string(self):
        return f"""data : {bytes_to_hex(self.obj)}
    class & ID : {VMA430.get_classname(self.class_byte)} / {self.class_byte}-{self.id_byte}
    checksum : {bytes_to_hex(self.checksum)} / calculated checksum : {bytes_to_hex(VMA430.calculate_checksum(self.obj[2:-2]))}
    valid : {self.valid}"""

#end class UBX


NAV_MODE = {'portable': 0x00, 'stationary': 0x02, 'pedestrian': 0x03, 'automotive': 0x04, 'sea': 0x05, 'airborne': 0x06}
DATA_RATE = {'1HZ': 0xE803, '2HZ': 0xFA01, '3_33HZ': 0x2C01, '4HZ': 0xFA00}
PORT_RATE = {4800: 0xC01200, 9600: 0x802500, 19200: 0x004B00, 38400: 0x009600, 57600: 0x00E100, 115200: 0x00C200, 230400: 0x008400}
UBX_SYNC = b'\xB5\x62'

# definition of UBX class IDs
# source: U-blox7 V14 Receiver Description Protocol page 88 https://www.u-blox.com/sites/default/files/products/documents/u-blox7-V14_ReceiverDescriptionProtocolSpec_%28GPS.G7-SW-12001%29_Public.pdf
NAV_CLASS = 0x01 # Navigation Results: Position, Speed, Time, Acc, Heading, DOP, SVs used
RXM_CLASS = 0x02 # Receiver Manager Messages: Satellite Status, RTC Status
INF_CLASS = 0x04 # Information Messages: Printf-Style Messages, with IDs such as Error, Warning, Notice
ACK_CLASS = 0x05 # Ack/Nack Messages: as replies to CFG Input Messages
CFG_CLASS = 0x06 # Configuration Input Messages: Set Dynamic Model, Set DOP Mask, Set Baud Rate, etc
MON_CLASS = 0x0A #10 Monitoring Messages: Comunication Status, CPU Load, Stack Usage, Task Status
AID_CLASS = 0x0B #11 AssistNow Aiding Messages: Ephemeris, Almanac, other A-GPS data input
TIM_CLASS = 0x0D #13 Timing Messages: Time Pulse Output, Timemark Results
LOG_CLASS = 0x21 #33 Logging Messages: Log creation, deletion, info and retrieval


class VMA430(object):
    def __init__(self):
        super(VMA430, self).__init__()
        self.utc_time = Time_UTC()
        self.location = Location()


    def begin(self, port='/dev/ttyAMA0', baudrate=9600, debug=False):

        self.debug = debug
        self.baudrate = baudrate
        self.serial = serial.Serial(port=port, baudrate=self.baudrate,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS, timeout=1)

        self.serial.read(self.serial.in_waiting)
        self.callback_pos = None
        self.callback_time = None


    def send_ubx(self, data):
        if self.debug:
            print(f"SEND : {bytes_to_hex(data)}")

        self.serial.write(data)


    @staticmethod
    def get_classname(class_id):

        if class_id == NAV_CLASS: return "NAV"
        elif class_id == RXM_CLASS: return "RXM"
        elif class_id == INF_CLASS: return "INF"
        elif class_id == ACK_CLASS: return "ACK"
        elif class_id == CFG_CLASS: return "CFG"
        elif class_id == MON_CLASS: return "MON"
        elif class_id == AID_CLASS: return "AID"
        elif class_id == TIM_CLASS: return "TIM"
        elif class_id == LOG_CLASS: return "LOG"


    def get_nav_mode(self):
        """ Return current NAV settings """

        payload = [0xB5, 0x62, 0x06, 0x24, 0x00, 0x00]
        CK_A, CK_B = VMA430.calculate_checksum(payload[2:])
        payload = payload + [CK_A, CK_B]

        for _ in range(3):

            self.send_ubx(payload)
            time.sleep(0.4 + _/5)

            packets = gps.get_ubx_packet()

            for packet in packets:
                if packet.class_byte == 0x06 and packet.id_byte == 0x24:
                    return True, packet.payload

        return False


    def set_nav_mode(self, mode):
        """ Set dynamic model (is this module is moving ?) """
        #mode can be : Portable, Stationary, Pedestrian, Automotive, Sea and Airborne

        nav_mode = NAV_MODE[mode]
        payload = [0xB5, 0x62, 0x06, 0x24, 0x24, 0x00, 0x01, 0x00, nav_mode] + [0x00] * 33

        CK_A, CK_B = VMA430.calculate_checksum(payload[2:])
        payload = payload + [CK_A, CK_B]

        for _ in range(3):

            self.send_ubx(payload)
            time.sleep(0.5 + _/5)
            packets = gps.get_ubx_packet()

            for packet in packets:
                if packet.class_byte == 0x05 and packet.id_byte == 0x1:
                    return True

        return False


    def set_power_mode(self, mode):
        """ NOT TESTED / FINISHED """
        """ Sets power mode between "continous" or "power save" modes """
        #power save mode requires GLONASS to be disabled

        if mode == "continous":
            mode = 0
        elif mode == "power_save":
            mode = 1

        payload = [0xB5, 0x62, 0x06, 0x11, 0x08, 0x02, 0x00, 0x08, mode]        

        CK_A, CK_B = VMA430.calculate_checksum(payload[2:])
        payload = payload + [CK_A, CK_B]

        for _ in range(3):
            self.send_ubx(payload)
            time.sleep(0.5 + _/5)
            packets = gps.get_ubx_packet()

            for packet in packets:
                if packet.class_byte == 0x05 and packet.id_byte == 0x1:
                    return True

        return False

    
    def set_power_mode_parameters(self):
        """ NOT TESTED / FINISHED """
        """ Sets power mode between "continous" or "power save" modes """
        #power save mode requires GLONASS to be disabled

        flags = [0x00, 0x00, 0x00, 0x00]
        updatePeriod = 10000
        updatePeriod = updatePeriod.to_bytes(4, 'little')

        searchPeriod = 30000
        searchPeriod = searchPeriod.to_bytes(4, 'little')

        gridOffset = 0
        gridOffset = gridOffset.to_bytes(4, 'little')

        onTime = 0
        onTime = onTime.to_bytes(2, 'little')

        data = [0x01, 0x00, 0x00, 0x00, ]

        payload = [0xB5, 0x62, 0x06, 0x3B, 0x2C, 0x00]

        CK_A, CK_B = VMA430.calculate_checksum(payload[2:])
        payload = payload + [CK_A, CK_B]

        for _ in range(3):
            self.send_ubx(payload)
            time.sleep(0.5 + _/5)
            packets = gps.get_ubx_packet()

            for packet in packets:
                if packet.class_byte == 0x05 and packet.id_byte == 0x1:
                    return True

        return False


    def set_measure_rate(self, rate):
        #CFG-RATE
        #0xB5 0x62 0x06 0x08 0x06 0x00
        pass


    def get_message_rate(self, msg_class, msg_id):

        payload = [0xB5, 0x62, 0x06, 0x01, 0x02, 0x00, msg_class, msg_id]

        CK_A, CK_B = VMA430.calculate_checksum(payload[2:])
        payload = payload + [CK_A, CK_B]

        for _ in range(3):
            self.send_ubx(payload)
            time.sleep(0.5 + _/5)
            packets = gps.get_ubx_packet()

            if self.debug:
                print("get_message_rate")
                for packet in packets:
                    print(packet.to_string())                

        return False


    def set_active(self, active):
        """ NOT TESTED / NOT WORKING Turn on and off receiver until said otherwise """

        active = 0 if active else 1
        active = active.to_bytes(4, 'little')
        
        #if duration = 0 : limitless
        duration = 0
        duration = duration.to_bytes(4, 'little')

        payload = [0xB5, 0x62, 0x02, 0x41, 0x08, 0x00] + list(duration) + list(active)

        CK_A, CK_B = VMA430.calculate_checksum(payload[2:])
        payload = payload + [CK_A, CK_B]

        for _ in range(3):
            self.send_ubx(payload)
            time.sleep(0 + _/5)
            packets = gps.get_ubx_packet()

            if self.debug:
                self.debug_packets(packets)
                """
                for packet in packets:
                    if packet.class_byte == 0x05 and packet.id_byte == 0x1:
                        return True
                """

        return False


    def check_pos_validity(self):
        """ Gives indications on time and position accuracy """

        payload = [0xB5, 0x62, 0x01, 0x07, 0x00, 0x00]

        CK_A, CK_B = VMA430.calculate_checksum(payload[2:])
        payload = payload + [CK_A, CK_B]

        fix_type = {0x00: "No Fix", 0x01: "Dead Reckoning only", 0x02: "2D-Fix", 0x03: "3D-Fix", 0x04: "GNSS + dead reckoning combined", 0x05: "Time only fix" }

        for _ in range(3):
            self.send_ubx(payload)
            time.sleep(0.5 + _/5)
            packets = gps.get_ubx_packet()

            for packet in packets:

                if packet.class_byte == 0x01 and packet.id_byte == 0x07:
                    gnss_fix_ok = packet.payload[21] & 0x01
                    correction_applied = packet.payload[21] & 0x02

                    if self.debug:
                        print(f"fix_type = {fix_type[packet.payload[20]]} / gnss_fix_ok={gnss_fix_ok}, correction_applied={correction_applied}")
                    return fix_type[packet.payload[20]], gnss_fix_ok, correction_applied


    def reset_config(self):
        set_config_mode("reset")

    def save_config(self):
        set_config_mode("save")

    def load_config(self):
        set_config_mode("load")

    def set_config_mode(self, mode):
        """ SAVE currents settings as permanent, or LOAD to replace current settings with permanent """
        """ or CLEAR to load default into permanent settings"""

        payload = [0xB5, 0x62, 0x06, 0x09, 0x0C, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]

        if mode == "clear":
            payload[6:10] = [0xFF, 0xFF, 0xFF, 0xFF]
        elif mode == "save":
            payload[10:14] = [0xFF, 0xFF, 0xFF, 0xFF]
        elif mode == "load":
            payload[14:18] = [0xFF, 0xFF, 0xFF, 0xFF]
        else:
            return False

        CK_A, CK_B = VMA430.calculate_checksum(payload[2:])
        payload = payload + [CK_A, CK_B]

        for _ in range(3):
            self.send_ubx(payload)
            time.sleep(0.5 + _/5)
            packets = gps.get_ubx_packet()

            for packet in packets:
                if packet.class_byte == 0x05 and packet.id_byte == 0x01:
                    return True

        return False


    def activate_poll(self):
        """ Activate POS and TIME polling (chip sends regularly time & pos UBX messages) """

        polling_messages = [ [NAV_CLASS, 0x21], [NAV_CLASS, 0x02] ]
        rate = 0x01
        results = []
        max_retry = 3

        for idx in range(len(polling_messages)):

            msg_class = polling_messages[idx][0]
            msg_id = polling_messages[idx][1]

            if self.debug:
                print(f"Enabling UBX {VMA430.get_classname(msg_class)} - {msg_id}... ", end="")

            got_ack = False

            for _ in range(max_retry):
                data = [0xB5, 0x62, 0x06, 0x01, 0x03, 0x00, msg_class, msg_id, rate]
                CK_A, CK_B = VMA430.calculate_checksum(data[2:])

                self.send_ubx(data + [CK_A, CK_B])
                time.sleep(0.3 + _/5)
                packets = gps.get_ubx_packet()

                for packet in packets:
                    if packet.class_byte == 0x05 and packet.id_byte == 0x01:
                        got_ack = True
                        break

                if got_ack:
                    break

            results.append(got_ack)

        return all(results)


    def debug_packets(self, packets):
        """ Print packets contents """

        if packets:
            for ubx_packet in packets:
                #print(f"{VMA430.get_classname(ubx_packet.class_byte)} - {hex(ubx_packet.class_byte)} {hex(ubx_packet.id_byte)}")
                print(f"DEBUG {ubx_packet.to_string()}")
        else:
            print("no packets")


    def parse_nav_timeutc(self, payload):
        """ Extract time from a payload """

        if len(payload) != 20:
            self.utc_time = Time_UTC()
            return False

        if payload[19] == 0x07:

            dt = datetime.datetime(year=int.from_bytes(payload[12:14], byteorder='little'),
                month = payload[14], day = payload[15], hour = payload[16], minute = payload[17], 
                second = payload[18])
            dt = dt + datetime.timedelta(microseconds=struct.unpack("<l", payload[8:12])[0])

            self.utc_time.datetime = dt
            self.utc_time.valid = True

            if self.callback_time:
                self.callback_time(self.utc_time)
        else:
            self.utc_time = Time_UTC()

        return True


    def parse_nav_pos(self, payload):
        """ Extract position from a payload """

        self.location.valid = True
        
        if len(payload) != 28:
            self.location.longitude = None
            self.location.latitude = None
            self.location.valid = False
            return False

        self.location.longitude = struct.unpack("<I", payload[4:8])[0] / 10000000
        self.location.latitude = struct.unpack("<I", payload[8:12])[0] / 10000000

        if self.location.longitude == 0.0 and self.location.latitude == 0.0:
            self.location.valid = False

        if self.callback_pos:
            self.callback_pos(self.location)

        return True


    @staticmethod
    def calculate_checksum(data):
        CK_A, CK_B = 0, 0

        for i in range(len(data)):
            CK_A = CK_A + data[i]
            CK_B = CK_B + CK_A

        return (CK_A & 0xFF, CK_B & 0xFF)


    def handle_ubx_packet(self, ubx_packet):
        """ Do something for each type of packet """

        if self.debug:
            print(f"{VMA430.get_classname(ubx_packet.class_byte)} - {hex(ubx_packet.class_byte)} {hex(ubx_packet.id_byte)}")

        if ubx_packet.class_byte == NAV_CLASS and ubx_packet.id_byte == 33:
            self.parse_nav_timeutc(ubx_packet.payload)

        elif ubx_packet.class_byte == NAV_CLASS and ubx_packet.id_byte == 2:
            self.parse_nav_pos(ubx_packet.payload)

        elif ubx_packet.class_byte == CFG_CLASS:
            #print(ubx_packet.to_string())
            pass



    def goto_sync(self, data):
        """ return buffer starting with SYNC bytes (or None if SYNC not found) """

        if not data:
            return None

        for idx in range(len(data)):
            if data[idx:idx+2] == UBX_SYNC:
                return data[idx:]

        return None


    def get_ubx_packet(self):
        """ Read serial and return one or many UBX packets """
        #Ignore possible data loss

        packets = []
        buffer_receive = b''
        max_retry = 3

        for _ in range(max_retry):
            buffer_receive += self.serial.read(self.serial.in_waiting)
            if _ < max_retry - 1:
                time.sleep(0.2)

        while True:
            buffer_receive = self.goto_sync(buffer_receive)

            if buffer_receive:
                ubx_packet = UBX(buffer_receive)
                buffer_receive = buffer_receive[ubx_packet.size:]

                if ubx_packet.valid:
                    packets.append(ubx_packet)
                    #self.handle_ubx_packet(ubx_packet)
                else:
                    break
            else:
                break

        return packets


    def listen(self, callback_pos, callback_time):
        self.running_listen = True
        self.callback_pos = callback_pos
        self.callback_time = callback_time

        self.t_receive = threading.Thread(target=self.listen_loop, args=[])
        self.t_receive.start()


    def listen_loop(self):
        while self.running_listen:
            packets = gps.get_ubx_packet()
            for p in packets:
                gps.handle_ubx_packet(p)

            time.sleep(0.5)

    def close(self):
        """ Close VMA430 object """

        if self.running_listen:
            self.running_listen = False
            self.t_receive.join()

        self.serial.close()


#end class VMA430


def bytes_to_hex(b):
    """ Get bytes to proper hex notation """
    return ' '.join(['{:02X}'.format(x) for x in b])



#For test purposes
if __name__ == "__main__":

    def callback_time(data):
        print(f"callback_time : {data.to_string()}")

    def callback_pos(data):
        print(f"callback_pos : {data.to_string()}")

    debug = False

    gps = VMA430()
    gps.begin(port="/dev/ttyAMA2", baudrate=9600, debug=debug)

    #gps.reset_config()

    #Set stationary mode for a more precise position
    nav_mode = 'stationary'
    success = gps.set_nav_mode(nav_mode)

    if debug:
        print(f"set_nav_mode {nav_mode} : {success}")
    
    #We need to activate polling to actually get data
    for _ in range(3):
        success = gps.activate_poll()
        if success:
            if debug:
                print("activate_poll ok !")
            break
        time.sleep(0.1)

    #Lets get some data, two ways :

    #Use callbacks
    #gps.listen(callback_pos=callback_pos, callback_time=callback_time)

    #Or manually ask for UBX packets and send them to handle_ubx_packet to update POS and time
    while True:
        gps.location = Location()
        gps.utc_time = Time_UTC()

        packets = gps.get_ubx_packet()
        for p in packets:
            gps.handle_ubx_packet(p)

        if gps.location.longitude and gps.location.latitude:
            print(f"longitude {gps.location.longitude} / latitude {gps.location.latitude}")

        if gps.utc_time.datetime and gps.utc_time.valid:
            print(f"utc_time {gps.utc_time.datetime}")


        time.sleep(2)
