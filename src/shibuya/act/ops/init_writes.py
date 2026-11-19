"""act.ops.init_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Any
import numpy as np
from shibuya.foundation.vocab.agent_codes import Activity
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.world.body import rules as _BODY
from shibuya.foundation.ports.ledger import LedgerBundle
from shibuya.world.model.state import World

__all__ = [
    "initialize", "set_initial_activity",
]


# ---------------------------------------------------------------- 初期化
def initialize(
    agents: AgentState,
    world: World,
    schedule,
    *,
    day_index: int = 0,
    ledger: LedgerBundle | None = None,
    body: Any = None,
) -> None:
    """個体を自宅セルに置き、所持金・種別・内受容の初期段を設定する(**ランの最初に1回**)。

    ここも書き込みなので resolve に置く(``run.py`` は初期化後に ``freeze()`` する)。

    ``ledger`` を渡した場合、初期財布は**直接代入ではなく外界からの transfer**で入れる
    (境界・経済設計書 §2.3 ex nihilo 禁止)。金額は同じなので状態ハッシュは変わらない。

    〔第 3 期 3-5〕刻み 0 の空腹・疲れ・暑さと段(D18)は本人の体の層の口 ``BodyModel.initial``(``body`` を渡さない
    呼び手は同じ値の ``engine.body.rules.initial_values``)が返し、ここは書くだけ(値は前と同じ)。
    """
    n = agents.n
    init = body.initial(n) if body is not None else _BODY.initial_values(n)
    with agents.writable(), world.writable():
        home = np.asarray(schedule.home_cell, dtype=np.int64)[:n]
        # I6 −1 ガード(D-66): 域外居住者は ``home_cell < 0`` のまま来る(計画実行層が
        # 起動直後に ``place_at_external`` で外へ置く)。**セル表を −1 で索引しない**。
        # 全員が ``home_cell >= 0`` のラン(帰無腕・mock・合成世界)では 1 バイトも変わらない。
        has_home = home >= 0
        safe = np.where(has_home, home, 0)
        agents.registry.cell[:] = np.where(has_home, home, -1)
        node = np.where(has_home, world.assets.cell_rep_node[safe], -1)
        agents.registry.node[:] = node
        agents.registry.band[:] = np.where(has_home, world.assets.cell_band[safe], 0)
        agents.registry.xy[:] = np.where(
            has_home[:, None], world.assets.node_xy[np.maximum(node, 0)], 0.0
        )
        agents.registry.field("kind")[:] = np.asarray(schedule.kind)[:n]
        # W16 母集団を載せたランだけ年齢・性別が入る(mock は既定値 0 / −1 のまま)
        if getattr(schedule, "age", None) is not None:
            agents.registry.field("age")[:] = np.asarray(schedule.age)[:n]
        if getattr(schedule, "sex", None) is not None:
            agents.registry.field("sex")[:] = np.asarray(schedule.sex)[:n]
        money0 = np.asarray(schedule.initial_money, dtype=np.int64)[:n]
        if ledger is not None and ledger.money is not None:
            # 台帳経路: 外界 → 世帯の transfer(来街者持込)で入れる(残高の直接代入をしない)
            agents.registry.money[:] = 0
            ledger.money.endow_households(money0, 0)
        else:
            agents.registry.money[:] = money0
        agents.registry.activity[:] = int(Activity.SLEEPING)
        agents.registry.hunger[:] = init.hunger
        agents.registry.fatigue[:] = init.fatigue
        agents.registry.thermal[:] = init.thermal
        for stage_field in ("hunger_stage", "fatigue_stage", "thermal_stage"):
            agents.registry.field(stage_field)[:] = init.stages[stage_field]
        world.cells.density[:] = world.compute_density(agents.registry.cell)
        world.cells.density_stage[:] = world.density_stage()
        world.cells.open_count[:] = world.open_count_per_cell(0)


def set_initial_activity(agents: AgentState, activity) -> int:
    """tick 0 の ``activity`` を**計画(W17)の 0:00 時点の活動**から立てる(D-62 (b))。

    ``initialize`` は全員を ``SLEEPING`` に置く(週次表を持たない合成世界/mock 日課の
    既定=**従来どおり**)。週次表があるランだけ、この関数で 0:00 の活動から立て直す
    (``agents.weekly.WeeklySchedule.initial_activity``)。

    ``transit_state != 0``(域外滞在・乗車中)の個体は**触らない**——域外居住者は
    ``place_at_external`` が ``WAITING`` を立てており、3 値(乗客の保存則の分母)と
    ``activity`` の整合はそちらが正(D-62 の決定文「rail の事前割当の整合を保つ」)。

    Args:
        activity: 形 ``(n,)`` の ``Activity`` 値(``int8``)。

    Returns:
        実際に書いた体数。
    """
    act = np.asarray(activity, dtype=np.int8).ravel()
    with agents.writable():
        r = agents.registry
        if act.size != r.activity.size:
            raise ValueError(f"初期活動の長さが体数と違う({act.size} != {r.activity.size})")
        free = r.transit_state == 0
        r.activity[free] = act[free]
    return int(np.count_nonzero(free))
