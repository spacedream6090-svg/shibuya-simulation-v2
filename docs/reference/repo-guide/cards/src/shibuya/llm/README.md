# src/shibuya/llm

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../src/shibuya/llm/__init__.py)

llm: 艦隊クライアント/パーサ/録画テープ。world/agents を import しない(mock LLMが成立する)。

- 公開の関数とクラス
  - `LLMClient`(クラス): LLM クライアントの最小契約(同期)。非同期は実装側の任意 ``acomplete``。
  - `LLMRequest`(クラス): 1回の LLM 呼び出し。
  - `LLMResponse`(クラス): 1回の応答。
  - `TapeLookup`(クラス): 録画テープの完全一致検索(``engine.tape.Replay`` がこの形を満たす)。
  - `estimate_tokens`(関数): 粗いトークン数見積り(expedient: UTF-8 文字数 ÷ 2、最低 1)。
- import している内部モジュール: `shibuya.core.hashing`・`shibuya.llm.contract`・`shibuya.llm.fleet`・`shibuya.llm.mock`・`shibuya.llm.parser`・`shibuya.llm.undefined`
- 呼び手: `shibuya.engine.classical`・`shibuya.engine.experiment.branch`・`shibuya.engine.llm_bridge`・`shibuya.llm.fleet`・`shibuya.llm.mock`・`shibuya.llm.undefined`・`tools/vocab/adjudicate.py`・`tools/vocab/registry_from_tape.py`
- 読む試験: `tests/build_pop/test_w21_stage8_9.py`・`tests/c6/test_c6lib_scenes.py`・`tests/c8/test_ablations_ab7.py`・`tests/economy/cp2/test_cp2_event_links.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_conversation.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_llm_mock.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/llm/test_fleet.py`・`tests/llm/test_mock_v3.py`・`tests/llm/test_undefined.py`・`tests/perception/test_b6_invite.py`・`tests/vocab/test_adjudicate.py`・`tests/vocab/test_undefined_out.py`
- 読む試験(道筋で): `tests/test_places_guard.py`・`tests/tools/test_pkgmove.py`

## [contract.py](../../../../../../../src/shibuya/llm/contract.py)

llm.contract — 行動契約書(R4・v1)の**唯一の正典置き場**(語彙・契約表・対象の型)。

- 公開の関数とクラス
  - `ActionSpec`(クラス): 行動契約表の**1行**(§2.1 の12語 / §2.2 の役割語)。
  - `Target`(クラス): 「対象」欄の解釈結果。``raw`` は**常に逐語**(文面凍結のため加工しない)。
  - `TargetKind`(クラス): 「対象」欄の型(行動契約書 §1 の ``<セルID|物カテゴリ|人ID|なし>`` の一般化)。
  - `Until`(クラス): 「まで」欄の解釈結果。
  - `UntilKind`(クラス): 「まで」欄の型(アジェンダ §1-2 の 6 型)。
  - `action_code_of`(関数): 行動語 → コード。12語は 0..11・役割語は 12..・未知は ``UNDEFINED_ACTION``。
  - `action_words`(関数): その版でパーサが受理する行動語(v1=24 語・v2=25 語・v3=23 語)。
  - `append_comment`(関数): 〔1-8b〕応答の 2 行目の最後に ``ひと言:`` の欄を足す(mock と古典の方策の発話=発話の口の入口)。
  - `check_vocab_version`(関数): ``vocab_version`` を検査して正規化する(不正値は ``ValueError``)。
  - `compat_word`(関数): ある版の語を別の版の語彙で読む(``VOCAB_COMPAT``・F)。対応が無い語はそのまま返す。
  - `cross_action_words`(関数): その版の**種別横断語**(v1=12 語・v2=13 語・v3=11 語+なし)。B0 の出力規約に出す並び。
  - `engine_action_codes`(関数): その版で**エンジンに適用分岐がある**語 → コード(役割語は含まない)。
  - `format_two_line`(関数): 行動契約書 §1 の固定2行形に整形する(字数は呼び出し側が守る)。
  - `format_two_line_v3`(関数): v3 の固定 2 行形に整形する(字数は呼び出し側が守る)。``until`` の既定は語の 1 つ。
  - `is_role_action`(関数): §2.2 の役割語か(``"v3"`` では 並ぶ は横断語=役割語ではない)。
  - `parse_target`(関数): 「対象」欄の文字列 → ``Target``。**例外を投げない**。
  - `parse_until`(関数): 「まで」欄の文字列 → ``Until``。**例外を投げない**。
  - `resolve_landmark`(関数): 固有名 → POI 索引(``None``=解決できない)。
  - `role_action_words`(関数): その版の**役割語**(v1/v2=12 語=``ROLE_ACTION_WORDS`` そのもの・v3=11 語)。
  - `safe_action_word`(関数): その版の安全弁の語(**失敗しない**・未定義行動の落ち先)。v1/v2=待機・v3=なし。
  - `spec_of`(関数): 行動語 → 契約行(未知は None)。``"v2"`` で「食事」・``"v3"`` で v3 の 23 行を引く。
- import している内部モジュール: `shibuya.core.time_consts`
- 呼び手: `shibuya.engine.activity`・`shibuya.engine.classical`・`shibuya.engine.commit`・`shibuya.engine.decision.ports`・`shibuya.engine.duties.port`・`shibuya.engine.events.vocab`・`shibuya.engine.intent`・`shibuya.engine.llm_bridge`・`shibuya.engine.norm_meter`・`shibuya.engine.resolve`・`shibuya.engine.rights.record`・`shibuya.engine.run`・`shibuya.engine.speech.layer`・`shibuya.engine.speech_clock`・`shibuya.engine.systems.build`・`shibuya.llm`・`shibuya.llm.fleet`・`shibuya.llm.mock`・`shibuya.llm.parser`・`shibuya.llm.undefined`・`tools/c6/c6lib.py`・`tools/fig/fig_ab7_actions.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`・`tools/vocab/adjudicate.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`・`tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/speech/test_speech_choice_utterance.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/tape_analysis.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/llm/test_contract.py`・`tests/llm/test_mock_v3.py`・`tests/llm/test_parser.py`・`tests/llm/test_undefined.py`・`tests/llm/test_vocab_v2.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`・`tests/test_cli_vocab_version.py`・`tests/tools/test_dm_eval.py`
- 決定の ID: D-71・D-89・D-92・D-116・第 223・第 271・第 274・第 275

## [fleet.py](../../../../../../../src/shibuya/llm/fleet.py)

llm.fleet — 実 vLLM 艦隊クライアント(httpx 非同期 × N レプリカ)と艦隊ブリッジ。

- 公開の関数とクラス
  - `Deferred`(クラス): 答えが返らなかった 1 呼。**破棄しない**(呼び出し側が次 tick へ繰り延べる)。
  - `FleetBridge`(クラス): ``engine.llm_bridge`` の ``source="fleet"`` 実装(層契約のため llm 側に置く)。
  - `FleetBridgeResult`(クラス): 1 呼の解釈済み結果(engine が intent を組むのに必要なものだけ)。
  - `FleetClient`(クラス): 実 vLLM 艦隊への非同期クライアント(engine の同期ループから使う)。
  - `FleetConfig`(クラス): 艦隊設定(manifest ``llm_fleet`` 節のうちクライアントが要る分)。
  - `FleetDeferredError`(クラス): 同期 1 呼経路(``FleetClient.complete``)で繰り延べになった。
  - `FleetTapeRow`(クラス): ``engine.tape.TapeRow`` と**同じ欄名**の既定行(テープ実体を注入しないときの器)。
  - `LLMCall`(クラス): 艦隊へ投げる 1 呼(engine 側 ``RenderedPrompt`` + 起床情報を層契約越しに運ぶ器)。
  - `LLMResult`(クラス): 答えが返った 1 呼。
  - `Outcome`(クラス): 1 呼の帰結(§7「全て診断行に計数」の分類)。
  - `TapeSink`(クラス): 録画テープの書き出し口(``engine.tape.TapeWriter`` がこの形を満たす)。
  - `cache_salt_for`(関数): 実行モード別 ``cache_salt``(運用設計書 §1.2・実装計画書 §7)。
  - `call_from_request`(関数): ``llm.LLMRequest`` → ``LLMCall``(同期経路と既存テストのための橋)。
  - `fleet_auth_headers`(関数): ``SHIBUYA_FLEET_API_KEY`` が空でなければ ``Authorization: Bearer <値>``。無ければ None。
  - `l4_calls_per_day`(関数): 予算行 L4「上限 400 万呼/日(o64)」を読む(憲法1 の監査点)。
  - `l6_in_flight_per_gpu`(関数): 予算行 L6「**64 in-flight/GPU**(bounded)」を読む(数値をコード側に複製しない)。
  - `max_tokens_for`(関数): レーン → ``max_tokens``(U19 ③ インフラ保護)。
  - `plan_batch`(関数): 1 バッチの発射順とレプリカ割当を決める**純関数**(実装計画書 §7 順序制御)。
  - `route_primary`(関数): レプリカ配分 ``xxhash(call_id) mod N``(実装計画書 §7・N=7 が既定艦隊)。
  - `seed_for`(関数): 呼ごとのデコード seed(``xxh64(call_id, seed=run_seed)`` の下位 31 bit)。
  - `split_system_user`(関数): 描画本文を ``(system, user)`` に割る(B0=system・残り=user)。
- import している内部モジュール: `shibuya.core.budget`・`shibuya.core.hashing`・`shibuya.llm`・`shibuya.llm.contract`・`shibuya.manifest.schema`
- 呼び手: `shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.decide`・`shibuya.engine.systems.llm_io`・`shibuya.engine.systems.run_end`・`shibuya.llm`・`tools/c6/c6lib.py`・`tools/vocab/adjudicate.py`
- 読む試験: `tests/c6/test_l4_l6_budget.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/llm/test_fleet.py`・`tests/llm/test_fleet_auth.py`・`tests/llm/test_fleet_contract.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/test_cli_l4_scale.py`
- 読む試験(道筋で): `tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_state_checks_10f.py`・`tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `fleet_bridge`(`FleetBridge`)
    - `O88` FleetBridge _interned(挙動 no・復元 required) 道筋 `fleet_bridge._interned` 書ける系: decide・drain・llm_receive
    - `O89` FleetBridge の計数(挙動 diag・復元 discardable) 道筋 `fleet_bridge.n_calls`・`fleet_bridge.n_debug_rows`・`fleet_bridge.n_debug_skipped`・`fleet_bridge.n_deferred`・`fleet_bridge.n_deferred_rows`・`fleet_bridge.n_dictionary_mapped`・`fleet_bridge.n_label_alias`・`fleet_bridge.n_parse_errors`・`fleet_bridge.n_parse_errors_strict`・`fleet_bridge.n_positional`・`fleet_bridge.n_role_actions`・`fleet_bridge.n_tape_rows`・`fleet_bridge.n_undefined_mapped`・`fleet_bridge.n_unknown_action` 書ける系: decide・drain・llm_receive
- 環境変数: `SHIBUYA_FLEET_API_KEY`
- 決定の ID: D-55・D-58・D-71

## [mock.py](../../../../../../../src/shibuya/llm/mock.py)

llm.mock — ネットワーク不要の決定論クライアント(MockLLM)とテープ再生クライアント(TapeLLM)。

- 公開の関数とクラス
  - `MockLLM`(クラス): 決定論の 2 行形を返す mock クライアント(ネットワーク・GPU 不要)。
  - `TapeLLM`(クラス): 録画テープから答えるクライアント。**テープ外は例外**(黙って実LLMへ落とさない)。
- import している内部モジュール: `shibuya.core.rng`・`shibuya.core.types`・`shibuya.llm`・`shibuya.llm.contract`
- 呼び手: `shibuya.engine.calendar2.layer`・`shibuya.engine.classical`・`shibuya.engine.contact.port`・`shibuya.engine.experiment.switch`・`shibuya.engine.run`・`shibuya.engine.speech.layer`・`shibuya.engine.systems.build`・`shibuya.llm`・`tools/c6/metric_b_rerun.py`
- 読む試験: `tests/c6/test_t5_order_bias.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/speech/test_speech_choice_utterance.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_tape_wiring.py`・`tests/llm/test_mock_v3.py`
- 読む試験(道筋で): `tests/engine/bridging/test_bridging_ledger.py`・`tests/test_places_guard.py`
- 決定の ID: D-116・D-119・第 277

## [parser.py](../../../../../../../src/shibuya/llm/parser.py)

llm.parser — 2行形の**ラベル基準・寛容行指向**パーサ(知覚契約書 §2.5 の正典実装)。

- 公開の関数とクラス
  - `ParseResult`(クラス): 1応答の解釈結果。
  - `find_action_word`(関数): テキスト中で**最初に現れる**語彙語(同位置なら最長)を返す。
  - `parse_two_line`(関数): 2行形(および4行形)を寛容に読む。**例外を投げない**。
- import している内部モジュール: `shibuya.llm.contract`・`shibuya.llm.undefined`
- 呼び手: `shibuya.engine.commit`・`shibuya.llm`・`tools/c6/c6lib.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/instruments/dm_eval/situations.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/tape_analysis.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_parser_contract.py`・`tests/llm/test_mock_v3.py`・`tests/llm/test_parser.py`・`tests/llm/test_vocab_v2.py`・`tests/perception/test_b6_invite.py`
- 決定の ID: D-71・D-113・D-116・第 266・第 274・第 275

## [undefined.py](../../../../../../../src/shibuya/llm/undefined.py)

llm.undefined — 未定義行動の受理5段(行動契約書 §7・決定台帳 行16)。

- 公開の関数とクラス
  - `Proposal`(クラス): 段2 が作った契約行の候補(段3 で状態が決まる)。
  - `ProposalStatus`(クラス): 裁定行の状態(段2→段3→段4)。
  - `UndefinedActionRecord`(クラス): 段1 の未定義行動レコード。
  - `UndefinedActionRegistry`(クラス): 未定義行動の5段(§7)を回す台帳。**エンジン状態には触れない**。
  - `UndefinedOutcome`(クラス): ``observe`` の返り値。
  - `fallback_actions`(関数): 語彙版 → 段1 の「いま可能な行動」(v1/v2 は ``FALLBACK_ACTIONS`` そのもの)。
  - `map_synonym`(関数): 段0 辞書写像。完全一致 → 最長部分一致の順に引く。**ゼロ呼**。
  - `synonym_table`(関数): 語彙版 → 段0 辞書(``"v1"`` は ``SYNONYMS`` と**同一オブジェクト**)。
  - `synonym_table_version`(関数): 語彙版 → 段0 辞書の版文字列(run manifest の欄)。
  - `target_hints`(関数): 語彙版 → 対象ヒント表(``"v1"`` は現行の 3 行・``"v2"`` は G5 の辞書 v4・``"v3"`` は v5)。
  - `target_surface_hint`(関数): **「対象」欄**の表層 → 対象ヒント(語彙 v3 だけ・完全一致・NFKC)。それ以外は ``""``。
  - `undefined_feedback`(関数): 段1 の失敗フィードバック文面(**文面凍結**)。
- import している内部モジュール: `shibuya.llm`・`shibuya.llm.contract`
- 呼び手: `shibuya.cli`・`shibuya.engine.commit`・`shibuya.engine.run`・`shibuya.llm`・`shibuya.llm.parser`・`tools/c6/c6lib.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/vocab/adjudicate.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_undefined_action.py`・`tests/llm/test_undefined.py`・`tests/llm/test_vocab_v2.py`・`tests/vocab/test_adjudicate.py`・`tests/vocab/test_undefined_out.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `undefined`(`UndefinedActionRegistry`)
    - `O62` UndefinedActionRegistry log・counts・precedents(挙動 no・復元 discardable) 道筋 `undefined.counts`・`undefined.log`・`undefined.precedents` 書ける系: decide・llm_receive
    - `O82` UndefinedActionRegistry proposals・vocabulary_extension・_agents(挙動 no・復元 unknown) 道筋 `undefined._agents`・`undefined.proposals`・`undefined.vocabulary_extension` 書ける系: decide・llm_receive
    - `O83` UndefinedActionRegistry の計数(挙動 diag・復元 discardable) 道筋 `undefined.n_adjudication_calls`・`undefined.n_dictionary_mapped`・`undefined.n_dropped_records` 書ける系: decide・llm_receive
- 決定の ID: D-71・D-116・第 205・第 274
