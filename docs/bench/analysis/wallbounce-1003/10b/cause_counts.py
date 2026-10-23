"""10b の準備: 「原因の欄」を入れる書き口の 1 日の件数を、既存の出力から数える(書き口にカウンタは挿さない)。

使い方(リポのルートで。src は git archive HEAD の写しを先頭に置く):

    python cause_counts.py <src の根> <出力 JSON> [腕]

腕: ``default``(vocab v3+活動層=10a-prep の b56 の既定と同じ呼び方・golden 993276d5…)/
``mem_rel_store``(それに記憶・関係辺・店の記憶を ON)。mock・5,000 体・seed 1・1 シミュ日。

数える出どころ(どれも既存の出力):
- 金の台帳の生ログ ``Ledger.raw_rows()``(科目 × 支払部門 × 受取部門)と追記の総数 ``_raw_pos``・落ちた数。
- 物の台帳の配達ログ ``GoodsLedger.delivery_rows()``(科目)と ``_dl_pos``・落ちた数。
- ``RunResult.diagnostics``(tick ごとの moved・arrived・purchases・conversations・intents ほか)の合計。
- ``RunResult`` の計数(内受容の閾値越え・行動の件数・乗降・補充・配達・世界の過程の記録の行数ほか)。
- 腕が ON のときの記憶・関係辺・店の記憶の要約。
あわせて、Registry.state_hash の計算の時間を体数を変えて測る(2 つのハッシュの費用の見積り)。

絶対パスは JSON に書かない。
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

ARMS: dict[str, dict[str, Any]] = {
    "default": {"vocab_version": "v3", "activity": True},
    "mem_rel_store": {"vocab_version": "v3", "activity": True, "memory": "on",
                      "relations": "on", "store_memory": "on"},
}


def _jsonable(x: Any) -> Any:
    if isinstance(x, dict):
        return {str(k): _jsonable(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_jsonable(v) for v in x]
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, np.ndarray):
        return x.tolist()
    if isinstance(x, (int, float, str, bool)) or x is None:
        return x
    return str(x)


def hash_cost() -> dict[str, Any]:
    from shibuya.agents.state import AgentState

    out: dict[str, Any] = {}
    for label, kw in (("default", {}),
                      ("all_arms", dict(plan_columns=True, edge_columns=True, attention_columns=True,
                                        activity_columns=True, familiarity_columns=True,
                                        energy_columns=True, memory_columns=True,
                                        store_memory_columns=True, relation_columns=True))):
        for n in (5_000, 50_000):
            a = AgentState(n, **kw)
            r = a.registry
            names = [d.name for d in r.decls]
            t0 = time.perf_counter()
            for _ in range(3):
                r.state_hash()
            full = (time.perf_counter() - t0) / 3
            out[f"{label}_{n}"] = {
                "columns": len(names),
                "bytes_per_agent": int(r.actual_bytes_per_entity),
                "bytes_total": int(r.bytes_total()),
                "state_hash_s": round(full, 4),
                "ns_per_byte": round(full / max(1, r.bytes_total()) * 1e9, 3),
            }
            del a
    return out


def main(argv: list[str]) -> int:
    src = Path(argv[1])
    sys.path.insert(0, str(src))
    dst = Path(argv[2])
    arm = argv[3] if len(argv) > 3 else "default"
    import shibuya
    from shibuya import cli
    from shibuya.economy.accounts import ACCOUNT_NAMES
    from shibuya.economy.goods import GOODS_CODE_NAMES
    from shibuya.engine.run import DIAG_RUN_COLUMNS

    assert Path(shibuya.__file__).resolve().is_relative_to(src.resolve()), "HEAD の写しを読んでいない"
    t0 = time.perf_counter()
    res = cli.run(n_agents=5_000, seed=1, world_dir="data/world/v2", **ARMS[arm])
    wall = time.perf_counter() - t0

    led = res.ledger  # type: ignore[attr-defined]
    money, goods = led.money, led.goods
    raw = money.raw_rows()
    by_code: dict[str, int] = {}
    by_code_sector: dict[str, int] = {}
    for code in np.unique(raw[:, 6]) if raw.size else []:
        m = raw[:, 6] == code
        by_code[ACCOUNT_NAMES[int(code)]] = int(m.sum())
        for ps in np.unique(raw[m, 1]):
            for qs in np.unique(raw[m & (raw[:, 1] == ps), 3]):
                k = int(np.count_nonzero(m & (raw[:, 1] == ps) & (raw[:, 3] == qs)))
                by_code_sector[f"{ACCOUNT_NAMES[int(code)]}|{int(ps)}->{int(qs)}"] = k
    dl = goods.delivery_rows()
    g_by_code = {GOODS_CODE_NAMES[int(c)]: int(np.count_nonzero(dl[:, 4] == c))
                 for c in (np.unique(dl[:, 4]) if dl.size else [])}
    diag = np.asarray(res.diagnostics)
    diag_sum = {c: int(diag[:, i].sum()) for i, c in enumerate(DIAG_RUN_COLUMNS) if c != "tick"} \
        if diag.size else {}

    out = {
        "schema": "shibuya.bench/wallbounce-1003/10b-cause-counts/1",
        "arm": arm,
        "arm_kwargs": ARMS[arm],
        "agents": 5_000, "seed": 1, "ticks": int(res.ticks),
        "final_hash": res.final_hash[:16],
        "llm_calls": int(res.llm_calls),
        "wall_s_reference": round(wall, 1),
        "checkpoints": len(res.checkpoints),
        "phase_checkpoint_s": round(float(res.phase_seconds.get("checkpoint", 0.0)), 4),
        "money_ledger": {
            "appended_total": int(money._raw_pos),
            "retained": int(raw.shape[0]),
            "dropped": int(money.n_raw_dropped),
            "row_bytes": 24,
            "by_code": by_code,
            "by_code_sector": by_code_sector,
        },
        "goods_ledger": {
            "appended_total": int(goods._dl_pos),
            "retained": int(dl.shape[0]),
            "dropped": int(goods.n_delivery_dropped),
            "row_bytes": 16,
            "by_code": g_by_code,
        },
        "diagnostics_sum": diag_sum,
        "counters": {
            "intero_crossings": res.intero_crossings,
            "action_usage": res.action_usage,
            "calls_by_condition": res.calls_by_condition,
            "conversation_counters": res.conversation_counters,
            "planned_sleep_counts": res.planned_sleep_counts,
            "actual_log_rows": int(res.actual_log_rows),
            "fares_paid": int(res.fares_paid),
            "n_boarded": int(res.n_boarded), "n_alighted": int(res.n_alighted),
            "restocks": int(res.restocks), "deliveries": int(res.deliveries),
            "parcels": int(res.parcels), "dispatches": int(res.dispatches),
            "hotel_checkins": int(res.hotel_checkins), "bus_arrivals": int(res.bus_arrivals),
            "salient_events": int(res.salient_events), "noticed": int(res.noticed),
            "meals": int(res.meals),
            "move_bad_target": int(res.move_bad_target),
            "activity_counters": res.activity_counters,
            "intent": res.intent,
            "energy_keys": sorted(res.energy.keys()) if res.energy else [],
            "energy_counts": {k: v for k, v in (res.energy or {}).items()
                              if isinstance(v, (int, float)) or k in ("counts", "meals")},
            "presence_exit": res.presence_exit,
            "leave_effects": res.leave_effects,
            "process_counters": res.process_counters,
        },
        "arm_summaries": {
            "memory_summary": res.memory_summary,
            "store_memory_summary": res.store_memory_summary,
            "relations": res.relations,
            "wom": res.wom,
            "familiarity_summary": res.familiarity_summary,
        },
    }
    if arm == "default":
        out["hash_cost"] = hash_cost()
    dst.write_text(json.dumps(_jsonable(out), ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(out["final_hash"], out["llm_calls"], round(wall, 1))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
