"""10a(A9): 応答の遅れ +1 / +2 で、艦隊の会話の流れがどう変わるかを測る(偽 vLLM・判定しない)。

使い方(リポのルートで): ``python <この置き場>/response_delay_measure.py <出力 JSON>``

偽 vLLM(``tests.llm.test_fleet.FakeVLLM``・``pair_talk``=全員が対の相手に「会話」)で、合成世界 200 体 ×
600 tick を ``response_delay`` 1 と 2 で回し、会話ターンの呼の数・発話の tick(発射からの差)・未応答の体への
再発射(``fleet_resent``)・会話の開閉を並べる。絶対パスは書かない。
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]
sys.path.insert(0, str(REPO))


def one(delay: int) -> dict:
    from shibuya.agents.state import WakeCondition
    from shibuya.engine import run as RUN
    from shibuya.engine.conversation import ConversationManager
    from shibuya.llm.fleet import FleetClient, FleetConfig
    from shibuya.manifest.schema import Mode
    from shibuya.world.state import World
    from tests.llm.test_fleet import FakeVLLM

    servers = [FakeVLLM(), FakeVLLM(), FakeVLLM()]
    for s in servers:
        s.pair_talk = True
    utt: list[tuple[int, int]] = []
    fired: list[tuple[int, int]] = []
    turn = int(WakeCondition.CONVERSATION_TURN)
    orig_u = ConversationManager.utterance
    orig_s = RUN.FleetBridge.submit

    def spy_u(self, agent_id, tick, **k):
        utt.append((int(agent_id), int(tick)))
        return orig_u(self, agent_id, tick, **k)

    def spy_s(self, batch, now_tick):
        fired.extend((int(c.agent_id), int(c.tick)) for c in batch if int(c.condition) == turn)
        return orig_s(self, batch, now_tick=now_tick)

    ConversationManager.utterance = spy_u  # type: ignore[method-assign]
    RUN.FleetBridge.submit = spy_s  # type: ignore[method-assign]
    try:
        client = FleetClient(FleetConfig(
            endpoints=tuple(s.endpoint for s in servers), model=servers[0].model, mode=Mode.SMOKE,
            run_id="10a-delay", run_seed=1, per_replica_in_flight=16, queue_capacity=256,
            ttft_timeout_s=5.0, e2e_timeout_s=8.0, connect_timeout_s=5.0, stream=False, latency_samples=1000,
        ))
        res = RUN.run_day(n_agents=200, seed=1, world=World.synthetic(n_cells=2, seed=1), ticks=600,
                          fleet=client, fleet_wait_s=10.0, renderer="stub", processes=False, population=False,
                          world_dir=None, response_delay=delay)
    finally:
        ConversationManager.utterance = orig_u  # type: ignore[method-assign]
        RUN.FleetBridge.submit = orig_s  # type: ignore[method-assign]
        for s in servers:
            s.close()
    fired_c = Counter(fired)
    lag = Counter(t - ft for (a, t) in utt for ft in [t - 1] if fired_c[(a, ft)] > 0)
    c = res.conversation_counters
    return {
        "response_delay": delay,
        "llm_calls": int(res.llm_calls),
        "conversation_turn_calls": len(fired),
        "utterances": len(utt),
        "utterance_tick_minus_fire_tick": {str(k): int(v) for k, v in sorted(lag.items())},
        "fleet_resent": float(res.bridge_counters.get("fleet_resent", 0.0)),
        "sessions_opened": int(res.conversation_sessions),
        "conv_invites": int(c.get("conv_invites", 0)),
        "conv_accepted": int(c.get("conv_accepted", 0)),
        "final": res.final_hash[:16],
    }


def main(argv: list[str]) -> int:
    out = Path(argv[1])
    doc = {"schema": "shibuya.bench/wallbounce-1003/10a/response-delay/1",
           "how": "偽 vLLM(pair_talk)・合成世界 2 セル・200 体 × 600 tick・fleet_wait_s=10・stub レンダラ・過程なし",
           "runs": [one(1), one(2)]}
    out.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    for r in doc["runs"]:
        print(r)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
