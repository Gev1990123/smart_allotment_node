import logging
import board
import busio
from adafruit_ads1x15.ads1115 import ADS1115
from adafruit_ads1x15.analog_in import AnalogIn

logger = logging.getLogger("moisture")

# =============================
# I2C & ADC setup (ONE TIME)
# =============================
i2c = busio.I2C(board.SCL, board.SDA)
ads = ADS1115(i2c)

# =============================
# Local probe configuration
# =============================
# These IDs must match what you publish in MQTT
SOIL_PROBES = {
    "soil-sensor-001": {"channel": 0, "dry": 2.48, "wet": 1.00},
    "soil-sensor-002": {"channel": 1, "dry": 2.48, "wet": 1.00},
}

# =============================
# Initialize channels
# =============================
CHANNELS = {}

for probe_id, cfg in SOIL_PROBES.items():
    try:
        CHANNELS[probe_id] = AnalogIn(ads, cfg["channel"])
        logger.info(f"Initialized soil probe {probe_id} on {cfg['channel']}")
    except Exception as e:
        logger.error(f"Failed to init {probe_id}: {e}")


# =============================
# Public API
# =============================
def read_moisture(probe_id: str):
    """
    Read soil moisture as percentage for a given probe ID.
    Returns None if probe not found or error.
    """
    try:
        if probe_id not in CHANNELS:
            logger.warning(f"Unknown soil probe: {probe_id}")
            return None

        channel = CHANNELS[probe_id]
        cfg = SOIL_PROBES[probe_id]

        voltage = channel.voltage

        # Clamp voltage to calibration range
        voltage = max(min(voltage, cfg["dry"]), cfg["wet"])

        # Convert voltage to percentage
        percent = ((cfg["dry"] - voltage) / (cfg["dry"] - cfg["wet"])) * 100
        percent = round(percent, 1)

        logger.info(
            f"{probe_id}: {percent}% (V={voltage:.3f}, dry={cfg['dry']}, wet={cfg['wet']})"
        )

        return percent

    except Exception as e:
        logger.error(f"Error reading {probe_id}: {e}")
        return None