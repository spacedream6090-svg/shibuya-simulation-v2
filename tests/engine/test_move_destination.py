"""段 2b(行き先を対象欄から・D-112 ②): 移動の対象欄の解決順・近傍探索の上限・落選の分け・manifest。

正典: ``docs/design/v2-intent-chooser-implementation-agenda.md`` §2。
"""

from __future__ import annotations

import dataclasses
import re

import numpy as np
import pytest

from shibuya.agents.state import AgentState, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine.chooser import NearestChooser
from shibuya.engine.poi_target import (
    MOVE_BAD_TARGET,
    MOVE_SEARCH_RADIUS_CELLS,
    TargetResolver,
    move_resolution_summary,
)
from shibuya.engine.run import run_day
from shibuya.llm import LLMRequest
from shibuya.llm.contract import parse_target
from shibuya.llm.mock import MOCK_MOVE_TARGET_WORDS, MockLLM
from shibuya.world.state import World

NOON = 720
# 8 POI: セル 0 に 0..1、セル 1 に 2..3、セル 2 に 4..5、セル 3 に 6..7
CELLS = [0, 0, 1, 1, 2, 2, 3, 3]
CATS = ["shop", "office", "food", "shop", "food", "landmark", "food", "shop"]
NAMES = ["スターバックス", "事務所A", "スターバックス", "書店B", "カフェ・ベローチェ", "忠犬ハチ公像",
         "おむすび権米衛", "花屋C"]
# セル間距離: 0→1 150 m・0→2 300 m・0→3 600 m
DIST = np.array([[0, 150, 300, 600], [150, 0, 150, 450], [300, 150, 0, 300], [600, 450, 300, 0]],
                dtype=np.uint16)


def _world(open_from=None, visible=None):
    base = World.synthetic(n_cells=4, seed=1).assets
    n = base.n_poi
    assert n == len(CELLS)
    a = dataclasses.replace(
        base,
        poi_cell=np.asarray(CELLS, dtype=np.int32),
        poi_cat=tuple(CATS),
        poi_name=tuple(NAMES),
        poi_subcat=("",) * n,
        poi_open_from=np.asarray(open_from if open_from is not None else [0] * n, dtype=np.int16),
        poi_open_to=np.asarray([1440] * n, dtype=np.int16),
        cell_dist=DIST,
    )
    w = World(a)
    w._poi_visibility = np.zeros(n, dtype=np.int32)
    # 見えている POI(W8 の代わり): セル c → (POI, 視点数)
    vis = visible or {}
    off = np.zeros(5, dtype=np.int64)
    pois, nv = [], []
    for c in range(4):
        items = sorted(vis.get(c, []))
        pois += [p for p, _ in items]
        nv += [k for _, k in items]
        off[c + 1] = off[c] + len(items)
    w._visible_by_cell = (off, np.asarray(pois, dtype=np.int64), np.asarray(nv, dtype=np.int32))
    return w


def _agents(cells) -> AgentState:
    ag = AgentState(len(cells))
    ag.registry.cell[:] = np.asarray(cells)
    ag.registry.node[:] = 0
    return ag


def _move(w, cells, texts, radius=MOVE_SEARCH_RADIUS_CELLS):
    res = TargetResolver(world=w, chooser=NearestChooser(), seed=1, move_search_radius=radius)
    tg = [None if t is None else parse_target(t) for t in texts]
    out = res.resolve_move(_agents(cells), NOON, np.arange(len(cells)),
                           np.full(len(cells), C.ACT_MOVE), tg, np.ones(len(cells), dtype=bool))
    return out, res


def _place(w, c) -> str:
    band = {-1: "UG", 0: "GL", 1: "DECK"}[int(w.assets.cell_band[c])]
    return f"g{int(w.assets.cell_ix[c])}_{int(w.assets.cell_iy[c])}_{band}"


# ------------------------------------------------------------------ 解決順
def test_cell_id_including_the_cell_prefix_and_unknown_cells():
    w = _world()
    out, res = _move(w, [0, 0, 0, 0], [_place(w, 2), "セル" + _place(w, 3), "g99_99_GL", "C-0001"])
    assert out.tolist() == [2, 3, MOVE_BAD_TARGET, 1]
    s = move_resolution_summary(res.move_stats)
    assert s["cell"] == 3 and s["bad_target"]["cell_unknown"] == 1


def test_named_prefers_the_instance_in_the_current_cell_else_the_nearest():
    w = _world()
    out, res = _move(w, [0, 3, 0], ["スターバックス", "スターバックス", "忠犬ハチ公像"])
    assert out[0] == 0          # 今いるセルに同名の店がある
    assert out[1] == 1          # セル 3 から: セル 0(600 m)とセル 1(450 m)のうち近い方
    assert out[2] == 2          # 目印名 → その目印のセル
    s = move_resolution_summary(res.move_stats)
    assert s["named"] == 2 and s["named_landmark"] == 1


def test_category_order_in_cell_then_visible_then_nearby_within_the_radius():
    # 「飲食店」: セル 0 に food なし。見えている POI(W8)に food 4(セル 2)がある
    w = _world(visible={0: [(4, 30), (1, 99)]})
    out, res = _move(w, [0], ["飲食店"])
    assert out.tolist() == [2] and res.move_stats["category_visible"] == 1
    # 見えている POI に無ければ近い順(セル 1 の food 2=150 m)
    w = _world()
    out, res = _move(w, [0], ["飲食店"])
    assert out.tolist() == [1] and res.move_stats["category_nearby"] == 1
    # 今いるセルに候補があれば、そのセル(=動かない)
    out, res = _move(w, [1], ["飲食店"])
    assert out.tolist() == [1] and res.move_stats["category_in_cell"] == 1
    # 閉まっている店は候補にならない(セル 1 の food 2 が閉店 → セル 2 の food 4)
    w = _world(open_from=[0, 0, 900, 0, 0, 0, 0, 0])
    out, _ = _move(w, [0], ["飲食店"])
    assert out.tolist() == [2]


def test_the_nearby_search_stops_at_the_radius_and_fails_as_bad_target():
    w = _world(open_from=[0, 0, 900, 0, 900, 0, 0, 0])  # 開いている food はセル 3(600 m)だけ
    out, _ = _move(w, [0], ["飲食店"], radius=3)
    assert out.tolist() == [3]
    out, res = _move(w, [0], ["飲食店"], radius=2)   # 近い 2 セル(1, 2)に無い → 対象不正
    assert out.tolist() == [MOVE_BAD_TARGET]
    assert res.move_stats["bad_target:category_none_nearby"] == 1
    out, _ = _move(w, [0], ["飲食店"], radius=0)     # 0 = 近傍探索しない
    assert out.tolist() == [MOVE_BAD_TARGET]
    with pytest.raises(ValueError):
        TargetResolver(world=w, chooser=NearestChooser(), seed=1, move_search_radius=-1)


def test_none_and_explanations_keep_the_default_and_offmap_agents_are_untouched():
    w = _world()
    out, res = _move(w, [0, 0, -1], [None, "目的地", "飲食店"])
    assert out.tolist() == [-1, -1, -1]
    s = move_resolution_summary(res.move_stats)
    assert s["none_default"] == 2 and s["offmap_default"] == 1


# ------------------------------------------------------------------ commit / resolve
def _space(w, n):
    return C.ResourceSpace(n_poi=w.n_poi, n_agents=n, n_cells=w.n_cells)


def test_commit_uses_the_target_field_but_keeps_explicit_hints_and_wander():
    w = _world()
    ag = _agents([0, 0, 0, 0])
    res = TargetResolver(world=w, chooser=NearestChooser(), seed=1)
    home = np.array([3, 3, 3, 3])
    work = np.array([2, 2, 2, 2])
    hint = np.zeros(4, dtype=np.int64)
    hint[1] = C.TARGET_HINT_HOME
    move_dest = np.array([-1, -1, 1, -1])
    batch = C.intents_from_responses(
        ag, w, _space(w, 4), NOON, np.arange(4), np.zeros(4, dtype=np.int64),
        np.full(4, C.ACT_MOVE), home_cell=home, work_cell=work, target_hint=hint,
        move_dest=move_dest, targets=[parse_target("飲食店")] * 3 + [parse_target("なし")],
        poi_resolver=res,
    )
    # 体0: 対象欄のカテゴリ → セル 1 / 体1: 「帰宅」のヒント → 自宅 3 / 体2: あたり → 1 /
    # 体3: なし → 従来の既定(職場 2 に居ないので職場へ)
    assert batch.target_id.tolist() == [1, 3, 1, 2]


def test_bad_target_and_unreachable_are_counted_separately():
    w = _world()
    ag = _agents([0, 0])
    out = R.ResolveOutcome(tick=NOON)
    R._apply_move(ag, w, np.array([0, 1]), np.array([MOVE_BAD_TARGET, -1]), NOON, out, None)
    assert ag.registry.last_result[:2].tolist() == [int(ResultCode.BAD_TARGET),
                                                   int(ResultCode.UNREACHABLE)]
    assert out.n_move_bad_target == 1 and out.n_move_unreachable == 1


def test_run_day_records_move_resolution_in_the_manifest():
    res = run_day(n_agents=40, seed=1, ticks=30, renderer="stub", checkpoint_every=30)
    m = res.run_manifest_fields()
    assert m["move_search_radius"] == MOVE_SEARCH_RADIUS_CELLS == 5
    assert m["mock_move_target_p"] == 0.0
    mr = m["move_resolution"]
    assert {"cell", "named", "named_landmark", "category_in_cell", "category_visible",
            "category_nearby", "none_default", "offmap_default", "bad_target",
            "category_distance_m", "category_distance_mean_m", "result_bad_target",
            "result_unreachable"} == set(mr)
    with pytest.raises(ValueError):
        run_day(n_agents=10, seed=1, ticks=2, renderer="stub", mock_move_target_p=1.5)


# ------------------------------------------------------------------ mock の口
def test_mock_move_target_knob_is_off_by_default_and_uses_words_or_visible_names():
    req = LLMRequest(agent_id=7, tick=3, wake_class=1,
                     prompt="[B2 可視] 見えるもの: 物販店、飲食店、ヨンデル。")
    base = MockLLM(master_seed=1, vocab=("移動",), form="v3")
    off = MockLLM(master_seed=1, vocab=("移動",), form="v3", move_target_p=0.0)
    assert base.render(req) == off.render(req)  # 既定 0 = 1 バイトも変わらない
    on = MockLLM(master_seed=1, vocab=("移動",), form="v3", move_target_p=1.0)
    seen = set()
    for a in range(60):
        r = LLMRequest(agent_id=a, tick=3, wake_class=1, prompt=req.prompt)
        text = on.render(r)
        seen.add(re.search(r"対象: (\S+)", text).group(1))
    allowed = set(MOCK_MOVE_TARGET_WORDS) | {"物販店", "飲食店", "ヨンデル", "あたり"}
    assert seen <= allowed and "ヨンデル" in seen
    with pytest.raises(ValueError):
        MockLLM(master_seed=1, form="v3", move_target_p=2.0)
