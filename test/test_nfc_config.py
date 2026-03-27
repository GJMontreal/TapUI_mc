"""
ST25DV16K NFC configuration diagnostic and repair.

Checks whether the RF interface is enabled and memory area 1 is
readable via NFC, then writes a simple NDEF Text record so you can
verify with a phone app (e.g. NFC Tap).

Run with:  mpremote run test/test_nfc_config.py
"""

from machine import I2C, Pin
import time

I2C_SDA  = 4
I2C_SCL  = 5
USER_ADDR = 0x53
SYS_ADDR  = 0x57

# Dynamic register addresses (no password required)
RF_MNGT_DYN  = 0x2002   # RF management — bit 0: RF_DISABLE, bit 1: RF_SLEEP
IT_STS_DYN   = 0x2005   # interrupt status (read to clear)

# Static register addresses (require security session to write)
RF_MNGT_STAT = 0x0003   # static RF management
RFA1SS       = 0x0004   # area 1 RF access security
I2C_PWD_REG  = 0x0900   # password register

# RFAxSS access right values
RF_RW_OPEN   = 0x00     # read/write, no password


def read_sys(i2c, addr, length=1):
    i2c.writeto(SYS_ADDR, bytes([addr >> 8, addr & 0xFF]))
    return i2c.readfrom(SYS_ADDR, length)


def write_sys(i2c, addr, data: bytes):
    i2c.writeto(SYS_ADDR, bytes([addr >> 8, addr & 0xFF]) + data)
    time.sleep_ms(5)


def open_security_session(i2c, password: bytes = b"\x00" * 8):
    msg = bytes([I2C_PWD_REG >> 8, I2C_PWD_REG & 0xFF])
    msg += password + b"\x09" + password
    i2c.writeto(SYS_ADDR, msg)


def check_rf_management(i2c):
    print("\n── RF management ──")
    stat = read_sys(i2c, RF_MNGT_STAT)[0]
    print(f"  RF_MNGT static: {hex(stat)}")
    if stat & 0x01:
        print("  RF_DISABLE set in static register — clearing (requires security session)...")
        open_security_session(i2c)
        time.sleep_ms(10)
        write_sys(i2c, RF_MNGT_STAT, bytes([0x00]))
        time.sleep_ms(20)
        stat = read_sys(i2c, RF_MNGT_STAT)[0]
        print(f"  RF_MNGT static after fix: {hex(stat)}")
    else:
        print("  RF enabled (OK) — phone detecting tag confirms this")
    return True


def check_area1_security(i2c):
    print("\n── Area 1 RF access security ──")
    rfa1 = read_sys(i2c, RFA1SS)[0]
    print(f"  RFA1SS: {hex(rfa1)}")
    read_prot  = (rfa1 >> 2) & 0x03
    write_prot = (rfa1 >> 4) & 0x03
    print("  Read protection:  " + ("open (OK)" if read_prot == 0 else "PROTECTED (level {})".format(read_prot)))
    print("  Write protection: " + ("open (OK)" if write_prot == 0 else "PROTECTED (level {})".format(write_prot)))

    if read_prot != 0:
        print("  Opening area 1 read access (using default password)...")
        open_security_session(i2c)
        write_sys(i2c, RFA1SS, bytes([RF_RW_OPEN]))
        rfa1 = read_sys(i2c, RFA1SS)[0]
        print(f"  RFA1SS after fix: {hex(rfa1)}")


def check_cc(i2c):
    print("\n── Capability Container ──")
    i2c.writeto(USER_ADDR, bytes([0x00, 0x00]))
    cc = i2c.readfrom(USER_ADDR, 4)
    print(f"  CC: {[hex(b) for b in cc]}")
    # Byte 2: MLEN — 0xFF signals 16Kbit tag using 4-byte CC
    if cc[2] != 0xFF:
        print(f"  MLEN is {hex(cc[2])}, expected 0xFF for ST25DV16K — fixing...")
        fixed_cc = bytes([cc[0], cc[1], 0xFF, cc[3]])
        i2c.writeto(USER_ADDR, bytes([0x00, 0x00]) + fixed_cc)
        time.sleep_ms(5)
        i2c.writeto(USER_ADDR, bytes([0x00, 0x00]))
        cc = i2c.readfrom(USER_ADDR, 4)
        print(f"  CC after fix: {[hex(b) for b in cc]}")
    else:
        print("  MLEN OK")


def write_test_ndef(i2c):
    print("\n── Writing test NDEF Text record ──")
    text    = '{"pattern":"solid"}'
    lang    = b"en"
    payload = bytes([len(lang)]) + lang + text.encode()
    record  = bytes([0xD1, 0x01, len(payload), 0x54]) + payload
    tlv     = bytes([0x03, len(record)]) + record + bytes([0xFE])

    # Read existing CC
    i2c.writeto(USER_ADDR, bytes([0x00, 0x00]))
    cc = i2c.readfrom(USER_ADDR, 4)
    image = cc + tlv
    image += b"\x00" * ((-len(image)) % 4)  # pad to 4-byte boundary

    for offset in range(0, len(image), 4):
        page = image[offset:offset + 4]
        i2c.writeto(USER_ADDR, bytes([offset >> 8, offset & 0xFF]) + page)
        time.sleep_ms(5)

    print(f"  Wrote {len(image)} bytes")
    print(f"  Payload: {text}")
    print("  Tap the tag with NFC Tap — should show a Text record with the JSON above")


def main():
    i2c = I2C(0, sda=Pin(I2C_SDA), scl=Pin(I2C_SCL), freq=400_000)

    check_rf_management(i2c)
    check_area1_security(i2c)
    check_cc(i2c)
    write_test_ndef(i2c)


main()
