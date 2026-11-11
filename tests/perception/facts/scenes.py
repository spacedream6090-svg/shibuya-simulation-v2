"""第 1 期 1-2 の試験の道具(試験ではない): HEAD の描画の写しの読み込み・合成の場面・HEAD の双子の描画。

- ``head_module()``: ``head_renderer_136fdbb.py``(本体 HEAD ``136fdbb`` の ``src/shibuya/perception/renderer.py`` の
  バイトそのままの写し。固定は ``tests/_head_copy_pin.py`` の 3 つ=字面 ``HEAD_RENDERER_TEXT_SHA256``・文の順
  ``HEAD_RENDERER_ORDER``・読み込んだ後の意味 ``HEAD_RENDERER_REFS``)をモジュールとして読む。1-2 の前の描画の正。
- ``twin(r)``: 1-2 の描画 ``r`` と同じ世界・個体・資産・設定・口を持つ HEAD の描画を作る(``near_salt`` は値を写す)。
- ``build(...)``: 合成の世界と個体(内受容・所持金・手・行為・直前の結果がばらける)。
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

import numpy as np

from shibuya.agents.state import AgentKind, AgentState
from shibuya.world.model.state import World
from tests import _head_copy_pin as PIN

HERE = Path(__file__).resolve().parent
HEAD_FILE = HERE / "head_renderer_136fdbb.py"
#: 写しの固定(コードの区分の移動 段 4 の下ごしらえ・親の決定 10 を検収 M-1 の後に改めた。``tests/_head_copy_pin.py``)。
#: 段 4 で移す道具が import の文のモジュールの道を書き換えても(1 本の文を分けても)同じ値。覆わないのは読むモジュールの道と、
#: 束の中で 1 本の文を分けた文どうしの順だけ。
#: 元の全体の sha256(本体 HEAD 136fdbb の時点のバイト=``git show 136fdbb:src/shibuya/perception/renderer.py | sha256sum``)は
#: b1d82c4f05b90d36172d7cf8dc1b998e2fd8f599d3130df86b99981ac586cbfe(前はこの値で固定していた)。
#: 字面: import の文の束を印の行(字下げ・空行・置く名・注)に替えた全体の sha256。
HEAD_RENDERER_TEXT_SHA256 = "244494801a763377e5ee12625b7aaff786c5251a9388f52574b300c117d09c51"
#: 文の順: 束ごとに、元の文ごとの置く名(元の順)。
HEAD_RENDERER_ORDER = (
    (
        ("INTENT_NONE", "INTEROCEPTION_FIELDS", "RESULT_TEXT", "Activity", "ActivityKind", "AgentState", "IntentKind",
         "ResultCode", "WakeCondition"),
        ("blake3_hex", "blake3_u64", "xxh64"),
        ("ch",),
        ("H",),
        ("N",),
        ("T",),
        ("P_SEE_MEDIUM_RANGE", "SalientItem", "gate_stage1", "rank_by_saliency", "strip_imperatives"),
        ("CELL_SIZE_M", "WorldAssets", "array_sha256", "file_sha256"),
        ("LANDMARK_CATS", "World"),
        ("HOURS_PER_DAY", "MINUTES_PER_HOUR"),
    ),
)
#: 意味: 置いた名 → 指す物の元の置き場(``shibuya.`` を外した元のモジュールの名=移す道具に書き換えさせない)。
HEAD_RENDERER_REFS = {
    "Activity": "def agents.state Activity",
    "ActivityKind": "def agents.state ActivityKind",
    "AgentState": "def agents.state AgentState",
    "CELL_SIZE_M": "value world.assets 43b87f618caab482",
    "H": "module perception.hashes",
    "HOURS_PER_DAY": "value core.time_consts c2356069e9d1e79c",
    "INTENT_NONE": "value agents.state 1bad6b8cf97131fc",
    "INTEROCEPTION_FIELDS": "value agents.state 47be11d2bc67e62a",
    "IntentKind": "def agents.state IntentKind",
    "LANDMARK_CATS": "value world.state b22438302b3bb332",
    "MINUTES_PER_HOUR": "value core.time_consts 39fa9ec190eee7b6",
    "N": "module perception.normalize",
    "P_SEE_MEDIUM_RANGE": "value perception.attention e7f019dd7357f734",
    "RESULT_TEXT": "value agents.state ce2c4fc60c24eb90",
    "ResultCode": "def agents.state ResultCode",
    "SalientItem": "def perception.attention SalientItem",
    "T": "module perception.templates",
    "WakeCondition": "def agents.state WakeCondition",
    "World": "def world.state World",
    "WorldAssets": "def world.assets WorldAssets",
    "array_sha256": "def world.assets array_sha256",
    "blake3_hex": "def core.hashing blake3_hex",
    "blake3_u64": "def core.hashing blake3_u64",
    "ch": "module perception.channels",
    "file_sha256": "def world.assets file_sha256",
    "gate_stage1": "def perception.attention gate_stage1",
    "rank_by_saliency": "def perception.attention rank_by_saliency",
    "strip_imperatives": "def perception.attention strip_imperatives",
    "xxh64": "def core.hashing xxh64",
}
#: 双子に写す口(関数)。``memory_recall`` は 1-2 の側が引いた行を渡す(想起の計数を 2 回にしない)。
HOOKS = ("acquaintance_fn", "session_partner_fn", "named_closed_lookup", "weather_date_fn", "weather_words_fn",
         "weather_words_key_fn")

_HEAD: Any = None


def head_module() -> Any:
    global _HEAD
    if _HEAD is None:
        assert PIN.text_sha256(HEAD_FILE) == HEAD_RENDERER_TEXT_SHA256
        assert PIN.order_problems(HEAD_FILE, HEAD_RENDERER_ORDER) == []
        spec = importlib.util.spec_from_file_location("_p12_head_renderer", HEAD_FILE)
        mod = importlib.util.module_from_spec(spec)
        sys.modules["_p12_head_renderer"] = mod
        spec.loader.exec_module(mod)  # type: ignore[union-attr]
        assert PIN.ref_problems(mod, HEAD_FILE, HEAD_RENDERER_REFS) == []
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
