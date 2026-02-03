import logging
import time
import RPi.GPIO as GPIO

logger = logging.getLogger("pump")

PUMP_GPIO = 17

# Relay logic — change if needed
RELAY_ACTIVE = GPIO.LOW if GPIO else None   # many relays are active LOW
RELAY_INACTIVE = GPIO.HIGH if GPIO else None


_initialized = False


def init():
    global _initialized

    if GPIO is None:
        logger.warning("RPi.GPIO not available — pump disabled (dev mode)")
        return

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(PUMP_GPIO, GPIO.OUT)

    # Ensure pump is OFF on startup
    GPIO.output(PUMP_GPIO, RELAY_INACTIVE)

    _initialized = True
    logger.info(f"🚰 Pump initialized on GPIO{PUMP_GPIO}")


def on():
    if not _initialized:
        raise RuntimeError("Pump not initialized. Call pump.init() first.")

    logger.info("🚰 Pump ON")
    GPIO.output(PUMP_GPIO, RELAY_ACTIVE)


def off():
    if not _initialized:
        raise RuntimeError("Pump not initialized. Call pump.init() first.")

    logger.info("🚰 Pump OFF")
    GPIO.output(PUMP_GPIO, RELAY_INACTIVE)


def run_for(seconds: float):
    """
    Run pump for N seconds safely.
    """
    logger.info(f"🚰 Pump running for {seconds} seconds")
    on()
    try:
        time.sleep(seconds)
    finally:
        off()


def cleanup():
    if GPIO:
        GPIO.cleanup()
        logger.info("Pump GPIO cleaned up")
