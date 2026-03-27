"""
TapUI_mc — entry point.

Interrupt-driven: the ST25DV64K GPO pin asserts (active-low) when the iOS
app finishes an NFC write. A Pico IRQ sets a flag; the main loop reads the
tag and updates the LED ring only when new data arrives.

Between writes the main loop keeps running to animate the LEDs smoothly.

Pin assignments (Raspberry Pi Pico):
  GP4   I2C0 SDA  → ST25DV64K SDA
  GP5   I2C0 SCL  → ST25DV64K SCL
  GP15  GPO input → ST25DV64K GPO  (active-low, needs PULL_UP)
  GP28  LED data  → WS2812 DIN
"""

import time
import json
import micropython
from machine import I2C, Pin

from st25dv import ST25DV
from led_ring import LEDRing

# ── Hardware config ────────────────────────────────────────────────────
I2C_SDA  = 4
I2C_SCL  = 5
GPO_PIN  = 15
LED_PIN  = 28
NUM_LEDS = 16

# ── Timing ────────────────────────────────────────────────────────────
FRAME_MS       = 16    # ~60 fps for smooth LED animation
UPTIME_WRITE_S = 5     # how often to write uptime back to tag

# ── Interrupt flag (set in IRQ context, cleared in main loop) ─────────
_tag_written = False


def _gpo_irq(_pin):
    # IRQ handler — only safe to set a flag here; I2C must happen in main.
    micropython.schedule(_set_tag_written, 0)


def _set_tag_written(_arg):
    global _tag_written
    _tag_written = True


def main():
    global _tag_written

    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)
    tag = ST25DV(i2c)
    ring = LEDRing(Pin(LED_PIN), NUM_LEDS)

    # Configure GPO for RF-write interrupt, then attach Pico IRQ.
    try:
        tag.configure_gpo_rf_write()
        tag.clear_interrupt()
    except OSError as e:
        print("GPO config failed (check I2C password?):", e)

    gpo = Pin(GPO_PIN, Pin.IN, Pin.PULL_UP)
    gpo.irq(trigger=Pin.IRQ_FALLING, handler=_gpo_irq)

    # Do one initial read so we start with whatever is already on the tag.
    pattern = "off"
    try:
        raw = tag.read_ndef_text()
        if raw:
            pattern = json.loads(raw).get("pattern", "off")
    except Exception as e:
        print("initial read error:", e)

    last_uptime_write = 0
    start_ms = time.ticks_ms()
    print("TapUI_mc ready — waiting for NFC writes")

    while True:
        now_ms = time.ticks_ms()

        # ── Handle tag write event ────────────────────────────────────
        if _tag_written:
            _tag_written = False
            try:
                raw = tag.read_ndef_text()
                if raw:
                    pattern = json.loads(raw).get("pattern", "off")
                    print("pattern:", pattern)
                tag.clear_interrupt()
            except Exception as e:
                print("read error:", e)

        # ── Animate LEDs ──────────────────────────────────────────────
        ring.update(pattern, now_ms)

        # ── Write uptime back to tag ──────────────────────────────────
        uptime_s = time.ticks_diff(now_ms, start_ms) // 1000
        if uptime_s - last_uptime_write >= UPTIME_WRITE_S:
            try:
                tag.write_ndef_text(json.dumps({"pattern": pattern, "uptime": uptime_s}))
                last_uptime_write = uptime_s
            except Exception as e:
                print("write error:", e)

        time.sleep_ms(FRAME_MS)


main()
