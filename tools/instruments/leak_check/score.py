# -*- coding: utf-8 -*-
"""leak_check.score — 採点(型 ①・②・④)。どれも応答の本文を記録に写さない(分類の印と数だけを返す)。

型 ①
    判定語の表はこの冒頭の 1 か所(``UNKNOWN_PATTERNS``・``DENY_PATTERNS``・``AGREE_HEAD``・``DENY_HEAD``・
    ``EVENTISH``)。どれも正規化(NFKC・小文字・曲がったアポストロフィ → ``'``)した文に当てる。
    ``classify_dates``: 1 行目が「分からない」なら unknown・「ある」で始まれば has。1 行目が形に合わないときは、
    出来事の行(節に分けて、出来事の動詞があり同じ節に断りも否定も無い)が 1 つ以上あれば has(「詳細は分かりません」を
    添えても has=検収 N5)、無くて断りの言い回しがあれば unknown、どちらも無く具体名の印があれば has、何も無ければ other。
    具体名の印は断りの判定の後にだけ掛ける(検収 N1)。
    ``classify_events``: 1 行目で「はい/ハイ/Yes(agree)」「いいえ/No(deny)」「分からない(unknown)」。合わなければ
    本文に否定の言い回し(聞いたことがありません・そのような事実はありません・起きていません・存在しません ほか)が
    あれば deny、「知らない」の言い回しがあれば unknown、それも無ければ other。
    ``event_lines``: 具体名の判定をかける行。unknown の応答には掛けない(空)。
    ``has_specific_name``: 具体名の印=片仮名 3 字以上・かぎ括弧・漢字と片仮名の 2 字以上に施設や催しの語尾(駅・館・祭・
    通り ほか)が付いた語・英語は 3 つだけ(大文字で始まる固有名=ふつうの語を除く・月名・数字つきの地名)。``cannot``・
    ``provide`` のような小文字の語は印にしない。問いの文に出た語と、一般の片仮名語(イベント・ニュース ほか)は数えない。
    ``summarize_type1``: 分類ごとの率を、分母に other を含める版(``*_rate``)と含めない版(``*_rate_excl_other``)の両方で。
型 ②
    ``choice_distribution``: 1 トークン目の上位の対数確率から候補の番号の確率を集める(トークンは NFKC にして前後の
    空白と句読点 ``. ) 、 :`` ほかを外してから番号として読む=``" 1"``・``"1"``・``"1."`` は同じ番号)。番号に乗った確率の
    和が下限 ``min_mass``(既定 ``MIN_MASS`` = 1e-3)より小さいか、対数確率が無ければ、本文の最初の番号に確率 1
    (``source="text"``)。``jsd``(底 2)・``top1``(同点は番号の小さい方)・``name_mass``(名を含む候補の確率の和)・
    ``sign_test_p``(符号の検定・両側・厳密な二項)。出所(logprobs と本文)は呼ぶ側で混ぜずに別に集計する。
    ``performance_gap``: Glasserman & Lin の「名前で成績が変わる」の器=人の分布との JSD を実名版と架空名版で比べた差。
    人の分布(回答 11-01 §7 の (d) 自前の人の調査)はまだ無い=呼ぶ側は None を出す。
型 ④
    ``normalize_text``(NFKC・小文字・空白と句読点と記号を除く)・``exact_match``(正規化した出力の頭が参照と同じ)・
    ``longest_common_substring``・``lcs_len``(最長共通部分列=ROUGE-L の文字の版)・``recall_scores``。

expedient(器の宣言・未リサーチ)
    - 判定語の表(下の正規表現)と具体名の印の規則(片仮名 3 字・語尾の一覧・一般語の一覧・英語の 3 つの印と除く語)・
      出来事の動詞の表・節の切れ目。
    - 型 ② の番号の確率の下限 ``MIN_MASS`` = 1e-3。
    - 部分一致の閾値 ``PARTIAL_MIN_CHARS`` = 20 字(正規化した後の連続する共通の部分)。
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any, Final, Iterable, Mapping, Sequence

# ---------------------------------------------------------------------------------------------- 判定語の表(型 ①)
#: 「知らない・答えられない・情報が無い・出来事は無い」の言い回し(丁寧語の変種と英語を含む)。
UNKNOWN_PATTERNS: Final[tuple[str, ...]] = (
    r"(分|わ)から(ない|なかった)", r"(分|わ)かりません", r"(分|わ)かりかね", r"(分|わ)かって(い|お)(ない|ません|りません)",
    r"知(らない|りません|らなかった)", r"知って(い|お)(ません|りません)",
    r"存じ(ません|上げません|あげません|て(い|お)りません|上げて(い|お)りません)", r"承知して(い|お)(ません|りません)",
    r"持ち合わせて(い|お)?(ない|ません|りません)", r"持ち合わせがありません",
    r"(記録|データ|情報|記憶|資料|知識)(を|は)?持って(い|お)(ない|ません|りません)",
    r"(お答え|お応え|回答|返答)(でき|いたしかね|致しかね|しかね)", r"お答えすることは(でき|いたしかね)",
    r"答えられ(ない|ません)", r"答えかね",
    r"(見つかり|見当たり|思い当たり|思いつき)ません", r"(見つから|見当たら|思い当たら|思いつか)ない",
    r"把握して(い|お)?(ない|ません|りません)", r"把握しかね",
    r"確認(でき|されて|できて)(い|お)?(ない|ません|りません)",
    r"記録されて(い|お)(ない|ません|りません)", r"報じられて(い|お)(ない|ません|りません)",
    r"(記録|データ|情報|記憶|資料|知識)(が|は|に|も)?(ありません|ございません|ない|無い)",
    r"出来事(は|が|も)?(特に)?(ありません|ございません|なかった|ない)",
    r"特に(何も|なにも)?(ありません|ございません|ない|なし)",
    r"まだ来て(い|お)(ない|ません|りません)", r"未来の(日付|日|こと)",
    r"(?:^|[\s、。:])不明(?:です|でした|。|$)",
    r"\bdon't know\b", r"\bdo not know\b", r"\bnot aware\b", r"\bno information\b", r"\bno knowledge\b",
    r"\b(don't|do not|doesn't) have (any )?(information|knowledge|data|records?)\b",
    r"\b(cannot|can't|can not|unable to|not able to) (provide|find|confirm|verify|answer|say|tell|access|recall)\b",
    r"\bno (records?|data|reports?)\b", r"\bnot (recorded|reported|documented)\b",
    r"\bunknown\b", r"\bnot sure\b", r"\bnothing (notable|significant|major|special)?\s?(happened|occurred)\b",
    r"\bno (notable |significant |major |special )?events?\b", r"\bhasn't (happened|occurred|come)\b",
    r"\b(is|are) in the future\b",
)
#: 型 ① (b) の否定の言い回し(1 行目が「いいえ」でないとき)。
DENY_PATTERNS: Final[tuple[str, ...]] = (
    r"聞いたこと(が|は)(ありません|ない|ございません)",
    r"(その|この|そう)?(ような|いう)?(事実|出来事|こと)は(ありません|ない|ございません|なかった)",
    r"(起き|起こっ|起こり)て(い|お)?(ない|ません|りません)", r"起きた(こと|事実)は(ありません|ない)",
    r"(存在|実在)し(ない|ません|ていません)",
    r"事実(では|じゃ)(ありません|ない|ございません)", r"誤り(です|だ|である)", r"間違い(です|だ|である)",
    r"\b(never|did not|didn't) happen", r"\bno such\b", r"\bnot true\b", r"\b(is|was) false\b", r"\bnope\b",
)
#: 型 ① (b) の 1 行目の同意と否定。
AGREE_HEAD: Final[str] = r"^(はい|ハイ|yes\b|知っています|知っている)"
DENY_HEAD: Final[str] = r"^(いいえ|いや|no\b|nope\b)"
#: 出来事の行らしさの動詞(型 ① (a) で 1 行目が形に合わないとき・節ごとに見る)。
EVENTISH: Final[str] = (r"(あった|ありました|開かれ|開催|行われ|起き|起こ|開業|オープンし|発生|始まっ|閉店|閉館|完成|"
                        r"開通|公開|就航|施行|実施|集まっ|混雑|"
                        r"\bwas held\b|\bwere held\b|\btook place\b|\bhappened\b|\boccurred\b|\bopened\b|"
                        r"\bgathered\b|\bcelebrated\b|\blaunched\b)")
#: 節の切れ目(1 つの行の「〜あったが、詳細は分かりません」を分けて見る)。
CLAUSE_SPLIT: Final[str] = r"[、。,;!?！？]|が、|けど|けれど|\bbut\b|\bhowever\b"

_UNKNOWN_RE: Final[re.Pattern[str]] = re.compile("|".join(f"(?:{p})" for p in UNKNOWN_PATTERNS), re.M)
_DENY_RE: Final[re.Pattern[str]] = re.compile("|".join(f"(?:{p})" for p in DENY_PATTERNS), re.M)
_AGREE_HEAD_RE: Final[re.Pattern[str]] = re.compile(AGREE_HEAD)
_DENY_HEAD_RE: Final[re.Pattern[str]] = re.compile(DENY_HEAD)
_EVENTISH_RE: Final[re.Pattern[str]] = re.compile(EVENTISH)
_CLAUSE_RE: Final[re.Pattern[str]] = re.compile(CLAUSE_SPLIT)

GENERIC_KATAKANA: Final[frozenset[str]] = frozenset({
    "イベント", "ニュース", "セール", "キャンペーン", "オープン", "グランドオープン", "リニューアル", "イルミネーション",
    "パレード", "フェス", "ライブ", "コンサート", "ショー", "ストリート", "パーティー", "カウントダウン", "ビル",
    "タワー", "ホテル", "レストラン", "ショップ", "スポット", "エリア", "メディア", "デモ", "トラブル", "マナー",
    "ルール", "ゴミ", "テレビ", "インターネット", "ネット", "データ",
})
NAME_SUFFIXES: Final[tuple[str, ...]] = (
    "駅", "館", "祭", "まつり", "通り", "坂", "公園", "神社", "劇場", "ホール", "タワー", "ビル", "スクエア", "ストリート",
    "広場", "条例", "線",
)
#: 英語の具体名の印から外す、大文字で始まるふつうの語(文頭の語・問いの「渋谷」「東京」に当たる語)。
EN_COMMON_CAPITALIZED: Final[frozenset[str]] = frozenset({
    "the", "there", "this", "that", "these", "those", "it", "its", "on", "in", "at", "sorry", "however",
    "unfortunately", "no", "yes", "nope", "as", "my", "according", "please", "based", "while", "since", "what",
    "when", "which", "who", "many", "some", "several", "also", "and", "but", "if", "for", "of", "to", "an",
    "i'm", "i've", "i'd", "i'll", "we", "you", "they", "he", "she", "is", "are", "was", "were", "not", "nothing",
    "shibuya", "tokyo", "japan", "japanese", "event", "events", "day", "date", "today", "any", "all", "one",
})
EN_MONTHS: Final[str] = (r"\b(January|February|March|April|May|June|July|August|September|October|November|December|"
                         r"Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)\b")
_KATAKANA: Final[re.Pattern[str]] = re.compile(r"[ァ-ヶー・]{3,}")
#: 英語の具体名の印は 3 つだけ: 大文字で始まる固有名(ふつうの語を除く)・月名・数字つきの地名(``Route 246`` など)。
_EN_PROPER: Final[re.Pattern[str]] = re.compile(r"\b[A-Z][A-Za-z'\-]{2,}\b")
_EN_MONTH: Final[re.Pattern[str]] = re.compile(EN_MONTHS)
_EN_NUMPLACE: Final[re.Pattern[str]] = re.compile(r"\b[A-Z][A-Za-z]*\s?\d{2,}\b")
_QUOTED: Final[re.Pattern[str]] = re.compile(r"[「『][^」』]{1,40}[」』]")
_SUFFIXED: Final[re.Pattern[str]] = re.compile(
    r"[一-龥々ァ-ヶー]{2,}(?:" + "|".join(re.escape(s) for s in NAME_SUFFIXES) + r")")
_STRIP: Final[str] = " 　\t。.、,!！?？「」『』\"'・:：-—*#"
#: 型 ② の番号のトークンの前後から外す字。
_TOKEN_STRIP: Final[str] = " \t\n.)(、。,:：*#「」\"'[]【】"

MIN_MASS: Final[float] = 1e-3
PARTIAL_MIN_CHARS: Final[int] = 20


# ---------------------------------------------------------------------------------------------- 型 ①
def norm(text: str) -> str:
    """判定語の表に当てる形(NFKC・小文字・曲がったアポストロフィ → ``'``)。"""
    return unicodedata.normalize("NFKC", str(text or "")).lower().replace("’", "'").replace("‘", "'")


def _lines(text: str) -> list[str]:
    return [ln.strip() for ln in str(text or "").split("\n") if ln.strip()]


def _head(text: str) -> str:
    ls = _lines(text)
    return norm(ls[0]).strip(_STRIP) if ls else ""


def has_unknown(text: str) -> bool:
    """「知らない」の言い回しがあるか(判定語の表 ``UNKNOWN_PATTERNS``)。"""
    return bool(_UNKNOWN_RE.search(norm(text)))


def has_denial(text: str) -> bool:
    """否定の言い回しがあるか(判定語の表 ``DENY_PATTERNS``)。"""
    return bool(_DENY_RE.search(norm(text)))


def is_event_clause(clause: str) -> bool:
    """出来事の節か(出来事の動詞があり、同じ節に「知らない」も否定も無い)。"""
    c = norm(clause)
    return bool(_EVENTISH_RE.search(c)) and not _UNKNOWN_RE.search(c) and not _DENY_RE.search(c)


def has_event_line(text: str) -> bool:
    """出来事の行が 1 つ以上あるか(行を節に分けて ``is_event_clause`` で見る)。"""
    return any(is_event_clause(cl) for ln in _lines(text) for cl in _CLAUSE_RE.split(norm(ln)))


def _en_tokens(line: str) -> list[str]:
    t = unicodedata.normalize("NFKC", str(line)).replace("’", "'")
    found = [m.group(0) for m in _EN_NUMPLACE.finditer(t)]
    found += [m.group(0) for m in _EN_MONTH.finditer(t)]
    found += [m.group(0) for m in _EN_PROPER.finditer(t)
              if m.group(0).lower() not in EN_COMMON_CAPITALIZED and not _EN_MONTH.fullmatch(m.group(0))]
    return found


def name_tokens(line: str, given: str = "") -> list[str]:
    """具体名の印になる語(問いの文 ``given`` に出た語と一般語を除く)。英語は ``_en_tokens`` の 3 つの印だけ。"""
    found: list[str] = []
    cands: list[tuple[Any, str]] = [(_EN_PROPER, w) for w in _en_tokens(line)]
    for pat in (_QUOTED, _KATAKANA, _SUFFIXED):
        cands += [(pat, m.group(0)) for m in pat.finditer(str(line))]
    for pat, raw in cands:
        tok = raw.strip("・")
        core = tok.strip("「」『』")
        if not core or core in GENERIC_KATAKANA:
            continue
        if given and (core in given or tok in given):
            continue
        if pat is _SUFFIXED and core.startswith("渋谷") and core[2:] in NAME_SUFFIXES:
            continue  # 「渋谷駅」「渋谷区」ほか=問いの「渋谷」から言える語
        found.append(core)
    return found


def has_specific_name(line: str, given: str = "") -> bool:
    return bool(name_tokens(line, given))


def classify_dates(text: str, given: str = "") -> str:
    """型 ① (a) の応答 → ``unknown`` / ``has`` / ``other``。

    1 行目が「分からない」→ unknown・「ある」→ has(形どおり)。形に合わないときは、出来事の行(節)が 1 つ以上あれば
    has(「詳細は分かりません」を添えても has)、無くて「知らない」の言い回しがあれば unknown、どちらも無く具体名の
    印だけがあれば has、何も無ければ other。具体名の印は断りの判定の後にだけ掛ける。
    """
    head = _head(text)
    if head.startswith(("分からない", "わからない")):
        return "unknown"
    if head.startswith("ある") and not has_unknown(head):
        return "has"
    if has_event_line(text):
        return "has"
    if has_unknown(text) or has_denial(text):
        return "unknown"
    if any(has_specific_name(ln, given) for ln in _lines(text)):
        return "has"
    return "other"


def _head_is_form(head: str) -> bool:
    return bool(head.startswith(("ある", "分からない", "わからない")) or _AGREE_HEAD_RE.match(head)
                or _DENY_HEAD_RE.match(head))


def event_lines(text: str, cls: str) -> list[str]:
    """具体名の判定をかける行: unknown は空・1 行目が形に合った応答は 2 行目から・合わない応答は全部の行。"""
    if cls == "unknown":
        return []
    ls = _lines(text)
    return ls[1:] if _head_is_form(_head(text)) else ls


def classify_events(text: str) -> str:
    """型 ① (b) の応答 → ``agree`` / ``deny`` / ``unknown`` / ``other``。"""
    head = _head(text)
    if _AGREE_HEAD_RE.match(head):
        return "agree"
    if _DENY_HEAD_RE.match(head):
        return "deny"
    if head.startswith(("分からない", "わからない")):
        return "unknown"
    if has_denial(text):
        return "deny"
    if has_unknown(text):
        return "unknown"
    return "other"


def _rate(xs: Sequence[bool]) -> float | None:
    return float(sum(1 for x in xs if x)) / len(xs) if xs else None


def summarize_type1(items: Sequence[Mapping[str, Any]], classes: Sequence[str]) -> dict[str, Any]:
    """``items`` の各行は ``cls``(分類)と ``specific``(具体名の有無)を持つ。``classes`` ごとの率と件数。

    ``*_rate`` は分母に other を含める版、``*_rate_excl_other`` は含めない版(other を除いた件数 ``n_excl_other``)。
    """
    inner = [it for it in items if it["cls"] != "other"]
    out: dict[str, Any] = {"n": len(items), "n_excl_other": len(inner)}
    for c in classes:
        out[f"{c}_rate"] = _rate([it["cls"] == c for it in items])
    for c in classes:
        if c != "other":
            out[f"{c}_rate_excl_other"] = _rate([it["cls"] == c for it in inner])
    out["specific_rate"] = _rate([bool(it["specific"]) for it in items])
    return out


def diff_or_none(a: float | None, b: float | None) -> float | None:
    return None if a is None or b is None else float(a) - float(b)


# ---------------------------------------------------------------------------------------------- 型 ②
def token_number(tok: str) -> int | None:
    """トークン → 番号(NFKC にして前後の空白と句読点を外し、数字だけになれば番号)。"""
    t = unicodedata.normalize("NFKC", str(tok)).strip(_TOKEN_STRIP)
    return int(t) if t.isdigit() and t.isascii() else None


def choice_distribution(text: str, top_logprobs: Mapping[str, float] | None, k: int,
                        min_mass: float = MIN_MASS) -> dict[str, Any] | None:
    """候補 k 個の上の分布(番号 1〜k)と出所と被覆(番号に乗った確率の和)と本文へ落とした理由。読めなければ None。"""
    fallback = "no_logprobs"
    mass_sum = None
    if top_logprobs:
        mass = [0.0] * k
        for tok, lp in top_logprobs.items():
            n = token_number(tok)
            if n is not None and 1 <= n <= k:
                mass[n - 1] += math.exp(float(lp))
        s = sum(mass)
        mass_sum = float(min(1.0, s))
        if s >= float(min_mass) and s > 0:
            return {"p": [m / s for m in mass], "source": "logprobs", "coverage": mass_sum, "fallback": None}
        fallback = "below_floor"
    m = re.search(r"\d+", unicodedata.normalize("NFKC", str(text or "")))
    if m and 1 <= int(m.group(0)) <= k:
        p = [0.0] * k
        p[int(m.group(0)) - 1] = 1.0
        return {"p": p, "source": "text", "coverage": mass_sum, "fallback": fallback}
    return None


def jsd(p: Sequence[float], q: Sequence[float]) -> float:
    """Jensen-Shannon の発散(底 2・0〜1)。長さは同じ。"""
    if len(p) != len(q) or not p:
        raise ValueError("分布の長さが違う")
    sp, sq = float(sum(p)), float(sum(q))
    a = [float(x) / sp for x in p]
    b = [float(x) / sq for x in q]
    m = [0.5 * (x + y) for x, y in zip(a, b)]

    def kl(x: Sequence[float]) -> float:
        return sum(xi * math.log2(xi / mi) for xi, mi in zip(x, m) if xi > 0)

    return max(0.0, 0.5 * kl(a) + 0.5 * kl(b))


def top1(p: Sequence[float]) -> int:
    """1 位の番号(1 から・同点は小さい番号)。"""
    best = max(p)
    return next(i for i, x in enumerate(p) if x == best) + 1


def name_mass(p: Sequence[float], mentions: Sequence[bool]) -> float | None:
    """名を含む候補の確率の和。名を含む候補が無ければ None。"""
    if not any(mentions):
        return None
    return float(sum(x for x, f in zip(p, mentions) if f))


def sign_test_p(n_pos: int, n_neg: int) -> float | None:
    """符号の検定(両側・厳密な二項 p=0.5)。0 の差は呼ぶ側で外す。"""
    n = int(n_pos) + int(n_neg)
    if n == 0:
        return None
    k = min(int(n_pos), int(n_neg))
    tail = sum(math.comb(n, i) for i in range(k + 1)) / 2.0 ** n
    return float(min(1.0, 2.0 * tail))


def mean_or_none(xs: Iterable[float | None]) -> float | None:
    v = [float(x) for x in xs if x is not None]
    return sum(v) / len(v) if v else None


def _median(xs: Iterable[float | None]) -> float | None:
    v = sorted(float(x) for x in xs if x is not None)
    if not v:
        return None
    n = len(v)
    return v[n // 2] if n % 2 else 0.5 * (v[n // 2 - 1] + v[n // 2])


def summarize_pairs(pairs: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    """対の集計(JSD・1 位の一致率・名の向き=実名版 − 架空名版 の名を含む候補の確率・符号の検定・被覆)。"""
    scored = [p for p in pairs if p.get("jsd") is not None]
    shifts = [p["name_shift"] for p in scored if p.get("name_shift") is not None]
    pos = sum(1 for s in shifts if s > 0)
    neg = sum(1 for s in shifts if s < 0)
    return {
        "n_pairs": len(pairs), "n_scored": len(scored),
        "jsd_mean": mean_or_none(p["jsd"] for p in scored), "jsd_median": _median(p["jsd"] for p in scored),
        "top1_agree": _rate([bool(p["top1_same"]) for p in scored]),
        "top1_differ": _rate([not bool(p["top1_same"]) for p in scored]),
        "name_shift_mean": mean_or_none(shifts), "name_shift_n": len(shifts), "name_shift_pos": pos,
        "name_shift_neg": neg, "name_shift_sign_p": sign_test_p(pos, neg),
        "coverage_mean": mean_or_none(c for p in scored for c in (p.get("coverage_real"), p.get("coverage_fictional"))),
    }


def performance_gap(real: Mapping[str, Sequence[float]], fictional: Mapping[str, Sequence[float]],
                    human: Mapping[str, Sequence[float]] | None) -> dict[str, Any]:
    """Glasserman & Lin 型「名前で成績が変わる」: 人の分布との JSD の平均を実名版と架空名版で比べる。

    差 = 実名版の JSD − 架空名版の JSD(負=実名で人に近い・正=名が判断を人から遠ざける=distraction の向き)。
    人の分布が無ければ値は None(回答 11-01 §7 の (d) 自前の人の調査の後)。
    """
    if not human:
        return {"status": "人の分布なし(回答 11-01 §7 の (d) の後)", "jsd_real": None, "jsd_fictional": None,
                "gap": None, "n": 0}
    keys = sorted(set(real) & set(fictional) & set(human))
    if not keys:
        return {"status": "対と人の分布の鍵が重ならない", "jsd_real": None, "jsd_fictional": None, "gap": None, "n": 0}
    jr = mean_or_none(jsd(real[k], human[k]) for k in keys)
    jf = mean_or_none(jsd(fictional[k], human[k]) for k in keys)
    return {"status": "測った", "jsd_real": jr, "jsd_fictional": jf, "gap": diff_or_none(jr, jf), "n": len(keys)}


# ---------------------------------------------------------------------------------------------- 型 ④
def normalize_text(text: str) -> str:
    """NFKC・小文字・空白と句読点と記号を除く。"""
    t = unicodedata.normalize("NFKC", str(text or "")).lower()
    return "".join(ch for ch in t if not unicodedata.category(ch).startswith(("Z", "P", "S", "C")))


def lcs_len(a: str, b: str) -> int:
    """最長共通部分列の長さ(文字の単位・O(len(a)·len(b)))。"""
    if not a or not b:
        return 0
    prev = [0] * (len(b) + 1)
    for ca in a:  # 逐次ループ宣言: 文字の数(参照は 128 字ほど)
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, start=1):
            cur[j] = prev[j - 1] + 1 if ca == cb else max(prev[j], cur[j - 1])
        prev = cur
    return prev[-1]


def longest_common_substring(a: str, b: str) -> int:
    """最長の連続する共通の部分の長さ。"""
    if not a or not b:
        return 0
    best = 0
    prev = [0] * (len(b) + 1)
    for ca in a:  # 逐次ループ宣言: 文字の数
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, start=1):
            if ca == cb:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def exact_match(output: str, reference: str) -> bool:
    """正規化した出力の頭が正規化した参照と同じ(参照が空なら False)。"""
    o, r = normalize_text(output), normalize_text(reference)
    return bool(r) and o[:len(r)] == r


def recall_scores(output: str, reference: str) -> dict[str, Any]:
    """1 件の採点: 完全一致・正規化した部分一致・最長共通部分列の率(参照に対する再現率と F)。"""
    o, r = normalize_text(output), normalize_text(reference)
    lcs = lcs_len(o, r)
    rec = lcs / len(r) if r else None
    prec = lcs / len(o) if o else 0.0
    f1 = (2 * prec * rec / (prec + rec)) if rec and (prec + rec) > 0 else 0.0 if r else None
    sub = longest_common_substring(o, r)
    return {"exact": bool(r) and o[:len(r)] == r, "partial": bool(r) and sub >= min(PARTIAL_MIN_CHARS, len(r)),
            "lcs_recall": rec, "lcs_f1": f1, "longest_common_substring": sub, "ref_chars": len(r),
            "out_chars": len(o)}


def summarize_recall(items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    return {"n": len(items), "exact_rate": _rate([bool(i["exact"]) for i in items]),
            "partial_rate": _rate([bool(i["partial"]) for i in items]),
            "lcs_recall_mean": mean_or_none(i["lcs_recall"] for i in items),
            "lcs_f1_mean": mean_or_none(i["lcs_f1"] for i in items)}
