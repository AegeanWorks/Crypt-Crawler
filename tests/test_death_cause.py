"""Death-cause contract: status deaths end the turn and are named."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestDeathCause(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def test_status_ticks_return_their_cause(self):
        start = self.js.index("_tickPlayerStatuses() {")
        end = self.js.index("_tickMonsterStatuses()", start)
        body = self.js[start:end]
        self.assertIn('return "poison"', body)
        self.assertIn('return "burn"', body)
        self.assertIn("return null", body)

    def test_status_death_short_circuits_the_enemy_turn(self):
        start = self.js.index("finishPlayerTurn() {")
        end = self.js.index("_tickPlayerStatuses() {", start)
        body = self.js[start:end]
        self.assertIn("const statusDeath = this._tickPlayerStatuses()", body)
        self.assertIn("handlePlayerDeath(statusDeath)", body)
        self.assertIn("if (this.player.hp > 0) this._tickMonsterStatuses()", body)

    def test_enemy_loop_stops_when_the_hero_falls(self):
        start = self.js.index("processEnemyTurns() {")
        end = self.js.index("_stepToward(monster)", start)
        body = self.js[start:end]
        self.assertIn("if (this.player.hp <= 0) break;", body)


if __name__ == "__main__":
    unittest.main()
