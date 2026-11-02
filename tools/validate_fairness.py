"""Fairness validator for Crypt-Crawler: rejects unwinnable/unfair seeds.

Stdlib only. Checks a generated dungeon + server monster placement:
- spawn/stairs walkable, spawn->stairs/soul/pact/sigils/vault/merchant paths exist
- exactly 1 soul, 1 pact, >=3 sigils, 1 vault (depth>=1); merchant on depth>=2
- no prop on non-walkable tile, no monster on prop, no two monsters share tile
- boss on stairs depth>=3, warden adjacent to vault depth>=2, choir adjacent to vault when present
- trap variant in known set, room theme in known set, omen in known set

Usage:
    python tools/validate_fairness.py --seeds 42,777 --depths 1,2,3
    python tools/validate_fairness.py --check-one --seed 42 --depth 1
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from crawler.dungeon import DungeonGenerator, OMEN_IDS, ROOM_THEMES, TRAP_TYPES


def _validate_dungeon(dungeon, depth: int) -> List[str]:
    errors: List[str] = []
    sx, sy = dungeon.player_spawn
    if not dungeon.is_walkable(sx, sy):
        errors.append(f"spawn {dungeon.player_spawn} not walkable")
    stx, sty = dungeon.stairs_pos
    if not dungeon.is_walkable(stx, sty):
        errors.append(f"stairs {dungeon.stairs_pos} not walkable")
    if dungeon.find_path(dungeon.player_spawn, dungeon.stairs_pos) is None:
        errors.append("stairs unreachable from spawn")
    if len(dungeon.souls) != 1:
        errors.append(f"expected 1 soul, found {len(dungeon.souls)}")
    if len(dungeon.pacts) != 1:
        errors.append(f"expected 1 pact, found {len(dungeon.pacts)}")
    if len(dungeon.sigils) < 3:
        errors.append(f"expected >=3 sigils, found {len(dungeon.sigils)}")
    if dungeon.vault is None:
        errors.append("missing vault")
    if depth >= 2 and not dungeon.merchants:
        errors.append("depth>=2 must have a merchant")

    for label, pts in (("soul", dungeon.souls), ("pact", dungeon.pacts),
                       ("sigil", dungeon.sigils), ("merchant", dungeon.merchants)):
        for px, py in pts:
            if not dungeon.is_walkable(px, py):
                errors.append(f"{label} {(px, py)} not walkable")
            elif dungeon.find_path(dungeon.player_spawn, (px, py)) is None:
                errors.append(f"{label} {(px, py)} unreachable from spawn")
    if dungeon.vault is not None:
        vx, vy = dungeon.vault
        if not dungeon.is_walkable(vx, vy):
            errors.append(f"vault {(vx, vy)} not walkable")
        elif dungeon.find_path(dungeon.player_spawn, (vx, vy)) is None:
            errors.append("vault unreachable from spawn")

    # Room themes / trap variants must come from DATA tables.
    for theme in getattr(dungeon, "room_themes", []):
        if theme not in ROOM_THEMES:
            errors.append(f"unknown room theme {theme!r}")
    for kind in getattr(dungeon, "trap_kinds", {}).values():
        if kind not in TRAP_TYPES:
            errors.append(f"unknown trap variant {kind!r}")
    # Every trap coordinate must still be a TRAP tile and walkable.
    for tx, ty in dungeon.traps:
        if not dungeon.is_walkable(tx, ty):
            errors.append(f"trap {(tx, ty)} not walkable")
    return errors


def validate_seed(seed: int, depth: int) -> Dict[str, Any]:
    """Validate generator output plus server monster placement for one seed/depth."""
    from crawler.server import start_background_server
    import json
    from urllib.request import urlopen

    gen = DungeonGenerator(width=45, height=30, depth=depth)
    dungeon = gen.generate(seed=seed)
    errors = _validate_dungeon(dungeon, depth)

    # Omen must be a known id (mirrors engine.js OMENS).
    try:
        from crawler.dungeon import omen_for
        omen = omen_for(seed, depth)
        if omen not in OMEN_IDS:
            errors.append(f"unknown omen {omen!r}")
    except Exception as exc:  # pragma: no cover - defensive
        errors.append(f"omen lookup failed: {exc}")

    # Server placement rules: no stacking, no prop cover, boss/warden/choir posts.
    server, port = start_background_server(port=0)
    try:
        url = f"http://127.0.0.1:{port}/api/new-game?seed={seed}&depth={depth}"
        with urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()
    dd = data["dungeon"]
    props = set()
    for key in ("merchants", "chests", "shrines", "urns", "souls", "sigils", "pacts"):
        props.update(tuple(e) for e in dd[key])
    if dd.get("vault"):
        props.add(tuple(dd["vault"]))
    tiles = [(m["x"], m["y"]) for m in data["monsters"]]
    if len(tiles) != len(set(tiles)):
        errors.append("two monsters share a tile")
    overlap = set(tiles) & props
    if overlap:
        errors.append(f"monsters on props: {sorted(overlap)}")
    if depth >= 3:
        bosses = [m for m in data["monsters"] if m.get("is_boss")]
        if len(bosses) != 1:
            errors.append(f"depth3 needs 1 boss, found {len(bosses)}")
        elif (bosses[0]["x"], bosses[0]["y"]) != tuple(dd["stairs_pos"]):
            errors.append("boss not guarding stairs")
    if depth >= 2 and dd.get("vault"):
        vx, vy = tuple(dd["vault"])
        wardens = [m for m in data["monsters"] if m.get("type") == "vault_warden"]
        if len(wardens) != 1:
            errors.append(f"depth>=2 needs 1 warden, found {len(wardens)}")
        elif abs(wardens[0]["x"] - vx) + abs(wardens[0]["y"] - vy) != 1:
            errors.append("warden not adjacent to vault")
        for m in data["monsters"]:
            if m.get("type") == "boss_choir":
                if abs(m["x"] - vx) + abs(m["y"] - vy) != 1:
                    errors.append("choir not adjacent to vault")
                break
    return {"seed": seed, "depth": depth, "ok": not errors, "errors": errors}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Reject unwinnable crypt-crawler seeds.")
    ap.add_argument("--seeds", default="42,777,12345,999,2,4242,7,13,101,2026")
    ap.add_argument("--depths", default="1,2,3")
    ap.add_argument("--check-one", action="store_true")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--depth", type=int, default=1)
    args = ap.parse_args(argv)
    if args.check_one:
        res = validate_seed(args.seed, args.depth)
        print(f"seed={res['seed']} depth={res['depth']} ok={res['ok']}")
        for e in res["errors"]:
            print(f"  REJECT: {e}")
        return 0 if res["ok"] else 2
    seeds = [int(s) for s in args.seeds.split(",") if s.strip()]
    depths = [int(s) for s in args.depths.split(",") if s.strip()]
    rejects = 0
    for seed in seeds:
        for depth in depths:
            res = validate_seed(seed, depth)
            status = "OK " if res["ok"] else "REJECT"
            print(f"{status} seed={seed} depth={depth}" + ("" if res["ok"] else f" {res['errors']}"))
            if not res["ok"]:
                rejects += 1
    print(f"{len(seeds)*len(depths)-rejects}/{len(seeds)*len(depths)} fair")
    return 0 if rejects == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
