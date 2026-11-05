"""Swarm-triage regression locks: verified true findings only (failing-first)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE = ROOT / "static" / "js" / "engine.js"
UI = ROOT / "static" / "js" / "ui.js"
AUDIO = ROOT / "static" / "js" / "audio.js"
SERVER = ROOT / "crawler" / "server.py"


class TestSwarmFixes(unittest.TestCase):
    def test_crown_cannot_be_sold(self):
        js = ENGINE.read_text(encoding="utf-8")
        self.assertTrue("sellInventoryItem" in js, "missing sell path")
        # Direct-index sale must refuse the trophy even when hidden from the tab.
        block = js.split("  sellInventoryItem(index) {")[1].split("  tacticalStrike")[0]
        self.assertTrue("crown_eternity" in block, "crown guard missing")

    def test_grantxp_rejects_nonpositive(self):
        js = ENGINE.read_text(encoding="utf-8")
        block = js.split("_grantXp(amount)")[1].split("updateSigils")[0]
        self.assertIn("amount", block)
        # Bare `if (!amount)` lets -50 through (truthy); must guard <= 0.
        self.assertTrue("<= 0" in block or "Number.isFinite" in block)

    def test_attack_monster_guards_corpse_and_corpse_attacker(self):
        js = ENGINE.read_text(encoding="utf-8")
        block = js.split("  attackMonster(monster) {")[1].split("  _handleMonsterDefeat")[0]
        self.assertTrue("monster.hp <= 0" in block, "corpse guard missing")
        self.assertTrue("this.player.hp <= 0" in block, "dead-attacker guard missing")

    def test_heal_costs_match_engine(self):
        ui = UI.read_text(encoding="utf-8")
        # Engine + Python charge 8 MP for Divine Healing on every class.
        self.assertTrue("btnActionHeal: 8" in ui, "heal 8 missing")
        self.assertTrue("btnActionHeal: 10" not in ui, "stale heal 10 remains")

    def test_surge_docs_match_barrier(self):
        from crawler.engagement import ENGAGEMENT_TUNING
        self.assertTrue(ENGAGEMENT_TUNING["surge"]["bonus_def"] == 6, "tuning not 6")
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertTrue("+6 DEF" in readme, "readme not +6")
        js = ENGINE.read_text(encoding="utf-8")
        self.assertTrue("+6 DEF Barrier" in js, "log not +6")

    def test_audio_resume_caught(self):
        js = AUDIO.read_text(encoding="utf-8")
        self.assertTrue(".catch" in js or "try" in js.split("resume()")[0].split("init()")[-1])

    def test_seed_zero_is_deterministic(self):
        srv = SERVER.read_text(encoding="utf-8")
        # seed=0 must not silently become random (None).
        self.assertTrue("raw_seed != 0" not in srv, "seed 0 still mapped to random")
        js = ENGINE.read_text(encoding="utf-8")
        # `seed || Date.now()` treats 0 as missing; must use nullish check.
        self.assertTrue("seed || Date.now()" not in js, "falsy seed check remains")
        # All runSeed/seed fallbacks must be nullish-safe (0 is valid).
        self.assertNotIn("this.runSeed ||", js, "runSeed falsy fallback remains")
        self.assertNotIn("runSeed || 42", js, "bounty seed falsy fallback remains")
        self.assertNotIn("seed || 1234", js, "offline seed falsy fallback remains")
        self.assertNotIn("dungeon.seed ||", js, "dungeon seed falsy fallback remains")
        self.assertNotIn("if (!this.runSeed)", js, "runSeed falsy guard remains")
        self.assertIn("Number.isFinite(this.runSeed)", js, "runSeed nullish guard missing")
        self.assertIn("Number.isFinite(runSeed)", js, "bounty nullish guard missing")


if __name__ == "__main__":
    unittest.main()
