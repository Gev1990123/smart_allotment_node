import time
import logging

from mqtt_client import MQTTNode
from sensors.temperature import read_temperature
from sensors.moisture import read_moisture
from sensors.light import read_light
from config import PUBLISH_INTERVAL

logging.basicConfig(level=logging.INFO)

def build_sensor_payload():
    sensors = []

    # Temperature
    sensors.append({
        "type": "temperature",
        "id": "temp-sensor-001",
        "value": read_temperature()
    })

    # Moisture (multiple probes)
    sensors.append({
        "type": "moisture",
        "id": "soil-sensor-001",
        "value": read_moisture("soil-sensor-001")
    })

    sensors.append({
        "type": "moisture",
        "id": "soil-sensor-002",
        "value": read_moisture("soil-sensor-002")
    })

    # Light
    sensors.append({
        "type": "light",
        "id": "light-sensor-001",
        "value": read_light()
    })

    return sensors

def main():
    node = MQTTNode()
    node.connect()

    while True:
        sensors = build_sensor_payload()
        node.publish_sensors(sensors)
        time.sleep(PUBLISH_INTERVAL)

if __name__ == "__main__":
    main()
