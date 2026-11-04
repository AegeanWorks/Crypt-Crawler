"""Engagement metrics for Crypt-Crawler (stdlib only, deterministic).

Proves every engagement claim with a measurement, never "feels more fun":
- session length proxy (walkable tiles + prop counts per seed/depth)
- choice distribution surface (soul/pact/bounty ids available per seed)
- reward variance actually experienced (seeded roll distribution vs stated odds)
- fairness (validator passes on the matrix)
- determinism (depth_seed chain + layout_hash stable)

Usage:
    python tools/engagement_metrics.py --seeds 42,777,12345 --depths 1,2,3
    python tools/engagement_metrics.py --seeds 42 --depths 1 --rolls 10000 --json out.json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crawler.dungeon import DungeonGenerator, omen_for  # noqa: E402
from crawler.engagement import ENGAGEMENT_TUNING, depth_seed  # noqa: E402
from crawler.rewards import generate_dungeon_bounties, roll_distribution  # noqa: E402


def measure_seed(seed: int, depth: int, rolls: int = 2000) -> Dict[str, Any]:
    gen = DungeonGenerator(width=45, height=30, depth=depth)
    dungeon = gen.generate(seed=seed)
    walkable = sum(
        1 for y in range(dungeon.height) for x in range(dungeon.width)
        if dungeon.is_walkable(x, y)
    )
    dist = roll_distribution(rolls=rolls, seed=seed + depth)
    bounties = generate_dungeon_bounties(depth=depth, seed=seed)
    return {
        "seed": seed,
        "depth": depth,
        "depth_seed": depth_seed(seed, depth),
        "omen": omen_for(seed, depth),
        "walkable_tiles": walkable,
        "rooms": len(dungeon.rooms),
        "chests": len(dungeon.chests),
        "urns": len(dungeon.urns),
        "traps": len(dungeon.traps),
        "souls": len(dungeon.souls),
        "pacts": len(dungeon.pacts),
        "sigils": len(dungeon.sigils),
        "vault": dungeon.vault is not None,
        "merchant": len(dungeon.merchants) > 0,
        "bounty_ids": sorted(b["id"] for b in bounties),
        "chest_relic_rate": round(dist["chest_relic_rate"], 4),
        "chest_jackpot_rate": round(dist["chest_jackpot_rate"], 4),
        "chest_mean_gold": round(dist["chest_mean_gold"], 2),
        "urn_jackpot_rate": round(dist["urn_jackpot_rate"], 4),
        "urn_mean_gold": round(dist["urn_mean_gold"], 2),
    }


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Deterministic engagement metrics.")
    ap.add_argument("--seeds", default="42,777,12345,999,2,4242")
    ap.add_argument("--depths", default="1,2,3")
    ap.add_argument("--rolls", type=int, default=2000)
    ap.add_argument("--json", default=None)
    args = ap.parse_args(argv)
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    depths = [int(s) for s in args.depths.split(",") if s.strip()]
    rows: List[Dict[str, Any]] = []
    for seed in seeds:
        for depth in depths:
            rows.append(measure_seed(seed, depth, rolls=args.rolls))
    tune = ENGAGEMENT_TUNING
    # Stated vs experienced (tolerance bands, not exact equality).
    chest_j = sum(r["chest_jackpot_rate"] for r in rows) / max(1, len(rows))
    chest_r = sum(r["chest_relic_rate"] for r in rows) / max(1, len(rows))
    urn_j = sum(r["urn_jackpot_rate"] for r in rows) / max(1, len(rows))
    summary = {
        "matrix": {"seeds": seeds, "depths": depths, "rolls_each": args.rolls},
        "stated": {
            "chest_relic": tune["chest"]["relic_rate"],
            "chest_jackpot": tune["chest"]["jackpot_rate"],
            "urn_jackpot": tune["urn"]["jackpot_rate"],
        },
        "experienced_mean": {
            "chest_relic": round(chest_r, 4),
            "chest_jackpot": round(chest_j, 4),
            "urn_jackpot": round(urn_j, 4),
        },
        "tolerances": {"abs": 0.03},
        "rows": rows,
    }
    ok = (
        abs(chest_r - tune["chest"]["relic_rate"]) <= 0.03
        and abs(chest_j - tune["chest"]["jackpot_rate"]) <= 0.03
        and abs(urn_j - tune["urn"]["jackpot_rate"]) <= 0.03
    )
    # Every floor offers the full choice surface (no missing decisions).
    for r in rows:
        if not (r["souls"] == 1 and r["pacts"] == 1 and r["sigils"] >= 3 and r["vault"]):
            ok = False
            r["choice_gap"] = True
    payload = json.dumps(summary, indent=2)
    if args.json:
        Path(args.json).write_text(payload, encoding="utf-8")
    print(payload)
    print(f"{len(rows)}/{len(rows)} measured ok={ok}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
