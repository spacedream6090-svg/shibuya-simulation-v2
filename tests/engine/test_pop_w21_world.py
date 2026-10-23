"""第 4 期 4-3 段 10「差し替え」の engine の読み口の試験(合成の小さな母集団+組んだ資産があれば実データ)。

- 母集団の読み口(``agents.population``): 差し替えの版の列(``w21_person_id``・``wage_monthly``・``persona_occupation``・
  ``persona_employment``)を読む・``take`` と抽出で保つ・列の欠け・知らない種別・知らない語で止まる(負の対照)・本体の v2 の形
  (列なし)は 4 つとも ``None``。
- 賃金の入力(``engine.economy_stage2.wage_inputs``): 在庫の行の無い W21 の人は母集団の語・額は ``given``。
- 権利台帳の初期の行(``engine.rights.initial``): 表の無い世界は今の丸振りと同じ行(並びと出どころ)・表があれば店の担当と
  住まい・閉じた表の外で止まる・差し替えの母集団なのに表が無ければ組み立てが止まる。
- 人物の欄(``engine.decision.persona``): 短い版は B6 の前・長い版は B5 の前(共通部分の頭は同じ)・文の無い体は空・差し替えの
  口(元の文が残る・出どころ・止まる場合)・表に無い人の番号で止まる。
- 実データ(``requires_data("world_stage_4-3")``): 組んだ資産で短いランが回り、権利台帳に住まいの行・W21c の店の担当・残りの店の
  丸振り・外の雇用主の行が入る。
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shibuya.agents import population as POP
from shibuya.engine.decision import persona as PE
from shibuya.engine.decision.port import compose
from shibuya.engine.rights import initial as RI
from shibuya.engine.rights.ledger import AGENT, DWELLING, EMPLOY, LEASE, PARCEL, STORE

REPO = Path(__file__).resolve().parents[2]
STAGE = REPO / "data" / "world" / "v2_stage_4-3"


def _pop_table(n=6, swapped=True, **over):
    cols = {
        "agent_id": pa.array(np.arange(n), pa.int32()), "kind": pa.array([1, 8, 3, 2, 0, 0][:n], pa.int8()),
        "purpose": pa.array([3, 5, 4, 4, 0, 0][:n], pa.int8()), "age": pa.array([30, 40, 50, 35, 28, 45][:n], pa.uint8()),
        "sex": pa.array([0, 1, 0, 1, 0, 1][:n], pa.int8()), "home_cell": pa.array([-1, -1, 3, 4, -1, -1][:n], pa.int32()),
        "work_cell": pa.array([-1, 2, -1, 4, 5, 6][:n], pa.int32()), "school_cell": pa.array([-1] * n, pa.int32()),
        "direction_node": pa.array([0, 1, -1, -1, 2, 3][:n], pa.int32()),
        "chome_key": pa.array([""] * n, pa.string()), "household_id": pa.array([-1, -1, 0, 1, -1, -1][:n], pa.int32()),
        "home_building": pa.array([-1] * n, pa.int32()), "org_id": pa.array([-1, -1, -1, 2, 3, -1][:n], pa.int32()),
        "industry_key": pa.array([""] * n, pa.string()), "duty_role": pa.array(["", "バス運転士", "", "", "駅員", ""][:n],
                                                                                 pa.string()),
        "pool_layer": pa.array([4, 5, -1, -1, -1, -1][:n], pa.int8()), "pool_index": pa.array([1, 2, -1, -1, -1, -1][:n],
                                                                                              pa.int32()),
        "synthetic": pa.array([False] * n, pa.bool_()), "is_foreign": pa.array([False] * n, pa.bool_()),
    }
    if swapped:
        cols.update({
            "w21_person_id": pa.array([-1, -1, 0, 1, 2, 3][:n], pa.int32()),
            "wage_monthly": pa.array([-1, -1, -1, 300000, 250000, 400000][:n], pa.int64()),
            "persona_occupation": pa.array(["", "", "", "事務従事者", "輸送・機械運転従事者", "販売従事者"][:n], pa.string()),
            "persona_employment": pa.array(["", "", "", "正規", "非正規", "役員"][:n], pa.string()),
        })
    cols.update(over)
    return pa.table(cols)


def _write(tmp_path, table):
    pq.write_table(table, tmp_path / POP.POPULATION_FILE)
    return tmp_path


# ================================================================================ 母集団
def test_swapped_population_is_read_and_kept_through_take_and_sampling(tmp_path):
    pop = POP.load_population(_write(tmp_path, _pop_table()))
    assert pop.is_swapped
    assert pop.w21_person_id.tolist() == [-1, -1, 0, 1, 2, 3]
    assert pop.wage_monthly.tolist()[3:] == [300000, 250000, 400000]
    sub = pop.take(np.array([5, 3]))
    assert sub.persona_employment.tolist() == ["役員", "正規"] and sub.w21_person_id.tolist() == [3, 1]
    small = POP.sample_population(pop, 4, seed=1)
    assert small.is_swapped and small.n == 4
    # 駅員は定員先取り層(W21 の担当の体も同じ規則)
    assert 4 in small.source_agent_id.tolist()


def test_w16_shaped_population_has_no_swap_columns(tmp_path):
    pop = POP.load_population(_write(tmp_path, _pop_table(swapped=False)))
    assert not pop.is_swapped
    assert pop.wage_monthly is None and pop.persona_occupation is None and pop.w21_person_id is None
    assert pop.take(np.array([0])).wage_monthly is None


def test_missing_columns_and_unknown_words_stop(tmp_path):
    t = _pop_table().drop(["wage_monthly"])
    with pytest.raises(POP.PopulationSchemaError):
        POP.load_population(_write(tmp_path, t))
    t = _pop_table(kind=pa.array([1, 8, 3, 2, 0, 9], pa.int8()))
    with pytest.raises(POP.PopulationSchemaError):
        POP.load_population(_write(tmp_path, t))
    t = _pop_table(persona_employment=pa.array(["", "", "", "正規", "奴隷", "役員"], pa.string()))
    with pytest.raises(POP.PopulationSchemaError):
        POP.load_population(_write(tmp_path, t))
    t = _pop_table(persona_occupation=pa.array(["", "", "", "勇者", "", ""], pa.string()))
    with pytest.raises(POP.PopulationSchemaError):
        POP.load_population(_write(tmp_path, t))


def test_wage_inputs_take_w21_words_and_given_wages(tmp_path, monkeypatch):
    from shibuya.engine import economy_stage2 as ES2

    pop = POP.load_population(_write(tmp_path, _pop_table()))
    monkeypatch.setattr(ES2, "persona_words",
                        lambda root, lay, idx, fields=ES2.PERSONA_FIELDS: ({f: np.array(["在庫の語"] * len(lay),
                                                                                         dtype=object) for f in fields},
                                                                           len(lay)))
    monkeypatch.setattr(ES2, "PERSONA_POOL_RELPATH", str(tmp_path))
    winp = ES2.wage_inputs(type("S", (), {"master_seed": 1})(), pop, pop.n, pool_root=tmp_path)
    occ = [winp.occ_vocab[c] if c >= 0 else "" for c in winp.occ_code]
    emp = [winp.emp_vocab[c] if c >= 0 else "" for c in winp.emp_code]
    assert occ[:2] == ["在庫の語", "在庫の語"] and occ[3:] == ["事務従事者", "輸送・機械運転従事者", "販売従事者"]
    assert emp[3:] == ["正規", "非正規", "役員"]
    assert winp.given.tolist() == [-1, -1, -1, 300000, 250000, 400000]
    assert winp.source.endswith("+w21")


# ================================================================================ 権利台帳
def _old_build_initial(kind, n_poi, org):
    """1-5 の版の組み立て(今の丸振り)の写し=表の無い世界で同じ行になることを見る正解。"""
    out = []
    org = np.asarray(org)
    for a in np.flatnonzero(org >= 0).tolist():
        out.append(((AGENT, a), ("org", int(org[a])), EMPLOY, RI.SOURCE_W16_ORG))
    staff = RI.staff_assignment(kind, n_poi)
    for j in np.flatnonzero(staff >= 0).tolist():
        out.append(((AGENT, int(staff[j])), (STORE, j), EMPLOY, RI.SOURCE_STAFF))
    for j in range(n_poi):
        out.append(((STORE, j), (PARCEL, j), LEASE, RI.SOURCE_POI))
    return out


def test_without_the_table_the_rows_are_the_same_as_before():
    kind = np.array([2, 0, 2, 3, 2])
    org = np.array([1, -1, 4, -1, 0])
    r = RI.build_initial(kind, 7, org)
    got = [(x.holder, x.object, x.kind, x.source) for x in r]
    assert got == _old_build_initial(kind, 7, org)


def _rows_file(tmp_path, **over):
    cols = {"holder_agent_id": pa.array([12, 11, 11, 13], pa.int64()), "holder_person_id": pa.array([2, 1, 1, 3], pa.int64()),
            "object_kind": pa.array(["store", "store", "dwelling", "dwelling"]), "object_id": pa.array([1, 1, 5, 6], pa.int64()),
            "kind": pa.array(["employ", "employ", "own", "lease"]), "source": pa.array(["w21c", "w21c", "w21b", "w21b"]),
            "block": pa.array(["store_staff", "store_staff", "dwelling", "dwelling"])}
    cols.update(over)
    pq.write_table(pa.table(cols), tmp_path / RI.RUN_ROWS_FILE)
    return tmp_path


def test_table_rows_give_store_staff_and_dwellings(tmp_path):
    rows = RI.load_run_rows(_rows_file(tmp_path), np.array([11, 12]))  # 13 はランに居ない
    assert rows.dropped == 1 and rows.holder.tolist() == [1, 0, 0]
    r = RI.build_initial(np.array([0, 0]), 3, np.array([-1, -1]), rows=rows)
    assert RI.staff_of_poi(r, 3, 0).tolist() == [-1, 1, -1]  # 店 1 の最初の行=担当(体 12=行 1)
    assert r.holds((AGENT, 0), "own", (DWELLING, 5), 0)
    t = r.tally()
    assert t["by_object_kind"]["dwelling"] == 1 and t["by_kind"]["lease"] == 3
    with pytest.raises(ValueError):
        RI.load_run_rows(_rows_file(tmp_path, block=pa.array(["store_staff", "x", "dwelling", "dwelling"])), np.array([11]))
    with pytest.raises(ValueError):
        RI.load_run_rows(_rows_file(tmp_path, kind=pa.array(["own", "employ", "own", "lease"])), np.array([11]))
    assert RI.load_run_rows(tmp_path / "nowhere", np.array([1])) is None


def test_swapped_population_without_the_table_stops(tmp_path):
    from shibuya.engine.systems import build as SB

    pop = POP.load_population(_write(tmp_path, _pop_table()))
    with pytest.raises(ValueError):
        SB._initial_rights(tmp_path, pop, pop.n)
    w16 = POP.load_population(_write(tmp_path, _pop_table(swapped=False)))
    assert SB._initial_rights(tmp_path, w16, w16.n) is None


# ================================================================================ 人物の欄
def _persona_files(tmp_path):
    for v in PE.VERSIONS:
        texts = ["人物: 例の人 0。", "人物: 例の人 1。", "", "人物: 例の人 3。"] if v == "short" else [
            "人物: 例の人 0。\n家族: 一人。", "人物: 例の人 1。\n家族: 二人。", "", "人物: 例の人 3。\n家族: 三人。"]
        pq.write_table(pa.table({
            "person_id": pa.array([3, 0, 2, 1], pa.int32()), "text": pa.array([texts[3], texts[0], texts[2], texts[1]]),
            "text_source": pa.array(["facts"] * 4), "lang": pa.array(["ja"] * 4),
            "lang_basis": pa.array(["first_language", "first_language", "substitute_ja", "blank_assumed_ja"]),
            "named_poi": pa.array([[7], [1, 2], [], [3]], pa.list_(pa.int32())),
            "named_org": pa.array([-1, 4, -1, -1], pa.int32()),
        }), tmp_path / PE.PERSONA_FILES[v])
    return tmp_path


def test_persona_blocks_sit_before_b6_and_b5():
    blocks = {b: f"[{b}]" for b in ("B0", "B1", "B2", "B3", "B4", "B4b", "B5", "B6")}
    tab = PE.PersonaTable(texts={"short": np.array(["短い"], dtype=object), "long": np.array(["長い"], dtype=object)},
                          source={"short": np.array(["facts"], dtype=object), "long": np.array(["facts"], dtype=object)},
                          lang=np.array(["ja"], dtype=object), lang_basis=np.array(["first_language"], dtype=object),
                          named_poi={"short": np.array([None], dtype=object), "long": np.array([None], dtype=object)},
                          named_org=np.array([-1]), person_id=np.array([0]))
    s = compose({**blocks, **PE.persona_blocks(tab, 0, "short")}, [], length="short")
    lg = compose({**blocks, **PE.persona_blocks(tab, 0, "long")}, [], length="long")
    assert s.index("短い") < s.index("[B6]") and "[B5]" not in s and "長い" not in s
    assert lg.index("長い") < lg.index("[B5]") < lg.index("[B6]")
    common = "\n".join(f"[{b}]" for b in ("B0", "B1", "B2", "B3", "B4", "B4b"))
    assert s.startswith(common) and lg.startswith(common)
    # 人物の欄の無い入力は今のまま(欄が無ければ 1 バイトも変わらない)
    assert compose(blocks, [], length="short") == "\n".join([common, "[B6]", compose({}, [], length="short")])
    assert PE.persona_blocks(None, 0, "short") == {}


def test_load_persona_maps_run_rows_and_w16_rows_are_blank(tmp_path):
    tab = PE.load_persona(_persona_files(tmp_path), np.array([-1, 3, 0, 2]))
    assert tab.texts["short"].tolist() == ["", "人物: 例の人 3。", "人物: 例の人 0。", ""]
    assert tab.lang_basis.tolist() == ["", "first_language", "first_language", "substitute_ja"]
    assert tab.named_ids(1, "long") == ((7,), -1) and tab.named_ids(2, "long") == ((1, 2), 4)
    assert PE.persona_blocks(tab, 0, "long") == {} and PE.persona_blocks(tab, 2, "short") == {"PS": "人物: 例の人 0。"}
    rec = tab.record()
    assert rec["with_text"] == {"short": 2, "long": 2} and "人物" not in str(rec)
    with pytest.raises(PE.PersonaError):
        PE.load_persona(tmp_path, np.array([9]))  # 表に無い人の番号
    assert PE.load_persona(tmp_path / "nowhere", np.array([0])) is None
    with pytest.raises(AttributeError):
        tab.texts = {}


def test_persona_override_keeps_the_original_and_stops_on_bad_input(tmp_path):
    tab = PE.load_persona(_persona_files(tmp_path), np.array([0, 1]))
    t2 = PE.override(tab, [1], ["LLM が書いた文"], version="long", label="llm_test", meta={"model": "mock"})
    assert t2.texts["long"][1] == "LLM が書いた文" and t2.original["long"][1] == "人物: 例の人 1。\n家族: 二人。"
    assert t2.source["long"].tolist() == ["facts", "override:llm_test"]
    t3 = PE.override(t2, [1], ["もう一度"], version="long", label="again")
    assert t3.original["long"][1] == "人物: 例の人 1。\n家族: 二人。"  # 元の文は最初の 1 回だけ
    assert tab.texts["long"][1] == "人物: 例の人 1。\n家族: 二人。"  # 元の表は書き換えない
    assert t3.record()["overrides"][0]["model"] == "mock"
    for bad in (dict(rows=[5], texts=["x"]), dict(rows=[0, 0], texts=["x", "y"]), dict(rows=[0], texts=["x", "y"])):
        with pytest.raises(PE.PersonaError):
            PE.override(tab, version="short", label="x", **bad)
    with pytest.raises(PE.PersonaError):
        PE.override(tab, [0], ["x"], version="short", label="")


def test_persona_file_names_are_the_w21c_outputs():
    from shibuya.build.pop import w21_build_c as BC

    assert set(PE.PERSONA_FILES.values()) <= set(BC.OUTPUTS_C)


# ================================================================================ 実データ(組んだ資産)
@pytest.mark.requires_data("world_stage_4-3")
def test_real_short_run_has_dwellings_w21_store_staff_and_outside_employers():
    from shibuya import cli

    # 〔段 5-1b〕既定は nav1=段の世界(build_hash あり・nav1_* なし)は止まる → 前の移動(legacy)で回す(この試験は権利の行を見る)
    res = cli.run(n_agents=3000, seed=1, world_dir=str(STAGE), ticks=30, space="legacy")
    man = res.run_manifest_fields()
    r = man["rights"]
    assert r["by_object_kind"]["dwelling"] > 0
    assert any(s.startswith("w21c:") for s, n in r["by_source"].items() if n > 0)
    # 〔親の判断〕表の担当のいない店は丸振りのまま・〔検収 M3〕外の雇用主の行がある
    assert r["by_source"].get(RI.SOURCE_STAFF, 0) > 0 and r["by_source"].get(RI.SOURCE_OUTSIDE_EMPLOYER, 0) > 0
    pop = POP.load_population(STAGE, n=3000, seed=1)
    tab = PE.load_persona(STAGE, pop.w21_person_id)
    assert tab.n == 3000 and tab.record()["with_text"]["long"] == int((pop.w21_person_id >= 0).sum())


def test_stores_without_table_staff_keep_the_round_robin_and_bad_stores_stop(tmp_path):
    """〔検収の直し・親の判断〕表の担当のいない店は今の丸振り(出どころの語を分ける)・表の店の番号が POI の外なら止まる・
    外の雇用主の行(組織の番号 2^31−1)が入る。"""
    _rows_file(tmp_path, holder_agent_id=pa.array([12, 11, 11, 13, 11], pa.int64()),
               holder_person_id=pa.array([2, 1, 1, 3, 1], pa.int64()),
               object_kind=pa.array(["store", "store", "dwelling", "dwelling", "org"]),
               object_id=pa.array([1, 1, 5, 6, RI.OUTSIDE_EMPLOYER_ORG], pa.int64()),
               kind=pa.array(["employ", "employ", "own", "lease", "employ"]),
               source=pa.array(["w21c", "w21c", "w21b", "w21b", RI.SOURCE_OUTSIDE_EMPLOYER]),
               block=pa.array(["store_staff", "store_staff", "dwelling", "dwelling", "outside_employer"]))
    rows = RI.load_run_rows(tmp_path, np.array([11, 12, 20]))
    kind = np.array([2, 2, 2])  # 3 体とも従業者=丸振りの相手
    r = RI.build_initial(kind, 4, np.array([-1, -1, -1]), rows=rows)
    staff = RI.staff_of_poi(r, 4, 0)
    rr = RI.staff_assignment(kind, 4)
    assert staff[1] == 1  # 表の担当(体 12=行 1)
    assert staff[[0, 2, 3]].tolist() == rr[[0, 2, 3]].tolist()  # 担当のいない店は今の丸振り
    t = r.tally()
    assert t["by_source"][RI.SOURCE_STAFF] == 3 and t["by_source"]["w21c"] == 2
    assert r.holds((AGENT, 0), EMPLOY, ("org", RI.OUTSIDE_EMPLOYER_ORG), 0)
    with pytest.raises(ValueError, match="POI"):
        RI.build_initial(kind, 1, None, rows=rows)  # 店 1 は POI 1 個の外
