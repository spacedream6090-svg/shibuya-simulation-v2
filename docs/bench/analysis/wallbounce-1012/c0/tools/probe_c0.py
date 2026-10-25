"""第 1 期 1-7(c0): 系ごとの指紋(1-0 の ``engine.systems.probe``)を HEAD と作業木で比べる(作業用の道具)。

``p12/tools/probe_p12.py`` の写しを 1-7 に合わせて直した物。両側とも進行役の境目で ``probe.snapshot``(SoA の全列・
外の状態の全道筋・積算・buffers。scratch は入れない=既定の族)を全部の刻みで取り、(T, 系, 変わった欄の digest) の並びと
系ごとの指紋を JSON に書く。両側とも digest の材料から物の番号(``id``)を外す(別のプロセスの 2 本では番地が揃わない)。

1-7 で足した物を**作業木の側だけ**外す(HEAD には無い):

- 状態台帳の行 ``CT5`` の道筋 ``rel_layer._contact_flags``(連絡先の印=検収 L1 の後の名・前は ``rel_layer.contact_flags``)
- ``RunResult.tools``(manifest の ``tools`` の中身=report が書く)

使い方(リポの根で・``PYTHONHASHSEED=0``・``PYTHONPATH`` で src を選ぶ)::

    PYTHONPATH=<HEAD の写し>/src python $D/probe_c0.py side --label head --out $W/probe_head.json
    PYTHONPATH=src               python $D/probe_c0.py side --label c0   --out $W/probe_c0.json
    PYTHONPATH=src               python $D/probe_c0.py side --label c0l  --out $W/probe_c0l.json         --ledger <HEAD の写し>/docs/design/bridging-ledger.json     # 台帳だけ HEAD のものを読ませる
    python $D/probe_c0.py compare --a $W/probe_head.json --b $W/probe_c0.json --out $D/../probe_c0.json

絶対パスは JSON に書かない。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

#: 構成(e13・p12 と同じ: 合成の世界 80 体 720 刻み・世界資産 300 体の既定 v3 と記憶+関係)。
CONFIGS = {
    "syn_mem_rel_store": dict(fn="run_day", n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0,
                              sleep_suppression=False, vocab_version="v3", memory="on", relations="on",
                              rel_copresent="on", store_memory="on", checkpoint_every=60),
    "real300_v3_default": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3"),
    "real300_v3_mem_rel": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3",
                               memory="on", relations="on"),
}
#: 作業木の側だけで外す道筋(1-7 で足した行)と RunResult の欄。
DROP_PATHS = (("CT5", "rel_layer._contact_flags"),)
DROP_RESULT = ("tools",)


def _strip_ids(x):  # noqa: ANN001, ANN202
    if isinstance(x, tuple) and len(x) == 3 and x[0] in ("fn", "ref") and isinstance(x[2], int):
        return (x[0], x[1])
    if isinstance(x, (list, tuple)):
        return type(x)(_strip_ids(y) for y in x)
    return x


def _patch() -> list:
    from shibuya.engine.systems import probe as PR

    def digest_value(v, objs=False, refs=frozenset()):  # noqa: ANN001, ANN202
        return PR._hx(repr(_strip_ids(PR.plain(v, 0, objs, refs))).encode("utf-8"))

    PR._digest_value = digest_value
    rows = PR._ext_rows()
    dropped = [kp for kp in rows if kp in DROP_PATHS]
    PR._EXT_ROWS = [kp for kp in rows if kp not in DROP_PATHS]
    PR.RESULT_SKIP = frozenset(PR.RESULT_SKIP | set(DROP_RESULT))
    return [":".join(kp) for kp in dropped]


def cmd_side(a: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine.run import run_day
    from shibuya.engine.systems import probe as PR

    dropped = _patch()
    if a.ledger:
        # つなぎの台帳を別の道筋から読む(作業木の側で HEAD の台帳を読ませ、bridges_count/bridges_version の差を消す)
        from shibuya.engine.bridging import ledger as BR

        led = Path(a.ledger).resolve()
        BR.default_path = lambda: led  # type: ignore[assignment]
        BR.default_ledger.cache_clear()
    try:
        from shibuya.engine.tools import registry as _R  # noqa: F401  (作業木の側の印)
        is_c0 = True
    except ImportError:
        is_c0 = False
    out = {"label": a.label, "is_c0": is_c0, "dropped": dropped, "ledger_override": bool(a.ledger), "runs": {}}
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
    doc = {"schema": "shibuya.bench/c0/probe/1", "a": x["label"], "b": y["label"], "b_is_c0": y["is_c0"],
           "b_ledger_override": y.get("ledger_override", False),
           "dropped_b_side": y["dropped"] + [f"RunResult.{k}" for k in DROP_RESULT],
           "how": "1-0 の probe(全部の刻み・系ごとの全欄の差と指紋・scratch は入れない)。作業木の側だけ 1-7 で足した "
                  "状態台帳の行 CT5(rel_layer.contact_flags)と RunResult.tools を外した。PYTHONHASHSEED=0",
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
    sp.add_argument("--only", default="")
    sp.add_argument("--ledger", default="", help="つなぎの台帳の道筋(既定はリポの台帳)")
    sp = sub.add_parser("compare")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"side": cmd_side, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
