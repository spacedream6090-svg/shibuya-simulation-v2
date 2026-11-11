# コードの区分の移動 段 4(割らないファイルを移す)の記録

- 指示: [返事その 7](../../../design/prompt-2026-11-09-reply7.md) §4-2 の 4(段ごとに移す・移すたびに byte-check・final が変わったら止めて報告)。
- 計画: [最終の表](../../../reference/package-map-final-2026-11-09.md) §7 の段 4。道具: [tools/pkgmove/](../../../../tools/pkgmove/README.md)(記録 [pkgmove-346](../pkgmove-346/README.md))。試験の下ごしらえ: [prep4-346](../prep4-346/README.md)。
- 順: foundation → world → economy → act → mind → society → runtime → experiments → validation → delete。`interim_bundles` の段と保留の 7 行(連絡の器 4・`engine/resolve.py`・`engine/run.py`・`engine/removed_switches.py`)は、ユーザーの答えの後。

## 段ごとの手順(親が回す)

1. 直前の commit から linked の作業木を作る(data は本体へのつなぎ)。
2. 書かない実行 `python tools/pkgmove/cli.py move --stage <段> --tree <作業木> --out-dir <置き場>` で報告を読む。
3. `--apply` で当てる(終わりに全モジュールを別プロセスで import して確かめる。落ちれば終了コード 3)。道具は、段を当てていない木の物を使う(予行と同じ)。
4. world の段からは、続けて `contracts --stage <段> --apply --tree <作業木>`(import の決まりを段ごとに差し替える)。
5. byte-check 19 構成(`--base <直前の commit> --src <作業木>/src`)。final を含む 37 欄が全部同じで終了コード 0 のときだけ進む。
6. 範囲の試験(`pytest tests --ignore=tests/c7 -m "not gpu and not slow" -n 4 --dist loadfile`)・`lint-imports`・`map --check`・カードの作り直し。
7. commit → 本体の枝を早送り → 直前の commit に安定版のタグ → 版上げの履歴に 1 行 → push → CI。

`allow --check` は、段を当てた木では「違う」になる(許可の一覧は移す前の木の走査で作った物。試験も、当てていない木でだけ比べる)。許可の一覧は段 4 の間は作り直さない。

## 段ごとの結果

| 段 | 基準 | 移した | 書き換えたファイル | import の確かめ | byte-check(19 構成 37 欄) | 範囲の試験 | lint-imports |
|---|---|---:|---:|---|---|---|---|
| foundation | aabfa0d | 36(表の行 40) | 434 | モジュール 336・落ちた 0 | 19/19 同じ・終了コード 0 | 6,777 passed・1 failed(前からの 1 本)・2 skipped・1 xfailed | 5 kept(今の決まりのまま) |
| world | fbb2287 | 48(表の行 55=move 54・empty 1) | 274 | モジュール 340・落ちた 0 | 19/19 同じ・終了コード 0 | 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed | 9 kept(古い 4+新しい 5) |
| economy | 3b807f4 | 3(表の行 4=move 3・empty 1) | 38 | モジュール 339・落ちた 0 | 19/19 同じ・終了コード 0 | 6,788 passed・1 failed(前からの 1 本)・3 skipped・1 xfailed | 8 kept(古い 3+新しい 5) |
| act | ddce87e | 3(表の行 3=move 3) | 37 | モジュール 341・落ちた 0 | 19/19 同じ・終了コード 0 | 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed | 8 kept(古い 3+新しい 5) |
| mind | d6fa47c | 25(表の行 27=move 27) | 109 | モジュール 347・落ちた 0 | 19/19 同じ・終了コード 0 | 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed | 9 kept(古い 3+新しい 6) |
| society | 66d9509 | 6(表の行 8=move 8) | 56 | モジュール 349・落ちた 0 | 19/19 同じ・終了コード 0 | 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed | 10 kept(古い 3+新しい 7) |
| runtime | 37508e6 | 35(表の行 37=move 37) | 145 | モジュール 354・落ちた 0 | 19/19 同じ・終了コード 0 | 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed | 10 kept(古い 3+新しい 7) |
| experiments | b7ab0b9 | 9(表の行 10=move 10) | 39 | モジュール 356・落ちた 0 | 19/19 同じ・終了コード 0 | 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed | 10 kept(古い 3+新しい 7) |
| validation | 454c55c | 6(表の行 6=move 6) | 24 | モジュール 355・落ちた 0 | 19/19 同じ・終了コード 0 | 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed | 10 kept(古い 3+新しい 7) |

## foundation(2026-11-11)

- 当てた行 40(move)。ファイルの移動 36・新しい頭 9・空にした頭 4。保留で当てなかった行 1。
- import の文: src 382・build 33・tests 471・tools 22・docs の記録の道具 5。頭を通す import を定義のモジュールへ向け直した文: src 3・tests 10。
- 道の文字列: 26 か所(src の表 5・点の道 6・子のプロセスへ渡すコードの import 4・斜線の道 25・`/` の結合 2)。
- 頭から除いた再輸出: `engine` 9・`llm` 22・`perception` 30(頭の `__all__` からも同じ数を除いた)。
- `class_ids.py` の鍵 92 本(値=凍結の名は変えない)。つなぎの台帳の道の表に 36 行(台帳そのものは変えない)。
- 守り 7 つは全部「同じ」(names_frozen・class_ids・道の形の名 74 種・台帳の道・許可の一覧の外・import の名・頭の `__all__`)。
- byte-check: 基準 aabfa0d の写しと作業木の src で 19 構成・37 欄すべて同じ・動いた 0・誤り 0・final が同じ 19。既定の final `c8d68704b7b0760d`・呼数 60,939。JSON は [foundation/bytecheck/](foundation/bytecheck/)。
- 性能の参考(既定 w6_v3_default・5,000 体・seed 1・1 日・mock・同じ機械): 壁時計 基準 89.7 秒/後 81.2 秒。19 構成を 6 本並列で回し、裏で範囲の試験(4 並列)も回していたので、比べない参考値。最大メモリは測っていない。
- 範囲の試験: 6,777 passed・1 failed・2 skipped・1 xfailed(50 分 47 秒)。落ちた 1 本は前からの `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(linked の作業木だけで落ちる=data のつなぎで道の相対化の 1 行)。道具の報告は [foundation/pkgmove_foundation_report.json](foundation/pkgmove_foundation_report.json)。

## world(2026-11-11)

- 当てた行 55(move 54・empty 1)。ファイルの移動 48・新しい頭 10・空にした頭 2・消えた古いディレクトリ 6(`manifest` ほか)。
- import の文: src 199・build 2・tests 411・tools 10・docs の記録の道具 10。道の文字列 42 か所(src の表 60・斜線の道 38・子のプロセスへ渡すコードの import 6・`/` の結合 4・点の道 2)。
- 頭から除いた再輸出: `agents` 6・`perception` 14。`class_ids.py` の鍵 101 本。つなぎの台帳の道の表に 47 行。
- pyproject の package-data の鍵 `"shibuya.manifest"` → `"shibuya.world.ledger"`(JSON が移る段で一緒に直す=親の仮採用)。守り 8 つは全部「同じ」。
- **import の決まりの差し替え**(`contracts --stage world --apply`・親の仮採用): 古い決まり 4(`manifest` と意味が変わった `world` を外した。「core は manifest を読まない」は契約ごと消えた)+新しい決まり 5(計画 §6-4 の 1・2・5・6・8)。ignore 22 行(計画の 28 本のうちこの段の木で両側と辺が在る物+表の外の 1 本 `shibuya.llm -> shibuya.llm.fleet`)。決まり 5 の読んでよい側に、まだ移っていない読み手 4(`cli`・`core.wage_formula`・`engine.economy_rules`・`engine.economy_stage2`=最終の置き場が economy か interfaces)。どの決まりの元の側にも入らないモジュール 4(`cli`・`world.assets`・`world.processes.circularity`・`deletion_candidates`)。報告 [world/contracts_world.json](world/contracts_world.json)。
- byte-check: 基準 fbb2287 の写しと作業木の src で 19 構成・37 欄すべて同じ・動いた 0・誤り 0。既定の final `c8d68704b7b0760d`・呼数 60,939。JSON は [world/bytecheck/](world/bytecheck/)。
- 性能の参考(既定 w6_v3_default・5,000 体・seed 1・1 日・mock・同じ機械): 壁時計 基準 76.0 秒/後 75.3 秒(19 構成を 6 本並列+裏で範囲の試験を 4 並列。比べない参考値・最大メモリは測っていない)。
- 範囲の試験: 6,787 passed・1 failed・4 skipped・1 xfailed(39 分 35 秒)。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`。道具の報告は [world/pkgmove_world_report.json](world/pkgmove_world_report.json)。
- **1 回目の当て(基準 276019c)で見つけたこと**: 範囲の試験で `test_replay_full_hash_matches_the_head_copy` が落ちた(古い commit の src を取り出して子のコードで回す試験。道具が子のコードの import を新しい道に書き換える=結果の違いではなく試験の作り)。予行で見えなかったのは、役の写しの木が git の木でなく、git が要る試験 12 本が飛んでいたため。試験を直し(fbb2287・[prep4-346 §13](../prep4-346/README.md))、git のある作業木で world から delete までの予行をやり直してから、この段を当て直した。byte-check は 1 回目(基準 276019c)も 19/19 同じだった。

## economy(2026-11-11)

- 当てた行 4(move 3・empty 1)。ファイルの移動 3・新しい頭 0・空にした頭 1・消えた古いディレクトリやファイル 1・保留で当てなかった行 0。
- import の文: src 12・build 2・tests 26・tools 0・docs の記録の道具 1。道の文字列 6 か所(src の表 1・斜線の道 2・子のプロセスへ渡すコードの import 3)。
- 頭から除いた再輸出: 無し。`class_ids.py` の鍵 6 本。つなぎの台帳の道の表に 3 行。pyproject の package-data の鍵: 変えていない。
- 守り 8 つは全部「同じ」。当てた後の import の確かめ=モジュール 339・落ちた 0。
- import の決まり(`contracts --stage economy --apply`): 古い決まり 3+新しい決まり 5=lint-imports 8 kept。ignore 22 行。まだ移っていない読み手で読んでよい側に足したもの: 決まり 5: `cli`。どの決まりの元の側にも入らないモジュール: `cli`・`world.assets`・`world.processes.circularity`・`world.processes.deletion_candidates`。報告 [economy/contracts_economy.json](economy/contracts_economy.json)。
- byte-check: 基準 3b807f4 の写しと作業木の src で 19 構成・37 欄すべて同じ・動いた 0・誤り 0(終了コード 0)。既定の final `c8d68704b7b0760d`・呼数 60,939。JSON は [economy/bytecheck/](economy/bytecheck/)。
- 性能の参考(既定 w6_v3_default・5,000 体・seed 1・1 日・mock・同じ機械): 壁時計 基準 74.6 秒/後 65.2 秒(19 構成を 6 本並列+裏で範囲の試験を 4 並列。比べない参考値・最大メモリは測っていない)。
- 範囲の試験: 6,788 passed・1 failed(前からの 1 本)・3 skipped・1 xfailed(37 分 36 秒)。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`(linked の作業木だけで落ちる)。道具の報告は [economy/pkgmove_economy_report.json](economy/pkgmove_economy_report.json)。

## act(2026-11-11)

- 当てた行 3(move 3)。ファイルの移動 3・新しい頭 2・空にした頭 0・消えた古いディレクトリやファイル 0・保留で当てなかった行 0。
- import の文: src 10・build 0・tests 20・tools 7・docs の記録の道具 1。道の文字列 3 か所(src の表 2・斜線の道 2)。
- 頭から除いた再輸出: `llm` 3。`class_ids.py` の鍵 4 本。つなぎの台帳の道の表に 3 行。pyproject の package-data の鍵: 変えていない。
- 守り 8 つは全部「同じ」。当てた後の import の確かめ=モジュール 341・落ちた 0。
- import の決まり(`contracts --stage act --apply`): 古い決まり 3+新しい決まり 5=lint-imports 8 kept。ignore 22 行。まだ移っていない読み手で読んでよい側に足したもの: 決まり 5: `cli`。どの決まりの元の側にも入らないモジュール: `cli`・`world.assets`・`world.processes.circularity`・`world.processes.deletion_candidates`。報告 [act/contracts_act.json](act/contracts_act.json)。
- byte-check: 基準 ddce87e の写しと作業木の src で 19 構成・37 欄すべて同じ・動いた 0・誤り 0(終了コード 0)。既定の final `c8d68704b7b0760d`・呼数 60,939。JSON は [act/bytecheck/](act/bytecheck/)。
- 性能の参考(既定 w6_v3_default・5,000 体・seed 1・1 日・mock・同じ機械): 壁時計 基準 75.5 秒/後 68.8 秒(19 構成を 6 本並列+裏で範囲の試験を 4 並列。比べない参考値・最大メモリは測っていない)。
- 範囲の試験: 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed(37 分 56 秒)。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`(linked の作業木だけで落ちる)。道具の報告は [act/pkgmove_act_report.json](act/pkgmove_act_report.json)。

## mind(2026-11-11)

- 当てた行 27(move 27)。ファイルの移動 25・新しい頭 7・空にした頭 1・消えた古いディレクトリやファイル 1・保留で当てなかった行 0。
- import の文: src 88・build 0・tests 135・tools 2・docs の記録の道具 4。道の文字列 23 か所(src の表 27・点の道 1・斜線の道 29・`/` の結合 1・子のプロセスへ渡すコードの import 1)。
- 頭から除いた再輸出: 無し。`class_ids.py` の鍵 48 本。つなぎの台帳の道の表に 25 行。pyproject の package-data の鍵: 変えていない。
- 守り 8 つは全部「同じ」。当てた後の import の確かめ=モジュール 347・落ちた 0。
- import の決まり(`contracts --stage mind --apply`): 古い決まり 3+新しい決まり 6=lint-imports 9 kept。ignore 41 行。まだ移っていない読み手で読んでよい側に足したもの: 決まり 5: `cli`。どの決まりの元の側にも入らないモジュール: `cli`・`world.assets`・`world.processes.circularity`・`world.processes.deletion_candidates`。報告 [mind/contracts_mind.json](mind/contracts_mind.json)。
- byte-check: 基準 d6fa47c の写しと作業木の src で 19 構成・37 欄すべて同じ・動いた 0・誤り 0(終了コード 0)。既定の final `c8d68704b7b0760d`・呼数 60,939。JSON は [mind/bytecheck/](mind/bytecheck/)。
- 性能の参考(既定 w6_v3_default・5,000 体・seed 1・1 日・mock・同じ機械): 壁時計 基準 68.4 秒/後 91.6 秒(19 構成を 6 本並列+裏で範囲の試験を 4 並列。比べない参考値・最大メモリは測っていない)。
- 範囲の試験: 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed(38 分 5 秒)。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`(linked の作業木だけで落ちる)。道具の報告は [mind/pkgmove_mind_report.json](mind/pkgmove_mind_report.json)。

## society(2026-11-11)

- 当てた行 8(move 8)。ファイルの移動 6・新しい頭 3・空にした頭 1・消えた古いディレクトリやファイル 1・保留で当てなかった行 0。
- import の文: src 19・build 0・tests 53・tools 0・docs の記録の道具 1。道の文字列 7 か所(src の表 7・斜線の道 5・`/` の結合 1)。
- 頭から除いた再輸出: 無し。`class_ids.py` の鍵 12 本。つなぎの台帳の道の表に 6 行。pyproject の package-data の鍵: 変えていない。
- 守り 8 つは全部「同じ」。当てた後の import の確かめ=モジュール 349・落ちた 0。
- import の決まり(`contracts --stage society --apply`): 古い決まり 3+新しい決まり 7=lint-imports 10 kept。ignore 43 行。まだ移っていない読み手で読んでよい側に足したもの: 決まり 5: `cli`。どの決まりの元の側にも入らないモジュール: `cli`・`world.assets`・`world.processes.circularity`・`world.processes.deletion_candidates`。報告 [society/contracts_society.json](society/contracts_society.json)。
- byte-check: 基準 66d9509 の写しと作業木の src で 19 構成・37 欄すべて同じ・動いた 0・誤り 0(終了コード 0)。既定の final `c8d68704b7b0760d`・呼数 60,939。JSON は [society/bytecheck/](society/bytecheck/)。
- 性能の参考(既定 w6_v3_default・5,000 体・seed 1・1 日・mock・同じ機械): 壁時計 基準 73.6 秒/後 62.1 秒(19 構成を 6 本並列+裏で範囲の試験を 4 並列。比べない参考値・最大メモリは測っていない)。
- 範囲の試験: 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed(40 分 36 秒)。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`(linked の作業木だけで落ちる)。道具の報告は [society/pkgmove_society_report.json](society/pkgmove_society_report.json)。

## runtime(2026-11-11)

- 当てた行 37(move 37)。ファイルの移動 35・新しい頭 5・空にした頭 2・消えた古いディレクトリやファイル 0・保留で当てなかった行 0。
- import の文: src 90・build 0・tests 234・tools 12・docs の記録の道具 5。道の文字列 32 か所(src の表 36・斜線の道 17・`/` の結合 5・子のプロセスへ渡すコードの import 4・点の道 5)。
- 頭から除いた再輸出: 無し。`class_ids.py` の鍵 48 本。つなぎの台帳の道の表に 35 行。pyproject の package-data の鍵: 変えていない。
- 守り 8 つは全部「同じ」。当てた後の import の確かめ=モジュール 354・落ちた 0。
- import の決まり(`contracts --stage runtime --apply`): 古い決まり 3+新しい決まり 7=lint-imports 10 kept。ignore 43 行。まだ移っていない読み手で読んでよい側に足したもの: 決まり 5: `cli`。どの決まりの元の側にも入らないモジュール: `cli`・`world.assets`・`world.processes.circularity`・`world.processes.deletion_candidates`。報告 [runtime/contracts_runtime.json](runtime/contracts_runtime.json)。
- byte-check: 基準 37508e6 の写しと作業木の src で 19 構成・37 欄すべて同じ・動いた 0・誤り 0(終了コード 0)。既定の final `c8d68704b7b0760d`・呼数 60,939。JSON は [runtime/bytecheck/](runtime/bytecheck/)。
- 性能の参考(既定 w6_v3_default・5,000 体・seed 1・1 日・mock・同じ機械): 壁時計 基準 160.9 秒/後 71.2 秒(19 構成を 6 本並列+裏で範囲の試験を 4 並列。比べない参考値・最大メモリは測っていない)。
- 範囲の試験: 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed(50 分 44 秒)。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`(linked の作業木だけで落ちる)。道具の報告は [runtime/pkgmove_runtime_report.json](runtime/pkgmove_runtime_report.json)。

## experiments(2026-11-11)

- 当てた行 10(move 10)。ファイルの移動 9・新しい頭 3・空にした頭 0・消えた古いディレクトリやファイル 1・保留で当てなかった行 0。
- import の文: src 24・build 1・tests 37・tools 2・docs の記録の道具 0。道の文字列 5 か所(src の表 1・子のプロセスへ渡すコードの import 1・斜線の道 2・`/` の結合 1)。
- 頭から除いた再輸出: 無し。`class_ids.py` の鍵 15 本。つなぎの台帳の道の表に 9 行。pyproject の package-data の鍵: 変えていない。
- 守り 8 つは全部「同じ」。当てた後の import の確かめ=モジュール 356・落ちた 0。
- import の決まり(`contracts --stage experiments --apply`): 古い決まり 3+新しい決まり 7=lint-imports 10 kept。ignore 43 行。まだ移っていない読み手で読んでよい側に足したもの: 決まり 5: `cli`。どの決まりの元の側にも入らないモジュール: `cli`・`world.assets`・`world.processes.circularity`・`world.processes.deletion_candidates`。報告 [experiments/contracts_experiments.json](experiments/contracts_experiments.json)。
- byte-check: 基準 b7ab0b9 の写しと作業木の src で 19 構成・37 欄すべて同じ・動いた 0・誤り 0(終了コード 0)。既定の final `c8d68704b7b0760d`・呼数 60,939。JSON は [experiments/bytecheck/](experiments/bytecheck/)。
- 性能の参考(既定 w6_v3_default・5,000 体・seed 1・1 日・mock・同じ機械): 壁時計 基準 84.2 秒/後 79.5 秒(19 構成を 6 本並列+裏で範囲の試験を 4 並列。比べない参考値・最大メモリは測っていない)。
- 範囲の試験: 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed(38 分 37 秒)。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`(linked の作業木だけで落ちる)。道具の報告は [experiments/pkgmove_experiments_report.json](experiments/pkgmove_experiments_report.json)。

## validation(2026-11-11)

- 当てた行 6(move 6)。ファイルの移動 6・新しい頭 2・空にした頭 0・消えた古いディレクトリやファイル 3・保留で当てなかった行 0。
- import の文: src 0・build 0・tests 24・tools 0・docs の記録の道具 0。道の文字列 1 か所(斜線の道 3)。
- 頭から除いた再輸出: 無し。`class_ids.py` の鍵 10 本。つなぎの台帳の道の表に 6 行。pyproject の package-data の鍵: 変えていない。
- 守り 8 つは全部「同じ」。当てた後の import の確かめ=モジュール 355・落ちた 0。
- import の決まり(`contracts --stage validation --apply`): 古い決まり 3+新しい決まり 7=lint-imports 10 kept。ignore 43 行。まだ移っていない読み手で読んでよい側に足したもの: 決まり 5: `cli`。どの決まりの元の側にも入らないモジュール: `cli`・`world.assets`。報告 [validation/contracts_validation.json](validation/contracts_validation.json)。
- byte-check: 基準 454c55c の写しと作業木の src で 19 構成・37 欄すべて同じ・動いた 0・誤り 0(終了コード 0)。既定の final `c8d68704b7b0760d`・呼数 60,939。JSON は [validation/bytecheck/](validation/bytecheck/)。
- 性能の参考(既定 w6_v3_default・5,000 体・seed 1・1 日・mock・同じ機械): 壁時計 基準 63.6 秒/後 55.1 秒(19 構成を 6 本並列+裏で範囲の試験を 4 並列。比べない参考値・最大メモリは測っていない)。
- 範囲の試験: 6,787 passed・1 failed(前からの 1 本)・4 skipped・1 xfailed(32 分 18 秒)。落ちた 1 本は前からの `test_ab7_seed1_open_matches_the_parent_report`(linked の作業木だけで落ちる)。道具の報告は [validation/pkgmove_validation_report.json](validation/pkgmove_validation_report.json)。

## delete(止めた・2026-11-11)

- 対象は 2 行(`agents/__init__.py` の再輸出を消す・`census/__init__.py` を消す)。棚卸しの表([inventory-vessels-research-heads-2026-11-09.md](../../../reference/inventory-vessels-research-heads-2026-11-09.md))の確認 1 と同じ行で、「消すのは確かめの後」としている。
- validation の commit(1a1b584)の上に当てて確かめた所まで: 当てた後の import の落ち 0・守り 8 つ「同じ」・import の決まり(`shibuya.census` を外した形)は lint-imports 10 kept。byte-check と範囲の試験は回していない。
- 変更は取り消した(commit していない)。ユーザーの答えの後に 1 段で当てる。試験の役の予行(git のある作業木)では、delete まで当てた木の範囲の試験は 6,786 passed・1 failed(前からの 1 本)だった([prep4-346 §13](../prep4-346/README.md))。
