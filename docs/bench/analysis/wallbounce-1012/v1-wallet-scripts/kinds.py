import sys, glob, collections, pyarrow.parquet as pq, pyarrow.compute as pc
run = sys.argv[1]
cnt = collections.Counter(); maxstep = 0
for f in sorted(glob.glob(run + '/l1_events*.parquet')):
    t = pq.read_table(f, columns=['step', 'kind'])
    vc = pc.value_counts(t['kind']).to_pylist()
    for d in vc:
        cnt[d['values']] += d['counts']
    maxstep = max(maxstep, pc.max(t['step']).as_py())
print('maxstep', maxstep)
for k, v in cnt.most_common():
    print(k, v)
