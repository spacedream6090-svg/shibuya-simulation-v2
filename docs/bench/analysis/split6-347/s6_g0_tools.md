# 割る段 6 の S6-G0: 割る道具の拡張 E7・E8・E5-b・E9(src は変えない)

> 発注: scratchpad の `r8/order_stage6_g0_tools.md`。計画: `r8/plan_stage6.md` §5-2・§8、取り直し `r8/plan_stage6_retake.md` §5・§7・§11。
> 裁定: `r8/rulings_stage6.md`(Q1・Q8・追記・R2)・`r8/rulings_stage5b_g3.md`。前の記録: [split5b-347](../split5b-347/README.md) §16・§17-4。
> 作業の木: git の作業木・枝 `work/split6-g0-347`。実装と §1〜§8 の確かめは頭 `bde381e` の木で行い、検収の後に親が土台を本体の頭
> `8997e2d`(S6-A と台帳が入った後=src に本物の `LEDGER_PATHS_SPLIT`〔空〕が在る)へ載せ直した(変えた 8 本は 1 バイトも同じ)。
> §9「検収の後の直し」は `8997e2d` の木で行った。変えたのは `tools/pkgmove/`(`split.py`・`strings.py`・`ledgerpaths.py`・
> `cli.py`・`table.py` の読みの部分・`README.md`)と `tests/tools/test_pkgmove.py` と本書だけ。src・全ファイルの表・`map.toml`・
> `contracts.toml`・`pyproject.toml`・`table.SPLIT_ORDER`・カードは変えていない(`git status --porcelain -- src` は空)。本物の木に
> `--apply` は回していない。同じ置き場の `README.md` は S6-A の役が別の木で作る(本書はそれと別のファイル)。
> 重いもの(木をまるごと写す試験を含む `test_pkgmove`・slow・書かない実行・履歴の当て直し・`contracts --probe`)は合図のファイルを
> 取ってから 1 本ずつ回した。台本と出力は scratchpad の `r8/s6g0/`(`dry6g0.py`・`dry6g0_out.txt`・`replay_detail.py`・
> `replay_detail_out.txt`・`real_cli.txt`)。

## 1. 拡張の形と守り

使い方は [tools/pkgmove/README.md](../../../../tools/pkgmove/README.md) の「割る段 6 の S6-G0」の節。

### 1-1. E7 台帳の道の前向きの表(裁定 Q1 の (ii))

| 所 | 形 |
|---|---|
| `ledgerpaths.py` | `MAIN_TABLE="LEDGER_PATHS"`・`SPLIT_TABLE="LEDGER_PATHS_SPLIT"`。`split_table_of(text)`(表が無ければ `None`)・`ledger_of(main, split, path)`(1 対 1 → 前向き → そのまま)・`updated(old, moves, *, unique_values=True)`(前向きの表は値の重なりを許す)・`rewrite(text, moves, split_add=None)`(前向きの表に載った鍵は移しでも前向きの表のまま付いて行く・前向きの表は中身が変わったときだけ書き直す・表が無い木に行を足そうとすれば「前向きの表が無い」で止める・同じ今の道を 2 つの表に置かない)・`check(table, exists, ledger_text, split=None)`(前向きの表の今の道は木に在る・2 つの表の両方に同じ今の道が無い・台帳の行の逆向きは 1 対 1 の表だけ) |
| `split.py` | `ledger_split_rows(plan, lp_text)`=宣言が 1 つ以上入る 2 つ目以降の**新しい**割り先 → 元のファイルの台帳の道。`make_split_plan` の台帳の道の表の段で `LPT.rewrite(lp, moves, split_add)`(主な割り先が元のファイルの行は `moves` が空=前向きの表だけ書く)。報告 `ledger_paths_split`。守り「許可の一覧の外」の表の記号に `LEDGER_PATHS_SPLIT` を足した |
| 守り ④ | 台帳の道(1 対 1 → 前向き → そのまま)で数える宣言の多重集合が割る前と後で同じ(前と同じ厳しさ)。加えて: 2 つ目以降の新しい割り先は「宣言がある ⇔ 前向きの表に行」・既に在る割り先へ宣言が入れば止める・表のファイルがあれば `LPT.check`(台帳の JSON を渡せば行が届くかも)・前向きの表の今の道は宣言を 1 つ以上持つ(条件 ③) |

- 前向きの表の字面は `LEDGER_PATHS` と同じ形(`Final[Mapping[str, str]] = MappingProxyType({` … `})`・鍵の昇順・1 行 1 組・空なら `{` の次の行が `}`)。
- 段 4 の `move.py` は変えていない(変えてよいファイルの外)。段 4 の道具で前向きの表の鍵を動かす形は、`move.py` の守り「許可の一覧の外」が `LEDGER_PATHS_SPLIT` の記号を許可に持たないので止まる側。`move.py` の `ledgerpaths.check` の呼び出しは 1 対 1 の表だけ(前と同じ)。

### 1-2. E8 道の文字列の割り先の宣言(裁定 Q8)

| 所 | 形 |
|---|---|
| `split.py` | `PathDest(old, file, symbol, dest)`・`SPLIT_PATH_DESTS: tuple[PathDest, ...] = ()`(段 6 の 2 行は次の発注で載せる)。当てる前の守り `_path_decl_errors`・使われなかった宣言は当てた後に止める。報告 `path_declared`。`PathRules` に `declared`((ファイル, 記号) → 割り先)と `nameless_manual`(割り先が 2 つ以上の行の割るファイル)を渡す |
| `strings.py` | `split_path_dest(rules, path, sym, rel, sib)`=宣言 → 組の名 → 割り先が 1 つなら主な割り先。斜線の道の全体(`rewrite_file_strings`)・文の中の斜線の道(`_plain_reps`)・`/` の連鎖(`chain_edits`)・名の無い点の道(`split_nameless` の `declared`)に当てる。手で直す種類 `split_nameless`・`slash_nameless`・`chain_nameless`。使った宣言は `StrStats.declared_used` |
| 守り | 止める文は「道の文字列の割り先の宣言の守り:」の後に: ファイルが木に無い・記号がファイルに無い・割り先がその行の割り先でない・記号が範囲の外(`STRING_EXCLUDE`・`SPLIT_EXCLUDE_PATHS`・道具の自分)・同じ記号に 2 つ・使われなかった。宣言はその割る行でだけ使う |

- 宣言も名の手がかりも無い割るファイルの道は、割り先が 2 つ以上の行(`plan.dests` が 2 つ以上)では手で直す一覧へ。割り先が 1 つの行は前と同じに主な割り先へ。宣言と組の名が食い違えば手で直す一覧(宣言は引いた扱い)。記録の文(ASCII の外の字を含む文)の中は前と同じに書き換えず一覧にも出さない。名の無い点の道は `-m` の入口・転送の名が先、宣言は次。
- 宣言の口(`declared`・`used`)は、宣言のある記号でだけ `rewrite_value` に渡す(無ければ前と同じ呼び方)。段 4 の負の対照 3 本が `rewrite_value` を 3 引数の関数に差し替えるため(1 回目の全体の試験で落ちた=§2-3)。
- あわせて直した見落とし(`split._scan_strings`): tests と tools の文字列を選ぶとき、`/` の連鎖の記号は、ほかの記号に斜線・点の道の当たりがあるファイルでも拾う。前は当たりの無いファイルでだけ連鎖を見たので、連鎖が書き換えも一覧も無く残った(段 6 では §5 の 6 か所)。
- `split.STRING_EXCLUDE` に `("tests/tools/test_repo_guide.py", "LAYER_SRC")`(裁定 R2)。先に確かめたこと: `LAYER_SRC` は合成の木(tmp の `synth`)の `engine/layer.py` に書くだけの字面(試験の中の読みは 1 か所)で、`tools/repo_guide/` は AST で読む(`subprocess` は git だけ・`import_module`・`exec` は無い)。字面の `shibuya.engine.resolve` は合成の木の見本の resolve に解け、本物の src を読まない。

### 1-3. E5-b 差し替えの届く先の守り(追記・取り直し §11)

- `split.patch_reach(plan) -> list[str]`。`guards` の import の循環の後・決まりの前で呼ぶ。守りの値 `plan.guards["patch_reach"]`・止める文は「差し替えの届く先の守り:」。報告 `patch_checked`・`patch_unseen`・`patch_load_time`(`split --through` の行と要約にも)。
- 集める形(`_collect_patches`): `<何か>.setattr`/`.delattr`/`.object(<別名>, "名", …)`・組み込みの `setattr`/`delattr`・文字列の的(`.setattr("pkg.mod.名", …)`・`.delattr("pkg.mod.名")`・`patch("pkg.mod.名")`)・属性への代入と `del`・コードの文字列の中の同じ形(組は「記号(コードの文字列)」)。別名の結びは記号(関数)の中の import が先・無ければ頂上。範囲: src・tests(`tests/c7` を除く)・tools・docs の記録の道具(道具の自分と元のファイルを除く)。組=同じ記号(関数・メソッド・頂上の代入)。
- 届かせる割り先: (a) 元のファイルで関数の本体が素の名で読む頂上の関数(メソッドはクラス)の割り先(`_global_reads`=引数・代入・内包の変数に覆われた読みを除く) (b) src のほかのモジュールが呼ぶ時に別名の属性か `getattr`/`hasattr` で読めば名を定義する割り先(`_call_time_ids`) (c) (a)(b) が空なら名を結ぶ割り先(定義か再輸出)。
- 割った後の字面で同じ組の差し替えが向く割り先が集合と同じか。届かない割り先・集合の外の割り先は止める(名・差し替えの行・届かない割り先・呼ぶ時に読む所)。
- 読み込みの時だけの読み(デコレータ・既定の引数・注釈〔`from __future__ import annotations` が無いとき〕・クラスの親と本体・頂上の代入と表・src のほかのモジュールの頂上の別名の読み)は (a)(b) に数えず `patch_load_time`。
- 見られなかった形は止めずに `patch_unseen`: 名が字面でない・的の文字列を組み立てる(f 文字列・`+`)・別名が 2 つのモジュールに結ばれる・`vars`/`__dict__` を通す・割った後も別名が元のモジュールを指す(手で直す一覧の別名)・範囲の外(`SPLIT_EXCLUDE_PATHS`)・名が元のファイルで結ばれていない。`別名.物 = …`(物の属性の書き換え)はモジュールの差し替えでないので数えない。
- 〔検収の後に直した=§9〕主な割り先が元のファイルの行は元のモジュールを主な割り先として確かめる・割り先でないモジュールを指したままの差し替えは、別名が手で直す一覧に在るときだけ「見られなかった」(無ければ止める)・`strict` の当ては「見られなかった」が 1 つでも在れば断る。

### 1-4. E9 CLI の書かない道を見本の木で確かめる口(追記)

- `cli.py split` に `--map <対応表 TOML>`・`--contracts <決まり TOML>`。`--map` のときは順を表の割る行の `split_order` から読む(`table.split_order_of`=番号が 1 から続かないか、頭の `split_order` と食い違えば「断った: 対応表を読めない」で終了 2)。`split_state`・`next_split`・`make_split_plan` に `order`(既定 `None`=`table.SPLIT_ORDER`)。
- 渡さないときの読み先と順は前と同じ(`map.toml`・`table.SPLIT_ORDER`・`contracts.toml`)。要約の JSON と `--through` の行には E7・E8・E5-b の欄が増えた(`ledger_paths_split`・`path_declared`・`patch_checked`・`patch_unseen`・`patch_load_time`)。`--through` の標準出力の行は、その欄が空でないときだけ数を足す。

## 2. 試験

### 2-1. 数の前後(`tests/tools/test_pkgmove.py`・`-m "not slow"`・`-n` なし)

| | passed | skipped | 落ちた |
|---|---:|---:|---:|
| 前(頭 `bde381e`) | 112 | 21 | 0 |
| 後 | 145 | 21 | 0 |

- 増えた 33 は足した試験(§2-2)。飛ぶ 21 は前と同じ顔ぶれ(段 4 の当て済みの木 17・空にする頭/動かすファイル/凍結の JSON が残っていない木 3・割る段の終わりの木 1)。
- slow: 前からの `test_split_5a_5b_in_memory_keeps_the_import_rules_to_the_end` passed(当てる本 0)・足した `test_patch_reach_replays_the_22nd_split_on_the_g3_base_in_history` passed(57 秒)。
- `tests/tools` の残り(`test_pkgmove.py` を除く・`-n 2`・`-m "not slow and not gpu"`): 642 passed。
- 本物の木(作業の木): `split --next`・`split --through all` とも「割る段は全部当たっている」・`--out-dir` にファイル 0・`map --check` 同じ・`contracts --stage delete --tree . --check --probe` 同じ(契約 2+9・例外 20 辺・延べ 26 行・全部効く=5b の終わりと同じ)。

### 2-2. 足した試験(関数 22・場合 34。slow 1)

| 拡張 | 試験 |
|---|---|
| E7 | `test_ledger_paths_forward_table_reads_writes_and_follows_moves`・`test_ledger_paths_check_sees_the_forward_table`・`test_split_writes_a_forward_ledger_row_for_a_second_destination_with_a_declaration`・`test_split_writes_a_forward_ledger_row_when_the_main_destination_is_the_source_file`・`test_negative_forward_ledger_rows_keep_guard_4_as_strict_as_before`(4 場合)・`test_negative_a_tree_without_the_forward_table_stops_when_a_row_is_needed` |
| E8・R2 | `test_split_path_declarations_point_nameless_paths_to_the_declared_dest`・`test_negative_nameless_paths_without_a_declaration_are_listed_for_hand_fixing`・`test_split_path_declarations_apply_to_the_src_tables`・`test_negative_path_declaration_guards_each_stop`(6 場合)・`test_path_declarations_of_other_rows_are_not_used`・`test_path_declarations_name_files_and_symbols_that_exist_in_the_tree`・`test_string_exclude_has_the_fake_tree_sample_of_the_repo_guide_test` |
| E5-b | `test_patch_reach_passes_when_patches_point_to_every_reading_destination`・`test_negative_patch_reach_stops_patches_that_miss_a_reader`(5 場合)・`test_patch_reach_lists_load_time_reads_and_passes_string_and_code_targets_that_reach`・`test_patch_reach_lists_patches_it_cannot_see`・`test_negative_patch_reach_guard_is_what_stops`・`test_patch_reach_replays_the_22nd_split_on_the_g3_base_in_history`(slow) |
| E9 | `test_split_order_of_reads_the_split_rows_of_a_map`・`test_split_cli_dry_run_writes_nothing_in_a_sample_tree`・`test_negative_split_cli_dry_run_returns_nonzero_when_a_guard_stops_in_a_sample_tree` |

- E9 の見本の木: 割る行 2 本(5a の見本 `pk/old.py`・`pk/two.py`=順 1・2)・既に在る割り先・読み手・台帳の道の表(1 対 1 と前向き)・つなぎの宣言の走査は本物の `validation/static/bridging_scan.py` と `foundation/paths.py` の写し(CLI は木の src から読むため)・乱数の領域の表 3 つ・固定の表と凍結の JSON は見本の木から作る・決まりは段 s1 の古い決まり 1 つ(見本の全部の包みを元の側に持つ)。見本の木は全部のバイトの指紋が前後で同じで、`__pycache__` も作らない。
- 履歴の試験は git の外か commit の無い所(浅い写し)で飛ぶ。`tests/c7` の中身は読まない(名前の一覧から外す)。

### 2-3. 期待を書き換えた試験(3 本・確かめる中身と期待の字面は変えていない)

E8 で、割り先が 2 つの見本の行の名の手がかりの無い斜線の道は手で直す一覧へ出る(前は黙って主な割り先へ)。次の 3 本はその道を主な割り先へ書き換わる見本として使っていたので、`SPLIT_PATH_DESTS` に主な割り先への宣言を置く行を足した(行を足しただけ・削った行 0)。

| 試験 | 足したもの | わけ |
|---|---|---|
| `test_split_leaves_the_bytecheck_tool_and_its_test_alone` | 範囲の中の `tools/other.py::P` への宣言(範囲の外のファイルへの宣言は守りが止める)・負の対照では 3 本への宣言 | 範囲の外(E4)の確かめのまま |
| `test_split_keeps_the_table_keys_of_the_places_helpers` | `C` への宣言・負の対照(鍵の規則を外す)では `A`・`C` への宣言 | 規則を外すと鍵が主な割り先へ書き換わる形を前と同じに確かめる(宣言が無いと E8 が先に手で直す一覧へ出す) |
| `test_split_lists_a_code_import_inside_an_f_string_for_hand_fixing` | `build` への宣言 | 手で直す一覧の行が f 文字列の 1 行だけ、のまま |

- 1 回目の全体の試験で、段 4 の負の対照 3 本(`test_negative_naive_rewrite_of_rng_domain_names_is_stopped`・`test_negative_naive_rewrite_of_a_class_name_in_a_test_is_stopped`・`test_negative_shaped_74_guard_alone_catches_a_manifest_text`)が `TypeError` で落ちた(`rewrite_value` を 3 引数の関数に差し替える)。試験は変えず、道具の側で宣言の口を宣言のある記号でだけ渡す形に直した(§1-2)。2 回目に全部通った。

## 3. 負の対照の一覧

| 拡張 | 植えたもの | 止めた所 |
|---|---|---|
| E7 | 2 つ目以降の割り先の宣言を 1 つ消す(組み立ての後) | ④「宣言が元と割り先とで違う」 |
| E7 | 前向きの表の行を 1 つ落とす(`ledger_split_rows` を空に) | ④「前向きの表に行が無い」と「元と違う」 |
| E7 | 宣言の無い割り先(`nw/plain.py`)の行を足す | ④「宣言の無い 2 つ目以降の割り先 … の行が前向きの表に在る」と「前向きの表の今の道 … に宣言が無い」 |
| E7 | 既に在る割り先(`vocab/base.py`)へ宣言を入れる | ④「既に在る割り先 … につなぎの台帳の宣言が入る」と「元と違う」 |
| E7 | 前向きの表の無い木で行が要る/表のファイルが無い木 | 「前向きの表が無い」/④(前と同じ) |
| E7 | 表の単体: 表が無い木に足す・在る鍵へ足す・2 つの表に同じ今の道・1 対 1 の表の値の重なり・木に無い今の道 | `LedgerPathsError`・`check` の文 |
| E8 | 宣言を外す | 4 形(斜線の全体・文の中・連鎖・名の無い点)が手で直す一覧・`strict` は断る |
| E8 | 宣言と組の名が食い違う | 手で直す一覧 |
| E8 | ファイルが無い・記号が無い・割り先が違う・範囲の外・同じ記号に 2 つ・使われない | 守り 6 つが 1 つずつ |
| E8 | 宣言の腐り(在りもしないファイル・記号) | `_stale_path_dests` |
| E5-b | 片方の割り先だけ(setattr・属性への代入) | 「届かない割り先 ['pk2/b.py']」と読む所 `pk/mod.py:18 h→pk2/b.py` |
| E5-b | 集合の外(読み込みの時にだけ読む名を b へ差し替える) | 「届かない割り先 ['pk2/a.py']」「集合の外の割り先 ['pk2/b.py']」・読む所 `src/shibuya/use.py:5(別名の属性)` |
| E5-b | 文字列の的・コードの文字列の中で片方だけ | 「届かない割り先」 |
| E5-b | 守りを外す(`patch_reach` を空に) | 止まらずに当たる(守りが止めていることの確かめ) |
| E5-b(履歴) | 助けの main の側の 2 行を外す | `Ledger`・`_HouseholdWalletLedger` が「届かない割り先 ['interfaces/cli/main.py']」 |
| E5-b(履歴) | 別名の割り先の宣言(E5-a)を外す | `strict` は手で直す一覧で断る・書かない実行では宣言の在った別名の差し替えが「見られなかった」に出る(確かめた欄に出ない) |
| E9 | 順の違う行の名指し・互いの名を読む割り先・割る順が続かない表 | 終了 2(木は 1 本も変わらない) |

## 4. 本物の履歴での確かめ(5b の G3 の土台 `e6d221c` で 22 本目 `cli.py` を当て直す・メモリの中)

- (i) そのまま(`strict`): 守り 14 個とも「同じ」(転送・`patch_reach`・契約を含む)・手で直す 0・別名の割り先の宣言 6・書き換えた import 189(tests 177・tools 4・docs 8)・道の文字列の記号 14(5b の記録 §17-1 と同じ数)。E5-b は 23 組・**差し替え 25 か所**(`run` 19・`build_ledger_bundle` 1・台帳の型 5 行=`Ledger` 2・`_HouseholdWalletLedger` 2・`GoodsLedger` 1)を確かめた: 助けの `Ledger`・`_HouseholdWalletLedger` は main と wire_economy の両方・`GoodsLedger` は wire_economy だけ・`build_ledger_bundle` は main だけ・`run` は main だけ(裁定の表と同じ)。見られなかった 0。読み込みの時だけの読み 1(`Ledger`: 元の `cli.py:251` の `_HouseholdWalletLedger` のクラスの親=裁定の表の「251 はクラスの定義の親」と同じ)。
- (ii) 助け `tests/economy/_stage2_outside.py` の main の側の 2 行を外す: E5-b が止めた(`Ledger`・`_HouseholdWalletLedger` が main に届かない)。
- (iii) `SPLIT_ALIAS_DESTS` を外す: `strict` は手で直す一覧で断る。書かない実行では `test_resume_10d` の `build_ledger_bundle` と助けの台帳の型が「見られなかった」に出て、確かめた欄に出ない(E5-b は手で直す一覧の別名を、割った後の向く先を見られないので止めずに一覧へ出す=§7 の 1)。
- 試験 `test_patch_reach_replays_the_22nd_split_on_the_g3_base_in_history`(slow)が (i)〜(iii) を確かめる。細目は `r8/s6g0/replay_detail_out.txt`。

## 5. 段 6 の形の書かない実行(メモリの中・最後の道具で回し直して出力が 1 バイトも同じ)

計画の役の `r8/s6/retake/dry6r.py` を `r8/s6g0/dry6g0.py` に写して直した: 作業の木の木をメモリに読み、S6-A の形(`apply_detection` を 2 つに割る・`perceive.py` の 2 行・`ledger_paths.py` に空の `LEDGER_PATHS_SPLIT`)・裁定 Q2 の 2 名・2 つ目以降の 14 行・`[[ignore_split]]` 4 本と `[[split_weakens]]`・E8 の宣言 2 つをメモリの中で足し、`make_split_plan`(順の確かめなし・`strict=False`)。本物の木のファイルは書いていない。

| 項 | 結果 |
|---|---|
| 守り | 13 個とも「同じ」(`declarations`・`patch_reach` を含む)・契約は「宣言どおり 4」・止めた理由 0 |
| 前向きの表 | 2 行=`act/ops/plan_writes.py`・`mind/ops.py` → `engine/resolve.py`(宣言は 3=取り直し §5 と同じ)。1 対 1 の表に主な割り先 1 行 |
| 前向きの表の無い木(今の本物の木の形) | 「前向きの表が無い」で止めた(2 本を名指し) |
| E8 の宣言 2 つ | 当たった: `runtime/state/ledger.py::_ALLOW_REVENUE` → `"act/ops/shop.py"`・`runtime/state/ledger_ast.py::ext_reason` → `"runtime/state/restore.py"`(各 道 1)。宣言を外すと 2 か所が手で直す一覧へ(74 → 76) |
| 手で直す一覧 | **74 文・56 本**=import 52(src 9・tests 41・tools 2)+名の無い点の道 1(`guide_permits.py::RESOLVE_FILE`)+E8 の名の手がかりの無い道 21(tests の 17 記号) |
| E5-b(そのまま) | 10 組・11 か所を確かめた・5 組・6 か所は手で直す一覧の別名で見られなかった(`test_resume_10d` 3・`test_sim_time_T` 1・`tools/c7/attr_arms.py` 1・`occupancy_series.py` 1)・読み込みの時だけの読み 0 |
| E5-b(G1 の手直しの模擬を割った後の木に当てて回し直す) | **15 組・17 か所が全部通った**(名 9・止めた 0・見られなかった 0)。模擬: `test_resume_10d` の関数の中の 2 つの `R` を init_writes・body_writes へ・`test_sim_time_T` の `R` を mind/ops と別名 `RB`=body_writes に分け `advance_body` を `RB` で・c7 の道具 2 本の `module` を `act.apply` へ(計画 §7-1 の形) |

E8 で手で直す一覧に入った 21 文(17 記号): `test_cp2_write_window` 2・`test_stage2_writers::_callers_in_resolve`・`test_body_guard::test_only_the_ports_write_the_body_layer` 3・`test_move_prep_stage2` 5(4 記号・`_split_tree` を含む)・`test_fix_guards::_EXEMPT_D6`・`test_stage_a_guard` 2(`_EXEMPT_D6`・`test_every_state_ufunc_at_in_resolve_checks_the_written_array`)・`test_add_at_guard` 4(3 記号)・`test_energy_balance::_PER_TICK`・`test_two_phase` 2(`_hot_paths`・`test_only_resolve_writes_to_the_world`)。前は黙って `act/apply.py` へ書き換わっていた(取り直しの「道の文字列」16 記号)か、連鎖の見落としで残っていた(`test_add_at_guard` の 137・148・149 行と `test_stage_a_guard` の 163 行の `SRC / "engine" / "resolve.py"`・`test_move_prep_stage2` の 105 行と 122 行〔`_split_tree`〕の `root / "engine" / "resolve.py"`=6 か所)。どれも計画 §7-2 の「割る前に直す試験」と重なる。

## 6. 計画・取り直しの見立てと違った所

1. **E5-b の「17 か所を通す」は手直しの後**: 今の木のまま当てると、手で直す一覧に残る別名の差し替え 6 か所は割った後の向く先が決まらないので「見られなかった」に出る(止めない)。G1 の手直しの形を模擬すると 17 か所が全部通る。G1 では手直しの後の書かない実行で E5-b が全部を確かめる(手で直す一覧が 0 でないと `strict` は当てない)。
2. **手で直す一覧は 54 → 74**: R2 で 1 減(`LAYER_SRC`)・E8 で 21 増(§5)。取り直しは「黙って主へ向く道は src 2・tools 1・tests 2」と見たが、名の手がかりの無い斜線の道は tests にもっと在り(取り直しの「道の文字列」16 記号のうち名の手がかりの無いもの)、連鎖の見落としの直しで 6 か所が新しく見えた。
3. 計画 §8 は E8 の宣言を「全ファイルの表 §4 の注」に書く形と書いたが、発注のとおり E5-a にそろえて `split.py` の表にした(取り直し §11 の `table.py` の注の読みは使っていない)。
4. 守り ④ に `ledgerpaths.check`(1 対 1 の表の全部・前向きの表・台帳の行)を足した(前の割る道具は呼んでいなかった)。段 6 の書かない実行と履歴の当て直しの木で「同じ」。

## 7. 決めたこととわけ

1. **E5-b は手で直す一覧の別名の差し替えを止めずに「見られなかった」へ**: 割った後の向く先は手直しで決まる。`strict` は手で直す一覧で先に断るので、黙って当たることは無い。書かない実行(`--through`)で止めると、手で直す一覧ごと報告が消える(手直しの前の書かない実行が役に立たない)。発注の「見られなかった形は一覧に」に合わせた。〔検収の中-1・低-1 で改めた=§9: 主な割り先が元のファイルの行ではこのわけが成り立たなかった。別名が本当に手で直す一覧に在るときだけ「見られなかった」にし、`strict` は「見られなかった」が在れば断る〕
2. **E8 は主な割り先が元のファイルの行(18 本目の形)にも当てる**: 書き換えないまま元の道を指し続けるのも、主な割り先へ黙って向けるのと同じなので、割り先 2 つ以上なら手で直す一覧へ。今の順に当たる行は無い(延ばした 18 本目を当てる時に効く)。
3. **E8 の宣言は名の無い点の道にも効く**(`-m` の入口と転送の名が先)。`strings.split_nameless` の docstring が「E8 はここに宣言の表を先に引く形で足す」としていたため。
4. **宣言と組の名が食い違えば手で直す一覧**(どちらかを黙って選ばない)。宣言は引いた扱いにし、「使われなかった」で止めて手で直す一覧を隠さない。
5. **連鎖の見落としの直し**(§1-2): E8 の「黙って主へ向けない」が連鎖にも効くには、連鎖の記号を必ず選ぶ要がある。今の順の行は全部済んでいるので、当てた本の結果は変わらない(見本の試験も変わらない)。
6. **E7 の前向きの表の書き直しは中身が変わったときだけ**: S6-A の表の字面(注など)を保つ。1 対 1 の表は前と同じく毎回作り直す。
7. **元のファイル自身が前向きの表の鍵の行**(後の段でまた割る形): 主な割り先へ鍵が付いて行く(前向きの表のまま)。主な割り先に宣言が無ければ守り ④(前向きの表の今の道は宣言を持つ)が止める。今の順に当たる行は無い。
8. **E9 の表の順は割る行の `split_order` から**: 頭の `split_order` の並びが在れば食い違いを断る(片方だけ直した表を黙って使わない)。
9. **E5-b の組は記号(関数)単位**: `symbol_map` と同じ見方(入れ子の関数は外の関数・メソッドは `クラス.メソッド`)。コードの文字列の中は別の組(子のプロセスでだけ効く)。

## 8. 親に聞くこと・確かめていないこと

親に聞くこと:

1. §7 の 1(手で直す一覧の別名=止めずに「見られなかった」)と 2(元のファイルが主な割り先の行にも E8)でよいか。
2. 段 6 の E8 の 21 文: 計画 §7-2・裁定 R1 の割る前の直し(`split_files`・`RESOLVE_FILES` から範囲を作る)で消える物と、宣言(E8)で向ける物と、`test_move_prep_stage2::_split_tree`(偽の木を作る見本の字面=`LAYER_SRC` と同じ形)のように `STRING_EXCLUDE` の候補になる物の振り分け。
3. `move.py` に `LEDGER_PATHS_SPLIT` の許可を足すか(段 4 は済み・今は止まる側)。

確かめていないこと:

- src の側(S6-A)の本物の `LEDGER_PATHS_SPLIT` と `ledger_path()` の形では回していない(書かない実行は計画の形の空の表をメモリの中で足した)。道具は表の字面だけを読む。
- byte-check・範囲の全体の試験・import-linter・grimp は回していない(src を変えていない)。
- E5-b の有効範囲の見方は近似(内包の最初の iter・walrus・入れ子のクラスの有効範囲は細かく見ていない)。名で読まない使い方(別名を関数へ素で渡す)を通る差し替えは拾わない(その別名は E5-a と手で直す一覧の側で止まる)。
- E9 の見本の木は本物の `bridging_scan.py` と `foundation/paths.py` を写す。この 2 本の import が増えると試験が落ちる(大きな音で)。
- `tests/c7` は E5-b の走査に入れていない(発注のとおり)。道具は前と同じく c7 の import を書き換える。
- 段 6 の書かない実行は計画の形をメモリの中で足したもの。表と順が入った後の本物の `split --next` の数は、次の発注で取り直す。

## 9. 検収の後の直し(検収=条件つき受入の中 1・低 6 のうち中-1・低-1・低-3・低-5・`8997e2d` の木)

発注: scratchpad の `r8/order_stage6_g0_tools_fix.md`。検収: `r8/review_s6g0_tools.md`。変えたのは `split.py`(+55 行ほど)・`README.md` の E5-b の節・試験(+93 行=5 関数)・本書だけ。`strings.py`・`ledgerpaths.py`・`cli.py`・`table.py` は直しで変えていない。

### 9-1. 直し 1(中-1): 主な割り先が元のファイルの行で、E5-b が届かない差し替えを止めなかった

- なぜ: 主な割り先が元のファイルの行(元のモジュールが残る形=延ばした 18 本目)では、元のモジュールを指したままの差し替えを全部「見られなかった(手で直す一覧の別名)」に回していた。この形では別名は機械で書き換わる(元のモジュールのまま)ので手で直す一覧は空で、`strict` でも当たる。§7 の 1 のわけ(「`strict` が手で直す一覧で先に断る」)が成り立たなかった。
- どう直した: `split._dest_modules(plan)`=割り先のモジュールの名 → 割り先(元のファイルが主な割り先なら元のモジュールも入る)。差し替えが向くモジュールはこれで割り先に引き、ほかの割り先と同じに「届かない」「集合の外」を見る。割り先でないモジュール(割った後に無い元のモジュール・転送)を指したままの差し替えは、`split._listed_manual`(差し替えの別名を結ぶ import の文の行が手で直す一覧 `plan.manual` の項に在る・コードの文字列はその記号の項に在る)が真のときだけ「見られなかった」、偽なら止める(「割り先でないモジュール … を指す(手で直す一覧に無い)=どの割り先にも届かない」)。差し替え 1 か所の記録 `_Patch` に、別名を結ぶ import の行(`binds`)を足した。
- 確かめ(見本の木・元の `sp/port.py` に `_K`・`P`、`m` は `txt/mora.py` へ): `_K` を元のモジュールへ向けて差し替え・呼ぶ時に読む関数が外へ出た(`m`)=止まる(「届かない割り先 ['txt/mora.py']」「集合の外の割り先 ['sp/port.py']」)/読む関数が元に残った(`P.n`)=通る(確かめた `_K → ['sp/port.py']`)/誰も呼ぶ時に読まない `P`=名を結ぶ元へ向いて通る。どれも手で直す一覧は空。負の対照: 直しを外す(元のモジュールを割り先と見ない・手で直す一覧と突き合わせない)と、前と同じく守りは「同じ」のまま「見られなかった」に回る。もう 1 本: 書き換えの外の記号に在る文字列の的(別名を通さない=手で直す一覧に無い)が元のモジュールを指したままなら止まる。

### 9-2. 直し 2(低-1・親の裁定): 「見られなかった差し替え」が残る計画は、厳しい当てでは断る

- どう直した: `make_split_plan` の守りの後に、`strict`(`--apply` の道と `--through` でない書かない実行)で `patch_unseen` が 1 つでも在れば `SplitRefused`(終了コード 2・断る文に場所とわけ=手で直す一覧と同じ扱い)。宣言して通す口は作っていない。`strict=False`(`--through`)は前と同じに一覧に出す。
- 確かめ: 的の文字列を組み立てる差し替え(f 文字列)だけを持つ見本で、手で直す一覧は空・`strict=False` は一覧に 1 つ・`strict=True` は断る。5b の G3 の履歴の当て直し(そのまま)は今も `strict` で通る(見られなかった 0・細目は前と 1 バイトも同じ)。

### 9-3. 直し 3(低-3): 範囲の外のファイルの報告から、E8 の名の無い道が消えた

- なぜ: 範囲の外(E4)のファイルは数えるだけの計画(`probe`)で走査するが、`excluded_sites` の「手で直す」は import の警告だけを数えていた。E8 の前は名の無い道を書き換えに数えて出ていた(5b の G2 の当て直しで `test_bytecheck` の 4 か所)。
- どう直した: `probe.str_stats.skipped` の手で直す分(E8 の名の無い道・名の無い点の道ほか)も「手で直す N」に足す。範囲の外なので書き換えず、手で直す一覧にも入れない(前と同じ)。
- 確かめ: 範囲の外のファイルに名の無い道 1 つ=`excluded_sites` が「書き換え 0・手で直す 1(範囲の外=書き換えない)」・手で直す一覧は空・ファイルは変わらない。

### 9-4. 直し 4(低-5): 記録と README

- 本書の頭に土台(実装は `bde381e`・載せ直しの後は `8997e2d`)を書いた。「決めたこと」は §7 の 9 つが正(はじめの報告で 7 つと書いたのは 6〜9 を落とした書き損じ)。§1-3 と §7 の 1 に、この直しの指し先を書いた。
- `tools/pkgmove/README.md` の E5-b の節を直し 1・2 の形にし、直し 3 と、`--map` を渡さないときも CLI の出力の欄が増えていること(低-4)を書いた。

### 9-5. 裁定 T1〜T4(`r8/rulings_stage6.md`)

- T1(見られなかった差し替えを一覧に出す)=直し 1・2 の形に改めて受け入れ。
- T2(E8 を主な割り先が元のファイルの行にも)=受け入れ。
- T3(`move.py` に前向きの表の許可)=今は足さない(段 6〜8 で移す道具を使わない)。
- T4(E8 の 21 文の振り分け)=表と順の発注で、2 本の流れが入った後の書かない実行を取り直してから親が決める。

### 9-6. 数の前後と確かめ(`8997e2d` の木・重いものは合図を取ってから 1 本ずつ)

| 何を | 結果 |
|---|---|
| `test_pkgmove`(`-m "not slow"`・`-n` なし) | 145 passed・21 skipped → **150 passed・21 skipped**(+5=足した試験。飛ぶ 21 本は前と同じ顔ぶれ) |
| slow 2 本 | `test_split_5a_5b_in_memory_keeps_the_import_rules_to_the_end` passed・`test_patch_reach_replays_the_22nd_split_on_the_g3_base_in_history` passed(57 秒=そのまま通る・助けの行を外すと止まる・宣言を外すと断る) |
| 履歴の細目(`replay_detail.py`) | §4 と 1 バイトも同じ(守り 14 同じ・差し替え 25・見られなかった 0) |
| 本物の木 | `split --next`・`--through all` は「割る段は全部当たっている」(置き場にファイル 0)・`map --check` 同じ・`contracts --stage delete --tree . --check --probe` 同じ(2+9・20 辺・延べ 26 行・効かない 0)・`git status --porcelain -- src` 空 |

足した試験(5 関数): `test_patch_reach_checks_the_source_module_as_the_main_destination_of_an_in_place_row`・`test_negative_without_fix_1_an_in_place_patch_that_misses_slips_through`・`test_patch_reach_stops_a_stale_target_that_is_not_in_the_hand_fix_list`・`test_strict_split_refuses_a_plan_with_patches_it_cannot_see`・`test_excluded_files_report_nameless_paths`。前から在る試験は 1 字も変えていない。

### 9-7. 段 6 の形の書かない実行を今の木で回し直した(`r8/s6g0/dry6g0_now.py`・出力 `dry6g0_now_out.txt`)

今の木には S6-A の形(`write_b4_hash`・`write_intero_stages`)と本物の `LEDGER_PATHS_SPLIT`(空)が在るので、メモリの中で足す物からその 2 つを外した(ほかは §5 と同じ)。前向きの表の無い木の場合は、メモリの中で表を外して作った。

| 項 | 結果(§5=`bde381e` の木との違い) |
|---|---|
| 守り | 13 個とも「同じ」・契約は宣言どおり 4・止めた理由 0(同じ) |
| 前向きの表 | 2 行(`act/ops/plan_writes.py`・`mind/ops.py` → `engine/resolve.py`)・1 対 1 の表に主な割り先 1 行(同じ) |
| 前向きの表を外した木 | 「前向きの表が無い」で止めた(同じ) |
| E8 の宣言 2 つ | 当たった・外すと 2 か所が手で直す一覧へ(同じ) |
| 手で直す一覧 | 74 文・56 本(数は同じ)。中身の違い: `validation/static/system_static_check.py:31` が消えた(S6-A で読み方を直した)・S6-A で入った試験 `tests/engine/test_detection_writes_split.py:24` が足された・`test_tm3_step_scope` と `test_move_prep_stage2` の行の番号がずれた。import 52(src 8・tests 42・tools 2)+名の無い点の道 1+E8 の 21 |
| E5-b(そのまま) | 10 組・11 か所を確かめた・5 組・6 か所は手で直す一覧の別名で「見られなかった」(同じ。直し 1 の後も、6 か所の別名は手で直す一覧の import の行に在る=`_listed_manual` が真)。この形のまま `strict` で当てると、手で直す一覧と「見られなかった」の両方で断る |
| E5-b(G1 の手直しの模擬の後) | 15 組・17 か所が全部通った・止めた 0・見られなかった 0(同じ) |

### 9-8. 親に聞くこと・確かめていないこと(この直しの分)

- 聞くこと: 無い(直し 1〜3 は発注と裁定の形のまま)。
- 確かめていないこと: `_listed_manual` は手で直す一覧の項の字面(`<ファイル>:<行>:`・`<ファイル>::<記号>:`)と突き合わせる。手で直す一覧の項の書き方を変えると突き合わせが外れ、止める側(「手で直す一覧に無い」)に倒れる。延ばした 18 本目(`engine/speech/port.py`)の本物の木では回していない(今は順に無い)。

## 10. 親の確かめと検収(第347・2026-11-19)

### 10-1. 別の役の検収

- 判定: **条件つき受入**(高 0・中 1・低 6)→ 直し(§9)→ 直しの差分の再検収 **受入**(高 0・中 0・低 3=どれも知らせ)。検収役はファイルを 1 本も変えていない。
- 前から在る動き: 新旧の道具を土台の木に当て直して比べた。22 本目(土台 `e6d221c`)は、書いたファイル 127 本が 1 バイトも同じ(違いは報告の欄だけ)。5b の G1(18〜20 本目)・G2(21 本目)・5a の 12〜17 本目の違いは、名の無い道が「主な割り先への書き換え」から「手で直す一覧」へ移った分(E8)だけ。E5-b が誤って止めた所は 0。期待を書き換えた 3 本は、宣言の行を足しただけで弱まっていない。
- E7: 負の対照 4 つは全部止まる・表の無い木でも止まる・逆向きは 1 対 1 の表だけを引く・移すと鍵は付いて行く。S6-A の本物の空の表を読め、2 行を書いた字面は `LEDGER_PATHS` と同じ形。
- E8: 斜線・連鎖・点・`exact` の表のどれにも、黙って主な割り先へ向く道は残っていない。f 文字列と連結は前から黙って残す形だが、段 6 の本物の木に該当は 0。既に当てた 22 本で、`/` の連鎖の取り残しは本体の木に無い(偽の木の見本 2 か所だけ)。
- E5-b: 影・`global`・ラムダと内包・メソッド・デコレータ・関数ごとの組は正しく働く。本物の履歴 `e6d221c` では、そのままなら 25 か所が通り、main の側の 2 行を外す・wire の側の 2 行を外す・`GoodsLedger` を main へ向ける・宣言を外す、で止まる(断る)。
- E9: `--map`・`--contracts` を渡さないときの読み先・順・決まりは前と同じ(出力の欄は増えた)。見本の木の試験は空回りしない。
- 直しの後(再検収): 中-1 の見本(元の `_K` を差し替え・読むのは割り先の `m`)は止まる。手で直す一覧が空で f 文字列の的だけを持つ形は、厳しい当てで断る。5b の G1・G2・G3 の土台の当て直しは見られなかった 0 で、書いたファイル・手で直す一覧・守りは前と 1 バイトも同じ(誤って断る所は無い)。G2 の当て直しで、範囲の外のファイル `test_bytecheck.py` の当たりが報告に戻った。
- 再検収の低(知らせ): `_listed_manual` は import の行で突き合わせる(`strict` ではどちらでも断るので、変わるのは `--through` の報告の分け方だけ)/範囲の外のファイルの報告は、5b の G0 から数えていなかった名の無い点の道の分も出すようになった(漏れが減る側)/逃げ道が無いので、範囲の外のファイルの中の差し替えや、元のファイルで結ばれていない名の差し替えを持つ割る行は必ず断られる(段 6 には無い。段 7・8 では発注の前の書かない実行で先に数える)。

### 10-2. 親の裁定(`r8/rulings_stage6.md`)

- T1(見られなかった差し替え): 一覧に出すだけ、という前の仮の答えを改め、**厳しい当てでは 1 つでも在れば断る**(逃げ道は作らない)。T2(E8 を、主な割り先が元のファイルの行にも当てる): 受け入れる。T3(移す道具に前向きの表の許可): 今は足さない(段 6〜8 では移す道具を使わない)。T4(E8 で手で直す一覧に出た 21 文の振り分け): 表と順の commit の書かない実行を見てから決める(検収役の数え= 割る前の試験の直しで消える見込み 15・偽の道 6・宣言で向ける物 0)。
- 検収の低-2(`test_bridging_ledger.py` の「前向きの表は空」の比べ)は、割る前の試験の直しの commit で、空であることに頼らない形に直す。

### 10-3. 親が回した確かめ(載せ直しの後の木・S6-A の本物の `LEDGER_PATHS_SPLIT` が在る)

| 何を | 結果 |
|---|---|
| 載せ直し(実装は `bde381e` の木・親が `8997e2d` へ) | 変えたファイルは控えと 1 バイトも同じ・`git status --porcelain -- src` は空 |
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 150 passed・21 skipped・落ちた試験 0(前は 112 passed・21 skipped=足した 38 場合。飛ぶ 21 本は前と同じ) |
| `tests/tools/test_pkgmove.py` の slow | 2 passed(前からの 1 本と、足した履歴の当て直しの 1 本) |
| `tests/tools` の束(`-m "not gpu and not slow"`・`-n 2`) | 642 passed・落ちた試験 0(`test_pkgmove.py` を除く) |
| 本物の木の `split --next`・`map --check`・`contracts --check --probe` | 「割る段は全部当たっている」・同じ・同じ(例外 20 辺・延べ 26 行) |

## E5-c 素で使う別名の宣言(土台 `e543f3b`・親の裁定 T5・2026-11-19)

別名を属性で読まずに渡す・しまう形(素の使い方)は、別名を分けても消えない。割る道具はこの形を必ず手で直す一覧に出し、厳しい当ては断る。その形を宣言で通す拡張と、宣言 4 つ・除外 1 つを入れた。src・`tools/c7`・ほかの試験・表・`map.toml`・`contracts.toml` は変えていない。

### E5c-1. 変えたファイル(`git diff --numstat`・足した/消した)

| ファイル | 行 | 何を |
|---|---|---|
| `tools/pkgmove/split.py` | 110 / 10 | `AliasDest` の欄 4 つ・守り・`patch_reach` の宣言の確かめ・報告の `patch_declared`・宣言 4 つ・除外 1 つ |
| `tools/pkgmove/imports.py` | 48 / 3 | 素の使い方の形(`BARE_OK`・`bare_form`・`AliasUse.bare_forms`) |
| `tools/pkgmove/cli.py` | 4 / 2 | `split --through` の要約と行・`--next` の表示に `patch_declared` |
| `tools/pkgmove/README.md` | 30 / 0 | E5-a の節の後に E5-c の節・`STRING_EXCLUDE` の行 |
| `tests/tools/test_pkgmove.py` | 198 / 0 | 足した試験 23 本(下) |

### E5c-2. 形と守り

- 宣言の形: E5-a の `AliasDest` に欄を 4 つ足した。`bare`(素で使ってよい印)・`reads`(素で渡した先・しまった先で、そのモジュールの属性として読み書きする名)・`patches`(その別名を通す差し替えの名=字面で見える差し替えと、素で使った先の差し替えの全部)・`why`(渡した先・しまった先の関数と読む名)。印のある別名は宣言の割り先へ書き換え、手で直す一覧に出さない。印の無い別名の素の使い方は、今までどおり手で直す一覧へ出す。
- 許す素の使い方(`imports.BARE_OK`): 渡す(位置か名の引数)・返す・しまう(代入の値そのもの)・既定の引数・比べる(`is None`・`is not None`)。名を字面で書かない呼び出し(`getattr`・`setattr`・`vars`・`dir`・`.object` など)へ渡す形・入れ物に入れる・呼ぶ・`==` で比べる形は止める。「比べる」は発注の 4 つの形の外にある。`tools/c7/occupancy_series.py` の `if module is None` のために足した(名を読まない形)。
- 守り(別名の割り先の宣言の守り): 次のどれかで止める。印があるのに素の使い方が 1 つも無い(印の腐り)・許さない形・`reads` か `why` が無い・`reads` と `patches` の名が割り先の頂上で結ばれていない・印が無いのに `reads`・`patches` を書いた・使われなかった宣言(E5-a と同じ)。宣言はその割る行でだけ使う。別名の属性の読みは、E5-a と同じに割り先の頂上の名だけを許す。
- 差し替え(差し替えの届く先の守り): `patches` の名ごとに、E5-b の届かせる割り先の集合を出す。宣言の割り先が集合に無ければ止める(空振り)。ほかの割り先も集合に在れば止める(届かない)。字面で見える差し替えが印のある別名を通るなら、名が `patches` に無ければ止める。確かめた差し替えは報告の `patch_declared` に出す(`patch_checked`・`patch_unseen` とは分ける)。

### E5c-3. 宣言 4 つと根拠(渡した先・しまった先を読んで確かめた)

| ファイル | 別名 → 割り先 | 素の使い方 | 読む名(`reads`) | 差し替える名(`patches`) | 根拠 |
|---|---|---|---|---|---|
| `tests/engine/test_conversation_invite.py` | `R_TALK` → `act/ops/talk.py` | 渡す 1 | `talk_within_reach`・`set_conversing`・`end_conversation`・`revert_conversation` | 無し | `runtime/run.py` の `_settle_pending_invites`(引数 `R`)が `R` から読む 4 名。`R` への差し替えは無い |
| `tests/engine/test_defect_fixes_1103.py` | `R_TALK` → `act/ops/talk.py` | 渡す 5 | 同じ 4 名 | 無し | 同じ関数へ 5 か所で渡す |
| `tools/c7/attr_arms.py` | `module` → `act/apply.py` | しまう 1 | `apply` | `apply` | `AgentCellRecorder.attach` が `self._module` にしまい、`module.apply` を包みに替える。`detach` が `self._module.apply` を元に戻す |
| `tools/c7/occupancy_series.py` | `module` → `act/apply.py` | しまう 1・比べる 1 | `apply` | `apply` | `OccupancyRecorder.attach(module=None)` が引数で受けるか import し、同じく包んで戻す。ほかの属性は読まない |

- 4 つとも発注文の表と同じだった。`apply` の届かせる割り先の集合は `act/apply.py` だけ。元のファイルの中で `apply` を呼ぶ時に読む関数は無く、src の読み手が呼ぶ時に別名の属性で読む(=定義の割り先)。
- 除外 1 つ: `split.STRING_EXCLUDE` に `("tools/repo_guide/guide_permits.py", "RESOLVE_FILE")` を足した(親の裁定)。

### E5c-4. 足した試験(23 本・見本の木は E5-b の `_REACH_SRC` を割る)

- 通る形: 渡した別名が宣言の割り先へ書き換わる(`strict` でも当たる)/許す形を 1 つずつ数える(渡す 3・返す 1・しまう 2・既定の引数 1・比べる 1)/`patches` の名を、字面の差し替え 1 つの形と字面に無い形の両方で確かめ、`patch_declared` に出す/src のファイルの別名でも同じに効く(S6-G1 の `judge.py` の形)。
- 負の対照(どれも止まる・書かない実行でも止まる): 印の腐り・入れ物に入れる・`getattr(B, 変数)` へ渡す・`==` で比べる・呼ぶ・`reads` が無い・`why` が無い・`reads` の名が割り先に無い・別名の属性が割り先の外・`patches` の名が割り先に無い・印が無いのに `reads`・印の無い宣言の素の使い方・使われなかった宣言 2 つ(14 場合)/差し替える名の届く先が宣言の割り先だけでない(届かない・空振り)・字面の差し替えの名が `patches` に無い(3 場合)/`patch_reach` を外すと、届かない宣言が通る(守りが止めていることの確かめ)/宣言が無いと同じ読み手は手で直す一覧に出て断られる・ほかの割る行の宣言は使わない。
- 宣言が腐らない: 本物の印のある宣言 4 つの `reads` が、今の `_settle_pending_invites` が `R` から読む名と、`tools/c7` の 2 本のクラスが `module`・`self._module` から読み書きする名に一致する。

### E5c-5. 数の前後と確かめ(重いものは合図を取ってから 1 本ずつ)

| 何を | 前 | 後 |
|---|---|---|
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 150 passed・21 skipped | 173 passed・21 skipped(足した 23 本。飛ぶ 21 本は前と同じ) |
| slow(5a・5b の順の当て/履歴の当て直し) | 2 passed | 2 passed(25 秒・59 秒) |
| 履歴の当て直し(5b の G3 の土台 `e6d221c`・22 本目)を、前(HEAD の道具の写し)と後の道具で | — | 差分は 1 バイトも同じ。報告は鍵 `patch_declared`(空)が増えただけ。守り同じ・確かめた差し替え 25 か所・見られなかった 0 |
| `map --check`・`contracts --stage delete --tree . --check --probe` | 同じ・同じ | 同じ・同じ(古い 2+新しい 9・例外 26 行) |
| `git status --porcelain -- src`・秘密スキャン | — | 空・CLEAN |

### E5c-6. 本物の木の書かない実行(`split --through engine/resolve.py`)

- 守りは全部「同じ」で、決まりは「宣言どおり 4」。手で直す一覧は **8** で、src の import の別名 `R` だけが残った(`interim_bundles/calendar_self.py`・`mind/relations/layer.py`・`runtime/systems/assemble.py`・`body.py`・`judge.py`・`perceive.py`・`talk.py`・`world/laws/presence.py`)。親の取り直しの 13 から、宣言 4 つと除外 1 つで 5 減った。
- 差し替え: 確かめた 13・**見られなかった 0**・宣言で確かめた 2(`tools/c7/attr_arms.py` と `tools/c7/occupancy_series.py` の別名 `module` の名 `apply` → `act/apply.py`・字面で見えた差し替えは各 1)。読み込みの時だけの読みは 0。
- 別名の宣言 4 つは全部使われた。宣言の 4 本の import は `from shibuya.act.ops import talk as R_TALK` と `from shibuya.act import apply as module` に書き換わる。`guide_permits.py` は書き換えない。前向きの表 2 行・道の文字列の宣言 2・決まり 2+9 → 1+10・宣言した弱まり 4・宣言の無い弱まり 0 は前と同じ。

### E5c-7. 親に聞くこと・確かめていないこと

- 聞くこと: 許す形に「比べる(`is None`・`is not None`)」を足した。発注の 4 つの形の外だが、`occupancy_series.py` の `if module is None` は名を読まないので、止めると正しい形を止めることになる。この形でよいか。
- 確かめていないこと: HEAD の道具で今の木の書かない実行を回し、後の道具の差分と突き合わせることはしていない(合図を別の役が持っていた)。違いは、手で直す一覧の数(親の取り直し 13 → 8)と報告で見た。素の使い方の形は名の字面で見る(`alias_uses` と同じで、有効範囲は見ない)。`tools/c7` の 2 本の試験(`tests/c7`)は回しておらず、開いてもいない。

### E5c-8. 検収の後の続き(検収=受入〔高 0・中 0・低 3〕・土台 `2c4a164`=src の 8 本の別名の分けの後)

- 親の裁定 2 つ: 許す素の使い方に「比べる(`is None`・`is not None`)」を足したこと= 受け入れる(同一性を見るだけで名を読まない。`==`・`not`・`or`・三項は止まる)。`cli.py` の報告の欄の表示= 受け入れる。
- `judge.py` の宣言(1 行足した): `src/shibuya/runtime/systems/judge.py` の別名 `R_TALK` → `act/ops/talk.py`・印あり・`reads` は talk の 4 名(`talk_within_reach`・`set_conversing`・`end_conversation`・`revert_conversation`)・`patches` 無し。根拠: `R_TALK` は 29 行で import し、素の使い方は `sys_apply_responses` の 163 行で `_settle_pending_invites`(94 行で `runtime/run.py` の関数を写した名)へ渡す 1 つだけ。`R_TALK` の属性の読みは 0、差し替えの字面も 0。受け手が `R` から読む名は 4 名のまま。発注文と同じ。
- 決まり(検収の低-1・親の裁定): 道具に辿らせる拡張は今は入れない。`tools/pkgmove/README.md` の E5-c の節に、道具が辿らない形(しまう・既定の引数で写した先の読みと差し替え・渡した先の中・`inspect.getmembers(B)`・`functools.partial(getattr, B)` のように「渡す」として通る形)と、決まり「印のある宣言を足すときは、宣言が腐らない試験の受け手の表に受け手を足す」を書いた。
- 決まりを守らせる試験: 宣言が腐らない試験を、受け手の表 `_BARE_RECEIVERS`((ファイル, 別名) → (受け手のファイル, 受け手の関数かクラス, モジュールを持つ字面)・5 行)で作り直した。食い違いを出す `_bare_receiver_problems` が空であることを確かめる。見るのは次のとおり。印のある宣言の集合と受け手の表が同じ・`reads` が受け手の字面から引いた読み書きする名と同じ・`patches` が書く名と同じ・`why` に受け手の名が在る・宣言のファイルの素の使い方が受け手へ渡すか受け手の中だけ。前の試験は宣言の集合を字面で固めていたが、受け手は別名の名で選んでいた(`R_TALK` の宣言を足すと受け手の確かめは自動で付いた)。今は表の行が無ければ落ちる。
- 負の対照(1 本・4 つの確かめ): メモリの中で印のある宣言を 1 行足し、受け手を足さないと「受け手が無い」が出る/宣言を外すと「印のある宣言の無い受け手」/`reads` を 1 つ欠くと「と違う」/受け手を別の関数(`_inviter_of`)にすると「受け手の外の素の使い方(行 [163])」と「受け手が無いか」。
- 数の前後(合図を取って 1 本ずつ): `tests/tools/test_pkgmove.py`(not slow)は 173 passed・21 skipped → 174 passed・21 skipped(負の対照 1 本を足した。宣言が腐らない試験は作り直しで数は同じ)。slow は 2 passed(24 秒・58 秒=履歴の当て直しは前と同じに通る)。`map --check`・`contracts --probe` は同じ・同じ(古い 2+新しい 9・例外 26 行)。`git status --porcelain -- src` は空・秘密スキャンは CLEAN。
- 書かない実行の取り直し(載せ直しの後の本物の木・`split --through engine/resolve.py`): 守りは全部「同じ」(決まりは宣言どおり 4)。**手で直す一覧は 0・見られなかった差し替えは 0**。確かめた差し替え 13・宣言で確かめた差し替え 2(`tools/c7` の 2 本の `module` の `apply` → `act/apply.py`)・読み込みの時だけの読み 0。別名の割り先の宣言は印のある 5 つが全部使われた(`judge.py` 渡す 1・`test_conversation_invite.py` 渡す 1・`test_defect_fixes_1103.py` 渡す 5・`attr_arms.py` しまう 1・`occupancy_series.py` しまう 1 と比べる 1)。`judge.py` の import は `from shibuya.mind import ops as R_MIND`・`from shibuya.act.ops import talk as R_TALK` に書き換わる。前向きの表 2 行(`act/ops/plan_writes.py`・`mind/ops.py`)・道の文字列の宣言 2・決まり 2+9 → 1+10・宣言した弱まり 4・宣言の無い弱まり 0。この出力が、次の commit(道具で写す)の「当てる前」の姿になる。

## E5-c 素で使う別名の宣言: 親の確かめと検収(第347・2026-11-19)

### E5-c(親)-1. 別の役の検収

- 判定: **受入**(高 0・中 0・低 3)。続き(`judge.py` の宣言と決まり)の再検収: **受入**(高 0・中 0・低 2=どちらも知らせ)。judge の 3 条件(素の使い方はその関数へ渡す 1 つだけ・属性の読み 0・差し替え 0)と、受け手が talk の 4 名だけを読むことを、今の木で確かめた。作り直した試験は、宣言を足して受け手を足さない・宣言を外す・読む名を欠く・受け手を別の関数に替える、のどれでも落ちる。 検収役はファイルを 1 本も変えていない。
- 宣言の無い別名の動き: 新しい道具と前の道具で、5b の G1・G2・G3 の土台に当て直した。書いたファイル(42・166・127 本)・手で直す一覧・守りは 1 バイトも同じ(違いは、報告の空の欄が 1 つ増えただけ)。印の無い宣言の素の使い方は今も止まる。宣言の無い別名を素で渡すと、今も手で直す一覧に出て、厳しい当ては断る。
- 口の広さ: 止まる形= 属性の読みが割り先の外・渡した先で読む名が割り先に無い/空/わけが無い・差し替えの空振り/届かない/字面の差し替えの名が宣言に無い・印の腐り・使われない宣言・ほかの行の宣言・印無しで読む名を書いた宣言・`vars(別名)`。同じファイルの別の別名や、関数の中の同じ名の別名へ、宣言は漏れない。
- 許す素の使い方の「比べる」: 演算子が全部 `is`/`is not` で、項がその別名か `None` だけの形だけを許す(同一性を見るだけ=名は読まない)。`==`・`not`・`if 別名:`・`or`・三項は止まる。
- 宣言の根拠: `_settle_pending_invites` が受け取ったモジュールで読むのは talk の 4 名だけ(ほかへ渡す所も差し替えも無い)。`tools/c7` の 2 本は、モジュールをしまい、`apply` だけを読み書きする。`apply` の届く先は `act/apply.py` だけ。

### E5-c(親)-2. 検収の低と、親の裁定

- 低-1(口の広さ=「しまう」「既定の引数」で写した先の読みと差し替えを、道具は辿らない。宣言の外の名を写した先で差し替えると、音の立たない空振りになる): **道具に辿らせる拡張は今は入れない**。決まりを書いて試験で守らせる(印のある宣言を足すときは、宣言が腐らない試験に受け手を足す。試験は、受け手の字面から読む名・差し替える名を引いて、宣言と同じことを確かめる。印のある宣言の集合と、受け手を確かめる集合が同じことも固める)。段 7 で印のある宣言が増えるなら、辿る拡張を考える。
- 低-2(素の使い方は別名の名の字面で数え、有効範囲を見ない=止まる側): そのまま。低-3(`cli.py` の報告の欄の表示=発注の見込みの外): 受け入れる。
- 実装役が足した「`is None`・`is not None` で比べる」: 受け入れる(上の検収のとおり)。
- `runtime/systems/judge.py` の宣言(別名 `R_TALK` → `act/ops/talk.py`・渡した先で読む名は talk の 4 名・差し替え無し): src の別名の分けが入った後に足した(検収役の見立てのとおり)。

### E5-c(親)-3. 親が回した確かめ(src の別名の分けが入った後の木)

| 何を | 結果 |
|---|---|
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 174 passed・21 skipped・落ちた試験 0(前は 150 passed・21 skipped=足した 24 場合。飛ぶ 21 本は前と同じ) |
| `tests/tools/test_pkgmove.py` の slow | 2 passed |
| `tests/tools` の束(`-m "not gpu and not slow"`・`-n 2`) | 642 passed・落ちた試験 0(`test_pkgmove.py` を除く) |
| 本物の木の書かない実行(`split --through engine/resolve.py`) | 守りは全部「同じ」(決まりは宣言どおり 4)・**手で直す一覧 0・見られなかった差し替え 0**・差し替えの届く先は確かめた 13・宣言で確かめた 2(`tools/c7` の 2 本の `apply`)・印のある宣言 5 つと道の文字列の宣言 2 つが使われる・前向きの表に 2 行(`act/ops/plan_writes.py`・`mind/ops.py`)・消えるのは `engine/resolve.py` と `engine/__init__.py`・作る頭は `act/ops/__init__.py` |
| `map --check`・`contracts --check --probe`・`git status --porcelain -- src` | 同じ・同じ(例外 20 辺・延べ 26 行)・空 |

## M0: 延ばした 18 本目を順に載せる(土台 `c79ae25`=段 6 の本体の後・親の裁定 Q12・T2・2026-11-19)

5a で延ばした `engine/speech/port.py`(今の道は `society/speech/port.py`。`mora_count` と `_SMALL_KANA` を `foundation/text/mora.py` へ出し、残りの名は元のファイルに残す割る行)を、割る段の順の 24 本目に載せた。延ばした理由(台帳の道の表が 1 対 1)は E7 の前向きの表で無くなった。道具と表と試験だけで、src は変えていない。当てるのは別の commit(M1)。

### M0-1. 変えた所(`git diff --numstat`・足した/消した)

| ファイル | 行 | 何を |
|---|---|---|
| `tools/pkgmove/table.py` | 9 / 7 | `SPLIT_ORDER` の 24 本目・`SPLIT_DEFERRED` を空に(仕組みは残す)・`SPLIT_GROUPS["6"]` に群 `M`(24〜24・親の既定の形のまま)・注 |
| `tools/pkgmove/map.toml` | 4 / 3 | `cli.py map` で作り直した(358 行のまま・`split_order` 24 本・`split_deferred` 空・行 244 に `split_order = 24`) |
| `tools/pkgmove/contracts.toml` | 2 / 1 | 核 1(`runtime.clocks.speech → society.speech.port`・決まり 10)の `gone_at` を「段 6 の M(…)」に |
| `tools/pkgmove/split.py` | 6 / 1 | `judge.py` の宣言に `patches=("set_conversing",)`・わけの文(検収の低-2=意味の側) |
| `tools/pkgmove/README.md` | 10 / 2 | 5a の節(延ばした行を載せた)・E5-c の節(受け手の表の外の差し替えの欄・`judge.py` の `patches`) |
| 全ファイルの表 | 4 / 2 | 行 244 の割るかの欄(「延ばした」を外す)・行 244・244a の理由の注・行 244a の元の欄を「割る段 6」・§4-25 に注・頭の注に 1 行(割り先と名は変えていない) |
| `tests/tools/test_pkgmove.py` | 90 / 25 | 数の固定(24 本・群 M)・延ばした行の試験・受け手の表の外の差し替え |
| `tests/test_places_guard.py` | 1 / 1 | 注だけ(延ばした旨→24 本目に載せた) |
| カード `tests/engine/proximity` | 1 / 0 | 道具で作り直した(受け手の試験が `test_runs.py` の道を持つ=「読む試験」に 1 行) |

### M0-2. 本物の木の書かない実行(`split --through engine/speech/port.py`・当てる前の姿)

- 守り: 全部「同じ」(13 項。決まりも「同じ」=弱まり 0)。止めた守り 0。`strict` の `split --next` は手で直す一覧で断る(下)。
- 割り先: `society/speech/port.py`(元のファイル=主な割り先・名 10)・`foundation/text/mora.py`(新しいファイル・名 2)。消すファイルも作る頭も無い(`foundation/text/` の頭は在る)。
- **手で直す一覧 3**:
  - `tests/engine/speech/test_speech_on_reaches_addressee.py:26` と `tests/engine/speech/test_speech_port_schema.py:22` の別名 `P`(1 つの別名から、残る名と出る名の両方を読む)。
  - `tests/engine/speech/test_speech_writers_ast.py::PORT`(名の手がかりの無い道 `"society/speech/port.py"`)。
- **見られなかった差し替え 0**(この行の名を差し替える所は木に無い。確かめた 0・宣言で確かめた 0・読み込みの時だけ 0)。
- E5-b が「元のファイルが残ったまま名の一部だけを外へ出す行」で効くことの確かめ(見本の試験をメモリの中の木に 1 本足した 4 つ): `mora_count` を呼ぶ時に読むのは元に残る `Utterance.__post_init__`(`society/speech/port.py:145`)=届かせる割り先は元のファイルだけ。
  - 文字列の的 `"shibuya.society.speech.port.mora_count"`(名の割り先 mora へ書き換わる)→ 止まる(届かない `society/speech/port.py`・集合の外 `foundation/text/mora.py`)。
  - 読む名が `mora_count` だけの別名(道具の既定で mora へ向く)→ 止まる(同じ 2 つ)。
  - 別名を元のファイルへ宣言(E5-a)→ 通る(確かめた: `→ ['society/speech/port.py']`)。
  - 宣言なしで残る名も読む別名 → 手で直す一覧に出る。差し替えは元のモジュールを指したまま=主な割り先なので「確かめた」(S6-G0 の検収の中-1 の直しの形)。
- 台帳の道: 主な割り先の行 `"src/shibuya/society/speech/port.py": "src/shibuya/engine/speech/port.py"` は変わらない(足す行 0)。前向きの表に 1 行 `"src/shibuya/foundation/text/mora.py": "src/shibuya/engine/speech/port.py"`。つなぎの台帳の JSON は書かない。宣言の同定の集合は前後で同じ(元のファイルの宣言 2 → 元 1+割り先 1。割り先へ動くのは `mora_count` の docstring の宣言=台帳の行 `BR-DOC-SPEECH-MORA-KANA`)。守り ④ も「同じ」。
- 道の文字列・コードの文字列・src の道の表(E8)でこの行に当たる物:
  - 手で直す: `test_speech_writers_ast.py::PORT` 1 つ(上)。
  - 名の手がかりで元のファイルに残る(書き換えない・道具は何も出さない): src の `runtime/state/ledger.py` の `OWNER_CLASSES` の 2 行と、試験 `test_speech_port_schema.py:178`(どれも `("society/speech/port.py", "SpeechPort")`)。
  - 記録に出る文字列: `runtime/clocks/speech.py` の `manifest_fields` の `"mora_rule": "engine.speech.port.mora_count(仮名の数の近似・漢字 2 拍)"` は、ランの manifest の `talk_clock`(腕 mora のランだけ)に入る。字面は表の古い道(`engine.speech.port`)で今のモジュール(`society.speech.port`)ではないので、道具の書き換えに当たらない(src の文字列は許可の表の中だけを書き換える=この関数は表に無い)。書き換えないので byte-check は動かない。同じく古い道の字面の docstring(`runtime/clocks/speech.py`・`runtime/systems/boxes.py`・`society/contact/calls.py`)と `runtime/state/ledger.py` の `basis=` の文も当たらない。
- 道具が書くファイル 5(src 4=`foundation/decl/ledger_paths.py`・`foundation/text/mora.py`(新)・`runtime/clocks/speech.py`・`society/speech/port.py`/tests 1=`tests/engine/clock/test_tm2_talk_clock.py`)。書き換える import の文は src 1(`runtime/clocks/speech.py`)・tests 1(`test_tm2_talk_clock.py`)・tools 0・docs 0、元のファイルに作り直す import 1(`society/speech/port.py` が `mora_count` を割り先から読む)。道具の数え(見た文)は src 4・tests 8。`tests/c7` に当たる道 0。
- 当てた後の import の決まり: 契約は前後とも 11(古い 1+新しい 10)。例外は延べ 18 行/16 辺 → 17 行/15 辺(消えるのは核 1 だけ=`runtime.clocks.speech` が `foundation.text.mora` から読むようになり辺が無くなる)。載る例外 0・言えない決まり 0=`[[split_weakens]]` は要らない(宣言していない)。

### M0-3. M1 の下ごしらえの案(手で直す一覧を 0 にする・決めるのは親)

| ファイル | 別名 | 読む名 | 案 |
|---|---|---|---|
| `tests/engine/speech/test_speech_on_reaches_addressee.py:26` | `P` | 残る名 21(`SpeechPort` 9・`HEARD_MAX_PER_ADDRESSEE` 7・`HEARD_TTL_STEPS` 3・`SpeechContext` 1・`Utterance` 1)・出る名 1(`mora_count`=260 行) | `P` は残す。`from shibuya.society.speech import port as P_MORA` を足し、`P.mora_count(` を `P_MORA.mora_count(` に(段 6 の作法=割り先の葉の名を後ろに付ける・`R_TALK` と同じ形) |
| `tests/engine/speech/test_speech_port_schema.py:22` | `P` | 残る名 19・出る名 1(`mora_count`=82 行) | 同じ(`P_MORA`) |
| `tests/engine/speech/test_speech_writers_ast.py::PORT` | — | 道 `"society/speech/port.py"`=`SpeechPort` の書き手の置き場(割った後も元のファイル) | 案 1(推し): E8 の宣言 `PathDest("engine/speech/port.py", "tests/engine/speech/test_speech_writers_ast.py", "PORT", "society/speech/port.py")`(主な割り先へ向ける=字面は変わらない。後で元のファイルが動けば道具が見る)。案 2: `STRING_EXCLUDE` に足す(わけ=持ち主のファイルの道。後で動いても書き換えない) |

- メモリの中で試した(リポのファイルは書いていない): 試験 2 本の別名を上のとおり分け、`PORT` に案 1 の宣言を足すと、`strict` の当てが通る(守りは全部「同じ」・手で直す一覧 0・見られなかった 0)。分けた別名は `P_MORA` → `from shibuya.foundation.text import mora as P_MORA` に、`PORT` は字面のまま(宣言の使われ方 道 1)。

### M0-4. 検収の低-2(意味の側): `judge.py` の宣言の `patches`

- `tests/engine/proximity/test_runs.py` の `_recorded_run` が talk の `set_conversing` を差し替え、ランの中ではその読みが `judge.py` の渡す `R_TALK` を通る(受け手 `_settle_pending_invites` が `R.set_conversing` を読む)。宣言に `patches=("set_conversing",)` を足し、わけの文を正した。木の中で talk の 4 名を差し替える所は、この 1 か所だけ。
- 受け手の試験: `_BARE_RECEIVERS` に 4 つ目の欄(外の差し替え=受け手の外で割り先のモジュールの名を差し替え、ランの中でその別名を通って受け手に読まれる所)を足し、`judge.py` の行に `test_runs.py::_recorded_run` の `set_conversing` を書いた。宣言の `patches` は、受け手の中で書く名と外の差し替えの名を合わせたものと同じこと・外の差し替えが木に在ることを確かめる。受け手の読む名を割り先のモジュールで差し替える所を木の読み手(src・tools・`tests` の c7 を除く全部)から E5-b と同じ集め方で拾い、同じ受け手のどの行にも無ければ落ちる(同じ割り先の受け手の中の書きは数えない)。前の形はこの差し替えを見ていなかった。
- 負の対照(前の負の対照の試験に足した): 表から外の差し替えを外す→「patches と違う」と「どの受け手の行にも無い」/宣言の `patches` を外す→「patches [] と違う」/木に無い外の差し替えを書く→「木に無い」。
- 当て直し: 23 本目(土台 `4a5bd30`)を直す前と後の道具で当て直し、書いたファイル 112 本と差分は 1 バイトも同じ。違うのは報告の 2 欄だけ(`judge.py` の `alias_declared` に「差し替える名 set_conversing」・`patch_declared` に `judge.py` の `set_conversing → ['act/ops/talk.py']` の 1 行)。

### M0-5. 試験と確かめ(重いものは合図を取ってから 1 本ずつ・合図は単独の rm で返した)

| 何を | 結果 |
|---|---|
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 174 passed・21 skipped・落ちた試験 0(飛ぶ 21 本は前の回と同じ顔ぶれ=増えていない。次の割る行の書かない実行の試験は、割る行が残り 0 の枝から、24 本目を当てる枝に戻った。「割る段の終わりの木」で飛ぶ 1 本は残りが 1 本なので飛んだまま) |
| slow | 2 passed(5a・5b の順の当ては今の木で 24 本目まで当てて守りが通る・終わりの契約 11=19 秒/履歴の当て直し 53 秒) |
| `tests/tools` の残り+`tests/test_places_guard.py`(`-m "not slow and not gpu"`・`-n` なし) | 660 passed・落ちた試験 0・飛んだ試験 0 |
| 既に割った 23 本の当て直し(群ごとの土台 8 つ=5a の G1・G2・G3・G4/G5・5b の G1・G2・G3・段 6 の G1、前=HEAD の道具の写しと後の道具) | 書いたファイルと差分は 23 本とも 1 バイトも同じ。報告の違いは 23 本目の 2 欄だけ(M0-4) |
| `map --check`・`contracts --stage delete --tree . --check --probe`・`lint-imports` | 同じ・同じ(今の木=例外 18 行/16 辺)・11 kept |
| カード(`tools/repo_guide/build.py` → `cards/data.md` を単独の `git checkout --` で戻す → `--check`) | 最新(150 本)。変わったカードは `tests/engine/proximity` の 1 枚 |
| `git status --porcelain -- src`・秘密スキャン | 空・CLEAN |

- 親に聞くこと: M0-3 の案(別名の名 `P_MORA`・`PORT` の扱い)。カードの道具は `tests` の全部を自分で読む(`tests/c7` を含む・実装役は開いていない)。受け手の試験は、回すたびに `tests`(c7 を除く)・src・tools の .py を読む(約 2 秒)。
- 確かめていないこと: byte-check と範囲の全体の試験は回していない(src は変えていない)。M1(当てる)はしていない。

### M0-6. 親の裁定と、M0 の commit に足した下ごしらえ(src は変えていない)

- 親の裁定(仮採用・戻せる形): ① 別名の名は `P_MORA`(段 6 の `R_TALK` と同じ作法=同じ割り先には同じ名)。`PORT` は E8 の宣言(案 1)。② カードの道具が `tests` の全部を自分で読むのは前からの作り=そのまま。③ 受け手の試験が回すたびに src・tools・`tests`(c7 を除く)を読む形(約 2 秒)はそのまま。
- (a) `split.SPLIT_PATH_DESTS` に `PathDest("engine/speech/port.py", "tests/engine/speech/test_speech_writers_ast.py", "PORT", "society/speech/port.py")` を足した(`split.py` 9 / 1 の内の 3 行)。書かない実行で宣言は使われた(道 1・字面は変わらない)。使われなければ道具が止める(前からの守り)。`test_pkgmove` の宣言の腐りの試験(ファイルと記号が木に在る・割る行が順に在る)は直さずに通る。
- (b) 試験 2 本(`test_speech_on_reaches_addressee.py`・`test_speech_port_schema.py`。各 3 / 1)に、注 1 行と `from shibuya.society.speech import port as P_MORA` を足し、`mora_count` の読み 1 か所ずつを `P_MORA.mora_count(` に替えた(`P` は残す)。直す前と後で、2 本の 55 ノードがどれも passed で同じ(飛んだ試験 0)。足した別名を畳む(import の 1 文を外し `P_MORA` を `P` に戻す)と、AST は直す前と同じ。
- (c) 直した後の本物の木の書かない実行(`split --next`=厳しい当て・書かない): 守りは全部「同じ」(決まりも「同じ」)・**手で直す一覧 0・見られなかった差し替え 0**・E8 の宣言は `PORT` が道 1 で使われた・前向きの表 1 行(`foundation/text/mora.py` → `src/shibuya/engine/speech/port.py`)・決まり 11(古い 1+新しい 10)。当てたら書くファイルは 7 本(src 4=`foundation/decl/ledger_paths.py`・`foundation/text/mora.py`(新)・`runtime/clocks/speech.py`・`society/speech/port.py`/tests 3=`tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`)。前の 5 本の差分は M0-2 と 1 字も同じで、増えたのは試験 2 本の `P_MORA` の import の書き換え(→ `from shibuya.foundation.text import mora as P_MORA`)だけ。`tests/c7` に当たる道 0。
- (d) 確かめ(重いものは合図を取ってから 1 本ずつ・合図は単独の rm で返した):

| 何を | 結果 |
|---|---|
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 174 passed・21 skipped・落ちた試験 0(M0-5 と同じ) |
| slow | 2 passed |
| `tests/engine/speech`(`-m "not gpu"`) | 120 passed・落ちた試験 0・飛んだ試験 0 |
| カード(build → `cards/data.md` を単独の `git checkout --` で戻す → `--check`) | 最新(150 本)。試験 2 本の直しで変わるカードは無い(変わったカードは M0-5 の `tests/engine/proximity` の 1 枚のまま) |
| `git status --porcelain -- src`・秘密スキャン | 空・CLEAN |

## M0: 親の確かめと検収(第347・2026-11-19)

### M0(親)-1. 別の役の検収

- 判定: **受入**(高 0・中 0・低 3)。検収役はファイルを 1 本も変えていない。
- 範囲: src の差は 0。変わった 12 本は、どれも発注が許した範囲(道具の 5 本・全ファイルの表・試験 4 本・記録・カード 1 枚)。
- 書かない実行(検収役がメモリの中で): 守り 13 項は全部「同じ」(決まりも「同じ」)・手で直す一覧 0・見られなかった差し替え 0。当てたら書くファイルは 7 本(src 4= `ledger_paths.py`・`mora.py`〔新〕・`clocks/speech.py`・`port.py`/tests 3)。`port.py` には、残る `Utterance.__post_init__` のために `from shibuya.foundation.text.mora import mora_count` が足される(society → foundation の向き・循環 0)。
- 元のファイルが残る行での守り(E5-b・E8): 見本の試験で確かめた。文字列の的で差し替える形と、`mora_count` だけを読む別名で差し替える形は、どちらも止まる。残る名も読む別名は手で直す一覧に出て、厳しい当ては断る。届かない差し替えが黙って通る形は無い。`PORT` の宣言は使われ、外すと厳しい当てが断る。
- 台帳: 主な表の行は変わらず、前向きの表に `mora.py` の 1 行が入る。つなぎの台帳の JSON は書かない。当てた後の見出しの数え(今のファイル 83・台帳の道 81・見出し 84・項 367)は変わらない。
- 記録に出る文字列: `runtime/clocks/speech.py` の `"mora_rule": "engine.speech.port.mora_count(…)"` は、字面のまま残る(ランの manifest に入る値=書き換えると byte-check が動く)。ほかに、ランの出力に入る文字列の書き換えは無い。
- import の決まり: 当てた後の木で、契約は 11 のまま・例外は 18 行/16 辺 → 17 行/15 辺(消えるのは核 1 だけ・新しく載る例外 0・弱まり 0)。
- `judge.py` の宣言の直し: 受け手の試験は通る。木に差し替えを 1 つ足して崩すと落ちることを、検収役が自分で確かめた。23 本目を土台 `4a5bd30` に新旧の道具で当て直すと、書いたファイル 112 本と差分は 1 バイトも同じ(違うのは報告の 2 欄だけ)。22 本目も、新しい道具の出力が前の検収の出力と 1 バイトも同じ。
- 試験 2 本の別名の分け: 足した別名を畳むと AST は前と同じ。`P_MORA` が読むのは `mora_count` だけ。

### M0(親)-2. 検収の低と、親の答え

- 低-1(**M1 で必ず落ちる試験が 1 本在る**): `tests/engine/bridging/test_bridging_ledger.py` の負の対照(`test_negative_a_dropped_forward_row_changes_the_heading_ledger_count`)は、前向きの表の**どの行を落としても**、見出しの宣言を持つファイルを台帳の道で数えた数が 81 → 82 になることを確かめる。M1 で入る `mora.py` の行は docstring の宣言しか持たないので、その行を落としても 81 のまま=落ちる。→ **M1 の発注に入れる**(落とす行を「見出しの宣言を持つファイルの行」と「持たない行」に分け、前の行は 82 になること・後の行は見出しの数えが81 のままで、宣言の台帳の道が元の道に解けなくなることを確かめる形)。`test_the_counts_by_form` の数は変わらない。
- 低-2(全ファイルの表が変わったので、心の読みの凍結の表 `mind_world_reads_frozen.json` の `md_source.sha256` が古くなる): 親が、直した表の sha に合わせた(S6-G0 の表と順のときと同じ扱い。sha と注だけ・数と範囲は 1 字も変えていない・試験 5 本は通る)。
- 低-3(`SPLIT_DEFERRED` が空になり、延ばした行の守り 2 つは、どのデータでも通らない道になった): そのままにする。名指しの断り(割る段の順に無い行を断る)は、順を 1 本短くして今も確かめている。仕組みを残すか消すかは、段 8 の掃除で決める。

### M0(親)-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| `tests/tools/test_pkgmove.py`(not slow・`-n` なし) | 174 passed・21 skipped・failed 0 |
| 同(slow・木をまるごと写す 2 本) | 2 passed |
| `tests/tools` の残り・`tests/test_places_guard.py`・`tests/engine/speech`・`tests/engine/proximity`(not slow・`-n 2`) | 845 passed・failed 0・skipped 0 |
| 本物の木の書かない実行(`cli.py split --next`) | 守り 13 項とも「同じ」・見られなかった差し替え 0・書いていない |
| `cli.py map --check`・`cli.py contracts --stage delete --tree . --check --probe` | どちらも「同じ」 |
| `lint-imports`(作業木の src) | 11 kept・0 broken |
| 差分を読んだ(表・順・群・核 1 の消える段・`judge.py` の宣言・`PORT` の宣言・試験 2 本) | 発注と裁定のとおり・src の差は 0 |
| `tests/engine/state/test_mind_world_reads.py`(低-2 の sha を合わせた後) | 5 passed |
