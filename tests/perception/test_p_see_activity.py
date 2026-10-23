"""5 段目 5c(D-117・第293)の活動 → 知覚の乗数は、第 1 期 1-2 で消した(決定 10-12 §1-6「係数で持たない」)。

1-2 の前: 看板の注視 p_see に活動の種別の乗数(表は既定で全部 1.0・腕 ``--p-see-activity`` の例は通話 0.49・連れとの会話
1.39=Hyman 2010 表 2)を掛けていた。既定のランでは表が全部 1.0=効く道が無く、係数を 1.0 にした byte-check が 19 構成で
結果不変だった(記録 ``docs/bench/analysis/wallbounce-1012/p12/README.md``)。0.49・1.39 はパターン台帳 §10 の検証専用の値。
気づきの差は目の向き・心の向きの仕組み(CT2)から出す。

見るもの
(a) 乗数の表・検査の関数・腕の引数が無い(描画・ラン・CLI)。``run_day(p_see_activity=…)`` は ``None`` 以外を止める
(b) 看板の注視は p_see 1 つの値だけ: 結果は従来の式 ``gate_stage1(1, p_see, (tick, 体, 看板))`` と同じ・既定 1.0 は抽選を
    引かない・活動の種別で変わらない
(c) 活動の種別の読み(親しみの層が「入った回」の露出を種別ごとに数える計数の鍵として残した)
(d) 親しみの表の「入った回」の露出はスカラーの p_see だけ(乗数つきの ``p_see_fn`` は無い)
(e) run の manifest ``p_see_activity`` は欄を残して値は null
"""

from __future__ import annotations

import inspect
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.state import Activity, ActivityKind, AgentKind, AgentState
from shibuya.engine.familiarity import FamiliarityLayer
from shibuya.perception import renderer as RD
from shibuya.perception.attention import gate_stage1
from shibuya.perception.renderer import P_SEE_ACTIVITY_KINDS, Renderer
from shibuya.world.state import World


def crowd(n: int = 60, *, activity_columns: bool = False, seed: int = 13):
    """看板のあるセルへ全員を置いた合成場面。"""
    w = World.synthetic(n_cells=9, seed=2)
    a = AgentState(n, activity_columns=activity_columns)
    g = np.random.default_rng(3)
    with a.writable():
        a.xy[:] = g.uniform(0.0, 80.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 5_000
        a.last_result_tick[:] = 1
    probe = Renderer(w, a, seed=seed)
    cell = next(c for c in range(9) if probe._signage_body(c) is not None)
    with a.writable():
        a.cell[:] = cell
    w.cells.density[:] = w.compute_density(a.cell)
    return w, a, cell


# ---------------------------------------------------------------- (a) 乗数が無い
def test_the_multiplier_table_and_the_arm_are_gone():
    for name in ("P_SEE_BY_ACTIVITY", "check_p_see_activity"):
        assert not hasattr(RD, name), name
    assert "p_see_activity" not in inspect.signature(Renderer).parameters
    w, a, _ = crowd(4)
    r = Renderer(w, a)
    for name in ("effective_p_see", "p_see_activity_summary", "_p_see_mult", "_p_see_identity", "signage_by_kind",
                 "signage_effective_p", "p_see_activity"):
        assert not hasattr(r, name), name
    assert "p_see_fn" not in inspect.signature(FamiliarityLayer).parameters


def test_run_day_refuses_a_multiplier_table():
    from shibuya.engine.run import run_day

    with pytest.raises(ValueError, match="1-2"):
        run_day(n_agents=20, seed=2, ticks=5, p_see_activity={"companion_talk": 1.39})


def test_cli_has_no_flag():
    src = Path("src/shibuya/cli.py").read_text(encoding="utf-8")
    assert "--p-see-activity" not in src
    assert "p_see_activity=args" not in src


# ---------------------------------------------------------------- (b) p_see は 1 つの値だけ
def test_gate_equals_the_old_formula_and_ignores_the_activity():
    """ゲートの結果は従来の式 gate_stage1(1, p_see, (tick, 体, 看板)) と同じ(活動の種別に依らない)。"""
    w, a, cell = crowd(40)
    with a.writable():
        a.activity[: a.n // 2] = int(Activity.MOVING)
        a.activity[a.n // 2:] = int(Activity.CONVERSING)
    r = Renderer(w, a, seed=13, signage_p_see=0.3)
    poi = r._signage_poi(cell)
    for t in (5, 900):
        got = [r._signage_seen(i, cell, t) for i in range(a.n)]
        want = [bool(gate_stage1(1, 0.3, seed=13, domain_counters=(t, i, poi))[0]) for i in range(a.n)]
        assert got == want
    assert r.signage_gate_draws == 2 * a.n


def test_default_p_see_draws_nothing():
    w, a, cell = crowd(30)
    r = Renderer(w, a, seed=13)
    assert all(r._signage_seen(i, cell, 700) for i in range(a.n))
    assert (r.signage_gate_draws, r.signage_gate_shown) == (0, 0)


# ---------------------------------------------------------------- (c) 活動の種別の読み(計数の鍵)
def test_activity_classes_follow_the_state():
    w, a, _ = crowd(8, activity_columns=True)
    with a.writable():
        a.activity[:] = [int(Activity.MOVING), int(Activity.MOVING), int(Activity.SHOPPING),
                         int(Activity.IDLE), int(Activity.CONVERSING), int(Activity.SLEEPING),
                         int(Activity.RIDING), int(Activity.IDLE)]
        a.activity_kind[:] = [ActivityKind.MOVE_TO, ActivityKind.WANDER, ActivityKind.IN_SHOP,
                              ActivityKind.IN_PLACE, ActivityKind.IN_PLACE, ActivityKind.NONE,
                              ActivityKind.MOVE_TO, ActivityKind.NONE]
    r = Renderer(w, a, seed=1)
    names = [P_SEE_ACTIVITY_KINDS[r.activity_class_of(i)] for i in range(8)]
    assert names == ["move_to", "wander", "in_shop", "in_place", "companion_talk", "in_place",
                     "move_to", "in_place"]
    assert [P_SEE_ACTIVITY_KINDS[k] for k in r.activity_classes(np.arange(8))] == names
    # 活動層の無いラン: 物理の状態(歩行=目的地つき移動・在店=在店)
    w2, b, _ = crowd(3)
    with b.writable():
        b.activity[:] = [int(Activity.MOVING), int(Activity.SHOPPING), int(Activity.WAITING)]
    r2 = Renderer(w2, b, seed=1)
    assert [P_SEE_ACTIVITY_KINDS[r2.activity_class_of(i)] for i in range(3)] == [
        "move_to", "in_shop", "in_place"]
    assert "phone" in P_SEE_ACTIVITY_KINDS  # 鍵だけ(旗は D-121 O3)


# ---------------------------------------------------------------- (d) 露出の入った回
def test_familiarity_entry_uses_the_scalar_p():
    n = 30
    a = AgentState(n, familiarity_columns=True, familiarity_k=8)
    with a.writable():
        a.cell[:] = 0
    tab = np.array([5], dtype=np.int64)  # セル 0 の看板=POI 5
    base = FamiliarityLayer(n, 8, signage_poi_by_cell=tab, p_see=1.0, seed=1)
    ea, _ = base._signage_on_entry(10, np.arange(n), np.zeros(n, dtype=np.int64), set())
    assert ea.size == n
    part = FamiliarityLayer(n, 8, signage_poi_by_cell=tab, p_see=0.3, seed=1)
    got = part._signage_on_entry(10, np.arange(n), np.zeros(n, dtype=np.int64), set())[0]
    want = [i for i in range(n) if gate_stage1(1, 0.3, seed=1, domain_counters=(10, i, 5))[0]]
    assert got.tolist() == want


# ---------------------------------------------------------------- (e) ラン
def test_run_manifest_keeps_the_field_as_null():
    from shibuya.engine.run import run_day

    res = run_day(n_agents=60, seed=2, ticks=120, vocab_version="v3", signage_p_see=0.3)
    m = res.run_manifest_fields()
    assert "p_see_activity" in m and m["p_see_activity"] is None
