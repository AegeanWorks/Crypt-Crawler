"""Chronicle fade contract: a scrolled log fades its top edge instead of shearing glyphs."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLE_CSS = ROOT / "static" / "css" / "style.css"
INDEX_HTML = ROOT / "static" / "index.html"
UI_JS = ROOT / "static" / "js" / "ui.js"


class TestChronicleFade(unittest.TestCase):
    def test_markup_wraps_the_scroll_box_for_an_overlay(self):
        html = INDEX_HTML.read_text(encoding="utf-8")
        self.assertIn('class="chronicle-wrap"', html)
        self.assertIn('id="chronicleLog"', html)

    def test_css_fades_only_while_scrolled(self):
        css = STYLE_CSS.read_text(encoding="utf-8")
        self.assertIn(".chronicle-wrap:has(.chronicle-log.is-scrolled)::after", css)
        self.assertIn("linear-gradient(to bottom, #090c10", css)

    def test_ui_toggles_the_scrolled_state(self):
        js = UI_JS.read_text(encoding="utf-8")
        self.assertIn("_updateChronicleFade()", js)
        self.assertIn('classList.toggle("is-scrolled"', js)
        self.assertIn('addEventListener("scroll"', js)


if __name__ == "__main__":
    unittest.main()
