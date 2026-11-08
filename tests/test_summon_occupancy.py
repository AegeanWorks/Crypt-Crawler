"""Bodies summoned during an enemy turn block movement on that same turn."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestSummonOccupancy(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def test_pending_monsters_are_registered_and_cleared(self):
        self.assertIn("this._pendingMonsters = newMonsters;", self.js)
        self.assertIn("this._pendingMonsters = null;", self.js)

    def test_occupancy_includes_pending_bodies(self):
        start = self.js.index("_isOccupied(x, y) {")
        end = self.js.index("handlePlayerDeath", start)
        self.assertIn("this._pendingMonsters.some", self.js[start:end])


if __name__ == "__main__":
    unittest.main()
