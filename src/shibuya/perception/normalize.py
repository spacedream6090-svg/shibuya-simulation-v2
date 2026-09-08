"""perception.normalize — バイト一致の正規化規約 9 項(知覚契約書 §2.4)を関数にしたもの。

契約書の 9 項(逐語)
    ①数値は段階語彙か固定桁丸め ②列挙はID昇順 ③空白・改行は固定 ④単位固定
    ⑤段階語彙は法定/LOS境界に釘付け ⑥省略記法禁止 ⑦空要素は固定文言
    ⑧個体依存語をB0-B4に一切入れない(検査=同セル同時間帯の2体でB0-B4のバイト差分がゼロ)
    ⑨時刻表記は5分丸め

対応表(規約 → 本モジュールの関数)
    ① ``round_stage`` / ``round_fixed`` / ``format_money``(段階語彙は ``templates`` 側)
    ② ``sort_ids``
    ③ ``canonical_whitespace`` / ``join_lines``
    ④ ``UNITS`` / ``format_meters`` / ``format_minutes`` / ``format_money``
    ⑤ ``peg_stage``(境界配列は ``templates`` の法定/LOS 値)
    ⑥ ``assert_no_abbreviation``
    ⑦ ``EMPTY_PHRASE``(``templates``)・``or_empty``
    ⑧ ``assert_no_agent_dependent_words``
    ⑨ ``round_time_5min`` / ``format_time``

逐次ループ宣言(P4): なし(行数ぶんの内包表記のみ。個体数・tick 数に比例しない)。

**解決した曖昧点(親へ報告済み・黙って解決していない)**
    §2.4 ⑧ の検査文は「同セル**同時間帯**の2体で B0-B4 のバイト差分がゼロ」だが、
    §2.2 は B1 を「種別(変種数 約10)」と定義している。同一セルに種別の違う2体が居れば
    B1 は必ず異なるので、⑧ を逐語で満たすことは**構造的に不可能**。
    本実装は ⑧ を「B0-B4 に**個体を特定する語**(人ID・個体固有の数値)を入れない」と読み、
    バイト一致検査は **(セル, 5分帯, 種別)** の3つ組で行う(``renderer`` の golden テスト)。

**規約 ⑥ の適用範囲(解決した曖昧点)**
    ``ABBREVIATIONS`` の ``など``/``等`` は「A、B **など**」という**列挙の省略記法**を狙った規則。
    B0 の凍結散文(v0 由来)には「路上や公園**など**の公共の場所」のような自然な用法が含まれる
    ので、``assert_no_abbreviation`` は**列挙行**(B2 可視/地物・B4 行為・B5 近接・B4b 近景)に
    だけ掛ける。散文には掛けない。

expedient(本モジュール分)
- 省略記法の禁止語リスト ``ABBREVIATIONS``(契約書は「省略記法禁止」としか書かない)。
- 個体依存語の検出パターン ``AGENT_DEPENDENT_PATTERNS``(同上)。
- 5分丸めは **切り捨て**(``floor``)。契約書は丸め幅 5 分しか与えていない。切り上げ/最近接だと
  同一 tick 内で未来の時刻を名乗る場合がある(δ_perc は tick を進めない=運用設計書 §2.3)。
"""

from __future__ import annotations

import re
import unicodedata
from datetime import datetime
from typing import Final, Iterable, Sequence

import numpy as np

__all__ = [
    "TIME_ROUND_MINUTES",
    "UNITS",
    "ABBREVIATIONS",
    "AGENT_DEPENDENT_PATTERNS",
    "LIST_SEPARATOR",
    "LINE_SEPARATOR",
    "round_time_5min",
    "format_time",
    "time_band",
    "sort_ids",
    "canonical_whitespace",
    "join_lines",
    "format_meters",
    "format_minutes",
    "format_money",
    "round_fixed",
    "peg_stage",
    "peg_stage_array",
    "assert_no_abbreviation",
    "or_empty",
    "assert_no_agent_dependent_words",
    "AgentDependentWordError",
]

#: ⑨ 時刻の丸め幅[分](expedient・初期値5分。R5 と同時に再検討)。
TIME_ROUND_MINUTES: Final[int] = 5

#: ④ 単位の固定表記(**この表以外の単位語を使わない**)。
UNITS: Final[dict[str, str]] = {
    "distance": "メートル",
    "money": "円",
    "time": "分",
    "hour": "時",
    "sound": "デシベル",
    "temperature": "度",
    "person": "人",
}

#: ⑥ 省略記法(これらが観測文に出たら ``assert_no_abbreviation`` が弾く)。
ABBREVIATIONS: Final[tuple[str, ...]] = (
    "〜", "～", "…", "‥", "ほか", "など", "等", "他多数", "以下略", "略",
    "etc", "...", "e.g.", "i.e.",
)

#: ③ 列挙の区切り(読点)と行の区切り(LF)。**文字を変えない**。
LIST_SEPARATOR: Final[str] = "、"
LINE_SEPARATOR: Final[str] = "\n"

#: ⑧ 個体依存語の検出パターン(B0-B4 に現れてはいけない)。
AGENT_DEPENDENT_PATTERNS: Final[tuple[tuple[str, "re.Pattern[str]"], ...]] = (
    ("人ID", re.compile(r"P-\d+")),
    ("個体ID", re.compile(r"A-\d+")),
    ("二人称の所有", re.compile(r"あなたの(?:所持金|空腹|体力|体感温度|持ち物)")),
    ("所持金", re.compile(r"所持金は[\d,]+円")),
    ("内受容", re.compile(r"(?:空腹|体力|体感温度)は\d+(?:で|です)")),
    ("被注視", re.compile(r"あなたを見ている人")),
    ("直近の行動", re.compile(r"直近の行動は")),
)


class AgentDependentWordError(ValueError):
    """B0-B4 に個体依存語が混入した(§2.4 ⑧ 違反)。"""


# ------------------------------------------------------------------ ⑨ 時刻
def round_time_5min(when: datetime, minutes: int = TIME_ROUND_MINUTES) -> tuple[int, int]:
    """世界内日時 → (時, 分) を 5 分**切り捨て**で丸める(§2.4 ⑨)。

    Example:
        >>> from datetime import datetime
        >>> round_time_5min(datetime(2026, 7, 28, 12, 34))
        (12, 30)
        >>> round_time_5min(datetime(2026, 7, 28, 12, 31))
        (12, 30)
    """
    if minutes <= 0 or 60 % minutes:
        raise ValueError("丸め幅は 60 を割り切る正の分数")
    return int(when.hour), (int(when.minute) // minutes) * minutes


def format_time(when: datetime, minutes: int = TIME_ROUND_MINUTES) -> tuple[str, str]:
    """(時, 分) の**固定桁なし**表記(v0 文面「現在時刻は12時40分です」に合わせる)。"""
    h, m = round_time_5min(when, minutes)
    return str(h), f"{m:02d}"


def time_band(when: datetime, minutes: int = TIME_ROUND_MINUTES) -> int:
    """世界内日時 → 5 分帯の番号(0..287)。共有ブロックのキャッシュ鍵。"""
    h, m = round_time_5min(when, minutes)
    return (h * 60 + m) // minutes


# ------------------------------------------------------------------ ② 列挙
def sort_ids(ids: Iterable[str | int]) -> list[str]:
    """列挙は **ID 昇順**(§2.4 ②)。数値 ID は数として、文字列 ID はコードポイント順。

    数値と文字列が混じる場合は「数値が先・その中で昇順」→「文字列・その中で昇順」。
    """
    nums: list[int] = []
    strs: list[str] = []
    for v in ids:
        if isinstance(v, (int, np.integer)) and not isinstance(v, bool):
            nums.append(int(v))
        else:
            strs.append(str(v))
    return [str(n) for n in sorted(nums)] + sorted(strs)


# ------------------------------------------------------------------ ③ 空白・改行
_WS_RE: Final[re.Pattern[str]] = re.compile(r"[ \t　]+")


def canonical_whitespace(text: str) -> str:
    """空白・改行の正準形(§2.4 ③)。

    - Unicode 正規化 NFKC(全角空白・全角数字の揺れを潰す)
    - CRLF/CR → LF
    - 連続する空白 → 半角空白 1 個
    - 行頭・行末の空白を落とす / 末尾の改行を落とす
    """
    t = unicodedata.normalize("NFKC", str(text))
    t = t.replace("\r\n", "\n").replace("\r", "\n")
    lines = [_WS_RE.sub(" ", ln).strip() for ln in t.split("\n")]
    return "\n".join(lines).strip("\n")


def join_lines(lines: Sequence[str]) -> str:
    """1行1事実の行列 → ブロック本文(空行は落とし、LF 固定で連結)。"""
    return LINE_SEPARATOR.join(canonical_whitespace(ln) for ln in lines if str(ln).strip())


# ------------------------------------------------------------------ ①④ 数値・単位
def format_meters(value: float, digits: int = 0) -> str:
    """距離[m]の固定桁表記(④ 単位固定・① 固定桁丸め)。"""
    return f"{round(float(value), digits):.{digits}f}".rstrip(".") + UNITS["distance"]


def format_minutes(value: int) -> str:
    """時間[分]の固定表記。"""
    return f"{int(value)}{UNITS['time']}"


def format_money(value: int) -> str:
    """金額[円]の固定表記(3 桁区切り・v0 文面「所持金は1,200円です」に合わせる)。"""
    return f"{int(value):,}{UNITS['money']}"


def round_fixed(value: float, digits: int = 0) -> float:
    """① 固定桁丸め(段階語彙を持たない量に使う)。"""
    return float(np.round(float(value), digits))


def peg_stage(value: float, edges: Sequence[float]) -> int:
    """⑤ 段階語彙の釘付け: 値 → 段番号(``edges`` は昇順の**法定/LOS 境界**)。

    ``edges`` が n 個なら段は 0..n。境界値そのものは**上の段**に入る(``side="right"`` ではなく
    ``side="left"`` の逆=「以上で上の段」)。

    Example:
        >>> peg_stage(0.30754, (0.30754, 0.43056))   # 境界ちょうどは上の段
        1
    """
    e = np.asarray(edges, dtype=np.float64)
    if e.size and np.any(np.diff(e) <= 0):
        raise ValueError("境界は昇順の相異なる値")
    return int(np.searchsorted(e, float(value), side="right"))


def peg_stage_array(values: np.ndarray, edges: Sequence[float]) -> np.ndarray:
    """``peg_stage`` のベクトル版(セル配列にそのまま掛ける)。"""
    e = np.asarray(edges, dtype=np.float64)
    return np.searchsorted(e, np.asarray(values, dtype=np.float64), side="right").astype(np.uint8)


# ------------------------------------------------------------------ ⑥ 省略記法
def assert_no_abbreviation(text: str, where: str = "") -> None:
    """⑥ 省略記法が入っていないことを検査する。"""
    hits = [a for a in ABBREVIATIONS if a in text]
    if hits:
        raise ValueError(f"§2.4 ⑥ 省略記法禁止: {hits} が {where or '観測文'} に含まれる")


# ------------------------------------------------------------------ ⑦ 空要素
def or_empty(items: Sequence[str], empty_phrase: str) -> str:
    """⑦ 空要素は固定文言。非空なら読点で連結する。"""
    return LIST_SEPARATOR.join(items) if items else empty_phrase


# ------------------------------------------------------------------ ⑧ 個体依存語
def assert_no_agent_dependent_words(text: str, where: str = "B0-B4") -> None:
    """⑧ B0-B4 に個体依存語が無いことを検査する(混入したら例外)。

    Raises:
        AgentDependentWordError: 人ID・所持金・内受容値などが見つかった。
    """
    for name, pat in AGENT_DEPENDENT_PATTERNS:
        m = pat.search(text)
        if m is not None:
            raise AgentDependentWordError(
                f"§2.4 ⑧ 違反: {where} に個体依存語({name}: {m.group(0)!r})が入っている"
            )
