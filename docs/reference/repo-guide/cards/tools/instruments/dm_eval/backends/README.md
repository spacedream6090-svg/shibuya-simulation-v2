# tools/instruments/dm_eval/backends

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../tools/instruments/dm_eval/backends/__init__.py)

dm_eval.backends — モデルの当て口(〔11-01 段 1 の 3〕判断モデルの候補と Qwen3-8B の logprob=(G) 案の比べ)。

- import している内部モジュール: `tools/instruments/dm_eval/backends/base.py`・`tools/instruments/dm_eval/backends/hf.py`・`tools/instruments/dm_eval/backends/vllm.py`
- 読む試験: `tests/tools/test_dm_eval.py`
- 決定の ID: 11-01・R-125

## [base.py](../../../../../../../../tools/instruments/dm_eval/backends/base.py)

dm_eval.backends.base — モデルの当て口の抽象(〔11-01 段 1 の 3〕判断モデルの候補と (G) の比べ・重みは取らない)。

- 公開の関数とクラス
  - `BackendError`(クラス): 口の後ろの物の答えが読めない(形の違い)。``evaluate`` は場面ごとに捕まえて失敗と記録する。
  - `BackendHTTPError`(クラス): 艦隊への HTTP の失敗(200 でない・接続の失敗)。
  - `BackendTimeout`(クラス): 艦隊の答えが時間内に来ない。
  - `BackendUnavailable`(クラス): 口の後ろの物(transformers・torch・艦隊)が手元に無い(GPU の後・pip は許可の後)。
  - `ChoiceBackend`(クラス): 候補の文字列の logprob を返す口(実装は ``continuation_logprobs`` を書く)。
  - `ChoiceForm`(クラス): 推論の形 1 つ(差し替えられる=R-125 が候補ごとに決める)。
  - `FreeTextBackend`(クラス): 自由記述を返す口(実装は ``generate`` を書く)。
  - `FreeTextScorer`(クラス): ``FreeTextBackend`` の自由記述を候補に当てる当て口(推論の形 Noul)。当たらない答え(破綻)は分布では「その他」に
  - `LogprobChoiceScorer`(クラス): ``ChoiceBackend`` と ``ChoiceForm`` を組んだ当て口(推論の形 Choice/Score)。
  - `TokenBoundaryError`(クラス): 候補の文字列を、文の後ろのトークンから字面どおりに切り出せない(結合・位置のずれ)=破綻に数える。
  - `kanji_number`(関数): 漢数字の 1〜99(一・十・二十三 など)→ 数。読めなければ None。
  - `match_free_text`(関数): 自由記述 → 候補の id(「その他」は ``OTHER_ID``)・当たらなければ ``None``(=破綻)。
  - `negative_forms`(関数): 肯定の動詞の語(辞書形)→ 否定の形(〜ない・〜ません・〜なかった・〜ませんでした・〜ず・〜て(い)ない)。
  - `normalize_text`(関数): NFKC(全角の数字と英字を半角に)+助数詞の前の漢数字を数に+数の後ろの「個」を「つ」に+空白を除く。
  - `slice_continuation`(関数): トークンの頭の文字位置 ``starts`` と logprob の列から、文字の範囲 [begin, end) に頭がある物を切り出す。
  - `softmax_dist`(関数): まとめた logprob → 確率(最大を引いてから exp・-inf は 0)。全部 -inf なら ``BackendError``。
  - `verb_forms`(関数): 動詞の語(辞書形か「〜ない」)→ 当たりの形の集合(五段と一段の両方の読みを足す=多めに作る)。
  - `wrap_prompt`(関数): 判断の文(DM4 の版)を口に渡す形に包む(答えの頭 ``cue`` はこの後ろに付ける)。
- import している内部モジュール: `shibuya.foundation.ports.decision`・`tools/instruments/dm_eval/__init__.py`・`tools/instruments/dm_eval/judge.py`・`tools/instruments/dm_eval/situations.py`
- 呼び手: `tools/instruments/dm_eval/backends/__init__.py`・`tools/instruments/dm_eval/backends/hf.py`・`tools/instruments/dm_eval/backends/vllm.py`・`tools/instruments/dm_eval/cli.py`
- 読む試験: `tests/tools/test_dm_eval.py`
- 決定の ID: 11-01・R-83・R-125

## [hf.py](../../../../../../../../tools/instruments/dm_eval/backends/hf.py)

dm_eval.backends.hf — transformers の causal LM の口(〔11-01 段 1 の 3〕・(a)・重みは取らない・import は遅延)。

- 公開の関数とクラス
  - `HFCausalChoiceScorer`(クラス): transformers の causal LM(手元の道筋の重み)の logprob と自由記述の口。
  - `continuation_logprobs_from_logits`(関数): 候補のトークンを当てる位置の logits の行(``rows[k]`` が ``targets[k]`` を当てる)→ トークンごとの logprob。
  - `log_softmax_rows`(関数): 行ごとの log-softmax(float64・最大を引いてから)。
- import している内部モジュール: `tools/instruments/dm_eval/__init__.py`・`tools/instruments/dm_eval/backends/base.py`
- 呼び手: `tools/instruments/dm_eval/backends/__init__.py`・`tools/instruments/dm_eval/cli.py`
- 読む試験: `tests/tools/test_dm_eval.py`
- 決定の ID: 11-01・R-125

## [vllm.py](../../../../../../../../tools/instruments/dm_eval/backends/vllm.py)

dm_eval.backends.vllm — vLLM の OpenAI 互換 ``/v1/completions`` の logprob の口(〔11-01 段 1 の 3〕・(b)=(G) 案)。

- 公開の関数とクラス
  - `VLLMLogprobScorer`(クラス): vLLM の艦隊(127.0.0.1)の logprob と自由記述の口。作るときは接続しない(呼ぶときだけ)。
  - `post_json`(関数): 127.0.0.1 の ``port`` へ JSON を POST して JSON を返す(key は文に書かない)。
- import している内部モジュール: `tools/instruments/dm_eval/__init__.py`・`tools/instruments/dm_eval/backends/base.py`
- 呼び手: `tools/instruments/dm_eval/backends/__init__.py`・`tools/instruments/dm_eval/cli.py`
- 読む試験: `tests/tools/test_dm_eval.py`
- 環境変数: 名前を読めない所 1 か所
- 決定の ID: 11-01・R-125
