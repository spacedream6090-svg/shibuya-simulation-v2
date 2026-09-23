"""tests.c7 の共通フィクスチャ。

``tools/c7`` は実行スクリプト置き場でパッケージではない(親がサーバーで
``python tools/c7/xxx.py`` と直接叩く)。テストからは ``sys.path`` に足して素の
モジュール名で import する(``tests/c6/conftest.py`` と同じ作法)。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_C7 = REPO_ROOT / "tools" / "c7"
WORLD_DIR = REPO_ROOT / "data" / "world" / "v2"

if str(TOOLS_C7) not in sys.path:
    sys.path.insert(0, str(TOOLS_C7))

#: 実世界資産が無い環境(CI)では実データのテストを飛ばす。
real_data = pytest.mark.skipif(
    not (WORLD_DIR / "w2_cells.parquet").exists(),
    reason="実世界資産 data/world/v2 が無い",
)


@pytest.fixture(scope="session")
def c7lib():
    import c7lib as _m

    return _m


@pytest.fixture(scope="session")
def occ():
    import occupancy_series as _m

    return _m


@pytest.fixture(scope="session")
def hold():
    import holdout_compare as _m

    return _m


@pytest.fixture(scope="session")
def accept():
    import c7_accept as _m

    return _m


@pytest.fixture(scope="session")
def world_dir() -> Path:
    return WORLD_DIR


@pytest.fixture()
def toy_axes() -> dict:
    """合成の境界定義(原点中心・南北軸=x=0・東西軸=y=0・中心=原点の小矩形)。

    実データの読み取り値に依存しない**幾何の検査**用。
    """
    return {
        "version": "toy",
        "status": "test",
        "origin_latlon": [0.0, 0.0],
        "m_per_deg_lat": 1.0,
        "m_per_deg_lon": 1.0,
        "outer": {"kind": "ellipse", "center_latlon": [0.0, 0.0], "semi_axis_m": [1000.0, 1000.0]},
        "central": {"kind": "rect", "center_latlon": [0.0, 0.0], "half_size_m": [100.0, 100.0]},
        "axes": {
            "ns_jr": {"order": "north_to_south",
                      "waypoints_latlon": [[2000.0, 0.0], [-2000.0, 0.0]]},
            "ew_west_r246": {"order": "west_to_east",
                             "waypoints_latlon": [[0.0, -2000.0], [0.0, 2000.0]]},
            "ew_east_roppongi": {"order": "west_to_east",
                                 "waypoints_latlon": [[0.0, -2000.0], [0.0, 2000.0]]},
        },
        "area_ha_bands": {k: [0.0, 1e9] for k in
                          ("central", "northwest", "northeast", "southeast", "southwest")},
    }


def synth_holdout_doc(
    *,
    year: int = 2024,
    peak_hour_by_area: dict[str, int] | None = None,
    area_weight: dict[str, float] | None = None,
) -> dict:
    """**合成 holdout**(KDDI 生 JSON と同じ形の偽データ)。

    形: ``{"taizai_seibetu": [{名称, 年, 月, 時間帯, 性別, 人数_の合計}, ...],
           "taizai_zokuseibetu": [{名称, 年, 月, 属性, 人数_の合計}, ...]}``
    時間帯は **5..28**(KDDI の 24 区分)。値は「ピーク時刻に山を持つ滑らかな形」。
    """
    import c7lib as _c7

    peaks = peak_hour_by_area or {"central": 18, "northwest": 18, "northeast": 15,
                                  "southeast": 17, "southwest": 16}
    weights = area_weight or {"central": 0.30, "northwest": 0.30, "northeast": 0.18,
                              "southeast": 0.10, "southwest": 0.12}
    rows = []
    for aid in _c7.AREA_IDS:
        name = _c7.AREA_JA[aid]
        for b in _c7.KDDI_HOUR_BINS:
            h = b % 24
            d = min(abs(h - peaks[aid]), 24 - abs(h - peaks[aid]))
            value = round(1000.0 * weights[aid] * (1.0 + 9.0 * np.exp(-(d ** 2) / 18.0)), 3)
            for sex in ("男性", "女性"):
                rows.append({"名称": name, "年": year, "月": 7, "時間帯": f"{b}時台",
                             "性別": sex, "人数_の合計": value / 2.0})
    attrs = []
    shares = {"central": (0.19, 0.05, 0.76), "northeast": (0.42, 0.12, 0.46),
              "northwest": (0.29, 0.14, 0.57), "southeast": (0.45, 0.11, 0.44),
              "southwest": (0.47, 0.12, 0.40)}
    for aid in _c7.AREA_IDS:
        for label, frac in zip(("勤務者", "居住者", "来街者"), shares[aid]):
            attrs.append({"名称": _c7.AREA_JA[aid], "年": year, "月": 7,
                          "属性": label, "人数_の合計": 10_000.0 * frac})
    return {"taizai_seibetu": rows, "taizai_zokuseibetu": attrs}


@pytest.fixture()
def synth_holdout(tmp_path: Path):
    """合成 holdout を書いて、``(path, doc)`` を返す。"""
    doc = synth_holdout_doc()
    p = tmp_path / "la_raw_powerbi_2024.json"
    p.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return p, doc
