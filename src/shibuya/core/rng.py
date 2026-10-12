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

__all__ = [
    "derive_key",
    "philox",
    "stream",
    "MASK64",
    "RNG_SCHEME",
    "run_tick_key",
    "k19_counters",
]

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


# ---------------------------------------------------------------- 10c・10e: 状態を持たない乱数(counter)
#: 乱数の方式の名前(manifest の ``rng_scheme``・テープの脇の meta の値)。毎回 (seed, 用途, 鍵) から作る=状態を持たない
#: (10c・Q8・10e E4 で既定)。〔第330・RET〕10e より前の ``stateful``(日の頭に作った Generator を tick ごとに進める)と
#: 切替口 ``--rng-scheme`` は版上げ 1 回目の後に消した(旧値の再現は第330 ACT の commit で記録)。
RNG_SCHEME: str = "counter"


def k19_counters(*words: int) -> tuple[int, ...]:
    """10e(E4・K19)の鍵の並べ方。0 語目を 0 に空け、鍵の語を 1〜3 語目に置く。

    numpy の Philox は 1 ブロック(4 語)引くごとに 0 語目を 1 進める。0 語目に値(体・層・日の鍵・事象の番号)を置くと、
    2 ブロック以上引いた流れが「その値 +1」の流れの頭と重なる(10c 検収 P1〜P3・R3・R4・10f の U2=日の鍵の流れが
    次の日に 1 ブロックずれた写しになる)。0 語目を 0 にすれば、同じ鍵の流れは 2^64 ブロック引くまで隣と重ならない
    (10c の counter の 2 本と同じ形)。鍵の語は 3 つまで(Philox のカウンタは 4 語)。
    """
    w = tuple(int(x) for x in words)
    if len(w) > 3:
        raise ValueError(f"k19_counters: 鍵の語は 3 つまで(いま {len(w)})")
    return (0, *w)


def run_tick_key(day_key0: int, T: int, tick_seconds: int) -> int:
    """counter の乱数の鍵に入れる時刻 = ``day_key0 × 1 日の tick 数 + T``。

    ``T`` はランの通しの時刻(10a)。``day_key0`` はランの 0 日目の日の鍵(``SimCalendar.day_key(0)``:
    日番号=0=鍵は T そのもの。〔第330・RET〕``day_index`` のモードは消した)。
    ``day_key(日) = day_key0 + 日`` なので、この値は「日の鍵 × 1 日の tick 数 + 日の中の tick」と同じ。
    """
    tpd = 86_400 // max(1, int(tick_seconds))
    v = int(day_key0) * tpd + int(T)
    if v < 0 or v > MASK64:
        raise ValueError(f"鍵の時刻は 0..2^64-1(いま {v})")
    return v
