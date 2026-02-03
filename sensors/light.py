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
BH1750_ADDRESS = 0x23

# =============================
# GLOBAL STATE
# =============================

_i2c = None
_sensor = None

# =============================
# INIT
# =============================

def init(address: int = BH1750_ADDRESS):
    """
    Initialize BH1750 light sensor.
    Call once at startup.
    """
    global _i2c, _sensor

    try:
        logger.info(f"Initializing BH1750 at I2C address 0x{address:02X}")

        _i2c = busio.I2C(board.SCL, board.SDA)
        time.sleep(0.2)

        _sensor = adafruit_bh1750.BH1750(_i2c, address=address)

        # Test read
        lux = _sensor.lux
        logger.info(f"BH1750 initialized successfully, initial lux={lux:.1f}")

    except Exception as e:
        logger.exception(f"❌ Failed to initialize BH1750: {e}")
        _sensor = None


# =============================
# READ
# =============================

def read_light() -> float | None:
    """
    Read light level in lux.
    Returns float lux or None on failure.
    """
    if _sensor is None:
        logger.error("BH1750 not initialized — call init() first")
        return None

    try:
        lux = _sensor.lux
        result = round(float(lux), 1)

        logger.info(f"Light level: {result} lux")
        return result

    except Exception as e:
        logger.exception(f"❌ Error reading BH1750: {e}")
        return None