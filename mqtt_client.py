import json
import logging
import time
import paho.mqtt.client as mqtt
from config import DEVICE_UID, MQTT_HOST, MQTT_PORT, MQTT_USER, MQTT_PASS
from pump import pump_control    

logger = logging.getLogger(__name__)

# Reconnect backoff settings
_RECONNECT_DELAY_MIN = 2   # seconds
_RECONNECT_DELAY_MAX = 60  # seconds

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
        self.connected = False
        self._reconnect_delay = _RECONNECT_DELAY_MIN

        self.client = mqtt.Client(client_id=DEVICE_UID, clean_session=True)

        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self.on_message

        if MQTT_USER:
            self.client.username_pw_set(MQTT_USER, MQTT_PASS)
        else:
            logger.warning("No MQTT credentials configured — anonymous access")

        # Exponential backoff on reconnect (built into paho >= 1.6)
        self.client.reconnect_delay_set(
            min_delay=_RECONNECT_DELAY_MIN,
            max_delay=_RECONNECT_DELAY_MAX
        )

    # =============================
    # CONNECT
    # =============================

    def connect(self):
        logger.info(f"Connecting to MQTT {MQTT_HOST}:{MQTT_PORT}")
        logger.info(f"Using credentials: {MQTT_USER}:{'***' if MQTT_PASS else 'none'}")

        self.client.connect(MQTT_HOST, MQTT_PORT, keepalive=60)
        self.client.loop_start()

    # =============================
    # CALLBACKS
    # =============================

    def on_connect(self, client, userdata, flags, rc):
        RC_CODES = {
            0: "Connected",
            1: "Refused — incorrect protocol version",
            2: "Refused — invalid client ID",
            3: "Refused — broker unavailable",
            4: "Refused — bad credentials",
            5: "Refused — not authorised",
        }
        status = RC_CODES.get(rc, f"Unknown rc={rc}")

        if rc == 0:
            self._connected = True
            self._reconnect_delay = _RECONNECT_DELAY_MIN  # reset backoff on success
            logger.info(f"MQTT connected to {MQTT_HOST}:{MQTT_PORT}")
 
            pump_topic = f"pump/{DEVICE_UID}"
            read_topic = f"cmd/{DEVICE_UID}/read-now"
            client.subscribe([(pump_topic, 1), (read_topic, 1)])
            logger.info(f"Subscribed to: {pump_topic}, {read_topic}")
        else:
            self._connected = False
            logger.error(f"MQTT connection failed: {status}")

    def _on_disconnect(self, client, userdata, rc):
        self._connected = False
        if rc == 0:
            logger.info("MQTT disconnected cleanly")
        else:
            logger.warning(
                f"MQTT disconnected unexpectedly (rc={rc}) — "
                f"paho will retry with backoff ({_RECONNECT_DELAY_MIN}–{_RECONNECT_DELAY_MAX}s)"
            )

    def on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON on {msg.topic}: {e}")
            return

        logger.info(f"MQTT message on {msg.topic}: {payload}")

        if msg.topic == f"pump/{DEVICE_UID}":
            pump_control.handle_pump_command(payload)
        elif msg.topic == f"cmd/{DEVICE_UID}/read-now":
            requested_by = payload.get("requested_by", "unknown")
            logger.info(f"Manual read requested by: {requested_by}")
            self._trigger_reading()

    # =============================
    # PUBLISH
    # =============================

    def publish_sensors(self, sensors: list):
        if not self._connected:
            logger.warning("MQTT not connected — skipping publish")
            return
        
        topic = f"sensors/{DEVICE_UID}/data"
        payload = {
            "device_uid": DEVICE_UID,
            "sensors": sensors
        }

        self.client.publish(topic, json.dumps(payload), qos=1)
        logger.info(f"Publishing to {topic}: {payload}")
    
    # =============================
    # MANUAL READ TRIGGER
    # =============================    

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