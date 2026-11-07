"""Death beat contract: feedback and HUD first, the ledger after a short pause."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestDeathBeat(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def test_death_updates_the_hud_before_the_modal(self):
        start = self.js.index("handlePlayerDeath(cause")
        end = self.js.index("handleVictory()", start)
        body = self.js[start:end]
        self.assertIn("ui.updateHero(this.player, this.turn, this.depth, this.kills)", body)
        self.assertIn("YOU PERISHED", body)
        self.assertIn("setTimeout(", body)
        self.assertIn("deathToken !== this.runToken", body)
        self.assertLess(body.index("ui.updateHero"), body.index("setTimeout("))

    def test_death_modal_is_delayed(self):
        self.assertIn("}, 750);", self.js)


if __name__ == "__main__":
    unittest.main()
