# tests/w17

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tests/w17/__init__.py)

tests.w17 — W17 の物差し(tools/w17)の検査。

## [conftest.py](../../../../../../tests/w17/conftest.py)

tests.w17 の共通フィクスチャ。

- 公開の関数とクラス
  - `anchors`(関数): 構築側のファイル+検証側の作り物(:func:`synth_validation_anchors`)。
  - `anchors_file`(関数): CLI に渡す台帳(構築側+作り物を 1 本に書いたもの)。
  - `dy`(関数)
  - `make_sample`(関数): 行の並び → ``Sample``(parquet を書かずに器だけ作る)。
  - `synth_validation_anchors`(関数): 検証側の錨の**作り物**(検証側のファイルの値ではない)。
  - `write_responses`(関数): ``{agent_id: 本文}`` → fleet_gen 形式の応答 jsonl。
  - `write_toy_parquet`(関数): 合成の週次表 parquet を書く(列は ``agents.weekly._COLUMNS``)。
- import している内部モジュール: `tools/w17/diversity_yardstick.py`
- 読む試験: `tests/w17/test_diversity_yardstick.py`
- 決定の ID: 第 337

## [test_diversity_yardstick.py](../../../../../../tests/w17/test_diversity_yardstick.py)

tools/w17/diversity_yardstick.py の検査。

- 公開の関数とクラス
  - `test_anchors_reject_missing_field`(関数): 必須欄を 1 つ落としたら ``load_anchors`` は例外(推測で埋めない)。
  - `test_anchors_required_keys`(関数): 全アンカーに source/verified_by/tag と値がある(無ければ落ちる)。
  - `test_before_after_delta_sign_and_closer`(関数): 時刻をばらした after は M3a の H が上がり、:00+:30 が現実側へ寄る。
  - `test_block_kind_place_mismatch_is_reported`(関数): ``block_kind`` と場所語の矛盾を数える(移動 4 は判定しない・場所判定には使わない)。
  - `test_build_file_holds_only_non_validation_anchors`(関数): 構築側のファイルに検証側(第 30 表・Schneider)の名が無く、p0_prior は構築側にある。
  - `test_canonical_motif_is_isomorphism_invariant`(関数): 節点の付け替えで同じ形になる(出現順ラベルのままでは別物に見える)。
  - `test_cli_end_to_end`(関数): CLI: ``--parquet``/``--before-parquet``/``--floor``/``--out`` が通る(台帳は構築側+作り物=``--anchors``)。
  - `test_covered_minutes_handles_overlap`(関数): 重なった区間を二重に数えない(和集合の長さ)。
  - `test_default_reads_build_and_validation_and_the_guard_blocks_validation`(関数): 既定は 2 本(構築側+検証側)を合わせて読む。試験の中では番人が検証側を無いファイルに差し替えている=落ちる。
  - `test_file_path_and_directory_agree`(関数): 同じ中身なら**ファイル指定とディレクトリ指定で全指標が一致**する。
  - `test_floor_rows_absolute_difference`(関数): 同腕 2 標本の |A−B|。同じ標本なら 0、違えば差が出る。
  - `test_harm_structural_counts`(関数): 被覆率・就寝行あり率・深夜違反(合成では隙間 15/30 分だけ・違反 0)。
  - `test_m1_motifs_on_toy`(関数): 合成 4 人日 = 三角形 3 + 直線 4 節点 1。閾値 0.5% で 2 種・被覆 1.0・閉路 0.75。
  - `test_m1_unresolved_cells_collapse`(関数): **近似の宣言**: 店 2 軒はどちらも ``target_cell=-1`` なので 1 節点に潰れる。
  - `test_m2_timed_vs_untimed_signatures`(関数): 時刻を落とすと 2 体が同じ型(種類率 0.5・上位1型 1.0)、時刻を入れると別型。
  - `test_m3a_on_00_30_and_entropy`(関数): M3a: 20 本の開始分のうち 19 本が :00/:30 → 0.95・H は手計算 2.9464 bit。
  - `test_m3b_commute_proxy_and_m3c_work_start`(関数): M3b=勤務開始より前の最後の 移動/乗車(=乗車 480/480/480/510)。M3c=勤務開始。
  - `test_m3b_ignores_days_without_work`(関数): 勤務の無い日の 移動/乗車 を出勤代理に数えない(数えると分母が膨らむ)。
  - `test_m4_activity_and_place_counts`(関数): M4a=5.0±0.0(1 日 5 本)。M4b=場所種別 3,3,3,4 → 3.25±0.433・7 未満 1.0。
  - `test_m6_jaccard_pairs`(関数): M6: 体0 は 2 日が完全一致(J=1)・体1 は 4/6。平均 0.8333・完全一致率 0.5。
  - `test_m6_skips_pairs_with_an_empty_day`(関数): 片方の曜日に活動が無い対は数えない(J=0 で入れると『似ていない』に化ける)。
  - `test_merge_refuses_the_same_anchor_twice`(関数)
  - `test_on_00_30_is_the_15min_bin_label_not_the_exact_minute`(関数): アンカー(平均時刻編)は **15 分ビンのラベル**の集計。分ちょうど版は別欄に併記する。
  - `test_p0_prior_is_not_an_anchor`(関数): 設計書 §5 の前値は ``anchors`` ではなく ``p0_prior`` に居る(現実側と混ぜない)。
  - `test_parquet_file_path_is_accepted`(関数): ``--parquet`` に**ファイルパス**を渡せる(下見は w17_trial_<arm>_schedule.parquet)。
  - `test_parquet_roundtrip_and_outputs`(関数): 合成 parquet → ``load_weekly`` 経由で同じ数字・JSON と Markdown が書ける。
  - `test_parse_flat_and_block_lines`(関数): 現行形式とブロック形式を 1 本のパーサで読む(``vocab.parse_line`` を再利用)。
  - `test_responses_last_line_wins`(関数): 同じ id が 2 度書かれたら**最後**を採る(fleet_gen の resume 規約)。
  - `test_responses_sample_and_parse_failures`(関数): jsonl → Sample。壊れた行は ``format`` に計上され parse 失敗率に出る。
  - `test_stratified_weights_and_overall`(関数): w_k = 母集団体数 ÷ 標本体数。重みなし全体と加重全体が別に出る。
  - `test_vocabulary_not_duplicated`(関数): 語彙はツール側で二重定義していない(``agents.weekly`` と ``build.sched.vocab`` が一致)。
- import している内部モジュール: `shibuya.agents.weekly`・`shibuya.build.sched.vocab`・`tests/w17/conftest.py`
- 決定の ID: 第 337
