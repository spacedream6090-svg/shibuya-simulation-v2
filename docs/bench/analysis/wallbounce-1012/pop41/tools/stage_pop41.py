"""第 4 期 4-1 段 1〜3(W21): 世界資産 ``data/world/v2_stage_4-1`` の組み立て・差の表・写し・戻し・確かめ。

``vb24/tools/activate_vb24.py`` と同じ形(stage / plan / apply / revert / verify / materialize)。**本段では apply しない**
(W16 との差し替えは段 10=4-3・親が決める)。W21 は ``build.run`` の段に入れないので、組んだ資産は「本体の v2 の写し+
W21 の 6 本」で、``build_manifest.json`` と build_hash は本体の v2 と同じ(既定は不変)。

部分コマンド(リポの根で・作業木の ``src`` を ``PYTHONPATH`` に):

- ``stage``  : 本体の v2 の直下のファイル(W17 のプロンプトと応答の jsonl を除く)と ``acceptance/`` を ``--out`` へ本物の
  コピーで写し(sha256 を照らす)、W21 を ``--out`` に組む。``--runs 2`` で 2 回目を ``--scratch`` に組み、W21 の 6 本の
  sha256 が 1 回目と同じことを確かめる(決定的)。最後に ``--out`` の全部のファイルの ``MANIFEST.sha256`` を書く。
- ``plan``   : 本体の v2(``--live``)と組んだ資産(``--stage``)を sha256 で比べ、動いたファイル(added/moved)だけを
  ``--steps`` に写して ``MANIFEST.sha256`` と ``plan.json`` を書く(``--dry-run`` は書かない)。``--record`` に同じ表(絶対パスなし)。
- ``apply``  : **親が実行する**。``--dry-run`` は前提の確かめと写す一覧の表示だけ。
- ``revert`` / ``verify`` / ``materialize``: activate_vb24.py と同じ(退避から戻す・前か後かを確かめる・前の資産を組む)。

ファイルの中身は読まない(sha256・md5・バイト数だけ)。build_hash は ``build_manifest.json`` の 1 欄だけを読む。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]

SKIP_PREFIXES: tuple[str, ...] = ("w17_prompts", "w17_responses", "w17_pilot_prompts", "w17_pilot_responses")
W21_FILES: tuple[str, ...] = ("w21_frame.json", "w21_households.parquet", "w21_persons.parquet", "w21_checks.json",
                              "w21_manifest.json", "W21.header.json")
MANIFEST = "MANIFEST.sha256"
PLAN = "plan.json"


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
    """直下のファイル(W17 の jsonl と ``MANIFEST.sha256`` を除く)と ``acceptance/`` の下 → {相対パス: パス}。"""
    out: dict[str, Path] = {}
    for p in sorted(root.iterdir()):
        if p.is_file() and p.name != MANIFEST and not (p.suffix == ".jsonl" and p.name.startswith(SKIP_PREFIXES)):
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


def _w21(out: Path, data: str, extra: list[str]) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str((REPO / "src").resolve())
    cmd = [sys.executable, "-m", "shibuya.build.pop.w21_build", "--out", str(out), "--data", data, *extra]
    return subprocess.run(cmd, env=env, cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")


# ---------------------------------------------------------------------------------------------- stage
def cmd_stage(a: argparse.Namespace) -> int:
    base, out = Path(a.base), Path(a.out)
    if out.exists() and any(out.iterdir()) and not a.reuse:
        print(f"--out が空でない: {out}(作り直すなら消してから・続きなら --reuse)", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    if not a.reuse:
        src = {k: v for k, v in asset_files(base).items() if k not in W21_FILES}
        (out / "acceptance").mkdir(exist_ok=True)
        for rel, p in src.items():
            dst = out / rel
            shutil.copy2(p, dst)
            if sha256(dst) != sha256(p):
                raise RuntimeError(f"写しの sha256 が違う: {rel}")
        print(f"写した {len(src)} 本(sha256 一致)")
    extra = ["--world", str(base)] + (["--w21-anneal", a.anneal] if a.anneal else [])
    runs: list[dict[str, str]] = []
    dirs = [out] + [Path(a.scratch) / f"run{i + 1}" for i in range(1, int(a.runs))]
    codes = []
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        r = _w21(d, a.data, extra)
        codes.append(r.returncode)
        if r.returncode not in (0, 1):
            print(r.stdout[-3000:], r.stderr[-3000:], file=sys.stderr)
            return r.returncode
        runs.append({f: sha256(d / f) for f in W21_FILES})
        print(f"組み立て {len(runs)}: 終了コード {r.returncode}・{r.stdout.strip()[-140:]}")
    same = all(r == runs[0] for r in runs)
    files = asset_files(out)
    lines = [f"{sha256(p)}  {rel}" for rel, p in sorted(files.items())]
    (out / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    man = json.loads((out / "w21_manifest.json").read_text(encoding="utf-8"))
    doc = {"runs": int(a.runs), "exit_codes": codes, "w21_sha256_by_run": runs, "deterministic": same,
           "w21_build_hash": man["w21_build_hash"], "build_hash_of_stage": build_hash(out),
           "build_hash_of_base": build_hash(base), "files_in_stage": len(files),
           # 〔検収 L7〕ファイルそのもの(最後の改行を含むバイト列)の sha256
           "stage_manifest_sha256": sha256(out / MANIFEST)}
    print(json.dumps(doc, ensure_ascii=False))
    if a.record:
        Path(a.record).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0 if same else 3


# ---------------------------------------------------------------------------------------------- plan
def cmd_plan(a: argparse.Namespace) -> int:
    live, stage, steps = Path(a.live), Path(a.stage), Path(a.steps)
    fl, fs = asset_files(live), asset_files(stage)
    rows: list[dict[str, Any]] = []
    for rel in sorted(set(fl) | set(fs)):
        b, s = fl.get(rel), fs.get(rel)
        hb = sha256(b) if b else ""
        hs = sha256(s) if s else ""
        action = "kept_live_only" if s is None else ("added" if b is None else ("moved" if hb != hs else "same"))
        rows.append({"path": rel, "action": action, "sha256_before": hb, "sha256_after": hs,
                     "md5_before": md5(b) if b else "", "md5_after": md5(s) if s else "",
                     "bytes_before": b.stat().st_size if b else 0, "bytes_after": s.stat().st_size if s else 0})
    changed = [r for r in rows if r["action"] in ("added", "moved")]
    plan = {"schema": "pop41.activation/1", "build_hash_before": build_hash(live), "build_hash_after": build_hash(stage),
            "counts": {k: sum(1 for r in rows if r["action"] == k) for k in ("same", "moved", "added", "kept_live_only")},
            "rows": rows}
    if not a.dry_run:
        steps.mkdir(parents=True, exist_ok=True)
        lines = []
        for r in changed:
            dst = steps / r["path"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(fs[r["path"]], dst)
            if sha256(dst) != r["sha256_after"]:
                raise RuntimeError(f"steps の写しの sha256 が違う: {r['path']}")
            lines.append(f"{r['sha256_after']}  {r['path']}  {r['action']}")
        (steps / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        (steps / PLAN).write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    rec = {k: v for k, v in plan.items() if k != "rows"}
    rec["changed"] = changed
    if a.record:
        Path(a.record).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"同じ {plan['counts']['same']}・置き換え {plan['counts']['moved']}・追加 {plan['counts']['added']}"
          f"・本体の v2 だけ(触らない){plan['counts']['kept_live_only']}")
    print(f"build_hash {plan['build_hash_before'][:16]} → {plan['build_hash_after'][:16]}")
    for r in changed:
        print(f"  {r['action']:6s} {r['path']}  {r['sha256_before'][:16] or '-'} → {r['sha256_after'][:16]}")
    return 0


def _load_plan(steps: Path) -> dict[str, Any]:
    return json.loads((steps / PLAN).read_text(encoding="utf-8"))


def _check_side(live: Path, plan: dict[str, Any], want: str) -> list[str]:
    bad = []
    for r in plan["rows"]:
        if r["action"] not in ("added", "moved"):
            continue
        p = live / r["path"]
        exp = r["sha256_before"] if want == "before" else r["sha256_after"]
        got = sha256(p) if p.exists() else ""
        if got != exp:
            bad.append(r["path"])
    bh = build_hash(live)
    if bh != plan["build_hash_" + want]:
        bad.append(f"build_hash {bh[:16]} != {plan['build_hash_' + want][:16]}")
    return bad


def cmd_apply(a: argparse.Namespace) -> int:
    live, steps, backup = Path(a.live), Path(a.steps), Path(a.backup)
    plan = _load_plan(steps)
    changed = [r for r in plan["rows"] if r["action"] in ("added", "moved")]
    pre = _check_side(live, plan, "before")
    if pre:
        print("本体の v2 が plan の『前』と違う(止める):", *pre, sep="\n  ", file=sys.stderr)
        return 2
    for r in changed:
        if sha256(steps / r["path"]) != r["sha256_after"]:
            print(f"steps のファイルが plan と違う(止める): {r['path']}", file=sys.stderr)
            return 2
    if backup.exists() and any(backup.iterdir()):
        print(f"退避先が空でない(止める): {backup}", file=sys.stderr)
        return 2
    print(f"前提 OK: 置き換え {sum(r['action'] == 'moved' for r in changed)}・追加 "
          f"{sum(r['action'] == 'added' for r in changed)}・build_hash {plan['build_hash_before'][:16]} → "
          f"{plan['build_hash_after'][:16]}")
    for r in changed:
        print(f"  {'退避+写す' if r['action'] == 'moved' else '写す(新)':8s} {r['path']}")
    if a.dry_run:
        print("--dry-run: 何も書いていない")
        return 0
    backup.mkdir(parents=True, exist_ok=True)
    lines = []
    for r in changed:
        if r["action"] == "moved":
            (backup / r["path"]).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(live / r["path"], backup / r["path"])
            if sha256(backup / r["path"]) != r["sha256_before"]:
                raise RuntimeError(f"退避の sha256 が違う: {r['path']}")
            lines.append(f"{r['sha256_before']}  {r['path']}  moved")
        else:
            lines.append(f"{'-' * 64}  {r['path']}  added")
    (backup / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    shutil.copy2(steps / PLAN, backup / PLAN)
    for r in changed:
        shutil.copy2(steps / r["path"], live / r["path"])
    post = _check_side(live, plan, "after")
    if post:
        print("写した後の確かめで違う(revert で戻せる):", *post, sep="\n  ", file=sys.stderr)
        return 3
    print(f"写した。build_hash {build_hash(live)[:16]}(plan の後と同じ)")
    return 0


def cmd_revert(a: argparse.Namespace) -> int:
    live, backup = Path(a.live), Path(a.backup)
    plan = json.loads((backup / PLAN).read_text(encoding="utf-8"))
    for line in (backup / MANIFEST).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        _h, rel, action = line.split("  ")
        if action == "moved":
            if not a.dry_run:
                shutil.copy2(backup / rel, live / rel)
            print(f"  戻す {rel}")
        else:
            if not a.dry_run and (live / rel).exists():
                (live / rel).unlink()
            print(f"  消す {rel}(活性化で足したファイル)")
    if a.dry_run:
        print("--dry-run: 何も書いていない")
        return 0
    bad = _check_side(live, plan, "before")
    if bad:
        print("戻した後の確かめで違う:", *bad, sep="\n  ", file=sys.stderr)
        return 3
    print(f"戻した。build_hash {build_hash(live)[:16]}(plan の前と同じ)")
    return 0


def cmd_materialize(a: argparse.Namespace) -> int:
    """前の資産を ``--out`` に組み、plan の「前」と同じかを確かめる(本体の v2 と退避は読むだけ)。"""
    live, backup, out = Path(a.live), Path(a.backup), Path(a.out)
    if out.exists() and any(out.iterdir()):
        print(f"--out が空でない(止める): {out}", file=sys.stderr)
        return 2
    plan_p, man_p = backup / PLAN, backup / MANIFEST
    if not plan_p.exists() or not man_p.exists():
        print(f"退避に {PLAN} か {MANIFEST} が無い(止める): {backup}", file=sys.stderr)
        return 2
    plan = json.loads(plan_p.read_text(encoding="utf-8"))
    rows = {r["path"]: r for r in plan["rows"]}
    moved = sorted(r["path"] for r in plan["rows"] if r["action"] == "moved")
    backed = sorted(line.split("  ")[1] for line in man_p.read_text(encoding="utf-8").splitlines()
                    if line.strip() and line.split("  ")[2] == "moved")
    if backed != moved:
        print("退避の MANIFEST と plan の置き換えの一覧が違う(止める)", file=sys.stderr)
        return 2
    side = "after" if not _check_side(live, plan, "after") else ("before" if not _check_side(live, plan, "before") else "")
    if not side:
        print("本体の v2 が plan の前とも後とも違う(止める)", file=sys.stderr)
        return 2
    n = {"from_backup": 0, "from_live": 0, "skipped_added": 0}
    out.mkdir(parents=True, exist_ok=True)
    (out / "acceptance").mkdir(exist_ok=True)
    for rel, p in asset_files(live).items():
        r = rows.get(rel)
        action = r["action"] if r else "kept_live_only"
        if action == "added" and side == "after":
            n["skipped_added"] += 1
            continue
        dst = out / rel
        if action == "moved" and side == "after":
            shutil.copy2(backup / rel, dst)
            n["from_backup"] += 1
            continue
        shutil.copy2(p, dst)
        n["from_live"] += 1
    bad = _check_side(out, plan, "before")
    print(f"組んだ: 退避から {n['from_backup']}・本体の v2 から {n['from_live']}・足したファイルを除いた {n['skipped_added']}")
    print("plan の前と: " + ("同じ" if not bad else "違う: " + ", ".join(bad)))
    return 0 if not bad else 1


def cmd_verify(a: argparse.Namespace) -> int:
    plan = _load_plan(Path(a.steps))
    bad = _check_side(Path(a.live), plan, a.want)
    print("同じ" if not bad else "違う: " + ", ".join(bad))
    return 0 if not bad else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("stage")
    sp.add_argument("--base", default="data/world/v2")
    sp.add_argument("--out", default="data/world/v2_stage_4-1")
    sp.add_argument("--data", default="data")
    sp.add_argument("--runs", type=int, default=2)
    sp.add_argument("--scratch", default="_bc/w21_stage_runs")
    sp.add_argument("--anneal", choices=("on", "off"), default="")
    sp.add_argument("--reuse", action="store_true")
    sp.add_argument("--record", default="")
    sp = sub.add_parser("plan")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--stage", default="data/world/v2_stage_4-1")
    sp.add_argument("--steps", default="data/world/v2_steps_4-1")
    sp.add_argument("--record", default="")
    sp.add_argument("--dry-run", action="store_true")
    for name in ("apply", "revert"):
        sp = sub.add_parser(name)
        sp.add_argument("--live", default="data/world/v2")
        sp.add_argument("--backup", default="data/world/v2_pre_4-1")
        sp.add_argument("--dry-run", action="store_true")
        if name == "apply":
            sp.add_argument("--steps", default="data/world/v2_steps_4-1")
    sp = sub.add_parser("materialize")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--backup", default="data/world/v2_pre_4-1")
    sp.add_argument("--out", required=True)
    sp = sub.add_parser("verify")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--steps", default="data/world/v2_steps_4-1")
    sp.add_argument("--want", choices=("before", "after"), default="after")
    a = ap.parse_args(argv)
    return {"stage": cmd_stage, "plan": cmd_plan, "apply": cmd_apply, "revert": cmd_revert,
            "verify": cmd_verify, "materialize": cmd_materialize}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
