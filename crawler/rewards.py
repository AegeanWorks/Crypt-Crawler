"""Variable-ratio reward engine, dopamine loot schedules, and near-miss mechanics for Crypt-Crawler.

Adapted from behavioral game design principles (Skinner box variable-ratio schedules,
Clark et al. near-miss striatal activation, and Zeigarnik effect incomplete task tension).
"""

from __future__ import annotations

import random
from typing import Any, Dict, List, Optional, Tuple


from crawler.engagement import ENGAGEMENT_TUNING


class RewardType:
    STANDARD = "STANDARD"
    CRITICAL_JACKPOT = "CRITICAL_JACKPOT"
    RARE_RELIC_DROP = "RARE_RELIC_DROP"


EXPLOIT_RELIC_DROPS = [
    "potion_rejuvenation",
    "ring_shadow",
    "potion_elixir_str",
    "potion_elixir_def",
    "shield_tower",
]


def roll_chest_reward(depth: int = 1, rng: Optional[random.Random] = None,
                      gold_mult: float = 1.0) -> Tuple[int, str, Optional[str], str]:
    """Calculate variable-ratio reward payout and drops for opening chests (Skinner box reinforcement schedule).

    Returns: (gold_awarded, reward_description, optional_item_id, reward_type)
    gold_mult carries the floor omen (Gilded 1.5, Ember Tithe 0.75); stacking
    with a jackpot is capped at 3.0x so Gilded+jackpot cannot explode.
    Numbers come from ENGAGEMENT_TUNING (single source of truth).
    """
    if rng is None:
        rng = random.Random()

    tune = ENGAGEMENT_TUNING["chest"]
    base_gold = tune["base_min"] + rng.randint(0, tune["base_range"] - 1) + (depth - 1) * tune["depth_bonus"]

    roll = rng.random()

    # Rare Relic Artifact Drop (tunable rate)
    if roll < tune["relic_rate"]:
        drop_id = rng.choice(EXPLOIT_RELIC_DROPS)
        desc = "★ ANCIENT RELIC CACHE UNLOCKED! Discovered hidden artifact!"
        return int(base_gold * min(gold_mult, tune["omen_cap_mult"])), desc, drop_id, RewardType.RARE_RELIC_DROP

    # Critical Gold Jackpot (tunable rate + mult, omen-capped)
    if roll < tune["relic_rate"] + tune["jackpot_rate"]:
        # Simpler exact rule: jackpot mult, omen-capped total of base.
        jackpot_gold = min(
            int(base_gold * tune["jackpot_mult"] * gold_mult),
            int(base_gold * tune["omen_cap_mult"]),
        )
        desc = f"★★★ CRITICAL TREASURE JACKPOT! 2.4X PAYOUT (+{jackpot_gold} Gold) ★★★"
        return jackpot_gold, desc, None, RewardType.CRITICAL_JACKPOT

    # Standard Payout
    return int(base_gold * gold_mult), f"Recovered dungeon chest coins (+{int(base_gold * gold_mult)} Gold).", None, RewardType.STANDARD


def roll_urn_reward(depth: int = 1, rng: Optional[random.Random] = None,
                   gold_mult: float = 1.0) -> Tuple[int, str, bool]:
    """Variable-ratio coin and surprise relic payout when shattering burial urns."""
    if rng is None:
        rng = random.Random()

    tune = ENGAGEMENT_TUNING["urn"]
    base_gold = tune["base_min"] + rng.randint(0, tune["base_range"] - 1) + (depth - 1) * tune["depth_bonus"]
    roll = rng.random()

    # Critical Urn Jackpot (tunable rate + mult, omen-capped)
    if roll < tune["jackpot_rate"]:
        jackpot = min(
            int(base_gold * tune["jackpot_mult"] * gold_mult),
            int(base_gold * tune["omen_cap_mult"]),
        )
        return jackpot, f"✨ CRITICAL URN JACKPOT! (+{jackpot} Gold)!", True

    return int(base_gold * gold_mult), f"Shattered burial urn (+{int(base_gold * gold_mult)} Gold).", False


def check_near_miss_survival(current_hp: int, max_hp: int, damage_taken: int) -> Optional[Dict[str, Any]]:
    """Near-miss feedback engine (Clark et al. 2009).

    Surviving a near-fatal blow (remaining HP <= 28% of max HP after taking >= 6 damage)
    triggers an adrenaline surge, converting near-death loss aversion into an intense dopamine rush.
    Numbers come from ENGAGEMENT_TUNING. Callers enforce max_per_floor
    (one real comeback per floor, then flavor-only).
    """
    if current_hp <= 0:
        return None

    tune = ENGAGEMENT_TUNING["surge"]
    hp_ratio = current_hp / max(1, max_hp)
    if hp_ratio <= tune["hp_ratio"] and damage_taken >= tune["min_damage"]:
        # Near-miss triggered
        return {
            "type": "NEAR_MISS_SURGE",
            "hp_remaining": current_hp,
            "message": "⚡ NEAR-MISS ADRENALINE SURGE! Stared death in the eyes and stood firm (+2 MP, +4 DEF barrier)!",
            "bonus_mana": tune["bonus_mana"],
            "bonus_def": tune["bonus_def"],
            "duration": tune["duration"],
        }
    return None


def generate_dungeon_bounties(depth: int = 1, seed: Optional[int] = None) -> List[Dict[str, Any]]:
    """Generate 3 active contract bounties per floor (Zeigarnik Effect).

    Incomplete objectives create persistent engagement tension that drives exploration.
    """
    actual_seed = 42 if seed is None else seed
    rng = random.Random(actual_seed + depth * 31337)
    all_bounties = [
        {
            "id": "bounty_urns",
            "title": "Catacomb Purifier",
            "desc": "Shatter 3 Burial Urns in the depths",
            "target": 3,
            "progress": 0,
            "completed": False,
            "reward_gold": 25 + depth * 10,
            "reward_xp": 20 + depth * 5,
        },
        {
            "id": "bounty_streak",
            "title": "Frenzy of Blades",
            "desc": "Achieve a x3 Kill Streak in rapid combat",
            "target": 3,
            "progress": 0,
            "completed": False,
            "reward_gold": 35 + depth * 10,
            "reward_xp": 30 + depth * 5,
        },
        {
            "id": "bounty_champions",
            "title": "Champion Slayer",
            "desc": "Defeat an Elite Champion monster",
            "target": 1,
            "progress": 0,
            "completed": False,
            "reward_gold": 45 + depth * 15,
            "reward_xp": 40 + depth * 10,
        },
        {
            "id": "bounty_chests",
            "title": "Vault Plunderer",
            "desc": "Unlock 2 Hidden Treasure Chests",
            "target": 2,
            "progress": 0,
            "completed": False,
            "reward_gold": 30 + depth * 10,
            "reward_xp": 25 + depth * 5,
        },
        {
            "id": "bounty_shrine",
            "title": "Divine Reverence",
            "desc": "Pray at an Ancient Shrine for blessing",
            "target": 1,
            "progress": 0,
            "completed": False,
            "reward_gold": 20 + depth * 5,
            "reward_xp": 20 + depth * 5,
        },
        {
            "id": "bounty_vault",
            "title": "Seal Keeper",
            "desc": "Open a sealed vault (requires 3 sigils)",
            "target": 1,
            "progress": 0,
            "completed": False,
            "reward_gold": 60 + depth * 20,
            "reward_xp": 50 + depth * 10,
        },
    ]

    selected = rng.sample(all_bounties, 3)
    return selected


def roll_distribution(
    rolls: int = 10000, seed: int = 1234
) -> Dict[str, Any]:
    """Experienced reward variance over seeded rolls (no browser needed).

    Returns observed chest relic/jackpot/standard rates and urn jackpot
    rate plus mean gold, for `tools/engagement_metrics.py` and tests.
    Lives here (not in engagement.py) to avoid an import cycle:
    rewards -> engagement (DATA only), never the reverse.
    """
    rng = random.Random(seed)
    chest_counts = {"relic": 0, "jackpot": 0, "standard": 0}
    chest_gold = 0
    for _ in range(rolls):
        _gold, _desc, _item, rtype = roll_chest_reward(depth=1, rng=rng)
        chest_gold += _gold
        if rtype == RewardType.CRITICAL_JACKPOT:
            chest_counts["jackpot"] += 1
        elif rtype == RewardType.RARE_RELIC_DROP:
            chest_counts["relic"] += 1
        else:
            chest_counts["standard"] += 1
    urn_jackpots = 0
    urn_gold = 0
    for _ in range(rolls):
        _gold, _desc, crit = roll_urn_reward(depth=1, rng=rng)
        urn_gold += _gold
        if crit:
            urn_jackpots += 1
    return {
        "rolls": rolls,
        "seed": seed,
        "chest_relic_rate": chest_counts["relic"] / rolls,
        "chest_jackpot_rate": chest_counts["jackpot"] / rolls,
        "chest_standard_rate": chest_counts["standard"] / rolls,
        "chest_mean_gold": chest_gold / rolls,
        "urn_jackpot_rate": urn_jackpots / rolls,
        "urn_mean_gold": urn_gold / rolls,
    }
