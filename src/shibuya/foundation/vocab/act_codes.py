"""foundation.vocab.act_codes — 割る段で ``llm/undefined.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``act/intake/undefined.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

from typing import Final

__all__ = [
    "TARGET_HINT_WORDS",
]


#: 対象ヒントの語(**この並びが正典**。エンジンは索引で運ぶ=``engine.commit.TARGET_HINT_*``)。
#: ``""``=ヒントなし / ``home``/``work``/``school``=W16 の拠点セル(エンジンが解決する) /
#: ``category``=「対象」欄の物カテゴリをそのまま使う / ``approach``=対象(人/物)に近づく /
#: ``look``=対象(人/物)を注意の焦点にする。
TARGET_HINT_WORDS: Final[tuple[str, ...]] = (
    "", "home", "work", "school", "category", "approach", "look",
)
