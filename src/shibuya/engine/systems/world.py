"""engine.systems.world — 世界の系(world=世界過程 18 本の下位の系を ``runner.step`` で回す)(第 1 期 1-0)。

中身は HEAD ``ee3abc7`` の ``engine/run.py`` の ``run_day`` の同じ区間のまま。系の関数は ``(ctx, b)`` を受け取り、
区間の外から来る名前を箱から結ぶ前置き(局所の割り当ての表 ``local-assignment.json`` と同じ写像)と、
tick の中の受け渡しを ``TickScratch`` へ書く後置きだけを足した(文は変えない・``box.`` は ``b.``)。
``engine.run`` で定義された補助(``_split_due`` など)は呼ぶ時に ``engine.run`` から引く(試験の差し替えが効く)。

逐次ループ宣言: 区間の中の宣言は HEAD のまま(各関数の中の注を見る)。ほかに新しい逐次ループは無い。
"""

from __future__ import annotations

from typing import Any


def sys_world(ctx: Any, b: Any) -> None:
    """world(HEAD run.py の同じ区間・文は変えない)。"""
    runner = b.layers.runner
    tick = ctx.T
    if runner is not None:
        runner.step(tick)
