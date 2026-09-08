"""hashes / state: ハッシュ三役(§2.2/§5)と M12 バイト予算(§3.1/§7)。"""

from __future__ import annotations

import numpy as np
import pytest

from shibuya.perception import hashes as H
from shibuya.perception.state import PERCEPTION_BYTE_CAP, PerceptionState, heading_from_vector


# ---------------------------------------------------------------- ハッシュ三役
def test_block_hash_is_xxh64_of_the_rendered_bytes():
    from shibuya.core.hashing import xxh64

    data = "[B4 密度] 歩行者密度は段階Cです。".encode("utf-8")
    assert H.block_hash(data) == xxh64(data)
    assert H.block_hash(data) != H.block_hash(data + b" ")


def test_prefix_key_depends_on_order():
    a = H.prefix_key([1, 2, 3], ["B2", "B4", "B4b"])
    b = H.prefix_key([3, 2, 1], ["B2", "B4", "B4b"])
    c = H.prefix_key([1, 2, 3], ["B2", "B4", "B4b"])
    assert a == c and a != b
    with pytest.raises(ValueError):
        H.prefix_key([1, 2], ["B2"])


def test_should_resend_is_the_dormant_suppressor():
    assert H.should_resend(None, 7) is True  # 初回は必ず送る
    assert H.should_resend(7, 7) is False  # 変化なし → 再送しない
    assert H.should_resend(7, 8) is True


def test_field_row_hash_refines_the_rendered_bytes():
    """欄が同じ ⇒ 欄ハッシュが同じ(refinement の定義側)。"""
    rows = H.b4_field_row(
        np.array([0, 1, 1]), np.array([2, 2, 2]), np.array([0, 0, 0]), np.array([0, 0, 0])
    )
    hs = H.field_row_hashes(rows)
    assert hs[1] == hs[2] != hs[0]
    assert H.field_row_hash(rows[1]) == int(hs[1])


def test_b4_field_row_rejects_ragged_input():
    with pytest.raises(ValueError):
        H.b4_field_row(np.zeros(3), np.zeros(2), np.zeros(3), np.zeros(3))


# ---------------------------------------------------------------- M12
def test_m12_two_bytes_for_p_notice_state():
    """§3.1「向き量子化1 byte+課題従事フラグ1 byte=**2 byte/体**」。"""
    st = PerceptionState(8)
    rep = st.budget_report()
    per_field = {f.name: f.declared_bytes_per_entity for f in rep.fields}
    assert per_field["heading"] + per_field["task_flag"] == 2
    assert per_field["last_b2_hash"] + per_field["last_b4_hash"] == 16
    assert st.declared_bytes_per_agent == 18 <= PERCEPTION_BYTE_CAP
    assert rep.within_cap
    for f in rep.fields:
        assert f.within_budget, f.name
    print(f"\n[M12] 知覚側 {st.declared_bytes_per_agent} B/体 "
          f"(40万体で {st.declared_bytes_per_agent * 400_000 / 1e6:.1f} MB)")


def test_invocation_distance_is_not_double_declared_by_default():
    """``agents.state`` が既に持つので既定では宣言しない(M12 の二重計上を避ける)。"""
    from shibuya.agents.state import AgentState

    assert "invocation_distance" in dict(AgentState(2).registry.arrays)
    assert "invocation_distance" not in dict(PerceptionState(2).registry.arrays)
    standalone = PerceptionState(2, include_invocation_distance=True)
    assert standalone.declared_bytes_per_agent == 20 <= PERCEPTION_BYTE_CAP


def test_write_guard():
    st = PerceptionState(4)
    st.heading[:] = 3
    st.freeze()
    assert st.frozen and not st.heading.flags.writeable
    with pytest.raises(ValueError):
        st.heading[0] = 1
    with st.writable():
        st.heading[0] = 1
    assert st.frozen and int(st.heading[0]) == 1


def test_heading_quantization_16_sectors():
    dx = np.array([1.0, 0.0, -1.0, 0.0, 1.0])
    dy = np.array([0.0, 1.0, 0.0, -1.0, 1.0])
    q = heading_from_vector(dx, dy)
    assert list(q) == [0, 4, 8, 12, 2]
    assert q.dtype == np.uint8


def test_state_hash_changes_with_content():
    st = PerceptionState(4)
    h0 = st.state_hash()
    st.task_flag[0] = 1
    assert st.state_hash() != h0
