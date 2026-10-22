"""第 1 期 1-3 出来事の記録: ``what`` の語彙表は閉じている(表の外はエラー)・4 つの族の写しが元の表と同じ。

決定(口の約束 1-3〔空欄 1〕=親案・回答 10-13b §3): 行為 12 語+過程の名+お金の科目+物の出入り。
"""

from __future__ import annotations

import pytest

from shibuya.economy.accounts import ACCOUNT_NAMES
from shibuya.economy.goods import GOODS_CODE_NAMES
from shibuya.engine.events import log as EV
from shibuya.engine.events import vocab as V
from shibuya.engine.processes.runner import PROCESS_ORDER
from shibuya.llm.contract import ACTION_VOCAB_V3


def test_families_are_copies_of_their_sources():
    assert V.ACT_WORDS == tuple(ACTION_VOCAB_V3) and len(V.ACT_WORDS) == 12
    assert V.WORLD_PROCESSES == tuple(PROCESS_ORDER)  # engine.processes の名(写し)
    assert V.MONEY_WORDS == tuple(ACCOUNT_NAMES)      # economy の科目(engine は economy を import できない=写し)
    assert V.GOODS_WORDS == tuple(GOODS_CODE_NAMES)   # economy の物の出入り(写し)
    assert V.BOUNDARY_PROCESSES == ("day_close", "checkpoint")
    assert V.PROCESS_NAMES == V.WORLD_PROCESSES + V.BOUNDARY_PROCESSES


def test_vocab_size_and_uniqueness():
    # 1-5: 行為:許可のない行動・1-7: 道具:看板 を末尾に足した・〔第 1 期 1-8b〕行為:発話 をその後ろ(別の組)に足した・
    # 〔第 2 期 2-1〕金:引き出し・金:カード をその後ろ(別の組)に足した・〔第 3 期 3-3〕実験:改変・実験:届いた情報 をその後ろに足した
    # 〔第 2 期 2-3〕行為:会話の始まり・行為:会話の終わり・知覚:気づき(族 知覚)をその後ろ(別の組)に足した
    # 〔第 6 期 6-4 C1〕族 連絡の 15 語をその後ろに足した(2-3 までの 65 語のコードは動かない)
    # 〔第 6 期 6-2 カレンダー 2〕族 約束の 13 語をその後ろに足した(6-4 までの 80 語のコードは動かない)
    # 〔第 6 期 6-2 カレンダー 3〕族 勤務の 8 語をその後ろに足した(カレンダー 2 までの 93 語のコードは動かない)
    # 〔第 6 期 6-6 ② 第 1 部〕族 仕事の 4 語をその後ろに足した(カレンダー 3 までの 101 語のコードは動かない)
    assert len(V.VOCAB) == 12 + (18 + 2) + 15 + 8 + 1 + 1 + 1 + 2 + 2 + 3 + 15 + 13 + 8 + 4 == 105
    assert V.VOCAB[-4:] == tuple(f"仕事:{w}" for w in V.DUTY_WORDS)
    assert V.code_of("仕事:開けた") == 101 and V.code_of("仕事:捨てた") == 104
    assert V.VOCAB[-12:-4] == tuple(f"勤務:{w}" for w in V.WORK_WORDS)
    assert V.code_of("勤務:枠を決めた") == 93 and V.code_of("勤務:知らせ") == 100
    assert V.VOCAB[-25:-12] == tuple(f"約束:{w}" for w in V.PROMISE_WORDS)
    assert V.code_of("約束:誘った") == 80 and V.code_of("約束:知らせ") == 92
    assert V.VOCAB[-50:-40] == ("行為:許可のない行動", "道具:看板", "行為:発話", "金:引き出し", "金:カード", "実験:改変",
                                "実験:届いた情報", "行為:会話の始まり", "行為:会話の終わり", "知覚:気づき")
    assert V.VOCAB[-40:-25] == tuple(f"連絡:{w}" for w in V.CONTACT_WORDS)
    assert V.code_of("連絡:送った") == 65 and V.code_of("連絡:通話の終わり") == 79
    assert V.code_of("行為:会話の始まり") == 62 and V.code_of("知覚:気づき") == 64
    assert V.code_of("道具:看板") == 56 and V.code_of("行為:発話") == 57  # 1-7・1-8b の語のコードは動かない
    assert V.code_of("金:引き出し") == 58 and V.code_of("金:カード") == 59  # 2-1 の語のコードは動かない
    assert V.code_of("実験:改変") == 60 and V.code_of("実験:届いた情報") == 61
    assert len(set(V.VOCAB)) == len(V.VOCAB)
    assert all(w.split(":", 1)[0] in V.FAMILIES for w in V.VOCAB)
    # 族を付けた理由: 金と物に同じ語(域外仕入)がある
    assert "金:域外仕入" in V.VOCAB_CODES and "物:域外仕入" in V.VOCAB_CODES
    assert V.VOCAB_VERSION == "events-vocab/6-6-w1"  # 〔第 6 期 6-6 ② 第 1 部〕版を上げた(前 events-vocab/6-2-ca3=版の文字列は段の名)
    assert V.CAUSE_PROCESS_NAMES[-3] == "contact"  # 〔6-4 C1〕網の名(前の名の番号は動かない)
    assert V.CAUSE_PROCESS_NAMES[-2] == "calendar2"  # 〔6-2 カレンダー 2〕予定の道具の名
    assert V.CAUSE_PROCESS_NAMES[-1] == "calendar3"  # 〔6-2 カレンダー 3〕勤務の予定の道具の名は末尾


@pytest.mark.parametrize("what", [
    "移動",              # 族の無い語
    "行為:待機",         # 語彙 v3 で外した語
    "過程:決定",         # 表に無い過程
    "金:手数料",         # 表に無い科目
    "物:盗難",           # 表に無い物の出入り
    "物:",               # 空の語
    "",                  # 空
    None,                # 型が違う
])
def test_what_outside_the_table_is_an_error(what):
    with pytest.raises(ValueError, match="語彙表の外"):
        EV.Event(t_ns=0, who="engine", what=what, cause=EV.Process("rail"))  # type: ignore[arg-type]


def test_every_word_of_the_table_is_accepted():
    log = EV.EventLog()
    for w in V.VOCAB:
        log.append(EV.Event(t_ns=0, who="engine", what=w, cause=EV.Process("rail")))
    assert log.what_counts() == {w: 1 for w in V.VOCAB}


def test_word_helper_and_family():
    assert V.word("過程", "rail") == "過程:rail"
    assert V.family_of("金:賃金") == "金"
    with pytest.raises(ValueError):
        V.word("過程", "nonexistent")


def test_process_names_are_closed():
    for name in V.PROCESS_NAMES:
        assert EV.Process(name).name == name
    for bad in ("", "Rail", "rail_operation_static", "phase_c", "llm"):
        with pytest.raises(ValueError, match="過程の名"):
            EV.Process(bad)


def test_via_and_where_are_closed():
    assert V.VIA_WORDS == ("対面", "通話", "メッセージ", "グループ", "SNS", "無し")  # CT9 (b) の 5 つ+無し
    assert V.WHERE_KINDS == ("cell", "node", "poi")
    for via in V.VIA_WORDS:
        EV.Event(t_ns=0, who="engine", what="過程:rail", via=via, cause=EV.Process("rail"))
    with pytest.raises(ValueError):
        EV.Event(t_ns=0, who="engine", what="過程:rail", via="テレパシー", cause=EV.Process("rail"))
