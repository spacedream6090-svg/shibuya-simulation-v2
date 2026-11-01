"""W12 1.3.0 の渋谷の発着の表(第 2 期 2-3c・``build/field/w12_rail_events.py``)。

data の要らない試験(CI で走る): 合成の表 → 到着の行・直通のまとめ=1 本(東急の上り=地下鉄の行と同じ列車・下りの直通の
結び・当駅始発の印・成田エクスプレス ⊂ 湘南新宿ライン・相鉄線直通)・まとめない組の負の対照(行き先の違い・印が無い・
上限の外)・版の表と列の名・規則の conf と宣言の表・入力の層・エンジンの読む口の器(既定は読まない)。

data の要る試験(``requires_data``): W12 を一時の置き場で組み、時刻表が 1.2.0(本体の v2)とバイト一致・発着の表の本数が
記録 ``tt23c/README.md`` の golden と一致・ゲートが全部 PASS・版の表に時刻が無い/読み取りの検査(読み 1/2・時ごとのマス)/
地下鉄の到着の手前の駅の発車がユーザーの表の読み取りと一致/当駅始発の印がチャレンジ枠の isOrigin と一致(照合だけ)。
時刻そのものは比べない(記録に写さないので golden にも無い)。
"""

from __future__ import annotations

import csv
import gzip
import hashlib
import json
import re
import shutil
from collections import Counter
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.audit import w19_freeze as W19
from shibuya.build.field import common as C
from shibuya.build.field import w12_external_nodes as w12
from shibuya.build.field import w12_rail_events as RE
from shibuya.build.field import w12_real_timetables as RT
from shibuya.engine.processes import rail_events as ERE
from tests import _data_ids as D

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
WORLD = DATA_DIR / "world" / "v2"
RECORD = REPO_ROOT / "docs" / "bench" / "analysis" / "wallbounce-1012" / "tt23c" / "README.md"
_UPSTREAM = ("w11_station_exits.parquet", "w1_nodes.parquet", "w1_edges.parquet")
_HEADER = "会社,路線,駅,方面,平日土休,時,分,種別,行き先,版,md5,読み"
_KEIO_HEADER = _HEADER + ",直前の停車駅,直前の停車駅の発車時刻,列車番号,始発駅"
_SH = "odpt.Station:TokyoMetro.Fukutoshin.Shibuya"


# ---------------------------------------------------------------------- 合成の data 根
def _csv(path: Path, header: str, rows: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("﻿" + header + "\n" + "".join(r + "\n" for r in rows), encoding="utf-8")


def _spec(stem: str) -> RT.TableSpec:
    return next(s for s in RT.USER_TABLES if s.stem == stem)


_STEMS = ("東急_副都心線_渋谷_和光市方面", "東急_東横線_渋谷_横浜方面", RT.SOTETSU_TABLE, RT.OSAKI_TABLE,
          "JR_湘南新宿ライン_渋谷_南行")


def _train(sid: str, cal: str, objs: list[dict], dest: str, ttype: str, direction: str, origin: str) -> dict:
    return {"odpt:railway": "odpt.Railway:TokyoMetro.Fukutoshin", "odpt:calendar": f"odpt.Calendar:{cal}",
            "owl:sameAs": f"odpt.TrainTimetable:TokyoMetro.Fukutoshin.{sid}.{cal}", "dct:issued": "2026-03-14",
            "odpt:destinationStation": [dest], "odpt:originStation": [origin],
            "odpt:trainType": f"odpt.TrainType:TokyoMetro.{ttype}",
            "odpt:railDirection": f"odpt.RailDirection:{direction}", "odpt:trainTimetableObject": objs}


def _root(tmp: Path, *, up_dest: str = "和光市", mark: bool = True, b_arrival: str = "08:20",
          sotetsu_minute: int = 5, nex_minute: int = 9, extra_mark: bool = False) -> Path:
    """合成の data 根(5 表+京王の到着+成田エクスプレス+印+ODPT の列車時刻表)。

    負の対照の口: ``sotetsu_minute=7``=相鉄線直通の便を大崎方面の便と同じ分に植える(表の生の行では 2 便・発車の表では
    1 行)/``nex_minute``=成田エクスプレスの便を湘南新宿ラインの表に無い分に/``extra_mark``=発車の行の無い分に印。"""
    ext = tmp.joinpath(*RT.USER_TIMETABLE_DIR)
    tables = {
        "東急_副都心線_渋谷_和光市方面": [f"東急,副都心線,渋谷,x,平日,8,10,各停,{up_dest},v,m,1=2"],
        "東急_東横線_渋谷_横浜方面": ["東急,東横線,渋谷,x,平日,8,22,急行,元町・中華街,v,m,1=2",
                                    "東急,東横線,渋谷,x,平日,8,30,各停,元町・中華街,v,m,1=2"],
        RT.SOTETSU_TABLE: [f"JR東日本,相鉄線直通,渋谷,x,平日,8,{sotetsu_minute},普通,海老名,v,m,1=2"],
        RT.OSAKI_TABLE: ["JR東日本,埼京線・川越線,渋谷,x,平日,8,7,普通,新木場,v,m,1=2"],
        "JR_湘南新宿ライン_渋谷_南行": ["JR東日本,湘南新宿ライン,渋谷,x,平日,8,9,特急(成田エクスプレス),成田空港,v,m,1=2"],
    }
    for stem, rows in tables.items():
        _csv(ext / f"{stem}_平日_final.csv", _HEADER, rows)
        _csv(ext / f"{stem}_土休_final.csv", _HEADER, [])
    for stem, _into in RT.NEX_TABLES:
        rows = ([f"JR東日本,成田エクスプレス,渋谷,x,平日,8,{nex_minute},特急(成田エクスプレス),成田空港,v,m,1=2"]
                if stem.endswith("成田空港方面") else [])
        _csv(ext / f"{stem}_平日_final.csv", _HEADER, rows)
        _csv(ext / f"{stem}_土休_final.csv", _HEADER, [])
    _csv(ext / RT.TOKYU_MARKS_FILE, "表,平日土休,時,分,印,md5,読み",
         (["東急_東横線_渋谷_横浜方面,平日,8,30,●,m,1=2"] if mark else [])
         + (["東急_東横線_渋谷_横浜方面,平日,8,45,●,m,1=2"] if extra_mark else []))
    ch = tmp.joinpath(*RT.ODPT_CHALLENGE_DIR)
    _csv(ch / f"{RT.KEIO_ARRIVAL_STEM}_平日_odpt.csv", _KEIO_HEADER,
         ["京王,井の頭線,渋谷,到着(吉祥寺方面から),平日,8,15,各停,渋谷,v,m,odpt,神泉,x,101,吉祥寺"])
    _csv(ch / f"{RT.KEIO_ARRIVAL_STEM}_土休_odpt.csv", _KEIO_HEADER, [])
    hh, mm = b_arrival.split(":")
    trains = [
        _train("A1", "Weekday", [{"odpt:departureStation": _SH, "odpt:departureTime": "08:10"},
                                 {"odpt:departureStation": "odpt.Station:TokyoMetro.Fukutoshin.MeijiJingumae",
                                  "odpt:departureTime": "08:12"}],
               "odpt.Station:TokyoMetro.Fukutoshin.Wakoshi", "Local", "TokyoMetro.Wakoshi",
               "odpt.Station:Tokyu.Toyoko.Yokohama"),
        _train("B1", "Weekday", [{"odpt:departureStation": "odpt.Station:TokyoMetro.Fukutoshin.MeijiJingumae",
                                  "odpt:departureTime": "08:18"},
                                 {"odpt:arrivalStation": _SH, "odpt:arrivalTime": f"{hh}:{mm}"}],
               "odpt.Station:Minatomirai.Minatomirai.MotomachiChukagai", "Express", "TokyoMetro.Shibuya",
               "odpt.Station:Seibu.Ikebukuro.Kotesashi"),
        _train("C1", "Weekday", [{"odpt:departureStation": "odpt.Station:TokyoMetro.Fukutoshin.MeijiJingumae",
                                  "odpt:departureTime": "08:58"},
                                 {"odpt:arrivalStation": _SH, "odpt:arrivalTime": "09:00"}],
               _SH, "Local", "TokyoMetro.Shibuya", "odpt.Station:TokyoMetro.Fukutoshin.Wakoshi"),
        # 渋谷を発着しない列車(知らない駅でも読まない)
        _train("Z1", "Weekday", [{"odpt:departureStation": "odpt.Station:TokyoMetro.Fukutoshin.Ikebukuro",
                                  "odpt:departureTime": "08:00"}],
               "odpt.Station:Nowhere.Line.Unknown", "Local", "TokyoMetro.Wakoshi", "x"),
    ]
    st = tmp.joinpath(*RT.ODPT_STATIC_DIR)
    st.mkdir(parents=True, exist_ok=True)
    with gzip.open(st / RT.ODPT_STATIC_METRO_TRAIN_TIMETABLE, "wt", encoding="utf-8") as fh:
        json.dump({"data": trains}, fh, ensure_ascii=False)
    return tmp


def _station_doc(train: str = "A1", is_origin: bool = False) -> dict:
    obj = {"odpt:departureTime": "08:10",
           "odpt:destinationStation": ["odpt.Station:TokyoMetro.Fukutoshin.Wakoshi"],
           "odpt:train": f"odpt.Train:TokyoMetro.Fukutoshin.{train}",
           "odpt:trainType": "odpt.TrainType:TokyoMetro.Local"}
    if is_origin:
        obj["odpt:isOrigin"] = True
    return {"data": [{"odpt:calendar": "odpt.Calendar:Weekday",
                      "odpt:railDirection": "odpt.RailDirection:TokyoMetro.Wakoshi",
                      "odpt:stationTimetableObject": [obj]}]}


def _departures(*, without_sotetsu_row: bool = False) -> dict:
    rows = [("副都心線", "東京メトロ", "TokyoMetro.Wakoshi", "08:10", "real"),
            ("東横線", "東急電鉄", "上り", "08:10", RT.SRC_TOKYU),
            ("東横線", "東急電鉄", "下り", "08:22", RT.SRC_TOKYU),
            ("東横線", "東急電鉄", "下り", "08:30", RT.SRC_TOKYU),
            ("埼京線", "JR東日本", "上り", "08:05", RT.SRC_JR),
            ("埼京線", "JR東日本", "上り", "08:07", RT.SRC_JR),
            ("埼京線", "JR東日本", "上り", "08:09", RT.SRC_JR)]
    if without_sotetsu_row:  # 2-3b の重複の除去の後=同じ分の 2 便は発車の表で 1 行
        rows = [r for r in rows if r[3] != "08:05"]
    return {"line": [r[0] for r in rows], "operator": [r[1] for r in rows], "direction": [r[2] for r in rows],
            "calendar": ["Weekday"] * len(rows), "departure": [r[3] for r in rows],
            "departure_min": np.array([w12._minute(r[3]) for r in rows], dtype=np.int32),
            "source": [r[4] for r in rows]}


@pytest.fixture
def synth(monkeypatch):
    monkeypatch.setattr(RT, "USER_TABLES", tuple(_spec(s) for s in _STEMS))
    monkeypatch.setattr(RT, "USE_ODPT_CHALLENGE", True)
    return monkeypatch


def _build(tmp_path, *, station: dict | None = None, without_sotetsu_row: bool = False, **kw) -> RE.RailEvents:
    root = _root(tmp_path, **kw)
    return RE.build_rail_events(root, _departures(without_sotetsu_row=without_sotetsu_row),
                                {"副都心線": station or _station_doc()})


def _rows(ev: RE.RailEvents) -> list[dict]:
    cols = ev.columns
    return [{c: (cols[c][i].item() if hasattr(cols[c][i], "item") else cols[c][i]) for c in RE.COLUMNS}
            for i in range(len(cols["event"]))]


# ---------------------------------------------------------------------- data 不要
def test_synthetic_arrivals_and_through_merge(tmp_path, synth):
    ev = _build(tmp_path)
    rows = _rows(ev)
    dep = [r for r in rows if r["event"] == RE.EVENT_DEPARTURE]
    arr = [r for r in rows if r["event"] == RE.EVENT_ARRIVAL]
    assert [r["departure_row"] for r in dep] == list(range(7))
    assert len(arr) == 3 and all(r["departure_row"] == -1 for r in arr)
    a_id = "odpt.TrainTimetable:TokyoMetro.Fukutoshin.A1.Weekday"
    b_id = "odpt.TrainTimetable:TokyoMetro.Fukutoshin.B1.Weekday"
    # up_merge: 東急の上り(行 1)は地下鉄の行(行 0)と同じ列車=数えるのは 1 回
    assert (dep[0]["call_kind"], dep[0]["through_partner_line"], dep[0]["counted"], dep[0]["train_key"]) == (
        RE.KIND_THROUGH, "東横線", True, a_id)
    assert (dep[1]["merged_into_row"], dep[1]["counted"], dep[1]["train_key"], dep[1]["through_partner_line"],
            dep[1]["train_id"]) == (0, False, a_id, "副都心線", "")
    # down_through: 地下鉄の渋谷着 B1 ↔ 東急の下り 08:22(印の無い便)・08:30 は当駅始発(●)
    assert (dep[2]["call_kind"], dep[2]["through_partner_line"], dep[2]["train_key"]) == (RE.KIND_THROUGH, "副都心線", b_id)
    assert dep[3]["call_kind"] == RE.KIND_ORIGIN and dep[3]["train_key"] == ""
    b = next(r for r in arr if r["train_id"] == b_id)
    assert (b["call_kind"], b["through_partner_line"], b["direction"], b["source"]) == (
        RE.KIND_THROUGH, "東横線", "TokyoMetro.Shibuya", RE.SRC_METRO_ARRIVAL_0314)
    c = next(r for r in arr if r["train_id"].endswith("C1.Weekday"))
    assert (c["call_kind"], c["through_partner_line"], c["destination"]) == (RE.KIND_TERMINAL, "", "渋谷")
    k = next(r for r in arr if r["line"] == "井の頭線")
    assert (k["call_kind"], k["direction"], k["train_id"], k["source"]) == (RE.KIND_TERMINAL, "上り", "keio:101", RT.SRC_KEIO)
    # 相鉄線直通の表の便=相手の線「相鉄線」・JR の発車は call_kind unknown
    assert dep[4]["through_partner_line"] == "相鉄線" and dep[4]["call_kind"] == RE.KIND_UNKNOWN
    assert dep[5]["through_partner_line"] == "" and dep[6]["call_kind"] == RE.KIND_UNKNOWN
    s = ev.summary
    assert s["nex_in_shonan"] == {"merged": 1, "unmatched": 0}
    assert s["sotetsu"] == {"rows_with_partner": 1, "overlap_with_osaki_table": 0, "raw_rows": 1}
    assert s["down_through"]["dwell_min_hist"] == {"2": 1} and s["down_through"]["origin_marks_on_rows"] == 1
    assert s["attr_collapsed"] == 0 and s["sotetsu"]["raw_rows"] == 1
    assert s["metro_dep_join"] == {"static_join_missing": 0, "origin_flag_mismatch_station_vs_train_timetable": 0}
    assert RE.suspicious_total(s) == 0
    assert ev.columns["time_min"].dtype == np.int32 and ev.columns["counted"].dtype == bool
    assert list(ev.columns) == list(RE.COLUMNS)


def test_negative_controls_leave_suspicious_pairs(tmp_path, synth):
    """まとめない組: 上りの行き先が違う/当駅始発の印が無い/発車−到着が上限の外 → 疑わしい組が残る(黙って結ばない)。"""
    ev = _build(tmp_path / "a", up_dest="池袋")
    rows = _rows(ev)
    assert rows[1]["counted"] is True and rows[1]["merged_into_row"] == -1
    assert ev.summary["up_merge"]["unmatched_tokyu_rows"] == {"東横線|Weekday": 1}
    assert RE.suspicious_total(ev.summary) == 2  # 結べない東急の行 1+相手の無い地下鉄の行 1
    ev = _build(tmp_path / "b", mark=False)
    assert ev.summary["down_through"]["unpaired"] == 1 and RE.suspicious_total(ev.summary) == 1
    assert all(r["call_kind"] != RE.KIND_THROUGH for r in _rows(ev)[2:4])  # 数が合わない組は結ばない
    ev = _build(tmp_path / "c", b_arrival="08:00")
    assert ev.summary["down_through"]["out_of_window"] == 1 and RE.suspicious_total(ev.summary) == 1


def test_same_minute_two_trains_are_counted_on_the_raw_rows(tmp_path, synth):
    """〔検収 M1〕相鉄線直通の便と大崎方面の便が同じ分=表の生の行では 2 便・発車の表では 1 行(2-3b の重複の除去)。
    発車の行で数えると作りの上で 0 しか出ないので、重なりは生の行で数え、潰れた属性もゲートに入れる。"""
    ev = _build(tmp_path, sotetsu_minute=7, without_sotetsu_row=True)
    s = ev.summary
    assert sum(1 for e in ev.columns["event"] if e == RE.EVENT_DEPARTURE) == 6
    assert s["sotetsu"]["overlap_with_osaki_table"] == 1 and s["sotetsu"]["raw_rows"] == 1
    assert s["attr_collapsed"] == 1
    assert RE.suspicious_total(s) == 2  # 重なり 1+潰れた属性 1


@pytest.mark.parametrize("kw,key,want", [
    (dict(nex_minute=11), "nex_unmatched", 1),
    (dict(station=_station_doc(train="A9")), "static_join_missing", 1),
    (dict(extra_mark=True), "marks_not_on_rows", 1),
    (dict(station=_station_doc(is_origin=True)), "origin_flag_mismatch", 1),
])
def test_each_gate_component_has_a_negative_control(tmp_path, synth, kw, key, want):
    """〔検収 L1・L2〕ゲート ``rail_events_suspicious_pairs`` の残りの成分 1 つずつ: 成田エクスプレスの外れ・列車時刻表との
    結び損ね・印の分が発車の行に無い・始発の印の食い違い(駅の時刻表 vs 列車時刻表)。"""
    s = _build(tmp_path, **kw).summary
    got = {
        "nex_unmatched": s["nex_in_shonan"]["unmatched"],
        "static_join_missing": s["metro_dep_join"]["static_join_missing"],
        "marks_not_on_rows": s["down_through"]["origin_marks"] - s["down_through"]["origin_marks_on_rows"],
        "origin_flag_mismatch": s["metro_dep_join"]["origin_flag_mismatch_station_vs_train_timetable"],
    }
    assert got[key] == want
    assert {k: v for k, v in got.items() if k != key} == {k: 0 for k in got if k != key}
    assert RE.suspicious_total(s) == want


def test_unknown_station_or_type_stops():
    with pytest.raises(ValueError):
        RE.station_name("odpt.Station:Nowhere.Line.Unknown")
    with pytest.raises(ValueError):
        RE.type_name("odpt.TrainType:TokyoMetro.Rapid")
    assert RE.station_name("odpt.Station:Minatomirai.Minatomirai.MotomachiChukagai") == "元町・中華街"
    assert RE.TYPE_KEY == {"Fライナー": "急行"}


def test_version_table_names_rules_and_declarations():
    assert w12.STAGE_VERSION == "1.3.0"
    assert RE.EVENTS_FILE == ERE.RAIL_EVENTS_FILE
    assert set(ERE._COLUMNS) <= set(RE.COLUMNS)
    assert RE.COLUMNS == ("event", "call_kind", "line", "operator", "direction", "calendar", "time", "time_min",
                          "source", "train_id", "train_key", "train_type", "destination", "through_partner_line",
                          "departure_row", "merged_into_row", "counted")
    assert set(RE.RULE_CONF) == set(RE.THROUGH_RULES)
    assert set(RE.RULE_CONF.values()) <= {"mechanism", "expedient"}
    # expedient の規則は W12 の宣言の表に 1 行ずつ(台帳 EX-build.field.w12_external_nodes-*)
    assert sum(v == "expedient" for v in RE.RULE_CONF.values()) == len(w12.RAIL_EVENT_EXPEDIENTS) == 1
    assert w12.RAIL_EVENT_EXPEDIENTS[0].startswith("下りの直通の結び(2-3c)")
    assert ERE.READ_RAIL_EVENTS is False


def test_inputs_follow_the_challenge_switch(tmp_path, monkeypatch):
    user = RT.input_rel_paths(RT.FAMILY_USER)
    assert "user_timetables/_extracted/東急_印.final.csv" in user
    assert sum("成田エクスプレス" in p for p in user) == 4
    ch = RT.input_rel_paths(RT.FAMILY_CHALLENGE)
    keio_arr = [p for p in ch if RT.KEIO_ARRIVAL_STEM in p]
    assert len(keio_arr) == 2
    assert set(RT.all_input_rel_paths()) <= set(W19.data_asset_paths(tmp_path))
    monkeypatch.setattr(RT, "USE_ODPT_CHALLENGE", False)
    assert RT.input_rel_paths(RT.FAMILY_CHALLENGE) == ()
    assert set(keio_arr) <= set(RT.input_rel_paths(RT.FAMILY_CHALLENGE, in_use=False))
    assert RE.keio_arrivals(tmp_path) == []  # 切替口 False は京王の到着を読まない(ファイルが無くても止まらない)


def test_engine_reader_is_off_by_default(tmp_path):
    cols = {"event": ["departure", "arrival"], "call_kind": ["origin", "terminal"], "line": ["銀座線", "銀座線"],
            "calendar": ["Weekday", "SaturdayHoliday"], "time_min": np.array([1450, 600], dtype=np.int32),
            "departure_row": np.array([0, -1], dtype=np.int32), "merged_into_row": np.array([-1, -1], dtype=np.int32),
            "counted": np.array([True, True])}
    C.write_parquet(tmp_path, ERE.RAIL_EVENTS_FILE, cols)
    assert ERE.load_rail_events(tmp_path) is None  # 既定は読まない
    got = ERE.load_rail_events(tmp_path, enabled=True)
    assert got is not None and got.n == 2 and got.lines == ("銀座線",)
    assert got.minute_of_day.tolist() == [10, 600] and got.calendar.tolist() == [0, 1]
    assert got.arrivals().tolist() == [1]
    for name in ("event", "call_kind", "line_idx", "calendar", "minute_of_day", "departure_row", "merged_into_row",
                 "counted"):
        with pytest.raises(ValueError):  # 〔検収 L3〕読み取り専用
            getattr(got, name)[0] = 0
    assert ERE.load_rail_events(tmp_path / "none", enabled=True) is None
    bad = dict(cols, event=["departure", "pass"])
    C.write_parquet(tmp_path, ERE.RAIL_EVENTS_FILE, bad)
    with pytest.raises(ValueError):
        ERE.load_rail_events(tmp_path, enabled=True)


def test_engine_reader_is_not_called_from_any_process():
    """〔検収 L3〕読む口の器はどの過程・系からも呼ばれない(既定は読まない=結果不変の静的な番人)。"""
    import ast

    assert ERE.READ_RAIL_EVENTS is False
    src = REPO_ROOT / "src" / "shibuya"
    me = (src / "engine" / "processes" / "rail_events.py").resolve()
    hits = []
    for p in sorted(src.rglob("*.py")):
        if p.resolve() == me:
            continue
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module and n.module.endswith("rail_events")                     and "build" not in n.module:
                hits.append((p.name, n.lineno))
            elif isinstance(n, ast.ImportFrom) and any(a.name == "rail_events" for a in n.names)                     and "build" not in (n.module or ""):
                hits.append((p.name, n.lineno))
            elif isinstance(n, ast.Import) and any(a.name.endswith("processes.rail_events") for a in n.names):
                hits.append((p.name, n.lineno))
            elif isinstance(n, (ast.Name, ast.Attribute)) and getattr(n, "id", getattr(n, "attr", "")) in (
                    "load_rail_events", "READ_RAIL_EVENTS", "RailEventsAsset"):
                hits.append((p.name, n.lineno))
    assert hits == [], hits
    # engine/processes と engine/systems は名指しで確かめる(上の走査に含まれる)
    assert (src / "engine" / "processes").is_dir() and (src / "engine" / "systems").is_dir()


# ---------------------------------------------------------------------- data の要る試験
needs_data = pytest.mark.requires_data(
    "user_timetables",
    "odpt_static",
    *D.ids_of(
        *(WORLD / n for n in _UPSTREAM),
        WORLD / "w12_timetables.parquet",
        DATA_DIR / "odpt",
        DATA_DIR / "realworld" / "transport_census" / "station_flow_12.json",
    ),
)


def _golden() -> dict:
    text = RECORD.read_text(encoding="utf-8")
    m = re.search(r"<!-- golden-begin -->\s*```json\s*(.*?)```\s*<!-- golden-end -->", text, re.S)
    assert m, "記録に golden の塊が無い"
    return json.loads(m.group(1))


ISO_DATETIME = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}(?::\d{2}(?:\.\d+)?)?(?:Z|[+-]\d{2}:\d{2})?")
HHMM = re.compile(r"(?<!\d)\d{1,2}:\d{2}(?!\d)")


@needs_data
def test_real_run_matches_the_record_golden(tmp_path):
    g = _golden()
    out = tmp_path / "w12"
    out.mkdir()
    for n in _UPSTREAM:
        shutil.copy2(WORLD / n, out / n)
    res = w12.run(C.Ctx(data=DATA_DIR, out=out))
    gates = {x.name: x.to_json() for x in res.gates}
    assert all(v["pass"] for v in gates.values()), {k: v for k, v in gates.items() if not v["pass"]}
    # 発車の表は 1.2.0(本体の v2=2-4 で活性化した版)とバイト一致=エンジンの結果は変わらない
    sha = hashlib.sha256((out / "w12_timetables.parquet").read_bytes()).hexdigest()
    assert sha == hashlib.sha256((WORLD / "w12_timetables.parquet").read_bytes()).hexdigest()
    assert sha[:16] == g["timetables_sha256_16"]
    ev = res.notes["rail_events"]
    assert ev["rows"] == g["rows_total"] and ev["rows_by_event"] == g["rows_by_event"]
    assert ev["by_line_calendar"] == g["by_line_calendar"]
    assert ev["arrivals_by_source"] == g["arrivals_by_source"] and ev["arrival_versions"] == g["arrival_versions"]
    assert ev["up_merge"]["merged"] == g["up_merge_merged"]
    assert ev["down_through"]["paired"] == g["down_through_paired"]
    assert ev["down_through"]["dwell_min_hist"] == g["down_through_dwell_min_hist"]
    assert ev["down_through"]["type_pairs"] == g["down_through_type_pairs"]
    assert ev["down_through"]["swappable_adjacent_pairs"] == g["swappable_adjacent_pairs"]
    assert ev["down_through"]["origin_marks"] == g["origin_marks"]
    assert ev["nex_in_shonan"]["merged"] == g["nex_in_shonan_merged"]
    assert ev["sotetsu"]["rows_with_partner"] == g["sotetsu_rows_with_partner"]
    assert RE.suspicious_total(ev) == 0
    tab = C.read_parquet_columns(out / RE.EVENTS_FILE)
    assert list(tab) == list(RE.COLUMNS)
    dep = [i for i, e in enumerate(tab["event"]) if e == RE.EVENT_DEPARTURE]
    assert [tab["departure_row"][i] for i in dep] == list(range(len(dep)))
    # 発車の行の時刻は発車の表と同じ
    tt = C.read_parquet_columns(out / "w12_timetables.parquet")
    assert [tab["time"][i] for i in dep] == list(tt["departure"])
    # 版の表に rail_events の節(規則は conf つき)・時刻は無い(語 departure も無い=2-3b の検収 L3)
    ver = json.loads((out / w12.VERSIONS_FILE).read_text(encoding="utf-8"))
    rules = {r["id"]: r["conf"] for r in ver["rail_events"]["rules"]}
    assert rules == RE.RULE_CONF
    text = json.dumps(ver, ensure_ascii=False)
    assert "departure" not in text
    assert HHMM.findall(ISO_DATETIME.sub("", text)) == []
    assert set(w12.RAIL_EVENT_EXPEDIENTS) <= set(res.expedients)


def _read(p: Path) -> list[dict]:
    with open(p, encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


#: 2-3c が使うユーザー提供の表(読み 1/2 の CSV があるもの)。成田エクスプレス(まとめの確かめ)と手前の駅の 3 表(照合)。
_READ_TABLES = tuple(f"{stem}_{cal}" for stem, _ in RT.NEX_TABLES for cal in ("平日", "土休")) + tuple(
    f"{stem}_{cal}" for stem in ("メトロ_銀座線_表参道_渋谷ゆき", "メトロ_半蔵門線_表参道_渋谷方面",
                                 "メトロ_副都心線_明治神宮前_渋谷方面") for cal in ("平日", "土休"))
_EXT = DATA_DIR.joinpath(*RT.USER_TIMETABLE_DIR)


@pytest.mark.requires_data(*D.ids_of(*(_EXT / f"{t}_read1.csv" for t in _READ_TABLES),
                                     _EXT / "東急_印.read1.csv", _EXT / "東急_印.read2.csv",
                                     _EXT / "read2_raw" / "tokyu_origin_marks_resolutions.json"))
def test_readings_agree_read1_read2_and_hour_cells():
    """読み取りの検査(2-3b と同じ形): 読み 1 と読み 2 が (時, 分) と種別・行き先で一致・時ごとの本数が一致。
    当駅始発の印の表は 1 件の食い違いを決着の表で読み 1 に決めた(読み 2 の見落とし・300 dpi で確かめた)。"""
    for t in _READ_TABLES:
        r1, r2 = _read(_EXT / f"{t}_read1.csv"), _read(_EXT / f"{t}_read2.csv")
        k = lambda r: (int(r["時"]), int(r["分"]), r["種別"], r["行き先"])  # noqa: E731
        assert Counter(map(k, r1)) == Counter(map(k, r2)), t
        assert Counter(int(r["時"]) for r in r1) == Counter(int(r["時"]) for r in r2), t
    m1, m2 = _read(_EXT / "東急_印.read1.csv"), _read(_EXT / "東急_印.read2.csv")
    km = lambda r: (r["表"], r["平日土休"], int(r["時"]), int(r["分"]), r["印"])  # noqa: E731
    res = json.loads((_EXT / "read2_raw" / "tokyu_origin_marks_resolutions.json").read_text(encoding="utf-8"))
    resolved = {(x["表"], x["平日土休"], int(x["時"]), int(x["分"])) for x in res}
    diff = (Counter(map(km, m1)) - Counter(map(km, m2))) + (Counter(map(km, m2)) - Counter(map(km, m1)))
    assert {d[:4] for d in diff} == resolved and len(resolved) == 1
    hours = lambda rr: Counter((r["表"], r["平日土休"], int(r["時"])) for r in rr)  # noqa: E731
    cells = set(hours(m1)) | set(hours(m2))
    mism = [c for c in cells if hours(m1)[c] != hours(m2)[c]]
    assert len(mism) == 1  # 決着した 1 件の時のマスだけ
    final = _read(_EXT / RT.TOKYU_MARKS_FILE)
    assert Counter(map(km, final)) == Counter(map(km, m1))


_UPSTREAM_USER = {"銀座線": ("メトロ_銀座線_表参道_渋谷ゆき", "odpt.Station:TokyoMetro.Ginza.OmoteSando"),
                  "半蔵門線": ("メトロ_半蔵門線_表参道_渋谷方面", "odpt.Station:TokyoMetro.Hanzomon.OmoteSando"),
                  "副都心線": ("メトロ_副都心線_明治神宮前_渋谷方面", "odpt.Station:TokyoMetro.Fukutoshin.MeijiJingumae")}


@pytest.mark.requires_data("odpt_static", *D.ids_of(*(_EXT / f"{v[0]}_{c}_final.csv" for v in _UPSTREAM_USER.values()
                                                       for c in ("平日", "土休"))))
def test_metro_arrivals_upstream_departures_match_the_user_tables():
    """地下鉄の渋谷着の列車の手前の駅(表参道・明治神宮前)の発車は、ユーザーの表の読み取りと時刻の多重集合で一致
    (副都心線の S-TRAIN 2 本=明治神宮前に停まらない便は除く)。ユーザーの表は照合だけ(構築の入力ではない)。"""
    doc = RT.load_odpt_static(DATA_DIR.joinpath(*RT.ODPT_STATIC_DIR, RT.ODPT_STATIC_METRO_TRAIN_TIMETABLE))
    _deps, arrs = RE.metro_trains(doc)
    by_id = {t["owl:sameAs"]: t for t in doc["data"]}
    for line, (stem, up) in _UPSTREAM_USER.items():
        odpt: Counter = Counter()
        no_stop = 0
        for a in arrs:
            if a["line"] != line:
                continue
            hit = [o for o in by_id[a["train_id"]]["odpt:trainTimetableObject"] if o.get("odpt:departureStation") == up]
            if not hit:
                no_stop += 1
                continue
            odpt[(a["calendar"], hit[0]["odpt:departureTime"])] += 1
        user: Counter = Counter()
        for cal_ja, cal in RT.CALENDARS:
            for r in _read(_EXT / f"{stem}_{cal_ja}_final.csv"):
                user[(cal, RT.hhmm(int(r["時"]), int(r["分"])))] += 1
        assert odpt == user, line
        assert no_stop == (2 if line == "副都心線" else 0), line


_CH = DATA_DIR / "odpt" / "challenge"


@pytest.mark.requires_data(*D.ids_of(_EXT / RT.TOKYU_MARKS_FILE, _CH / "station_timetable_tokyu_toyoko_shibuya.json",
                                     _CH / "station_timetable_tokyu_denentoshi_shibuya.json"))
def test_origin_marks_match_the_challenge_isorigin():
    """当駅始発の印(ユーザーの PDF の読み取り)=チャレンジ枠の東急 渋谷の駅の時刻表の isOrigin(照合だけ)。"""
    marks = Counter((r["表"], RT.CALENDAR_OF[r["平日土休"]], RT.hhmm(int(r["時"]), int(r["分"])))
                    for r in _read(_EXT / RT.TOKYU_MARKS_FILE))
    orig: Counter = Counter()
    for stem, f in (("東急_東横線_渋谷_横浜方面", "station_timetable_tokyu_toyoko_shibuya.json"),
                    ("東急_田園都市線_渋谷_中央林間方面", "station_timetable_tokyu_denentoshi_shibuya.json")):
        for t in json.loads((_CH / f).read_text(encoding="utf-8"))["data"]:
            cal = str(t["odpt:calendar"]).split(":")[-1]
            for o in t["odpt:stationTimetableObject"]:
                if o.get("odpt:isOrigin"):
                    orig[(stem, cal, str(o["odpt:departureTime"]))] += 1
    assert marks == orig and sum(marks.values()) == 185
