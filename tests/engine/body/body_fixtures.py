"""第 3 期 3-5 の試験の共通の道具: 3-5 より前の式の写し(移しただけ=同じ値の物差し)・作り物の体の表・作り物のエネルギー。

``head_*`` は HEAD ``d35a9b6`` の ``engine/resolve.py`` の ``advance_body``・``initialize``・``initialize_energy``・
``engine/processes/environment.py`` の ``EnvironmentProcess.step``・``engine/processes/salient.py`` の ``_collapse_events`` の
式を、SoA の代わりに配列で書き直した物(式・型・順は変えていない)。体の層の口がこれと同じ値を返すことを見る。

作り物のエネルギー(:func:`stub_energy`)は錨を読まない(METs の 4 値と消費の式を手で置く)=``EnergyModel`` の語の段の
2 つの静的な関数(``stage_of``・``hunger_copy``)はそのまま使う。
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np

from shibuya.agents.state import Activity, ActivityKind
from shibuya.core.time_consts import MINUTES_PER_DAY, SECONDS_PER_DAY
from shibuya.engine.change_detect import INTERO_UP_EDGES
from shibuya.engine.energy import AVG_METS, EnergyModel

HEAD = "d35a9b6"


# ================================================================= 作り物のエネルギー(錨を読まない)
class StubModel:
    """``EnergyModel`` の 4 つの口だけ(METs と消費の式は energy.py と同じ形・METs の値は改訂版メッツ表の 4 値)。"""

    stage_of = staticmethod(EnergyModel.stage_of)
    hunger_copy = staticmethod(EnergyModel.hunger_copy)
    mets_sitting, mets_walk_dest, mets_wander, mets_sleep = np.float32(1.3), np.float32(3.5), np.float32(3.0), np.float32(1.0)
    minutes_per_tick = 1.0
    rate = "eer"

    def mets_of(self, activity, transit_state, activity_kind):  # noqa: ANN001, ANN201
        act = np.asarray(activity)
        mets = np.full(act.shape, self.mets_sitting, dtype=np.float32)
        moving = act == int(Activity.MOVING)
        if activity_kind is not None:
            wander = moving & (np.asarray(activity_kind) == int(ActivityKind.WANDER))
            mets[moving] = self.mets_walk_dest
            mets[wander] = self.mets_wander
        else:
            mets[moving] = self.mets_walk_dest
        mets[act == int(Activity.SLEEPING)] = self.mets_sleep
        mets[np.asarray(transit_state) == 2] = AVG_METS
        return mets

    def expenditure(self, eer, mets, bmr=None):  # noqa: ANN001, ANN201
        per_min = float(self.minutes_per_tick) / MINUTES_PER_DAY
        return (np.asarray(eer, dtype=np.float32) * np.float32(per_min / AVG_METS) * mets).astype(np.float32)

    def initial_since_meal(self, eer):  # noqa: ANN001, ANN201
        return (np.asarray(eer, dtype=np.float64) * (MINUTES_PER_DAY - 1158) / MINUTES_PER_DAY).astype(np.float32)


def stub_energy() -> SimpleNamespace:
    return SimpleNamespace(model=StubModel(), bmr=None)


# ================================================================= 作り物の体の表(registry の代わり)
def fake_registry(n: int, rng: np.random.Generator, *, energy: bool, activity_columns: bool) -> SimpleNamespace:
    acts = np.array([int(a) for a in Activity], dtype=np.int8)
    r = SimpleNamespace(
        activity=rng.choice(acts, n).astype(np.int8),
        fatigue=rng.integers(0, 11, n).astype(np.uint8),
        hunger=rng.integers(0, 11, n).astype(np.uint8),
        thermal=rng.integers(0, 11, n).astype(np.uint8),
        transit_state=rng.choice(np.array([0, 0, 0, 1, 2], dtype=np.int8), n),
        cell=rng.integers(-1, 6, n).astype(np.int32),
    )
    if activity_columns:
        r.activity_kind = rng.integers(0, 5, n).astype(np.int8)
        r.activity_until = rng.integers(-1, 200, n).astype(np.int32)
    if energy:
        r.eer_kcal = rng.uniform(900.0, 3200.0, n).astype(np.float32)
        r.since_meal_kcal = rng.uniform(0.0, 1500.0, n).astype(np.float32)
        r.energy_balance = np.zeros(n, dtype=np.float32)
        r.hunger = EnergyModel.hunger_copy(EnergyModel.stage_of(r.since_meal_kcal, r.eer_kcal))
    return r


def copy_registry(r: SimpleNamespace) -> SimpleNamespace:
    return SimpleNamespace(**{k: np.array(v, copy=True) for k, v in vars(r).items()})


def apply_update(r: SimpleNamespace, upd) -> None:  # noqa: ANN001
    """``resolve.advance_body`` の書き方の写し(作り物の表へ)。"""
    if upd is None:
        return
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
        r.since_meal_kcal[:] = upd.since_meal
        r.energy_balance -= upd.spent


# ================================================================= HEAD の式の写し(物差し)
def head_advance_body(r: SimpleNamespace, tick: int, energy=None, activity_columns: bool = False) -> None:  # noqa: ANN001
    """HEAD の ``resolve.advance_body`` の本体(``with agents.writable()`` の中の文=配列へそのまま)。"""
    body = int(tick) % 30 == 0
    rest = bool(activity_columns) and (int(tick) % 10 == 0)
    if energy is None and not (body or rest):
        return
    if body:
        if energy is None:
            r.hunger[:] = np.minimum(r.hunger.astype(np.int16) + 1, 10).astype(np.uint8)
        r.fatigue[:] = np.minimum(r.fatigue.astype(np.int16) + 1, 10).astype(np.uint8)
        sleeping = r.activity == int(Activity.SLEEPING)
        if sleeping.any():
            r.fatigue[sleeping] = np.maximum(r.fatigue[sleeping].astype(np.int16) - 2, 0).astype(np.uint8)
    if rest:
        kind = r.activity_kind
        act = r.activity
        resting = (
            ((kind == int(ActivityKind.IN_SHOP)) | (kind == int(ActivityKind.IN_PLACE)))
            & (r.activity_until > int(tick))
            & (act != int(Activity.MOVING))
            & (act != int(Activity.RIDING))
            & (act != int(Activity.SLEEPING))
        )
        if resting.any():
            r.fatigue[resting] = np.maximum(r.fatigue[resting].astype(np.int16) - 1, 0).astype(np.uint8)
    if energy is not None:
        model = energy.model
        mets = model.mets_of(r.activity, r.transit_state, r.activity_kind if activity_columns else None)
        spent = model.expenditure(r.eer_kcal, mets, energy.bmr)
        r.since_meal_kcal += spent
        r.energy_balance -= spent
        r.hunger[:] = model.hunger_copy(model.stage_of(r.since_meal_kcal, r.eer_kcal))


def head_felt(stage: int, shade: np.ndarray, cell: np.ndarray, n_cells: int) -> np.ndarray:
    """HEAD の ``EnvironmentProcess.step`` の体感温度(``R.set_thermal`` の丸めまで)。"""
    if stage < 0:
        v = np.full(cell.size, 5, dtype=np.uint8)
        return np.clip(v, 0, 10).astype(np.uint8)
    heat = (2, 4, 6, 8, 10)
    base = float(heat[min(stage, len(heat) - 1)])
    per_cell = np.where(shade, base * 0.86, base)
    c = cell.astype(np.int64)
    inside = (c >= 0) & (c < n_cells)
    value = np.where(inside, per_cell[np.maximum(c, 0)], base)
    return np.clip(np.rint(value).astype(np.int64), 0, 10).astype(np.uint8)


def head_collapse(g: np.random.Generator, rate: float, n: int, tick_seconds: int, cell: np.ndarray) -> np.ndarray:
    """HEAD の ``SalientProcess._collapse_events`` の乱数の引き方(倒れる体の id の列)。"""
    per_tick = rate * (n / 10_000.0) / (SECONDS_PER_DAY / max(1, tick_seconds))
    k = int(g.poisson(max(0.0, per_tick)))
    if k <= 0:
        return np.zeros(0, dtype=np.int64)
    inside = np.flatnonzero(np.asarray(cell) >= 0)
    if inside.size == 0:
        return np.zeros(0, dtype=np.int64)
    who = g.choice(inside, size=min(k, inside.size), replace=False)
    return np.sort(np.atleast_1d(who)).astype(np.int64)


def head_stage(v: np.ndarray) -> np.ndarray:
    stage = np.zeros(v.size, dtype=np.int8)
    for e in INTERO_UP_EDGES:
        stage += (v >= e).astype(np.int8)
    return stage
