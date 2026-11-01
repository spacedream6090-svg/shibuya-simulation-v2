"""W21 の表の組み立て(段 2 の手順 1・2=区の雛形と町丁目への配分)。

正: 答申 R-116 §3-2 の手順 1・2・PENDING 仮-23(「2025 の区の総数 × 2020 の町丁目の形」で作り、2025 の町丁目の表が
出たら差し替える)。

- **区の雛形(2025)**: 第10表の不詳補完値(家族類型 16 × 世帯人員 7)・第12-1表(世帯主の男女・年齢・配偶関係・家族類型)・
  第13-1表の不詳補完値(続き柄 × 男女 × 年齢 × 配偶関係 × 家族類型)・第19-1表(夫と妻の年齢 各歳)・第2-1表の不詳補完値
  (男女 × 年齢 各歳・国籍総数と日本人)。
- **町丁目(2020)の形**: 第1・2・3・4・5-2・6-1・6-2・7-1・8-1 表。町丁目の「不詳」(年齢・配偶関係・家族類型)は、区の
  「2020 の遡及の不詳補完値 − 2020 の原数値」の比で割り振る。ほかの表の「不詳」は町丁目 × 男女の既知の比で割り振る。
- **2020 の形 × 2025 の総数**: 町丁目 × 分類の表を、行=町丁目の 2020 の総数 × (区の 2025 の総数 ÷ 区の 2020 の総数)、
  列=区の 2025 の分類ごとの総数へ IPF(``fitting.ipf``)で合わせる(2025 の区の表が無い表は 2020 の形のまま総数だけ直す)。
  舞台の値は町丁目の被覆率を掛けた値(W16 と同じ按分)。

これらの近似の宣言は ``w21_build.W21_EXPEDIENTS``(つなぎの台帳に 1 行ずつ)。

逐次ループ宣言(P4): 表の分類の数ぶん(年齢 16〜106・家族類型 16・続き柄 12)と町丁目の数ぶん(80)。体の数に比例する
ループは無い。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Final, Mapping

import numpy as np

from . import fitting as F
from . import w16_population as W16
from . import w21_sources as S

__all__ = [
    "MAX_AGE",
    "AGE16_EDGES",
    "FAMILY_TYPES",
    "GROUPS",
    "GROUP_OF_TYPE",
    "COARSE_OF_TYPE",
    "SIZES",
    "MARITAL",
    "Ward2025",
    "ChomeTables",
    "Targets",
    "load_ward",
    "load_chome",
    "make_targets",
    "age_class",
    "expand_single_year",
    "rake_chome_to_ward",
]

#: 年齢の上限(各歳の表は 110 歳以上まで・これより上は上限に寄せる=宣言)。
MAX_AGE: Final[int] = 105
N_AGE: Final[int] = MAX_AGE + 1
#: 町丁目の年齢 16 階級(0-4 … 70-74・75 歳以上=W16 と同じ)。
AGE16_EDGES: Final[np.ndarray] = np.asarray(W16.AGE_EDGES, dtype=np.int64)
#: 第13-1表の年齢 21 階級(0-4 … 95-99・100 歳以上)。
AGE21_EDGES: Final[np.ndarray] = np.arange(0, 101, 5, dtype=np.int64)
#: 第12-1表の世帯主の年齢 15 階級(15-19 … 80-84・85 歳以上)。15 歳未満と「不詳」は使わない。
AGE_HEAD_EDGES: Final[np.ndarray] = np.arange(15, 86, 5, dtype=np.int64)
#: 就業の表の年齢 17 階級(15-19 … 90-94・95 歳以上)。
AGE17_EDGES: Final[np.ndarray] = np.arange(15, 96, 5, dtype=np.int64)

#: 家族類型(第10表の細かい区分=16)。番号は表の項目名の頭。
FAMILY_TYPES: Final[tuple[str, ...]] = (
    "111", "112", "113", "114", "1201", "1202", "1203", "1204", "1205", "1206", "1207", "1208", "1209", "1210",
    "2", "3",
)
#: 町丁目の第6-1表の区分(6)。
GROUPS: Final[tuple[str, ...]] = ("single", "couple", "couple_children", "lone_parent", "other_relatives",
                                  "non_relative")
GROUP_OF_TYPE: Final[Mapping[str, str]] = MappingProxyType({
    "111": "couple", "112": "couple_children", "113": "lone_parent", "114": "lone_parent",
    **{f"12{i:02d}": "other_relatives" for i in range(1, 11)}, "2": "non_relative", "3": "single",
})
#: 第13-1表の家族類型の粗い区分(世帯員の分布を引く先)。
COARSE_OF_TYPE: Final[Mapping[str, str]] = MappingProxyType({
    "111": "111", "112": "11", "113": "11", "114": "11",
    **{f"12{i:02d}": "12" for i in range(1, 11)}, "2": "2", "3": "3",
})
SIZES: Final[int] = 7
#: 配偶関係(人の列): 未婚・有配偶・死別・離別。町丁目の第4表は「死別・離別」をまとめる。
MARITAL: Final[tuple[str, ...]] = ("never_married", "married", "widowed", "divorced")
MARITAL3_OF4: Final[np.ndarray] = np.array([0, 1, 2, 2], dtype=np.int64)
for _arr in (AGE16_EDGES, AGE21_EDGES, AGE_HEAD_EDGES, AGE17_EDGES, MARITAL3_OF4):  # 読み取り専用(検収 L3)
    _arr.flags.writeable = False


def age_class(age: np.ndarray, edges: np.ndarray) -> np.ndarray:
    """各歳 → 階級(``edges`` の下端・最後の階級は上が開いている)。下端より若い年齢は −1。"""
    a = np.asarray(age, dtype=np.int64)
    k = np.searchsorted(edges, a, side="right") - 1
    return np.where(a < edges[0], -1, k)


def _num_prefix(label: str) -> str:
    return label.split("_", 1)[0]


# ------------------------------------------------------------------------------------------ 区(2025)
@dataclass(frozen=True)
class Ward2025:
    """区の雛形(2025)と、町丁目の不詳を割り振る比(2020 の補完値 − 原数値)。"""

    shape: np.ndarray            # (2, N_AGE) 各歳の人口(不詳補完値・男女)=階級の中の各歳の形
    foreign_share: np.ndarray    # (2, N_AGE) 国籍総数のうち日本人でない人の割合(補完値)
    pop_total: float             # 区の人口(2025)
    age16_sex: np.ndarray        # (16, 2) 2025 の年齢 16 階級 × 男女(補完値)
    pop15_by_sex: np.ndarray     # (2,) 15 歳以上
    marital3_sex: np.ndarray     # (3, 2) 15 歳以上の配偶関係(一般世帯人員の比を総人口へ伸ばした)
    hh_type_size: np.ndarray     # (16, 7) 家族類型 × 世帯人員(補完値)
    hh_total: float
    gh_persons: float            # 一般世帯人員
    head: dict[str, np.ndarray]  # 家族類型 → (2, 15, 4) 世帯主の男女 × 年齢 15 階級 × 配偶関係(原数値・不詳を除く)
    members: dict[tuple[str, str], np.ndarray]  # (続き柄の番号, 粗い家族類型) → (2, 21, 4) 男女 × 年齢 × 配偶関係
    couples: np.ndarray          # (N_AGE, N_AGE) 夫の年齢 × 妻の年齢(各歳・85 歳以上は形で各歳に広げた)
    inst_sex_age: np.ndarray     # (2, N_AGE) 施設等の世帯の人(総人口 − 一般世帯人員)
    unknown_age16: np.ndarray    # (2, 16) 町丁目の年齢不詳を割り振る比
    unknown_marital3: np.ndarray  # (2, 3) 町丁目の配偶関係不詳を割り振る比
    unknown_group: np.ndarray    # (6,) 町丁目の家族類型不詳を割り振る比
    pop2020: float               # 区の人口(2020 の遡及の補完値=総数)
    foreign_total: float         # 区の日本人でない人(2025 補完値)


def _single_year(vals: np.ndarray, items: tuple[str, ...]) -> np.ndarray:
    """第2-1表の各歳の項目 → ``N_AGE`` の配列(MAX_AGE より上は寄せる)。"""
    out = np.zeros(N_AGE)
    for j, lab in enumerate(items):
        m = re.match(r"^(\d{3})_(\d+)歳", lab)
        if not m or lab.startswith("000"):
            continue
        a = min(int(m.group(2)), MAX_AGE)
        v = vals[j]
        out[a] += 0.0 if np.isnan(v) else v
    return out


def expand_single_year(cls_vals: np.ndarray, edges: np.ndarray, shape: np.ndarray) -> np.ndarray:
    """階級の値(…, n_cls)→ 各歳(…, N_AGE)。階級の中は ``shape``(N_AGE)の比で配る(形が 0 の階級は一様)。"""
    v = np.asarray(cls_vals, dtype=np.float64)
    cls = age_class(np.arange(N_AGE), edges)
    out = np.zeros(v.shape[:-1] + (N_AGE,))
    for k in range(edges.size):  # 逐次: 階級の数ぶん
        ages = np.flatnonzero(cls == k)
        if ages.size == 0:
            continue
        w = shape[ages].astype(np.float64)
        w = w / w.sum() if w.sum() > 0 else np.full(ages.size, 1.0 / ages.size)
        out[..., ages] = v[..., k:k + 1] * w
    return out


def _cls_sum(single: np.ndarray, edges: np.ndarray) -> np.ndarray:
    cls = age_class(np.arange(N_AGE), edges)
    out = np.zeros(single.shape[:-1] + (edges.size,))
    for k in range(edges.size):  # 逐次: 階級の数ぶん
        out[..., k] = single[..., cls == k].sum(axis=-1)
    return out


_SEX = ("1_男", "2_女")
_MAR4 = ("1_未婚", "2_有配偶", "3_死別", "4_離別")


def _b13_members(d: S.Derived) -> tuple[dict[tuple[str, str], np.ndarray], np.ndarray]:
    """第13-1表 → (続き柄, 粗い家族類型) → (2, 21, 4)。2 つ目は一般世帯人員の男女 × 年齢 21(配偶・類型の総数)。"""
    types = {"111": "111_うち夫婦のみの世帯", "11": "11_核家族世帯", "12": "12_核家族以外の世帯",
             "2": "2_非親族を含む世帯", "3": "3_単独世帯"}
    ages = [lab for lab in sorted({k[3] for k in d.table}) if re.match(r"^(0[1-9]|1\d|2[01])_", lab)]
    ages = sorted(ages)
    rels = [it for it in d.items if re.match(r"^(0[1-9]|1[0-2])_", it)]
    out: dict[tuple[str, str], np.ndarray] = {}
    for tk, tlab in types.items():  # 逐次: 類型 5 × 続き柄 12
        for rel in rels:
            j = d.item(rel)
            arr = np.zeros((2, len(ages), 4))
            for si, sx in enumerate(_SEX):
                for mi, mr in enumerate(_MAR4):
                    for ai, ag in enumerate(ages):
                        v = d.table.get((mr, sx, tlab, ag))
                        arr[si, ai, mi] = 0.0 if v is None or np.isnan(v[j]) else v[j]
            out[(_num_prefix(rel), tk)] = arr
    tot = np.zeros((2, len(ages)))
    j0 = d.item("00_総数")
    for si, sx in enumerate(_SEX):
        for ai, ag in enumerate(ages):
            v = d.table.get(("0_総数", sx, "0_総数", ag))
            tot[si, ai] = 0.0 if v is None else np.nan_to_num(v[j0])
    if len(ages) != 21:
        raise ValueError(f"第13-1表の年齢の階級が 21 でない({len(ages)})")
    return out, tot


def _b13_marital15(d: S.Derived) -> np.ndarray:
    """第13-1表 → 15 歳以上の一般世帯人員の男女 × 配偶関係 3 区分((2, 3)・続き柄と類型は総数)。"""
    labs = sorted({k[3] for k in d.table if re.match(r"^(0[1-9]|1\d|2[01])_", k[3])})
    j = d.item("00_総数")
    out = np.zeros((2, 3))
    for si, sx in enumerate(_SEX):  # 逐次: 男女 2 × 配偶 4 × 年齢 18
        for mi, mr in enumerate(_MAR4):
            for lab in labs[3:]:  # 15 歳以上の階級
                v = d.table.get((mr, sx, "0_総数", lab))
                out[si, MARITAL3_OF4[mi]] += 0.0 if v is None else float(np.nan_to_num(v[j]))
    return out


def load_ward(guard: S.W21Guard, raw_age16_2020: np.ndarray, raw_marital3_2020: np.ndarray,
              raw_group_2020: np.ndarray) -> Ward2025:
    """区の雛形(2025)と不詳を割り振る比。``raw_*`` は町丁目の表の区の行(2020 の原数値・既知の分類)。"""
    b02w = S.read_derived(guard, "c25w_b02")
    shape = np.stack([_single_year(b02w.get("0_国籍総数", sx), b02w.items) for sx in _SEX])
    jp = np.stack([_single_year(b02w.get("1_うち日本人", sx), b02w.items) for sx in _SEX])
    foreign = np.clip(shape - jp, 0.0, None)
    foreign_share = np.divide(foreign, shape, out=np.zeros_like(shape), where=shape > 0)
    pop_total = float(b02w.get("0_国籍総数", "0_総数")[b02w.item("000_総数")])
    age16 = _cls_sum(shape, AGE16_EDGES).T  # (16, 2)
    pop15 = shape[:, 15:].sum(axis=1)

    b10w = S.read_derived(guard, "c25w_b10")
    sizes = [f"{i}_世帯人員が{i}人" for i in range(1, 7)] + ["7_世帯人員が7人以上"]
    hh = np.zeros((len(FAMILY_TYPES), SIZES))
    for ti, t in enumerate(FAMILY_TYPES):
        lab = next(it for it in b10w.items if _num_prefix(it) == t)
        for si, sz in enumerate(sizes):
            hh[ti, si] = np.nan_to_num(b10w.get(sz)[b10w.item(lab)])
    hh_total = float(b10w.get("0_総数")[b10w.item("0_総数")])

    b12 = S.read_derived(guard, "c25_b12")
    head_ages = sorted({k[2] for k in b12.table if re.match(r"^(0[2-9]|1[0-6])_", k[2])})
    if len(head_ages) != AGE_HEAD_EDGES.size:
        raise ValueError(f"第12-1表の世帯主の年齢の階級が {AGE_HEAD_EDGES.size} でない({len(head_ages)})")
    head: dict[str, np.ndarray] = {}
    for t in FAMILY_TYPES:
        lab = next(it for it in b12.items if _num_prefix(it) == t)
        j = b12.item(lab)
        arr = np.zeros((2, len(head_ages), 4))
        for si, sx in enumerate(_SEX):
            for mi, mr in enumerate(_MAR4):
                for ai, ag in enumerate(head_ages):
                    v = b12.table.get((sx, mr, ag))
                    arr[si, ai, mi] = 0.0 if v is None or np.isnan(v[j]) else v[j]
        head[t] = arr

    b13w = S.read_derived_merged(guard, ("c25w_b13_m", "c25w_b13_f"))
    members, gh_sex_age21 = _b13_members(b13w)
    b13t = S.read_derived(guard, "c25w_b13")
    gh_persons = float(b13t.get("0_総数", "0_総数", "0_総数", "00_総数")[b13t.item("00_総数")])
    if abs(gh_sex_age21.sum() - gh_persons) > 0.5:
        raise ValueError(f"第13-1表の男女の和が総数と違う({gh_sex_age21.sum()} != {gh_persons})")
    marital = _b13_marital15(b13w).T  # (3, 2)
    marital = marital / marital.sum(axis=0, keepdims=True) * pop15[None, :]
    inst21 = np.clip(_cls_sum(shape, AGE21_EDGES) - gh_sex_age21, 0.0, None)
    inst = expand_single_year(inst21, AGE21_EDGES, shape.mean(axis=0))

    b19 = S.read_derived(guard, "c25_b19")
    wives = [it for it in b19.items if re.match(r"^\d{2}_\d+歳", it) and not it.startswith("00")]
    couples = np.zeros((N_AGE, N_AGE))
    hus_keys = [k for k in b19.table if re.match(r"^\d{2}_\d+歳", k[0]) and not k[0].startswith("00")]
    for (hk,) in hus_keys:  # 逐次: 夫の年齢 71 × 妻の年齢 71
        ha = int(re.match(r"^\d{2}_(\d+)歳", hk).group(1))
        vals = b19.get(hk)
        row = np.zeros(N_AGE)
        for wl in wives:
            wa = int(re.match(r"^\d{2}_(\d+)歳", wl).group(1))
            v = vals[b19.item(wl)]
            v = 0.0 if np.isnan(v) else v
            if "以上" in wl:
                row[wa:] += v * shape[1, wa:] / max(shape[1, wa:].sum(), 1e-12)
            else:
                row[wa] += v
        if "以上" in hk:
            w = shape[0, ha:] / max(shape[0, ha:].sum(), 1e-12)
            couples[ha:, :] += w[:, None] * row[None, :]
        else:
            couples[ha, :] += row

    # 町丁目の不詳を割り振る比(区の 2020 の補完値 − 原数値の既知)
    b02_20 = S.read_derived(guard, "c20w_b02")
    shape20 = np.stack([_single_year(b02_20.get("0_国籍総数", sx), b02_20.items) for sx in _SEX])
    pop2020 = float(b02_20.get("0_国籍総数", "0_総数")[b02_20.item("000_総数")])
    imp16 = _cls_sum(shape20, AGE16_EDGES)  # (2, 16)
    unk_age = np.clip(imp16 - raw_age16_2020.T, 0.0, None)
    unk_age = _normalize_rows(unk_age, fallback=imp16)

    b13_20 = S.read_derived_merged(guard, ("c20w_b13_m", "c20w_b13_f"))
    imp_mar = _b13_marital15(b13_20)  # (2, 3)
    unk_mar = np.clip(imp_mar - raw_marital3_2020.T, 0.0, None)
    unk_mar = _normalize_rows(unk_mar, fallback=imp_mar)

    b10_20 = S.read_derived(guard, "c20w_b10")
    imp_g = np.zeros(len(GROUPS))
    for t in FAMILY_TYPES:
        lab = next(it for it in b10_20.items if _num_prefix(it) == t)
        imp_g[GROUPS.index(GROUP_OF_TYPE[t])] += np.nan_to_num(b10_20.get("0_総数")[b10_20.item(lab)])
    unk_g = np.clip(imp_g - raw_group_2020, 0.0, None)
    unk_g = unk_g / unk_g.sum() if unk_g.sum() > 0 else imp_g / imp_g.sum()

    return Ward2025(
        shape=shape, foreign_share=foreign_share, pop_total=pop_total, age16_sex=age16, pop15_by_sex=pop15,
        marital3_sex=marital, hh_type_size=hh, hh_total=hh_total, gh_persons=gh_persons, head=head,
        members=members, couples=couples, inst_sex_age=inst, unknown_age16=unk_age, unknown_marital3=unk_mar,
        unknown_group=unk_g, pop2020=pop2020, foreign_total=float(foreign.sum()),
    )


def _normalize_rows(x: np.ndarray, *, fallback: np.ndarray) -> np.ndarray:
    out = np.zeros_like(x, dtype=np.float64)
    for i in range(x.shape[0]):  # 逐次: 男女 2
        s = x[i].sum()
        out[i] = x[i] / s if s > 0 else fallback[i] / max(fallback[i].sum(), 1e-12)
    return out


# ------------------------------------------------------------------------------------------ 町丁目(2020)
@dataclass(frozen=True)
class ChomeTables:
    """町丁目(80)の 2020 の表。不詳は割り振り済み。``unknown`` は割り振った人数・世帯数(町丁目ごと)。"""

    keys: tuple[str, ...]
    jinko: np.ndarray            # (80,) 人口総数
    age16_sex: np.ndarray        # (80, 16, 2)
    marital3_sex: np.ndarray     # (80, 3, 2) 15 歳以上
    hh_size: np.ndarray          # (80, 7)
    hh_group: np.ndarray         # (80, 6)
    gh_persons: np.ndarray       # (80,) 一般世帯人員
    foreign: np.ndarray          # (80,) 外国人(原数値)
    tenure: np.ndarray           # (80, 6) 持ち家・公営等・民営借家・給与住宅・間借り・住宅以外
    building: np.ndarray         # (80, 8) 一戸建・長屋建・共同(1-2)・(3-5)・(6-10)・(11+)・その他・分類なし
    ward_raw_age16: np.ndarray   # (16, 2) 区の行(既知)
    ward_raw_marital3: np.ndarray  # (3, 2)
    ward_raw_group: np.ndarray   # (6,)
    ward_jinko: float
    ward_hh: float
    ward_15p: float
    ward_foreign: float
    unknown: dict[str, np.ndarray] = field(default_factory=dict)


TENURE: Final[tuple[str, ...]] = ("owned", "public_rent", "private_rent", "company_housing", "room_rent",
                                  "non_dwelling")
BUILDING: Final[tuple[str, ...]] = ("detached", "row_house", "apartment_1_2", "apartment_3_5", "apartment_6_10",
                                    "apartment_11plus", "other", "")


def load_chome(guard: S.W21Guard, keys: tuple[str, ...]) -> tuple[ChomeTables, dict[str, np.ndarray]]:
    """町丁目の表を読み、年齢・配偶関係・家族類型の不詳は**まだ割り振らない**(区の比が要るので 2 段で)。

    返り値の 2 つ目は割り振り前の不詳(年齢 (80, 2)・配偶 (80, 2)・類型 (80,))。
    """
    n = len(keys)
    sexv = S.read_estat_json(guard, "sa_t01")
    agev = S.read_estat_json(guard, "sa_t03")
    jinko = np.array([sexv.get((W16.CENSUS_SEX_CATS["total"], k), 0) for k in keys], dtype=np.float64)
    age = np.zeros((n, 16, 2))
    for si, cats in enumerate((W16.CENSUS_AGE_CATS_MALE, W16.CENSUS_AGE_CATS_FEMALE)):
        for ai, c in enumerate(cats):
            age[:, ai, si] = [agev.get((c, k), 0) for k in keys]
    sex_tot = np.stack([[agev.get((W16.CENSUS_AGE_SEX_TOTAL_CATS[si], k), 0) for k in keys] for si in range(2)], 1)
    unk_age = np.clip(sex_tot - age.sum(axis=1), 0.0, None)
    ward_age = np.array([[agev.get((c, W16.WARD_AREA), 0) for c in cats]
                         for cats in (W16.CENSUS_AGE_CATS_MALE, W16.CENSUS_AGE_CATS_FEMALE)], dtype=np.float64).T

    t04 = S.read_small_area(guard, "sa_t04", keys)
    mar = np.zeros((n, 3, 2))
    labs4 = ("未婚", "有配偶", "死別・離別")
    for si, sx in enumerate(("男", "女")):
        for mi, lab in enumerate(labs4):
            mar[:, mi, si] = np.nan_to_num(t04.col(lab, sx))
    unk_mar = np.stack([np.nan_to_num(t04.col("配偶関係「不詳」", sx)) for sx in ("男", "女")], 1)
    ward_mar = np.array([[t04.ward_col(lab, sx) for sx in ("男", "女")] for lab in labs4])
    ward_15p = t04.ward_col("総数")

    t52 = S.read_small_area(guard, "sa_t05_2", keys)
    size_labs = [f"世帯人員が{i}人" for i in range(1, 7)] + ["世帯人員が7人以上"]
    hh_size = np.stack([np.nan_to_num(t52.col(lab)) for lab in size_labs], 1)
    ward_hh = t52.ward_col("総数")

    t61 = S.read_small_area(guard, "sa_t06_1", keys)
    nuc = np.nan_to_num(t61.col("核家族世帯"))
    cpl = np.nan_to_num(t61.col("うち夫婦のみの世帯"))
    cch = np.nan_to_num(t61.col("うち夫婦と子供から成る世帯"))
    grp = np.stack([np.nan_to_num(t61.col("単独世帯")), cpl, cch, np.clip(nuc - cpl - cch, 0, None),
                    np.nan_to_num(t61.col("核家族以外の世帯")), np.nan_to_num(t61.col("非親族を含む世帯"))], 1)
    unk_grp = np.nan_to_num(t61.col("世帯の家族類型「不詳」"))
    wn = t61.ward_col("核家族世帯")
    wc, wcc = t61.ward_col("うち夫婦のみの世帯"), t61.ward_col("うち夫婦と子供から成る世帯")
    ward_grp = np.array([t61.ward_col("単独世帯"), wc, wcc, wn - wc - wcc, t61.ward_col("核家族以外の世帯"),
                         t61.ward_col("非親族を含む世帯")])

    t62 = S.read_small_area(guard, "sa_t06_2", keys)
    ghp = np.nan_to_num(t62.col("総数"))

    t02 = S.read_small_area(guard, "sa_t02", keys)
    fcol = [j for j, lab in enumerate(t02.labels) if lab == "-"]
    foreign = np.nan_to_num(t02.values["総数"][:, fcol[0]])
    ward_foreign = float(t02.ward["総数"][fcol[0]])

    t71 = S.read_small_area(guard, "sa_t07_1", keys)
    ten_labs = ("持ち家", "公営・都市再生機構・公社の借家", "民営の借家", "給与住宅", "間借り", "住宅以外に住む一般世帯")
    ten = np.stack([np.nan_to_num(t71.col(lab)) for lab in ten_labs], 1)
    unk_ten = np.nan_to_num(t71.col("住居の種類「不詳」"))
    ten = _mar_fill(ten, unk_ten)

    t81 = S.read_small_area(guard, "sa_t08_1", keys)
    apt = [lab for lab in t81.labels if lab.startswith("共同住宅（")]  # 1・2 階建 / 3〜5 / 6〜10 / 11 階建以上(表の順)
    if len(apt) != 4:
        raise ValueError(f"第8-1表の共同住宅の階の区分が 4 でない({len(apt)})")
    b_labs = ("一戸建", "長屋建", *apt, "その他")
    bld = np.stack([np.nan_to_num(t81.col(lab)) for lab in b_labs], 1)
    rest = np.clip(np.nan_to_num(t81.col("総数")) - bld.sum(axis=1), 0.0, None)
    bld = np.concatenate([bld, rest[:, None]], 1)

    ct = ChomeTables(
        keys=keys, jinko=jinko, age16_sex=age, marital3_sex=mar, hh_size=hh_size, hh_group=grp, gh_persons=ghp,
        foreign=foreign, tenure=ten, building=bld, ward_raw_age16=ward_age, ward_raw_marital3=ward_mar,
        ward_raw_group=ward_grp, ward_jinko=float(sexv.get((W16.CENSUS_SEX_CATS["total"], W16.WARD_AREA), 0)),
        ward_hh=ward_hh, ward_15p=ward_15p, ward_foreign=ward_foreign,
        unknown={"tenure": unk_ten},
    )
    return ct, {"age": unk_age, "marital": unk_mar, "group": unk_grp}


def _mar_fill(x: np.ndarray, unk: np.ndarray) -> np.ndarray:
    """町丁目の既知の比で不詳を割り振る(MAR)。既知が 0 の町丁目は割り振らない。"""
    s = x.sum(axis=1, keepdims=True)
    share = np.divide(x, s, out=np.zeros_like(x), where=s > 0)
    return x + share * unk[:, None]


def fill_unknown(ct: ChomeTables, unk: Mapping[str, np.ndarray], ward: Ward2025) -> ChomeTables:
    """年齢・配偶関係・家族類型の不詳を区の比(2020 の補完値 − 原数値)で割り振った表を返す。"""
    age = ct.age16_sex + unk["age"][:, None, :] * ward.unknown_age16.T[None, :, :]
    mar = ct.marital3_sex + unk["marital"][:, None, :] * ward.unknown_marital3.T[None, :, :]
    grp = ct.hh_group + unk["group"][:, None] * ward.unknown_group[None, :]
    u = dict(ct.unknown)
    u.update({"age": unk["age"].sum(axis=1), "marital": unk["marital"].sum(axis=1), "family_type": unk["group"]})
    return ChomeTables(**{**ct.__dict__, "age16_sex": age, "marital3_sex": mar, "hh_group": grp, "unknown": u})


# ------------------------------------------------------------------------------------------ 2020 の形 × 2025 の総数
def rake_chome_to_ward(x: np.ndarray, row_total: np.ndarray, col_total: np.ndarray) -> tuple[np.ndarray, float]:
    """町丁目 × 分類(2020 の形)を、行=町丁目の総数・列=区の分類ごとの総数(和は行に合わせる)へ IPF で合わせる。"""
    col = np.asarray(col_total, dtype=np.float64)
    col = col * (row_total.sum() / col.sum()) if col.sum() > 0 else col
    res = F.ipf(np.clip(x, 0.0, None), row_total, col)
    return res.table, float(res.max_residual)


@dataclass(frozen=True)
class Targets:
    """舞台の目標(町丁目は被覆率 > 0 の分だけ・実数)。"""

    stage_idx: np.ndarray        # (C,) 町丁目の索引(80 の中)
    coverage: np.ndarray         # (C,)
    persons: np.ndarray          # (C,) 人口(2025 換算 × 被覆率)
    age16_sex: np.ndarray        # (C, 16, 2)
    marital3_sex: np.ndarray     # (C, 3, 2)
    hh_size: np.ndarray          # (C, 7)
    hh_group: np.ndarray         # (C, 6)
    institution: np.ndarray      # (C,) 施設等の世帯の人
    foreign: np.ndarray          # (C,)
    tenure: np.ndarray           # (C, 6)
    building: np.ndarray         # (C, 8)
    ratios: dict[str, float]
    ipf_residual: dict[str, float]


def make_targets(ct: ChomeTables, ward: Ward2025, coverage: np.ndarray) -> Targets:
    """2020 の町丁目の形 × 2025 の区の総数 → 舞台の目標。"""
    r_pop = ward.pop_total / ct.ward_jinko
    r_hh = ward.hh_total / ct.ward_hh
    res: dict[str, float] = {}
    rows = ct.jinko * r_pop
    a, res["age16_sex"] = rake_chome_to_ward(ct.age16_sex.reshape(len(ct.keys), -1), rows,
                                             ward.age16_sex.reshape(-1))
    # 〔検収 L4〕配偶関係の行の総数=年齢の目標の 15 歳以上(同じ町丁目の同じ人数=区の平均の比で直す形はやめた)
    m_rows = a.reshape(len(ct.keys), 16, 2)[:, 3:, :].sum(axis=(1, 2))
    m, res["marital3_sex"] = rake_chome_to_ward(ct.marital3_sex.reshape(len(ct.keys), -1), m_rows,
                                                ward.marital3_sex.reshape(-1))
    h_rows = ct.hh_size.sum(axis=1) * r_hh
    sz, res["hh_size"] = rake_chome_to_ward(ct.hh_size, h_rows, ward.hh_type_size.sum(axis=0))
    g_ward = np.zeros(len(GROUPS))
    for ti, t in enumerate(FAMILY_TYPES):
        g_ward[GROUPS.index(GROUP_OF_TYPE[t])] += ward.hh_type_size[ti].sum()
    g, res["hh_group"] = rake_chome_to_ward(ct.hh_group, h_rows, g_ward)
    inst20 = np.clip(ct.jinko - ct.gh_persons, 0.0, None)
    r_inst = (ward.pop_total - ward.gh_persons) / max(inst20.sum(), 1.0)
    r_for = ward.foreign_total / max(ct.ward_foreign, 1.0)
    idx = np.flatnonzero(coverage > 0)
    cov = coverage[idx]
    return Targets(
        stage_idx=idx, coverage=cov, persons=rows[idx] * cov,
        age16_sex=a.reshape(len(ct.keys), 16, 2)[idx] * cov[:, None, None],
        marital3_sex=m.reshape(len(ct.keys), 3, 2)[idx] * cov[:, None, None],
        hh_size=sz[idx] * cov[:, None], hh_group=g[idx] * cov[:, None],
        institution=inst20[idx] * r_inst * cov, foreign=ct.foreign[idx] * r_for * cov,
        tenure=ct.tenure[idx] * r_hh * cov[:, None], building=ct.building[idx] * r_hh * cov[:, None],
        ratios={"r_pop": r_pop, "r_hh": r_hh, "r_institution": float(r_inst), "r_foreign": r_for},
        ipf_residual=res,
    )
