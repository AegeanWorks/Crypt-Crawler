import json, hashlib, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from crawler.dungeon import DungeonGenerator
pins = json.loads(pathlib.Path('tools/replay_transcripts/pins.json').read_text())
mismatch = 0
for key, old in sorted(pins.items()):
    s, d = key.split(':')
    dg = DungeonGenerator(width=45, height=30, depth=int(d)).generate(seed=int(s))
    dd = dg.to_dict()
    mat = {'seed': dd['seed'], 'depth': dd['depth'], 'biome': dd['biome'], 'omen': dd['omen'],
           'rooms': [(r['x'], r['y'], r['w'], r['h']) for r in dd['rooms']],
           'room_themes': sorted(dd['room_themes']), 'spawn': dd['player_spawn'],
           'stairs': dd['stairs_pos'], 'traps': sorted((t[0], t[1]) for t in dd['traps']),
           'trap_kinds': dd['trap_kinds']}
    h = hashlib.sha256(json.dumps(mat, sort_keys=True).encode()).hexdigest()[:16]
    if h != old:
        mismatch += 1
        print(f'DIFF {key}: {old} -> {h}')
print(f'{len(pins)-mismatch}/{len(pins)} identical' if mismatch == 0 else f'{mismatch} diffs')
