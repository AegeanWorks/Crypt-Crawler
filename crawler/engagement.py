"""Engagement tuning table for Crypt-Crawler (single source of truth, Python side).

All engagement numbers live here as DATA, never as hardcoded one-offs.
The live browser engine mirrors these values in `static/js/engine.js`
(see ODDS_PARITY_NOTE below); `tests/test_odds_parity.py` fails when
they drift apart.

Literature anchors (see CyberPulse ADR-002):
- Skinner variable-magnitude (every chest pays, magnitude varies).
- Clark almost-won (one capped comeback, then flavor-only).
- Kahneman/Tversky loss aversion (delve gold at risk vs banked gold).
- Ryan/Rigby/Przybylski SDT + Csikszentmihalyi flow (readable mastery).

Ethics line: tension yes, manipulation no. No empty chests, no
low-HP farming loop, no timers, no real-money pressure.
"""

from __future__ import annotations

from typing import Any, Dict


ENGAGEMENT_TUNING: Dict[str, Any] = {
    # Chest variable-magnitude schedule (stated odds, also in README).
    "chest": {
        "relic_rate": 0.14,
        "jackpot_rate": 0.20,  # roll in [0.14, 0.34)
        "jackpot_mult": 2.4,
        "omen_cap_mult": 3.0,
        "base_min": 17,
        "base_range": 14,  # randint(0, 13) -> 17..30 before depth bonus
        "depth_bonus": 10,
    },
    # Urn schedule.
    "urn": {
        "jackpot_rate": 0.18,
        "jackpot_mult": 2.4,
        "omen_cap_mult": 3.0,
        "base_min": 6,
        "base_range": 11,  # randint(0, 10) -> 6..16 before depth bonus
        "depth_bonus": 4,
    },
    # Survival surge (almost-died arousal, NOT Clark almost-won).
    # Capped: one real comeback per floor, then flavor-only (enforced
    # by the caller via `surge_used` / JS floor flag in Commit B).
    "surge": {
        "hp_ratio": 0.28,
        "min_damage": 6,
        "bonus_mana": 2,
        "bonus_def": 4,
        "duration": 3,
        "max_per_floor": 1,
    },
    # Almost-won near-miss (Clark, Commit B): one bonus then flavor.
    "near_miss": {
        "max_per_floor": 1,
    },
    # Kill-streak frenzy (flow channel, no ratchet).
    "streak": {
        "decay_turns": 4,
        "double_at": 2,
        "double_xp": 10,
        "triple_at": 3,
        "triple_mana": 1,
        "rampage_at": 5,
        "rampage_xp": 25,
        "rampage_gold": 5,
    },
    # Status combo payoff (fantasy-native sequencing).
    "combo": {
        "base": 12,
        "per_depth": 3,
    },
    # Black pact altar (push-your-luck, one shot per floor).
    "pact": {
        "wrath_attack": 4,
        "wrath_hp_fraction": 0.20,
        "wrath_hp_min": 5,
        "grave_max_hp": 18,
        "grave_mana_seal_max": 3,
        "avarice_base": 120,
        "avarice_per_depth": 30,
        "avarice_wraiths": 2,
    },
    # Lost soul (3-way choice, toll lottery is stated in README).
    "soul": {
        "ember_heal_fraction": 0.30,
        "ember_heal_min": 10,
        "toll_gold_base": 45,
        "toll_gold_per_depth": 15,
        "toll_relic_rate": 0.50,
        "lore_xp": 15,
    },
    # Bounty board (Zeigarnik, 3 sampled of 6, no deadlines in v1).
    "bounties": {
        "count": 3,
        "seed_stride": 31337,
    },
    # Mimic (deterministic 1-in-4 floors with chests).
    "mimic": {
        "floor_rate_denominator": 4,
    },
    # Champion (server spawn).
    "champion": {
        "rate": 0.16,
    },
}

ODDS_PARITY_NOTE = (
    "Python `roll_chest_reward` / `roll_urn_reward` are the audited "
    "reference; the shipped browser engine (`static/js/engine.js` chest "
    "/ urn branches) must use the same rates, multipliers and caps. "
    "`tests/test_odds_parity.py` reads both files and fails on drift. "
    "Known gap fixed in Commit B: JS chest base uses 0-19 vs py 0-13; "
    "JS must move to the table above."
)


def depth_seed(run_seed: int, depth: int) -> int:
    """Deterministic per-floor seed chaining a run across descents.

    Same 32-bit mix as `dungeon.omen_for` so Python and JS agree.
    Replaces `Date.now() % 1M` reseeds that broke replayability.
    """
    h = (int(run_seed) & 0xFFFFFFFF) ^ ((int(depth) or 1) * 0x9E3779B1 & 0xFFFFFFFF)
    h &= 0xFFFFFFFF
    h = (h ^ (h >> 15)) * 0x85EBCA6B & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 0xC2B2AE35 & 0xFFFFFFFF
    h = (h ^ (h >> 16)) & 0xFFFFFFFF
    return h
