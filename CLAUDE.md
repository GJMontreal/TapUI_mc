# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MicroPython firmware for a Raspberry Pi Pico (RP2040) that forms the microcontroller side of the TapUI NFC demo. The Pico polls an ST25DV64K NFC EEPROM tag over I2C, reads a JSON payload written by the iOS TapUI app, drives a 16-LED WS2812 ring to match the requested pattern, and writes its uptime back to the tag.

Sibling iOS project: `../TapUI` (Swift/SwiftUI).

## Hardware

| Signal       | Pico Pin | Connected to             |
|--------------|----------|--------------------------|
| I2C0 SDA     | GP4      | ST25DV64K SDA            |
| I2C0 SCL     | GP5      | ST25DV64K SCL            |
| WS2812 DIN   | GP28     | LED ring data in         |

- **NFC tag:** ST25DV64K — dual-interface EEPROM (NFC + I2C). iOS app writes NDEF; Pico reads/writes via I2C at address `0x53`.
- **LED ring:** 16× WS2812 addressable RGB LEDs. Driven by MicroPython's built-in `neopixel` module (no PIO setup required).

## Tag Memory Layout

```
0x0000–0x0003  CC (Capability Container) — initialized by iOS app, preserved on write
0x0004+        TLV: 0x03 | length | NDEF message | 0xFE terminator
```

NDEF Text record payload is a JSON string: `{"pattern":"rainbow","uptime":42}`

**LED patterns (must match iOS app exactly):** `off` | `solid` | `rainbow` | `chase` | `pulse`

## Deploying to the Pico

Install [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html):
```
pip install mpremote
```

Copy source files (Pico must have MicroPython firmware installed):
```
mpremote cp src/st25dv.py :st25dv.py
mpremote cp src/led_ring.py :led_ring.py
mpremote cp src/main.py :main.py
```

Run interactively (without persisting to flash):
```
mpremote run src/main.py
```

Open a REPL:
```
mpremote
```

Reset the Pico:
```
mpremote reset
```

## Architecture

```
main.py
  ├── ST25DV (st25dv.py)    — I2C read/write of NDEF Text records
  └── LEDRing (led_ring.py) — pattern rendering onto NeoPixel ring
```

`main.py` runs a tight loop: read tag → update LEDs → (every 5 s) write uptime back to tag.

`st25dv.py` caches the CC on first write so it is never corrupted. Writes are page-aligned (4 bytes) with a 5 ms inter-page delay as required by the ST25DV64K datasheet.

`led_ring.py` patterns are time-based (driven by `time.ticks_ms()`), matching the animation math in the iOS `LEDRingView`.

## Key Constraints

- MicroPython only — no CircuitPython (different `neopixel` API).
- Do not reformat or shrink files with `mpy-cross` unless flash space becomes an issue; readability is preferred.
- The ST25DV64K I2C address (`0x53`) conflicts with some sensors. Verify with `mpremote exec "from machine import I2C, Pin; print(I2C(0, sda=Pin(4), scl=Pin(5)).scan())"` if the tag is not responding.
- Concurrent NFC + I2C access is not guarded. The uptime write interval (5 s) is intentionally long to minimize contention with the iOS app.
