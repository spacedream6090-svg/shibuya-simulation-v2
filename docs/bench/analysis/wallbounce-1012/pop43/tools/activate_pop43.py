"""第 4 期 4-3(版上げ 3 回目)段 10 差し替え: 世界資産の組み立て・差の表・活性化・戻し・確かめの道具。

vb24 の ``activate_vb24.py`` と同じ形(plan / apply / verify)。差し替えの資産 ``data/world/v2_stage_4-3/`` を組み、本体の
``data/world/v2`` との差の表を作り、親が取り込みのときに本体の v2 へ写す。

部分コマンド(リポの根で・作業木の ``src`` を ``PYTHONPATH`` に):

- ``stage``  : 本体の v2(``--base``)の直下のファイル(W17 のプロンプトと応答の jsonl を除く)と ``acceptance/`` を ``--out`` へ
  本物のコピーで写し(sha256 を照らす)、W21 の段 1〜3 の資産(``--w21``=``v2_stage_4-1``・manifest の sha256 を照らす)を写し、
  W21b(段 4〜7・1.2.0=地位の分け)・W21c(段 8〜10・1.3.0)・W21apply(段 10 の差し替え)を組み、W18・W19・W20 を組む(ほかの
  段は ``--keep-stage``)。最後に ``MANIFEST.sha256``(全ファイル)と ``stage_build.json`` を書く。``--out2`` を渡すと同じ手順で
  2 回目を組み、全ファイルの sha256 が一致するかを確かめる(2 回目の置き場は確かめの後に消す=``--keep-out2`` で残す)。
- ``plan``   : 本体の v2(``--live``)と組んだ資産(``--stage``)の直下のファイル+``acceptance/`` を sha256 で比べた表
  (same/moved/added/kept_live_only・前後の sha256・md5・バイト数・build_hash の前後)を ``--record`` に書く。**表だけ**
  (何も写さない)。本体の v2 は読むだけ。
- ``apply``  : **親が実行する**(``--dry-run`` は前提の確かめと写す一覧の表示だけ=何も書かない)。本番は (1) 本体の v2 の今の
  sha256 が plan の「前」と同じか確かめる (2) 退避 ``--backup``(既定 ``data/world/v2_pre_4-3``)に**本体の v2 の資産の全部**
  (直下のファイル=W17 の jsonl を除く+``acceptance/``)を写す=``--world data/world/v2_pre_4-3`` でエンジンが旧値(W16)を
  再現できる置き場(``MANIFEST.sha256``・``plan.json``)(3) 動いたファイル(moved/added)を組んだ資産から本体の v2 へ写す
  (4) 写した全部の sha256 と build_hash が plan の「後」と同じか確かめる(違えば終了コード 3=``revert`` で戻せる)。
- ``revert`` : 退避から戻す(moved は写し戻し・added は消す)。戻した後の sha256 と build_hash が plan の「前」と同じか確かめる。
- ``verify`` : 本体の v2 が plan の「後」(``--want after``)か「前」(``--want before``)と同じかを確かめるだけ(sha256 の表)。

〔検収 M4〕plan の記録は**全部の行**(same・moved・added・本体だけ)の前後の sha256 を持ち、apply の前後・revert の後・verify は
全部の行を確かめる(same の 1 本を壊しても見つける=試験の負の対照)。

ファイルの中身は読まない(sha256・md5・バイト数だけ)。build_hash は ``build_manifest.json`` の 1 欄だけを読む。封印の層には
触れない(W19 は既存の規則どおり封印の層の sha256 を取る=方式 S・中身は解かない)。
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

#: W21 の段 1〜3 の資産のうち写すもの(``w21_manifest.json`` の sha256 と照らす=manifest と見出しはそのまま写す)。
W21_STAGE13_FILES: tuple[str, ...] = ("w21_frame.json", "w21_households.parquet", "w21_persons.parquet",
                                      "w21_checks.json")
W21_STAGE13_META: tuple[str, ...] = ("w21_manifest.json", "W21.header.json")
#: 組み直す段(W18 は全段階の見出しを・W19/W20 は W18 の出力を読む)。
AUDIT_STAGES: tuple[str, ...] = ("W18", "W19", "W20")
#: 写さないファイル(W17 の構築の途中の入出力=エンジンは読まない・計約 3 GB)。
SKIP_PREFIXES: tuple[str, ...] = ("w17_prompts", "w17_responses", "w17_pilot_prompts", "w17_pilot_responses")
MANIFEST = "MANIFEST.sha256"
PLAN = "plan.json"
STAGE_RECORD = "stage_build.json"
#: 組んだ資産だけにある記録(本体の v2 に写さない)。
STAGE_ONLY: tuple[str, ...] = (MANIFEST, STAGE_RECORD)
#: 置き場の名が中に入るファイル(W21c の manifest と見出しの「読んだファイル」の欄=data 根からの相対か名だけ)。2 回目を
#: 別の置き場に組むとこの 2 本だけが違う(出力の sha256・build_hash・w21_apply_build_hash は同じ)=確かめの外。
LOCATION_DEPENDENT: tuple[str, ...] = ("W21c.header.json", "w21c_manifest.json")


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
    """記録に書く道筋(リポの根からの相対・外ならファイル名だけ=絶対パスを書かない)。"""
    try:
        return Path(p).resolve().relative_to(REPO.resolve()).as_posix()
    except ValueError:
        return Path(p).name


# ---------------------------------------------------------------------------------------------- stage
def _env() -> dict[str, str]:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str((REPO / "src").resolve())
    return env


def _run(cmd: list[str]) -> tuple[int, float, str]:
    t0 = time.perf_counter()
    r = subprocess.run(cmd, env=_env(), cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")
    dt = time.perf_counter() - t0
    if r.returncode not in (0, 1) or "Traceback (most recent call last)" in r.stderr:  # 例外の終了コード 1 も止める
        print(r.stdout[-3000:], r.stderr[-5000:], file=sys.stderr)
        raise RuntimeError(f"止まった(終了コード {r.returncode}): {' '.join(cmd[2:4])}")
    return r.returncode, dt, r.stdout


def stage_one(base: Path, w21: Path, out: Path, data: str) -> dict[str, Any]:
    """1 回の組み立て(``out`` は空か無い置き場)。"""
    if out.exists() and any(out.iterdir()):
        raise RuntimeError(f"--out が空でない: {out.name}(作り直すなら消してから)")
    out.mkdir(parents=True, exist_ok=True)
    (out / "acceptance").mkdir(exist_ok=True)
    t0 = time.perf_counter()
    src = asset_files(base)
    for rel, p in src.items():
        dst = out / rel
        shutil.copy2(p, dst)
        if sha256(dst) != sha256(p):
            raise RuntimeError(f"写しの sha256 が違う: {rel}")
    man13 = _json(w21 / "w21_manifest.json")
    want = {o["path"]: o["sha256"] for o in man13["outputs"]}
    for f in (*W21_STAGE13_FILES, *W21_STAGE13_META):
        shutil.copy2(w21 / f, out / f)
        if f in want and sha256(out / f) != want[f]:
            raise RuntimeError(f"段 1〜3 の資産の sha256 が manifest と違う: {f}")
    times = {"copy_s": round(time.perf_counter() - t0, 1)}
    py = sys.executable
    codes = {}
    for name, cmd in (
        ("W21b", [py, "-m", "shibuya.build.pop.w21_build_b", "--out", str(out), "--data", data, "--base", str(w21),
                  "--world", str(base)]),
        ("W21c", [py, "-m", "shibuya.build.pop.w21_build_c", "--out", str(out), "--data", data, "--base", str(out),
                  "--world", str(base), "--in-place"]),
        ("W21apply", [py, "-m", "shibuya.build.pop.w21_apply", "--out", str(out), "--data", data, "--world",
                      str(base)]),
    ):
        code, dt, _so = _run(cmd)
        codes[name] = code
        times[name + "_s"] = round(dt, 1)
    from shibuya.build.run import ALL_STAGES  # noqa: PLC0415 (作業木の src)

    keep = [s for s in ALL_STAGES if s not in AUDIT_STAGES]
    cmd = [py, "-m", "shibuya.build.run", "--out", str(out), "--data", data, "--quiet"]
    for s in AUDIT_STAGES:
        cmd += ["--stage", s]
    for s in keep:
        cmd += ["--keep-stage", s]
    code, dt, _so = _run(cmd)
    codes["audit"] = code
    times["audit_s"] = round(dt, 1)
    files = asset_files(out)
    lines = [f"{sha256(p)}  {rel}" for rel, p in files.items() if rel not in STAGE_ONLY]
    (out / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    summ = out / "acceptance" / "summary.json"
    failed = ([(g["stage"], g["gate"]) for g in _json(summ)["gates_failed"]] if summ.exists() else [])
    rec = {
        "exit_codes": codes, "seconds": times, "build_hash": build_hash(out),
        "w21b_build_hash": _json(out / "w21b_manifest.json")["w21b_build_hash"],
        "w21c_build_hash": _json(out / "w21c_manifest.json")["w21c_build_hash"],
        "w21_apply_build_hash": _json(out / "w21_apply_manifest.json")["w21_apply_build_hash"],
        "w21_build_hash": man13["w21_build_hash"], "files": len(lines),
        "manifest_sha256": sha256(out / MANIFEST), "gates_failed": failed,
        "bytes": int(sum(p.stat().st_size for p in files.values())),
    }
    _write_json(out / STAGE_RECORD, rec)
    return rec


def cmd_stage(a: argparse.Namespace) -> int:
    base, w21, out = Path(a.base), Path(a.w21), Path(a.out)
    runs = [stage_one(base, w21, out, a.data)]
    print(f"組み立て 1: build_hash {runs[0]['build_hash'][:16]}・w21_apply_build_hash "
          f"{runs[0]['w21_apply_build_hash'][:16]}・{runs[0]['files']} 本")
    same = None
    diff: list[str] = []
    if a.out2:
        out2 = Path(a.out2)
        runs.append(stage_one(base, w21, out2, a.data))
        print(f"組み立て 2: build_hash {runs[1]['build_hash'][:16]}・w21_apply_build_hash "
              f"{runs[1]['w21_apply_build_hash'][:16]}")
        m1 = (out / MANIFEST).read_text(encoding="utf-8").splitlines()
        m2 = (out2 / MANIFEST).read_text(encoding="utf-8").splitlines()
        diff = sorted(set(m1) ^ set(m2))
        same = all(line.split("  ", 1)[1] in LOCATION_DEPENDENT for line in diff)
        if not a.keep_out2:
            shutil.rmtree(out2)
    doc = {"schema": "pop43.stage/1", "base": _rel(base), "w21": _rel(w21), "out": _rel(out),
           "runs": [{k: v for k, v in r.items()} for r in runs], "deterministic": same,
           "manifest_lines_differ": diff[:20], "location_dependent": list(LOCATION_DEPENDENT),
           "keys_equal": (len({(r["build_hash"], r["w21_apply_build_hash"]) for r in runs}) == 1) if len(runs) > 1 else None}
    print(json.dumps({k: doc[k] for k in ("deterministic", "keys_equal")}, ensure_ascii=False))
    if a.record:
        _write_json(Path(a.record), doc)
    return 0 if same in (None, True) else 3


# ---------------------------------------------------------------------------------------------- plan
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
    return {"schema": "pop43.activation/1", "build_hash_before": build_hash(live), "build_hash_after": build_hash(stage),
            "counts": {k: sum(1 for r in rows if r["action"] == k) for k in ("same", "moved", "added",
                                                                            "kept_live_only")},
            "rows": rows}


def cmd_plan(a: argparse.Namespace) -> int:
    plan = plan_rows(Path(a.live), Path(a.stage))
    rec = {k: v for k, v in plan.items() if k != "rows"}
    rec["changed"] = [r for r in plan["rows"] if r["action"] in ("added", "moved")]
    rec["kept_live_only"] = [r["path"] for r in plan["rows"] if r["action"] == "kept_live_only"]
    rec["same"] = [r["path"] for r in plan["rows"] if r["action"] == "same"]
    rec["rows"] = plan["rows"]  # 〔検収 M4〕全部の行の前後の sha256(確かめは全部に当てる)
    if a.record:
        _write_json(Path(a.record), rec)
    c = plan["counts"]
    print(f"同じ {c['same']}・置き換え {c['moved']}・追加 {c['added']}・本体の v2 だけ(触らない){c['kept_live_only']}")
    print(f"build_hash {plan['build_hash_before'][:16]} → {plan['build_hash_after'][:16]}")
    return 0


# ---------------------------------------------------------------------------------------------- apply / revert / verify
def _all_rows(plan: dict[str, Any]) -> list[dict[str, Any]]:
    """確かめに当てる行(全部=``rows``・前の版の記録は ``changed`` だけ=止める)。"""
    if "rows" not in plan:
        raise RuntimeError("plan の記録に全部の行(rows)が無い=plan を作り直す(検収 M4)")
    return list(plan["rows"])


def _check(root: Path, rows: list[dict[str, Any]], want: str) -> list[str]:
    bad = []
    for r in rows:
        p = root / r["path"]
        if r.get("action") == "kept_live_only":  # 本体の v2 だけにある行は前後とも同じ
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
    live, stage, backup = Path(a.live), Path(a.stage), Path(a.backup)
    plan = _json(Path(a.plan))
    changed = plan["changed"]
    pre = _check(live, _all_rows(plan), "before")
    if pre:
        print("本体の v2 が plan の「前」と違う(止めた):", *pre[:10], sep="\n  ", file=sys.stderr)
        return 2
    if backup.exists() and any(backup.iterdir()):
        print(f"退避の置き場が空でない: {backup.name}", file=sys.stderr)
        return 2
    print(f"写す {len(changed)} 本(置き換え {sum(r['action'] == 'moved' for r in changed)}・追加 "
          f"{sum(r['action'] == 'added' for r in changed)})・退避=本体の v2 の資産の全部を {backup.name} へ")
    if a.dry_run:
        for r in changed:
            print(f"  {r['action']:6s} {r['path']}")
        return 0
    backup.mkdir(parents=True)
    (backup / "acceptance").mkdir(exist_ok=True)
    lines = []
    for rel, p in asset_files(live).items():
        dst = backup / rel
        shutil.copy2(p, dst)
        sha = sha256(dst)
        if sha != sha256(p):
            raise RuntimeError(f"退避の写しの sha256 が違う: {rel}")
        lines.append(f"{sha}  {rel}")
    (backup / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    _write_json(backup / PLAN, plan)
    for r in changed:
        dst = live / r["path"]
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(stage / r["path"], dst)
    bad = _check(live, _all_rows(plan), "after")
    if bad or build_hash(live) != plan["build_hash_after"]:
        print("写した後の確かめに落ちた(revert で戻す):", *bad[:10], sep="\n  ", file=sys.stderr)
        return 3
    print(f"写した。build_hash {plan['build_hash_after'][:16]}")
    return 0


def cmd_revert(a: argparse.Namespace) -> int:
    live, backup = Path(a.live), Path(a.backup)
    plan = _json(backup / PLAN)
    for r in plan["changed"]:
        p = live / r["path"]
        if r["action"] == "moved":
            shutil.copy2(backup / r["path"], p)
        elif r["action"] == "added" and p.exists():
            p.unlink()
    bad = _check(live, _all_rows(plan), "before")
    if bad or build_hash(live) != plan["build_hash_before"]:
        print("戻した後の確かめに落ちた:", *bad[:10], sep="\n  ", file=sys.stderr)
        return 3
    print(f"戻した。build_hash {plan['build_hash_before'][:16]}")
    return 0


def cmd_verify(a: argparse.Namespace) -> int:
    live = Path(a.live)
    plan = _json(Path(a.plan))
    bad = _check(live, _all_rows(plan), a.want)
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
    sp.add_argument("--w21", default="data/world/v2_stage_4-1")
    sp.add_argument("--out", default="data/world/v2_stage_4-3")
    sp.add_argument("--out2", default="")
    sp.add_argument("--keep-out2", action="store_true")
    sp.add_argument("--data", default="data")
    sp.add_argument("--record", default="")
    sp = sub.add_parser("plan")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--stage", default="data/world/v2_stage_4-3")
    sp.add_argument("--record", default=str(HERE.parent / "activation_plan.json"))
    for name in ("apply", "verify", "revert"):
        sp = sub.add_parser(name)
        sp.add_argument("--live", default="data/world/v2")
        sp.add_argument("--stage", default="data/world/v2_stage_4-3")
        sp.add_argument("--backup", default="data/world/v2_pre_4-3")
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
