import glob
import time
import os
import logging
from typing import Dict, Optional

logger = logging.getLogger("temperature")

# =============================
# GLOBAL STATE
# =============================

BASE_DIR = "/sys/bus/w1/devices/"
SENSORS: Dict[str, str] = {}
_initialized = False

# =============================
# Init / Detect (call once)
# =============================

def init():
    """
    Scan system for DS18B20 devices and cache them.
    Call ONCE at startup from main.py.
    """
    global _initialized
    SENSORS.clear()

    devices = glob.glob(os.path.join(BASE_DIR, "28-*"))

    if not devices:
        logger.warning("⚠️ No DS18B20 temperature sensors detected")
        _initialized = True
        return

    for idx, device in enumerate(devices, start=1):
        device_file = os.path.join(device, "w1_slave")
        probe_id = f"temp-{idx:03d}"
        SENSORS[probe_id] = device_file
        logger.info(f"🌡️ Detected DS18B20: {probe_id} -> {device}")

    logger.info(f"🌡️ Temperature sensors ready: {len(SENSORS)}")
    _initialized = True

# =============================
# Read one temperature
# =============================

def read_temperature(probe_id: Optional[str] = None) -> Optional[float]:
    """
    Read temperature from a detected DS18B20.
    If probe_id is None, read first detected sensor.
    """
    if not _initialized:
        logger.error("Temperature sensors not initialized. Call temperature.init() first.")
        return None

    if not SENSORS:
        return None

    if probe_id is None:
        probe_id = next(iter(SENSORS.keys()))

    device_file = SENSORS.get(probe_id)
    if not device_file or not os.path.exists(device_file):
        logger.warning(f"DS18B20 device missing for {probe_id}")
        return None

    try:
        # Give sensor time
        time.sleep(0.75)

        with open(device_file, "r") as f:
            lines = f.readlines()

        if not lines[0].strip().endswith("YES"):
            logger.warning(f"DS18B20 CRC check failed for {probe_id}")
            return None

        pos = lines[1].find("t=")
        if pos == -1:
            logger.warning(f"Invalid DS18B20 data for {probe_id}")
            return None

        temp_c = float(lines[1][pos + 2:]) / 1000.0
        result = round(temp_c, 1)

        logger.info(f"{probe_id}: {result}°C")
        return result

    except Exception as e:
        logger.error(f"Error reading temp probe {probe_id}: {e}")
        return None