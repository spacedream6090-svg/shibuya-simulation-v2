# 第 1 期 1-4 規則の表とつなぎの台帳(CP10・CP5-5・PlanSpec)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `1-4/rules-bridges`(HEAD `136fdbb`=T0 と 1-3 を取り込んだ後)。commit は親。
- 正: [口の約束 1-4](../../../../design/v2-foundation-contracts-2026-10-13.md)(〔決定〕つなぎの台帳は docs(git)に置く・不応期 11 種と起床条件のクラスは「T3 で外す」)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) §1 の 3・第 1 期 1-4・第 2 期 2-0・[決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §1-12・§4-5 CP10・CP5-5・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3・§4-2 の 2・規則の中身は [R-106](../../../../research/v2-r106-rights-institutions-tax-credit.md)(親検収済)と [W7 の一次確認](../../../../research/v2-w7-law-primary-check-research.md)(等級 A)・先例は [R-113](../../../../research/v2-r113-e1-foundations-existing-implementations.md) §4。
- 経緯: 1 回目の実装(3 形・172 行)→ 親の判断 第334(第 4 形=docstring の見出しを見出し単位で・246 行)→ 独立検収 [review.md](review.md)(条件つき受入)→ 親の判断で M1・M2・低 7 件を直した(第 5・6 形と文書の行 4 つ・273 行・`run_kind` を `cli.run` で決める・§9)。本書は直した後の形で書く。
- 数は実測。生の出力(テープ・side の JSON)は git の外の作業用の置き場(作業木の `_bc/`)に置いた。比べた結果と道具だけをこのフォルダに置く。
- 道具(`tools/`・使い方は各ファイルの冒頭・絶対パスなし): `build_ledger.py`(台帳の最初の中身を作る・`--check` で同じ中身になるか)・`scan_expedients.py`(6 形の宣言の一覧)・`count_other_forms.py`(6 形の外の書き方を数える)・`manifest_check_r14.py`(10f の manifest の 2 つの側を比べる・e13 の道具の写し)・`probe_r14.py`(系ごとの指紋・e13 の道具の写し)。byte-check と 2 日のランは既存の道具(`10e/byte_check_10e.py`・`10e/two_day_check_act.py`)。

## 0. 結論

- **規則の表**(`engine/rules/table.py`+`docs/design/rules-table.json`): `Rule`(凍結・出典と版は必須)と読み口 `Rules.get(id, asof)`(asof の日に効いている版)。中身は実在の規則 3 行(消費税の標準税率・東京都の最低賃金・深夜の酒類提供の住居集合地域での禁止)。**読み手は作っていない**(表を import するのは manifest・日次の記録・組み立ての読み込みの検査の 3 か所だけ=AST の試験)。表の sha は `e26d43b4207b5301`。
- **つなぎの台帳**(`engine/bridging/ledger.py`+`docs/design/bridging-ledger.json`): **273 行(全部 active)**。コードの expedient の宣言 241 行(6 形)と、文書で宣言したつなぎ 32 行。口の約束の 16 件(計画 §1 の 3 の 9 件・#88 の 6 件・西武の 1 部屋)・不応期 11 種と起床条件のクラス(T3)・W16 の弱点 3 件・世界過程の宣言 18 本と conf 宣言つきフォールバック台帳 5 行・「繋ぎ」と明記した 3 か所・規則の表に結ぶ直書きの最低賃金を含む。
- **`bridges_count`(273)は宣言の行の数で、一意のつなぎの数ではない**。同じ近似をコードと文書の 2 か所以上で宣言した行がある(§3-3 の重なりの一覧)。重なる行の id を行に持たせ、一意の数も出すのは 2-0(計器の器)の課題。
- **コードとの 1 対 1**(`engine/bridging/scan.py`): 6 形(A `conf="expedient"` 0・B `expedients=[…]` 139・C docstring の `expedient:` の段落 5・D docstring の `expedient(…)` の見出し 74・E 世界過程と PlanSpec の `mechanism=False`+`repayment_due` 18・F フォールバック台帳の行 5)を数え、台帳の active の行と 1 対 1(欠け 0・余り 0)。負の対照(6 形とも足す・書き換える・台帳の行を消す・removed にする・見出しの項を足す)で落ちる。**1 対 1 は 6 形の中だけ**(6 形の外の書き方は §4-3)。
- **manifest**: 末尾に `rules_version`・`run_kind`・`bridges_version`(台帳の sha `470a7a543f5c5b61`)。`bridges_count` は null → 273。日次の記録(TM9 の行)にも `bridges_count` と `rules_version`。凍結の表(鍵 108 → 111・設定の節の sha)を更新した。
- **`run_kind`(検収 M2)**: `cli.run` が決める=試験の中は `test`・CLI の既定と違う腕の引数が 1 つでもあれば `arm`・ほかは `reproduction`。`cli.main` もこの決め方を使う。`run_day` を直に呼ぶランは null(決めていない)。manifest の 7 本では既定 v3 の 2 本が `reproduction`、帰無腕・記憶+関係・古典+記憶+関係の 5 本が `arm`。
- **結果不変**: 1 回目は byte-check 19/19 構成で 25 欄とも HEAD と同じ・2 日のラン・系ごとの指紋も同じ。検収の後の直しのあとは、親の指示どおり byte-check 4 構成(4/4 で 25 欄とも同じ)と manifest の 7 本(既存の欄が全部同じ・動いたのは `bridges_count` の null → 273 だけ)を回し直した(§6)。
- 仮採用は §8 の 14 件。試験は §7。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/rules/__init__.py`・`table.py`(新規) | `Source`・`Rule`(凍結の dataclass・slots)・`Rules`(読むだけ・`__setattr__` の守り・表は `MappingProxyType`)・`RuleNotInForce`・`load`・`default_rules`・`rules_version`・`canonical_sha` |
| `docs/design/rules-table.json`(新規・git) | 規則 3 行(§2) |
| `src/shibuya/engine/bridging/__init__.py`・`ledger.py`(新規) | `Bridge`(凍結・`remove_basis` 3 値・`code_at`・`rule_id`)・`BridgeLedger`(読むだけ・active の行だけ数えて突き合わせる)・`PLAN_STAGES`(外す段の閉じた表)・`load`(壊れた JSON・欠けた欄・知らない欄は `ValueError`)・`default_ledger`・`bridges_count`・`bridges_version`・`code_mismatch` |
| `src/shibuya/engine/bridging/scan.py`(新規) | 6 形の宣言を数える(A〜E は AST・F はフォールバック台帳を実行して読む。`Declaration`・`declared_in_of`・`scan_source`・`scan_package`・`fallback_declarations`・`count_by_form`) |
| `docs/design/bridging-ledger.json`(新規・git) | 台帳 273 行(§3) |
| `src/shibuya/engine/run_kind.py`(新規) | ランの種類の名と規則(`decide`・`resolve`・`check`・`in_test`)。規則そのものを expedient の段落で宣言し台帳に載せた(`BR-RUN-KIND-CLI-ARMS`) |
| `src/shibuya/engine/run.py` | `RunResult.run_kind`(既定 `None`=決めていない)・manifest の末尾の欄(`bridges_count` を null から件数に・`rules_version`・`run_kind`・`bridges_version`) |
| `src/shibuya/engine/systems/state_io.py` | 日次の記録の `bridges_count`(null から件数に)と `rules_version`(`events` の前) |
| `src/shibuya/engine/systems/build.py` | 組み立ての始めに台帳と表を 1 回読む(壊れていればランの始めで落ちる=検収 L10。読むだけ) |
| `src/shibuya/engine/manifest_sections.py` | 節の表に `rules_version`・`run_kind`・`bridges_version`(設定) |
| `src/shibuya/cli.py` | `cli.run` がランの種類を決める(`NON_ARM_RUN_KWARGS`・`arm_baseline`・`run_arms`・`_arm_norm`)。結果に置くだけ=`run_day` の引数・設定の指紋には入れない。`main` は HEAD の形のまま(種類は `run` が決める) |
| `tests/engine/rules/`・`tests/engine/bridging/`(新規) | §7 |
| `tests/engine/time/manifest_keys_frozen.json` | 末尾に `rules_version`・`run_kind`・`bridges_version`(凍結の表の増えた分) |
| `tests/engine/test_env_and_sections_10f.py` | 末尾の欄の表に `R14_KEYS`(3 つ)・設定の節の sha `d16f26e6…` → `d8a9a21d…`(凍結の表の増えた分) |
| `tests/engine/time/test_t0_tm9_fields.py` | **発注の編集してよい一覧の外**: `bridges_count is None` を件数に・「TM9 の 4 つが末尾」を「TM9 の 4 つが続きの並び・その後ろに 1-4 の 3 つ」に。発注が「T0 で null にした欄を件数に」と決めているので、直さないと落ちる(§8 の 9・検収役は認めてよいと読む) |

## 2. 規則の表(3 行・出典と版)

| id | kind | asof(効く最初の日) | 値 | 出典(条・版) |
|---|---|---|---|---|
| `consumption_tax.standard_rate` | machine | 2019-10-01 | 国 7.8%・地方消費税 22/78・合計 10% | 消費税法 29 条 1 号(`363AC0000000108`・版 2026-10-01)・地方税法 72 条の 83(`325AC0000000226`・版 2026-10-01)。R-106 §3-1・§0-2 |
| `minimum_wage.tokyo` | machine | 2026-10-01 | 1,280 円/時・東京都 | 東京労働局 報道発表(2026-09-30・R-106 #17)・最低賃金法 4 条・14 条(`334AC0000000137`・版 2025-06-01) |
| `late_night_alcohol.residential_ban` | human | 2025-11-28 | 住居集合地域で 00:00〜06:00 の深夜酒類提供飲食店営業を禁止 | 風営法 33 条 1 項(`323AC0000000122`・版 2025-11-28)・都の風営法施行条例 15 条(最終改正 令和 2 年条例第 48 号・W7 の一次確認で逐語一致)。`applies_to` は `plan.law_cap_key == 'shinya_shurui'`(W7 の PlanSpec の列) |

- 写し検査を試験にした: e-Gov の法令 ID と版が R-106 §0-2 の表の同じ行にあること・URL が R-106 か W7 の答申にあること・条例 15 条の逐語が W7 にあること(検収役も全部一致を確かめた)。
- `asof` の決め方: 消費税は税率 10% の施行日(R-106 §6-1 の例)。最低賃金は効力の日。深夜酒類は施行の初日が答申に無いので、読んだ法の版(2025-11-28)を下限にした(仮採用・§8 の 2)。
- 世界の時点 2026-07-13 の最低賃金 1,226 円(2025-10-03〜)は R-106 で △(報道)なので表に入れていない(親の判断 第334 で認める=4-2)。`Rules.get("minimum_wage.tokyo", "2026-07-13")` は `RuleNotInForce`。コードの直書き `economy/anchors.py` の `MIN_WAGE_HOURLY = 1_226` は台帳の行 `BR-MIN-WAGE-HOURLY-1226`(外す段 4-2・`rule_id: minimum_wage.tokyo`)にした(検収 L7)。
- 表の sha は正規化した JSON(鍵の昇順・空白なし)の sha256 の先頭 16 桁。改行(CRLF/LF)と字下げに左右されない(作業木の CRLF の事故=第330 の型を避ける)。行の順では変わる(文書の sha)。

## 3. つなぎの台帳

### 3-1. 行の形

`Bridge` の欄は口の約束の `id`・`what`・`why`・`remove_at`・`declared_in`・`conf` と発注の `since`・`status` に、3 つを足した(仮採用・§8 の 3): `remove_basis`・`code_at`(文書で宣言した行の、関わるコードの場所)・`rule_id`(規則の表の行に結ぶ直書きの係数の行=検収 L7)。

- `remove_basis`: `plan`=計画・決定・回答の文に外す段が書いてある(47 行)/ `declared`=コードの宣言の返済期限(`repayment_due`)が「エージェントへ」と書く行き先を 6-6 ②に読み替えた(8 行)/ `inferred`=実装役が段を当てた(218 行・仮採用)。
- `remove_at` は計画の段の番号の閉じた表(`PLAN_STAGES`): `1-0`〜`1-10`・`1-0b`・`1-8b`・`2-0`・`2-0b`・`2-1`〜`2-4`・`2-3b`・`3-1`〜`3-5`・`4-1`・`4-1b`・`4-2`・`4-3`・`5-0`〜`5-6`(空間の段 0〜6)・`6-1`〜`6-7`・`7`(第 7 期)・`T1`〜`T4`。**`7` は「外す段が計画に無い=主張の前に感度試験で駆動しないことを示す」**(CLAUDE.md §4)の意味で使った。計画の文書と突き合わせる試験は無い(手の表・限界 L9)。
- `declared_in`: コードの宣言は `src/<道筋>#<形>:<鍵>`(A〜D は中身の sha256 の先頭 8 桁・E は `id`・F は `<subject_id>|<plan_spec_id>`=scan.py が同じ文字列を作る)。文書の宣言は `docs/<道筋> §…`。
- `status`: `active` の行だけを数え、突き合わせる(検収 L2)。外したつなぎは `removed` で残してよい。`removed` の行がまだコードにある宣言を指すと、その宣言は「台帳に行が無い」で落ちる(試験)。
- `since`: 日付の形だけを見る(検収 L3)。今の行は全部 2026-10-14(台帳に載せた日)。
- id: build の段の宣言は `W<n>#<i>`=**C8 の感度の台帳(`docs/bench/c8/sensitivity_v1.md`)の D-44 の行の番号と同じ**(123 行。試験で、D-44 の切り詰めた文が台帳の `what` の頭に合うことを全部確かめた)。W17 v1 の構築(`sched/w17_schedule.py`・今の資産は v2)は `W17v1#<i>`。第 4 形は `HD-<モジュール>-<見出しの文の sha8>`(検収 L5=見出しを足しても後ろの id がずれない)。第 5 形は `PR-<id>`・第 6 形は `FB-<subject_id>`。ほかは `BR-…`。

### 3-2. 中身(273 行)

| 群 | 行 | 外す段 | 根拠 |
|---|---|---|---|
| 計画 §1 の 3 の 9 件 | `BR-W17-IO-SLEEP`(6-2)・`BR-E4-EXIT-VANISH`(6-2)・`BR-ATTENDANCE-LOTTERY`(6-6)・`BR-K9-MONDAY`(3-1)・`BR-SIGNAGE-FICTION`(7)・`BR-DELIVERY-INBOUND`(6-6)・`BR-THINK-TIME-TABLE`(6-7)・`BR-THINK-ALPHA`(6-7)・`BR-RENT-BLANK`(4-2) | 括弧内 | 看板(7)と家賃(4-2)は inferred(親の判断 第334 で認める)・ほかは plan |
| #88 の 6 件 | `BR-W18-X`(7)・`BR-W12-HOLIDAY-GT-WEEKDAY`(2-3b)・`BR-W11-SHINSEN-EXIT`(2-3b)・`BR-SHADOW-NEAREST-DAY`(2-3)・`BR-WEATHER-STRATUM-WIDEN`(7)・`W9#5`(2-3) | 括弧内 | 2-3b の 2 件は plan・ほかは inferred。4〜6 はコードの宣言の行をそのまま #88 の行にした |
| 西武渋谷店の 1 部屋 | `BR-SEIBU-ONE-ROOM` | 7 | inferred(図が入るまで外せない。作るのは空間の段 2・西武の規約の「営利の準備」の禁止を `why` に) |
| 不応期 11 種 | `BR-REFRACTORY-<条件>` ×11(会話ターン・睡眠中は conf=mechanism) | T3 | plan(回答 10-13b §4-2 の 2) |
| 起床条件のクラス | `BR-WAKE-CONDITION-CLASS` | T3 | plan |
| W16 の弱点 3 件 | `BR-W16-REPLICATED-108142`・`BR-W16-VISITOR-COUNT-BASIS`・`BR-W16-NO-TRANSFER-ONLY` | 4-1 | plan(計画 第 4 期の注=段 10) |
| 「繋ぎ」と明記した 3 か所〔検収 M1 (c)〕 | `BR-START-CELL-OUTSIDE-HOME`(`agents/population.py`・6-2)・`BR-MOCK-SCHEDULE-POPULATION`(`engine/run.py` の `_schedule_with_population`・6-2)・`BR-MOCK-ACTION-ANCHOR`(`llm/mock.py`・6-1) | 括弧内 | inferred。文書の行(`declared_in` は review.md の M1・`code_at` にコードの場所) |
| 規則の表に結ぶ直書き〔検収 L7〕 | `BR-MIN-WAGE-HOURLY-1226`(`economy/anchors.py` の `MIN_WAGE_HOURLY = 1_226`・`rule_id: minimum_wage.tokyo`) | 4-2 | plan(口の約束 1-4 の約束 (1)) |
| build の段の宣言 137 行(第 2 形) | W1〜W20(W0 は 0 個)と W17 v1 | 段ごと(下) | W16(4-1)・W12 の 4〜8(2-3b)・W17#2(3-1=K9)は plan・ほかは inferred(W7 → 4-2・W17 → 6-2 は親の判断 第334 で認める) |
| そのほかのコードの宣言 7 行 | `environment.py` の 2 つ(上の #88)・docstring 5 つ(`street_grid` 5-6・`core/rng` 7・`economy/ledger` 2-1・`manifest/schema` 7・`run_kind` 3-3) | 括弧内 | run_kind は plan(計画 3-3)・ほかは inferred |
| 第 4 形(docstring の見出し)74 行 | `HD-…`(§4-4) | ファイルごと | 全部 inferred(当てられないものは 7) |
| 第 5 形(世界過程と PlanSpec の宣言)18 行〔検収 M1 (a)〕 | `PR-<id>`(世界過程 16・PlanSpec 2=`plan.opening_hours`・`plan.road_works`) | 返済期限から | 「エージェントへ」と書く 4 行(鉄道・開閉店・断面交通・ホテル)は 6-6 ②=declared。データの取得待ちの 14 行は話題で当てた=inferred(多くは 6-6 ②・棚の補充 2-1・席 5-2・電力と水 7・営業時間表 4-2) |
| 第 6 形(フォールバック台帳)5 行〔検収 M1 (b)〕 | `FB-rail_operation_static`・`FB-store_opening`・`FB-vehicle_cross_section`・`FB-hotel_room_inventory`・`FB-large_event` | 6-6 | 4 行は declared・`large_event` は inferred |

build の段ごとの外す段(当てた理由は台帳の `why`): W1・W3・W11 → 5-1 / W2・W8・W15・W6#2・W10#8 → 5-3 / W4・W5 → 5-2 / W6#1 → 4-1 / W6#3 → 5-0 / W7 → 4-2 / W9#1〜4・W13・W14・W18〜W20 → 7 / W9#5 → 2-3 / W10 → 5-6 / W12#1〜3 → 4-1・#4〜8 → 2-3b / W16 → 4-1 / W17(#2 以外)と W17 v1 → 6-2 / W17#2 → 3-1(K9)。

### 3-3. 外す段の分布と重なり(active 273 行)

| 外す段 | 行 | plan | declared | inferred | うち第 4 形 | うち第 5・6 形 |
|---|---|---|---|---|---|---|
| 1-5 | 1 | 0 | 0 | 1 | 1 | 0 |
| 1-9 | 1 | 0 | 0 | 1 | 1 | 0 |
| 2-1 | 9 | 0 | 0 | 9 | 7 | 1 |
| 2-3 | 2 | 0 | 0 | 2 | 0 | 0 |
| 2-3b | 8 | 7 | 0 | 1 | 1 | 0 |
| 3-1 | 3 | 2 | 0 | 1 | 1 | 0 |
| 3-2 | 1 | 0 | 0 | 1 | 1 | 0 |
| 3-3 | 1 | 1 | 0 | 0 | 0 | 0 |
| 4-1 | 23 | 18 | 0 | 5 | 1 | 0 |
| 4-2 | 18 | 1 | 0 | 17 | 2 | 1 |
| 5-0 | 1 | 0 | 0 | 1 | 0 | 0 |
| 5-1 | 15 | 0 | 0 | 15 | 4 | 0 |
| 5-2 | 6 | 0 | 0 | 6 | 1 | 1 |
| 5-3 | 33 | 0 | 0 | 33 | 8 | 0 |
| 5-6 | 14 | 0 | 0 | 14 | 3 | 0 |
| 6-1 | 5 | 0 | 0 | 5 | 4 | 0 |
| 6-2 | 28 | 2 | 0 | 26 | 5 | 0 |
| 6-5 | 1 | 0 | 0 | 1 | 1 | 0 |
| 6-6 | 25 | 2 | 8 | 15 | 4 | 19 |
| 6-7 | 3 | 2 | 0 | 1 | 1 | 0 |
| 7 | 60 | 0 | 0 | 60 | 25 | 1 |
| T3 | 15 | 12 | 0 | 3 | 3 | 0 |
| 計 | 273 | 47 | 8 | 218 | 74 | 23 |

- conf: expedient 271・mechanism 2(不応期の会話ターンと睡眠中)。
- **`bridges_count` は宣言の行の数で、一意のつなぎの数ではない**(台帳の `note` にも 1 行書いた)。重なる行(同じ近似を 2 か所以上で宣言した行)は次のとおり。外すときは同じ段で両方を消すので、件数の増減(計器の向き)は正しく動く。**一意の数を出すため、行に重なる行の id(例 `overlaps`)を持たせるのは 2-0(計器の器)の課題**:
  - 第 2 形と第 4 形(同じファイルの `StageResult.expedients` の要旨の写し)7 組: `w7_planspec`・`w8_visibility`・`w10_noise`・`w13_weather`・`w14_signage`・`w15_cell_static`・`sched/trial` の見出しの行 ↔ 同じ段の `W<n>#<i>` の行。
  - 文書の行とコードの行: `BR-K9-MONDAY` ↔ `W17#2`(1 日モード=月曜 d0 のみ)/ `BR-E4-EXIT-VANISH`・`BR-ATTENDANCE-LOTTERY` ↔ `HD-engine.presence-…`(E4・E6 の項)/ `BR-W12-HOLIDAY-GT-WEEKDAY` ↔ `W12#4`〜`#8`(等間隔のダイヤ)/ `BR-W17-IO-SLEEP` ↔ `HD-engine.presence-…` と W17 の行 / `BR-DELIVERY-INBOUND` ↔ `PR-delivery_inbound` と `HD-engine.processes.goods_flow-…` / `BR-START-CELL-OUTSIDE-HOME` ↔ `BR-MOCK-SCHEDULE-POPULATION`(同じ規約の 2 か所)。
  - 第 5 形と第 6 形: フォールバック台帳の 5 行 `FB-…` ↔ 同じ過程の `PR-…`(鉄道・開閉店・断面交通・ホテル・大きな催し)。
  - 第 5 形と第 4 形: 世界過程の宣言 ↔ 実装のモジュールの見出し(`goods_flow`・`civic`・`logistics`・`traffic`・`rail`・`opening`)の項の一部。`PR-plan.opening_hours` ↔ `W7#1`(カテゴリ既定の営業時間)。
  - #88 の 4〜6 はコードの宣言の行と同じ行にした(この組だけは二重に数えていない)。
- 来街者の口座と現金の表示(2-1 のつなぎ)は発注どおり載せていない。

## 4. コードの expedient との対応

### 4-1. 数え方(`engine/bridging/scan.py`)

| 形 | 数えるもの | 件数 |
|---|---|---|
| A `conf` | キーワード引数 `conf="expedient"`(属性名 `EXPEDIENT` も)・代入 `conf = "expedient"`(`x.conf` も)・辞書 `{"conf": "expedient"}` | 0 |
| B `expedients` | `expedients=[…]` の要素 1 つずつ・`x.expedients.append/extend`・`x.expedients += […]`・モジュールの表 `EXPEDIENTS`/`*_EXPEDIENTS`(リストかタプルの文字の並び。`expedients=list(EXPEDIENTS)` はこの表を数える=二重に数えない) | 139 |
| C `docstring` | モジュール・クラス・関数の docstring の行頭が `expedient:`(全角のコロンも)の段落(空行まで) | 5 |
| D `heading`〔親の判断 第334〕 | docstring の、1 行まるごとが `expedient(…)` の見出し(全角のかっこも・閉じかっこで終わる・後ろのコロンは許す)。**見出し 1 つで 1 件**。下の項(空行までの `- ` で始まる行)の数を `items` に持つ | 74(71 ファイル・項 338) |
| E `process`〔検収 M1 (a)〕 | 呼び出しの引数に `mechanism=False` と `repayment_due=` の両方があるもの(`world/processes/first_batch.py` の `WorldProcess(...)` 16・`PlanSpec(...)` 2)。成長の宣言・状態の欄の `mechanism=False`(`repayment_due` が無い)は数えない | 18 |
| F `fallback`〔検収 M1 (b)〕 | `first_batch.build_registry().fallback_ledger()`(CLAUDE.md §3「エンジン規則でつなぐ(conf 宣言つき・カバー率を台帳へ)」の台帳=executor が engine_rule の行)を**実行して読む** | 5 |
| 計 | | 241 |

B の 139 の内訳: build の段 137(W1 3・W2 4・W3 3・W4 2・W5 2・W6 3・W7 13・W8 9・W9 5・W10 11・W11 5・W12 8・W13 8・W14 7・W15 10・W16 15・W17 6(`sched/trial.py`)・W17 v1 14(`sched/w17_schedule.py`)・W18 5・W19 2・W20 2)と `engine/processes/environment.py` の `WEATHER_EXPEDIENTS` 2。W17 v1 を除く 123 は `data/world/v2/build_manifest.json` の 123 行・C8 の D-44 の 123 行と同じ数。C の 5: `build/field/street_grid.py`・`core/rng.py`・`economy/ledger.py`・`manifest/schema.py`・`engine/run_kind.py`(1-4 で足した)。

D の 74 は、行頭だけを見るゆるい数え方の 75 から 1 つ少ない。違うのは `engine/arbiter.py` の 40 行目「expedient(感度試験必須)」と明記)。」で、`T_MAX_TICKS` の項の文の中の折り返し(見出しでない)。その下の 4 項は、ゆるい数え方では前の見出し「expedient(本モジュール分)」の項と二重に数えていた(342 − 4 = 338)。

### 4-2. 対応表と試験

- 対応: コードの宣言 241 個 ↔ `declared_in` が `src/…` の active の行 241 行(1 対 1・欠け 0・余り 0)。文書の行 32 行はコードの宣言を持たない(許す)。
- 中身の同定: A〜D は中身(文字列・f 文字列や式は `ast.unparse` の文字列・名前は同じファイルの 1 回だけの代入の右辺・見出しは見出しの行の文)の sha256 の先頭 8 桁。E は `id`、F は `<subject_id>|<plan_spec_id>`。**中身を書き換えると台帳の行も直す**(試験が落ちて知らせる)。行の順や行番号は見ない(§8 の 11)。
- 第 4 形の行: `what` は「<ファイル> の docstring の見出し「<見出し>」の下の項 <n> 個」(項 0 は「項の形でなく段落の文」と添える)。試験が `what` の見出しと項の数が今のコードと合うことを見る(項が増えると、同定は同じでも試験が落ちる)。
- 第 5・6 形の行: `what` に executor・感度試験の id・返済期限(`repayment_due`)をそのまま写した。試験が、第 5 形の数が世界の台帳の `mechanism=False` の過程と PlanSpec の数と同じこと・返済期限が `what` にあること・「エージェント」を書く返済期限の行だけが declared で 6-6 になることを見る。
- 台帳の `what`: 文字列の宣言はそのまま写した(試験で確かめる)。f 文字列と式の 11 個のうち 10 個は、構築したときの値(`build_manifest.json` の文)を写した。W17 v1 の 1 個(`W17v1#5`)は資産に無いので式の文字列のまま。
- 試験の負の対照: (a) `conf="expedient"` の関数を足す(ほか 4 つの書き方も数える・`conf="mechanism"` は数えない) (b) W10 の `expedients` の並びに 1 項を足す(append・extend・`+=`・表も数える) (c) docstring に `expedient:` の段落を足す(行頭でない `(expedient: …)` と `未リサーチ(expedient)` は数えない) (d) 宣言の中身を書き換える・台帳の行を消す (e) docstring に `expedient(…)` の見出しを足す(全角・関数の docstring・項 0 も 1 件。折り返しの `expedient(…)…。` は数えない) (f) 見出しの下に項を足す (g) `mechanism=False` と `repayment_due=` の世界過程を足す(`mechanism=True`・成長の宣言は数えない) (h) フォールバック台帳に行を足す (i) 行を `removed` にする(まだコードにある宣言は落ちる・宣言を消した後は通る)。どれも試験が落ちる。

### 4-3. 6 形の外の書き方(1 対 1 の外)

`tools/count_other_forms.py` で数えた(`src/shibuya`・`engine/bridging/` を除く)。

| 書き方 | 数 | 扱い |
|---|---|---|
| expedient を含む行 | 689 行(121 ファイル) | 内訳は下 |
| うち `#` で始まる注 | 277 行 | 数えていない(数えると数百行増える=親の判断待ち §8 の 13) |
| 6 形の宣言を 1 つも持たないファイル | 31 本(expedient を含む 121 本のうち) | 例 `engine/chooser.py`(習慣の確率 p_h・走査の揺らぎ τ)・`engine/relations.py`・`engine/store_memory.py`・`agents/weekly.py`(`#: expedient(自前の写像・登録簿 §8 D-62)`)・`build/geo/poi_class.py`。このうち `agents/population.py`・`llm/mock.py` は「繋ぎ」の文書の行で台帳に入れた(§3-2) |
| `未リサーチ(expedient)` の注記 | 17 | 数えていない |
| 行頭でない `(expedient: …)` | 5 | 数えていない(例 `llm/__init__.py` の「粗いトークン数見積り(expedient: …)」) |
| `mechanism=False` | 46 か所 | **第 5 形の 18(`world/processes/first_batch.py`=世界過程と PlanSpec の宣言・返済期限つき)は 1 対 1 に入れた**。残りは状態の欄と成長の宣言のタグ(`agents/state.py` 16・`world/state.py` 5・`engine/events/log.py`・`engine/growth_decl.py`・`perception/state.py`・`world/processes/actual_log.py` 各 1)と scan.py 自身の説明 3 で、返済期限を持たない=数えていない |
| `tag="expedient"` の契約の行 | 6 | 数えていない(`llm/contract.py`・LLM の契約の行のタグ) |

- **1 対 1 は 6 形の中だけ**。上の書き方の近似は台帳に行が無い(見出しや段落に書き直せば第 3・4 形として入る)。
- 〔1 回目の記録の訂正〕「`mechanism=False` の 44 欄は成長の宣言(`core/soa.py`)のタグ」は誤り。数は 46(scan.py の 3 を含む)で、そのうち 18 は世界過程と PlanSpec の宣言(返済期限つき)=第 5 形にした。

### 4-4. 第 4 形の 74 行(外す段は全部 inferred=仮採用)

外す段の理由は台帳の各行の `why`。当てられないもの(表し方・見積り・自前の規約で、置き換える段が計画に無い)は `7`。行番号はこの時点の写し(台帳の同定には使っていない)。見出しの行の `remove_at` は代表の項の段で、項のすべてがその段で外れるとは限らない(例 `HD-engine.processes.opening-…` の 1-5 は 1 項目めの担当の丸振りだけに合う=限界 L6)。

| id | ファイル(`src/shibuya/` の下)・行 | 見出し | 項 | 外す段 |
|---|---|---|---|---|
| `HD-agents.schedule-1af925f4` | `agents/schedule.py`:22 | expedient(本モジュール分) | 3 | 3-1 |
| `HD-agents.state-1af925f4` | `agents/state.py`:20 | expedient(本モジュール分) | 16 | 7 |
| `HD-build.field.road_names-83cc3004` | `build/field/road_names.py`:40 | expedient(すべて感度試験対象・notes に件数) | 4 | 5-6 |
| `HD-build.field.w10_noise-b7a51040` | `build/field/w10_noise.py`:36 | expedient(すべて感度試験対象) | 9 | 5-6 |
| `HD-build.field.w13_weather-06bce03e` | `build/field/w13_weather.py`:21 | expedient(すべて宣言) | 4 | 7 |
| `HD-build.field.w7_planspec-e861a776` | `build/field/w7_planspec.py`:15 | expedient(全文は ``EXPEDIENTS``=段階ヘッダに載る台帳。ここは要旨) | 7 | 4-2 |
| `HD-build.lang.common-bdcdae84` | `build/lang/common.py`:14 | expedient(本モジュールぶん・登録簿へ) | 5 | 7 |
| `HD-build.lang.w14_signage-cb122857` | `build/lang/w14_signage.py`:17 | expedient(本段階ぶん・登録簿へ) | 6 | 7 |
| `HD-build.lang.w15_cell_static-cb122857` | `build/lang/w15_cell_static.py`:31 | expedient(本段階ぶん・登録簿へ) | 4 | 5-3 |
| `HD-build.sched.pool_facts-f3c2f1ba` | `build/sched/pool_facts.py`:18 | expedient(本モジュール分・登録簿へ) | 2 | 6-2 |
| `HD-build.sched.trial-0ab55bb5` | `build/sched/trial.py`:36 | expedient(§8 登録簿へ・切替口つき) | 8 | 6-2 |
| `HD-build.sched.vocab-f3c2f1ba` | `build/sched/vocab.py`:13 | expedient(本モジュール分・登録簿へ) | 4 | 6-2 |
| `HD-build.vis.w8_visibility-b7a51040` | `build/vis/w8_visibility.py`:24 | expedient(すべて感度試験対象) | 9 | 5-3 |
| `HD-core.growth-1af925f4` | `core/growth.py`:41 | expedient(本モジュール分) | 3 | 7 |
| `HD-core.soa-1af925f4` | `core/soa.py`:26 | expedient(本モジュール分) | 2 | 7 |
| `HD-core.types-1af925f4` | `core/types.py`:20 | expedient(本モジュール分) | 2 | 7 |
| `HD-economy.anchors-1af925f4` | `economy/anchors.py`:19 | expedient(本モジュール分) | 4 | 2-1 |
| `HD-economy.census-1af925f4` | `economy/census.py`:39 | expedient(本モジュール分) | 2 | 2-1 |
| `HD-economy.checks-1af925f4` | `economy/checks.py`:40 | expedient(本モジュール分) | 2 | 2-1 |
| `HD-economy.entry_capital-cf8155f5` | `economy/entry_capital.py`:45 | expedient(本モジュール分・登録簿 §8 の C5 経済節へ登録) | 5 | 2-1 |
| `HD-economy.goods-1af925f4` | `economy/goods.py`:29 | expedient(本モジュール分) | 7 | 2-1 |
| `HD-economy.ledger-1af925f4` | `economy/ledger.py`:35 | expedient(本モジュール分) | 4 | 2-1 |
| `HD-economy.pricing-1af925f4` | `economy/pricing.py`:20 | expedient(本モジュール分) | 4 | 2-1 |
| `HD-engine.activity-090e5c85` | `engine/activity.py`:26 | expedient(本モジュール分・アジェンダ §5 に行) | 5 | 6-1 |
| `HD-engine.arbiter-1af925f4` | `engine/arbiter.py`:37 | expedient(本モジュール分) | 5 | T3 |
| `HD-engine.change_detect-1af925f4` | `engine/change_detect.py`:31 | expedient(本モジュール分) | 4 | 7 |
| `HD-engine.classical-4000a748` | `engine/classical.py`:30 | expedient(宣言・問いつき) | 6 | 7 |
| `HD-engine.commit-1af925f4` | `engine/commit.py`:22 | expedient(本モジュール分) | 4 | 7 |
| `HD-engine.conversation-1af925f4` | `engine/conversation.py`:23 | expedient(本モジュール分) | 7 | 5-3 |
| `HD-engine.energy-cc73b60c` | `engine/energy.py`:50 | expedient(本モジュール分・宣言) | 1 | 7 |
| `HD-engine.familiarity-a8af6821` | `engine/familiarity.py`:52 | expedient(宣言) | 0 | 6-5 |
| `HD-engine.geometry-1af925f4` | `engine/geometry.py`:33 | expedient(本モジュール分) | 6 | 5-1 |
| `HD-engine.growth_decl-1af925f4` | `engine/growth_decl.py`:14 | expedient(本モジュール分) | 3 | 7 |
| `HD-engine.intent-0c69afbc` | `engine/intent.py`:48 | expedient(宣言・アジェンダ §3) | 11 | 6-6 |
| `HD-engine.ledger_api-1af925f4` | `engine/ledger_api.py`:25 | expedient(本モジュール分) | 2 | 1-9 |
| `HD-engine.llm_bridge-1af925f4` | `engine/llm_bridge.py`:68 | expedient(本モジュール分) | 4 | 7 |
| `HD-engine.poi_target-a8af6821` | `engine/poi_target.py`:52 | expedient(宣言) | 4 | 5-3 |
| `HD-engine.presence-b560bcbc` | `engine/presence.py`:26 | expedient(本モジュール分・実装計画書 §8「D-66/計画実行層(第1段)」が正典) | 9 | 6-2 |
| `HD-engine.processes.civic-fe8b67d5` | `engine/processes/civic.py`:18 | expedient(本モジュール分・全て「返済対象」) | 6 | 6-6 |
| `HD-engine.processes.crowd-1af925f4` | `engine/processes/crowd.py`:27 | expedient(本モジュール分) | 6 | 5-2 |
| `HD-engine.processes.environment-1af925f4` | `engine/processes/environment.py`:23 | expedient(本モジュール分) | 5 | 7 |
| `HD-engine.processes.goods_flow-fe8b67d5` | `engine/processes/goods_flow.py`:29 | expedient(本モジュール分・全て「返済対象」) | 8 | 6-6 |
| `HD-engine.processes.logistics-fe8b67d5` | `engine/processes/logistics.py`:9 | expedient(本モジュール分・全て「返済対象」) | 4 | 6-6 |
| `HD-engine.processes.opening-1af925f4` | `engine/processes/opening.py`:27 | expedient(本モジュール分) | 4 | 1-5 |
| `HD-engine.processes.rail-1af925f4` | `engine/processes/rail.py`:55 | expedient(本モジュール分) | 6 | 2-3b |
| `HD-engine.processes.salient-1af925f4` | `engine/processes/salient.py`:31 | expedient(本モジュール分) | 5 | 7 |
| `HD-engine.processes.traffic-1af925f4` | `engine/processes/traffic.py`:23 | expedient(本モジュール分) | 3 | 5-6 |
| `HD-engine.resolve-1af925f4` | `engine/resolve.py`:28 | expedient(本モジュール分) | 6 | 5-1 |
| `HD-engine.resolve-b4604883` | `engine/resolve.py`:297 | expedient(自前規約・設計書に丸めの規定は無い) | 0 | T3 |
| `HD-engine.resolve-fd5772ea` | `engine/resolve.py`:658 | expedient(登録簿 §8 D-62) | 2 | 6-2 |
| `HD-engine.resolve-2dd500ab` | `engine/resolve.py`:837 | expedient(自前規約) | 1 | T3 |
| `HD-engine.run-1af925f4` | `engine/run.py`:33 | expedient(本モジュール分) | 8 | 6-7 |
| `HD-engine.scheduler-1af925f4` | `engine/scheduler.py`:34 | expedient(本モジュール分) | 3 | 3-2 |
| `HD-llm.__init__-fa88de99` | `llm/__init__.py`:33 | expedient(本パッケージ分) | 2 | 7 |
| `HD-llm.contract-1af925f4` | `llm/contract.py`:24 | expedient(本モジュール分) | 5 | 6-1 |
| `HD-llm.fleet-853ae8b1` | `llm/fleet.py`:59 | expedient(本モジュール分・登録簿 §8「C6 艦隊接続」へ転記) | 9 | 7 |
| `HD-llm.parser-1af925f4` | `llm/parser.py`:57 | expedient(本モジュール分) | 5 | 6-1 |
| `HD-llm.undefined-1af925f4` | `llm/undefined.py`:27 | expedient(本モジュール分) | 6 | 6-1 |
| `HD-perception.attention-1af925f4` | `perception/attention.py`:26 | expedient(本モジュール分) | 4 | 5-3 |
| `HD-perception.channels-1af925f4` | `perception/channels.py`:29 | expedient(本モジュール分) | 3 | 7 |
| `HD-perception.hashes-1af925f4` | `perception/hashes.py`:26 | expedient(本モジュール分) | 2 | 7 |
| `HD-perception.normalize-1af925f4` | `perception/normalize.py`:35 | expedient(本モジュール分) | 3 | 7 |
| `HD-perception.p_notice-16ea5cb3` | `perception/p_notice.py`:27 | expedient(本モジュール分・§3.1 の「expedient明示」を写したもの) | 6 | 5-3 |
| `HD-perception.renderer-1af925f4` | `perception/renderer.py`:23 | expedient(本モジュール分) | 8 | 5-3 |
| `HD-perception.state-1af925f4` | `perception/state.py`:28 | expedient(本モジュール分) | 2 | 7 |
| `HD-perception.templates-1af925f4` | `perception/templates.py`:22 | expedient(本モジュール分) | 5 | 4-1 |
| `HD-world.assets-1af925f4` | `world/assets.py`:24 | expedient(本モジュール分) | 3 | 5-1 |
| `HD-world.graph-1af925f4` | `world/graph.py`:11 | expedient(本モジュール分) | 2 | 5-1 |
| `HD-world.processes.actual_log-1af925f4` | `world/processes/actual_log.py`:26 | expedient(本モジュール分) | 4 | 7 |
| `HD-world.processes.constitution-1af925f4` | `world/processes/constitution.py`:18 | expedient(本モジュール分) | 4 | 7 |
| `HD-world.processes.records-6ad4df73` | `world/processes/records.py`:15 | expedient(本モジュール分・CLAUDE.md §4) | 3 | 4-2 |
| `HD-world.processes.registry-1af925f4` | `world/processes/registry.py`:14 | expedient(本モジュール分) | 2 | 7 |
| `HD-world.processes.relations-1af925f4` | `world/processes/relations.py`:12 | expedient(本モジュール分) | 2 | 7 |
| `HD-world.state-1af925f4` | `world/state.py`:18 | expedient(本モジュール分) | 4 | 5-3 |

## 5. manifest と日次の記録

| 欄 | manifest(一番上・末尾) | 日次の記録(`daily` の各行) | 節 |
|---|---|---|---|
| `bridges_count` | 273(台帳の active の行の数=宣言の行の数。T0 では null。位置は T0 のまま) | 同じ(TM9 の行・位置は T0 のまま) | 設定 |
| `rules_version` | `e26d43b4207b5301`(表の sha) | 同じ(`bridges_count` の後・`events` の前) | 設定 |
| `run_kind` | `reproduction`/`counterfactual`/`arm`/`test`/null(`run_day` を直に呼んだ=決めていない) | なし | 設定 |
| `bridges_version` | `470a7a543f5c5b61`(台帳の中身の sha=検収 L1) | なし | 設定 |

- manifest の一番上の鍵は 108 → 111(`rules_version`・`run_kind`・`bridges_version` を末尾に)。凍結の表 `tests/engine/time/manifest_keys_frozen.json` と 10f の末尾の欄の表・設定の節の sha を更新した。既存の欄の値は `bridges_count` のほか動いていない(§6)。
- 台帳と表は `docs/design/` の JSON をランの始め(組み立て)で 1 回読む(`lru_cache`)。壊れた JSON・欠けた欄・知らない欄はそこで `ValueError`(検収 L10)。ファイルが無い写し(`git archive` で `src` だけ取った木)では台帳と表の欄は null になり、`RuntimeWarning` を出してランは続ける。**以後の byte-check の HEAD の写しは `docs/design/rules-table.json` と `docs/design/bridging-ledger.json` も取り出すこと**(取り出さないと HEAD の側だけ null になる)。
- final・behavior-hash は manifest を読まない。試験で `bridges_count`・`rules_version`・`bridges_version` を書き換えても final と呼数が同じことを確かめた。

### 5-1. `run_kind` の規則(今は 1 つ・検収 M2 の後)

- `cli.run` が決める。優先の順: 試験(pytest の中=環境変数 `PYTEST_CURRENT_TEST` がある)→ `test` / CLI の既定と違う腕の引数が 1 つでもある → `arm` / ほか → `reproduction`。`counterfactual` は 3-3 の申込書で決める(今の規則は返さない。`cli.run(run_kind=…)` で渡せば使う)。`cli.main` は `run` の決め方を使う(`main` は HEAD の形のまま)。**`run_day` を直に呼ぶランは null**(決めていない)。
- CLI の既定(`cli.arm_baseline`): `run_day` の既定に、CLI と `run_day` の既定が違う 3 つ(語彙の版 v3・空腹のモデル energy・呼数の倍率 0=無制限)と `cli.run` の 2 つ(`use_population=True`・`store_capital_yen=None`)を重ねたもの。`on`/`off` と真偽・空の並び・列挙の書き方の違いはそろえて比べる。試験で、`main` の既定の引数を `run` が受け取ると腕が 1 つも無いことを確かめた。
- 腕に数えない引数(`cli.NON_ARM_RUN_KWARGS`・31 個): 規模と seed(`n_agents`・`seed`・`population_seed`・`environment_seed`・`n_cells`・`ticks`・`sim_days`・`day_index`)・データと出力の置き場(`world`・`world_dir`・`ledger`・`checkpoint_every`・`checkpoint_detail`・`occupancy_every`・`occupancy_path`・`census_out`)・再開と状態(`state_out`・`stop_at_tick`・`resume_from`・`run_id`)・テープの記録と再生(`tape_path`・`mode`・`replay`)・暦の日付とデータ(`start_sim_datetime`・`holiday_csv`・`school_holidays`)・LLM の接続(`llm`・`fleet`・`fleet_wait_s`・`fleet_debug_dir`)。CLI の `--events`・`--checkpoints-out`・`--undefined-out` は `run` の引数でない=腕でない。LLM の復号(`--temperature`・`--max-tokens`)は `fleet` の中=腕でない。ほかの `run_day` の引数(試験が使う `renderer`・`processes` を含む)と `--weather-perturb` は既定と違えば腕。
- `cli.run` を直に呼ぶ道具: byte-check(10e・19 構成)と 10f の manifest の道具の構成は、既定 v3(`w6_v3_default`)だけが `reproduction` で 18 構成が `arm`(試験)。byte-check の 4 構成では `w6_v3_default` が再現・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` が腕。C7 の `salt_runs` の再開の引数(`stop_at_tick`・`state_out`・`resume_from`)は腕でない(試験)。manifest の 7 本の実際の値は §6。
- 種類は結果に置くだけで、`run_day` の引数にはしていない(引数にすると設定の指紋 `_call_args` が変わり、状態のファイルの見出しと再開の照合が動くため)。この規則自体を `run_kind.py` の expedient の段落で宣言し、台帳の `BR-RUN-KIND-CLI-ARMS`(外す段 3-3)に載せた。

## 6. 結果不変の確かめ

| 確かめ | やり方 | 結果 |
|---|---|---|
| byte-check 19 構成(1 回目・[byte_check_r14.json](byte_check_r14.json)) | `10e/byte_check_10e.py`・19 構成・5,000 体・seed 1・1 日・テープつき。HEAD の側は `136fdbb` の `git archive` の写し(src・anchors・予算の表・w6 の道具+祝日の CSV)、r14 の側は作業木の src(`PYTHONPATH`・`src_is_worktree` 真) | **19/19 構成で 25 欄とも同じ**。既定 v3 の final `5f7ae9ff24005314` |
| byte-check 4 構成(検収の後・[byte_check_r14_4cfg.json](byte_check_r14_4cfg.json)) | 同じ道具の `--only w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`。HEAD の側は本体の HEAD(`fbe2c06`・`136fdbb` からの差は src・anchors・予算の表・w6 の道具のどれにも無い)の写し(`src_is_worktree` 偽)、r14 の側は作業木の src(真) | **4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`=検収役の 4 構成と同じ) |
| manifest(検収の後・[manifest_check_r14.json](manifest_check_r14.json)) | 10f の `manifest_check_10f.py side` の 7 本(既定 v3 の seed 1・2・帰無腕・記憶+関係 ×2・古典+記憶+関係 ×2)を両側とも回し直した。両側 `PYTHONHASHSEED=0`。`tools/manifest_check_r14.py` で平坦にした全欄を比べ、壁時計は除いた | **7/7 で final が同じ・既存の欄 1,730〜2,246 個がどれも同じ**。足したのは 7 葉(一番上の 3・日次の行の `rules_version`・節の表の 3 行)。動いたのは `bridges_count`(一番上と日次の行・null → 273)だけ。一番上の鍵は既存の並びの後ろに 3 つ。**`run_kind` は既定 v3 の 2 本が `reproduction`・帰無腕と記憶+関係 ×2 と古典+記憶+関係 ×2 の 5 本が `arm`**(検収 M2 の前は 7 本とも `reproduction`)。`bridges_version` は 7 本とも `470a7a543f5c5b61`。違う環境の欄は git の commit と汚れと env_id だけ |
| 2 日のラン(1 回目・[two_day_r14.json](two_day_r14.json)) | `10e/two_day_check_act.py one`・5,000 体・seed 1・既定 v3・テープつき・作業木の src | final `912446bd2b42b6ab`・140,913 呼・テープの calls `cb330e76b4b8a573`・blocks `7f09f3dc78d84ac4`・暦 2026-07-13 → 07-14(HEAD の記録の値と同じ) |
| 系ごとの指紋(1 回目・[probe_r14.json](probe_r14.json)) | `tools/probe_r14.py`(1-0 の probe・全部の刻み・`PYTHONHASHSEED=0`)。合成の世界 80 体 720 刻み・世界資産 300 体の既定 v3 と記憶+関係。r14 の側は 1-4 で足した `RunResult.run_kind` と日次の記録の `rules_version` を外し、`bridges_count` を HEAD と同じ null に戻した | **3 構成とも全部の系・全部の刻みで同じ**(並び 6,664・15,598・17,710) |
| 再開 | 既存の試験 `test_resume_10d.py`(1 回目の全体の試験)と `test_t0_tm9_fields.py` の再開 | 通った(§7) |
| 状態台帳・系の宣言 | 状態は足していない(台帳の行・`SYSTEMS` の宣言は不変)。`tests/engine/systems` が通る | 通った |
| 層の契約 | `lint-imports`(作業木の src・1 回目) | 5 kept・0 broken |

- 検収の後の直し(M1・M2・低)で変わったのは台帳の JSON・manifest と記録の欄・組み立ての始めの読み込み・`cli.run` の種類の決め方で、どれも状態と final に入らない。19 構成の byte-check・2 日・指紋・全体の試験は、親の指示どおり回し直していない。

## 7. 試験

新しい試験 80 本(`tests/engine/rules/` 31 本・`tests/engine/bridging/` 49 本=台帳 38・manifest 11・data 不要=合成の世界だけ・4 並列で 21 秒):

- `test_rules_table_schema.py`(31): リポの表 3 行・値が R-106 の値・写し検査・sha が決定的・asof で版を引く・出典の 4 欄は必須・不正な行 8 通り・知らない欄と欠けた欄・形式の版・凍結・読み手は manifest と日次の記録と組み立ての 3 か所だけ(AST・`from shibuya.engine import rules` と相対 import も見る=検収 L8)・その負の対照 6 形。
- `test_bridging_ledger.py`(38): 全行の欄(`since` は形だけ)・`rule_id` が規則の表にある・置き場のファイルがある・最初の中身・不応期 11 種と起床条件のクラス・**コードの宣言と 1 対 1**・形ごとの数(0・139・5・74・18・5)・第 5・6 形の行(数・返済期限・declared の条件)・文字列の宣言の写し・第 4 形の行(id=見出しの文の sha8・見出しと項の数)・C8 の D-44 の行と同じ項・負の対照 9 本(§4-2 の (a)〜(i))・文書の行(「繋ぎ」の 3 か所を含む)・不正な行 12 通り・知らない欄と重なり・凍結・sha・壊れた台帳は読み込みとランの始め(組み立て)で落ちる・分布の和。
- `test_manifest_rules_bridges.py`(11): 鍵の末尾と凍結・値が台帳と表に一致(`run_day` を直に呼ぶと `run_kind` は null)・節は設定・日次の記録・ファイルが無い写しでは null と警告・欄を書き換えても final と呼数が同じ・`run_kind` の規則・CLI の既定は腕でない(`main` の既定の引数)・byte-check と manifest の道具の 19 構成(既定 v3 だけが再現)と C7 の再開の引数・`main` と `cli.run` が種類を決める(試験の中/外・腕)・種類は記録だけ(final が同じ)・不正な名はランの前に止まる。

検収の後の指定の範囲(4 並列): `tests/engine/bridging tests/engine/rules tests/engine/time tests/engine/events tests/engine/systems tests/test_cli.py tests/engine/test_env_and_sections_10f.py` と `cli.main` に関わる `tests/test_cli_l4_scale.py`・`tests/test_cli_vocab_version.py`・`tests/test_cli_intent_mode.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/test_classical_policy.py` = **457 passed(7 分 23 秒)**。

### 7-1. 全体の試験(1 回目・第 4 形の前)

`-m "not gpu and not slow" -n 4 --dist loadfile`(data あり・作業木):

- 1 回目: 4,161 passed・2 failed・1 xfailed(14 分 37 秒)。落ちた 1 件は実装役の誤り: `tests/engine/processes/test_rng_scheme_10c.py::test_cli_flag_is_shared_by_engine_run_and_cli` が `cli.main` のソースに `add_calendar_args(ap)` があることを見ている。引数の表を `build_parser()` に切り出したのでソースから消えた。**切り出しをやめて `main` の形を HEAD に戻した**。
- 2 回目(戻した後): **4,162 passed・1 failed・1 xfailed(28 分 10 秒)**。落ちた 1 件は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(作業木の `data` が本体への junction であることで起きる既知の落ち)。
- 第 4 形と検収の後の直しのあとの全体の試験は、親の指示どおり回していない。

## 8. 限界・空欄・仮採用・親に確かめてほしい点

仮採用(回答 10-13b §0-3 の 2・どれも後から戻せる形):

1. **規則の表の行の形**: `source` を出典の並び(1 つ以上)にした(消費税は国と地方の 2 本の法)。`law_id`・`retrieved`(取得日)は任意の欄。`note` 欄を足した。
2. **深夜酒類の行の `asof`**: 施行の初日が答申に無いので、読んだ法の版 2025-11-28 を下限にした(実際の施行日は未確認)。
3. **`Bridge` に 3 欄を足した**: `remove_basis`(plan/declared/inferred)・`code_at`・`rule_id`。口の約束の欄の外。
4. **外す段 `7`**: 外す段が計画に無い行(60 行)に第 7 期を当て、「主張の前に感度試験で駆動しないことを示す」の意味にした。計画の段の番号に `7` という段は無い。`5-N` も計画の字としては無い(「第 5 期 空間の段 N」=限界 L9)。
5. **inferred の 218 行の外す段**: build の段ごと・ファイルごと・世界過程の話題ごとに当てた(§3-2・§4-4)。未リサーチ。〔親の判断 第334〕W7 → 4-2・W17 → 6-2・家賃 → 4-2 は認める。W14・看板・西武・W9 の幾何 → `7` のまま。第 4 形の 74 行と第 5・6 形の 23 行の当て方はまだ親が見ていない。
6. **#88 の 4〜6 をコードの宣言の行と同じ行にした**(二重に数えない)。
7. **不応期 11 種は各 1 行**。会話ターンと睡眠中は conf=mechanism だが、T3 で外す点は同じ。
8. **`run_kind` の規則**: 腕に数えない引数の一覧(`NON_ARM_RUN_KWARGS`)と CLI の既定の重ね方(`arm_baseline`)は実装役の振り分け。〔親の判断 第334〕数え方(`--weather-perturb` を腕に・復号と暦の日付を腕でない)は認める。pytest の判定は環境変数 `PYTEST_CURRENT_TEST`。
9. **発注の編集してよい一覧の外を 1 本直した**: `tests/engine/time/test_t0_tm9_fields.py` の 3 か所。発注の「null を件数に」と「末尾に足す」から必ず要る直し(検収役も認めてよいと読む)。
10. **第 4 形は見出し単位で 1 行**(親の判断 第334)。項の数は `what` に書き、試験が今のコードと突き合わせる。
11. **`declared_in` は行番号でなく中身**: 第 4 形は「ファイル+見出しの文の sha」、第 5 形は `id`、第 6 形は `<subject_id>|<plan_spec_id>`。行番号にすると、見出しより上の行を足し引きするたびに 1 対 1 の試験が落ちる。行番号は §4-4 の表に写した。
12. **第 5 形に PlanSpec の 2 本を入れた**(親の指示は「世界過程の宣言 16 本」): `plan.opening_hours`・`plan.road_works` も `mechanism=False`+`sensitivity_test_id`+`repayment_due` の同じ形の宣言なので、規則(引数に `mechanism=False` と `repayment_due=` の両方がある呼び出し)で数えると 18。外すなら規則を `WorldProcess(...)` に絞る。
13. **`#` の注の expedient(277 行)は数えていない**(検収 M1 (d)=親の判断)。6 形の宣言を持たない 31 ファイルの近似は台帳に行が無い。
14. **「繋ぎ」の 3 か所と直書きの最低賃金は文書の行**: コードの書き方を変えない(コードに宣言を足すと src の docstring が動く)ため、`declared_in` を review.md と口の約束にし、`code_at` にコードの場所を書いた。

空欄・限界(検収の低):

- **L4 二重の数え**: `bridges_count` は宣言の行の数(§3-3 の重なりの一覧)。一意の数は 2-0 の課題。
- **L6 見出しの行の `remove_at` は代表の項の段**: 項のすべてがその段で外れるとは限らない(例 `HD-engine.processes.opening-…` の 1-5 は担当の丸振りの項だけ・`HD-agents.state-…` の 16 項は 7)。
- **L9 `PLAN_STAGES` は手の表**: 計画の文書の段の番号と突き合わせる試験は無い。`5-N` は計画の §5-N や CP5-5 と字が重なる(空間の段を `S0`〜`S6` にするかは仮採用 4 と一緒に親の判断)。
- **L11 byte-check の compare の JSON に側ごとの `src_is_worktree` が残らない**(10e の道具の形・範囲の外)。検収の後の 4 構成は side の記録で HEAD の側が偽・r14 の側が真を確かめた(4 構成の side の JSON は `_bc/` にあり git に入れない)。1 回目の 19 構成も `PYTHONPATH` で作業木の src を選んで回した(標準出力で目で確かめたのは最初の 2 本・その置き場は消えた)。
- 台帳の初めの中身は `tools/build_ledger.py` で作った(`--check` で今の台帳と同じ中身になる)。f 文字列の `what` は `data/world/v2/build_manifest.json` を読むので、道具は data のある機械でだけ同じ中身を再現する(試験は data を読まない)。以後は台帳を手で直す前提。
- 世界の時点の最低賃金 1,226 円・軽減税率 6.24%・レジの端数の規則は表に入れていない(4-2・親の判断 第334 で認める)。e-Gov の版は今の版(2026-10-01)で、世界の時点の条文の取り直しはしていない。
- 計器盤への表示は発注どおり作っていない(manifest と日次の記録で足りる)。
- 用語: 「つなぎ」「外す段」「口」「約束」は用語集と既存の記録の語。新しい語として「外す段の根拠(plan/declared/inferred)」を使った。

## 9. 検収(review.md)の後の直し(親の判断 第334)

| 指摘 | 直したこと | 確かめ |
|---|---|---|
| M1 (a) | 第 5 形(`mechanism=False`+`repayment_due` の世界過程と PlanSpec の宣言)を AST で数え、18 行(`PR-…`)。外す段は返済期限から(エージェントへ=6-6 declared・データ待ち=話題で inferred) | 1 対 1・負の対照 (g) |
| M1 (b) | 第 6 形(`fallback_ledger()` の 5 行)を実行して読み、5 行(`FB-…`) | 1 対 1・負の対照 (h) |
| M1 (c) | 「繋ぎ」と明記した 3 か所を文書の行に | 試験(コードに「繋ぎ」がある) |
| M1 記録 | §4-3 を実際に合わせた(`#` の注 277 行・宣言の形の無いファイル 31 本・`mechanism=False` 46 の内訳)・「`bridges_count` は宣言の行の数で、一意のつなぎの数ではない」を §0・§3-3・台帳の `note` に・重なりの一覧(§3-3)と 2-0 の課題 | — |
| M2 | ランの種類を `cli.run` で決める(`arm_baseline`・`run_arms`)。`main` は `run` の決め方を使う。`run_day` を直に呼ぶランは null | 試験・manifest の 7 本(§6) |
| L1 | manifest に `bridges_version`(台帳の sha)・凍結の鍵を 1 つ増やした | 試験・manifest |
| L2 | `removed` の行を許し、件数と突き合わせは active だけ | 負の対照 (i) |
| L3 | `since` は日付の形だけを見る | 試験 |
| L5 | 第 4 形の id を「ファイル+見出しの文の sha8」に | 試験 |
| L7 | `MIN_WAGE_HOURLY = 1_226` を `BR-MIN-WAGE-HOURLY-1226`(4-2・`rule_id`)に | 試験(`rule_id` が規則の表にある) |
| L8 | 読み手の AST の試験に `from shibuya.engine import rules` と相対 import を足した | 負の対照 6 形 |
| L10 | 台帳を読み込みで検査し(壊れた JSON・欠けた欄・知らない欄)、組み立ての始めで 1 回読む | 試験(ランの始めで落ちる) |
| L4・L6・L9・L11 | 限界として §8 に書いた | — |

## 10. 親の検収(第334・2026-10-14)

- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・見出し 74 行を足した後): final が同じ 4/4・動いた欄 0(parent_head_vs_r14_4cfg.json)。直しの後(273 行)の 4 構成は実装役の byte_check_r14_4cfg.json(同じ)。
- 独立検収(review.md)=条件つき受入 → M1(4 形の外の宣言=第 5 形 18 行・第 6 形 5 行・文書 4 行)と M2(腕の判定を cli.run へ)を実装役が直し、低 L1・L2・L3・L5・L7・L8・L10 も直した(§9)。
- 親の答え: PlanSpec 2 本を第 5 形に入れる(仮採用 12)・外す段の当て方(第 4 形 74 行・第 5/6 形 23 行・inferred)は仮採用として認める(2-0 で件数を計器に出す前に見直す)・# の注 277 行と宣言の形を持たない 31 ファイルは台帳に入れない(宣言ではない)。範囲の外の試験の直し(T0 の TM9・10f の凍結)は「増えた分だけ」として認める。
