"""W21 段 9「見せ方」(PS7・4-1b の器): 体ごとの人物の説明文を**事実から決まった形で組み立てる**(LLM に書かせない)。

正: 計画 第 4 期 段 9(人物の説明文は事実から決まった形で組み立て、LLM に書かせない・人物の文を差し替えられる口=4-1b の器)・
設計書 §2-4 PS3((a) 属性を土台・(b) 作り物の生い立ちは使わない・(d) Big Five(TIPI-J)は腕)・§2-5 PS7(PS2 の属性を言葉で・
その人の第一言語・長さは計算の都合で決めず実際の長さを測る・同じ仕組みで判断モデルには短い版・LLM には長い版=DM4・改変した物の
名指しを機械で調べる=CP5-3)・§2-12(LLM が書いた人物像の腕=今後の検証)・決定 10-12 §4-7 DM4(全部を言葉で・数字はお金と
時刻だけ・共通部分を前に)・§4-8(考えるのは第一言語)。

形
- 入力は**事実の表** :class:`PersonaFacts`(体ごとの列+世帯の同居人の行+なじみの場所の行)。W21 の資産から作るのは
  :func:`facts_from_w21`(段 1〜7 の表を読むだけ)。
- :func:`render` が言語(``ja``・``en``)と版(``short``・``long``)ごとに文を組む。**長い版=短い版+行**(短い版は長い版の頭=
  DM4 の「共通部分を前に」)。行は事実があるときだけ出す=長さは人ごとに違い、決め打ちしない(実際の字数を表に書く)。
- 言語: 第一言語が日本語か英語の人はその言語の型で書く。第一言語が空欄で国籍も空欄の人(外から来て働く人=材料なし)は日本語の
  型で書く(``lang_basis="blank_assumed_ja"``=宣言)。第一言語がほかの言語の人と、外国籍で第一言語が空欄の人は**欄だけ**
  (文は空・``text_status="no_template"``=宣言)。
- 数字はお金と時刻だけ: 年齢・人数・年数は言葉(漢数字・英語の綴り)・時間と分は日本語の型だけ数字(英語の型は綴り)・お金は
  数字(円・万円・¥)。1 億円以上は「万円」の単位で書く(6-1 の計器の語に「億円」が無い)。固有名(なじみの場所と勤め先の名)
  の中の数字は名のまま(``mask_names=True`` で名を ``◇`` にした文を作れる=計器が名の分を分ける)。
- 判断の入力への載せ方: :func:`compose_blocks` が描画のブロック(B0〜B6)に人物の文を足す(engine に人物の欄が無い=個体の
  部分の頭に置く: 短い版は B6 の前・長い版は B5 の前)。``engine.decision.port.compose`` と 6-1 の器(``tools/instruments/
  dm_eval/situations.py`` の長さの腕 t300/t1000・数字の計器)がそのまま読める。
- 差し替えの口(4-1b の腕「LLM が書いた人物像」を刺す): :func:`override`(元の文は ``text_original`` に残す・出どころの欄と
  manifest の欄)。本段は口と試験だけ(LLM は呼ばない)。
- Big Five(TIPI-J)は腕: 欄 :data:`TIPI_COLUMNS`(値は空欄=実在の回答が使えるまで)と口 :func:`with_big_five`(値を入れた
  ときだけ長い版に 1 行)。
- CP5-3: :func:`naming_check_ids` が文に名の出る POI と組織の**番号**(表の ``named_poi``・``named_org``)を改変した物の
  番号と照らす(検収の後の親の判断=番号で見る)。:func:`naming_check` は番号の無い名だけの補助で、
  ``engine.experiment.checks.persona_naming``(3-3b の道具)を呼ぶ(名の一覧は呼び手が渡す)。
- engine を import しない(歩く時間は ``attr_fns.walk_seconds``)=組み立てで ``shibuya.llm`` が読み込まれない(試験)。

近似の宣言は ``w21_build_c.W21C_EXPEDIENTS``(つなぎの台帳と 1 対 1)。

逐次ループ宣言(P4): 行の種類の数ぶん(長い版で 15)・言語の数(2)・値の種類の数ぶんの語の写像(年齢 106・金額の種類・分の
種類・続き柄の組)。世帯の同居人となじみの場所の行は ``np.add.reduceat`` で人ごとに連ねる=体ごとの for は無い。
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.compute as pc

from shibuya.core.time_consts import SECONDS_PER_MINUTE

from . import attr_fns as A

__all__ = [
    "LANGS", "VERSIONS", "NAME_MASK", "TIPI_COLUMNS", "TIPI_WORDS", "CHARS_PER_TOKEN", "FACT_COLUMNS",
    "PersonaFacts", "facts_from_w21", "render", "build_tables", "compose_blocks", "override", "with_big_five",
    "naming_check", "naming_check_ids", "prefix_mismatches", "kanji_number", "english_number", "money_ja", "money_en",
    "age_words", "text_groups",
    "persona_langs", "place_words", "PLACE_WORDS",
    "PS2_BLANK_FIELDS", "HOUSEHOLD_CATEGORIES", "relation_category", "PersonaOverrideError",
]

#: 型のある言語(ほかの言語は欄だけ)。
LANGS: Final[tuple[str, ...]] = ("ja", "en")
#: 版(DM4: 短い版=判断モデル・長い版=LLM)。``engine.decision.port.LENGTHS`` と同じ語。
VERSIONS: Final[tuple[str, ...]] = ("short", "long")
#: 名を伏せた文の印(計器が名の中の数字を分けるため)。
NAME_MASK: Final[str] = "◇"
#: TIPI-J の 5 次元の欄(川本ほか 2015 の並び=外向性・協調性・勤勉性・神経症傾向・開放性)。値は空欄(腕)。
TIPI_COLUMNS: Final[tuple[str, ...]] = ("tipi_extraversion", "tipi_agreeableness", "tipi_conscientiousness",
                                        "tipi_neuroticism", "tipi_openness")
TIPI_WORDS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "tipi_extraversion": ("外向性", "extraversion"), "tipi_agreeableness": ("協調性", "agreeableness"),
    "tipi_conscientiousness": ("勤勉性", "conscientiousness"), "tipi_neuroticism": ("神経症傾向", "neuroticism"),
    "tipi_openness": ("開放性", "openness"),
})
#: 目安のトークン=字数 ÷ これ(``ja`` は 6-1 の器 ``dm_eval.situations.CHARS_PER_TOKEN`` と同じ値=試験が突き合わせる・
#: ``en`` は未計測=tokenizer で後で測る)。
CHARS_PER_TOKEN: Final[Mapping[str, float]] = MappingProxyType({"ja": 1.0, "en": 4.0})
#: PS2 の属性のうち、W21 に材料が無く文に載せない欄(空欄=推測で埋めない)。
PS2_BLANK_FIELDS: Final[tuple[str, ...]] = ("belongings", "body_and_senses", "mobility_aid", "voice_level")
#: 本人の貯蓄の行を出す年齢の下限(段 5 は世帯の資産を 18 歳以上の世帯員に配った=``w21_money.ADULT_AGE`` と同じ値=試験)。
ADULT_AGE: Final[int] = 18

# ------------------------------------------------------------------------------------------ 事実の表
#: 体ごとの列(語は空欄=""・数は空欄=−1・時間は NaN)。
FACT_COLUMNS: Final[tuple[str, ...]] = (
    "person_id", "kind", "age", "sex", "nationality", "first_language", "japanese_level",
    "home_chome", "institution", "origin_name", "tenure", "residence_period", "residence_years",
    "labour", "emp_status", "occupation", "industry", "org_role", "duty_role", "org_name", "org_sector", "org_size",
    "work_area", "work_chome", "is_org_head", "is_dept_head", "dept_mates", "has_supervisor", "weekly_hours",
    "school_kind", "school_place", "commute_mode", "commute_m",
    "wage_monthly", "wage_annual", "savings", "debt", "consumer_credit", "hh_size", "hh_savings", "outside_places",
    "org_index",
)
#: 同居人の続き柄の区分(本人から見た=``relation_category``)。
HOUSEHOLD_CATEGORIES: Final[tuple[str, ...]] = ("spouse", "child", "parent", "sibling", "grandchild", "grandparent",
                                                "relative", "housemate")


@dataclass(frozen=True)
class PersonaFacts:
    """人物の文の材料(事実だけ)。``cols`` は体ごとの列(:data:`FACT_COLUMNS`)・``members`` は同居人の行(``owner``=
    本人の行の番号・``cat``=:data:`HOUSEHOLD_CATEGORIES` の番号・``age``・``sex``=並びは本人・区分・年上の順)・
    ``places`` はなじみの場所の行(``owner``・``rank``・``poi_index``・``name``・``cat_ja``・``cat_en``=並びは本人・順位の
    順)。〔検収 L8〕3 つの表は読み取り専用の写像で、配列は書き込み禁止の view(呼び手の配列は書き換えない)。口
    (:func:`with_big_five`・:meth:`take`)は新しい表を作って返す。"""

    cols: Mapping[str, np.ndarray]
    members: Mapping[str, np.ndarray]
    places: Mapping[str, np.ndarray]

    def __post_init__(self) -> None:
        for name in ("cols", "members", "places"):
            object.__setattr__(self, name, MappingProxyType({k: _ro(v) for k, v in getattr(self, name).items()}))

    @property
    def n(self) -> int:
        return int(np.asarray(self.cols["person_id"]).size)

    def take(self, idx: np.ndarray) -> "PersonaFacts":
        """行の番号 ``idx`` の体だけの表(同居人となじみの場所の行も絞り、本人の番号を振り直す)。"""
        idx = np.asarray(idx, dtype=np.int64)
        pos = np.full(self.n, -1, dtype=np.int64)
        pos[idx] = np.arange(idx.size)

        def sub(rows: Mapping[str, np.ndarray]) -> dict[str, np.ndarray]:
            own = np.asarray(rows["owner"], dtype=np.int64)
            keep = pos[own] >= 0 if own.size else np.zeros(0, dtype=bool)
            out = {k: np.asarray(v)[keep] for k, v in rows.items()}
            out["owner"] = pos[own[keep]]
            order = np.argsort(out["owner"], kind="stable")
            return {k: v[order] for k, v in out.items()}

        return PersonaFacts({k: np.asarray(v)[idx] for k, v in self.cols.items()}, sub(self.members), sub(self.places))


def _ro(v: Any) -> np.ndarray:
    a = np.asarray(v).view()
    a.flags.writeable = False
    return a


# ------------------------------------------------------------------------------------------ 語の道具
_KD: Final[str] = "〇一二三四五六七八九"


def kanji_number(n: int) -> str:
    """0〜9,999 の整数 → 漢数字(十・百・千の位取り)。"""
    n = int(n)
    if n < 0 or n > 9_999:
        raise ValueError(f"漢数字は 0〜9,999(いま {n})")
    if n == 0:
        return "〇"
    out = ""
    for unit, word in ((1000, "千"), (100, "百"), (10, "十")):
        d, n = divmod(n, unit)
        if d:
            out += ("" if d == 1 else _KD[d]) + word
    return out + (_KD[n] if n else "")


_ONES: Final[tuple[str, ...]] = ("zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten",
                                 "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
                                 "eighteen", "nineteen")
_TENS: Final[tuple[str, ...]] = ("", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety")


def english_number(n: int) -> str:
    """0〜9,999 の整数 → 英語の綴り。"""
    n = int(n)
    if n < 0 or n > 9_999:
        raise ValueError(f"英語の綴りは 0〜9,999(いま {n})")
    if n < 20:
        return _ONES[n]
    if n < 100:
        t, o = divmod(n, 10)
        return _TENS[t] + ("" if o == 0 else "-" + _ONES[o])
    if n < 1000:
        h, r = divmod(n, 100)
        return _ONES[h] + " hundred" + ("" if r == 0 else " " + english_number(r))
    th, r = divmod(n, 1000)
    return english_number(th) + " thousand" + ("" if r == 0 else " " + english_number(r))


def _round2(yen: np.ndarray) -> np.ndarray:
    """2 桁の有効数字に丸める(正の値だけ・ほかはそのまま)。"""
    y = np.asarray(yen, dtype=np.float64)
    out = y.copy()
    pos = y > 0
    if pos.any():
        mag = 10.0 ** (np.floor(np.log10(y[pos])) - 1)
        out[pos] = np.round(y[pos] / mag) * mag
    return np.round(out).astype(np.int64)


def money_ja(yen: int) -> str:
    """円 → 日本語のお金の語(1 万円以上は「万円」・1 億円以上も「万円」の単位=計器の語に合わせた)。"""
    yen = int(yen)
    if yen >= 10_000:
        man = yen / 10_000
        return (f"{int(round(man)):,}" if abs(man - round(man)) < 1e-9 else f"{man:g}") + "万円"
    return f"{yen:,}円"


def money_en(yen: int) -> str:
    """円 → 英語のお金の語(¥・100 万円以上は million)。"""
    yen = int(yen)
    if yen >= 1_000_000:
        v = yen / 1_000_000
        return f"¥{v:.1f} million" if v < 10 else f"¥{v:.0f} million"
    return f"¥{yen:,}"


def age_words(age: int, sex: int, lang: str) -> str:
    """年齢と男女 → 言葉(13 歳未満は歳を漢数字・英語の綴りで・13〜19 歳は十代の前半/後半・20 歳以上は十年ごとの前半/後半)。"""
    a, s = int(age), int(sex)
    if lang == "ja":
        child = "男の子" if s == 0 else "女の子"
        adult = "男性" if s == 0 else "女性"
        if a < 13:
            return f"{kanji_number(max(a, 0))}歳の{child}"
        if a >= 100:
            return f"百歳を超える{adult}"
        dec = (a // 10) * 10
        half = "前半" if a % 10 < 5 else "後半"
        return f"{kanji_number(dec)}代{half}の{adult}"
    child = "boy" if s == 0 else "girl"
    adult = "man" if s == 0 else "woman"
    pron = "his" if s == 0 else "her"
    if a < 13:
        return f"a {english_number(max(a, 0))}-year-old {child}"
    if a < 20:
        return f"a teenage {child}"
    if a >= 100:
        return f"a {adult} over one hundred"
    dec = (a // 10) * 10
    half = "early" if a % 10 < 5 else "late"
    return f"a {adult} in {pron} {half} {_TENS[dec // 10]}ies".replace("tyies", "ties")


def _age_short(age: int, lang: str) -> str:
    """同居人の年齢の短い語(13 歳未満は歳・ほかは十年ごと)。"""
    a = int(age)
    if lang == "ja":
        if a < 13:
            return f"{kanji_number(max(a, 0))}歳"
        if a >= 100:
            return "百歳以上"
        return f"{kanji_number((a // 10) * 10)}代{'前半' if a % 10 < 5 else '後半'}"
    if a < 13:
        return f"{english_number(max(a, 0))} years old"
    if a < 20:
        return "teens"
    if a >= 100:
        return "over one hundred"
    return f"{'early' if a % 10 < 5 else 'late'} {_TENS[(a // 10)]}ies".replace("tyies", "ties")


def _lut(values: Any, fn: Callable[[Any], str]) -> np.ndarray:
    """値の種類ごとに ``fn`` を 1 回呼んで写す(逐次: 値の種類の数)。"""
    v = np.asarray(values)
    if v.size == 0:
        return np.zeros(0, dtype=object)
    uniq, inv = np.unique(v, return_inverse=True)
    table = np.array([fn(x) for x in uniq.tolist()], dtype=object)
    return table[np.asarray(inv).reshape(-1)]


def _s(x: Any) -> np.ndarray:
    """語の列(None は "")。"""
    a = np.asarray(x, dtype=object)
    return np.where(np.equal(a, None), "", a).astype(str).astype(object)


def _when(mask: np.ndarray, text: Any) -> np.ndarray:
    m = np.asarray(mask, dtype=bool)
    return np.where(m, text, "").astype(object)


def _join_lines(lines: Sequence[np.ndarray], n: int) -> np.ndarray:
    """行の列を改行で連ねる(空の行は飛ばす)。逐次: 行の種類の数。"""
    out = np.full(n, "", dtype=object)
    for ln in lines:
        ln = np.asarray(ln, dtype=object)
        has = ln != ""
        both = has & (out != "")
        out = np.where(both, out + "\n" + ln, np.where(has, ln, out))
    return out


def _group_join(owner: np.ndarray, items: np.ndarray, n: int, sep: str) -> np.ndarray:
    """``owner``(昇順)ごとに ``items`` を ``sep`` で連ねる(``np.add.reduceat``=体ごとの for は無い)。"""
    out = np.full(n, "", dtype=object)
    own = np.asarray(owner, dtype=np.int64)
    if own.size == 0:
        return out
    it = np.asarray(items, dtype=object)
    first = np.r_[True, own[1:] != own[:-1]]
    piece = np.where(first, it, sep + it).astype(object)
    starts = np.flatnonzero(first)
    out[own[starts]] = np.add.reduceat(piece, starts)
    return out


# ------------------------------------------------------------------------------------------ 語の表(日本語・英語)
_SEXJ = ("男性", "女性")
_OCC: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "A": ("管理の仕事", "management work"), "B": ("専門・技術の仕事", "professional or technical work"),
    "C": ("事務の仕事", "office work"), "D": ("販売の仕事", "sales work"), "E": ("サービスの仕事", "service work"),
    "F": ("保安の仕事", "security work"), "G": ("農林漁業の仕事", "farming, forestry or fishing work"),
    "H": ("ものを作る仕事", "production work"), "I": ("運転や機械を動かす仕事", "driving or machine operation"),
    "J": ("建設や採掘の仕事", "construction or mining work"),
    "K": ("運搬・清掃・包装の仕事", "carrying, cleaning or packing work"), "L": ("仕事", "work"), "": ("仕事", "work"),
})
_IND: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "A": ("農業・林業", "agriculture and forestry"), "B": ("漁業", "fishing"), "C": ("鉱業", "mining"),
    "D": ("建設業", "construction"), "E": ("製造業", "manufacturing"), "F": ("電気・ガス・水道", "utilities"),
    "G": ("情報通信業", "information and communications"), "H": ("運輸業・郵便業", "transport and postal services"),
    "I": ("卸売業・小売業", "wholesale and retail"), "J": ("金融業・保険業", "finance and insurance"),
    "K": ("不動産業・物品賃貸業", "real estate and rental"),
    "L": ("学術研究・専門技術サービス業", "professional and technical services"),
    "M": ("宿泊業・飲食サービス業", "accommodation and food services"),
    "N": ("生活関連サービス業・娯楽業", "personal services and entertainment"),
    "O": ("教育・学習支援業", "education"), "P": ("医療・福祉", "medical care and welfare"),
    "Q": ("複合サービス事業", "compound services"), "R": ("その他のサービス業", "other services"),
    "S": ("公務", "public service"), "T": ("", ""), "": ("", ""),
})
_STATUS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "regular": ("正社員として", "as a regular employee"), "dispatched": ("派遣社員として", "as a dispatched worker"),
    "part_time": ("パート・アルバイトで", "part-time"), "executive": ("会社の役員として", "as a company officer"),
    "employer": ("人を雇って自営で", "self-employed with staff"), "self_employed": ("自営で", "self-employed"),
    "family_worker": ("家族の事業を手伝って", "helping in a family business"), "home_worker": ("内職で", "doing piecework at home"),
    "": ("", ""),
})
_ROLE: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "店長": ("店長を務める", "store manager"), "部署長": ("部署の長を務める", "team leader"),
    "責任者": ("責任者を務める", "the person in charge"), "代表": ("代表を務める", "head of the organization"),
})
_DUTY: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "店長": ("店の開け閉め", "opening and closing the store"), "補充": ("店の品出しと補充", "restocking the shelves"),
    "納品ドライバー": ("納品の運転", "delivery driving"), "配送作業員": ("配送の作業", "delivery work"),
    "清掃作業員": ("清掃", "cleaning"), "警備員": ("警備", "security guarding"), "駅員": ("駅の業務", "station duties"),
    "電車運転士": ("電車の運転", "driving trains"), "車掌": ("車掌の業務", "conductor duties"),
    "警察官": ("警察官の勤務", "police duty"), "消防士": ("消防の勤務", "fire service duty"),
})
_SIZE_JA = (("1-4", "ごく小さな"), ("5-9", "小さな"), ("10-19", "小さな"), ("20-29", "中くらいの"), ("30-49", "中くらいの"),
            ("50-99", "中くらいの"), ("100-299", "大きな"), ("300+", "大きな"))
_SIZE_EN = (("1-4", "a very small"), ("5-9", "a small"), ("10-19", "a small"), ("20-29", "a mid-sized"),
            ("30-49", "a mid-sized"), ("50-99", "a mid-sized"), ("100-299", "a large"), ("300+", "a large"))
_SCHOOL: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "elementary": ("小学校に通っている", "attends elementary school"),
    "junior_high": ("中学校に通っている", "attends junior high school"),
    "high": ("高校に通っている", "attends high school"),
    "junior_college": ("短大・高専に通っている", "attends a junior college or college of technology"),
    "university": ("大学に通っている", "attends university"), "graduate": ("大学院に通っている", "attends graduate school"),
    "kindergarten": ("幼稚園に通っている", "attends kindergarten"), "nursery": ("保育園に通っている", "attends a nursery"),
    "kodomoen": ("認定こども園に通っている", "attends a certified childcare center"),
    "preschool_other": ("園や学校にはまだ通っていない", "does not attend a nursery or school yet"),
})
_SCHOOL_PLACE: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "in_ward": ("渋谷区内", "in Shibuya Ward"), "other_tokyo": ("都内の別の区市町村", "elsewhere in Tokyo"),
    "other_prefecture": ("東京都の外", "outside Tokyo"),
})
_TENURE: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "owned": ("持ち家", "owns the home"), "public_rent": ("公営の借家", "public rental housing"),
    "private_rent": ("民間の借家", "private rental housing"), "company_housing": ("社宅・官舎", "company housing"),
    "room_rent": ("間借り", "rents a room"),
})
_REL_WORDS: Final[Mapping[str, tuple[tuple[str, str], tuple[str, str]]]] = MappingProxyType({
    # 区分 → ((男の語, 女の語) 日本語, (男, 女) 英語)
    "spouse": (("夫", "妻"), ("husband", "wife")), "child": (("息子", "娘"), ("son", "daughter")),
    "parent": (("父", "母"), ("father", "mother")), "sibling": (("きょうだい", "きょうだい"), ("brother", "sister")),
    "grandchild": (("孫", "孫"), ("grandson", "granddaughter")),
    "grandparent": (("祖父", "祖母"), ("grandfather", "grandmother")),
    "relative": (("親族", "親族"), ("relative", "relative")), "housemate": (("同居人", "同居人"), ("housemate", "housemate")),
})
#: 世帯の言い方の区分の語(数を数える語)。
_CAT_COUNT: Final[Mapping[str, tuple[str, str, str]]] = MappingProxyType({
    "spouse": ("配偶者", "spouse", "spouses"), "child": ("子ども", "child", "children"), "parent": ("親", "parent", "parents"),
    "sibling": ("きょうだい", "sibling", "siblings"), "grandchild": ("孫", "grandchild", "grandchildren"),
    "grandparent": ("祖父母", "grandparent", "grandparents"), "relative": ("親族", "relative", "relatives"),
    "housemate": ("同居人", "housemate", "housemates"),
})
#: なじみの場所の種類の語(W6 の ``cat``・``subcat``)。subcat が先・無ければ cat。
PLACE_WORDS: Final[Mapping[str, tuple[str, str]]] = MappingProxyType({
    "food": ("飲食店", "restaurant"), "shop": ("店", "shop"), "nightlife": ("夜の店", "bar"), "office": ("事務所", "office"),
    "service": ("サービスの店", "service"), "hotel": ("宿", "hotel"), "school": ("学校", "school"),
    "landmark": ("名所", "landmark"), "leisure": ("遊びや運動の場所", "leisure spot"), "hall": ("ホール", "hall"),
    "attraction": ("見どころ", "attraction"), "cinema": ("映画館", "cinema"), "education": ("教室", "classes"),
    "|gallery": ("ギャラリー", "gallery"), "|museum": ("博物館・美術館", "museum"), "|events_venue": ("催しの会場", "event venue"),
    "|theatre": ("劇場", "theatre"), "|love_hotel": ("ホテル", "hotel"), "|worship": ("寺社", "shrine or temple"),
    "|arcade": ("ゲームセンター", "arcade"), "|gym": ("ジム", "gym"), "|park": ("公園", "park"),
    "|sports_centre": ("スポーツ施設", "sports centre"), "|club": ("クラブ", "club"), "|karaoke": ("カラオケ", "karaoke"),
    "|net_cafe": ("ネットカフェ", "internet café"), "|sauna": ("サウナ", "sauna"), "|childcare": ("保育施設", "childcare"),
    "|hospital": ("病院", "hospital"), "|library": ("図書館", "library"), "|art_supply": ("画材店", "art supply shop"),
    "|bicycle": ("自転車店", "bicycle shop"), "|books": ("書店", "bookshop"), "|convenience": ("コンビニ", "convenience store"),
    "|florist": ("花屋", "florist"), "|hobby": ("趣味の店", "hobby shop"), "|music_shop": ("音楽の店", "music shop"),
    "|musical_instrument": ("楽器店", "instrument shop"), "|pachinko": ("パチンコ", "pachinko parlor"),
    "|photo": ("写真店", "photo shop"), "|sports_shop": ("スポーツ用品店", "sports shop"),
    "|stationery": ("文具店", "stationery shop"), "|video_games": ("ゲーム店", "video game shop"),
})
_JLEVEL: Final[tuple[tuple[str, str], ...]] = (
    ("日本語はどんな場面でも相手に合わせて話せる", "speaks Japanese well in any situation"),
    ("日本語を流ちょうに話せる", "speaks Japanese fluently"),
    ("日本語は日常の会話ができる", "can handle everyday conversation in Japanese"),
    ("日本語は身近な基本のやりとりができる", "can exchange basic information in Japanese"),
    ("日本語はあいさつや決まった言い回しくらい", "knows only greetings and set phrases in Japanese"),
    ("日本語は話せない", "cannot speak Japanese"),
)
_NAT_EN: Final[Mapping[str, str]] = MappingProxyType({
    "日本": "Japan", "米国": "the United States", "英国": "the United Kingdom", "オーストラリア": "Australia", "カナダ": "Canada",
})


def place_words(cat: Any, subcat: Any) -> tuple[np.ndarray, np.ndarray]:
    """W6 の POI の(cat, subcat)→(日本語, 英語)の種類の語。"""
    key = np.char.add(np.char.add(_s(cat).astype(str), "|"), _s(subcat).astype(str))

    def f(k: str, j: int) -> str:
        c, sc = k.split("|", 1)
        return (PLACE_WORDS.get("|" + sc) or PLACE_WORDS.get(c) or ("場所", "place"))[j]

    return _lut(key, lambda k: f(k, 0)), _lut(key, lambda k: f(k, 1))


# ------------------------------------------------------------------------------------------ 続き柄(本人から見た区分)
_REL_OF: Final[Mapping[tuple[str, str], str]] = MappingProxyType({
    **{("head", v): c for v, c in (("spouse", "spouse"), ("child", "child"), ("parent", "parent"),
                                   ("sibling", "sibling"), ("grandchild", "grandchild"),
                                   ("grandparent", "grandparent"), ("non_relative", "housemate"))},
    **{("spouse", v): c for v, c in (("head", "spouse"), ("child", "child"), ("grandchild", "grandchild"),
                                     ("non_relative", "housemate"))},
    **{("child", v): c for v, c in (("head", "parent"), ("spouse", "parent"), ("child", "sibling"),
                                    ("parent", "grandparent"), ("non_relative", "housemate"))},
    **{("parent", v): c for v, c in (("head", "child"), ("sibling", "child"), ("child", "grandchild"),
                                     ("non_relative", "housemate"))},
    **{("sibling", v): c for v, c in (("head", "sibling"), ("sibling", "sibling"), ("parent", "parent"),
                                      ("non_relative", "housemate"))},
    **{("grandchild", v): c for v, c in (("head", "grandparent"), ("spouse", "grandparent"),
                                         ("non_relative", "housemate"))},
    **{("grandparent", v): c for v, c in (("head", "grandchild"), ("non_relative", "housemate"))},
})


def relation_category(rel_self: Any, rel_other: Any) -> np.ndarray:
    """(本人の続き柄, 同居人の続き柄)(どちらも世帯主から見た語)→ 本人から見た区分(:data:`HOUSEHOLD_CATEGORIES`)。
    表に無い組は、どちらかが非親族なら「同居人」・ほかは「親族」(どちらとも決まらない組=宣言)。"""
    a, b = _s(rel_self).astype(str), _s(rel_other).astype(str)
    key = np.char.add(np.char.add(a, "|"), b)

    def f(k: str) -> str:
        x, y = k.split("|", 1)
        if (x, y) in _REL_OF:
            return _REL_OF[(x, y)]
        return "housemate" if "non_relative" in (x, y) else "relative"

    return _lut(key, f)


# ------------------------------------------------------------------------------------------ 文の組み立て
def _cols(f: PersonaFacts) -> dict[str, np.ndarray]:
    return {k: np.asarray(v) for k, v in f.cols.items()}


def _money(values: np.ndarray, lang: str) -> np.ndarray:
    r = _round2(np.maximum(np.asarray(values, dtype=np.int64), 0))
    return _lut(r, money_ja if lang == "ja" else money_en)


def _num_words(values: np.ndarray, lang: str) -> np.ndarray:
    v = np.clip(np.asarray(values, dtype=np.int64), 0, 9_999)
    return _lut(v, kanji_number if lang == "ja" else english_number)


def _household_phrase(f: PersonaFacts, lang: str) -> np.ndarray:
    """暮らし方の句(ひとり暮らし・「夫・子ども二人と暮らしている」など)。"""
    n = f.n
    mem = f.members
    own = np.asarray(mem["owner"], dtype=np.int64)
    cat = np.asarray(mem["cat"], dtype=np.int64)
    sex = np.asarray(mem["sex"], dtype=np.int64)
    K = len(HOUSEHOLD_CATEGORIES)
    cnt = np.zeros((n, K), dtype=np.int64)
    if own.size:
        np.add.at(cnt, (own, cat), 1)
    sp_sex = np.full(n, -1, dtype=np.int64)
    sp = cat == HOUSEHOLD_CATEGORIES.index("spouse")
    sp_sex[own[sp]] = sex[sp]
    parts: list[np.ndarray] = []
    j = 0 if lang == "ja" else 1
    for k, name in enumerate(HOUSEHOLD_CATEGORIES):  # 逐次: 区分の数(8)
        c = cnt[:, k]
        if name == "spouse":
            male, female = _REL_WORDS["spouse"][j]
            word = np.where(sp_sex == 0, male, np.where(sp_sex == 1, female, _CAT_COUNT["spouse"][0 if j == 0 else 1]))
            parts.append(_when(c > 0, word))
            continue
        if lang == "ja":
            w = np.where(c == 1, _CAT_COUNT[name][0], _CAT_COUNT[name][0] + _num_words(c, "ja") + "人")
        else:
            w = np.where(c == 1, "a " + _CAT_COUNT[name][1], _num_words(c, "en") + " " + _CAT_COUNT[name][2])
        parts.append(_when(c > 0, w))
    listed = _join_parts(parts, "・" if lang == "ja" else ", ")
    if lang == "ja":
        return np.where(listed == "", "ひとり暮らし", listed + "と暮らしている").astype(object)
    return np.where(listed == "", "lives alone", "lives with " + listed).astype(object)


def _join_parts(parts: Sequence[np.ndarray], sep: str) -> np.ndarray:
    """句の列を ``sep`` で連ねる(空の句は飛ばす)。逐次: 句の種類の数。"""
    out = np.full(np.asarray(parts[0]).size if parts else 0, "", dtype=object)
    for p in parts:
        p = np.asarray(p, dtype=object)
        has = p != ""
        out = np.where(has & (out != ""), out + sep + p, np.where(has, p, out))
    return out


def _a(word: np.ndarray) -> np.ndarray:
    """英語の冠詞(綴りの数の頭が母音の音なら an)。"""
    return _lut(np.asarray(word, dtype=object).astype(object),
                lambda w: ("an " if str(w)[:1] in ("a", "e", "i", "o") and not str(w).startswith("one") else "a ") + str(w))


def _pa(texts: Any) -> pa.Array:
    return pa.array(np.asarray(texts, dtype=object).tolist(), type=pa.string())


def _len(texts: np.ndarray) -> np.ndarray:
    """文の字数(pyarrow の ``utf8_length``=配列の計算)。"""
    t = np.asarray(texts, dtype=object)
    if t.size == 0:
        return np.zeros(0, dtype=np.int64)
    return pc.utf8_length(_pa(t)).to_numpy(zero_copy_only=False).astype(np.int64)


def _nlines(texts: np.ndarray) -> np.ndarray:
    """文の行の数(空の文は 0・pyarrow の ``count_substring``)。"""
    t = np.asarray(texts, dtype=object)
    if t.size == 0:
        return np.zeros(0, dtype=np.int64)
    a = _pa(t)
    k = pc.count_substring(a, "\n").to_numpy(zero_copy_only=False).astype(np.int64) + 1
    return np.where(_len(t) > 0, k, 0)


def prefix_mismatches(short: Any, long: Any) -> int:
    """短い版が長い版の頭でない文の数(長い版の頭の字数ぶんを pyarrow で切り出して比べる=配列の計算)。"""
    s, lg = _pa(short), _pa(long)
    if len(s) == 0:
        return 0
    n_s = _len(np.asarray(short, dtype=object))
    n_l = _len(np.asarray(long, dtype=object))
    ok = n_l >= n_s
    # 長さごとに切り出す(長さの種類の数ぶん=逐次: ≤ 千)
    same = np.zeros(n_s.size, dtype=bool)
    for k in np.unique(n_s[ok]).tolist():
        m = np.flatnonzero(ok & (n_s == k))
        head = pc.utf8_slice_codeunits(lg.take(pa.array(m)), 0, int(k))
        same[m] = pc.equal(head, s.take(pa.array(m))).to_numpy(zero_copy_only=False)
    return int((~same).sum())


def _family_detail(f: PersonaFacts, lang: str) -> np.ndarray:
    """同居人の一覧(続き柄の語と年齢の短い語)。"""
    mem = f.members
    own = np.asarray(mem["owner"], dtype=np.int64)
    if own.size == 0:
        return np.full(f.n, "", dtype=object)
    cat = np.asarray(mem["cat"], dtype=np.int64)
    sex = np.asarray(mem["sex"], dtype=np.int64)
    age = np.asarray(mem["age"], dtype=np.int64)
    j = 0 if lang == "ja" else 1
    key = np.char.add(np.char.add(np.asarray(HOUSEHOLD_CATEGORIES, dtype=str)[cat], "|"), np.clip(sex, 0, 1).astype(str))
    word = _lut(key, lambda k: _REL_WORDS[k.split("|")[0]][j][int(k.split("|")[1])])
    agew = _lut(age, lambda a: _age_short(a, lang))
    item = word + ("(" if lang == "ja" else " (") + agew + ")"
    return _group_join(own, item, f.n, "・" if lang == "ja" else ", ")


def _places(f: PersonaFacts, lang: str, *, first: int | None, skip: int, mask_names: bool) -> np.ndarray:
    """なじみの場所の一覧(順位の順・``skip`` 件を飛ばして ``first`` 件まで)。"""
    pl = f.places
    own = np.asarray(pl["owner"], dtype=np.int64)
    if own.size == 0:
        return np.full(f.n, "", dtype=object)
    first_row = np.r_[True, own[1:] != own[:-1]]
    starts = np.flatnonzero(first_row)
    pos = np.arange(own.size) - np.repeat(starts, np.diff(np.r_[starts, own.size]))
    keep = (pos >= skip) & ((pos < skip + first) if first is not None else True)
    name = np.full(own.size, NAME_MASK, dtype=object) if mask_names else _s(pl["name"])
    cat = _s(pl["cat_ja" if lang == "ja" else "cat_en"])
    item = name + ("(" if lang == "ja" else " (") + cat + ")"
    return _group_join(own[keep], item[keep], f.n, "・" if lang == "ja" else ", ")


def _lines(f: PersonaFacts, lang: str, version: str, *, mask_names: bool) -> list[np.ndarray]:
    """行の列(短い版の行 → 長い版で足す行の順)。"""
    c = _cols(f)
    n = f.n
    ja = lang == "ja"
    j = 0 if ja else 1
    kind = _s(c["kind"])
    age = np.asarray(c["age"], dtype=np.int64)
    sex = np.asarray(c["sex"], dtype=np.int64)
    nat = _s(c["nationality"])
    flang = _s(c["first_language"])
    foreign = (nat != "") & (nat != A.JAPAN)
    akey = np.char.add(np.char.add(np.clip(age, 0, 120).astype(str), "|"), np.clip(sex, 0, 1).astype(str))
    agew = _lut(akey, lambda k: age_words(int(k.split("|")[0]), int(k.split("|")[1]), lang))

    # 1 人物
    natw = nat if ja else _lut(nat, lambda x: _NAT_EN.get(x, x))
    langw = _lut(flang, lambda x: A.LANGUAGE_NAMES.get(x, ("", ""))[j])
    if ja:
        who = "人物: " + agew + "。" + _when(foreign, "国籍は" + natw + "。") + _when(foreign & (langw != ""),
                                                                                   "第一言語は" + langw + "。")
    else:
        who = "Person: " + agew + "." + _when(foreign, " Nationality: " + natw + ".") + _when(
            foreign & (langw != ""), " First language: " + langw + ".")
    # 2 暮らし
    res = kind == "resident"
    inst = np.asarray(c["institution"], dtype=bool)
    chome = _s(c["home_chome"])
    hh = _household_phrase(f, lang)
    origin = _s(c["origin_name"])
    if ja:
        at = np.where(chome != "", chome + "で", "")
        home = np.where(inst, "暮らし: " + np.where(chome != "", chome + "の", "") + "施設で暮らしている。",
                        "暮らし: " + at + hh + "。")
        home = np.where(res, home, _when(origin != "", "暮らし: " + origin + "に住んでいる。"))
    else:
        at = np.where(chome != "", chome + "; ", "")
        home = np.where(inst, "Home: " + at + "lives in a care facility.", "Home: " + at + hh + ".")
        home = np.where(res, home, _when(origin != "", "Home: lives in " + origin + "."))
    # 3 仕事・学校
    lab = _s(c["labour"])
    st = _s(c["emp_status"])
    occ = _s(c["occupation"])
    ind = _s(c["industry"])
    role = _s(c["org_role"])
    duty = _s(c["duty_role"])
    area = _s(c["work_area"])
    wchome = _s(c["work_chome"])
    sector = _s(c["org_sector"])
    size = _s(c["org_size"])
    seated = _s(c["org_name"]) != ""
    stw = _lut(st, lambda x: _STATUS.get(x, ("", ""))[j])
    occw = _lut(occ, lambda x: _OCC.get(x, _OCC[""])[j])
    indw = _lut(ind, lambda x: _IND.get(x, ("", ""))[j])
    rolew = _lut(role, lambda x: _ROLE.get(x, ("", ""))[j])
    dutyw = _lut(duty, lambda x: _DUTY.get(x, ("", ""))[j])
    sizew = _lut(size, lambda x: dict(_SIZE_JA if ja else _SIZE_EN).get(x, ""))
    emp = lab == "employed"
    if ja:
        job = ("仕事: " + stw + occw + "をしている" + _when(indw != "", "(" + indw + ")") + "。"
               + _when(rolew != "", rolew + "。") + _when(dutyw != "", "受け持ちは" + dutyw + "。"))
        place = np.where(seated & (area == "stage"),
                         "勤め先は" + np.where(wchome != "", wchome + "にある", "") + sector + "の" + sizew + "事業所。",
                         np.where(area == "stage", _when(wchome != "", "勤め先は" + wchome + "。"),
                                  np.where(area == "home", "自宅で働いている。",
                                           np.where(area == "ward_outside_stage", "勤め先は渋谷区内の別の場所。",
                                                    _when(area == "outside_ward", "勤め先は渋谷区の外。")))))
        job = _when(emp, job + place)
        job = np.where(lab == "unemployed", "仕事: 仕事を探している。", job)
        job = np.where((lab == "not_in_labour_force") & (age >= 15) & (_s(c["school_kind"]).astype(str) == "none"),
                       "仕事: 仕事はしていない。", job)
    else:
        job = ("Work: " + occw + _when(stw != "", " " + stw) + _when(indw != "", " in " + indw) + "."
               + _when(rolew != "", " Works as " + rolew + ".") + _when(dutyw != "", " Responsible for " + dutyw + "."))
        place = np.where(seated & (area == "stage"),
                         " Workplace: " + sizew + " " + sector + " workplace" + np.where(wchome != "", " in " + wchome,
                                                                                         "") + ".",
                         np.where(area == "stage", _when(wchome != "", " Workplace: " + wchome + "."),
                                  np.where(area == "home", " Works from home.",
                                           np.where(area == "ward_outside_stage",
                                                    " Workplace: elsewhere in Shibuya Ward.",
                                                    _when(area == "outside_ward", " Workplace: outside Shibuya Ward.")))))
        job = _when(emp, job + place)
        job = np.where(lab == "unemployed", "Work: looking for a job.", job)
        job = np.where((lab == "not_in_labour_force") & (age >= 15) & (_s(c["school_kind"]).astype(str) == "none"),
                       "Work: not working.", job)
    sk = _s(c["school_kind"])
    sp = _s(c["school_place"])
    skw = _lut(sk, lambda x: _SCHOOL.get(x, ("", ""))[j])
    spw = _lut(sp, lambda x: _SCHOOL_PLACE.get(x, ("", ""))[j])
    if ja:
        school = _when(skw != "", "学校: " + skw + _when(spw != "", "(" + spw + ")") + "。")
    else:
        school = _when(skw != "", "School: " + skw + _when(spw != "", " " + spw) + ".")
    # 4 通勤
    mode = _s(c["commute_mode"])
    cm = np.asarray(c["commute_m"], dtype=np.int64)
    mins = np.maximum(1, np.round(np.nan_to_num(A.walk_seconds(np.maximum(cm, 0))) / SECONDS_PER_MINUTE)).astype(
        np.int64)  # 文は丸めた言葉(四捨五入)・W20 の片道は整数の分(切り上げ)=同じ関数 walk_seconds を通す
    minw = _lut(mins, lambda m: f"{m}分" if ja else english_number(m) + "-minute")
    ok_m = cm >= 0
    if ja:
        com = np.where(mode == "walk", "通勤: 家から勤め先まで歩いて" + minw + "ほど。",
                       np.where((mode == "rail") & (kind == "resident"), "通勤: 家から駅まで歩いて" + minw + "ほど。電車で通う。",
                                np.where((mode == "rail") & (kind == "commuter"),
                                         "通勤: 電車で渋谷に来て、駅から勤め先まで歩いて" + minw + "ほど。", "")))
    else:
        aw = _a(minw)
        com = np.where(mode == "walk", "Commute: " + aw + " walk from home to work.",
                       np.where((mode == "rail") & (kind == "resident"),
                                "Commute: " + aw + " walk to the station, then by train.",
                                np.where((mode == "rail") & (kind == "commuter"),
                                         "Commute: comes to Shibuya by train, then " + aw
                                         + " walk from the station to work.", "")))
    com = _when(emp & ok_m, com)
    # 5 お金
    wm = np.asarray(c["wage_monthly"], dtype=np.int64)
    # 世帯の資産は 18 歳以上の世帯員に配った(段 5)=未成年の本人の貯蓄の行は出さない(世帯の貯蓄は長い版)
    sv = np.where(age >= ADULT_AGE, np.asarray(c["savings"], dtype=np.int64), -1)
    wmw = _money(wm, lang)
    svw = _money(sv, lang)
    if ja:
        money = (_when(wm > 0, "月の給料はおよそ" + wmw + "。") + _when(sv > 0, "貯蓄はおよそ" + svw + "。")
                 + _when(sv == 0, "貯蓄はほとんどない。"))
        money = _when(money != "", "お金: " + money)
    else:
        money = (_when(wm > 0, " Monthly pay about " + wmw + ".") + _when(sv > 0, " Savings about " + svw + ".")
                 + _when(sv == 0, " Almost no savings."))
        money = _when(money != "", "Money:" + money)
    # 6 なじみの場所(上位 3)
    top = _places(f, lang, first=3, skip=0, mask_names=mask_names)
    fam = _when(top != "", ("なじみの場所: " if ja else "Familiar places: ") + top + ("。" if ja else "."))
    short = [who, home, job, school, com, money, fam]
    if version == "short":
        return short

    # ---- 長い版で足す行
    fd = _family_detail(f, lang)
    family = _when(fd != "", ("家族: " if ja else "Household members: ") + fd + ("。" if ja else "."))
    mates = np.asarray(c["dept_mates"], dtype=np.int64)
    oh = np.asarray(c["is_org_head"], dtype=bool)
    dh = np.asarray(c["is_dept_head"], dtype=bool)
    sup = np.asarray(c["has_supervisor"], dtype=bool)
    matew = _num_words(mates, lang)
    if ja:
        work2 = (_when(mates > 0, "同じ部署の同僚が" + matew + "人いる。") + _when(mates == 0, "同じ部署にほかの人はいない。")
                 + _when(oh, "組織の長。") + _when(dh & ~oh, "部署の長。") + _when(sup, "上司がいる。"))
        work2 = _when(seated & (work2 != ""), "職場: " + work2)
    else:
        work2 = (_when(mates > 0, " " + matew + " colleagues in the same team.") + _when(mates == 0, " No one else in the team.")
                 + _when(oh, " Heads the organization.") + _when(dh & ~oh, " Leads the team.")
                 + _when(sup, " Has a supervisor."))
        work2 = _when(seated & (work2 != ""), "Workplace:" + work2)
    oname = np.full(n, NAME_MASK, dtype=object) if mask_names else _s(c["org_name"])
    hours = np.asarray(c["weekly_hours"], dtype=np.float64)
    hr = np.where(np.isfinite(hours), np.round(np.nan_to_num(hours)), -1).astype(np.int64)
    hrw = _lut(np.maximum(hr, 0), lambda h: f"{h}時間" if ja else english_number(h) + " hours")
    if ja:
        emp2 = _when(seated, "勤め先の名前は" + oname + "。") + _when(emp & (hr > 0), "週の勤務はおよそ" + hrw + "。")
        emp2 = _when(emp2 != "", "働き方: " + emp2)
    else:
        emp2 = _when(seated, " Employer: " + oname + ".") + _when(emp & (hr > 0), " Works about " + hrw + " a week.")
        emp2 = _when(emp2 != "", "Job details:" + emp2)
    ten = _s(c["tenure"])
    tenw = _lut(ten, lambda x: _TENURE.get(x, ("", ""))[j])
    rp = _s(c["residence_period"])
    yrs = np.asarray(c["residence_years"], dtype=np.float64)
    yi = np.where(np.isfinite(yrs), np.floor(np.nan_to_num(yrs)), -1).astype(np.int64)
    yw = _num_words(np.maximum(yi, 0), lang)
    if ja:
        stay = np.where(rp == "since_birth", "生まれてからずっとこの町に住んでいる。",
                        np.where((yi >= 0) & (yi < 1), "この町に住んで一年に満たない。",
                                 _when(yi >= 1, "この町に住んで" + yw + "年ほど。")))
        house = _when(res & ~inst & ((tenw != "") | (stay != "")),
                      "住まい: " + _when(tenw != "", tenw + "。") + stay)
    else:
        stay = np.where(rp == "since_birth", " Has lived in this neighborhood since birth.",
                        np.where((yi >= 0) & (yi < 1), " Has lived here for less than a year.",
                                 _when(yi >= 1, " Has lived here for about " + yw + " years.")))
        house = _when(res & ~inst & ((tenw != "") | (stay != "")), "Housing:" + _when(tenw != "", " " + tenw + ".") + stay)
    wa = np.asarray(c["wage_annual"], dtype=np.int64)
    hs = np.asarray(c["hh_savings"], dtype=np.int64)
    hsz = np.asarray(c["hh_size"], dtype=np.int64)
    adult = age >= ADULT_AGE  # 本人の借入の行も 18 歳以上だけ(段 5 の配り方に合わせる)
    db = np.where(adult, np.asarray(c["debt"], dtype=np.int64), -1)
    cc = np.where(adult, np.asarray(c["consumer_credit"], dtype=np.int64), -1)
    if ja:
        money2 = (_when(wa > 0, "年収はおよそ" + _money(wa, lang) + "。")
                  + _when((hsz > 1) & (hs > 0), "世帯の貯蓄はおよそ" + _money(hs, lang) + "。")
                  + _when(db > 0, "借入(住宅ローンなど)がおよそ" + _money(db, lang) + "ある。") + _when(db == 0, "借入はない。")
                  + _when(cc > 0, "消費者金融などの借入がおよそ" + _money(cc, lang) + "ある。"))
        money2 = _when(money2 != "", "お金(詳しく): " + money2)
    else:
        money2 = (_when(wa > 0, " Annual pay about " + _money(wa, lang) + ".")
                  + _when((hsz > 1) & (hs > 0), " Household savings about " + _money(hs, lang) + ".")
                  + _when(db > 0, " Owes about " + _money(db, lang) + " (housing loans etc.).") + _when(db == 0, " No debts.")
                  + _when(cc > 0, " Consumer loans about " + _money(cc, lang) + "."))
        money2 = _when(money2 != "", "Money details:" + money2)
    rest = _places(f, lang, first=None, skip=3, mask_names=mask_names)
    outp = np.asarray(c["outside_places"], dtype=np.int64)
    if ja:
        fam2 = _when(rest != "", "ほかになじみの場所: " + rest + "。") + _when(outp > 0, "舞台の外にも行きつけの場所がある。")
    else:
        fam2 = _join_parts([_when(rest != "", "Other familiar places: " + rest + "."),
                            _when(outp > 0, "Also has regular places outside this area.")], " ")
    jl = np.asarray(c["japanese_level"], dtype=np.int64)
    jlw = _lut(np.clip(jl, 0, 5), lambda k: _JLEVEL[int(k)][j])
    lang2 = _when(foreign & (jl >= 0), ("言葉: " if ja else "Language: ") + jlw + ("。" if ja else "."))
    tipi = _tipi_line(c, lang)
    return short + [family, work2, emp2, house, money2, fam2, lang2, tipi]


def _tipi_line(c: Mapping[str, np.ndarray], lang: str) -> np.ndarray:
    """TIPI-J の行(腕=値があるときだけ・2〜14 点を 3 段の言葉に=低め 2〜6・ふつう 7〜10・高め 11〜14=宣言)。"""
    n = np.asarray(c["person_id"]).size
    if not all(k in c for k in TIPI_COLUMNS):
        return np.full(n, "", dtype=object)
    j = 0 if lang == "ja" else 1
    parts = []
    for k in TIPI_COLUMNS:  # 逐次: 5 次元
        v = np.asarray(c[k], dtype=np.float64)
        word = np.where(v < 7, "低め" if j == 0 else "low", np.where(v < 11, "ふつう" if j == 0 else "average",
                                                                    "高め" if j == 0 else "high"))
        parts.append(_when(np.isfinite(v), TIPI_WORDS[k][j] + ("は" if j == 0 else " ") + word))
    sep = "・" if j == 0 else ", "
    out = np.full(n, "", dtype=object)
    for p in parts:
        has = p != ""
        out = np.where(has & (out != ""), out + sep + p, np.where(has, p, out))
    head = "性格の自己評価(TIPI-J): " if j == 0 else "Self-rated personality (TIPI-J): "
    return _when(out != "", head + out + ("。" if j == 0 else "."))


#: 短い版の行の数(``_lines`` の頭の行=人物・暮らし・仕事・学校・通勤・お金・なじみの場所)。
_SHORT_LINES: Final[int] = 7


def render(facts: PersonaFacts, lang: str, version: str, *, mask_names: bool = False) -> np.ndarray:
    """事実の表 → 全員の文(``lang`` の型・``version`` の版)。同じ入力からは同じ文(決定的)。長い版は短い版の文に足す行を
    改行でつないだもの(短い版が頭=組み立てで決まる)。"""
    if lang not in LANGS:
        raise ValueError(f"lang は {LANGS} のどれか(いま {lang!r})")
    if version not in VERSIONS:
        raise ValueError(f"version は {VERSIONS} のどれか(いま {version!r})")
    lines = _lines(facts, lang, version, mask_names=mask_names)
    short = _join_lines(lines[:_SHORT_LINES], facts.n)
    if version == "short":
        return short
    return _join_parts([short, _join_lines(lines[_SHORT_LINES:], facts.n)], "\n")


def text_groups(texts: Sequence[str]) -> np.ndarray:
    """同じ文の組の番号(``np.unique`` の逆引き=区別できない組の数え・記録に文を写さない)。"""
    t = np.asarray(texts, dtype=object)
    if t.size == 0:
        return np.zeros(0, dtype=np.int64)
    return np.unique(t, return_inverse=True)[1].reshape(-1).astype(np.int64)


def persona_langs(cols: Mapping[str, Any]) -> tuple[np.ndarray, np.ndarray]:
    """体ごとの文の言語(``ja``・``en``・空=欄だけ)と出どころの語。"""
    fl = _s(cols["first_language"])
    nat = _s(cols["nationality"])
    lang = np.where(np.isin(fl, list(LANGS)), fl, "").astype(object)
    basis = np.where(lang != "", "first_language", "no_template").astype(object)
    assume = (fl == "") & (nat == "")
    lang = np.where(assume, "ja", lang).astype(object)
    basis = np.where(assume, "blank_assumed_ja", basis).astype(object)
    return lang, basis


def build_tables(facts: PersonaFacts, *, mask_names: bool = False) -> dict[str, dict[str, Any]]:
    """短い版と長い版の表(体 × 版 × 文・長さ)。文の無い体(欄だけ)は文が空。``tipi_*`` は空欄(腕)。"""
    c = _cols(facts)
    n = facts.n
    lang, basis = persona_langs(c)
    out: dict[str, dict[str, Any]] = {}
    texts = {v: np.full(n, "", dtype=object) for v in VERSIONS}
    for lg in LANGS:  # 逐次: 言語の数(2)
        idx = np.flatnonzero(lang == lg)
        if idx.size == 0:
            continue
        sub = facts.take(idx)
        for v in VERSIONS:  # 逐次: 版の数(2)
            texts[v][idx] = render(sub, lg, v, mask_names=mask_names)
    for v in VERSIONS:
        chars = _len(texts[v])
        cpt = np.where(lang == "en", CHARS_PER_TOKEN["en"], CHARS_PER_TOKEN["ja"])
        lines = _nlines(texts[v])
        named_poi = _named_poi(facts, v, built=lang != "")
        org_i = np.asarray(c["org_index"], dtype=np.int64)
        named_org = np.where((v == "long") & (lang != "") & (_s(c["org_name"]) != ""), org_i, -1)
        out[v] = {
            "person_id": np.asarray(c["person_id"], dtype=np.int32), "version": np.full(n, v, dtype=object),
            "lang": lang, "first_language": _s(c["first_language"]), "lang_basis": basis,
            "text": texts[v], "text_status": np.where(lang == "", "no_template", "built").astype(object),
            "text_source": np.full(n, "facts", dtype=object), "text_original": np.full(n, None, dtype=object),
            "chars": chars.astype(np.int32), "tokens_hint": np.round(chars / cpt).astype(np.int32),
            "lines": lines.astype(np.int16),
            **{k: (np.asarray(c[k], dtype=np.float32) if k in c else np.full(n, np.nan, dtype=np.float32))
               for k in TIPI_COLUMNS},
            "named_poi": named_poi, "named_org": named_org.astype(np.int32),
        }
    return out


def _named_poi(facts: PersonaFacts, version: str, *, built: np.ndarray) -> pa.ListArray:
    """文に名が出る POI の番号(短い版=順位の上位 3・長い版=載せた全部・文の無い体は空)。``pa.ListArray``(体ごと)。"""
    pl = facts.places
    own = np.asarray(pl["owner"], dtype=np.int64)
    poi = np.asarray(pl["poi_index"], dtype=np.int64)
    n = facts.n
    if own.size:
        first = np.r_[True, own[1:] != own[:-1]]
        starts = np.flatnonzero(first)
        pos = np.arange(own.size) - np.repeat(starts, np.diff(np.r_[starts, own.size]))
        keep = ((pos < 3) if version == "short" else np.ones(own.size, dtype=bool)) & np.asarray(built)[own]
        own, poi = own[keep], poi[keep]
    cnt = np.bincount(own, minlength=n) if own.size else np.zeros(n, dtype=np.int64)
    offsets = np.r_[0, np.cumsum(cnt)].astype(np.int32)
    return pa.ListArray.from_arrays(pa.array(offsets), pa.array(poi.astype(np.int32)))


# ------------------------------------------------------------------------------------------ 口
def compose_blocks(blocks: Mapping[str, str], persona_short: str, persona_long: str, length: str) -> dict[str, str]:
    """描画のブロックに人物の文を足す(``engine.decision.port.compose`` に渡す形)。engine に人物の欄が無いので、個体の
    部分の頭に置く: 短い版は B6 の前(B6 の文の頭)・長い版は B5 の前(B5 の文の頭)。共通部分(B0〜B4b)は触らない=短い版と
    長い版の頭は同じバイトのまま。"""
    if length not in VERSIONS:
        raise ValueError(f"length は {VERSIONS} のどれか(いま {length!r})")
    out = dict(blocks)
    b, text = ("B6", persona_short) if length == "short" else ("B5", persona_long)
    if text:
        out[b] = text + ("\n" + blocks[b] if blocks.get(b) else "")
    return out


class PersonaOverrideError(ValueError):
    """差し替えの口に、表に無い体や空の出どころを渡した。"""


def _rows_of(pid: np.ndarray, ids: Any) -> np.ndarray:
    """体の番号 → 表の行(表に無い番号があれば止める)。"""
    ids = np.asarray(ids, dtype=np.int64).reshape(-1)
    order = np.argsort(pid, kind="stable")
    k = np.searchsorted(pid[order], ids)
    k = np.clip(k, 0, max(pid.size - 1, 0))
    ok = (pid.size > 0) & (pid[order][k] == ids) if ids.size else np.zeros(0, dtype=bool)
    if ids.size and not np.all(ok):
        raise PersonaOverrideError(f"表に無い体: {ids[~ok][:5].tolist()}")
    if np.unique(ids).size != ids.size:
        raise PersonaOverrideError("同じ体が 2 回ある")
    return order[k]


def override(table: Mapping[str, Any], person_ids: Any, texts: Any, *, label: str,
             meta: Mapping[str, Any] | None = None) -> tuple[dict[str, Any], dict[str, Any]]:
    """人物の文を外から差し替える口(4-1b の腕「LLM が書いた人物像」を刺す)。返り値は(新しい表, manifest の欄)。

    ``person_ids`` と ``texts`` は同じ長さの配列(体の番号と新しい文)。差し替えた体は ``text`` が新しい文・``text_original``
    が元の文・``text_source`` が ``override:<label>``。長さの欄は新しい文で数え直す。元の表は書き換えない。``meta`` は
    書かせた LLM と版など(manifest に写す=呼び手が渡す)。"""
    if not label:
        raise PersonaOverrideError("差し替えの出どころ(label)が空")
    new = np.asarray(texts, dtype=object).reshape(-1)
    rows = _rows_of(np.asarray(table["person_id"], dtype=np.int64), person_ids)
    if rows.size != new.size:
        raise PersonaOverrideError("体の番号と文の数が違う")
    out = {k: (np.array(v, copy=True) if isinstance(v, np.ndarray) else v) for k, v in table.items()}
    text = np.asarray(out["text"], dtype=object)
    orig = np.asarray(out["text_original"], dtype=object)
    first = np.equal(orig[rows], None)  # 〔検収 L1〕事実の文は最初の差し替えのときだけ写す(2 回目からは残す)
    orig[rows[first]] = text[rows[first]]
    text[rows] = new
    out["text"], out["text_original"] = text, orig
    st = np.asarray(out["text_status"], dtype=object)
    st[rows] = "override"  # 〔検収 L2〕欄だけの体を差し替えても読める
    out["text_status"] = st
    src = np.asarray(out["text_source"], dtype=object)
    src[rows] = f"override:{label}"
    out["text_source"] = src
    chars = np.asarray(out["chars"]).astype(np.int64)
    chars[rows] = _len(new)
    out["chars"] = chars.astype(np.int32)
    lang = np.asarray(out["lang"]).astype(str)
    cpt = np.where(lang == "en", CHARS_PER_TOKEN["en"], CHARS_PER_TOKEN["ja"])
    out["tokens_hint"] = np.round(chars / cpt).astype(np.int32)
    lines = np.asarray(out["lines"]).astype(np.int64)
    lines[rows] = _nlines(new)
    out["lines"] = lines.astype(np.int16)
    man = {"label": label, "rows": int(rows.size), "meta": dict(meta or {})}
    return out, man


def with_big_five(facts: PersonaFacts, person_ids: Any, scores: Any, *, source: str) -> PersonaFacts:
    """Big Five(TIPI-J)の腕: 体の番号と 5 次元の得点((m, 5)・2〜14 点=川本ほか 2015 の尺度・並びは
    :data:`TIPI_COLUMNS`)を事実の表に入れる。入れた体だけ長い版に 1 行が足される(既定は空欄=行なし)。``source`` は得点の
    出どころ(実在の回答=PS3 (c) が使えるまで空)。"""
    if not source:
        raise PersonaOverrideError("TIPI-J の出どころ(source)が空")
    sc = np.asarray(scores, dtype=np.float64).reshape(-1, len(TIPI_COLUMNS))
    rows = _rows_of(np.asarray(facts.cols["person_id"], dtype=np.int64), person_ids)
    if rows.size != sc.shape[0]:
        raise PersonaOverrideError("体の番号と得点の数が違う")
    cols = dict(facts.cols)
    for d, k in enumerate(TIPI_COLUMNS):  # 逐次: 5 次元
        v = np.full(facts.n, np.nan)
        v[rows] = sc[:, d]
        cols[k] = v
    return PersonaFacts(cols, facts.members, facts.places)


NAMING_IDS_SCHEMA: Final[str] = "shibuya.build.pop.w21_persona/naming_ids/1"


def _list_column(col: Any) -> tuple[np.ndarray, np.ndarray]:
    """体ごとの番号の列(``pa.ListArray``・``ChunkedArray``・list の list)→(各行の数, 値)。"""
    a = col if isinstance(col, (pa.Array, pa.ChunkedArray)) else pa.array(list(col), type=pa.list_(pa.int32()))
    if isinstance(a, pa.ChunkedArray):
        a = pa.concat_arrays(a.chunks) if a.num_chunks else pa.array([], type=pa.list_(pa.int32()))
    lens = pc.list_value_length(a).to_numpy(zero_copy_only=False)
    lens = np.nan_to_num(lens.astype(np.float64)).astype(np.int64)
    vals = pc.list_flatten(a).to_numpy(zero_copy_only=False).astype(np.int64)
    return lens, vals


def naming_check_ids(table: Mapping[str, Any], *, poi: Sequence[int] = (), org: Sequence[int] = ()) -> dict[str, Any]:
    """CP5-3 を**番号で**見る口(検収の後の親の判断): 改変した POI の番号(``poi``)・組織の番号(``org``)を、文に名の出る
    番号の列(``named_poi``・``named_org``)と照らす。同じ名のチェーンの別の店は名指しに数えない(名の照合と違う)。
    返り値は名指しした体の番号と、番号ごとの数(文は写さない)。配列の計算だけ。"""
    pid = np.asarray(table["person_id"], dtype=np.int64)
    lens, vals = _list_column(table["named_poi"])
    owner = np.repeat(np.arange(pid.size), lens)
    want_p = np.asarray(list(poi), dtype=np.int64)
    hp = np.isin(vals, want_p)
    org_col = np.asarray(table["named_org"], dtype=np.int64)
    ho = np.isin(org_col, np.asarray(list(org), dtype=np.int64)) & (org_col >= 0)
    hit = np.zeros(pid.size, dtype=bool)
    hit[owner[hp]] = True
    hit |= ho
    by_poi = {int(k): int(c) for k, c in zip(*np.unique(vals[hp], return_counts=True))} if hp.any() else {}
    by_org = {int(k): int(c) for k, c in zip(*np.unique(org_col[ho], return_counts=True))} if ho.any() else {}
    return {"schema": NAMING_IDS_SCHEMA, "check": "persona_naming_ids", "poi": sorted(int(x) for x in want_p.tolist()),
            "org": sorted(int(x) for x in org), "texts": int((np.asarray(table["text"], dtype=object) != "").sum()),
            "ids": pid[hit].tolist(), "hits": int(hit.sum()), "by_poi": by_poi, "by_org": by_org,
            "found": bool(hit.any()),
            "note": "番号で照らす(同じ名のチェーンの別の店は数えない)。名の照合 naming_check は番号の無い名だけの補助"}


def naming_check(table: Mapping[str, Any], names: Sequence[str]) -> dict[str, Any]:
    """CP5-3 の補助(番号の無い名だけ=番号のある POI と組織は :func:`naming_check_ids`): 人物の文が改変した物の名
    (``names``=呼び手が渡す)を名指ししていないか(3-3b の ``engine.experiment.checks.persona_naming``)。名の部分一致なので、
    同じ名のチェーンの別の店も名指しに数える。返り値の ``hits`` は体の番号と名だけ(文は写さない)。

    この口だけが engine を import する(呼んだときに遅れて=engine のパッケージが ``shibuya.llm`` を読み込む・LLM は
    呼ばない=試験)。文の組み立て(``render``・``build_tables``)は engine を import しない。体ごとの文を写像に渡すので
    逐次: 文の数(呼び手の道具=組み立てでは呼ばない)。"""
    from shibuya.engine.experiment.checks import persona_naming

    pid = np.asarray(table["person_id"], dtype=np.int64)
    text = np.asarray(table["text"], dtype=object)
    has = text != ""
    # 口(3-3b)は id → 文の写像を受ける=表の文を写像にするだけ(記録には体の番号と名だけ)
    return persona_naming(dict(zip(pid[has].tolist(), text[has].tolist())), names)


# ------------------------------------------------------------------------------------------ W21 の資産 → 事実の表
def facts_from_w21(people: Mapping[str, Any], persons: Mapping[str, Any], households: Mapping[str, Any],
                   money: Mapping[str, Any], money_h: Mapping[str, Any], places: Mapping[str, Any],
                   poi: Mapping[str, Any], org_names: Sequence[str], org_table: Mapping[str, Any],
                   lang_cols: Mapping[str, Any], chome_names: Mapping[str, str],
                   origin_names: Mapping[str, str]) -> PersonaFacts:
    """段 1〜7 の資産の表 → 事実の表(読むだけ)。``people``=``w21_people``(並びが人の並び)・``persons``=段 1〜3 の
    住民(``person_id`` で結ぶ)・``households``・``money``(``person_id``)・``money_h``(``household_id``)・``places``=
    ``w21_prior_places``・``poi``=W6 の POI(``name``・``cat``・``subcat``)・``org_names``=W6 の組織の名(``org_index`` の
    並び)・``org_table``=``w21_org``・``lang_cols``=段 9 の言語の列(``nationality``・``first_language``・
    ``japanese_level``=``people`` の並び)・``chome_names``=町丁目の鍵 → 名・``origin_names``=市区町村の符号 → 名。"""
    pid = np.asarray(people["person_id"], dtype=np.int64)
    n = pid.size
    pos = np.full(int(pid.max()) + 1 if n else 0, -1, dtype=np.int64)
    pos[pid] = np.arange(n)
    kind = _s(people["kind"])
    # 段 1〜3 の住民の列(住んでいる人だけ)
    rp_pid = np.asarray(persons["person_id"], dtype=np.int64)
    rpos = pos[rp_pid]

    def from_persons(col: str, blank: Any) -> np.ndarray:
        out = np.full(n, blank, dtype=object if isinstance(blank, str) else np.asarray(blank).dtype)
        out[rpos] = np.asarray(persons[col])
        return out

    school_kind = _s(from_persons("school_kind", ""))
    school_place = _s(from_persons("school_place", ""))
    rperiod = _s(from_persons("residence_period", ""))
    rel = _s(people["relation"])
    hid = np.asarray(people["household_id"], dtype=np.int64)
    h_id = np.asarray(households["household_id"], dtype=np.int64)
    hpos = np.full(int(h_id.max()) + 1 if h_id.size else 0, -1, dtype=np.int64)
    hpos[h_id] = np.arange(h_id.size)
    has_h = hid >= 0
    hrow = np.where(has_h, hpos[np.clip(hid, 0, None)], -1)
    tenure = np.where(hrow >= 0, _s(households["tenure"])[np.clip(hrow, 0, None)], "").astype(object)
    hsize = np.where(hrow >= 0, np.asarray(households["size"], dtype=np.int64)[np.clip(hrow, 0, None)], -1)
    inst = rel == "institution_resident"
    # 世帯の同居人(本人から見た区分)
    from .w21_org import relation_pairs

    u, v = relation_pairs(np.where(inst, -1, hid))
    cat = relation_category(rel[u], rel[v])
    cat_i = np.array([HOUSEHOLD_CATEGORIES.index(x) for x in cat.tolist()], dtype=np.int64) if cat.size else \
        np.zeros(0, dtype=np.int64)
    age = np.asarray(people["age"], dtype=np.int64)
    sex = np.asarray(people["sex"], dtype=np.int64)
    order = np.lexsort((-age[v], cat_i, u))
    members = {"owner": u[order], "cat": cat_i[order], "age": age[v][order], "sex": sex[v][order]}
    # なじみの場所(舞台の POI だけ・順位の順)
    pp = np.asarray(places["person_id"], dtype=np.int64)
    pk = _s(places["place_kind"])
    pi = np.asarray(places["poi_index"], dtype=np.int64)
    rk = np.asarray(places["rank"], dtype=np.int64)
    ok = (pk == "poi") & (pi >= 0)
    cw_ja, cw_en = place_words(poi["cat"], poi["subcat"])
    pname = _s(poi["name"])
    sel = np.flatnonzero(ok)
    po = pos[pp[sel]]
    order = np.lexsort((rk[sel], po))
    sel, po = sel[order], po[order]
    plc = {"owner": po, "rank": rk[sel], "poi_index": pi[sel], "name": pname[pi[sel]], "cat_ja": cw_ja[pi[sel]],
           "cat_en": cw_en[pi[sel]]}
    # 職場
    org_i = np.asarray(people["org_index"], dtype=np.int64)
    seated = org_i >= 0
    oi = np.clip(org_i, 0, None)
    onames = np.asarray(list(org_names), dtype=object)
    sector = _s(org_table["sector_detail"])
    size = _s(org_table["size_band"])
    dep = np.asarray(people["department_id"], dtype=np.int64)
    dcnt = np.bincount(dep[dep >= 0], minlength=int(dep.max()) + 1 if (dep >= 0).any() else 0)
    mates = np.where(dep >= 0, dcnt[np.clip(dep, 0, None)] - 1 if dcnt.size else -1, -1)
    # お金
    m_pid = np.asarray(money["person_id"], dtype=np.int64)
    mpos = pos[m_pid]

    def from_money(col: str) -> np.ndarray:
        out = np.full(n, -1, dtype=np.int64)
        out[mpos] = np.asarray(money[col], dtype=np.int64)
        return out

    mh_id = np.asarray(money_h["household_id"], dtype=np.int64)
    mh_pos = np.full(int(mh_id.max()) + 1 if mh_id.size else 0, -1, dtype=np.int64)
    mh_pos[mh_id] = np.arange(mh_id.size)
    hh_sv = np.full(n, -1, dtype=np.int64)
    if mh_pos.size:
        r = np.where(has_h & (hid < mh_pos.size), mh_pos[np.clip(hid, 0, mh_pos.size - 1)], -1)
        okr = r >= 0
        hh_sv[okr] = np.asarray(money_h["savings"], dtype=np.int64)[r[okr]]
    chome_lut = lambda k: chome_names.get(k, "")  # noqa: E731
    origin = _s(people["origin_muni"])
    cols = {
        "person_id": pid, "kind": kind, "age": age, "sex": sex,
        "nationality": _s(lang_cols["nationality"]), "first_language": _s(lang_cols["first_language"]),
        "japanese_level": np.asarray(lang_cols["japanese_level"], dtype=np.int64),
        "home_chome": _lut(_s(people["home_chome_key"]), chome_lut), "institution": inst,
        "origin_name": np.where(kind == "commuter", _lut(origin, lambda k: origin_names.get(k, "")), "").astype(object),
        "tenure": tenure, "residence_period": rperiod,
        "residence_years": np.asarray(people["residence_years"], dtype=np.float64),
        "labour": _s(people["labour_status"]), "emp_status": _s(people["emp_status"]),
        "occupation": _s(people["occupation_major"]), "industry": _s(people["industry_major"]),
        "org_role": _s(people["org_role"]), "duty_role": _s(people["duty_role"]),
        "org_index": np.where(seated, org_i, -1).astype(np.int64),
        "org_name": np.where(seated, onames[oi] if onames.size else "", "").astype(object),
        "org_sector": np.where(seated, sector[oi] if sector.size else "", "").astype(object),
        "org_size": np.where(seated, size[oi] if size.size else "", "").astype(object),
        "work_area": _s(people["workplace_area"]), "work_chome": _lut(_s(people["work_chome_key"]), chome_lut),
        "is_org_head": np.asarray(people["is_org_head"], dtype=bool),
        "is_dept_head": np.asarray(people["is_dept_head"], dtype=bool), "dept_mates": mates.astype(np.int64),
        "has_supervisor": np.asarray(people["supervisor_id"], dtype=np.int64) >= 0,
        "weekly_hours": np.asarray(people["weekly_hours_hint"], dtype=np.float64),
        "school_kind": school_kind, "school_place": school_place,
        "commute_mode": _s(people["commute_mode"]), "commute_m": np.asarray(people["commute_path_m"], dtype=np.int64),
        "wage_monthly": from_money("wage_monthly"), "wage_annual": from_money("wage_annual"),
        "savings": from_money("savings"), "debt": from_money("debt"), "consumer_credit": from_money("consumer_credit"),
        "hh_size": hsize.astype(np.int64), "hh_savings": hh_sv.astype(np.int64),
        "outside_places": np.asarray(people["familiar_outside"], dtype=np.int64),
    }
    missing = [k for k in FACT_COLUMNS if k not in cols]
    if missing:
        raise KeyError(f"事実の表に無い列: {missing}")
    return PersonaFacts(cols, members, plc)
