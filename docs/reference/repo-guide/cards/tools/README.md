# tools

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [bench](bench/README.md)・[bench_spikes](bench_spikes/README.md)・[build_geo](build_geo/README.md)・[bytecheck](bytecheck/README.md)・[c6](c6/README.md)・[c7](c7/README.md)・[c8](c8/README.md)・[fig](fig/README.md)・[gen](gen/README.md)・[hunger](hunger/README.md)・[instruments](instruments/README.md)・[ledger](ledger/README.md)・[night5070](night5070/README.md)・[pkgmove](pkgmove/README.md)・[quality_probe_v0](quality_probe_v0/README.md)・[realworld_fetch](realworld_fetch/README.md)・[repo_guide](repo_guide/README.md)・[research](research/README.md)・[spatial](spatial/README.md)・[vocab](vocab/README.md)・[w17](w17/README.md)・[world_data](world_data/README.md)

## [commit_check.py](../../../../../tools/commit_check.py)

commit の前の確認: 「入れるはずのファイル」の一覧とステージの中身を突き合わせる(第330・CLAUDE.md §7)。

- 公開の関数とクラス
  - `compare`(関数): (足りない=一覧にあるがステージに無い, 余計=ステージにあるが一覧に無い, 一覧の重複)
  - `main`(関数)
  - `normalize_lines`(関数): CRLF/LF/CR・BOM・前後の空白を正規化。``#`` で始まる行と空行は無視。
  - `path_check`(関数): ステージした追加/変更ファイルの中身に記録してはいけない道筋があれば ``path:行:中身`` を返す。
  - `read_expect`(関数)
  - `staged_paths`(関数): ステージの全部(追加・変更・削除・改名の両側)。NUL 区切りで読み、空白入りでも分裂しない。
- 読む試験(道筋で): `tests/tools/test_commit_check.py`・`tests/tools/test_repo_guide.py`
- CLI の引数
  - `--expect`: 入れるはずのファイルの一覧(1 行 1 パス・改行は何でもよい)
  - `--expect-paths`: 一覧を引数で渡す
  - `--list`: ステージの一覧を LF で標準出力に出す
  - `--no-path-check`: 道筋の検査を省く
  - `--paths-only`: 道筋の検査だけ
- 環境変数: `COMMIT_EXPECT`
- 決定の ID: 第 329・第 330

## [decision_index.py](../../../../../tools/decision_index.py)

決定の ID の索引を自動生成する(回答 10-13b §1 1-7 案 B・CLAUDE.md §6)。

- 公開の関数とクラス
  - `main`(関数)
  - `render`(関数)
  - `scan`(関数): 戻り値 = (見出し [(行, 番号, 文), …], ID [(ID, 行, 文の先頭), …])。
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- CLI の引数
  - `--check`: 生成物が最新かを確かめるだけ(違えば exit 1)
- 決定の ID: 09-24d・09-25・09-29d・09-30・10-03・10-06・10-12・10-12/CA1・10-12b・10-12p・10-12p/2-0・10-13・10-13b・10-13b/§0-2・10-13b/§1・10-25・11-01・11-01g・11-01p・11-02・11-02r・11-03・11-04・11-04b・11-04c・11-05・11-09・R-129・R-149・R-150・第 330・第 332・第 338・第 340・第 344

## [scan_secrets.py](../../../../../tools/scan_secrets.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_repo_guide.py`・`tests/tools/test_scan_secrets_cp932.py`
- CLI の引数
  - `sys.argv` を直接読む
- 決定の ID: 第 202・第 333
