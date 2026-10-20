"""第 3 期 3-1 構築側の段 W20cal(暦 1a・``build.sched.w20_calendar_1a``)の受入の試験。

- 属性から作る関数(:func:`calendar_from_attributes`)は決定的で、体の部分集合でも同じ行になる(人口が変わっても作り直しに
  ならない形=計画 第 4 期の注)。
- 正規は毎週固定・非正規とシフトは週ごとの抽選(鍵=体・週・曜日)・空欄の規則(決まっていない予定・授業の時間帯)・勤務場所の
  種類(職業と duty_role)・始業=出勤+通勤・終業=帰宅−通勤(第 31/36 表の逆算)。
- 検証側の表(第14表・第15-1〜3表・第68-3表)を開かない守り(負の対照)。2-0 の ``read_guard`` の形でも確かめる。
- 実データ(``requires_data("world_v2")``)で 5,000 体の表の形と計器の値(golden は記録 ca31/README.md)。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.sched import trial as TR
from shibuya.build.sched import w20_calendar_1a as W

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"


# ================================================================= 作り物の材料
def _r(wd: float, sat: float, sun: float) -> dict:
    return {"2_平日": {"rate": wd}, "3_土曜日": {"rate": sat}, "4_日曜日": {"rate": sun}}


def _st(sole=1.0, fam=0.0, off=5.0, indef=70.0, fixed=20.0, temp=4.0) -> dict:
    return {"status": {"個人業主": sole, "無給の家族従業者": fam, "有給役員": off, "無期雇用者": indef,
                       "有期雇用者": fixed, "臨時雇用者": temp}}


def materials() -> W.Materials:
    t749 = {"総数": _r(0.82, 0.35, 0.22), "事務従事者": _r(0.86, 0.17, 0.10), "サービス職業従事者": _r(0.76, 0.59, 0.40),
            "輸送・機械運転従事者": _r(0.72, 0.74, 0.55), "保安職業従事者": _r(0.81, 0.72, 0.47),
            "管理的職業従事者": _r(0.70, 0.34, 0.32)}
    t746 = {"0_総数|0_総数": _r(0.82, 0.35, 0.22), "1_うち雇用されている人|0_総数": _r(0.84, 0.33, 0.20),
            "1_うち雇用されている人|1_フルタイム": _r(0.88, 0.32, 0.20),
            "1_うち雇用されている人|2_短時間勤務": _r(0.61, 0.31, 0.19), "2_うち自営業主|0_総数": _r(0.74, 0.54, 0.41)}
    days = {"321_正規の職員・従業員": 242.0, "3221_うちパート": 177.0, "3222_うちアルバイト": 142.0,
            "3223_うち労働者派遣事業所の派遣社員": 211.0, "3224_うち契約社員": 220.0, "322_非正規の職員・従業員": 180.0,
            "31_会社などの役員": 232.0, "1_自営業主": 218.0, "2_家族従業者": 203.0}
    t19 = {f"{k}|0_総数": {"mean_days": v} for k, v in days.items()}
    t62 = {"total": _st(), "majors": {"G": _st(indef=83.0, fixed=11.0, temp=1.0), "M": _st(indef=43.0, fixed=47.0),
                                      "H": _st(sole=0.0, indef=87.0, fixed=11.0, temp=0.2)},
           "middles": {"42": _st(sole=0.0, off=1.0, indef=90.0, fixed=9.0, temp=0.3)}}
    sim = {"IT": {"majors": ["G"], "middles": []}, "FB": {"majors": ["M"], "middles": []},
           "TR": {"majors": ["H"], "middles": []}}
    return W.Materials({"tables": {"74-9": {"rows": t749}, "74-6": {"rows": t746}, "19": {"rows": t19},
                                   "6-2": t62}, "industry_map": {"sim_mapping": sim}})


ANCHOR = TR.load_anchor()


def attrs(n: int = 400, *, seed: int = 0) -> W.Attributes:
    """n 体の作り物(勤務・授業・空欄・duty_role・舞台の外・自宅を混ぜる)。"""
    rng = np.random.default_rng(seed)
    kinds = rng.choice([0, 2, 3, 5, 1, 8], size=n, p=[0.45, 0.05, 0.15, 0.15, 0.15, 0.05])
    agent_id = np.arange(1000, 1000 + n, dtype=np.int64)
    roles = ["", "駅員", "電車運転士", "警察官", "タクシー運転手", "路上生活者"]
    duty = [roles[1 + (i % 5)] if kinds[i] == 8 else "" for i in range(n)]
    occs = ["事務従事者", "サービス職業従事者", "輸送・機械運転従事者", ""]
    cols = {"agent_id": agent_id, "kind": kinds, "age": np.where(kinds == 5, 19, 40),
            "home_cell": np.where(np.isin(kinds, [2, 3]), 7, -1), "work_cell": np.where(np.isin(kinds, [0, 2]), 11, -1),
            "school_cell": np.where(kinds == 5, 13, -1),
            "industry_key": [("IT", "FB", "TR")[i % 3] if kinds[i] in (0, 2) else "" for i in range(n)],
            "duty_role": duty}
    pool = {"occupation_major": [occs[i % 4] for i in range(n)],
            "employment": [("正規", "非正規", "自営業主", "非就業")[i % 4] for i in range(n)],
            "industry_key": ["IT" if i % 2 else "PA" for i in range(n)],
            "workplace_scope": [("in_area", "out_area", "at_home", "none")[i % 4] for i in range(n)],
            "school_stage": [None] * n, "arrival_lead_min": [None if i % 5 == 0 else 20 + i % 40 for i in range(n)]}
    return W.attributes_from_columns(cols, pool)


def build(a: W.Attributes, *, weeks: int = 1) -> dict:
    m = materials()
    emp = W.draw_employment_status(a, m, ANCHOR)
    return W.calendar_from_attributes(a, emp, m, ANCHOR, n_weeks=weeks)


def _subset(a: W.Attributes, idx: np.ndarray) -> W.Attributes:
    def take(v):
        return [v[i] for i in idx] if isinstance(v, list) else np.asarray(v)[idx]

    return W.Attributes(**{f: take(getattr(a, f)) for f in W.Attributes.__dataclass_fields__})


# ================================================================= 属性から作る関数
def test_deterministic_and_subset_invariant():
    """同じ属性なら同じ表・体の部分集合で作っても同じ行(体ごとの鍵=人口が変わっても作り直しにならない)。"""
    a = attrs()
    t1, t2 = build(a)["columns"], build(a)["columns"]
    assert all(np.array_equal(t1[k], t2[k]) for k in t1)
    idx = np.arange(3, a.n, 7)
    sub = build(_subset(a, idx))["columns"]
    rows = (idx[:, None] * W.N_DAYS + np.arange(W.N_DAYS)[None, :]).ravel()
    for k in t1:
        assert np.array_equal(np.asarray(t1[k])[rows], np.asarray(sub[k])), k


def test_rows_columns_and_order():
    a = attrs(50)
    t = build(a, weeks=2)["columns"]
    assert set(t) == set(W.TABLE_SCHEMA.names)
    assert t["agent_id"].size == 50 * 2 * 7
    assert np.array_equal(t["weekday"][:14], np.tile(np.arange(7), 2)) and np.array_equal(t["week"][:14],
                                                                                          np.repeat([0, 1], 7))
    assert (t["placement"] == W.PLACEMENT_BLANK).all() and (t["origin_conv"] == W.ORIGIN_NONE).all()


def test_fixed_every_week_and_weekly_redraws_with_the_body_week_key():
    """正規(毎週固定)は週が変わっても同じ・非正規とシフトは週ごとの抽選(鍵=体・週・曜日)。"""
    a = attrs(600)
    out = build(a, weeks=4)
    t = out["columns"]
    W4 = 4 * 7
    commit = t["commit"].reshape(a.n, 4, 7)
    start = t["start_min"].reshape(a.n, 4, 7)
    rec = t["recurrence"].reshape(a.n, 4, 7)
    fixed = (rec == W.RECUR_FIXED).any(axis=(1, 2))
    weekly = (rec == W.RECUR_WEEKLY).any(axis=(1, 2))
    assert fixed.sum() > 50 and weekly.sum() > 30 and not (fixed & weekly).any()
    for wk in range(1, 4):
        assert np.array_equal(commit[fixed, wk], commit[fixed, 0]) and np.array_equal(start[fixed, wk], start[fixed, 0])
    changed = np.array([not np.array_equal(commit[i, 1], commit[i, 0]) or not np.array_equal(start[i, 1], start[i, 0])
                        for i in np.flatnonzero(weekly)])
    assert changed.mean() > 0.5
    # 鍵: 同じ体・同じ週・同じ曜日なら同じ値(週の数を変えても週 0〜1 の行は同じ)
    t2 = build(a, weeks=2)["columns"]
    assert np.array_equal(t2["start_min"].reshape(a.n, 2, 7), start[:, :2])
    assert W4 == 28
    # 鍵の一様変数: 週が違えば違う値・同じ鍵なら同じ値
    u0 = W.draw_u("day", np.array([5, 6]), 0, 3)
    assert np.array_equal(u0, W.draw_u("day", np.array([5, 6]), 0, 3))
    assert not np.array_equal(u0, W.draw_u("day", np.array([5, 6]), 1, 3))
    assert W.draw_u("day", np.array([6]), 0, 3)[0] == u0[1]  # 体の数に依らない


def test_blank_rules_and_school():
    """決まっていない予定は空欄・授業は月〜金(規則)で時間帯は空欄・土日は空欄。"""
    a = attrs(400)
    t = build(a)["columns"]
    commit = t["commit"].reshape(a.n, 7)
    none = ~np.asarray(a.employed) & ~np.asarray(a.school)
    assert none.any()
    assert (commit[none] == W.COMMIT_NONE).all()
    blank_rows = (t["commit"] == W.COMMIT_NONE)
    for c in ("start_min", "end_min", "depart_min", "return_min", "lead_min", "target_cell"):
        assert (t[c][blank_rows] == W.BLANK).all(), c
    assert (t["place_kind"][blank_rows] == W.PLACE_NONE).all() and (t["certainty"][blank_rows] == W.CERT_BLANK).all()
    sch = np.asarray(a.school)
    assert sch.any()
    assert (commit[sch][:, :5] == W.COMMIT_SCHOOL).all() and (commit[sch][:, 5:] == W.COMMIT_NONE).all()
    srows = t["commit"] == W.COMMIT_SCHOOL
    assert (t["start_min"][srows] == W.BLANK).all() and (t["end_min"][srows] == W.BLANK).all()
    assert (t["recurrence"][srows] == W.RECUR_RULE).all() and (t["certainty"][srows] == W.CERT_FIXED).all()
    # 勤め先の約束が無い duty_role(路上生活者ほか)は空欄
    a2 = W.attributes_from_columns(
        {"agent_id": [1, 2], "kind": [8, 8], "age": [40, 40], "home_cell": [-1, -1], "work_cell": [3, 3],
         "school_cell": [-1, -1], "industry_key": ["", ""], "duty_role": ["路上生活者", "配信者"]}, {})
    assert not a2.employed.any() and (build(a2)["columns"]["commit"] == 0).all()


def test_place_kinds_by_role_and_workplace():
    """勤務場所の種類は duty_role の表だけで決め、W16 の事業所の体は建物(W16 に職業の列が無い=親の判断 2026-10-15 の 1)。"""
    a = W.attributes_from_columns(
        {"agent_id": np.arange(8), "kind": [8, 8, 8, 0, 0, 3, 3, 3], "age": [40] * 7 + [10],
         "home_cell": [-1, -1, -1, -1, -1, 5, 5, 5], "work_cell": [2, 2, 2, 2, 2, -1, -1, -1],
         "school_cell": [-1] * 8, "industry_key": ["", "", "", "TR", "IT", "", "", ""],
         "duty_role": ["駅員", "電車運転士", "警察官", "", "", "", "", ""]},
        {"occupation_major": [None, None, None, "輸送・機械運転従事者", "事務従事者", "事務従事者", "事務従事者", None],
         "employment": ["正規", "正規", "正規", "正規", "正規", "正規", "非正規", None],
         "workplace_scope": [None, None, None, None, None, "out_area", "at_home", None],
         "school_stage": [None] * 7 + ["小学校"]})
    t = build(a)["columns"]
    pk = t["place_kind"].reshape(8, 7)
    cm = t["commit"].reshape(8, 7)
    want = [W.PLACE_STATION, W.PLACE_VEHICLE, W.PLACE_AREA, W.PLACE_BUILDING, W.PLACE_BUILDING, W.PLACE_OUTSIDE,
            W.PLACE_HOME, W.PLACE_SCHOOL]
    for i, w in enumerate(want):
        got = set(pk[i][cm[i] > 0].tolist())
        assert got <= {w} and (got or i < 7), (i, got)
    assert set(pk[7][:5].tolist()) == {W.PLACE_SCHOOL}  # 舞台に住む子(学校のセル無し)=学校
    lead = t["lead_min"].reshape(8, 7)
    assert set(lead[6][cm[6] > 0].tolist()) <= {0}  # 自宅で働く=通勤なし
    # ペルソナの職業(occupation_major)は読まない=W16 の事業所の体の職業は空・duty_role の体だけ職業がある
    assert a.occupation[:3] == ["輸送・機械運転従事者", "輸送・機械運転従事者", "保安職業従事者"]
    assert a.occupation[3:] == [""] * 5 and "occupation_major" not in W.POOL_FIELDS
    # 公務は産業の鍵の 15 語に無い=空欄(新しい語を足さない)
    assert a.industry[2] == "" and all(v[1] != "公務" for v in W.DUTY_ROLE_SPEC.values())


def test_times_are_the_31_36_inverse_with_the_lead_and_the_clip():
    """始業=出勤+片道の通勤時間・終業=帰宅−片道の通勤時間(勤務の長さは [4h, 12h] に切る)。"""
    a = attrs(800)
    t = build(a)["columns"]
    w = t["commit"] == W.COMMIT_WORK
    dep, ret, lead = (t[c][w].astype(np.int64) for c in ("depart_min", "return_min", "lead_min"))
    st, en = t["start_min"][w].astype(np.int64), t["end_min"][w].astype(np.int64)
    assert np.array_equal(st, dep + lead)
    ln = en - st
    assert (ln >= W.WORK_LEN_MIN).all() and (ln <= W.WORK_LEN_MAX).all()
    inner = (ret - lead - st >= W.WORK_LEN_MIN) & (ret - lead - st <= W.WORK_LEN_MAX)
    assert inner.any() and np.array_equal(en[inner], (ret - lead)[inner])
    bins = ANCHOR["depart"]["bins"]
    assert dep.min() >= bins[0]["start_min"] and dep.max() < bins[-1]["start_min"] + bins[-1]["width_min"]
    # 配列の逆関数法は trial.inverse_sample と同じ値
    bt = TR._bin_table(ANCHOR["depart"], "正規の職員・従業員")
    u = np.random.default_rng(3).random(2000)
    assert W.inverse_sample_array(bt, u).tolist() == [TR.inverse_sample(bt, float(x)) for x in u]


def test_weekday_rates_are_table_74_6_and_table_19_is_only_a_gauge():
    """曜日の予定の率は第74-6表の地位・勤務形態の曜日の率そのもの(実現値=予定の下限・親の判断 第336 (1))・週の日数は
    その和・duty_role の体だけ第74-9表の比(上限 1)。第19表は年間の整合の計器(予定の率を動かさない)。"""
    m = materials()
    a = W.attributes_from_columns(
        {"agent_id": np.arange(3), "kind": [0, 0, 8], "age": [40] * 3, "home_cell": [-1] * 3, "work_cell": [3] * 3,
         "school_cell": [-1] * 3, "industry_key": ["IT", "IT", ""], "duty_role": ["", "", "駅員"]},
        {"employment": ["正規", "非正規", "正規"]})
    emp = W.draw_employment_status(a, m, ANCHOR)
    out = W.calendar_from_attributes(a, emp, m, ANCHOR)
    full = m.rate74(m.t746, "1_うち雇用されている人|1_フルタイム")
    assert np.allclose(out["p_type"][0], full)
    row1 = W.EMP_ROWS[int(emp.emp_row[1])]
    assert np.allclose(out["p_type"][1], np.clip(W._day_weights(m, "", row1), 0, 1))
    ratio = m.rate74(m.t749, "輸送・機械運転従事者") / m.rate74(m.t749, "総数")
    row2 = W.EMP_ROWS[int(emp.emp_row[2])]
    style = m.rate74(m.t746, W.EMP_ROW_TO_746[row2][0])
    assert np.allclose(out["p_type"][2], np.clip(style * ratio, 0, 1))
    t749 = {**m.t749, "輸送・機械運転従事者": _r(0.72, 0.99, 0.55), "総数": _r(0.82, 0.20, 0.22)}  # 土の比 4.95
    m3 = W.Materials({**m.doc, "tables": {**m.doc["tables"], "74-9": {"rows": t749}}})
    assert W.calendar_from_attributes(a, emp, m3, ANCHOR)["p_type"][2, 1] == 1.0  # 上限 1
    assert np.allclose(out["days_per_week"], (out["p_type"] * np.asarray(W.DAY_TYPE_COUNT)).sum(axis=1))
    # 第19表を変えても予定の率は動かない(年間の整合の計器だけが動く)
    m2 = W.Materials({**m.doc, "tables": {**m.doc["tables"], "19": {"rows": {k: {"mean_days": 100.0}
                                                                             for k in m.t19}}}})
    out2 = W.calendar_from_attributes(a, emp, m2, ANCHOR)
    assert np.array_equal(out2["columns"]["commit"], out["columns"]["commit"])
    ac = out["annual_check"]["正規の職員・従業員"]
    assert ac["t19_days_per_year"] == 242.0 and ac["plan_days_per_year"] > ac["t19_days_per_year"]
    assert out2["annual_check"]["正規の職員・従業員"]["t19_days_per_year"] == 100.0


def test_seat_but_nonworking_persona_is_blank():
    """W16 の席(種別 0・2)があってもペルソナの employment が非就業なら勤務の約束は空欄(親の判断 第336 (3))・数える。"""
    a = W.attributes_from_columns(
        {"agent_id": np.arange(3), "kind": [2, 0, 2], "age": [40] * 3, "home_cell": [5, -1, 5], "work_cell": [3] * 3,
         "school_cell": [-1] * 3, "industry_key": ["IT"] * 3, "duty_role": [""] * 3},
        {"employment": ["非就業", "非就業", "正規"]})
    assert a.seat_nonworking.tolist() == [True, True, False] and a.employed.tolist() == [False, False, True]
    out = build(a)
    assert (out["columns"]["commit"].reshape(3, 7)[:2] == W.COMMIT_NONE).all()
    assert out["counters"]["seat_nonworking"] == 2


def test_seat_beats_school_and_is_counted():
    """〔検収 中 1・親の判断 第337〕W16 の席(種別 0・2)があってペルソナが学校段階か学校のセルを持つ体は、席を優先して勤務の
    約束(授業は空欄)・数を ``seat_and_school`` に出す。非就業のペルソナは勤務も空欄(``seat_nonworking`` にも数える)。"""
    a = W.attributes_from_columns(
        {"agent_id": np.arange(5), "kind": [2, 0, 2, 5, 2], "age": [17, 17, 17, 17, 40],
         "home_cell": [5, -1, 5, 5, 5], "work_cell": [3, 3, 3, -1, 3], "school_cell": [9, -1, -1, 9, -1],
         "industry_key": ["FB", "FB", "FB", "", "IT"], "duty_role": [""] * 5},
        {"employment": ["非正規", "非正規", "非就業", None, "正規"],
         "school_stage": [None, "高等学校", "高等学校", "高等学校", None]})
    assert a.seat_and_school.tolist() == [True, True, True, False, False]
    assert a.employed.tolist() == [True, True, False, False, True]
    assert a.school.tolist() == [False, False, False, True, False] and a.seat_nonworking.tolist()[2]
    out = build(a)
    cm = out["columns"]["commit"].reshape(5, 7)
    assert not (cm[:3] == W.COMMIT_SCHOOL).any() and (cm[3, :5] == W.COMMIT_SCHOOL).all()
    assert (cm[2] == W.COMMIT_NONE).all()
    c = out["counters"]
    assert c["seat_and_school"] == 3 and c["seat_and_school_work"] == 2 and c["seat_nonworking"] == 1


def _full_week_materials() -> W.Materials:
    """どの行も曜日の率 1(7 日とも勤務を引く)の作り物。"""
    m = materials()
    t746 = {k: _r(1.0, 1.0, 1.0) for k in m.t746}
    t749 = {k: _r(1.0, 1.0, 1.0) for k in m.t749}
    return W.Materials({**m.doc, "tables": {**m.doc["tables"], "74-6": {"rows": t746}, "74-9": {"rows": t749}}})


def test_weekly_rest_day_for_employees_from_the_rules_table():
    """〔検収 中 2・親の判断 第337〕労働基準法 9 条の労働者(無期・有期・臨時)の体は、その週に 7 日とも勤務を引いたら 1 日を
    休みに。根拠は規則の表の行(35 条 1 項・対象の地位は行の applies_to_status)。自営業主・家族従業者と有給役員は対象の外
    =週 7 日のまま。どの曜日も率 1(働かない率が全部 0)の体は受け皿=率の最も低い曜日(同じなら日曜)。"""
    rule = W.load_weekly_rest_rule()
    assert rule["id"] == W.WEEKLY_REST_RULE_ID and rule["params"]["min_rest_days_per_week"] == 1
    assert rule["source"][0]["law_id"] == "322AC0000000049" and "35" in rule["source"][0]["article"]
    assert set(rule["params"]["applies_to_status"]) == {W.STATUS_WORDS[s] for s in W.REST_STATUSES}
    assert "有給役員" not in rule["params"]["applies_to_status"] and W.rest_statuses_of(rule) == W.REST_STATUSES
    with pytest.raises(ValueError):
        W.rest_statuses_of({"params": {"applies_to_status": ["社長"]}})
    assert W.rest_day_of(np.array([[0.9, 0.3, 0.5], [0.9, 0.4, 0.4], [1.0, 1.0, 1.0]])).tolist() == [5, 6, 6]
    emp_words = ["正規", "非正規", "役員", "自営業主", "家族従業者"]
    n = len(emp_words)
    a = W.attributes_from_columns(
        {"agent_id": np.arange(n), "kind": [3] * n, "age": [40] * n, "home_cell": [5] * n, "work_cell": [3] * n,
         "school_cell": [-1] * n, "industry_key": [""] * n, "duty_role": [""] * n},
        {"employment": emp_words, "industry_key": ["IT"] * n, "workplace_scope": ["in_area"] * n})
    m = _full_week_materials()
    emp = W.draw_employment_status(a, m, ANCHOR)
    out = W.calendar_from_attributes(a, emp, m, ANCHOR, n_weeks=2)
    cm = out["columns"]["commit"].reshape(n, 2, 7)
    rest = np.isin(np.asarray(emp.status), list(W.REST_STATUSES))
    assert rest.tolist() == [True, True, False, False, False]
    assert ((cm[rest] == W.COMMIT_WORK).sum(axis=2) == 6).all() and (cm[rest][:, :, 6] == W.COMMIT_NONE).all()
    assert ((cm[~rest] == W.COMMIT_WORK).sum(axis=2) == 7).all()
    assert out["counters"]["weekly_rest_inserted"] == 2
    rows = out["columns"]["commit"] == W.COMMIT_NONE
    assert (out["columns"]["start_min"][rows] == W.BLANK).all() and (out["columns"]["depart_min"][rows] == W.BLANK).all()
    off = W.calendar_from_attributes(a, emp, m, ANCHOR, rest_rule={**rule, "params": {"min_rest_days_per_week": 0}})
    assert ((off["columns"]["commit"].reshape(n, 7) == W.COMMIT_WORK).sum(axis=1) == 7).all()
    assert off["counters"]["weekly_rest_inserted"] == 0


def test_rest_day_is_drawn_in_proportion_to_the_not_working_rate():
    """〔親の判断 第337 (2)〕休みの曜日=その曜日の働かない率(1 − 予定の率)に比例して 1 日(体・週の鍵・毎週固定の体は
    毎週同じ)。働かない率が 0 の曜日は引かない。"""
    n = 17000
    d = W.rest_day_draw(np.tile([[0.9, 0.3, 0.5]], (n, 1)), (np.arange(n) + 0.5) / n)
    assert np.bincount(d, minlength=7).tolist() == [1000] * 5 + [7000, 5000]  # 0.1×5・0.7・0.5 の比
    u = np.linspace(0.0, 0.999999, 101)
    assert set(W.rest_day_draw(np.tile([[1.0, 0.5, 1.0]], (101, 1)), u).tolist()) == {5}
    assert W.rest_day_draw(np.ones((3, 3)), np.array([0.0, 0.5, 0.99])).tolist() == [6, 6, 6]  # 受け皿
    m = materials()
    t746 = {k: _r(1.0, 0.95, 0.9) for k in m.t746}
    m2 = W.Materials({**m.doc, "tables": {**m.doc["tables"], "74-6": {"rows": t746}}})
    n2 = 300
    a = W.attributes_from_columns(
        {"agent_id": np.arange(n2), "kind": [3] * n2, "age": [40] * n2, "home_cell": [5] * n2, "work_cell": [3] * n2,
         "school_cell": [-1] * n2, "industry_key": [""] * n2, "duty_role": [""] * n2},
        {"employment": [("正規", "非正規")[i % 2] for i in range(n2)], "industry_key": ["IT"] * n2,
         "workplace_scope": ["in_area"] * n2})
    emp = W.draw_employment_status(a, m2, ANCHOR)
    out = W.calendar_from_attributes(a, emp, m2, ANCHOR, n_weeks=4)
    cm = out["columns"]["commit"].reshape(n2, 4, 7) == W.COMMIT_WORK
    assert (cm.sum(axis=2) <= 6).all() and cm[:, :, :5].all()  # 平日の率 1=休みは土日だけ
    rec = out["columns"]["recurrence"].reshape(n2, 4, 7)
    fixed = (rec == W.RECUR_FIXED).any(axis=(1, 2))
    assert fixed.sum() > 50 and all(np.array_equal(cm[fixed, k], cm[fixed, 0]) for k in range(1, 4))
    off_sat = (~cm[:, :, 5] & cm[:, :, 6]).sum()
    off_sun = (cm[:, :, 5] & ~cm[:, :, 6]).sum()
    assert off_sat > 0 and off_sun > off_sat  # 働かない率 0.05 対 0.10(7 日の週に入れた休み+もとから休む日)


def test_clipped_work_recomputes_the_return():
    """〔検収 低 1〕勤務の長さを [4h, 12h] に切った体の帰宅は終業+片道の通勤時間(終業 ≤ 帰宅)=どの勤務の行も
    帰宅=終業+片道・出勤+片道=始業。"""
    a = attrs(800)
    out = build(a)
    t = out["columns"]
    w = t["commit"] == W.COMMIT_WORK
    dep, st, en, ret, lead = (t[c][w].astype(np.int64) for c in ("depart_min", "start_min", "end_min", "return_min",
                                                                  "lead_min"))
    assert out["counters"]["work_len_clipped"] > 0
    assert (en <= ret).all() and np.array_equal(ret, en + lead) and np.array_equal(st, dep + lead)
    assert (dep <= st).all() and (st < en).all()


def test_employment_status_from_the_persona_and_the_duty_role_redraw():
    """地位はペルソナの employment の 6 値を第6-2表の 6 区分へ写す(親の判断 2026-10-15 の 3)・duty_role の体だけ
    第6-2表(渋谷区・中分類)の人数比で引き直す(同 4)・ペルソナの無い体は正規の行(数える)。"""
    n = 6000
    a = W.attributes_from_columns(
        {"agent_id": np.arange(n), "kind": [8] * n, "age": [40] * n, "home_cell": [-1] * n, "work_cell": [3] * n,
         "school_cell": [-1] * n, "industry_key": [""] * n, "duty_role": ["駅員"] * n}, {"employment": ["正規"] * n})
    m = materials()
    emp = W.draw_employment_status(a, m, ANCHOR)
    assert (emp.source == W.SRC_CENSUS).all()
    share = np.bincount(emp.status, minlength=len(W.STATUS_WORDS)) / n
    c = m.status_counts("", ("42",))
    got = share[[st for st, _c in W.CENSUS_STATUS_COLS]]
    assert np.abs(got - c / c.sum()).max() < 0.02
    words = ["正規", "非正規", "役員", "自営業主", "家族従業者", "非就業", ""]
    b = W.attributes_from_columns(
        {"agent_id": np.arange(7), "kind": [0, 0, 0, 0, 0, 3, 4], "age": [40] * 7, "home_cell": [-1] * 5 + [5, -1],
         "work_cell": [3] * 5 + [-1, 3], "school_cell": [-1] * 7, "industry_key": ["FB"] * 5 + ["", ""],
         "duty_role": [""] * 6 + ["指令"]}, {"employment": words, "workplace_scope": [None] * 5 + ["out_area", None]})
    e = W.draw_employment_status(b, m, ANCHOR)
    assert e.status.tolist() == [W.ST_INDEF, W.ST_FIXED_TERM, W.ST_OFFICER, W.ST_SOLE, W.ST_FAMILY, W.ST_NONE,
                                 W.ST_INDEF]
    assert e.source.tolist() == [W.SRC_EMPLOYMENT] * 5 + [W.SRC_NONE, W.SRC_MISSING]
    names = [W.EMP_ROWS[i] if i >= 0 else "" for i in e.emp_row.tolist()]
    assert names[0] == "正規の職員・従業員" and names[2] == "会社などの役員" and names[4] == "家族従業者"
    assert names[1] in W.WEEKLY_ROWS and names[3] in ("雇人のある業主", "雇人のない業主") and names[5] == ""
    assert e.counters == {"from_employment": 5, "census_redraw_duty_role": 0, "employment_missing": 1}
    a2 = attrs(400)
    e2 = W.draw_employment_status(a2, m, ANCHOR)
    assert (e2.emp_row[a2.employed] >= 0).all() and (e2.emp_row[~a2.employed] == W.BLANK).all()
    assert (e2.status[~a2.employed] == W.ST_NONE).all()


def test_day_weights_use_table_74_6_first():
    """曜日の重みは第74-6表の地位・勤務形態の行・職業の分かる duty_role の体だけ第74-9表の比を掛ける。"""
    m = materials()
    w = W._day_weights(m, "", "正規の職員・従業員")
    assert np.allclose(w, m.rate74(m.t746, "1_うち雇用されている人|1_フルタイム"))
    assert np.allclose(W._day_weights(m, "", "パート"), m.rate74(m.t746, "1_うち雇用されている人|2_短時間勤務"))
    ratio = m.rate74(m.t749, "保安職業従事者") / m.rate74(m.t749, "総数")
    assert np.allclose(W._day_weights(m, "保安職業従事者", "正規の職員・従業員"), w * ratio)


def test_attributes_are_the_only_population_input():
    """関数の入力は属性の表だけ(W16 の版が変わっても、属性の読み口を差し替えれば同じ関数が使える)。"""
    import inspect

    params = list(inspect.signature(W.calendar_from_attributes).parameters)
    assert params[:4] == ["attrs", "employment", "materials", "anchor"]
    assert {"agent_id", "kind", "age", "industry", "duty_role", "occupation", "employed", "workplace",
            "school"} <= set(W.Attributes.__dataclass_fields__)


# ================================================================= 検証側を開かない守り
def test_r99_file_lists_follow_the_parent_judgement():
    """構築側に開いてよいのは 4 本だけ・検証側(第14表・第15-1〜3表・第68-3表)は名で落とす(パターン台帳 §10)。"""
    assert set(W.R99_BUILD_FILES) == {"74-9", "74-6", "19", "6-2"}
    assert {"ssb2021_jikantai_t14_occupation.xlsx", "ssb2021_jikantai_t15-1_emp_weekday.xlsx",
            "ssb2021_jikantai_t15-2_emp_sat.xlsx", "ssb2021_jikantai_t15-3_emp_sun.xlsx",
            "ssb2021_seikatsu_t68-3_activity_pref.xlsx"} == set(W.R99_VALIDATION_FILES)
    assert not set(W.R99_BUILD_FILES.values()) & set(W.R99_VALIDATION_FILES)
    for parts in W.INPUT_FILES:
        assert parts[-1] not in W.R99_VALIDATION_FILES


def test_guard_refuses_validation_tables_before_opening(tmp_path):
    """負の対照: 守りの間は検証側の名のファイル(どこにあっても)と r99 の許可の外を ``open`` の前に落とす。"""
    r99 = tmp_path / "research_cache" / "r99"
    r99.mkdir(parents=True)
    bad = r99 / "ssb2021_jikantai_t14_occupation.xlsx"
    other = tmp_path / "ssb2021_seikatsu_t68-3_activity_pref.xlsx"
    stray = r99 / "something_else.xlsx"
    ok = r99 / W.R99_BUILD_FILES["74-9"]
    for p in (bad, other, stray, ok):
        p.write_bytes(b"x")
    g = W.R99Guard()
    with g.active():
        for p in (bad, other, stray):
            with pytest.raises(W.ValidationTableError):
                open(p, "rb")
        with open(ok, "rb") as fh:
            assert fh.read() == b"x"
    assert g.opened == [W.R99_BUILD_FILES["74-9"].lower()]
    with pytest.raises(W.ValidationTableError):
        W.iter_xlsx_rows(bad, W.R99Guard()).__next__()
    with open(bad, "rb"):  # 守りの外では何もしない
        pass


def test_w19_lists_the_build_inputs_and_families(tmp_path):
    """W19 の資産表と層の元に W20cal の構築側の入力が載る(検証側の名は載らない)。"""
    from shibuya.build.audit import w19_freeze as W19

    paths = set(W19.data_asset_paths(tmp_path))
    for parts in W.INPUT_FILES:
        assert "/".join(parts) in paths
    assert not any(p.rsplit("/", 1)[-1] in W.R99_VALIDATION_FILES for p in paths)
    for fam, files in W.INPUT_FAMILIES.items():
        assert W19.BUILD_INPUT_FAMILIES[fam] == tuple(files)


# ================================================================= 実データ(5,000 体)
real = pytest.mark.requires_data("world_v2")
#: 5,000 体の golden(W16 の 390,067 体から 78 体おきに 5,000 体=下の fixture ``real5000``)。同じ値を記録
#: ``docs/bench/analysis/wallbounce-1012/ca31/README.md`` の「§4-3 5,000 体の golden」の表に載せる(第337 の版=席を優先・
#: 週 1 日の休み(有給役員は対象の外・休みの曜日は働かない率に比例)・切った体の帰宅の作り直しの後)。
GOLDEN_5000 = {
    "work_bodies": 3145, "school_bodies": 556, "weekly_bodies": 1119, "fixed_bodies": 2026,
    "work_by_weekday": [2551, 2521, 2545, 2527, 2521, 963, 630],
}


def _r99_present() -> bool:
    root = DATA.joinpath(*W.R99_DIR)
    return all((root / f).is_file() for f in W.R99_BUILD_FILES.values())


@pytest.fixture(scope="module")
def real5000():
    if not _r99_present():
        pytest.skip("requires_data: research_cache/r99 が無い")
    import pyarrow.parquet as pq

    guard = W.R99Guard()
    with guard.active():
        mat = W.Materials(W.build_materials(DATA, guard=guard))
        # 〔第 4 期 4-3 段 10〕W16 の世界の母集団(差し替えた本体の v2 なら活性化の退避 v2_pre_4-3=W21 の元の世界)
        from shibuya.build.pop.w21_build import source_world

        cols = pq.read_table(source_world(DATA, None) / "w16_population.parquet").to_pydict()
        n_all = len(cols["agent_id"])
        idx = np.arange(0, n_all, 78)[:5000]
        sub = {k: [cols[k][i] for i in idx.tolist()] for k in
               ("agent_id", "kind", "age", "home_cell", "work_cell", "school_cell", "industry_key", "duty_role",
                "pool_layer", "pool_index")}
        pool = W.read_pool_fields(DATA / "persona_pool_v2", np.asarray(sub["pool_layer"]), np.asarray(sub["pool_index"]))
        a = W.attributes_from_columns(sub, pool)
        emp = W.draw_employment_status(a, mat, ANCHOR)
        out = W.calendar_from_attributes(a, emp, mat, ANCHOR)
    return {"mat": mat, "attrs": a, "emp": emp, "out": out, "opened": list(guard.opened), "idx": idx}


@real
def test_real_materials_match_the_r99_primary_values(real5000):
    """材料の値が R-99 の親検収済みの値と一致(写し検査)。開いたのは構築側の 4 本だけ。"""
    m = real5000["mat"]
    assert sorted(real5000["opened"]) == sorted(x.lower() for x in W.R99_BUILD_FILES.values())
    assert [round(x, 3) for x in m.rate74(m.t749, "総数")] == [0.824, 0.347, 0.223]
    assert [round(x, 3) for x in m.rate74(m.t749, "事務従事者")][1:] == [0.167, 0.103]
    assert [round(x, 3) for x in m.rate74(m.t749, "サービス職業従事者")][1:] == [0.592, 0.395]
    assert [round(x, 3) for x in m.rate74(m.t746, "1_うち雇用されている人|11_始業時間が固定されている")] == [0.881, 0.259,
                                                                                                         0.16]
    assert m.t62["total"]["total"] == 581127.0
    st = m.status_counts("*")
    assert round(float(st[4] / st.sum()), 3) == 0.229  # 有期 22.9%
    r = m.t19["321_正規の職員・従業員|0_総数"]
    assert round(r["counts"]["2_200～249日"] / r["all_total"], 3) == 0.569  # 正規 200〜249 日 56.9%


@real
def test_real_5000_table_shape_and_golden(real5000):
    out = real5000["out"]
    t, c = out["columns"], out["counters"]
    assert t["agent_id"].size == 5000 * 7
    got = {k: c[k] for k in ("work_bodies", "school_bodies", "weekly_bodies", "fixed_bodies")}
    wd = t["weekday"]
    got["work_by_weekday"] = [int(((t["commit"] == W.COMMIT_WORK) & (wd == d)).sum()) for d in range(7)]
    assert got == GOLDEN_5000, got
    w = t["commit"] == W.COMMIT_WORK
    assert 6 * 60 < float(np.median(t["depart_min"][w])) < 9 * 60  # 出勤の中央は朝(第 31 表の形)
    assert ((t["commit"] == W.COMMIT_SCHOOL) <= (t["start_min"] < 0)).all()


@real
def test_real_5000_rows_equal_the_stage_asset_when_present(real5000):
    """組んだ資産(data/world/v2_stage_3-1)があれば、同じ 5,000 体の行が一致する(段=関数を全員にかけただけ)。"""
    from shibuya.engine.calendar_shadow import STAGE_DIR

    p = REPO / STAGE_DIR / W.OUTPUT_NAME
    if not p.is_file():
        pytest.skip(f"requires_data: {STAGE_DIR} が無い(段の資産は組んでいない)")
    import pyarrow.parquet as pq

    tab = pq.read_table(p)
    rows = (real5000["idx"][:, None] * 7 + np.arange(7)[None, :]).ravel()
    t = real5000["out"]["columns"]
    for k in ("agent_id", "commit", "start_min", "end_min", "depart_min", "return_min", "place_kind", "recurrence"):
        assert np.array_equal(np.asarray(tab.column(k).to_numpy())[rows], np.asarray(t[k])), k


@real
def test_read_guard_of_2_0_sees_no_validation_table(real5000):
    """2-0 の ``read_guard`` の形(監査フック)でも、材料の組み立ては検証側の名を開かない。負の対照つき。"""
    sys.path.insert(0, str(REPO / "tools" / "instruments"))
    import read_guard as RG

    guard = RG.ReadGuard.sealed_only()
    guard.tokens = tuple(RG.SEALED_TOKENS) + tuple(W.R99_VALIDATION_FILES)
    with guard.active():
        doc = W.build_materials(DATA)
        assert set(doc["r99_opened"]) == {x.lower() for x in W.R99_BUILD_FILES.values()}
        with pytest.raises(RG.SealedPathError):
            open(DATA.joinpath(*W.R99_DIR, W.R99_VALIDATION_FILES[0]), "rb")
