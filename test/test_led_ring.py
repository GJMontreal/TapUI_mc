"""
LED ring wiring verification.

Runs a sequence of tests to confirm the ring is wired and responding correctly.
Deploy and run with:  mpremote run test/test_led_ring.py

Tests:
  1. Color channels — full red, green, blue in sequence (checks R/G/B aren't swapped)
  2. Pixel walk    — lights each LED individually (confirms all 16 are connected)
  3. Brightness    — steps from off to full white (checks power rail is adequate)
"""

import time
from machine import Pin
from neopixel import NeoPixel

LED_PIN  = 28
NUM_LEDS = 16
STEP_MS  = 300   # pause between steps


def all_color(np, color, label):
    print(f"  {label}")
    for i in range(len(np)):
        np[i] = color
    np.write()
    time.sleep_ms(STEP_MS * 3)


def pixel_walk(np):
    print("  walking pixels...")
    off = (0, 0, 0)
    for i in range(len(np)):
        np[i] = (0, 0, 80)
        np.write()
        time.sleep_ms(STEP_MS)
        np[i] = off
    np.write()


def brightness_ramp(np):
    print("  ramping brightness...")
    for level in range(0, 256, 16):
        for i in range(len(np)):
            np[i] = (level, level, level)
        np.write()
        time.sleep_ms(80)
    time.sleep_ms(STEP_MS)
    for i in range(len(np)):
        np[i] = (0, 0, 0)
    np.write()


def main():
    np = NeoPixel(Pin(LED_PIN), NUM_LEDS)

    print("\n── Test 1: color channels ──")
    all_color(np, (80, 0, 0),  "red")
    all_color(np, (0, 80, 0),  "green")
    all_color(np, (0, 0, 80),  "blue")
    all_color(np, (0, 0, 0),   "off")

    print("\n── Test 2: pixel walk ──")
    pixel_walk(np)

    print("\n── Test 3: brightness ramp ──")
    brightness_ramp(np)

    print("\nDone. If all 16 LEDs lit correctly the ring is good.")


main()
