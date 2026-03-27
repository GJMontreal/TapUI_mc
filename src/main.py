"""
TapUI_mc — entry point.

Polls the ST25DV64K NFC tag via I2C, drives the WS2812 LED ring
to match the pattern set by the iOS TapUI app, and writes uptime
back to the tag so the app can display it.

Pin assignments (Raspberry Pi Pico):
  GP4   I2C0 SDA  → ST25DV64K SDA
  GP5   I2C0 SCL  → ST25DV64K SCL
  GP28  LED data  → WS2812 DIN
"""

import time
import json
from machine import I2C, Pin

from st25dv import ST25DV
from led_ring import LEDRing

# ── Hardware config ────────────────────────────────────────────────────
I2C_SDA       = 4
I2C_SCL       = 5
LED_PIN       = 28
NUM_LEDS      = 16

# ── Timing ────────────────────────────────────────────────────────────
POLL_MS       = 200   # tag read interval
UPTIME_WRITE_S = 5    # how often to write uptime back to tag


def main():
    i2c  = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)
    tag  = ST25DV(i2c)
    ring = LEDRing(Pin(LED_PIN), NUM_LEDS)

    pattern       = "off"
    last_uptime_write = 0
    start_ms      = time.ticks_ms()

    print("TapUI_mc ready")

    while True:
        now_ms = time.ticks_ms()

        # ── Read tag ──────────────────────────────────────────────────
        try:
            raw = tag.read_ndef_text()
            if raw:
                state   = json.loads(raw)
                pattern = state.get("pattern", "off")
        except Exception as e:
            print("read error:", e)

        # ── Drive LEDs ───────────────────────────────────────────────
        ring.update(pattern, now_ms)

        # ── Write uptime back to tag ──────────────────────────────────
        uptime_s = time.ticks_diff(now_ms, start_ms) // 1000
        if uptime_s - last_uptime_write >= UPTIME_WRITE_S:
            try:
                tag.write_ndef_text(json.dumps({"pattern": pattern, "uptime": uptime_s}))
                last_uptime_write = uptime_s
            except Exception as e:
                print("write error:", e)

        time.sleep_ms(POLL_MS)


main()
