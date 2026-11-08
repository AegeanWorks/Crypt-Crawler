"""Reduced motion freezes ambience, not the transient hit flash."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"


class TestReducedMotionFlash(unittest.TestCase):
    def setUp(self):
        self.js = RENDERER_JS.read_text(encoding="utf-8")

    def _body(self, start_marker, end_marker):
        start = self.js.index(start_marker)
        end = self.js.index(end_marker, start)
        return self.js[start:end]

    def test_player_flash_uses_live_clock(self):
        body = self._body("  _drawPlayer(ctx, player, ts, timestamp) {", "  _drawTorchlight(")
        self.assertNotIn("(timestamp - player._hitFlash)", body)
        self.assertIn("performance.now()", body)

    def test_monster_flash_uses_live_clock(self):
        body = self._body("  _drawMonster(", "  _drawPlayer(")
        self.assertNotIn("(timestamp - monster._hitFlash)", body)
        self.assertIn("performance.now()", body)


if __name__ == "__main__":
    unittest.main()
