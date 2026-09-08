"""世界カタログ v0.2(世界被覆指標の**分母**)の実行時リーダ。

分母は凍結資産である(docs/design/v2-world-catalog.md の本表)。実行時はここから
同梱 JSON を読むだけで、Markdown を再解析しない——生成は build 側
(``python -m shibuya.build.catalog_freeze``)の仕事。

層契約: shibuya.manifest は他の shibuya パッケージを import しない。
特に **shibuya.build を import しない**(import-linter で強制)。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files

__all__ = [
    "FROZEN_SHA16",
    "FROZEN_VERSION",
    "FROZEN_N_CLASSES",
    "CATALOG_RESOURCE",
    "WorldCatalog",
    "load_world_catalog",
    "verify_frozen",
]

#: 凍結 SHA(v0.2・2026-09-07 ユーザー承認)。docs/design/v2-world-catalog.md の
#: 本表を UTF-8 でハッシュした sha256 の先頭16桁。
FROZEN_SHA16 = "34f9fa9d316587be"
FROZEN_VERSION = "v0.2"
FROZEN_N_CLASSES = 57

#: 同梱 JSON の位置(package-data として pyproject に登録済み)。
CATALOG_RESOURCE = "frozen/world_catalog_v0_2.json"


@dataclass(frozen=True)
class WorldCatalog:
    """凍結された世界カタログ。

    Attributes:
        version: カタログ版(``v0.2``)。
        sha16: 凍結 SHA(先頭16桁)。
        columns: 本表の列名(9列)。
        rows: 行の辞書(キーは ``columns``)。Markdown 上の順。
    """

    version: str
    sha16: str
    columns: tuple[str, ...]
    rows: tuple[dict[str, str], ...]

    @property
    def n_classes(self) -> int:
        """カタログのクラス数(=被覆指標の分母)。"""
        return len(self.rows)


def load_world_catalog() -> WorldCatalog:
    """同梱 JSON から凍結カタログを読む。"""
    resource = files("shibuya.manifest").joinpath(CATALOG_RESOURCE)
    payload = json.loads(resource.read_text(encoding="utf-8"))
    return WorldCatalog(
        version=payload["version"],
        sha16=payload["sha16"],
        columns=tuple(payload["columns"]),
        rows=tuple(payload["rows"]),
    )


def verify_frozen(cat: WorldCatalog) -> None:
    """凍結値との一致を検査する(分母が黙って動いていないことの門)。

    Raises:
        ValueError: SHA またはクラス数が凍結値と異なる。
    """
    if cat.sha16 != FROZEN_SHA16:
        raise ValueError(
            f"世界カタログの SHA が凍結値と異なる: {cat.sha16} != {FROZEN_SHA16}"
            "(分母の変更はユーザー承認+版番号が必要)"
        )
    if cat.n_classes != FROZEN_N_CLASSES:
        raise ValueError(
            f"世界カタログのクラス数が凍結値と異なる: "
            f"{cat.n_classes} != {FROZEN_N_CLASSES}"
        )
