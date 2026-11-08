"""Boss phase contract: each boss owns its phase text and summons."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestBossPhases(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def test_malakor_phases_are_type_gated(self):
        self.assertIn('monster.type === "boss_lich" && !monster.phase_two', self.js)
        self.assertIn('monster.type === "boss_lich" && !monster.phase_three', self.js)
        self.assertIn("Malakor tears open the vault floor", self.js)

    def test_other_bosses_have_their_own_phase_text(self):
        self.assertIn("const otherBoss = monster.is_boss", self.js)
        self.assertIn('monster.type !== "boss_choir"', self.js)
        self.assertIn("THE SEAL BREAKS!", self.js)

    def test_choir_split_searches_wider_rings_and_retries(self):
        self.assertIn("for (let ring = 2; ring <= 3; ring += 1)", self.js)
        self.assertIn("no room to split", self.js)
        self.assertIn("splits into ${split} echoing voices", self.js)


if __name__ == "__main__":
    unittest.main()
