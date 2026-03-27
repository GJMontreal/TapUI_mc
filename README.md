# TapUI_mc

MicroPython firmware for a Raspberry Pi Pico (RP2040) — the microcontroller side of the TapUI NFC demo. The Pico reads a JSON payload written to an ST25DV64K NFC tag by the [TapUI iOS app](../TapUI), drives a 16-LED WS2812 ring to match the requested pattern, and writes its uptime back to the tag.

## Wiring

### Pico → ST25DV64K

| Pico | ST25DV64K | Notes |
|------|-----------|-------|
| GP4 | SDA | 4.7kΩ pull-up to 3.3V |
| GP5 | SCL | 4.7kΩ pull-up to 3.3V |
| GP15 | GPO | 10kΩ pull-up to 3.3V (GPO is open-drain) |
| 3V3 | VCC | |
| GND | GND | |
| GND | E0 | Ties I2C address to 0x53 |

### Pico → WS2812 ring

| Pico | WS2812 | Notes |
|------|--------|-------|
| GP28 | DIN | 300–500Ω series resistor recommended |
| 3V3 | VDD | See note below |
| GND | GND | |

**WS2812 power:** WS2812B are spec'd at 3.5–5.3V, so 3.3V is slightly out of spec. In practice they work reliably at 3.3V — just dimmer. The upside is that 3.3V data also satisfies the logic-high threshold (0.7 × 3.3V = 2.31V), eliminating any level-shifting concern. The Pico's onboard 3.3V regulator is rated 300mA; 16 LEDs at demo brightness levels stay well under that.

## Deploying

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

Run interactively without writing to flash:

```
mpremote run src/main.py
```
