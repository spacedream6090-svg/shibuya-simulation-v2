"""engine.body.rules — 本人の体の規則(③ 意図しない体と System 1・第 3 期 3-5)の値と純関数。

正: 決定 10-12 §1-5 の ③ 群(意図しない体と System 1 の反応=本人の体としてコードに残す・選択を決めないものに限る)と
D の論点 3(体の生理と急変=本人の体)・計画 10-12 の 3-5 の行。洗い出し ``wallbounce-1006/agentless-outcomes-inventory.md``
の A2(体感温度)・D8(空腹と疲れ)・D9(倒れる)・D18(刻み 0 の体の状態)。

ここに置くのは**値と計算だけ**(状態を持たない)。SoA への書き込みは今までどおり ``engine.resolve`` だけ
(``advance_body``・``initialize``・``initialize_energy``・``set_thermal``)。3-5 より前の場所と同じ式・同じ型・同じ順で
計算する(既定の結果は 1 バイトも変わらない=byte-check 19 構成):

| 規則 | 前の場所 | ここの口 |
|---|---|---|
| 空腹(v1)・疲れ・就寝と休みの回復(D8) | ``resolve.advance_body`` | :func:`interoception`・:func:`fatigue_after`・:func:`hunger_v1_after` |
| 空腹(エネルギー収支 5a・D8) | ``resolve.advance_body`` の後半 | :func:`interoception`(式は ``engine.energy.EnergyModel`` のまま) |
| 体感温度の写像(暑さ段 → 体感 × 日陰・A2) | ``processes/environment.py`` の ``step`` | :func:`felt_cells`・:func:`felt_temperature` |
| 倒れる(顕著行為の引き金=ポアソン・D9) | ``processes/salient.py`` の ``_collapse_events`` | :func:`collapse_draw` |
| 刻み 0 の体の状態(D18) | ``resolve.initialize``・``initialize_energy`` | :func:`initial_values`・:func:`initial_energy_values` |

規則ごとの conf(mechanism/expedient)と出典は :data:`BODY_RULES`。expedient の宣言は :data:`BODY_EXPEDIENTS`(つなぎの台帳の
``BR-BODY-*`` の行と 1 対 1)。体の活動の初期値(W17 の 0 時の行)は予定の表の側(``resolve.set_initial_activity``)に残した
(体の値でなく予定の値)。

層契約: engine の中(``agents.state`` の語・``engine.change_detect`` の段の刻み・``engine.energy`` の式)だけを読む。
逐次ループ宣言(P4): 体数に比例する Python のループは無い(全部配列演算)。:func:`stage_values` は段の刻み 3 本ぶん。
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

from shibuya.agents.state import Activity, ActivityKind
from shibuya.core.time_consts import SECONDS_PER_DAY
from shibuya.engine.change_detect import INTERO_UP_EDGES
from shibuya.engine.energy import HUNGER_RATIO_EDGES

__all__ = [
    "BODY_TICK_PERIOD", "SLEEP_FATIGUE_RELIEF", "ACTIVITY_REST_PERIOD_TICKS", "ACTIVITY_REST_FATIGUE_RELIEF",
    "INTERO_MAX", "HEAT_STAGE_TO_THERMAL", "SHADE_FACTOR", "FALLBACK_THERMAL", "COLLAPSE_PER_10K_PER_DAY",
    "INITIAL_HUNGER", "INITIAL_FATIGUE", "INITIAL_THERMAL", "STAGE_FIELDS",
    "BODY_EXPEDIENTS", "BodyRule", "BODY_RULES", "rule",
    "InteroUpdate", "BodyInitial", "rule_steps", "resting", "fatigue_after", "hunger_v1_after", "energy_spent",
    "hunger_copy_of", "interoception", "felt_cells", "felt_columns", "felt_temperature", "collapse_draw",
    "stage_values", "initial_values", "initial_energy_values", "steps_to_hunger_edge",
]

# ================================================================= 値(前の場所と同じ値・名は前のまま=写しの元)
#: 内受容の自然変動の周期[刻み](expedient=:data:`BODY_EXPEDIENTS` の 1)。3-5 より前は ``engine.resolve`` に置いた
#: (``resolve`` は同じ名で写して出す=読み手の import は変えない)。
BODY_TICK_PERIOD: Final[int] = 30
#: 就寝中の疲れの回復(体の刻みごと)。
SLEEP_FATIGUE_RELIEF: Final[int] = 2
#: 二層の段 2(第275 親の決め #1): 在店/その場で持続中の体の疲れの回復の周期[刻み](expedient=:data:`BODY_EXPEDIENTS` の 2)。
#: ``activity_columns`` のラン(語彙 v3 × ``--activity on``)だけで効く。
ACTIVITY_REST_PERIOD_TICKS: Final[int] = 10
ACTIVITY_REST_FATIGUE_RELIEF: Final[int] = 1
#: 内受容 3 変数の目盛の上限(0〜10)。
INTERO_MAX: Final[int] = 10

#: 暑さ段(0-4)→ 体感温度(0-10)の写像(expedient=:data:`BODY_EXPEDIENTS` の 3)。3-5 より前は
#: ``engine.processes.environment`` に置いた(同じ名で写して出す)。
HEAT_STAGE_TO_THERMAL: Final[tuple[int, ...]] = (2, 4, 6, 8, 10)
#: 日陰係数(知覚契約書 §3 内受容「係数0.86」・R3-2 決定)。**mechanism**(掛け先は expedient=:data:`BODY_EXPEDIENTS` の 4)。
SHADE_FACTOR: Final[float] = 0.86
#: 気象の資産が無い世界の体感温度(「穏やかな 1 日」= C2 の初期値と同値・expedient=:data:`BODY_EXPEDIENTS` の 5)。
FALLBACK_THERMAL: Final[int] = 5

#: 「倒れる」の発生率[件/10,000体/日](expedient=:data:`BODY_EXPEDIENTS` の 6・出典なし)。3-5 より前は
#: ``engine.processes.salient`` に置いた(同じ名で写して出す)。
COLLAPSE_PER_10K_PER_DAY: Final[float] = 3.0

#: 刻み 0 の体の状態(D18・C2 の初期値・expedient=:data:`BODY_EXPEDIENTS` の 7)。
INITIAL_HUNGER: Final[int] = 2
INITIAL_FATIGUE: Final[int] = 2
INITIAL_THERMAL: Final[int] = 5
#: 内受容の値の欄 → 段の欄(変化の検出の前回段。段は ``INTERO_UP_EDGES`` を何本越えたか)。
STAGE_FIELDS: Final[Mapping[str, str]] = MappingProxyType({
    "hunger": "hunger_stage", "fatigue": "fatigue_stage", "thermal": "thermal_stage",
})

#: 本人の体の規則の expedient の宣言(つなぎの台帳の ``BR-BODY-*`` の 7 行と 1 対 1・文を変えたら台帳も直す)。
#: 3-5 で ``resolve``・``processes/environment.py``・``processes/salient.py`` の docstring の見出しの項から移した。
BODY_EXPEDIENTS: Final[tuple[str, ...]] = (
    "内受容の自然変動: 体の刻み(30 刻み)ごとに空腹+1(v1)・疲れ+1、就寝中は疲れ−2(値は自前・契約書に無い・"
    "C4 の世界過程が入るまでの駆動源)",
    "在店/その場で持続中の体の疲れの回復: 10 刻みごとに −1(30 分で −3=旧 休憩 1 回ぶん・第275 親の決め #1・"
    "感度腕 5/10/20 刻み)",
    "暑さ段 → 体感温度 0〜10 の写像 2/4/6/8/10(知覚契約書 §3 はスケールだけを与え、写像を与えていない)",
    "日陰係数 0.86 の掛け先を体感温度の生値にした(係数の値は知覚契約書 §3 と R3-2 の決定=mechanism・掛け先は契約書に無い)",
    "気象の資産が無い世界の体感温度は 5 の固定(穏やかな 1 日=刻み 0 の初期値と同じ値)",
    "倒れる率 1 万体あたり 1 日 3.0 件(出典なし。東京消防庁の出場件数 935,373 件/年を都の人口で割ると 1 万人・日あたり"
    "約 1.8 件だが、救急要請と路上で倒れるは同じでないので同じ桁の丸い値を置いた)",
    "刻み 0 の体の初期値: 空腹 2・疲れ 2・暑さ 5(C2 の初期値・自前)",
)


@dataclass(frozen=True, slots=True)
class BodyRule:
    """本人の体の規則 1 つの出典の欄(conf=mechanism/expedient・出典・つなぎの台帳の行)。

    ``bridge`` はつなぎの台帳の行の id(expedient の規則だけ・mechanism は空)。``inventory`` は洗い出しの行
    (A2・D8・D9・D18)。``port`` はこの規則を計算する口。
    """

    id: str
    what: str
    conf: str
    source: str
    bridge: str
    inventory: str
    port: str


_M, _X = "mechanism", "expedient"
#: 規則の表(③ の 3 件=A2・D8・D9 と D18)。読み手は manifest の ``body.rules`` と試験だけ(結果を変えない)。
BODY_RULES: Final[tuple[BodyRule, ...]] = (
    BodyRule("body.natural_variation", "空腹(v1)+1・疲れ+1/体の刻み・就寝中の疲れ−2", _X,
             "自前(行動契約書に無い)・旧 resolve の expedient の見出しの項", "BR-BODY-NATURAL-VARIATION", "D8",
             "BodyModel.step(interoception)"),
    BodyRule("body.rest_recovery", "在店/その場で持続中の体の疲れ −1/10 刻み", _X,
             "第275 親の決め #1(二層の段 2)・感度腕 5/10/20 刻み", "BR-BODY-REST-RECOVERY", "D8",
             "BodyModel.step(interoception)"),
    BodyRule("body.energy_balance", "空腹=食後の消費 / (EER/3) の語の段(消費=EER/1440×分×METs/AVG)", _X,
             "D-118 K1 (c)・K2 (a)(式)・改訂版メッツ表 2012(METs)・AVG_METS と語の区切りは expedient(engine/energy.py の"
             "見出しの項)", "HD-engine.energy-cc73b60c", "D8", "BodyModel.step(interoception)"),
    BodyRule("body.felt_map", "暑さ段 → 体感温度 2/4/6/8/10", _X, "知覚契約書 §3(スケール 0-10 だけ)・写像は自前",
             "BR-BODY-FELT-MAP", "A2", "BodyModel.felt_temperature"),
    BodyRule("body.shade_factor", "日陰の体感温度=生値 × 0.86", _M, "知覚契約書 §3 内受容「係数0.86」・R3-2 の決定", "",
             "A2", "BodyModel.felt_temperature"),
    BodyRule("body.shade_target", "日陰係数の掛け先=体感温度の生値", _X, "自前(契約書は係数の値だけを与える)",
             "BR-BODY-SHADE-TARGET", "A2", "BodyModel.felt_temperature"),
    BodyRule("body.felt_fallback", "気象の資産が無い世界の体感温度 5", _X, "自前(穏やかな 1 日=C2 の初期値)",
             "BR-BODY-FELT-FALLBACK", "A2", "BodyModel.felt_temperature"),
    BodyRule("body.collapse_rate", "倒れる=1 万体あたり 1 日 3.0 件のポアソン・在圏の体から乱数で選ぶ", _X,
             "出典なし(東京消防庁の出場件数から同じ桁の丸い値・決定 10-12 §1-5 の D の論点 3=出典を探す)",
             "BR-BODY-COLLAPSE-RATE", "D9", "BodyModel.collapse_draw"),
    BodyRule("body.initial", "刻み 0 の空腹 2・疲れ 2・暑さ 5", _X, "C2 の初期値(自前)", "BR-BODY-INITIAL", "D18",
             "BodyModel.initial"),
    BodyRule("body.initial_energy", "刻み 0 の食後の消費=EER × (1 日 − 夕食の既定の分)/1 日", _X,
             "engine/energy.py の見出しの項(前夜の夕食から 0:00 まで基準日の速さ)", "HD-engine.energy-cc73b60c", "D18",
             "BodyModel.initial"),
)


def rule(rule_id: str) -> BodyRule:
    """規則の id → 行。"""
    for r in BODY_RULES:  # 逐次: 規則の数ぶん(10)
        if r.id == rule_id:
            return r
    raise KeyError(rule_id)


# ================================================================= 内受容(空腹・疲れ)
@dataclass(frozen=True, slots=True)
class InteroUpdate:
    """体の刻み 1 回の書き込み(``resolve.advance_body`` が SoA に写す)。

    ``*_ids`` が None なら全員(配列は体数の長さ)・配列ならその体だけ(値は同じ並び)。値が None の欄は書かない。
    ``spent``(1 刻みの消費・全員)と ``since_meal``(足した後の食後の消費・全員)はエネルギー収支のランだけ。
    """

    fatigue_ids: np.ndarray | None
    fatigue: np.ndarray | None
    hunger_ids: np.ndarray | None
    hunger: np.ndarray | None
    since_meal: np.ndarray | None
    spent: np.ndarray | None


def rule_steps(now: int, activity_columns: bool) -> tuple[bool, bool]:
    """``now`` が体の刻み(空腹+1・疲れ+1・就寝の回復)か・休みの回復の刻みか。"""
    body_now = int(now) % BODY_TICK_PERIOD == 0
    rest_now = bool(activity_columns) and (int(now) % ACTIVITY_REST_PERIOD_TICKS == 0)
    return body_now, rest_now


def resting(act: np.ndarray, kind: np.ndarray, until: np.ndarray, now: int) -> np.ndarray:
    """「休んでいる体」=活動の種別が 在店/その場 で持続中・移動/乗車/就寝中でない(二層の段 2)。"""
    return (
        ((kind == int(ActivityKind.IN_SHOP)) | (kind == int(ActivityKind.IN_PLACE)))
        & (until > int(now))
        & (act != int(Activity.MOVING))
        & (act != int(Activity.RIDING))
        & (act != int(Activity.SLEEPING))
    )


def fatigue_after(f: np.ndarray, act: np.ndarray, kind: np.ndarray | None, until: np.ndarray | None, now: int,
                  body_now: bool, rest_now: bool) -> np.ndarray:
    """疲れの規則(体の刻みの +1・就寝中の −2・休みの −1)。3-5 より前の ``advance_body`` と同じ値(``uint8``)。"""
    out = np.asarray(f)
    if body_now:
        out = np.minimum(out.astype(np.int16) + 1, INTERO_MAX).astype(np.uint8)
        sleeping = np.asarray(act) == int(Activity.SLEEPING)
        if sleeping.any():
            out = np.where(sleeping, np.maximum(out.astype(np.int16) - SLEEP_FATIGUE_RELIEF, 0).astype(np.uint8), out)
    if rest_now and kind is not None and until is not None:
        res = resting(np.asarray(act), np.asarray(kind), np.asarray(until), now)
        if res.any():
            out = np.where(res, np.maximum(out.astype(np.int16) - ACTIVITY_REST_FATIGUE_RELIEF, 0).astype(np.uint8),
                           out)
    return out


def hunger_v1_after(h: np.ndarray, body_now: bool) -> np.ndarray:
    """空腹(v1)の規則(体の刻みの +1・上限 10)。"""
    if not body_now:
        return np.asarray(h)
    return np.minimum(np.asarray(h).astype(np.int16) + 1, INTERO_MAX).astype(np.uint8)


def energy_spent(energy: Any, act: np.ndarray, transit: np.ndarray, kind: np.ndarray | None,
                 eer: np.ndarray) -> np.ndarray:
    """1 刻みの消費(``float32``・全員)=``EnergyModel.expenditure(eer, mets_of(活動), bmr)``(式は energy.py のまま)。"""
    model = energy.model
    mets = model.mets_of(act, transit, kind)
    return model.expenditure(eer, mets, energy.bmr)


def hunger_copy_of(energy: Any, since: np.ndarray, eer: np.ndarray) -> np.ndarray:
    """食後の消費 → 空腹の写し(語の段 1/5/8/10・``uint8``)。"""
    model = energy.model
    return model.hunger_copy(model.stage_of(since, eer))


def interoception(r: Any, now: int, *, energy: Any = None, activity_columns: bool = False) -> InteroUpdate | None:
    """全員を見る版(sweep)の体の刻み 1 回。3-5 より前の ``resolve.advance_body`` と同じ値。

    ``r`` は ``agents.registry``(読むだけ)。書くことが無い刻み(エネルギー収支の無いランの体の刻みでも休みの刻みでも
    ない刻み)は None。
    """
    body_now, rest_now = rule_steps(now, activity_columns)
    if energy is None and not (body_now or rest_now):
        return None
    ac = bool(activity_columns)
    act = r.activity
    kind = r.activity_kind if ac else None
    until = r.activity_until if ac else None
    fat = fatigue_after(r.fatigue, act, kind, until, now, body_now, rest_now) if (body_now or rest_now) else None
    hun = None
    since = spent = None
    if energy is None:
        if body_now:
            hun = hunger_v1_after(r.hunger, True)
    else:
        spent = energy_spent(energy, act, r.transit_state, kind, r.eer_kcal)
        since = r.since_meal_kcal + spent
        hun = hunger_copy_of(energy, since, r.eer_kcal)
    return InteroUpdate(None, fat, None, hun, since, spent)


def steps_to_hunger_edge(since: np.ndarray, eer: np.ndarray, spent: np.ndarray) -> np.ndarray:
    """今の食後の消費 ``since`` から、1 刻みに ``spent`` ずつ足して次の語の段の境目を越えるまでの刻みの数の見込み
    (``float64``・いちばん上の段と消費 0 は inf)。``stage_of`` と同じ ``float32`` の比で今の段を決め、境目の値は
    ``float64`` で見込む(浮動小数の積み上げの誤差の幅は ``engine.body.schedule`` が余白にする)。"""
    meal = np.maximum(np.asarray(eer, dtype=np.float32), np.float32(1e-3)) / np.float32(3.0)
    s32 = np.asarray(since, dtype=np.float32)
    edges = np.asarray(HUNGER_RATIO_EDGES, dtype=np.float32)
    k = np.searchsorted(edges, s32 / meal, side="right")
    top = np.append(edges.astype(np.float64), np.inf)
    target = top[k] * meal.astype(np.float64)
    gap = target - s32.astype(np.float64)
    x = np.asarray(spent, dtype=np.float64)
    with np.errstate(divide="ignore", invalid="ignore"):
        j = np.ceil(gap / x)
    return np.where(np.isfinite(j) & (x > 0.0), np.maximum(j, 1.0), np.inf)


# ================================================================= 体感温度(A2)
def felt_cells(stage: int, shade: np.ndarray | None, n_cells: int) -> np.ndarray:
    """その 5 分の窓のセルごとの体感温度(``uint8``・長さ ``n_cells + 1``=末尾は舞台の外の体の値)。

    3-5 より前の ``EnvironmentProcess.step`` と同じ値: 暑さ段 → 生値(:data:`HEAT_STAGE_TO_THERMAL`)・日陰のセルは
    × :data:`SHADE_FACTOR`・``rint`` して 0〜10 に丸める。気象の資産が無い(``stage < 0``)ときは全部
    :data:`FALLBACK_THERMAL`。
    """
    out = np.empty(int(n_cells) + 1, dtype=np.uint8)
    if int(stage) < 0:
        out[:] = FALLBACK_THERMAL
        return out
    base = float(HEAT_STAGE_TO_THERMAL[min(int(stage), len(HEAT_STAGE_TO_THERMAL) - 1)])
    per_cell = np.where(np.asarray(shade, dtype=bool), base * SHADE_FACTOR, base)
    out[: int(n_cells)] = np.clip(np.rint(per_cell), 0, INTERO_MAX).astype(np.uint8)
    out[int(n_cells)] = np.uint8(min(max(int(np.rint(base)), 0), INTERO_MAX))
    return out


def felt_columns(cell: np.ndarray, n_cells: int) -> np.ndarray:
    """体のセル → :func:`felt_cells` の列(舞台の中のセルはそのセル・外=−1 や範囲外は末尾の列)。"""
    c = np.asarray(cell).astype(np.int64)
    return np.where((c >= 0) & (c < int(n_cells)), c, int(n_cells))


def felt_temperature(stage: int, shade: np.ndarray | None, cell: np.ndarray, n_cells: int) -> np.ndarray:
    """全員の体感温度(``uint8``)=:func:`felt_cells` を体のセルで引いた値(全員を見る版)。"""
    return felt_cells(stage, shade, n_cells)[felt_columns(cell, n_cells)]


# ================================================================= 倒れる(D9)
def collapse_draw(g: np.random.Generator, rate_per_10k_per_day: float, n_agents: int, step_seconds: int,
                  cell: np.ndarray) -> np.ndarray:
    """この刻みに倒れる体(id の昇順・``int64``)。3-5 より前の ``SalientProcess._collapse_events`` と同じ乱数の引き方
    (ポアソンで件数 → 在圏(セル ≥ 0)の体から重複なしで選ぶ)。"""
    per_step = float(rate_per_10k_per_day) * (int(n_agents) / 10_000.0) / (SECONDS_PER_DAY / max(1, int(step_seconds)))
    n = int(g.poisson(max(0.0, per_step)))
    if n <= 0:
        return np.zeros(0, dtype=np.int64)
    inside = np.flatnonzero(np.asarray(cell) >= 0)
    if inside.size == 0:
        return np.zeros(0, dtype=np.int64)
    who = g.choice(inside, size=min(n, inside.size), replace=False)
    return np.sort(np.atleast_1d(who)).astype(np.int64)


# ================================================================= 刻み 0 の体の状態(D18)
@dataclass(frozen=True, slots=True)
class BodyInitial:
    """刻み 0 の体の状態(``uint8``・``int8``・``float32`` の配列)。エネルギー収支の欄はそのランだけ(ほかは None)。"""

    hunger: np.ndarray
    fatigue: np.ndarray | None
    thermal: np.ndarray | None
    stages: Mapping[str, np.ndarray]
    since_meal: np.ndarray | None = None


def stage_values(v: np.ndarray) -> np.ndarray:
    """内受容の値 → 段(``INTERO_UP_EDGES`` を何本越えたか・``int8``)。"""
    stage = np.zeros(np.asarray(v).shape, dtype=np.int8)
    for e in INTERO_UP_EDGES:  # 段の刻み 3 本ぶん(体数には比例しない)
        stage += (np.asarray(v) >= e).astype(np.int8)
    return stage


def initial_values(n: int) -> BodyInitial:
    """刻み 0 の空腹・疲れ・暑さと段(3-5 より前の ``resolve.initialize`` と同じ値)。"""
    h = np.full(int(n), INITIAL_HUNGER, dtype=np.uint8)
    f = np.full(int(n), INITIAL_FATIGUE, dtype=np.uint8)
    t = np.full(int(n), INITIAL_THERMAL, dtype=np.uint8)
    return BodyInitial(h, f, t, MappingProxyType({
        "hunger_stage": stage_values(h), "fatigue_stage": stage_values(f), "thermal_stage": stage_values(t)}))


def initial_energy_values(energy: Any, eer: np.ndarray) -> BodyInitial:
    """エネルギー収支のランの刻み 0 の食後の消費・空腹の写しと段(3-5 より前の ``resolve.initialize_energy`` と同じ値)。

    ``eer`` は ``float32``(``EnergyModel.draw_bodies`` の値=SoA の ``eer_kcal`` と同じ)。
    """
    model = energy.model
    # 〔小さな版上げ・回答 10-13b §7 の 2〕腕 w17 は体ごとの前夜の夕食の分(EnergyLayer.initial_dinner_min)から。
    # 無い呼び手(腕 validation・作り物の層)は前と同じ 1 つの既定の分
    dinner = getattr(energy, "initial_dinner_min", None)
    since = model.initial_since_meal(eer) if dinner is None else model.initial_since_meal(eer, dinner)
    hun = model.hunger_copy(model.stage_of(since, eer))
    return BodyInitial(hun, None, None, MappingProxyType({"hunger_stage": stage_values(hun)}), since)
