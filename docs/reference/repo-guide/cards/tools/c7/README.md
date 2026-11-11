# tools/c7

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 11 本・その他 1 本(このディレクトリの直下)

その他のファイル: `area_axes_v0.json`

## [attr_arms.py](../../../../../../tools/c7/attr_arms.py)

attr_arms.py — **KDDI 写像の感度腕**(在圏の形 9b・D-115 ③・解析側・エンジン不変)。

- 公開の関数とクラス
  - `AgentAxes`(クラス): 体の軸(起動時 1 回の写像)。エリアは ``AREA_IDS`` の索引・5 エリア外/域外は −1。
  - `AgentCellRecorder`(クラス): ``engine.resolve.apply`` を包み、毎 tick の ``cell`` を控える(**ソース非改変**・書き込みなし)。
  - `agent_axes`(関数): W16 の体の行 → 軸(自宅/職場/学校のセル → エリア)。起動時 1 回。
  - `area_attr_hour`(関数): 体の journal → ``(24, 5, 3)`` の 時 × エリア × 属性 の在圏数。
  - `arms_grid`(関数): 腕の格子(写像 × 滞在 × 20 歳未満)の H2〜H5。
  - `attr_matrix`(関数): ``(n, 5)`` の「体がエリア X に居るときの属性」(``ATTR_IDS`` の索引)。
  - `cells_to_area`(関数)
  - `kind_journal_rows`(関数): エンジンの在圏 journal だけから出せる腕(``kind`` / ``kind_student_worker`` × 滞在 0 × 20 歳未満を含む)。
  - `kind_journal_table`(関数): エンジンの在圏 journal(種別 × セル・正時)→ ``(24, 5, 3)``(``kind`` / ``kind_student_worker`` だけ)。
  - `kind_to_attr_map`(関数): 種別の写像(``kind`` / ``kind_student_worker``)。
  - `load_agent_journal`(関数)
  - `main`(関数)
  - `population_for`(関数): ``engine.run._resolve_population`` と同じ規約で体の行を取る(行 i = 体 i)。
  - `recorded_obs`(関数)
  - `save_agent_journal`(関数): 体の journal(``ticks`` (T,)・``cells`` (T, n) int16・``transit`` (T, n) int8・``kind`` (n,) int8・``meta``)。
  - `shape_metrics`(関数): ``(24, 5, 3)`` → H2〜H5 の値(sim)と開封済みの obs との差。**判定しない**(合否は書かない)。
- import している内部モジュール: `shibuya.agents.population`・`shibuya.engine.resolve`・`tools/c7/c7lib.py`・`tools/c7/occupancy_series.py`
- 呼び手: `tools/instruments/anchor_gauge.py`
- 読む試験: `tests/c7/test_attr_arms.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- CLI の引数
  - `--all-arms`: 写像 3 × 滞在 0/30 × 20 歳未満 off/on の格子
  - `--attr-map`
  - `--dwell-min`
  - `--exclude-under20`
  - `--journal`: 体の journal(.npz・record で作る)
  - `--kind-journal`: エンジンの在圏 journal(種別 × セル・kind の 2 腕だけ)
  - `--n-agents`
  - `--out`
  - `--seed`
  - `--world`
- 決定の ID: D-115

## [c7_accept.py](../../../../../../tools/c7/c7_accept.py)

c7_accept.py — **C7 受入表を 1 枚**にまとめる。

- 公開の関数とクラス
  - `build_table`(関数): 受入表(行の list)。**純関数**=テストの入口。
  - `determinism_rows`(関数): 2 本の checkpoint 列を突き合わせる。``prefix_ok`` なら短い方が前方一致で合格。
  - `main`(関数)
  - `normalize_checkpoints`(関数): ``run_hash.py`` の payload / c7 の checkpoint JSON のどちらでも読む。
  - `selfconsistency`(関数): T2-c: 本ラン単体の checkpoint 自己整合。
  - `table_markdown`(関数)
- import している内部モジュール: `tools/c7/c7lib.py`
- 読む試験: `tests/c7/conftest.py`・`tests/test_cli.py`
- CLI の引数
  - `--determinism`: T2-a: 5,000体 同seed 2 ランの checkpoint JSON
  - `--full`: T2-c だけ: 40万体の checkpoint JSON(テープ再生 cli --replay --checkpoints-out)。--summary があれば再生 final_hash と summary の 16 桁の一致も要求(D-54: 繰り延べのある規模では T2-b でなく再生で代替)
  - `--holdout`: holdout_compare.py の JSON
  - `--manifest`
  - `--out`
  - `--out-bytes`: S1 のバイト数を直接指定
  - `--out-dir`: 恒久記録の置き場(S1 の合計対象)
  - `--partial`: T2-b: 40万体 本ランと先頭K tick 部分再ランの checkpoint JSON
  - `--summary`: ラン CLI の標準出力ファイル
  - `--time-v`: /usr/bin/time -v の出力ファイル
  - `--wc`: wc_index.json
- 決定の ID: D-54

## [c7lib.py](../../../../../../tools/c7/c7lib.py)

c7lib — C7(40万体×1シミュ日・本番相当)受入計器の純関数。

- 公開の関数とクラス
  - `AreaMap`(クラス): セル索引 → 5エリア。エンジンのセル順(``w2_cells.parquet`` の行順)に一致する。
  - `LocalPlane`(クラス): PLATEAU 原点の局所平面(A7「座標系=PLATEAU原点の局所平面を全データで共有」)。
  - `OccupancySeries`(クラス): ランから作った在圏時系列(**形状のみ**を後段へ渡す)。
  - `area_ha_gate`(関数): 写像の自己検査: エリア別面積が地図読み取りの目安帯に入るか。
  - `area_share`(関数): ``(24, 5)`` → ``(5,)`` の 1 日合計のエリア構成シェア。
  - `budget_limits`(関数): 予算宣言表から上限を読む(**Markdown が正典**・複製しない)。
  - `build_area_map`(関数): W2 セル(格子索引)→ ``AreaMap``。**純関数**(parquet も IO も触らない)。
  - `classify_cells`(関数): セル代表点 → 5エリア索引(``AREA_IDS`` の位置)/ ``OUTSIDE``。**純関数**。
  - `counts_to_area_attr`(関数): 個体の (cell, kind) → ``(5, 3)`` エリア×属性 在圏数。**純関数**。
  - `dir_bytes`(関数): S1(恒久記録)のバイト数=対象ディレクトリのファイル合計。
  - `five_metrics`(関数): **形状5指標**(境界・経済設計書 §1.4)を計算する。**純関数**。
  - `hour_share`(関数): ``(24, 5)`` の在圏数 → ``(5, 24)`` の**エリアごとに正規化した時刻シェア**。
  - `kendall_tau`(関数): タウ-b(同順位を扱う・SciPy なし)。順序関係の一致を測る(D1′ (ii)(iii))。
  - `load_axes`(関数): ``area_axes_v0.json`` を読む(素の dict・改変しない)。
  - `metrics_markdown`(関数): 5指標を 1 表に。
  - `night_residual`(関数): ``(5, 24)`` シェア → 深夜残存率 = 深夜帯の平均シェア ÷ 終日平均シェア(=1/24)。
  - `parse_run_summary`(関数): ``RunResult.summary()`` の標準出力 → 数値辞書。**純関数**。
  - `parse_time_v`(関数): ``/usr/bin/time -v`` の出力 → RSS ほか。**純関数**。
  - `peak_hours`(関数): ``(5, 24)`` シェア → 各エリアのピーク時刻(0-23)。
  - `polyline_side`(関数): 折れ線に対する点の**符号つき側**(最近傍セグメントの外積の符号)。
  - `sample_ticks`(関数): 標本 tick(``every`` の倍数・最終 tick を必ず含めない=時×24 を崩さないため)。
- import している内部モジュール: `shibuya.foundation.budget`・`tools/c6/c6lib.py`
- 呼び手: `tools/c7/attr_arms.py`・`tools/c7/c7_accept.py`・`tools/c7/holdout_compare.py`・`tools/c7/occupancy_series.py`・`tools/c7/prereg_v13.py`・`tools/c7/presence_yardstick.py`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/c7/conftest.py`・`tests/c7/test_presence_yardstick.py`・`tests/engine/test_waste_sink_report.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- 決定の ID: 11-01

## [holdout_compare.py](../../../../../../tools/c7/holdout_compare.py)

holdout_compare.py — **封印された KDDI holdout を 1 回だけ開いて**形状5指標を照合する。

- 公開の関数とクラス
  - `SealError`(クラス): 封印規律に反する操作(未指定の開封・二度目の開封・sha256 不一致)。
  - `check_seal`(関数): 封印メンバーの sha256 が封印時と一致するか(**中身は読まない**・ハッシュだけ)。
  - `compare`(関数): 5 指標を計算する(**純関数**・テストの入口)。
  - `find_table`(関数): 入れ子のどこかにある ``key`` のテーブルを取り出す(**最初の一致**)。
  - `guard_open`(関数): 開封の門番。``--open-seal`` 無し / 既に開封済みで ``--force`` 無し は例外。
  - `hour_bin_to_sim_hour`(関数): KDDI の時間帯(5..28)→ 世界内の時(0-23)。``28時`` は翌 4 時。
  - `load_seal`(関数): ``w19_freeze.json`` の封印から 1 層を取り出す(**中身は開かない**)。
  - `main`(関数)
  - `observed_area_share`(関数): 同じテーブルから ``(5,)`` の**エリア構成シェア**(1 日合計の相対量)。
  - `observed_attr_share`(関数): 属性テーブル → ``(5, 3)`` の**エリア内属性シェア**。
  - `observed_hour_share`(関数): 滞在×時間帯テーブル → ``(5, 24)`` の**時刻シェア**(絶対水準は返さない)。
  - `read_holdout`(関数): 封印ファイルを開いて**形状だけ**取り出す(絶対水準はここで捨てる)。
  - `read_open_record`(関数)
  - `report`(関数): 照合の Markdown。``v13_section`` は ``--prereg-version v1.3`` のときだけ末尾に足す
  - `resolve_fields`(関数): レコード 1 件の欄名から論理欄 → 実欄名を決める。決まらなければ例外。
  - `sha256_file`(関数)
  - `sim_from_occupancy`(関数): ``c7_occupancy.json`` → ``(24, 5)`` 在圏数と ``(5, 3)`` 属性数。
  - `validate_prereg_version`(関数): 版と ``--occupancy`` の本数の整合。**ファイルには一切触らない**(封印の前に呼ぶ)。
  - `write_open_record`(関数): 開封記録を書く。**既存の記録は消さず** ``previous_openings``(古い順)に積む。
- import している内部モジュール: `tools/c7/c7lib.py`・`tools/c7/prereg_v13.py`
- 読む試験: `tests/c7/conftest.py`
- CLI の引数
  - `--data-root`: data 根(封印パスの起点)
  - `--field-map`: 生データの欄名対応 JSON
  - `--force`: 開封記録があっても開く(理由を登録簿へ)
  - `--manifest`: ラン manifest JSON(開封記録の書き込み先)
  - `--occupancy`: occupancy_series.py が出した JSON。v1.3 は seed の本数だけ並べる
  - `--open-seal`: **明示**しないと holdout を 1 バイトも読まない
  - `--out`: 出力ディレクトリ
  - `--prereg`: 事前登録の合格線 JSON(既定 PREREG_V0)
  - `--prereg-version`: 事前登録の版(既定 v1.2=1 ランの点判定・v1.3=seed アンサンブル判定)
  - `--record`: 開封記録の置き場
  - `--run-id`: 照合したランの run_id
  - `--world`: w19_freeze.json のある場所
  - `--write-manifest`: manifest に holdout_open 欄を実際に足す(既定は断片を印字するだけ)
- 決定の ID: 第 176・第 216

## [occupancy_series.py](../../../../../../tools/c7/occupancy_series.py)

occupancy_series.py — C7 の**在圏時系列**(5エリア×24時)を作る。

- 公開の関数とクラス
  - `OccupancyRecorder`(クラス): ``engine.resolve.apply`` を包んで在圏を標本化する(**ソース非改変**)。
  - `agent_field`(関数): 個体 SoA の欄を取る。
  - `build_map`(関数): W2 セル → ``AreaMap`` と自己検査(面積帯)。
  - `cells_from_world`(関数): ``w2_cells.parquet`` を**エンジンと同じ行順で**読む(place_id / ix / iy)。
  - `checkpoints_json`(関数): ``RunResult`` → T2 用 checkpoint JSON(``c7_accept.py --determinism/--partial`` の入力)。
  - `kind_cell_to_area_attr`(関数): ``(T, K, C)`` 種別×セル → ``(T, 5, 3)`` エリア×属性。**純関数**。
  - `load_journal`(関数): journal(``.npz``)→ ``OccupancySeries``。
  - `main`(関数)
  - `report_markdown`(関数)
  - `sensitivity`(関数): 境界 ±50m の膨張/収縮で写像がどれだけ動くか(地図読み取り答申の要求「④ expedient 登録:
  - `write_journal`(関数): エンジン側フックと本ツールが共有する journal 形式(``.npz``)。
- import している内部モジュール: `shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.world.state`・`tools/c7/c7lib.py`
- 呼び手: `tools/c7/attr_arms.py`・`tools/c7/presence_yardstick.py`・`tools/c7/seed_ensemble.py`・`tools/fig/fig_presence_24h.py`・`tools/fig/fig_seed_pair.py`
- 読む試験: `tests/c7/conftest.py`・`tests/c7/test_presence_yardstick.py`
- CLI の引数
  - `--agents`
  - `--area-map`: 既存の写像表 JSON(無ければ --world から作る)
  - `--axes`: 境界定義 JSON(既定 tools/c7/area_axes_v0.json)
  - `--build-map`: セル→エリア写像表を作る
  - `--checkpoint-every`: checkpoint 間隔[tick]\(T2-b の部分再ランと**同じ値**にすること)
  - `--dilate-m`: 境界の膨張/収縮[m]\(感度用)
  - `--every`: 標本間隔[tick]
  - `--journal`: エンジン側フックが出した .npz
  - `--out`: 出力ディレクトリ
  - `--record`: その場で run_day を回して標本化する
  - `--seed`
  - `--sensitivity`: 境界 ±50m の感度を測る
  - `--ticks`
  - `--world`: 世界資産ディレクトリ

## [prereg_v13.py](../../../../../../tools/c7/prereg_v13.py)

prereg_v13 — 事前登録 **v1.3**(3 seed のアンサンブル判定)の純関数。

- 公開の関数とクラス
  - `apply_ensemble_verdict`(関数): v1.3 では **トップレベルの ``n_pass``/``n_measured``/``pass`` をアンサンブル判定で置く**(親判断・第216)。
  - `crps_fair_terms`(関数): CRPS と **fair CRPS**(Ferro 2014)の 2 項を分けて返す。**純関数**。
  - `ensemble_verdict`(関数): 事前登録 v1.3 のアンサンブル判定。**純関数**(テストの入口)。
  - `fair_crps_table`(関数): エリア×時刻ごとの在圏シェアの アンサンブル CRPS と fair CRPS(平均・比)。
  - `family_half_width`(関数): 平均の家族 95% 区間の半幅 = ``t(0.995, n−1)·SD/√n``(第209 の親再計算と同じ式)。
  - `get_envelope`(関数): seed 間の min/max 包絡と、holdout が内側にある時刻数。**検定ではない**。
  - `h1_day_window`(関数): H1(相関)を**昼 6〜23 時だけ**で計算し直す。
  - `interval_verdict`(関数): 区間 ``[lo, hi]`` と線の関係を 3 値で返す(Sargent 2016 の区間仮説)。
  - `report_v13`(関数): v1.3 節の Markdown(``holdout_compare.report`` の末尾に足す)。
  - `seeds_needed`(関数): ``N=(t(0.995,N−1)·SD/距離)²`` を満たす最小の N(``n_min..n_max``)。無ければ None。
  - `stat_entry`(関数): 1 統計量の seed ごとの値 → 平均・SD・家族 95% 区間・同値検定の判定・要る seed 数。
- import している内部モジュール: `tools/c7/c7lib.py`・`tools/c7/seed_ensemble.py`・`tools/c8/ensemble.py`
- 呼び手: `tools/c7/holdout_compare.py`
- 読む試験: `tests/c7/test_prereg_v13.py`
- 決定の ID: D-79・D-83・第 209・第 210・第 216

## [presence_yardstick.py](../../../../../../tools/c7/presence_yardstick.py)

presence_yardstick.py — **在圏の物差し**。ランの「どこに何体居るか」を現実アンカーと並べる。

- 公開の関数とクラス
  - `Presence`(クラス): 1 ランの在圏。journal(生)からも series JSON(集計済み)からも作れる。
  - `anchors_echo`(関数): 報告に載せる現実側の数値(出典つきで JSON に残す)。
  - `build_payload`(関数): 1 ラン(または前後 2 ラン)→ 出力 JSON まるごと。**純関数**。
  - `check_anchors`(関数): 必須欄(source/verified_by/tag)と値の存在を検査する。**純関数**(例外で知らせる)。
  - `compare`(関数): before/after の同名指標を並べ、**現実側へ近づいたか**の bool を付ける。**純関数**。
  - `display_path`(関数): 記録に書くパス表記: リポ内なら ``<repo>/`` からの相対(個人ディレクトリ名を記録に残さない・第176)。
  - `hour_mean`(関数): ``(n_samples, …)`` → ``(24, …)``。同じ時の標本は平均。
  - `kind_tables`(関数): ``(T,9,C)`` 種別×セル → ``(24,9)`` の 5 エリア内 と bbox 全体。**純関数**。
  - `load_anchors`(関数): アンカー台帳を読む。**必須欄が欠けていたら落とす**(推測で埋めない)。
  - `main`(関数)
  - `markdown`(関数): JSON と同じ内容の表。**合格線は書かない**(距離と bool だけ)。
  - `measures`(関数): 1 ランの在圏 → 表の素(JSON にそのまま入る)。**純関数**。
  - `metric_entries`(関数): 比較に使う**スカラー指標**の一覧(値・目標・向き)。**純関数**。
  - `parse_calls_by_hour`(関数): ``呼/時 00:1550 …`` の 24 値。行が無ければ None。**純関数**。
  - `parse_n_agents`(関数): ``[run] n=5000 …`` の個体数。無ければ None。**純関数**。
  - `parse_planned_sleep`(関数): ``D-62 計画就寝 …`` 行 → 内訳。行が無ければ None。**純関数**。
  - `parse_wake_rate`(関数): ``起床率/時 00:0.185 …`` の 24 値(**割合**)。行が無ければ None。**純関数**。
  - `parse_wake_rate_in_area`(関数): ``起床率(在圏)/時 00:0.485 …`` の 24 値。行が無ければ None。**純関数**。
  - `presence_from_journal`(関数): journal(``.npz``)→ ``Presence``。読みと 5 エリア集計は既存物に任せる。
  - `presence_from_series`(関数): ``occupancy_series.py`` の集計済み JSON → ``Presence``(bbox と種別は空欄)。
  - `read_summary`(関数): 要約テキスト → 使う欄だけの辞書(読めない欄は None のまま=推測しない)。
  - `scale_factor`(関数): ``target`` 体換算の縮尺(**線形・expedient**)。個体数が分からなければ None。
- import している内部モジュール: `tools/c7/c7lib.py`・`tools/c7/occupancy_series.py`
- 読む試験: `tests/c7/test_presence_yardstick.py`
- CLI の引数
  - `--anchors`: (help を読めない)
  - `--area-map`: 既存の写像表 JSON
  - `--axes`: 境界定義 JSON(既定 tools/c7/area_axes_v0.json)
  - `--before`: 比較元の journal(.npz)
  - `--before-label`: before 側の名前
  - `--before-n-agents`: before の個体数
  - `--before-series`: 比較元の集計済み JSON
  - `--before-summary`: 比較元の要約テキスト
  - `--journal`: 在圏 journal(.npz)
  - `--label`: after 側の名前(既定=ファイル名)
  - `--n-agents`: after の個体数(縮尺の分母)
  - `--out`: 出力ディレクトリ(既定=標準出力のみ)
  - `--series`: 集計済み在圏 JSON(area_hour_counts)
  - `--summary`: ラン要約テキスト(cli の標準出力)
  - `--target-population`: 縮尺の分子(既定=台帳の full_population)
  - `--world`: 世界資産(写像表を作るとき)
- 決定の ID: D-62・D-66・第 170・第 173・第 176

## [salt_compare.py](../../../../../../tools/c7/salt_compare.py)

salt の比較の**読む役**(10f 第 2 段・R-71 の手順・K20 (a)・K21 (a))。

- 公開の関数とクラス
  - `aa_match`(関数): A/A: 同じ設定・同じ seed の 2 本が全 checkpoint(combined・behavior・full)と final で一致するか。
  - `achievable_alpha`(関数): 符号反転で作れる有意水準のうち ``alpha`` 以下で最大のもの(両側 2k/2^n・片側 k/2^n)。作れなければ 0。
  - `analyze`(関数): 指標ごとの値の組(``{id: {"base": [...], "arm": [...]}}``)と指標の一覧から、線・多重比較つきの表を作る。
  - `arm_keys_of`(関数): 腕の欄(検収 S3-4): 2 つの腕で値が違う引数(片方だけにある引数を含む)だけ。
  - `bh`(関数): Benjamini-Hochberg(k̂ = max{k: p_(k) ≤ kα/m} まで棄却・Storey 2002 式 (12))。q 値(min_{j≥i} m p_(j)/j)。
  - `crn_health`(関数): ``salt_runs.py`` の索引と読んだ checkpoints の JSON から CRN の健全性をまとめる。
  - `exit_code`(関数): CRN の健全性の ``status`` → 終了コード(``ok`` 0・``fail`` 1・``未検査`` 3)。
  - `first_divergence`(関数): 2 本の checkpoints の JSON の最初に食い違う checkpoint(``first_diff.compare`` を使う)と、どの hash が違うか。
  - `get_path`(関数): ``a.b.c`` の道筋で入れ子の辞書を引く(無ければ ``KeyError``)。
  - `holm`(関数): Holm の逐次棄却(Holm 1979)。調整済みの p(単調にした max_{j≤i} (m−j+1)p_(j)・1 で頭打ち)と棄却。
  - `input_match`(関数): 入力の一致(R-71 §8-1 の 1・K21 (a)・10f 第 2 段の直し S1)。
  - `main`(関数)
  - `n_halfwidth95`(関数): 95% の区間の半幅 t_{N−1,0.975}·CV/√N を r 以下にする最小の N(N ≥ 2)。``n_max`` までに無ければ ``None``。
  - `n_relative_se`(関数): 相対の標準誤差 CV/√N を r 以下にする最小の N = ceil((CV/r)²)(D-46 の式。半幅の式ではない)。
  - `p_floor`(関数): その対の数で到達できる最小の p(片側 1/2^n・両側 2/2^n・R-71 §2-3)。
  - `paired_stats`(関数): salt の対(同じ順)の値から、差・幅・差 ÷ 幅・ρ・区間・効果の大きさ・D-46 の本数を出す(検定の判定はしない)。
  - `perm_ci`(関数): 符号反転の検定(両側・差の平均)を反転した区間(R-71 §4-2・Ernst 2004 §4.1)。
  - `pre_t0_match`(関数): T0 より前の checkpoint(tick < T0)の behavior-hash が全部一致するか(R-71 §8-1 の 2)。
  - `report`(関数): 索引+checkpoints の JSON+指標の一覧 → 報告(純関数)。
  - `seed_key`(関数): seed の比べ方(検収 S3-8): 型も見る(``1`` と ``"1"`` は ``core.rng`` で別の鍵=``i:1`` と ``s:1``)。
  - `sign_flip_p`(関数): 対の差 ``d`` の符号反転の検定(統計量=差の平均)。
  - `t_cdf`(関数): Student の t 分布の累積分布関数。
  - `t_quantile`(関数): t 分布の分位(2 分法・相対 1e-12)。``q`` は 0〜1、``df`` は 1 以上。
  - `values_from_payloads`(関数): 索引の salt の順に、基準と腕の指標の値を集める。
- 呼び手: `tools/c7/salt_runs.py`
- 読む試験: `tests/c7/test_salt_compare_10f.py`・`tests/engine/test_salt_seed_split_10f.py`
- 読む試験(道筋で): `tests/engine/experiment/test_x33_ensemble.py`
- CLI の引数
  - `--metrics`: 指標の一覧(主要・副次・探索)の JSON
  - `--out`: 報告の JSON(既存のファイルへは書かない)
  - `--runs`: salt_runs.py の索引(runs.json)
  - `--values`: 計器の値の組の JSON({id: {base: [...], arm: [...]}})
- 決定の ID: R-71・D-46

## [salt_runs.py](../../../../../../tools/c7/salt_runs.py)

salt の比較の**回す役**(10f 第 2 段・K21 (a))。読む役は ``salt_compare.py``。

- 公開の関数とクラス
  - `cmd_one`(関数): 1 本を回して checkpoints の JSON を書く(``shibuya.cli.run`` を呼ぶだけ)。
  - `cmd_plan`(関数)
  - `main`(関数)
- import している内部モジュール: `shibuya.cli`・`tools/c7/salt_compare.py`
- 読む試験(道筋で): `tests/engine/test_salt_seed_split_10f.py`
- CLI の引数
  - サブコマンド `one`
  - サブコマンド `plan`
  - `--T0`: 改変の時刻(腕が最初から違うなら 0)
  - `--aa`: 基準の腕を最初の salt でもう 1 本(A/A)
  - `--agents`
  - `--arm`
  - `--arms`: JSON {"名前": {cli.run の引数}}
  - `--base`
  - `--checkpoint-every`
  - `--environment-mode`: fixed=天気は同じで動きだけ変える / salt=天気も変える(環境の seed を salt と同じに)
  - `--environment-seed`: fixed のときの環境の seed(省略=母集団の seed)
  - `--first-diff`: 対ごとに最初に食い違う tick を探す
  - `--jobs`
  - `--kwargs`
  - `--out`
  - `--population-seed`: 母集団の seed(全部のランで同じ)
  - `--resume-from`
  - `--salts`: 動きの seed(salt)の一覧
  - `--scratch`
  - `--seed`
  - `--state-out`
  - `--stop-at-tick`
  - `--world`
- 環境変数: `os.environ` をまるごと使う

## [seed_ensemble.py](../../../../../../tools/c7/seed_ensemble.py)

seed アンサンブル(N 本)の帰無参照 — prereg v1.3 §7「3 本の対ごとの平均」と家族 95% 区間(第215)。

- 公開の関数とクラス
  - `family_half_width_pct`(関数): 平均の家族 95% 区間半幅(%)= t(0.995, n−1)·CV/√n·100。n=3・CV 0.0038 → 2.2 / 0.0325 → 18.6(第209)。
  - `jsd_bits`(関数): 24 h シェアの Jensen–Shannon 距離²(bits)。fig_seed_pair と同じ定義。
  - `load_tables`(関数): ラベル → (24, n_area) の時×エリア表。
  - `main`(関数)
  - `summarize_ensemble`(関数): 数値だけの要約(描画・IO から分離=テスト用)。
  - `t_quantile_995`(関数): 両側 99%(=片側 0.995)の t 分位。scipy があれば計算・無ければ表。
- import している内部モジュール: `tools/c7/occupancy_series.py`
- 呼び手: `tools/c7/prereg_v13.py`・`tools/c7/seed_exchangeability.py`
- 読む試験: `tests/c7/test_seed_ensemble.py`
- CLI の引数
  - `--axes`
  - `--out`: JSON の出力先(既存ファイルへは書かない)
  - `--run`: label=occupancy.npz(省略時は DEFAULT_RUNS の 3 seed)
  - `--world`
- 決定の ID: 第 209・第 215

## [seed_exchangeability.py](../../../../../../tools/c7/seed_exchangeability.py)

seed の交換可能性の検査(D-83 ⑦・第217)— 「seed 以外は同一構成か」を機械で確かめる。

- 公開の関数とクラス
  - `compare`(関数): 純関数。checkpoints.json の dict を N 本受けて判定 dict を返す。
  - `flatten`(関数): 入れ子 dict を ``a.b.c`` に平坦化(list は JSON 文字列で 1 値扱い)。
  - `hour0_equality`(関数): 任意: 00 時の 5 エリア合計(初期配置)が seed 間で一致するか。
  - `main`(関数)
  - `parse_equivalents`(関数): ``key=v1|v2|...:理由`` → {key: {"values": {...}, "reason": str}}。値 ``None`` は JSON null と同一視。
  - `section_of`(関数): 道筋の節(最も長く一致する表の道筋)。``engine/manifest_sections.section_of`` と同じ規則(道具は src を import しない)。
- import している内部モジュール: `tools/c7/seed_ensemble.py`
- 読む試験: `tests/c7/test_seed_exchangeability.py`・`tests/engine/test_env_and_sections_10f.py`
- CLI の引数
  - `--axes`
  - `--checkpoints`
  - `--equivalent`: 親が根拠つきで同値と宣言する差(例 intent_mode=None|vocab:AB7 以後の既定名・挙動同一)
  - `--occupancy`: 任意: 00 時の初期配置の一致
  - `--out`: JSON の出力先(既存ファイルへは書かない)
  - `--world`
- 決定の ID: D-83・第 217
