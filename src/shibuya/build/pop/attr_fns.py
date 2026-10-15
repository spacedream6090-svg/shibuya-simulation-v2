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

〔段 4〜7=W21 の続き・版 1.1.0〕同じ形の関数を登録表に足した(``AttrFn.stage`` が 4〜6・``tables`` は段 3 の
:class:`AttrTables` か段 4〜7 の :class:`AttrTablesB`): 外から来て働く人の男女と年齢(第11-1表)・常住地(第4表)・駅の口
(W12)・組織の中の役割の語・週の時間の目安・②群の担当(規則の表)/賃金(賃金構造 令和 7 年=第9・6・18 表と短時間 第2表)・
世帯の貯蓄・通貨性預貯金・負債(全国家計構造調査 2024=階級の度数をそのまま)・貸金業の残高(JICC)・空欄の 3 つ(財布の現金・
カード・口座)/住んでいる年数・なじみの場所の容量(約 25 か所)・行ったことのある場所の数(t^0.6)。段 1〜3 の manifest に
書く版の表は段 3 の関数だけ(:func:`registry_versions`)。

逐次ループ宣言(P4): ``rake_draw`` の反復の数ぶん(既定 200・収束で打ち切り)・``duty_role_org`` の規則の数ぶん(9)・
語の種類の数ぶんの写像の引き。体の数に比例するループは無い。
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
    "registry_versions",
    "AttrTablesB",
    "WAGE_OCCUPATIONS",
    "WAGE_FORM_OF_STATUS",
    "WAGE_AGE_EDGES",
    "HH_TYPES",
    "ASSET_AGE_EDGES",
    "STORE_INDUSTRIES",
    "R80_SUBORDINATES",
    "R80_DIVISION_SUBORDINATES",
    "ROLE_OF_STATUS",
    "ROLE_RANK_OF_STATUS",
    "JICC_HOLDERS",
    "JICC_CLASS_PEOPLE",
    "JICC_CLASS_MEAN_YEN",
    "CREDIT_MIN_AGE",
    "PLACE_CAPACITY_MEAN",
    "PLACE_CAPACITY_CV",
    "PLACE_CAPACITY_RANGE",
    "RANK_EXPONENT",
    "HEAPS_EXPONENT",
    "CAPACITY_WINDOW_WEEKS",
    "WEEKS_PER_YEAR",
    "MONTHS_PER_YEAR",
    "DUTY_WORDS",
    "DUTY_WORDS_NOT_IN_W20",
    "DUTY_SPLIT_SHARE",
    "savings_class",
    "calendar_inputs",
    "calendar_inputs_b",
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
    fn: Callable[[Mapping[str, np.ndarray], Any, AttrKey], np.ndarray]
    #: 段(3=段 1〜3 の W21・4〜7=段 4〜7 の続き)。段 1〜3 の manifest は段 3 の関数だけを書く(版の表を変えない)。
    stage: int = 3


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


# ------------------------------------------------------------------------------------------ 段 4〜7(W21 の続き)
#: 職業大分類(国勢調査 A〜K)→ 賃金構造基本統計調査の職種(大分類)の名(同じ分類=日本標準職業分類)。L(分類不能)は無い。
WAGE_OCCUPATIONS: Final[tuple[str, ...]] = (
    "管理的職業従事者", "専門的・技術的職業従事者", "事務従事者", "販売従事者", "サービス職業従事者", "保安職業従事者",
    "農林漁業従事者", "生産工程従事者", "輸送・機械運転従事者", "建設・採掘従事者", "運搬・清掃・包装等従事者",
)
#: 従業上の地位(国勢調査 8 区分)→ 賃金構造の雇用形態(0=一般の正社員・正職員・1=一般の正社員・正職員以外・2=短時間労働者・
#: −1=対象外=役員・業主・家族従業者・内職=R-107 §1-1 の空欄)。派遣は「正社員・正職員以外」・パート等は短時間に寄せる(expedient)。
WAGE_FORM_OF_STATUS: Final[Mapping[str, int]] = MappingProxyType({
    "regular": 0, "dispatched": 1, "part_time": 2, "executive": -1, "employer": -1, "self_employed": -1,
    "family_worker": -1, "home_worker": -1,
})
#: 賃金構造 第6表の年齢階級の下の端(～19・20-24 … 65-69・70～=12 階級)。
WAGE_AGE_EDGES: Final[np.ndarray] = np.array([0, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70], dtype=np.int64)
WAGE_AGE_EDGES.flags.writeable = False
#: 全国家計構造調査の世帯の種類(0=総世帯・1=二人以上の世帯・2=単身世帯)。
HH_TYPES: Final[tuple[str, ...]] = ("total", "multi", "single")
#: 全国家計構造調査 第4-4表の世帯主の年齢(5 歳階級: 30 歳未満・30-34 … 80-84・85 歳以上=13 階級)の下の端。
ASSET_AGE_EDGES: Final[np.ndarray] = np.array([0, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85], dtype=np.int64)
ASSET_AGE_EDGES.flags.writeable = False
#: 店(SR2 の「店長」・②群の開店)の業種(W16 の 15 語)。
STORE_INDUSTRIES: Final[tuple[str, ...]] = ("FB", "WR", "LS", "AM")
#: 課長 1 人あたりの部下(R-80 §2-2 の規模計・2023 年・賃金構造の原表から計算=引)。運輸と複合サービスは産業計 12.6
#: (R-80 §6-1 の案 A)。部署の目安の人数 S = 1 + この値(SR2 の決定 (a))。
R80_SUBORDINATES: Final[Mapping[str, float]] = MappingProxyType({
    "IT": 8.2, "PS": 8.2, "CN": 8.4, "RE": 8.8, "WR": 9.7, "FI": 10.1, "MF": 12.8, "LS": 13.1, "AM": 13.1,
    "FB": 16.0, "SV": 16.3, "ED": 17.7, "MW": 24.1, "TR": 12.6, "CS": 12.6,
})
#: 部長 1 人あたりの部下(R-80 §2-2・産業計 25.6=部の段の腕だけ)。
R80_DIVISION_SUBORDINATES: Final[float] = 25.6
#: 従業上の地位 → 役割の語(段 4 の組織の中の役割。頭の「店長」「代表」「責任者」「部署長」は ``w21_org`` が上書き)。
ROLE_OF_STATUS: Final[Mapping[str, str]] = MappingProxyType({
    "regular": "正社員", "dispatched": "派遣社員", "part_time": "パート・アルバイト", "executive": "役員",
    "employer": "業主", "self_employed": "業主", "family_worker": "家族従業者", "home_worker": "内職",
})
#: 頭(組織の長・部署の長)を選ぶ順(小さいほど先・同じなら年上・同じなら人の番号)。自前(expedient)。
ROLE_RANK_OF_STATUS: Final[Mapping[str, int]] = MappingProxyType({
    "executive": 0, "employer": 0, "self_employed": 0, "regular": 1, "home_worker": 2, "dispatched": 2,
    "part_time": 3, "family_worker": 4,
})
#: JICC 2026-08 末(R-107 §4=引・親確認は 1,091.5 万人・86.3 万円): 貸金業の残高がある人と、借入件数ごとの人数と
#: 1 人あたりの残高(1 件・2 件・3 件・4 件・5 件以上)。**異動(延滞)は使わない**(R-107 の振り分けの案=検証側)。
JICC_HOLDERS: Final[int] = 10_915_000
JICC_CLASS_PEOPLE: Final[tuple[int, ...]] = (6_815_000, 2_493_000, 1_038_000, 404_000, 163_000)
JICC_CLASS_MEAN_YEN: Final[tuple[int, ...]] = (669_000, 1_013_000, 1_277_000, 1_521_000, 2_357_000)
#: 貸金業の残高の口を持てる年齢の下限(自前・宣言)。
CREDIT_MIN_AGE: Final[int] = 20
#: なじみの場所の数(Alessandretti ほか 2018=「typical size of ∼25 locations」・個人の値は平均のまわりに一様に散る=
#: 本文に数の幅は無い)。平均 25(引)・個人の幅は変動係数(expedient=未リサーチ・感度試験の腕)。
PLACE_CAPACITY_MEAN: Final[float] = 25.0
PLACE_CAPACITY_CV: Final[float] = 0.3
PLACE_CAPACITY_RANGE: Final[tuple[int, int]] = (5, 60)
#: 順位ごとの行く頻度 f_k ∝ k^−ζ(Song ほか 2010 の ζ≈1.2=設計書 §2-5)。
RANK_EXPONENT: Final[float] = 1.2
#: 行ったことのある場所の数 L(t) ∝ t^μ(Song ほか 2010 の μ≈0.6=設計書 §2-5。Alessandretti 2018 は 0.63〜0.76)。
HEAPS_EXPONENT: Final[float] = 0.6
#: なじみの場所の集合を決める窓(Alessandretti 2018 の定義=20 週)。住んでいる期間がこれより短い人は L(t) < 容量(自前の結び=
#: expedient)。
CAPACITY_WINDOW_WEEKS: Final[float] = 20.0
WEEKS_PER_YEAR: Final[float] = 52.1775
#: 月 → 週の換算(週の時間の目安=月の時間 × 12 ÷ 1 年の週の数=〔検収 L8〕換算の値を 1 つに)。
MONTHS_PER_YEAR: Final[float] = 12.0
#: 居住期間の区分 → 年の幅(第18表。出生時から=年齢・20 年以上の上の端=年齢)。
_RESIDENCE_YEARS: Final[tuple[tuple[float, float], ...]] = ((0.0, -1.0), (0.0, 1.0), (1.0, 5.0), (5.0, 10.0),
                                                           (10.0, 20.0), (20.0, -1.0))
#: ②群の担当(``duty_role_org``)の語。W16 の ``duty_role`` の語に寄せた(対応の表は記録 pop41b §段 4)。
DUTY_WORDS: Final[tuple[str, ...]] = ("店長", "補充", "納品ドライバー", "配送作業員", "清掃作業員", "警備員",
                                      "駅員", "電車運転士", "車掌", "警察官", "消防士")
#: 〔検収 M1〕W20 の ``DUTY_ROLE_SPEC`` の鍵に無い語(段 10 で鍵に足す=勤務場所・交替制。足すまで W20 は「担当なし」と読む)。
DUTY_WORDS_NOT_IN_W20: Final[tuple[str, ...]] = ("店長", "補充", "配送作業員", "警備員")
#: 〔検収 M1〕1 語にまとめていた担当を W20 の鍵のとおり 2 語に分ける割合(人ごとの乱数=決定的)。前の語の割合=
#: **未リサーチ(expedient)**: 電車運転士と車掌=1 編成に 1 人ずつ(ワンマン運転の割合は空欄)・警察官と消防士=半々
#: (公務の保安職の内訳の表は取得していない)。
DUTY_SPLIT_SHARE: Final[Mapping[str, tuple[str, str, float]]] = MappingProxyType({
    "rail_crew": ("電車運転士", "車掌", 0.5),
    "public_safety": ("警察官", "消防士", 0.5),
})
_DELIVERY_SECTORS: Final[tuple[str, ...]] = ("倉庫", "宅配拠点", "運送", "配送/物流")


@dataclass(frozen=True)
class AttrTablesB:
    """段 4〜7 の材料の表(書き込み禁止)。金額は円・時間は時間。``md5`` は材料の表の id → md5。

    賃金(賃金構造 令和 7 年・企業規模計・職種 11 × 男女 2): ``wage_level``/``wage_bonus``/``wage_hours``=(11, 2, 2)
    (正社員・正職員 / 以外の所定内給与[円/月]・年間賞与[円]・所定内実労働時間[時間/月])・``wage_all``=(11, 2)(常用労働者計)・
    ``wage_age_ratio``/``bonus_age_ratio``=(11, 2, 12)(第6表の年齢階級 ÷ 計)・``wage_cls_lo``/``wage_cls_hi``=(K,)[円]・
    ``wage_cls_freq``=(11, 2, K)(第18表の階級の度数)・``wage_median``=(11, 2)・短時間 ``pt_*``=(11, 2)。
    資産(全国家計構造調査 2024): ``sav_freq``=(3, 19)(東京都の世帯数分布・貯蓄の階級)・``sav_cls_mean``=(3, 19)・
    ``sav_rate_cls``=(3, 19)(階級の貯蓄保有率)・``sav_lo``/``sav_hi``=(19,)・``debt_rate_cls``=(3, 19)・
    年齢の形(全国 第4-4表・13 階級)=``sav_mean_age``・``sav_rate_age``・``dep_mean_age``・``debt_mean_age``・
    ``debt_rate_age``=(3, 13)・水準(東京都 ÷ 全国)=``tokyo_ratio_sav``・``tokyo_ratio_debt``=(3,)・``sav_tilt``=(3, 13)
    (年齢の平均に合わせる傾け=表から解く)。信用(JICC)=``jicc_holder_rate``(20 歳以上の人に対する割合)。
    外から来る人: ``origin_codes``/``origin_names``/``origin_w``(第4表の流入元の重み)・``entry_nodes``/``entry_w``(W12 の
    鉄道の外の口と大都市交通センサスの流入の比)。
    """

    wage_level: np.ndarray
    wage_bonus: np.ndarray
    wage_hours: np.ndarray
    wage_all: np.ndarray
    wage_age_ratio: np.ndarray
    bonus_age_ratio: np.ndarray
    wage_cls_lo: np.ndarray
    wage_cls_hi: np.ndarray
    wage_cls_freq: np.ndarray
    wage_median: np.ndarray
    pt_hourly: np.ndarray
    pt_bonus: np.ndarray
    pt_hours_day: np.ndarray
    pt_days: np.ndarray
    sav_freq: np.ndarray
    sav_cls_mean: np.ndarray
    sav_rate_cls: np.ndarray
    sav_lo: np.ndarray
    sav_hi: np.ndarray
    debt_rate_cls: np.ndarray
    sav_mean_age: np.ndarray
    sav_rate_age: np.ndarray
    dep_mean_age: np.ndarray
    debt_mean_age: np.ndarray
    debt_rate_age: np.ndarray
    tokyo_ratio_sav: np.ndarray
    tokyo_ratio_debt: np.ndarray
    sav_tilt: np.ndarray
    jicc_holder_rate: float
    origin_codes: np.ndarray
    origin_names: np.ndarray
    origin_w: np.ndarray
    entry_nodes: np.ndarray
    entry_w: np.ndarray
    md5: Mapping[str, str] = field(default_factory=dict)

    def freeze(self) -> "AttrTablesB":
        for v in self.__dict__.values():
            if isinstance(v, np.ndarray):
                v.flags.writeable = False
        if not isinstance(self.md5, MappingProxyType):
            object.__setattr__(self, "md5", MappingProxyType(dict(self.md5)))
        return self


def _kind_is(attrs: Mapping[str, np.ndarray], word: str) -> np.ndarray:
    return np.asarray(attrs["kind"]).astype(str) == word


def _commuter_draw(attrs, tables: AttrTables, key: AttrKey) -> tuple[np.ndarray, np.ndarray]:
    """外から来て働く人(``kind="commuter"``)の(男女, 各歳)。第11-1表(従業地=渋谷区の 15 歳以上就業者)の男女 × 年齢 17
    階級を 1 つ目の乱数で・階級の中の各歳を 2 つ目の乱数で一様に引く(95 歳以上は 95〜100 歳)。ほかの人は −1。"""
    sel = _kind_is(attrs, "commuter")
    n = sel.size
    sex = np.full(n, -1, dtype=np.int64)
    age = np.full(n, -1, dtype=np.int64)
    w = tables.commuter_industry.sum(axis=2).ravel()  # (男 17…, 女 17…)
    if sel.any() and w.sum() > 0:
        u = key.uniform(words=2)[sel]
        k = np.minimum(np.searchsorted(np.cumsum(w) / w.sum(), u[:, 0], side="right"), w.size - 1)
        a17 = k % 17
        lo = 15 + 5 * a17
        hi = np.where(a17 == 16, 100, lo + 4)
        sex[sel] = k // 17
        age[sel] = lo + np.minimum((u[:, 1] * (hi - lo + 1)).astype(np.int64), hi - lo)
    return sex, age


def f_commuter_sex(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """外から来て働く人の男女(従業地 第11-1表・``tables`` は段 3 の :class:`AttrTables`)。"""
    return _commuter_draw(attrs, tables, key)[0]


def f_commuter_age(attrs, tables: AttrTables, key: AttrKey) -> np.ndarray:
    """外から来て働く人の年齢(同じ表・5 歳階級の中は一様=宣言)。"""
    return _commuter_draw(attrs, tables, key)[1]


def _categorical(w: np.ndarray, u: np.ndarray) -> np.ndarray:
    c = np.cumsum(np.asarray(w, dtype=np.float64))
    return np.minimum(np.searchsorted(c / c[-1], u, side="right"), c.size - 1)


def f_origin_muni(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """常住地(市区町村の 5 桁)。外から来て働く人=第4表の流入元の重み(渋谷区の残りの町丁目=輪は区の行の重み)・住民=13113。"""
    n = np.asarray(attrs["kind"]).size
    out = np.full(n, "", dtype=object)
    out[_kind_is(attrs, "resident")] = "13113"
    com = _kind_is(attrs, "commuter")
    if com.any() and tables.origin_w.sum() > 0:
        out[com] = tables.origin_codes[_categorical(tables.origin_w, key.uniform()[com, 0])]
    return out


def f_entry_node(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """舞台の出入りの駅の口(W12 の鉄道の外の口)。外から来て働く人と、舞台の外で働く住民(区の残り・区の外)だけ。重み=
    大都市交通センサスの路線別の流入(W12 の ``daily_inflow``・構築側の欄)の比(expedient=方面と常住地を結ばない)。"""
    n = np.asarray(attrs["kind"]).size
    out = np.full(n, "", dtype=object)
    wa = np.asarray(attrs["workplace_area"]).astype(str)
    sel = _kind_is(attrs, "commuter") | (_kind_is(attrs, "resident") & np.isin(wa, ["ward_outside_stage", "outside_ward"]))
    if sel.any() and tables.entry_w.sum() > 0:
        out[sel] = tables.entry_nodes[_categorical(tables.entry_w, key.uniform()[sel, 0])]
    return out


def _status_words(attrs) -> np.ndarray:
    st = np.asarray(attrs["emp_status"], dtype=np.int64)
    lut = np.array([*EMP_STATUS, ""], dtype=object)
    return lut[np.where(st >= 0, st, len(EMP_STATUS))]


def f_org_role(attrs, tables: Any, key: AttrKey) -> np.ndarray:
    """従業上の地位 → 組織の中の役割の語(:data:`ROLE_OF_STATUS`・就業者でない人は "")。頭の語は ``w21_org`` が上書きする。"""
    sw = _status_words(attrs)
    uniq, inv = np.unique(sw.astype(str), return_inverse=True)
    lut = np.array([ROLE_OF_STATUS.get(x, "") for x in uniq.tolist()], dtype=object)  # 逐次: 語の種類の数
    return lut[inv] if sw.size else np.zeros(0, dtype=object)


def _occ_sex_form(attrs) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    occ = np.asarray(attrs["occupation_major"], dtype=np.int64)
    sex = np.asarray(attrs["sex"], dtype=np.int64)
    sw = _status_words(attrs)
    uniq, inv = np.unique(sw.astype(str), return_inverse=True)
    lut = np.array([WAGE_FORM_OF_STATUS.get(x, -1) for x in uniq.tolist()], dtype=np.int64)  # 逐次: 語の種類の数
    form = lut[inv] if sw.size else np.zeros(0, dtype=np.int64)
    ok = (occ >= 0) & (occ < len(WAGE_OCCUPATIONS)) & (sex >= 0) & (form >= 0)
    return np.clip(occ, 0, len(WAGE_OCCUPATIONS) - 1), np.clip(sex, 0, 1), form, ok


def f_weekly_hours(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """週の所定内の時間の目安(権利台帳の雇用の行・段 4)。一般=第9表の所定内実労働時間(月)× 12 ÷ 52.1775 週・短時間=
    第2表の 1 日の時間 × 実労働日数 × 12 ÷ 52.1775 週(:data:`WEEKS_PER_YEAR`)。役員・業主・家族従業者・職業が分類不能の
    人は NaN(空欄)。"""
    occ, sex, form, ok = _occ_sex_form(attrs)
    out = np.full(occ.size, np.nan)
    gen = ok & (form <= 1)
    out[gen] = tables.wage_hours[occ[gen], sex[gen], form[gen]] * MONTHS_PER_YEAR / WEEKS_PER_YEAR
    pt = ok & (form == 2)
    out[pt] = (tables.pt_hours_day[occ[pt], sex[pt]] * tables.pt_days[occ[pt], sex[pt]]
               * MONTHS_PER_YEAR / WEEKS_PER_YEAR)
    return np.round(out, 2)


def _wage_quantile(tables: AttrTablesB, occ: np.ndarray, sex: np.ndarray, u: np.ndarray) -> np.ndarray:
    """第18表の所定内給与額の階級の度数(職種 × 男女)から分位 u の値[円/月](階級の中は一様=宣言)。"""
    f = tables.wage_cls_freq[occ, sex]  # (n, K)
    c = np.cumsum(f, axis=1)
    tot = c[:, -1]
    k = np.minimum((c < (u * tot)[:, None]).sum(axis=1), f.shape[1] - 1)
    prev = np.where(k > 0, c[np.arange(k.size), np.maximum(k - 1, 0)], 0.0)
    fk = f[np.arange(k.size), k]
    pos = np.divide(u * tot - prev, fk, out=np.full(k.size, 0.5), where=fk > 0)
    lo, hi = tables.wage_cls_lo[k], tables.wage_cls_hi[k]
    return np.where(tot > 0, lo + np.clip(pos, 0.0, 1.0) * (hi - lo), np.nan)


def _wage(attrs, tables: AttrTablesB, key: AttrKey) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """(所定内給与[円/月], 時間あたり[円], 年の賃金[円])。同じ鍵なら 3 つは同じ人の同じ値から出る。対象外は −1。

    一般(正社員・正職員/以外): 第18表の階級の度数(職種 × 男女=雇用形態と年齢をまとめた形)の分位 u の値 × 年齢の比
    (第6表)× 雇用形態の比(第9表の形態 ÷ 常用労働者計)。年の賃金=12 × 月+賞与(第9表の形態 × 第6表の年齢の比)。
    短時間: 第2表の 1 時間あたり × 第18表の形(分位 u の値 ÷ 中位数)・月=時間あたり × 1 日の時間 × 日数・年=12 × 月+賞与。
    比をかけ合わせるのは独立の仮定(expedient)。"""
    occ, sex, form, ok = _occ_sex_form(attrs)
    age = np.asarray(attrs["age"], dtype=np.int64)
    n = occ.size
    monthly = np.full(n, -1.0)
    hourly = np.full(n, -1.0)
    annual = np.full(n, -1.0)
    if not ok.any():
        return monthly.astype(np.int64), hourly.astype(np.int64), annual.astype(np.int64)
    u = key.uniform()[:, 0]
    q = _wage_quantile(tables, occ, sex, u)
    ac = np.clip(np.searchsorted(WAGE_AGE_EDGES, age, side="right") - 1, 0, WAGE_AGE_EDGES.size - 1)
    gen = ok & (form <= 1) & np.isfinite(q)
    if gen.any():
        o, s, f, a = occ[gen], sex[gen], form[gen], ac[gen]
        ratio = np.divide(tables.wage_level[o, s, f], tables.wage_all[o, s], out=np.ones(o.size),
                          where=tables.wage_all[o, s] > 0)
        m = q[gen] * tables.wage_age_ratio[o, s, a] * ratio
        h = np.divide(m, tables.wage_hours[o, s, f], out=np.full(o.size, -1.0), where=tables.wage_hours[o, s, f] > 0)
        monthly[gen], hourly[gen] = m, h
        annual[gen] = 12.0 * m + tables.wage_bonus[o, s, f] * tables.bonus_age_ratio[o, s, a]
    pt = ok & (form == 2) & np.isfinite(q) & (tables.pt_hourly[occ, sex] > 0)
    if pt.any():
        o, s = occ[pt], sex[pt]
        shape = np.divide(q[pt], tables.wage_median[o, s], out=np.ones(o.size), where=tables.wage_median[o, s] > 0)
        h = tables.pt_hourly[o, s] * shape
        m = h * tables.pt_hours_day[o, s] * tables.pt_days[o, s]
        hourly[pt], monthly[pt] = h, m
        annual[pt] = 12.0 * m + tables.pt_bonus[o, s]
    r = lambda x: np.where(x >= 0, np.round(x), -1).astype(np.int64)  # noqa: E731
    return r(monthly), r(hourly), r(annual)


def f_wage_monthly(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """所定内給与[円/月](賃金構造 令和 7 年)。雇われて働く人で職業が分かる人だけ・ほかは −1(空欄)。"""
    return _wage(attrs, tables, key)[0]


def f_wage_hourly(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """時間あたりの所定内給与[円](同じ鍵で ``wage_monthly`` と同じ人の値)。"""
    return _wage(attrs, tables, key)[1]


def f_wage_annual(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """年の賃金[円]=12 × 月+年間賞与(同じ鍵で ``wage_monthly`` と同じ人の値)。"""
    return _wage(attrs, tables, key)[2]


def _hh(attrs) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    t = np.asarray(attrs["hh_type"], dtype=np.int64)
    a = np.asarray(attrs["head_age"], dtype=np.int64)
    ok = (t >= 0) & (t < len(HH_TYPES)) & (a >= 0)
    ac = np.clip(np.searchsorted(ASSET_AGE_EDGES, a, side="right") - 1, 0, ASSET_AGE_EDGES.size - 1)
    return np.clip(t, 0, len(HH_TYPES) - 1), ac, ok


def savings_class(tables: AttrTablesB, yen: np.ndarray) -> np.ndarray:
    """貯蓄[円] → 貯蓄現在高の階級(0=25 万円未満=0 円を含む)。"""
    return np.clip(np.searchsorted(tables.sav_lo, np.asarray(yen, dtype=np.float64), side="right") - 1, 0,
                   tables.sav_lo.size - 1)


def f_household_savings(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """世帯の金融資産残高(貯蓄現在高)[円](全国家計構造調査 2024・世帯の単位)。**階級の度数をそのまま**(R-107 結論 2):
    0 円か正かを全国の年齢 × 世帯の種類の貯蓄保有率で・正の階級を東京都の世帯数分布(25 万円未満の階級は貯蓄保有率の分だけ)を
    年齢の平均に合わせて傾けた重み(``sav_tilt``=表から解いた)で・階級の中は一様(最上の 1 億円以上の階級は階級の平均に合う
    Pareto=宣言)。入力は ``hh_type``(0 総世帯・1 二人以上・2 単身)と ``head_age``。ほかは −1。"""
    t, ac, ok = _hh(attrs)
    n = t.size
    out = np.full(n, -1, dtype=np.int64)
    if not ok.any():
        return out
    u = key.uniform(words=3)
    pos = (u[:, 0] < tables.sav_rate_age[t, ac] / 100.0) & ok
    w = tables.sav_freq[t] * tables.sav_rate_cls[t] / 100.0 * np.exp(
        tables.sav_tilt[t, ac][:, None] * np.log(np.maximum(tables.sav_cls_mean[t], 1.0)))
    c = np.cumsum(w, axis=1)
    k = np.minimum((c < (u[:, 1] * c[:, -1])[:, None]).sum(axis=1), w.shape[1] - 1)
    lo, hi = tables.sav_lo[k], tables.sav_hi[k]
    val = lo + u[:, 2] * (hi - lo)
    top = k == w.shape[1] - 1
    if top.any():
        m = tables.sav_cls_mean[t[top], k[top]]
        alpha = np.where(m > lo[top] * 1.0001, m / np.maximum(m - lo[top], 1.0), 50.0)
        val[top] = lo[top] * np.power(np.maximum(1.0 - u[top, 2], 1e-12), -1.0 / alpha)
    val[(k == 0) & pos] = np.maximum(val[(k == 0) & pos], 1.0)  # 25 万円未満の正の値は 1 円以上
    out[ok] = np.where(pos[ok], np.round(val[ok]), 0).astype(np.int64)
    return out


def f_household_deposits(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """世帯の通貨性預貯金[円]=貯蓄 × 通貨性預貯金の平均 ÷ 貯蓄の平均(全国 第4-4表・世帯の種類 × 年齢・比は一定=宣言)。"""
    t, ac, ok = _hh(attrs)
    sv = np.asarray(attrs["household_savings"], dtype=np.int64)
    r = np.divide(tables.dep_mean_age[t, ac], tables.sav_mean_age[t, ac], out=np.zeros(t.size),
                  where=tables.sav_mean_age[t, ac] > 0)
    return np.where(ok & (sv >= 0), np.round(sv * np.clip(r, 0.0, 1.0)), -1).astype(np.int64)


def f_household_debt(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """世帯の金融負債残高[円]。有無=全国の年齢 × 種類の負債保有率 × 東京都の貯蓄の階級ごとの負債保有率 ÷ 東京都の全体の率
    (貯蓄と負債の相関・R-107 §1-6)・額=負債を持つ世帯の平均(全国の年齢 × 種類 × 東京都 ÷ 全国の水準)=**額の広がりは空欄**
    (階級の度数の表が無い)。"""
    t, ac, ok = _hh(attrs)
    sv = np.asarray(attrs["household_savings"], dtype=np.int64)
    ok = ok & (sv >= 0)
    n = t.size
    out = np.full(n, -1, dtype=np.int64)
    if not ok.any():
        return out
    cls = savings_class(tables, np.maximum(sv, 0))
    zero = sv == 0
    overall = np.divide((tables.sav_freq * tables.debt_rate_cls).sum(axis=1), tables.sav_freq.sum(axis=1),
                        out=np.ones(len(HH_TYPES)), where=tables.sav_freq.sum(axis=1) > 0)
    cls_rate = np.where(zero, tables.debt_rate_cls[t, 0], tables.debt_rate_cls[t, cls])
    p = tables.debt_rate_age[t, ac] / 100.0 * np.divide(cls_rate, overall[t], out=np.ones(n), where=overall[t] > 0)
    u = key.uniform()[:, 0]
    holder = (u < np.clip(p, 0.0, 1.0)) & ok
    per = np.divide(tables.debt_mean_age[t, ac], tables.debt_rate_age[t, ac] / 100.0, out=np.zeros(n),
                    where=tables.debt_rate_age[t, ac] > 0) * tables.tokyo_ratio_debt[t]
    out[ok] = np.where(holder[ok], np.round(per[ok]), 0).astype(np.int64)
    return out


def f_consumer_credit(attrs, tables: AttrTablesB, key: AttrKey) -> np.ndarray:
    """貸金業の残高[円](JICC 2026-08 末=引)。20 歳以上だけ・有無=残高のある人 ÷ 全国の 20 歳以上人口(国勢調査 2025)・
    額=借入件数の区分を人数の比で引いて区分の 1 人あたり残高(区分の中の広がりは空欄)。世帯の負債とは別に引く(内訳の整合は
    空欄=宣言)。20 歳未満は 0。"""
    age = np.asarray(attrs["age"], dtype=np.int64)
    out = np.zeros(age.size, dtype=np.int64)
    adult = age >= CREDIT_MIN_AGE
    if not adult.any():
        return out
    u = key.uniform(words=2)
    has = adult & (u[:, 0] < tables.jicc_holder_rate)
    k = _categorical(np.asarray(JICC_CLASS_PEOPLE, dtype=np.float64), u[:, 1])
    out[has] = np.asarray(JICC_CLASS_MEAN_YEN, dtype=np.int64)[k[has]]
    return out


def f_blank_int(attrs, tables: Any, key: AttrKey) -> np.ndarray:
    """空欄(−1)を返すだけの関数(財布の現金・カードの有無・口座の有無=構築側の錨が無い=R-107 §1-7・回答 10-12b §3 (2))。"""
    return np.full(np.asarray(attrs["age"]).size, -1, dtype=np.int64)


def f_residence_years(attrs, tables: Any, key: AttrKey) -> np.ndarray:
    """住んでいる年数(第18表の区分の中で一様=宣言・出生時から=年齢・20 年以上の上の端=年齢)。区分が空欄の人は NaN。"""
    rp = np.asarray(attrs["residence_period"], dtype=np.int64)
    age = np.asarray(attrs["age"], dtype=np.float64)
    out = np.full(rp.size, np.nan)
    ok = rp >= 0
    if not ok.any():
        return out
    lo = np.array([r[0] for r in _RESIDENCE_YEARS])[np.clip(rp, 0, 5)]
    hi = np.array([r[1] for r in _RESIDENCE_YEARS])[np.clip(rp, 0, 5)]
    hi = np.where(hi < 0, np.maximum(age + 0.999, lo), hi)
    u = key.uniform()[:, 0]
    val = np.where(rp == 0, age + u * 0.999, lo + u * (hi - lo))
    out[ok] = np.minimum(val[ok], age[ok] + 0.999)
    return np.floor(out * 1000.0) / 1000.0  # 千分の 1 年で切り捨て(区分の上の端を越えない)


def f_place_capacity(attrs, tables: Any, key: AttrKey) -> np.ndarray:
    """なじみの場所の数(容量)C=round(正規(25, 25 × CV))を [5, 60] に切る(平均=Alessandretti 2018・幅=expedient)。"""
    n = np.asarray(attrs["age"]).size
    u = key.uniform(words=2)
    z = np.sqrt(-2.0 * np.log(np.maximum(u[:, 0], 1e-300))) * np.cos(2.0 * np.pi * u[:, 1])
    c = np.round(PLACE_CAPACITY_MEAN * (1.0 + PLACE_CAPACITY_CV * z))
    return np.clip(c, *PLACE_CAPACITY_RANGE).astype(np.int64) if n else np.zeros(0, dtype=np.int64)


def f_known_places(attrs, tables: Any, key: AttrKey) -> np.ndarray:
    """行ったことのある場所の数 L=C ×(住んでいる週 ÷ 20 週)^0.6(Song 2010 の μ・20 週=容量の窓)。住んでいる年数が空欄の
    人(外から来る人)は L=C。少なくとも 1。"""
    c = np.asarray(attrs["place_capacity"], dtype=np.float64)
    y = np.asarray(attrs["residence_years"], dtype=np.float64)
    wk = np.where(np.isfinite(y), np.maximum(y, 0.0) * WEEKS_PER_YEAR, CAPACITY_WINDOW_WEEKS)
    lt = c * np.power(np.maximum(wk, 1.0) / CAPACITY_WINDOW_WEEKS, HEAPS_EXPONENT)
    return np.maximum(1, np.round(lt)).astype(np.int64)


def f_duty_role_org(attrs, tables: Any, key: AttrKey) -> np.ndarray:
    """②群(開店・補充・配送・運転・駅員・車掌・運転士)を受け持つ体の語(規則の表=自前・expedient・W16 の語に寄せた)。

    1. 物流の組織(W6 の倉庫・宅配拠点・運送・配送/物流)で輸送・機械運転 I → 納品ドライバー・運搬・清掃・包装 K → 配送作業員
    2. 施設管理/メンテの組織で K → 清掃作業員・警備の組織で保安 F → 警備員
    3. 店(FB・WR・LS・AM)の頭(役割「店長」)→ 店長(開店と閉店)
    4. 小売(WR)の組織に席がある販売 D・サービス E・運搬 K → 補充
    5. 運輸(TR)で W6 に席が無い人(鉄道・バス・タクシーの会社は W6 に無い)の I → 電車運転士か車掌・事務 C・販売 D・
       サービス E → 駅員
    6. 公務(S)の保安 F → 警察官か消防士

    〔検収 M2〕どの規則も**勤め先が舞台の中**(``workplace_area == "stage"``)の体だけ=自宅で働く人と舞台の外で働く住民は
    担当なし(②群は舞台の中の仕事)。〔検収 M1〕まとめた 2 語は W20 の鍵のとおり 2 語に分ける(:data:`DUTY_SPLIT_SHARE`・
    人ごとの乱数 ``key``)。
    """
    ik = np.asarray(attrs["industry_key"]).astype(str)
    im = np.asarray(attrs["industry_major"], dtype=np.int64)
    sec = np.asarray(attrs["org_sector"]).astype(str)
    occ = np.asarray(attrs["occupation_major"], dtype=np.int64)
    role = np.asarray(attrs["org_role"]).astype(str)
    org = np.asarray(attrs["org_id"], dtype=np.int64)
    stage = np.asarray(attrs["workplace_area"]).astype(str) == "stage"
    L = OCCUPATION_MAJORS
    o = np.where(occ >= 0, np.array(L + ("",), dtype=object)[np.clip(occ, 0, len(L))], "").astype(str)
    out = np.full(ik.size, "", dtype=object)
    rules = [
        (np.isin(sec, _DELIVERY_SECTORS) & (o == "I"), "納品ドライバー"),
        (np.isin(sec, _DELIVERY_SECTORS) & (o == "K"), "配送作業員"),
        ((sec == "施設管理/メンテ") & (o == "K"), "清掃作業員"),
        ((sec == "警備") & (o == "F"), "警備員"),
        (np.isin(ik, STORE_INDUSTRIES) & (role == "店長") & (org >= 0), "店長"),
        ((ik == "WR") & (org >= 0) & np.isin(o, ["D", "E", "K"]), "補充"),
        ((ik == "TR") & (org < 0) & (o == "I"), "rail_crew"),
        ((ik == "TR") & (org < 0) & np.isin(o, ["C", "D", "E"]), "駅員"),
        ((im == INDUSTRY_MAJORS.index("S")) & (o == "F"), "public_safety"),
    ]
    done = ~stage  # 舞台の外で働く人・働いていない人は担当なし
    for m, word in rules:  # 逐次: 規則の数ぶん(9)
        hit = m & ~done
        out[hit] = word
        done |= hit
    u = key.uniform()[:, 0] if out.size else np.zeros(0)
    for group, (first, second, share) in DUTY_SPLIT_SHARE.items():  # 逐次: 分ける語の数(2)
        g = out == group
        out[g] = np.where(u[g] < share, first, second)
    return out


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
    # ---- 段 4 組織と関係(``tables`` は段 3 の AttrTables か段 4〜7 の AttrTablesB)
    AttrFn("commuter_sex", "1.1.0", ("kind",), ("c20_e11",), f_commuter_sex, 4),
    AttrFn("commuter_age", "1.1.0", ("kind",), ("c20_e11",), f_commuter_age, 4),
    AttrFn("origin_muni", "1.1.0", ("kind",), ("c20_t04",), f_origin_muni, 4),
    AttrFn("entry_node", "1.1.0", ("kind", "workplace_area"), ("w12_external_nodes",), f_entry_node, 4),
    AttrFn("org_role", "1.1.0", ("emp_status",), (), f_org_role, 4),
    AttrFn("weekly_hours", "1.1.0", ("emp_status", "occupation_major", "sex"), ("wage_t9", "wage_t2"),
           f_weekly_hours, 4),
    AttrFn("duty_role_org", "1.1.0", ("industry_key", "industry_major", "org_sector", "occupation_major", "org_role",
                                      "org_id", "workplace_area"), (), f_duty_role_org, 4),
    # ---- 段 5 お金(EC2)
    AttrFn("wage_monthly", "1.1.0", ("emp_status", "occupation_major", "sex", "age"),
           ("wage_t9", "wage_t6", "wage_t18", "wage_t2"), f_wage_monthly, 5),
    AttrFn("wage_hourly", "1.1.0", ("emp_status", "occupation_major", "sex", "age"),
           ("wage_t9", "wage_t6", "wage_t18", "wage_t2"), f_wage_hourly, 5),
    AttrFn("wage_annual", "1.1.0", ("emp_status", "occupation_major", "sex", "age"),
           ("wage_t9", "wage_t6", "wage_t18", "wage_t2"), f_wage_annual, 5),
    AttrFn("household_savings", "1.1.0", ("hh_type", "head_age"), ("zk_t31_0", "zk_t4_4", "zk_t23_0"),
           f_household_savings, 5),
    AttrFn("household_deposits", "1.1.0", ("hh_type", "head_age", "household_savings"), ("zk_t4_4",),
           f_household_deposits, 5),
    AttrFn("household_debt", "1.1.0", ("hh_type", "head_age", "household_savings"), ("zk_t31_0", "zk_t4_4",
                                                                                      "zk_t23_0"), f_household_debt, 5),
    AttrFn("consumer_credit", "1.1.0", ("age",), ("jicc_2026_08", "c25w_b02_05"), f_consumer_credit, 5),
    AttrFn("wallet_cash", "1.1.0", ("age",), (), f_blank_int, 5),
    AttrFn("card_holding", "1.1.0", ("age",), (), f_blank_int, 5),
    AttrFn("account_holding", "1.1.0", ("age",), (), f_blank_int, 5),
    # ---- 段 6 開始前の経験(PS4)
    AttrFn("residence_years", "1.1.0", ("residence_period", "age"), ("sa_t18",), f_residence_years, 6),
    AttrFn("place_capacity", "1.1.0", ("age",), ("alessandretti_2018",), f_place_capacity, 6),
    AttrFn("known_places", "1.1.0", ("place_capacity", "residence_years"), ("song_2010",), f_known_places, 6),
)})


def registry_versions(stages: tuple[int, ...]) -> dict[str, str]:
    """登録表の名 → 版(``stages`` の段の関数だけ・登録の順)。"""
    return {f.name: f.version for f in REGISTRY.values() if f.stage in stages}


def call(name: str, attrs: Mapping[str, np.ndarray], tables: AttrTables, key: AttrKey) -> np.ndarray:
    """登録表の関数を呼ぶ(入力の列がそろっていなければ止める)。"""
    f = REGISTRY[name]
    missing = [c for c in f.inputs if c not in attrs]
    if missing:
        raise KeyError(f"{name}: 入力の列が無い {missing}")
    return f.fn(attrs, tables, key)


def calendar_inputs_b(people: Mapping[str, Any]) -> dict[str, np.ndarray]:
    """**段 10 の材料**(W20 の入力そのものではない): 段 4〜7 の人の表(``w21_people``=住民+外から来て働く人)の 5 列
    (``kind``=W16 の番号 ``w16_kind``・``age``・``industry_key``・``employment_status``=英語の 5 語のまま・
    ``duty_role``=段 4 で埋めた②群の担当・空欄は "")。

    〔検収 M1・親の判断〕W20 の入力は ``Attributes``(19 欄)と ``Employment`` で、段 10 で W21 から ``Attributes`` を作る
    関数を書く(職業は ``occupation_major`` を直接・雇用の語は :data:`W16_EMPLOYMENT_OF` で写す・担当の語は W20 の
    ``DUTY_ROLE_SPEC`` の鍵)。W20 は鍵に無い担当の語を黙って「担当なし」と読み、種別 0・2 の体の担当を見ない
    (つなぎの台帳 ``DOC-pop41b-w20-port``)。"""
    return {
        "kind": np.asarray(people["w16_kind"], dtype=np.int64),
        "age": np.asarray(people["age"], dtype=np.int64),
        "industry_key": np.asarray(people["industry_key"], dtype=object),
        "employment_status": np.asarray(people["employment_status"], dtype=object),
        "duty_role": np.asarray(people["duty_role"], dtype=object),
    }


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
