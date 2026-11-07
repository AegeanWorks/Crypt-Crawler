"""Enemy pathing contract: a blocked greedy step falls back to a free BFS step."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestEnemyPathing(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def test_blocked_step_falls_back_to_the_path(self):
        self.assertIn("_stepTowardPath(monster)", self.js)
        self.assertIn("if (!this._stepToward(monster)) this._stepTowardPath(monster)", self.js)
        self.assertEqual(self.js.count("this._stepTowardPath(monster)"), 2)

    def test_path_respects_walls_and_occupied_tiles(self):
        start = self.js.index("_stepTowardPath(monster) {")
        end = self.js.index("_hasLineOfSight(", start)
        body = self.js[start:end]
        self.assertIn("cameFrom", body)
        self.assertIn("this.dungeon.isWalkable(nx, ny)", body)
        self.assertIn("this._isOccupied(nx, ny)", body)
        self.assertIn("nx === this.player.x && ny === this.player.y", body)


if __name__ == "__main__":
    unittest.main()
