#!/bin/bash
# Smart Allotment Node Update Script

# Activate venv
cd /opt/smart_allotment_node || exit 1
source venv/bin/activate

# Pull latest code
git pull origin main

# Install any new dependencies
pip install -r requirements.txt

# Restart systemd service
sudo systemctl restart smart-allotment-node

echo "Node updated and restarted successfully!"