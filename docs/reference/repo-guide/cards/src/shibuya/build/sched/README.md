# src/shibuya/build/sched

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 8 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/build/sched/__init__.py)

build.sched — 世界データ構築 W17(週次スケジュール生成・T0 活動表)。

- 公開の関数とクラス
  - `stage_funcs`(関数): 段階名 → 段階関数(``run.STAGE_FUNCS`` の遅延取得)。
- import している内部モジュール: `shibuya.build.sched.run`
- 呼び手: `shibuya.build.run`・`shibuya.build.sched.run`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [pool_facts.py](../../../../../../../../src/shibuya/build/sched/pool_facts.py)

build.sched.pool_facts — ペルソナプールの「生活の素材」欄だけを引く読み取り器。

- 公開の関数とクラス
  - `PoolFacts`(クラス): 要求した ``(layer, index)`` の並びに対応する素材(行順=要求順)。
  - `layer_files`(関数): 層の part ファイル(名前順=``pool_index`` の順・``build.pop.pool`` と同規約)。
  - `parse_days`(関数): ``"mon-fri"`` / ``"all"`` / ``"sat,sun"`` → 曜日ビットマスク(bit d = 曜日 d)。
  - `parse_hhmm`(関数): ``"09:00"`` / ``"0900"`` → 分。読めなければ ``-1``。
  - `read_facts`(関数): ``(pool_layer, pool_index)`` の並びに対応する素材を読む。
- import している内部モジュール: `shibuya.foundation.time_consts`
- 呼び手: `shibuya.build.sched.trial`・`shibuya.build.sched.w17_schedule`・`shibuya.build.sched.w20_calendar_1a`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/build_sched/test_trial.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: D-68

## [run.py](../../../../../../../../src/shibuya/build/sched/run.py)

build.sched.run — スケジュール生成レーン(W17)の段階を実行する CLI。

- 公開の関数とクラス
  - `main`(関数)
  - `parse_shard`(関数): ``"0/8"`` → ``(0, 8)``。``None`` は ``(0, 1)``(分割なし)。
  - `run_pilot`(関数): パイロット標本を書く(+ 応答があれば取り込んで報告する)。**段階ヘッダは書かない**。
  - `run_stages`(関数): 段階を順に実行してヘッダを書く(``geo.run.run_stages`` と同形)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.geo.run`・`shibuya.build.sched`・`shibuya.build.sched.w17_schedule`
- 呼び手: `shibuya.build.run`・`shibuya.build.sched`
- 読む試験: `tests/build_sched/test_w17_ingest.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--data`: 入力データ根(既定 data)
  - `--out`: 出力ディレクトリ(例 data/world/v2)
  - `--pilot`: 種別ごとに N 体のパイロット用プロンプトだけを書く(w17_pilot_prompts.jsonl)
  - `--pilot-ingest`: w17_pilot_responses.jsonl を取り込んで報告だけする(資産は書かない)
  - `--quiet`
  - `--shard`: プロンプトの分割 i/n(既定=分割なし)
  - `--stage`: 実行する段階

## [trial.py](../../../../../../../../src/shibuya/build/sched/trial.py)

build.sched.trial — D-68 下見(2,000 体・多腕)の**別経路**モジュール。

- 公開の関数とクラス
  - `ArmSpec`(クラス): 1 腕の凍結仕様(system 文・例示・事実行・regex・修復方針・raking 予算)。
  - `BinTable`(クラス): 1 行ぶんの 15 分ビン表(逆関数法の入力)。
  - `Block`(クラス): ブロック 1 件(``block_kind`` を持つ活動)。
  - `TrialFacts`(クラス): 下見の追加事実(行順=``AgentFacts`` の行順)。
  - `TrialReport`(クラス): 腕ごとの検査結果(``w17_trial_<arm>_report.json`` の中身)。
  - `anchor_path`(関数): アンカー台帳の既定の場所(``<repo>/docs/bench/anchors/commute_time_dist_r3.json``)。
  - `arm_dir`(関数)
  - `arm_of`(関数)
  - `arm_prompt_of`(関数): 1 体ぶんのプロンプト(本番 ``SchedPrompt`` と**同じ 1 行の形**= fleet_gen 入力)。
  - `arm_prompts`(関数): 標本ぶんのプロンプト列(行順=``rows`` の順=決定論)。
  - `arm_regex`(関数): 腕と体 → 構造化出力 regex(段1 は regex なし)。
  - `arm_seed`(関数): 腕タグ入りの生成 seed(§4「seed ドメインに腕タグを入れる」)。
  - `arm_system`(関数): 腕と体 → system 文。
  - `arm_user`(関数): 腕と体 → user 文(事実行)。
  - `assert_isolated`(関数): 出力先が本番資産のディレクトリと**同じでない**ことを確かめる(凍結資産の保護)。
  - `block3_system`(関数): P2′ の system 共通部(**全員共通**)。``days`` で 1 日モード(d0 のみ)に切り替わる。
  - `block_kind_conflict`(関数): ``block_kind`` と 活動語/場所語 の矛盾(空文字なら矛盾なし)。
  - `block_regex`(関数): ブロック形式の構造化出力 regex。
  - `build_anchor`(関数): 第31表(出勤)+第36表(帰宅)→ ``docs/bench/anchors/commute_time_dist_r3.json``。
  - `check_identity`(関数): 段1 の応答検査(字数 200〜420 と禁止 4 つ)。落ちた理由の list(空なら合格)。
  - `derive_block_kind`(関数): (活動語, 場所語, 自宅が域内か)→ ``block_kind``(現行形式の腕のための決定論的写像)。
  - `draw_windows`(関数): 設計書 §2 の写像(雇用形態 → 行 → 出勤/帰宅 → 始業/終業 → 欠勤)を体ごとに引く。
  - `employment_row`(関数): 雇用形態 → 第31表の行名(按分は ``employment_mix`` の重みで逆関数法)。
  - `example_block`(関数): **その体の事実から組んだ**例示(d0 の 1 日ぶん)。user 側に置く。
  - `files_avoid_production_globs`(関数): 本番 glob に当たる名前を返す(空なら安全)。**テストが機械検査する**(§7 リスク 8)。
  - `ingest_arm`(関数): 応答を読み、**修復せずに**検査して報告する(P0b だけ修復版も別に出す)。
  - `ingest_production`(関数): 本番 v2 の取り込み。**修復なし**・raking は 12%/0% を両方計算し**採用は 0%**。
  - `inverse_sample`(関数): 逆関数法 + **ビン内一様**。``u ∈ [0,1)`` → 分。
  - `load_anchor`(関数): アンカー台帳を読む(無ければ ``FileNotFoundError``)。
  - `load_failed_ids`(関数): ``--retry-failed`` の入力を読む。``w17_gates.json``(report)でも id の羅列でもよい。
  - `main`(関数)
  - `mock_text`(関数): その体の事実に素直に従った応答本文(**検収のドライラン用**・LLM は呼ばない)。
  - `parse_blocks`(関数): ブロック形式の応答本文 → (ブロック列, 理由の計数)。**壊れた行はその行だけ捨てる**。
  - `production_rows`(関数): 本番は**全体**(層化しない)= W16 の行順そのまま。
  - `production_spec`(関数): 本番 v2 の腕(P2′ の型・``days`` 日・段2)。
  - `promote`(関数): ``w17v2/`` の parquet と header を本番へ**コピー**し、旧版を退避する(親が実行)。
  - `sample_rows`(関数): 種別ごとの層化標本(``_mix64(agent_id)`` 昇順の先頭 n 体・``pilot_rows`` と同規約)。
  - `trial_file`(関数): 下見の出力名(``w17_trial_<arm>[_stage2]_<suffix>``)。
  - `u01`(関数): ``blake3(SEED_TAG_V2 ‖ domain ‖ ":" ‖ agent_id)`` → ``[0, 1)`` の一様乱数。
  - `write_arm_prompts`(関数): 腕のプロンプト jsonl を書く(1 行の形は本番の fleet_gen 入力と同じ)。
  - `write_mock_responses`(関数): 検収のドライラン用のモック応答 jsonl(``fleet_gen`` の出力形式)。
  - `write_production`(関数): ``w17_schedule.parquet`` / ``W17.header.json`` / ``w17_gates.json`` を**隔離先へ**書く。
  - `write_production_prompts`(関数): 本番 v2 のプロンプト jsonl を**ストリーミングで**書く(39 万行をメモリに載せない)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.w16_population`・`shibuya.build.sched.pool_facts`・`shibuya.build.sched.vocab`・`shibuya.build.sched.w17_schedule`・`shibuya.foundation.hashing`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.build.sched.w20_calendar_1a`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/build_sched/test_trial.py`・`tests/build_sched/test_w20_calendar_1a.py`・`tests/tools/test_anchor_gauge.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--anchor`: commute_time_dist_r3.json の場所
  - `--arm`: (help を読めない)
  - `--build-anchor`: 第31/36表の xlsx からアンカー台帳を作り直す
  - `--data`: 入力データ根(プール)
  - `--days`: 段2 の日数(1=月曜 d0 のみ)
  - `--identity`: 段1 の応答 jsonl(--stage 2 用)
  - `--ingest`: 応答 jsonl
  - `--ingest-production`: 本番 v2 の段2 応答 jsonl(修復なし・raking 採用 0%%)
  - `--max-tokens`: 段2 の生成上限を上書き
  - `--mock`: モック応答を書いてそれを取り込む
  - `--model-tag`: "32b" で 200 体の比較腕にする
  - `--n-per-kind`: 種別ごとの体数("40" か "0=100,3=20")
  - `--no-absent`: 行動者率による欠勤を引かない
  - `--no-parquet`: parquet を書かない
  - `--out`: 下見の出力根(既定 data/world/v2/trials)
  - `--production`: 全 390,067 体の本番プロンプトを書く(層化しない・出力先は隔離)
  - `--promote`: 隔離先の parquet/header を本番へコピーし旧版を退避する
  - `--retry-failed`: 検査に落ちた体だけ段2 を作り直す(w17_gates.json か id の羅列)
  - `--seed-bump`: 引き直しの seed 加算(--retry-failed と併用・最大 1 回)
  - `--stage`: 2 段腕の段(1=同一性 / 2=週次表)
  - `--stay-kinds`: 宿泊客とみなす種別(既定 7=訪日)
  - `--time-fact-repair`: 家を出る/帰宅の移動行を事実行の時刻へ合わせる(既定オフ=計数のみ)
  - `--world`: W16/W7/W6/W12 の場所
- 決定の ID: D-63・D-67・D-68

## [vocab.py](../../../../../../../../src/shibuya/build/sched/vocab.py)

build.sched.vocab — W17 週次活動表の**凍結語彙と行書式**(整形器・パーサ)。

- 公開の関数とクラス
  - `Act`(クラス): 活動 1 件(1 行)。``start``/``end`` は 0-1440 の分(``end`` は排他)。
  - `canonical_text`(関数): 応答本文の正規化(NFKC・``<think>`` 除去・改行 LF・行頭記号落とし)。
  - `format_body`(関数): 1 活動 → **日見出し形**の活動行(曜日を持たない 3 列)。
  - `format_line`(関数): 1 活動 → 1 行。``end==1440`` は ``2400`` と書く(24 時越えの分割点)。
  - `format_schedule`(関数): 活動列 → 応答本文(**日見出し形**・7 日ぶんの見出しを必ず出す)。
  - `format_schedule_flat`(関数): 活動列 → **旧形式**(1 行に曜日)。互換テスト用。
  - `parse_line`(関数): 1 行 → (活動 0-2 件, 不採用理由, 直した印)。理由が空文字なら採用。
  - `parse_text`(関数): 応答本文 → (活動列, 理由の計数)。**壊れた行はその活動だけ捨てる**。
- import している内部モジュール: `shibuya.foundation.time_consts`
- 呼び手: `shibuya.build.sched.trial`・`shibuya.build.sched.w17_schedule`・`tools/instruments/anchor_gauge.py`・`tools/w17/diversity_yardstick.py`
- 読む試験: `tests/build_geo/test_poi_class.py`・`tests/build_sched/conftest.py`・`tests/build_sched/test_trial.py`・`tests/build_sched/test_w17_ingest.py`・`tests/build_sched/test_w17_parse.py`・`tests/build_sched/test_w17_prompts.py`・`tests/build_sched/test_w17_repair.py`・`tests/build_sched/test_weekly_loader.py`・`tests/engine/test_eatery_place_food.py`・`tests/w17/test_diversity_yardstick.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w17_schedule.py](../../../../../../../../src/shibuya/build/sched/w17_schedule.py)

W17 スケジュール生成(§1 W17・D-W17・決定台帳「母集団合成」⑦)。

- 公開の関数とクラス
  - `AgentFacts`(クラス): W17 の生成・修復が使う個体の事実(行順=``w16_population`` の行順)。
  - `IngestReport`(クラス): 取り込みの集計(``w17_gates.json`` の中身)。
  - `RakeReport`(クラス): raking の前後(ゲート json へ)。
  - `RepairCounters`(クラス): 修復規則ごとの適用件数(ゲート json へ)。
  - `SchedPrompt`(クラス): 1 呼ぶんのプロンプト(``tools/gen/fleet_gen.py`` の入力行)。
  - `agent_seed`(関数): ``seed = blake3(SEED_TAG ‖ ":" ‖ agent_id) mod (2^53−1)``(D-W17 「seed=hash(agent)」)。
  - `build_facts`(関数): W16 母集団+プール素材 → ``AgentFacts``(決定論)。
  - `build_prompts`(関数): W16+プール → プロンプトの list(テスト・小規模用。実データは ``write_prompts``)。
  - `estimate_tokens`(関数): 粗いトークン数見積り(``perception.channels.estimate_tokens`` と**同一規約の二重定義**)。
  - `hour_curves`(関数): W12 の hour 重み → PT 目的別の 24 時間カーブ(和 1)。**expedient**(冒頭 docstring)。
  - `ingest`(関数): 応答を**ストリーミングで**読み、行パーサ → 整合修復 → raking を通して SoA を作る。
  - `iter_prompts`(関数): ``AgentFacts`` → プロンプト列(行順=母集団の行順・シャードは行の剰余で切る)。
  - `jensen_shannon`(関数): Jensen-Shannon divergence(底 2・0..1)。両方 0 の成分は 0 として扱う。
  - `open_share`(関数): W7+W6 → ``(場所種別, 曜日, 時)`` の開店率(その時間帯に開いている POI の割合)。
  - `pilot_rows`(関数): **種別ごとに ``per_kind`` 体**を決定論で抜いた行索引(昇順)。
  - `place_set`(関数): その体が**書いてよい場所語**(事実にない場所を regex で排除する)。
  - `prompt_bytes`(関数): プロンプト列 → jsonl の行バイト(決定論・LF 固定・キー整列)。
  - `prompt_of`(関数): 行 ``i`` の 1 呼ぶんのプロンプト(決定論)。
  - `prompt_regex`(関数): vLLM の構造化出力(``structured_outputs.regex``)に渡す正規表現。
  - `prompts_sha256`(関数): プロンプト列の版ハッシュ(文面を変えたら値が変わる=改版の検出器)。
  - `rake`(関数): 目的別の**開始時刻分布**を時間帯カーブへ寄せる(配列は in-place で書き換える)。
  - `regex_summary`(関数): 構造化出力 regex の版(ヘッダ ``notes``・登録簿用)。
  - `repair`(関数): 7 日ぶんの修復(``repair_day`` を曜日ごとに)。
  - `repair_day`(関数): 1 日ぶんの活動を整合させる。返り値=(修復後, 行ごとの修正フラグ, 捨てた件数)。
  - `response_files`(関数): 応答 jsonl(名前順=決定論)。
  - `run`(関数): W17: プロンプトを書き、応答があれば取り込んで週次表を凍結する(純関数)。
  - `shard_name`(関数): シャードのファイル名(``n_shards==1`` は素の ``w17_prompts.jsonl``)。
  - `skeleton`(関数): 骸格スケジュールの 7 日ぶん(``skeleton_day`` を曜日ごとに)。
  - `skeleton_day`(関数): 骸格スケジュールの **1 日ぶん**(全て expedient)。
  - `system_prompt`(関数): 種別 → 凍結 system プロンプト(``SYSTEM_COMMON`` + 種別 1 行)。
  - `system_sha256`(関数): 種別別テンプレの凍結 SHA(D-W17 (ii)「プロンプト=種別別テンプレ凍結(SHA)」)。
  - `user_prompt`(関数): 個体 ``i`` の user プロンプト(決定論・**セル ID は載せない**=答申 Q4-2)。
  - `write_pilot_prompts`(関数): 種別ごとに ``per_kind`` 体のパイロット用プロンプト jsonl を書く。
  - `write_prompts`(関数): プロンプト jsonl を**ストリーミングで**書く(39 万行をメモリに載せない)。
  - `write_schedule`(関数): SoA → ``w17_schedule.parquet``(行グループ単位で書く=全体を 1 テーブルに積まない)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.w16_population`・`shibuya.build.sched.pool_facts`・`shibuya.build.sched.vocab`・`shibuya.foundation.hashing`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.build.sched.run`・`shibuya.build.sched.trial`・`tools/c8/sensitivity.py`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/build_geo/test_poi_class.py`・`tests/build_sched/test_trial.py`・`tests/build_sched/test_w17_ingest.py`・`tests/build_sched/test_w17_prompts.py`・`tests/build_sched/test_w17_repair.py`・`tests/build_sched/test_weekly_loader.py`・`tests/engine/test_eatery_place_food.py`・`tests/engine/test_presence_executor.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w20_calendar_1a.py](../../../../../../../../src/shibuya/build/sched/w20_calendar_1a.py)

build.sched.w20_calendar_1a — 構築側の段 W20(暦 1a・勤務と授業の約束の週の表・第 3 期 3-1)。

- 公開の関数とクラス
  - `Attributes`(クラス): 体ごとの属性(行順=W16 の行順)。:func:`calendar_from_attributes` の入力。
  - `Employment`(クラス): 従業上の地位(``ST_*``)・第 31/36 表の行(``EMP_ROWS`` の番号・−1=無し)・地位の出どころ(``SRC_*``)と数。
  - `Materials`(クラス): 材料の表(:func:`build_materials` の辞書)を引く口。試験は作り物の辞書でも作れる。
  - `R99Guard`(クラス): ``research_cache/r99`` の読み口の守り(名で縛る+監査フック)。
  - `ValidationTableError`(クラス): 検証側の表(第14・15・68-3表)か、``research_cache/r99`` の許可の外のファイルを開こうとした(開く前に落とす)。
  - `annual_check`(関数): 年間の整合の計器(親の判断 第336 (1)・診断=合否にしない): 予定の週の日数 × 365/7 と、第19表(特別区部)の年間就業日数
  - `attributes_from_columns`(関数): 列の辞書(W16 と同じ名)+ペルソナの欄 → :class:`Attributes`。逐次ループ宣言: 体の数ぶん(文字列の欄の読み替え)。
  - `attributes_from_world`(関数): W16 の体の表(``<world_dir>/w16_population.parquet``)+ペルソナ → :class:`Attributes`(**ここだけが人口に依る**)。
  - `build_materials`(関数): 構築側の 4 本の xlsx・第 31/36 表の錨・産業の写像から材料の表(JSON にできる辞書)を作る。
  - `calendar_from_attributes`(関数): 属性と従業上の地位 → 週の表(体 × 週 × 曜日の列の辞書)と数(``counters``)。決定的・体の数に依らない。
  - `draw_employment_status`(関数): 勤務の約束を持つ体の従業上の地位(第6-2表の 6 区分)と第 31/36 表の行を決める(親の判断 2026-10-15 の 3・4)。
  - `draw_u`(関数): ``[0, 1)`` の一様変数(体・週・曜日がカウンタ・鍵は :data:`SEED_KEY` と用途の名)。決定的・体の数に依らない。
  - `duty_role_check`(関数): duty_role の在庫と経済センサスの二重計上の確かめ(記録の表)。
  - `extract_19`(関数): 第19表 → 特別区部・男女総数・(雇用形態, 産業 3 部門)の年間就業日数の階級の人数と平均の日数(階級の中央の値)。
  - `extract_6_2`(関数): 第6-2表 → 渋谷区(13113)の産業(全体・大分類・中分類)× 従業上の地位 6 区分の従業者数(男女計)。
  - `extract_74_6`(関数): 第74-6表 → 東京都・男女総数・(従業上の地位|勤務形態)× 曜日の「仕事」の行動者率(0〜1)。
  - `extract_74_9`(関数): 第74-9表 → 東京都・男女総数・職業 × 曜日(平日/土/日)の「仕事」の行動者率(0〜1)と推定人口・サンプル。
  - `hist15`(関数): 分 → 15 分の枠(96)の数(1 日の分を超える値は翌日の同じ枠に畳む)。
  - `inverse_sample_array`(関数): ``trial.inverse_sample`` の配列の版(同じ式・試験が値の一致を見る)。
  - `iter_xlsx_rows`(関数): xlsx(1 シート目)の行を順に返す(``ET.iterparse``=大きな表でも行ごとに捨てる)。開く前に守りで照らす。
  - `load_materials`(関数)
  - `load_weekly_rest_rule`(関数): 規則の表から週 1 日の休みの行(:data:`WEEKLY_REST_RULE_ID`)を読む(JSON を直に読む=build は engine を import しない)。
  - `main`(関数)
  - `read_pool_fields`(関数): ``(pool_layer, pool_index)`` の並びに対応するペルソナの欄(``pool_facts.read_facts`` と同じ読み方・必要な行だけ)。
  - `rest_day_draw`(関数): 休みの曜日を、その曜日の「働かない率」(1 − 予定の率)に比例して 1 日引く(``u``=体・週の鍵の一様変数・決定的)。
  - `rest_day_of`(関数): 体ごとの、曜日の予定の率が最も低い曜日(同じなら後の曜日=日曜)。:func:`rest_day_draw` の受け皿(働かない率が全部 0)。
  - `rest_statuses_of`(関数): 規則の表の行の ``applies_to_status``(地位の語)→ 地位の符号(行に無ければ :data:`REST_STATUSES`)。
  - `run`(関数): 段 W20cal: W16+ペルソナ+構築側の表 → ``w20_calendar_1a.parquet``・材料の表・ヘッダ(``calendar_1a.header.json``)。
  - `stage_params`(関数): 段の ``params``(``param_hash`` の元)。〔第 4 期 4-3 段 10〕差し替えの母集団で組む口(``build.pop.w21_apply``)も同じ関数を
  - `table_stats`(関数): 週の表の統計(曜日ごとの約束の数・空欄の数・出勤・始業・終業・帰宅の分位・通勤時間・日数の分布)。
  - `week_of`(関数): 日付 → 週の番号(:data:`WEEK0_MONDAY` の週を 0)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.pop.w16_population`・`shibuya.build.sched.pool_facts`・`shibuya.build.sched.trial`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.build.audit.w19_freeze`・`shibuya.build.pop.w21_apply`・`shibuya.build.sched.w20_w21_port`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_sched/test_w20_calendar_1a.py`・`tests/build_sched/test_w20_w21_port.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/calendar/test_calendar_shadow.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--data`
  - `--out`: W16 の出力がある置き場(例 data/world/v2_stage_3-1)
  - `--weeks`
- 決定の ID: R-99・R-116・第 336・第 337

## [w20_w21_port.py](../../../../../../../../src/shibuya/build/sched/w20_w21_port.py)

build.sched.w20_w21_port — W21(人口の作り直し)の人の表 → W20(暦 1a)の ``Attributes`` を作る口(第 4 期 4-1 段 10 の材料)。

- 公開の関数とクラス
  - `UnknownDutyRoleError`(クラス): W21 の担当の語が W20 の ``DUTY_ROLE_SPEC`` の鍵に無い(黙って「担当なし」にしない)。
  - `UnknownEmploymentStatusError`(クラス): 勤務の約束を持つ体の W21 の地位の語が 8 区分に無い(黙って正規にしない)。
  - `attributes_from_w21`(関数): W21 の人の表(``w21_people`` の列+段 3 の ``school_kind``=:data:`W21_INPUT_COLUMNS`)→ W20 の ``Attributes``。
  - `duty_role_spec`(関数): 本口が引く担当の語の表(W20 の 22 語+W21 の 4 語=鍵は重ならない)。
  - `employment_from_w21`(関数): W21 の体の従業上の地位(8 区分)→ W20 の ``Employment``(第6-2表の 6 区分・第 31/36 表の行)を直接写す。
  - `lead_minutes`(関数): 片道の通勤時間[分]: 歩き=道のり ÷ 歩く速さの参照値(切り上げ・少なくとも 1)・自宅=0・ほか(電車の人)は −1(空欄=W20 の
- import している内部モジュール: `shibuya.build.pop.attr_fns`・`shibuya.build.sched.w20_calendar_1a`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.build.pop.w21_apply`・`shibuya.build.pop.w21_build_c`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/build_sched/test_w20_w21_port.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 第 337
