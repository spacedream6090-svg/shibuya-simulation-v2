"""core.rng — カウンタベース乱数(numpy Philox4x64)のドメイン分離。

設計根拠: 実装計画書 §2(RNG=numpy.random.Philox・manifest欄 ``numpy-philox4x64``)・§3
(鍵=ドメイン・カウンタ=刻み/個体/抽選番号)・運用設計書 §1.4 T4(n=5,000 と 5,001 で既存個体の乱数列が
不変=カウンタベースの実証)・計器盤設計書 G-5(seed = blake3(manifest_sha256 ‖ run_index) の決定的写像)。

規約
- ``master_seed`` はランの manifest から与えられる 64bit 整数(または run_id 文字列)。
- ``domain`` は用途を表す短い文字列(例 ``"agent.habit"``・``"llm.sample"``・``"world.weather"``)。
  ドメイン表の版は manifest の ``rng.domain_table_version`` に記録する(本モジュールは表を持たない)。
- 個体 ID や刻みの番号はカウンタ側に置く。鍵は (master_seed, domain) のみから導く。
  → 同じ (master_seed, domain, counters) は常に同じ列。個体数を増やしても既存個体の列は変わらない(T4)。
- OS 乱数・暗黙 seed は禁止(G-5)。本モジュール以外で ``np.random.default_rng()`` を引数なしで呼ばない。

expedient: 鍵導出のハッシュ入力形式(UTF-8 の ``"i:<int>"`` または ``"s:<str>"`` ‖ 0x1F ‖ domain → blake3 16 バイト)は自前規約。
"""

from __future__ import annotations

from typing import Any, Iterable

import blake3
import numpy as np

from shibuya.core.time_consts import NS_PER_SECOND, SECONDS_PER_DAY

__all__ = [
    "derive_key",
    "philox",
    "stream",
    "MASK64",
    "RNG_SCHEME",
    "run_tick_key",
    "time_key_from_t_ns",
    "k19_counters",
    "philox_array",
    "k19_counter_array",
    "unit_float",
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
#: (10c・Q8・10e E4 で既定)。〔第330・RET〕10e より前の ``stateful``(日の頭に作った Generator を刻みごとに進める)と
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
    """counter の乱数の鍵に入れる時刻 = ``day_key0 × 1 日の刻みの数 + T``。

    ``T`` はランの通しの時刻(10a)。``day_key0`` はランの 0 日目の日の鍵(``SimCalendar.day_key(0)``:
    日番号=0=鍵は T そのもの。〔第330・RET〕``day_index`` のモードは消した)。
    ``day_key(日) = day_key0 + 日`` なので、この値は「日の鍵 × 1 日の刻みの数 + 日の中の刻み」と同じ。
    """
    tpd = SECONDS_PER_DAY // max(1, int(tick_seconds))
    v = int(day_key0) * tpd + int(T)
    if v < 0 or v > MASK64:
        raise ValueError(f"鍵の時刻は 0..2^64-1(いま {v})")
    return v


def time_key_from_t_ns(day_key0: int, t_ns: int, step_seconds: int) -> int:
    """〔第 1 期 1-1 T0・TM7 (d) の準備〕``run_tick_key`` と同じ鍵の値を、刻みの番号でなく通しの時刻 ``t_ns``
    (ナノ秒=``core.types.SimTime``)から作る。

    刻みの番号は ``t_ns // (幅 × 1e9)``(床=その時刻を含む刻み)。刻みの頭の時刻(``TickCtx.t_ns``)を渡せば
    ``run_tick_key(day_key0, T, 幅)`` と同じ値(``tests/engine/time/test_t0_rng_key.py`` が全刻みで検算)。
    **呼び手はまだ無い**(鍵の値は 10c の counter のまま=結果不変)。鍵の材料を出来事の時刻と中身に替えるのは後の段。

    Raises:
        ValueError: 幅が正の整数でない・鍵が 0..2^64-1 の外。
    """
    w = int(step_seconds)
    if w <= 0:
        raise ValueError(f"刻みの幅(秒)は正の整数: {step_seconds!r}")
    return run_tick_key(day_key0, int(t_ns) // (w * NS_PER_SECOND), w)


# ---------------------------------------------------------------- 第 2 期 2-2: 配列で回す Philox(同じ出力)
#: Philox4x64-10 の定数(Random123・numpy の ``philox.h`` と同じ値)。
_PHILOX_M0: int = 0xD2E7470EE14C6C93
_PHILOX_M1: int = 0xCA5A826395121157
_PHILOX_W0: int = 0x9E3779B97F4A7C15
_PHILOX_W1: int = 0xBB67AE8584CAA73B
_PHILOX_ROUNDS: int = 10
_LO32 = np.uint64(0xFFFFFFFF)
_SH32 = np.uint64(32)


def _mulhilo(a: np.ndarray, m: int) -> tuple[np.ndarray, np.ndarray]:
    """``a × m`` の 128 bit の上 64 bit と下 64 bit(配列・``m`` は定数)。32 bit に割って掛ける(どの積も 64 bit に収まる)。"""
    m_lo, m_hi = np.uint64(m & 0xFFFFFFFF), np.uint64(m >> 32)
    a_lo = a & _LO32
    a_hi = a >> _SH32
    ll = a_lo * m_lo
    lh = a_lo * m_hi
    hl = a_hi * m_lo
    hh = a_hi * m_hi
    mid = (ll >> _SH32) + (lh & _LO32) + (hl & _LO32)
    hi = hh + (lh >> _SH32) + (hl >> _SH32) + (mid >> _SH32)
    lo = ((mid & _LO32) << _SH32) | (ll & _LO32)
    return hi, lo


def _philox_block(key: tuple[int, int], ctr: np.ndarray) -> np.ndarray:
    """Philox4x64-10 の 1 ブロック(``ctr``: (n, 4) uint64 → (n, 4) uint64)。逐次ループ宣言: 段の数ぶん(10)。"""
    k0, k1 = int(key[0]) & MASK64, int(key[1]) & MASK64
    c0, c1, c2, c3 = (ctr[:, j].copy() for j in range(4))
    for r in range(_PHILOX_ROUNDS):  # 逐次: 段の数ぶん(10・体の数に依らない)
        if r:
            k0, k1 = (k0 + _PHILOX_W0) & MASK64, (k1 + _PHILOX_W1) & MASK64
        hi0, lo0 = _mulhilo(c0, _PHILOX_M0)
        hi1, lo1 = _mulhilo(c2, _PHILOX_M1)
        c0, c1, c2, c3 = hi1 ^ c1 ^ np.uint64(k0), lo1, hi0 ^ c3 ^ np.uint64(k1), lo0
    return np.stack([c0, c1, c2, c3], axis=1)


def _counter_array(counters: Any) -> np.ndarray:
    """鍵の語の配列((n, m)・m ≤ 4・整数・0..2^64-1)→ 4 語に詰めた (n, 4) uint64(足りない語は 0=``_counter_words`` と同じ)。"""
    c = np.asarray(counters)
    if c.ndim != 2 or c.shape[1] > 4:
        raise ValueError(f"カウンタの配列は (行の数, 語の数 ≤ 4)(いま {c.shape})")
    if c.size and not np.issubdtype(c.dtype, np.integer):
        raise TypeError(f"カウンタの配列は整数(いま {c.dtype})")
    if c.size and np.issubdtype(c.dtype, np.signedinteger) and bool((c < 0).any()):
        raise ValueError("カウンタ語は 0..2^64-1")
    out = np.zeros((c.shape[0], 4), dtype=np.uint64)
    out[:, : c.shape[1]] = c.astype(np.uint64, copy=False)
    return out


def _advance(ctr: np.ndarray, k: int) -> np.ndarray:
    """カウンタ(4 語・0 語目が下の桁)に ``k`` を足す(繰り上がりつき・2^256 で回る=numpy と同じ)。"""
    out = ctr.copy()
    add = np.full(out.shape[0], np.uint64(k), dtype=np.uint64)
    for j in range(4):  # 逐次: 語の数ぶん(4)
        new = out[:, j] + add
        carry = new < out[:, j]
        out[:, j] = new
        add = carry.astype(np.uint64)
        if not bool(carry.any()):
            break
    return out


def philox_array(master_seed: int | str, domain: str, counters: Any, *, words: int = 1) -> np.ndarray:
    """``philox(master_seed, domain, *counters[i]).random_raw(words)`` を全行まとめて引く((n, words) の uint64)。

    鍵は :func:`derive_key`(1 回)・行ごとのカウンタは ``counters`` の行(4 語に詰める=:func:`philox` と同じ)。numpy の
    Philox は引く前にカウンタを 1 進める(繰り上がりつき)ので、``b`` ブロック目(0 から)は「行のカウンタ + b + 1」の
    ブロック。出力は numpy の ``np.random.Philox`` と同じ(試験=1 万行の一致)。状態を持たない(毎回作り直す流れと同じ)。
    逐次ループ宣言: ブロックの数ぶん(``ceil(words / 4)``)× 段の数(10)=行の数に依らない。
    """
    w = int(words)
    if w < 1:
        raise ValueError(f"引く語数は 1 以上(いま {words!r})")
    key = derive_key(master_seed, domain)
    ctr = _counter_array(counters)
    out = np.empty((ctr.shape[0], w), dtype=np.uint64)
    if ctr.shape[0] == 0:
        return out
    for b in range(-(-w // 4)):  # 逐次: ブロックの数ぶん
        blk = _philox_block(key, _advance(ctr, b + 1))
        take = min(4, w - 4 * b)
        out[:, 4 * b: 4 * b + take] = blk[:, :take]
    return out


def k19_counter_array(*cols: Any) -> np.ndarray:
    """:func:`k19_counters` の配列の版(0 語目を 0 に空け、鍵の列を 1〜3 語目に置く=(n, 1 + 列の数) の uint64)。"""
    if len(cols) > 3:
        raise ValueError(f"k19_counter_array: 鍵の列は 3 つまで(いま {len(cols)})")
    arrs = [np.atleast_1d(np.asarray(c)) for c in cols]
    n = max((a.size for a in arrs), default=0)
    out = np.zeros((n, 1 + len(arrs)), dtype=np.uint64)
    for j, a in enumerate(arrs):  # 逐次: 列の数ぶん(3 まで)
        if a.size and not np.issubdtype(a.dtype, np.integer):
            raise TypeError(f"鍵の列は整数(いま {a.dtype})")
        if a.size and np.issubdtype(a.dtype, np.signedinteger) and bool((a < 0).any()):
            raise ValueError("鍵の語は 0..2^64-1")
        out[:, 1 + j] = np.broadcast_to(a, (n,)).astype(np.uint64, copy=False)
    return out


def unit_float(raw: Any) -> np.ndarray:
    """uint64 → [0, 1) の float64(numpy の ``Generator.random()`` と同じ写し方=上の 53 bit × 2^-53)。"""
    u = np.asarray(raw, dtype=np.uint64)
    return (u >> np.uint64(11)).astype(np.float64) * (1.0 / 9007199254740992.0)
