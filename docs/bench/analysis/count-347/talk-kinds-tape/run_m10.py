# -*- coding: utf-8 -*-
"""count-347 talk-kinds-tape: M10(記録 2-59)会話の後を数える運転用のスクリプト(返事その 8 §6-1 の 3)。

標準のラン(bytecheck の構成 ``w6_v3_default``=``vocab_version="v3"``・``activity=True``・mock・5,000 体・seed 1・1 日)を
1 本回し、エンジンの関数を包んで(読むだけ)次を数える。エンジンの状態には書かない。

- 会話の前の意図: 体が CONVERSING に入る直前の状態(各刻みの ``apply_responses`` の頭で、CONVERSING でない体の欄を控える)と、
  会話のセッションが終わった刻みの終わり(``activity_intent`` の後)の状態を、欄ごとに比べる。
- 会話の終わりに IDLE に戻された体の数(``resolve.end_conversation`` のうち、``ConversationManager.step`` が返した終わった
  セッションの参加者を解放する呼び出し=``runtime/systems/talk.py`` の会話の終わり)。
- IDLE に戻されてから次に判断が選ばれるまでの刻み(``arbiter`` の後の ``scratch.decision.selected``)・その起床の理由・
  終わった次の刻みの起床の候補(``wake_assemble`` の後の ``scratch.cands``)・次の観測の事実(``decide`` の後の
  ``scratch.percepts``=意図の行が出るか・直近の行動の語・B4b に自分の活動の文が出るか)。

使い方(cwd はリポの根・PYTHONPATH は読む src・PYTHONHASHSEED=0・SHIBUYA_ の環境変数なし):
    python run_m10.py --tape <テープの置き場> --out <数の JSON> --pop-out <抽出した母集団の番号の JSON>
住民の文は出さない(活動の文は体の中で同じかどうかを比べるだけ)。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from typing import Any

import numpy as np


def _pct(xs: list[int], q: float) -> float | None:
    if not xs:
        return None
    return float(np.percentile(np.asarray(xs, dtype=np.float64), q, method="lower"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--tape", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--pop-out", required=True)
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    a = ap.parse_args(argv)
    stray = sorted(k for k in os.environ if k.startswith("SHIBUYA_"))
    if stray:
        print("SHIBUYA_ の環境変数がある(構成が変わる):", stray, file=sys.stderr)
        return 2

    from shibuya import cli
    from shibuya.agents.state import INTENT_NONE, Activity, WakeCondition
    from shibuya.engine import resolve as R
    from shibuya.engine import run as ERUN
    from shibuya.act.activity import displayable_activity
    from shibuya.agents.state import ActivityKind, ResultCode
    from shibuya.foundation.vocab.actions import UntilKind
    from shibuya.runtime.systems import conductor as CD
    from shibuya.society.conversation import ConversationManager as CM

    CONV = int(Activity.CONVERSING)
    IDLE = int(Activity.IDLE)
    FIELDS = ("activity", "activity_kind", "activity_until", "target_node", "path_next_node", "intent_action",
              "intent_kind", "intent_target", "board_line", "sleep_pending", "transit_state", "plan_flags", "cell")

    S: dict[str, Any] = {"T": -1, "n": None, "session_end_flag": False}
    pre: dict[str, np.ndarray] = {}
    pre_text: list[str] = []
    conv_pre: dict[str, np.ndarray] = {}
    conv_pre_text: list[str] = []
    conv_start = None
    prev_conv = None
    ended_now: list[tuple[int, bool]] = []  # この刻みに会話の終わりで解放した (体, CONVERSING だったか)
    sessions = Counter()
    session_len: list[int] = []
    session_size = Counter()
    rec: list[dict[str, Any]] = []  # 解放した体ごとの記録(数だけ集計に使う・ファイルには数だけ出す)
    pending: dict[int, int] = {}  # 体 → rec の添字(次の判断をまだ受けていない)
    pop_capture: dict[str, Any] = {}
    conv_ref: dict[str, Any] = {}
    n_revert_calls = Counter()

    def reg_arrays(box: Any) -> dict[str, np.ndarray]:
        r = box.soa.agents.registry
        out = {}
        for f in FIELDS:
            try:
                out[f] = np.asarray(getattr(r, f))
            except AttributeError:
                pass
        return out

    def init(box: Any) -> None:
        nonlocal conv_start, prev_conv, pre_text, conv_pre_text
        n = int(box.soa.agents.n)
        S["n"] = n
        cur = reg_arrays(box)
        for f, v in cur.items():
            pre[f] = v.copy()
            conv_pre[f] = v.copy()
        txt = box.layers.act_layer.text
        pre_text = list(txt)
        conv_pre_text = list(txt)
        conv_start = np.full(n, -1, dtype=np.int64)
        prev_conv = np.zeros(n, dtype=bool)
        conv_ref["conv"] = box.layers.conv

    # ---- 包み 1: 進行役の系の呼び出し(前と後に読むだけの控え) ----
    orig_run_system = CD.run_system

    def run_system(spec: Any, ctx: Any, box: Any) -> Any:
        name = spec.name
        if ctx is not None:
            T = int(ctx.T)
            S["T"] = T
            if S["n"] is None:
                init(box)
            if name == "apply_responses":
                cur = reg_arrays(box)
                mask = cur["activity"] != CONV
                for f, v in cur.items():
                    pre[f][mask] = v[mask]
                txt = box.layers.act_layer.text
                for i in np.flatnonzero(mask).tolist():  # 体数ぶん(数える側だけ)
                    pre_text[i] = txt[i]
            elif name == "conversation":
                S["session_end_flag"] = False
                ended_now.clear()
        out = orig_run_system(spec, ctx, box)
        if ctx is None:
            return out
        T = int(ctx.T)
        if name == "conversation":
            post_conversation(box, T)
        elif name == "activity_intent":
            post_activity(box, T)
        elif name == "wake_assemble":
            post_wake_assemble(box, T)
        elif name == "arbiter":
            post_arbiter(box, T)
        elif name == "decide":
            post_decide(box, T)
        return out

    def post_conversation(box: Any, T: int) -> None:
        nonlocal prev_conv
        act = np.asarray(box.soa.agents.registry.activity)
        cur = act == CONV
        new = np.flatnonzero(cur & ~prev_conv)
        for f in conv_pre:
            conv_pre[f][new] = pre[f][new]
        for i in new.tolist():
            conv_pre_text[i] = pre_text[i]
        conv_start[new] = T
        prev_conv = cur

    # ---- 包み 2: 会話のセッションの終わり(ConversationManager.step が終わったセッションを返した後の解放だけ) ----
    orig_step = CM.step

    def step(self: Any, tick: int, **kw: Any) -> Any:
        finished = orig_step(self, tick, **kw)
        if finished:
            S["session_end_flag"] = True
            for s in finished:
                sessions[str(getattr(s, "close_reason", ""))] += 1
                ct = int(getattr(s, "closed_tick", -1))
                session_len.append((ct if ct >= 0 else int(tick)) - int(s.opened_tick))
                session_size[len(s.participants)] += 1
        return finished

    orig_end = R.end_conversation

    def end_conversation(agents: Any, agent_ids: Any) -> Any:
        ids = np.asarray(agent_ids, dtype=np.int64)
        before = np.asarray(agents.registry.activity)[ids].copy() if ids.size else np.zeros(0, dtype=np.int8)
        out = orig_end(agents, agent_ids)
        if S["session_end_flag"]:
            for i, b in zip(ids.tolist(), before.tolist()):
                ended_now.append((int(i), int(b) == CONV))
        else:
            n_revert_calls["revert_calls"] += 1
            n_revert_calls["revert_ids"] += int(ids.size)
        return out

    def post_activity(box: Any, T: int) -> None:
        if not ended_now:
            return
        cur = reg_arrays(box)
        al = box.layers.act_layer
        lrt = np.asarray(box.soa.agents.registry.last_result_tick)
        # 会話の番で出した呼の答えが、終わった時点でまだ適用を待っているか(mock の答えは次の刻みの apply_responses で適用)
        in_flight: dict[int, list[int]] = {}
        for item in list(getattr(box.llm, "pending", []) or []):
            in_flight.setdefault(int(item[2]), []).append(int(item[3]))
        for i, was_talking in ended_now:
            r: dict[str, Any] = {"agent": i, "T_end": T, "was_talking": was_talking,
                                 "conv_len": (T - int(conv_start[i])) if conv_start[i] >= 0 else None}
            for f in cur:
                r["pre_" + f] = int(conv_pre[f][i])
                r["post_" + f] = int(cur[f][i])
            r["pre_text_same_as_post"] = conv_pre_text[i] == al.text[i]
            r["pre_text_displayable"] = bool(displayable_activity(conv_pre_text[i]))
            r["post_until_kind"] = int(al.until_kind[i])
            r["lrt_end"] = int(lrt[i])
            r["in_flight_conds"] = in_flight.get(i, [])
            r["post_text_shown_id"] = int(al.text_id[i])
            r["first_cands"] = None
            r["cands_seen"] = []
            r["next"] = None
            rec.append(r)
            pending[i] = len(rec) - 1

    def post_wake_assemble(box: Any, T: int) -> None:
        if not pending:
            return
        c = box.scratch.cands
        ag = np.asarray(c.agent_id, dtype=np.int64)
        cd = np.asarray(c.condition, dtype=np.int64)
        keys = np.fromiter(pending.keys(), dtype=np.int64, count=len(pending))
        hit = np.isin(ag, keys)
        got: dict[int, list[int]] = {}
        for a_, c_ in zip(ag[hit].tolist(), cd[hit].tolist()):
            got.setdefault(int(a_), []).append(int(c_))
        for a_, k in pending.items():
            r = rec[k]
            conds = sorted(set(got.get(a_, [])))
            if T == r["T_end"] + 1:
                r["first_cands"] = conds
            r["cands_seen"] = sorted(set(r["cands_seen"]) | set(conds))

    sel_now: dict[int, int] = {}

    def post_arbiter(box: Any, T: int) -> None:
        sel_now.clear()
        if not pending:
            return
        sel = box.scratch.decision.selected
        ag = np.asarray(sel.agent_id, dtype=np.int64)
        cd = np.asarray(sel.condition, dtype=np.int64)
        for a_, c_ in zip(ag.tolist(), cd.tolist()):
            if int(a_) in pending:
                sel_now[int(a_)] = int(c_)

    def post_decide(box: Any, T: int) -> None:
        if not sel_now:
            return
        pcs = box.scratch.percepts
        al = box.layers.act_layer
        reg = box.soa.agents.registry
        rows = None
        for a_, cond in sel_now.items():
            k = pending.pop(a_)
            r = rec[k]
            p = pcs.get(a_) if pcs is not None else None
            nx: dict[str, Any] = {"T": T, "dt": T - r["T_end"], "cond": cond, "percept": p is not None}
            if p is not None:
                w = p.wake
                nx["reason"] = (int(w.reason) if not isinstance(w.reason, str) else "str")
                nx["inviter"] = w.inviter is not None and int(w.inviter) >= 0
                nx["intent_shown"] = p.intent is not None
                nx["intent_same_as_pre"] = (p.intent is not None and int(p.intent.action) == r["pre_intent_action"]
                                            and int(p.intent.target) == r["pre_intent_target"])
                nx["self_activity"] = int(p.self_view.activity)
                nx["last_action_given"] = w.last_action is not None
                nx["result_known"] = bool(w.result_known)
                nx["result"] = int(w.result)
                nx["last_action_word"] = w.last_action
            # B4b: 自分のセルの活動の行(上位 2)に自分の文が出ているか(cell_rows は読むだけ)
            live = int(np.asarray(reg.activity_until)[a_]) > T and int(al.text_id[a_]) > 0
            shown = False
            if live:
                if rows is None:
                    rows = al.cell_rows(box.soa.agents, T)
                cell = int(np.asarray(reg.cell)[a_])
                txt = al._texts[int(al.text_id[a_])]
                shown = any(t == txt for t, _n in rows.get(cell, ()))
            nx["own_text_live"] = live
            nx["own_text_in_b4b"] = shown
            nx["text_same_as_pre"] = conv_pre_text[a_] == al.text[a_]
            nx["pre_text_in_b4b"] = bool(shown and nx["text_same_as_pre"] and r["pre_text_displayable"])
            nx["target_node_same_as_pre"] = int(np.asarray(reg.target_node)[a_]) == r["pre_target_node"]
            nx["activity_now"] = int(np.asarray(reg.activity)[a_])
            nx["applied_after_end"] = int(np.asarray(reg.last_result_tick)[a_]) > r["T_end"]
            r["next"] = nx

    # ---- 包み 3: 母集団の抽出(A07 で使う番号を控える) ----
    orig_sample = ERUN.sample_population

    def sample_population(pop: Any, n: int, seed: Any) -> Any:
        out = orig_sample(pop, n, seed)
        pop_capture["source_agent_id"] = [int(x) for x in np.asarray(out.source_agent_id).tolist()]
        pop_capture["kind"] = [int(x) for x in np.asarray(out.kind).tolist()]
        pop_capture["n"] = int(n)
        pop_capture["seed"] = str(seed)
        return out

    CD.run_system = run_system
    CM.step = step
    R.end_conversation = end_conversation
    ERUN.sample_population = sample_population

    t0 = time.perf_counter()
    res = cli.run(n_agents=a.agents, seed=a.seed, world_dir=a.world, tape_path=a.tape,
                  vocab_version="v3", activity=True)
    wall = time.perf_counter() - t0

    # ---- 集計(数だけ) ----
    WN = {int(c): c.name for c in WakeCondition}
    UK = {int(u): u.name for u in UntilKind}
    AN = {int(x): x.name for x in Activity}
    talk = [r for r in rec if r["was_talking"]]
    kept = [r for r in rec if not r["was_talking"]]

    def field_keep(rs: list[dict[str, Any]], f: str, none_val: int) -> dict[str, int]:
        has = [r for r in rs if r["pre_" + f] != none_val]
        return {"pre_set": len(has),
                "post_same": sum(1 for r in has if r["post_" + f] == r["pre_" + f]),
                "post_none": sum(1 for r in has if r["post_" + f] == none_val),
                "post_other": sum(1 for r in has if r["post_" + f] not in (r["pre_" + f], none_val))}

    def summarize(rs: list[dict[str, Any]]) -> dict[str, Any]:
        nxt = [r["next"] for r in rs if r["next"] is not None]
        dts = [int(x["dt"]) for x in nxt]
        out: dict[str, Any] = {
            "n": len(rs),
            "unique_agents": len({r["agent"] for r in rs}),
            "pre_activity": dict(Counter(AN.get(r["pre_activity"], str(r["pre_activity"])) for r in rs)),
            "pre_activity_kind": dict(Counter(ActivityKind(r["pre_activity_kind"]).name for r in rs)),
            "post_activity_kind": dict(Counter(ActivityKind(r["post_activity_kind"]).name for r in rs)),
            "pre_text_displayable": sum(1 for r in rs if r["pre_text_displayable"]),
            "text_same_as_pre_and_displayable": sum(1 for r in rs if r["pre_text_same_as_post"] and r["pre_text_displayable"]),
            "post_activity": dict(Counter(AN.get(r["post_activity"], str(r["post_activity"])) for r in rs)),
            "keep_target_node": field_keep(rs, "target_node", -1),
            "keep_path_next_node": field_keep(rs, "path_next_node", -1),
            "keep_intent_action": field_keep(rs, "intent_action", INTENT_NONE),
            "keep_board_line": field_keep(rs, "board_line", -1),
            "keep_sleep_pending": field_keep(rs, "sleep_pending", 0),
            "keep_activity_kind": field_keep(rs, "activity_kind", 0),
            "keep_plan_flags_same": sum(1 for r in rs if r.get("pre_plan_flags") == r.get("post_plan_flags")),
            "activity_text_same_as_pre": sum(1 for r in rs if r["pre_text_same_as_post"]),
            "post_until_kind": dict(Counter(UK.get(r["post_until_kind"], str(r["post_until_kind"])) for r in rs)),
            "post_activity_until_live": sum(1 for r in rs if r["post_activity_until"] > r["T_end"]),
            "response_in_flight_at_end": sum(1 for r in rs if r["in_flight_conds"]),
            "response_in_flight_conds": dict(Counter(WN.get(c, str(c)) for r in rs for c in r["in_flight_conds"])),
            "post_until_minus_end": {
                "median": _pct([r["post_activity_until"] - r["T_end"] for r in rs if r["post_activity_until"] > r["T_end"]], 50),
                "p90": _pct([r["post_activity_until"] - r["T_end"] for r in rs if r["post_activity_until"] > r["T_end"]], 90),
                "max": max([r["post_activity_until"] - r["T_end"] for r in rs if r["post_activity_until"] > r["T_end"]], default=None)},
            "conv_len_ticks": {"median": _pct([r["conv_len"] for r in rs if r["conv_len"] is not None], 50),
                               "p90": _pct([r["conv_len"] for r in rs if r["conv_len"] is not None], 90),
                               "max": max([r["conv_len"] for r in rs if r["conv_len"] is not None], default=None)},
            "first_tick_after_end": {
                "with_any_candidate": sum(1 for r in rs if r["first_cands"]),
                "no_candidate": sum(1 for r in rs if r["first_cands"] == []),
                "not_observed": sum(1 for r in rs if r["first_cands"] is None),
                "conditions": dict(Counter(WN.get(c, str(c)) for r in rs for c in (r["first_cands"] or []))),
            },
            "next_decision": {
                "n_with_next": len(nxt),
                "n_without_next_by_run_end": len(rs) - len(nxt),
                "dt_ticks": {"min": min(dts, default=None), "median": _pct(dts, 50), "p90": _pct(dts, 90),
                             "max": max(dts, default=None)},
                "dt_eq_1": sum(1 for d in dts if d == 1),
                "dt_le_5": sum(1 for d in dts if d <= 5),
                "dt_le_15": sum(1 for d in dts if d <= 15),
                "dt_le_60": sum(1 for d in dts if d <= 60),
                "condition": dict(Counter(WN.get(x["cond"], str(x["cond"])) for x in nxt)),
                "percept_drawn": sum(1 for x in nxt if x["percept"]),
                "b6_inviter": sum(1 for x in nxt if x.get("inviter")),
                "b5_intent_line": sum(1 for x in nxt if x.get("intent_shown")),
                "b5_intent_same_as_pre": sum(1 for x in nxt if x.get("intent_same_as_pre")),
                "b5_self_activity": dict(Counter(AN.get(x.get("self_activity"), "none") for x in nxt if x["percept"])),
                "b6_result_known": sum(1 for x in nxt if x.get("result_known")),
                "own_activity_text_live": sum(1 for x in nxt if x["own_text_live"]),
                "own_activity_text_in_b4b": sum(1 for x in nxt if x["own_text_in_b4b"]),
                "activity_text_same_as_pre": sum(1 for x in nxt if x["text_same_as_pre"]),
                "pre_activity_text_in_b4b": sum(1 for x in nxt if x["pre_text_in_b4b"]),
                "action_applied_after_end_before_next": sum(1 for x in nxt if x["applied_after_end"]),
                "b6_last_action_word": dict(Counter(str(x.get("last_action_word")) for x in nxt if x["percept"])),
                "b6_result": dict(Counter(ResultCode(x["result"]).name for x in nxt if x["percept"])),
                "target_node_same_as_pre": sum(1 for x in nxt if x["target_node_same_as_pre"]),
                "activity_at_next": dict(Counter(AN.get(x["activity_now"], str(x["activity_now"])) for x in nxt)),
            },
        }
        return out

    conv = conv_ref.get("conv")
    doc = {
        "about": "M10 会話の後(返事その 8 §6-1 の 3)。構成 w6_v3_default・mock・5,000 体・seed 1・1 日",
        "run": {"agents": a.agents, "seed": a.seed, "world": a.world, "kw": {"vocab_version": "v3", "activity": True},
                "pythonhashseed": os.environ.get("PYTHONHASHSEED"), "wall_s": round(wall, 1),
                "llm_calls": int(getattr(res, "llm_calls", -1)),
                "ticks_seen_last": S["T"]},
        "sessions_finished": {"n": sum(sessions.values()), "close_reason": dict(sessions),
                              "size": {str(k): v for k, v in sorted(session_size.items())},
                              "len_ticks": {"median": _pct(session_len, 50), "p90": _pct(session_len, 90),
                                            "max": max(session_len, default=None)}},
        "participant_ends": len(rec),
        "participant_unique_agents": len({r["agent"] for r in rec}),
        "returned_to_idle": summarize(talk),
        "kept_other_activity": summarize(kept),
        "invite_revert_calls": dict(n_revert_calls),
        "engine_counter_n_conversation_end_kept_activity":
            (conv.defect_fix_counters().get("n_conversation_end_kept_activity") if conv is not None else None),
    }
    with open(a.out, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1, sort_keys=True)
    with open(a.pop_out, "w", encoding="utf-8") as f:
        json.dump(pop_capture, f)
    print(json.dumps({"participant_ends": len(rec), "returned_to_idle": len(talk), "wall_s": round(wall, 1)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
