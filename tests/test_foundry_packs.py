"""Foundry pack integration: installed packs load and take their posts."""

import json
import tempfile
import unittest
from pathlib import Path
from urllib.request import urlopen

from crawler import foundry_packs
from crawler.entities import BOSS_TEMPLATES
from crawler.foundry_packs import pack_load_errors, spawn_for
from crawler.server import start_background_server

PROJECT_ROOT = Path(__file__).resolve().parent.parent
INSTALLED = sorted((PROJECT_ROOT / "packs").glob("*.json"))


def fetch(seed, depth):
    server, port = start_background_server(port=0)
    try:
        url = f"http://127.0.0.1:{port}/api/new-game?seed={seed}&depth={depth}"
        with urlopen(url, timeout=5) as resp:
            return json.loads(resp.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()


class TestFoundryPackLoading(unittest.TestCase):
    def test_installed_packs_registered(self):
        self.assertTrue(INSTALLED, "no packs installed")
        for path in INSTALLED:
            pack = json.loads(path.read_text(encoding="utf-8"))
            key = pack["boss_id"]
            self.assertIn(key, BOSS_TEMPLATES)
            entry = BOSS_TEMPLATES[key]
            for stat in ("hp", "attack", "defense", "xp_reward", "gold_reward"):
                self.assertEqual(entry[stat], pack["stats"][stat])
            self.assertEqual(entry["loot_drop"], pack["loot"]["item_id"])

    def test_installed_packs_clean(self):
        self.assertEqual(pack_load_errors(), [])

    def test_spawn_claims_own_seed(self):
        for path in INSTALLED:
            pack = json.loads(path.read_text(encoding="utf-8"))
            seed = pack["spawn"]["seeds"][0]
            self.assertEqual(spawn_for(depth=3, seed=seed), pack["boss_id"])

    def test_unclaimed_seed_keeps_canon(self):
        self.assertIsNone(spawn_for(depth=3, seed=1))
        self.assertIsNone(spawn_for(depth=3, seed=None))

    def test_pack_boss_takes_stairs_alone(self):
        pack = json.loads(INSTALLED[0].read_text(encoding="utf-8"))
        seed = pack["spawn"]["seeds"][0]
        data = fetch(seed=seed, depth=3)
        bosses = [m for m in data["monsters"] if m["is_boss"]]
        self.assertEqual(len(bosses), 1)
        self.assertEqual(bosses[0]["type"], pack["boss_id"])
        self.assertEqual(
            (bosses[0]["x"], bosses[0]["y"]), tuple(data["dungeon"]["stairs_pos"])
        )

    def test_control_seed_still_lich(self):
        data = fetch(seed=1, depth=3)
        bosses = [m for m in data["monsters"] if m["is_boss"]]
        self.assertEqual(len(bosses), 1)
        self.assertEqual(bosses[0]["type"], "boss_lich")

    def test_foundry_bosses_returns_isolated_copies(self):
        foundry_packs.reset_cache()
        try:
            first = foundry_packs.foundry_bosses()
            key = next(iter(first))
            original = first[key]["hp"]
            first[key]["hp"] = -1
            second = foundry_packs.foundry_bosses()
            self.assertEqual(second[key]["hp"], original)
        finally:
            foundry_packs.reset_cache()

    def _write_temp_pack(self, tmp, overrides):
        import copy

        pack = {
            "pack_version": "1.0",
            "target_game": "crypt-crawler",
            "boss_id": "boss_temp_check",
            "name": "Temp",
            "stats": {"hp": 50, "attack": 10, "defense": 2, "xp_reward": 50, "gold_reward": 50},
            "loot": {"item_id": "ring_shadow"},
            "spawn": {"depth": 3, "anchor": "stairs", "replaces": "boss_lich", "seeds": [999991]},
        }
        for key, value in overrides.items():
            if "." in key:
                top, sub = key.split(".", 1)
                pack[top] = copy.deepcopy(pack[top])
                pack[top][sub] = value
            else:
                pack[key] = value
        path = Path(tmp) / "boss_temp_check.json"
        path.write_text(json.dumps(pack), encoding="utf-8")

    def _load_temp_dir(self, tmp):
        old = foundry_packs.PACKS_DIR
        foundry_packs.PACKS_DIR = Path(tmp)
        try:
            foundry_packs.reset_cache()
            return dict(foundry_packs.foundry_bosses()), list(foundry_packs.pack_load_errors())
        finally:
            foundry_packs.PACKS_DIR = old
            foundry_packs.reset_cache()

    def test_blank_loot_item_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_temp_pack(tmp, {"loot": {"item_id": "   "}})
            bosses, errors = self._load_temp_dir(tmp)
            self.assertEqual(bosses, {})
            self.assertTrue(any("loot.item_id" in e for e in errors))

    def test_duplicate_seeds_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_temp_pack(tmp, {"spawn": {"depth": 3, "anchor": "stairs", "replaces": "boss_lich", "seeds": [42, 42]}})
            bosses, errors = self._load_temp_dir(tmp)
            self.assertEqual(bosses, {})
            self.assertTrue(any("spawn.seeds" in e and "duplicate" in e for e in errors))

    def test_blank_name_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            self._write_temp_pack(tmp, {"name": "   "})
            bosses, errors = self._load_temp_dir(tmp)
            self.assertEqual(bosses, {})
            self.assertTrue(any("name" in e for e in errors))

    def test_bad_pack_skipped_loudly(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "boss_broken.json"
            bad.write_text(json.dumps({"boss_id": "nope"}), encoding="utf-8")
            old, foundry_packs.PACKS_DIR = foundry_packs.PACKS_DIR, Path(tmp)
            try:
                foundry_packs.reset_cache()
                self.assertEqual(foundry_packs.foundry_bosses(), {})
                errors = pack_load_errors()
            finally:
                foundry_packs.PACKS_DIR = old
                foundry_packs.reset_cache()
        self.assertTrue(errors, "bad pack produced no recorded error")
        self.assertTrue(all("boss_broken.json" in e for e in errors))
