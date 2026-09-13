# -*- coding: utf-8 -*-
"""holdout 照合の検査。**本物の KDDI データは開かない**——合成 holdout だけを使う。

検査するもの
- 封印ガード(``--open-seal`` 無し / 二度目 / sha256 不一致)
- 生データ読み取り(欄名の解決・時間帯 5-28 → 0-23・形状への正規化)
- 形状5指標(一致=合格 / ずらす=不合格 / H3 は代替であることの明示)
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pytest

from .conftest import synth_holdout_doc


# ---------------------------------------------------------------- 封印ガード


def test_guard_requires_explicit_flag(hold, tmp_path):
    with pytest.raises(hold.SealError, match="--open-seal"):
        hold.guard_open(tmp_path / "rec.json", open_seal=False, force=False)


def test_guard_allows_first_open(hold, tmp_path):
    assert hold.guard_open(tmp_path / "rec.json", open_seal=True, force=False) is None


def test_second_write_keeps_the_first_record_in_history(hold, tmp_path):
    """第176(層2 指摘 A): --force の 2 本目で主張腕の初回開封の証跡が消えない。"""
    import json

    rec = tmp_path / "rec.json"
    hold.write_open_record(rec, {"opened_utc": "2026-09-14T00:00:00Z", "run_id": "c7-day-4", "forced": False})
    assert hold.guard_open(rec, open_seal=True, force=True)["run_id"] == "c7-day-4"
    hold.write_open_record(rec, {"opened_utc": "2026-09-14T00:10:00Z", "run_id": "c7-day-3", "forced": True})
    hold.write_open_record(rec, {"opened_utc": "2026-09-14T00:20:00Z", "run_id": "c7-day-2", "forced": True})
    doc = json.loads(rec.read_text(encoding="utf-8"))
    assert doc["run_id"] == "c7-day-2" and doc["forced"] is True
    assert [h["run_id"] for h in doc["previous_openings"]] == ["c7-day-4", "c7-day-3"]
    assert doc["previous_openings"][0]["forced"] is False
    assert "previous_openings" not in doc["previous_openings"][1]


def test_guard_refuses_second_open(hold, tmp_path):
    rec = tmp_path / "rec.json"
    hold.write_open_record(rec, {"opened_utc": "2026-09-09T00:00:00Z", "run_id": "r1"})
    with pytest.raises(hold.SealError, match="1 回のみ"):
        hold.guard_open(rec, open_seal=True, force=False)
    # --force なら通る(理由は登録簿へ)
    prev = hold.guard_open(rec, open_seal=True, force=True)
    assert prev["run_id"] == "r1"


def _fake_freeze(tmp_path: Path, data_root: Path, member_rel: str, sha: str, size: int) -> Path:
    world = tmp_path / "world"
    world.mkdir(parents=True, exist_ok=True)
    (world / "w19_freeze.json").write_text(json.dumps({
        "holdout_seal": {"seal_scheme": "S", "layers": [
            {"name": "kddi_la", "members": [member_rel], "member_hash": "deadbeef",
             "member_files": [{"path": member_rel, "sha256": sha, "bytes": size}],
             "sealed_utc": "2026-09-08T00:00:00Z", "opened": False},
        ]}
    }, ensure_ascii=False), encoding="utf-8")
    return world


def test_check_seal_detects_mismatch(hold, tmp_path, synth_holdout):
    src, _ = synth_holdout
    data_root = tmp_path / "data"
    (data_root / "realworld" / "kddi_la").mkdir(parents=True)
    target = data_root / "realworld" / "kddi_la" / "la.json"
    target.write_bytes(src.read_bytes())
    good = hold.sha256_file(target)

    world_ok = _fake_freeze(tmp_path / "ok", data_root, "realworld/kddi_la/la.json",
                            good, target.stat().st_size)
    seal = hold.check_seal(data_root, hold.load_seal(world_ok))
    assert seal["ok"] and seal["files"][0]["match"]

    world_ng = _fake_freeze(tmp_path / "ng", data_root, "realworld/kddi_la/la.json",
                            "0" * 64, target.stat().st_size)
    seal_ng = hold.check_seal(data_root, hold.load_seal(world_ng))
    assert not seal_ng["ok"]


def test_check_seal_empty_members_raises(hold, tmp_path):
    with pytest.raises(hold.SealError, match="メンバーが 1 件も無い"):
        hold.check_seal(tmp_path, {"name": "kddi_la", "member_files": []})


def test_load_seal_unknown_layer(hold, tmp_path, synth_holdout):
    src, _ = synth_holdout
    world = _fake_freeze(tmp_path, tmp_path, "x.json", hold.sha256_file(src), 1)
    with pytest.raises(hold.SealError, match="封印層"):
        hold.load_seal(world, layer="shibuya_jinryu")


# ---------------------------------------------------------------- 生データ読み取り


def test_hour_bin_conversion(hold):
    assert hold.hour_bin_to_sim_hour("5時台") == 5
    assert hold.hour_bin_to_sim_hour(23) == 23
    assert hold.hour_bin_to_sim_hour("24時台") == 0
    assert hold.hour_bin_to_sim_hour("28時台") == 4
    assert hold.hour_bin_to_sim_hour("不明") is None


def test_resolve_fields_aliases_and_failure(hold):
    sample = {"名称": "渋谷駅中心エリア", "年": 2024, "時間帯": "5時台", "人数_の合計": 1.0}
    got = hold.resolve_fields(sample, ("area", "year", "hour", "value"))
    assert got == {"area": "名称", "year": "年", "hour": "時間帯", "value": "人数_の合計"}
    with pytest.raises(KeyError, match="attr"):
        hold.resolve_fields(sample, ("attr",))


def test_resolve_fields_explicit_override(hold):
    sample = {"AREA": "渋谷駅中心エリア", "Y": 2024, "H": 5, "V": 1.0}
    got = hold.resolve_fields(sample, ("area", "year", "hour", "value"),
                              {"area": "AREA", "year": "Y", "hour": "H", "value": "V"})
    assert got["area"] == "AREA"
    with pytest.raises(KeyError, match="生データに無い"):
        hold.resolve_fields(sample, ("area",), {"area": "MISSING"})


def test_read_holdout_shapes(hold, c7lib, synth_holdout):
    path, _ = synth_holdout
    got = hold.read_holdout(path)
    assert got["obs_hour_share"].shape == (5, 24)
    assert np.allclose(got["obs_hour_share"].sum(axis=1), 1.0)
    assert got["obs_area_share"].shape == (5,)
    assert got["obs_area_share"].sum() == pytest.approx(1.0)
    assert got["obs_attr_share"].shape == (5, 3)
    assert got["meta"]["hour"]["year"] == 2024
    assert got["meta"]["hour"]["n_skipped"] == 0
    # ピーク時刻が合成時の指定どおり
    peaks = c7lib.peak_hours(got["obs_hour_share"])
    assert dict(zip(c7lib.AREA_IDS, peaks.tolist()))["central"] == 18


def test_read_holdout_unknown_table_raises(hold, tmp_path):
    p = tmp_path / "x.json"
    p.write_text(json.dumps({"other": []}), encoding="utf-8")
    with pytest.raises(KeyError):
        hold.read_holdout(p)


def test_find_table_nested(hold):
    doc = {"tables": {"taizai_seibetu": [{"a": 1}]}}
    assert hold.find_table(doc, "taizai_seibetu") == [{"a": 1}]


# ---------------------------------------------------------------- 形状5指標


def _sim_table_from_share(c7lib, share, level=None):
    """``(5,24)`` シェア → ``(24,5)`` の在圏数(水準は形状判定に効かないことの確認も兼ねる)。"""
    lv = np.array(level if level is not None else [1.0] * 5)
    return (share * lv[:, None]).T * 1000.0


def test_five_metrics_identical_passes(hold, c7lib, synth_holdout):
    path, _ = synth_holdout
    obs = hold.read_holdout(path)
    sim = _sim_table_from_share(c7lib, obs["obs_hour_share"], obs["obs_area_share"] * 5)
    res = hold.compare(sim, obs, sim_attr=obs["obs_attr_share"])
    assert res["n_measured"] == 5
    assert res["pass"], res
    assert res["H1"]["jsd_mean"] == pytest.approx(0.0, abs=1e-9)
    assert res["H2"]["n_within"] == 5
    assert res["H3"]["substituted"] is True


def test_five_metrics_shifted_peaks_fail(hold, c7lib, synth_holdout, tmp_path):
    """ピークを 5 時間ずらすと H1(形)と H2(ピーク)が落ちる。"""
    path, _ = synth_holdout
    obs = hold.read_holdout(path)
    shifted = tmp_path / "shift.json"
    shifted.write_text(json.dumps(synth_holdout_doc(
        peak_hour_by_area={"central": 13, "northwest": 13, "northeast": 10,
                           "southeast": 12, "southwest": 11}), ensure_ascii=False),
        encoding="utf-8")
    sim_src = hold.read_holdout(shifted)
    sim = _sim_table_from_share(c7lib, sim_src["obs_hour_share"], obs["obs_area_share"] * 5)
    res = hold.compare(sim, obs, sim_attr=obs["obs_attr_share"])
    assert not res["pass"]
    assert res["H2"]["n_within"] == 0
    assert res["H1"]["jsd_mean"] > res["prereg"]["H1"]["jsd_area_hour_mean_max"]


def test_five_metrics_level_invariant(hold, c7lib, synth_holdout):
    """**絶対水準は判定に効かない**(D1′「値は形状と比のみ」)。"""
    path, _ = synth_holdout
    obs = hold.read_holdout(path)
    a = _sim_table_from_share(c7lib, obs["obs_hour_share"], obs["obs_area_share"] * 5)
    res_a = hold.compare(a, obs, sim_attr=obs["obs_attr_share"])
    res_b = hold.compare(a * 987.0, obs, sim_attr=obs["obs_attr_share"])
    assert res_a["H1"]["jsd_mean"] == pytest.approx(res_b["H1"]["jsd_mean"])
    assert res_a["H4"]["jsd"] == pytest.approx(res_b["H4"]["jsd"])


def test_five_metrics_missing_inputs_are_not_measured(hold, c7lib, synth_holdout):
    path, _ = synth_holdout
    obs = dict(hold.read_holdout(path))
    obs["obs_attr_share"] = None
    obs["obs_area_share"] = None
    sim = _sim_table_from_share(c7lib, obs["obs_hour_share"])
    res = hold.compare(sim, obs)
    assert res["H4"]["measured"] is False and res["H4"]["pass"] is None
    assert res["H5"]["measured"] is False
    assert res["n_measured"] == 3


def test_area_composition_detects_shift(hold, c7lib, synth_holdout):
    path, _ = synth_holdout
    obs = hold.read_holdout(path)
    bad = np.array([0.60, 0.10, 0.10, 0.10, 0.10])
    sim = _sim_table_from_share(c7lib, obs["obs_hour_share"], bad * 5)
    res = hold.compare(sim, obs, sim_attr=obs["obs_attr_share"])
    assert res["H4"]["measured"] and not res["H4"]["pass"]
    assert res["H1"]["pass"], "形(時刻シェア)は無傷のはず"


def test_tau_undefined_is_reported_not_hidden(hold, c7lib, synth_holdout, tmp_path):
    """全エリアが同じピーク時刻だと τ-b は定義できない。FAIL にしつつ理由を残す。"""
    flat = tmp_path / "flat.json"
    flat.write_text(json.dumps(synth_holdout_doc(
        peak_hour_by_area={a: 18 for a in c7lib.AREA_IDS}), ensure_ascii=False), encoding="utf-8")
    obs = hold.read_holdout(flat)
    sim = _sim_table_from_share(c7lib, obs["obs_hour_share"], obs["obs_area_share"] * 5)
    res = hold.compare(sim, obs, sim_attr=obs["obs_attr_share"])
    assert res["H2"]["n_within"] == 5            # 時刻そのものは完全一致
    assert res["H2"]["tau_undefined"] is True    # 順序は定義できない
    assert res["H2"]["kendall_tau"] is None
    assert res["H2"]["pass"] is False            # 分化していないので合格にしない


def test_prereg_thresholds_are_declared(c7lib):
    """事前登録案が『案』であること・下限対照が v1 テンプレ水準であることを固定する。"""
    pr = c7lib.PREREG_V0
    assert "案" in pr["status"]
    assert pr["jsd_reject"] == pytest.approx(0.0122)   # v1テンプレ vs KDDI(2024)
    assert pr["jsd_target"] == pytest.approx(0.0012)   # 年次変動の上端
    assert pr["H3"]["substituted"] is True


def test_metrics_markdown_has_all_rows(hold, c7lib, synth_holdout):
    path, _ = synth_holdout
    obs = hold.read_holdout(path)
    sim = _sim_table_from_share(c7lib, obs["obs_hour_share"], obs["obs_area_share"] * 5)
    md = c7lib.metrics_markdown(hold.compare(sim, obs, sim_attr=obs["obs_attr_share"]))
    for key in ("H1", "H2", "H3", "H4", "H5"):
        assert key in md
    assert "相関" in md and "平日休日比" in md


def test_report_does_not_leak_absolute_levels(hold, c7lib, synth_holdout):
    """報告に**実数(拡大推計値)**が出ない=D1′『形状と比のみ』の機械的な確認。"""
    path, _ = synth_holdout
    obs = hold.read_holdout(path)
    sim = _sim_table_from_share(c7lib, obs["obs_hour_share"], obs["obs_area_share"] * 5)
    res = hold.compare(sim, obs, sim_attr=obs["obs_attr_share"])
    text = json.dumps(res, ensure_ascii=False)
    for key in ("obs_hour_counts", "人数", "raw_value", "obs_counts"):
        assert key not in text
    # 出ている数はすべて 0-24 の範囲(シェア・時刻・τ・比)
    assert all(abs(v) <= 24.0 for v in _numbers(res))


def _numbers(obj):
    if isinstance(obj, (int, float)) and not isinstance(obj, bool):
        yield float(obj)
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from _numbers(v)
    elif isinstance(obj, (list, tuple)):
        for v in obj:
            yield from _numbers(v)


def test_sim_from_occupancy_shape_check(hold):
    with pytest.raises(ValueError, match="area_hour_counts"):
        hold.sim_from_occupancy({"area_hour_counts": [[0.0] * 5] * 12})
