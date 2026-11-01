"""engine.systems.day — 日の境目の系 day_head(D1)と day_close(D2)(第 1 期 1-0・段 F)。

中身は HEAD ``ee3abc7`` の ``run_day`` の同じ区間(ループの頭の「日の頭」とループの終わりの「途中の日の締め」)のまま。
立つ条件(進行役が見る): day_head は ``td == 0 and T > 0``・day_close は ``td == tpd - 1 and T != total_ticks - 1``
(HEAD の if の条件と同じ)。最後の日の締めは ``run_end.sys_close_final``(鉄道の最後の便を流す形=草案 §3-3 の 14)。

逐次ループ宣言: なし(日に 1 回)。
"""

from __future__ import annotations

from typing import Any

from shibuya.engine.systems import state_io as SIO

__all__ = ["sys_day_head", "sys_day_close", "day_head_due", "day_close_due"]


def day_head_due(T: int, td: int) -> bool:
    """10d: 日の頭(1 日目から)=表の張り直しと今日の計画の写し(初期化はしない)。HEAD の ``if td == 0 and tick > 0``。"""
    return td == 0 and T > 0


def day_close_due(T: int, td: int, tpd: int, total_ticks: int) -> bool:
    """10d: 複数日のランの途中の日の締め(1 日 1 回)。HEAD の ``if td == tpd - 1 and tick != total_ticks - 1``。"""
    return td == tpd - 1 and T != total_ticks - 1


def sys_day_head(ctx: Any, b: Any) -> None:
    """D1(HEAD run.py:3607-3609): 表の張り直し(``relay_tables``)と今日の計画の写し(``start_day``)。"""
    tick, tpd = ctx.T, b.cfg.tpd
    SIO.relay_tables(b, tick // tpd)
    SIO.start_day(b, tick // tpd)


def sys_day_close(ctx: Any, b: Any) -> None:
    """D2(HEAD run.py:4497-4500): 途中の日の締め(鉄道の最後の便は流さない)と、その後の状態の書き出し。"""
    tick, tpd, state_out = ctx.T, b.cfg.tpd, b.cfg.state_out
    SIO.close_day_midrun(b, tick // tpd)
    if state_out is not None:
        SIO.save_state(b, tick + 1, finished=False, closed=True)
