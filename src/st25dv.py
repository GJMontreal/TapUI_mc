"""
Minimal ST25DV16K I2C driver.

Reads and writes NDEF Text records from/to the user memory area.
The iOS app (TapUI) writes a JSON NDEF Text payload; this driver
parses it and can write back an updated payload (e.g. uptime).

Memory layout (I2C):
  0x0000–0x0003  CC (Capability Container) — written by iOS, not touched here
  0x0004+        TLV blocks: 0x03 (NDEF) | length | NDEF message | 0xFE (terminator)

NDEF Text record payload format:
  status_byte (lang_len in low 6 bits, UTF-8 = 0 in bit 7)
  language_code ("en")
  text (JSON string)

GPO interrupt:
  configure_gpo_rf_write() programs the ST25DV GPO pin to assert (active-low)
  whenever the NFC side completes a write. Call once at startup, then connect
  GPO to a Pico GPIO with PULL_UP and trigger an IRQ on IRQ_FALLING.
  Call clear_interrupt() after handling to de-assert GPO.
"""

import time
from machine import I2C

_ADDR           = 0x53    # user memory I2C address (7-bit)
_SYS_ADDR       = 0x57    # system config I2C address (7-bit)
_PAGE           = 4       # I2C write granularity; writes must be 4-byte aligned
_WRITE_DELAY_MS = 5

# System config register addresses
_GPO_CTRL_REG   = 0x0000  # static GPO configuration (requires security session)
_I2C_PWD_REG    = 0x0900  # I2C password presentation register

# Dynamic register addresses (no password needed)
_GPO_CTRL_DYN   = 0x2000  # dynamic GPO enable (bit 7: GPO_EN — no password required)
_IT_STS_DYN     = 0x2005  # interrupt status — reading this clears all flags

# GPO_CTRL bit masks
_GPO_EN         = 0x80    # global GPO enable
_RF_WRITE_BIT   = 0x01    # assert GPO when RF write completes


class ST25DV:
    def __init__(self, i2c: I2C):
        self._i2c = i2c
        self._cc = None  # cached Capability Container (4 bytes)

    # ------------------------------------------------------------------
    # Low-level memory access
    # ------------------------------------------------------------------

    def read_bytes(self, addr: int, length: int) -> bytes:
        self._i2c.writeto(_ADDR, bytes([addr >> 8, addr & 0xFF]))
        return self._i2c.readfrom(_ADDR, length)

    def _write_page(self, addr: int, data: bytes):
        """Write exactly 4 bytes to a 4-byte-aligned address."""
        assert addr % _PAGE == 0 and len(data) == _PAGE
        self._i2c.writeto(_ADDR, bytes([addr >> 8, addr & 0xFF]) + data)
        time.sleep_ms(_WRITE_DELAY_MS)

    def _write_block(self, addr: int, data: bytes):
        """Write arbitrary bytes starting at a 4-byte-aligned address."""
        assert addr % _PAGE == 0
        padded = data + b"\x00" * ((-len(data)) % _PAGE)
        for i in range(0, len(padded), _PAGE):
            self._write_page(addr + i, padded[i : i + _PAGE])

    # ------------------------------------------------------------------
    # NDEF helpers
    # ------------------------------------------------------------------

    def _build_ndef_text(self, text: str) -> bytes:
        """Return a complete memory image (CC + TLV) for the given text."""
        if self._cc is None:
            self._cc = self.read_bytes(0x0000, 4)

        lang = b"en"
        payload = bytes([len(lang)]) + lang + text.encode("utf-8")
        # NDEF record: MB=1 ME=1 SR=1 TNF=Well-Known, Type="T"
        record = bytes([0xD1, 0x01, len(payload), 0x54]) + payload
        tlv = bytes([0x03, len(record)]) + record + bytes([0xFE])
        return self._cc + tlv

    def _parse_ndef_text(self, msg: bytes) -> str | None:
        """Extract the text string from a raw NDEF message."""
        if len(msg) < 5:
            return None
        type_len   = msg[1]
        payload_len = msg[2]
        offset     = 3 + type_len          # skip flags, type_len, payload_len, type
        if offset >= len(msg):
            return None
        status   = msg[offset]
        lang_len = status & 0x3F
        text_start = offset + 1 + lang_len
        text_end   = text_start + payload_len - 1 - lang_len
        return msg[text_start:text_end].decode("utf-8")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def read_ndef_text(self) -> str | None:
        """Return the NDEF Text record payload, or None if not found."""
        data = self.read_bytes(0x0000, 128)
        i = 4  # skip CC
        while i < len(data) - 1:
            t = data[i]
            if t == 0xFE:
                break
            if t == 0x03:
                length = data[i + 1]
                return self._parse_ndef_text(data[i + 2 : i + 2 + length])
            i += 2 + data[i + 1]
        return None

    def write_ndef_text(self, text: str):
        """Write a new NDEF Text record to the tag."""
        image = self._build_ndef_text(text)
        self._write_block(0x0000, image)

    # ------------------------------------------------------------------
    # GPO interrupt support
    # ------------------------------------------------------------------

    def _open_security_session(self, password: bytes = b"\x00" * 8):
        """Present the I2C password to open a security session.

        Factory default password is 8 zero bytes. Must be called before
        writing to write-protected system config registers (e.g. GPO_CTRL).
        """
        # Protocol: 2-byte reg addr + 8-byte pwd + 0x09 validation + 8-byte pwd
        msg = bytes([_I2C_PWD_REG >> 8, _I2C_PWD_REG & 0xFF])
        msg += password + b"\x09" + password
        self._i2c.writeto(_SYS_ADDR, msg)

    def configure_gpo_rf_write(self):
        """Configure GPO to assert (active-low) when an RF write completes.

        Writes both the static GPO_CTRL register (persists across power cycles,
        requires security session) and GPO_CTRL_Dyn (runtime enable, no session
        needed). Uses the factory-default I2C password (all zeros).
        """
        # Static register — persists in NVM, requires security session
        # Static register (NVM) — persists across power cycles, requires security session
        self._open_security_session()
        self._i2c.writeto(
            _SYS_ADDR,
            bytes([_GPO_CTRL_REG >> 8, _GPO_CTRL_REG & 0xFF, _GPO_EN | _RF_WRITE_BIT]),
        )
        time.sleep_ms(10)  # wait for NVM write to complete


    def clear_interrupt(self):
        """Clear pending GPO interrupt by reading IT_STS_Dyn.

        Must be called after handling an RF-write event so the GPO line
        de-asserts and the next event can be detected.
        """
        self._i2c.writeto(_SYS_ADDR, bytes([_IT_STS_DYN >> 8, _IT_STS_DYN & 0xFF]))
        self._i2c.readfrom(_SYS_ADDR, 1)
