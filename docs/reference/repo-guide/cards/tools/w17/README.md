# tools/w17

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 1 本・その他 0 本(このディレクトリの直下)

## [diversity_yardstick.py](../../../../../../tools/w17/diversity_yardstick.py)

diversity_yardstick.py — **個体の行動多様性の物差し**(D-68 下見 P0/P0b/P1a/P1b/P2)。

- 公開の関数とクラス
  - `Sample`(クラス): 1 標本(1 腕の 1 ラン)。行は ``(体行, 曜日, 並び)`` 昇順。
  - `ScopeCache`(クラス): 1 つの曜日スコープ(平日 / 全 7 日)について、**種別に依らない**中間結果を 1 度だけ作る。
  - `anchors_echo`(関数): 報告に載せる現実側の数値(出典つきで JSON に残す)。
  - `block_consistency`(関数): ``block_kind`` と場所語の矛盾を数える(計画実行層設計書 §9 の検査項目)。**純関数**。
  - `build_payload`(関数): 1 標本(または前後 2 標本・フロア 2 標本)→ 出力 JSON まるごと。**純関数**。
  - `build_scope`(関数): 1 スコープぶんの中間結果を作る(種別に依らない部分は**ここで 1 度だけ**)。
  - `canonical_motif`(関数): 有向グラフ(節点ラベルなし)の**正準形**と「総当たりできたか」。**純関数**。
  - `check_anchors`(関数): 必須欄(source/verified_by/tag)と値の存在を検査する。**純関数**(例外で知らせる)。
  - `compare`(関数): 指標ごとに「現実アンカーとの距離」と「前より近づいたか」を並べる。**純関数**。
  - `covered_minutes`(関数): (体・日)ごとに**重なりを除いた**被覆分。**純関数**・ループなし。
  - `dig`(関数): 入れ子辞書から経路で取り出す(欠けていたら ``None``)。**純関数**。
  - `floor_rows`(関数): 同腕 2 標本の差 ``|A−B|`` = 揺らぎのフロア。**純関数**。
  - `group_digests`(関数): CSR 区切りごとの 8 バイトダイジェスト(空区間も一意に区別する)。**純関数**。
  - `jsonable`(関数): numpy のスカラを Python の型へ落とす(``json.dumps`` が通るように)。**純関数**。
  - `load_anchors`(関数): アンカー台帳を読む。**必須欄が欠けていたら落とす**(推測で埋めない)。
  - `main`(関数)
  - `markdown`(関数): JSON と同じ内容の表。**合格線は書かない**(距離と bool だけ)。
  - `mean_sd`(関数): 平均・標準偏差(母標準偏差 ddof=0)・件数。**純関数**。
  - `measure`(関数): 1 標本 → 全スコープ・全種別の表。**純関数**。
  - `measure_group`(関数): 1 つの (曜日スコープ × 種別) の指標一式。**純関数**(配列を畳むだけ)。
  - `merge_anchor_docs`(関数): 複数の台帳を 1 つに戻す(``anchors`` は合わせる・同じ名は止める・ほかの鍵は前の側を残す)。
  - `motif_table`(関数): モチーフ索引の並び → 出現率 ``threshold`` 以上の形の個数と累積被覆。**純関数**。
  - `parse_response_text`(関数): 応答本文 → ``(活動列, block_kind 列, 理由の計数, 検査した行数)``。**純関数**。
  - `population_kind_counts`(関数): W16 母集団の種別ごとの体数(層化重み ``w_k`` の分子)。資産が無ければ ``None``。
  - `prior_rows`(関数): 設計書 §5 の前値と実測を並べる(**物差し自身の再現性検査**)。**純関数**。
  - `read_extra_columns`(関数): ``block_kind``/``arm`` 列があれば読む(無ければ ``None``)。行順は ``_COLUMNS`` と同じ。
  - `read_responses`(関数): 応答 jsonl → ``{id: text}``。**同じ id が二度書かれたら最後の行を採る**
  - `read_weekly_any`(関数): ``--parquet`` の引数 → ``(WeeklySchedule, 読んだファイル)``。**純関数**。
  - `restrict_agents`(関数): 先頭 ``limit`` 体だけに絞る(小さく回すため・**決定論**=agent_id 昇順の先頭)。
  - `sample_from_responses`(関数): 下見の応答 jsonl → ``Sample``(**修復なし**)。
  - `sample_from_weekly`(関数): W17 週次表 parquet → ``Sample``。``load_weekly`` の CSR を行ごとの形に展開する。
  - `signature_stats`(関数): 体ごとの署名ダイジェスト → 種類数・種類率・上位 1 型の占有率。**純関数**。
  - `time_stats`(関数): 開始分の並び → ``:00+:30`` 率・15 分ビンの最頻と占有率・エントロピー。**純関数**。
  - `unverified_anchors`(関数): ``verified_by`` が「未確認」で始まるアンカーの名前(報告に印を出すため)。
- import している内部モジュール: `shibuya.build.sched.vocab`・`shibuya.world.facts.population_reader`・`shibuya.world.facts.weekly_reader`・`tools/c6/c6lib.py`
- 読む試験: `tests/tools/test_seal_split_337.py`・`tests/w17/conftest.py`
- CLI の引数
  - `--anchors`: アンカー台帳(複数なら合わせる。既定 構築側+検証側の 2 本=DEFAULT_ANCHORS_PATHS)
  - `--before-label`: before 側の名前
  - `--before-parquet`: 比較元(.parquet ファイル でも ディレクトリ でもよい)
  - `--before-responses`: 比較元の応答 jsonl
  - `--floor`: 同腕 2 標本(parquet か jsonl)= 揺らぎのフロア
  - `--label`: after 側の名前
  - `--limit-agents`: 先頭 N 体だけ測る(小さく回す)
  - `--out`: 出力ディレクトリ(既定=標準出力のみ)
  - `--parquet`: W17 週次表(.parquet ファイル でも 世界資産ディレクトリ でもよい)
  - `--responses`: 下見の応答 jsonl(複数可)
  - `--world`: 世界資産(種別と層化重みの出所)
- 決定の ID: D-63・D-68・第 154・第 337
