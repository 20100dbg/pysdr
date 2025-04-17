import gevent
import json
import os
import sqlite3
import struct
import sx126x
import threading
import time
from datetime import datetime
from flask import Flask, request, make_response
from flask_socketio import SocketIO, emit
from gps import *
from helper import *

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='gevent')

############

#receive_history 
#[{id:xx, type:xx, to:xx, time:xx}]


##################
#
# Routing
#
##################


@app.route("/")
def main():
    """ Main page : we open or refresh the app"""

    #Retrieve detections in database
    cursor.execute("""SELECT module_id, dt, frq, pwr,
                    latitude, longitude
                    FROM detection 
                    INNER JOIN module ON detection.module_id = module.id""")
    detections = cursor.fetchall()

    #Retrieve modules in database
    cursor.execute("SELECT id, frq_start, frq_end, threshold, latitude, longitude, last_ping, config_applied FROM module")
    modules = cursor.fetchall()

    if params.debug:
        print(f"in main() /  {len(detections)} detections / {len(modules)} modules ")
        log(f"in main() /  {len(detections)} detections / {len(modules)} modules ")

    #Insert data into HTML template
    tpl = open('templates/main.html', 'r').read()
    tpl = tpl.replace('{{modules}}', json.dumps(modules))
    tpl = tpl.replace('{{detections}}', json.dumps(detections))

    #Send back HTTP response
    response = make_response(tpl)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/download")
def download():
    """ Download data as CSV file """

    cursor.execute("SELECT module_id, dt, frq FROM detection")
    rows = cursor.fetchall()
    csv = 'module;gdh;frq\n'

    for row in rows:
        dt = datetime.fromtimestamp(row[1])
        frq = pretty_frq(row[2])
        csv += f'{row[0]};{dt};{frq}\n'

    current_dt = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    response = make_response(csv)
    response.headers["Content-Disposition"] = f'attachment; filename="{current_dt}_activite.csv"'
    response.headers["Content-Type"] = f'text/csv'
    response.headers["Pragma"] = "public"
    response.headers["Cache-Control"] = "must-revalidate, post-check=0, pre-check=0"
    return response


@socketio.on('config')
def config(args):
    """ Receive config update for a module"""
    module_id = int(args['module_id'])
    frq_start = int(args['frq_start'])
    frq_end = int(args['frq_end'])
    threshold = int(args['threshold'])
    
    if params.debug:
        print(f"in config() / args {args}")
        log(f"in config() / args {args}")


    #update DB
    cursor.execute(f"UPDATE module SET frq_start='{frq_start}', frq_end='{frq_end}', \
                        threshold='{threshold}', config_applied=false \
                        WHERE id={module_id}")
    db.commit()

    #Send config to module via LoRa
    data = int_to_bytes(frq_start, 2) + int_to_bytes(frq_end, 2) + struct.pack("b", threshold)
    pkt = Packet(MsgType.CONF_SCAN.value, params.local_msg_id, module_id, data)

    add_history(pkt)
    lora.send_bytes(pkt.build())

    increment_msg_id()



@socketio.on('set_nb_module')
def set_nb_module(nb_module):
    """ At startup and manually, client defines how many modules are used. """
    """ We assume for X modules, modules are always identified by ID 1,2,3...X """

    cursor.execute(f'DELETE FROM module')
    db.commit()
    
    #id frq_start frq_end threshold latitude longitude last_ping config_applied
    data = [(module_id, 400, 420, -10, 0, 0, 0, True) for module_id in range(1, nb_module+1)]
    cursor.executemany("INSERT INTO module VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data)
    db.commit()


@socketio.on('ping')
def ping(module_id):
    """ Send PING to module"""
    module_id = int(module_id)

    pkt = Packet(MsgType.PING.value, params.local_msg_id, module_id)
    add_history(pkt)
    lora.send_bytes(pkt.build())

    increment_msg_id()


@socketio.on('reset_db')
def reset_db(args):
    """ Reset DB : empty both module and detection tables """
    cursor.execute(f'DELETE FROM module')
    db.commit()

    cursor.execute(f'DELETE FROM detection')
    db.commit()

    if params.debug:
        print(f"in reset_db()")
        log(f"in reset_db()")



##################
#
# LoRa
#
##################


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
    
    current_dt = time.time()

    if params.debug:
        print(f"in callback_lora()")
        log(f"in reset_db()")

    pkt = Packet.read(data)

    msg_type = pkt.type
    msg_id = pkt.num
    msg_from = pkt.from_to
    payload = pkt.payload

    #Check if received message is duplicate

    msg_history = get_history_msg(msg_type=msg_type, msg_id=msg_id, msg_from_to=msg_from)

    if msg_history:
        if time.time() - msg_history["time"] < 30:
            #update receive_history to update time ?
            print("msg discarded")
            return None
    

    if params.debug:
        print(f"received : {bytes_to_hex(data)}", flush=True)
        #print(f"type={msg_type} id={msg_id} from={msg_from}", flush=True)

    #A module detected something
    if msg_type == MsgType.FRQ.value:

        frq = bytes_to_int(payload[0:4])
        #pwr = -1 * bytes_to_int(payload[4:6]) / 100
        pwr = struct.unpack("e", payload[4:6])[0]

        cursor.execute(f'INSERT INTO detection (module_id, dt, frq, pwr) VALUES ("{msg_from}", "{current_dt}", "{frq}", "{pwr}")')
        db.commit()
        socketio.emit('got_frq', {'dt': current_dt, 'module_id': msg_from, 'frq': frq, 'pwr': pwr})

    #receive PING (probably from tester)
    elif msg_type == MsgType.PING.value:

        if msg_from == 255:
            pkt = Packet(MsgType.ACK.value, msg_id, local_address)
            add_history(pkt)
            lora.send_bytes(pkt.build())

    #A module sent back ACK
    elif msg_type == MsgType.ACK.value:
        
        #check history
        original_msg = get_history_msg(msg_id=msg_id, msg_from_to=msg_from)

        if not original_msg:
            print("not found in history")
            return None

        original_msg_type = original_msg["packet"].type
        print(f"original_msg_type : {original_msg_type}")
        
        if original_msg_type == MsgType.CONF_SCAN.value:

            cursor.execute(f"SELECT frq_start, frq_end, threshold FROM module WHERE id={msg_from}")
            module = cursor.fetchone()

            if module[0] == bytes_to_int(payload[0:2]) \
                and module[1] == bytes_to_int(payload[2:4]) \
                and module[2] == struct.unpack("b", int_to_bytes(payload[4], 1))[0]:
                cursor.execute(f'UPDATE module SET config_applied=true WHERE id={msg_from}')
                socketio.emit('got_config_ack', msg_from)

        elif original_msg_type == MsgType.CONF_LORA.value:
            pass

        elif original_msg_type == MsgType.PING.value:

            latitude = struct.unpack("d", payload[0:8])[0]
            longitude = struct.unpack("d", payload[8:16])[0]
            scanning = payload[16] != 0 #is scanning
            frq_start = bytes_to_int(payload[17:19])
            frq_end = bytes_to_int(payload[19:21])
            threshold = struct.unpack("b", int_to_bytes(payload[21], 1))[0]

            print(f"PING ACK latitude {latitude} / longitude {longitude}")

            cursor.execute(f"UPDATE module SET \
                last_ping='{current_dt}', latitude='{latitude}', longitude='{longitude}' \
                WHERE id={msg_from}")
            db.commit()

            socketio.emit('got_pong', {"module_id": msg_from, "latitude": latitude, "longitude": longitude, 
                                        "frq_start": frq_start, "frq_end": frq_end, "threshold": threshold})



##################
#
# GPS
#
##################

def gps_loop():


    gps_online = gps.activate_poll()

    while params.gps_running:

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
                params.current_lat = gps.location.latitude
                params.current_lng = gps.location.longitude
                socketio.emit('set_master_position', {"latitude": params.current_lat, "longitude": params.current_lng})
                

            if not params.time_set and gps.utc_time.datetime and gps.utc_time.valid:

                if params.debug:
                    print(f"datetime {gps.utc_time.datetime}")
                    log(f"datetime {gps.utc_time.datetime}")

                set_system_date(gps.utc_time.datetime)
                params.time_set = True

            if params.debug:
                print(f"lat : {params.current_lat} / lng {params.current_lng}")
                log(f"lat : {params.current_lat} / lng {params.current_lng}")


        time.sleep(params.delay_gps)



##################
#
# Misc
#
##################


def get_js_timestamp():
    """ Return time as javascript timestamp (in milliseconds) """
    if params.time_set:
        return time.time() * 1000
    return 0


def add_history(pkt):
    msg_time = time.time()
    direction = "send"

    if params.debug:
        print(f"add_history {pkt.type} {pkt.num} {pkt.from_to}")
        log(f"add_history {pkt.type} {pkt.num} {pkt.from_to}")


    params.receive_history.append({"packet": pkt,
                                    "time": msg_time,
                                    "direction": direction})


def get_history_msg(msg_type=None, msg_id=None, msg_from_to=None):
    for hist_line in params.receive_history:

        if (not msg_type or hist_line["packet"].type == msg_type) and \
            (not msg_id or hist_line["packet"].num == msg_id) and \
            (not msg_from_to or hist_line["packet"].from_to == msg_from_to):
            return hist_line

    return None


def increment_msg_id():
    params.local_msg_id += 1
    if params.local_msg_id == 255:
        params.local_msg_id = 0




#Entry point

#Init DB
db = sqlite3.connect("db.sqlite")
cursor = db.cursor()

with open('script.sql', 'r') as f:
    cursor.executescript(f.read())
    db.commit()


params = Parameters(debug=True)

if params.debug:
    print("Start master")
    log("Start master")


lora = sx126x.sx126x(port="/dev/ttyS0", debug=params.debug)

lora.set_config(channel=params.channel,network=0, tx_power=22, 
                air_data_rate=params.air_data_rate, 
                sub_packet_size=params.sub_packet_size)

is_running = True
t_receive = threading.Thread(target=listen_loop, 
        args=[callback_lora, Packet.IDX_PAYLOAD_SIZE, 
        Packet.HEADER_SIZE + Packet.FOOTER_SIZE, Packet.SYNC_WORD])
t_receive.start()

if params.debug:
    print(f"LoRa ready : {lora.ready}")
    log(f"LoRa ready : {lora.ready}")


gps = VMA430()
gps.begin(port="/dev/ttyAMA2", baudrate=9600, debug=False)
gps.set_nav_mode('stationary')

last_gps = 0

t_gps = threading.Thread(target=gps_loop, args=[])
t_gps.start()

