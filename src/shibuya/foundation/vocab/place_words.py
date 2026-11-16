"""foundation.vocab.place_words — 割る段で ``world/assets.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``world/model/assets.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final


#: 合成 POI のカテゴリと価格[円](expedient)。
SYNTHETIC_POI_CATS: Final[tuple[str, ...]] = ("コンビニ", "飲食", "物販")
