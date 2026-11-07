"""Room theme emblem contract: every generated theme has a rendered glyph."""

import unittest
from pathlib import Path

from crawler.dungeon import ROOM_THEMES

ROOT = Path(__file__).resolve().parent.parent
RENDERER_JS = ROOT / "static" / "js" / "renderer.js"


class TestRoomThemes(unittest.TestCase):
    def setUp(self):
        self.js = RENDERER_JS.read_text(encoding="utf-8")

    def test_renderer_reads_generated_themes(self):
        self.assertIn("dungeon.room_themes", self.js)
        self.assertIn("_drawRoomThemes(ctx, dungeon, ts)", self.js)
        self.assertIn("_drawThemeGlyph(ctx, themes[i]", self.js)

    def test_every_generated_theme_has_a_glyph_and_colour(self):
        for theme in ROOM_THEMES:
            self.assertIn(f'      {theme}: "#', self.js, f"missing palette colour for {theme}")
            self.assertIn(f'theme === "{theme}"', self.js, f"missing glyph branch for {theme}")

    def test_save_persists_room_themes(self):
        engine = (ROOT / "static" / "js" / "engine.js").read_text(encoding="utf-8")
        self.assertIn("room_themes: this.dungeon.room_themes", engine)


if __name__ == "__main__":
    unittest.main()
