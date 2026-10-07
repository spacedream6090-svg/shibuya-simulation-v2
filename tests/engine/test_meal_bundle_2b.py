"""第2波 §2B: 食事の束の 3 項(切替口つき・既定は旧のまま=指示書 §8-2)。

- 項 1(Q34 (b))``meal_sleep_defer``: 範囲外の既定の食事時刻に W17 で就寝中の体は、起床の時刻へ遅らせ、
  時間帯の窓の中なら食べる(過ぎていれば無し)。
- 項 2(Q35 (a))``home_meal``: 範囲内の自宅の食事行を「予定の実行」としてエンジンが食べさせる。
- 項 3(Q31 (b))``hunger_words``: B5 の空腹の語を 4 段とも描く腕。

検算は答えの分かっている合成の場面で先に行う(指示書 §0-1)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentKind, AgentState
from shibuya.agents.weekly import ACTIVITY_WORDS, N_DAYS, PLACE_WORDS, WeeklySchedule
from shibuya.engine import energy as E
from shibuya.engine import resolve as R
from shibuya.engine.change_detect import ChangeDetector
from shibuya.perception import templates as T
from shibuya.perception.renderer import HUNGER_WORDS_MODES, Renderer, check_hunger_words
from shibuya.world.state import World

ANC, ANC_MD5 = E.load_anchors()
SLEEP, PREP, WORK, EAT = (ACTIVITY_WORDS.index(w) for w in ("就寝", "支度", "勤務", "食事"))
HOME, OUT, EATERY = (PLACE_WORDS.index(w) for w in ("自宅", "域外", "飲食店"))
B_MIN, L_MIN, D_MIN = 449, 735, 1158  # 既定の時刻(朝 7:29・昼 12:15・夕 19:18)


def model() -> E.EnergyModel:
    return E.EnergyModel(ANC, ANC_MD5)


def weekly(rows, n_agents: int) -> WeeklySchedule:
    """``(体, 開始分, 終了分, 活動, 場所)`` の行 → 月曜(day 0)だけの週次表。"""
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


# 合成の体(指示書の検算): 0=7:29 に就寝中・8:00 に起床 / 1=11:30 に起床(朝の窓を過ぎる)/
# 2=7:00 に起床済み / 3=就寝の行が 2 本つながる(5:00・8:20 に起床)/ 4=W17 の行なし
ROWS_SLEEP = [
    (0, 0, 480, SLEEP, HOME), (0, 480, 600, PREP, HOME),
    (1, 0, 690, SLEEP, HOME), (1, 690, 900, WORK, OUT),
    (2, 0, 420, SLEEP, HOME), (2, 420, 600, PREP, HOME),
    (3, 0, 300, SLEEP, HOME), (3, 300, 500, SLEEP, HOME), (3, 500, 600, PREP, HOME),
]
N_SLEEP = 5


def run_out_of_area(oom: E.OutOfAreaMeals, transit: np.ndarray | None = None, ticks: int = 1440,
                    transit_fn=None):
    """全 tick で ``due_with_deferred`` を引き、食べた ``(体, tick, 時間帯, 行由来, 遅らせた)`` を返す。"""
    got = []
    n = N_SLEEP if transit is None else transit.size
    ts = np.full(n, 2, dtype=np.int8) if transit is None else transit
    for t in range(ticks):  # テストの道具(本番の経路ではない)
        cur = transit_fn(t) if transit_fn is not None else ts
        ids, slots, fr, dfr = oom.due_with_deferred(t, cur)
        got += list(zip(ids.tolist(), [t] * ids.size, slots.tolist(), fr.tolist(), dfr.tolist()))
    return sorted(got)


# ================================================================= 項 1: 起床の分
def test_w17_wake_minute_reads_the_sleep_row_and_chains_consecutive_rows():
    w = weekly(ROWS_SLEEP, N_SLEEP)
    a = np.arange(N_SLEEP)
    got = E.w17_wake_minute(w, N_SLEEP, 0, a, np.full(N_SLEEP, B_MIN))
    assert got.tolist() == [480, 690, -1, 500, -1]
    # 昼の既定の時刻にはだれも寝ていない
    assert E.w17_wake_minute(w, N_SLEEP, 0, a, np.full(N_SLEEP, L_MIN)).tolist() == [-1] * N_SLEEP
    # 行の境目ちょうど(8:00)は起きている(終了分は含まない)
    assert E.w17_wake_minute(w, N_SLEEP, 0, np.array([0]), np.array([480])).tolist() == [-1]
    # 行の重なり(就寝 0〜1156 の途中 7:00 に支度の行が始まる)=次の行の開始で起きる
    wo = weekly([(0, 0, 1156, SLEEP, HOME), (0, 420, 450, PREP, HOME), (0, 450, 1440, WORK, OUT)], 1)
    assert E.w17_wake_minute(wo, 1, 0, np.array([0]), np.array([300])).tolist() == [420]
    assert E.w17_wake_minute(wo, 1, 0, np.array([0]), np.array([B_MIN])).tolist() == [-1]
    # W17 が無い
    assert E.w17_wake_minute(None, N_SLEEP, 0, a, np.full(N_SLEEP, B_MIN)).tolist() == [-1] * N_SLEEP


# ================================================================= 項 1: 予定の検算
def test_sleep_defer_on_moves_the_breakfast_to_the_wake_time_inside_the_window():
    w = weekly(ROWS_SLEEP, N_SLEEP)
    got = run_out_of_area(E.OutOfAreaMeals(model(), N_SLEEP, 1440, weekly=w, sleep_defer="on"))
    breakfast = {a: (t, d) for a, t, s, fr, d in got if s == E.SLOT_BREAKFAST}
    assert breakfast == {
        0: (480, True),   # 7:29 に就寝中・8:00 に起床 → 8:00 に朝食
        # 1: 11:30 に起床(朝の窓 5:00〜10:59 を過ぎる)→ 朝食なし
        2: (B_MIN, False),  # 7:00 に起床済み → 7:29 に朝食(旧と同じ)
        3: (500, True),   # 就寝の行 2 本 → 8:20 に朝食
        4: (B_MIN, False),  # W17 の行なし → 旧と同じ
    }
    # 昼・夕は全員が既定の時刻(だれも寝ていない)
    for slot, minute in ((E.SLOT_LUNCH, L_MIN), (E.SLOT_DINNER, D_MIN)):
        assert sorted(a for a, t, s, fr, d in got if s == slot and t == minute and not d) == list(range(N_SLEEP))


def test_sleep_defer_off_is_the_old_schedule():
    w = weekly(ROWS_SLEEP, N_SLEEP)
    old = run_out_of_area(E.OutOfAreaMeals(model(), N_SLEEP, 1440, weekly=w))
    off = run_out_of_area(E.OutOfAreaMeals(model(), N_SLEEP, 1440, weekly=w, sleep_defer="off"))
    assert old == off
    assert sorted(a for a, t, s, fr, d in off if s == E.SLOT_BREAKFAST and t == B_MIN) == list(range(N_SLEEP))
    assert not any(d for *_, d in off)
    # due(3 本)は due_with_deferred の先頭 3 本と同じ
    oom = E.OutOfAreaMeals(model(), N_SLEEP, 1440, weekly=w)
    ts = np.full(N_SLEEP, 2, dtype=np.int8)
    for t in (B_MIN, L_MIN, D_MIN, 480):
        a3 = oom.due(t, ts)
        a4 = E.OutOfAreaMeals(model(), N_SLEEP, 1440, weekly=w).due_with_deferred(t, ts)
        for x, y in zip(a3, a4[:3]):
            np.testing.assert_array_equal(x, y)
    with pytest.raises(ValueError):
        E.OutOfAreaMeals(model(), N_SLEEP, 1440, weekly=w, sleep_defer="yes")


def test_invariants_awake_inside_window_and_once_per_slot():
    """on のとき: 食事はどれも W17 で起きている時刻・遅らせた食事は窓の中・同じ時間帯に 2 回食べない。"""
    rng = np.random.default_rng(3)
    rows = []
    n = 400
    for a in range(n):  # テストの道具: 就寝の終わりと食事行を乱数で置く
        wake = int(rng.integers(240, 800))
        rows.append((a, 0, wake, SLEEP, HOME))
        rows.append((a, wake, min(1440, wake + 60), PREP, HOME))
        if rng.random() < 0.3 and wake + 60 < 1380:
            rows.append((a, wake + 60, wake + 90, EAT, OUT))
        if rng.random() < 0.3:
            rows.append((a, 1380, 1440, SLEEP, HOME))
    w = weekly(rows, n)
    oom = E.OutOfAreaMeals(model(), n, 1440, weekly=w, sleep_defer="on")
    got = run_out_of_area(oom, transit=np.full(n, 2, dtype=np.int8))
    a = np.asarray([g[0] for g in got])
    t = np.asarray([g[1] for g in got])
    s = np.asarray([g[2] for g in got])
    d = np.asarray([g[4] for g in got])
    assert d.any() and (~d).any()
    # (i) 食べた時刻に W17 で就寝中の体は居ない
    assert (E.w17_wake_minute(w, n, 0, a, t) < 0).all()
    # (ii) 遅らせた食事は時間帯の窓の中
    for slot, key in enumerate(("breakfast", "lunch", "dinner")):
        lo, hi = E.MEAL_WINDOWS_MIN[key]
        sel = d & (s == slot)
        assert ((t[sel] >= lo) & (t[sel] < hi)).all()
    # (iii) 同じ時間帯に 2 回食べない(既定の時刻と起床時の二重なし)
    pairs = list(zip(a.tolist(), s.tolist()))
    assert len(pairs) == len(set(pairs))
    # 件数の閉じ: 仕掛けた = 食べた遅らせ + 起床時に域外でなかった(0)+ 窓を過ぎた
    assert oom.n_armed == int(d.sum()) + oom.n_deferred_not_out + oom.n_skipped_past_window
    assert oom.n_deferred_not_out == 0


def test_only_bodies_out_of_area_at_the_default_time_are_deferred():
    """遅らせるのは既定の時刻に域外に居た体だけ(旧で食事が置かれた体)・起床時に範囲内なら食べない。"""
    w = weekly(ROWS_SLEEP, N_SLEEP)

    def ts(t):
        x = np.full(N_SLEEP, 2, dtype=np.int8)
        if t < 470:
            x[0] = 0  # 体 0 は 7:29 に範囲内 → 仕掛けない(8:00 に域外でも食べない)
        if t >= 490:
            x[3] = 0  # 体 3 は 8:10 に範囲内へ → 8:20 の起床時に域外でない → 食べない
        return x

    oom = E.OutOfAreaMeals(model(), N_SLEEP, 1440, weekly=w, sleep_defer="on")
    got = run_out_of_area(oom, transit_fn=ts)
    breakfast = sorted(a for a, t, s, fr, d in got if s == E.SLOT_BREAKFAST)
    assert breakfast == [2, 4]
    assert oom.n_deferred_not_out == 1  # 体 3
    assert oom.n_skipped_past_window == 1  # 体 1
    # 既定の時刻に域外で就寝中だった体=1 と 3(体 0 は範囲内・2 と 4 は起きている)
    assert oom.defer_summary()["armed_out_of_area_at_default"] == 2


def _bodies(n: int, *, transit: int) -> tuple[AgentState, E.EnergyLayer]:
    a = AgentState(n, energy_columns=True)
    lay = E.EnergyLayer(model=model(), n_agents=n)
    with a.writable():
        a.age[:] = 30
        a.sex[:] = np.arange(n) % 2
        a.transit_state[:] = transit
        a.activity[:] = int(Activity.IDLE)
    R.initialize_energy(a, lay, seed=5)
    return a, lay


def test_three_meal_day_still_closes_to_zero_with_deferred_breakfast():
    """範囲外の体は METs=基準日の平均 → 1 日の消費=EER。3 食(比の和 1.0)なら収支 0。遅らせても同じ。"""
    w = weekly(ROWS_SLEEP, N_SLEEP)
    for mode in ("off", "on"):
        a, lay = _bodies(N_SLEEP, transit=2)
        lay.out_of_area = E.OutOfAreaMeals(lay.model, N_SLEEP, 1440, weekly=w, sleep_defer=mode)
        with a.writable():
            a.energy_balance[:] = 0.0
        for t in range(1440):  # テストの道具
            R.advance_body(a, t, lay)
            ids, slots, fr, dfr = lay.out_of_area.due_with_deferred(t, a.transit_state)
            if ids.size:
                R.energy_out_of_area_meal(a, lay, ids, slots, fr, t, deferred=dfr)
        eer = a.eer_kcal.astype(np.float64)
        bal = a.energy_balance.astype(np.float64)
        three = (lay.meal_bits & 7) == 7
        np.testing.assert_allclose(bal[three] / eer[three], 0.0, atol=2e-3)
        if mode == "on":
            assert not three[1]  # 体 1 は朝食なし=2 食 → 収支は朝の比ぶん負
            share_b = lay.model.meal_share_for_slot(a.age[1:2], a.sex[1:2], np.array([0]))[0]
            assert bal[1] / eer[1] == pytest.approx(-share_b, abs=2e-3)
            assert lay.counts["meals_out_deferred"] == 2  # 体 0・3
            assert lay.counts["meals_out_default"] == 3 * N_SLEEP - 1
        else:
            assert three.all() and "meals_out_deferred" not in lay.counts


# ================================================================= 項 2: 自宅の食事行
ROWS_HOME = [
    (0, 0, 400, SLEEP, HOME), (0, 420, 450, EAT, HOME),     # 自宅が範囲内・自宅に居る → 食べる
    (1, 0, 400, SLEEP, HOME), (1, 420, 450, EAT, HOME),     # 自宅が範囲内・外出中 → 食べない
    (2, 0, 400, SLEEP, HOME), (2, 420, 450, EAT, HOME),     # 自宅が範囲外 → 対象外(K9 の側)
    (3, 0, 400, SLEEP, HOME), (3, 420, 450, EAT, EATERY),   # 飲食店の食事行 → 対象外
    (4, 0, 400, SLEEP, HOME), (4, 420, 450, EAT, HOME),     # 自宅に居るが就寝中 → 食べない
]
HOME_CELL = np.array([5, 5, -1, 5, 5])


def _home_scene():
    a, lay = _bodies(5, transit=0)
    with a.writable():
        a.cell[:] = [5, 6, 5, 5, 5]
        a.activity[4] = int(Activity.SLEEPING)
        a.since_meal_kcal[:] = 1500.0
        a.energy_balance[:] = 0.0
        a.money[:] = 3_000
    hm = E.HomeMeals(5, 1440, weekly(ROWS_HOME, 5), HOME_CELL)
    lay.home_meals = hm
    return a, lay, hm


def test_home_meal_rows_are_only_meal_at_home_with_home_in_area():
    _a, _lay, hm = _home_scene()
    assert sorted(hm.agent.tolist()) == [0, 1, 4]
    assert hm.tick.tolist() == [420, 420, 420]
    assert hm.slot.tolist() == [E.SLOT_BREAKFAST] * 3
    assert E.HomeMeals(5, 1440, None, HOME_CELL).n_rows == 0


def test_home_meal_eats_only_at_home_and_awake_once_per_row():
    a, lay, hm = _home_scene()
    eaten = []
    for t in range(1440):  # テストの道具
        ids, slots = hm.due(t, a.transit_state, a.cell, a.activity)
        if ids.size:
            R.energy_home_meal(a, lay, ids, slots, t)
            eaten += [(int(i), t) for i in ids]
    assert eaten == [(0, 420)]  # 1 行 1 回・自宅に居ない体(1)・就寝中の体(4)には起きない
    assert hm.summary() == {"rows": 3, "agents_with_rows": 3, "not_at_home": 1, "asleep": 1}
    assert lay.counts["meals_home_plan"] == 1 and lay.counts["meals_in_area"] == 0
    assert int(lay.meal_start_in.sum()) == 0 and int(lay.meal_start_home[420 // 15]) == 1
    assert int(lay.meal_bits[0]) == 1 and int(lay.n_meals[0]) == 1
    eer = float(a.eer_kcal[0])
    share = lay.model.meal_share_for_slot(a.age[:1], a.sex[:1], np.array([0]))[0]
    assert float(a.energy_balance[0]) == pytest.approx(share * eer, rel=1e-5)
    assert float(a.since_meal_kcal[0]) == 0.0 and float(a.since_meal_kcal[1]) == 1500.0
    assert lay.summary(a)["home_meal"]["rows"] == 3


def test_home_meal_moves_no_money_or_goods_only_the_four_energy_fields():
    """予定の実行は金と物を動かさない=書き換える欄は since_meal・収支・hunger・hunger_stage の 4 本だけ。"""
    a, lay, hm = _home_scene()
    names = list(a.registry)
    assert "money" in names and "since_meal_kcal" in names
    before = {k: np.array(a.registry.field(k), copy=True) for k in names}
    ids, slots = hm.due(420, a.transit_state, a.cell, a.activity)
    R.energy_home_meal(a, lay, ids, slots, 420)
    changed = {k for k, v in before.items() if not np.array_equal(v, a.registry.field(k))}
    assert changed <= {"since_meal_kcal", "energy_balance", "hunger", "hunger_stage"}
    assert "money" not in changed and int(a.money.sum()) == 15_000
    # 引数に世界・台帳を取らない(=店・棚・席に触れる経路が無い)
    import inspect
    assert set(inspect.signature(R.energy_home_meal).parameters) == {"agents", "energy", "agent_id", "slots", "tick"}


def test_home_meal_itself_adds_no_interoception_wake():
    """自宅の食事は hunger_stage も合わせる=内受容の下げ跨ぎ(起床)を作らない。店の食事の口は作る(対照)。"""
    w = World.synthetic(n_cells=9, seed=1)
    for how in ("home", "restaurant"):
        a, lay, hm = _home_scene()
        with a.writable():
            a.since_meal_kcal[:] = 2.0 * a.eer_kcal / 3.0  # とても空腹
            a.hunger[:] = lay.model.hunger_copy(lay.model.stage_of(a.since_meal_kcal, a.eer_kcal))
            a.hunger_stage[:] = 3
        det = ChangeDetector(a.n, w.n_cells)
        det.detect(w, a, tick=419)
        if how == "home":
            ids, slots = hm.due(420, a.transit_state, a.cell, a.activity)
            R.energy_home_meal(a, lay, ids, slots, 420)
        else:
            with a.writable():
                R._energy_meal(a.registry, np.array([0]), 420, lay, kind="meal_in")
        res = det.detect(w, a, tick=420)
        woke = 0 in res.b5_wake_agents.tolist()
        assert woke is (how == "restaurant")


def test_home_meal_needs_a_valid_mode():
    assert E.check_home_meal("off") == "off" and E.check_home_meal("plan") == "plan"
    with pytest.raises(ValueError):
        E.check_home_meal("on")
    assert E.DEFAULT_HOME_MEAL == "off" and E.DEFAULT_MEAL_SLEEP_DEFER == "off"


# ================================================================= 項 3: B5 の空腹の語
def _b5(hunger: list[int], mode: str) -> list[str]:
    a = AgentState(len(hunger), energy_columns=True)
    w = World.synthetic(n_cells=4, seed=1)
    with a.writable():
        a.cell[:] = 0
        a.kind[:] = AgentKind.VISITOR
        a.hunger[:] = hunger
        a.fatigue[:] = 0
        a.thermal[:] = 0
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=7, hunger_words=mode)
    return [r.render(i, 760, 3).blocks["B5"].decode("utf-8").split("\n")[0] for i in range(len(hunger))]


def test_all_draws_the_four_words_and_hungry_is_the_old_rule():
    words = [T.HUNGER_ITEM_TEMPLATE.format(word=x) for x in T.HUNGER_WORDS]
    got = _b5([1, 5, 8, 10], "all")
    assert got == [f"[B5 内受容] {x}" for x in words]
    old = _b5([1, 5, 8, 10], "hungry")
    assert "体調に変わりはありません" in old[0] and "体調に変わりはありません" in old[1]
    assert old[2:] == [f"[B5 内受容] {words[2]}", f"[B5 内受容] {words[3]}"]
    # 語は 4 段のどれか 1 つだけ
    for line in got:
        assert sum(line.count(f"いま{x}です") for x in T.HUNGER_WORDS) == 1
    assert HUNGER_WORDS_MODES == ("hungry", "all") and check_hunger_words("all") == "all"
    with pytest.raises(ValueError):
        check_hunger_words("full")


#: 参照場面(``energy_columns`` のラン・語彙 v3)の prompt_hash=HEAD 01b6f5b の src で計算した値(空腹の写し 1/5/8/10)。
REF_ENERGY_SCENE_HASH = {
    1: "67b33cd0984d80b3bdd5380a10aa677d76305a30ce1147b442059f7ca64c9827",
    5: "67b33cd0984d80b3bdd5380a10aa677d76305a30ce1147b442059f7ca64c9827",
    8: "177fb643e2ab24661bb4384368276328e9d0b337b58368fc459f78bdabf60f6c",
    10: "33c6be1841d799a17f33ed580e7bdbc262d967f8903834eb6280619d6cfd0f80",
}


def _ref_scene(hunger: int, **kw):
    w = World.synthetic(n_cells=9, seed=2)
    a = AgentState(12, energy_columns=True)
    g = np.random.default_rng(11)
    with a.writable():
        a.cell[:] = g.integers(0, 9, size=12)
        a.xy[:] = g.uniform(0.0, 80.0, size=(12, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 5_000
        a.hunger[:] = hunger
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=13, vocab_version="v3", **kw)
    r.prepare_tick(750)
    return r.render(0, tick=750, wake_reason=3)


def test_hungry_keeps_the_reference_scene_prompt_hash_and_all_moves_only_below_hungry():
    for h, want in REF_ENERGY_SCENE_HASH.items():
        assert _ref_scene(h).prompt_hash == want
        assert _ref_scene(h, hunger_words="hungry").prompt_hash == want
        got = _ref_scene(h, hunger_words="all")
        assert (got.prompt_hash == want) is (h >= 8)  # 空腹以上は同じ文・満腹/ふつうだけ動く
        if h < 8:
            base = _ref_scene(h)
            assert [b for b in got.blocks if got.blocks[b] != base.blocks[b]] == ["B5"]


def test_all_keeps_the_individual_blocks_within_budget():
    """all で 1,000 描画: 個体の群(B5+B6)が 300 tok 以内・各ブロックも予算内(B0 は既知の超過)。"""
    n = 1_000
    w = World.synthetic(n_cells=32, seed=3)
    a = AgentState(n, energy_columns=True)
    g = np.random.default_rng(3)
    with a.writable():
        a.cell[:] = g.integers(0, 32, size=n)
        a.xy[:] = g.uniform(0.0, 100.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = g.integers(0, 8_000, size=n)
        a.hunger[:] = np.asarray(E.HUNGER_STAGE_VALUES)[g.integers(0, 4, size=n)]
        a.fatigue[:] = g.integers(0, 11, size=n)
        a.thermal[:] = g.integers(0, 11, size=n)
        a.activity[:] = g.integers(0, 8, size=n)
        a.last_result[:] = g.integers(0, 18, size=n)
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=11, hunger_words="all")
    ticks = g.integers(0, 1_440, size=n)
    drawn = 0
    for i in range(n):  # テストの道具
        out = r.render(i, int(ticks[i]), wake_reason=int(i % 11))
        assert out.within_group_budgets()
        for b, v in out.tokens_est.items():
            if b != "B0":
                assert v <= T.BLOCK_TOKEN_BUDGET[b], (b, v)
        b5 = out.blocks["B5"].decode("utf-8")
        k = sum(b5.count(f"いま{x}です") for x in T.HUNGER_WORDS)
        assert k <= 1
        drawn += k
    assert drawn == n  # 4 段とも描く=全員に 1 つ


# ================================================================= ランの結線(実資産があれば)
WORLD = "data/world/v2"


@pytest.mark.skipif(not __import__("pathlib").Path(WORLD, "w17_schedule.parquet").exists(),
                    reason="実資産(W17)が無い")
def test_run_wiring_defaults_are_old_and_switches_reach_the_run():
    from shibuya import cli
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine.run import _resolve_population

    kw = dict(n_agents=1500, seed=1, world_dir=WORLD, vocab_version="v3")
    base = cli.run(**kw)
    old = cli.run(meal_sleep_defer="off", home_meal="off", hunger_words="hungry", **kw)
    assert (base.final_hash, base.llm_calls) == (old.final_hash, old.llm_calls)
    m = base.run_manifest_fields()
    assert (m["meal_sleep_defer"], m["home_meal"], m["hunger_words"]) == ("off", "off", "hungry")
    assert "meals_out_deferred" not in base.energy["counts"] and "home_meal" not in base.energy

    # 項 1: 食べた範囲外の食事はどれも W17 で起きている時刻(記録して検査)
    eaten: list[tuple[np.ndarray, int]] = []
    orig = R.energy_out_of_area_meal

    def spy(agents, energy, agent_id, slots, from_row, tick, deferred=None):
        # 項 1 が置く食事=既定の時刻と遅らせた食事(W17 の食事行由来は項 1 の外=W17 の行の重なりは別に数える)
        eaten.append((np.asarray(agent_id)[~np.asarray(from_row, dtype=bool)].copy(), int(tick)))
        return orig(agents, energy, agent_id, slots, from_row, tick, deferred=deferred)

    R.energy_out_of_area_meal = spy
    try:
        on = cli.run(meal_sleep_defer="on", **kw)
    finally:
        R.energy_out_of_area_meal = orig
    assert on.final_hash != base.final_hash
    assert on.run_manifest_fields()["meal_sleep_defer"] == "on"
    assert on.energy["counts"]["meals_out_deferred"] > 0
    sd = on.energy["out_of_area_schedule"]["sleep_defer"]
    assert sd["armed_out_of_area_at_default"] == (
        on.energy["counts"]["meals_out_deferred"] + sd["skipped_wake_past_window"]
        + sd["deferred_not_out_of_area_at_wake"]
    )
    pop = _resolve_population(None, WORLD, 1500, 1, 10**9)
    w = load_weekly(WORLD).restrict_to(pop.source_agent_id)
    a = np.concatenate([x for x, _ in eaten])
    t = np.concatenate([np.full(x.size, tk) for x, tk in eaten])
    assert a.size == on.energy["counts"]["meals_out_default"]
    assert (E.w17_wake_minute(w, 1500, 0, a, t) < 0).all()

    # 項 2: plan で自宅の食事が起き、照合の件数(範囲内)とは別に数える
    home = cli.run(home_meal="plan", **kw)
    hm = home.energy["home_meal"]
    assert hm["rows"] > 0 and home.energy["counts"].get("meals_home_plan", 0) == hm["rows"] - hm["not_at_home"] - hm["asleep"]
    assert sum(hm["meal_start_home_15min"]) == home.energy["counts"].get("meals_home_plan", 0)

    # 項 3: all は描画だけを変える(mock は B5 を読まない=final は同じ)
    allw = cli.run(hunger_words="all", **kw)
    assert (allw.final_hash, allw.llm_calls) == (base.final_hash, base.llm_calls)
    assert allw.run_manifest_fields()["hunger_words"] == "all"


def test_cli_has_the_three_switches_with_old_defaults():
    from shibuya import cli

    src = (__import__("pathlib").Path("src/shibuya") / "cli.py").read_text(encoding="utf-8")
    for flag, dest in (("--meal-sleep-defer", "meal_sleep_defer"), ("--home-meal", "home_meal"),
                       ("--hunger-words", "hunger_words")):
        assert f'"{flag}"' in src and f"{dest}=str(args.{dest})" in src
    # 既定(argparse の default)は旧の値
    for flag, default in (("--meal-sleep-defer", "off"), ("--home-meal", "off"), ("--hunger-words", "hungry")):
        i = src.index(f'"{flag}"')
        assert f'default="{default}"' in src[i:i + 200]
    assert callable(cli.main)


# ================================================================= 検収後の追加(§2B の直し)
def test_consecutive_sleep_rows_are_read_as_one_sleep():
    """就寝 0:00〜7:40 と 7:40〜8:20 の 2 本: 7:29 は 1 本目の中 → 連鎖して 8:20 に起床(つながないと 7:40)。"""
    w = weekly([(0, 0, 460, SLEEP, HOME), (0, 460, 500, SLEEP, HOME), (0, 500, 600, PREP, HOME)], 1)
    assert E.w17_wake_minute(w, 1, 0, np.array([0]), np.array([B_MIN])).tolist() == [500]
    got = run_out_of_area(E.OutOfAreaMeals(model(), 1, 1440, weekly=w, sleep_defer="on"),
                          transit=np.full(1, 2, dtype=np.int8))
    assert [(t, d) for a, t, s, fr, d in got if s == E.SLOT_BREAKFAST] == [(500, True)]


@pytest.mark.parametrize("wake, want", [(659, [(659, True)]), (660, [])])
def test_breakfast_window_edge_is_fixed(wake, want):
    """窓は [5:00, 11:00): 10:59 に起床 → 10:59 に朝食・11:00 に起床 → 朝食なし。"""
    w = weekly([(0, 0, wake, SLEEP, HOME), (0, wake, 900, PREP, HOME)], 1)
    oom = E.OutOfAreaMeals(model(), 1, 1440, weekly=w, sleep_defer="on")
    got = run_out_of_area(oom, transit=np.full(1, 2, dtype=np.int8))
    assert [(t, d) for a, t, s, fr, d in got if s == E.SLOT_BREAKFAST] == want
    assert oom.n_skipped_past_window == (1 if not want else 0)


def test_template_fingerprint_follows_the_drawn_hunger_stage():
    """all の腕は描画に使った段の下限 0 で文面の指紋を計算する。既定(hungry)と v1 のランは凍結値のまま。"""
    frozen = T.template_sha256()
    assert T.template_sha256(hunger_draw_min_stage=None) == frozen
    assert T.template_sha256(hunger_draw_min_stage=T.HUNGER_WORD_DRAW_MIN_STAGE) == frozen
    all_sha = T.template_sha256(hunger_draw_min_stage=0)
    assert all_sha != frozen

    def manifest_sha(words: str, model_: str) -> str:
        from shibuya.engine.run import run_day

        res = run_day(n_agents=20, seed=1, ticks=3, hunger_model=model_, hunger_words=words)
        return res.run_manifest_fields()["template_sha256"]

    assert manifest_sha("hungry", "energy") == frozen
    assert manifest_sha("all", "v1") == frozen  # v1 のランは語を描かない
    assert manifest_sha("all", "energy") == all_sha
    # 描画の報告行も同じ指紋
    a = AgentState(2, energy_columns=True)
    w = World.synthetic(n_cells=4, seed=1)
    assert f"template_sha256={all_sha[:16]}" in Renderer(w, a, seed=1, hunger_words="all").report()
    assert f"template_sha256={frozen[:16]}" in Renderer(w, a, seed=1).report()
    assert f"template_sha256={frozen[:16]}" in Renderer(w, AgentState(2), seed=1, hunger_words="all").report()
