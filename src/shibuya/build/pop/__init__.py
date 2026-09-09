"""build.pop — 世界データ構築 W16(母集団合成)。

各段階=純関数(入力ファイル群+パラメータ→出力+ヘッダ)。ヘッダ形式は build.geo と同一。
仕様: docs/design/v2-world-data-build-spec.md §1 段階表 W16・§2 D-W16(町丁目→セル写像=
建物床面積按分)・D-W14(集計表は生成/較正/検証のみ)・D-W20(CI で W16 再構築一致)。
決定台帳「母集団合成」「母集団合成(追補)」の 7 段手順のうち **①〜⑥**(⑦スケジュール生成=W17)。

実行: ``python -m shibuya.build.pop.run --out data/world/v2``
      (全段階の通しは ``python -m shibuya.build.run --out data/world/v2``)

層契約: build は manifest と core だけを import してよい。実行時に build を import してはならない。
"""

from __future__ import annotations

__all__ = ["STAGES"]

#: 実行順(W 番号順)。W16 のみ。W17(スケジュール生成・LLM 40万呼)は C5-b。
STAGES: tuple[str, ...] = ("W16",)
