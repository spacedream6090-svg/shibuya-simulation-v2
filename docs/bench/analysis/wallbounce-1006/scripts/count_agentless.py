"""領域の中の結果をエージェントの行動なしに作る処理が、既定の 1 日ランで何回動いたかを数える(読むだけ)。

使い方(リポジトリの根で):
    PYTHONIOENCODING=utf-8 .venv/Scripts/python.exe docs/bench/analysis/wallbounce-1006/scripts/count_agentless.py OUT.json

- src は変えない。書き込み口(engine.resolve の関数)と計画実行層・会話の一部のメソッドを、このスクリプトの中だけで
  包み直して「呼ばれた回数」と「対象の件数(体・店・行の数)」を数える。呼び手(関数名)ごとに分けて数える。
- ランは CLI の既定(cli.main に引数なし=5,000 体・mock・語彙 v3・空腹 energy・計画実行層あり・世界過程あり)。
  CLI の既定は何もファイルに書かない(--checkpoints-out などを渡していない)。出力は引数の JSON だけ。
- 世界過程の診断カウンタ(runner.counters)・計画実行層のカウンタ・会話の終わりの理由・RunResult の欄も一緒に書く。
"""

from __future__ import annotations

import collections
import functools
import json
import sys
import time
from pathlib import Path

import numpy as np

from shibuya import cli
from shibuya.engine import conversation as CV
from shibuya.engine import presence as PR
from shibuya.engine import resolve as R
from shibuya.engine import activity as ACT

CALLS: collections.Counter = collections.Counter()
ROWS: collections.Counter = collections.Counter()


def _size(v) -> int:
    if v is None:
        return 0
    if isinstance(v, np.ndarray):
        return int(v.size)
    if isinstance(v, (list, tuple)):
        return len(v)
    return 1


def _caller() -> str:
    f = sys._getframe(2)
    mod = f.f_globals.get("__name__", "?")
    return f"{mod.rsplit('.', 1)[-1]}.{f.f_code.co_name}"


def wrap_module(mod, name: str, idx: int | None = None, kw: str | None = None) -> None:
    orig = getattr(mod, name)

    @functools.wraps(orig)
    def w(*a, **k):
        key = f"{name} <- {_caller()}"
        CALLS[key] += 1
        if kw is not None and kw in k:
            ROWS[key] += _size(k[kw])
        elif idx is not None and len(a) > idx:
            ROWS[key] += _size(a[idx])
        return orig(*a, **k)

    setattr(mod, name, w)


def wrap_method(cls, name: str, idx: int | None = None) -> None:
    orig = getattr(cls, name)

    @functools.wraps(orig)
    def w(self, *a, **k):
        key = f"{cls.__name__}.{name} <- {_caller()}"
        CALLS[key] += 1
        if idx is not None and len(a) > idx:
            ROWS[key] += _size(a[idx])
        return orig(self, *a, **k)

    setattr(cls, name, w)


# ---- engine.resolve の書き込み口(位置引数の何番目が「対象の配列」か) ----
for _n, _i, _kw in (
    ("initialize", None, None),
    ("set_initial_activity", 1, None),
    ("initialize_energy", None, None),
    ("advance_body", None, None),
    ("begin_planned_sleep", 2, None),
    ("wake_from_plan", 1, None),
    ("energy_out_of_area_meal", 2, None),
    ("energy_home_meal", 2, None),
    ("restock", 2, None),
    ("discard_to_bin", 2, None),
    ("consume", 2, None),
    ("collect_waste", 2, None),
    ("set_thermal", None, None),
    ("set_open_flags", None, "indices"),
    ("request_open_close", 3, None),
    ("place_at_external", 1, None),
    ("rail_arrive", 2, None),
    ("rail_depart", 1, None),
    ("release_indoor", 1, None),
    ("balk_queue", 1, None),
    ("begin_exit_walk", 3, None),
    ("set_conversing", 1, None),
    ("revert_conversation", 1, None),
    ("_serve_poi_queue", None, None),
    ("_serve_board_queue", None, None),
    ("fail_intent", 1, None),
    ("clear_intent", 1, None),
):
    wrap_module(R, _n, _i, _kw)

# ---- 計画実行層(在圏の出入り) ----
for _n, _i in (("_do_arrive", 0), ("_do_depart", 0), ("_depart_now", 0), ("initialize", None)):
    wrap_method(PR.PlanExecutor, _n, _i)

# ---- 会話(終わりの理由と定型の発話) ----
_close_reason: collections.Counter = collections.Counter()
_orig_close = CV.ConversationManager._close


def _close(self, s, tick, reason):
    _close_reason[str(reason)] += 1
    return _orig_close(self, s, tick, reason)


CV.ConversationManager._close = _close
wrap_method(CV.ConversationManager, "backchannel_for", None)
wrap_method(CV.ConversationManager, "closing_utterance", None)

# ---- 活動層の「あたり」の行き先(エンジンが埋める細部) ----
wrap_method(ACT.ActivityLayer, "wander_destinations", 0)


def main(out: str) -> int:
    t0 = time.perf_counter()
    captured: dict = {}
    orig_run = cli.run

    def run_and_keep(*a, **k):
        res = orig_run(*a, **k)
        captured["res"] = res
        return res

    cli.run = run_and_keep
    rc = cli.main([])
    res = captured["res"]
    runner = getattr(res, "runner", None)
    payload = {
        "schema": "wallbounce-1006/agentless-counts/1",
        "argv": "cli.main([])  # CLI の既定",
        "n_agents": int(res.n_agents),
        "ticks": int(res.ticks),
        "wall_seconds": round(time.perf_counter() - t0, 1),
        "calls": dict(sorted(CALLS.items())),
        "rows": dict(sorted(ROWS.items())),
        "conversation_close_reason": dict(_close_reason),
        "process_counters": dict(runner.counters()) if runner is not None else {},
        "enabled_processes": sorted(runner.enabled) if runner is not None else [],
        "result": {
            "llm_calls": int(res.llm_calls),
            "n_boarded": int(res.n_boarded),
            "n_alighted": int(res.n_alighted),
            "n_queued": int(res.n_queued),
            "n_served_from_queue": int(res.n_served_from_queue),
            "n_queue_closed": int(res.n_queue_closed),
            "meals": int(res.meals),
            "fares_paid": int(res.fares_paid),
            "salient_events": int(res.salient_events),
            "dispatches": int(res.dispatches),
            "n_report_ok": int(res.n_report_ok),
            "replay_date": str(res.replay_date),
        },
        "conversation_counters": {k: v for k, v in dict(res.conversation_counters).items()
                                  if isinstance(v, (int, float))},
    }
    payload["intent"] = {k: v for k, v in dict(getattr(res, "intent", {}) or {}).items() if isinstance(v, (int, float))}
    payload["plan_executor"] = bool(getattr(res, "plan_executor", False))
    payload["presence_counters"] = {k: float(v) for k, v in dict(res.presence_counters).items()}
    payload["planned_sleep_counts"] = dict(res.planned_sleep_counts)
    payload["energy"] = {k: v for k, v in dict(res.energy).items() if isinstance(v, (int, float, str))}
    Path(out).write_text(json.dumps(payload, ensure_ascii=False, indent=1, default=str) + "\n",
                         encoding="utf-8", newline="\n")
    print(f"wrote {Path(out).name} rc={rc} wall={payload['wall_seconds']}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1]))
