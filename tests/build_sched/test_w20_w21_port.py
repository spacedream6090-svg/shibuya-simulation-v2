"""W21 → W20 の ``Attributes`` の口(``build.sched.w20_w21_port``・第 4 期 4-1 段 10 の材料)の試験。

- 19 欄が W20 の入力の仕様に合い、本体の ``draw_employment_status`` と ``calendar_from_attributes`` に通る(例外なし)。
- 職業は ``occupation_major`` から・地位は W21 の値(第6-2表で引き直さない)・担当の語は ``DUTY_ROLE_SPEC`` の鍵。
- 知らない担当の語は止まる(黙って担当なしにしない=負の対照)。
- W16 の既定の口(``attributes_from_columns``)は変わらない(W16 の在庫に新しい 4 語は無い)。
- 実データ(``requires_data``): W21 の人 5,000 人を本体の材料(第74-6・74-9・19・6-2 表)で回して例外なし。
"""

from __future__ import annotations

import dataclasses
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.sched import w20_calendar_1a as W
from shibuya.build.sched import w20_w21_port as WP

from .test_w20_calendar_1a import ANCHOR, materials

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"


def _people() -> dict:
    n = 9
    return {
        "person_id": np.arange(100, 100 + n), "w16_kind": np.array([3, 2, 2, 0, 0, 0, 3, 3, 0]),
        "age": np.array([40, 35, 50, 30, 45, 28, 8, 19, 41]),
        "industry_key": np.array(["", "IT", "WR", "FB", "TR", "SV", "", "", ""], dtype=object),
        "duty_role": np.array(["", "", "店長", "補充", "駅員", "警備員", "", "", "警察官"], dtype=object),
        "occupation_major": np.array(["", "C", "D", "D", "C", "F", "", "E", "F"], dtype=object),
        "employment_status": np.array(["", "regular", "executive", "non_regular", "regular", "regular", "", "non_regular",
                                       "regular"], dtype=object),
        "labour_status": np.array(["not_in_labour_force", "employed", "employed", "employed", "employed", "employed", "",
                                   "employed", "employed"], dtype=object),
        "workplace_area": np.array(["", "home", "stage", "stage", "stage", "stage", "", "outside_ward", "stage"],
                                   dtype=object),
        "school_kind": np.array(["none", "none", "none", "", "", "", "elementary", "university", ""], dtype=object),
        "home_cell": np.array([5, 6, 7, -1, -1, -1, 5, 8, -1]), "work_cell": np.array([-1, 6, 9, 9, 10, 11, -1, -1, 12]),
        "commute_mode": np.array(["", "home", "walk", "rail", "rail", "rail", "", "rail", "rail"], dtype=object),
        "commute_path_m": np.array([-1, 0, 500, 200, 100, 300, -1, 700, 50]),
    }


def test_attributes_from_w21_has_the_19_fields_and_passes_the_calendar():
    a = WP.attributes_from_w21(_people())
    assert [f.name for f in dataclasses.fields(W.Attributes)] == [
        "agent_id", "kind", "age", "industry", "duty_role", "occupation", "employment_pool", "employed", "workplace",
        "school", "work_cell", "school_cell", "home_cell", "lead_min", "census_middles", "place_hint", "shift",
        "seat_nonworking", "seat_and_school"]
    assert a.n == 9 and a.agent_id.tolist() == list(range(100, 109))
    assert a.occupation[1] == "事務従事者" and a.occupation[0] == "" and a.occupation[5] == "保安職業従事者"
    assert all(o == "" or o in W.OCC_ROWS for o in a.occupation)
    assert a.employment_pool[:3] == ["非就業", "正規", "役員"]
    assert a.employed.tolist() == [False, True, True, True, True, True, False, True, True]
    assert a.school.tolist() == [False] * 6 + [True, False, False] and a.seat_and_school.tolist()[7] is True
    assert a.workplace[1] == W.WP_HOME and a.workplace[2] == W.WP_AREA and a.workplace[7] == W.WP_OUTSIDE
    assert a.place_hint[2] == W.PLACE_BUILDING and a.place_hint[4] == W.PLACE_STATION and a.place_hint[8] == W.PLACE_AREA
    assert a.shift.tolist()[3] is True and a.shift.tolist()[2] is False  # 補充=交替制・店長=固定
    # 歩き 500 m ÷ 1.34 m/s=6.2 分 → 7・電車の人は空欄(−1=W20 の 30 分)。〔第 4 期 4-3 段 10〕いったん電車の人を舞台の中の
    # 道のりで埋めた(3・2・4・9・1)が、親の判断(検収 L6)で空欄に戻した
    assert a.lead_min.tolist() == [-1, 0, 7, -1, -1, -1, -1, -1, -1]
    assert all(m == () for m in a.census_middles) and not a.seat_nonworking.any()
    m = materials()
    emp = W.draw_employment_status(a, m, ANCHOR)
    assert (emp.source[a.employed] == W.SRC_EMPLOYMENT).all()  # 地位は W21 の値=第6-2表で引き直さない
    out = W.calendar_from_attributes(a, emp, m, ANCHOR)
    c = out["columns"]["commit"].reshape(9, 7)
    assert (c[0] == W.COMMIT_NONE).all() and (c[6][:5] == W.COMMIT_SCHOOL).all()
    assert out["counters"]["seat_and_school"] == 1 and out["counters"]["lead_default"] >= 1
    pk = out["columns"]["place_kind"].reshape(9, 7)
    assert set(pk[4][c[4] > 0].tolist()) <= {W.PLACE_STATION} and set(pk[1][c[1] > 0].tolist()) <= {W.PLACE_HOME}


def test_unknown_duty_role_stops():
    p = _people()
    p["duty_role"] = p["duty_role"].copy()
    p["duty_role"][3] = "知らない担当"
    with pytest.raises(WP.UnknownDutyRoleError) as e:
        WP.attributes_from_w21(p)
    assert "知らない担当" in str(e.value)
    q = _people()
    del q["school_kind"]
    with pytest.raises(KeyError):
        WP.attributes_from_w21(q)


def test_new_duty_words_are_keys_and_w16_default_is_unchanged():
    from shibuya.build.pop import attr_fns as A

    # 〔検収 中 1〕4 語は W21 用の表=W20 の表は土台のまま(W16 の在庫の 22 語)
    assert set(A.DUTY_WORDS) <= set(WP.duty_role_spec())  # W21b の 11 語は全部どちらかの表の鍵
    assert set(WP.DUTY_ROLE_SPEC_W21) == set(A.DUTY_WORDS_NOT_IN_W20) and not (set(WP.DUTY_ROLE_SPEC_W21)
                                                                                & set(W.DUTY_ROLE_SPEC))
    for w in A.DUTY_WORDS_NOT_IN_W20:
        occ, _ind, _mids, place, _sh, job = WP.DUTY_ROLE_SPEC_W21[w]
        assert occ in W.OCC_ROWS and place in (W.PLACE_BUILDING, W.PLACE_AREA) and job is True
    # W16 の既定の口: W16 の在庫の語(22)は前からの鍵だけ=体の表は変わらない
    w16_words = {"キッチンカー営業者", "ストリートミュージシャン", "タクシー運転手", "ティッシュ配り", "バス運転士", "募金スタッフ",
                 "夜間清掃員", "指令", "救急隊員", "消防士", "清掃作業員", "納品ドライバー", "街頭演説者", "警察官", "議員",
                 "路上占い師", "路上支援員", "路上生活者", "車掌", "配信者", "電車運転士", "駅員"}
    assert w16_words == set(W.DUTY_ROLE_SPEC) and not (w16_words & set(A.DUTY_WORDS_NOT_IN_W20))


@pytest.mark.requires_data("world_v2")
def test_w20cal_param_hash_is_unchanged():
    """〔検収 中 1〕W20cal の ``params`` の ``duty_role_spec`` は組んだ資産(v2_stage_3-1)のヘッダと同じ=組み直しても
    ``param_hash`` が動かない(ヘッダの params から param_hash を計算し直して同じことも確かめる)。"""
    import json

    from shibuya.build.geo import common as C

    h = REPO / "data" / "world" / "v2_stage_3-1" / W.HEADER_NAME
    if not h.is_file():
        pytest.skip("requires_data: v2_stage_3-1 が無い")
    head = json.loads(h.read_text(encoding="utf-8"))
    now = {k: list(v[:2]) + [list(v[2])] + list(v[3:]) for k, v in W.DUTY_ROLE_SPEC.items()}
    assert head["params"]["duty_role_spec"] == now
    assert C.param_hash(head["params"]) == head["param_hash"]


def test_lead_minutes():
    got = WP.lead_minutes(np.array(["walk", "walk", "home", "rail", ""], dtype=object), np.array([1, 134 * 60, 0, 300, -1]))
    assert got.tolist() == [1, 100, 0, -1, -1]  # 〔段 10・親の判断〕電車の人は空欄のまま


# ================================================================= 実データ(W21 の人 5,000 人)
real = pytest.mark.requires_data("world_v2")


@real
def test_real_w21_people_pass_the_calendar():
    import pyarrow.parquet as pq

    base = DATA / "world" / "v2_stage_4-1b"
    if not (base / "w21_people.parquet").is_file():
        pytest.skip("requires_data: 段 4〜7 の資産 v2_stage_4-1b が無い")
    root = DATA.joinpath(*W.R99_DIR)
    if not all((root / f).is_file() for f in W.R99_BUILD_FILES.values()):
        pytest.skip("requires_data: research_cache/r99 が無い")
    cols = [c for c in WP.W21_INPUT_COLUMNS if c != "school_kind"]
    people = pq.read_table(base / "w21_people.parquet", columns=cols).to_pydict()
    persons = pq.read_table(base / "w21_persons.parquet", columns=["person_id", "school_kind"]).to_pydict()
    n = len(people["person_id"])
    sk = np.full(n, "", dtype=object)
    sk[np.asarray(persons["person_id"])] = np.asarray(persons["school_kind"], dtype=object)  # 住民は番号=行
    idx = np.arange(0, n, max(1, n // 5000))[:5000]
    sub = {k: np.asarray(v, dtype=object if isinstance(v[0], str) else None)[idx] for k, v in people.items()}
    sub["school_kind"] = sk[idx]
    a = WP.attributes_from_w21(sub)
    guard = W.R99Guard()
    with guard.active():
        mat = W.Materials(W.build_materials(DATA, guard=guard))
    emp = W.draw_employment_status(a, mat, ANCHOR)
    out = W.calendar_from_attributes(a, emp, mat, ANCHOR)
    assert out["columns"]["agent_id"].size == a.n * 7
    assert out["counters"]["work_bodies"] > 0 and out["counters"]["seat_nonworking"] == 0
    duty = np.asarray(a.duty_role, dtype=object)
    assert set(duty[duty != ""]) <= set(WP.duty_role_spec())  # W20 の 22 語+W21 の 4 語
