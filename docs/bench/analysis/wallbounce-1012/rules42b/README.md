# 第 4 期 4-2b 規則の表の空欄 3 件を埋める(小さな版上げ)の記録

- 実装役 Opus 5.5。作業木の枝 `4-2b/rules-values-fill`(土台 `f27377a`=本体の先端・本体の世界は W21)。commit は親。
- 正: [R-118 §10-2](../../../../research/v2-r118-rights-and-rules-contents.md)(親の一次確認=値と出典)・§2-6・§7-1、4-2 の記録
  [rules42](../rules42/README.md)(§7・§8・§10・§11)・PENDING 仮-43・回答 10-13b §0-6・§0-7。
- 入れた値は R-118 §10-2 の表のとおり(推測で埋めていない)。新しい一次出典は取りに行っていない(ネットワークなし)。数は実測。
  生の出力は作業木の `_bc/`(git の外)。絶対パスなし。

## 0. 結論

- 4-2 で空欄の宣言にした 3 件を規則の表に入れ、給料日の天引きで使う(既定=腕 `SHIBUYA_RULES_42B=on`)。
  1. 住民税: 基礎控除(43/29/15 万円・0)・調整控除(5%)・非課税(扶養 0 で合計所得 45 万円以下・未成年者 135 万円以下)。
  2. 年齢の上限: 厚年 70 歳未満・健保 75 歳未満(健保・介護・支援金とも)。
  3. 子ども・子育て拠出金: 事業主だけ・厚年の標準報酬 × 0.36%(雇用主の分の 5 項目め)。
- 額面 30 万円・45 歳の 1 人: 住民税 16,099 → **12,308 円**・本人の分の合計 68,849 → **65,058 円**・雇用主の分 47,550 →
  **48,630 円**(拠出金 1,080 円)。電卓の式と差 0。
- byte-check 19 構成(1 日・給料日なし): **off も on も f27377a の写しと 25 欄が 19/19 で同じ**(1 日のランは給料日を含まない)。
- 給料日を含む 2 日(5,000 体): 本人の分 1.957 → **1.828 億円**(住民税 0.532 → 0.432 億円)・雇用主の分 0.7781 → 0.7759 億円
  (拠出金 +172 万円・年齢の上限で厚年と健保 −194 万円)。**体ごとの検算 2,726 行 × 11 項目で食い違い 0**・保存則 毎日 残差 0・
  再開(日の境目と給料日の昼)=通し・段 B 宣言の外 0・記録 on/off で final と checkpoint 8 個と帳簿が同じ・off は写しと全部同じ。
- 性能は 4-2 と同じ範囲(2 日の壁時計 69.8〜72.2 秒・判断の呼び 143,286 回で同じ)。

## 1. 入れた値と出典(R-118 §10-2=親の一次確認)

| 項目 | 値 | 出典(読んだ版) | 規則の表 |
|---|---|---|---|
| 住民税の基礎控除 | 合計所得 2,400 万円以下 43 万円・2,450 万円以下 29 万円・2,500 万円以下 15 万円・超は 0 | 地方税法 314 条の 2 第 2 項 1〜3 号(2026-10-16 の版)・都主税局「個人住民税」 | `resident_tax.basic_deduction`(新) |
| 住民税の調整控除 | 扶養 0=人的控除額の差 5 万円。課税所得 200 万円以下=min(5 万円, 課税所得)× 5%・超=max(5 万円 −(課税所得 − 200 万円), 5 万円)× 5%=2,500 円・合計所得 2,500 万円超は 0 | 地方税法 314 条の 6(親が実読=5 万円・3%)・37 条(都民税 2%=**未読=都主税局の頁の値**)・都主税局の頁 | `resident_tax.adjustment_credit_tokyo_ward`(新) |
| 住民税の非課税(23 区・扶養 0) | 合計所得 45 万円以下=均等割も所得割も 0・未成年者(18 歳未満)は 135 万円以下で 0 | 地方税法 295 条 1 項 2 号(親が実読=135 万円・2026-10-16 の版)・同条 3 項(45 万円=**未読=都主税局の頁の値**)・都主税局の頁(区の条例の額) | `resident_tax.non_taxable_tokyo_ward`(新) |
| 厚年の年齢の上限 | 70 歳未満が被保険者 | 厚年法 9 条(2026-10-01 の版) | `pension.employees_rate` の欄 `age_max_exclusive`(足した) |
| 健保の年齢の上限 | 75 歳未満(75 歳以上は後期高齢者医療へ) | 健保法 3 条 1 項ただし書 7 号・36 条 3 号・高確法 50 条 1 号(2026-10-01 の版) | `health_insurance.kyoukai_tokyo` の欄 `age_max_exclusive`(足した) |
| 子ども・子育て拠出金 | 事業主だけ・千分の 3.6(0.36%)・厚年の標準報酬月額 | 子ども・子育て支援法施行令 27 条(法 70 条 2 項・2026-10-01 の版)・年金機構「厚生年金保険料額表」 | `child_care_contribution.rate`(新) |

## 2. 規則の表の行(新旧)

| 行 | kind | asof(印) | 4-2(f27377a) | 4-2b | 読み手 |
|---|---|---|---|---|---|
| `resident_tax.basic_deduction` | machine | 2026-06-01(下限) | 無し | `bands` 4 帯 | `economy.taxes._basic_deduction`(`resident_tax_monthly`) |
| `resident_tax.adjustment_credit_tokyo_ward` | machine | 2026-06-01(下限) | 無し | 差 5 万円・都 2%+区 3%・200 万円・下限 5 万円・2,500 万円 | `economy.taxes._adjustment_credit` |
| `resident_tax.non_taxable_tokyo_ward` | machine | 2026-06-01(下限) | 無し | 45 万円・135 万円・18 歳未満(扶養ありの式は写しだけ) | `economy.taxes.resident_non_taxable` |
| `child_care_contribution.rate` | machine | 2025-04-01(下限) | 無し | 0.0036・本人 0・厚年の標準報酬 | `economy.taxes.deductions` |
| `health_insurance.kyoukai_tokyo` | machine | 2026-03-01(変えない) | 年齢の欄なし | `age_max_exclusive` 75・出典 `age_max_exclusive_source`(健保法・高確法) | `economy.taxes.payroll_tables`・`enrollment` |
| `pension.employees_rate` | machine | 2017-09-01(変えない) | 年齢の欄なし | `age_max_exclusive` 70・出典 `age_max_exclusive_source`(厚年法) | 同上 |

- 表は 26 → 30 行(id 24 → 28)。表の sha `621c7894796a5fcb` → `1490c5a2fdc8beb4`(検収の直しの後・直す前は `3a22317cf609aad6`・manifest の `rules_version` が動く=版上げ)。
- 下限の印(Q6): 住民税の 3 行は既存の住民税の行の年度の始まり(2026-06-01)・拠出金は読んだ年金機構の頁の年度の始まり
  (令和 7 年度と同じ率=2025-04-01)。条文はどれも世界の時点より後の版で読んだ=版の比較はしていない。
- 住民税の 3 行は住民税の行がある日(2026-06-01 以後)だけ引く=5 月の給料日でも止まらない。拠出金の行を 2025-04-01 より前に
  引くと止まる(`RuleNotInForce`=4-2 の検収 L5 の形)。
- 出典の URL は〔検収 低 1・親の判断〕親が読んだ形=e-Gov 法令 API の `law_data/<法令 ID>?elm=MainProvision-Article_<条>`(asof なし)。読んだ版は `version` に文で書く(地方税法=令和 8 年法律第 2 号による改正後・2026-10-16 施行の版/健保法・厚年法・高確法・施行令=2026-10-01 施行の版・どれも 2026-10-22 取得)。4-2 の行(`?asof=` つき)は読んだ形が違うので触っていない。

## 3. 手計算(額面 300,000 円・45 歳・週 37 時間・雇用主の被保険者 100 人・2026-08-25・扶養 0)

| 項目 | 本人 | 雇用主 | 筋道 |
|---|---|---|---|
| 健保+介護・支援金・厚年・雇用保険 | 17,205・345・27,450・1,500 | 17,205・345・27,450・2,550 | 4-2 と同じ |
| 源泉所得税 | 6,250 | ― | 4-2 と同じ |
| 子ども・子育て拠出金 | ― | **1,080** | 厚年の標準報酬 300,000 × 0.36% |
| 住民税 | **12,308**(4-2 は 16,099) | ― | 合計所得=(300,000 − 給与所得控除 96,667)× 12=2,439,996 → 基礎控除 430,000。課税所得=2,439,996 − 558,000(46,500 × 12)− 430,000=1,451,996 → × 10%=145,199 → 調整控除 min(50,000, 1,451,996)× 5%=2,500 → 142,699 → +均等割 5,000=147,699 ÷ 12=12,308 |
| 合計 | **65,058**(手取り 234,942) | **48,630** | |

境の確かめ(試験 `test_rules42b_payroll.py`): 基礎控除は 2,400 万円で 43 万円・2,400 万 1 円で 29 万円・2,450 万 1 円で 15 万円・
2,500 万 1 円で 0。調整控除は課税所得 12,345 円で 617 円(1 円未満の切り捨て)・200 万円と 200 万 1 円で 2,500 円・合計所得
2,500 万 1 円で 0。非課税は合計所得 45 万円で真・45 万 1 円で偽・17 歳の 135 万円で真・135 万 1 円で偽・18 歳と年齢不明は特別の
限度の外。月の額面で見ると、合計所得 45 万円以下の上の端の額面で住民税 0・1 円上で均等割から。70 歳と 75 歳の境(64・69・70・
74・75 歳の行): 厚年と拠出金は 69 歳まで・健保と支援金は 74 歳まで・雇用保険は全員。

## 4. 天引きの形(コード)

- `economy.taxes.payroll_tables(asof, rules, *, r42b=True)`: `r42b` なら新しい 4 行と年齢の上限を引く(偽=4-2 の値)。キャッシュの
  鍵は (日, r42b)。`PayrollTables.employer_items` は 5 項目(偽は 4 項目)。記録 `record()` は on だけ `age_max_exclusive` を持つ。
- `enrollment`: `social`(健保・介護・支援金)は健保の行の上限未満・新しい欄 `pension`(厚年・拠出金)は厚年の行の上限未満
  (年齢 −1=不明は上限の内)。`Enrollment` に `pension`・`age` を足した(既定 `None`=4-2 の形)。
- `deductions`: 厚年は `enroll.pension` の行・拠出金=厚年の標準報酬 × 率の 1 円未満の切り捨て(雇用主の分の既存の形)・住民税は
  `_resident_tax`(基礎控除・調整控除・非課税)。`Deductions.resident_exempt` を足した。どれも配列演算(Python のループは帯の数 4
  だけ=宣言)。
- 腕: `engine.economy_rules` に `SHIBUYA_RULES_42B`(`arm_42b`・`set_arm_42b`・既定 on)。組み立てで読み `PayrollInputs.rules_42b`
  に載せ、`economy.stage2` が `payroll_tables(r42b=…)` に渡す。状態のファイルの見出し `economy_stage2.rules_42b`(on のランだけ)と
  再開の検査(違えば止める)。manifest の設定の節 `economy.stage2.plan.rules_42b`(on だけ)。〔検収 低 6〕4-2 の版で保存した
  状態のファイル(見出しに `rules_42b` が無い)は既定 on では再開できない(止まる=`SHIBUYA_RULES_42B=off` で再開する=設計どおり・
  版上げの後は安定版のタグで)。
- お金の流れ: 拠出金は雇用主の分に足して既存の「給与の天引き(雇用主 → 政府)」で移す(新しい登録なし)・原資(外界 → 雇用主)=
  額面+雇用主の分(拠出金を含む)。計器 `wages.employer_child_care_contribution` と、on だけの観測の鍵 `enrolled_pension`・
  `age_70_plus`・`age_75_plus`・`minors`・`resident_non_taxable`。腕 off の計器と記録は 4-2 のまま。
- AST の試験: `taxes.py` に年齢の上限・控除の額・率・限度の直書きが無い(規則の表から)。

## 5. 動いた量

### 5-1. 1 日の 19 構成(byte-check・mock/classical 5,000 体・seed 1・テープつき・W21 の世界・`--jobs 1`=1 本ずつ)

| 比べ方 | final が同じ | 25 欄が全部同じ | 記録 |
|---|---|---|---|
| `f27377a` の写し vs 作業木 `SHIBUYA_RULES_42B=off` | 19/19 | 19/19 | [bc19_head_vs_off.json](bc19_head_vs_off.json) |
| `f27377a` の写し vs 作業木 既定(on) | 19/19 | 19/19 | [bc19_head_vs_on.json](bc19_head_vs_on.json) |

- 1 日のラン(2026-07-13 から)は給料日を含まない=天引きが起きない=on でも 25 欄は動かない。動くのは給料日の帳簿だけ(§5-2)。
  side の JSON に腕の環境変数が残る(off の側は `SHIBUYA_RULES_42B=off`=10e の `SWITCH_ENV` に足した)。
- 壁時計の合計(19 構成): 写し 665.6 秒・off 674.9 秒・on 659.9 秒(同じ機械で試験が並走)。

### 5-2. 給料日を含む 2 日(5,000 体・`w6_v3_default`・開始 2026-08-24・1 本ずつ・道具 [tools/runs_rules42b.py](tools/runs_rules42b.py))

| 量 | `f27377a` の写し | off | 既定(on) |
|---|---|---|---|
| final | `a5a3eb6f…` | `a5a3eb6f…` | `a5a3eb6f…`(給料日の支払いは最後の checkpoint の後=4-2 §11-2 と同じ) |
| 額面(2,726 体) | 897,159,093 | 同じ | 同じ |
| 本人の分(世帯の口座 → 政府) | 195,662,910 | 195,662,910 | **182,754,344** |
| うち 健保+介護・支援金・厚年・雇用保険 | 40,283,868・865,711・67,013,685・3,854,131 | 同じ | 39,664,306・851,247・64,497,435・3,854,131 |
| うち 源泉所得税・住民税 | 30,460,890・53,184,625 | 同じ | 30,697,050・**43,190,175** |
| 雇用主の分(雇用主 → 政府・995 雇用主) | 77,812,151 | 77,812,151 | **77,592,324** |
| うち 健保・支援金・厚年・雇用保険・拠出金 | 27,339,126・588,735・45,385,830・4,498,460・― | 同じ | 26,972,211・580,165・43,817,520・4,498,460・**1,723,968** |
| 外の雇用主の雇用主の分(記録しない) | 36,902,940 | 同じ | 36,510,083 |
| 原資(外界 → 雇用主) | 712,257,335 | 同じ | 712,037,508 |
| 政府の口座 | 273,475,061 | 同じ | 260,346,668 |
| 世帯の預金の合計 | 1,425,374,407 | 同じ | 1,438,282,973 |
| 加入(健保・厚年) | 2,199・(健保と同じ) | 同じ | 2,159・2,109 |
| 判断の呼び | 143,286 | 143,286 | 143,286 |

- off は写しと final・checkpoint 8 個(behavior と full)・帳簿の流れ・政府と世帯の残高・計器の全部が同じ(旧値の再現)。
- 源泉所得税が増えたのは、70 歳以上の厚年(と 75 歳以上の健保)が 0 になり社会保険料控除が減ったため。
- 拠出金の全体(外の雇用主の体を含む 2,109 行)は 2,537,604 円・うち帳簿に移したのは 1,723,968 円(外の雇用主の分は 4-2 の宣言
  `DOC-rules42-outside-employer-share` のとおり記録しない)。

### 5-3. 体ごとの検算・保存則・再開・段 B・記録 on/off

- **体ごとの検算**(`--verify`): 給料日の入力と結果を `economy.stage2.payroll_deductions` の口で控え、規則の表の JSON を直に読む
  別の実装(道具の中の行ごとの整数の計算)で本人の分 6 項目と雇用主の分 5 項目を出し直した。加入の材料の判定(時間・役割・学生・
  被保険者の数)は 4-2 のコードの判定を使い、年齢の上限・控除・非課税・拠出金・各料率と端数は道具の中で出し直した。
  2,726 行 × 11 項目で**食い違い 0**。出し直しの合計 本人 182,754,344・雇用主 114,102,407(帳簿に移した 77,592,324+外の雇用主の
  分 36,510,083)=コードと同じ。
- 4 本の流れの検算: 世帯 → 政府 182,754,344=計器の本人の分・雇用主 → 政府 77,592,324=計器の雇用主の分(店の担当の分 0)・
  外界 → 雇用主 712,037,508=賃金(雇用主)634,445,184+雇用主の分 77,592,324・差 0。
- 保存則: 2 日とも毎日 残差 0・登録の無い流れ 0・預かり金の検算 0(on・off・写し)。`RunResult.conserved` は通しのランで真。
- **再開=通し**: 日の境目(刻み 1,440)と給料日の昼(刻み 2,190)で止めて再開 → final・残りの checkpoint の behavior-hash
  (4 個・2 個)・帳簿の流れ・政府と世帯の残高・計器が通しと同じ。再開したランの `RunResult.conserved` は偽だが、写し
  (`f27377a`)の再開も同じく偽(再開のランの現金の等式の起点の問題=本段の前からある=§9 の問い 7)。日次の保存則は残差 0。
- **段 B**: 合成 80 体・2 日(08-24 → 給料日 08-25 の締め)・`SHIBUYA_SYSTEMS_CHECK=1` で宣言の外 0
  (`test_rules42b_ledger.py::test_stage_b_payday_has_no_undeclared_writes`・slow・約 5 分)。
- **記録 on/off**(`SHIBUYA_EVENTS=off`): final・checkpoint 8 個・帳簿・計器が記録 on と同じ。

記録: [runs_2day_on.json](runs_2day_on.json)(検算つき)・[runs_2day_off.json](runs_2day_off.json)・
[runs_2day_head.json](runs_2day_head.json)・[runs_2day_on_events_off.json](runs_2day_on_events_off.json)・
[runs_2day_resume1440.json](runs_2day_resume1440.json)・[runs_2day_resume2190.json](runs_2day_resume2190.json)・
[runs_2day_head_resume2190.json](runs_2day_head_resume2190.json)。

## 6. 年齢の分布と影響を受けた体(5,000 体の給料日の雇用の行 2,726)

| 年齢 | 18 歳未満 | 18〜39 | 40〜64 | 65〜69 | 70〜74 | 75 以上 | 不明 |
|---|---|---|---|---|---|---|---|
| 行の数 | 19 | 1,218 | 1,277 | 92 | 68 | 52 | 0 |

- 厚年の年齢の上限で外れた体(健保の加入の材料があり 70 歳以上)90・健保の上限で外れた体(75 歳以上)40。
- 未成年者 19 体(払われた)・住民税の非課税は 0 体(合計所得 45 万円以下も未成年者の 135 万円以下もいない=この日の賃金の額では
  当たらない)。
- 拠出金の月額の合計 2,537,604 円(2,109 行)・帳簿に移した分 1,723,968 円。

## 7. 性能(§0-7・5,000 体・seed 1・Windows 11・x86-64・同じ機械で試験と別の作業木のランが並走)

| | `f27377a` の写し | off | 既定(on) |
|---|---|---|---|
| 2 日の壁時計[秒] | 69.8 | 71.2 | 72.2(記録 off 68.9) |
| 2 日の最大の作業集合[MB] | 505.0 | 507.2 | 488.3(記録 off 520.9) |
| 判断の呼び(LLM 0) | 143,286 | 143,286 | 143,286 |
| 1 日 19 構成の壁時計の合計[秒] | 665.6 | 674.9 | 659.9 |

- 揺れの中=悪化は見えない。給料日の追加の計算は配列演算(行 2,726 で計器に出ないほど小さい)。状態の外のバイトは増えない
  (拠出金と年齢の上限は状態を持たない=見出しの 1 鍵だけ)。新しい逐次ループは無い(帯の数 4 のループだけ=宣言)。

## 8. 試験

- 新しい試験: `tests/economy/test_rules42b_payroll.py`(53 件=手計算・off=4-2 の値・基礎控除の帯の境・調整控除の境と下限・
  非課税の限度と未成年者・月の額面の境・住民税の年度の前・行の無い表=0・拠出金の行の下限・70/75 歳の境・年齢不明・拠出金=厚年の
  等級 × 0.36% で事業主だけ・支援金と別物・本人の分 ≤ 額面(32 通り)・AST の直書きなし・R-118 §10-2 との写し検査)・
  `tests/economy/test_rules42b_ledger.py`(8 件=給料日の 4 本の流れと保存則と計器・off の計器と記録・on − off の差=拠出金と年齢の
  上限・再開の見出し・腕の名・合成の 2 日の on/off・組み立てで腕を載せる・段 B(slow))。
- 直した既存の試験: `test_rules42_payroll.py`(**4-2 の値=off で通す**=`payroll_tables(…, r42b=False)`・期待は変えていない)・
  `test_rules_table_schema.py`(行の数 26 → 30・R-118 §10-2 の出典の写し検査の枝)・`test_rules42_table.py`(足した欄・行の数・
  下限の印の 4 行)・見出しの試験 3 本(`test_stage2_resume_arm.py`・`test_stage2_default_2_4.py`・`test_wage_occupation.py`=
  既定 on の見出しは `rules_42b` も持つ)。
- 件数は §11。`lint-imports` 5 kept・0 broken。`tests/c7` は回していない。

## 9. 限界・仮採用・親に確かめてほしいこと

仮採用(発注のとおり・宣言は台帳 §10):

- 合計所得=前年の収入(月の額面 × 12)− 給与所得控除(4-2 の expedient のまま)。住民税の所得割の 100 円未満の切り捨て・都民税と
  区民税を分けた端数・6 月の端数寄せは入れていない。調整控除は 5% をまとめて 1 円未満の切り捨て。
- 年齢=母集団の年齢(誕生日の前日に資格を失う決まり・月の途中・1 月 1 日の年齢は入れていない)・年齢不明は上限の内。
- 75 歳以上の後期高齢者医療の保険料は天引きしない(空欄)。非課税の障害者・寡婦・ひとり親は入れていない。
- 拠出金の端数=全額の 1 円未満の切り捨て(雇用主の分の既存の形=`DOC-rules42-rounding` の雇用主の分と同じ考え・行の文には
  足していない)。

問い(推測で埋めていない):

1. **法令 ID の 2 つ**: 〔検収〕親が実読した ID と同じ=解けた。
2. **URL の asof**: 〔検収 低 1・親の判断〕asof なしの `?elm=MainProvision-Article_<条>` に直した(§2)。
3. **未成年者=18 歳未満**: 発注の値=宣言(民法 4 条の成年=条文は本段で読んでいない・親の次の一次確認のついで)。
4. **調整控除の 37 条(都民税 2%)・非課税の 295 条 3 項**: 〔検収 低 2〕出典の `article` と §1 に「未読=都主税局の頁の値」と
   書いた(親が読んだのは 314 条の 6 と 295 条 1 項 2 号)。
5. **住民税の 3 行の asof**: 既存の住民税の行の 2026-06-01 に下限の印(発注どおり)。条文は 2026-10-16 の版で読んだ=令和 8 年度分
   (2026-06〜)の版とは比べていない。
6. **非課税の 0 体**: この 5,000 体の給料日では非課税に当たる体が 0(額面が十分に高い)。合計所得 45 万円以下は月の額面
   91,667 円以下(給与所得控除 54,167 円の帯)。未成年者 19 体はどれも 135 万円超。
7. **再開のランの `RunResult.conserved` が偽**: 写し(`f27377a`)でも同じ=本段の外。日次の保存則は残差 0。
8. **1 日の 19 構成が on でも動かない**: 版上げだが、1 日の byte-check では見えない(給料日を含まない)。給料日を含む 2 日の帳簿
   (§5-2)だけが動く。final も給料日が最後の checkpoint の後なので 2 日のランでは同じ(4-2 と同じ形)。

## 10. つなぎの台帳(道具 [tools/add_bridges_r42b.py](tools/add_bridges_r42b.py)・何度回しても同じ)

- 直した: `DOC-rules42-resident-tax-base`(「控除は 2 つだけ=過大の方向」→ 基礎控除・調整控除・非課税を入れた・残るのは前年の
  所得=月 × 12 と都外の体)・`DOC-rules42-enrollment-basis`(年齢の上限の空欄の文を外し、年齢の扱いの宣言に)。
- 外した(removed): `DOC-rules42-employer-levy-missing`(why の末尾に外した印=4-2 の `DOC-ec21-payroll-deduction-blank` の形)。
- 足した 4 行: `DOC-rules42b-legacy-switch`(next-bump・plan)・`DOC-rules42b-late-elderly-medical-blank`・
  `DOC-rules42b-non-taxable-only-minor`・`DOC-rules42b-resident-tax-rounding`(どれも外す段 7・inferred)。
- 台帳 602 → 606 行(active 579 → 582)。c8 の感度の一覧に 4-2 の行は無い=足していない。

## 11. 試験の件数

| 範囲 | passed | failed | errors |
|---|---|---|---|
| `tests/economy tests/engine tests/build_pop tests/c8 tests/tools`(`-n 2 --dist loadfile -m "not slow"`・43 分 40 秒) | 3,816(+直した 1 件) | 1 → 0(下) | 0 |
| slow(`tests/economy tests/engine/rules tests/engine/rights -m slow`・`-n 2 --dist loadfile`) | 50(15 分 20 秒・段 B の試験と 4-2 の再開=通しを含む) | 0 | 0 |

- 全体の 1 回目の failed 1 件=`test_wage_occupation.py::test_wage_path_header_and_resume_check`(見出しの期待に `rules_42b` が
  無い)。直した後、その試験と台帳の試験を回し直して 68 passed。1 skipped(data 以外の理由)。

## 12. 触った共有ファイル

| ファイル | 触り方 |
|---|---|
| `docs/design/rules-table.json` | 末尾に 4 行・健保と厚年の行に欄 2 つと note の末尾 1 文 |
| `docs/design/bridging-ledger.json` | 末尾に 4 行・既存の 3 行の欄(§10) |
| `src/shibuya/economy/taxes.py` | 新しい行の id・`PayrollTables` の欄・`payroll_tables` の `r42b`・住民税の読み手・`Enrollment`/`Deductions` の欄・`enrollment`/`deductions` の分岐 |
| `src/shibuya/economy/stage2.py` | `payroll_deductions` と `_payroll_law` に `r42b`・`_empty_meter` の引数・計器の鍵・manifest の `plan.rules_42b` |
| `src/shibuya/engine/economy_rules.py` | 腕 `SHIBUYA_RULES_42B`・`PayrollInputs.rules_42b` |
| `src/shibuya/engine/economy_stage2.py` | `header_fields` と `check_resume` に各 1 か所 |
| `src/shibuya/economy/accounts.py` | 注の 1 行だけ(登録は変えない) |
| `docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py` | `SWITCH_ENV` に `SHIBUYA_RULES_42B`(親が rebase で解く) |
| 試験 | §8 |

`cli.py`・`manifest_sections.py`・状態台帳(`state_ledger.py`)・系の表(`systems/table.py`)は触っていない(状態の行は増えない)。

## 13. 独立検収の直し(条件つき受入 高 0・中 0・低 6 → 低 1〜4・6 を直した・低 5 は親が PENDING へ)

| # | 直し方 | 場所 |
|---|---|---|
| 低 1 | 新しい e-Gov の出典 7 つの URL を `law_data/<法令 ID>?elm=MainProvision-Article_<条>`(asof なし)に・読んだ版は `version` に文で(施行日と 2026-10-22 取得)。4-2 の行は触らない。URL の形を見る試験 2 か所も同じ形に | `docs/design/rules-table.json`・`tests/economy/test_rules42b_payroll.py`(末尾)・`tests/engine/rules/test_rules_table_schema.py`(4-2b の枝) |
| 低 2 | 37 条と 295 条 3 項は「未読=都主税局の頁の値」と `article` と §1 に | `rules-table.json`・本書 §1 |
| 低 3 | docstring の鍵を `economy.stage2.plan.rules_42b` に | `src/shibuya/economy/stage2.py` |
| 低 4 | 拠出金の 1 円未満の切り捨てを `DOC-rules42-rounding` の what に 1 文(道具の FIX に足した=冪等・`f27377a` の台帳から 1 回で同じバイト) | `tools/add_bridges_r42b.py`・`docs/design/bridging-ledger.json` |
| 低 6 | 4-2 の版の状態のファイルは既定 on では再開できない(off が要る=設計どおり)を §4 に 1 文 | 本書 §4 |
| 低 5 | 再開のランの `RunResult.conserved`(本段の前から)=親が PENDING に載せる=触らない | ― |

値と挙動は変えていない(規則の表の sha は出典の文と URL の分だけ動く=`3a22317cf609aad6` → `1490c5a2fdc8beb4`)。
- 直した後の試験: `tests/engine/rules tests/economy`(`-n 2 --dist loadfile -m "not slow"`)434 passed・0 failed・0 errors・`tests/engine/bridging` 49 passed・`lint-imports` 5 kept・0 broken・`scan_secrets` CLEAN。

## §親の検収(第337・2026-10-23・Fable 5.1)

- **実在と差分**: 作業木の 29 本(src 5・tests 8+新規 2・docs 15・表と台帳)を親がディスクで確かめ、明示の一覧で stage(`commit_check` 一覧 29=ステージ 29・秘密スキャン CLEAN・絶対パスと個人名 0・CR 0・新しい識別子に `open`/`tick` 0)。親 commit ad4b682 → 本体 01649bb(カレンダー 3 の後)へ rebase=衝突 2(`byte_check_10e.py` の `SWITCH_ENV`=両方の行を残す・`bridging-ledger.json`=本体の台帳を取って `add_bridges_r42b.py` を再適用=620 行・active 595・重複 0)=`c4c7f1f`。rebase の後の台帳・規則・カレンダー 3 の試験 180 passed。
- **値の正**: 入れた値は親が原典で確かめた R-118 §10-2 のとおり(写し検査=検収役が 1 つずつ突き合わせ・親も規則の表の 4 行と 2 欄を読んだ)。法令 ID 5 つと読んだ版は親の取得と同じ。出典の URL は親が読んだ形(asof なし・版は文)。
- **既定の byte-check(親・4 構成)**: 本体 01649bb の src の写しと作業木 c4c7f1f の src で `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` の 25 欄が全部同じ(1 日のランは給料日を含まない=動くのは給料日の帳簿だけ・[byte_check_r42b_parent_4cfg.json](byte_check_r42b_parent_4cfg.json))。給料日を含む 2 日の動いた量と体ごとの検算 0 は実装役と検収役が別の実装で出した(§8・review.md)。
- **範囲の試験(親・-n 4・not slow)**: `tests/economy tests/engine tests/perception tests/build_pop tests/c8 tests/tools`=**4,249 passed・1 skipped・0 failed・0 errors**(27 分 44 秒)。
- **data 無しの写しの全体試験(CI-1 と同じ印・c4c7f1f)**: **5,781 passed・290 skipped(data 無し)・0 failed・0 errors**(33 分 15 秒・faulthandler 900 秒の門に当たらず)。
- **親の判断**: 検収の低 1〜6 は直し済み(URL の形・未読の条の印・docstring・端数の文・README の注)。低 5(再開の `conserved` が偽=本段の前から・帳簿の起点のずれ)は PENDING §5 に親案(小さな整理で起点を揃える)で載せる。空欄の宣言 3 行の外す段 7 は受入。小さな版上げ=安定版のタグ `stable-v2-before-rules-42b` を 01649bb に打ち、`SHIBUYA_RULES_42B` は next-bump で消す。
- **読んだ所**: `economy/taxes.py`(`resident_tax_monthly` の基礎控除・調整控除・非課税の分岐・`enrollment` の `pension`/`age`・`deductions` の拠出金=厚年の標準報酬 × 率の切り捨て・雇用主だけ)・`engine/economy_rules.py`(腕)・`docs/design/rules-table.json`(新 4 行と 2 欄の出典)。
