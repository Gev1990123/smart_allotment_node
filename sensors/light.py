import time
import logging
import board
import busio
import adafruit_bh1750

logger = logging.getLogger("light")

# =============================
# CONFIG
# =============================

# Default BH1750 I2C address (0x23 is most common)
BH1750_ADDRESS = 0x5C
LIGHT_SENSORS = {
    "light-sensor-001": BH1750_ADDRESS,
    # "light-sensor-002": 0x23,  # second sensor at alternate address
}

# =============================
# GLOBAL STATE
# =============================

_i2c = None
_sensors = {}

# =============================
# INIT
# =============================

def init(address: int = BH1750_ADDRESS):
    """
    Initialize BH1750 light sensor. Call once at startup.
    """
    global _i2c

    try:
        logger.info(f"Initializing BH1750 at I2C address 0x{address:02X}")
        _i2c = busio.I2C(board.SCL, board.SDA)
        time.sleep(0.2)
    except Exception as e:
        logger.exception(f"Failed to initialize I2C: {e}")
        return
    
    for sensor_id, address in LIGHT_SENSORS.items():
        try:
            sensor = adafruit_bh1750.BH1750(_i2c, address=address)
            lux = sensor.lux  # test read
            _sensors[sensor_id] = sensor
            logger.info(f"BH1750 {sensor_id} initialized at 0x{address:02X}, lux={lux:.1f}")
        except Exception as e:
            logger.exception(f"Failed to initialize BH1750 {sensor_id} at 0x{address:02X}: {e}")

# =============================
# Read all light (for API)
# =============================

def read_all_light():
    """Returns a list of sensor payloads for all configured light sensors."""
    return [
        {"type": "light", "id": sensor_id, "value": read_light(sensor_id)}
        for sensor_id in LIGHT_SENSORS
    ]


# =============================
# READ
# =============================

def read_light(sensor_id: str) -> float | None:
    """
    Read light level in lux. Returns float lux or None on failure.
    """
    sensor = _sensors.get(sensor_id)

    if sensor is None:
        logger.error("BH1750 not initialized — call init() first")
        return None
    try:
        result = round(float(sensor.lux), 1)
        logger.info(f"{sensor_id}: {result} lux")
        return result
    except Exception as e:
        logger.exception(f"Error reading BH1750 {sensor_id}: {e}")
        return None