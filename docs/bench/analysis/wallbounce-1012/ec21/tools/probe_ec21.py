"""第 2 期 2-1(ec21・検収 L5): 系ごとの指紋(1-0 の ``engine.systems.probe``)を本体の HEAD と作業木で比べる(腕 off=既定)。

1-3 の ``e13/tools/probe_e13.py`` と 1-9 の検収の形を写した。両側とも進行役の境目で ``probe.snapshot`` を全部の刻みで取り、
(T, 系, 変わった欄の digest) の並びと系ごとの指紋を JSON に書く。両側とも次を指紋から外す(無い側では何もしない):

- 状態台帳の行のうち 2-1 で足した 4 行(``EC``・``ATM``・``CR``・``EM``=腕 off は持ち主が None)と、本体の HEAD に先に入った
  1-8b の腕の行(``S8``・``S8M``)は rebase の前の比べ(作業木の土台 ``f2405e3`` に無い)だけ外した(環境変数 ``PROBE_EC21_SKIP_S8=1``)。
  行 ``E``(出来事の記録=診断)も外す(1-9 の検収と同じ)。
- 日次の記録の ``economy.conservation``(2-1 で足した保存則の検算=腕によらず)と ``bridges_count``・``rules_version``(1-4 の台帳と
  規則の表の数=作業木は台帳の行を足した・写しに表が無ければ null)・``events``。積算 ``daily_records`` と ``RunResult.daily``。
- ``RunResult.money_stage2_in``(2-1 で足した欄=腕 off は 0)。
- ActualLog の 1-3 の目印の 3 欄(1-9 の検収 L9=出来事の通し番号の並びは書き手の数で動く)。

両側とも digest の材料から物の番号(``id``)を外す(``probe_e13`` と同じ)。

使い方(作業木の根で・``PYTHONHASHSEED=0``・``PYTHONPATH`` で src を選ぶ=付けないと venv の editable install が本体の src
を読む。出力の ``src_is_worktree`` で確かめる)::

    PYTHONPATH=<HEAD の src の写し> python $D/probe_ec21.py side --label head --out $W/probe_head.json
    PYTHONPATH=src                  python $D/probe_ec21.py side --label ec21 --out $W/probe_ec21.json
    python $D/probe_ec21.py compare --a $W/probe_head.json --b $W/probe_ec21.json --out $D/../probe_ec21.json

``keys``/``keydiff``: ランの終わりの系(close_final・report・END=T が無い境目)だけ snapshot を取り、欄ごとの digest を
書いて比べる(``compare`` が最後の差を close_final に見たとき、どの欄が違うかを名指す)::

    PYTHONPATH=<HEAD の src の写し> python $D/probe_ec21.py keys --label head --out $W/keys_head.json
    PYTHONPATH=src                  python $D/probe_ec21.py keys --label ec21 --out $W/keys_ec21.json
    python $D/probe_ec21.py keydiff --a $W/keys_head.json --b $W/keys_ec21.json --out $D/../probe_ec21_keys.json

絶対パスは JSON に書かない。
"""
from __future__ import annotations

import argparse
import os
import json
import sys
import time
from pathlib import Path

#: 構成(probe_e13 と同じ 3 つ=合成の世界 80 体 720 刻み・世界資産 300 体の既定 v3 と記憶+関係)。
CONFIGS = {
    "syn_mem_rel_store": dict(fn="run_day", n_agents=80, seed=1, n_cells=9, ticks=720, budget=80.0,
                              sleep_suppression=False, vocab_version="v3", memory="on", relations="on",
                              rel_copresent="on", store_memory="on", checkpoint_every=60),
    "real300_v3_default": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3"),
    "real300_v3_mem_rel": dict(fn="cli", n_agents=300, seed=1, world_dir="data/world/v2", vocab_version="v3",
                               memory="on", relations="on"),
}
SKIP_ROWS = frozenset({"E", "EC", "ATM", "CR", "EM"} | ({"S8", "S8M"} if os.environ.get("PROBE_EC21_SKIP_S8") == "1" else set()))
ACTUAL_LOG_ATTRS = ("event_sink", "_event_t_ns", "_event_seq")
RESULT_EXTRA = ("money_stage2_in",)
#: 日次の記録から外す欄(1-3 の出来事・1-4 の台帳と規則の表の数=作業木は台帳の行を足した・写しに表が無ければ null)。
DAILY_SKIP = frozenset({"events", "bridges_count", "rules_version"})


def _strip_ids(x):  # noqa: ANN001, ANN202
    if isinstance(x, tuple) and len(x) == 3 and x[0] in ("fn", "ref") and isinstance(x[2], int):
        return (x[0], x[1])
    if isinstance(x, (list, tuple)):
        return type(x)(_strip_ids(y) for y in x)
    return x


def _strip_daily(rows):  # noqa: ANN001, ANN202
    out = []
    for r in rows:
        r = {k: x for k, x in r.items() if k not in DAILY_SKIP}
        eco = r.get("economy")
        if isinstance(eco, dict) and "conservation" in eco:
            r["economy"] = {k: x for k, x in eco.items() if k != "conservation"}
        out.append(r)
    return out


def _patch() -> dict:
    from shibuya.engine.systems import probe as PR

    def digest_value(v, objs=False, refs=frozenset()):  # noqa: ANN001, ANN202
        return PR._hx(repr(_strip_ids(PR.plain(v, 0, objs, refs))).encode("utf-8"))

    PR._digest_value = digest_value
    rows = PR._ext_rows()
    skipped = sorted({k for k, _p in rows if k in SKIP_ROWS})
    PR._EXT_ROWS = [kp for kp in rows if kp[0] not in SKIP_ROWS]
    real_plain = PR.plain

    def plain(v, depth=0, objs=False, refs=frozenset()):  # noqa: ANN001, ANN202
        if type(v).__name__ == "ActualLog" and hasattr(v, "_event_seq") and objs and depth == 0:
            d = {k: x for k, x in vars(v).items() if k not in ACTUAL_LOG_ATTRS}
            return (type(v).__qualname__, real_plain(d, depth + 1, objs, refs))
        return real_plain(v, depth, objs, refs)

    PR.plain = plain
    real_view_of = PR.view_of
    PR.RESULT_SKIP = frozenset(PR.RESULT_SKIP) | frozenset(RESULT_EXTRA)

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
    return {"skipped_rows": skipped}


def cmd_side(a: argparse.Namespace) -> int:
    import shibuya
    from shibuya import cli
    from shibuya.engine.run import run_day
    from shibuya.engine.systems import probe as PR

    meta = _patch()
    here = Path.cwd().resolve()
    src_is_worktree = Path(shibuya.__file__).resolve().is_relative_to(here / "src")
    out = {"label": a.label, "src_is_worktree": bool(src_is_worktree), **meta, "runs": {}}
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


def cmd_keys(a: argparse.Namespace) -> int:
    """ランの終わりの系の境目だけ snapshot を取り、欄ごとの digest を書く。"""
    import shibuya
    from shibuya import cli
    from shibuya.engine.run import run_day
    from shibuya.engine.systems import probe as PR

    meta = _patch()
    here = Path.cwd().resolve()
    out = {"label": a.label, "src_is_worktree": Path(shibuya.__file__).resolve().is_relative_to(here / "src"),
           **meta, "runs": {}}
    only = [x for x in (a.only or "real300_v3_default").split(",") if x]
    for name in only:
        kw = dict(CONFIGS[name])
        fn = run_day if kw.pop("fn") == "run_day" else cli.run
        snaps: list = []
        pr = PR.Probe(check=None, ticks=frozenset())
        real_point = pr.point

        def point(nm, T, view, _real=real_point, _snaps=snaps):  # noqa: ANN001, ANN202
            if T is None:
                _snaps.append((nm, PR.snapshot(view, families=pr.families)))
            return _real(nm, T, view)

        pr.point = point  # type: ignore[method-assign]
        PR.ACTIVE = pr
        try:
            res = fn(**kw)
        finally:
            PR.ACTIVE = None
        out["runs"][name] = {"final": res.final_hash[:16], "calls": int(res.llm_calls),
                             "points": [[nm, snap] for nm, snap in snaps]}
        print(name, res.final_hash[:16], [nm for nm, _s in snaps], flush=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return 0


def cmd_keydiff(a: argparse.Namespace) -> int:
    """``keys`` の 2 本を境目ごとに比べ、digest の違う欄を名指す。"""
    x = json.loads(Path(a.a).read_text(encoding="utf-8"))
    y = json.loads(Path(a.b).read_text(encoding="utf-8"))
    rows = {}
    for name in x["runs"]:
        pa, pb = x["runs"][name]["points"], y["runs"][name]["points"]
        per = []
        for (na, sa), (nb, sb) in zip(pa, pb):
            keys = sorted(k for k in set(sa) | set(sb) if sa.get(k) != sb.get(k))
            per.append({"point_a": na, "point_b": nb, "diff_keys": keys})
        rows[name] = {"final_a": x["runs"][name]["final"], "final_b": y["runs"][name]["final"],
                      "n_points": [len(pa), len(pb)], "points": per}
    doc = {"schema": "shibuya.bench/ec21/probe-keys/1", "a": x["label"], "b": y["label"],
           "a_src_is_worktree": x.get("src_is_worktree"), "b_src_is_worktree": y.get("src_is_worktree"),
           "how": "ランの終わりの系の境目(T が無い)ごとの snapshot の欄ごとの digest を比べた(外す欄は side と同じ)",
           "rows": rows}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rows, ensure_ascii=False)[:3000])
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
                      "fp_same_all_systems": same_fp,
                      "fp_diff_systems": sorted(k for k in set(ra["fp"]) | set(rb["fp"])
                                                if ra["fp"].get(k) != rb["fp"].get(k)),
                      "first_diff": fd}
        ok &= same_fp and fd is None and ra["final"] == rb["final"]
    doc = {"schema": "shibuya.bench/ec21/probe/1", "a": x["label"], "b": y["label"],
           "a_src_is_worktree": x.get("src_is_worktree"), "b_src_is_worktree": y.get("src_is_worktree"),
           "a_skipped_rows": x.get("skipped_rows"), "b_skipped_rows": y.get("skipped_rows"),
           "how": "1-0 の probe(全部の刻み・系ごとの全欄の差と指紋)。両側とも状態台帳の行 E・EC・ATM・CR・EM(rebase の前は S8・S8M も)・"
                  "日次の economy.conservation・bridges_count・rules_version・events・RunResult.money_stage2_in・ActualLog の目印の 3 欄を外した。PYTHONHASHSEED=0",
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
    sp = sub.add_parser("keys")
    sp.add_argument("--label", required=True)
    sp.add_argument("--out", required=True)
    sp.add_argument("--only", default="")
    for nm in ("compare", "keydiff"):
        sp = sub.add_parser(nm)
        sp.add_argument("--a", required=True)
        sp.add_argument("--b", required=True)
        sp.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"side": cmd_side, "keys": cmd_keys, "compare": cmd_compare, "keydiff": cmd_keydiff}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
