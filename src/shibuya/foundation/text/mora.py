"""foundation.text.mora — 割る段で ``engine/speech/port.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``society/speech/port.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

import unicodedata
from typing import Final

__all__ = [
    "mora_count",
]


# ---- モーラの数え方(仮名の数の近似) ----
_SMALL_KANA: Final[frozenset[str]] = frozenset("ぁぃぅぇぉゃゅょゎゕゖァィゥェォャュョヮ")


def mora_count(text: str) -> int:
    """本文のモーラ数(TM3 の入力=発言の長さ=モーラ数 × 話す速さ)。

    expedient: モーラ数は仮名の数の近似で数える(読みの辞書を使わない)。仮名 1 字=1 拍(拗音・小書きの母音の
    ゃゅょぁぃぅぇぉゎ は前の字と合わせて 1 拍=0 と数える・促音 っ・撥音 ん・長音 ー は 1 拍)・漢字 1 字=2 拍(音読みの多くが
    2 拍=仮の値)・英数字 1 字=1 拍・記号と空白は 0。TM3 の会話の時計(6-3 の T2)で読みの辞書に替える。

    逐次ループ宣言(P4): 本文の字数ぶん(≤ 数十字・呼数に比例)。
    """
    n = 0
    for ch in unicodedata.normalize("NFKC", str(text)):  # 逐次: 字数ぶん
        o = ord(ch)
        if ch in _SMALL_KANA:
            continue
        if 0x3041 <= o <= 0x3096 or 0x30A1 <= o <= 0x30FA or ch == "ー":
            n += 1
        elif 0x4E00 <= o <= 0x9FFF or 0x3400 <= o <= 0x4DBF or ch == "々":
            n += 2
        elif ch.isascii() and ch.isalnum():
            n += 1
    return n
