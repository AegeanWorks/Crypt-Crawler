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

    def test_trap_search_disarm_and_kinds_have_their_own_cues(self):
        self.assertIn("playSearch()", self.audio)
        self.assertIn("playDisarm()", self.audio)
        self.assertIn("playTrap(kind = \"spike\")", self.audio)
        self.assertIn("this._blip(\"triangle\", 600, 900", self.audio)
        self.assertIn("this._blip(\"square\", 350, 90", self.audio)
        self.assertIn("this._blip(\"sawtooth\", 140, 40", self.audio)
        self.assertIn("this._blip(\"triangle\", 700, 660", self.audio)
        self.assertIn("this._blip(\"square\", 220, 70", self.audio)
        self.assertEqual(self.engine.count("sounds.playSearch()"), 1)
        self.assertEqual(self.engine.count("sounds.playDisarm()"), 1)
        self.assertEqual(self.engine.count("sounds.playTrap(kind)"), 1)

    def test_floor_descent_has_a_cue(self):
        self.assertIn("playDescend()", self.audio)
        self.assertIn("this._blip(\"sawtooth\", 220, 55", self.audio)
        self.assertIn("this._blip(\"sine\", 110, 40", self.audio)
        self.assertEqual(self.engine.count("sounds.playDescend()"), 1)

    def test_run_endings_have_their_own_cues(self):
        self.assertIn("playDeath()", self.audio)
        self.assertIn("playVictory()", self.audio)
        self.assertIn("this._blip(\"sine\", 98, 98", self.audio)
        self.assertIn("this._blip(\"sine\", 73.42, 73.42", self.audio)
        for freq in ("440", "554.37", "880"):
            self.assertIn(freq, self.audio)
        self.assertEqual(self.engine.count("sounds.playDeath()"), 1)
        self.assertEqual(self.engine.count("sounds.playVictory()"), 1)

    def test_damage_over_time_has_distinct_ticks(self):
        self.assertIn("playStatusTick(kind", self.audio)
        self.assertIn("this._blip(\"sine\", 260, 150", self.audio)
        self.assertIn("this._blip(\"sawtooth\", 200, 80", self.audio)
        self.assertEqual(self.engine.count('sounds.playStatusTick("poison")'), 1)
        self.assertEqual(self.engine.count('sounds.playStatusTick("burn")'), 1)


if __name__ == "__main__":
    unittest.main()
