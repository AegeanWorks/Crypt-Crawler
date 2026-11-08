"""The Hollow Choir's phase transition must beat a new hum roll."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestChoirPhasePriority(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def test_hum_waits_for_a_due_phase(self):
        self.assertIn('const choirPhaseDue = monster.type === "boss_choir"', self.js)
        self.assertIn("!monster.phase_two && monster.hp <= monster.max_hp * 0.5", self.js)
        self.assertIn("!monster.phase_three && monster.hp <= monster.max_hp * 0.25", self.js)
        self.assertIn("!choirPhaseDue", self.js)

    def test_split_turn_does_not_move_onto_the_new_echoes(self):
        start = self.js.index("The Hollow Choir splits into")
        end = self.js.index("} else {", start)
        self.assertIn("continue;", self.js[start:end])


if __name__ == "__main__":
    unittest.main()
