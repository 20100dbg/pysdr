import gevent
import sx126x
import threading
import time
import os
from flask import Flask, request, make_response
from flask_socketio import SocketIO, emit
from signal import signal, SIGINT

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins='*',async_mode='gevent')

#dict_scanner = {}

#list_events = []
#GDH, ID capteur, event(frq/config)

@app.route("/")
def main():
    tpl = open('templates/main.html', 'r').read()
    tpl = tpl.replace('{{nb_scanner}}', str(nb_scanner))

    response = make_response(tpl)
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response


@socketio.on('config')
def config(params):
    addr = int(params['id'])
    frq_start = int(params['frq_start'])
    frq_end = int(params['frq_end'])
    threshold = int(params['threshold'])

    data = frq_start.to_bytes(2, 'big') + frq_end.to_bytes(2, 'big') + threshold.to_bytes(1, 'big')
    send(dict_msg['CONF'], addr, data)


@socketio.on('set_time')
def set_time(ts):
    os.system(f'date -s {ts}')


    print(list_events)
    #socketio.emit('msg_from_server', list_events)


def handler_msg(data):
    print(f"Received {data}")

    msg_type = int.from_bytes(data[0:1])
    addr = int.from_bytes(data[1:2])
    gdh = time.time()

    if dict_msg["FRQ"] == msg_type:
        
        frq = int.from_bytes(data[2:6])
        print(f"from : {addr} - MSG : {getmsgkey(msg_type)} - FRQ : {frq}")

        list_events.append([gdh, addr, frq])
        socketio.emit('got_frq', {'addr': addr, 'frq': frq})

    elif dict_msg["CONF_ACK"] == msg_type:
        print(f"from : {addr} - MSG : {getmsgkey(msg_type)}")

        list_events.append([gdh, addr, "Conf OK"])
        socketio.emit('got_config_ack', addr)

    #update()


def listener():
    global lora

    while True:
        data = lora.receive()
        if data:
            handler_msg(data)
        time.sleep(0.01)


def send(msg_type, addr, data):
    global lora

    msg = b''
    msg += msg_type.to_bytes(1, 'big')
    msg += addr.to_bytes(1, 'big')
    msg += data

    print(f"Sending {msg}")
    lora.sendraw(msg)


def getmsgkey(msg_type):
    idx = list(dict_msg.values()).index(msg_type)
    return list(dict_msg.keys())[idx]


nb_scanner = 1

list_events = []
dict_scanner = {}
dict_msg = {"FRQ": 0, "CONF": 1, "CONF_ACK": 2 }

global lora
lora = sx126x.sx126x(channel=18,address=0,network=0, txPower='22', airDataRate='9.6', packetSize='32')

t_receive = threading.Thread(target=listener)
t_receive.start()
