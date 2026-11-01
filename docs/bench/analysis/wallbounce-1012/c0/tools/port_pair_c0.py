"""第 1 期 1-7 の 1-8 への結線: 腕 port で、結線の前(HEAD の src)と後(作業木の src)の候補の列・選んだ番号・適用した
行為のコードの並びと final を比べる。

``side`` は 1 つの src で(``PYTHONPATH`` で選ぶ)構成ごとに 1 本回し、判断ごとに (刻み・体・候補の (id, 源) の列)・
(刻み・体・提示の番号・選んだ候補の id・その他か)・(刻み・体・適用したコード)を集めて sha256 にし、final・呼数・manifest の
``decision_port`` の観測の子と一緒に JSON に書く。``compare`` は 2 つの side を比べる。構成は byte-check と同じ表
(``wave2_bytecheck.configs``・mock/古典 5,000 体・seed 1・1 シミュ日・世界資産・テープなし)。

使い方(リポの根で)::

    PYTHONPATH=<HEAD の写し>/src python $D/port_pair_c0.py side --label head --out $W/pp_head.json w6_v3_default v3_mem_rel
    PYTHONPATH=src               python $D/port_pair_c0.py side --label c0   --out $W/pp_c0.json   w6_v3_default v3_mem_rel
    python $D/port_pair_c0.py compare --a $W/pp_head.json --b $W/pp_c0.json --out <記録>

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
WAVE2 = REPO / "docs" / "bench" / "analysis" / "wave2-2026-09-30" / "wave2_bytecheck.py"


def _configs() -> dict:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod.configs()


class _Sha:
    def __init__(self) -> None:
        self.h = hashlib.sha256()
        self.n = 0

    def add(self, row: tuple) -> None:
        self.h.update(repr(row).encode("utf-8"))
        self.n += 1

    def out(self) -> dict:
        return {"rows": self.n, "sha": self.h.hexdigest()[:16]}


def one(name: str, kw: dict) -> dict:
    from shibuya import cli
    from shibuya.engine.decision import layer as DL
    from shibuya.engine.decision import port as PT

    cands, chosen, applied = _Sha(), _Sha(), _Sha()
    real_build, real_choose, real_dec = DL.build_candidates, PT.DecisionPort.choose, DL.DecisionLayer.decide_one

    def build(ctx, **k):  # noqa: ANN001, ANN202
        cs = real_build(ctx, **k)
        cands.add((int(ctx.step), int(ctx.agent_id), tuple((c.id, c.source) for c in cs)))
        return cs

    def choose(self, ctx, cs):  # noqa: ANN001, ANN202
        ch = real_choose(self, ctx, cs)
        chosen.add((int(ctx.step), int(ctx.agent_id), int(ch.number), str(ch.candidate_id), bool(ch.is_other)))
        return ch

    def dec(self, bridge, agent_id, step, *a, **k):  # noqa: ANN001, ANN202
        res, p = real_dec(self, bridge, agent_id, step, *a, **k)
        applied.add((int(step), int(agent_id), int(res.action_code)))
        return res, p

    DL.build_candidates = build
    PT.DecisionPort.choose = choose
    DL.DecisionLayer.decide_one = dec
    prev = DL.arm()
    DL.set_arm(DL.ARM_PORT)
    t0 = time.perf_counter()
    try:
        res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", **kw)
    finally:
        DL.set_arm(prev)
        DL.build_candidates, PT.DecisionPort.choose, DL.DecisionLayer.decide_one = real_build, real_choose, real_dec
    m = res.run_manifest_fields()["decision_port"]
    return {"config": name, "final": res.final_hash[:16], "calls": int(res.llm_calls), "candidates": cands.out(),
            "chosen": chosen.out(), "applied": applied.out(),
            "decision_port": {k: m.get(k) for k in ("arm", "port", "decisions", "late", "presented_by_source",
                                                     "chosen_by_source", "chosen_number", "n_candidates", "mismatch",
                                                     "other")},
            "has_tools_module": importlib.util.find_spec("shibuya.engine.tools") is not None,
            "wall_seconds_nondeterministic": round(time.perf_counter() - t0, 1)}


def cmd_side(a: argparse.Namespace) -> int:
    conf = _configs()
    out = {"label": a.label, "runs": {}}
    for name in a.configs:
        row = one(name, dict(conf[name]))
        out["runs"][name] = row
        print(name, row["final"], row["calls"], row["candidates"], row["chosen"], flush=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def cmd_compare(a: argparse.Namespace) -> int:
    x = json.loads(Path(a.a).read_text(encoding="utf-8"))
    y = json.loads(Path(a.b).read_text(encoding="utf-8"))
    rows, ok = {}, True
    keys = ("final", "calls", "candidates", "chosen", "applied", "decision_port")
    for name, ra in x["runs"].items():
        rb = y["runs"][name]
        same = [k for k in keys if ra[k] == rb[k]]
        moved = {k: {"a": ra[k], "b": rb[k]} for k in keys if ra[k] != rb[k]}
        rows[name] = {"same": same, "moved": moved, "a_has_tools": ra["has_tools_module"],
                      "b_has_tools": rb["has_tools_module"], "decisions": rb["decision_port"]["decisions"],
                      "candidates": rb["candidates"], "chosen": rb["chosen"], "applied": rb["applied"]}
        ok &= not moved
    doc = {"schema": "shibuya.bench/c0/port-pair/1", "a": x["label"], "b": y["label"], "all_same": bool(ok),
           "how": "腕 port・5,000 体・seed 1・1 日・世界資産。判断ごとの候補の (id, 源) の列・提示の番号と選んだ id・適用したコードの"
                  "並びの sha と final・呼数・manifest の decision_port の観測の子を比べる",
           "rows": rows}
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"all_same": ok, **{k: sorted(v["moved"]) for k, v in rows.items()}}, ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("side")
    s.add_argument("--label", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("configs", nargs="+")
    c = sub.add_parser("compare")
    c.add_argument("--a", required=True)
    c.add_argument("--b", required=True)
    c.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"side": cmd_side, "compare": cmd_compare}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
