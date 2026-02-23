import time
import logging
from mqtt_client import MQTTNode
from sensors import temperature, light
from sensors.temperature import read_all_temperatures
from sensors.light import read_all_light
from sensors.moisture import read_all_moisture
from pump import pump_control
from config import PUBLISH_INTERVAL

logging.basicConfig(level=logging.INFO)

def build_sensor_payload():
    sensors = []
    sensors.extend(read_all_temperatures())
    sensors.extend(read_all_moisture())
    sensors.extend(read_all_light())
    return sensors

def main():
    # init hardware
    light.init()
    temperature.init()
    pump_control.init()

    node = MQTTNode(read_callback=build_sensor_payload)
    node.connect()

    while True:
        sensors = build_sensor_payload()
        node.publish_sensors(sensors)
        time.sleep(PUBLISH_INTERVAL)

if __name__ == "__main__":
    main()
