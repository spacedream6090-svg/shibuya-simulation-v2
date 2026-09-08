"""core.rng の性質テスト(hypothesis)。運用設計書 §1.4 T4(規模不変性)と G-5(決定的写像)を機械化。"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.core import rng

seeds = st.integers(min_value=0, max_value=rng.MASK64)
domains = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P"), blacklist_characters="\x1f"),
    min_size=1,
    max_size=24,
)
counters = st.lists(st.integers(min_value=0, max_value=rng.MASK64), min_size=0, max_size=4)


@settings(max_examples=60, deadline=None)
@given(seed=seeds, domain=domains, ctr=counters)
def test_same_inputs_same_stream(seed, domain, ctr):
    a = rng.stream(seed, domain, *ctr).integers(0, 2**63, size=8)
    b = rng.stream(seed, domain, *ctr).integers(0, 2**63, size=8)
    assert np.array_equal(a, b)


@settings(max_examples=60, deadline=None)
@given(seed=seeds, d1=domains, d2=domains)
def test_domain_separation(seed, d1, d2):
    """ドメインが違えば鍵が違う(同じドメイン名なら同じ鍵)。"""
    k1, k2 = rng.derive_key(seed, d1), rng.derive_key(seed, d2)
    assert (k1 == k2) == (d1 == d2)


@settings(max_examples=40, deadline=None)
@given(seed=seeds, domain=domains, agent_id=st.integers(min_value=0, max_value=10**6))
def test_t4_scale_invariance(seed, domain, agent_id):
    """個体 agent_id の列は、個体総数(5,000 か 5,001 か)に依存しない=カウンタベースの実証(T4)。

    集団側の実装が「個体 ID をカウンタに置く」規約を守れば、n を増やしても既存個体の列は変わらない。
    ここでは規約そのものを検査する: 同じ (seed, domain, agent_id) は他の個体の存在と無関係に同じ列を返す。
    """
    draws_alone = rng.stream(seed, domain, agent_id).random(4)
    # 「他の個体」を先に大量に引いても影響しない(状態を共有しない)
    for other in (agent_id + 1, agent_id + 5000, agent_id + 5001):
        rng.stream(seed, domain, other).random(4)
    draws_after = rng.stream(seed, domain, agent_id).random(4)
    assert np.array_equal(draws_alone, draws_after)


def test_master_seed_str_and_int_are_distinct_domains():
    """run_id(16進文字列)と整数 seed を取り違えても同じ鍵にならない。"""
    assert rng.derive_key(12345, "x") != rng.derive_key("12345", "x")


def test_rejects_bad_inputs():
    with pytest.raises(ValueError):
        rng.derive_key(1, "")
    with pytest.raises(ValueError):
        rng.derive_key(1, "a\x1fb")
    with pytest.raises(ValueError):
        rng.philox(1, "d", 1, 2, 3, 4, 5)
    with pytest.raises(TypeError):
        rng.derive_key(True, "d")  # type: ignore[arg-type]


def test_known_answer_is_stable():
    """既知解(golden・2026-09-08 固定): 変わったら鍵導出規約か numpy の Philox が変わった=宣言して更新する。"""
    assert rng.derive_key(0, "golden") == (3655438906380691500, 119420714387262803)
    assert rng.stream(0, "golden", 0).integers(0, 1000, size=3).tolist() == [218, 653, 484]
    assert rng.derive_key("run-abc", "agent.habit") == (17748353242256841054, 9819351675922092276)
    assert rng.stream("run-abc", "agent.habit", 42, 7).integers(0, 1000, size=3).tolist() == [842, 309, 266]
