# tools/c8

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 3 本(このディレクトリの直下)

その他のファイル: `ablations_v1.json`・`expedient_triage_v1.json`・`sensitivity_v1.json`

## [ablation_runner.py](../../../../../../tools/c8/ablation_runner.py)

ablation_runner.py — ablation **第1陣 6 本**(知覚契約書 §8)の腕定義表と実行器。

- 公開の関数とクラス
  - `arm_by_id`(関数): 腕定義表から 1 腕を引く(前方一致・大文字小文字を無視)。
  - `arm_markdown`(関数): 1 腕の結果 → Markdown(**純関数**)。
  - `compare_runs`(関数): baseline と腕の指標を突き合わせる(**純関数**)。
  - `execute_arm`(関数): 1 腕を回す(``runs`` の各構成を順に)。**切替口が無ければ回さない**。
  - `first_wave_ids`(関数): 知覚契約書 §8 の**第1陣 6 本**の id(表の ``first_wave.ids`` が正典)。
  - `main`(関数)
  - `run_metrics`(関数): 1 ランの結果 → 指標辞書(**腕の比較はこの辞書の上で行う**)。
  - `table_markdown`(関数): 腕定義表 → Markdown(``--list`` と計器盤が使う・**純関数**)。
  - `validate_table`(関数): 腕定義表の自己検査(テストと ``--list`` が使う)。**問題の一覧を返す**(例外にしない)。
- import している内部モジュール: `shibuya.engine.tape`・`tools/c8/c8lib.py`
- 読む試験: `tests/c8/conftest.py`
- CLI の引数
  - `--arm`: 回す腕の id(例 AB1-BUDGET-MODE / AB1 / ①)
  - `--fleet-wait-s`: tick ごとに艦隊の応答を待つ上限秒(本番既定 120=D-26。0 なら非ブロッキング)
  - `--list`: 腕定義表を印字して終わる
  - `--max-tokens`
  - `--run-id`
  - `--table`: 腕定義表 JSON(既定 tools/c8/ablations_v1.json)
  - `--tape-dir`: テープの置き場(既定=--out/c8_tapes)
  - `--temperature`
- 決定の ID: D-26・D-58・D-59・D-66・D-71・D-99・第 200・第 245

## [c8lib.py](../../../../../../tools/c8/c8lib.py)

c8lib — C8(ablation・感度・計器盤)の純関数と共通部品。

- 公開の関数とクラス
  - `SensitivityRow`(クラス): 設計書から機械的に拾った「感度: …」の 1 行。
  - `budget_row`(関数): 予算宣言表の 1 行(Markdown が正典・数値をここに複製しない)。
  - `compare_counts`(関数): 宣言値の分布 vs 対照の分布(**構築段階の対照の標準形**)。
  - `fmt`(関数): 表用の整形(``None``/NaN は「—」)。
  - `gpu_hours_for_calls`(関数): 呼数 → 艦隊の壁時計[時間]\(**実測 1 点の外挿=expedient**)。
  - `iter_rows`(関数)
  - `ledger_gaps`(関数): 設計書の感度行が台帳に載っているか(漏れ)/台帳にしか無い行(過剰)を返す。
  - `load_ablations`(関数): 腕定義表(``ablations_v1.json``)を読む。
  - `load_json`(関数)
  - `load_sensitivity`(関数): 感度試験の台帳(``sensitivity_v1.json``)を読む。
  - `markdown_table`(関数): ``c6lib.markdown_table`` と同じだが**セルの ``|`` を必ず逃がす**。
  - `md_cell`(関数): Markdown の表セルへ入れる文字列(``|`` と改行を潰す=表が崩れないように)。
  - `null_jsd_p95`(関数): **同じ分布から 2 回引いた**2 標本の JSD[bits] の 95% 点(帰無参照)。
  - `scan_build_spec_sensitivities`(関数): 世界データ構築仕様書 §2 の「感度: …」を全部拾う(**漏れ検出の分母**)。
  - `scan_engine_ablation_ids`(関数): ``src/shibuya/engine/processes/*.py`` が宣言する ``ablation_id``(``AB-*``)を集める。
  - `scan_first_wave_arms`(関数): 知覚契約書 §8 の「第1陣(…)=6本: ①… ②… ⑥…」を丸数字で切り出す。
  - `scan_plan_sensitivities`(関数): 実装計画書 §8 登録簿のうち「感度(試験)?:」を宣言している行を拾う(**報告用**)。
  - `verdict_from_stage`(関数): 構築段階の対照から**言えること**(片側の論法)。
- import している内部モジュール: `shibuya.core.budget`・`tools/c6/c6lib.py`
- 呼び手: `tools/c8/ablation_runner.py`・`tools/c8/dashboard.py`・`tools/c8/ensemble.py`・`tools/c8/sensitivity.py`
- 読む試験: `tests/c8/conftest.py`・`tests/c8/test_ablations_ab7.py`
- 決定の ID: D-66

## [dashboard.py](../../../../../../tools/c8/dashboard.py)

dashboard.py — **忠実度計器盤**(R14 G-1 の3面)を Markdown+JSON の 1 枚にまとめる。

- 公開の関数とクラス
  - `build`(関数): 計器盤の payload(**入力が欠けても落ちない**)。
  - `collect_ablations`(関数): 腕定義表 + 実行済み結果 → 面1の ablation 節。
  - `collect_build_gates`(関数): build_manifest → 段階ごとのゲート合否(W0-W20)。
  - `collect_calibration`(関数): 面1(較正面)の主要行。**合否線を付けない**(良くて当たり前=R14 G-1)。
  - `collect_coverage`(関数): wc_index → 世界被覆指標(5 値ベクトル+X+孤児)。**加重和にしない**。
  - `collect_distortions`(関数): PENDING.md から「歪む場所」の宣言候補を拾う(D-33/D-37/D-38 ほか)。
  - `collect_distortions_with_fallback`(関数): ``PENDING.md`` → 拾えた行が 0 件なら凍結した旧 PENDING(``PENDING_ARCHIVE``)。
  - `collect_holdout`(関数): 面2(holdout 面)。**唯一のゲート**・判定はアンサンブル単位(R14 G-1/G-2)。
  - `collect_ops`(関数): 面3(運用面)。``tools/c7/c7_accept`` の受入表を行に使う(**holdout 行は除く**)。
  - `collect_quality`(関数): 書式/役割語率・指標 B・ablation ① の実測(面1の補助指標)。
  - `collect_sensitivity`(関数): 感度台帳 → 面1の expedient 感度節。
  - `collect_verification`(関数): T1-T9 の状態を受入報告(build-report-C*.md)の該当行から拾う(**報告の補助**)。
  - `main`(関数)
  - `render`(関数): payload → 計器盤 1 枚(**純関数**)。
- import している内部モジュール: `tools/c8/c8lib.py`
- 読む試験: `tests/c8/conftest.py`
- CLI の引数
  - `--ablation-result`: tools/c8/ablation_runner の出力 JSON(複数可)
  - `--accept`: tools/c7/c7_accept の出力 JSON
  - `--bench`
  - `--out`
  - `--world`
- 決定の ID: D-33・D-37・D-38・D-40・D-118・第 279

## [ensemble.py](../../../../../../tools/c8/ensemble.py)

ensemble.py — アンサンブル運用(Phase 5・T8)の**設計だけ**: ラン構成 manifest の生成器。

- 公開の関数とクラス
  - `crps_ensemble`(関数): CRPS のアンサンブル標本推定量 ``mean|x−y| − ½·mean_{i,j}|x_i−x_j|``。**純関数**。
  - `ensemble_spec`(関数): EnsembleSpec(R14 G-4)を組む。**master_seed 以外は 1 バイトも変えない**。
  - `implausibility`(関数): 実行不能度 ``I``(R14 G-2)。**I ≤ 3 が合格**(Pukelsheim 3σ)。
  - `main`(関数)
  - `run_seed`(関数): G-5 の seed 写像 ``seed = blake3(manifest_sha256 ‖ run_index)``。
  - `spec_markdown`(関数): EnsembleSpec → Markdown(**純関数**)。
  - `spread_skill_ratio`(関数): spread-skill ratio(R14 G-8)。``sqrt(mean Var_ens) / RMSE(mean_ens, obs)``。**純関数**。
- import している内部モジュール: `tools/c8/c8lib.py`
- 呼び手: `tools/c7/prereg_v13.py`
- 読む試験: `tests/c7/test_prereg_v13.py`・`tests/c8/conftest.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- CLI の引数
  - `--agents`
  - `--calls-per-run`: 0 なら 10 呼/体/日で見積る
  - `--label`
  - `--manifest-sha`: 元のラン manifest の sha256(空なら placeholder)
  - `--n`
  - `--out`
  - `--ticks`
  - `--world`

## [sensitivity.py](../../../../../../tools/c8/sensitivity.py)

sensitivity.py — expedient 登録簿の**感度試験の台帳**と、構築段階の対照の実行器。

- 公開の関数とクラス
  - `attach_d44`(関数): D-44(第311): 判定不能の行に ``d44``(5 値の状態・指標・JSD・理由)と集計 ``d44_summary`` を足す(既存の列は変えない)。
  - `attach_read_graph`(関数): D-44 (c): 判定不能の行に ``engine_reads``(3 値)・``engine_reads_via`` を足す(**既存の判定列は変えない**)。
  - `attach_triage`(関数): Q146(第308): エンジンが読む行に ``triage``(3 分類・対照の候補・費用の見込み)を足す(既存の列は変えない)。
  - `build_manifest_verdicts`(関数): D-44 (a): build_manifest の expedient 全行 → 3 値の判定(既存の記録だけ・**純関数**)。
  - `engine_read_graph`(関数): D-44 (c): 段 → 出力 → 読み口(エンジン直接/下流の段)→ 推移的な到達(**純関数に近い**=src を読むだけ)。
  - `ledger_markdown`(関数): 台帳 → Markdown(**純関数**・計器盤が同じ表を埋め込む)。
  - `main`(関数)
  - `run_row`(関数): 1 行の対照を実行して ``result`` を作る。
  - `validate_ledger`(関数): 台帳の自己検査+**設計書との突合(漏れ検出)**。問題の一覧を返す。
  - `w12_hour_uniform`(関数): **D-W14 前半**: 外界ノードの時間帯配分を「一様」にした対照。
  - `w12_jr_phase`(関数): **D-W14 後半**: 等間隔ダイヤ(JR/東急/京王=expedient)の**位相を半運転間隔ずらす**対照。
  - `w13_temp_plus`(関数): **D-W15**: 気温 +1.5 ℃ の対照(体感段階 ``heat_stage`` の分布が動くか)。
  - `w16_area_apportionment`(関数): **D-W16**: 町丁目→セルの按分を「建物床面積」(宣言)vs「面積」(対照)。
  - `w17_rake_fixed12`(関数): **§8 RAKE_MAX_FRAC**: raking 予算の「適応」(宣言)vs「固定 12%」(対照)。
- import している内部モジュール: `shibuya.build.field.w13_weather`・`shibuya.build.geo.common`・`shibuya.build.pop.fitting`・`shibuya.build.pop.shapefile`・`shibuya.build.pop.w16_population`・`shibuya.build.sched.w17_schedule`・`tools/c8/c8lib.py`
- 読む試験: `tests/c8/conftest.py`
- CLI の引数
  - `--d44`: D-44(第311): 構築段階の対照と mock の対照の結果(docs/bench/analysis/d44-controls-2026-09-30)を判定不能の行に付けて台帳へ書く
  - `--data`
  - `--include-heavy`: heavy=true の行も回す(W17 再 ingest 約 90 s)
  - `--judge-manifest`: D-44 (a): build_manifest の expedient 全行を既存の記録だけで判定して台帳へ書く(第306)
  - `--ledger`: 台帳 JSON(既定 tools/c8/sensitivity_v1.json)
  - `--list`: 台帳を印字して終わる(既定でも印字するので、--run を付けないときの明示用)
  - `--manifest`
  - `--no-write-ledger`: 結果を台帳へ書き戻さない
  - `--out`
  - `--read-graph`: D-44 (c): 依存グラフで判定不能の行に「エンジンが読む/読まない/不明」を付けて台帳へ書く(第307)
  - `--run`: 実行する行 id、または all
  - `--triage`: Q146: 読む行に 3 分類(自前の構成=未リサーチ・tools/c8/expedient_triage_v1.json)を付けて台帳へ書く(第308)
  - `--world`
- 決定の ID: D-44・第 200・第 229・第 306・第 307・第 308・第 311・第 330
