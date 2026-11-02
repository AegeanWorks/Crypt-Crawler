"""Fairness validator tests: fair seeds pass, broken maps are rejected."""

import unittest

from crawler.dungeon import DungeonGenerator, OMEN_IDS, ROOM_THEMES, TRAP_TYPES, omen_for
from tools.validate_fairness import validate_seed


class TestFairness(unittest.TestCase):
    def test_known_good_seeds_are_fair(self):
        for seed in (42, 777, 12345, 999, 2, 4242):
            for depth in (1, 2, 3):
                with self.subTest(seed=seed, depth=depth):
                    res = validate_seed(seed, depth)
                    self.assertTrue(res["ok"], f"seed {seed} depth {depth}: {res['errors']}")

    def test_degenerate_maps_stay_fair(self):
        for seed in (20, 27, 54, 102, 118):
            with self.subTest(seed=seed):
                res = validate_seed(seed, 1)
                self.assertTrue(res["ok"], res["errors"])

    def test_room_themes_and_trap_variants_come_from_data(self):
        dungeon = DungeonGenerator(width=45, height=30).generate(seed=42)
        self.assertEqual(len(dungeon.room_themes), len(dungeon.rooms))
        for theme in dungeon.room_themes:
            self.assertIn(theme, ROOM_THEMES)
        for kind in dungeon.trap_kinds.values():
            self.assertIn(kind, TRAP_TYPES)
        data = dungeon.to_dict()
        self.assertIn("room_themes", data)
        self.assertIn("trap_kinds", data)
        self.assertIn("omen", data)
        self.assertIn(data["omen"], OMEN_IDS)

    def test_omen_is_deterministic_and_covers_new_moods(self):
        seen = {omen_for(seed, depth) for seed in range(1, 60) for depth in (1, 2, 3)}
        self.assertIn("ember_tithe", seen)
        self.assertIn("hollow_silence", seen)
        self.assertEqual(omen_for(42, 1), omen_for(42, 1))

    def test_rejects_unwinnable_map(self):
        from tools.validate_fairness import _validate_dungeon
        dungeon = DungeonGenerator(width=45, height=30).generate(seed=42)
        # Break it: remove the stairs reachability by walling the stairs tile.
        sx, sy = dungeon.stairs_pos
        dungeon.tiles[sy][sx] = 0  # WALL under stairs
        errors = _validate_dungeon(dungeon, 1)
        self.assertTrue(errors, "a walled stairs tile must be rejected")


if __name__ == "__main__":
    unittest.main()
