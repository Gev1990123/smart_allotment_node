import time
import logging

from mqtt_client import MQTTNode
from sensors import temperature
from sensors import light
from sensors.moisture import read_moisture
from pump import pump_control
from config import PUBLISH_INTERVAL

logging.basicConfig(level=logging.INFO)

def build_sensor_payload():
    sensors = []

    # Temperature
    sensors.append({
        "type": "temperature",
        "id": "temp-sensor-001",
        "value": temperature.read_temperature()
    })

    # Moisture (multiple probes)
    sensors.append({
        "type": "moisture",
        "id": "soil-sensor-001",
        "value": read_moisture("soil-sensor-001")
    })

#    sensors.append({
#        "type": "moisture",
#        "id": "soil-sensor-002",
#        "value": read_moisture("soil-sensor-002")
#    })

    # Light
    sensors.append({
        "type": "light",
        "id": "light-sensor-001",
        "value": light.read_light()
    })

    return sensors

def main():
    # init hardware
    light.init()
    temperature.init()
    pump_control.init()

    node = MQTTNode()
    node.connect()

    while True:
        sensors = build_sensor_payload()
        node.publish_sensors(sensors)
        time.sleep(PUBLISH_INTERVAL)

if __name__ == "__main__":
    main()
