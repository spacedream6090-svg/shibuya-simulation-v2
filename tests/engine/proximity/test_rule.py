"""第 2 期 2-2 段 11a: 判定の規則 ``ProximityRule``・切替口・気づく確率 p(d)(合成の体)。

アジェンダ §2-1 の不変条件(合成の 2 体):

- 別セルの 1 m 隣は会話できる(腕 distance)・今の判定(同じセル)では話せない。
- 同セルの 3 m は会話できない(腕 distance)・今の判定では話せる。
- 層が違う 1 m は会話できない(地上とデッキ)。
- B5: 同じ単位(在席中の POI の区画)の中なら距離を見ずに会話できる(つなぎ)。
- 舞台の外(セル −1)は話せない。

ほか: p(d) が R-62 の 2 点(10.4 m で 75%・23.5 m で 25%)を通る・感度の腕 1.0/2.5 m・離脱 d+1 m・気づく抽選の鍵が
状態を持たない(同じ組と時刻なら同じ)・腕の検査。
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.engine import proximity as P
from shibuya.engine import resolve as R


def agents(xy, cell, band=None, unit=None):
    n = len(xy)
    reg = SimpleNamespace(
        xy=np.asarray(xy, dtype=np.float32), cell=np.asarray(cell, dtype=np.int32),
        band=np.zeros(n, np.int8) if band is None else np.asarray(band, dtype=np.int8),
        poi_ref=np.full(n, -1, np.int32) if unit is None else np.asarray(unit, dtype=np.int32),
    )
    return SimpleNamespace(registry=reg, n=n)


RULE = P.ProximityRule(d=2.0, seed=12345)
A0, B1 = np.array([0]), np.array([1])


def _both(ag):
    """(腕 distance の答え, 今の判定=同じセルの答え)。"""
    return (bool(R.talk_within_reach(ag, A0, B1, by_distance=False, rule=RULE)[0]),
            bool(R.talk_within_reach(ag, A0, B1, by_distance=False)[0]))


def test_other_cell_1m_can_talk_only_in_distance():
    assert _both(agents([(0, 0), (0, 1)], [7, 8])) == (True, False)


def test_same_cell_3m_cannot_talk_in_distance():
    assert _both(agents([(0, 0), (3, 0)], [7, 7])) == (False, True)


def test_other_band_1m_cannot_talk():
    ag = agents([(0, 0), (1, 0)], [7, 9], band=[0, 1])        # 地上とデッキ
    assert _both(ag) == (False, False)
    ag = agents([(0, 0), (0, 0)], [7, 7], band=[-1, 0])        # 同じ座標でも地下と地上は話せない
    assert bool(RULE.reach(ag, A0, B1)[0]) is False


def test_same_unit_talks_without_distance_b5():
    ag = agents([(0, 0), (40, 0)], [7, 7], unit=[12, 12])      # 同じ店の区画の中・40 m
    assert _both(ag) == (True, True)
    assert bool(RULE.by_unit(ag, A0, B1)[0]) is True
    ag = agents([(0, 0), (40, 0)], [7, 7], unit=[12, 13])      # 別の区画
    assert _both(ag)[0] is False


def test_off_stage_cannot_talk_and_boundary_is_inclusive():
    assert _both(agents([(0, 0), (0, 0)], [-1, -1]))[0] is False
    assert _both(agents([(0, 0), (2, 0)], [7, 8]))[0] is True    # 2 m ちょうど(境を含む)
    assert _both(agents([(0, 0), (2.0001, 0)], [7, 7]))[0] is False


def test_rule_none_and_cell_mode_keep_the_current_judgement():
    ag = agents([(0, 0), (0, 1), (3, 0)], [7, 8, 7])
    a, b = np.array([0, 0]), np.array([1, 2])
    now = R.talk_within_reach(ag, a, b, by_distance=False)
    assert now.tolist() == [False, True]
    assert R.talk_within_reach(ag, a, b, by_distance=False, rule=None).tolist() == now.tolist()
    cell_rule = P.ProximityRule(mode=P.MODE_CELL)
    assert R.talk_within_reach(ag, a, b, by_distance=False, rule=cell_rule).tolist() == now.tolist()
    assert R.talk_within_reach(ag, a, b, by_distance=True, rule=cell_rule).tolist() == [False, False]


@pytest.mark.parametrize("d,want", [(1.0, False), (2.0, False), (2.5, True)])
def test_sensitivity_arms(d, want):
    ag = agents([(0, 0), (2.2, 0)], [7, 8])
    rule = P.ProximityRule(d=d)
    assert bool(rule.reach(ag, A0, B1)[0]) is want
    assert rule.leave_m == pytest.approx(d + 1.0)
    # 離脱はヒステリシス(d+1 m): 成立しない距離でも続けられる幅がある
    ag2 = agents([(0, 0), (d + 0.5, 0)], [7, 7])
    assert bool(rule.reach(ag2, A0, B1)[0]) is False and bool(rule.stay(ag2, A0, B1)[0]) is True


def test_d_default_is_the_talk_open_constant():
    assert P.D_DEFAULT == R.TALK_OPEN_METERS == 2.0
    assert P.LEAVE_MARGIN_M == R.TALK_LEAVE_METERS - R.TALK_OPEN_METERS


# ================================================================= 気づく確率(B4・R-62)
def test_notice_curve_passes_r62_two_points():
    p = P.notice_p([P.NOTICE_D75_M, P.NOTICE_D25_M])
    assert p[0] == pytest.approx(0.75, abs=1e-12) and p[1] == pytest.approx(0.25, abs=1e-12)
    assert (P.NOTICE_D75_M, P.NOTICE_D25_M) == (10.4, 23.5)
    assert P.NOTICE_D50_M == pytest.approx(16.95) and P.NOTICE_SCALE_M == pytest.approx(5.9621, abs=1e-4)
    d = np.linspace(0, 120, 241)
    pd = P.notice_p(d)
    assert np.all(np.diff(pd) < 0) and pd[0] < 1.0               # 連続・単調に減る(区切りではない)
    assert P.notice_p(P.NOTICE_CUTOFF_M) < 1e-6                 # 打ち切りの距離では無視できる
    assert P.notice_p(2.0) == pytest.approx(0.925, abs=1e-3)    # R-79 §8-1 の再計算(2 m で 0.925)


def test_notice_draws_are_counter_streams_stateless_and_uniform():
    """検収・親の判断 A1: 気づく抽選は 10c の counter の流れ(用途名 proximity.notice・k19 の並べ方=時刻の鍵・体・相手)。"""
    from shibuya.core.rng import k19_counters, run_tick_key, stream

    rule = P.ProximityRule(seed=11, day_key0=3, step_seconds=60)
    a = np.arange(4_000) % 500
    b = (np.arange(4_000) * 7) % 499
    u1 = rule.notice_u(100, a, b)
    tk = run_tick_key(3, 100, 60)
    assert u1[17] == stream(11, P.NOTICE_DOMAIN, *k19_counters(tk, int(a[17]), int(b[17]))).random()
    assert k19_counters(tk, 1, 2)[0] == 0                      # 0 語目は空ける(K19)
    assert np.array_equal(u1, rule.notice_u(100, a, b)) and np.all((u1 >= 0) & (u1 < 1))
    assert abs(float(u1.mean()) - 0.5) < 0.02                  # 一様
    assert not np.array_equal(u1, rule.notice_u(101, a, b))    # 時刻で変わる
    assert not np.array_equal(u1, rule.notice_u(100, b, a))    # 向きで変わる(体と相手)
    assert not np.array_equal(u1, P.ProximityRule(seed=12, day_key0=3).notice_u(100, a, b))   # seed で変わる
    # 規模に依らない: 1 組だけ引いても同じ値(鍵は組と時刻だけ)
    assert rule.notice_u(100, a[17:18], b[17:18])[0] == u1[17]
    # 親の判断 10-14 の 1: 配列で引いた値は 1 組ずつ stream で引いた値と全部同じ(意味を変えない)
    loop = np.array([stream(11, P.NOTICE_DOMAIN, *k19_counters(tk, int(x), int(y))).random()
                     for x, y in zip(a.tolist(), b.tolist())])
    assert np.array_equal(u1, loop)
    assert rule.notice_u(100, np.zeros(0, np.int64), np.zeros(0, np.int64)).shape == (0,)


def test_notice_streams_pass_the_k19_overlap_check():
    """K19 の重なりの検査の控え(StreamRecorder)に載り、重なりも作り直しも無い。"""
    from shibuya.engine import rng_audit as RA

    rule = P.ProximityRule(seed=5)
    with RA.StreamRecorder() as rec:
        for t in range(20):
            rule.notice_u(t, np.arange(50), np.arange(50)[::-1])
    st = rec.analyze()
    assert st[P.NOTICE_DOMAIN].streams == 1000 and st[P.NOTICE_DOMAIN].max_blocks == 1
    assert RA.check_overlaps(st) == []
    sites = [s for s in RA.scan_sites(Path("src/shibuya")) if s.domain == P.NOTICE_DOMAIN]
    assert [(s.func, s.verdict) for s in sites] == [("ProximityRule.notice_u", RA.SAFE_STATIC)]


def test_edge_view_reach_equals_reach():
    """検収 M2: 同席と知人出現が共有する辺の見え方の「届く」は ``reach`` と同じ答え(単位は打ち切りの外でも届く)。"""
    rng = np.random.default_rng(3)
    n = 2000
    ag = agents(rng.uniform(-200, 200, (n, 2)), rng.integers(-1, 4, n), band=rng.integers(-1, 2, n),
                unit=np.where(rng.random(n) < 0.3, rng.integers(0, 5, n), -1))
    a, b = rng.integers(0, n, 30_000), rng.integers(0, n, 30_000)
    inr, dist, reach = RULE.edge_view(ag, a, b)
    assert np.array_equal(reach, RULE.reach(ag, a, b)) and reach.sum() > 50
    assert np.array_equal(inr, RULE.notice_range(ag, a, b)[0])


def test_resume_arm_check():
    """検収 M1: 再開の腕の検査(見出しの proximity が無ければ cell)。"""
    prev = (P.arm(), P.d())
    try:
        P.set_arm("cell")
        P.check_resume(None)
        with pytest.raises(ValueError, match="近接の腕"):
            P.check_resume({"mode": "distance", "d_m": 2.0})
        P.set_arm("distance")
        P.set_d(2.0)
        P.check_resume({"mode": "distance", "d_m": 2.0})
        for saved in (None, {"mode": "cell", "d_m": None}, {"mode": "distance", "d_m": 2.5}):
            with pytest.raises(ValueError, match="近接の腕"):
                P.check_resume(saved)
    finally:
        P.set_arm(prev[0])
        P.set_d(prev[1])
    assert P.header_fields(None) is None
    assert P.header_fields(P.ProximityLayer(P.ProximityRule(d=2.5))) == {"mode": "distance", "d_m": 2.5}


def test_notice_range_prefilter_equals_the_full_definition():
    """``notice_range`` は float32 の距離で先に落とす(上位集合)=全部を ``_parts`` で見たときと同じ答え。"""
    rng = np.random.default_rng(11)
    n = 3000
    ag = agents(rng.uniform(-150, 150, (n, 2)), rng.integers(-1, 4, n), band=rng.integers(-1, 2, n))
    a = rng.integers(0, n, 20_000)
    b = rng.integers(0, n, 20_000)
    rule = P.ProximityRule()
    inr, dist = rule.notice_range(ag, a, b)
    on, sb, d, _u = rule._parts(ag, a, b)
    want = on & sb & (d <= rule.notice_cutoff_m)
    assert np.array_equal(inr, want) and want.sum() > 100
    assert np.array_equal(dist[want], d[want])


def test_noticed_needs_same_band_stage_and_cutoff():
    ag = agents([(0, 0), (0, 0), (0, 0), (150, 0)], [1, 1, -1, 1], band=[0, 1, 0, 0])
    rule = P.ProximityRule(seed=1)
    a = np.zeros(3, dtype=np.int64)
    inr, dist = rule.notice_range(ag, a, np.array([1, 2, 3]))
    assert inr.tolist() == [False, False, False]                # 層が違う・舞台の外・打ち切りの外
    hits = sum(int(rule.noticed(ag, t, np.array([0]), np.array([0]))[0]) for t in range(2000))
    assert 0.90 < hits / 2000 < 0.99                            # 0 m で p ≈ 0.945


# ================================================================= 切替口
def test_arm_and_d_switches_are_checked():
    prev_arm, prev_d = P.arm(), P.d()
    try:
        P.set_arm("distance")
        assert P.arm() == "distance"
        P.set_d("2.5")
        assert P.d() == 2.5
        with pytest.raises(ValueError):
            P.set_arm("grid")
        with pytest.raises(ValueError):
            P.set_d(3.0)
        with pytest.raises(ValueError):
            P.set_d("x")
    finally:
        P.set_arm(prev_arm)
        P.set_d(prev_d)
    assert P.ProximityRule().is_distance and not P.ProximityRule(mode="cell").is_distance
    with pytest.raises(ValueError):
        P.ProximityRule(mode="grid")


def test_manifest_fields_cell_and_distance():
    cell = P.manifest_fields(None)
    assert cell["mode"] == "cell" and cell["d_m"] is None and cell["index_builds"] is None
    assert list(cell) == list(P.CONFIG_KEYS) + list(P.OBSERVED_KEYS)
    lay = P.ProximityLayer(P.ProximityRule(geometry="node"))
    dist = P.manifest_fields(lay)
    assert dist["mode"] == "distance" and dist["d_m"] == 2.0 and dist["leave_m"] == 3.0
    assert dist["b5_radius_m"] == 10.3 and set(dist["marks"]) == {"B6", "B8"}
    assert set(P.marks_for("edge")) == {"B6"}                   # B8 は node 幾何だけ
    assert dist["notice"]["d75_m"] == 10.4 and "R-62" in dist["notice"]["source"]
    assert dist["schema"] == "shibuya.proximity/3" and "philox_array" in dist["notice"]["rng"]


def test_layer_meter_counts_unit_occupancy():
    ag = agents([(0, 0)] * 6, [1, 1, 1, -1, 2, 2], unit=[5, 5, 5, 5, 6, -1])
    lay = P.ProximityLayer(P.ProximityRule())
    idx = lay.build_index(ag)
    assert len(idx) == 5                                        # 舞台の外(セル −1)は入れない
    m = lay.observed()
    assert m["index_builds"] == 1 and m["indexed_max"] == 5
    assert m["unit_occupancy_max"] == 3 and m["units_occupied_max"] == 2
    assert m["unit_occupancy_hist"]["1"] == 1 and m["unit_occupancy_hist"]["2-4"] == 1
    # 検収 L3: 計器は読むだけの写し・欄の付け替えと消すのは断る
    with pytest.raises(TypeError):
        lay.meter_view["index_builds"] = 9
    with pytest.raises(TypeError):
        lay.meter_view["unit_occupancy_hist"]["1"] = 9
    with pytest.raises(AttributeError):
        lay.rule = P.ProximityRule(d=1.0)
    with pytest.raises(AttributeError):
        del lay.rule
    assert lay.meter_view["index_builds"] == 1


# ================================================================= 親の判断 10-14 の 2: B5 の単位は店のセルの中の体だけ
def test_unit_needs_the_store_cell():
    """在席の印があっても、その店のセルの外に居る体(店を出て歩いている体)は単位に数えない。"""
    poi_cell = np.array([7, 8, 7])                              # POI 0・2 はセル 7・POI 1 はセル 8
    rule = P.ProximityRule(d=2.0, poi_cell=poi_cell)
    # 体 0: POI 0 でセル 7(中)・体 1: POI 0 でセル 9(外=歩き出した)・体 2: POI 0 でセル 7(中・40 m)・体 3: POI 2 でセル 7
    ag = agents([(0, 0), (40, 0), (40, 0), (1, 0)], [7, 9, 7, 7], unit=[0, 0, 0, 2])
    assert rule.units(ag).tolist() == [0, -1, 0, 2]
    assert rule.reach(ag, np.array([0, 0, 0]), np.array([1, 2, 3])).tolist() == [False, True, True]
    assert rule.by_unit(ag, np.array([0, 0]), np.array([1, 2])).tolist() == [False, True]
    assert RULE.reach(ag, np.array([0]), np.array([1])).tolist() == [True]     # 絞らない規則(合成の試験だけ)は今のまま
    inr, _d, reach = rule.edge_view(ag, np.array([0, 0, 0]), np.array([1, 2, 3]))
    assert reach.tolist() == rule.reach(ag, np.array([0, 0, 0]), np.array([1, 2, 3])).tolist()
    # 索引の単位も絞った単位(描画の B5 の単位の仲間と束の相手の候補)
    lay = P.ProximityLayer(rule)
    idx = lay.build_index(ag)
    assert sorted(idx.unit_members(0).tolist()) == [0, 2]
    assert P.batch_partners(ag, rule, np.array([0, 1, 2]), np.array([0])).tolist() == [2]
    # POI の範囲の外の印は単位にしない・poi_cell は読むだけの写し
    ag2 = agents([(0, 0), (0, 0)], [7, 7], unit=[5, 5])
    assert rule.units(ag2).tolist() == [-1, -1]
    with pytest.raises(ValueError):
        rule.poi_cell[0] = 1
    poi_cell[0] = 99                                            # 元の配列を変えても規則は変わらない
    assert rule.units(ag).tolist() == [0, -1, 0, 2]


def test_rule_from_requires_poi_cell():
    kw = dict(mode="distance", d_m=2.0, seed=1, day_key0=0, step_seconds=60, geometry="node")
    with pytest.raises(ValueError, match="poi_cell"):
        P.rule_from(poi_cell=None, **kw)
    r = P.rule_from(poi_cell=[3, 4], **kw)
    assert r.poi_cell.tolist() == [3, 4] and r == P.ProximityRule(d=2.0, seed=1)   # poi_cell は比べない(hash も)
    hash(r)
