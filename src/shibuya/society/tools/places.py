"""engine.tools.places — 店の番号の場所の表(第 1 期 1-7 C0・CT5 の「店や組織の番号は場所の表の側」)。

口の約束 1-7〔決定(回答 10-13b §3)〕: 店の番号の場所の表は OSM の ``phone`` タグから作る(ライセンスを増やさない=ODbL は
既にライセンス台帳にある)。

- C0 は**空の表**。読み口 ``phone_of(poi_id)`` は今は全部 ``None``。中身は構築の段(W6 の POI)に欄を足す形で、版上げ 2 回目
  (計画 2-4)に OSM の ``phone`` タグから埋める=つなぎの台帳 ``BR-PHONE-TABLE-BLANK``。``w6_poi.parquet`` には OSM の番号の
  列が無いが、元の JSON(``shibuya_osm_wide_v8.json`` の ``pois``)の行の並びで OSM の番号に結べる見込み(2,259 行・``phone``
  477 行=記録 c0/README.md §5)。2-4 で確かめる(結べない行の扱いもそこで決める)。
- 本段で数えた OSM の ``phone`` タグを持つ要素の数は記録 ``docs/bench/analysis/wallbounce-1012/c0/README.md``(数える規則は
  ``osm_phone_of``=道具 ``c0/tools/count_osm_phone.py`` と試験が同じ関数を使う)。
- 書く口は組み立ての ``PhoneTable(rows)`` だけ(作った後は書けない=読み取り専用の表)。

逐次ループ宣言: なし(表を作るのは起動時に 1 回)。
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Any, Final, Mapping

import numpy as np

__all__ = ["PHONE_TAGS", "SOURCE", "PhoneTable", "osm_phone_of"]

#: OSM の電話番号のタグ(OSM の wiki の Key:phone と contact:phone=同じ意味の 2 つの書き方)。
PHONE_TAGS: Final[tuple[str, ...]] = ("phone", "contact:phone")
#: 表の出どころ(回答 10-13b §3)。
SOURCE: Final[str] = "osm:phone"


def osm_phone_of(tags: Mapping[str, Any] | None) -> str | None:
    """OSM の要素のタグ → 電話番号の文字列(``phone`` を先に・無ければ ``contact:phone``・空は ``None``)。"""
    if not tags:
        return None
    for k in PHONE_TAGS:
        v = tags.get(k)
        if isinstance(v, str) and v.strip():
            return v.strip()
    return None


def _is_int(x: Any) -> bool:
    return isinstance(x, (int, np.integer)) and not isinstance(x, (bool, np.bool_))


class PhoneTable:
    """店の番号の場所の表(POI の番号 → 電話番号)。C0 は空。作った後は書けない。"""

    __slots__ = ("__rows",)

    def __init__(self, rows: Mapping[int, str] | None = None) -> None:
        try:  # 検収 L2: 作った後に __init__ を呼び直して中身を入れ替えない
            object.__getattribute__(self, "_PhoneTable__rows")
        except AttributeError:
            pass
        else:
            raise RuntimeError("PhoneTable は作った後に __init__ を呼び直せない(中身を入れ替えない)")
        out: dict[int, str] = {}
        for k, v in dict(rows or {}).items():
            if not _is_int(k) or int(k) < 0:
                raise ValueError(f"POI の番号は 0 以上の整数(いま {k!r})")
            if not isinstance(v, str) or not v.strip():
                raise ValueError(f"電話番号は空でない文字列(いま {v!r})")
            out[int(k)] = v.strip()
        object.__setattr__(self, "_PhoneTable__rows", MappingProxyType(out))

    def __setattr__(self, name: str, value: Any) -> None:
        raise AttributeError(f"PhoneTable は組み立ての後に書けない({name})")

    def __delattr__(self, name: str) -> None:
        raise AttributeError(f"PhoneTable は組み立ての後に書けない({name})")

    def phone_of(self, poi_id: int) -> str | None:
        """POI の番号 → 電話番号(表に無ければ ``None``)。"""
        if not _is_int(poi_id) or int(poi_id) < 0:
            raise ValueError(f"poi_id は 0 以上の整数(いま {poi_id!r})")
        return self.__rows.get(int(poi_id))

    @property
    def rows(self) -> Mapping[int, str]:
        return self.__rows

    def __len__(self) -> int:
        return len(self.__rows)

    def tally(self) -> dict[str, Any]:
        """manifest の ``tools.phone_table``。"""
        from shibuya.engine.tools.registry import PHONE_BRIDGE

        return {"rows": len(self), "source": SOURCE, "bridge": PHONE_BRIDGE}
