"""build.field — 世界データ構築 W7/W10/W12/W13(場・境界レーン)。

各段階=純関数(入力ファイル群+パラメータ→出力+ヘッダ)。ヘッダ形式は build.geo と同一。
仕様: docs/design/v2-world-data-build-spec.md §0 構築原則・§1 段階表 W7/W10/W12/W13・
§2 D-W8(営業時間・価格帯)/D-W11(静的騒音場)/D-W14(外界ノード)/D-W15(気象再生日)/D-W22(PT表)。
接続: 境界経済設計書 §1(U10 方面別外界ノード)・世界過程設計書 §2(PlanSpec 型)・知覚契約書 §3(B3/B4 語彙)。

実行: ``python -m shibuya.build.field.run --out data/world/v2 [--stage W7 ...]``
      (地理レーン込みの通し実行は ``python -m shibuya.build.run --out data/world/v2``)

層契約: build は manifest と core だけを import してよい。実行時に build を import してはならない。
"""

from __future__ import annotations

__all__ = ["STAGES"]

#: 実行順(W 番号順)。W11(駅・出口)は build.geo 側。
STAGES: tuple[str, ...] = ("W7", "W10", "W12", "W13")
