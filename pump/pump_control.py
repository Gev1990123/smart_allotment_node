import logging
import time
import threading

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

logger = logging.getLogger("pump")

PUMP_GPIO = 17

# Relay logic — change if needed
RELAY_ACTIVE = GPIO.LOW if GPIO else None
RELAY_INACTIVE = GPIO.HIGH if GPIO else None

_initialized = False
_pump_lock = threading.Lock()
_pump_thread = None

# Safety limits
MAX_RUN_SECONDS = 300   # 5 minutes max


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


def pump_on():
    if not _initialized:
        logger.error("Pump not initialized")
        return

    with _pump_lock:
        logger.info("🚰 Pump ON")
        GPIO.output(PUMP_GPIO, RELAY_ACTIVE)


def pump_off():
    if not _initialized:
        logger.error("Pump not initialized")
        return

    with _pump_lock:
        logger.info("🚰 Pump OFF")
        GPIO.output(PUMP_GPIO, RELAY_INACTIVE)


def _run_worker(seconds: float):
    """
    Background worker to run pump without blocking MQTT.
    """
    try:
        pump_on()
        time.sleep(seconds)
    finally:
        pump_off()
        logger.info("🚰 Pump run complete")


def pump_run_for(seconds: float):
    global _pump_thread

    if not _initialized:
        logger.error("Pump not initialized")
        return

    # Safety clamp
    try:
        seconds = float(seconds)
    except Exception:
        logger.error(f"Invalid pump seconds: {seconds}")
        return

    seconds = max(0, min(seconds, MAX_RUN_SECONDS))

    if seconds <= 0:
        logger.warning("Pump run requested with 0 seconds — ignoring")
        return

    # Prevent overlapping runs
    if _pump_thread and _pump_thread.is_alive():
        logger.warning("Pump already running — ignoring new run command")
        return

    logger.info(f"🚰 Pump running for {seconds} seconds (async)")

    _pump_thread = threading.Thread(
        target=_run_worker,
        args=(seconds,),
        daemon=True
    )
    _pump_thread.start()


def cleanup():
    try:
        pump_off()
    except Exception:
        pass

    if GPIO:
        GPIO.cleanup()
        logger.info("Pump GPIO cleaned up")


def handle_pump_command(payload):
    """
    Entry point from MQTT.
    """
    action = payload.get("action")

    if action == "on":
        pump_on()

    elif action == "off":
        pump_off()

    elif action == "run":
        seconds = payload.get("seconds", 0)
        pump_run_for(seconds)

    else:
        logger.warning(f"Unknown pump action: {action}")