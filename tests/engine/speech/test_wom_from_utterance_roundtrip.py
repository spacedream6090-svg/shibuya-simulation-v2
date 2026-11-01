"""第 1 期 1-8b 発話の口: 口コミの抽出が語彙 v3 でも動く(口の約束 1-8b の (c)・受入の試験 ``test_wom_from_utterance_roundtrip``)。

仕分け §3-5: パーサと口コミの抽出(``wom_source=utterance``)は語彙 v3 でも ``comment`` を受け取る=欄が戻ればコードを変えずに
動く。ここで確かめる往復:

1. v3 の 5 ラベル形の 2 行目の最後に ``ひと言:`` を足した答え → パーサ(コードは 1-8b の前のまま)が ``comment`` を返す・
   5 ラベルの書式の判定(``format_ok``・``strict_format_ok``)は落ちない。
2. 今の道(腕 off の ``llm_io.utter``)でも、その ひと言 から店名と評価語が抽出され、宛先の店の行に伝聞で書かれる。
3. 腕 on の発話の口(``SpeechPort.say`` の (c))が同じ抽出と同じ行を書く(書く口は口の 1 つ=今の道の口コミの段は通らない)。
4. mock の決まった文(店名なし)は抽出 0。
"""

from __future__ import annotations

from types import SimpleNamespace

import numpy as np
import pytest

from shibuya.agents.state import AgentState
from shibuya.engine import memory as M
from shibuya.engine import store_memory as SM
from shibuya.engine import wom as W
from shibuya.engine.conversation import ConversationManager
from shibuya.engine.events.log import EventLog
from shibuya.engine.speech import layer as SPL
from shibuya.engine.systems import llm_io as IO
from shibuya.llm import parse_two_line
from shibuya.llm.contract import append_comment, format_two_line_v3
from shibuya.llm.mock import MOCK_UTTERANCE

NAMES = ["一蘭 渋谷店", "松屋", "ビーフキッチン渋谷店"]
CATS = ["food", "food", "food"]
CELLS = np.array([1, 1, 1])
DIST = (np.abs(np.arange(4)[:, None] - np.arange(4)[None, :]) * 100).astype(np.uint16)
ANSWER = append_comment(format_two_line_v3("店の話をしたいから", "会話", "P-2", "話す", "30分"), "松屋がおいしかった")


def _world(n: int = 3):
    a = AgentState(n, memory_columns=True, memory_n=32, store_memory_columns=True)
    with a.writable():
        a.cell[:] = 1
        a.talk_partner[0] = 2
    lay = M.MemoryLayer(n, 32, minutes_per_tick=1.0)
    lay.enable_store()
    conv = ConversationManager(1)
    s = conv.invite(0, 2, tick=5, cell=1, same_cell=True, partner_idle=True, answered=True)
    assert s is not None
    return a, lay, conv


def _box(a, lay, conv, wom, speech):
    return SimpleNamespace(
        soa=SimpleNamespace(agents=a),
        layers=SimpleNamespace(conv=conv, mem_layer=lay, wom=wom, speech=speech),
        cfg=SimpleNamespace(vocab_version="v3", store_wom_on=True, tick_seconds=60),
    )


def _rows(a, listener: int):
    poi = np.asarray(a.sm_poi[listener])
    j = np.flatnonzero(poi >= 0)
    return [(int(poi[k]), int(a.sm_source[listener, k]), float(a.sm_valence[listener, k])) for k in j]


def test_the_v3_parser_receives_the_comment_without_code_changes():
    p = parse_two_line(ANSWER, "v3")
    assert p.comment == "松屋がおいしかった" and p.raw_comment == "松屋がおいしかった"
    assert p.format_ok and p.strict_format_ok and p.action == "会話" and p.until.kind is not None
    assert p.activity == "話す" and p.target.raw == "P-2"
    # 3 行目に書いても読める(位置の欄ではなくラベルで読む)
    p3 = parse_two_line(format_two_line_v3("x", "会話", "P-2", "話す", "30分") + "\nひと言: 松屋がおいしかった", "v3")
    assert p3.comment == "松屋がおいしかった" and p3.format_ok


@pytest.mark.parametrize("arm", ["off", "on"])
def test_legacy_path_and_the_port_write_the_same_word_of_mouth(arm):
    a, lay, conv = _world()
    wom = W.WomExtractor(NAMES, CATS, CELLS, DIST)
    speech = None
    if arm == "on":
        speech = SPL.make_port(events=EventLog(), wom=wom, vocab_version="v3", agents=a, mem_layer=lay,
                               store_wom_on=True, step_seconds=60)
    p = parse_two_line(ANSWER, "v3")
    IO.utter(_box(a, lay, conv, wom, speech), 0, 6, p.action, p.comment, p.reason, p, call_id="6:0:0")
    assert _rows(a, 2) == [(1, SM.STORE_SOURCE_BIT["wom"], pytest.approx(0.25))]  # 宛先=会話の相手・松屋・+
    assert _rows(a, 0) == [] and _rows(a, 1) == []                                  # 話し手・第三者は書かない
    assert wom.stats["utterances"] == 1 and wom.stats["wom_extracted"] == 1 and wom.stats["wom_valence+1"] == 1
    if speech is not None:
        assert speech.meter["said"] == 1 and speech.meter["wom_passed"] == 1
        assert len(speech.events) == 1 and speech.inbox[2][0][2] == "松屋がおいしかった"


def test_the_mock_utterance_extracts_nothing():
    a, lay, conv = _world()
    wom = W.WomExtractor(NAMES, CATS, CELLS, DIST)
    speech = SPL.make_port(events=EventLog(), wom=wom, vocab_version="v3", agents=a, mem_layer=lay,
                           store_wom_on=True, step_seconds=60)
    text = append_comment(format_two_line_v3("x", "会話", "P-2", "話す", "30分"), MOCK_UTTERANCE)
    p = parse_two_line(text, "v3")
    IO.utter(_box(a, lay, conv, wom, speech), 0, 6, p.action, p.comment, p.reason, p, call_id="6:0:0")
    assert speech.meter["said"] == 1 and speech.meter["wom_passed"] == 1
    assert wom.stats["utterances"] == 1 and wom.stats.get("wom_extracted", 0) == 0 and _rows(a, 2) == []
