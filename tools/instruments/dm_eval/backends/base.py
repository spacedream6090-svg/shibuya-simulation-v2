# -*- coding: utf-8 -*-
"""dm_eval.backends.base — モデルの当て口の抽象(〔11-01 段 1 の 3〕判断モデルの候補と (G) の比べ・重みは取らない)。

2 つの抽象
    - ``ChoiceBackend``: 文(prompt)に続く候補の文字列(continuation)の logprob を返す口。分布はこちら側で作る
      (``LogprobChoiceScorer``=推論の形 Choice/Score)。
    - ``FreeTextBackend``: 文に続く自由記述を返す口。候補に当てるのはこちら側(``FreeTextScorer``=推論の形 Noul)。

推論の形は差し替えられる(答申 R-125 が候補ごとの形を決める=ここでは決めない)
    ``ChoiceForm``=(形の見出し・何に logprob を付けるか・まとめ方・答えの頭の文・包み方・「その他」を入れるか・後ろに
    付ける文)。既定の 4 つ(``FORMS``):
    - ``choice_number``(Choice): 提示の番号の文字列(「3」)の logprob の和。
    - ``choice_number_first``(Choice): 番号の 1 トークン目の logprob(R-83 §5 の (G)「1 トークン目の確率」の形)。
    - ``score_text_sum``(Score): 候補の見せ方の文の logprob の和。
    - ``score_text_mean``(Score): 同じく 1 トークンあたりの平均(長さで割る)。
    分布=まとめた値の softmax(「その他」は番号 n+1・見せ方は ``OTHER_TEXT``)。

日本語での破綻(表の列 ``breakdown_rate``・〔検収 中 2・低 5・問い 4〕)
    - Noul(``FreeTextScorer``): 自由記述を ``match_free_text``(丁寧語と活用を正規化した後)で当て、どの候補にも
      「その他」にも当たらない答え=破綻。破綻の答えは分布では「その他」に確率 1 を置くが、記録の数え方は分ける
      (``trace`` の印 ``miss`` と ``other``=明示の「その他」)。表の「その他の率」は Noul の行では明示の「その他」だけ。
    - Choice/Score(``LogprobChoiceScorer``): 提示の候補(「その他」を含む)の文字列の確率の和(まとめる前の
      logprob の和の exp・1 トークン目の形は 1 トークン目の exp)が下限 ``MASS_FLOOR``=1e-3 未満の件=破綻。
      切り出しの不一致(``TokenBoundaryError``)も破綻に数え、その件は失敗として上へ投げる(黙って別のトークンを
      使わない)。

当て口は作った後に欄を付け替えない(``judge.Scorer`` の守り=DM9)。``trace`` は箱の中身だけ増える。重み(``backend``)
は当て口の間で共有してよい(厳密モードの検査は当て口を作り直すが、重みは 1 回だけ読む=重みは変えない値)。

expedient(未リサーチ・R-125 で決める)
    - 答えの頭の文 ``cue`` の既定「答え: 」・包み方の既定 ``plain``(文+改行+cue)・``chatml_nothink`` は Qwen3 の
      考えない形の頭(``<think>`` の空の組)を手で書いた物(chat template を tokenizer から読む形に替えるのは R-125)。
    - 番号の形で 10 以上の番号は桁ごとのトークンになり得る(Qwen 系は数字を 1 桁ずつ)=``choice_number_first`` は
      候補が 9 個以下の場面でだけ意味がある。
    - 破綻の下限 1e-3(親の指示 11-01 の値・根拠の原典なし)。
    - 自由記述の当て方 ``match_free_text``(下の説明)と活用の表(五段・一段・来る・する・否定)は自前。
逐次ループ宣言: 候補の数(≤ 20)× 件の数。
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Final, Mapping, Sequence

import dm_eval  # noqa: F401
from dm_eval.judge import ROLE_CANDIDATE, Scorer, ScoreFailed
from dm_eval.situations import Situation
from shibuya.engine.decision.port import OTHER_ID, OTHER_TEXT, Candidate

__all__ = [
    "FORM_CHOICE", "FORM_SCORE", "FORM_NOUL", "FORM_LABELS", "MASS_FLOOR", "BackendUnavailable", "BackendError",
    "TokenBoundaryError", "ChoiceBackend", "FreeTextBackend", "WRAPS", "wrap_prompt", "ChoiceForm", "FORMS",
    "softmax_dist", "LogprobChoiceScorer", "FreeTextScorer", "match_free_text", "slice_continuation", "verb_forms",
    "normalize_text", "negative_forms", "NEGATION_KINDS", "NEGATION_OF", "kanji_number", "BackendHTTPError", "BackendTimeout",
]

FORM_CHOICE: Final[str] = "Choice"
FORM_SCORE: Final[str] = "Score"
FORM_NOUL: Final[str] = "Noul"
#: 推論の形の見出し(R-J の Choice/Score/Noul)。
FORM_LABELS: Final[tuple[str, ...]] = (FORM_CHOICE, FORM_SCORE, FORM_NOUL)
#: logprob の形の破綻の下限(候補に当たる確率の和がこれ未満=破綻・親の指示 11-01・expedient)。
MASS_FLOOR: Final[float] = 1e-3
_NEG_INF: Final[float] = float("-inf")


class BackendError(ScoreFailed):
    """口の後ろの物の答えが読めない(形の違い)。``evaluate`` は場面ごとに捕まえて失敗と記録する。

    記録に残すのは型の名と短い分類 ``category`` だけ(例外の文は入力や艦隊の答えを含み得るので写さない=〔再検収 新 低 1〕)。
    """

    category = "parse"


class BackendUnavailable(BackendError):
    """口の後ろの物(transformers・torch・艦隊)が手元に無い(GPU の後・pip は許可の後)。"""

    category = "unavailable"


class BackendHTTPError(BackendError):
    """艦隊への HTTP の失敗(200 でない・接続の失敗)。"""

    category = "http"


class BackendTimeout(BackendError):
    """艦隊の答えが時間内に来ない。"""

    category = "timeout"


class TokenBoundaryError(BackendError):
    """候補の文字列を、文の後ろのトークンから字面どおりに切り出せない(結合・位置のずれ)=破綻に数える。"""

    category = "boundary"


class ChoiceBackend:
    """候補の文字列の logprob を返す口(実装は ``continuation_logprobs`` を書く)。"""

    name: str = ""
    uses_gpu: bool = True

    def continuation_logprobs(self, prompt: str, continuations: Sequence[str]) -> list[tuple[float, ...]]:
        """各候補の文字列のトークンごとの logprob(自然対数・文 ``prompt`` に続けたとき)。"""
        raise NotImplementedError

    def first_token_logprobs(self, prompt: str, continuations: Sequence[str]) -> list[float]:
        """各候補の文字列の 1 トークン目の logprob(既定は ``continuation_logprobs`` の頭)。"""
        return [float(r[0]) if r else _NEG_INF for r in self.continuation_logprobs(prompt, continuations)]

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "uses_gpu": self.uses_gpu}


class FreeTextBackend:
    """自由記述を返す口(実装は ``generate`` を書く)。"""

    name: str = ""
    uses_gpu: bool = True

    def generate(self, prompt: str) -> str:
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "uses_gpu": self.uses_gpu}


#: 包み方(``plain``=文+改行・``chatml_nothink``=Qwen3 の考えない形の頭を手で書いた物=expedient)。
WRAPS: Final[tuple[str, ...]] = ("plain", "chatml_nothink")


def wrap_prompt(text: str, wrap: str = "plain") -> str:
    """判断の文(DM4 の版)を口に渡す形に包む(答えの頭 ``cue`` はこの後ろに付ける)。"""
    if wrap == "plain":
        return f"{text}\n"
    if wrap == "chatml_nothink":
        return f"<|im_start|>user\n{text}<|im_end|>\n<|im_start|>assistant\n<think>\n\n</think>\n\n"
    raise ValueError(f"wrap は {WRAPS} のどれか(いま {wrap!r})")


_TARGETS: Final[tuple[str, ...]] = ("number", "text")
_REDUCES: Final[tuple[str, ...]] = ("sum", "mean", "first")


@dataclass(frozen=True)
class ChoiceForm:
    """推論の形 1 つ(差し替えられる=R-125 が候補ごとに決める)。"""

    name: str
    form: str
    target: str
    reduce: str
    cue: str = "答え: "
    wrap: str = "plain"
    include_other: bool = True
    suffix: str = ""

    def __post_init__(self) -> None:
        if self.form not in (FORM_CHOICE, FORM_SCORE):
            raise ValueError(f"ChoiceForm.form は {FORM_CHOICE} か {FORM_SCORE}(いま {self.form!r})")
        if self.target not in _TARGETS or self.reduce not in _REDUCES or self.wrap not in WRAPS:
            raise ValueError(f"target は {_TARGETS}・reduce は {_REDUCES}・wrap は {WRAPS} のどれか")

    def prompt(self, text: str) -> str:
        return wrap_prompt(text, self.wrap) + self.cue

    def continuations(self, presented: Sequence[Candidate]) -> list[tuple[str, str]]:
        """(候補の id, logprob を付ける文字列) の並び(番号の順+「その他」)。"""
        pres = sorted(presented, key=lambda c: int(c.number or 0))
        if any(c.number is None for c in pres):
            raise ValueError("提示の番号の無い候補(``situations.orders`` の 1 通りを渡す)")
        if self.target == "number":
            out = [(c.id, f"{c.number}{self.suffix}") for c in pres]
            other = f"{len(pres) + 1}{self.suffix}"
        else:
            out = [(c.id, f"{c.text}{self.suffix}") for c in pres]
            other = f"{OTHER_TEXT}{self.suffix}"
        if self.include_other:
            out.append((OTHER_ID, other))
        return out

    def reduce_lps(self, lps: Sequence[float]) -> float:
        if not lps:
            raise BackendError("候補の文字列のトークンが 0 個")
        if self.reduce == "mean":
            return float(sum(lps)) / len(lps)
        if self.reduce == "first":
            return float(lps[0])
        return float(sum(lps))

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "form": self.form, "target": self.target, "reduce": self.reduce, "cue": self.cue,
                "wrap": self.wrap, "include_other": self.include_other, "suffix": self.suffix}


FORMS: Final[Mapping[str, ChoiceForm]] = MappingProxyType({
    "choice_number": ChoiceForm("choice_number", FORM_CHOICE, "number", "sum"),
    "choice_number_first": ChoiceForm("choice_number_first", FORM_CHOICE, "number", "first"),
    "score_text_sum": ChoiceForm("score_text_sum", FORM_SCORE, "text", "sum"),
    "score_text_mean": ChoiceForm("score_text_mean", FORM_SCORE, "text", "mean"),
})


def softmax_dist(scores: Mapping[str, float]) -> dict[str, float]:
    """まとめた logprob → 確率(最大を引いてから exp・-inf は 0)。全部 -inf なら ``BackendError``。"""
    vals = {k: float(v) for k, v in scores.items()}
    if any(math.isnan(v) or v == float("inf") for v in vals.values()):
        raise BackendError("logprob に NaN か +inf")
    finite = [v for v in vals.values() if v != _NEG_INF]
    if not finite:
        raise BackendError("候補の logprob が全部 -inf")
    m = max(finite)
    w = {k: (math.exp(v - m) if v != _NEG_INF else 0.0) for k, v in vals.items()}
    s = sum(w.values())
    return {k: v / s for k, v in w.items()}


def slice_continuation(starts: Sequence[int], lps: Sequence[float | None], begin: int, end: int, *,
                       texts: Sequence[str | None] | None = None, expected: str | None = None) -> tuple[float, ...]:
    """トークンの頭の文字位置 ``starts`` と logprob の列から、文字の範囲 [begin, end) に頭がある物を切り出す。

    範囲の最初のトークンの頭が ``begin`` でない(文の末尾と候補の頭が 1 トークンに結合した)か、〔検収 中 3〕
    ``texts`` と ``expected`` を渡したとき切り出したトークンの文字列の連結が ``expected``(=候補の文字列)と違えば
    ``TokenBoundaryError``(黙って別のトークンを使わない)。
    """
    if len(starts) != len(lps) or (texts is not None and len(texts) != len(lps)):
        raise BackendError("トークンの位置・文字列・logprob の数が違う")
    idx = [i for i, st in enumerate(starts) if begin <= int(st) < end]
    if not idx:
        raise TokenBoundaryError("候補の文字列に頭のあるトークンが無い")
    if int(starts[idx[0]]) != begin:
        raise TokenBoundaryError(f"候補の頭が文の末尾と結合した(位置 {starts[idx[0]]} ≠ {begin})")
    if idx != list(range(idx[0], idx[-1] + 1)):
        raise BackendError("トークンの位置が昇順でない")
    if texts is not None and expected is not None:
        got = "".join(str(texts[i] or "") for i in idx)
        if got != expected:
            raise TokenBoundaryError(f"切り出したトークンの字面 {got!r} が候補 {expected!r} と違う")
    out = []
    for i in idx:
        v = lps[i]
        if v is None:
            raise BackendError("候補のトークンの logprob が空")
        out.append(float(v))
    return tuple(out)


class _Traced:
    """当て口の記録の箱(``trace``)の読み口(``trace_reset``・``trace_summary`` を ``evaluate`` が読む)。"""

    trace: list[tuple[str, float | None]]

    def trace_reset(self) -> None:
        self.trace.clear()


class LogprobChoiceScorer(_Traced, Scorer):
    """``ChoiceBackend`` と ``ChoiceForm`` を組んだ当て口(推論の形 Choice/Score)。"""

    reads_text = True

    def __init__(self, backend: ChoiceBackend, form: ChoiceForm | str = "choice_number", *, name: str | None = None,
                 role: str = ROLE_CANDIDATE, length: str = "short", mass_floor: float = MASS_FLOOR) -> None:
        cf = FORMS[form] if isinstance(form, str) else form
        if length not in ("short", "long"):
            raise ValueError("length は short か long")
        self.backend = backend
        self.choice_form = cf
        self.name = name or f"{backend.name}:{cf.name}"
        self.role = role
        self.form = cf.form
        self.uses_gpu = bool(backend.uses_gpu)
        self.prompt_length = length
        self.mass_floor = float(mass_floor)
        self.trace = []
        self.meta = MappingProxyType({"backend": MappingProxyType(dict(backend.describe())),
                                      "form": MappingProxyType(cf.describe()), "length": length,
                                      "mass_floor": self.mass_floor})
        super().__init__()

    def _score(self, situation: Situation, candidates: tuple[Candidate, ...], text: str | None
               ) -> Mapping[str, float]:
        if text is None:
            raise ValueError(f"{self.name}: 文(DM4 の版)が要る当て口")
        cf = self.choice_form
        prompt = cf.prompt(text)
        pairs = cf.continuations(candidates)
        conts = [c for _cid, c in pairs]
        try:
            if cf.reduce == "first":
                raw = [float(x) for x in self.backend.first_token_logprobs(prompt, conts)]
                scores = raw
            else:
                rows = self.backend.continuation_logprobs(prompt, conts)
                if len(rows) != len(conts):
                    raise BackendError("候補の数と logprob の行の数が違う")
                raw = [float(sum(r)) for r in rows]
                scores = [cf.reduce_lps(r) for r in rows]
        except TokenBoundaryError:
            self.trace.append(("boundary", None))
            raise
        mass = float(sum(math.exp(v) for v in raw if v != _NEG_INF))
        self.trace.append(("ok" if mass >= self.mass_floor else "low_mass", mass))
        return softmax_dist({cid: s for (cid, _c), s in zip(pairs, scores)})

    def trace_summary(self) -> dict[str, Any]:
        n = len(self.trace)
        low = sum(1 for k, _m in self.trace if k == "low_mass")
        boundary = sum(1 for k, _m in self.trace if k == "boundary")
        masses = sorted(m for _k, m in self.trace if m is not None)
        bd = low + boundary
        return {"n": n, "breakdown": bd, "breakdown_rate": bd / n if n else None, "low_mass": low,
                "boundary": boundary, "mass_floor": self.mass_floor,
                "mass_median": masses[len(masses) // 2] if masses else None,
                "definition": "候補(その他を含む)の文字列の確率の和が下限未満か、切り出しが字面と違った件の率"}


# ---------------------------------------------------------------------------------------------- 自由記述の当て方
_INT: Final[re.Pattern[str]] = re.compile(r"[0-9]+")
#: 番号でない数(値段・数量・時刻・順位)の印=数字の後ろ(空白を飛ばして)に続く語。
_UNIT_AFTER: Final[tuple[str, ...]] = ("円", "個", "つ", "時", "分", "人", "本", "枚", "回", "歳", "%", "メートル", "袋",
                                       "杯", "日", "月", "年", "万", "千", ",", "倍", "位", "点", "割", "度", "キロ",
                                       "グラム", "パック", "箱", "皿", "品")
_OTHER_WORDS: Final[tuple[str, ...]] = (OTHER_TEXT, "その他")
#: 区切りの字(句の中の内容の語を分ける)。
_PARTICLES: Final[re.Pattern[str]] = re.compile(r"[をにでのへとはが、。,.!?！？「」()()\s]+|ずに")
_PHRASE_SPLIT: Final[re.Pattern[str]] = re.compile(r"[()()、。]+")
#: 五段の終わりの字 → ます形の字・た形・て形・否定(ない形)の字。
_GODAN: Final[Mapping[str, tuple[str, str, str, str]]] = MappingProxyType({
    "う": ("い", "った", "って", "わ"), "く": ("き", "いた", "いて", "か"), "ぐ": ("ぎ", "いだ", "いで", "が"),
    "す": ("し", "した", "して", "さ"), "つ": ("ち", "った", "って", "た"), "ぬ": ("に", "んだ", "んで", "な"),
    "ぶ": ("び", "んだ", "んで", "ば"), "む": ("み", "んだ", "んで", "ま"), "る": ("り", "った", "って", "ら"),
})
_NEG_TO_U: Final[Mapping[str, str]] = MappingProxyType({v[3]: k for k, v in _GODAN.items()})


#: 漢数字(〔再検収 新 低 2〕数の助数詞の前だけを数に読む=「一緒」「一番」は読まない)。
_KANJI_DIGITS: Final[Mapping[str, int]] = MappingProxyType(
    {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9})
_COUNTERS: Final[str] = "つ|個|本|枚|袋|杯|パック|箱|皿|品|点|人分"
_KANJI_NUM: Final[re.Pattern[str]] = re.compile(r"([一二三四五六七八九十]+)(?=" + _COUNTERS + ")")
#: 数の後ろの「個」は「つ」と同じに読む(候補の文は 9 以下を「つ」で書く)。
_KO: Final[re.Pattern[str]] = re.compile(r"([0-9]+)個")


def kanji_number(text: str) -> int | None:
    """漢数字の 1〜99(一・十・二十三 など)→ 数。読めなければ None。"""
    t = str(text)
    if not t or any(ch not in _KANJI_DIGITS and ch != "十" for ch in t) or t.count("十") > 1:
        return None
    if "十" not in t:
        return _KANJI_DIGITS[t] if len(t) == 1 else None
    head, _sep, tail = t.partition("十")
    if len(head) > 1 or len(tail) > 1:
        return None
    return (_KANJI_DIGITS[head] if head else 1) * 10 + (_KANJI_DIGITS[tail] if tail else 0)


def _kanji_to_digits(text: str) -> str:
    def rep(m: re.Match[str]) -> str:
        v = kanji_number(m.group(1))
        return m.group(1) if v is None else str(v)

    return _KANJI_NUM.sub(rep, text)


def normalize_text(text: str) -> str:
    """NFKC(全角の数字と英字を半角に)+助数詞の前の漢数字を数に+数の後ろの「個」を「つ」に+空白を除く。"""
    t = _kanji_to_digits(unicodedata.normalize("NFKC", str(text or "")))
    return _KO.sub(lambda m: m.group(1) + "つ", re.sub(r"\s+", "", t))


def _is_kanji(ch: str) -> bool:
    return "一" <= ch <= "鿿" or ch in "々"


def _is_hiragana(ch: str) -> bool:
    return "ぁ" <= ch <= "ゟ"


def _verb_word(phrase: str) -> str | None:
    """句の末尾の動詞の語(漢字の並び+かなの尾・かなだけの動詞は最後の区切りの後)。動詞で終わらなければ None。"""
    p = phrase
    if not p or not _is_hiragana(p[-1]):
        return None
    i = len(p)
    while i > 0 and _is_hiragana(p[i - 1]):
        i -= 1
    tail = p[i:]
    if i > 0 and _is_kanji(p[i - 1]) and len(tail) <= 3 and tail[0] not in "をにでへとはが":
        j = i
        while j > 0 and _is_kanji(p[j - 1]):
            j -= 1
        return p[j:]
    m = list(re.finditer(r"[をにでへとはが]|ずに", tail))
    word = tail[m[-1].end():] if m else tail
    return word if len(word) >= 2 else None


def verb_forms(word: str) -> frozenset[str]:
    """動詞の語(辞書形か「〜ない」)→ 当たりの形の集合(五段と一段の両方の読みを足す=多めに作る)。

    辞書形(肯定)の語には肯定の形(丁寧・過去・て形)だけを作り、否定の形は入れない(〔再検収 新 中 1〕)。
    「〜ない」の語(否定の候補の文)には否定の形(〜ません・〜なかった・〜ないです)を作る。
    """
    w = str(word)
    forms = {w}
    if w.endswith("ない") and len(w) > 2:  # 否定: 行かない → 行きません・行かなかった・やめない → やめません
        stem = w[:-2]
        forms |= {stem + "なかった", stem + "ません", stem + "ないです"}
        if stem[-1:] in _NEG_TO_U:
            forms.add(stem[:-1] + _GODAN[_NEG_TO_U[stem[-1]]][0] + "ません")
        return frozenset(forms)
    # 来る・くる・する(連用の字・否定の字)
    for head, ren, neg in (("来る", "来", "来"), ("くる", "き", "こ"), ("する", "し", "し")):
        if w.endswith(head):
            b = w[:-len(head)]
            forms |= {b + ren + "ます", b + ren + "ました", b + ren + "た", b + ren + "て"}
            return frozenset(forms)
    last = w[-1:]
    if last not in _GODAN:
        return frozenset(forms)
    b = w[:-1]
    masu, ta, te, _neg = _GODAN[last]
    forms |= {b + masu + "ます", b + masu + "ました", b + ta, b + te}
    if w.endswith("行く"):
        forms |= {b + "った", b + "って"}
    if last == "る":  # 一段の読み(やめる → やめます・やめた)
        forms |= {b + "ます", b + "ました", b + "た", b + "て"}
    return frozenset(forms)


#: 否定の意味の候補の語(否定の答え=「買いません」「もう来ない」を当てる先)。
NEGATION_KINDS: Final[frozenset[str]] = frozenset({"buy_skip", "price_skip", "no_revisit"})
#: 肯定の候補の語 → その否定に当たる候補の語(この表に無い語の否定=「尋ねない」は当たらない=破綻)。
NEGATION_OF: Final[Mapping[str, tuple[str, ...]]] = MappingProxyType({
    "購入": ("buy_skip", "price_skip"),
    "revisit": ("no_revisit",),
})


def negative_forms(word: str) -> frozenset[str]:
    """肯定の動詞の語(辞書形)→ 否定の形(〜ない・〜ません・〜なかった・〜ませんでした・〜ず・〜て(い)ない)。

    「〜ない」で終わる語(すでに否定)は空。動詞として読めない語も空。
    """
    w = str(word)
    if w.endswith("ない"):
        return frozenset()
    for head, ren, neg in (("来る", "来", "来"), ("くる", "き", "こ"), ("する", "し", "し")):
        if w.endswith(head):
            b = w[:-len(head)]
            nb = b + ("せ" if head == "する" else neg)
            return frozenset({b + neg + "ない", b + neg + "なかった", b + ren + "ません", b + ren + "ませんでした",
                              nb + "ず", b + ren + "てない", b + ren + "ていない"})
    last = w[-1:]
    if last not in _GODAN:
        return frozenset()
    b = w[:-1]
    masu, _ta, te, neg = _GODAN[last]
    te_form = b + ("って" if w.endswith("行く") else te)
    out = {b + neg + "ない", b + neg + "なかった", b + neg + "ず", b + masu + "ません", b + masu + "ませんでした",
           te_form + "ない", te_form + "いない"}
    if last == "る":  # 一段の読み(やめる → やめない・やめません)
        out |= {b + "ない", b + "なかった", b + "ず", b + "ません", b + "ませんでした", b + "てない", b + "ていない"}
    return frozenset(out)


def _negated(out_norm: str, cand_text: str) -> bool:
    """候補の見せ方の文の肯定の動詞が、答えの中で否定の形で出ているか。"""
    for ph in _PHRASE_SPLIT.split(normalize_text(cand_text)):
        vw = _verb_word(ph) if ph else None
        if vw and any(f in out_norm for f in negative_forms(vw)):
            return True
    return False


def _phrase_keys(text: str) -> list[tuple[frozenset[str] | None, str, tuple[str, ...]]]:
    """候補の見せ方の文 → 句ごとの(動詞の形の集合 or None・句・内容の語)。"""
    out = []
    for ph in _PHRASE_SPLIT.split(normalize_text(text)):
        if not ph:
            continue
        vw = _verb_word(ph)
        rest = ph[:len(ph) - len(vw)] if vw else ph
        segs = tuple(s for s in _PARTICLES.split(rest) if s)
        out.append((verb_forms(vw) if vw else None, ph, segs))
    return out


def _text_score(out_norm: str, cand_text: str) -> int:
    """自由記述(正規化済み)と候補の見せ方の文の当たりの強さ(0=当たらない)。句ごとの最大。"""
    best = 0
    for forms, ph, segs in _phrase_keys(cand_text):
        if forms is not None:
            if any(f in out_norm for f in forms):
                best = max(best, 1 + sum(1 for s in segs if s in out_norm))
        elif ph in out_norm:
            best = max(best, 1 + len(segs))
    return best


def _answer_numbers(line: str, n: int) -> list[int]:
    """行の中の、番号として読める 1〜n+1 の整数(後ろに単位・順位の語が続く物は読まない)。"""
    found = []
    for m in _INT.finditer(line):
        after = line[m.end():].lstrip()
        if after.startswith(_UNIT_AFTER):
            continue
        k = int(m.group())
        if 1 <= k <= n + 1:
            found.append(k)
    return found


def match_free_text(output: str, presented: Sequence[Candidate]) -> str | None:
    """自由記述 → 候補の id(「その他」は ``OTHER_ID``)・当たらなければ ``None``(=破綻)。

    順: (1) 後ろの行から、番号として読める整数(単位・順位の語が空白を挟んで続く物は除く・全角は NFKC で半角・
    助数詞の前の漢数字は数に読む) (2) 否定の答え(肯定の候補の動詞が否定の形で出る=「買いません」「もう来ない」)
    は、否定された候補の語に対応する否定の候補(``NEGATION_OF``=購入 → buy_skip・price_skip・revisit → no_revisit)
    のうち、見せ方の文で当たる物が 1 つならそれ・無ければ対応する否定の候補がちょうど 1 つならそれ・どちらでもなければ
    当たらない(肯定の候補には当てない・対応の無い語の否定=「尋ねない」も当たらない) (3) 見せ方の文の句ごとに、末尾の
    動詞の当たりの形(肯定は丁寧・過去・て形・否定の候補の文は否定の形)のどれかが答えにあれば当たり、句の内容の語が
    答えにある数だけ強い=最も強い候補が 1 つだけのとき (4) 語彙の語(「なし」と ASCII の名を除く)がちょうど 1 つの
    候補に当たる (5) 「その他」の語 (6) 当たらない。
    """
    pres = sorted(presented, key=lambda c: int(c.number or 0))
    n = len(pres)
    raw = _kanji_to_digits(unicodedata.normalize("NFKC", str(output or "")))
    for line in reversed([ln for ln in raw.split("\n") if ln.strip()]):  # 逐次ループ宣言: 行の数
        found = _answer_numbers(line, n)
        if found:
            k = found[-1]
            return OTHER_ID if k == n + 1 else pres[k - 1].id
    norm = normalize_text(raw)
    negated = {c.id: c.kind for c in pres if c.kind not in NEGATION_KINDS and _negated(norm, c.text)}
    positive = [c for c in pres if c.kind not in NEGATION_KINDS and c.id not in negated
                and _text_score(norm, c.text) > 0]
    if negated and not positive:  # 否定の答え(ほかの肯定の候補にも当たらない=「迷わずに買います」は肯定の側)
        targets = {k for kind in negated.values() for k in NEGATION_OF.get(kind, ())}
        negs = [c for c in pres if c.kind in targets]
        nsc = [(_text_score(norm, c.text), c.id) for c in negs]
        ntop = max((x for x, _i in nsc), default=0)
        hit = [i for x, i in nsc if x == ntop and x > 0]
        if len(hit) == 1:
            return hit[0]
        return negs[0].id if len(negs) == 1 and ntop == 0 else None
    scores = [(0 if c.id in negated else _text_score(norm, c.text), c.id) for c in pres]
    top = max((s for s, _i in scores), default=0)
    if top > 0:
        best = [i for s, i in scores if s == top]
        return best[0] if len(best) == 1 else None
    by_kind: dict[str, list[str]] = {}
    for c in pres:
        if c.kind != "なし" and not c.kind.isascii():
            by_kind.setdefault(c.kind, []).append(c.id)
    khits = [ids for k, ids in by_kind.items() if k in norm]
    if len(khits) == 1 and len(khits[0]) == 1:
        return khits[0][0]
    if any(normalize_text(w) in norm for w in _OTHER_WORDS):
        return OTHER_ID
    return None


class FreeTextScorer(_Traced, Scorer):
    """``FreeTextBackend`` の自由記述を候補に当てる当て口(推論の形 Noul)。当たらない答え(破綻)は分布では「その他」に
    確率 1 を置くが、``trace`` で明示の「その他」と分けて数える(〔検収 低 5〕)。"""

    reads_text = True
    form = FORM_NOUL

    def __init__(self, backend: FreeTextBackend, *, name: str | None = None, role: str = ROLE_CANDIDATE,
                 cue: str = "", wrap: str = "plain", length: str = "long") -> None:
        if wrap not in WRAPS:
            raise ValueError(f"wrap は {WRAPS} のどれか")
        if length not in ("short", "long"):
            raise ValueError("length は short か long")
        self.backend = backend
        self.cue = cue
        self.wrap = wrap
        self.name = name or f"{backend.name}:noul"
        self.role = role
        self.uses_gpu = bool(backend.uses_gpu)
        self.prompt_length = length
        self.trace = []
        self.meta = MappingProxyType({"backend": MappingProxyType(dict(backend.describe())), "cue": cue, "wrap": wrap,
                                      "length": length,
                                      "matcher": "match_free_text(番号 → 活用を正規化した句 → 語 → その他)"})
        super().__init__()

    def _score(self, situation: Situation, candidates: tuple[Candidate, ...], text: str | None
               ) -> Mapping[str, float]:
        if text is None:
            raise ValueError(f"{self.name}: 文(DM4 の版)が要る当て口")
        out = self.backend.generate(wrap_prompt(text, self.wrap) + self.cue)
        cid = match_free_text(out, candidates)
        self.trace.append(("miss" if cid is None else ("other" if cid == OTHER_ID else "matched"), None))
        return {OTHER_ID if cid is None else cid: 1.0}

    def trace_summary(self) -> dict[str, Any]:
        n = len(self.trace)
        miss = sum(1 for k, _m in self.trace if k == "miss")
        other = sum(1 for k, _m in self.trace if k == "other")
        return {"n": n, "breakdown": miss, "breakdown_rate": miss / n if n else None, "other_explicit": other,
                "other_explicit_rate": other / n if n else None,
                "definition": "自由記述が、丁寧語と活用を正規化した後で、提示の候補にも「その他」にも当たらない率"
                              "(破綻の答えは明示の「その他」の数に入れない)"}
