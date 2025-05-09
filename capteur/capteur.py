import os
import random
import struct
import sx126x
import sys
import threading
import time
from helper import *
from scanner import *
from gps import *

###### MSG structure
# TYPE (1) - ID (1) - TO (1) - SIZE (1) - PAYLOAD (variable size) - CHECKSUM (2)


def listen_loop(callback, idx_payload_size, header_footer_size, sync_word):
    """ Check if data is received """
    
    buffer_receive = b''
    last_receive = 0
    
    while True:
        data = lora.receive()

        if data:
            buffer_receive += data
            last_receive = time.time()

        while True:
            idx_start = find_sync(buffer_receive, sync_word)

            if idx_start >= 0:
                buffer_receive = buffer_receive[idx_start:]

                if len(buffer_receive) > idx_payload_size:
                    expected_size = buffer_receive[idx_payload_size]
                    expected_size += header_footer_size

                    if len(buffer_receive) >= expected_size:
                        
                        packet = buffer_receive[idx_start:expected_size]
                        if params.debug:
                            print(f"expected_size {expected_size} - real size {len(packet)}")
                            log(f"expected_size {expected_size} - real size {len(packet)}")

                        callback(packet)
                        buffer_receive = buffer_receive[expected_size:]                        
                    else:
                        break
                else:
                    break
            else:
                break


        #buffer timeout to avoid misalignment of packets
        if time.time() - last_receive > 1:
            if buffer_receive and params.debug:
                print(f"timeout, lost data {buffer_receive}")
                log(f"timeout, lost data {buffer_receive}")
            buffer_receive = b''

        #time.sleep(0.05) #minimal sleep time
        time.sleep(0.1)



def callback_lora(data):
    """ Handles every message received from LoRa """
   
    if params.debug:
        print(f"callback_lora {bytes_to_hex(data)}")
        log(f"callback_lora {bytes_to_hex(data)}")



    pkt = Packet.read(data)

    msg_type = pkt.type
    msg_id = pkt.num
    msg_to = pkt.from_to
    payload = pkt.payload


    """
    msg_history = get_history_msg(msg_type=msg_type, msg_id=msg_id, msg_from_to=msg_to)

    if msg_history:
        print("msg discarded")
        return None
    """
    

    #Local node is not recipient, lets re-send it 
    if msg_to != params.local_addr and msg_to != 255:
        relay_message(data)
        return

    #Update scanner config
    if msg_type == MsgType.CONF_SCAN.value:
        
        #Update local vars
        params.frq_start = bytes_to_int(payload[0:2])
        params.frq_end = bytes_to_int(payload[2:4])
        params.threshold = struct.unpack("b", int_to_bytes(payload[4], 1))[0]
        
        #stop, set config, and start again scanner
        scanner.stop()
        scanner.set_config(frq_start=params.frq_start, frq_end=params.frq_end, threshold=params.threshold)
        scanner.activate()

        #Save config in file
        params.save_config()

        #Send back ACK + config
        data = int_to_bytes(params.frq_start, 2) + int_to_bytes(params.frq_end, 2) + struct.pack("b", params.threshold)
        
        if params.debug:
            print(f"Send ACK CONF_SCAN : {bytes_to_hex(data)}")
            log(f"Send ACK CONF_SCAN : {bytes_to_hex(data)}")


        pkt = Packet(MsgType.ACK.value, msg_id, params.local_addr, data)
        add_history(pkt)
        send_lora(pkt.build())


    #Update LoRa config
    elif msg_type == MsgType.CONF_LORA.value:

        #Not used right now
        channel = payload[0]
        air_data_rate = bytes_to_int(payload[1:3]) / 10

        lora.set_config(channel=channel,air_data_rate=air_data_rate)        

        pkt = Packet(MsgType.ACK.value, msg_id, params.local_addr)
        add_history(pkt)
        send_lora(pkt.build())


    elif msg_type == MsgType.PING.value:

        #receive broadcast PING (proabably from tester)
        if msg_to == 255:

            pkt = Packet(MsgType.ACK.value, msg_id, params.local_addr)
            add_history(pkt)
            send_lora(pkt.build())

            if params.debug:
                print(f"Send ACK PING TESTER")
                log(f"Send ACK PING TESTER")

        else:
            is_scanning = 1 if scanner.scanning else 0

            data = b''
            data += struct.pack("d", params.current_lat)
            data += struct.pack("d", params.current_lng)
            data += int_to_bytes(is_scanning, 1)
            data += int_to_bytes(params.frq_start, 2) 
            data += int_to_bytes(params.frq_end, 2)
            data += struct.pack("b", params.threshold)

            if params.debug:
                print(f"Send ACK PING")
                log(f"Send ACK PING")

            pkt = Packet(MsgType.ACK.value, msg_id, params.local_addr, data)
            add_history(pkt)
            send_lora(pkt.build())



def relay_message(data):
    """ Anytime we need to send back a message """

    (msg_type, msg_id, msg_to) = extract_header(data)

    #Check for duplicates
    key = build_key_history(data)

    if key not in params.relay_history:
        params.relay_history[key] = {"time": time.time(), "data": data, "sent": False}
        
        lora.send_bytes(data)
        
        if params.debug:
            print(f"Relai message : {bytes_to_hex(data)}")
            log(f"Relai message : {bytes_to_hex(data)}")


    
def send_lora(data):
    lora.send_bytes(data)

    if params.debug:
        print(f"send_lora : {bytes_to_hex(data)}")
        log(f"send_lora : {bytes_to_hex(data)}")

    """
    for _ in range(2):
        lora.send_bytes(data)
        time.sleep(1 + random.randint(2,6))
    """


def callback_scanner(frequency, power):
    """ Handles frequencies detection from scanner """
    frq = clean_frq(frequency, step=5)
    params.detection_history[frq] = {'time': time.time(), 'power': power}


def increment_msg_id():
    params.local_msg_id += 1
    if params.local_msg_id == 255:
        params.local_msg_id = 0



def get_history_msg(msg_type=None, msg_id=None, msg_from_to=None):
    for hist_line in params.receive_history:

        if (not msg_type or hist_line["packet"].type == msg_type) and \
            (not msg_id or hist_line["packet"].num == msg_id) and \
            (not msg_from_to or hist_line["packet"].from_to == msg_from_to):
            return hist_line

    return None



def add_history(pkt):
    msg_time = time.time()
    direction = "send"

    if params.debug:
        print(f"add_history {pkt.type} {pkt.num} {pkt.from_to}")
        log(f"add_history {pkt.type} {pkt.num} {pkt.from_to}")


    params.receive_history.append({"packet": pkt,
                                    "time": msg_time,
                                    "direction": direction})




#Entry point

if len(sys.argv) != 2:
    print(f"Usage : python {sys.argv[0]} <ID CAPTEUR>")
    exit(1)

global params
params = Parameters(debug=True)
params.local_addr = int(sys.argv[1])

if params.debug:
    print("Start capteur")
    log("Start capteur")

if os.path.isfile("config.json"):
    params.load_config()
else:
    params.save_config()

lora = sx126x.sx126x(port="/dev/ttyS0", debug=params.debug)

if not lora.ready:
    print("LoRa NOT ready ! reboot...")
    log("LoRa NOT ready ! reboot...")
    os.system("sudo reboot")

lora.set_config(channel=params.channel,network=0, tx_power=22, 
                air_data_rate=params.air_data_rate, 
                sub_packet_size=params.sub_packet_size)

is_running = True

t_receive = threading.Thread(target=listen_loop, 
        args=[callback_lora, params.idx_payload_size, 
        params.header_size + params.footer_size, params.sync_word])
t_receive.start()


#Scanner init
scanner = scanner(callback=callback_scanner, debug=False)

#frq_start=400, frq_end=420, gain=49, sample_rate=2000000, ppm=0, repeats=64, threshold=-10, bins=512, dev_index=0
scanner.set_config(frq_start=params.frq_start, frq_end=params.frq_end, threshold=params.threshold)
scanner.activate(blocking=False)


#GPS init

gps = VMA430()
gps.begin(port="/dev/ttyAMA2", baudrate=9600, debug=False)
gps.set_nav_mode('stationary')

last_gps = 0
gps_online = gps.activate_poll()

#Main loop
while True:

    #gps
    if time.time() - last_gps > params.delay_gps:
        
        #keep trying to set it online
        if not gps_online:
            gps_online = gps.activate_poll()

            if params.debug:
                print(f"gps_online : {gps_online}")

        else:
            #when online, get position
            gps.location = Location()
            gps.utc_time = Time_UTC()

            packets = gps.get_ubx_packet()
            for p in packets:
                gps.handle_ubx_packet(p)

            if gps.location.latitude and gps.location.longitude:
                fix_3d, gnss_fix_ok, correction_applied = gps.check_pos_validity()

                if fix_3d:
                    params.current_lat = gps.location.latitude
                    params.current_lng = gps.location.longitude

                    if params.debug:
                        print(f"lat : {params.current_lat} / lng {params.current_lng}")
                        log(f"lat : {params.current_lat} / lng {params.current_lng}")

            if not params.time_set and gps.utc_time.datetime and gps.utc_time.valid:

                if params.debug:
                    print(f"datetime {gps.utc_time.datetime}")
                    log(f"datetime {gps.utc_time.datetime}")

                set_system_date(gps.utc_time.datetime)
                params.time_set = True

        last_gps = time.time()


    #filter out detections
    frq_max, pwr_max = 0,-120

    for frq, val in params.detection_history.copy().items():
        if time.time() - val["time"] > params.delay_detection:
            if val["power"] > pwr_max:
                frq_max = frq
                pwr_max = val["power"]
            del params.detection_history[frq]


    if frq_max != 0 and pwr_max != -120:
        send = True

        #avoid sending again a close and/or recent frequency
        for hist_frq in params.send_history:
            hist_time = params.send_history[hist_frq]

            if frq_max >= hist_frq - params.range_duplicate and \
                frq_max <= hist_frq + params.range_duplicate and \
                time.time() - hist_time < params.delay_duplicate:
                send = False
                break

        if send:
            params.send_history[frq_max] = time.time()

            data = b''
            data += int_to_bytes(frq_max, 4)
            #pwr = abs(int(pwr_max * 100))
            data += struct.pack("e", pwr_max)

            if params.debug:
                print(f"sending {frq_max} / {pwr_max}")
                log(f"sending {frq_max} / {pwr_max}")

            pkt = Packet(MsgType.FRQ.value, params.local_msg_id, params.local_addr, data)
            add_history(pkt)
            send_lora(pkt.build())

            increment_msg_id()


    #clean send_history queue
    for key, val in params.send_history.copy().items():
        if time.time() - val > params.delay_duplicate: 
            del params.send_history[key]

    #send relay messages and clean relay_history queue
    for key, val in params.relay_history.copy().items():
        diff_time = time.time() - val["time"]
        
        if diff_time > 0.5 and val["sent"] == False:
            lora.send_bytes(val["data"])
            time.sleep(0.1)
            val["sent"] = True

        if diff_time > 60:
            del params.relay_history[key]

    """
    #clean receive_history queue
    for key, val in params.receive_history.copy().items():
        if time.time() - val > params.delay_receive: 
            del params.receive_history[key]

    params.receive_history = [x for x in params.receive_history if x[]]
    """

    time.sleep(0.1)


scanner.stop()
lora.stop()
thread_lora.join()
