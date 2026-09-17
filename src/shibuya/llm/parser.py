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

C6 パーサ許容(2026-09-09・実 LLM スモークのテープが根拠)
- 初回スモーク(5,000体×24tick・Qwen3-8B INT8・温度0)の書式エラー率 **0.176** の主因は
  「モデルが2行形はほぼ守るが**ラベルを言い換える**」(「対象:」の代わりに「目的地:」「目的:」)。
  **契約書の決定項(2行形・12語+役割語)は変えず、パーサ側の許容**として別名を足した
  (``LABEL_ALIASES_C6``)。
- 受入指標の「書式エラー率」を**同じ定義のまま数え続けられる**よう、C6 以前の別名表
  ``LABEL_ALIASES_V0`` だけで判定した ``strict_format_ok`` を併記する
  (``format_ok`` は C6 別名を含めた寛容判定=再生成の要否に使う)。
- 別名を1つでも使ったら ``alias_used=True``(+使った表層を ``alias_surfaces``)。
- **追加(09-09 夕・``--fleet-debug-dir`` 60tick/2,083呼の失敗 531 の内訳が根拠)**: 失敗の最大群は
  ``missing_label:対象`` 226・``対象+ひと言`` 78・``ひと言`` 6 で、中身は**ラベルを省いて値だけを
  契約の順序で並べた**形(「行動: 移動 なし なし」)。欄の順序は §1 で固定なので、
  **位置**で読む(``_fill_positional``・``positional_used``)。``unknown_action_word`` 96 の内訳
  (探索 50・通勤 16・観察 9・調査 …)は §7 段0 の辞書を広げて受ける。
- 語彙外の語が段0 の辞書で救えるかは ``dictionary_candidate`` に出す(**実効 ``format_ok`` は
  真にしない**=語彙外だった事実を残す・親決定 09-09)。

expedient(本モジュール分)
- ラベルの別名表(``行き先``/``行先``/``相手``→``対象``、``一言``/``ひとこと``/``発話``→``ひと言``、
  英語名)は自前。品質プローブv0 ``tools/quality_probe_v0/scorer.py`` の別名表を参考にした
  (コードは流用せず、対象=R4 の一般化に合わせて作り直した)。C6 追加分も同じく自前
  (根拠=実測テープの言い換え。昇格条件はテンプレ v1.1 で「対象:」固定を強調して再測)。
- 行末の literal ``\n``(テープに ``ため  \n`` の形で現れる escaped newline)は、本文に実改行が
  無いときだけ実改行へ直し、値の末尾に残ったものは落とす。
- 行動欄に語彙語が無く、かつ**行動ラベル自体が無い**ときだけ、ラベル外の残りテキストから
  語彙語を拾う(``action_from_free_text``)。ラベルがあるのに語彙外なら拾わない
  (=未定義行動として §7 段0 の辞書写像へ回す)。
- ``<think>…</think>`` の除去(Qwen3 等の思考ブロック)。
- 値の終端は「次のラベル」か「行末」の**早い方**(契約の各欄は1行1値のため)。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field, replace
from typing import Final, Mapping

from shibuya.llm.contract import (
    DEFAULT_VOCAB_VERSION,
    action_words,
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
from shibuya.llm.undefined import map_synonym

__all__ = [
    "CANONICAL_LABELS",
    "LABEL_ALIASES",
    "LABEL_ALIASES_V0",
    "LABEL_ALIASES_C6",
    "POSITIONAL_SURFACE",
    "ParseResult",
    "parse_two_line",
    "find_action_word",
]

#: ``alias_surfaces`` に入れる位置引数の印(ラベル表層ではないので別名表には入れない)。
POSITIONAL_SURFACE: Final[str] = "positional"

#: 契約の4ラベル(この順に返す)。
CANONICAL_LABELS: Final[tuple[str, ...]] = ("理由", "行動", "対象", "ひと言")

#: C6 以前の別名表(**凍結**=受入指標「書式エラー率」の分母を動かさないための参照点)。
LABEL_ALIASES_V0: Final[Mapping[str, str]] = {
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

#: C6 で追加した別名(**expedient**・実 LLM スモークのテープに現れた言い換えが根拠)。
LABEL_ALIASES_C6: Final[Mapping[str, str]] = {
    # 対象(スモークで最多=「目的地」「目的」)
    "目的地": "対象",
    "目的": "対象",
    "場所": "対象",
    "対象物": "対象",
    # ひと言
    "コメント": "ひと言",
    "セリフ": "ひと言",
    "台詞": "ひと言",
    # 理由
    "根拠": "理由",
    "わけ": "理由",
    # 行動
    "アクション": "行動",
    "行為": "行動",
}

#: 表層ラベル → 正準ラベル(expedient)。``LABEL_ALIASES_V0`` ∪ ``LABEL_ALIASES_C6``。
LABEL_ALIASES: Final[Mapping[str, str]] = {**LABEL_ALIASES_V0, **LABEL_ALIASES_C6}

#: C6 で足した表層(``alias_used`` の内訳と ``strict_format_ok`` の短絡判定に使う)。
_C6_SURFACES: Final[frozenset[str]] = frozenset(LABEL_ALIASES_C6)


def _label_pattern(table: Mapping[str, str]) -> re.Pattern[str]:
    """ラベル検出(**行内でも分割する**=知覚契約書 §2.5 の前処理要求)。

    全角/半角コロン・ラベル前後の空白(全角空白を含む)・``**``/``[]``/``【】`` の飾りを吸収する。
    長い表層から順に並べる(``目的地`` が ``目的`` に食われないように)。
    """
    alternation = "|".join(re.escape(k) for k in sorted(table, key=len, reverse=True))
    return re.compile(
        r"[\[【]?\*{0,2}\s*(?P<label>" + alternation + r")\s*\*{0,2}[\]】]?\s*[:：]\s*",
        re.IGNORECASE,
    )


_LABEL_RE: Final[re.Pattern[str]] = _label_pattern(LABEL_ALIASES)
#: C6 以前の判定を再現するための走査(``strict_format_ok``)。
_LABEL_RE_V0: Final[re.Pattern[str]] = _label_pattern(LABEL_ALIASES_V0)

_THINK_RE: Final[re.Pattern[str]] = re.compile(r"<think>.*?</think>", re.S | re.I)
_OPEN_THINK_RE: Final[re.Pattern[str]] = re.compile(r"<think>.*$", re.S | re.I)
_FENCE_RE: Final[re.Pattern[str]] = re.compile(r"^\s*```.*$")
_BULLET_RE: Final[re.Pattern[str]] = re.compile(r"^\s*(?:[-*•・>#]+\s*)+")
#: 値の前後から剥がす飾り。
_VALUE_STRIP: Final[str] = " \t　*_`「」『』\"'<>＜＞"
#: 値の末尾に残った literal ``\n``(escaped newline・C6 テープに出た形)。
_TRAILING_ESCAPED_NL: Final[re.Pattern[str]] = re.compile(r"(?:\s*\\n)+\s*$")


def _clean_text(text: str) -> str:
    """思考ブロック・コードフェンス・箇条書き記号を落とす(**値の中身は変えない**)。

    C6 追加: 実改行が1つも無く literal ``\\n`` がある本文は、それを改行として読む
    (テープに ``理由: …ため  \\n行動: …`` の形で現れる)。行末の空白は従来どおり ``rstrip``。
    """
    t = _THINK_RE.sub("", text)
    t = _OPEN_THINK_RE.sub("", t)
    if "\n" not in t and "\\n" in t:
        t = t.replace("\\n", "\n")
    lines: list[str] = []
    for line in t.split("\n"):
        if _FENCE_RE.match(line):
            continue
        lines.append(_BULLET_RE.sub("", line).rstrip())
    return "\n".join(lines).strip()


def _clean_value(value: str) -> str:
    v = _TRAILING_ESCAPED_NL.sub("", value.strip())
    v = v.strip().strip(_VALUE_STRIP).strip()
    return v


def find_action_word(
    text: str, vocab_version: str = DEFAULT_VOCAB_VERSION
) -> str | None:
    """テキスト中で**最初に現れる**語彙語(同位置なら最長)を返す。

    「移動する」「移動します」のように助詞・語尾が付いていても、部分一致で語が取れる。

    Args:
        text: 走査対象。
        vocab_version: 語彙版(``"v1"``=24 語・既定 / ``"v2"``=25 語=24 語+「食事」)。
            既定では ``ALL_ACTION_WORDS`` と**同一の並び**を走るので 1 件も結果が変わらない。

    逐次ループ宣言(P4): 語彙数(v1=24 / v2=25)ぶん。
    """
    if not text:
        return None
    best: tuple[int, int, str] | None = None
    for word in action_words(vocab_version):
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
        format_ok: 書式順守(4ラベルが揃い行動欄から語彙語が取れた)。**C6 別名を含む**寛容判定。
        strict_format_ok: C6 以前の別名表(``LABEL_ALIASES_V0``)だけで見た同じ判定。
            受入指標「書式エラー率」は**この欄で数え続ける**(定義を動かさないため)。
        alias_used: 正準ラベル以外の表層を1つでも使ったか(``label_alias_used`` と同義)。
            **位置引数(``positional_used``)はここには入れない**(ラベル表層の話ではないため)。
        alias_surfaces: 使った別名の表層(検出順・重複なし)。位置引数を使った応答では末尾に
            ``"positional"`` が入る(内訳を1本の列で数えられるようにするため)。
        positional_used: ラベルを省いて値だけ並べた形を**位置**で読んだか。
        dictionary_mapped: §7 段0 の辞書写像で行動語が入ったか
            (``with_dictionary_mapping`` を通したときだけ真)。
        dictionary_candidate: 語彙外だったとき、§7 段0 の辞書で**救える語**(写像先)。
            救えなければ ``None``。**初回判定でも数えられる**診断で、写像そのもの(呼数・計数・
            段1〜4)は ``undefined.UndefinedActionRegistry`` の仕事。段4 の判例は見ない。
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
    strict_format_ok: bool = False
    alias_used: bool = False
    alias_surfaces: tuple[str, ...] = ()
    positional_used: bool = False
    dictionary_mapped: bool = False
    dictionary_candidate: str | None = None
    labels: Mapping[str, str] = field(default_factory=dict)

    @property
    def ok(self) -> bool:
        """書式順守 **かつ** 行動語彙一致(=エンジンがそのまま intent にできる)。"""
        return self.format_ok and self.action is not None

    @property
    def label_alias_used(self) -> bool:
        """``alias_used`` の別名(C6 の診断名)。"""
        return self.alias_used

    def with_dictionary_mapping(
        self, word: str, vocab_version: str = DEFAULT_VOCAB_VERSION
    ) -> "ParseResult":
        """§7 段0 の辞書写像の結果を載せた**新しい** ``ParseResult`` を返す。

        ``undefined.UndefinedActionRegistry.observe`` が段0(``source="dictionary"``)で
        写した語を、呼び出し側(``engine.llm_bridge`` / ``llm.fleet``)がここに載せる。
        ``format_ok`` / ``strict_format_ok`` / ``errors`` は**生の応答の記述なので変えない**
        (語彙外だったという事実は残す)。

        Args:
            word: 契約語彙(``UndefinedOutcome.word``)。
            vocab_version: 語彙版(``"v2"`` で「食事」もコード化できる)。

        Returns:
            ``action``/``action_code``/``is_role_action``/``dictionary_mapped`` を更新した複製。
        """
        return replace(
            self,
            action=word,
            action_code=action_code_of(word, vocab_version),
            is_role_action=is_role_action(word),
            dictionary_mapped=True,
        )


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


def parse_two_line(
    text: str | None, vocab_version: str = DEFAULT_VOCAB_VERSION
) -> ParseResult:
    """2行形(および4行形)を寛容に読む。**例外を投げない**。

    Args:
        text: LLM の応答本文(``None`` や非文字列も受ける)。
        vocab_version: 語彙版(D-71 §3 F)。``"v2"`` で「食事」を語彙語として読み、
            段0 辞書の候補判定(``dictionary_candidate``)も辞書 v3 で引く。
            **既定 ``"v1"`` は 1 バイトも挙動が変わらない**。

    Returns:
        ``ParseResult``。

    Example:
        >>> r = parse_two_line("理由: 予定の時間\\n行動: 移動 対象: C-0117 ひと言: なし")
        >>> r.action, r.target.cell_index, r.format_ok
        ('移動', 117, True)
    """
    try:
        return _parse(text, vocab_version)
    except Exception as exc:  # pragma: no cover - 契約「例外を投げない」の最後の砦
        return _empty_result((f"internal:{type(exc).__name__}",))


def _parse(text: str | None, vocab_version: str = DEFAULT_VOCAB_VERSION) -> ParseResult:
    if text is None:
        return _empty_result(("empty_output",))
    if not isinstance(text, str):
        text = str(text)
    strict = _is_strict_two_line(text)
    cleaned = _clean_text(text)
    if not cleaned:
        return _empty_result(("empty_output",))

    # ---- ラベル走査(行内でも分割する) ----
    labels, spans, surfaces = _scan_labels(cleaned, _LABEL_RE, LABEL_ALIASES)
    alias_surfaces = tuple(s for s in surfaces if LABEL_ALIASES[s] != s)
    alias_used = bool(alias_surfaces)

    errors: list[str] = []
    for label in CANONICAL_LABELS:
        if label not in labels:
            errors.append(f"missing_label:{label}")

    # ---- ラベルを省いて値だけ並べた形(C6・位置引数)の回収 ----
    filled = _fill_positional(labels)
    positional_used = bool(filled)
    if positional_used:
        errors.extend(filled)
        alias_surfaces = alias_surfaces + (POSITIONAL_SURFACE,)

    # ---- 行動語 ----
    raw_action = labels.get("行動", "")
    action = find_action_word(raw_action, vocab_version) if raw_action else None
    from_free_text = False
    if action is None and "行動" not in labels:
        # ラベルごと無いときだけ、ラベル外の残りから拾う(expedient)
        action = find_action_word(_outside_labels(cleaned, spans), vocab_version)
        from_free_text = action is not None
        if from_free_text:
            errors.append("action_from_free_text")
    dictionary_candidate: str | None = None
    if action is None:
        errors.append("unknown_action_word")
        # §7 段0 の辞書で**救える語かどうか**だけを見る(写像そのものは台帳の仕事=
        # 呼数も計数も台帳側。ここは初回判定でも数えられる診断のため)。
        if raw_action:
            dictionary_candidate = map_synonym(raw_action, None, vocab_version)[0]

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
    # C6 以前の判定(受入指標の定義を動かさない)。C6 別名も位置引数も使っていなければ同じ
    # 走査になるので**短絡**する(逐次ループ宣言: 使ったときだけラベル走査がもう1回)。
    if not positional_used and not any(s in _C6_SURFACES for s in surfaces):
        strict_format_ok = format_ok
    else:
        labels_v0, _, _ = _scan_labels(cleaned, _LABEL_RE_V0, LABEL_ALIASES_V0)
        strict_format_ok = all(label in labels_v0 for label in CANONICAL_LABELS) and (
            find_action_word(labels_v0.get("行動", ""), vocab_version) is not None
        )
    return ParseResult(
        action=action,
        action_code=action_code_of(action, vocab_version) if action else UNDEFINED_ACTION,
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
        strict_format_ok=strict_format_ok,
        alias_used=alias_used,
        alias_surfaces=alias_surfaces,
        positional_used=positional_used,
        dictionary_candidate=dictionary_candidate,
        labels=labels,
    )


def _fill_positional(labels: dict[str, str]) -> tuple[str, ...]:
    """ラベルを省いて**値だけ並べた**2行目から「対象」「ひと言」を位置で拾う(C6・expedient)。

    正典: 行動契約書 §1 の2行目は「行動: <語彙1語> 対象: <…> ひと言: <…>」で**欄の順序が固定**。
    実測(``--fleet-debug-dir``・60tick・2,083呼)の失敗 531 のうち 310 が
    ``missing_label:対象``(+ひと言)で、中身は「行動: 移動 なし なし」「行動: 待機 なし ひと言: なし」
    「行動: 購入 物のカテゴリ」のように**値だけが契約の順序で並んだ**形だった。
    そこで「欠けたラベルの値は、**直前に在る欄の余りトークン**」として拾う:

    - 「行動: <語> <v1> <v2…>」→ 対象=v1・ひと言=v2 以降
    - 「行動: <語> <v1> ひと言: …」→ 対象=v1(ひと言はラベルで在る)
    - 「行動: <語> 対象: <t1> <t2…>」→ ひと言=t2 以降(ひと言が対象の値に押し込まれた形)
    - v2 が無い(「行動: 購入 物のカテゴリ」)ときの ひと言 は契約の既定値 ``なし``

    安全弁: **行動ラベルが在り、その先頭トークンに行動語がある**ときだけ働く
    (「行動: すぐに 移動 なし」のように語が先頭に無い形は、位置で読める形ではないので触らない)。
    余りトークンが1つも無ければ何もしない(=欄の欠落は欠落のまま)。

    Args:
        labels: ``_scan_labels`` が作った表。**破壊的に更新する**。

    Returns:
        補ったラベルの診断名(``positional:対象`` 等・``errors`` に載せる。空なら未発動)。

    逐次ループ宣言(P4): 行動欄のトークン数ぶん(数個)。1呼=1回。
    """
    if "行動" not in labels:
        return ()
    if "対象" in labels and "ひと言" in labels:
        return ()
    filled: list[str] = []
    tokens = labels["行動"].split()
    if not tokens:
        return ()
    action_all = find_action_word(labels["行動"])
    if action_all is not None and find_action_word(tokens[0]) != action_all:
        return ()  # 行動語が先頭トークンに無い=位置で読める形ではない
    rest = tokens[1:]
    if not rest and "対象" not in labels:
        return ()  # 余りが無い=ただの欄落ち(ここでは補わない)
    if "対象" not in labels and rest:
        labels["対象"] = rest.pop(0)
        filled.append("positional:対象")
    if "ひと言" not in labels and rest:
        labels["ひと言"] = " ".join(rest)
        rest = []
        filled.append("positional:ひと言")
    if filled:
        labels["行動"] = tokens[0]  # ``raw_action`` は語彙語だけにする
    if "ひと言" not in labels and "対象" in labels:
        target_tokens = labels["対象"].split()
        if len(target_tokens) > 1:
            labels["対象"] = target_tokens[0]
            labels["ひと言"] = " ".join(target_tokens[1:])
            filled.append("positional:ひと言")
        elif filled:
            # 「行動: 購入 物のカテゴリ」型。ひと言は契約の既定値へ倒す
            labels["ひと言"] = NO_TARGET
            filled.append("comment_defaulted")
    return tuple(filled)


def _scan_labels(
    cleaned: str, pattern: re.Pattern[str], table: Mapping[str, str]
) -> tuple[dict[str, str], list[tuple[int, int]], tuple[str, ...]]:
    """ラベルを走査して ``(正準ラベル→値, 値の範囲, 使った表層)`` を返す。

    値の終端は「次のラベル」か「行末」の**早い方**。同じ正準ラベルが2回出たら**最初**を採る。

    逐次ループ宣言(P4): ラベル出現数ぶん(≤10程度)。1呼=1回。
    """
    matches = list(pattern.finditer(cleaned))
    labels: dict[str, str] = {}
    spans: list[tuple[int, int]] = []
    surfaces: list[str] = []
    for i, m in enumerate(matches):
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(cleaned)
        nl = cleaned.find("\n", start)
        if 0 <= nl < end:
            end = nl
        raw_label = m.group("label")
        surface = raw_label.lower() if raw_label.isascii() else raw_label
        canonical = table[surface]
        value = _clean_value(cleaned[start:end])
        if canonical not in labels:
            labels[canonical] = value
        if surface not in surfaces:
            surfaces.append(surface)
        spans.append((m.start(), end))
    return labels, spans, tuple(surfaces)


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
