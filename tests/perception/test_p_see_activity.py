"""5 段目 5c: 活動 → 知覚の乗数(D-117 M1 (a)・M2 (b)・M4 (a)・第293)。

正典: ``docs/design/v2-energy-classical-implementation-agenda.md`` §3・草案
``docs/design/v2-hunger-choice-attention-draft.md`` §3(Hyman 2010 表 2: 二人連れ 71.4 > 単独 51.3
=比 1.39・通話 25.0/51.3=0.49)。

見るもの
(a) 既定(乗数表なし=全部 1.0)は描画バイトも抽選も 1 バイトも動かない(p_see 1.0 と 0.30 の両方)
(b) 実効 p_see=min(1, p_see × 乗数[活動の種別])・同じカウンタの同じ u を比べる(腕どうしで単調)
(c) **p_see にだけ掛かる**(M4): 実効 p_see が 1 の体は乗数があっても描画が同じ
(d) 活動の種別の読み(会話の成立=連れとの会話中・活動層の種別・活動層の無いランは物理の状態)
(e) 親しみの表の「入った回」の露出も同じ実効 p_see(乗数表が全部 1.0 なら従来の経路)
(f) run の manifest ``p_see_activity`` と CLI ``--p-see-activity``
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import Activity, ActivityKind, AgentKind, AgentState
from shibuya.engine.familiarity import FamiliarityLayer
from shibuya.perception import templates as T
from shibuya.perception.attention import gate_stage1
from shibuya.perception.renderer import (
    P_SEE_ACTIVITY_KINDS,
    P_SEE_BY_ACTIVITY,
    Renderer,
    check_p_see_activity,
)
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


def renders(w, a, *, ticks=(700, 701, 702), **kw):
    r = Renderer(w, a, seed=13, **kw)
    out = []
    for t in ticks:
        r.prepare_tick(t)
        out.extend(r.render(i, tick=t, wake_reason=3).text for i in range(a.n))
    return r, out


# ---------------------------------------------------------------- 表の検査
def test_table_defaults_and_validation():
    assert set(P_SEE_BY_ACTIVITY) == set(P_SEE_ACTIVITY_KINDS)
    assert all(v == 1.0 for v in P_SEE_BY_ACTIVITY.values())
    assert check_p_see_activity(None) == dict(P_SEE_BY_ACTIVITY)
    got = check_p_see_activity('{"phone": 0.49, "companion_talk": 1.39, "move_to": 0.5}')
    assert (got["phone"], got["companion_talk"], got["move_to"], got["wander"]) == (0.49, 1.39, 0.5, 1.0)
    with pytest.raises(ValueError):
        check_p_see_activity({"running": 0.5})
    with pytest.raises(ValueError):
        check_p_see_activity({"phone": -0.1})


# ---------------------------------------------------------------- (a) 既定不変
@pytest.mark.parametrize("p_see", [1.0, 0.30])
def test_identity_table_is_byte_identical_and_draws_the_same(p_see):
    w, a, _ = crowd()
    with a.writable():
        a.activity[: a.n // 2] = int(Activity.MOVING)
        a.activity[a.n // 2:] = int(Activity.CONVERSING)
    r0, base = renders(w, a, signage_p_see=p_see)
    r1, same = renders(w, a, signage_p_see=p_see, p_see_activity=dict(P_SEE_BY_ACTIVITY))
    assert base == same
    assert (r0.signage_gate_draws, r0.signage_gate_shown) == (r1.signage_gate_draws, r1.signage_gate_shown)
    if p_see >= 1.0:
        assert r0.signage_gate_draws == 0  # 既定は抽選を 1 回も引かない(従来どおり)


def test_identity_gate_equals_the_old_formula():
    """乗数表が全部 1.0 のとき、ゲートの結果は従来の式 gate_stage1(1, p_see, (tick, 体, 看板)) と同じ。"""
    w, a, cell = crowd(40)
    r = Renderer(w, a, seed=13, signage_p_see=0.3)
    poi = r._signage_poi(cell)
    for t in (5, 900):
        got = [r._signage_seen(i, cell, t) for i in range(a.n)]
        want = [bool(gate_stage1(1, 0.3, seed=13, domain_counters=(t, i, poi))[0]) for i in range(a.n)]
        assert got == want


# ---------------------------------------------------------------- (b)(c) 乗数の効き
def test_effective_p_is_clipped_and_monotone_in_the_multiplier():
    w, a, cell = crowd(200)
    with a.writable():
        a.activity[:] = int(Activity.CONVERSING)  # 全員=連れとの会話中
    lo = Renderer(w, a, seed=13, signage_p_see=0.3)
    hi = Renderer(w, a, seed=13, signage_p_see=0.3, p_see_activity={"companion_talk": 1.39})
    np.testing.assert_allclose(hi.effective_p_see(np.arange(a.n)), 0.3 * 1.39)
    s_lo = [lo._signage_seen(i, cell, 700) for i in range(a.n)]
    s_hi = [hi._signage_seen(i, cell, 700) for i in range(a.n)]
    assert all(h for lw, h in zip(s_lo, s_hi) if lw)  # 同じ u を比べる=通った体は大きい p でも通る
    assert sum(s_hi) > sum(s_lo)
    # p_see 1.0 × 1.39 は 1 で切る=抽選を引かず全員が通る
    one = Renderer(w, a, seed=13, signage_p_see=1.0, p_see_activity={"companion_talk": 1.39})
    assert all(one._signage_seen(i, cell, 700) for i in range(a.n)) and one.signage_gate_draws == 0


def test_multiplier_touches_only_the_gate_not_the_b2_rows():
    """M4 (a): 実効 p_see が 1 のままの体(乗数 > 1 で切られる)は描画が 1 バイトも変わらない。"""
    w, a, _ = crowd()
    with a.writable():
        a.activity[:] = int(Activity.CONVERSING)
    _r0, base = renders(w, a)
    _r1, same = renders(w, a, p_see_activity={"companion_talk": 1.39, "phone": 0.0})
    assert base == same  # 通話の体はいない=phone 0.0 も効かない(旗は D-121 O3)


def test_move_to_half_drops_signage_only_for_walking_bodies():
    w, a, cell = crowd(100)
    with a.writable():
        a.activity[:50] = int(Activity.MOVING)
    r = Renderer(w, a, seed=13, p_see_activity={"move_to": 0.5})
    r.prepare_tick(700)
    shown = [T.TEMPLATES["B2.signage_empty"] not in r.render(i, tick=700, wake_reason=3).text
             for i in range(a.n)]
    assert all(shown[50:])                       # その場の体は 1.0 のまま
    assert 10 < sum(shown[:50]) < 40              # 歩いている体は 0.5 の二項(50 件)
    summ = r.p_see_activity_summary()
    assert summ["identity"] is False
    assert summ["by_kind"]["move_to"]["draws"] == 50 and summ["by_kind"]["in_place"]["draws"] == 0
    assert summ["effective_p_see"] == {"0.5000": 50, "1.0000": 50}


# ---------------------------------------------------------------- (d) 活動の種別の読み
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


# ---------------------------------------------------------------- (e) 露出の入った回
def test_familiarity_entry_uses_the_effective_p():
    n = 30
    a = AgentState(n, familiarity_columns=True, familiarity_k=8)
    with a.writable():
        a.cell[:] = 0
    tab = np.array([5], dtype=np.int64)  # セル 0 の看板=POI 5
    base = FamiliarityLayer(n, 8, signage_poi_by_cell=tab, p_see=1.0, seed=1)
    ea, _ = base._signage_on_entry(10, np.arange(n), np.zeros(n, dtype=np.int64), set())
    assert ea.size == n
    none = FamiliarityLayer(n, 8, signage_poi_by_cell=tab, p_see=1.0, seed=1,
                            p_see_fn=lambda ids: np.zeros(ids.size))
    assert none._signage_on_entry(10, np.arange(n), np.zeros(n, dtype=np.int64), set())[0].size == 0
    half = FamiliarityLayer(n, 8, signage_poi_by_cell=tab, p_see=1.0, seed=1,
                            p_see_fn=lambda ids: np.full(ids.size, 0.3))
    got = half._signage_on_entry(10, np.arange(n), np.zeros(n, dtype=np.int64), set())[0]
    want = [i for i in range(n) if gate_stage1(1, 0.3, seed=1, domain_counters=(10, i, 5))[0]]
    assert got.tolist() == want


# ---------------------------------------------------------------- (f) ラン
def test_run_manifest_and_mock_behaviour():
    from shibuya.engine.run import run_day

    kw = dict(n_agents=60, seed=2, ticks=120, vocab_version="v3")
    base = run_day(**kw)
    arm = run_day(p_see_activity={"move_to": 0.5, "companion_talk": 1.39}, signage_p_see=0.3, **kw)
    ref = run_day(signage_p_see=0.3, **kw)
    m = base.run_manifest_fields()["p_see_activity"]
    assert m["identity"] is True and m["table"] == dict(P_SEE_BY_ACTIVITY)
    ma = arm.run_manifest_fields()["p_see_activity"]
    assert ma["identity"] is False and ma["table"]["move_to"] == 0.5
    # mock はプロンプトを読まない=行動(checkpoint)は看板の注視で動かない(M4 は描画だけ)
    assert arm.final_hash == ref.final_hash
    with pytest.raises(ValueError):
        run_day(p_see_activity={"bogus": 1.0}, **{**kw, "ticks": 5})


def test_cli_has_the_flag():
    from pathlib import Path

    assert "--p-see-activity" in Path("src/shibuya/cli.py").read_text(encoding="utf-8")
