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
