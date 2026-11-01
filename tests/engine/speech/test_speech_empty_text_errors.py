"""第 1 期 1-8b 発話の口: 本文の無い発話はエラー(口の約束 1-8b の約束 (3)・受入の試験 ``test_speech_empty_text_errors``)。

- ``Utterance`` は本文が空・空白だけ・文字列でないと作れない(TM3 はモーラ数を入力にする)。前後の空白は落とす。
- 口の入口 ``say`` は ``Utterance`` しか受け取らない=本文の無い発話は口を通れない(出来事ログにも未読にも入らない)。
- 会話の番の答えの ひと言 が空か「なし」なら発話にしない(``speak_turn`` は数えるだけ=``silent``)。セッションの外の答え
  (被招待の返事など)も発話にしない(``no_session``)。
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.engine.events.log import EventLog
from shibuya.engine.speech import layer as SPL
from shibuya.engine.speech import port as P


@pytest.mark.parametrize("text", ["", " ", "　\n", None, 5])
def test_utterance_without_text_is_an_error(text):
    with pytest.raises(ValueError, match="本文の無い発話"):
        P.Utterance(speaker=1, t_ns=0, text=text, addressees=(2,))  # type: ignore[arg-type]


def test_text_is_stripped():
    assert P.Utterance(speaker=1, t_ns=0, text="  やあ ", addressees=(2,)).text == "やあ"


def _box(n: int = 8, conv=None):
    reg = SimpleNamespace(cell=np.arange(n, dtype=np.int64), talk_partner=np.full(n, -1, dtype=np.int64))
    return SimpleNamespace(soa=SimpleNamespace(agents=SimpleNamespace(registry=reg)),
                           cfg=SimpleNamespace(tick_seconds=60), layers=SimpleNamespace(conv=conv))


@pytest.mark.parametrize("comment", ["", "なし", "  ", None])
def test_silent_turns_do_not_reach_the_port(comment):
    log = EventLog()
    port = P.SpeechPort(events=log)
    session = SimpleNamespace(participants=[1, 2], session_id=0)
    got = SPL.speak_turn(_box(), port, 1, 10, session, comment, "", None, "10:1:0", -1)
    assert got is None and len(log) == 0 and port.inbox == {}
    assert port.meter["silent"] == 1 and port.meter["said"] == 0 and port.meter["turns"] == 1


def test_turns_outside_a_session_do_not_reach_the_port():
    """セッションも返事待ちの招待も無い番は口を通さない(``no_session``)。"""
    from shibuya.engine.conversation import ConversationManager

    log = EventLog()
    port = P.SpeechPort(events=log)
    assert SPL.speak_turn(_box(), port, 1, 10, None, "こんにちは", "", None, "10:1:0", -1) is None
    conv = ConversationManager(1)
    assert SPL.speak_turn(_box(conv=conv), port, 1, 10, None, "こんにちは", "", None, "10:1:0", -1) is None
    assert len(log) == 0 and port.meter["no_session"] == 2 and port.meter["said"] == 0


def test_an_invitee_reply_reaches_the_inviter():
    """親の判断 A2: 返事待ちの招待への返事(セッションはまだ無い)は招待した人に届く(``to_inviter``)。空の返事は数えるだけ。"""
    from shibuya.engine.conversation import ConversationManager

    conv = ConversationManager(1)
    assert conv.register_pending(3, 1, 9, 0, same_cell=True)
    log = EventLog()
    port = P.SpeechPort(events=log)
    assert SPL.speak_turn(_box(conv=conv), port, 1, 10, None, "なし", "", None, "10:1:0", -1) is None
    assert port.meter["silent"] == 1 and port.meter["to_inviter"] == 0
    eid = SPL.speak_turn(_box(conv=conv), port, 1, 10, None, "いいよ", "", None, "10:1:0", -1)
    assert eid is not None and log.get(eid).whom == 3 and port.meter["to_inviter"] == 1
    assert port.inbox == {3: [(eid, 1, "いいよ", 10 * 60 * 10**9, -1)]}


def test_a_real_turn_reaches_the_port_once():
    log = EventLog()
    port = P.SpeechPort(events=log)
    session = SimpleNamespace(participants=[1, 2], session_id=4)
    eid = SPL.speak_turn(_box(), port, 1, 10, session, "こんにちは", "", None, "10:1:0", -1)
    assert eid is not None and len(log) == 1 and port.meter["said"] == 1
    assert port.inbox == {2: [(eid, 1, "こんにちは", 10 * 60 * 10**9, 4)]}
