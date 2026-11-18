"""〔11-02r §1 #7〕「無い」と宣言した過程 5 件を止める切替口 ``engine.absent_processes`` の試験(過程ごとの正と負の対照)。

各過程について、既定(腕 stopped)では世界を変えない(件数 0)・切替口(腕 legacy)では前の版と同じに動くことを、過程を直に
組んで確かめる。止めない判断(世帯の消費・倒れる事象そのもの・ポイ捨ての腕)はこの腕に依らないことも見る。ランの全体
(manifest の節・実行器の受け渡し・CLI の口)は小さな合成世界の run_day で確かめる。記録 ``docs/bench/analysis/s2e-1102/README.md``。
〔第347 止めた切替口の削除〕ランの切替口(``--absent-processes``・環境変数 ``SHIBUYA_ABSENT_PROCESSES``)は消した=旧道は過程の
部品の口(引数 ``absent_processes``)だけ・ランの旧道は試験の中だけの助け(``tests/engine/_legacy_world.py``)。記録
``docs/bench/analysis/switch-removal-347/README.md``。
正しい不合格(11-02r #7「街路にごみが残る・倒れた人が運ばれない」)は過程の試験で数で見る。

時間の方針(11-02r §2-2): 本試験は刻みの番号を決め打ちしない。時刻は世界の時刻(秒)で書き、過程に渡す刻みの番号は刻みの幅
``STEP_S`` から :func:`_k` で都度求める(過程も同じ幅で組む)。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.foundation.time_consts import SECONDS_PER_DAY, SECONDS_PER_HOUR, SECONDS_PER_MINUTE
from shibuya.world.laws import switch_absent as AP
from shibuya.engine import resolve as R
from shibuya.world.laws.civic import InfraLoadProcess, PublicServiceDispatchProcess
from shibuya.world.laws.goods_flow import (
    COLLECT_WINDOW,
    HOUSEHOLD_CONSUME_MINUTE,
    StreetCleaningProcess,
    WasteCollectionProcess,
)
from shibuya.world.laws.logistics import ROADWORK_WINDOW, RoadWorksProcess
from shibuya.world.laws.runner import WorldProcessRunner
from shibuya.world.laws.salient import SalientProcess
from shibuya.world.model.assets import ProcessAssets
from shibuya.world.ledger.actual_log import ActualLog

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


# ================================================================= 切替口(〔第347〕消した)と部品の口
def test_the_run_arm_is_stopped_and_the_switch_is_removed():
    """〔第347 止めた切替口の削除〕前(``test_the_default_arm_is_stopped_and_names_are_checked``)は「既定 stopped・
    ``resolve(None)`` は今の腕・腕の名の誤り(``set_arm("off")``)で止まる」。切替口を消した: 腕を選ぶ名(``arm``・``set_arm``・
    ``_ARM``)が無い・``resolve(None)`` は既定 stopped・消した環境変数と旗の名とタグは止める一覧にある(止まることは
    ``tests/engine/test_removed_switches_346.py``)。部品の口の名の検査・印・宣言との 1 対 1 は残す。"""
    from shibuya.foundation.arms import removed as RSW

    for name in ("arm", "set_arm", "_ARM"):
        assert not hasattr(AP, name), name
        assert name not in AP.__all__, name
    assert AP.DEFAULT_MODE == AP.MODE_STOPPED and AP.MODES == ("stopped", "legacy")
    assert AP.resolve(None) == AP.DEFAULT_MODE and AP.is_legacy() is False and AP.is_legacy("legacy") is True
    assert AP.ENV_REMOVED == "SHIBUYA_ABSENT_PROCESSES" and AP.ENV_REMOVED in RSW.REMOVED_ENV
    assert RSW.REMOVED_CLI_FLAGS["--absent-processes"] == AP.ENV_REMOVED
    assert RSW.tag_of(AP.ENV_REMOVED) == RSW.REMOVED_SWITCH_TAG_347 == "stable-v2-before-switch-removal-347"
    for bad in ("off", "bogus"):  # 部品の口の名の検査(前は set_arm("off") で見た名の誤り)
        with pytest.raises(ValueError):
            AP.resolve(bad)
    assert AP.PROCESSES == ("waste_collection", "street_cleaning", "road_works", "dispatch", "infra")
    assert set(AP.STOPPED_PROCESSES) == set(AP.PROCESSES)
    assert AP.stopped_flags("stopped") == {f"absent_{p}_stopped": 1 for p in AP.PROCESSES}
    assert AP.stopped_flags("legacy") == {f"absent_{p}_stopped": 0 for p in AP.PROCESSES}
    # 宣言(world/processes/absent.py)と 1 対 1
    from shibuya.world.ledger import absent as AB

    ab = AB.by_id()
    for name, v in AP.STOPPED_PROCESSES.items():
        a = ab[v["absent"]]
        assert a.kind == "no_actor" and a.engine_stopped and a.world_process_id == v["world_process"], name
        assert v["anchor_kept"] == "・".join(a.keeps_anchor), name


def test_state_header_and_resume_check():
    """〔第347 止めた切替口の削除〕前は切替口の腕を stopped と legacy に置いて再開の検査を見た(legacy の腕なら見出しに無い
    ファイルからも再開できた)。切替口を消した: 今の腕はいつも既定 stopped=見出し stopped は通る・見出しに無い(legacy=版上げの
    前のラン)と legacy は止まる・文に消した切替口と安定版のタグ。"""
    assert AP.header_fields("stopped") == {"mode": "stopped"} and AP.header_fields("legacy") is None
    AP.check_resume({"mode": "stopped"})
    with pytest.raises(ValueError, match="「無い」の過程の腕が親と違う.*--absent-processes legacy.*消した.*"
                                         "stable-v2-before-switch-removal-347"):
        AP.check_resume(None)  # 見出しに無い=版上げの前(legacy)のラン
    with pytest.raises(ValueError, match="「無い」の過程の腕が親と違う"):
        AP.check_resume({"mode": "legacy"})


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
def test_runner_hands_the_arm_to_the_five_processes(mode):
    """実行器が 5 過程に部品の口を渡す(``None``=既定 stopped)。〔第347〕前は切替口の腕を stopped にしてから見た(既定と同じ)。"""
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
    """〔第347 止めた切替口の削除〕legacy は切替口(``--absent-processes`` の腕)の代わりに、試験の中だけで実行器に部品の口
    (「無い」の過程の旧道)を挿して回す(``tests/engine/_legacy_world.py``)。"""
    from shibuya.runtime.run import run_day
    from tests.engine._legacy_world import legacy_world_rules

    kw = dict(n_agents=30, seed=2, n_cells=9, tick_seconds=STEP_S, ticks=_k(2 * SECONDS_PER_HOUR))
    out = {"stopped": run_day(**kw)}
    with pytest.MonkeyPatch.context() as mp:
        legacy_world_rules(mp, rate=False)
        out["legacy"] = run_day(**kw)
    return out


def test_run_manifest_section(tiny_runs):
    m = tiny_runs["stopped"].run_manifest_fields()
    ap = m["absent_processes"]
    assert list(m)[-3:] == ["rate_rules", "absent_processes", "defect_fixes_1103"]  # 〔11-03 §3〕その後ろ(末尾)に defect_fixes_1103
    assert ap["schema"] == AP.SCHEMA and ap["mode"] == "stopped" and set(ap["processes"]) == set(AP.PROCESSES)
    assert all(v == 1 for v in ap["stopped"].values())
    assert {k: v for k, v in ap["counts"].items() if v not in (0, None)} == {}
    leg = tiny_runs["legacy"].run_manifest_fields()["absent_processes"]
    # 〔第347〕旧道は実行器の部品の口で動く(5 過程の印が 0=旧道)。manifest の mode と stopped の印は組み立ての腕(既定 stopped)
    # を書く=試験の中だけの助けの注。件数(counts)は実行器の計数から数える=旧道の件数
    leg_rn = tiny_runs["legacy"].runner
    assert leg_rn.absent_processes == "legacy"
    assert all(getattr(leg_rn, v["runner_key"]).absent_processes == "legacy" for v in AP.STOPPED_PROCESSES.values())
    assert leg["mode"] == "stopped"
    assert leg["counts"]["infra_power_kwh_day"] > 0  # 旧道は電気と水の負荷を数える


def test_resume_through_run_day_checks_the_arm(tmp_path):
    """〔検収 低-6〕run_day を通す再開: 同じ腕なら通しのランと final が同じ・違う腕なら止める(ValueError)。

    〔第347 止めた切替口の削除〕前は切替口の腕を legacy に置いて同じファイルから再開した(違う腕で止まる)。切替口を消した=今の
    腕はいつも stopped。違う腕のファイル=見出しに ``absent_processes`` の無いファイル(版上げの前=legacy のラン)を、保存の
    間だけ見出しを書かない形で作り、そこからの再開が止まることを見る。"""
    from shibuya.runtime.run import run_day
    from shibuya.runtime.state import resume as RS

    kw = dict(n_agents=300, seed=1, n_cells=16, tick_seconds=STEP_S, ticks=_k(SECONDS_PER_DAY), checkpoint_every=60)
    stop = _k(12 * SECONDS_PER_HOUR)
    straight = run_day(**kw)
    a = run_day(state_out=tmp_path / "state", stop_at_tick=stop, **kw)
    files = a.resume["state_files"]
    assert files and files[-1]["T"] == stop and not files[-1]["finished"]
    parent = tmp_path / "state" / files[-1]["file"]
    assert RS.read_state(parent).header["absent_processes"] == {"mode": "stopped"}
    b = run_day(resume_from=parent, **kw)
    assert b.final_hash == straight.final_hash and b.resume["finished"]
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(AP, "header_fields", lambda mode: None)  # 版上げの前の見出し(absent_processes の欄が無い)
        c = run_day(state_out=tmp_path / "old", stop_at_tick=stop, **kw)
    old = tmp_path / "old" / c.resume["state_files"][-1]["file"]
    assert "absent_processes" not in RS.read_state(old).header
    with pytest.raises(ValueError, match="「無い」の過程の腕が親と違う.*消した.*stable-v2-before-switch-removal-347"):
        run_day(resume_from=old, **kw)


def test_cli_flag_is_removed(capsys):
    """〔第347 止めた切替口の削除〕前(``test_cli_rejects_a_wrong_arm_name``)は ``--absent-processes off`` が名の誤りで止まるのを
    見た。旗は消した=値に依らず、表に出さない旗で受けて消した切替口の文で止まる。"""
    from shibuya.interfaces.cli import main as cli

    for value in ("off", "legacy", "stopped"):
        with pytest.raises(SystemExit) as exc:
            cli.main(["--absent-processes", value])
        assert exc.value.code == 2
        assert "--absent-processes は消した切替口" in capsys.readouterr().err
