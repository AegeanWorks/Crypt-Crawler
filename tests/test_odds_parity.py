"""Odds parity: stated README odds match coded odds in Python and shipped JS."""

import re
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
        # Chest relic / jackpot thresholds.
        self.assertIn("0.14", js)
        self.assertIn("0.34", js)
        self.assertIn("0.18", js)
        self.assertIn("2.4", js)
        self.assertIn("3.0", js)
        # Jackpot threshold must equal relic + jackpot from the table.
        expected = tune["chest"]["relic_rate"] + tune["chest"]["jackpot_rate"]
        m = re.search(r"if\s*\(\s*roll\s*>=\s*0\.14\s*&&\s*roll\s*<\s*([0-9.]+)", js)
        self.assertIsNotNone(m, "chest jackpot branch not found in engine.js")
        self.assertAlmostEqual(float(m.group(1)), expected, places=6)

    def test_readme_states_current_odds(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        # README odds table is added in Commit A; until then this names the gap.
        self.assertIn("17+0-13", readme)


if __name__ == "__main__":
    unittest.main()
