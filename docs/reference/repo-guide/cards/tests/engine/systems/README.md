# tests/engine/systems

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 1 本(このディレクトリの直下)

その他のファイル: `writes_soa_frozen.json`

## [__init__.py](../../../../../../../tests/engine/systems/__init__.py)

(冒頭の説明なし)

## [test_boxes.py](../../../../../../../tests/engine/systems/test_boxes.py)

1-0 段 C: 状態の箱・局所の割り当ての表(漏れ 0)・scratch の番兵(T4)と書きの宣言(段 C)・持ち主の名と順。

- 公開の関数とクラス
  - `test_box_targets_exist`(関数)
  - `test_every_local_of_run_day_is_assigned`(関数): 段 C の門(草案 §2-3〔改訂 K8〕): HEAD の run_day の局所 450 個に割り当て無しが 0。
  - `test_owner_names_match_the_hash_owners`(関数)
  - `test_run_day_signature_is_unchanged_and_build_unpacks_every_argument`(関数): 草案 §3-3 の 3: 設定の指紋 ``_call_args = dict(locals())`` は run_day の頭のまま。組み立ては引数を全部結ぶ。
  - `test_scratch_fields_cover_the_table`(関数)
  - `test_scratch_reset_keeps_buffers`(関数): R1: ``focus_request`` は scratch でなく ``Buffers``(tick の頭で空にしない)。
  - `test_scratch_write_outside_the_declaration_fails`(関数)
  - `test_strict_scratch_raises_on_read_before_write`(関数)
  - `test_tick_ctx`(関数)
- import している内部モジュール: `shibuya.core.write_permit`・`shibuya.engine.run`・`shibuya.engine.systems.boxes`・`shibuya.engine.systems.guard`・`shibuya.engine.systems.state_io`
- 決定の ID: 11-01

## [test_fix_guards.py](../../../../../../../tests/engine/systems/test_fix_guards.py)

1-0 段 FIX(検収 review-impl-1-0.md §1 の 1〜10): 「宣言の外を書いたら落ちる」の穴を塞いだ検査と負の対照。

- 公開の関数とクラス
  - `bypass_setattr_sites`(関数): ``object.__setattr__(…)``(箱の ``__setattr__`` の段 C を素通りする)を系のモジュールで使う行。
  - `d2_mismatches`(関数): 凍結の表と食い違う系の名(閉包を ``resolve_ops`` から計算し直したもの・系が持つ ``writes.soa`` の両方を見る)。
  - `d6_hits`(関数): 層の属性(``X.attr = …``・組の代入の要素)に SoA の配列・ビュー・別名を入れる行。
  - `permit_offenders`(関数)
  - `soa_ish`(関数): 式が SoA の配列・ビュー・登録表を指すか(別名 ``aliases`` は局所の名)。
  - `test_bypass_setattr_check_catches_a_planted_line`(関数): 負の対照(検収 L4b): ``object.__setattr__(b.scratch, "outcome", …)`` が見つかる。
  - `test_d1_sees_plain_imports_and_other_aliases`(関数): 負の対照(検収 L9): resolve の口を素の import・別の別名で呼んでも ``resolve_calls`` に出る。
  - `test_d2_detects_a_widened_or_narrowed_permit`(関数): 負の対照(D②・検収 §1 の 10): 系の ``resolve_ops`` に口を 1 つ足す(許可が広がる)・1 つ外す(狭まる)と、
  - `test_d2_writes_soa_matches_the_frozen_table`(関数): D②: 系の書く SoA の列(resolve の口の閉包)が、凍結して確かめた表と同じ。resolve.py の書きが変わったり
  - `test_d3_tally_writes_through_tuple_aliases_are_seen`(関数): 検収 §1 の 7: 組の代入の別名(``a, b = rs.x, rs.y``)と ``rs.<欄>`` の別名を通した書きも積算の書きに数える。
  - `test_d6_finds_the_alias_forms`(関数): 負の対照(検収 §1 の 5): 9 つの形のうち AST で追える 8 つが見つかる(np.asarray の写しは dtype で写しかビューか
  - `test_d6_no_layer_holds_a_soa_array_view_or_alias`(関数)
  - `test_permit_check_catches_planted_switches`(関数): 負の対照(検収 L2・L11): 系と層から許可を外す口を呼ぶ・大域を書き換えると見つかる。
  - `test_permit_check_catches_reexported_names`(関数): 負の対照(再検収 R1・段 FIX2): 再輸出の名 ``_WP`` を通して許可を外す形が見つかる。
  - `test_permit_switches_are_called_only_from_known_places`(関数)
  - `test_systems_modules_do_not_bypass_the_box_setattr`(関数): 系のモジュール(箱の定義 ``boxes.py`` の外)は ``object.__setattr__`` を使わない(段 C を素通りしない)。
- import している内部モジュール: `shibuya.core.write_permit`・`shibuya.engine.state_ledger_ast`・`shibuya.engine.systems.allow`・`shibuya.engine.systems.boxes`・`shibuya.engine.systems.guard`・`shibuya.engine.systems.static_check`・`shibuya.engine.systems.table`・`tests/_places.py`

## [test_guard_runs.py](../../../../../../../tests/engine/systems/test_guard_runs.py)

1-0: 書きの検査をランの単位で確かめる(草案 §3-1 の T1〜T4・合成世界の小さなラン)。

- 公開の関数とクラス
  - `base_final`(関数)
  - `test_box_rooted_ufunc_at_outside_resolve_is_caught_by_B`(関数): 検収 L1 の実行時の側: resolve の外の ``np.add.at(b.soa.agents.registry.money, …)`` は段 A では止まらない
  - `test_buffers_replacement_outside_the_declaration_fails`(関数): 負の対照(検収 L5・段 C): 宣言の無い系が ``b.buffers.focus_request`` を差し替えると ``AttributeError``。
  - `test_declared_writes_cover_the_observed_changes`(関数): 段 B(正): 系の前後で変わった欄 ⊆ 宣言(SoA・外の道筋・積算・buffers)。
  - `test_declared_writes_cover_the_observed_changes_including_scratch`(関数): 段 B(正・段 FIX): scratch の中身(配列・dataclass・物の属性)まで含めて、変わった欄 ⊆ 宣言。
  - `test_dropping_a_column_fails_where_it_is_written`(関数)
  - `test_dropping_a_path_shows_up_in_the_per_system_diff`(関数)
  - `test_dropping_a_scratch_field_fails`(関数)
  - `test_guard_on_and_off_give_the_same_final`(関数)
  - `test_scratch_in_place_write_by_a_non_writer_shows_in_B`(関数): 負の対照(検収 L4): 書き手でない phase_c が scratch.plan の中身をその場で書き換えると、段 B が phase_c に出す。
  - `test_strict_scratch_no_stale_reads`(関数): T4: tick の頭で scratch を番兵で埋めても読む前に書かれている(final も同じ)。
- import している内部モジュール: `shibuya.core.write_permit`・`shibuya.engine.run`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.overrides`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.table`

## [test_stage_a_guard.py](../../../../../../../tests/engine/systems/test_stage_a_guard.py)

1-0 段 A: 系ごとの書きの許可(``core.write_permit``)・配列単位の ``_require_thawed``・静的な検査 D④⑤⑥⑦・閉包の道具。

- 公開の関数とクラス
  - `test_alias_table_covers_ledger_money_writes`(関数)
  - `test_closure_follows_tables_and_local_aliases`(関数)
  - `test_closure_is_an_upper_bound_of_resolve_ops`(関数)
  - `test_d5_detector_catches_a_planted_flag_write`(関数): 負の対照(T2・D ⑤): 決まった場所の外で旗を立てる行をわざと書くと見つかる。
  - `test_d6_detector_catches_a_planted_alias`(関数): 負の対照(T2・D ⑥): 層の属性に SoA の列のビューを持たせる行をわざと書くと見つかる。
  - `test_direct_flag_writes_live_only_in_known_places`(関数)
  - `test_every_state_ufunc_at_in_resolve_checks_the_written_array`(関数)
  - `test_no_layer_holds_a_soa_array_or_view_as_an_attribute`(関数)
  - `test_no_permit_means_everything_thaws_as_before`(関数)
  - `test_numpy_ufunc_at_still_ignores_the_flag`(関数): 穴の実在(この振る舞いが変われば配列単位の検査は要らなくなる)。
  - `test_perception_state_thaws_only_permitted_columns`(関数)
  - `test_require_thawed_checks_each_array`(関数)
  - `test_scope_nests_and_restores`(関数)
  - `test_set_refractory_ufunc_at_is_blocked_outside_the_permit`(関数): 負の対照(T1・refractory_until): ``np.maximum.at`` は旗を見ないので配列単位の検査が止める。
  - `test_switch_off_restores_the_old_full_thaw`(関数)
  - `test_systems_package_never_thaws`(関数)
  - `test_writable_thaws_only_permitted_columns`(関数)
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.write_permit`・`shibuya.engine.resolve`・`shibuya.engine.state_ledger_ast`・`shibuya.engine.systems.allow`・`shibuya.perception.state`・`shibuya.world.state`・`tests/_places.py`

## [test_systems_table.py](../../../../../../../tests/engine/systems/test_systems_table.py)

1-0: 系の宣言の表 ``SYSTEMS`` の約束(草案 §2-2・§2-5・§2-6 の D ①②③⑧)。

- 公開の関数とクラス
  - `test_d1_d3_code_matches_the_declaration`(関数)
  - `test_d2_writes_soa_is_the_static_closure`(関数)
  - `test_d3_detects_undeclared_reads_and_writes`(関数): 負の対照(T2・D ③): 宣言に無い箱の属性の参照・scratch の書き・resolve の口の呼び出しが見つかる。
  - `test_d8_written_keys_exist_in_the_ledger`(関数)
  - `test_every_scratch_field_has_a_writer_and_a_reader`(関数)
  - `test_order_and_counts`(関数)
  - `test_scratch_is_written_before_it_is_read_in_tick_order`(関数)
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.engine.state_ledger`・`shibuya.engine.systems.allow`・`shibuya.engine.systems.boxes`・`shibuya.engine.systems.spec`・`shibuya.engine.systems.static_check`・`shibuya.engine.systems.table`
