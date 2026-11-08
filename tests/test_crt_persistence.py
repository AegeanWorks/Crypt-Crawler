"""The CRT scanline preference is persisted across reloads."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
UI_JS = ROOT / "static" / "js" / "ui.js"


class TestCrtPersistence(unittest.TestCase):
    def setUp(self):
        self.ui = UI_JS.read_text(encoding="utf-8")

    def test_crt_preference_is_loaded_and_applied(self):
        self.assertIn('localStorage.getItem("crypt_crawler_crt")', self.ui)
        self.assertIn("this._applyCrtState();", self.ui)
        self.assertIn("_applyCrtState() {", self.ui)

    def test_toggle_writes_the_preference(self):
        self.assertIn('localStorage.setItem("crypt_crawler_crt"', self.ui)
        self.assertIn("this.crtActive ? \"1\" : \"0\"", self.ui)


if __name__ == "__main__":
    unittest.main()
