# 移す段 3「移す道具」(コードの区分の移動・返事その 7 §4-2)

> 段 3 は道具と試験と記録だけ。**src は 1 バイトも変えていない**(`git diff --stat -- src` が空)。ファイルを動かすのは段 4。
> 発注: [返事その 7](../../../design/prompt-2026-11-09-reply7.md) §4。計画: [最終の表と移す段の計画](../../../reference/package-map-final-2026-11-09.md)
> §7-0・§7-2・§7-4(段 3 の行)・§7-5 と[全ファイルの表](../../../reference/package-map-final-2026-11-09-files.md)。段 1・段 2 の記録:
> [move-346](../move-346/README.md)(§5〜§7)。土台 `f5426de`(枝 `stage/pkgmove`)。実装役 Opus 5.5。commit とタグは親。
> **段 3 の続き(§10・枝 `stage/pkgmove2`)では、段 4 の下ごしらえとして src を変えた**(4 ファイルの直しと新しいファイル 1 本=§10-3。
> 作業木の src の byte-check 0)。tools は `tools/repo_guide/guide_permits.py` を直した(§10-10 の 5)。§0〜§9 は段 3 の 1 回目の記録。

## 0. 要点

- **道具** [tools/pkgmove/](../../../../tools/pkgmove/README.md): 全ファイルの表から対応表 TOML(`map.toml`・327 行)を作り、
  段を選んでファイルを移す。既定は書かずに差分と報告だけを出す。書くのは `--apply --tree <置き場>` のときだけで、
  git の本体の作業木(か、その中)は断る。書き換えるのは許可の一覧だけ((a) import の文・(b) 道の文字列の表=
  (ファイル, 記号) の一覧・(c) 固定の表の鍵)。それ以外の文字列の定数は書き換えない。書く前に凍結の値が残ることを確かめ、
  変わるなら書かずに止める。保留の 7 行は動かさない。
- **試験** `tests/tools/test_pkgmove.py`(19 本・data 不要): 一時のコピーの木で回す。import の文と許可の一覧の行のほかは 1 バイトも
  変わらない・許可の一覧の外の定数が変わらない・凍結の値が残る(負の対照 5 本)・書かない実行は何も書かない・保留と本体の作業木を
  断る・冪等。
- **dry-run**: 段 4 の全段で import の文 **836 / 38 / 1,408 / 55**(src / build / tests / tools。計画 855 / 38 / 1,378 / 52)。
  foundation の段は 381 / 33 / 456 / 22。守りはどちらも 4 つとも「同じ」(§4)。
- **予行**(git の作業木の外の写しの木で、段 4 の最初の小さな段 foundation を `--apply`): byte-check 19 構成 37 欄
  **19/19 同じ・動いた 0・誤り 0・終了コード 0**。表を作る道具と凍結の道具の `--check` も「同じ」(凍結の道具は 6 つの短いランで
  道の形の名 74 種を拾い直した)。写しの木の範囲の試験は 6,610 passed・81 failed(1 本は前からの data のつなぎの 1 本。残る 80 本は
  段 4 の題=頭の写しの固定のバイト 53・つなぎの台帳 12・凍結の名を置き場として使う試験 4・道具が触らない形の道と名 8・試験の中の
  作った木の一部だけが書き換わった 3。§5-4)。
- **段 4 の前に要る判断**は §7(つなぎの台帳の `declared_in`・許可の一覧の外で働く道の文字列・頭を属性で読む所・表を作る道具の
  置き場ほか)。

## 1. 作ったもの

| ファイル | 中身 |
|---|---|
| `tools/pkgmove/__init__.py` | 包みの説明 |
| `tools/pkgmove/table.py` | 全ファイルの表を読む・対応表 TOML の書き手(標準ライブラリだけ。tomllib は読むだけなので小さな書き手を自前で)と読み手・**保留の一覧 `HELD`(1 か所)**・段の名 |
| `tools/pkgmove/map.toml` | 対応表(`cli.py map` が作る。327 行=move 205・keep 94・split 24・delete 2・empty 2。保留 7) |
| `tools/pkgmove/model.py` | 木(ファイルの中身を手元に持つ・改行はファイルのまま)・モジュールの索引・頭の再輸出の引き先・記号の決め方・書き換えの当て方 |
| `tools/pkgmove/imports.py` | (a) import の文の書き換え |
| `tools/pkgmove/allow.py` | 許可の一覧((b-src) の表・(c) 固定の表・(b-tests/tools) の読み手と書き手) |
| `tools/pkgmove/allow_tests_tools.toml` | (b-tests/tools) の (ファイル, 記号)(`cli.py allow` が走査で作る。67 ファイル・123 記号) |
| `tools/pkgmove/strings.py` | (b) 道の文字列の書き換えと、触らなかった道の形の文字列の拾い |
| `tools/pkgmove/classids.py` | (c) 固定の表の鍵の書き換えと鍵の守り(同じ `__qualname__` の組) |
| `tools/pkgmove/guard.py` | 凍結の値の守りと、許可の一覧の外が変わらないことの確かめ |
| `tools/pkgmove/move.py` | 計画(書き換えた後の木を手元で作る)・報告・差分・木へ書く |
| `tools/pkgmove/cli.py` | 入口(`map`・`allow`・`move`) |
| `tools/pkgmove/README.md` | 使い方・許可の一覧・保留の一覧・守り・報告の欄 |
| `tests/tools/test_pkgmove.py` | 試験 19 本 |
| `docs/bench/analysis/pkgmove-346/` | 本書・dry-run の報告 2 本(`dryrun/`)・予行の byte-check の JSON 3 本(`bytecheck/`) |

表を作る道具と凍結の道具(`docs/bench/analysis/move-346/tools/gen_class_ids.py`・`gen_frozen_names.py`)は、**記録の下に置いたまま**に
した(move-346 §7-2 の (4) をこの役が決めた)。理由: 置き場の道は src の `engine/class_ids.py` の docstring と凍結の JSON の `note` に
書かれていて、動かすとそれを書き換えることになる(段 3 は docstring も凍結の値も書き換えない)。道具の守り(`guard.py`)は凍結の
道具と同じ集め方を手元の木の文字列で別に実装した(3 つ目の実装)。ただし `gen_class_ids.py` は書く先を
`src/shibuya/engine/class_ids.py` に決め打ちしているので、段 4 の runtime の段で `class_ids.py` を動かすと壊れる(§7 の 5)。

## 2. 許可の一覧(書き換えてよいもの)

| 記号 | 何を | 規則 |
|---|---|---|
| (a) | src(build を含む)・tests・tools の全部の Python の import の文 | AST で見つけ、文の該当の部分(モジュールの名と別名)だけを書き換える。行き先が 2 つ以上に分かれる文だけを作り直す(名の行の注は名に付けて残す)。再輸出の頭を通る import は、頭を空にする段か、元のモジュール・頭の直の引き先が移る段で、定義したモジュールへ向ける |
| (b-src) | `engine/state_ledger.py` の `OWNER_CLASSES`・`OWNER_ALT_CLASSES`・`_ALLOW_BAND`・`_ALLOW_B4`・`_ALLOW_REVENUE`・`_ALLOW_ENERGY_BALANCE`・`_ALLOW_HEADING`・`_ALLOW_TASK`/`engine/state_ledger_ast.py` の `DECL_FILES`・`UNRESOLVED_ALLOW`・`RESULT_FILES`・`GENERIC_FILES`・`DIAG_EXITS`・`EXT_AST_ALLOW`・`ext_reason`(関数の中 1)/`engine/rng_audit.py` の `SAFE_SITES`・`UNDETERMINED_SITES`・`scan_sites`(関数の中 1) | `exact`=文字列の全体が移すファイルの今の道(`src/shibuya` からの相対)なら新しい道へ。乱数の用途名・理由の文は全体が道でないので変わらない |
| (b-tests/tools) | tests と tools の 67 ファイル・123 記号(`allow_tests_tools.toml`) | `paths`=斜線の道・点の道(`shibuya.` で始まる。後ろが `/` の版の ID と凍結の名は触らない)・コードとして読める文字列の import の文・2 つ以上の定数にまたがる `/` の結合。ASCII の外の字を含む文(コードを除く)と f 文字列の部分は触らない。値で作って字面へ当て、`ast.literal_eval` で値が合うかを確かめる |
| (c) | `engine/class_ids.py` の `CLASS_IDS` の鍵だけ | 鍵のモジュールの部分を対応表で新しい名に(`__qualname__` は凍結の JSON から)。値は変えない。鍵の昇順に並べ直す(表を作る道具の並びと同じにする。1 行 1 組の行の中身は変えない) |

記号の決め方: 頂上の関数とクラスはその名・メソッドは `クラス.メソッド`・関数の中の入れ子は外の関数の名・頂上の代入は左辺の名・
ほかの頂上の文は `<module>`。

**書き換えないもの**: 上の外の全部の文字列とバイト列の定数(docstring・注・`basis` の記録の文・理由の文・manifest に出る文・
乱数の用途名・版の ID・クラスの凍結の名)・`engine/events/log.py` の `Experiment.CLASS_ID`・docs・pyproject・つなぎの台帳。
例: 腕 `SHIBUYA_TALK_CLOCK=mora` の manifest に出る `engine/speech_clock.py` の `"engine.speech.port.mora_count(…)"` は、全段の
dry-run でも変わらない(試験 `test_mora_rule_and_other_untouched_path_shaped_strings_stay_in_the_all_plan`)。

(b-tests/tools) の一覧は道具の走査で作った(段 4 の全段・保留を除く対応で書き換えが起きる記号)。`--check` で今の木との食い違いを
見る。この一覧には `tools/bytecheck/tree.py` の `ROOT_READERS`(鍵の `shibuya/core/paths.py` などだけ。理由の文は日本語なので
触らない)が入る。byte-check の道具は別の役の持ち物なので、段 4 で書き換えてよいかは親が確かめる(§7 の 6)。

## 3. 保留の一覧(道具は動かさない)

`tools/pkgmove/table.py` の `HELD` の 1 か所。名指しで動かそうとすれば断る(終了コード 2)。段を選んだときは動かさずに報告の
`refused_held` に出す。

| 今の道 | 理由 | 種類 |
|---|---|---|
| `engine/contact/deliver.py`・`calls.py`・`chat_state.py`・`tools.py` | 問い 1 連絡の器 4 本の置き場(本文 §8-1 の 1) | move(interim_bundles の段で断る) |
| `engine/resolve.py` | 問い 2 `apply_detection` の割り先(本文 §8-1 の 2) | split(段 3・段 4 では元々動かない。割り先の一覧を記録だけ) |
| `engine/run.py` | 問い 6 `python -m shibuya.engine.run` の入口(本文 §8-1 の 6) | split(同上) |
| `engine/removed_switches.py` | 行 224a 置き場は段 4 の前に親が確かめる | move(foundation の段で断る) |

## 4. dry-run の報告(書かない実行)

`python tools/pkgmove/cli.py move --stage foundation --out-dir <置き場>` と `--stage all`(段 4 の 11 の小さな段をまとめて 1 回で)。
報告の JSON: [dryrun/pkgmove_foundation_report.json](dryrun/pkgmove_foundation_report.json)・
[dryrun/pkgmove_all_report.json](dryrun/pkgmove_all_report.json)(差分は道具で作り直せるので入れていない)。

| | foundation | 段 4 の全段 | 計画 §7-4 の段 4 の見積もり |
|---|---:|---:|---:|
| 当てる行(move・empty・delete) | 39(move 39) | 204(move 200・empty 2・delete 2) | 204(`.py` 201・JSON 1・消す 2) |
| 移すファイル(頭を除く) | 35 | 179 | — |
| 保留で断った行 | 1(`removed_switches`) | 5(連絡の器 4・`removed_switches`) | — |
| import の文 src / build / tests / tools | 381 / 33 / 456 / 22 | **836 / 38 / 1,408 / 55** | 855 / 38 / 1,378 / 52 |
| そのファイルの数 | 148 / 28 / 230 / 14 | 176 / 30 / 352 / 29 | 179 / 30 / 349 / 28 |
| 再輸出の頭を通る import(名を元のモジュールへ向けた文) | 3 / 0 / 10 / 0 | 5 / 0 / 17 / 1 | 10 / 14 / 40 / 3 |
| 包みから子のモジュールを読む文で子が移すもの(`from P import 子`) | 83 / 2 / 205 / 1 | 275 / 5 / 705 / 5 | — |
| 行き先が 2 つ以上に分かれて分けた文 | 3 / 0 / 9 / 0 | 4 / 0 / 11 / 1 | — |
| 道の文字列(src の表 / 斜線 / 点 / `/` の結合 / コードの import) | 5 / 29 / 19 / 3 / 27 | 145 / 150 / 35 / 16 / 45 | — |
| 固定の表の鍵 | 92 | 352 | — |
| 書き換えたファイル | 428 | 596 | — |
| 新しい頭・空にした頭・消した頭 | 9・4・0 | 46・8・17 | 新しい頭 28 |
| つなぎの台帳の `declared_in` で移すファイルを指す行(書き換えない) | 14(active 14) | 105(active 103) | —(`src/shibuya/…` は全部で 398 行) |
| 守り(names_frozen・class_ids・shaped_74・outside_allowlist) | 4 つとも同じ | 4 つとも同じ | — |

- 計画との差: import の文は数え方の違い(計画は 11-09 の木・この役は文が実際に書き換わるかで数える)と、11-09 の後に足された試験の
  分(段 1・段 2 の試験ほか)。再輸出の頭を通る数は計画の数え方が書かれていないので、この役の数え方を 2 つ(名を元のモジュールへ
  向けた文・包みから子のモジュールを読む文)並べた。どちらも計画の 10 / 14 / 40 / 3 とは合わない(数え方の違い=確かめていない)。
- 新しい頭: 全段で 46=頭の行から作る新しい頭 21+頭の行の無い新しいディレクトリの頭 25(計画の「新しい頭 28」との差 3 は、割り先
  だけが入るディレクトリ=段 4 では作らないもの、と見ている=確かめていない)。
- **段を順に当てても同じ**: 段 4 の 11 の小さな段を手元で順に当て(書かない)、各段で守りが 4 つとも「同じ」・保留の行は
  foundation で 1・interim_bundles で 4 を断った。順に当てた木と、全段をまとめて当てた木の違いは 1 ファイル
  (`tests/perception/test_b6_invite.py`)の import の文の並び(`from shibuya.llm import …` を 2 つの段で分けたため、分けた文の
  並びが入れ替わる=読む名は同じ)だけ。最初の版では、前の段で空にして残した古い頭(`core`・`manifest`・`engine/bridging`・
  `engine/systems`・`world/processes`)が、後の段で古いディレクトリが空になっても残っていた=後の段で消す形に直した
  (試験 `test_stages_in_order_give_the_same_tree_as_together`)。各段の数: foundation 39 行・world 55・economy 4・act 3・mind 27・
  society 8・interim_bundles 13・runtime 37・experiments 10・validation 6・delete 2。
- 触らなかった道の形の文字列(`untouched`=移すモジュールを指すが許可の一覧の外のもの): 全段で 282(src 219・build 6・tests 39・
  tools 18)。どのモジュールでも道の形を含む定数(許可の一覧の外)は src 311・build 20・tests 148・tools 25。再検収の「凍結に無い道の
  形の定数 472 本(うち 378 本は 3 本の表)」とは数え方が違う(この役は許可の一覧の記号を外し、移すモジュールを指すものを数えた)。
  src の 219 の内訳(ファイルごと): `state_ledger.py` 133(`_EXT` 110・`_SOA` 23=`basis` の記録の文)・`run.py` 19(乱数の
  領域の名の表 17 ほか)・`world/processes/absent.py` 14(宣言の文)・`state_codec.py` 13 と `state_hashes.py` 3(クラスの凍結の名)・
  `removed_switches.py` 5(保留の行)・`agents/state.py` 4・`cli.py` 4・`engine/body/rules.py` 4(manifest に出る文)・`inputs.py` 3・
  `events/log.py` 2(CP12 の宣言と文)・ほか 1 ずつ 15(乱数の用途名 `rail.py`・`environment.py`・`p_notice.py`・
  `rng_audit.K19_RECREATED`・mora の文・`proximity.py` の f 文字列の文・`bridging/scan.py` の `FALLBACK_PATH`=§7 の 1 ほか)。
  build の 6 のうち `catalog_freeze.py` の `CATALOG_JSON_RELPATH` は働く道(§7 の 2)。
- 注意(全段で 6): `from shibuya.engine import body as _body`(`cli.py` 2・試験 2)と `from shibuya.engine import systems`(src 1・
  試験 1)は、包みの頭を空にする段(world・runtime)で、頭の名を属性で読む所が壊れる(§7 の 3)。
- 許可の一覧の中で規則が触らなかったもの: 全段で 8(`tools/bytecheck/tree.py` の理由の文 7・`test_names_frozen.py` の日本語の文 1)。

## 5. 予行(段 4 の最初の小さな段 foundation だけ・結果の物差し)

### 5-1 置き方

1. 写しの木: `git -C <作業木> archive HEAD`(`f5426de`)を〔git の作業木の外の置き場〕へ展開(追跡ファイル 3,333 本)。data は
   作業木の data と同じ先へのつなぎ(cmd を通さない `_winapi.CreateJunction`)。
2. `python tools/pkgmove/cli.py move --stage foundation --tree <写しの木> --out-dir <スクラッチ>`(書かない)の差分が、作業木で
   回した差分と 1 バイトも同じことを確かめてから、`--apply`。当てた行 39(計画の 38 本+移す段 2 で足した `core/paths.py`=91a。
   `removed_switches.py`=224a は保留で断った)・移したファイル 35・新しい頭 9・空にした古い頭 4(`core`・`manifest`・
   `engine/events`・`engine/bridging`=古いディレクトリにファイルが残る)・書き換えたファイル 428。
3. 2 回目の実行(書かない)は、当たっている行 39・書き換えるファイル 0。`import shibuya.cli` ほかが写しの木の
   `foundation/rng.py` を読む。

> 発注の「foundation の 38 本」は計画の数。表の foundation の割らない行は今 40 本(計画の 38+91a+224a)で、224a は保留なので
> 39 本を移した(§7 の 8)。

### 5-2 byte-check

`python tools/bytecheck/cli.py run --base f5426de --src <写しの木>/src --work <短い作業の置き場> --out-dir docs/bench/analysis/pkgmove-346/bytecheck --set all19 --jobs 6`

- **19 構成・37 欄すべて同じ 19・一部を比べていない 0・動いた 0・誤り 0・final が同じ 19 → 終了コード 0**。
  基準の側 208 秒・比べる側 205 秒・全体 413 秒。final `w6_v3_default` = `c8d68704b7b0760d`(60,939 呼)。
- 出力 3 本: [bytecheck/](bytecheck/)(compare と両側の side。道筋は道具の決まりどおり伏せてある)。
- 作業の置き場につなぎが残っていないことを確かめた(0 件)。作業の置き場・写しの木・写しの木の data のつなぎは**消さずに残した**
  (親が外す)。

### 5-3 そのほかの確かめ(写しの木で)

- 表を作る道具 `gen_class_ids.py --check`: 「同じ」(import で確かめた 480・関数の中のクラス 1・新しい鍵 0・落とした鍵 0)=書き換えた
  鍵が全部、移した後の `__module__.__qualname__` と同じで、並びも道具と同じ。
- 凍結の道具 `gen_frozen_names.py --check`: 「同じ」(乱数の領域の名 41・道の形 8・接尾 2・版の ID 69・見出し 9・ほかの名 3・
  6 つの短いランから拾った道の形 74 種)。
- 範囲の試験(tests/c7 を除く): §5-4。

### 5-4 範囲の試験(写しの木)

`pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`(写しの木を cwd に・venv は本体)

- **6,610 passed・81 failed・13 skipped・1 xfailed・errors 0**(計 6,705=作業木の範囲の試験と同じ数)。
- 飛ばした 13 のうち 12 は「git が無い」「commit が無い」(写しの木は git の外=`tests/tools/test_bytecheck.py` 10・
  `test_state_format_10f.py` 1・`test_percept_is_scratch.py` 1。`-rs` で確かめた)。残る 1 は前からの Ruri の重み。移す段の変更で
  飛んだ試験は無い。
- 落ちた 81 のうち 1 は前からの `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`
  (data のつなぎで道の相対化の 1 行=move-346 §7-2)。**残る 80 は段 4 の題**(この段では直さない)。原因で分けた:

| 原因 | 試験(落ちた数) | 段 4 で要ること |
|---|---|---|
| A. 頭の写しの固定のバイト(古い commit の写しを sha256 で固定した試験の材料の import の文を道具が書き換えた) | `tests/perception/facts/test_render_from_percept_bytes.py`(47)・`tests/engine/speech/test_speech_on_reaches_addressee.py`(5=同じ写しを使う)・`tests/economy/cp2/test_cp2_nine_ops_equivalence.py::test_the_copies_are_the_head_blobs`(1) | 写し(`tests/perception/facts/head_renderer_136fdbb.py`・`tests/economy/cp2/head_*_136fdbb.py`)を道具の外に置くか(書き換えないと import が古い置き場を読んで落ちる)、書き換えて固定の sha を張り替えるか、読み込むときに古い名を新しい名へ向けるか=判断(§7 の 10) |
| B. つなぎの台帳の `declared_in`(§7 の 1) | `tests/engine/bridging/test_bridging_ledger.py`(12。foundation で 14 行) | 台帳の扱いの判断の後 |
| C. 凍結の名を今の置き場として使う試験 | `tests/engine/state/test_class_ids.py`(3=CP12 の型の凍結の名 `EXP_ID` を置き場の鍵としても使う・凍結の名で import する)・`tests/engine/test_state_format_10f.py::test_u3_value_class_fields_match_the_class`(1=凍結の名から src の道を作る) | 試験を「凍結の名」と「今の置き場(`class_path`)」に分けて書く(src は変えない) |
| D. 道具が触らない形の道・名 | `tests/engine/time/test_t0_time_consts.py`(1=`shibuya.` の無い点の名 10)・`tests/engine/test_salt_seed_split_10f.py`(1=`core.rng`)・`tests/engine/memory/test_m0_store_schema.py`(1=包みの名の表 `("engine", …, "core")`)・`tests/engine/decision/test_j0_port_schema.py`(1=ディレクトリの道の結合)・`tests/engine/experiment/test_x33_form.py`(1=ディレクトリの中のファイルの名の一覧に `gate.py`)・`tests/engine/multiday/test_md23_w9_window.py`・`test_md23_tool.py`(2=docs の記録の道具 `multiday_md23.py` を読む)・`tests/engine/test_version_bump_10e.py`(1=docs の記録の道具 `rel8b_measure.py` を読む) | 試験の表を直す・記録の道具を読む試験の扱いを決める(記録の道具は書き換えない=move-346 §5)(§7 の 4) |
| E. 試験の中の作った木・差し込むコードの一部だけを道具が書き換えて食い違った | `tests/tools/test_bytecheck.py::test_root_scanner_counts_the_paths_helpers`(1=ファイルの道の鍵は書き換わり、`mkdir("core")` のディレクトリの名は残った)・`tests/engine/experiment/test_x33_apply.py::test_the_entry_check_catches_a_planted_call`(1)・`tests/engine/systems/test_fix_guards.py::test_permit_check_catches_planted_switches`(1) | 試験を直す。道具はディレクトリだけの名を書き換えない(どこへ行くかが 1 つに決まらない)ので、作った木の形を持つ試験は手で直す |

ランの結果は byte-check で 1 バイトも変わっていない(§5-2)ので、80 本はどれも試験の側の道・名・固定の写しの問題で、エンジンの
振る舞いの違いではない(B は台帳の道筋の照合・C は試験の書き方)。

## 6. 試験(`tests/tools/test_pkgmove.py`・19 本)

| 試験 | 確かめること |
|---|---|
| `test_map_toml_is_made_from_the_table_and_is_current` | 327 行・種類の数・保留の一覧・割り先の記録・`map --check` |
| `test_allow_toml_is_current_and_src_tables_exist` | `allow --check`・(b-src) の記号が全部ある・`_ALLOW_*` が全部載る |
| `test_dry_run_writes_nothing` | 書かない実行の前後で木の全ファイルの digest が同じ |
| `test_held_rows_are_refused` | 保留の 7 行の名指しは断る・CLI は終了コード 2・段を選べば保留の行を外す |
| `test_foundation_plan_refuses_the_held_row_and_leaves_it` | foundation で 224a を断り、動かさない |
| `test_apply_refuses_a_main_worktree_and_allows_others` | 一時の git の本体の木(とその中)は断る・`git worktree add` の木と git の外は書ける・`--apply` に `--tree` が要る・このリポの本体の作業木を本体と見分ける(書かずに関数だけ) |
| `test_only_import_statements_and_allowlisted_string_lines_change` | 当てた木で、import の文の行と許可の一覧の記号の文字列の行を除くと、全ファイルが行ごとに同じ(移したファイルは古い道と新しい道)・頭は空 |
| `test_string_constants_outside_the_allowlist_do_not_change` | 許可の一覧の外の全部の文字列とバイト列の定数が、ファイルごとに同じ(道具の守りと別の実装) |
| `test_mora_rule_and_other_untouched_path_shaped_strings_stay_in_the_all_plan` | 全段でも mora の文が変わらず、触らなかった文字列に出る・つなぎの台帳を書かない(398 行)・守りが同じ・保留の 5 行を断る |
| `test_frozen_values_are_kept_by_the_foundation_plan` | 守りが同じ・固定の表の値が同じで鍵が新しい置き場・昇順・`Arbiter` の組が正しい・`CLASS_ID` の宣言と乱数の用途名がそのまま |
| `test_negative_naive_rewrite_of_rng_domain_names_is_stopped` | 負の対照: 字面を全部置き換える書き手を `rng_audit.SAFE_SITES` に差し込むと、names_frozen と凍結の字面の守りが止める |
| `test_negative_naive_rewrite_of_a_class_name_in_a_test_is_stopped` | 負の対照: 試験の中のクラスの凍結の名を書き換えると止める |
| `test_negative_swapping_a_same_qualname_pair_is_stopped` | 負の対照: `Arbiter` の組の値を入れ替えた表(値の集合は同じ)を鍵の守りが止める(再検収 L-a) |
| `test_negative_a_table_that_rewrites_values_is_stopped` | 負の対照: 値まで書き換える表を止める |
| `test_negative_a_map_sending_two_modules_to_one_is_stopped` | 負の対照: 2 つの古いモジュールを同じ行き先へ送る対応表を断る |
| `test_frozen_guard_stops_when_a_frozen_value_is_already_different` | 移す前の木が凍結と違えば何もしない |
| `test_stages_in_order_give_the_same_tree_as_together` | foundation → world を順に当てた木と、まとめて当てた木が同じ・前の段で空にした古い頭(`manifest/__init__.py`)を最後のファイルが出た段で消す・各段で守りが同じ |
| `test_apply_twice_is_the_same` | 2 回当てても同じ(2 回目は当てる行 0・書き換えるファイル 0) |
| `test_applied_tree_has_the_new_places_and_empty_heads` | 39 行・35 本・新しい頭 9 と空にした頭 4・`core/wage_formula.py` は残る |

## 7. 段 4 の前に要る判断(この役は決めていない)

1. **つなぎの台帳の `declared_in`**(move-346 §7-2 の追加の問い): `src/shibuya/…` は 398 行。foundation の段で移すファイルを指す行
   14(active 14)、全段で 105(active 103)。道具は書き換えない(報告の `bridging_ledger_moving` に今の道と新しい道)。`engine/bridging/scan.py`
   の `FALLBACK_PATH`(`src/shibuya/world/processes/registry.py`=F の宣言の `declared_in` を作る道)も同じ問いに入る(world の段で
   動く)。(a) 台帳と `FALLBACK_PATH` の道筋を直す/(b) 台帳は今の道のまま、台帳の試験と走査が対応表を引く。
2. **許可の一覧の外で働く道の文字列**: `build/catalog_freeze.py` の `CATALOG_JSON_RELPATH`(`src/shibuya/manifest/frozen/world_catalog_v0_2.json`=
   構築の側が凍結の JSON を書く先の既定。world の段で JSON が動く)と上の `FALLBACK_PATH`。どちらも計画 §7-5 の「段 3 の道具で直す」
   表に無いので、許可の一覧に足すかを決める。pyproject の `package-data`(`shibuya.manifest`)と import の決まりは計画どおり段 4 の
   終わり(道具は触らない)。
3. **頭を属性で読む所**(§4 の注意 6 件): `cli.py:486`・`:1616` と `tests/engine/body/test_body_manifest.py`・`test_body_reserve.py` の
   `from shibuya.engine import body as …` の後の `….X`(world の段で `engine/body/__init__.py` を空にすると壊れる)、
   `engine/systems/static_check.py:32` と `tests/engine/state/test_move_prep_stage2.py` の `from shibuya.engine import systems`
   (`__name__` だけを読むなら壊れない=確かめていない)。直すなら src の変更(段 4 の前か段 4 の中)。
4. **tests と tools で触らなかった働く文字列**: 点の名を `shibuya.` 無しで持つ試験(`tests/engine/time/test_t0_time_consts.py` の
   `engine.scheduler`・`core.growth` ほか 10・`test_salt_seed_split_10f.py` の `core.rng` ほか)と、クラスの凍結の名と同じ字面の
   置き場の文字列(`tests/engine/experiment/test_x33_apply.py` の `pytestmark` の
   `ignore::shibuya.engine.processes.environment.WeatherWarning`=警告の型の置き場。凍結の名と同じ字面なので触らない)。乱数の
   用途名と見分けられないので道具は触らない。段 4 で落ちる試験として扱う(§5-4 の一覧)か、許可の一覧に足すかを決める。
5. **表を作る道具の書く先**: `docs/bench/analysis/move-346/tools/gen_class_ids.py` の `OUT_PY` は `src/shibuya/engine/class_ids.py` の
   決め打ち。runtime の段で `class_ids.py` が `runtime/state/class_ids.py` へ動くと壊れる(凍結の道具 `gen_frozen_names.py` は木の全部を
   読むので壊れない)。道具を tools へ移す・対応表を引く形にする・記録として残し壊れると書く、のどれか。
6. **byte-check の道具の `ROOT_READERS`**: (b-tests/tools) の一覧に `tools/bytecheck/tree.py::ROOT_READERS` が入る(鍵の道だけ書き換わる)。
   道具は別の役の持ち物なので、段 4 で道具が書き換えてよいか。
7. **古い記録の道具**: move-346 §5 のとおり `docs/bench/analysis/wallbounce-1012/ec21/tools/split_l2_l3.py` は暦の暗黙の再輸出で
   動いている(docs の下=道具は触らない)。全段の dry-run でも変わらない。
8. **foundation の段の本数**: 計画の 38 本に、移す段 2 で足した `core/paths.py`(91a・foundation)を加えて 39 本を移した。224a を
   foundation の段で動かすかは 224a の判断と一緒に決める。
9. **空にする頭の docstring**: 表の「(空にする)」に従い、新しい頭は 0 バイト、古い頭も 0 バイトにする(再輸出の口を残さない)。
   古い頭の docstring(例 `core: SoAレジストリ…`)が消える。docstring を残す形にするなら道具を直す(既定の結果は変わらない見込み=
   foundation の予行では byte-check が同じ)。
10. **古い commit の写しを固定した試験の材料**(§5-4 の A): `tests/perception/facts/head_renderer_136fdbb.py` と
   `tests/economy/cp2/head_goods_136fdbb.py`・`head_ledger_136fdbb.py` は、古い commit のファイルのバイトを sha256 で固定した写しで、
   中に import の文がある。道具は (a) で書き換えるので固定の sha と合わなくなる(予行で 53 本)。書き換えなければ古い置き場を
   import して落ちる。(a) 道具の外に置き、試験の側で読み込むときに古い名を新しい名へ向ける (b) 書き換えて固定の sha を張り替える
   (写しの意味=古い commit のバイト、が変わる) (c) ほか、を決める。

## 8. しなかったこと

- src を変えていない。ファイルを動かしたのは写しの木だけ(予行の結果は作業木に持ち込んでいない)。
- 割らない(割るファイル 24 本は割り先の一覧を対応表に記録しただけ)。保留の 7 行を動かしていない。
- docs・つなぎの台帳・pyproject・CI・カードの外の索引は書き換えていない(カードは道具で作り直した=§9)。
- 予行で落ちた試験を直していない(§5-4 の一覧は段 4 の題)。
- commit・git add・タグ・枝の作成・子のエージェントの起動・STATUS/PENDING/IMPLEMENTED/devlog/CLAUDE.md の書き換えはしていない。
- 封印の層・IMPLEMENTED.md ほか発注で開かないとしたものは開いていない(写しの木は `git archive` の展開=中身は読んでいない)。
  Web は使っていない。pip で何も入れていない。

## 9. 作業木での確かめ

- `git diff --stat -- src` は空(src は 1 バイトも変えていない)。
- 範囲の試験 `pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`(作業木の src・venv は本体):
  **1 failed・6,721 passed・1 skipped・1 xfailed**・35 分 18 秒。落ちた 1 本は前からの
  `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(data のつなぎ)。飛ばした 1 本は前からの
  Ruri の重み。足した試験 19 本の分だけ増えた(move-346 の最後 6,702)。
- `tests/tools/test_pkgmove.py` だけ: 19 passed(およそ 3 分)。
- `lint-imports`: 5 つの決まり全部 KEPT(326 ファイル・1,270 の依存)。予行の写しの木でも KEPT(335 ファイル=新しい頭 9 の分。
  foundation はまだ決まりに入っていない=計画どおり段 4 の終わりに差し替える)。
- `cli.py map --check`・`cli.py allow --check`: どちらも「同じ」。
- カード: `python tools/repo_guide/build.py` で作り直した(カード 123 本=`tools/pkgmove` の 1 本が増えた)。`--check` は最新。
  全体の作り直しなので、`data.md`(data の大きさの揺れ)・`docs.md`・入口の `README.md` と、試験 `test_pkgmove.py` が道で読む src の
  カード(「読む試験(道筋で)」の行)も書き換わった。
- 秘密スキャン `python tools/scan_secrets.py <変えたファイルと足したファイル>`: CLEAN。足したファイルに絶対パス・本名は無い
  (grep で確かめた)。

## 10. 段 3 の続き(全段の予行と、段 4 の下ごしらえ=親の決定 1〜12・検収の指摘 M-1〜M-3・L-1〜L-9)

> 置き場: 作業木 `stage/pkgmove2`(基準 `f5426de`)。予行の写しの木は〔git の作業木の外の置き場〕に段ごとの木
> (`s00_base`〜`s11_interim_bundles`)を作った。親の決定は `parent_decisions_prep4`・検収の裁定は `parent_rulings_review1`・`2`
> (どれもスクラッチ)。試験の側(tests の下=`tests/tools/test_pkgmove.py` と `tests/engine/bridging/` を除く)は別の役が直す。

### 10-1 全段の予行(段ごとに重ねて当てる・interim_bundles は最後=決定 12)

作業木の今の中身(下ごしらえの src を含む)から写しの木を作り、foundation → world → economy → act → mind → society → runtime →
experiments → validation → delete → interim_bundles の順に、段ごとに前の段の木を写して `move --stage <段> --apply` を当てた。
`--apply` は書いた後に木の全モジュールを 1 本ずつ最初から import する確かめを回す(§10-2)。読んだ `shibuya` は、どの段でも
その段の木の `src`(確かめの結果に `shibuya.__file__` を残した)。

| 段 | 当てた行 | 移したファイル | import の文 src/build/tests/tools/docs | 頭を通す | 道の文字列 | 固定の表の鍵 | 台帳の道の表 | 頭から除いた再輸出 | 新しい頭・空にした頭・消した頭 | 保留で断った | 守り(6) | import(モジュール・落ちた・cli --help) | byte-check |
|---|---:|---:|---|---|---:|---:|---:|---|---|---:|---|---|---|
| foundation | 40 | 36 | 382/33/457/22/5 | 3/0/10/0 | 77 | 92 | 36 | engine 9・llm 22・perception 30 | 9・4・0 | 1 | 同じ | 336・0・0 | — |
| world | 55 | 48 | 199/2/398/10/10 | 1/0/3/0 | 118 | 101 | 47 | agents 6・perception 14 | 10・2・6 | 0 | 同じ | 340・0・0 | **0** |
| economy | 4 | 3 | 12/2/26/0/1 | 1/0/0/0 | 6 | 6 | 3 | — | 0・1・1 | 0 | 同じ | 339・0・0 | — |
| act | 3 | 3 | 10/0/18/7/1 | 2/0/5/1 | 6 | 4 | 3 | llm 3 | 2・0・0 | 0 | 同じ | 341・0・0 | **0** |
| mind | 27 | 25 | 88/0/132/2/4 | 0 | 61 | 48 | 25 | — | 7・1・1 | 0 | 同じ | 347・0・0 | — |
| society | 8 | 6 | 19/0/53/0/1 | 0 | 14 | 12 | 6 | — | 3・1・1 | 0 | 同じ | 349・0・0 | — |
| runtime | 37 | 35 | 90/0/226/12/5 | 0 | 76 | 48 | 35 | — | 5・2・0 | 0 | 同じ | 354・0・0 | **0** |
| experiments | 10 | 9 | 24/1/33/2/0 | 0 | 5 | 15 | 9 | — | 3・0・1 | 0 | 同じ | 356・0・0 | — |
| validation | 6 | 6 | 0/0/24/0/0 | 0 | 3 | 10 | 6 | — | 2・0・3 | 0 | 同じ | 355・0・0 | — |
| delete | 2 | 0 | 0 | 0 | 0 | 0 | 0 | — | 0・1・1 | 0 | 同じ | 354・0・0 | — |
| interim_bundles | 13 | 9 | 24/0/44/0/0 | 0 | 15 | 16 | 9 | — | 5・1・3 | 4 | 同じ | 356・0・0 | **0**(全段の木) |

- 移す前(作業木の src=下ごしらえの後)の byte-check も **0**。どれも 19 構成・37 欄すべて同じ 19・動いた 0・誤り 0・final が
  同じ 19(出力 [round2/bytecheck/](round2/bytecheck/)=`wt`・`world`・`act`・`runtime`・`all`)。byte-check を回したのは
  道具を直す前の写しの木(try4)で、最後の道具で作り直した木(try5)の `src` は、全段で try4 と 1 バイトも同じ(sha256 で
  確かめた)=byte-check の結果がそのまま当たる。
- 頭を空にする段(world・runtime)・原因を直した段(world・act)・全段の木で回した。途中のほかの段は回していない。
- 守り(6)= names_frozen・class_ids・shaped_74・ledger_paths・outside_allowlist・import_names(§10-11 で head_all を足して 7)。
- 〔再検収 L-b で直した〕runtime の行は、前は try5 の数(tests の import 225・道 72)のままだった。§10-10 の直し(bridging の試験の
  関数の中の import 1・`guide_permits.py` の点の道 4)の後の数 226・76 に直した。同じ木に段を重ねて当てた予行(§10-11)でも、
  表の数は全段で同じ(守りは 7 つ=`head_all` を足した)。

### 10-2 道具の直し(round2)

| 直し | 原因・根拠 | 試験 |
|---|---|---|
| **頭の再輸出を除く**: この段で空にしない包みの頭の再輸出のうち、出どころが包みの外へ移るものの import の文を頭から除く(頭の中で使う名は除かない・`__all__` は書き換えない) | 予行の try2 で world の段に `world.facts.mock_schedule` が循環の import(agents の頭が読み返す)、act の段に `act.intake.parser`(llm の頭が読み返す)。計画 §7-4「再輸出の口は残さない」 | `test_head_reexports_of_modules_leaving_the_package_are_dropped` |
| **import の確かめ**(`importcheck.py`・`cli.py importcheck`・`--apply` の後に必ず。落ちれば終了コード 3) | 検収 M-1(守りが import できるかを見ていない) | `test_import_check_catches_a_cycle_and_passes_a_clean_tree` |
| **import の文が結ぶ名の守り**(各ファイルの import が結ぶ名=別名を含む、の多重集合が前後で同じ) | 検収 m14(`from shibuya.llm import contract` → `… import actions` に変えても通った) | `test_bound_names_guard_catches_a_changed_binding`・`test_negative_changing_the_names_bound_by_imports_is_stopped_in_a_plan` |
| **本体の作業木の見分けを断る側に**(.git が 1 つも無いときだけ git の外・ディレクトリなら本体・git が失敗したら断る・`GIT_` の環境変数を外して聞く)。`--out-dir` が本体の中なら断る | 検収 M-2・L-6 | `test_main_worktree_check_fails_closed` |
| (d) **つなぎの台帳の道の表**を段ごとに書き足す・守り `ledger_paths` | 親の決定 1(§10-4) | `test_ledger_paths_table_follows_the_moves_and_the_ledger_is_kept` |
| `build/catalog_freeze.py` の `CATALOG_JSON_RELPATH` を (b-src) へ(規則 exact が `src/shibuya/` の頭も読む) | 親の決定 2 | `test_catalog_json_relpath_moves_with_the_json` |
| tests が道で読む docs の記録の道具 11 本を (a) の範囲へ(`RECORD_TOOLS`・tests の走査と同じ一覧) | 親の決定 7 | `test_record_tools_list_matches_the_scan_of_tests`・`test_record_tools_get_only_their_import_statements_rewritten` |
| 包み(ディレクトリ)の名だけの点の文字列は書き換えず注意(`dotted_package`) | 検収 L-7 | `test_package_names_alone_are_not_rewritten_and_relative_imports_are_noted` |
| 相対の import が移すファイルにかかれば注意 | 検収 L-5 | 同上 |
| 74 種の守りは、値の全体が移すファイルの道の定数だけを外して数える(許可の記号の中の文も数える) | 検収 m04(74 種の守りだけが止める場面が無かった) | `test_negative_shaped_74_guard_alone_catches_a_manifest_text` |
| docstring は許可の記号の中でも比べる | 検収 L-9・m29 | `test_negative_rewriting_a_docstring_in_an_allowlisted_symbol_is_stopped`・`test_outside_guard_compares_docstrings_inside_allowlisted_symbols` |
| 識別子 `_TICK_RE`・`ticks` → `_CODE_SPAN_RE`・`spans` | 検収 L-4 | — |
| 負の対照は止めた守りの文(か例外の型)まで確かめる | 検収 L-8・m19 | 負の対照の全部 |
| ほかの突然変異を落とす試験 | m03・m20(固定の表の値と網羅)・m21(版の ID・見出し・乱数の表の鍵)・m18(空にする頭の定義)・m12(空にする頭を通る import の向け直し)・m28(`/` の結合の道が当てた木で在る)・m13(分けた文の注) | `test_negative_class_ids_guard_catches_values_and_coverage`・`test_negative_names_guard_catches_version_ids_headers_and_rng_tables`・`test_negative_an_emptied_head_with_a_definition_is_stopped`・`test_imports_through_an_emptied_head_are_sent_to_the_defining_modules`・`test_every_rewritten_path_chain_points_to_a_file_in_the_applied_tree`・`test_split_import_keeps_the_comments_of_its_names` |
| interim_bundles を飛ばして後の段を当て、最後に当てても守りが通り、まとめて当てた木と同じ | 親の決定 12 | `test_skipping_interim_bundles_then_applying_it_keeps_the_guards` |

- `tools/pkgmove/allow_tests_tools.toml` は L-7 で作り直した(記号 123 → 114・ファイル 67 → 65)。§10-10 の 5(`guide_permits.py`)で
  もう一度作り直した(記号 114 → 118・ファイル 65 → 66)。取り込みのときに親がもう一度作り直す(試験の役の変更を入れた後)。
  `map.toml` は行 125a を足して作り直した(328 行)。
- 試験 `tests/tools/test_pkgmove.py` は 19 本 → 38 本 → 39 本(§10-10 の 1=今の木の状態に依らない形に書き直した)→ 46 本(§10-11)。

### 10-3 src の下ごしらえ(今の置き場のまま通る・既定の結果は変わらない=作業木の src の byte-check 0)

`git diff --stat -- src`(と新しいファイル 1 本):

```
 src/shibuya/cli.py                         | 4 ++--
 src/shibuya/engine/bridging/scan.py        | 6 ++++--
 src/shibuya/engine/systems/static_check.py | 4 ++--
 src/shibuya/llm/parser.py                  | 7 ++++++-
 4 files changed, 14 insertions(+), 7 deletions(-)
 新: src/shibuya/engine/bridging/ledger_paths.py
```

| ファイル | 変えたこと | 理由 |
|---|---|---|
| `src/shibuya/cli.py`(2 か所) | `from shibuya.engine import body as _body` → `from shibuya.engine.body import schedule as _body` | 親の決定 3(包みの頭を属性で読む所=world の段で頭を空にすると壊れる。`arm`・`DEFAULT_ARM`・`set_arm` は schedule の物そのもの) |
| `src/shibuya/engine/systems/static_check.py` | `from shibuya.engine import systems as _SYSTEMS` → `from shibuya.engine.systems import allow as _SYSTEMS_MEMBER`、包みの名は `_SYSTEMS_MEMBER.__name__` の親 | 親の決定 3(包みの頭でなく中のモジュールを直に読む。包みの名の頭の字面は同じ) |
| `src/shibuya/llm/parser.py` | `from shibuya.llm.undefined import map_synonym, target_surface_hint` をモジュールの終わりへ(関数の中でだけ使う) | 決定 11・検収 M-1(§10-5) |
| `src/shibuya/engine/bridging/ledger_paths.py`(新) | 「今の道 → 台帳に書いてある道」の表(空)と `ledger_path`・`current_path` | 親の決定 1(§10-4)。全ファイルの表に行 125a(→ `foundation/decl/ledger_paths.py`)を足した |
| `src/shibuya/engine/bridging/scan.py` | `declared_in_of` は道筋を `ledger_path` で台帳の道にする | 親の決定 1 |

`tests/engine/bridging/test_bridging_ledger.py`(この役の受け持ち): `test_declared_places_exist` は台帳の道を `current_path` で今の道へ
引く。足した試験 2 本: 表が 1 対 1 で台帳のコードの行の道が全部今のファイルに届く・負の対照(ファイルを動かしたふりで表に 1 行
足すと、宣言の同定は台帳の道で作られて台帳の行と同じ鍵になり、そのファイルに宣言を 1 つ足すと台帳の道の鍵で「台帳に行が無い」に
出る=`code_mismatch` の意味が移した後も同じ)。全段の木で `test_bridging_ledger.py` は通る(§10-6)。

作業木(下ごしらえの後・§10-10 の直しの後)の範囲の試験(`tests/c7` を除く・`-m "not gpu and not slow" -n 4 --dist loadfile`):
**6,743 passed・1 failed・1 skipped・1 xfailed**。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`(data のつなぎ)。
`import-linter` は 5 契約とも KEPT。`map --check`・`allow --check` は「同じ」。

### 10-4 つなぎの台帳の対応の表の形(親の決定 1=案 (b))

- 置き場: `src/shibuya/engine/bridging/ledger_paths.py`(段 4 で `foundation/decl/ledger_paths.py`=台帳の読み口と同じ所)。
  何も import しない。読み手は宣言の走査(`scan.declared_in_of`)と試験だけ(ランの中では読まない)。
- 形: `LEDGER_PATHS`=「今の道(リポの根からの道筋)→ 台帳に書いてある道」。段 4 の前は空。道具が段ごとに、移したファイル
  (`.py`・頭を除く)の行を足す(前の段で移したファイルをまた動かせば、古い今の道の行を外して台帳の道を引き継ぐ)。鍵の昇順・
  1 行 1 組。
- 走査の側が台帳の鍵を出す(`declared_in_of` が表を引く)形にした。突き合わせ(`code_mismatch`)は変えない=足りない宣言と
  宙に浮いた行の意味がそのまま。`Declaration.path` は今の道のまま(どこにあるか)。`FALLBACK_PATH` は字面を変えない。
- 道具の守り `ledger_paths`: 表の今の道は木にある・台帳の道が重ならない・台帳のコードの行の道は全部、表を通して今のファイルに届く。
- 全段で足した行は 179(foundation 36 ほか §10-1)。台帳の JSON は 1 バイトも変わらない(道具は docs を書かない)=manifest の
  `bridges_version` は動かない(byte-check 0)。
- 戻し方(次の版上げ=`bridges_version` が動いてよい段): 道具で台帳の道を今の道に書き換え、表を空にする。

### 10-5 M-1 の循環と、親の案 ① との違い

- 連なり(検収役): `cli.py` → `engine/__init__.py` → `engine/commit.py`(`act.intake.parser` を読む)→ `act/intake/parser.py:97`
  (`shibuya.llm.undefined` を読む=llm の頭が走る)→ `llm/__init__.py:206`(parser の名の再輸出)→ parser は途中=ImportError。
- 予行 try3 で、道具が llm の頭から parser の名の再輸出を除いた(=親の案 ① と同じ形が移した後に起きる)木でも、act の段で
  141 モジュールが落ちた。連なりは parser → `llm.undefined` → llm の頭 → 頭が import する `llm.fleet`(`from shibuya.llm import
  ParseResult, parse_two_line` を道具が parser へ向けた)→ parser(定義の前)。**案 ① だけでは直らない**(fleet が parser を読む限り
  循環が残る)。
- 直し: parser が包みの兄弟 `llm.undefined` を読むのをモジュールの終わりへ移した(src の下ごしらえ・関数の中でだけ使う)。移した後は
  循環しても名は定義の後なので通る。今の置き場では読む順が変わるだけ(byte-check 0)。保留(案 ②)は要らなかった。
- 同じ形の走査: 道具は段ごとに全部の頭を見て、出どころが包みの外へ移る再輸出を除く(§10-2)。除いたのは foundation=engine 9・llm 22・
  perception 30、world=agents 6・perception 14、act=llm 3(§10-1)。頭の中で使う名で除かなかったのは llm の頭の `sha256_cbor`
  (再輸出でなく頭が使う import=循環しない)だけ。全段で import の確かめが 0 なので、ほかの頭に同じ形の循環は無い。

### 10-6 全段の木の範囲の試験と、最初に落ちる段(試験の役へ渡す一覧)

- 全段の木(try5 の `s11_interim_bundles`)で範囲の試験(`tests/c7`・`test_pkgmove.py` を除く・`-m "not gpu and not slow" -n 4
  --dist loadfile`)。1 回目は 11 分で INTERNALERROR(`test_x33_apply.py` の `pytestmark` の警告の型=類 F で xdist の worker が落ちた)。
  そのファイルを外して回し直した結果: **122 failed・6,548 passed・13 skipped・1 xfailed・24 errors**(落ちた node id 138)。
  `test_x33_apply.py` は単独で回して落ちる(1 と数えた)。
- 落ちた試験の関数 82 本を、段ごとの木(`s00_base`〜`s11`)でファイルの単位に回し直し、関数ごとに最初に落ちる段を出した。
  段: 移す前 1(前から=`test_ab7_seed1_open_matches_the_parent_report`)・foundation 25・world 34・economy 1・act 1・mind 3・society 1・
  runtime 7・experiments 0・validation 1・delete 0・interim_bundles 8。
- 類(関数の数 / node id の数): A 頭の写しの固定のバイト 10 / 53・B つなぎの台帳の道 6 / 6(うち `tests/engine/bridging/` の 3 本は
  この役が直した=§10-3)・C 凍結の名を置き場として使う 4 / 4・D 道具が触らない形の道と名 25 / 25・E 作った木と差し込むコードの
  一部だけが書き換わる 12 / 15・F 警告の印の型の字面 1 / 1・G 包みの頭を属性で読む 13 / 24・H tools の下の道具 9 / 9
  (うち `tests/tools/test_repo_guide.py` の 2 本は §10-10 の 5 で直した。残る `tests/c8/` の 7 本は §10-9 の 1)・I 読み込みの順に頼る 1 / 1・
  前から 1 / 1。`test_repo_guide.py` の残りの 4 本は、作った木の一部だけが書き換わる E 3 と、範囲をディレクトリの道の頭で選ぶ D 1 に
  分け直した。
- 直した後の全段の木(try6)で `tests/engine/bridging/` と `tests/tools/test_repo_guide.py` を回し直した: bridging は全部通る。
  repo_guide は 5 本落ちる(上の E 3・D 1 と、新しく落ちる `test_missing_ledger_is_reported`=E・runtime の段から。作った木から消す道は
  道具が新しい置き場へ書き換え、`guide_permits.py` も新しい置き場を見るので、出る文は「`src/shibuya/runtime/state/ledger.py が無い`」に
  なり、期待の字面「`state_ledger.py が無い`」と合わない。try5 で通ったのは、古い道を見る `guide_permits.py` と、古い道の無い作った木が
  たまたま合っていたから)。
- 一覧(段・類・試験・id の数): [round2/failing_tests_by_stage.md](round2/failing_tests_by_stage.md)。試験の側の直しは別の役の受け持ち
  (この役は直していない)。
- 段ごとの回し直しは、最後の道具で作り直した写しの木 try6 ではなく try5 の木で回した。try6 の `src` は全段で try5 と 1 バイトも同じ
  (sha256 で確かめた)。違うのは tests・tools の中の、この役が後から直したファイル(`test_pkgmove.py`・`tests/engine/bridging/`・
  `tools/repo_guide/guide_permits.py`・許可の一覧 TOML)だけ。

### 10-7 数え方(検収 L-1〜L-3)

- 道具の `import_statements` は「道具が書き換えた import の文」(空にする頭・消す頭の中の import は数えない=頭は丸ごと空にする。
  頭から除いた再輸出の文は数える)。
- 計画 §7-4 の定義(動くファイル=頭を除くモジュールを読む import の文)で数え直すと、2 回目の作業木(下ごしらえの後)で全段
  **861/38/1,390/54**(ファイル 184/30/351/29)・foundation 381/33/447/22。検収役が 1 回目の木で数えた 857/38/1,388/54 との差は、
  下ごしらえの src 4 文(cli 2・static_check 1・scan 1)と bridging の試験 2 文(`ledger_paths` と `systems.build` を読む文)。
  計画の 855/38/1,378/52 とは 11-09 の後に足したファイルの分だけ違う。〔再検収 L-c で直した: 前は tests を 1,389・bridging の
  試験を 1 文と書いていた。検収役の数え直しは 1,390〕
- 「当てる行」は道具の数。段 3 の報告の時点で全段 204(move 200〔保留 4 を除き、91a・143a を含む〕・empty 2・delete 2)、round2 で
  125a を足して 205(move 201)。計画の 204(move 202+消す 2)とは中身が違う(empty の 2 行=`economy/__init__.py`・
  `world/__init__.py` を計画は数えない・保留の 4 行を計画は数える・91a・125a・143a は計画の後に足した)。

### 10-8 docs の記録の道具(親の決定 7)

- tests が道で読む 11 本は (a) の範囲に入れた(`tools/pkgmove/allow.py` の `RECORD_TOOLS`)。import の文だけを書き換える。
- 〔再検収 L-e〕走査が拾わない読み方が 2 つある: `REC / "tools" / "persona_meter.py"` と `joinpath(*D44_DIR_REL, "d44_controls.py")`
  (道が 1 つの文字列にならない)。どちらの道具も build と割る行の `engine/calendar.py` だけを読むので、今は段 4 で壊れない。
- tests が読まない記録の道具で、段 4 の後に動かなくなるもの(移すモジュールか空にする頭を import する)は 131 本。一覧だけ残す:
  [round2/docs_tools_not_read_by_tests.md](round2/docs_tools_not_read_by_tests.md)。道具は書き換えない。

### 10-9 残る判断(この役は決めていない)

1. **tools の下の、どちらの役の受け持ちでもない道具**(§10-6 の類 H): `tools/c8/sensitivity.py`・`c8lib.py` の包みの名の表
   (`ENGINE_PACKAGES`)とディレクトリの走査。全段の木で `tests/c8/` 7 本が落ちる。誰が直すか。`tools/repo_guide/guide_permits.py` の
   f 文字列の道は、親の裁定 tests1 の 5 でこの役が直した(§10-10 の 5)。
2. **pytest の印の警告の型の字面**(類 F): `tests/engine/experiment/test_x33_apply.py` の
   `pytestmark = … filterwarnings("ignore::shibuya.engine.processes.environment.WeatherWarning")` は凍結のクラスの名と同じ字面なので、
   道具は書き換えない(凍結の名の守り)。world の段で読めなくなり、xdist の worker が落ちて範囲の試験が途中で止まる(予行の 1 回目)。
   試験の側で型を import して渡す形にするか、道具に「警告の印の中の型の道」だけを書き換える例外を足すか。
3. ~~**頭の `__all__`**~~ → 親の裁定 review3 の 2 で決まった(頭から除いた名は `__all__` からも除く)。§10-11 で実装した。
4. **`allow_tests_tools.toml`** は試験の役の変更を入れた後に作り直す(親の取り込みのとき)。L-7 で包みの名だけの文字列を書き換え
   なくしたので、試験の役が字面を `shibuya.` で始まるモジュールの名か `src/shibuya/` からの道にすれば、作り直しで拾われる。
5. **読み込みの順に頼る試験**(類 I): 頭の再輸出を除くと、エンジンを読んでも llm の頭が読まれない(`test_w21_stage8_9.py` の
   「llm_loaded_by_engine True」)。試験の期待を直すか、頭の再輸出を除かない形(循環が残る=§10-5)にするか。
6. **docs の記録の道具 131 本**(§10-8)は段 4 の後に動かない(記録として残す)。

### 10-10 試験の役の報告を受けた直し(親の裁定 `parent_rulings_tests1`)

1. **`tests/tools/test_pkgmove.py` を、今の木の状態に依らない形にした**(foundation を当てた木で 7 本が落ちた件)。
   - 本物の木を写した試験の木で「次に当てる段」(まだ当てる行の残る最初の段)を選び、期待は対応表の行と計画から作る
     (当てた行の数・移したファイル・空にする頭・保留で断る行・台帳の道の表・固定の表の値)。foundation の段に固有の確かめ
     (行 40・同じ `__qualname__` の組・`rng_audit` の道・`/` の結合 3 か所ほか)は、当てる段が foundation のときだけ回す。
   - 負の対照は、作った試験のファイル(凍結のクラスの名・docstring と道・別名の import)か、守りを直に呼ぶ形にした。本物の
     ファイルは `locate`(移した後なら新しい置き場)で引く。
   - 当てる段が無い木(全段を当てた木)では、当てる段の要る試験を理由つきで飛ばす。行 0 の計画でも回る試験(書き換えの道と守り・
     冪等・保留・本体の作業木)と作った木の試験は回る。
   - `allow --check`(許可の一覧 TOML が作り直しと同じ)は、どの段も当たっていない木でだけ比べる(段を当てた木では作り直しが要る)。
   - このリポが git の外の写しの木でも回る(本体の作業木の見分けの試験は一時の git の木で確かめ、リポの git は在るときだけ見る)。
   - 試験は 38 本 → 39 本(結ぶ名の守りを直に呼ぶ試験と計画の中の試験に分け、記録の道具の試験を 2 本に分け、`/` の結合の 2 本を
     1 本に)。
   - 回した結果(どれも cwd をその木にし、読んだ `shibuya` はその木の `src`):

     | 木 | 結果 | 飛ばした理由 |
     |---|---|---|
     | 作業木(どの段も当たっていない) | 39 passed | — |
     | try6 の `s01_foundation`(foundation を当てた木) | 38 passed・1 skipped | 同じ `__qualname__` の組の計画の中の試験(組の片方が動く段が残っていない。鍵の守りは直に呼ぶ試験で確かめる) |
     | try6 の `s11_interim_bundles`(全段を当てた木) | 23 passed・16 skipped | 当てる段が無い 13・foundation の段が無い 1・空にする頭の行が残っていない 1・動かすファイルが残っていない 1 |

     try6 は、この直しの後の作業木から段ごとに作り直した写しの木(§10-1 と同じ作り方。全段で import の確かめ 0・`cli --help` 0)。
     try6 の `src` は全段で try5 と 1 バイトも同じ(byte-check の結果がそのまま当たる)。
2. **M-1 の循環の読み手 `tools/vocab/registry_from_tape.py:49`**: 直していない(直す要が無い)。src の下ごしらえは llm の頭の再輸出を
   手で外していない(外すのは道具の「頭の再輸出を除く」=act の段)。道具はこの文を act の段で
   `from shibuya.llm import UndefinedActionRegistry` と `from shibuya.act.intake.parser import parse_two_line` に分ける(全段の木で確かめた)。
   - 気づいた点: 1 行の文を 2 つに分けると、行の終わりの注(`# noqa: E402`)は後ろの文にだけ残る。CI は ruff を回さないので
     結果は変わらない。
   - `docs/bench/analysis/wallbounce-1003/r86/ab7_sample.py`・`ab7_surface_counts.py` は tests が読まない記録の道具(§10-8 の 131 本)で、
     act の段の後に動かなくなる(記録として残す)。
3. **静的の検査がたどる補助の範囲**(guard・overrides・static_check が系の包みから出ていく件): **変わらない**。移す前の作業木と全段の木で
   `analyze_spec` を 36 系に回し、たどる関数(80 本)・箱の参照・scratch・tally・resolve の呼び出しを比べた。モジュールの改名を当てると
   全部同じ([round2/static_range_base.json](round2/static_range_base.json)・[round2/static_range_all.json](round2/static_range_all.json))。
   たどる関数は系の包みの 15 本のモジュールと各層の `layer`(calendar2・calendar3・contact・duties・experiment)にあり、
   guard・overrides・static_check には 1 本も無い。`_SYSTEMS_PREFIX` は全段の木で `shibuya.runtime.systems.`。
4. **試験が読む記録の道具の数え**: この役の一覧は 11 本(`RECORD_TOOLS`=tests が道の文字列で読む docs の `.py`)。試験の役の 14 本との
   差の 3 本(`move-346/tools/gen_class_ids.py`・`gen_frozen_names.py`・`s2-rules-1101/tools/add_bridges_s2rules.py`)は、tests の docstring・
   注・失敗の文に名が出るだけで、tests は読まない。3 本とも `shibuya` を import しない=書き換える import の文は無い(道の文字列は
   持つので段 4 の後は古い置き場を指す=§10-8 と同じ扱い)。
   - 書き換えの数: 試験の役の 16・3・4・8 は、全段を 1 回で当てる計画の書き換え(`Edit`)の数と同じ(1 つの文の包みの名と名を別々に
     数える)。行で数えると 16・2・2・7(段を順に当てた全段の木と作業木の差)。全段の木で 11 本の import は全部、道具の索引で解決する。
5. **`tools/repo_guide/guide_permits.py:27-31`**: 道を `_src_file("shibuya.engine.state_ledger")` の形(モジュールの名 → `src/….py`)で作る
   ようにした(f 文字列をやめた)。値は前と 1 文字も同じ(5 本とも比べた)=カードは変わらない。モジュールの名は `shibuya.` で始まる
   点の道なので、許可の一覧の作り直しで拾われ(記号 4=`RESOLVE_FILE` は保留の `engine/resolve.py` なので拾われない)、段ごとに
   新しい置き場の名へ書き換わる。`tools/pkgmove/allow_tests_tools.toml` を作り直した(記号 114 → 118・ファイル 65 → 66)。
   - `build.py --check` は作業木で「カードが古い 13 本」と未追跡 17 本を出す。どれも round2 の道具・試験・src の変更の分
     (guide_permits の分は無い)。CI は `build.py --check` を回すので、取り込みの commit ごとにカードの作り直しが要る(親)。
   - 全段の木(try6)で `tests/tools/test_repo_guide.py`: 実物の木を読む `test_real_ledger_rows_match_import`・
     `test_real_write_permits_match_import` が通るようになった(try5 では runtime の段から落ちた)。残る 5 本は試験の側(§10-6)。
     そのうち `test_missing_ledger_is_reported` は、この直しで新しく落ちる(期待の字面が古いファイルの名=§10-6)。
6. **`tests/_places.py` が `tools/pkgmove/map.toml` を読む件**: この回は対応表の置き場も形(行の鍵の名)も変えていない
   (変えたのは round2 の行 125a の追加だけ=前の報告のとおり)。`_places` の新しい確かめ(src の `.py` は表の `old` か move の `new` に
   必ず在る・無くてよいのは 0 バイトの `__init__.py` だけ)を、作業木と try6 の全段の木(`s00`〜`s11`)で同じ規則で数えた: 表に無い
   ファイルはどの木でも 0。この役が src に足したファイルは `engine/bridging/ledger_paths.py`(行 125a)だけで、道具が作る新しい頭は
   全部 0 バイト。
7. `allow_tests_tools.toml` は 5 のために作業木で作り直した(取り込みのときに親がもう一度作り直す)。TOML は (i) に、
   `guide_permits.py` は (ii) に入るので、(i) だけを入れた commit では TOML に `guide_permits.py` の記号 4 つが先に載る
   (その commit では `allow --check` が「違う」と出る。`test_pkgmove.py` の `allow --check` も、どの段も当たっていない木では比べる)。
   (ii) を入れた後に作り直せば合う。

### 10-11 再検収(受入・H 0・M 0・L 8)の後の直し(親の裁定 `parent_rulings_review3`)

| 直し | 中身 | 試験 |
|---|---|---|
| **L-a 古い包みのディレクトリが `__pycache__` だけを持って残る**(同じ木に段を重ねて当てると出る) | `--apply` の終わりに、`src/shibuya` の下の「`__pycache__` のほかに何も無いディレクトリ」を `__pycache__` ごと消す(`move.prune_cache_only_dirs`。つなぎ=シンボリックリンク・junction と `src/shibuya` そのものは消さない)。消したディレクトリは標準出力と import の確かめの JSON(`removed_cache_only_dirs`)に出す。import の確かめは、対応表の頭の行のうち木に頭がもう無い包み(`move.gone_packages`)が `importlib.util.find_spec` で `None` になることも見る(名前空間の包みとして import できれば落ちる) | `test_cache_only_dirs_are_pruned_and_namespace_leftovers_are_caught`(小さな木)・`test_stacked_apply_prunes_old_package_dirs_and_returns_3_when_imports_fail`(全部のディレクトリに古い `__pycache__` を置いた写しの木へ残る最初の 2 段を当てる。古い包みの名は `find_spec` で `None`) |
| **頭の `__all__`**(§10-9 の 3・親の裁定) | 頭から除いた再輸出の名は、その頭の `__all__` からも除く=許可の一覧の (e)(`imports.all_drops`。1 行 1 要素の行を行ごと除き、行の終わりの注は注の行として残す。ほかの形は除かずに注意)。守り `head_all` を足した(7 つ目): 空にしない頭の `__all__` の名は全部その頭で結ばれている(定義・代入・import・子のモジュール)・(e) で書き換えた頭は「前の `__all__` から除いた名を抜いたもの」と同じ(並びも)。移す前の木で結ばれない名があれば止める(前の道具で当てた木) | `test_head_all_drops_only_the_dropped_reexport_names`(別の実装で確かめる)・`test_all_drops_keeps_comments_and_refuses_other_forms`・`test_negative_head_all_guards_stop_a_writer_that_keeps_or_overdrops_names`(除かない書き手=「結ばれない名」・余分に除く書き手=「除いた再輸出の名のほかで変わった」) |
| L-d n05 | 読む順でだけ循環が出る小さな木(`a_pkg` を先に読めば `z_moved` も読めるが、`z_moved` を最初に読むと落ちる) | `test_import_check_reimports_every_module_from_scratch` |
| L-d n06 | 木の `src/shibuya` に頭が無い木(子は別の場所の `shibuya` を読む)=落ちたと数える | `test_import_check_fails_when_it_reads_a_shibuya_outside_the_tree` |
| L-d n07 | 読めないモジュールを足した木へ `move --apply` → 終了コード 3 | `test_stacked_apply_…`(上と同じ試験) |
| L-d n11 | `.git` がファイルの作業木(linked)で、呼び手の `GIT_DIR` が本体の `.git` を指していても本体と取り違えない | `test_main_worktree_check_fails_closed` に足した |
| L-f | 空にする頭に、関数とクラスのほか、import・docstring・`__all__` のほかの文(代入・`if`・`try` ほか)があれば止める | `test_negative_an_emptied_head_with_a_definition_is_stopped` に足した(代入) |
| L-g | `importcheck --out` の置き場が本体の作業木の中なら断る(`--out-dir` と同じ) | `test_main_worktree_check_fails_closed` に足した |
| L-b・L-c・L-e(記録) | §10-1 の runtime の行(226・76)・§10-7 の tests 1,390(bridging の試験の文は 2 つ)・§10-8 に走査が拾わない 2 つの形 | — |

頭の `__all__` から除いた名: foundation=engine 9・llm 22・perception 30、world=agents 6・perception 14、act=llm 3(計 84=頭から除いた
再輸出の名と同じ数)。全段の後に残る中身のある頭は llm だけで、`__all__` は 53 → 28(25 を除いた=再検収の「結ばれない 25」)。

**同じ木に段を重ねて当てた予行(try7)**: 作業木の写しの木 1 本に、foundation → world → economy → act → mind → society → runtime →
experiments → validation → delete → interim_bundles を順に `--apply` した(段ごとに写さない=段 4 の本物の当て方。各段の
import の確かめが作った `__pycache__` が次の段に残る)。

- どの段も終了コード 0・守り 7 つとも「同じ」・import の確かめの落ち 0・`cli --help` 0・読んだ `shibuya` はその木の `src`。
- 当てた行・移したファイル・import の文・道の文字列・固定の表の鍵・台帳の道の表・除いた再輸出・頭の数は、§10-1 の表(runtime の
  行は直した後)と全段で同じ。
- 消した古いディレクトリ(`__pycache__` だけ): world 6・economy 1・mind 1・society 1・experiments 1・validation 3・delete 1・
  interim_bundles 3(計 17=再検収が見つけた 17)。無くなった包みは全段の後で 17 で、どれも `find_spec` が `None`。最後の木に
  `__pycache__` だけのディレクトリは 0。
- try6(段ごとに写した木)との違いは、src では頭の `__init__.py` だけ(foundation の後=engine・llm・perception、全段の後=llm。
  `__all__` の行)。

**byte-check**(`--base f5426de --set all19 --jobs 6`): foundation の木・全段の木とも **19 構成・37 欄すべて同じ 19・動いた 0・
誤り 0・final が同じ 19・終了コード 0**(出力 [round2/bytecheck/](round2/bytecheck/) の `found3b`・`all3`)。全段の木は try7 の木
そのもの(段を重ねて当てた木)。foundation の木は、try7 の foundation の後の src の写しが src だけで byte-check に要る docs と
data を持たなかった(1 回目は終了コード 2=記録には残していない)ので、同じ道具で foundation だけを当てた写しの木で回した
(その src は try7 の foundation の後の src と同じ=`diff -r` で確かめた)。

**作業木での試験**: `tests/tools/test_pkgmove.py` 46 passed(39 → 46 本)・`tests/engine/bridging/` 51 passed。移した木での `test_pkgmove.py`: foundation の木(上の byte-check と同じ木)45 passed・1 skipped(同じ `__qualname__` の組の計画の中の試験)・全段の木(try7)28 passed・18 skipped(当てる段が無い 15・foundation の段が無い 1・空にする頭の行が残っていない 1・動かすファイルが残っていない 1)。

**突然変異**(写しの木で 1 本ずつ・その変異を落とすはずの試験だけ・元に戻した): 9 本とも落ちる。n05(1 つ読むたびに `sys.modules` から外すのをやめる)・n06(木の src でない `shibuya` を読んだら落とす、を殺す)・n07(`--apply` の後の import の確かめの落ちを終了コード 0 に)・n11(`GIT_` の環境変数を外さない)・L-g(`importcheck --out` の置き場を断らない)・L-a の 2 本(`__pycache__` だけのディレクトリを消さない・無くなった包みの名前空間を見ない)・L-f(ほかの文を見ない)・`head_all` の守りを外す。

- 〔取り込みの木での直し・親の裁定〕`test_pkgmove.py` は本物の tests の字面と本数を前提にしない: `/` の結合の 3 本と `test_cp2_event_links.py`・頭を通す import の `test_manifest_roundtrip.py`・記録の道具が 1 本以上書き換わる、の 3 つの前提を外し、
  m28・m12 を落とす力は作った見本の木の試験 2 本(`…_in_a_sample`)で持つ(試験は 48 本)。
