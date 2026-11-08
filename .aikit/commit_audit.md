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

## 1 → 12 — `f4c1f80` (relic slots, comparisons, loot FX)

- **Historical gate**: `python -m unittest discover -s tests` → **35 tests OK**.
- **Cumulative changes**: five relic slots, item comparison card, loot FX, starter weapon
  and expanded catalog data.
- **Finding**: the comparison feature had no end-to-end verification. The unit suite
  checked item data and equipment caps, but nothing selected an item in the live UI and
  asserted the diff card.
- **Fix**: add the `equipment_comparison_shows_deltas` harness check: click the starting
  `sword_iron` slot and require a visible `vs Empty Slot` card with `+4 ATK`.
- **Proof**: harness check returns
  `{"text": "vs Empty Slot:+4 ATK", "hidden": false}`; harness **137/137**, unit 210 OK.
- **Action**: test gap closed.
- **Commit**: `test(harness): cover the equipment comparison`.
- **Push**: via `python aikit.py publish crypt-crawler`.

## 1 → 15 — `6d1e583` (low-HP warning and damage feedback)

- **Historical gate**: `python -m unittest discover -s tests` → **37 tests OK**.
- **Cumulative changes**: low-HP vignette and HP-bar warning, transient damage flash,
  weapon stun/poison procs, filterable inventory and capacity meter.
- **Findings**: no surviving defect. The low-HP and damage-feedback paths are exercised
  by the three-viewport inspector (`low_hp_warning_visible`, `damage_flash_active`) and
  its 75/75 audit; weapon procs are covered by `tests/test_combat.py`; the filter and
  capacity paths are exercised by the inspector inventory audit.
- **Action**: none.
- **Push**: via `python aikit.py publish crypt-crawler`.

## 1 → 18 — `7025ae0` (inventory selection and equipment caps)

- **Historical gate**: `python -m unittest discover -s tests` → **39 tests OK**.
- **Cumulative changes**: real-index inventory selection under filters/sorting, expanded
  equipment slots, equip/unequip caps and the full-backpack guard.
- **Findings**: no surviving defect. `tests/test_combat.py` covers the full-backpack and
  unequip limits; `tests/test_equipment_save.py` covers the free-action save paths; the
  inspector checks `.inv-slot.selected` against the real item title. The 1→12 comparison
  check also exercises the same selection path at current `HEAD`.
- **Action**: none.
- **Push**: via `python aikit.py publish crypt-crawler`.

## 1 → 21 — `4770907` (mobile layout)

- **Historical gate**: `python -m unittest discover -s tests` → **39 tests OK**.
- **Cumulative changes**: below 768px the three panels stack into one scrolling column,
  the action deck and D-pad stay visible, and the header wraps instead of overflowing.
- **Findings**: no surviving defect. The current inspector runs the mobile 390×844
  viewport with 75/75 checks and 0 console errors; the canvas/action deck/D-pad and
  panel order are exercised there.
- **Action**: none.
- **Push**: via `python aikit.py publish crypt-crawler`.

## 1 → 24 — `4e5733d` (AGL-1.1 licensing migration)

- **Historical gate**: `python -m unittest discover -s tests` → **48 tests OK**.
- **Cumulative changes**: licensing switch to Aegean Game License 1.1, commercial rider,
  license metadata and README license copy.
- **Findings**: no surviving defect. `LICENSE` is AGL-1.1, `COMMERCIAL.md` is present,
  and the README links both. No game code path is affected.
- **Action**: none.

## 1 → 27 — `a8dcbed` (reviewed media assets)

- **Historical gate**: `python -m unittest discover -s tests` → **48 tests OK**.
- **Cumulative changes**: reviewed social previews, project identity media and the
  accepted-assets set.
- **Findings**: no surviving defect. `assets/social-preview.png` exists and is the image
  referenced at the top of the README; no broken media path.
- **Action**: none.

## 1 → 30 — `ab1e7c7` (brand identity)

- **Historical gate**: `python -m unittest discover -s tests` → **48 tests OK**.
- **Cumulative changes**: reviewed AI-art brand marks and identity assets replacing the
  procedural marks.
- **Findings**: no surviving defect. The README brand-assets section points at the
  current assets and the historical markup is gone; no game behavior changed.
- **Action**: none.

- **Push (24/27/30 batch)**: via `python aikit.py publish crypt-crawler`.
