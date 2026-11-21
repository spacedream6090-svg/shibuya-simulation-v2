# tests/build_geo

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/build_geo/__init__.py)

(冒頭の説明なし)

## [test_c9c_walkable_area.py](../../../../../../tests/build_geo/test_c9c_walkable_area.py)

C9c-1 歩行可能面積の実測化(``tools/build_geo/walkable_area.py``)の検収。

- 公開の関数とクラス
  - `test_build_is_deterministic_and_refuses_to_overwrite`(関数)
  - `test_clip_preserves_area_across_four_cells`(関数): セル境界(100 m)にまたがる 200×200 m の正方形 → 4 セルに 10,000 m² ずつ。
  - `test_default_build_has_no_cell_above_its_own_area`(関数): **物理検査**: 100 m セルに 10,000 m² を超える道路面は入らない。
  - `test_default_covered_min_frac_is_declared`(関数): 被覆の 2 条件の既定(親決定 2026-09-17): 被覆率 ≥ 0.5 かつ 歩道率 ≥ 0.15。
  - `test_function_codes_follow_the_plateau_codelist`(関数): 2000 歩道部 / 2010 自転車歩行者道 / 2020 歩道 と 1000 車道部 / 1020 車道交差部。
  - `test_gate_ii_fails_when_the_median_leaves_the_band`(関数)
  - `test_gate_iii_fails_above_the_district_total`(関数)
  - `test_gate_values_pass_on_synthetic_numbers`(関数)
  - `test_gml_reader_reproduces_the_advisory_counts_and_areas`(関数): 答申 a8(地物数・LOD3 の内訳)と a9(区全域の面積)を**地物単位の数え方**で再現する。
  - `test_lod_merge_modes_and_ring_dedup_modes`(関数)
  - `test_merge_cell_areas_by_lod_prefers_lod3_per_cell`(関数)
  - `test_npz_source_still_builds`(関数): ``--source npz``(GML の無い環境用)も動く。値は LOD3 + clip_rect の部分集合。
  - `test_polyline_cell_lengths_handles_diagonals`(関数)
  - `test_polyline_cell_lengths_split_on_cell_boundaries`(関数)
  - `test_real_asset_header_records_the_three_gates`(関数): 出荷済み資産のヘッダに S7 の 3 ゲートが値つきで載っている。
  - `test_ring_dedup_removes_the_sixfold_repetition`(関数): LOD3 の環は 6 重。畳むと環数も面積も減る(答申の 897,556 m² は重複込み)。
  - `test_road_surface_width_follows_the_lane_width_table`(関数): 道路構造令 第五条第4項(第四種第一級 3.25 / 第二級・第三級 3.0)+ 第十一条第3項 2.0×2。
  - `test_triangle_cell_areas_conserve_the_total`(関数): 三角形の集合をセルに割り振っても合計は動かない(跨ぐものも含む)。
  - `test_triangle_straddling_one_boundary_splits_in_half`(関数)
  - `test_unique_rings_folds_repeated_and_reversed_rings`(関数): 渋谷区 2025 の LOD3 TrafficArea は**同じ三角形を 6 回**持つ(実測)。
  - `test_unique_rings_keeps_holes_apart_from_the_same_outer_ring`(関数): 符号が違えば別物(外環と同じ形の穴は畳まない)。
  - `test_unique_triangle_mask_folds_repeated_faces`(関数): PLATEAU の npz は同じ面を 2〜6 回持つ(S1「1 地物 1 LOD=二重計上しない」)。
  - `test_width_rules_match_the_road_structure_ordinance`(関数): 道路構造令 11 条 3 項 2.0 m / 10 条の 2 2 項 3.0 m / 5 条 5 項 4.0 m(答申 §1-1)。
- import している内部モジュール: `tests/_data_ids.py`

## [test_geo_pipeline.py](../../../../../../tests/build_geo/test_geo_pipeline.py)

build.geo の統合テスト(実データ必須・CI では skip)。

- 公開の関数とクラス
  - `built`(関数)
  - `test_all_gates_pass`(関数)
  - `test_catalog_classes_declared`(関数)
  - `test_cli_partial_stage`(関数)
  - `test_next_hop_matrix_shape_and_dtype`(関数)
  - `test_outputs_exist_and_hashes_match`(関数)
  - `test_rebuild_is_reproducible`(関数)
  - `test_runtime_budget`(関数)
  - `test_spec_numbers`(関数)
  - `test_stage_order_is_w_order`(関数)
  - `test_w6_raw_tag_cat_conflicts_are_the_three_review_candidates`(関数): 生タグの subcat が v8 の cat と矛盾して捨てられた件数(対の閉包を守る不変条件)。
  - `test_w6_subcat_is_rebuilt_from_raw_osm_tags`(関数): W6 subcat 改訂(2026-09-17)+ 2026-09-28 の Overpass 再取得(段 1a)を実データで固定する。
- import している内部モジュール: `shibuya.build.geo`・`shibuya.build.geo.common`・`shibuya.build.geo.run`・`shibuya.build.geo.w6_poi_org`・`tests/_data_ids.py`
- 決定の ID: D-97・第 281

## [test_geo_units.py](../../../../../../tests/build_geo/test_geo_units.py)

build.geo の純粋ヘルパの単体テスト(データ不要)。

- 公開の関数とクラス
  - `test_band_of_layer`(関数)
  - `test_band_of_layer_rejects_unknown`(関数)
  - `test_build_csr_dedups_parallel_edges_with_min_length`(関数)
  - `test_canonical_json_is_key_sorted_and_compact`(関数)
  - `test_count_components_two_islands`(関数)
  - `test_face_traversal_on_single_triangle`(関数)
  - `test_gate_to_json_pass_semantics`(関数)
  - `test_grid_ij_floor_semantics`(関数)
  - `test_height_rule_priority`(関数)
  - `test_input_hash_is_order_dependent`(関数)
  - `test_kind_default_h_is_floors_times_3`(関数)
  - `test_kind_default_table_covers_v8_kinds`(関数)
  - `test_latlon_to_local_origin_and_scale`(関数)
  - `test_node_layer_majority_plain`(関数)
  - `test_node_layer_majority_tie_prefers_zero`(関数)
  - `test_node_layer_majority_tie_without_zero_takes_smallest_abs`(関数)
  - `test_param_hash_is_order_independent`(関数)
  - `test_place_id_format`(関数)
  - `test_prune_pendants_dissolves_tree`(関数)
  - `test_prune_pendants_removes_chain_keeps_cycle`(関数)
  - `test_ring_stats_unit_square`(関数)
  - `test_stage_result_header_roundtrip`(関数)
  - `test_write_parquet_is_byte_stable`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.geo.w1_walk_graph`・`shibuya.build.geo.w2_cells`・`shibuya.build.geo.w3_distances`・`shibuya.build.geo.w4_heights`

## [test_poi_class.py](../../../../../../tests/build_geo/test_poi_class.py)

W6 POI 分類(``build.geo.poi_class``)の単体テスト(データ不要・CI で常に走る)。

- 公開の関数とクラス
  - `test_a_bookshop_poi_is_reachable_by_subcat_and_stays_a_shop`(関数)
  - `test_a_library_poi_is_reachable_by_subcat`(関数)
  - `test_a_park_poi_now_routes_to_place_park`(関数): 合成の POI 行: OSM タグ leisure=park → subcat=park → 場所語「公園」。
  - `test_catsub_pairs_closure_matches_topcat_table`(関数)
  - `test_every_name_rule_has_a_topcat`(関数)
  - `test_every_tag_rule_has_a_topcat`(関数)
  - `test_name_rules_do_not_cross_the_cat`(関数): 「代々木公園陸上競技場」は cat=hall。名前に「公園」があっても park にしない。
  - `test_only_park_changes_the_place_word_among_the_new_subcats`(関数): 新しい subcat のうち、場所語を変えるのは park だけ(場所語 12 語は不変)。
  - `test_pattern_ledger_gate_every_subcat_states_its_use`(関数): パターン台帳ゲート: どの現実パターン照合で使うか 1 行で書けない語は足さない。
  - `test_place_park_is_not_in_the_opening_envelope`(関数): 公園に開店時刻は無い(営業エンベロープを掛けない)。
  - `test_poi_category_from_raw_tags`(関数)
  - `test_poi_category_keeps_park_in_leisure_cat`(関数): cat の語彙は動かさない。公園は cat=leisure のまま、subcat で分ける。
  - `test_poi_category_stays_inside_the_frozen_cat_vocabulary`(関数)
  - `test_poi_subcategory_from_raw_tags`(関数)
  - `test_poi_subcategory_is_deterministic_in_rule_order`(関数): 複数の値が当たるときは SUBCAT_TAG_VALUES の並び順で決まる。
  - `test_poi_subcategory_never_reads_the_name`(関数): 名前は一次規則に一切入らない(タグが無ければ None)。
  - `test_resolve_drops_a_tag_subcat_that_contradicts_the_cat`(関数): cat=attraction の POI に shop=hobby(topcat=shop)が付いていても採らない。
  - `test_resolve_falls_back_to_frozen_when_no_tags`(関数)
  - `test_resolve_name_layer_can_be_switched_off`(関数)
  - `test_resolve_prefers_raw_tags_over_frozen_value`(関数)
  - `test_resolve_returns_none_for_a_plain_shop`(関数)
  - `test_resolve_uses_name_only_as_the_last_resort`(関数)
  - `test_subcat_from_name`(関数)
  - `test_tag_index_accepts_an_empty_document`(関数)
  - `test_tag_index_by_priority_fills_elements_missing_from_the_new_document`(関数): 新しい文書に無い要素(例: 美竹公園)は旧い文書のタグで埋める。
  - `test_tag_index_by_priority_merges_inside_a_tier_like_tag_index`(関数): 同じ群の中は :func:`tag_index` と同じく重ねる(2026-09-07 の 2 文書の従来の挙動)。
  - `test_tag_index_by_priority_takes_the_newest_document_per_element`(関数): 同じ要素が新旧に出たら**新しい文書のタグ一式**を採る(旧のキーを混ぜない)。
  - `test_tag_index_merges_documents`(関数)
  - `test_tag_index_uses_the_w7_poi_id_convention`(関数)
  - `test_tag_rule_order_starts_with_the_v1_eleven`(関数): v1 の 11 語を先頭に固定する(判定順が変わると既存 POI の subcat が動きうる)。
  - `test_tag_tier_report_counts_matches_and_differences`(関数)
  - `test_the_added_subcats_are_exactly_these_twenty`(関数): 足した語を明示的に固定する(黙って語彙が増えない)。
  - `test_the_defect_itself_a_park_without_subcat_falls_into_place_leisure`(関数): 改訂前の姿(subcat 無しの公園)を固定する=回帰したら気づける。
  - `test_v1_frozen_subcats_are_still_there_with_the_same_topcat`(関数)
  - `test_w6_declares_the_raw_tag_inputs`(関数)
  - `test_w6_park_gate_is_not_zero`(関数): 改訂前は PLACE_PARK へ写る POI が 0 件だった。期待値は 0 であってはならない。
  - `test_w6_raw_tag_priority_puts_the_2026_09_28_document_first`(関数): 実装アジェンダ §1-1: 新文書(2026-09-28)→ 旧 2 文書(2026-09-07)。
  - `test_w6_stage_version_moved`(関数)
  - `test_w6_topcat_conflict_expectation_matches_the_review_table`(関数): 親決定 第281 Q1 (a): 期待値 3 = cat の見直し候補 3 件(cat は動かさない)。
  - `test_w6_unclassified_gates_cover_the_d97_target_cats`(関数): D-97 ③: hall/attraction/leisure の未分類をゲートにする(値は実測・理由は W6 の notes)。
- import している内部モジュール: `shibuya.build.geo.poi_class`・`shibuya.build.geo.w6_poi_org`・`shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`
- 決定の ID: D-97・第 281
