"""Bounty modal readability: all three contracts fit above the fold."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_JS = ROOT / "static" / "js" / "ui.js"


class TestBountyModal(unittest.TestCase):
    def setUp(self):
        self.js = UI_JS.read_text(encoding="utf-8")

    def test_bounty_list_cap_is_viewport_relative(self):
        start = self.js.index("showBountiesModal(")
        end = self.js.index("showHallOfRecordsModal(", start)
        body = self.js[start:end]
        self.assertNotIn("max-height: 280px", body, "fixed 280px cap clips the third contract")
        self.assertIn("max-height: min(", body, "use a viewport-aware cap")
        self.assertIn("vh", body, "the cap must scale with the viewport")
        self.assertIn("overflow-y: auto", body, "short screens still scroll")


if __name__ == "__main__":
    unittest.main()
