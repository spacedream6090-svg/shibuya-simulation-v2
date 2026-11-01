"""W21 段 2「世帯と人」(答申 R-116 §3-2 の手順 3〜7・標本なしの組み立て+焼きなましの詰め)。

手順(手順 1・2 の表は ``w21_tables``)
3. **整数化**: 町丁目ごとに、家族類型の区分(6)× 世帯人員(7)を区の 2025 の結合(第10表の補完値)を種にした IPF で合わせ、
   区分を細かい家族類型(16)へ区の比で分け、``largest_remainder`` で整数にする。
4. **世帯員の組み立て(標本なし・条件付き)**: 家族類型と世帯人員から続き柄の並びを決め(:data:`COMPOSITION`)、
   世帯主(第12-1表=男女 × 年齢 × 配偶関係 | 家族類型)→ 配偶者(第19-1表=夫と妻の年齢 各歳)→ 子・親・他の親族・
   非親族(第13-1表の補完値=男女 × 年齢 × 配偶関係 | 続き柄 × 粗い家族類型)の順に引く。年齢は「年齢の窓」
   (:func:`windows`=子は若い方の親より 15 歳以上若い 等)で切った分布から引く。
5. **詰め**: 町丁目 × 年齢 16 階級 × 男女と町丁目 × 配偶関係 3 区分 × 男女(15 歳以上)の目標との誤差の絶対値の和を、
   同じ家族類型・同じ世帯人員の世帯どうしで町丁目を入れ替える(=世帯員を丸ごと入れ替える)焼きなましで詰める
   (腕 ``anneal``=on/off・既定 on・比べる腕は off)。
6. **建物への配置**: 住宅の建て方(第8-1表)の階の区分ごとに、町丁目の住居系建物の床面積(W16#3 と同じ)で配る。
7. **外国人**: 町丁目の外国人(第2表)× 2025 の補完値の総数。年齢と性別の重みは 2025 の補完値の「国籍総数 − 日本人」。
   世帯ごとに選ぶ。国籍は空欄(住民基本台帳の後)。

決定性: 乱数は ``core.rng`` の Philox だけ(ドメイン ``w21.<手順>``・鍵は世帯=(町丁目の鍵, 通し番号)・世帯員=
(町丁目の鍵, 通し番号, 世帯員の番号)・詰めは提案の番号)。並べ方は鍵の辞書順。

近似の宣言は ``w21_build.W21_EXPEDIENTS``(つなぎの台帳)。

逐次ループ宣言(P4): 町丁目の数ぶん(42)・家族類型 × 続き柄の組の数ぶん(≤ 60)・**詰めの提案の数ぶん**(``anneal_iter``・
既定 400,000=体の数に比例しない固定の回数・1 回あたり 38 要素のベクトルの演算)。
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from types import MappingProxyType
from typing import Final, Mapping, Sequence

import numpy as np

from shibuya.core.rng import k19_counter_array, philox_array, unit_float

from . import fitting as F
from . import w21_tables as T

__all__ = [
    "SLOT_NAMES",
    "COMPOSITION",
    "HouseholdDraw",
    "AnnealParams",
    "household_cells",
    "make_households",
    "compose_members",
    "draw_members",
    "anneal",
    "anneal_vectors",
    "assign_categories",
    "choose_foreign",
    "windows",
]

# 続き柄の枠(人の列 ``relation`` の語は census の番号=01 世帯主・02 配偶者・03 子・05 父母 …)
HEAD, SPOUSE, CHILD, PARENT, OTHER_REL, SIBLING, NON_REL = range(7)
SLOT_NAMES: Final[tuple[str, ...]] = ("head", "spouse", "child", "parent", "other_relative", "sibling",
                                      "non_relative")
#: 家族類型 → (決まった枠, 余りを埋める枠)。世帯員 = 世帯主 + 決まった枠[: 人員 − 1] + 余りの枠 × 残り。
COMPOSITION: Final[Mapping[str, tuple[tuple[int, ...], int | None]]] = MappingProxyType({
    "3": ((), None),
    "111": ((SPOUSE,), OTHER_REL),
    "112": ((SPOUSE, CHILD), CHILD),
    "113": ((CHILD,), CHILD),
    "114": ((CHILD,), CHILD),
    "1201": ((SPOUSE, PARENT, PARENT), OTHER_REL),
    "1202": ((SPOUSE, PARENT), OTHER_REL),
    "1203": ((SPOUSE, PARENT, PARENT, CHILD), CHILD),
    "1204": ((SPOUSE, PARENT, CHILD), CHILD),
    "1205": ((SPOUSE, OTHER_REL), OTHER_REL),
    "1206": ((SPOUSE, OTHER_REL, CHILD), CHILD),
    "1207": ((SPOUSE, PARENT, OTHER_REL), OTHER_REL),
    "1208": ((SPOUSE, PARENT, OTHER_REL, CHILD), CHILD),
    "1209": ((SIBLING,), SIBLING),
    "1210": ((OTHER_REL,), OTHER_REL),
    "2": ((NON_REL,), NON_REL),
})
#: 他の親族の枠で引く続き柄(第13-1表の番号)と、非親族の枠の続き柄。
OTHER_REL_CODES: Final[tuple[str, ...]] = ("04", "07", "08", "09", "10")
NON_REL_CODES: Final[tuple[str, ...]] = ("11", "12")
#: 世帯主の性を決める家族類型(ひとり親と子は親を世帯主にする=宣言)。
HEAD_SEX_FIXED: Final[Mapping[str, int]] = MappingProxyType({"113": 0, "114": 1})
#: 世帯主が有配偶に限られる家族類型(夫婦のいる類型)。
COUPLE_TYPES: Final[frozenset[str]] = frozenset({"111", "112", *(f"12{i:02d}" for i in range(1, 9))})
#: 子の年齢の窓: 若い方の親より ``CHILD_GAP_MIN`` 歳以上若い・母より ``MOTHER_GAP_MAX`` 歳以内・父より
#: ``FATHER_GAP_MAX`` 歳以内(自前の表・未リサーチ)。
CHILD_GAP_MIN: Final[int] = 15
MOTHER_GAP_MAX: Final[int] = 50
FATHER_GAP_MAX: Final[int] = 65
#: 世帯主の父母は世帯主より 15〜50 歳上・孫は 30 歳以上下・祖父母は 30 歳以上上・兄弟姉妹は ±20 歳(同)。
PARENT_GAP: Final[tuple[int, int]] = (15, 50)
#: 孫・祖父母と世帯主の差の下限=親子の最小の差 × 2(30 歳)〔検収 L2〕。
GRANDCHILD_GAP_MIN: Final[int] = 2 * CHILD_GAP_MIN
GRANDPARENT_GAP_MIN: Final[int] = 2 * CHILD_GAP_MIN
SIBLING_GAP_MAX: Final[int] = 20
MAX_SIZE: Final[int] = 7
#: 詰めの誤差のベクトル: 年齢 16 階級 × 男女(32)+配偶関係 3 区分 × 男女(15 歳以上・6)。
N_VEC: Final[int] = 16 * 2 + 3 * 2


@dataclass(frozen=True)
class AnnealParams:
    """焼きなましのパラメータ(自前の値・感度試験の前=宣言)。"""

    enabled: bool = True
    n_iter: int = 400_000
    t0: float = 2.0
    t1: float = 0.02


# ------------------------------------------------------------------------------------------ 手順 3
def household_cells(tg: T.Targets, ward: T.Ward2025) -> tuple[np.ndarray, np.ndarray, dict[str, float]]:
    """町丁目 × 家族類型 16 × 世帯人員 7 の世帯数(整数)と実数の表。

    単独世帯の数は家族類型の表を正とし、世帯人員 1 人の列をそれに合わせる(2 つの表を別々に 2025 へ直したので
    わずかに違う)。区分 → 細かい類型は区の 2025 の比(第10表の補完値)で分ける。
    """
    C = tg.stage_idx.size
    nt = len(T.FAMILY_TYPES)
    g_of_t = np.array([T.GROUPS.index(T.GROUP_OF_TYPE[t]) for t in T.FAMILY_TYPES])
    seed_g = np.zeros((len(T.GROUPS), T.SIZES))
    np.add.at(seed_g, g_of_t, ward.hh_type_size)
    share_t = np.divide(ward.hh_type_size, seed_g[g_of_t], out=np.zeros_like(ward.hh_type_size),
                        where=seed_g[g_of_t] > 0)
    real = np.zeros((C, nt, T.SIZES))
    max_res = 0.0
    totals = tg.hh_size.sum(axis=1)
    H_total = int(round(float(totals.sum())))
    H_c = F.largest_remainder(totals, H_total)
    ints = np.zeros((C, nt, T.SIZES), dtype=np.int64)
    for c in range(C):  # 逐次: 町丁目の数ぶん
        rows = tg.hh_group[c].copy()
        cols = tg.hh_size[c].copy()
        total = rows.sum()
        single = rows[T.GROUPS.index("single")]
        rest = cols[1:].sum()
        if rest > 0:
            cols[1:] = cols[1:] * ((total - single) / rest)
        cols[0] = single
        r = F.ipf(seed_g, rows, cols)
        max_res = max(max_res, float(r.max_residual))
        real[c] = r.table[g_of_t] * share_t
        ints[c] = F.largest_remainder(real[c].ravel(), int(H_c[c])).reshape(nt, T.SIZES)
    return ints, real, {"households": float(H_total), "ipf_max_residual": max_res}


@dataclass
class HouseholdDraw:
    """世帯と世帯員(SoA)。``hh_*`` は世帯・``m_*`` は世帯員。``m_hh`` は世帯の行の番号。"""

    hh_chome: np.ndarray     # 町丁目(舞台の中の番号)
    hh_type: np.ndarray      # 家族類型(FAMILY_TYPES の番号)・施設等は −1
    hh_size: np.ndarray
    hh_serial: np.ndarray    # 町丁目の中の通し番号(鍵)
    hh_chome_key: np.ndarray  # 町丁目の鍵(整数=11 桁)
    m_hh: np.ndarray
    m_no: np.ndarray
    m_slot: np.ndarray
    m_rel: np.ndarray        # 続き柄の番号(文字列 "01" …・施設等は "inst")
    m_sex: np.ndarray
    m_age: np.ndarray
    m_marital: np.ndarray    # 0..3・15 歳未満は −1
    fallbacks: dict[str, int]

    @property
    def n_households(self) -> int:
        return int(self.hh_type.size)


def make_households(ints: np.ndarray, inst: np.ndarray, chome_keys: Sequence[int]) -> HouseholdDraw:
    """整数の表 → 世帯の行(町丁目 → 家族類型 → 世帯人員の順・通し番号は町丁目の中の順)+施設等の人(1 人 1 世帯)。"""
    C, nt, ns = ints.shape
    cnt = ints.reshape(C, -1)
    hc = np.repeat(np.repeat(np.arange(C), nt * ns), cnt.ravel())
    cell = np.repeat(np.tile(np.arange(nt * ns), C), cnt.ravel())
    ht = cell // ns
    hs = cell % ns + 1
    ic = np.repeat(np.arange(C), np.asarray(inst, dtype=np.int64))
    hc = np.concatenate([hc, ic])
    ht = np.concatenate([ht, np.full(ic.size, -1)])
    hs = np.concatenate([hs, np.ones(ic.size, dtype=np.int64)])
    order = np.lexsort((np.arange(hc.size), hc))
    hc, ht, hs = hc[order], ht[order], hs[order]
    serial = np.arange(hc.size) - np.searchsorted(hc, hc, side="left")
    keys = np.asarray(chome_keys, dtype=np.int64)[hc]
    empty = np.zeros(0, dtype=np.int64)
    return HouseholdDraw(hc, ht, hs, serial, keys, empty, empty, empty, np.zeros(0, dtype=object), empty, empty,
                         empty, {})


# ------------------------------------------------------------------------------------------ 手順 4
def _slot_table() -> np.ndarray:
    out = np.full((len(T.FAMILY_TYPES) + 1, MAX_SIZE + 1, MAX_SIZE), -1, dtype=np.int64)
    for ti, t in enumerate(T.FAMILY_TYPES):
        fixed, fill = COMPOSITION[t]
        for s in range(1, MAX_SIZE + 1):
            slots = [HEAD, *fixed[: s - 1]]
            while len(slots) < s:
                slots.append(fill if fill is not None else OTHER_REL)
            out[ti, s, :s] = slots
    out[-1, 1, 0] = HEAD  # 施設等(−1 は最後の行)
    return out


_SLOTS = _slot_table()
_SLOTS.flags.writeable = False


def compose_members(hd: HouseholdDraw) -> HouseholdDraw:
    """世帯の行 → 世帯員の行(世帯の順・世帯員の番号の順)と枠。"""
    m_hh = np.repeat(np.arange(hd.n_households), hd.hh_size)
    starts = np.repeat(np.cumsum(hd.hh_size) - hd.hh_size, hd.hh_size)
    m_no = np.arange(m_hh.size) - starts
    t = hd.hh_type[m_hh]
    t = np.where(t < 0, len(T.FAMILY_TYPES), t)
    m_slot = _SLOTS[t, hd.hh_size[m_hh], m_no]
    n = m_hh.size
    hd.m_hh, hd.m_no, hd.m_slot = m_hh, m_no, m_slot
    hd.m_rel = np.full(n, "", dtype=object)
    hd.m_sex = np.full(n, -1, dtype=np.int64)
    hd.m_age = np.full(n, -1, dtype=np.int64)
    hd.m_marital = np.full(n, -1, dtype=np.int64)
    return hd


def _uniform(seed: int | str, domain: str, keys: np.ndarray, sub: np.ndarray, words: int = 1) -> np.ndarray:
    """(町丁目の鍵, 通し番号, 枝)→ [0,1) の一様乱数((n, words))。"""
    raw = philox_array(seed, domain, k19_counter_array(keys[:, 0], keys[:, 1], sub), words=words)
    return unit_float(raw)


def windows(slot: np.ndarray, rel: np.ndarray, head_age: np.ndarray, spouse_age: np.ndarray,
            mother_age: np.ndarray, father_age: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """世帯員の年齢の窓 [lo, hi](世帯主・配偶者・父母の年齢から)。−1 は「その親がいない」。"""
    lo = np.zeros(slot.size, dtype=np.int64)
    hi = np.full(slot.size, T.MAX_AGE, dtype=np.int64)
    ch = slot == CHILD
    youngest = np.where(spouse_age >= 0, np.minimum(head_age, spouse_age), head_age)
    hi = np.where(ch, youngest - CHILD_GAP_MIN, hi)
    lo_m = np.where(mother_age >= 0, mother_age - MOTHER_GAP_MAX, 0)
    lo_f = np.where(father_age >= 0, father_age - FATHER_GAP_MAX, 0)
    lo = np.where(ch, np.maximum(0, np.maximum(lo_m, lo_f)), lo)
    pa = slot == PARENT
    lo = np.where(pa, head_age + PARENT_GAP[0], lo)
    hi = np.where(pa, head_age + PARENT_GAP[1], hi)
    sib = (slot == SIBLING) | (rel == "09")
    lo = np.where(sib, head_age - SIBLING_GAP_MAX, lo)
    hi = np.where(sib, head_age + SIBLING_GAP_MAX, hi)
    gc = rel == "07"
    hi = np.where(gc, head_age - GRANDCHILD_GAP_MIN, hi)
    gp = rel == "08"
    lo = np.where(gp, head_age + GRANDPARENT_GAP_MIN, lo)
    csp = rel == "04"
    lo = np.where(csp, 15, lo)
    hi = np.where(csp, head_age - CHILD_GAP_MIN, hi)
    lo, hi = np.clip(lo, 0, T.MAX_AGE), np.minimum(hi, T.MAX_AGE)
    # 子の窓の下の端(母・父との差の上限)が上の端を越えたら下の端を外す(子が親より 15 歳以上若いのは保つ)
    lo = np.where(ch & (lo > hi), 0, lo)
    return lo, hi


def feasible_other(head_age: np.ndarray) -> np.ndarray:
    """他の親族の続き柄(``OTHER_REL_CODES`` の順)ごとに、世帯主の年齢で窓が空にならないか((n, 5) の真偽)。

    子の配偶者=世帯主 30 歳以上(15 歳以上で世帯主より 15 歳以上若い)・孫=世帯主 30 歳以上・祖父母=世帯主が上限より
    30 歳以上若い・兄弟姉妹と他の親族はいつでも〔検収 L2=窓が空になる続き柄は引かない〕。
    """
    h = np.asarray(head_age, dtype=np.int64)[:, None]
    lim = np.array([15 + CHILD_GAP_MIN, GRANDCHILD_GAP_MIN, -1, -1, -1])[None, :]
    ok = h >= lim
    ok[:, 2] = (h[:, 0] + GRANDPARENT_GAP_MIN) <= T.MAX_AGE
    return ok


def _draw_sex_age(p2: np.ndarray, lo: np.ndarray, hi: np.ndarray, u: np.ndarray,
                  sex_fixed: np.ndarray | None = None) -> tuple[np.ndarray, np.ndarray, int, int]:
    """(男女, 各歳)の分布 ``p2``((2, N_AGE))を窓で切って引く。窓に重みが無ければ窓の中で一様(数を返す)。

    返り値の 4 つ目は窓そのものが空だった人の数(端の年齢を当てた=続き柄の引き直しと世帯主の上限で 0 にする)。
    """
    n = lo.size
    ages = np.arange(T.N_AGE)
    sex_out = np.zeros(n, dtype=np.int64)
    age_out = np.zeros(n, dtype=np.int64)
    fb = 0
    emp = 0
    for a in range(0, n, 20_000):  # 逐次: 2 万行ずつ(記憶の上限)
        b = min(n, a + 20_000)
        m = (ages[None, :] >= lo[a:b, None]) & (ages[None, :] <= hi[a:b, None])
        w = p2[None, :, :] * m[:, None, :]
        if sex_fixed is not None:
            sf = sex_fixed[a:b]
            keep = np.stack([(sf < 0) | (sf == 0), (sf < 0) | (sf == 1)], axis=1)
            w = w * keep[:, :, None]
        w = w.reshape(b - a, -1)
        tot = w.sum(axis=1)
        bad = tot <= 0
        if bad.any():  # 窓の中に重みが無い=窓の中で一様(窓が空なら端の年齢)
            fb += int(bad.sum())
            mm = m[bad].astype(np.float64)
            empty = mm.sum(axis=1) == 0
            emp += int(empty.sum())
            mm[empty, np.clip(lo[a:b][bad][empty], 0, T.MAX_AGE)] = 1.0
            sx = np.zeros((int(bad.sum()), 2))
            if sex_fixed is not None:
                sfb = sex_fixed[a:b][bad]
                sx[:, 0] = (sfb < 0) | (sfb == 0)
                sx[:, 1] = (sfb < 0) | (sfb == 1)
            else:
                sx[:] = 1.0
            w[bad] = (sx[:, :, None] * mm[:, None, :]).reshape(int(bad.sum()), -1)
            tot = w.sum(axis=1)
        cdf = np.cumsum(w, axis=1)
        k = (cdf < (u[a:b] * tot)[:, None]).sum(axis=1)
        k = np.minimum(k, w.shape[1] - 1)
        sex_out[a:b] = k // T.N_AGE
        age_out[a:b] = k % T.N_AGE
    return sex_out, age_out, fb - emp, emp


def _expand_by_sex(tab2: np.ndarray, edges: np.ndarray, shape: np.ndarray) -> np.ndarray:
    """(2, 階級)→(2, N_AGE)。階級の中は男女それぞれの各歳の形で配る。"""
    return np.stack([T.expand_single_year(tab2[s], edges, shape[s]) for s in range(2)])


def _marital_given(table: np.ndarray, sex: np.ndarray, age: np.ndarray, u: np.ndarray) -> np.ndarray:
    """(2, 21, 4) の表から、男女と年齢の階級ごとの配偶関係を引く(15 歳未満は −1)。"""
    cls = T.age_class(age, T.AGE21_EDGES)
    w = table[sex, cls]  # (n, 4)
    tot = w.sum(axis=1)
    w = np.where(tot[:, None] > 0, w, np.array([1.0, 0.0, 0.0, 0.0]))
    tot = w.sum(axis=1)
    k = (np.cumsum(w, axis=1) < (u * tot)[:, None]).sum(axis=1)
    return np.where(age < 15, -1, np.minimum(k, 3))


def draw_members(hd: HouseholdDraw, ward: T.Ward2025, seed: int | str,
                 age_sex_target: np.ndarray | None = None) -> HouseholdDraw:
    """世帯員の続き柄・男女・年齢・配偶関係を引く(世帯主 → 配偶者 → ほかの順)。

    ``age_sex_target``((町丁目, 16, 2))を渡すと、単独世帯の世帯主は最後に町丁目ごとに引く: 町丁目の目標から
    ほかの世帯員と施設等の人の数えを引いた残り(負は 0)の比で(男女 × 年齢 16 階級)の数を最大剰余で決め、階級の中の
    各歳は単独世帯の世帯主の分布(第12-1表)で、配偶関係はその男女 × 年齢の比で引く(:func:`_draw_singles`)。
    """
    n = hd.m_hh.size
    hkey = np.stack([hd.hh_chome_key, hd.hh_serial], axis=1)
    mkey = hkey[hd.m_hh]
    lut = np.array([*T.FAMILY_TYPES, "inst"], dtype=object)
    types = lut[np.where(hd.hh_type >= 0, hd.hh_type, len(T.FAMILY_TYPES))]
    m_type = types[hd.m_hh]
    fb = {"window_no_weight": 0, "window_empty": 0, "spouse_same_age": 0, "composition_truncated": 0}
    shape = ward.shape

    # 世帯主(施設等の人を含む)
    head_rows = np.flatnonzero(hd.m_slot == HEAD)
    u = _uniform(seed, "w21.head", mkey[head_rows], hd.m_no[head_rows], words=2)
    hd.m_rel[head_rows] = "01"
    late_singles = age_sex_target is not None
    for t in [*T.FAMILY_TYPES, "inst"]:  # 逐次: 家族類型の数ぶん
        if late_singles and t == "3":
            continue
        rows = head_rows[m_type[head_rows] == t]
        if rows.size == 0:
            continue
        sel = np.searchsorted(head_rows, rows)
        if t == "inst":
            p2 = ward.inst_sex_age
            mar_tab = ward.members.get(("01", "3"))
        else:
            h = ward.head[t].copy()  # (2, 15, 4)
            if t in COUPLE_TYPES and h[:, :, 1].sum() > 0:
                h[:, :, [0, 2, 3]] = 0.0
            if t in HEAD_SEX_FIXED:
                h[1 - HEAD_SEX_FIXED[t]] = 0.0
            p2 = _expand_by_sex(h.sum(axis=2), T.AGE_HEAD_EDGES, shape)
            p2[:, :15] = 0.0
            mar_tab = None
        lo = np.full(rows.size, 15 if t != "inst" else 0)
        # 父母のいる世帯の世帯主は、父母の窓(世帯主 + 15 歳以上)が上限を越えない年齢まで〔検収 L2〕
        top = T.MAX_AGE - PARENT_GAP[0] if t != "inst" and PARENT in COMPOSITION[t][0] else T.MAX_AGE
        hi = np.full(rows.size, top)
        sx, ag, f, e = _draw_sex_age(p2, lo, hi, u[sel, 0])
        fb["window_no_weight"] += f
        fb["window_empty"] += e
        hd.m_sex[rows], hd.m_age[rows] = sx, ag
        if t == "inst":
            hd.m_marital[rows] = _marital_given(mar_tab, sx, ag, u[sel, 1])
        else:
            cls = T.age_class(ag, T.AGE_HEAD_EDGES)
            w = h[sx, np.clip(cls, 0, None)]
            tot = w.sum(axis=1)
            w = np.where(tot[:, None] > 0, w, np.array([1.0, 0.0, 0.0, 0.0]))
            k = (np.cumsum(w, axis=1) < (u[sel, 1] * w.sum(axis=1))[:, None]).sum(axis=1)
            hd.m_marital[rows] = np.minimum(k, 3)
    head_of = np.full(hd.n_households, -1, dtype=np.int64)
    head_of[hd.m_hh[head_rows]] = head_rows
    head_age = hd.m_age[head_of[hd.m_hh]]
    head_sex = hd.m_sex[head_of[hd.m_hh]]

    # 配偶者(第19-1表=夫の年齢 × 妻の年齢)
    sp = np.flatnonzero(hd.m_slot == SPOUSE)
    if sp.size:
        u = _uniform(seed, "w21.spouse", mkey[sp], hd.m_no[sp])[:, 0]
        hs, ha = head_sex[sp], head_age[sp]
        cond = np.where((hs == 0)[:, None], ward.couples[ha, :], ward.couples[:, ha].T)  # (n, N_AGE)
        cond[:, :15] = 0.0
        tot = cond.sum(axis=1)
        flat = tot <= 0
        if flat.any():  # 表に重みの無い年齢=同じ年齢(数える)
            fb["spouse_same_age"] += int(flat.sum())
            cond[flat] = 0.0
            cond[flat, np.clip(ha[flat], 15, T.MAX_AGE)] = 1.0
            tot = cond.sum(axis=1)
        k = (np.cumsum(cond, axis=1) < (u * tot)[:, None]).sum(axis=1)
        hd.m_age[sp] = np.minimum(k, T.MAX_AGE)
        hd.m_sex[sp] = 1 - hs
        hd.m_rel[sp] = "02"
        hd.m_marital[sp] = 1
    spouse_of = np.full(hd.n_households, -1, dtype=np.int64)
    spouse_of[hd.m_hh[sp]] = sp
    sp_m = spouse_of[hd.m_hh]
    spouse_age = np.where(sp_m >= 0, hd.m_age[np.maximum(sp_m, 0)], -1)
    spouse_sex = np.where(sp_m >= 0, hd.m_sex[np.maximum(sp_m, 0)], -1)
    mother_age = np.where(head_sex == 1, head_age, np.where(spouse_sex == 1, spouse_age, -1))
    father_age = np.where(head_sex == 0, head_age, np.where(spouse_sex == 0, spouse_age, -1))

    # 他の親族の枠は続き柄を先に引く(粗い類型の中の比)
    c_lut = np.array([*(T.COARSE_OF_TYPE[t] for t in T.FAMILY_TYPES), "3"], dtype=object)
    coarse = c_lut[np.where(hd.hh_type >= 0, hd.hh_type, len(T.FAMILY_TYPES))][hd.m_hh]
    oth = np.flatnonzero(hd.m_slot == OTHER_REL)
    if oth.size:
        u = _uniform(seed, "w21.other_rel", mkey[oth], hd.m_no[oth])[:, 0]
        ok_all = feasible_other(head_age[oth])
        for ck in sorted(set(coarse[oth].tolist())):  # 逐次: 粗い類型 ≤ 5
            sel = np.flatnonzero(coarse[oth] == ck)
            rows = oth[sel]
            w = np.array([ward.members.get((r, ck), np.zeros(1)).sum() for r in OTHER_REL_CODES])
            w = w if w.sum() > 0 else np.ones(len(OTHER_REL_CODES))
            ww = w[None, :] * ok_all[sel]  # 窓が空になる続き柄は引かない(引き直し)
            k = (np.cumsum(ww, axis=1) < (u[sel] * ww.sum(axis=1))[:, None]).sum(axis=1)
            hd.m_rel[rows] = np.asarray(OTHER_REL_CODES, dtype=object)[np.minimum(k, len(OTHER_REL_CODES) - 1)]
    hd.m_rel[hd.m_slot == CHILD] = "03"
    hd.m_rel[hd.m_slot == PARENT] = "05"
    hd.m_rel[hd.m_slot == SIBLING] = "09"
    non = np.flatnonzero(hd.m_slot == NON_REL)
    hd.m_rel[non] = "12"

    # 父母が 2 人の世帯は 1 人目を父・2 人目を母にする
    par = np.flatnonzero(hd.m_slot == PARENT)
    sex_fixed = np.full(n, -1, dtype=np.int64)
    if par.size:
        n_par = np.bincount(hd.m_hh[par], minlength=hd.n_households)[hd.m_hh[par]]
        first = np.r_[True, hd.m_hh[par][1:] != hd.m_hh[par][:-1]]
        sex_fixed[par] = np.where(n_par >= 2, np.where(first, 0, 1), -1)

    rest = np.flatnonzero((hd.m_slot != HEAD) & (hd.m_slot != SPOUSE))
    lo, hi = windows(hd.m_slot[rest], hd.m_rel[rest], head_age[rest], spouse_age[rest], mother_age[rest],
                     father_age[rest])
    u = _uniform(seed, "w21.member", mkey[rest], hd.m_no[rest], words=2)
    gkey = np.char.add(np.char.add(hd.m_rel[rest].astype(str), "|"), coarse[rest].astype(str))
    ukeys, inv = np.unique(gkey, return_inverse=True)
    for gi, gk in enumerate(ukeys.tolist()):  # 逐次: 続き柄 × 粗い類型の組(≤ 60)
        r, ck = gk.split("|")
        idx = np.flatnonzero(inv == gi)
        rows = rest[idx]
        tab = ward.members.get((r, ck))
        if r == "05":
            tab = tab + ward.members.get(("06", ck), 0.0)
        if r in NON_REL_CODES:
            tab = ward.members.get(("11", ck), 0.0) + ward.members.get(("12", ck), 0.0)
        if tab is None or np.asarray(tab).sum() <= 0:
            tab = ward.members.get((r, "12"))
            if tab is None or tab.sum() <= 0:
                tab = np.ones((2, 21, 4))
        p2 = _expand_by_sex(np.asarray(tab).sum(axis=2), T.AGE21_EDGES, shape)
        sx, ag, f, e = _draw_sex_age(p2, lo[idx], hi[idx], u[idx, 0], sex_fixed[rows])
        fb["window_no_weight"] += f
        fb["window_empty"] += e
        hd.m_sex[rows], hd.m_age[rows] = sx, ag
        hd.m_marital[rows] = _marital_given(np.asarray(tab), sx, ag, u[idx, 1])
    if late_singles:
        _draw_singles(hd, ward, seed, np.asarray(age_sex_target), m_type, mkey)
    hd.m_marital = np.where(hd.m_age < 15, -1, hd.m_marital)
    fb["composition_truncated"] = int(sum(
        int(np.sum((types == t) & (hd.hh_size - 1 < len(COMPOSITION[t][0]))))
        for t in T.FAMILY_TYPES))
    hd.fallbacks = fb
    return hd


def _draw_singles(hd: HouseholdDraw, ward: T.Ward2025, seed: int | str, target: np.ndarray, m_type: np.ndarray,
                  mkey: np.ndarray) -> None:
    """単独世帯の世帯主を町丁目の残りの目標で引く(``draw_members`` の最後・逐次: 町丁目の数ぶん)。"""
    h = ward.head["3"]  # (2, 15, 4)
    p2 = _expand_by_sex(h.sum(axis=2), T.AGE_HEAD_EDGES, ward.shape)
    p2[:, :15] = 0.0
    a16 = T.age_class(np.arange(T.N_AGE), T.AGE16_EDGES)
    prior16 = np.zeros((16, 2))
    for s in range(2):  # 逐次: 男女 2
        np.add.at(prior16[:, s], a16, p2[s])
    known = hd.m_age >= 0
    a_k = T.age_class(hd.m_age[known], T.AGE16_EDGES)
    done = np.zeros_like(target)
    np.add.at(done, (hd.hh_chome[hd.m_hh[known]], a_k, hd.m_sex[known]), 1.0)
    rows_all = np.flatnonzero((m_type == "3") & (hd.m_slot == HEAD))
    u = _uniform(seed, "w21.single", mkey[rows_all], hd.m_no[rows_all], words=3)
    chome_of = hd.hh_chome[hd.m_hh[rows_all]]
    for c in range(target.shape[0]):  # 逐次: 町丁目の数ぶん
        sel = np.flatnonzero(chome_of == c)
        if sel.size == 0:
            continue
        q = np.clip(target[c] - done[c], 0.0, None) * (prior16 > 0)
        if q.sum() <= 0:
            q = prior16.copy()
        cnt = F.largest_remainder(q.ravel(), sel.size)
        sel = sel[np.argsort(u[sel, 0], kind="stable")]
        cells = np.repeat(np.arange(32), cnt)
        cls, sx = cells // 2, cells % 2
        rows = rows_all[sel]
        # 階級の中の各歳=単独世帯の世帯主の各歳の分布
        ages = np.zeros(sel.size, dtype=np.int64)
        for k in np.unique(cells):  # 逐次: 階級 × 男女(≤ 32)
            m = cells == k
            w = p2[k % 2] * (a16 == k // 2)
            w = w if w.sum() > 0 else (a16 == k // 2).astype(np.float64)
            cdf = np.cumsum(w) / w.sum()
            ages[m] = np.minimum(np.searchsorted(cdf, u[sel[m], 1], side="right"), T.MAX_AGE)
        hd.m_sex[rows], hd.m_age[rows] = sx, ages
        hc = T.age_class(ages, T.AGE_HEAD_EDGES)
        w = h[sx, np.clip(hc, 0, None)]
        tot = w.sum(axis=1)
        w = np.where(tot[:, None] > 0, w, np.array([1.0, 0.0, 0.0, 0.0]))
        kk = (np.cumsum(w, axis=1) < (u[sel, 2] * w.sum(axis=1))[:, None]).sum(axis=1)
        hd.m_marital[rows] = np.minimum(kk, 3)
        hd.m_rel[rows] = "01"


# ------------------------------------------------------------------------------------------ 手順 5
def anneal_vectors(hd: HouseholdDraw) -> np.ndarray:
    """世帯ごとの誤差のベクトル(年齢 16 × 男女 32+配偶 3 × 男女 6)=世帯員の数え。"""
    V = np.zeros((hd.n_households, N_VEC), dtype=np.float64)
    a16 = T.age_class(hd.m_age, T.AGE16_EDGES)
    np.add.at(V, (hd.m_hh, a16 * 2 + hd.m_sex), 1.0)
    adult = hd.m_marital >= 0
    m3 = T.MARITAL3_OF4[np.clip(hd.m_marital, 0, 3)]
    np.add.at(V, (hd.m_hh[adult], 32 + m3[adult] * 2 + hd.m_sex[adult]), 1.0)
    return V


def anneal_targets(tg: T.Targets) -> np.ndarray:
    return np.concatenate([tg.age16_sex.reshape(tg.stage_idx.size, -1), tg.marital3_sex.reshape(tg.stage_idx.size, -1)],
                          axis=1)


def anneal(hd: HouseholdDraw, target: np.ndarray, params: AnnealParams, seed: int | str) -> dict[str, float]:
    """同じ家族類型・同じ世帯人員の世帯どうしで町丁目を入れ替える焼きなまし(``hd.hh_chome`` を書き換える)。

    目的関数 = Σ 町丁目 Σ 要素 |数え − 目標|。施設等の人は動かさない。
    """
    V = anneal_vectors(hd)
    C = target.shape[0]
    ch = hd.hh_chome.copy()
    S = np.zeros((C, N_VEC))
    np.add.at(S, ch, V)
    e0 = float(np.abs(S - target).sum())
    info = {"error_before": e0, "error_after": e0, "accepted": 0, "proposed": 0, "iterations": 0}
    if not params.enabled or params.n_iter <= 0:
        return info
    movable = np.flatnonzero(hd.hh_type >= 0)
    gid = hd.hh_type[movable] * (MAX_SIZE + 1) + hd.hh_size[movable]
    order = movable[np.lexsort((movable, gid))]
    gsorted = hd.hh_type[order] * (MAX_SIZE + 1) + hd.hh_size[order]
    g_of = np.full(hd.n_households, -1, dtype=np.int64)
    g_of[order] = gsorted
    ug, gstart, glen = np.unique(gsorted, return_index=True, return_counts=True)
    gpos = {int(g): (int(s), int(L)) for g, s, L in zip(ug, gstart, glen)}
    raw = philox_array(seed, "w21.anneal", k19_counter_array(np.arange(params.n_iter, dtype=np.int64)), words=3)
    u = unit_float(raw)
    h1s = order[np.minimum((u[:, 0] * order.size).astype(np.int64), order.size - 1)]
    temps = params.t0 * (params.t1 / params.t0) ** (np.arange(params.n_iter) / max(params.n_iter - 1, 1))
    acc = 0
    prop = 0
    for k in range(params.n_iter):  # 逐次: 提案の数ぶん(固定の回数=宣言)
        h1 = int(h1s[k])
        s, L = gpos[int(g_of[h1])]
        if L < 2:
            continue
        h2 = int(order[s + min(int(u[k, 1] * L), L - 1)])
        a = int(ch[h1])
        b = int(ch[h2])
        if a == b:
            continue
        d = V[h2] - V[h1]
        prop += 1
        Sa, Sb, Ta, Tb = S[a], S[b], target[a], target[b]
        dE = float((np.abs(Sa + d - Ta) - np.abs(Sa - Ta)).sum() + (np.abs(Sb - d - Tb) - np.abs(Sb - Tb)).sum())
        if dE <= 0.0 or u[k, 2] < math.exp(-dE / temps[k]):
            S[a] += d
            S[b] -= d
            ch[h1], ch[h2] = b, a
            acc += 1
    hd.hh_chome = ch
    info.update({"error_after": float(np.abs(S - target).sum()), "accepted": acc, "proposed": prop,
                 "iterations": int(params.n_iter)})
    return info


# ------------------------------------------------------------------------------------------ 手順 6・7
def assign_categories(hh_chome: np.ndarray, shares: np.ndarray, u: np.ndarray, mask: np.ndarray) -> np.ndarray:
    """町丁目ごとに、``mask`` の世帯へ分類(列)を整数の数(最大剰余)で割り当てる(並びは乱数 ``u`` の順)。

    返り値は分類の番号(``mask`` の外は −1)。逐次ループ宣言: 町丁目の数ぶん。
    """
    out = np.full(hh_chome.size, -1, dtype=np.int64)
    for c in range(shares.shape[0]):  # 逐次: 町丁目の数ぶん
        rows = np.flatnonzero((hh_chome == c) & mask)
        if rows.size == 0:
            continue
        cnt = F.largest_remainder(shares[c], rows.size)
        rows = rows[np.argsort(u[rows], kind="stable")]
        out[rows] = np.repeat(np.arange(shares.shape[1]), cnt)
    return out


def choose_foreign(hd: HouseholdDraw, target: np.ndarray, ward: T.Ward2025, seed: int | str) -> np.ndarray:
    """町丁目ごとの外国人の数へ、世帯ごとに選ぶ(重み=世帯員の「日本人でない」割合の平均・Efraimidis–Spirakis の鍵)。

    返り値は世帯員ごとの真偽。逐次ループ宣言: 町丁目の数ぶん。
    """
    C = target.size
    tgt = F.largest_remainder(np.clip(target, 0.0, None), int(round(float(np.clip(target, 0.0, None).sum()))))
    p = ward.foreign_share[hd.m_sex, hd.m_age]
    wsum = np.bincount(hd.m_hh, weights=p, minlength=hd.n_households)
    w = np.maximum(wsum / np.maximum(hd.hh_size, 1), 1e-9)
    u = _uniform(seed, "w21.foreign", np.stack([hd.hh_chome_key, hd.hh_serial], 1), np.zeros(hd.n_households,
                                                                                          dtype=np.int64))[:, 0]
    key = np.log(np.maximum(u, 1e-300)) / w  # = log(u^(1/w))(大きいほど先)
    chosen = np.zeros(hd.n_households, dtype=bool)
    for c in range(C):  # 逐次: 町丁目の数ぶん
        rows = np.flatnonzero(hd.hh_chome == c)
        rows = rows[np.lexsort((rows, -key[rows]))]
        need = int(tgt[c])
        cum = np.cumsum(hd.hh_size[rows])
        take = cum <= need  # 鍵の順の頭から、数を越えない所まで
        k = int(take.sum())
        chosen[rows[:k]] = True
        left = need - (int(cum[k - 1]) if k else 0)
        if left > 0:  # 残りは鍵の順の 1 人世帯で埋める(越えない)
            ones = rows[k:][hd.hh_size[rows[k:]] == 1][:left]
            chosen[ones] = True
    return chosen[hd.m_hh]


#: 住宅の建て方 → 建物の階の区分(下限, 上限)。``None`` は町丁目の住居系の建物全部(自前の写像=宣言)。
LEVEL_CLASS: Final[Mapping[str, tuple[int, int] | None]] = MappingProxyType({
    "detached": (0, 2), "row_house": (0, 2), "apartment_1_2": (0, 2), "apartment_3_5": (3, 5),
    "apartment_6_10": (6, 10), "apartment_11plus": (11, 10_000), "other": None, "": None,
})


def place_households(hh_chome: np.ndarray, hh_building_type: np.ndarray, stage_idx: np.ndarray,
                     b_chome: np.ndarray, b_cell: np.ndarray, b_res: np.ndarray, b_floor: np.ndarray,
                     b_levels: np.ndarray, cover_cells: Sequence[tuple[np.ndarray, np.ndarray]],
                     u: np.ndarray) -> tuple[np.ndarray, np.ndarray, dict[str, int]]:
    """世帯 → 建物とセル(建て方の階の区分ごとに、町丁目の住居系の建物の床面積で配る=W16#3 と同じ床面積)。

    落とし先の順: 1. 区分に合う住居系の建物 2. 町丁目の住居系の建物全部(区分の候補が無い)3. 町丁目の建物全部
    4. 被覆したセルの面積(建物 −1)。逐次ループ宣言: 町丁目の数ぶん × 建て方の区分(8)。
    """
    building = np.full(hh_chome.size, -1, dtype=np.int64)
    cell = np.full(hh_chome.size, -1, dtype=np.int64)
    stats = {"by_class": 0, "class_fallback": 0, "by_any_building": 0, "by_covered_area": 0, "unplaced": 0}
    names = list(LEVEL_CLASS)
    for c, ci in enumerate(stage_idx.tolist()):  # 逐次: 町丁目の数ぶん
        res_c = np.flatnonzero((b_chome == ci) & (b_cell >= 0) & (b_floor > 0) & b_res)
        any_c = np.flatnonzero((b_chome == ci) & (b_cell >= 0))
        for bi, name in enumerate(names):  # 逐次: 建て方の区分
            rows = np.flatnonzero((hh_chome == c) & (hh_building_type == bi))
            if rows.size == 0:
                continue
            rows = rows[np.argsort(u[rows], kind="stable")]
            bounds = LEVEL_CLASS[name]
            cand = res_c
            mode = "by_class"
            if bounds is not None and res_c.size:
                lv = b_levels[res_c]
                inc = res_c[(lv >= bounds[0]) & (lv <= bounds[1])]
                if inc.size:
                    cand = inc
                else:
                    mode = "class_fallback"
            if cand.size == 0:
                cand = any_c
                mode = "by_any_building"
            if cand.size == 0:
                cells, counts = cover_cells[ci]
                if cells.size == 0:
                    stats["unplaced"] += int(rows.size)
                    continue
                per = F.largest_remainder(counts.astype(np.float64), rows.size)
                cell[rows] = np.repeat(cells, per)
                stats["by_covered_area"] += int(rows.size)
                continue
            w = np.maximum(b_floor[cand], 1.0)
            per = F.largest_remainder(w, rows.size)
            building[rows] = np.repeat(cand, per)
            cell[rows] = b_cell[building[rows]]
            stats[mode] += int(rows.size)
    return building, cell, stats
