"""Narrow canvases get a readable DOM minimap key."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"
STYLE_CSS = ROOT / "static" / "css" / "style.css"
LABELS = ("Stairs", "Chest", "Shop", "Sigil", "Vault", "Trap", "Shrine", "Pact", "Soul")


class TestMinimapLegendDom(unittest.TestCase):
    def setUp(self):
        self.js = RENDERER_JS.read_text(encoding="utf-8")
        self.css = STYLE_CSS.read_text(encoding="utf-8")

    def test_all_nine_labels_stay_in_the_single_source(self):
        for label in LABELS:
            self.assertIn(f'["{label}"', self.js)

    def test_narrow_canvas_switches_to_the_dom_key(self):
        self.assertIn("_buildMinimapLegendDom", self.js)
        self.assertIn('id = "minimapLegend"', self.js)
        self.assertIn("this._minimapLegendCompact", self.js)
        self.assertIn("if (this._minimapLegendCompact) return;", self.js)

    def test_dom_key_text_is_readable_css_pixels(self):
        self.assertIn(".minimap-legend.visible", self.css)
        self.assertIn("font: 10px/1.2", self.css)
        self.assertIn("grid-template-columns: repeat(2, max-content)", self.css)


if __name__ == "__main__":
    unittest.main()
