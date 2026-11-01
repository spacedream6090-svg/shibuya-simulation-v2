"""第 1 期 1-5: 今の既定で「権限で止める検査」が当たった回数を 19 構成で数える(口の約束 1-5 の約束 (1))。

数えるもの(どれも結果を変えない=関数を包んで数えるだけ):

- ``resolve.request_open_close`` の呼び出しと行の数・``permitted`` が偽の行(HEAD では NO_PERMISSION を書いて止める行)。
  ``NO_PERMISSION`` を ``last_result`` に書くのは src の中でこの関数だけ(grep で確かめた=記録 r15/README.md §4)。
- 判断(LLM/mock/古典)の応答が役割語だった回数(``LLMBridge.call`` の ``role_action``・語ごと)。HEAD ではここで
  待機/なしへ落とす(「権限検査待ち」の印)。
- 群・規範の計器(``norm_meter``)の ``no_permission`` と ``role_actions``(manifest の ``group_norms.role_words``)。
- 開閉と補充の過程の計数(担当が現場に居たか=実行の主体の選び。止める検査ではない・参考)。
- 作業木の側だけ: 出来事の記録の ``行為:許可のない行動`` の行数と manifest の ``rights``(1-5 で足した欄)。

構成は byte-check と同じ 19 構成(``10e/byte_check_10e.py`` が使う ``wave2_bytecheck.configs()``)・5,000 体・seed 1・
1 シミュ日。テープは書かない(数えるだけ。final は byte-check の side と同じになるはず=記録で突き合わせる)。

使い方(リポの根で・``$W`` = 作業用の短いディレクトリ・``$H`` = HEAD の写しの src):

    python <この置き場>/count_no_permission.py side --src $H --label head --out $W/np_head.json
    python <この置き場>/count_no_permission.py side --label r15 --out $W/np_r15.json
    python <この置き場>/count_no_permission.py table --a $W/np_head.json --b $W/np_r15.json --out <記録の置き場>/no_permission_r15.json

絶対パスは JSON に書かない。壁時計は JSON に入れない(標準出力だけ)。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import os
import subprocess
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
WAVE2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"


def _wave2() -> Any:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def cmd_one(args: argparse.Namespace) -> int:
    import numpy as np

    import shibuya
    from shibuya import cli
    from shibuya.engine import llm_bridge as LB
    from shibuya.engine import resolve as R

    cnt: Counter[str] = Counter()
    role_words: Counter[str] = Counter()
    orig_roc = R.request_open_close

    def roc(agents, world, agent_ids, poi_ids, want_open, tick, *a, **kw):  # noqa: ANN001
        ids = np.asarray(agent_ids, dtype=np.int64).ravel()
        perm = kw.get("permitted")
        ok = np.zeros(ids.size, dtype=bool) if perm is None else np.asarray(perm, dtype=bool).ravel()
        cnt["open_close_calls"] += 1
        cnt["open_close_rows"] += int(ids.size)
        cnt["open_close_not_permitted_rows"] += int((~ok).sum())
        return orig_roc(agents, world, agent_ids, poi_ids, want_open, tick, *a, **kw)

    R.request_open_close = roc
    orig_call = LB.LLMBridge.call

    def call(self, *a, **kw):  # noqa: ANN001
        res = orig_call(self, *a, **kw)
        cnt["bridge_calls"] += 1
        if getattr(res, "role_action", False):
            cnt["bridge_role_actions"] += 1
            role_words[str(getattr(res.parse, "action", "") or "")] += 1
        return res

    LB.LLMBridge.call = call
    w2 = _wave2()
    kw = dict(w2.configs()[args.config])
    t0 = time.perf_counter()
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, **kw)
    wall = time.perf_counter() - t0
    man = res.run_manifest_fields()
    gn = dict(man.get("group_norms", {}) or {})
    rw = dict(gn.get("role_words", {}) or {})
    pc = dict(getattr(res, "process_counters", {}) or {})
    ev = getattr(res, "event_log", None)
    unauth = None
    if ev is not None:
        unauth = int(ev.what_counts().get("行為:許可のない行動", 0)) if "行為:許可のない行動" in _vocab() else None
    src_root = Path(shibuya.__file__).resolve().parents[1]
    print(json.dumps({
        "config": args.config,
        "src_is_worktree": src_root == (REPO / "src").resolve(),
        "final": res.final_hash[:16],
        "calls": int(res.llm_calls),
        "counts": dict(sorted(cnt.items())),
        "bridge_role_words": dict(sorted(role_words.items())),
        "norm_meter_enabled": bool(gn.get("enabled", False)),
        "norm_meter_no_permission": rw.get("no_permission"),
        "norm_meter_role_actions": rw.get("role_actions"),
        "norm_meter_by_word_result": rw.get("by_word_result"),
        "opening": {k: pc.get(f"opening.{k}") for k in ("events", "role_actions", "fallback", "staffed_pois")},
        "shelf": {k: pc.get(f"shelf.{k}") for k in ("role_actions", "fallback")},
        "events_unauthorized": unauth,
        "manifest_rights": man.get("rights", "(欄なし)"),
        "wall_s": round(wall, 1),
    }, ensure_ascii=False))
    return 0


def _vocab() -> tuple[str, ...]:
    from shibuya.engine.events import vocab as V

    return tuple(V.VOCAB)


def cmd_side(args: argparse.Namespace) -> int:
    w2 = _wave2()
    names = list(w2.configs()) if not args.only else [s for s in args.only.split(",") if s]
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    if args.src:
        env["PYTHONPATH"] = str(Path(args.src).resolve())
        env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"

    def one(name: str) -> dict[str, Any]:
        cmd = [sys.executable, str(Path(__file__)), "one", "--config", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", env=env, cwd=str(REPO))
        if r.returncode != 0:
            return {"config": name, "error": r.stderr[-3000:]}
        return json.loads(r.stdout.strip().splitlines()[-1])

    got: dict[str, Any] = {}
    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for row in ex.map(one, names):
            got[row["config"]] = row
            print(row["config"], row.get("final"), row.get("counts"), row.get("norm_meter_no_permission"),
                  row.get("src_is_worktree"), row.get("wall_s"), (row.get("error") or "")[-300:], flush=True)
    for row in got.values():
        row.pop("wall_s", None)
    doc = {"label": args.label, "src": "写し" if args.src else "作業木", "agents": args.agents, "seed": args.seed,
           "runs": got}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def cmd_table(args: argparse.Namespace) -> int:
    """2 つの側の数を構成ごとに並べる(HEAD=止める検査が当たった回数・作業木=記録に替えた後の行数)。"""
    a = json.loads(Path(args.a).read_text(encoding="utf-8"))
    b = json.loads(Path(args.b).read_text(encoding="utf-8")) if args.b else {"runs": {}}
    rows: dict[str, Any] = {}
    tot: Counter[str] = Counter()
    for name, ra in a["runs"].items():
        rb = b["runs"].get(name, {})
        if "error" in ra or "error" in rb:
            rows[name] = {"error_a": ra.get("error", "")[-300:], "error_b": rb.get("error", "")[-300:]}
            continue
        c = ra["counts"]
        row = {
            "head_open_close_not_permitted_rows": int(c.get("open_close_not_permitted_rows", 0)),
            "head_open_close_rows": int(c.get("open_close_rows", 0)),
            "head_bridge_role_actions": int(c.get("bridge_role_actions", 0)),
            "head_norm_meter_no_permission": ra.get("norm_meter_no_permission"),
            "head_norm_meter_role_actions": ra.get("norm_meter_role_actions"),
            "head_final": ra.get("final"),
        }
        if rb:
            cb = rb["counts"]
            row.update({
                "r15_open_close_not_permitted_rows": int(cb.get("open_close_not_permitted_rows", 0)),
                "r15_bridge_role_actions": int(cb.get("bridge_role_actions", 0)),
                "r15_norm_meter_no_permission": rb.get("norm_meter_no_permission"),
                "r15_events_unauthorized": rb.get("events_unauthorized"),
                "r15_final": rb.get("final"),
                "final_same": ra.get("final") == rb.get("final"),
                "r15_rights": rb.get("manifest_rights"),
            })
        for k in ("head_open_close_not_permitted_rows", "head_bridge_role_actions"):
            tot[k] += int(row[k])
        tot["head_norm_meter_no_permission"] += int(row["head_norm_meter_no_permission"] or 0)
        if rb:
            tot["r15_events_unauthorized"] += int(row["r15_events_unauthorized"] or 0)
        rows[name] = row
    doc = {"a": {"label": a.get("label"), "src": a.get("src")}, "b": {"label": b.get("label"), "src": b.get("src")},
           "agents": a.get("agents"), "seed": a.get("seed"), "totals": dict(sorted(tot.items())), "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["totals"], ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("one", "side"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name == "one":
            sp.add_argument("--config", required=True)
        else:
            sp.add_argument("--src", default="")
            sp.add_argument("--label", required=True)
            sp.add_argument("--out", required=True)
            sp.add_argument("--only", default="")
            sp.add_argument("--jobs", type=int, default=4)
    sp = sub.add_parser("table")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", default="")
    sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"one": cmd_one, "side": cmd_side, "table": cmd_table}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
