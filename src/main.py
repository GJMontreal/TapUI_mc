"""
TapUI_mc — entry point.

Interrupt-driven: the ST25DV16K GPO pin (GP15, active-low) asserts when
the phone writes to the tag via NFC. The Pico only accesses I2C on that
event, leaving the bus free for NFC the rest of the time.

Pin assignments (Raspberry Pi Pico):
  GP4   I2C0 SDA  → ST25DV16K SDA
  GP5   I2C0 SCL  → ST25DV16K SCL
  GP15  GPO input → ST25DV16K GPO  (active-low, needs PULL_UP)
  GP25  Onboard LED (heartbeat)
  GP28  LED data  → WS2812 DIN
"""

import time
import json
import micropython
from machine import I2C, Pin

from st25dv import ST25DV
from led_ring import LEDRing

# ── Hardware config ────────────────────────────────────────────────────
I2C_SDA       = 4
I2C_SCL       = 5
GPO_PIN       = 15
LED_PIN       = 28
NUM_LEDS      = 16
HEARTBEAT_PIN = "LED"  # onboard LED (Pico W — routed via WiFi chip)

# ── Timing ────────────────────────────────────────────────────────────
FRAME_MS     = 16    # ~60 fps for smooth LED animation
HEARTBEAT_MS = 500   # onboard LED toggle interval

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

    i2c       = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)
    tag       = ST25DV(i2c)
    ring      = LEDRing(Pin(LED_PIN), NUM_LEDS)
    heartbeat = Pin(HEARTBEAT_PIN, Pin.OUT)

    # ── Startup NDEF check ────────────────────────────────────────────
    # Report tag contents before any writes so we can see if something
    # at startup is erasing the NDEF record.
    try:
        raw = tag.read_ndef_text()
        print("startup NDEF:", raw)
    except Exception as e:
        print("startup NDEF read error:", e)

    # ── Configure GPO ────────────────────────────────────────────────
    try:
        tag.configure_gpo_rf_write()
        tag.clear_interrupt()
    except OSError as e:
        print("GPO config failed:", e)

    # ── Check NDEF again after GPO config ────────────────────────────
    try:
        raw = tag.read_ndef_text()
        print("post-config NDEF:", raw)
    except Exception as e:
        print("post-config NDEF read error:", e)

    # ── GPO interrupt ────────────────────────────────────────────────
    gpo = Pin(GPO_PIN, Pin.IN, Pin.PULL_UP)
    gpo.irq(trigger=Pin.IRQ_FALLING, handler=_gpo_irq)

    pattern = "off"
    if raw:
        pattern = json.loads(raw).get("pattern", "off")

    last_heartbeat_ms = 0
    print("TapUI_mc ready — pattern:", pattern)

    while True:
        now_ms = time.ticks_ms()

        # ── Handle GPO interrupt ──────────────────────────────────────
        if _tag_written:
            _tag_written = False
            try:
                raw = tag.read_ndef_text()
                if raw:
                    new_pattern = json.loads(raw).get("pattern", "off")
                    if new_pattern != pattern:
                        pattern = new_pattern
                        print("pattern:", pattern)
                tag.clear_interrupt()
            except Exception as e:
                print("read error:", e)

        # ── Animate LEDs ──────────────────────────────────────────────
        ring.update(pattern, now_ms)

        # ── Heartbeat ─────────────────────────────────────────────────
        if time.ticks_diff(now_ms, last_heartbeat_ms) >= HEARTBEAT_MS:
            heartbeat.toggle()
            last_heartbeat_ms = now_ms

        time.sleep_ms(FRAME_MS)


main()
