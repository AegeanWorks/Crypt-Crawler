"""Canvas fit contract: the element box hugs the 760x540 bitmap and clicks use it."""

import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STYLE_CSS = ROOT / "static" / "css" / "style.css"
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


def rule_for(css: str, selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", css)
    return match.group(1) if match else ""


class TestCanvasFit(unittest.TestCase):
    def setUp(self):
        self.css = STYLE_CSS.read_text(encoding="utf-8")

    def test_canvas_keeps_bitmap_aspect_ratio(self):
        rule = rule_for(self.css, "#gameCanvas")
        self.assertIn("aspect-ratio: 760 / 540", rule)
        self.assertIn("height: auto", rule)
        # A percentage height is what produced the black letterbox bands.
        self.assertNotIn("height: 100%", rule)
        self.assertIn("max-width: min(1100px", rule)

    def test_mobile_canvas_keeps_bitmap_aspect_ratio(self):
        mobile = self.css[self.css.index("@media (max-width: 768px)"):]
        rule = rule_for(mobile, "#gameCanvas")
        self.assertIn("aspect-ratio: 760 / 540", rule)
        self.assertIn("height: auto", rule)

    def test_pointer_mapping_uses_the_drawn_content_box(self):
        js = ENGINE_JS.read_text(encoding="utf-8")
        start = js.index("_getTileAtPointer(e) {")
        body = js[start:start + 1400]
        self.assertIn("const bufferAspect", body)
        self.assertIn("drawWidth", body)
        self.assertIn("drawHeight", body)
        self.assertIn("offsetX", body)
        self.assertIn("pointerX < 0", body)


if __name__ == "__main__":
    unittest.main()
