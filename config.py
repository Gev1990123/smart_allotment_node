import os
from dotenv import load_dotenv

load_dotenv()

def get_pi_serial():
    try:
        with open('/proc/cpuinfo', 'r') as f:
            for line in f:
                if line.startswith('Serial'):
                    return line.split(':')[1].strip()
    except Exception:
        pass
    return "UNKNOWN"

PI_SERIAL = get_pi_serial()
MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
DEVICE_UID = f"SA-PI-{PI_SERIAL.strip().upper()}"
MQTT_USER =DEVICE_UID
MQTT_PASS = os.getenv("MQTT_PASSWORD", "")
PUBLISH_INTERVAL = int(os.getenv("PUBLISH_INTERVAL", "30"))
