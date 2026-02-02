#!/bin/bash
# Smart Allotment Node Install Script
# Run as the smartallotment user

set -e

echo "=== Smart Allotment Node Installer ==="

# --- 1. Prompt user for configuration ---
read -p "Enter DEVICE_ID for this Pi (e.g., SA-NODE1): " DEVICE_ID
read -p "Enter MQTT broker host/IP (e.g., 192.168.0.114): " MQTT_HOST
read -p "Enter MQTT broker port [1883]: " MQTT_PORT
MQTT_PORT=${MQTT_PORT:-1883}

# Optional: username/password
read -p "Enter MQTT username (leave empty if none): " MQTT_USERNAME
read -s -p "Enter MQTT password (leave empty if none): " MQTT_PASSWORD
echo ""

# --- 2. Prepare Node directory ---
NODE_DIR=/opt/smart_allotment_node
sudo mkdir -p $NODE_DIR
sudo chown $USER:$USER $NODE_DIR
cd $NODE_DIR

# --- 3. Clone or update repo ---
if [ -d ".git" ]; then
    echo "Updating existing Node repository..."
    git pull origin main
else
    echo "Cloning Node repository..."
    git clone git@github.com:Gev1990123/smart_allotment_node.git .
fi

# --- 4. Create Python virtual environment ---
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

source venv/bin/activate

# --- 5. Install Python dependencies ---
pip install --upgrade pip
pip install -r requirements.txt

# --- 6. Create .env file ---
cat > $NODE_DIR/.env <<EOL
DEVICE_ID=$DEVICE_ID
MQTT_HOST=$MQTT_HOST
MQTT_PORT=$MQTT_PORT
MQTT_USERNAME=$MQTT_USERNAME
MQTT_PASSWORD=$MQTT_PASSWORD
PUBLISH_INTERVAL=30
EOL

echo ".env file created at $NODE_DIR/.env"

# --- 7. Create systemd service ---
SERVICE_FILE=/etc/systemd/system/smart-allotment-node.service
sudo bash -c "cat > $SERVICE_FILE" <<EOL
[Unit]
Description=Smart Allotment MQTT Node
After=network.target

[Service]
User=$USER
Group=$USER
WorkingDirectory=$NODE_DIR
ExecStart=$NODE_DIR/venv/bin/python $NODE_DIR/main.py
Restart=always
RestartSec=5
EnvironmentFile=$NODE_DIR/.env

[Install]
WantedBy=multi-user.target
EOL

echo "systemd service created at $SERVICE_FILE"

# --- 8. Enable and start service ---
sudo systemctl daemon-reload
sudo systemctl enable smart-allotment-node
sudo systemctl restart smart-allotment-node

echo "Smart Allotment Node installed and running!"
echo "You can check logs with: journalctl -u smart-allotment-node -f"