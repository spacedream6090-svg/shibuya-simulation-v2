# tools/instruments/dm_eval/scenes

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 6 本(このディレクトリの直下)

その他のファイル: `appeal_v1.b0.json`・`appeal_v1.jsonl`・`appeal_v1.md5`・`consumption_v1.b0.json`・`consumption_v1.jsonl`・`consumption_v1.md5`

## [make_appeal_v1.py](../../../../../../../../tools/instruments/dm_eval/scenes/make_appeal_v1.py)

呼びかけの場面 v1 を作る(再現用・第 347・返事その 8 §6-2・記録 2-61 ①・2-62)。**正は同梱の jsonl と md5**で、このスクリプトはそれを作り直す道具。

- 公開の関数とクラス
  - `C`(関数)
  - `band`(関数)
  - `build_rows`(関数): 場面の行(並びは 種類 → 場面 → ない版が先)。
  - `main`(関数)
  - `pro_cands`(関数)
  - `render_files`(関数): 書き出す 3 本の名 → バイト(LF・UTF-8・鍵の順は固定)。
  - `req_cands`(関数)
  - `req_text`(関数)
  - `row`(関数)
  - `scene_text`(関数): 観測の文(B1〜B4b → B6)。``sign`` は B2 看板の行・``speech`` は B6 の末尾に足す発話の行(無ければ None)。
  - `sign_line`(関数)
  - `speech_line`(関数)
- 読む試験(道筋で): `tests/tools/test_dm_eval.py`
- CLI の引数
  - `sys.argv` を直接読む
- 決定の ID: R-149・第 347

## [make_consumption_v1.py](../../../../../../../../tools/instruments/dm_eval/scenes/make_consumption_v1.py)

消費の場面 v1 を作る(再現用・〔11-01 段 1 の 3〕)。**正は同梱の jsonl と md5**で、このスクリプトはそれを作り直す道具。

- 公開の関数とクラス
  - `C`(関数)
  - `add`(関数)
  - `b6`(関数)
  - `band`(関数)
  - `build_rows`(関数): 場面の行(並びは判断点の順 → 番号の順)。
  - `buy_cands`(関数)
  - `common`(関数)
  - `main`(関数)
  - `price_cands`(関数)
  - `qty_cands`(関数)
  - `render_files`(関数): 書き出す 3 本の名 → バイト(LF・UTF-8・鍵の順は固定)。
  - `revisit_cands`(関数)
- 読む試験(道筋で): `tests/tools/test_dm_eval.py`
- CLI の引数
  - `sys.argv` を直接読む
- 決定の ID: 11-01
