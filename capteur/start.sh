#!/bin/bash

cd /home/rpi/capteur
source .venv/bin/activate
python capteur.py $(cat id_slave | tr -d '\n')