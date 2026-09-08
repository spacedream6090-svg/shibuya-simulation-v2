"""core.serialize のテスト: checkpoint 往復一致と M7(膨張率 ≤2.0x)。

M7 の分母の読みは ``core.serialize`` の docstring 参照(**非圧縮**シリアライズ長を分母にする=
「v1事故13.6倍の再発防止」の読み)。参考値として圧縮後ファイルに対する比も表示する。
"""

from __future__ import annotations

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from shibuya.core import serialize as S
from shibuya.core.soa import Registry

N_AGENTS = 5_000


def _filled_registry(n: int = N_AGENTS, seed: int = 0) -> Registry:
    """縮小ラン相当(5,000体)のレジストリ。ランダム値=圧縮が効かない=厳しい側。"""
    reg = Registry.for_agents(n)
    rng = np.random.default_rng(seed)
    reg.declare("pos_xy", np.float32, (2,), byte_budget_per_agent=8, mechanism=True, doc="M2 位置")
    reg.declare("cell_id", np.int32, byte_budget_per_agent=4, mechanism=True, doc="M2 所属セル")
    reg.declare("facing_q", np.uint8, byte_budget_per_agent=1, mechanism=False, doc="M12 向き")
    reg.declare("habit", np.uint8, (64, 20), byte_budget_per_agent=1_280, mechanism=True, doc="M3 縮小版")
    reg.pos_xy[:] = rng.random((n, 2), dtype=np.float32)
    reg.cell_id[:] = rng.integers(0, 453, n)
    reg.facing_q[:] = rng.integers(0, 256, n)
    reg.habit[:] = rng.integers(0, 256, (n, 64, 20))
    return reg


def test_roundtrip_and_m7_bloat(tmp_path, capsys):
    reg = _filled_registry()
    path = tmp_path / "checkpoint.npz.zst"
    saved = S.save_registry(reg, path)
    assert saved.state_hash == reg.state_hash()

    loaded = S.load_registry(path)
    assert loaded.state_hash() == reg.state_hash()
    assert loaded.n_entities == reg.n_entities
    assert [d.name for d in loaded.decls] == [d.name for d in reg.decls]
    assert [d.mechanism for d in loaded.decls] == [d.mechanism for d in reg.decls]
    assert np.array_equal(loaded.habit, reg.habit)
    assert loaded.bytes_total() == reg.bytes_total()

    m = S.measure_bloat(path)
    with capsys.disabled():
        print("\n[M7] " + m.as_text())
    assert m.ram_bytes_after_load == reg.bytes_total()
    assert m.ratio <= S.M7_MAX_BLOAT_RATIO, m.as_text()
    # 参考値(圧縮後ファイル基準)も取れること
    assert m.ratio_vs_file > 0
    assert m.within_m7


def test_zeros_registry_shows_why_denominator_matters(tmp_path, capsys):
    """全ゼロ=zstd がよく効く場合。非圧縮基準の比は 1.0 付近、圧縮後基準は跳ね上がる。"""
    reg = Registry.for_agents(N_AGENTS)
    reg.declare("habit", np.uint8, (64, 20), byte_budget_per_agent=1_280, mechanism=True, doc="M3")
    path = tmp_path / "zeros.npz.zst"
    S.save_registry(reg, path)
    m = S.measure_bloat(path)
    with capsys.disabled():
        print(f"\n[M7 zeros] {m.as_text()}")
    assert m.ratio <= S.M7_MAX_BLOAT_RATIO
    assert m.ratio_vs_file > 10.0, "圧縮後を分母にすると『膨張率』が圧縮率になってしまう"


def test_load_detects_tampering(tmp_path):
    reg = _filled_registry(64)
    path = tmp_path / "ck.npz.zst"
    S.save_registry(reg, path)
    raw = path.read_bytes()
    path.write_bytes(raw[:-3])  # 末尾を壊す
    with pytest.raises(Exception):
        S.load_registry(path)


@settings(max_examples=10, deadline=None)
@given(n=st.integers(min_value=1, max_value=200), seed=st.integers(min_value=0, max_value=1000))
def test_property_roundtrip_preserves_state_hash(tmp_path_factory, n, seed):
    reg = _filled_registry(n, seed)
    path = tmp_path_factory.mktemp("ck") / "r.npz.zst"
    S.save_registry(reg, path)
    assert S.load_registry(path).state_hash() == reg.state_hash()


def test_empty_registry_roundtrip(tmp_path):
    reg = Registry.for_agents(0)
    reg.declare("cell_id", np.int32, byte_budget_per_agent=4, mechanism=True, doc="M2")
    path = tmp_path / "empty.npz.zst"
    S.save_registry(reg, path)
    assert S.load_registry(path).state_hash() == reg.state_hash()
