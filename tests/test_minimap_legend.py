"""Minimap legend contract: every map colour is named next to the map."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"


class TestMinimapLegend(unittest.TestCase):
    def setUp(self):
        self.js = RENDERER_JS.read_text(encoding="utf-8")

    def test_minimap_draws_a_named_legend(self):
        self.assertIn("_drawMinimapLegend(ctx, mx, my, mw, mh)", self.js)
        for label in ("Stairs", "Chest", "Shop", "Sigil", "Vault", "Trap", "Shrine", "Pact", "Soul"):
            self.assertIn(f'"{label}"', self.js, f"missing minimap legend label {label}")

    def test_trap_blip_is_distinct_from_vault_and_stairs(self):
        self.assertIn('ctx.fillStyle = "#f6ad55"', self.js)
        self.assertIn('"#d69e2e"', self.js)
        self.assertIn('"#ecc94b"', self.js)


if __name__ == "__main__":
    unittest.main()
