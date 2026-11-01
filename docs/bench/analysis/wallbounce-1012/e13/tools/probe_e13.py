"""第 1 期 1-3(e13): 系ごとの指紋(1-0 の ``engine.systems.probe``)を HEAD と作業木で比べる。

両側とも進行役の境目で ``probe.snapshot``(SoA の全列・外の状態の全道筋・積算・buffers)を全部の刻みで取り、
(T, 系, 変わった欄の digest) の並びと系ごとの指紋を JSON に書く。作業木の側では 1-3 で足した物を指紋から外す:

- 状態台帳の行 ``E``(出来事の記録)の道筋=``E:events.*``(HEAD に無い)。
- ActualLog(``O61:runner.log``)の 1-3 の欄 ``event_sink``・``_event_t_ns``・``_event_seq``(目印の列。HEAD に無い)。
  ActualLog のほかの中身(固定幅の行・索引・集約)は比べる。
- 日次の記録の 1-3 の欄 ``events``(積算 ``daily_records`` と ``RunResult.daily`` の各行)。ほかの欄は比べる。

両側とも、digest の材料から物の番号(``id``)を外す(段 FIX の digest は 1 本のランの中の差し替えを見るために番号を
入れる=別のプロセスの 2 本では揃わない)。

使い方(リポの根で・``PYTHONHASHSEED=0``・``PYTHONPATH`` で src を選ぶ)::

    PYTHONPATH=<本体>/src  python $D/probe_e13.py side --label head --out $W/probe_head.json
    PYTHONPATH=<作業木>/src python $D/probe_e13.py side --label e13  --out $W/probe_e13.json
    python $D/probe_e13.py compare --a $W/probe_head.json --b $W/probe_e13.json --out $D/probe_e13.json

絶対パスは JSON に書かない。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

#: 構成(合成の世界 80 体 720 刻み・世界資産 300 体の既定 v3 と記憶+関係)。
CONFIGS = {
    "syn_mem_rel_store": dict(fn="run_day", n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0,
                              sleep_suppression=False, vocab_version="v3", memory="on", relations="on",
                              rel_copresent="on", store_memory="on", checkpoint_every=60),
    "real300_v3_default": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3"),
    "real300_v3_mem_rel": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3",
                               memory="on", relations="on"),
}
E13_ACTUAL_LOG_ATTRS = ("event_sink", "_event_t_ns", "_event_seq")


def _strip_ids(x):  # noqa: ANN001, ANN202
    """digest の材料から物の番号(``id``=プロセスごとに違うメモリの番地)を外す。"""
    if isinstance(x, tuple) and len(x) == 3 and x[0] in ("fn", "ref") and isinstance(x[2], int):
        return (x[0], x[1])
    if isinstance(x, (list, tuple)):
        return type(x)(_strip_ids(y) for y in x)
    return x


def _patch_both() -> None:
    """両側: 段 FIX の ``objs`` の digest は物の番号(id)を入れる(1 本のランの中の差し替えを見るため)。別のプロセスの
    2 本を比べるときは番号が揃わないので、番号だけを外す(型の名と中身は残す)。"""
    from shibuya.engine.systems import probe as PR

    def digest_value(v, objs=False, refs=frozenset()):  # noqa: ANN001, ANN202
        return PR._hx(repr(_strip_ids(PR.plain(v, 0, objs, refs))).encode("utf-8"))

    PR._digest_value = digest_value


def _patch_e13() -> bool:
    """作業木の側だけ: 1-3 で足した道筋と ActualLog の欄を指紋から外す(HEAD の側では何もしない)。"""
    from shibuya.engine.systems import probe as PR

    try:
        from shibuya.engine.events import log as _EV  # noqa: F401  (作業木の側の印)
    except ImportError:
        return False
    rows = [kp for kp in PR._ext_rows() if not kp[0] == "E"]
    PR._EXT_ROWS = rows
    real_plain = PR.plain

    def plain(v, depth=0, objs=False, refs=frozenset()):  # noqa: ANN001, ANN202
        if type(v).__name__ == "ActualLog" and hasattr(v, "_event_seq") and objs and depth == 0:
            d = {k: x for k, x in vars(v).items() if k not in E13_ACTUAL_LOG_ATTRS}
            return (type(v).__qualname__, real_plain(d, depth + 1, objs, refs))
        return real_plain(v, depth, objs, refs)

    PR.plain = plain

    # 日次の記録の 1-3 の欄 ``events``(積算 ``daily_records`` と ``RunResult.daily``)も外す(HEAD に無い)
    real_view_of, real_rd = PR.view_of, PR._result_digest

    def view_of(box):  # noqa: ANN001, ANN202
        v = real_view_of(box)
        t = dict(v.tally)
        if t.get("daily_records"):
            t["daily_records"] = [{k: x for k, x in r.items() if k != "events"} for r in t["daily_records"]]
        v.tally = t
        return v

    def result_digest(res):  # noqa: ANN001, ANN202
        daily = getattr(res, "daily", None)
        if not daily:
            return real_rd(res)
        res.daily = [{k: x for k, x in r.items() if k != "events"} for r in daily]
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
    patched = _patch_e13()
    out = {"label": a.label, "patched_e13": patched, "runs": {}}
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
    doc = {"schema": "shibuya.bench/e13/probe/1", "a": x["label"], "b": y["label"], "b_patched_e13": y["patched_e13"],
           "how": "1-0 の probe(全部の刻み・系ごとの全欄の差と指紋)。作業木の側は 1-3 で足した E の道筋と ActualLog の"
                  "目印の 3 欄を外した。PYTHONHASHSEED=0", "all_ok": bool(ok), "rows": rows}
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
    sp.add_argument("--only", default="")
    sp = sub.add_parser("compare")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"side": cmd_side, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
