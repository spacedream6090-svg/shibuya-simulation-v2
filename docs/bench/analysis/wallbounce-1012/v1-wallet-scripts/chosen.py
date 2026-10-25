import sys, glob, json, collections
import pyarrow.parquet as pq, pyarrow.compute as pc, pyarrow as pa
run = sys.argv[1]
chosen = 0; n = 0; meals = collections.Counter(); free = 0
for f in sorted(glob.glob(run + '/l1_events*.parquet')):
    t = pq.read_table(f, columns=['agent_id', 'kind', 'payload'])
    t = t.filter(pc.equal(t['kind'], 'spend')).to_pydict()
    for a, pl in zip(t['agent_id'], t['payload']):
        p = json.loads(pl); n += 1
        if p.get('chosen'): chosen += 1
        if str(p.get('cat', '')).startswith('free_'): free += 1
        if p.get('cat') in ('food', 'nightlife'): meals[a] += 1
v = sorted(meals.values())
print('spend n', n, 'chosen', chosen, 'free_*', free)
print('food+nightlife per eating agent: n', len(v), 'med', v[len(v)//2], 'p90', v[9*len(v)//10], 'max', v[-1], 'agents >=4', sum(1 for x in v if x >= 4))
