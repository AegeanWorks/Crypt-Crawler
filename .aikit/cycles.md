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

## Cycle 6 — Bow release and boss telegraph audio cues (2026-11-07)

- **Area**: Audio cues.
- **Find**: Instrumenting `AudioContext.createOscillator` showed the Skeletal Archer scheduled
  only the impact (160 Hz) and the Hollow Choir's hum / Malakor's inhale scheduled nothing. The
  two avoidable windups were log-only, and an arrow sounded like a melee hit.
- **Analyze**: Add two synth cues and wire the three call sites; no visual, rule, save or RNG
  change. Killed: a distinct hex cue for the necromancer (the fireball sound is already audible;
  keep the cycle to silent events).
- **Fix**: `playBow()` (880 -> 220 Hz) before the archer impact; `playTelegraph(kind)` (196 Hz
  hymn, 110 Hz drain) on the Choir hum, Choir silence phase and Malakor inhale. Selftest
  `ranged_and_telegraph_cues_fire` records the scheduled frequencies; `tests/test_audio_cues.py`
  locks the synth and call-site contract.
- **Screenshots** (same scenes, seed 42 B2F / seed 4242 B3F, 1920x1080; the cues are audio, so
  the pairs also carry the before/after oscillator logs):
  - archer: `.inspect/cycles/c6/before-archer.png` / `after-archer.png` (log "looses a bone
    arrow"; before events [160], after [880, 160])
  - Choir: `before-choir.png` / `after-choir.png` (log "hums one note"; before [], after [196])
  - Malakor: `before-lich.png` / `after-lich.png` (log "Malakor inhales"; before [], after [110])
  - command: `python .inspect/cycles/play_c6.py before|after` (before uses HEAD audio/engine)
- **Played run**: real Playwright sessions with `waitTurn`; archer at (31,21) vs player (30,18)
  hit for 3 (65 -> 62); Choir hummed on turn 3 and Malakor inhaled on turn 2; no page errors.
  The JSON event logs are in `before.txt` / `after.txt`.
- **Gates**: `python -m unittest discover -s tests` -> 145 OK;
  `python tools/ai_harness.py selftest` -> 74 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(audio): cue bow releases and boss telegraphs`.

## Cycle 7 — Chronicle top-edge fade (2026-11-07)

- **Area**: UI readability.
- **Find**: The bottom-anchored Dungeon Chronicle shears its oldest visible line at the top
  edge whenever it overflows (`before-chronicle-zoom.png`: "heal 30% more." cut through the
  glyphs at seed 42, turn 9, scrollTop 137).
- **Analyze**: The log is a scroll box with no top affordance. A sticky pseudo-element changed
  the scroll geometry (688 vs 701px) and shifted the visible line, so the fix moved to a wrapper
  overlay. Killed: mask-image on the box (it fades the border and the first line when unscrolled)
  and increasing the height (does not address the cut).
- **Fix**: `.chronicle-wrap` + `:has(.chronicle-log.is-scrolled)::after` gradient, toggled by a
  scroll listener and `_updateChronicleFade()` after each append; `tests/test_chronicle_fade.py`.
- **Screenshots** (same seed 42, B1F, turn 9, 19 log entries, scrollTop 137, 1920x1080):
  - before: `.inspect/cycles/c7/before-chronicle-full.png` / `before-chronicle-zoom.png`
  - after: `.inspect/cycles/c7/after-chronicle-full.png` / `after-chronicle-zoom.png`
  - command: `python .inspect/cycles/play_c7.py before|after` (before uses HEAD CSS/JS/HTML)
- **Played run**: the inspector opened a fresh run at three viewports; the scrolled chronicle in
  `.inspect/cycles/c7/inspect/dungeon_desktop.png` shows the faded top edge; 75/75 audit checks,
  0 console errors.
- **Gates**: `python -m unittest discover -s tests` -> 148 OK;
  `python tools/ai_harness.py selftest` -> 74 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(ui): fade the scrolled chronicle top edge`.

## Cycle 8 — Physical arrows vs spell bolts (2026-11-07)

- **Area**: Graphics and effects.
- **Find**: The Skeletal Archer's bone arrow and the Dread Necromancer's grave bolt both
  rendered as the same 5px glowing orb with sparks. At flight progress 0.51 the before captures
  are indistinguishable.
- **Analyze**: `addProjectile` carried only a color; `_renderProjectiles` drew one orb. Add a
  `kind` and two shapes, display-only. Killed: changing projectile speed/impact (it is cosmetic
  and the damage is applied on the turn, so timing must not move).
- **Fix**: `addProjectile(..., kind = "bolt")`; `_renderProjectiles` draws `arrow` as a 20px
  fletched shaft rotated along the flight and `bolt` as an orb with a 20px tapered trail; the
  archer passes `"arrow"`. `tests/test_projectile_style.py` locks both shapes and the call.
- **Screenshots** (same seed 42 B2F, player 4 tiles from the target, projectile frozen at
  progress 0.51, 1920x1080):
  - archer: `.inspect/cycles/c8/before-archer-zoom.png` (glowing orb) vs
    `after-archer-zoom.png` (fletched arrow)
  - hex: `before-hex-zoom.png` (orb) vs `after-hex-zoom.png` (orb + trail)
  - full pages: `before-archer.png`, `after-archer.png`, `before-hex.png`, `after-hex.png`
  - command: `python .inspect/cycles/play_c8.py before|after` (before uses HEAD renderer/engine)
- **Played run**: real `waitTurn` sessions; the archer hit for 4 and the necromancer for 7 in
  `after.txt`, with matching chronicle lines and no page errors; the frozen frame is only for
  the comparison shot.
- **Gates**: `python -m unittest discover -s tests` -> 150 OK;
  `python tools/ai_harness.py selftest` -> 74 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(gfx): render bone arrows as arrows, spells as streaks`.

## Cycle 9 — The killing blow gets a beat (2026-11-07)

- **Area**: Combat feel (death feedback).
- **Find**: `handlePlayerDeath` opened the ledger in the same frame as the fatal hit. The
  before capture 150ms after death is already the modal, hiding the `-98` float, and the HUD
  still reads 65/65 because `finishPlayerTurn` returns before `ui.updateHero`. The failing
  selftest read `modal: true` at t=0 and no PERISHED float.
- **Analyze**: Centralize the beat in `handlePlayerDeath`; keep `gameOver`, save clearing and
  run recording immediate, show the HUD at zero, and delay only the modal. Killed: delaying
  the state change (would let a dead hero act) and animating the modal itself (out of scope).
- **Fix**: `ui.updateHero` before feedback, `☠ YOU PERISHED` float + 500ms shake, 750ms
  `runToken`-guarded modal delay; inspector gameover scenario waits 0.9s; new
  `tests/test_death_beat.py` and two selftest checks.
- **Screenshots** (same seed 42 B1F, player 13,15 at 1 HP vs goblin 13,14):
  - before: `.inspect/cycles/c9/before-death-early.png` (modal at 150ms, HUD 65/65)
  - after: `.inspect/cycles/c9/after-death-early.png` (canvas at 150ms, HUD 0/65,
    `☠ YOU PERISHED` + `-98`, red vignette)
  - modal at 1s: `before-death-modal.png` / `after-death-modal.png`
  - command: `python .inspect/cycles/play_c9.py before|after` (before uses HEAD engine.js)
- **Played run**: real `waitTurn` death. Before: gameOver, modal true, HUD 65/65, no PERISHED.
  After: gameOver true, modal false, HUD "0 / 65", PERISHED float; modal true at 1s with
  "YOU PERISHED IN THE CRYPT"; no page errors.
- **Gates**: `python -m unittest discover -s tests` -> 152 OK;
  `python tools/ai_harness.py selftest` -> 77 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(combat): hold the death ledger for the killing blow`.

## Cycle 10 — A dead hero cannot be attacked or robbed (2026-11-08)

- **Area**: Combat feel (death handling).
- **Find**: Poison ticked first, then the enemy phase ran anyway. At 1 HP with poison, the
  goblin attacked for 98 and stole 9 gold after the hero was already dead; the ledger said
  "in mortal combat". Two adjacent killers both acted after the first killed the hero.
  Failing checks: `poison_death_skips_the_enemy_turn` (goblin attack in the log) and
  `death_stops_later_enemies` (`first: true, second: true`).
- **Analyze**: `_tickPlayerStatuses` had no return, `finishPlayerTurn` checked death only after
  the enemy phase, and `processEnemyTurns` never stopped mid-loop. Fix all three; keep the
  state changes and death beat from ADR-050. Killed: reviving/undoing the poison tick (the state
  is correct; only the post-death actions are wrong).
- **Fix**: status tick returns `poison`/`burn`, `finishPlayerTurn` passes it to
  `handlePlayerDeath` and returns, monster status ticks stop while dead, enemy loop breaks on
  `hp <= 0` (top, archer, melee; boss/necromancer branches break), new `tests/test_death_cause.py`
  and two selftest checks.
- **Screenshots** (same seed 42 B1F, player 13,15 at 1 HP with poison 3, goblin 13,14):
  - early: `.inspect/cycles/c10/before-poison-early.png` (goblin `-98` + theft, gold 16) vs
    `after-poison-early.png` (only `-3 POISON`, gold 25)
  - ledger: `before-poison-modal.png` ("in mortal combat", gold 16) vs
    `after-poison-modal.png` ("You fell to poison.", gold 25)
  - command: `python .inspect/cycles/play_c10.py before|after` (before uses HEAD engine.js)
- **Played run**: real `waitTurn` death. Before: hp 0, gold 25 -> 16, log "Sneaky Goblin attacks
  you for 98 damage!" and "stole 9 gold"; after: hp 0, gold 25, log only "Venom burns in your
  veins! (-3 HP)", modal "You fell to poison."; no page errors.
- **Gates**: `python -m unittest discover -s tests` -> 155 OK;
  `python tools/ai_harness.py selftest` -> 81 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(combat): stop enemies and name the cause after a status death`.

## Cycle 11 — Melee enemies detour around blockers (2026-11-08)

- **Area**: Enemies/bosses (melee AI).
- **Find**: `_stepToward` tries one x then one y step. With a real chest at (10,7) between
  a skeleton at (9,7) and the player at (11,7), the skeleton stayed at (9,7) for six turns,
  distance 2, no damage, only wait lines. Failing check: `monster_paths_around_a_blocking_prop`
  read `moved: false, distance: 2, damage: 0`.
- **Analyze**: Greedy movement has no detour. Add a BFS fallback over walkable, unoccupied
  tiles; keep greedy as the preferred step. Killed: full A* or a navigation grid (the map is
  45x30, BFS only on a blocked step is enough).
- **Fix**: `_stepTowardPath` (BFS to the player tile, walls/props/monsters solid, player tile
  only as the goal), used when `_stepToward` fails for the normal step and the hound/Swift
  second step; `tests/test_enemy_pathing.py` + `monster_paths_around_a_blocking_prop`.
- **Screenshots** (same seed 42 B1F, player 11,7, skeleton 9,7, chest 10,7, after six waits):
  - start: `.inspect/cycles/c11/before-path-start.png` / `after-path-start.png`
  - after: `before-path-after.png` (skeleton still at 9,7, HP 65) vs
    `after-path-after.png` (skeleton at 11,8, HP 61, three attack lines in the chronicle)
  - command: `python .inspect/cycles/play_c11.py before|after` (before uses HEAD engine.js)
- **Played run**: real `waitTurn` x6. Before: turn 7, monster (9,7), distance 2, HP 65, log only
  waits. After: turn 7, monster (11,8), distance 1, HP 61, log "Path Skeleton attacks you for
  1/2/1 damage!"; no page errors.
- **Gates**: `python -m unittest discover -s tests` -> 157 OK;
  `python tools/ai_harness.py selftest` -> 83 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(enemies): walk melee foes around blocking props`.

## Cycle 12 — Room themes survive resume (2026-11-08)

- **Area**: Levels (floor identity across save/resume).
- **Find**: The save stored tiles, rooms and props but not `room_themes`; `ClientDungeon`
  defaults a missing list to `"ossuary"`, so a reload repainted every room as an ossuary.
  Failing check: seed 4242 saved 4 distinct themes and resumed with 13x "ossuary".
- **Analyze**: Additive save field; no version bump (old saves keep the old default). The
  behavior lives in the writer; the reader already accepts the field. Killed: a save-version
  bump/migration (not needed, and would refuse otherwise valid saves).
- **Fix**: `room_themes: this.dungeon.room_themes` in `saveGameState`; writer contract in
  `tests/test_room_themes.py`; `resume_restores_room_themes` selftest check.
- **Screenshots** (same seed 42 B1F save at (11,6), turn 1, real page reload, 1920x1080):
  - chapel: `.inspect/cycles/c12/before-chapel.png` (skull) vs `after-chapel.png` (cross)
  - urn crypt: `before-urn_crypt.png` (skull) vs `after-urn_crypt.png` (urn)
  - ossuary: `before-ossuary.png` / `after-ossuary.png` (unchanged skull)
  - command: `python .inspect/cycles/play_c12.py before|after` (before uses HEAD engine.js)
- **Played run**: real `page.reload` resume. Before: themes all "ossuary", player (11,6),
  turn 1. After: the original 11-theme list (gallery/chapel/choke/ossuary/urn_crypt) loads
  unchanged, player (11,6), turn 1; no page errors.
- **Gates**: `python -m unittest discover -s tests` -> 158 OK;
  `python tools/ai_harness.py selftest` -> 85 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(levels): persist room themes across save and resume`.

## Cycle 13 — Deck affordability matches the real costs (2026-11-08)

- **Area**: UI readability (action deck).
- **Find**: The dimming table keyed costs by button id, but slot 4 is class-dependent: rogue
  Fireball and mage Nova both cost 10 MP while the table said 8. At 8-9 MP the buttons looked
  enabled and lacked `aria-disabled`; only the cast-time check refused them. Failing checks:
  `rogue_slot4_is_dimmed_below_10_mana` / `mage_slot4_is_dimmed_below_10_mana` (8/9 not dimmed).
- **Analyze**: Correct the two costs and lock the slot-4 parity; the engine stays the authority.
  The old `test_swarm_fixes` assertion that `btnActionHeal: 10` never appears was stale because
  slot 4 changed class; corrected to check the engine's Heal-8 rule and both Heal slots, intent
  preserved. Killed: a new shared cost module (two values, no new abstraction).
- **Fix**: rogue/mage `btnActionHeal: 10`; `tests/test_deck_costs.py`; two selftest checks
  (dimmed + aria at 8/9, clear at 10).
- **Screenshots** (same seed 42 B1F, turn 1, 8 MP, 1920x1080):
  - rogue: `.inspect/cycles/c13/before-rogue-deck.png` (Fireball bright) vs
    `after-rogue-deck.png` (Fireball dimmed, Heal still bright)
  - mage: `before-mage-deck.png` (Fireball dimmed, Nova bright) vs `after-mage-deck.png`
    (both dimmed, Frost/Barrier bright)
  - full pages: `before-<class>-full.png`, `after-<class>-full.png`
  - command: `python .inspect/cycles/play_c13.py before|after` (before uses HEAD ui.js)
- **Played run**: real rogue/mage sessions at 8 MP. Before: `dimmed: false`, `aria: null`, forced
  click logs "Not enough mana ... (Needs 10 MP)". After: `dimmed: true`, `aria: "true"`,
  Playwright normally refuses the click; forced click still logs the same refusal. No page errors.
- **Gates**: `python -m unittest discover -s tests` -> 160 OK;
  `python tools/ai_harness.py selftest` -> 89 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(ui): dim the right spells in the action deck`.

## Cycle 14 — Cavern floor and wall contrast (2026-11-08)

- **Area**: Graphics and effects (biome readability).
- **Find**: The B2F cavern palette put visible floors at `#0e1c20`/`#0a1619` and walls at
  `#122629`; a real four-step walk showed the room as a near-black void with faint grid lines.
  The floor luminance was ~0.010 versus the crypt's ~0.019, so the room shape was unreadable
  even without the CRT overlay.
- **Analyze**: Raise only the visible cavern palette, leave unexplored/water/torchlight alone.
  Killed: changing the torchlight radius (Deep Fog/positional light already owns that rule) and
  the CRT overlay (optional, page-wide).
- **Fix**: visible walls `#1b3a40` / grid `#2a565e` / lichen `#2f6b70`; visible floors
  `#14343a`/`#102c31` / grid `#24535c`; `tests/test_cavern_contrast.py` locks relative luminance
  (floor >= 0.02, wall >= 0.025, unexplored < half).
- **Screenshots** (same seed 42 B2F, rogue, four steps (6,26) -> (8,24), turn 5, HP 48, 1920x1080):
  - before: `.inspect/cycles/c14/before-cavern-full.png` / `before-cavern-zoom.png`
  - after: `after-cavern-full.png` / `after-cavern-zoom.png` (readable teal floor/wall grid)
  - command: `python .inspect/cycles/play_c14.py before|after` (before uses HEAD renderer.js)
- **Played run**: real `stepPlayer` walk through the B2F spawn room (four steps, turn 5, HP 48);
  before near-black floor, after readable room shape; no page errors.
- **Gates**: `python -m unittest discover -s tests` -> 162 OK;
  `python tools/ai_harness.py selftest` -> 89 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(gfx): lift the cavern floor and wall contrast`.

## Cycle 15 — Trap cues are distinct (2026-11-08)

- **Area**: Audio cues (trap identity).
- **Find**: A trap reveal and a disarm both played the shrine blessing chime (`[220, 277,
  330, 440]`), and spike/dart/snare triggers all played the generic melee hit (`[90, 160]`).
  The audio could not tell a scan from a blessing or one trap kind from another.
- **Analyze**: Add three small synths and wire the existing branches; real shrines keep their
  cue. Killed: changing the search/disarm visuals (already legible; this cycle is audio).
- **Fix**: `playSearch` 600→900, `playDisarm` 350→90, `playTrap(kind)` spike 140→40 / dart
  700+520 / snare 220→70 + rattle, via `_blip` with an optional delay; extend
  `tests/test_audio_cues.py` and add `trap_cues_are_distinct`.
- **Screenshots** (same seed 42 B1F trap scene; the visuals are unchanged, the event logs are
  the proof):
  - reveal: `.inspect/cycles/c15/before-reveal.png` vs `after-reveal.png` (dashed grille,
    `TRAP!`, log "reveal 1 trap")
  - disarm: `before-disarm.png` / `after-disarm.png` ("You disarm the revealed dart trap")
  - trigger: `before-trigger.png` / `after-trigger.png` ("dart trap! Two volleys")
  - command: `python .inspect/cycles/play_c15.py before|after` (before uses HEAD audio/engine)
- **Played run**: real search → disarm → step on a trap at seed 42 B1F. Before: reveal/disarm
  `[220,277,330,440]`, trigger `[90,160]`. After: reveal `[600]`, disarm `[350]`, trigger
  `[90,700,520]` (dart), HP 65 -> 57; no page errors.
- **Gates**: `python -m unittest discover -s tests` -> 163 OK;
  `python tools/ai_harness.py selftest` -> 91 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(audio): give traps their own cues`.

## Cycle 16 — Choir Echoes appear in the Records bestiary (2026-11-08)

- **Area**: Progression and saves (records/bestiary).
- **Find**: A killed `choir_echo` increments `records.bestiary.choir_echo.slain`, but the
  Records modal's `bestiaryDefs` had no echo row. With one echo kill, "Monsters Slain" was 1
  while the codex's last rows were all Unknown Entity. Failing check: `rows: []` despite
  `slain: 2`.
- **Analyze**: Add the missing definition and lock the full killable roster; no save/rule
  change. Killed: changing the split spawn (the echo already exists and is recorded; the
  display row is the defect).
- **Fix**: Choir Echo row (split lore, burst/fire weakness); `tests/test_bestiary.py`;
  `records_show_choir_echo_kills` selftest check.
- **Screenshots** (same seed 42 B2F state with `bestiary.choir_echo.slain = 1`, Records modal,
  1920x1080):
  - before: `.inspect/cycles/c16/before-records-full.png` / `before-records-zoom.png` —
    "Monsters Slain 1" but three Unknown Entity rows
  - after: `after-records-full.png` / `after-records-zoom.png` — "Choir Echo — Slayed: 1"
  - command: `python .inspect/cycles/play_c16.py before|after` (before uses HEAD ui.js)
- **Played run**: seed 42 B2F; the Choir's split posts were crowded by the vault/warden, so the
  shipped `_spawnChoirEcho` helper placed an echo on a free tile; `attackMonster` killed it
  (record `choir_echo.slain: 1`, totalKills 1), then the Records modal showed the row. No page
  errors (`source: "spawn"` recorded in the report).
- **Gates**: `python -m unittest discover -s tests` -> 165 OK;
  `python tools/ai_harness.py selftest` -> 93 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(progression): show Choir Echo kills in the bestiary`.

## Cycle 17 — Execute feedback is rogue-only (2026-11-08)

- **Area**: Combat feel (execute feedback accuracy).
- **Find**: The skull marker and the hover "EXECUTE 💀" suffix appeared for every class at
  <=30% HP, though only the rogue's Executioner passive grants +25%; the hover range also
  ignored the bonus. Paladin saw a promise the engine did not keep; rogue saw "~5-8" when the
  execute hit could reach ~10.
- **Analyze**: Pass the hero class into the monster draw and gate the marker/suffix; apply the
  1.25x to the preview range. The damage rule itself is unchanged and already covered. Observed
  but out of scope: the champion title/affix overlap on long names (future UI cycle).
- **Fix**: `_drawMonster(..., heroClass)` skull only for rogue; tooltip `execute` gate, 1.25x
  range, suffix only for rogue; `tests/test_execute_marker.py`.
- **Screenshots** (same seed 42 B1F, Swift Crypt Skeleton at 60/200 HP, player adjacent, hover,
  1920x1080):
  - paladin: `.inspect/cycles/c17/before-paladin-execute.png` (EXECUTE + skull) vs
    `after-paladin-execute.png` (no EXECUTE, no skull; "Strike ~5-6 • Crit 15%")
  - rogue: `before-rogue-execute.png` ("~5-8 • EXECUTE") vs `after-rogue-execute.png`
    ("~7-10 • EXECUTE", skull retained)
  - full pages: `before-<class>-full.png`, `after-<class>-full.png`
  - command: `python .inspect/cycles/play_c17.py before|after` (before uses HEAD renderer.js)
- **Played run**: real hover and attack on the 60/200 target. Paladin 6 damage, rogue 7 damage
  from their base attacks; the +25% execute rule itself remains proven by
  `rogue_executioner_boosts_low_hp_targets`. No page errors.
- **Gates**: `python -m unittest discover -s tests` -> 167 OK;
  `python tools/ai_harness.py selftest` -> 93 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(combat): show the execute window only to the rogue`.

## Cycle 18 — Boss phases belong to their own boss (2026-11-08)

- **Area**: Enemies/bosses (phase ownership).
- **Find**: Both boss phase blocks were keyed on `monster.is_boss`, so every boss ran
  Malakor's phase first. The Hollow Choir's `phase_two` was consumed by "Malakor tears open the
  vault floor" + 2 risen skeletons, so its split never ran (seed 42 B2F: 0 echoes, 3 skeletons,
  wrong log). The foundry Ashen Warden borrowed the same text and summoned 2 skeletons (5
  total). A crowded Choir also logged "splits into 0".
- **Analyze**: Gate Malakor by type; give other bosses their own named escalation; let the
  Choir own its split and search rings 1-3, retrying instead of spending the phase when
  crowded. Killed: keeping the generic summon for all bosses (wrong fiction and double phase).
- **Fix**: `boss_lich` gates on both Malakor blocks; `otherBoss` seal-break/fury for pack
  bosses; Choir split rings 2-3 + "no room to split" retry; `tests/test_boss_phases.py` and
  three selftest checks (choir split, pack boss, Malakor).
- **Screenshots** (same seed 42, 50% boss HP, real `waitTurn`, 1920x1080):
  - Choir: `.inspect/cycles/c18/before-choir-zoom.png` (0 echoes, 2 risen skeletons,
    "Malakor..." log) vs `after-choir-zoom.png` (2 purple echoes, "splits into 2" log)
  - Warden: `before-warden-full.png` (5 skeletons, Malakor log) vs `after-warden-full.png`
    (3 skeletons, "Ashen Warden's seal breaks", attack 15 -> 18)
  - command: `python .inspect/cycles/play_c18.py before|after` (before uses HEAD engine.js)
- **Played run**: real `waitTurn` at 50% HP. Choir after: 2 echoes, split log; before: 0 echoes,
  3 skeletons, Malakor log. Warden after: attack 15 -> 18, own seal log, no summons; before:
  2 summoned skeletons and Malakor log. Malakor selftest still summons 2 and reaches phase
  three; no page errors.
- **Gates**: `python -m unittest discover -s tests` -> 170 OK;
  `python tools/ai_harness.py selftest` -> 99 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(enemies): give each boss its own phase`.

## Cycle 19 — Named minimap legend (2026-11-08)

- **Area**: Levels (minimap navigation).
- **Find**: The minimap used nine colours (stairs, chest, shop, sigil, vault, trap,
  shrine, pact, soul) plus player/enemy with no key; trap amber was the same as vault gold.
  A new player could not tell a vault from a trap. Failing test: no legend labels in the
  renderer.
- **Analyze**: Add a three-row legend under the 120x84 map; distinguish the trap blip. No rule
  or save change. Killed: replacing the minimap with a DOM panel (bigger surface, no need).
- **Fix**: `_drawMinimapLegend` with nine labelled swatches; trap `#f6ad55`; README
  "Minimap Key"; `tests/test_minimap_legend.py`.
- **Screenshots** (same seed 42 B1F, three real `stepPlayer` moves (6,26)->(8,25), turn 4,
  1920x1080, 4x nearest upscales for legibility):
  - before: `.inspect/cycles/c19/before-minimap.png` / `before-minimap-4x.png` (map only)
  - after: `after-minimap.png` / `after-minimap-4x.png` (Stairs/Chest/Shop,
    Sigil/Vault/Trap, Shrine/Pact/Soul)
  - command: `python .inspect/cycles/play_c19.py before|after` (before uses HEAD renderer.js)
- **Played run**: real three-step walk; turn 4, player (8,25); no page errors. Gate stability:
  `damage_flash_active` flaked once, so the inspector now reads the class in the same
  synchronous evaluate as `flashDamage()`; two consecutive full runs passed 75/75.
- **Gates**: `python -m unittest discover -s tests` -> 172 OK;
  `python tools/ai_harness.py selftest` -> 99 checks, 0 failed (JSON `ok: true`);
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `feat(levels): label every minimap blip`.

## Cycle 20 — Hover titles fit the card (2026-11-08)

- **Area**: UI readability (monster hover card).
- **Find**: Champion names already start with their affix, but the card repeated it
  right-aligned, producing "SkeletonSWIFT" in the 148px card; long names were never measured and
  could spill past the card. Failing test: no `_fitText`/wider card/badge gate.
- **Analyze**: Drop the redundant champion badge (names carry the affix), keep the boss BOSS
  badge, widen the card and ellipsize the title to the remaining width. No rule/save change.
  Killed: dropping the BOSS badge too (boss names do not carry it).
- **Fix**: `const affix = monster.is_boss ? "Boss" : ""`; `cardW = 168`; title measured and
  passed through `_fitText`; `tests/test_hover_title.py`.
- **Screenshots** (same seed 42, paladin, 1920x1080):
  - champion: `.inspect/cycles/c20/before-champion.png` ("SkeletonSWIFT" collision) vs
    `after-champion.png` ("★ Swift Crypt Skeleton" clean, no badge)
  - boss: `before-boss.png` / `after-boss.png` ("Hollow Choir" + right-aligned BOSS, no overlap)
  - full pages: `before-<case>-full.png`, `after-<case>-full.png`
  - command: `python .inspect/cycles/play_c20.py before|after` (before uses HEAD renderer.js)
- **Played run**: real hover over the Swift Crypt Skeleton at 60/200 and the Hollow Choir; no
  page errors; the card reads fully in both cases.
- **Gates**: `python -m unittest discover -s tests` -> 174 OK;
  `python tools/ai_harness.py selftest` -> 99 checks, 0 failed;
  `python tools/inspect_ui.py --viewports desktop,laptop,mobile --scenario all` -> 75/75;
  `python aikit.py check crypt-crawler` -> 5/5.
- **Commit**: `fix(ui): fit hover titles and drop the duplicate affix`.
