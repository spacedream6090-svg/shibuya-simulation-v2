"""engine.wom — **会話からの店の抽出**(D-120 7b・N3 (a)・口コミ=伝聞の書き手・第297)。

正典: ``docs/design/v2-store-memory-implementation-agenda.md`` §2(段 7b の 1〜6)。上位=
``docs/design/v2-memory-wom-internet-draft.md`` §1-2 の 2 (ii)・1-5 N3 (a)。

どこで・何から
    ``engine.run`` の ``_utter``(会話ターンの応答のパース時・``MemoryLayer.note_utterance`` の隣)。**呼数 0**
    (正規表現+辞書照合)。語彙 v1/v2=「ひと言」欄・v3=理由欄+対象欄(発話本文が無い=薄い・宣言)。
    ``--store-memory on`` のランだけ(書き先は店の評価の記憶=7a)。

店名の照合(正規化 v0・宣言)
    - 辞書=W6 の ``name`` のうち**店**(``poi_target.BUYABLE_CATS``・合成世界は全部)の名。事務所・学校・
      ホテル・目印は入れない(店の評価ではない)。
    - 正規化 v0(名と発話の両方): NFKC(全角/半角)・英字は小文字・空白を全部消す。
    - 名の鍵: 正規化した名そのもの+**支店の接尾辞を外した名**(1 回だけ): 空白で区切った最後の語が「店」で
      終わる(「一蘭 渋谷店」→「一蘭」)/ 末尾が :data:`BRANCH_SUFFIXES_V0`(渋谷本店・渋谷店・本店・渋谷 …・
      「店」)。外した残りが 2 字未満・カテゴリ語/総称語なら作らない。2 字未満の名は鍵にしない。
    - 別名表 v0 は**空**(チェーン名・略称の表は空欄=問い)。
    - 照合=**最長一致**(左から・その位置で一番長い鍵・重ならない)。境界(v0): 英数字の鍵は前後が英数字でない・
      カタカナで始まる/終わる鍵は前/後がカタカナでない・**2 字の鍵は後ろの字が鍵の最後の字と同じ字種でない**
      (「一番近い」を「一番」にしない)。
    - 同名の POI が複数(チェーン)なら**話し手のセルに近い順**(``cell_dist``・同距離は POI 索引の小さい方)で
      1 件。話し手のセルが範囲外なら索引の小さい方。
    - 照合できない「店らしき語」(:data:`STORE_WORD_RE_V0`=漢字/カタカナ/英数字の 1〜15 字+「屋・店・カフェ・
      食堂・亭・軒・酒場」)は照合した名の範囲の外にあり、総称(:data:`STORE_WORD_GENERIC_V0`・カテゴリ語)で
      なければ ``wom_unmatched`` に数える。

評価語の辞書 v0(宣言・問い)
    :data:`VALENCE_POSITIVE_V0` / :data:`VALENCE_NEGATIVE_V0`(正規化してから最長一致・重ならない)→
    向き=sign(+の数 − −の数)。**同じ発話に店名と評価語が両方あるときだけ向きを付ける**・無ければ 0
    (知っているだけ)。1 発話に店が複数なら全部に同じ向き(v0)。

聞き手への転写(行動契約書 §4 の重み)
    宛先(会話の相手)1.0・非宛先 0.5・傍受 0.2 のうち**本段は宛先だけ**(非宛先・傍受は B5 傍受が未実装=
    後・宣言)。宛先の店の行に 出どころ=伝聞(σ=2 → 精度 +重み × 1/4)・向き=評価語。話し手の行には書かない。

逐次ループ宣言(P4): 1 発話の文字数ぶん(≤ 数十字)×その位置から始まる鍵の数=呼ごとの文字列処理(呼数比例)。
体数に比例するループは無い。
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any, Final, NamedTuple, Sequence

import numpy as np

from shibuya.engine.poi_target import BUYABLE_CATS, CATEGORY_WORDS, GENERIC_WORDS, SYNTHETIC_BUYABLE_CATS
from shibuya.engine.store_memory import STORE_SOURCE_BIT

__all__ = [
    "WOM_TEXT_FIELDS",
    "WOM_WEIGHT",
    "NAME_MIN_CHARS_V0",
    "BRANCH_SUFFIXES_V0",
    "STORE_WORD_RE_V0",
    "STORE_WORD_GENERIC_V0",
    "VALENCE_POSITIVE_V0",
    "VALENCE_NEGATIVE_V0",
    "normalize_v0",
    "WomExtraction",
    "WomExtractor",
    "hear",
]

#: 語彙の版 → 読む欄(v1/v2=ひと言・v3=理由+対象)。
WOM_TEXT_FIELDS: Final[dict[str, tuple[str, ...]]] = {
    "v1": ("comment",), "v2": ("comment",), "v3": ("reason", "target"),
}
#: 聞き手への転写の重み(行動契約書 §4)。本段は宛先だけを使う。
WOM_WEIGHT: Final[dict[str, float]] = {"addressee": 1.0, "bystander": 0.5, "overheard": 0.2}
#: 鍵にする名の最小字数(正規化後)。
NAME_MIN_CHARS_V0: Final[int] = 2
#: 支店の接尾辞(長い順に 1 回だけ外す・v0)。空白区切りの最後の語が「店」で終わる場合は別に外す。
BRANCH_SUFFIXES_V0: Final[tuple[str, ...]] = (
    "渋谷駅前店", "渋谷本店", "渋谷駅店", "渋谷店", "本店", "渋谷", "店",
)
#: 「店らしき語」(照合できなければ ``wom_unmatched``・v0)。正規化後の文字列に掛ける。
STORE_WORD_RE_V0: Final[re.Pattern[str]] = re.compile(
    r"([一-龯々〆ヵヶァ-ヴーa-z0-9・&']{1,15})(屋|店|カフェ|食堂|亭|軒|酒場)"
)
#: 店らしき語の総称(店の名ではない=数えない・v0)。
STORE_WORD_GENERIC_V0: Final[frozenset[str]] = frozenset({
    "本屋", "薬屋", "花屋", "肉屋", "魚屋", "八百屋", "居酒屋", "飲み屋", "そば屋", "蕎麦屋", "寿司屋",
    "鮨屋", "牛丼屋", "定食屋", "ラーメン屋", "パン屋", "ケーキ屋", "服屋", "古着屋", "雑貨屋", "酒屋",
    "飲食店", "喫茶店", "書店", "売店", "商店", "本店", "支店", "名店", "新店", "同店", "当店", "各店",
    "閉店", "開店", "来店", "入店", "出店", "店", "物販店", "食品店", "専門店", "料理店", "洋菓子店",
    "和菓子店", "小売店", "量販店", "百貨店", "飲食", "食堂", "カフェ", "酒場", "定食", "茶屋",
    "餃子屋", "弁当屋", "うどん屋", "焼肉屋", "焼鳥屋", "焼き鳥屋", "カレー屋", "中華屋", "天ぷら屋", "洋食屋",
    "牛丼店", "定食店", "和食店", "中華料理店", "店舗", "屋台",
    "飯屋", "人気店", "チェーン店", "酒店", "通販店", "目的店", "目標店", "隣接店", "近隣店", "露店",
    "テイクアウト店", "食材店",
})
#: 評価語の辞書 v0(+1)。正規化(NFKC・小文字)してから最長一致。裸の「良い」は入れない(実 LLM テープの
#: 理由欄の「食後は歩くのが良い」を拾うため)。第297 親決定 Q78: 「人気」「評判」「満足」は入れない(用法が曖昧)。
VALENCE_POSITIVE_V0: Final[tuple[str, ...]] = (
    "良かった", "よかった", "良い店", "いい店", "おいしい", "美味しい", "おいしかった", "美味しかった",
    "うまい", "旨い", "うまかった", "おすすめ", "オススメ", "お勧め", "お薦め", "安い", "安かった", "割安", "お得",
    "快適", "最高", "気に入った", "気に入って", "好き", "楽しかった", "楽しい", "便利", "親切", "丁寧",
    "きれい", "綺麗", "落ち着く", "居心地がいい", "居心地が良い", "空いていた", "空いてた", "すいていた",
    "すいてた",
)
#: 評価語の辞書 v0(−1)。裸の「高い」は入れない(「必要性が高い」を拾うため)。**第298 親決定 Q83**: 「営業時間外」
#: 「閉店」は −1 に**戻す**(第297 Q78 の「状態だから 0」を撤回=自分の訪問の向きの表 `STORE_VALENCE_NEGATIVE`
#: (CLOSED → −1)と修正 4「失敗の回避」に揃える。「人気/評判/満足」は +1 にしないまま)。
VALENCE_NEGATIVE_V0: Final[tuple[str, ...]] = (
    "まずい", "不味い", "まずかった", "ひどい", "ひどかった", "酷い", "値段が高い", "高かった", "高すぎ", "割高",
    "混んでいた", "混んでた", "混んでいる", "混んでる", "混雑", "満席", "閉まっていた", "閉まってた",
    "閉まっている", "閉まってる", "売り切れ", "品切れ", "在庫切れ", "待たされた", "最悪",
    "営業時間外", "閉店",  # 第298 Q83
    "残念", "がっかり", "不満", "汚い", "うるさい", "微妙", "良くない", "よくない", "良くなかった",
    "よくなかった", "おいしくない", "美味しくない", "おいしくなかった", "美味しくなかった", "うまくない",
    "人気がない", "人気がなかった",
)
_WS: Final[re.Pattern[str]] = re.compile(r"\s+")
_FIELD_SEP: Final[str] = "|"
_NONE_WORDS: Final[frozenset[str]] = frozenset({"", "なし", "無し"})
#: 人の参照(対象欄の ``P-<id>``)は店の名と照合しない(数字だけの店名 「526」 と取り違えない)。
_PERSON_REF: Final[re.Pattern[str]] = re.compile(r"p-\d+")
_DIGITS_ONLY: Final[re.Pattern[str]] = re.compile(r"^[\d\W_]+$")
_VAL_LABEL: Final[dict[int, str]] = {1: "+1", 0: "0", -1: "-1"}


def normalize_v0(text: str) -> str:
    """正規化 v0: NFKC(全角/半角)・英字は小文字・空白を全部消す。"""
    return _WS.sub("", unicodedata.normalize("NFKC", str(text or "")).lower())


def _script(ch: str) -> str:
    if not ch:
        return ""
    o = ord(ch)
    if ch.isascii():
        return "ascii" if ch.isalnum() else "punct"
    if 0x30A0 <= o <= 0x30FF or ch == "ー":
        return "kata"
    if 0x3040 <= o <= 0x309F:
        return "hira"
    if 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or ch in "々〆":
        return "kanji"
    return "other"


def _branch_stripped(raw_name: str) -> str:
    """支店の接尾辞を外した名(正規化前の空白を使う)。外せなければ ``""``。"""
    nk = unicodedata.normalize("NFKC", str(raw_name)).strip()
    parts = nk.split()
    if len(parts) >= 2 and parts[-1].endswith("店"):
        return normalize_v0(" ".join(parts[:-1]))
    n = normalize_v0(nk)
    for suf in BRANCH_SUFFIXES_V0:  # 接尾辞の数ぶん(≤ 7)
        if n.endswith(suf) and len(n) > len(suf):
            return n[: -len(suf)]
    return ""


def _by_first(words: Sequence[str]) -> dict[str, list[str]]:
    """語 → 最初の字ごとの長い順の表(照合の走査をその位置で始まる語に絞る)。"""
    out: dict[str, list[str]] = {}
    for w in words:
        out.setdefault(w[0], []).append(w)
    return {c: sorted(v, key=lambda s: (-len(s), s)) for c, v in out.items()}


def _longest_words(text: str, by_first: dict[str, list[str]]) -> list[str]:
    """``text`` の中の語(最初の字ごとの表)を左から最長一致・重ならないで拾う(逐次: 文字数 × その字の語)。"""
    out: list[str] = []
    i = 0
    while i < len(text):
        hit = next((w for w in by_first.get(text[i], ()) if text.startswith(w, i)), "")
        if hit:
            out.append(hit)
            i += len(hit)
        else:
            i += 1
    return out


class WomExtraction(NamedTuple):
    """1 発話の抽出結果。"""

    pois: tuple[int, ...]          # 照合できた店(話し手に近いチェーンの 1 件ずつ・出現順・重複なし)
    names: tuple[str, ...]         # 照合した鍵(正規化後)
    valence: int                   # 向き(店があるときだけ −1/0/+1・店が無ければ 0)
    positive: tuple[str, ...]      # 拾った評価語(+)
    negative: tuple[str, ...]      # 拾った評価語(−)
    unmatched: tuple[str, ...]     # 照合できない店らしき語
    text: str                      # 正規化した発話(欄は | でつなぐ)


class WomExtractor:
    """店名の辞書と評価語の辞書(1 ランに 1 つ・世界は読むだけ)。"""

    def __init__(self, names: Sequence[str], cats: Sequence[str], poi_cell: np.ndarray,
                 cell_dist: np.ndarray | None) -> None:
        n = len(names)
        self.n_poi = n
        self.poi_cell = np.asarray(poi_cell, dtype=np.int64)[:n] if n else np.zeros(0, dtype=np.int64)
        self.cell_dist = cell_dist
        shop_cats = set(BUYABLE_CATS) | set(SYNTHETIC_BUYABLE_CATS)
        cat_words = {normalize_v0(w) for w, _c, _s in CATEGORY_WORDS} | {normalize_v0(w) for w in GENERIC_WORDS}
        keys: dict[str, list[int]] = {}
        for j in range(n):  # 逐次: POI の数ぶん(ランの始めに 1 回)
            if str(cats[j]) not in shop_cats:
                continue
            full = normalize_v0(names[j])
            for k in (full, _branch_stripped(names[j])):
                if len(k) >= NAME_MIN_CHARS_V0 and k not in cat_words and not _DIGITS_ONLY.match(k):
                    lst = keys.setdefault(k, [])
                    if j not in lst:
                        lst.append(j)
        self.keys: dict[str, tuple[int, ...]] = {k: tuple(v) for k, v in keys.items()}
        self._by_first = _by_first(list(self.keys))
        self._generic = {normalize_v0(w) for w in STORE_WORD_GENERIC_V0} | cat_words
        self._generic_tails = tuple(sorted((g for g in self._generic if len(g) >= 2), key=len, reverse=True))
        self._cat_tails = tuple(sorted(cat_words, key=len, reverse=True))
        self._val_words = _by_first(sorted({normalize_v0(w) for w in VALENCE_POSITIVE_V0
                                            + VALENCE_NEGATIVE_V0}))
        self._neg = frozenset(normalize_v0(w) for w in VALENCE_NEGATIVE_V0)
        self.stats: Counter = Counter()
        self.top: Counter = Counter()
        self.unmatched_words: Counter = Counter()

    @classmethod
    def from_world(cls, world: Any) -> "WomExtractor":
        a = world.assets
        return cls(tuple(getattr(a, "poi_name", ()) or ()), tuple(getattr(a, "poi_cat", ()) or ()),
                   np.asarray(world.pois.cell, dtype=np.int64), getattr(a, "cell_dist", None))

    # ------------------------------------------------------------------ 照合
    def _ok_boundary(self, text: str, i: int, key: str) -> bool:
        prev = text[i - 1] if i > 0 else ""
        nxt = text[i + len(key)] if i + len(key) < len(text) else ""
        s0, s1 = _script(key[0]), _script(key[-1])
        if s0 == "ascii" and _script(prev) == "ascii":
            return False
        if s1 == "ascii" and _script(nxt) == "ascii":
            return False
        if s0 == "kata" and _script(prev) == "kata":
            return False
        if s1 == "kata" and _script(nxt) == "kata":
            return False
        if len(key) <= 2 and nxt and _script(nxt) == s1:
            return False
        return True

    def _pick(self, pois: tuple[int, ...], cell: int) -> int:
        if len(pois) == 1 or self.cell_dist is None or cell < 0 or cell >= len(self.cell_dist):
            return min(pois)
        pc = self.poi_cell[list(pois)]
        d = np.array([int(self.cell_dist[cell, c]) if 0 <= c < len(self.cell_dist) else 1 << 30
                      for c in pc.tolist()], dtype=np.int64)  # チェーンの数ぶん(≤ 33)
        order = np.lexsort((np.asarray(pois), d))
        return int(pois[int(order[0])])

    def extract(self, text: str, speaker_cell: int = -1) -> WomExtraction:
        """正規化した 1 発話 → 店・向き・店らしき語(逐次: 文字数 × その位置の鍵の数)。"""
        t = _PERSON_REF.sub("|", str(text))
        pois: list[int] = []
        names: list[str] = []
        spans: list[tuple[int, int]] = []
        i = 0
        while i < len(t):
            hit = ""
            for k in self._by_first.get(t[i], ()):
                if t.startswith(k, i) and self._ok_boundary(t, i, k):
                    hit = k
                    break
            if hit:
                p = self._pick(self.keys[hit], int(speaker_cell))
                if p not in pois:
                    pois.append(p)
                    names.append(hit)
                spans.append((i, i + len(hit)))
                i += len(hit)
            else:
                i += 1
        unmatched: list[str] = []
        for m in STORE_WORD_RE_V0.finditer(t):  # 店らしき語の数ぶん
            s, e = m.span()
            if any(a < e and s < b for a, b in spans):
                continue
            word, stem = m.group(0), m.group(1)
            if (word in self._generic or stem in self._generic
                    or word.endswith(self._generic_tails) or stem.endswith(self._cat_tails)):
                continue  # 総称・「X+総称」(カテゴリ飲食店・10時開店)・「カテゴリ語+屋」(ラーメン屋)
            unmatched.append(word)
        pos: tuple[str, ...] = ()
        neg: tuple[str, ...] = ()
        valence = 0
        if pois:
            masked = list(t)  # 店の名の中の語(「満足」「人気」)を評価語に数えない
            for a, b in spans:
                masked[a:b] = ["|"] * (b - a)
            got = _longest_words("".join(masked), self._val_words)
            neg = tuple(w for w in got if w in self._neg)
            pos = tuple(w for w in got if w not in self._neg)
            valence = int(np.sign(len(pos) - len(neg)))
        return WomExtraction(tuple(pois), tuple(names), valence, pos, neg, tuple(unmatched), t)

    def utterance_text(self, vocab_version: str, *, comment: str = "", reason: str = "",
                       target: str = "") -> str:
        """語彙の版 → 読む欄を正規化して | でつなぐ(「なし」の欄は読まない)。"""
        fields = {"comment": comment, "reason": reason, "target": target}
        parts = [normalize_v0(fields[f]) for f in WOM_TEXT_FIELDS.get(str(vocab_version), ("comment",))]
        return _FIELD_SEP.join(p for p in parts if p not in _NONE_WORDS)

    def observe(self, ex: WomExtraction) -> None:
        """1 発話の抽出を計数へ(manifest ``wom``)。"""
        self.stats["utterances"] += 1
        if ex.pois:
            self.stats["wom_extracted"] += 1
            self.stats["wom_valence" + _VAL_LABEL[ex.valence]] += 1
            if ex.valence != 0:
                self.stats["wom_with_valence"] += 1
            self.stats["wom_pois"] += len(ex.pois)
            self.top.update(ex.pois)
        if ex.unmatched:
            self.stats["wom_unmatched"] += 1
            self.stats["wom_unmatched_words"] += len(ex.unmatched)
            self.unmatched_words.update(ex.unmatched)

    def _top_by_name(self, names: Sequence[str]) -> dict[str, int]:
        """照合できた店の上位 20(同名のチェーンは名で合算)。"""
        by: Counter = Counter()
        for j, c in self.top.items():  # 照合できた店の数ぶん
            by[str(names[j]) if 0 <= j < len(names) else str(j)] += int(c)
        return dict(by.most_common(20))

    def summary(self, names: Sequence[str] = ()) -> dict[str, Any]:
        """manifest ``wom``: 発話・抽出・向き・照合できない語・照合できた店の上位。"""
        u = max(1, self.stats.get("utterances", 0))
        return {
            "text_fields": {k: list(v) for k, v in WOM_TEXT_FIELDS.items()},
            "weight_addressee": WOM_WEIGHT["addressee"],
            "dictionary_keys": len(self.keys),
            "counts": {k: int(v) for k, v in sorted(self.stats.items())},
            "extracted_share": round(self.stats.get("wom_extracted", 0) / u, 4),
            "with_valence_share": round(self.stats.get("wom_with_valence", 0) / u, 4),
            "unmatched_share": round(self.stats.get("wom_unmatched", 0) / u, 4),
            "top_pois": self._top_by_name(names),
            "top_unmatched_words": dict(self.unmatched_words.most_common(20)),
        }


def hear(store: Any, agents: Any, tick: int, listener: int, ex: WomExtraction,
         weight: float = WOM_WEIGHT["addressee"]) -> int:
    """抽出した店を聞き手(宛先)の店の行へ(出どころ=伝聞・精度 +重み × 1/σ²)→ 書いた行の数。"""
    if store is None or not ex.pois or int(listener) < 0:
        return 0
    k = len(ex.pois)
    store.write(agents, int(tick), np.full(k, int(listener)), np.asarray(ex.pois, dtype=np.int64),
                np.full(k, int(ex.valence)), np.full(k, STORE_SOURCE_BIT["wom"]), scale=float(weight))
    store.stats["events:wom"] += k
    store.stats["events:wom:valence" + _VAL_LABEL[ex.valence]] += k
    return k
