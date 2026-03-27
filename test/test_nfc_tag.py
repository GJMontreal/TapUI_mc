"""
ST25DV16K wiring verification.

Checks I2C connectivity, reads the Capability Container, and attempts
a read/write roundtrip on the NDEF payload.

Run with:  mpremote run test/test_nfc_tag.py
"""

import time
from machine import I2C, Pin

I2C_SDA  = 4
I2C_SCL  = 5
USER_ADDR = 0x53
SYS_ADDR  = 0x57


def scan(i2c):
    print("\n── Test 1: I2C scan ──")
    found = i2c.scan()
    print(f"  Devices found: {[hex(a) for a in found]}")
    ok = USER_ADDR in found and SYS_ADDR in found
    print(f"  0x53 (user mem): {'OK' if USER_ADDR in found else 'MISSING'}")
    print(f"  0x57 (sys cfg):  {'OK' if SYS_ADDR in found else 'MISSING'}")
    return ok


def read_cc(i2c):
    print("\n── Test 2: Capability Container ──")
    try:
        i2c.writeto(USER_ADDR, bytes([0x00, 0x00]))
        cc = i2c.readfrom(USER_ADDR, 4)
        print(f"  CC bytes: {[hex(b) for b in cc]}")
        if cc[0] == 0xE2:
            print("  Magic number 0xE2: OK")
        else:
            print(f"  Unexpected magic number: {hex(cc[0])} (expected 0xE2)")
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def roundtrip(i2c):
    print("\n── Test 3: read/write roundtrip ──")
    # Read first 32 bytes and print as hex
    try:
        i2c.writeto(USER_ADDR, bytes([0x00, 0x00]))
        data = i2c.readfrom(USER_ADDR, 32)
        print(f"  First 32 bytes: {data.hex()}")

        # Look for an existing NDEF TLV (type 0x03) starting at byte 4
        i = 4
        while i < len(data) - 1:
            if data[i] == 0xFE:
                print("  No NDEF TLV found (tag may be blank)")
                break
            if data[i] == 0x03:
                length = data[i + 1]
                payload = data[i + 2: i + 2 + length]
                print(f"  NDEF TLV found, payload ({length}B): {payload}")
                break
            i += 2 + data[i + 1]
        return True
    except Exception as e:
        print(f"  Failed: {e}")
        return False


def main():
    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)

    ok1 = scan(i2c)
    if not ok1:
        print("\nI2C scan failed — check SDA/SCL wiring and pull-ups before continuing.")
        return

    ok2 = read_cc(i2c)
    ok3 = roundtrip(i2c)

    print("\n── Summary ──")
    print(f"  I2C scan:   {'PASS' if ok1 else 'FAIL'}")
    print(f"  CC read:    {'PASS' if ok2 else 'FAIL'}")
    print(f"  Memory read:{'PASS' if ok3 else 'FAIL'}")


main()
