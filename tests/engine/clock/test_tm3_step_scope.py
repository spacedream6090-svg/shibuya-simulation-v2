"""第 6 期 6-3 時計の段 T3: 何かあった体だけ(``engine.step_scope``・腕 ``--step-scope changed``)の試験。

- 検出器の内受容の判定を印の体だけに通した結果は、全員を見る版と同じ(印=判定の結果が変わりうる体を全部含むとき)。
  負の対照: 跨ぐ体を印から 1 つ抜くと違う。
- 変化の印: 前の検出の後に値か段が変わった体+前に跨いだ体(段は 1 回に 1 段=跨いだ体は次も見る)。負の対照: 跨いだ体を
  印に残さないと 2 段の跨ぎを取りこぼして全員を見る版と食い違う。
- 腕 changed のランは既定 all と final・呼数・checkpoint が同じ(合成の世界・世界資産)・2 日と再開=通し・段 B の宣言の外の
  書き 0・体の反映は TM5 の予約(reserve)・manifest の節と設定の指紋・CLI。
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys

import numpy as np
import pytest

from shibuya import cli
from shibuya.agents.state import AgentState
from shibuya.core.time_consts import STEPS_PER_DAY
from shibuya.engine import change_detect as CD
from shibuya.engine import manifest_sections as MS
from shibuya.engine import resume as RS
from shibuya.engine import step_scope as SS
from shibuya.engine.run import run_day
from shibuya.engine.systems import conductor as CO
from shibuya.engine.systems import probe as PR
from shibuya.engine.systems.table import SPECS
from shibuya.world.state import World

real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")
TPD = STEPS_PER_DAY
SYN = dict(n_agents=60, seed=1, n_cells=9, ticks=360, budget=60.0, checkpoint_every=60, vocab_version="v3",
           memory="on", relations="on", rel_copresent="on", store_memory="on", renderer="stub")


@contextlib.contextmanager
def scope(name: str):
    prev = SS.arm()
    SS.set_arm(name)
    try:
        yield
    finally:
        SS.set_arm(prev)


def _agents(n: int, seed: int) -> AgentState:
    a = AgentState(n)
    rng = np.random.default_rng(seed)
    for f in ("hunger", "fatigue", "thermal"):
        a.registry.field(f)[:] = rng.integers(0, 11, size=n)
    for _v, sf in CD.INTERO_VARS:
        a.registry.field(sf)[:] = rng.integers(0, 4, size=n)  # 値と合わない段も混ぜる(多段の跨ぎを含む)
    return a


def _crossing_set(det) -> set[int]:  # noqa: ANN001
    return {int(x) for c in det.crossings for x in c.agent_id.tolist()}


def _same(a, b) -> bool:  # noqa: ANN001
    return all(x.var == y.var and x.stage_field == y.stage_field and np.array_equal(x.agent_id, y.agent_id)
               and np.array_equal(x.new_stage, y.new_stage) and x.agent_id.dtype == y.agent_id.dtype
               and x.new_stage.dtype == y.new_stage.dtype for x, y in zip(a.crossings, b.crossings))


# ================================================================= 印の体だけの判定=全員を見る版
@pytest.mark.parametrize("seed", [1, 2, 3])
def test_scoped_interoception_equals_the_full_one_on_a_superset(seed):
    w = World.synthetic(n_cells=4, seed=seed)
    a = _agents(3000, seed)
    full = CD.ChangeDetector(a.n, w.n_cells).detect(w, a, 0)
    hit = sorted(_crossing_set(full))
    assert hit, "跨ぐ体が無い(試験にならない)"
    rng = np.random.default_rng(seed)
    extra = rng.choice(a.n, size=500, replace=False)
    for idx in (np.arange(a.n, dtype=np.int64), np.unique(np.concatenate([hit, extra])).astype(np.int64),
                np.asarray(hit, dtype=np.int64)):
        got = CD.ChangeDetector(a.n, w.n_cells).detect(w, a, 0, scope=idx)
        assert _same(got, full)
    # 負の対照: 跨ぐ体を 1 つ抜くと違う
    drop = np.asarray(hit[1:], dtype=np.int64)
    got = CD.ChangeDetector(a.n, w.n_cells).detect(w, a, 0, scope=drop)
    assert not _same(got, full)
    # 空の印=跨ぎなし(形は全員を見る版の空と同じ)
    none = CD.ChangeDetector(a.n, w.n_cells).detect(w, a, 0, scope=np.empty(0, dtype=np.int64))
    assert all(c.agent_id.size == 0 and c.agent_id.dtype == np.int64 and c.new_stage.dtype == np.uint8
               for c in none.crossings)


def _drive(a: AgentState, w: World, steps: int, rng, use_scope: bool, keep_crossed: bool = True):
    """値を乱数で少し動かしながら検出 → 段の書き戻しを繰り返す(全員を見る版と印の版)。"""
    from shibuya.engine import resolve as R

    det = CD.ChangeDetector(a.n, w.n_cells)
    sc = SS.StepScope(a.n)
    out = []
    for t in range(steps):
        k = rng.integers(0, a.n, size=40)
        for f in ("hunger", "fatigue", "thermal"):
            v = a.registry.field(f)
            v[k] = rng.integers(0, 11, size=k.size)
        if use_scope:
            res = sc.detect(det, w, a, t)
            R.apply_detection(a, w, res)
            sc.after_detection(a, res)
            if not keep_crossed:
                with SS._OG.writing(sc):  # 負の対照: 跨いだ体を印に残さない(持ち主の中を白箱で書き換える)
                    sc._ss_crossed = np.empty(0, dtype=np.int64)
        else:
            res = det.detect(w, a, t)
            R.apply_detection(a, w, res)
        out.append([(c.agent_id.tolist(), c.new_stage.tolist()) for c in res.crossings])
    return out, sc


def test_marks_follow_value_changes_and_keep_crossed_agents():
    w = World.synthetic(n_cells=4, seed=5)
    base_a, scoped_a = _agents(2000, 5), _agents(2000, 5)
    full, _ = _drive(base_a, w, 40, np.random.default_rng(9), use_scope=False)
    got, sc = _drive(scoped_a, w, 40, np.random.default_rng(9), use_scope=True)
    assert got == full
    m = sc.observed()
    assert m["steps"] == 40 and m["full_steps"] == 1 and m["marked"] < 40 * 2000 and m["crossed"] > 0
    # 負の対照: 跨いだ体を印に残さないと、2 段以上の跨ぎ(値と合わない段)を取りこぼす
    bad, _ = _drive(_agents(2000, 5), w, 40, np.random.default_rng(9), use_scope=True, keep_crossed=False)
    assert bad != full


def test_marks_are_exactly_the_changed_columns_and_the_crossed():
    w = World.synthetic(n_cells=4, seed=1)
    a = _agents(50, 1)
    det = CD.ChangeDetector(a.n, w.n_cells)
    sc = SS.StepScope(a.n)
    assert sc.marks(a) is None  # 写しの無い最初は全員
    res = sc.detect(det, w, a, 0)
    from shibuya.engine import resolve as R

    R.apply_detection(a, w, res)
    sc.after_detection(a, res)
    crossed = _crossing_set(res)
    a.registry.hunger[[3, 7]] = (a.registry.hunger[[3, 7]] + 1) % 11
    a.registry.thermal_stage[11] = (int(a.registry.thermal_stage[11]) + 1) % 4
    want = sorted(crossed | {3, 7, 11})
    assert sc.marks(a).tolist() == want


# ================================================================= ラン(既定 all と同じ)
def _hashes(res):  # noqa: ANN001
    return (res.final_hash, int(res.llm_calls), [(c.tick, c.behavior_hash, c.full_hash) for c in res.checkpoints])


def test_changed_run_matches_all_on_the_synthetic_world():
    base = run_day(**SYN)
    with scope("changed"):
        arm = run_day(**SYN)
    assert _hashes(arm) == _hashes(base)
    m = arm.run_manifest_fields()
    s = m["step_scope"]
    assert "step_scope" not in base.run_manifest_fields()
    assert s["arm"] == "changed" and s["body_schedule"] == "reserve" and m["body"]["arm"] == "reserve"
    assert s["steps"] == SYN["ticks"] and s["full_steps"] == 1 and 0 < s["marked_share"] < 1
    for k in SS.CONFIG_KEYS:
        assert MS.section_of(f"step_scope.{k}") == MS.CONFIG, k
    for k in SS.OBSERVED_KEYS:
        assert MS.section_of(f"step_scope.{k}") == MS.OBSERVED, k
    assert tuple(s) == SS.CONFIG_KEYS + SS.OBSERVED_KEYS


def test_two_days_and_resume_with_changed_match_the_straight_default(tmp_path):
    kw = dict(n_agents=40, seed=1, n_cells=9, ticks=TPD, checkpoint_every=360, renderer="stub")
    straight = run_day(sim_days=2, **kw)
    with scope("changed"):
        straight_c = run_day(sim_days=2, **kw)
        day = run_day(state_out=tmp_path / "d", stop_at_tick=TPD, sim_days=2, **kw)
        mid = run_day(state_out=tmp_path / "m", stop_at_tick=TPD + 371, sim_days=2, **kw)
        r_day = run_day(resume_from=tmp_path / "d" / day.resume["state_files"][-1]["file"], sim_days=2, **kw)
        r_mid = run_day(resume_from=tmp_path / "m" / mid.resume["state_files"][-1]["file"], sim_days=2, **kw)
    assert straight_c.final_hash == straight.final_hash
    assert r_day.final_hash == r_mid.final_hash == straight.final_hash
    assert [c.behavior_hash for c in r_day.checkpoints] == [c.behavior_hash for c in straight.checkpoints[-4:]]
    assert r_mid.run_manifest_fields()["step_scope"]["full_steps"] == 1  # 再開の後の最初の検出は全員
    hd = RS.read_state(tmp_path / "d" / day.resume["state_files"][-1]["file"]).header["fingerprint"]
    assert hd[SS.FP_KEY] == "changed"


def test_stage_b_declared_writes_with_changed():
    pr = PR.Probe(check=CO.declared_check(SPECS), ticks=None)
    PR.ACTIVE = pr
    try:
        with scope("changed"):
            run_day(**dict(SYN, ticks=120))
    finally:
        PR.ACTIVE = None
    assert pr.n_snap > 0 and not pr.violations, pr.violations[:10]
    writers = {s for _t, s, _d, keys in pr.entries if any(k.startswith("T3M:") for k in keys)}
    assert writers == {"detect"}


@real_data
def test_changed_run_matches_all_on_world_assets():
    kw = dict(n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3", memory="on", relations="on")
    base = cli.run(**kw)
    with scope("changed"):
        arm = cli.run(**kw)
    assert _hashes(arm) == _hashes(base)
    s = arm.run_manifest_fields()["step_scope"]
    assert s["marked_share"] < 0.5


_ARGS = ["--agents", "20", "--seed", "1", "--world", "__no_such_dir__", "--cells", "9", "--ticks", "30"]
_CODE = "import sys; from shibuya import cli; sys.exit(cli.main(sys.argv[1:]))"


def test_cli_step_scope_beats_the_environment_and_is_an_arm(tmp_path):
    out = tmp_path / "c.json"
    env = dict(os.environ, PYTHONIOENCODING="utf-8", **{SS.ENV: "all"})
    r = subprocess.run([sys.executable, "-c", _CODE, *_ARGS, "--checkpoints-out", str(out), "--step-scope", "changed"],
                       capture_output=True, text=True, encoding="utf-8", env=env, timeout=600)
    assert r.returncode == 0, r.stderr[-2000:]
    man = json.loads(out.read_text(encoding="utf-8"))["manifest"]
    assert man["step_scope"]["arm"] == "changed" and man["run_kind"] in ("arm", "test")


def test_arm_plumbing():
    assert SS.arm() == SS.DEFAULT_ARM == "all" and SS.is_default() and SS.make(10) is None
    with pytest.raises(ValueError):
        SS.set_arm("some")
    with scope("changed"):
        assert isinstance(SS.make(10), SS.StepScope)
    assert SS.manifest_fields(None) is None


def test_m2_step_scope_refuses_writes_from_outside():
    """〔検収 M2〕負の対照: 外から欄を書く・消す・写しの配列と計器の中身を書くと止まる。"""
    w = World.synthetic(n_cells=4, seed=1)
    a = _agents(50, 1)
    det = CD.ChangeDetector(a.n, w.n_cells)
    sc = SS.StepScope(a.n)
    from shibuya.engine import resolve as R

    res = sc.detect(det, w, a, 0)
    R.apply_detection(a, w, res)
    sc.after_detection(a, res)
    for name, value in (("_ss_copy", {}), ("_ss_crossed", np.arange(3)), ("_ss_meter", {}), ("n", 1), ("x", 1)):
        with pytest.raises(AttributeError):
            setattr(sc, name, value)
    with pytest.raises(AttributeError):
        del sc._ss_copy
    with pytest.raises(TypeError):
        sc._ss_copy["hunger"] = np.zeros(50, dtype=np.uint8)
    with pytest.raises(ValueError):
        sc._ss_copy["hunger"][0] = 9
    with pytest.raises(ValueError):
        sc._ss_crossed[:] = 0
    with pytest.raises(TypeError):
        sc._ss_meter["steps"] = 99
    # 持ち主の書く口は書ける(2 回目の検出)
    res = sc.detect(det, w, a, 1)
    R.apply_detection(a, w, res)
    sc.after_detection(a, res)
    assert sc._ss_meter["steps"] == 2
