"""第 1 期 1-8 候補の口 J0: 腕 on/off の同値(口の約束 1-8 の約束 (1)(2)・受入の試験 ``test_j0_mock_equivalence``)。

- 単体: ``MockPort`` は今の mock(``MockLLM.render``)と**同じ乱数の鍵から同じ番号**=同じ語(語彙 v1・v2・v3 の全部・提示を
  並べ替えても)。
- ラン: 腕 legacy と port で final・呼数・行動の件数・テープの全部の列が同じ。判断の番号列(呼ごとの (刻み・体・適用した
  行動のコード))が同じ。口の計器 ``mismatch``(今の道と違うコードを当てた数)は 0。古典の方策も同じ。
- 負の対照: ``MockPort`` の番号を 1 つずらすと ``mismatch`` が出て final が動く(口の答えが本当に当たっている)。
- 5,000 体 mock の 1 日(世界資産・slow): 判断の番号列が一致。
- 19 構成の byte-check(既定 legacy)と腕 port の 4 構成は記録 ``docs/bench/analysis/wallbounce-1012/j0/README.md``
  (``byte_check_j0.json``)。
"""

from __future__ import annotations

import hashlib
import json

import pyarrow.parquet as pq
import pytest

from shibuya.engine.decision import layer as DL
from shibuya.engine.decision import port as P
from shibuya.engine.decision import ports as PS
from shibuya.engine.llm_bridge import LLMBridge
from shibuya.engine.run import run_day
from shibuya.llm import LLMRequest, parse_two_line
from shibuya.llm.contract import cross_action_words
from shibuya.llm.mock import MockLLM

from tests.engine.decision._j0 import SMALL, FakeBridge, ctx_of, decision_arm, vocab_candidates


# ================================================================= 単体: 同じ鍵から同じ番号
@pytest.mark.parametrize("version,form", [("v1", "v1"), ("v2", "v1"), ("v3", "v3")])
def test_mock_port_picks_the_word_the_mock_writes(version, form):
    vocab = cross_action_words(version)
    mock = MockLLM(5, vocab=vocab, form=form)
    port = PS.MockPort(FakeBridge(), mock, seed=5)
    n = 0
    for a in range(0, 400, 7):
        for step in (0, 1, 59, 600, 1439, 2000):
            for cls in (-1, 0, 1, 2):
                ctx = ctx_of(agent_id=a, step=step, wake_class=cls)
                cands = vocab_candidates(version, ctx)
                ch = port.choose(ctx, cands)
                text = mock.render(LLMRequest(agent_id=a, tick=step, wake_class=cls, prompt=""))
                word = parse_two_line(text, version).action
                assert word is not None and ch.kind == word, (a, step, cls, word, ch.kind)
                assert vocab[mock.action_draw(a, step, cls) % len(vocab)] == ch.kind
                n += 1
    assert n > 1000


def test_mock_port_ignores_the_presented_order():
    mock = MockLLM(5, vocab=cross_action_words("v3"), form="v3")
    port = PS.MockPort(FakeBridge(), mock, seed=5)
    ctx = ctx_of(agent_id=11, step=777, wake_class=1)
    cands = vocab_candidates("v3", ctx)
    pr1 = P.present(cands, P.present_rng(5, 777, 11, len(cands)))
    pr2 = P.present(tuple(reversed(cands)), P.present_rng(5, 777, 11, len(cands)))
    assert [c.id for c in pr1] != [c.id for c in pr2]
    assert port.pick(ctx, pr1) == port.pick(ctx, pr2)


# ================================================================= ラン: 腕 on/off
def _tape_sha(path) -> dict:
    t = pq.read_table(path / "calls.parquet")
    return {n: hashlib.sha256(json.dumps(t.column(n).to_pylist(), ensure_ascii=False, default=str).encode()).hexdigest()
            for n in t.column_names}


def _flat(d, p: str = "") -> dict:
    """manifest を葉に平らにする(環境の節と壁時計の葉は落とす)。"""
    out: dict = {}
    if isinstance(d, dict):
        for k, v in d.items():
            q = f"{p}.{k}" if p else str(k)
            if q == "environment" or "wall" in str(k):
                continue
            out.update(_flat(v, q))
    elif isinstance(d, list):
        for i, v in enumerate(d):
            out.update(_flat(v, f"{p}.{i}"))
    else:
        out[p] = d
    return out


def _record_decisions(monkeypatch, sink: list) -> None:
    """判断の番号列: 呼ごとの (刻み・体・適用した行動のコード)。今の道は ``LLMBridge.call``・口の道は ``decide_one``。"""
    real_call, real_one = LLMBridge.call, DL.DecisionLayer.decide_one

    def call(self, agent_id, tick, wake_class, condition=0, **kw):
        res = real_call(self, agent_id, tick, wake_class, condition, **kw)
        sink.append((int(tick), int(agent_id), int(res.action_code)))
        return res

    def one(self, bridge, agent_id, step, wake_class, condition, **kw):
        res, p = real_one(self, bridge, agent_id, step, wake_class, condition, **kw)
        sink.append((int(step), int(agent_id), int(res.action_code)))
        return res, p

    monkeypatch.setattr(LLMBridge, "call", call)
    monkeypatch.setattr(DL.DecisionLayer, "decide_one", one)


def _pair(monkeypatch, tmp_path, **extra):
    kw = {**SMALL, **extra}
    seq_a: list = []
    seq_b: list = []
    with monkeypatch.context() as m:
        _record_decisions(m, seq_a)
        with decision_arm("legacy"):
            a = run_day(**kw, tape_path=tmp_path / "a")
    with monkeypatch.context() as m:
        _record_decisions(m, seq_b)
        with decision_arm("port"):
            b = run_day(**kw, tape_path=tmp_path / "b")
    return a, b, seq_a, seq_b


@pytest.mark.parametrize("extra", [
    {}, {"vocab_version": "v1"}, {"vocab_version": "v2"},
    {"memory": "on", "relations": "on"},
    {"policy": "classical", "chooser": "classical", "memory": "on", "relations": "on"},
], ids=["v3", "v1", "v2", "v3_mem_rel", "v3_classical_mem_rel"])
def test_arm_on_off_same_final_tape_and_decision_sequence(monkeypatch, tmp_path, extra):
    a, b, seq_a, seq_b = _pair(monkeypatch, tmp_path, **extra)
    assert a.final_hash == b.final_hash and a.llm_calls == b.llm_calls
    assert dict(a.action_usage) == dict(b.action_usage)
    assert _tape_sha(tmp_path / "a") == _tape_sha(tmp_path / "b")
    assert seq_a == seq_b and len(seq_a) == a.llm_calls > 0
    ma, mb = a.run_manifest_fields(), b.run_manifest_fields()
    da, db = ma["decision_port"], mb["decision_port"]
    assert da["arm"] == "legacy" and da["port"] is None and da["decisions"] is None
    assert db["arm"] == "port" and db["port"] == ("classical" if extra.get("policy") == "classical" else "mock")
    assert db["mismatch"] == 0 and db["decisions"] == a.llm_calls and db["late"] == 0 and db["other"] == 0
    # 既存の欄は不変(違う葉は decision_port と、出来事の記録の日次の計器だけ。壁時計の葉と環境の節は比べない)
    fa, fb = _flat(ma), _flat(mb)
    moved = sorted(k for k in set(fa) | set(fb) if fa.get(k) != fb.get(k))
    assert moved and all(k.startswith("decision_port.") or ".events." in k for k in moved), moved
    assert any(k.startswith("daily.") and ".events." in k for k in moved)
    ev_a, ev_b = ma["daily"][-1]["events"], mb["daily"][-1]["events"]
    assert ev_b["by_cause"].get("llm_call", 0) == db["events"] > 0 and "llm_call" not in ev_a["by_cause"]


def test_negative_control_shifting_the_mock_number_moves_the_final(monkeypatch, tmp_path):
    real = PS.MockPort.pick

    def shifted(self, ctx, presented):
        cid = real(self, ctx, presented)
        ex = sorted((c for c in presented if c.kind in self._rank), key=lambda c: (self._rank[c.kind], c.id))
        ids = [c.id for c in ex]
        return ids[(ids.index(cid) + 1) % len(ids)]

    with decision_arm("legacy"):
        a = run_day(**SMALL)
    monkeypatch.setattr(PS.MockPort, "pick", shifted)
    with decision_arm("port"):
        b = run_day(**SMALL)
    db = b.run_manifest_fields()["decision_port"]
    assert db["mismatch"] > 0 and a.final_hash != b.final_hash


def test_legacy_arm_builds_no_layer_and_keeps_the_bridge_call(monkeypatch):
    seen = []
    real = DL.DecisionLayer.__init__

    def init(self, *a, **k):
        seen.append(1)
        real(self, *a, **k)

    monkeypatch.setattr(DL.DecisionLayer, "__init__", init)
    with decision_arm("legacy"):
        r = run_day(**{**SMALL, "ticks": 60})
    assert seen == [] and getattr(r, "decision_layer", "x") is None


@pytest.mark.slow
@pytest.mark.requires_data("world_v2:w17_schedule.parquet")
def test_5000_agents_one_day_same_decision_sequence(monkeypatch, tmp_path):
    """5,000 体 mock の 1 日(世界資産・語彙 v3=byte-check の w6_v3_default と同じ構成): 判断の番号列が一致。"""
    from shibuya import cli

    seqs = []
    for arm in ("legacy", "port"):
        seq: list = []
        with monkeypatch.context() as m:
            _record_decisions(m, seq)
            with decision_arm(arm):
                res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", vocab_version="v3",
                              tape_path=str(tmp_path / arm))
        seqs.append((seq, res.final_hash, res.llm_calls))
    (sa, fa, ca), (sb, fb, cb) = seqs
    assert fa == fb and ca == cb and sa == sb and len(sa) == ca > 50_000
