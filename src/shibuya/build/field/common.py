"""build.field.common — 場・境界レーンの共有ヘルパ。

build.geo.common(ハッシュ・ヘッダ・座標・格子・出力 I/O)をそのまま再輸出し、
本レーン固有の小道具(dB のエネルギー和・全角/旧字の正規化・分表記)だけを足す。
ヘッダ規約(§0-1/§0-2/§0-6/§0-7)は geo と完全に同一。
"""

from __future__ import annotations

import math
import unicodedata
from typing import Iterable, Sequence

from ..geo.common import (  # noqa: F401  (再輸出)
    BAND_OF_LAYER,
    BANDS,
    CELL_M,
    GROUND0_M,
    M_PER_DEG_LAT,
    M_PER_DEG_LON,
    ORIGIN_LATLON,
    Ctx,
    Gate,
    StageResult,
    band_of_layer,
    canonical_json_bytes,
    grid_ij,
    input_hash,
    load_json,
    node_layer_from_incident,
    param_hash,
    place_id,
    read_parquet_columns,
    sha256_bytes,
    sha256_file,
    write_header,
    write_json,
    write_npy,
    write_npz,
    write_parquet,
)

__all__ = [
    "BAND_OF_LAYER",
    "BANDS",
    "CELL_M",
    "GROUND0_M",
    "M_PER_DEG_LAT",
    "M_PER_DEG_LON",
    "ORIGIN_LATLON",
    "Ctx",
    "Gate",
    "StageResult",
    "band_of_layer",
    "canonical_json_bytes",
    "grid_ij",
    "input_hash",
    "load_json",
    "node_layer_from_incident",
    "param_hash",
    "place_id",
    "read_parquet_columns",
    "sha256_bytes",
    "sha256_file",
    "write_header",
    "write_json",
    "write_npy",
    "write_npz",
    "write_parquet",
    # --- field 固有 ---
    "db_sum",
    "db_from_power",
    "power_from_db",
    "normalize_jp",
    "hhmm_to_min",
    "min_to_hhmm",
    "json_text",
]

_MISSING_DB = -300.0


def power_from_db(level_db: float) -> float:
    """dB → 相対エネルギー。"""
    return 10.0 ** (level_db / 10.0)


def db_from_power(power: float) -> float:
    """相対エネルギー → dB(0 以下は ``-300`` を返す=無音の番兵)。"""
    if power <= 0.0:
        return _MISSING_DB
    return 10.0 * math.log10(power)


def db_sum(levels: Iterable[float]) -> float:
    """dB のエネルギー和(パワー和)。空なら ``-300``。"""
    total = 0.0
    for lv in levels:
        if lv > _MISSING_DB:
            total += power_from_db(lv)
    return db_from_power(total)


_ZEN2HAN = str.maketrans({chr(0xFF10 + i): str(i) for i in range(10)})
_KANJI_NUM = {
    "〇": "0",
    "一": "1",
    "二": "2",
    "三": "3",
    "四": "4",
    "五": "5",
    "六": "6",
    "七": "7",
    "八": "8",
    "九": "9",
}


def normalize_jp(text: str) -> str:
    """路線名などの日本語キーを突合可能な形へ正規化する。

    NFKC(全角英数→半角)・空白除去・漢数字→算用数字・「号線/号」の表記ゆれ吸収。
    例: ``環状六号線`` と ``環状6号線``・``一般国道２４６号`` と ``一般国道246号`` が同値になる。
    """
    s = unicodedata.normalize("NFKC", text).translate(_ZEN2HAN)
    s = "".join(_KANJI_NUM.get(ch, ch) for ch in s)
    s = "".join(s.split())
    return s


def hhmm_to_min(text: str) -> int:
    """``HH:MM`` → 0時からの分。``24:00`` は 1440。"""
    hh, mm = text.strip().split(":")
    return int(hh) * 60 + int(mm)


def min_to_hhmm(minutes: int) -> str:
    """0時からの分 → ``HH:MM``(24時以降は 25:10 のように繰り上げ表記)。"""
    return f"{minutes // 60:02d}:{minutes % 60:02d}"


def json_text(obj: object) -> str:
    """Parquet の文字列列へ入れる canonical JSON(バイト決定論のため)。"""
    return canonical_json_bytes(obj).decode("utf-8")


def clamp(value: float, low: float, high: float) -> float:
    return low if value < low else (high if value > high else value)


def median(values: Sequence[float]) -> float:
    """偶数個は下側中央値(決定論・浮動小数の平均を避ける)。"""
    if not values:
        raise ValueError("median: 空列")
    xs = sorted(values)
    return xs[(len(xs) - 1) // 2]


__all__ += ["clamp", "median"]
