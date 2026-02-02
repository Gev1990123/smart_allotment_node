import os

DEVICE_ID = os.getenv("DEVICE_ID", "device001")

MQTT_HOST = os.getenv("MQTT_HOST", "mqtt")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
MQTT_USER = os.getenv("MQTT_USERNAME", "")
MQTT_PASS = os.getenv("MQTT_PASSWORD", "")

PUBLISH_INTERVAL = int(os.getenv("PUBLISH_INTERVAL", "30"))