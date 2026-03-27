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

### Pico → TXS0102 → WS2812 ring

The WS2812 is powered from 5V (VBUS) and requires ≥3.5V logic high; the Pico outputs 3.3V. A TXS0102 level shifter bridges the two.

| Pico | TXS0102 | Notes |
|------|---------|-------|
| 3V3 | VCCA | Low-voltage reference |
| VBUS | VCCB | High-voltage reference |
| 3V3 | OE | Always enabled |
| GND | GND | |
| GP28 | A1 | Data in (3.3V side) |

| TXS0102 | WS2812 | Notes |
|---------|--------|-------|
| B1 | DIN | Data out (5V side); 300–500Ω series resistor recommended |

| Pico | WS2812 | |
|------|--------|-|
| VBUS | VDD | 5V from USB |
| GND | GND | |

**Note:** The TXS0102 supports up to 24Mbps (push-pull); WS2812 runs at 800kHz, well within spec.

## Deploying

### 1. Install MicroPython on the Pico

1. Download the latest MicroPython `.uf2` for the Pico from [micropython.org/download/RPI_PICO](https://micropython.org/download/RPI_PICO/)
2. Hold the **BOOTSEL** button on the Pico, plug it into USB, then release the button
3. It mounts as a drive called `RPI-RP2` — drag the `.uf2` onto it
4. The Pico reboots automatically into MicroPython

### 2. Install mpremote

Install [mpremote](https://docs.micropython.org/en/latest/reference/mpremote.html):

```
pip install mpremote
```

### 3. Copy source files

```
mpremote cp src/st25dv.py :st25dv.py
mpremote cp src/led_ring.py :led_ring.py
mpremote cp src/main.py :main.py
```

Run interactively without persisting to flash:

```
mpremote run src/main.py
```
