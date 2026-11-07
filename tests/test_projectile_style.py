"""Projectile style contract: arrows read physical, spells keep a glowing trail."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestProjectileStyle(unittest.TestCase):
    def setUp(self):
        self.renderer = RENDERER_JS.read_text(encoding="utf-8")
        self.engine = ENGINE_JS.read_text(encoding="utf-8")

    def test_renderer_has_arrow_and_bolt_shapes(self):
        self.assertIn('kind = "bolt"', self.renderer)
        self.assertIn('p.kind === "arrow"', self.renderer)
        self.assertIn("ctx.rotate(angle)", self.renderer)
        self.assertIn("Math.cos(angle) * 20", self.renderer)

    def test_archer_fires_the_arrow_shape(self):
        self.assertIn('"#e2e8f0", "arrow"', self.engine)
        self.assertIn("sounds.playBow()", self.engine)


if __name__ == "__main__":
    unittest.main()
