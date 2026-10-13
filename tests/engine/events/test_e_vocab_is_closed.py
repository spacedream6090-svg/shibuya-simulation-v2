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
    assert len(V.VOCAB) == 12 + (18 + 2) + 15 + 8 == 55
    assert len(set(V.VOCAB)) == len(V.VOCAB)
    assert all(w.split(":", 1)[0] in V.FAMILIES for w in V.VOCAB)
    # 族を付けた理由: 金と物に同じ語(域外仕入)がある
    assert "金:域外仕入" in V.VOCAB_CODES and "物:域外仕入" in V.VOCAB_CODES
    assert V.VOCAB_VERSION == "events-vocab/1-3"


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
