"""第 4 期 4-1 段 4〜7(W21 の続き=``w21_build_b``)の受入の試験。

- 段 4〜7 の合成の単体: 舞台で働く人の数・住民の勤め先・席への所属(空席と席の外)・部署(上司は 1 人・部署の数)・役割の語・
  関係の組・店の持ち主・段 5 の関数(純粋・空欄の規則・0 円の割合・傾け)・段 6 の法則(約 25 か所・k^−1.2・t^0.6=合成で)・
  段 7 の層の数と空欄。
- 読み口の守りの負の対照(検証側の表=#45・#47・#49・#50・#16・#57 を開くと止まる・r99 の置き場の第6-2表も止まる)。
- 出力先の守り(本体の v2・段 1〜3 の資産・既存の置き場には書かない)。
- 実データ(``requires_data``): 2 回組んで sha256 一致・golden(記録 pop41b/README.md)・計器の表・W12 の検証側の欄を読まない・
  段 1〜3 の資産は変わらない・既定の組み立てに W21b が入らない。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
import pytest

from shibuya.build import run as build_run
from shibuya.build.pop import STAGES as POP_STAGES
from shibuya.build.pop import attr_fns as A
from shibuya.build.pop import w21_build_b as B
from shibuya.build.pop import w21_money as M
from shibuya.build.pop import w21_org as O
from shibuya.build.pop import w21_outside as X
from shibuya.build.pop import w21_prior as P
from shibuya.build.pop import w21_sources as S

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"


# ================================================================================ 合成の表
def _tables_b(rng_seed: int = 0) -> A.AttrTablesB:
    rng = np.random.default_rng(rng_seed)
    O_ = len(A.WAGE_OCCUPATIONS)
    K = 6
    lo = np.array([80_000, 150_000, 200_000, 300_000, 400_000, 600_000], dtype=float)
    hi = np.array([150_000, 200_000, 300_000, 400_000, 600_000, 900_000], dtype=float)
    sav_lo = np.array([0, 250_000, 1_000_000, 5_000_000, 20_000_000], dtype=float)
    sav_hi = np.array([250_000, 1_000_000, 5_000_000, 20_000_000, 40_000_000], dtype=float)
    freq = np.array([[10, 10, 30, 30, 20]] * 3, dtype=float)
    cmean = 0.5 * (sav_lo + sav_hi)
    cmean[-1] = 30_000_000
    nA = A.ASSET_AGE_EDGES.size
    t = A.AttrTablesB(
        wage_level=np.full((O_, 2, 2), 300_000.0), wage_bonus=np.full((O_, 2, 2), 600_000.0),
        wage_hours=np.full((O_, 2, 2), 160.0), wage_all=np.full((O_, 2), 300_000.0),
        wage_age_ratio=np.ones((O_, 2, A.WAGE_AGE_EDGES.size)), bonus_age_ratio=np.ones((O_, 2, A.WAGE_AGE_EDGES.size)),
        wage_cls_lo=lo, wage_cls_hi=hi, wage_cls_freq=rng.random((O_, 2, K)) + 0.1,
        wage_median=np.full((O_, 2), 300_000.0), pt_hourly=np.full((O_, 2), 1200.0),
        pt_bonus=np.full((O_, 2), 30_000.0), pt_hours_day=np.full((O_, 2), 5.0), pt_days=np.full((O_, 2), 15.0),
        sav_freq=freq, sav_cls_mean=np.tile(cmean, (3, 1)), sav_rate_cls=np.array([[50, 100, 100, 100, 100]] * 3,
                                                                                    dtype=float),
        sav_lo=sav_lo, sav_hi=sav_hi, debt_rate_cls=np.array([[40, 35, 30, 30, 20]] * 3, dtype=float),
        sav_mean_age=np.full((3, nA), 8_000_000.0), sav_rate_age=np.full((3, nA), 90.0),
        dep_mean_age=np.full((3, nA), 3_000_000.0), debt_mean_age=np.full((3, nA), 2_000_000.0),
        debt_rate_age=np.full((3, nA), 30.0), tokyo_ratio_sav=np.ones(3), tokyo_ratio_debt=np.ones(3),
        sav_tilt=np.zeros((3, nA)), jicc_holder_rate=0.1,
        origin_codes=np.array(["13114", "13112", "13113"], dtype=object),
        origin_names=np.array(["中野区", "世田谷区", "渋谷区(輪)"], dtype=object), origin_w=np.array([1.0, 3.0, 1.0]),
        entry_nodes=np.array(["ext_rail_a", "ext_rail_b"], dtype=object), entry_w=np.array([1.0, 3.0]),
    )
    return t.freeze()


def _key(name: str, n: int, offset: int = 0) -> A.AttrKey:
    ids = np.arange(n) + offset
    return A.AttrKey(11, f"test.{name}", np.stack([ids, np.zeros(n, int), np.zeros(n, int)], axis=1))


def _status_codes(words) -> np.ndarray:
    return np.array([A.EMP_STATUS.index(w) if w else -1 for w in words], dtype=np.int64)


# ================================================================================ 登録表
def test_registry_has_stage_4_to_6_functions_with_stage_marks():
    # 〔段 8〜10〕段 9・10 の関数は test_w21_stage8_9.py(段 4〜6 の集合と版はこのまま)
    names = {f.name: f.stage for f in A.REGISTRY.values() if 4 <= f.stage <= 6}
    assert names == {
        "commuter_sex": 4, "commuter_age": 4, "origin_muni": 4, "entry_node": 4, "org_role": 4, "weekly_hours": 4,
        "duty_role_org": 4, "wage_monthly": 5, "wage_hourly": 5, "wage_annual": 5, "household_savings": 5,
        "household_deposits": 5, "household_debt": 5, "consumer_credit": 5, "wallet_cash": 5, "card_holding": 5,
        "account_holding": 5, "residence_years": 6, "place_capacity": 6, "known_places": 6}
    assert all(f.version == "1.1.0" for f in A.REGISTRY.values() if 4 <= f.stage <= 6)
    # 段 1〜3 の manifest に載る版の表は変えない(段 3 の関数だけ)
    assert set(A.registry_versions((3,))) == {f.name for f in A.REGISTRY.values() if f.stage == 3}
    assert B.STAGE_VERSION_B == "1.1.0" and B.STAGE_B == "W21b"


# ================================================================================ 段 4
def test_stage_worker_targets_census_number_with_ecen_distribution():
    emp80 = np.array([100.0, 300.0, 600.0, 0.0])
    stage_idx = np.array([1, 2])
    cov = np.array([1.0, 0.5])
    n, s = O.stage_worker_targets(emp80, 1000.0, stage_idx, cov, 2000.0)
    assert s == pytest.approx((300 + 300) / 1000)
    assert n.sum() == 1200 and n.tolist() == [600, 600]  # 席の配分(経済センサス)× 人数(国勢調査)


def test_resident_workplaces_rules():
    wk = np.array([0, 1, 1, 2, 3, -1])
    home = np.array([1, 0, 0, 0, 1, 0])
    emp80 = np.array([0.0, 10.0, 0.0, 10.0])  # 町丁目 1 と 3 だけに働く場所
    stage_idx = np.array([1, 2])
    cov = np.array([1.0, 1.0])
    u = np.array([[0.0, 0.0], [0.1, 0.0], [0.9, 0.0], [0.5, 0.5], [0.5, 0.5], [0.5, 0.5]])
    area, ch = O.assign_resident_workplaces(wk, home, emp80, stage_idx, cov, u)
    W = O.WORKPLACE_AREAS
    assert [W[a] for a in area] == ["home", "stage", "ward_outside_stage", "outside_ward", "outside_ward", ""]
    assert ch.tolist() == [1, 0, -1, -1, -1, -1]  # 自宅=家の町丁目・区内=町丁目 1(舞台の 0 番)


def test_fill_seats_min_of_seats_and_people_proportional_and_deterministic():
    oi = np.array(["IT", "IT", "FB", "FB"])
    seats = np.array([10, 30, 5, 5])
    pi = np.array(["IT"] * 20 + ["FB"] * 15 + ["", "MW"])
    u = np.linspace(0, 1, pi.size, endpoint=False)[::-1]
    org_of, filled, rep = O.fill_seats(oi, seats, pi, u)
    assert rep["IT"] == {"seats": 40, "people": 20, "filled": 20, "vacant": 20, "overflow": 0}
    assert rep["FB"] == {"seats": 10, "people": 15, "filled": 10, "vacant": 0, "overflow": 5}
    assert rep["MW"]["seats"] == 0 and rep["MW"]["overflow"] == 1
    assert filled.tolist() == [5, 15, 5, 5]  # 席に比例
    assert (filled <= seats).all() and (org_of[-2:] == -1).all()
    assert np.bincount(org_of[org_of >= 0], minlength=4).tolist() == filled.tolist()
    org2, _f, _r = O.fill_seats(oi, seats, pi, u)
    assert np.array_equal(org_of, org2)


def test_class_seats_and_role_aware_filling():
    seats = np.array([10, 3, 0])
    sh = np.array([[0.1, 0.0, 0.1, 0.5, 0.3]] * 3)
    cs = O.class_seats(seats, sh)
    assert cs.sum(axis=1).tolist() == [10, 3, 0] and cs[0].tolist() == [1, 0, 1, 5, 3]
    oi = np.array(["IT", "IT", "IT"])
    # 人: 業主 4・無期 9・有期 1(区分 0・3・4)
    pc = np.array([0] * 4 + [3] * 9 + [4])
    pi = np.array(["IT"] * pc.size)
    u = np.linspace(0, 1, pc.size, endpoint=False)
    org_of, filled, rep = O.fill_seats_by_role(oi, cs, pi, pc, u)
    r = rep["IT"]
    seats0 = int(cs[:, 0].sum())
    assert (org_of[pc == 0] >= 0).sum() == seats0  # 業主は業主の席にだけ(残りは席の外)
    emp_seats = int(cs[:, 3].sum() + cs[:, 4].sum())
    assert (org_of[np.isin(pc, [3, 4])] >= 0).sum() == min(10, emp_seats)  # 雇われる人は無期と有期の席を相互に使う
    assert r["filled"] == int((org_of >= 0).sum()) and r["filled"] + r["vacant"] == r["seats"]
    assert (filled <= seats).all() and np.bincount(org_of[org_of >= 0], minlength=3).tolist() == filled.tolist()
    assert set(r["by_class"]) == set(O.WC.ECEN_STATUS5)


def test_departments_one_supervisor_and_sizes():
    n = 30
    org = np.r_[np.zeros(n, dtype=int), np.ones(3, dtype=int), -np.ones(2, dtype=int)]
    rank = np.r_[np.array([1] * n), [0, 3, 3], [1, 1]]
    age = np.r_[np.arange(n) + 20, [50, 30, 40], [30, 30]]
    ind = np.array(["IT", "FB"])
    d = O.departments(org, rank, age, ind)
    # IT: S = 1+8.2 → k = round(30/9.2) = 3・FB: S = 17 → k = 1
    assert d["n_departments_of_org"].tolist() == [3, 1]
    m0 = org == 0
    sizes = np.bincount(d["department"][m0])
    assert sizes.max() - sizes[sizes > 0].min() <= 1
    assert d["is_org_head"].sum() == 2 and (d["supervisor"][d["is_org_head"]] == -1).all()
    members = (org >= 0) & ~d["is_org_head"]
    assert (d["supervisor"][members] >= 0).all()  # 上司はちょうど 1 人
    head0 = int(np.flatnonzero(d["is_org_head"] & m0)[0])
    assert age[head0] == 49  # 同じ順位なら年上
    dh = np.flatnonzero(d["is_dept_head"] & m0 & ~d["is_org_head"])
    assert (d["supervisor"][dh] == head0).all()
    rest = np.flatnonzero(m0 & ~d["is_dept_head"])
    for p in rest:  # 部署の長が上司
        sup = d["supervisor"][p]
        assert d["department"][sup] == d["department"][p] and d["is_dept_head"][sup]
    fb_head = int(np.flatnonzero(d["is_org_head"] & (org == 1))[0])
    assert age[fb_head] == 50 and rank[fb_head] == 0  # 役員・業主が先
    assert (d["department"][org < 0] == -1).all()
    d2 = O.departments(org, rank, age, ind)
    assert all(np.array_equal(d[k], d2[k]) for k in d)
    words = O.role_words(np.array(["正社員"] * org.size, dtype=object), d, org, ind, rank)
    assert words[fb_head] == "店長" and words[head0] == "責任者"


def test_departments_division_arm():
    n = 200
    org = np.zeros(n, dtype=int)
    d = O.departments(org, np.ones(n, dtype=int), np.arange(n), np.array(["IT"]), division_arm=True)
    k = int(d["n_departments_of_org"][0])  # round(200/9.2) = 22
    g = int(np.floor(n / 26.6 + 0.5))  # 8 部
    assert k == 22 and d["is_division_head"].sum() == g - 1
    head = int(np.flatnonzero(d["is_org_head"])[0])
    div = np.flatnonzero(d["is_division_head"])
    assert (d["supervisor"][div] == head).all()
    lower = np.flatnonzero(d["is_dept_head"] & ~d["is_division_head"] & ~d["is_org_head"])
    assert (np.isin(d["supervisor"][lower], np.r_[div, head])).all()


def test_relation_pairs_all_ordered_pairs_within_groups():
    g = np.array([0, 0, 0, 1, 1, -1, 2])
    u, v = O.relation_pairs(g)
    assert u.size == 3 * 2 + 2 * 1
    assert (u != v).all() and (g[u] == g[v]).all()
    assert set(zip(u.tolist(), v.tolist())) == {(a, b) for a in range(7) for b in range(7)
                                                if a != b and g[a] == g[b] and g[a] >= 0}


def test_store_owners_same_building_and_industry():
    owner = O.store_owners(np.array(["food", "food", "shop", "landmark", "service"]),
                           np.array(["", "", "convenience", "", "hospital"]),
                           np.array(["b1", "b1", "b1", "b1", "b2"]), np.array(["FB", "FB", "WR", "MW"]),
                           np.array(["b1", "b1", "b1", "b2"]))
    assert owner.tolist() == [0, 1, 2, -1, 3]


def test_commuter_and_role_functions():
    t3 = _attr_tables3()
    n = 3000
    attrs = {"kind": np.r_[np.full(n - 10, "commuter"), np.full(10, "resident")].astype(object)}
    k = _key("sexage", n)
    sx = A.call("commuter_sex", attrs, t3, k)
    ag = A.call("commuter_age", attrs, t3, k)
    assert (sx[-10:] == -1).all() and (ag[-10:] == -1).all()
    assert set(np.unique(sx[:-10])) <= {0, 1} and ag[:-10].min() >= 15 and ag[:-10].max() <= 100
    assert np.array_equal(sx, A.call("commuter_sex", attrs, t3, k))
    tb = _tables_b()
    o = A.call("origin_muni", attrs, tb, _key("o", n))
    assert set(o[:-10].tolist()) <= {"13114", "13112", "13113"} and (o[-10:] == "13113").all()
    assert (o[:-10] == "13112").mean() == pytest.approx(0.6, abs=0.05)
    wa = np.r_[np.full(n - 10, "stage"), ["outside_ward"] * 5, ["stage"] * 5].astype(object)
    e = A.call("entry_node", {"kind": attrs["kind"], "workplace_area": wa}, tb, _key("e", n))
    assert (e[:-5] != "").all() and (e[-5:] == "").all()
    roles = A.call("org_role", {"emp_status": _status_codes(["regular", "part_time", "", "executive"])}, tb,
                   _key("r", 4))
    assert roles.tolist() == ["正社員", "パート・アルバイト", "", "役員"]


def _attr_tables3() -> A.AttrTables:
    rng = np.random.default_rng(0)
    G = 4
    return A.AttrTables(
        emp_rate=np.full((2, 17, 4), 0.6), status_prior=rng.random((2, 4, 17, 8)) + 0.01,
        industry_prior=rng.random((2, 17, 8, 20)) + 0.01, occupation_prior=rng.random((2, 17, 20, 12)) + 0.01,
        workplace_prior=rng.random((5, 20, 4)) + 0.01, commuter_industry=rng.random((2, 17, 20)) + 0.01,
        commuter_occupation=rng.random((2, 20, 12)) + 0.01, commuter_status=rng.random((20, 5)) + 0.01,
        student_in=np.ones((2, 3)), student_in_ages=np.array([[6, 14], [15, 19], [20, 24]]), n_split=(1.0, 1.0),
        chome_labour=np.ones((G, 3)), chome_status=np.ones((G, 3)), chome_industry=np.ones((G, 20)),
        chome_occupation=np.ones((G, 12)), chome_workplace=np.ones((G, 4)), chome_school=np.ones((G, 11)),
        chome_school_place=np.ones((G, 3)), chome_residence=np.ones((G, 6)),
    ).freeze()


def test_duty_role_rules():
    occ = {c: A.OCCUPATION_MAJORS.index(c) for c in "CDEFIK"}
    rows = [  # (industry_key, major, sector, occ, role, org, 勤め先の場所) → 語
        ("TR", 7, "宅配拠点", occ["I"], "正社員", 3, "stage", "納品ドライバー"),
        ("TR", 7, "倉庫", occ["K"], "パート・アルバイト", 3, "stage", "配送作業員"),
        ("SV", 17, "施設管理/メンテ", occ["K"], "正社員", 5, "stage", "清掃作業員"),
        ("SV", 17, "警備", occ["F"], "正社員", 5, "stage", "警備員"),
        ("FB", 12, "カフェ", occ["E"], "店長", 7, "stage", "店長"),
        ("WR", 8, "食品小売", occ["D"], "パート・アルバイト", 9, "stage", "補充"),
        ("TR", 7, "", occ["E"], "正社員", -1, "stage", "駅員"),
        ("IT", 6, "業務SaaS", occ["C"], "正社員", 2, "stage", ""),
        # 〔検収 M2〕自宅で働く人・舞台の外で働く住民には②群の担当が付かない
        ("TR", 7, "", occ["E"], "正社員", -1, "home", ""),
        ("TR", 7, "", occ["E"], "正社員", -1, "outside_ward", ""),
        ("TR", 7, "", occ["I"], "正社員", -1, "ward_outside_stage", ""),
        ("", 18, "", occ["F"], "正社員", -1, "outside_ward", ""),
    ]
    attrs = {"industry_key": np.array([r[0] for r in rows], dtype=object),
             "industry_major": np.array([r[1] for r in rows]), "org_sector": np.array([r[2] for r in rows], dtype=object),
             "occupation_major": np.array([r[3] for r in rows]), "org_role": np.array([r[4] for r in rows], dtype=object),
             "org_id": np.array([r[5] for r in rows]), "workplace_area": np.array([r[6] for r in rows], dtype=object)}
    assert A.call("duty_role_org", attrs, None, _key("d", len(rows))).tolist() == [r[7] for r in rows]
    # 〔検収 M1〕まとめた 2 語は W20 の鍵のとおり 2 語に分ける(人ごとの乱数・決定的・半々)
    n = 4000
    split = {"industry_key": np.array(["TR"] * (n // 2) + [""] * (n // 2), dtype=object),
             "industry_major": np.array([7] * (n // 2) + [18] * (n // 2)),
             "org_sector": np.full(n, "", dtype=object),
             "occupation_major": np.array([occ["I"]] * (n // 2) + [occ["F"]] * (n // 2)),
             "org_role": np.full(n, "正社員", dtype=object), "org_id": np.full(n, -1),
             "workplace_area": np.full(n, "stage", dtype=object)}
    w = A.call("duty_role_org", split, None, _key("s", n))
    assert set(w[: n // 2].tolist()) == {"電車運転士", "車掌"} and set(w[n // 2:].tolist()) == {"警察官", "消防士"}
    assert (w[: n // 2] == "電車運転士").mean() == pytest.approx(0.5, abs=0.04)
    assert np.array_equal(w, A.call("duty_role_org", split, None, _key("s", n)))
    assert set(w.tolist()) | {r[7] for r in rows if r[7]} <= set(A.DUTY_WORDS)
    assert "運転士・車掌" not in A.DUTY_WORDS and "警察官・消防士" not in A.DUTY_WORDS
    assert set(A.DUTY_WORDS_NOT_IN_W20) == {"店長", "補充", "配送作業員", "警備員"}


def test_weekly_hours():
    tb = _tables_b()
    st = _status_codes(["regular", "part_time", "executive", "regular"])
    h = A.call("weekly_hours", {"emp_status": st, "occupation_major": np.array([1, 3, 1, 11]),
                                "sex": np.array([0, 1, 0, 0])}, tb, _key("h", 4))
    assert h[0] == pytest.approx(160 * 12 / A.WEEKS_PER_YEAR, abs=0.01)  # 〔検収 L8〕換算は 1 つ
    assert h[1] == pytest.approx(5 * 15 * 12 / A.WEEKS_PER_YEAR, abs=0.01)
    assert np.isnan(h[2]) and np.isnan(h[3])  # 役員・職業が分類不能=空欄


# ================================================================================ 段 5
def test_money_functions_are_pure_and_follow_blank_rules():
    tb = _tables_b()
    n = 4000
    rng = np.random.default_rng(3)
    st = _status_codes(rng.choice(["regular", "dispatched", "part_time", "executive", "self_employed", ""], n))
    attrs = {"emp_status": st, "occupation_major": rng.integers(0, 12, n), "sex": rng.integers(0, 2, n),
             "age": rng.integers(15, 80, n)}
    before = {k: v.copy() for k, v in attrs.items()}
    seen: list[str] = []

    def hook(ev, args):
        if ev == "open" and seen is not None and isinstance(args[0], str):
            seen.append(args[0])

    k = _key("wage", n)
    A.call("wage_monthly", attrs, tb, k)  # 遅れて読まれる import を先に済ませる
    sys.addaudithook(hook)
    m1 = A.call("wage_monthly", attrs, tb, k)
    a1 = A.call("wage_annual", attrs, tb, k)
    h1 = A.call("wage_hourly", attrs, tb, k)
    n_reads = len(seen)
    seen = None  # type: ignore[assignment]
    assert n_reads == 0
    assert np.array_equal(m1, A.call("wage_monthly", attrs, tb, k))
    for c, v in before.items():
        assert np.array_equal(attrs[c], v), c
    words = np.array([*A.EMP_STATUS, ""], dtype=object)[np.where(st >= 0, st, len(A.EMP_STATUS))]
    blank = ~np.isin(words, ["regular", "dispatched", "part_time"]) | (attrs["occupation_major"] >= 11)
    assert (m1[blank] == -1).all() and (a1[blank] == -1).all() and (h1[blank] == -1).all()
    assert (m1[~blank] > 0).all() and (a1[~blank] >= 12 * m1[~blank]).all()
    gen = ~blank & np.isin(words, ["regular", "dispatched"])
    assert m1[gen].min() >= 80_000 and m1[gen].max() <= 900_000  # 階級の幅の中(比は 1)
    pt = ~blank & (words == "part_time")
    assert (h1[pt] > 0).all()
    with pytest.raises(ValueError):
        tb.wage_level[0, 0, 0] = 1.0  # 表は書き込み禁止
    for blank_fn in ("wallet_cash", "card_holding", "account_holding"):
        assert (A.call(blank_fn, {"age": attrs["age"]}, tb, k) == -1).all()


def test_household_assets_zero_share_tilt_and_debt():
    tb = _tables_b()
    n = 20000
    ha = {"hh_type": np.full(n, 2), "head_age": np.full(n, 40)}
    k = _key("sav", n)
    sv = A.call("household_savings", ha, tb, k)
    assert np.array_equal(sv, A.call("household_savings", ha, tb, k))
    assert (sv == 0).mean() == pytest.approx(0.10, abs=0.01)  # 貯蓄保有率 90%
    pos = sv[sv > 0]
    cls = A.savings_class(tb, pos)
    w = tb.sav_freq[2] * tb.sav_rate_cls[2] / 100.0
    assert np.bincount(cls, minlength=5) / pos.size == pytest.approx(w / w.sum(), abs=0.015)  # 階級の度数そのまま
    assert pos[cls == 4].min() >= 20_000_000  # 最上の階級は下の端より上(Pareto)
    ha["household_savings"] = sv
    dep = A.call("household_deposits", ha, tb, k)
    assert (dep <= sv).all() and dep[sv > 0].sum() == pytest.approx(sv.sum() * 3 / 8, rel=1e-3)
    debt = A.call("household_debt", ha, tb, k)
    assert (debt >= 0).all() and set(np.unique(debt[debt > 0])) == {round(2_000_000 / 0.3)}
    # 傾け: 平均を上げると高い階級が増える
    lam = M.solve_tilt(w, tb.sav_cls_mean[2], 15_000_000)
    assert lam > 0
    bad = {"hh_type": np.array([-1, 1]), "head_age": np.array([40, -1])}
    assert (A.call("household_savings", bad, tb, _key("b", 2)) == -1).all()


def test_consumer_credit_adults_only():
    tb = _tables_b()
    n = 20000
    age = np.r_[np.full(n // 2, 30), np.full(n // 2, 19)]
    cc = A.call("consumer_credit", {"age": age}, tb, _key("cc", n))
    assert (cc[n // 2:] == 0).all()
    assert (cc[: n // 2] > 0).mean() == pytest.approx(0.1, abs=0.01)
    assert set(np.unique(cc[cc > 0])) <= set(A.JICC_CLASS_MEAN_YEN)


def test_build_money_distributes_household_assets_to_adults():
    tb = _tables_b()
    people = {"person_id": np.arange(6), "kind": np.array(["resident"] * 5 + ["commuter"], dtype=object),
              "age": np.array([40, 38, 10, 70, 16, 30]), "sex": np.array([0, 1, 0, 1, 1, 0]),
              "household_id": np.array([0, 0, 0, 1, 2, -1]),
              "relation": np.array(["head", "spouse", "child", "head", "head", ""], dtype=object),
              "emp_status": _status_codes(["regular", "part_time", "", "", "", "regular"]),
              "occupation_major": np.array([2, 3, -1, -1, -1, 1])}
    hh = {"household_id": np.array([0, 1, 2]), "family_type": np.array(["112", "3", "3"], dtype=object),
          "head_age": np.array([40, 70, 16])}
    p, h = M.build_money(people, hh, tb, 5)
    assert p["asset_share"].tolist() == [0.5, 0.5, 0.0, 1.0, 1.0, 1.0]
    assert p["savings"][0] + p["savings"][1] == pytest.approx(h["savings"][0], abs=1)
    assert p["savings"][2] == 0 and p["money_basis"][5] == "commuter_own_household_total"
    assert h["hh_type"].tolist() == ["multi", "single", "single"]
    assert (p["wallet_cash"] == -1).all() and (p["card_holding"] == -1).all()


# ================================================================================ 段 6
def test_residence_capacity_and_known_places_laws():
    n = 20000
    rng = np.random.default_rng(4)
    rp = rng.integers(0, 6, n)
    age = rng.integers(25, 80, n)
    k = _key("y", n)
    y = A.call("residence_years", {"residence_period": rp, "age": age}, None, k)
    assert np.isfinite(y).all() and (y <= age + 1).all()
    assert (y[rp == 1] < 1).all() and ((y[rp == 2] >= 1) & (y[rp == 2] < 5)).all() and (y[rp == 5] >= 20).all()
    c = A.call("place_capacity", {"age": age}, None, _key("c", n))
    assert c.mean() == pytest.approx(25.0, abs=0.3) and c.min() >= 5 and c.max() <= 60  # 約 25 か所
    assert c.std() == pytest.approx(7.5, abs=0.4)
    ys = np.array([20 / 52.1775 * f for f in (0.5, 1, 4, 16, 64)])
    L = A.call("known_places", {"place_capacity": np.full(5, 25), "residence_years": ys}, None, _key("L", 5))
    slope = np.polyfit(np.log(ys[1:]), np.log(L[1:]), 1)[0]
    assert slope == pytest.approx(A.HEAPS_EXPONENT, abs=0.03) and L[1] == 25  # 20 週で容量・t^0.6
    assert A.call("known_places", {"place_capacity": np.array([25]), "residence_years": np.array([np.nan])}, None,
                  _key("L", 1))[0] == 25
    sh = P.rank_shares(np.arange(1, 31), np.full(30, 30))
    assert sh.sum() == pytest.approx(1.0) and np.polyfit(np.log(np.arange(1, 31)), np.log(sh), 1)[0] == \
        pytest.approx(-A.RANK_EXPONENT)


def _toy_world():
    xy = np.array([[0, 0], [100, 0], [200, 0], [300, 0], [400, 0]])
    dist = (np.abs(xy[:, None, 0] - xy[None, :, 0])).astype(np.uint16)
    P_ = 40
    poi = {"poi_id": np.array([f"p{j}" for j in range(P_)], dtype=object),
           "cat": np.array(["food", "shop", "nightlife", "leisure", "office"] * 8, dtype=object),
           "subcat": np.array(["", "convenience", "", "park", ""] * 8, dtype=object),
           "cell": (np.arange(P_) // 5) % 5}
    return dist, poi


def test_familiar_places_rules_and_chunk_independence(monkeypatch):
    dist, poi = _toy_world()
    people = {"person_id": np.arange(6), "kind": np.array(["resident"] * 4 + ["commuter"] * 2, dtype=object),
              "age": np.array([30, 10, 45, 70, 30, 40]), "home_cell": np.array([0, 1, 2, 3, -1, -1]),
              "work_cell": np.array([4, -1, -1, -1, 2, 3]),
              "workplace_area": np.array(["stage", "", "outside_ward", "", "stage", "stage"], dtype=object),
              "known_places": np.array([30, 5, 30, 30, 20, 20]), "place_capacity": np.array([20, 20, 20, 20, 20, 20]),
              "young_child_household": np.zeros(6, dtype=bool)}
    pl, cnt = P.familiar_places(9, people, poi, dist)
    pid = pl["person_id"]
    for p in range(6):
        m = pid == p
        assert np.unique(pl["rank"][m]).size == m.sum()  # 順位は重ならない
        pois = pl["poi_index"][m]
        assert np.unique(pois[pois >= 0]).size == (pois >= 0).sum()  # 同じ店を 2 回載せない
    office = np.flatnonzero(poi["cat"] == "office")
    assert not np.isin(pl["poi_index"], office).any()  # 事務所は載らない
    child = pl["poi_index"][(pid == 1) & (pl["poi_index"] >= 0)]
    assert not np.isin(child, np.flatnonzero(poi["cat"] == "nightlife")).any()  # 子どもに夜の店は無い
    assert cnt["familiar_target"][1] == 5 and cnt["listed_places"][1] == 5  # L=5 < C=20 → 5 か所
    # 住民 0(舞台で働く): 家と勤め先の錨+両側・住民 2(区の外で働く)=職場の側は外・外から来る人=家の側は外
    assert {"home", "work"} <= set(pl["place_kind"][pid == 0].tolist())
    assert cnt["outside_places"][2] == (20 - 2) // 2 and cnt["outside_places"][4] == (20 - 2 + 1) // 2
    assert "home" not in set(pl["place_kind"][pid == 4].tolist())
    vs = pl["visit_share"][(pid == 0)]
    rk = pl["rank"][(pid == 0)]
    assert np.allclose(vs, P.rank_shares(rk, np.full(rk.size, 30)))
    assert (cnt["short_of_target"] == 0).all()
    monkeypatch.setattr(P, "CHUNK", 2)
    pl2, _ = P.familiar_places(9, people, poi, dist)
    for k in pl:
        assert np.array_equal(pl[k], pl2[k]), k  # 塊の大きさに依らない
    pl3, c3 = P.familiar_places(9, people, poi, dist, arm="distance_only")  # 腕の口
    assert not np.isin(pl3["poi_index"], office).any() and np.array_equal(c3["listed_places"], cnt["listed_places"])
    kid = pl3["poi_index"][(pl3["person_id"] == 1) & (pl3["poi_index"] >= 0)]
    assert not np.isin(kid, np.flatnonzero(poi["cat"] == "nightlife")).any()  # 年齢の制限はどの腕でも残る
    with pytest.raises(ValueError):
        P.affinity_matrix(poi["cat"], poi["subcat"], arm="bogus")


@pytest.mark.parametrize("arm", P.AFFINITY_ARMS)
def test_nightlife_is_zero_under_20_and_love_hotel_under_18(arm):
    """〔検収 L1〕夜の店は 20 歳未満 0(カラオケを除く)・ラブホテルは 18 歳未満 0=人の年齢で切る(18・19 歳の負の対照)。"""
    dist, _ = _toy_world()
    P_ = 30
    cat = np.array(["nightlife"] * 10 + ["hotel"] * 10 + ["food"] * 10, dtype=object)
    sub = np.array(["club"] * 5 + ["karaoke"] * 5 + ["love_hotel"] * 10 + [""] * 10, dtype=object)
    poi = {"poi_id": np.array([f"q{j}" for j in range(P_)], dtype=object), "cat": cat, "subcat": sub,
           "cell": np.arange(P_) % 5}
    ages = np.array([17, 18, 19, 20, 21, 25])
    n = ages.size
    people = {"person_id": np.arange(n), "kind": np.full(n, "resident", dtype=object), "age": ages,
              "home_cell": np.full(n, 2), "work_cell": np.full(n, -1), "workplace_area": np.full(n, "", dtype=object),
              "known_places": np.full(n, 60), "place_capacity": np.full(n, 60), "young_child_household": np.zeros(n, bool)}
    pl, _cnt = P.familiar_places(3, people, poi, dist, arm=arm)
    pid, pi = pl["person_id"], pl["poi_index"]
    club = np.flatnonzero((cat == "nightlife") & (sub != "karaoke"))
    lh = np.flatnonzero(sub == "love_hotel")
    for k, a in enumerate(ages):
        got = pi[(pid == k) & (pi >= 0)]
        if a < P.NIGHTLIFE_MIN_AGE:
            assert not np.isin(got, club).any(), a
        if a < P.LOVE_HOTEL_MIN_AGE:
            assert not np.isin(got, lh).any(), a
    assert np.isin(pi[(pid >= 3) & (pi >= 0)], club).any()  # 20 歳以上には載りうる(正の対照)


def test_commute_facts():
    dist, _poi = _toy_world()
    mode, path = P.commute_facts(np.array(["resident", "resident", "resident", "commuter", "resident"], dtype=object),
                                 np.array(["stage", "home", "outside_ward", "stage", ""], dtype=object),
                                 np.array([0, 1, 3, -1, 2]), np.array([4, 1, -1, 1, -1]), dist, np.array([2]))
    assert mode.tolist() == ["walk", "home", "rail", "rail", ""]
    assert path.tolist() == [400, 0, 100, 100, -1]


# ================================================================================ 段 7
def test_outside_strata_layers_and_blanks():
    org = {"codes": np.array(["13114", "14101"], dtype=object), "names": np.array(["中野区", "横浜市鶴見区"], dtype=object),
           "workers": np.array([100.0, 50.0]), "students": np.array([10.0, 0.0]), "total": np.array([110.0, 50.0]),
           "inside": {}}
    pop = np.zeros((2, 2, len(X.AGE5_LABELS)))
    pop[:, :, 5] = 1000.0
    frame = [{"layer": "visitors_inbound", "value": [43000, 85000], "mark": "引", "source": "s"},
             {"layer": "transfer_only", "value": [700000, 800000], "mark": "引", "source": "s"},
             {"layer": "through_jr", "value": [460000, 460000], "mark": "引", "source": "s"},
             {"layer": "visitors_metro_private_business", "value": None, "mark": "空欄", "source": "—"},
             {"layer": "visitors_domestic_outside_metro", "value": None, "mark": "空欄", "source": "—"}]
    st = X.outside_strata(org=org, pop=pop, missing=[], commuters={"origin_muni": np.array(["13114", "13113"]),
                                                                   "sex": np.array([0, 1]), "age": np.array([30, 40])},
                          ring_age16_sex=np.ones((1, 16, 2)), ring_keys=["13113001001"], frame_rows=frame)
    lay = np.asarray(st["layer"]).astype(str)
    assert (lay == "commuter").sum() == 2 and (lay == "potential_visitor").sum() == 4 and (lay == "ring").sum() == 32
    assert (lay == "student_in").sum() == 1 and (lay == "inbound").sum() == len(X.JNTO_2025) + 1
    assert all(v is None for v in st["appearance_prob"].tolist())  # 出現の確からしさは空欄
    for blank in ("visitors_metro_private_business", "visitors_domestic_outside_metro", "bodiless_contact"):
        i = int(np.flatnonzero(lay == blank)[0])
        assert st["count"][i] is None and st["count_low"][i] is None and st["mark"][i] == "空欄"
    inb = lay == "inbound"
    assert sum(st["count_low"][inb]) == pytest.approx(43000, abs=1)
    assert not np.asarray(st["has_bodies"])[lay != "commuter"].any()
    pv = lay == "potential_visitor"
    assert set(np.round(np.array(st["inflow_weight"][pv], dtype=float), 4).tolist()) == {round(110 / 160, 4),
                                                                                        round(50 / 160, 4)}


def test_outside_ring_total_and_missing_origins_are_renormalized():
    """〔検収 L3・L6〕表に無い流入元は除いて重みの和 1・輪の和は渡した値(段 1 の枠)に合う。"""
    org = {"codes": np.array(["13114", "22131", "14101"], dtype=object),
           "names": np.array(["中野区", "浜松市中区", "横浜市鶴見区"], dtype=object),
           "workers": np.array([100.0, 30.0, 50.0]), "students": np.zeros(3), "total": np.array([100.0, 30.0, 50.0]),
           "inside": {}}
    pop = np.ones((3, 2, len(X.AGE5_LABELS)))
    st = X.outside_strata(org=org, pop=pop, missing=["22131"], commuters={"origin_muni": np.array([], dtype=object),
                                                                          "sex": np.array([], dtype=int),
                                                                          "age": np.array([], dtype=int)},
                          ring_age16_sex=np.full((2, 16, 2), 2.0), ring_keys=["a", "b"], frame_rows=[], ring_total=100.0)
    lay = np.asarray(st["layer"]).astype(str)
    pv = lay == "potential_visitor"
    codes = set(np.asarray(st["origin_code"])[pv].tolist())
    assert codes == {"13114", "14101"}  # 表に無い符号は行にしない
    w = {c: x for c, x in zip(np.asarray(st["origin_code"])[pv].tolist(), np.array(st["inflow_weight"][pv], float))}
    assert w["13114"] + w["14101"] == pytest.approx(1.0)  # 和 1 に正規化し直す
    assert sum(np.array(st["count"][lay == "ring"], float)) == pytest.approx(100.0, abs=1e-3)
    assert X.MUNI_CODE_2025["22131"][0] == "22138" and X.MUNI_CODE_2025["22137"][0] == "22140"


def test_module_tables_are_read_only():
    """〔検収 L7〕モジュールの表は書き換えられない。"""
    from shibuya.build.pop import w21_checks as WCk

    for t in (WCk.ECEN_MAJOR_OF_KEY, WCk.CENSUS_TO_ECEN5, B.WORLD_COLUMNS, X.MUNI_CODE_2025, A.DUTY_SPLIT_SHARE):
        with pytest.raises(TypeError):
            t["x"] = 1  # type: ignore[index]


# ================================================================================ 守り
@pytest.mark.parametrize("row,token", [("#45", "together_time"), ("#47", "kakei"), ("#49", "jutaku_tochi"),
                                       ("#50", "consideration_set"), ("#16", "jinryu"), ("#57", "research_cache/r99")])
def test_read_guard_stops_verify_side_tables(tmp_path, row, token):
    p = tmp_path / "data" / Path(token) / "x.csv" if "/" in token else tmp_path / "data" / f"{token}_x.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("a\n", encoding="utf-8")
    g = S.W21Guard.for_build(tmp_path / "data", out=tmp_path / "out")
    g.allow.add(S._norm(p))  # 許可の一覧に足しても検証側の語で開く前に止まる
    with pytest.raises(S.VerificationSideError) as e:
        g.check(p)
    assert row in str(e.value)
    with g.active():
        with pytest.raises(S.VerificationSideError):
            p.read_bytes()


def test_read_guard_r99_copy_is_blocked_and_pop41b_copy_is_listed(tmp_path):
    g = S.W21Guard.for_build(DATA, out=tmp_path)
    with pytest.raises(S.VerificationSideError):
        g.check(DATA / "research_cache" / "r99" / "ecensus2021_t6-2_industry_status_muni.xlsx")
    src = S.source("ecen21_t6_2")
    assert src.rel.startswith("research_cache/pop41b/")
    assert all(s.side == "build" for s in S.SOURCES_B)
    toks = [t for _r, t in S.verify_tokens()]
    for s in S.SOURCES_B:
        for rel in (s.rel, s.derived_rel or ""):
            assert not any(t in rel.lower() for t in toks), rel


def test_check_out_b_protects_v2_base_and_existing_dirs(tmp_path):
    data = tmp_path / "data"
    world = data / "world" / "v2"
    base = data / "world" / "v2_stage_4-1"
    for d in (world, base, data / "world" / "v2_stage_2-4"):
        d.mkdir(parents=True)
    for bad in (world, world / "x", base, base / "y", data / "world" / "v2_stage_2-4"):
        with pytest.raises(B.ProtectedOutputErrorB):
            B.check_out_b(data, bad, world, base)
    B.check_out_b(data, data / "world" / "v2_stage_4-1b", world, base)
    B.check_out_b(data, tmp_path / "elsewhere", world, base)
    assert B.main(["--out", str(base), "--data", str(data)]) == 2
    # 読み口の守り: 段 1〜3 の資産は読めるが、書き込みのモードは出力先の下だけ
    (base / "w21_persons.parquet").write_bytes(b"x")
    out = data / "world" / "v2_stage_4-1b"
    g = S.W21Guard.for_build(data, world=world, out=out, extra_dirs=(base,))
    with g.active():
        assert g.read_bytes(base / "w21_persons.parquet") == b"x"
        with pytest.raises(S.NotAllowedError):
            (base / "w21_persons.parquet").write_bytes(b"y")
        out.mkdir(parents=True, exist_ok=True)
        (out / "ok.txt").write_bytes(b"z")
    assert (base / "w21_persons.parquet").read_bytes() == b"x"


# ================================================================================ 実データ
REAL = pytest.mark.requires_data("world_v2")
#: golden(記録 pop41b/README.md §資産・seed 20260909・既定の腕)。
GOLDEN_COUNTS = {"residents": 42642, "commuters": 173150, "people": 215792, "seated": 136537}
GOLDEN_BUILD_HASH_B = "34798bd5d9b67dbeca81457187f8698e9a22ea520c0ba01b3df04fd10160c58f"


def _need_real() -> None:
    if not (DATA / "world" / B.BASE_ASSET / "w21_manifest.json").exists():
        pytest.skip("requires_data: 段 1〜3 の資産 v2_stage_4-1 が無い")
    for s in (*S.SOURCES, *S.SOURCES_B):
        for parts in (s.path, s.derived):
            if parts and not DATA.joinpath(*parts).exists():
                pytest.skip(f"requires_data: 材料が無い({'/'.join(parts[:2])})")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    _need_real()
    out = tmp_path_factory.mktemp("w21b")
    _res, man = B.build_b(DATA, out)
    return out, man


@REAL
def test_real_two_builds_are_byte_identical(built, tmp_path):
    out, man = built
    base = DATA / "world" / B.BASE_ASSET
    before = {f: _sha(base / f) for f in (*B.BASE_FILES, "w21_manifest.json")}
    B.build_b(DATA, tmp_path)
    for f in (*B.OUTPUTS_B, B.MANIFEST_B, "W21b.header.json"):
        assert _sha(out / f) == _sha(tmp_path / f), f
    assert {f: _sha(base / f) for f in before} == before  # 段 1〜3 の資産は変わらない


@REAL
def test_real_golden_counts_and_hash(built):
    _out, man = built
    for k, v in GOLDEN_COUNTS.items():
        assert man["counts"][k] == v, k
    assert man["w21b_build_hash"] == GOLDEN_BUILD_HASH_B
    assert man["stage_version"] == "1.1.0" and man["population_seed"] == B.W.DEFAULT_SEED
    assert man["base"]["w21_build_hash"] == "ca823451cad3f57b5a2636b65a6cc94806e9a62f9b7a9b7dd6546370c97f00c0"


@REAL
def test_real_structure_and_checks(built):
    out, _man = built
    c = json.loads((out / "w21_checks_b.json").read_text(encoding="utf-8"))
    assert {"workers", "seats", "roles", "duty_role", "rights", "relations", "money", "prior", "outside", "commute",
            "blanks"} <= set(c)
    s = c["seats"]["total"]
    assert s["filled"] + s["vacant"] == s["seats"] and s["filled"] + s["overflow"] == s["people"]
    p = pq.read_table(out / "w21_people.parquet").to_pydict()
    pid = np.array(p["person_id"])
    assert np.array_equal(pid, np.arange(pid.size)) and not any(p["synthetic"])
    sup = np.array(p["supervisor_id"])
    head = np.array(p["is_org_head"])
    org = np.array(p["org_index"])
    assert (sup[head] == -1).all() and (sup[(org >= 0) & ~head] >= 0).all()
    r = pq.read_table(out / "w21_rights_initial.parquet").to_pydict()
    assert set(r["kind"]) <= {"employ", "own", "lease"} and "licence" not in r["kind"]
    closed = np.array(r["in_closed_table"])
    assert set(np.array(r["object_kind"])[~closed].tolist()) == {"store"}
    assert all(v is None for v in r["since_ns"]) and all(v is None for v in r["cause"])
    rel = pq.read_table(out / "w21_relations_initial.parquet").to_pydict()
    assert set(rel["kind"]) == {1, 2} and (np.array(rel["u"]) != np.array(rel["v"])).all()
    x = pq.read_table(out / "w21_outside.parquet").to_pydict()
    assert all(v is None for v in x["appearance_prob"])
    i = x["layer"].index("visitors_metro_private_business")
    assert x["count"][i] is None and x["count_low"][i] is None
    assert c["prior"]["capacity_mean"] == pytest.approx(25.0, abs=0.2)
    # 〔検収 M2〕②群の担当は勤め先が舞台の中の体だけ
    duty = np.array(p["duty_role"]).astype(str)
    area = np.array(p["workplace_area"]).astype(str)
    assert (area[duty != ""] == "stage").all()
    assert not np.isin(duty, ["運転士・車掌", "警察官・消防士"]).any()
    # 〔検収 L3・L6〕流入元は 2025 の表に全部ある・輪の和は段 1 の枠の行と同じ
    o = c["outside"]
    assert o["missing_origin_codes"] == [] and o["origins_in_2025_table"] == o["origins"]
    ring = sum(v for v, layer in zip(x["count"], x["layer"]) if layer == "ring")
    assert ring == pytest.approx(o["ring_frame_value"], abs=0.01)
    # 〔検収 L2〕通勤の道のりは種類で分ける
    assert set(c["commute"]["path_m"]) == {"walk_resident_home_to_work", "rail_commuter_station_to_work",
                                           "rail_resident_home_to_station"}


@REAL
def test_real_rights_rows_pass_engine_grant(built):
    """〔検収 L9〕閉じた表の行は engine の ``Rights.grant`` が全部受け付け、店の持ち主の行(閉じた表の外)ははじかれる。"""
    from shibuya.engine.rights.ledger import Right, Rights

    out, _man = built
    r = pq.read_table(out / "w21_rights_initial.parquet").to_pydict()
    closed = np.array(r["in_closed_table"])
    book = Rights(capacity=int(closed.sum()))
    n_ok = n_bad = 0
    for k in range(len(r["right_id"])):  # 逐次: 行の数ぶん(試験だけ)
        cp = None if r["counterparty_kind"][k] == "" else (r["counterparty_kind"][k], int(r["counterparty_id"][k]))
        kw = dict(holder=(r["holder_kind"][k], int(r["holder_id"][k])), object=(r["object_kind"][k],
                  int(r["object_id"][k])), kind=r["kind"][k], since_ns=r["since_ns"][k], until_ns=r["until_ns"][k],
                  counterparty=cp, source=r["source"][k], cause=None if r["cause"][k] is None else
                  (r["cause"][k]["t_ns"], r["cause"][k]["seq"]))
        if closed[k]:
            book.grant(Right(**kw))
            n_ok += 1
        else:
            with pytest.raises(ValueError):
                Right(**kw)
            n_bad += 1
    assert n_ok == int(closed.sum()) and n_bad == int((~closed).sum()) and len(book) == n_ok
    assert all(v is None for v in r["cause"])



@REAL
def test_real_materials_and_world_columns(built):
    out, man = built
    toks = [t for _r, t in S.verify_tokens()]
    for rel in man["read"]:
        assert not any(t in rel.lower() for t in toks), rel
        assert "pt2018" not in rel and "pt6_" not in rel
    assert all(s["side"] == "build" for s in man["sources"])
    assert "odpt_survey_value" not in B.WORLD_COLUMNS["w12_external_nodes.parquet"]
    assert not any(c.startswith("odpt") for c in B.WORLD_COLUMNS["w12_external_nodes.parquet"])
    assert man["verify_side_rows"] == [r.row for r in S.VERIFY_SIDE]


def test_default_build_is_unchanged():
    assert "W21b" not in build_run.ALL_STAGES and "W21" not in build_run.ALL_STAGES and POP_STAGES == ("W16",)


def test_activation_tool_shape():
    """活性化の道具(``pop41b/tools/stage_pop41b.py``)は段 1〜3 の道具の plan 以下を使い、書くファイルは段 4〜7 の出力。"""
    import importlib.util

    tool = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "pop41b" / "tools" / "stage_pop41b.py"
    spec = importlib.util.spec_from_file_location("stage_pop41b", tool)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    assert set(mod.W21B_FILES) == {*B.OUTPUTS_B, B.MANIFEST_B, "W21b.header.json"}
    assert mod.MANIFEST == "MANIFEST.sha256" and callable(mod.P41.cmd_apply) and callable(mod.cmd_stage)
