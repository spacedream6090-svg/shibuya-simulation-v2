# tests

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 21 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [agents](agents/README.md)・[bench](bench/README.md)・[bridging](bridging/README.md)・[build_audit](build_audit/README.md)・[build_field](build_field/README.md)・[build_geo](build_geo/README.md)・[build_lang](build_lang/README.md)・[build_pop](build_pop/README.md)・[build_rail](build_rail/README.md)・[build_sched](build_sched/README.md)・[build_space](build_space/README.md)・[build_vis](build_vis/README.md)・[c6](c6/README.md)・[c7](c7/README.md)・[c8](c8/README.md)・[core](core/README.md)・[economy](economy/README.md)・[engine](engine/README.md)・[fig](fig/README.md)・[fixtures](fixtures/README.md)・[llm](llm/README.md)・[perception](perception/README.md)・[tools](tools/README.md)・[vocab](vocab/README.md)・[w17](w17/README.md)・[world](world/README.md)

## [__init__.py](../../../../../tests/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_repo_guide.py`

## [_data_ids.py](../../../../../tests/_data_ids.py)

data が要る試験の印 ``requires_data(<id>, ...)`` の登録表(第333・3-2-4)。

- 公開の関数とクラス
  - `check_id`(関数): 登録の無い id(書き間違い)なら ``ValueError``。
  - `first_missing`(関数): 並べた id のうち最初に無いもの(全部あれば ``None``)。
  - `id_of`(関数): data の下の道筋 → id(``<base>:<相対パス>``)。相対の道筋はリポの根からと読む。
  - `ids_of`(関数): 複数の道筋 → id の並び(``pytest.mark.requires_data(*ids_of(a, b))`` の形で使う)。
  - `present`(関数): id の data があるか(プロセスの中で 1 回だけ判定して覚える)。
  - `reason`(関数): 飛ばすときの一律の理由。
  - `skip_unless`(関数): 関数の途中で data の有無を見て飛ばす(理由は印と同じ)。
- import している内部モジュール: `shibuya.build.run`・`shibuya.world.assets`
- 読む試験: `tests/build_audit/test_audit_pipeline.py`・`tests/build_field/test_field_pipeline.py`・`tests/build_field/test_w10_road_names.py`・`tests/build_field/test_w10_ruler.py`・`tests/build_field/test_w12_keio_switch_2_4.py`・`tests/build_field/test_w12_pm_peak_switch.py`・`tests/build_field/test_w12_real_timetables.py`・`tests/build_geo/test_c9c_walkable_area.py`・`tests/build_geo/test_geo_pipeline.py`・`tests/build_pop/test_pop_pipeline.py`・`tests/build_rail/test_w12_arrivals_2_3c.py`・`tests/build_vis/test_vis_pipeline.py`・`tests/conftest.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_version_bump_10e.py`・`tests/test_build_run_keep_stage.py`
- 決定の ID: 第 333

## [_head_copy_pin.py](../../../../../tests/_head_copy_pin.py)

古い commit の写し(試験の材料)を固定する道具(試験の補助)。

- 公開の関数とクラス
  - `order_problems`(関数): 文の順の固定と違う所: 束の数・束ごとに、文を元の文の組の順に、組の名を使い切るまで割り当てられるか。
  - `ref_problems`(関数)
  - `refs`(関数): 意味の固定: 読み込んだ写し ``mod`` の、``shibuya`` を読む import の文が置いた名 → 指す物の元の置き場。
  - `shibuya_imports`(関数): ``shibuya`` を読む import の文(関数の中も含む・相対の import は数えない)。
  - `statement_names`(関数): 束ごとに、文ごとの置く名(文の中の順)。移す前の写しで作ったものが文の順の固定の表になる。
  - `text_sha256`(関数): 字面の固定: 束を印の行に替えた全体の sha256(``lf`` なら先に CRLF を LF に揃える)。
- import している内部モジュール: `tests/_places.py`
- 読む試験: `tests/economy/cp2/head_copies.py`・`tests/perception/facts/scenes.py`・`tests/perception/facts/test_percept_is_scratch.py`

## [_places.py](../../../../../tests/_places.py)

元の置き場で範囲を決める道具(試験の補助・段 4=コードの区分の移動の下ごしらえ)。

- 公開の関数とクラス
  - `Names`(クラス): モジュールの名の集まり。頭(包み)は名の一致だけ、頭でないモジュールは中の名(``mod.名``)も含む。
  - `PlacesMapError`(クラス): 対応表が今の木を説明しない(空・形が違う・古い)。試験を黙って通さず落とす(検収 M-2)。
  - `current_index`(関数): 「今の道 → 元の道」から「元の道 → 今の道」の索引を作る。〔再検収 L-7〕2 つの今のファイルが同じ元の道を持てば止める
  - `current_of`(関数): 元の道 → 今の道(``.py`` だけ。移す前の木では同じ道。今の木に無い元の道は ``KeyError``)。src の宣言の文などが元の道で
  - `declared_path_now`(関数): src の宣言の文が書く ``.py`` の道(``src/shibuya`` からの相対)→ 今の木の道。
  - `files_from`(関数): :func:`rels_from` の今のファイル。
  - `imported`(関数): import の文が読むモジュール: ``import a.b`` は ``a.b``。``from P import c`` は、``P.c`` が木のモジュール(子の
  - `module_names`(関数): モジュールそのものの名(包みの代わりでなく 1 本ずつ)。
  - `module_of`(関数): ``src/shibuya`` からの道 → モジュールの名(``__init__.py`` は包みの名)。
  - `names_from`(関数): 元の置き場が ``mods`` の元のディレクトリにある、今のモジュールの名。
  - `origin_dir`(関数): モジュールの元の置き場のディレクトリ(``src/shibuya`` からの相対・末尾に ``/``。根なら空)。
  - `origin_module`(関数): 今のモジュールの名 → 元の置き場のモジュールの名(木に無い名=``shibuya`` の外など はそのまま)。
  - `origin_of`(関数): 今の道 → 元の道。
  - `origins`(関数): 今の木の全部の ``.py``(``src/shibuya`` からの道)→ 元の道(:func:`origins_from` で表を確かめてから)。
  - `origins_from`(関数): 対応表の中身と包みの根 → 今の木の全部の ``.py``(``pkg`` からの道)→ 元の道。
  - `rel_of`(関数): モジュールの今の道(``src/shibuya`` からの相対)。
  - `rels_from`(関数): 元の置き場が ``mods`` の元のディレクトリ(``recursive`` なら下の包みも)にある、今のファイルの道(並べたもの)。
  - `tree_modules`(関数): 今の木の全部のモジュールの名(包みの頭を含む)。
  - `unknown`(関数): ``shibuya.`` で始まるのに、木のどのモジュールにも包みにも解けない名(:func:`imported` が返す名に使う)。
- 読む試験: `tests/_head_copy_pin.py`・`tests/bench/test_refr20b_tool.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/c6/test_t3_parallel_invariance.py`・`tests/c8/test_places_rule_copies.py`・`tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/test_single_write_path.py`・`tests/engine/experiment/test_x33_form.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/processes/test_runner.py`・`tests/engine/rights/test_rights_from_w16.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/test_add_at_guard.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_two_phase.py`・`tests/engine/time/test_t0_no_tick_word.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/llm/test_fleet_contract.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/test_places_guard.py`・`tests/tools/test_repo_guide.py`・`tests/world/processes/test_declarations_1101.py`

## [_time_gates.py](../../../../../tests/_time_gates.py)

slow の試験の時間の門(壁時計の上限)を「記録だけ」にする切替(第333・3-2-4)。

- 公開の関数とクラス
  - `TimeGateWarning`(クラス): 時間の門を超えた(``SHIBUYA_TIME_GATES=record`` なので落とさず記録だけにした)。
  - `check`(関数): 時間の門の判定。既定は ``ok`` をそのまま返す(呼び手の ``assert`` が落とす)。
  - `recording`(関数): ``SHIBUYA_TIME_GATES=record`` か。
- 読む試験: `tests/build_pop/test_pop_pipeline.py`・`tests/engine/test_change_detect_p6.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_mock_day_w2.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_scheduler_p3.py`・`tests/engine/test_state_format_10f.py`
- 環境変数: `SHIBUYA_TIME_GATES`
- 決定の ID: 第 333

## [conftest.py](../../../../../tests/conftest.py)

tests 共通(ルート)。

- 公開の関数とクラス
  - `pytest_collection_modifyitems`(関数): 印 ``requires_data(<id>, ...)`` の id が 1 つでも無ければ、一律の理由で飛ばす。
  - `pytest_terminal_summary`(関数): id ごとの飛ばした数の表(合否にしない)。
- import している内部モジュール: `tests/_data_ids.py`
- 環境変数: `GITHUB_STEP_SUMMARY`・`PYTHONPATH`
- 決定の ID: 第 137・第 333

## [golden_env.py](../../../../../tests/golden_env.py)

golden を環境ごとの行で持つための小道具(10f・K26 (1))。

- 公開の関数とクラス
  - `GoldenUnregisteredWarning`(クラス): 今の環境が golden に登録されていない(golden とは比べず A/A だけを確かめた)。
  - `announce_once`(関数): 登録の有無を標準エラーに 1 回だけ書く(プロセスごと)。返り値=登録されているか。
  - `assert_aa`(関数): golden の行が無い環境の検査: 同じ設定で 2 回回し、``key`` の値が一致することを確かめる。1 回目の結果を返す。
  - `platform_id`(関数): 今の環境の ``platform_id``。
  - `row`(関数): ``{platform_id: 値}`` の表から今の環境の行(無ければ ``None``=未登録の警告を出す)。
  - `soa_combined`(関数): 〔第330・RET〕checkpoint の「SoA の全列+母集団+予定表(+活動)」の組み立て(10e より前の final の式)。
  - `warn_unregistered`(関数): 未登録の環境で golden の比較を飛ばしたことを警告する(pytest の要約に出る)。
- import している内部モジュール: `shibuya.engine.resume`・`shibuya.foundation.hashing`
- 読む試験: `tests/engine/space/test_nav1_world.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_wom.py`・`tests/perception/test_near_tiebreak.py`
- 決定の ID: 第 330

## [test_budget_table.py](../../../../../tests/test_budget_table.py)

予算宣言表リーダの検収(docs/design/v2-budget-declaration.md を正典として読む)。

- 公開の関数とクラス
  - `by_id`(関数)
  - `rows`(関数)
  - `test_bad_id_raises`(関数)
  - `test_category_matches_first_letter`(関数)
  - `test_core_series_is_33_rows`(関数): W1-W3・P1-P7・M1-M12・L1-L7・S1-S4 の33行が過不足なく揃っている。
  - `test_duplicate_id_raises`(関数)
  - `test_env_override`(関数)
  - `test_every_row_has_item_and_declared`(関数)
  - `test_id_set_and_row_count`(関数): 表の全行 = 中核33行 + I1(初期化予算)= 34行。
  - `test_parse_limit_cases`(関数)
  - `test_parse_limit_known_table_rows`(関数): 表の実セルからの抽出(best-effort だが主要行は当たること)。
  - `test_parse_limit_m8_from_table`(関数)
  - `test_parse_limit_m8_rss`(関数): M8 = RSS総額 ≤24GB(太字セル)。
  - `test_parse_limit_s1_storage`(関数): S1 = 恒久記録 ≤5GB/シミュ日(太字でないセルからも拾える)。
  - `test_rows_are_in_document_order`(関数)
  - `test_sections_are_1_to_5`(関数): §6(ハードウェアプロファイル)の表は読み込まれていない。
- import している内部モジュール: `shibuya.foundation.budget`
- 環境変数: `SHIBUYA_BUDGET_MD`

## [test_build_run_keep_stage.py](../../../../../tests/test_build_run_keep_stage.py)

``python -m shibuya.build.run`` の凍結段の口(``--keep-stage``)と安全弁(第281 親決定 Q2 (b))。

- 公開の関数とクラス
  - `fake_world`(関数): 全段階の偽ヘッダが在る out と、呼ばれた段を記録する偽の ``run_all``。
  - `test_keep_stage_and_stage_on_the_same_stage_is_a_usage_error`(関数)
  - `test_keep_stage_leaves_the_kept_outputs_and_header_untouched`(関数)
  - `test_keep_stage_refuses_a_header_whose_output_does_not_match`(関数): 保つ段の出力がヘッダと合わなければ、何も走らせずに止まる。
  - `test_refuses_to_overwrite_the_promoted_output_unless_the_stage_is_explicit`(関数): 安全弁: 昇格版の md5 に一致する出力は ``--stage`` の明示なしには上書きしない。
  - `test_the_protected_md5_is_the_promoted_w17_golden_key`(関数): 安全弁の md5 は golden 表の鍵(W17 v2・第168 昇格)と同じ値。実資産があれば当たることも見る。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.run`・`tests/_data_ids.py`
- 決定の ID: 第 168・第 281

## [test_child_imports_this_tree.py](../../../../../tests/test_child_imports_this_tree.py)

試験が起こす子プロセスは、この木(rootdir)の ``src`` の ``shibuya`` を import する(第333・3-2-4)。

- 公開の関数とクラス
  - `test_child_process_imports_shibuya_from_this_tree`(関数)
  - `test_this_process_imports_shibuya_from_this_tree`(関数)
- import している内部モジュール: `shibuya`
- 決定の ID: 第 333

## [test_cli.py](../../../../../tests/test_cli.py)

shibuya.cli(台帳つき実行入口)の検査。engine↛economy の層契約を守ったまま束ねる。

- 公開の関数とクラス
  - `test_apportioned_run_still_conserves_and_passes_the_census_gate`(関数)
  - `test_bundle_endows_stores_with_the_apportioned_amounts`(関数): 按分版でも注入は endow_stores(外界 → 店舗・ex nihilo 禁止)のまま。
  - `test_checkpoints_out_is_deterministic_across_two_runs`(関数): 同 seed 2 ランの checkpoint 列は全点一致(T2-a の形)。
  - `test_checkpoints_out_writes_the_t2_payload_that_c7_accept_reads`(関数): ``--checkpoints-out`` は checkpoint 列を JSON に出し、final_hash は summary と同じ値。
  - `test_cli_main_parses_and_runs`(関数)
  - `test_cli_no_population_flag_is_the_lower_bound_control`(関数): (軽-5) ``--no-population`` を cli にも用意する(engine.run と同じ意味)。
  - `test_cli_run_builds_ledger_and_census_on_synthetic_world`(関数)
  - `test_default_run_does_not_write_checkpoints_file`(関数)
  - `test_default_store_capital_is_apportioned_not_flat`(関数): 既定は経済センサス按分=カテゴリごとに額が違う(一律 200,000 ではない)。
  - `test_explicit_store_capital_still_overrides_with_a_flat_value`(関数)
  - `test_no_population_keeps_the_mock_wallet_path`(関数): 母集団を使わないランは C4 と同じ ``Ledger``(mock の一様財布)。
  - `test_store_capital_report_totals_match_the_array`(関数)
  - `test_wallet_ledger_substitutes_the_amounts_but_keeps_the_transfer_path`(関数): 注入の経路(外界 → 世帯・科目 CARRY_IN)は変えず、金額だけ差し替える。
  - `test_wallets_are_not_used_for_a_synthetic_world`(関数): 実データの母集団を合成小世界へ載せない(engine の判断と同じ)。
  - `test_wallets_come_from_the_anchor_table_and_are_deterministic`(関数): W16 母集団の種別 → ``anchors.initial_wallets``(対数正規)・同 seed 同結果。
- import している内部モジュール: `shibuya.cli`・`shibuya.economy.accounts`・`shibuya.economy.anchors`・`shibuya.economy.entry_capital`・`shibuya.world.model.state`・`tools/c7/c7_accept.py`
- 決定の ID: D-13・第 304

## [test_cli_help.py](../../../../../tests/test_cli_help.py)

`python -m shibuya.cli --help` が描けること(第342・R-130 が見つけた既存の不具合=help の文の `%` が`・` の前で書式の指定として読まれ ValueError になっていた。argparse の help では `%` は `%%` と書く)。

- 公開の関数とクラス
  - `test_help_renders_and_exits_zero`(関数)
- import している内部モジュール: `shibuya.cli`
- 決定の ID: R-130・第 342

## [test_cli_intent_mode.py](../../../../../tests/test_cli_intent_mode.py)

CLI ``--intent-mode {vocab,open,hint}``(AB7 自由意図の腕の切替口・仕様書 §2 の表)。

- 公開の関数とクラス
  - `test_cli_choices_come_from_the_templates_module`(関数): choices は ``templates.INTENT_MODES`` が正典(文字列を CLI 側に二重に持たない)。
  - `test_cli_main_has_the_intent_mode_flag`(関数)
  - `test_cli_run_defaults_to_vocab`(関数)
  - `test_cli_run_passes_intent_mode_through_kwargs`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.foundation.text.templates`
- 決定の ID: 第 277

## [test_cli_l4_scale.py](../../../../../tests/test_cli_l4_scale.py)

CLI ``--l4-scale FACTOR``(L4 呼数予算の倍率・PENDING D-99 (a)・腕 AB8-L4-SCALE)。

- 公開の関数とクラス
  - `test_a_negative_factor_is_a_usage_error`(関数): 負の倍率は traceback ではなく usage で落とす(``--signage-p-see`` と同じ作法)。
  - `test_an_explicit_budget_wins_over_the_factor`(関数): ``budget`` を直に渡した呼び出しは倍率より優先(倍率は 1.0 のまま manifest に載る)。
  - `test_cli_main_has_the_l4_scale_flag`(関数)
  - `test_cli_run_rejects_a_negative_factor`(関数)
  - `test_fleet_x_unlimited_queue_capacity_defaults_to_the_agent_count`(関数): 第289 Q28(D-55): 艦隊 × 無制限 × 枠 未指定 → 枠の既定=体数(``FleetConfig`` を差し替え・manifest に載る)。
  - `test_fleet_x_unlimited_without_a_queue_capacity_is_noted_when_it_cannot_be_fixed`(関数): 艦隊 × 無制限で ``--fleet-queue-capacity`` が未指定かつ枠が体数未満なら注記の文(D-55)。
  - `test_the_default_is_unlimited_and_identical_with_the_explicit_0`(関数): 3 段目(D-99 (a′)・D-110): CLI と ``cli.run`` の既定は **0=無制限**(``CLI_DEFAULT_L4_SCALE``)。
  - `test_the_explicit_1_0_is_the_old_l4_share`(関数): ``--l4-scale 1`` で旧挙動(L4 按分・持ち越し 2 tick)。ライブラリ ``run_day`` の既定と同じ。
  - `test_the_factor_multiplies_the_l4_share`(関数)
  - `test_the_manifest_always_carries_the_l4_audit_fields`(関数)
  - `test_zero_means_one_call_per_agent_per_tick`(関数): ``0`` = **無制限**。アービタは合流後に体あたり高々 1 件なので体数で足りる。
- import している内部モジュール: `shibuya.cli`・`shibuya.engine.arbiter`・`shibuya.engine.run`・`shibuya.llm.fleet`
- 決定の ID: D-55・D-99・D-110・第 277・第 289

## [test_cli_vocab_version.py](../../../../../tests/test_cli_vocab_version.py)

CLI ``--vocab-version {v1,v2}``(語彙成長 v0 の切替口・D-71 §3 F)。

- 公開の関数とクラス
  - `test_cli_choices_come_from_the_templates_module`(関数): choices は ``templates.VOCAB_VERSIONS`` が正典(文字列を CLI 側に二重に持たない)。
  - `test_cli_default_is_v3_but_the_library_default_stays_v1`(関数): 第277: CLI の既定だけが v3。ライブラリの既定(=退化検査・golden の切替口)は v1 のまま。
  - `test_cli_main_has_the_activity_flag`(関数): 二層の段 2: ``--activity {on,off}``(既定 on)が ``run(activity=...)`` へ届く。
  - `test_cli_main_has_the_vocab_version_flag`(関数)
  - `test_cli_run_defaults_to_v1`(関数)
  - `test_cli_run_passes_vocab_version_through_kwargs`(関数)
  - `test_intent_mode_and_vocab_version_are_orthogonal`(関数): 3 腕 × 2 版のどの組み合わせでも回り、manifest に両方が載る。
  - `test_open_and_hint_arms_need_an_explicit_v1_or_v2_on_the_cli`(関数): v3 の B0 は vocab 腕だけ=CLI の既定(v3)のまま open/hint を頼むと usage で落とす。
  - `test_the_default_run_is_byte_identical_with_the_explicit_v1`(関数)
- import している内部モジュール: `shibuya.cli`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`
- 決定の ID: D-71・第 274・第 276・第 277

## [test_fixture_holiday_csv.py](../../../../../tests/test_fixture_holiday_csv.py)

祝日の fixture(``tests/fixtures/calendar/syukujitsu.csv``)が内閣府の CSV のバイトのままであること(第333)。

- 公開の関数とクラス
  - `test_holiday_fixture_is_byte_identical_to_the_cabinet_office_csv`(関数)
- 決定の ID: 第 333

## [test_manifest_roundtrip.py](../../../../../tests/test_manifest_roundtrip.py)

U8 run manifest: 往復一致・自己ハッシュ(T1)・機械化される規則のテスト。

- 公開の関数とクラス
  - `test_batch_invariant_required_for_verification`(関数): 規則(c): 検証ランは sha256_cbor + VLLM_BATCH_INVARIANT=1。
  - `test_clean_hardware_and_output_accepted`(関数): 規則(d)の偽陽性検査: 版番号(3成分)や相対パスは通る。
  - `test_diag_columns_required_for_calibration`(関数): 規則(e)/T9: 較正・holdout は診断行4列+保存則2検算が必要。
  - `test_dirty_rejected_for_holdout`(関数): 規則(a): dirty=true は較正・holdout に使えない。
  - `test_extra_field_forbidden`(関数): extra="forbid": 知らない欄は拒否(欄の作り足しを検出)。
  - `test_field_change_changes_run_id`(関数): 本文の1欄が変われば run_id が変わる(封印後の変更は新 run_id)。
  - `test_ip_in_hardware_rejected`(関数): 規則(d): ハードウェア節・出力節に IP / URL を書かない。
  - `test_key_order_and_whitespace_invariance`(関数): YAML のキー順・字下げ・改行幅・引用符は run_id に影響しない。
  - `test_manifest_is_frozen`(関数): frozen=True: 読み込み後の書き換えを禁止(押印後の改変防止)。
  - `test_opened_layer_rejected_outside_holdout`(関数): 規則(b): mode≠holdout で opened=true があれば起動拒否。
  - `test_rng_scheme_is_fixed_literal`(関数): 乱数方式は numpy-philox4x64 固定(実装計画書§2 部品表)。
  - `test_roundtrip_yaml`(関数): load → with_run_id → dump → load でモデルも正規化本文も一致する。
  - `test_run_id_mismatch_detected`(関数): 記録された run_id が本文と食い違えば verify は False。
  - `test_t1_self_hash`(関数): T1: run_id = blake3(正規化本文)。run_id 自身は本文に入らない。
- import している内部モジュール: `shibuya.foundation.manifest.canonical`・`shibuya.foundation.manifest.schema`

## [test_manifest_rules_extra.py](../../../../../tests/test_manifest_rules_extra.py)

manifest 機械化規則の追加検査(層2レビュー指摘・C0出口): MARLIN atomic add の禁止・phases の固定列。

- 公開の関数とクラス
  - `test_fixture_declares_marlin_atomic_add_off`(関数)
  - `test_marlin_atomic_add_not_enforced_for_smoke`(関数)
  - `test_marlin_atomic_add_required_for_verification_modes`(関数)
  - `test_phases_are_fixed_sequence`(関数)
- import している内部モジュール: `shibuya.foundation.manifest.schema`

## [test_places_guard.py](../../../../../tests/test_places_guard.py)

``tests/_places.py`` の対応表の確かめ(検収 M-2)と、解けない名の扱い(検収 L-1)。

- 公開の関数とクラス
  - `non_move_rows`(関数): 表の move でない行の old と、move で old と new が同じ行の old。
  - `test_a_fake_tree_maps_moves_and_allows_only_empty_new_heads`(関数)
  - `test_a_map_missing_one_row_stops`(関数): 1 行欠けた(古い)表: 今の木にある ``cli.py`` の行を抜くと、``cli.py`` が表に無いファイルとして止まる。
  - `test_a_map_with_renamed_row_keys_stops`(関数)
  - `test_a_non_move_row_for_a_new_file_is_caught_and_a_move_row_is_not`(関数): 負の対照: 新しい置き場のファイルを道が変わらない行(keep・split・delete・empty か、old と new が同じ move)で載せた表は
  - `test_an_empty_or_foreign_map_stops`(関数)
  - `test_current_index_stops_when_two_files_share_one_origin`(関数): 〔再検収 L-7〕2 つの今のファイルが同じ元の道を持てば ``current_of`` の索引は止める。
  - `test_declared_path_now_reads_the_origin_first_then_the_tree`(関数): 〔再検収 L-6〕宣言の道は、表の元の道として引ければ今の道へ・引けなければ今の木に在るか・どちらでもなければ止める。
  - `test_rows_that_keep_their_place_are_frozen`(関数): 〔再検収 M-4・L-8〕道が変わらない行(move でない行と、move で old と new が同じ行)は黙って足せない: 表の集合が固定の
  - `test_the_real_map_explains_the_current_tree`(関数)
  - `test_unresolvable_shibuya_names_are_hits`(関数): 検収 L-1: 木のどのモジュールにも包みにも解けない ``shibuya.`` の名は、層の試験の違反(``Names.hits``)。
- import している内部モジュール: `shibuya.cli`・`tests/_places.py`

## [test_rng_properties.py](../../../../../tests/test_rng_properties.py)

core.rng の性質テスト(hypothesis)。運用設計書 §1.4 T4(規模不変性)と G-5(決定的写像)を機械化。

- 公開の関数とクラス
  - `test_domain_separation`(関数): ドメインが違えば鍵が違う(同じドメイン名なら同じ鍵)。
  - `test_known_answer_is_stable`(関数): 既知解(golden・2026-09-08 固定): 変わったら鍵導出規約か numpy の Philox が変わった=宣言して更新する。
  - `test_master_seed_str_and_int_are_distinct_domains`(関数): run_id(16進文字列)と整数 seed を取り違えても同じ鍵にならない。
  - `test_rejects_bad_inputs`(関数)
  - `test_same_inputs_same_stream`(関数)
  - `test_t4_scale_invariance`(関数): 個体 agent_id の列は、個体総数(5,000 か 5,001 か)に依存しない=カウンタベースの実証(T4)。
- import している内部モジュール: `shibuya.foundation.rng`

## [test_world_catalog_sha.py](../../../../../tests/test_world_catalog_sha.py)

世界カタログ(被覆指標の分母)の凍結検収。

- 公開の関数とクラス
  - `table`(関数)
  - `test_columns`(関数): (4) 列名9つが凍結時の通り。
  - `test_freeze_reproduces_packaged_json_byte_for_byte`(関数): (5) freeze() の再実行が同梱 JSON をバイト単位で再現する。
  - `test_manifest_does_not_import_build`(関数): 層契約の自己点検: manifest 単体を新規プロセスで import しても build を引かない。
  - `test_markdown_is_lf_only`(関数): SHA 規則は実バイト依存 — CRLF が混ざったら SHA が動く。
  - `test_packaged_catalog_matches_frozen`(関数): (2) 同梱 JSON の SHA・クラス数が凍結値と一致する。
  - `test_parse_catalog_rows_matches_packaged`(関数)
  - `test_row_numbers_are_1_to_57`(関数): (3) `#` 列は "1".."57" で重複がない。
  - `test_sha16_recomputed_from_markdown`(関数): (1) Markdown から再計算した SHA が凍結値と一致する。
  - `test_verify_frozen_rejects_drift`(関数)
- import している内部モジュール: `shibuya.build.catalog_freeze`・`shibuya.world.ledger.world_catalog`
