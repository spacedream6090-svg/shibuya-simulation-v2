"""B5 近接候補のベクトル化(C7 性能修正)が**挙動を 1 ビットも変えていない**ことの固定。

C7(390,067 体)の実測で llm 位相 46 s/tick・1 呼 17 ms になり、cProfile が
``_nearby_items`` のセル在席者ぶんの Python 反復(距離の辞書内包・``set(peers)``)と
``np.asarray(a.xy, float64)``(float32 SoA の**全体コピー**)を名指しした。

ここでは**修正前の実装を逐語で持ち**(``_reference_nearby_items``)、混雑した合成世界で
新実装と突き合わせる。順序・上位 k・知人常掲・同点処理・**距離の値(ビット一致)**まで見る。
"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import AgentKind, AgentState
from shibuya.perception import channels as ch
from shibuya.perception.renderer import Renderer, person_word
from shibuya.world.state import World


def _reference_nearby_items(self, i: int, cell: int, tc) -> list[tuple[str, float]]:
    """**C7 修正前の実装(逐語)**。比較の基準にするだけで、本体では使わない。"""
    a = self.agents
    if not (0 <= cell < tc.los_stage.size) or tc.cell_start.size == 0:
        return []
    lo, hi = int(tc.cell_start[cell]), int(tc.cell_end[cell])
    peers = tc.cell_order[lo:hi]
    peers = peers[peers != i]
    if peers.size == 0:
        return []
    los = int(tc.los_stage[cell])
    k = 3 if los <= 1 else (2 if los <= 3 else 1)
    xy = np.asarray(a.xy, dtype=np.float64)
    d2 = ((xy[peers] - xy[i]) ** 2).sum(axis=1)
    take = min(k, peers.size)
    sel = peers[np.argpartition(d2, take - 1)[:take]] if peers.size > take else peers
    friends = set(int(x) for x in self.acquaintances.get(i, ()))
    chosen = sorted(set(int(x) for x in sel) | (friends & set(int(x) for x in peers)))
    dist = {int(pj): float(np.sqrt(d2[t])) for t, pj in enumerate(peers)}
    return [
        (
            f"{person_word(j)}({'知人' if j in friends else '未知'})",
            max(dist.get(int(j), ch.RANKING_PRIORS["B5.near_person"].distance_m), 0.1),
        )
        for j in chosen
    ]


def crowd(n: int = 400, n_cells: int = 9, seed: int = 11, *, friends: bool = False, mode="fixed"):
    """混雑した合成世界(1 セルに数百体・密度段階が上がって k が 3/2/1 に散る)。"""
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n)
    g = np.random.default_rng(seed)
    with a.writable():
        # セル 0 に半分・残りを散らす(セル人口を偏らせて k の分岐を全部通す)
        a.cell[:] = g.integers(0, n_cells, size=n)
        a.cell[: n // 2] = 0
        a.xy[:] = g.uniform(0.0, 100.0, size=(n, 2))
        a.kind[:] = AgentKind.VISITOR
        a.money[:] = 3_000
        a.hunger[:] = 6
        a.last_result_tick[:] = 1
    w.cells.density[:] = w.compute_density(a.cell)
    acq = {i: [int(x) for x in g.choice(n, size=8, replace=False)] for i in range(0, n, 7)}
    r = Renderer(w, a, seed=7, budget_mode=mode, acquaintances=acq if friends else None)
    r.prepare_tick(600)
    return r, a


@pytest.mark.parametrize("with_friends", [False, True])
def test_vectorized_nearby_matches_the_previous_implementation(with_friends):
    """全個体で新旧の出力が**完全一致**(語も距離もビット一致)。"""
    r, a = crowd(friends=with_friends)
    tc = r._tickc
    n_checked = 0
    for i in range(a.n):
        cell = int(a.cell[i])
        new = r._nearby_items(i, cell, tc)
        old = _reference_nearby_items(r, i, cell, tc)
        assert [t for t, _ in new] == [t for t, _ in old], i
        assert [np.float64(d).tobytes() for _, d in new] == [
            np.float64(d).tobytes() for _, d in old
        ], i
        n_checked += 1
    assert n_checked == a.n


def test_agents_outside_the_tick_index_fall_back_like_before():
    """tick 索引に自分が居ない(セルが動いた)場合も旧実装と同じ(素通り)。"""
    r, a = crowd(n=60, n_cells=4)
    tc = r._tickc
    # 索引を作った後にセルだけ動かす(prepare_tick は呼び直さない)
    with a.writable():
        a.cell[0] = 3
    new = r._nearby_items(0, 3, tc)
    old = _reference_nearby_items(r, 0, 3, tc)
    assert [t for t, _ in new] == [t for t, _ in old]
    assert [d for _, d in new] == [d for _, d in old]


def test_empty_and_single_occupant_cells():
    r, a = crowd(n=12, n_cells=64)
    tc = r._tickc
    empty = [c for c in range(64) if int(tc.cell_end[c] - tc.cell_start[c]) == 0]
    assert empty, "空セルが無い(標本として不適)"
    assert r._nearby_items(0, empty[0], tc) == []
    assert r._nearby_items(0, -1, tc) == []
    assert r._nearby_items(0, 10_000, tc) == []


def test_tick_cache_arrays_are_consistent_with_the_soa():
    """``cell_pos``(逆置換)と ``cell_x/cell_y``(セル順の連続座標)の不変条件。"""
    r, a = crowd(n=200, n_cells=16)
    tc = r._tickc
    order = tc.cell_order
    assert np.array_equal(tc.cell_pos[order], np.arange(order.size))
    xy = np.asarray(a.xy, dtype=np.float64)
    assert np.array_equal(tc.cell_x, xy[order, 0])
    assert np.array_equal(tc.cell_y, xy[order, 1])
    assert tc.cell_x.flags["C_CONTIGUOUS"] and tc.cell_y.flags["C_CONTIGUOUS"]
    # CSR の範囲と実際のセルが一致する(``cell_pos`` の範囲比較で同セル判定ができる根拠)
    for c in range(16):
        lo, hi = int(tc.cell_start[c]), int(tc.cell_end[c])
        assert all(int(a.cell[j]) == c for j in order[lo:hi])


@pytest.mark.parametrize("mode", ["fixed", "ranking"])
def test_rendered_bytes_are_unchanged_in_both_modes(mode):
    """描画バイトが新旧で一致(B5 の行・順序・ランキングの距離まで)。"""
    r, a = crowd(n=300, mode=mode, friends=True)
    tc = r._tickc
    hashes_new = [r.render(i, tick=600, wake_reason=3).prompt_hash for i in range(0, 300, 3)]
    Renderer._nearby_items, saved = _reference_nearby_items, Renderer._nearby_items
    try:
        r2, a2 = crowd(n=300, mode=mode, friends=True)
        hashes_old = [r2.render(i, tick=600, wake_reason=3).prompt_hash for i in range(0, 300, 3)]
    finally:
        Renderer._nearby_items = saved
    assert hashes_new == hashes_old
    assert tc.cell_x.size == a.n
