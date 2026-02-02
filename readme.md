## Prerequisites

- Raspberry Pi or Linux machine
- Git installed: sudo apt install git
- Python 3.13+ installed: sudo apt install python3 python3-venv python3-pip
- Docker & Docker Compose installed:

```
sudo apt install docker.io docker-compose
```
```
sudo usermod -aG docker $USER
```

## Node Installation
### Clone Repository

```
cd /opt
sudo mkdir -p /opt/smart_allotment_node
sudo chown smartallotment:smartallotment /opt/smart_allotment_node
cd /opt/smart_allotment_node
git clone git@github.com:Gev1990123/smart_allotment_node.git .
```

### Setup Python Virtual Environment
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Configure .env
Create a .env file with relevant configuration:
```
DEVICE_ID=SA-NODE1
MQTT_HOST=<hub_ip_or_hostname>
MQTT_PORT=1883
MQTT_USERNAME=
MQTT_PASSWORD=
```

### Systemd Service
Create the systemd service to run the Node on boot:
```
sudo nano /etc/systemd/system/smart-allotment-node.service
```

Paste:
```
[Unit]
Description=Smart Allotment MQTT Node
After=network.target

[Service]
User=smartallotment
Group=smartallotment
WorkingDirectory=/opt/smart_allotment_node
ExecStart=/opt/smart_allotment_node/venv/bin/python /opt/smart_allotment_node/main.py
Restart=always
RestartSec=5
EnvironmentFile=/opt/smart_allotment_node/.env

[Install]
WantedBy=multi-user.target
```

Enable and start service:
```
sudo systemctl daemon-reload
sudo systemctl enable smart-allotment-node
sudo systemctl start smart-allotment-node
sudo systemctl status smart-allotment-node
```

### Updating Node
1. Pull latest code:
```
cd /opt/smart_allotment_node
git pull origin main
```
2. Update packages if required:
```
source venv/bin/activate
pip install -r requirements.txt
```
