# 2-3b 鉄道の実ダイヤ 検収の記録(独立の検収役)

> 検収役(Opus 5.5)。実装は見ていない。作業木 `2-3b/timetables`(土台 `f2405e3`・未 commit)を読むだけで検収した。書いたのは本書だけ。W12 の組み直し・資産の作り直し・byte-check の出力は作業用の置き場(git の外)に置き、終わりに消した。試験の実行で作業木に `__pycache__` などの gitignore 下のファイルができた以外は書いていない。
> 封印: `kddi_la`・`shibuya_jinryu`・`boundary_counts.json`・`realworld_live/odpt_rt/`・PT の検証側の表・`presence_anchors_v0.json` は、検収役が自分で開いていない。ただし、発注の手順(資産の作り直し=W19 を含む・`tests/build_audit` の全段の構築)を回すと、W19 の封印の処理が holdout の層の sha256 を取る(中身は解かない=既存の封印の方式 S)。それ以外に封印の層に触れる道は無い(W12 の run を open の監査フックで見て確かめた=§2)。京王のチャレンジ枠の生の行は本書に写していない(本数と版だけ)。`tests/c7` は回していない。

## 判定

**条件つき受入**。条件は H1(つなぎの台帳の試験が 11 件落ちる=CI-1 が赤になる)を commit の前に直すこと。実ダイヤの中身は、本数・時刻の多重集合・版・資産の再現・動いた量のすべてで申告と一致した。

## 1〜9 の確かめ

| # | 項目 | 判定 | 根拠 |
|---|---|---|---|
| 1 | エンジン不変 | ✓ | `git diff --stat -- src/shibuya/engine` は空。差は `src/shibuya/build/{audit/w19_freeze.py, field/w12_external_nodes.py}` と新しい `field/w12_real_timetables.py`、試験 7 本(新 1・直し 5・`_data_ids.py`)、記録 1 本。作業木の根に実装役の作業用の置き場 `_bc/`(未追跡)がある=取り込むときに載せない |
| 2 | 本数の独立の数え直し | ✓ | 下の §2。計器と読み口のコードを使わず CSV と JSON から数えた。線 × 暦の 12 マスが記録・資産と全部一致。線 × 向き × 暦の 20 組で時刻の多重集合が資産と一致 |
| 3 | 方面の写像 | ✓(注あり) | §3。山手線の「内回り=上り」は推測のまま(検収役も確かめる手段を持たない)。エンジンへの影響は同じ時刻の便の並びだけ |
| 4 | 切替口 False | ✓ | §4。`w12_timetables.parquet` の sha256 が 1.1.0 と一致(`c548b2bb7ecd5c21`)。ヘッダは stage_version だけ違う(L2) |
| 5 | 資産の再現・版の表 | ✓ | §5。build_hash `591c854352dcff06` を 2 回再現。107 ファイルが stage の資産とバイト一致。版の表は記録 §7 と合う |
| 6 | W19 の層の元・凍結の表 | ✓ | §6。`layer_independence()` の出力は土台と作業木でバイト一致。凍結の表の増分 26 件は W12 が読むファイルと完全に一致 |
| 7 | 動いた量(w6_v3_default) | ✓ | §7。final `4bcca9f0216362bb`・呼数 65,400。`frozen_sources` で動いたのは `process:w12_timetables.parquet` だけ(HEAD の資産の sha256 と独立に照合) |
| 8 | 試験 | ✗ | §8。発注の範囲は 240 passed・1 xfailed。ただし範囲の外の `tests/engine/bridging` が 11 件落ちる(土台では 49 passed)=H1 |
| 9 | 記録 | ✓ | §9。絶対パス・ホスト名・個人名なし。`HH:MM` の形の文字列 0 件。改行 LF。秘密の検査 CLEAN。ライセンス台帳の案の本数は本数の表と整合 |

## 2. 本数の独立の数え直し

検収役の写像の表(timetables の記録を読んで独立に書いた)で `_extracted/*_final.csv`(渋谷発の 11 表)・`odpt_challenge/` の渋谷発の 1 表・`odpt_static/2026-10-13/traintimetable_TokyoMetro.json.gz`(銀座線)を Python の csv・gzip・json だけで読んで数えた。

| 線 | 平日(検収役/記録/資産) | 土休(検収役/記録/資産) |
|---|---|---|
| 山手線 | 513 / 513 / 513 | 507 / 507 / 507 |
| 埼京線(湘南新宿・相鉄線直通を含む・臨時を除く) | 453 / 453 / 453 | 410 / 410 / 410 |
| 東横線 | 607 / 607 / 607 | 559 / 559 / 559 |
| 田園都市線 | 573 / 573 / 573 | 425 / 425 / 425 |
| 井の頭線 | 305 / 305 / 305 | 261 / 261 / 261 |
| 銀座線 | 360 / 360 / 360 | 305 / 305 / 305 |

- 時刻の多重集合: 線 × 向き × 暦の 20 組(半蔵門線・副都心線を除く)で、検収役の数え直しと資産 `v2_stage_2-3b/w12_timetables.parquet` が全部一致。資産の `departure_min` は全行で `departure` と運行日の切れ目(4 時)から計算した値に一致。資産の行は 6,273(`source` ごと: real 995・JR 1,883・東急 2,164・京王 566・銀座線 665)。
- 表ごとの生の本数(臨時を除く前)も記録の golden の `table_counts` と一致(例: 湘南新宿ライン 北行 96/91・南行 95/93)。
- **臨時の 4 本**: 種別に「踊り子」を含む行は JR の表で 4 行だけで、すべて土休(北行 特急(踊り子) 1・南行 特急(踊り子) 2・特急(サフィール踊り子) 1)。4 行とも `JR_注記.final.csv` の同じ (表, 暦, 時, 分) に ◆ がある。平日には無い。
- **重複**: 20 組とも 0(同じ線・向き・暦・時刻)。向きを無視すると同じ分の便は多い(例 山手線 平日 110)が、上下の別の便で重複ではない。
- **銀座線**: ODPT の銀座線の列車は 728/618 本。最初の停車が渋谷の列車は 360/305 本で、`odpt:originStation` が渋谷だけの列車の数と同じ。渋谷を途中で発車する列車は 0。665 本とも `dct:issued` 2026-09-19・`odpt:railDirection` TokyoMetro.Asakusa。ユーザーの G01(9 月改正)の読み取りと時刻の多重集合で平日・土休とも一致(G01 は試験でだけ読まれ、構築の入力ではない)。
- **使わない表が読まれないこと**: 読み口は白い一覧 `USER_TABLES`(12 表)と `JR_注記.final.csv` だけをパスで組み、glob を使わない。W12 の `run()`(実ダイヤ)を open の監査フックの下で回し、開いたファイルを控えた: 大都市交通センサス 3 本・ODPT 乗降人員・PT core 1 本・ODPT の駅の時刻表 2 本(半蔵門線・副都心線)・実ダイヤの入力 26 本・上流の資産 3 本と出力だけ。到着・神泉・原宿・明治神宮前・代々木八幡・成田エクスプレス・G01・封印の層・`odpt_rt` は 0 件。

## 3. 方面の写像

- docstring の表(`w12_real_timetables.py` 冒頭)は記録と合う: 埼京線 大宮方面=下り・大崎方面=上り(頁の題名)/相鉄線方面の表は題名が下りだが、ODPT の埼京線 南行=大崎方面+相鉄線方面で全一致(extraction-jr.md §6)なので南行=上り/湘南新宿ライン 北行=下り・南行=上り/東急の上り=東急が出す副都心線・半蔵門線の標準時刻表(README §2-1 の題名「TY01_渋谷(上り)」「DT01_渋谷(上り)」・ODPT と 1 対 1=extraction-tokyu-metro.md §5)。
- 井の頭線は「下り」。keio-odpt-challenge.md §6 の 5 は `Outbound` に写す案だったが、向きの値の集まり {上り, 下り, TokyoMetro.*} を保つ(エンジンの `didx` を振り直さない)ために下りにした、と記録 §3 に宣言がある。妥当。
- 山手線の「内回り=上り・外回り=下り」は線路名称の品川起点による**推測・未リサーチ**のまま。ODPT は山手線の向きを内回り/外回りで持つので ODPT では決まらない。
- W12 の方面ノードとの矛盾は無い: 鉄道の 8 ノードの `direction_label` は方面の束(例 `ext_rail_jr_yamanote`=「新宿・池袋/恵比寿・品川方面」・`ext_rail_jr_saikyo_shonan`=「新宿・大宮/大崎・横浜方面」)で上り/下りを持たない。エンジンは向きを `engine/processes/rail.py` の `np.lexsort((direction, line, dep))`(同じ時刻・同じ線の便の並び)にだけ使い、方面ノードは `lines` の先頭の線で便を引く(`world/assets.py` の E2)。向きの値の集まりが同じなので `didx` も同じ。
- 注: `rail.py` の docstring は「山手線の 134%(外回り)/139%(内回り)は direction に写せない」と書く。将来この推測の写像で向き別の混雑率を当てると、推測が結果を動かす。expedient の宣言を残すこと。

## 4. 切替口 False の同一性

上流の資産 3 本(HEAD の `w11_station_exits`・`w1_nodes`・`w1_edges`)を作業用の置き場に写し、作業木の `src` で `USE_REAL_TIMETABLES=False` にして W12 だけを組んだ。

- `w12_timetables.parquet` `c548b2bb7ecd5c21`=HEAD の 1.1.0 と sha256 一致。`w12_external_nodes.parquet` `031fe09e9a566eff`・`w12_generation_weights.parquet` `eb85f8acf5a20809` も一致。版の表は作られない。
- ヘッダの input_hash・param_hash・params・outputs・gates・catalog_classes・expedients・notes は 1.1.0 と全部一致。違うのは `stage_version`(1.2.0 と 1.1.0)だけで、そのためヘッダのファイルのバイトは一致しない(L2)。

## 5. 資産の再現と版の表

- W12 だけ(実ダイヤ): `w12_timetables.parquet` `7ef7ab9038348e59`・`w12_timetable_versions.json` `4ee484eb75037467`・W12 のヘッダが stage の資産とバイト一致。全ゲート PASS(新しい 6 つ: 残る等間隔の線 0・両方の暦あり・土休 > 平日 0・臨時 4・重複 0・銀座線の渋谷発 665)。
- 記録 §8 の手順(HEAD の資産の写し+`--stage W12 W18 W19 W20`・`--keep-stage` 17 段)を作業用の置き場で 2 回: 2 回とも rc 0・build_hash `591c854352dcff06`=stage の資産。全 107 ファイルが stage の資産とバイト一致。HEAD の資産から動いたファイルは記録 §8 の 4 の一覧と同じ 11 本(W12・W18・W19・W20 のヘッダ・受入パック 2 本・`build_manifest.json`・新しい版の表・時刻表・`w19_freeze.json`・`wc_index.json`)。
- 版の表: 銀座線 `after`(dct:issued 2026-09-19 × 665・dc:date 2026-09-24)・山手線と埼京線 `before_inferred`(表の版の文言「JR時刻表2026年10月号に基づく(改正日の記載なし)」)・東横線と田園都市線 `before`(2026-03-14)・井の頭線 `before_inferred`(表の版 2026-07-03(チャレンジ枠)・宣言の文に dct:issued 2025-03-15/17)・半蔵門線と副都心線 `before`(ODPT の駅の時刻表 dct:issued 2026-03-14・2026-07-07 取得)。記録 §5・timetables/README §7・keio-odpt-challenge.md §5 と一致。入力の行 28(実ダイヤ 26+駅の時刻表 2)。
- 版の表に発車の時刻は無い: `HH:MM` の形の文字列は 14 件あるが、全部 ISO の日時(dc:date・取得の時刻)の一部。

## 6. W19 の層の元と凍結の表

- `layer_independence()` を土台 `f2405e3` の `src`(git archive の写し)と作業木の `src` で回し、出力の JSON がバイト一致(3 層とも「照合用(独立でない)」・理由も同じ)。足した 3 つの鍵は holdout の層の名にも元にも当たらないので、判定に入らない。
- 凍結の表 `data_assets` 66 → 91。足した 26 件は `w12_real_timetables.all_input_rel_paths()` と完全に一致(ユーザー提供の読み取り 23・チャレンジ枠 2・静的データ版 1 の 1)。外したのは `odpt/station_timetable_metro_ginza.json` の 1 件。共通の 65 件の sha256 は不変。holdout の 3 層の member_hash は HEAD の資産と同じ(層に足されたのは第333 の欄 `source_family`・`independent`・`mark` だけ)。
- 注(L4): `SOURCE_FAMILIES` は holdout の層の元の表だったが、構築の入力の層の鍵も同じ表に入った。今は判定に効かないが、`odpt_static`(時刻表=計画)と `odpt_rt`(在線=実績)を別の元とするのは宣言で、将来 `odpt_rt` を holdout にするときは「同じ元」と見るかを親が決める。

## 7. 動いた量(w6_v3_default の再現)

`byte_check_10e.py side --world data/world/v2_stage_2-3b --only w6_v3_default`(作業木の `src`=`src_is_worktree` True・5,000 体・seed 1・1 日)。

- final `4bcca9f0216362bb`・呼数 65,400。比べる 25 欄すべてが実装役の後の side と一致(blocks 8,157・行動の延べ 296,016・気づき 302・食事 4,400・出動の平均の遅れ 10.8 分)。HEAD の側 `5f7ae9ff24005314`/65,597 は 2-0 の最初の記録と同じ値。
- `frozen_sources`: 17 行のうち HEAD の資産のファイルの sha256 と違うのは `process:w12_timetables.parquet` だけ(15 行をファイルの sha256 で照合・残り 2 行は騒音の段のセルの digest で実装役の HEAD の side と同じ)。

## 8. 試験

- 発注の範囲(作業木・`tests/build_field tests/build_audit tests/engine/time`・`-n 2 --dist loadfile -m "not slow"`): **240 passed・1 xfailed(4 分 38 秒)**。新しい試験 19 件を含む。
- data の無い写し(`src`・`tests`・`pyproject.toml`・記録だけ)で直した 6 本+新しい 1 本: 33 passed・28 skipped。要約に `user_timetables` 2 件・`odpt_static` 1 件が出る=新しい id が効く。
- 直した 5 本の中身は「新しい既定で落ちる所の固定」だけ: `test_w12_pm_peak_switch`=切替口 False で回す 2 か所・`test_field_pipeline`=`source` の集まりの更新と「残る線 0・土休 ≦ 平日」の検査への置き換え・data の印・`test_audit_pipeline`/`test_vis_pipeline`=data の印だけ。
- `test_audit_units` の「`realworld_live/` の下は odpt_static だけ載る」は封印を弱めていない: 旧の「`realworld_live/` の下は 1 つも載らない」を、`realworld_live/` の下の集合が静的データ版 1 の 1 ファイルと**等しい**、に替えた。`odpt_rt` の道筋が載ればこの等式で落ちる。ただし試験は `odpt_rt` のファイルを置いていない(負の対照が無い)・docstring が古い(L1)。
- **範囲の外で落ちる試験(H1)**: `tests/engine/bridging` が **11 failed・38 passed**。土台 `f2405e3` の写しでは 49 passed。
- 範囲の外の隣の試験(`tests/c8/test_sensitivity_ledger.py`・`tests/engine/processes/test_rail.py`・`tests/test_world_catalog_sha.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/systems/test_systems_table.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/tools`・`tests/test_build_run_keep_stage.py`・`tests/build_vis`・`tests/build_pop`・`tests/build_sched`・`-n 2 -m "not slow"`): **523 passed(8 分 52 秒)**。今の `data/world/v2`(1.1.0)を読む試験は 2-4 の差し替えまで動かない(実装役の §12 の 5 のとおり)。

## 9. 記録

- `tt23b/README.md` に絶対パス・ホスト名・個人名なし。`HH:MM` の形の文字列 0 件(時刻を写していない)。改行は LF。`tools/scan_secrets.py`(変えた 11 本)CLEAN。
- ライセンス台帳の行の案(§12 の 7)の本数: 京王 566=305+261・JR 1,883=山手線 1,020+埼京線 863・東急 2,164=東横線 1,166+田園都市線 998・銀座線 665=360+305。本数の表(§4)・資産の `source` ごとの数と一致。

## 欠陥(重さ順)

### 高

**H1 つなぎの台帳の試験が 11 件落ちる(CI-1 が赤になる)** — `src/shibuya/build/field/w12_external_nodes.py` 782〜808 行と 823 行。
- 原因: 時刻表の expedient を局所のリスト `timetable_expedients` に移し、`StageResult(expedients=[..., *timetable_expedients])` で渡した。つなぎの台帳の走査器(`engine/bridging/scan.py` の形 B)は `expedients=[...]` の要素を 1 つずつ数えるが、星付きの要素は中身が見えず `*timetable_expedients` という 1 件の宣言(`#expedients:a75988f5`)になる。旧の 5 行(台帳の W12#4〜#8=`ffb7db3f`・`bdc23d38`・`dc17c013`・`d61ba9ea`・`669ec214`)は局所のリストに移って見えなくなり、台帳の行が孤児になった。実ダイヤの道の新しい expedient 8 行も走査器から見えない=1-4 の「コードの宣言と台帳の行が 1 対 1」の仕組みを弱める。
- 影響: `test_code_declarations_and_ledger_rows_are_one_to_one` ほか 10 件(負の対照を含む)が落ちる。data の要らない試験なので CI-1 が赤になる(10-13b §0-4)。実装役の試験の範囲(build_* と engine/time)に `tests/engine/bridging` が無く、記録 §10・§12 に申告が無い。
- 直し方: (1) 宣言を走査器が数える形にする。例: モジュールの表 `REAL_TIMETABLE_EXPEDIENTS`・`EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS`(名は `scan._TABLE_NAME` の形)に固定の文を置き、`res.expedients.extend(<表の名>)` で足す。動的な文(残る線の名の連結・`pm_expedient`)は固定の文と notes に分ける。(2) 台帳 `docs/design/bridging-ledger.json` の W12#4〜#8 の扱い(切替口 False の道の宣言として active のまま残すか、外した段 2-3b で removed にするか)と、新しい 8 行の追加は親が書く(実装役は台帳に触れない規律)。(3) 発注の「既存の試験が通る」の範囲に `tests/engine/bridging` を入れる。

### 低

- **L1** `tests/build_audit/test_audit_units.py` 240〜259 行: docstring が「`realworld_live`(検証専用)…は載らない」のまま(今は静的データ版 1 の 1 本が載る)。`odpt_rt` の負の対照が無い。直し方: docstring を直し、`realworld_live/odpt_rt/…` と `realworld_live/odpt_static/<別の日付>/…` の偽のファイルを置いて、等式で落ちないことを確かめる。
- **L2** `w12_external_nodes.py` 67 行: 切替口 False でもヘッダの `stage_version` は 1.2.0 なので、ヘッダ・manifest・build_hash は 1.1.0 とバイト一致しない(時刻表の parquet と params・ゲートなどは一致)。2-4 で旧値に戻す道として使うなら、この差を記録に書く。
- **L3** `tests/build_field/test_w12_real_timetables.py` 273 行: 「時刻の一覧を載せない」の検査が `"departure"` の語が無いことだけ。`HH:MM` の形(ISO の日時を除く)が無いことも確かめる方が強い。
- **L4** 層の名の扱いの食い違い: `tools/instruments/read_guard.py` 56 行は `realworld_live` を封印の語に入れ、回答 10-12b §1 は(W13 の文脈で)「`realworld_live` は読まない(検証専用のまま)」と書く。2-3b は構築が `realworld_live/odpt_static/` を読む(発注は構築側と明記)。機能の衝突は無い(計器はエンジンだけを回す)が、「`realworld_live` の下は検証専用」という読み方と食い違う。親が例外を宣言するか、静的データの置き場を分ける。
- **L5** 記録 §12 の 5(2-4 で動くもの)に、つなぎの台帳で `remove_at` が 2-3b の 8 行(W12#4〜#8・`BR-W12-HOLIDAY-GT-WEEKDAY`・`BR-W11-SHINSEN-EXIT`・`HD-engine.processes.rail-1af925f4`)が載っていない。

## 親に確かめてほしいこと

1. **H1 の直し方**: 宣言の形(モジュールの表)と、台帳の W12#4〜#8 を active のまま残すか removed にするか。新しい 8 行の `remove_at`。
2. **(中)京王のチャレンジ枠の時刻表を本体の世界資産に入れることと、回答 10-13b §5 の表の整合**: §5 の表は「チャレンジ枠の時刻表=今の扱いのまま(本体は公式 PDF・チャレンジ枠は作品だけ)」とし、同じ §5 で「ODPT の作品は本体を絞った版でよい」と書く。一方、回答 10-13 の 3・7 と計画 2-3b の行は「京王はチャレンジ枠で入れる(京王だけ本体)」。2-3b は計画どおり京王の 566 本を本体の W12 に入れた。2-4 で `data/world/v2` を差し替えると、本体の実験・論文・未踏・事業の世界に京王のチャレンジ枠の行が入る。限定ライセンス 第 4 条 1 項(目的は応募に限る)との関係を、ユーザーの言葉で 1 回確かめることを勧める(矛盾の検出=CLAUDE.md §2-1)。
3. **計画 2-3b の行の残り**: 計画は「終点の到着(井の頭線の急行は神泉を通過)」「直通の二重計上のまとめ方」も 2-3b に置き、つなぎの台帳の `BR-W11-SHINSEN-EXIT` も `remove_at` 2-3b。発注は渋谷の発車だけに絞ったので、これらは残っている。段を移すか、2-3b の続きを作るか。
4. **山手線の上り/下り**(推測・未リサーチ)をこのまま expedient にするか。
5. 実装役の作業用の置き場 `_bc/`(作業木の根・未追跡・テープ入り)は取り込みに載せないこと。
