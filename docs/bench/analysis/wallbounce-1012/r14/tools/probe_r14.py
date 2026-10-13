"""第 1 期 1-4(r14): 系ごとの指紋(1-0 の ``engine.systems.probe``)を HEAD と作業木で比べる。

e13 の ``e13/tools/probe_e13.py`` を写して、外す物だけを 1-4 の分に替えた(HEAD は 1-3 を含むので 1-3 の物は外さない)。
作業木の側で 1-4 が足した物を指紋から外す:

- ``RunResult.run_kind``(1-4 で足した結果の欄。ランの中は常に ``None``=``cli.run`` が終わった後に置く)。
- 日次の記録の ``rules_version``(足した欄)と ``bridges_count``(HEAD は null・1-4 は件数=HEAD と同じ null に戻して比べる)
  (積算 ``daily_records`` と ``RunResult.daily`` の各行)。ほかの欄は比べる。

両側とも、digest の材料から物の番号(``id``)を外す(e13 と同じ)。

使い方(リポの根で・``PYTHONHASHSEED=0``・``PYTHONPATH`` で src を選ぶ)::

    PYTHONPATH=<HEAD の写し>/src python $D/probe_r14.py side --label head --out $W/probe_head.json
    PYTHONPATH=<作業木>/src     python $D/probe_r14.py side --label r14  --out $W/probe_r14.json
    python $D/probe_r14.py compare --a $W/probe_head.json --b $W/probe_r14.json --out $D/../probe_r14.json

絶対パスは JSON に書かない。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

#: 構成(e13 と同じ=合成の世界 80 体 720 刻み・世界資産 300 体の既定 v3 と記憶+関係)。
CONFIGS = {
    "syn_mem_rel_store": dict(fn="run_day", n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0,
                              sleep_suppression=False, vocab_version="v3", memory="on", relations="on",
                              rel_copresent="on", store_memory="on", checkpoint_every=60),
    "real300_v3_default": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3"),
    "real300_v3_mem_rel": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3",
                               memory="on", relations="on"),
}


def _strip_ids(x):  # noqa: ANN001, ANN202
    if isinstance(x, tuple) and len(x) == 3 and x[0] in ("fn", "ref") and isinstance(x[2], int):
        return (x[0], x[1])
    if isinstance(x, (list, tuple)):
        return type(x)(_strip_ids(y) for y in x)
    return x


def _patch_both() -> None:
    from shibuya.engine.systems import probe as PR

    def digest_value(v, objs=False, refs=frozenset()):  # noqa: ANN001, ANN202
        return PR._hx(repr(_strip_ids(PR.plain(v, 0, objs, refs))).encode("utf-8"))

    PR._digest_value = digest_value


def _daily_as_head(rows):  # noqa: ANN001, ANN202
    out = []
    for r in rows:
        d = {k: x for k, x in r.items() if k != "rules_version"}
        if "bridges_count" in d:
            d["bridges_count"] = None
        out.append(d)
    return out


def _patch_r14() -> bool:
    """作業木の側だけ: 1-4 で足した結果の欄と日次の記録の欄を外す(HEAD の側では何もしない)。"""
    from shibuya.engine.systems import probe as PR

    try:
        from shibuya.engine.bridging import ledger as _BR  # noqa: F401  (作業木の側の印)
    except ImportError:
        return False
    PR.RESULT_SKIP = PR.RESULT_SKIP | {"run_kind"}
    real_view_of, real_rd = PR.view_of, PR._result_digest

    def view_of(box):  # noqa: ANN001, ANN202
        v = real_view_of(box)
        t = dict(v.tally)
        if t.get("daily_records"):
            t["daily_records"] = _daily_as_head(t["daily_records"])
        v.tally = t
        return v

    def result_digest(res):  # noqa: ANN001, ANN202
        daily = getattr(res, "daily", None)
        if not daily:
            return real_rd(res)
        res.daily = _daily_as_head(daily)
        try:
            return real_rd(res)
        finally:
            res.daily = daily

    PR.view_of, PR._result_digest = view_of, result_digest
    return True


def cmd_side(a: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine.run import run_day
    from shibuya.engine.systems import probe as PR

    _patch_both()
    patched = _patch_r14()
    out = {"label": a.label, "patched_r14": patched, "runs": {}}
    for name, kw in CONFIGS.items():
        kw = dict(kw)
        fn = run_day if kw.pop("fn") == "run_day" else cli.run
        pr = PR.Probe(check=None, ticks=None)
        PR.ACTIVE = pr
        t0 = time.perf_counter()
        try:
            res = fn(**kw)
        finally:
            PR.ACTIVE = None
        d = pr.to_json()
        out["runs"][name] = {"final": res.final_hash[:16], "calls": int(res.llm_calls), "fp": d["fp"],
                             "n_entries": len(d["entries"]), "entries": d["entries"],
                             "wall_s": round(time.perf_counter() - t0, 1)}
        print(name, res.final_hash[:16], len(d["entries"]), flush=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return 0


def cmd_compare(a: argparse.Namespace) -> int:
    from shibuya.engine.systems import probe as PR

    x = json.loads(Path(a.a).read_text(encoding="utf-8"))
    y = json.loads(Path(a.b).read_text(encoding="utf-8"))
    rows, ok = {}, True
    for name in x["runs"]:
        ra, rb = x["runs"][name], y["runs"][name]
        fd = PR.first_diff(ra, rb)
        same_fp = ra["fp"] == rb["fp"]
        rows[name] = {"final_a": ra["final"], "final_b": rb["final"], "calls_a": ra["calls"], "calls_b": rb["calls"],
                      "n_entries_a": ra["n_entries"], "n_entries_b": rb["n_entries"], "systems": len(ra["fp"]),
                      "fp_same_all_systems": same_fp, "first_diff": fd}
        ok &= same_fp and fd is None and ra["final"] == rb["final"]
    doc = {"schema": "shibuya.bench/r14/probe/1", "a": x["label"], "b": y["label"], "b_patched_r14": y["patched_r14"],
           "how": "1-0 の probe(全部の刻み・系ごとの全欄の差と指紋)。作業木の側は 1-4 で足した RunResult.run_kind と日次の"
                  "記録の rules_version を外し、bridges_count を HEAD と同じ null に戻した。PYTHONHASHSEED=0",
           "all_ok": bool(ok), "rows": rows}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_ok": ok, **{k: (v["fp_same_all_systems"], v["first_diff"]) for k, v in rows.items()}},
                     ensure_ascii=False))
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("side")
    sp.add_argument("--label", required=True)
    sp.add_argument("--out", required=True)
    sp = sub.add_parser("compare")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"side": cmd_side, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
