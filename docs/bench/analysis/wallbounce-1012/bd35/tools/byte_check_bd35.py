"""第 3 期 3-5 の byte-check(10e の道具の 1 本のランをそのまま使い、体の層の腕と段の境目の列の欄を足す)。

比べ方は [10e/byte_check_10e.py](../../10e/byte_check_10e.py) と同じ 19 構成(mock/classical 5,000 体・seed 1・1 シミュ日・
テープつき)。``one`` は 10e の ``one`` をそのまま回し(``cli.run`` を包んで結果を受け取るだけ)、manifest の ``body`` から
腕(``body_arm``)・段の境目の列の鎖のハッシュ(``boundary_digest``)・種類ごとの数(``boundaries``)・規則に通した体の延べ
(``body_evals``・``felt_evals``)を足す。

- ``--body-schedule {sweep,reserve}``: 体の予約の腕(``engine.body.set_arm``)。
- ``--gauge``: 段の境目の計器を数える(環境変数 ``SHIBUYA_BODY_BOUNDARY_GAUGE=1`` を子のプロセスに渡す・〔3-5 検収 L6〕既定の
  ランは数えない=``boundary_digest``・``boundaries`` は null)。腕の一致(reserve=sweep)の比べは両側とも立てて回す。
- ``--shift K``: **負の対照**(試験のときだけ): 予約の刻みと体感温度の予約の窓を K だけ遅らせる(K<0 は早める=下界の予約
  なので結果は変わらない=早めは「今の刻み+1」より前にしない)。``engine.body.schedule.next_intero_steps`` と
  ``next_felt_frames`` をこの道具のプロセスの中だけ包む(src は変えない)。

使い方(作業木の根で・``$W`` = 作業用の置き場 ``_bc``・head の side は 10e の道具で作る):

    python $D/tools/byte_check_bd35.py side --label wt_sweep --scratch $W --out $W/wt_sweep.json
    python $D/tools/byte_check_bd35.py side --label wt_reserve --body-schedule reserve --scratch $W --out $W/wt_reserve.json
    python $D/tools/byte_check_bd35.py side --label wt_shift1 --body-schedule reserve --shift 1 --only w6_v3_default \\
        --scratch $W --out $W/wt_shift1.json
    python $D/tools/byte_check_bd35.py compare --a $W/head.json --b $W/wt_sweep.json --out $D/head_vs_sweep.json

``compare`` は 10e の欄(25)に、両方の side にあれば体の欄(``boundary_digest``・``boundaries``)を足して比べる。
絶対パスは JSON に書かない。逐次ループ宣言: 構成の数ぶん(道具)。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import contextlib
import importlib.util
import io
import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
B10E = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "10e" / "byte_check_10e.py"
BODY_KEYS = ("boundary_digest", "boundaries")


def _b10e() -> Any:
    spec = importlib.util.spec_from_file_location("byte_check_10e", B10E)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["byte_check_10e"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _shift(k: int) -> None:
    """負の対照: 予約を k だけずらす(このプロセスの中だけ)。"""
    import numpy as np

    from shibuya.engine.body import schedule as BS

    real_i, real_f = BS.next_intero_steps, BS.next_felt_frames

    def intero(now, **kw):  # noqa: ANN001, ANN003, ANN202
        at = real_i(now, **kw)
        fin = at != BS.NEVER
        out = at.copy()
        out[fin] = np.maximum(at[fin] + int(k), int(now) + 1)
        return out

    def felt(frame, cols, nxt):  # noqa: ANN001, ANN202
        nf = real_f(frame, cols, nxt)
        fin = nf != BS.NEVER
        out = nf.copy()
        out[fin] = np.maximum(nf[fin] + int(k), int(frame) + 1)
        return out

    BS.next_intero_steps = intero  # type: ignore[assignment]
    BS.next_felt_frames = felt  # type: ignore[assignment]


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine import body as B

    if args.body_schedule:
        B.set_arm(args.body_schedule)
    if args.shift:
        _shift(int(args.shift))
    m10 = _b10e()
    real = cli.run
    box: dict[str, Any] = {}

    def run(*a: Any, **k: Any) -> Any:
        r = real(*a, **k)
        box["r"] = r
        return r

    cli.run = run  # type: ignore[assignment]
    ns = argparse.Namespace(config=args.config, world=args.world, agents=args.agents, seed=args.seed, tape=args.tape,
                            kw=args.kw, drop_behavior_item="", multiset_items="")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        m10.cmd_one(ns)
    row = json.loads(buf.getvalue().strip().splitlines()[-1])
    man = box["r"].run_manifest_fields()["body"]
    row.update(body_arm=man["arm"], boundary_digest=man["boundary_digest"], boundaries=man["boundaries"],
               body_evals=man["agent_evals"], felt_evals=man["felt_evals"], body_reservations=man["reservations"],
               felt_reservations=man["felt_reservations"], body_shift=int(args.shift or 0))
    print(json.dumps(row, ensure_ascii=False))
    return 0


def cmd_side(args: argparse.Namespace) -> int:
    m10 = _b10e()
    w2 = m10._wave2()
    scratch = Path(args.scratch)
    names = list(w2.configs()) if not args.only else [s for s in args.only.split(",") if s]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(REPO / "src")  # 子プロセスは作業木の src を読む(``src_is_worktree`` が真になる)
    if args.gauge:
        env["SHIBUYA_BODY_BOUNDARY_GAUGE"] = "1"

    def one(name: str) -> dict[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed),
               "--tape", str(scratch / f"{args.label}_{name}"), "--kw", args.kw or "",
               "--body-schedule", args.body_schedule or "", "--shift", str(args.shift or 0)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": name, "error": r.stderr[-3000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    got: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, names):
            got[row["config"]] = row
            print(row["config"], row.get("final"), row.get("calls"), row.get("body_arm"),
                  (row.get("boundary_digest") or "")[:16], (row.get("error") or "")[-300:], flush=True)
    doc = {"label": args.label, "kw": json.loads(args.kw or "{}"), "src": "作業木", "env": m10.switch_env(),
           "body_schedule": args.body_schedule or "(既定)", "shift": int(args.shift or 0), "gauge": bool(args.gauge),
           "agents": args.agents, "seed": args.seed, "runs": got}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    m10 = _b10e()
    a = json.loads(Path(args.a).read_text(encoding="utf-8"))
    b = json.loads(Path(args.b).read_text(encoding="utf-8"))
    rows: dict[str, Any] = {}
    for name in a["runs"]:
        ra, rb = a["runs"][name], b["runs"].get(name, {})
        if not rb:
            continue
        if "error" in ra or "error" in rb:
            rows[name] = {"error_a": ra.get("error", "")[-500:], "error_b": rb.get("error", "")[-500:]}
            continue
        keys = list(m10.COMPARE_KEYS) + [k for k in BODY_KEYS if k in ra and k in rb]
        same, moved = [], {}
        for k in keys:
            if ra.get(k) == rb.get(k):
                same.append(k)
            else:
                moved[k] = {"a": ra.get(k), "b": rb.get(k)}
        rows[name] = {"same": same, "moved": moved, "n_keys": len(keys),
                      "body_arm": [ra.get("body_arm", "(欄なし=HEAD)"), rb.get("body_arm", "(欄なし=HEAD)")],
                      "body_evals": [ra.get("body_evals"), rb.get("body_evals")],
                      "felt_evals": [ra.get("felt_evals"), rb.get("felt_evals")]}
    meta = ("label", "kw", "src", "env", "body_schedule", "shift", "gauge")
    doc = {"a": {k: a.get(k) for k in meta}, "b": {k: b.get(k) for k in meta}, "note": args.note, "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n_same = sum(1 for r in rows.values() if "moved" in r and not r["moved"])
    print(f"{len(rows)} 構成・全部の欄が同じ {n_same}")
    for name, r in rows.items():
        print(name, sorted(r.get("moved", {}).keys()) if "moved" in r else r)
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "side"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        sp.add_argument("--kw", default="")
        sp.add_argument("--body-schedule", default="")
        sp.add_argument("--shift", type=int, default=0)
        if name == "one":
            sp.add_argument("--config", required=True)
            sp.add_argument("--tape", required=True)
        else:
            sp.add_argument("--label", required=True)
            sp.add_argument("--scratch", required=True)
            sp.add_argument("--out", required=True)
            sp.add_argument("--only", default="")
            sp.add_argument("--jobs", type=int, default=4)
            sp.add_argument("--gauge", action="store_true")
    sp = sub.add_parser("compare")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--note", default="")
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
