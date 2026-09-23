"""C9 位置幾何(``engine.geometry``)の検収。

正典
- ``docs/design/v2-c9-geometry-agenda.md`` §1 + §4 改訂(2026-09-17 ユーザー決定):
  **G1 (b) 辺上の連続位置** / **G2 (b) 希望速度 1.00〜1.60 m/s + Kladek 減速** /
  **G9 P2 ≤300 ms/tick@40 万体** / **G11 ``UNREACHABLE``・``TARGET_GONE``**。
- ``docs/research/lit/crowd__kretz2015_kladek-formula.md``(式と再計算値)。
- ``docs/research/lit/crowd__bosina-weidmann2018_fd-generic-model.md`` Table 2(速度の帯)。

検査する 8 点(親の指示)
  (i) node 既定でバイト不変 / (ii) edge で同 seed 2 回=同 hash / (iii) 速度分布 /
  (iv) 密度 0 と ρ=3.33 の 1 tick 距離 / (v) 到着判定 / (vi) 失敗コード /
  (vii) P2 の実測 / (viii) T2-c 再生。
"""

from __future__ import annotations

import time

import numpy as np
import pytest

from shibuya.agents.state import Activity, AgentState, RESULT_TEXT, ResultCode
from shibuya.core.budget import budget_by_id, load_budget_table
from shibuya.engine import commit as C
from shibuya.engine import geometry as G
from shibuya.engine import resolve as R
from shibuya.engine.run import run_day
from shibuya.world.state import DENSITY_STAGE_EDGES, DENSITY_STAGE_EDGES_PER_M2, World

#: 600 tick = 世界内 10:00 まで回す。**体が実際に歩き出すまで回さないと edge の腕が
#: 「欄が 2 本増えただけ」の検査になる**(120 tick では移動が 1 件も出ない)。
SMALL = dict(n_agents=200, seed=1, ticks=600, checkpoint_every=200, n_cells=25)


class BoomLLM:
    """再生モードで**呼ばれたら落ちる** LLM(テープ外 0 の陽性対照)。"""

    def generate(self, *a, **k):  # pragma: no cover - 呼ばれないことが検査
        raise AssertionError("リプレイで実 LLM が呼ばれた")


# ================================================================ 表・定数
def test_geometry_modes_and_default():
    assert G.GEOMETRY_MODES == ("node", "edge")
    assert G.DEFAULT_GEOMETRY == "node"
    assert G.check_geometry("edge") == "edge"
    with pytest.raises(ValueError):
        G.check_geometry("辺上")


def test_kladek_constants_match_the_lit_note():
    """Kretz 2015 §2 式 (7)(8)(9) の 3 値。"""
    assert G.SPEED_REFERENCE_MS == 1.34
    assert G.KLADEK_GAMMA == 1.913
    assert G.KLADEK_RHO_MAX_PER_M2 == 5.4
    assert (G.DESIRED_SPEED_MIN_MS, G.DESIRED_SPEED_MAX_MS) == (1.00, 1.60)


def test_kladek_curve_reproduces_the_recomputed_values():
    """lit メモ **[再計算]** の v(ρ)(v0=1.34 m/s)を 3 桁で再現する。

    Note:
        lit メモ ``crowd__kretz2015_kladek-formula.md`` の再計算 7 値のうち **6 値は一致**。
        ρ=1.076 だけメモは 1.015 と書くが、式 v=1.34·[1−exp(−1.913·(1/ρ−1/5.4))] を
        素直に計算すると **1.017**(親へ報告済みの食い違い。メモは「**親未確認**」の段階)。
        本テストは**式**を正とする。
    """
    expect = {0.238: 1.339, 0.431: 1.317, 0.718: 1.207,
              2.15: 0.556, 3.33: 0.265, 5.0: 0.037}
    for rho, v in expect.items():
        got = float(G.kladek_speed_factor(rho)) * G.SPEED_REFERENCE_MS
        assert round(got, 3) == v, (rho, got, v)
    assert round(float(G.kladek_speed_factor(1.076)) * G.SPEED_REFERENCE_MS, 3) == 1.017
    assert float(G.kladek_speed_factor(0.0)) == 1.0
    assert float(G.kladek_speed_factor(5.4)) == 0.0
    assert float(G.kladek_speed_factor(9.9)) == 0.0  # 詰め込み密度超えは clip(負にしない)


def test_density_stage_edges_are_the_fruin_los_boundaries():
    """edge 幾何の段は **Fruin LOS**(人/m²)。``perception`` 側の表と 1 対 1(二重定義の検査)。"""
    from shibuya.perception import templates as T

    assert DENSITY_STAGE_EDGES_PER_M2 == T.DENSITY_LOS_EDGES_PER_M2
    assert len(DENSITY_STAGE_EDGES_PER_M2) == len(T.DENSITY_LOS_LETTERS) - 1
    # node 幾何の既存の段(人/セル)は**動かさない**
    assert DENSITY_STAGE_EDGES == (1, 5, 20, 60, 150, 400, 1_000)


def test_mix64_matches_the_presence_definition():
    """``geometry._mix64`` は ``presence``/``build.sched`` と**同じ式**(三重定義の機械検査)。"""
    from shibuya.engine.presence import _mix64 as presence_mix64

    x = np.arange(64, dtype=np.uint64) * np.uint64(2_654_435_761)
    assert np.array_equal(G._mix64(x), presence_mix64(x))


# ================================================================ (vi) 失敗コード
def test_result_codes_for_c9_exist_and_are_appended_at_the_end():
    """G11: ``UNREACHABLE``(既存)と ``TARGET_GONE``(新設・末尾追加)。"""
    assert int(ResultCode.UNREACHABLE) == 1  # 既存の行をそのまま使う
    assert int(ResultCode.TARGET_GONE) == 20  # 末尾に足すだけ=既存の配列も描画も動かない
    assert RESULT_TEXT[ResultCode.TARGET_GONE] == "対象が去った"
    assert RESULT_TEXT[ResultCode.TARGET_GONE] != RESULT_TEXT[ResultCode.PARTNER_GONE]
    assert max(int(c) for c in ResultCode) == int(ResultCode.TARGET_GONE)


def test_target_gone_is_written_and_rendered_like_any_other_failure():
    """``_fail`` に載る=描画まで通る(**発生させる側は C9b の領分**=ここでは口だけ検査)。"""
    agents = AgentState(4)
    out = R.ResolveOutcome(tick=7)
    R._fail(agents, np.array([1, 2]), ResultCode.TARGET_GONE, 7, out)
    assert list(agents.last_result[[1, 2]]) == [int(ResultCode.TARGET_GONE)] * 2
    assert out.per_result[int(ResultCode.TARGET_GONE)] == 2


# ================================================================ (iii) 速度分布
def test_desired_speeds_are_inside_the_bosina_weidmann_band():
    v = G.desired_speeds(1, np.arange(20_000))
    assert v.dtype == np.float32
    assert float(v.min()) >= 1.00 and float(v.max()) <= 1.60
    assert abs(float(v.mean()) - 1.30) < 0.01, float(v.mean())
    assert abs(float(np.median(v)) - 1.30) < 0.01


def test_desired_speeds_are_deterministic_and_scale_invariant():
    """T4: 体数を増やしても既存個体の値が動かない(``core.rng`` の列を引かない)。"""
    small = G.desired_speeds(1, np.arange(100))
    big = G.desired_speeds(1, np.arange(5_000))
    assert np.array_equal(small, big[:100])
    assert not np.array_equal(small, G.desired_speeds(2, np.arange(100)))


# ================================================================ (iv) 1 tick の距離
@pytest.fixture(scope="module")
def synthetic_world() -> World:
    return World.synthetic(n_cells=25, seed=1)


def test_one_tick_distance_at_zero_density_is_v_times_60(synthetic_world):
    """密度 0 → 1 tick の移動距離 = ``v_desired × 60 s``(減速なし)。"""
    w = synthetic_world
    g = G.EdgeGeometry(w.assets, seed=1, n_agents=8)
    budget = g.tick_budget_m(np.arange(8), np.zeros(8, np.int64), np.zeros(w.n_cells))
    assert np.allclose(budget, g.v_desired.astype(np.float64) * 60.0)
    # 合成世界の辺は 100 m なので 1 tick では渡り切らない=辺上の距離がそのまま出る
    node = np.zeros(8, np.int64)
    nxt = np.full(8, -1, np.int64)
    s = np.zeros(8, np.float32)
    eid = np.full(8, -1, np.int64)
    tgt = np.full(8, w.n_nodes - 1, np.int64)
    nd, nx, ss, ee, arr, stk, _ = g.advance(
        node=node, next_node=nxt, edge_s=s, edge_id=eid, target=tgt,
        budget_m=budget, route=w.graph.route_next_node,
    )
    assert not arr.any() and not stk.any()
    assert np.allclose(ss.astype(np.float64), budget, atol=1e-3)


def test_one_tick_distance_at_fruin_los_f_is_about_one_fifth(synthetic_world):
    """ρ=3.33 人/m²(C7 実測の最混雑)→ 係数 0.198 ≒ **0.2 v**(lit メモの再計算)。"""
    w = synthetic_world
    area = np.full(w.n_cells, 1_500.0)
    g = G.EdgeGeometry(w.assets, seed=1, n_agents=4, walkable_area_m2=area)
    density = np.full(w.n_cells, 3.33 * 1_500.0)
    free = g.tick_budget_m(np.arange(4), np.zeros(4, np.int64), np.zeros(w.n_cells))
    jam = g.tick_budget_m(np.arange(4), np.zeros(4, np.int64), density)
    ratio = jam / free
    assert np.allclose(ratio, 0.1977, atol=5e-4), ratio
    assert abs(float(ratio[0]) - 0.2) < 0.01


def test_density_stage_uses_people_per_square_metre_in_edge_mode(synthetic_world):
    """edge では段が Fruin LOS(人/m²)。node の段(人/セル)とは別物。"""
    w = synthetic_world
    area = np.full(w.n_cells, 4_206.0)  # 本番の歩行可能面積の中央値
    g = G.EdgeGeometry(w.assets, seed=1, n_agents=4, walkable_area_m2=area)
    # 1,000 人/セル = 0.238 人/m² = LOS A(段 0)。node の段では最上段(7)だった
    stage = g.density_stage(np.full(w.n_cells, 1_000.0))
    assert int(stage[0]) == 0
    assert int(w.density_stage(np.full(w.n_cells, 1_000.0))[0]) == 7
    # LOS C の入口 1,811 人/セル・LOS F の入口 2.153 人/m²
    assert int(g.density_stage(np.array([1_811.0]))[0]) == 2
    assert int(g.density_stage(np.array([2.16 * 4_206.0]))[0]) == 5


# ================================================================ (v) 到着判定
def test_arrival_is_detected_when_s_reaches_the_target_node(synthetic_world):
    w = synthetic_world
    g = G.EdgeGeometry(w.assets, seed=1, n_agents=2)
    start = np.array([0, 0], np.int64)
    tgt = np.array([w.graph.route_next_node(np.array([0]), np.array([8]))[0]] * 2, np.int64)
    assert tgt[0] >= 0
    nd, nx, ss, ee, arr, stk, _ = g.advance(
        node=start, next_node=np.full(2, -1, np.int64), edge_s=np.zeros(2, np.float32),
        edge_id=np.full(2, -1, np.int64), target=tgt, budget_m=np.full(2, 500.0),
        route=w.graph.route_next_node,
    )
    assert arr.all() and not stk.any()
    assert list(nd) == list(tgt)
    # 到着した体は辺から降りる(辺上に居てよいのは移動中の体だけ)
    assert list(nx) == [-1, -1] and list(ee) == [-1, -1] and float(ss.max()) == 0.0


def test_positions_interpolate_between_the_two_end_nodes(synthetic_world):
    w = synthetic_world
    g = G.EdgeGeometry(w.assets, seed=1, n_agents=1)
    u, v = 0, int(w.graph.route_next_node(np.array([0]), np.array([1]))[0])
    e, length = g.lookup_edge(np.array([u]), np.array([v]))
    half = np.array([length[0] / 2.0], np.float32)
    cell, band, xy = g.positions(np.array([u]), np.array([v]), half, e)
    mid = (w.assets.node_xy[u] + w.assets.node_xy[v]) / 2.0
    assert np.allclose(xy[0], mid, atol=1e-3)
    # 比 0.5 以上は**先のノード**のセル(近い方の端点)
    assert int(cell[0]) == int(w.assets.node_cell[v])
    # 辺に乗っていない体はノード座標そのもの(= node 幾何と同じ)
    _, _, xy0 = g.positions(np.array([u]), np.array([-1]), np.zeros(1, np.float32),
                            np.array([-1]))
    assert np.allclose(xy0[0], w.assets.node_xy[u])


# ================================================================ (vi) UNREACHABLE
def test_unreachable_is_raised_when_the_next_hop_table_has_no_path(synthetic_world):
    """次ホップが引けない体は ``stuck``(``resolve`` が ``UNREACHABLE`` を書く)。"""
    w = synthetic_world
    g = G.EdgeGeometry(w.assets, seed=1, n_agents=2)

    def no_route(u, v):
        return np.full(np.asarray(u).size, -1, dtype=np.int32)

    nd, nx, ss, ee, arr, stk, _ = g.advance(
        node=np.array([0, 1], np.int64), next_node=np.full(2, -1, np.int64),
        edge_s=np.zeros(2, np.float32), edge_id=np.full(2, -1, np.int64),
        target=np.array([9, 9], np.int64), budget_m=np.full(2, 80.0),
        route=no_route,
    )
    assert stk.all() and not arr.any()


def test_engine_step_writes_unreachable_end_to_end_in_edge_mode():
    """``resolve.apply`` まで通して ``ResultCode.UNREACHABLE`` が立つ(next_hop を塞ぐ)。"""
    w = World.synthetic(n_cells=25, seed=1)
    src, dst = 0, 9
    w.assets.next_hop[src, dst] = -1  # 資産を 1 マスだけ塞ぐ(合成世界なので書ける)
    agents = AgentState(4, edge_columns=True)
    agents.registry.node[:] = src
    agents.registry.cell[:] = int(w.assets.node_cell[src])
    agents.registry.activity[:] = int(Activity.MOVING)
    agents.registry.target_node[:] = dst
    g = G.EdgeGeometry(w.assets, seed=1, n_agents=4)
    batch = C.IntentBatch(
        agent_id=np.arange(4, dtype=np.int64),
        action_code=np.full(4, C.ENGINE_STEP, dtype=np.int8),
        target_id=np.full(4, dst, dtype=np.int32),
        resource_id=np.full(4, -1, dtype=np.int32),
        t_notice_ns=np.zeros(4, dtype=np.int64),
    )
    empty = C.IntentBatch.empty()
    out = R.apply(batch, empty, agents, w, 1, geometry=g)
    assert out.per_result[int(ResultCode.UNREACHABLE)] == 4
    assert list(agents.registry.activity) == [int(Activity.IDLE)] * 4


# ================================================================ (i) node のバイト不変
def test_node_mode_declares_no_extra_columns():
    """既定(node)は ``edge_id``/``edge_s`` を確保しない=``state_hash`` が動かない。"""
    base = AgentState(32)
    same = AgentState(32, edge_columns=False)
    assert base.state_hash() == same.state_hash()
    assert base.declared_bytes_per_agent == same.declared_bytes_per_agent
    with pytest.raises(AttributeError):
        _ = base.edge_id
    edge = AgentState(32, edge_columns=True)
    assert edge.declared_bytes_per_agent == base.declared_bytes_per_agent + 8
    assert edge.state_hash() != base.state_hash()
    assert edge.edge_id.dtype == np.int32 and edge.edge_s.dtype == np.float32
    assert int(edge.edge_id[0]) == -1 and float(edge.edge_s[0]) == 0.0


def test_position_columns_still_fit_the_m2_budget():
    """M2(位置・運動・身体)≤128 B/体 に辺上の 2 欄を足しても収まる。"""
    st = AgentState(4, edge_columns=True)
    core = {
        "cell", "node", "band", "xy", "path_next_node", "target_node", "kind",
        "hunger", "fatigue", "thermal", "money", "holdings", "activity",
        "edge_id", "edge_s",
    }
    total = sum(d.byte_budget_per_entity for d in st.registry.decls if d.name in core)
    assert total <= 128, total


def test_explicit_node_geometry_is_byte_identical_to_the_default():
    a = run_day(**SMALL)
    b = run_day(geometry="node", **SMALL)
    assert a.final_hash == b.final_hash
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert a.run_manifest_fields()["geometry"] == "node"
    assert a.geometry_hops == 0 and a.geometry_jammed == 0


def test_bad_geometry_is_rejected_before_anything_is_built():
    with pytest.raises(ValueError):
        run_day(geometry="辺", n_agents=8, ticks=1, n_cells=9)


# ================================================================ (ii) edge の決定論
@pytest.fixture(scope="module")
def edge_run():
    return run_day(geometry="edge", **SMALL)


def test_edge_mode_is_deterministic_across_two_runs(edge_run):
    again = run_day(geometry="edge", **SMALL)
    assert again.final_hash == edge_run.final_hash
    assert [c.combined for c in again.checkpoints] == [
        c.combined for c in edge_run.checkpoints
    ]


def test_edge_mode_changes_the_run_and_records_the_arm(edge_run):
    node = run_day(**SMALL)
    assert edge_run.final_hash != node.final_hash
    assert edge_run.run_manifest_fields()["geometry"] == "edge"
    assert edge_run.conserved
    assert "幾何 edge" in edge_run.summary()
    assert "幾何" not in node.summary()
    # 辺上を実際に歩いている(=欄が増えただけではない)
    assert edge_run.geometry_hops > 0
    assert edge_run.geometry_jammed == 0  # 合成小世界は LOS A(詰め込み密度に届かない)


# ================================================================ (viii) T2-c 再生
def test_edge_tape_replays_bit_for_bit(tmp_path):
    """T2-c: edge モードで録ったテープの再生が checkpoint 列まで一致・テープ外 0。"""
    path = tmp_path / "tape_edge"
    rec = run_day(geometry="edge", tape_path=path, **SMALL)
    rep = run_day(geometry="edge", mode="replay", replay=path, llm=BoomLLM(), **SMALL)
    assert rep.final_hash == rec.final_hash
    assert [c.combined for c in rep.checkpoints] == [c.combined for c in rec.checkpoints]
    assert rep.tape_miss_count == 0


# ================================================================ (vii) P2 の実測
def _p2_edge_bench(n_agents: int, world: World, ticks: int = 60, walkable=None):
    """「辺上前進 + 位置確定 + 密度」の 1 tick あたり壁時計[ms](P2 の測定対象)。"""
    rng = np.random.default_rng(12345)
    agents = AgentState(n_agents, edge_columns=True)
    r = agents.registry
    n_nodes = world.n_nodes
    r.node[:] = rng.integers(0, n_nodes, n_agents)
    r.target_node[:] = rng.integers(0, n_nodes, n_agents)
    r.activity[:] = int(Activity.MOVING)
    r.cell[:] = world.assets.node_cell[r.node.astype(np.int64)]
    g = G.EdgeGeometry(
        world.assets, seed=1, n_agents=n_agents,
        walkable_area_m2=_walkable_of(world) if walkable is None else walkable,
    )
    world.cells.density[:] = world.compute_density(r.cell)
    aid = np.arange(n_agents, dtype=np.int64)
    t0 = time.perf_counter()
    for _ in range(ticks):
        budget = g.tick_budget_m(aid, r.cell, world.cells.density)
        nd, nx, s, eid, arrived, stuck, _h = g.advance(
            node=r.node, next_node=r.path_next_node, edge_s=r.edge_s, edge_id=r.edge_id,
            target=r.target_node, budget_m=budget, route=world.graph.route_next_node,
        )
        r.node[:] = nd.astype(np.int32)
        r.path_next_node[:] = nx.astype(np.int32)
        r.edge_s[:] = s
        r.edge_id[:] = eid.astype(np.int32)
        # 着いた体はその場で新しい行き先へ(移動中の体を保って走査量を最大に保つ)
        done = np.flatnonzero(arrived | stuck)
        if done.size:
            r.target_node[done] = rng.integers(0, n_nodes, done.size)
        cell, band, xy = g.positions(r.node, r.path_next_node, r.edge_s, r.edge_id)
        r.cell[:] = cell
        r.band[:] = band
        r.xy[:] = xy
        world.cells.density[:] = world.compute_density(r.cell)
        world.cells.density_stage[:] = g.density_stage(world.cells.density)
    return (time.perf_counter() - t0) / ticks * 1_000.0


def _walkable_of(world: World):
    from shibuya.perception.renderer import (
        CELL_SIZE_M,
        WALKABLE_FRACTION_SYNTHETIC,
    )

    return np.full(
        world.n_cells, CELL_SIZE_M * CELL_SIZE_M * WALKABLE_FRACTION_SYNTHETIC, np.float64
    )


def test_p2_declaration_has_the_400k_row():
    """予算宣言表 P2 に **40 万体の行**(G9 ≤300 ms/tick)が書かれている。"""
    row = budget_by_id(load_budget_table())["P2"]
    assert "300 ms/tick@40万体" in row.declared
    assert "≤5ms/フレーム@5千体" in row.declared  # 5 千体の行は動かさない


def test_p2_scaled_down_runs_in_ci():
    """CI 用の縮小版(4 万体・合成 453 セル)。絶対値ゲート(40 万体)は slow 側。"""
    w = World.synthetic(n_cells=453, seed=1)
    ms = _p2_edge_bench(40_000, w, ticks=20)
    print(f"\n[P2 edge 縮小] 40,000体×453セル: {ms:.3f} ms/tick")
    assert ms <= 300.0


@pytest.mark.slow
def test_p2_edge_geometry_under_300ms_at_400k_agents():
    """予算行 P2(G9 delta 2026-09-17): **40 万体で ≤300 ms/tick**。

    **全体が毎 tick 移動中**という、実ラン(移動中は 1 割前後)よりずっと重い条件で測る。
    歩行可能面積は 3 通り: 床 1,500 m²(密=最も減速する)/ 実資産(街路点×6.25・本番)/
    自由流(減速なし=**work の上限**)。ゲートは**本番相当**に掛け、上限は参考に出す。
    """
    from pathlib import Path

    from shibuya.perception.renderer import PerceptionAssets
    from shibuya.world.assets import assets_available

    path = Path("data/world/v2")
    has_assets = assets_available(path)
    world = World.load(path) if has_assets else World.synthetic(n_cells=453, seed=1)
    real = (
        np.asarray(
            PerceptionAssets.load_or_synthetic(path, world).walkable_area_m2, np.float64
        )
        if has_assets
        else _walkable_of(world)
    )
    free = np.full(world.n_cells, 1e9)
    rows = [
        ("床 1,500 m²", _p2_edge_bench(400_000, world, 60, _walkable_of(world))),
        ("実資産(街路点×6.25)", _p2_edge_bench(400_000, world, 60, real)),
        ("自由流(減速なし・上限)", _p2_edge_bench(400_000, world, 60, free)),
    ]
    print(f"\n[P2 edge] 400,000体 × {world.n_cells}セル × 60 tick(全体が移動中)")
    for label, ms in rows:
        print(f"  {label:24s} {ms:7.2f} ms/tick (宣言 ≤300)")
    ms_real = rows[1][1]
    assert ms_real <= 300.0, f"P2(40 万体・本番相当)超過: {ms_real:.2f} ms/tick > 300 ms"
