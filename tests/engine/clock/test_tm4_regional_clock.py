"""第 6 期 6-3 時計の段 T4: 場所ごとの時計(``engine.regional_clock``・腕 ``--clock regional``)の試験。

- 区域の作り方(セルの重心の 500 m の格子・世界資産 520 セル → 29 区域+舞台の外)・区域ごとの窓の処理の順・区域をまたぐ
  事象は境目で届ける(聞く人の区域またぎの遅れ=窓の終わり − 発言の時刻・処理し終えた区域への予約は窓の終わりへ)。
- 境目の移動(全体で 1 つの時計との遅れ 0)・遅刻の計器(計画実行層の日の表から)・待ち合わせは欄だけ(null)。
- 一致: 腕 regional は既定 global と final・呼数・checkpoint が同じ(合成の世界・世界資産)・2 日と再開=通し・会話の時計を
  載せても世界は同じで会話の計器も区域またぎの遅れのほかは同じ・段 B の宣言の外の書き 0。
- TM9 の欄 ``clock_kind``(manifest と日次の記録)=regional・混合は口だけ(止める)・CLI・TM4 の道具の遅刻の列。
"""

from __future__ import annotations

import contextlib
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest

from shibuya import cli
from shibuya.core.time_consts import CLOCK_KIND, NS_PER_SECOND, STEP_SECONDS, STEPS_PER_DAY
from shibuya.engine import manifest_sections as MS
from shibuya.engine import regional_clock as RC
from shibuya.engine import resume as RS
from shibuya.engine import speech_clock as TC
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CO
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS
from shibuya.world.state import World

ROOT = Path(__file__).resolve().parents[3]
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
TPD = STEPS_PER_DAY
SEC = NS_PER_SECOND
SYN = dict(n_agents=60, seed=1, n_cells=9, ticks=360, budget=60.0, checkpoint_every=60, vocab_version="v3",
           memory="on", relations="on", rel_copresent="on", store_memory="on", renderer="stub")


@contextlib.contextmanager
def arms(clock: str = "global", talk: str = "table"):
    pc, pt = RC.arm(), TC.arm()
    RC.set_arm(clock)
    TC.set_arm(talk)
    try:
        yield
    finally:
        RC.set_arm(pc)
        TC.set_arm(pt)


def _agents(cells: list[int]):
    return SimpleNamespace(registry=SimpleNamespace(cell=np.asarray(cells, dtype=np.int64)))


# ================================================================= 区域
def test_regions_from_cell_centroids():
    w = World.synthetic(n_cells=36, seed=1)
    roc, how = RC.region_of_cells(w)
    assert how == "cell_centroid" and roc.shape == (36,) and roc.min() == 0
    c = np.asarray(w.assets.cell_centroid, dtype=np.float64)
    ix = np.floor((c - c.min(axis=0)) / RC.REGION_SIZE_M).astype(np.int64)
    same = (ix[:, None, :] == ix[None, :, :]).all(axis=2)
    assert np.array_equal(same, roc[:, None] == roc[None, :])  # 同じ格子=同じ区域
    noxy = SimpleNamespace(n_cells=60, assets=None)
    roc2, how2 = RC.region_of_cells(noxy)
    assert how2 == "cell_index" and roc2.tolist() == [c // RC.REGION_CELLS_FALLBACK for c in range(60)]


@real_data
def test_world_assets_have_29_regions():
    w = World.load_or_synthetic(Path("data/world/v2"), n_cells=139, seed=1)
    roc, how = RC.region_of_cells(w)
    assert how == "cell_centroid" and w.n_cells == 520 and int(roc.max()) + 1 == 29


# ================================================================= 区域ごとの窓
def _clock(cells: list[int], region_of_cell: list[int], width_s: int = STEP_SECONDS) -> RC.RegionalClock:
    return RC.RegionalClock(region_of_cell=np.asarray(region_of_cell), agents=_agents(cells), width_s=width_s,
                            start_ns=0)


def test_region_events_run_per_region_in_time_order():
    # 体 0,1 は区域 0・体 2 は区域 1・体 3 は舞台の外
    rc = _clock([0, 0, 1, -1], [0, 1])
    seen: list[tuple[int, list[int]]] = []
    rc.register(1, "talk", lambda t, a, s: seen.append((int(t), a.tolist())))
    rc.schedule([5 * SEC, 2 * SEC, 1 * SEC, 3 * SEC], [0, 1, 2, 3], 1)
    rc.schedule(2 * SEC, 0, 1)
    rc.run_windows(0, 60 * SEC)
    # 区域の番号の順(0 → 1 → 外=2)・区域の中は時刻 → 体の順・同じ時刻の続きは 1 つの束
    assert seen == [(2 * SEC, [0, 1]), (5 * SEC, [0]), (1 * SEC, [2]), (3 * SEC, [3])]
    m = rc.observed()
    assert (m["events"], m["dispatches"], m["region_windows"], m["windows"], m["pending_at_end"]) == (5, 4, 3, 1, 0)
    assert rc._rc_head.tolist() == [60 * SEC] * 3


def test_hearing_across_regions_is_delivered_at_the_window_end():
    rc = _clock([0, 1, 0], [0, 1], width_s=10)
    assert rc.hear_delay_ns(13 * SEC, 0, 2) == 0  # 同じ区域
    assert rc.hear_delay_ns(13 * SEC, 0, 1) == 7 * SEC  # 窓 [10, 20) の終わり − 13 秒
    m = rc.observed()
    assert (m["hear"], m["hear_cross"], m["hear_delay_ns_max"], m["message_delay_ns_max"]) == (2, 1, 7 * SEC, 7 * SEC)


def test_an_event_for_a_region_already_run_in_the_window_goes_to_the_boundary():
    rc = _clock([0, 1], [0, 1])
    got: list[tuple[int, int]] = []

    def fn(t, a, s):  # 区域 1 の事象の処理の中で、処理し終えた区域 0 の体に同じ窓の時刻で予約する
        got.append((int(t), int(a[0])))
        if int(a[0]) == 1:
            rc.schedule(int(t) + SEC, 0, 1)

    rc.register(1, "x", fn)
    rc.schedule(2 * SEC, 0, 1)
    rc.schedule(4 * SEC, 1, 1)
    rc.run_windows(0, 60 * SEC)
    assert got == [(2 * SEC, 0), (4 * SEC, 1)]  # 区域 0 の新しい事象はこの窓では処理しない
    m = rc.observed()
    assert (m["cross_events"], m["cross_delay_ns_max"], m["pending_at_end"]) == (1, 55 * SEC, 1)
    rc.run_windows(60 * SEC, 120 * SEC)
    assert got[-1] == (60 * SEC, 0)  # 窓の終わり(境目)で届いた


def test_past_schedule_is_refused():
    rc = _clock([0], [0])
    rc.register(1, "x", lambda t, a, s: None)
    rc.run_windows(0, 60 * SEC)
    with pytest.raises(ValueError, match="過去への予約"):
        rc.schedule(10 * SEC, 0, 1)


def test_boundary_moves_are_counted_with_zero_delay():
    ag = _agents([0, 0, 1])
    rc = RC.RegionalClock(region_of_cell=np.asarray([0, 1]), agents=ag, width_s=STEP_SECONDS, start_ns=0)
    rc.run_windows(0, 60 * SEC)
    ag.registry.cell[:] = [1, 0, 1]
    rc.run_windows(60 * SEC, 120 * SEC)
    ag.registry.cell[:] = [1, -1, 1]  # 舞台の外へ=外の区域
    rc.run_windows(120 * SEC, 180 * SEC)
    m = rc.observed()
    assert (m["cross_moves"], m["cross_move_delay_ns_max"], m["boundaries"]) == (2, 0, 3)


def test_lateness_from_the_plan_tables():
    rc = _clock([0], [0])
    presence = SimpleNamespace(arrival_tick=np.array([5, 5, 7, 9, 2000]), blocks=SimpleNamespace(
        start=np.array([5, 3, 6, 9, 10])))
    rc.run_windows(5 * STEP_SECONDS * SEC, 6 * STEP_SECONDS * SEC, presence=presence, tpd=TPD)
    rc.run_windows(6 * STEP_SECONDS * SEC, 8 * STEP_SECONDS * SEC, presence=presence, tpd=TPD)
    m = rc.observed()
    # 刻み 5: 予定 2(遅い 1=2 分)・刻み 7: 予定 1(遅い 1=1 分)・刻み 9 は窓の外・2000 は日の外
    assert (m["planned_arrivals"], m["late_arrivals"], m["late_minutes_sum"], m["late_minutes_max"]) == (3, 2, 3, 2)
    assert m["meeting"] is None


def test_mixed_is_a_port_only():
    from shibuya.engine.systems import build as BLD

    with arms(clock="mixed"):
        with pytest.raises(NotImplementedError, match="口だけ") as exc:
            run_day(n_agents=10, seed=1, n_cells=9, ticks=5, renderer="stub")
    # 〔検収 L7〕止めるのは組み立て(build)の段
    assert any(Path(str(e.path)).name == Path(BLD.__file__).name for e in exc.traceback)
    with pytest.raises(ValueError):
        RC.set_arm("lp")


# ================================================================= 一致(全体で 1 つの時計と同じ)
def _hashes(res):  # noqa: ANN001
    return (res.final_hash, int(res.llm_calls), [(c.tick, c.behavior_hash, c.full_hash) for c in res.checkpoints])


def test_regional_run_matches_global_on_the_synthetic_world():
    base = run_day(**SYN)
    with arms(clock="regional"):
        arm = run_day(**SYN)
    assert _hashes(arm) == _hashes(base)
    mb, ma = base.run_manifest_fields(), arm.run_manifest_fields()
    assert "clock" not in mb and mb["clock_kind"] == CLOCK_KIND == "steps"
    assert ma["clock_kind"] == RC.CLOCK_KIND_REGIONAL and all(d["clock_kind"] == "regional" for d in ma["daily"])
    c = ma["clock"]
    assert tuple(c) == RC.CONFIG_KEYS + RC.OBSERVED_KEYS
    assert c["windows"] == SYN["ticks"] and c["boundaries"] == SYN["ticks"] and c["meeting"] is None
    for k in RC.CONFIG_KEYS:
        assert MS.section_of(f"clock.{k}") == MS.CONFIG, k
    for k in RC.OBSERVED_KEYS:
        assert MS.section_of(f"clock.{k}") == MS.OBSERVED, k


def test_two_days_and_resume_with_regional_match_the_straight_global(tmp_path):
    kw = dict(n_agents=40, seed=1, n_cells=9, ticks=TPD, checkpoint_every=360, renderer="stub")
    straight = run_day(sim_days=2, **kw)
    with arms(clock="regional"):
        straight_r = run_day(sim_days=2, **kw)
        day = run_day(state_out=tmp_path / "d", stop_at_tick=TPD, sim_days=2, **kw)
        mid = run_day(state_out=tmp_path / "m", stop_at_tick=TPD + 371, sim_days=2, **kw)
        r_day = run_day(resume_from=tmp_path / "d" / day.resume["state_files"][-1]["file"], sim_days=2, **kw)
        r_mid = run_day(resume_from=tmp_path / "m" / mid.resume["state_files"][-1]["file"], sim_days=2, **kw)
    assert straight_r.final_hash == straight.final_hash
    assert r_day.final_hash == r_mid.final_hash == straight.final_hash
    hd = RS.read_state(tmp_path / "d" / day.resume["state_files"][-1]["file"]).header["fingerprint"]
    assert hd[RC.FP_KEY] == "regional"
    assert r_mid.run_manifest_fields()["clock"]["windows"] == 2 * TPD - (TPD + 371)


@pytest.mark.parametrize("clock", ["global", "regional"])
def test_stage_b_declared_writes_with_utterances(clock):
    """〔検収 M1・L4〕段 B を会話の発言のある構成(合成の世界・語彙 v1・150 体・600 刻み)で腕 mora(全体の時計と区域ごとの時計)
    に回す=発言の予約が書く行 BW・T4W も系 decide・llm_receive の宣言の中(宣言の外 0)。"""
    pr = PR.Probe(check=CO.declared_check(SPECS), ticks=None)
    PR.ACTIVE = pr
    try:
        with arms(clock=clock, talk="mora"):
            res = cli.run(n_agents=150, seed=1, world_dir=None, n_cells=9, ticks=600, vocab_version="v1")
    finally:
        PR.ACTIVE = None
    t = res.run_manifest_fields()["talk_clock"]
    assert t["utterances"] > 0  # 空振りでない
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]
    key = "T4W:" if clock == "regional" else "BW:batching._bw_sched"
    writers = {s for _t, s, _d, keys in pr.entries if any(k.startswith(key) for k in keys)}
    assert {"decide"} & writers or {"llm_receive"} & writers, writers  # 会話の番の予約は系の宣言で書く


def test_negative_control_stage_b_catches_the_missing_declaration(monkeypatch):
    """負の対照: decide の宣言から行 BW を外すと、発言のある構成の段 B が宣言の外の書きを捕まえる。"""
    import dataclasses as dc

    from shibuya.engine.systems import spec as SPM

    sp = SPECS["decide"]
    paths = frozenset(x for x in sp.writes.paths if not x.startswith("BW:"))
    bad = dict(SPECS)
    bad["decide"] = dc.replace(sp, writes=dc.replace(sp.writes, paths=paths))
    pr = PR.Probe(check=CO.declared_check(bad), ticks=None)
    PR.ACTIVE = pr
    try:
        with arms(clock="global", talk="mora"):
            cli.run(n_agents=150, seed=1, world_dir=None, n_cells=9, ticks=600, vocab_version="v1")
    finally:
        PR.ACTIVE = None
    assert any(v[1] == "decide" and "BW:" in str(v) for v in pr.violations), pr.violations[:5]
    assert SPM is not None


def test_window_mark_passes_the_new_rows():
    check = CO.declared_check(SPECS)
    for key in ("BW:batching._bw_head", "TCC:talk_clock._tc_meter", "T4W:clock._rc_head"):
        assert check(CO.WINDOW_MARK, key), key
    assert not check(CO.WINDOW_MARK, "T3M:step_scope._ss_copy") and not check(CO.WINDOW_MARK, "agents.cell")


@real_data
def test_regional_with_talk_clock_matches_global_on_world_assets():
    kw = dict(n_agents=1000, seed=1, world_dir="data/world/v2", vocab_version="v1", memory="on", relations="on")
    with arms(clock="global", talk="mora"):
        g = cli.run(**kw)
    with arms(clock="regional", talk="mora"):
        r = cli.run(**kw)
    assert _hashes(r) == _hashes(g)
    tg, tr = g.run_manifest_fields()["talk_clock"], r.run_manifest_fields()["talk_clock"]
    # 違うのは区域またぎの聞こえと束の分け方だけ(区域ごとの時計は束を区域ごとに分ける=束の数が増え最大の束が小さい)
    skip = {"cross_heard", "hear_delay_ns_sum", "hear_delay_ns_max", "dispatches", "batch_max"}
    assert {k: v for k, v in tr.items() if k not in skip} == {k: v for k, v in tg.items() if k not in skip}
    assert tr["dispatches"] >= tg["dispatches"] and tr["batch_max"] <= tg["batch_max"]
    assert tr["batch_sum"] == tg["batch_sum"] == tg["utterances"]
    assert tg["cross_heard"] == 0
    c = r.run_manifest_fields()["clock"]
    assert c["events"] == tr["utterances"] and c["hear"] == tr["heard"] and c["hear_cross"] == tr["cross_heard"]
    assert c["n_regions"] == 30 and c["cross_moves"] > 0 and c["planned_arrivals"] > 0


# ================================================================= CLI・TM4 の道具
_ARGS = ["--agents", "20", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "30"]
_CODE = "import sys; from shibuya import cli; sys.exit(cli.main(sys.argv[1:]))"


def test_cli_clock_regional(tmp_path):
    out = tmp_path / "c.json"
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop(RC.ENV, None)
    r = subprocess.run([sys.executable, "-c", _CODE, *_ARGS, "--checkpoints-out", str(out), "--clock", "regional"],
                       capture_output=True, text=True, encoding="utf-8", env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    man = json.loads(out.read_text(encoding="utf-8"))["manifest"]
    assert man["clock"]["arm"] == "regional" and man["clock_kind"] == "regional"


def test_gauge_lateness_reads_the_clock_section():
    spec = importlib.util.spec_from_file_location("bwg_tm4", ROOT / "tools" / "instruments" / "batch_width_gauge.py")
    G = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(G)
    assert G.DEFAULT_METRICS["lateness"] == "clock.late_arrivals" and G.DEFAULT_METRICS["meeting"] == "clock.meeting"
    recs = []
    for w in (60, 10):
        for s in range(1, 7):
            recs.append({"width_s": w, "salt": s, "final": f"f{s}", "calls": 100.0 + s, "actions": 50.0 + s,
                         "message_delay_max_s": 0.0, "clock": {"late_arrivals": 3 + s, "meeting": None}})
    tab = G.table(recs)
    row = next(r for r in tab["rows"] if r["width_s"] == 10)
    assert row["metrics"]["lateness"]["diff"] == 0.0 and row["metrics"]["lateness"]["within"] is True
    assert row["metrics"]["meeting"]["diff"] is None


def test_m2_regional_clock_refuses_writes_from_outside():
    """〔検収 M2〕負の対照: 外から欄を書く・消す・配列と表の中身を書くと止まる。"""
    rc = _clock([0, 1], [0, 1])
    rc.register(1, "x", lambda t, a, s: None)
    rc.schedule(2 * SEC, 0, 1)
    rc.run_windows(0, 60 * SEC)
    for name, value in (("_rc_head", None), ("_rc_events", {}), ("_rc_meter", {}), ("_rc_seq", 0),
                        ("_rc_snap", None), ("region_of_cell", np.zeros(2)), ("y", 1)):
        with pytest.raises(AttributeError):
            setattr(rc, name, value)
    with pytest.raises(AttributeError):
        del rc._rc_head
    with pytest.raises(ValueError):
        rc._rc_head[:] = 5
    with pytest.raises(ValueError):
        rc.region_of_cell[0] = 1
    with pytest.raises(ValueError):
        rc._rc_snap[0] = 1
    with pytest.raises(TypeError):
        rc._rc_meter["windows"] = 0
    with pytest.raises(TypeError):
        rc._rc_events[0] = ()
    with pytest.raises(TypeError):
        rc._rc_kinds[2] = ("y", None)
    with pytest.raises(RuntimeError, match="最初の窓で閉じた"):
        rc.register(2, "y", lambda t, a, s: None)
    assert rc._rc_meter["windows"] == 1 and rc._rc_head.tolist() == [60 * SEC] * 3


def test_m2_the_region_handler_runs_with_the_clock_closed():
    """区域の事象の処理の関数(外のコード)を呼ぶ間は時計の欄を書けない(予約の口は書ける=自分で開く)。"""
    rc = _clock([0], [0])
    seen = []

    def fn(t, a, s):
        with pytest.raises(AttributeError):
            object.__getattribute__(rc, "__setattr__")("_rc_seq", 99)
        seen.append(int(rc.schedule(int(t) + SEC, 0, 1)[0]))

    rc.register(1, "x", fn)
    rc.schedule(2 * SEC, 0, 1)
    rc.run_windows(0, 4 * SEC)
    assert seen and rc._rc_seq == seen[-1] + 1
