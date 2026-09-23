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
    RETURN_MIN_AWAY_MIN,
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


def w17_digest(world_dir: Path = WORLD_DIR) -> str:
    """実 W17(``w17_schedule.parquet``)の md5 先頭 12 桁。golden は表ごとに持つ(第170・層2 指摘)。"""
    import hashlib

    p = world_dir / "w17_schedule.parquet"
    if not p.exists():
        return ""
    return hashlib.md5(p.read_bytes()).hexdigest()[:12]


#: 実 W17 の golden(親再実行値・2026-09-12)。キー= parquet md5 先頭 12 桁。
#: 11a7129beaea = W17 v1(週 7 日・第 1 弾・w17v1_backup/)/ 3113e9ba7abb = W17 v2(1 日・本番 第 2 回・第168 昇格)。
W17_GOLDEN = {
    "11a7129beaea": {
        "null_arm_final": "c96baf821c9a046f", "null_arm_llm_calls": 37_111,
        "v1_outside_blocks": 306_410, "v1_outside_dist": [85_766, 214_998, 45_631, 50],
        "s5000_v1": {"n_blocks": 4_918, "zero": 1_107, "outside": 4_077, "in": 841},
        "s5000_v2": {"n_blocks": 4_021, "zero": 1_350, "outside": 3_180, "in": 841},
    },
    "3113e9ba7abb": {
        "null_arm_final": "b4ad8140fe4176db", "null_arm_llm_calls": 41_072,
        "v1_outside_blocks": 590_430, "v1_outside_dist": [92, 160_033, 133_575, 47_861],
        "s5000_v1": {"n_blocks": 8_589, "zero": 1, "outside": 7_733, "in": 856},
        "s5000_v2": {"n_blocks": 6_377, "zero": 150, "outside": 5_521, "in": 856},
    },
}
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


def make_world_agents(n: int, n_cells: int = 9, seed: int = 1, home_cell=None):
    """``resolve.initialize`` と**同じ置き方**(``home_cell < 0`` の体は ``cell = node = -1``)。"""
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n, plan_columns=True)
    base = np.arange(n) % n_cells if home_cell is None else np.asarray(
        home_cell, dtype=np.int64
    )[:n]
    ok = base >= 0
    a.registry.cell[:] = np.where(ok, np.clip(base, 0, n_cells - 1), -1)
    a.registry.node[:] = np.where(
        ok, w.assets.cell_rep_node[np.clip(base, 0, n_cells - 1)], -1
    )
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
    w, a = make_world_agents(n, n_cells=n_cells, home_cell=home_cell)
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
    g = W17_GOLDEN.get(w17_digest())
    if g is None:
        pytest.skip(f"実 W17 の golden が無い(md5 {w17_digest()})=親が再実行して W17_GOLDEN に足す")
    assert res.final_hash.startswith(g["null_arm_final"])
    assert res.run_manifest_fields()["plan_executor"] is False
    assert res.presence_counters == {}
    assert res.conserved and int(res.llm_calls) == g["null_arm_llm_calls"]


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


def test_being_in_the_stage_implies_having_a_cell_on_every_tick():
    """④-b(§5 I6・層2 指摘 2026-09-11): **在圏(``transit_state==0``)⇒ セルとノードがある**。

    保存則(3 値の和=体数)は遷移が 2 本しか無いので恒真になりやすい。その隣に
    「舞台に居るのに ``cell = -1``」(=どこにも居ない在圏)が 1 体も出ないことを置く。
    域外居住(``home_cell < 0``)で 0 時から在圏のブロックを持つ体がこの穴に落ちていた。
    """
    n = 24
    rows = []
    for i in range(n):
        if i % 3 == 0:  # 0 時から在圏(``home_cell < 0`` なのでセルが無いまま始まる)
            rows += [(i, 0, 500, ACT_WORK, PK_WORK, 3), (i, 500, 1_440, ACT_SLEEP, PK_OUT, -1)]
        else:
            rows += [
                (i, 0, 300 + i, ACT_SLEEP, PK_OUT, -1),
                (i, 300 + i, 900, ACT_WORK, PK_WORK, 3),
                (i, 900, 1_440, ACT_SLEEP, PK_OUT, -1),
            ]
    wk = make_weekly(rows, n)
    _, agents, _, layer = make_layer(wk, n=n, home_cell=np.full(n, -1, dtype=np.int64))
    layer.initialize()
    assert layer.n_placed_at_start == len(range(0, n, 3))
    r = agents.registry
    for tick in range(1_000):
        layer.step(tick)
        layer.step_plan_boundaries(tick)
        here = np.asarray(r.transit_state) == 0
        assert not np.any(here & (np.asarray(r.cell) < 0)), tick
        assert not np.any(here & (np.asarray(r.node) < 0)), tick


def test_a_resident_stays_in_the_stage_when_the_next_row_is_not_outside():
    """③-b(§10-7 (a)): **域内居住者は「次が域外」のときだけ退出**(隙間では出ない)。"""
    rows = [
        # 住民 0: 自宅 → 隙間 → 公園 → 自宅(域外の行が 1 つも無い)= 終日在圏
        (0, 0, 480, ACT_REST, PK_HOME, 5),
        (0, 600, 900, ACT_REST, PK_STATION, -1),
        (0, 900, 1_440, ACT_REST, PK_HOME, 5),
        # 住民 1: 自宅 → 乗車(駅)→ 域外 → 自宅 = 乗車行を飛ばして「次が域外」を読む
        (1, 0, 480, ACT_REST, PK_HOME, 5),
        (1, 480, 540, ACT_RIDE, PK_STATION, -1),
        (1, 540, 1_000, ACT_WORK, PK_OUT, -1),
        (1, 1_000, 1_440, ACT_REST, PK_HOME, 5),
    ]
    wk = make_weekly(rows, 2)
    _, agents, _, layer = make_layer(wk, n=2, home_cell=np.array([5, 5]))
    layer.initialize()
    assert census(agents) == (2, 0, 0)
    for tick in range(1_440):
        layer.step(tick)
    st = np.asarray(agents.registry.transit_state)
    assert int(st[0]) == 0  # 住民 0 は一度も出ない(隙間は退出ではない)
    assert layer.n_departures == 1  # 住民 1 だけが 480 に出る
    assert int(st[1]) == 0  # 1,000 の在圏ブロックで帰ってくる


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
    """⑫(§5 I4): 引き込み後に古い ARRIVE が発火しない・押し出しは**翌 tick に戻さない**。"""
    wk = make_weekly(
        [
            (0, 0, 300, ACT_SLEEP, PK_OUT, -1),
            (0, 400, 1_000, ACT_WORK, PK_WORK, 3),    # 在圏ブロック 1
            (0, 1_000, 1_100, ACT_SLEEP, PK_OUT, -1),  # 域外行(ブロックを切る)
            (0, 1_100, 1_300, ACT_WORK, PK_WORK, 3),   # 在圏ブロック 2
        ],
        1,
    )
    _, agents, _, layer = make_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    assert layer.candidates_for_pull(0).tolist() == [0]
    R.rail_arrive(agents, layer.world, np.array([0]), np.array([1]))
    layer.notify_pulled_in(np.array([0]), 0)
    for tick in range(0, 600):
        layer.step(tick)
        assert sum(census(agents)) == 1
    assert census(agents)[0] == 1  # 在圏のまま(古い到着で状態が壊れない)
    assert layer.n_arrive_skipped >= 1
    # 押し出し(civic の退場)→ **進行中ブロックには張り直さない**
    R.rail_depart(agents, np.array([0]), np.array([0]))
    layer.notify_pushed_out(np.array([0]), 600)
    assert layer.n_pushed_out == 1 and layer.n_rearmed == 0
    for tick in range(600, 999):
        layer.step(tick)
        assert sum(census(agents)) == 1
        assert census(agents)[2] == 1, tick  # 翌 tick に戻らない
    for tick in range(999, 1_101):
        layer.step(tick)
    assert layer.n_depart_dropped == 1  # 進行中ブロック(終了 1,000)の DEPART は落ちた
    assert layer.n_depart_skipped == 0  # 「在圏でない DEPART」の取り残しも出ない
    assert census(agents)[0] == 1  # 次のブロックの到着で帰ってくる


def test_llm_boarding_is_re_armed_for_the_next_block():
    """④(§4): LLM が乗車で域外へ出たら、残り DEPART を落として**次のブロックの開始**へ張り直す。"""
    wk = make_weekly(
        [
            (0, 0, 400, ACT_WORK, PK_WORK, 3),        # 在圏ブロック 1(0 時から在圏)
            (0, 400, 800, ACT_SLEEP, PK_OUT, -1),
            (0, 800, 1_000, ACT_WORK, PK_WORK, 3),     # 在圏ブロック 2
        ],
        1,
    )
    _, agents, _, layer = make_layer(wk, n=1, home_cell=np.array([-1]))
    layer.initialize()
    assert census(agents)[0] == 1 and int(agents.registry.cell[0]) >= 0  # I6
    for tick in range(0, 500):
        layer.step(tick)
    assert census(agents)[0] == 1  # 400 で退出 → 便 480 で戻っている(ブロック 2 の到着)
    # 500 tick 目に LLM が乗車して域外へ出た(rail の発車ブロックが層へ通知する経路)
    R.rail_depart(agents, np.array([0]), np.array([0]))
    layer.notify_departed_by_llm(np.array([0]), 500)
    assert layer.n_departed_by_llm == 1 and layer.n_rearmed == 1
    for tick in range(500, 800):
        layer.step(tick)
        assert census(agents)[2] == 1, tick  # 次のブロックの開始まで戻らない
    layer.step(800)
    assert census(agents)[0] == 1  # ブロック 2 の開始 tick に張り直された到着で戻る


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
    per_train = np.bincount(layer.arrival_train[layer.arrival_train >= 0], minlength=6)
    assert layer.n_spread_moved > 0
    # 両側に散らす(①早い便へ ②溢れた分は遅い便へ)。**最後の便以外**は上限を超えない。
    assert int(per_train[:-1].max()) <= 4
    # 席が足りない分(60 体 vs 6 便 × 4 席)は最後の便が受け切る=E8 の宣言どおり
    assert int(per_train[-1]) == n - 4 * 5
    assert layer.n_spread_overflow > 0
    assert ARRIVAL_SPREAD_MAX_TRAINS == 8


def test_arrival_spread_stays_inside_the_eight_train_window():
    """⑬-b(§3 E8・第3段): **|到着便 − E1 便| ≤ 8** がどの体でも破れない。

    第2段の実装は①(早い便へ)で hop 上限に達した体を置かずに運び続け、始発まで流して
    いた(390,067 体で |便差| 最大 191 便・09 時開始の 21,418 体が 06 時前に到着=層2 実測)。
    """
    n = 400
    rows = [(i, 0, 400, ACT_SLEEP, PK_OUT, -1) for i in range(n)]
    rows += [(i, 500, 900, ACT_WORK, PK_WORK, 3) for i in range(n)]
    wk = make_weekly(rows, n)
    deps = tuple(300 + 10 * k for k in range(30))  # 30 便(10 分間隔)
    pa = fake_assets(departures=deps)
    w, a = make_world_agents(n, home_cell=np.full(n, -1, dtype=np.int64))
    rail = RailProcess(w, a, pa, master_seed=1, day_index=0, plan_executor=True)
    rail.capacity100 = np.full(rail.dep_tick.size, 5.0)
    rail.cap_pct = np.full(rail.dep_tick.size, 100.0)  # 上限 5 人/便 × 30 便 = 150 席
    layer = PlanExecutor(
        w, a, wk, day_index=0,
        home_cell=np.full(n, -1, dtype=np.int64),
        direction_node=np.zeros(n, dtype=np.int64),
        kind=np.zeros(n, dtype=np.int64),
        agent_id=np.arange(n, dtype=np.int64),
        rail=rail, assets=pa, ticks=1_440,
    )
    e1 = layer.arrival_train_e1
    got = layer.arrival_train
    served = np.flatnonzero(e1 >= 0)
    assert served.size == n
    # 同一線なので「便索引の差」= スロット差(``_build_trains`` は発車 tick 昇順)
    diff = np.abs(got[served] - e1[served])
    assert int(diff.max()) <= ARRIVAL_SPREAD_MAX_TRAINS, int(diff.max())
    assert layer.n_spread_moved > 0 and layer.n_spread_overflow > 0
    # 到着はどの体も「E1 便 ± 8 便」の窓に入るので、始発まで流れない
    assert int(layer.arrival_tick[served].min()) >= int(
        np.asarray(rail.enter_tick).min()
    )


def test_overflow_on_the_last_train_stays_on_its_own_e1_train():
    """⑬-c(§3 E8・層2 最終確認): **E1 便が最終便**の体は③(E1 便が受け切り)へ直送する。

    ②の ``carry`` に入れて j=0 から回すと ``far = (0 - e1) > 8`` が偽になり**始発便**に
    置かれ得る(|便差| が窓を破る潜在経路。390,067 体では未発火)。
    """
    n = 40
    deps = tuple(300 + 10 * k for k in range(12))  # 12 便(最終 410)
    # 全員のブロックが**最終便の後**に始まる=E1 便は必ず最終便
    rows = [(i, 0, 400, ACT_SLEEP, PK_OUT, -1) for i in range(n)]
    rows += [(i, 600, 900, ACT_WORK, PK_WORK, 3) for i in range(n)]
    wk = make_weekly(rows, n)
    pa = fake_assets(departures=deps)
    w, a = make_world_agents(n, home_cell=np.full(n, -1, dtype=np.int64))
    rail = RailProcess(w, a, pa, master_seed=1, day_index=0, plan_executor=True)
    rail.capacity100 = np.full(rail.dep_tick.size, 2.0)   # 上限 2 人/便
    rail.cap_pct = np.full(rail.dep_tick.size, 100.0)
    layer = PlanExecutor(
        w, a, wk, day_index=0,
        home_cell=np.full(n, -1, dtype=np.int64),
        direction_node=np.zeros(n, dtype=np.int64),
        kind=np.zeros(n, dtype=np.int64),
        agent_id=np.arange(n, dtype=np.int64),
        rail=rail, assets=pa, ticks=1_440,
    )
    e1, got = layer.arrival_train_e1, layer.arrival_train
    sv = np.flatnonzero(e1 >= 0)
    assert sv.size == n
    last = int(np.asarray(rail.enter_tick).argmax())
    assert set(e1[sv].tolist()) == {last}          # E1 便は全員 最終便
    assert int(np.abs(got[sv] - e1[sv]).max()) <= ARRIVAL_SPREAD_MAX_TRAINS
    # ①で 8 便ぶん(2 人 × 8 = 16 人)は早い便へ、残りは**自分の E1 便**が受け切る
    assert np.all(got[sv] <= last) and np.all(got[sv] >= last - ARRIVAL_SPREAD_MAX_TRAINS)
    assert int(np.count_nonzero(got[sv] == last)) == n - 2 * ARRIVAL_SPREAD_MAX_TRAINS
    # 受け切り = 全体 − (E1 便の定員 2 + 早い 8 便 × 2)
    assert layer.n_spread_overflow == n - 2 * (ARRIVAL_SPREAD_MAX_TRAINS + 1)
    # **始発便には 1 体も置かれない**(窓の外)
    first = int(np.asarray(rail.enter_tick).argmin())
    assert int(np.count_nonzero(got[sv] == first)) == 0


def test_a_resident_who_boards_in_the_last_block_comes_back(monkeypatch):
    """E12(第3段): **次のブロックが無い**体が LLM 乗車で出たら、``t+60`` 以降の便で戻る。

    civic の押し出し(``notify_pushed_out``)は**この復帰を使わない**(翌 tick 復帰の再発防止)。
    """
    wk = make_weekly(
        [
            (0, 0, 200, ACT_SLEEP, PK_OUT, -1),
            (0, 200, 1_440, ACT_WORK, PK_WORK, 3),  # その日 最後の(唯一の)在圏ブロック
            (1, 0, 200, ACT_SLEEP, PK_OUT, -1),
            (1, 200, 1_440, ACT_WORK, PK_WORK, 3),
        ],
        2,
    )
    deps = tuple(300 + 30 * k for k in range(20))  # 300, 330, … 870
    _, agents, _, layer = make_layer(
        wk, n=2, home_cell=np.array([-1, -1]), assets=fake_assets(departures=deps)
    )
    layer.initialize()
    for tick in range(0, 400):
        layer.step(tick)
    assert census(agents) == (2, 0, 0)
    # 体 0 = LLM の乗車で退出 → 進行中ブロックへ戻る / 体 1 = civic の押し出し → 戻らない
    R.rail_depart(agents, np.array([0, 1]), np.array([0, 0]))
    layer.notify_departed_by_llm(np.array([0]), 400)
    layer.notify_pushed_out(np.array([1]), 400)
    assert layer.n_returned_to_block == 1
    ret = min(k for k in layer._extra)
    assert ret >= 400 + RETURN_MIN_AWAY_MIN
    assert ret == 480  # 480 発の便がホームへ入る tick(通過型は dep_tick と同じ)
    for tick in range(400, 1_440):
        layer.step(tick)
        assert sum(census(agents)) == 2
    st = np.asarray(agents.registry.transit_state)
    assert int(st[0]) == 0  # 乗車で出た体は 480 の便で戻り、日末まで在圏
    assert int(st[1]) == 2  # 押し出された体は戻らない
    assert layer.plan_stranded_eod == 1  # 計画では 2 体とも在圏のはず → 1 体だけ取り残し


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
    per_full = PlanBlocks.from_weekly(wk_full, 0, ho_full, derive_rule="v1").blocks_per_agent()
    # **親検証値そのもの**(全 390,067 体・day0・定義 B の集計軸=域外居住者)。表ごとの golden(第170)
    g = W17_GOLDEN.get(w17_digest())
    if g is None:
        pytest.skip(f"実 W17 の golden が無い(md5 {w17_digest()})=親が再実行して W17_GOLDEN に足す")
    assert int(ho_full.sum()) == 346_445
    assert int(per_full[ho_full].sum()) == g["v1_outside_blocks"]
    assert np.bincount(per_full[ho_full], minlength=4)[:4].tolist() == g["v1_outside_dist"]
    # 5,000 体標本(前後測定に使う縮尺)の実測 golden
    pop = sample_population(full, 5_000, 1)
    wk = wk_full.restrict_to(pop.source_agent_id)
    home_out = np.asarray(pop.home_cell) < 0
    blocks = PlanBlocks.from_weekly(wk, 0, home_out, derive_rule="v1")  # 読み口 v1 の golden
    per = blocks.blocks_per_agent()
    s1 = g["s5000_v1"]
    assert int(home_out.sum()) == 4_491
    assert blocks.n_blocks == s1["n_blocks"]
    assert int(np.count_nonzero(per == 0)) == s1["zero"]
    assert int(per[home_out].sum()) == s1["outside"]
    assert int(np.count_nonzero(per[home_out] == 0)) == s1["zero"]
    assert int(per[~home_out].sum()) == s1["in"]  # 域内居住者の「自宅」行は在圏に数える
    # 読み口 v2(既定・§2 追補 2026-09-12)の同じ標本(親再実行値): 域内居住者は同一
    b2 = PlanBlocks.from_weekly(wk, 0, home_out)
    per2 = b2.blocks_per_agent()
    s2 = g["s5000_v2"]
    assert b2.derive_rule == "v2"
    assert b2.n_blocks == s2["n_blocks"]
    assert int(per2[home_out].sum()) == s2["outside"]
    assert int(np.count_nonzero(per2[home_out] == 0)) == s2["zero"]
    assert int(per2[~home_out].sum()) == s2["in"]


# ================================================================= 腕・切替口
def test_the_real_civic_path_pulls_and_pushes_through_the_layer():
    """⑫-b(§5 I4): **civic の実経路**(``LargeEventProcess._arrive/_leave``)が層を通る。

    引き込み候補は「その日在圏予定のある域外の体」だけ・退場は翌 tick に戻らない。
    """
    from shibuya.engine.processes.civic import EVENT_WINDOW, LargeEventProcess

    n = 12
    rows = []
    for i in range(n):
        if i < 8:  # 来街予定あり(夕方の在圏ブロック)
            rows += [
                (i, 0, 1_000, ACT_SLEEP, PK_OUT, -1),
                (i, 1_000, 1_200, ACT_REST, PK_STATION, -1),
                (i, 1_200, 1_440, ACT_SLEEP, PK_OUT, -1),
            ]
        else:  # 非来街日=終日域外(引き込み候補にしない)
            rows += [(i, 0, 1_440, ACT_SLEEP, PK_OUT, -1)]
    wk = make_weekly(rows, n)
    world, agents, rail, layer = make_layer(
        wk, n=n, home_cell=np.full(n, -1, dtype=np.int64)
    )
    layer.initialize()
    ev = LargeEventProcess(
        world, agents, rail=rail, master_seed=1, day_index=0, visitor_delta=4
    )
    ev.presence = layer
    lo, hi = EVENT_WINDOW
    # 引き込み候補は「その日在圏予定のある域外の体」= 先頭 8 体だけ
    assert set(layer.candidates_for_pull(lo).tolist()) <= set(range(8))
    for tick in range(lo, lo + 2):
        ev.step(tick)
        layer.step(tick)
    assert ev.n_in == 4 and layer.n_pulled_in == 4
    assert census(agents)[0] == 4
    for tick in range(hi, hi + 30):
        ev.step(tick)
        layer.step(tick)
        assert sum(census(agents)) == n
    assert ev.n_out == 4 and layer.n_pushed_out == 4
    assert census(agents)[0] == 0  # 翌 tick に戻らない(進行中ブロックへ張り直さない)


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
