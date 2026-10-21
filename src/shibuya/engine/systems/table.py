"""engine.systems.table — 系の宣言の表 ``SYSTEMS``(呼ぶ順の 1 つの表)(第 1 期 1-0・草案 §2-2・§2-5)。

- 並び=呼ぶ順(ランの頭 → 日の頭 → 刻みの中 25 → 日の終わり → ランの終わり)。進行役はこの順にしか呼ばない。
  ``llm_receive`` は ``perceive_prepare`` の後(〔第 2 部〕応答の遅れ 2=旧の位置 B の切替口は消した)。
- ``writes.soa`` は ``resolve_ops`` の静的な閉包(``spec.make``・手で書かない)。``resolve_ops``・``writes.paths``・
  scratch・tally は手で書く表(下書き: 6 構成の観測・HEAD の系ごとの差の測り・層のメソッドの静的な到達)。
- 外の道筋は ``鍵:道筋``(末尾の ``*`` で前方一致・``[...]`` で行の範囲)。行は割らない(草案 §0-2)。
- 群は名札(体・世界・知覚・判断・会話・行為の解決・記憶・計器・暦・組み立て)。話題ごとのまとめ直しは T1 の後。

〔第 1 期 1-3〕出来事の記録(状態台帳の行 ``E``)を書く系は ``writes.paths`` に ``E:events.*`` を載せる: world(ActualLog の
行ごとの出来事)・checkpoint と day_close(E=診断の区切りの行)・close_final(最後の便の行と最後の日の締め)。宣言の外の
書きは段 B(試験)と、段 C と同じ実行時の検査(``guard.events_write_allowed``)が落とす。凍結の表は
``tests/engine/events/writes_paths_events.json``。

〔第 1 期 1-6〕記憶の器(状態台帳の行 ``M0``・``M0R``・腕 ``--memory-store events`` のランだけ)を書く系: memory(``M0*``=
その刻みの出来事と計数)・decide と llm_receive(``M0*``=発話の記憶・想起の計数・見せた行の録画・テープの列の控え)・drain
(``M0R``=艦隊の残りの呼のテープの列)。宣言の外の書きは段 B と、器の口の実行時の検査
(``engine.memory_store`` の ``_check_permit``=出来事の記録と同じ形)が落とす。
〔第 1 期 1-9〕金の移動(基本操作 ``economy.ops.transfer``)の目印の列と計器(状態台帳の行 ``A``=CP1 の A 湧かないもの)を書く系は
``writes.paths`` に ``A:ledger.*`` を載せる: phase_c(購入・食事・運賃)・world(補充の代金)・day_close と close_final(締めの計器と検算)。
原因を渡す移動は出来事も書く=phase_c(運賃=過程 rail)に ``E:events.*`` を足した(world は 1-3 で宣言済み)。
〔第 1 期 1-8b〕発話の口(状態台帳の腕の行 ``S8``=未読の列・``S8M``=計器・腕 ``--speech-port on`` のランだけ)を書く系:
decide(届ける=描画の ``perceive`` の ``take_heard``・話す=会話の番の発話)と llm_receive(艦隊と再生の到着の発話)。どちらも
発話の出来事 1 行を書く=llm_receive に ``E:events.*`` を足した(decide は 1-8 J0 で宣言済み)。

〔第 1 期 1-7〕道具の台帳 C0: decide は看板を読んだ出来事(腕 ``SHIBUYA_TOOL_EVENTS``・既定 off=既定のランでは書かない)を
書くので ``E:events.*``(1-8 J0 の判断の出来事と同じ宣言=1 つにまとめた)と、口を持つ ``fx.tools`` の読みを載せた。memory は新しい相手の欄の連絡先の印を消す(状態台帳の
行 ``CT5``=``CT5:rel_layer._contact_flags``)。report は manifest の ``tools`` を作るので ``fx.tools`` を読む。

〔第 2 期 2-1〕経済の段階 2 の腕(``--economy-stage2 on``・状態台帳の行 ``EC``=中身と計器・``EM``=生ログの支払いの方法の列)を
書く系: phase_c(引き出し・支払いの方法・レジの税)・day_close と close_final(給料日の賃金・日の欄)は ``EC:ledger.*``・
``EM:ledger.*``、world(補充の代金の行の方法の列=0)は ``EM:ledger.*``。ATM の表(行 ``ATM``)と信用の器(行 ``CR``)は
組み立ての後は書かない。
〔第 3 期 3-3〕申込書の改変を効かせる系 ``experiment``(刻みの中の最初=日の頭の後・``when="experiment"``=申込書を渡したランだけ
立つ=既定のランでは呼ばない=結果不変)。書くのは申込書の控え(状態台帳の行 ``X``)・決定と告知の出来事(``E:events.*``)・天気の
再生日(L0=``O56:runner.environment.*``)。営業時間の表(``runner.opening.open_matrix``)と暦の祝日の表は台帳の外(キャッシュと
組み立ての物)。

〔第 2 期 2-3〕体の出来事の口(腕 ``--memory-store events`` と出来事の記録のあるランだけ・``engine.events.body``)を書く系:
memory(その刻みの記憶の出来事)・conversation(会話の終わり)は ``E:events.*`` を足した(decide と llm_receive=会話の番は宣言済み)。
記憶の器の記録の目印の seq(状態台帳の腕の行 ``M0L``)は ``M0*:mem_layer.memory_store.*`` に入る。apply_responses は意図に呼の id を
付けるかを見る(``layers.mem_layer`` を読む)・conversation は口を ``layers.mem_layer`` から引く。

〔第 3 期 3-5〕本人の体の層(状態台帳の行 ``BD``=段の境目の計器と TM5 の予約の列)を書く系: body(体の刻み=空腹と疲れ)と
world(5 分の窓の体感温度=環境の過程が体の層の口を呼ぶ)は ``BD:body.*`` を足した。close_final は体の層を結果に渡す
(``layers.body`` を読む)。系の表の変更は宣言の持ち主の付け替え(体の値の書きは resolve の口のまま=``writes.soa`` は前と同じ)。

〔第 6 期 6-2〕カレンダー 1b(腕 ``--calendar 1b``・状態台帳の腕の行 ``C1B``=本人の予定の器・``C1BM``=判断の記録と計器)を
書く系: day_head(日の頭に約束と機会を張る)と presence(計画実行層の後に本人の出入り=``C1B*:calendar_self.*``・判断の出来事
``E:events.*``・歩く口 ``begin_walk_to``)。鉄道の発車が計画実行層に知らせる口から器の連続性の手がかりを書く world・day_close・
close_final は ``C1B:calendar_self.cal_store`` を足した(腕のランだけ=既定では書かない)。close_final は層を結果に渡す。

〔第 6 期 6-2 カレンダー 2〕会話とメッセージから生まれる予定(腕 ``--calendar-2 arm``・状態台帳の腕の行 ``CA2*``)を書く系:
calendar_2(新設・連絡の系の後=本人の予定の器・誘い・帳面・計器・判断の出来事 ``E:events.*``・歩く口 ``begin_walk_to``)。会話の番の
控え(行 ``CA2G``=``calendar2._turns``)は対面の会話の番の発話(decide と llm_receive)と通話の番とメッセージを送る判断(contact)が
積む(腕のランだけ=既定では書かない)。close_final は層を結果に渡す。

〔親の決め〕世界過程が持ち主をまたいで書く所(鉄道と大きな催しが計画実行層の O36・O37・O70 と鉄道の O74 を書く)は
1-0 では宣言で認める(``world`` の ``writes.paths``)。

逐次ループ宣言: なし(表を作るのは起動時に 1 回)。
"""

from __future__ import annotations

from shibuya.engine.systems import act as _AC
from shibuya.engine.systems import body as _BD
from shibuya.engine.systems import day as _DY
from shibuya.engine.systems import decide as _DC
from shibuya.engine.systems import judge as _JG
from shibuya.engine.systems import llm_io as _LIO
from shibuya.engine.systems import observe as _OB
from shibuya.engine.systems import perceive as _PC
from shibuya.engine.systems import remember as _RM
from shibuya.engine.systems import report as _RP
from shibuya.engine.systems import run_end as _RE
from shibuya.engine.systems import talk as _TK
from shibuya.engine.systems import world as _WD
from shibuya.engine.experiment import layer as _EXP
from shibuya.engine.contact import layer as _CTL
from shibuya.engine.calendar2 import layer as _CA2L
from shibuya.engine.systems.spec import SystemSpec, make

__all__ = ["SYSTEMS", "SPECS", "TICK_ORDER"]

_E = "ee3abc7"


def _build_fn(ctx, b):  # noqa: ANN001, ANN202
    """表の上の build(R1)。進行役は ``engine.systems.build.build(_call_args)`` を直に呼ぶ(箱が無いので守らない)。"""
    raise RuntimeError("build は進行役が engine.systems.build.build で呼ぶ")

SYSTEMS: tuple[SystemSpec, ...] = (
    # ================================================================ ランの頭
    make("build", "組み立て", "run_head", _build_fn,
         resolve_ops="initialize initialize_energy set_initial_activity restore_soa restore_items place_at_external "
                     "rail_arrive set_plan_state write_relations",
         origin=f"S0〜S8・run.py:2372-3604 @{_E}"),
    # ================================================================ 日の頭
    make("day_head", "暦", "day_head", _DY.sys_day_head,
         resolve_ops="set_plan_state",
         paths="O3[5-8]:presence.* O70:presence.* O4[6-9]:runner.* O5[0-6]:runner.* O61:runner.* O7[3-6]:runner.* "
               "O95:runner.* "
               "CAL:calendar_shadow.* "  # 〔第 3 期 3-1〕暦 1a の影(腕 1a のランだけ・計器=状態台帳の行 CAL)
               "C1B*:calendar_self.*",  # 〔第 6 期 6-2〕カレンダー 1b の器と計器(腕 1b のランだけ=状態台帳の腕の行 C1B・C1BM)
         tally="day_heads", reads="cfg.ticks cfg.tpd day.b_agent day.b_cell day.b_cond day.b_start day.b_tick "
               "day.w17_substituted fx.calendar fx.schedule fx.weekly layers.act_layer "
               "layers.classical layers.ledger layers.poi_resolver layers.presence layers.runner "
               "runstats.day_heads soa.agents "
               "layers.calendar_shadow "
               "layers.calendar_self",  # 〔第 6 期 6-2〕カレンダー 1b(日の頭に約束と機会を張る)
         origin=f"L0・run.py:3607-3609 @{_E}"),
    # ================================================================ 刻みの中(25+〔3-3〕申込書の系 1)
    # 〔第 3 期 3-3〕申込書の改変を効かせる口(申込書を渡したランだけ立つ・刻みの中の最初=日の頭で張り直した表の後)
    make("experiment", "実験", "tick", _EXP.sys_experiment,
         paths="X:experiment.* E:events.* O56:runner.environment.*",
         when="experiment", reads="layers.experiment",
         origin="第 3 期 3-3(新設・HEAD の区間なし)"),
    make("body", "体", "tick", _BD.sys_body,
         resolve_ops="advance_body energy_out_of_area_meal",
         paths="O2[7-9]:energy.* O3[0-3]:energy.* O21:classical.* "
               "BD:body.*",  # 〔第 3 期 3-5〕本人の体の層(段の境目の計器・TM5 の予約の列=状態台帳の行 BD)
         reads="cfg.meal_sleep_defer layers.classical layers.energy soa.agents "
               "layers.body",  # 〔第 3 期 3-5〕体の自然変動の値は体の層の口が返す
         origin=f"L1・run.py:3610-3624 @{_E}"),
    make("world", "世界", "tick", _WD.sys_world,
         resolve_ops="rail_arrive rail_depart sync_transit_activity balk_queue release_indoor set_thermal "
                     "collect_waste consume discard_to_bin restock request_open_close set_open_flags set_notice_state "
                     "set_plan_state",
         paths="O3[5-7]:presence.* O70:presence.* O4[6-9]:runner.* O5[0-6]:runner.* O61:runner.* O7[2-6]:runner.* "
               "O95:runner.* O5[7-9]:ledger.* O60:ledger.* O7[7-9]:ledger.* O8[01]:ledger.* O9[23]:ledger.* "
               # 段 FIX: 前の刻みの描画の前計算 ``renderer._tickc.flow`` は ``runner.flow`` と同じ配列(``prepare_tick`` の
               # ``np.asarray(flow, uint8)`` は写さない)=世界過程が流れの段をその場で書くと見える(別名)
               "O63:renderer._tickc "
               # 第 1 期 1-3: ActualLog の行ごとの出来事(原因=過程)と行の目印(ActualLog の口 event_sink から)
               "E:events.* "
               # 第 1 期 1-9: 補充の代金の transfer(原因=過程 shelf)の目印の列と計器(状態台帳の行 A)
               "A:ledger.* "
               # 第 2 期 2-1: 生ログの支払いの方法の列(状態台帳の行 EM)
               "EM:ledger.* "
               # 〔第 3 期 3-5〕体感温度は本人の体の層の口(段の境目の計器・TM5 の予約の列=状態台帳の行 BD)
               "BD:body.* "
               # 〔第 6 期 6-2〕鉄道の発車が計画実行層に知らせる口からカレンダー 1b の連続性の手がかり(腕 1b のランだけ)
               "C1B:calendar_self.cal_store",
         reads="layers.runner",
         origin=f"L2・run.py:3629-3630 @{_E}"),
    make("presence", "体", "tick", _BD.sys_presence,
         resolve_ops="balk_queue begin_exit_walk begin_planned_sleep clear_board_intent rail_arrive rail_depart "
                     "release_indoor set_plan_state wake_from_plan set_activity "
                     "begin_walk_to",  # 〔第 6 期 6-2〕カレンダー 1b: 本人が決めた行き先へ歩く(体の基本動作)
         paths="O3[5-8]:presence.* O70:presence.* O66:act_layer.* O1:act_layer.* O2:act_layer.* O5[01]:runner.* "
               "O73:runner.* O75:runner.* "
               # 〔第 6 期 6-2〕カレンダー 1b の器と計器(腕 1b のランだけ)・判断の出来事(行為:移動・原因 LlmCall=候補の源と番号)
               "C1B*:calendar_self.* E:events.*",
         tally="layer_counts phase", when="presence", reads="cfg.tick_seconds layers.act_layer layers.presence runstats.layer_counts "
               "runstats.phase soa.agents "
               "layers.calendar_self",  # 〔第 6 期 6-2〕カレンダー 1b(計画実行層の後に本人の出入り)
         origin=f"L3・run.py:3633-3643 @{_E}"),
    make("perceive_prepare", "知覚", "tick", _PC.sys_perceive_prepare,
         paths="O63:renderer.* O84:renderer.* "
               "PX:proximity.*",  # 第 2 期 2-2: 腕 distance の近傍の索引の計器(状態台帳の行 PX)
         scratch_w="field_rows near_index", reads="cfg.tick_seconds fx.perception layers.act_layer layers.runner scratch.field_rows "
               "soa.agents soa.world "
               "layers.proximity scratch.near_index",  # 第 2 期 2-2: 腕 distance の近傍の索引(既定 None)
         origin=f"L4・run.py:3649-3664 @{_E}"),
    make("llm_receive", "判断", "tick", _LIO.sys_llm_receive,
         resolve_ops="write_memory write_store_memory",
         paths="O43:run_day.* O44:run_day.* O96:run_day.* O39:conv.* O40:conv.* O41:conv.* O91:conv.* "
               "O8:mem_layer.* O9:mem_layer.* O1[01]:mem_layer.* O12:mem_layer.* O15:wom.* O8[89]:fleet_bridge.* "
               "O87:bridge.* O62:undefined.* O8[23]:undefined.* "
               "M0*:mem_layer.memory_store.*"  # 1-6: 記憶の器(会話の発話の記憶・テープの列の控え)
               " S8:speech.* S8M:speech.* S8E:speech.* E:events.*"  # 1-8b: 腕 on の到着の発話(未読の列・計器・発話の出来事 1 行)
               " TCR:talk_clock.* TCC:talk_clock.*"  # 〔第 6 期 6-3 T2〕腕 mora の会話の時計(話す速さの控え・発言の予約・計器)
               # 〔6-3 検収 M1〕腕 mora の発言の予約は全体の窓の待ち行列(行 BW)か区域ごとの時計(行 T4W)に事象を置く
               " BW:batching.* T4W:clock.*"
               # 〔第 6 期 6-2 カレンダー 2〕腕 arm: 到着した会話の番の控え(系 calendar_2 が同じ刻みに読む)
               " CA2G:calendar2._turns",
         scratch_w="n_parse_errors_fleet", calls_llm="receive",
         tally="phase", reads="cfg.fleet_wait_s cfg.store_wom_on cfg.tick_seconds "
               "cfg.vocab_version layers.conv layers.fleet_bridge layers.mem_layer layers.speech layers.wom "
               "llm.fleet_deferred llm.fleet_inflight llm.fleet_waiting llm.pending llm.replay_inbox "
               "runstats.phase scratch.n_parse_errors_fleet soa.agents "
               "layers.talk_clock "  # 〔第 6 期 6-3 T2〕会話の時計(腕 mora のランだけ)
               "layers.calendar2",  # 〔第 6 期 6-2 カレンダー 2〕会話の番の控え(腕 arm のランだけ)
         origin=f"L5(遅れ 1)・L11 前半(遅れ 2)・run.py:3668・3890-3891 @{_E}"),
    make("apply_responses", "判断", "tick", _JG.sys_apply_responses,
         resolve_ops="revert_conversation set_conversing talk_within_reach",
         paths="O43:run_day.* O39:conv.* O40:conv.* O41:conv.* O91:conv.* O[4-6]:intent_layer.* O13:poi_resolver.* "
               "O2[56]:poi_resolver.* O68:poi_resolver.* O94:poi_resolver.* O19:rel_layer.* O34:norm_meter.* "
               "O66:act_layer.*",
         scratch_w="llm_intents n_undefined applied_activity applied_now", buffers_w="focus_request",
         tally="n_undefined_total phase talk_stats", reads="buffers.focus_request cfg.attention_on cfg.salt cfg.v3_hints cfg.vocab_version "
               "fx.schedule fx.space layers.act_layer layers.conv layers.intent_layer layers.ledger "
               "layers.norm_meter layers.poi_resolver layers.rel_layer llm.pending "
               "runstats.n_undefined_total runstats.phase runstats.talk_stats "
               "scratch.applied_activity scratch.applied_now scratch.llm_intents scratch.n_undefined "
               "soa.agents soa.world "
               "layers.proximity "  # 第 2 期 2-2: 腕 distance の判定の規則(返事待ち・会話の相手)
               "layers.mem_layer",  # 第 2 期 2-3: 体の出来事の口のあるランか(意図に呼の id を付ける)
         origin=f"L6・run.py:3671-3785 @{_E}"),
    make("detect", "知覚", "tick", _PC.sys_detect,
         resolve_ops="apply_detection",
         paths="O45:detector.* O66:act_layer.* O6:intent_layer.* "
               "T3M:step_scope.*",  # 〔第 6 期 6-3 T3〕腕 changed の変化の印(内受容の値と段の写し・跨いだ体・計器)
         scratch_r="field_rows", scratch_w="det_agent det_cond det_class e_agent e_cond e_class",
         tally="intero_cross phase", reads="layers.act_layer layers.detector layers.intent_layer runstats.intero_cross "
               "runstats.phase scratch.det_agent scratch.det_class scratch.det_cond scratch.e_agent "
               "scratch.e_class scratch.e_cond scratch.field_rows soa.agents soa.world "
               "layers.step_scope",  # 〔第 6 期 6-3 T3〕何かあった体の印(腕 changed のランだけ)
         origin=f"L7・run.py:3788-3813 @{_E}"),
    make("plan_boundary", "体", "tick", _BD.sys_plan_boundary,
         resolve_ops="balk_queue begin_exit_walk begin_planned_sleep rail_arrive rail_depart release_indoor "
                     "set_plan_state wake_from_plan",
         paths="O3[5-8]:presence.* O70:presence.* O5[01]:runner.* O73:runner.* O75:runner.*",
         scratch_w="p_agent p_cond p_class", tally="layer_counts phase sleep_counts",
         reads="cfg.plan_sleep cfg.tick_seconds day.b_agent day.b_cell day.b_cond day.b_start "
               "fx.schedule layers.presence runstats.layer_counts runstats.phase runstats.sleep_tally "
               "scratch.p_agent scratch.p_class scratch.p_cond soa.agents soa.world",
         origin=f"L8・run.py:3816-3859 @{_E}"),
    make("home_meal", "体", "tick", _BD.sys_home_meal,
         resolve_ops="energy_home_meal",
         paths="O2[7-9]:energy.* O3[0-3]:energy.* O21:classical._gate_hazard",
         when="home_meals", reads="layers.energy soa.agents",
         origin=f"L9・run.py:3863-3867 @{_E}"),
    make("wake_sources", "判断", "tick", _JG.sys_wake_sources,
         paths="O39:conv.* O41:conv.* O46:runner.* O72:runner.*",
         scratch_w="c_agent c_cond c_class s_agent s_cond s_class",
         reads="layers.conv layers.runner scratch.c_agent scratch.c_class scratch.c_cond "
               "scratch.s_agent scratch.s_class scratch.s_cond",
         origin=f"L10・run.py:3870-3884 @{_E}"),
    make("wake_filter", "判断", "tick", _JG.sys_wake_filter,
         resolve_ops="clear_refractory",
         paths="O44:run_day.* O70:presence.*",
         scratch_r="det_agent det_cond det_class e_agent e_cond e_class p_agent p_cond p_class",
         scratch_w="f_agent f_cond f_class f_since f_exempt det_agent det_cond det_class e_agent e_cond e_class "
                   "p_agent p_cond p_class",
         tally="n_fleet_reinjected", reads="layers.presence llm.fleet_deferred runstats.n_fleet_reinjected scratch.det_agent "
               "scratch.det_class scratch.det_cond scratch.e_agent scratch.e_class scratch.e_cond "
               "scratch.f_agent scratch.f_class scratch.f_cond scratch.f_exempt scratch.f_since "
               "scratch.p_agent scratch.p_class scratch.p_cond soa.agents",
         origin=f"L11 後半+L12 前半・run.py:3894-3926 @{_E}"),
    make("relations_wake", "会話", "tick", _TK.sys_relations_wake,
         resolve_ops="write_relations",
         paths="O1[6-9]:rel_layer.*",
         scratch_r="e_agent e_cond e_class", scratch_w="e_agent e_cond e_class",
         when="rel_layer", reads="cfg.n_agents cfg.outside_suppression cfg.plan_exec_on cfg.sleep_suppression "
               "layers.rel_layer scratch.e_agent scratch.e_class scratch.e_cond soa.agents "
               "layers.proximity",  # 第 2 期 2-2: 腕 distance の判定の規則(同席・知人出現)
         origin=f"L12 中・run.py:3929-3950 @{_E}"),
    make("wake_assemble", "判断", "tick", _JG.sys_wake_assemble,
         scratch_r="p_agent p_cond p_class det_agent det_cond det_class c_agent c_cond c_class s_agent s_cond s_class "
                   "f_agent f_cond f_class f_since f_exempt e_agent e_cond e_class",
         scratch_w="cands", reads="scratch.c_agent scratch.c_class scratch.c_cond scratch.cands scratch.det_agent "
               "scratch.det_class scratch.det_cond scratch.e_agent scratch.e_class scratch.e_cond "
               "scratch.f_agent scratch.f_class scratch.f_cond scratch.f_exempt scratch.f_since "
               "scratch.p_agent scratch.p_class scratch.p_cond scratch.s_agent scratch.s_class "
               "scratch.s_cond",
         origin=f"L12 後半・run.py:3952-3978 @{_E}"),
    make("arbiter", "判断", "tick", _JG.sys_arbiter,
         paths="O42:arbiter.* O71:arbiter.*",
         scratch_r="cands", scratch_w="outside_now decision",
         tally="awake_sum awake_ticks phase", reads="cfg.n_agents cfg.outside_suppression cfg.plan_exec_on cfg.sleep_suppression "
               "layers.arbiter runstats.awake_sum runstats.awake_ticks runstats.phase scratch.cands "
               "scratch.decision scratch.outside_now soa.agents",
         origin=f"L13・run.py:3981-3999 @{_E}"),
    make("decide", "判断", "tick", _DC.sys_decide,
         resolve_ops="set_refractory talk_within_reach write_memory write_store_memory",
         paths="O43:run_day.* O44:run_day.* O96:run_day.* O39:conv.* O40:conv.* O41:conv.* O91:conv.* "
               "O8:mem_layer.* O9:mem_layer.* O1[01]:mem_layer.* O12:mem_layer.* O15:wom.* O17:rel_layer.* "
               "O19:rel_layer.* O2[0-4]:classical.* O69:classical.* O90:classical.* O6[34]:renderer.* O84:renderer.* "
               "O85:bridge.* O86:bridge.* O87:bridge.* O8[89]:fleet_bridge.* O62:undefined.* O8[23]:undefined.* "
               "O35:presence.* O70:presence.* "
               "M0*:mem_layer.memory_store.*"  # 1-6: 記憶の器(想起の計数・見せた行の録画・発話の記憶・テープの列)
               # 1-8 J0: 腕 port の候補の口の計器・営業中の店の控えと判断の出来事の行/1-7: 看板を読んだ出来事(作り物の印・
               # 腕 SHIBUYA_TOOL_EVENTS・既定 off)=E:events.* は 1-8 と 1-7 で 1 つ
               " J0:decision.* E:events.*"
               " S8:speech.* S8M:speech.* S8E:speech.*"  # 1-8b: 腕 on の発話の口(届ける=描画の perceive・話す=会話の番)
               " TCR:talk_clock.* TCC:talk_clock.*"  # 〔第 6 期 6-3 T2〕腕 mora の会話の時計(話す速さの控え・発言の予約・計器)
               # 〔6-3 検収 M1〕腕 mora の発言の予約は全体の窓の待ち行列(行 BW)か区域ごとの時計(行 T4W)に事象を置く
               " BW:batching.* T4W:clock.*"
               # 〔第 6 期 6-4 C1 検収 M5〕腕 c1+腕 port: 主の判断が候補の「スマホを見る」を選んだ体の控え(同じ刻みの系 contact が読む)
               " CT1G:contact._look_main CT1M:contact._meter"
               # 〔第 6 期 6-2 カレンダー 2〕腕 arm: 会話の番の控え(系 calendar_2 が同じ刻みに読む)
               " CA2G:calendar2._turns",
         # 第 1 期 1-2: 描いた知覚の事実 ``percepts``(``TickScratch`` の欄・状態台帳の行 P)
         scratch_r="decision outside_now n_parse_errors_fleet", scratch_w="parse_errors percepts",
         tally="calls_by_cond layer_counts n_fleet_resent n_outside_calls peak_backlog peak_pending phase result",
         calls_llm="send", reads="cfg.call_layer cfg.lane cfg.refractory_table cfg.store_wom_on cfg.tick_seconds "
               "cfg.vocab_version layers.arbiter layers.bridge layers.classical layers.conv "
               "layers.decision layers.fleet_bridge layers.mem_layer layers.presence layers.rel_layer layers.speech "
               "layers.wom "
               "llm.fleet_deferred llm.fleet_inflight llm.fleet_waiting llm.pending llm.replay_inbox "
               "runstats.calls_by_cond runstats.layer_counts runstats.n_fleet_resent "
               "runstats.n_outside_calls runstats.peak_backlog runstats.peak_pending runstats.phase "
               "runstats.result scratch.decision scratch.n_parse_errors_fleet scratch.outside_now "
               "scratch.parse_errors scratch.percepts soa.agents fx.tools "
               "layers.talk_clock "  # 〔第 6 期 6-3 T2〕会話の時計(腕 mora のランだけ)
               "layers.calendar2",  # 〔第 6 期 6-2 カレンダー 2〕会話の番の控え(腕 arm のランだけ)
         origin=f"L14・run.py:4002-4127 @{_E}"),
    make("phase_a", "行為の解決", "tick", _AC.sys_phase_a,
         resolve_ops="intent_kept_by",
         paths="O[4-6]:intent_layer.* O66:act_layer.*",
         scratch_r="llm_intents", scratch_w="intents llm_intents",
         tally="layer_counts peak_intents phase", reads="cfg.tick_seconds fx.space layers.act_layer layers.intent_layer runstats.layer_counts "
               "runstats.peak_intents runstats.phase scratch.intents scratch.llm_intents soa.agents",
         origin=f"L15・run.py:4130-4156 @{_E}"),
    make("phase_b", "行為の解決", "tick", _AC.sys_phase_b,
         scratch_r="intents", scratch_w="plan", tally="phase", reads="cfg.salt fx.space runstats.phase scratch.intents scratch.plan soa.world",
         origin=f"L16・run.py:4159-4163 @{_E}"),
    make("phase_c", "行為の解決", "tick", _AC.sys_phase_c,
         resolve_ops="apply",
         paths="O2[7-9]:energy.* O5[0-1]:runner.* O48:runner.* O46:runner.* O47:runner.* O7[2-5]:runner.* "
               "O5[7-9]:ledger.* O60:ledger.* O7[7-9]:ledger.* O8[01]:ledger.* O9[23]:ledger.* O34:norm_meter.* "
               "O94:poi_resolver.* O26:poi_resolver.* O[4-6]:intent_layer.* O66:act_layer.* "
               # 〔T5 で見つけた持ち主をまたぐ書き〕食事で per_hour の門の H を 0 に(resolve._energy_meal が
               # EnergyLayer.meal_reset=ClassicalPolicy._gate_hazard の同じ配列を書く=別名)
               "O21:classical._gate_hazard "
               # 第 1 期 1-9: 購入・食事・運賃の transfer の目印の列と計器(行 A)・運賃の出来事(原因=過程 rail)
               "A:ledger.* E:events.* "
               # 第 2 期 2-1: 経済の段階 2(行 EC=引き出し・支払いの方法・税の計器・行 EM=生ログの支払いの方法の列)
               "EC:ledger.* EM:ledger.* "
               # 第 4 期 4-2: 店の預かり消費税(レジの税を預かり金に積む・腕 SHIBUYA_RULES_42=on)
               "TXD:ledger.*",
         scratch_r="plan", buffers_r="focus_request", scratch_w="outcome",
         tally="geometry_hops geometry_jammed leave_counts per_action_total phase result",
         reads="buffers.focus_request cfg.attention_on cfg.queue_service cfg.seat_release "
               "cfg.report_precondition cfg.vocab_version fx.geom fx.schedule layers.energy "
               "layers.fam_layer layers.ledger layers.mem_layer layers.norm_meter layers.runner "
               "runstats.geometry_hops runstats.geometry_jammed runstats.leave_counts "
               "runstats.per_action_total runstats.phase runstats.result scratch.outcome scratch.plan "
               "soa.agents soa.world "
               "layers.proximity",  # 第 2 期 2-2: 腕 distance の判定の規則(会話の開始)
         origin=f"L17・run.py:4166-4222 @{_E}"),
    make("conversation", "会話", "tick", _TK.sys_conversation,
         resolve_ops="revert_conversation join_conversation set_conversing talk_within_reach",
         paths="O39:conv.* O40:conv.* O41:conv.* O91:conv.* O19:rel_layer.* "
               "E:events.* "  # 第 2 期 2-3: 会話の終わりの出来事(体の出来事の口・腕のランだけ)
               "TCC:talk_clock.*",  # 〔第 6 期 6-3 T2〕腕 mora の会話の時計(終わった会話の長さ・時計の行を消す)
         scratch_r="plan applied_now outcome", tally="leave_closed",
         when="conv", reads="cfg.attention_on layers.conv layers.rel_layer runstats.leave_closed "
               "scratch.applied_now scratch.outcome scratch.plan soa.agents "
               "layers.proximity "  # 第 2 期 2-2: 腕 distance の判定の規則(招待・3 人会話・離脱)
               "layers.mem_layer "  # 第 2 期 2-3: 体の出来事の口(記憶の器が持つ)
               "layers.talk_clock",  # 〔第 6 期 6-3 T2〕会話の時計(腕 mora のランだけ)
         origin=f"L18・run.py:4229-4356 @{_E}"),
    make("activity_intent", "体", "tick", _BD.sys_activity_intent,
         resolve_ops="set_activity set_activity_until clear_intent fail_intent relabel_intent_failure set_intent",
         paths="O[1-3]:act_layer.* O66:act_layer.* O[4-6]:intent_layer.*",
         scratch_r="applied_activity", when="act_layer", reads="layers.act_layer layers.conv layers.intent_layer scratch.applied_activity soa.agents",
         origin=f"L19・run.py:4360-4368 @{_E}"),
    # 〔第 6 期 6-4 C1〕連絡の道具(腕 c1 のランだけ立つ・活動の確定の後=その刻みの判断と会話と活動が決まった後・記憶の前=
    # 周りの出来事の門=顕著行為の「気づいた体」を記憶の書き手より先に絞る)。書くのは持ち主 contact(状態台帳の腕の行 CT1*)と
    # 出来事の記録(族 連絡・通話の発話)と進行役の待ち行列(行 BW=送信と着信の予約)。顕著行為の門の結果は連絡の持ち主の側
    # (腕の行 CT1G)に持ち、顕著行為の過程のキャッシュは書き換えない(〔検収 M1〕記憶の系が salient_view で読む=その刻みに
    # 門を通していなければ止まる)。窓の境目の処理(送信・着信)は進行役の待ち行列の種類(ContactLayer.bind_queue)
    make("contact", "連絡", "tick", _CTL.sys_contact,
         # 〔検収 H1〕送信と着信の予約=系の中から進行役の待ち行列(行 BW)に書く
         paths="CT1*:contact.* E:events.* BW:batching.* "
               "CA2G:calendar2._turns",  # 〔第 6 期 6-2 カレンダー 2〕通話の番とメッセージを送る判断の控え(腕 arm のランだけ)
         scratch_r="decision",
         when="contact", reads="layers.contact layers.conv layers.runner scratch.decision soa.agents soa.world",
         origin="第 6 期 6-4 C1(新設・HEAD の区間なし)"),
    # 〔第 6 期 6-2 カレンダー 2〕会話とメッセージから生まれる予定(腕 arm のランだけ立つ・連絡の系の後=その刻みの会話の番と
    # メッセージを送る判断が控えに積まれた後・会話の終わり(会話の系と連絡の系の掃除)の後・記憶の系の前)。書くのは持ち主
    # calendar2(状態台帳の腕の行 CA2*)と出来事の記録(族 約束)と、本人が約束の場所へ歩く口(体の基本動作 begin_walk_to)
    make("calendar_2", "暦", "tick", _CA2L.sys_calendar_2,
         resolve_ops="begin_walk_to",
         paths="CA2*:calendar2.* E:events.*",
         scratch_r="decision",
         when="calendar2", reads="layers.calendar2 scratch.decision soa.agents soa.world "
                                 "layers.conv layers.contact layers.runner",  # 〔検収 L3〕層が参照で読む持ち主
         origin="第 6 期 6-2 カレンダー 2(新設・HEAD の区間なし)"),
    make("memory", "記憶", "tick", _RM.sys_memory,
         resolve_ops="write_memory write_relations write_store_memory",
         paths="O[89]:mem_layer.* O1[0-2]:mem_layer.* O1[6-9]:rel_layer.* O64:renderer.* O1[34]:poi_resolver.* "
               "O68:poi_resolver.* O15:wom.* "
               "M0*:mem_layer.memory_store.* "  # 1-6: 記憶の器(この刻みの出来事を器にも覚えさせる・計数と新しい行の録画の印)
               "E:events.* "  # 第 2 期 2-3: 体の出来事の口(この刻みの記憶の出来事を記録へ・腕のランだけ)
               "CT5:rel_layer._contact_flags",  # 1-7: 新しい相手の欄の連絡先の印を消す(関係辺の書き手と同じ所)
         scratch_r="plan outcome", scratch_w="exposures", reads="layers.contact layers.conv layers.fam_layer layers.mem_layer layers.renderer layers.runner "
               "scratch.exposures scratch.outcome scratch.plan soa.agents",
         origin=f"L20 前半・run.py:4369-4393 @{_E}"),
    make("familiarity", "記憶", "tick", _RM.sys_familiarity,
         resolve_ops="write_familiarity",
         paths="O7:fam_layer.* O67:fam_layer.*",
         scratch_r="outcome exposures", when="fam_layer", reads="layers.fam_layer scratch.exposures scratch.outcome soa.agents",
         origin=f"L20 中・run.py:4395-4398 @{_E}"),
    make("energy_after", "体", "tick", _BD.sys_energy_after,
         paths="O28:energy.* O33:energy.*",
         when="energy", reads="cfg.tick_seconds layers.energy soa.agents",
         origin=f"L20 後半・run.py:4400-4401 @{_E}"),
    make("observe", "計器", "tick", _OB.observe,
         paths="O34:norm_meter.* O70:presence.*",
         scratch_r="decision cands intents plan outcome n_undefined parse_errors",
         tally="diag_rows prev_tape_misses prev_sessions sleep_counts occ_ticks occ_counts occ_kind occ_transit",
         reads="cfg.occupancy_every layers.arbiter layers.bridge layers.conv layers.norm_meter "
               "layers.presence llm.pending runstats.diag_rows runstats.occ_counts runstats.occ_kind "
               "runstats.occ_ticks runstats.occ_transit runstats.prev_sessions "
               "runstats.prev_tape_misses runstats.sleep_tally scratch.cands scratch.decision "
               "scratch.intents scratch.n_undefined scratch.outcome scratch.parse_errors scratch.plan "
               "soa.agents soa.world",
         origin=f"L21+L22・run.py:4403-4451 @{_E}"),
    make("checkpoint", "計器", "tick", _OB.checkpoint,
         paths="O2:act_layer._digest_cache E:events.*",  # 1-3: E(診断)の区切りの行(checkpoint)
         tally="result phase",  # 段 FIX: phase["checkpoint"](壁時計)=組の別名 ``result, phase = rs.result, rs.phase``
         reads="cfg.checkpoint_detail cfg.checkpoint_every cfg.total_ticks fx.schedule "
               "fx.schedule_hash layers.act_layer layers.arbiter layers.bridge layers.classical "
               "layers.conv layers.detector layers.energy layers.fam_layer layers.fleet_bridge "
               "layers.intent_layer layers.ledger layers.mem_layer layers.norm_meter "
               "layers.poi_resolver layers.presence layers.rel_layer layers.renderer layers.runner "
               "layers.wom llm.fleet_deferred llm.fleet_waiting llm.pending llm.replay_inbox "
               "runstats.phase runstats.result soa.agents soa.world layers.events",
         origin=f"L23・run.py:4452-4495 @{_E}"),
    # ================================================================ 日の終わり
    make("day_close", "暦", "day_end", _DY.sys_day_close,
         # 鉄道の日の締め(rail.step)は計画実行層へ知らせる(notify_departed_by_plan → set_plan_state)=world の鉄道と同じ口
         resolve_ops="rail_arrive rail_depart sync_transit_activity set_plan_state",
         paths="O2:act_layer._digest_cache O5[0-6]:runner.* O61:runner.* O7[2-6]:runner.* O95:runner.* "
               "O5[7-9]:ledger.* O60:ledger.* O7[7-9]:ledger.* O8[01]:ledger.* O9[23]:ledger.* O70:presence.* "
               "O3[5-8]:presence.* "
               "E:events.* A:ledger.* "  # 1-3: E(診断)の区切りの行(日の締め)・その日の記録の計器と保持窓/1-9: 金の計器の締め
               "EC:ledger.* EM:ledger.* "  # 2-1: 経済の段階 2(給料日の賃金・日の欄)と生ログの支払いの方法の列
               "TXD:ledger.* "  # 4-2: 申告の期限の日の締めに預かり消費税を政府へ(腕 SHIBUYA_RULES_42=on)
               "C1B:calendar_self.cal_store",  # 〔6-2〕鉄道の日の締めの発車=カレンダー 1b の連続性の手がかり(腕 1b だけ)
         tally="daily_records state_files result", reads="cfg.census_out cfg.checkpoint_every cfg.fp cfg.parent_run cfg.run_id cfg.seat_release cfg.sim_days "
               "cfg.state_out cfg.tick_seconds cfg.tpd fx.calendar fx.env_fields fx.schedule fx.schedule_hash "
               "layers.act_layer layers.arbiter layers.bridge layers.classical layers.conv "
               "layers.detector layers.energy layers.fam_layer layers.fleet_bridge "
               "layers.intent_layer layers.ledger layers.mem_layer layers.norm_meter "
               "layers.poi_resolver layers.presence layers.rel_layer layers.renderer layers.runner "
               "layers.wom llm.fleet_deferred llm.fleet_inflight llm.fleet_waiting llm.pending "
               "llm.replay_inbox runstats.daily_records runstats.result runstats.state_files "
               "soa.agents soa.world layers.events "
               "layers.proximity "  # 第 2 期 2-2(検収 M1): 状態のファイルの見出しに近接の腕を書く
               "layers.experiment "  # 3-3(検収 L7): 状態の見出しに申込書の指紋(save_state)
               "layers.clock",  # 〔第 6 期 6-3 T4〕日次の記録の時計の種類(区域ごとの時計のランだけ regional)
         origin=f"L24・run.py:4497-4500 @{_E}"),
    # ================================================================ ランの終わり
    make("drain", "判断", "run_end", _RE.sys_drain,
         paths="O43:run_day.* O44:run_day.* O96:run_day.* O8[89]:fleet_bridge.* O87:bridge.* "
               "M0R:mem_layer.memory_store.*",  # 1-6: 艦隊の残りの呼のテープの行=記憶の器の録画の控えを取り出す
         tally="result state_files", calls_llm="drain", reads="cfg.fp cfg.parent_run cfg.run_id cfg.seat_release cfg.sim_days cfg.state_out cfg.t_end "
               "cfg.tick_seconds cfg.total_ticks cfg.tpd fx.env_fields fx.schedule fx.schedule_hash "
               "layers.act_layer layers.arbiter layers.bridge layers.classical layers.conv "
               "layers.detector layers.energy layers.fam_layer layers.fleet_bridge "
               "layers.intent_layer layers.ledger layers.mem_layer layers.norm_meter "
               "layers.poi_resolver layers.presence layers.rel_layer layers.renderer layers.runner "
               "layers.wom llm.fleet_deferred llm.fleet_inflight llm.fleet_waiting llm.pending "
               "llm.replay_inbox runstats.result runstats.state_files soa.agents soa.world "
               "layers.proximity "  # 第 2 期 2-2(検収 M1): 状態のファイルの見出しに近接の腕を書く
               "layers.experiment",  # 3-3(検収 L7): 状態の見出しに申込書の指紋(save_state)
         origin=f"E0・run.py:4503-4549 @{_E}"),
    make("close_final", "暦", "run_end", _RE.sys_close_final,
         # 〔T5 で見つけた漏れ〕歩いて乗る退出の腕では最後の便の発車が計画の印を落とす(presence.notify_departed_by_plan
         # → set_plan_state)。6 構成の観測と既定の腕では通らない道
         resolve_ops="rail_arrive rail_depart sync_transit_activity set_plan_state",
         paths="O2:act_layer._digest_cache O5[0-6]:runner.* O61:runner.* O7[2-6]:runner.* O95:runner.* "
               "O5[7-9]:ledger.* O60:ledger.* O7[7-9]:ledger.* O8[01]:ledger.* O9[23]:ledger.* O70:presence.* "
               "O3[5-8]:presence.* O8[5-7]:bridge.* "
               "E:events.* A:ledger.* "  # 1-3: 最後の便の ActualLog の行の出来事・E の区切りの行・計器と保持窓/1-9: 金の計器
               "EC:ledger.* EM:ledger.* "  # 2-1: 経済の段階 2(最後の日の給料日の賃金・日の欄)と生ログの支払いの方法の列
               "TXD:ledger.* "  # 4-2: 最後の日の締めの預かり消費税の納付(腕 SHIBUYA_RULES_42=on)
               "C1B:calendar_self.cal_store",  # 〔6-2〕最後の便の発車=カレンダー 1b の連続性の手がかり(腕 1b だけ)
         tally="daily_records ledger_growth result state_files", reads="cfg.census_out cfg.checkpoint_every cfg.fp cfg.parent_run cfg.run_id cfg.seat_release cfg.sim_days "
               "cfg.state_out cfg.stopped cfg.t_end cfg.tick_seconds cfg.total_ticks cfg.tpd fx.calendar fx.env_fields "
               "fx.schedule fx.schedule_hash layers.act_layer layers.arbiter layers.bridge "
               "layers.classical layers.conv layers.detector layers.energy layers.fam_layer "
               "layers.fleet_bridge layers.intent_layer layers.ledger layers.mem_layer "
               "layers.norm_meter layers.poi_resolver layers.presence layers.rel_layer "
               "layers.renderer layers.runner layers.wom llm.fleet_deferred llm.fleet_inflight "
               "llm.fleet_waiting llm.pending llm.replay_inbox runstats.daily_records "
               "runstats.ledger_growth runstats.result runstats.state_files soa.agents soa.world layers.events "
               "layers.decision "  # 1-8 J0: 候補の口の層を結果に渡す(manifest の decision_port)
               "layers.speech "  # 1-8b: 発話の口を結果に渡す(manifest の speech_port)
               "layers.proximity "  # 第 2 期 2-2: 近接の層を結果に渡す(manifest の proximity)
               "layers.experiment "  # 3-3: 申込書の持ち主を結果に渡す(manifest の experiment)
               "layers.body "  # 3-5: 本人の体の層を結果に渡す(manifest の body)
               "layers.calendar_shadow "  # 〔第 3 期 3-1〕暦 1a の影を結果に渡す(manifest の calendar_shadow)
               "layers.calendar_self "  # 〔第 6 期 6-2〕カレンダー 1b を結果に渡す(manifest の末尾の calendar_1b)
               "layers.talk_clock layers.step_scope layers.clock "  # 〔第 6 期 6-3〕時計の段の腕の持ち主を結果に渡す
               "layers.contact "  # 〔第 6 期 6-4 C1〕連絡の道具を結果に渡す(manifest の contact_c1)
               "layers.calendar2",  # 〔第 6 期 6-2 カレンダー 2〕会話から生まれる予定を結果に渡す(manifest の calendar_2)
         origin=f"E1・run.py:4551-4592 @{_E}"),
    make("report", "計器", "run_end", _RP.report,
         tally="result sleep_counts frozen_sources_map",  # 段 FIX: 欄の別名 ``frozen_sources_map.update``
         reads="cfg.activity_on cfg.activity_region cfg.area_source cfg.attendance_rate "
               "cfg.attention_on cfg.budget_mode_enum cfg.chooser cfg.classical_habit_p "
               "cfg.classical_tau cfg.day_index cfg.derive_rule cfg.eatery cfg.energy_on "
               "cfg.energy_rate cfg.exit_mode cfg.familiarity_k cfg.familiarity_on cfg.geometry "
               "cfg.home_meal cfg.hunger_model cfg.hunger_words cfg.intent_max_ticks cfg.intent_mode "
               "cfg.l4_scale cfg.meal_sleep_defer cfg.memory_n cfg.memory_on "
               "cfg.mock_move_target_p cfg.mock_out_of_cell_target_p cfg.move_search_radius "
               "cfg.n_agents cfg.occupancy_path "
               "cfg.outside_suppression cfg.p_notice_ablation cfg.p_notice_d50_scale "
               "cfg.parent_run cfg.plan_exec_on "
               "cfg.plan_sleep cfg.policy cfg.refractory_scale_norm cfg.response_delay "
               "cfg.role_words cfg.run_id cfg.seat_area_eatery_m2 cfg.seat_area_retail_m2 cfg.seat_release cfg.signage "
               "cfg.signage_p_see cfg.sim_days cfg.sleep_suppression cfg.stopped cfg.store_memory_on "
               "cfg.store_recall_scope cfg.store_signage_on cfg.store_wom_on cfg.t_begin cfg.t_end "
               "cfg.tick_seconds cfg.vocab_version day.w17_substituted fx.calendar fx.fleet "
               "fx.perception fx.renderer_obj fx.schedule fx.start_check fx.walkable layers.act_layer "
               "layers.arbiter layers.bridge layers.classical layers.conv layers.energy "
               "layers.fam_layer layers.fleet_bridge layers.intent_layer layers.ledger "
               "layers.mem_layer layers.norm_meter layers.poi_resolver layers.presence "
               "layers.rel_layer layers.renderer layers.runner layers.wom llm.fleet_inflight "
               "runstats.awake_sum runstats.awake_ticks runstats.calls_by_cond runstats.daily_records "
               "runstats.day_heads runstats.diag_rows runstats.frozen_sources_map "
               "runstats.geometry_hops runstats.geometry_jammed runstats.intero_cross "
               "runstats.layer_counts runstats.leave_closed runstats.leave_counts "
               "runstats.ledger_growth runstats.n_fleet_reinjected runstats.n_fleet_resent "
               "runstats.n_outside_calls runstats.occ_counts runstats.occ_kind runstats.occ_ticks "
               "runstats.occ_transit runstats.peak_backlog runstats.peak_intents "
               "runstats.peak_pending runstats.per_action_total runstats.phase runstats.read_seconds "
               "runstats.restore_seconds runstats.result runstats.sleep_tally runstats.state_files "
               "runstats.t_start runstats.talk_stats soa.agents soa.world fx.tools",
         origin=f"E2〜E4・run.py:4593-4965 @{_E}"),
)

SPECS: dict[str, SystemSpec] = {s.name: s for s in SYSTEMS}
#: 刻みの中の系の呼ぶ順(``llm_receive`` は ``perceive_prepare`` の後)。
TICK_ORDER: tuple[str, ...] = tuple(s.name for s in SYSTEMS if s.timing == "tick")
