"""Hover title contract: no repeated champion affix, no overflow past the card."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"


class TestHoverTitle(unittest.TestCase):
    def setUp(self):
        self.js = RENDERER_JS.read_text(encoding="utf-8")

    def test_champion_name_does_not_repeat_the_affix_badge(self):
        self.assertIn('const affix = monster.is_boss ? "Boss" : ""', self.js)

    def test_title_is_fitted_inside_a_wider_card(self):
        self.assertIn("_fitText(ctx,", self.js)
        self.assertIn("const cardW = 168", self.js)
        self.assertIn("titleMax", self.js)

    def test_champion_affix_hints_cover_the_shipped_affixes(self):
        for affix in ("Swift", "Fortified", "Molten", "Vampiric"):
            self.assertIn(f'        {affix}: "', self.js)

    def test_hover_card_draws_the_affix_hint(self):
        self.assertIn("const affixHint =", self.js)
        self.assertIn("affixHint ? 12", self.js)


if __name__ == "__main__":
    unittest.main()
