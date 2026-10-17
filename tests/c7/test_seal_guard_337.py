# -*- coding: utf-8 -*-
"""〔第337 検収 L1〕tests/c7 の番人(``conftest._seal_hook``)の試験。

検証側・封印の名の道筋を開こうとすると、開く前に落ちる(無いファイルの名で確かめる=何も読まない)。較正側と
合成の置き場は落とさない。番人が効いているので、tests/c7 を全体試験に戻しても、fixture が混在・検証側の錨へ
戻れば落ちる。
"""
from __future__ import annotations

import pytest

from .conftest import REPO_ROOT, seal_hit

ANCH = REPO_ROOT / "docs" / "bench" / "anchors"


@pytest.mark.parametrize("rel", [
    "docs/bench/anchors/_absent_presence_validation_anchors_v0.json",
    "docs/bench/anchors/_absent_diversity_validation_anchors_v0.json",
    "docs/bench/anchors/_absent_presence_anchors_v0.json",
    "data/realworld/kddi_la/_absent.json",
    "data/realworld/_absent_boundary_counts.json",
    "data/calib/pt2018/_absent_pt6_b-4.csv",
])
def test_guard_refuses_before_opening(rel):
    p = REPO_ROOT / rel
    assert not p.exists()
    assert seal_hit(p)
    with pytest.raises(PermissionError, match="tests/c7"):
        open(p, "rb")  # noqa: SIM115 - 開く前に落ちる(無いファイル=FileNotFoundError より先)


def test_guard_lets_calibration_side_and_tmp_through(tmp_path):
    assert seal_hit(ANCH / "presence_calib_anchors_v0.json") is None
    assert seal_hit(tmp_path / "realworld" / "kddi_la" / "la.json") is None  # 合成の置き場はリポの外
    (ANCH / "presence_calib_anchors_v0.json").read_bytes()
