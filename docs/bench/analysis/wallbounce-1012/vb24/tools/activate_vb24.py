"""第 2 期 2-4(版上げ 2 回目)V1: 世界資産の活性化の道具(組み立て・差の表・写し・戻し・確かめ)。

10e の ACT と同じ形(``data/world/v2_10e_steps/ACT/MANIFEST.sha256``・``data/world/v2_pre_10e_2026-10-12/``)。
2-3b(W12 の実ダイヤ・``data/world/v2_stage_2-3b``)と 2-3(W9 の影 7 日の窓・``data/world/v2_stage_2-3``)は、どちらも
本体の ``data/world/v2`` の写しから別々に組んだので、W18〜W20 の見出しと ``build_manifest.json`` が互いに食い違う。
本道具はそれを 1 つに組み直す: 本体の v2 の写しに、今のコード(W9 の 7 日の窓+W12 1.2.0 の実ダイヤ+W9 のゲートの
宣言の直し)で W9・W12・W18・W19・W20 を組み、ほかの 16 段は ``--keep-stage``。

部分コマンド(リポの根で・作業木の ``src`` を ``PYTHONPATH`` に):

- ``stage``  : 本体の v2 の直下のファイル(W17 のプロンプトと応答の jsonl を除く)と ``acceptance/`` を ``--out`` へ本物の
  コピーで写し(sha256 を照らす)、W9・W12・W18・W19・W20 を組む。``--runs 2`` で 2 回組み、build_hash が一致する
  ことを確かめる(決定的)。終了コードは構築の終了コード(落ちたゲートがあれば 1)。
- ``plan``   : 本体の v2(``--live``)と組んだ資産(``--stage``)の直下のファイル+``acceptance/`` を sha256 で比べ、
  動いたファイル(added/moved)だけを ``--steps`` に写して ``MANIFEST.sha256``(sha256・パス・added/moved)と
  ``plan.json``(前後の sha256・md5・バイト数・build_hash の前後)を書く。``--record`` に同じ表(絶対パスなし)。
  本体の v2 は読むだけ。
- ``apply``  : **親が実行する**。``--dry-run`` は前提の確かめと写す一覧の表示だけ(何も書かない)。本番は
  (1) 本体の v2 の今の sha256 が plan の「前」と同じか確かめる(違えば止める)(2) 置き換えるファイルを ``--backup``
  (既定 ``data/world/v2_pre_2-4``)へ写して ``MANIFEST.sha256``(sha256・パス・moved/added)を書く(足すファイルは
  名前だけ記録=戻すときに消す)(3) ``--steps`` のファイルを本体の v2 へ写す(4) 写した全部の sha256 と
  ``build_manifest.json`` の build_hash が plan の「後」と同じか確かめる。
- ``revert`` : ``--backup`` から戻す(moved は写し戻し・added は消す)。戻した後の sha256 と build_hash が plan の「前」と
  同じか確かめる。
- ``verify`` : 本体の v2 が plan の「後」(``--want after``)か「前」(``--want before``)と同じかを確かめるだけ。

ファイルの中身は読まない(sha256・md5・バイト数だけ)。build_hash は ``build_manifest.json`` の 1 欄だけを読む。
封印の層には触れない(W19 は既存の規則どおり封印の層の sha256 を取る=方式 S・中身は解かない)。
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

#: 組み直す段(2-3b の W12・2-3 の W9 と、それを写す W18〜W20)。
REBUILD_STAGES: tuple[str, ...] = ("W9", "W12", "W18", "W19", "W20")
#: 写さないファイル(W17 の構築の途中の入出力=エンジンも W9・W12 も読まない・計約 3 GB)。
SKIP_PREFIXES: tuple[str, ...] = ("w17_prompts", "w17_responses", "w17_pilot_prompts", "w17_pilot_responses")
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


# ---------------------------------------------------------------------------------------------- stage
def cmd_stage(a: argparse.Namespace) -> int:
    base, out = Path(a.base), Path(a.out)
    if out.exists() and any(out.iterdir()) and not a.reuse:
        print(f"--out が空でない: {out}(作り直すなら消してから・続きなら --reuse)", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    if not a.reuse:
        src = asset_files(base)
        (out / "acceptance").mkdir(exist_ok=True)
        for rel, p in src.items():
            dst = out / rel
            shutil.copy2(p, dst)
            if sha256(dst) != sha256(p):
                raise RuntimeError(f"写しの sha256 が違う: {rel}")
        print(f"写した {len(src)} 本(sha256 一致)")
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str((REPO / "src").resolve())
    from shibuya.build.run import ALL_STAGES  # noqa: PLC0415 (作業木の src)

    keep = [s for s in ALL_STAGES if s not in REBUILD_STAGES]
    cmd = [sys.executable, "-m", "shibuya.build.run", "--out", str(out), "--data", a.data, "--quiet"]
    for s in REBUILD_STAGES:
        cmd += ["--stage", s]
    for s in keep:
        cmd += ["--keep-stage", s]
    hashes: list[str] = []
    codes: list[int] = []
    for i in range(int(a.runs)):
        r = subprocess.run(cmd, env=env, cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")
        codes.append(r.returncode)
        hashes.append(build_hash(out))
        print(f"組み立て {i + 1}: 終了コード {r.returncode}・build_hash {hashes[-1][:16]}")
        if r.returncode not in (0, 1):
            print(r.stdout[-3000:], r.stderr[-3000:], file=sys.stderr)
            return r.returncode
    gates_failed = []
    summ = out / "acceptance" / "summary.json"
    if summ.exists():
        gates_failed = [(g["stage"], g["gate"]) for g in json.loads(summ.read_text(encoding="utf-8"))["gates_failed"]]
    doc = {"rebuild_stages": list(REBUILD_STAGES), "keep_stages": keep, "runs": int(a.runs),
           "exit_codes": codes, "build_hashes": hashes, "deterministic": len(set(hashes)) == 1,
           "gates_failed": gates_failed}
    print(json.dumps(doc, ensure_ascii=False))
    if a.record:
        Path(a.record).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0 if len(set(hashes)) == 1 else 3


# ---------------------------------------------------------------------------------------------- plan
def cmd_plan(a: argparse.Namespace) -> int:
    live, stage, steps = Path(a.live), Path(a.stage), Path(a.steps)
    fl, fs = asset_files(live), asset_files(stage)
    rows: list[dict[str, Any]] = []
    for rel in sorted(set(fl) | set(fs)):
        b = fl.get(rel)
        s = fs.get(rel)
        hb = sha256(b) if b else ""
        hs = sha256(s) if s else ""
        if s is None:
            action = "kept_live_only"  # 組んだ資産に無い(本体の v2 だけ)=触らない
        elif b is None:
            action = "added"
        elif hb != hs:
            action = "moved"
        else:
            action = "same"
        rows.append({"path": rel, "action": action, "sha256_before": hb, "sha256_after": hs,
                     "md5_before": md5(b) if b else "", "md5_after": md5(s) if s else "",
                     "bytes_before": b.stat().st_size if b else 0, "bytes_after": s.stat().st_size if s else 0})
    changed = [r for r in rows if r["action"] in ("added", "moved")]
    bad = [r["path"] for r in rows if r["action"] == "kept_live_only" and r["path"] == "build_manifest.json"]
    if bad:
        raise RuntimeError("組んだ資産に build_manifest.json が無い")
    plan = {
        "schema": "vb24.activation/1",
        "build_hash_before": build_hash(live),
        "build_hash_after": build_hash(stage),
        "counts": {k: sum(1 for r in rows if r["action"] == k) for k in ("same", "moved", "added", "kept_live_only")},
        "rows": rows,
    }
    if not a.dry_run:
        steps.mkdir(parents=True, exist_ok=True)
        (steps / "acceptance").mkdir(exist_ok=True)
        lines = []
        for r in changed:
            dst = steps / r["path"]
            shutil.copy2(fs[r["path"]], dst)
            if sha256(dst) != r["sha256_after"]:
                raise RuntimeError(f"steps の写しの sha256 が違う: {r['path']}")
            lines.append(f"{r['sha256_after']}  {r['path']}  {r['action']}")
        (steps / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
        (steps / PLAN).write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                  newline="\n")
    rec = {k: v for k, v in plan.items() if k != "rows"}
    rec["changed"] = changed
    if a.record:
        Path(a.record).write_text(json.dumps(rec, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                  newline="\n")
    print(f"同じ {plan['counts']['same']}・置き換え {plan['counts']['moved']}・追加 {plan['counts']['added']}"
          f"・本体の v2 だけ(触らない){plan['counts']['kept_live_only']}")
    print(f"build_hash {plan['build_hash_before'][:16]} → {plan['build_hash_after'][:16]}")
    for r in changed:
        print(f"  {r['action']:6s} {r['path']}  {r['sha256_before'][:16] or '-'} → {r['sha256_after'][:16]}")
    return 0


def _load_plan(steps: Path) -> dict[str, Any]:
    return json.loads((steps / PLAN).read_text(encoding="utf-8"))


def _check_side(live: Path, plan: dict[str, Any], want: str) -> list[str]:
    """本体の v2 が plan の前(before)か後(after)と同じか。違うパスの一覧。"""
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


# ---------------------------------------------------------------------------------------------- apply
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
    (backup / "acceptance").mkdir(exist_ok=True)
    lines = []
    for r in changed:
        if r["action"] == "moved":
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
    sp.add_argument("--out", default="data/world/v2_stage_2-4")
    sp.add_argument("--data", default="data")
    sp.add_argument("--runs", type=int, default=2)
    sp.add_argument("--reuse", action="store_true")
    sp.add_argument("--record", default="")
    sp = sub.add_parser("plan")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--stage", default="data/world/v2_stage_2-4")
    sp.add_argument("--steps", default="data/world/v2_steps_2-4")
    sp.add_argument("--record", default="")
    sp.add_argument("--dry-run", action="store_true")
    for name in ("apply", "revert"):
        sp = sub.add_parser(name)
        sp.add_argument("--live", default="data/world/v2")
        sp.add_argument("--backup", default="data/world/v2_pre_2-4")
        sp.add_argument("--dry-run", action="store_true")
        if name == "apply":
            sp.add_argument("--steps", default="data/world/v2_steps_2-4")
    sp = sub.add_parser("verify")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--steps", default="data/world/v2_steps_2-4")
    sp.add_argument("--want", choices=("before", "after"), default="after")
    a = ap.parse_args(argv)
    return {"stage": cmd_stage, "plan": cmd_plan, "apply": cmd_apply, "revert": cmd_revert,
            "verify": cmd_verify}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
