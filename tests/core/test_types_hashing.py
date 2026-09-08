"""core.types / core.hashing のテスト(golden 値の凍結を含む)。

golden 値は**本実装が最初に出した値**であり、外部仕様との一致を主張するものではない
(バイト配置の規約は ``core.hashing`` の docstring=凍結対象)。値が変わるときは
「ハッシュ入力の規約を変えた」ことを意味する=宣言つきの改版が要る。
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.core import hashing as H
from shibuya.core import types as T


# ---------------- types ----------------
def test_class_rank_values_match_design_2_5():
    """運用設計書 §2.5: institution −1・conversation 0・plan_boundary 1・individual 2・cell 3。"""
    assert int(T.EventClass.INSTITUTION) == -1
    assert int(T.EventClass.CONVERSATION) == 0
    assert int(T.EventClass.PLAN_BOUNDARY) == 1
    assert int(T.EventClass.INDIVIDUAL) == 2
    assert int(T.EventClass.CELL) == 3
    assert list(T.CLASS_RANKS) == sorted(T.CLASS_RANKS)
    # 繰り延べ4クラス(知覚契約書 §6): 会話ターン > 計画境界 > 個体変化 > セル変化
    assert T.DEFERRAL_CLASSES == (
        T.EventClass.CONVERSATION,
        T.EventClass.PLAN_BOUNDARY,
        T.EventClass.INDIVIDUAL,
        T.EventClass.CELL,
    )


def test_dtypes_are_fixed():
    assert T.AGENT_ID_DTYPE == np.dtype(np.int32)
    assert T.CELL_ID_DTYPE == np.dtype(np.int32)
    assert T.RESOURCE_ID_DTYPE == np.dtype(np.int32)
    assert T.TICK_DTYPE == np.dtype(np.int64)
    assert T.T_SIM_NS_DTYPE == np.dtype(np.int64)


@settings(max_examples=100, deadline=None)
@given(
    tick=st.integers(min_value=-(10**6), max_value=T.max_tick()),
    offset_ns=st.integers(min_value=0, max_value=60 * 10**9 - 1),
)
def test_t_sim_ns_roundtrip(tick, offset_ns):
    v = T.t_sim_ns(tick, offset_ns)
    assert T.split_t_sim_ns(v) == (tick, offset_ns)
    assert T.INT64_MIN <= v <= T.INT64_MAX


def test_t_sim_ns_rejects_out_of_range_offset():
    with pytest.raises(ValueError):
        T.t_sim_ns(0, 60 * 10**9)
    with pytest.raises(ValueError):
        T.t_sim_ns(0, -1)


def test_t_sim_ns_overflow_is_loud():
    """int64 の限界(60秒tickで約 292 年)を黙って回さない。"""
    assert T.max_tick() == 153_722_866  # 全オフセットで int64 に収まる上限(境界修正 09-08)
    span = T.DEFAULT_TICK_SECONDS * T.NS_PER_SECOND
    T.t_sim_ns(T.max_tick(), span - 1)  # 上限 tick は最大オフセットでも収まる
    with pytest.raises(OverflowError):
        T.t_sim_ns(T.max_tick() + 1, span - 1)  # 1 つ上は最大オフセットで溢れる


def test_id_range_checks():
    assert T.as_agent_id(0) == 0
    assert T.as_cell_id(452) == 452
    with pytest.raises(ValueError):
        T.as_agent_id(-1)
    with pytest.raises(ValueError):
        T.as_resource_id(2**31)
    with pytest.raises(TypeError):
        T.as_agent_id(True)


# ---------------- hashing: golden ----------------
def test_blake3_known_vector():
    """blake3 の空入力(公開既知ベクトル)。"""
    assert H.blake3_hex(b"") == "af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262"


def test_priority_apply_wake_keys_are_pinned():
    assert H.priority_key(b"salt", 5, 3, 7) == 14412608829072322143
    assert H.apply_key(b"salt", 5, 7) == 6956806185499713271
    assert H.wake_tiebreak(b"salt", 5, 0, 7) == 14629333383363863323


def test_sha256_cbor_and_xxh64_are_pinned():
    assert (
        H.sha256_cbor({"a": 1, "b": [1, 2]})
        == "d517773978c2dfb475b7a2f9cb18784f0c30cc319a8e77bd04b4cdcb59eabec1"
    )
    assert H.xxh64(b"abc") == 4952883123889572249
    # CBOR 正準符号化はキー順に依らない
    assert H.sha256_cbor({"b": [1, 2], "a": 1}) == H.sha256_cbor({"a": 1, "b": [1, 2]})


def test_domain_tags_separate_uses():
    """同じ (salt, tick, id) 三つ組でも用途が違えば別の値(用途タグ)。"""
    assert H.priority_key(b"s", 1, 2, 3) != H.wake_tiebreak(b"s", 1, 2, 3)
    assert H.apply_key(b"s", 1, 2) != H.blake3_u64(b"s" + b"\x00" * 16)


# ---------------- hashing: 性質 ----------------
salts = st.binary(min_size=0, max_size=16)
ints = st.integers(min_value=0, max_value=2**31 - 1)


@settings(max_examples=100, deadline=None)
@given(salt=salts, tick=ints, rid=ints, aid=ints)
def test_priority_key_determinism_and_range(salt, tick, rid, aid):
    a = H.priority_key(salt, tick, rid, aid)
    b = H.priority_key(salt, tick, rid, aid)
    assert a == b
    assert 0 <= a < 2**64


@settings(max_examples=50, deadline=None)
@given(salt=salts, tick=ints, ids=st.lists(ints, min_size=0, max_size=32))
def test_array_variants_match_scalar(salt, tick, ids):
    agents = np.array(ids, dtype=np.int64)
    classes = np.zeros_like(agents)
    got = H.wake_tiebreak_array(salt, tick, classes, agents)
    want = np.array([H.wake_tiebreak(salt, tick, 0, int(a)) for a in agents], dtype=np.uint64)
    assert np.array_equal(got, want)
    got_p = H.priority_key_array(salt, tick, agents, agents)
    want_p = np.array([H.priority_key(salt, tick, int(a), int(a)) for a in agents], dtype=np.uint64)
    assert np.array_equal(got_p, want_p)


def test_array_variant_rejects_ragged_columns():
    with pytest.raises(ValueError):
        H.apply_key_array(b"", np.array([1, 2]), np.array([1]))
