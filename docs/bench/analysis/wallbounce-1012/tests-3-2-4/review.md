# 3-2-4 検収(第333・取り出したばかりの状態での試験)

- 検収役 Opus 5.5。実装は見ていない。対象は作業木の未 commit の変更(枝 `build/spatial-d102-prep`・HEAD `adc2b93`)と実装役の記録 [README.md](README.md)。読むだけで、書いたのは本記録だけ。
- **判定: 条件つき受入**。条件は M1(実装役の記録の古い記述 4 か所を、親が後から直した 2 点に合わせる)。コードと CI の定義に「高」の欠陥は無い。低の 8 件は任意。

## 1. 確かめたこと(1〜8)

| # | 項目 | 判定 | 根拠 |
|---|---|---|---|
| 1 | fixture の同一性 | ✓ | md5 `733fabb6b488794a0cd3d94df4b1f24a`・21,538 B・cp932 で strict に読める(UTF-8 では読めない)・CRLF 1,068 本/LF 1,068 本/裸の CR 0。`cmp` で `data/calendar/syukujitsu.csv` と同じ。`git check-attr -a` は binary=set・text=unset(`eol: lf` は残るが text が unset なので効かない)。`git hash-object --path=…` と `--no-filters` がどちらも `76e45cd7…`=改行の変換は起きない |
| 2 | conftest の複製の条件 | ✓ | `tests/conftest.py:57-72`: あれば return・無いときだけ一時名に写して `os.replace`・書くのは `data/calendar/` の下だけ。`git diff .gitignore` は空。`git check-ignore` で `data/` は無視のまま、fixture は無視されない。W0(§8)では 2 並列でも複製は 1 回(controller が先に読む)・一時ファイルは残らない・複製後の md5 は同じ |
| 3a | 試験の名・assert の中身 | ✓ | `git diff -U0 -- tests` の +/- 行から assert と def を全部抜いた。変わった assert は環境依存の 4 種(時間の門 8 ファイル 11 か所・t 分位 2 行・ホスト名 1 行・「登録済みか」1 行)だけ。試験の名と slow/gpu/xfail/parametrize の印は不変。消えた行は `skipif`・`pytest.skip`・`assets_available` の判定と補助 `_real_world_or_skip` だけ |
| 3b | 前の条件と id が同じファイルを見るか | △ | 82 か所を定数の定義(`WORLD_DIR`・`REAL_INPUTS`・`GML`・`RN.ROAD_NAMES`・`W.KASYO`・`R.BOUNDARY_*`・`PerceptionAssets.REQUIRED_FILES`=7 ファイル・`CAL.DEFAULT_HOLIDAY_CSV` ほか)までたどって照らした。違いは 2 種: (i) `tests/engine/test_calendar_sites.py:170` は前が `Path("data/world/v2").is_dir()`、今は `world_v2`(6 ファイル=`assets_available`)=前より厳しい(L3)。(ii) 前の判定が cwd 相対(`Path("data/world/v2")` など)だった約 25 ファイルが根からの道筋になった(L4)。`is_file()`→`exists()` の 3 か所は実質同じ |
| 3c | 印の付け忘れ | ✓ | `skipif` は 0 本。残る `pytest.skip` 14 か所と `importorskip` 4 か所は全部 data 以外(git の有無・旧 commit・環境変数・合成の世界・golden の行・辞書の版・追跡済みの anchors 台帳)。`exists()/is_file()` で飛ばす所は残っていない。新しく印を足した `test_calendar_10e_e3.py::test_e3_two_days_…` は、W0 で印を外して回すと `assert [] == [(1, 0)]` で落ちた(合成の世界では計画実行層が動かない)=印は要る(id の選び方は L5) |
| 3d | `D.skip_unless` 5 か所 | ✓ | `test_calendar_sites.py:177`(`pa.has_timetable`)・`test_relations_tenure.py:153`(`assets_available`)・`test_version_bump_10e.py:266`(W17 の有無)・`test_build_run_keep_stage.py:144-145`(W17 の有無→md5 の頭)。5 か所とも前と同じ条件・同じ順 |
| 4a | golden の表の試験 | ✓ | `REGISTERED=()` で未登録を模した: 警告(`GoldenUnregisteredWarning`)だけで通る。表の値を 1 つ書き換えると落ちる。登録済みでは前の assert が全部残る(消えたのは「登録済みか」の 1 行だけ=K26 (1) に合う。L2) |
| 4b | ホスト名 | ✓ | 値の葉(文字列)との完全一致。`platform.node()` を差し替えて回した: `vm`・`runnervm0abc`・空文字は通る(空は前と同じく検査しない)。葉と同じ名(例 `Windows`)は偽赤・長い値に埋め込まれた名は捕まえない(L6) |
| 4c | t 分位 | ✓ | 期待値は `seed_ensemble.t_quantile_995`(`prereg_v13` が import して使う同じ関数)から組む=scipy の有無のどちらの枝でも自己整合。表の値との近さ(rel 1e-3)と `st["t_quantile"]` の検査は残る。ほかの 9.925 の比較(`test_seed_ensemble`・`test_salt_compare_10f`)は許容 1e-3/6e-4 で、ppf の 9.92484 でも落ちない |
| 4d | 時間の門 | ✓ | 8 ファイル 11 か所。`TG.check` は既定で `bool(ok)` を返す=前と同じ assert(`tests/_time_gates.py:35-36`)。記録だけになるのは値が `record`(大小と前後の空白は無視)のときだけで、`1` などでは記録にならない。条件・上限・文言は前のまま。slow の 35 本を集めて、時間の門で変えていないものは無い |
| 5 | 子プロセスの穴 | ✓ | `tests/conftest.py:49-54`: 先頭が `<rootdir>/src` なら足さない(先頭以外にあれば重複して足すが無害)・`os.pathsep`。`test_state_format_10f.py:467` は `dict(os.environ, PYTHONPATH=…)` で丸ごと置き換える=上書きされない。`test_child_imports_this_tree.py` は cwd を一時の置き場にした子を起こして `shibuya.__file__` を見る。W0 で `PYTHONPATH` の無い子が本体の `src` を読むことを確かめた=穴は実在し、試験は W0 で通る |
| 6 | CI の定義 | ✓ | ci-0(md5 の固定・秘密スキャン・`lint-imports`・`data/` が未追跡)/ci-1(`-m "not gpu and not slow" -n 2 --dist loadfile`・`fetch-depth: 0`)/ci-2(cron と dispatch・`slow and not gpu`・`SHIBUYA_TIME_GATES=record`)は要件どおり。ci-0 は親の直し(`scan_secrets.py` が cp932 も試す)で fixture もスキャンの対象。手元で追跡ファイルと新規の 1,891 本を 150 本ずつスキャンして全部 CLEAN。`pytest-xdist==3.8.0`(venv も 3.8.0)。要約は W0 で一時のファイルに 1 回だけ、表の形も正しく書かれた |
| 7a | 未登録の id | △ | 置き場が未登録なら `UsageError`(直列は rc 4 で試験の名と id を出す)。2 並列では INTERNALERROR(rc 3・crashitem)で止まる=落ちるが文言が読みにくい(L7)。引数の無い印も `UsageError`。`skip_unless` の未登録は `ValueError` で fail。**置き場は正しく相対パスを書き間違えた id は黙って飛ぶ**(要約に「data が無い」として数えるだけ・L1) |
| 7b | assert の後で飛ぶ所 | ✓ | 2 本(`test_relations_tenure` の切替の試験・`test_build_run_keep_stage`)。どちらも前と同じ位置で飛んでいた。結果は skipped と出て passed にはならない |
| 7c | xdist | ✓ | `pytest_collection_modifyitems` は worker ごとに走るが、判定はファイルの有無だけなので全 worker で同じ収集になる。`pytest_terminal_summary` は controller だけで、`GITHUB_STEP_SUMMARY` も `workerinput` を除く=二重にならない(W0 で確かめた) |
| 8 | data 無しの再現 | ✓ | 下の §2 |

## 2. data 無しの再現(W0)

- 作り方: `git ls-files` の全ファイルと、未 commit の変更(M と ??。削除の 1 本は除く)を作業木から一時の置き場へ写した(1,891 本・`data/` なし・`.git` なし)。実装役の W0(HEAD+本変更だけ)と違い、作業木の他の作業の変更も入っている。
- 命令: 指示のとおり(`-m "not gpu and not slow" -n 2 --dist loadfile -x --maxfail=5`・6 つの道筋・`PYTHONIOENCODING=utf-8`)。`GITHUB_STEP_SUMMARY` は一時のファイルに向けた。
- 結果: **205 passed・0 failed・2 skipped・65 秒**。conftest が fixture を複製した(1 行の通知・md5 同じ)。

| id | 飛ばした数 |
|---|---:|
| `world_v2:w2_cells.parquet` | 2 |
| data 以外の理由 | 0 |

- ついでに確かめたこと(W0 の中だけ・終わった後に消した): 未登録の id・書き間違いの id・引数の無い印・`skip_unless` の未登録の動き(7a)/印を外した e3 の試験が落ちること(3c)/未登録の環境を模した golden の表の試験(4a)/ホスト名の差し替え(4b)/`TG.check` の既定と記録(4d)。
- W0 は `[IO.Directory]::Delete` で消した。本体の作業木の `git status` は検収の前と同じ 108 項目。

## 3. 欠陥(重さ順)

| # | 重さ | 場所 | 中身 | 直し方の案 |
|---|---|---|---|---|
| M1 | 中 | `README.md`(本記録の隣)の 4・14・33・83・106・140 行 | 親が後から直した 2 点が記録に入っていない。(a) 「`src/` と `tools/` は変えていない」→ `tools/scan_secrets.py` が変わった。(b) 「CI ではスキャンから外し」「73 件 HIT する」「判断待ち」→ 今は cp932 も試すので 0 件で、ci-0 は fixture もスキャンする。(c) golden の表の試験は「`pytest.skip`」→ 今は警告だけで検査を続ける。(d) §8 の判断待ち 2 件は決着済み。ほかに 50 行の「REQUIRED_FILES の 5 ファイル」は 7 ファイル | commit の前に該当の行を今のコードに合わせ、「親が後から直した 2 点」の小節を足す。正典になる記録なので、写しの事故として扱う |
| L1 | 低 | `tests/_data_ids.py:100-108`(`check_id`) | 置き場の後ろの相対パスは検査しないので、書き間違えると data のある機械でも黙って飛ぶ(要約に「data が無い」と 1 行出るだけ)。前の `skipif` の道筋の書き間違いと同じで、回帰ではない | 作者の機械の夜間用に、印で飛んだら fail にする厳格の切替(例 環境変数)を足す。挙動の追加なので先に聞く |
| L2 | 低 | `tests/engine/test_env_and_sections_10f.py:309-312` | 「登録済みか」の assert を外したので、作者の機械が版上げ(numpy など)で未登録になっても落ちず、golden の比較は全部 A/A と警告に変わる。K26 (1) には合う | 作者の夜間は `-W error::tests.golden_env.GoldenUnregisteredWarning` で回すか、要約の警告の数を見る手順を書く |
| L3 | 低 | `tests/engine/test_calendar_sites.py:170` | 前は「`data/world/v2` という置き場がある」、今は「6 ファイルがそろう」。前より厳しい。どちらの機械でも結果はほぼ変わらない | 記録の「前の skipif が見ていたファイルをそのまま id にした」に例外として 1 行足す |
| L4 | 低 | 前の判定が cwd 相対だった約 25 ファイル(`Path("data/world/v2")` など) | 判定は根からの道筋になったが、本文は cwd 相対で読むまま。根以外を cwd にして回すと、前は飛んだ試験が今は回って落ちる。CI と通常の使い方(根で回す)では差が出ない | 記録に「根で回す前提」と 1 行書く(本文の道筋は変えない) |
| L5 | 低 | `tests/engine/test_calendar_10e_e3.py:165` | 足した印は `world_v2:w7_plan_spec.parquet`。落ちた assert は計画実行層(W17)の分なので、W7 があって W17 が無い機械では回って落ちる | `world_v2:w17_schedule.parquet` も並べる(任意) |
| L6 | 低 | `tests/engine/test_env_and_sections_10f.py:104-106` | 完全一致なので、葉と同じホスト名(例 `Windows`・`11`)は偽赤、長い値に埋め込まれた名(`名@ホスト` など)は捕まえない | 葉を `[^\w.-]` で区切った語との一致にする(`llvmlite==…` に `vm` は当たらず、`名@vm` は当たる) |
| L7 | 低 | `tests/conftest.py:83-98` | xdist の worker で `UsageError` を投げると INTERNALERROR(crashitem)になり、未登録の id の文言が読みにくい。止まりはする | 文言を `pytest.fail` の理由にする、または controller でも 1 回検査する(任意) |
| L8 | 低 | `tools/scan_secrets.py:15-22` | 親の直しに試験が無い。UTF-8 として壊れたファイルを cp932 で読むと、先行バイトの直後の ASCII 1 文字が 2 バイト文字に食われうる(秘密の型の先頭が隣接するときだけの、ごく狭い穴) | `tests/tools/` に 2 本足す: fixture は CLEAN・cp932 の中の秘密の型は HIT |

## 4. 親に確かめてほしいこと

1. 全体の試験(data あり・なし)は親が回す。本検収は一部(6 つの道筋)だけを回した。
2. push の後に `gh run list` で見る: ci-0 のスキャンが Linux でも CLEAN か/ci-1 で未登録の golden が警告だけで通るか/ci-1 の slow でない時間の門(P6 縮小 2 ms・P2 縮小 300 ms・艦隊 0.3 秒・描画 1 ms)が共有の機械の 2 並列で揺れて落ちないか。落ちたら、ci-1 にも記録だけの切替を使うかを決める(要件の外なので先に聞く)。
3. ci-2 は `schedule` も `workflow_dispatch` も既定の枝(main)のワークフローで動く=main に入るまで夜の段は回らない(実装役の記録 §8 のとおり)。
4. `execnet`(xdist の依存)は版を固定していない。固定するかは親の判断。
5. 実装役の記録は、手元の 1・3 を作業木の他の作業の変更が入った状態で回している(記録 §8)。本検収の W0 も同じく他の作業を含む。
