"""D-56 就寝抑止(ユーザー決定 (a)・2026-09-10)のテスト。

正典・根拠
- PENDING D-56 / 答申 ``docs/research/v2-c7-fix-research.md`` §2。C7 本番(390,067 体)で
  深夜 0〜5 時の LLM 呼が昼と同数(毎時 107,520=按分上限)出ていた=**寝ている住民に
  移動/購入を選ばせていた**。
- 規則: ``activity == Activity.SLEEPING`` の個体の起床候補は、アービタに入る前に落とす。
  例外は候補の**源**で決まる(``WakeCandidates.sleep_exempt``): 計画境界(``PLAN_*`` の
  4 条件=眠りから覚める境界を含む)・顕著行為・会話ターン。
- 東京都 平日の起床率 a(h)(令和 3 年社会生活基本調査 第 4-1 表): 0 時 20.5% / 1 時 11.1 /
  2 時 5.7 / 3 時 3.5 / 4 時 5.3 / 5 時 15.3 / 6 時 40.7 / 12〜19 時 97.8〜98.9。
  **一律に掛けない**(交替制勤務 12.9%)。ここでは深夜の呼数の**照合**にだけ使う。
- 診断は不応期の ``suppressed`` とは**別列** ``sleep_suppressed``。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import N_WAKE_CONDITIONS, Activity, WakeCondition
from shibuya.core.types import EventClass
from shibuya.engine.arbiter import Arbiter, WakeCandidates, arbitrate
from shibuya.engine.run import DIAG_RUN_COLUMNS, run_day
from shibuya.world.state import World

SALT = b"\x0d\x56\x0d\x56"
N = 8


def _cands(agents, conds, *, exempt=None, since=0) -> WakeCandidates:
    from shibuya.agents.state import WAKE_CONDITION_CLASS

    a = np.asarray(agents, dtype=np.int64)
    c = np.asarray(conds, dtype=np.int8)
    cls = np.asarray([int(WAKE_CONDITION_CLASS[int(x)]) for x in c], dtype=np.int64)
    ex = np.zeros(a.size, dtype=bool) if exempt is None else np.asarray(exempt, dtype=bool)
    return WakeCandidates(a, c, cls, np.full(a.size, int(since), dtype=np.int64), ex)


def _asleep(*ids) -> np.ndarray:
    m = np.zeros(N, dtype=bool)
    for i in ids:
        m[int(i)] = True
    return m


# ================================================================= (i) 抑止そのもの
def test_interoception_and_cell_change_do_not_wake_a_sleeping_agent():
    """内受容閾値・セル動的ブロックの候補は、就寝中の個体では呼にならない。"""
    c = _cands(
        [0, 1], [int(WakeCondition.INTEROCEPTION), int(WakeCondition.CELL_BLOCK)]
    )
    d = arbitrate(c, tick=5, budget=10, run_salt=SALT, asleep=_asleep(0, 1))
    assert d.n_calls == 0
    assert d.n_sleep_suppressed == 2
    assert len(d.deferred) == 0  # 抑止は繰り延べではない(保留に積まない)
    # 起きている個体は同じ候補で呼ばれる=抑止しているのは「寝ていること」だけ
    awake = arbitrate(c, tick=5, budget=10, run_salt=SALT, asleep=np.zeros(N, dtype=bool))
    assert awake.n_calls == 2 and awake.n_sleep_suppressed == 0


def test_the_other_individual_conditions_are_suppressed_too():
    """知人出現・近接入替・被注視・傍受(第2陣)も同じ扱い=源が変化検出なら落とす。"""
    conds = [
        int(WakeCondition.ACQUAINTANCE), int(WakeCondition.PROXIMITY_SWAP),
        int(WakeCondition.BEING_WATCHED), int(WakeCondition.OVERHEARD),
    ]
    d = arbitrate(_cands([0, 1, 2, 3], conds), tick=1, budget=10, run_salt=SALT,
                  asleep=_asleep(0, 1, 2, 3))
    assert d.n_calls == 0 and d.n_sleep_suppressed == 4


# ================================================================= (ii) 例外: 計画境界
@pytest.mark.parametrize(
    "cond",
    [WakeCondition.PLAN_SLEEPING, WakeCondition.PLAN_WORKING,
     WakeCondition.PLAN_GENERAL, WakeCondition.PLAN_TRANSIT],
)
def test_plan_boundaries_still_wake_a_sleeping_agent(cond):
    """**眠りから覚める境界**を含む計画境界 4 条件は就寝中でも通る(例外 (i))。"""
    c = _cands([0], [int(cond)], exempt=[True])
    d = arbitrate(c, tick=300, budget=10, run_salt=SALT, asleep=_asleep(0))
    assert d.n_calls == 1 and d.n_sleep_suppressed == 0
    assert int(d.selected.condition[0]) == int(cond)


def test_a_sleeping_agent_is_woken_by_the_boundary_but_not_by_the_body():
    """同じ体・同じ tick に境界と内受容が立ったら、**境界だけ**が残って 1 呼になる。"""
    c = _cands(
        [0, 0], [int(WakeCondition.PLAN_GENERAL), int(WakeCondition.INTEROCEPTION)],
        exempt=[True, False],
    )
    d = arbitrate(c, tick=420, budget=10, run_salt=SALT, asleep=_asleep(0))
    assert d.n_calls == 1
    assert int(d.selected.condition[0]) == int(WakeCondition.PLAN_GENERAL)
    assert d.n_sleep_suppressed == 1
    assert int(d.merged_per_class.sum()) == 0  # 合流ではなく抑止で消えている


# ================================================================= (iii) 例外: 顕著行為
def test_salient_events_reach_a_sleeping_agent():
    """顕著行為(火事・急病)は就寝中でも起こす(例外 (ii))。

    条件は変化検出と同じ ``CELL_BLOCK`` なので、**条件では区別できない**=源の印
    (``sleep_exempt``)で通す。同じ条件・同じ体でも印の有無で結果が割れることを固定する。
    """
    cond = [int(WakeCondition.CELL_BLOCK)]
    salient = arbitrate(_cands([0], cond, exempt=[True]), tick=90, budget=10,
                        run_salt=SALT, asleep=_asleep(0))
    detected = arbitrate(_cands([0], cond, exempt=[False]), tick=90, budget=10,
                         run_salt=SALT, asleep=_asleep(0))
    assert salient.n_calls == 1 and salient.n_sleep_suppressed == 0
    assert detected.n_calls == 0 and detected.n_sleep_suppressed == 1


def test_conversation_turns_pass_through_even_while_asleep():
    """会話ターンは ``resolve._UNADDRESSABLE`` で就寝中には来ないが、来たら通す。

    片側だけ ``CONVERSING`` が残る事故を作らないため(例外 (iii)・念のため)。
    """
    c = _cands([0], [int(WakeCondition.CONVERSATION_TURN)], exempt=[True])
    d = arbitrate(c, tick=7, budget=10, run_salt=SALT, asleep=_asleep(0))
    assert d.n_calls == 1 and d.n_sleep_suppressed == 0


# ================================================================= (iv) 保留の掃除
def test_pending_candidates_are_dropped_when_the_agent_falls_asleep():
    """繰り延べで保留に積まれた候補も、就寝に入った体の分は同じ規則で落ちる。"""
    arb = Arbiter(n_agents=N, run_salt=SALT, budget=1.0)
    conds = [int(WakeCondition.INTEROCEPTION)] * 4
    d0 = arb.step(0, _cands([0, 1, 2, 3], conds), asleep=np.zeros(N, dtype=bool))
    assert d0.n_calls == 1 and arb.n_pending() == 3  # 3 件が保留へ

    # 次 tick: 保留の 3 体が全員就寝に入った(新規候補は無し)
    d1 = arb.step(1, WakeCandidates.empty(), asleep=_asleep(*d0.deferred.agent_id.tolist()))
    assert d1.n_calls == 0
    assert d1.n_sleep_suppressed == 3
    assert arb.n_pending() == 0, "保留が掃除されていない"
    assert arb.sleep_suppressed_total == 3


def test_refractory_and_sleep_are_counted_in_separate_columns():
    """``suppressed``(不応期)と ``sleep_suppressed``(就寝)は排他=二重計上しない。"""
    ru = np.zeros((N, N_WAKE_CONDITIONS), dtype=np.int32)
    ru[0, int(WakeCondition.INTEROCEPTION)] = 99  # 体 0 は不応期中
    c = _cands([0, 1], [int(WakeCondition.INTEROCEPTION)] * 2)
    d = arbitrate(c, tick=5, budget=10, run_salt=SALT, refractory_until=ru,
                  asleep=_asleep(0, 1))
    # 就寝抑止が**先**なので 2 件とも sleep_suppressed に入り、suppressed は 0
    assert d.n_sleep_suppressed == 2
    assert len(d.suppressed) == 0
    assert int(d.diag[3].sum()) == 0  # DIAG_COLUMNS[3] == "suppressed"


def test_arbitrate_stays_a_pure_function_under_the_sleep_rule():
    """並び順に依存しない(T3 の前提)。抑止を入れても選抜集合・計数は同じ。"""
    rng = np.random.default_rng(56)
    agents = rng.integers(0, N, size=40)
    conds = rng.integers(0, N_WAKE_CONDITIONS, size=40)
    ex = rng.random(40) < 0.3
    c = _cands(agents, conds, exempt=ex, since=-3)
    sl = rng.random(N) < 0.5
    base = arbitrate(c, tick=3, budget=7.0, run_salt=SALT, asleep=sl)
    for _ in range(10):
        idx = rng.permutation(len(c))
        got = arbitrate(c.take(idx), tick=3, budget=7.0, run_salt=SALT, asleep=sl)
        assert got.selected.agent_id.tolist() == base.selected.agent_id.tolist()
        assert got.n_sleep_suppressed == base.n_sleep_suppressed
        assert np.array_equal(got.diag, base.diag)


# ================================================================= ラン全体
NIGHT = dict(n_agents=300, seed=4, ticks=180, checkpoint_every=180, n_cells=16,
             processes=False, population=False, world_dir=None)


def test_a_midnight_window_makes_no_calls_and_the_null_arm_shows_the_bug():
    """tick 0 = 世界内 00:00(``resolve.initialize`` が全員 ``SLEEPING``)。

    既定(D-56 あり)は深夜の 3 時間で呼が 0・帰無腕(``sleep_suppression=False``)は
    上限まで呼ぶ=**D-56 が直した挙動そのもの**。
    """
    on = run_day(**NIGHT)
    off = run_day(**NIGHT, sleep_suppression=False)
    assert on.llm_calls == 0
    assert on.sleep_suppressed_count > 0
    assert off.llm_calls > 0
    assert off.sleep_suppressed_count == 0
    assert on.final_hash != off.final_hash
    assert on.run_manifest_fields()["sleep_suppression"] is True
    assert off.run_manifest_fields()["sleep_suppression"] is False


def test_calls_come_back_once_the_first_plan_boundary_is_crossed():
    """合成日課の最初の境界(起床・tick 300-480)を跨ぐ窓では呼が立つ。"""
    res = run_day(**{**NIGHT, "ticks": 540, "checkpoint_every": 540})
    calls = res.column("calls")
    assert int(calls[:300].sum()) == 0, "境界前に呼が立っている"
    assert int(calls[300:].sum()) > 0, "境界を跨いでも呼が立たない"


def test_calls_by_hour_sums_to_llm_calls():
    """``calls_by_hour``(24 要素)の合計 = ``llm_calls``(C7 受入で a(h) と照合する欄)。"""
    res = run_day(**{**NIGHT, "ticks": 540, "checkpoint_every": 540})
    assert len(res.calls_by_hour) == 24
    assert sum(res.calls_by_hour) == res.llm_calls
    # 診断行の calls 列とも時間帯ごとに一致する
    calls = res.column("calls")
    for h in range(9):
        assert res.calls_by_hour[h] == int(calls[h * 60:(h + 1) * 60].sum())
    assert res.summary().count("呼/時 ") == 1
    assert "診断 sleep_suppressed:" in res.summary()
    assert "sleep_suppressed" in DIAG_RUN_COLUMNS


def test_two_runs_with_the_same_seed_are_bit_identical():
    """決定論(T2)。抑止を入れても同 seed 2 回で checkpoint・診断が一致する。"""
    kw = {**NIGHT, "ticks": 540, "checkpoint_every": 180}
    a = run_day(**kw)
    b = run_day(**kw)
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert a.llm_calls == b.llm_calls
    assert a.calls_by_hour == b.calls_by_hour
    assert a.sleep_suppressed_count == b.sleep_suppressed_count


def test_the_sleeping_population_shrinks_the_night_share_of_the_calls():
    """1 シミュ日: 深夜 0〜5 時の呼の割合が帰無腕より小さくなる(a(h) の向き)。"""
    kw = dict(n_agents=400, seed=2, ticks=1_440, checkpoint_every=1_440, n_cells=25,
              processes=False, population=False, world_dir=None)
    on = run_day(**kw)
    off = run_day(**kw, sleep_suppression=False)
    night_on = sum(on.calls_by_hour[0:6]) / max(1, on.llm_calls)
    night_off = sum(off.calls_by_hour[0:6]) / max(1, off.llm_calls)
    assert night_on < night_off, (night_on, night_off)
    # 起床率 a(h) の 0〜5 時は 3.5〜20.5%=1 日の 25% の窓に呼の 25% は多すぎる
    assert night_off > 0.20, night_off
    assert night_on < 0.10, night_on


def test_the_activity_that_drives_the_rule_is_the_sleeping_one():
    """規則が読むのは ``Activity.SLEEPING`` ただ 1 つ(tick 0 の種の確認込み)。"""
    world = World.synthetic(n_cells=16, seed=1)
    res = run_day(n_agents=64, seed=1, world=world, ticks=30, checkpoint_every=30,
                  processes=False, population=False, world_dir=None)
    act = np.asarray(res.agents.registry.activity)  # type: ignore[attr-defined]
    assert (act == int(Activity.SLEEPING)).all(), "tick 0 の種が変わった(前提の確認)"
    assert res.llm_calls == 0
    assert int(res.column("candidates").sum()) > 0, "候補は出ている(抑止で消えている)"
    assert EventClass.INDIVIDUAL in tuple(EventClass)
