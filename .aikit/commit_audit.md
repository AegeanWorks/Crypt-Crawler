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

## 1 → 9 — `f87efc4` (champions, rewards, bounties, CRT)

- **Historical gate**: `python -m unittest discover -s tests` → **33 tests OK**.
- **Cumulative changes**: elite champion affixes, kill streak, bestiary records,
  click-to-move pathfinding, variable-ratio rewards, near-miss surge, floor bounties and
  the CRT scanline overlay/toggle.
- **Finding**: the CRT toggle is a display preference, but it was not persisted. Toggling
  it sets `body.crt-active` and shows the overlay, then writes nothing to storage; a
  reload resets the page to CRT-off. Probe before the fix: `on: {active: true, stored:
  null}` → `afterReload: {active: false, overlayHidden: true, stored: null}`. The
  reduced-motion preference next to it already persists, so this was a surviving gap
  from the 1→9 range.
- **Fix**: `ui.js` reads `crypt_crawler_crt`, applies it on construction through
  `_applyCrtState()`, and `toggleCrt()` writes the choice. Add
  `tests/test_crt_persistence.py` and the `crt_preference_survives_reload` harness check;
  document the persistence in the README.
- **Proof**: seed 42 B1F, 1920x1080, dsf 2. Before fix after reload:
  `.inspect/cycles/c42/before-3-after-reload.png` (no scanlines, CRT off). After fix:
  `.inspect/cycles/c42/after-3-after-reload.png` (scanline overlay on, button teal,
  `stored: "1"`). The on/off pair is `after-1-off.png` / `after-2-on.png`.
- **Gates**: unit 210 OK; harness 135 checks, 0 failed; inspector 75/75 at three
  viewports, 0 console errors; aikit check 5/5.
- **Action**: fixed at `HEAD`.
- **Commit**: `fix(ui): persist the CRT scanline preference`.
- **Push**: via `python aikit.py publish crypt-crawler`.
