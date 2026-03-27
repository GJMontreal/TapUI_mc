"""
GPO wiring check using RF_ACTIVITY.

Reconfigures GPO to assert when an NFC field is detected (no write
needed). If the GPO line goes low when you bring the phone near,
the wiring is good and the issue is RF_WRITE not triggering.

Run with:  mpremote run test/test_gpo_activity.py

Restore RF_WRITE config afterward with:
  mpremote run test/test_gpo_config.py
"""

import time
from machine import I2C, Pin
from st25dv import ST25DV

I2C_SDA  = 4
I2C_SCL  = 5
SYS_ADDR = 0x57

GPO_CTRL_REG  = 0x0000
GPO_EN        = 0x80
RF_ACTIVITY   = 0x20   # assert on NFC field detected/lost


def main():
    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)
    tag = ST25DV(i2c)

    tag._open_security_session()
    i2c.writeto(SYS_ADDR, bytes([GPO_CTRL_REG >> 8, GPO_CTRL_REG & 0xFF, GPO_EN | RF_ACTIVITY]))
    time.sleep_ms(10)  # wait for NVM write to complete

    i2c.writeto(SYS_ADDR, bytes([GPO_CTRL_REG >> 8, GPO_CTRL_REG & 0xFF]))
    val = i2c.readfrom(SYS_ADDR, 1)[0]
    print("GPO_CTRL set to:", hex(val), "(expected 0xa0)")
    print("Now bring the phone near the tag and watch the GPO line on the scope.")


main()
