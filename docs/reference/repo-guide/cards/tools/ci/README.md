# tools/ci

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 3 本・その他 1 本(このディレクトリの直下)

その他のファイル: `test_shards.json`

## [changed_scope.py](../../../../../../tools/ci/changed_scope.py)

変えたファイルの範囲から、どの試験を回すかを決める(11-22 §3-2 の 1・5)。標準ライブラリだけ(CI で依存を入れる前に回す)。

- 公開の関数とクラス
  - `affects_runs`(関数)
  - `changed_paths`(関数): ``git diff --name-only base head``。失敗・基準なしは None(=分からない)。
  - `classify`(関数): 道筋の一覧 → 判定。空の一覧は「分からない」として重い側。
  - `heavy_groups`(関数): 重い組の名(``tools/ci/test_shards.json`` の ``weight`` が ``heavy`` の組)。文書だけの変更では回さない。
  - `is_document`(関数): 文書だけの変更に数えてよい 1 本か。
  - `main`(関数)
  - `runtime_docs`(関数): ランが実行時に開きうる追跡ファイル(``tools/bytecheck/tree.py`` の ``TRACKED_READS`` の鍵)。
- 読む試験(道筋で): `tests/tools/test_ci_changed_scope.py`
- CLI の引数
  - `--base`: 比べる基準の commit(PR の土台・push の前の頭)
  - `--github-output`: $GITHUB_OUTPUT に heavy・run_affecting・skip_groups(回さない組の名・空白区切り)を書く
  - `--head`
  - `--paths`: 道筋を直に渡す(git を使わない)
  - `--root`
- 環境変数: `GITHUB_OUTPUT`
- 決定の ID: 11-22/§3-2

## [check_lock.py](../../../../../../tools/ci/check_lock.py)

入っている版がロックのファイル(``requirements-lock.txt``)と同じかを確かめる(第348・返事その 9 §1 の 13)。

- 公開の関数とクラス
  - `Lock`(クラス)
  - `LockLine`(クラス)
  - `compare`(関数): ロックと入っている版を比べる。戻り値の ``missing``・``extra``・``differ`` のどれかが空でなければ違う。
  - `freeze_here`(関数): この python で ``pip freeze --exclude-editable`` を回した出力。
  - `head_checks`(関数): 頭の行の pip と Python の版が、入っている pip と動いている Python と同じか(頭の行が無いのも違いに数える)。
  - `main`(関数): 入口。``freeze_text``・``pip_version``・``python_version``・``env`` は試験の口(無ければ今の環境から取る)。
  - `marker_applies`(関数): 環境の印が今の環境(か ``env`` で上書きした環境)で真か。印が無ければ真。
  - `normalize`(関数): 配布の名を比べる形に(PEP 503: 小文字・``-_.`` の続きを ``-`` に)。
  - `parse_freeze`(関数): ``pip freeze`` の出力を読む(正規化した名 → 版)。``-e`` の行と注は飛ばす。``名 @ URL`` は版を ``@ URL`` とする。
  - `parse_lock`(関数): ロックの文を読む。``==`` でない行・同じ名の重なり・頭の行の重なりは ``ValueError``。
  - `pip_here`(関数)
  - `render`(関数): 人が読む行(違いがあれば 1 行ずつ)。
- 読む試験(道筋で): `tests/tools/test_ci_check_lock.py`
- CLI の引数
  - `--freeze`: pip freeze の出力のファイル(無ければこの python で回す)
  - `--lock`: ロックのファイル(既定はリポの根の requirements-lock.txt)
- 決定の ID: 第 348

## [check_test_shards.py](../../../../../../tools/ci/check_test_shards.py)

CI の ci-1 を同時に回す組の表(``tools/ci/test_shards.json``)の検査と、組の道筋の出力(第348・返事その 9 §1 の 31)。

- 公開の関数とクラス
  - `ci_matrix`(関数): ci.yml の ci-1 の matrix の組の名(無ければ ``ValueError``)。
  - `group_paths`(関数): 組の pytest に渡す道筋(``tests/<名>``・表の並び)。知らない組・空の組は ``KeyError``。
  - `heavy_groups`(関数): 重い組の名(表の並び)。文書だけの変更では回さない(``tools/ci/changed_scope.py`` が使う)。
  - `is_test_file`(関数)
  - `load_table`(関数): 組の表を読む(形が違えば ``ValueError``)。
  - `main`(関数)
  - `problems`(関数): 揃っていない所の文(空なら揃っている)。
  - `python_files`(関数): pytest が集めるファイルの名の型(``pyproject.toml`` の ``python_files``・無ければ既定)。
  - `top_entries`(関数): ``tests/`` の直下のディレクトリと試験のファイルの名(中には入らない)。
- 読む試験(道筋で): `tests/tools/test_ci_check_test_shards.py`
- CLI の引数
  - サブコマンド `check`
  - サブコマンド `paths`
  - `--group`
  - `--root`: リポの根(既定はこのファイルから 2 つ上・試験の口)
- 決定の ID: 11-22/§3-2・第 348・第 349
