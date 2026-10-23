"""第 2 波 §2A 項 3-1 の検収後の直し(話しかけられない知人を候補から除く)の前後の値(計測だけ・判定しない)。

使い方(リポのルートで): ``python $D/social_measure.py --out $D/item3_social.json``

構成: classical・v3・energy・記憶 on・関係 on・5,000 体・seed 1・1 シミュ日。「直しの前」は
``engine.run.classical_acq_addressable`` を恒等(A をそのまま返す)に差し替えて再現する(このプロセスの中だけ)。
加えて関係 off の classical(既定 acquaintance と旧 near_first)で、会話の返事の件数を控える。
量: 符号 18 の件数・知人を選んだ件数と選んだ時点の相手の状態・会話ターンの返事(reply_talk)・会話の開始と結果
(``conversation_counters``)・final・呼数。壁時計は JSON に入れない。
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def one(label: str, patch_before: bool, **extra: Any) -> dict[str, Any]:
    from shibuya import cli
    from shibuya.agents.state import Activity
    from shibuya.engine import classical as CL
    from shibuya.engine import run as RUN

    orig_filter = RUN.classical_acq_addressable
    orig_best = CL.ClassicalPolicy._best_acquaintance
    states: Counter = Counter()

    def best(self: Any, aid: int, prompt: str) -> int:
        pid = orig_best(self, aid, prompt)
        if pid >= 0:
            states[Activity(int(self.agents.registry.activity[pid])).name] += 1
        return pid

    CL.ClassicalPolicy._best_acquaintance = best  # type: ignore[method-assign]
    if patch_before:
        RUN.classical_acq_addressable = lambda agents, aid, ids, A, *, by_distance: A  # type: ignore[assignment]
    try:
        kw = dict(n_agents=5000, seed=1, world_dir="data/world/v2", vocab_version="v3", policy="classical",
                  chooser="classical")
        kw.update(extra)
        res = cli.run(**kw)
    finally:
        RUN.classical_acq_addressable = orig_filter  # type: ignore[assignment]
        CL.ClassicalPolicy._best_acquaintance = orig_best  # type: ignore[method-assign]
    c = res.run_manifest_fields()["classical"]["counts"]
    return {"label": label, "args": {k: v for k, v in extra.items()}, "final": res.final_hash[:16],
            "calls": int(res.llm_calls), "activity_18": int(c.get("activity:18", 0)),
            "talk_acquaintance": int(c.get("talk_acquaintance", 0)),
            "talk_no_acquaintance": int(c.get("talk_no_acquaintance", 0)),
            "reply_talk": int(c.get("reply_talk", 0)),
            "chosen_partner_state_at_choice": dict(states),
            "conversations_opened": int(res.column("conversations_opened").sum()) if res.diagnostics.size else 0,
            "conversation_sessions": int(res.conversation_sessions),
            "conversation_counters": dict(res.conversation_counters)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    rows = [
        one("rel_on_before_fix", True, memory="on", relations="on"),
        one("rel_on_after_fix", False, memory="on", relations="on"),
        one("rel_on_near_first", False, memory="on", relations="on", classical_social="near_first"),
        one("rel_off_acquaintance", False),
        one("rel_off_near_first", False, classical_social="near_first"),
    ]
    for r in rows:
        print(json.dumps({k: r[k] for k in ("label", "final", "calls", "activity_18", "talk_acquaintance",
                                            "reply_talk", "chosen_partner_state_at_choice",
                                            "conversation_sessions")}, ensure_ascii=False), flush=True)
    doc = {"schema": "shibuya.bench/wave2-2026-09-30/classical-social/1",
           "how": "classical 5,000 体・seed 1・v3・energy・1 シミュ日。直しの前=除外の関数を恒等に差し替え。判定しない",
           "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, default=str) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
