"""W12 の夕ピークの切替口が ``run()`` の出力で効くこと(第330 B2・答え 10-12b 1-2)。

欠陥(D-44 §読み 2・10e 構築側の材料 §2-1): ``PM_PEAK_ASSUMED_EQUAL_TO_AM=False`` のとき
``run()`` は朝の本数を夕へ渡しており、True でも False でも夕ピークは朝と同じだった。
``equal_interval_departures`` を直接呼ぶ試験(``test_field_units.py``)では捕まらないので、
ここでは ``run()`` を通して時刻表の parquet を数える。

- 既定(True)= 夕=朝・params に新しい鍵を足さない(param_hash 不変)。
- False = 夕ピークは引数の表 ``PM_PEAK_TRAINS_PER_HOUR`` から。既定の表は無い(None)ので、
  False で表が無い・線が無いときは ValueError(黙って夕=朝に戻さない)。他社の比で埋めない。

〔第 2 期 2-3b〕W12 1.2.0 から既定は実ダイヤ(等間隔の線 0)。夕ピークの切替口は等間隔の推定の道(実データの
無い線が出たとき)にだけ効くので、``run()`` を通す試験は等間隔の線が出る形で回す。〔第 4 期 4-3 版上げ 3 回目の第 2 部〕
前は 1.1.0 の形の切替口 ``USE_REAL_TIMETABLES=False``(5 線が等間隔)を使った=消したので、京王の切替口
``USE_ODPT_CHALLENGE=False``(井の頭線が等間隔=``test_w12_keio_switch_2_4.py``)で回す。
"""

from __future__ import annotations

import shutil
from collections import Counter
from pathlib import Path

import pytest

from shibuya.build.field import common as C
from shibuya.build.field import w12_external_nodes as w12
from shibuya.build.field import w12_real_timetables as RT
from tests import _data_ids as D

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
WORLD = DATA_DIR / "world" / "v2"
_UPSTREAM = ("w11_station_exits.parquet", "w1_nodes.parquet", "w1_edges.parquet")

#: 等間隔ダイヤを作る線(京王の切替口 off=井の頭線だけ・〔第 2 部〕前は 1.1.0 の形の 5 線)。
LINES = ("井の頭線",)


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


needs_data = pytest.mark.requires_data(*D.ids_of(*(WORLD / n for n in _UPSTREAM), DATA_DIR / "odpt"))


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
    monkeypatch.setattr(RT, "USE_ODPT_CHALLENGE", False)  # 〔第 2 部〕等間隔の道=井の頭線(京王の切替口 off)
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
        # 既定=夕=朝: 真ん中の時(18 時台と 8 時台)は同じ本数。境の時(17・19 時台)は入る時刻の
        # 端数で 1 本までずれうる(第330 B3 の「小数で積み切り捨て」)。
        assert pm0[18] == am0[8], f"{ln}: 既定で夕≠朝 {pm0} {am0}"
        assert all(abs(pm0[h] - am0[8]) <= 1 for h in (17, 19)), f"{ln}: {pm0}"
        assert pm1[18] == 10 and all(9 <= pm1[h] <= 10 for h in (17, 19)), (
            f"{ln}: 夕ピークが表の値にならない {pm1}"
        )
        assert pm1 != pm0, f"{ln}: 切替口が効かない"
    # メトロの実ダイヤの行は切替口で動かない
    real0 = [(a, b, c) for a, b, c, s in zip(tt0["line"], tt0["direction"], tt0["departure"], tt0["source"]) if s == "real"]
    real1 = [(a, b, c) for a, b, c, s in zip(tt1["line"], tt1["direction"], tt1["departure"], tt1["source"]) if s == "real"]
    assert real0 == real1


@needs_data
def test_switch_without_table_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(RT, "USE_ODPT_CHALLENGE", False)  # 〔第 2 部〕等間隔の道=井の頭線(京王の切替口 off)
    monkeypatch.setattr(w12, "PM_PEAK_ASSUMED_EQUAL_TO_AM", False)
    monkeypatch.setattr(w12, "PM_PEAK_TRAINS_PER_HOUR", None)
    with pytest.raises(ValueError):
        _run_w12(tmp_path / "noTable")
