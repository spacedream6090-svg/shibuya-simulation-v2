# tools/instruments

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 8 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [dm_eval](dm_eval/README.md)・[leak_check](leak_check/README.md)

## [absent_declarations.py](../../../../../../tools/instruments/absent_declarations.py)

absent_declarations — 「無いと宣言」の一覧を Markdown に出す計器(第340 段 2 の 6・回答 11-01 §10-3)。

- 公開の関数とクラス
  - `fingerprint`(関数): 宣言の中身の指紋(absent と inputs の as_dict を正規化した JSON の sha256 の先頭 16 桁)。
  - `main`(関数)
  - `render`(関数)
- import している内部モジュール: `shibuya.world.processes.absent`・`shibuya.world.processes.inputs`
- 読む試験(道筋で): `tests/tools/test_absent_declarations.py`
- CLI の引数
  - `--out`: 出力の Markdown(既定は標準出力)
- 決定の ID: 11-01・11-01/§1・11-01/§2・11-01/§10-3・第 340

## [anchor_gauge.py](../../../../../../tools/instruments/anchor_gauge.py)

anchor_gauge — 第 2 期 2-0 **較正側の錨の計器**(記録を読むだけ・エンジン不変)。

- 公開の関数とクラス
  - `Static`(クラス): 構築側の入力(2 腕で共通)。
  - `area_and_stage`(関数): 刻み × 体 → (エリアの索引 or −1, 舞台に居るか)。
  - `arrays_sha16`(関数): journal の配列だけの sha256(先頭 16 桁)。meta(壁時計を含む)は入れない=同じランなら同じ値(検収 L10)。
  - `arrivals_table`(関数): transit_state が域外(1・2)→ 舞台(0)に変わった刻み × direction_node。(n_nodes+1, 24)・最後の行=なし。
  - `attr_by_area`(関数): (n, 5) の属性(0=勤務者・1=居住者・2=来街者)。居住地が先(R-56 §2 の判定順)。
  - `attr_by_kind`(関数)
  - `blank_visitor`(関数): 計画の比の表から来街者の列を空にする(セルが分からない=0 ではない)。
  - `cells_to_area`(関数)
  - `chome_of_cells`(関数): セル → 町丁目の符号(W16 の居住者の chome_key の多数決・居住者の居ないセルは最も近いセル)。
  - `col_masks`(関数): 1 刻みぶん → (7, n) の列の印(5 エリア・5 エリア計・舞台)。
  - `compare_docs`(関数): 前の版との差の表(要約の値ごと・腕ごと)。数は差・文字は同じか。
  - `core9_keys`(関数)
  - `core9_run`(関数): ランの昼夜間の比: 夜=中核 9 の居住者(ω)・昼=居住者か勤務・通学先が中核 9 の体で 10〜16 時に 30 分以上居た(ω)。
  - `core9_w16_static`(関数): W16 の静的な昼夜間人口比(夜=居住者・昼=夜−流出+流入・全年齢)。
  - `daily_qualified`(関数): 1 日単位の 30 分(``sum``=合計=本則 / ``cont``=連続=腕)→ (7, n) bool。
  - `declared_text`(関数)
  - `dist_stats`(関数): 始まりの分布(15 分)。平均・分位・:00/:30 の率・最頻のビン・15 分の構成(重みつき)。
  - `duty_open_anchor`(関数): 3-4 錨 1〔写〕: W17 v2 の勤務窓の作り方(trial.draw_windows=第 31 表の逆関数法+arrival_lead)を対象の体に。
  - `expansion_factors`(関数): 拡大係数 ω_k = N_k / n_k(標本に居ない種別は 0)→ 体ごとの ω。
  - `first_work_run`(関数): その日に初めて work_cell に 30 分以上続けて居た区間の始まり[分]\(無ければ −1)と 15 分の在席の率 (96, n)。
  - `gauge`(関数)
  - `gauge_arm`(関数)
  - `git_head`(関数)
  - `hm`(関数)
  - `hour_minutes`(関数): (時 24, 列 7, 体)の居た分と、列ごとの 1 日の最長の連続[刻み]。
  - `jsd`(関数): Jensen-Shannon divergence(底 2・形だけ)。どちらかが空なら None。
  - `load_journal`(関数)
  - `load_static`(関数)
  - `main`(関数)
  - `make_guard`(関数): 許可の一覧を組む(役割ごとに名で縛る・封印の語は組んだ時点で落ちる)。
  - `meal_time_validation_mark`(関数): 第 18-1 表と比べた食事時刻の結果の印(置き換えの前の版=``validation``・欄なし=無効/置き換えの後=検証可)。
  - `node_ids`(関数)
  - `opened_listing`(関数): ランの段で開いた道筋の一覧。計器の段で落とす語(〔検〕・〔灰〕)に当たる行に印を付ける(値は読まない)。
  - `peak_hour`(関数): KDDI の軸(5〜28 時)の系列 → ピーク時刻(同点は早い方)。全部 0 なら None。
  - `peaks_block`(関数)
  - `plan_arrivals_table`(関数)
  - `plan_unknown_shares`(関数): 計画で舞台の中に居るがセルが分からない(−2)体分の割合(全体・来街の種別・それ以外)。
  - `population_masks`(関数): v1.4 の母集団 P′(本則)・P(kind≠7・継続)・全員。
  - `presence_hourly`(関数): N^θ_{c,h} = Σ_i ω_i · 1[i∈母集団] · 1[1 日 30 分] · 1[その時間帯に θ 分以上]。KDDI の軸 (7, 24)。
  - `presence_on_hour`(関数): 正時の標本(v1.3 の数え方・1 日の条件なし)。KDDI の軸 (7, 24)。
  - `ratio`(関数)
  - `ratio_block`(関数): 1 日単位の在圏(5 エリア)を属性で分けた数と V/Res・W/Res。計=エリアの数の和。
  - `record`(関数): 1 腕のラン → 体の journal(``anchor_journal_*.npz``)。``use_recorder=False`` は包まずに回す(不変の確かめ)。
  - `render_compare`(関数)
  - `render_markdown`(関数)
  - `resolve_paths`(関数)
  - `rise_slot`(関数): 15 分の率の曲線 → 1 日の最大の ``frac`` を初めて超える 15 分の索引(全部 0 なら None)。
  - `share`(関数)
  - `ssb_work_rise`(関数): 第 8-1 表(平日・関東大都市圏・有業者・年齢総数)の仕事(05)の行動者率を男女の推定人口で混ぜた曲線の立ち上がり。
  - `summarize`(関数): 版の間で比べる値(平らな辞書)。
  - `time_dist_shape`(関数): time_dist_12 の 1 行(目的 × 乗降)→ KDDI の軸の形。開端は W12 と同じ等分(～6時台→5,6・0時台～→24,25)。
  - `w12_node_anchors`(関数)
  - `w12_stock_shape`(関数): N̂(h) = R + I·Σ_{t≤h}α(t) − O·Σ_{t≤h}β(t)(時間帯の終わりの在庫・5 時の在庫=居住者)。
  - `w16_static_ratios`(関数): 3-2 錨 1〔写〕: W16 の体数(kind の写像は舞台全体・area の写像はエリアごとの W/Res)。
  - `w20_start_anchor`(関数): 3-4 錨 5〔写〕(第 3 期 3-1): W20cal(暦 1a)の週の表の、その日の曜日の勤務の約束の始まり(週 0・対象の体)。
  - `weighted_curve`(関数)
  - `work_targets`(関数)
  - `wquantiles`(関数)
  - `write_outputs`(関数)
- import している内部モジュール: `shibuya`・`shibuya.agents.weekly`・`shibuya.build.sched.pool_facts`・`shibuya.build.sched.trial`・`shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`・`shibuya.cli`・`shibuya.engine.calendar_shadow`・`shibuya.engine.presence`・`shibuya.engine.run`・`shibuya.foundation.time_consts`・`tools/c7/attr_arms.py`・`tools/c7/c7lib.py`・`tools/instruments/read_guard.py`
- CLI の引数
  - サブコマンド `compare`
  - サブコマンド `gauge`
  - サブコマンド `record`
  - サブコマンド `run`
  - `--agents`
  - `--arm`
  - `--compare`
  - `--cur`
  - `--journal`
  - `--label`: 既定 <日付>_<commit>
  - `--no-recorder`: 包まずに回す(final と呼数だけ・不変の確かめ)
  - `--out`: (help を読めない)
  - `--out-dir`
  - `--out-root`
  - `--prev`
  - `--scratch`
  - `--seed`
  - `--world`
  - 名前を読めない呼び出し 1 か所
- 決定の ID: 10-13b/§7・R-56・R-115

## [anchor_split.py](../../../../../../tools/instruments/anchor_split.py)

anchor_split — 錨のファイルを区分(構築側/検証側)ごとに**鍵の名で機械的に**分ける(第337・封印の分離の残り)。

- 公開の関数とクラス
  - `Plan`(クラス)
  - `anchor_md5`(関数)
  - `check`(関数): git の版の元と 2 本を比べる(真偽と数だけ)。
  - `cmd_check`(関数)
  - `cmd_split`(関数)
  - `main`(関数)
  - `merge`(関数): 2 本を 1 つに戻す(読み手と同じ規則: ``anchors`` は合わせる・見出しは検証側の元の文を優先)。
  - `split_doc`(関数): 元の辞書 → (構築側, 検証側)。錨の名が表に無いもの・両方にあるものは止める(推測で振らない)。
- 読む試験: `tests/tools/test_seal_split_337.py`
- CLI の引数
  - サブコマンド `check`
  - サブコマンド `split`
  - `--rev`
  - `plan`
- 決定の ID: 10-13b/§7・R-115・第 337

## [batch_width_gauge.py](../../../../../../tools/instruments/batch_width_gauge.py)

batch_width_gauge — 第 3 期 3-2 **TM4 の既定の幅の試験の道具**(計算のまとめの幅 W の列 × salt の対)。

- 公開の関数とクラス
  - `cmd_run`(関数)
  - `cmd_table`(関数)
  - `main`(関数)
  - `markdown`(関数): 表の Markdown(幅の行 × 指標の列=差/salt の幅/中か)。
  - `metric_value`(関数): 記録の欄(``a.b`` で入れ子)から指標の値。道筋が None か値が無ければ None。
  - `read_records`(関数)
  - `run_one`(関数)
  - `table`(関数): 記録(1 行=1 本のラン: ``width_s``・``salt``・``final``・指標の欄)から幅ごとの表を作る。
- import している内部モジュール: `shibuya.foundation.time_consts`
- 読む試験(道筋で): `tests/engine/clock/test_tm4_regional_clock.py`・`tests/tools/test_batch_width_gauge.py`
- CLI の引数
  - サブコマンド `run`
  - サブコマンド `table`
  - `--agents`
  - `--alpha`
  - `--jobs`
  - `--kw`: cli.run に足す引数(JSON)
  - `--out`
  - `--out-json`
  - `--out-md`
  - `--population-seed`
  - `--records`
  - `--ref-width`
  - `--salts`
  - `--src`: 子プロセスの src(既定=この道具のリポの src)
  - `--widths`
  - `--world`
- 環境変数: `os.environ` をまるごと使う
- 決定の ID: 10-12/§4-2

## [hm_gauge.py](../../../../../../tools/instruments/hm_gauge.py)

hm_gauge — 第 3 期 3-3b **ヒストリーマッチング(HM)の直接判定の器**(器だけ・読むだけ・記録に JSON)。

- 公開の関数とクラス
  - `check_candidate`(関数): 候補=離散の seed の組だけ(ほかの欄・整数でない値は ``ValueError``)。
  - `check_observations`(関数): 観測は較正側だけ・分散は 0 以上の有限の数。
  - `check_path`(関数): 入力の道筋に封印と検証側の語があれば開く前に落とす(``read_guard.deny_hit``=小文字にそろえて照らし、当たらなければ
  - `combine`(関数): 束ね: 2 つ以上なら 2 番目に大きい値・1 つなら最大。
  - `implausibility`(関数): I = |z − 平均| / √(Var_ens + Var_obs + Var_disc)(分母 0 は ``ValueError``)。
  - `judge`(関数): 候補ごとの非含意度と残す/除く(器だけ=候補の初期状態は 4-1 の後)。
  - `main`(関数)
- 読む試験(道筋で): `tests/tools/test_hm_gauge.py`
- CLI の引数
  - サブコマンド `judge`
  - `--input`
  - `--out`
  - `--threshold`
- 決定の ID: 10-12/§1-6・10-12/§4-5・R-117

## [read_guard.py](../../../../../../tools/instruments/read_guard.py)

read_guard — 計器の読み口を**許可の一覧(allow list)**で縛る(第 2 期 2-0・較正側の錨の計器)。

- 公開の関数とクラス
  - `NotAllowedError`(クラス): 許可の一覧に無い道筋を開こうとした(開く前に落とす)。
  - `ReadGuard`(クラス): 許可の一覧(役割 → ファイル / 役割 → ディレクトリ)と守る根。
  - `SealedPathError`(クラス): 封印・検証側・〔灰〕の語を含む道筋を開こうとした(開く前に落とす)。
  - `deny_hit`(関数): 道筋に落とす語があれば、その語を返す(無ければ None)。
  - `files_listing`(関数): 読んだファイルの一覧(役割と道筋で並べた写し)。
  - `roles_table`(関数): 許可の一覧(役割 → 相対の道筋)。記録に載せる。
- 呼び手: `tools/instruments/anchor_gauge.py`・`tools/instruments/dm_eval/situations.py`・`tools/instruments/leak_check/run.py`・`tools/spatial/las_pointcloud_agg.py`
- 読む試験: `tests/build_sched/test_w20_calendar_1a.py`・`tests/c7/conftest.py`・`tests/tools/test_dm_eval.py`・`tests/tools/test_leak_check.py`・`tests/tools/test_seal_split_337.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- 決定の ID: 10-13b/§1・R-115・第 337

## [skill_gauge.py](../../../../../../tools/instruments/skill_gauge.py)

skill_gauge — 第 3 期 3-3b **CP14 の技量スコアの隣に生の点数を並べる器**(読むだけ・記録に JSON)。

- 公開の関数とクラス
  - `check_path`(関数): 入力の道筋に封印と検証側の語があれば開く前に落とす(``read_guard.deny_hit``・〔検収 L7〕)。
  - `crps_ensemble`(関数): 通常の CRPS(経験分布の CRPS=1/(2M²) の形)。
  - `crps_fair`(関数): fair CRPS(M ≥ 2)。
  - `crps_point`(関数): 点の予測の CRPS=絶対誤差。
  - `fill`(関数): 技量スコアの器(``ensemble.skill_container``)に点数を埋めた写しを返す(器の欄の名は変えない)。
  - `main`(関数)
  - `rank_histogram`(関数): 事例ごとの観測の順位(0〜M)の度数。同じ値は乱数で割る(seed つき)。
  - `score`(関数): 入力の全部の指標の点数(``SCHEMA``)。
  - `score_metric`(関数): 1 つの指標の点数: 生の点数(fair CRPS の平均・基準の CRPS の平均・rank histogram・広がりと誤差の比)と技量スコア。
  - `spread_skill`(関数): 広がり(√ 平均の 1/(M−1) の分散)・誤差(平均の RMSE)・比=√((M+1)/M)·広がり/誤差(Fortin ら 2014 の式 15)。
- import している内部モジュール: `shibuya.engine.experiment.ensemble`
- 読む試験(道筋で): `tests/tools/test_skill_gauge.py`
- CLI の引数
  - サブコマンド `score`
  - `--input`
  - `--out`
  - `--seed`
- 決定の ID: 10-12/§4-5・R-117

## [warmup_gauge.py](../../../../../../tools/instruments/warmup_gauge.py)

warmup_gauge — 第 3 期 3-3b **CP5-6 慣らしの自動判定の器**(MSER を「差の系列」に当てる・読むだけ・記録に JSON)。

- 公開の関数とクラス
  - `check_metric`(関数): 指標の種類の検査: 知らない種類・累積の系列(``kind: cumulative``)・累計の印の無い累計の道筋(``CUMULATIVE_PATHS``)は拒む。
  - `check_path`(関数): 入力の道筋に封印と検証側の語があれば開く前に落とす(``read_guard.deny_hit``=小文字にそろえて照らし、当たらなければ
  - `cmd_q1`(関数)
  - `cmd_q2`(関数)
  - `day_series`(関数): md23 のランの記録 → 日の番号 → 値(``<列の名>.<行の中の道筋>``・値の無い日は飛ばす)。
  - `difference_rows`(関数): (x, y, ずれ) の列 → 本ごとの差の系列 D_d = x_d − y_{d + ずれ}(x の日の番号で)。
  - `get_path`(関数)
  - `main`(関数)
  - `mean_of`(関数): 日ごとの平均(全部の本に値のある日だけ・日の昇順)。
  - `metrics_sha256`(関数)
  - `mser_curve`(関数): d = 0 … n − 1 の MSER(n, d) = Σ_{i>d}(y_i − Ȳ(n,d))² / (n − d)²。
  - `mser_point`(関数): 打ち切り点 d*(候補は d ≤ n − ``exclude_last``=最後の数バッチを候補にしない)。候補が無ければ ``d_star=None``。
  - `mser_rule`(関数): MSER の作法(``RULE``): 初めの長さ ``n0``(既定=全部)で当て、d* > n/2 なら 10% 延ばして当て直す。
  - `question1`(関数): 問い 1(基準のランの慣らしの日数): (A=開始日から, B=k 日前から, k) の列。差の系列 A − B を日ごとに平均して当てる。
  - `question2`(関数): 問い 2(3 区間): (改変の枝, A/A の枝) の列。実行の日から先の差の系列(改変 − A/A)の日ごとの平均に同じ規則を当て、
  - `to_flow`(関数): 在庫 → 流量(総流量の欄が無い間の代わり=日ごとの差=純流量・expedient)・累計 → その日の数(〔検収 M1〕)。
- import している内部モジュール: `shibuya.engine.experiment.warmup`
- 読む試験(道筋で): `tests/engine/experiment/test_cf33b_manifest.py`・`tests/tools/test_warmup_gauge.py`
- CLI の引数
  - `--input`
  - `--metrics`: 指標の表の JSON(既定=METRICS=計器の側の表)
  - `--n0`: 初めの長さ(日・既定=全部=延ばす余地なし)
  - `--out`
  - 名前を読めない呼び出し 1 か所
- 決定の ID: 10-12/§4-5・R-117
