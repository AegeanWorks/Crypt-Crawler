import json, hashlib, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))
from crawler.dungeon import DungeonGenerator
seeds=[42,777,12345,999,2,4242,7,13,101,2026]
depths=[1,2,3]
out=pathlib.Path('tools/replay_transcripts')
out.mkdir(exist_ok=True)
rec={}
for s in seeds:
    for d in depths:
        dg=DungeonGenerator(width=45,height=30,depth=d).generate(seed=s)
        dd=dg.to_dict()
        mat={'seed':dd['seed'],'depth':dd['depth'],'biome':dd['biome'],'omen':dd['omen'],
             'rooms':[(r['x'],r['y'],r['w'],r['h']) for r in dd['rooms']],
             'room_themes':sorted(dd['room_themes']),'spawn':dd['player_spawn'],
             'stairs':dd['stairs_pos'],'traps':sorted((t[0],t[1]) for t in dd['traps']),
             'trap_kinds':dd['trap_kinds']}
        h=hashlib.sha256(json.dumps(mat,sort_keys=True).encode()).hexdigest()[:16]
        rec[f'{s}:{d}']=h
(out/'pins.json').write_text(json.dumps(rec,indent=2,sort_keys=True))
print(f"pinned {len(rec)} combos")
