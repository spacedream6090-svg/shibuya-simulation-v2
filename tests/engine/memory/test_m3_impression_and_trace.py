"""第 6 期 6-5 記憶 M3 の器(印象の履歴と寝たときの書き直し)と、注意を向けずに見ていた人の浅い痕跡の口(mock で試験)。

- M3: 会話の直後に短く履歴へ足す(原因=LLM の呼び)・寝たときに追記のあった相手だけ書き直しを**足す**(古い要約も残る)・
  今の印象=最後の書き直し・昼の結論は意味の記憶へ・原因が LLM の呼びでなければ書かない(同席だけ・エンジンの規則では
  書かない)・文の長さは切らない(MR13)・印象に埋め込みの口(MR2 問い 3)。
- 浅い痕跡: 出来事の記録から「同じ場所の近い時刻に居た回」を組み立てる(保存しない)・言葉(注意を向けた記憶=空文字・
  浅い痕跡だけ=「見たような気もする」・何も無い=空文字)・計器「話を合わせた割合」。
- 話し手の指した相手の見えない欄 ``Percept.heard_referents``: 描画の作る知覚の事実では空(None)=描画は変わらない。
"""

from __future__ import annotations

import pytest

from shibuya.core.time_consts import NS_PER_STEP
from shibuya.engine import memory_trace as MT
from shibuya.engine.events.log import Event, EventLog, LlmCall, Process
from shibuya.engine.memory_impression import KIND_AFTER_TALK, KIND_SLEEP_REWRITE, ImpressionBook
from shibuya.perception import facts as F


def test_impressions_are_appended_and_rewritten_on_sleep():
    seen: list = []
    book = ImpressionBook(embed=lambda keys, texts: seen.append((tuple(keys), tuple(texts))))
    book.after_conversation(1, 2, "話しやすい人だった", 100, LlmCall("100:1:3"))
    book.after_conversation(1, 2, "店に詳しい", 200, LlmCall("200:1:3"))
    book.after_conversation(1, 3, "急いでいた", 210, LlmCall("210:1:3"))
    assert book.pending(1) == (2, 3) and book.current(1, 2) == "店に詳しい"
    calls = []

    def rewrite(agent, partner, hist):
        calls.append((agent, partner, len(hist)))
        return ("・".join(e.text for e in hist) + "(まとめ)" * 40, LlmCall(f"900:{agent}:9"))

    out = book.on_sleep(1, 900, rewrite)
    assert [e.kind for e in out] == [KIND_SLEEP_REWRITE] * 2 and calls == [(1, 2, 2), (1, 3, 1)]
    h = book.history(1, 2)
    assert [e.kind for e in h] == [KIND_AFTER_TALK, KIND_AFTER_TALK, KIND_SLEEP_REWRITE]  # 古い要約も残る
    assert book.current(1, 2).startswith("話しやすい人だった・店に詳しい") and len(book.current(1, 2)) > 128  # 切らない
    assert book.pending(1) == () and book.on_sleep(1, 1000, rewrite) == []  # 追記の無い相手は書き直さない
    assert len(seen) == 5  # 追記 3+書き直し 2 の埋め込み


def test_impressions_need_an_llm_call_cause():
    book = ImpressionBook()
    with pytest.raises(TypeError, match="LLM の呼び"):
        book.after_conversation(1, 2, "同席しただけ", 100, Process("resolve"))
    with pytest.raises(ValueError):
        book.after_conversation(1, 1, "自分", 100, LlmCall("1:1:1"))
    with pytest.raises(ValueError):
        book.after_conversation(1, 2, "  ", 100, LlmCall("1:1:1"))
    e = book.add_conclusion(1, "あの店は昼に混む", 300, LlmCall("300:1:2"))
    assert book.semantic(1) == (e,)
    with pytest.raises(AttributeError):
        book._hist = {}


def _log() -> EventLog:
    log = EventLog()
    for step, who, cell in ((10, 1, 5), (10, 2, 5), (11, 2, 5), (20, 1, 6), (20, 2, 7), (30, 3, 5)):
        log.begin_step(step * NS_PER_STEP)
        log.append(Event(t_ns=step * NS_PER_STEP, who=who, what="行為:移動", where=("cell", cell), how_much=0,
                         cause=Process("resolve")))
    return log


def test_shallow_trace_from_the_shared_log():
    log = _log()
    tr = MT.shallow_trace(log, 1, 2, t0_ns=0, t1_ns=100 * NS_PER_STEP)
    assert tr.seen == 2 and tr.places == (("cell", 5, 2),) and tr.first_ns == 10 * NS_PER_STEP
    assert MT.shallow_trace(log, 1, 3, t0_ns=0, t1_ns=100 * NS_PER_STEP).seen == 0  # 同じ場所だが時刻が遠い
    assert MT.shallow_trace(log, 1, 2, t0_ns=15 * NS_PER_STEP, t1_ns=100 * NS_PER_STEP).seen == 0  # 窓の外
    assert MT.shallow_trace(EventLog(), 1, 2, t0_ns=0, t1_ns=1).seen == 0
    assert MT.trace_word(False, tr) == "見たような気もする" and MT.trace_word(True, tr) == ""
    assert MT.trace_word(False, MT.TraceView(0, -1, -1, ())) == ""


def test_played_along_share_gauge():
    assert MT.played_along_share([]) is None
    assert MT.played_along_share([(True, True), (True, False)]) is None  # 覚えていた行だけ
    assert MT.played_along_share([(False, True), (False, False), (False, True), (True, True)]) == pytest.approx(2 / 3)


def test_hidden_referent_field_is_empty_and_versioned():
    assert "heard_referents" in F.EMPTY_FIELDS and F.percept_fields()[-1] == "heard_referents"
    assert F.PERCEPT_SCHEMA.endswith("/2")
