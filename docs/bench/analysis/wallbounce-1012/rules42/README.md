# 第 4 期 4-2 権利台帳と規則の表の中身(R-118 §7-1 の「4-3 に束ねる分」・小さな版上げ)の記録

- 実装役 Opus 5.5。作業木の枝 `4-2/rules-and-payroll`(土台 `9743268`=本体の先端・本体の世界は W21)。commit は親。
- 正: [R-118](../../../../research/v2-r118-rights-and-rules-contents.md)(§2・§3・§4・§5・§7-1・§8・§10)と付属
  [19 行](../../../../research/v2-r118-rules-rows-draft.json)・[等級表](../../../../research/v2-r118-standard-remuneration-grades.json)、
  [計画](../../../../design/v2-implementation-plan-2026-10-12.md) 第 4 期 4-2・§3 版上げ 3 回目、PENDING 仮-40 の親の判断(Q1〜Q7=
  仮採用)、CLAUDE.md §3・§4(保存則=取引の保存はエンジン強制・faucet/sink は全登録・残差科目)、回答 10-13b §0-6・§0-7。
- 新しい一次出典は取りに行っていない(R-118・R-106 の値だけ)。空欄は空欄のまま(§7)。数は実測。生の出力は作業木の `_bc/`
  (git の外)。絶対パスなし。
- **〔独立検収の直し・載せ替え〕§11・§12 が正**([review.md](review.md)=条件つき受入 高 1・中 2・低 9 → 全部直した・本体の先端
  `6f07eff` へ載せ替えた)。§0〜§10 は直す前の記録(数と形は §11・§12 の表で上書きする)。

## 0. 結論

- 規則の表を形式の版 2(`norm`・下限の印)にし、R-118 の 19 行+消費税の申告の期限の 1 行を足した。machine の行は全部読み手と
  一緒に入れた(給料日・レジ・日の締めの 8 行+呼び手の無い器の 4 行)。
- **給料日に税と社会保険を天引きし、雇用主の分も払う**(既定=腕 `SHIBUYA_RULES_42=on`)。5,000 体の給料日(2026-08-25):
  額面 8.97 億円・本人の分 2.00 億円(2,719 体)・雇用主の分 0.78 億円・政府の口座 0.01 億円 → 2.78 億円。保存則は毎日 残差 0。
- **レジの消費税は店の預かり金に積み、申告の期限(2027-03-31)に政府へ移す**(Q1)。2 日のランでは納付は起きない=預かり
  119 万円(594 店)が店の現金に残る・預かり金の検算は毎日 残差 0。
- 総量規制と利息の上限の検査を信用の器に足した(呼び手なし=結果不変)。カードの枠の割合は空欄。
- 権利台帳に `credit`・`road_segment`・`signboard`・`credit_contract`(行 0)・閉じた表に `own → store`。
- **byte-check**: 腕 off は本体 `9743268` の写しと 19 構成 × 25 欄が全部同じ(旧値の再現)。既定(on)は 1 日のランでも 4 欄
  (final・full_last・behavior_last・end_of_day=帳簿の残高と腕の行 TXD)が動き、行動の 21 欄(呼数・テープ・行動の件数・食事・
  会話・出動ほか)は 19/19 で同じ。**発注の「1 日は不変のはず」とは違う**(Q1 でレジの税が政府でなく店の現金に残るため=§9 の 1)。
- 性能: 2 日のランの壁時計 86.0 → 86.3〜86.9 秒・判断の呼び 143,286 回は同じ・状態の外のバイト +18,906 B/checkpoint
  (預かり金 2,337 店 × 8 B ほか)。

## 1. 作ったもの

| # | 中身 | 場所 |
|---|---|---|
| 1 | 規則の表を形式の版 2 に(`kind` に `norm`・`asof_basis`=`lower_bound` の印)。R-118 の 19 行と消費税の申告の期限の 1 行(R-106 §3-1)を足した(6 → 26 行・id 4 → 24)。§5 ② の 2 行の出典の版を世界の時点の版に直した。表の sha `4dda40d8f83d6a3f` → `8ed5b777fc169907` | `docs/design/rules-table.json`・`src/shibuya/engine/rules/table.py` |
| 2 | 給与の天引き(源泉所得税=電算機計算の特例・住民税の特別徴収・健保と介護・支援金・厚年・雇用保険)と雇用主の分 | `src/shibuya/economy/taxes.py`・`src/shibuya/economy/stage2.py`(`payroll_deductions`・`_payroll_law`) |
| 3 | 加入の判定の材料(W21b の役割と週の時間の目安・雇用主の被保険者の数・学生・年齢)と腕 `SHIBUYA_RULES_42` | `src/shibuya/engine/economy_rules.py`・`src/shibuya/engine/economy_stage2.py`(`Stage2Plan.law`・見出しと再開の検査) |
| 4 | 店の預かり消費税(Q1): レジの税を預かり金に積み、申告の期限の日の締めに店 → 政府 | `src/shibuya/economy/tax_deposit.py`・状態台帳の腕の行 `TXD` |
| 5 | 保存則の科目: 登録の流れ 4 本(本人 → 政府・雇用主 → 政府・店の担当従業者の雇用主 → 政府・預かり金の納付)と検算 `tax_deposit_check` | `src/shibuya/economy/accounts.py`・`src/shibuya/economy/checks.py` |
| 6 | 総量規制の検査と利息の上限の器(呼び手なし)・カードの枠の割合は空欄 | `src/shibuya/economy/credit.py` |
| 7 | 権利台帳の種類 `credit`・物の種類 `road_segment`・`signboard`・`credit_contract`(行 0)・閉じた表に `own → store` | `src/shibuya/engine/rights/ledger.py` |
| 8 | つなぎの台帳 13 行を足し、`DOC-ec21-payroll-deduction-blank` を removed に | `docs/design/bridging-ledger.json` |

## 2. 規則の表の行と読み手

| 行 | kind | asof(印) | 読み手 | 呼び手 |
|---|---|---|---|---|
| `income_tax.withholding_monthly` | machine | 2026-01-01 | `economy.taxes.income_tax_withholding` | 給料日 |
| `resident_tax.special_collection_tokyo_ward` | machine | 2026-06-01 | `economy.taxes.resident_tax_monthly` | 給料日 |
| `health_insurance.kyoukai_tokyo` | machine | 2026-03-01 | `economy.taxes.deductions`・`enrollment`(等級表・加入の範囲) | 給料日 |
| `child_support_levy.rate` | machine | 2026-04-01 | `economy.taxes.deductions` | 給料日 |
| `pension.employees_rate` | machine | 2017-09-01 | `economy.taxes.deductions`(等級表) | 給料日 |
| `employment_insurance.rate_general` | machine | 2026-04-01 | `economy.taxes.deductions`・`enrollment`(〜2027-03-31) | 給料日 |
| `consumption_tax.invoice_rounding` | machine | 2023-10-01 | `economy.taxes.invoice_rounding` | レジ(記録) |
| `consumption_tax.filing_deadline`(20 行目) | machine | 2026-10-01(下限) | `economy.taxes.filing_deadline`(課税期間の末日に効く版) | 日の締め |
| `consumption_tax.reduced_rate` | machine | 2019-10-01 | `economy.taxes.reduced_rate` | なし(器) |
| `credit.total_volume_cap` | machine | 2025-10-01(下限) | `economy.credit.total_volume_check` | なし(器) |
| `credit.interest_cap` | machine | 2010-06-18(下限) | `economy.credit.interest_cap_rate` | なし(器) |
| `labor.overtime_premium` | machine | 2026-06-24(下限) | `economy.taxes.overtime_premium` | なし(器) |
| `consumption_tax.standard_rate`(既存) | machine | 2019-10-01 | `economy.anchors.consumption_tax_rate` | レジ |
| `minimum_wage.tokyo`(既存・3 版) | machine | 2025-10-03 ほか | `economy.anchors`・`economy.wages` | 給料日 |
| `food_business.licence` | human | 2025-06-01(下限) | なし(許可の行は空=Q5) | ― |
| `building_lease.termination_notice` | human | 2026-05-21(下限) | なし | ― |
| `labor.statutory_hours` | human | 2026-06-24(下限) | なし | ― |
| `road_use.police_permit` | human | 2026-06-14(下限) | なし | ― |
| `road_occupancy.shibuya_ward_road` | human | 2026-04-01 | なし | ― |
| `outdoor_ad.tokyo_permit` | human | 2026-01-01(下限) | なし | ― |
| `national_pension.premium` | human | 2026-04-01 | なし(本人が納める) | ― |
| `national_health_insurance.shibuya` | human | 2026-04-01 | なし(世帯主が納める) | ― |
| `late_night_alcohol.residential_ban`(既存) | human | 2025-11-28(下限=印を足した) | W7(構築側) | ― |
| `labor.weekly_rest_day`(既存) | human | 1947-09-01 | W20(構築側) | ― |

- norm の行は 0(罰則の無い決まりの行=路上飲酒などは R-118 の 19 行に無い)。種類と形式の版だけ足した。
- machine の行はどれも読み手がある(試験 `test_every_machine_row_has_a_reader`)。読み手の無い machine の行は残していない。
  器の 4 行(軽減税率・総量規制・利息の上限・割増)は読み手の関数だけあり、呼び手は無い(結果不変)。
- 19 行に足した値の欄: 健保の `grades`(50 級)・`full_time_share`(3/4)・`short_time_coverage`(51 人・週 20 時間・学生を除く・
  2027-10 から 36 人)、厚年の `grades`(32 級)、雇用保険の `min_weekly_hours`(20)。等級表は付属の JSON の写し(試験で一致を
  見る)、加入の範囲は R-118 §2-3(#5)と行の note の値。ほかの欄は付属の JSON のまま(試験が id・kind・asof・出典・値・note を
  突き合わせる)。
- 下限の印(Q6)は 10 行: note に「下限」とある 8 行(既存の深夜酒類の行を含む)と、note が「asof は読んだ版の施行日」と書く
  2 行(利息の上限・割増=条の施行の初日ではない)。申告の期限の行は R-106 が読んだ版(2026-10-01)が下限=世界の時点 2026-07-13
  には効いていない。読み手は課税期間の末日(2026-12-31)の版を引く。

## 3. 天引きの式と 1 人の例

給料日(毎月 25 日・土休なら前の営業日)の日の締めに、雇用の行の体ごとに(`economy.taxes.deductions`):

1. **標準報酬月額**=今月の額面を等級表の下限で引く(健保 50 級・厚年 32 級)。定時決定と「前月分を控除」の 1 か月のずれは
   入れない(`DOC-rules42-standard-remuneration-month`)。
2. **健保**=標準報酬 ×(9.85%+40〜64 歳は介護 1.62%)・**支援金**=健保の標準報酬 × 0.23%・**厚年**=厚年の標準報酬 × 18.3%。
   どれも本人の分=全額の半分を 50 銭の決まり(50 銭以下は切り捨て・超えれば切り上げ)で円に・雇用主の分=全額の 1 円未満の
   切り捨て − 本人の分。
3. **雇用保険**=額面 × 5/1,000(本人・50 銭の決まり)・額面 × 8.5/1,000(雇用主・切り捨て)。率は 2027-03-31 まで(行の
   `valid_until`=その後は版なし=0)。
4. **源泉所得税**(電算機計算の特例・甲欄・扶養 0 人=Q7): A=額面 − 本人の社会保険料等、B=A − 給与所得控除(別表第一・1 円未満
   切り上げ)− 基礎控除(別表第三)、税=B × 税率 − 控除額(別表第四)を 10 円未満で四捨五入。
5. **住民税**(Q4): (額面 × 12 ×(都 4%+区 6%)+均等割 1,000+3,000+森林環境税 1,000)÷ 12 の切り捨て。令和 8 年度の行
   (2026-06-01〜)の前は 0。
6. 本人の社会保険料等が額面を超える行は何も天引きしない(計器 `over_gross`)。本人の分の合計は額面を超えない(住民税を削る)。

お金の流れ: 雇用主 → 世帯の口座=額面(`金:賃金`)・世帯の口座 → 政府=本人の分の合計(`金:税`)・雇用主 → 政府=雇用主の分の
合計(雇用主ごとに 1 行)・外界 → 雇用主=額面+雇用主の分(原資)。原因はどれも `Process("payroll")`。外の雇用主の体は外界が額面を
払い、本人の分だけ政府へ。

**1 人の例**(試験 `tests/economy/test_rules42_payroll.py`・額面 300,000 円・45 歳・週 37 時間・雇用主の被保険者 100 人・
2026-08-25):

| 項目 | 本人 | 雇用主 | 筋道 |
|---|---|---|---|
| 健保+介護 | 17,205 | 17,205 | 標準報酬 300,000 × 11.47%=34,410 の折半 |
| 支援金 | 345 | 345 | 300,000 × 0.23%=690 の折半 |
| 厚年 | 27,450 | 27,450 | 300,000 × 18.3%=54,900 の折半 |
| 雇用保険 | 1,500 | 2,550 | 300,000 × 5/1,000・8.5/1,000 |
| 源泉所得税 | 6,250 | ― | A=300,000 − 46,500=253,500・給与所得控除 253,500 × 30%+6,667=82,717・基礎控除 48,334 → B=122,449 × 5.105%=6,251.0 → 6,250 |
| 住民税 | 30,416 | ― | (3,600,000 × 10%+5,000)÷ 12 |
| 合計 | **83,166**(手取り 216,834) | **47,550** | |

- 50 銭の決まりの例: 1 級 58,000 円の健保 5,713.0 の折半 2,856.5 → 本人 2,856・雇用主 2,857(額表の「給与から控除」と同じ)。
  支援金 133.4 の折半 66.7 → 本人 67・雇用主 66。
- **特例の式と月額表**(R-118 §1-2 #9 の区分 105,000〜107,000 円=甲欄 扶養 0 人 170 円): 特例は 105,000 円で 130 円(差 40)・
  区分の中央 106,000 円で 180 円(差 10)・106,999 円で 230 円(差 60)=答申の「中央で 0〜10 円・端で最大 60 円」と同じ。月額表の
  105,000 円未満は 0 円だが、特例は A が 102,501 円を超えると正(最大 130 円=区分の外の差・§9 の問い)。
- 住民税の元を額面 × 12 にした(Q4)ので、所得控除の無い分だけ重い(300,000 円で月 30,416 円=額面の 10.1%)。§9 の問い。

## 4. 加入の判定

`economy.taxes.enrollment`(材料=`engine.economy_rules.PayrollInputs`):

| 判定 | 規則 | 材料 |
|---|---|---|
| 社会保険(健保・介護・支援金・厚年) | 週の時間の目安 ≥ 30(通常の労働者 40 時間 × 3/4)/ 20〜30 時間は雇用主の被保険者 ≥ 51 人かつ学生でない | W21b の雇用の行の `weekly_hours_hint`・組織ごとの週 30 時間以上の雇われる側の行の数・体の種別 STUDENT |
| 介護 | 社会保険の加入者で 40〜64 歳 | 母集団の `age` |
| 雇用保険 | 週の時間の目安 ≥ 20(31 日以上の見込みは全員あり) | 同上 |
| 源泉と住民税 | 雇われる側(業主・家族従業者・内職でない) | W21b の `role` |
| 何もしない | 業主・家族従業者・内職(本人で納める=human) | 同上 |
| 判定の材料なし | 役割も時間も無い体(W16 の残す体・外の雇用主の体・時間の欄が空の行)=社会保険と雇用保険は未加入・源泉と住民税は天引き | ― |

- 全母集団(345,858 体)で材料のある体 147,065(W21b の雇用の行と 1 対 1)・時間のある体 134,881・雇用主の被保険者 51 人以上の体
  71,918・学生(種別 STUDENT)33,385。組み立ての時間 0.14 秒(全母集団)。
- 年齢の上限(厚年 70 歳・健保 75 歳)・役員の雇用保険の除外は答申に無い=入れていない(`DOC-rules42-enrollment-basis`)。

## 5. 消費税の預かり金(Q1)

- レジ: 税込の額 × 率/(1+率) の切り捨て(1 回の購入=1 枚のレシート=1 つの税率=規則の表の端数の行)を店ごとの預かり金に積む
  (`TaxDeposit.collect`・課税期間=レジの日の年)。お金は店の現金のまま(店はその間も使える)。店の売上の写し `pois.revenue` は
  今までどおり税抜き(`last_purchase_tax`=積んだ額)。
- 期限: 課税期間の末日に効いている `consumption_tax.filing_deadline` の版で、個人事業者の決まり(翌年 3 月 31 日)を全部の店に
  当てる(2026 年の分=2027-03-31・`DOC-rules42-tax-deadline`)。期限の日以後の日の締めに店 → 政府(`金:税`・`Process("register")`)。
  店の現金が足りない分は残り、次の日の締めにまた移す(計器 `unpaid_rows`)。
- 保存則: 預かり金は店の現金の中=部門の残高の検算(faucet − sink = ΔM)はそのまま。科目「店の預かり消費税」の検算
  `tax_deposit_check`=積んだ額の累計 − 移した額の累計 − 残高=0 を日次の記録の `economy.stage2.tax.deposit_check` に毎日。
- 状態: 状態台帳の腕の行 `TXD`(behavior・required・腕 `rules-42`)=`held`(年 → 店ごとの額)と `totals`。腕 off のランは持ち主が
  無い=2 つのハッシュと状態のファイルは 4-2 の前と同じバイト。再開(日の境目と給料日の昼)=通し(試験・slow)。
- 合成の試験: 期限をまたぐラン(2026-08-24 → 2027-03-30 → 03-31 → 04-01)で、03-31 の締めに積んだ額の全部が政府へ・店の現金が
  足りない日は残って翌日に移る。

## 6. 権利台帳

- 権利の種類 `credit`(5 つ目・object=信用の器の行=番号の空間 `credit_contract`)、物の種類 `road_segment`・`signboard`。許可は
  店・道路の区間・看板に取れる。所有は区画・住まい・店。番号の空間と種類は末尾に足した=前のコードは不変。
- 行は 0 で始める(道路と看板は第 5 期・信用は借りる判断の段)。初期の行(段 10)は変えていない=W21b の店の持ち主の 286 行は
  閉じた表の中になったが、入れていない(`DOC-pop43-store-owner-deferred` の注・§9 の問い)。W21b の表の `in_closed_table` の列は
  世界の作り直しまで偽のまま(`data/world/**` は書いていない)。
- manifest の `rights.by_kind` に `credit`、`by_object_kind` に 3 つの種類が 0 で出る。

## 7. つなぎの台帳と空欄

- removed: `DOC-ec21-payroll-deduction-blank`。
- 直した: `DOC-ec21-register-tax-rounding`(端数は表の行を読む=残るのは軽減税率なし・外す段 7)・
  `DOC-ec21-employer-funding-exogenous`(原資=額面+雇用主の分)・`BR-RIGHTS-LICENCE-BLANK`(Q5=この段では取得しない)・
  `DOC-pop43-store-owner-deferred`(閉じた表に店)。
- 足した 13 行(どれも expedient・記録=本書): `DOC-rules42-legacy-switch`(next-bump)・`-dependents-zero`・`-resident-tax-base`・
  `-enrollment-basis`・`-full-time-hours`・`-rounding`・`-standard-remuneration-month`・`-remit-timing`・`-tax-deadline`・
  `-card-limit-blank`・`-credit-lender-kind`・`-outside-employer-share`・`-employer-levy-missing`(外す段は計画に無い=7・inferred)。
- 台帳 585 → 598 行(active 566 → 578)。
- 空欄のまま(R-118 §8): カードの枠の割合・割増の政令の率・住民税の控除・定時決定の時期・雇用保険の端数・子ども・子育て拠出金
  (事業主 0.36%)の行・年齢の上限。

## 8. 動いた量・保存則・性能

### 8-1. 1 日の 19 構成(byte-check・mock/classical 5,000 体・seed 1・テープつき・W21 の世界)

| 比べ方 | final が同じ | 25 欄が全部同じ | 動いた欄 | 記録 |
|---|---|---|---|---|
| 本体 `9743268` の写し vs 腕 off | 19/19 | 19/19 | なし | [bc19_head_vs_off.json](bc19_head_vs_off.json) |
| 本体 `9743268` の写し vs 既定(on) | 0/19 | 0/19 | final・full_last・behavior_last・end_of_day(19/19 とも この 4 欄だけ) | [bc19_head_vs_on.json](bc19_head_vs_on.json) |

- 既定の final(例): `w6_v3_default` `eb759bb4…` → `bb86f898…`・`w6_golden_null_arm` `90582d70…` → `dcebb7c1…`。呼数・テープの列の
  sha・行動の件数の sha・食事・出動・気づきは 19/19 で同じ=体の行動は変わらず、帳簿(店の現金に税が残る・政府は受け取らない)と
  腕の行 TXD が behavior-hash と full-hash に入った分だけ動いた。
- 状態の外のバイト: +18,906 B/checkpoint(19/19 とも同じ=TXD の預かり金 2,337 店 × 8 B と累計)。

### 8-2. 給料日を含む 2 日(5,000 体・`w6_v3_default`・開始 2026-08-24・1 本ずつ・[runs_2day.json](runs_2day.json))

| 量 | 本体の写し | 既定(on) | off |
|---|---|---|---|
| final | `88b1d279…` | `a5a3eb6f…` | `88b1d279…`(本体と同じ) |
| 払った額面(2,726 体) | 897,159,093 | 897,159,093 | 897,159,093 |
| 本人の分(世帯の口座 → 政府) | 0 | 200,226,913(2,719 体) | 0 |
| うち 健保+介護・支援金・厚年・雇用保険 | ― | 27,338,796・588,405・45,385,830・2,646,604 | ― |
| うち 源泉所得税・住民税 | ― | 33,638,000・90,629,278 | ― |
| 手取り | 897,159,093 | 696,932,180 | 897,159,093 |
| 雇用主の分(雇用主 → 政府・995 雇用主) | 0 | 77,812,151(健保 27,339,126・支援金 588,735・厚年 45,385,830・雇用保険 4,498,460) | 0 |
| 原資(外界 → 雇用主) | 634,445,184 | 712,257,335(+雇用主の分) | 634,445,184 |
| 政府の口座 | 1,192,445(レジの税) | 278,039,064(天引きだけ) | 1,192,445 |
| 店の預かり消費税 | ― | 1,192,445(594 店・期限 2027-03-31) | ― |
| 店の現金の合計 | 297,973,286 | 299,165,731(+預かり金) | 297,973,286 |
| 世帯の預金の合計 | 1,621,037,317 | 1,420,810,404(−本人の分) | 1,621,037,317 |
| 加入(社会保険・介護・雇用保険・材料なし) | ― | 1,484・694・1,548・941 | ― |
| 判断の呼び | 143,286 | 143,286 | 143,286 |

- 雇用主の分の健保が本人の分より 330 円多いのは端数(本人=50 銭の決まり・雇用主=全額の切り捨て − 本人の分)。
- 外の雇用主の体 715 人の額面 2.42 億円は外界から・本人の分だけ政府へ(雇用主の分は記録しない)。店の担当従業者の雇用主(店)の
  分は 0(担当の体はどれも判定の材料なし=W16 の丸振りの体)。

### 8-3. 保存則の検算

- 2 日とも毎日 残差 0・登録の無い流れ 0(本体・on・off)。`RunResult.conserved` は 3 本とも真。
- 預かり金の検算(積んだ − 移した − 残高): 0 日目 686,409 − 0 − 686,409=0・1 日目 1,192,445 − 0 − 1,192,445=0。
- 合成の台帳で期限をまたぐ試験(2026 → 2027-03-31 → 04-01): 期限の締めに全部移る・足りない店は翌日・検算 0。

### 8-4. 性能(§0-7)・試験

| | 本体の写し | 既定(on) | off |
|---|---|---|---|
| 1 日 19 構成の壁時計の合計[秒] | 810.5 | 737.9 | 746.2 |
| 2 日の壁時計[秒] | 86.0 | 86.3 / 86.9 | 89.1 |
| 2 日の最大の作業集合[MB] | 515.0 | 526.7 / 509.4 | 491.9 |
| 判断の呼び(2 日・LLM 0) | 143,286 | 143,286 | 143,286 |

- 5,000 体・seed 1・Windows 11・x86-64。同じ機械で別の作業木の試験とランが並行していた=壁時計と作業集合は揺れの中(悪化は
  見えない)。給料日の天引きの計算は配列演算(5,000 体で計器に出ないほど小さい・加入の材料の組み立ては全母集団で 0.14 秒)。
  バイト予算: 預かり金=店の数 × 16 B(課税期間 2 つ)の定数(成長の宣言の fixed に足した)・体あたりは 0。
- golden の張り替え(final が動いた試験=呼数はどれも同じ): `test_state_ledger_10b`(T7)・`test_state_checks_10f`(K19)・
  `test_presence_executor`(W21 の行)・`test_env_and_sections_10f`(写しの検査)・`test_intent_chooser`・`proximity/test_runs`・
  `test_relations_tenure`・`test_classical_social`・`body/test_meal_default_w17`(定数経由)。各行の注に前の値(=腕 off で戻る値)。

### 8-5. 試験

- 新しい試験 44 件: `tests/engine/rules/test_rules42_table.py`(19 行の写し・`norm`・下限の印・既存の値・読み手・R-118 の表との
  写し検査)・`tests/economy/test_rules42_payroll.py`(1 人の手計算・介護の年齢・特例と月額表の 1 区分・50 銭・加入の判定)・
  `tests/economy/test_rules42_ledger.py`(給料日の流れ・外の雇用主・預かり金 → 期限・足りない店・腕 off・合成の 2 日の保存則)・
  `tests/economy/test_rules42_credit.py`(3 分の 1・書類の欄・利息の上限・呼び手なし)・`tests/engine/rights/test_rules42_rights.py`
  (credit の読み書き・道路の区間と看板の許可・own → store)・`tests/economy/test_rules42_runs.py`(合成の 2 日の on/off・再開の
  腕の検査・slow の再開=通し 2 件)。
- `tests/economy tests/engine tests/c8 tests/tools`(`-n 2 --dist loadfile -m "not slow"`): **3,541 passed・1 skipped・0 failed**
  (52 分 44 秒)。slow(`tests/economy`・`tests/engine/rules`・`tests/engine/rights` の `-m slow`): **50 passed**(26 分 35 秒)。
  `lint-imports` 5 kept・0 broken。`tools/scan_secrets.py`(変えたファイル全部)CLEAN。`tests/c7` は回していない。
- 直した既存の試験: 権利台帳の種類の数(`test_rights_schema`・`test_rights_from_w16`・`test_rights_manifest`)・規則の表(行の数・
  写し検査・読み手の一覧)・再開の見出し(`rules_42`)・合成の 2 日の税の流れ(`test_stage2_runs`)・w17 と occupation の比べ
  (`test_wage_occupation_runs`=天引きの科目を除いて比べる)・状態台帳の行の数(142 → 143・233 → 234)と腕の行の並び・golden(§8-4)。

## 9. 仮採用と、親に確かめてほしいこと

仮採用(発注の親の判断=PENDING 仮-40 のまま実装): Q1 預かり金と申告の期限・Q2 `norm`(形式の版 2)・Q3 `credit`・道路の区間・
看板・`own → store`・Q4 前年の所得=月の賃金 × 12・Q5 営業許可の一覧は取得しない・Q6 asof の下限の印・Q7 電算機計算の特例。

問い(推測で埋めていない):

1. **1 日の 19 構成は「不変」ではない**(発注の見込みと違う): Q1 で、レジの税が政府でなく店の現金に残るので、帳簿の残高と
   状態台帳の行 TXD が入る 4 欄(final・full_last・behavior_last・end_of_day)が動く。行動の欄(呼数・テープの列・行動の件数・
   食事・会話・出動など 21 欄)は 19/19 で同じ。腕 off で 19/19 × 25 欄が本体の写しと同じ(§8)。この形で受け入れるか。
2. **住民税の元(Q4)**: 「月の賃金 × 12」を額面のまま所得とし、給与所得控除・基礎控除などを引いていない(答申に住民税の控除の
   値が無い)。300,000 円で月 30,416 円(額面の 10.1%)=控除のある現実の額のおよそ 2 倍(推測・未計測)。5,000 体の給料日で本人の
   分 2.00 億円のうち住民税 0.91 億円(45%)。控除を入れるなら、源泉の別表第一(月の給与所得控除)を 12 倍して使うか、住民税の控除の
   一次の確認を待つか。
3. **源泉の 105,000 円未満**: 月額表は 0 円・特例の式は A が 102,501 円を超えると正(最大 130 円)。特例をそのまま使った(Q7)。
4. **消費税の期限**: 全部の店を個人事業者(課税期間=暦年・翌年 3 月 31 日)で代えた。法人(末日の翌日から 2 か月)を混ぜる材料が
   無い。期限の行は R-106 の版(2026-10-01)が下限=世界の時点には効いていない(課税期間の末日に引く)。行の kind は machine にした
   (申告と納付は人の手続き=R-118 §2-6 では human・Q1 で機械が移す)。この扱いでよいか。
5. **19 行に足した値の欄**: 健保の行の `grades`・`full_time_share`・`short_time_coverage`、厚年の行の `grades`、雇用保険の行の
   `min_weekly_hours`(付属の JSON の写しから外れる)。消費税の申告の期限の 20 行目。どちらも「機械が読む値は表に置く」のための足し。
6. **権利台帳の credit の物**: 決定は「権利の種類 credit」と「物の種類 道路の区間・看板」だけ。credit の物に番号の空間
   `credit_contract`(信用の器の行=R-118 §4)を足した。
7. **店の持ち主の 286 行**: 閉じた表に入ったが、初期の行は変えない(発注)=入れていない。入れる段と、`DOC-pop43-store-owner-deferred`・
   `EX-build.pop.w21_apply-3c06c862`(外す段 4-2)の外す段の付け直し。`BR-RIGHTS-LICENCE-BLANK`(外す段 4-2・Q5 で後の段)も同じ。
8. **外す段 4-2 の行が台帳に残る**: 本段で触らなかった active の行(W7#1〜13・BR-RENT-BLANK・ATM と支店の時間・給料日 25 日など
   30 行あまり)の外す段は 4-2 のまま。
9. **天引きの納付の時期**: 給料日に即時(預り金の口は作っていない)。消費税だけ預かり金(Q1)。
10. **子ども・子育て拠出金**(事業主 0.36%)の行が 19 行に無い=雇用主の分に入れていない。
11. **腕 `SHIBUYA_RULES_42`**: 旧値の再現の切替口として環境変数だけ(CLI の旗は作っていない=cli.py は並走の段が触るため)。
    byte-check の道具 `10e/byte_check_10e.py` の `SWITCH_ENV` に足すのは親(本段では足していない)。

## 10. 触った共有ファイル

並走の段(旧道の切替口の削除: `economy/wages.py`・`engine/energy.py`・`cli.py`・`manifest_sections.py`・つなぎの台帳・設定の指紋)と
重なりうるもの。どれも末尾に足すか、局所の置き換え:

| ファイル | 触り方 |
|---|---|
| `docs/design/bridging-ledger.json` | 末尾に 13 行・既存の 5 行(§7)の欄を直した |
| `src/shibuya/economy/stage2.py` | `payroll` の頭に腕 on の分かれ道 1 か所(`_payroll_law` へ)・`purchase` の税の分かれ道・`before_close`・計器の鍵・`manifest_record`・`day_record`・新しいメソッド `_payroll_law`(`external_sales` の前)。w17 の道(`payroll` の本体)は変えていない |
| `src/shibuya/engine/economy_stage2.py` | `Stage2Plan.__init__` の引数 `law`(末尾)・`attach` に 4 行・`header_fields` と `check_resume` に各 1 か所 |
| `src/shibuya/economy/ledger.py` | `attach_stage2` の 1 行(店の数を渡す) |
| `src/shibuya/engine/state_ledger.py` | 外の状態の行の末尾に `TXD`・`OWNER_CLASSES` と `EXCLUDED` の末尾に 1 行ずつ |
| `src/shibuya/engine/systems/table.py` | phase_c・day_close・close_final の `paths` に `TXD:ledger.*` |
| `src/shibuya/economy/accounts.py` | `FLOW_REGISTRY` の末尾(器の 1 行を「本人 → 政府」に改名+3 行) |
| `tests/engine/test_state_ledger_10b.py` ほか golden の試験 | §8-4 の張り替え |

`manifest_sections.py`・`cli.py`・`economy/wages.py`・`engine/energy.py` は触っていない(新しい manifest の欄は既存の観測の節
`economy.stage2.{rules,wages,tax}` と設定の節 `economy.stage2.plan` の子に入れた=設定の指紋 `CONFIG_PATHS_SHA256` は不変)。

## 11. 独立検収の直し(条件つき受入 高 1・中 2・低 9 → 全部直した)

| # | 欠陥 | 箇所 | 直し方 | 試験 |
|---|---|---|---|---|
| H1 | 抽出で動く数(`matched`・`students`)が設定の節 `economy.stage2.plan.law` に入っていた | `engine/economy_rules.py`(`PayrollInputs.record`・`material_counts`)・`economy/stage2.py`(`MoneyStage2.__init__`) | 設定の節には出どころ・語・定数(`source`・`role_vocab`・`full_time_weekly_hours`・`non_employee_roles`)だけ。数(`bodies`・`matched`・`students`・`hours_known`)は観測の `economy.stage2.rules.payroll_inputs`(先例 `rules.wage_build`) | `test_rules42_runs::test_on_keeps_the_register_tax_in_the_deposit_and_deducts_on_payday`・10f の slow の交換可能性・`tools/c7/seed_exchangeability.py`(§12-3) |
| M1 | 住民税の元=額面 × 12・控除なし(約 2.5 倍) | `economy/taxes.py`(`resident_tax_monthly`・`deductions`) | 所得割の元=額面 − 給与所得控除(源泉の別表第一を月の額面に当てた額)− 社会保険料控除(本人の分)の 12 か月分。基礎控除・調整控除・非課税の限度は入れない(台帳 `DOC-rules42-resident-tax-base` に「控除は 2 つだけ=まだ過大の方向」) | `test_rules42_payroll::test_one_person_month_matches_the_hand_calculation`・`test_resident_tax_takes_the_two_deductions` |
| M2 | 判定の材料が無い体 941(うち外の雇用主 715)が社会保険と雇用保険に未加入 | `economy/taxes.py`(`enrollment` の `assume_full_time`)・`economy/stage2.py`(`_payroll_law`) | 外の雇用主の体は「被保険者 51 人以上の事業所の正社員(週 40 時間)」とみなして加入(台帳 `DOC-rules42-outside-employer-enrolled`)。それ以外の材料の無い体(226)は宣言のまま未加入 | `test_outside_employer_rows_are_enrolled_as_full_time`・`test_rules42_ledger::test_outside_employer_pays_gross_from_the_outside_and_only_the_employee_share` |
| L1 | 申告の期限の行が machine | `docs/design/rules-table.json`・`economy/taxes.py`(`_bridge_row`・`BRIDGE_READ_RULES`・`filing_deadline`) | 行は human に戻した。期限に預かり金を移す機械の側は「つなぎ」(台帳 `DOC-rules42-tax-remit-machine`・外す段 6-6=人が納める行動)。machine の行を読む口 `_row` は変えず、human の行はつなぎの読み口 `_bridge_row`(一覧の行だけ・human だけ)で読む | `test_rules42_table::test_every_machine_row_has_a_reader`・`test_the_filing_deadline_row_is_from_r106_and_used_at_the_period_end` |
| L2 | 年齢の上限なし | 台帳 `DOC-rules42-enrollment-basis` | 一次の確認が無い=入れない=空欄の宣言を行の文に | ― |
| L3 | byte-check の道具の `SWITCH_ENV` | (親) | 親が足す(本段では足していない) | ― |
| L4 | 預かり金の検算が記録だけ | `economy/stage2.py`(`tax_deposit_ok`)・`engine/systems/report.py`・`engine/run.py`(`RunResult.money_stage2_deposit_ok`・`conserved`) | 積んだ − 移した − 残高=0 と店ごとの残高が負でないことを `RunResult.conserved` に入れた(腕 off と段階 2 の無いランは真) | `test_rules42_runs::test_conserved_fails_when_the_deposit_check_breaks` |
| L5 | 下限の印の行を下限より前に引くと「規則なし」・雇用保険の率は 2027-03-31 の後に黙って 0 | `economy/taxes.py`(`_get`・`_valid`) | 下限の印の行を下限より前に引いたとき・`valid_until` の後は `RuleNotInForce` で止まる。2027-10 からの 36 人の値は世界の時点の外=読まない(注) | `test_lower_bound_rows_stop_before_the_bound`・`test_rows_not_in_force_give_zero`・`test_rules42_credit::test_before_the_lower_bound_the_check_stops` |
| L6 | 「20 の id」 | `engine/rules/table.py` の docstring | 24 の id に | ― |
| L7 | 試験の組を丸ごと 0 にしていた | `tests/economy/stage2/test_wage_occupation_runs.py` | 本体 `6f07eff` で w17 との比べごと消えた=原資の等式だけを直した(額面+雇用主の分) | 同じ試験(slow) |
| L8 | 足した欄が note に無い | `docs/design/rules-table.json`(健保・厚年・雇用保険・源泉の 4 行) | note の末尾に「付属の JSON の行に足した欄」を 1 文 | `test_the_19_rows_are_the_draft_rows_and_in_force_on_the_world_date` |
| L9 | Q7 の宣言の行が無い | 台帳 | `DOC-rules42-withholding-special-formula`(外す段 7)を足した | ― |
| 問い 3 | 105,000 円未満で特例の式が正 | `economy/taxes.py`(`income_tax_withholding`)・規則の表の源泉の行 `kou_zero_below_yen`=105,000 | 月額表の甲欄どおり 105,000 円未満は 0 円・それ以上は特例の式 | `test_special_formula_versus_the_monthly_table_bracket` |
| 問い 4 | 期限の決まり | 台帳 `DOC-rules42-tax-deadline` | 「法人の決まりは別=入れていない」を 1 文 | ― |
| 問い 7・8 | 外す段 4-2 の active の行 35 | 台帳 | 店の持ち主に依る 4 行 → `next-bump`(`EX-build.pop.w21_apply-3c06c862`・`DOC-pop43-store-owner-deferred`・`EX-build.pop.w21_build_c-5d13fbc8`・`DOC-pop43-store-round-robin-kept`)・依らない 30 行 → 7(理由を why に=W7#1〜13・HD 2・PR-plan.opening_hours・BR-RENT・BR-MIN-WAGE・BR-RIGHTS-LICENCE・BR-PHONE・DOC-ec21 の 7・DOC-cf33-l4・DOC-ca1b-commuter-pass・EX-build.pop.w21_apply-0abb5b47)・`BR-RIGHTS-DWELLING-BLANK` は 4-2 のまま(活性化の後に閉じる=親) | `test_bridging_ledger`・`test_c0_phone_table…`・`test_rights_from_w16`(外す段の期待を直した) |
| 問い 8 | 子ども・子育て拠出金 | 台帳 `DOC-rules42-employer-levy-missing` | 入れない=R-118 の一次確認の外=空欄の宣言 | ― |

### 11-1. 天引きの例(1 人・額面 300,000 円・45 歳・週 37 時間)の新旧

| 項目 | 直す前 | 直した後 |
|---|---|---|
| 健保+介護・支援金・厚年・雇用保険(本人) | 17,205・345・27,450・1,500 | 同じ |
| 源泉所得税 | 6,250 | 6,250 |
| 住民税 | 30,416(額面 × 12 × 10%+5,000)÷ 12 | **16,099**((300,000 − 96,667 − 46,500)× 12 × 10%+5,000)÷ 12 |
| 本人の分の合計・手取り | 83,166・216,834 | **68,849・231,151** |
| 雇用主の分 | 47,550 | 47,550 |

### 11-2. 給料日を含む 2 日(5,000 体・`w6_v3_default`・08-24 から)の新旧

| 量 | 直す前(土台 9743268) | 直した後(本体 6f07eff の上) |
|---|---|---|
| final | `a5a3eb6f…` | `a5a3eb6f…`(給料日の支払いは最後の checkpoint の後) |
| 額面(2,726 体) | 897,159,093 | 897,159,093 |
| 本人の分 | 200,226,913 | **195,662,910** |
| うち 健保+介護・支援金・厚年・雇用保険 | 27,338,796・588,405・45,385,830・2,646,604 | 40,283,868・865,711・67,013,685・3,854,131 |
| うち 源泉所得税・住民税 | 33,638,000・90,629,278 | 30,460,890・**53,184,625** |
| 手取り | 696,932,180 | 701,496,183 |
| 雇用主の分(雇用主 → 政府) | 77,812,151 | 77,812,151(外の雇用主の雇用主の分 36,902,940 は記録しない) |
| 政府の口座 | 278,039,064 | **273,475,061** |
| 預かり消費税 | 1,192,445(594 店) | 1,192,445(594 店) |
| 保存則・預かり金の検算 | 毎日 残差 0 | 毎日 残差 0・`conserved` 真(預かり金の検算を含む) |

### 11-3. 加入の割合の新旧(同じ 2 日・払った 2,726 体)

| | 直す前 | 直した後 |
|---|---|---|
| 社会保険 | 1,484(54.4%) | **2,199(80.7%)** |
| 介護 | 694 | 1,049 |
| 雇用保険 | 1,548(56.8%) | **2,263(83.0%)** |
| 判定の材料なし(未加入) | 941(うち外の雇用主 715) | **226**(外の雇用主は加入) |

## 12. 本体の先端 6f07eff への載せ替え

### 12-1. 手順と衝突

- 控え(作業木の変更 30 本と土台 9743268 の版)→ 追跡ファイルを戻して `git merge --ff-only 6f07eff` → ファイルごとに
  `git merge-file`(本段の版・9743268・6f07eff)。両方で変わったのは 15 本。
- 衝突と解き方:
  - `economy/stage2.py`(2 か所): 本体で w17 の道の分岐が消えた。成長の宣言(預かり金の足し)と manifest の `plan`(本体の
    `wage_path` の後に本段の `rules_42`・`law`)を本体の形に足した。
  - `engine/economy_stage2.py`(4 か所): 見出しと再開の検査(本体の賃金の道の検査の後に `rules_42`)・`Stage2Plan` の引数
    `law`・`attach` の `law=law` を本体の形に足した。
  - つなぎの台帳: 本体の版(586 行)に本段の直しの道具を当て直した(13+3 行を足し・既存の行を直した)。
  - 試験(golden と見出し): 本体の版にして、本段の分を当て直した。本体で消えた腕の golden(`--poi-target legacy`・
    `--rel-tenure-hash v1`・`--meal-default validation`)は張り替えない(本体のとおり)。本体で動いた腕の golden(退去の効果 on の
    `l4x1`・`hunger_v1`)は本段の値に張り替えた(§12-2)。
  - `CONFIG_PATHS_SHA256` は本体の `ceb58699…` のまま(本段は設定の節の道筋を足していない)。
- 表の sha: `4dda40d8f83d6a3f`(土台)→ `621c7894796a5fcb`(直した後=期限の行 human・`kou_zero_below_yen`・note の 1 文)。
- つなぎの台帳: 586 → 602 行(active 576 → 579)。

### 12-2. byte-check(本体 6f07eff の写し・4 構成・5,000 体・seed 1・1 日・1 本ずつ)

| 比べ方 | final が同じ | 25 欄 | 記録 |
|---|---|---|---|
| 写し vs 腕 off | 4/4 | 4/4 で 25 欄同じ | [bc4_head6f_vs_off.json](bc4_head6f_vs_off.json) |
| 写し vs 既定(on) | 0/4 | 4/4 で動いたのは final・full_last・behavior_last・end_of_day の 4 欄だけ | [bc4_head6f_vs_on.json](bc4_head6f_vs_on.json) |

- 既定の final は直す前と同じ(`w6_v3_default` bb86f898…・`w6_v3_activity_off` 3cdf9dbf…・`w6_v1_default` 8fca095b…・`v3_mem_rel`
  94becde2…)=1 日のランは給料日を含まないので、M1・M2 の直しでは動かない。
- golden の張り替え(本体で値の変わった腕): `test_presence_executor` の W21 の行の `v3_default_final_l4x1`(本体 aea727f0… →
  b698b0e5…)・`null_arm_final_hunger_v1`(本体 09c7907e… → 730512bf…)・`v3_default_final_hunger_v1`(本体 4c71d4d4… → 2e5ba0c9…)・ほか §8-4 の行。

### 12-3. 試験(直した後・本体 6f07eff の上)

| 範囲 | passed | failed | errors |
|---|---|---|---|
| `tests/economy tests/engine tests/c8 tests/tools`(`tests/engine/rules`・`rights`・`bridging` を含む・`-n 2 --dist loadfile -m "not slow"`) | 3,535 | 0 | 0(1 skipped・48 分 57 秒) |
| slow(`tests/economy tests/engine/rules tests/engine/rights -m slow`・`-n 2 --dist loadfile`) | 49 | 0 | 0(12 分 33 秒・再開=通しの 2 件と賃金の 2 日を含む) |
| 10f の slow の交換可能性(`test_relations_on_5000_seeds_are_exchangeable_and_config_leaves_do_not_move`・H1) | 1 | 0 | 0 |

- `tools/c7/seed_exchangeability.py`(5,000 体・seed 1 と 2・1 日・既定 v3): exchangeable=True・未説明の差 0・観測の節の差 370・
  環境の警告なし(H1 の直しの後)。
- `lint-imports` 5 kept・0 broken。`tools/scan_secrets.py`(変えたファイル全部)CLEAN。`tests/c7` は回していない。
- 2 日の記録: [runs_2day_after_fix.json](runs_2day_after_fix.json)(壁時計 91.7 秒・最大の作業集合 515.1 MB・判断の呼び 143,286=
  同じ機械で試験が並走)。

### 12-4. 仮採用の一覧(親の判断=PENDING 仮-40 と検収の後の判断)

Q1 預かり金と申告の期限(期限の行は human・移す機械の側はつなぎ)・Q2 `norm`・Q3 `credit`・道路の区間・看板・`own → store`
(物 `credit_contract`)・Q4 前年の収入=月の賃金 × 12(給与所得控除と社会保険料控除だけ)・Q5 営業許可の一覧は取得しない・Q6 下限の
印(下限より前は止まる)・Q7 電算機計算の特例(105,000 円未満は 0 円)・外の雇用主の体は 51 人以上の事業所の正社員とみなす・
年齢の上限と子ども・子育て拠出金は空欄の宣言・天引きの納付は給料日に即時・1 日のランで 4 欄が動くのは受入(版上げ=宣言)・
腕は環境変数だけ(`SWITCH_ENV` は親)。

## §親の検収(第337・Fable 5.1・rebase の後・小さな版上げ)

- 本体 6f07eff へ rebase(9743268 からの載せ替えは実装役が控え+早送り+merge-file で(衝突=`economy/stage2.py` 2 か所・`engine/economy_stage2.py` 4 か所・台帳・golden=4-3 第 2 部で w17 の道が消えた分)・6f07eff へは衝突なし)→ 05faf98。範囲の試験(economy・`tests/engine` 全体・c8・tools)**3,535 passed・1 skipped・0 failed・0 errors(`-n 4 --dist loadfile -m "not slow"`・24 分 8 秒)**。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・W21 の世界)=**3 面**: 既定 on は **4 欄(final・full_last・behavior_last・end_of_day)だけ動き 21 欄は同じ**(w6_v3_default/activity_off/v1_default/v3_mem_rel の 4 構成とも final・full_last・behavior_last・end_of_day の 4 欄だけ(side の JSON に腕の鍵は出ない=本体の 10e の道具にはまだ `SHIBUYA_RULES_42` が無い・off が 25 欄同じことが切替口の効きの証拠)=`parent_head_vs_r42_on_4cfg.json`=レジの税が店の現金に残る+状態の行 TXD=版上げ=宣言どおり)/ 切替口 `SHIBUYA_RULES_42=off`(side の env に残ることを JSON で確認)は **final 同じ・25 欄とも差なし**(`parent_head_vs_r42_off_4cfg.json`)。実装役の 19 構成 × 2 と検収役の 4 構成 × 2 も同じ。
- **data 無しの写し(detached の作業木・junction なし)で CI-1 と同じ引数の全体試験(tests/c7 を含む)=**5,665 passed・290 skipped・failed 0・errors 0**(1,814 秒・CI の印=`-m "not gpu and not slow" -n 2 --dist loadfile`・05faf98・faulthandler 900 s で traceback なし)**。
- 独立検収([review.md](review.md))=条件つき受入(高 1=抽出で動く数が manifest の設定の節に入り 5,000 体の交換可能性の試験が落ちる/ 中 2=住民税に控除が無く約 2.5 倍・判定の材料が無い体 941 が未加入/ 低 9)→ 全部直した(§11)。検収役の独立の再計算=天引きの例(額面 30 万円)は電卓と差 0・5,000 体の給料日 2,726 行の体ごとの検算 0・保存則の 4 本の流れと預かり金の検算 0・期限をまたぐ合成のラン ○。親の判断: (1) 住民税は給与所得控除と社会保険料控除だけ(基礎控除・調整控除・非課税の限度・年齢の上限 70/75・子ども・子育て拠出金 0.36% は一次確認の後=空欄の宣言=**親の宿題**)。(2) 外の雇用主の体は 51 人以上の正社員とみなして加入(expedient)。(3) 105,000 円未満の源泉は月額表どおり 0。(4) 申告の期限の行は human・期限に移す機械の側はつなぎ(外す段 6-6 ②)。(5) 消費税の期限は全店 翌年 3/31(expedient・法人は別)。(6) 外す段 4-2 の 35 行=店の持ち主に依る 4 行は next-bump・30 行は 7。(7) 腕は環境変数だけ(`SWITCH_ENV` に親が足した)。
- **版上げ(§0-6・§0-7)**: 既定が変わる(給料日を含むランで天引きと納付・1 日でもレジの税の預かりで 4 欄)。直前の本体 HEAD に安定版のタグ **`stable-v2-before-rules-42`**。戻す手順=`git checkout stable-v2-before-rules-42`(または `SHIBUYA_RULES_42=off`=次の版上げで消す=台帳 `DOC-rules42-legacy-switch`・next-bump)。性能=実装役の表(2 日の壁時計 86.0 → 86.3〜86.9 s・判断の呼び 143,286 で同じ・状態の外 +18,906 B/checkpoint・加入の材料の組み立て 0.14 s/全母集団)=悪化なし(予算の宣言に写す)。
- 判定: **受入**(小さな版上げ=4-2 の R-118 §7-1 の分。営業許可・道路・屋外広告物の行は第 5 期と区のデータの判断の後)。
