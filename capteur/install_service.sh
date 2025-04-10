sudo cat <<EOF > /etc/systemd/system/capteur.service
[Unit]
Description=capteur
After=network.target

[Service]
User=rpi
WorkingDirectory=/home/rpi/capteur/
ExecStart=/home/rpi/capteur/start.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl enable capteur.service