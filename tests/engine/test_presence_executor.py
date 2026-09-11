"""D-66 計画実行層(``engine.presence``・第1段)のテスト。

正典: ``docs/design/v2-plan-executor-design.md``(ユーザー承認・第145)。
§2 ブロックの畳み方 / §3 イベントと tick 処理 / §4 LLM との分担 / §5 不変条件 I1-I6 /
§6 帰無腕と expedient / §7 新規テスト候補 14 本。
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentState, AgentKind
from shibuya.agents.weekly import ACTIVITY_WORDS, N_DAYS, PLACE_WORDS, WeeklySchedule
from shibuya.engine import resolve as R
from shibuya.engine.presence import (
    ARRIVAL_SPREAD_MAX_TRAINS,
    FLAG_HAS_PLAN,
    FLAG_HOME_OUT,
    PlanBlocks,
    PlanExecutor,
    _mix64,
)
from shibuya.engine.processes.rail import RailProcess
from shibuya.engine.run import run_day
from shibuya.world.assets import ProcessAssets
from shibuya.world.state import World

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.skipif(
    not (WORLD_DIR / "w17_schedule.parquet").exists(), reason="実世界資産が無い"
)

ACT_SLEEP = ACTIVITY_WORDS.index("就寝")
ACT_WORK = ACTIVITY_WORDS.index("勤務")
ACT_RIDE = ACTIVITY_WORDS.index("乗車")
ACT_REST = ACTIVITY_WORDS.index("休憩")
PK_HOME = PLACE_WORDS.index("自宅")
PK_WORK = PLACE_WORDS.index("職場")
PK_STATION = PLACE_WORDS.index("駅")
PK_OUT = PLACE_WORDS.index("域外")


# ================================================================= 道具
def make_weekly(rows, n_agents: int, day: int = 0) -> WeeklySchedule:
    """``rows`` = ``[(agent_row, start, end, activity, place_kind, target_cell), …]``。"""
    rows = sorted(rows, key=lambda r: (r[0], r[1]))
    counts = np.zeros(n_agents * N_DAYS, dtype=np.int64)
    for r in rows:
        counts[int(r[0]) * N_DAYS + day] += 1
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
        target_cell=np.asarray([r[5] for r in rows], dtype=np.int32),
        seq=np.asarray([i for i in range(len(rows))], dtype=np.int16),
    )


def fake_assets(
    *, lines=("山手線",), departures=(300, 360, 420, 480), platform_cell=0, exits=(1, 2)
) -> ProcessAssets:
    """1 駅・平日のみの最小時刻表 + 方面→線の表 + 駅出口セル。"""
    line_idx, dep = [], []
    for li in range(len(lines)):
        for d in departures:
            line_idx.append(li)
            dep.append(d)
    n = len(dep)
    return ProcessAssets(
        source="test",
        tt_lines=tuple(lines),
        tt_line_idx=np.asarray(line_idx, dtype=np.int16),
        tt_calendar=np.zeros(n, dtype=np.int8),
        tt_direction=np.zeros(n, dtype=np.int16),
        tt_departure_min=np.asarray(dep, dtype=np.int32),
        line_platform_cell=np.full(len(lines), platform_cell, dtype=np.int32),
        # 方面ノード 0 = その線 / 1 = 非鉄道ゲート
        ext_node_line_idx=np.asarray([0, -1], dtype=np.int16),
        station_exit_cell=np.asarray(exits, dtype=np.int32),
    )


def make_world_agents(n: int, n_cells: int = 9, seed: int = 1):
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n, plan_columns=True)
    a.registry.cell[:] = np.arange(n) % n_cells
    a.registry.node[:] = w.assets.cell_rep_node[a.registry.cell]
    a.registry.activity[:] = int(Activity.IDLE)
    a.freeze()
    w.freeze()
    return w, a


def make_layer(
    weekly,
    *,
    n: int,
    home_cell,
    direction=None,
    assets=None,
    n_cells: int = 9,
    ticks: int = 1_440,
    attendance_rate: float = 1.0,
    kind=None,
    with_rail: bool = True,
):
    w, a = make_world_agents(n, n_cells=n_cells)
    pa = assets if assets is not None else fake_assets()
    rail = (
        RailProcess(w, a, pa, master_seed=1, day_index=0, plan_executor=True)
        if with_rail
        else None
    )
    layer = PlanExecutor(
        w,
        a,
        weekly,
        day_index=0,
        home_cell=home_cell,
        direction_node=np.zeros(n, dtype=np.int64) if direction is None else direction,
        kind=np.zeros(n, dtype=np.int64) if kind is None else kind,
        agent_id=np.arange(n, dtype=np.int64),
        rail=rail,
        assets=pa,
        ticks=ticks,
        attendance_rate=attendance_rate,
    )
    return w, a, rail, layer


def census(agents) -> tuple[int, int, int]:
    s = np.asarray(agents.registry.transit_state)
    return (
        int(np.count_nonzero(s == 0)),
        int(np.count_nonzero(s == 1)),
        int(np.count_nonzero(s == 2)),
    )


# ================================================================= ① 乱数を引かない
def test_the_layer_draws_no_random_numbers():
    """①(§7): 層は ``core.rng`` を 1 語も引かない(T4 規模不変・帰無腕とのバイト一致)。"""
    import ast

    src = Path("src/shibuya/engine/presence.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    # docstring の言及は無視して、**実コード**に乱数源が無いことを見る
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert all("rng" not in a.name for a in node.names), ast.dump(node)
        if isinstance(node, ast.ImportFrom):
            assert "rng" not in (node.module or ""), node.module
        if isinstance(node, ast.Name):
            assert node.id not in {"philox", "stream", "default_rng"}, node.id
        if isinstance(node, ast.Attribute):
            assert node.attr not in {"random", "random_raw", "choice", "shuffle"}, node.attr
    # 決定論の実体: 同じ入力から 2 回組んで**イベント列がバイト一致**
    wk = make_weekly(
        [(0, 0, 480, ACT_SLEEP, PK_HOME, -1), (0, 540, 1020, ACT_WORK, PK_WORK, 3)], 4
    )
    home = np.array([-1, -1, 5, 5], dtype=np.int64)
    _, _, _, a1 = make_layer(wk, n=4, home_cell=home)
    _, _, _, a2 = make_layer(wk, n=4, home_cell=home)
    for name in ("ev_tick", "ev_agent", "ev_type", "ev_arg"):
        assert np.array_equal(getattr(a1, name), getattr(a2, name)), name


# ================================================================= ② 帰無腕で旧 checkpoint
@real_data
def test_null_arm_reproduces_the_recorded_checkpoint():
    """②(§7・**退化検査の要**): ``plan_executor=False`` は D-62 時点の golden と一致。

    golden = 実装計画書 §8 D-62 の退化検査行(mock 実資産 5,000 体×1 日・seed 1)。
    """
    from shibuya.cli import run as cli_run  # golden は台帳つきの標準入口で録られている

    res = cli_run(
        n_agents=5_000, seed=1, world_dir=str(WORLD_DIR), plan_executor=False
    )
    assert res.final_hash.startswith("c96baf821c9a046f")
    assert res.run_manifest_fields()["plan_executor"] is False
    assert res.presence_counters == {}
    assert res.conserved and int(res.llm_calls) == 37_111


# ================================================================= ③ T4 規模不変
def test_blocks_are_scale_invariant():
    """③(§7): n 体と n+1 体で、既存の体のブロックが 1 本も動かない。"""
    rows = [
        (0, 0, 480, ACT_SLEEP, PK_HOME, -1),
        (0, 540, 1020, ACT_WORK, PK_WORK, 3),
        (1, 0, 600, ACT_SLEEP, PK_OUT, -1),
        (1, 600, 900, ACT_REST, PK_STATION, -1),
    ]
    wk4 = make_weekly(rows, 4)
    wk5 = make_weekly(rows + [(4, 60, 120, ACT_REST, PK_STATION, -1)], 5)
    ho4 = np.array([True, True, False, False])
    ho5 = np.array([True, True, False, False, True])
    b4 = PlanBlocks.from_weekly(wk4, 0, ho4)
    b5 = PlanBlocks.from_weekly(wk5, 0, ho5)
    k = int(b4.offset[4])
    assert np.array_equal(b4.start, b5.start[:k])
    assert np.array_equal(b4.end, b5.end[:k])
    assert np.array_equal(b4.offset, b5.offset[:5])


# ================================================================= ④ 保存則(全 tick)
def test_rider_conservation_holds_on_every_tick():
    """④(§5 I1): 在圏 + 乗車中 + 域外 = 体数 を**全 tick で**満たす。"""
    n = 30
    rows = []
    for i in range(n):
        rows += [
            (i, 0, 300, ACT_SLEEP, PK_HOME, -1),
            (i, 300, 360, ACT_RIDE, PK_STATION, -1),
            (i, 360 + i, 900, ACT_WORK, PK_WORK, 3),
            (i, 900, 1_440, ACT_SLEEP, PK_HOME, -1),
        ]
    wk = make_weekly(rows, n)
    home = np.where(np.arange(n) % 3 == 0, 4, -1).astype(np.int64)
    _, agents, _, layer = make_layer(wk, n=n, home_cell=home, ticks=960)
    layer.initialize()
    for tick in range(960):
        layer.step(tick)
        layer.step_plan_boundaries(tick)
        assert sum(census(agents)) == n, tick
    assert layer.n_arrivals > 0 and layer.n_departures > 0


# ================================================================= ⑤ 決定論(ラン経由)
@real_data
def test_same_seed_gives_the_same_run_with_the_layer():
    """⑤(§7・T2): 既定腕で同 seed 2 ランが全 checkpoint 一致。"""
    kw = dict(
        n_agents=400,
        seed=3,
        world_dir=str(WORLD_DIR),
        ticks=240,
        checkpoint_every=120,
        renderer="stub",
        conversations=False,
    )
    a = run_day(world=World.load_or_synthetic(WORLD_DIR, n_cells=139, seed=3), **kw)
    b = run_day(world=World.load_or_synthetic(WORLD_DIR, n_cells=139, seed=3), **kw)
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert a.plan_executor is True


# ================================================================= ⑥ 到着が間に合う
def test_arrival_is_never_later_than_the_block_start():
    """⑥(§3 E1): 到着 tick ≤ ブロック開始(間に合う最も遅い便。始発前は始発)。"""
    rows = [
        (0, 0, 300, ACT_SLEEP, PK_OUT, -1),
        (0, 500, 900, ACT_WORK, PK_WORK, 3),  # 便 480 が「間に合う最も遅い便」
        (1, 0, 100, ACT_SLEEP, PK_OUT, -1),
        (1, 100, 200, ACT_WORK, PK_WORK, 3),  # 始発(300)より前 → 始発へ
    ]
    wk = make_weekly(rows, 2)
    _, _, rail, layer = make_layer(wk, n=2, home_cell=np.array([-1, -1]))
    enter = np.asarray(rail.enter_tick)
    assert int(layer.arrival_tick[0]) == int(enter[np.asarray(rail.dep_tick) == 480][0])
    assert int(layer.arrival_tick[0]) <= 500
    # 始発(300)より前に始まり **始発より前に終わる**ブロックには来ない(到着を捨てる)
    assert int(layer.arrival_tick[1]) == int(enter.min())
    assert int(layer.arrival_tick[1]) > 200  # ブロック終了(200)より後 → ARRIVE は出ない
    assert not np.any((layer.ev_agent == 1) & (layer.ev_type == 0))


# ================================================================= ⑦ 日 2〜3 回の出入り
def test_an_outside_resident_enters_and_leaves_two_or_three_times_a_day():
    """⑦(§7): 域外居住者は 1 日に 2〜3 回だけ出入りする(常駐しない)。"""
    rows = [
        (0, 0, 420, ACT_SLEEP, PK_HOME, -1),  # 域外居住 → 自宅は域外
        (0, 420, 480, ACT_RIDE, PK_STATION, -1),
        (0, 480, 720, ACT_WORK, PK_WORK, 3),  # 在圏ブロック 1
        (0, 720, 780, ACT_REST, PK_OUT, -1),  # 域外へ
        (0, 780, 1_020, ACT_WORK, PK_WORK, 3),  # 在圏ブロック 2
        (0, 1_020, 1_440, ACT_SLEEP, PK_HOME, -1),
    ]
    wk = make_weekly(rows, 1)
    _, agents, _, layer = make_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    assert census(agents)[2] == 1  # tick 0 は域外
    for tick in range(1_440):
        layer.step(tick)
    assert layer.n_arrivals == 2
    assert layer.n_departures == 2
    assert census(agents)[2] == 1  # 日末も域外(1,020 で退出)


# ================================================================= ⑧ 非来街日は終日域外
def test_a_visitor_without_a_block_stays_outside_all_day():
    """⑧(§6 E7): その日 在圏ブロックが 0 本の体は**終日域外**(起床率の分母から外れる)。"""
    rows = [(0, 0, 1_440, ACT_SLEEP, PK_OUT, -1)]  # 来街しない日
    wk = make_weekly(rows, 1)
    _, agents, _, layer = make_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    for tick in range(1_440):
        layer.step(tick)
    assert layer.blocks.n_blocks == 0
    assert layer.n_all_day_outside == 1
    assert census(agents) == (0, 0, 1)
    assert layer.n_arrivals == 0


# ================================================================= ⑨ 職場で寝る体が 0
def test_an_outside_resident_never_sleeps_inside_the_stage():
    """⑨(§5 I6): ``home_cell < 0`` の体は就寝境界で**寝ない**(職場で寝る穴が塞がる)。"""
    rows = [
        (0, 0, 480, ACT_WORK, PK_WORK, 3),  # 在圏で働いている
        (0, 480, 1_440, ACT_SLEEP, PK_HOME, -1),  # 自宅(= 域外・セル未解決)で就寝
    ]
    wk = make_weekly(rows, 1)
    _, agents, _, layer = make_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    for tick in range(600):
        layer.step(tick)
        layer.step_plan_boundaries(tick)
    assert layer.n_home_out_slept_inside == 0
    assert int(agents.registry.activity[0]) != int(Activity.SLEEPING)
    assert census(agents)[2] == 1  # 480 に退出して域外


# ================================================================= ⑩ 退出の優先規則
def test_exit_is_deferred_while_conversing_and_interrupts_shopping():
    """⑩(§4): 退出 tick に**会話中は繰り延べ**(≤30 tick)・**買物中/待ち行列は中断**。"""
    rows = [
        (0, 0, 100, ACT_WORK, PK_WORK, 3),
        (1, 0, 100, ACT_WORK, PK_WORK, 3),
        (2, 0, 100, ACT_WORK, PK_WORK, 3),
    ]
    wk = make_weekly(rows, 3)
    _, agents, _, layer = make_layer(wk, n=3, home_cell=np.array([-1, -1, -1]))
    layer.initialize()
    with agents.writable():
        agents.registry.activity[0] = int(Activity.CONVERSING)
        agents.registry.poi_ref[1] = 2
        agents.registry.activity[1] = int(Activity.SHOPPING)
        agents.registry.queue_poi[2] = 3
    layer.step(100)
    assert census(agents) == (1, 0, 2)  # 会話中の 0 だけ残る
    assert layer.n_exit_deferred == 1
    assert layer.n_shopping_interrupted == 1 and layer.n_queue_balked == 1
    assert int(agents.registry.poi_ref[1]) == -1
    assert int(agents.registry.queue_poi[2]) == -1
    # 会話が終われば次の tick で出る
    with agents.writable():
        agents.registry.activity[0] = int(Activity.IDLE)
    layer.step(101)
    assert census(agents) == (0, 0, 3)


def test_a_conversation_that_never_ends_is_forced_out_after_the_limit():
    """⑩-b(§4): 繰り延べ上限 30 tick で**強制退出**(幽霊を残さない)。"""
    wk = make_weekly([(0, 0, 100, ACT_WORK, PK_WORK, 3)], 1)
    _, agents, _, layer = make_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    with agents.writable():
        agents.registry.activity[0] = int(Activity.CONVERSING)
    for tick in range(100, 131):
        layer.step(tick)
    assert census(agents) == (0, 0, 1)
    assert layer.n_exit_forced == 1


# ================================================================= ⑪ 二重到着/二重退出なし
def test_no_double_arrival_and_no_double_departure():
    """⑪(§5 I2/I3): ARRIVE は域外の体だけ・DEPART は在圏の体だけに適用される。"""
    wk = make_weekly(
        [
            (0, 0, 300, ACT_SLEEP, PK_OUT, -1),
            (0, 480, 600, ACT_WORK, PK_WORK, 3),
            (0, 600, 700, ACT_WORK, PK_WORK, 3),
        ],
        1,
    )
    _, agents, _, layer = make_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    # 先に別経路(civic)で引き込んでおく → ARRIVE は捨てられる
    R.rail_arrive(agents, layer.world, np.array([0]), np.array([1]))
    for tick in range(1_440):
        layer.step(tick)
        assert sum(census(agents)) == 1
    assert layer.n_arrive_skipped >= 1
    assert layer.n_arrivals + layer.n_departures <= 2


# ================================================================= ⑫ civic 干渉(I4)
def test_pulled_in_agents_do_not_fire_a_stale_arrival():
    """⑫(§5 I4): 引き込み後に古い ARRIVE が発火しない・押し出しは張り直される。"""
    wk = make_weekly(
        [
            (0, 0, 400, ACT_SLEEP, PK_OUT, -1),
            (0, 480, 1_000, ACT_WORK, PK_WORK, 3),
        ],
        1,
    )
    _, agents, _, layer = make_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    assert layer.candidates_for_pull(0).tolist() == [0]
    R.rail_arrive(agents, layer.world, np.array([0]), np.array([1]))
    layer.notify_pulled_in(np.array([0]), 0)
    for tick in range(0, 470):
        layer.step(tick)
        assert sum(census(agents)) == 1
    assert census(agents)[0] == 1  # 在圏のまま(古い到着で状態が壊れない)
    # 押し出し(civic の退場)→ 次のブロックへ到着を張り直す
    R.rail_depart(agents, np.array([0]), np.array([0]))
    layer.notify_pushed_out(np.array([0]), 470)
    assert layer.n_rearmed == 1
    for tick in range(470, 1_000):
        layer.step(tick)
    assert layer.n_arrivals >= 1


# ================================================================= ⑬ 到着分散
def test_arrival_spread_never_exceeds_capacity_times_the_cap():
    """⑬(§3 E8): 容量ベース backward fill で 1 便が ``定員 × 混雑率上限`` を超えない。"""
    n = 60
    rows = [(i, 0, 400, ACT_SLEEP, PK_OUT, -1) for i in range(n)]
    rows += [(i, 500, 900, ACT_WORK, PK_WORK, 3) for i in range(n)]
    wk = make_weekly(rows, n)
    # 定員 2 人の線を作る(``LINE_CAPACITY_PERSONS`` に無い線名 → 既定 1,200 なので、
    # 便あたりの上限を小さくするために ``capacity100`` を直に縮める)
    pa = fake_assets(departures=(300, 340, 380, 420, 460, 500))
    w, a = make_world_agents(n)
    rail = RailProcess(w, a, pa, master_seed=1, day_index=0, plan_executor=True)
    rail.capacity100 = np.full(rail.dep_tick.size, 4.0)
    rail.cap_pct = np.full(rail.dep_tick.size, 100.0)
    layer = PlanExecutor(
        w, a, wk, day_index=0,
        home_cell=np.full(n, -1, dtype=np.int64),
        direction_node=np.zeros(n, dtype=np.int64),
        kind=np.zeros(n, dtype=np.int64),
        agent_id=np.arange(n, dtype=np.int64),
        rail=rail, assets=pa, ticks=1_440,
    )
    per_train = np.bincount(layer.arrival_train[layer.arrival_train >= 0])
    assert layer.n_spread_moved > 0
    # **先頭の便を除く全便**が ``定員 × 混雑率上限`` を超えない(容量ベース backward fill)
    assert int(per_train[1:].max()) <= 4
    # 先頭の便だけは溢れを受け切る(上限 k=8 便まで送って行き場が無くなった分・E8 の宣言)
    assert int(per_train[0]) == n - 4 * (per_train.size - 1)
    assert ARRIVAL_SPREAD_MAX_TRAINS == 8


# ================================================================= ⑭ derive の畳み方
@real_data
def test_derive_folding_matches_the_parent_verified_counts():
    """⑭(§7): 実 W17(day0)の畳み方が親検証値と合う。

    親検証値(``docs/design/v2-d66-outside-residents-agenda.md`` §1・全 390,067 体):
    **域外居住 346,445 体の在圏ブロック 306,410 本 / うち 0 本の体 85,766**。
    ここでは 5,000 体標本の実測を golden として釘付ける(親が再実行して検収する値)。
    """
    from shibuya.agents.population import load_population, sample_population
    from shibuya.agents.weekly import load_weekly

    full = load_population(WORLD_DIR, n=None, seed=1)
    wk_full = load_weekly(WORLD_DIR)
    ho_full = np.asarray(full.home_cell) < 0
    per_full = PlanBlocks.from_weekly(wk_full, 0, ho_full).blocks_per_agent()
    # **親検証値そのもの**(全 390,067 体・day0・定義 B の集計軸=域外居住者)
    assert int(ho_full.sum()) == 346_445
    assert int(per_full[ho_full].sum()) == 306_410
    assert np.bincount(per_full[ho_full])[:4].tolist() == [85_766, 214_998, 45_631, 50]
    # 5,000 体標本(前後測定に使う縮尺)の実測 golden
    pop = sample_population(full, 5_000, 1)
    wk = wk_full.restrict_to(pop.source_agent_id)
    home_out = np.asarray(pop.home_cell) < 0
    blocks = PlanBlocks.from_weekly(wk, 0, home_out)
    per = blocks.blocks_per_agent()
    assert int(home_out.sum()) == 4_491
    assert blocks.n_blocks == 4_918
    assert int(np.count_nonzero(per == 0)) == 1_107
    assert int(per[home_out].sum()) == 4_077
    assert int(np.count_nonzero(per[home_out] == 0)) == 1_107
    assert int(per[~home_out].sum()) == 841  # 域内居住者の「自宅」行は在圏に数える


# ================================================================= 腕・切替口
def test_native_mode_and_other_exit_modes_are_reserved():
    """§10-1/3: ``mode='native'`` と ``--exit-mode`` の他 2 値は**予約**(NotImplemented)。"""
    wk = make_weekly([(0, 0, 100, ACT_WORK, PK_WORK, 3)], 1)
    with pytest.raises(NotImplementedError):
        PlanBlocks.from_weekly(wk, 0, np.array([True]), mode="native")
    w, a = make_world_agents(1)
    with pytest.raises(NotImplementedError):
        PlanExecutor(w, a, wk, home_cell=np.array([-1]), exit_mode="board_intent")
    with pytest.raises(ValueError):
        PlanExecutor(w, a, wk, home_cell=np.array([-1]), exit_mode="teleport")
    with pytest.raises(ValueError):
        PlanExecutor(w, a, wk, home_cell=np.array([-1]), attendance_rate=1.5)


def test_attendance_rate_removes_a_deterministic_share_of_commuters():
    """§6 E6: ``attendance_rate`` は通勤・通学の一部を**決定論で**終日域外にする。"""
    n = 400
    rows = [(i, 0, 400, ACT_SLEEP, PK_OUT, -1) for i in range(n)]
    rows += [(i, 500, 900, ACT_WORK, PK_WORK, 3) for i in range(n)]
    wk = make_weekly(rows, n)
    kinds = np.where(np.arange(n) % 2 == 0, int(AgentKind.COMMUTER), int(AgentKind.VISITOR))
    home = np.full(n, -1, dtype=np.int64)
    _, _, _, full = make_layer(wk, n=n, home_cell=home, kind=kinds)
    _, _, _, part = make_layer(
        wk, n=n, home_cell=home, kind=kinds, attendance_rate=0.88
    )
    assert int(full.absent.sum()) == 0
    assert 0 < int(part.absent.sum()) < n // 2
    assert not part.absent[kinds == int(AgentKind.VISITOR)].any()  # 来街者は対象外
    # 同じ入力なら同じ体が抜ける(乱数ではない)
    _, _, _, part2 = make_layer(
        wk, n=n, home_cell=home, kind=kinds, attendance_rate=0.88
    )
    assert np.array_equal(part.absent, part2.absent)
    assert part.blocks.n_blocks == full.blocks.n_blocks - int(part.absent.sum())


def test_mix64_matches_the_build_side_definition():
    """``_mix64`` は W17 側(``build.sched``)と**同じ式**(二重定義の機械検査)。"""
    from shibuya.build.sched.w17_schedule import _mix64 as build_mix64

    x = np.arange(64, dtype=np.uint64)
    assert np.array_equal(_mix64(x), build_mix64(x))


def test_plan_flags_are_written_through_resolve():
    """§2: ``plan_flags`` の bit0(域外居住)/bit1(当日在圏予定)が立つ。"""
    wk = make_weekly(
        [(0, 0, 100, ACT_WORK, PK_WORK, 3), (1, 0, 1_440, ACT_SLEEP, PK_OUT, -1)], 2
    )
    _, agents, _, layer = make_layer(wk, n=2, home_cell=np.array([-1, 5]))
    layer.initialize()
    f = np.asarray(agents.registry.plan_flags)
    assert (int(f[0]) & FLAG_HOME_OUT) and (int(f[0]) & FLAG_HAS_PLAN)
    assert not (int(f[1]) & FLAG_HOME_OUT) and not (int(f[1]) & FLAG_HAS_PLAN)


def test_the_synthetic_world_keeps_the_layer_asleep():
    """§6: 合成世界(母集団・週次表なし)では層が立たない=既存テストが無改造で通る。"""
    res = run_day(
        n_agents=40, ticks=5, n_cells=9, renderer="stub", processes=False,
        conversations=False, checkpoint_every=0, population=False,
    )
    assert res.plan_executor is False
    assert res.presence_counters == {}
    assert res.run_manifest_fields()["exit_mode"] == "immediate"


@real_data
def test_summary_line_is_invisible_to_the_c7_parser():
    """§5: 要約 1 行が ``c7lib.parse_run_summary`` の既存正規表現に当たらない。"""
    res = run_day(
        n_agents=200,
        seed=1,
        world=World.load_or_synthetic(WORLD_DIR, n_cells=139, seed=1),
        world_dir=str(WORLD_DIR),
        ticks=120,
        checkpoint_every=0,
        renderer="stub",
        conversations=False,
    )
    text = res.summary()
    assert "計画実行: 域外居住" in text
    line = next(ln for ln in text.splitlines() if "計画実行:" in ln)
    assert re.match(r"^\s*診断\s+(\w+):\s*([0-9,]+)\s*$", line) is None
    assert re.search(r"呼/時\s+((?:\d{2}:\d+\s*)+)", line) is None
    assert re.search(r"起床率/時", line) is None
    assert re.search(r"checkpoint\s+(\d+)\s*点", line) is None
