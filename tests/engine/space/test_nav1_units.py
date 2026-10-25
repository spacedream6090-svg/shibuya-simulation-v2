"""段 1 の移動(engine.space.nav1)の受入の試験(合成の小さな面・データ不要)。

正: 指示書 10-03 §8 3-4-5 の移動の 2 本(位置の変化が歩く速さの上限以内か接続口を通ったもの・同じ時刻に 2 か所に
いない)+面の外に居ない・接続口の容量と待ち・SR11 (a)+(d)・SR12 (a)+(d)・エンジンが本人の判断を決めていない(AST)。
"""

from __future__ import annotations

import ast
import math
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.geometry import desired_speeds
from shibuya.engine.space import nav1 as N
from shibuya.world import navmesh as NV
from tests.build_space import synth as SY

SRC = Path(__file__).resolve().parents[3] / "src" / "shibuya" / "engine" / "space" / "nav1.py"


@pytest.fixture(scope="module")
def space(tmp_path_factory):
    d = tmp_path_factory.mktemp("nav1_engine")
    out, _ = SY.build_synth(d)
    mesh = NV.load_navmesh(out)
    return N.NavSpace(mesh, SY.fake_assets(), world_dir=out, seed=1, n_agents=400, tick_seconds=60)


def _inside(m, fi, x, y) -> bool:
    return any(m.locate(int(fi), x + dx, y + dy) >= 0 for dx in (0, 1e-6, -1e-6) for dy in (0, 1e-6, -1e-6))


# ------------------------------------------------------------------ 式
def test_slope_factor_matches_r63_table():
    # R-63 §1-3: +3.3%(スペイン坂)で Wood 4.72 km/h・Tobler 4.49 km/h(平地 4.86・5.04)
    assert float(N.slope_speed_factor("wood", 0.033)) == pytest.approx(4.72 / 4.86, abs=0.003)
    assert float(N.slope_speed_factor("tobler", 0.033)) == pytest.approx(4.49 / 5.04, abs=0.003)
    assert float(N.slope_speed_factor("wood", 0.0)) == pytest.approx(1.0)
    assert N.slope_factor_max("wood") < 1.01 and N.slope_factor_max("tobler") == pytest.approx(math.exp(0.175))


def test_turn_weights_fixed_and_person_range_deterministic():
    f = N.turn_weights("fixed", 1, 10)
    assert np.all(f == 50.0)
    p1 = N.turn_weights("person", 1, 5000)
    p2 = N.turn_weights("person", 1, 5000)
    assert np.array_equal(p1, p2) and p1.min() >= 32.0 and p1.max() < 62.0 and p1.std() > 5.0


def test_link_times_sr11(space):
    m = space.mesh
    v = np.full(m.n_links, 1.40)
    tab, tba = space.link_times(v)
    h = float(m.link_rise_m[0])
    L = max(float(m.link_len_m[0]), 0.1)
    tan_s = math.tan(math.radians(N.STAIRS_ANGLE_DEG))
    flat = max(L - h / tan_s, 0.0) / 1.40  # 段の水平の分を超える残りは平らに歩く
    assert tab[0] == pytest.approx(h / (0.76 * tan_s) + flat)
    assert tba[0] == pytest.approx(h / (0.87 * tan_s) + flat)
    # 容量=65.7 人/分・m × 幅 2.0 m(SR11 (a))
    assert float(m.link_cap_per_min[0]) == pytest.approx(65.7 * 2.0)


def test_long_link_is_not_faster_than_walking(space):
    # 両端の離れた階段・エスカレーター・エレベーター(水平 100 m)でも水平に歩く速さを超えて動かない
    import dataclasses

    m = space.mesh
    v = np.full(m.n_links, 1.40)
    try:
        for k in (NV.LINK_STAIRS, NV.LINK_ESCALATOR, NV.LINK_ELEVATOR):
            space.mesh = dataclasses.replace(m, link_len_m=np.full(m.n_links, 100.0),
                                             link_kind=np.full(m.n_links, k, dtype=m.link_kind.dtype))
            tab, tba = space.link_times(v)
            assert np.all(tab >= 100.0 / 1.40 - 1e-6) and np.all(tba >= 100.0 / 1.40 - 1e-6)
    finally:
        space.mesh = m


def test_speed_is_the_body_attribute(space):
    # 歩く速さは体の属性(10f K21 (a)=母集団の seed から)=エンジンが決めた値ではない
    assert np.array_equal(space.v_desired, desired_speeds(1, np.arange(400)))


# ------------------------------------------------------------------ 受入: 速さの上限・面の上・着く
def _walk_agent(space, agent, origin_node, target_node, max_ticks=200):
    m = space.mesh
    ox, oy, of_ = m.anchor_x[origin_node], m.anchor_y[origin_node], m.anchor_fi[origin_node]
    aid = np.array([agent])
    changed, nox, noy, nof, ok = space.ensure_routes(aid, [ox], [oy], [of_], [target_node], [-1], [0.0], [0.0], [0])
    assert ok.all()
    t = np.zeros(1)
    wait = np.full(1, -1)
    pos = [(ox, oy, int(of_))]
    links = 0
    for tick in range(max_ticks):
        res = space.advance(aid, t, np.ones(1), wait, tick)
        t = res["t"]
        wait = res["wait"]
        pos.append((float(res["x"][0]), float(res["y"][0]), int(res["fi"][0])))
        links += int(res["links"][0])
        if res["arrived"][0]:
            break
    return pos, links, bool(res["arrived"][0])


def test_speed_bound_inside_and_arrival(space):
    m = space.mesh
    pos, links, arrived = _walk_agent(space, 7, 0, 2)
    assert arrived and links == 0
    vmax = float(space.v_desired[7]) * 60.0 * space.factor_max + 1e-6
    for (x0, y0, f0), (x1, y1, f1) in zip(pos[:-1], pos[1:]):
        assert math.hypot(x1 - x0, y1 - y0) <= vmax           # 3-4-5 (a) 歩く速さの上限
        assert _inside(m, f1, x1, y1)                         # 面の外に居ない
    assert pos[-1][:2] == pytest.approx((m.anchor_x[2], m.anchor_y[2]))


def test_crossing_floors_only_through_a_link(space):
    m = space.mesh
    pos, links, arrived = _walk_agent(space, 9, 0, 4)
    assert arrived and links == 1
    changes = [(a, b) for a, b in zip(pos[:-1], pos[1:]) if a[2] != b[2]]
    assert len(changes) == 1
    assert int(m.floor_code[pos[-1][2]]) == 1


def test_link_capacity_and_first_come_first_served(space):
    m = space.mesh
    n = 300
    aid = np.arange(n)
    s6 = 6
    ox = np.full(n, m.anchor_x[s6])
    oy = np.full(n, m.anchor_y[s6])
    of_ = np.full(n, m.anchor_fi[s6])
    changed, nox, noy, nof, ok = space.ensure_routes(aid, ox, oy, of_, np.full(n, 3), np.full(n, -1), ox, oy, of_)
    assert ok.all()
    t = np.zeros(n)
    wait = np.full(n, -1)
    cap = int(space.cap_step[0])
    assert cap == 131
    res = space.advance(aid, t, np.ones(n), wait, 0)
    entered = (res["links"] > 0) | (res["t"] > 0) & (res["req"] < 0)
    assert int((res["req"] >= 0).sum()) == n - cap               # 超えた分は前で待つ
    # 先着順(同じ刻みに着いた体は番号の順)
    assert np.all(res["req"][:cap] < 0) and np.all(res["req"][cap:] >= 0)
    assert np.all(res["wait"][cap:] == 0)
    res2 = space.advance(aid, res["t"], np.ones(n), res["wait"], 1)
    assert int((res2["req"] >= 0).sum()) == max(0, n - 2 * cap)
    _ = entered


def test_unique_position_per_agent_per_step(space):
    # 3-4-5 (b): 体ごとに位置は 1 つ(配列の 1 行)=同じ体を 2 回渡しても同じ答え(状態は呼び手の 1 行だけ)
    m = space.mesh
    aid = np.array([11, 11])
    ox = np.full(2, m.anchor_x[0])
    oy = np.full(2, m.anchor_y[0])
    of_ = np.full(2, m.anchor_fi[0])
    space.ensure_routes(aid[:1], ox[:1], oy[:1], of_[:1], [2], [-1], ox[:1], oy[:1], of_[:1])
    res = space.advance(aid, np.zeros(2), np.ones(2), np.full(2, -1), 0)
    assert res["x"][0] == res["x"][1] and res["y"][0] == res["y"][1]


def test_resume_replans_the_same_route(space, tmp_path):
    m = space.mesh
    pos_a, _l, _a = _walk_agent(space, 21, 0, 2)
    # 経路の置き場を捨てて(再開)、状態(出発の点・行き先)から引き直すと同じ点の並び
    s, n = int(space.pool.r_start[21]), int(space.pool.r_len[21])
    space.pool.drop(21)
    aid = np.array([21])
    ox = np.array([m.anchor_x[0]], dtype=np.float32)
    oy = np.array([m.anchor_y[0]], dtype=np.float32)
    of_ = np.array([m.anchor_fi[0]], dtype=np.int8)
    changed, *_r, ok = space.ensure_routes(aid, ox, oy, of_, [2], [2], ox, oy, of_)
    assert not changed[0] and ok[0]
    pos_b, _l, _a = _walk_agent(space, 21, 0, 2)
    assert pos_a == pos_b


def test_engine_does_not_decide_for_the_person():
    """AST: nav1 は判断の層・LLM・選び手を読まない(速さは体の属性・経路は既定の重み=宣言)。"""
    tree = ast.parse(SRC.read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
        elif isinstance(node, ast.Import):
            mods.update(a.name for a in node.names)
    banned = ("shibuya.llm", "shibuya.engine.decision", "shibuya.engine.chooser", "shibuya.engine.intent",
              "shibuya.engine.classical", "shibuya.engine.activity")
    assert not [m for m in mods if m.startswith(banned)]
    assert any("既定の重み" in e and "本人の判断ではない" in e for e in N.NAV1_EXPEDIENTS)


def test_p_notice_tiny_distance_is_one_without_overflow():
    """連続の位置で出る、ごく近い距離の一次検出(s^e が溢れる所)は極限の 1(NaN にしない)。"""
    import warnings

    from shibuya.perception.p_notice import p1_primary

    with warnings.catch_warnings():
        warnings.simplefilter("error")
        p = p1_primary(np.array([1e-9, 1e-3, 30.0]), 30.0)
    assert p[0] == 1.0 and np.isfinite(p).all() and 0.0 < p[2] < 1.0


# ------------------------------------------------------------------ 段 1 の検収の直し(M4・L3・L4・M5・問い 3/4)
def test_m4_density_denominator_is_area_times_population_scale():
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        out, _ = SY.build_synth(Path(td))
        mesh = NV.load_navmesh(out)
        full = N.NavSpace(mesh, SY.fake_assets(), world_dir=out, seed=1, n_agents=10, tick_seconds=60)
        part = N.NavSpace(mesh, SY.fake_assets(), world_dir=out, seed=1, n_agents=10, tick_seconds=60,
                          population_scale=0.01)
        d = np.full(full.walkable_area_m2.size, 20.0)
        assert np.allclose(part.density_area_m2, full.walkable_area_m2 * 0.01)
        # 同じ体の数でも抽出の割合が小さいほど人/m² は大きい=段が上がり、Kladek の速さは落ちる
        assert (part.density_stage(d) >= full.density_stage(d)).all() and (part.density_stage(d) > 0).any()
        assert (part.kladek_factor(np.arange(d.size), d) <= full.kladek_factor(np.arange(d.size), d)).all()
        assert part.manifest_fields()["navmesh"]["density_population_scale"] == 0.01
        # 0 や負は 1(合成の世界の宣言)
        assert N.NavSpace(mesh, SY.fake_assets(), world_dir=out, seed=1, n_agents=10, tick_seconds=60,
                          population_scale=0.0).population_scale == 1.0


def test_l3_ramp_inside_is_on_the_line_and_within_the_speed_bound():
    # 経路: 点 0 (0,0) → スロープ(接続口 0)→ 点 1 (100, 0)・所要 100 s。刻み 60 s で 1 刻み目は線の上の 60 m
    px = np.array([0.0, 100.0]); py = np.array([0.0, 0.0]); pfi = np.array([0, 1], dtype=np.int64)
    pt = np.array([0.0, 100.0]); plink = np.array([0, -1], dtype=np.int64); pnode = np.array([-1, -1], dtype=np.int32)
    out = [np.zeros(1) for _ in range(3)]
    ofi = np.zeros(1, dtype=np.int64); onode = np.zeros(1, dtype=np.int64); oarr = np.zeros(1, dtype=np.bool_)
    oreq = np.zeros(1, dtype=np.int64); owall = np.zeros(1); owalk = np.zeros(1); olinks = np.zeros(1, np.int64)
    for is_ramp, want_x in ((1, 60.0), (0, 100.0)):
        N.advance_kernel(np.zeros(1), np.array([0]), np.array([2]), px, py, pfi, pt, plink, pnode, np.ones(1),
                         np.array([60.0]), np.array([0]), np.array([is_ramp], dtype=np.uint8), out[0], out[1], out[2],
                         ofi, onode, oarr, oreq, owall, owalk, olinks)
        assert out[1][0] == pytest.approx(want_x)  # スロープは線の上・階段などは半分を過ぎたら出口の端(宣言の跳び)
        assert int(ofi[0]) == 1


def test_l4_space_argument_beats_the_environment(monkeypatch):
    monkeypatch.setenv("SHIBUYA_SPACE", "legacy")
    assert N.space_env_override("nav1") == "nav1"
    assert N.space_env_override(None) == "legacy"
    monkeypatch.delenv("SHIBUYA_SPACE")
    assert N.space_env_override(None) == N.DEFAULT_SPACE == "nav1"  # 〔段 5-1b・版上げ 4 回目〕既定は nav1(段 1 は legacy)
    import inspect

    assert inspect.signature(N.NavSpace.__init__).parameters["tick_seconds"].default is inspect.Parameter.empty


def test_q4_production_world_is_the_one_with_a_build_hash(tmp_path):
    assert not N.is_production_world(tmp_path) and not N.is_production_world(None)
    (tmp_path / "build_manifest.json").write_text('{"build_hash": "abc"}', encoding="utf-8")
    assert N.is_production_world(tmp_path)
    (tmp_path / "build_manifest.json").write_text('{"schema": "x"}', encoding="utf-8")
    assert not N.is_production_world(tmp_path)


def test_m5_hop_walk_steps_legacy_is_one_step_per_node_and_nav1_uses_the_speed():
    from shibuya.engine.calendar_self import hop_walk_steps

    steps = np.array([3, 0, 10])
    assert hop_walk_steps(steps, None, [0, 1, 2]).tolist() == [3, 0, 10]
    hop = np.array([0.5, 0.25, 0.4])  # 節 1 つの刻み(平均の辺長 ÷ 本人の m/刻み)
    assert hop_walk_steps(steps, hop, [0, 1, 2]).tolist() == pytest.approx([1.5, 0.0, 4.0])
    src = (SRC.parents[1] / "calendar2" / "layer.py").read_text(encoding="utf-8")
    assert "hop_walk_steps(" in src


def test_q3_b6_mark_text_for_nav1_and_no_b8():
    from shibuya.engine import proximity as P

    m = P.marks_for("nav1")
    assert set(m) == {"B6"} and "面の上" in m["B6"]
    assert set(P.marks_for("node")) == {"B6", "B8"}


def test_m4a_surface_counts_leave_out_the_agents_inside_buildings(space):
    from types import SimpleNamespace

    from shibuya.agents.state import Activity

    m = space.mesh
    ax, ay, af = space.anchor_of(np.array([0, 0, 0, 0, 0, 0]))
    xy = np.stack([np.full(6, ax[0]), np.full(6, ay[0])], axis=1).astype(np.float32)
    xy[1] += 1.0  # 1 は入口の点から外れて面の上に立ち止まった体
    cell, _b = space.cells(xy[:, 0], xy[:, 1], np.full(6, af[0]))
    reg = SimpleNamespace(
        nav_fi=np.full(6, af[0], dtype=np.int8), node=np.zeros(6, dtype=np.int32), cell=cell.astype(np.int32),
        activity=np.array([int(Activity.IDLE), int(Activity.IDLE), int(Activity.MOVING), int(Activity.SHOPPING),
                           int(Activity.IDLE), int(Activity.SLEEPING)], dtype=np.int8),
        xy=xy, nav_tgt=np.array([-1, -1, 3, -1, -1, -1], dtype=np.int32),
        poi_ref=np.array([-1, -1, -1, -1, 2, -1], dtype=np.int32), queue_poi=np.full(6, -1, dtype=np.int32))
    got = space.surface_counts(reg)
    # 数えるのは 1(面の上に立ち止まった)と 2(移動中)だけ: 0=入口の点・3=購入・4=在店・5=就寝
    assert int(got.sum()) == 2 and int(got[int(cell[1])]) >= 1
    _ = m
