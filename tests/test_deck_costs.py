"""Deck affordability parity: the dimmed slots must match the engine mana costs."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_JS = ROOT / "static" / "js" / "ui.js"
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestDeckCosts(unittest.TestCase):
    def setUp(self):
        self.ui = UI_JS.read_text(encoding="utf-8")
        self.engine = ENGINE_JS.read_text(encoding="utf-8")

    def test_rogue_and_mage_slot4_costs_match_the_engine(self):
        self.assertIn(
            "rogue: { btnActionFireball: 4, btnActionBash: 6, btnActionHeal: 10, "
            "btnActionShieldWall: 8 }",
            self.ui,
        )
        self.assertIn(
            "mage: { btnActionFireball: 10, btnActionBash: 6, btnActionHeal: 10, "
            "btnActionShieldWall: 6 }",
            self.ui,
        )
        self.assertIn("Not enough mana for Fireball! (Needs 10 MP)", self.engine)
        self.assertIn("Not enough mana for Arcane Nova! (Needs 10 MP)", self.engine)

    def test_paladin_slot4_heal_stays_at_eight(self):
        self.assertIn(
            "paladin: { btnActionFireball: 10, btnActionBash: 4, btnActionHeal: 8, "
            "btnActionShieldWall: 6 }",
            self.ui,
        )


if __name__ == "__main__":
    unittest.main()
