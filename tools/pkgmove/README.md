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
```

- `--stage`: 段 4 の小さな段の名(`foundation`・`world`・`economy`・`act`・`mind`・`society`・`interim_bundles`・`runtime`・
  `experiments`・`validation`・`delete`)をコンマでつなぐか `all`。`--only <今の道>` で行を名指せる(何回でも)。
- `--tree`: 木の根(既定は道具のリポ)。対応表と許可の一覧は道具のリポのものを読み、凍結の JSON とつなぎの台帳は木のものを読む。
- `--out-dir`: `pkgmove_<段>_report.json`(報告)と `pkgmove_<段>.diff`(差分)、`--apply` なら `pkgmove_<段>_imports.json`
  (import の確かめ)を書く。木の外に置く。本体の作業木(か、その中)なら断る。
- 終了コード: **0**=できた(書かない実行では報告と差分だけ)・**1**=守りが止めた(書いていない)か `--check` の食い違い・
  **2**=断った(保留の行の名指し・本体の作業木への `--apply` か報告の置き場・`--apply` に `--tree` が無い・対応表の行き先の
  重なり・表と木の食い違い)・**3**=書いた後の import の確かめが落ちた(木は書いたまま)。
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
`refused_held` に出す。

| 今の道 | 理由 |
|---|---|
| `engine/contact/deliver.py`・`calls.py`・`chat_state.py`・`tools.py` | 問い 1 連絡の器 4 本の置き場(本文 §8-1 の 1) |
| `engine/resolve.py` | 問い 2 `apply_detection` の割り先(本文 §8-1 の 2。割る行なので段 3・段 4 では元々動かない) |
| `engine/run.py` | 問い 6 `python -m shibuya.engine.run` の入口(本文 §8-1 の 6。割る行) |
| `engine/removed_switches.py` | 行 224a 置き場は段 4 の前に親が確かめる |

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
8. 移す前の木が凍結と既に違えば、何もせずに止める。移す前の木の頭の `__all__` に結ばれない名があっても止める(前の道具で
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
