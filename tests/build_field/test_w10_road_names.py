"""段 1c(D-1 (a)): W10 の道路名の突合(``build.field.road_names``)と W10 の切替口。

- 辺 → 最も近い way(辺の弧長の中点から ≤ 8 m=D-W9 のバッファ)→ センサス路線。
- 正規化の規則(区道は対象外・国道/都道の別・ref の番号・名前だけは路線名の完全一致)。
- 区の優先順(渋谷 → 目黒 → 港 → 世田谷 → 新宿 → 都内)。
- 実データ: 写像率・名寄せ成立数・切替口 OFF は改訂前の騒音場とバイト一致。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.field import common as C
from shibuya.build.field import road_names as RN
from shibuya.build.field import w10_noise as W

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
WORLD = DATA_DIR / "world" / "v2"
ROAD_NAMES_P = DATA_DIR.joinpath(*RN.ROAD_NAMES)
KASYO_P = DATA_DIR.joinpath(*W.KASYO)
real = pytest.mark.skipif(
    not (ROAD_NAMES_P.exists() and KASYO_P.exists() and (WORLD / "w1_edges.parquet").exists()),
    reason="data/ absent (CI)",
)


def _sec(kind: str, no: str, name: str, city: str, q12: float = 1000.0) -> dict:
    return {
        "section_id": f"{kind}{no}{city}", "road_kind": kind, "route_no": no, "route_name": name,
        "route_key": C.normalize_jp(name), "city": city, "q12": q12, "q24": q12 * 1.3,
        "heavy_pct": 10.0, "v_kmh": 20.0, "width_m": 10.0, "lanes": 2.0,
    }


# ------------------------------------------------------------------ 正規化の規則
@pytest.mark.parametrize(
    "tags, expected",
    [
        ({"highway": "trunk", "ref": "246", "official_name": "一般国道246号"}, ("national", ("246",))),
        ({"highway": "trunk", "ref": "２４６"}, ("national", ("246",))),               # 全角→半角
        ({"highway": "primary", "name": "国道二十号"}, ("unnumbered", ())),            # 「号」が無い=国道ではない
        ({"highway": "primary", "official_name": "一般国道２０号"}, ("national", ("20",))),
        ({"highway": "primary", "ref": "305", "name": "明治通り"}, ("prefectural", ("305",))),
        ({"highway": "tertiary", "ref": "859;853"}, ("prefectural", ("859", "853"))),
        ({"highway": "tertiary", "ref": "870", "name": "渋谷区特別区道870号線"}, ("ward", ())),
        ({"highway": "residential", "name": "宇田川通り", "official_name": "特別区道第890号路線"}, ("ward", ())),
        ({"highway": "motorway", "ref": "3", "name": "首都高速3号渋谷線"}, ("motorway", ("3",))),
        ({"highway": "tertiary", "name": "井ノ頭通り"}, ("unnumbered", ())),
        ({"highway": "service"}, ("unnamed", ())),
    ],
)
def test_census_key_rules(tags, expected):
    assert RN.census_key(tags) == expected


def test_sections_for_key_uses_the_ward_order_and_road_kind():
    secs = [
        _sec("6", "423", "渋谷経堂線", "13112", 1507.0),   # 世田谷
        _sec("6", "423", "渋谷経堂線", "13110", 6014.0),   # 目黒(世田谷より先)
        _sec("3", "423", "一般国道４２３号", "13113"),      # 国道は都道の検索に混ざらない
        _sec("4", "305", "芝新宿王子線", "13113"),
        _sec("4", "305", "芝新宿王子線", "13104"),
    ]
    got = RN.sections_for_key(secs, "prefectural", ("423",))
    assert [s["city"] for s in got] == ["13110"]
    assert [s["city"] for s in RN.sections_for_key(secs, "prefectural", ("305",))] == ["13113"]
    assert RN.sections_for_key(secs, "national", ("305",)) == []
    assert RN.sections_for_key(secs, "ward", ()) == []
    # 名前だけの道は路線名の完全一致(正規化後)だけ
    assert len(RN.sections_for_key(secs, "unnumbered", (), "芝新宿王子線")) == 1
    assert RN.sections_for_key(secs, "unnumbered", (), "明治通り") == []


# ------------------------------------------------------------------ 幾何
def test_edge_midpoints_are_arc_length_midpoints():
    coords = np.array([[0.0, 0.0], [10.0, 0.0], [10.0, 30.0]])  # 長さ 10+30 → 中点は (10, 10)
    mid = RN.edge_midpoints([0], [3], coords)
    assert mid[0] == pytest.approx([10.0, 10.0])


def _way(i: int, pts: list[tuple[float, float]], **tags) -> dict:
    """ローカル m の点列 → Overpass 形式の way(緯度経度に戻す)。"""
    geom = [
        {"lat": C.ORIGIN_LATLON[0] + y / C.M_PER_DEG_LAT, "lon": C.ORIGIN_LATLON[1] + x / C.M_PER_DEG_LON}
        for x, y in pts
    ]
    return {"type": "way", "id": i, "geometry": geom, "tags": tags}


def test_the_nearest_way_wins_even_if_it_has_no_name():
    """自分の way(名前なし・0 m)の隣を幹線(名前あり・6 m)が走っても、幹線の名前を拾わない。"""
    ways = [
        _way(1, [(0.0, 6.0), (100.0, 6.0)], highway="primary", ref="305", name="明治通り"),
        _way(2, [(0.0, 0.0), (100.0, 0.0)], highway="service"),
    ]
    secs = [_sec("4", "305", "芝新宿王子線", "13113")]
    m = RN.match_edges_to_ways(np.array([[50.0, 0.0], [50.0, 5.0], [50.0, 30.0]]), ways, secs)
    assert m.key_kind == ["unnamed", "prefectural", "no_way"]   # 3 本目は 8 m より遠い
    assert m.route == ["", "4:305:芝新宿王子線", ""]
    assert "4:305:芝新宿王子線" in m.route_sections


def test_match_report_counts_road_edges_only_in_the_totals():
    ways = [_way(1, [(0.0, 0.0), (100.0, 0.0)], highway="primary", ref="305", name="明治通り")]
    secs = [_sec("4", "305", "芝新宿王子線", "13113")]
    m = RN.match_edges_to_ways(np.array([[10.0, 1.0], [20.0, 2.0], [30.0, 50.0]]), ways, secs)
    rep = RN.match_report(m, ["primary", "footway", "residential"], W.ROAD_KLASSES)
    assert rep["road_edges"] == {"edges": 2, "own_way_le_8m": 1, "named": 1, "census_matched": 1}
    assert rep["by_klass"]["footway"]["census_matched"] == 1  # 歩道も写るが音源ではない
    assert rep["road_edges_by_route"] == {"4:305:芝新宿王子線": 1}


# ------------------------------------------------------------------ W10 の切替口
def test_way_band_follows_layer_then_tunnel_and_bridge():
    assert RN.way_band({"layer": "1", "bridge": "yes"}) == "DECK"
    assert RN.way_band({"layer": "-1", "tunnel": "yes"}) == "UG"
    assert RN.way_band({"layer": "3"}) == "DECK"          # |layer|>2 は ±2 に丸める
    assert RN.way_band({"tunnel": "building_passage"}) == "GL"
    assert RN.way_band({"bridge": "yes"}) == "DECK"
    assert RN.way_band({}) == "GL"


def test_q7_restricts_candidates_to_named_ways_of_the_same_class():
    """段 1c′ Q7: 住宅地の辺は隣の幹線(名前つき・6 m)にも、名前の無い自分の way にも写らない。
    primary の辺は名前の無い自分の way ではなく、同じ階級の名前つき way(trunk≒primary)に写る。"""
    ways = [
        _way(1, [(0.0, 6.0), (100.0, 6.0)], highway="trunk", ref="246", official_name="一般国道246号"),
        _way(2, [(0.0, 0.0), (100.0, 0.0)], highway="service"),
    ]
    secs = [_sec("3", "246", "一般国道２４６号", "13113")]
    pts = np.array([[50.0, 0.0], [50.0, 0.0]])
    plain = RN.match_edges_to_ways(pts, ways, secs, edge_klass=["residential", "primary"])
    assert plain.key_kind == ["unnamed", "unnamed"]
    q7 = RN.match_edges_to_ways(
        pts, ways, secs, edge_klass=["residential", "primary"], require_named_same_class=True
    )
    assert q7.key_kind == ["no_way", "national"]
    assert q7.route == ["", "3:246:一般国道２４６号"]


def test_q9_restricts_candidates_to_the_same_band():
    """段 1c′ Q9: 地上(GL)の辺は真上の高架(DECK)の way を拾わず、同じ層の way を拾う。"""
    ways = [
        _way(1, [(0.0, 0.0), (100.0, 0.0)], highway="motorway", ref="3", layer="1", bridge="yes"),
        _way(2, [(0.0, 5.0), (100.0, 5.0)], highway="primary", ref="317", name="山手通り"),
    ]
    secs = [_sec("4", "317", "環状六号線", "13113")]
    pts = np.array([[50.0, 0.5]])
    assert RN.match_edges_to_ways(pts, ways, secs).key_kind == ["motorway"]
    q9 = RN.match_edges_to_ways(pts, ways, secs, edge_band=["GL"], require_same_band=True)
    assert q9.key_kind == ["prefectural"] and q9.route == ["4:317:環状六号線"]


def test_the_filters_need_the_edge_attributes():
    ways = [_way(1, [(0.0, 0.0), (10.0, 0.0)], highway="primary", ref="1")]
    with pytest.raises(ValueError):
        RN.match_edges_to_ways(np.zeros((1, 2)), ways, [], require_named_same_class=True)
    with pytest.raises(ValueError):
        RN.match_edges_to_ways(np.zeros((1, 2)), ways, [], require_same_band=True)


def test_w10_declares_the_switch_and_the_input():
    # 既定 OFF(親決定・段 1c の検収): 対応表は作るが騒音場には当てない
    assert W.USE_ROAD_NAME_MATCH is False
    assert W.ROAD_NAME_REQUIRE_NAMED_SAME_CLASS is False
    assert W.ROAD_NAME_REQUIRE_SAME_BAND is False
    assert W.ROAD_NAMES == ("realworld", "osm", "road_names_overpass_20260928.json")
    assert W.STAGE_VERSION == "1.1.0"
    assert RN.MATCH_BUFFER_M == 8.0


def _w10(tmp_path: Path, name: str):
    out = tmp_path / name
    out.mkdir()
    for f in ("w1_edges.parquet", "w1_edge_geometry.npz"):
        (out / f).write_bytes((WORLD / f).read_bytes())
    return W.run(C.Ctx(data=DATA_DIR, out=out))


@real
def test_w10_road_name_match_on_real_data(tmp_path, monkeypatch):
    """実データ: 写像率・名寄せ・primary/secondary 190/202・残差は突合に依存しない・OFF は当てない。"""
    monkeypatch.setattr(W, "USE_ROAD_NAME_MATCH", True)
    on = _w10(tmp_path, "w10on")
    gates = {g.name: g.to_json() for g in on.gates}
    rep = on.notes["road_name_match"]
    assert rep["road_edges"] == {"edges": 2493, "own_way_le_8m": 2487, "named": 760, "census_matched": 246}
    assert gates["primary_secondary_sections_matched"]["value"] == 190
    assert gates["road_edges_with_census_traffic"]["value"] == 246
    assert rep["road_klass_highway_agreement"] == {"agree": 2298, "with_way": 2487}
    assert set(on.notes["road_name_route_sections"]) == {
        "3:246:一般国道２４６号", "4:305:芝新宿王子線", "4:317:環状六号線", "6:412:霞ヶ関渋谷線",
        "6:413:赤坂杉並線", "6:423:渋谷経堂線", "6:432:淀橋渋谷本町線",
    }
    on_calib = {r["no"]: (r["residual_day_db"], r["residual_night_db"]) for r in on.notes["calibration_rows"]}
    on_out = {o["path"]: o["sha256"] for o in on.outputs}
    assert "w10_edge_section.parquet" in on_out

    # 切替口 OFF(既定)= 対応表は作る(診断)が当てない。騒音場のバイトが違い、較正の残差は同じ。
    monkeypatch.setattr(W, "USE_ROAD_NAME_MATCH", False)
    off = _w10(tmp_path, "w10off")
    off_gates = {g.name: g.to_json() for g in off.gates}
    assert off_gates["primary_secondary_sections_matched"]["value"] == 0
    assert off_gates["road_edges_with_census_traffic"]["value"] == 0
    assert off_gates["primary_secondary_sections_matchable"]["value"] == 190
    assert off_gates["primary_secondary_sections_matchable_q7_q9"]["value"] == 202
    assert off.notes["road_name_match_applied"] is False
    assert off.notes["road_name_match_off_reason"]
    off_out = {o["path"]: o["sha256"] for o in off.outputs}
    assert "w10_edge_section.parquet" in off_out  # 診断として書く
    assert off_out["w10_street_points.parquet"] == on_out["w10_street_points.parquet"]
    assert off_out["w10_noise_day.npy"] != on_out["w10_noise_day.npy"]
    off_calib = {r["no"]: (r["residual_day_db"], r["residual_night_db"]) for r in off.notes["calibration_rows"]}
    assert on_calib == off_calib  # 較正は路線名でセンサスを引く=辺の突合を通らない
    assert on_calib["61"] == (5.1, 4.5) and on_calib["75"] == (7.3, 6.4)


@real
def test_w10_default_off_noise_field_equals_the_pre_1c_asset(tmp_path):
    """既定(OFF)の騒音場 4 本は、段 1c 前の資産(W10 1.0.0 の出力)とバイト一致する。"""
    import pyarrow.parquet as pq

    off = _w10(tmp_path, "w10default")
    assert W.USE_ROAD_NAME_MATCH is False
    out = {o["path"]: o["sha256"] for o in off.outputs}
    # 1.0.0 の出力の sha256(段 1a の build_manifest=第284 の記録)
    assert out["w10_noise_day.npy"].startswith("6f3e3b0f2b4c")
    assert out["w10_noise_night.npy"].startswith("4d682d3ac1eb")
    assert out["w10_noise_stage_day.npy"].startswith("d4d02af1a770")
    assert out["w10_noise_stage_night.npy"].startswith("33ba443230ec")
    assert out["w10_street_points.parquet"].startswith("de1340b15bda")
    t = pq.read_table(tmp_path / "w10default" / "w10_edge_section.parquet").to_pydict()
    assert not any(t["traffic_from_census"]) and sum(t["matchable"]) == 246
    assert sum(1 for r in t["census_route_q7_q9"] if r) >= 225


@real
def test_w10_refined_q7_q9_on_real_data(tmp_path, monkeypatch):
    """段 1c′: Q7+Q9 の絞り込みで当てうる辺 246 → 225・primary+secondary 190 → 202。"""
    monkeypatch.setattr(W, "USE_ROAD_NAME_MATCH", True)
    monkeypatch.setattr(W, "ROAD_NAME_REQUIRE_NAMED_SAME_CLASS", True)
    monkeypatch.setattr(W, "ROAD_NAME_REQUIRE_SAME_BAND", True)
    ref = _w10(tmp_path, "w10ref")
    gates = {g.name: g.to_json() for g in ref.gates}
    assert gates["road_edges_with_census_traffic"]["value"] == 225
    assert gates["primary_secondary_sections_matched"]["value"] == 202
    assert gates["primary_secondary_sections_matched"]["pass"] is True
    rows = {r["no"]: (r["residual_day_db"], r["residual_night_db"]) for r in ref.notes["calibration_rows"]}
    assert rows["61"] == (5.1, 4.5) and rows["75"] == (7.3, 6.4)  # 較正は動かない
