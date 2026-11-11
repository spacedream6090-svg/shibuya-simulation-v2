# src/shibuya/foundation/text

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/foundation/text/__init__.py)

(冒頭の説明なし)

## [channels.py](../../../../../../../../src/shibuya/foundation/text/channels.py)

perception.channels — チャネル別トークン上限表(知覚契約書 §3.2)と有界化(切り詰め)。

- 公開の関数とクラス
  - `BudgetMode`(クラス): §3.2 の**義務 ablation**「固定枠 vs 単一ランキング」の切替。
  - `ChannelLimit`(クラス): 1チャネルの上限(§3.2 の表の1行)。
  - `Grade`(クラス): 根拠等級(知覚契約書 §3.2 凡例)。
  - `RankingPrior`(クラス): 単一ランキングでチャネルに与える顕著性の既定素性(**全て expedient**)。
  - `TruncationReport`(クラス): 切り詰めの記録(診断行へ出す)。
  - `block_channel_total`(関数): あるブロックのチャネル上限の合計(§3.2 の「| ブロック | 内訳 |」の縦計)。
  - `estimate_tokens`(関数): 粗いトークン数見積り(expedient: UTF-8 文字数 ÷ 2、最低 1)。
  - `pool_token_budget`(関数): §3.2「**同一総トークン**」= そのブロック群のチャネル上限の総和。
  - `take_within_pool`(関数): **順位順**に並んだ行列から、池の予算に収まる**先頭 n 件**を返す。
  - `truncate_lines`(関数): チャネル上限までの行を残す(**行の途中では絶対に切らない**)。
- 呼び手: `shibuya.build.lang.common`・`shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.report`・`shibuya.engine.tape`・`shibuya.perception.renderer`・`tools/c6/ablation1_fixed_vs_ranking.py`
- 読む試験: `tests/build_lang/test_w14_signage.py`・`tests/build_lang/test_w15_cell_static.py`・`tests/build_lang/test_wiring.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_two_layer_activity.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_channels.py`・`tests/perception/test_nearby_vectorized.py`・`tests/perception/test_templates.py`
- 決定の ID: 11-03・11-03/§2

## [hashes.py](../../../../../../../../src/shibuya/foundation/text/hashes.py)

perception.hashes — **ハッシュ三役**(知覚契約書 §2.2/§5)。

- 公開の関数とクラス
  - `b4_field_row`(関数): B4 の**描画に使う欄**を ``(n_cells, 4)`` int32 に並べる(欄ハッシュの素)。
  - `block_hash`(関数): 描画済みブロックのバイト列 → xxh64(三役の 1 本目=prefix キャッシュ鍵)。
  - `block_hashes`(関数): バイト列の列 → uint64 配列。
  - `field_row_hash`(関数): 1 行の欄 → xxh64。
  - `field_row_hashes`(関数): ``(n, k)`` int32 の行ごとの xxh64。
  - `hash_report`(関数): 診断行用の 1 行(``B2=0x… B4=0x…``)。
  - `prefix_key`(関数): ブロックハッシュの列 → prefix キャッシュ鍵(1 本の u64)。
  - `should_resend`(関数): dormant 再送抑止(三役の 3 本目)。
- import している内部モジュール: `shibuya.foundation.hashing`
- 呼び手: `shibuya.engine.change_detect`・`shibuya.perception.renderer`
- 読む試験: `tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_render_from_percept_bytes.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_hashes_state.py`・`tests/perception/test_renderer_golden.py`
- 読む試験(道筋で): `tests/engine/test_salt_seed_split_10f.py`

## [normalize.py](../../../../../../../../src/shibuya/foundation/text/normalize.py)

perception.normalize — バイト一致の正規化規約 9 項(知覚契約書 §2.4)を関数にしたもの。

- 公開の関数とクラス
  - `AgentDependentWordError`(クラス): B0-B4 に個体依存語が混入した(§2.4 ⑧ 違反)。
  - `assert_no_abbreviation`(関数): ⑥ 省略記法が入っていないことを検査する。
  - `assert_no_agent_dependent_words`(関数): ⑧ B0-B4 に個体依存語が無いことを検査する(混入したら例外)。
  - `canonical_whitespace`(関数): 空白・改行の正準形(§2.4 ③)。
  - `format_meters`(関数): 距離[m]の固定桁表記(④ 単位固定・① 固定桁丸め)。
  - `format_minutes`(関数): 時間[分]の固定表記。
  - `format_money`(関数): 金額[円]の固定表記(3 桁区切り・v0 文面「所持金は1,200円です」に合わせる)。
  - `format_time`(関数): (時, 分) の**固定桁なし**表記(v0 文面「現在時刻は12時40分です」に合わせる)。
  - `join_lines`(関数): 1行1事実の行列 → ブロック本文(空行は落とし、LF 固定で連結)。
  - `or_empty`(関数): ⑦ 空要素は固定文言。非空なら読点で連結する。
  - `peg_stage`(関数): ⑤ 段階語彙の釘付け: 値 → 段番号(``edges`` は昇順の**法定/LOS 境界**)。
  - `peg_stage_array`(関数): ``peg_stage`` のベクトル版(セル配列にそのまま掛ける)。
  - `round_fixed`(関数): ① 固定桁丸め(段階語彙を持たない量に使う)。
  - `round_time_5min`(関数): 世界内日時 → (時, 分) を 5 分**切り捨て**で丸める(§2.4 ⑨)。
  - `sort_ids`(関数): 列挙は **ID 昇順**(§2.4 ②)。数値 ID は数として、文字列 ID はコードポイント順。
  - `time_band`(関数): 世界内日時 → 5 分帯の番号(0..287)。共有ブロックのキャッシュ鍵。
- import している内部モジュール: `shibuya.foundation.time_consts`
- 呼び手: `shibuya.build.lang.common`・`shibuya.engine.activity`・`shibuya.engine.change_detect`・`shibuya.engine.memory_store`・`shibuya.perception.renderer`
- 読む試験: `tests/build_lang/test_wiring.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_normalize.py`・`tests/perception/test_renderer_golden.py`

## [templates.py](../../../../../../../../src/shibuya/foundation/text/templates.py)

perception.templates — **凍結された観測テンプレ v1**(知覚契約書 §1 条5「文面凍結」)。

- 公開の関数とクラス
  - `b0_sha256`(関数): B0 本文そのものの版ハッシュ(**腕の切替が効いたかの指紋**)。
  - `b0_system`(関数): 腕(``intent_mode``)と語彙版(``vocab_version``)に応じた B0(system)の全文。
  - `block_group`(関数): ブロック id → 予算グループ名。
  - `check_intent_mode`(関数): ``intent_mode`` を検査して正規化する(不正値は ``ValueError``)。
  - `check_role_words`(関数): ``role_words`` を検査して bool に正規化する(``"on"/"off"`` も受ける)。
  - `check_vocab_version`(関数): ``vocab_version`` を検査して正規化する(不正値は ``ValueError``)。
  - `role_words_line`(関数): 語彙版 → B0 の末尾に足す役割語の 1 行(v3 は 11 語)。
  - `template_sha256`(関数): テンプレ全体の版ハッシュ(§1 条5「ハッシュで版管理」)。
- import している内部モジュール: `shibuya.foundation.hashing`
- 呼び手: `shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.classical`・`shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.perception.renderer`・`shibuya.world.things.device`
- 読む試験: `tests/build_lang/test_wiring.py`・`tests/c6/test_c6lib_scenes.py`・`tests/c8/test_ablations_ab7.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_relations.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_two_layer_activity.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_b4b_queue_feed.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_channels.py`・`tests/perception/test_intent_mode_open.py`・`tests/perception/test_normalize.py`・`tests/perception/test_renderer_golden.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`・`tests/test_cli_intent_mode.py`・`tests/test_cli_vocab_version.py`
- 決定の ID: 11-03・11-03/§2・D-38・D-71・D-73・D-89・D-113・D-116・D-118・D-120・第 268・第 269・第 274・第 291・第 295・第 298・第 299
