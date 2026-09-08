"""agents.state のテスト: M9 バイト予算・§6 不応期表・書き込みガード。"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.agents.state import (
    N_WAKE_CONDITIONS,
    REFRACTORY_MINUTES,
    RESULT_TEXT,
    WAKE_CONDITION_CLASS,
    Activity,
    AgentKind,
    AgentState,
    ResultCode,
    WakeCondition,
)
from shibuya.core.types import EventClass


def test_m9_every_field_declared_and_within_m1():
    st = AgentState(64)
    rep = st.budget_report()
    assert rep.per_entity_byte_cap == 30_000  # 予算行 M1
    assert rep.within_cap
    assert rep.declared_bytes_per_entity == rep.actual_bytes_per_entity
    for f in rep.fields:
        assert f.within_budget, f.name
        assert f.declared_bytes_per_entity > 0
    print(f"\n[M1/M9] 宣言 {rep.declared_bytes_per_entity} B/体 "
          f"(上限 30,000 B/体・40万体で {rep.declared_bytes_per_entity * 400_000 / 1e9:.2f} GB)")


def test_core_fields_fit_m2_position_body_budget():
    """M2(位置・運動・身体)≤128B/体 に、起床機構(refractory)を除いた欄が収まる。"""
    st = AgentState(4)
    core = {
        "cell", "node", "band", "xy", "path_next_node", "target_node", "kind",
        "hunger", "fatigue", "thermal", "money", "holdings", "activity",
    }
    total = sum(d.byte_budget_per_entity for d in st.registry.decls if d.name in core)
    assert total <= 128, total


def test_refractory_table_matches_perception_contract_section6():
    """知覚契約書 §6 の不応期表(11 行)と 1 対 1。"""
    assert N_WAKE_CONDITIONS == 11 == len(WakeCondition)
    assert REFRACTORY_MINUTES == (0, 360, 150, 60, 15, 45, 10, 15, 5, 5, 30)
    assert REFRACTORY_MINUTES[WakeCondition.CONVERSATION_TURN] == 0  # 会話=床なし
    # 4クラス固定優先の順序(会話 > 計画境界 > 個体変化 > セル変化)
    assert WAKE_CONDITION_CLASS[WakeCondition.CONVERSATION_TURN] == EventClass.CONVERSATION
    assert WAKE_CONDITION_CLASS[WakeCondition.PLAN_GENERAL] == EventClass.PLAN_BOUNDARY
    assert WAKE_CONDITION_CLASS[WakeCondition.INTEROCEPTION] == EventClass.INDIVIDUAL
    assert WAKE_CONDITION_CLASS[WakeCondition.CELL_BLOCK] == EventClass.CELL


def test_refractory_array_shape():
    st = AgentState(8)
    assert st.refractory_until.shape == (8, N_WAKE_CONDITIONS)
    assert st.refractory_until.dtype == np.int32


def test_result_codes_cover_action_contract_failures():
    for code in ResultCode:
        assert code in RESULT_TEXT and RESULT_TEXT[code]
    assert RESULT_TEXT[ResultCode.NO_TRAIN] == "列車なし"
    assert RESULT_TEXT[ResultCode.OUT_OF_STOCK] == "在庫切れ"
    assert RESULT_TEXT[ResultCode.CLOSED] == "営業時間外"


def test_freeze_blocks_writes_and_writable_restores():
    st = AgentState(4)
    st.money[:] = 100
    st.freeze()
    assert st.frozen and not st.money.flags.writeable
    with pytest.raises(ValueError):
        st.money[0] = 1
    with st.writable():
        st.money[0] = 7
    assert st.frozen and int(st.money[0]) == 7
    assert not st.money.flags.writeable


def test_kind_field_is_not_shadowed_by_registry_kind():
    """``Registry.kind`` は文字列 ``"agent"``。同名フィールドが**配列で**引けること(回帰)。"""
    st = AgentState(4)
    assert st.registry.kind == "agent"
    assert isinstance(st.kind, np.ndarray) and st.kind.dtype == np.int8
    st.kind[:] = int(AgentKind.WORKER)
    assert int(st.registry.field("kind")[0]) == int(AgentKind.WORKER)


def test_defaults_use_minus_one_sentinels():
    st = AgentState(3)
    for name in ("cell", "node", "path_next_node", "target_node", "talk_partner"):
        assert np.all(st.registry.field(name) == -1), name
    assert np.all(st.wake_pending_class == -1)
    assert np.all(st.activity == int(Activity.IDLE))


def test_state_hash_changes_with_state():
    st = AgentState(4)
    h0 = st.state_hash()
    st.money[0] = 1
    assert st.state_hash() != h0


def test_unknown_field_raises():
    st = AgentState(2)
    with pytest.raises(AttributeError):
        _ = st.no_such_field
