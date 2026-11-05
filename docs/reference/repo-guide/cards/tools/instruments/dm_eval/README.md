# tools/instruments/dm_eval

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [backends](backends/README.md)・[scenes](scenes/README.md)

## [__init__.py](../../../../../../../tools/instruments/dm_eval/__init__.py)

dm_eval — 第 6 期 6-1 判断モデル(DM)の**評価の器**(GPU の前に作る分・読むだけ・エンジン不変)。

- 呼び手: `tools/instruments/dm_eval/backends/base.py`・`tools/instruments/dm_eval/backends/hf.py`・`tools/instruments/dm_eval/backends/vllm.py`・`tools/instruments/dm_eval/bias.py`・`tools/instruments/dm_eval/cli.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`・`tools/instruments/dm_eval/table.py`
- 読む試験: `tests/tools/test_dm_eval.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- 決定の ID: 11-01・R-108

## [bias.py](../../../../../../../tools/instruments/dm_eval/bias.py)

dm_eval.bias — 位置の偏りの対照試験(R-108 §1-1・§1-4・§3-1・C-2 の対策 1・第 6 期 6-1 の器)。

- 公開の関数とクラス
  - `pbs_null_floor`(関数): PBS の帰無の床(フロア併記): 中身だけで選ぶ当て口の PBS の分布を模擬で出す。
  - `position_bias`(関数): 並べ替え試験の集計(上の説明の量)。``records`` は ``score_orders`` の 1 つ目。
  - `salt_compare`(関数): 10f の salt の比較(``tools/c7/salt_compare.py``)を道筋から読む(1 回だけ)。
  - `score_orders`(関数): 状況 × 並びの全部を採点する → (状況 → [(提示, 分布)]・1 件あたりの壁時計の秒)。
  - `tape_fixed_order`(関数): テープの LLM が見た B0 の固定の並び(語彙 v1 の順)での選んだ位置の分布(記録だけ=位置と中身が分けられない)。
- import している内部モジュール: `shibuya.core.rng`・`shibuya.engine.decision.port`・`tools/instruments/dm_eval/__init__.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`
- 呼び手: `tools/instruments/dm_eval/cli.py`
- 読む試験: `tests/tools/test_dm_eval.py`
- 決定の ID: 11-01・R-108

## [cli.py](../../../../../../../tools/instruments/dm_eval/cli.py)

dm_eval.cli — 評価の器を 1 回通して、記録の JSON と表を書く(第 6 期 6-1・読むだけ・GPU とネットワークは使わない)。

- 公開の関数とクラス
  - `compare_digest_of`(関数): 比べの節の digest(壁時計を除く)。
  - `default_factories`(関数): 表の並び(宣言の順=対照 → 基準 → 候補)の当て口を作る関数(``judge.scorer_registry`` と同じ並び)。
  - `digest_of`(関数): 壁時計を除き、小数を 10 桁に丸めた決定的な部分の sha256(golden)。比べの節と表は含めない。
  - `evaluate`(関数): 状況(と本人の経験の代わり)→ 採点の結果(data は読まない)。
  - `main`(関数)
  - `model_factories`(関数): 引数 → (当て口を作る関数の並び・(G) の名)。重みと艦隊は作るときに触らない(呼ぶときだけ)。
  - `qty_measures`(関数): 〔11-01 検収 低 7〕何をいくつの数の指標(数の欄 ``qty`` が 2 通り以上ある場面=何をいくつだけ)。
  - `table_footnotes`(関数): 表の脚注(PBS の帰無の床=フロア併記・提示の並びを見ていない当て口の注・比べの列の読み方)。
  - `write_outputs`(関数): ``result.json``・``table.md``・``table.json`` を書く(LF・UTF-8)。
- import している内部モジュール: `shibuya.engine.decision.port`・`tools/instruments/dm_eval/__init__.py`・`tools/instruments/dm_eval/backends/base.py`・`tools/instruments/dm_eval/backends/hf.py`・`tools/instruments/dm_eval/backends/vllm.py`・`tools/instruments/dm_eval/bias.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`・`tools/instruments/dm_eval/table.py`
- 読む試験: `tests/tools/test_dm_eval.py`
- CLI の引数
  - サブコマンド `run`
  - `--determinism-limit`: 決定論の検査の件の上限(0=全部)
  - `--determinism-repeats`: 同一入力の回数(既定 32)
  - `--hf-device`
  - `--hf-form`
  - `--hf-model`: 候補=手元の重みの道筋(transformers・GPU の後)
  - `--hf-name`
  - `--length`: (G) と候補の口が読む文の版(DM4・既定 short)
  - `--mock-seed`
  - `--n-orders`
  - `--no-tape-experience`: 本人の経験の代わり(テープの前の呼)を使わない
  - `--out-dir`
  - `--overwrite`
  - `--scenes`: evalset=1-10 の 340 件(既定)・consumption=消費の場面・both=両方(out-dir の下に 2 つ)
  - `--seed`
  - `--vllm-api-key-env`
  - `--vllm-form`
  - `--vllm-mode`: prompt_logprobs(既定)か echo(腕)
  - `--vllm-model`: (G) の基準=127.0.0.1 の艦隊のモデルの名(GPU の後)
  - `--vllm-port`
- 決定の ID: 11-01・11-01/§11

## [judge.py](../../../../../../../tools/instruments/dm_eval/judge.py)

dm_eval.judge — 候補の当て口 ``Scorer`` と採点の器(第 6 期 6-1・DM1・DM5・DM9・§1-9)。

- 公開の関数とクラス
  - `ClassicalScorer`(クラス): 基準: 今の古典モデルの判断の分布(活動の事前分布 → 対応表 v0 → 語彙 v1)。
  - `ClefScorer`(クラス): 候補 Clef-flash(``variant="flash"``)と Clef(``"full"``)。Apache-2.0(R-83 §2-1・判断モデルの草案 DM1)。
  - `FirstNumberControl`(クラス): 位置の偏りの正の対照: いつも番号 1 を選ぶ(並べ替え試験の検出力を確かめる)。
  - `GScorer`(クラス): 基準 (G)=vLLM の 8B 級の 1 トークン目の確率(R-83 §5・DM1 の基準)。
  - `KevScorer`(クラス): 候補 Kev-9B。Apache-2.0(R-83 §2-1)。
  - `MockScorer`(クラス): 対照: 単体の上で一様な重み(Dirichlet(1))・種と状況の id の鍵・候補の中身(id)の順に引く。
  - `ScoreFailed`(クラス): 〔11-01 検収 低 4〕1 件の採点の失敗(モデルの口の後ろの失敗・切り出しの不一致など)。``evaluate`` は場面ごとに
  - `Scorer`(クラス): 候補の当て口(差し替えられる口)。実装は ``_score`` だけを書く。
  - `ScorerUnavailable`(クラス): 口だけの当て口(重みの取得と GPU の後=S6)。
  - `SokudanScorer`(クラス): 候補 即断 sokudan-ja-310m(R-94・日本語・3.1 億)。DM1 の追加の測り 3 つは欄だけ(``extra_measures``)。
  - `TapeScorer`(クラス): 基準: テープの応答(System 2 の原型=8B の記録)の行為の語に確率 1。語彙 v1 の外は「その他」。
  - `agreement`(関数): 分布の一致(状況ごとの JSD と順位相関・1 位の一致率・周辺の JSD)。``kinds`` は状況 → 候補 id → 語。
  - `determinism_check`(関数): 同一入力を ``repeats`` 回: 1 つの当て口(重みを 1 回だけ読む)で各件を続けて N 回採点し、件ごとに N 回の分布が
  - `dist_digest`(関数): 分布の列の sha256(鍵の順と float64 のバイト=厳密モードの一致の印)。
  - `failure_record`(関数): 失敗の記録の欄(型の名と分類だけ・例外の文の本文は写さない)。
  - `gpu_hours_per_sim_day`(関数): 1 シム日あたりの GPU 時間 = 呼数/日 ×(人口の倍率)× 1 件の秒 ÷ 3,600 ÷ GPU の数。1 件の秒が空なら空。
  - `hesitation`(関数): 迷い(DM5)=``port.Hesitation.of``(1 位と 2 位の差・エントロピー=自然対数)。
  - `hesitation_summary`(関数): 迷いの集計(差とエントロピーの平均と中央)。
  - `jsd`(関数): Jensen-Shannon の距離の 2 乗(発散)・底 2(0〜1)。鍵の和集合の上(無い所は 0)。
  - `normalize`(関数): 分布を検査して正規化する(鍵は提示の id と「その他」・0 以上・和が正)。並びは番号の順+「その他」。
  - `other_rate`(関数): 「その他」の確率の平均(R-108 §3-3=低い割合は候補の十分さの証拠にならない)。
  - `scorer_registry`(関数): 表の並び(宣言の順=対照 → 基準 → 候補・**指標で並べ替えない**)。
  - `spearman`(関数): 順位相関(スピアマン=順位のピアソン)。鍵の和集合の上。どちらかが一定なら None(定義できない)。
  - `speed_fields`(関数): 速さの欄(壁時計は実測・トークン数と GPU の秒は空欄=後で測る)。
  - `strict_check`(関数): 同じ入力を ``repeats`` 回(同じ並び)と、まとめ方を変えた 1 回(並びを逆)で、状況ごとの分布がバイト単位で同じか。
  - `surprise_of`(関数): 驚きの語(DM5 の 6 語)→ 0〜5。前後の空白と句読点を除いて 6 語のどれかと同じときだけ(それ以外は None)。
  - `top1`(関数): 1 位の候補の id(同点は id の順=中身で決める)。
- import している内部モジュール: `shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.engine.classical`・`shibuya.engine.decision.port`・`shibuya.llm.contract`・`tools/instruments/dm_eval/__init__.py`・`tools/instruments/dm_eval/situations.py`
- 呼び手: `tools/instruments/dm_eval/backends/base.py`・`tools/instruments/dm_eval/bias.py`・`tools/instruments/dm_eval/cli.py`・`tools/instruments/dm_eval/table.py`
- 読む試験: `tests/tools/test_dm_eval.py`
- 決定の ID: 11-01・11-01/§11・R-83・R-94・R-94 §0 #2・R-108・R-125・第 323

## [situations.py](../../../../../../../tools/instruments/dm_eval/situations.py)

dm_eval.situations — 状況の読み口(DM4)と候補の口(DM-0)(第 6 期 6-1 の器・読むだけ)。

- 公開の関数とクラス
  - `EvalsetMissing`(クラス): 評価セットのファイルが無い(data/ は gitignore の下)。
  - `Rendered`(クラス): DM4 の 1 つの文と長さの欄(``tokens`` は後で測る欄=空)。
  - `SceneSet`(クラス): 場面のファイルの中身(読むだけ)。``candidates`` は状況の id → 候補(番号なし=提示で振る)。
  - `Situation`(クラス): 評価セットの 1 件(読むだけ)。``tape_output`` はテープの応答の本文(記録に写さない・テープの当て口だけが読む)。
  - `affordance_from_facts`(関数): 1-10 の事実から「周りが示すできること」の語(語彙の順・engine の規則の形・expedient)。
  - `arm_blocks`(関数): 長さの腕で使うブロック(``ARM_DROP_BLOCKS`` を外す・並びは ``BLOCK_ORDER``)。
  - `candidate_of_spec`(関数): 場面の候補の欄 → ``Candidate``(番号なし)。知らない鍵は ``ValueError``。
  - `candidates_for`(関数): DM-0 の 5 つの源(+語彙の残り)の候補を ``engine.decision.sources.build_candidates`` で作る(番号なし)。
  - `common_text`(関数): 共通部分(B0〜B4b のうち手元にある物)の文。短い版と長い版の頭はこの文で始まる。
  - `context_of`(関数): 1-10 の状況 → ``DecisionContext``(予定は空・記憶はテープの前の呼の語=``origin="tape"``)。口は値を解釈しない。
  - `describe_candidates`(関数): 候補の集計(源ごとの提示の数・候補の数の分布)。中身の文は写さない。
  - `file_md5`(関数): ファイルの md5(16 MiB ずつ読む・封印の道筋は開く前に落とす)。
  - `iter_lengths`(関数): 腕 × 長さごとの文字数の集計(最小・中央・最大・目安を超えた件数・数字の計器)。トークン数は空。
  - `load_scene_file`(関数): 場面のファイル(jsonl+``.b0.json``+``.md5``)を読む。md5 が同梱の値と違えば ``ValueError``。
  - `load_situations`(関数): 1-10 の 340 件を読む(並びはファイルの並び=鍵の昇順)。md5 が記録と違えば ``ValueError``。
  - `md5_of`(関数)
  - `numbers_outside_money_time`(関数): 数字の並びのうち、時刻(時・分・時間・:)とお金(円・万円・千円・¥)に続かない物の数(DM4 の計器)。
  - `orders`(関数): 並べ替え試験の N 通りの提示: ``present``(種と状況の id の鍵)の並びを巡回させ、番号を 1 から振り直す。
  - `read_md5_list`(関数): ``<md5>  <ファイル名>`` の行 → {名: md5}。
  - `render`(関数): DM4 の短い版(``length="short"``=判断モデル)か長い版(``"long"``=LLM)を ``port.compose`` で作る。
  - `rotation_offsets`(関数): 巡回の位置 ``k × n // N``(k=0〜N−1)。N は 1〜n。
  - `scene_sidecars`(関数): 場面の jsonl → (前置き ``.b0.json``・md5 ``.md5``) の道筋。
  - `situation_from_row`(関数): ``situations.jsonl`` の 1 行と B0 の本文の表 → ``Situation``。
  - `situation_text`(関数): 状況の部分(共通 → 人ごと)の文=``compose`` の文から提示と指示を除いた頭(数字の計器はここだけを数える=
  - `split_blocks`(関数): ``input_text``(B1〜B4b を改行で連結)→ ブロックごとの文(行の頭の ``[Bx …]`` で分ける)。
  - `tape_experience`(関数): 本人の経験の代わり: 同じテープの同じ体の、状況より前の呼(刻みが小さい・繰り延べでない)の行為の語を新しい順に k 呼。
  - `verify_tape_md5`(関数): 状況のあるテープの ``calls.parquet`` の md5 を 1-10 の ``summary.json`` の表(``md5_calls``)と照らす。
  - `word_of_output`(関数): テープの応答(2 行形)の行為の語(語彙 v1 の横断語だけ・それ以外は None)。
- import している内部モジュール: `shibuya.core.rng`・`shibuya.core.time_consts`・`shibuya.engine.decision.port`・`shibuya.engine.decision.sources`・`shibuya.llm.contract`・`shibuya.llm.parser`・`tools/instruments/dm_eval/__init__.py`・`tools/instruments/read_guard.py`
- 呼び手: `tools/instruments/dm_eval/backends/base.py`・`tools/instruments/dm_eval/bias.py`・`tools/instruments/dm_eval/cli.py`・`tools/instruments/dm_eval/judge.py`
- 読む試験: `tests/build_pop/test_w21_stage10_swap.py`・`tests/build_pop/test_w21_stage8_9.py`・`tests/tools/test_dm_eval.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- 決定の ID: 11-01・11-01/§2・R-108

## [table.py](../../../../../../../tools/instruments/dm_eval/table.py)

dm_eval.table — 表「人らしさ × 速さ × 1 シム日あたりの GPU 時間」(DM1・§1-9・第 6 期 6-1 の器)。

- 公開の関数とクラス
  - `blank_reason`(関数): 空の欄の印(値があれば ``None``・注の欄は空でよい=``""``)。``missing_refs`` は記録の無い基準の名。
  - `blanks_of`(関数): 行ごとの空の欄 → 印(注の欄は除く)。
  - `build_rows`(関数): 当て口ごとの結果(``cli.evaluate`` の ``scorers`` の各要素)→ 表の行。
  - `order_blind_note`(関数): 提示の並びを見ていない当て口の注(表だけを読んで位置の偏りが無いと読めないように)。
  - `to_json`(関数)
  - `to_markdown`(関数): 表を Markdown に(空の欄は ``blank_reason`` の印)。
- import している内部モジュール: `tools/instruments/dm_eval/__init__.py`・`tools/instruments/dm_eval/judge.py`
- 呼び手: `tools/instruments/dm_eval/cli.py`
- 読む試験: `tests/tools/test_dm_eval.py`
- 決定の ID: 10-12/§1-9・11-01
