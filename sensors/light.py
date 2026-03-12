import time
import logging
import board
import busio
import adafruit_bh1750

logger = logging.getLogger("light")

# =============================
# CONFIG
# =============================
# BH1750 can only ever be 0x23 (ADDR pin low) or 0x5C (ADDR pin high)
BH1750_POSSIBLE_ADDRESSES = [0x23, 0x5C]

# Map sensor IDs to *preferred* address (used as a hint, not a hard requirement).
# If the preferred address isn't found at boot, the other address is tried automatically.

LIGHT_SENSORS = {
    "light-sensor-001": 0x23,
    # "light-sensor-002": 0x5C # second sensor at alternate address
}

# =============================
# GLOBAL STATE
# =============================

_i2c = None
_sensors = {} # sensor_id -> adafruit_bh1750.BH1750 instance
_addresses = {} # sensor_id -> int address actually used

# =============================
# HELPERS
# =============================

def _probe_address(i2c, preferred: int) -> int | None:
    """
    Try the preferred address first, then the alternate.
    Returns the first address that responds with a valid lux reading, or None.
    """
    candidates = [preferred] + [a for a in BH1750_POSSIBLE_ADDRESSES if a != preferred]
    for addr in candidates:
        try:
            sensor = adafruit_bh1750.BH1750(i2c, address=addr)
            _ = sensor.lux  # will raise if nothing is at this address
            logger.info(f"BH1750 responded at 0x{addr:02X} (preferred was 0x{preferred:02X})")
            return addr
        except Exception:
            logger.debug(f"No BH1750 at 0x{addr:02X}")
    return None

# =============================
# INIT
# =============================

def init():
    """
    Initialize all configured BH1750 light sensors.
    Each sensor is probed at its preferred address first; if that fails the
    alternate address (0x23 <-> 0x5C) is tried automatically.
    Call once at startup.
    """
    global _i2c

    try:
        logger.info("Initializing I2C bus")
        _i2c = busio.I2C(board.SCL, board.SDA)
        time.sleep(0.2)
    except Exception as e:
        logger.exception(f"Failed to initialize I2C: {e}")
        return
    
    for sensor_id, preferred_address in LIGHT_SENSORS.items():
        try:
            actual_address = _probe_address(_i2c, preferred_address)
            if actual_address is None:
                logger.error(f"BH1750 {sensor_id} not found at 0x{preferred_address:02X} or alternate address")
                continue


            sensor = adafruit_bh1750.BH1750(_i2c, address=actual_address)
            lux = sensor.lux  # test read
            _sensors[sensor_id] = sensor
            _addresses[sensor_id] = actual_address

            if actual_address != preferred_address:
                logger.warning(f"BH1750 '{sensor_id}' initialised at 0x{actual_address:02X} " f"(preferred 0x{preferred_address:02X} was unavailable)")
            else:
                logger.info(f"BH1750 '{sensor_id}' initialised at 0x{actual_address:02X}, "f"lux={lux:.1f}")
 
        except Exception as e:
            logger.exception(f"Failed to initialize BH1750 '{sensor_id}': {e}")

# =============================
# RE-INIT (call after a read failure)
# =============================
def reinit_sensor(sensor_id: str) -> bool:
    """
    Attempt to re-initialise a single sensor after a failure.
    Returns True if successful.
    """
    if _i2c is None:
        logger.error("I2C bus not initialised — call init() first")
        return False
 
    preferred = LIGHT_SENSORS.get(sensor_id)
    if preferred is None:
        logger.error(f"Unknown sensor_id '{sensor_id}'")
        return False
 
    logger.info(f"Re-probing BH1750 '{sensor_id}'...")
    try:
        actual_address = _probe_address(_i2c, preferred)
        if actual_address is None:
            logger.error(f"BH1750 '{sensor_id}' not found during re-init")
            return False
 
        sensor = adafruit_bh1750.BH1750(_i2c, address=actual_address)
        _ = sensor.lux  # verify
        _sensors[sensor_id] = sensor
        _addresses[sensor_id] = actual_address
        logger.info(f"BH1750 '{sensor_id}' re-initialised at 0x{actual_address:02X}")
        return True
    except Exception as e:
        logger.exception(f"Re-init failed for BH1750 '{sensor_id}': {e}")
        return False


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
    Automatically attempts one re-init if the read fails.
    """
    sensor = _sensors.get(sensor_id)
    if sensor is None:
        logger.warning(f"BH1750 '{sensor_id}' not initialised — attempting re-init")
        if not reinit_sensor(sensor_id):
            return None
        sensor = _sensors[sensor_id]
 
    try:
        result = round(float(sensor.lux), 1)
        logger.info(f"{sensor_id} @ 0x{_addresses[sensor_id]:02X}: {result} lux")
        return result
    except Exception as e:
        logger.warning(f"Read failed for BH1750 '{sensor_id}': {e} — attempting re-init")
        if reinit_sensor(sensor_id):
            try:
                result = round(float(_sensors[sensor_id].lux), 1)
                logger.info(f"{sensor_id} (recovered): {result} lux")
                return result
            except Exception as e2:
                logger.exception(f"BH1750 '{sensor_id}' still failing after re-init: {e2}")
        return None
 