import serial
import time
from gpiozero import LED


class sx126x():

    #
    # Possible values for every settings
    #

    SERIAL_PORT_RATE = {1200 : 0b00000000, 2400 : 0b00100000, 4800 : 0b01000000, 9600 : 0b01100000, 19200 : 0b10000000, 38400 : 0b10100000, 57600 : 0b11000000, 115200 : 0b11100000 }
    SERIAL_PARITY_BIT = {'8N1' : 0b00000000, '8O1' : 0b00001000, '8E1' : 0b00010000 } #serial.PARITY_NONE - 8N1, serial.PARITY_ODD - 8O1, serial.PARITY_EVEN - 8E1
    AIR_DATA_RATE = {0.3 : 0b00000000, 1.2 : 0b00000001, 2.4 : 0b00000010, 4.8 : 0b00000011, 9.6 : 0b00000100, 19.2 : 0b00000101, 38.4 : 0b00000110, 62.5 : 0b00000111 }
    SUB_PACKET_SIZE = {240 : 0b00000000, 128 : 0b01000000, 64 : 0b10000000, 32 : 0b11000000 }
    CHANNEL_NOISE = {'disabled' : 0b00000000, 'enabled' : 0b00100000 }
    TX_POWER = {22 : 0b00000000, 17 : 0b00000001, 13 : 0b00000010, 10 : 0b00000011 }
    ENABLE_RSSI = {'disabled' : 0b00000000, 'enabled' : 0b10000000 }
    TRANSMISSION_MODE = {'fixed' : 0b01000000, 'transparent' : 0b000000000 }
    ENABLE_REPEATER = {'disabled' : 0b00000000, 'enabled' : 0b00100000 }
    ENABLE_LBT = {'disabled' : 0b00000000, 'enabled' : 0b00010000 }
    WOR_CONTROL = {'transmitter' : 0b00001000, 'receiver' : 0b00000000 }
    WOR_CYCLE = {500 : 0b00000000, 1000 : 0b00000001, 1500 : 0b00000010, 2000 : 0b00000011, 2500 : 0b00000100, 3000 : 0b00000101, 3500 : 0b00000110, 4000 : 0b00000111 }

    #
    # Init : the module is reading the chip current settings and accordingly fill local variables
    #

    """
    address=100, network=0, channel=18, tx_power=22, enable_rssi=False,
    air_data_rate=2.4, sub_packet_size=240, key=0,
    repeater='none', netid1=0, netid2=0, debug=False
    """
    
    def __init__(self, **kwargs):
        """ Constructor """
   
        self.__set_config_serial()
        self.serial = self.__open_serial()
        self.debug = True if "debug" in kwargs and kwargs['debug'] else False 

        self.M0 = LED("GPIO22")
        self.M1 = LED("GPIO27")

        if kwargs:
            self.set_config(**kwargs)
            self.write_config()
        else:
            print("reading config")
            arr = self.read_config()

            if arr:
                #Fill class variables with config currently applied to chip
                self.set_config(address=arr[0], network=arr[1], channel=arr[8], tx_power=arr[7], enable_rssi=arr[9],
                        air_data_rate=arr[4], sub_packet_size=arr[5], key=0,
                        repeater='none', netid1=0, netid2=0)
            else:
                print("[-] Error reading config")


    #
    # Serial
    #

    def __set_config_serial(self, port="/dev/ttyS0", serial_port_rate=9600,
                            timeout=1, serial_parity_bit=serial.PARITY_NONE):
        """ Set serial related class variables """

        self.port = port
        self.serial_port_rate = serial_port_rate
        self.timeout = timeout
        self.serial_parity_bit = serial_parity_bit
        self.lora_parity_bit = self.__convert_serial_parity(self.serial_parity_bit)


    def __open_serial(self):
        """ Tries to open serial port. Will try ttyS0 and AMA0. Return serial variable or None if failed """

        #/dev/ttyAMA0

        return serial.Serial(port=self.port, baudrate=self.serial_port_rate,
                    parity=self.serial_parity_bit, stopbits=serial.STOPBITS_ONE,
                    bytesize=serial.EIGHTBITS, timeout=self.timeout)


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


    def __convert_serial_parity(self,parity):
        if parity == serial.PARITY_ODD:
            return "8O1"
        elif parity == serial.PARITY_EVEN:
            return "8E1"
        else: #serial.PARITY_NONE
            return "8N1"


    #
    # Bytes manipulation
    #


    def __bytes_pair_to_int(self, b1, b2):
        """ Create a 16bit integer from two 8bit integers. Useful to get two numbers in a single register """
        return (b1 << 8) + b2


    def __btohex(self, b):
        """ Get bytes to proper hex notation """
        return ' '.join(['{:02X}'.format(x) for x in b])


    #
    # Send and receive data
    #

    def send_bytes(self, data):
        """ Send bytes through serial. Check if data is bytes """
        
        if not isinstance(data, bytes):
            print("[!] Data parameter must be bytes")
            return

        if self.debug:
            print(f'[+] SENDING {self.__btohex(data)}')
            print(f'[+] SENDING {data}')
        
        self.serial.write(data)
        time.sleep(0.01)


    def send_string(self, data):
        """ Send string through serial. Check if data is string and .encode() it """

        if not isinstance(data, str):
            print("[!] Data parameter must be str")
            return

        self.send_bytes(data.encode())


    def receive(self):
        """ Check if data is received """

        data = self.serial.read_until(expected='')

        if not data:
            data = None
        elif self.debug:
            print(f'[+] RECEIVED {len(data)} bytes')
            print(f'[+] {self.__btohex(data)}')
            print(f'[+] {data}')

        return data


    #
    # LoRa config
    #

    def __set_mode(self, mode):
        """ Set the LoRa HAT mode from software instead using the card's jumpers """
        if mode == 'conf':
            self.M0.off()
            self.M1.on()
        elif mode == 'wor':
            self.M0.on()
            self.M1.off()
        elif mode == 'sleep':
            self.M0.on()
            self.M1.on()
        else: #transmission mode
            self.M0.off()
            self.M1.off()

        time.sleep(0.1)


    def show_config(self):
        """ Print some useful config variables to help debug """
        print(f'[+] Channel {self.channel}, address {self.logicalAddress}, network {self.network}, key {self.key}')
        x = self.address.to_bytes(2, 'big')
        print(f'[+] Mode {self.transmission_mode}, real address {self.address} ({x}), repeater {self.enable_repeater}')


    def set_config(self, address=100, network=0, channel=18, tx_power=22, enable_rssi=False,
                    air_data_rate=2.4, sub_packet_size=240, key=0,
                    repeater='none', netid1=0, netid2=0, debug=False):
        """ Update class internals variables. This method DOES NOT update chip's registers """
        
        self.channel = channel
        self.key = key
        self.network = network
        self.logicalAddress = address

        self.air_data_rate = air_data_rate
        self.sub_packet_size = sub_packet_size
        self.channel_noise = 'disabled' #current noise + last message's db on request
        self.tx_power = tx_power
        self.enable_rssi = 'enabled' if enable_rssi else 'disabled' #every message get one more byte for RSSI
        self.enable_lbt = 'disabled'
        self.wor_control = 'transmitter'
        self.wor_cycle = 2000

        if repeater == "server":
            self.transmission_mode = 'fixed'
            self.address = self.__bytes_pair_to_int(netid1, netid2)
            self.enable_repeater = 'enabled'
        elif repeater == "client":
            self.transmission_mode = 'fixed'
            self.address = address
            self.enable_repeater = 'disabled'
        else: #none
            self.transmission_mode = 'transparent'
            self.address = 65535
            self.enable_repeater = 'disabled'


    def factory_reset(self):
        """ Request factory reset to the chip. NOT TESTED YET """
        config = bytearray(b'\xC0\x00\x09\x12\x34\x00\x61')
        ret = self.send_config(bytes(config))
        return ret


    def read_config(self):
        """ Request config read to the chip. Returns refined array containing human readable values """
        config = bytearray(b'\xC1\x00\x09')
        ret = self.send_config(bytes(config))

        if ret == b'\xff\xff\xff' or not ret:
            return None

        return self.config_bytes_to_arr(ret[3:])


    def config_bytes_to_arr(self, arr):
        """ Transform byte array to array of human readable values """

        addrh = arr[0]
        addrl = arr[1]
        addr = self.__bytes_pair_to_int(addrh, addrl)
        netid = arr[2]
        tmp = f'{arr[3]:0>8b}'
        
        serial_port_rate = [k for k, v in self.SERIAL_PORT_RATE.items() if v == int(tmp[:3], 2) << 5][0]
        serial_parity_bit = [k for k, v in self.SERIAL_PARITY_BIT.items() if v == int(tmp[3:5], 2) << 3][0]
        air_data_rate = [k for k, v in self.AIR_DATA_RATE.items() if v == int(tmp[5:], 2)][0]
        tmp = f'{arr[4]:0>8b}'
        sub_packet_size = [k for k, v in self.SUB_PACKET_SIZE.items() if v == int(tmp[:2], 2) << 6][0]
        channel_noise = [k for k, v in self.CHANNEL_NOISE.items() if v == int(tmp[2:3], 2) << 5][0]
        tx_power = [k for k, v in self.TX_POWER.items() if v == int(tmp[6:], 2)][0]
        channel = arr[5]
        tmp = f'{arr[6]:0>8b}'
        enable_rssi = [k for k, v in self.ENABLE_RSSI.items() if v == int(tmp[:1], 2) << 7][0]
        transmission_mode = [k for k, v in self.TRANSMISSION_MODE.items() if v == int(tmp[1:2], 2) << 6][0]
        enable_repeater = [k for k, v in self.ENABLE_REPEATER.items() if v == int(tmp[2:3], 2) << 5][0]
        enable_lbt = [k for k, v in self.ENABLE_LBT.items() if v == int(tmp[3:4], 2) << 4][0]
        wor_mode = [k for k, v in self.WOR_CONTROL.items() if v == int(tmp[4:5], 2) << 3][0]
        wor_cycle = [k for k, v in self.WOR_CYCLE.items() if v == int(tmp[5:], 2)][0]
        crypth = arr[7]
        cryptl = arr[8]
        crypt = self.__bytes_pair_to_int(crypth, cryptl)

        return [addr, netid, serial_port_rate, serial_parity_bit, air_data_rate,
                sub_packet_size, channel_noise, tx_power, channel, enable_rssi, transmission_mode,
                enable_repeater, enable_lbt, wor_mode, wor_cycle, crypt]



    def write_config(self):
        """ Write current class variables to chip's registers """

        RESERVE = 0b00000000

        #C0 = config, 00 = start address, 09 = length
        config = bytearray(b'\xC0\x00\x09')

        address_tmp = self.address.to_bytes(2, 'big')
        config.append(address_tmp[0])
        config.append(address_tmp[1])

        config.append(self.network)

        config.append(self.SERIAL_PORT_RATE[self.serial_port_rate] +
                      self.SERIAL_PARITY_BIT[self.lora_parity_bit] +
                      self.AIR_DATA_RATE[self.air_data_rate])


        config.append(self.SUB_PACKET_SIZE[self.sub_packet_size] +
                      self.CHANNEL_NOISE[self.channel_noise] +
                      RESERVE +
                      self.TX_POWER[self.tx_power])
        
        config.append(self.channel)

        config.append(self.ENABLE_RSSI[self.enable_rssi] +
                      self.TRANSMISSION_MODE[self.transmission_mode] +
                      self.ENABLE_REPEATER[self.enable_repeater] +
                      self.ENABLE_LBT[self.enable_lbt] +
                      self.WOR_CONTROL[self.wor_control] +
                      self.WOR_CYCLE[self.wor_cycle])

        key_tmp = self.key.to_bytes(2, 'big')
        config.append(key_tmp[0])
        config.append(key_tmp[1])
        
        self.send_config(bytes(config))


    def send_config(self, data):
        """ Send bytes to chip and returns chip's response """

        self.__set_mode('conf')
        
        self.serial.write(data)
        time.sleep(0.5)
        ret = self.serial.read_until(expected='')
        
        if self.debug:
            print(f"[+] Config sent {self.__btohex(data)}")
            print(f"[+] Config recv {self.__btohex(ret)}")

            if ret == b'\xff\xff\xff':
                print("[-] CONFIG ERROR")

        self.__set_mode('')
        return ret

    #
    # LoRa chip utilities
    #

    def getRSSI(self):
        """ Send bytes to chip and returns chip's response """
        
        if self.channel_noise == 'disabled':
            return

        self.serial.write(b'\xC0\xC1\xC2\xC3\x00\x02')
        
        ret = self.serial.read_until(expected='')

        currentNoise = ret[3]
        lastReceive = ret[4]

        return currentNoise, lastReceive

    #
    # Miscellanous
    #

    def str_hex_to_bytes(self, txt):
        """ Transform hex string to bytes """
        txt = txt.replace(' ', '')
        return bytes.fromhex(txt)

    def close(self):
        self.serial.close()
