# tools/ci

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 1 本・その他 0 本(このディレクトリの直下)

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
