# src/shibuya/build/lang

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 5 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../../src/shibuya/build/lang/__init__.py)

build.lang — 世界データ構築 W14/W15(静的言語化レーン)。

- 公開の関数とクラス
  - `stage_funcs`(関数): 段階名 → 段階関数(``run.STAGE_FUNCS`` の遅延取得)。
- import している内部モジュール: `shibuya.build.lang.run`
- 呼び手: `shibuya.build.lang.run`・`shibuya.build.run`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [common.py](../../../../../../../../src/shibuya/build/lang/common.py)

build.lang.common — W14/W15 が共有する純粋ヘルパ。

- 公開の関数とクラス
  - `IngestReport`(クラス): 応答取り込みの結果(ゲート json の中身)。
  - `Prompt`(クラス): 1 呼ぶんのプロンプト(``fleet_gen`` の入力行)。
  - `Verdict`(クラス): 1 プロンプトぶんの判定。
  - `Violation`(クラス): 検査の指摘 1 件。
  - `check_abbreviation`(関数): §2.4 ⑥ 省略記法の検査。
  - `check_banned_words`(関数): 評価語・誘導表現・命令文の検査(広告答申 §4・憲法6)。
  - `check_individual_words`(関数): §2.4 ⑧ 個体依存語の検査(B2 はセル共有ブロック=個体語を置けない)。
  - `gate_rows`(関数): 取り込み結果 → 段階ゲート行。
  - `iter_chunks`(関数): (補助)決定論的なチャンク分け。
  - `normalize_generated`(関数): 生成文 → (正規化文, 異常理由)。理由が空文字なら正常。
  - `prompts_sha256`(関数): プロンプト列の版ハッシュ(文面を変えたら値が変わる=改版の検出器)。
  - `read_prompts`(関数)
  - `read_responses`(関数): 応答 jsonl → ``(id, rep) → text``。
  - `scan_proper_nouns`(関数): 固有名詞・数字の捏造検査(D-W18 のゲート「固有名詞は入力(POI名)由来のみ」)。
  - `verify_one`(関数): 1 プロンプトぶんの応答を検証して凍結可否を決める。
  - `write_prompts`(関数): プロンプト jsonl を書く(``common.write_json`` と同じ記録を返す)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.perception.attention`・`shibuya.perception.channels`・`shibuya.perception.normalize`
- 呼び手: `shibuya.build.lang.w14_signage`・`shibuya.build.lang.w15_cell_static`
- 読む試験: `tests/build_lang/test_checker.py`・`tests/build_lang/test_w14_signage.py`・`tests/build_lang/test_w15_cell_static.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [run.py](../../../../../../../../src/shibuya/build/lang/run.py)

build.lang.run — 静的言語化レーン(W14/W15)の段階を W 番号順に実行する CLI。

- 公開の関数とクラス
  - `main`(関数)
  - `run_stages`(関数)
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.geo.run`・`shibuya.build.lang`・`shibuya.build.lang.w14_signage`・`shibuya.build.lang.w15_cell_static`
- 呼び手: `shibuya.build.lang`・`shibuya.build.run`
- 読む試験(道筋で): `tests/test_places_guard.py`
- CLI の引数
  - `--data`: 入力データ根(既定 data)
  - `--out`: 出力ディレクトリ(例 data/world/v2)
  - `--quiet`
  - `--stage`: 実行する段階

## [w14_signage.py](../../../../../../../../src/shibuya/build/lang/w14_signage.py)

W14 看板(a)文面(§1 W14・D-W18)。

- 公開の関数とクラス
  - `build_prompts`(関数): W6/W7 → POI ごとのプロンプト(決定論・行順は w6_poi の行順)。
  - `business_word`(関数): (cat, subcat) → 業種語。subcat が表にあればそちらを採る。
  - `format_opening_hours`(関数): W7 ``content``(7 日 × 区間の JSON)→ (営業時間の文, 定休日の文)。
  - `ingest`(関数): 応答 jsonl を読み、ゲートを掛けて凍結対象を決める(ファイルは書かない)。
  - `run`(関数): W14: プロンプトを書き、応答があれば凍結する(純関数)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.lang.common`・`shibuya.core.time_consts`
- 呼び手: `shibuya.build.lang.run`・`shibuya.build.lang.w15_cell_static`
- 読む試験: `tests/build_lang/test_w14_signage.py`・`tests/build_lang/test_w15_cell_static.py`
- 読む試験(道筋で): `tests/test_places_guard.py`

## [w15_cell_static.py](../../../../../../../../src/shibuya/build/lang/w15_cell_static.py)

W15 B2 セル静的文(§1 W15・D-W18)。

- 公開の関数とクラス
  - `build_prompts`(関数): W2/W6/W8/W11 → セルごとのプロンプト(決定論・行順は w2_cells の行順)。
  - `ingest`(関数): 応答 jsonl を読み、ゲートを掛けて凍結対象を決める(ファイルは書かない)。
  - `run`(関数): W15: プロンプトを書き、応答があれば凍結する(純関数)。
- import している内部モジュール: `shibuya.build.geo.common`・`shibuya.build.lang.common`・`shibuya.build.lang.w14_signage`
- 呼び手: `shibuya.build.lang.run`
- 読む試験: `tests/build_lang/test_w15_cell_static.py`・`tests/build_lang/test_wiring.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
