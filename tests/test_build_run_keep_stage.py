"""``python -m shibuya.build.run`` の凍結段の口(``--keep-stage``)と安全弁(第281 親決定 Q2 (b))。

- ``--keep-stage W17``: その段は再構築せず、ディスク上の出力と既存ヘッダをそのまま採る。
  走らせた段+保った段で全段階がそろえば ``build_manifest.json`` を**正典として**書き、
  ``kept: ["W17"]`` を記録する。
- 安全弁: 走らせる段の出力の md5 が昇格版と一致したら、``--stage <段>`` の明示が無い限り
  何も走らせずに止まる(終了コード 2)。

段階の本体は走らせない(``run_all`` を差し替える)ので、データ無しで CI でも走る。
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from shibuya.build import run as build_run
from shibuya.build.geo import common as C

REPO_ROOT = Path(__file__).resolve().parents[1]


def _write_stage(out: Path, stage: str, payload: bytes) -> None:
    """偽の段階: 出力 1 本+ヘッダ(manifest が読む欄だけ)。"""
    name = f"{stage.lower()}_out.bin"
    (out / name).write_bytes(payload)
    header = {
        "stage": stage,
        "stage_version": "0.0.0",
        "input_hash": "0" * 64,
        "param_hash": "0" * 64,
        "outputs": [
            {"path": name, "sha256": C.sha256_file(out / name), "bytes": len(payload), "rows": 0}
        ],
        "gates": {},
        "catalog_classes": [],
        "expedients": [],
    }
    (out / f"{stage}.header.json").write_bytes(C.canonical_json_bytes(header) + b"\n")


@pytest.fixture
def fake_world(tmp_path, monkeypatch):
    """全段階の偽ヘッダが在る out と、呼ばれた段を記録する偽の ``run_all``。"""
    out = tmp_path / "world"
    out.mkdir()
    for st in build_run.ALL_STAGES:
        _write_stage(out, st, f"old {st}".encode())
    calls: list[list[str]] = []

    def fake_run_all(ctx, stages, verbose=True):
        calls.append(list(stages))
        for st in stages:
            _write_stage(ctx.out, st, f"new {st}".encode())
        return []

    monkeypatch.setattr(build_run, "run_all", fake_run_all)
    return out, calls


def test_keep_stage_leaves_the_kept_outputs_and_header_untouched(fake_world, tmp_path):
    out, calls = fake_world
    kept_header = (out / "W17.header.json").read_bytes()
    kept_output = (out / "w17_out.bin").read_bytes()

    rc = build_run.main(["--out", str(out), "--data", str(tmp_path), "--keep-stage", "W17", "--quiet"])

    assert rc == 0
    # W17 は走らせていない・他の段は全部走った
    assert calls == [[s for s in build_run.ALL_STAGES if s != "W17"]]
    # 保った段の出力とヘッダはバイト不変
    assert (out / "W17.header.json").read_bytes() == kept_header
    assert (out / "w17_out.bin").read_bytes() == kept_output
    # 正典の manifest(partial ではない)に kept が載る
    assert not (out / build_run.PARTIAL_MANIFEST_NAME).exists()
    manifest = json.loads((out / build_run.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert "partial" not in manifest
    assert manifest["kept"] == ["W17"]
    assert manifest["stage_order"] == list(build_run.ALL_STAGES)
    # build_hash は保った段の出力 sha256 を含む全段階の連結
    digests = []
    for st in build_run.ALL_STAGES:
        h = json.loads((out / f"{st}.header.json").read_text(encoding="utf-8"))
        digests += [o["sha256"] for o in h["outputs"]]
    assert manifest["build_hash"] == C.sha256_bytes("".join(digests).encode("utf-8"))


def test_keep_stage_refuses_a_header_whose_output_does_not_match(fake_world, tmp_path):
    """保つ段の出力がヘッダと合わなければ、何も走らせずに止まる。"""
    out, calls = fake_world
    (out / "w17_out.bin").write_bytes(b"tampered")
    rc = build_run.main(["--out", str(out), "--data", str(tmp_path), "--keep-stage", "W17", "--quiet"])
    assert rc == 2
    assert calls == []


def test_keep_stage_and_stage_on_the_same_stage_is_a_usage_error(fake_world, tmp_path):
    out, calls = fake_world
    rc = build_run.main(
        ["--out", str(out), "--data", str(tmp_path), "--stage", "W17", "--keep-stage", "W17"]
    )
    assert rc == 2
    assert calls == []


def test_refuses_to_overwrite_the_promoted_output_unless_the_stage_is_explicit(
    fake_world, tmp_path, monkeypatch
):
    """安全弁: 昇格版の md5 に一致する出力は ``--stage`` の明示なしには上書きしない。"""
    out, calls = fake_world
    promoted = out / "w17_schedule.parquet"
    promoted.write_bytes(b"promoted W17 v2")
    md5 = hashlib.md5(promoted.read_bytes()).hexdigest()
    monkeypatch.setattr(
        build_run, "PROTECTED_OUTPUTS", {"W17": {"w17_schedule.parquet": (md5[:12],)}}
    )

    # 既定(全段階)は拒否=何も走らない・ファイルも manifest も書かない
    rc = build_run.main(["--out", str(out), "--data", str(tmp_path), "--quiet"])
    assert rc == 2
    assert calls == []
    assert promoted.read_bytes() == b"promoted W17 v2"
    assert not (out / build_run.MANIFEST_NAME).exists()

    # --keep-stage W17 なら W17 を走らせないので通る
    rc = build_run.main(["--out", str(out), "--data", str(tmp_path), "--keep-stage", "W17", "--quiet"])
    assert rc == 0 and "W17" not in calls[-1]

    # --stage W17 を明示したときだけ作り直す
    rc = build_run.main(["--out", str(out), "--data", str(tmp_path), "--stage", "W17", "--quiet"])
    assert rc == 0 and calls[-1] == ["W17"]


def test_the_protected_md5_is_the_promoted_w17_golden_key():
    """安全弁の md5 は golden 表の鍵(W17 v2・第168 昇格)と同じ値。実資産があれば当たることも見る。"""
    assert build_run.PROTECTED_OUTPUTS["W17"]["w17_schedule.parquet"] == ("3113e9ba7abb",)
    real = REPO_ROOT / "data" / "world" / "v2"
    p = real / "w17_schedule.parquet"
    if not p.exists():
        pytest.skip("実世界資産が無い")
    if not hashlib.md5(p.read_bytes()).hexdigest().startswith("3113e9ba7abb"):
        pytest.skip("実 W17 が昇格版ではない")
    # 読むだけの関数(何も走らせない)
    assert build_run.protected_output_hits(real, ["W17"], set())
    assert build_run.protected_output_hits(real, ["W17"], {"W17"}) == []
