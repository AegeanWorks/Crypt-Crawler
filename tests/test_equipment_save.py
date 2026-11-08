"""Free inventory and equipment actions persist immediately."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestEquipmentSave(unittest.TestCase):
    def setUp(self):
        self.js = ENGINE_JS.read_text(encoding="utf-8")

    def _body(self, start_marker, end_marker):
        start = self.js.index(start_marker)
        end = self.js.index(end_marker, start)
        return self.js[start:end]

    def test_equip_saves(self):
        body = self._body("  useInventoryItem(idx) {", "  dropInventoryItem(idx) {")
        self.assertIn("this.saveGameState();", body)

    def test_drop_saves(self):
        body = self._body("  dropInventoryItem(idx) {", "  unequipSlot(slot) {")
        self.assertIn("this.saveGameState();", body)

    def test_unequip_saves(self):
        body = self._body("  unequipSlot(slot) {", "  _recalculatePlayerStats() {")
        self.assertIn("this.saveGameState();", body)


if __name__ == "__main__":
    unittest.main()
