# tests/perception

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 19 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [facts](facts/README.md)

## [__init__.py](../../../../../../tests/perception/__init__.py)

perception のテスト(知覚契約書 R3-8 v1 の節と 1 対 1)。

## [test_ablation1.py](../../../../../../tests/perception/test_ablation1.py)

ablation ①「チャネル固定枠 vs 同一総トークンの単一ランキング」(知覚契約書 §3.2 の**義務**)。

- 公開の関数とクラス
  - `ab1_tool`(関数)
  - `crowded_scene`(関数): 固定枠が**件数でもトークンでも**切る場面(全員が同一セル・全員が知人)。
  - `n_items`(関数): ``[B4 行為] 目につく出来事: a、b。`` のような列挙行の件数。
  - `reference_scene`(関数): 釘付け用の小さな合成場面(乱数の引き方まで固定)。``kw`` はレンダラへ(``near_order`` など)。
  - `test_budget_mode_parse_accepts_cli_words`(関数)
  - `test_cli_main_has_the_budget_mode_flag`(関数): ``--budget-mode {fixed,ranking}``(既定 fixed)が ``run`` まで届く。
  - `test_cli_run_passes_the_arm_through_kwargs`(関数)
  - `test_default_mode_is_fixed_slots_and_the_golden_bytes_do_not_move`(関数): 既定は固定枠。参照場面のバイトもテンプレ SHA も ablation ① で動かない。
  - `test_every_channel_has_a_ranking_prior`(関数): 上限表の全チャネルに顕著性の既定素性がある(片方だけ増える事故の防止)。
  - `test_group_budgets_hold_in_both_modes`(関数): §2.2 の実効ゲート(共有静的 ≤750・セル ≤250・個体 ≤300)。
  - `test_pool_budget_equals_the_fixed_slot_total`(関数): §3.2「**同一総トークン**」= 池の総額はチャネル上限の総和と一致する。
  - `test_ranking_cache_returns_the_same_cell_bytes`(関数): セル依存ブロックのキャッシュ(鍵=セル×B4 欄ハッシュ)が同じバイトを返す。
  - `test_ranking_keeps_what_the_fixed_slots_cut`(関数): 件数枠(B4.salient 上位2)とトークン枠(B5.near_person 100 tok)を外した差。
  - `test_ranking_orders_near_persons_by_distance`(関数): 単一ランキングの順位は顕著性(視角=サイズ/距離)。近接人物は**近い順**になる。
  - `test_ranking_stays_within_budget_on_many_cells`(関数): 多数セル×多数個体を単一ランキングで描いても予算を破らない。
  - `test_rule8_same_cell_same_band_same_kind_is_byte_identical`(関数): §2.4 ⑧ は**両モードで**成り立つ(池の材料はセルの情報だけ=prefix を壊さない)。
  - `test_run_day_carries_the_arm_into_the_manifest`(関数)
  - `test_run_day_defaults_to_fixed_slots`(関数)
  - `test_shared_static_blocks_are_identical_across_arms`(関数): 共有静的(B0/B1/B3)は両腕で 1 バイトも変わらない(prefix キャッシュの土台)。
  - `test_take_within_pool_never_splits_a_line`(関数)
  - `test_the_switch_is_not_a_no_op`(関数): §3.2 の義務 ablation が**測定可能**であること(C6-b の no-op 報告の解消)。
  - `test_tool_probe_reports_that_the_switch_is_effective`(関数)
  - `test_tool_runs_end_to_end_against_a_fake_vllm`(関数): 偽 vLLM 2 本に対して ``ablation1_fixed_vs_ranking.py`` を端から端まで回す。
  - `test_two_runs_give_the_same_bytes`(関数): 同入力 → 同バイト(2 回組み直して比較)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.run`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`・`tools/c6/ablation1_fixed_vs_ranking.py`
- 決定の ID: D-56・第 304

## [test_ablation6_signage.py](../../../../../../tests/perception/test_ablation6_signage.py)

ablation ⑥「広告ゼロ」(知覚契約書 §8 第1陣 ⑥)の切替口。

- 公開の関数とクラス
  - `scene`(関数): ``test_ablation1.reference_scene`` と同じ合成場面(乱数の引き方まで同じ)。
  - `signage_line`(関数)
  - `test_cli_main_has_the_no_signage_flag`(関数)
  - `test_cli_run_passes_signage_through_kwargs`(関数)
  - `test_default_is_signage_on_and_the_golden_bytes_do_not_move`(関数): 既定は看板あり。参照場面のバイトもテンプレ SHA も ⑥ の導入で動かない。
  - `test_every_cell_loses_its_signage_line`(関数): 1 セルだけでなく**全セル**で空になる(腕は「広告ゼロ」)。
  - `test_group_budget_only_shrinks`(関数)
  - `test_rule8_holds_with_the_arm`(関数): §2.4 ⑧「同セル同時間帯の 2 体で B0-B4b バイト一致」は腕を切っても成り立つ。
  - `test_run_day_defaults_to_signage_on_and_is_byte_identical`(関数)
  - `test_run_day_signage_off_changes_the_prompt_but_not_the_mock_actions`(関数)
  - `test_signage_body_is_the_single_material_for_both_modes`(関数): 材料は ``_signage_body`` 1 本(固定枠=行・ランキング=候補列)。
  - `test_signage_off_renders_the_empty_line_in_both_modes`(関数): 看板行は「表示が無いセル」と**同じ描画**になる(テンプレは元からある空文言)。
  - `test_templates_and_sha_are_untouched`(関数): 凍結テンプレの payload に 1 文字も足していない(v1.1 delta は不要)。
  - `test_the_switch_is_not_a_no_op`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.run`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 決定の ID: D-56・第 304

## [test_attention.py](../../../../../../tests/perception/test_attention.py)

attention: §4 注意ゲート 段1-段3(p_see・注意予算・内容キャップ・命令文除去)。

- 公開の関数とクラス
  - `test_apply_budget_default_is_non_injection`(関数): 既定は**非注入**: 枠が 0 なら何も載らない。
  - `test_budget_counts_match_the_contract`(関数): §4「広告1件・顕著行為1-2・傍受上位1-2」。
  - `test_content_cap_round_7_5_times_gaze_seconds`(関数): §4「round(7.5×注視秒)・下限4字・上限30字」。
  - `test_deviance_raises_rank`(関数): 順位は逸脱度優先(Jovancevic-Misic & Hayhoe 2009)。
  - `test_effect_and_memory_caps_are_declared`(関数)
  - `test_feature_tag_is_required_on_world_text`(関数): §1 条6「素性タグ必須」。
  - `test_gate_stage1_is_deterministic_and_calibrated`(関数)
  - `test_p_see_constants_match_the_contract`(関数): §4「大型ビジョン=0.70(音声有0.78/無音0.63)」・中小媒体 0.14-0.40(expedient)。
  - `test_saliency_is_log_sum_with_floor_not_a_linear_sum`(関数): 積形はフロア付き対数加算(0 の項があっても −inf にならない)。
  - `test_saliency_ties_break_by_id_ascending`(関数)
  - `test_saliency_uses_visual_angle_not_distance_twice`(関数): §4 09-06 改訂: 顕著性 = **視角(サイズ/距離)** × 局所コントラスト。
  - `test_strip_imperatives`(関数)
  - `test_strip_imperatives_keeps_declarative_facts`(関数)
  - `test_tag_world_text_applies_the_content_cap`(関数)
- import している内部モジュール: `shibuya.perception.attention`

## [test_b4_detector_gap.py](../../../../../../tests/perception/test_b4_detector_gap.py)

B4 の「安い変化検出器」と「描画バイト」の関係を測る診断テスト+**結線後のゲート**。

- 公開の関数とクラス
  - `test_c2_field_row_missed_almost_half_of_the_rendered_changes`(関数): 記録: C2 の欄(密度段8値)で見ると LOS の跨ぎを取りこぼす件数(結線の根拠)。
  - `test_c3_field_row_misses_nothing_and_never_over_detects`(関数): ゲート: 結線後の欄(``hashes.b4_field_row``)は描画バイト変化を**1件も落とさない**。
  - `test_perception_field_hash_is_a_true_refinement`(関数): 知覚側の欄ハッシュは描画バイトの refinement(欄が同じ ⇒ バイトも同じ)。
  - `test_prepare_tick_publishes_the_rows_the_engine_hashes`(関数): ``Renderer.b4_field_rows`` が ``prepare_tick`` の欄そのもの(engine が読む 1 本)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.text.hashes`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`

## [test_b4b_queue_feed.py](../../../../../../tests/perception/test_b4b_queue_feed.py)

B4b「近景」への待ち行列の差し込み(C4 後半で付けた唯一の可変欄)。

- 公開の関数とクラス
  - `test_b4b_change_is_visible_to_the_change_detector`(関数): B4b が変われば ``b4_field_rows``(起床条件 (i) が読む欄)も変わる。
  - `test_b4b_is_the_fixed_empty_phrase_without_queues`(関数)
  - `test_b4b_respects_the_channel_token_budget`(関数)
  - `test_b4b_stays_cell_shared_bytes_rule_eight`(関数): 規約⑧: 同じセルの 2 体は B4b もバイト一致(行列は POI 単位=セル共有)。
  - `test_queue_rows_reach_b4b_for_the_cell_that_holds_the_poi`(関数)
  - `test_the_largest_queue_wins_inside_a_cell`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`

## [test_b6_invite.py](../../../../../../tests/perception/test_b6_invite.py)

被招待の提示(知覚契約書 §6 起床(ii))を B6 の**既存スロット**で出す。

- 公開の関数とクラス
  - `build`(関数)
  - `test_budgets_hold_with_the_invite_line`(関数): B6 はブロック予算 80 内・個体群は 300 内(混雑+長い id+失敗理由の最悪ケース)。
  - `test_deterministic_and_parses_back_to_the_inviter`(関数): 同入力→同バイト。文面の「対象: P-<id>」は**パーサで招待者 id に戻る**。
  - `test_end_to_end_only_the_real_renderer_lets_the_invitee_accept`(関数): 情報経路そのものの効果: 招待文が届く構成でだけ承諾が立つ。
  - `test_inviter_wins_over_the_wake_reason_word`(関数): 被招待は起床理由そのもの=``wake_reason`` の語ではなく招待文が出る。
  - `test_no_invite_renders_exactly_as_before`(関数): 招待が無ければ(None/負値)**バイト不変**=既存 golden は動かない。
  - `test_only_the_pending_invitee_gets_an_inviter`(関数): 返事待ちの被招待だけが招待者を持つ。**起床条件では絞らない**。
  - `test_rule8_and_b5_do_not_move_for_the_invitee`(関数): B6 は**個体ブロック**なので、被招待でも B0-B4b と B5 は 1 バイトも動かない。
  - `test_template_sha256_is_untouched`(関数): テンプレ本体(``TEMPLATES``/``WAKE_REASON_TEXT``)に行を足していない。
  - `test_the_invitee_is_told_who_spoke_to_them`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.run`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.parser`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 決定の ID: D-62・第 137

## [test_channels.py](../../../../../../tests/perception/test_channels.py)

channels: §3.2 チャネル別トークン上限表・根拠等級・有界化(行を割らない切り詰め)。

- 公開の関数とクラス
  - `test_budget_mode_has_the_mandatory_ablation_arm`(関数): §3.2 の**義務 ablation**「固定枠 vs 単一ランキング」の枠がある。
  - `test_channel_table_matches_contract_section_3_2`(関数): §3.2 の表(内訳 → tok・等級)を逐語で持っている。
  - `test_channel_totals_equal_the_block_budgets`(関数): 縦計が §2.2 のブロック予算に一致(B5 220 / B2 150 / B4 60 / B4b 40)。
  - `test_estimate_tokens_matches_the_llm_side_convention`(関数): ``llm.estimate_tokens``(文字数÷2・最低1)との二重定義が一致している。
  - `test_grades_map_to_mechanism_or_expedient`(関数)
  - `test_intentional_distortion_note_is_present`(関数): §3.2 の「反対証拠の明記」はコードに残す(消したら契約違反)。
  - `test_truncation_never_splits_a_line`(関数)
  - `test_truncation_reports_no_truncation_when_it_fits`(関数)
  - `test_truncation_respects_item_count_cap`(関数)
  - `test_unknown_channel_requires_explicit_limit`(関数)
- import している内部モジュール: `shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`

## [test_hashes_state.py](../../../../../../tests/perception/test_hashes_state.py)

hashes / state: ハッシュ三役(§2.2/§5)と M12 バイト予算(§3.1/§7)。

- 公開の関数とクラス
  - `test_b4_field_row_rejects_ragged_input`(関数)
  - `test_block_hash_is_xxh64_of_the_rendered_bytes`(関数)
  - `test_field_row_hash_refines_the_rendered_bytes`(関数): 欄が同じ ⇒ 欄ハッシュが同じ(refinement の定義側)。
  - `test_heading_quantization_16_sectors`(関数)
  - `test_invocation_distance_is_not_double_declared_by_default`(関数): 既定では宣言しない(単体ベンチの逃げ道だけ)。〔10e(E1・Q9)〕``agents.state`` の死蔵の
  - `test_m12_two_bytes_for_p_notice_state`(関数): §3.1「向き量子化1 byte+課題従事フラグ1 byte=**2 byte/体**」。
  - `test_prefix_key_depends_on_order`(関数)
  - `test_should_resend_is_the_dormant_suppressor`(関数)
  - `test_state_hash_changes_with_content`(関数)
  - `test_write_guard`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.hashing`・`shibuya.foundation.text.hashes`・`shibuya.world.model.percept_state`

## [test_intent_mode_open.py](../../../../../../tests/perception/test_intent_mode_open.py)

AB7 自由意図の腕の切替口 — 描画側(``docs/design/v2-open-intent-arm-spec.md``)。

- 公開の関数とクラス
  - `scene`(関数): ``test_ablation6_signage.scene`` と同じ合成場面(乱数の引き方まで同じ)。
  - `test_default_intent_mode_is_vocab`(関数)
  - `test_default_path_keeps_the_frozen_hashes`(関数): 既定の B0 は ``TEMPLATES["B0.system"]`` と**同一オブジェクト**=凍結 SHA は動かない。
  - `test_default_renderer_bytes_do_not_move`(関数): 参照場面の描画バイト(⑥ の golden と同じ場面)は AB7 の導入で動かない。
  - `test_hint_mode_b0_sha256_is_frozen`(関数): **文面の指紋**。3 腕はすべて別の SHA(=腕が空振りしていない)。
  - `test_hint_mode_shows_the_vocabulary_and_allows_free_text`(関数): 語彙は**例として残す**+当てはまらないときだけ 10 字以内の自由文(ユーザー決定)。
  - `test_only_the_action_line_differs_between_the_arms`(関数): 腕の差は ``行動:`` の 1 行だけ(理由・対象・ひと言・2 行形・JSON 禁止は同文)。
  - `test_only_the_action_line_differs_in_the_hint_arm`(関数)
  - `test_open_mode_changes_the_b0_sha256`(関数): ``b0_system("open")`` は別の本文=別の SHA(=腕が空振りしていない)。
  - `test_open_mode_hides_the_whitelist_but_keeps_the_target_field`(関数): 語彙は見せない/**対象欄の制約は残す**(効果を閉じるのはエンジンの仕事・仕様書 §2)。
  - `test_renderer_hint_mode_changes_the_rendered_bytes`(関数)
  - `test_renderer_open_mode_changes_the_rendered_bytes`(関数): レンダラ経由でも切替が効く(B0 ブロックと prompt_hash が動く)。
  - `test_unknown_intent_mode_is_refused`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 決定の ID: 第 304

## [test_near_tiebreak.py](../../../../../../tests/perception/test_near_tiebreak.py)

小さいもの①(第300 Q107): B5 近接行の**距離の同点**を run_salt の決定論ハッシュで撹拌する。第 2 批①(第304 Q130): 近接行の**並び**を距離の昇順に(同点は同じ鍵の順)。

- 公開の関数とクラス
  - `test_classical_checkpoint_with_the_default_hash_order`(関数)
  - `test_cli_has_no_near_order_flag`(関数)
  - `test_cli_has_no_near_tiebreak_flag`(関数)
  - `test_default_salt_is_the_run_salt_of_the_seed`(関数)
  - `test_distance_order_breaks_ties_with_the_same_keys_and_keeps_the_focus_first`(関数)
  - `test_distance_order_sorts_by_distance_and_keeps_text_and_members`(関数): 連続座標の混雑世界: 距離順は旧(id 順)と**同じ人・同じ文面・同じ距離**を並べ替えただけ。
  - `test_hash_mode_equals_id_when_no_tie_sits_on_the_boundary`(関数): 連続座標(同点なし)では両モードの出力がビットまで同じ(=同点の無いランは不変)。
  - `test_hash_mode_mixes_who_is_seen_but_keeps_text_and_order`(関数)
  - `test_id_mode_is_the_previous_implementation_even_with_ties`(関数)
  - `test_id_order_reproduces_the_previous_order`(関数)
  - `test_keys_are_deterministic_per_observer_and_salt`(関数)
  - `test_modes_and_default`(関数)
  - `test_near_order_modes_and_default`(関数)
  - `test_strictly_nearer_people_always_stay_in`(関数): k 人目より近い人は撹拌に関係なく全員載る(同点の中からだけ選ぶ)。
  - `tied_crowd`(関数): 1 セルに n 体が**同じ座標**(同じノード)=全員が同点。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.run`・`shibuya.perception.renderer`・`shibuya.world.model.state`・`tests/golden_env.py`・`tests/perception/test_nearby_vectorized.py`
- 読む試験: `tests/engine/test_env_and_sections_10f.py`
- 決定の ID: 11-01・11-03/§3・第 300・第 304・第 330・第 337・第 340

## [test_nearby_vectorized.py](../../../../../../tests/perception/test_nearby_vectorized.py)

B5 近接候補のベクトル化(C7 性能修正)が**挙動を 1 ビットも変えていない**ことの固定。

- 公開の関数とクラス
  - `crowd`(関数): 混雑した合成世界(1 セルに数百体・密度段階が上がって k が 3/2/1 に散る)。
  - `test_agents_outside_the_tick_index_fall_back_like_before`(関数): tick 索引に自分が居ない(セルが動いた)場合も旧実装と同じ(素通り)。
  - `test_empty_and_single_occupant_cells`(関数)
  - `test_negative_control_a_changed_reference_is_caught`(関数): 負の対照: 差し替えの口で 1 人の印を変えると描画の指紋が変わる(差し替えが描画に効いている)。
  - `test_rendered_bytes_are_unchanged_in_both_modes`(関数): 描画バイトが新旧で一致(B5 の行・順序・ランキングの距離まで)。
  - `test_tick_cache_arrays_are_consistent_with_the_soa`(関数): ``cell_pos``(逆置換)と ``cell_x/cell_y``(セル順の連続座標)の不変条件。
  - `test_vectorized_nearby_matches_the_previous_implementation`(関数): 全個体で新旧の出力が**完全一致**(語も距離もビット一致)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.ports.percept`・`shibuya.foundation.text.channels`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 読む試験: `tests/perception/test_near_tiebreak.py`
- 決定の ID: 第 304

## [test_normalize.py](../../../../../../tests/perception/test_normalize.py)

normalize: バイト一致の正規化規約 9 項(知覚契約書 §2.4)。hypothesis の性質テストつき。

- 公開の関数とクラス
  - `test_rule1_and_4_fixed_units`(関数)
  - `test_rule2_sorting_is_permutation_invariant`(関数): 入力の並び順を変えても結果は同じ(=列挙は ID 昇順で正準化される)。
  - `test_rule2_sorts_numeric_then_string`(関数)
  - `test_rule3_canonical_form_has_no_stray_whitespace`(関数)
  - `test_rule3_join_lines_drops_blank_lines_and_uses_lf`(関数)
  - `test_rule3_whitespace_canonicalization_is_idempotent`(関数)
  - `test_rule5_peg_stage_array_matches_scalar`(関数)
  - `test_rule5_peg_stage_on_los_edges`(関数)
  - `test_rule5_rejects_non_monotone_edges`(関数)
  - `test_rule6_detects_abbreviations_in_enumerations`(関数)
  - `test_rule7_empty_phrase`(関数)
  - `test_rule8_guard_accepts_the_frozen_b0_prose`(関数): B0 の散文(「所持金を超える支払い」「空腹・体力・体感温度は0から10」)は個体依存語ではない。
  - `test_rule8_guard_catches_agent_dependent_words`(関数)
  - `test_rule9_1231_and_1234_are_the_same_band`(関数)
  - `test_rule9_rejects_bad_round_width`(関数)
  - `test_rule9_time_is_floored_to_5min`(関数)
- import している内部モジュール: `shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`

## [test_p_notice.py](../../../../../../tests/perception/test_p_notice.py)

p_notice: §3.1 の 2 段ヒル型(TTPF+社会伝播)・検算表・ablation A0-A4・P7 予算。

- 公開の関数とクラス
  - `test_ablation_arms_are_ordered_by_strength_at_a_fixed_distance`(関数): A1(距離のみ)≥ A2(+夜。第 1 期 1-2 で負荷の係数=歩きスマホは消した)≥ A3(+偏心・密度)。
  - `test_ablation_arms_run_and_a0_is_the_constant`(関数)
  - `test_coefficients_match_the_contract`(関数)
  - `test_combination_rule`(関数)
  - `test_contract_table_is_reproduced`(関数): §3.1「d50=40 mのP1: 10 m 0.9995 / … / 200 m 0.010(親再計算で一致)」。
  - `test_cutoff_80m`(関数)
  - `test_determinism_same_seed_same_draw`(関数)
  - `test_eccentricity_zero_behind_the_head`(関数): ``|E_ang|>110°`` は一次視覚ゼロ。
  - `test_event_budget_caps_at_200_per_tick`(関数)
  - `test_load_coefficient_is_gone`(関数): 第 1 期 1-2(決定 10-12 §1-6「係数で持たない」): 負荷の係数 ``m_load``(歩きスマホ 0.46)は消した。
  - `test_moving_event_is_easier_to_detect`(関数)
  - `test_p7_budget_26000_candidates`(関数): §7 P7「0.26 MOPS/イベント」= 26,000 体規模を 1 イベント 1 回のベクトル演算で。
  - `test_social_counts_are_exact_within_radius`(関数)
  - `test_social_fallback_counter_fires_on_extreme_density`(関数): 対の総数が上限を超えると近似へ退避し、退避回数が counters に載る。
  - `test_social_hill_curve`(関数): ``P2 = 0.92·N^1.05/(1.2^1.05+N^1.05)``・N=0 で 0・単調増加・上限 0.92。
  - `test_social_term_lifts_probability`(関数): A4 は A3 より p が高い(社会伝播が上乗せされる)。
  - `test_ttpf_formula_constants`(関数): ``s=d50/d``・``E=2.7+0.7s``・``P1=s^E/(1+s^E)``。
- import している内部モジュール: `shibuya.world.model.notice_reach`
- 決定の ID: 10-12/§1-6

## [test_p_see_activity.py](../../../../../../tests/perception/test_p_see_activity.py)

5 段目 5c(D-117・第293)の活動 → 知覚の乗数は、第 1 期 1-2 で消した(決定 10-12 §1-6「係数で持たない」)。

- 公開の関数とクラス
  - `crowd`(関数): 看板のあるセルへ全員を置いた合成場面。
  - `test_activity_classes_follow_the_state`(関数)
  - `test_cli_has_no_flag`(関数)
  - `test_default_p_see_draws_nothing`(関数)
  - `test_familiarity_entry_uses_the_scalar_p`(関数)
  - `test_gate_equals_the_old_formula_and_ignores_the_activity`(関数): ゲートの結果は従来の式 gate_stage1(1, p_see, (tick, 体, 看板)) と同じ(活動の種別に依らない)。
  - `test_run_day_refuses_a_multiplier_table`(関数)
  - `test_run_manifest_keeps_the_field_as_null`(関数)
  - `test_the_multiplier_table_and_the_arm_are_gone`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.familiarity`・`shibuya.engine.run`・`shibuya.perception.attention`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 決定の ID: 10-12/§1-6・D-117・D-121・第 293

## [test_renderer_golden.py](../../../../../../tests/perception/test_renderer_golden.py)

renderer: golden テスト(§2.4 ⑧ バイト一致・決定論・予算・5分丸め・ハッシュ三役)。

- 公開の関数とクラス
  - `build`(関数): 合成世界+個体(全員 来街者・同一セルに複数体)。
  - `test_a2_different_kind_changes_only_b1`(関数): 種別が違えば B1 だけ動く(B2-B4b は変わらない)。
  - `test_a_same_cell_same_band_same_kind_gives_identical_shared_bytes`(関数): §2.4 ⑧「同セル・同時間帯の2体で B0-B4 のバイト差分がゼロ」。
  - `test_acquaintances_are_always_listed`(関数): 人物④「知人は常に掲載」。
  - `test_b2_wake_reason_and_result_move_only_b6`(関数)
  - `test_b6_carries_reason_observation_and_three_options`(関数): R4 §6「直前の結果」= 失敗理由 + 観測値 + いま可能な行動 3 語。
  - `test_b6_reports_success_and_absence`(関数)
  - `test_b_individual_field_change_moves_only_b5_b6`(関数)
  - `test_blocks_are_in_contract_order_and_text_matches`(関数)
  - `test_c2_prompt_hash_is_blake3_of_the_concatenated_blocks`(関数)
  - `test_c_rendering_is_deterministic`(関数)
  - `test_cache_hit_rate_is_high_on_repeated_cells`(関数)
  - `test_clock_fn_is_injectable`(関数)
  - `test_d_1000_random_renders_stay_within_budgets`(関数)
  - `test_dormant_suppression_uses_the_block_hash`(関数)
  - `test_f_five_minute_rounding_gives_identical_b3`(関数): §2.4 ⑨: 12:31 と 12:34 は同じ B3(丸め幅 5 分)。12:35 は別。
  - `test_field_hash_unchanged_implies_b4_bytes_unchanged`(関数): 欄ハッシュが同じ ⇒ 描画 B4 バイトも同じ(dormant 抑止が取りこぼさない条件)。
  - `test_g_guard_catches_a_planted_person_id_in_b2`(関数): §2.4 ⑧ の機械検査: B2 に ``P-12`` を仕込むと描画が例外で落ちる。
  - `test_interoception_only_shows_threshold_crossings`(関数)
  - `test_j2_real_assets_carry_names_noise_and_weather`(関数)
  - `test_j_real_world_render_100_agents`(関数): 実資産(520 セル)で 100 体描画 → 予算・⑧・キャッシュ命中率を検査する。
  - `test_nearby_persons_decay_with_density`(関数): 人物④「k=密度で逓減(疎3/中2/密1)」。
  - `test_out_of_world_agent_renders_the_fixed_empty_phrases`(関数)
  - `test_salient_events_reach_b4_and_change_its_hash`(関数)
  - `test_signage_is_feature_tagged_and_imperative_free`(関数): §1 条6: 世界内テキストは素性タグつき・命令文除去済み。
  - `test_watched_by_renders_the_fixed_empty_phrase`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.hashing`・`shibuya.foundation.text.hashes`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`

## [test_signage_p_see_gate.py](../../../../../../tests/perception/test_signage_p_see_gate.py)

看板(広告面)の**注視ゲート** ``signage_p_see``(知覚契約書 §4 段1 の p_see)。

- 公開の関数とクラス
  - `crowd`(関数): 看板のあるセルへ全員を置いた場面(二項分布の検定用)。
  - `scene`(関数): ``test_ablation6_signage.scene`` と同じ合成場面(乱数の引き方まで同じ)。
  - `signage_line`(関数)
  - `test_cli_main_has_the_flag`(関数)
  - `test_cli_main_rejects_a_bad_probability`(関数)
  - `test_cli_run_passes_the_gate_through_kwargs`(関数)
  - `test_explicit_one_is_byte_identical_to_not_passing_it`(関数): ``signage_p_see=1.0`` を明示しても描画は 1 バイトも変わらない(両モード)。
  - `test_no_lottery_where_there_is_no_signage`(関数): 看板の無いところでは抽選を引かない(乱数を無駄に消費しない)。
  - `test_out_of_range_is_refused`(関数)
  - `test_rule8_still_holds_at_p_see_one`(関数): p=1.0 では §2.4 ⑧「同セル同時間帯の 2 体で B0-B4b バイト一致」は従来どおり。
  - `test_run_day_carries_the_gate_into_the_manifest_and_counters`(関数)
  - `test_run_day_defaults_to_one_and_is_byte_identical`(関数)
  - `test_run_day_refuses_a_bad_probability`(関数)
  - `test_the_arm_values_sit_inside_the_declared_band`(関数): 腕の 0.30 / 0.14 は §4 段1 の帯の下側(0.14=中小媒体の帯の下端そのもの)。
  - `test_the_default_draws_nothing_even_where_there_is_signage`(関数)
  - `test_the_default_is_one_and_the_golden_bytes_do_not_move`(関数): 既定 p_see=1.0。参照場面のバイトもテンプレ SHA も切替口の導入で動かない。
  - `test_the_derivation_is_pinned_to_gate_stage1`(関数): **導出式の釘付け**: ``gate_stage1(1, p, seed=seed, counters=(tick, agent, poi))``。
  - `test_the_freed_slot_is_not_given_to_another_channel`(関数): 固定枠では、落ちた看板行の**枠を他へ回さない**(他の行はバイト一致・群予算は減る)。
  - `test_the_gate_is_independent_across_ticks_and_agents`(関数): 同じ体でも tick が違えば別の抽選・同じ tick でも体が違えば別の抽選。
  - `test_the_gate_splits_the_shared_prefix_into_at_most_two_variants`(関数): p<1.0 では ⑧ が**体ごとに分かれる**が、同セルの変種は看板あり/なしの高々 2 つ。
  - `test_the_realised_rate_is_inside_the_binomial_band`(関数): n=2,000 の描画で「看板が載った回数」が二項分布 ±4σ に入る(合成世界)。
  - `test_the_seed_changes_the_draw`(関数)
  - `test_two_renderers_with_the_same_seed_agree`(関数): 同じ seed・同じ場面を 2 回作ると**同じ体が同じ tick で同じ結果**になる。
  - `test_zero_is_not_a_no_op`(関数)
  - `test_zero_matches_the_ad_zero_arm_bytes`(関数): ``p_see=0.0`` の B2 は ⑥(``signage_enabled=False``)の B2 とバイト一致。
  - `test_zero_removes_every_signage_line`(関数): ``p_see=0.0`` は全員・全 tick で看板行が空文言になる(=⑥ 広告ゼロと同じ描画)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.cli`・`shibuya.engine.run`・`shibuya.foundation.text.templates`・`shibuya.perception.attention`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 決定の ID: D-56・D-59・第 304

## [test_templates.py](../../../../../../tests/perception/test_templates.py)

templates: 文面凍結(§1 条5)・ブロック表(§2.2)・段階語彙の釘付け(§2.4 ⑤)。

- 公開の関数とクラス
  - `test_action_vocab_matches_llm_contract`(関数): ``llm.contract.ACTION_VOCAB_12`` との二重定義が一致している(同層で import 不可)。
  - `test_b0_keeps_the_ordinance_rules`(関数): §2.5「B0 に**条例の適用規則を明記する方針を維持**」(v0 ③役割知識QAが不合格だった)。
  - `test_b0_output_spec_is_the_two_line_form`(関数): 行動契約書 §1 の 2 行形(理由 / 行動・対象・ひと言)。旧「行き先」は使わない。
  - `test_b0_over_block_budget_but_within_shared_static_group`(関数): **解決した曖昧点**: B0 単体は 300 tok を超えるが、共有静的グループ ≤750 に収まる。
  - `test_b0_with_role_words_appends_one_line_and_keeps_the_frozen_base_d113_4`(関数)
  - `test_b0_with_role_words_stays_within_the_shared_static_group_budget`(関数)
  - `test_b1_has_no_individual_words`(関数): §2.4 ⑧: B1 から v0 の年代・性別(個体依存語)を落とした。
  - `test_block_table_matches_contract_section_2_2`(関数): §2.2 のブロック表(順序=変化率の昇順・予算 tok)と 1 対 1。
  - `test_default_options_always_contain_the_never_failing_action`(関数): 行動契約書 §2.1「失敗しない行動が常に1つ以上(待機)」。
  - `test_density_stage_edges_are_pegged_to_fruin_los`(関数): §2.4 ⑤: 密度段の境界は Fruin 歩行路 LOS(sq ft/人 の逆数)に釘付け。
  - `test_every_template_line_is_one_fact_with_a_feature_tag`(関数): §2.1「素性タグ付きの短い平叙文(1行1事実)」= B1-B6 の行は ``[Bn 名]`` で始まる。
  - `test_noise_stage_bounds_are_pegged_to_environment_standard`(関数): §2.4 ⑤: 騒音段の境界は環境基準(道路に面する地域)昼60/65/70・夜55/60/65。
  - `test_noise_vocab_matches_the_build_side_definition`(関数): ``build.field.w10_noise`` との二重定義が一致している(層契約で共有できないため)。
  - `test_renderer_v3_changes_only_the_b0_block`(関数): 共有ブロックの差は B0 だけ。個体ブロック(B5/B6)は段 2(第276)で v1 の語(待機/休憩)を
  - `test_role_words_match_llm_contract`(関数): ``llm.contract.ROLE_ACTION_WORDS`` との二重定義が一致している(同層で import 不可)。
  - `test_template_sha256_is_frozen`(関数): テンプレ版ハッシュが釘付け(改版は意図的にこの定数を書き換えること)。
  - `test_v3_b0_differs_only_in_the_target_knowledge_and_the_output_spec`(関数)
  - `test_v3_b0_drops_the_placeholder_words_d89`(関数): D-89 (i)(b): 「物のカテゴリ」「セルID」を書かせない(v1 の B0 は不変)。
  - `test_v3_b0_fingerprint_and_the_frozen_v1`(関数)
  - `test_v3_b0_stays_within_the_shared_static_group_budget`(関数)
  - `test_v3_is_the_vocab_arm_only`(関数)
  - `test_v3_output_spec_has_the_five_slots_and_the_note`(関数)
  - `test_v3_vocab_twins_match_llm_contract`(関数)
  - `test_wake_reason_text_covers_all_wake_conditions`(関数): §6 不応期表の 11 行(``agents.state.WakeCondition``)と 1 対 1。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 決定の ID: D-89・D-113・D-116・D-118・D-120・第 269・第 274・第 276・第 291・第 295・第 298・第 299

## [test_vocab_v2_templates.py](../../../../../../tests/perception/test_vocab_v2_templates.py)

語彙 v2 の描画側 — B0 の出力規約に 13 語目「食事」が載る(D-71 §3 E/F)。

- 公開の関数とクラス
  - `scene`(関数): ``test_intent_mode_open.scene`` と同じ合成場面(乱数の引き方まで同じ)。
  - `test_every_arm_and_version_combination_renders`(関数)
  - `test_hint_arm_freezes_its_v2_hash`(関数)
  - `test_only_the_action_line_differs_between_the_vocab_versions`(関数)
  - `test_open_arm_is_identical_across_vocab_versions`(関数): open 腕は語彙を見せない=v1/v2 で B0 は**同一オブジェクト**(差は接地の側だけ)。
  - `test_renderer_v2_changes_the_rendered_bytes`(関数)
  - `test_the_default_bytes_are_frozen`(関数)
  - `test_the_reference_scene_prompt_hash_is_unchanged`(関数)
  - `test_the_thirteen_word_list_matches_the_contract`(関数): 層契約で二重定義になっている 13 語の並びが ``llm.contract`` と一致する。
  - `test_unknown_vocab_version_is_refused`(関数)
  - `test_v2_changes_the_b0_and_shows_the_new_word`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`・`shibuya.perception.renderer`・`shibuya.world.model.state`
- 決定の ID: D-71・第 274・第 304
