"""第 4 期 4-1 段 4〜7(W21b): 世界資産 ``data/world/v2_stage_4-1b`` の組み立て・差の表・写し・戻し・確かめ。

段 1〜3 の道具 ``pop41/tools/stage_pop41.py`` と同じ形(stage / plan / apply / revert / verify / materialize)。plan 以下は
段 1〜3 の道具の関数をそのまま使う(既定の置き場だけ 4-1b に)。**本段では apply しない**(段 10=4-3・親が決める)。

- ``stage``: 段 1〜3 の資産(``--base``=``v2_stage_4-1``・本体の v2 の写し 107 本+W21 の 6 本)の直下のファイルと
  ``acceptance/`` を ``--out`` へ本物のコピーで写し(sha256 を照らす)、段 4〜7(``w21_build_b``)を ``--out`` に組む
  (``--base`` は読むだけ)。``--runs 2`` で 2 回目を ``--scratch`` に組み、出力の sha256 が 1 回目と同じことを確かめる。
  最後に ``--out`` の全部のファイルの ``MANIFEST.sha256`` を書く。build_hash は本体の v2 と同じ(W21・W21b は ``build.run``
  の段に入らない)。
- ``plan``・``apply``(**親が実行する**・``--dry-run`` は前提の確かめだけ)・``revert``・``verify``・``materialize``: 段 1〜3 の
  道具と同じ。

ファイルの中身は読まない(sha256・md5・バイト数だけ)。build_hash は ``build_manifest.json`` の 1 欄だけを読む。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
_P41 = HERE.parents[1] / "pop41" / "tools" / "stage_pop41.py"
_spec = importlib.util.spec_from_file_location("stage_pop41", _P41)
P41 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(P41)  # type: ignore[union-attr]

W21B_FILES: tuple[str, ...] = ("w21_people.parquet", "w21_org.parquet", "w21_rights_initial.parquet",
                               "w21_relations_initial.parquet", "w21_money.parquet", "w21_money_households.parquet",
                               "w21_prior_places.parquet", "w21_outside.parquet", "w21_outside_households.parquet",
                               "w21_checks_b.json", "w21b_manifest.json", "W21b.header.json")
MANIFEST = P41.MANIFEST


def _w21b(out: Path, data: str, base: str, extra: list[str]) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str((REPO / "src").resolve())
    cmd = [sys.executable, "-m", "shibuya.build.pop.w21_build_b", "--out", str(out), "--data", data, "--base", base,
           *extra]
    return subprocess.run(cmd, env=env, cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")


def cmd_stage(a: argparse.Namespace) -> int:
    base, out = Path(a.base), Path(a.out)
    if out.exists() and any(out.iterdir()) and not a.reuse:
        print(f"--out が空でない: {out}(作り直すなら消してから・続きなら --reuse)", file=sys.stderr)
        return 2
    out.mkdir(parents=True, exist_ok=True)
    if not a.reuse:
        src = {k: v for k, v in P41.asset_files(base).items() if k not in W21B_FILES}
        (out / "acceptance").mkdir(exist_ok=True)
        for rel, p in src.items():
            dst = out / rel
            shutil.copy2(p, dst)
            if P41.sha256(dst) != P41.sha256(p):
                raise RuntimeError(f"写しの sha256 が違う: {rel}")
        print(f"写した {len(src)} 本(sha256 一致)")
    extra = ["--world", a.world] + (["--division-arm", a.division_arm] if a.division_arm else []) + \
        (["--affinity", a.affinity] if a.affinity else [])
    runs: list[dict[str, str]] = []
    dirs = [out] + [Path(a.scratch) / f"run{i + 1}" for i in range(1, int(a.runs))]
    codes = []
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        r = _w21b(d, a.data, str(base), extra)
        codes.append(r.returncode)
        if r.returncode not in (0, 1):
            print(r.stdout[-3000:], r.stderr[-3000:], file=sys.stderr)
            return r.returncode
        runs.append({f: P41.sha256(d / f) for f in W21B_FILES})
        print(f"組み立て {len(runs)}: 終了コード {r.returncode}・{r.stdout.strip()[-160:]}")
    same = all(r == runs[0] for r in runs)
    files = P41.asset_files(out)
    lines = [f"{P41.sha256(p)}  {rel}" for rel, p in sorted(files.items())]
    (out / MANIFEST).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    man = json.loads((out / "w21b_manifest.json").read_text(encoding="utf-8"))
    doc = {"runs": int(a.runs), "exit_codes": codes, "w21b_sha256_by_run": runs, "deterministic": same,
           "w21b_build_hash": man["w21b_build_hash"], "w21_build_hash_of_base": man["base"]["w21_build_hash"],
           "build_hash_of_stage": P41.build_hash(out), "build_hash_of_base": P41.build_hash(base),
           "files_in_stage": len(files), "stage_manifest_sha256": P41.sha256(out / MANIFEST),
           "bytes_w21b": {f: (out / f).stat().st_size for f in W21B_FILES}}
    print(json.dumps({k: v for k, v in doc.items() if k != "w21b_sha256_by_run"}, ensure_ascii=False))
    if a.record:
        Path(a.record).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0 if same else 3


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("stage")
    sp.add_argument("--base", default="data/world/v2_stage_4-1")
    sp.add_argument("--world", default="data/world/v2")
    sp.add_argument("--out", default="data/world/v2_stage_4-1b")
    sp.add_argument("--data", default="data")
    sp.add_argument("--runs", type=int, default=2)
    sp.add_argument("--scratch", default="_bc/w21b_stage_runs")
    sp.add_argument("--division-arm", choices=("on", "off"), default="")
    sp.add_argument("--affinity", choices=("lifestage", "distance_only"), default="")
    sp.add_argument("--reuse", action="store_true")
    sp.add_argument("--record", default="")
    sp = sub.add_parser("plan")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--stage", default="data/world/v2_stage_4-1b")
    sp.add_argument("--steps", default="data/world/v2_steps_4-1b")
    sp.add_argument("--record", default="")
    sp.add_argument("--dry-run", action="store_true")
    for name in ("apply", "revert"):
        sp = sub.add_parser(name)
        sp.add_argument("--live", default="data/world/v2")
        sp.add_argument("--backup", default="data/world/v2_pre_4-1b")
        sp.add_argument("--dry-run", action="store_true")
        if name == "apply":
            sp.add_argument("--steps", default="data/world/v2_steps_4-1b")
    sp = sub.add_parser("materialize")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--backup", default="data/world/v2_pre_4-1b")
    sp.add_argument("--out", required=True)
    sp = sub.add_parser("verify")
    sp.add_argument("--live", default="data/world/v2")
    sp.add_argument("--steps", default="data/world/v2_steps_4-1b")
    sp.add_argument("--want", choices=("before", "after"), default="after")
    a = ap.parse_args(argv)
    return {"stage": cmd_stage, "plan": P41.cmd_plan, "apply": P41.cmd_apply, "revert": P41.cmd_revert,
            "verify": P41.cmd_verify, "materialize": P41.cmd_materialize}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
