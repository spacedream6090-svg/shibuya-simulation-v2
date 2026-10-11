import sys, glob, json, collections, statistics
import pyarrow.parquet as pq, pyarrow.compute as pc, pyarrow as pa
run = sys.argv[1]
KINDS = ['spend', 'wage', 'withdraw', 'tax', 'interest_paid', 'medical_bill', 'donation', 'lost_return', 'lost_keep']
agents = json.load(open(run + '/agents.json', encoding='utf-8'))
meta = {a['id']: a for a in agents}
init_money = {a['id']: float(a.get('money') or 0) for a in agents}
print('agents.json n', len(agents), 'visitors', sum(1 for a in agents if a.get('visitor')))
# L3 step0
t = pq.read_table(run + '/l3_snapshots.part-0000.parquet')
st = json.loads(t.to_pydict()['state'][0])['agents']
s0 = {a['id']: (float(a.get('money') or 0), float(a.get('account') or 0)) for a in st}
print('L3 step0 n', len(s0))
def q(v):
    v = sorted(v)
    if not v: return None
    n = len(v)
    return {'n': n, 'p10': v[n//10], 'p25': v[n//4], 'med': v[n//2], 'p75': v[3*n//4], 'p90': v[9*n//10], 'mean': round(sum(v)/n, 1), 'lt2000': sum(1 for x in v if x < 2000), 'eq0': sum(1 for x in v if x <= 0)}
vis = lambda i: bool(meta.get(i, {}).get('visitor'))
print('step0 cash all', q([m for m, a in s0.values()]))
print('step0 cash+acct visitor', q([m + a for i, (m, a) in s0.items() if vis(i)]))
print('step0 cash+acct nonvisitor', q([m + a for i, (m, a) in s0.items() if not vis(i)]))
print('step0 acct nonvisitor', q([a for i, (m, a) in s0.items() if not vis(i)]))
spend_cat = collections.defaultdict(lambda: [0, 0.0]); src = collections.Counter(); clip_n = 0; clip_short = 0.0
zero_after = 0; wage_to = collections.Counter(); wage_src = collections.Counter(); wage_sum = 0.0
wage_agents = set(); withdraw = []; last_cash = {}; last_acct = {}; spend_by_agent = collections.defaultdict(float)
spend_n_vis = collections.Counter(); tax_sum = collections.Counter(); kind_n = collections.Counter()
for f in sorted(glob.glob(run + '/l1_events*.parquet')):
    t = pq.read_table(f, columns=['step', 'agent_id', 'kind', 'payload'])
    mask = pc.is_in(t['kind'], value_set=pa.array(KINDS))
    t = t.filter(mask).to_pydict()
    for step, aid, kind, pl in zip(t['step'], t['agent_id'], t['kind'], t['payload']):
        kind_n[kind] += 1
        try:
            p = json.loads(pl) if pl else {}
        except Exception:
            p = {}
        if kind == 'spend':
            amt = float(p.get('amount', 0)); c = p.get('cat')
            spend_cat[c][0] += 1; spend_cat[c][1] += amt
            src[p.get('src')] += 1
            spend_by_agent[aid] += float(p.get('paid', amt))
            spend_n_vis['visitor' if vis(aid) else 'non'] += 1
            if 'paid' in p:
                clip_n += 1; clip_short += amt - float(p['paid'])
            if float(p.get('balance', 1)) <= 0:
                zero_after += 1
            if 'balance' in p: last_cash[aid] = float(p['balance'])
            if 'account' in p: last_acct[aid] = float(p['account'])
        elif kind == 'wage':
            wage_to[p.get('to')] += 1; wage_src[p.get('source')] += 1
            wage_sum += float(p.get('amount', 0)); wage_agents.add(aid)
            if 'balance' in p: last_cash[aid] = float(p['balance'])
            if 'account' in p: last_acct[aid] = float(p['account'])
        elif kind == 'withdraw':
            withdraw.append((step, aid, p))
        elif kind == 'tax':
            tax_sum[p.get('tax') or p.get('kind') or p.get('type')] += float(p.get('amount', 0))
print('kind counts', dict(kind_n))
print('spend by cat (n, sum)', {k: (v[0], round(v[1])) for k, v in sorted(spend_cat.items(), key=lambda x: -x[1][1])})
print('spend src', dict(src), 'spend n by visitor', dict(spend_n_vis))
print('spend with paid<amount (clipped)', clip_n, 'shortfall sum', round(clip_short))
print('spend leaving cash balance<=0', zero_after)
print('wage to', dict(wage_to), 'source', dict(wage_src), 'sum', round(wage_sum), 'agents', len(wage_agents), 'visitor recipients', sum(1 for a in wage_agents if vis(a)))
print('withdraw', withdraw)
print('tax', {k: round(v) for k, v in tax_sum.items()})
sp = list(spend_by_agent.values())
print('spend per spending agent (paid)', q(sp), 'total', round(sum(sp)))
# last observed cash among agents with money events
lc_v = [v for a, v in last_cash.items() if vis(a)]; lc_n = [v for a, v in last_cash.items() if not vis(a)]
print('last observed cash visitor', q(lc_v)); print('last observed cash nonvisitor', q(lc_n))
both = [last_cash[a] + last_acct.get(a, s0.get(a, (0, 0))[1]) for a in last_cash if not vis(a)]
print('last observed cash+acct nonvisitor', q(both))
# who is below 2000 at last observation: occupation breakdown
low = [a for a in last_cash if last_cash[a] + last_acct.get(a, s0.get(a, (0, 0))[1] if not vis(a) else 0) < 2000]
occ = collections.Counter(meta.get(a, {}).get('occupation') for a in low)
print('n low(<2000 cash+acct at last obs)', len(low), 'visitor share', sum(1 for a in low if vis(a)))
print('low occupations top', occ.most_common(15))
# for low: initial money, spend total
iv = [s0.get(a, (init_money.get(a, 0), 0))[0] + s0.get(a, (0, 0))[1] for a in low if a in s0]
print('low: step0 cash+acct', q(iv))
print('low: spend total', q([spend_by_agent[a] for a in low]))
