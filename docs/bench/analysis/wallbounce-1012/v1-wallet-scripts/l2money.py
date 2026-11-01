import sys, glob, pyarrow.parquet as pq
run = sys.argv[1]
files = sorted(glob.glob(run + '/l2_metrics*.parquet'))
cols = ['step','mean_money','mean_account','n_broke','asset_mean','asset_median','asset_gini','n_present','n_agents','n_in_world']
rows = []
for f in files:
    t = pq.read_table(f)
    names = t.column_names
    use = [c for c in cols if c in names]
    d = t.select(use).to_pydict()
    for i in range(t.num_rows):
        rows.append({c: d[c][i] for c in use})
rows.sort(key=lambda r: r.get('step', 0))
print('n rows', len(rows), 'cols', [c for c in cols if rows and c in rows[0]])
other = [c for c in pq.read_table(files[0]).column_names if c.startswith('n_') or 'present' in c or 'pop' in c]
print('n_* cols', other)
step = int(sys.argv[2]) if len(sys.argv) > 2 else 144
for r in rows:
    s = r.get('step', 0)
    if s % step == 0 or r is rows[-1] or r is rows[0]:
        print({k: (round(v, 1) if isinstance(v, float) else v) for k, v in r.items()})
