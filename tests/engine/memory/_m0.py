"""第 1 期 1-6 M0 の試験の共通(腕の切替・合成の世界の小さなランの設定・記憶の表と器の行の突き合わせ)。"""

from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

import numpy as np

from shibuya.engine import memory_store as MS

ROOT = Path(__file__).resolve().parents[3]
WORLD = ROOT / "data" / "world" / "v2"
#: 合成の世界の小さなラン(記憶+関係+同席+店の記憶=1-3 の試験と同じ腕)。
KW = dict(n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0, sleep_suppression=False, vocab_version="v3",
          memory="on", relations="on", rel_copresent="on", store_memory="on", checkpoint_every=60)


@contextmanager
def arm(name: str) -> Iterator[None]:
    """腕を一時的に選ぶ(組み立てが読む)。"""
    prev = MS.arm()
    MS.set_arm(name)
    try:
        yield
    finally:
        MS.set_arm(prev)


def run_with_arm(name: str, fn: Any, **kw: Any) -> Any:
    with arm(name):
        return fn(**kw)


def table_vs_store(agents: Any, layer: Any) -> list[str]:
    """記憶の表(``mem_*``・要旨)と器の行の食い違い(空なら同じ)。M0 の器は表の写し=全部の体・全部の行で同じはず。"""
    ms = layer.memory_store
    r = agents.registry
    n, N = ms.n, ms.n_rows
    ns = ms.ns_per_step
    bad: list[str] = []
    used_t = (r.mem_kind != 0).reshape(-1)
    used_s = ms._ms_origin >= 0
    if not np.array_equal(used_t, used_s):
        bad.append(f"使っている行が違う: 表 {int(used_t.sum())}・器 {int(used_s.sum())}")
        return bad
    g = np.flatnonzero(used_t)
    pairs = (
        ("kind", r.mem_kind, ms._lg_kind), ("partner", r.mem_partner, ms._lg_partner),
        ("object", r.mem_object, ms._lg_object), ("result", r.mem_result, ms._lg_result),
        ("cell", r.mem_cell, ms._lg_cell), ("n", r.mem_n, ms._ms_n), ("importance", r.mem_importance, ms._ms_imp),
    )
    for name, t, s in pairs:
        if not np.array_equal(np.asarray(t).reshape(-1)[g].astype(np.int64), s[g].astype(np.int64)):
            bad.append(name)
    if not np.array_equal(np.asarray(r.mem_tick).reshape(-1)[g].astype(np.int64) * ns, ms._ms_first_ns[g]):
        bad.append("first")
    if not np.array_equal(np.asarray(r.mem_last).reshape(-1)[g].astype(np.int64) * ns, ms._ms_ev_t_ns[g]):
        bad.append("last=目印の時刻")
    # 〔第 2 期 2-3〕腕のランで記録があれば目印は記録の出来事(出どころ None=0・seq=記録の seq=行 M0L)・無ければ仮の行
    log = ms._ms_origin[g] == 0
    want = np.where(log, ms._ms_log_seq[g].astype(np.int64), -1 - g)
    if not np.array_equal(ms._ms_ev_seq[g].astype(np.int64), want):
        bad.append("目印の seq(仮の出来事の番地・記録の seq)")
    if (not np.isin(ms._ms_origin[g], (0, 1)).all() or (ms._ms_log_seq[g][log] < 0).any()
            or (ms._ms_log_seq[g][~log] != -1).any()):
        bad.append("出どころ(legacy か記録の出来事)")
    notes = {(int(k) // N, int(k) % N): v for k, v in ms._ms_note.items()}
    if notes != dict(layer.gist):
        bad.append("注釈と要旨")
    order_t = {a: list(od) for a, od in layer._gist_order.items() if od}
    order_s = {a: list(od) for a, od in ms._ms_note_order.items() if od}
    if order_t != order_s:
        bad.append("注釈の順")
    assert n * N == ms._ms_origin.size
    return bad
