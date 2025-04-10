import serial
import threading
import time
from gpiozero import LED, OutputDevice

class sx126x():

    #
    # Possible values for every settings
    #

    SERIAL_PORT_RATE = {1200 : 0b00000000, 2400 : 0b00100000, 4800 : 0b01000000, 9600 : 0b01100000, 19200 : 0b10000000, 38400 : 0b10100000, 57600 : 0b11000000, 115200 : 0b11100000 }
    SERIAL_PARITY_BIT = {"8N1" : 0b00000000, "8O1" : 0b00001000, "8E1" : 0b00010000 }
    AIR_DATA_RATE = {0.3 : 0b00000000, 1.2 : 0b00000001, 2.4 : 0b00000010, 4.8 : 0b00000011, 9.6 : 0b00000100, 19.2 : 0b00000101, 38.4 : 0b00000110, 62.5 : 0b00000111 }
    SUB_PACKET_SIZE = {240 : 0b00000000, 128 : 0b01000000, 64 : 0b10000000, 32 : 0b11000000 }
    CHANNEL_NOISE = {"disabled" : 0b00000000, "enabled" : 0b00100000 }
    TX_POWER = {22 : 0b00000000, 17 : 0b00000001, 13 : 0b00000010, 10 : 0b00000011 }
    ENABLE_RSSI = {"disabled" : 0b00000000, "enabled" : 0b10000000 }
    TRANSMISSION_MODE = {"fixed" : 0b01000000, "transparent" : 0b000000000 }
    ENABLE_REPEATER = {"disabled" : 0b00000000, "enabled" : 0b00100000 }
    ENABLE_LBT = {"disabled" : 0b00000000, "enabled" : 0b00010000 }
    WOR_CONTROL = {"transmitter" : 0b00001000, "receiver" : 0b00000000 }
    WOR_CYCLE = {500 : 0b00000000, 1000 : 0b00000001, 1500 : 0b00000010, 2000 : 0b00000011, 2500 : 0b00000100, 3000 : 0b00000101, 3500 : 0b00000110, 4000 : 0b00000111 }
    BROADCAST_MONITORING_ADDRESS = 65535
    
    #
    # Init : the module is reading the chip current settings and accordingly fill local variables
    #

    def __init__(self, port="/dev/ttyAMA0", baudrate=9600, debug=False):
        """ Constructor : init vars, open serial and read chip's current settings """

        self.default_params = {"addrh" : 0, "addrl": 0, "network": 0, "air_data_rate": 2.4,
                        "sub_packet_size": 240, "channel_noise": "disabled", "tx_power": 22,
                        "channel": 18, "enable_rssi": "disabled", "transmission_mode": "transparent",
                        "enable_repeater": "disabled", "enable_lbt": "disabled", "wor_control": "receiver",
                        "wor_cycle": 2000, "crypth": 0, "cryptl": 0 }

        self.serial_params = {"port": port, "baudrate": 9600, "parity": serial.PARITY_NONE, 
                                "stopbits": serial.STOPBITS_ONE, "bytesize": serial.EIGHTBITS}

        self.t_receive = None
        self.conf_mode = False
        self.params = self.default_params
        self.debug = debug
        self.ready = True

        self.M0 = LED("GPIO22")
        self.M1 = LED("GPIO27")

        self.serial = self.__open_serial(port=self.serial_params["port"], timeout=1)
        
        #Due to some weird bug (only on Rpi5) we need to close and reopen serial
        time.sleep(0.2)
        self.serial.close()
        time.sleep(0.2)
        self.serial.open()
                
        self.serial.read(self.serial.in_waiting)
        read_params = self.read_registers()

        if self.debug:
            print("[+] Reading registers")
            print(read_params)

        #Fill class variables with config currently applied to chip
        if read_params:
            self.set_config(addrh=read_params['addrh'], addrl=read_params['addrl'], network=read_params['network'], 
                            air_data_rate=read_params['air_data_rate'], sub_packet_size=read_params['sub_packet_size'],
                            channel_noise=read_params['channel_noise'], tx_power=read_params['tx_power'], 
                            channel=read_params['channel'], enable_rssi=read_params['enable_rssi'], 
                            transmission_mode=read_params['transmission_mode'], enable_repeater=read_params['enable_repeater'], 
                            enable_lbt=read_params['enable_lbt'], wor_control=read_params['wor_control'], 
                            wor_cycle=read_params['wor_cycle'], crypth=read_params['crypth'], cryptl=read_params['cryptl'],
                            use_logical_address=read_params["use_logical_address"], serial_port_rate=read_params["serial_port_rate"],
                            write_registers=False)
        else:
            print("[-] Error reading config")
            self.ready = False


    #
    # Serial
    #

    def serial_state(self):
        """ Print serial infos for debug """
        print(f"{self.serial.name} {self.serial.is_open} {self.serial.baudrate}")
        print(f"{self.serial.get_settings()}")
        

    def reset_buffers(self):
        """ Reset serial buffers for debug """
        self.serial.reset_input_buffer()
        self.serial.reset_output_buffer()
        self.serial.flush()


    def __open_serial(self, port, timeout=1):
        """ Tries to open serial port """

        return serial.Serial(port=port, 
                    baudrate=self.serial_params["baudrate"],
                    parity=self.serial_params["parity"], 
                    stopbits=self.serial_params["stopbits"],
                    bytesize=self.serial_params["bytesize"], timeout=timeout)


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


    def __int_to_bytes_pair(self, b):
        """ Return two 8bit integers from a 16bit integer """
        return b.to_bytes(2, "big")


    def __bytes_pair_to_int(self, b1, b2):
        """ Create a 16bit integer from two 8bit integers. Useful to get two numbers in a single register """
        return (b1 << 8) + b2


    def __btohex(self, b):
        """ Get bytes to proper hex notation """
        return " ".join(["{:02X}".format(x) for x in b])


    #
    # Send and receive data
    #

    def send_bytes(self, data):
        """ Send bytes through serial. Check if data is bytes """
        
        if not isinstance(data, bytes):
            print("[!] Data parameter must be bytes")
            return

        if self.debug:
            print(f"[+] SENDING {len(data)} bytes : {self.__btohex(data)}")
        
        self.serial.write(data)
        time.sleep(0.05) #minimal sleep time


    def send_string(self, data):
        """ Send string through serial. Check if data is string and .encode() it """

        if not isinstance(data, str):
            print("[!] Data parameter must be str")
            return

        self.send_bytes(data.encode())


    def receive(self):
        """ Check if data is received """

        #safety to make sure we receive conf ACK
        if self.conf_mode:
            return None

        data = self.serial.read(self.serial.in_waiting)

        if data and self.debug:
            print(f"[+] RECEIVED {len(data)} bytes : {self.__btohex(data)}")

        return data


    def listen_loop(self, callback):
        while self.running_listen:            
            data = self.receive()

            if data:
                callback(data)

            time.sleep(0.05) #minimal sleep time


    def listen(self, callback):
        
        self.running_listen = True
        self.t_receive = threading.Thread(target=self.listen_loop, args=[callback])
        self.t_receive.start()


    #
    # LoRa config
    #

    def set_mode(self, mode):
        """ Set the LoRa HAT mode from software instead using the card"s jumpers """

        if self.debug:
            print(f"[+] Setting mode {mode}")

        self.conf_mode = False

        if mode == "conf":
            self.conf_mode = True
            self.M0.off()
            self.M1.on()
        elif mode == "wor":
            self.M0.on()
            self.M1.off()
        elif mode == "sleep":
            self.M0.on()
            self.M1.on()
        else: #transmission mode
            self.M0.off()
            self.M1.off()


        #We need to use baudrate 9600 to config
        if self.conf_mode:
            if self.serial_params["baudrate"] != 9600:
                self.serial.baudrate = 9600
        else:
            if self.serial_params["baudrate"] != 9600:
                self.serial.baudrate = self.serial_params["baudrate"]

        time.sleep(0.1)


    def show_config(self):
        """ Print some useful config variables to help debug """
        print(f"addrh {self.params['addrh']}, addrl {self.params['addrl']}")
        print(f"[+] channel {self.params['channel']}, network {self.params['network']}, crypth {self.params['crypth']}, cryptl {self.params['cryptl']}")        
        print()
        print(f"[+] params {self.params}")
        print()


    def set_repeater(self, mode, client_address=None, repeater_netid1=None, repeater_netid2=None):
        """ Helper to enable repeater mode """

        if mode == "server":
            self.params["transmission_mode"] = "fixed"
            self.params["addrh"] = repeater_netid1
            self.params["addrl"] = repeater_netid2
            self.params["enable_repeater"] = "enabled"

        elif mode == "client":
            self.params["transmission_mode"] = "fixed"
            address_tmp = self.__int_to_bytes_pair(address)
            self.params["addrh"] = address_tmp[0]
            self.params["addrl"] = address_tmp[1]
            self.params["enable_repeater"] = "disabled"

        self.write_registers()


    def set_config(self, addrh=None, addrl=None, network=None, air_data_rate=None, sub_packet_size=None,
                        channel_noise=None, tx_power=None, channel=None, enable_rssi=None, 
                        transmission_mode=None, enable_repeater=None, enable_lbt=None,
                        wor_control=None, wor_cycle=None, crypth=None, cryptl=None,
                        use_logical_address=True, serial_port_rate=9600, write_registers=True):
                  
        """ Human readable settings from user are processed into internal parameters. """

        if addrh is not None: self.params["addrh"] = addrh
        if addrl is not None: self.params["addrl"] = addrl
        if network is not None: self.params["network"] = network
        if air_data_rate: self.params["air_data_rate"] = air_data_rate
        if sub_packet_size: self.params["sub_packet_size"] = sub_packet_size
        if channel_noise is not None: self.params["channel_noise"] = "enabled" if channel_noise == 'enabled' or channel_noise == True else "disabled"
        if tx_power: self.params["tx_power"] = tx_power
        if channel is not None: self.params["channel"] = channel
        if enable_rssi is not None: self.params["enable_rssi"] = "enabled" if enable_rssi == 'enabled' or enable_rssi == True else "disabled"
        if transmission_mode: self.params["transmission_mode"] = transmission_mode
        if enable_repeater is not None: self.params["enable_repeater"] = "enabled" if enable_repeater == 'enabled' or enable_repeater == True else "disabled"
        if enable_lbt is not None: self.params["enable_lbt"] = "enabled" if enable_lbt == 'enabled' or enable_lbt == True else "disabled"
        if wor_control: self.params["wor_control"] = wor_control
        if wor_cycle: self.params["wor_cycle"] = wor_cycle
        if crypth is not None: self.params["crypth"] = crypth
        if cryptl is not None: self.params["cryptl"] = cryptl

        if serial_port_rate != 9600:
            self.serial_params["baudrate"] = serial_port_rate

        if use_logical_address:
            address_tmp = self.__int_to_bytes_pair(self.BROADCAST_MONITORING_ADDRESS)
            self.params["addrh"] = address_tmp[0]
            self.params["addrl"] = address_tmp[1]

        if write_registers:
            self.write_registers()


    def factory_reset(self):

        self.params = self.default_params
        self.write_registers()

        """ Request factory reset to the chip. NOT TESTED YET 
        config = bytearray(b"\xC0\x00\x09\x12\x34\x00\x61")
        ret = self.write_serial(bytes(config))
        return ret
        """


    def read_registers(self):
        """ Request config read to the chip. Returns refined array containing human readable values """

        def registers_to_params(arr):
            """ Transform byte array to array of human readable values """

            addrh = arr[0]
            addrl = arr[1]
            network = arr[2]
            tmp = f"{arr[3]:0>8b}"
            
            serial_port_rate = [k for k, v in self.SERIAL_PORT_RATE.items() if v == int(tmp[:3], 2) << 5][0]
            serial_parity_bit = [k for k, v in self.SERIAL_PARITY_BIT.items() if v == int(tmp[3:5], 2) << 3][0]
            air_data_rate = [k for k, v in self.AIR_DATA_RATE.items() if v == int(tmp[5:], 2)][0]
            tmp = f"{arr[4]:0>8b}"
            sub_packet_size = [k for k, v in self.SUB_PACKET_SIZE.items() if v == int(tmp[:2], 2) << 6][0]
            channel_noise = [k for k, v in self.CHANNEL_NOISE.items() if v == int(tmp[2:3], 2) << 5][0]
            tx_power = [k for k, v in self.TX_POWER.items() if v == int(tmp[6:], 2)][0]
            channel = arr[5]
            tmp = f"{arr[6]:0>8b}"
            enable_rssi = [k for k, v in self.ENABLE_RSSI.items() if v == int(tmp[:1], 2) << 7][0]
            transmission_mode = [k for k, v in self.TRANSMISSION_MODE.items() if v == int(tmp[1:2], 2) << 6][0]
            enable_repeater = [k for k, v in self.ENABLE_REPEATER.items() if v == int(tmp[2:3], 2) << 5][0]
            enable_lbt = [k for k, v in self.ENABLE_LBT.items() if v == int(tmp[3:4], 2) << 4][0]
            wor_control = [k for k, v in self.WOR_CONTROL.items() if v == int(tmp[4:5], 2) << 3][0]
            wor_cycle = [k for k, v in self.WOR_CYCLE.items() if v == int(tmp[5:], 2)][0]
            crypth = arr[7]
            cryptl = arr[8]

            #"serial_parity_bit": serial.PARITY_NONE, 

            use_logical_address = addrh == 255 and addrl == 255

            return {"serial_port_rate": serial_port_rate, "addrh" : addrh, "addrl": addrl, "network": network, "air_data_rate": air_data_rate,
                    "sub_packet_size": sub_packet_size, "channel_noise": channel_noise, "tx_power": tx_power,
                    "channel": channel, "enable_rssi": enable_rssi, "transmission_mode": transmission_mode,
                    "enable_repeater": enable_repeater, "enable_lbt": enable_lbt, "wor_control": wor_control,
                    "wor_cycle": wor_cycle, "crypth": crypth, "cryptl": cryptl, "use_logical_address": use_logical_address}

            
            #end registers_to_params

        config = bytearray(b"\xC1\x00\x09")
        ret = self.write_serial(bytes(config))

        if ret == b"\xff\xff\xff" or not ret:
            return None

        return registers_to_params(ret[3:])


    def write_registers(self):
        """ Write current class variables to chip"s registers """

        RESERVE = 0b00000000

        #C0 = config, 00 = start address, 09 = length
        config = bytearray(b"\xC0\x00\x09")

        config.append(self.params["addrh"])
        config.append(self.params["addrl"])

        config.append(self.params["network"])

        lora_parity_bit = self.__convert_serial_parity(self.serial_params["parity"])
        config.append(self.SERIAL_PORT_RATE[self.serial_params["baudrate"]] +
                      self.SERIAL_PARITY_BIT[lora_parity_bit] +
                      self.AIR_DATA_RATE[self.params["air_data_rate"]])


        config.append(self.SUB_PACKET_SIZE[self.params["sub_packet_size"]] +
                      self.CHANNEL_NOISE[self.params["channel_noise"]] +
                      RESERVE +
                      self.TX_POWER[self.params["tx_power"]])
        
        config.append(self.params["channel"])

        config.append(self.ENABLE_RSSI[self.params["enable_rssi"]] +
                      self.TRANSMISSION_MODE[self.params["transmission_mode"]] +
                      self.ENABLE_REPEATER[self.params["enable_repeater"]] +
                      self.ENABLE_LBT[self.params["enable_lbt"]] +
                      self.WOR_CONTROL[self.params["wor_control"]] +
                      self.WOR_CYCLE[self.params["wor_cycle"]])

        config.append(self.params["crypth"])
        config.append(self.params["cryptl"])
        
        self.write_serial(bytes(config))


    def write_serial(self, data):
        """ Send bytes to chip and returns chip"s response """

        self.set_mode("conf")
        self.serial.write(data)

        time.sleep(0.1)
        ret = self.serial.read(self.serial.in_waiting)        
        
        idx_start = self.find_sync(ret, b"\xC1\x00\x09")

        if idx_start >= 0 and len(ret[idx_start:]) == idx_start+12:
            ret = ret[idx_start:idx_start+12]
        else:
            ret = b"\xff\xff\xff"


        if self.debug:
            print(f"[+] Config sent {self.__btohex(data)}")
            print(f"[+] Config recv {self.__btohex(ret)}")

            if ret == b"\xff\xff\xff":
                print("[-] CONFIG ERROR")

        self.set_mode("transmission")
        return ret

    #
    # LoRa chip utilities
    #


    def get_channel_noise(self):
        """ Request current channel noise and last message"s RSSI """
        #Chip needs to be in transmitting or WOR mode

        if self.params["channel_noise"] == "disabled":
            return None

        self.conf_mode = True

        self.serial.write(b"\xC0\xC1\xC2\xC3\x00\x02")
        time.sleep(0.1)

        ret = self.serial.read(self.serial.in_waiting)
        self.conf_mode = False

        channel_noise = ret[3]
        last_rssi = ret[4]

        return channel_noise, last_rssi


    def close(self):

        if self.debug:
            print("[+] Closing")

        if self.t_receive:
            self.running_listen = False
            self.t_receive.join()

        self.M0.close()
        self.M1.close()

        self.serial.close()

    #
    # Miscellanous
    #

    def find_sync(self, data, sync_word, idx_start=0):
        if not data:
            return -1

        for idx in range(idx_start, len(data)):
            if data[idx:idx+len(sync_word)] == sync_word:
                return idx

        return -1

    def str_hex_to_bytes(self, txt):
        """ Transform hex string to bytes """
        txt = txt.replace(" ", "")
        return bytes.fromhex(txt)


    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    @staticmethod
    def channel_to_frequency(channel):
        return 850_125_000 + (channel * 1_000_000)

    @staticmethod
    def frequency_to_channel(frequency):
        return (frequency - 850_125_000) / 1_000_000
