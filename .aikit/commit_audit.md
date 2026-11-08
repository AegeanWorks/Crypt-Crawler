# Commit-range audit

Audit protocol: the baseline is commit 1 (`6f58598`). Checkpoints are every third
commit to `HEAD`: 1→3, 1→6, 1→9, and so on. Each checkpoint is checked out in an
isolated worktree, its own canonical test command is run, and the cumulative diff is
reviewed against the current tree for surviving bugs, gaps or missing implementations.
A found defect is fixed at `HEAD` with a failing-first test; otherwise the run is
recorded dry. Every run ends with `python aikit.py publish crypt-crawler`.

## 1 → 3 — `6a49650` (initial game, launchers, descent persistence)

- **Historical gate**: `python -m unittest discover -s tests` → **17 tests OK**.
- **Cumulative changes**: playable tactical game, procedural dungeon, combat, HUD,
  headless inspector, Windows/POSIX launchers, player progression on floor descent.
- **Findings**: no failure in the historical suite. The range has no full run
  save/resume, classes, bosses or status effects; those are later checkpoint work and
  are present and covered at current `HEAD` (208 tests).
- **Action**: none.
- **Push**: `python aikit.py publish crypt-crawler` → pushed `d70ba13` (UI review
  closed first; direct `git push` is intentionally blocked by AIKit).

## 1 → 6 — `b5729c4` (merchant safety, descent class, crit sync)

- **Historical gate**: `python -m unittest discover -s tests` → **27 tests OK**.
- **Cumulative changes**: hero classes, biomes, hermit merchant, run save/resume,
  merchant sanctuary spacing, descent class persistence, crit-rate sync.
- **Findings**: no surviving defect. Current coverage still exercises the fixes:
  `tests/test_server.py` (merchant coordinates disjoint from monsters),
  `tests/test_combat.py` (class crit rates), and the harness descent/resume checks.
- **Action**: none.
- **Push**: recorded with this file.
