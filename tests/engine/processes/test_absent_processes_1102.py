"""〔11-02r §1 #7〕「無い」と宣言した過程 5 件を止める切替口 ``engine.absent_processes`` の試験(過程ごとの正と負の対照)。

各過程について、既定(腕 stopped)では世界を変えない(件数 0)・切替口(腕 legacy)では前の版と同じに動くことを、過程を直に
組んで確かめる。止めない判断(世帯の消費・倒れる事象そのもの・ポイ捨ての腕)はこの腕に依らないことも見る。ランの全体
(manifest の節・実行器の受け渡し・CLI の口)は小さな合成世界の run_day で確かめる。記録 ``docs/bench/analysis/s2e-1102/README.md``。
正しい不合格(11-02r #7「街路にごみが残る・倒れた人が運ばれない」)は過程の試験で数で見る。

時間の方針(11-02r §2-2): 本試験は刻みの番号を決め打ちしない。時刻は世界の時刻(秒)で書き、過程に渡す刻みの番号は刻みの幅
``STEP_S`` から :func:`_k` で都度求める(過程も同じ幅で組む)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.core.time_consts import SECONDS_PER_DAY, SECONDS_PER_HOUR, SECONDS_PER_MINUTE
from shibuya.engine import absent_processes as AP
from shibuya.engine import resolve as R
from shibuya.engine.processes.civic import InfraLoadProcess, PublicServiceDispatchProcess
from shibuya.engine.processes.goods_flow import (
    COLLECT_WINDOW,
    HOUSEHOLD_CONSUME_MINUTE,
    StreetCleaningProcess,
    WasteCollectionProcess,
)
from shibuya.engine.processes.logistics import ROADWORK_WINDOW, RoadWorksProcess
from shibuya.engine.processes.runner import WorldProcessRunner
from shibuya.engine.processes.salient import SalientProcess
from shibuya.world.assets import ProcessAssets
from shibuya.world.processes.actual_log import ActualLog

from .conftest import make_agents, make_world
from .test_goods_flow import _setup as goods_setup


#: 刻みの幅[秒](過程を組むときに渡す)。
STEP_S = 60


def _k(seconds: float) -> int:
    """世界の時刻[秒](日の頭から)→ その時刻を含む刻みの番号(幅 ``STEP_S`` から求める)。"""
    return int(seconds // STEP_S)


def _span(lo_s: float, hi_s: float) -> range:
    """世界の時刻 [lo_s, hi_s) の刻みの番号。"""
    return range(_k(lo_s), _k(hi_s))


def _log() -> ActualLog:
    return ActualLog("actual_log", retention_days=7, ticks_per_day=SECONDS_PER_DAY // STEP_S)


@pytest.fixture
def arm_restore():
    prev = AP.arm()
    yield
    AP.set_arm(prev)


# ================================================================= 切替口そのもの
def test_the_default_arm_is_stopped_and_names_are_checked(arm_restore):
    assert AP.DEFAULT_MODE == AP.MODE_STOPPED and AP.MODES == ("stopped", "legacy")
    assert AP.resolve(None) == AP.arm()
    with pytest.raises(ValueError):
        AP.set_arm("off")
    with pytest.raises(ValueError):
        AP.resolve("bogus")
    assert AP.PROCESSES == ("waste_collection", "street_cleaning", "road_works", "dispatch", "infra")
    assert set(AP.STOPPED_PROCESSES) == set(AP.PROCESSES)
    assert AP.stopped_flags("stopped") == {f"absent_{p}_stopped": 1 for p in AP.PROCESSES}
    assert AP.stopped_flags("legacy") == {f"absent_{p}_stopped": 0 for p in AP.PROCESSES}
    # 宣言(world/processes/absent.py)と 1 対 1
    from shibuya.world.processes import absent as AB

    ab = AB.by_id()
    for name, v in AP.STOPPED_PROCESSES.items():
        a = ab[v["absent"]]
        assert a.kind == "no_actor" and a.engine_stopped and a.world_process_id == v["world_process"], name
        assert v["anchor_kept"] == "・".join(a.keeps_anchor), name


def test_state_header_and_resume_check(arm_restore):
    assert AP.header_fields("stopped") == {"mode": "stopped"} and AP.header_fields("legacy") is None
    AP.set_arm("stopped")
    AP.check_resume({"mode": "stopped"})
    with pytest.raises(ValueError):
        AP.check_resume(None)  # 見出しに無い=版上げの前(legacy)のラン
    AP.set_arm("legacy")
    AP.check_resume(None)
    with pytest.raises(ValueError):
        AP.check_resume({"mode": "stopped"})


# ================================================================= ごみ収集(#103)
@pytest.mark.parametrize("mode", ["stopped", "legacy"])
def test_waste_collection(mode):
    world, agents, bundle = goods_setup(n_agents=30, n_cells=16)
    stores = np.arange(min(4, int(np.asarray(world.pois.cell).size)), dtype=np.int64)
    R.discard_to_bin(world, bundle, stores, np.ones(stores.size, dtype=np.int64), tick=_k(0),
                     slot=np.zeros(stores.size, dtype=np.int64))
    in_bins = int(bundle.goods.bins.sum())
    assert in_bins > 0
    bundle.goods.sell_many(np.array([0, 0, 1, 1]), tick=_k(SECONDS_PER_MINUTE))  # 世帯の消費の材料(test_goods_flow と同じ)
    with agents.writable():
        agents.registry.holdings[:4] = 1
    waste = WasteCollectionProcess(world, agents, ledger=bundle, tick_seconds=STEP_S, absent_processes=mode)
    lo, hi = COLLECT_WINDOW  # [分]
    for k in _span(lo * SECONDS_PER_MINUTE, hi * SECONDS_PER_MINUTE):
        waste.step(k)
    waste.step(_k(HOUSEHOLD_CONSUME_MINUTE * SECONDS_PER_MINUTE))  # 世帯の消費(#41)は腕に依らない
    assert waste.n_consumed > 0
    if mode == "stopped":  # ごみの収集は無い=ビンに溜まる一方(正しい不合格)
        assert waste.waste_g_collected == 0.0 and waste.n_stops == 0 and int(bundle.goods.bins.sum()) == in_bins
        assert waste.counters()["absent_waste_collection_stopped"] == 1.0
    else:
        assert waste.waste_g_collected > 0 and int(bundle.goods.bins.sum()) == 0
        assert waste.counters()["absent_waste_collection_stopped"] == 0.0
    assert bundle.goods.sku_balanced()


# ================================================================= 街路の清掃(#104)
@pytest.mark.parametrize("mode", ["stopped", "legacy"])
def test_street_cleaning_leaves_litter_when_stopped(mode):
    """ポイ捨ての旧道(rate_rules legacy)でごみを生じさせ、掃除の巡回の腕だけを変える。"""
    world, agents, _ = goods_setup(n_agents=40, n_cells=9)
    clean = StreetCleaningProcess(world, agents, tick_seconds=STEP_S, rate_rules="legacy", absent_processes=mode)
    for k in _span(5 * SECONDS_PER_HOUR, 7 * SECONDS_PER_HOUR):  # 05〜07 時(掃除の窓)
        clean.step(k)
    assert clean.litter_generated_g > 0
    if mode == "stopped":  # 道の清掃は無い=街路にごみが残る(正しい不合格)
        assert clean.swept_g == 0.0 and clean.n_swept_cells == 0
        assert float(clean.litter_g.sum()) == pytest.approx(clean.litter_generated_g)
        assert clean.counters()["absent_street_cleaning_stopped"] == 1.0
    else:
        assert clean.swept_g > 0 and clean.n_swept_cells > 0
        assert clean.counters()["absent_street_cleaning_stopped"] == 0.0


# ================================================================= 道路工事(#106)
def _road_assets() -> ProcessAssets:
    return ProcessAssets(
        source="test",
        edge_cell=np.arange(20, dtype=np.int32) % 16,
        edge_klass_code=np.zeros(20, dtype=np.int16),
        edge_length_m=np.full(20, 50.0),
        edge_klass_names=("residential",),
    )


@pytest.mark.parametrize("mode", ["stopped", "legacy"])
def test_road_works(mode):
    world = make_world(16)
    alog = _log()
    rw = RoadWorksProcess(world, _road_assets(), master_seed=1, n_works=4, tick_seconds=STEP_S, actual_log=alog,
                          absent_processes=mode)
    assert rw.active and rw.planned_edges.size == 4  # 辺の抽選は腕に依らない(ほかの流れを動かさない)
    lo, _hi = ROADWORK_WINDOW  # [分]
    rw.step(_k(lo * SECONDS_PER_MINUTE))
    if mode == "stopped":
        assert rw.occupied_edges.size == 0 and int(rw.blocked_cells.sum()) == 0 and rw.n_started == 0
        assert len(alog) == 0 and rw.counters()["absent_road_works_stopped"] == 1.0
    else:
        assert rw.occupied_edges.size == 4 and int(rw.blocked_cells.sum()) > 0 and len(alog) == 4
        assert rw.counters()["absent_road_works_stopped"] == 0.0


def test_road_works_plan_is_the_same_in_both_arms():
    world = make_world(16)
    a = RoadWorksProcess(world, _road_assets(), master_seed=5, n_works=4, absent_processes="stopped")
    b = RoadWorksProcess(world, _road_assets(), master_seed=5, n_works=4, absent_processes="legacy")
    assert np.array_equal(a.planned_edges, b.planned_edges)


# ================================================================= 救急と警察の出動(#110)
@pytest.mark.parametrize("mode", ["stopped", "legacy"])
def test_dispatch(mode):
    world = make_world(9)
    alog = _log()
    d = PublicServiceDispatchProcess(world, master_seed=1, tick_seconds=STEP_S, actual_log=alog, absent_processes=mode)
    at = _k(10 * SECONDS_PER_MINUTE)
    arrive = d.request(at, 2, (5.0, 6.0))
    if mode == "stopped":  # 出動は無い=倒れた人は運ばれない(正しい不合格)
        assert arrive == -1 and not d.pending and d.n_dispatched == 0 and len(alog) == 0
        assert d.arrivals(_k(SECONDS_PER_DAY)) == []
        assert d.counters()["absent_dispatch_stopped"] == 1.0
    else:
        assert arrive > at and d.n_dispatched == 1 and len(alog) == 1
        assert len(d.arrivals(arrive)) == 1
        assert d.counters()["absent_dispatch_stopped"] == 0.0


def test_collapse_still_happens_but_nobody_is_dispatched_when_stopped():
    """倒れる事象そのもの(rate_rules の collapse)はこの腕に依らない。止めた腕では出動も到着(警察の顕著行為)も無い。"""
    world = make_world(9)
    agents, _ = make_agents(world, 50)
    out = {}
    for mode in ("stopped", "legacy"):
        d = PublicServiceDispatchProcess(world, master_seed=1, tick_seconds=STEP_S, absent_processes=mode)
        s = SalientProcess(world, agents, dispatch=d, tick_seconds=STEP_S, rate_rules="legacy",
                           rate_per_10k_per_day=20_000.0)
        for k in _span(0, 200 * SECONDS_PER_MINUTE):
            s._collapse_events(k)
        arrived = sum(len(s._dispatch_events(k)) for k in _span(200 * SECONDS_PER_MINUTE, 400 * SECONDS_PER_MINUTE))
        out[mode] = (s.n_collapse, d.n_dispatched, arrived)
    assert out["stopped"][0] == out["legacy"][0] > 0  # 倒れた数は同じ(乱数の流れは counter)
    assert out["stopped"][1:] == (0, 0)
    assert out["legacy"][1] == out["legacy"][0] and out["legacy"][2] > 0


# ================================================================= 電気と水(#43)
@pytest.mark.parametrize("mode", ["stopped", "legacy"])
def test_infra(mode):
    world = make_world(9)
    agents, _ = make_agents(world, 30)
    infra = InfraLoadProcess(world, agents, tick_seconds=STEP_S, absent_processes=mode)
    for k in _span(0, 3 * SECONDS_PER_HOUR):
        infra.step(k)
    c = infra.counters()
    if mode == "stopped":
        assert c["power_kwh_day"] == 0.0 and c["water_m3_day"] == 0.0 and c["absent_infra_stopped"] == 1.0
    else:
        assert c["power_kwh_day"] > 0 and c["water_m3_day"] > 0 and c["absent_infra_stopped"] == 0.0


@pytest.mark.parametrize("mode", ["stopped", "legacy"])
def test_infra_peak_hour_is_minus_one_when_stopped(mode):
    """〔検収 低-5〕止めた腕の山の時は −1(全部 0 の argmax=0 時に見せない)。旧道は 0〜23。"""
    world = make_world(9)
    agents, _ = make_agents(world, 30)
    infra = InfraLoadProcess(world, agents, tick_seconds=STEP_S, absent_processes=mode)
    for k in _span(8 * SECONDS_PER_HOUR, 10 * SECONDS_PER_HOUR):
        infra.step(k)
    peak = infra.counters()["peak_hour"]
    if mode == "stopped":
        assert peak == -1.0 and "止めた" in infra.summary()
    else:
        assert 0 <= peak < 24


# ================================================================= 実行器の受け渡しとランの全体
@pytest.mark.parametrize("mode", ["stopped", "legacy", None])
def test_runner_hands_the_arm_to_the_five_processes(mode, arm_restore):
    AP.set_arm("stopped")
    world = make_world(9)
    agents, _ = make_agents(world, 10)
    rn = WorldProcessRunner(world=world, agents=agents, absent_processes=mode)
    want = AP.MODE_STOPPED if mode is None else mode
    assert rn.absent_processes == want
    for key in ("waste", "street_cleaning", "road_works", "dispatch", "infra"):
        assert getattr(rn, key).absent_processes == want, key
    assert [v["runner_key"] for v in AP.STOPPED_PROCESSES.values()] == [
        "waste", "street_cleaning", "road_works", "dispatch", "infra"]


@pytest.fixture(scope="module")
def tiny_runs():
    from shibuya.engine.run import run_day

    prev = AP.arm()
    out = {}
    try:
        for mode in ("stopped", "legacy"):
            AP.set_arm(mode)
            out[mode] = run_day(n_agents=30, seed=2, n_cells=9, tick_seconds=STEP_S, ticks=_k(2 * SECONDS_PER_HOUR))
    finally:
        AP.set_arm(prev)
    return out


def test_run_manifest_section(tiny_runs):
    m = tiny_runs["stopped"].run_manifest_fields()
    ap = m["absent_processes"]
    assert list(m)[-2:] == ["rate_rules", "absent_processes"]
    assert ap["schema"] == AP.SCHEMA and ap["mode"] == "stopped" and set(ap["processes"]) == set(AP.PROCESSES)
    assert all(v == 1 for v in ap["stopped"].values())
    assert {k: v for k, v in ap["counts"].items() if v not in (0, None)} == {}
    leg = tiny_runs["legacy"].run_manifest_fields()["absent_processes"]
    assert leg["mode"] == "legacy" and all(v == 0 for v in leg["stopped"].values())
    assert leg["counts"]["infra_power_kwh_day"] > 0  # 旧道は電気と水の負荷を数える


def test_resume_through_run_day_checks_the_arm(tmp_path, arm_restore):
    """〔検収 低-6〕run_day を通す再開: 同じ腕なら通しのランと final が同じ・違う腕なら止める(ValueError)。"""
    from shibuya.engine.run import run_day

    kw = dict(n_agents=300, seed=1, n_cells=16, tick_seconds=STEP_S, ticks=_k(SECONDS_PER_DAY), checkpoint_every=60)
    stop = _k(12 * SECONDS_PER_HOUR)
    AP.set_arm("stopped")
    straight = run_day(**kw)
    a = run_day(state_out=tmp_path / "state", stop_at_tick=stop, **kw)
    files = a.resume["state_files"]
    assert files and files[-1]["T"] == stop and not files[-1]["finished"]
    parent = tmp_path / "state" / files[-1]["file"]
    b = run_day(resume_from=parent, **kw)
    assert b.final_hash == straight.final_hash and b.resume["finished"]
    AP.set_arm("legacy")
    with pytest.raises(ValueError, match="「無い」の過程の腕が親と違う"):
        run_day(resume_from=parent, **kw)


def test_cli_rejects_a_wrong_arm_name():
    from shibuya import cli

    with pytest.raises(SystemExit):
        cli.main(["--absent-processes", "off"])
