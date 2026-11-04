"""Odds parity: stated README odds match coded odds in Python and shipped JS."""

import unittest
from pathlib import Path

from crawler.engagement import ENGAGEMENT_TUNING

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestOddsParity(unittest.TestCase):
    def test_python_matches_tuning(self):
        src = (ROOT / "crawler" / "rewards.py").read_text(encoding="utf-8")
        # Rewards must read the table, not hardcode fresh odds.
        self.assertIn("ENGAGEMENT_TUNING", src)

    def test_shipped_js_matches_tuning_rates(self):
        tune = ENGAGEMENT_TUNING
        js = ENGINE_JS.read_text(encoding="utf-8")
        # The shipped engine mirrors the Python table as TUNING (no fresh literals).
        self.assertIn("export const TUNING", js)
        self.assertIn("relicRate: 0.14", js)
        self.assertIn("jackpotRate: 0.20", js)
        self.assertIn("jackpotRate: 0.18", js)
        self.assertIn("jackpotMult: 2.4", js)
        self.assertIn("omenCapMult: 3.0", js)
        self.assertIn("baseMin: 17", js)
        self.assertIn("baseMin: 6", js)
        # Live branches read TUNING, never hardcoded odds.
        self.assertIn("TUNING.chest.relicRate", js)
        self.assertIn("TUNING.chest.jackpotRate", js)
        self.assertIn("TUNING.urn.jackpotRate", js)
        self.assertNotIn("roll >= 0.14 && roll < 0.34", js)
        self.assertNotIn("Math.random() < 0.18", js)
        # Table values equal the Python source of truth.
        self.assertAlmostEqual(tune["chest"]["relic_rate"], 0.14, places=6)
        self.assertAlmostEqual(tune["chest"]["jackpot_rate"], 0.20, places=6)
        self.assertAlmostEqual(tune["urn"]["jackpot_rate"], 0.18, places=6)

    def test_readme_states_current_odds(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        # README odds table is added in Commit A; until then this names the gap.
        self.assertIn("17+0-13", readme)


if __name__ == "__main__":
    unittest.main()
