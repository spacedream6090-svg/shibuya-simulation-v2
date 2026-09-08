"""U8 run manifest: 往復一致・自己ハッシュ(T1)・機械化される規則のテスト。

正典: docs/design/v2-run-manifest-concurrency.md §1.2(13節スキーマ)・§1.4 T1/T9。
"""

from __future__ import annotations

import copy
from pathlib import Path
from typing import Any

import pytest
import yaml
from pydantic import ValidationError

from shibuya.manifest import (
    CONSERVATION_CHECKS,
    DIAG_COLUMNS,
    RunManifest,
    canonical_bytes,
    compute_run_id,
    dump_yaml,
    load_yaml,
    verify_run_id,
    with_run_id,
)

FIXTURE = Path(__file__).parent / "fixtures" / "manifest_example.yaml"


# --- ヘルパ ------------------------------------------------------------------
def _raw() -> dict[str, Any]:
    """フィクスチャを素の dict で読む(モデル検証は通さない)。"""
    return yaml.safe_load(FIXTURE.read_text(encoding="utf-8"))


def _manifest_from(data: dict[str, Any]) -> RunManifest:
    return RunManifest.model_validate(data)


def _reverse_keys(obj: Any) -> Any:
    """dict のキー順を再帰的に逆転させる(list の順序は本文の一部なので保つ)。"""
    if isinstance(obj, dict):
        return {key: _reverse_keys(obj[key]) for key in reversed(list(obj))}
    if isinstance(obj, list):
        return [_reverse_keys(item) for item in obj]
    return obj


# --- 往復・自己ハッシュ ------------------------------------------------------
def test_roundtrip_yaml(tmp_path: Path) -> None:
    """load → with_run_id → dump → load でモデルも正規化本文も一致する。"""
    m = load_yaml(FIXTURE)
    stamped = with_run_id(m)

    out = dump_yaml(stamped, tmp_path / "manifest.yaml")
    assert out.exists()

    reloaded = load_yaml(out)

    assert reloaded == stamped
    assert canonical_bytes(reloaded) == canonical_bytes(stamped)
    assert reloaded.identity.run_id == stamped.identity.run_id
    # 13節が全て往復している
    assert set(reloaded.model_dump().keys()) == set(stamped.model_dump().keys())
    assert len(reloaded.model_dump()) == 13


def test_t1_self_hash() -> None:
    """T1: run_id = blake3(正規化本文)。run_id 自身は本文に入らない。"""
    m = load_yaml(FIXTURE)
    # プレースホルダの run_id は本文から除かれるので、押印前後でハッシュが変わらない
    expected = compute_run_id(m)
    stamped = with_run_id(m)

    assert stamped.identity.run_id == expected
    assert verify_run_id(stamped) is True
    assert len(expected) == 64
    assert compute_run_id(stamped) == expected
    # 本文に run_id が含まれていないこと
    assert b'"run_id"' not in canonical_bytes(stamped)
    # 二度押印しても同じ(冪等)
    assert with_run_id(stamped).identity.run_id == expected


def test_run_id_mismatch_detected() -> None:
    """記録された run_id が本文と食い違えば verify は False。"""
    m = with_run_id(load_yaml(FIXTURE))
    data = m.model_dump(mode="json")
    data["identity"]["run_id"] = "0" * 64
    assert verify_run_id(_manifest_from(data)) is False


def test_key_order_and_whitespace_invariance(tmp_path: Path) -> None:
    """YAML のキー順・字下げ・改行幅・引用符は run_id に影響しない。"""
    baseline = compute_run_id(load_yaml(FIXTURE))

    shuffled = _reverse_keys(_raw())
    alt = tmp_path / "alt.yaml"
    alt.write_text(
        yaml.safe_dump(
            shuffled,
            sort_keys=False,          # キー順を逆転したまま出す
            allow_unicode=True,
            default_flow_style=False,
            indent=7,                 # 字下げを変える
            width=30,                 # 折り返し位置を変える
        ),
        encoding="utf-8",
    )
    assert alt.read_text(encoding="utf-8") != FIXTURE.read_text(encoding="utf-8")
    assert compute_run_id(load_yaml(alt)) == baseline

    # フロー形式(1行寄り)でも同じ
    flow = tmp_path / "flow.yaml"
    flow.write_text(
        yaml.safe_dump(_raw(), sort_keys=True, allow_unicode=True, default_flow_style=True),
        encoding="utf-8",
    )
    assert compute_run_id(load_yaml(flow)) == baseline


def test_field_change_changes_run_id() -> None:
    """本文の1欄が変われば run_id が変わる(封印後の変更は新 run_id)。"""
    base = load_yaml(FIXTURE)
    baseline = compute_run_id(base)

    for path, value in (
        (("settings", "n_agents"), 5001),
        (("rng", "master_seed"), 20260909),
        (("llm_fleet", "cache_salt"), "production"),
        (("identity", "label"), "別のラベル"),
    ):
        data = copy.deepcopy(_raw())
        node: Any = data
        for key in path[:-1]:
            node = node[key]
        assert node[path[-1]] != value
        node[path[-1]] = value
        assert compute_run_id(_manifest_from(data)) != baseline, path

    # 配列の順序も本文の一部(phases は固定列なので diagnostics.columns の順序で検査)
    data = copy.deepcopy(_raw())
    cols = data["output"]["diagnostics"]["columns"]
    assert len(cols) >= 2
    data["output"]["diagnostics"]["columns"] = list(reversed(cols))
    assert compute_run_id(_manifest_from(data)) != baseline

    # run_id 欄そのものは本文に入らない=変えてもハッシュは動かない
    data = copy.deepcopy(_raw())
    data["identity"]["run_id"] = "deadbeef"
    assert compute_run_id(_manifest_from(data)) == baseline


# --- 機械化される規則 --------------------------------------------------------
def test_dirty_rejected_for_holdout() -> None:
    """規則(a): dirty=true は較正・holdout に使えない。"""
    for mode in ("calibration", "holdout"):
        data = copy.deepcopy(_raw())
        data["identity"]["mode"] = mode
        data["code"]["dirty"] = True
        with pytest.raises(ValidationError) as exc:
            _manifest_from(data)
        assert "規則(a)" in str(exc.value)

    # smoke/ablation/production では dirty=true は通る
    for mode in ("smoke", "ablation", "production"):
        data = copy.deepcopy(_raw())
        data["identity"]["mode"] = mode
        data["code"]["dirty"] = True
        assert _manifest_from(data).code.dirty is True


def test_opened_layer_rejected_outside_holdout() -> None:
    """規則(b): mode≠holdout で opened=true があれば起動拒否。"""
    data = copy.deepcopy(_raw())
    data["holdout_seal"]["layers"][0]["opened"] = True
    with pytest.raises(ValidationError) as exc:
        _manifest_from(data)
    message = str(exc.value)
    assert "規則(b)" in message
    assert "kddi_shape_5metrics" in message

    # mode=holdout なら opened=true を許す(dirty は false のまま)
    data["identity"]["mode"] = "holdout"
    m = _manifest_from(data)
    assert m.holdout_seal.layers[0].opened is True


def test_batch_invariant_required_for_verification() -> None:
    """規則(c): 検証ランは sha256_cbor + VLLM_BATCH_INVARIANT=1。"""
    data = copy.deepcopy(_raw())
    data["identity"]["mode"] = "calibration"
    data["llm_fleet"]["prefix_caching_hash_algo"] = "builtin"
    with pytest.raises(ValidationError) as exc:
        _manifest_from(data)
    assert "規則(c)" in str(exc.value)

    data = copy.deepcopy(_raw())
    data["identity"]["mode"] = "holdout"
    data["llm_fleet"]["env"]["VLLM_BATCH_INVARIANT"] = "0"
    with pytest.raises(ValidationError) as exc:
        _manifest_from(data)
    assert "VLLM_BATCH_INVARIANT" in str(exc.value)

    # 欄ごと無い場合も拒否
    data = copy.deepcopy(_raw())
    data["identity"]["mode"] = "holdout"
    del data["llm_fleet"]["env"]["VLLM_BATCH_INVARIANT"]
    with pytest.raises(ValidationError):
        _manifest_from(data)


@pytest.mark.parametrize(
    ("section", "field", "value"),
    [
        ("hardware", "profile", "gpu-node 192.168.10.7"),
        ("hardware", "os", "Ubuntu 24.04 @ 10.0.0.5"),
        ("output", "journal", "http://example.invalid/runs/journal.parquet"),
        ("output", "llm_tape", "https://example.invalid/tape.parquet"),
    ],
)
def test_ip_in_hardware_rejected(section: str, field: str, value: str) -> None:
    """規則(d): ハードウェア節・出力節に IP / URL を書かない。"""
    data = copy.deepcopy(_raw())
    data[section][field] = value
    with pytest.raises(ValidationError) as exc:
        _manifest_from(data)
    assert "規則(d)" in str(exc.value)


def test_clean_hardware_and_output_accepted() -> None:
    """規則(d)の偽陽性検査: 版番号(3成分)や相対パスは通る。"""
    data = copy.deepcopy(_raw())
    data["hardware"]["os"] = "Ubuntu 24.04.1 LTS"
    data["hardware"]["gpus"] = ["NVIDIA A5000 (driver 570.86.15)"]
    data["output"]["checkpoints"] = "runs/2026-09-08/checkpoints/"
    assert _manifest_from(data).hardware.os == "Ubuntu 24.04.1 LTS"


def test_diag_columns_required_for_calibration() -> None:
    """規則(e)/T9: 較正・holdout は診断行4列+保存則2検算が必要。"""
    required = list(DIAG_COLUMNS) + list(CONSERVATION_CHECKS)

    for dropped in required:
        data = copy.deepcopy(_raw())
        data["identity"]["mode"] = "calibration"
        data["output"]["diagnostics"]["columns"] = [
            c for c in data["output"]["diagnostics"]["columns"] if c != dropped
        ]
        with pytest.raises(ValidationError) as exc:
            _manifest_from(data)
        assert "規則(e)" in str(exc.value)
        assert dropped in str(exc.value)

    # 6つ揃っていれば通る
    data = copy.deepcopy(_raw())
    data["identity"]["mode"] = "calibration"
    assert set(required) <= set(_manifest_from(data).output.diagnostics.columns)

    # smoke では欠けていても通る(T9のゲートは較正・holdoutのみ)
    data = copy.deepcopy(_raw())
    data["output"]["diagnostics"]["columns"] = ["deferred"]
    assert _manifest_from(data).output.diagnostics.columns == ["deferred"]


# --- スキーマの締まり --------------------------------------------------------
def test_extra_field_forbidden() -> None:
    """extra="forbid": 知らない欄は拒否(欄の作り足しを検出)。"""
    data = copy.deepcopy(_raw())
    data["identity"]["hostname"] = "some-box"
    with pytest.raises(ValidationError):
        _manifest_from(data)


def test_rng_scheme_is_fixed_literal() -> None:
    """乱数方式は numpy-philox4x64 固定(実装計画書§2 部品表)。"""
    data = copy.deepcopy(_raw())
    data["rng"]["scheme"] = "mt19937"
    with pytest.raises(ValidationError):
        _manifest_from(data)


def test_manifest_is_frozen() -> None:
    """frozen=True: 読み込み後の書き換えを禁止(押印後の改変防止)。"""
    m = load_yaml(FIXTURE)
    with pytest.raises(ValidationError):
        m.identity.run_id = "x"  # type: ignore[misc]
