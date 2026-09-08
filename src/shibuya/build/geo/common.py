"""build.geo.common — 全段階で共有する純粋ヘルパ(ハッシュ・ヘッダ・座標・格子・層バンド)。

設計根拠
- §0-1 決定論: 各段階=純関数。出力ヘッダに ``input_hash``(入力SHA256連結)・``param_hash``
  (canonical JSON)・``stage_version`` を書く。時刻など非決定な値はヘッダに入れない
  (= 再構築でヘッダもバイト一致する)。
- §0-2 版の凍結・§0-6 カタログ写像: ヘッダに ``catalog_classes``(世界カタログ v0.2 のクラス名)を書く。
- §0-7 expedient 登録: ヘッダに ``expedients`` を列挙する。
- 実装計画書 §5 データ層: 表=Parquet(pyarrow)・行列=.npy/.npz・小辞書=JSON。
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Sequence

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

__all__ = [
    "ORIGIN_LATLON",
    "GROUND0_M",
    "M_PER_DEG_LAT",
    "M_PER_DEG_LON",
    "CELL_M",
    "BAND_OF_LAYER",
    "BANDS",
    "latlon_to_local",
    "band_of_layer",
    "node_layer_from_incident",
    "grid_ij",
    "place_id",
    "sha256_file",
    "sha256_bytes",
    "canonical_json_bytes",
    "input_hash",
    "param_hash",
    "Gate",
    "StageResult",
    "write_json",
    "write_parquet",
    "write_npy",
    "write_npz",
    "write_header",
    "load_json",
    "read_parquet_columns",
    "Ctx",
]

# --- W0 で凍結する座標系(§1 W0・D-W1)------------------------------------------------
#: 原点(緯度, 経度)。OSM meta / PLATEAU plateau_index.params / tran_lod3 の3ファイルが同値。
ORIGIN_LATLON: tuple[float, float] = (35.6595, 139.70062)
#: 地盤高の基準 [m](PLATEAU DEM 由来)。terrain.json / extras.json / plateau_index が同値。
GROUND0_M: float = 15.18
#: 緯度1度あたりのメートル(v1 の local-m 定義。PLATEAU tran_lod3 の
#: clip_rect ↔ latlon_bbox から相対誤差 <1e-8 で復元した定数)。
M_PER_DEG_LAT: float = 111132.9
#: 経度1度あたりのメートル = 111320 * cos(原点緯度)(同上の復元)。
M_PER_DEG_LON: float = 111320.0 * math.cos(math.radians(ORIGIN_LATLON[0]))

#: セル格子の一辺 [m](D-W2・格子原点=世界原点(0,0))。
CELL_M: float = 100.0

#: OSM layer 素値 → バンド(D-W3)。
BAND_OF_LAYER: dict[int, str] = {-2: "UG", -1: "UG", 0: "GL", 1: "DECK", 2: "DECK"}
#: バンドの並び(place_id・ゲート出力の安定順)。
BANDS: tuple[str, ...] = ("UG", "GL", "DECK")


def latlon_to_local(lat: float, lon: float) -> tuple[float, float]:
    """WGS84 (lat, lon) → 世界ローカル平面 (x=東, y=北) [m]。"""
    return (
        (lon - ORIGIN_LATLON[1]) * M_PER_DEG_LON,
        (lat - ORIGIN_LATLON[0]) * M_PER_DEG_LAT,
    )


def band_of_layer(layer: int | None) -> str:
    """OSM layer 素値 → バンド。未タグ(None)は 0 とみなす(D-W3)。

    Raises:
        ValueError: 表にない layer 値(|layer|>2)。
    """
    lay = 0 if layer is None else int(layer)
    try:
        return BAND_OF_LAYER[lay]
    except KeyError as exc:  # pragma: no cover - 現データには存在しない
        raise ValueError(f"層バンド表にない layer 値: {lay}") from exc


def node_layer_from_incident(layers: Sequence[int]) -> int:
    """接続エッジ層の多数決 → ノード層(D-W3)。

    同数のときは 0 を優先し、0 が候補になければ |layer| 最小(さらに同点なら値が小さい方)。
    接続エッジが無いノードは 0。
    """
    if not layers:
        return 0
    counts: dict[int, int] = {}
    for lay in layers:
        counts[int(lay)] = counts.get(int(lay), 0) + 1
    top = max(counts.values())
    cand = sorted(lay for lay, c in counts.items() if c == top)
    if 0 in cand:
        return 0
    return sorted(cand, key=lambda lay: (abs(lay), lay))[0]


def grid_ij(x: float, y: float, cell_m: float = CELL_M) -> tuple[int, int]:
    """座標 → 100m 格子の (ix, iy)。格子原点=世界原点、床関数。"""
    return (int(math.floor(x / cell_m)), int(math.floor(y / cell_m)))


def place_id(ix: int, iy: int, band: str) -> str:
    """セル ID 文字列 ``g{ix}_{iy}_{band}``(D-W2)。"""
    return f"g{ix}_{iy}_{band}"


# --- ハッシュ(§0-1)------------------------------------------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    """canonical JSON(キー整列・空白なし・UTF-8・非ASCIIはそのまま)。"""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def input_hash(paths: Sequence[Path]) -> str:
    """入力ファイル群の SHA256 を **与えられた順に** 連結して再ハッシュする。

    連結形式 = 各ファイルの hex digest を改行区切りで並べた UTF-8 文字列。
    """
    digests = [sha256_file(p) for p in paths]
    return sha256_bytes("\n".join(digests).encode("utf-8"))


def param_hash(params: Any) -> str:
    return sha256_bytes(canonical_json_bytes(params))


# --- ゲート・段階結果 ----------------------------------------------------------------


@dataclass(frozen=True)
class Gate:
    """機械検査1件。``expected`` が None のときは「報告のみ(仕様書の空欄)」。"""

    name: str
    value: Any
    expected: Any = None
    passed: bool | None = None

    def to_json(self) -> dict[str, Any]:
        ok = self.passed
        if ok is None:
            ok = True if self.expected is None else bool(self.value == self.expected)
        return {"value": self.value, "expected": self.expected, "pass": bool(ok)}


@dataclass
class StageResult:
    stage: str
    stage_version: str
    input_hash: str
    param_hash: str
    params: dict[str, Any]
    outputs: list[dict[str, Any]] = field(default_factory=list)
    gates: list[Gate] = field(default_factory=list)
    catalog_classes: list[str] = field(default_factory=list)
    expedients: list[str] = field(default_factory=list)
    notes: dict[str, Any] = field(default_factory=dict)

    @property
    def all_passed(self) -> bool:
        return all(g.to_json()["pass"] for g in self.gates)

    def to_json(self) -> dict[str, Any]:
        return {
            "stage": self.stage,
            "stage_version": self.stage_version,
            "input_hash": self.input_hash,
            "param_hash": self.param_hash,
            "params": self.params,
            "outputs": self.outputs,
            "gates": {g.name: g.to_json() for g in self.gates},
            "catalog_classes": self.catalog_classes,
            "expedients": self.expedients,
            "notes": self.notes,
        }


# --- 出力 I/O -------------------------------------------------------------------------

_PARQUET_KW: dict[str, Any] = dict(
    compression="zstd", compression_level=3, version="2.6", write_statistics=False
)


def _record(out_dir: Path, path: Path, rows: int | None) -> dict[str, Any]:
    return {
        "path": path.relative_to(out_dir).as_posix(),
        "sha256": sha256_file(path),
        "bytes": path.stat().st_size,
        "rows": rows,
    }


def write_json(out_dir: Path, name: str, obj: Any, rows: int | None = None) -> dict[str, Any]:
    path = out_dir / name
    path.write_bytes(canonical_json_bytes(obj) + b"\n")
    return _record(out_dir, path, rows)


def write_parquet(
    out_dir: Path, name: str, columns: dict[str, Any], schema: pa.Schema | None = None
) -> dict[str, Any]:
    """列辞書 → Parquet(zstd)。列順=辞書順。"""
    if schema is not None:
        table = pa.table(
            {k: pa.array(v, type=schema.field(k).type) for k, v in columns.items()}, schema=schema
        )
    else:
        table = pa.table({k: pa.array(v) for k, v in columns.items()})
    path = out_dir / name
    pq.write_table(table, path, **_PARQUET_KW)
    return _record(out_dir, path, table.num_rows)


def write_npy(out_dir: Path, name: str, arr: np.ndarray) -> dict[str, Any]:
    path = out_dir / name
    with open(path, "wb") as fh:
        np.save(fh, arr, allow_pickle=False)
    return _record(out_dir, path, int(arr.shape[0]) if arr.ndim else None)


def write_npz(out_dir: Path, name: str, **arrays: np.ndarray) -> dict[str, Any]:
    """非圧縮 .npz。``np.savez`` は zip 内に日時を書かないので再構築でバイト一致する。"""
    path = out_dir / name
    with open(path, "wb") as fh:
        np.savez(fh, **arrays)
    rows = int(next(iter(arrays.values())).shape[0]) if arrays else None
    return _record(out_dir, path, rows)


def write_header(out_dir: Path, result: StageResult) -> Path:
    path = out_dir / f"{result.stage}.header.json"
    path.write_bytes(canonical_json_bytes(result.to_json()) + b"\n")
    return path


def load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def read_parquet_columns(path: Path, names: Iterable[str] | None = None) -> dict[str, list]:
    """Parquet → 列辞書(Python リスト)。段階間の受け渡し用。"""
    table = pq.read_table(path, columns=list(names) if names is not None else None)
    return {name: table.column(name).to_pylist() for name in table.schema.names}


@dataclass(frozen=True)
class Ctx:
    """段階の実行文脈(入力データ根・出力先)。"""

    data: Path
    out: Path

    def osm(self) -> Path:
        return self.data / "realworld" / "osm" / "shibuya_osm_wide_v8.json"

    def path(self, *parts: str) -> Path:
        return self.data.joinpath(*parts)
