"""第 1 期 1-9(CP2 の段階 1)の byte-check: 10e の ``byte_check_10e.py`` の 19 構成に、帳簿の残高と金・物の台帳の行の sha と
manifest の ``economy``(K17 の容量と溢れ・transfer の計器)を足す。

``one`` は 10e の ``one`` をそのまま呼び(同じ 25 欄)、``cli.run`` の結果から次を足す(どちらの src でも同じ式):

- ``money_balances_sha``: 帳簿の残高(5 行 × 6 部門の配列・型つき)・``agents_money_sha``: 世帯の現金(SoA)
- ``money_flow_daily_sha``: 日次の流れの表の集約行・``money_core``: 取引の件数・却下の計数・容量
- ``money_raw_rows_sha``: 生ログの保持窓の中の行の全部・``money_raw_rows_last16384_sha``: その末尾 16,384 行
  (HEAD の既定の輪=16,384 行が持っていた行=溢れた輪と広げた輪で両方が持つ行)・``money_n_raw_dropped``
- ``goods_state_sha``: 物の台帳の在庫の配列と納品ログの行・``economy``: manifest の欄(HEAD には無い=「(欄なし)」)

``--rate`` で金の生ログの輪の係数(``economy.ledger.TRANSFERS_PER_AGENT_PER_DAY``)を上書きして回す(K17 の前の 3.0 で
HEAD と全部の欄が同じことを見るため)。

使い方(リポの根で・``$D`` = この置き場・``$W`` = 作業用の短いディレクトリ):

    git archive 136fdbb src docs/bench/anchors docs/design/v2-budget-declaration.md \\
        docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
    mkdir -p $W/head_src/data/calendar && cp data/calendar/syukujitsu.csv $W/head_src/data/calendar/
    python $D/byte_check_cp2.py side --src $W/head_src/src --label head --scratch $W --out $W/head.json
    python $D/byte_check_cp2.py side --label cp2 --scratch $W --out $W/cp2.json
    python $D/byte_check_cp2.py side --label cp2_rate3 --rate 3.0 --scratch $W --out $W/cp2_rate3.json
    python $D/byte_check_cp2.py compare --a $W/head.json --b $W/cp2.json --out $D/../byte_check_cp2.json

絶対パスは JSON に書かない。逐次ループ宣言: なし(道具)。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import contextlib
import hashlib
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
B10 = REPO / "docs" / "bench" / "analysis" / "wallbounce-1012" / "10e" / "byte_check_10e.py"
TAIL = 16_384


def _b10() -> Any:
    spec = importlib.util.spec_from_file_location("byte_check_10e_cp2", B10)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["byte_check_10e_cp2"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _sha(parts: list[bytes]) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(len(p).to_bytes(8, "little"))
        h.update(p)
    return h.hexdigest()[:16]


def _arr(a: Any) -> list[bytes]:
    import numpy as np

    x = np.ascontiguousarray(np.asarray(a))
    return [f"{x.dtype.str}{x.shape}".encode("ascii"), x.tobytes()]


def ledger_fields(res: Any) -> dict[str, Any]:
    """帳簿の残高と金・物の台帳の行の sha(HEAD と今の src で同じ式)。"""
    bundle = getattr(res, "ledger", None)
    out: dict[str, Any] = {}
    led = getattr(bundle, "money", None)
    if led is not None:
        parts: list[bytes] = []
        for line in sorted(led._lines):
            for arr in led._lines[line]:
                parts += _arr(arr)
        out["money_balances_sha"] = _sha(parts)
        parts = []
        for f in led.flow_daily:
            parts += _arr(f)
        out["money_flow_daily_sha"] = _sha(parts)
        rows = led.raw_rows()
        out["money_raw_rows"] = int(rows.shape[0])
        out["money_raw_rows_sha"] = _sha(_arr(rows))
        out["money_raw_rows_last16384_sha"] = _sha(_arr(rows[-TAIL:]))
        out["money_n_raw_dropped"] = int(led.n_raw_dropped)
        out["money_core"] = {"n_transfers": int(led.n_transfers),
                             "rejections": {str(k): int(v) for k, v in led.rejections.items()},
                             "raw_capacity": int(led.raw_capacity)}
        out["money_state_hash"] = led.state_hash()[:16]
    g = getattr(bundle, "goods", None)
    if g is not None:
        parts = []
        for a in g._guarded():
            parts += _arr(a)
        parts += _arr(g.delivery_rows())
        out["goods_state_sha"] = _sha(parts)
        out["goods_n_moves"] = int(g.n_moves)
    agents = getattr(res, "agents", None)
    if agents is not None:
        out["agents_money_sha"] = _sha(_arr(agents.registry.money))
    man = res.run_manifest_fields()
    out["economy"] = man.get("economy", "(欄なし)")
    out["daily_economy"] = [d.get("economy", "(欄なし)") for d in man.get("daily", [])]
    out["daily_events_rows"] = [int((d.get("events") or {}).get("rows", -1)) for d in man.get("daily", [])]
    return out


def cmd_one(args: argparse.Namespace) -> int:
    from shibuya import cli

    if args.rate:
        from shibuya.economy import ledger as LED

        LED.TRANSFERS_PER_AGENT_PER_DAY = float(args.rate)  # type: ignore[misc]
    got: dict[str, Any] = {}
    orig = cli.run

    def run(*a: Any, **k: Any) -> Any:
        res = orig(*a, **k)
        got["res"] = res
        return res

    cli.run = run  # type: ignore[assignment]
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _b10().cmd_one(args)
    if rc != 0:
        return rc
    row = json.loads(buf.getvalue().strip().splitlines()[-1])
    row.update(ledger_fields(got["res"]))
    row["rate"] = args.rate or ""
    print(json.dumps(row, ensure_ascii=False))
    return 0


def cmd_side(args: argparse.Namespace) -> int:
    b10 = _b10()
    w2 = b10._wave2()
    scratch = Path(args.scratch)
    names = list(w2.configs()) if not args.only else [s for s in args.only.split(",") if s]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if args.src:
        env["PYTHONPATH"] = str(Path(args.src).resolve())
        env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"

    def one(name: str) -> dict[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed),
               "--tape", str(scratch / f"{args.label}_{name}"), "--kw", args.kw or "", "--rate", args.rate or "",
               "--drop-behavior-item", "", "--multiset-items", ""]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": name, "error": r.stderr[-3000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    got: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, names):
            got[row["config"]] = row
            print(row["config"], row.get("final"), row.get("calls"), (row.get("economy") or {}) if isinstance(
                row.get("economy"), dict) else row.get("economy"), (row.get("error") or "")[-300:], flush=True)
    doc = {"label": args.label, "kw": json.loads(args.kw or "{}"), "rate": args.rate or "",
           "src": "写し" if args.src else "作業木", "agents": args.agents, "seed": args.seed, "runs": got}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


#: 10e の 25 欄に足す欄(帳簿の残高と台帳の行)。
LEDGER_KEYS = ("money_balances_sha", "agents_money_sha", "money_flow_daily_sha", "money_core", "money_state_hash",
               "goods_state_sha", "goods_n_moves", "money_raw_rows_last16384_sha", "money_raw_rows_sha",
               "money_raw_rows", "money_n_raw_dropped")


def cmd_compare(args: argparse.Namespace) -> int:
    b10 = _b10()
    keys = tuple(b10.COMPARE_KEYS) + LEDGER_KEYS
    a = json.loads(Path(args.a).read_text(encoding="utf-8"))
    b = json.loads(Path(args.b).read_text(encoding="utf-8"))
    rows: dict[str, Any] = {}
    for name in a["runs"]:
        ra, rb = a["runs"][name], b["runs"].get(name, {})
        if "error" in ra or "error" in rb:
            rows[name] = {"error_a": ra.get("error", "")[-500:], "error_b": rb.get("error", "")[-500:]}
            continue
        same, moved = [], {}
        for k in keys:
            va, vb = ra.get(k), rb.get(k)
            if va == vb:
                same.append(k)
            else:
                moved[k] = {"a": va, "b": vb}
        rows[name] = {"same": same, "moved": moved, "economy_b": rb.get("economy"),
                      "daily_economy_b": rb.get("daily_economy"),
                      "daily_events_rows": {"a": ra.get("daily_events_rows"), "b": rb.get("daily_events_rows")}}
    doc = {"a": {"label": a.get("label"), "rate": a.get("rate"), "src": a.get("src")},
           "b": {"label": b.get("label"), "rate": b.get("rate"), "src": b.get("src")},
           "note": args.note, "keys": list(keys), "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    n_final = sum(1 for r in rows.values() if "moved" in r and "final" not in r["moved"])
    n_all = sum(1 for r in rows.values() if "moved" in r and not r["moved"])
    print(f"{len(rows)} 構成・final が同じ {n_final}・全部の欄が同じ {n_all}")
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
        sp.add_argument("--rate", default="")
        sp.add_argument("--drop-behavior-item", default="")
        sp.add_argument("--multiset-items", default="")
        if name == "one":
            sp.add_argument("--config", required=True)
            sp.add_argument("--tape", required=True)
        else:
            sp.add_argument("--src", default="")
            sp.add_argument("--label", required=True)
            sp.add_argument("--scratch", required=True)
            sp.add_argument("--out", required=True)
            sp.add_argument("--only", default="")
            sp.add_argument("--jobs", type=int, default=4)
    sp = sub.add_parser("compare")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--note", default="")
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "compare": cmd_compare}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
