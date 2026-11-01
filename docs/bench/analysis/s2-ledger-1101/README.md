# 段 2 の 2・6・7 台帳の欄・「無いと宣言」の計器・入力の宣言の欄(第340・枝 stage/s2ledger-1101)

正: [回答 11-01](../../../design/v2-answers-2026-11-01.md) §1(5 区分と入力の宣言の型)・§2(代打の 5 条件・無いと宣言)・§3(循環の機械検査)・§10-3(無いと宣言する過程)、[指示書 11-01](../../../design/prompt-2026-11-01.md) 段 2 の 2・6・7。根拠: [routing](../../../reference/decision-routing-2026-11-01.md) §1・§3・§4・§6-B、[a1-research](../../../reference/a1-research-2026-10-31.md) §6。独立の検収: [review.md](review.md)(条件つき受入・中 4・低 9)。直しは §8。

この段は**宣言と計器の整理**です。エンジンの挙動は変えていません。`src/` で触ったのは `src/shibuya/world/processes/` と、親の許可(検収の直し・今回だけ)で `src/shibuya/engine/bridging/ledger.py`(欄と段の名の追加だけ)です。率の規則の削除(S2-rates)と規則の表(S2-rules)には触っていません。

## §1 作ったもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/world/processes/records.py` | `WorldProcess` と `PlanSpec` に 3 欄: `drives_from`(値の系=パターン ID・`data:<id>`・`none`)・`absence`(型 `Absence`)・`input_decl`(型 `InputDecl`)。欄の名は `absent` だと在圏の欄 `presence.absent` と状態の検査 O38 でぶつかったので `absence` にした。3 欄は `as_dict` に入れない=`registry_hash` は変わらない。`Absence` は宣言の文・理由・外す段の文・`engine_stopped`(エンジンがもう動かしていないか)・`stage`(DEC の行の `remove_at` と同じ段の語)ほか。`InputDecl` は回答 §1 の型と `carrier`(世界の台帳に記録の無い入力の置き場) |
| `src/shibuya/world/processes/absent.py` | 「無いと宣言」26 件(主体が居ない過程 8・入力/初期の予定 2・口が無い判断 13・率を外して無いにするもの 2=ポイ捨てと売れ残りの廃棄・補足 1)。routing §3 の文案の写しは 19 件(試験で原文と照合)。W3 の文の 2 件(救急と倒れる)は回答 §3 の読みに統一した |
| `src/shibuya/world/processes/inputs.py` | 入力の宣言 13 件(既存 5=埋めた・新しい 7=欄だけ・納品=欄だけ) |
| `src/shibuya/world/processes/circularity.py` | 突き合わせ(`drives_from` × 採点する系 × `burned` × 無いの宣言の `engine_stopped`)と代打の条件 ⑤ の見方 |
| `src/shibuya/world/processes/first_batch.py` | 世界過程 21 本と PlanSpec 4 本の全部に `drives_from`。`absence` を 7 本、`input_decl` を 6 本に付けた |
| `src/shibuya/engine/bridging/ledger.py` | `Bridge` に空でよい欄 7 つ(`drives_from`・`routing_row`・`world_process`・`decided`・`contributes`・`calibration_declined`・`drives_note`)。空なら `as_dict` に出さない。`PLAN_STAGES` に `11-01p-1`〜`11-01p-5` |
| `docs/design/bridging-ledger.json` | `DEC-<#>-<英数>` を 112 行足した(末尾・欄つき)。既存の 673 行は不変(試験で指紋を固定)。前の版の頭の鍵 `row_fields` は消した |
| `docs/design/v2-pattern-ledger.md` | 10 表に「採点する系」(行の ID と出典の系 `data:<id>`)と `burned` の 2 列(既存のセルは不変) |
| `tools/ledger/add_decision_rows_1101.py`・`add_pattern_columns_1101.py` | 冪等な道具(本体の版の上で何度回しても同じ) |
| `tools/instruments/absent_declarations.py` | 「無いと宣言」の一覧を Markdown に出す計器。いまの出力は [absent_declarations.md](absent_declarations.md)(指紋 `bf0b9eeeb6d9c0a9`)。試験が生成と一致を見る |
| 試験 | `tests/bridging/test_drives_from_vs_scoring.py` 17 本・`test_decision_rows_1101.py` 6 本・`tests/world/processes/test_declarations_1101.py` 11 本・`tests/tools/test_absent_declarations.py` 3 本 |

### 1-1 DEC の行の欄

- `what`=判断、`why`=routing §1 のセルの写し、`declared_in`=routing の行、`since`=2026-11-01、`status`=active、`remove_basis`=inferred。
- `remove_at`(当てた値・検収 中-4・低-6 で当て直し): L1.5→`11-01p-3`(語彙と判断の口)・初期の予定→6-2・代打と無いと宣言→6-6・L2→6-7(#100・#101 は店の仕事=6-6・#49・50・52 は会話の段=6-4)・#79→7・L1 残すと要判断→7。ただし回答 §2 で外す 9 件(#2・3・10・22・42・83・99・105・101=Calvo)と routing が「すぐ外せる/すぐ外す」と書く行(#104・106・110・111)は `next-bump`(「すぐ外すか」の問いの形の #108 は除く)。件数は 11-01p-3 が 50・7 が 34・next-bump が 13・6-2 が 6・6-6 が 4・6-4 が 3・6-7 が 2。
- `conf`: L1 残すで仕組みも値も裏付けのある 5 行(#17・58・84・87・92)は mechanism。#76(語の区切り)・#83(率の置き換え)・#85(不応期 30 分)・#88(器だけ)とほかは expedient(検収 低-5)。
- 欄の数: `drives_from` 31・`world_process` 23・`decided` 41・`contributes` 4(#83=W3・#63=A5〜A7・#69・#71=A5・A6)・`calibration_declined` 1(#101=E7)・`drives_note` 28。
- 前の版で既存の行に書いた値は、同じものの DEC の行へ移した(BR-BODY-COLLAPSE-RATE→DEC-83・BR-ATTENDANCE-LOTTERY→DEC-2・BR-W17-IO-SLEEP→DEC-1/63/69/71・BR-DELIVERY-INBOUND→DEC-102・HD-economy.pricing→DEC-101)。PR-/FB- の行は世界過程の宣言(`first_batch`)が正。

### 1-2 drives_from(世界過程と PlanSpec)

| 値 | 過程 |
|---|---|
| `W2` | delivery_last_mile(区按分 27,000 個/日=a1 §6 #16) |
| `W3` | public_service_dispatch(出動の回数は倒れる率=W3 と同系=a1 §6 #8) |
| `data:road_census_r3` | vehicle_cross_section(klass 既定はセンサス R3 の同じ行=traffic.py の docstring)・static_noise_field |
| `data:tokyo_noise_r5` | static_noise_field(W10 は都環境局 R5 の 7 点で残差を照合=D12′ の用途欄) |
| `data:timetables_w12` | rail_operation_static・plan.rail_timetable |
| `data:jma_etrn` | weather |
| `data:w7_opening_hours` | store_opening・plan.opening_hours |
| `none` | 残りの 16 本 |

W17 の系の DEC の行(#1・5・63・69・71・79)は `data:ssb`・`data:pt2018`(D11′ の用途欄「W17較正」)。祝日(#74)は `data:cao_syukujitsu`。

### 1-3 パターン台帳の 2 列

- 「採点する系」: 行の ID と、照合値の出典の系(分かる行だけ)。`D5`・`D5′`=`data:road_census_r3`(D5′ は D5 の一次化)・`D12′`=`data:tokyo_noise_r5`・`A4`〜`A7`=`data:ssb`(A5 は `data:nhk_time_use` も)・`D6`・`D7`・`D11′`=`data:pt2018`・`D1′`・`D4′`=`data:kddi_la`。気象・鉄道のダイヤ・祝日を出典にする行は無い(突き合わせの相手が無い)。
- `burned`: `burned(…)`=F1・F2・F3・D11′(検収 低-1)/`外す(W3 は錨に残す・体の式ができるまで検証から外す)`=W3(低-8)/`—(較正→検証へ)`=D5′/`要確認(…)`=E5・A5・E1・D12′・AD2・W1・W6(印だけ)/ほか `—`。
- §10-1 は `—(検証専用)`、§10-2 は「一部 burned(構築・較正に使う部分)」ほか。§10-3 は箇条なので列を足せない(問い 6)。

## §2 既定の結果が不変であること(宣言だけを変えた)

```
$ git diff --stat src/
 src/shibuya/engine/bridging/ledger.py      |  41 +++++-
 src/shibuya/world/processes/__init__.py    |   3 +
 src/shibuya/world/processes/first_batch.py |  45 ++++++
 src/shibuya/world/processes/records.py     | 215 +++++++++++++++++++++++++++++
 4 files changed, 303 insertions(+), 1 deletion(-)
```

ledger.py の 1 行の削除は `from_dict` の知っている欄の集合の行を置き換えたもの。新しいファイルは `world/processes` の `absent.py`・`inputs.py`・`circularity.py`。エンジンからは import していない。

- `build_registry().registry_hash()` は前と同じ `1a5fcb8c…31095743`(試験で固定)。
- manifest で動くもの: `bridges_count` 643→755・`bridges_version`(台帳の中身の sha)。この段の意図した差(問い 2)。台帳の形式の版 `shibuya.bridging-ledger/1` は上げていない(足した欄は空でよく、古い行はそのまま読める)。

## §3 突き合わせの結果

規則(`circularity.py`): 主体の `drives_from` の語が、主体の `contributes` に入るパターン行の ID か「採点する系」の語(`data:<id>` を含む)と同じなら重なり。例外は (1) その行の `burned` が `burned`/`外す` で始まる、(2) 主体に「無い」の宣言があり `engine_stopped=True` で、その行が宣言の錨(`keeps_anchor` と結ぶ過程の `contributes`)に入る、の 2 つ。`engine_stopped=False` の宣言は例外にせず「宣言と実装が食い違う」と出して落とす。

| 主体 | 系 | 行 | 扱い |
|---|---|---|---|
| world_process:delivery_last_mile・DEC-105 | W2 | W2 | **落ちる=宣言と実装が食い違う**(宅配の率の規則がまだ動く。S2-rates の後に通る=§7) |
| world_process:public_service_dispatch・DEC-83・DEC-110 | W3 | W3 | W3=外す で通る |
| world_process:vehicle_cross_section・DEC-109 | data:road_census_r3 | D5′・D5 | 疑い=警告(親が決める) |
| world_process:static_noise_field | data:tokyo_noise_r5 | D12′ | 疑い=警告(D12′ は burned=要確認) |
| DEC-63 | data:ssb | A5・A6・A7 | 疑い=警告(W17 の元の表と A5〜A7 の表が同じかは未確認) |
| DEC-69・DEC-71 | data:ssb | A5・A6 | 同上 |

β と E7: `drives_from` に E7 を持つ主体は 0 件。`DEC-101-changePrice` に `calibration_declined: ["E7"]`、パターン台帳の E7 は `—`。

### 3-1 疑いの 5 行(代打の条件 ⑤ を `contributes` で確かめた・いまは警告だけ)

| 疑い | 主体 | 結んだ過程 | contributes | ⑤ の重なり | drives_from の重なり | 読み |
|---|---|---|---|---|---|---|
| 席 30 分→D8 | DEC-31・DEC-32 | indoor_occupancy | D8 | **D8** | なし | 席の規則が決めた滞在時間が D8 で採点される |
| 補充→W1/E5 | DEC-98 | shelf_stock_restock | W1・E5 | **W1・E5** | なし | W1 の帯は同じ定数から作った自己整合(台帳 §9 W1)。E5 は較正(要確認) |
| 家で使う→W1 | DEC-41 | goods_conservation | W1 | **W1** | なし | W1 の帯に世帯の消費は入らない(「記録のみ」) |
| 車→D5′ | DEC-109・vehicle_cross_section | vehicle_cross_section | D5′・D5 | **D5′** | **D5′・D5** | §10-2 の区間の分け方(外側=較正・内側=検証)を drives_from に書けば解ける見込み |
| バス→D11′ | DEC-108 | bus_taxi_operation | D6・D7 | なし | なし | 循環なし。D11′ は生成に使う錨(burned)で、そもそも検証に使わない(検収 低-9) |

## §4 空欄と自己申告の欠陥

1. ごみ収集・清掃・道路工事・救急と警察・電気と水は「無い」と宣言したが、エンジンの規則がまだ動く(`engine_stopped=False`)。外す段は指示書 11-01 に無い(問い 3)。W3 と D5′ 以外の重なりは今は出ていないが、これらの過程に `drives_from` の重なりが出れば落ちる。
2. W17 の DEC の行の `contributes`(A5〜A7)は実装役の読み。D1′・D6・D7 に入るかは確かめていない。
3. β の較正の予定の文は世界過程設計書 §8 H-5 に残る(問い 4)。
4. 納品の量を錨から外すには `delivery_inbound` の `contributes`(E5)を外す必要がある。registry_hash が変わるので未着手(問い 5)。
5. `first_batch` の weather の更新規則の文「tick 単位に線形補間」はエンジンと違う(エンジンは時別の値を 5 分ごとに引き、補間しない)。文は registry_hash に入るので直していない。入力の宣言はエンジンに合わせた(検収 中-2)。
6. `burned=要確認` の 7 行は印だけで、突き合わせの結果は変えない。
7. 入力の宣言の「空欄(…)」: 外界ノードの版・取得日・時間の細かさ・補間・揺らし方、外の売上の版と揺らし方と期間、各入力の「較正か検証かの期間」。
8. `plan.bus_timetable` は中身が「ODPT GTFS(バス)」だが、エンジンは 10 分おきの定数で走る。`drives_from` は `none`。
9. ODPT の乗降人員(W12 の境界の量の材料)と D10 の公式値の関係は「採点する系」に書いていない(外界ノードは世界の台帳に主体が無く、突き合わせの相手にならない)。

## §5 問い(親へ)

1. byte-check で `bridges_count`・`bridges_version` の差を意図した差として扱ってよいか。DEC の 112 行(L1 残すの 9 行を含む)を active として数えてよいか。
2. 台帳の形式の版(`shibuya.bridging-ledger/1`)を上げるか(欄を足した。上げると既存の試験の文字列 2 か所も直す)。
3. ごみ収集・清掃・道路工事・救急と警察・電気と水の規則をエンジンから外す段。
4. 世界過程設計書 §8 H-5 の「E7 取得後に較正」の文を消すか。
5. `delivery_inbound` の contributes の E5 と、weather の更新規則の文を次の版上げで直すか(どちらも registry_hash が変わる)。
6. §10-3 の 2 項の `burned` の置き場。
7. 疑いの重なり(車・騒音・W17)と ⑤ の 4 行を CI で落とす側へ移すか。
8. DEC の行の `remove_at`(当てた値)を確かめてください。

## §6 試験

- 新しい試験 37 本。いまの作業木で落ちるのは `tests/bridging/test_drives_from_vs_scoring.py::test_no_unexpected_circularity` の 1 本だけで、**意図した落ち**(宅配の W2=宣言と実装が食い違う。§7 の後に通る)。ほかは通る。
- 回した範囲: tests/bridging・tests/world/processes・tests/tools/test_absent_declarations.py・tests/engine/bridging・tests/c8/test_sensitivity_ledger.py・tests/engine/test_state_checks_10f.py=265 本が通り、上の 1 本が落ちる。
- 前回の全体(`-m "not gpu and not slow"`)の落ち 4 件のうち 3 件(O38)は欄の名を `absence` にして直った。残りの `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report` は作業木では本体の src でも落ちる(テープの道筋。本体のリポでは通る=検収)。
- import-linter は 5 契約とも通る。秘密スキャンは CLEAN。

## §7 取り込みの手順(率の規則を外す段=S2-rates の後)

1. S2-rates(宅配・倒れる率・催しの注入・ポイ捨て・売れ残りの廃棄の率の規則を外す)を先に取り込む。
2. `src/shibuya/world/processes/absent.py` で次の 5 件の `engine_stopped` を `True` にする: `absent.parcel_delivery`・`absent.collapse`・`absent.event_injection`・`absent.litter`・`absent.discard_unsold`。`engine_now` の文を「外した(段の名)」に直す。
3. `tests/bridging/test_drives_from_vs_scoring.py` の `test_engine_stopped_flags`(5 件は False と書いてある)と `test_mismatch_list_is_what_s2_rates_must_resolve`(宅配の 2 件)を、空の一覧と True に直す。`test_no_unexpected_circularity` は直さなくても通る(実装役が 5 件を True にした写しで確かめた)。
4. S2-rates が既存の行(出勤率のくじなど)を removed にしたら、`tests/bridging/test_decision_rows_1101.py` の `BASE_ROWS_SHA` を直し、変えた行を記録に書く。
5. 計器を回して記録を出し直す: `python tools/instruments/absent_declarations.py --out docs/bench/analysis/s2-ledger-1101/absent_declarations.md`(試験 `test_record_matches_the_current_output` が一致を見る)。
6. 台帳を本体の版の上で作り直すときは `python tools/ledger/add_decision_rows_1101.py` と `python tools/ledger/add_pattern_columns_1101.py`(どちらも冪等)。

## §8 検収の直し

| 番号 | 直したこと |
|---|---|
| 問い 1・中 1 の土台 | 欄を `Bridge` の欄へ移した(7 欄・空なら出さない)。`row_fields` を消した。`PLAN_STAGES` に `11-01p-1`〜`11-01p-5` |
| 中 1 | 「採点する系」に出典の系 `data:<id>` を併記。車と騒音の `drives_from` を同じ語にそろえ、騒音に `data:tokyo_noise_r5`(D12′ の系)を足した。W17 の行に `contributes`(A5〜A7)。D5′→D5・騒音→D12′・W17→A5〜A7 が検出される(警告) |
| 中 2 | `input.weather` をエンジン(`_heat_now`)に合わせた: 時別の暑さ段と WBGT を 5 分ごとに引く・補間なし |
| 中 3 | `Absence.engine_stopped` を足し、「無い」の例外は True のときだけにした(False は「宣言と実装が食い違う」で落とす)。ポイ捨てと売れ残りの廃棄の宣言を足した。手順は §7 |
| 中 4 | 回答 §2 の 9 件と「すぐ外せる」行を `next-bump`、L1.5 を `11-01p-3` に。`Absence.stage` を DEC の `remove_at` とそろえた(試験) |
| 低 1 | D11′ を `burned` に |
| 低 2 | 「無い」の例外を宣言の錨に限った |
| 低 3 | 土台の 673 行の指紋を固定する試験 |
| 低 4 | 外界ノードの `one_way` を一方向の文に。外の売上の実体(`stage2.py` の `external_sales`)と値 0。暦・外界ノード・外の売上の置き場(`carrier`) |
| 低 5 | L1 残すの conf: #76・85・88(と #83)を expedient に |
| 低 6 | #49・50・52 を 6-4、#79 を 7 に |
| 低 7 | 計器の出力が生成と一致する試験は既にある(`test_record_matches_the_current_output`)。runbook と STATUS の 1 行は親 |
| 低 8 | W3 の文を「W3 は錨に残す・体の式ができるまで検証から外す」に統一(パターン台帳と Absence の 2 件) |
| 低 9 | バスの読みに「D11′ は生成に使う錨」を足した(§3-1) |
