"""第 1 期 1-2(p12): 系ごとの指紋(1-0 の ``engine.systems.probe``)を HEAD と作業木で比べる(作業用の道具)。

``e13/tools/probe_e13.py`` の写しを 1-2 に合わせて直した物。両側とも進行役の境目で ``probe.snapshot``(SoA の全列・
外の状態の全道筋・積算・buffers。scratch は入れない=既定の族)を全部の刻みで取り、(T, 系, 変わった欄の digest) の並びと
系ごとの指紋を JSON に書く。

1-2 で中身の形を変えた描画のキャッシュ(状態台帳の O63=``derivable``・full-hash でも中身を入れない ``hash_skip`` の道筋)
の 2 本を、**両側とも**指紋から外す:

- ``renderer._tickc``(刻みの前計算。1-2 で時刻の見方の材料と、その場・時刻の見方・B3 の文の刻みの中のキャッシュの欄を足した)
- ``renderer._b3_cache``(B3 の鍵 → 1-2 の前は描いた文・1-2 では天候・日照・暑さの語)

ほかの道筋(描画の計数 O84・口 O64 を含む)はそのまま比べる。両側とも digest の材料から物の番号(``id``)を外す
(別のプロセスの 2 本では番地が揃わない)。

使い方(リポの根で・``PYTHONHASHSEED=0``・``PYTHONPATH`` で src を選ぶ)::

    PYTHONPATH=<HEAD の写し>/src python $D/probe_p12.py side --label head --out $W/probe_head.json
    PYTHONPATH=src               python $D/probe_p12.py side --label p12  --out $W/probe_p12.json
    python $D/probe_p12.py compare --a $W/probe_head.json --b $W/probe_p12.json --out $D/../probe_p12.json

絶対パスは JSON に書かない。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

#: 構成(e13 と同じ: 合成の世界 80 体 720 刻み・世界資産 300 体の既定 v3 と記憶+関係)。
CONFIGS = {
    "syn_mem_rel_store": dict(fn="run_day", n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0,
                              sleep_suppression=False, vocab_version="v3", memory="on", relations="on",
                              rel_copresent="on", store_memory="on", checkpoint_every=60),
    "real300_v3_default": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3"),
    "real300_v3_mem_rel": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3",
                               memory="on", relations="on"),
}
#: 両側で外す道筋(状態台帳の O63 の中の 2 本)。
DROP_PATHS = (("O63", "renderer._tickc"), ("O63", "renderer._b3_cache"))


def _strip_ids(x):  # noqa: ANN001, ANN202
    """digest の材料から物の番号(``id``=プロセスごとに違うメモリの番地)を外す。"""
    if isinstance(x, tuple) and len(x) == 3 and x[0] in ("fn", "ref") and isinstance(x[2], int):
        return (x[0], x[1])
    if isinstance(x, (list, tuple)):
        return type(x)(_strip_ids(y) for y in x)
    return x


def _patch_both() -> list:
    """両側: 物の番号を外し、O63 の 2 本を指紋から外す。外した道筋を返す(記録に出す)。"""
    from shibuya.engine.systems import probe as PR

    def digest_value(v, objs=False, refs=frozenset()):  # noqa: ANN001, ANN202
        return PR._hx(repr(_strip_ids(PR.plain(v, 0, objs, refs))).encode("utf-8"))

    PR._digest_value = digest_value
    rows = PR._ext_rows()
    dropped = [kp for kp in rows if kp in DROP_PATHS]
    PR._EXT_ROWS = [kp for kp in rows if kp not in DROP_PATHS]
    return [":".join(kp) for kp in dropped]


def cmd_side(a: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine.run import run_day
    from shibuya.engine.systems import probe as PR

    dropped = _patch_both()
    try:
        from shibuya.perception import facts as _F  # noqa: F401  (作業木の側の印)
        is_p12 = True
    except ImportError:
        is_p12 = False
    out = {"label": a.label, "is_p12": is_p12, "dropped": dropped, "runs": {}}
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
    doc = {"schema": "shibuya.bench/p12/probe/1", "a": x["label"], "b": y["label"], "b_is_p12": y["is_p12"],
           "dropped_both_sides": x["dropped"],
           "how": "1-0 の probe(全部の刻み・系ごとの全欄の差と指紋・scratch は入れない)。両側とも状態台帳 O63 の "
                  "renderer._tickc と renderer._b3_cache(描画のキャッシュ=1-2 で中身の形を変えた)を外した。PYTHONHASHSEED=0",
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
    sp = sub.add_parser("compare")
    sp.add_argument("--a", required=True)
    sp.add_argument("--b", required=True)
    sp.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"side": cmd_side, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
