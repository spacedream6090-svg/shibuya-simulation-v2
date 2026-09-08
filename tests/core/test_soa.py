"""core.soa のテスト: M9(宣言なきフィールドはマージ不可)と state_hash の性質。"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.core import budget as B
from shibuya.core import soa


def _small_registry(n: int = 64) -> soa.Registry:
    reg = soa.Registry.for_agents(n)
    reg.declare("pos_xy", np.float32, (2,), byte_budget_per_agent=8, mechanism=True, doc="M2 位置")
    reg.declare("cell_id", np.int32, byte_budget_per_agent=4, mechanism=True, doc="M2 所属セル")
    reg.declare(
        "facing_q", np.uint8, byte_budget_per_agent=1, mechanism=False, doc="M12 向きの量子化"
    )
    return reg


# ---------------- 予算(M9/M1) ----------------
def test_agent_cap_comes_from_budget_row_m1():
    """個体あたり上限は予算行 M1(≤30KB/体)。KB は 10 進(M3 の 64×200B=12.8KB より)。"""
    rows = B.budget_by_id(B.load_budget_table())
    assert B.parse_limit(rows["M1"].declared) == (30.0, "KB/体")
    assert soa.default_per_entity_byte_cap("agent") == 30_000
    assert soa.default_per_entity_byte_cap("cell") is None
    reg = soa.Registry.for_agents(4)
    assert reg.per_entity_byte_cap == 30_000
    assert "M1" in reg.cap_source


def test_declare_requires_budget_tag_and_doc():
    reg = soa.Registry.for_agents(4)
    with pytest.raises(ValueError, match="M9"):
        reg.declare("a", np.int32, mechanism=True, doc="x")
    with pytest.raises(ValueError, match="mechanism"):
        reg.declare("b", np.int32, byte_budget_per_agent=4, doc="x")
    with pytest.raises(ValueError, match="doc"):
        reg.declare("c", np.int32, byte_budget_per_agent=4, mechanism=True)
    assert len(reg) == 0


def test_declare_rejects_actual_over_declared_and_total_over_cap():
    reg = soa.Registry.for_agents(4)
    with pytest.raises(ValueError, match="実バイト"):
        reg.declare("x", np.float64, byte_budget_per_agent=4, mechanism=True, doc="8B なのに 4B 宣言")
    with pytest.raises(ValueError, match="上限"):
        reg.declare(
            "habit", np.uint8, (40_000,), byte_budget_per_agent=40_000, mechanism=True, doc="cap 超え"
        )


def test_duplicate_and_bad_names_rejected():
    reg = _small_registry()
    with pytest.raises(ValueError, match="重複"):
        reg.declare("pos_xy", np.int32, byte_budget_per_agent=4, mechanism=True, doc="d")
    with pytest.raises(ValueError, match="不正"):
        reg.declare("2bad", np.int32, byte_budget_per_agent=4, mechanism=True, doc="d")


def test_budget_report_declared_vs_actual():
    reg = _small_registry(100)
    rep = reg.budget_report()
    assert rep.declared_bytes_per_entity == 13
    assert rep.actual_bytes_per_entity == 13
    assert rep.actual_bytes_total == 1300 == reg.bytes_total()
    assert rep.within_cap
    assert all(f.within_budget for f in rep.fields)
    assert [f.name for f in rep.fields] == ["pos_xy", "cell_id", "facing_q"]
    assert [f.mechanism for f in rep.fields] == [True, True, False]
    assert "M1" in rep.as_text()


def test_cell_registry_has_no_per_entity_cap_row():
    reg = soa.Registry.for_cells(453)
    assert reg.per_entity_byte_cap is None
    assert soa.CELL_CAP_BUDGET_ROW is None
    reg.declare("noise_db", np.float32, byte_budget_per_agent=4, mechanism=True, doc="B4 騒音")
    assert reg.bytes_total() == 453 * 4


# ---------------- state_hash ----------------
def test_state_hash_is_stable_and_order_sensitive():
    a = _small_registry()
    b = _small_registry()
    assert a.state_hash() == b.state_hash()

    c = soa.Registry.for_agents(64)
    c.declare("cell_id", np.int32, byte_budget_per_agent=4, mechanism=True, doc="M2 所属セル")
    c.declare("pos_xy", np.float32, (2,), byte_budget_per_agent=8, mechanism=True, doc="M2 位置")
    c.declare("facing_q", np.uint8, byte_budget_per_agent=1, mechanism=False, doc="M12")
    assert c.state_hash() != a.state_hash(), "宣言順が違えば別のハッシュ(順序も状態の一部)"


def test_state_hash_changes_on_any_byte_change():
    reg = _small_registry()
    h0 = reg.state_hash()
    reg.cell_id[7] = 1
    assert reg.state_hash() != h0
    reg.cell_id[7] = 0
    assert reg.state_hash() == h0


@settings(max_examples=60, deadline=None)
@given(
    idx=st.integers(min_value=0, max_value=63),
    value=st.integers(min_value=-(2**20), max_value=2**20),
)
def test_property_state_hash_changes_iff_bytes_change(idx, value):
    """性質: state_hash が変わる ⟺ 配列のバイト列が変わる。"""
    reg = _small_registry()
    before_bytes = bytes(reg.cell_id.tobytes())
    before_hash = reg.state_hash()
    reg.cell_id[idx] = value
    after_bytes = bytes(reg.cell_id.tobytes())
    after_hash = reg.state_hash()
    assert (before_bytes == after_bytes) == (before_hash == after_hash)


def test_attribute_and_field_access():
    reg = _small_registry()
    assert reg.field("pos_xy") is reg.pos_xy
    assert "pos_xy" in reg
    assert set(iter(reg)) == {"pos_xy", "cell_id", "facing_q"}
    with pytest.raises(AttributeError):
        _ = reg.nope
    with pytest.raises(KeyError):
        reg.field("nope")
