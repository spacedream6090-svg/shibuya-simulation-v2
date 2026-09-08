"""build.geo — 世界データ構築 W0-W6/W11(地理レーン)。

各段階=純関数(入力ファイル群+パラメータ→出力+ヘッダ)。
仕様: docs/design/v2-world-data-build-spec.md §0 構築原則・§1 段階表・§2 D-W1〜D-W7/D-W9/D-W13。
実行: ``python -m shibuya.build.geo.run --out data/world/v2 [--stage W1 ...]``

層契約: build は manifest と core だけを import してよい。実行時に build を import してはならない。
"""

from __future__ import annotations

__all__ = ["STAGES"]

#: 実行順(W 番号順)。build_hash はこの順の出力 sha256 連結。
STAGES: tuple[str, ...] = ("W0", "W1", "W2", "W3", "W4", "W5", "W6", "W11")
