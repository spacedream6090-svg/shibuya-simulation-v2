"""第 1 期 1-8 候補の口 J0: 「その他(自由記述)」の欄と割合の計器(C-2 の 3・受入の試験 ``test_j0_other_ratio_field``)。

- 「その他」は提示の最後(番号 n+1)・自由記述は ``Choice.other_text``。LLM の口は、どの候補にも当たらない答え(語彙の外・
  役割語・書式の誤り)を「その他」にし、答えの語を残す(生まれた行動の入口)。
- 割合の既定は R-108 の値=**値を置かない**(測った原典なし=空欄 R108-1)。割合は manifest の ``decision_port.other_ratio``
  (計器)。腕 legacy のランは観測の子が null。mock と古典は「その他」を選ばない(今の道と同じ=0)。
"""

from __future__ import annotations

from shibuya.engine.decision import layer as DL
from shibuya.engine.decision import port as P
from shibuya.engine.decision import ports as PS
from shibuya.engine.run import run_day

from tests.engine.decision._j0 import SMALL, FakeBridge, FakePolicy, ctx_of, decision_arm, vocab_candidates


def test_default_other_share_is_unset_with_the_r108_basis():
    assert P.OTHER_SHARE_DEFAULT is None
    assert "R-108" in P.OTHER_SHARE_BASIS and "R108-1" in P.OTHER_SHARE_BASIS
    assert P.OTHER_ID == "other" and P.OTHER_TEXT.startswith("その他")


def test_llm_port_puts_an_unmatched_answer_in_other():
    cands = vocab_candidates("v3")
    ch = PS.LlmPort(FakeBridge(None, raw="踊る"), seed=1).choose(ctx_of(), cands)
    assert ch.is_other and ch.other_text == "踊る" and ch.number == len(cands) + 1 and ch.kind is None
    # 役割語(v3 の横断語に無い)も「その他」(今の道は安全弁に落とす=口は語を残すだけ)
    ch = PS.LlmPort(FakeBridge("接客"), seed=1).choose(ctx_of(), cands)
    assert ch.is_other and ch.other_text == "接客"


def test_classical_port_answers_other_only_outside_the_candidates():
    cands = vocab_candidates("v3")
    assert not PS.ClassicalPort(FakeBridge(), FakePolicy("食事"), seed=1).choose(ctx_of(), cands).is_other
    ch = PS.ClassicalPort(FakeBridge(), FakePolicy("散歩"), seed=1).choose(ctx_of(), cands)
    assert ch.is_other and ch.other_text == "散歩"


def test_manifest_carries_the_ratio_field():
    with decision_arm("legacy"):
        a = run_day(**SMALL)
    with decision_arm("port"):
        b = run_day(**SMALL)
    da, db = a.run_manifest_fields()["decision_port"], b.run_manifest_fields()["decision_port"]
    assert set(da) == set(db) == set(DL.CONFIG_KEYS) | set(DL.OBSERVED_KEYS)
    assert list(db) == list(DL.CONFIG_KEYS) + list(DL.OBSERVED_KEYS)
    assert da["other_ratio"] is None and da["other"] is None and da["other_share_default"] is None
    assert db["other"] == 0 and db["other_ratio"] == 0.0 and db["decisions"] > 0
    assert db["chosen_by_source"]["other"] == 0
    assert sum(db["chosen_by_source"].values()) == db["decisions"]
    assert sum(db["chosen_number"].values()) == db["decisions"]
    assert set(db["presented_by_source"]) == set(P.ALL_SOURCES)
    n = int(next(iter(db["n_candidates"])))
    assert sum(db["presented_by_source"].values()) == n * db["decisions"]
    assert db["presented_by_source"]["deliberate"] == db["decisions"]
