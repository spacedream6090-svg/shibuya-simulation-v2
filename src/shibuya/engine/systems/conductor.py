"""engine.systems.conductor — 系を呼ぶ進行役(第 1 期 1-0・草案 §2-4)。

``run_system(spec, ctx, box)`` が 1 つの系を包む: 試験の境目(``probe.at``=系ごとの全欄の差と指紋)・書きの許可
(``guard.system_scope``=SoA は ``writes.soa``・scratch は ``writes.scratch``)・系ごとの壁時計(``RunStats.system_seconds``。
``phase`` の鍵の集合は変えない=草案 §3-3 の 22)。

逐次ループ宣言: なし(系 1 回あたり定数回)。
"""

from __future__ import annotations

import os
import time
from typing import Any

from shibuya.engine.systems import guard as _G
from shibuya.engine.systems import probe as _PR
from shibuya.engine.systems.spec import SystemSpec, path_allowed

__all__ = ["run_system", "declared_check"]


def run_system(spec: SystemSpec, ctx: Any, box: Any) -> Any:
    """系 ``spec`` を 1 回呼ぶ(``ctx`` はその刻みの ``TickCtx``・ランの単位の系は ``None``)。"""
    _PR.at(spec.name, None if ctx is None else ctx.T, box)
    t0 = time.perf_counter()
    with _G.system_scope(spec.name, spec.writes.soa, spec.writes.scratch, spec.writes.buffers):
        out = spec.fn(ctx, box)
    ss = box.runstats.system_seconds
    ss[spec.name] = ss.get(spec.name, 0.0) + (time.perf_counter() - t0)
    return out


def declared_check(specs: dict[str, SystemSpec]):
    """段 B(試験のとき): 系の前後で変わった欄 ⊆ 宣言の書く欄、を見る関数(``probe.Probe.check`` に渡す)。

    欄の鍵の族: SoA ``agents.cell`` → ``writes.soa``・外の道筋 ``O39:conv.sessions`` → ``writes.paths``(前方一致の ``*``)・
    ``stats.<名>`` → ``writes.tally``・``buffers.<名>`` → ``writes.buffers``。宣言の無い系の名(``build`` など)は通す。
    """

    def check(name: str, key: str) -> bool:
        sp = specs.get(name)
        if sp is None:
            return True
        w = sp.writes
        if key.startswith("stats."):
            return key[6:] in w.tally
        if key.startswith("buffers."):
            return key[8:] in w.buffers
        if key.startswith("scratch."):
            return key[8:] in w.scratch
        if ":" in key:
            return path_allowed(key, w.paths)
        return key in w.soa

    return check


#: 刻みの頭の境目の名(系ではない=宣言を持たない。scratch を空にする差の帰属先)。
TICK_HEAD = "(tick_head)"

#: 試験(T4)のとき真: 刻みの頭で scratch を番兵で埋め、その刻みに書かれる前に読むと落とす。
STRICT_SCRATCH: bool = False

#: 立つ条件(``SystemSpec.when``)の名 → 箱を見る述語(組み立ての後は変わらない=ランの頭で 1 回だけ見る)。
WHEN = {
    "": lambda b: True,
    "presence": lambda b: b.layers.presence is not None,
    "rel_layer": lambda b: b.layers.rel_layer is not None,
    "conv": lambda b: b.layers.conv is not None,
    "act_layer": lambda b: b.layers.act_layer is not None,
    "fam_layer": lambda b: b.layers.fam_layer is not None,
    "energy": lambda b: b.layers.energy is not None,
    "home_meals": lambda b: b.layers.energy is not None and b.layers.energy.home_meals is not None,
}


def tick_plan(box: Any, specs: tuple[SystemSpec, ...]) -> list[SystemSpec]:
    """刻みの中で呼ぶ系の並び(表の順・立たない系を外す・``llm_receive`` の位置を応答の遅れで選ぶ=草案 §2-2)。"""
    plan = [s for s in specs if s.timing == "tick" and WHEN[s.when](box)]
    if int(box.cfg.response_delay) == 2:  # 位置 B(旧): wake_sources の後
        rec = next(s for s in plan if s.name == "llm_receive")
        plan.remove(rec)
        plan.insert(next(k for k, s in enumerate(plan) if s.name == "wake_sources") + 1, rec)
    return plan


def conduct(call_args: dict) -> Any:
    """``run_day`` の本体: 組み立て(R1)→ 刻みのループ(日の頭 D1・刻みの系・日の終わり D2)→ ランの終わり(R2・締め・R3)。

    逐次ループ宣言1: 刻みの数ぶん(10a: ``T`` は通しの時刻・``td`` はその日の中の刻み)。1 刻みの中身は系の並び。
    """
    from shibuya.engine.systems import boxes as _BX
    from shibuya.engine.systems import build as _BLD
    from shibuya.engine.systems import day as _DAY
    from shibuya.engine.systems.table import SPECS, SYSTEMS

    check = os.environ.get("SHIBUYA_SYSTEMS_CHECK", "").strip()  # 試験(T5): 既存の試験の上で段 B と番兵を回す口
    if check and _PR.ACTIVE is None:
        return _conduct_checked(call_args, check)
    t0 = time.perf_counter()
    box = _BLD.build(call_args)
    box.runstats.system_seconds["build"] = time.perf_counter() - t0
    if STRICT_SCRATCH:
        box.scratch = _BX.TickScratchStrict()
    unset = _BX.UNSET if STRICT_SCRATCH else None
    cfg = box.cfg
    tpd, total = int(cfg.tpd), int(cfg.total_ticks)
    step_s = int(cfg.tick_seconds)  # 1-1 T0: 刻みの幅[秒](``TickCtx`` の ``t_ns``・``tod_s`` の換算)
    plan = tick_plan(box, SYSTEMS)
    s_head, s_close = SPECS["day_head"], SPECS["day_close"]
    for T in range(cfg.t_begin, cfg.t_end):
        ctx = _BX.TickCtx.of(T, tpd, step_s)
        _PR.at(TICK_HEAD, T, box)  # 試験だけ: scratch を空にした差を前の系に帰属させない境目(既定のランでは何もしない)
        box.scratch.reset(unset)  # 刻みの中の受け渡しは刻みの頭で空にする(Buffers は空にしない=R1)
        if _DAY.day_head_due(T, ctx.td):
            run_system(s_head, ctx, box)
        for spec in plan:
            run_system(spec, ctx, box)
        if _DAY.day_close_due(T, ctx.td, tpd, total):
            run_system(s_close, ctx, box)
    run_system(SPECS["drain"], None, box)
    run_system(SPECS["close_final"], None, box)
    result = run_system(SPECS["report"], None, box)
    _PR.at("END", None, box)
    return result


def _conduct_checked(call_args: dict, every: str) -> Any:
    """``SHIBUYA_SYSTEMS_CHECK=<間引き>`` のとき(試験だけ・T5): 段 B(系の前後で変わった欄 ⊆ 宣言)と番兵の scratch(T4)を
    入れて回し、宣言の外の変化があれば ``AssertionError``。``<間引き>`` は snapshot を取る刻みの間隔(``1``=全部)。"""
    global STRICT_SCRATCH
    from shibuya.engine.systems.table import SPECS

    k = max(1, int(every)) if every.isdigit() else 1
    T_max = 10 ** 8
    pr = _PR.Probe(check=declared_check(SPECS), ticks=frozenset(range(0, T_max, k)) if k > 1 else None,
                   families=("soa", "ext", "stats", "buffers", "scratch"))  # 段 FIX: scratch の中身も
    prev_strict = STRICT_SCRATCH
    _PR.ACTIVE, STRICT_SCRATCH = pr, True
    try:
        out = conduct(call_args)
    finally:
        _PR.ACTIVE, STRICT_SCRATCH = None, prev_strict
    if pr.violations:
        raise AssertionError(f"1-0 段 B: 宣言の外の変化 {len(pr.violations)} 件(先頭 {pr.violations[:5]})")
    return out
