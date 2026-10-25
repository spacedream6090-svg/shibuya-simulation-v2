"""第 4 期 4-1 段 8〜9 と段 10 の材料(W21 の続き=``w21_build_c``)の受入の試験。

- 段 8(点検・合否なし): 分布の表の形と印(構築に使った表/使っていない区分)・二重の検出(植えた二重を見つける=負の対照)・
  別人の検査(同じ属性の組を植えて数える・文まで同じなら区別できない)・多様性の指標の単調性。
- 段 9(見せ方): 事実から決まった形(同じ入力で同じ文)・LLM を呼ばない(AST で llm の口を参照しない)・短い版 ⊂ 長い版
  (共通部分が前=DM4)・数字はお金と時刻だけ(6-1 の計器)・第一言語(日本語/英語の型・ほかは欄だけ)・差し替えの口(差し
  替えた文が読まれる・元は残る)・Big Five は腕(既定は空欄)・CP5-3(名指しを植えると見つかる)・判断の入力への置き場。
- 段 10 の材料: 地位の分けの比が第6-2表どおり・体 → 店の雇用の行が ``Rights.grant`` に通る・W16 の在庫の表。
- 段 9〜10 の関数(``attr_fns``)の純粋さ・読み口の守りの負の対照・出力先の守り。
- 実データ(``requires_data``): 2 回組んで sha256 一致・golden・席の数え直しが段 4 と同じ・個人の文が記録に無い。
"""

from __future__ import annotations

import ast
import hashlib
import json
import sys
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pyarrow.parquet as pq
import pytest

from shibuya.build import run as build_run
from shibuya.build.pop import attr_fns as A
from shibuya.build.pop import w21_build_c as BC
from shibuya.build.pop import w21_check as K
from shibuya.build.pop import w21_checks as WC
from shibuya.build.pop import w21_money as M
from shibuya.build.pop import w21_persona as P
from shibuya.build.pop import w21_port10 as T10
from shibuya.build.pop import w21_sources as S
from shibuya.build.pop import w21_tables as T

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
_INSTR = REPO / "tools" / "instruments"
if str(_INSTR) not in sys.path:
    sys.path.insert(0, str(_INSTR))
from dm_eval import situations as DS  # noqa: E402

REC = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "pop41c"


def _key(name: str, n: int) -> A.AttrKey:
    ids = np.arange(n)
    return A.AttrKey(7, f"test.{name}", np.stack([ids, np.zeros(n, int), np.zeros(n, int)], axis=1))


def _tables_c(split=None) -> A.AttrTablesC:
    sp = np.zeros((20, 3))
    if split is None:
        sp[A.INDUSTRY_MAJORS.index("G")] = (3.0, 1.0, 1.0)
        sp[A.INDUSTRY_MAJORS.index("I")] = (1.0, 2.0, 1.0)
    else:
        sp[:] = split
    return A.AttrTablesC(nationality_names=np.array(["中国", "米国", "フランス", "フィリピン"], dtype=object),
                         nationality_w=np.array([5.0, 3.0, 1.0, 1.0]), status_split=sp).freeze()


# ================================================================================ 登録表と関数(段 9〜10)
def test_registry_has_stage_9_and_10_functions():
    # 〔検収 L9〕段 7 以降の関数の集合を固定(段 7・8 の関数が足されたらここで分かる)
    names = {f.name: (f.stage, f.version) for f in A.REGISTRY.values() if f.stage >= 7}
    assert names == {"nationality": (9, "1.2.0"), "first_language": (9, "1.2.0"), "japanese_level": (9, "1.2.0"),
                     "commuter_status_split": (10, "1.2.0")}
    assert set(A.registry_versions((9, 10))) == set(names)
    # 〔第 4 期 4-3 段 10〕組み立ての版 1.2.0 → 1.3.0(関数の版は不変)
    assert BC.STAGE_VERSION_C == "1.3.0" and BC.STAGE_C == "W21c"
    # 段 1〜3 と段 4〜7 の manifest に載る版の表は変えない
    assert all(f.version == "1.1.0" for f in A.REGISTRY.values() if 4 <= f.stage <= 6)


def test_language_functions_are_pure_and_follow_blank_rules():
    n = 6000
    kind = np.array(["resident"] * 5000 + ["commuter"] * 1000, dtype=object)
    fo = np.zeros(n, dtype=bool)
    fo[:4000] = True
    t = _tables_c()
    opened: list[str] | None = []

    def hook(ev, args):  # 世界も材料も読まない(open が 0 回)
        if ev == "open" and opened is not None and isinstance(args[0], str):
            opened.append(args[0])

    age = np.where(np.arange(n) % 10 == 0, 10, 40)

    def run():
        nat_ = A.call("nationality", {"kind": kind, "is_foreign": fo}, t, _key("nat", n))
        fl_ = A.call("first_language", {"nationality": nat_}, t, _key("fl", n))
        jl_ = A.call("japanese_level", {"nationality": nat_, "age": age}, t, _key("jl", n))
        return nat_, fl_, jl_

    run()  # 一度呼んで遅れて読まれる import を済ませる(import の open を数えない)
    sys.addaudithook(hook)
    nat, fl, jl = run()
    n_open = len(opened)
    opened = None
    nat2, _fl2, _jl2 = run()
    assert n_open == 0
    assert np.array_equal(nat, nat2)
    assert set(nat[4000:5000]) == {A.JAPAN} and set(nat[5000:]) == {""}  # 外から来る人は空欄
    share = {k: float((nat[:4000] == k).mean()) for k in ("中国", "米国", "フランス", "フィリピン")}
    assert share["中国"] == pytest.approx(0.5, abs=0.03) and share["米国"] == pytest.approx(0.3, abs=0.03)
    assert set(fl[nat == "中国"]) == {"zh"} and set(fl[nat == "米国"]) == {"en"} and set(fl[nat == A.JAPAN]) == {"ja"}
    assert set(fl[nat == "フィリピン"]) == {""} and set(fl[nat == ""]) == {""}  # 多言語の国・空欄は空欄
    assert (jl[nat == A.JAPAN] == -1).all() and (jl[age < 18] == -1).all() and (jl[nat == ""] == -1).all()
    m = (nat == "中国") & (age >= 18)
    got = np.bincount(jl[m], minlength=6) / m.sum()
    want = np.asarray(A.JAPANESE_LEVEL_TABLE["中国"]) / 100.0
    assert np.abs(got - want).max() < 0.04
    m = (nat == "フランス") & (age >= 18)  # 表に無い国籍は「その他」の行
    got = np.bincount(jl[m], minlength=6) / m.sum()
    assert np.abs(got - np.asarray(A.JAPANESE_LEVEL_TABLE["その他"]) / 100.0).max() < 0.08
    for v in (A.JAPANESE_LEVEL_TABLE.values()):
        assert sum(v) == pytest.approx(100.0, abs=0.15)
    assert len(A.JAPANESE_LEVELS) == 6 and all(len(v) == 6 for v in A.JAPANESE_LEVEL_TABLE.values())


def test_commuter_status_split_follows_table_6_2_ratios():
    n = 30000
    kind = np.array(["commuter"] * (n - 1000) + ["resident"] * 1000, dtype=object)
    se = A.EMP_STATUS.index("self_employed")
    st = np.full(n, se)
    st[:2000] = A.EMP_STATUS.index("regular")
    ind = np.full(n, A.INDUSTRY_MAJORS.index("G"))
    ind[20000:25000] = A.INDUSTRY_MAJORS.index("S")  # 公務=第6-2表(民営)に行が無い=分けない
    t = _tables_c()
    out = A.call("commuter_status_split", {"kind": kind, "emp_status": st, "industry_major": ind}, t, _key("sp", n))
    assert np.array_equal(out[:2000], st[:2000])  # ほかの地位は元のまま
    assert (out[n - 1000:] == se).all()  # 住民は元のまま
    assert (out[20000:25000] == se).all()  # 公務は元のまま
    m = np.arange(n)
    m = (m >= 2000) & (m < 20000)
    words = np.array(A.EMP_STATUS)[out[m]]
    share = {w: float((words == w).mean()) for w in A.STATUS_SPLIT_WORDS}
    assert share == pytest.approx({"executive": 0.6, "self_employed": 0.2, "family_worker": 0.2}, abs=0.02)
    out2 = A.call("commuter_status_split", {"kind": kind, "emp_status": st, "industry_major": ind}, t, _key("sp", n))
    assert np.array_equal(out, out2)


def test_status_split_table_reads_the_table_6_2_columns():
    items = tuple(f"{lab}|従業者数_男女計" for lab in ("1_個人業主", "2_無給の家族従業者", "3_有給役員", "41_無期雇用者"))
    rows = [["0", "x", "2", "G", "", [10, 2, 30, 100]], ["0", "x", "2", "I", "", [5, 1, 4, 50]],
            ["0", "x", "3", "G", "39", [1, 1, 1, 1]]]
    tab = T10.status_split_table(rows, items)
    assert tab.shape == (20, 3)
    assert tab[A.INDUSTRY_MAJORS.index("G")].tolist() == [30, 10, 2]  # 有給役員・個人業主・無給の家族
    assert tab[A.INDUSTRY_MAJORS.index("S")].sum() == 0


# ================================================================================ 段 8 点検
def test_fit_cells_shape_and_max_diff():
    r = WC.fit_cells(np.array([10, 30, 60]), np.array([20, 30, 50]), ["a", "b", "c"])
    assert r["cells"] == 3 and r["srmse"] > 0 and r["jsd"] > 0
    assert r["max_diff"]["cell"] in ("a", "c") and abs(r["max_diff"]["diff"]) == pytest.approx(0.1)
    with pytest.raises(ValueError):
        WC.fit_cells(np.ones(3), np.ones(2), ["a", "b", "c"])
    same = WC.fit_cells(np.array([1, 2]), np.array([2, 4]), ["a", "b"])
    assert same["srmse"] == pytest.approx(0.0) and same["jsd"] == pytest.approx(0.0)


def test_tuple_duplicates_finds_planted_duplicates_and_indistinguishable_groups():
    keys = np.array(["a", "b", "c", "a", "d", "a", "c"], dtype=object)
    r = WC.tuple_duplicates(keys)
    assert r["people_in_shared_tuples"] == 5 and r["shared_groups"] == 2 and r["largest_group"] == 3
    text = np.array([0, 1, 2, 0, 3, 0, 4])  # a の 3 人は文も同じ・c の 2 人は文が違う
    r = WC.tuple_duplicates(keys, text)
    assert r["indistinguishable_groups"] == 1 and r["indistinguishable_people"] == 3
    r = WC.tuple_duplicates(np.array(["x", "y"], dtype=object), np.array([0, 0]))
    assert r["people_in_shared_tuples"] == 0 and r["indistinguishable_groups"] == 0


def test_diversity_is_monotone_in_clones():
    rng = np.random.default_rng(0)
    base = {"a": rng.integers(0, 1000, 2000), "b": rng.integers(0, 1000, 2000)}
    d0 = WC.diversity(base)
    clone = {k: np.r_[v, np.repeat(v[:1], 2000)] for k, v in base.items()}  # 同じ人を 2,000 体足す=複製
    d1 = WC.diversity(clone)
    assert d1["joint"]["entropy_bits"] < d0["joint"]["entropy_bits"]
    assert d1["joint"]["shared_share"] > d0["joint"]["shared_share"]
    codes = lambda c: np.stack([np.asarray(v) for v in c.values()], axis=1)  # noqa: E731
    p0 = WC.pair_distance(codes(base), 20000, 1, "t")
    p1 = WC.pair_distance(codes(clone), 20000, 1, "t")
    assert p1["zero_share"] > p0["zero_share"] and p1["mean"] < p0["mean"]
    assert WC.pair_distance(codes(base), 20000, 1, "t") == p0  # 決定的
    assert WC.entropy_bits(np.zeros(5)) == 0.0 and WC.entropy_bits(np.array([0, 1])) == pytest.approx(1.0)


def _people_small() -> dict:
    """合成の小さな人口(住民 4・外から来て働く人 3)。"""
    return {
        "person_id": np.arange(7), "kind": np.array(["resident"] * 4 + ["commuter"] * 3, dtype=object),
        "home_cell": np.array([5, 5, 6, 7, -1, -1, -1]), "household_id": np.array([0, 0, 1, 2, -1, -1, -1]),
        "origin_muni": np.array(["13113"] * 4 + ["13112", "13113", "13114"], dtype=object),
        "duty_role": np.array(["", "店長", "", "", "駅員", "", "補充"], dtype=object),
        "org_index": np.array([0, 0, -1, -1, -1, 1, 1]), "age": np.array([30, 28, 40, 70, 30, 30, 50]),
        "sex": np.array([0, 1, 0, 1, 0, 0, 1]), "relation": np.array(["head", "spouse", "head", "head", "", "", ""],
                                                                      dtype=object),
        "occupation_major": np.array(["C", "D", "C", "", "C", "C", "D"], dtype=object),
        "org_code": np.array(["o0", "o0", "", "", "", "o1", "o1"], dtype=object),
        "workplace_area": np.array(["stage", "stage", "home", "", "stage", "stage", "stage"], dtype=object),
        "work_cell": np.array([9, 9, 6, -1, 9, 9, 9]),
    }


def test_double_rows_find_planted_doubles():
    p = _people_small()
    rights = {"holder_kind": np.array(["agent"] * 4, dtype=object), "holder_id": np.array([0, 1, 5, 6]),
              "object_kind": np.array(["org"] * 4, dtype=object), "object_id": np.array([0, 0, 1, 1]),
              "kind": np.array(["employ"] * 4, dtype=object)}
    org = {"seats": np.array([2, 2]), "filled": np.array([2, 2])}
    keep = {"w16_total": 0, "rows_removed_stage10": 0, "rows_kept": 0, "w21_duty_double_with_kept_transport": {}}
    d = K.double_rows(p, rights, org, keep)
    assert d["person_id_duplicates"] == 0 and d["people_with_two_or_more_employ_rows"] == 0
    assert d["commuters_with_stage_home"] == 0 and d["orgs_over_capacity"] == 0 and d["no_seat_rule_but_seated"] == 0
    assert d["commuters_from_ward_ring"] == 1
    # 負の対照: 植えた二重(同じ人の番号・同じ人の雇用の行 2 つ・席の超過・席のある駅員・家のある外から来る人)を見つける
    p2 = {k: np.array(v, copy=True) for k, v in p.items()}
    p2["person_id"][6] = 5
    p2["org_index"][4] = 1
    p2["home_cell"][5] = 3
    r2 = {k: np.r_[v, v[:1]] for k, v in rights.items()}
    d2 = K.double_rows(p2, r2, {"seats": np.array([2, 1]), "filled": np.array([2, 2])}, keep)
    assert d2["person_id_duplicates"] == 1 and d2["people_with_two_or_more_employ_rows"] == 1
    assert d2["orgs_over_capacity"] == 1 and d2["no_seat_rule_but_seated"] == 1 and d2["commuters_with_stage_home"] == 1


def test_uniqueness_counts_planted_same_tuples():
    p = _people_small()
    hh = {"household_id": np.array([0, 1, 2]), "family_group": np.array(["couple", "single", "single"], dtype=object),
          "size": np.array([2, 1, 1])}
    places = {"person_id": np.array([0, 1, 5, 6]), "rank": np.array([3, 3, 3, 3]),
              "place_kind": np.array(["poi"] * 4, dtype=object), "poi_index": np.array([1, 2, 3, 3])}
    n = 7
    u = K.uniqueness(p, hh, places, np.arange(n), np.arange(n))
    assert u["people_in_shared_tuples"] == 0 and u["distinct"] == n
    # 植える: 6 番を 5 番と同じ属性の組に(年齢・性別・職業・勤め先・常住地・なじみの場所)
    p2 = {k: np.array(v, copy=True) for k, v in p.items()}
    for c in ("age", "sex", "occupation_major", "org_code", "origin_muni", "workplace_area", "work_cell"):
        p2[c][6] = p2[c][5]
    u2 = K.uniqueness(p2, hh, places, np.arange(n), np.arange(n))
    assert u2["people_in_shared_tuples"] == 2 and u2["shared_groups"] == 1 and u2["indistinguishable_groups"] == 0
    same_text = np.arange(n)
    same_text[6] = same_text[5]
    u3 = K.uniqueness(p2, hh, places, same_text, np.arange(n))
    assert u3["indistinguishable_groups"] == 1 and u3["indistinguishable_people"] == 2
    assert u3["without_familiar_places"]["people_in_shared_tuples"] >= 2


def _derived(dims, items, table) -> S.Derived:
    return S.Derived("t", tuple(dims), tuple(items), {k: np.asarray(v, dtype=float) for k, v in table.items()})


def test_distribution_rows_shape_and_basis_marks():
    """分布の点検の表の形(行の名・印・区分の数)。構築に使っていない区分の行は 4 つ(従業地 第15-1表・2025 第15-1表 2・
    東京都 第1表)。"""
    rng = np.random.default_rng(3)
    n_res, n_com = 60, 40
    n = n_res + n_com
    p = {"person_id": np.arange(n), "kind": np.array(["resident"] * n_res + ["commuter"] * n_com, dtype=object),
         "age": rng.integers(20, 70, n), "sex": rng.integers(0, 2, n),
         "home_chome_key": np.array(["k0"] * n_res + [""] * n_com, dtype=object),
         "workplace_area": np.array(["stage"] * n, dtype=object),
         "occupation_major": np.array([A.OCCUPATION_MAJORS[i % 11] for i in range(n)], dtype=object),
         "industry_major": np.array([A.INDUSTRY_MAJORS[i % 18] for i in range(n)], dtype=object),
         "household_id": np.r_[np.repeat(np.arange(30), 2), np.full(n_com, -1)],
         "relation": np.array(["head", "spouse"] * 30 + [""] * n_com, dtype=object),
         "emp_status": np.array(["regular"] * n, dtype=object), "org_index": np.r_[np.zeros(50), -np.ones(50)]}
    hh = {"size": np.full(30, 2), "family_group": np.array(["couple"] * 30, dtype=object),
          "family_type": np.array(["111"] * 30, dtype=object)}
    tg = SimpleNamespace(age16_sex=np.ones((1, 16, 2)), hh_size=np.ones((1, 7)), hh_group=np.ones((1, 6)))
    ward = SimpleNamespace(hh_type_size=np.ones((16, 7)))
    t3 = SimpleNamespace(commuter_industry=np.ones((2, 17, 20)), commuter_occupation=np.ones((2, 20, 12)))
    e15_items = ["0_総数"] + [f"{L}_x" for L in A.OCCUPATION_MAJORS]
    e15 = _derived(("男女", "年齢"), e15_items, {(sx, f"{a:02d}_y"): np.ones(13) for sx in ("1_男", "2_女")
                                                for a in range(1, 18)})
    hlab = [f"{i:02d}_{15 + 5 * (i - 1)}～" for i in range(1, 12)]
    clab = ("1_子供なし", "21_子供が1人", "22_子供が2人", "23_子供が3人", "24_子供が4人以上")
    tab = {(h, c, "0_総数", "0_総数"): np.ones(5) for h in hlab for c in clab}
    tab.update({("00_総数", "2_子供あり", f"{k}_z", "0_総数"): np.ones(5) for k in range(1, 9)})
    b15 = _derived(("夫の年齢", "子", "最年少", "最年長"), ["0_総数", "1", "2", "3", "R1"], tab)
    items62 = tuple(f"{lab}|従業者数_男女計" for lab in ("1_個人業主", "2_無給の家族従業者", "3_有給役員", "41_無期雇用者",
                                                    "42_有期雇用者", "5_臨時雇用者"))
    rows62 = [["0", "x", "2", "G", "", [1, 1, 1, 10, 1, 1]]]
    nat = np.array([A.JAPAN] * n_res + [""] * n_com, dtype=object)
    nat[:5] = "中国"
    rows = K.distribution_rows(people=p, households=hh, tg=tg, ward=ward, tables3=t3, e15=e15, b15=b15,
                               nationality=nat, japanese_level=np.where(nat == "中国", 2, -1),
                               juki_t3={"中国": 5.0, "米国": 2.0}, juki_t1={"中国": 5.0, "その他": 2.0},
                               rows62=rows62, items62=items62, stage_keys=["k0"])
    assert len(rows) == 13 and all({"name", "basis", "table", "srmse", "jsd", "max_diff"} <= set(r) for r in rows)
    nb = [r["name"] for r in rows if r["basis"] == WC.BASIS_NOT_BUILD]
    assert len(nb) == 4 and any("第15-1表" in r["table"] for r in rows if r["basis"] == WC.BASIS_NOT_BUILD)
    assert {r["basis"] for r in rows} == {WC.BASIS_BUILD, WC.BASIS_NOT_BUILD}
    assert rows[2]["cells"] == 2 * 17 * 12 and "occupation_within_age_jsd" in rows[2]


def test_couple_children_counts():
    p = {"household_id": np.array([0, 0, 0, 0, 1, 1, 2]), "relation": np.array(
        ["head", "spouse", "child", "child", "head", "spouse", "head"], dtype=object),
         "age": np.array([40, 38, 8, 3, 70, 68, 30]), "sex": np.array([1, 0, 0, 1, 0, 1, 0])}
    c = K.couple_children(p)
    assert c["husband_age"].tolist() == [38, 70] and c["children"].tolist() == [2, 0] and c["youngest"].tolist() == [3, -1]


# ================================================================================ 段 9 見せ方
def _facts(n: int = 4, *, first_language=None, nationality=None, names=None) -> P.PersonaFacts:
    fl = first_language or ["ja", "ja", "en", ""]
    nat = nationality or [A.JAPAN, A.JAPAN, "米国", ""]
    cols = {
        "person_id": np.arange(n), "kind": np.array(["resident", "resident", "resident", "commuter"][:n], dtype=object),
        "age": np.array([34, 8, 45, 52][:n]), "sex": np.array([1, 0, 0, 1][:n]),
        "nationality": np.array(nat[:n], dtype=object), "first_language": np.array(fl[:n], dtype=object),
        "japanese_level": np.array([-1, -1, 1, -1][:n]),
        "home_chome": np.array(["例町一丁目", "例町一丁目", "例町三丁目", ""][:n], dtype=object),
        "institution": np.zeros(n, dtype=bool), "origin_name": np.array(["", "", "", "例市"][:n], dtype=object),
        "tenure": np.array(["owned", "owned", "private_rent", ""][:n], dtype=object),
        "residence_period": np.array(["y5_10", "since_birth", "lt1", ""][:n], dtype=object),
        "residence_years": np.array([6.5, 8.0, 0.4, np.nan][:n]),
        "labour": np.array(["employed", "", "employed", "employed"][:n], dtype=object),
        "emp_status": np.array(["regular", "", "part_time", "executive"][:n], dtype=object),
        "occupation": np.array(["C", "", "D", "A"][:n], dtype=object),
        "industry": np.array(["G", "", "I", "M"][:n], dtype=object),
        "org_role": np.array(["正社員", "", "パート・アルバイト", "代表"][:n], dtype=object),
        "duty_role": np.array(["", "", "補充", ""][:n], dtype=object),
        "org_name": np.array((names or ["(株)例", "", "(株)例商店", "(株)例食堂"])[:n], dtype=object),
        "org_sector": np.array(["業務SaaS", "", "食品小売", "カフェ"][:n], dtype=object),
        "org_size": np.array(["10-19", "", "1-4", "100-299"][:n], dtype=object),
        "work_area": np.array(["stage", "", "stage", "stage"][:n], dtype=object),
        "work_chome": np.array(["例町二丁目", "", "例町三丁目", "例町四丁目"][:n], dtype=object),
        "is_org_head": np.array([False, False, False, True][:n]), "is_dept_head": np.array([False, False, False, True][:n]),
        "dept_mates": np.array([6, -1, 0, 3][:n]), "has_supervisor": np.array([True, False, True, False][:n]),
        "weekly_hours": np.array([37.4, np.nan, 18.0, 40.0][:n]),
        "school_kind": np.array(["none", "elementary", "none", ""][:n], dtype=object),
        "school_place": np.array(["", "", "", ""][:n], dtype=object),
        "commute_mode": np.array(["walk", "", "walk", "rail"][:n], dtype=object),
        "commute_m": np.array([900, -1, 300, 241][:n]),
        "wage_monthly": np.array([312_000, -1, 80_000, -1][:n]), "wage_annual": np.array([4_620_000, -1, 980_000, -1][:n]),
        "savings": np.array([3_870_000, 0, 0, 152_000_000][:n]), "debt": np.array([0, 0, 12_000_000, 0][:n]),
        "consumer_credit": np.array([0, 0, 500_000, 0][:n]), "hh_size": np.array([2, 3, 1, -1][:n]),
        "hh_savings": np.array([7_740_000, 9_000_000, 0, -1][:n]), "outside_places": np.array([3, 0, 0, 2][:n]),
        "org_index": np.array([10, -1, 11, 12][:n]),
    }
    members = {"owner": np.array([0, 1, 1]), "cat": np.array([0, 2, 2]), "age": np.array([36, 40, 38]),
               "sex": np.array([0, 0, 1])}
    places = {"owner": np.array([0, 0, 0, 0, 2]), "rank": np.array([3, 4, 5, 6, 3]),
              "poi_index": np.array([100, 101, 102, 103, 104]),
              "name": np.array(["例の喫茶店", "例の書店", "例の公園", "例の食堂", "Cafe 109"], dtype=object),
              "cat_ja": np.array(["飲食店", "書店", "公園", "飲食店", "飲食店"], dtype=object),
              "cat_en": np.array(["restaurant", "bookshop", "park", "restaurant", "restaurant"], dtype=object)}
    return P.PersonaFacts(cols, members, places)


def test_persona_is_deterministic_and_short_is_prefix_of_long():
    f = _facts()
    a = P.build_tables(f)
    b = P.build_tables(_facts())
    for v in P.VERSIONS:
        assert np.asarray(a[v]["text"]).tolist() == np.asarray(b[v]["text"]).tolist()
    for s, lg in zip(a["short"]["text"].tolist(), a["long"]["text"].tolist()):
        assert lg.startswith(s) and len(lg) >= len(s)
    assert (np.asarray(a["long"]["chars"]) >= np.asarray(a["short"]["chars"])).all()
    t = a["long"]["text"].tolist()
    assert t[0].startswith("人物: 三十代前半の女性。") and "\n暮らし: 例町一丁目で夫と暮らしている。" in t[0]
    assert t[1].startswith("人物: 八歳の男の子。") and "学校: 小学校に通っている。" in t[1]
    assert "お金:" not in a["short"]["text"][1]  # 未成年の本人の貯蓄の行は出さない
    assert "借入" not in a["long"]["text"][1] and "世帯の貯蓄はおよそ900万円。" in a["long"]["text"][1]  # 借入の行も 18 歳以上
    assert t[2].startswith("Person: a man in his late forties. Nationality: the United States. First language: English.")
    assert "Responsible for restocking the shelves." in t[2] and "Language: speaks Japanese fluently." in t[2]
    assert t[3].startswith("人物: 五十代前半の女性。") and "暮らし: 例市に住んでいる。" in t[3]
    assert "貯蓄はおよそ15,000万円。" in t[3]  # 1 億円以上は万円の単位(2 桁の有効数字)


def test_persona_languages_and_blank_templates():
    # 〔第 4 期 4-3 段 10・仮-33 (7)〕型の無い言語の人は日本語の型で代えて印(substitute_ja)を付ける(前の版は欄だけ=
    # lang "" ・text_status no_template)。本当の第一言語は first_language の欄と文の人物の行に残る
    f = _facts(first_language=["ja", "zh", "en", ""], nationality=[A.JAPAN, "中国", "米国", ""])
    tab = P.build_tables(f)["long"]
    assert tab["lang"].tolist() == ["ja", "ja", "en", "ja"]
    assert tab["lang_basis"].tolist() == ["first_language", P.SUBSTITUTE_BASIS, "first_language", "blank_assumed_ja"]
    assert tab["text_status"].tolist() == ["built"] * 4 and tab["first_language"][1] == "zh"
    assert tab["text"][1].startswith("人物:") and "第一言語は中国語" in tab["text"][1] and tab["chars"][1] > 0
    assert tab["text"][2].startswith("Person:") and "人物:" not in tab["text"][2]
    # 外国籍で第一言語が空欄(多言語の国)も日本語の型で代える・国籍も空欄(外から来る人)は日本語の型
    f2 = _facts(first_language=["ja", "", "en", ""], nationality=[A.JAPAN, "フィリピン", "米国", ""])
    tab2 = P.build_tables(f2)["long"]
    assert tab2["lang"].tolist() == ["ja", "ja", "en", "ja"]
    assert tab2["lang_basis"][1] == P.SUBSTITUTE_BASIS and "国籍はフィリピン" in tab2["text"][1]
    with pytest.raises(ValueError):
        P.render(f, "zh", "short")


def test_numbers_are_only_money_and_time_by_the_6_1_meter():
    tabs = P.build_tables(_facts())
    masked = P.build_tables(_facts(), mask_names=True)
    for v in P.VERSIONS:
        for t in masked[v]["text"].tolist():
            assert DS.numbers_outside_money_time(t) == 0, t
    # 名の中の数字(なじみの場所の名 Cafe 109)は名のまま=伏せない文では計器が数える(名の分を分けられる)
    assert DS.numbers_outside_money_time(tabs["long"]["text"][2]) == 1
    assert DS.numbers_outside_money_time(masked["long"]["text"][2]) == 0
    assert P.CHARS_PER_TOKEN["ja"] == DS.CHARS_PER_TOKEN


def _llm_refs(src: str) -> list[str]:
    """llm の口への参照(import・名・属性・関数とクラスの名・動的 import の文字列・docstring でない文字列の
    「.llm」「llm.」)。"""
    tree = ast.parse(src)
    docs = {id(n.body[0].value) for n in ast.walk(tree)
            if isinstance(n, (ast.Module, ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)) and n.body
            and isinstance(n.body[0], ast.Expr) and isinstance(n.body[0].value, ast.Constant)}
    out: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            mods = [a.name for a in node.names] + ([node.module] if isinstance(node, ast.ImportFrom) and node.module
                                                    else [])
            out += [m for m in mods if "llm" in (m or "").lower()]
        elif isinstance(node, ast.Name) and "llm" in node.id.lower():
            out.append(node.id)
        elif isinstance(node, ast.Attribute) and "llm" in node.attr.lower():
            out.append(node.attr)
        elif isinstance(node, (ast.FunctionDef, ast.ClassDef)) and "llm" in node.name.lower():
            out.append(node.name)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            v = node.value.lower()
            if ".llm" in v or "llm." in v or v.strip() == "llm":
                out.append(node.value)
    return out


def test_persona_does_not_reference_llm_ports():
    src = (REPO / "src" / "shibuya" / "build" / "pop" / "w21_persona.py").read_text(encoding="utf-8")
    assert _llm_refs(src) == []
    # 負の対照(検収 L3): 直接の import・相対 import・importlib と __import__ の動的 import を植えると見つかる
    for planted in ("from shibuya.llm import fleet\n", "import shibuya.llm.fleet\n", "from ...llm import fleet\n",
                    "import importlib\nm = importlib.import_module('shibuya.llm.fleet')\n",
                    "m = __import__('shibuya.llm')\n", "def ask_llm():\n    pass\n"):
        assert _llm_refs(src + "\n" + planted), planted


def test_persona_build_does_not_import_or_call_llm(tmp_path):
    """組み立て(import と ``build_tables``)で ``shibuya.llm`` が読み込まれない・名の照合(``naming_check``=engine を遅れて
    import する)では読み込まれても呼ばれない(実行時の監視=別のプロセス)。"""
    import pickle
    import subprocess

    f = _facts()
    pk = tmp_path / "facts.pkl"
    pk.write_bytes(pickle.dumps(({k: np.array(v) for k, v in f.cols.items()},
                                 {k: np.array(v) for k, v in f.members.items()},
                                 {k: np.array(v) for k, v in f.places.items()})))
    code = (
        "import sys, pickle\n"
        "from shibuya.build.pop import w21_persona as P\n"
        "c, m, pl = pickle.loads(open(%r, 'rb').read())\n" % str(pk) +
        "tab = P.build_tables(P.PersonaFacts(c, m, pl))['long']\n"
        "print('after_build', any(m == 'shibuya.llm' or m.startswith('shibuya.llm.') for m in sys.modules))\n"
        "calls = []\n"
        "def prof(frame, event, arg):\n"
        "    if event == 'call' and ('shibuya' + chr(92) + 'llm' in frame.f_code.co_filename\n"
        "                            or 'shibuya/llm' in frame.f_code.co_filename):\n"
        "        calls.append(frame.f_code.co_name)\n"
        "import shibuya.engine.experiment.checks\n"  # 遅れて読まれる import を先に済ませる(import の実行は数えない)
        "print('llm_loaded_by_engine', 'shibuya.llm' in sys.modules)\n"
        "sys.setprofile(prof)\n"
        "r = P.naming_check(tab, ['例の書店'])\n"
        "sys.setprofile(None)\n"
        "print('naming_found', r['found'], 'llm_calls', len(calls))\n")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, encoding="utf-8", cwd=str(REPO),
                         env={**__import__("os").environ, "PYTHONIOENCODING": "utf-8"})
    assert out.returncode == 0, out.stderr[-2000:]
    assert "after_build False" in out.stdout and "naming_found True llm_calls 0" in out.stdout, out.stdout
    # 宣言: 名の照合の口は engine を import する=engine のパッケージ経由で shibuya.llm が読み込まれる(呼ばれない=上)
    assert "llm_loaded_by_engine True" in out.stdout


def test_override_port_reads_new_text_and_keeps_original():
    tab = P.build_tables(_facts())["long"]
    before = np.asarray(tab["text"]).copy()
    new, man = P.override(tab, [2, 0], ["差し替えた文。\n二行目。", "別の文。"], label="llm_written_arm_test",
                          meta={"model": "なし(試験)", "version": "-"})
    assert new["text"][0] == "別の文。" and new["text"][2] == "差し替えた文。\n二行目。"
    assert new["text_original"][0] == before[0] and new["text_original"][2] == before[2]
    assert new["text_original"][1] is None and new["text"][1] == before[1]
    assert new["text_source"].tolist() == ["override:llm_written_arm_test", "facts", "override:llm_written_arm_test",
                                           "facts"]
    assert new["chars"][0] == len("別の文。") and new["lines"][2] == 2
    assert np.asarray(tab["text"]).tolist() == before.tolist()  # 元の表は書き換えない
    assert man == {"label": "llm_written_arm_test", "rows": 2, "meta": {"model": "なし(試験)", "version": "-"}}
    # 〔検収 L1〕2 回差し替えても事実の文は残る
    new2, _ = P.override(new, [0], ["三つ目の文。"], label="second")
    assert new2["text"][0] == "三つ目の文。" and new2["text_original"][0] == before[0]
    assert new2["text_source"][0] == "override:second"
    # 〔検収 L2〕差し替えた体は text_status が override(〔段 10〕型の無い言語の人も日本語の型で代えた=文がある)
    blank = P.build_tables(_facts(first_language=["ja", "zh", "en", ""], nationality=[A.JAPAN, "中国", "米国", ""]))["long"]
    assert blank["text_status"][1] == "built" and blank["lang_basis"][1] == P.SUBSTITUTE_BASIS
    nb, _ = P.override(blank, [1], ["差し替えた文。"], label="x")
    assert nb["text_status"][1] == "override" and nb["text"][1] == "差し替えた文。"
    assert nb["text_original"][1] == blank["text"][1] and nb["text_status"][0] == "built"
    with pytest.raises(P.PersonaOverrideError):
        P.override(tab, [99], ["x"], label="a")
    with pytest.raises(P.PersonaOverrideError):
        P.override(tab, [0], ["x"], label="")


def test_big_five_is_an_arm_with_blank_default():
    f = _facts()
    tab = P.build_tables(f)["long"]
    for k in P.TIPI_COLUMNS:
        assert np.isnan(np.asarray(tab[k], dtype=float)).all()
    assert not any("TIPI" in t for t in tab["text"].tolist())
    f2 = P.with_big_five(f, [0], [[12, 7, 9, 3, 13]], source="試験の値")
    t2 = P.build_tables(f2)["long"]["text"].tolist()
    assert "性格の自己評価(TIPI-J): 外向性は高め・協調性はふつう・勤勉性はふつう・神経症傾向は低め・開放性は高め。" in t2[0]
    assert not any("TIPI" in t for t in t2[1:])
    assert P.build_tables(f2)["short"]["text"].tolist() == P.build_tables(f)["short"]["text"].tolist()
    with pytest.raises(P.PersonaOverrideError):
        P.with_big_five(f, [0], [[1, 2, 3, 4, 5]], source="")


def test_cp5_3_naming_by_id_does_not_count_same_name_chains():
    f = _facts()
    # 体 2 の POI(番号 104)は体 0 の POI(番号 100)と同じ名にする=チェーン
    pl = dict(f.places)
    pl["name"] = np.array(["例の喫茶店", "例の書店", "例の公園", "例の食堂", "例の喫茶店"], dtype=object)
    tab = P.build_tables(P.PersonaFacts(f.cols, f.members, pl))["long"]
    by_name = P.naming_check(tab, ["例の喫茶店"])
    assert sorted(h["id"] for h in by_name["hits"]) == [0, 2]  # 名は同じ名の別の店も数える
    by_id = P.naming_check_ids(tab, poi=[100])
    assert by_id["ids"] == [0] and by_id["by_poi"] == {100: 1} and by_id["found"]
    assert P.naming_check_ids(tab, poi=[999])["found"] is False
    assert P.naming_check_ids(tab, org=[11])["ids"] == [2]  # 長い版は勤め先の名を出す
    short = P.build_tables(P.PersonaFacts(f.cols, f.members, pl))["short"]
    assert P.naming_check_ids(short, org=[11])["found"] is False  # 短い版は勤め先の名を出さない
    assert P.naming_check_ids(short, poi=[103])["found"] is False and P.naming_check_ids(tab, poi=[103])["ids"] == [0]
    blank = P.build_tables(_facts(first_language=["ja", "zh", "en", ""], nationality=[A.JAPAN, "中国", "米国", ""]))
    assert np.asarray(blank["long"]["named_org"])[1] == -1


def test_prefix_mismatches_and_read_only_facts():
    t = P.build_tables(_facts())
    assert P.prefix_mismatches(t["short"]["text"], t["long"]["text"]) == 0
    bad = np.asarray(t["long"]["text"], dtype=object).copy()
    bad[0] = "違う頭" + bad[0]
    assert P.prefix_mismatches(t["short"]["text"], bad) == 1
    f = _facts()
    with pytest.raises(TypeError):
        f.cols["age"] = np.zeros(4)  # type: ignore[index]
    with pytest.raises(ValueError):
        f.cols["age"][0] = 1
    src = {"person_id": np.arange(2), "age": np.array([1, 2])}
    P.PersonaFacts(src, {"owner": np.zeros(0)}, {"owner": np.zeros(0)})
    src["age"][0] = 5  # 呼び手の配列は書き込み禁止にしない(view)
    assert src["age"][0] == 5


def test_walk_minutes_share_one_function():
    from shibuya.build.sched import w20_w21_port as WP
    from shibuya.engine.geometry import SPEED_REFERENCE_MS

    assert A.WALK_SPEED_REFERENCE_MS == SPEED_REFERENCE_MS
    t = P.build_tables(_facts())["long"]["text"]
    assert "歩いて11分ほど" in t[0]  # 900 m ÷ 1.34 m/s = 671.6 秒 = 11.2 分 → 四捨五入(丸めた言葉)
    assert WP.lead_minutes(np.array(["walk"], dtype=object), np.array([900])).tolist() == [12]  # 切り上げ(整数の分)


def test_cp5_3_naming_check_finds_planted_names():
    tab = P.build_tables(_facts())["long"]
    r = P.naming_check(tab, ["例の書店"])
    assert r["found"] and [h["id"] for h in r["hits"]] == [0] and r["check"] == "persona_naming"
    assert not P.naming_check(tab, ["どこにも無い店"])["found"]
    planted = P.build_tables(_facts(names=["(株)改変の対象", "", "(株)例商店", "(株)例食堂"]))["long"]
    assert [h["id"] for h in P.naming_check(planted, ["改変の対象"])["hits"]] == [0]


def test_compose_blocks_with_the_engine_compose_and_6_1_lengths():
    from shibuya.engine.decision.port import Candidate, compose

    tabs = P.build_tables(_facts())
    blocks = {"B0": "[B0 共通] 前置き", "B1": "[B1 種別] 住民", "B6": "[B6 起床] 9時の目覚まし"}
    cand = (Candidate(id="a", kind="移動", text="移動する", source="continue", number=1),)
    sb = P.compose_blocks(blocks, tabs["short"]["text"][0], tabs["long"]["text"][0], "short")
    lb = P.compose_blocks(blocks, tabs["short"]["text"][0], tabs["long"]["text"][0], "long")
    s = compose(sb, cand, length="short")
    lg = compose(lb, cand, length="long")
    common = "[B0 共通] 前置き\n[B1 種別] 住民\n"
    assert s.startswith(common) and lg.startswith(common)
    assert s[len(common):].startswith(tabs["short"]["text"][0] + "\n[B6 起床]")
    assert lg[len(common):].startswith(tabs["long"]["text"][0] + "\n[B6 起床]")
    sit = DS.Situation(sid="x", blocks=sb)
    for arm in DS.LENGTH_ARMS:
        r = DS.render(sit, cand, length="short", arm=arm)
        assert r.chars == len(r.text) and r.numbers_outside_money_time == 0
    assert P.compose_blocks(blocks, "", "", "short") == blocks


def test_words_and_money_formats():
    assert [P.kanji_number(x) for x in (1, 10, 11, 20, 26, 105, 1234)] == ["一", "十", "十一", "二十", "二十六", "百五",
                                                                          "千二百三十四"]
    assert [P.english_number(x) for x in (8, 15, 21, 40, 117)] == ["eight", "fifteen", "twenty-one", "forty",
                                                                   "one hundred seventeen"]
    assert P.money_ja(280_000) == "28万円" and P.money_ja(84_000) == "8.4万円" and P.money_ja(1_300_000_000) == "130,000万円"
    assert P.money_ja(5_000) == "5,000円"
    assert P.money_en(280_000) == "¥280,000" and P.money_en(4_600_000) == "¥4.6 million"
    assert P.money_en(28_000_000) == "¥28 million"
    assert P.age_words(34, 1, "ja") == "三十代前半の女性" and P.age_words(47, 0, "en") == "a man in his late forties"
    assert P.age_words(8, 0, "ja") == "八歳の男の子" and P.age_words(15, 1, "en") == "a teenage girl"
    for v in (280_000, 84_000, 1_300_000_000, 5_000):
        assert DS.numbers_outside_money_time(P.money_ja(v)) == 0 and DS.numbers_outside_money_time(P.money_en(v)) == 0
    assert P.ADULT_AGE == M.ADULT_AGE


def test_relation_category_from_the_persons_view():
    got = P.relation_category(np.array(["head", "spouse", "child", "child", "parent", "non_relative"], dtype=object),
                              np.array(["spouse", "head", "head", "child", "head", "head"], dtype=object))
    assert got.tolist() == ["spouse", "spouse", "parent", "sibling", "child", "housemate"]
    assert P.relation_category(np.array(["child_spouse"], dtype=object), np.array(["head"], dtype=object)).tolist() == \
        ["relative"]


# ================================================================================ 段 10 の材料
def test_store_staff_rows_round_robin_head_first_and_engine_grant():
    from shibuya.engine.rights.ledger import Right, Rights
    from shibuya.engine.rights.initial import staff_of_poi

    p = {"person_id": np.arange(6), "org_index": np.array([0, 0, 0, 1, -1, 0]),
         "is_org_head": np.array([False, True, False, True, False, False]),
         "is_dept_head": np.array([False, True, True, True, False, False]),
         "org_role": np.array(["正社員", "店長", "部署長", "代表", "", "パート・アルバイト"], dtype=object),
         "weekly_hours_hint": np.array([40, 40, 40, 40, np.nan, 20.0])}
    rights = {"holder_kind": np.array(["org", "org", "agent"], dtype=object), "holder_id": np.array([0, 0, 1]),
              "object_kind": np.array(["store", "store", "org"], dtype=object), "object_id": np.array([7, 3, 0]),
              "kind": np.array(["own", "own", "employ"], dtype=object)}
    r = T10.store_staff_rows(p, rights)
    assert list(r) == list(T10.O.RIGHT_COLUMNS)
    # 組織 0 の 4 人(頭 1 → 部署長 2 → 0 → 5)を店 3・7 へ順に: 店 3=1・0、店 7=2・5(店の番号の順・店ごとの最初が担当)
    assert np.asarray(r["object_id"]).tolist() == [3, 3, 7, 7]
    assert np.asarray(r["holder_id"]).tolist() == [1, 0, 2, 5]
    assert set(np.asarray(r["in_closed_table"]).tolist()) == {True}
    book = Rights(capacity=8)
    for k in range(len(r["right_id"])):  # 逐次: 行(試験)
        book.grant(Right(holder=(r["holder_kind"][k], int(r["holder_id"][k])),
                         object=(r["object_kind"][k], int(r["object_id"][k])), kind=r["kind"][k],
                         source=r["source"][k]))
    staff = staff_of_poi(book, 10, 0)
    assert staff[3] == 1 and staff[7] == 2 and staff[0] == -1


def test_w16_keep_table_actions():
    kind = np.array([0, 0, 3, 3, 8, 8, 8, 8, 1, 5, 4])
    duty = np.array(["", "", "", "議員", "駅員", "バス運転士", "警察官", "路上生活者", "", "", "指令"], dtype=object)
    syn = np.array([True, False, False, False, False, False, False, False, False, True, True])
    t = T10.w16_keep_table(kind, duty, syn, {"駅員": 3, "警察官": 5}, {"residents": 10, "commuters": 20})
    act = {(r["w16_kind"], r["duty_role"]): r["action"] for r in t["rows"]}
    assert act[(0, "")] == "replace" and act[(3, "")] == "replace" and act[(3, "議員")] == "replace_no_equivalent"
    assert act[(8, "駅員")] == "keep_transport" and act[(8, "バス運転士")] == "keep_transport"
    assert act[(8, "警察官")] == "replace" and act[(8, "路上生活者")] == "keep_no_w21"
    assert act[(1, "")] == "keep_no_w21" and act[(5, "")] == "keep_no_w21" and act[(4, "指令")] == "keep_no_w21"
    assert t["rows_removed_stage10"] == 5 and t["rows_kept"] == 6 and t["w16_total"] == 11
    assert t["w21_duty_double_with_kept_transport"] == {"駅員": 3}


# ================================================================================ 守り
@pytest.mark.parametrize("row,token", [("#11", "pt6_b-4"), ("#16", "jinryu"), ("#17", "passengersurvey"),
                                       ("#42", "kumin_ishiki"), ("#45", "together_time"), ("#47", "kakei"),
                                       ("#49", "jutaku_tochi"), ("#50", "consideration_set"),
                                       ("#57", "research_cache/r99"), ("#58", "hanzai"), ("#59", "/holdout/")])
def test_read_guard_stops_the_11_verify_side_rows(tmp_path, row, token):
    p = tmp_path / "data" / Path(token.strip("/")) / "x.csv" if "/" in token else tmp_path / "data" / f"{token}_x.csv"
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text("a\n", encoding="utf-8")
    g = S.W21Guard.for_build(tmp_path / "data", out=tmp_path / "out")
    g.allow.add(S._norm(p))
    with pytest.raises(S.VerificationSideError) as e:
        g.check(p)
    assert row in str(e.value)


def test_read_guard_language_verify_side_files_are_not_allowed(tmp_path):
    """在留外国人統計と訪日外客の統計の検証側の区分(言語の結果=受入環境のアンケート・行動特性調査の満足度=R-110 §3-5 の
    「検証の候補」)は許可の一覧に無い=開く前に止まる。段 9 が読む東京都の外国人人口の 2 本は一覧にある。"""
    g = S.W21Guard.for_build(DATA, out=tmp_path / "out", extra_sources=S.SOURCES_C)
    r110 = DATA / "research_cache" / "r110"
    for name in ("mlit_ukeire_001998584.pdf", "mlit_ukeire_001998583.pdf", "tokyo_inbound_behavior_2025_bessi2.pdf",
                 "mlit_inbound_002018884.pdf", "zairyu_2025-12_t2_municipality.xlsx"):
        with pytest.raises(S.NotAllowedError):
            g.check(r110 / name)
    for sid in ("jukiki_tokyo_t3_2026_01", "jukiki_tokyo_t1_2026_07", "c20_e15", "c25_b15"):
        s = S.source(sid)
        assert s.side == "build" and g.check(DATA.joinpath(*s.path))
    # 〔検収 L7〕段 1〜7 の守り(extra_sources なし)では、段 8〜10 の 4 本は一覧の外=開く前に止まる(負の対照)
    g17 = S.W21Guard.for_build(DATA, out=tmp_path / "out")
    for sid in ("jukiki_tokyo_t3_2026_01", "jukiki_tokyo_t1_2026_07", "c20_e15", "c25_b15"):
        src_ = S.source(sid)
        for parts in (src_.path, src_.derived):
            if parts:
                with pytest.raises(S.NotAllowedError):
                    g17.check(DATA.joinpath(*parts))
    toks = [t for _r, t in S.verify_tokens()]
    for s in S.SOURCES_C:
        for rel in (s.rel, s.derived_rel or ""):
            assert not any(t in rel.lower() for t in toks), rel


def test_check_out_c_protects_v2_bases_and_existing_dirs(tmp_path):
    data = tmp_path / "data"
    world = data / "world" / "v2"
    base = data / "world" / "v2_stage_4-1b"
    for d in (world, base, data / "world" / "v2_stage_4-1", data / "world" / "v2_stage_2-4"):
        d.mkdir(parents=True)
    for bad in (world, world / "x", base, base / "y", data / "world" / "v2_stage_4-1", data / "world" / "v2_stage_2-4"):
        with pytest.raises(BC.ProtectedOutputErrorC):
            BC.check_out_c(data, bad, world, base)
    BC.check_out_c(data, data / "world" / "v2_stage_4-1c", world, base)
    BC.check_out_c(data, tmp_path / "elsewhere", world, base)
    assert BC.main(["--out", str(base), "--data", str(data)]) == 2


def test_module_tables_and_defaults():
    assert "W21c" not in build_run.ALL_STAGES
    from shibuya.build.sched import w20_w21_port as WP

    for t in (A.NATIONALITY_LANGUAGE, A.JAPANESE_LEVEL_TABLE, A.LANGUAGE_NAMES, P.PLACE_WORDS, P.CHARS_PER_TOKEN,
              BC.WORLD_COLUMNS_C, BC.BASE_FILES_C, T10.W16_KIND_WORDS, WP.OCC_OF_MAJOR, WP.TEACHING_OF_SCHOOL,
              WP.WORKPLACE_OF_AREA, WP.DUTY_ROLE_SPEC_W21):
        with pytest.raises(TypeError):
            t["x"] = 1  # type: ignore[index]
    # 〔第 4 期 4-3 段 10〕16 → 14 行(置き場・W16 の在庫の案・地位の分けを消し、通う駅の口を足した)・段 10 に結ぶ宣言は無い
    assert len(BC.W21C_EXPEDIENTS) == 14 and BC.STAGE10_ROWS_OF_DECLARATIONS == ()
    assert set(A.NATIONALITY_LANGUAGE.values()) - {""} <= set(A.LANGUAGE_NAMES)


# ================================================================================ 実データ
REAL = pytest.mark.requires_data("world_v2")
#: golden(記録 pop41c/README.md §資産・seed 20260909)。
#: 〔第 4 期 4-3 段 10〕1.3.0(段 4〜7 の 1.2.0 の上・型の無い言語を日本語の型で・通う駅の口)で組み直した値。前の値(1.2.0)は
#: persona_built 212897・persona_no_template 2895・w21c_build_hash 36ac56f8290a9f7ac11368b5f8fbfddf85e0748507290d8a16312fcf1f23b122
#: (記録 pop41c)=記録 pop43。
GOLDEN_COUNTS = {"people": 215792, "persona_rows": 215792, "persona_built": 215792, "persona_no_template": 0}
GOLDEN_BUILD_HASH_C = "5936be9caf93f447e2b0dc709243a957ae3d0646521220443e66dedb2b1b5c2c"
#: 段 4〜7 の 1.2.0 の golden(``test_w21_stage4_7.GOLDEN_BUILD_HASH_B`` と同じ)。
GOLDEN_BUILD_HASH_B12 = "1ccbfb048516d45484895398a58e49ab5a8aede960461e821b4d845fb647542b"


def _need_real() -> None:
    if not (DATA / "world" / BC.STAGE13_ASSET / "w21_manifest.json").exists():
        pytest.skip("requires_data: 段 1〜3 の資産 v2_stage_4-1 が無い")
    for s in (*S.SOURCES, *S.SOURCES_B, *S.SOURCES_C):
        for parts in (s.path, s.derived):
            if parts and not DATA.joinpath(*parts).exists():
                pytest.skip(f"requires_data: 材料が無い({'/'.join(parts[:2])})")


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


@pytest.fixture(scope="module")
def base12(tmp_path_factory):
    """〔第 4 期 4-3 段 10〕段 4〜7 を 1.2.0(地位の分けを席の前に)で組んだ置き場(段 1〜3 の資産の写しを足す)。"""
    import shutil

    from shibuya.build.pop import w21_build_b as BB

    _need_real()
    base = tmp_path_factory.mktemp("w21b12")
    BB.build_b(DATA, base)
    s13 = DATA / "world" / BC.STAGE13_ASSET
    for f in ("w21_frame.json", "w21_households.parquet", "w21_persons.parquet", "w21_checks.json", "w21_manifest.json"):
        shutil.copy2(s13 / f, base / f)
    return base


@pytest.fixture(scope="module")
def built(tmp_path_factory, base12):
    out = tmp_path_factory.mktemp("w21c")
    _res, man = BC.build_c(DATA, out, base=base12)
    return out, man


@REAL
def test_real_two_builds_are_byte_identical(built, base12, tmp_path):
    out, _man = built
    base = base12
    before = {f: _sha(base / f) for names in BC.BASE_FILES_C.values() for f in names}
    BC.build_c(DATA, tmp_path, base=base)
    for f in (*BC.OUTPUTS_C, BC.MANIFEST_C, "W21c.header.json"):
        assert _sha(out / f) == _sha(tmp_path / f), f
    assert {f: _sha(base / f) for f in before} == before  # 段 1〜7 の資産は変わらない


@REAL
def test_real_golden_counts_and_hash(built):
    _out, man = built
    for k, v in GOLDEN_COUNTS.items():
        assert man["counts"][k] == v, k
    assert man["w21c_build_hash"] == GOLDEN_BUILD_HASH_C
    assert man["base"]["w21b_build_hash"] == GOLDEN_BUILD_HASH_B12
    assert man["base"]["w21_build_hash"] == "ca823451cad3f57b5a2636b65a6cc94806e9a62f9b7a9b7dd6546370c97f00c0"


@REAL
def test_real_structure_and_instruments(built):
    out, man = built
    c = json.loads((out / "w21_checks_c.json").read_text(encoding="utf-8"))
    k = json.loads((out / "w21_check.json").read_text(encoding="utf-8"))
    assert {"distribution", "doubles", "uniqueness", "diversity", "foreigners"} <= set(k)
    assert k["doubles"]["person_id_duplicates"] == 0 and k["doubles"]["people_with_two_or_more_employ_rows"] == 0
    assert k["diversity"]["dm6_behavior_variance_ratio"] is None
    s10 = c["stage10"]
    # 〔第 4 期 4-3 段 10〕分けは段 4(W21b 1.2.0)が入れた=分けの後の数え直しが段 4 の所属と同じ(前の版は分けの前が同じ)
    assert s10["seat_recount"]["after_matches_stage4"] is True and s10["seat_recount"]["before_matches_stage4"] is False
    assert s10["seat_recount"]["before"]["overflow"] == 34175 and s10["seat_recount"]["overflow_reduction"] > 0
    bd = s10["seat_recount"]["breakdown"]  # 〔検収 中 2〕内訳(候補/候補でない × 得た/失った/勤め先が変わった)
    net = (bd["candidates"]["seated_after"] - bd["candidates"]["seated_before"]
           + bd["others"]["seated_after"] - bd["others"]["seated_before"])
    assert net == s10["seat_recount"]["seated_increase"] and bd["others"]["lost"] > 0
    assert bd["workplace_changed_total"] == bd["candidates"]["workplace_changed"] + bd["others"]["workplace_changed"]
    assert c["persona"]["short_not_prefix"] == 0 and c["persona"]["tipi_filled"] == 0
    long_t = pq.read_table(out / "w21_persona_long.parquet").to_pydict()
    assert len(long_t["person_id"]) == man["counts"]["people"]
    assert all(v is None for v in long_t["text_original"][:1000]) and set(long_t["text_source"]) == {"facts"}
    assert len(long_t["named_poi"]) == len(long_t["person_id"]) and set(long_t["text_status"]) == {"built"}
    assert long_t["lang_basis"].count(P.SUBSTITUTE_BASIS) == 2895  # 型の無い言語の人(前の版の欄だけ 2,895 人)
    for kk in P.TIPI_COLUMNS:
        assert all(v is None or v != v for v in long_t[kk][:1000])
    # 分けの比: 外から来て働く人の候補の地位は第6-2表の比(産業ごとの重みの和)に近い
    sp = pq.read_table(out / "w21c_status_split.parquet").to_pydict()
    assert set(sp["emp_status_before"]) == {"self_employed"}
    assert set(sp["emp_status_after"]) <= set(A.STATUS_SPLIT_WORDS)


@REAL
def test_real_store_staff_rows_pass_engine_grant(built):
    from shibuya.engine.rights.ledger import Right, Rights
    from shibuya.engine.rights.initial import staff_of_poi

    out, _man = built
    r = pq.read_table(out / "w21c_rights_store_staff.parquet").to_pydict()
    book = Rights(capacity=len(r["right_id"]))
    for k in range(len(r["right_id"])):  # 逐次: 行の数ぶん(試験だけ)
        book.grant(Right(holder=(r["holder_kind"][k], int(r["holder_id"][k])),
                         object=(r["object_kind"][k], int(r["object_id"][k])), kind=r["kind"][k],
                         since_ns=r["since_ns"][k], until_ns=r["until_ns"][k], source=r["source"][k]))
    assert len(book) == len(r["right_id"]) > 0
    staff = staff_of_poi(book, 2337, 0)
    assert int((staff >= 0).sum()) == len(set(r["object_id"]))


@REAL
def test_real_w20_attributes_table_is_the_port_output(built):
    out, _man = built
    t = pq.read_table(out / "w21c_w20_attributes.parquet").to_pydict()
    assert set(t) == {"agent_id", "kind", "age", "industry", "duty_role", "occupation", "employment_pool", "employed",
                      "workplace", "school", "work_cell", "school_cell", "home_cell", "lead_min", "census_middles",
                      "place_hint", "shift", "seat_nonworking", "seat_and_school"}
    assert len(t) == 19 and set(t["census_middles"]) == {""} and not any(t["seat_nonworking"])


@REAL
def test_real_materials_are_build_side(built):
    _out, man = built
    toks = [t for _r, t in S.verify_tokens()]
    for rel in man["read"]:
        assert not any(t in rel.lower() for t in toks), rel
        assert "mlit_ukeire" not in rel and "inbound_behavior" not in rel and "zairyu" not in rel
    assert all(s["side"] == "build" for s in man["sources"])
    assert {"research_cache/r110/tokyo_gaikoku_2026_ga26ev0300.csv",
            "research_cache/pop41/derived/c20_e15_01.json"} <= set(man["read"])


def test_record_has_no_personal_text():
    """記録(README と JSON)に個人の文が無い: 例は合成の 1 人(``persona_meter.example``)の文だけ。資産があれば、体の
    長い版の文(1,000 人)がどれも記録に無い。"""
    import importlib.util

    readme = REC / "README.md"
    if not readme.exists():
        pytest.skip("記録 pop41c/README.md が無い")
    spec = importlib.util.spec_from_file_location("persona_meter", REC / "tools" / "persona_meter.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    ex = mod.example()
    text = readme.read_text(encoding="utf-8")
    for v in ex.values():
        for line in v.split("\n"):
            assert line in text, line
    recs = [text] + [p.read_text(encoding="utf-8") for p in REC.glob("*.json")]
    long_p = DATA / "world" / BC.OWN_ASSET_C / "w21_persona_long.parquet"
    if long_p.exists():
        t = pq.read_table(long_p, columns=["text"]).column("text").to_pylist()
        for s in t[:: max(1, len(t) // 1000)]:
            if s:
                assert not any(s in r for r in recs)
