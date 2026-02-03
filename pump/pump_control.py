import RPi.GPIO as GPIO
import time

PUMP_GPIO = 17

import RPi.GPIO as GPIO
import time

PUMP_GPIO = 17

GPIO.setmode(GPIO.BCM)
GPIO.setup(PUMP_GPIO, GPIO.OUT)

print("Pump ON")
GPIO.output(PUMP_GPIO, GPIO.HIGH)   # or LOW depending on relay
time.sleep(5)

print("Pump OFF")
GPIO.output(PUMP_GPIO, GPIO.LOW)

GPIO.cleanup()
print("Done")
