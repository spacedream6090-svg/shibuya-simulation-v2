"""R-130 (a) §4: W17 の在圏ブロックの境目・圏内への出入りの数を時間帯ごとに数える(読むだけ・リポの根で実行)。"""
import json
import numpy as np, pyarrow.parquet as pq
t = pq.read_table('data/world/v2/w17_schedule.parquet').to_pydict()
a = np.asarray(t['agent_id']); d = np.asarray(t['day']); s = np.asarray(t['seq']); st = np.asarray(t['start_min'])
cell = np.asarray(t['target_cell'])
out = {'rows': int(a.size), 'days': sorted(set(d.tolist()))}
for day in sorted(set(d.tolist()))[:2]:
    m = d == day
    aa, ss, stt, cc = a[m], s[m], st[m], cell[m]
    o = np.lexsort((ss, aa)); aa, ss, stt, cc = aa[o], ss[o], stt[o], cc[o]
    agents = np.unique(aa)
    same = aa[1:] == aa[:-1]
    # 境目=同じ体の次のブロックの始まり
    bstart = stt[1:][same]
    inside_prev = cc[:-1][same] >= 0
    inside_next = cc[1:][same] >= 0
    arr = bstart[(~inside_prev) & inside_next]
    dep = bstart[inside_prev & (~inside_next)]
    move_in = bstart[inside_prev & inside_next & (cc[1:][same] != cc[:-1][same])]
    h = lambda x: np.bincount((np.asarray(x, int) // 60) % 24, minlength=24).tolist()
    out[f'day{day}'] = {'agents': int(agents.size), 'blocks': int(m.sum()), 'boundaries': int(bstart.size),
                        'boundaries_by_hour': h(bstart), 'enter_area': int(arr.size), 'enter_by_hour': h(arr),
                        'leave_area': int(dep.size), 'leave_by_hour': h(dep), 'inside_cell_change': int(move_in.size),
                        'inside_change_by_hour': h(move_in)}
print(json.dumps(out))
