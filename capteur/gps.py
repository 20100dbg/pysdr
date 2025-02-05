import serial
import time

class Time_UTC(object):
    def __init__(self):
        super(Time_UTC, self).__init__()
        self.year = None
        self.month = None
        self.day = None
        self.hour = None
        self.minute = None
        self.second = None
        self.valid = None

    def to_string(self):
        return f"{self.year}-{self.month}-{self.day} {self.hour}:{self.minute}:{self.second} ({self.valid})"

class Location(object):
    def __init__(self):
        super(Location, self).__init__()
        self.longitude = None
        self.latitude = None
        self.valid = None

class UBX(object):
    def __init__(self):
        self.class_byte = None
        self.id_byte = None
        self.payload_length = None
        self.payload = None
        self.checksum = None
        self.obj = None

    def read(self, data):
        self.obj = data
        self.class_byte = data[2]
        self.id_byte = data[3]
        self.payload_length = int.from_bytes(data[4:6], byteorder='little')
        self.payload = data[6:self.payload_length+6]
        self.checksum = data[self.payload_length+6:self.payload_length+8]

    def to_string(self):
        print(f"data : {btohex(self.obj[:40])}")
        print(f"class_byte : {self.class_byte}")
        print(f"id_byte : {self.id_byte}")
        print(f"payload length : {self.payload_length} {len(self.payload)}")
        print(f"payload : {btohex(self.payload)}")
        print(f"checksum : {btohex(self.checksum)}")


NAV_MODE = {'pedestrian': 0x03, 'automotive': 0x04, 'sea': 0x05, 'airborne': 0x06}
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

    def begin(self, baudrate):

        port = '/dev/ttyAMA2'
        self.baudrate = baudrate
        self.nav_mode = NAV_MODE['pedestrian']
        self.data_rate = DATA_RATE['4HZ']
        self.serial = serial.Serial(port=port, baudrate=self.baudrate,
                    parity=serial.PARITY_NONE, stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS, timeout=1)

    def sendUBX(self, UBXmsg):
        print(f"[+] SENDING {UBXmsg}")
        self.serial.write(UBXmsg)
        time.sleep(0.1)


    ####################################
    ####################################


    def generateConfiguration(self):
        
        tmp_data_rate = self.data_rate.to_bytes(2, 'little')
        tmp_baudrate = self.baudrate.to_bytes(3, 'little')
        print(f"tmp_baudrate {tmp_baudrate}")

        arr = bytearray()
        arr.append(self.nav_mode)
        arr.append(tmp_data_rate[0])
        arr.append(tmp_data_rate[1])
        arr.append(tmp_baudrate[0])
        arr.append(tmp_baudrate[1])
        arr.append(tmp_baudrate[2])
        arr.append(int(self.GLLSentence))
        arr.append(int(self.GSVSentence))
        arr.append(int(self.RMCSentence))
        arr.append(int(self.VTGSentence))

        return arr

    def sendConfiguration(self):
        
        settings = self.generateConfiguration()
        gpsSetSuccess = 0
        print("Configuring u-Blox GPS initial state...");

        #Generate the configuration string for Navigation Mode
        setNav = [0xB5, 0x62, 0x06, 0x24, 0x24, 0x00, 0xFF, 0xFF] + settings + [0x03, 0x00, 0x00, 0x00, 0x00, 0x10, 0x27, 0x00, 0x00, 0x05, 0x00, 0xFA, 0x00, 0xFA, 0x00, 0x64, 0x00, 0x2C, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        CK_A, CK_B = self.calculate_checksum(setNav[2:len(setNav)-4])

        #Generate the configuration string for Data Rate
        setDataRate = [0xB5, 0x62, 0x06, 0x08, 0x06, 0x00, settings[1], settings[2], 0x01, 0x00, 0x01, 0x00, 0x00, 0x00]
        CK_A, CK_B = self.calculate_checksum(setDataRate[2:len(setDataRate)-4])

        #Generate the configuration string for Baud Rate
        setPortRate = [0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0xD0, 0x08, 0x00, 0x00, settings[3], settings[4], settings[5], 0x00, 0x07, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]
        CK_A, CK_B = self.calculate_checksum(setPortRate[2:len(setPortRate)-4])

        setGLL = [0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x01, 0x2B]
        setGSA = [0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x02, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x02, 0x32]
        setGSV = [0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x03, 0x39]
        setRMC = [0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x01, 0x04, 0x40]
        setVTG = [0xB5, 0x62, 0x06, 0x01, 0x08, 0x00, 0xF0, 0x05, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x04, 0x46]

        gpsStatus = [False, False, False, False, False, False, False]


        while gpsSetSuccess < 3:
        
            print("Setting Navigation mode...")

            self.sendUBX(setNav)     #Send UBX Packet
            gpsSetSuccess += self.getUBX_ACK(setNav[2:4]) #Passes Class ID and Message ID to the ACK Receive function

            if gpsSetSuccess == 5:
                gpsSetSuccess -= 4
                time.sleep(0.1)
                lowerPortRate = [0xB5, 0x62, 0x06, 0x00, 0x14, 0x00, 0x01, 0x00, 0x00, 0x00, 0xD0, 0x08, 0x00, 0x00, 0x80, 0x25, 0x00, 0x00, 0x07, 0x00, 0x03, 0x00, 0x00, 0x00, 0x00, 0x00, 0xA2, 0xB5]
                self.sendUBX(lowerPortRate)
                time.sleep(0.1);

            if gpsSetSuccess == 6:
                gpsSetSuccess -= 4
            if gpsSetSuccess == 10:
                gpsStatus[0] = True;

        if gpsSetSuccess == 3:
            print("Navigation mode configuration failed.");
            
        gpsSetSuccess = 0;

        if settings[4] != 0x25:
            print("Setting Port Baud Rate... ");
            self.sendUBX(setPortRate);
            print("Success!");
            time.sleep(0.1);


    def setUBXNav(self):
        setNAVUBX = [0xB5, 0x62, 0x06, 0x01, 0x03, 0x00, 0x01, 0x21, 0x01]
        setNAVUBX_pos = [0xB5, 0x62, 0x06, 0x01, 0x03, 0x00, 0x01, 0x02, 0x01]
        print("Enabling UBX time NAV data");
        
        CK_A, CK_B = self.calculate_checksum(setNAVUBX[2:])
        setNAVUBX.append(CK_A)
        setNAVUBX.append(CK_B)

        self.sendUBX(setNAVUBX)
        self.getUBX_ACK(setNAVUBX[2:4]);

        print("Enabling UBX position NAV data");
        CK_A, CK_B = self.calculate_checksum(setNAVUBX_pos[2:])
        setNAVUBX_pos.append(CK_A)
        setNAVUBX_pos.append(CK_B)

        self.sendUBX(setNAVUBX_pos)
        self.getUBX_ACK(setNAVUBX_pos[2:4])


    def getconfig(self):
        get_cfg_message = UBX_SYNC + b'\x06\x00\x00\x00\x00\x00'

        CK_A, CK_B = 0, 0
        for i in range(4):
            CK_A = CK_A + get_cfg_message[i + 2]
            CK_B = CK_B + CK_A

        get_cfg_message[6] = CK_A
        get_cfg_message[7] = CK_B
        
        self.sendUBX(get_cfg_message)

    ####################################
    ####################################


    def getUBX_packet(self):
        receivedSync = False
        data = self.serial.read_until(expected='')

        idx = 0
        while True:

            if len(data[idx:]) > 6 and data[idx:idx+2] == UBX_SYNC:
                receivedSync = True

                ubx_packet = UBX()
                ubx_packet.read(data[idx:])

                #ubx_packet.to_string()
                #print(f"ubx_packet.id_byte : {ubx_packet.id_byte}")

                if ubx_packet.id_byte == LOG_CLASS:
                    self.parse_nav_timeutc(ubx_packet.payload)
                elif ubx_packet.id_byte == RXM_CLASS:
                    self.parse_nav_pos(ubx_packet.payload)

                idx += 6 + ubx_packet.payload_length + 2
        
            idx += 1

            if idx >= len(data):
                break

        return receivedSync


    def parse_nav_timeutc(self, payload):

        if len(payload) != 20:
            return False

        self.utc_time.year = int.from_bytes(payload[12:14], byteorder='little')
        self.utc_time.month = payload[14]
        self.utc_time.day = payload[15]
        self.utc_time.hour = payload[16]
        self.utc_time.minute = payload[17]
        self.utc_time.second = payload[18]
        self.utc_time.valid = (payload[19] == 0x07)
        
        #print(f"date : {self.utc_time.to_string()}")
        return True


    def parse_nav_pos(self, payload):

        if len(payload) != 28:
            return False

        self.location.longitude = self.extract_long(payload[4:8]) *0.0000001
        self.location.latitude = self.extract_long(payload[8:12]) *0.0000001

        return True;


    def getUBX_ACK(self, msgID):

        ackPacket = b'\xB5\x62\x05'
        receivedACK = False

        idx = 0
        data = self.serial.read_until(expected='')
        
        while True:

            if data and data[idx: idx+3] == ackPacket:

                receivedACK = True
                CK_A, CK_B = self.calculate_checksum(data[idx + 2:idx + 8])

                if msgID[0] == data[idx + 6] and msgID[1] == data[idx + 7] and \
                    CK_A == data[idx + 8] and CK_B == data[idx + 9]:
                    print("[+] ACK Received! ")
                    return 10
                else:
                    print("[-] ACK Checksum Failure: ")
                    return 1

            idx += 1

            if idx >= len(data):
                break

        if not receivedACK:
            print("[-] Did not received ACK")
            return 1


    def extract_long(self, number):
        val = 0
        #val |= number[0] << 8 * 0
        val |= number[1] << 8 * 1
        val |= number[2] << 8 * 2
        val |= number[3] << 8 * 3
        return val


    def calculate_checksum(self, data):
        CK_A, CK_B = 0, 0

        for i in range(len(data)):
            CK_A = CK_A + data[i]
            CK_B = CK_B + CK_A

        return (CK_A, CK_B)



def btohex(b):
    """ Get bytes to proper hex notation """
    return ' '.join(['{:02X}'.format(x) for x in b])
