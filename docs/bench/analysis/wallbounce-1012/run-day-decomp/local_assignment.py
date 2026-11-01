"""1-0 段 C の門: HEAD ``ee3abc7`` の ``run_day`` の局所の名前(symtable の局所・引数と内包表記の変数を含む)を全部、
状態の箱の欄か「系の中だけの一時」に割り当てる表を作る(草案 §2-3〔改訂 K8〕・漏れ 0 が門)。

割り当ての規則(上から順に当てる):

1. 手で書く表 ``BOX``(箱の欄 ``cfg.*``・``soa.*``・``layers.*``・``llm.*``・``day.*``・``buffers.*``・``scratch.*``・``stats.*``・
   ``fx.*``)。
2. 入れ子の関数・無名関数の名前 → ``FUNCS``(系のモジュールの関数か、組み立ての中に残る差し込み)。
3. 組み立て(ループの前)の中だけで書いて読む名前 → ``build``(``engine/systems/build.py`` の局所)。
4. ループの中だけで使う名前 → 書きと読みの行が 1 つの系の中だけなら ``tick:<系>``(系の関数の局所)。2 つ以上の系に
   またがるのに 1. に無ければ**漏れ**(scratch の欄に足す)。同じ名の別の一時(``i``・``k`` など)は系ごとの局所。
5. ループの後だけで使う名前 → ``end:<系>``(drain・close_final・report の局所)。

使い方(リポの根で): ``python $D/local_assignment.py <HEAD の run.py> <出力 json>``。HEAD の run.py は
``git show ee3abc7:src/shibuya/engine/run.py`` で取る。絶対パスは書かない。
"""

from __future__ import annotations

import ast
import json
import symtable
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from probe_run import BOUNDS_HEAD  # noqa: E402

#: 系の境目(HEAD の行)。ループの後は drain・close_final・report。
CFG_PARAMS = (
    "n_agents seed tick_seconds ticks fleet_wait_s checkpoint_every day_index l4_scale mode lane census_out "
    "attendance_rate exit_mode derive_rule checkpoint_detail classical_habit_p classical_tau familiarity_k "
    "intent_max_ticks leave_effect memory_n move_search_radius occupancy_every occupancy_path outside_suppression "
    "p_notice_ablation p_notice_d50_scale plan_sleep queue_service report_precondition response_delay run_id "
    "seat_area_eatery_m2 seat_area_retail_m2 signage signage_p_see sim_days sleep_suppression state_out "
    "store_recall_scope vocab_version activity_region area_source chooser eatery energy_rate geometry home_meal "
    "hunger_model hunger_words intent_mode meal_sleep_defer mock_move_target_p mock_out_of_cell_target_p near_order "
    "near_tiebreak poi_target policy role_words"
).split()
CFG_DERIVED = {
    "pop_seed": "pop_seed", "env_seed": "env_seed", "tpd": "tpd", "total_ticks": "total_ticks", "t_begin": "t_begin",
    "t_end": "t_end", "activity_on": "activity_on", "energy_on": "energy_on", "familiarity_on": "familiarity_on",
    "memory_on": "memory_on", "store_memory_on": "store_memory_on", "store_signage_on": "store_signage_on",
    "store_wom_on": "store_wom_on", "plan_exec_on": "plan_exec_on", "attention_on": "attention_on",
    "v3_hints": "v3_hints", "salt": "salt", "refractory_table": "refractory_table",
    "refractory_scale_norm": "refractory_scale_norm", "budget_mode_enum": "budget_mode_enum",
    "p_see_activity_table": "p_see_activity_table", "p_see_activity_identity": "p_see_activity_identity",
    "_call_layer": "call_layer", "_fp": "fp", "parent_run": "parent_run", "_stopped": "stopped(性質)",
}
BOX: dict[str, str] = {}
BOX.update({p: f"cfg.{p}" for p in CFG_PARAMS})
BOX.update({k: f"cfg.{v}" for k, v in CFG_DERIVED.items()})
BOX.update({"agents": "soa.agents", "world": "soa.world"})
BOX.update({
    "act_layer": "layers.act_layer", "intent_layer": "layers.intent_layer", "fam_layer": "layers.fam_layer",
    "mem_layer": "layers.mem_layer", "poi_resolver": "layers.poi_resolver", "wom_ex": "layers.wom",
    "rel_layer": "layers.rel_layer", "classical_policy": "layers.classical", "energy_layer": "layers.energy",
    "norm_meter": "layers.norm_meter", "presence": "layers.presence", "conv": "layers.conv",
    "arbiter": "layers.arbiter", "detector": "layers.detector", "runner": "layers.runner", "ledger": "layers.ledger",
    "_fam_renderer": "layers.renderer", "bridge": "layers.bridge", "fleet_bridge": "layers.fleet_bridge",
})
BOX.update({n: f"llm.{n}" for n in ("pending", "fleet_deferred", "fleet_waiting", "fleet_inflight", "replay_inbox")})
BOX.update({n: f"day.{n}" for n in ("b_agent", "b_cond", "b_tick", "b_cell", "b_start", "w17_substituted")})
BOX["focus_request"] = "buffers.focus_request"
SCRATCH = ("field_rows n_parse_errors_fleet llm_intents n_undefined applied_activity applied_now d_agent d_cond d_class "
           "e_agent e_cond e_class p_agent p_cond p_class c_agent c_cond c_class s_agent s_cond s_class f_agent f_cond "
           "f_class f_since f_exempt cands outside_now decision n_parse_errors intents plan outcome").split()
BOX.update({n: f"scratch.{n}" for n in SCRATCH})
BOX["_exp"] = "scratch.exposures"
# 名の衝突で欄の名を変えたもの(boxes.SCRATCH_FIELDS の注)
BOX.update({"d_agent": "scratch.det_agent", "d_cond": "scratch.det_cond", "d_class": "scratch.det_class",
            "n_parse_errors": "scratch.parse_errors"})
STATS = ("result phase diag_rows layer_counts leave_counts sleep_counts awake_sum awake_ticks calls_by_cond "
         "per_action_total talk_stats intero_cross occ_ticks occ_counts occ_kind occ_transit daily_records day_heads "
         "state_files frozen_sources_map leave_closed geometry_hops geometry_jammed n_fleet_reinjected n_fleet_resent "
         "n_outside_calls n_undefined_total peak_backlog peak_intents peak_pending prev_sessions prev_tape_misses "
         "t_start ledger_growth").split()  # 段 FIX(検収 §1 の 10): ledger_growth は RunStats の欄
BOX.update({n: f"stats.{n}" for n in STATS})
BOX.update({"_read_seconds": "stats.read_seconds", "_restore_seconds": "stats.restore_seconds"})
BOX.update({
    "calendar": "fx.calendar", "schedule": "fx.schedule", "schedule_hash": "fx.schedule_hash", "weekly": "fx.weekly",
    "space": "fx.space", "geom": "fx.geom", "perception": "fx.perception", "renderer_obj": "fx.renderer_obj",
    "walkable": "fx.walkable", "_env_fields": "fx.env_fields", "start_check": "fx.start_check", "fleet": "fx.fleet",
})
#: 入れ子の関数・無名関数(HEAD の名 → 1-0 の置き場)。
FUNCS: dict[str, str] = {
    "_onoff": "build:_onoff(組み立ての中の検査)",
    "_utter": "fn:engine/systems/llm_io.py:utter",
    "_receive_arrivals": "fn:engine/systems/llm_io.py:receive_arrivals",
    "_hash_owners": "fn:engine/systems/state_io.py:hash_owners",
    "_pst_now": "fn:engine/systems/state_io.py:pst_now",
    "_act_hash_now": "fn:engine/systems/state_io.py:act_hash_now",
    "_eod_hashes": "fn:engine/systems/state_io.py:eod_hashes",
    "_money_now": "fn:engine/systems/state_io.py:money_now",
    "_bodies_now": "fn:engine/systems/state_io.py:bodies_now",
    "_w17_weekday": "fn:engine/systems/state_io.py:w17_weekday",
    "_relay_tables": "fn:engine/systems/state_io.py:relay_tables",
    "_start_day": "fn:engine/systems/state_io.py:start_day",
    "_ledger_close": "fn:engine/systems/state_io.py:ledger_close",
    "_day_record": "fn:engine/systems/state_io.py:day_record",
    "_close_day_midrun": "fn:engine/systems/state_io.py:close_day_midrun",
    "_save_state": "fn:engine/systems/state_io.py:save_state",
    "_rebuild_derived": "fn:engine/systems/state_io.py:rebuild_derived",
    "_classical_acq": "build:差し込み(組み立ての中の入れ子の def のまま=捕まえる物の同一性・草案 §3-3 の 6)",
    "_classical_partner": "build:差し込み(同上)",
    "_session_partners": "build:差し込み(同上)",
    "_b3_words": "build:差し込み(同上)",
    "_revert": "tick:conversation(系の関数の中の入れ子の def)",
    "GroupNormMeter": "build:import(組み立ての中の import)",
    "role_code_table": "build:import(同上)",
    "_AWBC": "build:import(同上)",
    "_json": "end:report(報告の中の import)",
}


def main(run_py: str, out: str) -> int:
    src = Path(run_py).read_text(encoding="utf-8")
    tree = ast.parse(src)
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "run_day")
    st = symtable.symtable(src, "run.py", "exec")
    rd = next(c for c in st.get_children() if c.get_name() == "run_day")
    params = set(rd.get_parameters())
    names = sorted(s.get_name() for s in rd.get_symbols() if s.is_local())
    loop = next(n for n in fn.body if isinstance(n, ast.For) and getattr(n.target, "id", "") == "tick")
    bounds = sorted((ln, s) for s, ln in BOUNDS_HEAD)

    def system_of(ln: int) -> str:
        if ln < loop.lineno:
            return "build"
        cur = "build"
        for b, s in bounds:
            if ln >= b:
                cur = s
        if loop.lineno <= ln <= loop.end_lineno and cur in ("drain", "close_final", "report", "END"):
            cur = "day_close"
        if ln == loop.lineno or (loop.lineno < ln < bounds[0][0]):
            cur = "loop_head"
        return cur

    nested = [n for n in ast.walk(fn) if isinstance(n, (ast.FunctionDef, ast.Lambda)) and n is not fn]

    def in_nested(ln: int) -> bool:
        return any(n.lineno <= ln <= n.end_lineno for n in nested)

    sites: dict[str, list[int]] = defaultdict(list)
    for node in ast.walk(fn):
        if isinstance(node, ast.Name) and not in_nested(node.lineno):
            sites[node.id].append(node.lineno)
    rows: dict[str, dict] = {}
    unassigned: list[str] = []
    for nm in names:
        lines = sorted(set(sites.get(nm, [])))
        systems = sorted({system_of(x) for x in lines})
        row = {"param": nm in params, "systems": systems}
        if nm in BOX:
            row["to"] = "box:" + BOX[nm]
        elif nm in FUNCS:
            row["to"] = FUNCS[nm]
        elif not lines:
            row["to"] = "build:引数(組み立てで検査して捨てる)" if nm in params else "build"
        elif systems == ["build"]:
            row["to"] = "build"
        elif all(s in ("drain", "close_final", "report", "END") for s in systems):
            row["to"] = "end:" + ",".join(systems) + "(系の局所)"
        elif systems == ["loop_head"] or nm in ("tick", "td"):
            row["to"] = "ctx:T/td(進行役の TickCtx)"
        elif "build" not in systems and len([s for s in systems if s != "loop_head"]) == 1:
            row["to"] = f"tick:{systems[0]}(系の局所)"
        else:
            row["to"] = None
            unassigned.append(nm)
        rows[nm] = row
    # 同じ名の別の一時(系ごとに別の束縛=系の関数の局所に分かれる)。書きが各系の中にあることを確かめる。
    multi_ok = []
    for nm in list(unassigned):
        stores = sorted({system_of(n.lineno) for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id == nm
                         and isinstance(n.ctx, ast.Store) and not in_nested(n.lineno)})
        loads = sorted({system_of(n.lineno) for n in ast.walk(fn) if isinstance(n, ast.Name) and n.id == nm
                        and isinstance(n.ctx, ast.Load) and not in_nested(n.lineno)})
        if set(loads) <= set(stores):
            rows[nm]["to"] = "tick/end:系ごとの別の一時(" + ",".join(stores) + ")"
            unassigned.remove(nm)
            multi_ok.append(nm)
    from collections import Counter

    kinds = Counter(r["to"].split(":")[0] + (":" + r["to"].split(":")[1].split(".")[0] if r["to"].startswith("box:") else "")
                    for r in rows.values() if r["to"])
    doc = {"format": "shibuya.bench/1-0/local-assignment/1", "head": "ee3abc7", "n_locals": len(names),
           "n_params": len(params), "unassigned": unassigned, "kinds": dict(sorted(kinds.items())),
           "same_name_temporaries": multi_ok, "locals": rows}
    Path(out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("n_locals", "n_params", "unassigned", "kinds")}, ensure_ascii=False, indent=1))
    return 0 if not unassigned else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
