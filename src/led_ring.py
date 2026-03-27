"""
WS2812 LED ring driver — patterns mirror the iOS TapUI app.

Patterns: off | solid | rainbow | chase | pulse
"""

import math
from neopixel import NeoPixel
from machine import Pin


class LEDRing:
    def __init__(self, pin: Pin, num_leds: int = 16):
        self._np = NeoPixel(pin, num_leds)
        self._n  = num_leds

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def update(self, pattern: str, t_ms: int):
        """Render one frame for the given pattern at time t_ms."""
        t = t_ms / 1000.0
        dispatch = {
            "off":     self._off,
            "solid":   self._solid,
            "rainbow": self._rainbow,
            "chase":   self._chase,
            "pulse":   self._pulse,
        }
        dispatch.get(pattern, self._off)(t)
        self._np.write()

    # ------------------------------------------------------------------
    # Patterns
    # ------------------------------------------------------------------

    def _off(self, _t: float):
        self._fill((0, 0, 0))

    def _solid(self, _t: float):
        self._fill((200, 200, 200))

    def _rainbow(self, t: float):
        for i in range(self._n):
            hue = (i / self._n + t * 0.2) % 1.0
            self._np[i] = _hsv(hue, 1.0, 0.5)

    def _chase(self, t: float):
        pos = (t * 2.0) % 1.0
        for i in range(self._n):
            dist = abs(i / self._n - pos)
            dist = min(dist, 1.0 - dist)
            bright = max(0.0, 1.0 - dist * self._n * 0.5)
            v = int(bright * 200)
            self._np[i] = (0, v, v)

    def _pulse(self, t: float):
        bright = (math.sin(t * 2 * math.pi) + 1) / 2
        v = int(bright * 200)
        self._fill((v, v, v))

    # ------------------------------------------------------------------

    def _fill(self, color: tuple):
        for i in range(self._n):
            self._np[i] = color


def _hsv(h: float, s: float, v: float) -> tuple:
    if s == 0:
        c = int(v * 255)
        return (c, c, c)
    i = int(h * 6) % 6
    f = h * 6 - int(h * 6)
    p = v * (1 - s)
    q = v * (1 - f * s)
    t = v * (1 - (1 - f) * s)
    r, g, b = [(v, t, p), (q, v, p), (p, v, t), (p, q, v), (t, p, v), (v, p, q)][i]
    return (int(r * 255), int(g * 255), int(b * 255))
