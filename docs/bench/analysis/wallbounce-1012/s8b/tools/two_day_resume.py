"""1-8b の記録の道具: 世界資産の 2 日のラン(通し)と、途中で止めて状態を書き再開したランを比べる(読むだけの記録)。

使い方(リポの根で・腕は環境変数 ``SHIBUYA_SPEECH_PORT`` で選ぶ・``--src`` で読む src を替えるときは ``PYTHONPATH`` を渡す):

    python docs/bench/analysis/wallbounce-1012/s8b/tools/two_day_resume.py straight --agents 2000 --out <JSON>
    python docs/bench/analysis/wallbounce-1012/s8b/tools/two_day_resume.py resume --agents 2000 --stop 2100 \\
        --scratch <作業用> --out <JSON>
    python docs/bench/analysis/wallbounce-1012/s8b/tools/two_day_resume.py compare --a <JSON> --b <JSON> --out <JSON>

``straight``=通し(final・checkpoint の 2 本・締めの後の 2 本・呼数・発話の計器)。``resume``=``--stop`` の刻みで止めて状態を
書き、そのファイルから再開(止めたランと再開のランの値・状態のファイルの末尾の道筋と未読の数・見出しの指紋の腕)。構成は
byte-check と同じ ``w6_v3_default``(``wave2_bytecheck.configs()``)の 2 日。絶対パスは書かない。
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


def _cfg(name: str) -> dict:
    spec = importlib.util.spec_from_file_location("wave2_bytecheck", WAVE2)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["wave2_bytecheck"] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return dict(mod.configs()[name])


def _summary(res) -> dict:
    m = res.run_manifest_fields()
    sp = m.get("speech_port") or {}
    return {
        "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "checkpoints": [(int(c.tick), c.behavior_hash[:16], c.full_hash[:16]) for c in res.checkpoints],
        "end_of_day": {str(k): v for k, v in dict(getattr(res, "state_hashes_end_of_day", {}) or {}).items()},
        "speech": {k: sp.get(k) for k in ("arm", "said", "to_inviter", "delivered", "expired", "overflow",
                                         "all_imperative", "dropped_budget", "pending")},
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=("straight", "resume", "compare"))
    ap.add_argument("--agents", type=int, default=2_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--config", default="w6_v3_default")
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--stop", type=int, default=2100)
    ap.add_argument("--scratch", default="")
    ap.add_argument("--a", default="")
    ap.add_argument("--b", default="")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "compare":
        x = json.loads(Path(a.a).read_text(encoding="utf-8"))
        y = json.loads(Path(a.b).read_text(encoding="utf-8"))
        sx, sy = x["run"], y["run"]
        cps_y = {c[0] for c in sy["checkpoints"]}
        out = {"a": x["label"], "b": y["label"], "final_same": sx["final"] == sy["final"],
               "calls_a": sx["calls"], "calls_b": sy["calls"],
               "checkpoints_same": [c for c in sx["checkpoints"] if c[0] in cps_y] == sy["checkpoints"],
               "end_of_day_same": sx["end_of_day"] == sy["end_of_day"],
               "final_a": sx["final"], "final_b": sy["final"]}
        Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
        print(json.dumps(out, ensure_ascii=False))
        return 0
    import shibuya
    from shibuya import cli
    from shibuya.engine import resume as RS

    try:  # 1-8b の前の src(本体 HEAD の写し)には発話の口が無い=腕は「無し」
        from shibuya.engine.speech import layer as SPL

        arm = SPL.arm()
    except ImportError:
        arm = "(無し)"
    kw = _cfg(a.config)
    kw.update(sim_days=2, ticks=1440, checkpoint_every=360)
    src_is_worktree = Path(shibuya.__file__).resolve().parents[1] == (REPO / "src").resolve()
    doc: dict = {"label": f"{a.cmd}:{arm}", "config": a.config, "agents": a.agents, "seed": a.seed,
                 "src_is_worktree": src_is_worktree, "arm": arm}
    t0 = time.perf_counter()
    if a.cmd == "straight":
        doc["run"] = _summary(cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, **kw))
    else:
        st = Path(a.scratch)
        st.mkdir(parents=True, exist_ok=True)
        first = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, state_out=str(st), stop_at_tick=a.stop,
                        **kw)
        path = RS.state_path(st, a.stop)
        bundle = RS.read_state(path)
        items = list(bundle.items)
        doc["stopped"] = _summary(first)
        doc["state_file"] = {"next_T": bundle.header["progress"]["next_T"], "tail": items[-2:],
                             "unread": (sum(len(v) for v in bundle.items["speech.inbox"].values())
                                        if "speech.inbox" in bundle.items else None),
                             "fingerprint_speech_port": bundle.header["fingerprint"].get("speech_port")}
        doc["resumed"] = _summary(cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world,
                                          resume_from=str(path), **kw))
        doc["run"] = doc["resumed"]
    doc["wall_s"] = round(time.perf_counter() - t0, 1)
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: v for k, v in doc.items() if k != "run"}, ensure_ascii=False)[:2000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
