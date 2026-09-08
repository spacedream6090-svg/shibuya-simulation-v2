"""build.vis — 世界データ構築 W8/W9(可視性・影レーン)。

各段階=純関数(入力ファイル群+パラメータ→出力+ヘッダ)。ヘッダ形式は build.geo と同一。
仕様: docs/design/v2-world-data-build-spec.md §0 構築原則・§1 段階表 W8/W9・
§2 D-W9(可視性テーブル)/D-W10(影グリッドの時刻刻み=5分)。
接続: 知覚契約書 §4(p_see・顕著性)・予算書 M10(≤512MB)。

実行: ``python -m shibuya.build.vis.run --out data/world/v2 [--stage W8]``
      (通し実行は ``python -m shibuya.build.run --out data/world/v2``)

層契約: build は manifest と core だけを import してよい。実行時に build を import してはならない。
"""

from __future__ import annotations

__all__ = ["STAGES"]

#: 実行順(W 番号順)。W8 は W4/W5/W6/W10/W11 の出力を、W9 は W8 の場と W13 の再生日を使う。
STAGES: tuple[str, ...] = ("W8", "W9")
