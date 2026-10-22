"""第 1 期 1-8b 発話の口: 口の型(口の約束 1-8b の「口」・受入の試験 ``test_speech_port_schema``)。

- ``Utterance``(凍結): 欄の名と並び・凍結と slots・本文から数えるモーラ数(init しない)・欄の検査(話し手・届け先・道具・
  目印の形)。``SpeechContext``(凍結)。``SpeechPort.say(ctx, utterance) -> EventId`` の 1 つの書く口(型の検査・目印は口が
  付ける・欄の付け替えと消去を許さない)。
- 1-3 の語彙表の末尾に ``行為:発話``・道具の語は 1-3 の ``VIA_WORDS``。
- 出力の欄の指示の文が llm と perception で同じ(層契約の二重定義)。manifest の ``speech_port`` の欄。
- 状態台帳の腕の行 ``S8``(behavior・required)・``S8M``(diag・discardable)=持ち主の居るランだけ ``arm_items`` に出る。
"""

from __future__ import annotations

import dataclasses
import inspect

import pytest

from shibuya.engine import state_ledger as SL
from shibuya.engine.events import vocab as V
from shibuya.engine.events.log import EventLog
from shibuya.engine.speech import layer as SPL
from shibuya.engine.speech import port as P
from shibuya.llm import contract as C
from shibuya.perception import renderer as R

FIELDS = ("speaker", "t_ns", "text", "addressees", "via", "mora", "event_id", "modality")


def _u(**kw):
    base = dict(speaker=3, t_ns=60 * 10**9, text="こんにちは", addressees=(5,))
    base.update(kw)
    return P.Utterance(**base)


# ---------------------------------------------------------------- Utterance
def test_utterance_fields_frozen_and_mora_from_the_text():
    assert tuple(f.name for f in dataclasses.fields(P.Utterance)) == FIELDS
    params = P.Utterance.__dataclass_params__
    assert params.frozen and hasattr(P.Utterance, "__slots__")
    u = _u()
    assert (u.speaker, u.t_ns, u.text, u.addressees, u.via, u.mora, u.event_id, u.modality) == (
        3, 60 * 10**9, "こんにちは", (5,), "対面", 5, None, None)
    with pytest.raises(dataclasses.FrozenInstanceError):
        u.text = "別"  # type: ignore[misc]
    with pytest.raises(TypeError):
        P.Utterance(speaker=3, t_ns=0, text="x", addressees=(5,), mora=9)  # mora は本文から数える(渡せない)
    # 書いた後の写し(目印つき)もモーラ数は本文から
    v = dataclasses.replace(u, event_id=(60 * 10**9, 0))
    assert v.event_id == (60 * 10**9, 0) and v.mora == 5


@pytest.mark.parametrize("kw,match", [
    (dict(speaker=-1), "speaker"),
    (dict(speaker=True), "speaker"),
    (dict(t_ns=-5), "t_ns"),
    (dict(addressees=()), "addressees"),
    (dict(addressees=(3,)), "話し手"),
    (dict(addressees=(5, 5)), "重ならず"),
    (dict(addressees=(-2,)), "addressees"),
    (dict(via="無し"), "via"),
    (dict(via="手紙"), "via"),
    (dict(event_id=(1, 2, 3)), "event_id"),
])
def test_utterance_rejects_bad_fields(kw, match):
    with pytest.raises(ValueError, match=match):
        _u(**kw)


def test_via_is_the_1_3_vocabulary_and_three_participants_are_allowed():
    for w in V.VIA_WORDS:
        if w != V.VIA_NONE:
            assert _u(via=w).via == w
    assert _u(addressees=[5, 9]).addressees == (5, 9)  # 3 人の会話=届け先 2 人(list も組に)
    assert P.VIA_FACE == "対面" and P.VIA_FACE in V.VIA_WORDS


@pytest.mark.parametrize("text,mora", [
    ("こんにちは", 5), ("きょう", 2), ("ちょっと", 3), ("コーヒー", 4), ("渋谷駅", 6), ("ABC1", 4), ("!?。…", 0),
    ("また後で", 5),  # 仮名 3 拍+漢字 1 字=2 拍(expedient の数え方)
])
def test_mora_count_is_the_declared_kana_approximation(text, mora):
    assert P.mora_count(text) == mora
    assert _u(text=text).mora == mora


# ---------------------------------------------------------------- SpeechContext・SpeechPort
def test_context_and_the_one_writing_port():
    ctx = P.SpeechContext(step=1, call_id="1:3:0", cell=4, input_event_ids=[(1, 2)])
    assert ctx.input_event_ids == ((1, 2),)
    with pytest.raises(ValueError, match="call_id"):
        P.SpeechContext(step=1, call_id=" ")
    with pytest.raises(ValueError, match="step"):
        P.SpeechContext(step=-1, call_id="x")
    sig = inspect.signature(P.SpeechPort.say)
    assert list(sig.parameters) == ["self", "ctx", "utterance"]
    port = P.SpeechPort(events=EventLog())
    with pytest.raises(TypeError):
        port.say(ctx, "こんにちは")  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        port.say({"step": 1}, _u())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="口が付ける"):
        port.say(ctx, _u(event_id=(0, 0)))
    eid = port.say(ctx, _u())
    assert isinstance(eid, tuple) and len(eid) == 2
    # 書く口は say・take_heard だけ(欄の付け替えと消去は落ちる)
    with pytest.raises(AttributeError):
        port.inbox = {}
    with pytest.raises(AttributeError):
        del port.meter
    with pytest.raises(AttributeError):
        port.events = None


def test_the_word_is_appended_to_the_1_3_vocabulary():
    # 〔第 2 期 2-1〕発話の後ろに金の 2 語(別の組)を足した=発話は末尾でなくなった(コード 57 は動かない)
    assert P.WHAT == "行為:発話" and V.VOCAB[57] == P.WHAT and V.code_of(P.WHAT) == 57
    # 1-5 の「行為:許可のない行動」=55・1-7 の「道具:看板」=56 のコードは動かない(発話は 1-7 の組の後ろの別の組)
    assert V.VOCAB[55:58] == ("行為:許可のない行動", "道具:看板", "行為:発話") and V.SPEECH_WORDS == ("発話",)
    assert V.VOCAB[58:60] == ("金:引き出し", "金:カード")  # 2-1(その後ろに 3-3 の実験の族の 2 語)
    assert V.VOCAB[62:65] == ("行為:会話の始まり", "行為:会話の終わり", "知覚:気づき")  # 〔第 2 期 2-3〕体の出来事の 3 語(3-3 の後ろ・〔6-4 C1〕その後ろに連絡の族)
    assert "発話" not in V.ACT_WORDS  # 判断の語彙(v3 の 12 語)の外
    assert V.VOCAB_VERSION == "events-vocab/6-6-w1"  # 〔第 6 期 6-4 C1〕連絡の族の 15 語を表の末尾に足して版を上げた(前 events-vocab/2-3・前の語のコードは動かない)・〔第 6 期 6-2 カレンダー 2〕約束の族の 13 語をその後ろに足して版を上げた(前 events-vocab/6-4)・〔第 6 期 6-2 カレンダー 3〕勤務の族の 8 語をその後ろに足して版を上げた(前 events-vocab/6-2-ca2)・〔第 6 期 6-6 ② 第 1 部〕仕事の族の 4 語をその後ろに足して版を上げた(前 events-vocab/6-2-ca3)


def test_the_field_line_is_the_same_text_in_llm_and_perception():
    assert C.SPEECH_FIELD_LINE == R.SPEECH_FIELD_LINE
    # 欄の書き方は v1 の出力規約の ひと言 の意味の短い形(20 字以内・または なし=中身を誘導しない=Q57・根拠の札を書かせない
    # =MR11)・10 tok(親の判断=B6 の枠)
    assert C.SPEECH_FIELD_LINE == "2行目末尾に ひと言:<20字内|なし>"
    assert all(w not in C.SPEECH_FIELD_LINE for w in ("根拠", "理由", "記憶", "出来事", "番号"))
    assert C.append_comment("理由: a\n行動: なし 対象: なし 活動: 休む まで: 30分", "やあ").endswith(" ひと言: やあ")


def test_manifest_fields_shape():
    off = SPL.manifest_fields(None)
    assert list(off) == list(SPL.CONFIG_KEYS + SPL.OBSERVED_KEYS)
    assert off["arm"] == "off" and off["port"] is None and all(off[k] is None for k in SPL.OBSERVED_KEYS)
    assert (off["schema"], off["reach"], off["via"], off["field_line"]) == (
        P.SPEECH_SCHEMA, "session", "対面", C.SPEECH_FIELD_LINE)
    port = P.SpeechPort()
    on = SPL.manifest_fields(port)
    assert list(on) == list(SPL.CONFIG_KEYS + SPL.OBSERVED_KEYS)
    assert on["arm"] == "on" and on["port"] == "speech" and on["said"] == 0 and on["pending"] == 0


def test_arm_is_off_by_default_and_checked():
    assert SPL.ARMS == ("off", "on")
    with pytest.raises(ValueError):
        SPL.set_arm("yes")


# ---------------------------------------------------------------- 状態台帳の腕の行
def test_ledger_arm_rows_and_arm_items():
    s8, s8m = SL.row("S8"), SL.row("S8M")
    assert (s8.behavior, s8.restore, s8.items, s8.arm, s8.arm_owner) == (
        SL.BEHAVIOR, SL.REQUIRED, ("speech.inbox",), "speech-port", "speech")
    assert (s8m.behavior, s8m.restore) == (SL.DIAG, SL.DISCARDABLE)
    # 〔1-3 の (1) の直し〕口の目印 → 記録の id の診断の表と口の通し番号の控え(diag・required)
    s8e = SL.row("S8E")
    assert (s8e.behavior, s8e.restore, s8e.items, s8e.arm) == (
        SL.DIAG, SL.REQUIRED, ("speech._mark_event_of",), "speech-port")
    # 〔第 2 期 2-3〕M0L・〔第 6 期 6-5〕M0M・M0C・〔検収 M4〕M0S・〔第 6 期 6-2〕カレンダー 1b の C1B・C1BM(腕 calendar)
    # 〔第 6 期 6-3〕その後に時計の段 T2〜T4 の腕の行 TCR・TCC・T3M・T4W
    assert [r.key for r in SL.arm_rows()] == ["S8", "S8M", "S8E", "M0L", "M0M", "M0C", "M0S", "C1B", "C1BM",
                                             "TCR", "TCC", "T3M", "T4W", "CT1D", "CT1A", "CT1AS", "CT1I", "CT1IS", "CT1C", "CT1K", "CT1S", "CT1M", "CT1G", "CT1Q",  # 〔第 6 期 6-4 C1〕
                                             "CA2B", "CA2O", "CA2G", "CA2M", "CA2Q",  # 〔第 6 期 6-2 カレンダー 2〕
                                             "TXD",  # 〔第 4 期 4-2〕店の預かり消費税(腕 rules-42)
                                             "CA3S", "CA3P", "CA3G", "CA3M", "CA3Q",  # 〔第 6 期 6-2 カレンダー 3〕
                                             "DUS", "DUG", "DUM", "DUQ"]  # 〔第 6 期 6-6 ② 第 1 部〕
    assert [(SL.row(k).arm, SL.row(k).arm_owner) for k in ("C1B", "C1BM")] == [
        ("calendar", "calendar_self"), ("calendar", "calendar_self")]
    # 腕の行は静的な表に入らない(既定の 2 つのハッシュと状態のファイルは前と同じ道筋)
    assert all(k not in ("S8", "S8M", "S8E") for k, _ in SL.behavior_items() + SL.full_items())
    assert SL.arm_items({"speech": None}, behavior=True) == () == SL.arm_items({}, behavior=False)
    port = P.SpeechPort()
    assert SL.arm_items({"speech": port}, behavior=True) == (("S8", "speech.inbox"),)
    assert SL.arm_items({"speech": port}, behavior=False) == (("S8", "speech.inbox"), ("S8E", "speech._mark_event_of"))
    assert SL.OWNER_CLASSES["speech"] == ("engine/speech/port.py", "SpeechPort")
    # 検収 低7: 持ち主の腕の名(LEDGER_ARM)を行の arm と照合する=別の腕の物を同じ根の名に挿すと落ちる
    assert P.SpeechPort.LEDGER_ARM == s8.arm

    class Other:
        LEDGER_ARM = "decision-port"

    with pytest.raises(ValueError, match="腕"):
        SL.arm_items({"speech": Other()}, behavior=True)
    with pytest.raises(ValueError, match="腕"):
        SL.arm_items({"speech": object()}, behavior=False)
