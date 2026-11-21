"""R-130 (a) §4: W7 の営業時間の開店と閉店の数を時間帯ごとに数える(読むだけ・リポの根で実行)。"""
import json, sys
import numpy as np, pyarrow.parquet as pq
t = pq.read_table('data/world/v2/w7_plan_spec.parquet', columns=['poi_id','content','src']).to_pydict()
res = {}
for day, name in ((0, 'monday'), (5, 'saturday')):
    opens = np.zeros(24, int); closes = np.zeros(24, int); always = 0; closed_all = 0
    for c in t['content']:
        segs = json.loads(c)[day]
        m = np.zeros(1440, bool)
        for s, e in segs:
            s = max(0, int(s)); e = int(e)
            if e <= 1440: m[s:e] = True
            else:
                m[s:1440] = True; m[0:min(1440, e - 1440)] = True
        if m.all(): always += 1; continue
        if not m.any(): closed_all += 1; continue
        prev = np.roll(m, 1)
        for mm in np.flatnonzero(m & ~prev): opens[mm // 60] += 1
        for mm in np.flatnonzero(~m & prev): closes[mm // 60] += 1
    res[name] = {'pois': len(t['content']), 'always_open': always, 'closed_all_day': closed_all,
                 'opens': int(opens.sum()), 'closes': int(closes.sum()),
                 'opens_by_hour': opens.tolist(), 'closes_by_hour': closes.tolist()}
print(json.dumps(res, ensure_ascii=False))
