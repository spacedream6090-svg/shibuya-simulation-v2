"""第 1 期 1-2 の試験の道具(試験ではない): HEAD の描画の写しの読み込み・合成の場面・HEAD の双子の描画。

- ``head_module()``: ``head_renderer_136fdbb.py``(本体 HEAD ``136fdbb`` の ``src/shibuya/perception/renderer.py`` の
  バイトそのままの写し=sha256 は ``HEAD_RENDERER_SHA256``)をモジュールとして読む。1-2 の前の描画の正。
- ``twin(r)``: 1-2 の描画 ``r`` と同じ世界・個体・資産・設定・口を持つ HEAD の描画を作る(``near_salt`` は値を写す)。
- ``build(...)``: 合成の世界と個体(内受容・所持金・手・行為・直前の結果がばらける)。
"""

from __future__ import annotations

import hashlib
import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np

from shibuya.agents.state import AgentKind, AgentState
from shibuya.world.state import World

HERE = Path(__file__).resolve().parent
HEAD_FILE = HERE / "head_renderer_136fdbb.py"
#: 写しの sha256(本体 HEAD 136fdbb の blob と同じ=``git show 136fdbb:src/shibuya/perception/renderer.py | sha256sum``)。
HEAD_RENDERER_SHA256 = "b1d82c4f05b90d36172d7cf8dc1b998e2fd8f599d3130df86b99981ac586cbfe"
#: 双子に写す口(関数)。``memory_recall`` は 1-2 の側が引いた行を渡す(想起の計数を 2 回にしない)。
HOOKS = ("acquaintance_fn", "session_partner_fn", "named_closed_lookup", "weather_date_fn", "weather_words_fn",
         "weather_words_key_fn")

_HEAD: Any = None


def head_module() -> Any:
    global _HEAD
    if _HEAD is None:
        assert hashlib.sha256(HEAD_FILE.read_bytes()).hexdigest() == HEAD_RENDERER_SHA256
        spec = importlib.util.spec_from_file_location("_p12_head_renderer", HEAD_FILE)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_p12_head_renderer"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        _HEAD = mod
    return _HEAD


def twin(r: Any) -> Any:
    """1-2 の描画 ``r`` の HEAD の双子(同じ物を指す・設定と口を写す)。"""
    HD = head_module()
    h = HD.Renderer(
        r.world, r.agents, r.assets, clock_fn=r.clock_fn, seed=r.seed,
        acquaintances=r.acquaintances, watched_by=r.watched_by, budget_mode=r.budget_mode,
        strict_group_budget=r.strict_group_budget, signage_enabled=r.signage_enabled,
        signage_p_see=r.signage_p_see, intent_mode=r.intent_mode,
        vocab_version=r.vocab_version, role_words=r.role_words, near_tiebreak=r.near_tiebreak,
        near_salt=b"\x00" * 16, near_order=r.near_order, hunger_words=r.hunger_words,
    )
    h._near_salt64 = r._near_salt64
    for name in HOOKS:
        setattr(h, name, getattr(r, name))
    return h


def build(n_agents: int = 120, n_cells: int = 9, seed: int = 1, **agent_kw: Any) -> tuple[World, AgentState]:
    """合成世界+個体(同じセルに複数体・内受容と所持金と行為と直前の結果がばらける)。"""
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n_agents, **agent_kw)
    g = np.random.default_rng(seed)
    with a.writable():
        a.cell[:] = g.integers(0, n_cells, size=n_agents)
        a.xy[:] = g.uniform(0.0, 100.0, size=(n_agents, 2))
        # 同じ点に数人(距離の同点)
        a.xy[1:4] = a.xy[0]
        a.cell[1:4] = a.cell[0]
        a.kind[:] = g.integers(0, 4, size=n_agents)
        a.money[:] = g.integers(0, 8_000, size=n_agents)
        a.hunger[:] = g.integers(0, 11, size=n_agents)
        a.fatigue[:] = g.integers(0, 11, size=n_agents)
        a.thermal[:] = g.integers(0, 11, size=n_agents)
        a.holdings[:] = g.integers(0, 2, size=n_agents)
        a.activity[:] = g.integers(0, 8, size=n_agents)
        a.last_result[:] = g.integers(0, 19, size=n_agents)
        a.last_result_tick[:] = np.where(g.random(n_agents) < 0.2, -1, 1)
        a.kind[0] = AgentKind.VISITOR
    w.cells.density[:] = w.compute_density(a.cell)
    return w, a
