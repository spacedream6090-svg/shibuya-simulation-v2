# src/shibuya/act/intake

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/act/intake/__init__.py)

(冒頭の説明なし)

## [parser.py](../../../../../../../../src/shibuya/act/intake/parser.py)

llm.parser — 2行形の**ラベル基準・寛容行指向**パーサ(知覚契約書 §2.5 の正典実装)。

- 公開の関数とクラス
  - `ParseResult`(クラス): 1応答の解釈結果。
  - `find_action_word`(関数): テキスト中で**最初に現れる**語彙語(同位置なら最長)を返す。
  - `parse_two_line`(関数): 2行形(および4行形)を寛容に読む。**例外を投げない**。
- import している内部モジュール: `shibuya.act.intake.undefined`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.engine.commit`・`shibuya.runtime.inference.bridge`・`shibuya.runtime.inference.fleet`・`tools/c6/c6lib.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/instruments/dm_eval/situations.py`・`tools/vocab/registry_from_tape.py`
- 読む試験: `tests/build_pop/test_w21_stage8_9.py`・`tests/c6/test_c6lib_aggregate.py`・`tests/economy/cp2/test_cp2_event_links.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/tape_analysis.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_parser_contract.py`・`tests/llm/test_mock_v3.py`・`tests/llm/test_parser.py`・`tests/llm/test_vocab_v2.py`・`tests/perception/test_b6_invite.py`
- 決定の ID: D-71・D-113・D-116・第 266・第 274・第 275

## [undefined.py](../../../../../../../../src/shibuya/act/intake/undefined.py)

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
- import している内部モジュール: `shibuya.foundation.ports.inference`・`shibuya.foundation.vocab.act_codes`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.act.intake.parser`・`shibuya.cli`・`shibuya.engine.run`・`shibuya.runtime.inference.bridge`・`shibuya.runtime.inference.fleet`・`tools/c6/c6lib.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/vocab/adjudicate.py`・`tools/vocab/registry_from_tape.py`
- 読む試験: `tests/c6/test_c6lib_aggregate.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_undefined_action.py`・`tests/llm/test_fleet.py`・`tests/llm/test_fleet_contract.py`・`tests/llm/test_undefined.py`・`tests/llm/test_vocab_v2.py`・`tests/vocab/test_adjudicate.py`・`tests/vocab/test_undefined_out.py`
- 状態台帳の行
  - 持ち主 `undefined`(`UndefinedActionRegistry`)
    - `O62` UndefinedActionRegistry log・counts・precedents(挙動 no・復元 discardable) 道筋 `undefined.counts`・`undefined.log`・`undefined.precedents` 書ける系: decide・llm_receive
    - `O82` UndefinedActionRegistry proposals・vocabulary_extension・_agents(挙動 no・復元 unknown) 道筋 `undefined._agents`・`undefined.proposals`・`undefined.vocabulary_extension` 書ける系: decide・llm_receive
    - `O83` UndefinedActionRegistry の計数(挙動 diag・復元 discardable) 道筋 `undefined.n_adjudication_calls`・`undefined.n_dictionary_mapped`・`undefined.n_dropped_records` 書ける系: decide・llm_receive
- 決定の ID: D-71・D-116・第 205・第 274
