"""Procedural dungeon generation and grid management for Crypt-Crawler."""

from __future__ import annotations

import collections
import math
import random
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Tuple


class TileType:
    WALL = 0
    FLOOR = 1
    DOOR_CLOSED = 2
    DOOR_OPEN = 3
    STAIRS_DOWN = 4
    CHEST = 5
    TRAP = 6
    SHRINE = 7
    URN = 8
    MERCHANT = 9
    SOUL = 10
    SIGIL = 11
    VAULT = 12
    PACT = 13


# Procedural depth tables: the generator reads these, never hardcoded one-offs.
# Room themes only change prop density/placement, never connectivity.
ROOM_THEMES: Tuple[str, ...] = ("ossuary", "choke", "gallery", "urn_crypt", "chapel")

# Trap variants share one Search/disarm loop; damage lives here as DATA.
TRAP_TYPES: Dict[str, Dict[str, Any]] = {
    "spike": {"name": "Spike Trap", "damage": (8, 13), "desc": "8-13 damage when stepped on."},
    "dart": {"name": "Dart Trap", "damage": (4, 6), "desc": "4-6 damage twice (volley)."},
    "snare": {"name": "Snare Trap", "damage": (0, 2), "desc": "0-2 damage and stuns 1 turn."},
}

# Omen ids mirror static/js/engine.js OMENS (order-independent lookup).
OMEN_IDS: Tuple[str, ...] = (
    "blood_moon", "deep_fog", "gilded_crypt", "restless_dead",
    "ember_tithe", "hollow_silence",
)

OMEN_TABLE: Dict[str, Dict[str, Any]] = {
    "blood_moon": {"atkMult": 1.25, "fov": 7, "goldMult": 1.0, "extraFoe": 0},
    "deep_fog": {"atkMult": 1.0, "fov": 5, "goldMult": 1.0, "extraFoe": 0},
    "gilded_crypt": {"atkMult": 1.0, "fov": 7, "goldMult": 1.5, "extraFoe": 0},
    "restless_dead": {"atkMult": 1.0, "fov": 7, "goldMult": 1.0, "extraFoe": 1},
    "ember_tithe": {"atkMult": 1.0, "fov": 7, "goldMult": 0.75, "extraFoe": 0,
                    "shrineHealMult": 1.5},
    "hollow_silence": {"atkMult": 1.0, "fov": 7, "goldMult": 1.0, "extraFoe": 0,
                       "trapBonus": 1, "disarmXpMult": 2.0},
}


def omen_for(seed: int, depth: int) -> str:
    """Python mirror of engine.js omenFor, extended to six omens.

    Same 32-bit mix as the client so both engines agree on the floor mood.
    """
    h = (int(seed) & 0xFFFFFFFF) ^ ((int(depth) or 1) * 0x9E3779B1 & 0xFFFFFFFF)
    h &= 0xFFFFFFFF
    h = (h ^ (h >> 15)) * 0x85EBCA6B & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 0xC2B2AE35 & 0xFFFFFFFF
    h = (h ^ (h >> 16)) & 0xFFFFFFFF
    ids = ["blood_moon", "deep_fog", "gilded_crypt", "restless_dead",
           "ember_tithe", "hollow_silence"]
    return ids[h % len(ids)]


@dataclass
class Room:
    x: int
    y: int
    w: int
    h: int

    @property
    def x1(self) -> int:
        return self.x

    @property
    def y1(self) -> int:
        return self.y

    @property
    def x2(self) -> int:
        return self.x + self.w

    @property
    def y2(self) -> int:
        return self.y + self.h

    @property
    def center(self) -> Tuple[int, int]:
        return (self.x + self.w // 2, self.y + self.h // 2)

    def intersects(self, other: "Room", padding: int = 1) -> bool:
        return (
            self.x1 - padding < other.x2
            and self.x2 + padding > other.x1
            and self.y1 - padding < other.y2
            and self.y2 + padding > other.y1
        )


class Dungeon:
    def __init__(self, width: int, height: int, seed: Optional[int] = None):
        self.width = width
        self.height = height
        self.seed = seed if seed is not None else random.randint(1, 999999)
        self.rng = random.Random(self.seed)
        self.tiles: List[List[int]] = [[TileType.WALL for _ in range(width)] for _ in range(height)]
        self.rooms: List[Room] = []
        self.player_spawn: Tuple[int, int] = (0, 0)
        self.stairs_pos: Tuple[int, int] = (0, 0)
        self.chests: List[Tuple[int, int]] = []
        self.traps: List[Tuple[int, int]] = []
        self.shrines: List[Tuple[int, int]] = []
        self.urns: List[Tuple[int, int]] = []
        self.souls: List[Tuple[int, int]] = []
        self.sigils: List[Tuple[int, int]] = []
        self.vault: Optional[Tuple[int, int]] = None
        self.pacts: List[Tuple[int, int]] = []
        self.sconces: List[Tuple[int, int]] = []
        self.merchants: List[Tuple[int, int]] = []
        self.depth: int = 1
        # DATA-driven dressing: parallel to rooms/traps, same rng stream.
        self.room_themes: List[str] = []
        self.trap_kinds: Dict[Tuple[int, int], str] = {}

    @property
    def biome(self) -> str:
        if self.depth <= 1:
            return "crypt"
        elif self.depth == 2:
            return "cavern"
        return "inferno"

    def in_bounds(self, x: int, y: int) -> bool:
        return 0 <= x < self.width and 0 <= y < self.height

    def is_walkable(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        tile = self.tiles[y][x]
        return tile in (
            TileType.FLOOR,
            TileType.DOOR_OPEN,
            TileType.DOOR_CLOSED,
            TileType.STAIRS_DOWN,
            TileType.CHEST,
            TileType.TRAP,
            TileType.SHRINE,
            TileType.URN,
            TileType.MERCHANT,
            TileType.SOUL,
            TileType.SIGIL,
            TileType.VAULT,
            TileType.PACT,
        )

    def is_transparent(self, x: int, y: int) -> bool:
        if not self.in_bounds(x, y):
            return False
        tile = self.tiles[y][x]
        return tile in (
            TileType.FLOOR,
            TileType.DOOR_OPEN,
            TileType.STAIRS_DOWN,
            TileType.CHEST,
            TileType.TRAP,
            TileType.SHRINE,
            TileType.URN,
            TileType.MERCHANT,
            TileType.SOUL,
            TileType.SIGIL,
            TileType.VAULT,
            TileType.PACT,
        )

    def compute_fov(self, px: int, py: int, radius: int = 8) -> Set[Tuple[int, int]]:
        """Calculate field of view using symmetric raycasting with distance attenuation."""
        visible: Set[Tuple[int, int]] = set()
        if not self.in_bounds(px, py):
            return visible

        visible.add((px, py))
        num_rays = max(64, radius * 16)
        for i in range(num_rays):
            angle = (2.0 * math.pi * i) / num_rays
            dx = math.cos(angle)
            dy = math.sin(angle)

            cx = float(px) + 0.5
            cy = float(py) + 0.5

            for r in range(1, radius + 1):
                cx += dx
                cy += dy
                tx = int(math.floor(cx))
                ty = int(math.floor(cy))

                if not self.in_bounds(tx, ty):
                    break

                dist_sq = (tx - px) ** 2 + (ty - py) ** 2
                if dist_sq <= radius * radius:
                    visible.add((tx, ty))

                if not self.is_transparent(tx, ty):
                    break

        return visible

    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> Optional[List[Tuple[int, int]]]:
        """Breadth-first search shortest path on the walkable grid."""
        if not self.is_walkable(start[0], start[1]):
            return None
        if not self.is_walkable(goal[0], goal[1]):
            return None
        if start == goal:
            return [start]

        queue = collections.deque([start])
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}

        neighbors = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        while queue:
            current = queue.popleft()
            if current == goal:
                break

            for dx, dy in neighbors:
                nx, ny = current[0] + dx, current[1] + dy
                neighbor = (nx, ny)
                if self.is_walkable(nx, ny) and neighbor not in came_from:
                    came_from[neighbor] = current
                    queue.append(neighbor)

        if goal not in came_from:
            return None

        path = []
        curr: Optional[Tuple[int, int]] = goal
        while curr is not None:
            path.append(curr)
            curr = came_from[curr]
        path.reverse()
        return path

    def to_dict(self) -> Dict[str, Any]:
        """Serialize dungeon layout to JSON-friendly dictionary."""
        return {
            "width": self.width,
            "height": self.height,
            "seed": self.seed,
            "depth": self.depth,
            "biome": self.biome,
            "omen": omen_for(self.seed, self.depth),
            "player_spawn": list(self.player_spawn),
            "stairs_pos": list(self.stairs_pos),
            "chests": [list(c) for c in self.chests],
            "traps": [list(t) for t in self.traps],
            "trap_kinds": {f"{x},{y}": k for (x, y), k in self.trap_kinds.items()},
            "shrines": [list(s) for s in self.shrines],
            "urns": [list(u) for u in self.urns],
            "souls": [list(s) for s in self.souls],
            "sigils": [list(s) for s in self.sigils],
            "vault": list(self.vault) if self.vault else None,
            "pacts": [list(p) for p in self.pacts],
            "sconces": [list(sc) for sc in self.sconces],
            "merchants": [list(m) for m in self.merchants],
            "rooms": [
                {"x": r.x, "y": r.y, "w": r.w, "h": r.h, "center": list(r.center)}
                for r in self.rooms
            ],
            "room_themes": list(self.room_themes),
            "tiles": [row[:] for row in self.tiles],
        }


class DungeonGenerator:
    def __init__(
        self,
        width: int = 50,
        height: int = 35,
        min_room_size: int = 4,
        max_room_size: int = 9,
        max_rooms: int = 15,
        depth: int = 1,
    ):
        self.width = width
        self.height = height
        self.min_room_size = min_room_size
        self.max_room_size = max_room_size
        self.max_rooms = max_rooms
        self.depth = depth

    def generate(self, seed: Optional[int] = None) -> Dungeon:
        min_side = self.max_room_size + 4
        if self.width < min_side or self.height < min_side:
            raise ValueError(
                "Why: dungeon "
                f"{self.width}x{self.height} is too small for max_room_size "
                f"{self.max_room_size} (need at least {min_side} per side). "
                "Fix: use a larger width/height or a smaller max_room_size."
            )
        dungeon = Dungeon(self.width, self.height, seed=seed)
        dungeon.depth = self.depth
        rng = dungeon.rng

        # Generate non-overlapping rooms
        attempts = 0
        while len(dungeon.rooms) < self.max_rooms and attempts < 150:
            attempts += 1
            w = rng.randint(self.min_room_size, self.max_room_size)
            h = rng.randint(self.min_room_size, self.max_room_size)
            x = rng.randint(1, self.width - w - 2)
            y = rng.randint(1, self.height - h - 2)

            new_room = Room(x, y, w, h)
            if any(new_room.intersects(other) for other in dungeon.rooms):
                continue

            # Carve room floors
            for rx in range(new_room.x1, new_room.x2):
                for ry in range(new_room.y1, new_room.y2):
                    dungeon.tiles[ry][rx] = TileType.FLOOR

            if dungeon.rooms:
                # Connect to previous room center with L-tunnel
                prev_center = dungeon.rooms[-1].center
                new_center = new_room.center
                self._carve_corridor(dungeon, prev_center, new_center, rng)

            dungeon.rooms.append(new_room)
            # DATA theme per room, same rng stream so replay holds.
            dungeon.room_themes.append(rng.choice(list(ROOM_THEMES)))

        # Player spawn in first room center
        if dungeon.rooms:
            dungeon.player_spawn = dungeon.rooms[0].center

            # Find room farthest from room 0 for stairs
            p_center = dungeon.rooms[0].center
            farthest_room = max(
                dungeon.rooms[1:],
                key=lambda r: abs(r.center[0] - p_center[0]) + abs(r.center[1] - p_center[1]),
                default=dungeon.rooms[0],
            )
            dungeon.stairs_pos = farthest_room.center
            dungeon.tiles[dungeon.stairs_pos[1]][dungeon.stairs_pos[0]] = TileType.STAIRS_DOWN

            # Wandering Hermit Merchant on depths >= 2. The first spare room
            # can be the stairs room; keep looking for another room instead of
            # dropping the merchant entirely (seeds 1/3/15 at depth 2-3).
            if self.depth >= 2 and len(dungeon.rooms) >= 2:
                for shop_room in dungeon.rooms[1:]:
                    if shop_room == farthest_room:
                        continue
                    mx = shop_room.center[0]
                    my = shop_room.center[1]
                    if dungeon.tiles[my][mx] != TileType.FLOOR or (mx, my) in (
                        dungeon.player_spawn,
                        dungeon.stairs_pos,
                    ):
                        continue
                    dungeon.tiles[my][mx] = TileType.MERCHANT
                    dungeon.merchants.append((mx, my))
                    break

                if not dungeon.merchants:
                    # Two-room maps can leave no spare room center; fall back
                    # to any free floor tile, never spawn or stairs.
                    reserved = {dungeon.player_spawn, dungeon.stairs_pos}
                    for shop_room in dungeon.rooms:
                        for my in range(shop_room.y1 + 1, shop_room.y2 - 1):
                            for mx in range(shop_room.x1 + 1, shop_room.x2 - 1):
                                if (dungeon.tiles[my][mx] == TileType.FLOOR
                                        and (mx, my) not in reserved):
                                    dungeon.tiles[my][mx] = TileType.MERCHANT
                                    dungeon.merchants.append((mx, my))
                                    break
                            if dungeon.merchants:
                                break
                        if dungeon.merchants:
                            break

            # Scatter chests, traps, shrines, and urns
            for i, room in enumerate(dungeon.rooms[1:], 1):
                if room == farthest_room:
                    continue

                # Ancient Shrine in one room
                if i == len(dungeon.rooms) // 2:
                    sx = room.center[0]
                    sy = room.center[1]
                    if (sx, sy) not in dungeon.merchants:
                        dungeon.tiles[sy][sx] = TileType.SHRINE
                        dungeon.shrines.append((sx, sy))
                        continue

                # Chests
                if rng.random() < 0.6:
                    cx = rng.randint(room.x1 + 1, room.x2 - 2)
                    cy = rng.randint(room.y1 + 1, room.y2 - 2)
                    if (
                        dungeon.tiles[cy][cx] == TileType.FLOOR
                        and (cx, cy) not in (dungeon.player_spawn, dungeon.stairs_pos)
                        and (cx, cy) not in dungeon.merchants
                    ):
                        dungeon.tiles[cy][cx] = TileType.CHEST
                        dungeon.chests.append((cx, cy))

                # Traps (variant lives in DATA; one Search/disarm loop covers all)
                trap_chance = 0.4
                try:
                    theme_idx = dungeon.rooms.index(room)
                    theme = dungeon.room_themes[theme_idx] if theme_idx < len(dungeon.room_themes) else ""
                except ValueError:
                    theme = ""
                if theme == "choke":
                    trap_chance = 0.55
                elif theme == "gallery":
                    trap_chance = 0.25
                if omen_for(dungeon.seed, dungeon.depth) == "hollow_silence":
                    trap_chance = min(0.75, trap_chance + 0.15)
                if rng.random() < trap_chance:
                    tx = rng.randint(room.x1 + 1, room.x2 - 2)
                    ty = rng.randint(room.y1 + 1, room.y2 - 2)
                    if (
                        dungeon.tiles[ty][tx] == TileType.FLOOR
                        and (tx, ty) not in (dungeon.player_spawn, dungeon.stairs_pos)
                        and (tx, ty) not in dungeon.merchants
                    ):
                        dungeon.tiles[ty][tx] = TileType.TRAP
                        dungeon.traps.append((tx, ty))
                        dungeon.trap_kinds[(tx, ty)] = rng.choice(list(TRAP_TYPES.keys()))

                # Urns
                if rng.random() < 0.7:
                    ux = rng.randint(room.x1 + 1, room.x2 - 2)
                    uy = rng.randint(room.y1 + 1, room.y2 - 2)
                    if (
                        dungeon.tiles[uy][ux] == TileType.FLOOR
                        and (ux, uy) not in (dungeon.player_spawn, dungeon.stairs_pos)
                        and (ux, uy) not in dungeon.merchants
                    ):
                        dungeon.tiles[uy][ux] = TileType.URN
                        dungeon.urns.append((ux, uy))

            # One Lost Soul per floor: an optional choice, never on a shrine
            for room in dungeon.rooms[1:]:
                if room == farthest_room:
                    continue
                if any(room.center == m for m in dungeon.merchants):
                    continue
                sx, sy = room.center
                if dungeon.tiles[sy][sx] == TileType.FLOOR:
                    dungeon.tiles[sy][sx] = TileType.SOUL
                    dungeon.souls.append((sx, sy))
                    break

            if not dungeon.souls:
                # Degenerate maps can leave every room center occupied; keep the
                # one-soul-per-floor contract by falling back to any free tile.
                for room in dungeon.rooms:
                    if any(room.center == m for m in dungeon.merchants):
                        continue
                    placed_soul = False
                    for sy in range(room.y1 + 1, room.y2 - 1):
                        for sx in range(room.x1 + 1, room.x2 - 1):
                            if (sx, sy) in (dungeon.player_spawn, dungeon.stairs_pos):
                                continue
                            if dungeon.tiles[sy][sx] == TileType.FLOOR:
                                dungeon.tiles[sy][sx] = TileType.SOUL
                                dungeon.souls.append((sx, sy))
                                placed_soul = True
                                break
                        if placed_soul:
                            break
                    if placed_soul:
                        break

            # One black pact altar: a risk-for-power bargain on every floor.
            # Placed before sigils so the objective never consumes its tile.
            for room in dungeon.rooms[1:]:
                if room == farthest_room:
                    continue
                if any(room.center == m for m in dungeon.merchants):
                    continue
                altar: Optional[Tuple[int, int]] = None
                for ay in range(room.y1 + 1, room.y2 - 1):
                    for ax in range(room.x1 + 1, room.x2 - 1):
                        if dungeon.tiles[ay][ax] == TileType.FLOOR:
                            altar = (ax, ay)
                            break
                    if altar:
                        break
                if altar:
                    px, py = altar
                    dungeon.tiles[py][px] = TileType.PACT
                    dungeon.pacts.append(altar)
                    break

            # A tiny map can have no ordinary room to spare (finding: seeds 20/27/54
            # at 20x20). Fall back to any free floor, then to the stairs room itself,
            # never on the stairs tile, spawn or a merchant.
            if not dungeon.pacts:
                reserved = {dungeon.player_spawn, dungeon.stairs_pos} | set(dungeon.merchants)
                fallback = next(
                    (
                        (x, y)
                        for room in dungeon.rooms
                        for y in range(room.y1 + 1, room.y2 - 1)
                        for x in range(room.x1 + 1, room.x2 - 1)
                        if dungeon.tiles[y][x] == TileType.FLOOR and (x, y) not in reserved
                    ),
                    None,
                )
                if fallback:
                    px, py = fallback
                    dungeon.tiles[py][px] = TileType.PACT
                    dungeon.pacts.append(fallback)

            # Three sigils and one sealed vault: the floor's optional objective
            free_tiles = [
                (x, y)
                for room in dungeon.rooms
                for y in range(room.y1 + 1, room.y2 - 1)
                for x in range(room.x1 + 1, room.x2 - 1)
                if dungeon.tiles[y][x] == TileType.FLOOR
                and (x, y) not in (dungeon.player_spawn, dungeon.stairs_pos)
            ]
            rng.shuffle(free_tiles)
            for sx, sy in free_tiles[:3]:
                dungeon.tiles[sy][sx] = TileType.SIGIL
                dungeon.sigils.append((sx, sy))
            for vx, vy in free_tiles[3:]:
                dungeon.tiles[vy][vx] = TileType.VAULT
                dungeon.vault = (vx, vy)
                break

            # Wall sconces (torches on walls directly above floors)
            for room in dungeon.rooms:
                top_y = room.y1 - 1
                if top_y >= 0:
                    mid_x = room.center[0]
                    if dungeon.tiles[top_y][mid_x] == TileType.WALL:
                        dungeon.sconces.append((mid_x, top_y))

        return dungeon

    def _carve_corridor(
        self,
        dungeon: Dungeon,
        start: Tuple[int, int],
        end: Tuple[int, int],
        rng: random.Random,
    ) -> None:
        x1, y1 = start
        x2, y2 = end

        if rng.random() < 0.5:
            self._carve_h(dungeon, x1, x2, y1)
            self._carve_v(dungeon, y1, y2, x2)
        else:
            self._carve_v(dungeon, y1, y2, x1)
            self._carve_h(dungeon, x1, x2, y2)

    def _carve_h(self, dungeon: Dungeon, x1: int, x2: int, y: int) -> None:
        for x in range(min(x1, x2), max(x1, x2) + 1):
            if dungeon.in_bounds(x, y):
                dungeon.tiles[y][x] = TileType.FLOOR

    def _carve_v(self, dungeon: Dungeon, y1: int, y2: int, x: int) -> None:
        for y in range(min(y1, y2), max(y1, y2) + 1):
            if dungeon.in_bounds(x, y):
                dungeon.tiles[y][x] = TileType.FLOOR
