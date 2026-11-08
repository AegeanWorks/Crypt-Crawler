"""Molten counter-burn gives the same hit feedback as any other blow."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestMoltenFeedback(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")
        start = self.js.index("Molten Champion Counter-Burn")
        end = self.js.index("Weapon on-hit procs", start)
        self.block = self.js[start:end]

    def test_counter_burn_is_a_real_hit(self):
        self.assertIn("this.player.hp = Math.max(0, this.player.hp - 2);", self.block)
        self.assertIn("this.player._hitFlash = performance.now();", self.block)
        self.assertIn("sounds.playHit(false);", self.block)


if __name__ == "__main__":
    unittest.main()
