import json
import logging
import paho.mqtt.client as mqtt
from config import DEVICE_ID, MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS

logger = logging.getLogger(__name__)

class MQTTNode:
    def __init__(self):
        self.client = mqtt.Client(client_id=DEVICE_ID)
        self.client.on_connect = self.on_connect

        if MQTT_USER:
            self.client.username_pw_set(MQTT_USER, MQTT_PASS)

    def connect(self):
        logger.info(f"Connecting to MQTT {MQTT_HOST}:{MQTT_PORT}")
        self.client.connect(MQTT_HOST, MQTT_PORT, 60)
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"MQTT connected with rc={rc}")

    def publish_sensors(self, sensors):
        topic = f"sensors/{DEVICE_ID}/data"
        payload = {
            "device_id": DEVICE_ID,
            "sensors": sensors
        }

        logger.info(f"Publishing to {topic}: {payload}")
        self.client.publish(topic, json.dumps(payload), qos=1)