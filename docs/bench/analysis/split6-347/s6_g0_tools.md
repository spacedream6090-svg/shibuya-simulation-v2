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
