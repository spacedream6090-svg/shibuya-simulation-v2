# tools/pkgmove — コードの区分を移す道具(移す段 3)

全ファイルの表([package-map-final-2026-11-09-files.md](../../docs/reference/package-map-final-2026-11-09-files.md))から作った
対応表 `map.toml` に従って、ファイルを新しい置き場へ移す道具。発注は [返事その 7](../../docs/design/prompt-2026-11-09-reply7.md)
§4-2、計画は [最終の表と移す段の計画](../../docs/reference/package-map-final-2026-11-09.md) §7-4(段 3 の行)・§7-5。
記録は [docs/bench/analysis/pkgmove-346/README.md](../../docs/bench/analysis/pkgmove-346/README.md)。

> **既定は書かない。** `move` は差分と報告だけを出す(dry-run)。木に書くのは `--apply --tree <置き場>` のときだけで、
> 置き場が git の本体の作業木(か、その中)なら断る。段 4 で使う作業木は親が決める。
> **`--apply` は途中で失敗しても戻さない**(書いたファイルはそのまま)。当てる先は写しの木か、git で戻せる作業木に限る。
> 書いた後に、木の全モジュールを 1 本ずつ最初から import する確かめを必ず回す(落ちれば終了コード 3)。

## 使い方

リポの根(作業木の根)で、venv の python で:

```
python tools/pkgmove/cli.py map [--check]        # 全ファイルの表 → tools/pkgmove/map.toml(--check は書かずに比べる)
python tools/pkgmove/cli.py allow [--check]      # tests と tools の許可の一覧 → tools/pkgmove/allow_tests_tools.toml
python tools/pkgmove/cli.py move --stage foundation --out-dir <置き場>                      # 書かない(報告と差分)
python tools/pkgmove/cli.py move --stage all --out-dir <置き場>                             # 段 4 の全段をまとめて(書かない)
python tools/pkgmove/cli.py move --stage foundation --apply --tree <木> --out-dir <置き場>  # 書く(書いた後に import の確かめ)
python tools/pkgmove/cli.py importcheck --tree <木> [--out <JSON>]                         # import の確かめだけ
python tools/pkgmove/cli.py contracts --stage <段> --tree <木> [--check|--apply] [--out <JSON>] [--probe]  # 段の import の決まり(pyproject の節)
```

- `--stage`: 段 4 の小さな段の名(当てた順に `foundation`・`world`・`economy`・`act`・`mind`・`society`・`runtime`・
  `experiments`・`validation`・`society_contact`・`interim_bundles`・`foundation_224a`・`delete`=`table.STAGES`)をコンマでつなぐか
  `all`。`--only <今の道>` で行を名指せる(何回でも)。`society_contact`(連絡の器 4 本 → `society/contact/`)と `foundation_224a`
  (行 224a → `foundation/arms/removed.py`)は、11-16 の答えの後に済んだ段の包みへ移す行だけの段(`table.LATE_STAGES`)。済んだ段の
  名で当て直しても、その行は選ばない。
- **段の順**(検収 中-2): 当てる行の段は、木の今の段(`move.tree_stage`=`contracts.stage_of` と同じ見分け)の次の段から順で
  なければ断る(終了コード 2・「段の順が違う」)。段を飛ばす・逆の順・木の段が分からない木(飛ばして当てた木)は、書かない実行でも
  断る。済んだ段の名で当て直す計画(当てる行 0)は通す。次の段から順の 2 段以上をまとめて渡すのは通す(`--stage all` も)。
- `--tree`: 木の根(既定は道具のリポ)。対応表と許可の一覧は道具のリポのものを読み、凍結の JSON とつなぎの台帳は木のものを読む。
- `--out-dir`: `pkgmove_<段>_report.json`(報告)と `pkgmove_<段>.diff`(差分)、`--apply` なら `pkgmove_<段>_imports.json`
  (import の確かめ)を書く。木の外に置く。本体の作業木(か、その中)なら断る。
- 終了コード: **0**=できた(書かない実行では報告と差分だけ)・**1**=守りが止めた(書いていない)か `--check` の食い違い・
  **2**=断った(保留の行の名指し・本体の作業木への `--apply` か報告の置き場・`--apply` に `--tree` が無い・対応表の行き先の
  重なり・表と木の食い違い・段の順が違う)・**3**=書いた後の import の確かめが落ちた(木は書いたまま)。
- 本体の作業木の見分け(断る側に倒す=検収 M-2): 木とその親に `.git` が 1 つも無いときだけ git の外=書ける。見つかった `.git` が
  ディレクトリなら本体=断る。ファイル(`git worktree add` の作業木)なら git に `--git-dir` と `--git-common-dir` を聞き、違えば
  ほかの作業木=書ける。git が失敗したら断る。呼び手の `GIT_DIR` などの環境変数は外して聞く。
- 2 回当てても同じ(当たっている行=古い道が無く新しい道がある行は飛ばす)。

## 何をするか

1. 選んだ段の行(`kind` が `move`・`empty`・`delete`)を、木の今の形で「当てる」「当たっている」「保留(断る)」に分ける。
2. 書き換える(**許可の一覧だけ**。下の節)。この段で空にしない包みの頭の再輸出のうち、出どころのモジュールが包みの外へ移る
   ものは、その import の文を頭から除く(頭を通る import は同じ段で元のモジュールへ向け直すので、読み手は残らない。残すと、移した
   モジュールが古い包みの兄弟を読むときに古い頭が走り、頭が移したモジュールを読み返す循環の import になる=全段の予行で
   `agents/__init__.py`・`llm/__init__.py` に見つかった。頭の中で使う名は除かない)。除いた名は、その頭の `__all__` からも除く
   (頭が自己整合であること=親の裁定 review3 の 2。許可の一覧の (e))。
3. ファイルを新しい道へ移す。頭の行(`__init__.py`)は、新しい頭を空(0 バイト)にし、古い頭は古いディレクトリにファイルが
   残るなら空にして残し、残らなければ消す(表の「(空にする)」と、計画 §7-4 の「古い頭は空にし、古い包みに割るファイルが残る間は
   残す」)。前の段で空にして残した古い頭は、古いディレクトリの最後のファイルが出た段で消す(段を順に当てても、まとめて当てても
   同じ木になる=試験 `test_stages_in_order_give_the_same_tree_as_together`)。新しいディレクトリで頭の無いものには空の頭を足す
   (計画の「新しい頭 28」)。`economy/__init__.py`・`world/__init__.py`
   は置き場が同じで頭を空にする行(`empty`)。
4. 守り(下の節)を通らなければ書かずに止める。
5. `--apply` のときは書き、終わりに `src/shibuya` の下の「`__pycache__` のほかに何も無いディレクトリ」を `__pycache__` ごと消す
   (検収 L-a。同じ木に段を重ねて当てると、前の段の import の確かめが作った `__pycache__` だけが古い包みのディレクトリに残り、
   名前空間の包みとして import できてしまう)。消したディレクトリは標準出力と import の確かめの JSON(`removed_cache_only_dirs`)
   に出す。そのあと import の確かめを回す(下の節)。

## 許可の一覧(書き換えてよいもの)

| 記号 | 何を | どこ |
|---|---|---|
| (a) | src・tests・tools の Python の import の文(AST で見つけ、文の該当の部分だけ。再輸出の頭を通る import は元のモジュールへ) | `imports.py` |
| (b-src) | 計画 §7-5 で「段 3 の道具で直す」としたランの側の道の表。規則 `exact`=文字列の全体が移すファイルの今の道なら新しい道へ | `allow.py` の `SRC_TABLES` |
| (b-tests/tools) | tests と tools の道の文字列・`/` の結合・点の道・子のプロセスに渡すコードの import の文。規則 `paths` | `allow_tests_tools.toml`(`cli.py allow` が走査で作る) |
| (c) | 固定の表 `class_ids.py` の鍵だけ(値=凍結の名は変えない) | `allow.py` の `CLASS_IDS_TABLE`・`classids.py` |
| (d) | つなぎの台帳の道の対応の表 `engine/bridging/ledger_paths.py` の `LEDGER_PATHS`。移したファイルごとに「今の道 → 台帳に書いてある道」を足す(台帳の JSON は書き換えない=親の決定 1・案 (b)) | `allow.py` の `LEDGER_PATHS_TABLE`・`ledgerpaths.py` |
| (e) | この段で頭から除いた再輸出の名だけを、その頭の `__all__` から除く(1 行 1 要素の行を行ごと。行の終わりの注は注の行として残す。ほかの形は除かずに注意=守り `head_all` が止める) | `imports.py` の `all_drops` |
| (f) | pyproject の `[tool.setuptools.package-data]` の鍵のうち、この段で無くなる包みの名だけ。glob に当たっていたファイルが同じ形で 1 つの包みへ移ったとき、鍵をその包みの名にする(親の裁定 2026-11-11 判断 2。world の段で `shibuya.manifest` → `shibuya.world.ledger`)。pyproject のほかの行は触らない | `pkgdata.py` |
| (a) の範囲の追加 | tests が道で読む docs の記録の道具 11 本(import の文だけ。文字列は書き換えない=親の決定 7)。一覧は tests の走査と同じ(試験) | `allow.py` の `RECORD_TOOLS`・`scan_record_tools` |

(b-src) の (ファイル, 記号): `engine/state_ledger.py` の `OWNER_CLASSES`・`OWNER_ALT_CLASSES`・`_ALLOW_BAND`・`_ALLOW_B4`・
`_ALLOW_REVENUE`・`_ALLOW_ENERGY_BALANCE`・`_ALLOW_HEADING`・`_ALLOW_TASK`/`engine/state_ledger_ast.py` の `DECL_FILES`・
`UNRESOLVED_ALLOW`・`RESULT_FILES`・`GENERIC_FILES`・`DIAG_EXITS`・`EXT_AST_ALLOW`・`ext_reason`(関数の中の 1 か所)/
`engine/rng_audit.py` の `SAFE_SITES`・`UNDETERMINED_SITES`・`scan_sites`(関数の中の 1 か所)/`build/catalog_freeze.py` の
`CATALOG_JSON_RELPATH`(構築の側が凍結の JSON を書く先=親の決定 2。規則 exact は `src/shibuya/` から始まる形も読む)。乱数の
用途名(`engine.processes.rail` など)・理由の文は文字列の全体が道でないので書き換わらない。

**それ以外の文字列の定数は書き換えない**: docstring・注・`basis` の記録の文・理由の文・manifest に出る文(腕 mora の
`engine.speech.port.mora_count(…)` など)・ランの側の src の道の形の文字列のうち表の外のもの・docs・つなぎの台帳
(`docs/design/bridging-ledger.json` の `declared_in`)・pyproject。触らなかった道の形の文字列は報告の `untouched` に出す。

規則 `paths` の細部: 斜線の道 `[src/shibuya/|shibuya/]<道>.py|.json`・点の道 `shibuya.<モジュール>[.<名>…]`(後ろが `/` の
版の ID と、凍結の名=クラスの凍結の名・乱数の用途名ほかは触らない。包み=ディレクトリの名だけの `"shibuya.engine"` は、中の
ファイルが 2 つ以上の包みへ分かれて行き先が 1 つに決まらないので、書き換えずに報告の `skipped_in_allowlist` に `dotted_package`
で出す=検収 L-7。斜線のディレクトリの道も書き換えない)・コードとして読める文字列の import の文・2 つ以上の定数に
またがる `/` の結合。ASCII の外の字を含む文(コードとして読めるものを除く)と f 文字列の部分は触らない。書き換えは値で作って
字面へ当て、`ast.literal_eval` で値が合うかを確かめる(合わなければ触らずに報告)。

記号の決め方(`model.symbol_map`): 頂上の関数とクラスはその名・メソッドは `クラス.メソッド`・関数の中の入れ子は外の関数の名・
頂上の代入は左辺の名・ほかの頂上の文は `<module>`。

## 保留の一覧(道具は動かさない)

保留の一覧は `table.py` の `HELD` の 1 か所だけ。名指しで動かそうとすれば断り(終了コード 2)、段を選んだときは動かさずに報告の
`refused_held` に出す。**11-16 の答え([返事その 8](../../docs/design/prompt-2026-11-16-reply8.md) §1-6)で 7 行とも決着し、今は空**
(仕組みは残す=試験は作った見本の対応表で確かめる)。決着の文は全ファイルの表の行の「理由」にある。

| 今の道 | 決着 |
|---|---|
| `engine/contact/deliver.py`・`calls.py`・`chat_state.py`・`tools.py` | 今 society に置く(§1-6 の 1)=`society/contact/`・段 `society_contact` |
| `engine/resolve.py` | 移す段では act に置く・割る段 6 で `apply_detection` を 2 つに割る(`act/ops/detect_writes.py` と `mind/ops.py`=§1-6 の 2)。割る行なので段 4 では動かさない |
| `engine/run.py` | `python -m shibuya.engine.run` の入口は interfaces へ(割り先 `interfaces/cli/run_args.py`=§1-6 の 6)。割る行(段 5b) |
| `engine/removed_switches.py` | 行 224a=親が置き場を確かめた(`foundation/arms/removed.py`)・段 `foundation_224a` |

## 守り(1 つでも当たれば書かずに止める・終了コード 1)

1. `names_frozen`: `tests/engine/state/names_frozen.json` の静的な欄(乱数の領域の名・道の形の領域の名と接尾とほかの名の
   出てくる数・版の ID とハッシュの見出しの多重集合)を、書き換えた後の src から集め直して比べる。
2. `class_ids`: 固定の表の値と置き場の宣言(`CLASS_ID`)が凍結の写像(`class_ids_frozen.json`)と同じ・表の鍵と宣言が src の
   全部のクラスと 1 対 1。鍵を書き換えるときは、全行で新しい鍵が対応表で古い鍵に戻り、値が古い鍵の値と同じことを確かめる
   (同じ `__qualname__` の組 `Arbiter`・`GoodsLedger`・`Renderer`・`Scheduler` の取り違えを止める=再検収 L-a)。対応表が
   1 対 1 でないときも止める。`engine/events/log.py` の `Experiment.CLASS_ID` は書き換えない。
3. `shaped_74`: ランから拾った道の形の名 74 種が、ランの側の src の文字列の定数(許可の一覧の記号と固定の表の鍵を除く)に
   出てくる数が前と同じ。
4. `outside_allowlist`: 許可の一覧の外の文字列とバイト列の定数(docstring を含む)がファイルごとに 1 つも変わらない。許可の
   一覧の中でも、凍結の値の字面(クラスの凍結の名・乱数の用途名・接尾・版の ID・見出し・ほかの名・点の形の 74 種)の出てくる数は
   変わらない。空にする頭に定義(関数・クラス)か、import・docstring・`__all__` のほかの文(代入・`if`・`try` ほか)があれば
   止める(空にすると消える=検収 L-f)。
5. `ledger_paths`: (d) の表の今の道は木にある・台帳の道が重ならない・台帳のコードの行の道は全部、表を通して今のファイルに
   届く(台帳の JSON があるとき)。
6. `import_names`: 書き換えの前後で、各ファイルの import の文が結ぶ名(別名を含む・`import a.b` は `a`)の多重集合が同じ
   (検収 m14。頭から除いた再輸出の名だけは減ってよい)。
7. `head_all`: 空にしない頭の `__all__` の名は全部その頭で結ばれている(定義・代入・import・子のモジュール)。(e) で `__all__`
   を書き換えた頭は「前の `__all__` から除いた再輸出の名を抜いたもの」と同じ(並びも)。
8. `package_data`(pyproject を渡したとき): package-data の鍵は全部、木に在る包みで、glob が 1 本以上に当たる。
9. 移す前の木が凍結と既に違えば、何もせずに止める。移す前の木の頭の `__all__` に結ばれない名があっても止める(前の道具で
   当てた木)。

書いた後の import の確かめ(`importcheck.py`): `src/shibuya` の全モジュールを、子のプロセスで 1 つずつ(`shibuya` のモジュールを
毎回 `sys.modules` から外して)最初から import する+`python -m shibuya.cli --help`。循環の import は読む順で落ちたり落ちなかったり
するので、全部を最初に読む。守り(書く前)ではなく、書いた後の確かめ(木が要る)。読んだ `shibuya` が木の `src` でなければ
落ちたと数える。対応表の頭の行のうち木に頭がもう無い包み(移して無くなった包み)が、名前空間の包みとして import できない
(`importlib.util.find_spec` が `None`)ことも見る(検収 L-a)。`--apply` の後に落ちれば終了コード 3。`importcheck --out` の
置き場が本体の作業木の中なら断る(検収 L-g)。

## 報告(`pkgmove_<段>_report.json`)

- 書き換えた import の文の数(`import_statements`=src / build / tests / tools / docs=記録の道具)・ファイルの数・再輸出の頭を通したもの
  (`import_via_head`)・包みから子のモジュールを読む文で子が移すもの(`import_via_package`)・行き先が 2 つ以上に分かれて文を
  分けたもの(`import_split_statements`)と、計画 §7-4 の段 4 の見積もり(`plan_estimate_stage4`)。
- 道の文字列の数(`path_strings`=`src_table`・`slash`・`dotted`・`chain`・`code_import`)と (ファイル, 記号)。
- 固定の表の鍵の数・並べ直したか。(d) の表に足した行の数(`ledger_paths_added`)。頭から除いた再輸出の名
  (`dropped_reexports`)と、頭の `__all__` から除いた名(`dropped_all`)。保留で断った行・当たっていた行。新しい頭・空にした頭・
  消した頭。
- 触らなかった道の形の文字列(`untouched`=移すモジュールを指すが許可の一覧の外のもの・`skipped_in_allowlist`=許可の一覧の
  中で規則が触らなかったもの)と、どのモジュールでも道の形を含む定数の数(`untouched_broad_constants`)。
- つなぎの台帳の `declared_in` の `src/shibuya/…` の行の数と、移すファイルを指す行(書き換えない=段 4 の前の判断待ち)。
- 注意(`warnings`): 頭を空にする包みを属性で読む所(`from shibuya.engine import body as _body` の後の `_body.X`)・相対の
  import が移すファイルか移すモジュールにかかる所(書き換えない=検収 L-5)・頭から除いた再輸出ほか。
- **数え方**: `import_statements` は、道具が書き換えた import の文の数(文の中の名の数ではない)。空にする頭・消す頭の中の import
  は数えない(頭は丸ごと空にする)。頭から除いた再輸出の文は数える。計画 §7-4 の定義(動くファイル=頭を除くモジュールを読む
  import の文)の数は別に数え直して記録に書く。

## 試験

`tests/tools/test_pkgmove.py`(data は要らない)。一時のコピーの木で回し、import の文と許可の一覧の行のほかは 1 バイトも変わら
ないこと・許可の一覧の外の定数が変わらないこと・凍結の値が残ること(負の対照つき)・書かない実行が何も書かないこと・保留と本体の
作業木を断ること・冪等・対応表と許可の一覧が作り直しと同じことを確かめる。

## 段ごとの import の決まり(`contracts.py`・`contracts.toml`)

段 4 の各段の木で CI の `lint-imports` が通るように、pyproject の `[tool.importlinter]` の節を段ごとに作る(親の決定=brief_contracts)。元は `contracts.toml`(計画 §1-2 の層・§6-4 の決まり 1〜8・今の 5 つ・28 本・計画の表の外の辺 1 本=親の仮採用)。作り方と段ごとの結果は記録 `docs/bench/analysis/pkgmove-346/README.md` の §10-12。`--apply` は本体の作業木を断り、木の当たっている行が段と食い違えば断る。

〔段 4 の残り〕計画 §6-6 の 2 つを足した(返事その 8 §1-6 の 7・3): 決まり 9「一時の区分を読めるのは runtime と interfaces だけ」(protected・`interim_bundles` の段から)と決まり 10「runtime の核は中身を読まない」(forbidden・直の辺だけ=`allow_indirect_imports`・`delete` の段から。§6-6 の表の辺は `[[ignore_66]]`)。報告と要約に例外の数(延べ `ignore_lines`・重なりを除いた `ignore_unique`・消える段ごとの `ignore_gone_at`)を出す。記録は §13。

- **効いている例外**(検収 中-1): 例外は「両側と辺が在る」だけで載せる(計画の 28 本と「消える段」の注を保つ)ので、何も止めて
  いない例外も載る。`--out`(か `--probe`)を付けると、例外の行を 1 本ずつ外してその契約を回し、broken になる行(延べ)と辺
  (重なりを除く)・消える段ごとの数を報告の `ignore_effective` に出す(`ignoreprobe.py`=grimp と import-linter の契約のクラスを
  子のプロセスでメモリの中で回す。木は変えない)。
- **決まり 10 は直の辺だけ**(検収 中-3・名に「(直の辺だけ)」): 核のモジュールが中身の包みを直に読む辺だけを見る。間接の辺は
  見ない: 核の `runtime.systems.conductor` は核の外の `assemble`・`probe`・`table` を、核の `runtime.systems.day` は核の外の
  `state_io` を読み、その先で act・economy・experiments.port・interim_bundles・mind に届く(例 conductor → assemble → act.intent・
  day → state_io → engine.run → mind.judge.classical)。理由: 計画 §6-6 は核から中身を読む辺を直の辺で数えた。間接も見るには核の外の
  runtime への辺 4 本を例外にすることになる=核の範囲の問い(親がユーザーに上げる)。
- **節が前の段と同じなら pyproject を書かない**(検収 低-1): `contracts --apply` は節の中身(`same_section`)が同じなら書かない。
  見出しの注の段の名は前の段のまま残る(society_contact の段=「段 validation」・foundation_224a の段=「段 interim_bundles」)。

## 〔割る段 5a〕割る行を当てる(`split.py`・親の裁定 Q10=案 A)

割る段 5a(語彙・型・定数を下ろす割り・17 本)は、割る行(`kind = "split"`)を 1 本ずつ当てる。計画の要旨は第347 の報告
[docs/ops/report-347-2026-11-16.md](../../docs/ops/report-347-2026-11-16.md) §2、親の裁定と道具の記録は
[docs/bench/analysis/split5a-347/README.md](../../docs/bench/analysis/split5a-347/README.md)。順は `table.SPLIT_ORDER`
(群 G1〜G5 の 17 本)。18 本目だった `engine/speech/port.py`(`mora_count`)は延ばした(割る行のまま順から外した=
`table.SPLIT_DEFERRED`・台帳の道を書き換えられる版上げで下ろす)。道具は順に無い行を断る。

```
python tools/pkgmove/cli.py split --next [--tree <木>] [--out-dir <置き場>]           # 次の 1 本(書かない)
python tools/pkgmove/cli.py split --only <今の道> [--tree <木>] [--out-dir <置き場>]  # 名指し(順が違えば断る)
python tools/pkgmove/cli.py split --next --apply --tree <木> [--out-dir <置き場>]      # 書く(本体の作業木は断る)
python tools/pkgmove/cli.py split --through <今の道>|all --out-dir <置き場>           # 書かない実行だけ: 次の本から順に
                                                                                     # メモリの中で当てて本ごとの報告
```

- 終了コード: **0**=できた・**2**=断った(表せない・順が違う・手で直す読みが残る)か守りが止めた(親の発注=守りが「同じ」で
  なければ当てない)・**3**=書いた後の import の確かめが落ちた。`--through` は「手で直す」読みを残したまま順に当てて報告する
  (書かない)。
- 名の単位の表: 全ファイルの表 §4 の節(5a の 17 本と延ばした 1 本は全部の名に開いた=親の裁定 Q9)を `cli.py map` が `map.toml` の割る行の
  `[row.names]`(頂上の名 → 割り先)へ写す。§4 の注「宣言した書き換え: 割り先 `X` では別名 `V` を外す」は `[row.rewrites]`
  (親の裁定 Q6=`V.x` → `x`)。割り先の 2 つ目以降の新しいファイルは §3 に move の形の行(割るかの欄=「いいえ(`元` の割り先)」=
  `split_from`・親の裁定 Q1)。この行は段 4 の段の行に数えない(割る前は old も new も無い)。
- 当て方: 元のファイルの頂上の文を「単位」(前の注と空行を付けた文)に切り、名を結ぶ文は表の割り先へ、ほかの文(assert)は読む
  名の割り先へ。主な割り先の docstring は元のまま、2 つ目以降の新しいファイルは決まった型の docstring。import は割り先が使う名
  だけ(全部の名を使うなら元の字面のまま)・兄弟の割り先からの import を足す・`__all__` は割り先ごと(元の並び)。既に在る割り先へ
  は import を在る import の後ろへ・`__all__` の名を在る `__all__` の後ろへ(無ければ作る)・単位をファイルの後ろへ。元のファイル
  の頭(`llm/__init__.py`)は、ディレクトリにほかのファイルが残る間は 0 バイトで残し、0 バイトの頭しか残らないディレクトリの頭は
  消す(親の裁定 Q14・Q15)。主な割り先が元のファイルの今の置き場(段 4 で移した=延ばした 18 本目の形)なら、そのファイルを書き直す。
  元の相対の import は絶対の形に作り直す。星の import のある元・既に在る割り先と同じ名を足す形・`from __future__` が元と既に在る
  割り先とで食い違う形・宣言した書き換えの `x` が局所の名に捕まる形は断る(G0 の検収 中-1・中-2・低-1・低-3)。どの割り先も使わない
  import(途中の再輸出を含む)と、import・`__all__` の前と中の注は写さず、報告の `unwritten` に本ごとに出す(低-2)。
- 読み手: import の文は名の単位で割り先へ(文を割り先ごとに分ける=今の `_edits_from`)。割るモジュールが import で結んだ名
  (再輸出)は、その名を持ち続ける割り先へ(無ければ元のモジュールへ)。別名で読む形(`from P import m as X`・`import M as X`)は
  `X.名` などの割り先が 1 つのときだけ書き換え、2 つ以上・表に無い名・名で読まない使い方は「手で直す一覧」(報告の `manual`)。
  相対の import と星の import で割るモジュールを読む読み手も「手で直す一覧」(中-2)。
  道の文字列: src は許可の一覧 (b-src) の表(同じ組の中の関数・クラスの名の割り先へ=計画 c9・無ければ主な割り先)、tests と tools
  はその割る行の道か名を持つ文字列の記号だけを、その本の走査で許可の一覧にする(`split.STRING_EXCLUDE` は除く=表の old の固定の
  一覧・植えた文)。docs の記録の道具は import だけ(親の決定 7)。固定の表の鍵はクラスの単位の写像(`classids.split_keymap`・守り
  `check_split_keys`)。つなぎの台帳の道の表は「主な割り先 → 元の道」を 1 行足す(台帳の JSON は変えない)。
- 守り(1 つでも当たれば書かない): ① 元の頂上の文の AST の多重集合=割り先に足した文(宣言した書き換えは元の側を同じ形に直して
  比べる)と、割り先ごとの文の順(元の並びからその割り先の文だけを抜いた並び・中-3) ② 文字列とバイト列の定数の多重集合
  (モジュールの docstring を含む) ③ 割り先で結ばれない名が元より増えない・元の頂上で結ぶ名(組み込みの名を覆う名を含む)を読む文は
  割り先でも同じ物に結ばれる(中-1) ④ つなぎの台帳の 6 形の宣言が元と割り先とで同じ(2 つ目以降の新しい割り先に宣言が入れば、
  台帳の道の表=1 対 1 で表せないので止める)。ほかに段 4 の守り(名の凍結・固定の表・道の形の 74 種・許可の一覧の外の定数・import
  の文が結ぶ名・頭の `__all__`)と、import の決まり(高-1): 割る前と後の木で `contracts.toml` から作る節を比べ、言えなくなった
  単位・決まりと古い決まりから外れた名が、`[[split_weakens]]` の宣言(2 本目の agents・10 本目の llm)のほかに増えたら止める
  (守りの値は「同じ」か「宣言どおり N」)。`cli.py split` は書かない実行でも木の src に `__pycache__` を書かない(低-4)。
  〔G2 の 5 本目の欠陥の後〕守り「import の循環」: 読み込みの時に走る import のグラフで、割る前に無かった循環ができたら止める
  (既に在る割り先へ足す import が、その割り先を読むモジュールと循環する形。止めた文に循環の新しい辺と読む文の場所を出す)。
- 試験: `tests/tools/test_pkgmove.py` の「割る段 5a」の節(見本の木・負の対照=1 文を落とす・2 か所に置く・定数を変える・import
  を落とす・宣言の無い別名・2 つ目以降の割り先の宣言・鍵の取り違え・手で直す読み・主な割り先が元のファイル・本物の表と木)と
  「G0 の検収の直し」の節(済んだ本・順が違う本・飛ばした木・本体の作業木への `--apply`・頭を割る行の最終の名・宣言の外の弱まり・
  組み込みを覆う名・星と相対の import・在る名の上書き・`from __future__` の食い違い・順の入れ替え・docstring だけの変異=② だけ・
  局所の名に捕まる書き換え・写さなかった import と注・本物の木で 17 本を順に当てる契約の数=`slow`)。
- 契約: `contracts.toml` の `[[ignore_split]]`(割る段で出る辺 4 本・親の裁定 Q3)。`appears_with` の割る行を当てた木から載せる。

## 〔割る段 5b〕入口の転送・入口の移し・byte-check の範囲(`split.py` の G0 の拡張)

割る段 5b(大きな部品 5 本=`engine/commit.py`・`engine/presence.py`・`engine/calendar_shadow.py`・`engine/run.py`・`cli.py`)は、
`table.SPLIT_ORDER` の 18〜22 本目(群は `table.SPLIT_GROUPS["5b"]`=G1 が commit → presence → calendar_shadow・G2 が run・
G3 が cli)。親の裁定と記録は [docs/bench/analysis/split5b-347/README.md](../../docs/bench/analysis/split5b-347/README.md)。
使い方は 5a と同じ(`split --next`・`--only`・`--apply --tree`・`--through`)。足したもの:

- E2 入口の転送(`table.SPLIT_FORWARDERS`=`cli.py` → `interfaces/cli/main.py`・型は `table.forwarder_text`・親の裁定 Q6 の (a)・Q7):
  割った後の元のファイルを消さず、`if __name__ == "__main__":` の中で割り先の `main` を import して `raise SystemExit(main())` する
  だけの転送(docstring つき・頂上で名を結ばない)で書き直す。`is_done` は転送が型どおりのときだけ済んだと見る・`source_rel` は転送
  を元のファイルと見ない・`contracts.view` は転送の行の主な割り先を最終の名と見る(単位 interfaces が言える)。名の無い点の道
  `"shibuya.cli"` は書き換えない(転送が受ける=`-m shibuya.cli` は外との約束)。守り「入口の転送」: 型と同じ・頂上で名を結ばない
  (AST で各部分を見る)・つなぎの宣言が無い・呼ぶ `main` が割り先の頂上に在る。
- E3 入口の移し(`table.SPLIT_ENTRIES`=`engine/run.py` → `interfaces/cli/run_args.py`・返事その 8 §1-6 の 6): `if __name__ ==
  "__main__":` は宣言した入口の割り先へ(読む名 `main` の割り先と食い違う宣言・宣言の無い入口は断る)。名の無い点の道(割るモジュール
  の名だけの文字列)は、`-m` の文脈(文字列の中の `-m <名>`・並びや呼び出しの引数で 1 つ前の要素が `"-m"`)なら入口の割り先へ、
  それ以外は主な割り先へ黙って向けず「手で直す一覧」へ(`strings.split_nameless`=段 6 の E8 はここに宣言の表を先に引く形で足す)。
  文字列の中の手で直す所(コードの文字列の import を含む)も「手で直す一覧」に入れる。書いた後の確かめは、在る入口
  (`importcheck.ENTRY_MODULES`=`shibuya.cli`・`shibuya.interfaces.cli.run_args`)ごとに `python -m <入口> --help` を回す。
- E4 書き換えの範囲の外(`split.SPLIT_EXCLUDE_PATHS`=`tools/bytecheck/`・`tests/tools/test_bytecheck.py`・親の裁定 Q9 の (a)):
  書き換えず、書き換えたはずの所を報告の `excluded_sites` に出す。byte-check のランの入口は `tools/bytecheck/check.py` の
  `resolve_run` が解く(`interfaces/cli/main.py` が在ればその `run`・無ければ `shibuya.cli.run`)。
- 〔G0 の直し・検収 高-1〕`tests/_places.py` の割る行の口(`split_files`・`split_source`・`split_module_names`・`_split_names`=
  `strings.TABLE_KEY_CALLS`)の第 1 引数は対応表の鍵(元の道=値そのもの)なので書き換えない(呼び出しの形で見る)。書き換えなかった所は
  報告の `table_key_sites` に出す。〔高-2〕tests と tools の文字列を選ぶとき、コードの文字列の `from <包み> import <割るモジュール>`
  の形も拾う(`strings.code_import_hits`)。コードとして読めれば import の書き換え(別名の割り先が 1 つなら機械で)・決まらなければ
  「手で直す一覧」、コードとして読めない文字列(シェルの文)と f 文字列の部分の中のものも「手で直す一覧」(黙って残さない)。
- `split.STRING_EXCLUDE` に `tools/c8/c8lib.py` の `scan_engine_ablation_ids` を足した(元の置き場の道と比べる字面
  `"engine/presence.py"`=今の道へ書き換えると比べる相手が無くなる)。〔G2 の直し〕`tests/engine/test_state_format_10f.py` の
  `_HEAD_CHILD` も足した(古い commit の src の写しでだけ回す子のコード=古い置き場の名のまま・今の置き場へ書き換えると `No module named`)。
- 試験: `tests/tools/test_pkgmove.py` の「割る段 5b の G0」の節(見本の木の転送・転送を変えた木・名を結ぶ転送の負の対照・転送の
  形の各部分・転送の行の最終の名・入口の移しと `-m` の文字列・`-m` でない名の無い点の道=手で直す・食い違う宣言と宣言の無い入口・
  byte-check の範囲の外と負の対照・入口ごとの `--help`)と、本物の木で残りの本(22 本の順)を順に当てる `slow`。
  `tests/tools/test_bytecheck.py` の `test_resolve_run_takes_the_split_entry_when_it_exists`。

## 〔割る段 5b の G3 の前〕別名の割り先の宣言(`split.SPLIT_ALIAS_DESTS`・E5-a・親の裁定)

- なぜ要るか: 割るモジュールを別名で読む読み手(`from shibuya import cli` の `cli`)の向け先を、道具の既定は読む名の**定義の割り先**
  (import で結んだ名は再輸出の割り先=主な割り先が先)で決める。差し替え(`monkeypatch.setattr(cli, "名", …)`)は、その名を**呼ぶ時に
  読む関数の割り先**のモジュールの属性へ向けないと届かない。2 つが違う所(例: `cli.run` が読む `build_ledger_bundle` の定義は
  wire_economy)では、既定では「手で直す一覧」から抜けられない。読む関数が 2 つの割り先に分かれた名は、割り先ごとの別名で両方を
  差し替える(割る前は 1 つの差し替えが両方に効いていた)。
- 何を宣言するか: 1 行(`split.AliasDest`)=割る行(元の道)・ファイル・別名 → 割り先。割り先に無いのが正しい名(常に偽の `hasattr`
  で守られた読み)は `absent` に名前で挙げる。宣言の在る別名は宣言の割り先へ向き、宣言の無い別名は今までどおり。使った宣言は報告の
  `alias_declared` と `split --through` の行に出る。
- 守り(1 つでも当たれば書かない・書かない実行でも止める・止めた文は「別名の割り先の宣言の守り:」の後にファイル・別名・名):
  別名が割るモジュールを import していない(同じ名を別のモジュールに結ぶ場合を含む)・宣言の割り先がその割る行の割り先でない・別名で
  読む名(下の拾う形)が割った後の割り先の頂上で結ばれていない(定義でも、道具が足す import でもない。`absent` のほか)・名で読まない
  使い方がある(読む名を確かめられない)・`absent` に挙げた名を別名で読んでいないか、割り先の頂上に在る・宣言が使われなかった
  (その割る行を当てるのに、宣言のファイルが木に無い・範囲の外・別名を結ぶ import が無い)。
- 拾う形(`imports.alias_uses`): `X.名`(読み・代入・`del`)・`setattr`/`getattr`/`hasattr`/`delattr(X, "名", …)`・
  `<何か>.setattr`/`.delattr`/`.object(X, "名", …)`(`monkeypatch`・`mock.patch.object`)。拾わない形: 名が字面の定数でない
  `setattr(X, 変数)` と、`X` を素で渡す・読む形(どちらも「名で読まない使い方」で止める)・`mock.patch("shibuya.cli.名")` のような
  点の道の文字列(文字列の書き換えの側=名の割り先へ。今の木に cli のこの形は無い)・コードの文字列の中の別名(宣言はファイルの別名
  だけ=コードの文字列は既定の決め方)。
- 宣言が腐らないこと(`tests/tools/test_pkgmove.py` の `test_alias_declarations_name_files_and_aliases_that_exist_in_the_tree`):
  宣言のファイルが今の木に在り、その別名が割る前のモジュールか宣言の割り先を import している(割る前と割った後のどちらでも)。
- 差し替えが読む関数の割り先の全部に向いているかを道具が機械で確かめる守り(E5-b)は、段 6 の S6-G0 で入れた(下の節)。G3 では
  裁定の表・「外すと落ちる」の確かめ・検収で見た。

### 〔割る段 6 の S6-G0〕E5-c 素で使ってよい別名(`AliasDest` の `bare`・親の裁定 T5)

- なぜ要るか: 別名を属性で読まずに関数へ渡す・しまう形(素の使い方)は、別名を割り先ごとに分けても消えず、道具は必ず「手で直す
  一覧」に出す(厳しい当ては断る)。渡した先の関数がモジュールを受け取る約束の所(`runtime/run.py` の `_settle_pending_invites`
  の引数 `R`)や、モジュールをしまって `apply` を包む計器(`tools/c7` の 2 本)は、割る前に形を直す手が無い。
- 何を宣言するか: E5-a の 1 行に `bare=True`(印)・`reads`(素で渡した先・しまった先で、そのモジュールの属性として読み書きする
  名=親と検収役が渡した先の関数を読んで確かめた名)・`patches`(その別名を通す差し替えの名=字面で見える差し替えと、素で使った先の
  差し替えの全部)・`why`(渡した先・しまった先の関数と読む名)を書く。印のある別名は、許す形の素の使い方があっても宣言の割り先へ
  書き換わり、手で直す一覧に出ない。印の無い別名の素の使い方は今までどおり手で直す一覧へ。
- 許す素の使い方(`imports.BARE_OK`・`imports.bare_form`): 渡す(位置か名の引数。名を字面で書かない `getattr`・`setattr`・
  `vars`・`dir`・`.object` などへ渡すのは除く)・返す(`return`・`yield`)・しまう(代入の値そのもの=変数か属性へ)・既定の引数・
  比べる(`is None`・`is not None`=名を読まない)。ほかの形(入れ物に入れる・呼ぶ・添字・`==` で比べる)は宣言で表せない=止める。
- 守り(別名の割り先の宣言の守り=E5-a と同じ場所・同じ文の頭): 印があるのに素の使い方が 1 つも無い(印の腐り)・許さない形・
  `reads` か `why` が無い・`reads` と `patches` の名が割り先の頂上で結ばれていない・印が無いのに `reads`・`patches` がある・
  使われなかった宣言(E5-a と同じ)。別名の属性の読み(`X.名`)は E5-a と同じに割り先の頂上の名だけ。
- 差し替え(差し替えの届く先の守り=E5-b の `patch_reach`): `patches` の名ごとに E5-b の「届かせる割り先の集合」を出し、宣言の
  割り先が集合に無ければ止める(空振り)・集合にほかの割り先も在れば止める(素で使った先の差し替えは宣言の割り先にしか向かない=
  ほかへ届かない)。字面で見える、印のある別名を通す差し替えは、名が `patches` に無ければ止める。確かめた差し替えは報告の
  `patch_declared`(ファイル: 別名 の名 → 宣言の割り先・字面で見えた数)と `split --through` の行に出る(`patch_checked`・
  `patch_unseen` とは分ける)。
- 道具が辿らない形(`reads`・`patches` は人の確かめだけが根拠): しまう・既定の引数で写した先の読みと差し替え
  (`m = B; m.g(…)`・`self.m = B; self.m.g = …`・`def f(m=B): m.g(…)`)と、渡した先の関数の中の読みと差し替え。名を字面で
  書かずに読む関数へ「渡す」として通る形(`inspect.getmembers(B)`・`functools.partial(getattr, B)` など)も辿らない。宣言の外の名を
  写した先で読めば実行で音が立つが、**差し替えは音の立たない空振りになる**。
- **決まり(親の裁定・検収の低-1)**: 印(`bare`)のある宣言を足すときは、宣言が腐らない試験の受け手の表
  (`tests/tools/test_pkgmove.py` の `_BARE_RECEIVERS`)に、その受け手(渡した先・しまった先の関数やクラスと、その中でモジュールを
  持つ字面)を足す。試験(`test_bare_alias_declarations_name_what_the_receiving_functions_read`)は、受け手の字面から読み書きする
  名・書く名を引いて宣言の `reads`・`patches` と同じことを、`why` に受け手の名が在ることを、宣言のファイルの素の使い方が受け手へ
  渡すか受け手の中だけであることを確かめる。印のある宣言の集合と受け手の表は同じでなければ落ちる(受け手を足し忘れると落ちる=
  `test_negative_a_bare_declaration_without_its_receiver_fails_the_rot_check`)。道具に辿らせる拡張は今は入れない(段 7 で印の
  ある宣言が増えるなら、そのとき考える)。
- 段 6 の宣言は 5 つ(`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・
  `src/shibuya/runtime/systems/judge.py` の `R_TALK` → `act/ops/talk.py`=受け手は `runtime/run.py` の `_settle_pending_invites`・
  `tools/c7/attr_arms.py`・`tools/c7/occupancy_series.py` の `module` → `act/apply.py`=受け手は各ファイルの記録のクラス)。
  `judge.py` の宣言は、src の別名の分け(S6-G1 の下ごしらえ)の後に足した。

## 〔割る段 6 の S6-G0〕道具の拡張 E7・E8・E5-b・E9(親の裁定 Q1・Q8・追記・R2)

段 6(`engine/resolve.py` を 18 の割り先へ)の前に入れた 4 つ。src は変えていない。記録は
[docs/bench/analysis/split6-347/s6_g0_tools.md](../../docs/bench/analysis/split6-347/s6_g0_tools.md)。

### E7 台帳の道の前向きの表(`ledgerpaths.py`・`split.ledger_split_rows`・守り ④)

- 表 `LEDGER_PATHS_SPLIT`(src の `foundation/decl/ledger_paths.py`。src の側は S6-A が入れる)=割る段で 2 つ目以降の割り先になった
  ファイルの今の道 → 台帳の道。字面は `LEDGER_PATHS` と同じ形(`Final[Mapping[str, str]] = MappingProxyType({ … })`・鍵の昇順・1 行
  1 組・空なら `{` の次の行が `}`)。値は `LEDGER_PATHS` の値と重なってよい。前向きに引く順は `LEDGER_PATHS` → `LEDGER_PATHS_SPLIT`
  → そのまま(`ledgerpaths.ledger_of`)。逆向き(台帳の道 → 今の道)は `LEDGER_PATHS` だけ。
- 割る行を当てるとき、つなぎの台帳の宣言が 1 つ以上入る 2 つ目以降の**新しい**割り先ごとに、前向きの表へ「割り先の今の道 → 元の
  ファイルの台帳の道」を 1 行書き足す(宣言の入らない割り先の行は書かない=裁定 Q1 の条件 ③)。主な割り先の行は今までどおり
  `LEDGER_PATHS` へ。主な割り先が元のファイルの今の置き場の行(延ばした 18 本目の形)は、`LEDGER_PATHS` を変えずに前向きの表だけを
  書く。報告の `ledger_paths_split`。
- 前向きの表が無い木(S6-A の前)で行が要れば、「前向きの表が無い」で止める(黙って通さない)。行が要らなければ前と同じ。
- 移す(`ledgerpaths.rewrite` の `moves`): 前向きの表に載った鍵は前向きの表のまま付いて行く。前向きの表は中身が変わったときだけ
  書き直す。段 4 の `move.py` は変えていない(前向きの表の鍵を動かす移しは、その守り「許可の一覧の外」が止める側)。
- 守り ④(比べの厳しさは前と同じ=裁定 Q1 の条件 ④): 台帳の道で数える宣言の多重集合が割る前と後で同じ。あわせて、2 つ目以降の新しい
  割り先は「宣言がある ⇔ 前向きの表に行がある」・既に在る割り先(別の台帳の道)へ宣言が入る形は止める・`ledgerpaths.check`
  (表の今の道と前向きの表の今の道は木に在る・同じ今の道が 2 つの表の両方に無い・台帳のコードの行は `LEDGER_PATHS` で引いて今の
  ファイルに届く)・前向きの表の今の道は宣言を 1 つ以上持つ。

### E8 道の文字列の割り先の宣言(`split.SPLIT_PATH_DESTS`・`strings.split_path_dest`)

- 1 行(`split.PathDest`)=割る行(元の道)・読むファイル・記号 → 割り先。記号は `strings.py` が文字列の持ち主として出す名(頂上の
  関数・クラス・代入の左辺・メソッドは `クラス.メソッド`=`STRING_EXCLUDE` と同じ見方)。宣言はその記号の中の、名の手がかりの無い
  割るファイルの道(斜線の道の全体・文の中の斜線の道・`/` の連鎖・名の無い点の道)に効く。今は空(段 6 の 2 行
  `runtime/state/ledger.py::_ALLOW_REVENUE` → `act/ops/shop.py`・`runtime/state/ledger_ast.py::ext_reason` →
  `runtime/state/restore.py` は、割る行が順に入る次の発注で載せる)。
- 行き先の順: 宣言 → 同じ組の名(5a の `sibling_dest`)→ 割り先が 1 つの行なら主な割り先。**宣言も名の手がかりも無い道は、割り先が
  2 つ以上の行では主な割り先へ黙って向けず「手で直す一覧」へ**(主な割り先が元のファイルの行も同じ)。宣言と組の名が食い違えば手で
  直す一覧へ。名の無い点の道は前と同じ(`-m` の入口・転送の名)に加えて、宣言があればその割り先のモジュールへ。記録の文(ASCII の
  外の字を含む文)の中のものは前と同じく書き換えず、一覧にも出さない。使った宣言は報告の `path_declared`。
- 守り(書かない実行でも止める・止めた文は「道の文字列の割り先の宣言の守り:」の後に): ファイルが木に無い・記号がそのファイルに無い・
  宣言の割り先がその割る行の割り先でない・記号が書き換えの範囲の外(`STRING_EXCLUDE`・`SPLIT_EXCLUDE_PATHS`・道具の自分)・同じ記号に
  宣言が 2 つ・宣言が使われなかった。宣言はその割る行でだけ使う(ほかの行の宣言は引かない)。
- あわせて直した見落とし: tests と tools の文字列を選ぶとき、`/` の連鎖の記号は、ほかの記号に当たりのあるファイルでも拾う(前は当たりの
  無いファイルでだけ連鎖を見たので、連鎖が書き換えも一覧も無く残る形があった)。
- `split.STRING_EXCLUDE` に `tests/tools/test_repo_guide.py` の `LAYER_SRC`(偽の木の見本のコード=裁定 R2)を足した。
  〔表と順の検収の後の裁定〕`tools/repo_guide/guide_permits.py` の `RESOLVE_FILE`(`allow.py` に `RESOLVE_FILES` の無い見本の木で
  読む 1 本。`test_repo_guide` の見本の木がこの道に resolve の材料を置く=書き換えると試験が落ちる。割った後の本物の木では使わない)も
  足した。

### E5-b 差し替えの届く先の守り(`split.patch_reach`・守り `patch_reach`)

1. 割る前の読み手(src・tests〔`tests/c7` を除く〕・tools・docs の記録の道具。道具の自分と元のファイルを除く)から、割るモジュールの
   別名を通す差し替えを集める: `<何か>.setattr`/`.delattr`/`.object(<別名>, "名", …)`・組み込みの `setattr`/`delattr`・文字列の的
   (`<何か>.setattr("pkg.mod.名", …)`・`patch("pkg.mod.名")`)・属性への代入と `del`(`<別名>.名 = …`)・子のプロセスへ渡すコードの
   文字列の中の同じ形。別名の結びは、その関数の中の import が先・無ければ頂上の import。
2. 名ごとに届かせる割り先の集合: (a) 元のファイルの中で、その名を関数の本体で素の名で読む頂上の関数(メソッドはそのクラス)の割り先
   (引数・代入・内包の変数に覆われた読みは数えない) (b) src のほかのモジュールが呼ぶ時に別名の属性(`別名.名`・`getattr`)で読むなら、
   名を定義する割り先 (c) (a)(b) が空なら名を結ぶ割り先(定義の割り先か、import で結ぶ名は再輸出の割り先)。
3. 割った後の字面(道具の書き換えと E5-a の宣言を当てた後)で、同じ関数(試験・助け・フィクスチャ。コードの文字列の中は
   「記号(コードの文字列)」)の中の差し替えが向く割り先が 2 の集合と同じか。届かない割り先が 1 つでも在れば止め、名・差し替えの行・
   届かない割り先・呼ぶ時に読む所を出す。集合の外の割り先へ向く差し替え(その名を呼ぶ時に読む関数が無い=空振り)も止める。
4. 読み込みの時にだけ読む文(デコレータ・既定の引数・注釈・クラスの親と本体・頂上の代入と表・src のほかのモジュールの頂上の読み)は
   (a) に数えず、報告の `patch_load_time` に出す(差し替えが効かない読み)。
5. 主な割り先が元のファイルの行(元のモジュールが残る形=延ばした 18 本目)では、元のモジュールを主な割り先として、ほかの割り先と同じに
   確かめる(元のモジュールへ向いた差し替えで、呼ぶ時に読む関数が外へ出た割り先に在れば「届かない」で止める)。割り先でないモジュール
   (割った後に無い元のモジュール・転送)を指したままの差し替えは、その別名が手で直す一覧(`plan.manual`=別名を結ぶ import の文の
   行・コードの文字列はその記号の項)に在るときだけ「見られなかった」。在らなければ止める(〔検収の後の直し 1〕)。
6. 見られなかった形は報告の `patch_unseen` に出す: 名が字面の定数でない・的の文字列を組み立てる・別名が 2 つのモジュールに結ばれる・
   `vars`/`__dict__` を通す・手で直す一覧に在る別名が割った後も元のモジュールを指す・書き換えの範囲の外(`SPLIT_EXCLUDE_PATHS`)・
   名が元のファイルで結ばれていない。**厳しい当て(`strict`=`--apply` の道と `--through` でない書かない実行)は、`patch_unseen` が
   1 つでも在れば断る**(終了コード 2・断る文に場所とわけ。手で直す一覧と同じ扱い・宣言して通す口は無い=親の裁定)。`--through`
   (`strict=False`)は一覧に出すだけ。確かめた差し替えは `patch_checked`。`split --through` の行と要約にも出る。
- 範囲の外のファイル(E4)の名の無い割るファイルの道は、書き換えず手で直す一覧にも入れないが、報告の `excluded_sites` に「手で直す N」
  として出す(〔検収の後の直し 3〕)。
- `--map` を渡さないときも、CLI の要約の JSON・名指しの実行の JSON・`--through` の行に E7・E8・E5-b の欄が増えている(読み先・順・
  決まりは前と同じ)。

### E9 CLI の書かない道を見本の木で確かめる口(`cli.py split --map`・`--contracts`)

```
python tools/pkgmove/cli.py split --through all --tree <見本の木> --map <対応表 TOML> [--contracts <決まり TOML>] --out-dir <置き場>
```

- `--map` を渡すと、対応表を道具のリポの `map.toml` の代わりにその表から読み、割る段の順も表の割る行の `split_order`(1 から)から
  読む(`table.split_order_of`=番号が 1 から続かない・頭の `split_order` と食い違えば断る=終了コード 2)。`--contracts` は import の
  決まりの元。渡さないときの動きは前と同じ(表は `map.toml`・順は `table.SPLIT_ORDER`・決まりは `contracts.toml`)。
- 試験(`test_split_cli_dry_run_writes_nothing_in_a_sample_tree` ほか)は、見本の木(割る行 2 本・つなぎの宣言の走査は本物の
  `bridging_scan.py` の写し・凍結の JSON は見本の木から作る)で、終了 0・見本の木のバイトが同じ・要約の JSON に行ごとの守り・
  「書いていない」と、守りが止める見本(順の違う行の名指し・互いの名を読む割り先・割る順が続かない表)の終了コード 2 を確かめる。

### 試験

`tests/tools/test_pkgmove.py` の「割る段 6 の S6-G0」の節(E7 の表の読み書きと移し・前向きの行・元が主な割り先の行・守り ④ の負の
対照 4 つ・表が無い木/E8 の宣言の当て方・名の手がかりの無い道の手で直す一覧・src の道の表・守りの負の対照 6 つ・宣言の腐り・R2/
E5-b の通る形・止まる形 5 つ・読み込みの時だけの読み・見られなかった形・守りを外した負の対照/E9 の表の順・CLI の書かない道)と、
本物の履歴(5b の G3 の土台 `e6d221c`)で 22 本目を当て直す `slow`(git が無い所では飛ぶ)。
