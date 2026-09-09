"""W16 母集団合成の統合テスト(実データ必須・CI では skip)。

検査
- 町丁目 **80 件**の ``JINKO`` が e-Stat 小地域(男女別人口総数)と 1 件残らず一致する
  (dbf 11 桁 KEY_CODE ↔ e-Stat area コードの対応を**仮定せず**、値の一致で確かめる)。
- 決定台帳の合否ライン(SRMSE 性別 <0.01・年齢 <0.13・方面 JSD <0.01・空セル 0%)。
- 再構築で出力とヘッダが**バイト一致**(D-W20 の T1)。
- 母集団を載せたランがエンジンの 1 日(短縮)を通り、保存則が保たれる。
"""

from __future__ import annotations

import hashlib
import shutil
import time
from pathlib import Path

import numpy as np
import pytest

from shibuya.agents.population import load_population, sample_population
from shibuya.build.geo import common as C
from shibuya.build.pop import w16_population as W16

REPO_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = REPO_ROOT / "data"
WORLD_DIR = DATA_DIR / "world" / "v2"
SHP = DATA_DIR / "realworld" / "estat" / "r2ka13113" / "r2ka13113.shp"
POOL = DATA_DIR / "persona_pool_v2" / "meta.json"

#: W16 が読む先行段階の出力(tmp_path へ写して純関数として回す)。
UPSTREAM = (
    "w2_cells.parquet",
    "w4_buildings.parquet",
    "w6_org.parquet",
    "w6_poi.parquet",
    "w11_station_exits.parquet",
    "w12_external_nodes.parquet",
    "w12_generation_weights.parquet",
)

pytestmark = pytest.mark.skipif(
    not (SHP.exists() and POOL.exists() and all((WORLD_DIR / f).exists() for f in UPSTREAM)),
    reason="data/ absent (CI)",
)


@pytest.fixture(scope="module")
def built(tmp_path_factory):
    out = tmp_path_factory.mktemp("w16")
    for name in UPSTREAM:
        shutil.copy2(WORLD_DIR / name, out / name)
    ctx = C.Ctx(data=DATA_DIR, out=out)
    t0 = time.perf_counter()
    res = W16.run(ctx)
    C.write_header(out, res)
    return out, res, time.perf_counter() - t0


def _gate(res: C.StageResult, name: str) -> dict:
    for g in res.gates:
        if g.name == name:
            return g.to_json()
    raise AssertionError(f"ゲート {name} が無い")


def test_all_gates_pass(built):
    out, res, _dt = built
    failed = [g.name for g in res.gates if not g.to_json()["pass"]]
    assert failed == [], failed


def test_eighty_chome_match_estat_population(built):
    """dbf の JINKO と e-Stat 小地域の人口総数が 80 件すべて一致する。"""
    _out, res, _dt = built
    assert _gate(res, "chome_jinko_match")["value"] == 80
    assert res.notes["chome_polygons"] == 80


def test_acceptance_lines_from_the_decision_ledger(built):
    """SRMSE 性別 <0.01・年齢 <0.13・方面 JSD <0.01・空セル 0%。"""
    out, res, _dt = built
    gates = C.load_json(out / "w16_gates.json")
    assert gates["srmse_sex_resident"] < 0.01
    assert gates["srmse_sex_worker"] < 0.01
    assert gates["srmse_age_resident"] < 0.13
    assert gates["jsd_direction_max"] < 0.01
    assert gates["empty_residential_cells"] == 0
    assert gates["residents_without_home_cell"] == 0


def test_public_anchors_are_the_source_of_the_targets(built):
    """目標体数が公的値から来ていること(在庫比ではない)。"""
    out, res, _dt = built
    cohorts = C.load_json(out / "w16_cohorts.json")
    by_name = {row["cohort"]: row for row in cohorts["cohorts"]}
    # 従業者の座席 = 経済センサス2021 町丁目別の従業者数(組織台帳の employees 総和)
    assert cohorts["org_seats"] == 222_849
    # 住民 = 国勢調査 町丁目人口 × 被覆率。区の夜間人口(243,883)の部分集合。
    assert 0 < by_name["resident"]["n"] < 243_883
    assert by_name["resident"]["n"] == by_name["resident"]["target"]
    # 通勤+在区就業 = 座席数(過不足なし)
    assert by_name["commuter"]["n"] + cohorts["residents_working_in_area"] == cohorts["org_seats"]
    # 40 万は「結果」: 公的値の積み上げが 30 万台後半〜40 万台に落ちること
    assert 300_000 <= cohorts["n_total"] <= 450_000
    assert res.notes["ward_anchors"]["夜間人口"] == 243_883
    assert res.notes["ward_anchors"]["昼間人口"] == 551_344
    assert res.notes["ward_anchors"]["流入"] == 363_883
    assert res.notes["ward_anchors"]["従業者(区・経済センサス2021)"] == 516_541


def test_pool_inventory_matches_meta(built):
    """① 在庫棚卸し: 層別件数が meta.json と一致(1,000,000 体)。"""
    _out, res, _dt = built
    assert res.notes["pool_counts"] == res.notes["pool_meta_counts"]
    assert sum(res.notes["pool_counts"].values()) == 1_000_000


def test_rebuild_is_byte_identical(tmp_path, built):
    """D-W20 T1: 同じ入力からの再構築で出力とヘッダがバイト一致する。"""
    src, res, _dt = built
    out = tmp_path / "again"
    out.mkdir()
    for name in UPSTREAM:
        shutil.copy2(WORLD_DIR / name, out / name)
    again = W16.run(C.Ctx(data=DATA_DIR, out=out))
    C.write_header(out, again)
    for name in [p.name for p in sorted(src.glob("w16_*"))] + ["W16.header.json"]:
        a = hashlib.sha256((src / name).read_bytes()).hexdigest()
        b = hashlib.sha256((out / name).read_bytes()).hexdigest()
        assert a == b, name
    assert again.input_hash == res.input_hash
    assert again.param_hash == res.param_hash


def test_output_columns_and_byte_size(built):
    """出力の列と 1 体あたりバイト(予算報告用の実測)。"""
    out, res, dt = built
    import pyarrow.parquet as pq

    table = pq.read_table(out / "w16_population.parquet")
    names = set(table.schema.names)
    assert {
        "agent_id", "kind", "age", "sex", "home_cell", "work_cell", "school_cell",
        "direction_node", "chome_key", "household_id", "org_id", "industry_key",
        "pool_layer", "pool_index",
    } <= names
    n = table.num_rows
    size = (out / "w16_population.parquet").stat().st_size
    print(
        f"\n[W16] {n:,} 体 / {dt:.1f}s / parquet {size:,} B = {size / n:.1f} B/体"
        f" / 世帯 {pq.read_table(out / 'w16_households.parquet').num_rows:,}"
    )
    assert size / n < 100.0  # 静的属性は 1 体 100 B 未満(M1 30KB/体 の内数)


def test_direction_shares_follow_w12_weights(built):
    """⑤ 方面 OD: 一様事前を捨て、W12 の生成用重みへ寄る。"""
    _out, res, _dt = built
    report = res.notes["direction"]
    assert "commuter" in report and report["commuter"]["n"] > 1_000
    shares = np.asarray(report["commuter"]["shares"])
    target = np.asarray(report["commuter"]["target"])
    assert shares.size == target.size >= 8
    # 一様(1/N)ではない=プールの ``residence_line`` 一様事前を捨てている
    assert float(np.abs(target - 1.0 / target.size).max()) > 0.02
    assert float(np.abs(shares - target).max()) < 0.01


# ------------------------------------------------------------------ ローダとエンジン結線
@pytest.mark.skipif(
    not (WORLD_DIR / "w16_population.parquet").exists(),
    reason="data/world/v2/w16_population.parquet が無い(先に W16 を回す)",
)
def test_loader_reads_the_published_population():
    pop = load_population(WORLD_DIR)
    assert pop is not None and pop.n > 300_000
    assert pop.age.max() < 120 and set(np.unique(pop.sex).tolist()) <= {0, 1}
    assert pop.home_cell.max() < 520 and pop.work_cell.max() < 520
    small = sample_population(pop, 5_000, seed=1)
    assert len(small) == 5_000
    assert int(small.reserved_mask.sum()) == int(pop.reserved_mask.sum())


@pytest.mark.skipif(
    not (WORLD_DIR / "w16_population.parquet").exists(),
    reason="data/world/v2/w16_population.parquet が無い(先に W16 を回す)",
)
def test_population_backed_run_conserves_money():
    """(f) 母集団を載せたランがエンジンを通る・保存則が保たれる・同 seed 同ハッシュ。"""
    from shibuya.engine.run import run_day
    from shibuya.world.state import World

    world = World.load(WORLD_DIR)
    a = run_day(n_agents=500, seed=4, ticks=240, checkpoint_every=120,
                world=world, world_dir=str(WORLD_DIR))
    assert a.conserved, (a.money_start, a.money_end)
    assert a.min_stock >= 0
    assert a.checkpoints[-1].population_hash != ""
    b = run_day(n_agents=500, seed=4, ticks=240, checkpoint_every=120,
                world=World.load(WORLD_DIR), world_dir=str(WORLD_DIR))
    assert a.final_hash == b.final_hash
    # 母集団を切ると別の世界になる(下限対照が効いている)
    c = run_day(n_agents=500, seed=4, ticks=240, checkpoint_every=120,
                world=World.load(WORLD_DIR), world_dir=str(WORLD_DIR), population=False)
    assert c.final_hash != a.final_hash
    assert c.checkpoints[-1].population_hash == ""


@pytest.mark.slow
@pytest.mark.skipif(
    not (WORLD_DIR / "w16_population.parquet").exists(),
    reason="data/world/v2/w16_population.parquet が無い(先に W16 を回す)",
)
def test_population_backed_full_day_5000_agents():
    """(f) 5,000 体 × 1 シミュ日(mock LLM)・保存則不変(予算行 W2 ≤10 分)。"""
    from shibuya.engine.run import run_day
    from shibuya.world.state import World

    t0 = time.perf_counter()
    res = run_day(n_agents=5_000, seed=1, world=World.load(WORLD_DIR),
                  world_dir=str(WORLD_DIR))
    dt = time.perf_counter() - t0
    print(f"\n[W16→1日ラン] 5,000体 {dt:.1f}s / 呼 {res.llm_calls:,}")
    assert res.conserved
    assert res.min_stock >= 0
    assert dt < 600.0  # 予算行 W2
