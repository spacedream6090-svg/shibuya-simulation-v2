# tools/pkgmove

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 16 本・その他 4 本(このディレクトリの直下)

その他のファイル: `README.md`・`allow_tests_tools.toml`・`contracts.toml`・`map.toml`

## [__init__.py](../../../../../../tools/pkgmove/__init__.py)

pkgmove — コードの区分の移動の道具(移す段 3・返事その 7 §4-2・計画 docs/reference/package-map-final-2026-11-09.md §7-4)。

## [allow.py](../../../../../../tools/pkgmove/allow.py)

許可の一覧: 道具が文字列を書き換えてよい (ファイル, 記号)。ここに無い文字列の定数は 1 つも書き換えない。

- 公開の関数とクラス
  - `Site`(クラス): 許可の一覧の 1 行(リポの根からの道筋・記号・規則)。
  - `load_tests_tools`(関数)
  - `render_tests_tools`(関数)
  - `scan_record_tools`(関数): tests の Python(``files`` の ``tests/`` の下)が道で読む docs の ``.py``: 道 → 読む試験。拾う形は ``/`` の結合
  - `src_sites`(関数): (b-src) の行を、今の木の置き場で(``locate``=今の道 → 木の道筋。移した後の木でも引ける)。
- import している内部モジュール: `tools/pkgmove/table.py`
- 呼び手: `tools/pkgmove/cli.py`・`tools/pkgmove/move.py`・`tools/pkgmove/split.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [classids.py](../../../../../../tools/pkgmove/classids.py)

固定の表 ``class_ids.py`` の鍵の書き換え(許可の一覧の (c))と鍵の守り。

- 公開の関数とクラス
  - `ClassIdError`(クラス): 鍵の守りが止めた。
  - `ClassIdResult`(クラス)
  - `check_keys`(関数): 鍵の守り: 全行で、新しい鍵が対応表で古い鍵に戻り、値が古い鍵の値と同じ。
  - `check_split_keys`(関数): 〔割る段 5a〕鍵の守り(クラスの単位): 写像は 1 対 1・行の数と値の多重集合が同じ・全行で新しい鍵が逆写像で古い鍵に戻り、値が
  - `find_table`(関数)
  - `new_table`(関数): 鍵だけを書き換えた表(値はそのまま)。
  - `rewrite`(関数): ``class_ids.py`` の文字列の鍵を書き換えた文字列と結果(鍵の守りを通らなければ :class:`ClassIdError`)。
  - `split_keymap`(関数): 〔割る段 5a〕割るモジュール ``src_mod`` のクラス(``__qualname__``)→ 新しい鍵の写像。割り先は頂上の名(``__qualname__``
  - `split_table`(関数): 〔割る段 5a〕鍵だけを ``keymap``(古い鍵 → 新しい鍵)で書き換えた表(値はそのまま)。
  - `table_of`(関数)
- import している内部モジュール: `tools/pkgmove/model.py`
- 呼び手: `tools/pkgmove/guard.py`・`tools/pkgmove/ledgerpaths.py`・`tools/pkgmove/move.py`・`tools/pkgmove/split.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [cli.py](../../../../../../tools/pkgmove/cli.py)

移す段 3 の道具の入口。使い方は ``tools/pkgmove/README.md``。

- 公開の関数とクラス
  - `cmd_allow`(関数)
  - `cmd_contracts`(関数): 段の木の import の決まり(親の決定=brief_contracts)。--apply は木の pyproject の節だけを書き換える。
  - `cmd_importcheck`(関数)
  - `cmd_map`(関数)
  - `cmd_move`(関数)
  - `cmd_split`(関数): 〔割る段 5a〕割る行を当てる(``split.py``)。
  - `is_main_worktree`(関数): ``path`` が git の本体の作業木(か、その中)なら ``True``=書かない。
  - `main`(関数)
  - `scan_allow`(関数): tests と tools の走査: 段 4 の全段(保留を除く)で道の文字列の書き換えが起きる (ファイル, 記号)。
- import している内部モジュール: `tools/pkgmove/allow.py`・`tools/pkgmove/contracts.py`・`tools/pkgmove/guard.py`・`tools/pkgmove/importcheck.py`・`tools/pkgmove/model.py`・`tools/pkgmove/move.py`・`tools/pkgmove/split.py`・`tools/pkgmove/strings.py`・`tools/pkgmove/table.py`
- 読む試験: `tests/tools/test_pkgmove.py`
- CLI の引数
  - サブコマンド `allow`
  - サブコマンド `contracts`
  - サブコマンド `importcheck`
  - サブコマンド `map`
  - サブコマンド `move`
  - サブコマンド `split`
  - `--apply`: 木の pyproject の節を書き換える(本体の作業木は断る)
  - `--check`: 木の pyproject の節が作り直しと同じかを見る(違えば 1)
  - `--import-jobs`
  - `--jobs`
  - `--next`: 木の次の割る行(順の次の 1 本)
  - `--only`: 割る行を今の道(表の old)で名指す(順が違えば断る)
  - `--out`: 報告の JSON を書く道(木の外)。書くときは効いている例外の数も回す
  - `--out-dir`: 報告の JSON と差分を書く置き場(木の外)
  - `--probe`: 効いている例外の数を回す(--out が無くても)
  - `--stage`: 段の名(contracts.toml の stage_order)
  - `--through`: 書かない実行だけ: 次の本から、この行(か all)まで順にメモリの中で当てる
  - `--tree`: 段を当てた木の根
- 環境変数: `os.environ` をまるごと使う

## [contracts.py](../../../../../../tools/pkgmove/contracts.py)

段ごとの import の決まり(pyproject の ``[tool.importlinter]`` の節)を、元のファイル ``contracts.toml`` と木の今の形から作る(親の決定=brief_contracts・2026-11-11・仮採用)。

- 公開の関数とクラス
  - `ContractsError`(クラス): 木の形が段と合わない・pyproject の節の形が読めない。
  - `Spec`(クラス)
  - `TreeView`(クラス): 木の今の形: モジュールの集合・今の名 → 最終の名・ほかの置き場から入ったファイル(古い名, 新しい名)。
  - `build`(関数): (契約の一覧=pyproject の [[tool.importlinter.contracts]] の形, 報告)。
  - `check_stage`(関数): 木の当たっている行が「段の順で ``stage`` まで」と同じか(保留の行を除く)。
  - `effective_ignores`(関数): 〔検収 中-1〕効いている例外の数: 例外の行を 1 本ずつ外すと、その契約が broken になる行(延べ)と、どれかの契約で効く辺
  - `has_edge`(関数): 木で ``importer`` が ``imported`` を読む import の文が在るか(関数の中を含む・相対も解く)。
  - `ignore_counts`(関数): 例外(ignore)の数(返事その 8 §1-12 の 3): 延べの行・重なりを除いた辺・重なりを除いた辺の「消える段」ごとの数。
  - `load_spec`(関数)
  - `old_contracts`(関数): 今の 5 つの決まり(移す前と old_only_through の段まで)の契約。
  - `render`(関数)
  - `same_section`(関数): 節の中身(名・型・名の並び)が同じか(書き方の違いは見ない)。
  - `section_dict`(関数)
  - `split_pyproject`(関数): (節の前, 節)。節は「# ---- 層契約」の行(無ければ ``[tool.importlinter]`` の行)から終わりまで。後ろに別の表があれば断る。
  - `stage_of`(関数): 木の段: どの段の行も当たっていなければ ``""``・段の順で ``S`` までが当たっていれば ``S``・どちらでもなければ ``None``。
  - `uncovered`(関数): どの契約の元の側(層の名・``source_modules``)にも入らないランの側のモジュール(頭・根・build を除く)。そのモジュールから
  - `view`(関数)
  - `weakened`(関数): 〔割る段 5a・検収 高-1・再検収 低-1〕割る行 ``split_old`` を当てる前と後の報告(:func:`build` の 2 つ目)を比べ、決まりが
- import している内部モジュール: `tools/pkgmove/model.py`・`tools/pkgmove/move.py`・`tools/pkgmove/split.py`・`tools/pkgmove/table.py`
- 呼び手: `tools/pkgmove/cli.py`・`tools/pkgmove/split.py`
- 読む試験: `tests/tools/test_pkgmove.py`
- 環境変数: `os.environ` をまるごと使う

## [guard.py](../../../../../../tools/pkgmove/guard.py)

凍結の値の守りと、許可の一覧の外が変わらないことの確かめ(書き換えた後の木で。1 つでも当たれば書かずに止める)。

- 公開の関数とクラス
  - `Frozen`(クラス): 凍結の値(2 本の JSON)。
  - `GuardReport`(クラス)
  - `bound_names`(関数): ファイルの import の文が結ぶ名の多重集合(``import a.b`` は ``a``・別名があれば別名・関数の中の import を含む)。
  - `check_bound_names`(関数): 書き換えの前後で、各ファイルの import の文が結ぶ名(別名を含む)の多重集合が同じ(検収 m14)。頭から除いた再輸出の
  - `check_class_ids`(関数): 固定の表の値と宣言 → 凍結の写像・表の鍵と宣言 = src の全部のクラス(build を除く)。
  - `check_head_all`(関数): 空にしない頭(中身のある ``src/shibuya/**/__init__.py``)の ``__all__`` の名が、全部その頭で結ばれている
  - `check_names`(関数)
  - `check_outside`(関数): 許可の一覧の外の定数がファイルごとに同じ・許可の一覧の中でも凍結の値の字面の出てくる数は同じ
  - `collect_names`(関数): ``names_frozen.json`` の静的な欄を木から集める(道の形の領域の名は凍結の鍵ごとの数)。
  - `const_table`(関数): (記号, docstring か, 値) の多重集合(docstring を含む全部の文字列とバイト列の定数)。
  - `head_all_names`(関数): 頭の頂上の ``__all__ = [...]`` の名(文字列の要素)。``__all__`` が無ければ ``None``。
  - `id_pattern`(関数)
  - `shaped_counts`(関数): 74 種がランの側の src の文字列の定数に出てくる数。数えないのは、固定の表の鍵と、値の全体が移すファイルの道そのもの
- import している内部モジュール: `tools/pkgmove/classids.py`・`tools/pkgmove/imports.py`・`tools/pkgmove/model.py`
- 呼び手: `tools/pkgmove/cli.py`・`tools/pkgmove/move.py`・`tools/pkgmove/split.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [ignoreprobe.py](../../../../../../tools/pkgmove/ignoreprobe.py)

効いている例外(ignore)の確かめ(検収 中-1・親の裁定 2026-11-16)。木を変えずに、メモリの中で回す。

- 公開の関数とクラス
  - `main`(関数)
  - `probe`(関数)
- CLI の引数
  - `sys.argv` を直接読む

## [importcheck.py](../../../../../../tools/pkgmove/importcheck.py)

木の ``src/shibuya`` の全モジュールを、1 本ずつ最初から import できるかの確かめ(検収 M-1・親の裁定)。

- 公開の関数とクラス
  - `check`(関数): 結果: ``n``(モジュールの数)・``bad``(名 → 誤り)・``cli_help_exit``(cli が無ければ ``None``)・``cli_help_err``・
  - `modules`(関数)
  - `ok`(関数)
  - `summary`(関数)
- 呼び手: `tools/pkgmove/cli.py`
- 読む試験: `tests/tools/test_pkgmove.py`
- 環境変数: `os.environ` をまるごと使う

## [imports.py](../../../../../../tools/pkgmove/imports.py)

import の文の書き換え(許可の一覧の (a))。

- 公開の関数とクラス
  - `ImportStats`(クラス)
  - `Target`(クラス): 書き換えた後の 1 つの名(モジュール・名・別名)。
  - `alias_dests`(関数): 〔割る段 5a〕ファイル(かコードの文字列)で割るモジュールを結んだ別名 → 割り先のモジュール(``X.名``・``setattr(X, "名")``
  - `all_drops`(関数): 〔親の裁定 review3 の 2〕頭から除いた再輸出の名を、その頭の ``__all__`` からも除く(頭が自己整合であること)。
  - `head_all_node`(関数): 頂上の ``__all__ = [...]``(か ``(...)``)の値。無ければ ``None``。
  - `head_drops`(関数): この段で空にしない包みの頭の再輸出のうち、出どころのモジュールが包みの外へ移るものの import の文を除く
  - `plan_from`(関数): ``from … import`` の書き換えの計画(変わらなければ ``None``)・頭を通したか・注意(子のモジュールを読んだ印は
  - `plan_import`(関数): ``import …`` の書き換え(別名の名ごとに新しい名)。
  - `render_from`(関数): 行き先ごとの ``from … import`` の文(1 つ目は元の位置から始まる=頭の空白を含まない)。
  - `rewrite_code`(関数): 文字列の中の Python のコード(子のプロセスに渡す文など)の import の文の書き換え: (元の文, 新しい文) の並び。
  - `rewrite_file`(関数): 1 本のファイルの import の文の書き換え。
- import している内部モジュール: `tools/pkgmove/model.py`
- 呼び手: `tools/pkgmove/guard.py`・`tools/pkgmove/move.py`・`tools/pkgmove/split.py`・`tools/pkgmove/strings.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [ledgerpaths.py](../../../../../../tools/pkgmove/ledgerpaths.py)

(d) つなぎの台帳の道の対応の表 ``engine/bridging/ledger_paths.py`` の ``LEDGER_PATHS`` を書き足す(親の決定 1=案 (b))。

- 公開の関数とクラス
  - `LedgerPathsError`(クラス): 表の守りが止めた。
  - `check`(関数): 表の今の道は木にある・台帳の道が重ならない・台帳のコードの行の道は表を通して木にある。
  - `rewrite`(関数): 表の字面を書き換えた文字列と、足した行の数。
  - `table_of`(関数)
  - `updated`(関数): ``moves``(古い今の道 → 新しい今の道)を当てた表。
- import している内部モジュール: `tools/pkgmove/classids.py`・`tools/pkgmove/model.py`
- 呼び手: `tools/pkgmove/move.py`・`tools/pkgmove/split.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [model.py](../../../../../../tools/pkgmove/model.py)

木(ファイルの中身を手元に持つ)とモジュールの索引・頭の再輸出の引き先。

- 公開の関数とクラス
  - `Ctx`(クラス): 選んだ段の書き換えの材料(木は移す前のもの)。
  - `Edit`(クラス): 1 か所の書き換え(文字列の位置 ``start``〜``end`` を ``new`` に)。``kind``: ``import``・``path``・``class_key``。
  - `Index`(クラス): 木の src のモジュールの索引(名 → 道筋)と、頭の再輸出の引き先。
  - `ModInfo`(クラス): モジュールの頂上の名: 定義した名と、import で結んだ名(名 → (モジュール, 元の名))。
  - `Text`(クラス): 1 本のファイルの文字列と、行と位置の換算。
  - `Tree`(クラス): 木の中身。``files`` は Python(文字列)、``blobs`` は src の中のほかのファイル(バイト列)。
  - `apply_edits`(関数): 重ならない書き換えを当てる(重なれば止める)。
  - `area_of`(関数): 木の道筋の区分(``src``・``build``・``tests``・``tools``・``docs``・``other``)。
  - `docstring_ids`(関数): docstring の定数(``id``)。
  - `docstrings_of`(関数): :func:`docstring_ids` の覚え書き(:func:`parse` の木に対して)。
  - `is_self`(関数)
  - `mod_of`(関数): ``src/shibuya`` からの道筋 → モジュールの名(``core/rng.py`` → ``shibuya.core.rng``・頭は包みの名)。
  - `parse`(関数): ``ast.parse`` の覚え書き(同じ文字列は同じ木=木は書き換えない約束で使う)。
  - `rel_of_mod`(関数): モジュールの名 → ``src/shibuya`` からの道筋。
  - `resolve_from`(関数): ``from … import`` のモジュールの名(相対は ``pkg`` から解く)。
  - `symbol_map`(関数): 木の中の各ノード(``id``)→ 記号の名。頂上の関数とクラスはその名(メソッドは ``クラス.メソッド``・関数の中の
  - `symbols_of`(関数): :func:`symbol_map` の覚え書き(:func:`parse` の木に対して)。
- 呼び手: `tools/pkgmove/classids.py`・`tools/pkgmove/cli.py`・`tools/pkgmove/contracts.py`・`tools/pkgmove/guard.py`・`tools/pkgmove/imports.py`・`tools/pkgmove/ledgerpaths.py`・`tools/pkgmove/move.py`・`tools/pkgmove/pkgdata.py`・`tools/pkgmove/split.py`・`tools/pkgmove/strings.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [move.py](../../../../../../tools/pkgmove/move.py)

段を選んで計画を作り(書き換えた後の木を手元で作る)、守りを通し、報告と差分を出す。``--apply`` のときだけ木へ書く。

- 公開の関数とクラス
  - `Plan`(クラス)
  - `Refused`(クラス): 断った(保留の行の名指し・道具の使い方)。終了コード 2。
  - `Stopped`(クラス): 守りが止めた(書かない)。終了コード 1。
  - `apply`(関数): 書き換えた後の木を ``root`` へ書く(書く・移す・消すのは計画にあるファイルだけ)。終わりに、``src/shibuya`` の下の
  - `check_order`(関数): 〔検収 中-2〕当てる行の段が、木の段の次の段(行のある段で数える)から順に並ぶか。違えば :class:`Refused`(終了コード 2)。
  - `gone_packages`(関数): 対応表の頭の行(古い ``__init__.py``)のうち、木に頭がもう無い包みの名(移して無くなった包み)。import の確かめが、
  - `ledger_rows`(関数): つなぎの台帳の ``declared_in``(``src/shibuya/…``)のうち、移すファイルを指す行(書き換えない=報告だけ)。
  - `locate`(関数): 今の道(``src/shibuya`` からの相対)のファイルの、木の中の道筋(移した後なら新しい道)。
  - `make_ctx`(関数): 書き換えの材料と、移すファイルの道(``src/shibuya`` からの相対の古い → 新しい)。
  - `make_plan`(関数): 計画(書き換えた後の木)を作り、守りを通す(当たれば :class:`Stopped`)。``extra_sites``・``keyfn`` は試験の口。
  - `prune_cache_only_dirs`(関数): 〔検収 L-a〕``root/src/shibuya`` の下で、``__pycache__`` のほかに何も無いディレクトリ(移した後の古い包みの残り)を
  - `report`(関数)
  - `select_rows`(関数): (当てる候補の行, 保留で断る行)。``only`` で保留の行を名指せば :class:`Refused`。
  - `tree_stage`(関数): 木の段(``contracts.stage_of`` と同じ見分けを段の順 :data:`STAGES` で): どの段の行も当たっていなければ ``""``・段の順で
  - `unified_diff`(関数)
- import している内部モジュール: `tools/pkgmove/allow.py`・`tools/pkgmove/classids.py`・`tools/pkgmove/guard.py`・`tools/pkgmove/imports.py`・`tools/pkgmove/ledgerpaths.py`・`tools/pkgmove/model.py`・`tools/pkgmove/pkgdata.py`・`tools/pkgmove/strings.py`・`tools/pkgmove/table.py`
- 呼び手: `tools/pkgmove/cli.py`・`tools/pkgmove/contracts.py`・`tools/pkgmove/split.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [pkgdata.py](../../../../../../tools/pkgmove/pkgdata.py)

pyproject の ``[tool.setuptools.package-data]`` の鍵(親の裁定 2026-11-11・判断 2=許可の一覧の (f))。

- 公開の関数とクラス
  - `check`(関数): 鍵は全部、木に在る包みで、glob が 1 本以上に当たる。
  - `entries`(関数)
  - `rewrite`(関数): (書き換えた文, 書き換えた鍵 (古い, 新しい), 注意)。書き換えるのは、この段で無くなる包みの鍵だけ。
- import している内部モジュール: `tools/pkgmove/model.py`
- 呼び手: `tools/pkgmove/move.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [split.py](../../../../../../tools/pkgmove/split.py)

割る段(段 5a〜)の道具: 割る行(``kind="split"``)を 1 本ずつ当てる(親の裁定 Q10=案 A)。

- 公開の関数とクラス
  - `SplitPlan`(クラス)
  - `SplitRefused`(クラス): 断った(表せない・順が違う・使い方)。終了コード 2。
  - `SplitStopped`(クラス): 守りが止めた(書かない)。終了コード 2(親の発注=守りが「同じ」でなければ当てない)。
  - `Unit`(クラス)
  - `apply`(関数): 計画の木を ``root`` へ書く(変わったファイルだけ・消すファイル)。``__pycache__`` だけのディレクトリを消す。
  - `compose`(関数): 割り先ごとの新しい字面(既に在る割り先は書き足した後の全文・元のファイルが主な割り先なら書き直した全文)。
  - `forwarder_problems`(関数): 〔割る段 5b・E2 の守り〕転送が決まった型か(字面が型と同じ・頂上で名を結ばない・import は ``if __name__ == "__main__":`` の
  - `free_names`(関数): 単位の中で結ばれない名(=割り先のモジュールの頂上で結ぶ要る名)と、文字列の注釈の中の名。``keep`` は組み込みの名でも
  - `guards`(関数)
  - `import_graph`(関数): src のモジュール → 読み込みの時に読むモジュール(``shibuya`` の中・親の包みの頭を含む)→ 読む文の場所(道:行 名)。
  - `is_done`(関数): 割る行が当たっているか: どの名も割り先のファイルの頂上に在り、元のファイルは無いか 0 バイトの頭(主な割り先へ移ったもの
  - `is_forwarder`(関数): 〔割る段 5b・E2〕元のファイルが入口の転送(:data:`pkgmove.table.SPLIT_FORWARDERS` の行で、中身が決まった型そのもの)か。
  - `is_split_excluded`(関数)
  - `make_split_plan`(関数): 割る行 ``old`` を当てた後の木と報告(守りを通らなければ :class:`SplitStopped`・表せなければ :class:`SplitRefused`)。
  - `names_used`(関数): 文が読む名(読み・注釈の名・文字列の注釈の中の名。結ぶ名は含めない)。局所の名も含む(多めに数える)。
  - `new_import_cycles`(関数): 〔G2 の 5 本目の欠陥〕割った後の木で、読み込みの時の import が作る循環のうち、割る前に無かったもの(循環の中の新しい辺と
  - `next_split`(関数)
  - `report`(関数)
  - `source_rel`(関数): 割る行の元のファイルの今の道(``src/shibuya`` からの相対)。段 4 で主な割り先へ移ったもの(18 本目)は主な割り先。
  - `split_state`(関数): 済んだ割る行(順の頭から)。順の途中が抜けていれば ``None``(段を飛ばした木)。
  - `template_docstring`(関数): 2 つ目以降の新しい割り先の docstring(決まった型。凍結の値・expedient の見出しを書かない)。
  - `top_names`(関数): ファイルの頂上で結ぶ名(関数・クラス・代入の左辺。``__all__`` を除く)。
  - `unbound_names`(関数): 頂上・関数・クラスの中で読むのに、どこでも結ばれない名(組み込みを除く。``keep`` の名は組み込みでも数える)。比べるための
  - `unified_diff`(関数)
  - `units_of`(関数): 頂上の文の単位(前の注と空行を付ける)。表せない形は :class:`SplitRefused`。
- import している内部モジュール: `shibuya.validation.static.bridging_scan`・`tools/pkgmove/allow.py`・`tools/pkgmove/classids.py`・`tools/pkgmove/contracts.py`・`tools/pkgmove/guard.py`・`tools/pkgmove/imports.py`・`tools/pkgmove/ledgerpaths.py`・`tools/pkgmove/model.py`・`tools/pkgmove/move.py`・`tools/pkgmove/strings.py`・`tools/pkgmove/table.py`
- 呼び手: `tools/pkgmove/cli.py`・`tools/pkgmove/contracts.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [strings.py](../../../../../../tools/pkgmove/strings.py)

道の文字列の書き換え(許可の一覧の (b))と、触らなかった道の形の文字列の拾い。

- 公開の関数とクラス
  - `PathRules`(クラス): 移すファイルの道(``src/shibuya`` からの相対)。
  - `StrStats`(クラス)
  - `chain_edits`(関数): ``X / "engine" / "clock.py"`` の連なりのうち、道が 2 つ以上の定数にまたがるもの。
  - `code_import_hits`(関数): 〔割る段 5b の G0 の直し 高-2〕文字列の中のコードが割るモジュール(``Ctx.namemap``)を読む import(``from <包み> import
  - `dotted_new`(関数): 点の道の書き換え(変わらなければそのまま)。
  - `is_table_key`(関数): 〔割る段 5b の G0 の直し 高-1〕文字列 ``n`` が :data:`TABLE_KEY_CALLS` の呼び出しの第 1 引数(か ``old=``)か。
  - `literal_source`(関数): 字面へ書き換えを同じ順に当てた新しい字面(値が合わなければ ``None``)。
  - `rewrite_file_strings`(関数): 1 本のファイルの許可の一覧の記号の中の文字列の書き換え。``rule_of``: 記号 → 規則(``exact``・``paths``)。
  - `rewrite_value`(関数): 文字列の値の書き換え(``paths`` の規則): 新しい値・書き換え(値の位置)・触らなかったもの(種類・字面・理由)。
  - `sibling_dest`(関数): 〔割る段 5a〕全体が割るファイルの道 ``rel`` の文字列 ``n`` の、同じ組の中の頂上の名が指す割り先(無ければ ``None``)。
  - `split_nameless`(関数): 〔割る段 5b・E2・E3〕割るモジュールの名の無い点の道 ``tok`` の行き先: (新しい字面か ``None``, 触らなかった印か ``None``)。
  - `untouched_in_file`(関数): 許可の一覧の外の文字列の定数のうち、移すモジュールの道の形を含むもの(ファイル・記号・種類・字面)と、
- import している内部モジュール: `tools/pkgmove/imports.py`・`tools/pkgmove/model.py`
- 呼び手: `tools/pkgmove/cli.py`・`tools/pkgmove/move.py`・`tools/pkgmove/split.py`
- 読む試験: `tests/tools/test_pkgmove.py`

## [table.py](../../../../../../tools/pkgmove/table.py)

全ファイルの表を読み、対応表 TOML(今の道 → 新しい道)を書く・読む。保留の一覧はここだけに置く。

- 公開の関数とクラス
  - `MapDoc`(クラス): 対応表 TOML の中身。
  - `Row`(クラス): 表の 1 行(道筋は ``src/shibuya`` からの相対・``/`` 区切り)。
  - `build_map_text`(関数)
  - `forwarder_text`(関数): 〔割る段 5b・E2・親の裁定 Q6 の (a)〕入口の転送の決まった型(:data:`SPLIT_FORWARDERS`)。頂上で名を結ばない(``import shibuya.cli``
  - `load_map`(関数): 対応表 TOML を読む(保留の一覧が道具の一覧と同じかも確かめる)。
  - `parse_split_tables`(関数): §4 の節 → 今の道 → (名と割り先の並び, 名が揃っているか, 宣言した書き換え)。名が 2 つの割り先に載れば ``ValueError``。
  - `parse_table`(関数): 表の §3 の行を読む(行の数と道筋の重なりを確かめる)。割る行には §4 の名の表を付ける。
  - `render_map`(関数): 対応表 TOML の文(行の順は表の順)。割る行の名の表は ``[row.names]``(名 → 割り先)・宣言した書き換えは
  - `sha256_text`(関数)
- 呼び手: `tools/pkgmove/allow.py`・`tools/pkgmove/cli.py`・`tools/pkgmove/contracts.py`・`tools/pkgmove/move.py`・`tools/pkgmove/split.py`
- 読む試験: `tests/tools/test_pkgmove.py`
- 決定の ID: 11-16・第 347
