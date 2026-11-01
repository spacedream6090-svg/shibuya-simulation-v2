import sys, glob, json, collections
import pyarrow.parquet as pq
run = sys.argv[1]
agents = json.load(open(run + '/agents.json', encoding='utf-8')); meta = {a['id']: a for a in agents}
rows = []
for f in sorted(glob.glob(run + '/l3_snapshots*.parquet')):
    d = pq.read_table(f).to_pydict(); rows += list(zip(d['step'], d['state']))
rows.sort()
c = collections.Counter(); first_last = {}
for step, st in rows:
    o = json.loads(st); ag = o['agents'] if isinstance(o, dict) else o
    for a in ag:
        v = 'V' if meta.get(a['id'], {}).get('visitor') else 'R'
        m = float(a.get('money') or 0); acc = float(a.get('account') or 0)
        c[v + '_n'] += 1
        if m < 2000: c[v + '_cash_lt2000'] += 1
        if m <= 0: c[v + '_cash_0'] += 1
        if m < 2000 and acc >= 20000: c[v + '_cash_lt2000_acct_ge20000'] += 1
        if m + acc < 2000: c[v + '_total_lt2000'] += 1
print('n agents', len(agents), 'visitors', sum(1 for a in agents if a.get('visitor')), 'snapshots', len(rows), 'steps', rows[0][0], rows[-1][0])
for v in 'RV':
    n = c[v + '_n']
    if n:
        print(v, 'agent-snapshots', n, {k[2:]: '%d (%.1f%%)' % (c[k], 100 * c[k] / n) for k in c if k.startswith(v + '_') and k != v + '_n'})
