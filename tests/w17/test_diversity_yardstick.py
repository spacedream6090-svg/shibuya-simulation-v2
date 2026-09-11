# -*- coding: utf-8 -*-
"""tools/w17/diversity_yardstick.py の検査。

方針: **合成データで手計算と突き合わせる**。合格線は持たないツールなので、検査するのは
「数え方が定義どおりか」「近似の宣言が出力に残るか」「前後差とフロアが出るか」の 3 点。
実データ(390,067 体)の再現性は親が ``--out`` のランで確認する(設計書 §5 の前値との突合)。
"""

from __future__ import annotations

import json
import math
from pathlib import Path

import numpy as np
import pytest

from .conftest import (
    BLOCK_TEXT,
    FLAT_TEXT,
    TOY_ROWS,
    make_sample,
    write_responses,
    write_toy_parquet,
)


def _weekday(m):
    return m["scopes"]["weekday"]["overall"]


# ---------------------------------------------------------------- 1 アンカー台帳

def test_anchors_required_keys(dy, anchors):
    """全アンカーに source/verified_by/tag と値がある(無ければ落ちる)。"""
    dy.check_anchors(anchors)
    assert anchors["anchors"], "アンカーが空"
    for key, a in anchors["anchors"].items():
        assert a["tag"] in dy.ANCHOR_TAGS, key
        assert a["source"].strip() and a["verified_by"].strip(), key
    # M1/M3 が読む 3 件は必ず居る
    for need in ("motif_count", "motif_threshold", "tokyo_weekday_depart_on_00_30"):
        assert need in anchors["anchors"]
    # 親一次確認の済んでいない項目は報告に出せるように列挙できる
    assert isinstance(dy.unverified_anchors(anchors), list)


def test_anchors_reject_missing_field(dy, anchors, tmp_path):
    """必須欄を 1 つ落としたら ``load_anchors`` は例外(推測で埋めない)。"""
    broken = json.loads(json.dumps({k: v for k, v in anchors.items() if k != "_path"}))
    broken["anchors"]["motif_count"].pop("verified_by")
    p = tmp_path / "broken.json"
    p.write_text(json.dumps(broken, ensure_ascii=False), encoding="utf-8")
    with pytest.raises(ValueError):
        dy.load_anchors(p)


def test_p0_prior_is_not_an_anchor(dy, anchors):
    """設計書 §5 の前値は ``anchors`` ではなく ``p0_prior`` に居る(現実側と混ぜない)。"""
    assert "p0_prior" in anchors
    assert set(anchors["p0_prior"]["values"]) & {"m3a_on_00_30", "m6_exact_share"}
    assert not (set(anchors["anchors"]) & set(anchors["p0_prior"]["values"]))


# ---------------------------------------------------------------- 2 M3(時刻)

def test_m3a_on_00_30_and_entropy(dy, anchors):
    """M3a: 20 本の開始分のうち 19 本が :00/:30 → 0.95・H は手計算 2.9464 bit。"""
    m = dy.measure(make_sample(dy), anchors)
    w = _weekday(m)["m3a"]
    assert w["n"] == len(TOY_ROWS)
    assert w["on_00_30"] == pytest.approx(19 / 20)
    counts = np.array([4, 2, 3, 3, 4, 1, 1, 1, 1], dtype=float) / 20.0
    want = float(-(counts * np.log2(counts)).sum())
    assert w["entropy_bits"] == pytest.approx(want, abs=1e-9)
    assert w["top_bin"] == "00:00" and w["top_bin_share"] == pytest.approx(0.2)


def test_m3b_commute_proxy_and_m3c_work_start(dy, anchors):
    """M3b=勤務開始より前の最後の 移動/乗車(=乗車 480/480/480/510)。M3c=勤務開始。"""
    m = dy.measure(make_sample(dy), anchors)
    b, c = _weekday(m)["m3b"], _weekday(m)["m3c"]
    assert b["n"] == 4 and b["top_bin"] == "08:00"
    assert b["top_bin_share"] == pytest.approx(0.75)
    assert b["on_00_30"] == pytest.approx(1.0)
    assert b["entropy_bits"] == pytest.approx(-(0.75 * math.log2(0.75) + 0.25 * math.log2(0.25)))
    assert b["n_agent_days_with_work"] == 4 and b["n_missing_proxy"] == 0
    assert c["n"] == 4 and c["top_bin"] == "09:00"
    assert c["top_bin_share"] == pytest.approx(0.75)
    assert c["on_00_30"] == pytest.approx(1.0)


def test_m3b_ignores_days_without_work(dy, anchors):
    """勤務の無い日の 移動/乗車 を出勤代理に数えない(数えると分母が膨らむ)。"""
    rows = list(TOY_ROWS) + [
        (2, 0, 0, 600, 0, 0, 3),      # 就寝 自宅
        (2, 0, 600, 700, 2, 3, -1),   # 移動 駅(勤務なしの日)
        (2, 0, 700, 1440, 8, 7, -1),  # 娯楽 娯楽施設
    ]
    m = dy.measure(make_sample(dy, rows=rows, kinds=(0, 0, 1)), anchors)
    assert _weekday(m)["m3b"]["n"] == 4
    assert _weekday(m)["m3b"]["n_agent_days_with_work"] == 4


# ---------------------------------------------------------------- 3 M4 / M6

def test_m4_activity_and_place_counts(dy, anchors):
    """M4a=5.0±0.0(1 日 5 本)。M4b=場所種別 3,3,3,4 → 3.25±0.433・7 未満 1.0。"""
    m = dy.measure(make_sample(dy), anchors)
    a, b = _weekday(m)["m4a"], _weekday(m)["m4b"]
    assert a["mean"] == pytest.approx(5.0) and a["sd"] == pytest.approx(0.0)
    assert b["place_kind"]["mean"] == pytest.approx(3.25)
    assert b["place_kind"]["sd"] == pytest.approx(math.sqrt(0.1875))
    assert b["place_kind"]["lt7_share"] == pytest.approx(1.0)
    assert b["place_cell"]["mean"] == pytest.approx(3.25)


def test_m6_jaccard_pairs(dy, anchors):
    """M6: 体0 は 2 日が完全一致(J=1)・体1 は 4/6。平均 0.8333・完全一致率 0.5。"""
    m = dy.measure(make_sample(dy), anchors)
    j = _weekday(m)["m6"]
    assert j["n"] == 2 and j["n_day_pairs"] == 10  # 平日 5 日の全対=10(在る日だけ数える)
    assert j["mean"] == pytest.approx((1.0 + 4 / 6) / 2)
    assert j["sd"] == pytest.approx(abs(1.0 - 4 / 6) / 2)
    assert j["exact_share"] == pytest.approx(0.5)
    # 設計書 §5 の書き方 J(d0,d) は「最初の曜日を基準にした対」だけ。合成は 2 日しか
    # 無いので全対と同じ値になるが、対の本数(4=d0-d1..d0-d4)が違う。
    j0 = _weekday(m)["m6_from_d0"]
    assert j0["n_day_pairs"] == 4 and j0["n"] == 2
    assert j0["mean"] == pytest.approx(j["mean"])


def test_m6_skips_pairs_with_an_empty_day(dy, anchors):
    """片方の曜日に活動が無い対は数えない(J=0 で入れると『似ていない』に化ける)。"""
    rows = [r for r in TOY_ROWS if not (r[0] == 1 and r[1] == 1)]  # 体1 の火曜を消す
    m = dy.measure(make_sample(dy, rows=rows), anchors)
    j = _weekday(m)["m6"]
    assert j["n"] == 1 and j["mean"] == pytest.approx(1.0)


# ---------------------------------------------------------------- 4 M1(モチーフ)

def test_canonical_motif_is_isomorphism_invariant(dy):
    """節点の付け替えで同じ形になる(出現順ラベルのままでは別物に見える)。"""
    a, ok_a = dy.canonical_motif([(0, 1), (1, 2), (2, 0)], 3)
    b, ok_b = dy.canonical_motif([(1, 2), (2, 0), (0, 1)], 3)
    assert a == b and ok_a and ok_b
    path, _ = dy.canonical_motif([(2, 1), (1, 0)], 3)
    assert path == dy.canonical_motif([(0, 1), (1, 2)], 3)[0]
    big, ok = dy.canonical_motif([(i, i + 1) for i in range(dy.MOTIF_PERM_CAP + 1)],
                                 dy.MOTIF_PERM_CAP + 2)
    assert not ok and big.startswith(f"N{dy.MOTIF_PERM_CAP + 2}*:")


def test_m1_motifs_on_toy(dy, anchors):
    """合成 4 人日 = 三角形 3 + 直線 4 節点 1。閾値 0.5% で 2 種・被覆 1.0・閉路 0.75。"""
    m = dy.measure(make_sample(dy), anchors)
    m1 = _weekday(m)["m1"]
    assert m1["n_day_graphs"] == 4
    assert m1["n_motifs_ge_threshold"] == 2
    assert m1["coverage_ge_threshold"] == pytest.approx(1.0)
    assert m1["closed_share"] == pytest.approx(0.75)
    assert m1["capped_share"] == pytest.approx(0.0)
    assert m1["place_basis"] == "(place_kind, target_cell)"
    top = {t["motif"]: t["n"] for t in m1["top"]}
    assert top["N3:0>1,1>2,2>0"] == 3


def test_m1_unresolved_cells_collapse(dy, anchors):
    """**近似の宣言**: 店 2 軒はどちらも ``target_cell=-1`` なので 1 節点に潰れる。"""
    rows = [
        (0, 0, 0, 400, 0, 0, 5),      # 就寝 自宅(cell 5)
        (0, 0, 400, 600, 2, 5, -1),   # 買物 物販店 A(未解決)
        (0, 0, 600, 800, 2, 5, -1),   # 買物 物販店 B(未解決=同じ節点になる)
        (0, 0, 800, 1440, 2, 0, 5),   # 移動 自宅
    ]
    m = dy.measure(make_sample(dy, rows=rows, kinds=(0,)), anchors)
    top = _weekday(m)["m1"]["top"]
    assert top[0]["motif"] == "N2:0>1,1>0", "店 2 軒が別節点なら N3 になる"
    assert "target_cell" in dy.build_payload(m, anchors)["approximations"]["m1_place"]


# ---------------------------------------------------------------- 5 M2(署名)

def test_m2_timed_vs_untimed_signatures(dy, anchors):
    """時刻を落とすと 2 体が同じ型(種類率 0.5・上位1型 1.0)、時刻を入れると別型。"""
    m = dy.measure(make_sample(dy), anchors)
    untimed = _weekday(m)["m2"]["day0_untimed"]
    timed = _weekday(m)["m2"]["day0_timed"]
    assert untimed["n_types"] == 1 and untimed["type_rate"] == pytest.approx(0.5)
    assert untimed["top1_share"] == pytest.approx(1.0)
    assert timed["n_types"] == 2 and timed["type_rate"] == pytest.approx(1.0)
    assert timed["top1_share"] == pytest.approx(0.5)


# ---------------------------------------------------------------- 6 弊害側・被覆

def test_covered_minutes_handles_overlap(dy):
    """重なった区間を二重に数えない(和集合の長さ)。"""
    gid = np.array([0, 0, 0, 1], dtype=np.int64)
    start = np.array([0, 300, 500, 100], dtype=np.int64)
    end = np.array([600, 400, 900, 200], dtype=np.int64)
    got = dy.covered_minutes(gid, start, end, 2)
    assert got[0] == pytest.approx(900.0)
    assert got[1] == pytest.approx(100.0)


def test_harm_structural_counts(dy, anchors):
    """被覆率・就寝行あり率・深夜違反(合成では隙間 15/30 分だけ・違反 0)。"""
    m = dy.measure(make_sample(dy), anchors)
    h = _weekday(m)["harm_structural"]
    assert h["coverage_mean"] == pytest.approx((1440 + 1440 + 1425 + 1410) / 4 / 1440)
    assert h["sleep_line_share"] == pytest.approx(1.0)
    assert h["night_violation_rows"] == 0
    rows = list(TOY_ROWS) + [(2, 0, 0, 60, 1, 0, 3), (2, 0, 60, 1440, 4, 1, 4)]
    m2 = dy.measure(make_sample(dy, rows=rows, kinds=(0, 0, 0)), anchors)
    assert _weekday(m2)["harm_structural"]["night_violation_rows"] == 1


# ---------------------------------------------------------------- 7 応答 jsonl

def test_parse_flat_and_block_lines(dy):
    """現行形式とブロック形式を 1 本のパーサで読む(``vocab.parse_line`` を再利用)。"""
    acts, blocks, bad, considered = dy.parse_response_text(FLAT_TEXT)
    assert len(acts) == 5 and considered == 5 and not bad
    assert set(blocks) == {-1}
    acts_b, blocks_b, bad_b, considered_b = dy.parse_response_text(BLOCK_TEXT)
    assert len(acts_b) == 5 and considered_b == 5 and not bad_b
    assert blocks_b == [3, 1, 4, 2, 4]
    assert [(a.start, a.activity, a.place) for a in acts] == \
           [(a.start, a.activity, a.place) for a in acts_b]


def test_responses_sample_and_parse_failures(dy, anchors, tmp_path):
    """jsonl → Sample。壊れた行は ``format`` に計上され parse 失敗率に出る。"""
    p = write_responses(tmp_path / "w17_trial_x_responses.jsonl", {
        11: BLOCK_TEXT,
        12: FLAT_TEXT + "\nごめん、わかりません",
    })
    s = dy.sample_from_responses([p], None, label="trial")
    assert s.n_agents == 2 and s.n_rows == 10 and s.block_kind is not None
    g = s.ingest
    assert g["n_lines_considered"] == 11 and g["parse_fail_lines"] == 1
    assert g["parse_fail_rate"] == pytest.approx(1 / 11)
    assert g["bad"]["format"] == 1
    m = dy.measure(s, anchors)
    assert m["input"] == "responses"
    assert _weekday(m)["m4a"]["mean"] == pytest.approx(5.0)


def test_responses_last_line_wins(dy, tmp_path):
    """同じ id が 2 度書かれたら**最後**を採る(fleet_gen の resume 規約)。"""
    p = tmp_path / "r.jsonl"
    p.write_text(
        json.dumps({"id": "7", "text": "d0\n0000-2400 就寝 自宅"}, ensure_ascii=False) + "\n"
        + json.dumps({"id": "7", "text": FLAT_TEXT}, ensure_ascii=False) + "\n",
        encoding="utf-8")
    s = dy.sample_from_responses([p], None)
    assert s.n_rows == 5


# ---------------------------------------------------------------- 8 前後差・フロア・重み

def test_before_after_delta_sign_and_closer(dy, anchors):
    """時刻をばらした after は M3a の H が上がり、:00+:30 が現実側へ寄る。"""
    before = dy.measure(make_sample(dy, label="before"), anchors)
    spread = [list(r) for r in TOY_ROWS]
    for i, delta in ((1, 23), (3, 23), (12, 1)):  # 支度 07:23・勤務 09:23・乗車 08:01
        spread[i][2] += delta
    after = dy.measure(make_sample(dy, rows=[tuple(r) for r in spread], label="after"), anchors)
    rows = {r["id"]: r for r in dy.compare(after, before, anchors)}
    assert rows["m3a_H"]["delta"] > 0 and rows["m3a_H"]["closer"] is True
    assert rows["m3a_on"]["delta"] < 0
    assert rows["m3b_on"]["gap_after"] < rows["m3b_on"]["gap_before"]
    assert rows["m3b_on"]["closer"] is True
    assert rows["m3b_on"]["target"] == anchors["anchors"][
        "tokyo_weekday_depart_on_00_30"]["value"]


def test_floor_rows_absolute_difference(dy, anchors):
    """同腕 2 標本の |A−B|。同じ標本なら 0、違えば差が出る。"""
    a = dy.measure(make_sample(dy, label="A"), anchors)
    rows = {r["id"]: r for r in dy.floor_rows(a, a)}
    assert rows["m3a_on"]["abs_diff"] == pytest.approx(0.0)
    rows2 = list(TOY_ROWS)
    rows2 = [(r[0], r[1], r[2] + (7 if r[4] == dy.ACT_WORK else 0), r[3], r[4], r[5], r[6])
             for r in rows2]
    b = dy.measure(make_sample(dy, rows=rows2, label="B"), anchors)
    f = {r["id"]: r for r in dy.floor_rows(a, b)}
    assert f["m3c_on"]["abs_diff"] > 0
    payload = dy.build_payload(a, anchors, floor=(a, b))
    assert payload["floor"]["a_label"] == "A" and payload["floor"]["b_label"] == "B"
    assert "差の絶対値" in dy.markdown(payload)  # 見出しに | を入れない(表が壊れる)
    assert any(r["abs_diff"] for r in payload["floor"]["rows"])


def test_stratified_weights_and_overall(dy, anchors):
    """w_k = 母集団体数 ÷ 標本体数。重みなし全体と加重全体が別に出る。"""
    pop = np.zeros(9, dtype=np.int64)
    pop[0], pop[1] = 100, 900
    m = dy.measure(make_sample(dy, kinds=(0, 1)), anchors, pop_counts=pop)
    assert m["weights"] == {"0": 100.0, "1": 900.0}
    wk = m["scopes"]["weekday"]
    plain = wk["overall"]["m3a"]["on_00_30"]
    weighted = wk["overall_weighted"]["m3a"]["on_00_30"]
    k0 = wk["by_kind"]["0"]["m3a"]["on_00_30"]
    k1 = wk["by_kind"]["1"]["m3a"]["on_00_30"]
    assert plain == pytest.approx((k0 * 10 + k1 * 10) / 20)
    assert weighted == pytest.approx((100 * 10 * k0 + 900 * 10 * k1) / (100 * 10 + 900 * 10))
    assert weighted != pytest.approx(plain)
    # 件数の定義が無い欄(M1 の個数)は加重しない=None のまま出す
    assert wk["overall_weighted"]["m1"]["n_motifs_ge_threshold"] is None


# ---------------------------------------------------------------- 9 入口と出力

def test_parquet_roundtrip_and_outputs(dy, anchors, tmp_path):
    """合成 parquet → ``load_weekly`` 経由で同じ数字・JSON と Markdown が書ける。"""
    write_toy_parquet(tmp_path / "w17_schedule.parquet")
    s = dy.sample_from_weekly(tmp_path, label="P0toy")
    assert s.n_agents == 2 and s.n_rows == len(TOY_ROWS)
    m = dy.measure(s, anchors)
    assert _weekday(m)["m3a"]["on_00_30"] == pytest.approx(19 / 20)
    payload = dy.build_payload(m, anchors)
    json.dumps(payload, ensure_ascii=False)  # numpy スカラが混ざっていないこと
    md = dy.markdown(payload)
    assert "合格線は書かない" in md and "設計書 §5 の前値との突合" in md
    assert "PASS" not in md and "FAIL" not in md
    paths = dy.write_outputs(tmp_path / "out", "diversity_yardstick", payload, md)
    assert Path(paths["json"]).exists() and Path(paths["md"]).exists()


def test_parquet_file_path_is_accepted(dy, anchors, tmp_path):
    """``--parquet`` に**ファイルパス**を渡せる(下見は w17_trial_<arm>_schedule.parquet)。"""
    p = write_toy_parquet(tmp_path / "trials" / "p1a" / "w17_trial_p1a_schedule.parquet",
                          block=[2] * len(TOY_ROWS), arm="p1a")
    s = dy.sample_from_weekly(None, parquet=p, label="P1a")
    assert s.n_agents == 2 and s.n_rows == len(TOY_ROWS)
    assert s.arm == "p1a" and s.block_kind is not None
    assert dy.measure(s, anchors)["arm"] == "p1a"
    # CLI からも通る(ファイル名が w17_schedule.parquet でなくてよい)
    rc = dy.main(["--parquet", str(p), "--world", str(tmp_path), "--label", "P1a",
                  "--out", str(tmp_path / "o")])
    assert rc == 0
    doc = json.loads((tmp_path / "o" / "diversity_yardstick.json").read_text(encoding="utf-8"))
    assert doc["after"]["arm"] == "p1a"
    with pytest.raises(SystemExit):
        dy.read_weekly_any(tmp_path / "trials" / "p1a" / "missing.parquet")
    with pytest.raises(SystemExit):
        dy.read_weekly_any(tmp_path / "trials" / "p1a" / "w17_trial_p1a_schedule.csv")


def test_file_path_and_directory_agree(dy, anchors, tmp_path):
    """同じ中身なら**ファイル指定とディレクトリ指定で全指標が一致**する。

    余分な列(``block_kind``/``arm``)が増えても M1〜M8 は動かない=場所の判定に使っていない。
    """
    d = tmp_path / "w"
    write_toy_parquet(d / "w17_schedule.parquet")
    f = write_toy_parquet(tmp_path / "t" / "w17_trial_x_schedule.parquet",
                          block=[2] * len(TOY_ROWS), arm="x")
    by_dir = dy.measure(dy.sample_from_weekly(d, label="dir"), anchors)
    by_file = dy.measure(dy.sample_from_weekly(None, parquet=f, label="file"), anchors)
    for scope in ("weekday", "all_days"):
        a = dict(by_dir["scopes"][scope]["overall"])
        b = dict(by_file["scopes"][scope]["overall"])
        assert a.pop("harm_block") != b.pop("harm_block")  # block 検査だけ増える
        assert a == b
    assert by_dir["scopes"]["weekday"]["overall"]["harm_block"]["present"] is False


def test_block_kind_place_mismatch_is_reported(dy, anchors, tmp_path):
    """``block_kind`` と場所語の矛盾を数える(移動 4 は判定しない・場所判定には使わない)。"""
    # 行順は TOY_ROWS のまま: 就寝自宅/支度自宅/乗車駅/勤務職場/移動自宅 × 4 日
    block = []
    for r in TOY_ROWS:
        block.append({0: 3, 1: 1, 3: 4, 4: 2, 7: 2}.get(r[4], 2))
    block[2] = 1   # 乗車 駅 を「自宅」ブロックに=矛盾 1 件
    block[3] = 0   # 勤務 職場 を「域外」ブロックに=矛盾 1 件
    f = write_toy_parquet(tmp_path / "w17_trial_b_schedule.parquet", block=block, arm="b")
    hb = _weekday(dy.measure(dy.sample_from_weekly(None, parquet=f), anchors))["harm_block"]
    assert hb["present"] and hb["mismatch_rows"] == 2
    assert hb["by_rule"]["1 自宅なのに場所語が自宅でない"] == 1
    assert hb["by_rule"]["0 域外なのに場所語が域外でない"] == 1
    assert hb["n_move_unjudged"] == sum(1 for b in block if b == 4)
    assert hb["mismatch_share"] == pytest.approx(2 / hb["n"])
    assert "expedient" in hb["rule"]


def test_cli_end_to_end(dy, anchors, tmp_path, capsys):
    """CLI: ``--parquet``/``--before-parquet``/``--floor``/``--out`` が通る。"""
    p = write_toy_parquet(tmp_path / "w17_schedule.parquet")
    rc = dy.main(["--parquet", str(p), "--world", str(tmp_path), "--label", "P0",
                  "--before-parquet", str(p), "--before-label", "P0b",
                  "--floor", str(p), str(p), "--out", str(tmp_path / "o")])
    assert rc == 0
    doc = json.loads((tmp_path / "o" / "diversity_yardstick.json").read_text(encoding="utf-8"))
    assert doc["schema"] == "shibuya.tools.w17/diversity_yardstick/1"
    assert doc["after"]["label"] == "P0" and doc["before"]["label"] == "P0b"
    assert doc["comparison_counts"]["judged"] >= 1
    assert all(r["abs_diff"] in (0.0, None) for r in doc["floor"]["rows"])
    assert "m5" in doc["approximations"] and "m7" in doc["approximations"]


def test_vocabulary_not_duplicated(dy):
    """語彙はツール側で二重定義していない(``agents.weekly`` と ``build.sched.vocab`` が一致)。"""
    from shibuya.agents import weekly as W
    from shibuya.build.sched import vocab as V

    assert W.ACTIVITY_WORDS == V.ACTIVITY_WORDS
    assert W.PLACE_WORDS == V.PLACE_WORDS
    assert dy.ACTIVITY_WORDS is W.ACTIVITY_WORDS and dy.PLACE_WORDS is W.PLACE_WORDS
    assert W.ACTIVITY_WORDS[dy.ACT_WORK] == "勤務"
    assert W.ACTIVITY_WORDS[dy.ACT_RIDE] == "乗車"
