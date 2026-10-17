# -*- coding: utf-8 -*-
"""dm_eval.judge — 候補の当て口 ``Scorer`` と採点の器(第 6 期 6-1・DM1・DM5・DM9・§1-9)。

当て口(差し替えられる口)
    ``Scorer.score(situation, candidates, *, text=None) -> 分布``。``candidates`` は提示した候補(番号つき=
    ``situations.orders`` の 1 通り)、``text`` は DM4 の短い版の文(文を読む当て口だけが使う)。分布は候補の id
    (と「その他」``OTHER_ID``)→ 確率(和 1)。本段で実装するのは 3 つ(どれも GPU を使わない):
    - ``MockScorer``(対照): 単体の上で一様(Dirichlet(1))な重みを、種と状況の id の鍵から**候補の中身の順**に引く
      =決定的・提示の並びに左右されない(位置の偏りの負の対照)。
    - ``ClassicalScorer``(基準): 今の古典モデル(``engine.classical`` の方策 classical)の判断の分布=活動の事前分布
      (``ActivityPrior``・錨 ``ssb2021_activity_prior_v0.json``・状態の乗数は既定の 1.0=IPF なし)を対応表 v0
      (``ACTIVITY_MAP_V0``)で行為の語にし、語彙 v1 に読み替えた物(``compat_word``)。中身だけで決まる(負の対照)。
    - ``TapeScorer``(基準=System 2 の原型の記録): テープの応答の行為の語に確率 1(語彙 v1 の外は「その他」)。
      テープの LLM は B0 の固定の並びを見ていて、ここで入れ替えた並びは見ていない(=並べ替えに対しては構成上 0)。
    口だけ(``implemented=False``・``score`` は ``ScorerUnavailable``=S6 の後): ``ClefScorer``(Clef-flash・Clef)・
    ``KevScorer``(Kev-9B)・``SokudanScorer``(即断 sokudan-ja-310m)・``GScorer``((G)=基準)。重みは取らない。

採点の器(「人らしさ」の指標の器。**正解の表は作らない**)
    (a) 分布の一致: 同じ提示の候補の上で JSD(底 2=0〜1)と順位相関(スピアマン・同順位は平均の順位)。基準は古典と
        テープ((G) は GPU の後)。周辺(行為の語ごとの平均の分布)の JSD も。
    (b) 自己整合: 同じ状況を並びを変えて 2 回=同じ 1 位の率(位置の偏りの対照試験=``bias``)。
    (c) 迷い(DM5): 1 位と 2 位の差+エントロピー(自然対数)=``engine.decision.port.Hesitation.of``。
    (d) 驚きの語(0〜5)の読み口: ``surprise_of``(DM5 の 6 語)。今の 3 つの当て口は驚きを返さない=空。
    (e) 人のデータとの照合: **欄だけ**(``HUMAN_FIELDS``=値は空・検証側の値は入れない=パターン台帳 §10-1)。

速さと計算量の欄(§1-9): 1 件あたりの壁時計(実測・CPU)・トークン数(後で測る欄)・1 シム日あたりの GPU 時間の
    見積りの式 ``gpu_hours_per_sim_day``(呼数 × 1 件の秒 ÷ 3,600)。呼数の母数は 5,000 体 1 日の実測 64,528 呼
    (bd35 の記録の byte-check の表の ``w6_v3_default``=10e の道具)。1 件の秒は空欄(GPU の後)。

厳密モード(DM9「重みを手元・まとめ方固定・実測で一致」)の検査 ``strict_check``: 新しく作った当て口で同じ入力を
    2 回(同じ並び)と、並びを逆にした 1 回(まとめ方を変えた)で、状況ごとの分布がバイト単位で同じか。

expedient(器の宣言・未リサーチ)
    - 1 位の同点は候補の id の順(中身)で決める(番号の順にしない=位置の偏りを作らない)。
    - JSD の底は 2(0〜1 に収まる)。分布の比べは同じ提示の候補の和集合の上(無い所は 0)。
    - 古典の当て口: 曜日=平日(材料の曜日は入力に無い・1-10 §5 の 4)・地域=関東(engine の既定)・性と年齢は不明
      =男女の行の平均と年齢の総数の行・就業=B1 の種別(通勤者・従業者・指令=有業・ほかは有業と無業の平均)・
      場所=全件セルの路上(自宅・職場・学校でない)=「自宅/職場/学校/通勤」の活動は移動・交際は近くの知人が
      材料に無い(B5)=なし(待機)・食事の門は空腹の語(B5)が無いので通さない(語彙 v1 に食事は無い)。
逐次ループ宣言: 状況の数 × 並びの数 × 候補の数。古典の当て口は 19 種の配列演算。
"""

from __future__ import annotations

import hashlib
import math
import struct
import time
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping, Sequence

import numpy as np

import dm_eval  # noqa: F401
from dm_eval.situations import CONTINUE_WORD, VOCAB_VERSION, Situation, word_of_output
from shibuya.core.rng import stream
from shibuya.core.time_consts import MINUTES_PER_DAY, MINUTES_PER_HOUR, SECONDS_PER_HOUR
from shibuya.engine.decision.port import OTHER_ID, SURPRISE_WORDS, Candidate, Hesitation
from shibuya.llm.contract import compat_word

__all__ = [
    "ScorerUnavailable", "Scorer", "MockScorer", "ClassicalScorer", "TapeScorer", "ClefScorer", "KevScorer",
    "SokudanScorer", "GScorer", "FirstNumberControl", "scorer_registry", "normalize", "top1", "jsd", "spearman",
    "hesitation", "surprise_of", "agreement", "HUMAN_FIELDS", "CALLS_PER_DAY_BASIS", "gpu_hours_per_sim_day",
    "speed_fields", "strict_check", "dist_digest",
]

ROLE_CONTROL: Final[str] = "control"
ROLE_BASELINE: Final[str] = "baseline"
ROLE_CANDIDATE: Final[str] = "candidate"
ROLE_WORDS: Final[Mapping[str, str]] = MappingProxyType({
    ROLE_CONTROL: "対照", ROLE_BASELINE: "基準", ROLE_CANDIDATE: "候補"})

#: 人のデータとの照合の欄(値は入れない=検証側)。
HUMAN_FIELDS: Final[Mapping[str, Any]] = MappingProxyType({
    "human_match": None,
    "basis": "検証側(パターン台帳 §10-1=考慮集合の大きさ・習慣の割合ほか #50)=器は値を持たない・正解の表は作らない",
})

#: 1 シム日の呼数の母数(5,000 体・1 日・mock・既定 v3 の実測=bd35 の記録の byte-check の表の w6_v3_default)。
CALLS_PER_DAY_BASIS: Final[Mapping[str, Any]] = MappingProxyType({
    "calls_per_day": 64_528, "n_agents": 5_000, "days": 1,
    "source": "docs/bench/analysis/wallbounce-1012/bd35/README.md の byte-check の表(w6_v3_default・10e の道具)",
})


class ScorerUnavailable(RuntimeError):
    """口だけの当て口(重みの取得と GPU の後=S6)。"""


# ---------------------------------------------------------------------------------------------- 分布の道具
def normalize(dist: Mapping[str, float], presented: Sequence[Candidate]) -> dict[str, float]:
    """分布を検査して正規化する(鍵は提示の id と「その他」・0 以上・和が正)。並びは番号の順+「その他」。"""
    ids = [c.id for c in sorted(presented, key=lambda c: int(c.number or 0))]
    allowed = set(ids) | {OTHER_ID}
    bad = [k for k in dist if k not in allowed]
    if bad:
        raise ValueError(f"提示に無い候補の id: {bad}")
    vals = {k: float(v) for k, v in dist.items()}
    if any((not math.isfinite(v)) or v < 0 for v in vals.values()):
        raise ValueError("分布は有限で 0 以上")
    s = sum(vals.values())
    if not s > 0:
        raise ValueError("分布の和が 0")
    out = {i: vals.get(i, 0.0) / s for i in ids}
    out[OTHER_ID] = vals.get(OTHER_ID, 0.0) / s
    return out


def top1(dist: Mapping[str, float]) -> str:
    """1 位の候補の id(同点は id の順=中身で決める)。"""
    best = max(dist.values())
    return min(k for k, v in dist.items() if v == best)


def jsd(p: Mapping[str, float], q: Mapping[str, float]) -> float:
    """Jensen-Shannon の距離の 2 乗(発散)・底 2(0〜1)。鍵の和集合の上(無い所は 0)。"""
    keys = sorted(set(p) | set(q))
    a = np.asarray([float(p.get(k, 0.0)) for k in keys])
    b = np.asarray([float(q.get(k, 0.0)) for k in keys])
    a = a / a.sum()
    b = b / b.sum()
    m = 0.5 * (a + b)

    def kl(x: np.ndarray) -> float:
        nz = x > 0
        return float((x[nz] * np.log2(x[nz] / m[nz])).sum())

    return max(0.0, 0.5 * kl(a) + 0.5 * kl(b))


def _ranks(x: np.ndarray) -> np.ndarray:
    order = np.argsort(x, kind="mergesort")
    r = np.empty(x.size, dtype=np.float64)
    r[order] = np.arange(1, x.size + 1, dtype=np.float64)
    for v in np.unique(x):  # 同順位は平均の順位
        sel = x == v
        if int(sel.sum()) > 1:
            r[sel] = float(r[sel].mean())
    return r


def spearman(p: Mapping[str, float], q: Mapping[str, float]) -> float | None:
    """順位相関(スピアマン=順位のピアソン)。鍵の和集合の上。どちらかが一定なら None(定義できない)。"""
    keys = sorted(set(p) | set(q))
    a = _ranks(np.asarray([float(p.get(k, 0.0)) for k in keys]))
    b = _ranks(np.asarray([float(q.get(k, 0.0)) for k in keys]))
    sa, sb = float(a.std()), float(b.std())
    if sa == 0.0 or sb == 0.0:
        return None
    return float(((a - a.mean()) * (b - b.mean())).mean() / (sa * sb))


def hesitation(dist: Mapping[str, float]) -> Hesitation:
    """迷い(DM5)=``port.Hesitation.of``(1 位と 2 位の差・エントロピー=自然対数)。"""
    return Hesitation.of([float(v) for v in dist.values()])


def surprise_of(text: str | None) -> int | None:
    """驚きの語(DM5 の 6 語)→ 0〜5。前後の空白と句読点を除いて 6 語のどれかと同じときだけ(それ以外は None)。"""
    if text is None:
        return None
    t = str(text).strip().strip("。.、,「」『』\"' 　")
    for i, w in enumerate(SURPRISE_WORDS):
        if t == w:
            return i
    return None


def dist_digest(dists: Sequence[Mapping[str, float]]) -> str:
    """分布の列の sha256(鍵の順と float64 のバイト=厳密モードの一致の印)。"""
    h = hashlib.sha256()
    for d in dists:
        for k in sorted(d):
            h.update(k.encode("utf-8"))
            h.update(struct.pack("<d", float(d[k])))
        h.update(b"|")
    return h.hexdigest()


# ---------------------------------------------------------------------------------------------- 当て口
def _plain(x: Any) -> Any:
    """読み取り専用の写像と組を JSON に書ける形へ(``describe`` 用)。"""
    if isinstance(x, Mapping):
        return {str(k): _plain(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_plain(v) for v in x]
    return x


class Scorer:
    """候補の当て口(差し替えられる口)。実装は ``_score`` だけを書く。

    作った後は欄を付け替えられない(``__setattr__``/``__delattr__`` の守り=厳密モード DM9 の「まとめ方固定」の前提)。
    欄を持つ実装は ``__init__`` の**最後**で ``super().__init__()`` を呼んで閉じる。
    """

    name: str = ""
    role: str = ROLE_CANDIDATE
    implemented: bool = True
    #: 文(DM4 の短い版)を読むか。読まない当て口は長さの腕で結果が変わらない。
    reads_text: bool = False
    #: 当て口がここで入れ替えた提示の並びを見るか(テープ=見ていない=位置の偏りの列は構成上 0)。
    sees_presented_order: bool = True
    meta: Mapping[str, Any] = MappingProxyType({})

    def __init__(self) -> None:
        object.__setattr__(self, "_sealed", True)

    def __setattr__(self, key: str, value: Any) -> None:
        if getattr(self, "_sealed", False):
            raise AttributeError(f"{type(self).__name__} は作った後に欄 {key!r} を変えない(厳密モード DM9)")
        object.__setattr__(self, key, value)

    def __delattr__(self, key: str) -> None:
        raise AttributeError(f"{type(self).__name__} の欄 {key!r} は消さない(厳密モード DM9)")

    def score(self, situation: Situation, candidates: Sequence[Candidate], *, text: str | None = None
              ) -> dict[str, float]:
        """提示した候補の上の分布(``normalize`` 済み)。"""
        if not self.implemented:
            raise ScorerUnavailable(f"{self.name}: 重みの取得と GPU の後(S6)の口")
        return normalize(self._score(situation, tuple(candidates), text), candidates)

    def _score(self, situation: Situation, candidates: tuple[Candidate, ...], text: str | None
               ) -> Mapping[str, float]:
        raise NotImplementedError

    def describe(self) -> dict[str, Any]:
        return {"name": self.name, "role": self.role, "implemented": self.implemented,
                "reads_text": self.reads_text, "sees_presented_order": self.sees_presented_order,
                "meta": _plain(self.meta)}


class MockScorer(Scorer):
    """対照: 単体の上で一様な重み(Dirichlet(1))・種と状況の id の鍵・候補の中身(id)の順に引く。"""

    name = "mock"
    role = ROLE_CONTROL

    def __init__(self, seed: str | int = "dm61-mock") -> None:
        self.seed = seed
        self.meta = MappingProxyType({"draw": "Dirichlet(1)=指数分布の重みを正規化", "key": "種|状況の id",
                                      "order": "候補の id の順(提示の並びを使わない)"})
        super().__init__()

    def _score(self, situation: Situation, candidates: tuple[Candidate, ...], text: str | None
               ) -> Mapping[str, float]:
        ids = sorted(c.id for c in candidates)
        w = stream(self.seed, f"dm_eval.mock|{situation.sid}").exponential(size=len(ids))
        return {i: float(x) for i, x in zip(ids, w)}


class ClassicalScorer(Scorer):
    """基準: 今の古典モデルの判断の分布(活動の事前分布 → 対応表 v0 → 語彙 v1)。"""

    name = "classical"
    role = ROLE_BASELINE

    #: 有業とみなす B1 の種別の語(engine の ``_EMPLOYED_KINDS``=通勤者・従業者・指令・乗務員のうち材料にある語)。
    EMPLOYED_WORDS: Final[frozenset[str]] = frozenset({"通勤者", "従業者", "指令"})
    #: 場所で行き先が決まる活動の種類(全件セルの路上=行く=移動)。
    GO_KINDS: Final[frozenset[str]] = frozenset({"home", "work", "school", "commute"})

    def __init__(self, *, day_kind: str = "weekday", region: str = "kanto") -> None:
        from shibuya.engine.classical import ACTIVITY_MAP_V0, SSB_ACTIVITY_CODES, ActivityPrior, load_activity_prior

        anchors, md5 = load_activity_prior()
        self.prior = ActivityPrior(anchors, day_kind, region)
        self.prior.rates.setflags(write=False)  # 錨の率は読むだけ(厳密モード=重みを手元・変えない)
        self.prior.sample.setflags(write=False)
        self.slot_minutes = MINUTES_PER_DAY // int(anchors["n_slots"])
        words = []
        for code in SSB_ACTIVITY_CODES:
            kind, action, _t, _a, _u = ACTIVITY_MAP_V0[code]
            if kind in self.GO_KINDS:
                w = "移動"
            elif kind == "talk":
                w = compat_word("なし", "v3", VOCAB_VERSION)  # 近くの知人が材料に無い=なし(待つ)
            else:
                w = compat_word(action, "v3", VOCAB_VERSION)
            words.append(w)
        self.words = tuple(words)
        self.meta = MappingProxyType({"anchors_md5": md5, "day_kind": day_kind, "region": region,
                                      "multipliers": "1.0(IPF なし=engine の既定)", "meal_gate": "通さない(B5 が無い)",
                                      "sex": "男女の平均", "age": "総数の行", "words": self.words})
        super().__init__()

    def activity_probs(self, kind_word: str, slot: int) -> np.ndarray:
        """P(活動 | 15 分帯)(19 種)。性は平均・年齢は総数・就業は種別の語(不明は有業と無業の平均)。"""
        emp = (0,) if kind_word in self.EMPLOYED_WORDS else (0, 1)
        vec = np.zeros(self.prior.rates.shape[3], dtype=np.float64)
        for si in (0, 1):
            for ei in emp:
                vec += self.prior.rates[si, ei, 0, :, int(slot)]  # engine の ``ActivityPrior.row`` と同じく率を足してから割る
        s = float(vec.sum())
        return vec / s if s > 0 else np.full(vec.size, 1.0 / vec.size)

    def word_probs(self, situation: Situation) -> dict[str, float]:
        f = situation.facts
        minute = int(f.get("hour", 0)) * MINUTES_PER_HOUR + int(f.get("minute", 0))
        p = self.activity_probs(str(situation.strata.get("kind", "")), minute // self.slot_minutes)
        out: dict[str, float] = {}
        for w, x in zip(self.words, p.tolist()):
            out[w] = out.get(w, 0.0) + float(x)
        return out

    def _score(self, situation: Situation, candidates: tuple[Candidate, ...], text: str | None
               ) -> Mapping[str, float]:
        by_kind = {c.kind: c.id for c in candidates}
        out: dict[str, float] = {}
        for w, x in self.word_probs(situation).items():
            cid = by_kind.get(w, OTHER_ID)
            out[cid] = out.get(cid, 0.0) + x
        return out


class TapeScorer(Scorer):
    """基準: テープの応答(System 2 の原型=8B の記録)の行為の語に確率 1。語彙 v1 の外は「その他」。"""

    name = "tape"
    role = ROLE_BASELINE
    sees_presented_order = False
    meta = MappingProxyType({"source": "1-10 の評価セットの output(52 本のテープの応答)=本文は記録に写さない",
                             "presented_order": "テープの LLM は B0 の固定の並びを見た(ここの並べ替えは見ていない)"})

    def _score(self, situation: Situation, candidates: tuple[Candidate, ...], text: str | None
               ) -> Mapping[str, float]:
        w = word_of_output(situation.tape_output)
        for c in candidates:
            if w is not None and c.kind == w:
                return {c.id: 1.0}
        return {OTHER_ID: 1.0}


class FirstNumberControl(Scorer):
    """位置の偏りの正の対照: いつも番号 1 を選ぶ(並べ替え試験の検出力を確かめる)。"""

    name = "first_number"
    role = ROLE_CONTROL
    meta = MappingProxyType({"rule": "番号 1 に確率 1"})

    def _score(self, situation: Situation, candidates: tuple[Candidate, ...], text: str | None
               ) -> Mapping[str, float]:
        first = min(candidates, key=lambda c: int(c.number or 0))
        return {first.id: 1.0}


class _ModelPort(Scorer):
    """口だけの当て口(重みは取らない・GPU は使わない=S6 の後に ``_score`` を書く)。"""

    implemented = False
    reads_text = True


class ClefScorer(_ModelPort):
    """候補 Clef-flash(``variant="flash"``)と Clef(``"full"``)。Apache-2.0(R-83 §2-1・判断モデルの草案 DM1)。"""

    def __init__(self, variant: str = "flash") -> None:
        if variant not in ("flash", "full"):
            raise ValueError("variant は flash か full")
        self.variant = variant
        self.name = "clef_flash" if variant == "flash" else "clef"
        self.meta = MappingProxyType({"model": "Clef-flash" if variant == "flash" else "Clef",
                                      "license": "Apache-2.0", "source": "R-83 §2-1(判断モデルの草案 DM1 の材料)",
                                      "weights": "取らない(S6)"})
        super().__init__()


class KevScorer(_ModelPort):
    """候補 Kev-9B。Apache-2.0(R-83 §2-1)。"""

    name = "kev_9b"
    meta = MappingProxyType({"model": "Kev-9B", "license": "Apache-2.0", "source": "R-83 §2-1",
                             "weights": "取らない(S6)"})


class SokudanScorer(_ModelPort):
    """候補 即断 sokudan-ja-310m(R-94・日本語・3.1 億)。DM1 の追加の測り 3 つは欄だけ(``extra_measures``)。"""

    name = "sokudan_ja_310m"
    meta = MappingProxyType({
        "model": "GeneLab/sokudan-ja-310m", "license": "Apache-2.0", "source": "R-94 §0 #2(親検収 第323)",
        "train_mean_tokens": 134, "lang": "ja", "weights": "取らない(S6・手元の 5070 で回してよい=回答 2-1)",
        "extra_measures": MappingProxyType({
            "long_input_t300_t1000": None,
            "synthetic_training_data_effect": None,
            "non_japanese_first_language": None,
        }),
    })


class GScorer(_ModelPort):
    """基準 (G)=vLLM の 8B 級の 1 トークン目の確率(R-83 §5・DM1 の基準)。"""

    name = "g_first_token"
    role = ROLE_BASELINE
    meta = MappingProxyType({"model": "(G) 8B 級の 1 トークン目の確率", "source": "R-83 §5・判断モデルの草案 DM1",
                             "weights": "GPU の後(S6)"})


def scorer_registry(*, mock_seed: str | int = "dm61-mock") -> tuple[Scorer, ...]:
    """表の並び(宣言の順=対照 → 基準 → 候補・**指標で並べ替えない**)。"""
    return (MockScorer(mock_seed), ClassicalScorer(), TapeScorer(), GScorer(), ClefScorer("flash"),
            ClefScorer("full"), KevScorer(), SokudanScorer())


# ---------------------------------------------------------------------------------------------- 採点
def agreement(dists: Mapping[str, Mapping[str, float]], refs: Mapping[str, Mapping[str, float]],
              kinds: Mapping[str, Mapping[str, str]]) -> dict[str, Any]:
    """分布の一致(状況ごとの JSD と順位相関・1 位の一致率・周辺の JSD)。``kinds`` は状況 → 候補 id → 語。"""
    sids = sorted(set(dists) & set(refs))
    if not sids:
        return {"n": 0, "jsd_mean": None, "jsd_median": None, "spearman_mean": None, "spearman_undefined": 0,
                "top1_agree": None, "marginal_jsd": None}
    js = np.asarray([jsd(dists[s], refs[s]) for s in sids])
    rhos = [spearman(dists[s], refs[s]) for s in sids]
    rr = [r for r in rhos if r is not None]
    agree = np.asarray([top1(dists[s]) == top1(refs[s]) for s in sids], dtype=np.float64)
    ma: dict[str, float] = {}
    mb: dict[str, float] = {}
    for s in sids:
        km = kinds[s]
        for k, v in dists[s].items():
            w = km.get(k, OTHER_ID)
            ma[w] = ma.get(w, 0.0) + float(v)
        for k, v in refs[s].items():
            w = km.get(k, OTHER_ID)
            mb[w] = mb.get(w, 0.0) + float(v)
    return {"n": len(sids), "jsd_mean": float(js.mean()), "jsd_median": float(np.median(js)),
            "spearman_mean": float(np.mean(rr)) if rr else None, "spearman_undefined": len(rhos) - len(rr),
            "top1_agree": float(agree.mean()), "marginal_jsd": jsd(ma, mb)}


def hesitation_summary(dists: Mapping[str, Mapping[str, float]]) -> dict[str, Any]:
    """迷いの集計(差とエントロピーの平均と中央)。"""
    if not dists:
        return {"n": 0, "margin_mean": None, "margin_median": None, "entropy_mean": None, "entropy_median": None}
    hs = [hesitation(d) for d in dists.values()]
    m = np.asarray([h.margin for h in hs])
    e = np.asarray([h.entropy for h in hs])
    return {"n": len(hs), "margin_mean": float(m.mean()), "margin_median": float(np.median(m)),
            "entropy_mean": float(e.mean()), "entropy_median": float(np.median(e))}


def other_rate(dists: Mapping[str, Mapping[str, float]]) -> float | None:
    """「その他」の確率の平均(R-108 §3-3=低い割合は候補の十分さの証拠にならない)。"""
    if not dists:
        return None
    return float(np.mean([float(d.get(OTHER_ID, 0.0)) for d in dists.values()]))


# ---------------------------------------------------------------------------------------------- 速さと計算量
def gpu_hours_per_sim_day(sec_per_call: float | None, *, calls_per_day: float | None = None,
                          n_agents: int | None = None, scale_to_agents: int | None = None,
                          n_gpus: int = 1) -> float | None:
    """1 シム日あたりの GPU 時間 = 呼数/日 ×(人口の倍率)× 1 件の秒 ÷ 3,600 ÷ GPU の数。1 件の秒が空なら空。"""
    if sec_per_call is None:
        return None
    calls = float(CALLS_PER_DAY_BASIS["calls_per_day"] if calls_per_day is None else calls_per_day)
    base_n = int(CALLS_PER_DAY_BASIS["n_agents"] if n_agents is None else n_agents)
    scale = 1.0 if scale_to_agents is None else float(scale_to_agents) / float(base_n)
    return calls * scale * float(sec_per_call) / float(SECONDS_PER_HOUR) / float(n_gpus)


GPU_HOURS_FORMULA: Final[str] = ("1 シム日あたりの GPU 時間 = 呼数/日(5,000 体 1 日の実測 64,528)×(人口 ÷ 5,000)"
                                 "× 1 件の秒(GPU・空欄)÷ 3,600 ÷ GPU の数")


def speed_fields(scorer: Scorer, wall_s_per_item: float | None) -> dict[str, Any]:
    """速さの欄(壁時計は実測・トークン数と GPU の秒は空欄=後で測る)。"""
    return {"wall_s_per_item": wall_s_per_item, "wall_clock_device": "CPU" if scorer.implemented else None,
            "tokens_in": None, "tokens_out": None, "gpu_sec_per_call": None,
            "gpu_hours_per_sim_day": gpu_hours_per_sim_day(None), "formula": GPU_HOURS_FORMULA,
            "calls_basis": dict(CALLS_PER_DAY_BASIS)}


# ---------------------------------------------------------------------------------------------- 厳密モード(DM9)
def strict_check(make_scorer: Callable[[], Scorer], items: Sequence[tuple[Situation, Sequence[Candidate], str | None]]
                 ) -> dict[str, Any]:
    """同じ入力を 2 回(同じ並び)と、まとめ方を変えた 1 回(並びを逆)で、状況ごとの分布がバイト単位で同じか。

    ``make_scorer`` は毎回新しい当て口を作る(隠れた状態を持ち越さない)。口だけの当て口は検査できない(空欄)。
    """
    probe = make_scorer()
    if not probe.implemented:
        return {"name": probe.name, "status": "GPU の後(S6)", "identical_repeat": None, "identical_reordered": None}

    def run(seq: Sequence[tuple[int, tuple[Situation, Sequence[Candidate], str | None]]]
            ) -> dict[str, dict[str, float]]:
        sc = make_scorer()
        return {f"{s.sid}#{i}": sc.score(s, c, text=t) for i, (s, c, t) in seq}

    indexed = list(enumerate(items))
    t0 = time.perf_counter()
    a = run(indexed)
    b = run(indexed)
    c = run(list(reversed(indexed)))
    keys = sorted(a)
    da = dist_digest([a[k] for k in keys])
    db = dist_digest([b[k] for k in keys])
    dc = dist_digest([c[k] for k in keys])
    diff = max((abs(a[k][j] - c[k].get(j, 0.0)) for k in keys for j in a[k]), default=0.0)
    return {"name": probe.name, "status": "検査済み", "n_items": len(keys), "identical_repeat": da == db,
            "identical_reordered": da == dc, "max_abs_diff_reordered": float(diff), "digest": da,
            "weights_local": probe.meta.get("anchors_md5", "重みなし(規則)"), "batching": "1 件ずつ(まとめない)",
            "wall_s": time.perf_counter() - t0}
