"""Death effect contract: every defeat leaves a visible burst at its tile."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestDeathEffect(unittest.TestCase):
    def setUp(self):
        self.renderer = RENDERER_JS.read_text(encoding="utf-8")
        self.engine = ENGINE_JS.read_text(encoding="utf-8")

    def test_renderer_has_a_death_burst(self):
        self.assertIn("addDeathBurst(x, y, color", self.renderer)
        self.assertIn("this.addShockwave(x, y, color, 48)", self.renderer)
        self.assertIn("this.addParticles(x, y, color, 16)", self.renderer)

    def test_defeat_uses_the_death_burst(self):
        start = self.engine.index("_handleMonsterDefeat(monster) {")
        end = self.engine.index("triggerSlotAction(slotNum)", start)
        body = self.engine[start:end]
        self.assertIn("addDeathBurst(monster.x, monster.y", body)


if __name__ == "__main__":
    unittest.main()
