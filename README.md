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
| VBUS (pin 40) | VDD | 5V from USB; use 3V3 only for very dim/short strings |
| GND | GND | |

**WS2812 power:** The ring draws up to ~960mA at full white (16 LEDs × 60mA). Demo patterns run dimmed and stay well under USB limits, but avoid full-brightness white from USB alone.

**Level shifting:** GP28 is 3.3V logic; WS2812 at 5V expects ≥3.5V as logic high (0.7 × 5V). A 74AHCT125 buffer between GP28 and DIN is the clean fix — many demos skip it and get away with it, but it's marginal.

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
