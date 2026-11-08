"""Strike targeting contract: an adjacent hovered enemy is the chosen target."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestStrikeTarget(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def test_strike_prefers_the_hovered_adjacent_enemy(self):
        start = self.js.index("tacticalStrike() {")
        end = self.js.index("tacticalFireball()", start)
        body = self.js[start:end]
        self.assertIn("this.renderer && this.renderer.hoverTile", body)
        self.assertIn("m.x === hover.x && m.y === hover.y", body)
        self.assertIn("if (!adj) adj = this.monsters.find(isAdjacent)", body)


if __name__ == "__main__":
    unittest.main()
