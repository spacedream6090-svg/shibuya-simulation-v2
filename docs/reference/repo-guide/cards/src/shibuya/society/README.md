# src/shibuya/society

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [speech](speech/README.md)・[tools](tools/README.md)

## [__init__.py](../../../../../../../src/shibuya/society/__init__.py)

(冒頭の説明なし)

## [conversation.py](../../../../../../../src/shibuya/society/conversation.py)

engine.conversation — 会話プロトコル(行動契約書 §3)のセッション状態機械。

- 公開の関数とクラス
  - `ConvState`(クラス): セッションの状態(契約書 §3「invited/walkingOver/participating」+ 終了2段)。
  - `ConversationManager`(クラス): 会話セッションの生成・進行・終了(**終了はLLMに決めさせない**)。
  - `GateResult`(クラス): 開始ゲートの判定(契約書 §3 の5条件)。
  - `PendingInvite`(クラス): **返事待ちの招待**(C6・09-09)。
  - `Session`(クラス): 1会話セッション。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.types`
- 呼び手: `shibuya.engine.contact.calls`・`shibuya.engine.contact.chat_state`・`shibuya.engine.contact.layer`・`shibuya.engine.systems.build`・`shibuya.society.speech.port`
- 読む試験: `tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/speech/test_speech_empty_text_errors.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_conversation.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_version_bump_10e.py`
- 読む試験(道筋で): `tests/economy/cp2/test_cp2_write_window.py`
- 状態台帳の行
  - 持ち主 `contact.calls`(`ConversationManager`)
    - `CT1K` CallManager(電話の会話=ConversationManager のセッションと表・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.calls._next_id`・`contact.calls._of_agent`・`contact.calls._pair_invite_until`・`contact.calls._refusal_until`・`contact.calls._speaker_invite_until`・`contact.calls._video`・`contact.calls.join_events`・`contact.calls.n_opened`・`contact.calls.pending_invites`・`contact.calls.sessions` 書ける系: calendar_3・contact
    - `CT1M` 連絡の道具の計器(層・チャット・通話・通話の発話の口の計数と分布・通話の切った判断の控え・第 6 期 6-4 C1)(挙動 diag・復元 discardable・腕 contact-c1) 道筋 `contact.calls.closed_by_reason`・`contact.calls.ignored_events`・`contact.calls.n_accepted`・`contact.calls.n_backchannels`・`contact.calls.n_blocks`・`contact.calls.n_declined`・`contact.calls.n_end_kept_activity`・`contact.calls.n_expired_purged`・`contact.calls.n_gate_rejected`・`contact.calls.n_ignored_invites`・`contact.calls.n_interrupts`・`contact.calls.n_invite_refractory_blocked`・`contact.calls.n_invites`・`contact.calls.n_pending_expired`・`contact.calls.n_pending_unreachable`・`contact.calls.n_revert_kept_activity`・`contact.calls.origin_counts`・`contact.calls.size_hist` 書ける系: calendar_3・contact
  - 持ち主 `contact.chats`(`ConversationManager`)
    - `CT1C` ChatBook(チャットの会話の状態=対面の会話の器 ConversationManager の子・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.chats._next_id`・`contact.chats._of_agent`・`contact.chats._of_key`・`contact.chats._pair_invite_until`・`contact.chats._refusal_until`・`contact.chats._speaker_invite_until`・`contact.chats.join_events`・`contact.chats.n_opened`・`contact.chats.pending_invites`・`contact.chats.sessions` 書ける系: calendar_3・contact
    - `CT1M` 連絡の道具の計器(層・チャット・通話・通話の発話の口の計数と分布・通話の切った判断の控え・第 6 期 6-4 C1)(挙動 diag・復元 discardable・腕 contact-c1) 道筋 `contact.chats._chat_meter`・`contact.chats.closed_by_reason`・`contact.chats.ignored_events`・`contact.chats.n_accepted`・`contact.chats.n_backchannels`・`contact.chats.n_blocks`・`contact.chats.n_declined`・`contact.chats.n_end_kept_activity`・`contact.chats.n_expired_purged`・`contact.chats.n_gate_rejected`・`contact.chats.n_ignored_invites`・`contact.chats.n_interrupts`・`contact.chats.n_invite_refractory_blocked`・`contact.chats.n_invites`・`contact.chats.n_pending_expired`・`contact.chats.n_pending_unreachable`・`contact.chats.n_revert_kept_activity`・`contact.chats.origin_counts`・`contact.chats.size_hist` 書ける系: calendar_3・contact
  - 持ち主 `conv`(`ConversationManager`)
    - `O39` ConversationManager sessions・_of_agent・_refusal_until・_next_id・pending_invites・_pair_invite_until・_speaker_invite_until(挙動 behavior・復元 required) 道筋 `conv._next_id`・`conv._of_agent`・`conv._pair_invite_until`・`conv._refusal_until`・`conv._speaker_invite_until`・`conv.pending_invites`・`conv.sessions` 書ける系: apply_responses・conversation・decide・llm_receive・wake_sources
    - `O40` ConversationManager join_events(挙動 behavior・復元 required) 道筋 `conv.join_events` 書ける系: apply_responses・conversation・decide・llm_receive
    - `O41` ConversationManager origin_counts ほかの計数(挙動 diag・復元 discardable) 道筋 `conv.closed_by_reason`・`conv.ignored_events`・`conv.n_accepted`・`conv.n_backchannels`・`conv.n_blocks`・`conv.n_declined`・`conv.n_end_kept_activity`・`conv.n_expired_purged`・`conv.n_gate_rejected`・`conv.n_ignored_invites`・`conv.n_interrupts`・`conv.n_invite_refractory_blocked`・`conv.n_invites`・`conv.n_pending_expired`・`conv.n_pending_unreachable`・`conv.n_revert_kept_activity`・`conv.origin_counts`・`conv.size_hist` 書ける系: apply_responses・conversation・decide・llm_receive・wake_sources
    - `O91` ConversationManager n_opened(開いたセッションの数)(挙動 behavior・復元 required) 道筋 `conv.n_opened` 書ける系: apply_responses・conversation・decide・llm_receive
- 決定の ID: 11-03・11-03/§2・11-03/§3・D-93・第 346

## [norm_meter.py](../../../../../../../src/shibuya/society/norm_meter.py)

engine.norm_meter — **群・規範の計器**(D-107 (a)・第255 決定・第256 R-42 Q4 親検収)。**読むだけ**。

- 公開の関数とクラス
  - `GroupNormMeter`(クラス): 群・規範の計器(読むだけ)。``engine.run`` が tick の骨格の決まった位置で呼ぶ。
  - `entropy_bits`(関数): 度数 → シャノンエントロピー[bit]\(D-68 の M3b と同じ計算)。度数 0 は 0。
  - `role_code_table`(関数): 語彙の版 → 役割語 → 行動コード(``llm.contract``)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.engine.systems.build`
- 読む試験: `tests/engine/test_norm_meter.py`
- 状態台帳の行
  - 持ち主 `norm_meter`(`GroupNormMeter`)
    - `O34` GroupNormMeter _prev_xy・_pair_keys・_pair_len・計数(挙動 no・復元 discardable) 道筋 `norm_meter._cowalk_pairs_seen`・`norm_meter._ctx`・`norm_meter._pair_keys`・`norm_meter._pair_len`・`norm_meter._prev_xy`・`norm_meter._role_rows`・`norm_meter.cowalk_agent_minutes`・`norm_meter.cowalk_episodes`・`norm_meter.cowalk_pairs_max_tick`・`norm_meter.cowalk_ticks_skipped`・`norm_meter.group_size_minutes`・`norm_meter.inst_group_count`・`norm_meter.inst_grouped_minutes`・`norm_meter.inst_pairs_max_tick`・`norm_meter.inst_size_minutes`・`norm_meter.inst_ticks_skipped`・`norm_meter.inst_walker_minutes`・`norm_meter.moving_agent_minutes`・`norm_meter.n_actions_counted`・`norm_meter.n_actions_off_stage`・`norm_meter.n_ticks`・`norm_meter.no_permission_total`・`norm_meter.role_by_kind`・`norm_meter.role_result`・`norm_meter.seconds`・`norm_meter.tick_ms_max` 書ける系: apply_responses・observe・phase_c
- 決定の ID: R-36・R-42・D-68・D-107・第 255・第 256・第 309
