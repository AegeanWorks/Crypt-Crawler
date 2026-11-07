"""Audio cue contract: ranged and telegraphed attacks keep an entrance cue."""

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
AUDIO_JS = ROOT / "static" / "js" / "audio.js"
ENGINE_JS = ROOT / "static" / "js" / "engine.js"


class TestAudioCues(unittest.TestCase):
    def setUp(self):
        self.audio = AUDIO_JS.read_text(encoding="utf-8")
        self.engine = ENGINE_JS.read_text(encoding="utf-8")

    def test_cue_synths_exist_with_distinct_frequencies(self):
        self.assertIn("playBow()", self.audio)
        self.assertIn("setValueAtTime(880", self.audio)
        self.assertIn("playTelegraph(kind", self.audio)
        self.assertIn('kind === "drain" ? 110 : 196', self.audio)

    def test_enemy_telegraphs_and_bow_release_call_the_cues(self):
        self.assertEqual(self.engine.count('sounds.playTelegraph("hymn")'), 2)
        self.assertEqual(self.engine.count('sounds.playTelegraph("drain")'), 1)
        self.assertEqual(self.engine.count("sounds.playBow()"), 1)


if __name__ == "__main__":
    unittest.main()
