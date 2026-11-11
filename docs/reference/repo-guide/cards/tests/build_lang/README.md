# tests/build_lang

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/build_lang/__init__.py)

tests.build_lang — W14/W15(静的言語化レーン)のテスト。

## [conftest.py](../../../../../../tests/build_lang/conftest.py)

tests.build_lang の共通フィクスチャ。

- 公開の関数とクラス
  - `duplicate_reps`(関数): ``{id: text}`` → rep0/rep1 が同一の応答行(バイト一致ゲートを通る形)。
  - `world_dir`(関数): W14/W15 が読む最小の world_dir。
  - `write_responses`(関数): ``(id, rep, text)`` の並び → fleet_gen 形式の応答 jsonl。
- 読む試験: `tests/build_lang/test_w14_signage.py`・`tests/build_lang/test_w15_cell_static.py`

## [test_checker.py](../../../../../../tests/build_lang/test_checker.py)

検査器の回帰テスト(**第1回生成 2026-09-09 の全件分析が根拠**)。

- 公開の関数とクラス
  - `rules`(関数): その文が踏んだ規則 id の集合(固有名詞+禁止語+個体語+省略記法)。
  - `test_24h_wording_from_the_input_passes`(関数): 新しい入力表現「24時間営業(毎日)」はそのまま書ける。
  - `test_fabricated_hours_against_24h_input_is_caught`(関数): 入力が「24時間営業(毎日)」なのに 10-22 時と書いたら落とす(第1回 74 件の真陽性)。
  - `test_fabricated_kanji_is_still_caught`(関数): 入力にも一般語表にも無い 3 文字以上の漢字列は落とす(真陽性)。
  - `test_full_weekday_names_side_by_side_are_not_abbreviations`(関数): **完全な曜日名を並べただけ**は略記でない(親指示 2026-09-09 第3回)。
  - `test_fullwidth_digits_in_the_input_are_normalized_before_comparison`(関数): 入力側に全角数字があっても偽陽性にしない(NFKC で寄せる)。
  - `test_generic_katakana_words_pass`(関数)
  - `test_heading_only_output_is_empty_not_frozen`(関数)
  - `test_input_derived_watashi_passes`(関数): **陽性(通る)**: 入力(POI 名)由来の「私」は個体語ではない。
  - `test_kanji_compound_of_input_and_generic_passes`(関数): 「歯科診療」= 入力語(歯科)+ 一般語(診療)は分解して通す。
  - `test_latin_name_followed_by_digits_passes`(関数): 英字店名に空白・数字が連結しても偽陽性にしない(第1回 47 件の原因)。
  - `test_latin_word_is_matched_case_insensitively`(関数)
  - `test_latin_word_not_in_input_is_still_caught`(関数): 語単位に割っても**入力に無い英字語**は捕まる(捏造の検出は落とさない)。
  - `test_leading_heading_is_stripped`(関数)
  - `test_non_leading_heading_words_are_kept`(関数)
  - `test_normalize_generated_is_idempotent`(関数): 凍結するのは「通したもの」= もう一度通しても動かない(``verify_one`` の検査)。
  - `test_person_id_is_caught_even_if_the_input_mentions_it`(関数): I2(人ID・所持金・内受容)は**本文そのもの**に掛ける(入力で免罪しない)。
  - `test_proper_katakana_not_in_input_is_caught`(関数): 固有名詞らしいカタカナは残す(真陽性)。
  - `test_real_first_person_is_still_caught`(関数): **陰性(落ちる)**: 人称としての語は、入力に「私立…」があっても残る。
  - `test_run_on_kanji_containing_an_input_substring_passes`(関数): 「分日曜」のような連結は、入力に「日曜」があれば文字単位で消えて通る。
  - `test_two_character_common_kanji_words_pass`(関数): 2 文字の一般漢語は N7 の対象外(第1回 113 件のほぼ全部がこれ)。
  - `test_w15_abbreviation_is_caught`(関数): 第1回 W15 の最大要因(106/147)。system で禁止したうえで検査でも落とす。
  - `test_w15_counting_with_digits_is_caught`(関数): 個数を数字で書く(「2軒」)のは入力に無い数字=真陽性(第1回 50 件)。
  - `test_w15_first_person_is_caught`(関数)
  - `test_w15_names_from_the_input_pass`(関数)
  - `test_weekday_abbreviation_is_caught_by_a1_not_n7`(関数): **曜を伴わない**曜日字の連なりだけが略記。⑥(A1)で扱い N7 では扱わない。
  - `test_weekday_pair_present_in_the_input_passes`(関数): 入力に「土日」と書いた場合、その表現は略記ではない。
- import している内部モジュール: `shibuya.build.lang.common`

## [test_w14_signage.py](../../../../../../tests/build_lang/test_w14_signage.py)

W14 看板(a)文面: プロンプト生成の決定論・取り込みゲート・固有名詞検査。

- 公開の関数とクラス
  - `passed_except`(関数): ``poi_rows``(実資産 2,337 の釘付け)以外のゲートが全部通ったか。
  - `test_bad_answers_are_rejected_with_the_right_rule`(関数): 入力に無い固有名詞・数字・評価語・誘導・個体語・省略記法を弾く(陽性例)。
  - `test_frozen_text_survives_strip_imperatives_bytewise`(関数): 凍結文は描画側の命令文除去を通しても**バイトが動かない**(文面凍結宣言 §1 条5)。
  - `test_ingest_freezes_good_answers`(関数)
  - `test_input_derived_proper_nouns_pass`(関数): **陰性例**: 入力(POI 名)由来の固有名詞は通る。
  - `test_missing_response_is_rejected_not_crashed`(関数)
  - `test_normalization_rules`(関数): §2.4 の正規化(1行・空でない)と §3.2 の長さ上限。
  - `test_opening_hours_japanese`(関数)
  - `test_opening_hours_phrase_stays_short`(関数): **実資産**: 圧縮後の営業時間表現が 45 字の本文に収まる長さに落ちている。
  - `test_prompt_fields_match_fleet_gen_format`(関数): ``tools/gen/fleet_gen.py`` が読む欄が揃っている(温度0・seed固定・repeat 2)。
  - `test_prompt_states_the_three_rules`(関数): プロンプトに「固有名詞」「評価語/誘導」「表記」の 3 規則が明記されている。
  - `test_prompts_are_deterministic`(関数): 同じ入力から 2 回作って SHA が一致する(§0-1 決定論)。
  - `test_property_text_covered_by_input_never_violates`(関数): **不変条件**: 生成文が入力文字列に丸ごと含まれるなら固有名詞違反は出ない。
  - `test_property_unknown_katakana_is_always_caught`(関数): **不変条件**: 入力にも一般語表にも無いカタカナ語は必ず捕まる(検出漏れなし)。
  - `test_real_data_prompt_count_and_sha`(関数): 実資産で 2,337 件・プロンプト SHA・平均トークンを出す(§1 W14 の呼数)。
  - `test_rep_mismatch_is_rejected`(関数): 温度 0 なのに rep0/rep1 が違う店は凍結しない(§1 W14 ゲート)。
  - `test_run_is_reproducible`(関数)
  - `test_run_with_responses_freezes_and_records_hashes`(関数)
  - `test_run_without_responses_writes_prompts_only`(関数)
  - `test_whitespace_and_quotes_are_normalized`(関数): 全角空白・引用符・句点まわりの空白は正規化して凍結する(通したものを凍結)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.lang.common`・`shibuya.build.lang.w14_signage`・`shibuya.foundation.text.channels`・`shibuya.perception.attention`・`tests/build_lang/conftest.py`

## [test_w15_cell_static.py](../../../../../../tests/build_lang/test_w15_cell_static.py)

W15 B2 セル静的文: プロンプト生成の決定論・取り込みゲート・個体語の検出・上限。

- 公開の関数とクラス
  - `passed_except`(関数)
  - `test_bad_answers_are_rejected`(関数)
  - `test_gate_population_is_the_frozen_rows`(関数): **ゲートの母集団は凍結行**(親決定 2026-09-09)。
  - `test_individual_word_gate_counts_only_frozen_rows`(関数): 個体語も同じ: 合否は凍結行 0、全応答の件数は報告値。
  - `test_ingest_freezes_good_answers`(関数)
  - `test_over_the_wiring_cap_is_rejected`(関数): 結線枠(``B2.visible`` 60 tok = 120 字)を超えた文は凍結しない。
  - `test_prompt_carries_the_length_regex`(関数): 第3回: 長さは指示ではなく**文法**で保証する(fleet_gen → structured_outputs)。
  - `test_prompt_carries_w2_w6_w8_facts`(関数): W2(層・街区の有無)・W8(可視物・目印)・W6(多い店の種別)がプロンプトに載る。
  - `test_prompt_forbids_individual_and_dynamic_content`(関数): §2.4 ⑧: 個体語・時刻・天候・混雑を書かせない指示が入っている。
  - `test_prompt_lists_at_most_two_names_each`(関数): 第3回: 可視物・目印は**上位 2 件**だけ渡す(too_long 181/188 の直接原因を断つ)。
  - `test_prompt_states_the_first_and_second_round_fixes`(関数): 第1回・第2回生成の不合格要因を system が名指しで禁じている。
  - `test_prompts_are_deterministic_and_keyed_by_cell`(関数)
  - `test_real_data_prompt_count_and_sha`(関数): 実資産で 520 セル(仕様の「≈600」は推定・C1 実測 520)。
  - `test_rep_mismatch_is_rejected`(関数)
  - `test_run_is_reproducible`(関数)
  - `test_run_with_responses_freezes`(関数)
  - `test_run_without_responses_writes_prompts_only`(関数)
  - `test_trailing_kuten_is_stripped_for_the_template`(関数): テンプレ ``B2.visible`` が「。」を持つので、凍結文の末尾句点は落とす。
  - `test_w14_prompt_rows_have_no_regex_key`(関数): W14 は生成済み=**行の形を動かさない**(regex キーを足すと SHA が動く)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.lang.common`・`shibuya.build.lang.w14_signage`・`shibuya.build.lang.w15_cell_static`・`shibuya.foundation.text.channels`・`tests/build_lang/conftest.py`

## [test_wiring.py](../../../../../../tests/build_lang/test_wiring.py)

W14/W15 → レンダラの結線: 凍結文があれば使い、無ければ従来の合成文。

- 公開の関数とクラス
  - `build`(関数)
  - `test_assets_flags`(関数)
  - `test_budgets_hold_with_frozen_text_at_the_cap`(関数): 結線枠いっぱい(``B2.visible`` 60 tok=120 字・``B2.signage`` 25 tok=50 字)でも
  - `test_frozen_cell_static_replaces_the_visible_line_only`(関数)
  - `test_frozen_signage_replaces_the_signage_body`(関数)
  - `test_frozen_text_changes_the_b2_hash_and_prefix_key`(関数): §5 ハッシュ三役: 文面が変われば prefix 鍵も変わる(キャッシュの取り違えなし)。
  - `test_individual_word_in_frozen_text_is_caught_at_render_time`(関数): 凍結文に個体語が混ざっていたら描画が落ちる(多重防御・W15 の ingest でも弾く)。
  - `test_oversized_frozen_text_falls_back_to_the_synthesized_list`(関数): 枠を超える凍結文は切り詰めで落ち、**従来の合成可視物リストへ戻る**(壊れない)。
  - `test_real_assets_load_without_frozen_files`(関数): 実資産には凍結ファイルがまだ無い=従来の合成文のまま(結線が既定を変えない)。
  - `test_real_assets_with_max_length_frozen_text_stay_within_budget`(関数): **実資産 520 セル**に枠いっぱいの凍結文を入れても B2 150 / セル群 250 に収まる。
  - `test_report_line_carries_the_frozen_sha`(関数)
  - `test_switch_is_decided_by_file_presence_and_records_sha`(関数): ``_load_frozen_text``: ファイルが無ければ空文字・在れば読んで sha を記録する。
  - `test_template_sha256_is_still_frozen`(関数): 結線でテンプレ本体を触っていない(凍結 SHA 40af870e(v1.4・旧 v1.3 ea204a66)… が動かない)。
  - `test_two_agents_in_the_same_cell_get_identical_shared_bytes`(関数): W15 のゲート「同セル 2 体でバイト差分ゼロ」を描画側で確かめる。
  - `test_w15_token_cap_derivation_still_holds`(関数): ``w15_cell_static.TOKEN_CAP`` の導出を実資産で再測する。
  - `test_without_frozen_text_b2_is_the_synthesized_one`(関数)
  - `with_frozen`(関数): 合成資産に凍結文を差し込む(``PerceptionAssets.load`` が作る形と同じ)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.build.lang.w15_cell_static`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.model.state`
