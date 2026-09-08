"""manifest.canonical: run manifest の正規化・自己ハッシュ(run_id)・YAML入出力。

正典: docs/design/v2-run-manifest-concurrency.md §1.1(run_id=manifest正規化本文の自己ハッシュ)・
§1.4 T1(manifest自己整合・CI常時)。ハッシュは blake3(実装計画書§2 部品表)。

正規化本文の定義(この実装が正)::

    canonical_bytes(m) = json.dumps(
        model_dump(mode="json") から identity.run_id を **削除** したもの,
        sort_keys=True, ensure_ascii=False, separators=(",", ":")
    ).encode("utf-8")

- 辞書のキーは再帰的に昇順。**配列の順序は意味を持つので並べ替えない**
  (replicas・phases・data_assets・diagnostics.columns の順序は本文の一部)。
- ``identity.run_id`` は null 代入ではなく**キーごと削除**する。
  こうすると「run_id 未設定の manifest」と「run_id 設定済みの manifest」が同じ本文になり、
  自己参照(ハッシュの中に自分のハッシュ)が起きない。
- YAML のキー順・字下げ・改行幅・引用符は正規化で消えるため run_id に影響しない(T1)。
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import blake3
import yaml

from shibuya.manifest.schema import RunManifest

__all__ = [
    "canonical_bytes",
    "compute_run_id",
    "dump_yaml",
    "load_yaml",
    "normalized_yaml",
    "verify_run_id",
    "with_run_id",
]


def _sort_keys(obj: Any) -> Any:
    """dict のキーを再帰的に昇順へ。list の順序は保つ。"""
    if isinstance(obj, dict):
        return {key: _sort_keys(obj[key]) for key in sorted(obj)}
    if isinstance(obj, list):
        return [_sort_keys(item) for item in obj]
    return obj


def _plain(m: RunManifest) -> dict[str, Any]:
    """JSON 互換の素の dict(datetime→ISO文字列・Enum→値)。"""
    dumped = m.model_dump(mode="json")
    if not isinstance(dumped, dict):  # pragma: no cover - pydantic の保証
        raise TypeError("RunManifest.model_dump が dict を返しませんでした")
    return dumped


def canonical_bytes(m: RunManifest) -> bytes:
    """正規化本文(run_id を除いた決定論的 JSON バイト列)を返す。"""
    data = _plain(m)
    identity = data.get("identity")
    if isinstance(identity, dict):
        identity.pop("run_id", None)
    return json.dumps(
        _sort_keys(data),
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")


def compute_run_id(m: RunManifest) -> str:
    """run_id = blake3(正規化本文) の16進文字列(64桁)。"""
    return blake3.blake3(canonical_bytes(m)).hexdigest()


def with_run_id(m: RunManifest) -> RunManifest:
    """``identity.run_id`` を自己ハッシュで埋めた**新しい** manifest を返す。"""
    data = _plain(m)
    data["identity"]["run_id"] = compute_run_id(m)
    return RunManifest.model_validate(data)


def verify_run_id(m: RunManifest) -> bool:
    """T1: 記録された run_id が正規化本文のハッシュと一致するか。"""
    return m.identity.run_id is not None and m.identity.run_id == compute_run_id(m)


def normalized_yaml(m: RunManifest) -> str:
    """決定論的な YAML 文字列(キー昇順・UTF-8そのまま・ブロック形式)。"""
    return yaml.safe_dump(
        _sort_keys(_plain(m)),
        sort_keys=True,
        allow_unicode=True,
        default_flow_style=False,
        width=4096,
    )


def load_yaml(path: str | Path) -> RunManifest:
    """YAML ファイルを読んで検証済み ``RunManifest`` を返す。"""
    text = Path(path).read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError(f"manifest YAML の最上位はマッピングである必要があります: {path}")
    return RunManifest.model_validate(data)


def dump_yaml(m: RunManifest, path: str | Path) -> Path:
    """``normalized_yaml`` の内容を UTF-8 で書き出し、書いたパスを返す。"""
    out = Path(path)
    if out.parent != Path(""):
        out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(normalized_yaml(m), encoding="utf-8")
    return out
