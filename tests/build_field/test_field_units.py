"""build.field の単体テスト(データ不要・CI で常に走る)。

- W7: opening_hours パーサの対応部分集合・法規上限の適用・カテゴリ既定表の被覆・
  **法規の記録**(citation の条番号・expedient 台帳・D-72 (a))。
- W10: ASJ RTN-Model 2018 の式値(手計算)・伝搬・車線幾何・段階境界・路線名の正規化。
- W12: 時間帯ラベルの写像・等間隔ダイヤ・運行日の分。
- W13: NOAA 太陽位置(東京の公表値と突合)・曜日種別・層からの日選択の決定論。
- build.run: 段階順(W7 → W10 → W11 の数値順)・部分ランの manifest 分離。
"""

from __future__ import annotations

import datetime as dt
import inspect
import math
from pathlib import Path

import pytest

from shibuya.build.field import common as C
from shibuya.build.field import w7_planspec as w7
from shibuya.build.field import w10_noise as w10
from shibuya.build.field import w12_external_nodes as w12
from shibuya.build.field import w13_weather as w13
from shibuya.build.geo import poi_class
from shibuya.build import run as build_run

# --- W7 opening_hours パーサ ---------------------------------------------------------------

ALL_DAY = [[(0, 1440)] for _ in range(7)]


@pytest.mark.parametrize(
    "text,expected",
    [
        ("24/7", ALL_DAY),
        ("Mo-Su,PH 00:00-24:00", ALL_DAY),
        ("Mo-Su 10:00-22:00", [[(600, 1320)]] * 7),
        ("10:00-22:00", [[(600, 1320)]] * 7),
        # 日跨ぎ(閉店 < 開店)は +1440
        ("11:30-02:00", [[(690, 1560)]] * 7),
        # 複数時刻範囲
        ("11:00-15:00, 17:00-20:00", [[(660, 900), (1020, 1200)]] * 7),
    ],
)
def test_parse_opening_hours_uniform(text, expected):
    assert w7.parse_opening_hours(text) == expected


def test_parse_opening_hours_day_ranges():
    got = w7.parse_opening_hours("Mo-Fr 07:00-21:00; Sa 08:00-20:00; Su,PH 08:00-19:00")
    assert got[:5] == [[(420, 1260)]] * 5
    assert got[5] == [(480, 1200)]
    assert got[6] == [(480, 1140)]  # PH は無視され Su だけが立つ


def test_parse_opening_hours_comma_separated_rules():
    """``Mo-Fr …, Sa …`` は規則の並び・``Mo-Th, Su …`` は曜日の列挙(割らない)。"""
    got = w7.parse_opening_hours("Mo-Fr 11:00-22:00, Sa 11:00-21:00, Su 11:00-22:00")
    assert got[5] == [(660, 1260)] and got[6] == [(660, 1320)]
    got2 = w7.parse_opening_hours("Mo-Th, Su 17:00-02:00")
    assert got2[0] == [(1020, 1560)] and got2[6] == [(1020, 1560)]
    assert got2[4] == [] and got2[5] == []


def test_parse_opening_hours_off():
    got = w7.parse_opening_hours("Mo,Tu,Fr,Sa 17:00-24:00; We off; Th off; Su 04:00-23:00; PH off")
    assert got[2] == [] and got[3] == []
    assert got[6] == [(240, 1380)]


@pytest.mark.parametrize(
    "text",
    [
        "",
        "sunrise-sunset",
        "Jan-Mar 10:00-18:00",
        "Mo-Su 10:00-22:00; 2026 Jul 21 - 2026 Aug 28 closed",
        "12:00-14:30 sat sun , 17:30-23:00 22 last order",
    ],
)
def test_parse_opening_hours_unsupported(text):
    with pytest.raises(w7.OpeningHoursParseError):
        w7.parse_opening_hours(text)


# --- W7 法規上限 -----------------------------------------------------------------------------


def _windows(key: str):
    return w7.LAW_CAPS[key]["closed_windows_min"]


def test_law_cap_truncates_and_drops():
    week = [[(1320, 1800)] for _ in range(7)]  # 22:00-30:00
    capped, eff = w7.apply_law_cap(week, _windows("tokutei_yukyo"))
    assert eff.changed is True and eff.closing_moved == 7 and eff.opening_moved == 0
    assert capped == [[(1320, 1740)] for _ in range(7)]  # 5:00 で切る
    # 営業不可窓の中にしか無い区間は消える(特定遊興の 5:00-6:00)
    dropped, eff2 = w7.apply_law_cap([[(310, 350)]], _windows("tokutei_yukyo"))
    assert eff2.dropped == 1 and dropped == [[]]


def test_law_cap_none_is_identity():
    week = [[(600, 1800)] for _ in range(7)]
    capped, eff = w7.apply_law_cap(week, _windows("ippan_inshoku"))
    assert eff.changed is False and capped == week


def test_law_cap_clips_opening_side_pachinko():
    """D-W8 ぱちんこ 4号=23:00-翌10:00 営業不可 → 09:00-23:30 は 10:00-23:00 になる。"""
    week = [[(540, 1410)] for _ in range(7)]  # 09:00-23:30
    capped, eff = w7.apply_law_cap(week, _windows("pachinko_mahjong"))
    assert capped == [[(600, 1380)] for _ in range(7)]  # 10:00-23:00
    assert eff.opening_moved == 7 and eff.closing_moved == 7 and eff.dropped == 0


def test_law_cap_game_center_splits_24h():
    """ゲームセンター 5号=1:00-10:00 営業不可 → 24時間営業は 0:00-1:00 と 10:00-24:00 に割れる。"""
    capped, eff = w7.apply_law_cap([[(0, 1440)]], _windows("game_center"))
    assert capped == [[(0, 60), (600, 1440)]]
    assert eff.split == 1


def test_law_cap_opening_side_by_law_key():
    """開店側の切り上げ(D-W8 の営業不可時間欄)を業態ごとに1本ずつ。"""
    # 店舗型性風俗 0:00-6:00 → 開店は 6:00 以降・閉店は 24:00 まで
    assert w7.apply_law_cap([[(0, 1440)]], _windows("tenpo_seifuzoku"))[0] == [[(360, 1440)]]
    # 接待飲食等 1:00-6:00 → 17:00-5:00 は 17:00-1:00(翌1:00=1500)
    assert w7.apply_law_cap([[(1020, 1740)]], _windows("settai_inshoku"))[0] == [[(1020, 1500)]]
    # 接待飲食等は開店側も切る(4:00 開店 → 6:00)
    assert w7.apply_law_cap([[(240, 720)]], _windows("settai_inshoku"))[0] == [[(360, 720)]]
    # 特定遊興 5:00-6:00 → 閉店 5:00 まで、または開店 6:00 から
    assert w7.apply_law_cap([[(330, 720)]], _windows("tokutei_yukyo"))[0] == [[(360, 720)]]


def test_prohibited_window_expansion_repeats_daily():
    """営業不可窓は毎日繰り返す(23:00-翌10:00 は当日 0:00-10:00 でもある)。"""
    assert w7.prohibited_intervals(((1380, 2040),)) == [(0, 600), (1380, 2040), (2820, 2880)]
    assert w7.prohibited_intervals(((0, 360),)) == [(0, 360), (1440, 1800)]
    assert w7.prohibited_intervals(()) == []


def test_intervals_in_prohibited_window_is_zero_after_apply():
    """適用後の不変条件(ゲート intervals_over_law_cap_after_apply)を関数の水準で。"""
    for key in w7.LAW_CAPS:
        win = _windows(key)
        week = [[(0, 1440)], [(540, 1410)], [(1020, 1740)], [], [(300, 400)], [(0, 1440)], []]
        before = w7.intervals_in_prohibited_window(week, win)
        capped, _eff = w7.apply_law_cap(week, win)
        assert w7.intervals_in_prohibited_window(capped, win) == 0, key
        if win:
            assert before > 0, key


def test_law_cap_values_match_dw8_table():
    caps = {k: v["close_cap_min"] for k, v in w7.LAW_CAPS.items()}
    assert caps["settai_inshoku"] == 1500  # 1:00
    assert caps["pachinko_mahjong"] == 1380  # 23:00
    assert caps["game_center"] == 1500  # 1:00
    assert caps["tokutei_yukyo"] == 1740  # 5:00
    assert caps["tenpo_seifuzoku"] == 1440  # 0:00
    assert caps["shinya_shurui"] is None and caps["ippan_inshoku"] is None
    assert all(v["citation"] for k, v in w7.LAW_CAPS.items() if k != "none")
    # 営業不可時間欄(D-W8)の転記
    win = {k: v["closed_windows_min"] for k, v in w7.LAW_CAPS.items()}
    assert win["settai_inshoku"] == ((60, 360),)  # 1:00-6:00
    assert win["pachinko_mahjong"] == ((1380, 2040),)  # 23:00-翌10:00
    assert win["game_center"] == ((60, 600),)  # 1:00-10:00
    assert win["tokutei_yukyo"] == ((300, 360),)  # 5:00-6:00
    assert win["tenpo_seifuzoku"] == ((0, 360),)  # 0:00-6:00
    assert win["shinya_shurui"] == () and win["ippan_inshoku"] == ()
    # 立入制限は営業時間の規制ではない(D-W8 の閉店上限欄=「—」)
    assert win["minor_entry_limit"] == () and caps["minor_entry_limit"] is None
    # 閉店上限欄は窓から導ける値であること(整合の検算)
    for key, cap in caps.items():
        if cap is None or not win[key]:
            continue
        pw = w7.prohibited_intervals(win[key])
        assert any(a == cap for a, _b in pw), key


def test_law_key_prefers_osm_tag():
    assert w7.law_key_for("nightlife", None, {"amenity": "nightclub"}) == "tokutei_yukyo"
    assert w7.law_key_for("nightlife", None, {}) == "shinya_shurui"
    assert w7.law_key_for("shop", "pachinko", {}) == "pachinko_mahjong"
    assert w7.law_key_for("hotel", "love_hotel", {}) == "none"  # 判定不能=上限なし


def test_default_week_respects_closed_days():
    week = w7.default_week("office", None)
    assert week[5] == [] and week[6] == []
    assert week[0] == [(540, 1080)]
    assert w7.weekly_open_minutes(w7.default_week("shop", "convenience")) == 7 * 1440


# --- W7 法規の記録(D-72 (a)・2026-09-17・**数値は動かさない**) -------------------------------
# 出典: docs/research/v2-w7-law-primary-check-research.md(等級A・親が条文を一次確認)。
# ここで固定するのは**記録**(citation の条番号・expedient 台帳)だけで、窓・上限は上の
# test_law_cap_values_match_dw8_table が引き続き守る。


def test_citation_article_numbers_are_fixed():
    """答申 §3 ②: 規則6条2項は**時**(午前1時)・地域は 条例4条の2第2項+規則5条+告示。"""
    settai = w7.LAW_CAPS["settai_inshoku"]["citation"]
    assert "規則6条2項" in settai and "午前1時" in settai
    assert "4条の2第2項" in settai and "規則5条" in settai and "公安委員会告示" in settai
    assert "4条の3第2号" in settai
    # 「規則6条(営業延長許容地域=…)」という旧記述(時と地域の取り違え)は消えていること
    assert "同施行規則6条(営業延長許容地域" not in settai
    game = w7.LAW_CAPS["game_center"]["citation"]
    assert "条例5条 表" in game and "営業延長許容地域の行" in game
    assert "規則6条2項" in game and "4条の2第2項" in game and "規則5条" in game
    # 他の業態の条番号は動かしていない(答申 §2 の一次確認どおり)
    assert w7.LAW_CAPS["pachinko_mahjong"]["citation"].startswith("東京都風俗営業")
    assert "5条" in w7.LAW_CAPS["pachinko_mahjong"]["citation"]
    assert "31条の23" in w7.LAW_CAPS["tokutei_yukyo"]["citation"]
    assert "15条" in w7.LAW_CAPS["shinya_shurui"]["citation"]
    assert "11条" in w7.LAW_CAPS["tenpo_seifuzoku"]["citation"]
    assert "16条" in w7.LAW_CAPS["minor_entry_limit"]["citation"]


def test_expedients_ledger_registers_the_law_gaps():
    """答申 §3 の ①⑦⑧④ が expedient 台帳に載っていること(方法論「全cap/近似にタグ」)。"""
    led = w7.EXPEDIENTS
    assert isinstance(led, tuple) and all(isinstance(s, str) and s for s in led)
    joined = "\n".join(led)
    # ① 地域条件なしの一律適用
    area = [s for s in led if "地域条件なしの一律適用" in s]
    assert len(area) == 1, led
    for token in ("営業延長許容地域", "住居集合地域", "54町丁", "20m", "law_key_for"):
        assert token in area[0], token
    # ⑦ 特別日なし
    special = [s for s in led if "特別日なし" in s]
    assert len(special) == 1 and "4条の2第1項" in special[0]
    assert "4条の3第1号" in special[0] and "規則6条1項" in special[0]
    # ⑧ 青少年条例16条1項の一・二号(興行場・ボウリング/スケート/水泳)が未写像
    assert "興行場" in joined and "ボウリング" in joined and "未写像" in joined
    # ④ D-W8 表にあってコードに無い 2 行=未実装
    assert "条例8条" in joined and "条例6条" in joined and "未実装" in joined
    # ③ violability の修正は保留(生成値を動かさないため)=保留の事実も記録する
    assert "26条六号" in joined and "保留" in joined


def test_minor_entry_limit_is_still_mapped_to_three_and_four_only():
    """⑧ は**登録だけ**(写像は足さない=生成値が動かない)。"""
    keys = {k for k, v in w7.LAW_KEY_BY_CATSUB.items() if v == "minor_entry_limit"}
    assert keys == {("nightlife", "karaoke"), ("nightlife", "net_cafe")}
    tagged = {t for t in w7.OSM_TAG_LAW_OVERRIDE if t[2] == "minor_entry_limit"}
    assert tagged == {("amenity", "internet_cafe", "minor_entry_limit")}
    assert w7.law_key_for("cinema", None, {}) == "none"  # 興行場は未写像のまま
    assert w7.law_key_for("leisure", None, {"leisure": "bowling_alley"}) == "none"


def test_violability_rule_is_unchanged_so_the_parquet_does_not_move():
    """③ は**保留**(D-72)。窓の有無で決める規則のままであること=生成列が動かない。"""
    src = inspect.getsource(w7.run)
    assert 'violability.append("enforced" if windows else "unenforced")' in src
    # 窓が空の業態(立入制限・上限なし)は unenforced 側に落ちる=現行 parquet と同じ割当
    for key in ("minor_entry_limit", "shinya_shurui", "ippan_inshoku", "none"):
        assert w7.LAW_CAPS[key]["closed_windows_min"] == ()
    for key in ("settai_inshoku", "pachinko_mahjong", "game_center", "tokutei_yukyo"):
        assert w7.LAW_CAPS[key]["closed_windows_min"] != ()


# --- W7 カテゴリ既定表の被覆(W6 subcat 改訂 2026-09-17)-------------------------------------


def test_category_defaults_cover_every_catsub_pair_w6_can_emit():
    """W6 が出しうる (cat, subcat) 対は全部 CATEGORY_DEFAULTS にある。

    ここが欠けると W7 は ``CATEGORY_DEFAULTS[(cat, subcat)]`` で KeyError になり、
    ゲート ``category_defaults_cover_all_catsub`` に届く前に落ちる。
    """
    missing = sorted(p for p in poi_class.CATSUB_PAIRS if p not in w7.CATEGORY_DEFAULTS)
    assert missing == []


def test_new_subcat_rows_inherit_the_parent_cat_row():
    """足した subcat 行は親 cat の行をそのまま継ぐ。

    = 「subcat が付いた」というだけでは営業窓も価格帯も 1 つも動かない。公園を
    0-1440/free に、図書館を公立図書館の窓にするような実態合わせは**別の判断**
    (親決定待ち・docs/design/v2-hobby-affordance-map.md §6 #5)。
    """
    added = (
        ("attraction", ("gallery", "museum")),
        ("hall", ("events_venue", "music_venue", "theatre")),
        ("leisure", ("gym", "park", "sports_centre")),
        ("service", ("library",)),
        (
            "shop",
            (
                "art_supply",
                "bicycle",
                "books",
                "florist",
                "hobby",
                "music_shop",
                "musical_instrument",
                "photo",
                "sports_shop",
                "stationery",
                "video_games",
            ),
        ),
    )
    for cat, subs in added:
        parent = w7.CATEGORY_DEFAULTS[(cat, None)]
        for sub in subs:
            assert w7.CATEGORY_DEFAULTS[(cat, sub)] == parent, (cat, sub)


def test_law_key_for_new_subcats_falls_back_to_the_cat():
    """新しい subcat は法規上限表に行を持たない=cat の行に落ちる(上限は動かない)。"""
    for sub in ("park", "books", "library", "theatre", "museum"):
        cat = poi_class.SUBCAT_TOPCAT[sub]
        assert w7.law_key_for(cat, sub, {}) == w7.law_key_for(cat, None, {})


# --- W10 ASJ RTN-Model 2018 -----------------------------------------------------------------


def test_l_wa_hand_computed():
    # 非定常・密粒・小型車・V=40 km/h → 82.3 + 10*lg 40 = 98.3206
    assert w10.l_wa("light", 40.0) == pytest.approx(82.3 + 10.0 * math.log10(40.0))
    assert w10.l_wa("light", 40.0) == pytest.approx(98.3206, abs=1e-3)
    # 大型車(2区分)
    assert w10.l_wa("heavy", 40.0) == pytest.approx(88.8 + 10.0 * math.log10(40.0))
    # 定常(首都高)は b=30
    assert w10.l_wa("light", 40.0, "steady_dense") == pytest.approx(
        45.8 + 30.0 * math.log10(40.0)
    )


def test_l_wa_speed_clamped_for_nonsteady():
    assert w10.l_wa("light", 5.0) == w10.l_wa("light", 10.0)
    assert w10.l_wa("light", 120.0) == w10.l_wa("light", 60.0)


def test_propagation_at_10m():
    # L_A = L_WA − 8 − 20 lg 10 = L_WA − 28
    assert w10.l_a_max(98.3206, 10.0) == pytest.approx(98.3206 - 28.0, abs=1e-9)
    # 距離倍で −6 dB
    assert w10.l_a_max(100.0, 20.0) - w10.l_a_max(100.0, 40.0) == pytest.approx(6.0206, abs=1e-3)


def test_lane_energy_coeff_matches_written_formula():
    v_kmh, n = 36.0, 3600.0
    got = w10.lane_energy_coeff("light", v_kmh, n, "nonsteady_dense")
    expect = (
        10 ** ((82.3 + 10 * math.log10(36.0) - 8.0) / 10.0) * (math.pi / (36.0 / 3.6)) * n / 3600.0
    )
    assert got == pytest.approx(expect, rel=1e-12)
    assert w10.lane_energy_coeff("light", v_kmh, 0.0, "nonsteady_dense") == 0.0


def test_geometry_factor_lane_positions():
    # 幅 8m・2車線 → 車線中心は中心線から ±2m。d=10 なら 8m と 12m。
    assert w10.lane_offsets(8.0, 2) == [2.0, -2.0]
    assert w10.geometry_factor(10.0, 8.0, 2) == pytest.approx(1 / 8 + 1 / 12)
    # 車道の上(d=0)は半車線幅で床を打つ
    assert w10.geometry_factor(0.0, 8.0, 2) == pytest.approx(1 / 2 + 1 / 2)


def test_hourly_flows_split():
    flows = w10.hourly_flows(q12=12000.0, q24=24000.0, heavy_pct=10.0)
    assert flows[12] == pytest.approx((900.0, 100.0))  # 昼 1000/h の 10%
    assert flows[2] == pytest.approx((900.0, 100.0))  # 夜も (24000-12000)/12=1000/h
    flows2 = w10.hourly_flows(q12=12000.0, q24=12000.0, heavy_pct=0.0)
    assert flows2[2] == (0.0, 0.0)


def test_noise_stage_boundaries_pegged_to_environmental_standard():
    assert w10.noise_stage(59.9) == 0 and w10.noise_stage(60.0) == 1
    assert w10.noise_stage(64.9) == 1 and w10.noise_stage(65.0) == 2
    assert w10.noise_stage(70.0) == 3
    assert w10.noise_stage(54.9, night=True) == 0 and w10.noise_stage(55.0, night=True) == 1
    assert w10.noise_stage(65.0, night=True) == 3
    assert len(w10.NOISE_STAGE_VOCAB) == len(w10.NOISE_STAGE_BOUNDS_DAY) + 1


def test_laeq_at_is_energy_sum_over_lanes():
    sec = {"q12": 12000.0, "q24": 24000.0, "heavy_pct": 10.0, "v_kmh": 36.0, "width_m": 8.0, "lanes": 2}
    day, night = w10.laeq_at(sec, 10.0, "nonsteady_dense")
    a_day, _ = w10.energy_coeffs(sec, "nonsteady_dense")
    assert day == pytest.approx(C.db_from_power(a_day * w10.geometry_factor(10.0, 8.0, 2)))
    # 昼夜の交通量が同じ設定なので昼夜同値
    assert day == pytest.approx(night)


def test_normalize_jp_route_names():
    assert C.normalize_jp("環状六号線") == C.normalize_jp("環状6号線")
    assert C.normalize_jp("一般国道２４６号") == C.normalize_jp("一般国道246号")


def test_route_match_prefix_and_city():
    sections = [
        {"route_key": C.normalize_jp("角筈和泉町線"), "city": "13113", "route_name": "角筈和泉町線"},
        {"route_key": C.normalize_jp("四谷角筈線"), "city": "13113", "route_name": "四谷角筈線"},
        {"route_key": C.normalize_jp("環状六号線"), "city": "13110", "route_name": "環状六号線"},
    ]
    hit = w10.route_match(sections, "角筈和泉線", "13113")
    assert [h["route_name"] for h in hit] == ["角筈和泉町線"]
    hit2 = w10.route_match(sections, "環状6号線", "13113")  # 市区町村に無ければ全都
    assert [h["route_name"] for h in hit2] == ["環状六号線"]


# --- W10 街路格子 ---------------------------------------------------------------------------


def test_street_points_on_a_single_edge():
    from shibuya.build.field.street_grid import street_points
    import numpy as np

    coords = np.array([[0.0, 0.0], [10.0, 0.0]])
    edges = {
        "edge_idx": [0],
        "klass": ["primary"],
        "band": ["GL"],
        "geom_start": [0],
        "geom_count": [2],
    }
    pts = street_points(edges, coords, buffer_m=2.5, pitch_m=2.5)
    # 格子は世界原点起点なので x∈{0,2.5,5,7.5,10}・y∈{-2.5,0,2.5} のうち距離≤2.5 の点
    xy = sorted(zip(pts.x.tolist(), pts.y.tolist()))
    assert (0.0, 0.0) in xy and (10.0, 0.0) in xy
    assert all(abs(y) <= 2.5 for _x, y in xy)
    assert set(pts.band) == {"GL"}
    assert set(pts.nearest_edge_idx.tolist()) == {0}


# --- W12 -------------------------------------------------------------------------------------


def test_time_bin_mapping():
    assert w12._pt_bin_to_hours("7時台") == [7]
    assert w12._pt_bin_to_hours("～6時台") == [5, 6]
    assert w12._pt_bin_to_hours("0時台～") == [0, 1]


def test_hour_shares_sum_to_one():
    rows = [
        {"purpose": "通勤", "flow": "降車", "bin": "～6時台", "share": 0.2},
        {"purpose": "通勤", "flow": "降車", "bin": "8時台", "share": 0.8},
        {"purpose": "通勤", "flow": "乗車", "bin": "18時台", "share": 1.0},
    ]
    got = w12.hour_shares(rows, "降車")["通勤"]
    assert sum(got) == pytest.approx(1.0)
    assert got[5] == pytest.approx(0.1) and got[6] == pytest.approx(0.1)
    assert got[8] == pytest.approx(0.8)


def test_service_day_minutes():
    assert w12._minute("05:01") == 301
    assert w12._minute("00:20") == 1460  # 終電は運行日の 24:20
    assert w12._minute("25:00") == 1500


def test_equal_interval_departures_headways():
    deps = w12.equal_interval_departures(peak_tph=20, offpeak_ratio=0.5, first_min=300, last_min=1400)
    assert deps[0] == "05:00"
    mins = [w12._minute(d) for d in deps]
    assert mins == sorted(mins)
    # ピーク(8時台)は 3分間隔・オフピーク(11時台)は 6分間隔
    peak = [m for m in mins if 480 <= m < 540]
    off = [m for m in mins if 660 <= m < 720]
    assert len(peak) == 20 and len(off) == 10
    assert w12.equal_interval_departures(0, 0.5, 300, 1400) == []


def test_equal_interval_departures_pm_peak_defaults_to_am():
    """D-W14 の本数表は朝ピークのみ=夕ピークは朝と同数に置く(明示の既定値)。"""
    am_only = w12.equal_interval_departures(20, 0.5, 300, 1400)
    same = w12.equal_interval_departures(20, 0.5, 300, 1400, peak_tph_pm=20)
    assert am_only == same
    assert w12.PM_PEAK_ASSUMED_EQUAL_TO_AM is True
    # 夕ピークを別に与えれば 17-19時だけ本数が変わる
    half = w12.equal_interval_departures(20, 0.5, 300, 1400, peak_tph_pm=10)
    mins_same = [w12._minute(d) for d in same]
    mins_half = [w12._minute(d) for d in half]
    assert len([m for m in mins_same if 1080 <= m < 1140]) == 20
    assert len([m for m in mins_half if 1080 <= m < 1140]) == 10
    # 朝ピーク(8時台)は変わらない
    assert len([m for m in mins_half if 480 <= m < 540]) == 20


def test_offpeak_ratio_from_uses_own_rows():
    """平日と土休は**別の行集合**から同じ式で比を導く(土休が平日の値を借りない)。"""
    weekday = [{"departure": f"08:{m:02d}"} for m in range(0, 60, 3)]  # 20 本/h
    weekday += [{"departure": f"{h:02d}:{m:02d}"} for h in range(10, 16) for m in range(0, 60, 6)]
    ratio_wd, peak_wd, off_wd = w12.offpeak_ratio_from(weekday)
    assert peak_wd == 20 and off_wd == 10.0 and ratio_wd == pytest.approx(0.5)
    holiday = [{"departure": f"08:{m:02d}"} for m in range(0, 60, 6)]  # 10 本/h
    holiday += [{"departure": f"{h:02d}:{m:02d}"} for h in range(10, 16) for m in range(0, 60, 6)]
    ratio_hd, peak_hd, off_hd = w12.offpeak_ratio_from(holiday)
    assert peak_hd == 10 and off_hd == 10.0 and ratio_hd == pytest.approx(1.0)
    assert ratio_hd != ratio_wd
    # 行が無ければ一様(比 1.0)
    assert w12.offpeak_ratio_from([]) == (1.0, 0, 0.0)


def test_rail_flows_uses_total_ticket_only():
    flow = [
        {"line": "山手線", "ticket": "合計", "measure": "乗車", "value": 10, "direction": "上り"},
        {"line": "山手線", "ticket": "定期券利用者テイキ", "measure": "乗車", "value": 7, "direction": "上り"},
        {"line": "山手線", "ticket": "合計", "measure": "降車", "value": 20, "direction": "上り"},
    ]
    transfer = [
        {"kind": "transfer", "from_line": "山手線", "to_line": "銀座線", "daily": 5},
        {"kind": "gate_entry", "from_line": "", "to_line": "山手線", "daily": 100},
    ]
    lines, tr_out, tr_in = w12.rail_flows(flow, transfer)
    assert lines["board"]["山手線"] == 10 and lines["alight"]["山手線"] == 20
    assert tr_out["山手線"] == 5 and tr_in["銀座線"] == 5
    assert "山手線" not in tr_in  # gate_entry は使わない


def test_node_defs_shape():
    assert len(w12.NODE_DEFS) == 10
    kinds = {d["kind"] for d in w12.NODE_DEFS}
    assert kinds == {"rail", "walk", "road"}
    assert w12.PEAK_TRAINS_PER_HOUR["湘南新宿ライン"] is None


# --- W13 -----------------------------------------------------------------------------------


@pytest.mark.parametrize(
    "date_s,sunrise,sunset",
    [
        # 東京(渋谷の世界原点 35.6595N/139.70062E)の夏至・冬至。
        # 参照値は国立天文台暦計算室が公表する東京の日の出/日の入(分単位)。
        ("2026-06-21", "04:25", "19:00"),
        ("2026-12-22", "06:47", "16:32"),
    ],
)
def test_sun_times_within_3_min_of_published_tokyo_values(date_s, sunrise, sunset):
    sr, ss = w13.sun_times(dt.date.fromisoformat(date_s))
    assert sr is not None and ss is not None
    assert abs(sr - C.hhmm_to_min(sunrise)) <= 3.0
    assert abs(ss - C.hhmm_to_min(sunset)) <= 3.0


def test_equinox_day_length_is_about_12h():
    sr, ss = w13.sun_times(dt.date(2026, 3, 20))
    assert (ss - sr) / 60.0 == pytest.approx(12.1, abs=0.15)


def test_solar_elevation_peaks_near_local_noon():
    date = dt.date(2026, 8, 1)
    elevs = [(m, w13.solar_elevation_deg(date, m)) for m in range(0, 1440, 5)]
    best = max(elevs, key=lambda t: t[1])
    assert 690 <= best[0] <= 750  # 11:30-12:30 JST
    assert w13.solar_elevation_deg(date, 0) < 0


def test_daylight_phase_vocabulary():
    sr, ss = w13.sun_times(dt.date(2026, 8, 1))
    assert w13.daylight_phase(sr - 10, sr, ss) == "夜明け前"
    assert w13.daylight_phase(sr + 10, sr, ss) == "日中"
    assert w13.daylight_phase(ss + 10, sr, ss) == "日没後"


def test_weekday_kind_holiday():
    assert w13.weekday_kind(dt.date(2026, 8, 11)) == "土休"  # 山の日(火曜)
    assert w13.weekday_kind(dt.date(2026, 8, 12)) == "平日"
    assert w13.weekday_kind(dt.date(2026, 8, 15)) == "土休"  # 土曜
    assert w13.weekday_kind(dt.date(2026, 7, 20)) == "土休"  # 海の日


def test_day_weather_type_rules():
    assert w13.day_weather_type(35.1, 0.0, 10.0, 14.0) == "猛暑"
    assert w13.day_weather_type(30.0, 1.0, 10.0, 14.0) == "雨"
    assert w13.day_weather_type(30.0, 0.0, 10.0, 14.0) == "晴"
    assert w13.day_weather_type(30.0, 0.0, 1.0, 14.0) == "曇"


def test_hour_weather_vocabulary():
    assert w13.hour_weather(1.0, 0.9, "晴") == "雨"
    assert w13.hour_weather(0.2, 0.9, "晴") == "小雨"
    assert w13.hour_weather(0.0, 0.9, "晴") == "晴"
    assert w13.hour_weather(0.0, 0.3, "晴") == "薄曇"
    assert w13.hour_weather(0.0, 0.0, "晴") == "曇"
    assert w13.hour_weather(0.0, None, "雨") == "曇"  # 夜間は日単位の型へ落とす
    assert set(w13.WEATHER_VOCAB) >= {"晴", "薄曇", "曇", "小雨", "雨"}


def test_wbgt_and_heat_stage():
    hot = w13.wbgt_estimate(35.0, 70.0, 1.0, 0.8)
    mild = w13.wbgt_estimate(20.0, 50.0, 1.0, 0.0)
    assert hot > mild
    assert w13.heat_stage(20.9) == 0 and w13.heat_stage(21.0) == 1
    assert w13.heat_stage(31.0) == 4
    assert len(w13.HEAT_VOCAB) == len(w13.HEAT_BOUNDS) + 1


def test_select_day_deterministic():
    strata = {"平日|晴": ["2026-08-03", "2026-08-04", "2026-08-05"], "土休|雨": ["2026-08-08"]}
    a = w13.select_day(12345, "平日|晴", strata)
    b = w13.select_day(12345, "平日|晴", strata)
    assert a == b and a in strata["平日|晴"]
    assert w13.select_day("run-7", "土休|雨", strata) == "2026-08-08"
    # 層が違えば別の列(同じ seed でも独立)
    assert w13.select_day(12345, "土休|雨", strata) == "2026-08-08"
    with pytest.raises(KeyError):
        w13.select_day(1, "存在しない層", strata)


def test_select_day_varies_with_seed():
    strata = {"平日|晴": [f"2026-08-{d:02d}" for d in range(1, 21)]}
    picks = {w13.select_day(s, "平日|晴", strata) for s in range(30)}
    assert len(picks) > 1


# --- build.run --------------------------------------------------------------------------------


def test_stage_order_is_numeric():
    assert build_run.stage_order(["W11", "W7", "W10", "W2"]) == ["W2", "W7", "W10", "W11"]
    # build_hash の順 = W 番号順(可視性 W8/W9 は番号どおり W7 と W10 の間に入る)
    assert build_run.ALL_STAGES == (
        "W0",
        "W1",
        "W2",
        "W3",
        "W4",
        "W5",
        "W6",
        "W7",
        "W8",
        "W9",
        "W10",
        "W11",
        "W12",
        "W13",
        "W14",
        "W15",
        "W16",
        "W17",
        "W18",
        "W19",
        "W20",
    )


def _fake_header(out: Path, stage: str, sha: str) -> None:
    """ヘッダ1枚(manifest 組み立てに要る最小の形)。"""
    C.write_json(
        out,
        f"{stage}.header.json",
        {
            "stage": stage,
            "stage_version": "0.0.0",
            "input_hash": "",
            "param_hash": "",
            "params": {},
            "outputs": [{"path": f"{stage.lower()}.parquet", "sha256": sha, "bytes": 1, "rows": 1}],
            "gates": {},
            "catalog_classes": [],
            "expedients": [],
            "notes": {},
        },
    )


def test_partial_run_does_not_touch_build_manifest(tmp_path):
    """一部段階だけのランは build_manifest.json を書き換えず partial を書く。"""
    ctx = C.Ctx(data=tmp_path, out=tmp_path / "out")
    ctx.out.mkdir(parents=True)
    for stage in build_run.ALL_STAGES:
        _fake_header(ctx.out, stage, "a" * 64)
    full = build_run.write_build_manifest(ctx, stages_run=list(build_run.ALL_STAGES))
    assert "partial" not in full
    assert (ctx.out / build_run.MANIFEST_NAME).exists()
    assert not (ctx.out / build_run.PARTIAL_MANIFEST_NAME).exists()
    canon = (ctx.out / build_run.MANIFEST_NAME).read_bytes()

    # W7 だけ作り直した(=残りのヘッダは前回のランの残り)
    _fake_header(ctx.out, "W7", "b" * 64)
    part = build_run.write_build_manifest(ctx, stages_run=["W7"])
    assert part["partial"] is True
    assert part["stages_run"] == ["W7"]
    assert part["stages_from_previous_runs"] == [s for s in build_run.ALL_STAGES if s != "W7"]
    assert part["build_hash"] != full["build_hash"]
    assert "partial_note" in part
    # 正典の manifest は**触られていない**
    assert (ctx.out / build_run.MANIFEST_NAME).read_bytes() == canon
    written = C.load_json(ctx.out / build_run.PARTIAL_MANIFEST_NAME)
    assert written["partial"] is True and written["stages_run"] == ["W7"]

    # 全段階を渡し直せば正典が更新され、partial の値と一致する
    full2 = build_run.write_build_manifest(ctx, stages_run=list(build_run.ALL_STAGES))
    assert "partial" not in full2
    assert full2["build_hash"] == part["build_hash"]
    assert (ctx.out / build_run.MANIFEST_NAME).read_bytes() != canon


def test_write_build_manifest_without_stages_run_is_full(tmp_path):
    """既定(stages_run=None)は「全段階を走らせた」= 従来どおり build_manifest.json。"""
    ctx = C.Ctx(data=tmp_path, out=tmp_path / "out")
    ctx.out.mkdir(parents=True)
    for stage in ("W0", "W1"):
        _fake_header(ctx.out, stage, "c" * 64)
    manifest = build_run.write_build_manifest(ctx)
    assert "partial" not in manifest
    assert manifest["stage_order"] == ["W0", "W1"]
    assert (ctx.out / build_run.MANIFEST_NAME).exists()
    assert not (ctx.out / build_run.PARTIAL_MANIFEST_NAME).exists()
    # **実行順**は別: W8/W9 は W10 の街路格子と W11 の駅出口を入力にするので W13 の後。
    # W16(母集団合成)はさらにその後(監査 W18-W20 の直前)。
    order = list(build_run.RUN_ORDER)
    assert build_run.RUN_ORDER[-3:] == ("W18", "W19", "W20")
    assert order.index("W8") > order.index("W13")
    assert order.index("W9") > order.index("W8")
    assert order.index("W13") < order.index("W16") < order.index("W18")

    assert set(build_run.RUN_ORDER) == set(build_run.ALL_STAGES)


def test_db_helpers():
    assert C.db_sum([80.0, 80.0]) == pytest.approx(83.0103, abs=1e-3)
    assert C.db_sum([]) == pytest.approx(-300.0)
    assert C.db_from_power(C.power_from_db(63.5)) == pytest.approx(63.5)
