"""foundation.text.percept_words — 割る段で ``perception/renderer.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``world/model/percept_scene.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final, Sequence
from shibuya.foundation.vocab.agent_codes import INTERO_UP_EDGES
from shibuya.foundation.text import channels as ch
from shibuya.foundation.text import normalize as N
from shibuya.foundation.text import templates as T
from shibuya.foundation.ports.percept import SeenPerson
from shibuya.foundation.time_consts import HOURS_PER_DAY, MINUTES_PER_HOUR

__all__ = [
    "ACTIVITY_WORDS_V3", "ACTIVITY_LINE", "ACTIVITY_LINE_MAX_TOKENS", "activity_line", "INTENT_LINE",
    "INTENT_LINE_MAX_TOKENS", "INTENT_FALLBACK_TARGET", "intent_line", "NAMED_CLOSED_NOTE",
    "NAMED_CLOSED_NOTE_MAX_TOKENS", "named_closed_note", "person_word", "near_person_text", "ACTIVITY_WORDS",
]


def _hunger_word(value: int, min_stage: int | None = None) -> str | None:
    """空腹の写し(1/5/8/10)→ B5 の語の 1 文(5 段目 5a)。段が ``min_stage``(既定
    ``HUNGER_WORD_DRAW_MIN_STAGE``)未満なら ``None``(描かない)。段=``INTERO_UP_EDGES`` を何本越えたか。
    ``min_stage=0``(``hunger_words="all"``)は 4 段とも描く。"""
    stage = sum(1 for e in INTERO_UP_EDGES if int(value) >= e)
    if stage < (T.HUNGER_WORD_DRAW_MIN_STAGE if min_stage is None else int(min_stage)):
        return None
    return T.HUNGER_ITEM_TEMPLATE.format(word=T.HUNGER_WORDS[stage])

#: ``Activity`` → 日本語(B5 直近の行動・B6 直前の結果)。
ACTIVITY_WORDS: Final[tuple[str, ...]] = (
    "待機", "移動", "待機", "休憩", "就寝", "購入", "会話", "乗車",
)
#: 同(語彙 v3=待機/休憩 → なし の機械的な読み替え・二層の段 2)。
ACTIVITY_WORDS_V3: Final[tuple[str, ...]] = tuple(
    "なし" if w in ("待機", "休憩", "降車") else w for w in ACTIVITY_WORDS
)
#: 同セルの活動の 1 行(B4b・**テンプレ本体ではない**=``template_sha256`` は不変・二層の段 2)。
#: 同セルの**全員**の活動文で作る=同セルの 2 体でバイト一致(規約⑧)。
ACTIVITY_LINE: Final[str] = "[B4b 活動] 近くの人: {items}。"
#: 1 行の上限[tok](アジェンダ §2「1 行 ≤ 15 tok」)。
ACTIVITY_LINE_MAX_TOKENS: Final[int] = 15
#: 項目の区切り(アジェンダ §2 の文面「…が<人数>人・…」)。
ACTIVITY_ITEM_SEPARATOR: Final[str] = "・"


#: 段 2c: 意図の 1 行(B5・**テンプレ本体ではない**=``template_sha256`` は不変・アジェンダ §3-2
#: 「いま <行為> のため <対象> へ向かっている」・文面は自前=expedient)。意図を持つ体だけに出る
#: (=その体の prompt_hash だけが動く)。
INTENT_LINE: Final[str] = "[B5 意図] いま{action}のため{target}へ向かっている。"
#: 1 行の上限[tok](アジェンダ §3-2「≤ 15 tok」)。対象の名を末尾から切り詰めて収める。
INTENT_LINE_MAX_TOKENS: Final[int] = 15
#: 対象の名に省略記法の語(⑥)が入っているときの代わりの語(宣言・expedient)。
INTENT_FALLBACK_TARGET: Final[str] = "目的の場所"


def intent_line(action_word: str, target: str) -> str:
    """意図の 1 行(``INTENT_LINE_MAX_TOKENS`` に収まるよう対象の名を末尾から切り詰める)。"""
    t = N.canonical_whitespace(str(target)).strip() or INTENT_FALLBACK_TARGET
    if any(a in t for a in N.ABBREVIATIONS):
        t = INTENT_FALLBACK_TARGET
    line = INTENT_LINE.format(action=action_word, target=t)
    while ch.estimate_tokens(line) > INTENT_LINE_MAX_TOKENS and len(t) > 1:
        t = t[:-1]
        line = INTENT_LINE.format(action=action_word, target=t)
    return line


#: 段 2c Q25: 名指しの店が見えるが閉店で歩かずに失敗した体の B6「直前の結果」の補足の 1 句
#: (``RESULT_TEXT`` の短句「営業時間外」は変えない・テンプレ本体ではない=``template_sha256`` 不変)。
NAMED_CLOSED_NOTE: Final[str] = "({name}は閉店中{opens})"
#: 同(開店の時刻=W7 の当日/翌日の最初の開店・無ければ付けない)。
NAMED_CLOSED_OPENS: Final[str] = "・{hhmm}に開く"
#: 補足の 1 句の上限[tok](≤ 15 tok・B6 枠 80 の内)。店名を末尾から切り詰めて収める。
NAMED_CLOSED_NOTE_MAX_TOKENS: Final[int] = 15
#: 店名に省略記法の語が入っているときの代わりの語(宣言・expedient)。
NAMED_CLOSED_FALLBACK_NAME: Final[str] = "その店"


def named_closed_note(name: str, open_minute: int = -1) -> str:
    """Q25 の補足の 1 句(店名 + 閉店中 + あれば「HH:MM に開く」・≤ 15 tok)。"""
    n = N.canonical_whitespace(str(name)).strip() or NAMED_CLOSED_FALLBACK_NAME
    if any(a in n for a in N.ABBREVIATIONS):
        n = NAMED_CLOSED_FALLBACK_NAME
    m = int(open_minute)
    opens = (
        NAMED_CLOSED_OPENS.format(hhmm=f"{(m // MINUTES_PER_HOUR) % HOURS_PER_DAY:02d}:{m % MINUTES_PER_HOUR:02d}") if m >= 0 else ""
    )
    line = NAMED_CLOSED_NOTE.format(name=n, opens=opens)
    while ch.estimate_tokens(line) > NAMED_CLOSED_NOTE_MAX_TOKENS and len(n) > 1:
        n = n[:-1]
        line = NAMED_CLOSED_NOTE.format(name=n, opens=opens)
    return line


def activity_line(rows: Sequence[tuple[str, int]]) -> str:
    """活動の (文, 人数) の列(人数降順→文字列順・上位 2)→ B4b の 1 行(無ければ ``""``)。

    ``ACTIVITY_LINE_MAX_TOKENS`` に収まる分だけ項目を載せる。先頭の項目だけでも収まらなければ
    文を末尾から切り詰める(expedient)。省略記法・個体依存語を含む文は載せない(⑥⑧)。
    """
    items: list[str] = []
    for text, count in rows:
        t = N.canonical_whitespace(str(text)).strip()
        if not t or any(a in t for a in N.ABBREVIATIONS):
            continue
        if any(p.search(t) for _, p in N.AGENT_DEPENDENT_PATTERNS):
            continue
        item = f"{t}が{int(count)}人"
        cand = items + [item]
        line = ACTIVITY_LINE.format(items=ACTIVITY_ITEM_SEPARATOR.join(cand))
        if ch.estimate_tokens(line) <= ACTIVITY_LINE_MAX_TOKENS:
            items = cand
            continue
        if not items:
            while len(t) > 1:
                t = t[:-1]
                item = f"{t}が{int(count)}人"
                line = ACTIVITY_LINE.format(items=item)
                if ch.estimate_tokens(line) <= ACTIVITY_LINE_MAX_TOKENS:
                    items = [item]
                    break
        break
    if not items:
        return ""
    return ACTIVITY_LINE.format(items=ACTIVITY_ITEM_SEPARATOR.join(items))


def person_word(agent_id: int) -> str:
    """個体 id → 観測に出る人 ID の表層(``P-17``)。

    ``B5.near_person`` の ``P-<id>(未知/知人)`` と**同じ表層**にする(行動契約書 §1-2 の
    「対象: 人ID」・``llm.contract`` の ``_PERSON_RE`` が読む形)。
    """
    return f"P-{int(agent_id)}"


def near_person_text(sp: SeenPerson) -> str:
    """見えた人(``facts.SeenPerson``)→ B5 近接行の項(``P-<id>(未知/知人)``・1-2 の前と同じ表層)。"""
    marks = T.NEAR_PERSON_MARKS  # (未知, 知人)=v1.4 で定数へ(文面は v1 から同じ)
    return f"{person_word(sp.id)}({marks[1] if sp.acquainted else marks[0]})"


def _activity_word(code: int, v3: bool = False) -> str:
    words = ACTIVITY_WORDS_V3 if v3 else ACTIVITY_WORDS
    return words[code] if 0 <= code < len(words) else words[0]
