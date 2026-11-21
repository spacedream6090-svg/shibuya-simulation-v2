# tools/hunger

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 2 本・その他 0 本(このディレクトリの直下)

## [build_activity_prior.py](../../../../../../tools/hunger/build_activity_prior.py)

活動選択の事前分布(D-119 L2・5 段目 5b)の錨を **追跡ファイル**へ書き出す(決定論)。

- 公開の関数とクラス
  - `build`(関数)
  - `dumps`(関数)
  - `main`(関数)
  - `read_table`(関数)
- CLI の引数
  - `--check`: 追跡ファイルと一致するかだけ見る
- 決定の ID: D-119

## [build_hunger_anchors.py](../../../../../../tools/hunger/build_hunger_anchors.py)

空腹のエネルギー収支(D-118・5 段目 5a)の錨を **追跡ファイル**へ書き出す(決定論)。

- 公開の関数とクラス
  - `build`(関数)
  - `dumps`(関数)
  - `main`(関数)
  - `split_doc`(関数): 〔第 2 期 2-4 V6〕錨の辞書 → (構築側, 検証側)。表と ``sources`` の鍵の名で分ける(値は同じ・順は元のまま)。
- CLI の引数
  - `--check`: 追跡ファイルと一致するかだけ見る
- 決定の ID: D-118・第 291
