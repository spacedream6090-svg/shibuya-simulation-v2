# -*- coding: utf-8 -*-
"""tests.w17 の共通フィクスチャ。

``tools/w17`` は実行スクリプト置き場でパッケージではない(親が
``python tools/w17/xxx.py`` と直接叩く)。テストからは ``sys.path`` に足して素の
モジュール名で import する(``tests/c7/conftest.py`` と同じ作法)。
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS_W17 = REPO_ROOT / "tools" / "w17"
WORLD_DIR = REPO_ROOT / "data" / "world" / "v2"

if str(TOOLS_W17) not in sys.path:
    sys.path.insert(0, str(TOOLS_W17))

#: 実世界資産が無い環境(CI)では実データのテストを飛ばす。
real_data = pytest.mark.requires_data("world_v2:w17_schedule.parquet")


@pytest.fixture(scope="session")
def dy():
    import diversity_yardstick as _m

    return _m


#: 〔第337 封印の分離の残り〕fixture は**構築側のファイル**(``diversity_build_anchors_v0.json``)だけを開き、
#: 検証側(第 30 表〔検〕・Schneider 2013〔灰〕)は鍵の名だけ同じ**作り物**にする(値は試験の中で作る)。
BUILD_ANCHORS_PATH = REPO_ROOT / "docs" / "bench" / "anchors" / "diversity_build_anchors_v0.json"
SYNTH_SOURCE = "synthetic(test)"
#: 作り物の鍵(``diversity_validation_anchors_v0.json`` と同じ名・値は作り物)。
SYNTH_KEYS = ("tokyo_weekday_depart_on_00_30", "tokyo_weekday_depart_top_bin_share",
              "tokyo_weekday_depart_top_hour_share", "tokyo_weekday_depart_entropy_bits",
              "national_weekday_depart_on_00_30", "national_weekday_depart_entropy_bits",
              "motif_count", "motif_coverage", "motif_threshold",
              "daily_locations_lt7_share", "daily_locations_lognormal")


def synth_validation_anchors() -> dict:
    """検証側の錨の**作り物**(検証側のファイルの値ではない)。

    ``motif_threshold`` は M1 の数え方の閾値で、合成 4 人日の試験の docstring(閾値 0.5%)に合わせた。ほかは
    既存の assert が通る形の作り物(:00/:30 の割合は合成の before より低い=時刻をばらした after が近づく)。
    """
    def row(tag: str, **kw) -> dict:
        return {"source": SYNTH_SOURCE, "verified_by": SYNTH_SOURCE, "tag": tag, "unit": "synthetic",
                "scope": "synthetic(test)", **kw}

    return {
        "tokyo_weekday_depart_on_00_30": row("anchor", value=0.4),
        "tokyo_weekday_depart_top_bin_share": row("anchor", value=0.2),
        "tokyo_weekday_depart_top_hour_share": row("anchor", value=0.3),
        "tokyo_weekday_depart_entropy_bits": row("anchor", value=4.0),
        "national_weekday_depart_on_00_30": row("anchor", value=0.4),
        "national_weekday_depart_entropy_bits": row("anchor", value=4.0),
        "motif_count": row("anchor", value=10),
        "motif_coverage": row("anchor", value=0.8),
        "motif_threshold": row("anchor", value=0.005),
        "daily_locations_lt7_share": row("anchor", value=0.9),
        "daily_locations_lognormal": row("anchor", value=2.0, values={"mu": 0.7, "sigma": 0.4}),
    }


@pytest.fixture(scope="session", autouse=True)
def _no_default_validation_file(dy, tmp_path_factory):
    """番人: 既定の道筋(構築側+検証側)で台帳を読もうとしたら、検証側を無いファイルに差し替えて落とす。"""
    absent = tmp_path_factory.mktemp("no_validation") / "absent_diversity_validation_anchors.json"
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(dy, "DEFAULT_ANCHORS_PATHS", (dy.DEFAULT_ANCHORS_PATHS[0], absent))
        yield


@pytest.fixture(scope="session")
def anchors(dy):
    """構築側のファイル+検証側の作り物(:func:`synth_validation_anchors`)。"""
    doc = dy.load_anchors(BUILD_ANCHORS_PATH)  # 構築側のファイルだけを開く
    clash = set(doc["anchors"]) & set(SYNTH_KEYS)
    assert not clash, f"構築側のファイルに作り物と同じ鍵がある: {sorted(clash)}"
    doc["anchors"] = {**doc["anchors"], **synth_validation_anchors()}
    dy.check_anchors(doc)
    return doc


@pytest.fixture()
def anchors_file(anchors, tmp_path):
    """CLI に渡す台帳(構築側+作り物を 1 本に書いたもの)。"""
    import json

    p = tmp_path / "anchors_synth.json"
    p.write_text(json.dumps({k: v for k, v in anchors.items() if k != "_path"}, ensure_ascii=False), encoding="utf-8")
    return p


# ---------------------------------------------------------------- 合成データ

#: 語彙の索引(``agents.weekly.ACTIVITY_WORDS``/``PLACE_WORDS`` の順)。
A_SLEEP, A_PREP, A_MOVE, A_RIDE, A_WORK = 0, 1, 2, 3, 4
A_SHOP = 7
P_HOME, P_WORK, P_STATION, P_STORE = 0, 1, 3, 5

#: 合成 2 体 × 2 日。手計算しやすいように端数を 1 か所ずつだけ入れてある。
#: 行 = (体, 曜日, 開始分, 終了分, 活動, 場所種別, セル)
TOY_ROWS: tuple[tuple[int, int, int, int, int, int, int], ...] = (
    # 体 0: 月・火とも完全に同じ日課(すべて :00)
    (0, 0, 0, 420, A_SLEEP, P_HOME, 5),
    (0, 0, 420, 480, A_PREP, P_HOME, 5),
    (0, 0, 480, 540, A_RIDE, P_STATION, -1),
    (0, 0, 540, 1080, A_WORK, P_WORK, 9),
    (0, 0, 1080, 1440, A_MOVE, P_HOME, 5),
    (0, 1, 0, 420, A_SLEEP, P_HOME, 5),
    (0, 1, 420, 480, A_PREP, P_HOME, 5),
    (0, 1, 480, 540, A_RIDE, P_STATION, -1),
    (0, 1, 540, 1080, A_WORK, P_WORK, 9),
    (0, 1, 1080, 1440, A_MOVE, P_HOME, 5),
    # 体 1: 月は 07:15 起き(:15 が 1 本・隙間 15 分)、火は 30 分ずれ+帰りが買物
    (1, 0, 0, 420, A_SLEEP, P_HOME, 7),
    (1, 0, 435, 480, A_PREP, P_HOME, 7),
    (1, 0, 480, 540, A_RIDE, P_STATION, -1),
    (1, 0, 540, 1080, A_WORK, P_WORK, 9),
    (1, 0, 1080, 1440, A_MOVE, P_HOME, 7),
    (1, 1, 0, 420, A_SLEEP, P_HOME, 7),
    (1, 1, 450, 510, A_PREP, P_HOME, 7),
    (1, 1, 510, 570, A_RIDE, P_STATION, -1),
    (1, 1, 570, 1080, A_WORK, P_WORK, 9),
    (1, 1, 1080, 1440, A_SHOP, P_STORE, -1),
)


def make_sample(dy, rows=TOY_ROWS, kinds=(0, 0), label="toy", block=None):
    """行の並び → ``Sample``(parquet を書かずに器だけ作る)。"""
    r = np.asarray(rows, dtype=np.int64)
    order = np.lexsort((np.arange(r.shape[0]), r[:, 1], r[:, 0]))
    r = r[order]
    agents = np.unique(r[:, 0])
    row_agent = np.searchsorted(agents, r[:, 0])
    return dy.Sample(
        label=label, source="toy", input_kind="parquet",
        agent_id=agents.astype(np.int64),
        kind=np.asarray(kinds, dtype=np.int8),
        row_agent=row_agent.astype(np.int64), row_day=r[:, 1],
        start=r[:, 2], end=r[:, 3], activity=r[:, 4],
        place_kind=r[:, 5], target_cell=r[:, 6],
        block_kind=None if block is None else np.asarray(block, dtype=np.int64)[order],
    )


def write_toy_parquet(path: Path, rows=TOY_ROWS, *, block=None, arm=None) -> Path:
    """合成の週次表 parquet を書く(列は ``agents.weekly._COLUMNS``)。

    ``block``/``arm`` を渡すと下見の出力形
    (``w17_trial_<arm>_schedule.parquet`` = 8 列 + ``block_kind`` + ``arm``)になる。
    """
    import pyarrow as pa
    import pyarrow.parquet as pq

    r = np.asarray(rows, dtype=np.int64)
    order = np.lexsort((np.arange(r.shape[0]), r[:, 1], r[:, 0]))
    r = r[order]
    seq = np.zeros(r.shape[0], dtype=np.int16)
    key = r[:, 0] * 10 + r[:, 1]
    for k in np.unique(key):
        m = key == k
        seq[m] = np.arange(int(m.sum()), dtype=np.int16)
    table = pa.table({
        "agent_id": pa.array(r[:, 0], pa.int64()),
        "day": pa.array(r[:, 1], pa.int8()),
        "seq": pa.array(seq, pa.int16()),
        "start_min": pa.array(r[:, 2], pa.int16()),
        "end_min": pa.array(r[:, 3], pa.int16()),
        "activity_code": pa.array(r[:, 4], pa.int8()),
        "place_kind": pa.array(r[:, 5], pa.int8()),
        "target_cell": pa.array(r[:, 6], pa.int32()),
    })
    if block is not None:
        table = table.append_column(
            "block_kind", pa.array(np.asarray(block, dtype=np.int64)[order], pa.int8()))
    if arm is not None:
        table = table.append_column("arm", pa.array([arm] * r.shape[0], pa.string()))
    path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(table, path)
    return path


#: 応答 1 体ぶんの本文(現行形式=日見出し+3 列)。
FLAT_TEXT = "\n".join([
    "d0",
    "0000-0700 就寝 自宅",
    "0700-0800 支度 自宅",
    "0800-0900 乗車 駅",
    "0900-1800 勤務 職場",
    "1800-2400 移動 自宅",
])

#: 同じ内容のブロック形式(計画実行層設計書 §9: 0 域外/1 自宅/2 在圏/3 就寝/4 移動)。
BLOCK_TEXT = "\n".join([
    "d0",
    "0000-0700 3 就寝 自宅",
    "0700-0800 1 支度 自宅",
    "0800-0900 4 乗車 駅",
    "0900-1800 2 勤務 職場",
    "1800-2400 4 移動 自宅",
])


def write_responses(path: Path, texts: dict[int, str]) -> Path:
    """``{agent_id: 本文}`` → fleet_gen 形式の応答 jsonl。"""
    import json

    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        for aid, text in texts.items():
            fh.write(json.dumps({"id": str(aid), "text": text, "completion_tokens": 100},
                                ensure_ascii=False) + "\n")
    return path
