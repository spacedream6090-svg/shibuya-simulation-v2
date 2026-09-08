"""perception.hashes — **ハッシュ三役**(知覚契約書 §2.2/§5)。

正典
- §2.2:「**B2/B4 のバイト列ハッシュ=prefixキャッシュキー=変化検出器=dormant再送抑止**
  (三役・追加コストなし)」。
- §5:「ハッシュ三役: B2/B4 のバイト列ハッシュ=キャッシュキー(prefix)・変化検出器(§6)・
  dormant 再送抑止。」「B0-B4 は**同セル・同時間帯の全員でバイト一致**(検査は §2.4 ⑧)。」
- 実装計画書 §2 部品表: 高速ハッシュ=xxhash(変化検出・prefixキー・ルーティング)。

**2 つのハッシュを両方持つ**(親への報告事項・黙って一本化しない)
    1. **描画バイト列ハッシュ**(本モジュール ``block_hash``)= B2/B4/B4b の**描画結果**の xxh64。
       契約書 §2.2/§5 が「バイト列ハッシュ」と書いているのはこれ。prefix キャッシュ鍵は
       プロンプトのバイト列で決まるので、**prefix 用の正典はこちら**。
    2. **構造化欄ハッシュ**(``engine.change_detect.b4_block_hashes``)= 密度段・騒音段・
       営業中POI数の int32 行の xxh64。描画せずに済む**安い変化検出器**。
    両方を保つのが正しい(描画は起床した個体ぶんしか走らないので、全セルの変化検出には
    欄ハッシュが要る)。ただし **欄ハッシュが描画バイトの refinement であること**
    (欄が同じなら描画も同じ)が成立していないと dormant 抑止が取りこぼす。
    本モジュールの ``b4_field_row`` は**描画に使う欄そのもの**を並べるので refinement が
    定義上成立する。``tests/perception/test_hashes.py`` が機械検査する。

逐次ループ宣言(P4)
- ``block_hashes``: **行数**(=セル数)ぶんの xxh64 ループ1本。実装計画書 §3 が
  「xxhash で 453 回(宣言済みの小ループ)」と明示的に許した形。個体数には比例しない。

expedient(本モジュール分)
- ``prefix_key`` のバイト配置(ブロック id と u64 を LE で連結して xxh64)。契約書は
  「B2/B4 のバイト列ハッシュ=キャッシュキー」としか書かず、複数ブロックの合成規則が無い。
- ``b4_field_row`` に載せる欄(LOS 段・騒音段・流れ・顕著行為ダイジェスト)。
"""

from __future__ import annotations

from typing import Final, Iterable, Mapping, Sequence

import numpy as np

from shibuya.core.hashing import xxh64

__all__ = [
    "PREFIX_TAG",
    "block_hash",
    "block_hashes",
    "prefix_key",
    "should_resend",
    "b4_field_row",
    "field_row_hash",
    "field_row_hashes",
]

#: ``prefix_key`` の用途タグ(別用途のハッシュと値が衝突しないための固定接頭辞)。
PREFIX_TAG: Final[bytes] = b"shibuya.perception.prefix/v1\x1f"

_U64_LE = np.dtype("<u8")


def block_hash(data: bytes, seed: int = 0) -> int:
    """描画済みブロックのバイト列 → xxh64(三役の 1 本目=prefix キャッシュ鍵)。"""
    return xxh64(bytes(data), seed)


def block_hashes(blocks: Iterable[bytes], seed: int = 0) -> np.ndarray:
    """バイト列の列 → uint64 配列。

    Note:
        逐次ループ宣言(P4): 行数ぶんの xxh64 ループ1本(上限=セル数)。
    """
    return np.fromiter((block_hash(b, seed) for b in blocks), dtype=np.uint64)


def prefix_key(block_hashes_in_order: Sequence[int], block_ids: Sequence[str] | None = None) -> int:
    """ブロックハッシュの列 → prefix キャッシュ鍵(1 本の u64)。

    Args:
        block_hashes_in_order: **プロンプト本文と同じ順序**のブロックハッシュ。
        block_ids: 同じ長さのブロック id(順序も鍵の一部にする)。None なら省略。

    Note:
        順序が鍵に入るので、同じ集合でも並びが違えば別の鍵になる(prefix は前方一致なので
        並びが違えば実際に別のキャッシュになる)。
    """
    payload = bytearray(PREFIX_TAG)
    if block_ids is not None:
        if len(block_ids) != len(block_hashes_in_order):
            raise ValueError("block_ids と block_hashes の長さが違う")
        payload += ("\x1f".join(block_ids) + "\x1f").encode("utf-8")
    arr = np.asarray([int(h) & ((1 << 64) - 1) for h in block_hashes_in_order], dtype=_U64_LE)
    payload += arr.tobytes()
    return xxh64(bytes(payload))


def should_resend(prev_hash: int | None, new_hash: int) -> bool:
    """dormant 再送抑止(三役の 3 本目)。

    「dormant→B2(**変化まで再送しない**)」(§2.3)。初回(``prev_hash is None``)は必ず送る。

    Example:
        >>> should_resend(None, 7)
        True
        >>> should_resend(7, 7)
        False
        >>> should_resend(7, 8)
        True
    """
    if prev_hash is None:
        return True
    return int(prev_hash) != int(new_hash)


def b4_field_row(
    los_stage: np.ndarray,
    noise_stage: np.ndarray,
    flow: np.ndarray,
    salient_digest: np.ndarray,
) -> np.ndarray:
    """B4 の**描画に使う欄**を ``(n_cells, 4)`` int32 に並べる(欄ハッシュの素)。

    描画がこの 4 欄**だけ**に依存するので、欄ハッシュは描画バイトの refinement になる
    (欄が同じ ⇒ 描画バイトが同じ)。
    """
    cols = [los_stage, noise_stage, flow, salient_digest]
    n = int(np.asarray(cols[0]).size)
    out = np.empty((n, len(cols)), dtype=np.int32)
    for j, c in enumerate(cols):
        a = np.asarray(c).ravel()
        if a.size != n:
            raise ValueError("全ての欄は同じ長さでなければならない")
        out[:, j] = a.astype(np.int32, copy=False)
    return out


def field_row_hash(row: Sequence[int]) -> int:
    """1 行の欄 → xxh64。"""
    return xxh64(np.asarray(row, dtype=np.int32).tobytes())


def field_row_hashes(rows: np.ndarray, indices: np.ndarray | None = None) -> np.ndarray:
    """``(n, k)`` int32 の行ごとの xxh64。

    Note:
        逐次ループ宣言(P4): 行数ぶんの xxh64 ループ1本(上限=セル数)。
    """
    raw = np.ascontiguousarray(np.asarray(rows, dtype=np.int32))
    width = raw.shape[1] * 4
    flat = memoryview(raw.reshape(-1).view(np.uint8))
    idx = np.arange(raw.shape[0]) if indices is None else np.asarray(indices, dtype=np.int64)
    if idx.size == 0:
        return np.empty(0, dtype=np.uint64)
    return np.fromiter(
        (xxh64(flat[int(i) * width : (int(i) + 1) * width]) for i in idx),
        dtype=np.uint64,
        count=int(idx.size),
    )


def hash_report(named: Mapping[str, int]) -> str:
    """診断行用の 1 行(``B2=0x… B4=0x…``)。"""
    return " ".join(f"{k}=0x{int(v):016x}" for k, v in named.items())
