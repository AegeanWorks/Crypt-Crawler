"""Cavern contrast contract: B2F floors/walls stay readable in the dark biome."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"


def _luminance(hex_color: str) -> float:
    def channel(value: int) -> float:
        c = value / 255
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)


class TestCavernContrast(unittest.TestCase):
    def setUp(self):
        self.js = RENDERER_JS.read_text(encoding="utf-8")

    def test_visible_cavern_floor_and_wall_are_readable(self):
        self.assertIn('altColor ? "#14343a" : "#102c31"', self.js)
        self.assertIn('ctx.fillStyle = isVis ? "#1b3a40" : "#0b1a1d"', self.js)
        floor = min(_luminance("#14343a"), _luminance("#102c31"))
        wall = _luminance("#1b3a40")
        self.assertGreaterEqual(floor, 0.02, "cavern floor is too dark to read")
        self.assertGreaterEqual(wall, 0.025, "cavern wall is too dark to read")

    def test_unexplored_cavern_stays_black(self):
        floor = min(_luminance("#14343a"), _luminance("#102c31"))
        self.assertLess(_luminance("#08181b"), floor * 0.5)
        self.assertLess(_luminance("#0b1a1d"), _luminance("#1b3a40") * 0.5)


if __name__ == "__main__":
    unittest.main()
