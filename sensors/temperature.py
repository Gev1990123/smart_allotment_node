import glob
import logging
from typing import Dict, Optional

logger = logging.getLogger("temperature")

BASE_DIR = "/sys/bus/w1/devices/"

# Cache of detected sensors
SENSORS: Dict[str, str] = {}  # {probe_id: device_file}


# =============================
# Init / Detect (call once)
# =============================
def init():
    """
    Scan system for DS18B20 devices and cache them.
    Call ONCE at startup from main.py.
    """
    global SENSORS
    SENSORS.clear()

    devices = glob.glob(BASE_DIR + "28-*")

    if not devices:
        logger.warning("⚠️ No DS18B20 temperature sensors detected")
        return

    for idx, device in enumerate(devices, start=1):
        device_file = f"{device}/w1_slave"
        probe_id = f"temp-{idx:03d}"
        SENSORS[probe_id] = device_file
        logger.info(f"🌡️ Detected DS18B20: {probe_id} -> {device}")

    logger.info(f"🌡️ Temperature sensors ready: {len(SENSORS)}")


# =============================
# Read Temperature
# =============================
def read_temperature(probe_id: str = None) -> Optional[float]:
    """
    Read temperature in Celsius.
    Assumes init() already called.
    """
    try:
        if not SENSORS:
            logger.error("Temperature sensors not initialized. Call temperature.init() first.")
            return None

        # Default to first sensor
        if probe_id is None:
            probe_id = next(iter(SENSORS.keys()))

        device_file = SENSORS.get(probe_id)
        if not device_file:
            logger.warning(f"Unknown temperature probe: {probe_id}")
            return None

        with open(device_file, "r") as f:
            lines = f.readlines()

        # CRC check
        if not lines[0].strip().endswith("YES"):
            logger.warning(f"CRC check failed for {probe_id}")
            return None

        temp_pos = lines[1].find("t=")
        if temp_pos == -1:
            return None

        temp_c = float(lines[1][temp_pos + 2:]) / 1000.0
        temp_c = round(temp_c, 1)

        logger.info(f"{probe_id}: {temp_c}°C")
        return temp_c

    except Exception as e:
        logger.error(f"Error reading temperature {probe_id}: {e}")
        return None


# =============================
# Optional Manual Rescan
# =============================
def rescan():
    logger.info("🔄 Rescanning temperature sensors...")
    init()
