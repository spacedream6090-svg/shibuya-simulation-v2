# tools/repo_guide

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 4 本・その他 0 本(このディレクトリの直下)

## [build.py](../../../../../../tools/repo_guide/build.py)

段 3 ファイルのカードを作る(11-05/§3-1 の 1)。標準ライブラリだけ。対象のコードは import も実行もしない。

- 公開の関数とクラス
  - `CodeCards`(クラス)
  - `apply_masks`(関数)
  - `build_all`(関数): 全部を書く。戻り値は伏せた語の数(ファイルごと)。
  - `check`(関数): (差のあるファイルの一覧)。無いカード・余計なカードも差に入れる。
  - `data_rows`(関数)
  - `docs_rows`(関数)
  - `first_heading`(関数)
  - `list_files`(関数): リポからの道筋の一覧(sort 済み・``/`` 区切り)。git があれば追跡+無視されない未追跡、無ければ歩く。
  - `list_untracked`(関数): 無視されない未追跡のファイル(``.git`` が無ければ空)。カードには載るが commit に入るとは限らないので知らせる。
  - `main`(関数)
  - `mask_patterns`(関数): 検出パターンを 2 つの検査の道具のソースから AST で読む(本道具に語を持たない)。
  - `masked`(関数)
- import している内部モジュール: `tools/repo_guide/guide_facts.py`・`tools/repo_guide/guide_permits.py`・`tools/repo_guide/guide_render.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- CLI の引数
  - `--check`: src・tests・tools のカードだけを作って比べる(違えば exit 1)
  - `--root`: リポの根(既定はこのファイルから 2 つ上・試験用)
- 決定の ID: 11-05/§3-1

## [guide_facts.py](../../../../../../tools/repo_guide/guide_facts.py)

ファイルごとの事実を AST と本文の文字列から集める(対象のコードは import も実行もしない)。

- 公開の関数とクラス
  - `DecisionRegexes`(クラス)
  - `FileFacts`(クラス)
  - `ImportRef`(クラス)
  - `ModuleIndex`(クラス): リポの中の Python のファイルの一覧から、import の先のファイルを解く。
  - `decision_ids`(関数)
  - `decision_regexes`(関数): 決定の一覧の接頭から正規表現を作る(``接頭/ID``・``接頭 §番号``・接頭だけ・接頭につながる ``#N``)。
  - `decision_sort_key`(関数): 並び: 指示書と回答 → R- → D- → 第 N。数は数の順(末尾の ``id_text`` は同じ重みの字の並びの決め手)。
  - `first_line`(関数)
  - `first_paragraph`(関数)
  - `join_lines`(関数): 折り返しを 1 行に戻す(どちらかの端が ASCII でなければ空白を入れない)。
  - `module_label`(関数): src の下は import の名前(``shibuya.engine.resolve``)、ほかはリポの道筋。
  - `normalized_text`(関数): UTF-8(BOM は外す)で読み、改行を LF にする。読めなければ ``UnicodeDecodeError``。
  - `read_python`(関数): Python のファイル 1 本の事実(構文が読めなければ ``error`` に理由だけを入れる)。
- 呼び手: `tools/repo_guide/build.py`・`tools/repo_guide/guide_permits.py`・`tools/repo_guide/guide_render.py`
- 決定の ID: 11-02r/§1・11-02r/§1 #7・R-116・R-116 §1-4 #46・第 170・第 275・第 275 #4・第 340

## [guide_permits.py](../../../../../../tools/repo_guide/guide_permits.py)

状態台帳の持ち主の行と系の書きの許可を、ソースの AST だけから読む(対象のコードは import も実行もしない)。

- 公開の関数とクラス
  - `Permits`(クラス)
  - `Row`(クラス)
  - `System`(クラス)
  - `Unread`(クラス): AST から値を決められない。
  - `module_constants`(関数): 頂上の代入のうち静的に決まるものだけ(順に。決まらない代入は飛ばす)。
  - `read_constant`(関数): 1 ファイルの頂上の定数を AST で読む(無ければ ``KeyError``)。
  - `read_permits`(関数)
  - `static_eval`(関数)
- import している内部モジュール: `tools/repo_guide/guide_facts.py`
- 呼び手: `tools/repo_guide/build.py`・`tools/repo_guide/guide_render.py`

## [guide_render.py](../../../../../../tools/repo_guide/guide_render.py)

事実の表からカードの Markdown を作る(並びは sort・時刻なし・絶対パスなし・行番号なし)。

- 公開の関数とクラス
  - `DirCard`(クラス)
  - `Edges`(クラス)
  - `build_dir_table`(関数)
  - `build_edges`(関数)
  - `card_path`(関数): ディレクトリのカードの道筋(リポから)。
  - `decision_natural`(関数)
  - `escape_links`(関数): 説明文の ``](`` を ``]\(`` にする(コードの囲みの中はそのまま)。
  - `human_size`(関数)
  - `ledger_lines_by_file`(関数): ファイル → カードに載せる台帳の行(持ち主ごとに鍵の順)。
  - `permit_lines_by_file`(関数)
  - `render_data_index`(関数): rows: (ディレクトリ, 大きさ)。大きさが ``None`` はリンクか読めなかったもの。
  - `render_dir_card`(関数)
  - `render_docs_index`(関数): rows: ディレクトリ → (ファイルの数, [(.md の名前, 最初の見出し)])。
  - `render_readme`(関数)
- import している内部モジュール: `tools/repo_guide/guide_facts.py`・`tools/repo_guide/guide_permits.py`
- 呼び手: `tools/repo_guide/build.py`
- 決定の ID: 10-12・10-13b・10-25/§2-5・11-01/A1-2・11-02r/§1・11-02r/§1 #7・11-05/§3-1・R-116・R-116 §1-4 #46・R-126・D-74・第 170・第 275・第 275 #4・第 340
