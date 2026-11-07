# Improvement Cycle Record

Evidence images live under `.inspect/cycles/<cycle>/` (git-ignored: binaries are not committed).
Each entry names the exact capture command so the pair can be reproduced from the same seed,
class, difficulty and viewport.

## Cycle 1 — Canvas fit and click-to-move alignment (2026-11-07)

- **Area**: UI readability / pointer input (graphics).
- **Find**: At 1920x1080 the `#gameCanvas` frame was 900x920 while the 760x540 bitmap was
  letterboxed to 900x639, leaving 140px of dead black above and below (116px at 1440x900). The
  drawn map was smaller than the panel allowed, and `_getTileAtPointer` mapped clicks against the
  full element rect: a click on visible tile (5,17) decoded as (5,18), and a click in the black
  band moved the hero. Reproducer: the three new selftest checks failed before the fix
  (`canvas_hugs_its_bitmap` gap 116, `click_maps_to_the_visible_tile` 5,17 -> 5,18,
  `click_outside_the_bitmap_is_ignored` decoded 5,17 from the band).
- **Analyze**: `static/css/style.css` `#gameCanvas` forced `height: 100%` with
  `object-fit: contain`; `static/js/engine.js` `_getTileAtPointer` used `rect.width/height`.
  Fix the CSS ratio and the pointer math, guard both with tests. Killed: enlarging the bitmap
  buffer (renderer rework, out of scope for this defect; the CSS fix already enlarges the
  displayed map).
- **Fix**: `aspect-ratio: 760 / 540`, `height: auto`,
  `max-width: min(1100px, calc((100vh - 160px) * 760 / 540))`; mobile keeps 100% width and the
  360px cap. `_getTileAtPointer` now derives the drawn content box from the buffer aspect,
  rejects points in a band, and scales through it. New `tests/test_canvas_fit.py`; three new
  `tools/ai_harness.py selftest` checks.
- **Screenshots** (same seed 42, paladin, normal, turn 1, player 6,26, 1920x1080):
  - before: `.inspect/cycles/c1/before-desktop-1920.png` (900x920 frame, 140px bands, 54px tiles)
  - after: `.inspect/cycles/c1/after-desktop-1920.png` (1100x781 frame, no bands, 66px tiles)
  - command: `python .inspect/cycles/capture.py --out .inspect/cycles/c1/<name>.png --seed 42 --width 1920 --height 1080`
  - laptop/mobile: `.inspect/cycles/c1/inspect/dungeon_laptop.png`, `dungeon_mobile.png` (inspector).
- **Played run** (real mouse clicks, `.inspect/cycles/play_c1.py`): at 1920x1080 seed 42 the
  hero stood at (6,26); a click on the visible explored tile (5,21), five rows up, moved the
  hero to (6,25) and advanced turn 1 -> 2 (`play-before-click.png` -> `play-after-click.png`,
  the clicked tile is outlined). With a forced tall box, a click in the 87px letterbox band left
  position and turn unchanged (`play-band-click.png`). Page errors: none.
- **Gates**: `python -m unittest discover -s tests` -> 139 tests OK;
  `python tools/ai_harness.py selftest` -> 66 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75,
  0 console errors; `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(ui): fit the canvas to its bitmap and align click-to-move`.

## Cycle 2 — Twin-hit damage numbers (2026-11-07)

- **Area**: Combat feel (damage feedback).
- **Find**: Two melee enemies striking in one enemy phase spawn identical `-1` floats at the
  same x/y with the same velocity and life, so they draw exactly on top of each other. The
  reproducer (`twin_hits_stack_and_sum_to_damage`) read two floats at y=1021 (`distinct: 1`)
  after the player lost 10 HP.
- **Analyze**: `static/js/renderer.js:addFloatingText` pushed raw coordinates with no stacking.
  Fix there only; a per-enemy animation cadence was killed because it would make the turn loop
  asynchronous and risk input during resolution, well outside this defect.
- **Fix**: count recent floats (life > 30) within 2px on x and lift the new float 18px; add the
  selftest check plus `no_page_errors_after_stacked_hits`.
- **Screenshots** (same seed 42, paladin, normal, turn 3, player 13,15, HP 62, goblins at
  13,14 and 14,15):
  - before: `.inspect/cycles/c2/before-double-hit.png` / `before-double-hit-zoom.png`
  - after: `.inspect/cycles/c2/after-double-hit.png` / `after-double-hit-zoom.png`
  - command: `python .inspect/cycles/play_c2.py before|after`
- **Played run**: real Playwright session (not the harness) at 1920x1080; the hero waited while
  two goblins closed in, then waited again. Before the fix the player lost 2 HP and one `-1`
  appeared; after the fix the same state lost 2 HP and two `-1` numbers appeared 18px apart
  (`after-run.txt`: floats y=690 and y=672, `damage_dealt: 2`, turn 4). No page errors.
- **Gates**: `python -m unittest discover -s tests` -> 139 OK;
  `python tools/ai_harness.py selftest` -> 68 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75,
  0 console errors; `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(combat): stack simultaneous damage numbers`.

## Cycle 3 — Dread Necromancer ranged identity (2026-11-07)

- **Area**: Enemies/bosses.
- **Find**: The server spawns Dread Necromancers from B2F and the bestiary claimed they chant
  spells from afar, but the shipped engine had no necromancer branch. At range 4 the selftest
  read `necroHit: 0, necroStayed: false`: it walked one tile closer instead of casting; behind a
  chest it stood idle because the step was blocked.
- **Analyze**: `static/js/engine.js:processEnemyTurns` handles archers, hounds, the Choir and
  Malakor but not the necromancer. Add one ranged branch plus text alignment; no new subsystem,
  save field or RNG change. Killed: a mana-shield mechanic (would need every damage path
  refactored; the bestiary now states the shipped rule instead).
- **Fix**: at visible range 2-5 with LOS the necromancer chants a grave bolt (enemy damage roll,
  purple projectile, `-N HEX` float, log) and holds position; adjacent it still staff-melees.
  Bestiary, README enemy table and in-game guide updated. Selftest checks
  `necromancer_hexes_from_range` and `necromancer_melees_when_adjacent`.
- **Screenshots** (same seed 42, B2F, paladin, normal, player 36,16, necromancer 37,19):
  - before: `.inspect/cycles/c3/before-hex-full.png` / `before-hex-zoom.png` (necro steps to
    36,19, no projectile, HP stays 65)
  - after: `.inspect/cycles/c3/after-hex-full.png` / `after-hex-zoom.png` (necro holds, purple
    bolt, `-6 HEX`, HP 59, log line)
  - command: `python .inspect/cycles/play_c3.py before|after` (the before run uses HEAD engine.js)
- **Played run** (`.inspect/cycles/play_c3_fight.py`, real Playwright session, 1920x1080):
  equipped the Forged Iron Sword (ATK 12), waited at range: hexes took 65 -> 59 -> 53 -> 46 -> 41
  while the necromancer held at (37,19); closed to (36,19); staff melees then five strikes killed
  it (necro HP 37 -> 28 -> 18 -> 10 -> 1 -> 0) for 45 XP and 49 gold, player finished at 15 HP
  with Zeal +3. Logs: "Dread Necromancer chants a grave bolt for 6 damage!", "Defeated Dread
  Necromancer! Gained 45 XP, 49 Gold." No page errors (`fight-hex.png`, `fight-final.png`).
- **Gates**: `python -m unittest discover -s tests` -> 139 OK;
  `python tools/ai_harness.py selftest` -> 70 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75,
  0 console errors; `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(enemies): make the Dread Necromancer hex from range`.

## Cycle 4 — Room theme floor emblems (2026-11-07)

- **Area**: Levels (room identity).
- **Find**: The generator assigns five room themes and tunes trap density by theme, but
  `renderer.js` never read `room_themes`. Before-captures of seed 42 rooms 1 (chapel), 6
  (ossuary) and 9 (urn crypt) are identical plain stone floors.
- **Analyze**: Pure display gap, no rule defect; draw a faint glyph under props/actors so the
  existing DATA becomes legible. Killed: per-theme gameplay rules (out of scope, would touch the
  generator contract) and text labels (breaks the diegetic map).
- **Fix**: `_drawRoomThemes` + `_drawThemeGlyph` at 17% alpha: gold cross+halo, bone skull, blue
  arches, orange urn, red chevrons. `tests/test_room_themes.py` locks one palette colour and one
  glyph branch per `ROOM_THEMES` entry.
- **Screenshots** (same seed 42, B1F, paladin, normal, 1920x1080, player at each room centre):
  - chapel: `.inspect/cycles/c4/before-chapel.png` / `after-chapel.png`
  - ossuary: `.inspect/cycles/c4/before-ossuary.png` / `after-ossuary.png`
  - urn crypt: `.inspect/cycles/c4/before-urn_crypt.png` / `after-urn_crypt.png`
  - command: `python .inspect/cycles/play_c4.py before|after`
- **Played run**: visual-only change, no mechanics claim. The inspector opened a fresh run
  (1440/1920 desktop, laptop, mobile) and the east choke room shows the red chevrons in
  `.inspect/cycles/c4/inspect/dungeon_desktop.png`; 75/75 audit checks, 0 console errors.
- **Gates**: `python -m unittest discover -s tests` -> 141 OK;
  `python tools/ai_harness.py selftest` -> 70 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(levels): draw a floor emblem for every room theme`.

## Cycle 5 — Save version refusal (2026-11-07)

- **Area**: Progression and saves.
- **Find**: `saveGameState` wrote `version: 2`, but `loadSavedRun` never checked it. Repro:
  `unsupported_save_version_is_refused` read `acceptedFuture: true`; a real reload with a
  `version: 99` save resumed Turn 3 / seed 42 with no warning.
- **Analyze**: The shipped writer and loader must share one version constant and the loader must
  refuse anything else without mutating storage (project guideline). No migration is needed: v1
  lived under a different key. Killed: a migration table (no older version can reach this key).
- **Fix**: `SAVE_VERSION = 2` exported, writer uses it, loader refuses `data.version !==
  SAVE_VERSION` with a console warning and no `setItem`/`removeItem`; new
  `tests/test_save_version.py` and selftest check.
- **Screenshots** (same real reload, 1920x1080; save taken at Turn 3, seed 42, then version
  forced to 99):
  - before: `.inspect/cycles/c5/before-reload-top.png` (resumed Turn 3, Ember Tithe)
  - after: `.inspect/cycles/c5/after-reload-top.png` (fresh Turn 1, Blood Moon)
  - full pages: `before-reload-full.png`, `after-reload-full.png`
  - command: `python .inspect/cycles/play_c5.py before|after` (before uses HEAD engine.js)
- **Played run**: real page reload after waiting two turns and saving. Before: turn 3, runSeed 42,
  log "Resumed your ongoing dungeon run from crystal memory.", disk version 99. After: turn 1,
  runSeed 81401, log starts at "Entered Depth B1F...", console warning "Refusing unsupported
  save version 99; expected 2. The stored save was left untouched.", no page errors.
- **Gates**: `python -m unittest discover -s tests` -> 143 OK;
  `python tools/ai_harness.py selftest` -> 72 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(save): refuse unsupported save versions`.
