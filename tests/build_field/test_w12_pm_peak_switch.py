"""W12 の夕ピークの切替口が ``run()`` の出力で効くこと(第330 B2・答え 10-12b 1-2)。

欠陥(D-44 §読み 2・10e 構築側の材料 §2-1): ``PM_PEAK_ASSUMED_EQUAL_TO_AM=False`` のとき
``run()`` は朝の本数を夕へ渡しており、True でも False でも夕ピークは朝と同じだった。
``equal_interval_departures`` を直接呼ぶ試験(``test_field_units.py``)では捕まらないので、
ここでは ``run()`` を通して時刻表の parquet を数える。

- 既定(True)= 夕=朝・params に新しい鍵を足さない(param_hash 不変)。
- False = 夕ピークは引数の表 ``PM_PEAK_TRAINS_PER_HOUR`` から。既定の表は無い(None)ので、
  False で表が無い・線が無いときは ValueError(黙って夕=朝に戻さない)。他社の比で埋めない。
"""

from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path

import pytest

from shibuya.build.field import common as C
from shibuya.build.field import w12_external_nodes as w12

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
WORLD = DATA_DIR / "world" / "v2"
_UPSTREAM = ("w11_station_exits.parquet", "w1_nodes.parquet", "w1_edges.parquet")

#: 等間隔ダイヤを作る 5 線(湘南新宿ラインは本数が無い=対象外)。
LINES = ("田園都市線", "東横線", "井の頭線", "山手線", "埼京線")


def test_pm_peak_for_line_rules():
    assert w12.pm_peak_for_line("山手線", True, None) is None
    assert w12.pm_peak_for_line("山手線", True, {"山手線": 12}) is None  # 既定は表を読まない
    assert w12.pm_peak_for_line("山手線", False, {"山手線": 12}) == 12
    with pytest.raises(ValueError):
        w12.pm_peak_for_line("山手線", False, None)
    with pytest.raises(ValueError):
        w12.pm_peak_for_line("山手線", False, {"東横線": 20})


def test_default_has_no_pm_table():
    """既定の表は無い(他社の比 0.79 などを当てはめない)・既定は夕=朝。"""
    assert w12.PM_PEAK_ASSUMED_EQUAL_TO_AM is True
    assert w12.PM_PEAK_TRAINS_PER_HOUR is None


needs_data = pytest.mark.skipif(
    not all((WORLD / n).exists() for n in _UPSTREAM) or not (DATA_DIR / "odpt").exists(),
    reason="data/ absent (CI)",
)


def _run_w12(tmp: Path) -> tuple[C.StageResult, dict]:
    tmp.mkdir(parents=True, exist_ok=True)
    for n in _UPSTREAM:
        shutil.copy2(WORLD / n, tmp / n)
    res = w12.run(C.Ctx(data=DATA_DIR, out=tmp))
    tt = C.read_parquet_columns(tmp / "w12_timetables.parquet")
    return res, tt


def _per_hour(tt: dict, line: str, hours: range) -> dict[int, int]:
    c: Counter = Counter(
        m // 60
        for ln, cal, d, m, src in zip(
            tt["line"], tt["calendar"], tt["direction"], tt["departure_min"], tt["source"]
        )
        if ln == line and cal == "Weekday" and d == "上り" and src == "equal_interval_expedient"
    )
    return {h: c[h] for h in hours}


@needs_data
def test_switch_changes_pm_peak_in_run_output(tmp_path, monkeypatch):
    res0, tt0 = _run_w12(tmp_path / "default")
    assert "pm_peak_trains_per_hour" not in res0.params  # 既定の param_hash は不変
    table = {ln: 10 for ln in LINES}  # 試験用の小さな表(出典の無い値=試験の中だけ)
    monkeypatch.setattr(w12, "PM_PEAK_ASSUMED_EQUAL_TO_AM", False)
    monkeypatch.setattr(w12, "PM_PEAK_TRAINS_PER_HOUR", table)
    res1, tt1 = _run_w12(tmp_path / "switched")
    assert res1.params["pm_peak_trains_per_hour"] == dict(sorted(table.items()))
    assert res1.param_hash != res0.param_hash
    for ln in LINES:
        am0, am1 = _per_hour(tt0, ln, range(7, 10)), _per_hour(tt1, ln, range(7, 10))
        pm0, pm1 = _per_hour(tt0, ln, range(17, 20)), _per_hour(tt1, ln, range(17, 20))
        assert am0 == am1, f"{ln}: 朝ピークが動いた"
        assert list(pm0.values()) == list(am0.values()), f"{ln}: 既定で夕≠朝"
        assert pm1 == {17: 10, 18: 10, 19: 10}, f"{ln}: 夕ピークが表の値にならない {pm1}"
        assert pm1 != pm0, f"{ln}: 切替口が効かない"
    # メトロの実ダイヤの行は切替口で動かない
    real0 = [(a, b, c) for a, b, c, s in zip(tt0["line"], tt0["direction"], tt0["departure"], tt0["source"]) if s == "real"]
    real1 = [(a, b, c) for a, b, c, s in zip(tt1["line"], tt1["direction"], tt1["departure"], tt1["source"]) if s == "real"]
    assert real0 == real1


@needs_data
def test_switch_without_table_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(w12, "PM_PEAK_ASSUMED_EQUAL_TO_AM", False)
    monkeypatch.setattr(w12, "PM_PEAK_TRAINS_PER_HOUR", None)
    with pytest.raises(ValueError):
        _run_w12(tmp_path / "noTable")
