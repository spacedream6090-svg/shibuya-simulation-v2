"""1-8b の記録の道具: byte-check と同じ構成(``wave2_bytecheck.configs()``・5,000 体・seed 1・1 日)を腕 on で回し、manifest の
``speech_port`` の計器と呼数・行動の件数・壁時計を出す(読むだけの記録・テープは書かない)。

使い方(リポの根で): ``SHIBUYA_SPEECH_PORT=on python docs/bench/analysis/wallbounce-1012/s8b/tools/arm_meters.py
--only w6_v3_default,v3_classical_mem_rel --out <JSON>``。腕は環境変数で選ぶ(組み立てが読む)。絶対パスは書かない。

種類ごとの数(``by_kind``): 道具の中だけで口の ``say`` と ``report_shown`` を包み、発話を「セッションの中」(``session`` ≥ 0)と
「返事」(返事待ちの招待への返事=``session`` = -1)に分けて、届け先の数(``posted``)・B6 に載った数(``delivered``)・
ランの終わりの未読(``pending``)を数える(src は変えない・記録だけ)。届かない率=1 − ``delivered`` / ``posted``
(ランの終わりの未読も「届かない」に入る)。窓の外(``expired``)はセッションの中だけ(返事は窓なし)。
"""

from __future__ import annotations

import argparse
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


def _instrument() -> dict:
    """口の ``say`` と ``report_shown`` を包んで、種類ごとの数を集める器を返す(``reset`` で次の構成へ)。"""
    from shibuya.engine.speech import port as P

    box: dict = {"kinds": {}, "by": {}}

    def reset() -> None:
        box["kinds"] = {}
        box["by"] = {k: {"posted": 0, "delivered": 0} for k in ("session", "invite")}

    orig_say, orig_rep = P.SpeechPort.say, P.SpeechPort.report_shown

    def say(self, ctx, utterance):  # noqa: ANN001
        eid = orig_say(self, ctx, utterance)
        k = "invite" if int(ctx.session) < 0 else "session"
        box["kinds"][eid] = k
        box["by"][k]["posted"] += len(utterance.addressees)
        return eid

    def report_shown(self, agent, shown, all_imperative, dropped_budget):  # noqa: ANN001
        orig_rep(self, agent, shown, all_imperative, dropped_budget)
        for e in shown:
            box["by"][box["kinds"][e]]["delivered"] += 1

    P.SpeechPort.say = say
    P.SpeechPort.report_shown = report_shown
    box["reset"] = reset
    reset()
    return box


def _by_kind(box: dict, port) -> dict:  # noqa: ANN001
    by = {k: dict(v) for k, v in box["by"].items()}
    for k in by:
        by[k]["pending"] = 0
    if port is not None:
        for q in port.inbox.values():
            for _eid, _who, _text, _t, sid in q:
                by["invite" if int(sid) < 0 else "session"]["pending"] += 1
    tot = {"posted": sum(v["posted"] for v in by.values()), "delivered": sum(v["delivered"] for v in by.values()),
           "pending": sum(v["pending"] for v in by.values())}
    by["all"] = tot
    for v in by.values():
        v["not_delivered_rate"] = round(1 - v["delivered"] / v["posted"], 4) if v["posted"] else None
    return by


def main() -> int:
    from shibuya import cli
    from shibuya.engine.speech import layer as SPL

    ap = argparse.ArgumentParser()
    ap.add_argument("--only", required=True)
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    cfgs = _configs()
    box = _instrument()
    out = {"arm": SPL.arm(), "agents": a.agents, "seed": a.seed, "runs": {}}
    for name in a.only.split(","):
        box["reset"]()
        t0 = time.perf_counter()
        res = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, **dict(cfgs[name]))
        m = res.run_manifest_fields()
        out["runs"][name] = {
            "final": res.final_hash[:16], "calls": int(res.llm_calls),
            "action_usage_total": int(sum(dict(res.action_usage).values())),
            "speech_port": m["speech_port"], "by_kind": _by_kind(box, getattr(res, "speech_layer", None)),
            "wall_s": round(time.perf_counter() - t0, 1),
        }
        print(name, json.dumps(out["runs"][name], ensure_ascii=False), flush=True)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
