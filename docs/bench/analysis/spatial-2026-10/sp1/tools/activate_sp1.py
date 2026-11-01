"""第 5 期 空間の段 1(ナビメッシュと移動): 世界資産の組み立て・差の表・活性化・戻し・確かめの道具。

段 10 の ``activate_pop43.py`` と同じ形(stage / plan / apply / verify / revert)。段 1 は**足すだけ**(本体の v2 の
ファイルは 1 本も置き換えない=``moved`` が 0 でなければ止める)。足すファイル=``nav1_*``(7 本)・``nav1_meta.json``・
``navmesh1.header.json``。``build_manifest.json`` は変えない(ナビメッシュは脇の段=``build.run`` の段の外)。

部分コマンド(リポの根で・作業木の ``src`` を ``PYTHONPATH`` に):

- ``stage``  : 本体の v2(``--base``)の直下のファイル(W17 のプロンプトと応答の jsonl を除く)と ``acceptance/`` を
  ``--out`` へ本物のコピーで写し(sha256 を照らす)、写した置き場で ``shibuya.build.space.navmesh1`` を回す。最後に
  ``MANIFEST.sha256``(全ファイル)と ``stage_build.json``。``--out2`` を渡すと同じ手順で 2 回目を組み、全ファイルの
  sha256 が一致するかを確かめる(2 回目の置き場は確かめの後に消す=``--keep-out2`` で残す)。
- ``plan``   : 本体の v2(``--live``)と組んだ資産(``--stage``)の sha256 の表(same/moved/added/kept_live_only)。
- ``apply``  : **親が実行する**(``--dry-run`` は確かめと一覧だけ)。(1) 本体の v2 が plan の「前」と同じか (2) 足す
  ファイルを写す (3) 全部の行が plan の「後」と同じか(違えば終了コード 3=``revert``)。
- ``revert`` : 足したファイルを消し、全部の行が plan の「前」と同じか確かめる。
- ``verify`` : 本体の v2 が plan の「後」/「前」と同じか(sha256 の表)。

ファイルの中身は読まない(sha256・md5・バイト数だけ)。絶対パスは記録に書かない。

逐次ループ宣言: ファイルの数ぶん(構築と活性化の 1 回きり・ランには入らない)。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]

#: 写さないファイル(W17 の構築の途中の入出力=エンジンは読まない)。
SKIP_PREFIXES: tuple[str, ...] = ("w17_prompts", "w17_responses", "w17_pilot_prompts", "w17_pilot_responses")
MANIFEST = "MANIFEST.sha256"
STAGE_RECORD = "stage_build.json"
STAGE_ONLY: tuple[str, ...] = (MANIFEST, STAGE_RECORD)
#: 段 1 が足すファイルの頭(これ以外が added / moved になったら止める)。
ADDED_PREFIXES: tuple[str, ...] = ("nav1_", "navmesh1.")


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def md5(p: Path) -> str:
    h = hashlib.md5()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def asset_files(root: Path) -> dict[str, Path]:
    """直下のファイル(W17 の jsonl を除く)と ``acceptance/`` の下のファイル → {相対パス: パス}。"""
    out: dict[str, Path] = {}
    for p in sorted(root.iterdir()):
        if p.is_file() and not (p.suffix == ".jsonl" and p.name.startswith(SKIP_PREFIXES)):
            out[p.name] = p
    acc = root / "acceptance"
    if acc.is_dir():
        for p in sorted(acc.iterdir()):
            if p.is_file():
                out["acceptance/" + p.name] = p
    return out


def build_hash(root: Path) -> str:
    p = root / "build_manifest.json"
    return str(json.loads(p.read_text(encoding="utf-8")).get("build_hash", "")) if p.exists() else ""


def _json(p: Path) -> Any:
    return json.loads(p.read_text(encoding="utf-8"))


def _write_json(p: Path, obj: Any) -> None:
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")


def _rel(p: Path) -> str:
    try:
        return Path(p).resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return Path(p).name


def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str((REPO / "src").resolve())
    return env


def stage_one(base: Path, out: Path, data: str) -> dict[str, Any]:
    """1 回の組み立て(``out`` は空か無い置き場)。"""
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"--out が空でない: {out.name}(作り直すなら消してから)")
    out.mkdir(parents=True, exist_ok=True)
    (out / "acceptance").mkdir(exist_ok=True)
    t0 = time.perf_counter()
    for rel, p in asset_files(base).items():
        dst = out / rel
        shutil.copy2(p, dst)
        if sha256(dst) != sha256(p):
            raise RuntimeError(f"写しの sha256 が違う: {rel}")
    times = {"copy_s": round(time.perf_counter() - t0, 1)}
    t1 = time.perf_counter()
    r = subprocess.run([sys.executable, "-m", "shibuya.build.space.navmesh1", "--data", data, "--world", str(out),
                        "--out", str(out)], env=_env(), cwd=str(REPO), capture_output=True, text=True,
                       encoding="utf-8")
    times["navmesh1_s"] = round(time.perf_counter() - t1, 1)
    if r.returncode != 0:
        print(r.stdout[-3000:], r.stderr[-5000:], file=sys.stderr)
        raise RuntimeError(f"navmesh1 が止まった(終了コード {r.returncode})")
    files = asset_files(out)
    lines = [f"{sha256(p)}  {rel}" for rel, p in files.items() if rel not in STAGE_ONLY]
    (out / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    head = _json(out / "navmesh1.header.json")
    nav_bytes = sum(p.stat().st_size for rel, p in files.items() if rel.startswith(ADDED_PREFIXES))
    rec = {"exit_code": r.returncode, "seconds": times, "build_hash": build_hash(out), "files": len(lines),
           "manifest_sha256": sha256(out / MANIFEST), "navmesh1_gates_failed": [
               k for k, v in head["gates"].items() if not v["pass"]], "nav_bytes": int(nav_bytes),
           "bytes": int(sum(p.stat().st_size for p in files.values()))}
    _write_json(out / STAGE_RECORD, rec)
    return rec


def cmd_stage(a: argparse.Namespace) -> int:
    base, out = Path(a.base), Path(a.out)
    runs = [stage_one(base, out, a.data)]
    print(f"組み立て 1: {runs[0]['files']} 本・ナビメッシュ {runs[0]['nav_bytes']:,} B・門の不合格 "
          f"{runs[0]['navmesh1_gates_failed']}")
    same = None
    diff: list[str] = []
    if a.out2:
        out2 = Path(a.out2)
        runs.append(stage_one(base, out2, a.data))
        m1 = (out / MANIFEST).read_text(encoding="utf-8").splitlines()
        m2 = (out2 / MANIFEST).read_text(encoding="utf-8").splitlines()
        diff = sorted(set(m1) ^ set(m2))
        same = not diff
        if not a.keep_out2:
            shutil.rmtree(out2)
    doc = {"schema": "sp1.stage/1", "base": _rel(base), "out": _rel(out), "runs": runs, "deterministic": same,
           "manifest_lines_differ": diff[:20]}
    print(json.dumps({"deterministic": same}, ensure_ascii=False))
    if a.record:
        _write_json(Path(a.record), doc)
    return 0 if same in (None, True) else 3


def plan_rows(live: Path, stage: Path) -> dict[str, Any]:
    fl = asset_files(live)
    fs = {k: v for k, v in asset_files(stage).items() if k not in STAGE_ONLY}
    rows: list[dict[str, Any]] = []
    for rel in sorted(set(fl) | set(fs)):
        b, s = fl.get(rel), fs.get(rel)
        hb = sha256(b) if b else ""
        hs = sha256(s) if s else ""
        action = ("kept_live_only" if s is None else "added" if b is None else "moved" if hb != hs else "same")
        rows.append({"path": rel, "action": action, "sha256_before": hb, "sha256_after": hs,
                     "md5_before": md5(b) if b else "", "md5_after": md5(s) if s else "",
                     "bytes_before": b.stat().st_size if b else 0, "bytes_after": s.stat().st_size if s else 0})
    return {"schema": "sp1.activation/1", "build_hash_before": build_hash(live), "build_hash_after": build_hash(stage),
            "counts": {k: sum(1 for r in rows if r["action"] == k) for k in ("same", "moved", "added",
                                                                            "kept_live_only")},
            "rows": rows}


def cmd_plan(a: argparse.Namespace) -> int:
    plan = plan_rows(Path(a.live), Path(a.stage))
    bad = [r["path"] for r in plan["rows"] if r["action"] == "moved"
           or (r["action"] == "added" and not r["path"].startswith(ADDED_PREFIXES))]
    rec = {k: v for k, v in plan.items() if k != "rows"}
    rec["changed"] = [r for r in plan["rows"] if r["action"] in ("added", "moved")]
    rec["unexpected"] = bad
    rec["rows"] = plan["rows"]
    if a.record:
        _write_json(Path(a.record), rec)
    c = plan["counts"]
    print(f"同じ {c['same']}・置き換え {c['moved']}・追加 {c['added']}・本体の v2 だけ {c['kept_live_only']}・"
          f"段 1 の外の変化 {len(bad)}")
    return 0 if not bad else 2


def _check(root: Path, rows: list[dict[str, Any]], want: str) -> list[str]:
    bad = []
    for r in rows:
        p = root / r["path"]
        if r.get("action") == "kept_live_only":
            sha = r["sha256_before"]
        else:
            sha = r["sha256_after"] if want == "after" else r["sha256_before"]
        if not sha:
            if p.exists():
                bad.append(f"有ってはいけない: {r['path']}")
            continue
        if not p.exists() or sha256(p) != sha:
            bad.append(f"sha256 が違う: {r['path']}")
    return bad


def cmd_apply(a: argparse.Namespace) -> int:
    live, stage = Path(a.live), Path(a.stage)
    plan = _json(Path(a.plan))
    if plan.get("unexpected"):
        print("段 1 の外の変化がある plan は当てない:", plan["unexpected"][:10], file=sys.stderr)
        return 2
    changed = plan["changed"]
    pre = _check(live, plan["rows"], "before")
    if pre:
        print("本体の v2 が plan の「前」と違う(止めた):", *pre[:10], sep="\n  ", file=sys.stderr)
        return 2
    print(f"足す {len(changed)} 本")
    if a.dry_run:
        for r in changed:
            print(f"  {r['action']:6s} {r['path']}")
        return 0
    for r in changed:
        shutil.copy2(stage / r["path"], live / r["path"])
    bad = _check(live, plan["rows"], "after")
    if bad or build_hash(live) != plan["build_hash_after"]:
        print("写した後の確かめに落ちた(revert で戻す):", *bad[:10], sep="\n  ", file=sys.stderr)
        return 3
    print(f"足した。build_hash {build_hash(live)[:16]}(変わらない)")
    return 0


def cmd_revert(a: argparse.Namespace) -> int:
    live = Path(a.live)
    plan = _json(Path(a.plan))
    for r in plan["changed"]:
        p = live / r["path"]
        if r["action"] == "added" and p.exists():
            p.unlink()
    bad = _check(live, plan["rows"], "before")
    if bad or build_hash(live) != plan["build_hash_before"]:
        print("戻した後の確かめに落ちた:", *bad[:10], sep="\n  ", file=sys.stderr)
        return 3
    print(f"戻した。build_hash {plan['build_hash_before'][:16]}")
    return 0


def cmd_verify(a: argparse.Namespace) -> int:
    live = Path(a.live)
    plan = _json(Path(a.plan))
    bad = _check(live, plan["rows"], a.want)
    want_bh = plan["build_hash_after"] if a.want == "after" else plan["build_hash_before"]
    ok = not bad and build_hash(live) == want_bh
    print(f"{a.want}: {'同じ' if ok else '違う'}(build_hash {build_hash(live)[:16]}・違うファイル {len(bad)})")
    for b in bad[:10]:
        print("  ", b)
    return 0 if ok else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("stage")
    sp.add_argument("--base", default="data/world/v2")
    sp.add_argument("--out", default="data/world/v2_stage_5-1")
    sp.add_argument("--out2", default="")
    sp.add_argument("--keep-out2", action="store_true")
    sp.add_argument("--data", default="data")
    sp.add_argument("--record", default="")
    sp = sub.add_parser("plan")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--stage", default="data/world/v2_stage_5-1")
    sp.add_argument("--record", default=str(HERE.parent / "activation_plan.json"))
    for name in ("apply", "verify", "revert"):
        sp = sub.add_parser(name)
        sp.add_argument("--live", default="data/world/v2")
        sp.add_argument("--stage", default="data/world/v2_stage_5-1")
        sp.add_argument("--plan", default=str(HERE.parent / "activation_plan.json"))
        if name == "apply":
            sp.add_argument("--dry-run", action="store_true")
        if name == "verify":
            sp.add_argument("--want", choices=("after", "before"), default="after")
    a = ap.parse_args(argv)
    return {"stage": cmd_stage, "plan": cmd_plan, "apply": cmd_apply, "revert": cmd_revert,
            "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
