"""Engagement tuning tests: DATA bounds, determinism, sampler contract."""

import unittest

from crawler.dungeon import omen_for
from crawler.engagement import ENGAGEMENT_TUNING, depth_seed
from crawler.rewards import generate_dungeon_bounties, roll_distribution


class TestEngagementTuning(unittest.TestCase):
    def test_tuning_bounds_are_sane(self):
        t = ENGAGEMENT_TUNING
        self.assertGreater(t["chest"]["relic_rate"], 0)
        self.assertGreater(t["chest"]["jackpot_rate"], 0)
        self.assertLess(t["chest"]["relic_rate"] + t["chest"]["jackpot_rate"], 1.0)
        self.assertEqual(t["chest"]["jackpot_mult"], 2.4)
        self.assertEqual(t["chest"]["omen_cap_mult"], 3.0)
        self.assertEqual(t["urn"]["jackpot_rate"], 0.18)
        self.assertEqual(t["surge"]["max_per_floor"], 1)
        self.assertEqual(t["near_miss"]["max_per_floor"], 1)
        self.assertEqual(t["bounties"]["count"], 3)

    def test_depth_seed_is_deterministic(self):
        self.assertEqual(depth_seed(42, 1), depth_seed(42, 1))
        self.assertNotEqual(depth_seed(42, 1), depth_seed(42, 2))
        self.assertNotEqual(depth_seed(42, 1), depth_seed(43, 1))
        # Same mix as omen_for: agrees on floor mood source.
        self.assertEqual(omen_for(42, 2), omen_for(42, 2))

    def test_bounty_sampler_returns_three_of_six(self):
        seen = set()
        for seed in range(20):
            b = generate_dungeon_bounties(depth=2, seed=seed)
            self.assertEqual(len(b), 3)
            self.assertEqual(len({x["id"] for x in b}), 3)
            seen.update(x["id"] for x in b)
        self.assertTrue(len(seen) >= 4)

    def test_roll_distribution_matches_stated_odds(self):
        dist = roll_distribution(rolls=10000, seed=1234)
        self.assertAlmostEqual(dist["chest_relic_rate"], 0.14, delta=0.03)
        self.assertAlmostEqual(dist["chest_jackpot_rate"], 0.20, delta=0.03)
        self.assertAlmostEqual(dist["urn_jackpot_rate"], 0.18, delta=0.03)


if __name__ == "__main__":
    unittest.main()
