import json
import gevent
import sqlite3
import sx126x
import threading
import time
import os
from datetime import datetime
from flask import Flask, request, make_response
from flask_socketio import SocketIO, emit
from signal import signal, SIGINT

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*',async_mode='gevent')

@app.route("/")
def main():

    cursor.execute("SELECT id_module, gdh, frq FROM detection")
    detections = cursor.fetchall()

    cursor.execute("SELECT id, frq_start, frq_end, threshold, config_applied FROM module")
    modules = cursor.fetchall()

    tpl = open('templates/main.html', 'r').read()
    tpl = tpl.replace('{{modules}}', json.dumps(modules))
    tpl = tpl.replace('{{detections}}', json.dumps(detections))

    response = make_response(tpl)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@app.route("/download")
def download():

    cursor.execute("SELECT id_module, gdh, frq FROM detection")
    rows = cursor.fetchall()
    csv = 'id_module;gdh;frq\n'

    for row in rows:
        gdh = datetime.fromtimestamp(row[1])
        frq = pretty_frq(row[2])
        csv += f'{row[0]};{gdh};{frq}\n'

    dt = datetime.now()
    gdh = dt.strftime("%d/%m/%Y %H:%M:%S")

    response = make_response(csv)
    response.headers["Content-Disposition"] = f'attachment; filename="{gdh}_activite.csv"'
    response.headers["Content-Type"] = f'text/csv'
    response.headers["Pragma"] = "public"
    response.headers["Cache-Control"] = "must-revalidate, post-check=0, pre-check=0"
    return response


@socketio.on('config')
def config(params):
    addr = int(params['id'])
    frq_start = int(params['frq_start'])
    frq_end = int(params['frq_end'])
    threshold = int(params['threshold'])
    gdh = get_time()
    
    cursor.execute(f'UPDATE module SET frq_start={frq_start}, frq_end={frq_end}, threshold={threshold}, last_config={gdh}, config_applied=false WHERE id={addr}')
    db.commit()

    data = frq_start.to_bytes(2, 'big') + frq_end.to_bytes(2, 'big') + threshold.to_bytes(1, 'big')
    send(dict_msg['CONF'], addr, data)


@socketio.on('set_time')
def set_time(ts):
    global time_setup

    if not time_setup:
        ts = int(ts // 1000)
        os.system(f'sudo date -s @{ts}')
        time_setup = True


@socketio.on('set_nb_module')
def set_nb_module(nb):
    global nb_module
    nb_module = nb

    cursor.execute(f'DELETE FROM module')
    db.commit()

    data = [(id_module, 0, 0, 400, 420, 0.9) for id_module in range(1,nb_module+1)]
    cursor.executemany("INSERT INTO module VALUES (?, ?, ?, ?, ?, ?, True)", data)
    db.commit()


@socketio.on('ping')
def ping(id_module):
    addr = int(id_module)
    send(dict_msg['PING'], addr, b'')


@socketio.on('reset_db')
def reset_db(params):
    cursor.execute(f'DELETE FROM module')
    db.commit()

    cursor.execute(f'DELETE FROM detection')
    db.commit()




def get_time():
    if time_setup:
        return time.time()
    return 0


def pretty_frq(frq):
    strfrq = str(frq/1000000)
    strfrq = strfrq.ljust(7, '0')
    return strfrq + 'M'


def handler_msg(data):


    if len(data) >= 2:
        msg_type = int.from_bytes(data[0:1])
        addr = int.from_bytes(data[1:2])    
        gdh = get_time()
        #print(f"from : {addr} - MSG : {getmsgkey(msg_type)}")

        if dict_msg["FRQ"] == msg_type and len(data) == 6:        
            frq = int.from_bytes(data[2:6])

            cursor.execute(f'INSERT INTO detection (id_module, gdh, frq) VALUES ("{addr}", "{gdh}", "{frq}")')
            db.commit()
            socketio.emit('got_frq', {'gdh': gdh, 'addr': addr, 'frq': frq})

        elif dict_msg["CONF_ACK"] == msg_type and len(data) == 7:
            
            cursor.execute(f"SELECT frq_start, frq_end, threshold FROM module WHERE id={addr}")
            module = cursor.fetchone()

            if module[0] == int.from_bytes(data[2:4]) and module[1] == int.from_bytes(data[4:6]) and module[2] == int.from_bytes(data[6:7]):
                cursor.execute(f'UPDATE module SET config_applied=true WHERE id={addr}')
                socketio.emit('got_config_ack', addr)

        elif dict_msg["PONG"] == msg_type:
            cursor.execute(f'UPDATE module SET last_ping={gdh} WHERE id={addr}')
            db.commit()
            socketio.emit('got_pong', addr)


def listener():
    global lora

    while True:
        data = lora.receive()
        if data:
            handler_msg(data)
        time.sleep(0.01)


def send(msg_type, addr, data):
    global lora
    msg = msg_type.to_bytes(1, 'big')
    msg += addr.to_bytes(1, 'big')
    msg += data

    #print(f"Sending {msg}")
    lora.sendraw(msg)


def getmsgkey(msg_type):
    idx = list(dict_msg.values()).index(msg_type)
    return list(dict_msg.keys())[idx]


"""
def init_module(id_module):
    data = [('',id_module, 0, 0, 0) for _ in range(4)]
    cursor.executemany("INSERT INTO sdr VALUES (?, ?, ?, ?, ?)", data)
    db.commit()
"""    


db = sqlite3.connect("db.sqlite")
cursor = db.cursor()

with open('script.sql', 'r') as f:
    cursor.executescript(f.read())
    db.commit()

global nb_module
nb_module = 0

dict_msg = {"FRQ": 0, "CONF": 1, "CONF_ACK": 2, "PING": 3, "PONG": 4 }
time_setup = False

global lora
lora = sx126x.sx126x(channel=18,address=0,network=0, txPower='22', airDataRate='9.6', packetSize='32')

t_receive = threading.Thread(target=listener)
t_receive.start()
