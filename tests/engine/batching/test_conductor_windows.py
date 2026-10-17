"""第 3 期 3-2(時計の段 T1): 進行役の窓のループ(``engine.systems.conductor.conduct``)の試験。

- 既定(W=60): 窓 1 つに刻みの事象 1 つ・系に渡す時刻(``TickCtx``)=窓の頭・持ち越し 0・manifest の ``batching``。
- 腕(W=30・10・5・1): 系の呼ぶ順(刻み・系の名)・final・呼数・全 checkpoint の 2 本のハッシュが W=60 と同じ
  (T1 の世界の事象の時刻の粒度は 60 秒=どの幅でも同じ)。
- 2 日のラン・日の境目と日の途中で止めて再開=通し(腕 30 秒でも)。幅の違う再開は設定の指紋で止まる。
- 設定の指紋: 既定は今のまま(``batch_width_s`` が無い)・腕のときだけ入る。ランの種類: 腕は ``arm``。
- 試験の差の測り(段 B): 窓の待ち行列と計器(状態台帳の行 ``BW``)の変化は窓の境目 ``WINDOW_MARK`` だけに帰属し、系ごとの
  指紋(行 BW を外した entries)は幅によらず同じ・宣言の外の書きは 0。
- CLI ``--batch-width-s``(環境変数より強い・刻みの幅の約数の外は使い方の誤り)。
- 世界資産(300 体・既定 v3): W=60 と W=10 で final と呼数が同じ。
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys

import pytest

from shibuya import cli
from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS, STEPS_PER_DAY
from shibuya.engine import batching as BA
from shibuya.engine import resume as RS
from shibuya.engine import run_kind as RK
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CD
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS

TPD = STEPS_PER_DAY
#: 合成の世界の構成(記憶・関係・店の記憶=会話と関係の初期化が走る)。
SYN = dict(n_agents=60, seed=1, n_cells=9, ticks=360, budget=60.0, checkpoint_every=60, vocab_version="v3",
           memory="on", relations="on", rel_copresent="on", store_memory="on", renderer="stub")


@contextlib.contextmanager
def width(w: int):
    prev = BA.arm()
    BA.set_arm(w)
    try:
        yield
    finally:
        BA.set_arm(prev)


def _calls(monkeypatch) -> list[tuple[int | None, str, int | None]]:
    """系を呼んだ順(刻み・系の名・系に渡した時刻[ns])を控える(進行役の ``run_system`` を包む)。"""
    seen: list[tuple[int | None, str, int | None]] = []
    real = CD.run_system

    def spy(spec, ctx, box):  # noqa: ANN001, ANN202
        seen.append((None if ctx is None else ctx.T, spec.name, None if ctx is None else ctx.t_ns))
        return real(spec, ctx, box)

    monkeypatch.setattr(CD, "run_system", spy)
    return seen


def _hashes(res) -> tuple:  # noqa: ANN001
    return (res.final_hash, int(res.llm_calls), [(c.tick, c.behavior_hash, c.full_hash) for c in res.checkpoints])


# ================================================================= 既定(W=60)
def test_default_width_is_one_step_per_window_and_ctx_is_the_window_head(monkeypatch):
    seen = _calls(monkeypatch)
    with width(BA.DEFAULT_WIDTH_S):
        res = run_day(**SYN)
    b = res.run_manifest_fields()["batching"]
    n = SYN["ticks"]
    assert (b["width_s"], b["default_width_s"], b["step_s"]) == (STEP_SECONDS, STEP_SECONDS, STEP_SECONDS)
    assert (b["windows"], b["windows_with_events"], b["events"], b["dispatches"]) == (n, n, n, n)
    assert (b["in_window"], b["carried"], b["cap_hits"], b["pending_at_end"], b["max_events_window"]) == (0, 0, 0, 0, 1)
    assert b["cap_events"] == BA.DEFAULT_CAP_EVENTS and b["kinds"] == {
        "step": {"kind": BA.KIND_STEP, "rank": 0, "delivery": BA.IN_WINDOW}}
    steps = [(T, t_ns) for T, _name, t_ns in seen if T is not None]
    assert sorted({T for T, _ in steps}) == list(range(n))
    assert all(t_ns == T * STEP_SECONDS * NS_PER_SECOND for T, t_ns in steps)  # 系の時刻=窓の頭=刻みの時刻


# ================================================================= 腕(W < 60)は同じ
@pytest.mark.parametrize("w", [30, 10, 5, 1])
def test_finer_widths_give_the_same_calls_order_final_and_checkpoints(monkeypatch, w):
    seen60 = _calls(monkeypatch)
    with width(BA.DEFAULT_WIDTH_S):
        r60 = run_day(**SYN)
    order60 = list(seen60)
    seen60.clear()
    with width(w):
        rw = run_day(**SYN)
    assert list(seen60) == order60  # 系の呼ぶ順・刻み・時刻が同じ
    assert _hashes(rw) == _hashes(r60)
    b = rw.run_manifest_fields()["batching"]
    assert b["width_s"] == w and b["windows"] == SYN["ticks"] * (STEP_SECONDS // w)
    assert (b["events"], b["windows_with_events"], b["carried"], b["cap_hits"]) == (SYN["ticks"], SYN["ticks"], 0, 0)


def test_the_system_order_is_the_old_step_loop(monkeypatch):
    """系の並びは前の刻みのループ(``for T in range(t_begin, t_end)``)と同じ: 刻みごとに 日の頭(立つ日)→ 刻みの系の表の順 →
    途中の日の締め(立つ日)・ランの終わりに drain・close_final・report。2 日のランを幅 10 秒で回して組み立て直した並びと比べる。"""
    from shibuya.engine.systems import day as DAY

    seen = _calls(monkeypatch)
    total = 2 * TPD
    with width(10):
        run_day(n_agents=20, seed=1, n_cells=9, ticks=TPD, sim_days=2, checkpoint_every=360, renderer="stub")
    plan = [name for T, name, _t in seen if T == 0]
    assert "day_head" not in plan and "day_close" not in plan and plan[0] == "body"  # 申込書の無いランは系 experiment が立たない
    want: list[tuple[int | None, str]] = []
    for T in range(total):
        td = T % TPD
        if DAY.day_head_due(T, td):
            want.append((T, "day_head"))
        want.extend((T, name) for name in plan)
        if DAY.day_close_due(T, td, TPD, total):
            want.append((T, "day_close"))
    want.extend((None, name) for name in ("drain", "close_final", "report"))
    assert [(T, name) for T, name, _t in seen] == want
    assert sum(1 for _T, name in want if name == "day_head") == 1 and ("day_close" in {n for _T, n in want})


# ================================================================= 2 日・再開
def test_two_days_and_resume_match_the_straight_run_for_the_arm(tmp_path):
    kw = dict(n_agents=30, seed=1, n_cells=9, ticks=TPD, checkpoint_every=360, renderer="stub")
    with width(BA.DEFAULT_WIDTH_S):
        straight60 = run_day(sim_days=2, **kw)
    with width(30):
        straight30 = run_day(sim_days=2, **kw)
        day = run_day(state_out=tmp_path / "d", stop_at_tick=TPD, sim_days=2, **kw)
        mid = run_day(state_out=tmp_path / "m", stop_at_tick=TPD + 371, sim_days=2, **kw)
        r_day = run_day(resume_from=tmp_path / "d" / day.resume["state_files"][-1]["file"], sim_days=2, **kw)
        r_mid = run_day(resume_from=tmp_path / "m" / mid.resume["state_files"][-1]["file"], sim_days=2, **kw)
    assert straight30.final_hash == straight60.final_hash
    assert r_day.final_hash == r_mid.final_hash == straight30.final_hash
    assert [c.behavior_hash for c in r_day.checkpoints] == [c.behavior_hash for c in straight30.checkpoints[-4:]]
    b = r_mid.run_manifest_fields()["batching"]
    assert b["windows"] == (2 * TPD - (TPD + 371)) * 2 and b["pending_at_end"] == 0  # 再開の窓は再開の刻みから
    # 幅の違う再開は設定の指紋で止まる(腕は指紋に入る)
    with width(BA.DEFAULT_WIDTH_S), pytest.raises(ValueError, match="設定が親と違う"):
        run_day(resume_from=tmp_path / "m" / mid.resume["state_files"][-1]["file"], sim_days=2, **kw)


def test_fingerprint_has_the_width_only_for_the_arm(tmp_path):
    kw = dict(n_agents=20, seed=1, n_cells=9, ticks=TPD, checkpoint_every=360, renderer="stub", sim_days=2,
              stop_at_tick=120)
    with width(BA.DEFAULT_WIDTH_S):
        a = run_day(state_out=tmp_path / "a", **kw)
    with width(5):
        b = run_day(state_out=tmp_path / "b", **kw)
    ha = RS.read_state(tmp_path / "a" / a.resume["state_files"][-1]["file"]).header["fingerprint"]
    hb = RS.read_state(tmp_path / "b" / b.resume["state_files"][-1]["file"]).header["fingerprint"]
    assert BA.FP_KEY not in ha and hb[BA.FP_KEY] == 5
    assert {k: v for k, v in hb.items() if k != BA.FP_KEY} == ha
    assert a.final_hash == b.final_hash


def test_a_non_default_width_is_an_arm_run(monkeypatch):
    kw = dict(n_agents=20, seed=1, world_dir=None, n_cells=9, ticks=30, checkpoint_every=10, vocab_version="v3")
    monkeypatch.delenv(RK.PYTEST_ENV, raising=False)
    with width(BA.DEFAULT_WIDTH_S):
        base = cli.run(**kw)
    with width(10):
        arm = cli.run(**kw)
    assert (base.run_kind, arm.run_kind) == ("reproduction", "arm")
    assert base.final_hash == arm.final_hash
    assert arm.run_manifest_fields()["batching"]["width_s"] == 10


# ================================================================= 試験の差の測り(段 B)と系ごとの指紋
def _probe_run(w: int) -> PR.Probe:
    pr = PR.Probe(check=CD.declared_check(SPECS), ticks=None)
    PR.ACTIVE = pr
    try:
        with width(w):
            run_day(**dict(SYN, ticks=150))
    finally:
        PR.ACTIVE = None
    return pr


def test_window_changes_are_attributed_to_the_window_mark_and_fingerprints_do_not_move():
    p60, p10 = _probe_run(BA.DEFAULT_WIDTH_S), _probe_run(10)
    for pr in (p60, p10):
        assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]
        writers = {s for _t, s, _d, keys in pr.entries if any(k.startswith("BW:") for k in keys)}
        assert writers == {CD.WINDOW_MARK}
        assert all(all(k.startswith("BW:") for k in keys) for _t, s, _d, keys in pr.entries if s == CD.WINDOW_MARK)
    rest = lambda pr: [e for e in pr.entries if e[1] != CD.WINDOW_MARK]  # noqa: E731
    assert rest(p10) == rest(p60)
    assert {k: v for k, v in p10.fp.items() if k != CD.WINDOW_MARK} == {
        k: v for k, v in p60.fp.items() if k != CD.WINDOW_MARK}


# ================================================================= CLI
_ARGS = ["--agents", "20", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "30"]
_CODE = "import sys; from shibuya import cli; sys.exit(cli.main(sys.argv[1:]))"


def _cli(tmp_path, name: str, env_w: str | None, cli_w: str | None) -> subprocess.CompletedProcess:
    out = tmp_path / f"{name}.json"
    argv = [*_ARGS, "--checkpoints-out", str(out)] + ([] if cli_w is None else ["--batch-width-s", cli_w])
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    env.pop(BA.ENV, None)
    if env_w is not None:
        env[BA.ENV] = env_w
    return subprocess.run([sys.executable, "-c", _CODE, *argv], capture_output=True, text=True, encoding="utf-8",
                          env=env, timeout=600)


@pytest.mark.parametrize("env_w,cli_w,want", [("10", "30", 30), ("30", None, 30), (None, None, STEP_SECONDS)])
def test_cli_batch_width_beats_the_environment(tmp_path, env_w, cli_w, want):
    r = _cli(tmp_path, f"{env_w}_{cli_w}", env_w, cli_w)
    assert r.returncode == 0, r.stderr[-2000:]
    man = json.loads((tmp_path / f"{env_w}_{cli_w}.json").read_text(encoding="utf-8"))["manifest"]
    assert man["batching"]["width_s"] == want


def test_cli_rejects_a_width_that_does_not_divide_the_step(tmp_path):
    r = _cli(tmp_path, "bad", None, "7")
    assert r.returncode == 2 and "--batch-width-s" in r.stderr


def test_a_bad_environment_width_fails_at_import():
    env = dict(os.environ, PYTHONIOENCODING="utf-8", **{BA.ENV: "7"})
    r = subprocess.run([sys.executable, "-c", "import shibuya.engine.batching"], capture_output=True, text=True,
                       encoding="utf-8", env=env, timeout=120)
    assert r.returncode != 0 and "まとめの幅" in r.stderr


# ================================================================= 世界資産
@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
def test_real_assets_width_10_matches_width_60():
    kw = dict(n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3")
    with width(BA.DEFAULT_WIDTH_S):
        r60 = cli.run(**kw)
    with width(10):
        r10 = cli.run(**kw)
    assert _hashes(r10) == _hashes(r60)
    assert r10.run_manifest_fields()["batching"]["windows"] == TPD * (STEP_SECONDS // 10)


# ================================================================= 〔3-2 検収 L1〕窓の境目は行 BW の鍵だけを通す
def test_l1_window_mark_passes_only_bw_keys_and_tick_head_stays_open():
    check = CD.declared_check(SPECS)
    assert check(CD.WINDOW_MARK, "BW:batching._bw_head") and check(CD.WINDOW_MARK, "BW:batching._bw_meter")
    for key in ("agents.cell", "stats.n_undefined_total", "E:events._ev_n", "scratch.plan", "buffers.focus_request"):
        assert not check(CD.WINDOW_MARK, key), key
        assert check(CD.TICK_HEAD, key), key  # 刻みの頭は前からの素通り(進行役の決まった文の差)


def test_l1_stage_b_catches_a_non_bw_change_at_the_window_mark(monkeypatch):
    """段 B(``SHIBUYA_SYSTEMS_CHECK``=``_conduct_checked``)が、窓の境目に帰属した行 BW の外の変化を落とす(負の対照:
    処理の後の境目の直後に診断の積算を 1 つ書き換える)。書き換えないランは通る(正の対照)。"""
    kw = dict(n_agents=20, seed=1, n_cells=9, ticks=30, renderer="stub")
    monkeypatch.setenv("SHIBUYA_SYSTEMS_CHECK", "1")
    with width(10):
        run_day(**kw)  # 正の対照
    real = BA.WindowQueue.run_window

    def bad(self, after_dispatch=None):  # noqa: ANN001, ANN202
        def ad():  # noqa: ANN202
            after_dispatch()
            box = after_dispatch.args[2]
            box.runstats.n_undefined_total += 1  # 窓の境目に帰属する、行 BW の外の変化

        return real(self, after_dispatch=ad)

    monkeypatch.setattr(BA.WindowQueue, "run_window", bad)
    with width(10), pytest.raises(AssertionError, match="宣言の外の変化"):
        run_day(**kw)
