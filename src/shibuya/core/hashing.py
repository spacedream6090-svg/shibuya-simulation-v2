"""core.hashing — 決定論ハッシュ(blake3/xxh64/sha256_cbor)と優先度キー。

正典
- 実装計画書 §2 部品表: 暗号ハッシュ=blake3(manifest・資産・封印・**優先度キー**)/
  高速ハッシュ=xxhash(変化検出・prefixキー・ルーティング)。
- 実装計画書 §7/運用設計書 §1.2: vLLM の prefix caching は ``sha256_cbor``
  (= CBOR 正準符号化した鍵を SHA-256)。本モジュールの ``sha256_cbor`` は**同名の算法**を
  ローカルで再現し、テープの ``params_hash``・プロンプト鍵に使う。
- 運用設計書 §2.2: 優先度キー pk = (ceil_ns(t_notice), blake3(run_salt‖tick‖resource_id‖agent_id))。
  本モジュールが担うのは第2要素(u64 に切ったもの)。
- 運用設計書 §2.4: apply_key = (t_apply, event_class, blake3(run_salt‖t_apply‖agent_id))。
  同じく第3要素を担う。
- 運用設計書 §2.5: 同時刻イベントのタイブレーク第3要素 blake3(…)。起床イベント用は
  ``wake_tiebreak``。

バイト配置(**本モジュールの規約=凍結対象**。設計書は「‖」としか書いていない=下記は expedient)
    入力 = run_salt(可変長バイト列) ‖ 用途タグ(3バイト) ‖ 各整数を **8バイト little-endian
    two's complement (int64)** で連結。用途タグは
      ``b"pk\x00"`` 優先度キー / ``b"ak\x00"`` LLM 適用キー / ``b"wk\x00"`` 起床タイブレーク。
    出力 = blake3 の先頭8バイトを little-endian の unsigned int64 として読む。
    用途タグを挟むのは、同じ (salt, tick, id) 三つ組が別用途で同一値にならないようにするため
    (設計書に規定なし=expedient・golden 値をテストで固定する)。

逐次ループ宣言(P4・実装計画書 §6/予算 P4)
- ``priority_key_array`` / ``apply_key_array`` / ``wake_tiebreak_array``:
  blake3 は要素ごとに1回呼ぶ必要があるため **要素数ぶんの Python ループを1本持つ**
  (list 内包+``b"".join``+``np.frombuffer`` の形。実測 約2.0 M件/秒 @ Windows/1コア)。
  代替のベクトル化混合関数(splitmix64 等)は blake3 と値が一致しないため採らない。
  P3(≥10万イベント/秒)に対して 20 倍の余裕があることを ``tests/engine`` の P3 テストで機械検査する。
"""

from __future__ import annotations

import hashlib
import struct
from typing import Any, Iterable, Sequence

import blake3 as _blake3_mod
import cbor2
import numpy as np
import xxhash

__all__ = [
    "BLAKE3_TAG_PRIORITY",
    "BLAKE3_TAG_APPLY",
    "BLAKE3_TAG_WAKE",
    "blake3_hex",
    "blake3_u64",
    "xxh64",
    "xxh64_array",
    "sha256_cbor",
    "cbor_canonical",
    "priority_key",
    "apply_key",
    "wake_tiebreak",
    "priority_key_array",
    "apply_key_array",
    "wake_tiebreak_array",
]

BLAKE3_TAG_PRIORITY = b"pk\x00"
BLAKE3_TAG_APPLY = b"ak\x00"
BLAKE3_TAG_WAKE = b"wk\x00"

_I64 = struct.Struct("<q")
_U64_LE = np.dtype("<u8")


def blake3_hex(data: bytes, length: int = 32) -> str:
    """blake3 の16進ダイジェスト(既定32バイト=64桁)。"""
    return _blake3_mod.blake3(data).hexdigest(length=length)


def blake3_u64(data: bytes) -> int:
    """blake3 の先頭8バイトを little-endian の unsigned int64 として読む。"""
    return int.from_bytes(_blake3_mod.blake3(data).digest(length=8), "little")


def xxh64(data: bytes, seed: int = 0) -> int:
    """xxh64(変化検出・prefix キー・ルーティング用の高速ハッシュ)。"""
    return xxhash.xxh64_intdigest(data, seed)


def xxh64_array(chunks: Iterable[bytes], seed: int = 0) -> np.ndarray:
    """バイト列の列 → uint64 配列(セルB2/B4の変化検出用・要素ごとの逐次ループ=宣言済み)。"""
    return np.fromiter((xxh64(c, seed) for c in chunks), dtype=np.uint64)


def cbor_canonical(obj: Any) -> bytes:
    """CBOR 正準符号化(``cbor2.dumps(obj, canonical=True)``)。"""
    return cbor2.dumps(obj, canonical=True)


def sha256_cbor(obj: Any) -> str:
    """CBOR 正準符号化 → SHA-256 の16進(vLLM の ``--prefix-caching-hash-algo sha256_cbor`` と同名算法)。

    Note:
        vLLM 側の実装と**バイト一致することは保証しない**(向こうは内部のブロック表現を CBOR 化する)。
        本関数は「同じ算法名の、こちら側の決定論ハッシュ」であり、テープの ``params_hash`` と
        プロンプト鍵に使う(算法名を manifest と揃えるのが目的)。
    """
    return hashlib.sha256(cbor_canonical(obj)).hexdigest()


def _pack(tag: bytes, run_salt: bytes, *values: int) -> bytes:
    if not isinstance(run_salt, (bytes, bytearray, memoryview)):
        raise TypeError("run_salt は bytes")
    return bytes(run_salt) + tag + b"".join(_I64.pack(int(v)) for v in values)


def priority_key(run_salt: bytes, tick: int, resource_id: int, agent_id: int) -> int:
    """資源競合の優先度キー第2要素(運用設計書 §2.2)。

    ``blake3(run_salt ‖ b"pk\x00" ‖ i64le(tick) ‖ i64le(resource_id) ‖ i64le(agent_id))`` の
    先頭8バイト u64。第1要素(気づいた時刻=tick開始+δ_perc)は呼び出し側が持つ。
    """
    return blake3_u64(_pack(BLAKE3_TAG_PRIORITY, run_salt, tick, resource_id, agent_id))


def apply_key(run_salt: bytes, t_apply: int, agent_id: int) -> int:
    """LLM 応答の適用順キー第3要素(運用設計書 §2.4)。

    ``blake3(run_salt ‖ b"ak\x00" ‖ i64le(t_apply) ‖ i64le(agent_id))`` の先頭8バイト u64。
    完全な適用順は ``(t_apply, event_class, apply_key(...))`` の昇順(第1・第2要素は呼び出し側)。
    """
    return blake3_u64(_pack(BLAKE3_TAG_APPLY, run_salt, t_apply, agent_id))


def wake_tiebreak(run_salt: bytes, tick: int, class_rank: int, agent_id: int) -> int:
    """同時刻起床イベントのタイブレーク第3要素(運用設計書 §2.5)。

    ``blake3(run_salt ‖ b"wk\x00" ‖ i64le(tick) ‖ i64le(class_rank) ‖ i64le(agent_id))``。
    ID 順バイアス(v1 C-8)を断つのが目的なので、agent_id を最後の鍵に置いても
    実効順序はハッシュで撹拌される。
    """
    return blake3_u64(_pack(BLAKE3_TAG_WAKE, run_salt, tick, class_rank, agent_id))


def _hash_rows_u64(tag: bytes, run_salt: bytes, columns: Sequence[np.ndarray]) -> np.ndarray:
    """列(int64 配列)を行ごとに連結して blake3 → u64 配列。

    逐次ループ宣言: 行数ぶんの Python ループ1本(blake3 は要素ごとの呼び出しが必要)。
    """
    cols = [np.ascontiguousarray(np.asarray(c, dtype=np.int64).ravel()) for c in columns]
    n = cols[0].size
    for c in cols:
        if c.size != n:
            raise ValueError("全ての列は同じ長さでなければならない")
    if n == 0:
        return np.empty(0, dtype=np.uint64)
    rec = np.empty((n, len(cols)), dtype="<i8")
    for j, c in enumerate(cols):
        rec[:, j] = c
    width = 8 * len(cols)
    mv = memoryview(rec.reshape(-1).view(np.uint8))
    base = _blake3_mod.blake3(bytes(run_salt) + tag)
    joined = b"".join(
        [base.copy().update(mv[i * width : (i + 1) * width]).digest(length=8) for i in range(n)]
    )
    return np.frombuffer(joined, dtype=_U64_LE).astype(np.uint64, copy=True)


def priority_key_array(
    run_salt: bytes, tick: int, resource_ids: np.ndarray, agent_ids: np.ndarray
) -> np.ndarray:
    """``priority_key`` のベクトル版(同一 tick の全 intent 分)。"""
    resource_ids = np.asarray(resource_ids)
    agent_ids = np.asarray(agent_ids)
    ticks = np.full(resource_ids.shape, int(tick), dtype=np.int64)
    return _hash_rows_u64(BLAKE3_TAG_PRIORITY, run_salt, (ticks, resource_ids, agent_ids))


def apply_key_array(run_salt: bytes, t_apply: np.ndarray, agent_ids: np.ndarray) -> np.ndarray:
    """``apply_key`` のベクトル版(pending_apply の一括適用順づけ)。"""
    return _hash_rows_u64(BLAKE3_TAG_APPLY, run_salt, (np.asarray(t_apply), np.asarray(agent_ids)))


def wake_tiebreak_array(
    run_salt: bytes, tick: int, class_ranks: np.ndarray, agent_ids: np.ndarray
) -> np.ndarray:
    """``wake_tiebreak`` のベクトル版(1 tick 分の起床イベント)。"""
    class_ranks = np.asarray(class_ranks)
    agent_ids = np.asarray(agent_ids)
    ticks = np.full(class_ranks.shape, int(tick), dtype=np.int64)
    return _hash_rows_u64(BLAKE3_TAG_WAKE, run_salt, (ticks, class_ranks, agent_ids))
