import json
import logging
import paho.mqtt.client as mqtt
from config import DEVICE_UID, MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS
from pump import pump_control    

logger = logging.getLogger(__name__)

class MQTTNode:
    def __init__(self, read_callback=None):
        """
        read_callback: callable that returns a list of sensor dicts, e.g:
            [
                {"type": "moisture", "id": "soil-sensor-001", "value": 65},
                {"type": "temperature", "id": "temp-sensor-001", "value": 18.2},
                {"type": "light", "id": "light-sensor-001", "value": 450}
            ]
        """

        self.read_callback = read_callback
        self.client = mqtt.Client(client_id=DEVICE_UID)
        self.client.on_connect = self.on_connect
        self.client.on_message = self.on_message

        if MQTT_USER:
            self.client.username_pw_set(MQTT_USER, MQTT_PASS)

    def connect(self):
        logger.info(f"Connecting to MQTT {MQTT_HOST}:{MQTT_PORT}")
        logger.info(f"Using credentials: {MQTT_USER}:{'***' if MQTT_PASS else 'none'}")

        if MQTT_USER:
            self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        else:
            logger.warning("No MQTT credentials - anonymous access")

        result = self.client.connect(MQTT_HOST, MQTT_PORT, 60)
        logger.info(f"Connect result code: {result}")
        self.client.loop_start()

    def on_connect(self, client, userdata, flags, rc):
        logger.info(f"MQTT connected with rc={rc}")

        # Subscribe to pump commands for this node
        topic = f"pump/{DEVICE_UID}"
        self.client.subscribe(topic, qos=1)
        logger.info(f"Subscribed to {topic} for pump commands")

    def publish_sensors(self, sensors):
        topic = f"sensors/{DEVICE_UID}/data"
        payload = {
            "device_uid": DEVICE_UID,
            "sensors": sensors
        }

        logger.info(f"Publishing to {topic}: {payload}")
        self.client.publish(topic, json.dumps(payload), qos=1)
    
    def on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = json.loads(msg.payload.decode())
        logger.info(f"MQTT message received on {topic}: {payload}")

        if topic == f"pump/{DEVICE_UID}":
            pump_control.handle_pump_command(payload)

    def _trigger_reading(self):
        """Take an immediate sensor reading and publish it."""
        if not self.read_callback:
            logger.warning("No read_callback provided - cannot trigger manual reading")
            return
        try:
            sensors = self.read_callback()
            if sensors:
                self.publish_sensors(sensors)
                logger.info(f"Manual read complete - published {len(sensors)} sensors")
            else:
                logger.warning("Manual read returned no sensor data")
        except Exception as e:
            logger.error(f"Error during manual read: {e}")