"""第 3 期 3-2(tm32): 系ごとの指紋(1-0 の ``engine.systems.probe``)を本体の HEAD の写しと作業木(幅の腕を含む)で比べる。

2-1 の ``ec21/tools/probe_ec21.py`` の形を写した。両側とも進行役の境目で ``probe.snapshot`` を全部の刻みで取り、(T, 系,
変わった欄の digest) の並びと系ごとの指紋を JSON に書く。作業木の側は状態台帳の行 ``BW``(3-2 で足した計算のまとめの窓=
軸 1 diag・軸 2 discardable)を指紋から外す(HEAD の写しには無い行)。行 BW を外すと、窓の境目 ``(window)`` に帰属する差は
空になり entries に載らない(=系の境目の並びと digest は HEAD と同じになるはず)。両側とも日次の記録(``daily_records``・
``RunResult.daily``)から ``bridges_count``(つなぎの台帳の active の行の数=3-2 で 4 行足した)を外す(ec21 と同じ)。両側とも digest の材料から物の番号(id)を
外す(``probe_ec21`` と同じ)。幅の腕は環境変数 ``SHIBUYA_BATCH_WIDTH_S`` で渡す(HEAD の写しは読まない)。

使い方(作業木の根で・``PYTHONHASHSEED=0``・``PYTHONPATH`` で src を選ぶ)::

    PYTHONPATH=<HEAD の写しの src> python $D/probe_tm32.py side --label head --out $W/probe_head.json
    PYTHONPATH=src                  python $D/probe_tm32.py side --label w60 --out $W/probe_w60.json
    SHIBUYA_BATCH_WIDTH_S=5 PYTHONPATH=src python $D/probe_tm32.py side --label w5 --out $W/probe_w5.json
    python $D/probe_tm32.py compare --a $W/probe_head.json --b $W/probe_w60.json --out $D/../probe_tm32_w60.json

絶対パスは JSON に書かない。
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

#: 構成(probe_ec21 と同じ 3 つ=合成の世界 80 体 720 刻み・世界資産 300 体の既定 v3 と記憶+関係)。
CONFIGS = {
    "syn_mem_rel_store": dict(fn="run_day", n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0,
                              sleep_suppression=False, vocab_version="v3", memory="on", relations="on",
                              rel_copresent="on", store_memory="on", checkpoint_every=60),
    "real300_v3_default": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3"),
    "real300_v3_mem_rel": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3",
                               memory="on", relations="on"),
}
SKIP_ROWS = frozenset({"BW"})
#: 日次の記録から外す欄(1-4 のつなぎの台帳の行の数=3-2 で台帳に 4 行を足した=作業木だけ 4 多い。ec21 と同じ外し方)。
DAILY_SKIP = frozenset({"bridges_count"})


def _strip_daily(rows):  # noqa: ANN001, ANN202
    return [{k: x for k, x in r.items() if k not in DAILY_SKIP} for r in rows]


def _strip_ids(x):  # noqa: ANN001, ANN202
    if isinstance(x, tuple) and len(x) == 3 and x[0] in ("fn", "ref") and isinstance(x[2], int):
        return (x[0], x[1])
    if isinstance(x, (list, tuple)):
        return type(x)(_strip_ids(y) for y in x)
    return x


def _patch() -> dict:
    from shibuya.engine.systems import probe as PR

    def digest_value(v, objs=False, refs=frozenset()):  # noqa: ANN001, ANN202
        return PR._hx(repr(_strip_ids(PR.plain(v, 0, objs, refs))).encode("utf-8"))

    PR._digest_value = digest_value
    rows = PR._ext_rows()
    skipped = sorted({k for k, _p in rows if k in SKIP_ROWS})
    PR._EXT_ROWS = [kp for kp in rows if kp[0] not in SKIP_ROWS]
    real_view_of = PR.view_of

    def view_of(box):  # noqa: ANN001, ANN202
        v = real_view_of(box)
        t = dict(v.tally)
        if t.get("daily_records"):
            t["daily_records"] = _strip_daily(t["daily_records"])
        v.tally = t
        return v

    real_rd = PR._result_digest

    def result_digest(res):  # noqa: ANN001, ANN202
        daily = getattr(res, "daily", None)
        if not daily:
            return real_rd(res)
        res.daily = _strip_daily(daily)
        try:
            return real_rd(res)
        finally:
            res.daily = daily

    PR.view_of, PR._result_digest = view_of, result_digest
    return {"skipped_rows": skipped, "daily_skip": sorted(DAILY_SKIP)}


def cmd_side(a: argparse.Namespace) -> int:
    import shibuya
    from shibuya import cli
    from shibuya.engine.run import run_day
    from shibuya.engine.systems import probe as PR

    meta = _patch()
    here = Path.cwd().resolve()
    src_is_worktree = Path(shibuya.__file__).resolve().is_relative_to(here / "src")
    out = {"label": a.label, "src_is_worktree": bool(src_is_worktree),
           "batch_width_env": os.environ.get("SHIBUYA_BATCH_WIDTH_S", ""), **meta, "runs": {}}
    only = [x for x in (a.only or "").split(",") if x]
    for name, kw in CONFIGS.items():
        if only and name not in only:
            continue
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
        bat = (res.run_manifest_fields().get("batching") or {}) if hasattr(res, "run_manifest_fields") else {}
        out["runs"][name] = {"final": res.final_hash[:16], "calls": int(res.llm_calls), "fp": d["fp"],
                             "n_entries": len(d["entries"]), "entries": d["entries"],
                             "width_s": bat.get("width_s"), "windows": bat.get("windows"),
                             "wall_s": round(time.perf_counter() - t0, 1)}
        print(name, res.final_hash[:16], len(d["entries"]), bat.get("width_s"), flush=True)
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
                      "width_s_b": rb.get("width_s"), "windows_b": rb.get("windows"),
                      "fp_same_all_systems": same_fp,
                      "fp_diff_systems": sorted(k for k in set(ra["fp"]) | set(rb["fp"])
                                                if ra["fp"].get(k) != rb["fp"].get(k)),
                      "first_diff": fd}
        ok &= same_fp and fd is None and ra["final"] == rb["final"]
    doc = {"schema": "shibuya.bench/tm32/probe/1", "a": x["label"], "b": y["label"],
           "a_src_is_worktree": x.get("src_is_worktree"), "b_src_is_worktree": y.get("src_is_worktree"),
           "a_batch_width_env": x.get("batch_width_env"), "b_batch_width_env": y.get("batch_width_env"),
           "a_skipped_rows": x.get("skipped_rows"), "b_skipped_rows": y.get("skipped_rows"),
           "how": "1-0 の probe(全部の刻み・系ごとの全欄の差と指紋)。作業木の側は状態台帳の行 BW(3-2 の窓)を外した"
                  "(HEAD の写しには無い行)。両側とも digest から物の番号を外し、日次の記録の bridges_count(3-2 でつなぎの"
                  "台帳に 4 行足した)を外した。PYTHONHASHSEED=0",
           "a_daily_skip": x.get("daily_skip"), "b_daily_skip": y.get("daily_skip"),
           "all_ok": bool(ok), "rows": rows}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_ok": ok, **{k: (v["fp_same_all_systems"], v["first_diff"]) for k, v in rows.items()}},
                     ensure_ascii=False))
    return 0


def main(argv=None) -> int:  # noqa: ANN001
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("side")
    sp.add_argument("--label", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--only", default="")
    sp = sub.add_parser("compare")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"side": cmd_side, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
