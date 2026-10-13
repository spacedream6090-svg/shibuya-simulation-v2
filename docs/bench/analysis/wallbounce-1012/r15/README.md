# 第 1 期 1-5 権利台帳の器(CP4・CP3)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `1-5/rights`(HEAD `6b82be2`=T0・1-3・1-4 を取り込んだ後)。commit は親。
- 正: [口の約束 1-5](../../../../design/v2-foundation-contracts-2026-10-13.md)(〔決定(回答 10-13b §3)〕営業許可のオープンデータは許可の一覧の中で探し、無ければ空・`NO_PERMISSION` が 0 でなければ ▲ として第 2 期へ=縮める部分だけを腕にする)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) 第 1 期 1-5・[決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-5 CP3・CP4・§1-4(行動を止めるのは物理と機械の決まった動きだけ・権利に反する行動は「許可のない行動」として記録)・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(仮採用)。先例は [R-113](../../../../research/v2-r113-e1-foundations-existing-implementations.md) §5(権利を行で持つ実装は無い・Dwarf Fortress の司法=止めずに事件にする。形だけ借り、コードは写していない)。中身の出どころは [R-106](../../../../research/v2-r106-rights-institutions-tax-credit.md) §2-1 と [R-76](../../../../research/v2-r76-openpoi-reliability.md) #17。
- 数は実測。生の出力(テープ・side の JSON)は git の外の作業用の置き場(作業木の `_bc/`)に置いた。比べた結果と道具だけをこのフォルダに置く。
- 道具(`tools/`・使い方は各ファイルの冒頭・絶対パスなし): `count_no_permission.py`(止める検査が当たった回数を 19 構成で数える)・`add_bridges_r15.py`(つなぎの台帳に 1-5 の行を足す・`--check`)・`manifest_check_r15.py`(10f の manifest の 2 つの側を比べる・r14 の道具の写し)・`time_rights_r15.py`(台帳を作る時間と大きさ)。byte-check は既存の道具(`10e/byte_check_10e.py`)。

## 0. 結論

- **権利台帳の器**(`engine/rights/ledger.py`): `Right`(口の約束の 8 欄・凍結・slots)と `Rights`(列ごとの配列・1 行 72 B)。**書く口は `grant` と `revoke` の 2 つだけ**(AST の試験と負の対照)。属性の付け替えと消去は `AttributeError`・表は `MappingProxyType`・読み口は `holds`・`holders_of`(口の約束)と配列で引く `holds_each`・`holder_table`。
- **最初の中身**(`engine/rights/initial.py`・5,000 体の既定のラン): 雇用(W16 の `org_id`)2,421 行・担当従業者の雇用 2,337 行・店の賃借 2,337 行=**7,095 行**。営業許可 0 行と住まい 0 行は空欄として宣言した(§2)。全母集団(390,067 体)では 227,523 行(雇用 222,849=W16 の `org_id` を持つ体の数と同じ)。
- **`staff_of_poi` は権利台帳の `employ` の行から読む**。丸振りの規則は台帳の組み立てへ移しただけで、割り当ては HEAD と同じ(合成の世界 8 通り・実データの 5,000 体・再開の作り直しで値と型まで一致・byte-check 19/19)。
- **`NO_PERMISSION` の回数は 19 構成とも 0**(開閉店の口の権利の無い行 0・判断の応答の役割語 0・群・規範の計器 0)。口の約束どおり ◎ として、**腕を作らずに縮めた**: 開閉店の口は権利の無い行も止めず、出来事の記録へ `行為:許可のない行動`(原因 `Process("rights")`)を書く。役割語は権利台帳で確かめ、許可が無ければ記録する(待機/なしに落とすのは効果の先が無いからで、変えていない)(§4)。
- **結果不変**: byte-check 19/19 構成で 25 欄とも HEAD と同じ。manifest の 7 本は既存の欄が全部同じ(動いたのは `bridges_count` 273 → 277 と `bridges_version` だけ=つなぎの台帳に行を足したため)。
- manifest の末尾に `rights`(行の数・種類と物と出どころの分布・空欄のつなぎの台帳の行・許可のない行動の数)。
- 試験: 新しい試験 6 ファイル・101 本(§8)。全体は §8。仮採用は §10 の 12 件。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/rights/__init__.py`・`ledger.py`(新規) | `Right`・`RIGHT_FIELDS`・`Rights`(`grant`・`revoke`・`holds`・`holds_any`・`holders_of`・`holds_each`・`holder_table`・`tally`(数え=名は状態台帳の項目 `counts` との衝突を避けた)・`right`・`ended_by`)・番号の空間(`agent`・`org`・`store`・`parcel`・`dwelling`)・権利の種類(`own`・`lease`・`employ`・`licence`)と種類ごとに取れる物の表 |
| `src/shibuya/engine/rights/initial.py`(新規) | 最初の中身(`build_initial`・`staff_assignment`=HEAD の丸振りの規則・`staff_of_poi`=台帳から読む)・出どころの名・空欄 → つなぎの台帳の行の表 `BLANK_BRIDGES` |
| `src/shibuya/engine/rights/record.py`(新規) | `record_unauthorized`(起きた許可のない行為を出来事の記録へ書く口)・`events_of`(過程の ActualLog の口から出来事の記録を引く)・`RoleActCheck`(役割語の権利の判定だけ・書かない)・`manifest_fields`(manifest の `rights`)。〔§14 で改めた: 1 回目の `UnauthorizedLog` は消した〕 |
| `src/shibuya/engine/processes/opening.py` | `_assign_staff` を消し、権利台帳を持つ(`rights`・材料 `org_of_agent`)・担当の表は台帳から読む(`_staff_from_rights`)・再開の作り直しは台帳ごと・開閉店の権利は台帳に聞く(`holds_each`)・記録の口 `unauthorized`(`attach_unauthorized`) |
| `src/shibuya/engine/resolve.py` | `request_open_close`: 権利の無い行も効果を確定し(止めない)、`on_unauthorized` に渡す。結果の欄は今の値(`NO_PERMISSION`) |
| `src/shibuya/engine/llm_bridge.py` | `role_rights`(役割語の権利の確かめの口)・`attach_role_rights`。役割語のとき口を呼ぶ(行動コードの落とし方は変えない) |
| `src/shibuya/engine/processes/runner.py` | `org_of_agent` を開閉の過程へ渡す・`attach_events` で記録の口を開閉の過程に挿す・`rights`(読むだけの property)・`role_act_check`・`rights_fields`(manifest の中身) |
| `src/shibuya/engine/systems/build.py` | 母集団の `org_id` を体の順に並べて実行器へ(`_org_of_agent`)・判断の口に役割語の権利の確かめを挿す |
| ~~`src/shibuya/engine/systems/table.py`~~ | 〔§14 で戻した〕1 回目は decide の `writes.paths` に `E:events.*` を足したが、役割語の出来事を書かない形(検収 L4)にしたので HEAD のまま |
| `src/shibuya/engine/state_ledger.py` | 除外の一覧に 3 行(`runner.opening` の `rights`=導出・`org_of_agent`=設定・`bridge` の `role_rights`=参照・読むだけ)・計数の行 O73 に `runner.opening.n_unauthorized`・O86 に `bridge.n_role_unauthorized`・`n_role_unjudged`(どれも diag)〔§14〕 |
| `src/shibuya/engine/events/vocab.py`・`log.py` | 語 `行為:許可のない行動` を表の末尾に(56 語・版 `events-vocab/1-5`)・原因の名に検査の名 `rights`(`CHECK_PROCESSES`・`過程:` の語ではない) |
| `src/shibuya/engine/run.py`・`manifest_sections.py` | manifest の末尾に `rights`(観測の節) |
| `docs/design/bridging-ledger.json` | 4 行を足した(§3)。既存の行は変えていない |
| `tests/engine/rights/`(新規) | §8 |
| 凍結の表(増えた分だけ) | `tests/engine/time/manifest_keys_frozen.json`(末尾に `rights`)・`tests/engine/events/writes_paths_events.json`(decide) | 〔§14: `writes_paths_events.json` は HEAD に戻した〕
| **発注の編集してよい一覧の外**(数の固定を直しただけ) | `tests/engine/events/test_e_vocab_is_closed.py`(55 → 56 語・版)・`tests/engine/bridging/test_bridging_ledger.py`(見出し 74 → 76・ファイル 71 → 73・項 338 → 343・`HD-` の行 74 → 76)・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/test_env_and_sections_10f.py`(manifest の末尾の並びに `rights`)。発注が「語彙に足す」「新しい宣言は台帳に行を足す」「manifest に欄」を決めているので、直さないと落ちる(1-3・1-4 と同じ扱い) | 〔§14: 検収 L2 で `tests/engine/processes/test_opening.py` の 1 本(権利の無い開閉の結果=OK)も直した〕

## 2. 最初の中身の 4 つ(計画 1-5)

| 中身 | 行(5,000 体の既定のラン) | 行(全母集団) | 出どころ(`source`) | 欄 |
|---|---|---|---|---|
| (a) 雇用 | 2,421 | 222,849 | `w16_population.org_id` | holder=体・object=組織(W6 の組織台帳の番号=W16 の `org_id`)・開始前から終わりなし・原因なし |
| (a′) 担当従業者(`staff_of_poi` の置き換えの行) | 2,337 | 2,337 | `宣言:担当従業者の丸振り(engine.rights.initial)` | holder=体・object=店(POI)。HEAD の `_assign_staff` の規則(店 j → 従業者の j mod 人数 番目) |
| (b) 営業許可 | **0** | **0** | ― | 空欄=`BR-RIGHTS-LICENCE-BLANK` |
| (c) 店の賃借 | 2,337 | 2,337 | `w6_poi(区画にいること)` | holder=店・object=区画(POI の番号で代用)・家賃は空欄=`BR-RENT-BLANK`(1-4 の行)・貸し手(相手)も空欄 |
| (d) 住まい | **0** | **0** | ― | 空欄=`BR-RIGHTS-DWELLING-BLANK` |

- 種類の分布(既定のラン): 所有 0・賃借 2,337・雇用 4,758・許可 0。大きさ 510,840 B(1 行 72 B)。作る時間 0.022 秒(全母集団 0.69 秒・16.4 MB)(`time_rights_r15.py`・目安)。
- **(b) 営業許可の判断(記録から)**: 渋谷区の「食品等営業許可・届出一覧」は SHIBUYA OPEN DATA(`city-shibuya-data.opendata.arcgis.com`・データセット `e68f41ebfa5f4ea490ca9af701d44e02_0`・39,304 件・CC BY 4.0・最終編集 2026-09-09)にある(R-76 #17・R-106 §2-1)。ドメインは 10-12 で許可の一覧に入った。ただし本体は取得されていない(`data/realworld/` に置き場が無く、取得の記録 `data/realworld/_ledger.jsonl` にも無い)。ネットは使わない発注なので、**行は 0 で空欄を宣言した**。取得は親に頼む。取れても、1 件が 1 つの許可で施設の数と一致しない・廃業を含む(R-76)ので、POI と突き合わせる規則(名前と座標の距離など)を決めてからでないと行は作れない(設計者の指紋になる=判断が要る)。
- **(d) 住まいの判断**: 国勢調査 2020 の表 18-4(住宅の所有の関係・町丁目)は表の場所だけ分かり、値は未取得(R-106 §2-1 #40 △)。住宅・土地統計調査の渋谷区 36.55%(二次・△)は検証専用の候補で、割り当てには使わない。W16 の世帯(`w16_households.parquet`)に持ち家/借家の列は無い。**行は 0 で、欄(`own`/`lease` の物 `dwelling`)だけ用意した**。e-Stat は取得の許可の一覧にあるので、取得は親に頼む。

## 3. つなぎの台帳に足した行(273 → 277 行)

| id | 外す段 | 根拠 | 中身 |
|---|---|---|---|
| `HD-engine.rights.initial-1af925f4` | **4-1**(§14・検収 L6) | inferred | `initial.py` の見出し「expedient(本モジュール分)」の項 3 個(担当従業者の丸振り・店の賃借=全 POI と区画の代用・最初の行の時刻)。丸振りの項は `HD-engine.processes.opening` の項 1 と同じつなぎ=外す段をそろえた |
| `HD-engine.rights.record-1af925f4` | 6-6 | inferred | `record.py` の見出しの項 2 個(役割語の権利の判定・許可のない行動の出来事の欄) |
| `BR-RIGHTS-LICENCE-BLANK` | 4-2 | plan(計画 4-2「営業許可」) | 営業許可の行は 0 |
| `BR-RIGHTS-DWELLING-BLANK` | 4-2 | inferred(発注「住まいの権利=4-2 で」・計画 4-2 は賃貸借だけ書く) | 住まいの行は 0 |

- 家賃の空欄は 1-4 の `BR-RENT-BLANK` に結んだ(行は足していない=`initial.BLANK_BRIDGES` の `lease.rent`)。
- **既存の行で親に確かめてほしいもの**: `HD-engine.processes.opening-1af925f4`(外す段 1-5=1-4 で実装役が当てた)。1-5 では丸振りの規則を `initial.py` へ**移しただけ**(値は不変=つなぎは外れていない)。`opening.py` の見出しの項 1 つ目は「規則は権利台帳の組み立てへ移し、ここは台帳から読む」に書き換えた(項の数 4 と見出しの文は同じ=行の id と `what` は同じ)。この行の外す段(残りの 3 項=日跨ぎ・REPLACEMENT の意味・5 分刻み)を直すかは親の判断(発注は「行を足すだけ」)。
- 1 対 1(コードの宣言 ↔ 台帳の行)は 6 形とも欠け 0・余り 0。数: 見出し 74 → 76(ファイル 71 → 73・項 338 → 343)。ほかの形は同じ。

## 4. `NO_PERMISSION` の回数(19 構成)と縮めた範囲

数え方(`count_no_permission.py`・関数を包んで数えるだけ): HEAD の側は `6b82be2` の写しの src(5,000 体・seed 1・1 日・mock/古典)。`NO_PERMISSION` を `last_result` に書くのは src の中で `resolve.request_open_close` だけ(grep)。その呼び手は開閉の過程だけで、HEAD は `permitted=np.ones(...)` を渡していた。役割語は判断の口(`LLMBridge.call`)で待機/なしに落としていた(「権限検査待ち」の印)。表の全体は [no_permission_r15.json](no_permission_r15.json)。

| 構成 | 開閉店の口を通った行 | うち権利の無い行(HEAD) | 役割語(HEAD) | 計器の no_permission(HEAD) | 許可のない行動の記録(r15) | final(両側で同じ) |
|---|---|---|---|---|---|---|
| w6_v3_default | 20 | 0 | 0 | 0 | 0 | 5f7ae9ff24005314 |
| w6_v3_activity_off | 19 | 0 | 0 | 0 | 0 | e0054a837c6ec4c1 |
| w6_v1_default | 19 | 0 | 0 | 0 | 0 | 24375ee3dab349e8 |
| w6_v1_derive_v2_1 | 16 | 0 | 0 | 0 | 0 | 59329a9a3611c16c |
| w6_v2 | 19 | 0 | 0 | 0 | 0 | 7e3a16b4190c10b5 |
| w6_v1_edge | 18 | 0 | 0 | 0 | 0 | 0e0430daa24c109e |
| w6_v2_edge | 22 | 0 | 0 | 0 | 0 | 8151c3ee812ef412 |
| w6_v1_edge_plateau | 16 | 0 | 0 | 0 | 0 | a9d0c78a8e3bb079 |
| w6_old_v1_default | 19 | 0 | 0 | 0 | 0 | 5f3665e29e8c55e1 |
| w6_old_v1_derive_v2_1 | 16 | 0 | 0 | 0 | 0 | f1ac9740ef2d04ca |
| w6_old_v2 | 19 | 0 | 0 | 0 | 0 | 24efbaa77c1ce701 |
| w6_old_v1_edge | 18 | 0 | 0 | 0 | 0 | 607b93b4cef8f716 |
| w6_old_v2_edge | 22 | 0 | 0 | 0 | 0 | c1056e6fda20f2c5 |
| w6_old_v1_edge_plateau | 16 | 0 | 0 | 0 | 0 | 8a15b93709c7ebdf |
| w6_golden_null_arm | 18 | 0 | 0 | 0 | 0 | 354f49ca9a61b986 |
| v3_mem_store | 20 | 0 | 0 | 0 | 0 | f7ff0a6953fb9a38 |
| v3_mem_rel | 21 | 0 | 0 | 0 | 0 | 73a78288ab5e1498 |
| v3_classical | 17 | 0 | 0 | 0 | 0 | 202a05a22c5bd8e1 |
| v3_classical_mem_rel | 22 | 0 | 0 | 0 | 0 | 4c512a1fdc2a70c0 |

- **19 構成とも 0** → 口の約束の ◎。腕(`--rights-check`)は作っていない。mock の判断は横断語だけを引く(役割語を出さない)ので役割語は 0。古典も役割語を出さない。
- **縮めた範囲**:
  - `resolve.request_open_close`: 権利(`permitted`)の無い行も**止めない**。開閉の旗は権利のある行と同じに確定し、権利の無い行を `on_unauthorized` へ渡す。開閉の過程が渡す口は `UnauthorizedLog.record`=出来事の記録へ `行為:許可のない行動`(`who`=体・`where`=店の POI・原因 `Process("rights")`)を 1 行ずつ。結果の欄は今の値のまま(`NO_PERMISSION`=許可のない行動の印・仮採用 §10 の 5)。開閉の過程は権利を台帳に聞く(`holds_each`・担当の表は台帳から読んだので全部 真)。 〔§14 で改めた: 権利の無い行の結果も `OK`(行動は起きた)・印は出来事の記録にだけ=検収 L2。記録の口は開閉の過程の ActualLog の `event_sink` から引き、数えは開閉の過程の `n_unauthorized`〕
  - `llm_bridge.py` の役割語: 「権限検査待ち」の意味を外した。権利台帳の確かめの口(`RoleActCheck`)が、権限の持ち主が「従業者」の語(接客・補充・開閉店・価格改定)で雇用の行を 1 つも持たない体を記録する。行動コードを待機/なしに落とすのは変えていない(効果の先=世界の部品が無い=決定 10-12 D4 の「欠陥」の側で、権利の検査ではない)。 〔§14 で改めた: 役割語は行動が起きない(待機に落ちる)ので出来事は書かず、許可なし・判定しないの数だけを判断の口の計器(`n_role_unauthorized`・`n_role_unjudged`)に出す=検収 L4・L10〕
- **縮めていないもの**(物理と機械の決まった動き・止める検査でないもの): 開閉の過程が担当が現場(同じセル)に居るかを見る所(物理)・営業時間の旗と `open_mask`(機械の決まった動き)・補充の過程の `has_permission`(従業者・担当・同じセル・営業中=誰が実行するか(担当か engine_rule の代打か)を選ぶ所で、どちらでも補充は起きる=止める検査ではない)・開閉の過程の `has_permission`(試験だけが呼ぶ・同じ形)。

## 5. `staff_of_poi` の同値

- 比べた相手は HEAD の `OpeningProcess._assign_staff` の写し(試験 `test_staff_of_poi_equivalence.py` の `head_assign_staff`)。
- 合成の世界 5 通り+種別の端 3 通り(従業者 0・1 人・全員)・POI 0・実データ(5,000 体の抽出・seed 1・POI 2,337)で、配列の値と型(int64)まで同じ。担当のいる店ごとに `holders_of((store, j), employ)` が担当の体 1 人だけ。
- 再開の作り直し(`rebuild_derived`)は台帳ごと作り直し、同じ行(値まで)・同じ配列(補充の過程と共有)を保つ。既存の再開の試験(`test_resume_10d.py`)も通る。
- byte-check 19/19(§6)。

## 6. 結果不変

| 検査 | 方法 | 結果 |
|---|---|---|
| byte-check 19 構成([byte_check_r15.json](byte_check_r15.json)) | `10e/byte_check_10e.py`・5,000 体・seed 1・1 日・テープつき。HEAD の側は `6b82be2` の `git archive` の写し(src・anchors・予算の表・w6 の道具・`rules-table.json`・`bridging-ledger.json`+祝日の CSV・`src_is_worktree` 偽)、r15 の側は作業木の src(`--src src`=`PYTHONPATH`・`src_is_worktree` 真) | **19/19 構成で 25 欄とも同じ**(2 回=直しの前と、`counts` の名を `tally` に替えた後。記録の JSON は 2 回目)。既定 v3 の final `5f7ae9ff24005314` |
| manifest の 7 本([manifest_check_r15.json](manifest_check_r15.json)) | 10f の `manifest_check_10f.py side`(両側 `PYTHONHASHSEED=0`)→ `manifest_check_r15.py` | **all_ok**。既存の欄 1,737〜2,253 個が全部同じ。足したのは `rights` の中の 21 欄と節の表の 1 行(計 22)。動いたのは `bridges_count`(一番上と日次の各行=273 → 277)と `bridges_version`(`470a7a543f5c5b61` → `99311158c5cb6093`)だけ。final は 7 本とも同じ(r15 の側は直しの後に回し直した) |
| 数えた 2 つの側の final | `count_no_permission.py`(テープなし) | 19 構成とも HEAD と同じ final |

- **作業の事故(記録)**: r15 の側の最初の試みは `--src` を付けずに回し、venv が本体の src を読んでいた(`src_is_worktree` 偽で気づいた)。その出力は捨て、`--src src` で回し直した(上の表はその後の回)。venv は本体の src を入れてあるので、**作業木の側にも `--src`(か `PYTHONPATH`)を付けること**。

## 7. manifest の `rights`

- 一番上の鍵の末尾(凍結の表は 112 鍵)・節は観測(権利は行動で変わる段=2-1 で動く)。
- 中身: `rows`・`with_until`(終わりの時刻がある行)・`by_kind`(4 種とも)・`by_holder_kind`・`by_object_kind`・`by_source`・`bytes`・`blank_bridges`(空欄 → つなぎの台帳の行)・`unauthorized`(`rows`・`by_act`・判定しない職務の語の `unjudged_by_act`)。世界過程の無いランは `null`。
- 既定 v3(5,000 体): `rows` 7,095・`by_kind` 所有 0/賃借 2,337/雇用 4,758/許可 0・`unauthorized.rows` 0。 〔§14: `unauthorized` の中身は `open_close`(開閉の過程)・`role_action_unauthorized`・`role_action_unjudged`(判断の口)の 3 つに改めた〕
- 記録だけ: 台帳の中身を変えても final と呼数は同じ(試験)。日次の記録には足していない(1-3 の `events` が末尾の並びを固定しているため・必要なら親が決める)。

## 8. 試験

- 新規 `tests/engine/rights/`(6 ファイル・101 本・1 回 約 80 秒=うち 19 構成の生きた数えが 約 70 秒):
  - `test_rights_schema.py`(42): 欄の名と順・表(MappingProxyType)・凍結と slots・不正な行 16 形・値の正規化・`grant` の往復(値まで)・時刻の窓・`revoke`(1 回だけ・始まる前は不可)・`Right` 以外は書けない・属性の付け替えと消去(5 名)・読み口は写し・**書く口は 2 つだけ(AST)**・台帳の外から列に触らない(src 全体の AST)・負の対照(第 3 の書く口 4 形・外からの書き 5 形)。
  - `test_rights_from_w16.py`(5): 雇用の行=W16 の `org_id` を持つ体(全母集団=222,849・値まで)・4 つの中身と空欄・5,000 体の抽出と組み立ての材料の関数・母集団の無いラン・空欄の行がつなぎの台帳に active。
  - `test_staff_of_poi_equivalence.py`(12): §5。
  - `test_no_permission_count.py`(22): 19 構成の生きた数え(200 体・0 でなければ警告 `NoPermissionHit`=▲ の印で落とさない)・5,000 体の記録の表・▲ の印の負の対照。
  - `test_rights_events.py`(15): 語彙と原因(1-3 の 55 語のコードは不変)・開閉店の口(止めない・記録・結果の欄)・開閉の過程の端から端(担当の雇用を `revoke` すると記録されて店は開く)・役割語(従業者の語 4 つ・職務の語・「全員」の語・口なし)・記録を切ったときの数え・既定のランは 0 行。
  - `test_rights_manifest.py`(5): §7。
- 既存の `tests/engine/systems`・`events`・`rules`・`bridging`・`time` と開閉・補充・規範の計器・10f の試験: 394 passed(数の固定を直した後)。
- 全体(`-m "not gpu and not slow" -n 4 --dist loadfile`・data あり・作業木): 1 回目は 4 failed。うち 3 件は `tests/engine/test_state_checks_10f.py`(軸 1 の AST: 台帳の数えの名 `counts` が状態台帳の項目 `counts`=軸 1 no/diag と名前で衝突)=名を `tally` に替えて直した。残りの 1 件は既知の落ち(下)。**2 回目: 4,280 passed・1 failed(既知・§11)・1 xfailed(15 分 33 秒)**。

## 9. 共有のファイルの一覧(取り込みの rebase 用)

`engine/state_ledger.py`(除外の一覧に 3 行・計数の行 O73 と O86 に 3 項)・`engine/systems/build.py`(実行器の引数 1 つ・判断の口に挿す 1 行・末尾に補助の関数 1 つ)・`engine/llm_bridge.py`(属性 3・口 1・数える 5 行・計数 2 鍵と docstring)・`engine/resolve.py`(`request_open_close` だけ)・`engine/run.py`(manifest の末尾 1 欄)・`engine/manifest_sections.py`(1 行)・`engine/processes/runner.py`・`engine/processes/opening.py`・`engine/events/vocab.py`・`engine/events/log.py`・`docs/design/bridging-ledger.json`(末尾に 4 行)。凍結の表: `tests/engine/time/manifest_keys_frozen.json`。数の固定: §1 の表の最後の行の 5 ファイルと `tests/engine/processes/test_opening.py`。`cli.py`・`engine/systems/table.py` は触っていない(§14)。

## 10. 仮採用(回答 10-13b §0-3)

1. **権利台帳の置き場=開閉の過程**(`runner.opening.rights`・実行器から `runner.rights` で読む)。状態台帳では導出(SoA の種別・W16・POI の数から作る・再開で作り直す)。共有のファイル(箱・持ち主の名・状態台帳の行)を増やさないため。権利が行動で変わる段(2-1)で、独立の持ち主と状態の行にする。
2. **番号の空間 5 つ**(体・組織=W6 の番号・店=POI の番号=お金の台帳の店舗の口座と同じ索引・区画・住まい)。権利を持てるのは体・組織・店(口の約束の「体の id か組織の id」に店を組織として含めた)。
3. **店の賃借=すべての POI**(お金の台帳が全 POI を店とするのに合わせた)・区画の番号は POI の番号で代用・貸し手は空欄。
4. **担当従業者の雇用の行を W16 の雇用の行と別に持つ**(物=店)。丸振りの規則と組織台帳の対応は無い(HEAD と同じ近似)。
5. **開閉店の権利の無い行の結果の欄=`NO_PERMISSION`(今の値のまま)**・効果は確定。発注の「`last_result` は今の値のまま」をこう読んだ。代案: 止めないのだから `OK` にする(本人の知覚に「権限なし」が載らない)。今の既定では 0 回なので結果は同じ。 〔§14 で改めた: 結果は `OK`(検収 L2)〕
6. **役割語の判定=雇用の行を 1 つでも持つか**(対象の店を見ない)・職務の語(乗務員・駅員・指令)は判定しない(数えるだけ)・「全員」の語は何もしない。役割語の効果と対象の解決を作る段(6-6 ②)で直す。
7. **出来事の語 `行為:許可のない行動` を表の末尾に**(1-3 の 55 語のコードを動かさない)。口の約束の英字 `unauthorized_act` ではなく、発注と 1-3 の語の形(`族:語`)に合わせた。行為 12 語の写し(語彙 v3)には入れない。
8. **原因=`Process("rights")`**(発注どおり)。役割語の記録でも LLM の呼び出し(`LlmCall`)ではなく検査を原因にした。検査の名は `過程:` の語に足さない(`CHECK_PROCESSES`)。 〔§14: 役割語は出来事を書かなくなったので、原因 `rights` の行は開閉店だけ〕
9. manifest の `rights` は**観測の節**。日次の記録には足していない。
10. **規則の表(`rules-table.json`)に営業許可の行は足していない**(許可の行が 0 で読み手が無い・足すと `rules_version` が動く)。
11. **列は書き込める配列**(段 A の守り `test_direct_flag_writes_live_only_in_known_places` が `flags.writeable=True` を既知の場所の外で禁じる)。書く口が 2 つだけなことは AST の試験(台帳の中と src 全体)と負の対照で守る。 〔§14: 中身は名を変えた slot の `_Store` へ移し、AST は 1-9 と同じ広さにした(検収 M1)〕
12. **decide 系の `writes.paths` に `E:events.*`** を足した(役割語の記録を書く系)。 〔§14 で戻した: 役割語の出来事は書かない(検収 L4)〕

## 11. 限界と空欄・親に確かめてほしいこと

- **営業許可の行を作るには**: 区のデータの取得(親に頼む・ドメインは許可の一覧の中)と、POI との突き合わせの規則の判断(§2)。
- **住まいの行を作るには**: 国勢調査の表 18-4 の値の取得(e-Stat・親に頼む)と、世帯への割り当て方の判断(町丁目の割合で抽選するなら乱数の鍵も)。
- **艦隊(fleet)の経路の役割語は確かめていない**: 落とし方は `llm/fleet.py`(llm の層=engine を読めない)にあり、確かめの口を挿していない。GPU の後に、受け取りの系(`llm_io`)で同じ口を呼ぶ形にする。
- **職務の役割語は判定しない**: W16 の職務者(駅員・運転士・指令・警察など `duty_role` を持つ 1,316 体)は `org_id` を持たず、権利台帳に職務の行が無い。行の作り方(相手の組織)は 4-1/4-2 の判断。
- **開閉の過程の見出しの行の外す段**(§3)。
- `NO_PERMISSION` の数えは mock と古典の 19 構成だけ。実 LLM のテープ(1-10 の 52 本)は数えていない(役割語は出うる)。
- 記録だけで、気づいた人・持ち主・警察の事後の反応は無い(後の段)。許可のない行動の頻度を現実の統計と比べるのも後の段(検証専用)。
- 既知の落ち `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` は、作業木の `data` が本体への junction であることで起きる(1-3・1-4 の記録と同じ・本体では通る)。

## 13. 親の検収(第334・2026-10-14)

- 親の byte-check 4 構成(本体 HEAD ec060e7 の src=1-4・1-6・1-9 取り込み済み vs 作業木の src・--src 指定): final が同じ 4/4。動いた欄は w6_v3_default と v3_mem_rel の end_of_day/full_last だけ=本体には 1-9(K17=輪 6.5)が入り、この枝の土台(6b82be2)には入っていないための差(1-5 の変更ではない)。本体へ rebase した後に親がもう一度 4 構成を回して 0 になることを確かめる(parent_head_vs_r15_4cfg.json)。
- 親の答え: 営業許可(区の一覧 39,304 件・CC BY 4.0)と住まい(e-Stat 表 18-4)の中身は 4-2 で埋める(取得は許可の一覧の中=親が 4-2 の前に)。既存の台帳の行 HD-engine.processes.opening-1af925f4(外す段 1-5)は丸振りを台帳からの読みに移しただけなので、外す段を 4-1(組織と関係の実データ)に改める(取り込み後に親)。職務者 1,316 体の org_id 無しは W16 の弱点の行に含める。艦隊の経路の役割語は 6-4 で。独立検収(review.md)=条件つき受入 → M1(書く口の AST の検査=rights_writers.py・台帳の中身を名を替えた slot に・負の対照 26 形)と低 L1・L2(止めない行の結果は OK)・L3・L4/L10(役割語は出来事を書かず数えるだけ・持ち主またぎを消した)・L6・L9 を実装役が直した(§14)。直しの後の試験 718 passed・byte-check 4 構成 同じ(実装役・土台 6b82be2)。

## 14. 独立検収(review.md)の後の直し(親の判断・第334)

親の判断: M1 と低 L1〜L4・L6・L9・L10 を直す。L5 は記録へ写す。L7 は下の注のとおり不要になった。L8 と開閉の過程の見出しの行(4-1)は本体へ rebase した後に親が足す。

| 項 | 直し |
|---|---|
| **M1** 書く口の AST の穴 | 書く形を 1-9 の `tests/economy/cp2/money_writers.py` と同じ広さにした検出器 `tests/engine/rights/rights_writers.py` を作った(本体の 1-9 は rebase の後に来るので規則を写した=rebase の後に共通化の候補)。数える形: 添字への代入と `+=`・`fill`/`put`/`sort`/`itemset`/`resize`/`setfield`/`partition`・`np.copyto`/`put`/`place`/`putmask`/`put_along_axis`/`fill_diagonal`・`ufunc.at`・`out=`・局所の別名(添字・ビュー・`getattr`・`for` を通す)・`setattr`/`object.__setattr__`/`delattr`/`vars()`/`__dict__` の 4 形・名が式の `getattr`/`setattr`(名の分からない書き)。台帳の中は「列の中身を書くのは `Rights._write` だけ・差し替えは `_Store.__init__`・`Rights.__init__`・`grant`・`_grow` だけ・`_write` を呼ぶのは `grant`・`revoke` だけ・`_grow` を呼ぶのは `grant` だけ」。台帳の外(src 全体)は列の名(`_r_*`)・名を変えた slot・`_Store`・`_COL_NAMES`・`_COLS` の参照と import、名を組み立てる文字列(定数の足し算・f 文字列の頭)、中の名への `setattr` の 4 形、他の物の `_write`/`_grow` を落とす。**負の対照は台帳の中 13 形(検収で通った `fill`・`np.copyto`・`put`・`np.add.at`・局所の別名・`getattr` の別名・`out=`・slot の差し替え・`for` の別名を含む)と外 13 形(検収で通った外からの `object.__setattr__(rights, '_n', 0)`・`'_r' + '_kind'` の `getattr`・`_COL_NAMES` を回す `getattr`・f 文字列・`_COL_NAMES` の import・名を変えた slot・`vars()` を含む)**。正の対照=決めた所に書きが実際にあること |
| M1 実行時 | 台帳の中身(列・行の数・出どころの表)を名を変えた slot 1 つ(`_Rights__st` の `_Store`)へ移した。`Rights` は `__slots__ = ("__st",)` だけ(`__dict__` なし)なので、`object.__setattr__(rights, "_n", 0)`・`object.__setattr__(rights, "_r_kind", …)`・`rights._r_kind`・`vars(rights)` は実行時に止まる(試験)。**止められない形(限界)**: 名を変えた slot の名を知って触る形(`object.__setattr__(rights, "_Rights__st", …)`・`rights._Rights__st.n = 0`)=Python の限界。src の中では上の AST が止める(試験 `test_the_runtime_limit_is_the_mangled_slot`) |
| L1 | `RoleActCheck.__call__` の引数の名 `tick` → `step` |
| L2 | 止めずに旗を確定した開閉の行の結果を **`OK`** にした(`out_code` と `last_result`)。「許可のない行動」の印は出来事の記録にだけ(仮採用 5 を改めた)。`NO_PERMISSION` を書く所は src から無くなった(契約の失敗の語としては残る)。既存の試験 `tests/engine/processes/test_opening.py` の 1 本を「止めない・結果は OK・権利の無い行を記録の口へ渡す」に直した |
| L3 | 判断の系(decide)の中で回す試験 `test_role_words_inside_the_decide_system`(台本の LLM・`run_day` 60 体・720 刻み・語彙 v1): 開閉店は 350 呼のうち雇用の行の無い体の 261 を数え(検収役の値と同じ)、発車は全部を判定しない語として数える。出来事は 0 行・確かめの口を外したランと final と呼数が同じ |
| L4 | 役割語は待機/なしに落ちて行動が起きないので、**出来事は書かない**。数(許可なし・判定しない)だけを判断の口の計器 `n_role_unauthorized`・`n_role_unjudged`(状態台帳の O86=diag・`bridge.counters()` の `role_unauthorized`・`role_unjudged`)に出し、manifest の `rights.unauthorized.role_action_unauthorized`・`role_action_unjudged` に載せる。出来事を書くのは行動が起きた所(開閉の過程)だけ |
| L6 | `HD-engine.rights.initial-1af925f4` の外す段を 4-2 → **4-1**(丸振りの項は `HD-engine.processes.opening` の項 1 と同じつなぎ)。開閉の過程の行の 4-1 は rebase の後に親 |
| L7 | **不要になった**: L4 で decide の系は出来事を書かなくなったので、1 回目に足した decide の `writes.paths` の `E:events.*` と凍結の表 `writes_paths_events.json` の decide を HEAD に戻した(`engine/systems/table.py` は HEAD のまま)。行 E の注(書く系)は変えていない(phase_c は 1-9=rebase の後) |
| L9 | 19 構成の生きた数えのうち 18 構成を `slow` にした。既定 v3 の 1 構成だけを `slow` の外に残した(軽い版) |
| L10 | 持ち主をまたぐ書きをやめた: 1 回目は decide の系が開閉の過程の持つ記録の物(`UnauthorizedLog`)の数えを書いていた。役割語の数えは判断の口(`LLMBridge`=decide の持ち物・O86)に、開閉の数えは開閉の過程(`n_unauthorized`=O73・world の系)に持たせた。開閉の過程の出来事の記録は ActualLog の口(`event_sink` の `ActualLogLink`)から引く(新しい参照を持たない)。状態台帳の除外の REF `runner.opening.unauthorized` は消した。`bridge.role_rights` は読むだけの口(状態を持たない) |
| L5 | 検収役の値を写す(下) |

**検収役が確かめた結果不変(L5・review.md §1 から写した・1 回目の差分に対して)**: byte-check 4 構成(`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`)で 25 欄とも同じ(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`・full_last と end_of_day も同じ)・2 日のラン(5,000 体・seed 1・既定 v3)全欄同じ(final `912446bd2b42b6ab`・140,913 呼・テープの calls `cb330e76b4b8a573`・blocks `7f09f3dc78d84ac4`・暦 07-13 → 07-14)・系ごとの指紋 3 構成で全部の系・全部の刻みが同じ(合成 80 体 720 刻み 19 系・並び 6,664/世界資産 300 体の既定 v3 19 系・15,598/記憶+関係 21 系・17,710)・再開(`tests/engine/processes`・`test_t0_tm9_fields.py`・`test_rebuild_gives_the_same_ledger`)・`staff_of_poi` の独立の再計算 1,284 本(合成 640 通り+作り直し・実データ seed 2 と 3)で値と型が同じ。

**直しの後の結果不変**: byte-check 4 構成(土台 `6b82be2` の写しの src=`src_is_worktree` 偽 vs 作業木の src=`--src src`・真)=**4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`・[byte_check_r15_fix_4cfg.json](byte_check_r15_fix_4cfg.json))。

**親の答え(記録)**:
- 営業許可(区の一覧 39,304 件)と住まい(表 18-4)は **4-2 で入れる**。今は空欄の宣言のまま(`BR-RIGHTS-LICENCE-BLANK`・`BR-RIGHTS-DWELLING-BLANK`)。
- 予算の宣言(1 行 72 B・全母集団 227,523 行=16.4 MB)は親が設計書に足す。

**限界に足す: `NO_PERMISSION`=0 は作りから来る**。(i) HEAD の開閉の過程は `permitted=np.ones(...)` を渡していた(担当の表と権利が同じ物から作られる)=権利の無い行は作りの上で出ない。(ii) mock と古典は役割語を出さない(19 構成で役割語 0)。(iii) 群・規範の計器の `no_permission`・`role_actions` は判断の口が役割語を待機に置き換えた**後**の行動コードを見るので、役割語を数えられない(1-5 の前からの盲点=検収で台本の LLM に 409 呼「開閉店」を答えさせても計器は 0)。だから「19 構成とも 0」は「今の既定に止める経路が無い」ことの確認で、結果不変の**強い根拠は次の 2 つ**: 縮めた後も役割語の行動コードは今までどおり待機/なしに落ちる(L3 の試験=確かめの口を外しても final が同じ)・記録は出来事の記録(行 E=軸 1 diag・軸 2 discardable)と計数の行(O73・O86=diag)だけに入る。

**記録の JSON について**: `no_permission_r15.json` は直しの前に取った(HEAD の側の数=止める検査が当たった回数は HEAD の src なので直しと関係なく有効。作業木の側の `r15_rights.unauthorized` は 1 回目の形=`rows`・`by_act`・`unjudged_by_act`)。`byte_check_r15.json`・`manifest_check_r15.json` も直しの前(19 構成・7 本)。直しの後は byte-check 4 構成だけを回した(親の指示)。

**試験(直しの後)**: 範囲(`tests/engine/rights`・`systems`・`events`・`time`・`bridging`・`processes`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/test_cli.py`・`-m "not slow" -n 4 --dist loadfile`・作業木): **718 passed・0 failed(6 分 15 秒)**。`slow` の 18 構成の生きた数えは別に回して通った(`tests/engine/rights` を印なしで=125 本)。新しい試験は 125 本(`slow` の外 107)=`test_rights_schema.py` 65・`test_no_permission_count.py` 22・`test_rights_events.py` 16・`test_staff_of_poi_equivalence.py` 12・`test_rights_from_w16.py` 5・`test_rights_manifest.py` 5。途中で 1 回 `test_state_ledger_10b.py::test_ast_check_passes_on_the_current_source` が落ちた(台帳の中の局所の名 `st` が状態台帳の AST の「SoA らしい名」に当たり、`getattr(st, 変数)` が解決できない動的な読みとされた)=名を `store` に替えて直した。`lint-imports` は 5 kept・0 broken。

## 15. 本体への rebase の衝突の解き方と合わせ(親の指示・第334)

本体 `fc05011`(1-6・1-9・1-2 取り込み済み)へこの枝(`8434a27`)を rebase した時の衝突 9 本の印を解いた。方針は「両方の追加を残す」。`git add`・`rebase --continue`・commit は親がする(実装役は git の操作をしていない。台帳の 2 つの版は `git show` で読んだだけ)。

| ファイル | 解き方 |
|---|---|
| `src/shibuya/engine/manifest_sections.py` | 本体の `percept`(1-2・設定)の後ろに 1-5 の `rights`(観測) |
| `src/shibuya/engine/run.py` | manifest の末尾の並び=T0 の TM9 → 1-4 の 3 欄 → `economy`(1-9)→ `percept`(1-2)→ **`rights`(1-5・最後)** |
| `src/shibuya/engine/systems/build.py` | `if runner is not None:` の中(`attach_events` の直後)に 1-5 の役割語の確かめの口、その後ろに本体の 1-9 の金の出来事の口(`MoneyEventLink`)。1-5 の注は「確かめて数える(出来事は書かない)」に直した |
| `tests/engine/time/manifest_keys_frozen.json` | 凍結の鍵 113 → **114**(末尾 `economy`・`percept`・`rights`)・注は本体の注に 1-5 の 1 文を足した |
| `tests/engine/time/test_t0_tm9_fields.py` | 1-4 の 3 欄の後ろが `economy`・`percept`・`rights` |
| `tests/engine/bridging/test_manifest_rules_bridges.py` | 1-4 の 3 欄は末尾の 3 つ前までの続き・末尾 3 つが `economy`・`percept`・`rights` |
| `tests/engine/test_env_and_sections_10f.py` | 本体の `C19_KEYS`・`P12_KEYS` を残し、末尾の並び `_tail` に `R15_KEYS` を足した。`CONFIG_PATHS_SHA256` は変えていない(`rights` は観測の節=設定の節の道筋に入らない。試験が通ることで確かめた) |
| `tests/engine/bridging/test_bridging_ledger.py` | 見出しのファイル 73・項 342(本体の 71・337=1-2 が p_notice の項を 1 つ消した後に、1-5 の 2 見出し=項 3+2)。見出しの数 76・`HD-` の行 76 は 1-5 の側の値のまま |
| `docs/design/bridging-ledger.json` | 本体の 277 行(1-4 の 273・1-6 の `DOC-memory-store-legacy`・1-9 の `DOC-money-fare-cause-rail`・`DOC-money-uncaused-rows`・`DOC-k17-raw-ring-coefficient`・1-2 の項の数の直し)を全部残し、末尾に 1-5 の 4 行と下の L8 の行を足した=**282 行** |
| (衝突ではない合わせ)`tests/perception/facts/test_percept_schema.py` | `keys[-1] == "percept"` を末尾 3 つ `economy`・`percept`・`rights` の確かめに(1-5 の `rights` が最後に来るため) |

**合わせ(親の指示)**:
1. **L8 の行** `BR-RIGHTS-FLEET-ROLE-CHECK`(外す段 **6-4**・文書の行の 9 欄・inferred・宣言の置き場=この記録 §15): 艦隊の経路の役割語に権利台帳の確かめの口を挿していない(役割語を落とす所は `llm/fleet.py`=llm の層で、engine の権利台帳を読めない)=艦隊のランでは `n_role_unauthorized`・`n_role_unjudged` が 0 のまま。艦隊の受け取りの系(`llm_io`)で同じ口を呼ぶ段で外す。
2. **既存の行 `HD-engine.processes.opening-1af925f4`** の外す段を 1-5 → **4-1** に改めた。`why` に「1-5 では丸振りを権利台帳からの読み(`engine.rights.initial` の employ の行)に移しただけ=つなぎは外れていない・実データは 4-1」と書いた。`HD-engine.rights.initial-1af925f4`(4-1)とそろった。
3. **状態台帳の行 E の注**: 書く系に decide は入っていない(L4 で役割語の出来事を書かなくなった=1-5 の decide の宣言は戻した)=矛盾なし。ただし本体の注は書く系を「world・checkpoint・day_close・close_final」のままにしていて、1-9 で凍結の表 `writes_paths_events.json` に入った **phase_c が抜けていた**ので、注に phase_c(1-9)を足し、「凍結の表と同じ・1-5 の役割語は出来事を書かない=decide は書く系でない」と書き添えた(注だけ=道筋・軸は変えていない)。

**突き合わせ**: つなぎの台帳とコードの宣言は 6 形とも欠け 0・余り 0(見出し 76・ファイル 73・項 342・active 282 行)。

**試験(rebase の後・作業木)**: 範囲(`tests/engine/rights`・`systems`・`events`・`time`・`bridging`・`rules`・`memory`・`tests/perception`・`tests/economy`・`tests/engine/processes`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/test_cli.py`・`-m "not slow" -n 4 --dist loadfile`): **1,388 passed・0 failed(6 分 24 秒)**。`slow` の 18 構成の生きた数え(`tests/engine/rights -m slow`): 18 passed(▲ の印なし)。byte-check は親が回す。
