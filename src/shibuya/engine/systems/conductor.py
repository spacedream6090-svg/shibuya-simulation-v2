"""engine.systems.conductor — 系を呼ぶ進行役(第 1 期 1-0・草案 §2-4)。

``run_system(spec, ctx, box)`` が 1 つの系を包む: 試験の境目(``probe.at``=系ごとの全欄の差と指紋)・書きの許可
(``guard.system_scope``=SoA は ``writes.soa``・scratch は ``writes.scratch``)・系ごとの壁時計(``RunStats.system_seconds``。
``phase`` の鍵の集合は変えない=草案 §3-3 の 22)。

逐次ループ宣言: なし(系 1 回あたり定数回)。
"""

from __future__ import annotations

import time
from typing import Any

from shibuya.engine.systems import guard as _G
from shibuya.engine.systems import probe as _PR
from shibuya.engine.systems.spec import SystemSpec, path_allowed

__all__ = ["run_system", "declared_check"]


def run_system(spec: SystemSpec, ctx: Any, box: Any) -> Any:
    """系 ``spec`` を 1 回呼ぶ(``ctx`` はその tick の ``TickCtx``・ランの単位の系は ``None``)。"""
    _PR.at(spec.name, None if ctx is None else ctx.T, box)
    t0 = time.perf_counter()
    with _G.system_scope(spec.name, spec.writes.soa, spec.writes.scratch):
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

