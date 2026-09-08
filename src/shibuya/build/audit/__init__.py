"""build.audit — 世界データ構築 W18/W19/W20(被覆指標・凍結・検収パック)。

仕様: docs/design/v2-world-data-build-spec.md §1 段階表 W18/W19/W20・§2 D-W19/D-W20・
§0-5 holdout規律・§0-6 カタログ写像。方法論「世界被覆指標」(C,Q,D,V,R+X+孤児)。
運用設計書 §1.2(データ資産・holdout封印)。

実行: ``python -m shibuya.build.audit.run --out data/world/v2 [--stage W18]``
      (通し実行は ``python -m shibuya.build.run --out data/world/v2``)

層契約: build は manifest と core だけを import してよい。実行時に build を import してはならない。
"""

from __future__ import annotations

__all__ = ["STAGES"]

#: 実行順(W 番号順)。W18→W19→W20 は依存順でもある。
STAGES: tuple[str, ...] = ("W18", "W19", "W20")
