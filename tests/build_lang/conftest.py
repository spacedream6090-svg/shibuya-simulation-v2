"""tests.build_lang の共通フィクスチャ。

実資産(data/world/v2)を要さずに W14/W15 を回せる**最小の world_dir** を tmp に作る。
列は各段階が実際に読む列だけ(``C.read_parquet_columns`` は列指定で読む)。
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

#: セル 3 個・POI 4 件の最小世界。
PLACE_IDS = ["g0_0_GL", "g1_0_GL", "g0_1_UG"]
POIS = [
    # poi_id, name, cat, subcat, place_id
    ("p_a", "Journal Standard", "shop", None, "g0_0_GL"),
    ("p_b", "ベーカリー宮下", "food", None, "g0_0_GL"),
    ("p_c", "ローソン", "shop", "convenience", "g1_0_GL"),
    ("p_d", "観世能楽堂", "landmark", None, "g0_1_UG"),
]
#: W7 の content(7 日 × 区間・分)。
PLANS = {
    "p_a": ("[[[600,1320]],[[600,1320]],[[600,1320]],[[600,1320]],[[600,1320]],[],[]]", "mid"),
    "p_b": ("[[[420,1140]],[[420,1140]],[[420,1140]],[[420,1140]],[[420,1140]],"
            "[[420,1140]],[[420,1140]]]", "low"),
    "p_c": ("[[[0,1440]],[[0,1440]],[[0,1440]],[[0,1440]],[[0,1440]],[[0,1440]],[[0,1440]]]",
            "mid"),
    "p_d": ("[[[540,1050]],[[540,1050]],[[540,1050]],[[540,1050]],[[540,1050]],[],[]]", "free"),
}


def _write(path: Path, cols: dict[str, list]) -> None:
    pq.write_table(pa.table({k: pa.array(v) for k, v in cols.items()}), path)


@pytest.fixture()
def world_dir(tmp_path: Path) -> Path:
    """W14/W15 が読む最小の world_dir。"""
    d = tmp_path / "world"
    d.mkdir()
    _write(
        d / "w6_poi.parquet",
        {
            "poi_id": [p[0] for p in POIS],
            "name": [p[1] for p in POIS],
            "cat": [p[2] for p in POIS],
            "subcat": [p[3] for p in POIS],
            "place_id": [p[4] for p in POIS],
        },
    )
    _write(
        d / "w7_plan_spec.parquet",
        {
            "poi_id": [p[0] for p in POIS],
            "content": [PLANS[p[0]][0] for p in POIS],
            "price_tier": [PLANS[p[0]][1] for p in POIS],
        },
    )
    _write(
        d / "w2_cells.parquet",
        {
            "place_id": PLACE_IDS,
            "band": ["GL", "GL", "UG"],
            "block_ids": [[1, 2], [3], []],
        },
    )
    _write(
        d / "w8_targets.parquet",
        {
            "target_id": [0, 1, 2, 3, 4],
            "kind": ["poi", "poi", "poi", "poi", "exit"],
            "ref_id": ["p_a", "p_b", "p_c", "p_d", "e1"],
        },
    )
    _write(
        d / "w8_t1_cell.parquet",
        {
            "place_idx": [0, 0, 0, 1, 1, 2],
            "target_id": [0, 1, 4, 2, 0, 3],
            "n_viewpoints": [30, 20, 10, 40, 5, 7],
        },
    )
    _write(
        d / "w11_station_exits.parquet",
        {"exit_id": ["e1"], "exit_name": ["西口"], "station_title": ["渋谷駅"]},
    )
    return d


def write_responses(path: Path, rows: list[tuple[str, int, str]]) -> Path:
    """``(id, rep, text)`` の並び → fleet_gen 形式の応答 jsonl。"""
    with open(path, "w", encoding="utf-8") as fh:
        for pid, rep, text in rows:
            fh.write(
                json.dumps(
                    {
                        "id": pid,
                        "rep": rep,
                        "model": "Qwen3-32B-AWQ",
                        "endpoint": "http://127.0.0.1:8100",
                        "text": text,
                        "finish_reason": "stop",
                        "prompt_tokens": 100,
                        "completion_tokens": 20,
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    return path


def duplicate_reps(pairs: dict[str, str]) -> list[tuple[str, int, str]]:
    """``{id: text}`` → rep0/rep1 が同一の応答行(バイト一致ゲートを通る形)。"""
    return [(pid, rep, text) for pid, text in pairs.items() for rep in (0, 1)]
