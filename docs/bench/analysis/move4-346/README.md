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
