"""W10 の物差し(W10 の Q6・2026-09-30)と ON+Q7 のゲート(W10 の Q7)。

- 検算: 合成の騒音場(点の位置に既知の値を置く)で、物差しが既知の差を返すこと。
- 住所 → 小地域名(.dbf の S_NAME の書き方)・面積重心。
- 実データ: 切替口 OFF は昇格版の build_manifest と W10 の出力 6 本が sha256 一致・ON+Q7 の
  ゲート(当てた辺 225・primary+secondary 202/202・階級の不一致 0・既定比の最大 10 倍)・
  物差しが 7 点のうち渋谷区の 5 点に座標を付ける。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.field import common as C
from shibuya.build.field import road_names as RN
from shibuya.build.field import w10_noise as W
from shibuya.build.field import w10_ruler as R
from shibuya.build.pop import shapefile as SH

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
WORLD = DATA_DIR / "world" / "v2"
REAL_INPUTS = (
    DATA_DIR.joinpath(*RN.ROAD_NAMES),
    DATA_DIR.joinpath(*W.KASYO),
    DATA_DIR.joinpath(*W.R5_POINTS),
    DATA_DIR.joinpath(*R.BOUNDARY_SHP),
    DATA_DIR.joinpath(*R.BOUNDARY_DBF),
    WORLD / "w1_edges.parquet",
    WORLD / "w1_edge_geometry.npz",
    WORLD / "w10_street_points.parquet",
    WORLD / "w10_noise_day.npy",
    WORLD / "w10_noise_night.npy",
    WORLD / "build_manifest.json",
)
#: 実資産(R5 の CSV・境界の .shp/.dbf・街路点・騒音場・W1・manifest)が 1 つでも無ければ skip。
real = pytest.mark.skipif(not all(p.exists() for p in REAL_INPUTS), reason="data/ absent (CI)")


# ------------------------------------------------------------------ 住所・幾何
@pytest.mark.parametrize(
    "address, expected",
    [
        ("渋谷区神宮前5丁目53-1", ("渋谷区", "神宮前五丁目")),
        ("渋谷区鉢山町14", ("渋谷区", "鉢山町")),
        ("渋谷区広尾5丁目7-4", ("渋谷区", "広尾五丁目")),
        ("渋谷区本町1丁目56-2", ("渋谷区", "本町一丁目")),
        ("渋谷区東3丁目2-10", ("渋谷区", "東三丁目")),
        ("目黒区青葉台4丁目4", ("目黒区", "青葉台四丁目")),
        ("世田谷区用賀２丁目31", ("世田谷区", "用賀二丁目")),   # 全角数字
        ("東京都渋谷区テスト町12丁目1", ("渋谷区", "テスト町十二丁目")),
    ],
)
def test_chome_name_from_address(address, expected):
    assert R.chome_name_from_address(address) == expected


@pytest.mark.parametrize(
    "address, ward, name, code",
    [
        ("目黒区三田1丁目2", "目黒区", "三田一丁目", "CHOME"),         # 町名の漢数字はそのまま
        ("目黒区五本木2丁目", "目黒区", "五本木二丁目", "CHOME"),
        ("港区六本木6丁目", "港区", "六本木六丁目", "CHOME"),
        ("新宿区四谷1丁目", "新宿区", "四谷一丁目", "CHOME"),
        ("渋谷区千駄ヶ谷3丁目", "渋谷区", "千駄ヶ谷三丁目", "CHOME"),
        ("渋谷区神宮前五丁目53-1", "渋谷区", "神宮前五丁目", "CHOME"),   # 丁目の番号が漢数字
        ("港区三田三丁目", "港区", "三田三丁目", "CHOME"),
        ("渋谷区テスト町十二丁目", "渋谷区", "テスト町十二丁目", "CHOME"),
        ("渋谷区神宮前5-53-1", "渋谷区", "神宮前", "NO_CHOME_HYPHEN"),   # 丁目の無い書き方
        ("渋谷区鉢山町14", "渋谷区", "鉢山町", "TOWN"),
        ("渋谷区鉢山町", "渋谷区", "鉢山町", "TOWN"),
        ("神宮前5丁目", None, None, "UNPARSEABLE"),                     # 区が無い
    ],
)
def test_parse_address(address, ward, name, code):
    assert R.parse_address(address) == {"ward": ward, "name": name, "code": code}


def test_chome_name_from_address_raises_only_when_unparseable():
    with pytest.raises(ValueError):
        R.chome_name_from_address("神宮前5丁目")


def test_kanji_number():
    assert [R._kanji_number(n) for n in (1, 9, 10, 12, 20, 21)] == ["一", "九", "十", "十二", "二十", "二十一"]
    assert [R._parse_kanji_number(k) for k in ("一", "九", "十", "十二", "二十", "二十一")] == [1, 9, 10, 12, 20, 21]


def test_projection_uses_the_canonical_function():
    """小地域の投影は正典 ``geo.common.latlon_to_local`` と同じ値(写しを持たない)。"""
    from shibuya.build.geo import common as G

    lat, lon = 35.66, 139.70
    x, y = R._lonlat_to_local(np.array([lon]), np.array([lat]))
    assert (float(x[0]), float(y[0])) == G.latlon_to_local(lat, lon)


def test_polygon_centroid_of_an_l_shape():
    # L 字(4×2 の長方形+2×2 の正方形)の重心を分割で検算
    ring = np.array([[0, 0], [4, 0], [4, 2], [2, 2], [2, 4], [0, 4]], dtype=np.float64)
    poly = SH.Polygon(np.array([0]), ring, (0, 0, 4, 4))
    # 分割: [0,4]×[0,2](面積 8・重心 (2,1))+[0,2]×[2,4](面積 4・重心 (1,3))
    ex = ((8 * 2 + 4 * 1) / 12, (8 * 1 + 4 * 3) / 12)
    assert R.polygon_centroid(poly) == pytest.approx(ex)
    # 向きを逆にしても同じ
    assert R.polygon_centroid(SH.Polygon(np.array([0]), ring[::-1].copy(), (0, 0, 4, 4))) == pytest.approx(ex)


def test_points_to_segments_min_dist():
    segs = (np.array([0.0]), np.array([0.0]), np.array([10.0]), np.array([0.0]), np.array([0]))
    d = R.points_to_segments_min_dist(np.array([5.0, -3.0, 13.0]), np.array([2.0, 4.0, 4.0]), segs)
    assert d == pytest.approx([2.0, 5.0, 5.0])
    empty = tuple(np.zeros(0) for _ in range(4)) + (np.zeros(0, dtype=np.int64),)
    assert np.isinf(R.points_to_segments_min_dist(np.array([0.0]), np.array([0.0]), empty)).all()


# ------------------------------------------------------------------ 検算(合成の騒音場)
def test_measure_near_returns_known_values():
    px = np.array([0.0, 10.0, 30.0, 0.0, 200.0])
    py = np.array([0.0, 0.0, 0.0, 60.0, 0.0])
    val = {"day": np.array([60.0, 70.0, 80.0, 90.0, 99.0]), "night": np.array([50.0, 66.0, 76.0, 86.0, 95.0])}
    rd = np.array([5.0, 0.5, 0.5, 9.0, 0.0])
    m25 = R.measure_near(0.0, 0.0, px, py, val, rd, 25.0)
    assert m25["n"] == 2 and m25["max"] == {"day": 70.0, "night": 66.0}
    assert m25["road"] == {"day": 70.0, "night": 66.0} and m25["road_index"] == 1
    assert m25["road_dist_m"] == 0.5 and m25["road_beyond_band"] is False
    m100 = R.measure_near(0.0, 0.0, px, py, val, rd, 100.0)
    assert m100["max"] == {"day": 90.0, "night": 86.0} and m100["n"] == 4  # 200 m 先の 99 は入らない
    empty = R.measure_near(500.0, 500.0, px, py, val, rd, 25.0)
    assert empty["max"] == {"day": None, "night": None} and empty["road_index"] is None
    none = R.measure_near(0.0, 0.0, px, py, val, np.full(5, np.inf), 25.0)
    assert none["road"] == {"day": None, "night": None} and none["road_beyond_band"] is None


def test_measure_near_ties_pick_one_grid_point_for_day_and_night():
    """同距離(0.5 m)の 2 点: 格子の番号の小さい方(添字 1)を採り、昼も夜も同じ点から読む。
    昼は添字 2 の方が大きく、夜は添字 1 の方が大きい=「値の大きい方」なら昼夜で別の点になる場面。"""
    px = np.array([0.0, 10.0, 20.0])
    py = np.zeros(3)
    val = {"day": np.array([60.0, 70.0, 80.0]), "night": np.array([50.0, 77.0, 66.0])}
    rd = np.array([5.0, 0.5, 0.5])
    m = R.measure_near(0.0, 0.0, px, py, val, rd, 50.0)
    assert m["road_index"] == 1 and m["road"] == {"day": 70.0, "night": 77.0}
    # 並びを入れ替えても「番号の小さい方」
    m2 = R.measure_near(0.0, 0.0, px[[0, 2, 1]], py, {k: v[[0, 2, 1]] for k, v in val.items()}, rd[[0, 2, 1]], 50.0)
    assert m2["road_index"] == 1 and m2["road"] == {"day": 80.0, "night": 66.0}


def test_measure_near_marks_road_values_beyond_the_grid_band():
    """道路から ROAD_BAND_M(8 m・D-W9)より遠い格子の値は、値を残して印を付ける。"""
    assert R.ROAD_BAND_M == 8.0 == RN.MATCH_BUFFER_M
    px, py = np.array([0.0]), np.array([0.0])
    for dist, beyond in ((8.0, False), (8.001, True), (120.0, True)):
        m = R.measure_near(0.0, 0.0, px, py, {"day": np.array([60.0])}, np.array([dist]), 10.0)
        assert m["road"] == {"day": 60.0} and m["road_beyond_band"] is beyond


def test_measure_near_rejects_nan():
    px, py = np.array([0.0, 1.0]), np.zeros(2)
    with pytest.raises(ValueError, match="距離"):
        R.measure_near(0.0, 0.0, px, py, {"day": np.array([50.0, 60.0])}, np.array([np.nan, 2.0]), 5.0)
    with pytest.raises(ValueError, match="値"):
        R.measure_near(0.0, 0.0, px, py, {"day": np.array([np.nan, 60.0])}, np.array([1.0, 2.0]), 5.0)


def test_road_facing_point_ties_take_the_lower_grid_index():
    ring = np.array([[-10, -10], [10, -10], [10, 10], [-10, 10]], dtype=np.float64)
    ch = R.Chome("t", "t", SH.Polygon(np.array([0]), ring, (-10, -10, 10, 10)), (0.0, 0.0), 400.0)
    px, py = np.array([5.0, -5.0, 0.0]), np.array([0.0, 0.0, 0.0])
    on = np.array([True, True, False])
    assert R.road_facing_point(ch, px, py, on) == (5.0, 0.0)
    assert R.road_facing_point(ch, px[[1, 0, 2]], py, on) == (-5.0, 0.0)


def _synthetic():
    """200 m 四方の町丁目(中心=e-Stat の代表点=原点)+ y=50 に幹線(primary)の格子点(70/66 dB)・
    y=−50 に住宅地(55/51 dB)・(0, 80) に service の格子点(90/86 dB)。"""
    ring = np.array([[-100, -100], [100, -100], [100, 100], [-100, 100]], dtype=np.float64)
    ch = R.Chome("t", "テスト町一丁目", SH.Polygon(np.array([0]), ring, (-100, -100, 100, 100)), (0.0, 0.0), 40000.0)
    xs = np.arange(-100.0, 101.0, 10.0)
    gx = np.concatenate([xs, xs, [0.0]])
    gy = np.concatenate([np.full(xs.size, 50.0), np.full(xs.size, -50.0), [80.0]])
    gday = np.concatenate([np.full(xs.size, 70.0), np.full(xs.size, 55.0), [90.0]])
    gnight = gday - 4.0
    gklass = ["primary"] * xs.size + ["residential"] * xs.size + ["service"]
    seg_primary = (np.array([-100.0]), np.array([52.0]), np.array([100.0]), np.array([52.0]), np.array([0]))
    seg_all = tuple(np.concatenate([a, b]) for a, b in zip(
        seg_primary,
        (np.array([-100.0]), np.array([-52.0]), np.array([100.0]), np.array([-52.0]), np.array([1])),
    ))

    def segs_of(klasses):
        return seg_primary if set(klasses) == {"primary", "secondary"} else seg_all

    return ch, gx, gy, gday, gnight, gklass, segs_of


def test_ruler_rows_returns_the_known_difference_on_a_synthetic_field():
    ch, gx, gy, gday, gnight, gklass, segs_of = _synthetic()
    pts = [
        {"no": "1", "address": "渋谷区テスト町1丁目2", "road_kind": "4",
         "measured_day_db": 65.0, "measured_night_db": 60.0},
        {"no": "2", "address": "目黒区テスト町1丁目2", "road_kind": "4",
         "measured_day_db": 65.0, "measured_night_db": 60.0},
    ]
    rows = R.ruler_rows(pts, {ch.s_name: ch}, gx, gy, gday, gnight, gklass, segs_of)
    ok, nb = rows
    assert nb["status"] == "NO_BOUNDARY"
    assert ok["status"] == "OK" and ok["rep_xy"]["road_facing"] == [0.0, 50.0]
    d = ok["diff"]
    # e-Stat の点(原点): 25 m 内に格子点なし / 50 m で幹線 70(+5/+6)・住宅地 55 も入るが max は 70
    assert d["estat"]["max"]["25"] is None and d["estat"]["road"]["25"] is None
    assert d["estat"]["max"]["50"] == [5.0, 6.0] and d["estat"]["road"]["50"] == [5.0, 6.0]
    # 100 m で service の 90 dB が入る → max は +25/+26・道路に最も近い格子は幹線のまま +5/+6
    assert d["estat"]["max"]["100"] == [25.0, 26.0] and d["estat"]["road"]["100"] == [5.0, 6.0]
    # 道路に面した点 (0, 50): 25 m で幹線だけ(+5)・50 m で service(30 m 先)が入る
    assert d["road_facing"]["max"]["25"] == [5.0, 6.0]
    assert d["road_facing"]["max"]["50"] == [25.0, 26.0] and d["road_facing"]["road"]["50"] == [5.0, 6.0]
    err = ok["error"]
    assert err["equivalent_radius_m"] == pytest.approx(round(float(np.sqrt(40000 / np.pi)), 1))
    assert err["estat_to_road_facing_m"] == 50.0 and err["estat_to_centroid_m"] == 0.0
    assert err["measured_road_day_pct"] == {"5": 70.0, "50": 70.0, "95": 70.0}


def test_ruler_rows_shifts_exactly_with_the_field():
    """騒音場を一様に +k dB すると、全ての差がちょうど +k 動く(物差しの線形性)。"""
    ch, gx, gy, gday, gnight, gklass, segs_of = _synthetic()
    pts = [{"no": "1", "address": "渋谷区テスト町1丁目2", "road_kind": "5",
            "measured_day_db": 65.0, "measured_night_db": 60.0}]
    a = R.ruler_rows(pts, {ch.s_name: ch}, gx, gy, gday, gnight, gklass, segs_of)[0]
    b = R.ruler_rows(pts, {ch.s_name: ch}, gx, gy, gday + 3.0, gnight + 3.0, gklass, segs_of)[0]
    for rep in R.REPRESENTATIVES:
        for s in R.STATISTICS:
            for r, v in a["diff"][rep][s].items():
                w = b["diff"][rep][s][r]
                assert (v is None) == (w is None)
                if v is not None:
                    assert w == pytest.approx([v[0] + 3.0, v[1] + 3.0])


def test_raising_one_grid_point_moves_only_the_max_of_the_radii_that_contain_it():
    """幾何が効く検算: (0, 80) の service 点(e-Stat の点から 80 m)だけを +20 dB すると、
    e-Stat の点の max は r=100 だけ +20 動き、r=25/50 と road(幹線)は動かない。"""
    ch, gx, gy, gday, gnight, gklass, segs_of = _synthetic()
    pts = [{"no": "1", "address": "渋谷区テスト町1丁目2", "road_kind": "4",
            "measured_day_db": 65.0, "measured_night_db": 60.0}]
    a = R.ruler_rows(pts, {ch.s_name: ch}, gx, gy, gday, gnight, gklass, segs_of)[0]
    bump = np.zeros(gx.size)
    bump[-1] = 20.0
    b = R.ruler_rows(pts, {ch.s_name: ch}, gx, gy, gday + bump, gnight + bump, gklass, segs_of)[0]
    assert a["diff"]["estat"]["max"]["100"] == [25.0, 26.0] and b["diff"]["estat"]["max"]["100"] == [45.0, 46.0]
    for r in ("25", "50"):
        assert a["diff"]["estat"]["max"][r] == b["diff"]["estat"]["max"][r]
    assert a["diff"]["estat"]["road"] == b["diff"]["estat"]["road"]


def test_address_forms_become_status_codes_not_exceptions():
    ch, gx, gy, gday, gnight, gklass, segs_of = _synthetic()
    chome = {ch.s_name: ch, "鉢山町": ch}
    base = {"road_kind": "4", "measured_day_db": 65.0, "measured_night_db": 60.0}
    addrs = {
        "a": "渋谷区テスト町1丁目2",   # OK
        "b": "渋谷区テスト町1-2-3",    # 丁目の無い書き方・町に丁目がある
        "c": "渋谷区三田1丁目2",      # 町名に漢数字・渋谷区の境界に無い
        "d": "目黒区三田1丁目2",      # 区の境界が無い
        "e": "テスト町1丁目",          # 区が読めない
        "f": "渋谷区鉢山町14",        # 丁目の無い町
    }
    rows = R.ruler_rows([{"no": k, "address": v, **base} for k, v in addrs.items()],
                        chome, gx, gy, gday, gnight, gklass, segs_of)
    got = {r["no"]: r["status"] for r in rows}
    assert got == {"a": "OK", "b": "AMBIGUOUS_NO_CHOME", "c": "NAME_NOT_FOUND", "d": "NO_BOUNDARY",
                   "e": "UNPARSEABLE", "f": "OK"}
    assert set(got.values()) <= set(R.STATUSES)


def test_summarize_diffs():
    s = R.summarize_diffs([[1.0, -2.0], None, [3.0, 2.0]])
    assert s == {"n": 2, "mean_day": 2.0, "mean_night": 0.0, "mean_abs_day": 2.0, "mean_abs_night": 2.0}
    assert R.summarize_diffs([None])["n"] == 0


# ------------------------------------------------------------------ 実データ
def _w10(tmp_path: Path, name: str):
    out = tmp_path / name
    out.mkdir()
    for f in ("w1_edges.parquet", "w1_edge_geometry.npz"):
        (out / f).write_bytes((WORLD / f).read_bytes())
    return W.run(C.Ctx(data=DATA_DIR, out=out)), out


def _manifest_w10() -> dict[str, str]:
    m = json.loads((WORLD / "build_manifest.json").read_text(encoding="utf-8"))
    st = next(s for s in m["stages"] if s["stage"] == "W10")
    return {o["path"]: o["sha256"] for o in st["outputs"]}


@real
def test_switch_off_reproduces_the_promoted_w10_outputs(tmp_path):
    """切替口 OFF(既定)の W10 の出力 6 本は、昇格版の build_manifest の sha256 と一致する。"""
    assert W.USE_ROAD_NAME_MATCH is False and W.ROAD_NAME_REQUIRE_NAMED_SAME_CLASS is False
    res, _ = _w10(tmp_path, "off")
    got = {o["path"]: o["sha256"] for o in res.outputs}
    assert got == _manifest_w10()


@real
def test_on_q7_gates(tmp_path, monkeypatch):
    """ON+Q7(W10 の Q7): 当てた辺 225・primary+secondary 202/202(PASS)・階級の不一致 0・最大 10 倍。"""
    import pyarrow.parquet as pq

    monkeypatch.setattr(W, "USE_ROAD_NAME_MATCH", True)
    monkeypatch.setattr(W, "ROAD_NAME_REQUIRE_NAMED_SAME_CLASS", True)
    monkeypatch.setattr(W, "ROAD_NAME_REQUIRE_SAME_BAND", False)
    res, out = _w10(tmp_path, "onq7")
    gates = {g.name: g.to_json() for g in res.gates}
    assert gates["road_edges_with_census_traffic"]["value"] == 225
    assert gates["primary_secondary_sections_matched"]["value"] == 202
    assert gates["primary_secondary_sections_matched"]["pass"] is True
    t = pq.read_table(out / "w10_edge_section.parquet").to_pydict()
    applied = [i for i, a in enumerate(t["traffic_from_census"]) if a]
    assert len(applied) == 225
    mismatch = [
        i for i in applied
        if RN.CLASS_TIER.get(t["klass"][i], "") != RN.CLASS_TIER.get(t["way_highway"][i], "?")
    ]
    assert mismatch == []
    routes = res.notes["road_name_route_sections"]
    defaults = res.notes["census_defaults"]
    ratio = max(routes[t["census_route"][i]]["q24"] / defaults[t["klass"][i]]["q24"] for i in applied)
    assert round(ratio, 1) == 10.0
    # 較正の残差は ON+Q7 でも動かない(較正は辺を通らない)
    rows = {r["no"]: (r["residual_day_db"], r["residual_night_db"]) for r in res.notes["calibration_rows"]}
    assert rows["61"] == (5.1, 4.5) and rows["75"] == (7.3, 6.4)
    # 街路格子は OFF と同じ(交通量だけが変わる)
    assert {o["path"]: o["sha256"] for o in res.outputs}["w10_street_points.parquet"] == (
        _manifest_w10()["w10_street_points.parquet"]
    )


@real
def test_ruler_places_the_five_shibuya_points_on_the_promoted_field():
    import pyarrow.parquet as pq

    chome = R.load_chome(DATA_DIR.joinpath(*R.BOUNDARY_SHP), DATA_DIR.joinpath(*R.BOUNDARY_DBF))
    assert len(chome) == 80
    pts = W.read_r5_points(DATA_DIR.joinpath(*W.R5_POINTS))
    names = {p["no"]: R.chome_name_from_address(p["address"]) for p in pts}
    placed = sorted(no for no, (ward, name) in names.items() if ward == "渋谷区" and name in chome)
    assert placed == ["78", "79", "80", "81", "82"]
    # e-Stat の代表点は町丁目の中にある(5 点とも)
    for no in placed:
        ch = chome[names[no][1]]
        assert SH.points_in_polygon(np.array([ch.estat_xy[0]]), np.array([ch.estat_xy[1]]), ch.poly)[0]
    # 街路格子(=世界の範囲)が届くのは 78・79・82 の 3 点だけ(80 広尾五・81 本町一は世界の外)
    d = pq.read_table(WORLD / "w10_street_points.parquet", columns=["x", "y", "band"]).to_pydict()
    gx, gy = np.asarray(d["x"], dtype=np.float64), np.asarray(d["y"], dtype=np.float64)
    inside = {no: int(SH.points_in_polygon(gx, gy, chome[names[no][1]].poly).sum()) for no in placed}
    assert sorted(no for no, n in inside.items() if n > 1000) == ["78", "79", "82"]
    assert inside["80"] == 0 and inside["81"] == 0


@real
def test_ruler_values_on_the_promoted_field():
    """README §W10 の見出しの数値(昇格版=OFF の騒音場)を固定する。"""
    rows = {r["no"]: r for r in R.ruler_from_world(WORLD, DATA_DIR)}
    assert {k: r["status"] for k, r in rows.items()} == {
        "61": "NO_BOUNDARY", "75": "NO_BOUNDARY", "78": "OK", "79": "OK",
        "80": "OUTSIDE_WORLD", "81": "OUTSIDE_WORLD", "82": "OK",
    }
    assert rows["79"]["diff"]["estat"]["max"]["50"] == [0.0, -3.0]
    assert rows["79"]["diff"]["estat"]["max"]["25"] is None          # 25 m 内に GL の格子なし
    assert rows["78"]["diff"]["road_facing"]["road"]["25"] == [9.0, 7.0]
    assert rows["78"]["road_beyond_band"]["road_facing"]["25"] is False
    # e-Stat の点の road は道路から 234 m 離れた格子の値=帯の外の印
    assert rows["78"]["road_dist_m"]["estat"]["50"] == pytest.approx(233.891)
    assert rows["78"]["road_beyond_band"]["estat"]["50"] is True
    assert rows["79"]["road_beyond_band"]["estat"]["100"] is True
    ok = [r for r in rows.values() if r["status"] == "OK"]
    s = R.summarize_diffs([r["diff"]["estat"]["max"]["50"] for r in ok])
    assert (s["n"], s["mean_day"], s["mean_night"]) == (3, 6.33, 4.33)
    err = rows["79"]["error"]
    assert err["equivalent_radius_m"] == 185.3 and err["estat_to_road_facing_m"] == 140.3


@real
def test_ruler_values_on_the_on_q7_field(tmp_path, monkeypatch):
    """ON+Q7 の騒音場で物差しが最も動く所: No.82 の road_facing/max/r25 が +7/+6 → +5/+3(夜 −3)。"""
    monkeypatch.setattr(W, "USE_ROAD_NAME_MATCH", True)
    monkeypatch.setattr(W, "ROAD_NAME_REQUIRE_NAMED_SAME_CLASS", True)
    monkeypatch.setattr(W, "ROAD_NAME_REQUIRE_SAME_BAND", False)
    _, out = _w10(tmp_path, "onq7ruler")
    rows = {r["no"]: r for r in R.ruler_from_world(out, DATA_DIR)}
    assert rows["82"]["diff"]["road_facing"]["max"]["25"] == [5.0, 3.0]
    assert rows["78"]["diff"]["road_facing"]["max"]["50"] == [13.0, 11.0]
    assert rows["79"]["diff"]["estat"]["max"]["50"] == [0.0, -3.0]   # e-Stat の点の近くは動かない
