"""第 4 期 4-3 段 10「差し替え」(``build.pop.w21_apply``)の受入の試験。

- 合成の小さな母集団で: W16 の群の扱いの表(残す/外す・知らない群で止まる=負の対照)・W21 の人 → W16 の列(番号の対応が
  全単射・知らない種別と駅の口で止まる)・母集団の合わせ(残す行は不変・番号の重なりで止まる)・W17 の提供者(層・使っていない
  提供者から・セルの置き換え・提供者の居ない種別で止まる)・権利台帳の初期の行(engine の ``load_run_rows``・``build_initial``
  に通る=閉じた表・閉じた表の外で止まる)・活性化の道具の plan の表と verify の sha の確かめ・W20 の口(8 区分から第 31/36 表の
  行へ直接・知らない地位の語で止まる・W20cal の params は第337 の版と同じ=param_hash 不変)・出力先の守り。
- 実データ(``requires_data``・組んだ資産 ``data/world/v2_stage_4-3`` があるとき): 門・数・golden・W17 が全員を覆う・engine が
  母集団を読む。
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shibuya.build.pop import w21_apply as AP
from shibuya.build.pop import w21_build_b as BB
from shibuya.build.pop import w21_build_c as BC
from shibuya.build.sched import w20_calendar_1a as W20
from shibuya.build.sched import w20_w21_port as WP

REPO = Path(__file__).resolve().parents[2]
DATA = REPO / "data"
STAGE = DATA / "world" / AP.SWAP_ASSET
TOOL = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "pop43" / "tools" / "activate_pop43.py"


def _tool():
    spec = importlib.util.spec_from_file_location("activate_pop43", TOOL)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["activate_pop43"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


# ================================================================================ W16 の群
def test_w16_group_actions_follow_the_parent_decisions():
    kind = np.array([0, 1, 2, 3, 3, 4, 5, 6, 7, 8, 8, 8, 8, 8, 8, 8])
    duty = np.array(["", "", "", "", "議員", "指令", "", "", "", "駅員", "電車運転士", "車掌", "バス運転士",
                     "タクシー運転手", "警察官", "救急隊員"], dtype=object)
    keep, table = AP.w16_actions(kind, duty)
    # 〔検収 M1〕通学者(種別 5)は残す(前の版は外した=index 6 が False)
    want = [False, True, False, False, False, True, True, True, True, False, False, False, True, True, False, True]
    assert keep.tolist() == want
    assert table["5|"]["action"] == "keep" and table["8|バス運転士"]["action"] == "keep"
    # 親の判断 (1): 鉄道の 3 語は外す・バスとタクシーは残す / (10)・検収 M1: 来街者と通学者は残す
    for role in ("駅員", "電車運転士", "車掌"):
        assert AP.W16_GROUP_ACTION[(8, role)] == "remove"
    for k in (1, 5, 6, 7):
        assert AP.W16_GROUP_ACTION[(k, "")] == "keep"


def test_unknown_w16_group_stops():
    with pytest.raises(AP.UnknownW16GroupError):
        AP.w16_actions(np.array([8, 8]), np.array(["駅員", "知らない役"], dtype=object))
    with pytest.raises(AP.UnknownW16GroupError):
        AP.w16_actions(np.array([9]), np.array([""], dtype=object))


# ================================================================================ W21 → W16 の列
def _people(n=4):
    return {
        "person_id": np.arange(n), "w16_kind": np.array([3, 2, 0, 0][:n]), "age": np.array([30, 41, 25, 60][:n]),
        "sex": np.array([0, 1, 0, 1][:n]), "home_cell": np.array([5, 6, -1, -1][:n]),
        "work_cell": np.array([-1, 6, 7, 8][:n]),
        "entry_node": np.array(["ext_a", "", "ext_b", "ext_a"][:n], dtype=object),
        "home_chome_key": np.array(["k1", "k2", "", ""][:n], dtype=object),
        "household_id": np.array([0, 1, -1, -1][:n]), "org_index": np.array([-1, 3, 4, -1][:n]),
        "industry_key": np.array(["", "IT", "WR", "WR"][:n], dtype=object),
        "duty_role": np.array(["", "", "駅員", "店長"][:n], dtype=object),
        "occupation_major": np.array(["", "C", "I", "D"][:n], dtype=object),
        "employment_status": np.array(["", "regular", "non_regular", "self_employed"][:n], dtype=object),
    }


def _persons():
    return {"person_id": np.array([0, 1]), "is_foreign": np.array([True, False]), "home_building": np.array([11, -1])}


def _money(n=4):
    return {"person_id": np.arange(n), "wage_monthly": np.array([-1, 300000, 200000, 250000][:n])}


def test_w21_columns_are_a_bijection_from_person_ids():
    cols = AP.w21_population_columns(_people(), _persons(), _money(), ["ext_a", "ext_b"], base=100)
    assert cols["agent_id"].tolist() == [100, 101, 102, 103]
    assert cols["w21_person_id"].tolist() == [0, 1, 2, 3]
    assert cols["purpose"].tolist() == [AP.PURPOSE_RESIDE, AP.PURPOSE_RESIDE, AP.PURPOSE_WORK, AP.PURPOSE_WORK]
    assert cols["direction_node"].tolist() == [0, -1, 1, 0]
    assert cols["is_foreign"].tolist() == [True, False, False, False]
    assert cols["home_building"].tolist() == [11, -1, -1, -1]
    assert cols["pool_layer"].tolist() == [-1] * 4 and cols["school_cell"].tolist() == [-1] * 4
    assert cols["persona_occupation"].tolist() == ["", "事務従事者", "輸送・機械運転従事者", "販売従事者"]
    assert cols["persona_employment"].tolist() == ["", "正規", "非正規", "自営業主"]
    assert cols["wage_monthly"].tolist() == [-1, 300000, 200000, 250000]


def test_w21_columns_stop_on_unknown_entry_kind_and_gaps():
    with pytest.raises(KeyError):
        AP.w21_population_columns(_people(), _persons(), _money(), ["ext_a"], base=100)
    p = _people()
    p["w16_kind"] = np.array([3, 2, 0, 8])
    with pytest.raises(ValueError):
        AP.w21_population_columns(p, _persons(), _money(), ["ext_a", "ext_b"], base=100)
    p = _people()
    p["person_id"] = np.array([0, 1, 2, 5])
    with pytest.raises(ValueError):
        AP.w21_population_columns(p, _persons(), _money(), ["ext_a", "ext_b"], base=100)


def _w16(n=5):
    cols = {name: np.zeros(n, dtype=np.int64) for name, t in AP.POPULATION_COLUMNS[:19] if not pa.types.is_string(t)}
    cols.update({name: np.full(n, "", dtype=object) for name, t in AP.POPULATION_COLUMNS[:19]
                 if pa.types.is_string(t)})
    cols["agent_id"] = np.arange(n)
    cols["kind"] = np.array([1, 0, 3, 6, 8][:n])
    cols["age"] = np.arange(n) + 20
    cols["synthetic"] = np.zeros(n, dtype=bool)
    cols["is_foreign"] = np.zeros(n, dtype=bool)
    return cols


def test_merge_keeps_w16_rows_and_sorts_by_agent_id():
    w16 = _w16()
    keep = np.array([True, False, False, True, True])
    w21 = AP.w21_population_columns(_people(2), _persons(), _money(2), ["ext_a", "ext_b"], base=5)
    pop = AP.merge_population(w16, keep, w21)
    assert pop["agent_id"].tolist() == [0, 3, 4, 5, 6]
    assert pop["kind"].tolist() == [1, 6, 8, 3, 2]
    assert pop["w21_person_id"].tolist() == [-1, -1, -1, 0, 1]
    assert pop["wage_monthly"].tolist()[:3] == [-1, -1, -1]
    bad = AP.w21_population_columns(_people(2), _persons(), _money(2), ["ext_a", "ext_b"], base=3)
    with pytest.raises(ValueError):
        AP.merge_population(w16, keep, bad)


# ================================================================================ W17 の提供者
def _w17(ids, rows_per=3):
    aid = np.repeat(np.asarray(ids), rows_per)
    m = aid.size
    return {"agent_id": aid, "day": np.tile(np.arange(rows_per), len(ids)) % 7, "seq": np.zeros(m, dtype=np.int64),
            "start_min": np.tile([0, 480, 1080], len(ids))[:m], "end_min": np.tile([480, 1080, 1439], len(ids))[:m],
            "activity_code": np.tile([0, 4, 0], len(ids))[:m], "place_kind": np.tile([0, 1, 0], len(ids))[:m],
            "target_cell": np.tile([9, 99, 9], len(ids))[:m], "block_kind": np.zeros(m, dtype=np.int64)}


def _donors(ids, kind, work, sex, age):
    n = len(ids)
    return {"agent_id": np.asarray(ids), "kind": np.asarray(kind), "work": np.asarray(work),
            "entry": np.zeros(n, dtype=np.int64), "school": np.zeros(n, dtype=np.int64), "sex": np.asarray(sex),
            "age": np.asarray(age)}


def _recips(kind, work, sex, age, home, workc):
    n = len(kind)
    return {"new_id": 1000 + np.arange(n), "person_id": np.arange(n), "kind": np.asarray(kind),
            "work": np.asarray(work), "entry": np.zeros(n, dtype=np.int64), "school": np.zeros(n, dtype=np.int64),
            "sex": np.asarray(sex), "age": np.asarray(age), "home_cell": np.asarray(home),
            "work_cell": np.asarray(workc)}


def test_donor_rows_are_copied_and_cells_retargeted():
    d = _donors([10, 11, 12], [0, 0, 3], [1, 1, 0], [0, 0, 1], [30, 31, 50])
    r = _recips([0, 0, 0, 3], [1, 1, 1, 0], [0, 0, 0, 1], [33, 34, 32, 52], [-1, -1, -1, 77], [55, 56, 57, -1])
    rows, of, info = AP.donor_schedules(_w17([10, 11, 12]), d, r, seed=7)
    assert set(of["donor_agent_id"][:3].tolist()) == {10, 11}  # 同じ層(種別 0・勤め先あり・男・30〜34)
    assert of["donor_agent_id"][3] == 12 and (of["level"] == 0).all()
    assert info["recipients_with_reused_donor"] == 2 and info["max_reuse"] == 2  # 3 人に 2 人=使っていない人から
    aid = np.asarray(rows["agent_id"])
    pk = np.asarray(rows["place_kind"])
    cell = np.asarray(rows["target_cell"])
    assert sorted(set(aid.tolist())) == [1000, 1001, 1002, 1003]
    for j, (home, work) in enumerate(((-1, 55), (-1, 56), (-1, 57), (77, -1))):
        m = aid == 1000 + j
        assert (cell[m & (pk == 0)] == home).all()
        if work >= 0:
            assert (cell[m & (pk == 1)] == work).all()
    # 決定的(同じ seed で同じ・違う seed で並べ替えが変わりうる)
    rows2, of2, _ = AP.donor_schedules(_w17([10, 11, 12]), d, r, seed=7)
    assert np.array_equal(of["donor_agent_id"], of2["donor_agent_id"])


def test_donor_reuse_over_the_limit_stops():
    """〔検収 L4〕1 人の提供者を使ってよい回数(3 回)に達したら使わない=受け手が残れば止まる(合成の入力)。"""
    d = _donors([10], [0], [1], [0], [30])
    r = _recips([0] * 4, [1] * 4, [0] * 4, [30] * 4, [-1] * 4, [5] * 4)
    with pytest.raises(ValueError, match="提供者の決まらない受け手 1 人"):
        AP.donor_schedules(_w17([10]), d, r, seed=1)
    _rows, _of, info = AP.donor_schedules(_w17([10]), d, r, seed=1, max_reuse=4)
    assert info["max_reuse"] == 4 and info["max_reuse_limit"] == 4
    assert AP.DONOR_MAX_REUSE == 3


def test_crews_take_the_functional_quota_and_crew_donors_by_role():
    """〔検収 M2〕担当の体は機能定員まで(人ごとの Philox の順)・乗務員の提供者は同じ担当の語から・居なければ止まる。"""
    pid = np.arange(8)
    duty = np.array(["警察官"] * 5 + ["駅員"] * 2 + [""], dtype=object)
    sel = AP.select_crews(pid, duty, {"警察官": 2, "駅員": 9, "消防士": 3}, seed=1)
    assert int(sel[:5].sum()) == 2 and sel[5:7].all() and not sel[7]
    assert np.array_equal(sel, AP.select_crews(pid, duty, {"警察官": 2, "駅員": 9, "消防士": 3}, seed=1))
    cd = {"agent_id": np.array([50, 51, 52]), "role": np.array([0, 0, 4]), "sex": np.array([0, 1, 0]),
          "age": np.array([30, 40, 50])}
    rc = {"new_id": np.array([900, 901]), "person_id": np.array([0, 1]), "role": np.array([0, 4]),
          "sex": np.array([1, 1]), "age": np.array([41, 22]), "home_cell": np.array([-1, -1]),
          "work_cell": np.array([3, 4]), "school": np.zeros(2, dtype=np.int64)}
    _rows, of, _info = AP.donor_schedules(_w17([50, 51, 52]), cd, rc, seed=1, levels=AP.CREW_DONOR_LEVELS)
    assert of["donor_agent_id"].tolist() == [51, 52] and of["level"].tolist() == [0, 2]
    rc2 = {**rc, "role": np.array([0, 3])}  # 納品ドライバーの提供者が居ない=担当の語は外さない=止まる
    with pytest.raises(ValueError):
        AP.donor_schedules(_w17([50, 51, 52]), cd, rc2, seed=1, levels=AP.CREW_DONOR_LEVELS)
    assert AP.KIND_CREW == 8 and AP.PURPOSE_DUTY == 5


def test_reserved_mask_skips_commuter_and_worker_kinds():
    """〔検収 M2〕差し替えの母集団の W21 の行は、役割の名を持っていても種別 0・2 なら先取りしない(機能定員の外=統計層)。
    W16 の行(``w21_person_id``=−1)と列の無い母集団(本体の v2 の W16)は前と同じ(役割で先取り・本体の v2 の W16 には役割を
    持つ種別 0・2 が居ない=実測)。"""
    from shibuya.agents.population import Population

    n = 5
    z = np.zeros(n, dtype=np.int32)
    args = (None, np.arange(n), np.array([8, 0, 2, 3, 0], np.int8), z.astype(np.int8), np.full(n, 30, np.uint8),
            z.astype(np.int8), z, z, z, z, z, z, z, z.astype(np.int8), z, np.zeros(n, bool), np.zeros(n, bool))
    roles = np.array(["警察官", "警察官", "駅員", "議員", "駅員"], dtype=object)
    swapped = Population(*args, duty_role=roles, w21_person_id=np.array([0, 1, 2, 3, -1], np.int32))
    assert swapped.reserved_mask.tolist() == [True, False, False, True, True]  # 最後=W16 の行(種別 0)は前と同じ
    w16 = Population(*args, duty_role=roles)
    assert w16.reserved_mask.tolist() == [True] * n


def test_donor_levels_widen_and_missing_kind_stops():
    d = _donors([10], [0], [1], [1], [70])
    r = _recips([0], [1], [0], [20], [-1], [5])
    _rows, of, info = AP.donor_schedules(_w17([10]), d, r, seed=1)
    assert of["level"][0] == 2 and info["level_counts"]["kind+work+entry+school"] == 1  # 年齢と男女を外して見つかる
    with pytest.raises(ValueError):
        AP.donor_schedules(_w17([10]), d, _recips([3], [0], [0], [20], [4], [-1]), seed=1)


# ================================================================================ 権利台帳
def _staff():
    return {"holder_kind": np.array(["agent", "agent"], dtype=object), "holder_id": np.array([2, 1]),
            "object_kind": np.array(["store", "store"], dtype=object), "object_id": np.array([0, 0]),
            "kind": np.array(["employ", "employ"], dtype=object), "source": np.array(["w21c", "w21c"], dtype=object)}


def _rights_b():
    return {"holder_kind": np.array(["agent", "org", "agent", "store"], dtype=object),
            "holder_id": np.array([0, 3, 1, 0]),
            "object_kind": np.array(["org", "store", "dwelling", "parcel"], dtype=object),
            "object_id": np.array([3, 0, 1, 0]), "kind": np.array(["employ", "own", "lease", "lease"], dtype=object),
            "source": np.array(["a", "b", "c", "d"], dtype=object)}


def test_rights_rows_pass_the_engine_initial_table(tmp_path):
    from shibuya.engine.rights import initial as RI
    from shibuya.engine.rights.ledger import AGENT, DWELLING, EMPLOY, STORE

    rows = AP.rights_run_rows(_staff(), _rights_b(), base=100)
    assert rows["block"].tolist() == ["store_staff", "store_staff", "dwelling"]
    assert rows["holder_agent_id"].tolist() == [102, 101, 101]
    # 〔検収 M3〕外の雇用主の行(人の番号 → 組織の番号 2^31−1)=engine の表と同じ値
    oe = AP.rights_run_rows(_staff(), _rights_b(), base=100, outside_employer=np.array([1]))
    assert oe["block"].tolist()[-1] == "outside_employer" and oe["object_id"].tolist()[-1] == AP.OUTSIDE_EMPLOYER_ORG
    assert AP.OUTSIDE_EMPLOYER_ORG == RI.OUTSIDE_EMPLOYER_ORG
    spec = (("holder_agent_id", pa.int64()), ("holder_person_id", pa.int64()), ("object_kind", pa.string()),
            ("object_id", pa.int64()), ("kind", pa.string()), ("source", pa.string()), ("block", pa.string()))
    pq.write_table(pa.table(AP._table(rows, spec)), tmp_path / RI.RUN_ROWS_FILE)
    # ランの体=agent_id 100〜102 のうち 101・102(100 は抽出で外れた)
    got = RI.load_run_rows(tmp_path, np.array([102, 101]))
    assert len(got) == 3 and got.dropped == 0 and got.holder.tolist() == [0, 1, 1]
    rights = RI.build_initial(np.array([0, 0]), 2, None, rows=got)
    staff = RI.staff_of_poi(rights, 2, 0)
    assert staff.tolist() == [0, -1]  # 店ごとの最初の行=担当
    assert rights.holds((AGENT, 1), EMPLOY, (STORE, 0), 0)
    assert rights.holds((AGENT, 1), "lease", (DWELLING, 1), 0)
    with pytest.raises(ValueError):
        AP.rights_run_rows({**_staff(), "kind": np.array(["own", "employ"], dtype=object)}, _rights_b(), base=0)


# ================================================================================ W20 の口
def test_w20_direct_rows_from_eight_statuses_and_unknown_stops():
    n = 8
    attrs = W20.Attributes(
        agent_id=np.arange(n), kind=np.zeros(n, dtype=np.int64), age=np.full(n, 40), industry=[""] * n,
        duty_role=[""] * n, occupation=[""] * n, employment_pool=["正規"] * n, employed=np.ones(n, dtype=bool),
        workplace=np.full(n, W20.WP_AREA, dtype=np.int8), school=np.zeros(n, dtype=bool),
        work_cell=np.zeros(n, dtype=np.int64), school_cell=np.full(n, -1), home_cell=np.full(n, -1),
        lead_min=np.full(n, -1), census_middles=[()] * n, place_hint=np.zeros(n, dtype=np.int8),
        shift=np.zeros(n, dtype=bool))
    words = np.array(["regular", "dispatched", "executive", "employer", "self_employed", "family_worker",
                      "home_worker", "part_time"], dtype=object)
    anchor = {"employment_mix": {"非正規": {"パート": 0.5, "アルバイト": 0.25, "契約社員": 0.15, "嘱託": 0.05,
                                           "派遣社員": 0.05}}}
    emp = WP.employment_from_w21(attrs, words, anchor)
    rows = [W20.EMP_ROWS[i] for i in emp.emp_row[:7]]
    assert rows == ["正規の職員・従業員", "派遣社員", "会社などの役員", "雇人のある業主", "雇人のない業主", "家族従業者",
                    "雇人のない業主"]
    assert W20.EMP_ROWS[emp.emp_row[7]] in WP.PART_TIME_ROWS  # パートは派遣を除く 4 行の按分
    assert emp.status.tolist()[:3] == [W20.ST_INDEF, W20.ST_FIXED_TERM, W20.ST_OFFICER]
    with pytest.raises(WP.UnknownEmploymentStatusError):
        WP.employment_from_w21(attrs, np.array(["regular"] * 7 + ["serf"], dtype=object), anchor)


def test_rail_lead_stays_blank_for_the_w20_default():
    """〔親の判断=検収 L6〕電車の人の片道は空欄(W20 の既定 30 分)=舞台の中の道のりでは埋めない。"""
    lead = WP.lead_minutes(np.array(["rail", "walk", "home", "rail", ""], dtype=object), np.array([241, 900, 0, -1, -1]))
    assert lead[0] == W20.BLANK and lead[1] >= 1 and lead[2] == 0 and lead[3] == W20.BLANK and lead[4] == W20.BLANK


@pytest.mark.requires_data("world_v2")
def test_w20cal_params_are_the_337_version():
    hdr = DATA / "world" / "v2_stage_3-1" / W20.HEADER_NAME
    if not hdr.exists():
        pytest.skip("requires_data: v2_stage_3-1 の W20cal の見出しが無い")
    h = json.loads(hdr.read_text(encoding="utf-8"))
    rules = REPO / W20.RULES_TABLE_RELPATH
    params = W20.stage_params(W20.N_WEEKS, W20.load_weekly_rest_rule(rules))
    from shibuya.build.geo import common as C

    assert C.param_hash(params) == h["param_hash"]


# ================================================================================ 出力先の守りと版
def test_output_guard_and_versions(tmp_path):
    data = tmp_path / "data"
    world = data / "world" / "v2"
    world.mkdir(parents=True)
    for bad in (world, world / "x", data / "world" / "v2_stage_4-1c"):
        with pytest.raises(AP.ProtectedOutputErrorApply):
            AP.check_out_apply(data, bad, world)
    AP.check_out_apply(data, data / "world" / AP.SWAP_ASSET, world)
    AP.check_out_apply(data, tmp_path / "elsewhere", world)
    assert AP.main(["--out", str(world), "--data", str(data)]) == 2
    assert BB.STAGE_VERSION_B == "1.2.0" and BC.STAGE_VERSION_C == "1.3.0"
    assert BC.STAGE10_ROWS_OF_DECLARATIONS == ()
    # 段 4〜7・段 8〜10 は差し替えの置き場にも組める(同じ置き場は --in-place のときだけ)
    base = data / "world" / AP.SWAP_ASSET
    base.mkdir(parents=True)
    BB.check_out_b(data, base, world, data / "world" / "v2_stage_4-1")
    with pytest.raises(BC.ProtectedOutputErrorC):
        BC.check_out_c(data, base, world, base)
    BC.check_out_c(data, base, world, base, in_place=True)


# ================================================================================ 活性化の道具
def test_activation_plan_table_and_verify(tmp_path):
    t = _tool()
    live, stage = tmp_path / "live", tmp_path / "stage"
    for d in (live, stage):
        (d / "acceptance").mkdir(parents=True)
    (live / "a.bin").write_bytes(b"1")
    (live / "b.bin").write_bytes(b"2")
    (live / "w17_prompts.0of7.jsonl").write_bytes(b"skip")
    (stage / "a.bin").write_bytes(b"1")
    (stage / "b.bin").write_bytes(b"3")
    (stage / "c.bin").write_bytes(b"4")
    (stage / t.MANIFEST).write_bytes(b"x")
    for d, bh in ((live, "old"), (stage, "new")):
        (d / "build_manifest.json").write_text(json.dumps({"build_hash": bh}), encoding="utf-8")
    plan = t.plan_rows(live, stage)
    acts = {r["path"]: r["action"] for r in plan["rows"]}
    assert acts == {"a.bin": "same", "b.bin": "moved", "c.bin": "added", "build_manifest.json": "moved"}
    assert plan["build_hash_before"] == "old" and plan["build_hash_after"] == "new"
    changed = [r for r in plan["rows"] if r["action"] in ("moved", "added")]
    assert t._check(live, changed, "before") == [] and t._check(stage, changed, "after") == []
    assert t._check(live, changed, "after")  # 前の本体は「後」と違う
    # apply → verify → revert を作業用の写しで(本体の v2 は書かない)
    rec = {**{k: v for k, v in plan.items() if k != "rows"}, "changed": changed, "rows": plan["rows"]}
    pfile = tmp_path / "plan.json"
    pfile.write_text(json.dumps(rec), encoding="utf-8")
    args = ["--live", str(live), "--stage", str(stage), "--backup", str(tmp_path / "pre"), "--plan", str(pfile)]
    assert t.main(["apply", *args]) == 0
    assert (tmp_path / "pre" / "b.bin").read_bytes() == b"2" and not (tmp_path / "pre" / "w17_prompts.0of7.jsonl").exists()
    assert t.main(["verify", *args, "--want", "after"]) == 0
    assert t.main(["revert", "--live", str(live), "--backup", str(tmp_path / "pre")]) == 0
    assert (live / "b.bin").read_bytes() == b"2" and not (live / "c.bin").exists()
    assert t.main(["verify", *args, "--want", "before"]) == 0
    # 〔検収 M4〕same の 1 本を壊しても verify は見つける(全部の行の sha を確かめる)・changed だけの記録は止める
    (live / "a.bin").write_bytes(b"broken")
    assert t.main(["verify", *args, "--want", "before"]) == 1
    old = tmp_path / "old_plan.json"
    old.write_text(json.dumps({k: v for k, v in rec.items() if k != "rows"}), encoding="utf-8")
    with pytest.raises(RuntimeError):
        t.main(["verify", "--live", str(live), "--plan", str(old)])


# ================================================================================ 実データ(組んだ資産)
REAL = pytest.mark.requires_data("world_stage_4-3")
#: golden(記録 pop43/README.md の資産・seed 20260909)。
#: 〔検収の直し〕通学者を残した(前の値 population 312,473・w16_kept 96,681・w16_removed 293,386)。
GOLDEN_COUNTS = {"population": 345858, "w16_kept": 130066, "w16_removed": 260001, "w21_added": 215792,
                 "base_agent_id": 390067}


@REAL
def test_real_asset_gates_and_counts():
    man = json.loads((STAGE / AP.MANIFEST_APPLY).read_text(encoding="utf-8"))
    for k, v in GOLDEN_COUNTS.items():
        assert man["counts"][k] == v, k
    h = json.loads((STAGE / f"{AP.STAGE_APPLY}.header.json").read_text(encoding="utf-8"))
    assert all(g["pass"] for g in h["gates"].values())
    for o in man["outputs"]:
        import hashlib

        assert hashlib.sha256((STAGE / o["path"]).read_bytes()).hexdigest() == o["sha256"], o["path"]


@REAL
def test_real_engine_reads_the_swapped_population_and_w17():
    from shibuya.agents.population import load_population
    from shibuya.agents.weekly import load_weekly

    pop = load_population(STAGE)
    assert pop.is_swapped and pop.n == GOLDEN_COUNTS["population"]
    assert int((pop.w21_person_id >= 0).sum()) == GOLDEN_COUNTS["w21_added"]
    wk = load_weekly(STAGE)
    sub = wk.restrict_to(pop.source_agent_id)  # 全員の行がある(無ければ KeyError)
    assert sub.n_agents == pop.n
    small = load_population(STAGE, n=5000, seed=1)
    assert small.n == 5000 and small.is_swapped
    # 〔検収 M2〕先取りは機能定員まで(W21 の種別 8 の体)・定員の外の担当の体(種別 0・2)は先取りしない
    assert int(small.reserved_mask.sum()) == int(pop.reserved_mask.sum()) < 1000
    k8 = (pop.kind == 8) & (pop.w21_person_id >= 0)
    assert int(k8.sum()) == 366 and (pop.purpose[k8] == 5).all()
    roles = np.asarray(pop.duty_role, dtype=object)
    assert not (pop.reserved_mask & np.isin(pop.kind, [0, 2])).any() and (roles[pop.kind == 0] == "警察官").sum() > 0


# ================================================================================ 段 9 の口(親の判断 (5)・(7)・(9))
def test_number_meter_skips_digits_inside_names():
    """〔仮-33 (5)〕名(POI と組織の名)の中の数字は数字の計器から除く(名を渡さなければ今までどおり数える)。"""
    sys.path.insert(0, str(REPO / "tools" / "instruments"))
    from dm_eval import situations as DS

    text = "なじみの場所: SHIBUYA109(店)・カフェ 7(飲食店)。月の給料はおよそ31万円。"
    assert DS.numbers_outside_money_time(text) == 2
    assert DS.numbers_outside_money_time(text, names=["SHIBUYA109", "カフェ 7"]) == 0
    assert DS.numbers_outside_money_time(text, names=["カフェ 7"]) == 1


def test_commute_line_and_substitute_language_in_persona():
    """〔仮-33 (9)〕電車の人の通勤の行に通う駅の口の路線の名・〔(7)〕型の無い言語は日本語の型で代えて印。"""
    from shibuya.build.pop import w21_persona as P

    assert P.SUBSTITUTE_BASIS == "substitute_ja" and "commute_line" in P.FACT_COLUMNS
    lang, basis = P.persona_langs({"first_language": np.array(["ko", "", "en"], dtype=object),
                                   "nationality": np.array(["韓国", "フィリピン", "米国"], dtype=object)})
    assert lang.tolist() == ["ja", "ja", "en"] and basis.tolist() == ["substitute_ja", "substitute_ja", "first_language"]
