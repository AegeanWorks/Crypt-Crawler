"""Visual effects never consume the seeded gameplay RNG."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"


class TestEffectsRng(unittest.TestCase):
    def setUp(self):
        self.js = RENDERER_JS.read_text(encoding="utf-8")

    def test_renderer_has_its_own_random_stream(self):
        self.assertIn("this._fxRandomState = 0x9e3779b9;", self.js)
        self.assertIn("_fxRandom() {", self.js)
        self.assertIn("Math.imul(this._fxRandomState, 1664525)", self.js)

    def test_renderer_never_calls_the_gameplay_rng(self):
        self.assertNotIn("Math.random(", self.js)


if __name__ == "__main__":
    unittest.main()
