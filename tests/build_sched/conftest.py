"""tests.build_sched の共通フィクスチャ。

実資産(data/world/v2・data/persona_pool_v2)を要さずに W17 を回せる**最小の世界と
プール**を tmp に作る。列は段階が実際に読む列だけ。
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from shibuya.build.sched import vocab as V

# --- 母集団(9 体・全 9 種別のうち主要 7 種別を含む)-----------------------------------
# (agent_id, kind, purpose, age, sex, home, work, school, dir, pool_layer, pool_index)
AGENTS: list[tuple[int, int, int, int, int, int, int, int, int, int, int]] = [
    (0, 3, 4, 41, 0, 0, -1, -1, -1, 1, 0),   # 居住者(非就業)
    (1, 2, 4, 35, 1, 1, 2, -1, -1, 2, 0),    # 従業者(在区就業)
    (2, 0, 0, 42, 1, -1, 2, -1, 3, 2, 1),    # 通勤者(域外常住)
    (3, 5, 1, 9, 1, -1, -1, 3, 2, 3, 0),     # 通学者
    (4, 1, 3, 27, 0, -1, -1, -1, 1, 4, 0),   # 来街者(私事)
    (5, 7, 3, 20, 0, -1, -1, -1, 1, 4, 1),   # 訪日来街者
    (6, 8, 5, 35, 1, -1, 2, -1, 0, 5, 0),    # 乗務員
    (7, 4, 5, 48, 0, -1, 2, -1, -1, 0, -1),  # 指令(素材なし)
    (8, 3, 4, 11, 1, 0, -1, 3, -1, 1, 1),    # 学齢の住民
    (9, 6, 3, 33, 1, -1, -1, -1, 2, 3, 1),   # 定期来街者
]

#: プール素材(層 → 行の list)。``build.pop.pool`` と同じ jsonl。
POOL: dict[str, list[dict]] = {
    "L1": [
        {"id": "L1_0", "age": 41, "gender": "男", "occupation": "年金生活者",
         "bedtime_min": 1350, "sleep_steps": 45, "workplace_scope": "none"},
        {"id": "L1_1", "age": 11, "gender": "女", "occupation": "小学生",
         "school_stage": "小学校", "bedtime_min": 1290, "sleep_steps": 54},
    ],
    "L2": [
        {"id": "L2_0", "age": 35, "gender": "女", "occupation": "店長",
         "shift_pattern": {"open": "09:00", "close": "18:00", "days": "mon-fri",
                           "rotates": False},
         "work_days": "mon-fri", "bedtime_min": 1380, "sleep_steps": 42,
         "residence_line": ""},
        {"id": "L2_1", "age": 42, "gender": "女", "occupation": "深夜スタッフ",
         "shift_pattern": {"open": "09:00", "close": "18:00", "days": "mon-fri",
                           "rotates": False},
         "work_days": "mon-fri", "bedtime_min": 600, "sleep_steps": 40,
         "residence_line": "川崎・多摩方面"},
    ],
    "L3": [
        {"id": "L3_0", "age": 9, "gender": "女", "occupation": "小学生",
         "school_stage": "小学校", "visit_cadence": "school_day",
         "residence_line": "目黒方面", "bedtime_min": 1260, "sleep_steps": 57},
        {"id": "L3_1", "age": 33, "gender": "女", "occupation": "フリーランス",
         "visit_cadence": "weekly", "residence_line": "世田谷方面",
         "bedtime_min": 1400, "sleep_steps": 40},
    ],
    "L4": [
        {"id": "L4_0", "age": 27, "gender": "男", "occupation": "会社員",
         "visit_purpose": "買い物", "visit_rate": 0.12, "is_foreign": False,
         "bedtime_min": 1410, "sleep_steps": 41},
        {"id": "L4_1", "age": 20, "gender": "男", "occupation": "販売・サービス",
         "visit_purpose": "観光・見物", "visit_rate": 0.31, "is_foreign": True,
         "bedtime_min": 50, "sleep_steps": 41},
    ],
    "L5": [
        {"id": "L5_0", "age": 35, "gender": "女", "occupation": "駅員", "role": "駅員",
         "post": "改札", "duty_pattern": {"days": "all", "rotates": True, "shift_hours": 8},
         "bedtime_min": 1420, "sleep_steps": 41},
    ],
}

#: POI(営業エンベロープの種)。(poi_id, cat, subcat, 7日×区間 JSON)
POIS: list[tuple[str, str, str | None, str]] = [
    ("p_a", "shop", None, "[[[600,1320]]]*7"),
    ("p_b", "food", None, "[[[420,1320]]]*7"),
    ("p_c", "shop", "convenience", "[[[0,1440]]]*7"),
    ("p_d", "leisure", None, "[[[720,1380]]]*7"),
]


def _expand(spec: str) -> str:
    body, _, _ = spec.partition("]*7")
    return json.dumps([json.loads(body + "]")[0] for _ in range(7)])


def _write(path: Path, cols: dict[str, list]) -> None:
    pq.write_table(pa.table({k: pa.array(v) for k, v in cols.items()}), path)


def write_pool(root: Path, pool: dict[str, list[dict]] | None = None) -> Path:
    """``data/persona_pool_v2`` 相当を作る。"""
    pool = POOL if pool is None else pool
    root.mkdir(parents=True, exist_ok=True)
    (root / "meta.json").write_text(
        json.dumps({"layer_counts": {k: len(v) for k, v in pool.items()}}, ensure_ascii=False),
        encoding="utf-8",
    )
    for layer, rows in pool.items():
        d = root / layer
        d.mkdir(exist_ok=True)
        with open(d / "part-0000.jsonl", "w", encoding="utf-8") as fh:
            for r in rows:
                fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return root


def write_population(world: Path, agents: list[tuple] = None) -> Path:
    """``w16_population.parquet`` 相当(W17 が読む列だけ)。"""
    rows = AGENTS if agents is None else agents
    _write(
        world / "w16_population.parquet",
        {
            "agent_id": [r[0] for r in rows],
            "kind": [r[1] for r in rows],
            "purpose": [r[2] for r in rows],
            "age": [r[3] for r in rows],
            "sex": [r[4] for r in rows],
            "home_cell": [r[5] for r in rows],
            "work_cell": [r[6] for r in rows],
            "school_cell": [r[7] for r in rows],
            "direction_node": [r[8] for r in rows],
            "pool_layer": [r[9] for r in rows],
            "pool_index": [r[10] for r in rows],
        },
    )
    return world / "w16_population.parquet"


@pytest.fixture()
def world_dir(tmp_path: Path) -> Path:
    """W17 が読む最小の world_dir。"""
    d = tmp_path / "world"
    d.mkdir()
    write_population(d)
    _write(
        d / "w6_poi.parquet",
        {
            "poi_id": [p[0] for p in POIS],
            "cat": [p[1] for p in POIS],
            "subcat": [p[2] for p in POIS],
        },
    )
    _write(
        d / "w7_plan_spec.parquet",
        {"poi_id": [p[0] for p in POIS], "content": [_expand(p[3]) for p in POIS]},
    )
    # W12 生成用重み(時間帯カーブの出所)。朝に山を置いた粗い形。
    purposes = ["自宅－勤務", "自宅－通学", "私事", "自宅－私事"]
    peaks = {"自宅－勤務": 8, "自宅－通学": 8, "私事": 11, "自宅－私事": 11}
    node, purp, hour, w = [], [], [], []
    for p in purposes:
        for h in range(24):
            node.append("ext_rail_jr_yamanote")
            purp.append(p)
            hour.append(h)
            w.append(float(np.exp(-0.5 * ((h - peaks[p]) / 2.5) ** 2)))
    _write(
        d / "w12_generation_weights.parquet",
        {"node_id": node, "purpose": purp, "hour": hour, "weight": w},
    )
    return d


@pytest.fixture()
def data_dir(tmp_path: Path) -> Path:
    """``ctx.data`` 相当(プールだけ)。"""
    root = tmp_path / "data"
    write_pool(root / "persona_pool_v2")
    return root


def response_row(agent_id: int, text: str, completion_tokens: int = 0) -> dict:
    """``tools/gen/fleet_gen.py`` 形式の応答 1 行。"""
    return {
        "id": str(agent_id),
        "rep": 0,
        "model": "Qwen3-8B-INT8",
        "endpoint": "http://127.0.0.1:8100",
        "text": text,
        "finish_reason": "stop",
        "prompt_tokens": 350,
        "completion_tokens": completion_tokens or max(1, len(text) // 2),
        "latency_s": 1.0,
    }


def write_responses(path: Path, rows: list[dict]) -> Path:
    with open(path, "w", encoding="utf-8") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    return path


def mock_week(facts, row: int) -> str:
    """その体の事実に**素直に従った**応答本文(= プロンプトの指示どおりの出力)。

    修復がほとんど働かない形にして、「修正率<20%」ゲートの陽性側を作る。
    """
    visit = int(facts.visit_days[row])
    acts: list[V.Act] = []
    if visit:
        for d in range(7):
            if not (visit >> d) & 1:
                continue
            acts += [
                V.Act(d, 600, 630, V.ACT_RIDE, V.PLACE_STATION),
                V.Act(d, 630, 780, V.ACT_SHOP, V.PLACE_SHOP),
                V.Act(d, 780, 840, V.ACT_MEAL, V.PLACE_FOOD),
                V.Act(d, 840, 900, V.ACT_RIDE, V.PLACE_OUTSIDE),
            ]
        return V.format_schedule(acts)

    lo = int(facts.work_open[row])
    hi = min(1_380, int(facts.work_close[row]))
    duty = int(facts.duty_activity[row])
    at_home = int(facts.home_cell[row]) >= 0
    place = V.PLACE_SCHOOL if duty == V.ACT_SCHOOL else V.PLACE_WORK
    # 各日 4 行以上・支度と食事と移動を含む(短縮形式の規則 3 に従った「素直な」応答)
    for d in range(7):
        works = duty >= 0 and (int(facts.work_days[row]) >> d) & 1 and 0 <= lo < hi
        if at_home:
            acts.append(V.Act(d, 0, 420, V.ACT_SLEEP, V.PLACE_HOME))
            acts.append(V.Act(d, 420, 480, V.ACT_PREP, V.PLACE_HOME))
        if works:
            acts.append(V.Act(d, max(480, lo - 60), lo, V.ACT_MOVE, V.PLACE_STATION))
            acts.append(V.Act(d, lo, hi, duty, place))
            acts.append(V.Act(d, hi, min(1_440, hi + 45), V.ACT_MEAL, V.PLACE_FOOD))
            acts.append(V.Act(d, min(1_440, hi + 45), min(1_440, hi + 90), V.ACT_MOVE,
                              V.PLACE_HOME if at_home else V.PLACE_OUTSIDE))
        else:
            acts.append(V.Act(d, 600, 660, V.ACT_MOVE, V.PLACE_STATION))
            acts.append(V.Act(d, 660, 780, V.ACT_SHOP, V.PLACE_SHOP))
            acts.append(V.Act(d, 780, 840, V.ACT_MEAL, V.PLACE_FOOD))
            acts.append(V.Act(d, 840, 900, V.ACT_MOVE,
                              V.PLACE_HOME if at_home else V.PLACE_OUTSIDE))
        if at_home:
            acts.append(V.Act(d, 1_380, 1_440, V.ACT_SLEEP, V.PLACE_HOME))
    acts.sort(key=lambda a: (a.day, a.start))
    out: list[V.Act] = []
    for a in acts:  # 同日の重なりを先に潰す(素直な応答を作るのが目的)
        if out and out[-1].day == a.day and a.start < out[-1].end:
            continue
        out.append(a)
    return V.format_schedule(out)


def simple_week(
    *,
    work: tuple[int, int] = (540, 1080),
    days: tuple[int, ...] = (0, 1, 2, 3, 4),
    with_shop: bool = True,
) -> str:
    """検査に使う「素直な週」の応答本文(全て語彙内・重なりなし)。"""
    acts: list[V.Act] = []
    for d in range(7):
        acts.append(V.Act(d, 0, 420, V.ACT_SLEEP, V.PLACE_HOME))
        acts.append(V.Act(d, 420, 480, V.ACT_PREP, V.PLACE_HOME))
        if d in days:
            acts.append(V.Act(d, 480, work[0], V.ACT_MOVE, V.PLACE_WORK))
            acts.append(V.Act(d, work[0], work[1], V.ACT_WORK, V.PLACE_WORK))
            acts.append(V.Act(d, work[1], min(1440, work[1] + 60), V.ACT_MOVE, V.PLACE_HOME))
        elif with_shop:
            acts.append(V.Act(d, 660, 780, V.ACT_SHOP, V.PLACE_SHOP))
            acts.append(V.Act(d, 780, 840, V.ACT_MEAL, V.PLACE_FOOD))
        acts.append(V.Act(d, 1_320, 1_440, V.ACT_SLEEP, V.PLACE_HOME))
    return V.format_schedule(acts)
