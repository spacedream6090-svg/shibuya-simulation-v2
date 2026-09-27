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
- **D-113 ①(第266・2026-09-26・C8 の 8 テープ 485,527 呼のリプレイ計測が根拠)**: 別名表に無い
  ラベル(「目標:」32,736 呼ほか)が行動欄の値に残り、位置引数の回収がその**ラベル表層を対象の値**
  として採っていた(呼の 8.3% で対象が「語+コロン」だけ・``format_ok`` は True のまま)。直し=
  (1) テープで実測した表層 7 語を ``LABEL_ALIASES_D113``(→対象)に足す (2) 位置引数の回収で
  「語+コロン」だけのトークンは**未知のラベル**として読み飛ばし ``unknown_label:<表層>`` を
  ``errors`` に残す(後ろに値が無ければ欄落ち)。``strict_format_ok`` は V0 のまま。
  記録: docs/bench/analysis/d113-defects-2026-09-26/README.md。
- **語彙 v3(第274・D-116 行為と活動の二層・アジェンダ §1-2)**: ``vocab_version="v3"`` のときだけ
  別の経路(``_parse_v3``)で読む。ラベルは 理由・行動・対象・**活動**・**まで** の 5 つ
  (``CANONICAL_LABELS_V3``)で、**ひと言は必須から外す**(別名表に残し受理はする=会話側で使う)。
  ``format_ok``(v3)=5 ラベル揃い+行動語が取れた・``strict_format_ok``(v3)=5 ラベルを**正準表層
  だけ**で(別名なし・位置引数なし)。位置引数の順序も 理由→行動→対象→活動→まで。
  「まで」は ``contract.parse_until`` で型に写す・「対象: あたり」は ``Target.wander``・
  「対象: 自宅/職場/学校」は ``ParseResult.target_hint``(home/work/school)。
  **v1/v2 の経路は 1 行も通らない**(判定・別名表・位置引数の規則は 1 バイトも変えない)。
  第275 親の決め #4: **行動=なし のときだけ対象ラベルの省略を許す**(対象=なし として
  ``format_ok`` を落とさない・``errors`` の ``missing_label:対象`` を ``target_omitted`` に置き換える)。
  行為の語では従来どおり欠落は書式エラー。``strict_format_ok`` は 5 ラベルの定義のまま(省略は偽)。

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
    ACTION_WORD_NONE,
    ACTIVITY_MAX_CHARS,
    DEFAULT_UNTIL,
    DEFAULT_VOCAB_VERSION,
    TWO_LINE_RE_V3,
    action_words,
    COMMENT_MAX_CHARS,
    NO_TARGET,
    NO_TARGET_VALUE,
    REASON_MAX_CHARS,
    UNDEFINED_ACTION,
    Target,
    TargetKind,
    Until,
    action_code_of,
    is_role_action,
    parse_target,
    parse_until,
)
from shibuya.llm.undefined import map_synonym, target_surface_hint

__all__ = [
    "CANONICAL_LABELS",
    "LABEL_ALIASES",
    "LABEL_ALIASES_V0",
    "LABEL_ALIASES_C6",
    "LABEL_ALIASES_D113",
    "CANONICAL_LABELS_V3",
    "LABEL_ALIASES_V3_ADD",
    "LABEL_ALIASES_V3",
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

#: D-113 ①(第266・2026-09-26)で追加した別名(**expedient**・C8 の 8 テープ 48 万呼の実測が根拠:
#: 「目標:」32,736 呼・「カテゴリ:」1,984・「目的先:」523・「ターゲット:」378・「对象:」127・
#: 「目标:」57・「行く先:」19 が別名表に無く、``_fill_positional`` が**そのラベル表層を対象の値**
#: として読んでいた=顕著な出来事の台帳 §2 ⑥)。受入指標 ``strict_format_ok`` は V0 のまま。
LABEL_ALIASES_D113: Final[Mapping[str, str]] = {
    "目標": "対象",
    "目标": "対象",
    "カテゴリ": "対象",
    "目的先": "対象",
    "ターゲット": "対象",
    "对象": "対象",
    "行く先": "対象",
}

#: 表層ラベル → 正準ラベル(expedient)。``LABEL_ALIASES_V0`` ∪ ``LABEL_ALIASES_C6`` ∪ ``LABEL_ALIASES_D113``。
LABEL_ALIASES: Final[Mapping[str, str]] = {
    **LABEL_ALIASES_V0,
    **LABEL_ALIASES_C6,
    **LABEL_ALIASES_D113,
}

#: C6 で足した表層(``alias_used`` の内訳)。
_C6_SURFACES: Final[frozenset[str]] = frozenset(LABEL_ALIASES_C6)
#: V0 に無い表層(``strict_format_ok`` の短絡判定に使う=C6 ∪ D113)。
_NON_V0_SURFACES: Final[frozenset[str]] = _C6_SURFACES | frozenset(LABEL_ALIASES_D113)

#: 「語+コロン」だけのトークン=別名表に無い**未知のラベル**(「目安:」「データ:」「その他:」…)。
#: 位置引数の回収でこれを値として読まない(D-113 ①)。診断名 ``unknown_label:<表層>`` を残す。
_UNKNOWN_LABEL_TOKEN_RE: Final[re.Pattern[str]] = re.compile(r"^[^\s:：]{1,10}[:：]$")


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

# ------------------------------------------------------------------ 語彙 v3 のラベル(D-116 B)
#: 語彙 v3 の 5 ラベル(この順に返す・位置引数の順序も同じ)。**ひと言は必須から外す**。
CANONICAL_LABELS_V3: Final[tuple[str, ...]] = ("理由", "行動", "対象", "活動", "まで")
#: v3 で足すラベル(**正準の表層だけ**・別名は足さない=実測前に言い換えを推測しない)。
LABEL_ALIASES_V3_ADD: Final[Mapping[str, str]] = {"活動": "活動", "まで": "まで"}
#: v3 の寛容判定の表(v1 の全別名 + 2 ラベル)。v1 の ``LABEL_ALIASES`` は動かさない。
LABEL_ALIASES_V3: Final[Mapping[str, str]] = {**LABEL_ALIASES, **LABEL_ALIASES_V3_ADD}
#: v3 の ``strict_format_ok`` の走査表=**正準表層だけ**(ひと言 も正準表層なので載せる=
#: 値の終端を正しく切るため。必須かどうかは ``CANONICAL_LABELS_V3`` が決める)。
_STRICT_LABELS_V3: Final[Mapping[str, str]] = {
    label: label for label in (*CANONICAL_LABELS_V3, "ひと言")
}
_LABEL_RE_V3: Final[re.Pattern[str]] = _label_pattern(LABEL_ALIASES_V3)
_LABEL_RE_STRICT_V3: Final[re.Pattern[str]] = _label_pattern(_STRICT_LABELS_V3)
#: 行動の後ろに位置で並ぶ欄(v3)。**最後の欄(まで)は残りのトークンを全部取る**
#: (v1 の ひと言 と同じ扱い)。
_POSITIONAL_FIELDS_V3: Final[tuple[str, ...]] = ("対象", "活動", "まで")

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
        activity: **語彙 v3** の「活動」欄(10 字へ切り詰め済み・空なら ``なし``)。v1/v2 は ``""``。
        until: **語彙 v3** の「まで」欄の解釈(``contract.Until``・空/読めない=DEFAULT 60 分)。
            v1/v2 は ``None``(欄が無い)。
        raw_activity / raw_until: 活動・まで欄の逐語(切り詰め前)。
        activity_truncated: 活動が 10 字を超えて切り詰めたか。
        target_hint: **語彙 v3** の「対象: 自宅/職場/学校」→ ``home``/``work``/``school``
            (``llm.undefined.TARGET_SURFACE_HINTS_V5``)。それ以外・v1/v2 は ``""``。
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
    activity: str = ""
    until: Until | None = None
    raw_activity: str = ""
    raw_until: str = ""
    activity_truncated: bool = False
    target_hint: str = ""

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
            is_role_action=is_role_action(word, vocab_version),
            dictionary_mapped=True,
        )


def _empty_result(
    errors: tuple[str, ...], vocab_version: str = DEFAULT_VOCAB_VERSION
) -> ParseResult:
    if str(vocab_version) == "v3":
        # v3 では 活動/まで を常に持たせる(読めない応答=活動なし・既定の持続)。
        return ParseResult(
            action=None,
            action_code=UNDEFINED_ACTION,
            target=NO_TARGET_VALUE,
            reason="",
            comment=NO_TARGET,
            format_ok=False,
            errors=errors,
            activity=NO_TARGET,
            until=DEFAULT_UNTIL,
        )
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
    text: str | None,
    vocab_version: str = DEFAULT_VOCAB_VERSION,
    landmarks: Mapping[str, int] | None = None,
) -> ParseResult:
    """2行形(および4行形)を寛容に読む。**例外を投げない**。

    Args:
        text: LLM の応答本文(``None`` や非文字列も受ける)。
        vocab_version: 語彙版(D-71 §3 F)。``"v2"`` で「食事」を語彙語として読み、
            段0 辞書の候補判定(``dictionary_candidate``)も辞書 v4 で引く。
            ``"v3"``(D-116)は 5 ラベル形(理由・行動・対象・活動・まで)を ``_parse_v3`` で読む。
            **既定 ``"v1"`` は 1 バイトも挙動が変わらない**。
        landmarks: 目印の「名 → POI 索引」表(C9b G6 a′)。``parse_target`` へ素通しする。
            ``None``(既定)では ``target.poi_id`` が常に ``None``=**現行のまま**。

    Returns:
        ``ParseResult``。

    Example:
        >>> r = parse_two_line("理由: 予定の時間\\n行動: 移動 対象: C-0117 ひと言: なし")
        >>> r.action, r.target.cell_index, r.format_ok
        ('移動', 117, True)
    """
    try:
        if str(vocab_version) == "v3":
            return _parse_v3(text, landmarks)
        return _parse(text, vocab_version, landmarks)
    except Exception as exc:  # pragma: no cover - 契約「例外を投げない」の最後の砦
        return _empty_result((f"internal:{type(exc).__name__}",), vocab_version)


def _parse(
    text: str | None,
    vocab_version: str = DEFAULT_VOCAB_VERSION,
    landmarks: Mapping[str, int] | None = None,
) -> ParseResult:
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
    positional_used = any(f.startswith("positional:") for f in filled)
    if filled:
        errors.extend(filled)
    if positional_used:
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
    target = parse_target(labels.get("対象"), landmarks)
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
    if not positional_used and not any(s in _NON_V0_SURFACES for s in surfaces):
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


def _parse_v3(text: str | None, landmarks: Mapping[str, int] | None = None) -> ParseResult:
    """**語彙 v3** の 5 ラベル形を読む(アジェンダ §1-2)。v1/v2 の ``_parse`` とは別の経路。

    手順は ``_parse`` と同じ(ラベル走査 → 位置引数 → 行動語 → 辞書候補 → 欄)で、違いは
    (i) 必須ラベルが ``CANONICAL_LABELS_V3`` (ii) 位置引数が ``_fill_positional_v3``
    (iii) ``strict_format_ok`` が正準表層だけの走査 (iv) 活動・まで・対象ヒントを返す、の 4 点。

    逐次ループ宣言(P4): ``_parse`` と同じ(ラベル出現数・語彙数 23 ぶん)。1呼=1回。
    """
    ver = "v3"
    if text is None:
        return _empty_result(("empty_output",), ver)
    if not isinstance(text, str):
        text = str(text)
    strict = bool(TWO_LINE_RE_V3.match(text.strip()))
    cleaned = _clean_text(text)
    if not cleaned:
        return _empty_result(("empty_output",), ver)

    labels, spans, surfaces = _scan_labels(cleaned, _LABEL_RE_V3, LABEL_ALIASES_V3)
    alias_surfaces = tuple(s for s in surfaces if LABEL_ALIASES_V3[s] != s)
    alias_used = bool(alias_surfaces)

    errors: list[str] = [f"missing_label:{lab}" for lab in CANONICAL_LABELS_V3 if lab not in labels]

    filled = _fill_positional_v3(labels)
    positional_used = any(f.startswith("positional:") for f in filled)
    if filled:
        errors.extend(filled)
    if positional_used:
        alias_surfaces = alias_surfaces + (POSITIONAL_SURFACE,)

    raw_action = labels.get("行動", "")
    action = find_action_word(raw_action, ver) if raw_action else None
    from_free_text = False
    if action is None and "行動" not in labels:
        action = find_action_word(_outside_labels(cleaned, spans), ver)
        from_free_text = action is not None
        if from_free_text:
            errors.append("action_from_free_text")
    dictionary_candidate: str | None = None
    if action is None:
        errors.append("unknown_action_word")
        if raw_action:
            dictionary_candidate = map_synonym(raw_action, None, ver)[0]

    # 第275 親の決め #4: 行動=なし の応答は対象ラベルを省いてよい(対象=なし・診断は残す)。
    if action == ACTION_WORD_NONE and "対象" not in labels:
        labels["対象"] = NO_TARGET
        errors = ["target_omitted" if e == "missing_label:対象" else e for e in errors]
    target = parse_target(labels.get("対象"), landmarks, ver)
    target_hint = (
        target_surface_hint(target.raw, ver) if target.kind is TargetKind.ITEM_CATEGORY else ""
    )
    raw_reason = labels.get("理由", "")
    raw_comment = labels.get("ひと言", NO_TARGET)
    raw_activity = labels.get("活動", "")
    raw_until = labels.get("まで", "")
    reason = raw_reason[:REASON_MAX_CHARS]
    comment = raw_comment[:COMMENT_MAX_CHARS]
    activity = raw_activity[:ACTIVITY_MAX_CHARS]
    reason_truncated = len(raw_reason) > REASON_MAX_CHARS
    comment_truncated = len(raw_comment) > COMMENT_MAX_CHARS
    activity_truncated = len(raw_activity) > ACTIVITY_MAX_CHARS
    if reason_truncated:
        errors.append("reason_truncated")
    if comment_truncated:
        errors.append("comment_truncated")
    if activity_truncated:
        errors.append("activity_truncated")

    format_ok = (
        all(lab in labels for lab in CANONICAL_LABELS_V3)
        and action is not None
        and not from_free_text
    )
    # strict(v3)= 5 ラベルを**正準表層だけ**で・位置引数なし(アジェンダ §1-2)。
    # 対象を省いた「行動: なし」は 5 ラベルが揃っていない=strict は偽(定義を動かさない)。
    if positional_used or "target_omitted" in errors:
        strict_format_ok = False
    else:
        labels_s, _, _ = _scan_labels(cleaned, _LABEL_RE_STRICT_V3, _STRICT_LABELS_V3)
        strict_format_ok = all(lab in labels_s for lab in CANONICAL_LABELS_V3) and (
            find_action_word(labels_s.get("行動", ""), ver) is not None
        )
    return ParseResult(
        action=action,
        action_code=action_code_of(action, ver) if action else UNDEFINED_ACTION,
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
        is_role_action=bool(action) and is_role_action(action, ver),
        action_from_free_text=from_free_text,
        strict_format_ok=strict_format_ok,
        alias_used=alias_used,
        alias_surfaces=alias_surfaces,
        positional_used=positional_used,
        dictionary_candidate=dictionary_candidate,
        labels=labels,
        activity=activity or NO_TARGET,
        until=parse_until(raw_until),
        raw_activity=raw_activity,
        raw_until=raw_until,
        activity_truncated=activity_truncated,
        target_hint=target_hint,
    )


def _fill_positional_v3(labels: dict[str, str]) -> tuple[str, ...]:
    """**語彙 v3** の位置引数の回収(``_fill_positional`` の 5 ラベル版・expedient)。

    規則は v1 の一般化: 在る欄(行動を含む)の値の **2 トークン目以降**は、その欄の**直後に続く
    欠けた欄**へ順に溢れた値とみなす。途中の欄は 1 トークンずつ、**最後の欄(まで)は残り全部**
    (v1 の ひと言 と同じ)。溢れの先が在る欄に当たったら残りは捨てる(v1 と同じ)。

    - 「行動: 移動 自宅 散歩 30分」→ 対象=自宅・活動=散歩・まで=30分
    - 「行動: 移動 対象: 自宅 散歩 30分」→ 活動=散歩・まで=30分(対象の値から溢れた形)
    - 「行動: 移動 自宅」→ 対象=自宅・**活動=なし・まで=空**(``activity_defaulted``/
      ``until_defaulted``=v1 の ``comment_defaulted`` と同じく、位置で読んだ応答だけ既定へ倒す)

    安全弁(v1 と同じ): 行動ラベルが在り、その**先頭トークン**に行動語があるときだけ働く。
    行動の余りが無く対象ラベルも無ければ何もしない(=欄落ちは欄落ち)。未知のラベル
    (「語+コロン」)は値として読まず ``unknown_label:<表層>`` を残す(D-113 ①)。

    Args:
        labels: ``_scan_labels`` が作った表。**破壊的に更新する**。

    Returns:
        補った欄の診断名(``positional:活動`` 等)。空なら未発動。

    逐次ループ宣言(P4): 欄数(4)× 行動欄のトークン数(数個)。1呼=1回。
    """
    if "行動" not in labels:
        return ()
    fields = _POSITIONAL_FIELDS_V3
    if all(f in labels for f in fields):
        return ()
    tokens = labels["行動"].split()
    if not tokens:
        return ()
    action_all = find_action_word(labels["行動"], "v3")
    if action_all is not None and find_action_word(tokens[0], "v3") != action_all:
        return ()  # 行動語が先頭トークンに無い=位置で読める形ではない
    if not tokens[1:] and "対象" not in labels:
        return ()  # 余りが無い=ただの欄落ち(ここでは補わない)
    filled: list[str] = []
    unknown: list[str] = []
    seq = ("行動", *fields)
    last = seq[-1]
    for idx, src in enumerate(seq):
        if src not in labels:
            continue
        targets: list[str] = []
        for f in seq[idx + 1 :]:
            if f in labels:
                break
            targets.append(f)
        if not targets:
            continue
        src_tokens = tokens if src == "行動" else labels[src].split()
        overflow = _drop_unknown_labels(list(src_tokens[1:]), unknown)
        took = False
        for f in targets:
            if not overflow:
                break
            if f == last:
                labels[f] = " ".join(overflow)
                overflow = []
            else:
                labels[f] = overflow.pop(0)
                overflow = _drop_unknown_labels(overflow, unknown)
            filled.append(f"positional:{f}")
            took = True
        if took:
            labels[src] = src_tokens[0]  # 行動は語彙語だけ・対象/活動は先頭の値だけ
    if not filled:
        return tuple(f"unknown_label:{u}" for u in unknown)
    if "活動" not in labels:
        labels["活動"] = NO_TARGET
        filled.append("activity_defaulted")
    if "まで" not in labels:
        labels["まで"] = ""
        filled.append("until_defaulted")
    filled.extend(f"unknown_label:{u}" for u in unknown)
    return tuple(filled)


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
    # D-113 ①: 別名表に無い「語+コロン」のトークン(未知のラベル)は**値ではない**。読み飛ばして
    # 診断に残す(以前は「目標:」がそのまま対象の値になっていた)。
    unknown: list[str] = []
    rest = _drop_unknown_labels(rest, unknown)
    if "対象" not in labels and rest:
        labels["対象"] = rest.pop(0)
        filled.append("positional:対象")
        rest = _drop_unknown_labels(rest, unknown)
    if "ひと言" not in labels and rest:
        labels["ひと言"] = " ".join(rest)
        rest = []
        filled.append("positional:ひと言")
    if filled:
        labels["行動"] = tokens[0]  # ``raw_action`` は語彙語だけにする
    elif unknown:
        # 未知のラベルの後ろに値が無い(「行動: 移動 目安:」)= 欄落ちとして扱う(補わない)。
        return tuple(f"unknown_label:{u}" for u in unknown)
    filled.extend(f"unknown_label:{u}" for u in unknown)
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


def _drop_unknown_labels(rest: list[str], unknown: list[str]) -> list[str]:
    """先頭に並ぶ未知のラベル(「目安:」型)を落として表層を ``unknown`` に積む(D-113 ①)。

    逐次ループ宣言(P4): 行動欄のトークン数ぶん(数個)。1呼=1回。
    """
    while rest and _UNKNOWN_LABEL_TOKEN_RE.match(rest[0]):
        unknown.append(rest.pop(0).rstrip(":："))
    return rest


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
