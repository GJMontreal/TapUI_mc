"""
GPO configuration diagnostic.

Reads back GPO_CTRL (static) and GPO_CTRL_Dyn, then calls
configure_gpo_rf_write() and reads back again to confirm the
write stuck. Run with:  mpremote run test/test_gpo_config.py
"""

from machine import I2C, Pin
from st25dv import ST25DV

I2C_SDA = 4
I2C_SCL = 5
SYS_ADDR = 0x57

GPO_CTRL_REG = 0x0000
GPO_CTRL_DYN = 0x2000


def read_sys(i2c, addr):
    i2c.writeto(SYS_ADDR, bytes([addr >> 8, addr & 0xFF]))
    return i2c.readfrom(SYS_ADDR, 1)[0]


def report(i2c, label):
    stat = read_sys(i2c, GPO_CTRL_REG)
    try:
        dyn = read_sys(i2c, GPO_CTRL_DYN)
        dyn_str = hex(dyn)
    except OSError as e:
        dyn_str = "read failed: {}".format(e)
    print("{}: GPO_CTRL static={} GPO_CTRL_Dyn={}".format(label, hex(stat), dyn_str))


def main():
    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)
    tag = ST25DV(i2c)

    report(i2c, "before")
    tag.configure_gpo_rf_write()
    report(i2c, "after ")

    print("\nExpected: static=0x81, dyn=0x01")
    print("If static is not 0x81 the security session failed.")
    print("If dyn is not 0x01 GPO will not fire until next power cycle.")


main()
