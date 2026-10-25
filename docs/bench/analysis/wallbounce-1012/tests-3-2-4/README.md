# 3-2-4 取り出したばかりの状態での試験(第333)

- 実装役 Opus 5.5。commit は親。枝 `build/spatial-d102-prep`・HEAD `adc2b93`。決定=回答 10-13b §1 の 1-4。仕分けと案=[triage D §2](../../../../reviews/triage-2026-10-13/D.md)。
- 変えたのは `tests/`・`.github/workflows/ci.yml`・`pyproject.toml`(dev の extras と markers だけ)・`.gitattributes`・本記録。`src/` は変えていない。`tools/` は親が後から `tools/scan_secrets.py` を 1 か所直した(§10)。試験の名・assert の中身・golden の値は変えていない(飛ばし方と、環境に依存する 4 件だけ)。
- 数は実測。手元=Windows 11・Python 3.12.10・scipy なし。

## 0. 結論

- **data の無い写し(W0=HEAD の追跡ファイル+本変更・`data/` なし)**で `-m "not gpu and not slow" -n 2 --dist loadfile`: **3,766 passed・0 failed・172 skipped**(`requires_data` 171・git の commit が無い 1)・459 秒。前は同じ条件で 313 failed・68 errors(triage D §2-1 の回 2)。
- **手元(data あり)** で同じ選び方・2 並列: **3,941 passed・1 xfailed・0 failed・0 skipped**(5 回に分けて回した・壁時計の和 1,376 秒)。data のある機械で回る試験の集合は前と同じ(印の id は前の `skipif` が見ていたファイルをそのまま使った=§3)。
- 直列(xdist なし)でも同じ結果: §7 の 3。
- `lint-imports`: 5 kept・0 broken(本体・W0 とも)。
- 子プロセスの import 先の穴を塞いだ: W0 で conftest を通さない子は本体の `src` を読み、通した子は W0 の `src` を読む(§5)。
- **秘密スキャンの偽陽性**: 祝日の CSV(cp932)は `tools/scan_secrets.py`(UTF-8 で読む)で 73 件 HIT した(全部 U+04C2=文字化け。cp932 で読めば 0 件)。**〔親の直し(§10)〕** スキャンが UTF-8 で読めないファイルを cp932 でも読むようにしたので 0 件になり、CI でも fixture をスキャンの対象に戻した(md5 の固定は残す=§6)。

## 1. 変えたファイル

| 種類 | ファイル |
|---|---|
| 新規 | `tests/_data_ids.py`(id の登録表)・`tests/_time_gates.py`(時間の門の切替)・`tests/test_child_imports_this_tree.py`・`tests/test_fixture_holiday_csv.py`・`tests/fixtures/README.md`・`tests/fixtures/calendar/syukujitsu.csv`・本記録 |
| 書き直し | `tests/conftest.py`(祝日の複製・`PYTHONPATH`・印の判定・要約)・`.github/workflows/ci.yml`(3 段) |
| 追記 | `pyproject.toml`(`pytest-xdist==3.8.0`・印 `requires_data`)・`.gitattributes`(`tests/fixtures/calendar/*.csv binary`) |
| 印の置き換え | `tests/` の 58 ファイル(下の conftest 6 本を含む・ルートの conftest は別)。一覧は `git diff --stat -- tests` |
| 環境依存の直し | `tests/engine/test_env_and_sections_10f.py`・`tests/c7/test_prereg_v13.py`・時間の門 8 ファイル(§4) |

手元の venv に `pytest-xdist==3.8.0` を入れた(依存で `execnet 2.1.2` も入った。pyproject には書いていない)。

## 2. 祝日の fixture

- `data/calendar/syukujitsu.csv`(21,538 B・md5 `733fabb6b488794a0cd3d94df4b1f24a`・cp932・CRLF)を `cp` で `tests/fixtures/calendar/` へ。md5 は同じ。`.gitattributes` に `binary` を足し、`git hash-object --path=…` が変換なしの値(`76e45cd7…`)と一致することを確かめた(足す前の `text=auto eol=lf` だと別の値になる)。
- 出典と規約は `tests/fixtures/README.md`(内閣府「国民の祝日について」・公共データ利用規約 第1.0版・取得日 2026-10-03・手を加えていない)。ライセンス台帳の行は親が書く。
- ルートの conftest が、import の時に `data/calendar/syukujitsu.csv` が無ければ fixture を複製する(一時名に写して `os.replace`・既にあれば触らない・標準エラーに 1 行)。エンジンの既定の道筋は変えない。`data/` は gitignore のまま。
- `tests/test_fixture_holiday_csv.py`(**頼まれていない追加**): fixture の大きさ・md5・CRLF を確かめる 1 本。中身を md5 で固定していることを試験でも持つ(親が残した)。

## 3. 印 `requires_data`

仕組み:

- `@pytest.mark.requires_data("<id>", ...)`。id を並べたら全部そろったときだけ回す。`pyproject.toml` の markers に登録。
- `tests/_data_ids.py`: 置き場の表(`world_v2`・`osm`・`estat`・`plateau_2025`・`realworld`・`plateau`・`odpt`・`persona_pool`・`tape`・`calendar`)と、置き場では決まらない id の判定(`world_v2`=世界資産を読み込める 6 ファイル=`assets_available` と同じ・`timetables`・`w17_promoted`・`calendar`)。`<置き場>:<相対パス>` はそのファイルの有無。`id_of(path)`/`ids_of(...)` で道筋から id を作る(src の定数から組む道筋はこれで写した)。
- ルートの conftest の `pytest_collection_modifyitems` が判定し、無ければ一律の理由 `requires_data: <id> が無い` で飛ばす(並べた id のうち最初に無いもの)。未登録の id は `UsageError`(書き間違いで黙って回らない形にしない)。
- 関数の途中でしか決まらない所(前に data の要らない assert がある・fixture の中・読んだ資産の中身で決まる)は `D.skip_unless("<id>", have=...)`(理由は同じ文言)。5 か所。
- `pytest_terminal_summary` が id ごとの飛ばした数の表を出す(合否にしない)。`GITHUB_STEP_SUMMARY` があれば同じ表を Markdown で追記する(xdist の worker では書かない)。理由の文言から数えるので印と `skip_unless` の両方が入る。

置き換えの表(前の理由の文言 25 通り・82 か所 → id。`*` は `skip_unless`):

| 前の理由 | か所 | id |
|---|---:|---|
| 実世界資産が無い | 15 | `world_v2:w17_schedule.parquet` 10(うち `*` 2)・`world_v2:w6_poi.parquet` 2・`world_v2:w8_t1_cell.parquet` 2・`world_v2:w12_timetables.parquet` 1 |
| 実世界資産 data/world/v2 が無い | 12 | `world_v2:w2_cells.parquet` 5・`world_v2:w12_timetables.parquet` 3・`world_v2:w12_generation_weights.parquet`・`world_v2:w17_schedule.parquet`・`world_v2:build_manifest.json`・`PerceptionAssets.REQUIRED_FILES` の 7 ファイル 各 1(検収で訂正) |
| data/world/v2 が無い | 9 | `world_v2:w8_t1_cell.parquet` 6・`world_v2:w7_plan_spec.parquet` 2・`world_v2` 1 |
| data/ absent (CI) | 8 | 前の条件のファイルをそのまま並べた(`osm:shibuya_osm_wide_v8.json`・`plateau:terrain.npz`・`realworld:road_census_r3/kasyo13.csv`・`osm:road_names_overpass_20260928.json`・`estat:r2ka13113/…`・`persona_pool:meta.json`・`odpt`・`world_v2:<段の出力>`) |
| W 資産(data/world/v2)が無い | 7 | `world_v2`(うち `*` 1) |
| PLATEAU 生 GML が無い | 4 | `plateau_2025:13113_shibuya-ku_pref_2025_citygml_1_op/udx/tran` |
| 世界資産が無い環境 | 3 | `world_v2:w13_weather_days.parquet`・`world_v2:w7_plan_spec.parquet`・`world_v2:w13_weather_hourly.parquet` |
| data/world/v2/w16_population.parquet が無い(先に W16 を回す) | 3 | `world_v2:w16_population.parquet` |
| C9c-1 資産が無い | 3 | `world_v2:c9c_walkable_area.parquet` |
| 世界資産(gitignore 下)が無い環境 | 2 | `world_v2`+`world_v2:w10_noise_stage_day.npy`・`world_v2` |
| data/world/v2/w16_population.parquet が無い | 2 | `world_v2:w16_population.parquet` |
| 実資産(w16_population.parquet / persona_pool_v2)が無い | 1 | `world_v2:w16_population.parquet`+`persona_pool:meta.json` |
| 実資産(W17)が無い・実資産が無い・W17 が無い | 3 | `world_v2:w17_schedule.parquet` |
| W16 が無い | 1 | `world_v2:w16_population.parquet` |
| W 資産(data/world/v2)が無い=会話の起きる世界が無い | 1(補助の関数・呼び 3) | `world_v2` |
| data/world/v2 が無い(C1 の成果物) | 1 | `world_v2` |
| 祝日 CSV が無い環境・本物の祝日 CSV(gitignore 下)が無い環境 | 2 | `calendar` |
| 時刻表の資産が無い | 1 | `timetables`(`*`・`have=pa.has_timetable`) |
| 実 W17 が昇格版ではない | 1 | `w17_promoted`(`*`・`have=` md5 の頭 `3113e9ba7abb`) |
| e-Stat 小地域境界が無い | 1 | `estat:r2ka13113/r2ka13113.shp` |
| PLATEAU npz が無い | 1 | `plateau:tran_lod3.npz` |
| AB7 seed 1 のテープが無い | 1 | `tape:c8_ab7_s1/AB7-OPEN-INTENT__open/calls.parquet` |
| (印の付け忘れ) | 1 | `test_calendar_10e_e3.py::test_e3_two_days_…` に `@needs_world`(=`world_v2:w7_plan_spec.parquet`) |

- 印の付いた試験は 191 本(slow を含む収集)。手元ではどの id もある(収集して判定した)。
- 関数の頭で飛ばしていた所(補助の `_real_world_or_skip` を含む)は印に替え、補助の関数は消した。前に data の要らない assert がある所(`test_relations_tenure` の 1 本・`test_build_run_keep_stage` の 1 本)と fixture の中(`test_version_bump_10e` の `v4_tape`)は `skip_unless` にして、data なしでも前の assert を回す形を保った。
- `test_state_format_10f.py::test_u1_…` は `data/calendar/syukujitsu.csv` を直接開くだけ(ほかの data は読まない)=fixture の複製で解決(印は付けない)。

data ではない理由で今のまま残したもの: git が無い(2)・旧 commit が無い(1)・環境変数 `SHIBUYA_C6_FLEET_COUNTERS`(1)・合成の世界に従業者が居ない(1)・実 W17 の md5 の golden の行が無い(7=data の有無ではなく golden の行の有無)・辞書の版(1)・`docs/bench/anchors` の台帳(1=追跡ファイル)・`importorskip`(4)。

## 4. 環境依存の 4 件(試験だけ)

| # | 試験 | 前 | 直し方 |
|---|---|---|---|
| 1 | `test_env_and_sections_10f.py::test_golden_tables_are_keyed_by_platform_and_values_unchanged` | `assert GE.platform_id() in GE.REGISTERED`=未登録の環境(CI)で落ちた | K26 (1) に合わせ、未登録なら `GE.warn_unregistered(...)` を出して `pytest.skip` にした → **〔親の直し(§10)〕表の鍵と値の検査は環境に依らないので、未登録でも警告だけ出して検査を続ける**(CI でも値の改変を捕まえる)。登録済みなら前の検査のまま |
| 2 | 同 `test_environment_fields_shape_and_ids` のホスト名 | `node not in json.dumps(...)`=部分一致。CI のホスト名「vm」が「llvmlite==…」に当たった | 値の葉(文字列)を再帰で集め、`node` と等しい葉が無いことを見る(`deps` の各要素も葉)。手元で「vm」は `json.dumps` には当たり葉には当たらないことを確かめた |
| 3 | `tests/c7/test_prereg_v13.py::test_e_family95_half_width_matches_t995_df2` | 表の 9.925 と rel=1e-9(と既定の rel)で比べた=scipy があると落ちる | 期待値を `v13.t_quantile_995(2)`(道具が返す値)から組み、別に `approx(9.925, rel=1e-3)` を見る。scipy は入れず、`t.ppf` だけを持つ偽の `scipy`(9.924843…)を `PYTHONPATH` に置いて通ることを確かめた |
| 4 | 時間の門(slow) | 共有の機械では速さが揺れる | `SHIBUYA_TIME_GATES=record` のとき落とさず `TimeGateWarning`+print で記録だけ(`tests/_time_gates.py` の `TG.check`)。既定は前のまま落ちる。条件・上限・文言は変えない |

時間の門を `TG.check` に通した slow の試験: P6(`test_change_detect_p6`)・P2 40 万体(`test_geometry_c9`)・W2 と P2 5 千体 2 本(`test_mock_day_w2`)・W2 台帳あり(`test_ledger_wiring`)・W2 実世界 2 本(`test_processes_run`)・P3(`test_scheduler_p3`)・状態の書き読み 5 秒(`test_state_format_10f::test_size_and_time_5000`)・W16 5,000 体 600 秒(`test_pop_pipeline`)。slow でない時間の門(P6・P2 の縮小版・描画 1 ms・艦隊 0.3 秒・構築の通し)は変えていない。

## 5. 子プロセスの import 先

- ルートの conftest が import の時に `PYTHONPATH` の先頭へ `<rootdir>/src` を足す(既に先頭なら足さない)。子を起こす試験 6 ファイルはどれも `os.environ` を引き継ぐので、その木の `src` を読む。`test_state_format_10f.py` の旧 commit の子は自分で `PYTHONPATH` を上書きする(変えていない)。
- `tests/test_child_imports_this_tree.py`: 本体のプロセスと、木の外を cwd にした子の両方で `shibuya.__file__` が `<rootdir>/src/shibuya` であること。
- W0 で確かめた: conftest を通さない子の `shibuya.__file__` は本体の作業コピーの `src`(editable の `.pth`)、通した子は W0 の `src`。試験も W0 で 2 passed。

## 6. CI の 3 段(`.github/workflows/ci.yml`)

| 段 | いつ | 中身 | 上限 |
|---|---|---|---|
| ci-0 | push・PR | 祝日の fixture の md5(`md5sum -c`)・秘密スキャン(追跡ファイルから fixture の CSV を除く)・`lint-imports`・`data/` が追跡されていない | 15 分 |
| ci-1 | push・PR(ci-0 と並列) | `pip install -e ".[dev]"` → `pytest -q -m "not gpu and not slow" -n 2 --dist loadfile`(`fetch-depth: 0`=旧 commit の試験が回る)。飛ばした数の表はジョブの要約へ | 45 分 |
| ci-2 | 毎晩 UTC 18 時(JST 3 時)・手動 | `SHIBUYA_TIME_GATES=record` で `pytest -q -m "slow and not gpu" -n 2 --dist loadfile` | 120 分 |
| 本体の夜間 | 手元(作者の機械) | data のある全体・byte-check 19・golden・性能の門 | CI に入れない |

- `tools/commit_check.py` はステージ(`git diff --cached`)だけを見る作りで、追跡ファイル全体に道筋の検査をかける呼び方が無い=CI には足していない。
- 秘密スキャンと fixture: 旧は UTF-8(errors=replace)で読むので cp932 のバイト列が U+04C2 に化けて 73 件当たった。〔親の直し(§10)〕UTF-8 で読めないファイルは cp932 を試す形にしたので 0 件=ci-0 は fixture もスキャンする。中身は md5 で固定(ci-0 の 1 段目と `test_fixture_holiday_csv.py`)。

## 7. 確かめ方の結果

1. **手元(data あり)・`-m "not gpu and not slow" -n 2 --dist loadfile`**(`PYTHONIOENCODING=utf-8`・`-p no:cacheprovider -o addopts=""`): 3,941 passed・1 xfailed・0 failed・0 skipped。1 コマンドの時間の上限で 5 回に分けた: build_* 156 秒(776 passed・1 xfailed)・c6〜c8 ほかとトップ 93 秒(1,601)・engine の processes/systems/test_a〜l 154 秒(784)・engine の test_m〜z 962 秒(763)・engine の test_10a 11 秒(17)。試験の時間の和 2,564 秒(重いのは `test_resume_10d` 495 秒・`test_state_checks_10f` 291 秒・`test_presence_executor` 218 秒)。要約の表は「data が無くて飛ばした試験 0 件」。
2. **W0(data の無い写し)**・同じ選び方: 3,766 passed・0 failed・172 skipped・459 秒。祝日の表は conftest が fixture から複製した(md5 同じ)。飛ばした数の表(`GITHUB_STEP_SUMMARY` に置いた一時のファイルにも同じ表が書かれた):

   | id | 数 |
   |---|---:|
   | `world_v2:w17_schedule.parquet` | 47 |
   | `osm:shibuya_osm_wide_v8.json` | 33 |
   | `world_v2` | 15 |
   | `world_v2:w2_cells.parquet` | 15 |
   | `estat:r2ka13113/r2ka13113.shp` | 11 |
   | `osm:road_names_overpass_20260928.json` | 9 |
   | `world_v2:w8_t1_cell.parquet` | 8 |
   | `world_v2:w12_generation_weights.parquet`・`world_v2:w16_population.parquet` | 各 5 |
   | `world_v2:w13_weather_days.parquet`・`world_v2:w7_plan_spec.parquet` | 各 4 |
   | `world_v2:w12_timetables.parquet`・`world_v2:w13_weather_hourly.parquet` | 各 3 |
   | `tape:…/calls.parquet`・`world_v2:c9c_walkable_area.parquet`・`world_v2:w11_station_exits.parquet`・`world_v2:w6_poi.parquet` | 各 2 |
   | `world_v2:build_manifest.json` | 1 |
   | data 以外(旧 commit `129da80` が無い=W0 は git の外) | 1 |

   W0 の slow(ci-2 と同じ・`SHIBUYA_TIME_GATES=record`・2 並列): 12 passed・23 skipped(`requires_data` 22・環境変数 1)・83 秒。超えた時間の門は無かった。
3. **直列(xdist なし)・同じ選び方**:
   - 手元(data あり・ルート): 3,960 passed・1 xfailed・0 failed・0 skipped・3,054 秒(1 回で通し)。1 より 19 本多いのは、回している間に作業木の他の作業が足した試験ファイル 1 本(`tests/tools/test_realworld_fetch_odpt.py`・19 本)の分。共通の 3,942 本は 1 と同じ結果(junit で突き合わせた)。
   - W0(data なし・`data/` を消してから): 3,766 passed・0 failed・172 skipped・1,179 秒。飛ばした数の表は 2 と同じ(fixture の複製もやり直した)。2 並列(459 秒)と結果が同じ=ci-1 が xdist をやめても通る。
4. `lint-imports`: 本体・W0(`PYTHONPATH=src`)とも 5 kept・0 broken。

W0 の作り方: `git archive HEAD` を一時の置き場に展開し、本変更のファイル(74 項目・ディレクトリ 1 つを含む・本記録を除く)を上書きした(`data/` と `.venv` は無し・本体の venv の python で回した)。作業木の他の作業の未 commit の変更は W0 に入っていない。終わった後に消した。

## 8. 限界・判断待ち

- **xdist**: 2 並列で落ちた試験は無かった=`xdist_group` も `serial` の印も使っていない。なお `xdist_group` は `--dist loadgroup` のときだけ効く(`loadfile` では無視される)。
- **秘密スキャン(決着=§10)**: 案 (b) の「cp932 でも読む」を親が入れた。手元の commit の前のスキャンも 0 件。
- **golden の表の試験(判断待ち)**: 指示どおり未登録の環境では 1 本ごと飛ばした。表の鍵と値の検査は環境に依らないので、警告だけ出して続ける形もある(CI でも値の改変を捕まえられる)。
- ホスト名の検査は完全一致にしたので、長いホスト名が別の文字列の一部に入る形(例「名前@ホスト」)は捕まえない。
- GitHub の上ではまだ回していない(push は親)。Linux での振る舞い(未登録の環境の golden・ホスト名・2 vCPU で 2 並列の時の slow でない時間の門)は未確認。push の後に `gh run list` で見る。
- ci-2 の `schedule` は既定の枝(main)のワークフローで回る。この ci.yml が main に入るまで夜の段は動かない。`workflow_dispatch` も同じ。
- 手元の 1・3 は作業木の他の作業の未 commit の変更(`src/shibuya/build/audit/w19_freeze.py`・`tools/realworld_fetch/`・新しい試験 2 本)を含んだ状態で回した。W0 は HEAD+本変更だけ。

## 10. 親の直しと検収(第333・2026-10-14)

- **親の直し 2 点**(実装役の報告の「判断してほしいこと」1・2): (1) `tools/scan_secrets.py`=UTF-8 で読めないファイルは cp932 を試し、それも駄目なら UTF-8 の置換で読む(祝日の fixture の偽陽性 73 件 → 0 件。ci-0 の除外を外した)。試験 `tests/tools/test_scan_secrets_cp932.py`(fixture が CLEAN)。(2) golden の表の試験=未登録の環境でも表の鍵と値の検査(環境に依らない)を続け、登録の有無は警告だけ。
- **独立検収**([review.md](review.md)・実装を見ていない検収役): **条件つき受入** → 条件 M1(本記録の古い記述 6 行)は本節で解消。低 8 件のうち L5(`test_calendar_10e_e3.py:165` の印に `world_v2:w17_schedule.parquet` を並べる)と L8(スキャンの試験)は親が入れた。残り(L1 置き場の後ろの相対パスは検査しない・L2 登録済みの機械が未登録になっても落ちない=夜間を `-W error::tests.golden_env.GoldenUnregisteredWarning` で・L3/L4 判定が前より厳しく根からの道筋に・L6 ホスト名は葉の完全一致・L7 未登録の id は xdist で INTERNALERROR の文言)は限界として記録(直すなら先に聞く案件=挙動の追加)。
- **親の検収**: data あり(4 並列)の全体=§11。data 無しの写し(追跡+未 commit の 1,891 本・`data/` なし・4 並列)=**3,792 passed・172 skipped(requires_data 18 種 171 件+旧 commit 無し 1 件)・0 failed・4 分 54 秒**。`execnet` は pytest-xdist の依存のまま版を固定しない(試験の結果に効かない)。
