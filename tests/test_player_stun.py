"""A stunned hero loses the next turn action."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestPlayerStun(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def _head(self, marker, size=700):
        start = self.js.index(marker)
        return self.js[start:start + size]

    def test_consume_helper_exists(self):
        self.assertIn("_consumePlayerStun()", self.js)
        self.assertIn("You are stunned and cannot act!", self.js)

    def test_turn_actions_consume_the_stun(self):
        for marker in (
            "  stepPlayer(dx, dy) {",
            "  triggerSlotAction(slotNum) {",
            "  quickPotion() {",
            "  waitTurn() {",
            "  searchForTraps() {",
            "  useInventoryItem(idx) {",
        ):
            head = self._head(marker)
            self.assertIn("_consumePlayerStun()", head, marker)


if __name__ == "__main__":
    unittest.main()
