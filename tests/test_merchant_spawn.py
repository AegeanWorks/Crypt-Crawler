"""Every depth >= 2 floor must offer the Hermit Merchant."""

import unittest

from crawler.dungeon import DungeonGenerator, TileType


class TestMerchantSpawn(unittest.TestCase):
    def test_regression_seeds_have_a_merchant_on_depth_two_and_three(self):
        for seed in (1, 3, 15):
            for depth in (2, 3):
                with self.subTest(seed=seed, depth=depth):
                    dungeon = DungeonGenerator(width=45, height=30, depth=depth).generate(seed=seed)
                    self.assertEqual(len(dungeon.merchants), 1)
                    mx, my = dungeon.merchants[0]
                    self.assertEqual(dungeon.tiles[my][mx], TileType.MERCHANT)
                    self.assertTrue(dungeon.is_walkable(mx, my))
                    self.assertNotEqual((mx, my), dungeon.player_spawn)
                    self.assertNotEqual((mx, my), dungeon.stairs_pos)
                    props = (
                        set(dungeon.chests)
                        | set(dungeon.shrines)
                        | set(dungeon.urns)
                        | set(dungeon.souls)
                        | set(dungeon.sigils)
                        | set(dungeon.pacts)
                    )
                    self.assertNotIn((mx, my), props)
                    if dungeon.vault:
                        self.assertNotEqual((mx, my), dungeon.vault)
                    self.assertIsNotNone(dungeon.find_path(dungeon.player_spawn, (mx, my)))


if __name__ == "__main__":
    unittest.main()
