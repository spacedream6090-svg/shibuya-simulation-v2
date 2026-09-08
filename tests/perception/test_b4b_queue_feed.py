"""B4b「近景」への待ち行列の差し込み(C4 後半で付けた唯一の可変欄)。

正典
- 知覚契約書 §2.2 ブロック表 B4b(40 tok・グループ ``cell``)・§2.4 ⑧
  「B0-B4b は同セル・同時間帯・同種別でバイト一致」。
- 同 §3 人物②「行列・人だかり・グループ(上位 k)」。
- チャネル上限表 ``B4b.near``(``max_items=2``・40 tok)。
"""

from __future__ import annotations

import numpy as np

from shibuya.agents.state import AgentKind, AgentState
from shibuya.perception import templates as T
from shibuya.perception.renderer import Renderer
from shibuya.world.state import World


def _build(n_agents: int = 40, n_cells: int = 16, seed: int = 3):
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n_agents)
    g = np.random.default_rng(seed)
    a.cell[:] = g.integers(0, n_cells, size=n_agents)
    a.xy[:] = g.uniform(0.0, 100.0, size=(n_agents, 2))
    a.kind[:] = AgentKind.VISITOR
    w.cells.density[:] = w.compute_density(a.cell)
    return w, a, Renderer(w, a, seed=seed)


def _queue_cell(w: World, poi: int) -> int:
    return int(w.pois.cell[poi])


def test_b4b_is_the_fixed_empty_phrase_without_queues():
    w, a, r = _build()
    r.prepare_tick(600)
    out = r.render(0, tick=600)
    assert out.blocks["B4b"] == T.TEMPLATES["B4b.near_empty"].encode("utf-8")


def test_queue_rows_reach_b4b_for_the_cell_that_holds_the_poi():
    w, a, r = _build()
    poi = 0
    cell = _queue_cell(w, poi)
    a.cell[: 4] = cell
    r.prepare_tick(600, queues=((poi, "コンビニ0000", 7),))
    inside = int(np.flatnonzero(np.asarray(a.cell) == cell)[0])
    outside = int(np.flatnonzero(np.asarray(a.cell) != cell)[0])
    line = r.render(inside, tick=600).blocks["B4b"].decode("utf-8")
    assert "行列" in line and "7人" in line and "コンビニ0000" in line
    assert r.render(outside, tick=600).blocks["B4b"] == T.TEMPLATES[
        "B4b.near_empty"
    ].encode("utf-8")


def test_b4b_stays_cell_shared_bytes_rule_eight():
    """規約⑧: 同じセルの 2 体は B4b もバイト一致(行列は POI 単位=セル共有)。"""
    w, a, r = _build()
    poi = 0
    cell = _queue_cell(w, poi)
    a.cell[:6] = cell
    r.prepare_tick(600, queues=((poi, "飲食0000", 3),))
    first = r.render(0, tick=600).blocks["B4b"]
    for i in range(1, 6):
        assert r.render(i, tick=600).blocks["B4b"] == first


def test_the_largest_queue_wins_inside_a_cell():
    w, a, r = _build()
    cell = _queue_cell(w, 0)
    same = [p for p in range(w.n_poi) if int(w.pois.cell[p]) == cell]
    if len(same) < 2:
        same = same + [same[0]]
    a.cell[:3] = cell
    r.prepare_tick(
        600, queues=((same[0], "小さい店", 2), (same[1], "大きい店", 9))
    )
    line = r.render(0, tick=600).blocks["B4b"].decode("utf-8")
    assert ("9人" in line) if same[0] != same[1] else ("2人" in line or "9人" in line)


def test_b4b_change_is_visible_to_the_change_detector():
    """B4b が変われば ``b4_field_rows``(起床条件 (i) が読む欄)も変わる。

    B4b はセル動的なのに ``hashes.b4_field_row`` の 4 欄に居ない。列を増やすと凍結形が
    動くので、行列のダイジェストを**顕著行為の欄へ畳んで**取りこぼしを 0 にしている。
    """
    w, a, r = _build()
    poi = 0
    cell = _queue_cell(w, poi)
    r.prepare_tick(600)
    base = r.b4_field_rows.copy()
    r.prepare_tick(600, queues=((poi, "コンビニ0000", 5),))
    now = r.b4_field_rows
    assert not np.array_equal(base[cell], now[cell])
    other = [c for c in range(w.n_cells) if c != cell]
    assert np.array_equal(base[other], now[other])


def test_b4b_respects_the_channel_token_budget():
    w, a, r = _build()
    poi = 0
    cell = _queue_cell(w, poi)
    a.cell[:2] = cell
    r.prepare_tick(600, queues=((poi, "とても長い名前の店" * 8, 12_345),))
    out = r.render(0, tick=600)
    assert out.tokens_est["B4b"] <= T.BLOCK_TOKEN_BUDGET["B4b"]
    assert out.group_tokens["cell"] <= T.GROUP_TOKEN_BUDGET["cell"]
