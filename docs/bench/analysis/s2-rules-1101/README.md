# 段 2 の 5 規則の表の最低賃金を `human` へ(つなぎの床と違反の記録の器)の記録

- 実装役 Opus 5.5。作業木の枝 `stage/s2rules-1101`(土台 `c0729a4`。発注文の `a09809c` ではなかった=問い 1)。commit は親。
- 正: 回答 11-01 §5(判定は「現実でその場で物理的に止まるか」。止まるものだけ machine。最低賃金・法定労働時間は human へ。
  検知と反応の口ができるまで machine をつなぎとして残す)・指示書 11-01 段 2 の 5(違反が起きたら記録する器だけ先に)。
  根拠: A1 の調べ §6 の #4 と論点 5・R-118 §2(machine とした元の判断)・IMPLEMENTED #120・#122・10-12 §1-4・§1-12。
- 独立の検収 [review.md](review.md)(条件つき受入・高 0・中 2・低 6)を受けて直した(§10)。
- 新しい取得はしていない(ネットワークなし)。数は実測。生の出力は git の外。絶対パスなし。

## 0. 結論

- 規則の表 `minimum_wage.tokyo` の 3 版(1,163 円・1,226 円・1,280 円)を `kind: human` に直し、つなぎの欄
  `params.bridge`(machine・conf `expedient`)を足した。値の欄(`yen_per_hour`・`area`)は不変。
- 〔検収 M1〕表の中の「human の行の machine のつなぎ」の書き方を `params.bridge` の 1 つに統一した: 前からの
  `consumption_tax.filing_deadline`(つなぎの台帳 `DOC-rules42-tax-remit-machine`・`taxes.BRIDGE_READ_RULES`)にも同じ形を
  足した。つなぎのある行は 4 版(最低賃金の 3 版+申告の期限)。ほかの 26 行は不変。行の欄(形式の版 3)への移動は次の段
  (engine を触る段)。
- 床(最賃法 4 条 2 項の効果)は残した。床を当てるのは「行が machine」か「行が human/norm でつなぎが machine」のときだけ
  (`economy.anchors.min_wage_terms`・表の値を直書きしない)。つなぎを外せば床は当たらず、下回ったまま払う。
- 違反の記録の器 `economy.stage2` の `rules.minimum_wage_shortfall`(ランの積算・集計だけ・`scope: "run"`): 床を当てる
  直前に下回った体と額(`below_*`)・つなぎの床が上げた体と額(`lifted_*`)・下回ったまま払った体と額(`violation_*`=
  起きた違反)・組み立ての日に下回る体の数(`below_at_start`=つなぎの有無に依らない)。
- 既定(つなぎあり)では **`violation_rows` = 0**。下回りは立つ: 1,000 体で 614 行を見て **`below_rows` 93・
  `below_amount` 4,776,962 円**・5,000 体で 2,726 行を見て **531・29,642,965 円**(=前からの計器 `wage_model.floor` の
  `raised`・`raised_amount` と同じ数)。
- **1 バイト不変**(〔検収 M2〕根拠を直した): 3 日のラン(給料日の締めを含む)で、前と後の **日の締めごとのハッシュ
  (`daily[*].state_hashes_end_of_day`)・金の流れの表の sha・保存則・賃金の計器**が全部同じ(1,000 体と 5,000 体)。
  つなぎを外した対照ではどれも変わる=この 4 つが賃金の違いを見分ける(§4)。変わるのは `rules_version` と、manifest の
  `economy.stage2.rules` に足した器の鍵だけ。
- 法定労働時間(`labor.statutory_hours`)は前から human で、機械が止める側がコードに無い=つなぎは足さない。超えた数は
  エンジンのカレンダー 3 と持ち場の層が前から数える(§3)。経済の側の器は作らない(二重に数えない)。

## 1. 変えた行(規則の表)

| 行 | kind(前 → 後) | 足した欄 | note |
|---|---|---|---|
| `minimum_wage.tokyo`@2024-10-01(1,163 円) | machine → **human** | `params.bridge` | 「=機械が守らせる側」を「=R-106 の振り分けでは機械が守らせる側」に・末尾に 11-01 §5 の 1 文 |
| `minimum_wage.tokyo`@2025-10-03(1,226 円) | machine → **human** | `params.bridge` | 同上 |
| `minimum_wage.tokyo`@2026-10-01(1,280 円) | machine → **human** | `params.bridge` | 同上(R-106 §振り分けの例の注は残した) |
| `consumption_tax.filing_deadline`@2026-10-01 | human(不変) | `params.bridge`(〔検収 M1〕) | 末尾に「書き方を params.bridge に統一した」の 1 文 |

`params.bridge` の中身:

```json
// 最低賃金の 3 版(remove_at はつなぎの台帳の行と同じ段の語・説明の文は remove_note)
{"kind": "machine", "conf": "expedient", "remove_at": "7",
 "remove_note": "検知と反応の口(気づいた人・本人・監督)ができる段",
 "declared_in": "11-01 §5", "ledger_id": "DOC-s2rules-min-wage-floor-bridge"}
// 消費税の申告の期限(つなぎの台帳の既存の行 DOC-rules42-tax-remit-machine の値)
{"kind": "machine", "conf": "expedient", "remove_at": "6-6",
 "declared_in": "docs/bench/analysis/wallbounce-1012/rules42/README.md", "ledger_id": "DOC-rules42-tax-remit-machine"}
```

- 置き場: 表の形式(`engine/rules/table.py` の `Rule.from_dict`)は知らない欄を止め、`engine/` は本段で触らない約束なので
  `params` の中に置いた。**行の欄(`kind` と並ぶ欄・形式の版 `shibuya.rules-table/3`)への移動は次の段(engine)**。欄の検査は
  経済の側の読み口 `economy.anchors.rule_bridge`(必須 4 欄 `kind`・`conf`・`remove_at`・`declared_in`・任意 `ledger_id`・
  `remove_note`・
  知らない欄と空の値を止める・`kind` は表の 3 種・行と同じ kind のつなぎは止める・`conf` は `expedient`/`mechanism`)。
- `conf` はつなぎの台帳の語(`CONFS`=`expedient`/`mechanism`)のまま(親の判断・数の conf(0.5 など)は WorldProcess の側の語)。
- `remove_at` は計画の段の語(つなぎの台帳の `PLAN_STAGES`)で統一した(親の判断): 最低賃金=`7`(台帳の行
  `DOC-s2rules-min-wage-floor-bridge` と同じ)・申告の期限=`6-6`。最低賃金の外す段の説明の文は `remove_note` に置いた。
- 表の件数は不変(30 行・28 の id)。表の sha(`rules_version`)は **`1490c5a2fdc8beb4` → `86865567d548cbf3`**。
  `CONFIG_PATHS_SHA256`(設定の節の道筋)は変わらない(器は観測の節 `economy.stage2.rules` の下)。sha を固定した試験は無い
  (`rules_version` は表から計算して比べる形)=取り込みで直す値は無い。

## 2. 床の読み替えと器

| 場所 | 変えたこと |
|---|---|
| `economy/anchors.py` | `RULE_BRIDGE_KEY`・`rule_bridge`(欄の検査)・`check_rule_bridges`(〔検収 L1〕表の全部の行の全部の版を検査・つなぎのある行の `<id>@<asof>` を返す)・`MinWageTerms`(値・出どころ・行の kind・つなぎ・`enforced_by`=`machine`/`bridge`/`none`)・`min_wage_terms`。`min_wage_floor` は `min_wage_terms(...).floor()` に=前の「machine でない行は止める」を「machine かつなぎのときだけ値・ほかは `(None, "<kind>:rules:…")`」に |
| `economy/wages.py` | `min_wage_terms`(anchors の写し口)・`floor_with_shortfall`(`apply_floor` を呼び、床を機械が当てる行だけ上げた額を返す・下回った体と額は常に返す) |
| `economy/taxes.py` | 〔検収 M1〕`_bridge_row`(申告の期限のつなぎの読み口)が、行の `params.bridge` が machine のつなぎであることも確かめる(無ければ止める) |
| `economy/stage2.py` | `SHORTFALL_KEY`・`SHORTFALL_COUNTS`・`SHORTFALL_SCOPE`・`_empty_shortfall`・`MoneyStage2._below_at_start`・`_count_min_wage_shortfall`。組み立てで `check_rule_bridges()`(壊れていればランの始めに落ちる)。給料日(`payroll`)の床の 3 行を `floor_with_shortfall` に・器に積む。2-1 の道(賃金の表の無い写し=月の時間 × 時給)は前から床の式が無い=数えるだけ・`last.enforced_by="none"` |

器の欄(manifest の `economy.stage2.rules.minimum_wage_shortfall`・観測):

| 欄 | 中身 |
|---|---|
| `rule` | `minimum_wage.tokyo` |
| `scope` | `run`(このランの始めからの積算=再開のランでは再開の後の分だけ・〔検収 L3〕) |
| `paydays` | 数えた給料日の数 |
| `checked` | 見た雇用の行の数(給料日ごとの和) |
| `below_rows`・`below_amount` | 床を当てる直前に時給(月 ÷ 月の時間の目安)が最低賃金を下回った体の数と不足の合計[円] |
| `lifted_rows`・`lifted_amount` | つなぎの床が上げた体の数と額 |
| `violation_rows`・`violation_amount` | 下回ったまま払った体の数と額(=起きた違反)。つなぎで床が掛かる道(occupation)では 0・床の無い道(2-1 の道・つなぎの無い表)では数える(〔検収 L2〕) |
| `below_at_start` | 組み立ての日に効いている最低賃金を時給が下回る体の数(つなぎの有無に依らない・賃金の表の無い写しと版の無い日は null・〔検収 L4〕) |
| `last` | 最後の給料日の読み(`asof`・`yen_per_hour`・`source`・`kind`・`enforced_by`(その給料日に床を当てた道=2-1 の道は `none`)・`bridge_ledger_id`・`wage_path`) |

- 鍵の名に `open`・`tick` は無い(試験で見る)。日次の記録には入れない(manifest だけ・親の判断)。
- 金の流れは変えない: 床を当てる行では `floor_with_shortfall` の払う額と印が `apply_floor` の戻りと 1 バイト同じ(試験)。
- 前からの `wage_build.floor_at_start` は `min_wage_floor` を使う=つなぎの無い表では「床に当たる体 0」と出る(前の形のまま)。
  下回る体の数は器の `below_at_start` に残す。

## 3. 法定労働時間

- `labor.statutory_hours`(週 40 時間・1 日 8 時間)は R-118 の写しで前から `kind: human`。機械が止める側はコードに無い
  (`engine/calendar3/layer.py` の `labor_params` は `enforced: False`=読むだけ)。つなぎを足すと「機械が止めている」と
  誤って読めるので足していない。
- 超えた数は前から数えている: カレンダー 3 の層 `labor:over_week_hours`・`labor:over_day_hours`・`labor:short_rest_days`
  (manifest の `labor_over`)と、持ち場の層 `labor:over_day_hours`(つなぎの台帳 `DOC-ca3-labor-record-only`・
  `DOC-du1-labor-record-only`)。どちらも `engine/` の中=本段では触らない。
- 経済の側には勤務の時間の計算が無い(`wage_hours` は賃金構造の統計の月の時間の目安で、勤務の記録ではない)=経済の器は
  「法定労働時間は数えない(0 件・計算の口なし)」と宣言(`_empty_shortfall` の docstring)。

## 4. 既定での件数と 1 バイト不変(実測)

計器 `tools/measure_shortfall.py`(読むだけ・JSON を標準出力へ・引数 `[体数] [日数] [--no-bridge]`)。世界資産・seed 1・
開始日 2026-08-24・腕は既定(経済の段階 2 on・賃金 occupation)。給料日は 1 日目の締め(2026-08-25・効いている版 1,226 円)。
前=本体の src(土台 `c0729a4` と同じ中身)、後=作業木の src(表 `ec51280c383454a5`=`remove_at` を段の語にそろえる前・`params.bridge` の文の欄だけが違う=挙動は同じ)。対照=後の src で最低賃金の
3 版の `params.bridge` をメモリの中で消した表(`--no-bridge`)。

**`final_hash` と manifest の `state_hashes` は、最後の checkpoint の値で、2 日のランでは給料日の締めより前に取られる=賃金の
差を見分けない**(つなぎを外しても 2 日のランの `final_hash` は同じ=検収 M2)。3 日のランなら給料日の締めの後の日が入る。
1 バイト不変の根拠は、日の締めごとのハッシュ・流れの表の sha・保存則・賃金の計器に置く。

3 日のラン(日の締めのハッシュは behavior の先頭 16 桁・0 日目/1 日目(給料日)/2 日目):

| ラン | 日の締めのハッシュ | 流れの表の sha | 賃金の計器の sha・額面 | 保存則 | 器 |
|---|---|---|---|---|---|
| 1,000 体 前 | cbfa0dcc17ac0a3c / 6f37eda433a6312e / b3cc74b1489e1311 | 2092bb1216d63a9e | 8f40174d505a0175・201,493,397 | 3 日とも残差 0 | (無し) |
| 1,000 体 後 | **同じ** | **同じ** | **同じ** | 同じ | below 93・4,776,962・lifted 93・violation 0・below_at_start 142・`enforced_by` bridge |
| 1,000 体 対照(つなぎ無し) | cbfa0dcc17ac0a3c / **8d3591d7adcf8180** / **10a50e8cd794d176** | **bc23746b5a8864f7** | **6fd90eb666b4035e・196,716,435**(差 4,776,962) | 3 日とも残差 0 | below 93・lifted 0・**violation 93・4,776,962**・below_at_start 142・`enforced_by` none |
| 5,000 体 前 | 43fb264e3c6e08a1 / 9e939c99a8647ce5 / ec4647ae97a1ad45 | 43aa3a2da5c02cbb | 9989bef9cf68935b・897,159,093 | 3 日とも残差 0 | (無し) |
| 5,000 体 後 | **同じ** | **同じ** | **同じ** | 同じ | below 531・29,642,965・lifted 531・violation 0・below_at_start 924・`enforced_by` bridge |

- 3 日のランの `final_hash`: 1,000 体 前=後 a4e040d1c44e9c1e・対照 40c2b089b4b02700 / 5,000 体 前=後 095a4a900b93ed84。
- 前と後の JSON の `state`(`final_hash`・`state_hashes`・`state_hashes_end_of_day`・日ごとの日の締めのハッシュ)と
  `money`(流れの表の sha・保存則・賃金の計器・`wage_model.floor`・`wage_build.floor_at_start`)の欄は全部同じ。
- 2 日のラン(前の記録の数・`final_hash` 1,000 体 64cce6fd…・5,000 体 c689b20d…)も流れの表の sha(b7dfa80b7448bb3e・
  a69061ef2f12927e)と計器が前と後で同じだった。

## 5. 試験

- 新: `tests/economy/test_min_wage_human_bridge.py`(**20 本**)。つなぎのある行の一覧(最低賃金の 3 版と申告の期限)・
  どれも human+machine のつなぎ・法定労働時間は human でつなぎ無し・kind の並びが表と同じ・つなぎの欄の検査(負の 7 本)・
  床が kind とつなぎで決まる(machine・human+つなぎ・human だけ・norm・版の無い日)・`floor_with_shortfall` が
  `apply_floor` と 1 バイト同じ・器の初期値(`scope`・`below_at_start`)と鍵の名・**正の対照**(床を下回る合成の 40 体=件数と額が
  立つ・つなぎが上げる・違反 0・前からの計器と同じ数)・**つなぎを外した表**(下回ったまま払う=違反が立つ・`below_at_start`
  が残る・保存則の残差 0)・**負の対照**(高い賃金=0 件)・版の無い日・2-1 の道(`enforced_by` none)・〔検収 L1〕給料日に
  効いていない後の版のつなぎが壊れていても組み立てで落ちる・〔検収 M1〕申告の期限のつなぎを `params.bridge` から読む
  (つなぎの無い human の行はつなぎの読み口が止める)。
- 直した: `tests/engine/rules/test_rules_table_schema.py`(最低賃金の kind の 2 か所 machine → human)・
  `tests/engine/rules/test_rules42_table.py`(前の行の値の比べで `bridge` を除く・machine の行の読み手の集合から最低賃金を
  外し human+つなぎを確かめる・申告の期限の行の値の比べで `bridge` を取り出して台帳の値と比べる)。

## 6. 試験の結果

- 実装役の回(検収の直しの後・最終の状態・`-n 6 --dist loadfile`・slow を含む): `tests/economy tests/engine tests/build_pop
  tests/c8`(`--ignore=tests/c7`)= **3,936 passed・1 skipped・失敗 0**(33 分)。
- 最後の直し(`remove_at` の段の語・`rule_id`)の後: **3,935 passed・1 skipped・1 failed**(35 分)。落ちた 1 本は
  `tests/engine/bridging/test_bridging_ledger.py::test_rule_ids_point_to_the_rules_table`=台帳に行が無いため(親が道具を回すと通る・
  写しの台帳で確かめた・§7)。
- 直しの前の回: 3,933 passed・1 skipped・1 failed(落ちた 1 本は `tests/engine/test_geometry_c9.py::
  test_p2_edge_geometry_under_300ms_at_400k_agents`=40 万体で 300 ms の性能の門・ほかの作業木の試験と同時で機械が混んでいた・
  単独で回し直して 26 passed)。
- 近くの試験だけ(直しの後): `tests/economy/test_min_wage_human_bridge.py tests/engine/rules tests/economy/test_wage_occupation.py
  tests/engine/bridging`=128 passed。

## 7. つなぎの台帳

- 冪等の道具 `tools/add_bridges_s2rules.py`(親が回す): `DOC-s2rules-min-wage-floor-bridge` を 1 行足す
  (`remove_at` 7・`remove_basis` inferred・`conf` expedient・`declared_in` は本記録・`code_at` は anchors/wages/stage2)。
  写しの台帳で 2 回回して同じバイト(冪等)・形(indent 1・LF)のまま・`engine.bridging.ledger.load` が読めることを確かめた。
- 申告の期限の行 `DOC-rules42-tax-remit-machine` は台帳の側を変えていない(表の `params.bridge` がその行を `ledger_id` で指す)。
- 行に `rule_id: minimum_wage.tokyo` を付けた(親の判断)。試験 `test_rule_ids_point_to_the_rules_table` の固定の一覧に
  `DOC-s2rules-min-wage-floor-bridge` を足した=**親が道具を回して台帳に行を足すまで、作業木ではこの試験 1 本が落ちる**。
  写しの台帳に道具を回した上で、この試験と `test_every_row_has_remove_at_declared_in_and_conf`・`test_declared_places_exist`
  を通した。

## 8. 空欄と自己申告

- 2-1 の道(賃金の表の無い写し)には前から床の式が無い。既定の時給は最低賃金なので下回りは 0。合成の低い時給
  (`plan.hourly`)なら下回ったまま払い `violation_*` に立つ(試験)。床を足すかは本段の外(1 バイト不変の約束)。
- 器は manifest だけ(日次の記録には出していない)。再開のランでは 0 から積む(`scope: "run"`)。
- 「検知と反応の口」(気づいた人・本人・監督が違反を知って反応する)は本段の外。器は数えるだけで、世界の誰にも届けない。
- 端の値は前からの `apply_floor` を引き継ぐ(0 円で時間のある体は下回りに数えて床まで上げる・負の値と時間の無い体は飛ばす・
  検収 L5)。0 円の体が「値の無い体」の印でないかは構築の側で確かめる価値がある。
- 設計書の写し(R-118 の 3 か所・決定台帳 D-R2-3 の「最低賃金 1,226 円フロア(mechanism)」)は直していない=訂正の伝播は
  親が文書で行う(検収 L6)。
- 同じ判定(「現実でその場で物理的に止まるか」)を残りの machine の行(`labor.overtime_premium`・`credit.interest_cap` など)に
  当てるかは段の外=親が判断待ちに出す。

## 9. 問い

1. 発注文の土台は `a09809c` だったが、作業木の先端は `c0729a4`(本体の HEAD と同じ)だった。この先端の上で作った。
2. (解決)`bridge` は `params.bridge` の 1 つに統一。行の欄への移動(形式の版 3)は次の段(engine)。
3. (解決)`conf` は台帳の語 `expedient` のまま。
4. (解決)台帳の行に `rule_id: minimum_wage.tokyo`・remove_at 7 のまま・表の `remove_at` は段の語で統一(文は `remove_note`)。
5. (親へ)R-118・D-R2-3 への訂正の伝播。
6. (解決)器は manifest だけ(日次の記録には入れない)。

## 10. 検収(review.md)の直し

| 番号 | 直したこと |
|---|---|
| M1 | 申告の期限の行にも `params.bridge`(台帳の行の値)・`taxes._bridge_row` が machine のつなぎを確かめる・試験の「ほかの行につなぎ無し」を「つなぎのある行の一覧」に。行の欄への移動は次の段(engine) |
| M2 | 1 バイト不変の根拠を日の締めのハッシュ・流れの表の sha・保存則・賃金の計器に直し、3 日のランの前・後・対照の値を表に(§4)。`final_hash` は 2 日のランでは給料日の締めの前の値と明記 |
| L1 | 組み立てで `check_rule_bridges()`=表の全部の版のつなぎを検査(壊れていればランの始めに落ちる) |
| L2 | 2-1 の道は `last.enforced_by="none"`・docstring を「つなぎで床が掛かる道では 0・床の無い道では数える」に |
| L3 | 器に `scope: "run"`(再開で 0 に戻る) |
| L4 | 器に `below_at_start`(つなぎの無い表でも組み立ての日に下回る体の数を残す) |
| L5・L6 | 前からの挙動・本段の外=§8 に書いた |
| 問い 3 | conf は台帳の語のまま(§1) |
| 問い 5 | 段の外=親の判断待ち(§8) |
