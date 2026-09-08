"""core.serialize — SoA レジストリの checkpoint(.npz + zstd)と膨張率 M7 の測定。

正典
- 実装計画書 §5: 「checkpoint=.npz+zstd(**M7≤2.0x を機械検査**)」。
- 予算宣言表 M7: 「直列化↔in-RAM膨張率 **≤2.0x**」根拠=「**v1事故13.6倍(第141)の再発防止**」。
- 運用設計書 §1.4 T2: 同一 manifest×2 で全 checkpoint ハッシュ一致(本モジュールの
  ``state_hash`` 往復一致がその最小単位)。

**M7 の読み(expedient・両方の数字を出す)**
    M7 は比の分母を明示していない。zstd 圧縮後のファイルを分母にすると、SoA の疎な配列では
    圧縮が効くほど比が悪化する(圧縮が上手いことが「膨張」と判定される)ため、
    根拠に書かれた「**v1事故13.6倍の再発防止**」= *RAM 上の表現がシリアライズ表現より何倍に
    膨らむか* を測る、という読みを採る:

        ratio_vs_uncompressed = in_RAM バイト(Registry.bytes_total) / **非圧縮**シリアライズ長

    圧縮後ファイルに対する比 ``ratio_vs_file`` も同時に返し、どちらも報告する
    (どちらを正典にするかは**未決**——本モジュールは判定に前者を使う)。
    in-RAM は**プロセス RSS ではなく ``Registry.bytes_total()``**(配列実バイトの和)で測る
    (RSS は Python インタプリタ・アロケータ断片化を含み、フィールド追加の回帰検出に使えない)。

ファイル形式(自前規約=expedient・設計書は「.npz+zstd」までしか定めていない)
    ``zstd(np.savez(非圧縮) の zip バイト列)``。zip の中身は
      - ``__meta__``: uint8 配列(UTF-8 JSON。format/kind/n_entities/cap/decls/state_hash)
      - 各フィールド名: そのままの配列
    保存・読み込みとも**一時ファイル経由**(BytesIO を使わない=ピーク RAM を倍にしない)。

逐次ループ宣言(P4): フィールド数ぶんのループのみ(配列は丸ごと NumPy/zstd に渡す)。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import zstandard as zstd

from shibuya.core.soa import Registry

__all__ = [
    "CHECKPOINT_FORMAT",
    "CHECKPOINT_ZSTD_LEVEL",
    "M7_MAX_BLOAT_RATIO",
    "SaveResult",
    "BloatMeasurement",
    "save_registry",
    "load_registry",
    "measure_bloat",
]

#: ファイル形式の版(読み込み時に検査)。
CHECKPOINT_FORMAT = "shibuya.checkpoint/v1"
#: zstd 圧縮レベル(定数。3=zstandard 既定。速度/比のバランス=expedient)。
CHECKPOINT_ZSTD_LEVEL = 3
#: 予算行 M7 の上限。
M7_MAX_BLOAT_RATIO = 2.0

_META_KEY = "__meta__"
_ZSTD_MAX_WINDOW_LOG = 31  # 解凍側の窓上限(大きな checkpoint 用)


@dataclass(frozen=True)
class SaveResult:
    """``save_registry`` の結果。"""

    path: Path
    file_bytes: int
    uncompressed_bytes: int
    ram_bytes: int
    state_hash: str

    @property
    def compression_ratio(self) -> float:
        """非圧縮長 / ファイル長(大きいほどよく縮んだ)。"""
        return self.uncompressed_bytes / self.file_bytes if self.file_bytes else float("inf")


@dataclass(frozen=True)
class BloatMeasurement:
    """M7(直列化↔in-RAM 膨張率)の測定値。"""

    ram_bytes_after_load: int
    uncompressed_bytes: int
    file_bytes: int
    state_hash: str

    @property
    def ratio(self) -> float:
        """**M7 の判定に使う比** = in-RAM / 非圧縮シリアライズ長。"""
        return self.ram_bytes_after_load / self.uncompressed_bytes if self.uncompressed_bytes else float("inf")

    @property
    def ratio_vs_uncompressed(self) -> float:
        return self.ratio

    @property
    def ratio_vs_file(self) -> float:
        """参考値 = in-RAM / 圧縮後ファイル長(zstd が効くほど大きくなる)。"""
        return self.ram_bytes_after_load / self.file_bytes if self.file_bytes else float("inf")

    @property
    def within_m7(self) -> bool:
        return self.ratio <= M7_MAX_BLOAT_RATIO

    def as_text(self) -> str:
        return (
            f"M7: in-RAM {self.ram_bytes_after_load:,}B / 非圧縮 {self.uncompressed_bytes:,}B "
            f"= {self.ratio:.3f}x (上限 {M7_MAX_BLOAT_RATIO}x, "
            f"参考 in-RAM/圧縮後 {self.ratio_vs_file:.3f}x, ファイル {self.file_bytes:,}B)"
        )


def _meta_dict(reg: Registry) -> dict[str, Any]:
    return {
        "format": CHECKPOINT_FORMAT,
        "kind": reg.kind,
        "n_entities": reg.n_entities,
        "per_entity_byte_cap": reg.per_entity_byte_cap,
        "cap_source": reg.cap_source,
        "state_hash": reg.state_hash(),
        "fields": [
            {
                "name": d.name,
                "dtype": d.dtype.str,
                "shape_per_entity": list(d.shape_per_entity),
                "byte_budget_per_entity": d.byte_budget_per_entity,
                "mechanism": d.mechanism,
                "doc": d.doc,
            }
            for d in reg.decls
        ],
    }


def _tmp_path(path: Path, suffix: str) -> Path:
    return path.with_name(path.name + suffix)


def save_registry(
    reg: Registry, path: str | os.PathLike[str], level: int = CHECKPOINT_ZSTD_LEVEL
) -> SaveResult:
    """レジストリを ``.npz``(非圧縮)→ zstd で1ファイルに保存する。

    Args:
        reg: 保存するレジストリ。
        path: 出力パス(慣例 ``*.npz.zst``)。
        level: zstd 圧縮レベル。

    Returns:
        ``SaveResult``(ファイル長・非圧縮長・in-RAM バイト・state_hash)。
    """
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    raw = _tmp_path(out, ".raw.tmp")
    meta = _meta_dict(reg)
    meta_arr = np.frombuffer(
        json.dumps(meta, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8"),
        dtype=np.uint8,
    )
    try:
        with raw.open("wb") as fh:
            np.savez(fh, **{_META_KEY: meta_arr}, **reg.arrays)
        uncompressed = raw.stat().st_size
        cctx = zstd.ZstdCompressor(level=level)
        with raw.open("rb") as src, out.open("wb") as dst:
            cctx.copy_stream(src, dst)
    finally:
        if raw.exists():
            raw.unlink()
    return SaveResult(
        path=out,
        file_bytes=out.stat().st_size,
        uncompressed_bytes=uncompressed,
        ram_bytes=reg.bytes_total(),
        state_hash=meta["state_hash"],
    )


def _decompress_to_tmp(path: Path) -> tuple[Path, int]:
    raw = _tmp_path(path, ".load.tmp")
    dctx = zstd.ZstdDecompressor(max_window_size=2**_ZSTD_MAX_WINDOW_LOG)
    with Path(path).open("rb") as src, raw.open("wb") as dst:
        dctx.copy_stream(src, dst)
    return raw, raw.stat().st_size


def _registry_from_npz(npz: Any) -> Registry:
    meta = json.loads(bytes(npz[_META_KEY]).decode("utf-8"))
    if meta.get("format") != CHECKPOINT_FORMAT:
        raise ValueError(f"未知の checkpoint 形式: {meta.get('format')!r}")
    reg = Registry(
        meta["n_entities"],
        kind=meta["kind"],
        per_entity_byte_cap=meta["per_entity_byte_cap"],
    )
    reg.cap_source = meta.get("cap_source", "checkpoint 由来")
    for f in meta["fields"]:
        arr = reg.declare(
            f["name"],
            np.dtype(f["dtype"]),
            tuple(f["shape_per_entity"]),
            byte_budget_per_agent=f["byte_budget_per_entity"],
            mechanism=f["mechanism"],
            doc=f["doc"],
        )
        stored = npz[f["name"]]
        if stored.shape != arr.shape or stored.dtype != arr.dtype:
            raise ValueError(
                f"フィールド {f['name']!r} の形/dtype が不一致: "
                f"{stored.shape}/{stored.dtype} vs {arr.shape}/{arr.dtype}"
            )
        arr[...] = stored
    got = reg.state_hash()
    if got != meta["state_hash"]:
        raise ValueError(f"state_hash 不一致: 保存時 {meta['state_hash']} / 読込後 {got}")
    return reg


def load_registry(path: str | os.PathLike[str]) -> Registry:
    """``save_registry`` で書いたファイルを読み、``state_hash`` の一致を検査して返す。

    Raises:
        ValueError: 形式版・形/dtype・state_hash のいずれかが一致しない。
    """
    p = Path(path)
    raw, _ = _decompress_to_tmp(p)
    try:
        with np.load(raw, allow_pickle=False) as npz:
            return _registry_from_npz(npz)
    finally:
        if raw.exists():
            raw.unlink()


def measure_bloat(path: str | os.PathLike[str]) -> BloatMeasurement:
    """checkpoint を読み直して M7(膨張率)を測る。

    Returns:
        ``BloatMeasurement``: ``ram_bytes_after_load``(= ``Registry.bytes_total()``)・
        ``uncompressed_bytes``(zip 展開後のシリアライズ長)・``file_bytes``(zstd 後)・
        ``ratio``(= in-RAM / 非圧縮)。
    """
    p = Path(path)
    file_bytes = p.stat().st_size
    raw, uncompressed = _decompress_to_tmp(p)
    try:
        with np.load(raw, allow_pickle=False) as npz:
            reg = _registry_from_npz(npz)
    finally:
        if raw.exists():
            raw.unlink()
    return BloatMeasurement(
        ram_bytes_after_load=reg.bytes_total(),
        uncompressed_bytes=uncompressed,
        file_bytes=file_bytes,
        state_hash=reg.state_hash(),
    )
