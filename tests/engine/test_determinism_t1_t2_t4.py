"""決定論のテスト: T1/T2(同一 seed で checkpoint ハッシュ一致)・T4(規模不変)・M7(膨張率)。

正典: 運用設計書 §1.4 T2「同一 manifest×2 で**全 checkpoint ハッシュ一致**」・
T4「n=5,000 と 5,001 で既存個体の乱数列が不変」/ 予算宣言表 M7「直列化↔in-RAM 膨張率 ≤2.0x」。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents import schedule as S
from shibuya.core import serialize as SZ
from shibuya.engine.run import run_day, run_salt_for
from shibuya.world.state import World

SMALL = dict(n_agents=400, ticks=180, checkpoint_every=60, n_cells=25)


# ---------------------------------------------------------------- T1 / T2
def test_same_seed_gives_identical_checkpoint_hashes():
    a = run_day(seed=11, **SMALL)
    b = run_day(seed=11, **SMALL)
    assert [c.combined for c in a.checkpoints] == [c.combined for c in b.checkpoints]
    assert [c.agents_hash for c in a.checkpoints] == [c.agents_hash for c in b.checkpoints]
    assert [c.world_hash for c in a.checkpoints] == [c.world_hash for c in b.checkpoints]
    assert np.array_equal(a.diagnostics, b.diagnostics)


def test_different_seed_gives_different_hashes():
    a = run_day(seed=11, **SMALL)
    c = run_day(seed=12, **SMALL)
    assert a.final_hash != c.final_hash


def test_checkpoints_are_taken_at_the_declared_interval():
    res = run_day(seed=3, **SMALL)
    assert [c.tick for c in res.checkpoints] == [59, 119, 179]


def test_run_salt_is_a_deterministic_16_byte_digest():
    s1 = run_salt_for(7)
    assert isinstance(s1, bytes) and len(s1) == 16
    assert s1 == run_salt_for(7)
    assert s1 != run_salt_for(8)
    assert s1 != run_salt_for("7")


def test_run_is_reproducible_from_a_prebuilt_world():
    w1 = World.synthetic(n_cells=25, seed=11)
    w2 = World.synthetic(n_cells=25, seed=11)
    a = run_day(n_agents=400, seed=11, world=w1, ticks=120, checkpoint_every=60)
    b = run_day(n_agents=400, seed=11, world=w2, ticks=120, checkpoint_every=60)
    assert a.final_hash == b.final_hash


# ---------------------------------------------------------------- T4
def test_t4_scale_invariance_of_the_rng_stream():
    """n=5,000 と 5,001 で、先頭 5,000 体の抽選が**バイト一致**。"""
    a = S.synthesize(5_000, 99, n_cells=139)
    b = S.synthesize(5_001, 99, n_cells=139)
    assert np.array_equal(a.base_ticks, b.base_ticks[:5_000])
    assert np.array_equal(a.initial_money, b.initial_money[:5_000])
    assert np.array_equal(
        S.draw_words(99, 5_000), S.draw_words(99, 5_001)[:5_000]
    )


def test_t4_holds_for_the_run_initialisation():
    """個体数を 1 体増やしても、既存個体の初期状態は変わらない。"""
    a = run_day(n_agents=400, seed=5, ticks=1, checkpoint_every=1, n_cells=25)
    b = run_day(n_agents=401, seed=5, ticks=1, checkpoint_every=1, n_cells=25)
    for name in ("cell", "money", "kind"):
        left = a.agents.registry.field(name)  # type: ignore[attr-defined]
        right = b.agents.registry.field(name)  # type: ignore[attr-defined]
        assert np.array_equal(left, right[:400]), name


# ---------------------------------------------------------------- M7
def _measure(reg, path) -> SZ.BloatMeasurement:
    save = SZ.save_registry(reg, path)
    loaded = SZ.load_registry(path)
    assert loaded.state_hash() == save.state_hash
    return SZ.measure_bloat(path)


def test_m7_checkpoint_roundtrip_of_agents_and_world(tmp_path):
    res = run_day(n_agents=2_000, seed=4, ticks=60, checkpoint_every=60, n_cells=64)
    agents = res.agents  # type: ignore[attr-defined]
    world = res.world  # type: ignore[attr-defined]
    rows = []
    for label, reg in (
        ("agents", agents.registry),
        ("world.cells", world.cells),
        ("world.pois", world.pois),
    ):
        m = _measure(reg, tmp_path / f"{label}.npz.zst")
        rows.append((label, m))
        assert m.state_hash == reg.state_hash()
        assert m.within_m7, f"{label}: {m.as_text()}"
    print("\n[M7] checkpoint 往復(2,000体・64セル)")
    for label, m in rows:
        print(f"  {label:12s} {m.as_text()}")
    worst = max(m.ratio for _, m in rows)
    assert worst <= SZ.M7_MAX_BLOAT_RATIO


def test_checkpoint_hash_survives_a_reload(tmp_path):
    res = run_day(n_agents=500, seed=6, ticks=60, checkpoint_every=60, n_cells=25)
    agents = res.agents  # type: ignore[attr-defined]
    path = tmp_path / "agents.npz.zst"
    SZ.save_registry(agents.registry, path)
    reloaded = SZ.load_registry(path)
    assert reloaded.state_hash() == agents.state_hash()
    # 凍結状態は checkpoint に含まれない(読み直した配列は書ける)
    assert reloaded.field("money").flags.writeable


@pytest.mark.parametrize("n_agents", [1, 2])
def test_degenerate_sizes_do_not_crash(n_agents):
    res = run_day(n_agents=n_agents, seed=1, ticks=30, checkpoint_every=30, n_cells=9)
    assert res.conserved and len(res.checkpoints) == 1
