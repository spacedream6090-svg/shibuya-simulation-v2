"""「属性から作る関数」の置き場(計画 第 4 期の注・答申 R-116 §3-3・W21 段 3)。

形: ``f(attrs, tables, key) -> 値``。

- ``attrs``: 人の属性の列(SoA・``{列の名: 配列}``)。関数は書き換えない。
- ``tables``: 版と md5 を固定した材料の表(:class:`AttrTables`・配列は書き込み禁止)。
- ``key``: カウンタの鍵(:class:`AttrKey`=seed・ドメイン・人ごとの鍵の語)。乱数は ``core.rng`` の Philox だけ。
- 世界の状態(場所の混み具合など)を読まない純粋な関数。母集団が変わったら呼び直すだけで済む。3-1 の W20(勤務の約束)・
  2-1 の EC2(最初の資産)・第 5 期の空間が同じ形で呼ぶ。
- **入力に無い属性は空欄**(数は −1・語は "")を返し、推測で埋めない(空欄の数は計器 ``w21_checks`` に出す)。

登録表 :data:`REGISTRY` は名前・版・入力の列・材料の表(台帳の id)を持つ。``call`` は入力の列がそろっているかを
確かめてから呼ぶ。

住民の関数は、町丁目 × 男女の周辺(小地域の表)へ「区の結合表を事前の重みにした割合」を寄せてから引く(:func:`rake_draw`=
周辺への raking・反復の数ぶんのループ)。外から来る人(``kind`` が通勤)は従業地の表(第 11-1・8・16-1 表)から引く。

写像の表(自前・宣言はつなぎの台帳): :data:`INDUSTRY_KEY_OF_MAJOR`(産業大分類 → W16 の 15 語)・
:data:`EMPLOYMENT_OF_STATUS`(従業上の地位 → 正規/非正規/役員/自営/家族従業者)・:data:`W16_KIND`(段 1 の層と役割 →
W16 の kind の番号)。

逐次ループ宣言(P4): ``rake_draw`` の反復の数ぶん(既定 200・収束で打ち切り)。体の数に比例するループは無い。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any, Callable, Final, Mapping

import numpy as np

from shibuya.core.rng import k19_counter_array, philox_array, unit_float

__all__ = [
    "AttrKey",
    "AttrFn",
    "AttrTables",
    "REGISTRY",
    "INDUSTRY_MAJORS",
    "OCCUPATION_MAJORS",
    "EMP_STATUS",
    "LABOUR",
    "WORKPLACE",
    "SCHOOL",
    "SCHOOL_PLACE",
    "RESIDENCE",
    "INDUSTRY_KEY_OF_MAJOR",
    "EMPLOYMENT_OF_STATUS",
    "W16_KIND",
    "W16_EMPLOYMENT_OF",
    "STUDENT_IN_KIND",
    "SCHOOL_AGE_WEIGHTS",
    "rake_draw",
    "call",
    "calendar_inputs",
    "age17",
]

#: 産業大分類(A〜T・T=分類不能)。
INDUSTRY_MAJORS: Final[tuple[str, ...]] = tuple("ABCDEFGHIJKLMNOPQRST")
#: 職業大分類(A〜L・L=分類不能)。
OCCUPATION_MAJORS: Final[tuple[str, ...]] = tuple("ABCDEFGHIJKL")
#: 労働力状態(15 歳以上)。
LABOUR: Final[tuple[str, ...]] = ("employed", "unemployed", "not_in_labour_force")
#: 従業上の地位(国勢調査の 8 区分・第3-1表の順)。
EMP_STATUS: Final[tuple[str, ...]] = ("regular", "dispatched", "part_time", "executive", "employer",
                                      "self_employed", "family_worker", "home_worker")
#: 従業地(常住地から見た)。
WORKPLACE: Final[tuple[str, ...]] = ("home", "in_ward", "other_tokyo", "other_prefecture")
#: 在学・未就学の種類(第14表)と「在学していない」。
SCHOOL: Final[tuple[str, ...]] = ("elementary", "junior_high", "high", "junior_college", "university", "graduate",
                                  "kindergarten", "nursery", "kodomoen", "preschool_other", "none")
#: 通学地(15 歳以上の在学者・第16-3表)。
SCHOOL_PLACE: Final[tuple[str, ...]] = ("in_ward", "other_tokyo", "other_prefecture")
#: 居住期間(第18表)。
RESIDENCE: Final[tuple[str, ...]] = ("since_birth", "lt1", "y1_5", "y5_10", "y10_20", "ge20")

#: 産業大分類 → W16 の ``industry_key``(15 語)。``N`` は経済センサスの中分類の比で LS(78・79)と AM(80)に分ける。
#: A・B・C・F・S(公務)・T(分類不能)は 15 語に無い=空欄(R-116 §5・PENDING 仮-23=公務 S は空欄の宣言)。
INDUSTRY_KEY_OF_MAJOR: Final[Mapping[str, str]] = MappingProxyType({
    "D": "CN", "E": "MF", "G": "IT", "H": "TR", "I": "WR", "J": "FI", "K": "RE", "L": "PS", "M": "FB",
    "N": "LS|AM", "O": "ED", "P": "MW", "Q": "CS", "R": "SV",
    "A": "", "B": "", "C": "", "F": "", "S": "", "T": "",
})
#: 従業上の地位 → W20 に渡す ``employment_status``(国勢調査の区分と経済センサスの区分は対応しない=自前の写像)。
EMPLOYMENT_OF_STATUS: Final[Mapping[str, str]] = MappingProxyType({
    "regular": "regular", "dispatched": "non_regular", "part_time": "non_regular", "executive": "executive",
    "employer": "self_employed", "self_employed": "self_employed", "home_worker": "self_employed",
    "family_worker": "family_worker",
})
#: 〔親の判断=W20 との接続〕``employment_status`` → W16 の ``employment`` の 6 値(空欄=非就業・R-116 §5 の表)。
W16_EMPLOYMENT_OF: Final[Mapping[str, str]] = MappingProxyType({
    "regular": "正規", "non_regular": "非正規", "executive": "役員", "self_employed": "自営業主",
    "family_worker": "家族従業者", "": "非就業",
})
#: 外から来る通学者(通学地が渋谷区で他の市区町村に住む人)の ``kind`` の語〔検収 L6〕。
STUDENT_IN_KIND: Final[str] = "student_in"

#: (段 1 の層, 役割)→ W16 の ``kind``(``agents.state.AgentKind`` と同じ値)。新しい層(乗り換えだけ・通過)は W16 に
#: 番号が無い=−1(段 10 で親が決める)。
W16_KIND: Final[Mapping[tuple[str, str], int]] = MappingProxyType({
    ("in_area", "resident"): 3,
    ("in_area", "resident_worker_in_area"): 2,
    ("in_area", "commuter"): 0,
    ("in_area", "student"): 5,
    ("in_area", "visitor"): 1,
    ("in_area", "regular_visitor"): 6,
    ("in_area", "foreign_visitor"): 7,
    ("in_area", "crew"): 8,
    ("in_area", "dispatcher"): 4,
    ("in_area", "transfer_only"): -1,
    ("in_area", "through"): -1,
})

#: 在学の年齢の重み(各歳 0〜105 → 種類)。自前の表(未リサーチ・学年の区切りを年齢に当てた窓)。
_A = np.arange(106)


def _w(*pairs: tuple[int, int, float]) -> np.ndarray:
    out = np.zeros(106)
    for lo, hi, v in pairs:
        out[(_A >= lo) & (_A <= hi)] = v
    return out


SCHOOL_AGE_WEIGHTS: Final[np.ndarray] = np.stack([
    _w((6, 11, 1.0), (12, 12, 0.5)),                                   # 小学校
    _w((12, 12, 0.5), (13, 14, 1.0), (15, 15, 0.5)),                   # 中学校
    _w((15, 15, 0.5), (16, 17, 1.0), (18, 18, 0.3), (19, 25, 0.02)),   # 高校
    _w((15, 17, 0.2), (18, 20, 1.0), (21, 25, 0.1)),                   # 短大・高専
    _w((18, 22, 1.0), (23, 29, 0.15), (30, 105, 0.01)),               # 大学
    _w((22, 29, 1.0), (30, 39, 0.2), (40, 105, 0.02)),                # 大学院
    _w((3, 5, 1.0), (6, 6, 0.3)),                                      # 幼稚園
    _w((0, 5, 1.0), (6, 6, 0.3)),                                      # 保育園・保育所
    _w((0, 5, 1.0), (6, 6, 0.3)),                                      # 認定こども園
    _w((0, 5, 1.0), (6, 6, 0.3)),                                      # 未就学のその他
    _w((6, 14, 0.001), (15, 17, 0.05), (18, 105, 1.0)),               # 在学していない
], axis=1)  # (106, 11)
SCHOOL_AGE_WEIGHTS.flags.writeable = False
#: 居住期間の年齢の窓(その期間を持てる最低の年齢)。
_RESIDENCE_MIN_AGE: Final[np.ndarray] = np.array([0, 0, 1, 5, 10, 20])
_RESIDENCE_MIN_AGE.flags.writeable = False
#: 完全失業者の年齢の重み(15〜69 歳 1・70 歳以上 0.3=自前)。
UNEMPLOYED_AGE_WEIGHT: Final[tuple[float, float]] = (1.0, 0.3)


def age17(age: np.ndarray) -> np.ndarray:
    """各歳 → 就業の表の年齢 17 階級(15-19 … 90-94・95 歳以上)。15 歳未満は −1。"""
    a = np.asarray(age, dtype=np.int64)
    return np.where(a < 15, -1, np.minimum((a - 15) // 5, 16))


# ------------------------------------------------------------------------------------------ 鍵と表
@dataclass(frozen=True)
class AttrKey:
    """乱数の鍵(seed・ドメイン・人ごとの鍵の語 (n, ≤3))。"""

    seed: int | str
    domain: str
    counters: np.ndarray

    def uniform(self, words: int = 1, sub: str = "") -> np.ndarray:
        dom = self.domain + (f".{sub}" if sub else "")
        c = np.asarray(self.counters, dtype=np.int64)
        cols = [c[:, j] for j in range(c.shape[1])]
        return unit_float(philox_array(self.seed, dom, k19_counter_array(*cols), words=words))


@dataclass(frozen=True)
class AttrTables:
    """材料の表から作った確率の表(書き込み禁止)と、町丁目 × 男女の周辺の割合。

    ``chome_*`` の配列は (町丁目 × 2 + 男女, 区分) の割合。``md5`` は材料の表の id → md5。
    """

    emp_rate: np.ndarray            # (2, 17, 4) 就業者 ÷ 人口(男女 × 年齢 × 配偶関係)
    status_prior: np.ndarray        # (2, 4, 17, 8) 従業上の地位(男女 × 配偶 × 年齢)
    industry_prior: np.ndarray      # (2, 17, 8, 20) 産業(男女 × 年齢 × 地位)
    occupation_prior: np.ndarray    # (2, 17, 20, 12) 職業(男女 × 年齢 × 産業)
    workplace_prior: np.ndarray     # (5, 20, 4) 従業地(地位の組 × 産業)=常住地による
    commuter_industry: np.ndarray   # (2, 17, 20) 従業地が渋谷区の就業者の産業(男女 × 年齢)
    commuter_occupation: np.ndarray  # (2, 20, 12) 同 職業(男女 × 産業)
    commuter_status: np.ndarray     # (20, 5) 同 地位の組(産業)
    student_in: np.ndarray          # (2, 階級) 通学地が渋谷区で他の市区町村に住む通学者(男女 × 年齢の階級・第1-3表)
    student_in_ages: np.ndarray     # (階級, 2) 階級の各歳の下と上(15 歳未満は 6〜14 歳)
    n_split: tuple[float, float]    # 産業 N の LS と AM の比(経済センサス)
    chome_labour: np.ndarray        # (G, 3)
    chome_status: np.ndarray        # (G, 3) 雇用者(役員を含む)・自営業主(家庭内職者を含む)・家族従業者
    chome_industry: np.ndarray      # (G, 20)
    chome_occupation: np.ndarray    # (G, 12)
    chome_workplace: np.ndarray     # (G, 4)
    chome_school: np.ndarray        # (G, 11)
    chome_school_place: np.ndarray  # (G, 3)
    chome_residence: np.ndarray     # (G, 6)
    md5: Mapping[str, str] = field(default_factory=dict)

    def freeze(self) -> "AttrTables":
        """配列を書き込み禁止に・md5 の表を読み取り専用の写像にした自分を返す(検収 L3)。"""
        for v in self.__dict__.values():
            if isinstance(v, np.ndarray):
                v.flags.writeable = False
        if not isinstance(self.md5, MappingProxyType):
            object.__setattr__(self, "md5", MappingProxyType(dict(self.md5)))
        return self


@dataclass(frozen=True)
class AttrFn:
    """登録表の 1 行。"""

    name: str
    version: str
    inputs: tuple[str, ...]
    tables: tuple[str, ...]
    fn: Callable[[Mapping[str, np.ndarray], AttrTables, AttrKey], np.ndarray]


# ------------------------------------------------------------------------------------------ 道具
def rake_draw(prior: np.ndarray, group: np.ndarray, share: np.ndarray, u: np.ndarray, *,
              margin_of: np.ndarray | None = None, max_iter: int = 200, tol: float = 1e-9
              ) -> tuple[np.ndarray, dict[str, float]]:
    """人ごとの事前の重み(n, K)を、組ごとの周辺の割合(G, M)へ寄せてから引く(−1=重みが無い人)。

    ``margin_of``(K,)は区分 → 周辺の列(省略は恒等)。組の大きさ × 割合が周辺の目標の数。反復: 各組・各周辺の列の
    重みの和を目標に合わせる倍率を掛け、人ごとに和 1 へ直す(raking)。返り値の 2 つ目は最後の残差(人数の割合)。
    """
    P = np.asarray(prior, dtype=np.float64)
    n, K = P.shape
    mo = np.arange(K) if margin_of is None else np.asarray(margin_of, dtype=np.int64)
    M = int(mo.max()) + 1 if K else 0
    rs = P.sum(axis=1)
    ok = rs > 0
    W = np.divide(P, rs[:, None], out=np.zeros_like(P), where=ok[:, None])
    g = np.asarray(group, dtype=np.int64)
    G = share.shape[0]
    size = np.bincount(g[ok], minlength=G).astype(np.float64)
    sh = np.asarray(share, dtype=np.float64)
    sh_sum = sh.sum(axis=1, keepdims=True)
    tgt = np.divide(sh, sh_sum, out=np.zeros_like(sh), where=sh_sum > 0) * size[:, None]
    live = sh_sum[:, 0] > 0
    flat = (g[:, None] * M + mo[None, :]).ravel()

    def colsum(w: np.ndarray) -> np.ndarray:
        return np.bincount(flat, weights=w.ravel(), minlength=G * M).reshape(G, M)

    resid = 0.0
    it = 0
    for it in range(1, max_iter + 1):  # 逐次: 反復の数ぶん
        col = colsum(W)
        f = np.divide(tgt, col, out=np.ones_like(tgt), where=col > 0)
        f = np.where(live[:, None], f, 1.0)
        W = W * f[g][:, mo]
        rs2 = W.sum(axis=1)
        W = np.divide(W, rs2[:, None], out=np.zeros_like(W), where=rs2[:, None] > 0)
        col = colsum(W)
        resid = float(np.abs(col[live] - tgt[live]).sum() / max(size[live].sum(), 1.0))
        if resid <= tol:
            break
    dead = ok & (W.sum(axis=1) <= 0)  # 周辺の目標が 0 の区分にしか重みの無い人=寄せずに事前の重みで引く(数を返す)
    if dead.any():
        W[dead] = P[dead] / rs[dead, None]
    cdf = np.cumsum(W, axis=1)
    k = (cdf < u[:, None] * cdf[:, -1:]).sum(axis=1)
    k = np.where(ok & (W.sum(axis=1) > 0), np.minimum(k, K - 1), -1)
    return k, {"residual": resid, "iterations": float(it), "unraked_rows": float(dead.sum())}


def _nonzero(prior: np.ndarray, *fallbacks: np.ndarray) -> np.ndarray:
    """重みの和が 0 の行を、順に粗い条件の重み(周辺)で埋める(全部 0 なら 0 のまま=空欄)。"""
    out = np.array(prior, dtype=np.float64, copy=True)
    for fb in fallbacks:  # 逐次: 埋める段の数ぶん(≤ 2)
        bad = out.sum(axis=1) <= 0
        if not bad.any():
            break
        out[bad] = np.broadcast_to(fb, out.shape)[bad]
    return out


def _draw_rows(prob: np.ndarray, u: np.ndarray) -> np.ndarray:
    tot = prob.sum(axis=1)
    k = (np.cumsum(prob, axis=1) < (u * tot)[:, None]).sum(axis=1)
    return np.where(tot > 0, np.minimum(k, prob.shape[1] - 1), -1)


def _resident(attrs: Mapping[str, np.ndarray]) -> np.ndarray:
    return np.asarray(attrs["kind"]) == "resident"


def _commuter(attrs: Mapping[str, np.ndarray]) -> np.ndarray:
    return np.asarray(attrs["kind"]) == "commuter"


def _group(attrs: Mapping[str, np.ndarray]) -> np.ndarray:
    return np.asarray(attrs["chome"], dtype=np.int64) * 2 + np.asarray(attrs["sex"], dtype=np.int64)


# ------------------------------------------------------------------------------------------ 関数
def f_labour_status(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """労働力状態(住民の 15 歳以上)。事前の重み=区の就業率(男女 × 年齢 × 配偶関係)・周辺=町丁目の第9・10表。

    外から来る人(通勤)は就業者。15 歳未満と入力の無い人は −1。
    """
    age = np.asarray(attrs["age"], dtype=np.int64)
    n = age.size
    out = np.full(n, -1, dtype=np.int64)
    res = _resident(attrs) & (age >= 15)
    out[_commuter(attrs)] = 0
    if not res.any():
        return out
    sx = np.asarray(attrs["sex"])[res]
    mar = np.clip(np.asarray(attrs["marital"], dtype=np.int64)[res], 0, 3)
    a = age17(age[res])
    pe = np.clip(tables.emp_rate[sx, a, mar], 0.01, 0.99)
    wu = np.where(age[res] < 70, UNEMPLOYED_AGE_WEIGHT[0], UNEMPLOYED_AGE_WEIGHT[1])
    prior = np.stack([pe, (1 - pe) * 0.1 * wu, (1 - pe) * (1 - 0.1 * wu)], axis=1)
    k, _ = rake_draw(prior, _group(attrs)[res], tables.chome_labour, key.uniform()[res, 0])
    out[res] = k
    return out


def f_emp_status(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """従業上の地位(就業者)。住民: 第3-1表を事前の重みに町丁目の第10表(雇用者・自営業主・家族従業者)へ寄せる。
    通勤: 従業地の第8表(産業ごとの地位の組)・雇用者でない人は「雇人のない業主」に寄せる(自前)。"""
    lab = np.asarray(attrs["labour_status"], dtype=np.int64)
    n = lab.size
    out = np.full(n, -1, dtype=np.int64)
    res = _resident(attrs) & (lab == 0)
    if res.any():
        sx = np.asarray(attrs["sex"])[res]
        mar = np.clip(np.asarray(attrs["marital"], dtype=np.int64)[res], 0, 3)
        a = age17(np.asarray(attrs["age"])[res])
        prior = _nonzero(tables.status_prior[sx, mar, a], tables.status_prior[sx, :, a].sum(axis=1),
                         tables.status_prior.sum(axis=(0, 1, 2)))
        margin = np.array([0, 0, 0, 0, 1, 1, 2, 1])
        k, _ = rake_draw(prior, _group(attrs)[res], tables.chome_status, key.uniform()[res, 0], margin_of=margin)
        out[res] = k
    com = _commuter(attrs) & (lab == 0)
    if com.any() and "industry_major" in attrs:
        ind = np.asarray(attrs["industry_major"], dtype=np.int64)[com]
        p5 = np.where((ind >= 0)[:, None], _nonzero(tables.commuter_status[np.clip(ind, 0, None)],
                                                     tables.commuter_status.sum(axis=0)), 0.0)
        g5 = _draw_rows(p5, key.uniform(sub="commuter")[com, 0])
        to8 = np.array([0, 1, 2, 3, 5])
        out[com] = np.where(g5 >= 0, to8[np.clip(g5, 0, None)], -1)
    return out


def f_employment_status(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """W20 に渡す粗い区分(写像 :data:`EMPLOYMENT_OF_STATUS`)。空欄は ""。"""
    st = np.asarray(attrs["emp_status"], dtype=np.int64)
    lut = np.array([EMPLOYMENT_OF_STATUS[s] for s in EMP_STATUS] + [""], dtype=object)
    return lut[np.where(st >= 0, st, len(EMP_STATUS))]


def f_industry_major(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """産業大分類。住民: 第5-1表(男女 × 年齢 × 地位)を事前の重みに町丁目の第11表へ。通勤: 従業地の第11-1表。"""
    lab = np.asarray(attrs["labour_status"], dtype=np.int64)
    n = lab.size
    out = np.full(n, -1, dtype=np.int64)
    age = np.asarray(attrs["age"])
    res = _resident(attrs) & (lab == 0)
    if res.any():
        st = np.asarray(attrs["emp_status"], dtype=np.int64)[res]
        sx = np.asarray(attrs["sex"])[res]
        prior = tables.industry_prior[sx, age17(age[res]), np.clip(st, 0, None)]
        prior = np.where((st >= 0)[:, None], prior, tables.industry_prior[sx, age17(age[res])].sum(axis=1))
        prior = _nonzero(prior, tables.industry_prior[sx, age17(age[res])].sum(axis=1),
                         tables.industry_prior.sum(axis=(0, 1, 2)))
        k, _ = rake_draw(prior, _group(attrs)[res], tables.chome_industry, key.uniform()[res, 0])
        out[res] = k
    com = _commuter(attrs) & (lab == 0) & (age >= 15)
    if com.any():
        sx = np.asarray(attrs["sex"])[com]
        p = _nonzero(tables.commuter_industry[sx, age17(age[com])], tables.commuter_industry[sx].sum(axis=0))
        out[com] = _draw_rows(p, key.uniform(sub="commuter")[com, 0])
    return out


def f_industry_key(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """W16 の 15 語(写像 :data:`INDUSTRY_KEY_OF_MAJOR`・N は LS/AM を経済センサスの比で)。空欄は ""。"""
    ind = np.asarray(attrs["industry_major"], dtype=np.int64)
    lut = np.array([INDUSTRY_KEY_OF_MAJOR[m] for m in INDUSTRY_MAJORS] + [""], dtype=object)
    out = lut[np.where(ind >= 0, ind, len(INDUSTRY_MAJORS))].copy()
    nn = out == "LS|AM"
    if nn.any():
        ls = tables.n_split[0] / max(sum(tables.n_split), 1e-12)
        out[nn] = np.where(key.uniform()[nn, 0] < ls, "LS", "AM")
    return out


def f_occupation_major(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """職業大分類。住民: 第10-1表(男女 × 年齢 × 産業)を事前の重みに町丁目の第12表へ。通勤: 第16-1表(男女 × 産業)。"""
    ind = np.asarray(attrs["industry_major"], dtype=np.int64)
    n = ind.size
    out = np.full(n, -1, dtype=np.int64)
    age = np.asarray(attrs["age"])
    res = _resident(attrs) & (ind >= 0)
    if res.any():
        sx = np.asarray(attrs["sex"])[res]
        prior = _nonzero(tables.occupation_prior[sx, age17(age[res]), ind[res]],
                         tables.occupation_prior[sx, :, ind[res]].sum(axis=1),
                         tables.occupation_prior.sum(axis=(0, 1, 2)))
        k, _ = rake_draw(prior, _group(attrs)[res], tables.chome_occupation, key.uniform()[res, 0])
        out[res] = k
    com = _commuter(attrs) & (ind >= 0)
    if com.any():
        sx = np.asarray(attrs["sex"])[com]
        p = _nonzero(tables.commuter_occupation[sx, ind[com]], tables.commuter_occupation.sum(axis=(0, 1)))
        out[com] = _draw_rows(p, key.uniform(sub="commuter")[com, 0])
    return out


def f_workplace_kind(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """従業地(住民の就業者・常住地から見た)。事前の重み=第8表(地位の組 × 産業)・周辺=町丁目の第16-2表。
    外から来る人は空欄(常住地から見た表が無い)。"""
    st = np.asarray(attrs["emp_status"], dtype=np.int64)
    ind = np.asarray(attrs["industry_major"], dtype=np.int64)
    n = st.size
    out = np.full(n, -1, dtype=np.int64)
    res = _resident(attrs) & (st >= 0)
    if res.any():
        grp = np.array([0, 1, 2, 3, 4, 4, 4, 4])[st[res]]
        prior = tables.workplace_prior[grp, np.clip(ind[res], 0, None)]
        prior = np.where((ind[res] >= 0)[:, None], prior, tables.workplace_prior[grp].sum(axis=1))
        prior = _nonzero(prior, tables.workplace_prior[grp].sum(axis=1), tables.workplace_prior.sum(axis=(0, 1)))
        k, _ = rake_draw(prior, _group(attrs)[res], tables.chome_workplace, key.uniform()[res, 0])
        out[res] = k
    return out


def f_school_kind(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """在学・未就学の種類。住民: 事前の重み=年齢の窓(:data:`SCHOOL_AGE_WEIGHTS`)・周辺=町丁目の第14表。
    外から来る通学者: 年齢の窓の在学の 6 区分(小〜大学院)だけから引く(在学の種類 × 通学地の表が無い=宣言)。"""
    age = np.clip(np.asarray(attrs["age"], dtype=np.int64), 0, 105)
    out = np.full(age.size, -1, dtype=np.int64)
    res = _resident(attrs)
    if res.any():
        k, _ = rake_draw(SCHOOL_AGE_WEIGHTS[age[res]], _group(attrs)[res], tables.chome_school,
                         key.uniform()[res, 0])
        out[res] = k
    sin = (np.asarray(attrs["kind"]) == STUDENT_IN_KIND) & (np.asarray(attrs["age"], dtype=np.int64) >= 0)
    if sin.any():
        out[sin] = _draw_rows(SCHOOL_AGE_WEIGHTS[age[sin], :6], key.uniform(sub="student_in")[sin, 0])
    return out


def _student_in_draw(attrs, tables: AttrTables, key: AttrKey) -> tuple[np.ndarray, np.ndarray]:
    """外から来る通学者の(男女, 各歳)。第1-3表の男女 × 年齢の階級を 1 つ目の乱数で・階級の中の各歳を 2 つ目の乱数で
    一様に引く(同じ鍵なら ``student_in_sex`` と ``student_in_age`` は同じ人を指す)。ほかの人は −1。"""
    sel = np.asarray(attrs["kind"]) == STUDENT_IN_KIND
    n = sel.size
    sex = np.full(n, -1, dtype=np.int64)
    age = np.full(n, -1, dtype=np.int64)
    if sel.any() and tables.student_in.sum() > 0:
        u = key.uniform(words=2)[sel]
        w = tables.student_in.ravel()  # (男 階級…, 女 階級…)
        k = np.minimum(np.searchsorted(np.cumsum(w) / w.sum(), u[:, 0], side="right"), w.size - 1)
        ncls = tables.student_in.shape[1]
        cls = k % ncls
        lo, hi = tables.student_in_ages[cls, 0], tables.student_in_ages[cls, 1]
        sex[sel] = k // ncls
        age[sel] = lo + np.minimum((u[:, 1] * (hi - lo + 1)).astype(np.int64), hi - lo)
    return sex, age


def f_student_in_sex(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """外から来る通学者の男女(第1-3表の「うち他市区町村に常住」・通学地=渋谷区)。"""
    return _student_in_draw(attrs, tables, key)[0]


def f_student_in_age(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """外から来る通学者の年齢(同じ表・5 歳階級の中は一様=宣言)。"""
    return _student_in_draw(attrs, tables, key)[1]


def f_w16_employment(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """``employment_status`` → W16 の ``employment`` の 6 値(:data:`W16_EMPLOYMENT_OF`・None と空欄は「非就業」)。
    3-1 の W20 がどちらの語でも読めるようにする写像(親の判断)。"""
    es = np.asarray(attrs["employment_status"], dtype=object)
    norm = np.where(np.equal(es, None), "", es).astype(str)
    uniq, inv = np.unique(norm, return_inverse=True)
    lut = np.array([W16_EMPLOYMENT_OF.get(x, "非就業") for x in uniq.tolist()], dtype=object)  # 逐次: 語の種類の数
    return lut[inv] if norm.size else np.zeros(0, dtype=object)


def f_school_place(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """通学地(住民の 15 歳以上の在学者=高校・短大高専・大学・大学院)。周辺=町丁目の第16-3表。15 歳未満は空欄。"""
    sk = np.asarray(attrs["school_kind"], dtype=np.int64)
    age = np.asarray(attrs["age"], dtype=np.int64)
    out = np.full(sk.size, -1, dtype=np.int64)
    res = _resident(attrs) & np.isin(sk, [2, 3, 4, 5]) & (age >= 15)
    if res.any():
        k, _ = rake_draw(np.ones((int(res.sum()), len(SCHOOL_PLACE))), _group(attrs)[res],
                         tables.chome_school_place, key.uniform()[res, 0])
        out[res] = k
    return out


def f_residence_period(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """居住期間(住民)。事前の重み=年齢で上限を切った一様・周辺=町丁目の第18表。"""
    age = np.asarray(attrs["age"], dtype=np.int64)
    out = np.full(age.size, -1, dtype=np.int64)
    res = _resident(attrs)
    if res.any():
        prior = (age[res][:, None] >= _RESIDENCE_MIN_AGE[None, :]).astype(np.float64)
        k, _ = rake_draw(prior, _group(attrs)[res], tables.chome_residence, key.uniform()[res, 0])
        out[res] = k
    return out


def f_w16_kind(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """(層, 役割)→ W16 の kind の番号(:data:`W16_KIND`・表に無い組は −1)。"""
    pk = np.asarray(attrs["persona_kind"]).astype(str)
    ro = np.asarray(attrs["role"]).astype(str)
    uniq, inv = np.unique(np.char.add(np.char.add(pk, "|"), ro), return_inverse=True)
    codes = np.array([W16_KIND.get(tuple(x.split("|", 1)), -1) for x in uniq.tolist()], dtype=np.int64)  # 逐次: 組の種類の数
    return codes[inv] if pk.size else np.zeros(0, dtype=np.int64)


def f_duty_role(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """職務の役割(店長・正社員・パートなど)。段 4(PS5)まで空欄(v1 の在庫は使わない=R-116 §5)。"""
    return np.full(np.asarray(attrs["age"]).size, "", dtype=object)


REGISTRY: Final[Mapping[str, AttrFn]] = MappingProxyType({f.name: f for f in (
    AttrFn("labour_status", "1.0.0", ("kind", "sex", "age", "marital", "chome"), ("c20_c03", "c20w_b13_m",
           "c20w_b13_f", "sa_t09", "sa_t10"), f_labour_status),
    AttrFn("emp_status", "1.0.0", ("kind", "sex", "age", "marital", "chome", "labour_status"),
           ("c20_c03", "sa_t10", "c20_e08"), f_emp_status),
    AttrFn("employment_status", "1.0.0", ("emp_status",), (), f_employment_status),
    AttrFn("industry_major", "1.0.0", ("kind", "sex", "age", "chome", "labour_status", "emp_status"),
           ("c20_c05", "sa_t11", "c20_e11"), f_industry_major),
    AttrFn("industry_key", "1.0.0", ("industry_major",), ("ecen21_area",), f_industry_key),
    AttrFn("occupation_major", "1.0.0", ("kind", "sex", "age", "chome", "industry_major"),
           ("c20_c10", "sa_t12", "c20_e16"), f_occupation_major),
    AttrFn("workplace_kind", "1.0.0", ("kind", "sex", "chome", "emp_status", "industry_major"),
           ("c20_e08", "sa_t16_2"), f_workplace_kind),
    AttrFn("school_kind", "1.1.0", ("kind", "sex", "age", "chome"), ("sa_t14",), f_school_kind),
    AttrFn("school_place", "1.0.0", ("kind", "sex", "age", "chome", "school_kind"), ("sa_t16_3",),
           f_school_place),
    AttrFn("residence_period", "1.0.0", ("kind", "sex", "age", "chome"), ("sa_t18",), f_residence_period),
    AttrFn("w16_kind", "1.0.0", ("persona_kind", "role"), (), f_w16_kind),
    AttrFn("duty_role", "1.0.0", ("age",), (), f_duty_role),
    AttrFn("student_in_sex", "1.0.0", ("kind",), ("c20_e01_03",), f_student_in_sex),
    AttrFn("student_in_age", "1.0.0", ("kind",), ("c20_e01_03",), f_student_in_age),
    AttrFn("w16_employment", "1.0.0", ("employment_status",), (), f_w16_employment),
)})


def call(name: str, attrs: Mapping[str, np.ndarray], tables: AttrTables, key: AttrKey) -> np.ndarray:
    """登録表の関数を呼ぶ(入力の列がそろっていなければ止める)。"""
    f = REGISTRY[name]
    missing = [c for c in f.inputs if c not in attrs]
    if missing:
        raise KeyError(f"{name}: 入力の列が無い {missing}")
    return f.fn(attrs, tables, key)


def calendar_inputs(persons: Mapping[str, Any]) -> dict[str, np.ndarray]:
    """3-1 の W20(``calendar_from_attributes``)に渡す 5 属性(``kind``・``age``・``industry_key``・
    ``employment_status``・``duty_role``=段 4 まで空欄)。``kind`` は W16 の番号。"""
    return {
        "kind": np.asarray(persons["kind"], dtype=np.int64),
        "age": np.asarray(persons["age"], dtype=np.int64),
        "industry_key": np.asarray(persons["industry_key"], dtype=object),
        "employment_status": np.asarray(persons["employment_status"], dtype=object),
        "duty_role": np.asarray(persons["duty_role"], dtype=object),
    }
