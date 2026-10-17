# -*- coding: utf-8 -*-
"""tools/instruments/anchor_gauge.py(第 2 期 2-0・較正側の錨の計器)の試験。

- 合成の小さな記録(6 体 × 1,440 刻み)で 4 つの量が決定的に出る(手で数えた値と合う)。
- v1.4 の母集団(is_foreign と 20 歳未満)・1 日単位の 30 分(合計=本則/連続=腕)・時間帯の θ・24〜28 時の代え方・
  拡大係数 ω の単体。
- 許可の一覧の外は開く前に落ちる(負の対照=kddi_la の道筋を渡す)・監査フック。
- ``--compare`` の差の表。
- 実データ(``requires_data("world_v2", "realworld:…time_dist_12.json")``)は構築側の錨の値と許可の一覧の読みだけ。
  5,000 体の 2 腕は ``slow``。
"""
from __future__ import annotations

import importlib.util
import json
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[2]
_DIR = ROOT / "tools" / "instruments"


def _load(name: str):
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, _DIR / f"{name}.py")
    m = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = m
    spec.loader.exec_module(m)
    return m


@pytest.fixture(scope="module")
def G():
    return _load("anchor_gauge")


@pytest.fixture(scope="module")
def RG():
    _load("anchor_gauge")
    return sys.modules["read_guard"]


T = 1440
CORE9 = ["道玄坂一丁目", "道玄坂二丁目", "宇田川町", "神南一丁目", "桜丘町", "渋谷一丁目", "渋谷二丁目", "渋谷三丁目",
         "神宮前六丁目"]


# ---------------------------------------------------------------------- 合成の入力
def _syn_static(G, tmp_path: Path):
    """6 セル(エリア 0..4 と外)・W16 は標本の 2 倍(ω=2)・W12 は 2 ノード。"""
    kinds = [0, 3, 1, 2, 7, 5]
    w16 = {
        "agent_id": np.arange(12),
        "kind": np.asarray(kinds * 2, dtype=np.int8),
        "age": np.asarray([30, 40, 25, 50, 30, 19] * 2),
        "is_foreign": np.asarray([False, False, False, False, True, False] * 2),
        "home_cell": np.asarray([-1, 0, -1, 1, -1, -1] * 2),
        "work_cell": np.asarray([0, -1, -1, 2, -1, -1] * 2),
        "school_cell": np.asarray([-1, -1, -1, -1, -1, 3] * 2),
        "direction_node": np.asarray([0, -1, 1, -1, 0, 0] * 2),
        "chome_key": np.asarray(["", "K1", "", "KX", "", ""] * 2, dtype=object),
    }
    chome = {"key_code": np.asarray([f"K{i + 1}" for i in range(9)] + ["KX"], dtype=object),
             "s_name": np.asarray(CORE9 + ["その他"], dtype=object)}
    nodes = {"node_id": np.asarray(["n_rail_a", "n_walk"], dtype=object), "kind": np.asarray(["rail", "walk"], dtype=object),
             "daily_inflow": np.asarray([300.0, 100.0]), "daily_outflow": np.asarray([250.0, 80.0])}
    weights = {"node_id": np.asarray(["n_rail_a", "n_rail_a", "n_walk"], dtype=object),
               "hour": np.asarray([8, 18, 10]), "weight": np.asarray([0.6, 0.15, 0.25])}
    td = {"data": [{"purpose": "帰宅", "flow": "乗車", "bin": b, "share": v}
                   for b, v in (("～6時台", 0.1), ("8時台", 0.2), ("18時台", 0.6), ("0時台～", 0.1))]
          + [{"purpose": "合計", "flow": "乗車", "bin": "8時台", "share": 1.0}]}
    rates = [[0] * 96, [0] * 32 + [6000] * 40 + [0] * 24]  # 仕事(05)= 8:00〜17:59 に 60%
    ssb = {"activity_codes": ["01", "05"], "age_total_code": "00",
           "tables": {"weekday": {"03": {"1-1": {"00": {"pop_k": 1, "rates": rates}},
                                         "2-1": {"00": {"pop_k": 1, "rates": rates}}}}}}
    aoc = np.asarray([0, 1, 2, 3, 4, -1], dtype=np.int64)
    return G.Static(
        area_of_cell=aoc, cell_ix=np.arange(6), cell_iy=np.zeros(6, dtype=np.int64),
        place_ids=[f"g{i}_0_GL" for i in range(6)], area_meta={}, w16=w16, chome=chome, nodes=nodes,
        weights=weights, time_dist=td, commute={}, ssb=ssb,
        calib={"core9": {"chome_names": CORE9, "day_night_ratio": {"value": 14.8}}},
        pool_root=tmp_path / "nopool", dilated={"+0m": aoc.copy()},
    )


def _stay(cells, transit, i, lo, hi, cell):
    cells[lo:hi, i] = cell
    transit[lo:hi, i] = 0


def _syn_journal(G):
    """6 体 × 1,440 刻み。0=通勤(セル 0 で 9〜18 時)・1=住民(セル 0 で終日)・2=来街(セル 0 で 11〜12 時)・
    3=舞台内勤務(自宅セル 1・職場セル 2 で 10〜17 時)・4=訪日(セル 0 で 13〜14 時)・5=通学 19 歳(セル 3 で 8:30〜15 時)。"""
    n = 6
    cells = np.full((T, n), -1, dtype=np.int16)
    transit = np.full((T, n), 2, dtype=np.int8)
    _stay(cells, transit, 0, 480, 540, 5)       # 8:00 着(セル 5=エリア外)
    _stay(cells, transit, 0, 540, 1080, 0)      # 9:00〜18:00 職場
    _stay(cells, transit, 1, 0, T, 0)           # 住民=終日
    _stay(cells, transit, 2, 660, 720, 0)       # 来街 11:00〜12:00
    _stay(cells, transit, 3, 0, 570, 1)         # 自宅
    _stay(cells, transit, 3, 570, 600, 5)
    _stay(cells, transit, 3, 600, 1020, 2)      # 職場 10:00〜17:00
    _stay(cells, transit, 3, 1020, T, 1)
    _stay(cells, transit, 4, 780, 840, 0)       # 訪日 13:00〜14:00
    _stay(cells, transit, 5, 510, 900, 3)       # 通学 8:30〜15:00
    plan = np.full((T, n), -1, dtype=np.int16)
    plan[540:1080, 0] = 0
    plan[:, 1] = 0
    plan[660:720, 2] = -2                       # 来街の行=セル不明
    plan[0:540, 3] = 1
    plan[540:1020, 3] = 2
    plan[1020:, 3] = 1
    meta = {"schema": G.JOURNAL_SCHEMA, "arm": "syn", "tick_seconds": 60, "plan": {"day_index": 0},
            "final_hash": "0" * 16, "llm_calls": 0}
    kind = np.asarray([0, 3, 1, 2, 7, 5], dtype=np.int8)
    return {
        "ticks": np.arange(T), "cells": cells, "transit": transit, "kind": kind,
        "plan_cells": plan, "plan_work_start": np.asarray([540, -1, -1, 540, -1, -1], dtype=np.int32),
        "plan_arrive_tick": np.asarray([470, 650], dtype=np.int32), "plan_arrive_agent": np.asarray([0, 2], dtype=np.int32),
        "pop_source_agent_id": np.arange(n), "pop_kind": kind, "pop_age": np.asarray([30, 40, 25, 50, 30, 19]),
        "pop_is_foreign": np.asarray([False, False, False, False, True, False]),
        "pop_home_cell": np.asarray([-1, 0, -1, 1, -1, -1]), "pop_work_cell": np.asarray([0, -1, -1, 2, -1, -1]),
        "pop_school_cell": np.asarray([-1, -1, -1, -1, -1, 3]), "pop_direction_node": np.asarray([0, -1, 1, -1, 0, 0]),
        "pop_pool_layer": np.zeros(n, dtype=np.int8), "pop_pool_index": np.full(n, -1),
        "meta": meta,
    }


# ---------------------------------------------------------------------- 単体
def test_population_masks_use_is_foreign_and_age(G):
    pm = G.population_masks(np.asarray([1, 1, 7, 0]), np.asarray([30, 30, 30, 19]),
                            np.asarray([True, False, True, False]))
    assert pm["P_prime"].tolist() == [False, True, False, False]   # 業務来街の訪日(kind 1)も落ちる
    assert pm["P"].tolist() == [True, True, False, False]          # kind≠7 だけでは訪日の kind 1 が残る(R-115 §5 主張 1)
    assert pm["all"].all()


def test_expansion_factors_restore_kind_mix(G):
    full = np.asarray([0] * 90 + [8] * 10)
    samp = np.asarray([0] * 9 + [8] * 5)
    w = G.expansion_factors(full, samp)
    assert w[:9].tolist() == [10.0] * 9 and w[9:].tolist() == [2.0] * 5
    assert G.expansion_factors(np.asarray([0, 1]), np.asarray([0]))[0] == 2.0 / 1.0 * 0.5  # 種別 0 の N=1/n=1 → 1.0


def test_daily_dwell_sum_vs_continuous(G):
    n = 3
    area = np.full((T, n), -1, dtype=np.int8)
    area[600:620, 0] = 0
    area[700:720, 0] = 0          # 合計 40 分・連続 20 分
    area[600:629, 1] = 0          # 29 分
    area[600:630, 2] = 0          # 連続 30 分
    stage = area >= 0
    hm, best = G.hour_minutes(area, stage, np.arange(T))
    s = G.daily_qualified(hm, best, "sum")[0]
    c = G.daily_qualified(hm, best, "cont")[0]
    assert s.tolist() == [True, False, True]
    assert c.tolist() == [False, False, True]


def test_presence_theta_and_hour_axis_24_to_28(G):
    n = 2
    area = np.full((T, n), -1, dtype=np.int8)
    area[9 * 60 + 50:10 * 60 + 40, 0] = 1       # 9 時に 10 分・10 時に 40 分
    area[2 * 60:3 * 60, 1] = 1                  # 2 時台(=KDDI の 26 時)に 60 分
    stage = area >= 0
    hm, best = G.hour_minutes(area, stage, np.arange(T))
    q = G.daily_qualified(hm, best, "sum")
    w = np.ones(n)
    keep = np.ones(n, dtype=bool)
    n1 = G.presence_hourly(hm, q, w, keep, 1)[1]
    n30 = G.presence_hourly(hm, q, w, keep, 30)[1]
    hours = list(G.KDDI_HOURS)
    assert n1[hours.index(9)] == 1 and n1[hours.index(10)] == 1
    assert n30[hours.index(9)] == 0 and n30[hours.index(10)] == 1
    assert n1[hours.index(26)] == 1 and hours[-1] == 28 and len(hours) == 24   # 24〜28 時=同じ日の 0〜4 時
    assert G.peak_hour(n30) in (10, 26)


def test_ratio_block_area_attribute_and_foreign_column(G):
    q = np.zeros((len(G.COLS), 4), dtype=bool)
    q[0] = True
    att = G.attr_by_area(np.asarray([0, -1, -1, -1]), np.asarray([-1, 0, -1, -1]), np.asarray([-1, -1, -1, -1]))
    w = np.asarray([1.0, 2.0, 3.0, 5.0])
    keep = np.asarray([True, True, True, False])
    fo = np.asarray([False, False, False, True])
    r = G.ratio_block(q, att, w, keep, fo)["central"]
    assert (r["Res"], r["W"], r["V"]) == (1.0, 2.0, 3.0)
    assert r["V_per_Res"] == 3.0 and r["W_per_Res"] == 2.0 and r["foreign"] == 5.0


def test_arrivals_table_counts_transitions_by_direction(G):
    n = 3
    tr = np.full((T, n), 2, dtype=np.int8)
    tr[0:, 0] = 0                                # 0 時から舞台=到着に数えない
    tr[480:, 1] = 0                              # 8:00 に着く(方面 1)
    tr[600:, 2] = 1
    tr[601:, 2] = 0                              # 乗車 → 舞台(方面なし)
    tab, n_arr = G.arrivals_table(tr, np.arange(T), np.asarray([0, 1, -1]), np.ones(n), 2)
    hours = list(G.KDDI_HOURS)
    assert n_arr == 2
    assert tab[1, hours.index(8)] == 1 and tab[2, hours.index(10)] == 1 and tab[0].sum() == 0


def test_first_work_run_skips_overnight_and_short(G):
    cells = np.full((T, 1), -1, dtype=np.int16)
    cells[0:60, 0] = 7                            # 0 時から続く=前日の続き
    cells[490:510, 0] = 7                         # 20 分=足りない
    cells[540:600, 0] = 7                         # 9:00 から 60 分
    found, rate = G.first_work_run(cells, cells >= 0, np.asarray([7]), np.arange(T))
    assert found.tolist() == [540]
    assert rate.shape == (96, 1) and rate[36, 0] == 1.0


def test_dist_stats_weighted(G):
    st = G.dist_stats(np.asarray([480, 540, 600]), np.asarray([1.0, 2.0, 1.0]))
    assert st["mean"] == 540.0 and st["p50"] == "9:00" and st["mode_bin"] == "9:00"
    assert st["on_00_30"] == 1.0 and abs(sum(st["hist15"]) - 1.0) < 1e-9


def test_time_dist_open_bins_follow_w12(G):
    td = {"data": [{"purpose": "合計", "flow": "乗車", "bin": b, "share": v}
                   for b, v in (("～6時台", 0.2), ("7時台", 0.5), ("0時台～", 0.3))]}
    s = G.time_dist_shape(td, "合計", "乗車")
    h = list(G.KDDI_HOURS)
    assert s[h.index(5)] == pytest.approx(0.1) and s[h.index(6)] == pytest.approx(0.1)
    assert s[h.index(24)] == pytest.approx(0.15) and s[h.index(25)] == pytest.approx(0.15)


def test_rise_slot(G):
    c = np.zeros(96)
    c[30:40] = np.linspace(0.1, 0.8, 10)
    assert G.rise_slot(c) == 30 + int(np.flatnonzero(np.linspace(0.1, 0.8, 10) >= 0.4)[0])
    assert G.rise_slot(np.zeros(96)) is None


# ---------------------------------------------------------------------- 4 つの量(合成の記録)
def test_four_quantities_deterministic_on_synthetic_record(G, RG, tmp_path):
    S = _syn_static(G, tmp_path)
    J = _syn_journal(G)
    guard = RG.ReadGuard(dirs={"pool": tmp_path / "nopool"}, protect=[tmp_path])
    a = G.gauge_arm(J, S, guard)
    b = G.gauge_arm(_syn_journal(G), _syn_static(G, tmp_path), guard)
    dump = lambda d: G._jdump(G._strip_arrays(d))  # noqa: E731
    assert dump(a) == dump(b)
    # ω=2(W16 は標本の 2 倍)
    assert set(a["weights"]["omega_by_kind"].values()) == {2.0}
    # 3-1: central は 0・1・2 が 11 時に重なる(訪日 4 と 19 歳の 5 は P′ の外)
    m31 = a["3-1"]["arms"]["sim/sum/theta1"]
    assert m31["peak"]["central"] == 11
    assert a["3-1"]["a2_w12"]["peak"] == 10 and a["3-1"]["a2_w12"]["R"] == 4.0     # β=帰宅(本則)
    assert a["3-1"]["a2_w12"]["arm_beta_total"]["peak"] == 18                       # β=合計(腕)
    assert a["3-1"]["a3_pt_c2"]["value"] is None
    # 3-2: central の W・Res・V は ω=2 で 2・2・2・訪日の列は 2
    c = a["3-2"]["arms"]["sim/sum/area"]["central"]
    assert (c["W"], c["Res"], c["V"], c["foreign"]) == (2.0, 2.0, 2.0, 2.0)
    assert c["V_per_Res"] == 1.0 and c["W_per_Res"] == 1.0
    assert a["3-2"]["plan_unknown_cell_share"]["visitor_kinds"] == 1.0
    assert a["3-2"]["arms"]["plan/sum/area"]["total"]["V_per_Res"] is None   # 計画の来街はセル不明=空
    core = a["3-2"]["a3_core9"]
    assert core["w16_static"]["ratio"] == 2.0 and core["run"]["ratio"] == 2.0
    # 3-3: 方面 0 は 8 時(0)・8:30(5)・13 時(4)、方面 1 は 11 時(2)
    n0 = a["3-3"]["nodes"]["n_rail_a"]
    assert n0["sim_share"] == 0.75 and n0["sim_peak"] == 8 and n0["a1_share"] == 0.75 and n0["a2_peak"] == 8
    assert a["3-3"]["a4_grey"]["value"] is None
    # 3-4: 対象は 0(9:00)と 3(10:00)・計画の勤務の行は 9:00・立ち上がり 8:00(第 8-1 表)
    s34 = a["3-4"]
    assert s34["n_targets"] == 2 and s34["sim"]["mean_hm"] == "9:30" and s34["a2_w17_work_row"]["mean_hm"] == "9:00"
    assert s34["a3_ssb_8_1"]["rise"] == "8:00"
    assert s34["a1_r31_lead"]["mean"] is None and "プールが無い" in s34["a1_r31_lead"]["status"]
    assert s34["diff_vs_a2"]["mean_min"] == 30.0


def test_duty_open_anchor_matches_w17_v2_draw(G, RG, tmp_path):
    """錨 1 は W17 v2 の勤務窓(trial.draw_windows=第 31 表の逆関数法+arrival_lead)と同じ値。"""
    from shibuya.build.sched import trial as TR

    pool = tmp_path / "pool"
    (pool / "L4").mkdir(parents=True)
    lines = [{"employment": "正規", "arrival_lead_min": 40, "occupation": "会社員"},
             {"employment": "正規", "occupation": "会社員"}]
    (pool / "L4" / "part-0000.jsonl").write_text("\n".join(json.dumps(x, ensure_ascii=False) for x in lines) + "\n",
                                                 encoding="utf-8")
    bins = [{"label": f"{h}:00", "start_min": h * 60, "width_min": 60} for h in (7, 8, 9)]
    commute = {"depart": {"bins": bins, "rows": {"正規の職員・従業員": {"share": [0.2, 0.5, 0.3], "actor_rate": 1.0}}},
               "return": {"bins": [{"label": "18:00", "start_min": 1080, "width_min": 60}],
                          "rows": {"正規の職員・従業員": {"share": [1.0], "actor_rate": 1.0}}},
               "employment_mix": {"正規": {"正規の職員・従業員": 1.0}}}
    S = _syn_static(G, tmp_path)
    S.pool_root = pool
    S.commute = commute
    J = _syn_journal(G)
    J["pop_pool_layer"] = np.asarray([4, 0, 0, 4, 0, 0], dtype=np.int8)
    J["pop_pool_index"] = np.asarray([0, -1, -1, 1, -1, -1])
    targets = np.asarray([True, False, False, True, False, False])
    guard = RG.ReadGuard(dirs={"pool": pool}, protect=[tmp_path])
    with guard.active():
        got = G.duty_open_anchor(J, targets, S, guard)
    bt = TR._bin_table(commute["depart"], "正規の職員・従業員")
    want0 = TR.inverse_sample(bt, TR.u01("depart", 0)) + 40
    want3 = TR.inverse_sample(bt, TR.u01("depart", 3)) + TR.LEAD_DEFAULT_MIN   # lead 欠損=30 分
    assert got["duty_open"][0] == want0 and got["duty_open"][3] == want3
    assert got["n_window"] == 2 and got["counters"]["lead_default"] == 1
    assert [r["role"] for r in guard.log] == ["pool"]


# ---------------------------------------------------------------------- 許可の一覧
def test_guard_rejects_sealed_path_before_reading(RG, tmp_path):
    sealed = tmp_path / "realworld" / "kddi_la" / "stay.csv"
    sealed.parent.mkdir(parents=True)
    sealed.write_text("x", encoding="utf-8")
    ok = tmp_path / "ok.json"
    ok.write_text("{}", encoding="utf-8")
    g = RG.ReadGuard(files={"ok": ok}, protect=[tmp_path])
    with pytest.raises(RG.SealedPathError):
        g.check(sealed)
    with pytest.raises(RG.SealedPathError):
        g.read_bytes(sealed)
    assert g.log == []
    # 許可の一覧そのものに封印の道筋を入れると、組んだ時点で落ちる(負の対照)
    with pytest.raises(RG.SealedPathError):
        RG.ReadGuard(files={"x": sealed})
    with pytest.raises(RG.SealedPathError):
        RG.ReadGuard(dirs={"x": tmp_path / "shibuya_jinryu"})


def test_guard_rejects_unlisted_and_audit_hook(RG, tmp_path):
    root = tmp_path / "data"
    root.mkdir()
    listed = root / "a.json"
    other = root / "b.json"
    listed.write_text("{}", encoding="utf-8")
    other.write_text("{}", encoding="utf-8")
    jin = tmp_path / "shibuya_jinryu" / "c.json"
    jin.parent.mkdir()
    jin.write_text("{}", encoding="utf-8")
    g = RG.ReadGuard(files={"a": listed}, protect=[root])
    assert g.read_json(listed) == {}
    with pytest.raises(RG.NotAllowedError):
        g.read_json(other)
    with g.active():
        with pytest.raises(RG.NotAllowedError):
            open(other, "rb")                       # 読み口を通らない open も守る根の下では落ちる
        with pytest.raises(RG.SealedPathError):
            open(jin, "rb")                         # 封印の語は根の外でも落ちる
        with open(listed, "rb") as fh:              # 一覧の中は開ける
            assert fh.read() == b"{}"
    with open(other, "rb") as fh:                   # 守りの外では何もしない(フックは空)
        assert fh.read() == b"{}"
    assert [r["role"] for r in g.log] == ["a"]


def test_make_guard_rejects_sealed_and_renamed_inputs(G, RG, tmp_path, monkeypatch):
    paths = G.resolve_paths()
    bad = dict(paths)
    bad["time_dist_12"] = tmp_path / "kddi_la" / "time_dist_12.json"
    with pytest.raises(RG.SealedPathError):
        G.make_guard(bad)
    bad = dict(paths)
    bad["time_dist_12"] = tmp_path / "station_flow_12.json"   # 〔灰〕の内訳を持つファイル
    with pytest.raises((RG.SealedPathError, RG.NotAllowedError)):
        G.make_guard(bad)
    bad = dict(paths)
    bad["commute_r3"] = tmp_path / "other.json"                # 名の違うファイルは差し込めない
    with pytest.raises(RG.NotAllowedError):
        G.make_guard(bad)
    g = G.make_guard(paths)

    def _no_fs(p):  # 検収 L8: 生の道筋で語が当たれば realpath(=ファイルシステム)に触らない
        raise AssertionError(f"realpath を取った: {p}")

    monkeypatch.setattr(RG, "_real", _no_fs)
    for tok in ("presence_anchors_v0.json", "diversity_anchors_v0.json", "hunger_energy_anchors_v0.json",
                "presence_validation_anchors_v0.json", "hunger_energy_validation_anchors_v0.json",  # 〔2-4 V6〕分けた検証側
                "diversity_validation_anchors_v0.json"):  # 〔第337〕分けた検証側
        with pytest.raises(RG.SealedPathError):
            g.check(ROOT / "docs" / "bench" / "anchors" / tok)
    with pytest.raises(RG.SealedPathError):
        g.check(ROOT / "data" / "realworld" / "boundary_counts.json")
    with pytest.raises(RG.SealedPathError):
        g.check(ROOT / "data" / "calib" / "pt2018" / "pt6_c-2.csv")
    with pytest.raises(RG.SealedPathError):  # 〔第337〕v1 の頃の ODPT リアルタイムの置き場
        g.check(ROOT / "data" / "realworld" / "odpt_rt" / "x.json.gz")


# ---------------------------------------------------------------------- 書き出しと --compare(合成の世界)
def _write_world(tmp_path: Path, G) -> dict:
    import pyarrow as pa
    import pyarrow.parquet as pq

    S = _syn_static(G, tmp_path)
    world = tmp_path / "world"
    world.mkdir()
    pq.write_table(pa.table({"place_id": S.place_ids, "ix": S.cell_ix.astype(np.int32), "iy": S.cell_iy.astype(np.int32)}),
                   world / "w2_cells.parquet")
    pq.write_table(pa.table({k: (v.tolist() if v.dtype == object else v) for k, v in S.w16.items()}),
                   world / "w16_population.parquet")
    pq.write_table(pa.table({k: v.tolist() for k, v in S.chome.items()}), world / "w16_chome.parquet")
    pq.write_table(pa.table({k: (v.tolist() if v.dtype == object else v) for k, v in S.nodes.items()}),
                   world / "w12_external_nodes.parquet")
    pq.write_table(pa.table({k: (v.tolist() if v.dtype == object else v) for k, v in S.weights.items()}),
                   world / "w12_generation_weights.parquet")
    anc = tmp_path / "anchors"
    anc.mkdir()
    (anc / "time_dist_12.json").write_text(json.dumps(S.time_dist, ensure_ascii=False), encoding="utf-8")
    (anc / "commute_time_dist_r3.json").write_text("{}", encoding="utf-8")
    (anc / "ssb2021_activity_prior_v0.json").write_text(json.dumps(S.ssb), encoding="utf-8")
    (anc / "calib_anchors_v0.json").write_text(json.dumps(S.calib, ensure_ascii=False), encoding="utf-8")
    shutil.copyfile(ROOT / "tools" / "c7" / "area_axes_v0.json", anc / "area_axes_v0.json")
    return {"world": world, "area_axes": anc / "area_axes_v0.json", "time_dist_12": anc / "time_dist_12.json",
            "commute_r3": anc / "commute_time_dist_r3.json", "ssb_8_1": anc / "ssb2021_activity_prior_v0.json",
            "calib_anchors": anc / "calib_anchors_v0.json", "pool": tmp_path / "nopool", "records": tmp_path / "rec"}


def _write_journal(G, path: Path) -> Path:
    J = _syn_journal(G)
    meta = J.pop("meta")
    np.savez_compressed(path, **J, meta=np.asarray(json.dumps(meta, ensure_ascii=False)))
    return path


def test_gauge_writes_outputs_reads_only_listed_and_compare(G, tmp_path):
    paths = _write_world(tmp_path, G)
    jp = _write_journal(G, tmp_path / "anchor_journal_syn.npz")
    out1 = tmp_path / "rec" / "v1"
    doc = G.gauge({"syn": jp}, paths=paths, out_dir=out1)
    for name in ("anchor_gauge.json", "anchor_gauge.md"):
        assert (out1 / name).is_file()
    roles = {r["role"] for r in doc["inputs_read"]}
    assert roles <= set(doc["allow_list"]) | {"journal"}
    assert {"W16", "W2_cells", "W12_nodes", "W12_weights", "time_dist_12", "ssb_8_1", "calib_anchors",
            "journal"} <= roles
    for sec in ("3-1", "3-2", "3-3", "3-4"):
        assert sec in doc["arms"]["syn"]
    text = (out1 / "anchor_gauge.md").read_text(encoding="utf-8")
    assert "材料待ち" in text and "読まない" in text and ":\\" not in text   # 絶対パスを書かない
    # 前の版との差: 同じ記録なら差 0・要約の値が変われば行が出る
    out2 = tmp_path / "rec" / "v2"
    doc2 = G.gauge({"syn": jp}, paths=paths, out_dir=out2, compare_dir=out1)
    assert doc2["compare"]["n_changed"] == 0 and doc2["compare"]["n_rows"] > 20
    assert (out2 / "compare_vs_v1.md").is_file()
    prev = json.loads((out1 / "anchor_gauge.json").read_text(encoding="utf-8"))
    prev["arms"]["syn"]["summary"]["3-1/sim/peak/central"] = 99
    cmp = G.compare_docs(prev, json.loads((out2 / "anchor_gauge.json").read_text(encoding="utf-8")), prev_label="x")
    changed = [r for r in cmp["rows"] if not r["same"]]
    assert [r["key"] for r in changed] == ["3-1/sim/peak/central"] and changed[0]["diff"] == 11 - 99
    assert "3-1/sim/peak/central" in G.render_compare(cmp)


def test_gauge_rejects_journal_outside_list(G, tmp_path):
    paths = _write_world(tmp_path, G)
    jp = _write_journal(G, tmp_path / "anchor_journal_syn.npz")
    bad = tmp_path / "other_record.npz"
    shutil.copyfile(jp, bad)
    sys_mod = sys.modules["read_guard"]
    with pytest.raises(sys_mod.NotAllowedError):       # 名が記録の形でない=一覧の外
        G.gauge({"syn": bad}, paths=paths, out_dir=None)
    sealed = tmp_path / "kddi_la" / "anchor_journal_syn.npz"
    sealed.parent.mkdir()
    shutil.copyfile(jp, sealed)
    with pytest.raises(sys_mod.SealedPathError):       # 封印の語の下は名が合っても落ちる
        G.gauge({"syn": sealed}, paths=paths, out_dir=None)


# ---------------------------------------------------------------------- 実データ(構築側の錨だけ)
@pytest.mark.requires_data("world_v2", "realworld:transport_census/time_dist_12.json")
def test_real_static_anchors(G):
    paths = G.resolve_paths()
    g = G.make_guard(paths)
    with g.active():
        S = G.load_static(g, paths)
        km = G.w16_static_ratios(S)["kind_map_stage"]
        assert km["P"]["V_per_Res"] == pytest.approx(2.33, abs=0.01)    # R-115 §3-2 錨 1(kind≠7 ∧ age≥20)
        assert km["P"]["W_per_Res"] == pytest.approx(5.56, abs=0.01)
        anc = G.w12_node_anchors(S)
        ids = anc["ids"]
        assert abs(anc["share"].sum() - 1.0) < 1e-12
        assert float(np.max(np.abs(anc["share"] - anc["share_from_weights"]))) < 1e-9
        rail = [i for i, n in enumerate(ids) if n.startswith("ext_rail_")]
        assert len(rail) == 8 and {G.peak_hour(anc["shape"][i]) for i in rail} == {8}
        assert G.peak_hour(anc["shape"][ids.index("ext_walk_gate")]) == 10
        core = G._core9_static(S)
        assert core["w16_static"]["night"] == 8524                       # W16 の中核 9 の居住者(被覆つき)
        assert 100 <= core["mapping"]["n_gl_cells"] <= 180               # 1.39 km² ≒ 139 枚の目安
        assert G.ssb_work_rise(S.ssb)["rise"] == "8:30"
    assert S.area_meta["area_ha_gate_ok"]
    roles = {r["role"] for r in g.log}
    assert roles == {"W16", "W16_chome", "W2_cells", "W12_nodes", "W12_weights", "area_axes", "time_dist_12",
                     "commute_r3", "ssb_8_1", "calib_anchors"}


@pytest.mark.slow
@pytest.mark.requires_data("world_v2", "persona_pool", "realworld:transport_census/time_dist_12.json")
def test_real_record_is_invariant_and_gauge_runs(G, tmp_path):
    """記録器を付けても final と呼数は同じ(エンジン不変)・2 腕の計器が 4 つの量を出す。"""
    metas = {}
    for arm in G.ARMS:
        jp = tmp_path / f"anchor_journal_{arm}.npz"
        metas[arm] = G.record(arm, out_path=jp)
        plain = G.record(arm, out_path=jp, use_recorder=False)
        assert (plain["final_hash"], plain["llm_calls"]) == (metas[arm]["final_hash"], metas[arm]["llm_calls"])
        opened = [r["path"] for r in metas[arm]["record_opened_files"]]
        assert opened and not any("kddi" in p or "jinryu" in p or "boundary_counts" in p for p in opened)
        again = G.record(arm, out_path=tmp_path / f"anchor_journal_{arm}_2.npz")
        assert again["journal_arrays_sha16"] == metas[arm]["journal_arrays_sha16"]   # 壁時計は hash に入らない
    doc = G.gauge({a: tmp_path / f"anchor_journal_{a}.npz" for a in G.ARMS}, paths=G.resolve_paths(),
                  out_dir=tmp_path / "out")
    for arm in G.ARMS:
        s = doc["arms"][arm]["summary"]
        assert s["3-1/sim/peak/total5"] in G.KDDI_HOURS
        assert s["3-4/a1/mean"] is not None and s["3-4/a3/rise"] == "8:30"


# ---------------------------------------------------------------------- 検収の直し(L4・L5・L8・L10・M1)
def test_theta_compared_in_seconds(G):
    """θ は分で受けて秒で比べる(刻みが 30 秒なら 20 刻み=10 分)。"""
    n = 1
    T2 = 2 * T
    area = np.full((T2, n), -1, dtype=np.int8)
    area[9 * 120:9 * 120 + 20, 0] = 0                  # 30 秒の刻みで 9 時に 20 刻み=10 分
    area[10 * 120:10 * 120 + 60, 0] = 0                # 10 時に 30 分(1 日の合計 40 分)
    stage = area >= 0
    hm, best = G.hour_minutes(area, stage, np.arange(T2), tick_seconds=30)
    q = G.daily_qualified(hm, best, "sum", tick_seconds=30)
    hours = list(G.KDDI_HOURS)
    n10 = G.presence_hourly(hm, q, np.ones(n), np.ones(n, dtype=bool), 10, tick_seconds=30)[0]
    n11 = G.presence_hourly(hm, q, np.ones(n), np.ones(n, dtype=bool), 11, tick_seconds=30)[0]
    assert n10[hours.index(9)] == 1 and n11[hours.index(9)] == 0 and n11[hours.index(10)] == 1


def test_deny_hit_raw_first_does_not_touch_fs(RG, monkeypatch):
    def _no_fs(p):
        raise AssertionError("realpath を取った")

    monkeypatch.setattr(RG, "_real", _no_fs)
    assert RG.deny_hit("x/realworld/kddi_la/a.csv") == "kddi"
    with pytest.raises(RG.SealedPathError):
        RG.ReadGuard(files={}, protect=[]).check("y/data/realworld_live/z.json")


def test_order_compare_ignores_separator_and_zero_change_text(G):
    a = {"arms": {"m": {"summary": {"3-1/sim/order": "central>northeast", "x": 1}, "meta": {}}}}
    b = {"arms": {"m": {"summary": {"3-1/sim/order": "central→northeast", "x": 1}, "meta": {}}}}
    cmp = G.compare_docs(a, b, prev_label="p")
    assert cmp["n_changed"] == 0
    assert "変わった値は無い" in G.render_compare(cmp)
    b["arms"]["m"]["summary"]["3-1/sim/order"] = "northeast→central"
    assert G.compare_docs(a, b)["n_changed"] == 1


def test_arrays_hash_ignores_meta_and_record_tracking(G, RG, tmp_path):
    J = _syn_journal(G)
    meta = J.pop("meta")
    h1 = G.arrays_sha16(J)
    p1 = tmp_path / "anchor_journal_a.npz"
    p2 = tmp_path / "anchor_journal_b.npz"
    np.savez_compressed(p1, **J, meta=np.asarray(json.dumps({**meta, "wall": 1.0})))
    np.savez_compressed(p2, **J, meta=np.asarray(json.dumps({**meta, "wall": 2.0, "journal_arrays_sha16": h1})))
    g = RG.ReadGuard(protect=[], repo_root=ROOT)
    a = G.load_journal(g, p1)
    b = G.load_journal(g, p2)
    assert G.arrays_sha16({k: v for k, v in a.items() if k != "meta"}) == h1
    assert [r["arrays_sha16"] for r in g.log] == [h1, h1] and g.log[0]["md5"] != g.log[1]["md5"]
    bad = dict(J)
    bad["cells"] = bad["cells"].copy()
    bad["cells"][0, 0] = 3
    p3 = tmp_path / "anchor_journal_c.npz"
    np.savez_compressed(p3, **bad, meta=np.asarray(json.dumps({**meta, "journal_arrays_sha16": h1})))
    with pytest.raises(ValueError):
        G.load_journal(g, p3)
    # ランの段の控え: 根の下の open を道筋で控え、コード(.py)は控えない
    root = tmp_path / "data"
    root.mkdir()
    (root / "w.json").write_text("{}", encoding="utf-8")
    (root / "m.py").write_text("", encoding="utf-8")
    run_guard = RG.ReadGuard.sealed_only(track_roots=[root])
    with run_guard.active():
        open(root / "w.json", "rb").close()
        open(root / "m.py", "rb").close()
        open(root / "w.json", "rb").close()
    assert run_guard.opened == ["w.json"]
    rows = {r["path"]: r["gauge_deny_token"]
            for r in G.opened_listing(["docs/bench/anchors/hunger_energy_validation_anchors_v0.json",
                                       "docs/bench/anchors/hunger_energy_build_anchors_v0.json",
                                       "data/world/v2/W0.header.json"])}
    # 〔2-4 V6〕エンジンが開く空腹の錨は構築側と検証側の 2 本=検証側にだけ印
    assert rows == {"docs/bench/anchors/hunger_energy_validation_anchors_v0.json": "hunger_energy_validation_anchors",
                    "docs/bench/anchors/hunger_energy_build_anchors_v0.json": None,
                    "data/world/v2/W0.header.json": None}
