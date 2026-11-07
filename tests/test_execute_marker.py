"""Execute feedback contract: the skull and bonus preview belong to the rogue."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"


class TestExecuteMarker(unittest.TestCase):
    def setUp(self):
        self.js = RENDERER_JS.read_text(encoding="utf-8")

    def test_map_skull_is_rogue_only(self):
        self.assertIn('heroClass === "rogue"', self.js)
        self.assertIn("this._drawMonster(ctx, monster, ts, timestamp, player.hero_class", self.js)

    def test_tooltip_execute_and_range_are_rogue_only(self):
        self.assertIn('player.hero_class === "rogue"', self.js)
        self.assertIn("const execute = player.hero_class", self.js)
        self.assertIn("1.25", self.js)


if __name__ == "__main__":
    unittest.main()
