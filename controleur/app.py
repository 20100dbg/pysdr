import gevent
from helper import *
import json
import sqlite3
import sx126x
import threading
import time
import os
from datetime import datetime
from flask import Flask, request, make_response
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*', async_mode='gevent')

@app.route("/")
def main():
    """ Main page : we open or refresh the app"""

    #Retrieve previous data about modules and detections
    cursor.execute("SELECT module_id, dt, frq FROM detection")
    detections = cursor.fetchall()

    cursor.execute("SELECT id, frq_start, frq_end, threshold FROM module")
    modules = cursor.fetchall()

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
def config(params):
    """ Receive config update for a module"""
    global local_msg_id
    module_id = int(params['module_id'])
    frq_start = int(params['frq_start'])
    frq_end = int(params['frq_end'])
    threshold = int(params['threshold'])
    current_dt = get_time()
    
    #update DB
    cursor.execute(f"""UPDATE module SET frq_start='{frq_start}', frq_end='{frq_end}', \
                        threshold='{threshold}', last_config='{current_dt}', config_applied=false 
                        WHERE id={module_id}""")
    db.commit()

    #Send config to module via LoRa
    data = bytes_to_int(frq_start, 2) + bytes_to_int(frq_end, 2) + bytes_to_int(threshold, 1)

    add_history(MsgType.CONF.value, local_msg_id, module_id)
    lora.send_bytes(build_message(MsgType.CONF.value, local_msg_id, module_id, data))
    increment_msg_id()



@socketio.on('set_time')
def set_time(ts):
    """ If not set yet, set time using client's time """
    global time_setup

    if not time_setup:
        ts = int(ts // 1000)
        os.system(f'sudo date -s @{ts}')
        time_setup = True


@socketio.on('set_nb_module')
def set_nb_module(nb):
    """ At startup and manually, client defines how many modules are used. """
    """ We assume for X modules, modules are always identified by ID 1,2,3...X """

    global nb_module
    nb_module = nb

    cursor.execute(f'DELETE FROM module')
    db.commit()
    
    #id frq_start frq_end threshold latitude longitude last_ping config_applied
    data = [(module_id, 400, 420, -10, 0, 0, 0, True) for module_id in range(1, nb_module+1)]
    cursor.executemany("INSERT INTO module VALUES (?, ?, ?, ?, ?, ?, ?, ?)", data)
    db.commit()


@socketio.on('ping')
def ping(module_id):
    """ Send PING to module"""
    global local_msg_id
    module_id = int(module_id)
    add_history(MsgType.PING.value, local_msg_id, module_id)
    lora.send_bytes(build_message(MsgType.PING.value, local_msg_id, module_id))
    increment_msg_id()


@socketio.on('reset_db')
def reset_db(params):
    """ Reset DB : empty both module and detection tables """
    cursor.execute(f'DELETE FROM module')
    db.commit()

    cursor.execute(f'DELETE FROM detection')
    db.commit()


def get_time():
    """ Return time if set """
    if time_setup:
        return time.time()
    return 0


def callback_lora():
    """ Handles every message received from LoRa """

    #global lora

    while True:
        data = lora.receive()
        
        if data and len(data) >= HEADER_SIZE:

            msg_type, msg_id, msg_from = extract_header(data)
            payload = data[HEADER_SIZE:]
            current_dt = get_time()

            print(f"received : {bytes_to_str(data)}")
            print(f"type={msg_type} id={msg_id} from={msg_from} payload={bytes_to_str(payload)}")

            #A module detected something
            if msg_type == MsgType.FRQ.value:

                frq = bytes_to_int(payload[0:4])
                cursor.execute(f'INSERT INTO detection (module_id, dt, frq) VALUES ("{msg_from}", "{current_dt}", "{frq}")')
                db.commit()
                socketio.emit('got_frq', {'dt': current_dt, 'module_id': msg_from, 'frq': frq})


            #A module sent back ACK
            elif msg_type == MsgType.ACK.value:
                
                #check history
                original_msg_type = get_history(msg_id, msg_from)

                if original_msg_type == MsgType.CONF_SCAN.value:

                    cursor.execute(f"SELECT frq_start, frq_end, threshold FROM module WHERE id={msg_from}")
                    module = cursor.fetchone()

                    if module[0] == bytes_to_int(payload[0:2]) \
                        and module[1] == bytes_to_int(payload[2:4]) \
                        and module[2] == bytes_to_int(payload[4:5]):
                        
                        cursor.execute(f'UPDATE module SET config_applied=true WHERE id={msg_from}')
                        socketio.emit('got_config_ack', msg_from)

                elif original_msg_type == MsgType.CONF_LORA.value:
                    pass

                elif original_msg_type == MsgType.PING.value:

                    cursor.execute(f'UPDATE module SET last_ping={current_dt} WHERE id={msg_from}')
                    db.commit()
                    socketio.emit('got_pong', msg_from)

        time.sleep(0.1)


def add_history(msg_type, msg_id, msg_to):
    global history
    history.append({"msg_id": msg_id, "msg_type": msg_type, "msg_to": msg_to})

def get_history(msg_id, msg_to):
    for h in history:
        if h["msg_id"] == msg_id and h["msg_to"] == msg_to:
            return h["msg_type"]

    return None

def increment_msg_id():
    global local_msg_id
    local_msg_id += 1
    if local_msg_id == 256:
        local_msg_id = 0


#Entry point


#Init DB
db = sqlite3.connect("db.sqlite")
cursor = db.cursor()

with open('script.sql', 'r') as f:
    cursor.executescript(f.read())
    db.commit()


global nb_module, history
nb_module = 0
history = []
channel = 18
air_data_rate = 0.3
local_address = 0

time_setup = False
local_msg_id = 0

#global lora
lora = sx126x.sx126x(port="/dev/ttyS0", debug=True)
lora.set_config(channel=channel, logical_address=local_address, network=0, tx_power=22, 
                air_data_rate=air_data_rate, sub_packet_size=32)

t_receive = threading.Thread(target=callback_lora)
t_receive.start()
