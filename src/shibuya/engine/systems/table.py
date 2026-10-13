"""engine.systems.table — 系の宣言の表 ``SYSTEMS``(呼ぶ順の 1 つの表)(第 1 期 1-0・草案 §2-2・§2-5)。

- 並び=呼ぶ順(ランの頭 → 日の頭 → tick の中 25 → 日の終わり → ランの終わり)。進行役はこの順にしか呼ばない。
  ``llm_receive`` は 1 つの系で、位置が 2 つ(``response_delay=1`` は ``perceive_prepare`` の後・``2`` は ``wake_sources`` の後)。
  表には 1 回だけ載せ、進行役が設定で位置を選ぶ(草案 §2-2)。
- ``writes.soa`` は ``resolve_ops`` の静的な閉包(``spec.make``・手で書かない)。``resolve_ops``・``writes.paths``・
  scratch・tally は手で書く表(下書き: 6 構成の観測・HEAD の系ごとの差の測り・層のメソッドの静的な到達)。
- 外の道筋は ``鍵:道筋``(末尾の ``*`` で前方一致・``[...]`` で行の範囲)。行は割らない(草案 §0-2)。
- 群は名札(体・世界・知覚・判断・会話・行為の解決・記憶・計器・暦・組み立て)。話題ごとのまとめ直しは T1 の後。

〔親の決め〕世界過程が持ち主をまたいで書く所(鉄道と大きな催しが計画実行層の O36・O37・O70 と鉄道の O74 を書く)は
1-0 では宣言で認める(``world`` の ``writes.paths``)。

逐次ループ宣言: なし(表を作るのは起動時に 1 回)。
"""

from __future__ import annotations

from shibuya.engine.systems import observe as _OB
from shibuya.engine.systems import report as _RP
from shibuya.engine.systems.spec import SystemSpec, make

__all__ = ["SYSTEMS", "SPECS", "TICK_ORDER"]

_E = "ee3abc7"


SYSTEMS: tuple[SystemSpec, ...] = (
    # ================================================================ ランの頭
    make("build", "組み立て", "run_head", None,
         resolve_ops="initialize initialize_energy set_initial_activity restore_soa restore_items place_at_external "
                     "rail_arrive set_plan_state write_relations",
         origin=f"S0〜S8・run.py:2372-3604 @{_E}"),
    # ================================================================ 日の頭
    make("day_head", "暦", "day_head", None,
         resolve_ops="set_plan_state",
         paths="O3[5-8]:presence.* O70:presence.* O4[6-9]:runner.* O5[0-6]:runner.* O61:runner.* O7[3-6]:runner.* "
               "O95:runner.*",
         tally="day_heads", origin=f"L0・run.py:3607-3609 @{_E}"),
    # ================================================================ tick の中(25)
    make("body", "体", "tick", None,
         resolve_ops="advance_body energy_out_of_area_meal",
         paths="O2[7-9]:energy.* O3[0-3]:energy.* O21:classical.*",
         origin=f"L1・run.py:3610-3624 @{_E}"),
    make("world", "世界", "tick", None,
         resolve_ops="rail_arrive rail_depart sync_transit_activity balk_queue release_indoor set_thermal "
                     "collect_waste consume discard_to_bin restock request_open_close set_open_flags set_notice_state "
                     "set_plan_state",
         paths="O3[5-7]:presence.* O70:presence.* O4[6-9]:runner.* O5[0-6]:runner.* O61:runner.* O7[2-6]:runner.* "
               "O95:runner.* O5[7-9]:ledger.* O60:ledger.* O7[7-9]:ledger.* O8[01]:ledger.* O9[23]:ledger.*",
         origin=f"L2・run.py:3629-3630 @{_E}"),
    make("presence", "体", "tick", None,
         resolve_ops="balk_queue begin_exit_walk begin_planned_sleep clear_board_intent rail_arrive rail_depart "
                     "release_indoor set_plan_state wake_from_plan set_activity",
         paths="O3[5-8]:presence.* O70:presence.* O66:act_layer.* O1:act_layer.* O2:act_layer.* O5[01]:runner.* "
               "O73:runner.* O75:runner.*",
         tally="layer_counts", when="presence", origin=f"L3・run.py:3633-3643 @{_E}"),
    make("perceive_prepare", "知覚", "tick", None,
         paths="O63:renderer.* O84:renderer.*",
         scratch_w="field_rows", origin=f"L4・run.py:3649-3664 @{_E}"),
    make("llm_receive", "判断", "tick", None,
         resolve_ops="write_memory write_store_memory",
         paths="O43:run_day.* O44:run_day.* O96:run_day.* O39:conv.* O40:conv.* O41:conv.* O91:conv.* "
               "O8:mem_layer.* O9:mem_layer.* O1[01]:mem_layer.* O12:mem_layer.* O15:wom.* O8[89]:fleet_bridge.* "
               "O87:bridge.* O62:undefined.* O8[23]:undefined.*",
         scratch_w="n_parse_errors_fleet", calls_llm="receive",
         origin=f"L5(遅れ 1)・L11 前半(遅れ 2)・run.py:3668・3890-3891 @{_E}"),
    make("apply_responses", "判断", "tick", None,
         resolve_ops="revert_conversation set_conversing talk_within_reach",
         paths="O43:run_day.* O39:conv.* O40:conv.* O41:conv.* O91:conv.* O[4-6]:intent_layer.* O13:poi_resolver.* "
               "O2[56]:poi_resolver.* O68:poi_resolver.* O94:poi_resolver.* O19:rel_layer.* O34:norm_meter.* "
               "O66:act_layer.*",
         scratch_w="llm_intents n_undefined applied_activity applied_now", buffers_w="focus_request",
         tally="n_undefined_total talk_stats", origin=f"L6・run.py:3671-3785 @{_E}"),
    make("detect", "知覚", "tick", None,
         resolve_ops="apply_detection",
         paths="O45:detector.* O66:act_layer.* O6:intent_layer.*",
         scratch_r="field_rows", scratch_w="det_agent det_cond det_class e_agent e_cond e_class",
         tally="intero_cross", origin=f"L7・run.py:3788-3813 @{_E}"),
    make("plan_boundary", "体", "tick", None,
         resolve_ops="balk_queue begin_exit_walk begin_planned_sleep rail_arrive rail_depart release_indoor "
                     "set_plan_state wake_from_plan",
         paths="O3[5-8]:presence.* O70:presence.* O5[01]:runner.* O73:runner.* O75:runner.*",
         scratch_w="p_agent p_cond p_class", tally="layer_counts sleep_counts",
         origin=f"L8・run.py:3816-3859 @{_E}"),
    make("home_meal", "体", "tick", None,
         resolve_ops="energy_home_meal",
         paths="O2[7-9]:energy.* O3[0-3]:energy.*",
         when="home_meals", origin=f"L9・run.py:3863-3867 @{_E}"),
    make("wake_sources", "判断", "tick", None,
         paths="O39:conv.* O41:conv.* O46:runner.* O72:runner.*",
         scratch_w="c_agent c_cond c_class s_agent s_cond s_class",
         origin=f"L10・run.py:3870-3884 @{_E}"),
    make("wake_filter", "判断", "tick", None,
         resolve_ops="clear_refractory",
         paths="O44:run_day.* O70:presence.*",
         scratch_r="det_agent det_cond det_class e_agent e_cond e_class p_agent p_cond p_class",
         scratch_w="f_agent f_cond f_class f_since f_exempt det_agent det_cond det_class e_agent e_cond e_class "
                   "p_agent p_cond p_class",
         tally="n_fleet_reinjected", origin=f"L11 後半+L12 前半・run.py:3894-3926 @{_E}"),
    make("relations_wake", "会話", "tick", None,
         resolve_ops="write_relations",
         paths="O1[6-9]:rel_layer.*",
         scratch_r="e_agent e_cond e_class", scratch_w="e_agent e_cond e_class",
         when="rel_layer", origin=f"L12 中・run.py:3929-3950 @{_E}"),
    make("wake_assemble", "判断", "tick", None,
         scratch_r="p_agent p_cond p_class det_agent det_cond det_class c_agent c_cond c_class s_agent s_cond s_class "
                   "f_agent f_cond f_class f_since f_exempt e_agent e_cond e_class",
         scratch_w="cands", origin=f"L12 後半・run.py:3952-3978 @{_E}"),
    make("arbiter", "判断", "tick", None,
         paths="O42:arbiter.* O71:arbiter.*",
         scratch_r="cands", scratch_w="outside_now decision",
         tally="awake_sum awake_ticks", origin=f"L13・run.py:3981-3999 @{_E}"),
    make("decide", "判断", "tick", None,
         resolve_ops="set_refractory talk_within_reach write_memory write_store_memory",
         paths="O43:run_day.* O44:run_day.* O96:run_day.* O39:conv.* O40:conv.* O41:conv.* O91:conv.* "
               "O8:mem_layer.* O9:mem_layer.* O1[01]:mem_layer.* O12:mem_layer.* O15:wom.* O17:rel_layer.* "
               "O19:rel_layer.* O2[0-4]:classical.* O69:classical.* O90:classical.* O6[34]:renderer.* O84:renderer.* "
               "O85:bridge.* O86:bridge.* O87:bridge.* O8[89]:fleet_bridge.* O62:undefined.* O8[23]:undefined.* "
               "O35:presence.* O70:presence.*",
         scratch_r="decision outside_now n_parse_errors_fleet", scratch_w="parse_errors",
         tally="calls_by_cond layer_counts n_outside_calls n_fleet_resent peak_pending peak_backlog result",
         calls_llm="send", origin=f"L14・run.py:4002-4127 @{_E}"),
    make("phase_a", "行為の解決", "tick", None,
         resolve_ops="intent_kept_by",
         paths="O[4-6]:intent_layer.* O66:act_layer.*",
         scratch_r="llm_intents", scratch_w="intents llm_intents",
         tally="layer_counts peak_intents", origin=f"L15・run.py:4130-4156 @{_E}"),
    make("phase_b", "行為の解決", "tick", None,
         scratch_r="intents", scratch_w="plan", origin=f"L16・run.py:4159-4163 @{_E}"),
    make("phase_c", "行為の解決", "tick", None,
         resolve_ops="apply",
         paths="O2[7-9]:energy.* O5[0-1]:runner.* O48:runner.* O46:runner.* O47:runner.* O7[2-5]:runner.* "
               "O5[7-9]:ledger.* O60:ledger.* O7[7-9]:ledger.* O8[01]:ledger.* O9[23]:ledger.* O34:norm_meter.* "
               "O94:poi_resolver.* O26:poi_resolver.* O[4-6]:intent_layer.* O66:act_layer.*",
         scratch_r="plan", buffers_r="focus_request", scratch_w="outcome",
         tally="geometry_hops geometry_jammed leave_counts per_action_total result",
         origin=f"L17・run.py:4166-4222 @{_E}"),
    make("conversation", "会話", "tick", None,
         resolve_ops="revert_conversation join_conversation set_conversing talk_within_reach",
         paths="O39:conv.* O40:conv.* O41:conv.* O91:conv.* O19:rel_layer.*",
         scratch_r="plan applied_now outcome", tally="leave_closed",
         when="conv", origin=f"L18・run.py:4229-4356 @{_E}"),
    make("activity_intent", "体", "tick", None,
         resolve_ops="set_activity set_activity_until clear_intent fail_intent relabel_intent_failure set_intent",
         paths="O[1-3]:act_layer.* O66:act_layer.* O[4-6]:intent_layer.*",
         scratch_r="applied_activity", when="act_layer", origin=f"L19・run.py:4360-4368 @{_E}"),
    make("memory", "記憶", "tick", None,
         resolve_ops="write_memory write_relations write_store_memory",
         paths="O[89]:mem_layer.* O1[0-2]:mem_layer.* O1[6-9]:rel_layer.* O64:renderer.* O1[34]:poi_resolver.* "
               "O68:poi_resolver.* O15:wom.*",
         scratch_r="plan outcome", scratch_w="exposures", origin=f"L20 前半・run.py:4369-4393 @{_E}"),
    make("familiarity", "記憶", "tick", None,
         resolve_ops="write_familiarity",
         paths="O7:fam_layer.* O67:fam_layer.*",
         scratch_r="outcome exposures", when="fam_layer", origin=f"L20 中・run.py:4395-4398 @{_E}"),
    make("energy_after", "体", "tick", None,
         paths="O28:energy.* O33:energy.*",
         when="energy", origin=f"L20 後半・run.py:4400-4401 @{_E}"),
    make("observe", "計器", "tick", _OB.observe,
         paths="O34:norm_meter.* O70:presence.*",
         scratch_r="decision cands intents plan outcome n_undefined parse_errors",
         tally="diag_rows prev_tape_misses prev_sessions sleep_counts occ_ticks",
         reads="cfg.occupancy_every layers.arbiter layers.bridge layers.conv layers.norm_meter layers.presence "
               "llm.pending runstats.diag_rows runstats.occ_counts runstats.occ_kind runstats.occ_ticks "
               "runstats.occ_transit runstats.prev_sessions runstats.prev_tape_misses runstats.sleep_tally "
               "scratch.cands scratch.decision scratch.intents scratch.parse_errors scratch.n_undefined "
               "scratch.outcome scratch.plan soa.agents soa.world",
         origin=f"L21+L22・run.py:4403-4451 @{_E}"),
    make("checkpoint", "計器", "tick", _OB.checkpoint,
         paths="O2:act_layer._digest_cache",
         tally="result",
         reads="cfg.checkpoint_detail cfg.checkpoint_every cfg.total_ticks fx.schedule fx.schedule_hash "
               "layers.act_layer layers.intent_layer layers.runner runstats.phase runstats.result soa.agents soa.world",
         origin=f"L23・run.py:4452-4495 @{_E}"),
    # ================================================================ 日の終わり
    make("day_close", "暦", "day_end", None,
         resolve_ops="rail_depart sync_transit_activity",
         paths="O2:act_layer._digest_cache O5[0-6]:runner.* O61:runner.* O7[2-6]:runner.* O95:runner.* "
               "O5[7-9]:ledger.* O60:ledger.* O7[7-9]:ledger.* O8[01]:ledger.* O9[23]:ledger.* O70:presence.* "
               "O3[5-8]:presence.*",
         tally="daily_records state_files result", origin=f"L24・run.py:4497-4500 @{_E}"),
    # ================================================================ ランの終わり
    make("drain", "判断", "run_end", None,
         paths="O43:run_day.* O44:run_day.* O96:run_day.* O8[89]:fleet_bridge.* O87:bridge.*",
         tally="result state_files", calls_llm="drain", origin=f"E0・run.py:4503-4549 @{_E}"),
    make("close_final", "暦", "run_end", None,
         resolve_ops="rail_depart sync_transit_activity",
         paths="O2:act_layer._digest_cache O5[0-6]:runner.* O61:runner.* O7[2-6]:runner.* O95:runner.* "
               "O5[7-9]:ledger.* O60:ledger.* O7[7-9]:ledger.* O8[01]:ledger.* O9[23]:ledger.* O70:presence.* "
               "O3[5-8]:presence.* O8[5-7]:bridge.*",
         tally="daily_records state_files result", origin=f"E1・run.py:4551-4592 @{_E}"),
    make("report", "計器", "run_end", _RP.report,
         tally="result sleep_counts",
         origin=f"E2〜E4・run.py:4593-4965 @{_E}"),
)

SPECS: dict[str, SystemSpec] = {s.name: s for s in SYSTEMS}
#: tick の中の系の呼ぶ順(``llm_receive`` は位置 A=``perceive_prepare`` の後に置いた順。位置 B は進行役が選ぶ)。
TICK_ORDER: tuple[str, ...] = tuple(s.name for s in SYSTEMS if s.timing == "tick")
