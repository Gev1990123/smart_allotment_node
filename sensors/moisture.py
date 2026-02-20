import logging
import time
import board
import busio
import digitalio
from adafruit_ads1x15.ads1115 import ADS1115, P0, P1, P2, P3
from adafruit_ads1x15.analog_in import AnalogIn

logger = logging.getLogger("moisture")

# =============================
# GPIO Power Pin Setup
# =============================
# Connect sensor VCC to this GPIO pin (use a transistor/MOSFET for >3.3V sensors)
power_pin = digitalio.DigitalInOut(board.D27)  # Change to your GPIO pin
power_pin.direction = digitalio.Direction.OUTPUT
power_pin.value = False  # Start with sensor OFF

# =============================
# I2C & ADC setup (ONE TIME)
# =============================
i2c = busio.I2C(board.SCL, board.SDA)

# Map channel numbers to ADS1115 pin constants
CHANNEL_MAP = {0: P0, 1: P1, 2: P2, 3: P3}

# =============================
# Probe configuration
# Each probe has its own power GPIO pin and ADC channel
# =============================
SOIL_PROBES = {
    "soil-sensor-001": {"channel": 0, "power_pin": board.D27, "dry": 2.48, "wet": 1.00},
    #"soil-sensor-002": {"channel": 1, "power_pin": board.D22, "dry": 2.48, "wet": 1.00},
    # "soil-sensor-003": {"channel": 2, "power_pin": board.D23, "dry": 2.48, "wet": 1.00},
    # "soil-sensor-004": {"channel": 3, "power_pin": board.D24, "dry": 2.48, "wet": 1.00},
}

# =============================
# Initialise power pins
# =============================
_power_pins = {}
for probe_id, cfg in SOIL_PROBES.items():
    try:
        pin = digitalio.DigitalInOut(cfg["power_pin"])
        pin.direction = digitalio.Direction.OUTPUT
        pin.value = False  # Start OFF
        _power_pins[probe_id] = pin
        logger.info(f"Initialised power pin for {probe_id}")
    except Exception as e:
        logger.error(f"Failed to init power pin for {probe_id}: {e}")

# =============================
# Read all probes (for API)
# =============================
def read_all_moisture():
    """Returns a list of sensor payloads for all configured probes."""
    return [
        {"type": "moisture", "id": probe_id, "value": read_moisture(probe_id)}
        for probe_id in SOIL_PROBES
    ]

# =============================
# Public API
# =============================
def read_moisture(probe_id: str):
    """
    Powers on the sensor, waits 200ms, reads moisture, powers off.
    Returns moisture percentage or None on error.
    """
    try:
        if probe_id not in SOIL_PROBES:
            logger.warning(f"Unknown soil probe: {probe_id}")
            return None

        cfg = SOIL_PROBES[probe_id]
        pin = _power_pins.get(probe_id)

        if pin is None:
            logger.error(f"No power pin available for {probe_id}")
            return None

        # Power on the sensor
        power_pin.value = True
        time.sleep(0.2) 

        # Re-init ADC and channel after power cycle
        ads = ADS1115(i2c)
        ads.gain = 1
        channel = AnalogIn(ads, P0)
        voltage = channel.voltage
        logger.info(f"RAW: {channel.value}, V={voltage:.3f}")

        # --- Power OFF ---
        power_pin.value = False

        # Clamp and convert
        voltage = max(min(voltage, cfg["dry"]), cfg["wet"])
        percent = ((cfg["dry"] - voltage) / (cfg["dry"] - cfg["wet"])) * 100
        percent = round(percent, 1)

        logger.info(
            f"{probe_id}: {percent}% (V={voltage:.3f}, dry={cfg['dry']}, wet={cfg['wet']})"
        )

        return percent

    except Exception as e:
        power_pin.value = False
        logger.error(f"Error reading {probe_id}: {e}")
        return None