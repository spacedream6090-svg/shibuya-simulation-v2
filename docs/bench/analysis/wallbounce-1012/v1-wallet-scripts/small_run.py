import sys, glob, json, collections
import pyarrow.parquet as pq
run = sys.argv[1]; per = int(sys.argv[2]) if len(sys.argv) > 2 else 1440
agents = json.load(open(run + '/agents.json', encoding='utf-8'))
meta = {a['id']: a for a in agents}
print('n agents', len(agents), 'visitors', sum(1 for a in agents if a.get('visitor')))
files = sorted(glob.glob(run + '/l3_snapshots*.parquet'))
rows = []
for f in files:
    d = pq.read_table(f).to_pydict()
    rows += list(zip(d['step'], d['state']))
rows.sort()
print('l3 rows', len(rows), 'steps', rows[0][0], '...', rows[-1][0])
def show(step, st):
    o = json.loads(st); ag = o['agents'] if isinstance(o, dict) else o
    s = []
    for a in ag:
        m = meta.get(a['id'], {})
        s.append('%d%s:%s/%s' % (a['id'], 'V' if m.get('visitor') else 'R', int(a.get('money') or 0), int(a.get('account') or 0)))
    return s
if len(agents) <= 10:
    for a in agents:
        print(a['id'], 'visitor' if a.get('visitor') else 'resident', a.get('occupation') is not None, 'money0', a.get('money'), 'wage', a.get('wage'))
    for step, st in rows:
        if step % per == 0 or step == rows[-1][0]:
            print(step, show(step, st))
cnt = collections.Counter(); src = collections.Counter(); cat = collections.defaultdict(float); wto = collections.Counter(); wsum = collections.defaultdict(float)
spend_by = collections.defaultdict(float); wage_by = collections.defaultdict(float); wd_by = collections.Counter()
for f in sorted(glob.glob(run + '/l1_events*.parquet')):
    t = pq.read_table(f, columns=['step', 'agent_id', 'kind', 'payload']).to_pydict()
    for step, aid, k, pl in zip(t['step'], t['agent_id'], t['kind'], t['payload']):
        if k not in ('spend', 'wage', 'withdraw', 'rent', 'tax', 'eviction', 'bankruptcy', 'rent_arrears'):
            continue
        cnt[k] += 1
        p = json.loads(pl) if pl else {}
        if k == 'spend':
            src[p.get('src')] += 1; cat[p.get('cat')] += float(p.get('amount', 0)); spend_by[aid] += float(p.get('paid', p.get('amount', 0)))
        elif k == 'wage':
            wto[(p.get('to'), p.get('source'))] += 1; wage_by[aid] += float(p.get('amount', 0))
        elif k == 'withdraw':
            wd_by[aid] += 1
print('counts', dict(cnt)); print('spend src', dict(src)); print('spend by cat', {k: round(v) for k, v in cat.items()})
print('wage (to,source)', dict(wto))
if len(agents) <= 100:
    vs = [a for a in meta if meta[a].get('visitor')]; rs = [a for a in meta if not meta[a].get('visitor')]
    print('visitors: spend total', round(sum(spend_by[a] for a in vs)), 'wage total', round(sum(wage_by[a] for a in vs)), 'withdraw', sum(wd_by[a] for a in vs))
    print('residents: spend total', round(sum(spend_by[a] for a in rs)), 'wage total', round(sum(wage_by[a] for a in rs)), 'withdraw', sum(wd_by[a] for a in rs))
    if len(agents) <= 10:
        for a in meta:
            print(a, 'spend', round(spend_by[a]), 'wage', round(wage_by[a]), 'withdraw', wd_by[a])
