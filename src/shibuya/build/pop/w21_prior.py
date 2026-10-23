"""W21 段 6「開始前の経験」(PS4・設計書 §2-5・§2-6・計画 第 4 期 段 6)。版 1.1.0。

正: 設計書 §2-5 PS4(データで分かる事実を入れ、その上に開始前の習慣の初期化を **TimeGeo 型を核に 1 つ**で行う)・§2-6・
パターン台帳 §10-3(**なじみの場所の法則と初期化に使った集計は検証に使わない**=計器に出すのは診断だけ)・指示書 §4-1 AT2
(通勤の見積りは実際の道のりから)。

1. **事実**: 家(段 2)・勤め先(段 4)・世帯と同僚(段 4 の関係の行)・**通勤の道のり**=W3 のセル間の歩行の最短の道のり
   (舞台で働く住民=家 → 勤め先・舞台の外で働く住民=家 → 渋谷駅の口のセルの最も近いもの・外から来て働く人=駅 → 勤め先)・
   住んでいる年数(第18表の区分 → 年=``attr_fns.f_residence_years``)。
2. **なじみの場所の数**: 容量 C を約 25 か所の分布から一人ずつ引く(Alessandretti 2018・幅は expedient)。行ったことの
   ある場所の数 L=C ×(住んでいる週 ÷ 20 週)^0.6(Song 2010 の μ)。リストに載せるのは F=min(C, L)。
3. **順位ごとの頻度**: f_k ∝ k^−1.2(Song 2010)を k=1..L で正規化(``visit_share``)。順位 1=家・2=勤め先(働く人)。
4. **実在の店と場所の当てはめ**(規則=設計者の指紋=**expedient・感度試験の腕の口** ``affinity``): 残りの枠を家の側と職場の
   側に半分ずつ(働く人)。側の錨(家・勤め先)が舞台の外なら、その側の枠は「舞台の外の場所」で数えるだけ(リストに載せない)。
   舞台の中の側は W6 の POI(2,337)から、重み=生活の段(年齢・世帯に小さい子)と業種の合い方 × exp(−道のり/500 m)で、
   重複なしに引く(重みつきの引き直しで最初に出た順=``side_draws`` 回まで)。順位は両側を交互に(家の側から)。腕
   ``distance_only``=業種の合い方を 1(年齢の制限だけ残す)。
5. 友人と顔なじみは作らない(慣らしの期間で育つ)。作り物の経験の文は作らない。

逐次ループ宣言(P4): 人の塊(``CHUNK`` 人)の数ぶん(体あたりの配列演算)と、側の数(2)。体ごとの for は無い。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

from shibuya.core.rng import k19_counter_array, philox_array, unit_float

from . import attr_fns as A

__all__ = ["LIFE_STAGES", "AFFINITY", "AFFINITY_ARMS", "DISTANCE_DECAY_M", "CHUNK", "SIDE_DRAW_FACTOR",
           "NIGHTLIFE_MIN_AGE", "LOVE_HOTEL_MIN_AGE",
           "life_stage", "affinity_matrix", "commute_facts", "familiar_places", "rank_shares"]

#: 生活の段(年齢の窓・自前)。
LIFE_STAGES: Final[tuple[str, ...]] = ("child", "teen", "young", "adult", "senior")
_STAGE_EDGES: Final[np.ndarray] = np.array([0, 13, 18, 30, 65], dtype=np.int64)
#: 業種の合い方(POI の ``cat`` か ``cat|subcat`` → 生活の段ごとの重み)=**自前の表(未リサーチ・expedient)**。``office`` は
#: 0(事務所は勤め先の組織)。``school|childcare`` は乳幼児と、小さい子(6 歳未満)のいる世帯の大人だけ(下の規則)。
AFFINITY: Final[Mapping[str, tuple[float, ...]]] = MappingProxyType({
    "food": (0.3, 0.6, 1.0, 1.0, 0.8), "shop": (0.3, 0.8, 1.0, 1.0, 0.8),
    "shop|convenience": (0.5, 1.0, 1.0, 1.0, 0.8), "nightlife": (0.0, 0.0, 0.8, 0.5, 0.2),
    "nightlife|karaoke": (0.0, 0.5, 0.8, 0.4, 0.2), "hotel": (0.0, 0.0, 0.05, 0.05, 0.05),
    "hotel|love_hotel": (0.0, 0.0, 0.05, 0.05, 0.0), "service": (0.3, 0.3, 0.6, 0.8, 1.0),
    "service|hospital": (0.3, 0.2, 0.3, 0.5, 1.0), "service|library": (0.5, 0.8, 0.5, 0.5, 0.8),
    "school": (0.5, 0.6, 0.2, 0.1, 0.05), "school|childcare": (1.0, 0.0, 0.0, 0.0, 0.0),
    "education": (0.5, 0.6, 0.3, 0.1, 0.1), "leisure": (0.6, 0.6, 0.6, 0.6, 0.6),
    "leisure|park": (1.0, 0.6, 0.6, 0.8, 1.0), "leisure|gym": (0.0, 0.3, 0.8, 0.8, 0.4),
    "landmark": (0.2, 0.2, 0.3, 0.3, 0.4), "landmark|worship": (0.1, 0.1, 0.1, 0.3, 0.8),
    "cinema": (0.3, 0.6, 0.6, 0.5, 0.3), "hall": (0.3, 0.6, 0.6, 0.5, 0.3), "attraction": (0.3, 0.6, 0.6, 0.5, 0.3),
    "office": (0.0, 0.0, 0.0, 0.0, 0.0),
})
#: 年齢の制限(どの腕でも残す=法と施設の決まりの近似・人の年齢で切る=生活の段の境と別): 夜の店は 20 歳未満 0(カラオケを
#: 除く=:data:`NIGHTLIFE_MIN_AGE`)・ラブホテルは 18 歳未満 0(:data:`LOVE_HOTEL_MIN_AGE`)。〔検収 L1〕前の版は生活の段
#: (若者=18 歳から)で切っていて、18〜19 歳に夜の店が載った。
#: 腕: ``lifestage``(既定=上の表)・``distance_only``(表の正の値を 1 に)。
AFFINITY_ARMS: Final[tuple[str, ...]] = ("lifestage", "distance_only")
NIGHTLIFE_MIN_AGE: Final[int] = 20
LOVE_HOTEL_MIN_AGE: Final[int] = 18
#: 道のりの重みの減り方(exp(−d/L)・自前=expedient)。
DISTANCE_DECAY_M: Final[float] = 500.0
#: 人の塊の大きさ(メモリの上限のため・結果は塊の大きさに依らない=乱数は人ごとの流れの先頭から使う)。
CHUNK: Final[int] = 2048
#: 側ごとの引き直しの回数=枠 × この倍率(重複を除いて足りなければ枠より少なく載る=計器に数を出す)。
SIDE_DRAW_FACTOR: Final[int] = 4


def life_stage(age: np.ndarray) -> np.ndarray:
    return np.clip(np.searchsorted(_STAGE_EDGES, np.asarray(age, dtype=np.int64), side="right") - 1, 0,
                   len(LIFE_STAGES) - 1)


def affinity_matrix(poi_cat: np.ndarray, poi_subcat: np.ndarray, arm: str = "lifestage") -> np.ndarray:
    """(生活の段 5 × 2(小さい子のいる世帯か), POI)の重み。"""
    if arm not in AFFINITY_ARMS:
        raise ValueError(f"affinity の腕は {AFFINITY_ARMS}(いま {arm!r})")
    cat = np.asarray(poi_cat).astype(str)
    sub = np.asarray(poi_subcat).astype(str)
    P = cat.size
    out = np.zeros((len(LIFE_STAGES), 2, P))
    keys = np.char.add(np.char.add(cat, "|"), sub)
    for j, (k1, k2) in enumerate(zip(keys.tolist(), cat.tolist())):  # 逐次: POI の数ぶん(写像の引き)
        row = AFFINITY.get(k1) or AFFINITY.get(k2) or (0.0,) * len(LIFE_STAGES)
        out[:, 0, j] = row
        out[:, 1, j] = row
        if k1 == "school|childcare":
            out[2:4, 1, j] = 1.0  # 小さい子のいる世帯の大人(若者・大人)
    if arm == "distance_only":
        out = (out > 0).astype(np.float64)
        adult_only = np.isin(cat, ["nightlife"]) & (sub != "karaoke")
        out[:2, :, adult_only] = 0.0
        out[:2, :, sub == "love_hotel"] = 0.0  # 年齢そのものの制限は familiar_places で(どの腕でも)
        out[:, :, cat == "office"] = 0.0
    return out


def rank_shares(rank: np.ndarray, known: np.ndarray) -> np.ndarray:
    """順位 k の頻度の割合 k^−1.2 / Σ_{j≤L} j^−1.2(L=行ったことのある場所の数)。"""
    r = np.asarray(rank, dtype=np.float64)
    L = np.asarray(known, dtype=np.int64)
    Lmax = int(L.max()) if L.size else 1
    h = np.cumsum(np.arange(1, Lmax + 1, dtype=np.float64) ** (-A.RANK_EXPONENT))
    return (r ** (-A.RANK_EXPONENT)) / h[np.clip(L, 1, Lmax) - 1]


def commute_facts(kind: np.ndarray, workplace_area: np.ndarray, home_cell: np.ndarray, work_cell: np.ndarray,
                  dist: np.ndarray, station_cells: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """(通勤の手段の語, 舞台の中の歩く道のり[m]・−1=空欄)。住民の舞台の中の勤め先=歩き(家 → 勤め先)・自宅=家・舞台の外で
    働く住民=鉄道(家 → 最も近い駅の口のセル)・外から来て働く人=鉄道(最も近い駅の口のセル → 勤め先)。"""
    kd = np.asarray(kind).astype(str)
    wa = np.asarray(workplace_area).astype(str)
    hc = np.asarray(home_cell, dtype=np.int64)
    wc = np.asarray(work_cell, dtype=np.int64)
    D = np.asarray(dist)
    st = np.asarray(station_cells, dtype=np.int64)
    n = kd.size
    mode = np.full(n, "", dtype=object)
    path = np.full(n, -1, dtype=np.int64)
    walk = (kd == "resident") & (wa == "stage") & (hc >= 0) & (wc >= 0)
    mode[walk] = "walk"
    path[walk] = D[hc[walk], wc[walk]]
    home = (kd == "resident") & (wa == "home")
    mode[home] = "home"
    path[home] = 0
    out_res = (kd == "resident") & np.isin(wa, ["ward_outside_stage", "outside_ward"]) & (hc >= 0)
    mode[out_res] = "rail"
    if st.size:
        path[out_res] = D[hc[out_res]][:, st].min(axis=1)
    com = (kd == "commuter") & (wc >= 0)
    mode[kd == "commuter"] = "rail"
    if st.size:
        path[com] = D[wc[com]][:, st].min(axis=1)
    return mode, path


def _side_draw(seed: int | str, domain: str, pid: np.ndarray, anchor: np.ndarray, need: np.ndarray,
               weight_rows: np.ndarray, dist: np.ndarray, poi_cell: np.ndarray) -> tuple[np.ndarray, ...]:
    """1 つの側の当てはめ(塊の中)。返り値=(人の行, POI の番号, 側の中の順, 錨からの道のり)。"""
    n = pid.size
    if n == 0 or int(need.max(initial=0)) <= 0:
        z = np.zeros(0, dtype=np.int64)
        return z, z, z, z
    D = dist[anchor][:, poi_cell].astype(np.float64)  # (n, P)
    W = weight_rows * np.exp(-D / DISTANCE_DECAY_M)
    tot = W.sum(axis=1)
    R = int(need.max()) * SIDE_DRAW_FACTOR
    u = unit_float(philox_array(seed, domain, k19_counter_array(pid), words=R))  # (n, R)=人ごとの流れの先頭 R 語
    cdf = np.cumsum(W, axis=1) / np.where(tot > 0, tot, 1.0)[:, None]
    P = W.shape[1]
    flat = (cdf + np.arange(n)[:, None]).ravel()
    q = (u + np.arange(n)[:, None]).ravel()
    idx = np.searchsorted(flat, q, side="right") - np.repeat(np.arange(n) * P, R)
    idx = np.clip(idx, 0, P - 1).reshape(n, R)
    draw_ok = (tot > 0)[:, None] & (np.arange(R)[None, :] < (need * SIDE_DRAW_FACTOR)[:, None])
    rows = np.repeat(np.arange(n), R)[draw_ok.ravel()]
    pois = idx.ravel()[draw_ok.ravel()]
    pos = np.tile(np.arange(R), n)[draw_ok.ravel()]
    key = rows.astype(np.int64) * P + pois
    _uk, first = np.unique(key, return_index=True)
    rows, pois, pos = rows[first], pois[first], pos[first]
    order = np.lexsort((pos, rows))
    rows, pois = rows[order], pois[order]
    starts = np.flatnonzero(np.r_[True, rows[1:] != rows[:-1]]) if rows.size else np.zeros(0, dtype=np.int64)
    within = np.arange(rows.size) - np.repeat(starts, np.diff(np.r_[starts, rows.size])) if rows.size else rows
    keep = within < need[rows]
    rows, pois, within = rows[keep], pois[keep], within[keep]
    return rows, pois, within, D[rows, pois].astype(np.int64)


def familiar_places(seed: int | str, people: Mapping[str, Any], poi: Mapping[str, Any], dist: np.ndarray, *,
                    arm: str = "lifestage") -> tuple[dict[str, np.ndarray], dict[str, np.ndarray]]:
    """なじみの場所(体 × 場所 × 順位)と、人ごとの数(載せた数・舞台の外の数・引けずに足りなかった数)。

    ``people``: ``person_id``・``kind``・``age``・``home_cell``・``work_cell``・``workplace_area``・``known_places``・
    ``place_capacity``・``young_child_household``(6 歳未満のいる世帯の人)。``poi``: ``poi_id``・``cat``・``subcat``・
    ``cell``。乱数の鍵=(人の番号)・ドメイン ``w21b.prior.<側>``。
    """
    pid = np.asarray(people["person_id"], dtype=np.int64)
    n = pid.size
    kind = np.asarray(people["kind"]).astype(str)
    hc = np.asarray(people["home_cell"], dtype=np.int64)
    wc = np.asarray(people["work_cell"], dtype=np.int64)
    wa = np.asarray(people["workplace_area"]).astype(str)
    C = np.asarray(people["place_capacity"], dtype=np.int64)
    L = np.asarray(people["known_places"], dtype=np.int64)
    F = np.minimum(C, L)
    ls = life_stage(people["age"])
    yc = np.asarray(people["young_child_household"], dtype=bool).astype(np.int64)
    worker = np.isin(wa, ["home", "stage", "ward_outside_stage", "outside_ward"]) | (kind == "commuter")
    home_in = (kind == "resident") & (hc >= 0)
    work_in = (wc >= 0) & (wa != "home")
    # 錨: 順位 1=家(住民=舞台の中・外から来る人=外)・順位 2=勤め先(働く人・自宅で働く人は家と同じ=錨 1 つ)
    n_anchor = 1 + (worker & (wa != "home")).astype(np.int64)
    slots = np.maximum(F - n_anchor, 0)
    two_sides = worker & (wa != "home")
    home_need = np.where(two_sides, (slots + 1) // 2, slots)
    work_need = np.where(two_sides, slots // 2, 0)
    home_list = np.where(home_in, home_need, 0)
    work_list = np.where(work_in, work_need, 0)
    outside = np.where(home_in, 0, home_need) + np.where(work_in, 0, work_need)
    aff = affinity_matrix(poi["cat"], poi["subcat"], arm)
    age = np.asarray(people["age"], dtype=np.int64)
    pc = np.asarray(poi["cat"]).astype(str)
    ps = np.asarray(poi["subcat"]).astype(str)
    night = (pc == "nightlife") & (ps != "karaoke")
    lhotel = ps == "love_hotel"
    pcell = np.asarray(poi["cell"], dtype=np.int64)
    rows_p, rows_rank, rows_kind, rows_poi, rows_cell, rows_side, rows_dist = [], [], [], [], [], [], []
    got = np.zeros(n, dtype=np.int64)
    P_ = pcell.size
    for a in range(0, n, CHUNK):  # 逐次: 塊の数ぶん
        sl = np.arange(a, min(a + CHUNK, n))
        taken = np.zeros((sl.size, P_), dtype=bool)  # 家の側で載せた店は職場の側で引かない(同じ店を 2 回載せない)
        for side, need, anchor in (("home", home_list, hc), ("work", work_list, wc)):  # 逐次: 側の数(2)
            loc = np.flatnonzero(need[sl] > 0)
            if loc.size == 0:
                continue
            m = sl[loc]
            wrows = aff[ls[m], yc[m]] * ~taken[loc]
            wrows[np.ix_(age[m] < NIGHTLIFE_MIN_AGE, night)] = 0.0  # 〔検収 L1〕人の年齢で切る
            wrows[np.ix_(age[m] < LOVE_HOTEL_MIN_AGE, lhotel)] = 0.0
            r, p, w, d = _side_draw(seed, f"w21b.prior.{side}", pid[m], anchor[m], need[m], wrows, dist, pcell)
            taken[loc[r], p] = True
            who = m[r]
            np.add.at(got, who, 1)
            # 順位: 錨の後に、家の側を奇数番目・職場の側を偶数番目に(片側だけの人は続けて)
            base = n_anchor[who] + 1
            two = two_sides[who] & home_in[who] & work_in[who]
            rk = np.where(two, base + 2 * w + (1 if side == "work" else 0), base + w)
            rows_p.append(who)
            rows_rank.append(rk)
            rows_kind.append(np.full(who.size, "poi", dtype=object))
            rows_poi.append(p)
            rows_cell.append(pcell[p])
            rows_side.append(np.full(who.size, side, dtype=object))
            rows_dist.append(d)
    # 錨の行
    a_home = np.flatnonzero(home_in)
    a_work = np.flatnonzero(worker & (wa != "home") & work_in)
    rows_p += [a_home, a_work]
    rows_rank += [np.ones(a_home.size, dtype=np.int64), np.full(a_work.size, 2, dtype=np.int64)]
    rows_kind += [np.full(a_home.size, "home", dtype=object), np.full(a_work.size, "work", dtype=object)]
    rows_poi += [np.full(a_home.size, -1, dtype=np.int64), np.full(a_work.size, -1, dtype=np.int64)]
    rows_cell += [hc[a_home], wc[a_work]]
    rows_side += [np.full(a_home.size, "", dtype=object), np.full(a_work.size, "", dtype=object)]
    rows_dist += [np.zeros(a_home.size, dtype=np.int64), np.zeros(a_work.size, dtype=np.int64)]
    who = np.concatenate(rows_p)
    rank = np.concatenate(rows_rank)
    order = np.lexsort((rank, who))
    who, rank = who[order], rank[order]
    poi_idx = np.concatenate(rows_poi)[order]
    places = {
        "person_id": pid[who].astype(np.int32),
        "rank": rank.astype(np.int16),
        "place_kind": np.concatenate(rows_kind)[order],
        "poi_index": poi_idx.astype(np.int32),
        "poi_id": np.where(poi_idx >= 0, np.asarray(poi["poi_id"], dtype=object)[np.clip(poi_idx, 0, None)], ""),
        "cell": np.concatenate(rows_cell)[order].astype(np.int32),
        "side": np.concatenate(rows_side)[order],
        "dist_m": np.concatenate(rows_dist)[order].astype(np.int32),
        "visit_share": rank_shares(rank, L[who]).astype(np.float32),
    }
    listed = np.bincount(who, minlength=n)
    counts = {
        "familiar_target": F, "listed_places": listed, "outside_places": outside,
        "short_of_target": np.maximum(home_list + work_list - got, 0),
        "anchors_outside": (~home_in).astype(np.int64) + (worker & (wa != "home") & ~work_in).astype(np.int64),
    }
    return places, counts
