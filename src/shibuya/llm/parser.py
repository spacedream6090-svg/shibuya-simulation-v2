"""llm.parser — 2行形の**ラベル基準・寛容行指向**パーサ(知覚契約書 §2.5 の正典実装)。

正典
- 知覚契約書 §2.5: 「**厳密JSONは課さず、パーサはラベル基準の寛容行指向**(品質プローブv0
  =4行形で書式エラー率0.000・3モデル共通。2行形はラベル同一の詰め形なので**同じパーサで
  受理する**。…パーサは**ラベルを行内でも分割する前処理**を追加)」。
- 行動契約書 §1: 1行目「理由: <40字以内・1文>」/2行目「行動: <語彙1語> 対象: <…> ひと言: <…>」。
  旧「行き先」を**対象**へ一般化(=``行き先`` ラベルは ``対象`` として受理する)。
- 行動契約書 §2: 語彙は ``ACTION_VOCAB_12`` ∪ ``ROLE_ACTION_WORDS``(役割語も**全員に見せる**)。

本パーサの契約
1. **例外を投げない**(``parse_two_line`` は必ず ``ParseResult`` を返す)。
2. ``format_ok`` は B11 実測の「**厳密2行の書式順守**」に対応する指標
   (4ラベルが揃い、行動欄から語彙語が取れた)。``action is not None`` は「行動語彙一致」。
   この2つは B11 が別々に測った2指標なので**別々に返す**。
3. 字数超過(理由>40字・ひと言>20字)は**失敗ではなく切り詰め**(フラグを立てる)。

逐次ループ宣言(P4)
- ``parse_two_line``: **ラベル出現数**(≤10程度)と**語彙数**(24)ぶんのループ。1呼=1回で、
  個体数にも tick 数にも比例しない。呼び出し側(engine.llm_bridge)が呼数ぶん回す。

expedient(本モジュール分)
- ラベルの別名表(``行き先``/``行先``/``相手``→``対象``、``一言``/``ひとこと``/``発話``→``ひと言``、
  英語名)は自前。品質プローブv0 ``tools/quality_probe_v0/scorer.py`` の別名表を参考にした
  (コードは流用せず、対象=R4 の一般化に合わせて作り直した)。
- 行動欄に語彙語が無く、かつ**行動ラベル自体が無い**ときだけ、ラベル外の残りテキストから
  語彙語を拾う(``action_from_free_text``)。ラベルがあるのに語彙外なら拾わない
  (=未定義行動として §7 段0 の辞書写像へ回す)。
- ``<think>…</think>`` の除去(Qwen3 等の思考ブロック)。
- 値の終端は「次のラベル」か「行末」の**早い方**(契約の各欄は1行1値のため)。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final, Mapping

from shibuya.llm.contract import (
    ALL_ACTION_WORDS,
    COMMENT_MAX_CHARS,
    NO_TARGET,
    NO_TARGET_VALUE,
    REASON_MAX_CHARS,
    UNDEFINED_ACTION,
    Target,
    action_code_of,
    is_role_action,
    parse_target,
)

__all__ = [
    "CANONICAL_LABELS",
    "LABEL_ALIASES",
    "ParseResult",
    "parse_two_line",
    "find_action_word",
]

#: 契約の4ラベル(この順に返す)。
CANONICAL_LABELS: Final[tuple[str, ...]] = ("理由", "行動", "対象", "ひと言")

#: 表層ラベル → 正準ラベル(expedient)。
LABEL_ALIASES: Final[Mapping[str, str]] = {
    "理由": "理由",
    "reason": "理由",
    "行動": "行動",
    "action": "行動",
    "対象": "対象",
    "行き先": "対象",  # 4行形(品質プローブv0)の欄。R4 で「対象」へ一般化された
    "行先": "対象",
    "相手": "対象",
    "target": "対象",
    "destination": "対象",
    "ひと言": "ひと言",
    "一言": "ひと言",
    "ひとこと": "ひと言",
    "発話": "ひと言",
    "utterance": "ひと言",
    "comment": "ひと言",
}

_LABEL_ALTERNATION: Final[str] = "|".join(
    re.escape(k) for k in sorted(LABEL_ALIASES, key=len, reverse=True)
)
#: ラベル検出(**行内でも分割する**=知覚契約書 §2.5 の前処理要求)。全角/半角コロン両対応。
_LABEL_RE: Final[re.Pattern[str]] = re.compile(
    r"[\[【]?\*{0,2}\s*(?P<label>" + _LABEL_ALTERNATION + r")\s*\*{0,2}[\]】]?\s*[:：]\s*",
    re.IGNORECASE,
)

_THINK_RE: Final[re.Pattern[str]] = re.compile(r"<think>.*?</think>", re.S | re.I)
_OPEN_THINK_RE: Final[re.Pattern[str]] = re.compile(r"<think>.*$", re.S | re.I)
_FENCE_RE: Final[re.Pattern[str]] = re.compile(r"^\s*```.*$")
_BULLET_RE: Final[re.Pattern[str]] = re.compile(r"^\s*(?:[-*•・>#]+\s*)+")
#: 値の前後から剥がす飾り。
_VALUE_STRIP: Final[str] = " \t　*_`「」『』\"'<>＜＞"


def _clean_text(text: str) -> str:
    """思考ブロック・コードフェンス・箇条書き記号を落とす(**値の中身は変えない**)。"""
    t = _THINK_RE.sub("", text)
    t = _OPEN_THINK_RE.sub("", t)
    lines: list[str] = []
    for line in t.split("\n"):
        if _FENCE_RE.match(line):
            continue
        lines.append(_BULLET_RE.sub("", line).rstrip())
    return "\n".join(lines).strip()


def _clean_value(value: str) -> str:
    v = value.strip().strip(_VALUE_STRIP).strip()
    return v


def find_action_word(text: str) -> str | None:
    """テキスト中で**最初に現れる**語彙語(同位置なら最長)を返す。

    「移動する」「移動します」のように助詞・語尾が付いていても、部分一致で語が取れる。

    逐次ループ宣言(P4): 語彙数(24)ぶん。
    """
    if not text:
        return None
    best: tuple[int, int, str] | None = None
    for word in ALL_ACTION_WORDS:
        pos = text.find(word)
        if pos < 0:
            continue
        cand = (pos, -len(word), word)
        if best is None or cand < best:
            best = cand
    return best[2] if best else None


@dataclass(frozen=True)
class ParseResult:
    """1応答の解釈結果。

    Attributes:
        action: 行動語(語彙一致・取れなければ None)。
        action_code: ``contract.action_code_of`` の値(未知は ``UNDEFINED_ACTION``)。
        target: 「対象」欄の解釈。
        reason: 理由(40字へ切り詰め済み)。
        comment: ひと言(20字へ切り詰め済み)。
        format_ok: 書式順守(4ラベルが揃い行動欄から語彙語が取れた)。
        errors: 何が欠けたか(診断行の素材・**順序は検出順**)。
        raw_action: 行動欄の逐語(未定義行動の記録に使う)。
        raw_comment: ひと言欄の逐語(切り詰め前)。
        raw_reason: 理由欄の逐語(切り詰め前)。
        strict_two_line: ``TWO_LINE_RE`` に一致する厳密2行だったか。
        reason_truncated / comment_truncated: 字数超過で切り詰めたか。
        is_role_action: 取れた行動語が §2.2 の役割語か(権限検査行き)。
        action_from_free_text: 行動ラベルが無く残りテキストから拾ったか(expedient 経路)。
        labels: 見つかった正準ラベル → 値(逐語)。
    """

    action: str | None
    action_code: int
    target: Target
    reason: str
    comment: str
    format_ok: bool
    errors: tuple[str, ...] = ()
    raw_action: str = ""
    raw_reason: str = ""
    raw_comment: str = ""
    strict_two_line: bool = False
    reason_truncated: bool = False
    comment_truncated: bool = False
    is_role_action: bool = False
    action_from_free_text: bool = False
    labels: Mapping[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """書式順守 **かつ** 行動語彙一致(=エンジンがそのまま intent にできる)。"""
        return self.format_ok and self.action is not None


def _empty_result(errors: tuple[str, ...]) -> ParseResult:
    return ParseResult(
        action=None,
        action_code=UNDEFINED_ACTION,
        target=NO_TARGET_VALUE,
        reason="",
        comment=NO_TARGET,
        format_ok=False,
        errors=errors,
    )


def parse_two_line(text: str | None) -> ParseResult:
    """2行形(および4行形)を寛容に読む。**例外を投げない**。

    Args:
        text: LLM の応答本文(``None`` や非文字列も受ける)。

    Returns:
        ``ParseResult``。

    Example:
        >>> r = parse_two_line("理由: 予定の時間\\n行動: 移動 対象: C-0117 ひと言: なし")
        >>> r.action, r.target.cell_index, r.format_ok
        ('移動', 117, True)
    """
    try:
        return _parse(text)
    except Exception as exc:  # pragma: no cover - 契約「例外を投げない」の最後の砦
        return _empty_result((f"internal:{type(exc).__name__}",))


def _parse(text: str | None) -> ParseResult:
    if text is None:
        return _empty_result(("empty_output",))
    if not isinstance(text, str):
        text = str(text)
    strict = _is_strict_two_line(text)
    cleaned = _clean_text(text)
    if not cleaned:
        return _empty_result(("empty_output",))

    # ---- ラベル走査(行内でも分割する) ----
    matches = list(_LABEL_RE.finditer(cleaned))
    labels: dict[str, str] = {}
    spans: list[tuple[int, int]] = []
    # 逐次ループ宣言: ラベル出現数ぶん(≤10程度)
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        nl = cleaned.find("\n", start)
        if 0 <= nl < end:
            end = nl
        canonical = LABEL_ALIASES[m.group("label").lower()
                                 if m.group("label").isascii() else m.group("label")]
        value = _clean_value(cleaned[start:end])
        # 同じラベルが2回出たら**最初**を採る(後続はモデルの繰り返し)
        if canonical not in labels:
            labels[canonical] = value
        spans.append((m.start(), end))

    errors: list[str] = []
    for label in CANONICAL_LABELS:
        if label not in labels:
            errors.append(f"missing_label:{label}")

    # ---- 行動語 ----
    raw_action = labels.get("行動", "")
    action = find_action_word(raw_action) if raw_action else None
    from_free_text = False
    if action is None and "行動" not in labels:
        # ラベルごと無いときだけ、ラベル外の残りから拾う(expedient)
        action = find_action_word(_outside_labels(cleaned, spans))
        from_free_text = action is not None
        if from_free_text:
            errors.append("action_from_free_text")
    if action is None:
        errors.append("unknown_action_word")

    # ---- 対象・理由・ひと言 ----
    target = parse_target(labels.get("対象"))
    raw_reason = labels.get("理由", "")
    raw_comment = labels.get("ひと言", NO_TARGET)
    reason = raw_reason[:REASON_MAX_CHARS]
    comment = raw_comment[:COMMENT_MAX_CHARS]
    reason_truncated = len(raw_reason) > REASON_MAX_CHARS
    comment_truncated = len(raw_comment) > COMMENT_MAX_CHARS
    if reason_truncated:
        errors.append("reason_truncated")
    if comment_truncated:
        errors.append("comment_truncated")

    format_ok = (
        all(label in labels for label in CANONICAL_LABELS)
        and action is not None
        and not from_free_text
    )
    return ParseResult(
        action=action,
        action_code=action_code_of(action) if action else UNDEFINED_ACTION,
        target=target,
        reason=reason,
        comment=comment or NO_TARGET,
        format_ok=format_ok,
        errors=tuple(errors),
        raw_action=raw_action,
        raw_reason=raw_reason,
        raw_comment=raw_comment,
        strict_two_line=strict,
        reason_truncated=reason_truncated,
        comment_truncated=comment_truncated,
        is_role_action=bool(action) and is_role_action(action),
        action_from_free_text=from_free_text,
        labels=labels,
    )


def _outside_labels(text: str, spans: list[tuple[int, int]]) -> str:
    """ラベル(とその値)の範囲を抜いた残りテキスト。

    逐次ループ宣言(P4): ラベル出現数ぶん。
    """
    if not spans:
        return text
    parts: list[str] = []
    cursor = 0
    for start, end in spans:
        if start > cursor:
            parts.append(text[cursor:start])
        cursor = max(cursor, end)
    if cursor < len(text):
        parts.append(text[cursor:])
    return "\n".join(parts)


def _is_strict_two_line(text: str) -> bool:
    """``contract.TWO_LINE_RE`` に一致する厳密2行か(B11 の「厳密2行」指標)。"""
    from shibuya.llm.contract import TWO_LINE_RE

    return bool(TWO_LINE_RE.match(text.strip()))
