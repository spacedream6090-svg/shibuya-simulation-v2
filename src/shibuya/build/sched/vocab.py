"""build.sched.vocab — W17 週次活動表の**凍結語彙と行書式**(整形器・パーサ)。

設計の要点
- **出力は日見出し形**(第2回パイロット後・v3)。曜日の見出し行 `d0`〜`d6` と、
  その下の活動行 `<開始HHMM>-<終了HHMM> <活動語> <場所語>` の 3 列だけ。
  I1 予算(週7日フル生成 ≈2.3億 tok・DP7 12h)は 1 体あたり出力 ≤600 tok を要求するので、
  JSON も自然文も使わない(答申 Q4-3 の見積り 1,100 tok/体は W1 を 7 倍破る)。
  旧形式(1 行に曜日 `d0 0700-0830 支度 自宅`)も**互換で読める**。
- **活動語 12 + 場所語 12 の閉じた語彙**。活動語は行動契約書 §2.1 の「種別横断12語」へ
  **全語が写像できる**(``ACTIVITY_TO_ACTION``)= 契約書の「活動表の語はこれに写像できること」。
- パーサは**行単位で壊れを捨てる**。1 行が読めなくてもその活動だけ落とし、残りは使う。

expedient(本モジュール分・登録簿へ)
- 語彙表そのもの(活動語 12・場所語 12)と ``ACTIVITY_TO_ACTION`` の写像。先行研究なし
  (ActivitySim の CDAP は 3 値=mandatory/non-mandatory/home までしか与えない)。
- 行書式(4 列・空白区切り・HHMM)と許容する表記ゆれ(下記 ``parse_line`` の docstring)。
- 24 時越えの扱い(``end <= start`` は翌日へ分割)。
- 活動語 → 起床条件(計画境界クラス)の写像 ``ACTIVITY_TO_WAKE``。
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final, NamedTuple

__all__ = [
    "N_DAYS",
    "MINUTES_PER_DAY",
    "DAY_WORDS",
    "ACTIVITY_WORDS",
    "PLACE_WORDS",
    "ACTION_WORDS",
    "ACTIVITY_TO_ACTION",
    "ACTIVITY_TO_WAKE",
    "WAKE_PLAN_SLEEPING",
    "WAKE_PLAN_WORKING",
    "WAKE_PLAN_GENERAL",
    "WAKE_PLAN_TRANSIT",
    "ACT_SLEEP",
    "ACT_PREP",
    "ACT_MOVE",
    "ACT_RIDE",
    "ACT_WORK",
    "ACT_SCHOOL",
    "ACT_MEAL",
    "ACT_SHOP",
    "ACT_LEISURE",
    "ACT_ERRAND",
    "ACT_SOCIAL",
    "ACT_REST",
    "PLACE_HOME",
    "PLACE_WORK",
    "PLACE_SCHOOL",
    "PLACE_STATION",
    "PLACE_FOOD",
    "PLACE_SHOP",
    "PLACE_PARK",
    "PLACE_LEISURE",
    "PLACE_HOTEL",
    "PLACE_CLINIC",
    "PLACE_STREET",
    "PLACE_OUTSIDE",
    "ACTIVITY_SYNONYMS",
    "PLACE_SYNONYMS",
    "FAILURE_REASONS",
    "Act",
    "DAY_HEADER",
    "TIME_PATTERN",
    "format_line",
    "format_body",
    "format_schedule",
    "format_schedule_flat",
    "parse_line",
    "parse_text",
    "canonical_text",
]

#: 曜日数(週7日フル生成=決定台帳「母集団合成(追補)」)。
N_DAYS: Final[int] = 7
MINUTES_PER_DAY: Final[int] = 1_440

#: 曜日語(**d0=月曜**。W7 ``plan_spec`` の content の曜日順と同じ)。
DAY_WORDS: Final[tuple[str, ...]] = ("月曜", "火曜", "水曜", "木曜", "金曜", "土曜", "日曜")

# ---------------------------------------------------------------- 活動語(12・凍結)
#: 活動語。索引=``activity_code``(parquet 列)。**順序は凍結**(索引が意味を持つ)。
ACTIVITY_WORDS: Final[tuple[str, ...]] = (
    "就寝",  # 0
    "支度",  # 1
    "移動",  # 2
    "乗車",  # 3
    "勤務",  # 4
    "通学",  # 5
    "食事",  # 6
    "買物",  # 7
    "娯楽",  # 8
    "用事",  # 9
    "交流",  # 10
    "休憩",  # 11
)
ACT_SLEEP, ACT_PREP, ACT_MOVE, ACT_RIDE, ACT_WORK, ACT_SCHOOL = range(6)
ACT_MEAL, ACT_SHOP, ACT_LEISURE, ACT_ERRAND, ACT_SOCIAL, ACT_REST = range(6, 12)

# ---------------------------------------------------------------- 場所語(12・凍結)
#: 場所種別語。索引=``place_kind``(parquet 列)。**セル ID ではない**——答申 Q4-2
#: 「場所は『セルID』ではなく『場所種別』まで」+ D-W13「出口は経路の結果」。
PLACE_WORDS: Final[tuple[str, ...]] = (
    "自宅",  # 0
    "職場",  # 1
    "学校",  # 2
    "駅",  # 3
    "飲食店",  # 4
    "物販店",  # 5
    "公園",  # 6
    "娯楽施設",  # 7
    "宿泊施設",  # 8
    "医療施設",  # 9
    "路上",  # 10
    "域外",  # 11
)
PLACE_HOME, PLACE_WORK, PLACE_SCHOOL, PLACE_STATION = range(4)
PLACE_FOOD, PLACE_SHOP, PLACE_PARK, PLACE_LEISURE = range(4, 8)
PLACE_HOTEL, PLACE_CLINIC, PLACE_STREET, PLACE_OUTSIDE = range(8, 12)

# ---------------------------------------------------------------- 行動語彙への写像
#: 行動契約書 §2.1「種別横断12語」(**契約書の表そのまま**・写像先の検査に使う)。
ACTION_WORDS: Final[tuple[str, ...]] = (
    "移動", "乗車", "降車", "購入", "待機", "会話",
    "退去", "通報", "手伝い", "断る", "休憩", "就寝",
)

#: 活動語 → 行動語(行動契約書 §2.1)。活動表の語は**必ず**この表で行動語になる。
#: 「その計画境界で最初に試みる行動」であって、LLM が別の語を選ぶことは妨げない。
ACTIVITY_TO_ACTION: Final[dict[str, str]] = {
    "就寝": "就寝",
    "支度": "休憩",
    "移動": "移動",
    "乗車": "乗車",
    "勤務": "待機",  # 職務の中身(接客・補充など種別固有語)は境界で LLM が選ぶ
    "通学": "待機",
    "食事": "購入",
    "買物": "購入",
    "娯楽": "待機",
    "用事": "待機",
    "交流": "会話",
    "休憩": "休憩",
}

# 起床条件(知覚契約書 §6 不応期表・``agents.state.WakeCondition`` の値と一致させる。
# build は agents を import しないので**二重定義**・テストが一致を機械検査する)。
WAKE_PLAN_SLEEPING: Final[int] = 1
WAKE_PLAN_WORKING: Final[int] = 2
WAKE_PLAN_GENERAL: Final[int] = 3
WAKE_PLAN_TRANSIT: Final[int] = 4

#: 活動語コード → 起床条件(計画境界の 4 行)。
ACTIVITY_TO_WAKE: Final[tuple[int, ...]] = (
    WAKE_PLAN_SLEEPING,  # 就寝
    WAKE_PLAN_GENERAL,  # 支度
    WAKE_PLAN_TRANSIT,  # 移動
    WAKE_PLAN_TRANSIT,  # 乗車
    WAKE_PLAN_WORKING,  # 勤務
    WAKE_PLAN_WORKING,  # 通学
    WAKE_PLAN_GENERAL,  # 食事
    WAKE_PLAN_GENERAL,  # 買物
    WAKE_PLAN_GENERAL,  # 娯楽
    WAKE_PLAN_GENERAL,  # 用事
    WAKE_PLAN_GENERAL,  # 交流
    WAKE_PLAN_GENERAL,  # 休憩
)

_ACT_INDEX: Final[dict[str, int]] = {w: i for i, w in enumerate(ACTIVITY_WORDS)}
_PLACE_INDEX: Final[dict[str, int]] = {w: i for i, w in enumerate(PLACE_WORDS)}

# ---------------------------------------------------------------- 同義語(パイロット実測由来)
#: 語彙外の活動語 → 最近傍の活動語(**expedient**)。第1回パイロット(300 体・8B INT8・
#: 温度 0.7)で実際に出た語(学習 7・朝食 3)と、その周辺で出うる語を表にした。
#: **表に無い語は落とす**(勝手に既定語へ寄せない)。
ACTIVITY_SYNONYMS: Final[dict[str, str]] = {
    # 食事
    "朝食": "食事", "昼食": "食事", "夕食": "食事", "夜食": "食事", "外食": "食事",
    "昼休み": "食事", "食": "食事",
    # 用事(場所を問わない自習・家事の類)
    "学習": "用事", "勉強": "用事", "自習": "用事", "宿題": "用事", "読書": "用事",
    "家事": "用事", "掃除": "用事", "洗濯": "用事", "通院": "用事", "手続き": "用事",
    # 通学
    "授業": "通学", "登校": "通学", "部活": "通学", "部活動": "通学",
    # 移動
    "通勤": "移動", "出勤": "移動", "帰宅": "移動", "下校": "移動", "外出": "移動",
    "帰路": "移動", "徒歩": "移動",
    # 勤務
    "仕事": "勤務", "労働": "勤務", "業務": "勤務", "就業": "勤務", "接客": "勤務",
    # 支度
    "起床": "支度", "身支度": "支度", "準備": "支度", "朝支度": "支度", "就寝準備": "支度",
    # 買物
    "買い物": "買物", "ショッピング": "買物", "購入": "買物", "買い出し": "買物",
    # 娯楽
    "散歩": "娯楽", "運動": "娯楽", "遊び": "娯楽", "趣味": "娯楽", "観光": "娯楽",
    "鑑賞": "娯楽", "見物": "娯楽",
    # 休憩
    "入浴": "休憩", "風呂": "休憩", "休息": "休憩", "くつろぎ": "休憩", "在宅": "休憩",
    "自由時間": "休憩", "団らん": "休憩",
    # 就寝
    "睡眠": "就寝", "仮眠": "就寝", "昼寝": "就寝",
    # 乗車
    "電車": "乗車", "通勤電車": "乗車", "乗換": "乗車", "乗り換え": "乗車",
    # 交流
    "会話": "交流", "おしゃべり": "交流", "面会": "交流", "交際": "交流", "雑談": "交流",
}

#: 語彙外の場所語 → 最近傍の場所語(**expedient**)。パイロットで実際に出た語
#: (食事店 108・食物店 37・食事 25・高校 22・食事場 19・渋谷 19・家族 8・食品店 7・
#: 食べ物店 6・食堂 5)が大半。**1 文字の断片は入れない**(切れた末尾行の残骸なので落とす)。
PLACE_SYNONYMS: Final[dict[str, str]] = {
    # 飲食店
    "食事店": "飲食店", "食物店": "飲食店", "食事": "飲食店", "食事場": "飲食店",
    "食べ物店": "飲食店", "食堂": "飲食店", "レストラン": "飲食店", "カフェ": "飲食店",
    "喫茶店": "飲食店", "居酒屋": "飲食店", "飲食街": "飲食店",
    # 物販店
    "食品店": "物販店", "スーパー": "物販店", "コンビニ": "物販店", "商店": "物販店",
    "商業施設": "物販店", "百貨店": "物販店", "商店街": "物販店", "売り場": "物販店",
    # 学校
    "小学校": "学校", "中学校": "学校", "高校": "学校", "高等学校": "学校",
    "大学": "学校", "専門学校": "学校", "保育所": "学校", "幼稚園": "学校", "塾": "学校",
    # 自宅
    "家": "自宅", "自室": "自宅", "住宅": "自宅", "家族": "自宅", "自宅周辺": "自宅",
    # 職場
    "会社": "職場", "オフィス": "職場", "勤務先": "職場", "事務所": "職場", "店舗": "職場",
    # 駅
    "駅前": "駅", "ホーム": "駅", "改札": "駅",
    # 娯楽施設
    "映画館": "娯楽施設", "ジム": "娯楽施設", "劇場": "娯楽施設", "施設": "娯楽施設",
    # 医療施設
    "病院": "医療施設", "クリニック": "医療施設", "診療所": "医療施設",
    # 宿泊施設
    "ホテル": "宿泊施設", "宿": "宿泊施設", "旅館": "宿泊施設",
    # 公園・路上
    "公園内": "公園", "広場": "公園", "渋谷": "路上", "街": "路上", "屋外": "路上",
    "道": "路上", "街中": "路上",
    # 域外
    "外": "域外", "区外": "域外", "自宅外": "域外", "他地域": "域外", "郊外": "域外",
}

#: 「その活動を捨てた」理由(``parse_fail_rate`` の分子)。``fix_*`` は**直した**印なので入れない。
FAILURE_REASONS: Final[frozenset[str]] = frozenset(
    {"format", "bad_time", "unknown_activity", "unknown_place"}
)


class Act(NamedTuple):
    """活動 1 件(1 行)。``start``/``end`` は 0-1440 の分(``end`` は排他)。"""

    day: int
    start: int
    end: int
    activity: int
    place: int


# ---------------------------------------------------------------- 整形(骸格・テスト用)
def format_line(day: int, start: int, end: int, activity: int, place: int) -> str:
    """1 活動 → 1 行。``end==1440`` は ``2400`` と書く(24 時越えの分割点)。

    Example:
        >>> format_line(1, 420, 510, ACT_MOVE, PLACE_WORK)
        'd1 0700-0830 移動 職場'
    """
    return (
        f"d{int(day)} {int(start) // 60:02d}{int(start) % 60:02d}"
        f"-{int(end) // 60:02d}{int(end) % 60:02d} "
        f"{ACTIVITY_WORDS[int(activity)]} {PLACE_WORDS[int(place)]}"
    )


def format_body(start: int, end: int, activity: int, place: int) -> str:
    """1 活動 → **日見出し形**の活動行(曜日を持たない 3 列)。

    Example:
        >>> format_body(420, 510, ACT_MOVE, PLACE_WORK)
        '0700-0830 移動 職場'
    """
    return (
        f"{int(start) // 60:02d}{int(start) % 60:02d}"
        f"-{int(end) // 60:02d}{int(end) % 60:02d} "
        f"{ACTIVITY_WORDS[int(activity)]} {PLACE_WORDS[int(place)]}"
    )


def format_schedule(acts: list[Act]) -> str:
    """活動列 → 応答本文(**日見出し形**・7 日ぶんの見出しを必ず出す)。

    第2回パイロット(344 体)で 318/344 が ``max_tokens`` で切れたため、行から曜日欄を
    外して見出し行に畳んだ(``d0 0700-0830 支度 自宅`` の数字 8 桁は 1 桁 1 トークン)。

    Example:
        >>> print(format_schedule([Act(0, 420, 510, ACT_MOVE, PLACE_WORK)]).split(chr(10))[1])
        0700-0830 移動 職場
    """
    by_day: dict[int, list[Act]] = {}
    for a in acts:
        by_day.setdefault(int(a.day), []).append(a)
    out: list[str] = []
    for d in range(N_DAYS):
        out.append(f"d{d}")
        for a in sorted(by_day.get(d, []), key=lambda x: (x.start, x.end)):
            out.append(format_body(a.start, a.end, a.activity, a.place))
    return "\n".join(out)


def format_schedule_flat(acts: list[Act]) -> str:
    """活動列 → **旧形式**(1 行に曜日)。互換テスト用。"""
    return "\n".join(format_line(a.day, a.start, a.end, a.activity, a.place) for a in acts)


# ---------------------------------------------------------------- パース
_THINK = re.compile(r"<think>.*?</think>", re.DOTALL)
#: 行頭の箇条書き記号・番号(モデルが勝手に付ける分を落とす)。
_BULLET = re.compile(r"^[\s\-\*・•‐−―•]+|^\d+[.)]\s*")
#: 行末の空白・句読点・区切り記号(第1回パイロットで**全行**に「自宅␣␣」の二重空白が付いた)。
_TRAILING = re.compile(r"[\s。、．，.,;:|・*※\-–—_]+$")
#: 曜日の見出し行(**日見出し形**: ``d0`` だけの行。次の行から その日の活動)。
_DAY_HEADER_RE = re.compile(r"^d([0-6])$")
#: 見出し行の書式(構造化出力 regex の部品)。
DAY_HEADER: Final[str] = "d{day}"
#: 時刻 4 桁(00:00-24:59。構造化出力 regex の部品。パーサ側が h<=24・m<60 を再検査する)。
TIME_PATTERN: Final[str] = r"(?:[01][0-9]|2[0-4])[0-5][0-9]"
#: 活動行の中身(時刻2つ+活動語+場所語)。時刻は ``0700`` と ``7:00`` の両方、
#: 区切りは ``-``/``–``/``~``/``〜`` を許す。
_BODY = (
    r"(?P<h1>\d{1,2}):?(?P<m1>\d{2})\s*[-‐-―~〜～]\s*"
    r"(?P<h2>\d{1,2}):?(?P<m2>\d{2})\s+"
    r"(?P<act>\S+)\s+(?P<place>\S+)\s*$"
)
#: **日見出し形**の活動行(曜日は直前の見出しから引き継ぐ)。
_BODY_RE = re.compile(r"^" + _BODY)
#: **旧形式**(1 行に曜日を持つ ``d0 0700-0830 支度 自宅``)。互換のため読み続ける。
_LINE_RE = re.compile(r"^d(?P<day>[0-6])\s+" + _BODY)

#: 1 応答から取り込む活動の上限(暴走出力の打ち切り。7 日 × 8 = 56 + 24 時越え分割の余裕)。
MAX_ACTS_PER_RESPONSE: Final[int] = 80


def canonical_text(raw: str) -> str:
    """応答本文の正規化(NFKC・``<think>`` 除去・改行 LF・行頭記号落とし)。

    ``perception.normalize`` は使わない(W17 の出力は知覚ブロックの文面ではないので
    正規化規約 9 項の対象外=層契約の例外を作らない)。**この順序ごと凍結**。
    """
    text = _THINK.sub("", str(raw))
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for ln in text.split("\n"):
        ln = _TRAILING.sub("", _BULLET.sub("", ln)).strip()
        if ln:
            lines.append(re.sub(r"[ \t]+", " ", ln))
    return "\n".join(lines)


def parse_line(line: str, day: int | None = None) -> tuple[list[Act], str, tuple[str, ...]]:
    """1 行 → (活動 0-2 件, 不採用理由, 直した印)。理由が空文字なら採用。

    Args:
        line: 正規化済みの 1 行。
        day: **日見出し形**で直前の見出し(``d0`` の行)が与えた曜日。``None`` は見出しが
            まだ無い状態=旧形式(行頭に ``dN``)しか読めない。

    許容する表記ゆれ(**これ以外は不採用**): 行頭の箇条書き記号/番号・**行末の空白と
    句読点**・全角(NFKC で半角へ)・時刻のコロン(``7:00``)・区切りのダッシュ類/波ダッシュ・
    列間の連続空白・``ACTIVITY_SYNONYMS``/``PLACE_SYNONYMS`` に載る語彙外の語。

    **日をまたぐ行**(``end <= start``・例 ``d0 2300-0700 就寝 自宅``)は **2 件**に割る:
    ``(day, start, 1440)`` と ``((day+1) % 7, 0, end)``。``end == start`` は長さ 0 なので
    不採用(``bad_time``)。

    Returns:
        ``([Act, ...], "", 直した印)`` か ``([], 理由, ())``。理由は ``format``/``bad_time``/
        ``unknown_activity``/``unknown_place``、印は ``fix_activity``/``fix_place``。
    """
    m = _LINE_RE.match(line)
    if m is not None:  # 旧形式(行が曜日を持つ)
        day = int(m.group("day"))
    else:  # 日見出し形(曜日は直前の見出しから)
        if day is None:
            return [], "format", ()
        m = _BODY_RE.match(line)
        if m is None:
            return [], "format", ()
    h1, m1 = int(m.group("h1")), int(m.group("m1"))
    h2, m2 = int(m.group("h2")), int(m.group("m2"))
    if m1 >= 60 or m2 >= 60 or h1 > 24 or h2 > 24:
        return [], "bad_time", ()
    start, end = h1 * 60 + m1, h2 * 60 + m2
    if start >= MINUTES_PER_DAY:  # 0000 と 2400 は同義。開始が 2400 は不採用
        return [], "bad_time", ()
    notes: list[str] = []
    act = _ACT_INDEX.get(m.group("act"))
    if act is None:
        near = ACTIVITY_SYNONYMS.get(m.group("act"))
        if near is None:
            return [], "unknown_activity", ()
        act = _ACT_INDEX[near]
        notes.append("fix_activity")
    place = _PLACE_INDEX.get(m.group("place"))
    if place is None:
        near = PLACE_SYNONYMS.get(m.group("place"))
        if near is None:
            return [], "unknown_place", ()
        place = _PLACE_INDEX[near]
        notes.append("fix_place")
    fixed = tuple(notes)
    if end > start:
        return [Act(day, start, end, act, place)], "", fixed
    if end == start:
        return [], "bad_time", ()
    # 日をまたぐ: 当日の残りと翌日の頭に割る
    out = [Act(day, start, MINUTES_PER_DAY, act, place)]
    if end > 0:
        out.append(Act((day + 1) % N_DAYS, 0, end, act, place))
    return out, "", fixed


def parse_text(raw: str) -> tuple[list[Act], dict[str, int]]:
    """応答本文 → (活動列, 理由の計数)。**壊れた行はその活動だけ捨てる**。

    ``bad`` のキーのうち ``FAILURE_REASONS`` に入るものが「捨てた」、``fix_*`` は
    「同義語表で直した」= 失敗率(``parse_fail_rate``)には数えない。

    Example:
        >>> acts, bad = parse_text("d0 0000-0700 就寝 自宅\\nごめん、わかりません")
        >>> [a.activity for a in acts], bad
        ([0], {'format': 1})
    """
    acts: list[Act] = []
    bad: dict[str, int] = {}
    day: int | None = None
    for ln in canonical_text(raw).split("\n"):
        if not ln:
            continue
        head = _DAY_HEADER_RE.match(ln)
        if head is not None:  # 日見出し行: 以降の活動行の曜日を決める
            day = int(head.group(1))
            continue
        got, why, notes = parse_line(ln, day)
        if why:
            bad[why] = bad.get(why, 0) + 1
            continue
        for note in notes:  # 直した印(``FAILURE_REASONS`` に入れない=失敗率に数えない)
            bad[note] = bad.get(note, 0) + 1
        acts.extend(got)
        if len(acts) >= MAX_ACTS_PER_RESPONSE:
            bad["truncated"] = bad.get("truncated", 0) + 1
            break
    return acts, bad
