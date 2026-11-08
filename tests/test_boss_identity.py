"""Only Malakor uses Malakor's death text, lore and crown."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestBossIdentity(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def test_boss_death_uses_the_monster_payload(self):
        self.assertIn("const finalBoss = this.depth >= 3;", self.js)
        self.assertIn("if (monster.type === \"boss_lich\")", self.js)
        self.assertIn("BOSS_LOOT_ITEMS[monster.loot_drop]", self.js)
        self.assertIn("this.finalBoss = {", self.js)

    def test_victory_modal_reads_the_recorded_boss(self):
        self.assertIn("const finalBoss = this.finalBoss || {", self.js)
        self.assertIn("const lootLine = finalBoss.lootName", self.js)
        self.assertIn("defeated ${finalBoss.name}", self.js)

    def test_stairs_barrier_names_the_living_boss(self):
        self.assertIn("const livingBoss = this.monsters.find((m) => m.is_boss && m.hp > 0);", self.js)
        self.assertIn("You must slay ${livingBoss.name} first!", self.js)


if __name__ == "__main__":
    unittest.main()
