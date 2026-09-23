"""W17 行パーサ: 陽性/陰性・24 時越え・語彙外・壊れた行の落とし方(hypothesis 込み)。"""

from __future__ import annotations

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.build.sched import vocab as V


# ---------------------------------------------------------------- 陽性
@pytest.mark.parametrize(
    "line,expected",
    [
        ("d1 0700-0830 移動 職場", V.Act(1, 420, 510, V.ACT_MOVE, V.PLACE_WORK)),
        ("d0 0000-0700 就寝 自宅", V.Act(0, 0, 420, V.ACT_SLEEP, V.PLACE_HOME)),
        ("d6 2300-2400 休憩 自宅", V.Act(6, 1_380, 1_440, V.ACT_REST, V.PLACE_HOME)),
        # 表記ゆれ: 全角・コロン・ダッシュ・箇条書き・連続空白
        ("- d2 7:00-8:30  買物  物販店", V.Act(2, 420, 510, V.ACT_SHOP, V.PLACE_SHOP)),
        ("ｄ３ ０９００－１０００ 勤務 職場", V.Act(3, 540, 600, V.ACT_WORK, V.PLACE_WORK)),
        ("d4 1200〜1300 食事 飲食店", V.Act(4, 720, 780, V.ACT_MEAL, V.PLACE_FOOD)),
    ],
)
def test_parse_line_positive(line: str, expected: V.Act):
    acts, why, notes = V.parse_line(V.canonical_text(line))
    assert why == ""
    assert acts == [expected]
    assert notes == ()


# ---------------------------------------------------------------- 陰性
@pytest.mark.parametrize(
    "line,reason",
    [
        ("すみません、作れません。", "format"),
        ("d7 0700-0830 移動 職場", "format"),  # 曜日が範囲外
        ("d1 0700-0830 移動", "format"),  # 列が足りない
        ("d1 0770-0830 移動 職場", "bad_time"),  # 分が 60 以上
        ("d1 0700-0700 移動 職場", "bad_time"),  # 長さ 0
        ("d1 0700-0830 瞑想 職場", "unknown_activity"),  # 語彙外(同義語表にも無い)
        ("d1 0700-0830 移動 温泉宿泊所", "unknown_place"),  # 語彙外(同義語表にも無い)
        ("| d1 | 0700-0830 | 移動 | 職場 |", "format"),  # 表組み
    ],
)
def test_parse_line_negative(line: str, reason: str):
    acts, why, _ = V.parse_line(V.canonical_text(line))
    assert acts == []
    assert why == reason
    assert reason in V.FAILURE_REASONS


# ---------------------------------------------------------------- 24 時越え
def test_cross_midnight_is_split():
    acts, why, _ = V.parse_line("d6 2300-0600 就寝 自宅")
    assert why == ""
    assert acts == [
        V.Act(6, 1_380, 1_440, V.ACT_SLEEP, V.PLACE_HOME),
        V.Act(0, 0, 360, V.ACT_SLEEP, V.PLACE_HOME),  # d6 の翌日は d0(週は環)
    ]


def test_cross_midnight_to_2400_is_not_split():
    acts, _, _ = V.parse_line("d0 2300-2400 就寝 自宅")
    assert len(acts) == 1 and acts[0].end == 1_440


# ---------------------------------------------------------------- 全体
def test_parse_text_drops_only_broken_lines():
    text = "\n".join(
        [
            "以下が活動表です。",
            "d0 0000-0700 就寝 自宅",
            "d0 0700-0800 支度 自宅",
            "d0 0800-0900 瞑想 職場",  # 語彙外(同義語表にも無い)→ この行だけ捨てる
            "d0 0900-1800 勤務 職場",
            "",
        ]
    )
    acts, bad = V.parse_text(text)
    assert [a.activity for a in acts] == [V.ACT_SLEEP, V.ACT_PREP, V.ACT_WORK]
    assert bad == {"format": 1, "unknown_activity": 1}


def test_parse_text_strips_think_block():
    acts, bad = V.parse_text("<think>まず考える</think>\nd0 0000-0700 就寝 自宅")
    assert len(acts) == 1 and bad == {}


def test_parse_text_truncates_runaway_output():
    text = "\n".join("d0 0000-0100 休憩 自宅" for _ in range(500))
    acts, bad = V.parse_text(text)
    assert len(acts) == V.MAX_ACTS_PER_RESPONSE
    assert bad.get("truncated") == 1


# ---------------------------------------------------------------- 往復(hypothesis)
@settings(max_examples=300, deadline=None)
@given(
    day=st.integers(min_value=0, max_value=6),
    start=st.integers(min_value=0, max_value=1_438),
    length=st.integers(min_value=1, max_value=1_440),
    act=st.integers(min_value=0, max_value=11),
    place=st.integers(min_value=0, max_value=11),
)
def test_format_parse_roundtrip(day: int, start: int, length: int, act: int, place: int):
    """``format_line`` が書いた行は必ず読め、同じ活動に戻る(24 時越えは分割される)。"""
    end = min(V.MINUTES_PER_DAY, start + length)
    line = V.format_line(day, start, end, act, place)
    acts, why, _ = V.parse_line(line)
    assert why == ""
    assert acts[0] == V.Act(day, start, end, act, place)
    assert len(acts) == 1


# ---------------------------------------------------------------- 頑健化(パイロット由来)
@pytest.mark.parametrize(
    "line",
    [
        "d1 0700-0830 移動 職場  ",       # 行末の二重空白(パイロットの全行)
        "d1 0700-0830 移動 職場。",       # 行末の句点
        "d1 0700-0830 移動 職場" + chr(0x3000),  # 行末の全角空白
        "d1 0700-0830 移動 職場 |",       # 行末の区切り記号
    ],
)
def test_trailing_noise_is_stripped(line: str):
    acts, why, _ = V.parse_line(V.canonical_text(line))
    assert why == ""
    assert acts == [V.Act(1, 420, 510, V.ACT_MOVE, V.PLACE_WORK)]


@pytest.mark.parametrize(
    "word,expected",
    [("朝食", V.ACT_MEAL), ("学習", V.ACT_ERRAND), ("授業", V.ACT_SCHOOL),
     ("買い物", V.ACT_SHOP), ("仕事", V.ACT_WORK), ("散歩", V.ACT_LEISURE)],
)
def test_activity_synonyms_are_mapped(word: str, expected: int):
    acts, why, notes = V.parse_line(f"d0 0700-0800 {word} 自宅")
    assert why == "" and acts[0].activity == expected
    assert notes == ("fix_activity",)


@pytest.mark.parametrize(
    "word,expected",
    [("食事店", V.PLACE_FOOD), ("食物店", V.PLACE_FOOD), ("食堂", V.PLACE_FOOD),
     ("高校", V.PLACE_SCHOOL), ("渋谷", V.PLACE_STREET), ("家族", V.PLACE_HOME),
     ("会社", V.PLACE_WORK), ("コンビニ", V.PLACE_SHOP)],
)
def test_place_synonyms_are_mapped(word: str, expected: int):
    acts, why, notes = V.parse_line(f"d0 0700-0800 食事 {word}")
    assert why == "" and acts[0].place == expected
    assert notes == ("fix_place",)


def test_unmapped_words_are_still_dropped():
    """表に無い語は**寄せない**(勝手な既定語に落とさない)。1 文字の断片も落とす。"""
    for line in ("d0 0700-0800 瞑想 自宅", "d0 0700-0800 食事 自", "d0 0700-0800 食事 職"):
        acts, why, _ = V.parse_line(line)
        assert acts == [] and why in V.FAILURE_REASONS


def test_synonym_fixes_are_not_counted_as_failures():
    acts, bad = V.parse_text("d0 0700-0800 朝食 食事店" + chr(10) + "d0 0800-0900 学習 自宅")
    assert len(acts) == 2
    assert bad == {"fix_activity": 2, "fix_place": 1}
    assert not (set(bad) & V.FAILURE_REASONS)


def test_one_line_sleep_across_midnight_is_the_new_form():
    """短縮形式: 日をまたぐ就寝は 1 行(2 行に割らせない)。"""
    acts, bad = V.parse_text("d0 2300-0700 就寝 自宅")
    assert bad == {}
    assert acts == [
        V.Act(0, 1_380, 1_440, V.ACT_SLEEP, V.PLACE_HOME),
        V.Act(1, 0, 420, V.ACT_SLEEP, V.PLACE_HOME),
    ]


# ---------------------------------------------------------------- 日見出し形(v3)
def test_day_heading_form_is_parsed():
    """v3 の書式: 見出し行 ``dN`` の下の活動行に、その曜日が付く。"""
    text = "\n".join(["d0", "0000-0700 就寝 自宅", "0700-0800 支度 自宅",
                      "d1", "0900-1800 勤務 職場"])
    acts, bad = V.parse_text(text)
    assert bad == {}
    assert [(a.day, a.start, a.activity) for a in acts] == [
        (0, 0, V.ACT_SLEEP), (0, 420, V.ACT_PREP), (1, 540, V.ACT_WORK)
    ]


def test_empty_day_heading_yields_no_activity():
    """来街者の来訪日でない曜日=見出しだけ。"""
    acts, bad = V.parse_text("\n".join(["d0", "d1", "d2", "0600-0630 乗車 駅",
                                        "d3", "d4", "d5", "d6"]))
    assert bad == {} and len(acts) == 1 and acts[0].day == 2


def test_body_line_without_a_heading_is_dropped():
    """見出しの前に来た活動行は曜日が決まらないので捨てる。"""
    acts, bad = V.parse_text("0700-0800 支度 自宅\nd0\n0800-0900 移動 職場")
    assert len(acts) == 1 and acts[0].day == 0
    assert bad == {"format": 1}


def test_old_flat_form_is_still_read():
    """旧形式(1 行に曜日)も互換で読める。"""
    acts, bad = V.parse_text("d3 0900-1800 勤務 職場")
    assert bad == {} and acts == [V.Act(3, 540, 1_080, V.ACT_WORK, V.PLACE_WORK)]


def test_mixed_forms_are_read():
    """見出し形と旧形式が混ざっても、旧形式は自分の曜日を優先する。"""
    acts, _ = V.parse_text("d0\n0700-0800 支度 自宅\nd5 0900-1000 娯楽 公園")
    assert [(a.day, a.activity) for a in acts] == [(0, V.ACT_PREP), (5, V.ACT_LEISURE)]


def test_cross_midnight_in_heading_form():
    acts, bad = V.parse_text("d6\n2300-0700 就寝 自宅")
    assert bad == {}
    assert acts == [V.Act(6, 1_380, 1_440, V.ACT_SLEEP, V.PLACE_HOME),
                    V.Act(0, 0, 420, V.ACT_SLEEP, V.PLACE_HOME)]


def test_format_schedule_emits_seven_headings():
    text = V.format_schedule([V.Act(2, 420, 510, V.ACT_MOVE, V.PLACE_WORK)])
    lines = text.split("\n")
    assert [ln for ln in lines if V._DAY_HEADER_RE.match(ln)] == [f"d{d}" for d in range(7)]
    assert "0700-0830 移動 職場" in lines
    assert all(not ln.endswith(" ") for ln in lines)  # 行末に空白を置かない


def test_format_schedule_roundtrips_through_the_parser():
    acts = [V.Act(d, 60 * j, 60 * j + 30, V.ACT_REST, V.PLACE_HOME)
            for d in range(7) for j in range(4)]
    back, bad = V.parse_text(V.format_schedule(acts))
    assert bad == {} and back == acts


def test_format_body_has_three_columns():
    assert V.format_body(420, 510, V.ACT_MOVE, V.PLACE_WORK) == "0700-0830 移動 職場"
    assert len(V.format_body(0, 60, V.ACT_SLEEP, V.PLACE_HOME).split(" ")) == 3
