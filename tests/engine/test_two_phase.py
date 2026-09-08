"""二相コミットのテスト: Phase B の資源裁定・順序不変(T3)・**書き込み口が1本であることの静的検査**。

正典: 運用設計書 §2.2(reserve→arbitrate→commit・pk 昇順・atomic 直接更新の禁止)・
§1.4 T3(並列不変性)・実装計画書 §6 P4(逐次ループ宣言)。
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

import numpy as np
import pytest
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

from shibuya.agents.state import Activity, AgentState, ResultCode
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.world.state import World

SRC = Path("src/shibuya")
SALT = b"salt-two-phase"


# ================================================================= 静的検査
def _calls_attr(path: Path, attr: str) -> bool:
    """``<何か>.<attr>(...)`` の**呼び出し**が有るか(文字列・コメントは AST が無視する)。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            if node.func.attr == attr:
                return True
    return False


def _calls_writable(path: Path) -> bool:
    return _calls_attr(path, "writable")


def test_thaw_is_never_called_outside_the_state_modules():
    """``.thaw(`` は書き込みガードの解除口。呼び出しは agents/state.py・world/state.py の内部だけ
    (層2レビュー指摘: thaw が公開だと AST 検査をすり抜ける)。"""
    callers = sorted(
        str(p).replace("\\", "/") for p in SRC.rglob("*.py") if _calls_attr(p, "thaw")
    )
    assert set(callers) <= {"src/shibuya/agents/state.py", "src/shibuya/world/state.py"}, callers


def test_only_resolve_writes_to_the_world():
    """``.writable(`` を**呼ぶ**のは engine/resolve.py だけ(=世界への書き込み口は1本)。"""
    callers = sorted(
        str(p).replace("\\", "/") for p in SRC.rglob("*.py") if _calls_writable(p)
    )
    assert callers == ["src/shibuya/engine/resolve.py"], callers


def test_frozen_state_rejects_direct_updates():
    """resolve の外からの直接更新は例外(運用設計書 §2.2「atomic 演算による直接更新は禁止」)。"""
    a = AgentState(4)
    w = World.synthetic(n_cells=4, seed=1)
    a.freeze()
    w.freeze()
    with pytest.raises(ValueError):
        a.money[0] = 1
    with pytest.raises(ValueError):
        w.pois.stock[0] = 0


_HOT_PATHS = (
    "engine/run.py",
    "engine/resolve.py",
    "engine/commit.py",
    "engine/change_detect.py",
)
#: 個体数ぶんの Python ループ(P4 で禁止)を疑う書き方。
_AGENT_LOOP_RE = re.compile(
    r"for\s+\w+\s+in\s+range\(\s*(?:n_agents|self\.n_agents|agents\.n|len\(agents\)|self\.n\b)"
)


def test_no_python_loop_over_agents_in_engine_hot_paths():
    """P4: エンジンのホットパスに**個体数ぶんの逐次ループ**を書かない。"""
    offenders = []
    for rel in _HOT_PATHS:
        text = (SRC / rel).read_text(encoding="utf-8")
        for m in _AGENT_LOOP_RE.finditer(text):
            line = text[: m.start()].count("\n") + 1
            offenders.append(f"{rel}:{line}: {m.group(0)}")
    assert not offenders, offenders


def test_every_hot_path_declares_its_sequential_loops():
    """P4「逐次ループの新設は宣言必須」= モジュール docstring に『逐次ループ宣言』がある。"""
    for rel in _HOT_PATHS:
        text = (SRC / rel).read_text(encoding="utf-8")
        assert "逐次ループ宣言" in text, rel
    # 新規ファイル全体でも同じ規律
    for rel in ("agents/state.py", "agents/schedule.py", "world/assets.py",
                "world/graph.py", "world/state.py", "engine/arbiter.py"):
        assert "逐次ループ宣言" in (SRC / rel).read_text(encoding="utf-8"), rel


# ================================================================= Phase B
def _world_and_agents(n_agents=12, n_cells=4, seed=1):
    w = World.synthetic(n_cells=n_cells, seed=seed)
    a = AgentState(n_agents)
    a.registry.cell[:] = np.arange(n_agents) % n_cells
    a.registry.node[:] = a.registry.cell
    a.registry.money[:] = 10_000
    a.registry.activity[:] = int(Activity.IDLE)
    return w, a


def _buy_intents(space, agents, poi_id, n, tick=600):
    ids = np.arange(n, dtype=np.int64)
    return C.IntentBatch(
        agent_id=ids,
        action_code=np.full(n, C.ACT_BUY, dtype=np.int8),
        target_id=np.full(n, poi_id, dtype=np.int32),
        resource_id=space.poi(np.full(n, poi_id)),
        t_notice_ns=np.full(n, C.tick_start_ns(tick), dtype=np.int64),
    )


def test_capacity_limits_the_winners():
    w, a = _world_and_agents(n_agents=10)
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    intents = _buy_intents(space, a, 0, 10)
    plan = C.arbitrate_resources(intents, 600, SALT, space, w.pois.stock, w.pois.capacity)
    cap = int(min(w.pois.capacity[0], w.pois.stock[0]))
    assert len(plan.confirmed) == cap
    assert len(plan.losers) == 10 - cap
    assert plan.n_unresolved == 10 - cap


def test_stock_zero_means_nobody_wins():
    w, a = _world_and_agents(n_agents=5)
    with w.writable():
        w.pois.stock[0] = 0
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    plan = C.arbitrate_resources(
        _buy_intents(space, a, 0, 5), 600, SALT, space, w.pois.stock, w.pois.capacity
    )
    assert len(plan.confirmed) == 0 and len(plan.losers) == 5


def test_free_intents_never_contend():
    w, a = _world_and_agents(n_agents=6)
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    ids = np.arange(6, dtype=np.int64)
    intents = C.IntentBatch(
        ids,
        np.full(6, C.ACT_WAIT, dtype=np.int8),
        np.full(6, -1, dtype=np.int32),
        np.full(6, -1, dtype=np.int32),
        np.zeros(6, dtype=np.int64),
    )
    plan = C.arbitrate_resources(intents, 0, SALT, space, w.pois.stock, w.pois.capacity)
    assert len(plan.confirmed) == 6 and plan.n_conflicts == 0


def test_conversation_partner_capacity_is_one():
    w, a = _world_and_agents(n_agents=6)
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    ids = np.array([1, 2, 3], dtype=np.int64)
    intents = C.IntentBatch(
        ids,
        np.full(3, C.ACT_TALK, dtype=np.int8),
        np.zeros(3, dtype=np.int32),
        space.partner(np.zeros(3)),
        np.zeros(3, dtype=np.int64),
    )
    plan = C.arbitrate_resources(intents, 0, SALT, space, w.pois.stock, w.pois.capacity)
    assert len(plan.confirmed) == 1 and len(plan.losers) == 2


def test_earlier_t_notice_wins_before_the_hash():
    """pk の第1要素=気づいた時刻(δ_perc)。先に気づいた人が先に取る(§2.3)。"""
    w, a = _world_and_agents(n_agents=4)
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    with w.writable():
        w.pois.capacity[0] = 1
    n = 4
    intents = C.IntentBatch(
        np.arange(n, dtype=np.int64),
        np.full(n, C.ACT_BUY, dtype=np.int8),
        np.zeros(n, dtype=np.int32),
        space.poi(np.zeros(n)),
        C.tick_start_ns(600) + np.array([500, 100, 900, 300], dtype=np.int64),
    )
    plan = C.arbitrate_resources(intents, 600, SALT, space, w.pois.stock, w.pois.capacity)
    assert plan.confirmed.agent_id.tolist() == [1]  # t_notice が最小


def test_arbitration_is_permutation_invariant():
    w, a = _world_and_agents(n_agents=20)
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    intents = _buy_intents(space, a, 0, 20)
    base = C.arbitrate_resources(intents, 600, SALT, space, w.pois.stock, w.pois.capacity)
    rng = np.random.default_rng(0)
    for _ in range(15):
        perm = intents.take(rng.permutation(20))
        plan = C.arbitrate_resources(perm, 600, SALT, space, w.pois.stock, w.pois.capacity)
        assert sorted(plan.confirmed.agent_id.tolist()) == sorted(base.confirmed.agent_id.tolist())
        assert sorted(plan.losers.agent_id.tolist()) == sorted(base.losers.agent_id.tolist())


def test_one_per_agent_keeps_the_llm_intent_over_the_engine_step():
    ids = np.array([3, 3, 5], dtype=np.int64)
    b = C.IntentBatch(
        ids,
        np.array([C.ENGINE_STEP, C.ACT_BUY, C.ENGINE_STEP], dtype=np.int8),
        np.array([1, 2, 3], dtype=np.int32),
        np.array([-1, 7, -1], dtype=np.int32),
        np.zeros(3, dtype=np.int64),
    )
    out = b.one_per_agent()
    assert out.agent_id.tolist() == [3, 5]
    assert int(out.action_code[0]) == C.ACT_BUY


# ================================================================= T3(順序不変)
def _run_phase_abc(order: list[int], tick: int = 600) -> tuple[str, str]:
    """与えた並び順で Phase B→C を回し、(個体ハッシュ, 世界ハッシュ) を返す。"""
    w, a = _world_and_agents(n_agents=12, n_cells=4, seed=2)
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    n = 12
    poi = (np.arange(n) % 4).astype(np.int32)
    intents = C.IntentBatch(
        agent_id=np.arange(n, dtype=np.int64),
        action_code=np.array(
            [C.ACT_BUY, C.ACT_WAIT, C.ACT_REST, C.ACT_MOVE] * 3, dtype=np.int8
        ),
        target_id=np.where(np.arange(n) % 4 == 3, (np.arange(n) % 4).astype(np.int32), poi),
        resource_id=np.where(np.arange(n) % 4 == 0, space.poi(poi), -1).astype(np.int32),
        t_notice_ns=C.tick_start_ns(tick) + (np.arange(n) % 3).astype(np.int64) * 1_000,
    )
    permuted = intents.take(np.asarray(order, dtype=np.int64))
    a.freeze()
    w.freeze()
    plan = C.arbitrate_resources(permuted, tick, SALT, space, w.pois.stock, w.pois.capacity)
    R.apply(plan.confirmed, plan.losers, a, w, tick)
    return a.state_hash(), w.state_hash()


@settings(max_examples=25, deadline=None, suppress_health_check=[HealthCheck.too_slow])
@given(order=st.permutations(list(range(12))))
def test_phase_c_outcome_is_independent_of_intent_order(order):
    """T3 相当: Phase A の intent の並び順を変えても Phase C の結果は同一。"""
    assert _run_phase_abc(list(order)) == _run_phase_abc(list(range(12)))


# ================================================================= 落選の意味論
def test_losers_get_the_failure_code():
    w, a = _world_and_agents(n_agents=10)
    space = C.ResourceSpace(w.n_poi, a.n, w.n_cells)
    intents = _buy_intents(space, a, 0, 10)
    a.freeze()
    w.freeze()
    plan = C.arbitrate_resources(intents, 600, SALT, space, w.pois.stock, w.pois.capacity)
    R.apply(plan.confirmed, plan.losers, a, w, 600)
    for aid in plan.losers.agent_id.tolist():
        assert int(a.last_result[aid]) == int(ResultCode.LOST_ARBITRATION)
        assert int(a.fail_streak[aid]) == 1
