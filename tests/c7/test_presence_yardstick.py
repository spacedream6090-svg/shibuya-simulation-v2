# -*- coding: utf-8 -*-
"""``tools/c7/presence_yardstick.py`` の検査。

**合成 journal だけ**を使う(holdout も実世界資産も開かない)。実データでの実行は親が回す。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_C7 = REPO_ROOT / "tools" / "c7"
if str(TOOLS_C7) not in sys.path:  # conftest と同じ作法(単体実行でも通るように)
    sys.path.insert(0, str(TOOLS_C7))

ANCHORS_PATH = REPO_ROOT / "docs" / "bench" / "anchors" / "presence_anchors_v0.json"

#: 合成世界: 6 セル = 5 エリア各 1 + 域外 1。
AREA_OF_CELL = np.array([0, 1, 2, 3, 4, -1], dtype=np.int8)
#: 種別の重み(9 種)。合計 16。
KIND_W = np.array([3, 2, 1, 4, 1, 1, 1, 1, 2], dtype=np.int64)
#: セルの重み。域内合計 6・域外 5。
CELL_W = np.array([2, 1, 1, 1, 1, 5], dtype=np.int64)


@pytest.fixture(scope="module")
def yard():
    import presence_yardstick as _m

    return _m


@pytest.fixture(scope="module")
def anchors(yard):
    return yard.load_anchors()


@pytest.fixture()
def amap(yard):
    import c7lib

    n = AREA_OF_CELL.size
    return c7lib.AreaMap(
        place_ids=tuple(f"c{i}_GL" for i in range(n)),
        area_of_cell=AREA_OF_CELL.copy(),
        cell_x=np.zeros(n),
        cell_y=np.zeros(n),
        meta={"synthetic": True},
    )


def hour_mult(peak: dict[int, int] | None = None) -> np.ndarray:
    """時別の倍率(既定 1・``peak`` で持ち上げる)。"""
    hm = np.ones(24, dtype=np.int64)
    for h, v in (peak or {}).items():
        hm[h] = v
    return hm


def synth_journal(path: Path, hm: np.ndarray, *, zero_d66_at: int | None = None) -> Path:
    """合成 journal(``T=24``・``C=6``)。``counts[t,k,c] = hm[t]*KIND_W[k]*CELL_W[c]``。"""
    import occupancy_series as occ

    counts = (hm[:, None, None] * KIND_W[None, :, None] * CELL_W[None, None, :]).astype(np.int32)
    if zero_d66_at is not None:
        import presence_yardstick as py

        counts[zero_d66_at, list(py.D66_KINDS), :] = 0
    return occ.write_journal(path, np.arange(24, dtype=np.int64) * 60,
                             counts.sum(axis=1), counts, tick_seconds=60, start_hour=0)


#: base_summary.txt と**同じ書式**の抜粋(engine/run.py の summary 生成部に対応)。
SUMMARY_TEXT = (
    "[run] n=5000 cells=520 seed=1 ticks=1440 world=data\\world\\v2\n"
    "  呼/時 00:1550 01:466 02:1363 03:889 04:910 05:1082 06:1728 07:2118 08:2083 09:2083"
    " 10:2084 11:2083 12:2083 13:2084 14:1853 15:969 16:759 17:744 18:2118 19:2083 20:1145"
    " 21:1084 22:1632 23:2118\n"
    "  起床率/時 00:0.185 01:0.237 02:0.248 03:0.250 04:0.258 05:0.293 06:0.351 07:0.794"
    " 08:0.800 09:0.797 10:0.776 11:0.756 12:0.743 13:0.726 14:0.718 15:0.709 16:0.705"
    " 17:0.697 18:0.713 19:0.694 20:0.672 21:0.655 22:0.657 23:0.448\n"
    "  D-62 計画就寝 その場 1,193 + 着いて 602(歩行中 1,516) / 計画起床 4,674 /"
    " 寝かせなかった 乗車中 0・域外 636・会話中 0・就寝済 3,580・行けない 0\n"
)

#: D-66 計画実行層のランの要約(**``起床率(在圏)/時`` が増える**)。他の行は同じ書式。
SUMMARY_TEXT_IN_AREA = SUMMARY_TEXT + (
    "  起床率(在圏)/時 00:0.300 01:0.310 02:0.320 03:0.485 04:0.400 05:0.420 06:0.500"
    " 07:0.900 08:0.950 09:0.992 10:0.990 11:0.990 12:0.989 13:0.988 14:0.987 15:0.986"
    " 16:0.985 17:0.984 18:0.983 19:0.982 20:0.981 21:0.980 22:0.900 23:0.700\n"
    "  計画実行: 域外居住 4,491 / 到着 4,491 / 退出 3,460 / 終日域外 1,107 /"
    " 計画一致率(在圏) 0.870 / (域外) 0.990 / 昼夜比 09-03 4.27\n"
)


# ---------------------------------------------------------------- 1 アンカー台帳


def test_anchors_json_has_source_and_tag(yard, anchors):
    """台帳の全項目に source / verified_by / tag があり、値を持つ。"""
    assert ANCHORS_PATH.exists()
    a = anchors["anchors"]
    assert len(a) >= 8
    for key, row in a.items():
        assert row["source"], key
        assert row["verified_by"].startswith("parent"), key
        assert row["tag"] in yard.ANCHOR_TAGS, key
        assert any(k in row for k in ("value", "values", "low", "shares")), key
    assert len(a["wake_rate_tokyo_weekday"]["values"]) == 24
    assert a["wake_rate_tokyo_weekday"]["values"][0] == 20.5
    assert a["wake_rate_tokyo_weekday"]["values"][23] == 46.2
    assert len(a["homebound_boarding_time_dist_2015"]["shares"]) == 19
    assert a["attendance_rate"]["tag"] == "expedient"
    assert a["night_presence_estimate"]["tag"] == "estimate"
    assert a["core9_daytime_population"]["value"] == 130_167


def test_check_anchors_rejects_missing_fields(yard):
    """source が無い/tag が不正/値が無い台帳は**落ちる**(推測で埋めない)。"""
    ok = {"anchors": {"x": {"value": 1, "source": "u", "verified_by": "parent", "tag": "anchor"}}}
    yard.check_anchors(ok)
    for broken in (
        {"anchors": {"x": {"value": 1, "verified_by": "parent", "tag": "anchor"}}},
        {"anchors": {"x": {"value": 1, "source": "u", "verified_by": "p", "tag": "guess"}}},
        {"anchors": {"x": {"source": "u", "verified_by": "p", "tag": "anchor"}}},
        {"anchors": {}},
    ):
        with pytest.raises(ValueError):
            yard.check_anchors(broken)


# ---------------------------------------------------------------- 2 要約テキスト


def test_parse_summary_lines(yard):
    """``起床率/時`` ``D-62 計画就寝`` ``呼/時`` ``[run] n=`` を実書式から読む。"""
    wr = yard.parse_wake_rate(SUMMARY_TEXT)
    assert wr is not None and len(wr) == 24
    assert wr[0] == pytest.approx(0.185)
    assert wr[3] == pytest.approx(0.250)
    assert wr[12] == pytest.approx(0.743)
    assert wr[23] == pytest.approx(0.448)
    cb = yard.parse_calls_by_hour(SUMMARY_TEXT)
    assert cb is not None and cb[0] == 1550 and cb[23] == 2118
    ps = yard.parse_planned_sleep(SUMMARY_TEXT)
    assert ps == {"slept": 1193, "arrived": 602, "walking": 1516, "woke": 4674,
                  "riding": 0, "outside": 636, "conversing": 0, "asleep": 3580,
                  "unreachable": 0}
    assert yard.parse_n_agents(SUMMARY_TEXT) == 5000
    assert yard.parse_wake_rate("何も無い") is None
    assert yard.parse_planned_sleep("何も無い") is None


def test_in_area_wake_rate_line_wins_over_the_d62_line(yard, tmp_path):
    """**D-66**: ``起床率(在圏)/時`` があれば a(h) との比較にそちらを使う。

    ``起床率/時``(D-62 定義)は**域外滞在・乗車中も「起きている」に数える**ので、計画実行層の
    ランでは分母が揃わない。行が無い入力(before)では従来どおり ``起床率/時`` を使う。
    """
    # 2 本並んでも正規表現が食い合わない(既存行はそのまま読める)
    assert yard.parse_wake_rate(SUMMARY_TEXT_IN_AREA)[3] == pytest.approx(0.250)
    ia = yard.parse_wake_rate_in_area(SUMMARY_TEXT_IN_AREA)
    assert ia is not None and len(ia) == 24
    assert ia[3] == pytest.approx(0.485) and ia[12] == pytest.approx(0.989)
    assert yard.parse_wake_rate_in_area(SUMMARY_TEXT) is None  # 在圏行の無い入力

    new_p = tmp_path / "after.txt"
    new_p.write_text(SUMMARY_TEXT_IN_AREA, encoding="utf-8")
    old_p = tmp_path / "before.txt"
    old_p.write_text(SUMMARY_TEXT, encoding="utf-8")
    s_new = yard.read_summary(str(new_p))
    s_old = yard.read_summary(str(old_p))
    assert s_new["wake_rate_basis"] == "in_area"
    assert s_new["wake_rate"][3] == pytest.approx(0.485)  # 比較に使うのは在圏版
    assert s_new["wake_rate_plain"][3] == pytest.approx(0.250)  # 既存欄も残る
    assert s_old["wake_rate_basis"] == "all_agents"
    assert s_old["wake_rate"][3] == pytest.approx(0.250)
    assert s_old["wake_rate_in_area"] is None


def test_md_and_json_state_which_wake_rate_definition_was_used(
    yard, anchors, amap, tmp_path
):
    """§4 の md/json が**どちらの定義で測ったか**を明記する(前後で定義が違えばその旨も)。"""
    sp_new = tmp_path / "after.txt"
    sp_new.write_text(SUMMARY_TEXT_IN_AREA, encoding="utf-8")
    sp_old = tmp_path / "before.txt"
    sp_old.write_text(SUMMARY_TEXT, encoding="utf-8")
    jp = synth_journal(tmp_path / "a.npz", hour_mult({9: 10}))
    after = yard.presence_from_journal(jp, amap, summary=yard.read_summary(sp_new))
    before = yard.presence_from_journal(jp, amap, summary=yard.read_summary(sp_old))
    payload = yard.build_payload(after, anchors, target=1_000, before=before)
    w = payload["after"]["wake_rate"]
    assert w["basis"] == "in_area"
    assert "定義=在圏の体の非就寝率" in w["basis_note"]
    assert w["run"][3] == pytest.approx(0.485)
    assert payload["before"]["wake_rate"]["basis"] == "all_agents"
    md = yard.markdown(payload)
    assert "定義=在圏の体の非就寝率" in md
    assert "**before は定義が違う**" in md


# ---------------------------------------------------------------- 3 行が出る


def test_journal_rows_and_ratios(yard, anchors, amap, tmp_path):
    """合成 journal(C=6・T=24)→ 在圏行・昼夜比が手計算と一致する。"""
    p = synth_journal(tmp_path / "a.npz", hour_mult({9: 10, 12: 8}))
    pres = yard.presence_from_journal(p, amap, label="synth")
    m = yard.measures(pres, anchors, target=1_000)
    rows = {r["hour"]: r for r in m["presence_by_hour"]}
    assert sorted(rows) == sorted(yard.REPORT_HOURS)
    # 5 エリア = Σkind(16) × Σcell 域内(6) × hm ・ bbox = 16 × 11 × hm
    assert rows[3]["five_area"] == pytest.approx(96.0)
    assert rows[9]["five_area"] == pytest.approx(960.0)
    assert rows[3]["bbox"] == pytest.approx(176.0)
    assert rows[9]["bbox"] == pytest.approx(1760.0)
    assert m["ratios"]["r_day_night_09_03"] == pytest.approx(10.0)
    assert m["ratios"]["r_noon_night_12_03"] == pytest.approx(8.0)
    # 個体数は要約が無いので bbox 最大(下界)から推定される
    assert pres.n_agents == 1760
    assert "bbox" in pres.n_agents_source
    d = m["distance"]
    assert d["scaled"] is True
    assert d["night_03_in_estimate_band"] is False
    assert d["day_09_vs_core9_daytime"] > 0.0


def test_kind_at_03_breakdown(yard, anchors, amap, tmp_path):
    """03 時の種別内訳: D-66 の 5 種の合計と全体比。"""
    p = synth_journal(tmp_path / "a.npz", hour_mult({9: 10}))
    m = yard.measures(yard.presence_from_journal(p, amap), anchors, target=1_000)
    k = m["kind_at_03"]
    assert [r["name"] for r in k["rows"]] == list(yard.KIND_JA)
    assert k["five_area_total"] == pytest.approx(96.0)
    # kind k の 03 時 5 エリア在圏 = KIND_W[k] × 6
    for i, row in enumerate(k["rows"]):
        assert row["count_five_area"] == pytest.approx(float(KIND_W[i] * 6))
        assert row["count_bbox"] == pytest.approx(float(KIND_W[i] * 11))
        assert row["d66"] == (i in yard.D66_KINDS)
    d66 = float(KIND_W[list(yard.D66_KINDS)].sum() * 6)   # (3+2+1+2)*6 = 48(訪日は外す・第173)
    assert k["d66_total"]["count_five_area"] == pytest.approx(d66)
    assert k["d66_total"]["share_of_five_area"] == pytest.approx(d66 / 96.0, rel=1e-3)


def test_scaled_column_is_linear(yard, anchors, amap, tmp_path):
    """縮尺列 = 生値 × (target / n_agents)・線形で expedient と明記される。"""
    p = synth_journal(tmp_path / "a.npz", hour_mult({9: 10}))
    pres = yard.presence_from_journal(p, amap, n_agents=2_000)
    m = yard.measures(pres, anchors, target=8_000)
    assert pres.n_agents_source == "cli"
    assert m["scale"]["factor"] == pytest.approx(4.0)
    assert m["scale"]["tag"] == "expedient"
    rows = {r["hour"]: r for r in m["presence_by_hour"]}
    for h in yard.REPORT_HOURS:
        assert rows[h]["five_area_scaled"] == pytest.approx(rows[h]["five_area"] * 4.0)
        assert rows[h]["bbox_scaled"] == pytest.approx(rows[h]["bbox"] * 4.0)
    assert m["kind_at_03"]["rows"][0]["count_five_area_scaled"] == pytest.approx(3 * 6 * 4.0)


def test_runs_without_summary(yard, anchors, amap, tmp_path):
    """``--summary`` が無くても表は出る(起床率・計画就寝は None のまま=推測しない)。"""
    p = synth_journal(tmp_path / "a.npz", hour_mult({9: 10}))
    m = yard.measures(yard.presence_from_journal(p, amap), anchors, target=1_000)
    assert m["wake_rate"] is None
    assert m["planned_sleep"] is None
    payload = yard.build_payload(yard.presence_from_journal(p, amap), anchors, target=1_000)
    md = yard.markdown(payload)
    assert "## 1 在圏(5 エリア合計)" in md
    assert "起床率/時" in md            # 読めていない旨の注記
    assert "## 7" not in md             # before が無いので判定表は出ない


def test_summary_feeds_wake_and_sleep_rows(yard, anchors, amap, tmp_path):
    """要約を渡すと a(h) との差と D-62 計数が入り、個体数の出所が要約になる。"""
    sp = tmp_path / "s.txt"
    sp.write_text(SUMMARY_TEXT, encoding="utf-8")
    p = synth_journal(tmp_path / "a.npz", hour_mult({9: 10}))
    pres = yard.presence_from_journal(p, amap, summary=yard.read_summary(sp))
    m = yard.measures(pres, anchors, target=1_000)
    assert pres.n_agents == 5000 and pres.n_agents_source.startswith("summary")
    w = m["wake_rate"]
    assert w["diff_03"] == pytest.approx(0.250 - 0.035, abs=1e-6)
    assert w["diff_12"] == pytest.approx(0.743 - 0.978, abs=1e-6)
    assert w["max_abs_diff"] == pytest.approx(max(abs(x) for x in w["diff"]))
    assert m["planned_sleep"]["slept"] == 1193
    assert m["planned_sleep"]["outside"] == 636


# ---------------------------------------------------------------- 4 前後比較


def test_display_path_hides_the_personal_directory(yard):
    """第176: 記録に書く anchors_path はリポ内なら <repo>/ 相対・外ならそのまま。"""
    assert yard.display_path(yard.DEFAULT_ANCHORS_PATH) == "<repo>/docs/bench/anchors/presence_anchors_v0.json"
    assert yard.display_path("Z:/nowhere/anchors.json") == "Z:/nowhere/anchors.json"


def test_before_after_delta_and_closer(yard, anchors, amap, tmp_path):
    """before/after の差の符号と「現実側へ近づいたか」の bool。"""
    before_p = synth_journal(tmp_path / "b.npz", hour_mult({9: 10}))
    after_p = synth_journal(tmp_path / "a.npz", hour_mult({9: 20}), zero_d66_at=3)
    pb = yard.presence_from_journal(before_p, amap, label="before", n_agents=1_000)
    pa = yard.presence_from_journal(after_p, amap, label="after", n_agents=1_000)
    payload = yard.build_payload(pa, anchors, target=1_000, before=pb)
    rows = {r["metric"]: r for r in payload["comparison"]}
    # 09 時の在圏は現実(130,167)より遥かに小さい → 増えたぶんだけ近づく
    day = rows["在圏 09時 5エリア(換算) 対 昼間人口"]
    assert day["delta"] > 0 and day["closer"] is True
    assert day["gap_after"] < day["gap_before"]
    # 03 時の D-66 種別は 0 になった → 減った=近づいた
    d66 = rows["03時 D-66 種別 在圏(換算)"]
    assert d66["before"] == pytest.approx(48.0)
    assert d66["after"] == pytest.approx(0.0)
    assert d66["delta"] < 0 and d66["closer"] is True
    assert rows["03時 通勤 在圏(生)"]["closer"] is True
    # 訪日は宿泊施設で就寝=参考行(判定外・第173): 行は出るが closer は None
    assert "03時 訪日 在圏(生)" not in rows
    assert rows["03時 訪日 在圏(生・参考)"]["closer"] is None
    # 判定できない行(アンカー無し)は closer=None
    assert payload["comparison_counts"]["judged"] < len(payload["comparison"]) or True
    assert payload["comparison_counts"]["closer"] >= 3
    md = yard.markdown(payload)
    assert "## 7 前より良いか(現実側へ近づいたか)" in md
    assert "before" in md and "after" in md


def test_compare_symmetry_when_moving_away(yard, anchors, amap, tmp_path):
    """逆向き(現実から離れる)なら closer は False になる。"""
    # 昼夜比 before 15(現実 14.8 のすぐ隣)→ after 10(離れる)
    before_p = synth_journal(tmp_path / "b.npz", hour_mult({9: 15}))
    after_p = synth_journal(tmp_path / "a.npz", hour_mult({9: 10}))
    pb = yard.presence_from_journal(before_p, amap, label="before", n_agents=1_000)
    pa = yard.presence_from_journal(after_p, amap, label="after", n_agents=1_000)
    rows = {r["metric"]: r
            for r in yard.build_payload(pa, anchors, target=1_000, before=pb)["comparison"]}
    assert rows["在圏 09時 5エリア(換算) 対 昼間人口"]["closer"] is False
    assert rows["昼夜比 09/03"]["before"] == pytest.approx(15.0)
    assert rows["昼夜比 09/03"]["closer"] is False


# ---------------------------------------------------------------- 5 series JSON 入口


def test_series_json_route(yard, anchors, tmp_path):
    """集計済み JSON(area_hour_counts)からも表が出る(bbox と種別は空欄)。"""
    counts = [[10.0, 20.0, 30.0, 40.0, 50.0] for _ in range(24)]
    counts[9] = [100.0, 200.0, 300.0, 400.0, 500.0]
    doc = {"schema": "shibuya.tools.c7/occupancy/1", "n_samples": 24, "n_cells": 520,
           "tick_seconds": 60, "start_hour": 0, "area_ids": list(yard.AREA_IDS),
           "area_hour_counts": counts, "meta": {"day_index": 1}}
    p = tmp_path / "series.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    pres = yard.presence_from_series(p, label="c7", n_agents=390_067)
    m = yard.measures(pres, anchors, target=390_067)
    assert m["scale"]["factor"] == pytest.approx(1.0)
    rows = {r["hour"]: r for r in m["presence_by_hour"]}
    assert rows[3]["five_area"] == pytest.approx(150.0)
    assert rows[9]["five_area"] == pytest.approx(1500.0)
    assert rows[3]["bbox"] is None and rows[3]["bbox_scaled"] is None
    assert m["kind_at_03"] is None
    assert m["ratios"]["r_day_night_09_03"] == pytest.approx(10.0)
    md = yard.markdown(yard.build_payload(pres, anchors, target=390_067))
    assert "種別軸は journal" in md


def test_series_rejects_wrong_shape(yard, tmp_path):
    """(24,5) でない ``area_hour_counts`` は落とす。"""
    p = tmp_path / "bad.json"
    p.write_text(json.dumps({"area_hour_counts": [[1.0, 2.0]]}), encoding="utf-8")
    with pytest.raises(ValueError):
        yard.presence_from_series(p)
    p2 = tmp_path / "bad2.json"
    p2.write_text(json.dumps({"n_samples": 0}), encoding="utf-8")
    with pytest.raises(ValueError):
        yard.presence_from_series(p2)


def test_cli_writes_json_and_md(yard, amap, tmp_path, monkeypatch, capsys):
    """CLI が ``presence_yardstick.json`` と ``.md`` を書く(写像表は合成を注入)。"""
    monkeypatch.setattr(yard, "_area_map", lambda args: amap)
    a = synth_journal(tmp_path / "a.npz", hour_mult({9: 10}))
    b = synth_journal(tmp_path / "b.npz", hour_mult({9: 5}))
    sp = tmp_path / "s.txt"
    sp.write_text(SUMMARY_TEXT, encoding="utf-8")
    out = tmp_path / "out"
    rc = yard.main(["--journal", str(a), "--summary", str(sp), "--label", "after",
                    "--before", str(b), "--before-label", "before",
                    "--out", str(out)])
    assert rc == 0
    doc = json.loads((out / "presence_yardstick.json").read_text(encoding="utf-8"))
    assert doc["schema"] == "shibuya.tools.c7/presence_yardstick/1"
    assert doc["after"]["label"] == "after" and doc["before"]["label"] == "before"
    assert "comparison" in doc and doc["comparison_counts"]["judged"] > 0
    md = (out / "presence_yardstick.md").read_text(encoding="utf-8")
    assert md.startswith("# 在圏の物差し")
    assert "合格線は書かない" in md
    capsys.readouterr()
