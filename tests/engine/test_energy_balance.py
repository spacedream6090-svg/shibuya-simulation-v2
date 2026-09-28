"""5 段目 5a: 体のエネルギー収支(D-118 K1〜K9・第291)のテスト。

正典: ``docs/design/v2-energy-classical-implementation-agenda.md`` §1(1〜10)・草案
``docs/design/v2-hunger-choice-attention-draft.md`` §1-2・§1-2b・§1-6。
錨は追跡ファイル ``docs/bench/anchors/hunger_energy_anchors_v0.json`` だけを読む(data/ は読まない)。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import ENERGY_FIELDS, Activity, ActivityKind, AgentKind, AgentState
from shibuya.agents.weekly import ACTIVITY_WORDS, N_DAYS, PLACE_WORDS, WeeklySchedule
from shibuya.engine import energy as E
from shibuya.engine import resolve as R
from shibuya.engine.change_detect import ChangeDetector
from shibuya.perception import templates as T
from shibuya.perception.renderer import Renderer
from shibuya.world.state import World

ANC, ANC_MD5 = E.load_anchors()
SRC = Path("src/shibuya")
CJK = re.compile(r"[぀-ヿ㐀-鿿]")


def model(rate: str = "eer") -> E.EnergyModel:
    return E.EnergyModel(ANC, ANC_MD5, rate=rate)


def layer(n: int, rate: str = "eer") -> E.EnergyLayer:
    return E.EnergyLayer(model=model(rate), n_agents=n)


def energy_agents(n: int, *, activity_columns: bool = False) -> AgentState:
    return AgentState(n, energy_columns=True, activity_columns=activity_columns)


# ================================================================= 錨(追跡ファイル)
def test_anchor_values_are_pinned():
    """アジェンダ §1-9 の固定値: 23.7/63.0・1.75・199/164・31.1/37.3/26.5・77.2/7:12・3.5/4.3/3.0/1.0/1.3。"""
    dri = ANC["dri2025"]
    k = dri["age_classes"].index("18-29")
    assert dri["bmr_per_kg_kcal"]["male"][k] == 23.7
    assert dri["ref_weight_kg"]["male"][k] == 63.0
    assert dri["pal_normal"][k] == 1.75
    assert dri["eer_sd_kcal_day"] == {"male": 199, "female": 164}
    t10 = ANC["nhns_t10_breakfast_skip"]
    j = t10["age_classes"].index("20-29")
    assert (t10["pct"]["total"][j], t10["pct"]["male"][j], t10["pct"]["female"][j]) == (31.1, 37.3, 26.5)
    nat = ANC["ssb2021_t18_1_weekday"]["national"]["breakfast_start"]
    assert (nat["rate_pct"], nat["mean_time"]) == (77.2, "7:12")
    mets = ANC["mets_2012"]["mets"]
    assert (mets["17190"], mets["17200"], mets["17170"], mets["07030"], mets["07020"]) == (
        3.5, 4.3, 3.0, 1.0, 1.3
    )
    assert mets["11600"] == 3.0 and mets["07011"] == 1.3
    # 表4 の PAL ふつうは 12 階級すべてにある(1-2 歳 1.35・75+ 1.70)
    assert len(dri["pal_normal"]) == 12 and dri["pal_normal"][0] == 1.35 and dri["pal_normal"][-1] == 1.7


def test_default_meal_times_come_from_the_anchors():
    """範囲外の既定の時刻: 朝 7:29・夕 19:18(第18-1表 東京都 平日)・昼=第7-1表 東京都の最大区分の開始。"""
    m = model()
    assert m.default_meal_min == {"breakfast": 449, "lunch": 735, "dinner": 1158}
    tokyo = ANC["ssb2021_meal_rate_15min"]["series"]["t7_1_weekday_tokyo_total"]["rate_pct"]
    vals = [-1.0 if x is None else float(x) for x in tokyo]
    assert max(range(96), key=lambda i: (vals[i], -i)) * 15 == 735  # 12:15-12:30 = 35.21%
    assert 705 <= m.default_meal_min["lunch"] <= 735  # アジェンダの見込み 11:45〜12:15(上端)


def test_anchor_file_holds_numbers_and_codes_only():
    """表の文言(活動名の和文など)は入れない=和文は出典表記の 4 行だけ。"""
    raw = E.ANCHORS_PATH.read_text(encoding="utf-8")
    body = dict(ANC)
    attribution = body.pop("attribution")
    assert len(attribution) == 4
    assert sum("を加工して作成" in a for a in attribution) == 3
    assert "身体活動のメッツ" in attribution[3]
    import json

    assert not CJK.search(json.dumps(body, ensure_ascii=False)), "錨の本体に和文がある"
    assert raw.count("\r") == 0
    for name, src in ANC["sources"].items():
        assert re.fullmatch(r"[0-9a-f]{32}", src["json_md5"]), name


def test_meal_shares_are_normalized_to_three_meals():
    sh = ANC["nhns_t13_meal_kcal"]["shares_20plus"]["total"]
    assert (round(sh["breakfast"], 2), round(sh["lunch"], 2), round(sh["dinner"], 2)) == (0.24, 0.32, 0.44)
    assert round(sh["snack_of_four"], 3) == 0.069
    s = ANC["nhns_t13_meal_kcal"]["shares"]
    for sx in ("total", "male", "female"):
        for i in range(len(s[sx]["breakfast"])):
            assert abs(s[sx]["breakfast"][i] + s[sx]["lunch"][i] + s[sx]["dinner"][i] - 1.0) < 1e-5


# ================================================================= 体の定数
def test_eer_of_the_reference_body_is_2756():
    """草案 §1-2b: 男 30〜49 歳・参照体重 70.0 kg → BMR 1,575・EER 2,756。"""
    m = model()
    assert m.bmr_kcal(np.array([35]), np.array([0]), np.array([70.0]))[0] == pytest.approx(1575.0)
    assert round(m.eer_reference(35, 0, 70.0)) == 2756


def test_weight_is_clipped_to_three_sd_and_age_zero_uses_the_age_one_row():
    m = model()
    w, eer = m.bodies_from_z(
        np.array([0, 35, 35]), np.array([0, 0, 1]), np.array([0.0, 10.0, -10.0]), np.zeros(3)
    )
    t14 = ANC["nhns_t14_weight"]
    i1 = t14["rows"].index("1")
    i30 = t14["rows"].index("30-39")
    assert w[0] == pytest.approx(t14["weight_kg"]["male"]["mean"][i1])
    mm, ms = t14["weight_kg"]["male"]["mean"][i30], t14["weight_kg"]["male"]["sd"][i30]
    fm, fs = t14["weight_kg"]["female"]["mean"][i30], t14["weight_kg"]["female"]["sd"][i30]
    assert w[1] == pytest.approx(mm + 3 * ms, rel=1e-6)
    assert w[2] == pytest.approx(max(5.0, fm - 3 * fs), rel=1e-6)
    # EER = 表3 × 体重 × 表4 ふつう(個人差 0)
    assert eer[1] == pytest.approx(22.5 * w[1] * 1.75, rel=1e-5)
    assert eer[2] == pytest.approx(21.9 * w[2] * 1.75, rel=1e-5)


def test_eer_floor_is_the_basal_metabolism():
    m = model()
    w, eer = m.bodies_from_z(np.array([1]), np.array([0]), np.array([-3.0]), np.array([-10.0]))
    bmr = m.bmr_kcal(np.array([1]), np.array([0]), w)[0]
    assert eer[0] == pytest.approx(bmr * E.EER_FLOOR_PAL, rel=1e-6)


def test_body_draw_is_per_agent_and_deterministic():
    m = model()
    age = np.full(20, 30)
    sex = np.arange(20) % 2
    a = m.draw_bodies(age[:10], sex[:10], 1)
    b = m.draw_bodies(age, sex, 1)
    c = m.draw_bodies(age, sex, 2)
    np.testing.assert_array_equal(a[0], b[0][:10])
    np.testing.assert_array_equal(a[1], b[1][:10])
    assert not np.array_equal(b[0], c[0])
    assert a[0].dtype == np.float32 and a[1].dtype == np.float32


def test_unknown_sex_uses_the_mean_of_the_two_tables():
    m = model()
    w, _ = m.bodies_from_z(np.array([35, 35, 35]), np.array([0, 1, -1]), np.zeros(3), np.zeros(3))
    assert w[2] == pytest.approx((w[0] + w[1]) / 2.0, rel=1e-6)


# ================================================================= 消費(K1 (c))
def _reference_day(rate: str) -> float:
    """座位中心の基準日(就寝 7.5 h・その場 14.5 h・目的地つき移動 1.5 h・あたり 0.5 h)の 1,440 tick。"""
    a = energy_agents(1, activity_columns=True)
    lay = layer(1, rate)
    with a.writable():
        a.age[0] = 35
        a.sex[0] = 0
        a.weight_kg[0] = 70.0
        a.eer_kcal[0] = np.float32(model().eer_reference(35, 0, 70.0))
        a.transit_state[0] = 0
    if rate == "bmr":
        lay.bmr = np.array([1575.0], dtype=np.float32)
    plan = ([(Activity.SLEEPING, ActivityKind.NONE)] * 450
            + [(Activity.IDLE, ActivityKind.IN_PLACE)] * 870
            + [(Activity.MOVING, ActivityKind.MOVE_TO)] * 90
            + [(Activity.MOVING, ActivityKind.WANDER)] * 30)
    assert len(plan) == 1440
    for tick, (act, kind) in enumerate(plan):
        with a.writable():
            a.activity[0] = int(act)
            a.activity_kind[0] = int(kind)
        R.advance_body(a, tick, lay)
    return -float(a.energy_balance[0])


def test_reference_day_expenditure_equals_eer_within_0_1_percent():
    """(g) 基準日の構成で 1,440 tick の消費の和は EER に 0.1% 以内で一致する(AVG_METS=1.379)。"""
    spent = _reference_day("eer")
    eer = model().eer_reference(35, 0, 70.0)
    assert abs(spent - eer) / eer < 0.001


def test_bmr_arm_gives_bmr_times_mean_mets():
    """K1 (a) の感度腕: 基準日=BMR 1,575 × 平均 METs 1.379 ≈ 2,172(草案 §1-2b (1))。"""
    spent = _reference_day("bmr")
    assert spent == pytest.approx(1575.0 * 33.1 / 24.0, rel=1e-3)
    assert round(spent) in (2171, 2172)


def test_mets_follow_the_activity():
    m = model()
    act = np.array([Activity.SLEEPING, Activity.MOVING, Activity.MOVING, Activity.IDLE,
                    Activity.SHOPPING, Activity.RIDING, Activity.WAITING, Activity.IDLE], dtype=np.int8)
    kind = np.array([0, ActivityKind.MOVE_TO, ActivityKind.WANDER, ActivityKind.IN_PLACE,
                     ActivityKind.IN_SHOP, ActivityKind.MOVE_TO, 0, 0], dtype=np.int8)
    transit = np.array([0, 0, 0, 0, 0, 1, 2, 0], dtype=np.int8)
    got = m.mets_of(act, transit, kind)
    np.testing.assert_allclose(got, [1.0, 3.5, 3.0, 1.3, 1.3, 1.3, E.AVG_METS, 1.3], rtol=1e-6)
    # 活動層の無いラン(v1/v2・activity off): 歩行はすべて目的地つき移動
    got2 = m.mets_of(act, transit, None)
    assert got2[2] == pytest.approx(3.5)


# ================================================================= 語(K2)と写し
def test_stage_edges_and_hunger_copy():
    eer = np.full(7, 3000.0, dtype=np.float32)
    meal = 1000.0
    since = np.array([0.0, 0.249, 0.25, 0.749, 0.75, 1.499, 1.5], dtype=np.float32) * meal
    st = E.EnergyModel.stage_of(since, eer)
    np.testing.assert_array_equal(st, [0, 0, 1, 1, 2, 2, 3])
    np.testing.assert_array_equal(E.EnergyModel.hunger_copy(np.arange(4)), [1, 5, 8, 10])
    # 写しは INTERO_UP_EDGES=(4,7,9) の段 0〜3 にそのまま対応する
    from shibuya.engine.change_detect import INTERO_UP_EDGES

    for s, v in enumerate(E.HUNGER_STAGE_VALUES):
        assert sum(v >= e for e in INTERO_UP_EDGES) == s


def test_initialize_energy_places_the_copy_without_a_false_crossing():
    a = energy_agents(6)
    with a.writable():
        a.age[:] = [0, 8, 22, 35, 70, 90]
        a.sex[:] = [0, 1, 0, 1, -1, 1]
    lay = layer(6)
    R.initialize_energy(a, lay, seed=1)
    # 初期値 = EER × (1440 − 1158)/1440 → 比 0.5875 → ふつう
    np.testing.assert_allclose(a.since_meal_kcal, a.eer_kcal * (282 / 1440), rtol=1e-5)
    assert set(a.hunger.tolist()) == {5}
    assert set(a.hunger_stage.tolist()) == {1}
    assert float(np.abs(a.energy_balance).sum()) == 0.0
    w = World.synthetic(n_cells=4, seed=1)
    det = ChangeDetector(a.n, w.n_cells).detect(w, a, tick=0)
    assert det.crossings[0].agent_id.size == 0


def test_advance_body_without_energy_is_the_old_rule():
    a = AgentState(3)
    with a.writable():
        a.hunger[:] = [2, 9, 10]
    R.advance_body(a, 30)
    np.testing.assert_array_equal(a.hunger, [3, 10, 10])
    R.advance_body(a, 31)
    np.testing.assert_array_equal(a.hunger, [3, 10, 10])
    assert not any(f in a.registry.arrays for f in ENERGY_FIELDS)


def test_energy_run_stops_the_plus_one_and_keeps_fatigue():
    a = energy_agents(2)
    lay = layer(2)
    with a.writable():
        a.age[:] = 35
        a.sex[:] = 0
    R.initialize_energy(a, lay, seed=1)
    f0 = a.fatigue.copy()
    R.advance_body(a, 30, lay)
    np.testing.assert_array_equal(a.fatigue, f0 + 1)
    assert set(a.hunger.tolist()) <= set(E.HUNGER_STAGE_VALUES)


# ================================================================= 摂取(K7・K3)
def test_meal_share_depends_on_time_sex_and_age():
    m = model()
    s = ANC["nhns_t13_meal_kcal"]["shares"]
    age = np.array([25, 25, 25, 15])
    sex = np.array([0, 1, -1, 0])
    assert m.meal_share_of(age[:1], sex[:1], 7 * 60)[0] == pytest.approx(s["male"]["breakfast"][0])
    assert m.meal_share_of(age[1:2], sex[1:2], 12 * 60)[0] == pytest.approx(s["female"]["lunch"][0])
    assert m.meal_share_of(age[2:3], sex[2:3], 19 * 60)[0] == pytest.approx(s["total"]["dinner"][0])
    # 20 歳未満は 20-29 の行・窓の外(16 時台・深夜)は昼の比
    assert m.meal_share_of(age[3:], sex[3:], 16 * 60 + 30)[0] == pytest.approx(s["male"]["lunch"][0])
    assert m.meal_share_of(age[3:], sex[3:], 3 * 60)[0] == pytest.approx(s["male"]["lunch"][0])
    assert m.snack_share_of(age[2:3], sex[2:3])[0] == pytest.approx(s["total"]["snack_of_four"][0])


def test_out_of_area_meal_resets_since_meal_and_adds_the_share():
    a = energy_agents(2)
    lay = layer(2)
    with a.writable():
        a.age[:] = 25
        a.sex[:] = [0, 1]
    R.initialize_energy(a, lay, seed=3)
    with a.writable():
        a.since_meal_kcal[:] = 1500.0
    eer = a.eer_kcal.astype(np.float64)
    got = R.energy_out_of_area_meal(a, lay, np.array([0, 1]), np.array([0, 0]),
                                    np.array([True, False]), tick=449)
    assert got == 2
    np.testing.assert_array_equal(a.since_meal_kcal, [0.0, 0.0])
    s = ANC["nhns_t13_meal_kcal"]["shares"]
    np.testing.assert_allclose(
        a.energy_balance, eer * np.array([s["male"]["breakfast"][0], s["female"]["breakfast"][0]]),
        rtol=1e-5,
    )
    np.testing.assert_array_equal(a.hunger, [1, 1])
    assert lay.counts["meals_out_of_area"] == 2
    assert lay.counts["meals_out_from_row"] == 1 and lay.counts["meals_out_default"] == 1
    assert int(lay.meal_bits[0]) == 1 and int(lay.meal_start_out[449 // 15]) == 2


def test_snack_and_drink_subtract_from_since_meal():
    a = energy_agents(3)
    lay = layer(3)
    lay.poi_intake = np.array([E.INTAKE_SNACK, E.INTAKE_DRINK, E.INTAKE_NONE], dtype=np.int8)
    with a.writable():
        a.age[:] = 25
        a.sex[:] = -1
    R.initialize_energy(a, lay, seed=1)
    with a.writable():
        a.since_meal_kcal[:] = [900.0, 900.0, 900.0]
        a.energy_balance[:] = 0.0
        R._energy_snack(a.registry, np.array([0, 1, 2]), np.array([0, 1, 2]), 600, lay)
    eer = a.eer_kcal.astype(np.float64)
    snack = ANC["nhns_t13_meal_kcal"]["shares"]["total"]["snack_of_four"][0] * eer[0]
    drink = E.DRINK_SHARE * eer[1]
    assert a.since_meal_kcal[0] == pytest.approx(max(0.0, 900.0 - snack), rel=1e-5)
    assert a.since_meal_kcal[1] == pytest.approx(900.0 - drink, rel=1e-5)
    assert a.since_meal_kcal[2] == pytest.approx(900.0)
    np.testing.assert_allclose(a.energy_balance, [snack, drink, 0.0], rtol=1e-5)
    assert lay.counts["snacks"] == 1 and lay.counts["drinks"] == 1


def test_poi_intake_kind_is_food_or_convenience_for_snacks():
    got = E.EnergyModel.poi_intake_kind(
        ("food", "shop", "shop", "nightlife", "office"),
        ("", "convenience", "vending", "", ""), 5,
    )
    np.testing.assert_array_equal(got, [1, 1, 2, 0, 0])


# ================================================================= 範囲外の食事(K9)
def _weekly(rows, n_agents):
    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    counts = np.zeros(n_agents * N_DAYS, dtype=np.int64)
    for r in rows:
        counts[int(r[0]) * N_DAYS] += 1
    offset = np.zeros(counts.size + 1, dtype=np.int64)
    np.cumsum(counts, out=offset[1:])
    return WeeklySchedule(
        source=None,
        agent_id=np.arange(n_agents, dtype=np.int64),
        day_offset=offset,
        start_min=np.asarray([r[1] for r in rows], dtype=np.int16),
        end_min=np.asarray([r[2] for r in rows], dtype=np.int16),
        activity=np.asarray([r[3] for r in rows], dtype=np.int8),
        place_kind=np.asarray([r[4] for r in rows], dtype=np.int8),
        target_cell=np.full(len(rows), -1, dtype=np.int32),
        seq=np.arange(len(rows), dtype=np.int16),
    )


def test_out_of_area_schedule_uses_meal_rows_then_default_times():
    SLEEP, WORK, EAT = (ACTIVITY_WORDS.index(w) for w in ("就寝", "勤務", "食事"))
    HOME, OUT = PLACE_WORDS.index("自宅"), PLACE_WORDS.index("域外")
    rows = [
        (0, 0, 420, SLEEP, HOME), (0, 540, 750, WORK, OUT), (0, 750, 780, EAT, OUT),
        (0, 780, 1080, WORK, OUT),
        (1, 0, 600, SLEEP, HOME),  # 7:29 に就寝中でも既定の時刻どおり(アジェンダ §1-5 の文言)
    ]
    oom = E.OutOfAreaMeals(model(), 3, 1440, weekly=_weekly(rows, 3), day_index=0)
    ev = sorted(zip(oom.agent.tolist(), oom.tick.tolist(), oom.slot.tolist(), oom.from_row.tolist()))
    assert ev == [
        (0, 449, 0, False), (0, 750, 1, True), (0, 1158, 2, False),
        (1, 449, 0, False), (1, 735, 1, False), (1, 1158, 2, False),
        (2, 449, 0, False), (2, 735, 1, False), (2, 1158, 2, False),
    ]
    out = np.full(3, 2, dtype=np.int8)
    ids, slots, fr = oom.due(449, out)
    np.testing.assert_array_equal(ids, [0, 1, 2])
    ids, _, _ = oom.due(449, np.zeros(3, dtype=np.int8))  # 範囲内なら置かない
    assert ids.size == 0
    ids, slots, fr = oom.due(750, out)
    assert ids.tolist() == [0] and slots.tolist() == [1] and fr.tolist() == [True]


def test_out_of_area_schedule_without_weekly_is_three_default_times():
    oom = E.OutOfAreaMeals(model(), 2, 1440, weekly=None)
    assert sorted(set(oom.tick.tolist())) == [449, 735, 1158]
    assert oom.n_rows == 0 and oom.n_defaults == 6


# ================================================================= 描画(B5 は語)
def _render_b5(a: AgentState, i: int) -> str:
    w = World.synthetic(n_cells=4, seed=1)
    with a.writable():
        a.cell[:] = 0
        a.kind[:] = AgentKind.VISITOR
    w.cells.density[:] = w.compute_density(a.cell)
    return Renderer(w, a, seed=7).render(i, 760, 3).blocks["B5"].decode("utf-8")


def test_b5_draws_hunger_as_words_only_from_hungry():
    a = energy_agents(4)
    with a.writable():
        a.hunger[:] = [1, 5, 8, 10]
        a.fatigue[:] = 0
        a.thermal[:] = 0
    b = [_render_b5(a, i).split("\n")[0] for i in range(4)]
    assert "体調に変わりはありません" in b[0] and "体調に変わりはありません" in b[1]
    assert b[2] == "[B5 内受容] いま空腹です。"
    assert b[3] == "[B5 内受容] いまとても空腹です。"
    assert all("空腹は" not in x for x in b)


def test_b5_of_a_v1_run_keeps_the_old_numbers():
    a = AgentState(2)
    with a.writable():
        a.hunger[:] = [9, 0]
        a.fatigue[:] = 0
        a.thermal[:] = 0
    assert "空腹は9で閾値を超えています" in _render_b5(a, 0)


def test_hunger_words_live_in_the_templates():
    assert T.HUNGER_WORDS == ("満腹", "ふつう", "空腹", "とても空腹")
    assert T.HUNGER_ITEM_TEMPLATE == "いま{word}です。"
    assert "B5.intero_hunger" not in T.TEMPLATES  # 行テンプレではなく項(1 行 1 事実の契約)
    assert T.HUNGER_WORD_DRAW_MIN_STAGE == 2
    assert T.TEMPLATE_VERSION in ("v1.1", "v1.2", "v1.3")  # v1.2=6b・v1.3=7c も空腹の語は同じ


# ================================================================= P4(配列演算だけ)
_PER_TICK = {
    "engine/energy.py": ("mets_of", "expenditure", "stage_of", "hunger_copy", "meal_share_of",
                         "meal_share_for_slot", "snack_share_of", "due", "after_tick", "note"),
    "engine/resolve.py": ("advance_body", "_energy_meal", "energy_out_of_area_meal"),
}


def test_per_tick_paths_have_no_python_loops():
    """P4: 毎 tick 通る関数に for/while を書かない(体数ぶんの逐次ループを新設しない)。"""
    offenders = []
    for rel, names in _PER_TICK.items():
        tree = ast.parse((SRC / rel).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in names:
                for sub in ast.walk(node):
                    if isinstance(sub, (ast.For, ast.While)):
                        offenders.append(f"{rel}:{node.name}:{sub.lineno}")
    assert not offenders, offenders
    assert "逐次ループ宣言" in (SRC / "engine/energy.py").read_text(encoding="utf-8")


# ================================================================= ラン(合成世界・小)
def test_run_day_default_is_v1_and_energy_is_an_arm():
    from shibuya.engine.run import run_day

    kw = dict(n_agents=60, seed=2, ticks=120)
    base = run_day(**kw)
    v1 = run_day(hunger_model="v1", **kw)
    en = run_day(hunger_model="energy", **kw)
    assert base.hunger_model == "v1" and base.energy == {}
    assert base.final_hash == v1.final_hash
    assert en.final_hash != v1.final_hash
    m = en.run_manifest_fields()
    assert m["hunger_model"] == "energy" and m["energy_rate"] == "eer"
    e = m["energy"]
    assert e["avg_mets"] == 1.379 and e["anchors_md5"] == ANC_MD5
    assert e["mets"]["sleep"] == {"code": "07030", "mets": 1.0}
    for key in ("counts", "census", "balance_kcal", "breakfast_skip", "stage_time_share",
                "meal_start_in_15min"):
        assert key in e
    c = e["census"]
    assert c["intake_kcal"] - c["expenditure_kcal"] == pytest.approx(c["balance_kcal"], abs=1.0)
    assert set(m["intero_crossings"]) >= {"hunger_up", "hunger_down_awake_in_area"}
    assert all(f in en.agents.registry.arrays for f in ENERGY_FIELDS)  # type: ignore[attr-defined]
    with pytest.raises(ValueError):
        run_day(hunger_model="v2", **kw)
    with pytest.raises(ValueError):
        run_day(hunger_model="energy", energy_rate="kcal", **kw)


def test_bmr_arm_runs_and_is_recorded():
    from shibuya.engine.run import run_day

    res = run_day(n_agents=40, seed=2, ticks=60, hunger_model="energy", energy_rate="bmr")
    assert res.run_manifest_fields()["energy"]["rate"] == "bmr"


def test_cli_default_hunger_model_is_energy():
    from shibuya import cli

    assert cli.CLI_DEFAULT_HUNGER_MODEL == "energy"
    res = cli.run(n_agents=40, seed=2, world_dir=None, ticks=60, use_population=False)
    assert res.hunger_model == "energy"
    res1 = cli.run(n_agents=40, seed=2, world_dir=None, ticks=60, use_population=False,
                   hunger_model="v1")
    assert res1.hunger_model == "v1" and res1.final_hash != res.final_hash
