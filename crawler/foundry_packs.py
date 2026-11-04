"""Foundry pack loader: the consumer-side half of the versioned adapter.

Reads installed boss packs from <game>/packs/*.json and exposes them in
BOSS_TEMPLATES shape plus a (depth, seed) spawn index. This module is the
only game-side code that knows the foundry canonical format, and it only
implements slice 1 (depth-3 stairs replacement of boss_lich); anything
else is skipped with a recorded error naming the file, field and reason.

Loudness policy: full semantic validation (catalog membership, one-hit
cap, envelope) lives in foundry's validators/boss.py and gates shipping.
Here every structural problem is recorded in ERRORS (and warned to
stderr) instead of raising, so one bad pack can never brick the game --
but tests and tools can still assert the failure loudly via
pack_load_errors(). Duplicate (depth, seed) claims resolve
deterministically: sorted filename order, first pack wins.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PACKS_DIR = PROJECT_ROOT / "packs"

SUPPORTED_MAJOR = 1
TARGET_GAME = "crypt-crawler"

BOSS_ID_RE = re.compile(r"^boss_[a-z0-9_]{2,27}$")
STAT_BANDS = {
    "hp": (20, 200),
    "attack": (3, 25),
    "defense": (0, 12),
    "xp_reward": (20, 400),
    "gold_reward": (10, 300),
}

ERRORS: List[str] = []
_ENTRIES: Optional[Dict[str, Dict[str, Any]]] = None
_SPAWNS: Optional[Dict[Tuple[int, int], str]] = None


def pack_load_errors() -> List[str]:
    """Recorded pack problems, each naming file + field + reason."""
    _ensure_loaded()
    return list(ERRORS)


def foundry_bosses() -> Dict[str, Dict[str, Any]]:
    """boss_id -> BOSS_TEMPLATES-shaped entry for every clean pack."""
    _ensure_loaded()
    assert _ENTRIES is not None
    return {boss_id: dict(entry) for boss_id, entry in _ENTRIES.items()}


def spawn_for(depth: int, seed: Optional[int]) -> Optional[str]:
    """boss_id claiming (depth, seed), or None when the canon keeps it."""
    _ensure_loaded()
    assert _SPAWNS is not None
    if seed is None:
        return None
    return _SPAWNS.get((depth, seed))


def _fail(path: Path, field: str, reason: str) -> None:
    msg = f"{path.name}: {field}: {reason}"
    ERRORS.append(msg)
    print(f"foundry_packs: SKIP {msg}", file=sys.stderr)


def _check_pack(path: Path, pack: Any) -> Optional[Tuple[str, Dict[str, Any], List[Tuple[int, int]]]]:
    if not isinstance(pack, dict):
        _fail(path, "pack", "must be a JSON object")
        return None
    ver = pack.get("pack_version")
    if not isinstance(ver, str) or not re.match(r"^1\.[0-9]+$", ver):
        _fail(path, "pack_version", f"must match ^1.[0-9]+$, got {ver!r}")
        return None
    if pack.get("target_game") != TARGET_GAME:
        _fail(path, "target_game", f"must be {TARGET_GAME!r}")
        return None
    boss_id = pack.get("boss_id")
    if not isinstance(boss_id, str) or not BOSS_ID_RE.match(boss_id):
        _fail(path, "boss_id", f"must match ^boss_[a-z0-9_]{{2,27}}$, got {boss_id!r}")
        return None
    name = pack.get("name")
    if not isinstance(name, str) or not (1 <= len(name.strip()) <= 60):
        _fail(path, "name", "must be a 1-60 character string")
        return None
    stats = pack.get("stats")
    if not isinstance(stats, dict):
        _fail(path, "stats", "must be an object")
        return None
    entry: Dict[str, Any] = {"name": name}
    for key in ("hp", "attack", "defense", "xp_reward", "gold_reward"):
        value = stats.get(key) if isinstance(stats, dict) else None
        lo, hi = STAT_BANDS[key]
        if type(value) is not int or not (lo <= value <= hi):
            _fail(path, f"stats.{key}", f"must be an integer within [{lo}, {hi}]")
            return None
        entry[key] = value
    loot = pack.get("loot")
    item_id = loot.get("item_id") if isinstance(loot, dict) else None
    if not isinstance(item_id, str) or not item_id.strip():
        _fail(path, "loot.item_id", "must be a non-empty item id")
        return None
    entry["loot_drop"] = item_id
    spawn = pack.get("spawn")
    if not isinstance(spawn, dict):
        _fail(path, "spawn", "must be an object")
        return None
    if spawn.get("depth") != 3:
        _fail(path, "spawn.depth", f"slice 1 supports depth 3 only, got {spawn.get('depth')!r}")
        return None
    if spawn.get("anchor") != "stairs":
        _fail(path, "spawn.anchor", f"slice 1 supports 'stairs' only, got {spawn.get('anchor')!r}")
        return None
    if spawn.get("replaces") != "boss_lich":
        _fail(path, "spawn.replaces", f"slice 1 supports 'boss_lich' only, got {spawn.get('replaces')!r}")
        return None
    seeds = spawn.get("seeds")
    if (
        not isinstance(seeds, list)
        or not seeds
        or not all(type(s) is int and 1 <= s <= 999999 for s in seeds)
    ):
        _fail(path, "spawn.seeds", "must be a non-empty list of seeds 1..999999")
        return None
    if len(set(seeds)) != len(seeds):
        _fail(path, "spawn.seeds", "must not contain duplicate seeds")
        return None
    claims = [(3, s) for s in seeds]
    return boss_id, entry, claims


def _ensure_loaded() -> None:
    global _ENTRIES, _SPAWNS
    if _ENTRIES is not None:
        return
    _ENTRIES = {}
    _SPAWNS = {}
    if not PACKS_DIR.is_dir():
        return
    for path in sorted(PACKS_DIR.glob("*.json")):
        try:
            pack = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            _fail(path, "pack", f"unreadable: {exc}")
            continue
        checked = _check_pack(path, pack)
        if checked is None:
            continue
        boss_id, entry, claims = checked
        if boss_id in _ENTRIES:
            _fail(path, "boss_id", f"duplicate pack {boss_id!r}, first file wins")
            continue
        clash = [c for c in claims if c in _SPAWNS]
        if clash:
            _fail(path, "spawn.seeds", f"(depth, seed) already claimed: {clash}")
            continue
        _ENTRIES[boss_id] = entry
        for claim in claims:
            _SPAWNS[claim] = boss_id


def reset_cache() -> None:
    """Test hook: forget loaded packs and errors so a patched PACKS_DIR re-reads."""
    global _ENTRIES, _SPAWNS
    _ENTRIES = None
    _SPAWNS = None
    ERRORS.clear()
