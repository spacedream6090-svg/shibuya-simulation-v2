"""core.rng — カウンタベース乱数(numpy Philox4x64)のドメイン分離。

設計根拠: 実装計画書 §2(RNG=numpy.random.Philox・manifest欄 ``numpy-philox4x64``)・§3
(鍵=ドメイン・カウンタ=tick/個体/抽選番号)・運用設計書 §1.4 T4(n=5,000 と 5,001 で既存個体の乱数列が
不変=カウンタベースの実証)・計器盤設計書 G-5(seed = blake3(manifest_sha256 ‖ run_index) の決定的写像)。

規約
- ``master_seed`` はランの manifest から与えられる 64bit 整数(または run_id 文字列)。
- ``domain`` は用途を表す短い文字列(例 ``"agent.habit"``・``"llm.sample"``・``"world.weather"``)。
  ドメイン表の版は manifest の ``rng.domain_table_version`` に記録する(本モジュールは表を持たない)。
- 個体 ID や tick はカウンタ側に置く。鍵は (master_seed, domain) のみから導く。
  → 同じ (master_seed, domain, counters) は常に同じ列。個体数を増やしても既存個体の列は変わらない(T4)。
- OS 乱数・暗黙 seed は禁止(G-5)。本モジュール以外で ``np.random.default_rng()`` を引数なしで呼ばない。

expedient: 鍵導出のハッシュ入力形式(UTF-8 の ``"i:<int>"`` または ``"s:<str>"`` ‖ 0x1F ‖ domain → blake3 16 バイト)は自前規約。
"""

from __future__ import annotations

from typing import Iterable

import blake3
import numpy as np

__all__ = ["derive_key", "philox", "stream", "MASK64"]

MASK64 = (1 << 64) - 1
_SEP = "\x1f"  # ASCII unit separator


def _seed_to_text(master_seed: int | str) -> str:
    if isinstance(master_seed, bool):  # bool は int の部分型だが意図しない
        raise TypeError("master_seed に bool は使えません")
    if isinstance(master_seed, int):
        if master_seed < 0 or master_seed > MASK64:
            raise ValueError("master_seed は 0..2^64-1 の整数")
        return f"i:{master_seed}"
    if isinstance(master_seed, str):
        if not master_seed:
            raise ValueError("master_seed 文字列は空にできません")
        return f"s:{master_seed}"
    raise TypeError("master_seed は int または str")


def derive_key(master_seed: int | str, domain: str) -> tuple[int, int]:
    """(master_seed, domain) → Philox4x64 の 128bit 鍵 (k0, k1)。

    blake3 の 16 バイト出力を little-endian の uint64 ×2 に切る。
    """
    if not domain or _SEP in domain:
        raise ValueError("domain は空でなく、区切り文字 \\x1f を含まない")
    h = blake3.blake3(f"{_seed_to_text(master_seed)}{_SEP}{domain}".encode("utf-8")).digest(length=16)
    k0 = int.from_bytes(h[:8], "little")
    k1 = int.from_bytes(h[8:], "little")
    return k0, k1


def _counter_words(counters: Iterable[int]) -> list[int]:
    words = [int(c) for c in counters]
    if len(words) > 4:
        raise ValueError("カウンタは最大 4 語(Philox4x64 の 256bit カウンタ)")
    for w in words:
        if w < 0 or w > MASK64:
            raise ValueError("カウンタ語は 0..2^64-1")
    return words + [0] * (4 - len(words))


def philox(master_seed: int | str, domain: str, *counters: int) -> np.random.Philox:
    """鍵=derive_key・カウンタ=(counters を 4 語に詰めた 256bit) の Philox ビット生成器。"""
    key = derive_key(master_seed, domain)
    ctr = _counter_words(counters)
    # numpy は key/counter を uint64 配列として受ける(key は 2 語・counter は 4 語)
    return np.random.Philox(key=np.array(key, dtype=np.uint64), counter=np.array(ctr, dtype=np.uint64))


def stream(master_seed: int | str, domain: str, *counters: int) -> np.random.Generator:
    """用途別の Generator。例: ``stream(seed, "agent.habit", agent_id, tick)``。"""
    return np.random.Generator(philox(master_seed, domain, *counters))
