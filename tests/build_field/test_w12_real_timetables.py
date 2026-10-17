"""W12 の実ダイヤの読み口(第 2 期 2-3b・``build/field/w12_real_timetables.py``)。

data の要らない試験(CI で走る): 方面の写像の表・合成の CSV 3 行の読み・会社/方面の照らし・暦の写像・運行日の分
(T0 の定数で計算)・重複の除去・臨時の特急を外す規則(◆ の確かめ)・ODPT の列車時刻表の読み(合成の 2 列車)・
「等間隔で残る線が 0」の静的な検査・世界の時点が暦の既定と同じ・W19 の入力の層。

data の要る試験(``requires_data("user_timetables", "odpt_static", …)``・data の無い CI では飛ぶ): ``run()`` を一時の
置き場で回し、線ごとの本数が記録の md の golden と一致・残る等間隔の線 0・土休 ≦ 平日・版の表・切替口 False で
1.1.0 の本数に戻る・方面ノードと生成の重みは動かない。時刻そのものは比べない(記録に写さないので golden にも無い)。
"""

from __future__ import annotations

import json
import re
import shutil
from collections import Counter
from pathlib import Path

import pytest

from shibuya.build.audit import w19_freeze as W19
from shibuya.build.field import common as C
from shibuya.build.field import w12_external_nodes as w12
from shibuya.build.field import w12_real_timetables as RT
from shibuya.core.time_consts import MINUTES_PER_DAY, MINUTES_PER_HOUR
from tests import _data_ids as D

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
WORLD = DATA_DIR / "world" / "v2"
RECORD = REPO_ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "tt23b" / "README.md"
_UPSTREAM = ("w11_station_exits.parquet", "w1_nodes.parquet", "w1_edges.parquet")

#: 方面の写像の表(docstring の表と同じ=設計の写し。変えるときは記録と docstring も直す)。
EXPECTED_MAPPING: dict[str, tuple[str, str]] = {
    "JR_山手線_渋谷_内回り": ("山手線", "上り"),
    "JR_山手線_渋谷_外回り": ("山手線", "下り"),
    "JR_埼京線_渋谷_大宮方面": ("埼京線", "下り"),
    "JR_埼京線_渋谷_大崎方面": ("埼京線", "上り"),
    "JR_相鉄線直通_渋谷_相鉄線方面": ("埼京線", "上り"),
    "JR_湘南新宿ライン_渋谷_北行": ("湘南新宿ライン", "下り"),
    "JR_湘南新宿ライン_渋谷_南行": ("湘南新宿ライン", "上り"),
    "東急_東横線_渋谷_横浜方面": ("東横線", "下り"),
    "東急_副都心線_渋谷_和光市方面": ("東横線", "上り"),
    "東急_田園都市線_渋谷_中央林間方面": ("田園都市線", "下り"),
    "東急_半蔵門線_渋谷_押上方面": ("田園都市線", "上り"),
    "京王_井の頭線_渋谷_吉祥寺方面": ("井の頭線", "下り"),
}

_HEADER = "会社,路線,駅,方面,平日土休,時,分,種別,行き先,版,md5,読み"


def _spec(stem: str) -> RT.TableSpec:
    return next(s for s in RT.USER_TABLES if s.stem == stem)


def _write_csv(path: Path, rows: list[str]) -> Path:
    path.write_text("﻿" + _HEADER + "\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return path


# ---------------------------------------------------------------------- data 不要
def test_mapping_table_is_the_declared_one():
    got = {s.stem: (s.line, s.direction) for s in RT.USER_TABLES}
    assert got == EXPECTED_MAPPING
    # 方向の値の集まりは今の W12 と同じ(エンジンの didx を振り直さない)
    assert {s.direction for s in RT.USER_TABLES} == {"上り", "下り"}
    # 渋谷の発車の表だけ(到着・他の駅・成田エクスプレスの表は一覧に無い)
    stems = " ".join(got)
    for word in ("到着", "神泉", "原宿", "明治神宮前", "代々木", "表参道", "池尻大橋", "代官山", "成田エクスプレス"):
        assert word not in stems, word
    # 湘南新宿ラインは埼京線に畳む(切替口 fold_lines={} で畳まない)
    assert RT.FOLD_LINES == {"湘南新宿ライン": "埼京線"}


def test_synthetic_csv_three_rows_map_to_w12_rows(tmp_path):
    spec = _spec("JR_相鉄線直通_渋谷_相鉄線方面")
    p = _write_csv(tmp_path / spec.file_name("平日"), [
        "JR東日本,相鉄線直通,渋谷,相鉄線方面(下り),平日,6,5,普通,海老名,v,x,1=2",
        "JR東日本,相鉄線直通,渋谷,相鉄線方面(下り),平日,23,59,普通,海老名,v,x,1=2",
        "JR東日本,相鉄線直通,渋谷,相鉄線方面(下り),平日,0,7,普通,海老名,v,x,1=2",
    ])
    rows = RT.rows_from_table(spec, "平日", RT.read_csv_rows(p))
    assert [r["departure"] for r in rows] == ["06:05", "23:59", "00:07"]
    assert {(r["line"], r["direction"], r["calendar"], r["operator"], r["source"]) for r in rows} == {
        ("埼京線", "上り", "Weekday", "JR東日本", RT.SRC_JR)  # 題名は下りでも向き(南行)で上り
    }
    folded = RT.fold(RT.rows_from_table(_spec("JR_湘南新宿ライン_渋谷_北行"), "土休", [
        {"会社": "JR東日本", "路線": "湘南新宿ライン", "駅": "渋谷", "方面": "高崎・宇都宮方面(北行)",
         "平日土休": "土休", "時": "7", "分": "1", "種別": "快速", "版": "v"}]), RT.FOLD_LINES)
    assert (folded[0]["line"], folded[0]["line_raw"], folded[0]["direction"]) == ("埼京線", "湘南新宿ライン", "下り")
    assert RT.fold(folded, {})[0]["line"] == "埼京線"  # 畳んだ行は戻さない(畳むのは読みの段で 1 回)


def test_rows_from_table_rejects_a_wrong_heading_or_station(tmp_path):
    spec = _spec("JR_山手線_渋谷_内回り")
    bad_heading = [{"会社": "JR東日本", "路線": "山手線", "駅": "渋谷", "方面": "新宿・池袋方面(外回り)",
                    "平日土休": "平日", "時": "5", "分": "0"}]
    with pytest.raises(ValueError):
        RT.rows_from_table(spec, "平日", bad_heading)
    bad_station = [{**bad_heading[0], "方面": spec.heading, "駅": "原宿"}]
    with pytest.raises(ValueError):
        RT.rows_from_table(spec, "平日", bad_station)
    bad_cal = [{**bad_heading[0], "方面": spec.heading, "平日土休": "土休"}]
    with pytest.raises(ValueError):
        RT.rows_from_table(spec, "平日", bad_cal)


def test_calendar_mapping_and_file_names():
    assert RT.CALENDAR_OF == {"平日": "Weekday", "土休": "SaturdayHoliday"}
    s = _spec("東急_東横線_渋谷_横浜方面")
    assert s.file_name("土休") == "東急_東横線_渋谷_横浜方面_土休_final.csv"
    k = _spec("京王_井の頭線_渋谷_吉祥寺方面")
    assert k.file_name("平日") == "京王_井の頭線_渋谷_吉祥寺方面_平日_odpt.csv"
    assert k.rel_dir() == RT.ODPT_CHALLENGE_DIR


@pytest.mark.parametrize("h,m", [(0, 7), (0, 59), (4, 37), (12, 0), (23, 59)])
def test_departure_min_is_the_service_day_minute(h, m):
    dep = RT.hhmm(h, m)
    raw = h * MINUTES_PER_HOUR + m
    want = raw + MINUTES_PER_DAY if raw < w12.SERVICE_DAY_CUT_MIN else raw
    assert w12._minute(dep) == want


def test_hhmm_rejects_out_of_range():
    for h, m in ((24, 0), (-1, 0), (5, 60)):
        with pytest.raises(ValueError):
            RT.hhmm(h, m)


def test_dedup_keeps_the_first_and_counts():
    base = {"line": "埼京線", "direction": "下り", "calendar": "Weekday", "departure": "07:01", "source": "a"}
    rows = [base, {**base, "source": "b"}, {**base, "departure": "07:02"}, {**base, "calendar": "SaturdayHoliday"}]
    out, removed = RT.dedup(rows)
    assert [r["source"] for r in out] == ["a", "a", "a"]
    assert removed == {"埼京線|下り|Weekday": 1}


def test_temporary_trains_need_the_diamond_mark():
    r = {"source": RT.SRC_JR, "train_type": "特急(踊り子)", "table": "JR_湘南新宿ライン_渋谷_南行",
         "calendar": "SaturdayHoliday", "_hm": (10, 3)}
    other = {**r, "train_type": "快速"}
    keep, drop = RT.split_temporary([r, other], {("JR_湘南新宿ライン_渋谷_南行", "土休", 10, 3): "◆▲〔東〕"})
    assert drop == [r] and keep == [other]
    with pytest.raises(ValueError):
        RT.split_temporary([r], {})
    # JR の表の外(東急など)には当てない
    keep2, drop2 = RT.split_temporary([{**r, "source": RT.SRC_TOKYU}], {})
    assert drop2 == [] and len(keep2) == 1


def test_odpt_train_timetable_two_synthetic_trains():
    sp = RT.GINZA_SPEC
    shibuya = sp.origin_station
    doc = {"data": [
        {"odpt:railway": sp.railway, "odpt:calendar": "odpt.Calendar:Weekday", "dct:issued": "2026-09-19",
         "dc:date": "d", "odpt:railDirection": "odpt.RailDirection:TokyoMetro.Asakusa",
         "odpt:originStation": [shibuya], "odpt:trainType": "odpt.TrainType:TokyoMetro.Local",
         "odpt:trainTimetableObject": [{"odpt:departureTime": "00:05", "odpt:departureStation": shibuya},
                                       {"odpt:departureTime": "00:07", "odpt:departureStation": "x"}]},
        {"odpt:railway": sp.railway, "odpt:calendar": "odpt.Calendar:SaturdayHoliday", "dct:issued": "2026-09-19",
         "odpt:railDirection": "odpt.RailDirection:TokyoMetro.Shibuya", "odpt:originStation": ["u"],
         "odpt:trainTimetableObject": [{"odpt:departureTime": "06:00", "odpt:departureStation": "u"},
                                       {"odpt:arrivalTime": "06:30", "odpt:arrivalStation": shibuya}]},
        {"odpt:railway": "odpt.Railway:TokyoMetro.Hanzomon", "odpt:calendar": "odpt.Calendar:Weekday",
         "odpt:trainTimetableObject": [{"odpt:departureTime": "06:00", "odpt:departureStation": shibuya}]},
    ]}
    rows, check = RT.parse_train_timetable_departures(doc, sp)
    assert [(r["line"], r["calendar"], r["direction"], r["departure"], r["source"]) for r in rows] == [
        ("銀座線", "Weekday", "TokyoMetro.Asakusa", "00:05", RT.SRC_GINZA)
    ]
    assert check["n_trains_of_railway"] == 2 and check["n_departures_from_origin"] == 1
    assert check["dct_issued"] == {"2026-09-19": 1} and check["origin_station_field_mismatch"] == 0
    bad = {"data": [{**doc["data"][0], "odpt:calendar": "odpt.Calendar:Specific.X"}]}
    with pytest.raises(ValueError):
        RT.parse_train_timetable_departures(bad, sp)


def test_no_rail_line_is_left_for_equal_interval_statically():
    """方面ノードの線は全部、実ダイヤの表(畳みを含む)かメトロ 2 線+銀座線で埋まる=等間隔で残る線 0。"""
    node_lines = {ln for d in w12.NODE_DEFS if d["kind"] == "rail" for ln in d["lines"]}
    covered = {s.line for s in RT.USER_TABLES} | set(w12.METRO_LINES_KEPT_WITH_REAL) | {RT.GINZA_SPEC.line}
    covered |= {RT.FOLD_LINES.get(ln, ln) for ln in list(covered)}
    assert node_lines - covered == set()
    assert w12.USE_REAL_TIMETABLES is True
    # 〔第 2 期 2-3c〕1.3.0=発着の表を足した(時刻表の行は 1.2.0 と同じ=tests/build_rail/test_w12_arrivals_2_3c.py)
    assert w12.STAGE_VERSION == "1.3.0"


def test_world_time_point_matches_the_calendar_default():
    from shibuya.engine.calendar import DEFAULT_WORLD_START

    assert RT.WORLD_TIME_POINT == DEFAULT_WORLD_START.date().isoformat()
    assert RT.VERSION_DECLARATIONS["銀座線"]["relation_to_world_time"] == "after"


def test_w19_input_families_and_asset_paths(tmp_path):
    for fam in RT.INPUT_FAMILIES:
        assert W19.BUILD_INPUT_FAMILIES[fam] == RT.input_rel_paths(fam)
        assert W19.SOURCE_FAMILIES[fam] == fam
    paths = set(W19.data_asset_paths(tmp_path))
    assert set(RT.all_input_rel_paths()) <= paths
    assert "odpt/station_timetable_metro_ginza.json" not in paths  # 銀座線は 9 月改正の列車時刻表から
    assert {"odpt/station_timetable_metro_hanzomon.json", "odpt/station_timetable_metro_fukutoshin.json"} <= paths
    assert "user_timetables/_extracted/JR_注記.final.csv" in paths
    # 封印の層は構築の入力の層と同じ元を持たない(独立の判定は今のまま)
    rows = {r["name"]: r for r in W19.layer_independence()}
    for name in ("kddi_la", "shibuya_jinryu"):
        assert rows[name]["source_family"] not in RT.INPUT_FAMILIES


# ---------------------------------------------------------------------- data の要る試験
needs_data = pytest.mark.requires_data(
    "user_timetables",
    "odpt_static",
    *D.ids_of(
        *(WORLD / n for n in _UPSTREAM),
        DATA_DIR / "odpt",
        DATA_DIR / "realworld" / "transport_census" / "station_flow_12.json",
    ),
)


def _golden() -> dict:
    """記録 ``tt23b/README.md`` の golden(``<!-- golden-begin -->`` と ``<!-- golden-end -->`` の間の JSON)。"""
    text = RECORD.read_text(encoding="utf-8")
    m = re.search(r"<!-- golden-begin -->\s*```json\s*(.*?)```\s*<!-- golden-end -->", text, re.S)
    assert m, "記録に golden の塊が無い"
    return json.loads(m.group(1))


def _run(tmp: Path, use_real: bool, monkeypatch) -> tuple[C.StageResult, dict]:
    tmp.mkdir(parents=True, exist_ok=True)
    for n in _UPSTREAM:
        shutil.copy2(WORLD / n, tmp / n)
    monkeypatch.setattr(w12, "USE_REAL_TIMETABLES", use_real)
    res = w12.run(C.Ctx(data=DATA_DIR, out=tmp))
    return res, C.read_parquet_columns(tmp / "w12_timetables.parquet")


@needs_data
def test_real_run_counts_match_the_record_golden(tmp_path, monkeypatch):
    g = _golden()
    res, tt = _run(tmp_path / "real", True, monkeypatch)
    gates = {x.name: x.to_json() for x in res.gates}
    assert all(v["pass"] for v in gates.values()), {k: v for k, v in gates.items() if not v["pass"]}
    by = Counter(zip(tt["line"], tt["calendar"]))
    got = {ln: {"Weekday": by[(ln, "Weekday")], "SaturdayHoliday": by[(ln, "SaturdayHoliday")]}
           for ln in sorted({x for x in tt["line"]})}
    assert got == g["rows_by_line_calendar"]
    assert len(tt["line"]) == g["rows_total"]
    assert dict(sorted(Counter(tt["source"]).items())) == g["rows_by_source"]
    assert res.notes["real_timetable_table_counts"] == g["table_counts"]
    assert res.notes["temporary_trains_excluded"] == g["temporary_trains_excluded"]
    assert res.notes["dedup_removed"] == g["dedup_removed"]
    # 残る等間隔の線 0・等間隔の行 0・土休 ≦ 平日(第330 §6 の欠陥が消えた)
    assert res.notes["equal_interval_lines_remaining"] == [] and "equal_interval_expedient" not in set(tt["source"])
    assert all(v["SaturdayHoliday"] <= v["Weekday"] for v in got.values())
    # 列と向きの値の集まりはエンジンの読み口と同じ
    assert list(tt) == ["line", "operator", "direction", "calendar", "departure", "departure_min", "source"]
    assert set(tt["direction"]) == {"上り", "下り", "TokyoMetro.Asakusa", "TokyoMetro.Oshiage", "TokyoMetro.Wakoshi"}
    assert all(w12._minute(d) == m for d, m in zip(tt["departure"], tt["departure_min"]))
    # 版の表(資産の隣)
    ver = json.loads((tmp_path / "real" / w12.VERSIONS_FILE).read_text(encoding="utf-8"))
    assert sorted(ver["lines"]) == sorted(got)
    assert ver["lines"]["銀座線"]["relation_to_world_time"] == "after"
    assert ver["lines"]["銀座線"]["odpt_train_timetable"]["dct_issued"] == {"2026-09-19": got["銀座線"]["Weekday"]
                                                                            + got["銀座線"]["SaturdayHoliday"]}
    assert ver["lines"]["埼京線"]["folded_lines"] == ["湘南新宿ライン"]
    assert {i["path"] for i in ver["inputs"]} >= set(RT.all_input_rel_paths())
    assert all(len(i["md5"]) == 32 and i["bytes"] > 0 for i in ver["inputs"])
    # 時刻の一覧は載せない(検収 L3): 語 departure も、ISO の日時(dc:date・取得の時刻)を除いた HH:MM の形も無い
    text = json.dumps(ver, ensure_ascii=False)
    assert "departure" not in text
    assert ISO_DATETIME.search(text), "ISO の日時が 1 つも無い(下の除き方の前提が変わった)"
    assert HHMM.findall(ISO_DATETIME.sub("", text)) == []


#: ISO の日時(``2026-09-24T08:00:00+09:00``・``2026-07-07T15:34:13.850866+00:00`` の形)。
ISO_DATETIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?")
#: 発車の時刻の形(``05:01``・``0:07`` など)。
HHMM = re.compile(r"(?<!\d)\d{1,2}:\d{2}(?!\d)")


def test_hhmm_check_catches_a_planted_time():
    """L3 の検査の負の対照: ISO の日時は除き、紛れ込んだ発車の時刻は見つける。"""
    planted = json.dumps({"date": "2026-09-24T08:00:00+09:00", "x": "13:42"}, ensure_ascii=False)
    assert HHMM.findall(ISO_DATETIME.sub("", planted)) == ["13:42"]
    clean = json.dumps({"date": "2026-07-07T15:34:13.850866+00:00"}, ensure_ascii=False)
    assert HHMM.findall(ISO_DATETIME.sub("", clean)) == []


@needs_data
def test_switch_false_reproduces_the_110_shape_and_nodes_do_not_move(tmp_path, monkeypatch):
    g = _golden()
    res_r, _tt_r = _run(tmp_path / "real", True, monkeypatch)
    res_l, tt_l = _run(tmp_path / "legacy", False, monkeypatch)
    src = Counter(tt_l["source"])
    assert len(tt_l["line"]) == g["legacy_110"]["rows_total"]
    assert src["equal_interval_expedient"] == g["legacy_110"]["equal_interval_rows"]
    assert src["real"] == g["legacy_110"]["real_rows"]
    assert not (tmp_path / "legacy" / w12.VERSIONS_FILE).exists()
    out_r = {o["path"]: o["sha256"] for o in res_r.outputs}
    out_l = {o["path"]: o["sha256"] for o in res_l.outputs}
    for name in ("w12_external_nodes.parquet", "w12_generation_weights.parquet"):
        assert out_r[name] == out_l[name], f"{name} が動いた(方面ノードと重みは 2-3b で変えない)"
    assert out_r["w12_timetables.parquet"] != out_l["w12_timetables.parquet"]


_G01 = tuple(
    DATA_DIR.joinpath(*RT.USER_TIMETABLE_DIR, f"メトロ_銀座線_渋谷_浅草方面_{cal_ja}_final.csv")
    for cal_ja, _cal in RT.CALENDARS
)


@pytest.mark.requires_data("odpt_static", *D.ids_of(*_G01))
def test_ginza_open_static_matches_the_user_pdf_reading():
    """銀座線の ODPT オープン枠(9 月改正)の渋谷発は、ユーザーの G01(9 月改正)の読み取りと時刻の多重集合で一致
    (G01 は構築の入力ではない=照合だけ)。"""
    doc = RT.load_odpt_static(DATA_DIR.joinpath(*RT.ODPT_STATIC_DIR, RT.ODPT_STATIC_METRO_TRAIN_TIMETABLE))
    rows, _check = RT.parse_train_timetable_departures(doc, RT.GINZA_SPEC)
    odpt = Counter((r["calendar"], r["departure"]) for r in rows)
    pdf: Counter = Counter()
    for (cal_ja, cal), p in zip(RT.CALENDARS, _G01):
        for r in RT.read_csv_rows(p):
            pdf[(cal, RT.hhmm(int(r["時"]), int(r["分"])))] += 1
    assert odpt == pdf
