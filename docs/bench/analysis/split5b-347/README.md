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
