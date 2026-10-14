"""第 2 期 2-3c: 世界資産の組み立て・差の表・活性化の道具(``vb24/tools/activate_vb24.py`` と同じ形・**本段では apply しない**)。

2-3c は W12 を 1.3.0 にした(渋谷の発着の表 ``w12_rail_events.parquet`` を足す・発車の表 ``w12_timetables.parquet`` は
1.2.0 とバイト一致)。資産は本体の ``data/world/v2``(2-4 で活性化した版=build_hash ``6a7d34e8…``)の写しに、今のコードで
W12・W18・W19・W20 を組み、ほかの段は ``--keep-stage``。活性化(本体の v2 への写し)は版上げ 3 回目(計画 4-3)で親が行う。

vb24 の道具との違い: 差し替えのファイルを別の置き場(steps)に写さない。``plan`` は差の表を記録の JSON
(``--plan``=既定 ``tt23c/activation_plan.json``・sha256・md5・バイト数・build_hash の前後=時刻は無い)にだけ書き、
``apply`` は組んだ資産(``--stage``)から直に写す(写す前に sha256 を plan と照らす)。``data/world`` の下に新しく書くのは
組んだ資産(``stage``)と、親が ``apply`` を回したときの退避(``--backup``)だけ。

部分コマンド(リポの根で・作業木の ``src`` を ``PYTHONPATH`` に):

- ``stage``  : 本体の v2 の直下のファイル(W17 のプロンプトと応答の jsonl を除く)と ``acceptance/`` を ``--out`` へ本物の
  コピーで写し(sha256 を照らす)、W12・W18・W19・W20 を組む。``--runs 2`` で 2 回組み、build_hash が一致することを
  確かめる。``--record`` に組み立ての要約。
- ``plan``   : 本体の v2(``--live``)と組んだ資産(``--stage``)の直下+``acceptance/`` を sha256 で比べ、差の表を ``--plan``
  に書く(本体の v2 も組んだ資産も読むだけ)。
- ``apply``  : **親が実行する(版上げ 3 回目)**。``--dry-run`` は前提の確かめと写す一覧の表示だけ(何も書かない)。本番は
  (1) 本体の v2 の今の sha256 が plan の「前」と同じか (2) 組んだ資産のファイルが plan の「後」と同じか (3) 退避先
  ``--backup``(既定 ``data/world/v2_pre_2-3c``)が空か を確かめ、置き換えるファイルを退避して ``MANIFEST.sha256`` と
  plan の写しを書き、組んだ資産から写し、写した全部と build_hash を plan の「後」と照らす(違えば終了コード 3=revert)。
- ``revert`` : 退避から戻す(moved は写し戻し・added は消す)。戻した後に plan の「前」と照らす。
- ``verify`` : 本体の v2 が plan の「後」(``--want after``)か「前」(``--want before``)と同じか。
- ``materialize``: 退避(置き換えた分だけ)と本体の v2 から「前」の資産を ``--out`` に組み、plan の「前」と照らす。

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
RECORD_DIR = HERE.parent

#: 組み直す段(W12 と、W12 の出力を写す W18〜W20)。
REBUILD_STAGES: tuple[str, ...] = ("W12", "W18", "W19", "W20")
#: 写さないファイル(W17 の構築の途中の入出力=エンジンも W12 も読まない・計約 3 GB)。
SKIP_PREFIXES: tuple[str, ...] = ("w17_prompts", "w17_responses", "w17_pilot_prompts", "w17_pilot_responses")
MANIFEST = "MANIFEST.sha256"
PLAN = "plan.json"
SCHEMA = "tt23c.activation/1"


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
    from shibuya.build.run import ALL_STAGES  # noqa: PLC0415(作業木の src)

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
def make_plan(live: Path, stage: Path) -> dict[str, Any]:
    fl, fs = asset_files(live), asset_files(stage)
    rows: list[dict[str, Any]] = []
    for rel in sorted(set(fl) | set(fs)):
        b, s = fl.get(rel), fs.get(rel)
        hb = sha256(b) if b else ""
        hs = sha256(s) if s else ""
        if s is None:
            action = "kept_live_only"
        elif b is None:
            action = "added"
        elif hb != hs:
            action = "moved"
        else:
            action = "same"
        rows.append({"path": rel, "action": action, "sha256_before": hb, "sha256_after": hs,
                     "md5_before": md5(b) if b else "", "md5_after": md5(s) if s else "",
                     "bytes_before": b.stat().st_size if b else 0, "bytes_after": s.stat().st_size if s else 0})
    if "build_manifest.json" not in fs:
        raise RuntimeError("組んだ資産に build_manifest.json が無い")
    return {"schema": SCHEMA, "build_hash_before": build_hash(live), "build_hash_after": build_hash(stage),
            "counts": {k: sum(1 for r in rows if r["action"] == k) for k in ("same", "moved", "added", "kept_live_only")},
            "rows": rows}


def cmd_plan(a: argparse.Namespace) -> int:
    plan = make_plan(Path(a.live), Path(a.stage))
    Path(a.plan).write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    c = plan["counts"]
    print(f"同じ {c['same']}・置き換え {c['moved']}・追加 {c['added']}・本体の v2 だけ(触らない){c['kept_live_only']}")
    print(f"build_hash {plan['build_hash_before'][:16]} → {plan['build_hash_after'][:16]}")
    for r in plan["rows"]:
        if r["action"] in ("added", "moved"):
            print(f"  {r['action']:6s} {r['path']}  {r['sha256_before'][:16] or '-'} → {r['sha256_after'][:16]}")
    return 0


def _load_plan(path: str | Path) -> dict[str, Any]:
    plan = json.loads(Path(path).read_text(encoding="utf-8"))
    if plan.get("schema") != SCHEMA:
        raise ValueError(f"plan の形式が違う: {plan.get('schema')!r}")
    return plan


def _changed(plan: dict[str, Any]) -> list[dict[str, Any]]:
    return [r for r in plan["rows"] if r["action"] in ("added", "moved")]


def _check_side(root: Path, plan: dict[str, Any], want: str) -> list[str]:
    """``root`` が plan の前(before)か後(after)と同じか。違うパスの一覧。"""
    bad = []
    for r in _changed(plan):
        p = root / r["path"]
        exp = r["sha256_before"] if want == "before" else r["sha256_after"]
        got = sha256(p) if p.exists() else ""
        if got != exp:
            bad.append(r["path"])
    bh = build_hash(root)
    if bh != plan["build_hash_" + want]:
        bad.append(f"build_hash {bh[:16]} != {plan['build_hash_' + want][:16]}")
    return bad


# ---------------------------------------------------------------------------------------------- apply
def cmd_apply(a: argparse.Namespace) -> int:
    live, stage, backup = Path(a.live), Path(a.stage), Path(a.backup)
    plan = _load_plan(a.plan)
    changed = _changed(plan)
    pre = _check_side(live, plan, "before")
    if pre:
        print("本体の v2 が plan の『前』と違う(止める):", *pre, sep="\n  ", file=sys.stderr)
        return 2
    post_src = _check_side(stage, plan, "after")
    if post_src:
        print("組んだ資産が plan の『後』と違う(止める):", *post_src, sep="\n  ", file=sys.stderr)
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
    (backup / PLAN).write_text(json.dumps(plan, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in changed:
        shutil.copy2(stage / r["path"], live / r["path"])
    post = _check_side(live, plan, "after")
    if post:
        print("写した後の確かめで違う(revert で戻せる):", *post, sep="\n  ", file=sys.stderr)
        return 3
    print(f"写した。build_hash {build_hash(live)[:16]}(plan の後と同じ)")
    return 0


def cmd_revert(a: argparse.Namespace) -> int:
    live, backup = Path(a.live), Path(a.backup)
    plan = _load_plan(backup / PLAN)
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
    """退避と本体の v2 から「前」の資産を ``--out`` に組み、plan の「前」と同じかを確かめる(本体の v2 と退避は読むだけ)。"""
    live, backup, out = Path(a.live), Path(a.backup), Path(a.out)
    if out.exists() and any(out.iterdir()):
        print(f"--out が空でない(止める): {out}", file=sys.stderr)
        return 2
    plan_p, man_p = backup / PLAN, backup / MANIFEST
    if not plan_p.exists() or not man_p.exists():
        print(f"退避に {PLAN} か {MANIFEST} が無い(止める): {backup}", file=sys.stderr)
        return 2
    plan = _load_plan(plan_p)
    rows = {r["path"]: r for r in plan["rows"]}
    backed = {}
    for line in man_p.read_text(encoding="utf-8").splitlines():
        if line.strip():
            h, rel, action = line.split("  ")
            if action == "moved":
                backed[rel] = h
    moved = sorted(r["path"] for r in plan["rows"] if r["action"] == "moved")
    if sorted(backed) != moved or any(not (backup / rel).is_file() for rel in moved):
        print("退避の MANIFEST・ファイルと plan の置き換えの一覧が違う(止める)", file=sys.stderr)
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
            if sha256(dst) != r["sha256_before"]:
                raise RuntimeError(f"退避の sha256 が plan の前と違う: {rel}")
            n["from_backup"] += 1
            continue
        if a.hardlink:
            os.link(p, dst)
        else:
            shutil.copy2(p, dst)
        if action == "same" and sha256(dst) != r["sha256_before"]:
            raise RuntimeError(f"変わっていないはずのファイルの sha256 が plan と違う: {rel}")
        n["from_live"] += 1
    bad = _check_side(out, plan, "before")
    print(f"組んだ: 退避から {n['from_backup']}・本体の v2 から {n['from_live']}・活性化で足したファイルを除いた "
          f"{n['skipped_added']}(本体の v2 は plan の{'後' if side == 'after' else '前'})")
    print("plan の前と: " + ("同じ" if not bad else "違う: " + ", ".join(bad)))
    return 0 if not bad else 1


def cmd_verify(a: argparse.Namespace) -> int:
    bad = _check_side(Path(a.live), _load_plan(a.plan), a.want)
    print("同じ" if not bad else "違う: " + ", ".join(bad))
    return 0 if not bad else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    default_plan = str(RECORD_DIR / "activation_plan.json")
    sp = sub.add_parser("stage")
    sp.add_argument("--base", default="data/world/v2")
    sp.add_argument("--out", default="data/world/v2_stage_2-3c")
    sp.add_argument("--data", default="data")
    sp.add_argument("--runs", type=int, default=2)
    sp.add_argument("--reuse", action="store_true")
    sp.add_argument("--record", default="")
    sp = sub.add_parser("plan")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--stage", default="data/world/v2_stage_2-3c")
    sp.add_argument("--plan", default=default_plan)
    sp = sub.add_parser("apply")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--stage", default="data/world/v2_stage_2-3c")
    sp.add_argument("--plan", default=default_plan)
    sp.add_argument("--backup", default="data/world/v2_pre_2-3c")
    sp.add_argument("--dry-run", action="store_true")
    sp = sub.add_parser("revert")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--backup", default="data/world/v2_pre_2-3c")
    sp.add_argument("--dry-run", action="store_true")
    sp = sub.add_parser("materialize")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--backup", default="data/world/v2_pre_2-3c")
    sp.add_argument("--out", required=True)
    sp.add_argument("--hardlink", action="store_true")
    sp = sub.add_parser("verify")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--plan", default=default_plan)
    sp.add_argument("--want", choices=("before", "after"), default="after")
    a = ap.parse_args(argv)
    return {"stage": cmd_stage, "plan": cmd_plan, "apply": cmd_apply, "revert": cmd_revert,
            "verify": cmd_verify, "materialize": cmd_materialize}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
