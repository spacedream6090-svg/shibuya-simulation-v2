"""10d(D-102 Q3・Q5・指示書 10-03 §3-6 A10・§3-7 A11): 日境界の再開と複数日の通しラン。

既知の答え(アジェンダ §4-1・指示の (i)〜(vii)):

- (i)・(ii) ``resume == straight``: 通しのランと「止める → 状態を書く → 再開」が、再開の時刻から後の**全 checkpoint**
  (final=今の ``combined``・behavior-hash・full-hash)・tick ごとの呼数・日の締めの後の 2 つのハッシュと日次
  センサスの行・テープの呼ごとの prompt_hash で一致する。止める時刻は日の境目と、日中の 3 点
  (7:00=420・12:30=750・22:00=1320)と、2 日目の日中。
- (iii) プロセスの中のキャッシュを持ち越さない再開(別のプロセス・numba のキャッシュの置き場も空)でも一致する。
- (iv) 日次の締めは 1 日 1 回(=日数)・金と物の保存則が日ごとに閉じる・体の数が保存される・同じ便を 2 度
  流さない。
- (v) 2 日目の頭でお金が湧かない(財布と参入資本の入れ直しが 2 日目以降に走らない・再開でも走らない)。
- (vi) ``finished: true`` への再開・設定の違う再開・止める時刻の誤りを止める。
- (vii) counter の乱数(``--rng-scheme counter``)でも再開で二重に引かれない。
- 艦隊の「出したが返っていない呼」を保存し、再開で同じ call_id で出し直す(偽 vLLM)。

**保存の範囲(親の答え 1)**: 状態台帳(10d 版)の範囲=full-hash の範囲だけを保存する。10d の試験で見つけた保存し
忘れ 14 項目は台帳の行を直して吸収した(O37・O85・O88 の軸 2・O90〜O93 の新しい行)。
**テープの前提(親の答え 3)**: テープの共有ブロックの印(O85・O88)は full-hash に入るので、比べる 2 本は「両方とも
テープを書く」か「両方とも書かない」でそろえる(下の試験は通しも止めたランも再開のランもテープを書く)。
**再開の初期化(親の答え 2)**: 再開では日の頭の初期化を呼ばず、起動時に SoA から作る表だけを戻した SoA から作り直す
(``rebuild_derived``)。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import numpy as np
import pytest

from shibuya import cli
from shibuya.engine import resume as RS
from shibuya.engine import state_ledger as SL
from shibuya.engine.run import run_day
from shibuya.engine.tape import Tape

from tests.engine.test_sim_time_T import ALL_ARMS

WORLD_DIR = Path("data/world/v2")
real_data = pytest.mark.skipif(not (WORLD_DIR / "w17_schedule.parquet").exists(), reason="実世界資産が無い")
TPD = 1_440
#: 日中の 3 点(7:00・12:30・22:00)・日の境目・2 日目の日中(7:00)。
STOPS = (420, 750, 1320, 1440, 1860)
#: 世界資産の小さいラン(既定の腕=語彙 v3・活動層・CLI の既定のエネルギーの空腹)。
WORLD_KW = dict(n_agents=300, seed=1, world_dir=str(WORLD_DIR), sim_days=2, vocab_version="v3", activity=True)
SYN_KW = dict(n_agents=100, seed=1, n_cells=16, ticks=TPD, sim_days=2, budget=100.0, **ALL_ARMS)


# ---------------------------------------------------------------- 比べ方
def _hashes(res, from_T: int) -> list[tuple[int, str, str, str]]:
    return [(c.tick, c.combined, c.behavior_hash, c.full_hash) for c in res.checkpoints if c.tick >= from_T]


def _diag(res, from_T: int) -> dict[int, tuple[int, ...]]:
    """診断の行の全列(tick → 行)。10d 検収 T1: 累計の列は無い(差分の基準も戻す)ので全列を比べる。"""
    return {int(r[0]): tuple(int(x) for x in r) for r in res.diagnostics.tolist() if int(r[0]) >= from_T}


def _calls(res, from_T: int) -> dict[int, int]:
    t = res.column("tick").astype(np.int64)
    c = res.column("calls").astype(np.int64)
    return {int(a): int(b) for a, b in zip(t.tolist(), c.tolist()) if int(a) >= from_T}


def _tape(path: Path, from_T: int) -> list[tuple[int, int, int, str]]:
    return sorted((int(r.tick), int(r.agent_id), int(r.wake_class), str(r.prompt_hash))
                  for r in Tape(path).rows() if int(r.tick) >= from_T and not r.is_deferred)


def _days(res, from_T: int) -> list[tuple]:
    return [(r["day"], r.get("state_hashes_end_of_day", {}).get("full_hash"),
             r.get("state_hashes_end_of_day", {}).get("behavior_hash"),
             json.dumps(r.get("census_row", {}), sort_keys=True), r.get("census_pass"), json.dumps(r["bodies"]))
            for r in res.daily if int(r["end_T"]) > from_T]


def _split(run, kw: dict, stop: int, tmp: Path, **extra_kw):
    a = run(state_out=tmp / "state", stop_at_tick=stop, tape_path=tmp / "tape_a", **kw, **extra_kw)
    files = a.resume["state_files"]
    assert files and files[-1]["T"] == stop and not files[-1]["finished"]
    b = run(resume_from=tmp / "state" / files[-1]["file"], tape_path=tmp / "tape_b", **kw, **extra_kw)
    return a, b


def _assert_resume_equals_straight(straight, s_tape: Path, a, b, tmp: Path, stop: int) -> None:
    got, want = _hashes(b, stop), _hashes(straight, stop)
    assert want and [g[0] for g in got] == [w[0] for w in want]
    bad = [(g[0], g[1] == w[1], g[2] == w[2], g[3] == w[3]) for g, w in zip(got, want) if g != w]
    assert not bad, f"止めた T={stop}: 最初の食い違い {bad[:3]}"
    assert _calls(b, stop) == _calls(straight, stop)
    assert _diag(b, stop) == _diag(straight, stop)
    assert a.llm_calls + b.llm_calls == straight.llm_calls
    assert _days(b, stop) == _days(straight, stop)
    assert _tape(tmp / "tape_a", stop) == []
    assert _tape(tmp / "tape_b", stop) == _tape(s_tape, stop)
    assert b.resume["parent_run"]["run_id"] == a.resume["run_id"]
    assert b.resume["parent_run"]["resume_T"] == stop and b.resume["finished"]
    assert not a.resume["finished"]


# ================================================================= (i)(ii) 合成世界・全腕・毎 tick
@pytest.fixture(scope="module")
def syn_straight(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("syn_straight")
    res = run_day(checkpoint_every=1, tape_path=tmp / "tape", **SYN_KW)
    return res, tmp / "tape"


@pytest.mark.parametrize("stop", STOPS)
def test_synthetic_all_arms_resume_equals_straight_at_every_tick(syn_straight, tmp_path, stop):
    straight, s_tape = syn_straight
    a, b = _split(run_day, dict(SYN_KW, checkpoint_every=1), stop, tmp_path)
    _assert_resume_equals_straight(straight, s_tape, a, b, tmp_path, stop)
    assert len(_hashes(b, stop)) == 2 * TPD - stop  # 残りの tick の全点


# ================================================================= (i)(ii) 世界資産・毎 tick
@pytest.fixture(scope="module")
def world_straight(tmp_path_factory):
    tmp = tmp_path_factory.mktemp("world_straight")
    res = cli.run(checkpoint_every=1, tape_path=tmp / "tape", **WORLD_KW)
    return res, tmp / "tape"


@real_data
@pytest.mark.parametrize("stop", STOPS)
def test_world_resume_equals_straight_at_every_tick(world_straight, tmp_path, stop):
    straight, s_tape = world_straight
    a, b = _split(cli.run, dict(WORLD_KW, checkpoint_every=1), stop, tmp_path)
    _assert_resume_equals_straight(straight, s_tape, a, b, tmp_path, stop)
    assert len(_hashes(b, stop)) == 2 * TPD - stop


@real_data
@pytest.mark.parametrize("arms,stop", [
    (dict(memory="on", relations="on", store_memory="on", familiarity="on", rel_copresent="on"), 750),
    (dict(memory="on", relations="on", policy="classical", chooser="classical"), 1320),
    (dict(memory="on", relations="on", policy="classical", chooser="classical"), 1860),
    (dict(plan_executor=False, report_precondition=False, vocab_version="v1", activity=False), 750),
    (dict(geometry="edge", vocab_version="v2", activity=False), 1320),
    (dict(exit_mode="walk_to_platform"), 1080),
], ids=["v3_all_arms", "classical_mem_rel", "classical_day2", "null_arm", "v2_edge", "walk_exit"])
def test_world_arms_resume_equals_straight(tmp_path, arms, stop):
    kw = dict(WORLD_KW, checkpoint_every=10, **arms)
    straight = cli.run(tape_path=tmp_path / "tape_s", **kw)
    a, b = _split(cli.run, kw, stop, tmp_path)
    _assert_resume_equals_straight(straight, tmp_path / "tape_s", a, b, tmp_path, stop)


# ================================================================= 親の答え 1: 台帳を直した後は一致する
@real_data
def test_day_boundary_resume_keeps_the_census_after_the_ledger_fix(tmp_path):
    """10d で直した行(O92 の金の台帳の ``_snap``・生ログの位置)が無いと、日の境目で再開した日のセンサスが落ちた。"""
    kw = dict(WORLD_KW, checkpoint_every=60)
    straight = cli.run(tape_path=tmp_path / "tape_s", **kw)
    a, b = _split(cli.run, kw, TPD, tmp_path)
    _assert_resume_equals_straight(straight, tmp_path / "tape_s", a, b, tmp_path, TPD)
    assert b.daily[-1]["census_pass"] is True and b.daily[-1]["census_row"] == straight.daily[-1]["census_row"]


@real_data
def test_memory_mid_day_resume_keeps_calls_after_the_ledger_fix(tmp_path):
    """10d で直した行(O91 の ``conv.n_opened``=記憶の層が読む)が無いと、日中の再開で呼数が食い違った。"""
    kw = dict(WORLD_KW, checkpoint_every=60, memory="on", relations="on")
    straight = cli.run(tape_path=tmp_path / "tape_s", **kw)
    a, b = _split(cli.run, kw, 750, tmp_path)
    _assert_resume_equals_straight(straight, tmp_path / "tape_s", a, b, tmp_path, 750)


def test_ledger_rows_moved_by_10d():
    """親の答え 1: 14 項目を台帳の行に吸収した(軸の判定)。"""
    full = {p for _k, p in SL.full_items()}
    beh = {p for _k, p in SL.behavior_items()}
    moved = {"presence._pulled_in_today", "ledger.money._snap", "ledger.money._flow_daily", "ledger.money._raw_pos",
             "ledger.money._raw_head", "ledger.money._day_marks", "ledger.money.n_raw_dropped",
             "ledger.money.n_transfers", "ledger.goods._dl_pos", "ledger.goods._dl_head", "ledger.goods._dl_marks",
             "ledger.goods.n_delivery_dropped", "conv.n_opened", "classical._ipf_cache"}
    assert moved <= full
    assert {"conv.n_opened", "classical._ipf_cache", "poi_resolver.named_closed"} <= beh
    assert "presence._pulled_in_today" not in beh and SL.row("O37").behavior == SL.DIAG  # 検収 L5
    assert "poi_resolver.named_closed" in full and SL.row("O94").restore == SL.REQUIRED  # 検収 L2
    assert {"bridge._interned", "fleet_bridge._interned"} <= full and not ({"bridge._interned"} & beh)
    assert SL.row("O85").restore == SL.REQUIRED and SL.row("O88").restore == SL.REQUIRED
    for k in ("O90", "O91", "O92", "O93"):
        assert SL.row(k).restore == SL.REQUIRED
    # リングの中身(K16)は含めない
    assert "ledger.money._raw_amt" not in full and "ledger.goods._dl_qty" not in full


# ================================================================= (iii) キャッシュを持ち越さない再開
_CHILD = r"""
import json, sys
from shibuya import cli
from shibuya.engine import resume as RS
kw = json.loads(sys.argv[1])
res = cli.run(resume_from=sys.argv[2], tape_path=sys.argv[3], **kw)
print(json.dumps([[c.tick, c.combined, c.behavior_hash, c.full_hash] for c in res.checkpoints]))
"""


@real_data
def test_resume_in_a_fresh_process_with_empty_caches(world_straight, tmp_path):
    straight, _ = world_straight
    kw = dict(WORLD_KW, checkpoint_every=1)
    # テープは通しのランと同じく書く(テープの共有ブロックの印 O85 が full-hash に入るため)
    a = cli.run(state_out=tmp_path / "state", stop_at_tick=750, tape_path=tmp_path / "tape_a", **kw)
    env = dict(os.environ, PYTHONIOENCODING="utf-8", NUMBA_CACHE_DIR=str(tmp_path / "numba_empty"))
    state = str(tmp_path / "state" / a.resume["state_files"][-1]["file"])
    r = subprocess.run([sys.executable, "-c", _CHILD, json.dumps(kw), state, str(tmp_path / "tape_b")],
                       capture_output=True, text=True, encoding="utf-8", env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    got = [tuple(x) for x in json.loads(r.stdout.strip().splitlines()[-1])]
    assert got == _hashes(straight, 750)


# ================================================================= (iv) 日次の締め・保存則・体の数
def test_daily_close_runs_once_per_day(monkeypatch):
    from shibuya.engine.processes.runner import WorldProcessRunner

    seen: list[tuple[int, bool]] = []
    orig = WorldProcessRunner.end_of_day

    def spy(self, tick, *, flush_rail=True):
        seen.append((int(tick), bool(flush_rail)))
        return orig(self, tick, flush_rail=flush_rail)

    monkeypatch.setattr(WorldProcessRunner, "end_of_day", spy)
    res = run_day(n_agents=60, seed=2, n_cells=9, ticks=TPD, sim_days=3, checkpoint_every=360)
    assert seen == [(TPD - 1, False), (2 * TPD - 1, False), (3 * TPD - 1, True)]
    assert [r["day"] for r in res.daily] == [0, 1, 2] and res.resume["daily_closes"] == 3
    assert [r["end_T"] for r in res.daily] == [TPD, 2 * TPD, 3 * TPD]
    assert [h["day"] for h in res.day_heads] == [1, 2]


@real_data
def test_two_day_world_run_closes_money_goods_and_bodies_each_day(monkeypatch):
    from shibuya.engine.ledger_api import LedgerBundle

    closes: list[int] = []
    orig = LedgerBundle.end_of_day

    def spy(self, day):
        closes.append(int(day))
        return orig(self, day)

    monkeypatch.setattr(LedgerBundle, "end_of_day", spy)
    from shibuya.engine.presence import PlanExecutor

    arrive_ticks: list[int] = []
    orig_step = PlanExecutor.step

    def step_spy(self, tick):
        n0 = int(self.n_arrivals)
        orig_step(self, tick)
        if int(self.n_arrivals) > n0:
            arrive_ticks.append(int(tick))

    monkeypatch.setattr(PlanExecutor, "step", step_spy)
    res = cli.run(checkpoint_every=360, **WORLD_KW)
    assert closes == [0, 1] and len(res.daily) == 2
    for r in res.daily:
        row = r["census_row"]
        assert r["census_pass"] is True, row
        assert row["flow_ok"] and row["ex_nihilo_ok"] and row["residual_ok"] and row["goods_balanced"], row
        b = r["bodies"]
        assert b["in_area"] + b["riding"] + b["outside"] == b["n"] == WORLD_KW["n_agents"] and b["other"] == 0
    rail = res.runner.rail
    lo1, hi1 = rail.day_range(1)
    assert rail.day_range(0) == (0, lo1) and hi1 == rail.dep_tick.size and hi1 - lo1 == lo1  # 平日 2 日=同じ本数
    assert int(rail.dep_tick[lo1]) >= TPD and bool(np.all(np.diff(rail.dep_tick) >= 0))
    assert rail.n_departures == rail.dep_tick.size  # 便は 1 本 1 回だけ発車する(日の締めで 2 度流さない)
    assert res.resume["w17_weekday_substituted_days"] == [1]  # K9: 火曜は月曜の行
    # 2 日目にも計画実行層の出入り(張り直したイベント)と鉄道の到着がある
    st = res.column("tick")
    assert int(res.column("calls")[st >= TPD].sum()) > 0
    assert any(t >= TPD for t in arrive_ticks) and any(t < TPD for t in arrive_ticks)  # 2 日目にも到着がある


# ================================================================= (v) 2 日目の頭でお金が湧かない
@real_data
def test_no_money_is_added_at_the_head_of_day_two_or_on_resume(monkeypatch, tmp_path):
    from shibuya.economy.ledger import Ledger
    from shibuya.engine import resolve as R

    counts = {"households": 0, "stores": 0, "initialize": 0}
    oh, os_, oi = Ledger.endow_households, Ledger.endow_stores, R.initialize

    def eh(self, *a, **k):
        counts["households"] += 1
        return oh(self, *a, **k)

    def es(self, *a, **k):
        counts["stores"] += 1
        return os_(self, *a, **k)

    def ini(*a, **k):
        counts["initialize"] += 1
        return oi(*a, **k)

    monkeypatch.setattr(Ledger, "endow_households", eh)
    monkeypatch.setattr(Ledger, "endow_stores", es)
    monkeypatch.setattr(R, "initialize", ini)
    kw = dict(WORLD_KW, checkpoint_every=360)
    res = cli.run(**kw)
    assert counts == {"households": 1, "stores": 1, "initialize": 1}  # 0 日目の頭の 1 回だけ
    assert res.day_heads[0]["money"] == res.daily[0]["money"]         # 1 日目の終わり=2 日目の頭
    for k in counts:
        counts[k] = 0
    a = cli.run(state_out=tmp_path / "s", stop_at_tick=TPD, **kw)
    counts.update({"households": 0, "stores": 0, "initialize": 0})
    b = cli.run(resume_from=tmp_path / "s" / a.resume["state_files"][-1]["file"], **kw)
    # 再開: 日の頭の初期化(財布・参入資本・initialize)を呼ばない(親の答え 2)
    assert counts == {"households": 0, "stores": 0, "initialize": 0}
    assert b.money_start == a.daily[-1]["money"]["households"]
    assert b.daily[-1]["money"] == res.daily[-1]["money"]


# ================================================================= (vi) 誤用の拒否
def test_resume_refuses_finished_mismatched_and_wrong_stops(tmp_path):
    kw = dict(n_agents=30, seed=1, n_cells=9, ticks=TPD, checkpoint_every=360)
    done = run_day(state_out=tmp_path / "fin", sim_days=2, **kw)
    last = done.resume["state_files"][-1]
    assert last["finished"] and last["T"] == 2 * TPD and done.run_manifest_fields()["finished"] is True
    with pytest.raises(ValueError, match="finished"):
        run_day(resume_from=tmp_path / "fin" / last["file"], sim_days=2, **kw)
    mid = run_day(state_out=tmp_path / "mid", stop_at_tick=600, sim_days=2, **kw)
    path = tmp_path / "mid" / mid.resume["state_files"][-1]["file"]
    assert mid.run_manifest_fields()["finished"] is False
    with pytest.raises(ValueError, match="設定が親と違う"):
        run_day(resume_from=path, sim_days=2, **dict(kw, seed=2))
    day2 = run_day(state_out=tmp_path / "d2", stop_at_tick=2000, sim_days=2, **kw)
    with pytest.raises(ValueError, match="範囲"):
        run_day(resume_from=tmp_path / "d2" / day2.resume["state_files"][-1]["file"], sim_days=1, **kw)
    with pytest.raises(ValueError, match="state_out"):
        run_day(stop_at_tick=600, sim_days=2, **kw)
    with pytest.raises(ValueError, match="stop_at_tick"):
        run_day(state_out=tmp_path / "x", stop_at_tick=2 * TPD, sim_days=2, **kw)
    with pytest.raises(ValueError, match="再生"):
        run_day(state_out=tmp_path / "x", mode="replay", replay=None, **kw)
    # 台帳の版が違う状態のファイルは読まない
    b0 = RS.read_state(path)
    b0.header["ledger_version"] = "state-ledger/old"
    bad = tmp_path / "bad" / "bad.pkl"
    RS.write_state(bad, b0)
    with pytest.raises(ValueError, match="状態台帳の版"):
        run_day(resume_from=bad, sim_days=2, **kw)
    # 再開は親の ID と再開の時刻を持つ
    child = run_day(resume_from=path, sim_days=2, **kw)
    m = child.run_manifest_fields()
    assert m["parent_run"]["run_id"] == mid.resume["run_id"] and m["parent_run"]["resume_T"] == 600
    assert m["finished"] is True and m["resume"]["start_T"] == 600


@real_data
def test_resume_refuses_a_ledger_that_was_already_endowed(tmp_path, monkeypatch):
    kw = dict(WORLD_KW, checkpoint_every=360)
    a = cli.run(state_out=tmp_path / "s", stop_at_tick=TPD, **kw)
    orig = cli.build_ledger_bundle

    def endowed(*args, **k):  # 再開でも参入資本を入れた台帳を渡してしまう呼び手
        k["endow"] = True
        return orig(*args, **k)

    monkeypatch.setattr(cli, "build_ledger_bundle", endowed)
    with pytest.raises(ValueError, match="自動補充"):
        cli.run(resume_from=tmp_path / "s" / a.resume["state_files"][-1]["file"], **kw)


# ================================================================= (vii) counter の乱数
def test_counter_rng_resume_draws_once(tmp_path):
    kw = dict(n_agents=200, seed=1, n_cells=25, ticks=TPD, sim_days=2, checkpoint_every=10,
              rng_scheme="counter", salient_rate_per_10k=3000.0)
    straight = run_day(tape_path=tmp_path / "s", **kw)
    a, b = _split(run_day, kw, 1000, tmp_path)
    _assert_resume_equals_straight(straight, tmp_path / "s", a, b, tmp_path, 1000)
    n_s = straight.runner.salient.n_events
    assert n_s > 0 and a.runner.salient.n_events + b.runner.salient.n_events == n_s
    assert a.dispatches + b.dispatches == straight.dispatches > 0


# ================================================================= 艦隊の未着の呼
def test_fleet_inflight_calls_are_reissued_with_the_same_call_id(tmp_path):
    from tests.engine.test_fleet_wiring import make_client
    from tests.llm.test_fleet import FakeVLLM

    def run(**k):
        servers = [FakeVLLM(), FakeVLLM()]
        try:
            return run_day(n_agents=200, seed=1, n_cells=24, ticks=24, fleet=make_client(servers), fleet_wait_s=10.0,
                           renderer="stub", processes=False, population=False, world_dir=None,
                           sleep_suppression=False, checkpoint_every=1, **k)
        finally:
            for s in servers:
                s.close()

    straight = run(tape_path=tmp_path / "s")
    a, b = _split(run, {}, 12, tmp_path)
    head = json.loads((tmp_path / "state" / a.resume["state_files"][-1]["file"]).with_suffix(".json").read_text(
        encoding="utf-8"))
    assert head["counts"]["inflight_calls"] > 0  # T=11 に発射した呼が返る前に止めた
    assert [c[:4] for c in _hashes(b, 12)] == [c[:4] for c in _hashes(straight, 12)]
    assert _tape(tmp_path / "tape_b", 0) == _tape(tmp_path / "s", 11)  # 出し直した呼は T=11 の call_id のまま
    assert a.llm_calls + b.llm_calls == straight.llm_calls


# ================================================================= 書き出しの形
def test_state_file_is_one_atomic_bundle(tmp_path):
    kw = dict(n_agents=40, seed=1, n_cells=9, ticks=TPD, sim_days=2, checkpoint_every=360)
    res = run_day(state_out=tmp_path, stop_at_tick=700, **kw)
    f = res.resume["state_files"][-1]
    p = tmp_path / f["file"]
    assert p.exists() and p.with_suffix(".json").exists() and not list(tmp_path.glob("*.tmp"))
    bundle = RS.read_state(p)
    h = bundle.header
    assert h["format"] == RS.STATE_FORMAT and h["ledger_version"] == SL.LEDGER_VERSION
    assert h["progress"]["next_T"] == 700 and h["progress"]["closed_at_day_end"] is False
    assert set(bundle.items) == {p_ for _k, p_ in SL.full_items()}
    assert set(bundle.soa) == {"agents", "cells", "pois", "perception"}  # 合成世界でも知覚 SoA(顕著行為の持ち物)がある
    assert all(c not in SL.full_excluded("agents") for c in bundle.soa["agents"])
    assert f["bytes"] == p.stat().st_size and h["hashes"]["full_hash"] == f["full_hash"]


# ================================================================= 親の答え 7: 自分が書いたものだけを読む
def test_read_state_opens_only_files_it_wrote(tmp_path):
    kw = dict(n_agents=30, seed=1, n_cells=9, ticks=TPD, sim_days=2, checkpoint_every=360)
    res = run_day(state_out=tmp_path / "s", stop_at_tick=600, **kw)
    path = tmp_path / "s" / res.resume["state_files"][-1]["file"]
    data = path.read_bytes()
    head = data[: data.index(b"\n")].split(b" ")
    assert head[0] == RS.MAGIC and head[2].decode() == res.resume["run_id"]
    RS.read_state(path)                                  # そのままなら読める
    broken = tmp_path / "x" / path.name
    broken.parent.mkdir()
    broken.write_bytes(data[:-1] + bytes([data[-1] ^ 1]))  # 中身を 1 バイト変える
    (broken.parent / path.with_suffix(".json").name).write_bytes(path.with_suffix(".json").read_bytes())
    with pytest.raises(ValueError, match="sha256"):
        RS.read_state(broken)
    plain = tmp_path / "y" / path.name                   # 先頭の行の無い pickle は開かない
    plain.parent.mkdir()
    plain.write_bytes(data[data.index(b"\n") + 1:])
    with pytest.raises(ValueError, match="印"):
        RS.read_state(plain)
    nosidecar = tmp_path / "z" / path.name               # 見出しの写しが無いものは読まない
    nosidecar.parent.mkdir()
    nosidecar.write_bytes(data)
    with pytest.raises(ValueError, match="写し"):
        RS.read_state(nosidecar)
    side = json.loads(path.with_suffix(".json").read_text(encoding="utf-8"))
    side["run_id"] = "run-other"
    (nosidecar.parent / path.with_suffix(".json").name).write_text(json.dumps(side), encoding="utf-8")
    with pytest.raises(ValueError, match="ラン ID"):
        RS.read_state(nosidecar)


def test_cli_switches_for_sim_days_and_resume(tmp_path):
    """親の答え 7: ``--sim-days``・``--resume-from``(と書き出し先 ``--state-out``)を engine.run と cli で同じ綴りで。"""
    import argparse

    from shibuya.engine.run import add_calendar_args, calendar_kwargs_from_args

    ap = argparse.ArgumentParser()
    add_calendar_args(ap)
    assert "sim_days" not in calendar_kwargs_from_args(ap.parse_args([]))  # 既定は今の引数のまま
    got = calendar_kwargs_from_args(ap.parse_args(["--sim-days", "2", "--state-out", str(tmp_path / "s")]))
    assert got["sim_days"] == 2 and got["state_out"] == str(tmp_path / "s")
    kw = dict(n_agents=30, seed=1, n_cells=9, ticks=TPD, checkpoint_every=360)
    first = run_day(stop_at_tick=TPD, **{**kw, **got})
    f = tmp_path / "s" / first.resume["state_files"][-1]["file"]
    got2 = calendar_kwargs_from_args(ap.parse_args(["--sim-days", "2", "--resume-from", str(f)]))
    assert got2["resume_from"] == str(f)
    child = run_day(**{**kw, **got2})
    m = child.run_manifest_fields()
    assert m["sim_days"] == 2 and m["resumed_at_T"] == TPD and m["parent_run"]["run_id"] == first.resume["run_id"]
    assert run_day(**kw).run_manifest_fields()["resumed_at_T"] is None


@real_data
def test_daily_tables_are_relaid_from_the_calendar_day(tmp_path):
    """親の答え 5: 2 日目の頭で W7 の曜日の行と世界過程の日ごとの乱数の表を暦の口の日で引き直す。"""
    from shibuya.core.rng import stream

    res = cli.run(checkpoint_every=360, **WORLD_KW)
    rn = res.runner
    cal_key1 = 1  # day_index モード(既定 0)の 1 日目の日の鍵=0+1
    assert rn.opening.day_index == 1                     # 火曜の行(table_weekday(1))
    from shibuya.engine.processes.goods_flow import DELIVERY_WINDOW

    plan = stream(1, "world.delivery_inbound", cal_key1).integers(*DELIVERY_WINDOW, size=res.world.n_poi)
    assert np.array_equal(rn.delivery_inbound.plan_minute, plan) and rn.delivery_inbound.day_index == cal_key1
    one = cli.run(checkpoint_every=360, **dict(WORLD_KW, sim_days=1))
    assert not np.array_equal(one.runner.road_works.planned_edges, rn.road_works.planned_edges) or         rn.road_works.planned_edges.size == 0
    assert int(rn.last_mile.delivered.sum()) > 0          # 2 日目も配る(配達済みを日の頭で 0 に戻す)
    assert int(res.parcels) == int(one.parcels)            # 2 日目の終わりの配達済み=1 日の分


def test_ipf_cache_key_has_the_day(monkeypatch):
    """親の答え 4: classical の c_t の覚え書きの鍵に日がある(2 日目は 2 日目の状態から作る)。"""
    from shibuya.engine import classical as CL

    orig_bind = CL.ClassicalPolicy.bind
    seen: list = []

    def bind(self, *a, **k):
        orig_bind(self, *a, **k)
        self.m_next = np.full_like(self.m_next, 1.5)   # 乗数を 1 でなくする(覚え書きを使う)
        self._identity = False
        seen.append(self)

    monkeypatch.setattr(CL.ClassicalPolicy, "bind", bind)
    run_day(n_agents=60, seed=1, n_cells=16, ticks=TPD, sim_days=2, checkpoint_every=720, vocab_version="v3",
            policy="classical", chooser="classical", budget=60.0)
    keys = set(seen[0]._ipf_cache)
    assert {d for d, _s in keys} == {0, 1}


# ================================================================= 10d 検収の直し
@real_data
def test_b3_weather_and_the_environment_read_the_same_day_on_day_two(tmp_path):
    """検収 D1・T2: 2 日目の 12 時の B3 の天候の語と、環境の過程の暑さの段が、同じ再生の実日の W13 の行から来る。"""
    import pyarrow.parquet as pq

    from shibuya.perception import templates as T
    from shibuya.perception.renderer import PerceptionAssets

    res = cli.run(checkpoint_every=360, tape_path=tmp_path / "tape", **WORLD_KW)
    env = res.runner.environment
    rd = env.replay_date
    assert rd
    pa = PerceptionAssets.load_or_synthetic(WORLD_DIR, res.world)
    w, dl, heat = pa.weather_by_date_hour[(rd, 12)]
    want = T.TEMPLATES["B3.weather"].format(weather=w, daylight=dl)
    calls = pq.read_table(tmp_path / "tape" / "calls.parquet").to_pylist()
    blocks = {r["block_id"]: r["text"] for r in pq.read_table(tmp_path / "tape" / "blocks.parquet").to_pylist()}
    texts = {blocks.get(b, "") for c in calls if TPD + 720 <= int(c["tick"]) < TPD + 780 for b in c["block_ids"]}
    b3 = [t for t in texts if "[B3" in t]
    assert b3 and all(want in t for t in b3), (want, b3[:2])
    # 環境の過程の行も同じ実日(暑さの段はその行の 12 時)
    row = env.assets.day_index_of(rd)
    assert row == env._row and row >= 0
    assert int(env.assets.hourly_heat_stage[row, 12]) >= 0


def test_resume_rebuilds_the_staff_table_shared_with_restocking(tmp_path):
    """検収 L4・T3: 再開の後の開閉の担当従業者の表(補充の過程と同じ配列)が通しと同じ。

    合成世界で回す(W16 の母集団には種別「従業者」が居ないので、世界資産のランでは表が全部 −1 になる)。
    ``_rebuild_derived`` を外すと、再開では種別が初期化されていない SoA から作るので表が全部 −1 になって落ちる。
    """
    kw = dict(n_agents=80, seed=1, n_cells=16, ticks=TPD, sim_days=2, checkpoint_every=360)
    straight = run_day(**kw)
    a, b = _split(run_day, kw, 750, tmp_path)
    so, sb = straight.runner.opening, b.runner.opening
    assert np.array_equal(so.staff_of_poi, sb.staff_of_poi) and int((sb.staff_of_poi >= 0).sum()) > 0
    assert b.runner.shelf.staff_of_poi is sb.staff_of_poi


def test_named_closed_memo_survives_a_resume(tmp_path, monkeypatch):
    """検収 L2・T4(再確認 N2 で直した): 名指しの即時閉店の控えを入れてから止めて戻すと、控えが戻り、再開の後の
    B6 に控えの 1 句(店名・閉店中)が出て、その呼の prompt_hash が通しと同じ。

    T=599(止める tick の直前)の頭で、直前の結果が「閉店」の体ぜんぶに、その結果の tick を持つ控えを入れる(=描画が
    1 句を出す条件 ``last_result_tick == 控えの tick`` を満たす)。通しと止めたランは控えを入れ、再開のランは入れない
    (保存から戻る)。
    """
    from shibuya.agents.state import ResultCode
    from shibuya.engine import poi_target as PT
    from shibuya.engine import resolve as R
    from shibuya.perception import renderer as RD

    resolvers: list = []
    orig_init = PT.TargetResolver.__init__
    orig_ab = R.advance_body

    def init(self, *a, **k):
        orig_init(self, *a, **k)
        resolvers.append(self)

    def advance_body(agents, tick, *a, **k):
        if int(tick) == 599 and resolvers:
            r = agents.registry
            closed = np.flatnonzero(np.asarray(r.last_result) == int(ResultCode.CLOSED))
            for x in closed.tolist():
                resolvers[-1].named_closed[int(x)] = (0, int(r.last_result_tick[x]))
        return orig_ab(agents, tick, *a, **k)

    notes: list = []
    orig_note = RD.Renderer._named_closed_text

    def note_spy(self, i):  # 読むだけ(返す値はそのまま)
        out = orig_note(self, i)
        if out:
            notes.append((int(self._tickc.tick), int(i), out))
        return out

    monkeypatch.setattr(PT.TargetResolver, "__init__", init)
    monkeypatch.setattr(R, "advance_body", advance_body)
    monkeypatch.setattr(RD.Renderer, "_named_closed_text", note_spy)
    kw = dict(n_agents=200, seed=1, n_cells=9, ticks=TPD, sim_days=2, checkpoint_every=1, vocab_version="v3",
              budget=200.0)
    straight = run_day(tape_path=tmp_path / "s", **kw)
    s_notes = [x for x in notes if x[0] >= 600]
    a = run_day(state_out=tmp_path / "st", stop_at_tick=600, tape_path=tmp_path / "ta", **kw)
    notes.clear()
    memo = RS.read_state(tmp_path / "st" / a.resume["state_files"][-1]["file"]).items["poi_resolver.named_closed"]
    assert len(memo) > 0
    monkeypatch.setattr(R, "advance_body", orig_ab)  # 再開は控えを入れない=保存から戻る
    b = run_day(resume_from=tmp_path / "st" / a.resume["state_files"][-1]["file"], tape_path=tmp_path / "tb", **kw)
    assert resolvers[-1].named_closed == memo                     # 戻した控え(再開のランの解決器)
    assert _hashes(b, 600) == _hashes(straight, 600)
    assert _tape(tmp_path / "tb", 600) == _tape(tmp_path / "s", 600)
    # 再開の直後の描画で控えの 1 句(店名・閉店中)が実際に出て、通しの同じ tick・同じ体と同じ文(呼の prompt_hash は
    # 上のテープの比べで同じ)。合成世界は W7 が無いので開店の分は出ない形
    b_notes = [x for x in notes if x[0] >= 600]
    assert b_notes and b_notes == s_notes
    assert all("閉店中" in x[2] for x in b_notes)
    hit = {(t, i) for t, i, _ in b_notes}
    rows_b = [r for r in _tape(tmp_path / "tb", 600) if (r[0], r[1]) in hit]
    assert rows_b and rows_b == [r for r in _tape(tmp_path / "s", 600) if (r[0], r[1]) in hit]


def test_fleet_inflight_calls_at_the_day_boundary(tmp_path, monkeypatch):
    """検収 T5: 日の境目(T=1440)で艦隊の未着の呼がある形の再開(夜の街の分)。

    合成の日課は 23 時台に起床が無いので、体 0〜4 に 23:59 の計画境界を足して、日の最後の tick に呼を出す。
    """
    from shibuya.agents import schedule as SCH
    from tests.engine.test_fleet_wiring import make_client
    from tests.llm.test_fleet import FakeVLLM

    orig = SCH.MockWeeklySchedule.events_of_day

    def events(self, *a, **k):
        ag, sl, tk = orig(self, *a, **k)
        ag = np.concatenate([ag, np.arange(5, dtype=ag.dtype)])
        sl = np.concatenate([sl, np.zeros(5, dtype=sl.dtype)])
        tk = np.concatenate([tk, np.full(5, TPD - 1, dtype=tk.dtype)])
        o = np.lexsort((sl, ag, tk))
        return ag[o], sl[o], tk[o]

    monkeypatch.setattr(SCH.MockWeeklySchedule, "events_of_day", events)

    def run(**k):
        servers = [FakeVLLM(), FakeVLLM()]
        try:
            return run_day(n_agents=30, seed=1, n_cells=9, ticks=TPD, sim_days=2, fleet=make_client(servers),
                           fleet_wait_s=10.0, renderer="stub", processes=False, population=False, world_dir=None,
                           sleep_suppression=False, checkpoint_every=30, budget=3.0, **k)
        finally:
            for s in servers:
                s.close()

    straight = run(tape_path=tmp_path / "s")
    a, b = _split(run, {}, TPD, tmp_path)
    head = json.loads((tmp_path / "state" / a.resume["state_files"][-1]["file"]).with_suffix(".json").read_text(
        encoding="utf-8"))
    assert head["counts"]["inflight_calls"] > 0 and head["progress"]["closed_at_day_end"] is True
    assert _hashes(b, TPD) == _hashes(straight, TPD)
    assert _tape(tmp_path / "tape_b", 0) == _tape(tmp_path / "s", TPD - 1)
    assert a.llm_calls + b.llm_calls == straight.llm_calls


def test_fingerprint_and_header_have_no_paths_and_run_ids_are_unique(tmp_path):
    """検収 L3・L6: 指紋はパスの文字列でなく中身で同定する・見出しに絶対パスが入らない・ラン ID は実行ごとに違う。"""
    import os

    kw = dict(n_agents=30, seed=1, n_cells=9, ticks=TPD, sim_days=2, checkpoint_every=360)
    rel = run_day(state_out=tmp_path / "a", stop_at_tick=600, holiday_csv="data/calendar/syukujitsu.csv", **kw)
    ab = run_day(state_out=tmp_path / "b", stop_at_tick=600,
                 holiday_csv=os.path.abspath("data/calendar/syukujitsu.csv"), **kw)
    ha = RS.read_state(tmp_path / "a" / rel.resume["state_files"][-1]["file"]).header
    hb = RS.read_state(tmp_path / "b" / ab.resume["state_files"][-1]["file"]).header
    assert ha["fingerprint"] == hb["fingerprint"]                       # 書き方が違っても同じ中身=同じ指紋
    assert str(ha["fingerprint"]["holiday_csv"]).startswith(("sha256:", "missing"))
    assert ha["run_id"] != hb["run_id"]                                  # 実行ごとに一意
    side = (tmp_path / "b" / ab.resume["state_files"][-1]["file"]).with_suffix(".json").read_text(encoding="utf-8")
    assert os.path.abspath(".") not in side and os.path.expanduser("~") not in side
    # 相対で書いた状態を絶対パスの設定で再開できる(指紋が同じ)
    child = run_day(resume_from=tmp_path / "a" / rel.resume["state_files"][-1]["file"],
                    holiday_csv=os.path.abspath("data/calendar/syukujitsu.csv"), **kw)
    pr = child.run_manifest_fields()["parent_run"]
    assert (pr["run_id"], pr["resume_T"], pr["state_full_hash"]) == (rel.resume["run_id"], 600, ha["hashes"]["full_hash"])


def test_b3_weather_follows_the_replay_date_of_each_day():
    """再確認 N1: 再生の実日が日ごとに変わるとき、2 日目の B3 の天候は 2 日目の実日の W13 の行(描画の単体)。

    既定の世界は再生の実日が毎日同じ(影のある 1 日に絞る)なので、ここでは描画に 2 日分の違う行を持たせ、
    ``weather_date_fn`` が日ごとに別の実日を返す形で ``Renderer._b3`` を直接呼ぶ。B3 のキャッシュの鍵から日を外すと、
    2 日目も 0 日目の行を使い回して落ちる。
    """
    import dataclasses
    from datetime import datetime

    from shibuya.agents.state import AgentState
    from shibuya.perception import normalize as N
    from shibuya.perception import renderer as RD
    from shibuya.perception import templates as T
    from shibuya.world.state import World

    w = World.synthetic(n_cells=4, seed=1)
    a = AgentState(2)
    assets = dataclasses.replace(
        RD.PerceptionAssets.synthetic(w),
        weather_by_date_hour={("2026-07-28", 12): ("曇", T.DAYLIGHT_WORDS[1], T.HEAT_STAGE_WORDS[1]),
                              ("2026-07-29", 12): ("雨", T.DAYLIGHT_WORDS[1], T.HEAT_STAGE_WORDS[0])},
    )
    r = RD.Renderer(w, a, assets)
    day = {"d": "2026-07-28"}
    r.weather_date_fn = lambda: day["d"]

    def b3(when: datetime) -> str:
        return r._b3(RD._TickCache(when=when, band5=N.time_band(when))).decode("utf-8")

    first = b3(datetime(2026, 8, 3, 12, 0))     # 暦の日付は実日と別(日付の語は暦・天候は実日)
    day["d"] = "2026-07-29"
    second = b3(datetime(2026, 8, 4, 12, 0))    # 同じ 5 分帯・別の実日
    assert T.TEMPLATES["B3.weather"].format(weather="曇", daylight=T.DAYLIGHT_WORDS[1]) in first
    assert T.TEMPLATES["B3.weather"].format(weather="雨", daylight=T.DAYLIGHT_WORDS[1]) in second
    assert T.TEMPLATES["B3.heat"].format(heat=T.HEAT_STAGE_WORDS[0]) in second
    # 口が無ければ暦の日付で引く(合成世界・既定の旧経路)
    r.weather_date_fn = None
    assert "雨" not in b3(datetime(2026, 8, 4, 12, 0)) or ("2026-08-04", 12) in assets.weather_by_date_hour
