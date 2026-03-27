"""
GPO pin continuity check.

Polls GP15 and prints whenever it changes state.
Wave the phone near the tag — if GPO is wired correctly you'll
see the pin go low.

Run with:  mpremote run test/test_gpo_pin.py
Exit with: Ctrl-C
"""

import time
from machine import Pin

GPO_PIN = 15

gpo  = Pin(GPO_PIN, Pin.IN, Pin.PULL_UP)
last = gpo.value()
print("Monitoring GP{} — current state: {}".format(GPO_PIN, "HIGH" if last else "LOW"))
print("Wave the phone near the tag...")

while True:
    val = gpo.value()
    if val != last:
        print("GP{} -> {}".format(GPO_PIN, "HIGH" if val else "LOW"))
        last = val
    time.sleep_ms(10)
