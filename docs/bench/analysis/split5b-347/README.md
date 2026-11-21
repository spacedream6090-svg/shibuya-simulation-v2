# 割る段 5b の記録(G0=src は変えない・道具の拡張と、割る前の試験の直し)

- 指示: 返事その 8 §1-6 の 6・§8 の 5(段 5〜7=割る)。計画: [最終の表と移す段の計画](../../../reference/package-map-final-2026-11-09.md) §7-4 の段 5b の行。割り先の正: [全ファイルの表](../../../reference/package-map-final-2026-11-09-files.md) §3・§4。
- 段 5b の実行の計画(下調べ)と、問い Q1〜Q13 への親の裁定(と親が足した決め事 6 つ)は、親の作業の置き場にある(計画 plan_stage5b・裁定 rulings_stage5b)。下の §1 に裁定の表を写した。計画の数は 5a の途中の木と模擬の木で数えたもの=G0 で 5a が全部入った木(基準 `9363b36`)で取り直した(§4・§5)。
- 5 本(`engine/commit.py`・`engine/presence.py`・`engine/calendar_shadow.py`・`engine/run.py`・`cli.py`)を割るのは G1 から。G0 では src(`src/shibuya/`)を 1 字も変えていない(astsame: 基準 `9363b36` と比べて変わった .py 0 本=[astsame_g0.json](astsame_g0.json))。
- 裁定どおり、表に無いことを決めた所は全部「親の仮採用」(全ファイルの表の注に日付・わけ・裁定の番号)。実装役が新しく決めた所は無い(道具の守りの足し方と、試験の直し方の細部だけ=§3・§6)。

## 1. 親の裁定(Q1〜Q13)と、G0 での当て方

| 問い | 裁定 | G0 で入れたもの |
|---|---|---|
| Q1 互いに読む 3 組 | presence: `DERIVE_RULES`・`DERIVE_RULE_DEFAULT` → `world/laws/presence_plan.py`/run: `_ENTRANCES`・`DEFAULT_RESPONSE_DELAY`・`DIAG_RUN_COLUMNS`・`_synonym_table_version` → `runtime/result.py`/cli: A=`write_census_files` と 3 つの `*_FILENAME` → `interfaces/cli/wire_economy.py` | 全ファイルの表 §4-12・§4-15・§4-2 の名を動かし、注(親の仮採用)。書かない実行で 3 組とも循環 0(§4) |
| Q2 表に無い 5 名 | `RUN_DEFAULT_VOCAB_VERSION`・`RUN_DEFAULT_L4_SCALE` → `runtime/result.py`/`resolve_l4_scale`・`l4_budget` → `runtime/run.py`/`_RemovedFlag` → `interfaces/cli/main.py` | §4-15・§4-2 に足して注 |
| Q3 「ほか N 個」27 名 | その行の割り先(commit 22 → act_codes・presence 2 → presence・run 3 → run) | §4-8・§4-12・§4-15 を全部の名に開いて注 |
| Q4 主な割り先 | run は `runtime/run.py`・commit は `act/commit.py` | §3 の行 234・146 の割り先の並びを入れ替えて注 |
| Q5 2 つ目以降の割り先の仮の元の名 | 146a `engine/from_words.py`・207a `engine/presence_plan.py`・234a `engine/result.py`・234b `engine/run_args.py`・87a `wire_economy.py`・141a `engine/w20_calendar_reader.py` | §3 に move の形の行 6 本(行は 338 → 344 本)。act_codes は行 291a が既に在る |
| Q6 転送 `shibuya/cli.py` の形 | (a) `if __name__ == "__main__":` の中で `shibuya.interfaces.cli.main` の `main` を読んで `raise SystemExit(main())`・docstring つき・名を結ばない | `table.forwarder_text`(§3)。文字どおりの 1 行では `-m` で `main` が走らないので docstring を入れて 5 行(全ファイルの表の行 87 の注) |
| Q7 転送を道具が書く | 入れる | E2(§3) |
| Q8 `-m shibuya.engine.run` と tests/c7 の 4 本 | 返事その 8 §1-6 の 6 のとおり=道具が機械で書き換える・手で直す所は道具が挙げた行とその前後だけ・tests/c7 は手元で回さない | E3(§3)。書かない実行で道具が挙げたのは `test_accept_table.py` の 1 か所(機械)だけ(§4-2) |
| Q9 byte-check の入口 | (a) `check.py` に解決を足し、割る道具の範囲から `tools/bytecheck/` と `tests/tools/test_bytecheck.py` を外す | E4(§3)。割る前の木で 19 構成が前と同じ値(§7) |
| Q10 手で直す読み | (a) 手で直す(src は割り先ごとに別名 1 つ・属性の読みのまま) | G1〜G3。数は §4-1 |
| Q11 群と commit | G0 → G1(commit → presence → calendar_shadow)→ G2(run)→ G3(cli) | `table.SPLIT_ORDER` の 18〜22 本目・`table.SPLIT_GROUPS["5b"]` |
| Q12 中身を見る試験 | `test_boxes:90` は凍結の名(`class_id`)で比べる・`RESULT_FILES` の `engine/run.py` はそのまま | §6 |
| Q13 | Q4 で不要 | 台帳の行 BR-MOCK-SCHEDULE-POPULATION の試験は、割った後の写しの木で `runtime/run.py` に「繋ぎ」の字があることを確かめた(§5) |

親が足した決め事 6 つのうち、G0 に入るもの: 2(割る前に直す空回りの試験=§6)・6(計画の確かめていない所=§5)。3・4・5 は G1〜G3。

## 2. 表の直し(全ファイルの表・`map.toml` は `cli.py map` で作り直した)

- §3: 行 87(cli)に転送の注・行 146(commit)と 234(run)の主な割り先を入れ替えて注・行 234 に入口の割り先の注。行 87a・141a・146a・207a・234a・234b を足した(move の形・割るかの欄=「いいえ(`元` の割り先)」)。§2 の数の節に 1 行。
- §4: 4-2(cli: Q1 の A の 4 名を wire_economy へ・`_RemovedFlag` を main へ)・4-8(commit: 「ほか 22 個」を開いた)・4-12(presence: 「ほか 2 個」を開いた・`DERIVE_RULES` の 2 名を presence_plan へ)・4-15(run: 「ほか 3 個」を開いた・Q1 の 4 名を result へ・Q2 の 4 名)。4-5(calendar_shadow)は名が揃っていた(直しなし)。行数の欄は直していない(注)。
- 5 本とも、表の名=元のファイルの頂上の名(commit 54・presence 30・calendar_shadow 36・run 63・cli 30)。割り先ごとの名の数は計画 §2-3 の数と同じ(from_words 11・act/commit 9・act_codes 34/presence 15・presence_plan 15/result 19・run 39・run_args 5/main 20・wire_economy 10/society 21・w20_calendar_reader 15)。

## 3. 道具の拡張(計画 §8 の E1〜E4)

使い方は [tools/pkgmove/README.md](../../../../tools/pkgmove/README.md) の「割る段 5b」の節。

| 記号 | 足したもの | 試験(`tests/tools/test_pkgmove.py`・ほか) |
|---|---|---|
| E1 順と群 | `table.SPLIT_ORDER` の 18〜22 本目(commit・presence・calendar_shadow・run・cli)。`SPLIT_GROUPS` を段ごとの表に(5a は前のまま・5b は G1=18〜20・G2=21・G3=22)。`map.toml` に `split_forwarders`・`split_entries` の写しを書く。表の読み手は、入口の宣言が順に載る割る行の `main` の割り先か(転送は主な割り先と同じか)を確かめる | 本物の表の 22 本・2 つ目以降の割り先の行 16 本・行 344 本(move 221)。前は飛んでいた `test_split_order_is_kept_in_the_real_tree`・`test_split_dry_run_of_the_next_row_writes_nothing_and_keeps_every_guard` が回る(次の本=commit) |
| E2 入口の転送 | `table.SPLIT_FORWARDERS`(`cli.py` → `interfaces/cli/main.py`)・型 `table.forwarder_text`。`split.make_split_plan` は元のファイルを消さずに型で書き直す。`is_done` は転送が型どおりのときだけ真・`source_rel` は転送を元と見ない・`contracts.view` は転送の行の主な割り先を最終の名と見る(転送のモジュール自身は最終の名を持たない)。名の無い `"shibuya.cli"` は書き換えない(`-m` の文脈も)。守り「入口の転送」(`split.forwarder_problems`): 字面が型と同じ・docstring・頂上で名を結ばない・頂上の文が `if __name__` の 1 つ・その中が `from <割り先> import main` と `raise SystemExit(main())` だけ・つなぎの宣言が無い・`main` が割り先の頂上に在る | 見本の木で転送を書く・済んだ・元と見ない・名を結ばない(exec で確かめる)・読み手(名は割り先へ・`-m "shibuya.cli"` と `"shibuya.cli"` は残す)・転送の字面を変えた木は済んでいない/負の対照: 型を名を結ぶ形に差し替えても守りが止める・形の各部分 4 つ/入口の無い元の転送の宣言は断る/`contracts.view` の見本(型どおり=最終の名・型と違う=古い置き場) |
| E3 入口の移し | `table.SPLIT_ENTRIES`(`engine/run.py` → `interfaces/cli/run_args.py`)。`if __name__ == "__main__":` は宣言した入口の割り先へ(読む名の割り先と食い違う宣言・宣言の無い入口は断る)。名の無い点の道は `-m` の文脈(文字列の中の `-m <名>`・並びや呼び出しの引数で 1 つ前が `"-m"`)なら入口の割り先へ、それ以外は書き換えず「手で直す一覧」へ(`strings.split_nameless`=段 6 の E8 はここで宣言の表を先に引く形で足す)。記録の文(ASCII の外の字を含む文)の中のものは前と同じく書き換えず、一覧にも出さない。文字列の中の手で直す所(コードの文字列の import を含む=前は報告の `skipped_strings` に入るだけだった)も「手で直す一覧」に入れる。`importcheck` は在る入口(`ENTRY_MODULES`=`shibuya.cli`・`shibuya.interfaces.cli.run_args`)ごとに `python -m <入口> --help` | 見本の木で入口と `-m` の文字列(並びと文の中)・名つきの点の道/負の対照: `-m` でない名の無い点の道=手で直す(strict は断る)・食い違う宣言・宣言の無い入口/入口ごとの `--help`(壊れた入口で落ちる) |
| E4 byte-check の入口 | `tools/bytecheck/check.py` の `resolve_run`(読んだ `shibuya` の包みに `interfaces/cli/main.py` が在ればその `run`・無ければ `shibuya.cli.run`。在るかはファイルで見る=無い包みを import しに行かない)。割る道具は `split.SPLIT_EXCLUDE_PATHS`(`tools/bytecheck/`・`tests/tools/test_bytecheck.py`)を書き換えず、書き換えたはずの所を報告の `excluded_sites` に出す | 見本の木で範囲の外を書き換えない/負の対照: 範囲の外の一覧を空にすると書き換わる。`test_bytecheck.py` の `test_resolve_run_takes_the_split_entry_when_it_exists`(割る前の木=`shibuya.cli.run`・割った後の木=`interfaces.cli.main.run`・読んだモジュールに転送も無い包みも入らない) |
| ほか | `split.STRING_EXCLUDE` に `tools/c8/c8lib.py` の `scan_engine_ablation_ids` を足した(元の置き場の道 `"engine/presence.py"` と比べる字面=今の道へ書き換えると、割った後に計画実行層の ablation_id を拾わなくなる。`tests/c8/test_c8lib.py` が大きな音で落ちる側だった=§6 の洗い直しで見つけた) | 書かない実行で c8lib が書き換わらないことを確かめた(§4) |

`slow` の試験を広げた(`test_split_5a_5b_in_memory_keeps_the_import_rules_to_the_end`=本物の木で残りの本=5b の 5 本を順に当て、どの本でも守りが「同じ」・終わりに契約 11・単位 foundation と interfaces と決まり 2 が言える・読んでよい側に足した古い読み手 0・`cli.py` は転送で済んだ本)。

## 4. 書かない実行(本物の木=基準 `9363b36` の上の G0 の木・`cli.py split --through all`・メモリの中で順に当てた)

| 本 | 守り | 手で直す(試験の直しの前 → 後) | 割り先(新/在る) | 鍵 | 台帳の道 | 道の文字列(記号) | 頭 | 消す | 写さなかった import |
|---|---|---|---|---|---|---|---|---|---|
| 18 commit | 12 個とも「同じ」(決まりも「同じ」) | 26 → 26 | act/commit・from_words(新)・act_codes(在る) | 3 | 1 | 0 | — | engine/commit.py | 0(再輸出 `UNDEFINED_ACTION` は割り先に写さない=読み手は元の定義へ) |
| 19 presence | 同上 | 1 → 0 | presence・presence_plan(新) | 4 | 1 | src の表 2・斜線 5(4) | — | engine/presence.py | 0 |
| 20 calendar_shadow | 同上 | 2 → 2 | society/calendar_shadow・w20_calendar_reader(新) | 2 | 1 | src の表 1・斜線 1(1) | — | engine/calendar_shadow.py | 0 |
| 21 run | 同上 | 11 → 6 | runtime/run・result・interfaces/cli/run_args(新) | 3 | 1 | src の表 3・斜線 10・入口 1・コード 4(15)→〔G0 の直しの後〕src の表 3・斜線 5・入口 1・コード 4(10) | interfaces・interfaces/cli | engine/run.py | 1(`import warnings`=計画どおり) |
| 22 cli | 13 個とも「同じ」(守り「入口の転送」を含む) | 17 → 6 | interfaces/cli/main・wire_economy(新) | 2 | 1 | src の表 4(0)→〔G0 の直しの後〕src の表 4・コード 28(14) | — | なし(転送) | 0 |

〔G0 の直しの後=§10〕守り・手で直す件数(40=26・0・2・6・6)・宣言の外の弱まり 0・循環 0 は同じ。道の文字列は、試験の鍵(`split_files` ほかの第 1 引数)を書き換えなくなった分(presence の本 斜線 5 → 3・run の本 斜線 10 → 5)が減り、コードの文字列の `from shibuya import cli` の 14 か所(cli の本 コード 28)が増えた。

- 例外の本数の見込み・循環・宣言の外の弱まりは §5。宣言の外の弱まりは 5 本とも 0(宣言どおりの弱まりも 0)。循環 0。
- 範囲の外(E4): run の本で `tests/tools/test_bytecheck.py` の 4 か所(偽のエンジンの道と名)を書き換えずに残した。
- 名の無い `"shibuya.cli"` を残した所(転送の名): `tests/tools/test_night5070.py`・`tools/c8/ensemble.py` の 2 か所。
- 手で直す一覧(試験の直しの後の 40 件)は全部「別名の読みの割り先が 1 つに決まらない」の形: commit 26(src 5=`act/activity.py`・`act/intent.py`・`engine/run.py`・`runtime/systems/act.py`・`runtime/systems/judge.py`・tests 21)・calendar_shadow 2(`interim_bundles/calendar_self.py`・`test_calendar_shadow`)・run 6(`runtime/systems/assemble.py`・tests 5=`discard_probe`・`test_10a_review_fixes`・`test_response_delay`・`test_sim_time_T`・`test_cli_vocab_version`)・cli 6(tests 6=`_stage2_outside`・`test_census_out`・`test_classical_policy`・`test_resume_10d`・`test_t3_manifest`・`test_cli`)。差し替え(monkeypatch)の効く先を保つ注意は計画 §7-1 のとおり(G1〜G3)。

### 4-1. 計画の数との違い

| 数 | 計画 | G0 の木 | わけ |
|---|---|---|---|
| 手で直す読み | 約 51(commit 26・presence 1・calendar_shadow 2・run 9・cli 14) | 直す前 57(26・1・2・11・17)→ 直した後 40(26・0・2・6・6) | 道具は import の文ごとに数える(計画はファイルごと=`test_norm_meter`・`test_near_tiebreak` の 2〜3 文)。run の 11 には、E3 で「手で直す」になった名の無い点の道(`test_boxes:90`)を含む。G0 の試験の直し(§6)で 17 件が機械で済む形になった |
| 例外 | 5a の後 21 行・21 辺 → commit で 19 | 5a の後 22 辺・延べ 30 行 → commit の後 20 辺・延べ 26 行(#9・#15 が消える)→ 終わりまで同じ | 計画の 5a の残りは模擬の木(1 辺ずれる)。本物の数は 5a の記録の終わりの数(22・30)と同じ |
| 契約 | 11 | 11(古い 2+新しい 9)・5 つの木の全部で kept | 計画どおり |
| c7 | 4 本・4 か所(Grep の数) | 道具が挙げたのは `test_accept_table.py` の 1 か所だけ(機械) | ほかの 3 か所は文字列の定数の外(道具が挙げない=開いていない) |

### 4-2. tests/c7 の 4 本(裁定 Q8・開いたのは道具が挙げた行とその前後だけ・回していない)

- `test_accept_table.py`: 記号 `TIME_V`(行 29)の文字列 `Command being timed: "python -m shibuya.engine.run"`(`time -v` の出力の見本)。`-m` の文脈なので、道具が機械で `python -m shibuya.interfaces.cli.run_args` に書き換える(run の本)。手で直す所 0。
- `test_presence_yardstick.py`・`test_seed_exchangeability.py`・`test_salt_compare_10f.py`: 道具はどの本でも挙げない(import の文・文字列の定数・道の連なりのどれにも当たらない=注か docstring の中と見込む。開いていない)。手で直す所 0。
- 割った後の確かめは、裁定 Q8 のとおり AST で読めること・書き換えた名が割り先に在ること(import せずに)・CI。

## 5. 計画の「確かめていない所」(親の決め事 6)

1. **依存の図と grimp**: 割る前の本物の木と、5 本を 1 本ずつメモリの中で当てた 5 つの木(src だけを書き出した写し)で、道具の AST の辺(関数の中と `TYPE_CHECKING` の下を含む全部の import)と grimp の直の辺が同じ(1257 → 1263 → 1268 → 1269 → 1300 → 1306・違い 0)。
2. **import-linter の契約のクラスで決まり 1〜10**: 同じ 6 つの木で、道具が作る契約(`contracts --probe` と同じ `ignoreprobe`=lint-imports と同じクラス)が全部 kept。例外は全部効いている(割る前 30 行・22 辺/commit の後と以降 26 行・20 辺)・効いている例外だけを残しても kept。単位 interfaces は run の本で言えるようになる(決まりが強まる側)。読んでよい側に足した古い読み手(`shibuya.cli`・`shibuya.engine.run`)は run の本で `engine.run`、cli の本で `shibuya.cli` が消え 0 になる。決まり 4(`act.apply`・`act.ops`)は段 6 まで言えない(前と同じ)。
3. **植えた道の試験 2 本**: `test_body_guard` の走査は `world/body/`(体の層の置き場)・ほかの持ち主・持ち主の口だけで道の扱いを変える=`engine/presence.py` と `world/laws/presence.py` は同じ扱い。`test_cp2_transfer_only_writer` の負の対照は (道, 関数) の宣言の表(`economy/ledger.py`・`engine/resolve.py` だけ)で見る=どちらの道でも宣言の外。道具は植えた道の鍵と期待を同じ道へ書き換える(書かない実行の差分)。`STRING_EXCLUDE` に足す必要は無い。
4. 台帳の行 BR-MOCK-SCHEDULE-POPULATION(Q4 で入れ替えた後): 写しの木で `runtime/run.py` に「繋ぎ」の字が在り、台帳の道の表が `src/shibuya/runtime/run.py` → `src/shibuya/engine/run.py` を持つ(試験の道は道具が `runtime/run.py` へ書き換える)。

## 6. 割る前に直した試験(親の決め事 2・計画 §7-2・裁定 Q12・洗い直し)

`tests/_places.py` に、名の定義のファイルを表から引く口を足した: `split_files(old, names=None)`(割る行 `old` の名を頂上で定義する今のファイル。割る前は元のファイル 1 本、割った後は表の名の割り先。入口の転送は入らない)・`split_source`(その字面をつないだもの)・`split_module_names`(そのモジュールの名)。割る前の木では前の確かめと同じ範囲を返し、書き出した割った後の写しの木では割り先を返す(転送を除く)ことを確かめた。

| 試験 | 前 | 直し(割る前は同じ範囲) | 割った後に起きていたこと |
|---|---|---|---|
| `test_wage_occupation`・`test_defect_fixes_1103`・`test_seat_release_2_4` | `inspect.getsource(cli)` に消した旗が無い | `PL.split_source("cli.py")` | 転送を読み、何も確かめずに通る |
| `test_norm_meter`・`test_near_tiebreak`(2 本) | `open(cli.__file__)`・`open(RUN.__file__)` | `split_source("cli.py")`・`split_source("engine/run.py")` | 否定は空回り・肯定は落ちる |
| `test_mr65_guards` | `module_names(CLI)` を禁じる | `split_module_names("cli.py")` | 転送の名だけを禁じ、interfaces の割り先を見落とす |
| `test_mr65_review_fixes` | `rel_of(CLI)` が台帳の今の道に無い | `split_files("cli.py")` のどれも無い | 転送の道は常に無い=空回り |
| `test_places_guard`(3 本) | `cli` を割らないファイル・在るモジュールの例に使う | keep の行の `economy/ledger.py`(表の行を抜く試験・解けない名の試験)・割らない `act.intake.parser`(名の元の置き場) | cli が割られる(別名 `cli` は「手で直す」になる) |
| `test_two_phase`(`_hot_paths`) | `"engine/run.py"`・`"engine/commit.py"`・(5a の G5 で親が手で足した)`"world/model/scene_hash.py"` | `split_files("engine/run.py", ("run_day", "RunResult"))`・`split_files("engine/commit.py", ("arbitrate_resources", "intents_from_responses"))`・`split_files("engine/change_detect.py", ("ChangeDetector", "b4_block_raw", "b4_block_hashes"))`。〔G0 の直し・親の直し〕個体数ぶんのループを探す検査だけは、割る 3 行の名の全部の割り先(`split_files(鍵)`)も見る(`_loop_scan_paths`=割る前は前と同じファイル+`agent_codes`・割った後は 9 本=写しの木でループ 0)。「逐次ループ宣言」の検査は名で引く形のまま | 主な割り先 1 本だけになり、片方の名が P4 の検査から外れる。CLI の引数の口 `run_args` と語彙の定数(`act_codes`・`agent_codes`)はホットパスでない(「逐次ループ宣言」の確かめには入れない=宣言が無い) |
| `test_presence_executor` | `engine/presence.py` の字面に乱数の語が無い | `split_source("engine/presence.py")` | presence_plan(`_mix64` ほか)が外れる |
| `test_activation_10e`・`test_calendar_sites` | `not hasattr(RUN/_PRESENCE, 消した名)` | `split_files` の全部のモジュールで見る | 割り先の 1 つしか見ない |
| `test_boxes`(裁定 Q12) | `__module__ == "shibuya.engine.run"` | `class_id(...) == "shibuya.engine.run._RunDayLocals"`(凍結の名) | 道具の書き換えでは主な割り先の名になるだけで、注の意図(ハッシュに入る名を変えない)を見ない |
| `test_rules_table_schema` | 読み手の集合に `"engine/run.py"` | `split_files("engine/run.py", ("RunResult",))`(写しの木で読み手が `runtime/result.py` と確かめた) | 道具は主な割り先 `runtime/run.py` へ書き換え、落ちる(計画では G2 で手で直す 1 本だった) |
| **洗い直しで見つけた 15 本**: `test_classical_policy`・`test_classical_social`・`test_meal_bundle_2b`・`test_meal_gate_per_hour`・`test_memory_recall`・`test_memory_record`・`test_presence_exit_walk`・`test_relations`・`test_relations_8b`・`test_relations_tenure`・`test_store_choice`・`test_store_memory`・`test_wom`・`test_coef_removed_or_armed`・`test_p_see_activity` | `(SRC / "cli.py")` か `Path("src/shibuya/cli.py")` の字面に旗が在る/無い | `PL.split_source("cli.py")` | 道具は根の `cli.py`(ディレクトリの無い道)を書き換えない=割った後は転送を読む。否定の確かめ 4 本(`test_relations_tenure`・`test_coef_removed_or_armed`・`test_p_see_activity`・`test_presence_exit_walk` の半分)は空回り、肯定 11 本は落ちる。計画 §7-2 に無かった |

- 直す前と後で同じ 32 ノードを回した: 前 32 passed・0 skipped → 後 32 passed・0 skipped(`-p no:cacheprovider`・`-n` なし)。〔G0 の直し・検収 低-4〕前 33・後 33(下の 1 ノードを含む)は**割る前の木での比べ**。割った後の形は、書かない実行の差分と §10-1 の確かめ(割った後の写しの木で鍵を引く・回せる試験を回す)で見た。G0 の最初の形は、道具が鍵の字面を割り先へ書き換えて割った後に落ちる形だった(検収 高-1=§10-1 で直した)。`test_places_guard::test_unresolvable_shibuya_names_are_hits` は、最初の直しで別名 `cli` の 3 つ目の使い方を見落とし(決まりの束で NameError=大きな音で落ちた)、同じ形で直した。この 1 ノードの前は、基準の版のファイルを読んでその関数を直に呼んで passed(同じ版の 2 本も passed)・後は passed(33 ノードで前 33・後 33 passed・0 skipped)。
- 使わなくなった import を外した(`test_seat_release_2_4` の `inspect`・`test_p_see_activity` と `test_presence_exit_walk` の `Path`・`test_norm_meter` の `RUN`・`test_mr65_*` の `CLI`・`test_calendar_sites` の `_PRESENCE`)。
- 同じ見方で、道の字面を持つほかの試験も見た: `test_salt_seed_split_10f`(`("engine/run.py", "run_salt_for")`=同じ組の名の割り先へ=道具が正しく当てる)・`test_state_checks_10f`・`test_state_ledger_10b`(古い字面の負の対照=どちらでも同じ)・`test_calendar_shadow:68`(src の表と同じく同じ組の名で当てる)・`test_places_guard` の固定の一覧(`STRING_EXCLUDE`)・`tools/c8/sensitivity.py`(構築の段の表=当たらない)。直すものは無かった。

## 7. byte-check(E4 の後・割る前の木)

- 基準 `9363b36`(5a が全部入った本体の頭)・比べる側=G0 の作業の木の src(src は基準と同じ)・道具は G0 の道具(`resolve_run` の入った `check.py`)で両側を回した。19 構成・37 欄すべて同じ 19・比べていない欄 0・動いた 0・誤り 0・final が同じ 19 → 同じ(終了コード 0)。壁時計 基準の側 223 秒・比べる側 211 秒・全体 435 秒(6 本並べ)。記録は [bytecheck_g0_pre_split/](bytecheck_g0_pre_split/)。
- 割る前の木には `interfaces/cli/main.py` が無いので、両側とも `shibuya.cli.run` を呼ぶ(無い包みを import しに行かない=読むモジュールの digest `src_files` も前と同じ)。割った後の側(G3)で `interfaces.cli.main.run` を呼ぶことは、見本の木の試験で確かめた(§3 の E4)。
- 合図のファイルを取ってから回し、終わってから単独のコマンドで消した。
- 〔親の確かめ・第347〕親も木の側の道具で回した(基準 `9363b36`・記録は [bytecheck_G0_parent/](bytecheck_G0_parent/)): 19 構成・37 欄すべて同じ・動いた 0・誤り 0・436 秒・既定の final と呼数は前と同じ。前の `check.py` が出した 5a の G45 の記録(同じ src)と 19 構成の全欄を突き合わせ、違うのは時間の 3 欄と置き場の診断の 3 欄(`src_is_worktree`・`outside_reads`・`outside_reads_n`)だけ。G0 の直しは src も `tools/bytecheck/` も変えていないので、byte-check は回し直していない。

## 8. 試験の結果(作業の木・2026-11-18・重いものは 1 本ずつ・範囲の全体の試験は回していない)

| 何を | 結果 |
|---|---|
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 114 本=94 passed・20 skipped(段 4 を当てた後の木で飛ぶ試験=前と同じ種類)・落ち 0。前は飛んでいた割る段の 2 本が回る |
| 同 `slow`(残りの 5 本を順に当てる) | 1 passed |
| `tests/tools/test_bytecheck.py` | 124 passed |
| 直した試験のノード(§6) | 前 33 passed・0 skipped → 後 33 passed・0 skipped |
| 直した試験のファイルの全部(28 本・`-n 2`・`-m "not slow"`) | 391 passed・0 skipped |
| 置き場で範囲が決まる決まりの束(c8 の写しの一致を先に・`tests/c8/test_c8lib.py`・`tests/engine/time`・`state`・`bridging`・`systems`・`tests/test_places_guard.py`・`-n 2`) | 346 passed・0 skipped(1 回目は `test_places_guard` の NameError=§6 の見落とし。直して 2 回目) |
| `lint-imports` | 11 kept・0 broken |
| `cli.py contracts --stage delete --tree <作業の木> --check --probe` | 作り直しと同じ・契約 2+9・例外 30 行 22 辺(全部効く)・全部 kept |
| `cli.py map --check`・`tools/repo_guide/build.py --check` | 同じ・最新(カードは作り直し、`data.md` だけ戻した) |
| astsame(src・基準 `9363b36`) | 変わった .py 0 本 |
| 秘密の走査(変えたファイルと新しいファイル) | CLEAN |

- 〔親の確かめ・第347〕範囲の全体の試験: 6,942 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる `test_ab7_seed1_open_matches_the_parent_report`)・21 skipped・1 xfailed・39 分 30 秒(`-n 4`)。前の群(6,926 passed・23 skipped)との差 +16 passed・−2 skipped は、足した道具の試験 14 本(test_pkgmove 13・test_bytecheck 1)と、また回るようになった 2 本の分。
- G0 の直しの後の結果は §10-4。

## 9. 計画と違った所・止まる所・G1〜G3 に送ること

### 9-1. 計画と違った所

1. **字面を読む試験が計画の数より多かった**: 計画 §7-2 の 10 本前後のほかに、根の `cli.py` を道の字面で読む試験 15 本(道具は ディレクトリの無い道 `cli.py` を書き換えない=割った後は 5 行の転送を読む)と、`test_places_guard` の 3 か所目・`test_rules_table_schema`(計画では G2 で手で直す)を G0 で直した。直し方は計画の「名の定義のファイルを表から引く」と同じ形(§6)。
2. **`tools/c8/c8lib.py` の元の道の字面**: 道具が今の道へ書き換えると、計画実行層の ablation_id を黙って拾わなくなる(`tests/c8/test_c8lib.py` が落ちる側)。`split.STRING_EXCLUDE` に足した(5a の固定の一覧と同じ扱い)。
3. **手で直す読み**: 計画 51 件に対し、G0 の直しの後で 40 件(§4-1)。src は計画の 7 本のうち `act/activity.py`・`act/intent.py`・`runtime/systems/{act,judge,assemble}.py`・`interim_bundles/calendar_self.py`・`engine/run.py`(commit の別名 `C`)の 7 本で同じ。
4. **例外の本数**: 計画は模擬の木で「5a の後 21 辺 → 19 辺」。本物の木では 22 辺 → 20 辺(#9・#15 が消える=計画の狙いと同じ。数の 1 ずれは計画の模擬の木のずれ)。
5. **c7**: 道具が挙げたのは 1 か所(計画は Grep で 4 か所)。ほかの 3 本は道具の書き換えに当たらない。
6. **道具の厳しさを足した所**(5a の本は済んでいるので影響なし): 文字列の中の「手で直す」(コードの文字列の import を含む)を「手で直す一覧」に入れる(前は報告の `skipped_strings` に入るだけ)・`if __name__ == "__main__":` のある割る行に入口の宣言が無ければ断る。

### 9-2. 止まる所・親の判断を待つ所

- 無し(表に無いことを新しく決めた所は無い。裁定の外で決めたのは試験の直しの細部=ホットパスの名の選び方(計画 §7-2 の 4 名と、change_detect の `ChangeDetector`・B4 の 2 関数)と、`test_places_guard` の例のモジュール(`economy/ledger.py`)だけ。どちらも試験の中)。
- 〔G0 の検収 低-5〕上の 2 つと slow の試験の名前の変更は、検収で妥当とされ、親がそのまま採った。
- 〔G0 の直し〕5a の済んだ本のコードの文字列に、元のモジュールを読む import の残りが 2 本 3 か所あった(§10-2)。実装役は直さず、親が裁定した(§11-2)。

### 9-3. G1〜G3 に送ること

- 手で直す読み 40 件(§4)。src の 7 本は「割り先ごとに別名 1 つ・属性の読みのまま」(Q10)。差し替え(monkeypatch)の先が変わる試験(`test_response_delay`・`test_resume_10d`・`_stage2_outside` ほか)は、割った後に「差し替えを外すと落ちる」を 1 回ずつ確かめる(親の決め事 3)。`test_classical_policy` の `hasattr(cli, "build_parser")`(無い名)は G3 で手で直す。
- G2(run): `python -m shibuya.interfaces.cli.run_args` の使い方の表示の `prog` が `run.py` → `run_args.py` に変わる(ランの結果ではない・親の決め事 4)。`tests/c7/test_accept_table.py::TIME_V` は道具が機械で書き換える(確かめは AST と CI)。`importcheck` が `-m shibuya.interfaces.cli.run_args --help` を回すようになる。
- G3(cli): 転送の後に `python -m shibuya.cli --help` と `python -m shibuya.cli --llm mock`(既定のラン 1 本)の final と呼数が前と同じこと(親の決め事 5)。byte-check の比べる側は `interfaces.cli.main.run` を呼ぶ(§7)。見ておくこと: (a) `tests/_places.py` の元の置き場は、転送 `cli.py` が残る間は `interfaces/cli/main.py` の元の道をその今の道とする(0 バイトの頭が残る形と同じ枝=元の道が重ならない)。根の置き場で範囲を決める試験は無い(`rels_from` は根を断る)が、割った後の範囲の束で確かめる。(b) 台帳の道の表は `interfaces/cli/main.py` → `cli.py` を足す。転送のファイルの今の道も `cli.py` なので、ファイルの全部を台帳の道へ引く検査があれば重なる(転送に宣言は無い=宣言の走査は重ならない)。(c) docs の記録の道具(cli の本で 5 本=`byte_check_10e.py`・`wave2_bytecheck.py` ほか・run の本で 3 本)は import だけ書き換わる(親の決定 7)。`tests/tools/test_bytecheck.py` が読む `byte_check_10e.py` は関数の中の import で、試験は AST と関数だけを読む。(d)〔G0 の検収 低-3〕`_stage2_outside.use_outside_bundle` が差し替える台帳の型 `Ledger`・`_HouseholdWalletLedger` は、割った後に 2 か所で読まれる(作る側=`wire_economy.build_ledger_bundle`・表示の札を `isinstance` で決める側=`main.main`)。差し替えの先は wire_economy で、main の `isinstance` は部分型でも真なので結果は変わらない見込み。親の決め事 3(差し替えを外すと落ちる)で 1 回確かめる。

## 10. G0 の直し(検収=条件つき受入の高 2・低 3 と親の直し 1・2026-11-18・src と `tools/bytecheck/` は変えていない)

### 10-1. 高-1: 試験の鍵の字面を書き換えない

- 道具(`strings.TABLE_KEY_CALLS`・`strings.is_table_key`): `tests/_places.py` の割る行の口(`split_files`・`split_source`・`split_module_names`・`_split_names`)の呼び出しの第 1 引数(か `old=`)は、対応表の割る行の鍵(元の道=値そのもの)なので書き換えない。呼び出しの形で見る(新しい試験の鍵も漏れない)。書き換えなかった所は報告の `table_key_sites` に出す(書かない実行の要約にも)。
- 負の対照(`test_split_keeps_the_table_keys_of_the_places_helpers`): 鍵が 1 つの割り先だけを指す見本(名の指定なし・名 1 つ)で、規則が在ると書き換わらず、規則を外すと主な割り先へ書き換わる。ほかの道の文字列は前と同じく書き換える。
- 書かない実行: `table_key_sites` は commit 6・presence 2・calendar_shadow 0・run 14・cli 26(同じ鍵が本ごとに出る)。差分に `split_files(…)`・`split_source(…)`・`split_module_names(…)` の行の書き換えは 0。`path_string_sites` と鍵の記号の重なり 0(検収の 7 か所と `test_two_phase` の分は出ない)。
- 割った後の形で付いていくことの確かめ(低-4): メモリで 5 本を当てた後の木を、scratch に 1 本だけ書き出した(`r8\s5b\after_full`=src・tests・tools・docs・pyproject。data は写していない)。
  - 写しの木の `tests/_places.py` で、試験の中の呼び出し 33 か所(`split_files`・`split_source`・`split_module_names`)を直に引いた: 誤り 0。鍵は元の道のままで、割り先の一覧が返る(`cli.py` → `interfaces/cli/main.py`・`wire_economy.py`/`engine/run.py` → `run_args`・`result`・`run`(名の指定で `result` か `result`・`run`)/`engine/presence.py` → `presence`・`presence_plan`/`engine/commit.py`(2 名)→ `act/commit`・`from_words`/`engine/change_detect.py`(3 名)→ `mind/system1/change_detect`・`world/model/scene_hash`)。
  - 写しの木で回せた試験(G0 で直した 33 ノードのうち、割るモジュールの読みが src の手直しを待たない 10 本): 9 passed・1 skipped(`test_classical_social` は data が無くて飛ぶ)。回せたのは `test_rules_table_schema`(読み手の集合=`runtime/result.py`)・`test_classical_policy`・`test_memory_record`・`test_relations_8b`・`test_coef_removed_or_armed`・`test_p_see_activity`・`test_places_guard` の 3 本。
  - 回せなかった 23 本は、読み込みで `cannot import name 'commit' from 'shibuya.engine'`(src の手で直す読み=G1 で直す 26 件)で止まる。これらは上の「直に引く」で見た。`test_two_phase` のループを探す範囲(下の 10-3)は、写しの木の `_places` で引いて 9 本・個体数のループ 0・ホットパスの 6 本とも「逐次ループ宣言」あり。写しは `test_two_phase` の最後の直し(ループを探す範囲の鍵を割る口の第 1 引数に字面で書く)の前に書き出した。最後の形の鍵が書き換わらないことは、書き出しの後の書かない実行の `table_key_sites`(commit の本の 6=`_hot_paths` の 3 と `_loop_scan_paths` の 3)で確かめた。

### 10-2. 高-2: コードの文字列の `from <包み> import <割るモジュール>` を見落とさない

- 道具(`strings.code_import_hits`): tests と tools の文字列を選ぶとき、コードの文字列の中の import が割るモジュールを読む形(`from <包み> import <葉>`・`from <モジュール> import <名>`・`import <モジュール>`)も拾う(前は点の道と斜線の道の字面だけ)。コードとして読めれば import の書き換え(5a の `alias_dests` を通して、別名の読みの割り先が 1 つなら機械で・決まらなければ「手で直す一覧」)、コードとして読めない文字列(シェルの文)と f 文字列の部分の中のものは「手で直す一覧」。黙って残る形は 0。
- 負の対照(`test_split_sees_code_strings_that_import_the_split_module_from_its_package`・4 つの見本): 属性の読みが 1 つの割り先=機械で書き換える・別名つき(`from <包み> import <割るモジュール> as X`)=機械で・2 つの割り先に割れる=手で直す一覧(strict は断る)・シェルの文の中=手で直す一覧。選ぶ口を前の形に戻すと、どれも書き換えも一覧も無く残る。
- 検収の 14 か所(指摘の一覧の 13 か所+`tools/instruments/batch_width_gauge.py:209`。指摘の「15」は数え違いと見る=一覧は 14 行)の行き先(cli の本・書かない実行):

| か所 | 行き先 |
|---|---|
| `tests/engine/batching/test_conductor_windows.py:199`・`calendar/test_calendar_shadow.py:348`・`clock/test_tm3_step_scope.py:218`・`clock/test_tm4_regional_clock.py:282`・`decision/test_j0_cli.py:23`・`memory/test_m0_cli.py:26`・`memory/test_mr65_grain_and_cli.py:64`・`proximity/test_runs.py:241`・`:255`・`speech/test_speech_cli.py:28`・`test_env_and_sections_10f.py:288`・`test_removed_switches_346.py:34`・`test_resume_10d.py:196`・`tools/instruments/batch_width_gauge.py:209` | 14 か所とも機械で書き換え(`from shibuya.interfaces.cli import main as cli`=読む名は `main`・`run` で割り先は 1 つ)。手で直す一覧 0 |

- 当てた後の木(メモリ)で、コードの文字列の中の import が割った 5 本の元のモジュールを読む所の残り: 0(tests/c7 と道具の見本を除く)。手で直す件数は 40 のまま(26・0・2・6・6)。`from shibuya.engine.run import run_day` の形の 4 か所(run の本)は G0 から機械で書き換わっていた。
- 5a の済んだ 17 本の残り(同じ見方で今の木を数えた・実装役は直していない=親の裁定は §11-2): 2 本 3 か所。
  - `tests/build_pop/test_w21_stage8_9.py:438`(`from shibuya.llm import fleet`・`import shibuya.llm.fleet`): llm の字の検出器の試験の植えた文(`split.STRING_EXCLUDE` の記号=字面そのものを確かめる材料)。
  - `tests/engine/systems/test_fix_guards.py:186`(`import shibuya.agents.state`): 書きの許可の検査の負の対照の植えた文(コードを走査するだけで実行しない)。5a では、コードの文字列の import の「手で直す」が報告の `skipped_strings` に入るだけで一覧に出なかった(G0 で一覧に入れる形にした)ので、黙って残った形。

### 10-3. 親の直しと低の指摘

- 親の直し(`test_two_phase`): 上の 10-1 の最後と §6 の表。ループを探す範囲の鍵も割る口の第 1 引数に字面で書いた(並びの字面にすると道として書き換わる)。
- 低-1(`test_negative_forwarder_guard_branches_stop_one_by_one`): 守り「入口の転送」の 2 つの枝を、それぞれほかの枝に当たらない見本で落とす。(1) 型そのものの docstring に `expedient:` の宣言=字面と形は型どおりで「つなぎの台帳の宣言がある」だけが出る (2) 割る元に `main` が無い見本の行=「呼ぶ main が割り先 ui/main.py の頂上に無い」だけが出る(本物の表は読み込みで `main` の割り先を確かめるので、この形は表の外の見本だけ)。どちらも止めた文は 1 つだけ。
- 低-2(`test_split_groups_cover_the_split_order_in_order`): `SPLIT_GROUPS` を段の順・群の順につなぐと `SPLIT_ORDER` の 1〜22 本目と同じ(重なりと抜けが無い)。5b の群の中身も確かめる。
- 低-3・低-5: §9-3 (d)・§9-2。低-4: §6。

### 10-4. 直した後に取り直した数と試験(作業の木・重いものは 1 本ずつ・byte-check と範囲の全体は回していない)

| 何を | 結果 |
|---|---|
| 書かない実行(`split --through all`) | 5 本とも守り全部「同じ」・手で直す 26・0・2・6・6(計 40=前と同じ)・宣言の外の弱まり 0・循環 0・範囲の外は run の本の `test_bytecheck` 4 か所(前と同じ)・`table_key_sites` 6・2・0・14・26・c7 は `test_accept_table.py` の 1 か所(前と同じ) |
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 121 本=101 passed・20 skipped(足した 7 本の分だけ増えた)・落ち 0 |
| 同 `slow` | 1 passed |
| `tests/tools/test_bytecheck.py` | 124 passed |
| 直した試験のファイルの全部(28 本・`-n 2`) | 391 passed・0 skipped |
| 決まりの束(c8 を先に・`-n 2`) | 346 passed・0 skipped |
| `lint-imports`・`contracts --check --probe` | 11 kept/同じ・例外 30 行 22 辺(全部効く)・全部 kept |
| `map --check`・カード(作り直し・`data.md` だけ戻した)・astsame(src)・秘密の走査 | 同じ・最新・変わった .py 0 本・CLEAN |

## 11. 親の確かめと裁定(第347・2026-11-18)

### 11-1. 別の役の検収と再検収

- 検収(直しの前): 条件つき受入(高 2・中 0・低 5)。高-1=G0 で直した試験が表を引く鍵の字面を、道具が割る時に割り先へ書き換えて壊す(7 か所)。高-2=コードの文字列の中の `from shibuya import cli` の形(14 か所。指摘の「15」は検収役の数え違い=道具の見本 1 か所を数に入れていた)を、道具が書き換えもせず「手で直す一覧」にも出さない。直しは §10。
- 再検収(直しの後): 受入(高 0・中 0・低 3)。検収役が直した道具でメモリの中で 5 本を当て直し、鍵の字面の書き換え 0・割る 5 本の元のモジュールを読むコードの文字列の残り 0 を確かめた。`table_key_sites` の中身はどれも口の第 1 引数の鍵だけ・cli の本の「コード 28」は 14 か所 × 2 の書き換えでどれも子のプロセスの台本。14 か所が読む名は `main` 11・`run` 2・`checkpoints_payload` 1 で、どれも `interfaces/cli/main.py` の頂上に在る(§10-2 の「読む名は `main`・`run`」は `checkpoints_payload` を落としている。動き方は同じ)。
- 再検収の低 3 件: 低-1=f 文字列の部分を「手で直す一覧」へ出す枝に負の対照が無い(今の木に該当は無い)→ **G1 の最初に足す**(道具の試験だけ)。低-2=下の 11-2 を書いた。低-3=表の鍵を変数で渡すと守られない → `tests/_places.py` の `split_files` の説明に「鍵は第 1 引数に字面で書く」を足した(親。今の試験の呼び出しは全部字面=検索で確かめた)。

### 11-2. 5a の済んだ本に残っていた古い名の import(2 本 3 か所・§10-2)の裁定

- `tests/build_pop/test_w21_stage8_9.py` の 2 か所(`from shibuya.llm import fleet`・`import shibuya.llm.fleet`): **そのまま**。字面の "llm" を探す検出器の負の対照に植えた文で(`split.STRING_EXCLUDE` の記号)、今の名へ直すと負の対照でなくなる。
- `tests/engine/systems/test_fix_guards.py` の 1 か所(`import shibuya.agents.state`): **親が直した**。移す道具が下の行の点の道だけを今の名へ書き換え、import の行が元の名のまま残っていた形。import の行を下の行と同じ今の名 `shibuya.world.model.agent_table` にそろえた(注つき)。確かめる語(`_WP を読む`・`set_enabled`)は変わらない。そのファイルは直す前も後も 16 passed。

### 11-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| byte-check 19 構成(木の側の新しい道具で両側・基準 `9363b36`・直しの前。直しは src も `tools/bytecheck/` も変えていない) | 37 欄すべて同じ 19・動いた 0・誤り 0・436 秒。記録 [bytecheck_G0_parent/](bytecheck_G0_parent/)(§7) |
| 範囲の全体の試験(直しの前・`-n 4`) | 6,942 passed・1 failed(前からの 1 本)・21 skipped・1 xfailed・39 分 30 秒(§8) |
| 直しの後: `tests/tools/test_pkgmove.py` の全部(slow を含む・`-n` なし) | 122 本=102 passed・20 skipped・落ち 0 |
| 直しの後: 道具の試験の残り(`tests/tools` の test_pkgmove 以外)・c8 の写しの一致・`tests/c8/test_c8lib.py`・`test_two_phase`・`test_places_guard`・`tests/engine/time`・`state`・`bridging`・`systems`(`-n 2`) | 1,003 passed・0 skipped・落ち 0 |
| 親の手直しの後(`test_fix_guards` の 1 行・`_places.py` の説明の 2 行) | 11-4 |
| src の差(`git status -- src`) | 0 本 |

- 範囲の全体の試験を直しの後に回し直していないわけ: 直しが変えたのは `tools/pkgmove/`(4 本)・`tests/tools/test_pkgmove.py`・`tests/engine/test_two_phase.py`・記録・カードと、親の手直し 2 本だけ。それを読む試験(道具の試験・置き場の守り・決まりの束)は上で回した。

### 11-4. 親の手直しの後の確かめ

- `tests/c8/test_places_rule_copies.py`・`tests/test_places_guard.py`・`tests/engine/test_two_phase.py`・`tests/engine/systems/test_fix_guards.py`(`-n` なし): 59 passed・0 skipped・落ち 0。

## 12. G1 の当て(群の土台 `4af887b`=G0 の commit・安定版のタグ `stable-v2-before-split5b-G1`・2026-11-18)

最初に G0 の再検収の低-1 として、f 文字列の部分の枝の負の対照を 1 本足した(`test_split_lists_a_code_import_inside_an_f_string_for_hand_fixing`=その枝を外すと一覧に出ずに残る。`tools/pkgmove/` は変えていない)。そのあと 1 本ずつ、手で直す読みを先に直し(書かない実行で手で直す 0 を見てから)、当て、契約を作り直し、試験と byte-check を回した。

### 12-1. 本ごとの数

| 本 | 割る行 | 書き換えた import の文(src・tests・tools・docs) | 分けた文 | 鍵 | 台帳の道 | 道の文字列 | 書き換えなかった鍵 | 手で直した読み | 写さなかった | 守り | byte-check | 契約 | 例外 載せた・効いている(辺/行) |
|---:|---|---|---:|---:|---:|---|---:|---|---|---|---|---|---|
| 18 | `engine/commit.py` | 79(19・60・0・0) | 1 | 3 | 1 | 0 | 6(`test_two_phase`) | 26(src 5・tests 21) | 無い(自分を読む import 1=`TARGET_HINT_WORDS`・再輸出 `UNDEFINED_ACTION` は割り先へ写さない) | 12 個「同じ」 | 19/19 同じ | 2+9 | 20/26・20/26(#9・#15 が消えた) |
| 19 | `engine/presence.py` | 18(7・9・2・0) | 2 | 4 | 1 | src の表 2・斜線 3(植えた道 2 本) | 2 | 0 | 無い | 12 個「同じ」 | 19/19 同じ | 2+9 | 20/26・20/26 |
| 20 | `engine/calendar_shadow.py` | 13(7・4・2・0) | 0 | 2 | 1 | src の表 1・斜線 1 | 0 | 2(src 1・tests 1) | 無い | 12 個「同じ」 | 19/19 同じ | 2+9 | 20/26・20/26 |

- 割り先: 18 本目 `act/commit.py`(新・9 名)・`act/intake/from_words.py`(新・11 名)・`foundation/vocab/act_codes.py`(在る・34 名を後ろへ)/19 本目 `world/laws/presence.py`(新・15 名)・`world/laws/presence_plan.py`(新・15 名)/20 本目 `society/calendar_shadow.py`(新・21 名・`_ARM` の確かめの文 1)・`world/facts/w20_calendar_reader.py`(新・15 名)。作った頭 0・消えた頭 0(`engine/` は `resolve.py` が段 6 まで残る)。
- 例外: 18 本目で計画のとおり #9(`mind.judge.decision.layer -> act.commit`)・#15(`mind.memory.memory -> act.commit`)が消えた(22 辺・延べ 30 行 → 20 辺・延べ 26 行。読む名が `act_codes`=foundation に在るため)。19・20 本目は変わらない。`lint-imports` は 3 本とも 11 kept。
- 写さなかった import と注(`unwritten`): 3 本とも 0。
- tests/c7: 3 本とも道具は 1 か所も挙げなかった。
- byte-check(基準 `4af887b`・積み重ね・記録 `bytecheck_18`・`_19`・`_20`): 3 本とも 19 構成・37 欄すべて同じ 19・動いた 0・誤り 0(既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939=前と同じ)。

### 12-2. 手で直した読み(裁定 Q10=割り先ごとに別名を 1 つ・属性の読みのまま)

- 作法(5a の 17 本目と同じ): 別名の import の文は元のモジュールを指したまま別名だけを割り先ごとに分け(割る前は同じモジュール=1 バイト不変)、道具が別名ごとに割り先へ書き換える。名の import には替えない(差し替えの効く先=呼ぶ時に引くモジュールの属性を保つ)。別名の import の文ごとに、その有効範囲で使う名の割り先の別名だけを置いた。
- 18 本目(26 本): 別名 `C` を `C`=act.commit・`CW`=act.intake.from_words・`CV`=foundation.vocab.act_codes に分けた。再輸出の `UNDEFINED_ACTION` は、道具が割り先へ向けるのと同じ `from_words`(`CW`)で読む。src 5 本=`act/activity.py`(C 3・CV 9)・`act/intent.py`(C 9・CV 13)・`engine/run.py`(CW 1・CV 2)・`runtime/systems/act.py`(C 4・CW 2)・`runtime/systems/judge.py`(C 1・CV 5・CW 3)。tests 21 本=`test_stage2_calls`・`test_civic`・`test_crowd`・`test_rail`・`test_rail_board_intent`・`test_rail_return`・`test_c9b_targets_attention`・`test_conversation_invite`・`test_defect_fixes_1103`・`test_geometry_c9`・`test_intent_hold`・`test_ledger_wiring`・`test_move_destination`・`test_parser_contract`・`test_plan_sleep_d62`・`test_renderer_wiring`・`test_resolve`・`test_seat_release_2_4`・`test_two_layer_activity`・`test_two_phase`・`test_vocab_v2_eat`。G0 の木の数(26)と同じ。
- 20 本目(2 本): `interim_bundles/calendar_self.py` の `_CS` を `_CS`=society.calendar_shadow(`_hist15`・`_stats`)・`_CR`=world.facts.w20_calendar_reader(`_thaw`・`load_table`・`resolve_path`・定数 4)に、`tests/engine/calendar/test_calendar_shadow.py` の `CS` を `CS`・`CR` に分けた。G0 の木の数(2)と同じ。
- 19 本目: 手で直す読み 0(G0 の木の数と同じ)。

### 12-3. 差し替えの空振りの確かめ(親の決め事 3)と、中身を見る試験

- 18 本目: `tests/engine/test_response_delay.py` は `monkeypatch.setattr(C, "intents_from_responses", wrap)` で差し替え、`runtime/systems/judge.py` は呼ぶ時に `CW.intents_from_responses(...)` で引く。道具は試験の `C` を `act.intake.from_words` へ書き換えた(別名の読みの割り先が 1 つ)=差し替えの先と呼ぶ時に引く先が同じモジュール。差し替えの 1 行を外すと 2 本が落ちる(`+1 で反映されていない`・`Counter() == …`)ことを確かめ、戻して `git diff` が確かめの前と同じことを見た。
- 19・20 本目: src の手直しに関わる差し替えの試験は無い(19 本目は src の手直しが 0・20 本目の `calendar_self` の `_CS`・`_CR` を差し替える試験は無い=`setattr` の走査で 0)。
- 中身を見る試験: 18 本目で `test_two_phase` の `_hot_paths` が `act/commit.py`・`act/intake/from_words.py` を返し、ループを探す範囲に `foundation/vocab/act_codes.py`(と `agent_codes.py`)が加わる(鍵 6 は書き換わらない)。19 本目で `test_presence_executor`・`test_calendar_sites` の `split_files("engine/presence.py")` が `world/laws/presence.py`・`presence_plan.py` を返す(鍵 2 は書き換わらない)。道の文字列は 3 本とも、主な割り先へだけ書き換えて範囲が狭まった所は無い(19 本目の植えた道 2 本は鍵と期待を同じ道へ・`tools/c8/c8lib.py` の元の道の比べは `STRING_EXCLUDE` で残る=`tests/c8/test_c8lib.py` が通る)。

### 12-4. 狙いの試験(作業の木・`-m "not slow"`・`-n 2`。木をまるごと写す試験と slow は 1 本ずつ)

| 本 | その本で変わった試験のファイルと中身を見る試験 | `test_pkgmove`(slow を除く・`-n` なし) | 決まりの束(c8 を先に)+`tests/tools` の残り | slow |
|---|---|---|---|---|
| 18 | 30 本 545 passed | 122=102 passed・20 skipped(G0 の終わりの 121=101+20 に、f 文字列の負の対照 1 本が足された。slow の 1 本を入れると全部で 123 本) | 988 passed | 1 passed |
| 19 | 11 本 220 passed | 122=102 passed・20 skipped | 988 passed | — |
| 20 | `tests/engine/calendar`・`test_w20_calendar_1a`・`test_calendar_10e_e3` 77 passed | 122=102 passed・20 skipped | 988 passed | 1 passed |

### 12-5. G1 の終わりの確かめ

- `map --check` 同じ・`contracts --stage delete --check --probe` 作り直しと同じ(契約 2+9・例外 20 辺・延べ 26 行=全部効く・全部 kept)・`lint-imports` 11 kept・カードを作り直した(`data.md` だけ戻した・`--check` 最新)・秘密の走査 CLEAN(消したファイル 3 本を除く変えたファイルと新しいファイル)。astsame は使っていない(src が変わる段)。
- G2(run)に送ること: G0 の §9-3 のとおり(手で直す 6=`runtime/systems/assemble.py` の `_RUN` と tests 5・差し替えの確かめ=`test_resume_10d` ほか・`prog` の変化・`tests/c7/test_accept_table.py::TIME_V` の機械の書き換え・入口 `-m shibuya.interfaces.cli.run_args --help`)。`engine/run.py` は 18 本目で別名 `C` を `CW`・`CV` に分けた後の形で割る(`CW`=from_words・`CV`=act_codes の import は、割った後は名の割り先 `runtime/run.py` に写る)。

## 13. G1 の親の確かめと検収(第347・2026-11-18)

### 13-1. 別の役の検収

- 判定: **受入**(高 0・中 0・低 3)。検収役はファイルを 1 本も変えていない。
- 道具の当て直し: 土台 `4af887b` をメモリに読み、今の道具と表で 18〜20 本目を当て直した。守りは 3 本とも 12 個「同じ」・手で直す一覧は 26・0・2。作業木と違うのは 29 本=手で直した 28 本(commit 26・calendar_shadow 2)と、負の対照を足した `test_pkgmove` だけ(記録の一覧と過不足なし)。実装役の報告に名の出ない src の 13 本(`act/target.py`・`cli.py`・`engine/resolve.py`・`foundation/decl/ledger_paths.py`・`foundation/vocab/act_codes.py`・`interim_bundles/calendar3/roster.py`・`mind/judge/decision/layer.py`・`mind/memory/memory.py`・`runtime/state/class_ids.py`・`ledger.py`・`ledger_ast.py`・`runtime/systems/assemble.py`・`talk.py`)は、道具の出力とバイトが同じ(import の書き換え・台帳の道・固定の表の鍵・決まりの名の引き直し)。割り先 7 本の頂上の文は、字面・AST・前の注が元と同じ。
- src の手直し: 28 本とも名の import は前も後も 0(裁定 Q10 のとおり)。別名の読みはどれも表の名の割り先を指す(再輸出の `CW.UNDEFINED_ACTION` の 3 か所も同じ物)。新しい別名を元の別名へ戻すと 27 本は土台と AST が同じ・残る 1 本(`test_calendar_shadow`)の違いは道具が書き換えた OWNER の道の字面 1 つだけ。読み込みの時の循環は土台 0・作業木 0。
- 差し替えの空振り: 無い。割り先 7 本のモジュールの属性を差し替えるのは `test_response_delay` の 1 か所だけ(ほかはクラスの属性)。差し替える先(`from_words.intents_from_responses`)と、`runtime/systems/judge.py` が呼ぶ時に引く先(`CW.intents_from_responses`)は同じモジュールの属性。
- 範囲の狭まり・空回り: 無い。割った後の木で `split_files` は割り先の全部を返す(commit 3 本・presence 2 本・calendar_shadow 2 本)。`_hot_paths`・`_loop_scan_paths`・`test_presence_executor`・`test_calendar_sites` の 4 つを単独で回して passed。表の鍵の字面の書き換えは 0。
- import の決まり(`contracts --check --probe`): 契約 2+9・例外 22 辺/30 行 → 20 辺/26 行(消えたのは #9・#15 だけ・残りは全部効く・計画に無い例外は無い)。
- 凍結: `CLASS_IDS` の値の集合は同じ(変わった鍵 9 は今のクラスに解ける)・凍結の JSON とつなぎの台帳に差は無い。`tests/c7` は差分に道が 1 つも無い。

### 13-2. 検収の低 3 件の扱い

- 低-1(割り先に古い置き場の名の docstring・注が残る=`world/laws/presence.py`・`society/calendar_shadow.py` の見出し・`runtime/state/ledger.py` の basis・`act/intent.py`・`engine/resolve.py`・`runtime/inference/bridge.py`・`act/intake/undefined.py` の注): そのまま。割る段は文を変えない(1 バイト不変)。段 8 の文の掃除で直す。
- 低-2(**変わった所**): 環境変数 `SHIBUYA_CALENDAR_SHADOW` に不正な値が入っているとき、読み込みの時の確かめ(`ValueError`)が走るのは `society/calendar_shadow.py` を読んだ時だけになった。割る前は `engine/calendar_shadow.py` の 1 本だったので、W20 の表の読み口の定数だけを読む道具(`tools/instruments/anchor_gauge.py`=ファイルの名と置き場の 2 つを読む)も不正な値で止まっていた。割った後は、読み口(`world/facts/w20_calendar_reader.py`)だけを読む道具は止まらない。ランは変わらない(`cli`・`engine/run.py`・`calendar_self.py`・`runtime/systems/assemble.py` が `society/calendar_shadow.py` を読むので、不正な値なら前と同じに止まる)。正しい値のランと byte-check には効かない。確かめの文を腕の持ち主(`set_arm` と同じ割り先)に置くのは表のとおり。読み口の側にも確かめを置くと world → society の辺ができる。**親の仮採用=そのまま**(ランの結果ではないが、変わる所として報告に載せる)。
- 低-3(§12-4 の `test_pkgmove` の数): 1 本増えたわけを表に書き添えた(親)。

### 13-3. 親が回した確かめ

| 何を | 結果 |
|---|---|
| byte-check 19 構成(本体の道具=G0 の入った `check.py`・基準 `4af887b`・3 本を当てた後の木) | 37 欄すべて同じ 19・動いた 0・誤り 0・436 秒・既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。記録 [bytecheck_G1_parent/](bytecheck_G1_parent/) |
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`) | 6,950 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる)・21 skipped・1 xfailed・39 分 31 秒 |
| 別名の読みの突き合わせ(親の台本・src・tests・tools の 45 本 602 か所) | 別名の指す割り先の頂上に無い名 0・1 つの別名が 2 つの割り先を指す所 0 |
| 差し替えの走査(親の台本・tests の `setattr`・`patch`・属性への代入) | 割り先のモジュールの属性の差し替えは `test_response_delay` の 1 か所だけ |
| `pyproject.toml` の差 | 例外 4 行(2 辺 × 契約 2 つ)の削除だけ |


## 14. G2 の当て(群の土台 `ce59591`=G1 の commit・安定版のタグ `stable-v2-before-split5b-G2`・2026-11-18)

### 14-1. 本の数

| 本 | 割る行 | 書き換えた import の文(src・tests・tools・docs) | 分けた文 | 鍵 | 台帳の道 | 道の文字列 | 書き換えなかった鍵 | 手で直した読み | 写さなかった | 守り | byte-check | 契約 | 例外 載せた・効いている(辺/行) |
|---:|---|---|---:|---:|---:|---|---:|---|---|---|---|---|---|
| 21 | `engine/run.py` | 206(17・183・3・3) | 10 | 3 | 1 | src の表 3・斜線 5・入口 1(`-m` の文脈)・コード 4(記号 10) | 14 | 6(src 1・tests 5) | `import warnings`(計画どおり)・G1 で足した注 1 行(下) | 12 個「同じ」 | 19/19 同じ(430 秒) | 2+9 | 20/26・20/26 |

- 割り先: `runtime/run.py`(新・39 名)・`runtime/result.py`(新・19 名)・`interfaces/cli/run_args.py`(新・5 名と `if __name__ == "__main__"` の文 1)。作った頭 2(`interfaces/__init__.py`・`interfaces/cli/__init__.py`=0 バイト)。`engine/__init__.py` は `resolve.py` が段 6 まで残るので残る。
- 写さなかった注: G1 の 18 本目で `engine/run.py` に足した注「別名 C を割り先ごとに分けた…」(import の前)。割った後は import の文を割り先ごとに作り直すので写らない(報告の `unwritten` に出た)。割り先の import は `from shibuya.act import commit as C`・`from shibuya.act.intake import from_words as CW`・`from shibuya.foundation.vocab import act_codes as CV` のうち、その割り先が使うものだけ。
- 契約: `interfaces` の包みができ、単位 interfaces が言えるようになった(層の並びと「読んでよい側」に `shibuya.interfaces` が入った)。読んでよい側に足していた古い読み手 `shibuya.engine.run` は外れた(`shibuya.cli` は G3 まで残る)。契約の数は 2+9 のまま・例外は 20 辺・延べ 26 行のまま(全部効く)・計画に無い契約と例外は要らなかった。`lint-imports` 11 kept。
- tests/c7: 道具が挙げたのは `tests/c7/test_accept_table.py` の 1 か所だけ(記号 `TIME_V`・29 行)。前 `TIME_V = """\tCommand being timed: "python -m shibuya.engine.run"`/後 `TIME_V = """\tCommand being timed: "python -m shibuya.interfaces.cli.run_args"`(`-m` の文脈=入口の割り先)。書き換えた後の `-m` の先は、当てた後の import の確かめで `--help` が終了コード 0 で動く入口であることを確かめた。ほかの行は読んでいない・回していない。
- docs の記録の道具(import だけ・親の決定 7): `docs/bench/analysis/wallbounce-1003/10d/first_diff.py`・`wallbounce-1012/md23/tools/multiday_md23.py`・`c10-relations-2026-09-28/rel8b_measure.py` の 3 本・各 1 行。
- 範囲の外(E4): `tests/tools/test_bytecheck.py` の 4 か所を書き換えずに残した(G0 の見込みと同じ)。
- byte-check(基準 `ce59591`・記録 `bytecheck_21`): 19 構成・37 欄すべて同じ 19・動いた 0・誤り 0・430 秒(既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939=前と同じ)。

### 14-2. 入口の移しと使い方の表示(親の決め事 4)

- `main` と `if __name__ == "__main__":` は `interfaces/cli/run_args.py` へ行った。`engine/run.py` は消え、`python -m shibuya.engine.run` は `No module named shibuya.engine.run` で動かない(返事その 8 §1-6 の 6 の決定のとおり)。当てた後の import の確かめは `python -m shibuya.cli --help`・`python -m shibuya.interfaces.cli.run_args --help` とも終了コード 0。
- `--help` の出力を割る前(`-m shibuya.engine.run`)と後(`-m shibuya.interfaces.cli.run_args`)で比べた: 説明と引数の一覧(88 行)は同じ。違うのは使い方の行の `prog` が `run.py` → `run_args.py` になり、名が長くなった分だけ使い方の行の折り返しが変わる所だけ(空白をつぶして `prog` を除くと同じ)。ランの結果ではない。

### 14-3. 手で直した読み(裁定 Q10)

- G0 の木の数(6)と同じ。`runtime/systems/assemble.py` の `_RUN` を `_RUN`=runtime.run(14 か所)・`_RES`=runtime.result(`RunResult`・`_ENTRANCES` の 2 か所)に分けた(属性の読みのまま=呼ぶ時にモジュールの属性として引く形を保つ)。`tests/test_cli_vocab_version.py` の `RUN` を `RUN`・`RES` に分けた。使わない別名 `RUN` の import(属性の読みも素の使い方も無い)を 4 本から外した: `tests/engine/discard_probe.py`・`test_10a_review_fixes.py`・`test_response_delay.py`・`test_sim_time_T.py`。
- `runtime/systems/{act,body,decide,judge,llm_io,perceive,run_end}.py` の「呼ぶ時に引く」別名 `_RUN` は、読む名が全部 `runtime/run.py` に在るので道具が機械で `runtime.run` へ書き換えた(手直し不要)。

### 14-4. 頂上で読み込みの時に走る文(G1 の検収 低-2 と同じ見方)

| 行 | 文 | 割り先 | 割った後に走らなくなる読み手 |
|---:|---|---|---|
| 175 | `DELTA_THINK_TICKS = delta_think_ticks(…)`(値の計算) | `runtime/run.py` | 無い(純な計算・外への作用なし) |
| 257 | `_ENTRANCE_OF_CONDITION = np.array(…)`(表の組み立て) | `runtime/run.py` | 無い(同上) |
| 653 | `@dataclass class _RunDayLocals` | `runtime/run.py` | 無い |
| 663 | `@dataclass class Checkpoint` | `runtime/result.py` | 無い |
| 709 | `@dataclass class RunResult`(欄の既定の `np.zeros` ほか) | `runtime/result.py` | 無い |
| 2734 | `if __name__ == "__main__": raise SystemExit(main())` | `interfaces/cli/run_args.py` | 無い(`-m` の入口=14-2) |

- 環境変数の読み・登録・止める確かめの文は、`engine/run.py` の頂上に無い。
- あわせて、読み込みの時に import するモジュールの閉包を比べた: `runtime/result.py` だけを読むと、前は `engine/run.py` を読めば読み込まれた 26 モジュールが読み込まれなくなり、そのうち `act.intake.undefined` の頂上に定数の表の自己確かめの `assert` が 4 つある。今の木で `runtime.result` を読み込みの時に読む src 2 本・tests 7 本は、どれもほかの道で `act.intake.undefined` を読み込む=走らなくなる読み手は 0(一覧は空)。`runtime/run.py` だけを読む読み手は 4 モジュールが減る(`growth_decl`・`presence`・`presence_plan`・`switch_rate`)。〔検収の低-1 で親が直した〕そのうち `world/laws/switch_rate.py` の頂上には、消した切替口の環境変数(`SHIBUYA_RATE_RULES`)が在れば止める文が在る(止まる所が変わる=§15-2 の低-1)。`interfaces/cli/run_args.py` は減らない。

### 14-5. 差し替えの空振りの確かめ(親の決め事 3)

- 割る前の走査(元のモジュールの属性を差し替える 7 か所)で、差し替える名を読む頂上の文が別の割り先へ行く形(割り先どうしの間の読みで空振りする形)は 0。割った後に親の台本 2 本を run の割り先で回した: 差し替え 6 か所とも、その名を「名の import」で持つ src は 0・別名の属性の読み 75 か所(20 本)で割り先の頂上に無い名は 0。
- 差し替えごとの確かめ(書き換えは台本で 1 行だけ・回した後にバイトで戻し、`git diff` が確かめの前と同じことを見た):

| 試験 | 差し替え(割った後の先) | 使う側(呼ぶ時に引く先) | 外すと | 落ちる物に替えると |
|---|---|---|---|---|
| `test_state_ledger_10b::test_pending_tuple_carries_fire_tick_and_call_id` | `_split_due`(`runtime.run`) | `runtime/systems/judge.py` の `_RUN._split_due`(`runtime.run`) | 落ちる(`assert due_seen`) | — |
| `test_state_ledger_10b::test_t2_call_id_on_the_fleet_and_replay_paths` | `_call_ref`(`runtime.run`) | `runtime/systems/decide.py` の `_RUN._call_ref` | 落ちる(`set()`) | — |
| 同(1220 行) | `_split_due`(`runtime.run`) | `judge.py` の `_RUN._split_due` | 落ちない(この試験の確かめは差し替えの中の assert だけ) | 落ちる(`RuntimeError`=差し替えが使う側に届く) |
| `test_t0_tm9_fields::test_tm9_fields_do_not_feed_the_final_hash` | `CLOCK_KIND`(道具が `runtime.result` へ=`RunResult.run_manifest_fields` が読む割り先) | `RunResult.run_manifest_fields` の頂上の名 | 落ちる(`'steps' == 'other'`) | — |
| `test_version_bump_10e::test_e4_l2_load_population_and_three_argument_samplers_follow_the_engine` | `sample_population`(`runtime.run`) | `runtime/run.py` の `_resolve_population` | 落ちない(元の抽出でも同じ数を返す=試験の狙いは「3 引数の差し替えも呼べる」) | 落ちる(`RuntimeError`) |

- 試験の外の差し替え: `tools/instruments/anchor_gauge.py` の `RUN._resolve_population = _pop`(計器)は、別名 `RUN` が道具で `runtime.run` へ・使う側 `assemble.py` の `_RUN._resolve_population` も `runtime.run`=同じモジュール(走らせての確かめはしていない)。

### 14-6. 中身を見る試験・凍結と台帳

- `split_files("engine/run.py")` は割った後に `interfaces/cli/run_args.py`・`runtime/result.py`・`runtime/run.py` を返す(名の指定 `run_day`・`RunResult` で `result`・`run`/`RunResult` で `result`/`main` で `run_args`)。`_hot_paths` は `runtime/result.py`・`runtime/run.py` を、`_loop_scan_paths` はさらに `interfaces/cli/run_args.py` を見る。`test_activation_10e`・`test_norm_meter`・`test_near_tiebreak` は 3 本の全部を見る。表の鍵 14 か所は書き換わらない(`table_key_sites`)。
- `test_boxes` は凍結の名 `shibuya.engine.run._RunDayLocals` の字面のまま(道具は凍結の名を書き換えない=報告の触らなかった文字列)で通る(裁定 Q12)。
- 道の文字列で主な割り先へだけ書き換えて範囲が狭まった所は無い: `test_bridging_ledger`(台帳の行 BR-MOCK-SCHEDULE-POPULATION の道 → `runtime/run.py`=「繋ぎ」の字が在る・Q4)・`test_salt_seed_split_10f`(同じ組の名の割り先)・`test_state_checks_10f`・`test_state_ledger_10b`(古い字面の負の対照)・`test_commit_check`(道の形の負の対照)・コードの文字列 4 か所(`_T1_CHILD`・`RUN_DAY`・`_HEAD_CHILD`・`_REPLAY_CHILD`=名の割り先へ)。`tests/c8/test_sensitivity_ledger.py:525` の `"w99_x.parquet ← engine/run.py:1"` は記録の文(ASCII の外の字)で書き換えない(試験は通る)。
- 凍結: クラスの名の固定の表は鍵 3 つだけを書き換え、値(凍結の名 `shibuya.engine.run.Checkpoint`・`RunResult`・`_RunDayLocals`)は変わらない。名の凍結・つなぎの台帳の JSON・乱数の領域の名・manifest に入る文字列は変わらない(守りの「名の凍結」「定数」が同じ・`git diff` で台帳の JSON と `names_frozen.json` は差分 0)。台帳の道の表は `src/shibuya/runtime/run.py` → `src/shibuya/engine/run.py` を 1 行足した。
- `RESULT_FILES`(`runtime/state/ledger_ast.py`): 道具は src の表の道を主な割り先へ書き換え、`"engine/run.py"` は `"runtime/run.py"` になった(計画 §5-3 の見込みどおり)。`result.…` への代入の文は割る前の `engine/run.py` にも、割った後の 3 本にも 0 本=分類は同じ。発注の「変わっていないこと」は字面の意味なら違う(親に確かめたい所=§14-8)。`UNRESOLVED_ALLOW` の `("engine/run.py", "old = …")` は `runtime/run.py` へ(文字列の在る割り先=`_count_intero_crossings`・Q4)・`DIAG_EXITS` の `RunResult.*` は `runtime/result.py` へ。

### 14-7. 狙いの試験(作業の木・`-m "not slow"`)

| 何を | 結果 |
|---|---|
| その本で変わった試験のファイル 140 本+`tests/c8/test_sensitivity_ledger.py`(`-n 3`) | 2,108 本=2,106 passed・1 skipped(Ruri の重みが置き場に無い)・1 failed → 直して passed(下) |
| `tests/tools/test_pkgmove.py`(`-n` なし) | 122=101 passed・21 skipped・1 failed → 直して passed(下)。飛ぶ試験が 1 本増えた=`test_split_order_is_kept_in_the_real_tree`(割る段の終わりの木=次の本と、その次の本の 2 本が要る試験。22 本のうち 21 本が済んだ)|
| 決まりの束(c8 の写しの一致を先に・`tests/c8/test_c8lib.py`・`tests/engine/time`・`state`・`bridging`・`systems`・`tests/test_places_guard.py`)+`tests/tools` の残り(`-n 2`) | 988 passed |
| `test_pkgmove` の slow(残りの 1 本=cli を順に当てる) | 1 passed |
| 差し替えの試験 4 本(§14-5)・`test_state_format_10f::test_u1_resume_from_a_pkl_written_by_the_pickle_commit` | passed |

- 落ちた 2 本と直し(どちらも試験だけ・src と道具は変えていない):
  - `tests/engine/test_state_format_10f.py::test_u1_resume_from_a_pkl_written_by_the_pickle_commit`: 子のコード `_HEAD_CHILD` は古い commit(`LEGACY_COMMIT`)の src の写しでだけ回す(`assert "head_src" in shibuya.__file__`)。道具がコードの文字列の import を `runtime.run` へ書き換えたので、古い src で `No module named 'shibuya.runtime'`。元の字面 `from shibuya.engine.run import run_day` に戻し、注を付けた。古い src で回すもう 1 本(`tests/perception/facts/test_percept_is_scratch.py`)は、移す前の commit の子のコードを取り出して使う作り(段 4 で入れた)なので通る。古い src で回す試験は tests の中でこの 2 本だけ(`git archive` の走査)。
  - `tests/tools/test_pkgmove.py::test_negative_names_guard_catches_version_ids_headers_and_rng_tables`(道具の試験): 乱数の領域の名の表の置き場を `engine/run.py` の字面で引いていた(割った後は無い)。表の名 `POPULATION_RNG_DOMAINS` を頂上で定義するファイルを引く形に直した(割る前は `engine/run.py`・割った後は `runtime/run.py`)。

### 14-8. 計画・G0 の数と違った所・止まる所・G3 に送ること

- 手で直す読み・例外・契約・写さなかった `import warnings`・c7 の 1 か所は計画と G0 の見込みのとおり。写さなかった注が 1 行増えた(G1 で足した注)。
- 親に確かめたい所 1: 古い commit の src で回す子のコードの文字列(`test_state_format_10f._HEAD_CHILD`)を、割る道具が今の置き場へ書き換えないよう `split.STRING_EXCLUDE` に足すか(今回は試験の字面を戻しただけ=道具は変えていない。段 6 以降で `engine` の名を割る本でも同じ形が起きうる)。
- 親に確かめたい所 2: `RESULT_FILES` の字面が `engine/run.py` → `runtime/run.py` に変わったこと(§14-6。裁定 Q12 の「そのまま」を「道具の既定の当て方のまま」と読んだ)。直していない。
- 止まった所: 無い(割り先どうしの間の読みで空振りする差し替え 0・読み込みの時の文が走らなくなる読み手 0・計画に無い契約と例外 0)。
- G3(cli)に送ること: G0 の §9-3 の G3 の項のとおり(手で直す 6・転送の後の `python -m shibuya.cli --help` と `--llm mock` の final と呼数・コードの文字列 14 か所の機械の書き換えの後に子のプロセスの台本が動くことを狙いの試験で確かめる・`tests/_places.py` と台帳の道の表の転送の扱い)。cli は run の名を `interfaces/cli/run_args.py`(`add_fleet_args` ほか)と `runtime/run.py`・`runtime/result.py` から読む形になった(この本で道具が書き換えた)。
- G2 の終わりの確かめ: `map --check` 同じ・`contracts --check --probe` 作り直しと同じ(例外 20 辺・延べ 26 行=全部効く・全部 kept)・カードを作り直した(新しいカード 2=`interfaces`・`interfaces/cli`・`data.md` だけ戻した・`--check` 最新)・秘密の走査 CLEAN(消したファイル 1 本を除く)。astsame は使っていない。

### 14-9. G2 の直し(検収=受入の低 3 つ・親の裁定・src と `tools/bytecheck/` は変えていない)

- F1(親の裁定 1): `split.STRING_EXCLUDE` に `("tests/engine/test_state_format_10f.py", "_HEAD_CHILD")` を足した(注 2 行+1 行・`tools/pkgmove/README.md` に 2 行)。確かめ: 基準 `ce59591` の木をメモリに読んで 21 本目を当て直すと、`_HEAD_CHILD` は `from shibuya.engine.run import run_day` のまま(書き換わらない)。作業の木と当て直しの違いは 9 本=手で直した 6 本(`assemble.py`・`discard_probe.py`・`test_10a_review_fixes.py`・`test_response_delay.py`・`test_sim_time_T.py`・`test_cli_vocab_version.py`)・`test_state_format_10f.py`(足した注の 2 行だけ)・`test_pkgmove.py`・`tools/pkgmove/split.py`(F1 の除外の行=当て直しは基準の木の道具の写しで比べた側)。
- F2(検収 低-4): `test_string_excludes_name_symbols_that_exist_in_the_tree`=`STRING_EXCLUDE` の (ファイル, 記号) の全部で、ファイルが在り、記号がそのファイルの記号(道具と同じ `symbol_map`)に在る。負の対照: 在りもしない記号・在りもしないファイルを足した一覧では「無い」と言う。
- F3(検収 低-2): `test_split_order_is_kept_in_a_sample_tree`=`SPLIT_ORDER` を 3 行に差し替えた見本の木で、どの時点でも次の 1 本のほかは「順が違う」・済んだ本は「当たっている」で断る(本物の木の試験は残りの本が 2 本未満で飛ぶので、同じ確かめを見本で残す。本物の木の試験は消さず、飛ぶ条件も変えていない)。
- 親の裁定 2・3(`RESULT_FILES` の字面・読まない別名の import を外したこと)は直しなし。§14-4 は親が直す(この節では触らない)。
- `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし): 124 本=103 passed・21 skipped(前の 101 passed に足した 2 本)。`map --check` 同じ・`contracts --check --probe` 同じ(例外 20 辺・延べ 26 行=全部効く)。`git status --porcelain -- src` は直しの前と同じ。

## 15. G2 の親の確かめと検収(第347・2026-11-18)

### 15-1. 別の役の検収

- 判定: **受入**(高 0・中 0・低 5)。検収役はファイルを 1 本も変えていない。
- 道具の当て直し: 土台 `ce59591` をメモリに読み、今の道具と表で 21 本目を当て直した。守りは 12 個「同じ」・手で直す一覧は 6。作業木と違うのは 8 本=手で直した 6 本・`test_state_format_10f`(`_HEAD_CHILD` を戻した分)・`test_pkgmove`(負の対照の直し)だけ(記録の一覧と過不足なし)。割り先 3 本の頂上の文(run 39・result 19・run_args 6)は、字面・AST・前の注が元と同じ。docs の記録の道具 3 本は import の行だけ。
- src の手直し: `assemble.py` の `_RUN` は `_RUN`(runtime.run・14 名)と `_RES`(`RunResult`・`_ENTRANCES`)に分かれ、属性の読みのまま(名の import は増えていない)。割る前の `_RUN` の 16 名は表の割り先と合う。systems 7 本の「呼ぶ時に引く」`_RUN` は道具が runtime.run へ向け、読む名はどれもその頂上に在る。run の割り先を読む変わったファイル 158 本のうち 151 本は、別名を戻して import を除くと土台と AST が同じ・残る 7 本の違いは道具が書き換えた文字列だけ。
- 差し替えの空振り: 無い。土台の差し替え 5 か所(`_split_due`・`_call_ref`・`sample_population`・`CLOCK_KIND`)は、試験が差し替える先と、使う側が呼ぶ時に引く先が同じモジュール。割り先どうしの間の読みで空振りする形は 0・割り先のモジュールへ属性を直に代入する所は 0。実装役の「外すと落ちる」の確かめは、その差し替えの 1 行を外す形で正しい。
- 入口の移し: `run_args` の `main` と `if __name__` は元と同じ文。検収役が `--help` を両方取って比べ、違いは `prog`(`run.py` → `run_args.py`)と使い方の行の折り返しだけ。古い入口 `-m shibuya.engine.run` は `No module named`。名の無い点の道が黙って主な割り先へ向いた所は 0(`-m` の文脈は c7 の 1 か所だけ)。
- 範囲の狭まり・空回り: 無い。`split_files("engine/run.py")` は割り先 3 本を返す・`_hot_paths` は run と result・`_loop_scan_paths` は run_args を足す。`test_boxes`(凍結の名)とつなぎの台帳の試験を単独で回して passed。表の鍵の字面は 7 か所とも元のまま。
- import の決まり(`contracts --check --probe`): 契約 2+9・例外 20 辺/26 行で全部効く。`interfaces` は言えない単位から外れ、層と許す側に入った(決まりが強まる側)。計画に無い例外は無い・循環は 0。
- 凍結: `CLASS_IDS` の値は同じ(変わった鍵 3 は今のクラスに解ける)・凍結の JSON とつなぎの台帳に差は無い。`tests/c7` の差分は `test_accept_table.py` の 1 行だけ(検収役は中身を開いていない)。
- 直しの差分(§14-9 の F1〜F3)の再検収: **受入**(高 0・中 0・低 1)。今の道具で当て直すと `_HEAD_CHILD` は書き換わらず、作業木との違いは 9 本(手で直した 6 本・`test_state_format_10f` の注だけ・`test_pkgmove`・基準の側の道具との違いの `split.py`)。足した 2 本の試験は空回りしない(除外の記号は道具と同じ見方で引く・順の差し替えは道具が呼ぶ時に引く名に届く)。低-1(`test_state_format_10f` の注が「道具が書き換えたので戻した」のままだった)は、親が注の 2 行を直した(道具はこの記号を書き換えない、の文へ。コードの行は変えていない)。

### 15-2. 検収の低 5 件の扱い

- 低-1(**変わった所**・§14-4 の文の誤り): `runtime/run.py` だけを読むと、前は `engine/run.py` を読めば読み込まれた `world/laws/switch_rate.py` が読み込まれない。その頂上には、消した切替口の環境変数 `SHIBUYA_RATE_RULES` が在れば止める文が在る。**親が前後で動かして確かめた**(環境変数を置いて):割る前は `import shibuya.engine.run`・`-m shibuya.engine.run --help`・`-m shibuya.cli --help` が終了コード 1。割った後は `import shibuya.runtime.run`・`import shibuya.runtime.result` が終了コード 0(止まらない)、`import shibuya.interfaces.cli.run_args`・`-m shibuya.interfaces.cli.run_args --help`・`-m shibuya.cli --help` は終了コード 1(前と同じに止まる)。`run_day` は組み立て(`assemble.build`)で止まる=刻みの前に止まることは変わらない(検収役が `test_removed_switches_346` の該当の試験を単独で回して passed)。正しい環境のランと byte-check には効かない。**親の仮採用=そのまま**(G1 の §13-2 の低-2 と同じ扱い。ランの結果ではないが、変わる所として報告に載せる)。§14-4 の文は親が直した。
- 低-2(割る段の順を断る道の試験が、これから 0 になる): 直した(§14-9 の F3=見本の木で、順の違う行を断ることを確かめる試験を 1 本足した)。本物の木の試験 `test_split_order_is_kept_in_the_real_tree` は残した(残りの本が 2 本未満なので飛ぶ)。
- 低-3(読まない別名の import を 4 本から外した=計画と裁定に無い選択): **親の裁定=受け入れる**。読みが 0 の別名は割り先を選ぶ根拠が無い。検収役が、割る前の版で 4 本とも別名の読みが 0(名・属性・文字列)であること、外しても試験の時に読み込むモジュールが変わらないこと(`discard_probe` は唯一の読み手が頂上で runtime.run を読む)を確かめた。報告の親の決め事に足す。
- 低-4(`STRING_EXCLUDE` は名で引くので、記号を改名すると黙って除外が外れる): 直した(§14-9 の F2=除外の記号が今の木に在ることを確かめる試験を 1 本足した)。
- 低-5(割り先に古い置き場の名の docstring・注が残る=`runtime/run.py` の見出し・`runtime/state/ledger.py` の basis の文 7 か所・`runtime/systems/*` の docstring): そのまま。割る段は文を変えない(1 バイト不変)。段 8 の文の掃除で直す。

### 15-3. 実装役が聞いた 2 点の裁定

- `_HEAD_CHILD`(古い commit の src の写しでだけ回す子のコード)を `split.STRING_EXCLUDE` に足すか: **足す**(§14-9 の F1。道具の出力と木を同じにする=`tools/c8/c8lib.py` の行と同じ扱い)。検収役は、値が土台と 1 バイトも違わないこと・古い src で回す子のコードがほかに無いことを確かめた。
- `RESULT_FILES`(`runtime/state/ledger_ast.py`)の字面が `engine/run.py` → `runtime/run.py` に変わったこと: **道具の書き換えを受け入れる**。裁定 Q12 の「そのまま」は「割り先を 2 つとも載せず 1 つのまま」の意味で、発注の文(字面が変わっていないこと)は親の書き誤り。`site.path` は今の道なので、字面が元のままだとどのファイルにも当たらない。置き場の外の `result.… = …` は指摘になるので、1 つだけ載せるのは確かめの厳しい側(これから `runtime/result.py`・`run_args.py` に該当の文を書くと指摘になる)。該当の文は、割る前の `engine/run.py` も割り先 3 本も 0(検収役が `scan_external` で数えた)。

### 15-4. 親が回した確かめ

| 何を | 結果 |
|---|---|
| byte-check 19 構成(本体の道具・基準 `ce59591`・21 本目を当てた後の木) | 37 欄すべて同じ 19・動いた 0・誤り 0・431 秒・既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。記録 [bytecheck_G2_parent/](bytecheck_G2_parent/) |
| src の指紋(byte-check の後と、§14-9 の直しの後) | 同じ(371 本・直しは `tools/pkgmove/` と `tests/tools/test_pkgmove.py` だけ=byte-check は有効) |
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`・§14-9 の直しの後) | 6,951 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる)・22 skipped・1 xfailed・39 分 11 秒。前の 6,950 から、足した試験 2 本で +2・本物の木の順の試験 1 本が飛ぶ側へ移って −1(飛ぶ試験は 21 → 22) |
| 注を直した後の `tests/engine/test_state_format_10f.py` の全部と、除外の一覧の試験(範囲の試験の後・`-n 2`) | 42 passed |
| 消した切替口の環境変数を置いた前後の比べ(§15-2 の低-1) | 入口 2 つと `run_args` の import は前と同じに止まる・`runtime.run`・`runtime.result` の import だけは止まらなくなった |
| `--help` を Windows でファイルへ流す形(`PYTHONUTF8` なし) | 割る前も後も cp932 の誤りで終了コード 1(help の文に cp932 に無い字。割る段の違いではない=前からの欠陥として報告に載せる)。`PYTHONUTF8=1` では前後とも 0 |
| 古い入口を呼ぶ所の洗い(`.github`・`tools/night5070`・`*.ps1`・`*.sh`・`*.toml`) | `-m shibuya.engine.run` を呼ぶ所は 0(残るのは古い記録の文と docstring だけ) |

## 16. G3 の前の道具の拡張 E5 と、割る前の試験の直し(土台 `b0afefd`・2026-11-18)

G3(22 本目 `cli.py`)は 2 つの commit に分ける(5b の G0 → G1 と同じ形)。この節は 1 つ目=道具の拡張 E5-a と割る前の試験の直しだけ。`--apply`・byte-check・範囲の全体は回していない(src は 1 バイトも変えていない=`git status --porcelain -- src` は空)。

### 16-1. 止まった 2 回の経緯

- 1 回目(当てる前): 割り先どうしの間の差し替えが 2 つ見つかった(`test_resume_10d` の `build_ledger_bundle`=使う `run` は main・定義は wire_economy/`_stage2_outside.use_outside_bundle` の台帳の型=作る側は wire_economy・札を決める側は main)。発注のとおり直さずに止めた。親の裁定=差し替えは、割る前にその名を読んでいた関数の全部に届くよう、その関数が呼ぶ時に名を引く割り先へ向ける(下の表)。
- 2 回目(手で直す 6 件のうち 3 件を直した後): 裁定の形 3 つ(下の表の差し替える先・常に偽の `hasattr` の別名)は、道具の別名の割り先の決め方(読む名の定義の割り先か、再輸出の主な割り先)では 1 つに決まらず「手で直す一覧」から抜けられない=当てられない。発注の「発注の文と道具の当て方が食い違って見えたら聞く」で止めた。親の裁定=A(道具に宣言の表を足す)。B(当てた後に手で直す)・C(新しい書き方)は採らない。

### 16-2. 裁定の表(割る前の `cli.py` の読み手・作業の木で確かめ直して同じ)

| 名 | 読む所(割る前の行) | 読む関数の割り先 | 差し替える先 |
|---|---|---|---|
| `build_ledger_bundle` | 542(`run` の中)だけ | main | main だけ |
| `Ledger` | 304(`build_ledger_bundle` の中)・1794(`main()` の中)。251 はクラスの定義の親(読み込みの時に決まる) | wire_economy・main | 両方 |
| `_HouseholdWalletLedger` | 306(`build_ledger_bundle` の中)・1795(`main()` の中) | wire_economy・main | 両方 |
| `GoodsLedger` | 309(`build_ledger_bundle` の中)だけ | wire_economy | wire_economy だけ |
| `run`(ほかの差し替え 19 か所。〔検収の低-1 で親が直した〕合計 23=`run` 19・`build_ledger_bundle` 1・台帳の型 3) | `main()` の中(1714・1723)だけ | main | main だけ(道具の既定のまま) |

### 16-3. E5-a 別名の割り先の宣言(`tools/pkgmove/split.py`)

- `split.AliasDest`(割る行・ファイル・別名 → 割り先・割り先に無くてよい名 `absent`)と表 `split.SPLIT_ALIAS_DESTS`。宣言の在る別名は名の定義の割り先でなく宣言の割り先へ向く。宣言の無い別名は今までどおり。使った宣言は報告の `alias_declared` と `split --through` の行に出る。`imports.alias_dests` は別名の使い方を返す `imports.alias_uses` の上に作り直した(既定の決め方は同じ)。
- 守り(1 つでも当たれば書かない・書かない実行でも止める): 別名が割るモジュールを import していない/宣言の割り先がその割る行の割り先でない/別名で読む名が割った後の割り先の頂上で結ばれていない(定義でも道具が足す import でもない・`absent` のほか)/名で読まない使い方がある/`absent` に挙げた名を別名で読んでいないか割り先の頂上に在る/宣言が使われなかった(ファイルが木に無い・範囲の外・別名を結ぶ import が無い)。このうち「名で読まない使い方がある」と「`absent` が合わない」の 2 つは、発注の 4 つに足した(読む名を確かめられない形と、腐った宣言を黙って通さないため)。
- 拾う形: `X.名`(読み・代入・`del`)・`setattr`/`getattr`/`hasattr`/`delattr(X, "名", …)`・`<何か>.setattr`/`.delattr`/`.object(X, "名", …)`(`monkeypatch`・`mock.patch.object`)。拾わない形: 名が字面の定数でない形と `X` を素で使う形(どちらも「名で読まない使い方」で止める)・`mock.patch("shibuya.cli.名")` のような点の道の文字列(文字列の書き換えの側。今の木の src・tests・tools に `shibuya.cli.` で始まる文字列の差し替えは 0=凍結の表の鍵 2 つだけ)・コードの文字列の中の別名(宣言はファイルの別名だけ)。
- 宣言(6 行・4 ファイル):

| ファイル | 別名 | 割り先 | 無くてよい名 | 読む名(書かない実行の報告) |
|---|---|---|---|---|
| `tests/engine/test_resume_10d.py` | `cli` | `interfaces/cli/main.py` | — | 2(`run`・`build_ledger_bundle`) |
| `tests/economy/_stage2_outside.py` | `cli` | `interfaces/cli/main.py` | — | 2(`Ledger`・`_HouseholdWalletLedger`) |
| `tests/economy/_stage2_outside.py` | `cli_wire` | `interfaces/cli/wire_economy.py` | — | 3(`Ledger`・`_HouseholdWalletLedger`・`GoodsLedger`) |
| `tests/economy/cp2/test_cp2_nine_ops_equivalence.py` | `cli` | `interfaces/cli/main.py` | — | 3(`run`・`Ledger`・`_HouseholdWalletLedger`) |
| `tests/economy/cp2/test_cp2_nine_ops_equivalence.py` | `cli_wire` | `interfaces/cli/wire_economy.py` | — | 3(`Ledger`・`_HouseholdWalletLedger`・`GoodsLedger`) |
| `tests/engine/test_classical_policy.py` | `cli` | `interfaces/cli/main.py` | `build_parser` | 1 |

- 発注の見込み(4 行・3 ファイル)と違う所: 足した試験(§16-4)の別名 2 つも、割り先をまたぐ名(main の側で `_HouseholdWalletLedger`・wire_economy の側で `Ledger`)を読むので宣言が 2 行要った(+2 行・+1 ファイル)。

### 16-4. 割る前の試験の直し(どれも割る前は別名が全部 `shibuya.cli`=挙動は同じ)

- 別名を割り先ごとに分けた 3 本(1 回目の後・道具の既定で向く): `test_census_out`・`test_t3_manifest`・`test_cli`(`cli`=main・`cli_wire`=wire_economy・属性の読みのまま)。
- `test_resume_10d`: 別名 `cli` のまま(宣言で main)。差し替えの行に注 2 行。
- `_stage2_outside.use_outside_bundle`: 別名 `cli`(main)と `cli_wire`(wire_economy)。`Ledger`・`_HouseholdWalletLedger` は両方を同じ型で差し替え、`GoodsLedger` は wire_economy の側だけ。元の型は `cli_wire` から読む(差し替えの順は前と同じ=`Ledger` の後に財布の型を読む)。docstring に理由。
- `test_classical_policy`: 行は残し、別名 `cli` のまま(宣言で main・`build_parser` は無くてよい名)。注 2 行=確かめる事の無い行(常に偽)・段 8 の文の掃除の候補。
- 足した試験: `tests/economy/cp2/test_cp2_nine_ops_equivalence.py::test_the_outside_bundle_swaps_the_ledger_types_on_both_sides`(data なし)。省略の形と型を渡す形(HEAD の写し)の両方で、`use_outside_bundle` の後に main と wire_economy の `Ledger`・`_HouseholdWalletLedger` が同じ物で元の型と別の物・`GoodsLedger` は型を渡したときだけ wire_economy の側がその型・抜けると元に戻る。この助けを使うほかの試験 4 本は `cli.main` を呼ばないので、main の側の差し替えが外れても落ちない=この 1 本で確かめる(割った後の「外すと落ちる」の確かめは当てる発注の手順 6)。
- 書かない実行の後の字面(道具の書き換え): 7 本とも `from shibuya.interfaces.cli import main as cli`(と `wire_economy as cli_wire`)。`test_resume_10d` のコードの文字列(子のプロセスの台本)の別名は既定の決め方で main。

### 16-5. 試験と確かめ

| 何を | 結果 |
|---|---|
| 書かない実行 `split --through cli.py`(作業の木・頭 `b0afefd`) | 守り 13 個とも「同じ」(転送・契約を含む)・手で直す 0・別名の割り先の宣言 6・契約 2 → 2・宣言の外の弱まり 0・循環 0・写さなかった 0 |
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 133 本=112 passed・21 skipped(前の 103 passed に足した 9 本) |
| 足した道具の試験(9 本) | `test_split_alias_declaration_points_the_alias_to_the_declared_dest`(宣言どおりに向く・宣言が無ければ手で直す一覧=負の対照)・`test_negative_alias_declaration_guards_each_stop`(6 通り=守りごと)・`test_alias_declaration_names_the_names_that_may_be_absent`(挙げれば通る・挙げなければ止まる・腐った `absent` 2 通り)・`test_alias_declarations_name_files_and_aliases_that_exist_in_the_tree`(宣言が腐らない・負の対照 3) |
| 直した試験 7 本と、助けを使う試験(割る前の木・`-n 2`・`-m "not slow"`) | 145 passed・skipped 0(data あり)。直した 6 本(`test_census_out`・`test_t3_manifest`・`test_cli`・`test_resume_10d`・`test_classical_policy`・助けの `_stage2_outside` はその使い手で)と足した試験の在る `test_cp2_nine_ops_equivalence`、助けを使う `test_cp2_event_links`・`test_cp2_k17_capacity_and_overflow`(`test_stage2_world_two_day` は全部 slow で選ばれない)。助けを使う slow の試験(5,000 体 mock の 1 日)は回していない(足した試験が省略の形と型を渡す形の両方を見る) |
| slow の 1 本(本物の木で残りの本=cli を順に当てる) | `test_split_5a_5b_in_memory_keeps_the_import_rules_to_the_end` 1 passed(宣言が効いて 22 本目まで当たる)。あわせて、今の木で 22 本目をメモリの中で `strict` に当てると手で直す 0・宣言の報告 6、宣言の別名 6 つは割る前 `shibuya.cli`・割った後 宣言の割り先を import する(6/6) |
| `map --check`・`contracts --check --probe` | `map --check` 同じ・`contracts --check --probe` 同じ(例外 20 辺・延べ 26 行=全部効く・出力は G2 の直しの後と 1 バイトも同じ)。`git status --porcelain -- src` は空。カードを作り直した(3 枚=`tests/economy/cp2`・`tests/tools`・`tools/pkgmove`・`data.md` だけ戻した・`--check` 最新) |

### 16-6. 当てる発注(G3 の 2 つ目)へ送ること

- 差し替えの「外すと落ちる」(割った後に確かめる): `test_resume_10d` の 1 行=`pytest.raises(ValueError, match="自動補充")` が落ちる見込み。`use_outside_bundle` の 5 行=main の側 2 行は足した試験・wire_economy の側 3 行は足した試験と助けを使う data の試験が落ちる見込み。`run` の差し替え 21 か所(読む関数は `main()` だけ=main だけ・道具の既定のまま)は形ごとに 1 回。
- 記録に書く 1 行ずつ: `tools/instruments/batch_width_gauge.py` のコードの文字列は機械の書き換えのまま(割る前の木の src を渡す使い方では動かない=前から)・名の無い `"shibuya.cli"` の 2 か所(`test_night5070`・`tools/c8/ensemble.py`)は `-m` の入口として使う(属性を読む形でない=`ensemble.py` は `python -m shibuya.cli …` の命令の文字列・`test_night5070` は夜の台本に `tools/night5070/experiments.json` の `-m shibuya.cli` の字が在ることを確かめる)・`tests/c7` は道具が挙げた所 0。
- 割る前の側の準備は済み: `python -m shibuya.cli --help`(`PYTHONUTF8=1`・43,348 バイト)と `--llm mock` の既定のラン 1 本(final `c8d68704b7b0760d`・LLM 呼 60,939)を scratchpad に取った。結果は §17。

### 16-7. 親の確かめと検収(第347・2026-11-18)

- 別の役の検収: **受入**(高 0・中 0・低 2)。検収役はファイルを 1 本も変えていない。
  - 親の裁定の表(§16-2)は、検収役が土台の `cli.py` を読んで作った表と行の番号まで同じ(読み落としなし)。土台で `shibuya.cli` の属性を差し替える所は、別名を解いて 23 か所(`run` 19・`build_ledger_bundle` 1・台帳の型 3)。決まりを当てた差し替えの先は作業木の形と同じ。src に `shibuya.cli` を読むモジュールは 0(定義の割り先を差し替えの先に足す必要は無い)。
  - 道具の差分: 宣言はその割る行でだけ使われ、1〜21 本目では何もしない。`alias_dests` は組み直しただけで、割り先を決める条件は字面どおり同じ。守り 6 つ(発注の 4 つと実装役が足した 2 つ)は負の対照で 1 つずつ止まる。割り先に無い名は「無くてよい名」に挙げない限り止まる。拾わない形(点つきの文字列の的・コードの文字列の中の差し替え)は今の木に 0。
  - 割る前の試験の直し: 5 本は別名を 1 つに戻すと土台と AST が同じ。`_stage2_outside` は台帳の 2 つの型を両方の別名で、`GoodsLedger` を wire の側だけで差し替え、元の型は wire の側から読む(型を渡す形でも約束が成り立つ)。足した試験は、割った後に main の側の行を外すと落ちる形(割る前に外して落ちないのは、2 つの別名が同じモジュールなので正しい)。
  - 低-1(§16-2 の `run` の差し替えの数が 21=正しくは 19): 親が直した。低-2(`test_resume_10d` の差し替えと足した試験の「外すと落ちる」は、割った後でないと確かめられない): 当てる段(G3 の 2 つ目)で確かめ、§16-6 の「見込み」を結果に置き換える。
- 親の裁定: 実装役が発注の外で足した守り 2 つ(別名が素の名で使われていれば止める・`absent` の名が読まれていないか割り先で結ばれていれば止める)は**受け入れる**(宣言の在る別名にだけ効き、ほかの形を止めない=検収役が確かめた)。宣言が 6 行・4 ファイルになったこと(足した試験の分の 2 行)も受け入れる。
- 実装役の自己申告: grep の 1 つの範囲に `tests/c7` が入っていた(当たりは無く、中身は開いていない)。以後は範囲から外す。
- 親が回した確かめ(作業の木・src は土台と同じ=`git status --porcelain -- src` は空・src の指紋は G2 の後と同じ 371 本):

| 何を | 結果 |
|---|---|
| 直した試験 7 本の在るファイル・助けを使う試験・`tests/tools/test_pkgmove.py`(`-m "not gpu and not slow"`・`-n 2`) | 282 passed・21 skipped(飛ぶ 21 本は `test_pkgmove` の分)・落ちた試験 0 |
| 書かない実行 `split --through cli.py` | 守り 13 個とも「同じ」・手で直す 0・別名の割り先の宣言 6(書いていない) |
| `map --check`・`contracts --check --probe`・`lint-imports`・カード | 同じ・同じ(例外 20 辺・延べ 26 行)・11 kept・最新 |

## 17. G3 の当て(群の土台 `e6d221c`=E5 の commit・安定版のタグ `stable-v2-before-split5b-G3-apply`・2026-11-18)

### 17-1. 本の数

| 本 | 割る行 | 書き換えた import の文(src・tests・tools・docs) | 分けた文 | 鍵 | 台帳の道 | 道の文字列 | 書き換えなかった鍵 | 手で直した読み | 別名の割り先の宣言 | 写さなかった | 守り | byte-check | 契約 | 例外 載せた・効いている(辺/行) |
|---:|---|---|---:|---:|---:|---|---:|---|---:|---|---|---|---|---|
| 22 | `cli.py` | 189(0・177・4・8) | 0 | 2 | 1 | src の表 4・コード 28(記号 14) | 26 | 0(6 件は E5 の commit で済み=§16) | 6(4 ファイル) | 0 | 13 個「同じ」 | 19/19 同じ(440 秒) | 2+9 | 20/26・20/26 |

- 割り先: `interfaces/cli/main.py`(新・20 名と `if __name__ == "__main__":` の文 1)・`interfaces/cli/wire_economy.py`(新・10 名)。`shibuya/cli.py` は消さずに決まった型の転送で書き直した(裁定 Q6 の (a))。作った頭 0(`interfaces/cli/` は G2 で在る)。変わったファイル 126(書き換え 124+割り先 2)・消した 0。
- 転送: 字面は `table.forwarder_text("cli.py", "interfaces/cli/main.py")` と 1 バイトも同じ・`split.forwarder_problems` は 0・守り「入口の転送」は「同じ」。頂上で名を結ばない(docstring と `if __name__ == "__main__":` の中の import と呼び出しだけ)。
- 当てた後の import の確かめ: モジュール 372・落ちた 0・`python -m shibuya.cli --help`・`python -m shibuya.interfaces.cli.run_args --help` とも終了コード 0。
- 契約: 古い読み手 `shibuya.cli` が「読んでよい側」から外れた(2 つの契約の `allowed_importers` から 1 行ずつ=`pyproject.toml` −2 行)。単位 interfaces は言えるまま。契約 2+9・例外 20 辺・延べ 26 行のまま(全部効く)・計画に無い契約と例外は要らなかった。`lint-imports` 11 kept。
- 凍結と台帳: `CLASS_IDS` の鍵 2 つ(`_RemovedFlag` → main・`_HouseholdWalletLedger` → wire_economy)が変わり値は同じ・版の ID `shibuya.cli/checkpoints/2` は字面のまま(main)・`WALLET_DOMAIN` は wire_economy・台帳の道の表に `interfaces/cli/main.py` → `cli.py` を 1 行。src の道の表 4 か所(`ledger.py` の `ledger.money`・`ledger_ast.py` の `DiagExit` 2・`rng_audit.py` の `household_wallets`)は名の在る割り先へ。転送の今の道 `cli.py` と台帳の道の重なり: `tests/_places.py` の元の置き場は main の元の道を main 自身・wire_economy の元の道を `wire_economy.py`・転送を `cli.py` とし、`current_index` が重なり無しで作れる(G0 §9-3 の (a)・(b))。
- docs の記録の道具(import だけ・親の決定 7): `wallbounce-1012/10e/byte_check_10e.py`・`wave2-2026-09-30/wave2_bytecheck.py`(各 1 行)・`c10-relations-2026-09-28/rel8b_measure.py`・`wallbounce-1012/md23/tools/multiday_md23.py`・`wallbounce-1012/refr20b/tools/measure_refractory.py`(各 2 行)=5 本・8 行。tools は 5 本(`c6/c6lib.py`・`c7/salt_runs.py`・`instruments/anchor_gauge.py`・`instruments/batch_width_gauge.py`(コードの文字列)・`vocab/registry_from_tape.py`)。
- 範囲の外(E4): 書き換えたはずの所 0(`tests/tools/test_bytecheck.py` の `shibuya/cli.py` の字面は偽のエンジンを作る試験の材料=書き換えの対象でない)。
- tests/c7: 道具が挙げた所 0(書き換えた tests の 109 本に c7 は無い)。
- byte-check(基準 `e6d221c`・記録 `bytecheck_22`): 19 構成・37 欄すべて同じ 19・動いた 0・誤り 0・440 秒(既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939=前と同じ)。入口の解決(`tools/bytecheck/check.py` の `resolve_run`): 記録の開いた src の一覧で、基準の側は `shibuya/cli.py` を読み `interfaces/cli/main.py` を読まない(261 本)=`shibuya.cli.run`、比べる側は `interfaces/cli/main.py`・`wire_economy.py` を読み転送 `shibuya/cli.py` を読まない(262 本)=`shibuya.interfaces.cli.main.run`。

### 17-2. 使い方の表示と入口のラン(親の決め事 5)

- `python -m shibuya.cli --help`(`PYTHONUTF8=1`)を割る前(土台の src)と後で取った: 43,348 バイトで **1 バイトも同じ**(`prog` は転送の名 `cli.py` のまま=計画 §3-4 の見込みどおり)。
- `python -m shibuya.cli --llm mock`(既定のラン 1 本・5,000 体・1 日): 割る前(土台と同じ src)も後も final `c8d68704b7b0760d`・LLM 呼 60,939・保存則と診断の行も同じ。標準出力の違いは時間の行と、成長宣言の表の 6 行の並びだけだった。並びは台帳の `growth_parts`(`foundation/ports/ledger.py`)が鍵を `set` で回すため、文字列のハッシュの乱数で回ごとに変わる(割る段の違いではない)。`PYTHONHASHSEED=0` で前後を回し直すと、時間の行(壁時計・刻みあたり・内訳・過程別・movement)のほかは 1 バイトも同じ。

### 17-3. 頂上で読み込みの時に走る文と、読み込みの閉包(G2 の検収 低-1 と同じ見方)

- 割る前の `cli.py` の頂上で読み込みの時に走る文は 2 つ(`NON_ARM_RUN_KWARGS = frozenset(…)`=main・`if __name__ == "__main__":`=main)。環境変数・登録・確かめの文は無い。
- 読み込みの閉包(環境変数なしで `import` した後の `sys.modules` の shibuya の分):

| 読むもの | 閉包 | 土台の `import shibuya.cli`(161)から読み込まれなくなる | そのうち頂上に作用のある文を持つ |
|---|---:|---:|---|
| `import shibuya.interfaces.cli.main` | 162 | 0(`shibuya.cli` のほか。増えたのは main・wire_economy) | — |
| `import shibuya.interfaces.cli.wire_economy` | 39 | 123 | 23(下) |
| `import shibuya.cli`(転送・`-m` でない) | 2 | 159 | 23 を含む全部(名を結ばない=何も読み込まない) |

  wire_economy だけを読むと読み込まれなくなる 23 本: 読み込みの時に環境変数を読んで、置かれているか値が違えば止める 14 本(`economy/stage2_bind`(消した切替口 2 つ)・`world/laws/switch_rate`・`world/model/proximity`・`world/model/space/nav1`(`stop_if_set`)・`foundation/queues/batching`・`interim_bundles/calendar_self`・`mind/judge/decision/layer`・`runtime/clocks/{regional,speech,step_scope}`・`society/calendar_shadow`・`society/speech/layer`・`world/body/{energy,schedule}`)・既定の値を読むだけ 1 本(`foundation/journal/log`)・定数の表の自己確かめ(`assert`)や読み込みの確かめ(`raise`)だけ 8 本(`act/intake/undefined`・`engine/resolve`・`foundation/text/templates`・`foundation/vocab/{actions,agent_codes,events}`・`society/speech/port`・`world/body/reactions`)。転送だけを読む形では、ほかに `economy/accounts`・`economy/goods`(`assert`)と `foundation/write_permit`(既定の値を読むだけ)も読み込まれない。

- 環境変数を置いた前後の比べ(20 個=消した切替口の 9 個は値 `zz_invalid`・読み込みの時に値を確かめる 11 個は不正な値 `zz_invalid`。終了コード 1=止まる):

| 環境変数 | 土台 `import shibuya.cli` | 土台 `-m shibuya.cli --help` | 後 `-m shibuya.cli --help` | 後 `import …cli.main` | 後 `import …cli.wire_economy` | 後 `import shibuya.cli`(転送) |
|---|---|---|---|---|---|---|
| 止まる 15 個(`SHIBUYA_ECONOMY_STAGE2`・`SPACE`・`PROXIMITY`・`RATE_RULES`・`WAGE`・`MEAL_DEFAULT`・`CALENDAR`・`CALENDAR_SHADOW`・`DECISION_PORT`・`CLOCK`・`TALK_CLOCK`・`STEP_SCOPE`・`SPEECH_PORT`・`BODY_SCHEDULE`・`BATCH_WIDTH_S`) | 止まる | 止まる | 止まる | 止まる | **止まらない** | **止まらない** |
| 止まらない 5 個(`SHIBUYA_RULES_42`・`RULES_42B`・`DEFECT_FIXES_1103`・`SEAT_RELEASE`・`ABSENT_PROCESSES`=止める文のモジュールが入口の読み込みの閉包の外。消した切替口の 9 個は全部、ランの組み立ての最初の `check_environment`(`runtime/systems/assemble.py`)でも止まる) | 止まらない | 止まらない | 止まらない | 止まらない | 止まらない | 止まらない |

- **止まらなくなる形 2 つ(直さずに報告)**: (1) `import shibuya.interfaces.cli.wire_economy` だけを読む形(src に読み手 0・tests で `cli_wire` を読む 5 本は同じファイルで main も読む)。(2) 転送 `shibuya.cli` を `-m` でなく import する形(決まった型=名を結ばないので何も読み込まない。`-m shibuya.cli` は前と同じに止まる)。正しい環境のランと byte-check には効かない(入口 `-m shibuya.cli`・`interfaces.cli.main` の import は前と同じ 15 個で止まる。ランの組み立ては最初に `check_environment` を呼び、11 個の値の確かめのモジュールはランが必ず読み込む)。

### 17-4. 差し替えの「外すと落ちる」(親の決め事 3・E5 の検収 低-2・§16-6 の見込みの結果)

確かめに使った書き換えは、1 行ずつ一時に書き換えて試験を回し、同じ道具の中でバイトを戻した。毎回 `git diff` と `git status --porcelain` の指紋が確かめの前と同じことを見た。

| 差し替え(当てた後の行) | 外したとき | 結果 |
|---|---|---|
| `test_resume_10d` の `monkeypatch.setattr(cli, "build_ledger_bundle", endowed)`(cli=main) | 行を `pass` に | **落ちる**(`DID NOT RAISE ValueError`=`pytest.raises(…, match="自動補充")`)。対照: 同じ差し替えを定義の割り先 wire_economy へ向けても落ちる(=宣言が要る) |
| `_stage2_outside` の `mp.setattr(cli, "Ledger", ledger)`(main) | 行を `pass` に | **落ちる**(足した試験 `test_the_outside_bundle_swaps_the_ledger_types_on_both_sides`) |
| `_stage2_outside` の `mp.setattr(cli, "_HouseholdWalletLedger", wallet)`(main) | 行を `pass` に | **落ちる**(足した試験) |
| `_stage2_outside` の `mp.setattr(cli_wire, "Ledger", ledger)`(wire_economy) | 行を `pass` に | **落ちる**(足した試験)。HEAD の写しの 5,000 体の日(`test_5k_mock_day_matches_head[6.5]`)は通る=母集団のあるランは財布つきの台帳を作り、`Ledger` を直に作らない |
| `_stage2_outside` の `mp.setattr(cli_wire, "_HouseholdWalletLedger", wallet)`(wire_economy) | 行を `pass` に | **落ちる**(足した試験と `test_5k_mock_day_matches_head[6.5]` の両方) |
| `_stage2_outside` の `mp.setattr(cli_wire, "GoodsLedger", goods_cls)`(wire_economy・型を渡す形だけ) | 行を `pass` に | **落ちる**(足した試験)。`test_5k_mock_day_matches_head[6.5]` は通る=物の台帳は HEAD の写しと今の型で状態が同じ |
| `run` の差し替え 19 か所(どれも `monkeypatch.setattr(cli, "run", 代わり)`・cli=main・読む関数は `main()`=main だけ)。1 形 | `test_cli_intent_mode` の 1 行を `pass` に | **落ちる**(`KeyError: 'intent_mode'`=本物の `run` が回る) |

- 外しても落ちない行は 0。ただし wire_economy の側の `Ledger`・`GoodsLedger` の 2 行を落とすのは足した試験だけ(助けを使う前からの試験は、母集団のあるランと物の台帳の同値を見るので、この 2 つの差し替えに頼らない)。
- 割った後の木の差し替えの洗い(親の台本 `patch_targets` を割り先 2 つと転送に向けた写し): 26 か所=上の 25 か所と、`tests/tools/test_bytecheck.py` の `"shibuya.cli.run"` の字面 1(範囲の外 E4=入口の解決の試験の材料)。割り先どうしの間で空振りする形は 0。
- 転送を黙って読む形: tests と tools では 0(転送を読む別名が残る所 0・道の文字列 `shibuya/cli.py` は見本の木と偽のエンジンを作る試験の材料と docstring だけ)。docs の記録(記録の道具 5 本のほか)には `from shibuya import cli` が残る古い台本が 116 本(属性で読む=大きな音で落ちる)と、`weather-a48-347/stop_paths_a48.py` が別名を関数へ素で渡す 1 本(〔検収の中-1〕広い `except` の中で読むので、落ちずに『止まった』と黙って記録する。`arms_check.py` も同じ形。直した=§17-10)。G0 で直した 15 本+3 は割り先を見ている(§17-6)。

### 17-5. コードの文字列 14 か所

| ファイル::記号 | 回る src | 道具の書き換え | 狙いの試験 |
|---|---|---|---|
| `tests/engine/batching/test_conductor_windows.py::_CODE` | 今の木(子は親の環境を受け継ぐ) | `from shibuya import cli` → main | `_cli` を使う試験 passed |
| `tests/engine/calendar/test_calendar_shadow.py::_cli_sub` | 今の木(同) | 同 | `test_cli_flag_beats_the_environment` ほか passed |
| `tests/engine/clock/test_tm3_step_scope.py::_CODE` | 今の木(同) | 同 | `test_cli_step_scope_beats_the_environment_and_is_an_arm` passed |
| `tests/engine/clock/test_tm4_regional_clock.py::_CODE` | 今の木(同) | 同 | `test_cli_clock_regional` passed |
| `tests/engine/decision/test_j0_cli.py::_arm` | 今の木(同) | 同 | `test_cli_decision_port_beats_the_environment` passed |
| `tests/engine/memory/test_m0_cli.py::_columns` | 今の木(同) | 同 | `test_cli_memory_store_beats_the_environment` passed |
| `tests/engine/memory/test_mr65_grain_and_cli.py::CODE` | 今の木(同) | 同 | `_arms` を使う試験 passed |
| `tests/engine/proximity/test_runs.py::_cli` | 今の木(同) | 同 | `test_cli_runs_distance_and_the_removed_cell_switch_stops`・`test_cli_proximity_d_arm` passed |
| `tests/engine/proximity/test_runs.py::test_cli_runs_distance_and_the_removed_cell_switch_stops` | 今の木(同) | 同 | 同 passed |
| `tests/engine/speech/test_speech_cli.py::_arm` | 今の木(同) | 同 | `test_cli_speech_port_beats_the_environment` passed |
| `tests/engine/test_env_and_sections_10f.py::_T1_CHILD` | 今の木(`cwd=ROOT`・環境を受け継ぐ) | 同 | `test_t1_two_processes_write_the_same_env_id_and_final_to_the_files` passed |
| `tests/engine/test_removed_switches_346.py::CLI_MAIN` | 今の木(同) | 同 | `test_a_run_with_a_removed_switch_env_stops_before_the_ticks` passed |
| `tests/engine/test_resume_10d.py::_CHILD` | 今の木(同) | 同 | `test_resume_in_a_fresh_process_with_empty_caches` passed |
| `tools/instruments/batch_width_gauge.py::_CHILD` | `--src` の木(既定=道具のリポの src=今の木)。割る前の木の src を渡す使い方では動かない(前から=頂上でも `shibuya.foundation.…` を読む) | 同 | `tests/tools/test_batch_width_gauge.py` passed |

- 古い commit・別の木の src で回る子のコードは 0(`test_state_format_10f._HEAD_CHILD` は `STRING_EXCLUDE` で書き換えない=G2 の F1)。書き換えは 14 か所(道具の数え方で 28)。当てる前に 1 か所ずつ「どの src で回るか」を見た(13 か所は子が親の環境を受け継ぐ・1 か所は `--src`)。
- 名の無い `"shibuya.cli"` の 2 か所は書き換えない(転送の名): `tools/c8/ensemble.py`(`python -m shibuya.cli …` の命令の文字列)・`tests/tools/test_night5070.py`(夜の台本に `tools/night5070/experiments.json` の `-m shibuya.cli` の字が在ることを確かめる)。どちらも `-m` の入口として使う(属性を読む形でない)。

### 17-6. 中身を見る試験・宣言の腐り

- `tests/_places.py` の口: `split_files("cli.py")` は `interfaces/cli/main.py`・`interfaces/cli/wire_economy.py` の 2 本(転送を数に入れない)・`split_source("cli.py")` は 2 本をつないだ字面(79,675 字=main と wire_economy の字数の和+区切り 1)で転送の docstring を含まない・`split_module_names` は 2 つの葉。表の鍵の字面 26 か所は書き換えていない(`table_key_sites`)。
- 宣言の腐り: 当てた後、`SPLIT_ALIAS_DESTS` の 6 つの別名は宣言の割り先を import している(E5 の試験 `test_alias_declarations_name_files_and_aliases_that_exist_in_the_tree` が当てた後の木で通る=§17-7)。

### 17-7. 狙いの試験(作業の木・`-m "not slow"`)

| 何を | 結果 |
|---|---|
| 変わった試験のファイル 107 本と、助けを使う `tests/economy/cp2`・`tests/economy/stage2`・`tests/engine/duties`(`-n 2`) | 1,652 本=1,651 passed・1 failed・skipped 0。落ちた 1 本は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(`tools/vocab/registry_from_tape.py` の `_relative` が `path.resolve()` をリポの根からの相対にする=作業木の `data` はリンクなので resolve した道が作業木の外になり名だけを返す。作業木でだけ落ちる前からの 1 本=§15-4 の「1 failed」と同じ形。割る段の違いではない: 書き換わったのは import の 1 行だけで、`REPO_ROOT` は道具の置き場から引く) |
| `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし) | 133 本=111 passed・22 skipped(増えた 1 本は §17-8。〔再検収の低-1〕§17-10 の直しの後は 112 passed・21 skipped=その 1 本が passed に戻った) |
| `tests/tools/test_pkgmove.py` の slow 1 本(`test_split_5a_5b_in_memory_keeps_the_import_rules_to_the_end`) | passed(当てる本 0・終わりの木の確かめ=22 本済み・転送・契約 2+9・単位 interfaces) |
| 決まりの束(`tests/c8/test_c8lib.py` を先に=19 passed)・`tests/engine/time`・`state`・`bridging`・`systems`・`tests/test_places_guard.py`・`tests/tools` の残り 22 本(`test_bytecheck.py`・`test_batch_width_gauge.py` を含む・`-n 2`) | 958 passed |
| E5 の試験(宣言の腐り・宣言の守り) | 上の `test_pkgmove` の中で passed(`test_alias_declarations_name_files_and_aliases_that_exist_in_the_tree` は当てた後の木で通る) |

### 17-8. 5b の終わり

- 22 本が全部済んだ木で `split --next`(と `--through all`)は「割る段は全部当たっている」。
- `tests/tools/test_pkgmove.py` で飛ぶ試験は 21 → 22。増えた 1 本: `test_split_dry_run_of_the_next_row_writes_nothing_and_keeps_every_guard`(「割る段は全部当たっている」で飛ぶ)。確かめなくなった事: 本物の木で `cli.py split --through <次の本>`(書かない実行の口)が何も書かず(`map.toml`・`pyproject.toml` のバイトが同じ)、守りが全部「同じ」で、報告の要約を書くこと。**ほかで確かめている所**: 守りが全部「同じ」は見本の木の試験(`test_split_sample_composes_dests_and_rewrites_readers` ほか)と、メモリの中で当てる slow の 1 本。CLI の書かない実行の口が何も書かないことは、見本の木では確かめていない(`run_cli` は本物の木でしか回らない)=**確かめる範囲が 1 つ減る(直さずに報告)**。〔親の裁定〕直した=§17-10。段 6 で割る行が足されると、この試験はまた回る。
- 飛ぶ試験の残り 21 本は前と同じ(段 4 の当て済みの木・移したファイルが残っていない木・本物の木の順の試験=割る段の終わり)。

### 17-9. 計画・G0 の数と違った所・止まる所・段 6 に送ること

- 計画・G0 の数との違い: 手で直す読みの 6 は E5 の commit で済み(当てる時 0)。宣言は 6 行・4 ファイル(§16)。書き換えた tests は 109 本(import の文 177)。
- 止まった所: 無い(割り先どうしの間で空振りする差し替え 0・計画に無い契約と例外 0・古い src で回る子のコード 0)。
- **親に見てほしい所(直さずに報告)**: (1) 読み込みの閉包で止まらなくなる形 2 つ(§17-3=wire_economy だけの import と、転送を `-m` でなく import する形)。(2) `test_pkgmove` の CLI の書かない実行の試験が飛ぶ側へ移り、確かめる範囲が 1 つ減る(§17-8)。(3) `use_outside_bundle` の wire_economy の側の `Ledger`・`GoodsLedger` の差し替えを落とすのは、E5 で足した試験だけ(§17-4)。
- 前からの欠陥(割る段と関係ない・報告に載せる): 台帳の `growth_parts` が鍵を `set` で回すので、成長宣言の表の行の並びがハッシュの乱数で回ごとに変わる(§17-2・標準出力だけ)。`registry_from_tape` の相対の道は作業木のリンクの `data` で名だけになる(§17-7)。
- 段 6 に送ること: 割る段の道具は 22 本が済んだ。段 6(`resolve.py` を 18 の割り先へ)では、差し替える名を読む関数の割り先と定義の割り先が違う形が増える見込み=E5 の宣言の口を使い、差し替えの届く先の守り(E5-b)を道具の拡張(S6-G0)で計画する。CLI の書かない実行の試験は割る行が足されると戻る。

### 17-10. 検収の後の直し(検収=条件つき受入の中 1・低 1・親の裁定)

- 直し 1(検収の中-1): docs の古い台本 2 本(`weather-a48-347/stop_paths_a48.py`・`wallbounce-1012/run-day-decomp/arms_check.py`)の import の行だけを手で直した(`from shibuya import cli` → `from shibuya.interfaces.cli import main as cli`=道具が記録の道具に当てる書き換えと同じ形・各 1 行)。なぜ: どちらも `try:` の中で `cli.run(...)` を呼び `except Exception` で誤りを結果に書く形で、割った後は転送に `run` が無い AttributeError が「止まった」「ok: False」として黙って記録される(土台では動いていた)。道具の書き換えの範囲(記録の道具)の外なので、手で直す一覧に出なかった。記録の道具の一覧(`RECORD_TOOLS`)には足していない。確かめ: 名 `cli`(import の別名と、`stop_paths_a48.py` の `_one` の引数)の属性の読みを AST で全部挙げると、2 本とも `run` だけ(`stop_paths_a48.py` の 21 行・`arms_check.py` の 39 行)で、`interfaces/cli/main.py` の頂上に在る。`stop_paths_a48.py` の素の `cli` は 40・44 行(`_one` へ渡す所)だけ。2 本とも `ast.parse` が通る・差分は import の 1 行ずつ(`git diff --stat` で 2 本・各 1 行)。台本そのものは回していない。検収役の数え方(docs の古い台本 116 本のうち、広い `except` の中で別名の属性を読むのはこの 2 本だけ・72 本は土台で既に無いモジュールを import していて前から動かない)は検収役の言い分のまま(数え直していない)。§17-1 の表の「手で直した読み」の 0 は道具の範囲の数のまま。
- 直し 2(検収の低-2・実装役が上げた 2): `tests/tools/test_pkgmove.py` の `test_split_dry_run_of_the_next_row_writes_nothing_and_keeps_every_guard` を、割る行が残り 0 の木でも飛ばさない形にした(返事その 8 §1-1 の (b)「確かめる範囲を減らさない」)。残り 0 の木では、本物の木で書かない実行の口を 2 つの形(`split --next`・`split --through all`)で回し、終了コード 0・標準出力に「割る段は全部当たっている」・`--out-dir` に渡した置き場にファイルが 1 本も無い・`tools/pkgmove/map.toml` と `pyproject.toml` のバイトが前と同じ、を確かめる。割る行が残っている木の確かめは 1 字も変えていない(段 6 で行が足されたら元の道を通る)。docstring に 1 句。見本の木で CLI の書かない道を回す試験は足していない(段 6 の S6-G0 の道具の拡張)。確かめ: `tests/tools/test_pkgmove.py`(`-m "not slow"`・`-n` なし)133 本=112 passed・21 skipped(この 1 本が passed に戻った)。
- 裁定 1(止まらなくなる import の形 2 つ=`wire_economy` だけの import と、転送を `-m` でなく import する形): そのまま(入口 `-m shibuya.cli` と main の import は前と同じに止まる・転送に確かめの文を足すと決まった型を崩す)。
- 裁定 3(`use_outside_bundle` の wire_economy の側の `Ledger`・`GoodsLedger` の 2 行を落とすのは E5 で足した試験だけ): そのまま(割る前から薄かったという検収役の見立て。足した試験で初めて捕まるようになった)。
- 直した後の確かめ: カードを作り直した(試験のファイルの直しの直後に続けて・`data.md` だけ単独で戻した・`--check` 最新)・`split --next` は「割る段は全部当たっている」・`map --check` 同じ・`contracts --check --probe` 同じ(例外 20 辺・延べ 26 行=全部効く・出力は当てた直後と同じ)・秘密の走査 CLEAN。src・`tools/pkgmove/`・`tools/bytecheck/` は変えていない。

## 18. G3 の親の確かめと検収(第347・2026-11-18)

### 18-1. 別の役の検収

- 判定: **条件つき受入**(高 0・中 1・低 4)。src・試験・道具に欠陥は見つかっていない。検収役はファイルを 1 本も変えていない。
- 道具の当て直し: 土台 `e6d221c` をメモリに読み、今の道具と表で 22 本目を当て直した。作業木との違いは 0 本(手で直した所は無い)。割り先 2 本の頂上の文は、字面・AST・前の注まで元と同じ。`tools/pkgmove`・`tools/bytecheck`・`tests/c7` の差は 0 本。docs の記録の道具 5 本は import の 8 行だけ。
- 転送: `shibuya/cli.py` は決まった型と 1 バイトも違わず、名を結ばない。`import shibuya.cli` だけでは何も読み込まれない。`-m shibuya.cli --help` は検収役が前後の両方を取り、43,348 バイトで 1 バイトも同じ。
- 転送を黙って読む形: src・tests・tools には 0。名の無い `"shibuya.cli"` の 2 か所は `-m` の入口として使う形。黙って読む形は docs の古い台本 2 本だけ(中-1)。
- 差し替えの向け先: 25 か所(`run` 19・`build_ledger_bundle` 1・台帳の型 5 行)とも決まりどおり。親の表(§16-2)は土台の `cli.py` の読み手の行で正しい。助けを使う 4 本の試験は `run` だけを呼ぶ。足した試験は、助けの行を 1 つずつメモリの中で外した写しで 5 行とも落ち、外さない対照は通る(型を渡す形も試験の中で回る)。
- 読み込みの時に走る文: 頂上で走るのは `NON_ARM_RUN_KWARGS` と `__main__` の節で、どちらも main へ行った。消した切替口の環境変数を置いた前後の比べは実装役の表(§17-3)と合う。
- コードの文字列 14 か所: どれも今の木の src で回り、古い src で回る物は無い。代表 2 本を単独で回して passed。
- 範囲の狭まり・空回り: 無い。`split_files("cli.py")` は main と wire_economy を返し(転送は入らない)、表の鍵の字面は書き換わっていない。`test_classical_policy` の行は残り、別名だけが main。
- 入口そのもの: `--llm mock` の前後の出力はどちらも呼数 60,939・final `c8d68704b7b0760d`(`PYTHONHASHSEED=0` の 2 つは、時間の行を除いて同じことを検収役が比べた)。byte-check の記録の開いた src の一覧から、基準の側が転送の `cli.py`、比べる側が main と wire_economy を通ったことが分かる。
- import の決まり(`contracts --check --probe`): 契約 2+9・例外 20 辺/26 行で全部効く。`shibuya.cli` は決まり 5・9 の読んでよい側から外れた(決まりが強まる側)。循環は 0(main と wire_economy の間にも無い)。
- 凍結: `CLASS_IDS` は鍵 2 つだけが変わり値の集合は同じ。凍結の JSON とつなぎの台帳に差は無い。`shibuya.cli/checkpoints/2` は main に字面のまま・`WALLET_DOMAIN` は wire_economy に在る。`tests/c7` の差は 0 本。
- 成長の表の並び(§17-2): `growth_parts` が `set` を回す作りは土台と同じ。順が入るのは `growth_measured` と標準出力の表だけで、final・呼数・manifest・ハッシュには入らない(検収役が使う所を辿った)。割ったことの違いではない(前からの欠陥として報告に載せる)。
- 直しの差分(§17-10)の再検収: **受入**(高 0・中 0・低 2)。前の当て直しの台本を回し直すと、道具の出力と違うのは `test_pkgmove` の 1 本だけ(src・`tools/pkgmove`・`tools/bytecheck`・`tests/c7` に新しい差は無い)。直した 2 本は import の 1 行だけが変わり、docs を走査し直すと、転送を import する台本は残り 114 本で、黙って読む形は 0。足した枝は空回りしない(何かを書けば・文が出なければ・終了コードが 0 でなければ落ちる。単独で回して passed)。低-1(§17-7 の表の数が直す前のまま)は親が 1 句足した。低-2(直した 2 本は記録の道具の一覧の外)は §18-2 の中-1 に送り事項として書いた。

### 18-2. 検収の中 1 件・低 4 件の扱い

- 中-1(docs の古い台本 2 本が、割った後は誤りを飲み込んで「止まった」と黙って記録する): **直した**(§17-10 の直し 1= import の行だけ・各 1 行)。親が AST で確かめた(2 本とも、別名 `cli` の属性の読みは `run` だけで、`interfaces/cli/main.py` の頂上に在る)。台本は回していない。記録の道具の一覧には足さない(一覧は「tests が道で読む台本」の走査と同じでなければならない)。古い台本(検収役の数えで 116 本・うち 72 本は前から動かない)の扱いは報告の判断待ちに上げる。段 6・段 7 でも、当てる前に同じ走査(広い `except` の中で割るモジュールの別名の属性を読む形)を回す。〔再検収の低-2〕直した 2 本は記録の道具の一覧の外のままなので、これからの段で `run` が main からほかへ動くと、また黙って誤る形に戻る=その走査で、この 2 本も毎回見る(段 6 への送り事項)。
- 低-1(**変わった所**=読み込みの時の止める文が走らない形が 2 つ): **親の仮採用=そのまま**(G2 の §15-2 の低-1 と同じ扱い)。**親が前後で動かして確かめた**(`SHIBUYA_RATE_RULES`・`SHIBUYA_CLOCK`・`SHIBUYA_ECONOMY_STAGE2` に不正な値): 土台の `import shibuya.cli`・`-m shibuya.cli --help` は終了コード 1。割った後の `-m shibuya.cli --help`・`import shibuya.interfaces.cli.main` は終了コード 1(前と同じに止まる)、`import shibuya.interfaces.cli.wire_economy`・`import shibuya.cli`(転送)は終了コード 0(止まらない)。転送は名を結ばないので、読み込んだだけでは何も使えない。`wire_economy` だけを読む読み手は src に無い(試験の助け 1 本だけ)。転送に確かめの文を足すと、決まった型(裁定 Q6 の (a))を崩すので足さない。
- 低-2(本物の木で CLI の書かない道を確かめる試験が飛ぶ): **直した**(§17-10 の直し 2=残り 0 の木でも飛ばさず、書かない実行の口が何も書かないことを確かめる)。見本の木で CLI の書かない道(要約の JSON・守りの表示)を回す試験は、段 6 の S6-G0 の道具の拡張に入れる(CLI は本物の表を読む)。
- 低-3(`interfaces/cli/main.py` の docstring の見出しが `shibuya.cli —` のまま): そのまま。割る段は文を変えない(1 バイト不変)。段 8 の文の掃除で直す。
- 低-4(宣言の要る形を、割る前に確かめる口が無い): 段 6 の手順に入れる(別名の割り先の宣言を使った差し替えは、当てた後に「外すと落ちる」を1 行ずつ確かめて記録する)。今回は §17-4 で確かめた。

### 18-3. 実装役が上げた 3 点の裁定

- (1) 止まらなくなる import の形 2 つ: そのまま(§18-2 の低-1)。
- (2) 飛ぶようになった道具の試験: 直す(§18-2 の低-2。返事その 8 §1-1 の (b)「確かめる範囲を減らさない」)。
- (3) `use_outside_bundle` の wire_economy の側の `Ledger`・`GoodsLedger` の差し替えを落とすのは E5 で足した試験だけ: そのまま。検収役の見立て=割る前から薄かった(助けを使う 4 本は `run` だけを呼び、母集団のあるランは財布つきの台帳を作る。割る前の 1 行の時も、効き方は今の wire_economy の側の行と同じ)。足した試験で初めて捕まるようになった。`b0afefd` の時点でどの試験が落ちたかは回していない。

### 18-4. 親が回した確かめ

| 何を | 結果 |
|---|---|
| byte-check 19 構成(本体の道具・基準 `e6d221c`・22 本目を当てた後の木) | 37 欄すべて同じ 19・動いた 0・誤り 0・449 秒・既定の `w6_v3_default` の final `c8d68704b7b0760d`・呼数 60,939。比べる側の開いた src に `interfaces/cli/main.py`・`wire_economy.py` が在り、転送 `shibuya/cli.py` は無い。記録 [bytecheck_G3_parent/](bytecheck_G3_parent/) |
| byte-check の後に変わったファイル(時刻で洗った) | src・`tools/pkgmove/`・`tools/bytecheck/` は 0 本。変わったのは §17-10 の直しの 4 本(docs の台本 2・`tests/tools/test_pkgmove.py`・この記録)とカードだけ=byte-check は有効。src の指紋は 373 本(割る前の 371 本+割り先 2 本) |
| 範囲の全体の試験(`tests` から `tests/c7` を除く・`-m "not gpu and not slow"`・`-n 4`・当てた後の木) | 6,960 passed・1 failed(前からの 1 本=linked の作業木でだけ落ちる)・23 skipped・1 xfailed・40 分 28 秒(§17-10 の直しの前に集めた回)。前の 6,951 passed・22 skipped から、E5 の commit で足した試験 10 本で +10・本物の木の書かない実行の試験 1 本が飛ぶ側へ移って −1(飛ぶ試験は 22 → 23)。その 1 本は §17-10 の直しで passed に戻る(下の行)。範囲の全体は直しの後に回し直していない(直しは `tests/tools/test_pkgmove.py`・docs の台本 2 本・この記録・カードだけ) |
| §17-10 の直しの後の `tests/tools` の束(`-m "not gpu and not slow"`・`-n 2`) | 754 passed・21 skipped・落ちた試験 0(飛ぶ 21 本は `test_pkgmove` の分=直す前の 22 本から、この 1 本が passed に戻った) |
| `python -m shibuya.cli --help`(`PYTHONUTF8=1`)を割る前(本体の木= src は `e6d221c`)と後で取った | 43,348 バイトで 1 バイトも同じ。割った後の `shibuya.cli` の頂上の名は 0 |
| 不正な環境変数を置いた前後の比べ(3 つ・§18-2 の低-1) | 入口と main の import は前と同じに止まる・`wire_economy` だけの import と転送の import は止まらなくなった |
| 直した台本 2 本の AST(§18-2 の中-1) | 別名 `cli` の属性の読みは `run` だけ(`stop_paths_a48.py` の 21 行・`arms_check.py` の 39 行)・main の頂上に在る・`shibuya` の import はほかに変わっていない |
