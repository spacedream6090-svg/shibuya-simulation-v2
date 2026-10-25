"""第 1 期 1-8 候補の口 J0: 口の型と欄(口の約束 1-8 の受入の試験 ``test_j0_port_schema``)。

- ``Candidate``(id・kind・text・source=5 つの源・number=最後に振る・basis)・``Choice``(candidate_id・number・other_text・
  surprise 0〜5=空で始める・hesitation=空・continuous=DM13 の欄・reason_first・utterance=1-8b の欄=空)・``DecisionContext``
  (今の観測 ``percept`` と本人の予想 ``prediction`` を並べて持つ)。
- 3 つの実装が同じ入口(``DecisionPort.choose`` を上書きしない)。口は予想の値を解釈しない。
- 短い版と長い版は 1 つの仕組み(共通部分が先頭で同じバイト)。
"""

from __future__ import annotations

import ast
import dataclasses
import math
from pathlib import Path

import numpy as np
import pytest

from shibuya.engine.decision import port as P
from shibuya.engine.decision import ports as PS
from shibuya.engine.decision import sources as SR
from shibuya.llm.contract import cross_action_words

from tests.engine.decision._j0 import FakeBridge, FakePolicy, ctx_of, vocab_candidates

ROOT = Path(__file__).resolve().parents[3]
DECISION = ROOT / "src" / "shibuya" / "engine" / "decision"


def test_sources_are_the_five_of_dm0_and_the_bridge_mark():
    assert P.SOURCES == ("experience", "affordance", "plan", "continue", "deliberate")
    assert P.SOURCE_VOCAB == "vocab" and P.ALL_SOURCES == P.SOURCES + ("vocab",)
    with pytest.raises(ValueError):
        P.Candidate(id="x", kind="移動", text="移動", source="menu")


def test_candidate_fields_frozen_and_number_given_last():
    c = P.Candidate(id="affordance:購入", kind="購入", text="購入(ここでできる)", source="affordance",
                    basis=((np.int64(60), np.int32(2)),))
    assert [f.name for f in dataclasses.fields(P.Candidate)] == ["id", "kind", "text", "source", "number", "basis"]
    assert c.number is None and c.basis == ((60, 2),) and type(c.basis[0][0]) is int
    with pytest.raises(dataclasses.FrozenInstanceError):
        c.number = 1  # type: ignore[misc]
    assert not hasattr(c, "__dict__")  # slots
    for bad in (dict(id=""), dict(id=P.OTHER_ID), dict(kind=""), dict(text=" "), dict(number=0), dict(number=True),
                dict(basis=((1,),))):
        with pytest.raises(ValueError):
            P.Candidate(**{**dict(id="a", kind="移動", text="移動", source="vocab"), **bad})


def test_choice_fields_start_empty():
    names = [f.name for f in dataclasses.fields(P.Choice)]
    assert names == ["candidate_id", "number", "kind", "other_text", "surprise", "hesitation", "continuous",
                     "reason", "reason_first", "utterance", "payment", "backend"]  # payment=2-1 検収 A1(空で始める)
    ch = P.Choice(candidate_id="vocab:移動", number=3, kind="移動")
    assert (ch.surprise, ch.hesitation, ch.continuous, ch.utterance, ch.reason_first, ch.payment) == (None,) * 6
    with pytest.raises(ValueError):
        P.Choice(candidate_id="x", number=1, payment="小切手")  # 支払いの答えは PAYMENT_ANSWERS の語だけ
    assert not ch.is_other
    with pytest.raises(ValueError):
        P.Choice(candidate_id="x", number=1, surprise=6)
    with pytest.raises(ValueError):
        P.Choice(candidate_id="x", number=0)
    with pytest.raises(ValueError):
        P.Choice(candidate_id="x", number=1, other_text="自由")  # 自由記述は「その他」だけ
    with pytest.raises(ValueError):
        P.Choice(candidate_id=P.OTHER_ID, number=1, kind="移動")
    c = P.Choice(candidate_id="x", number=1, surprise=5, continuous={"speed": 1})
    assert P.SURPRISE_WORDS[c.surprise] == "ありえない" and dict(c.continuous) == {"speed": 1.0}
    with pytest.raises(TypeError):
        c.continuous["speed"] = 2.0  # type: ignore[index]
    # backend(口の後ろの道の結果)は比べない
    assert P.Choice(candidate_id="x", number=1, backend=1) == P.Choice(candidate_id="x", number=1, backend=2)


def test_surprise_words_and_hesitation():
    assert P.SURPRISE_WORDS == ("予想どおり", "少し違う", "違う", "かなり意外", "とても意外", "ありえない")
    h = P.Hesitation.of([0.5, 0.3, 0.2])
    assert math.isclose(h.margin, 0.2) and math.isclose(h.entropy, -(0.5 * math.log(0.5) + 0.3 * math.log(0.3)
                                                                       + 0.2 * math.log(0.2)))
    assert P.Hesitation.of([3]) == P.Hesitation(margin=1.0, entropy=0.0)
    with pytest.raises(ValueError):
        P.Hesitation.of([])


def test_context_puts_observation_and_prediction_side_by_side():
    names = [f.name for f in dataclasses.fields(P.DecisionContext)]
    assert names[:7] == ["agent_id", "step", "t_ns", "wake_class", "condition", "cell", "call_id"]
    assert names.index("prediction") == names.index("percept") + 1
    ctx = ctx_of()
    assert ctx.percept is None and ctx.prediction is None and ctx.memory is None and ctx.tools is None


@pytest.mark.parametrize("port_name", ["mock", "classical", "llm"])
def test_the_port_does_not_read_the_prediction(port_name):
    """口(と 3 つの実装)は予想の値を解釈しない: 予想を入れても同じ答え(驚くかは判断の側=10-03 §7)。"""
    cands = vocab_candidates()
    a = _choose(port_name, ctx_of(), cands)
    b = _choose(port_name, ctx_of(prediction={"次の電車": "8:03"}), cands)
    assert (a.candidate_id, a.number, a.kind) == (b.candidate_id, b.number, b.kind)


def _choose(port_name, ctx, cands):
    from shibuya.llm.mock import MockLLM

    kw = dict(seed=1)
    if port_name == "mock":
        port = PS.MockPort(FakeBridge("移動"), MockLLM(1, vocab=cross_action_words("v3"), form="v3"), **kw)
    elif port_name == "classical":
        port = PS.ClassicalPort(FakeBridge("就寝"), FakePolicy("就寝"), **kw)
    else:
        port = PS.LlmPort(FakeBridge("購入"), **kw)
    return port.choose(ctx, cands)


def test_three_implementations_share_one_entry():
    assert PS.PORT_NAMES == ("llm", "mock", "classical")
    for cls in (PS.LlmPort, PS.MockPort, PS.ClassicalPort):
        assert issubclass(cls, P.DecisionPort) and cls.choose is P.DecisionPort.choose and cls.name in PS.PORT_NAMES
    # AST: 実装のファイルに choose の定義が無い(上書きしない)
    tree = ast.parse((DECISION / "ports.py").read_text(encoding="utf-8"))
    assert not [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "choose"]


def test_present_numbers_last_and_maps_back():
    cands = vocab_candidates()
    assert all(c.number is None for c in cands)
    pr = P.present(cands, P.present_rng(1, 600, 7, len(cands)))
    assert sorted(c.number for c in pr) == list(range(1, len(cands) + 1))
    assert {c.id for c in pr} == {c.id for c in cands}
    again = P.present(cands, P.present_rng(1, 600, 7, len(cands)))
    assert [c.id for c in again] == [c.id for c in pr]  # 同じ鍵=同じ並び(決定的)
    orders = {tuple(c.id for c in P.present(cands, P.present_rng(1, 600, a, len(cands)))) for a in range(20)}
    assert len(orders) > 15  # 体ごとに並びが違う
    with pytest.raises(ValueError):
        P.present(cands + cands[:1], P.present_rng(1, 0, 0, 1))
    with pytest.raises(ValueError):
        P.present((dataclasses.replace(cands[0], number=1),), P.present_rng(1, 0, 0, 1))


def test_choose_returns_the_original_id_and_the_presented_number():
    cands = vocab_candidates()
    ch = PS.LlmPort(FakeBridge("会話"), seed=1).choose(ctx_of(), cands)
    assert ch.candidate_id.endswith(":会話") and ch.kind == "会話" and ch.reason_first is True and ch.reason == "理由"
    pr = P.present(cands, P.present_rng(1, 600, 7, len(cands)))
    assert ch.number == next(c.number for c in pr if c.id == ch.candidate_id)

    class Bad(P.DecisionPort):
        name = "bad"

        def _answer(self, ctx, presented):
            return "no-such-id", {}

    with pytest.raises(ValueError, match="提示に無い"):
        Bad(seed=1).choose(ctx_of(), cands)


def test_candidates_come_from_the_sources_and_keep_the_vocab():
    from shibuya.engine.llm_bridge import ACTION_WORD_BY_CODE
    from shibuya.llm.contract import safe_action_word

    for v in ("v1", "v2", "v3"):
        cands = vocab_candidates(v)
        assert [c.kind for c in cands if c.source != "deliberate"] == [safe_action_word(v)] + [
            w for w in cross_action_words(v) if w != safe_action_word(v)]
        assert cands[0].source == "continue" and cands[-1].id == SR.DELIBERATE_ID and cands[-1].source == "deliberate"
        assert len({c.id for c in cands}) == len(cands)
    # 予定(今の意図)・経験(想起)・周りが示すできこと
    from shibuya.perception.facts import IntentView

    class _P:
        intent = IntentView(action=0, target_kind=0, target=-1)  # 0=移動
        memories = (type("M", (), {"kind": 1, "event_id": (5, 1), "origin": "log"})(),  # 1=buy → 購入
                    type("M", (), {"kind": 1, "event_id": (9, 0), "origin": "legacy"})())
        seen_people = ()

    ctx = ctx_of(percept=_P())
    kind_words = SR.memory_kind_words(ACTION_WORD_BY_CODE)
    cands = SR.build_candidates(ctx, vocab=cross_action_words("v3"), continue_word="なし",
                                word_of_code=ACTION_WORD_BY_CODE, kind_words=kind_words,
                                affordance_words=lambda c, v: ("移動", "購入", "就寝"))
    by = {c.kind: c for c in cands}
    assert by["移動"].source == "plan" and by["購入"].source == "experience" and by["購入"].basis == ((5, 1),)
    assert by["就寝"].source == "affordance" and by["なし"].source == "continue" and by["通報"].source == "vocab"
    assert by["購入"].text == "購入(前にもした)" and by["通報"].text == "通報"


def test_compose_short_and_long_share_the_common_head():
    blocks = {b: f"[{b}] 中身" for b in ("B0", "B1", "B2", "B3", "B4", "B4b", "B5", "B6")}
    pr = P.present(vocab_candidates(), P.present_rng(1, 0, 0, 13))
    short, long = P.compose(blocks, pr, length="short"), P.compose(blocks, pr, length="long")
    common = "\n".join(blocks[b] for b in ("B0", "B1", "B2", "B3", "B4", "B4b"))
    assert short.startswith(common + "\n[B6]") and long.startswith(common + "\n[B5]")
    assert P.options_text(pr) in short and P.options_text(pr) in long
    assert long.endswith("最後に番号をひとつ書く(その他なら番号のあとに中身)。") and "理由" not in short
    lines = P.options_text(pr).splitlines()
    assert lines[0] == "頭に浮かんだこと:" and lines[-1] == f"{len(pr) + 1}. {P.OTHER_TEXT}"
    with pytest.raises(ValueError):
        P.compose(blocks, pr, length="medium")


def test_no_literal_example_numbers_in_the_prompt_parts():
    """DM4 の答え(数字はお金と時刻だけ)・R-97(例の数値を書かない): 提示と指示の文に数字の例を書かない。"""
    src = (DECISION / "port.py").read_text(encoding="utf-8")
    for name in ("_LONG_INSTRUCTION", "OTHER_TEXT"):
        line = next(ln for ln in src.splitlines() if ln.startswith(name))
        assert not any(ch.isdigit() for ch in line.split("=", 1)[1]), line
