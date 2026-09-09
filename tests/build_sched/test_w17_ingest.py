"""W17 取り込み: ストリーミング・最後の行を採る・ゲート・段階の 2 相・実データ。

対応する仕様行
- §1 W17 ゲート「PT 時間帯カーブとの JSD・修正率<20%・呼数=体数」
- §0-1 決定論(段階=純関数・応答 jsonl は**入力資産**として ``input_hash`` に入る)
- §0-8「LLM 呼は 3 段のみ」= 段階は LLM を呼ばない(応答が無くても落ちない)
"""

from __future__ import annotations

import json
import shutil
import time
from pathlib import Path

import numpy as np
import pytest

from shibuya.build.geo import common as C
from shibuya.build.sched import run as SCHED_RUN
from shibuya.build.sched import vocab as V
from shibuya.build.sched import w17_schedule as W17

from .conftest import (
    AGENTS,
    POIS,
    _expand,
    _write,
    mock_week,
    response_row,
    simple_week,
    write_pool,
    write_population,
    write_responses,
)

DATA_WORLD = Path("data/world/v2")
REAL_POPULATION = DATA_WORLD / "w16_population.parquet"
REAL_POOL = Path("data/persona_pool_v2/meta.json")


# ---------------------------------------------------------------- 段階の 2 相
def test_stage_writes_prompts_without_responses(world_dir: Path, data_dir: Path):
    """応答が無くても段階は落ちない(プロンプトだけ書いて「応答未取得」を報告)。"""
    res = W17.run(C.Ctx(data=data_dir, out=world_dir))
    assert res.all_passed
    assert (world_dir / W17.PROMPTS_NAME).exists()
    assert not (world_dir / W17.SCHEDULE_NAME).exists()
    gates = {g.name: g.to_json() for g in res.gates}
    assert gates["responses_present"]["value"] is False
    assert gates["n_calls_equals_n_agents"]["value"] == len(AGENTS)
    assert res.notes["hour_curve_source"].startswith("W12")


def test_stage_freezes_when_responses_are_present(world_dir: Path, data_dir: Path):
    """応答があれば parquet + ゲート json を書き、``input_hash`` に応答 SHA が入る。"""
    ctx = C.Ctx(data=data_dir, out=world_dir)
    first = W17.run(ctx)
    write_responses(
        world_dir / "w17_responses.jsonl",
        [response_row(r[0], simple_week()) for r in AGENTS],
    )
    res = W17.run(ctx)
    assert (world_dir / W17.SCHEDULE_NAME).exists()
    assert (world_dir / W17.GATES_NAME).exists()
    assert res.input_hash != first.input_hash  # 応答が入力資産に入った
    gates = {g.name: g.to_json() for g in res.gates}
    assert gates["responses_present"]["pass"]
    assert gates["response_rate"]["value"] == 1.0
    assert gates["raking_lowers_jsd"]["pass"]
    assert res.catalog_classes == ["週次活動スケジュール表"]
    report = json.loads((world_dir / W17.GATES_NAME).read_text(encoding="utf-8"))
    assert report["n_agents"] == len(AGENTS)
    assert report["n_skeleton_fallback"] <= len(AGENTS)


def test_stage_is_deterministic(world_dir: Path, data_dir: Path):
    """同じ入力で 2 回走らせて出力 SHA が一致する(D-W20 再構築テスト)。"""
    ctx = C.Ctx(data=data_dir, out=world_dir)
    write_responses(
        world_dir / "w17_responses.jsonl",
        [response_row(r[0], simple_week()) for r in AGENTS],
    )
    a = W17.run(ctx)
    b = W17.run(ctx)
    assert a.param_hash == b.param_hash
    assert [o["sha256"] for o in a.outputs] == [o["sha256"] for o in b.outputs]


# ---------------------------------------------------------------- 取り込みの規約
def test_last_row_wins_for_duplicate_ids(world_dir: Path, data_dir: Path):
    """fleet_gen の resume で同じ id が二度書かれたら**最後の行**を採る。"""
    old = V.format_schedule([V.Act(d, 0, 60, V.ACT_REST, V.PLACE_HOME) for d in range(7)])
    rows = [response_row(r[0], old) for r in AGENTS]
    rows += [response_row(r[0], simple_week()) for r in AGENTS]
    write_responses(world_dir / "w17_responses.jsonl", rows)
    rep, cols = W17.ingest(world_dir, data_dir)
    assert rep.n_response_rows == 2 * len(AGENTS)
    assert rep.n_with_response == len(AGENTS)
    assert int(cols["activity_code"].size) > 7 * len(AGENTS)  # 古い方(7 行)ではない


def test_missing_responses_fall_back_to_skeleton(world_dir: Path, data_dir: Path):
    """応答の無い体は骸格で埋め、**修正率に全件計上される**(ゲートが落ちる)。"""
    write_responses(
        world_dir / "w17_responses.jsonl",
        [response_row(AGENTS[0][0], simple_week())],
    )
    rep, cols = W17.ingest(world_dir, data_dir)
    assert rep.n_with_response == 1
    assert rep.n_skeleton == len(AGENTS) - 1
    assert rep.modified_rate > W17.GATE_MODIFIED_RATE
    assert rep.response_rate < W17.GATE_RESPONSE_RATE
    assert set(np.unique(cols["agent_id"])) <= {r[0] for r in AGENTS}


def test_broken_responses_only_lose_their_own_lines(world_dir: Path, data_dir: Path):
    text = simple_week().replace("0900-1800 勤務 職場", "0900-1800 瞑想 温泉宿泊所")
    write_responses(
        world_dir / "w17_responses.jsonl", [response_row(r[0], text) for r in AGENTS]
    )
    rep, _ = W17.ingest(world_dir, data_dir)
    assert rep.parse_bad.get("unknown_activity", 0) == 5 * len(AGENTS)  # 平日 5 日ぶん
    assert rep.n_skeleton == 0
    assert 0.0 < rep.parse_fail_rate < 0.2


def test_output_columns_and_ordering(world_dir: Path, data_dir: Path):
    write_responses(
        world_dir / "w17_responses.jsonl",
        [response_row(r[0], simple_week()) for r in AGENTS],
    )
    _, cols = W17.ingest(world_dir, data_dir)
    assert set(cols) == {
        "agent_id", "day", "seq", "start_min", "end_min",
        "activity_code", "place_kind", "target_cell",
    }
    key = (cols["agent_id"].astype(np.int64) * 10_000
           + cols["day"].astype(np.int64) * 100 + cols["seq"].astype(np.int64))
    assert np.all(np.diff(key) > 0)  # (agent, day, seq) の厳密昇順
    assert cols["start_min"].min() >= 0
    assert cols["end_min"].max() <= V.MINUTES_PER_DAY
    assert np.all(cols["end_min"] > cols["start_min"])
    # 自宅/職場/学校だけがセルまで解決される
    resolved = cols["target_cell"] >= 0
    assert set(np.unique(cols["place_kind"][resolved])) <= {
        V.PLACE_HOME, V.PLACE_WORK, V.PLACE_SCHOOL
    }


def test_write_schedule_roundtrips(world_dir: Path, data_dir: Path):
    write_responses(
        world_dir / "w17_responses.jsonl",
        [response_row(r[0], simple_week()) for r in AGENTS],
    )
    _, cols = W17.ingest(world_dir, data_dir)
    rec = W17.write_schedule(world_dir, cols)
    assert rec["rows"] == int(cols["agent_id"].size)
    got = C.read_parquet_columns(world_dir / W17.SCHEDULE_NAME)
    assert got["agent_id"] == cols["agent_id"].tolist()
    assert rec["bytes"] / max(1, len(AGENTS)) < 30_000  # 予算 M1(≤30KB/体)の内側


# ---------------------------------------------------------------- 規模(1,000 体・モック)
@pytest.fixture()
def big_world(tmp_path: Path) -> tuple[Path, Path, int]:
    """1,000 体のモック世界(ストリーミング取り込みの規模テスト)。"""
    n = 1_000
    world, data = tmp_path / "bw", tmp_path / "bd"
    world.mkdir()
    rows = []
    for i in range(n):
        k, p, layer, idx = (2, 4, 2, 0) if i % 2 else (1, 3, 4, 0)
        rows.append((i, k, p, 30 + i % 40, i % 2, i % 3 - 1, 2 if k == 2 else -1,
                     -1, i % 4, layer, idx))
    write_population(world, rows)
    _write(world / "w6_poi.parquet",
           {"poi_id": [q[0] for q in POIS], "cat": [q[1] for q in POIS],
            "subcat": [q[2] for q in POIS]})
    _write(world / "w7_plan_spec.parquet",
           {"poi_id": [q[0] for q in POIS], "content": [_expand(q[3]) for q in POIS]})
    node, purp, hour, w = [], [], [], []
    for p, peak in (("自宅－勤務", 8), ("私事", 11), ("自宅－通学", 8), ("自宅－私事", 11)):
        for h in range(24):
            node.append("n")
            purp.append(p)
            hour.append(h)
            w.append(float(np.exp(-0.5 * ((h - peak) / 2.0) ** 2)))
    _write(world / "w12_generation_weights.parquet",
           {"node_id": node, "purpose": purp, "hour": hour, "weight": w})
    write_pool(data / "persona_pool_v2")
    return world, data, n


def test_streaming_ingest_at_scale(big_world):
    """1,000 体をシャード 2 本の応答から取り込む(ストリーミング・壁時計を報告)。"""
    world, data, n = big_world
    facts = W17.build_facts(world, data)
    for s in range(2):
        write_responses(
            world / f"w17_responses.{s}of2.jsonl",
            [response_row(int(a), mock_week(facts, i))
             for i, a in enumerate(facts.agent_id) if i % 2 == s],
        )
    t0 = time.perf_counter()
    rep, cols = W17.ingest(world, data, facts=facts)
    dt = time.perf_counter() - t0
    assert rep.n_agents == n
    assert rep.n_with_response == n
    assert rep.response_rate == 1.0
    assert rep.n_skeleton == 0
    assert rep.modified_rate < W17.GATE_MODIFIED_RATE
    assert rep.rake.max_after <= rep.rake.max_before + 1e-12
    # 従業者は週 7 日ぶん・来街者は来訪日だけ(= 全体の平均は 16 活動/体前後)
    assert cols["agent_id"].size > 10 * n
    assert set(np.unique(cols["agent_id"])) == set(range(n))
    print(f"\n[W17 ingest] n={n} activities={cols['agent_id'].size} wall={dt:.2f}s "
          f"modified_rate={rep.modified_rate:.4f} "
          f"jsd {rep.rake.max_before:.4f}->{rep.rake.max_after:.4f}")


# ---------------------------------------------------------------- CLI
def test_cli_runs_and_accepts_shard(world_dir: Path, data_dir: Path, capsys):
    assert SCHED_RUN.parse_shard(None) == (0, 1)
    assert SCHED_RUN.parse_shard("2/8") == (2, 8)
    rc = SCHED_RUN.main(["--out", str(world_dir), "--data", str(data_dir), "--shard", "1/3"])
    assert rc == 0
    assert (world_dir / "w17_prompts.1of3.jsonl").exists()
    assert (world_dir / "W17.header.json").exists()


# ---------------------------------------------------------------- 実データ(skipif)
@pytest.mark.slow
@pytest.mark.skipif(
    not (REAL_POPULATION.exists() and REAL_POOL.exists()),
    reason="実資産(w16_population.parquet / persona_pool_v2)が無い",
)
def test_real_population_prompts(tmp_path: Path):
    """実データ: 件数=体数・平均入力トークン・プロンプト SHA を測って報告する。"""
    t0 = time.perf_counter()
    facts = W17.build_facts(DATA_WORLD, Path("data"))
    t_facts = time.perf_counter() - t0
    t1 = time.perf_counter()
    rec = W17.write_prompts(tmp_path, facts)
    t_prompts = time.perf_counter() - t1
    assert rec["rows"] == facts.n
    assert rec["prompt_tokens_mean"] <= W17.PROMPT_TOKEN_TARGET
    print(
        f"\n[W17 実データ] 体数={facts.n} 呼数={rec['rows'] * W17.REPEAT} "
        f"prompts_sha256={rec['sha256'][:16]}… bytes={rec['bytes']:,} "
        f"入力tok 平均={rec['prompt_tokens_mean']} 最大={rec['prompt_tokens_max']} "
        f"facts={t_facts:.1f}s prompts={t_prompts:.1f}s"
    )


# ---------------------------------------------------------------- ヘッダの決定論(W18/build_hash)
def test_header_is_byte_identical_across_two_builds(world_dir: Path, data_dir: Path,
                                                    tmp_path: Path):
    """``W17.header.json`` が 2 回の構築でバイト一致する(D-W20 の再構築テスト)。

    壁時計をヘッダに入れると W18 の input_hash → build_hash が毎回変わる
    (``tests/build_field/test_field_pipeline.py::test_rebuild_is_byte_identical`` が落ちた)。
    """
    write_responses(
        world_dir / "w17_responses.jsonl",
        [response_row(r[0], simple_week()) for r in AGENTS],
    )
    second = tmp_path / "world2"
    shutil.copytree(world_dir, second)
    a = W17.run(C.Ctx(data=data_dir, out=world_dir))
    b = W17.run(C.Ctx(data=data_dir, out=second))
    C.write_header(world_dir, a)
    C.write_header(second, b)
    assert (world_dir / "W17.header.json").read_bytes() == (
        second / "W17.header.json"
    ).read_bytes()
    assert a.input_hash == b.input_hash and a.param_hash == b.param_hash


def test_notes_carry_no_non_deterministic_values(world_dir: Path, data_dir: Path):
    """ヘッダの ``notes`` に時刻・壁時計・絶対パス・環境を入れない。"""
    res = W17.run(C.Ctx(data=data_dir, out=world_dir))
    blob = C.canonical_json_bytes(res.to_json()).decode("utf-8")
    assert "wall_clock" not in blob
    assert str(world_dir) not in blob and str(data_dir) not in blob
    for bad in ("elapsed", "timestamp", "\"ts\"", "perf_counter"):
        assert bad not in blob


# ---------------------------------------------------------------- パイロット標本
def test_pilot_prompts_are_per_kind_and_deterministic(world_dir: Path, data_dir: Path):
    facts = W17.build_facts(world_dir, data_dir)
    rows = W17.pilot_rows(facts, 1)
    assert np.array_equal(rows, W17.pilot_rows(facts, 1))  # 決定論
    assert np.all(np.diff(rows) > 0)  # 昇順・重複なし
    kinds = np.asarray(facts.kind)[rows]
    assert len(set(kinds.tolist())) == len(set(np.asarray(facts.kind).tolist()))
    for k in set(kinds.tolist()):  # 在庫のある種別から 1 体ずつ
        assert int((kinds == k).sum()) == 1
    with pytest.raises(ValueError):
        W17.pilot_rows(facts, 0)


def test_pilot_takes_up_to_per_kind_from_each_kind(world_dir: Path, data_dir: Path):
    facts = W17.build_facts(world_dir, data_dir)
    rows = W17.pilot_rows(facts, 40)  # 在庫より多い → ある分だけ
    assert rows.size == facts.n


def test_write_pilot_prompts(world_dir: Path, data_dir: Path):
    facts = W17.build_facts(world_dir, data_dir)
    rec = W17.write_pilot_prompts(world_dir, facts, 1)
    assert rec["path"] == W17.PILOT_PROMPTS_NAME
    assert rec["rows"] == len(rec["kinds"]) == 9  # 種別 9 つ × 1 体
    lines = (world_dir / W17.PILOT_PROMPTS_NAME).read_text(encoding="utf-8").splitlines()
    assert len(lines) == rec["rows"]
    got = [json.loads(x) for x in lines]
    assert all(g["temperature"] == W17.TEMPERATURE and g["repeat"] == 1 for g in got)
    # 本番の応答 glob と当たらない名前(誤って本番資産に混ざらない)
    assert not W17.PILOT_PROMPTS_NAME.startswith("w17_responses")
    assert W17.response_files(world_dir) == []


def test_pilot_cli_writes_only_the_sample(world_dir: Path, data_dir: Path):
    rc = SCHED_RUN.main(["--out", str(world_dir), "--data", str(data_dir), "--pilot", "2"])
    assert rc == 0
    assert (world_dir / W17.PILOT_PROMPTS_NAME).exists()
    assert not (world_dir / W17.PROMPTS_NAME).exists()  # 683 MB の本番ファイルは書かない
    assert not (world_dir / "W17.header.json").exists()  # ヘッダも書かない


def test_pilot_ingest_reports_without_writing_assets(world_dir: Path, data_dir: Path):
    facts = W17.build_facts(world_dir, data_dir)
    W17.write_pilot_prompts(world_dir, facts, 2)
    ids = [json.loads(x)["id"] for x in
           (world_dir / W17.PILOT_PROMPTS_NAME).read_text(encoding="utf-8").splitlines()]
    write_responses(
        world_dir / W17.PILOT_RESPONSES_NAME,
        [response_row(int(i), simple_week()) for i in ids],
    )
    rc = SCHED_RUN.main(["--out", str(world_dir), "--data", str(data_dir),
                         "--pilot", "2", "--pilot-ingest"])
    assert rc == 0
    assert not (world_dir / W17.SCHEDULE_NAME).exists()
    assert not (world_dir / W17.GATES_NAME).exists()
    assert not (world_dir / "W17.header.json").exists()


# ---------------------------------------------------------------- 適応 raking 予算
def _thin_week(n_lines: int) -> str:
    """1 日 ``n_lines`` 行だけの週(行数を減らすほど修復(穴埋め)が増える)。"""
    rows = [(600 + 60 * j, 630 + 60 * j, V.ACT_MEAL, V.PLACE_FOOD) for j in range(n_lines)]
    return V.format_schedule(
        [V.Act(d, s, e, a, p) for d in range(7) for (s, e, a, p) in rows]
    )


@pytest.mark.parametrize("n_lines", [1, 2, 3, 4, 5, 0])
def test_adaptive_budget_keeps_the_total_under_the_gate(big_world, n_lines: int):
    """修復率を振っても **raking がゲートを割らせない**(D-W17 (iii) 修正率<20%)。

    ``n_lines=0`` は「素直な応答」(``mock_week``)で修復率が低い場合。それ以外は 1 日
    ``n_lines`` 行だけの薄い応答で、修復(穴埋め・就寝補い)が重くなる。
    **不変条件**: 修復率が目標より下なら総修正率はゲート未満。修復率だけで目標を超えたら
    raking の予算は 0 で、raking は 1 行も動かさない(=悪化させない)。
    """
    world, data, n = big_world
    facts = W17.build_facts(world, data)
    texts = (
        [mock_week(facts, i) for i in range(facts.n)]
        if n_lines == 0
        else [_thin_week(n_lines)] * facts.n
    )
    write_responses(
        world / "w17_responses.jsonl",
        [response_row(int(a), t) for a, t in zip(facts.agent_id, texts)],
    )
    rep, _ = W17.ingest(world, data, facts=facts)
    repair_rate = rep.n_repair_modified / rep.n_considered
    # 予算は「目標 − 修復ぶん」から決まる(集計値だけの純関数=決定論)
    room = W17.ADAPTIVE_MODIFIED_TARGET * rep.n_considered - rep.n_repair_modified
    assert rep.rake.budget_rows == int(max(0.0, room))
    assert rep.rake.n_moved <= rep.rake.budget_rows
    if repair_rate < W17.ADAPTIVE_MODIFIED_TARGET:
        assert rep.modified_rate < W17.GATE_MODIFIED_RATE, (
            f"{n_lines}行/日: 修復 {rep.n_repair_modified} + raking {rep.rake.n_moved} "
            f"/ {rep.n_considered}"
        )
    else:  # 修復だけで枠を使い切った=raking は 1 行も足さない
        assert rep.rake.budget_rows == 0 and rep.rake.n_moved == 0
        assert rep.modified_rate == pytest.approx(repair_rate)


def test_adaptive_budget_is_zero_when_repair_already_fills_the_gate(big_world):
    """修復だけで枠を使い切る応答(骸格になる=全件修正)では raking を止める。"""
    world, data, n = big_world
    facts = W17.build_facts(world, data)
    write_responses(
        world / "w17_responses.jsonl",
        [response_row(int(a), "作れません") for a in facts.agent_id],
    )
    rep, _ = W17.ingest(world, data, facts=facts)
    assert rep.n_skeleton == n  # 全滅 → 骸格 → 修正率 1.0
    assert rep.rake.budget_rows == 0 and rep.rake.n_moved == 0
    assert rep.rake.jsd_after == rep.rake.jsd_before


def test_explicit_budget_overrides_the_adaptive_one(big_world):
    """ablation: 固定予算(旧 12%)を渡すと適応を上書きする(JSD 差の感度試験用)。"""
    world, data, n = big_world
    facts = W17.build_facts(world, data)
    write_responses(
        world / "w17_responses.jsonl",
        [response_row(int(a), mock_week(facts, i)) for i, a in enumerate(facts.agent_id)],
    )
    fixed, _ = W17.ingest(world, data, facts=facts, rake_budget_rows=0)
    adaptive, _ = W17.ingest(world, data, facts=facts)
    assert fixed.rake.n_moved == 0
    assert adaptive.rake.n_moved > 0
    assert adaptive.rake.max_after <= fixed.rake.max_after + 1e-12
    assert adaptive.modified_rate < W17.GATE_MODIFIED_RATE
