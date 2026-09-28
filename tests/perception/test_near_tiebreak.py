"""小さいもの①(第300 Q107): B5 近接行の**距離の同点**を run_salt の決定論ハッシュで撹拌する。

- ``id``(旧)= C7 のベクトル化前の実装と同じ(``test_nearby_vectorized`` の基準)=旧 golden。
- ``hash``(既定)= k 人目の距離より近い人は全員・同点の人から足りない分を撹拌鍵の小さい順に。
  **文面と並び(id 昇順)は変えない**。同点が境に無い描画は両方で同じ。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.perception.renderer import (
    DEFAULT_NEAR_TIEBREAK,
    NEAR_TIEBREAKS,
    Renderer,
    check_near_tiebreak,
    near_tie_keys,
    near_tie_salt64,
)
from shibuya.world.state import World

from .test_nearby_vectorized import _reference_nearby_items, crowd


def tied_crowd(n: int = 200, *, near: str = "hash", seed: int = 7, same_xy: bool = True, salt: bytes | None = None):
    """1 セルに n 体が**同じ座標**(同じノード)=全員が同点。"""
    w = World.synthetic(n_cells=4, seed=3)
    a = AgentState(n)
    with a.writable():
        a.cell[:] = 0
        a.xy[:] = 50.0 if same_xy else np.random.default_rng(5).uniform(0.0, 100.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 3_000
        a.hunger[:] = 6
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    r = Renderer(w, a, seed=seed, near_tiebreak=near, near_salt=salt)
    r.prepare_tick(600)
    return r, a


def _ids(items):
    return [int(t.split("(")[0].split("-")[1]) for t, _ in items]


def test_modes_and_default():
    assert NEAR_TIEBREAKS == ("hash", "id") and DEFAULT_NEAR_TIEBREAK == "hash"
    assert check_near_tiebreak("id") == "id"
    with pytest.raises(ValueError):
        check_near_tiebreak("random")


def test_id_mode_is_the_previous_implementation_even_with_ties():
    r, a = tied_crowd(near="id")
    tc = r._tickc
    for i in range(a.n):
        assert r._nearby_items(i, 0, tc) == _reference_nearby_items(r, i, 0, tc)
    assert r.near_tie_breaks == 0


def test_hash_mode_mixes_who_is_seen_but_keeps_text_and_order():
    r, a = tied_crowd(near="hash")
    tc = r._tickc
    old_ids = []
    new_ids = []
    for i in range(a.n):
        got = r._nearby_items(i, 0, tc)
        ref = _reference_nearby_items(r, i, 0, tc)
        assert len(got) == len(ref)
        assert all(t.endswith("(未知)") and t.startswith("P-") for t, _ in got)   # 文面の形は同じ
        assert _ids(got) == sorted(_ids(got))                                     # 並びは id 昇順のまま
        assert [d for _, d in got] == [d for _, d in ref]                         # 同点=距離は同じ
        old_ids += _ids(ref)
        new_ids += _ids(got)
    assert r.near_tie_breaks == a.n
    # 旧: いつも行番号の小さい k 人(同じ人ばかり)/新: 観る体ごとに散る
    assert len(set(old_ids)) <= 6
    assert len(set(new_ids)) > 0.5 * a.n
    rho = np.corrcoef(np.bincount(new_ids, minlength=a.n), np.arange(a.n))[0, 1]
    assert abs(rho) < 0.2


def test_hash_mode_equals_id_when_no_tie_sits_on_the_boundary():
    """連続座標(同点なし)では両モードの出力がビットまで同じ(=同点の無いランは不変)。"""
    for mode in ("fixed", "ranking"):
        r_h, a = crowd(n=300, friends=True, mode=mode)
        assert r_h.near_tiebreak == "hash"
        tc = r_h._tickc
        for i in range(a.n):
            got = r_h._nearby_items(i, int(a.cell[i]), tc)
            ref = _reference_nearby_items(r_h, i, int(a.cell[i]), tc)
            assert [t for t, _ in got] == [t for t, _ in ref]
            assert [np.float64(d).tobytes() for _, d in got] == [np.float64(d).tobytes() for _, d in ref]
        assert r_h.near_tie_breaks == 0


def test_strictly_nearer_people_always_stay_in():
    """k 人目より近い人は撹拌に関係なく全員載る(同点の中からだけ選ぶ)。"""
    r, a = tied_crowd(n=40, near="hash")
    with a.writable():  # 観る体 0 と体 5 だけを 0.4 m ずらす=体 0 から見て体 5 は 0 m・残り 38 体は 0.4 m で同点
        a.xy[5] = (50.0, 50.4)
        a.xy[0] = (50.0, 50.4)
    r2 = Renderer(r.world, a, seed=7, near_tiebreak="hash")
    r2.prepare_tick(600)
    for seed_salt in (b"\x01" * 16, b"\x02" * 16, b"\x03" * 16):
        r3 = Renderer(r.world, a, seed=7, near_tiebreak="hash", near_salt=seed_salt)
        r3.prepare_tick(600)
        assert 5 in _ids(r3._nearby_items(0, 0, r3._tickc))  # 一番近い人は salt に依らず必ず載る
    assert 5 in _ids(r2._nearby_items(0, 0, r2._tickc))


def test_keys_are_deterministic_per_observer_and_salt():
    s1 = near_tie_salt64(b"\x01" * 16)
    s2 = near_tie_salt64(b"\x02" * 16)
    ids = np.arange(1_000)
    k1 = near_tie_keys(s1, 3, ids)
    assert k1.dtype == np.uint64 and np.array_equal(k1, near_tie_keys(s1, 3, ids))
    assert not np.array_equal(np.argsort(k1), np.argsort(near_tie_keys(s1, 4, ids)))   # 観る体で順が変わる
    assert not np.array_equal(np.argsort(k1), np.argsort(near_tie_keys(s2, 3, ids)))   # salt で順が変わる
    rank = np.argsort(np.argsort(k1))
    assert abs(np.corrcoef(rank, ids)[0, 1]) < 0.1


def test_default_salt_is_the_run_salt_of_the_seed():
    from shibuya.engine.run import run_salt_for

    r, _a = tied_crowd(seed=11)
    assert r._near_salt64 == near_tie_salt64(run_salt_for(11))
    r2, _ = tied_crowd(seed=11, salt=run_salt_for(12))
    assert r2._near_salt64 != r._near_salt64


def test_cli_flag_and_manifest():
    from shibuya import cli
    from shibuya.engine import run as RUN

    src = open(cli.__file__, encoding="utf-8").read()
    assert '"--near-tiebreak"' in src and "near_tiebreak=str(args.near_tiebreak)" in src
    assert '"--near-tiebreak"' in open(RUN.__file__, encoding="utf-8").read()
    with pytest.raises(ValueError):
        RUN.run_day(n_agents=10, ticks=2, near_tiebreak="random")


#: classical 1,500 体・seed 1・v3(実世界資産)の final(第300 Q107)。``id`` = HEAD bb44474 の既定と同じ(旧 golden)。
CLASSICAL_1500_GOLDEN = {
    "hash": ("e0a6f3f90fd8fe388312ff4f472239e59cc0194fed50accc4b5073d4bfdfc1a0", 26_845),
    "classical_tie_id": ("803f04417718539898234b865bb5c6c16b50d7328b28ebd6e412b2b4db311d3b", 26_753),
}


def test_classical_checkpoint_moves_with_hash_and_id_reproduces_the_old_one():
    from pathlib import Path

    from shibuya import cli

    world = Path("data/world/v2")
    if not (world / "w2_cells.parquet").exists():
        pytest.skip("実世界資産 data/world/v2 が無い")
    kw = dict(n_agents=1500, seed=1, world_dir=str(world), vocab_version="v3", policy="classical",
              chooser="classical")
    new = cli.run(**kw)
    old = cli.run(near_tiebreak="id", **kw)
    assert (new.final_hash, int(new.llm_calls)) == CLASSICAL_1500_GOLDEN["hash"]
    assert (old.final_hash, int(old.llm_calls)) == CLASSICAL_1500_GOLDEN["classical_tie_id"]
    m = new.run_manifest_fields()["near_tiebreak"]
    assert m["mode"] == "hash" and m["ties_broken"] > 0
    assert old.run_manifest_fields()["near_tiebreak"] == {"mode": "id", "ties_broken": 0, "tie_candidates": 0}
