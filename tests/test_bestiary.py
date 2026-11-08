"""Bestiary coverage: every killable enemy type has a Records row."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_JS = ROOT / "static" / "js" / "ui.js"
ENGINE_JS = ROOT / "static" / "js" / "engine.js"

MONSTER_IDS = (
    "skeleton", "goblin", "spider", "bat", "necromancer", "wraith", "archer",
    "hound", "mimic", "boss_lich", "vault_warden", "boss_choir", "choir_echo",
)


class TestBestiary(unittest.TestCase):
    def setUp(self):
        self.ui = UI_JS.read_text(encoding="utf-8")
        self.engine = ENGINE_JS.read_text(encoding="utf-8")

    def test_every_killable_type_has_a_records_row(self):
        for monster_id in MONSTER_IDS:
            self.assertIn(f'id: "{monster_id}"', self.ui, f"missing bestiary row for {monster_id}")

    def test_choir_echo_is_a_real_spawned_type(self):
        self.assertIn('type: "choir_echo"', self.engine)
        self.assertIn("recordMonsterDefeat(monster.type, monster.name)", self.engine)

    def test_foundry_bosses_get_a_dynamic_row(self):
        self.assertIn("for (const [id, entry] of Object.entries(r.bestiary", self.ui)
        self.assertIn("entry.name || fallbackName", self.ui)
        self.assertIn("if (monsterName) rec.bestiary[monsterType].name = monsterName;", self.engine)


if __name__ == "__main__":
    unittest.main()
