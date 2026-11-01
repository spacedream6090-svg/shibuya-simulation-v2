"""第 1 期 1-8 候補の口 J0: 順のシャッフルと並べ替えの試験(C-2 の 1・受入の試験 ``test_j0_shuffle_invariance``)。

候補の順を入れ替えて渡しても、mock と古典(と LLM の口)の選択は**同じ中身**(候補の id と行為の語)。提示の番号は変わる。
並べ替えの試験(巡回のずらし全部)で、中身は 1 つ・選ばれた位置は散らばる(位置の偏りの記録=R-108 §3-1 の物差しの形)。
"""

from __future__ import annotations

import itertools

import pytest

from shibuya.engine.decision import port as P
from shibuya.engine.decision import ports as PS
from shibuya.llm.contract import cross_action_words
from shibuya.llm.mock import MockLLM

from tests.engine.decision._j0 import FakeBridge, FakePolicy, ctx_of, vocab_candidates


def _port(name: str):
    if name == "mock":
        return PS.MockPort(FakeBridge(), MockLLM(9, vocab=cross_action_words("v3"), form="v3"), seed=9)
    if name == "classical":
        return PS.ClassicalPort(FakeBridge(), FakePolicy("会話"), seed=9)
    return PS.LlmPort(FakeBridge("購入"), seed=9)


def _cyclic(seq):
    return [tuple(seq[k:]) + tuple(seq[:k]) for k in range(len(seq))]


@pytest.mark.parametrize("name", ["mock", "classical", "llm"])
def test_reordering_the_candidates_keeps_the_choice(name):
    port = _port(name)
    for agent, step in [(3, 100), (41, 777), (900, 1439)]:
        ctx = ctx_of(agent_id=agent, step=step, wake_class=1)
        cands = vocab_candidates("v3", ctx)
        got = [port.choose(ctx, order) for order in _cyclic(cands)]
        assert len({(c.candidate_id, c.kind) for c in got}) == 1, name   # 同じ中身
        assert len({c.number for c in got}) > 1, name                      # 提示の番号は変わる


@pytest.mark.parametrize("name", ["mock", "classical"])
def test_permutation_test_spreads_the_position(name):
    """並べ替えの試験: 同じ問いを巡回のずらし全部で出し、選ばれた位置の分布を見る(内容は 1 つ・位置は 13 か所に散る)。"""
    port = _port(name)
    ctx = ctx_of(agent_id=5, step=300, wake_class=2)
    cands = vocab_candidates("v3", ctx)
    positions = [port.choose(ctx, order).number for order in _cyclic(cands)]
    assert len(set(positions)) >= len(cands) // 2


def test_the_present_key_follows_agent_step_and_count():
    cands = vocab_candidates("v3")
    base = [c.id for c in P.present(cands, P.present_rng(1, 600, 7, len(cands)))]
    for args in [(2, 600, 7), (1, 601, 7), (1, 600, 8)]:
        other = [c.id for c in P.present(cands, P.present_rng(*args, len(cands)))]
        assert other != base, args
    # 候補の数も鍵の 1 語(数が違えば別の流れ)
    g1, g2 = P.present_rng(1, 600, 7, 13), P.present_rng(1, 600, 7, 12)
    assert g1.integers(0, 1 << 62) != g2.integers(0, 1 << 62)


def test_every_permutation_of_a_small_set_keeps_the_mock_choice():
    mock = MockLLM(2, vocab=cross_action_words("v3"), form="v3")
    port = PS.MockPort(FakeBridge(), mock, seed=2)
    ctx = ctx_of(agent_id=13, step=50, wake_class=0)
    cands = vocab_candidates("v3", ctx)
    sub = (cands[0],) + tuple(c for c in cands if c.kind in ("移動", "購入", "会話"))
    kinds = {port.choose(ctx, perm).kind for perm in itertools.permutations(sub)}
    assert len(kinds) == 1


def test_k19_runtime_audit_on_the_port_arm():
    """乱数の流れの検査(K19・実行時): 腕 port で並べ替えの流れ(decision.present)は重ならず、mock の鍵の作り直しは
    MockPort の設計として**腕 port の検査だけ**に渡す許可(``recreated_for(decision_port=True)``・検収 M2)。既定の腕の
    許可の表には無い=腕 port のランを既定の表で検査すると落ちる(負の対照)・既定の腕は作り直し 0。"""
    from shibuya.engine import rng_audit as RA
    from shibuya.engine.run import run_day

    from tests.engine.decision._j0 import SMALL, decision_arm

    out = {}
    for arm in ("legacy", "port"):
        with decision_arm(arm), RA.StreamRecorder() as rec:
            run_day(**SMALL)
        out[arm] = rec.analyze()
    assert "llm.mock" not in RA.K19_RECREATED
    assert RA.check_overlaps(out["legacy"]) == []
    assert RA.check_overlaps(out["port"], recreated=RA.recreated_for(decision_port=True)) == []
    bad = RA.check_overlaps(out["port"])  # 既定の表だけで見ると mock の作り直しを落とす
    assert len(bad) == 1 and "llm.mock" in bad[0]
    assert out["legacy"]["llm.mock"].same_key_recreated == 0 and "decision.present" not in out["legacy"]
    st = out["port"]["decision.present"]
    assert st.streams > 0 and st.actual_overlaps == 0 and st.keyed is False
    assert out["port"]["llm.mock"].same_key_recreated == out["port"]["decision.present"].streams
