# tools/instruments/leak_check

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 6 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [question_sets](question_sets/README.md)

## [__init__.py](../../../../../../../tools/instruments/leak_check/__init__.py)

leak_check — データ漏洩(学習データの混入)の検査の器(回答 11-01 §6・指示 11-01 段 1 の 4)。

- 呼び手: `tools/instruments/leak_check/run.py`・`tools/instruments/leak_check/sets.py`
- 読む試験: `tests/tools/test_leak_check.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- 決定の ID: 11-01・11-01/§6

## [backends.py](../../../../../../../tools/instruments/leak_check/backends.py)

leak_check.backends — 当て口(``mock``=決定的・``vllm``=127.0.0.1 の OpenAI 互換 ``/v1/chat/completions``)。

- 公開の関数とクラス
  - `Backend`(クラス)
  - `BackendError`(クラス): 当て口の失敗(HTTP の失敗・応答の形の違い)。
  - `MockBackend`(クラス): 決定的な当て口(種と問いの文の鍵)。
  - `Reply`(クラス)
  - `VllmBackend`(クラス): vLLM(OpenAI 互換)の当て口。口は 127.0.0.1 に固定。
  - `http_post`(関数): HTTP の POST(標準ライブラリ ``http.client``)。
  - `make_backend`(関数)
  - `parse_top_logprobs`(関数): OpenAI 互換の ``choices[0].logprobs.content[0].top_logprobs`` → トークン → 対数確率。無ければ None。
- 呼び手: `tools/instruments/leak_check/cli.py`・`tools/instruments/leak_check/run.py`
- 読む試験: `tests/tools/test_leak_check.py`
- 環境変数: 名前を読めない所 2 か所

## [cli.py](../../../../../../../tools/instruments/leak_check/cli.py)

leak_check.cli — 漏洩の検査を 1 回通して ``result.json``(集計だけ)と ``table.md`` を書く。

- 公開の関数とクラス
  - `AbsolutePathInRecord`(クラス): 記録の文に絶対の道筋の形がある。
  - `build_parser`(関数)
  - `check_args`(関数): 引数の検査(合わなければ分かる文で rc 2)。
  - `check_no_abs_path`(関数)
  - `main`(関数)
  - `run_once`(関数)
  - `write_outputs`(関数)
- import している内部モジュール: `tools/instruments/leak_check/backends.py`・`tools/instruments/leak_check/run.py`・`tools/instruments/leak_check/score.py`
- 読む試験: `tests/tools/test_leak_check.py`
- CLI の引数
  - サブコマンド `run`
  - サブコマンド `summary`
  - `--backend`
  - `--cont-chars`: (help を読めない)
  - `--expect-md5`: 型 ①・④: 入力の JSONL の md5(違うか、ファイルが無ければ止まる)
  - `--key-env`: API key を読む環境変数の名
  - `--limit`: 試走: 各集合の先頭 N 件だけ(1 以上)
  - `--min-mass`: 型 ②: 番号に乗った確率の和の下限(これより小さければ本文の番号)
  - `--mock-seed`
  - `--model`: vLLM の served-model-name(vllm では必須)
  - `--model-cutoff`: 型 ①: モデルの学習の締め切り(YYYY-MM か YYYY-MM-DD・任意)
  - `--model-version`: モデルの版(重みの revision・sha など)=台帳の 1 行の頭に付ける
  - `--out-dir`
  - `--port`: vLLM の口(127.0.0.1 に固定・1〜65535)
  - `--prefix-chars`: (help を読めない)
  - `--real-events`: 型 ①: 実在の出来事の JSONL(既定 data/leak_check/)
  - `--recall-refs`: 型 ④: 参照の JSONL(既定 data/leak_check/)
  - `--seed`: (help を読めない)
  - `--type`
  - `results`

## [run.py](../../../../../../../tools/instruments/leak_check/run.py)

leak_check.run — 型ごとに 1 回通して集計(``result.json`` の中身)と表(``table.md``)を作る。

- 公開の関数とクラス
  - `InputMismatch`(クラス): 親が置いた入力の md5 が渡した値と違う・md5 を渡したのにファイルが無い・形が違う。
  - `check_when`(関数): ``YYYY-MM`` か ``YYYY-MM-DD``(月は 01〜12・日は暦に合う)。合わなければ ``InputMismatch``。
  - `cutoff_side`(関数): モデルの学習の締め切り ``cutoff``(``YYYY-MM`` か ``YYYY-MM-DD``)に対する前後。
  - `digest_of`(関数): 記録の決定的な部分(``wall_s`` と ``digest`` を除く)の sha256(鍵の順をそろえた JSON)。
  - `ledger_block`(関数): 型 ①②④ の文をまとめた 1 行(頭にモデル名と版・測っていない型は「未測」)。
  - `ledger_part`(関数): 運用規則 9 の欄に写す型ごとの短い文。
  - `load_input`(関数): 親が置く入力を読む。無ければ ``([], 未投入)``(md5 を渡したのに無ければ ``InputMismatch``)。md5 は生のバイト。
  - `merge_ledger`(関数): いくつかの ``result.json`` の型ごとの文を 1 行にまとめる(同じ型が 2 つあれば後の方)。
  - `model_label`(関数)
  - `run_type1`(関数)
  - `run_type2`(関数)
  - `run_type4`(関数)
  - `to_markdown`(関数)
- import している内部モジュール: `tools/instruments/leak_check/__init__.py`・`tools/instruments/leak_check/backends.py`・`tools/instruments/leak_check/score.py`・`tools/instruments/leak_check/sets.py`・`tools/instruments/read_guard.py`
- 呼び手: `tools/instruments/leak_check/cli.py`
- 読む試験: `tests/tools/test_leak_check.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- 決定の ID: 11-01/§7

## [score.py](../../../../../../../tools/instruments/leak_check/score.py)

leak_check.score — 採点(型 ①・②・④)。どれも応答の本文を記録に写さない(分類の印と数だけを返す)。

- 公開の関数とクラス
  - `choice_distribution`(関数): 候補 k 個の上の分布(番号 1〜k)と出所と被覆(番号に乗った確率の和)と本文へ落とした理由。読めなければ None。
  - `classify_dates`(関数): 型 ① (a) の応答 → ``unknown`` / ``has`` / ``other``。
  - `classify_events`(関数): 型 ① (b) の応答 → ``agree`` / ``deny`` / ``unknown`` / ``other``。
  - `diff_or_none`(関数)
  - `event_lines`(関数): 具体名の判定をかける行: unknown は空・1 行目が形に合った応答は 2 行目から・合わない応答は全部の行。
  - `exact_match`(関数): 正規化した出力の頭が正規化した参照と同じ(参照が空なら False)。
  - `has_denial`(関数): 否定の言い回しがあるか(判定語の表 ``DENY_PATTERNS``)。
  - `has_event_line`(関数): 出来事の行が 1 つ以上あるか(行を節に分けて ``is_event_clause`` で見る)。
  - `has_specific_name`(関数)
  - `has_unknown`(関数): 「知らない」の言い回しがあるか(判定語の表 ``UNKNOWN_PATTERNS``)。
  - `is_event_clause`(関数): 出来事の節か(出来事の動詞があり、同じ節に「知らない」も否定も無い)。
  - `jsd`(関数): Jensen-Shannon の発散(底 2・0〜1)。長さは同じ。
  - `lcs_len`(関数): 最長共通部分列の長さ(文字の単位・O(len(a)·len(b)))。
  - `longest_common_substring`(関数): 最長の連続する共通の部分の長さ。
  - `mean_or_none`(関数)
  - `name_mass`(関数): 名を含む候補の確率の和。名を含む候補が無ければ None。
  - `name_tokens`(関数): 具体名の印になる語(問いの文 ``given`` に出た語と一般語を除く)。英語は ``_en_tokens`` の 3 つの印だけ。
  - `norm`(関数): 判定語の表に当てる形(NFKC・小文字・曲がったアポストロフィ → ``'``)。
  - `normalize_text`(関数): NFKC・小文字・空白と句読点と記号を除く。
  - `performance_gap`(関数): Glasserman & Lin 型「名前で成績が変わる」: 人の分布との JSD の平均を実名版と架空名版で比べる。
  - `recall_scores`(関数): 1 件の採点: 完全一致・正規化した部分一致・最長共通部分列の率(参照に対する再現率と F)。
  - `sign_test_p`(関数): 符号の検定(両側・厳密な二項 p=0.5)。0 の差は呼ぶ側で外す。
  - `summarize_pairs`(関数): 対の集計(JSD・1 位の一致率・名の向き=実名版 − 架空名版 の名を含む候補の確率・符号の検定・被覆)。
  - `summarize_recall`(関数)
  - `summarize_type1`(関数): ``items`` の各行は ``cls``(分類)と ``specific``(具体名の有無)を持つ。``classes`` ごとの率と件数。
  - `token_number`(関数): トークン → 番号(NFKC にして前後の空白と句読点を外し、数字だけになれば番号)。
  - `top1`(関数): 1 位の番号(1 から・同点は小さい番号)。
- 呼び手: `tools/instruments/leak_check/cli.py`・`tools/instruments/leak_check/run.py`
- 読む試験: `tests/tools/test_leak_check.py`
- 決定の ID: 11-01/§7

## [sets.py](../../../../../../../tools/instruments/leak_check/sets.py)

leak_check.sets — 問いの集合(型 ①・②・④)を作る。``python -m leak_check.sets --write`` で ``question_sets/`` に書く。

- 公開の関数とクラス
  - `block_sequence`(関数): ``input_text`` のブロックの並び(dm_eval ``split_blocks`` と同じ規則=行の頭の ``[Bx …]``・続けて並び・
  - `build_type1_dates`(関数)
  - `build_type1_events`(関数)
  - `build_type2`(関数)
  - `build_type4`(関数)
  - `choice_prompt`(関数): 場面の文(ブロック)+候補(番号つき)+指示。番号は候補の並びの順に 1 から。
  - `event_prompt`(関数)
  - `fictional_name`(関数): 実名のブランドの語だけを無意味語に置き換える(どの語も実名にちょうど 1 回出ること)。
  - `ja_month`(関数): ``YYYY-MM`` → ``YYYY年M月``。
  - `lf_md5`(関数): 改行を LF にそろえた md5(作業木の改行の変換に左右されない)。
  - `load_set`(関数): 問いの集合を読む(行と LF の md5)。
  - `main`(関数)
  - `read_jsonl`(関数)
  - `side_of`(関数): 世界の時点との前後(年月だけのときは、時点の月を「後」に数える=時点の月の出来事は時点の後でありうる)。
  - `to_jsonl`(関数): 行の並びのまま 1 行 1 件(utf-8・LF・鍵は書いた順)。
  - `write_sets`(関数)
- import している内部モジュール: `tools/instruments/leak_check/__init__.py`
- 呼び手: `tools/instruments/leak_check/run.py`
- 読む試験: `tests/tools/test_leak_check.py`
- CLI の引数
  - `--write`: question_sets/ に書く(無ければ件数だけ出す)
- 決定の ID: 10-03/§9-1
