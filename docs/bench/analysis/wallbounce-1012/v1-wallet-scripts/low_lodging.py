import sys, glob, json, collections
import pyarrow.parquet as pq, pyarrow.compute as pc, pyarrow as pa
run = sys.argv[1]
agents = json.load(open(run + '/agents.json', encoding='utf-8')); meta = {a['id']: a for a in agents}
last_cash = {}; last_acct = {}; lodg = collections.Counter(); spend = collections.defaultdict(float); refill = collections.Counter()
first_step_low = {}
for f in sorted(glob.glob(run + '/l1_events*.parquet')):
    t = pq.read_table(f, columns=['step', 'agent_id', 'kind', 'payload'])
    t = t.filter(pc.is_in(t['kind'], value_set=pa.array(['spend', 'wage', 'withdraw']))).to_pydict()
    for s, a, k, pl in zip(t['step'], t['agent_id'], t['kind'], t['payload']):
        p = json.loads(pl)
        if k == 'spend':
            spend[a] += float(p.get('paid', p.get('amount', 0)))
            if p.get('cat') == 'lodging': lodg[a] += 1
        if k == 'wage' and p.get('source') == 'home_refill': refill[a] += 1
        if 'balance' in p and k != 'withdraw': last_cash[a] = float(p['balance'])
        if 'account' in p: last_acct[a] = float(p['account'])
        if k == 'withdraw': last_cash[a] = float(p['cash'])
        if a in last_cash and last_cash[a] + last_acct.get(a, 0) < 2000 and a not in first_step_low and meta.get(a, {}).get('visitor'):
            first_step_low[a] = s
vis = [a for a in last_cash if meta.get(a, {}).get('visitor')]
low = [a for a in vis if last_cash[a] < 2000]
print('visitors with money events', len(vis), 'low(<2000 cash at last obs)', len(low))
print('low with lodging', sum(1 for a in low if lodg[a] > 0), 'low without lodging', sum(1 for a in low if lodg[a] == 0))
print('visitors lodged total', sum(1 for a in vis if lodg[a] > 0), 'of which low', sum(1 for a in vis if lodg[a] > 0 and last_cash[a] < 2000))
nl = [a for a in low if lodg[a] == 0]
print('low w/o lodging: spend total quantiles', sorted(spend[a] for a in nl)[len(nl)//2] if nl else None)
print('low occupations', collections.Counter(meta[a].get('occupation') for a in low).most_common(12))
print('low commute field sample', collections.Counter(str(meta[a].get('commute'))[:30] for a in low).most_common(5))
print('first step became low (visitors) hist by 8-step bins', sorted(collections.Counter(s // 8 * 8 for s in first_step_low.values()).items()))
print('low refilled at least once', sum(1 for a in low if refill[a] > 0))
