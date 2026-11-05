# tests/core

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/core/__init__.py)

core 層のテスト。

## [test_growth.py](../../../../../../tests/core/test_growth.py)

core.growth のテスト: **D-R2-6 の 5 欄が正典**+24step→1日/30日外挿。

- 公開の関数とクラス
  - `test_bad_steps_rejected`(関数)
  - `test_declaration_validation`(関数)
  - `test_declared_over_cap_fails_without_any_measurement`(関数): 宣言だけで cap を食い破る設計は実測を待たずに落ちる。
  - `test_declared_projection_by_order`(関数)
  - `test_extrapolation_arithmetic_is_linear`(関数): 実測 1,666B/24step → 100,000B/日 → 30日 3,000,000B(cap 10MB 内)。
  - `test_five_canonical_fields_are_required`(関数): D-R2-6 の 5 欄はキーワード必須(欠けたら TypeError)。
  - `test_growth_order_validation`(関数)
  - `test_missing_and_unknown_measurements_fail`(関数)
  - `test_old_fields_are_now_optional_records`(関数): 旧必須欄(unit/bytes_per_unit/growth_per_simday)は任意の記録欄に降格。
  - `test_on_t_declaration_requires_a_reason_it_cannot_be_aggregated`(関数): D-R2-6「O(N·t) 以上は宣言必須+なぜ集約できないかを記す」。
  - `test_over_cap_fails`(関数): 二乗爆発(runB 教訓)の検出: 1日 1GB は 30日で cap 10MB を必ず超える。
  - `test_over_declared_is_reported_but_not_a_failure`(関数): 実測が宣言を超えたら「delta 改訂が要る」印だけ立てる(cap 内なら失敗にしない)。
  - `test_retention_requires_a_target_when_bounded`(関数): D-R2-6「生ログ保持日数**と圧縮先**」——日数だけの宣言は不完全。
  - `test_retention_window_caps_the_horizon`(関数): 保持窓 7 日なら 30 日外挿でも 7 日分しか積まない(D-R2-6 の日次集約+保持窓)。
  - `test_steady_bytes`(関数)
  - `test_yaml_row_has_exactly_the_five_canonical_keys`(関数)
- import している内部モジュール: `shibuya.core.growth`

## [test_serialize.py](../../../../../../tests/core/test_serialize.py)

core.serialize のテスト: checkpoint 往復一致と M7(膨張率 ≤2.0x)。

- 公開の関数とクラス
  - `test_empty_registry_roundtrip`(関数)
  - `test_load_detects_tampering`(関数)
  - `test_property_roundtrip_preserves_state_hash`(関数)
  - `test_roundtrip_and_m7_bloat`(関数)
  - `test_zeros_registry_shows_why_denominator_matters`(関数): 全ゼロ=zstd がよく効く場合。非圧縮基準の比は 1.0 付近、圧縮後基準は跳ね上がる。
- import している内部モジュール: `shibuya.core.serialize`・`shibuya.core.soa`

## [test_soa.py](../../../../../../tests/core/test_soa.py)

core.soa のテスト: M9(宣言なきフィールドはマージ不可)と state_hash の性質。

- 公開の関数とクラス
  - `test_agent_cap_comes_from_budget_row_m1`(関数): 個体あたり上限は予算行 M1(≤30KB/体)。KB は 10 進(M3 の 64×200B=12.8KB より)。
  - `test_attribute_and_field_access`(関数)
  - `test_budget_report_declared_vs_actual`(関数)
  - `test_cell_registry_has_no_per_entity_cap_row`(関数)
  - `test_declare_rejects_actual_over_declared_and_total_over_cap`(関数)
  - `test_declare_requires_budget_tag_and_doc`(関数)
  - `test_duplicate_and_bad_names_rejected`(関数)
  - `test_property_state_hash_changes_iff_bytes_change`(関数): 性質: state_hash が変わる ⟺ 配列のバイト列が変わる。
  - `test_state_hash_changes_on_any_byte_change`(関数)
  - `test_state_hash_is_stable_and_order_sensitive`(関数)
- import している内部モジュール: `shibuya.core.budget`・`shibuya.core.soa`

## [test_types_hashing.py](../../../../../../tests/core/test_types_hashing.py)

core.types / core.hashing のテスト(golden 値の凍結を含む)。

- 公開の関数とクラス
  - `test_array_variant_rejects_ragged_columns`(関数)
  - `test_array_variants_match_scalar`(関数)
  - `test_blake3_known_vector`(関数): blake3 の空入力(公開既知ベクトル)。
  - `test_class_rank_values_match_design_2_5`(関数): 運用設計書 §2.5: institution −1・conversation 0・plan_boundary 1・individual 2・cell 3。
  - `test_domain_tags_separate_uses`(関数): 同じ (salt, tick, id) 三つ組でも用途が違えば別の値(用途タグ)。
  - `test_dtypes_are_fixed`(関数)
  - `test_id_range_checks`(関数)
  - `test_priority_apply_wake_keys_are_pinned`(関数)
  - `test_priority_key_determinism_and_range`(関数)
  - `test_sha256_cbor_and_xxh64_are_pinned`(関数)
  - `test_t_sim_ns_overflow_is_loud`(関数): int64 の限界(60秒tickで約 292 年)を黙って回さない。
  - `test_t_sim_ns_rejects_out_of_range_offset`(関数)
  - `test_t_sim_ns_roundtrip`(関数)
- import している内部モジュール: `shibuya.core.hashing`・`shibuya.core.types`
