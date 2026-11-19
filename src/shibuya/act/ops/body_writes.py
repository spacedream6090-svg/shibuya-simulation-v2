"""act.ops.body_writes — 割る段で ``engine/resolve.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/apply.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Any
import numpy as np
from shibuya.world.model.agent_table import (
    AgentState,
)
from shibuya.world.body import rules as _BODY
from shibuya.world.body.energy import INTAKE_DRINK, INTAKE_SNACK, EnergyModel
from shibuya.foundation.time_consts import MINUTES_PER_DAY

__all__ = [
    "initialize_energy", "energy_out_of_area_meal", "advance_body",
]


# ---------------------------------------------------------------- 身体の自然変動
def advance_body(agents: AgentState, tick: int, energy: Any = None, body: Any = None) -> None:
    """内受容 3 変数の自然変動(**C4 の世界過程が入るまでの駆動源**・expedient)。

    〔第 3 期 3-5〕値は本人の体の層が返す: ``body``(``engine.body.BodyModel``)を渡したランは ``body.step("interoception",
    …)``(腕 sweep=全員を見る・腕 reserve=TM5 の予約の来た体と入力の変わった体だけ)、渡さない呼び手は同じ値の
    ``engine.body.rules.interoception``(全員を見る版)。ここは返った値を書くだけ(式・値・型は下の段落のまま=前と同じ)。

    **二層の段 2(第275 親の決め #1)**: ``activity_columns`` のランでは、活動の種別が
    在店/その場 で持続中(``activity_until > tick``)・移動/乗車/就寝中でない体の疲労を
    ``ACTIVITY_REST_PERIOD_TICKS`` ごとに ``ACTIVITY_REST_FATIGUE_RELIEF`` 下げる
    (旧 休憩 の即時回復を時間経過の規則へ寄せた)。自然変動の**後**に掛ける。

    **5 段目 5a(D-118 K1 (c)・K2・K8)**: ``energy``(``engine.energy.EnergyLayer``)を渡したランは
    空腹の +1/30 分を止め、**毎 tick** ``since_meal_kcal += 消費``・``energy_balance −= 消費``
    (消費=EER/1440 × 分 × METs(活動)/AVG_METS)として ``hunger`` を語の段の写し
    (満腹 1 / ふつう 5 / 空腹 8 / とても空腹 10)に書き直す。疲労・休息の規則は変えない。
    ``None``(既定)は従来と 1 バイトも変わらない。
    """
    ac = bool(getattr(agents, "activity_columns", False))
    if body is not None:
        upd = body.step("interoception", agents.registry, int(tick), energy=energy, activity_columns=ac)
    else:
        upd = _BODY.interoception(agents.registry, int(tick), energy=energy, activity_columns=ac)
    if upd is None:
        return
    with agents.writable():
        r = agents.registry
        if upd.fatigue is not None:
            if upd.fatigue_ids is None:
                r.fatigue[:] = upd.fatigue
            else:
                r.fatigue[upd.fatigue_ids] = upd.fatigue
        if upd.hunger is not None:
            if upd.hunger_ids is None:
                r.hunger[:] = upd.hunger
            else:
                r.hunger[upd.hunger_ids] = upd.hunger
        if upd.spent is not None:
            r.since_meal_kcal[:] = upd.since_meal  # = 前の値 + 消費(float32 の足し算 1 回=前の ``+=`` と同じ値)
            r.energy_balance -= upd.spent


# ---------------------------------------------------------------- 5 段目 5a エネルギー収支
def initialize_energy(agents: AgentState, energy: Any, seed: int | str, body: Any = None) -> None:
    """体の定数(体重・EER)を抽選し、食後の消費・収支・``hunger`` の写しと段を置く(ラン開始時 1 回)。

    ``initialize`` の直後・``freeze`` の前に呼ぶ(``energy_columns`` のランだけ)。``hunger_stage``
    (変化検出の前回段)も写しから組み直す=tick 0 に偽の跨ぎを出さない。

    〔第 3 期 3-5〕食後の消費の初期値・空腹の写しと段(D18)は本人の体の層の口 ``BodyModel.initial(energy=…)``(``body`` を
    渡さない呼び手は同じ値の ``engine.body.rules.initial_energy_values``)が返し、ここは書くだけ(値は前と同じ)。
    """
    model: EnergyModel = energy.model
    r = agents.registry
    with agents.writable():
        weight, eer = model.draw_bodies(r.age, r.sex, seed)  # 10e(E4・K19): 鍵の並べ方
        r.weight_kg[:] = weight
        r.eer_kcal[:] = eer
        init = (body.initial(energy=energy, eer=eer) if body is not None
                else _BODY.initial_energy_values(energy, eer))
        r.since_meal_kcal[:] = init.since_meal
        r.energy_balance[:] = 0.0
        r.hunger[:] = init.hunger
        r.hunger_stage[:] = init.stages["hunger_stage"]
    if model.rate == "bmr":
        energy.bmr = model.bmr_kcal(r.age, r.sex, r.weight_kg).astype(np.float32)


def _tick_minute(energy: Any, tick: int) -> int:
    return int(int(tick) * float(energy.model.minutes_per_tick)) % MINUTES_PER_DAY


def _energy_meal(
    r, ids: np.ndarray, tick: int, energy: Any, *, kind: str,
    slots: np.ndarray | None = None, from_row: np.ndarray | None = None,
    deferred: np.ndarray | None = None,
) -> None:
    """食事の摂取(K7 (a)): 時間帯の比 × EER を収支へ・``since_meal=0``・写しを満腹へ。"""
    ids = np.asarray(ids, dtype=np.int64)
    if ids.size == 0:
        return
    model: EnergyModel = energy.model
    minute = _tick_minute(energy, tick)
    if slots is None:
        share = model.meal_share_of(r.age[ids], r.sex[ids], minute)
    else:
        share = model.meal_share_for_slot(r.age[ids], r.sex[ids], slots)
    kcal = (share * r.eer_kcal[ids].astype(np.float64)).astype(np.float32)
    r.since_meal_kcal[ids] = 0.0
    if getattr(energy, "meal_reset", None) is not None:  # 第2波 §2B Q-2B-6 (ii): 食事で per_hour の門の H を 0 に
        energy.meal_reset[ids] = 0.0
    r.energy_balance[ids] += kcal
    r.hunger[ids] = model.hunger_copy(model.stage_of(r.since_meal_kcal[ids], r.eer_kcal[ids]))
    if deferred is None:
        energy.note(kind, ids, minute, float(kcal.astype(np.float64).sum()), slots=slots,
                    from_row=from_row)
    else:
        energy.note(kind, ids, minute, float(kcal.astype(np.float64).sum()), slots=slots,
                    from_row=from_row, deferred=deferred)


def _energy_snack(r, buyers: np.ndarray, bought: np.ndarray, tick: int, energy: Any) -> None:
    """飲食系の購入の摂取(K3 (a)): 軽食=第13表「間」の比・飲料=``DRINK_SHARE``(× EER)。"""
    from shibuya.world.body.energy import DRINK_SHARE

    buyers = np.asarray(buyers, dtype=np.int64)
    bought = np.asarray(bought, dtype=np.int64)
    if buyers.size == 0 or energy.poi_intake.size == 0:
        return
    model: EnergyModel = energy.model
    kind = energy.poi_intake[np.clip(bought, 0, energy.poi_intake.size - 1)]
    minute = _tick_minute(energy, tick)
    for code, label in ((INTAKE_SNACK, "snack"), (INTAKE_DRINK, "drink")):  # 2 種ぶん
        ids = buyers[kind == code]
        if ids.size == 0:
            continue
        if code == INTAKE_SNACK:
            share = model.snack_share_of(r.age[ids], r.sex[ids])
        else:
            share = np.full(ids.size, DRINK_SHARE, dtype=np.float64)
        kcal = (share * r.eer_kcal[ids].astype(np.float64)).astype(np.float32)
        r.since_meal_kcal[ids] = np.maximum(r.since_meal_kcal[ids] - kcal, np.float32(0.0))
        r.energy_balance[ids] += kcal
        r.hunger[ids] = model.hunger_copy(
            model.stage_of(r.since_meal_kcal[ids], r.eer_kcal[ids])
        )
        energy.note(label, ids, minute, float(kcal.astype(np.float64).sum()))


def energy_out_of_area_meal(
    agents: AgentState, energy: Any, agent_id: np.ndarray, slots: np.ndarray,
    from_row: np.ndarray, tick: int, deferred: np.ndarray | None = None,
) -> int:
    """範囲外の食事(K9 (a)): 域外に居る体の予定の食事=時間帯の比 × EER・``since_meal=0``。

    値(誰がいつ)は ``engine.energy.OutOfAreaMeals.due`` が決める。件数を返す。
    ``deferred``(第2波 §2B 項 1)=起床時に遅らせた既定の食事の印(診断の内数だけ・摂取は同じ式)。
    """
    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return 0
    with agents.writable():
        _energy_meal(agents.registry, a, tick, energy, kind="meal_out",
                     slots=np.asarray(slots, dtype=np.int64), from_row=from_row,
                     deferred=deferred)
    return int(a.size)


def energy_home_meal(
    agents: AgentState, energy: Any, agent_id: np.ndarray, slots: np.ndarray, tick: int,
) -> int:
    """**第2波 §2B 項 2(Q35 (a))** 範囲内の自宅の食事行=予定の実行(``engine.energy.HomeMeals.due``)。

    摂取は K9 と同じ(時間帯の比 × EER・``since_meal=0``・写しを満腹へ)。**金と物は動かさない**
    (台帳・棚・店の席に触らない)。変化検出の前回段 ``hunger_stage`` も新しい段に合わせる=
    この食事そのものは内受容の起床(下げ跨ぎ)を作らない(予定の実行は驚きではない・起床を足さない・宣言)。
    件数を返す。
    """
    from shibuya.foundation.vocab.agent_codes import INTERO_UP_EDGES

    a = np.asarray(agent_id, dtype=np.int64)
    if a.size == 0:
        return 0
    with agents.writable():
        r = agents.registry
        _energy_meal(r, a, tick, energy, kind="meal_home", slots=np.asarray(slots, dtype=np.int64))
        stage = np.zeros(a.size, dtype=np.int8)
        for e in INTERO_UP_EDGES:  # 段の刻み 3 本ぶん(体数には比例しない)
            stage += (r.hunger[a] >= e).astype(np.int8)
        r.hunger_stage[a] = stage
    return int(a.size)
