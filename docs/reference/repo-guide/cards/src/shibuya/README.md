# src/shibuya

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [act](act/README.md)・[build](build/README.md)・[economy](economy/README.md)・[experiments](experiments/README.md)・[foundation](foundation/README.md)・[interfaces](interfaces/README.md)・[interim_bundles](interim_bundles/README.md)・[mind](mind/README.md)・[runtime](runtime/README.md)・[society](society/README.md)・[validation](validation/README.md)・[world](world/README.md)

## [__init__.py](../../../../../../src/shibuya/__init__.py)

shibuya-simulation-v2: 現実の渋谷を舞台にしたLLM社会シミュレーション第2世代(エンジン)。

- 呼び手: `tools/bytecheck/check.py`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/engine/state/test_move_prep_stage2.py`・`tests/engine/state/test_names_frozen.py`・`tests/test_child_imports_this_tree.py`
- 読む試験(道筋で): `tests/_head_copy_pin.py`・`tests/_places.py`・`tests/c8/test_places_rule_copies.py`・`tests/engine/test_two_phase.py`・`tests/test_places_guard.py`・`tests/tools/test_bytecheck.py`・`tests/tools/test_ci_check_test_shards.py`・`tests/tools/test_dm_eval.py`・`tests/tools/test_pkgmove.py`・`tests/tools/test_repo_guide.py`

## [cli.py](../../../../../../src/shibuya/cli.py)

shibuya.cli — ``python -m shibuya.cli`` の入口(外との約束)。中身は ``shibuya.interfaces.cli.main``(割る段 5b)。

- import している内部モジュール: `shibuya.interfaces.cli.main`
- 読む試験(道筋で): `tests/economy/test_wage_occupation.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_norm_meter.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_wom.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_p_see_activity.py`・`tests/test_places_guard.py`・`tests/tools/test_bytecheck.py`・`tests/tools/test_pkgmove.py`・`tests/tools/test_pkgmove_shapecheck.py`
