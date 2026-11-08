"""Save version contract: write and read the same SAVE_VERSION, refuse others."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestSaveVersion(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def test_save_and_loader_share_one_version_constant(self):
        self.assertIn("export const SAVE_VERSION = 2;", self.js)
        self.assertIn("version: SAVE_VERSION", self.js)
        self.assertIn("data.version !== SAVE_VERSION", self.js)

    def test_refusal_leaves_the_stored_save_untouched(self):
        start = self.js.index("loadSavedRun() {")
        end = self.js.index("clearSavedRun()", start)
        body = self.js[start:end]
        self.assertIn("Refusing unsupported save version", body)
        self.assertNotIn("removeItem", body)
        self.assertNotIn("setItem", body)

    def test_kill_streak_is_saved_restored_and_cleared(self):
        self.assertIn("killStreak: this.killStreak", self.js)
        self.assertIn("turnsSinceKill: this.turnsSinceKill", self.js)
        self.assertIn("this.killStreak = Number.isFinite(saved.killStreak)", self.js)
        self.assertIn("this.ui.updateStreak(this.killStreak)", self.js)
        self.assertIn("this.ui.updateStreak(0)", self.js)

    def test_explored_map_is_saved_and_restored(self):
        self.assertIn("explored: this.dungeon.explored", self.js)
        dungeon_js = (ROOT / "static" / "js" / "dungeon.js").read_text(encoding="utf-8")
        self.assertIn("const savedExplored", dungeon_js)
        self.assertIn("Boolean(savedExplored?.[y]?.[x])", dungeon_js)


if __name__ == "__main__":
    unittest.main()
