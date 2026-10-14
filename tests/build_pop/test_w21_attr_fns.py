"""W21 段 3「属性から作る関数」(``attr_fns``)の単体。

- 純粋(世界を読まない=守りの間に ``open`` が 0 回・入力の列と表を書き換えない・同じ鍵で同じ値)。
- 空欄の規則(15 歳未満の労働力状態・就業者でない人の産業・公務 S と分類不能 T の ``industry_key``・段 4 までの職務)。
- 写像の表の行の数(産業 20・地位 8・層と役割 11・在学の窓 106 × 11)。
- raking で町丁目 × 男女の周辺に寄る・外から来る人は従業地の表から引く・W20 に渡す 5 属性。
"""

from __future__ import annotations

import sys

import numpy as np
import pytest

from shibuya.build.pop import attr_fns as A

G = 4  # 町丁目 2 × 男女 2


def _tables() -> A.AttrTables:
    rng = np.random.default_rng(0)
    t = A.AttrTables(
        emp_rate=np.full((2, 17, 4), 0.6),
        status_prior=rng.random((2, 4, 17, 8)) + 0.01,
        industry_prior=rng.random((2, 17, 8, 20)) + 0.01,
        occupation_prior=rng.random((2, 17, 20, 12)) + 0.01,
        workplace_prior=rng.random((5, 20, 4)) + 0.01,
        commuter_industry=rng.random((2, 17, 20)) + 0.01,
        commuter_occupation=rng.random((2, 20, 12)) + 0.01,
        commuter_status=rng.random((20, 5)) + 0.01,
        student_in=np.array([[10.0, 50.0, 30.0], [20.0, 40.0, 0.0]]),
        student_in_ages=np.array([[6, 14], [15, 19], [20, 24]]),
        n_split=(1.0, 1.0),
        chome_labour=np.array([[6, 1, 3], [5, 1, 4], [7, 1, 2], [4, 1, 5]], dtype=float),
        chome_status=np.array([[8, 1, 1]] * G, dtype=float),
        chome_industry=np.ones((G, 20)),
        chome_occupation=np.ones((G, 12)),
        chome_workplace=np.array([[1, 3, 4, 2]] * G, dtype=float),
        chome_school=np.ones((G, 11)),
        chome_school_place=np.ones((G, 3)),
        chome_residence=np.ones((G, 6)),
    )
    return t.freeze()


def _people(n: int = 2000, kind: str = "resident") -> dict[str, np.ndarray]:
    rng = np.random.default_rng(1)
    return {
        "kind": np.full(n, kind, dtype=object),
        "sex": rng.integers(0, 2, n),
        "age": rng.integers(0, 90, n),
        "marital": rng.integers(0, 4, n),
        "chome": rng.integers(0, 2, n),
        "persona_kind": np.full(n, "in_area", dtype=object),
        "role": np.full(n, "resident", dtype=object),
    }


def _key(name: str, n: int) -> A.AttrKey:
    return A.AttrKey(7, f"test.{name}", np.stack([np.arange(n), np.zeros(n, int), np.zeros(n, int)], axis=1))


def _apply_all(attrs, tables):
    a = dict(attrs)
    for name in ("labour_status", "emp_status", "industry_major", "industry_key", "occupation_major",
                 "workplace_kind", "employment_status", "school_kind", "school_place", "residence_period",
                 "w16_kind", "duty_role"):
        a[name] = A.call(name, a, tables, _key(name, a["age"].size))
    return a


def test_mapping_tables_have_the_declared_rows():
    assert len(A.INDUSTRY_KEY_OF_MAJOR) == 20 == len(A.INDUSTRY_MAJORS)
    keys = {v for v in A.INDUSTRY_KEY_OF_MAJOR.values() if v}
    assert keys == {"CN", "MF", "IT", "TR", "WR", "FI", "RE", "PS", "FB", "LS|AM", "ED", "MW", "CS", "SV"}
    assert {m for m, v in A.INDUSTRY_KEY_OF_MAJOR.items() if not v} == {"A", "B", "C", "F", "S", "T"}
    assert len(A.EMPLOYMENT_OF_STATUS) == 8 == len(A.EMP_STATUS)
    assert len(A.W16_KIND) == 11
    assert A.SCHOOL_AGE_WEIGHTS.shape == (106, 11) and not A.SCHOOL_AGE_WEIGHTS.flags.writeable
    assert set(A.REGISTRY) == {"labour_status", "emp_status", "employment_status", "industry_major", "industry_key",
                               "occupation_major", "workplace_kind", "school_kind", "school_place",
                               "residence_period", "w16_kind", "duty_role", "student_in_sex", "student_in_age",
                               "w16_employment"}
    assert len(A.W16_EMPLOYMENT_OF) == 6
    for f in A.REGISTRY.values():
        assert f.version and f.inputs and callable(f.fn)


def test_functions_are_pure_and_deterministic():
    t = _tables()
    p = _people()
    before = {k: v.copy() for k, v in p.items()}
    opened: list[str] = []

    def hook(ev, args):  # 世界も材料も読まない(open が 0 回)
        if ev == "open" and opened is not None and isinstance(args[0], str):
            opened.append(args[0])

    _apply_all(p, t)  # 一度呼んで遅れて読まれる import を済ませる(import の open を数えない)
    sys.addaudithook(hook)
    a1 = _apply_all(p, t)
    n_open = len(opened)
    opened = None  # type: ignore[assignment]
    a2 = _apply_all(p, t)
    assert n_open == 0
    for k, v in before.items():
        assert np.array_equal(p[k], v), k
    for k in a1:
        assert np.array_equal(a1[k], a2[k]), k
    with pytest.raises(ValueError):
        t.emp_rate[0, 0, 0] = 1.0  # 表は書き込み禁止


def test_blank_rules():
    t = _tables()
    a = _apply_all(_people(), t)
    young = a["age"] < 15
    assert (a["labour_status"][young] == -1).all() and (a["labour_status"][~young] >= 0).all()
    not_emp = a["labour_status"] != 0
    for c in ("emp_status", "industry_major", "occupation_major", "workplace_kind"):
        assert (a[c][not_emp] == -1).all(), c
    assert (a["industry_key"][not_emp] == "").all() and (a["employment_status"][not_emp] == "").all()
    ind = a["industry_major"]
    st = np.isin(ind, [A.INDUSTRY_MAJORS.index(m) for m in "ABCFST"])
    assert (a["industry_key"][st] == "").all() and (a["industry_key"][(ind >= 0) & ~st] != "").all()
    assert (a["duty_role"] == "").all()
    sp = a["school_place"] >= 0
    assert (a["age"][sp] >= 15).all() and np.isin(a["school_kind"][sp], [2, 3, 4, 5]).all()
    assert (a["w16_kind"] == 3).all()
    # 居住期間は年齢を越えない(20 年以上は 20 歳以上だけ)
    assert (a["age"][a["residence_period"] == A.RESIDENCE.index("ge20")] >= 20).all()


def test_rake_draw_moves_counts_to_the_group_margins():
    n = 4000
    rng = np.random.default_rng(3)
    prior = rng.random((n, 3)) + 0.05
    group = rng.integers(0, 2, n)
    share = np.array([[0.7, 0.2, 0.1], [0.1, 0.3, 0.6]])
    k, info = A.rake_draw(prior, group, share, rng.random(n))
    assert info["residual"] < 1e-6
    for g in range(2):
        got = np.bincount(k[group == g], minlength=3) / (group == g).sum()
        assert np.abs(got - share[g]).max() < 0.03
    # 重みの無い人は空欄
    prior[0] = 0.0
    k2, _ = A.rake_draw(prior, group, share, rng.random(n))
    assert k2[0] == -1


def test_commuters_use_workplace_tables_and_are_employed():
    t = _tables()
    p = _people(500, kind="commuter")
    p["chome"][:] = -1
    p["age"] = np.maximum(p["age"], 15)
    a = dict(p)
    a["emp_status"] = np.full(500, -1)
    for name in ("labour_status", "industry_major", "emp_status", "industry_key", "occupation_major",
                 "employment_status", "workplace_kind", "school_kind", "residence_period"):
        a[name] = A.call(name, a, t, _key(name, 500))
    assert (a["labour_status"] == 0).all()
    assert (a["industry_major"] >= 0).all() and (a["occupation_major"] >= 0).all()
    assert np.isin(a["emp_status"], [0, 1, 2, 3, 5]).all()
    # 常住地から見た表の無い属性は空欄
    assert (a["workplace_kind"] == -1).all() and (a["school_kind"] == -1).all() and (a["residence_period"] == -1).all()


def test_missing_input_columns_are_refused():
    with pytest.raises(KeyError):
        A.call("emp_status", {"kind": np.array(["resident"]), "age": np.array([30])}, _tables(), _key("x", 1))


def test_calendar_inputs_are_the_five_w20_attributes():
    a = _apply_all(_people(50), _tables())
    a["kind"] = a["w16_kind"]
    ci = A.calendar_inputs(a)
    assert list(ci) == ["kind", "age", "industry_key", "employment_status", "duty_role"]
    assert all(v.shape == (50,) for v in ci.values())


def test_incoming_students_draw_sex_age_and_school_kind_and_blank_the_rest():
    """〔検収 L6〕外から来る通学者: 男女と年齢は表の階級から・在学の種類は年齢の窓の在学の 6 区分から・ほかは空欄。"""
    t = _tables()
    n = 3000
    a = {"kind": np.full(n, A.STUDENT_IN_KIND, dtype=object), "chome": np.full(n, -1)}
    key = _key("student_in", n)
    a["sex"] = A.call("student_in_sex", a, t, key)
    a["age"] = A.call("student_in_age", a, t, key)
    assert np.array_equal(a["sex"], A.call("student_in_sex", a, t, key))  # 同じ鍵=同じ人
    # 女の 20〜24 歳は表に 0 人=引かれない・15 歳未満は 6〜14 歳
    assert not ((a["sex"] == 1) & (a["age"] >= 20)).any()
    assert a["age"].min() >= 6 and a["age"].max() <= 24
    share = np.bincount(a["sex"], minlength=2) / n
    assert abs(share[0] - 90 / 150) < 0.03
    a["school_kind"] = A.call("school_kind", a, t, _key("school", n))
    assert (a["school_kind"] >= 0).all() and (a["school_kind"] <= 5).all()  # 在学の 6 区分だけ(未就学・在学していないは無い)
    assert (a["school_kind"][a["age"] <= 11] == 0).all()
    # 住民の関数は外から来る通学者に値を出さない(居住期間・労働力状態は空欄)
    assert (A.call("residence_period", a, t, _key("r", n)) == -1).all()
    assert (A.call("labour_status", dict(a, marital=np.full(n, -1)), t, _key("l", n)) == -1).all()


def test_w16_employment_maps_the_five_words_and_blank_to_non_employed():
    """〔親の判断=W20 との接続〕employment_status → W16 の employment の 6 値(None と空欄は非就業)。"""
    es = np.array(["regular", "non_regular", "executive", "self_employed", "family_worker", "", None], dtype=object)
    got = A.call("w16_employment", {"employment_status": es}, _tables(), _key("e", es.size))
    assert got.tolist() == ["正規", "非正規", "役員", "自営業主", "家族従業者", "非就業", "非就業"]


def test_negative_control_tables_are_read_only():
    """〔検収 L3〕表は書き換えられない(写像は MappingProxyType・配列は書き込み禁止)。"""
    from shibuya.build.pop import w21_attrs as WA
    from shibuya.build.pop import w21_build as WB
    from shibuya.build.pop import w21_frame as WF
    from shibuya.build.pop import w21_households as WH
    from shibuya.build.pop import w21_tables as WT

    for m in (WH.COMPOSITION, WH.LEVEL_CLASS, WH.HEAD_SEX_FIXED, WB.RELATION_WORDS, WA.VOCAB, WT.GROUP_OF_TYPE,
              WT.COARSE_OF_TYPE, A.INDUSTRY_KEY_OF_MAJOR, A.W16_EMPLOYMENT_OF, WF.FRAME_ROWS[0], _tables().md5):
        with pytest.raises(TypeError):
            m["x"] = 1  # type: ignore[index]
    with pytest.raises(TypeError):
        WF.FRAME_ROWS[4]["reference"]["value"] = 0  # 入れ子も
    for arr in (WH._SLOTS, WT.AGE16_EDGES, WT.MARITAL3_OF4, A.SCHOOL_AGE_WEIGHTS):
        with pytest.raises(ValueError):
            arr.ravel()[0] = 99
    # 書き換えようとしても元のまま(負の対照の後で表が変わっていない)
    assert WH.COMPOSITION["3"] == ((), None) and WB.RELATION_WORDS["01"] == "head"
