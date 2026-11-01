"""第 3 期 3-3b T からの切り替えの口(``engine.experiment.switch``・CP5-2 の完成)と 4 つの確認の (c)(d) の分け(仮-24)。

- T は計算のまとめの窓の頭(3-2 の窓の待ち行列): 窓の頭でない T は止める(負の対照)・幅 30 秒なら刻みの途中の窓の頭も受ける。
- 再生の箱: 刻みが替わると空にする(``box_carried``・``box_at_switch`` が 0)・空にしない写しは (b) が落ちる(負の対照=口の単体と
  合成の世界の分岐の両方)。テープに T をまたいで届く行(艦隊で録った到着待ちの行)があれば切り替えを拒む(負の対照)。
- 合成の世界の分岐: 仮のモデル=mock(決定論の確認=A/A の枝 2 本が厳密に同じ・final=基準・床 0)と、注入した非決定の口
  (T からだけ答えがずれる=実 LLM の代わり)の床の分布((d) は T より前の一致だけ・床は 0 でない・(c) は A/A の枝 2 本の最初の
  食い違いとの刻みの差)。古典の方策は札 classical・決定論。
- 〔検収 L2〕注入した口は属性 ``deterministic``(真偽)で決定論を宣言できる=宣言があれば (d) の決定論の確認をかける(宣言した決定論の口は A/A が厳密に同じで通る・宣言した口が実は非決定なら (d) が落ちる=負の対照)。宣言の無い注入の口は非決定のまま・``run_branch`` の指定が口の宣言より先・真偽でない値は宣言とみなさない。
- 〔検収 L8〕計器の数(テープの再生の数と箱の数)は読み取り専用(外からの代入は AttributeError)。
"""

from __future__ import annotations

import copy
import itertools
import json
from pathlib import Path

import pytest

from shibuya import cli
from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_DAY
from shibuya.engine.experiment import branch as BR
from shibuya.engine.experiment import switch as SW
from shibuya.engine.tape import TapeRow, TapeWriter
from shibuya.llm import LLMRequest, LLMResponse

from tests.engine.experiment._x33 import form

NOON_DAY2_NS = (SECONDS_PER_DAY + SECONDS_PER_DAY // 2) * NS_PER_SECOND
T0 = (SECONDS_PER_DAY + SECONDS_PER_DAY // 2) // 60
STEP_NS = 60 * NS_PER_SECOND
SKW = dict(n_agents=80, seed=1, world_dir=None, n_cells=9, sim_days=2, renderer="stub", checkpoint_every=60)


# ================================================================= 窓の頭
def test_window_head_step():
    assert SW.window_head_step(NOON_DAY2_NS, STEP_NS, STEP_NS) == T0
    # 幅 30 秒: 刻みの途中の窓の頭(正午 30 秒)も受ける=切り替わるのは次の刻み(切り上げ=申込書の T0 の刻みと同じ)
    t = NOON_DAY2_NS + 30 * NS_PER_SECOND
    assert SW.window_head_step(t, 30 * NS_PER_SECOND, STEP_NS) == T0 + 1 == form(start=t).start_step(60)
    # 負の対照: 窓の頭でない・幅が刻みの約数でない
    with pytest.raises(ValueError, match="窓の頭でない"):
        SW.window_head_step(NOON_DAY2_NS + NS_PER_SECOND, STEP_NS, STEP_NS)
    with pytest.raises(ValueError, match="窓の頭でない"):
        SW.window_head_step(NOON_DAY2_NS + 10 * NS_PER_SECOND, 30 * NS_PER_SECOND, STEP_NS)
    with pytest.raises(ValueError, match="約数"):
        SW.window_head_step(0, 7 * NS_PER_SECOND, STEP_NS)


def _fake_base(tmp_path: Path, *, width_s: int = 60, rows=()) -> Path:
    base = tmp_path / "base"
    (base / BR.BASE_TAPE).mkdir(parents=True)
    (base / BR.BASE_CHECKPOINTS).write_text(json.dumps({"manifest": {"tick_seconds": 60, "sim_days": 2,
                                                                     "batching": {"width_s": width_s}}}),
                                            encoding="utf-8")
    with TapeWriter(base / BR.BASE_TAPE) as w:
        for r in rows:
            w.append(r)
    return base


def _row(agent: int, step: int, *, observed: int = -1, deferred: int = 0, prompt: str = "p") -> TapeRow:
    req = LLMRequest(agent_id=agent, tick=step, wake_class=1, prompt=prompt)
    return TapeRow(call_id=f"c{agent}-{step}", agent_id=agent, tick=step, wake_class=1, prompt_hash=req.prompt_hash,
                   block_ids=(), params_hash="", response="" if deferred else f"答え{agent}-{step}",
                   deferred=deferred, observed_tick=observed)


def test_run_branch_refuses_a_t0_that_is_not_a_window_head(tmp_path):
    base = _fake_base(tmp_path)
    with pytest.raises(ValueError, match="窓の頭でない"):
        BR.run_branch(form(start=NOON_DAY2_NS + NS_PER_SECOND), base, runner=cli.run, run_kwargs={})


def test_run_branch_refuses_a_tape_with_rows_crossing_t0(tmp_path):
    """負の対照: T より前に出して T 以後に届く行(艦隊の到着待ち)=再生の箱に刻みの外の物が残る=止める。"""
    base = _fake_base(tmp_path, rows=[_row(1, 10), _row(2, T0 - 1, observed=T0 + 1)])
    with pytest.raises(ValueError, match="刻みの外の物"):
        BR.run_branch(form(start=NOON_DAY2_NS), base, runner=cli.run, run_kwargs={})
    from shibuya.engine.tape import Tape

    assert SW.tape_crossing(Tape(base / BR.BASE_TAPE), T0) == {"fleet_rows_before_t0": 1, "rows_crossing_t0": 1}
    assert SW.tape_crossing(Tape(base / BR.BASE_TAPE), T0 - 1) == {"fleet_rows_before_t0": 0, "rows_crossing_t0": 0}


# ================================================================= 再生の箱(口の単体)
class _Live:
    source = "stand_in"

    def __init__(self):
        self.n = 0

    def complete(self, request):
        self.n += 1
        return LLMResponse(text=f"今の口{request.agent_id}", source="stand_in")


def _switch(tmp_path, *, rows, t0_step: int, live=None, cls=SW.ReplaySwitch) -> SW.ReplaySwitch:
    base = _fake_base(tmp_path, rows=rows)
    spec = SW.SwitchSpec(tape=str(base / BR.BASE_TAPE), t0_step=t0_step, t0_ns=t0_step * STEP_NS, window_ns=STEP_NS,
                         step_ns=STEP_NS, live=live)
    return cls(_Live(), spec)


def _req(agent: int, step: int) -> LLMRequest:
    return LLMRequest(agent_id=agent, tick=step, wake_class=1, prompt="p")


def test_replay_switch_box_is_emptied_every_step(tmp_path):
    rows = [_row(a, s) for s in (3, 4, 5) for a in (1, 2)]
    sw = _switch(tmp_path, rows=rows, t0_step=5)
    for s in (3, 4):
        for a in (1, 2):
            assert sw.complete(_req(a, s)).text == f"答え{a}-{s}"  # T より前=テープの答え
    out = sw.complete(_req(1, 5))
    assert out.text == "今の口1" and sw.post.n == 1  # T から=仮のモデル
    m = sw.replay_meter()
    assert m["replayed_before_t0"] == 4 and m["live_from_t0"] == 1 and m["box_peak"] == 2
    assert m["box_carried"] == 0 and m["box_at_switch"] == 0 and m["first_live_step"] == 5
    assert m["model"] == "stand_in" and m["deterministic"] is False and m["tape_miss_before_t0"] == 0
    rec = sw.switch_record()
    assert rec["t0_step"] == 5 and rec["window_ns"] == STEP_NS and rec["post_is_run_client"] is True


class _Leaky(SW.ReplaySwitch):
    """負の対照: 刻みが替わっても箱を空にしない写し。"""

    def _box_reset(self, step):
        object.__setattr__(self, "_box_step", int(step))


def test_a_leaky_box_is_caught(tmp_path):
    rows = [_row(a, s) for s in (3, 4, 5) for a in (1, 2)]
    sw = _switch(tmp_path, rows=rows, t0_step=5, cls=_Leaky)
    for s in (3, 4):
        sw.complete(_req(1, s))
    sw.complete(_req(1, 5))
    m = sw.replay_meter()
    assert m["box_carried"] > 0 and m["box_at_switch"] > 0
    doc = {"checkpoints": [{"tick": 1, "behavior_hash": "x"}]}
    assert BR.pre_t0_match(doc, doc, 5, replay=m)["ok"] is False  # (b) が落ちる
    assert BR.pre_t0_match(doc, doc, 5, replay={**m, "box_carried": 0, "box_at_switch": 0})["ok"] is True


def test_live_factory_answers_only_from_t0(tmp_path):
    rows = [_row(1, 3)]
    sw = _switch(tmp_path, rows=rows, t0_step=4, live=lambda client: _Other(client))
    assert sw.complete(_req(1, 3)).text == "答え1-3"
    assert sw.complete(_req(1, 4)).text == "別の口" and sw.model == "other"
    assert sw.switch_record()["post_is_run_client"] is False


class _Other:
    source = "other"

    def __init__(self, inner):
        self.inner = inner

    def complete(self, request):
        return LLMResponse(text="別の口", source="other")


def test_model_labels_and_determinism():
    from shibuya.llm.mock import MockLLM

    assert SW.model_label(MockLLM(1)) == "mock" and SW.model_label(_Live()) == "stand_in"
    assert SW.is_deterministic("mock") and SW.is_deterministic("classical") and not SW.is_deterministic("llm")
    assert SW.is_deterministic("llm", True) and not SW.is_deterministic("mock", False)
    v = SW.vs_aa({"first_step": 100}, {"first_step": None})
    assert v["gap_steps"] is None and "床 0" in v["status"]
    assert SW.vs_aa({"first_step": 100}, {"first_step": 130})["gap_steps"] == 30
    assert "埋もれる" in SW.vs_aa({"first_step": 100}, {"first_step": 90})["status"]
    d = SW.determinism(model="mock", deterministic=True, twins_vs_base=(True, True), twins_before_t0=True,
                       aa_exact=False, final_equals_base=True, expect_base=True)
    assert d["ok"] is False  # 決定論の札で A/A が食い違う=落ちる
    nd = SW.determinism(model="llm", deterministic=False, twins_vs_base=(True, True), twins_before_t0=True,
                        aa_exact=False, final_equals_base=False, expect_base=True)
    assert nd["ok"] is True and nd["aa_exact_required"] is False


# ================================================================= 合成の世界の分岐
@pytest.fixture(scope="module")
def synth_base(tmp_path_factory):
    out = tmp_path_factory.mktemp("cf33b_base")
    res = cli.run(tape_path=out / BR.BASE_TAPE, state_out=out / BR.BASE_STATE, **SKW)
    (out / BR.BASE_CHECKPOINTS).write_text(json.dumps(cli.checkpoints_payload(res), ensure_ascii=False, default=str),
                                           encoding="utf-8")
    return out


def _event_form():
    return form(start=NOON_DAY2_NS, content=[{"decision": "event"}], notice={"to": [1, 2], "via": "メッセージ"})


def test_switch_with_the_mock_is_deterministic(synth_base, tmp_path):
    out = BR.run_branch(_event_form(), synth_base, runner=cli.run, run_kwargs=SKW, out_dir=tmp_path / "br")
    rep = out.report
    s = rep["summary"]
    assert s["a"] and s["b"] is True and s["d"] is True and s["ok"] and s["model"] == "mock" and s["deterministic"]
    det = rep["checks"]["d_determinism"]
    assert det["aa_exact"] and det["final_equals_base"] and det["final_equals_base_required"] and det["ok"]
    fl = rep["checks"]["d_floor"]
    assert fl["zero"] and fl["checkpoints_differ"] == 0 and fl["metrics"]["calls"]["abs_max"] == 0.0
    c = rep["checks"]["c_first_divergence"]
    assert c["aa_coarse"]["first_step"] is None and c["vs_aa"]["aa_first_step"] is None
    b = rep["checks"]["b_pre_t0"]
    assert b["aa_b"]["ok"] is True and b["branch"]["box_left"] == 0
    r = out.branch.run_manifest_fields()["experiment"]
    assert r["switch"]["model"] == "mock" and r["switch"]["t0_step"] == T0 and r["switch"]["window_ns"] == STEP_NS
    assert r["replay"]["box_carried"] == 0 and r["replay"]["box_at_switch"] == 0 and r["replay"]["first_live_step"] >= T0
    assert rep["switch"] == r["switch"] and r["checks"]["d_floor_zero"] is True


def test_switch_leaky_box_fails_b_end_to_end(synth_base, tmp_path, monkeypatch):
    """負の対照(合成の世界の分岐): 箱を空にしない写しに差し替えると (b) が落ちる。"""
    monkeypatch.setattr(SW.ReplaySwitch, "_box_reset", _Leaky._box_reset)
    out = BR.run_branch(_event_form(), synth_base, runner=cli.run, run_kwargs=SKW, out_dir=tmp_path / "leak")
    s = out.report["summary"]
    assert s["b"] is False and s["ok"] is False
    assert out.report["checks"]["b_pre_t0"]["branch"]["box_left"] > 0


class _Noisy:
    """T からだけ答えがずれる口(実 LLM の非決定の代わり=作るたびに別の種の mock)。"""

    source = "llm_stand_in"
    _ids = itertools.count(1)

    def __init__(self, inner):
        self.inner = copy.copy(inner)
        self.inner.master_seed = f"{inner.master_seed}:noisy{next(self._ids)}"

    def complete(self, request):
        return self.inner.complete(request)


def test_switch_with_a_nondeterministic_model_gives_a_floor(synth_base, tmp_path):
    out = BR.run_branch(_event_form(), synth_base, runner=cli.run, run_kwargs=SKW, out_dir=tmp_path / "noisy",
                        live=_Noisy)
    rep = out.report
    s = rep["summary"]
    assert s["model"] == "llm_stand_in" and s["deterministic"] is False
    assert s["a"] and s["b"] is True and s["d"] is True and s["ok"]  # (d)=T より前の一致だけ(厳密一致は求めない)
    det = rep["checks"]["d_determinism"]
    assert det["twins_before_t0"] is True and det["aa_exact"] is False and det["aa_exact_required"] is False
    fl = rep["checks"]["d_floor"]
    assert not fl["zero"] and fl["checkpoints_differ"] > 0 and fl["first_differ_step"] >= T0
    assert fl["metrics"]["calls"]["n"] == 1
    c = rep["checks"]["c_first_divergence"]
    assert c["aa_coarse"]["first_step"] is not None and c["vs_aa"]["gap_steps"] is not None
    assert s["c_aa_step"] == c["aa_coarse"]["first_step"]
    # T より前は全部の枝が基準と同じ(テープ)
    for k in ("aa", "aa_b", "branch"):
        assert rep["checks"]["b_pre_t0"][k]["ok"] is True and rep["checks"]["b_pre_t0"][k]["tape_miss_before_t0"] == 0
    assert out.branch.run_manifest_fields()["experiment"]["switch"]["post_is_run_client"] is False


def test_switch_with_the_classical_policy(tmp_path):
    kw = dict(n_agents=60, seed=1, world_dir=None, n_cells=9, sim_days=2, checkpoint_every=60, vocab_version="v3",
              policy="classical", chooser="classical", memory="on", relations="on")
    base = tmp_path / "base"
    res = cli.run(tape_path=base / BR.BASE_TAPE, state_out=base / BR.BASE_STATE, **kw)
    (base / BR.BASE_CHECKPOINTS).write_text(json.dumps(cli.checkpoints_payload(res), ensure_ascii=False, default=str),
                                            encoding="utf-8")
    out = BR.run_branch(form(start=NOON_DAY2_NS, content=[{"decision": "event"}]), base, runner=cli.run,
                        run_kwargs=kw, out_dir=tmp_path / "br")
    s = out.report["summary"]
    assert s["model"] == "classical" and s["deterministic"] and s["ok"] and out.report["checks"]["d_floor"]["zero"]
    r = out.branch.run_manifest_fields()["experiment"]["replay"]
    assert r["stateful_policy"] and r["policy_mismatch_before_t0"] == 0 and r["box_carried"] == 0


# ================================================================= 〔検収 L2〕注入した口の決定論の宣言
class _Declared:
    """決定論を宣言した注入の口(T からだけ答える・同じ入力に同じ答え)。"""

    source = "det_stub"
    deterministic = True

    def __init__(self, inner):
        self.inner = inner

    def complete(self, request):
        return self.inner.complete(request)


class _NoisyDeclared(_Noisy):
    """負の対照: 決定論を宣言したのに実は非決定の口(作るたびに別の種の mock)。"""

    source = "det_stub_noisy"
    deterministic = True


def test_an_injected_port_can_declare_determinism(tmp_path):
    rows = [_row(1, 3)]
    sw = _switch(tmp_path / "a", rows=rows, t0_step=4, live=_Declared)
    assert sw.model == "det_stub" and sw.deterministic is True and sw.deterministic_by == "port"
    assert sw.replay_meter()["deterministic"] is True and sw.switch_record()["deterministic_by"] == "port"
    # 宣言の無い注入の口は非決定のまま(既定は変えない)
    sw2 = _switch(tmp_path / "b", rows=rows, t0_step=4, live=lambda client: _Other(client))
    assert sw2.deterministic is False and sw2.deterministic_by == "label"
    # run_branch の指定は口の宣言より先
    base = _fake_base(tmp_path / "c", rows=rows)
    spec = SW.SwitchSpec(tape=str(base / BR.BASE_TAPE), t0_step=4, t0_ns=4 * STEP_NS, window_ns=STEP_NS, step_ns=STEP_NS,
                         live=_Declared, deterministic=False)
    sw3 = SW.ReplaySwitch(_Live(), spec)
    assert sw3.deterministic is False and sw3.deterministic_by == "spec"
    # 真偽でない値・属性の無い口は宣言とみなさない(札で決める=mock は決定論)
    from shibuya.llm.mock import MockLLM

    assert SW.declared_determinism(type("X", (), {"deterministic": 1})()) is None
    assert SW.declared_determinism(MockLLM(1)) is None and SW.declared_determinism(_Declared(None)) is True


def test_switch_with_a_declared_deterministic_port(synth_base, tmp_path):
    out = BR.run_branch(_event_form(), synth_base, runner=cli.run, run_kwargs=SKW, out_dir=tmp_path / "det",
                        live=_Declared)
    s = out.report["summary"]
    assert s["model"] == "det_stub" and s["deterministic"] is True and s["d"] is True and s["ok"]
    det = out.report["checks"]["d_determinism"]
    assert det["aa_exact_required"] is True and det["aa_exact"] is True and det["final_equals_base_required"] is False
    assert out.report["switch"]["deterministic_by"] == "port" and out.report["checks"]["d_floor"]["zero"]
    # 負の対照: 決定論を宣言したのに非決定の口は (d) が落ちる(厳密一致を求める)
    bad = BR.run_branch(_event_form(), synth_base, runner=cli.run, run_kwargs=SKW, out_dir=tmp_path / "bad",
                        live=_NoisyDeclared)
    sb = bad.report["summary"]
    assert sb["deterministic"] is True and sb["d"] is False and sb["ok"] is False
    assert bad.report["checks"]["d_determinism"]["aa_exact"] is False


# ================================================================= 〔検収 L8〕計器の数は読み取り専用
def test_meters_are_read_only(tmp_path):
    sw = _switch(tmp_path / "a", rows=[_row(1, 3)], t0_step=4)
    for name in ("box_carried", "box_at_switch", "box_peak", "box_repeats", "first_live_step", "n_miss", "n_live",
                 "n_mismatch", "n_replayed", "n_policy_before"):
        with pytest.raises(AttributeError):
            setattr(sw, name, 0)
    sw.complete(_req(1, 3))
    sw.complete(_req(1, 4))
    assert (sw.n_replayed, sw.n_live, sw.box_peak, sw.box_carried, sw.box_at_switch) == (1, 1, 1, 0, 0)
    base = _fake_base(tmp_path / "b", rows=[_row(1, 3)])
    bc = BR.BranchClient(_Live(), BR.BranchSpec(tape=str(base / BR.BASE_TAPE), t0_step=4))
    with pytest.raises(AttributeError):
        bc.n_miss = 3  # type: ignore[misc]
    assert bc.replay_meter()["tape_miss_before_t0"] == 0
