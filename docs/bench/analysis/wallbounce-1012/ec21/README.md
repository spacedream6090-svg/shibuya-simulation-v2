# 第 2 期 2-1 経済 EC(CP2 の段階 2)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `2-1/economy`(土台 HEAD `f2405e3`)。commit は親。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-11(EC1〜EC6・税・信用 C1〜C3・v1 の手持ちのお金の問題と直し方・見張り)・[計画 10-12](../../../../design/v2-implementation-plan-2026-10-12.md) 第 2 期 2-1・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §0-3(新しい問いは既定 off の腕で仮採用)・[口の約束 1-9](../../../../design/v2-foundation-contracts-2026-10-13.md)(約束 (3) 保存則の検算を全登録に)・[経済の設計](../../../../design/v2-boundary-economy-design.md) §2・1-9 の記録 [cp2/README.md](../cp2/README.md)(§2 口と約束・§4 AST の検査)。
- 数は実測。生の出力は作業木の `_bc/`(git の外)。比べた結果と道具だけをこのフォルダに置く(道具は `tools/`・絶対パスなし)。
- 道具: `tools/stage2_two_day.py`(世界資産の 2 日のランを腕 off・on・部品を 1 つずつ止めた 7 本で回す・`--with-port` で腕 on × 候補の口の腕 port の 1 本を足す・`summary` で §6 の表の行)・`tools/split_l2_l3.py`(ATM の表だけ検収の前の作り方に戻した腕 on の 1 本=来街者と銀行の支店の動いた量を分ける)・`tools/probe_ec21.py`(系ごとの指紋を本体の HEAD と 3 構成で比べる=1-3 の `probe_e13.py` の形)。byte-check は 1-9 の道具 `cp2/tools/byte_check_cp2.py`(10e の 19 構成+帳簿の 11 欄)をそのまま使った。

## 0. 結論

- 新しい動きは全部 1 つの腕 **`--economy-stage2 {off,on}`**(環境変数 `SHIBUYA_ECONOMY_STAGE2`・既定 off)の中。部品は **`--economy-stage2-parts wages,withdraw,payment,tax,visitors`**(環境変数 `SHIBUYA_ECONOMY_STAGE2_PARTS`・既定=全部)で 1 つずつ止められる。腕は組み立てのときに読む(`run_day` の引数でも設定の指紋でもない=出来事の記録・記憶の器・候補の口の腕と同じ扱い)。腕と部品は manifest の `economy.stage2` に出る。
- **腕 off: byte-check 19/19 構成で final が同じ・36 欄が全部同じ**(10e の 25 欄+帳簿の残高・世帯の現金・流れの集約行・取引の件数・却下・容量・`state_hash`・物の台帳・生ログの行と末尾 16,384 行・落ちた行=§5)。
- **腕 on(5,000 体・2 日・2026-08-24(月)→ 25 日=給料日・検収の直しの後)**: 賃金 2,392 人・1 億 1,284 万円(W6 の組織 → 世帯の口座・原資は外界の売上)・引き出し 463 回・704 万円(OSM の ATM・店の中・銀行の支店 55 点)・口座の購入と食事 29 行・IC の運賃 7,290 行・消費税 115 万円(店 → 政府)・来街者の口座 1,042 体(持ち込みを分けた 2,649 万円)。購入と食事の 16,212 行は全部が原因 `LlmCall(call_id)`・引き出し 463 回のうち 440 回も(検収 A1)。**保存則の検算の残差は毎日 0**(登録の無い流れ 0)・`RunResult.conserved` も真。部品を 1 つ止めるとその流れが 0(§6)。
- **保存則の検算を全登録に直した**(口の約束 1-9 の約束 (3)): 名前のある流れ 17 行(組 15 欄)の表 `accounts.FLOW_REGISTRY` と、日の締めの検算 `checks.conservation_check`(部門の残高の合計の変化 ΔM = 登録の faucet − 登録の sink・残差の科目 `residual`=0・登録の外の組の額 `unregistered`=0)。腕の有無によらず日次の記録の `economy.conservation` に出る。負の対照(登録の無い流れ・登録を 1 行外す)で落ちる。
- 規則の表の最初の読み手: 最低賃金 `anchors.min_wage_hourly(asof)`(2026-10-01 から表の 1,280 円・その前は表に版が無い=直書き 1,226 円=つなぎの台帳 `BR-MIN-WAGE-HOURLY-1226`)と消費税 `anchors.consumption_tax_rate(asof)`(7.8%×(1+22/78)=10%)。
- **v1 の「1 日 1 体 536 円ずつ減る」**(〔検収 M1〕の文言): 減り方は緩んだが止まってはいない(off −1,625/−1,168 → on −839/−521 円/体/日・月の見込み(推測)=支出 約 3.55 万円/体に対し賃金 2.26 万円=現金+預金は月に約 1.29 万円/体 減る=月の時間が短い(A3)ため)。検収の直しの後(来街者の持ち込みを分けた・銀行の支店を足した)は on −736/−406 円/体/日・月の見込みは同じ(1 日目の支出 1 体 1,182 円/日と賃金は変わらない)。2 日で財布 0 の体が 0 なのは腕 off も同じ(区別にならない)。W17 の「勤務」の時間が短い(雇用の行の体の月 38 時間・中央値 39.7 時間=現実の 1/4 程度の見込み・§11 の親に確かめてほしい点 3)。
- 試験: 新しい試験 `tests/economy/stage2/`(§8)。既存の試験の直しは凍結の表と数の試験だけ(§9)。`lint-imports` 5 契約とも守られている。
- **検収(条件つき受入=中 1・低 6)の直しと親の判断 A1〜A9 は §13**(呼の id の配線・実行時の守り・来街者の持ち込みを分ける・銀行の支店 23 を全部・状態のファイルの見出しの腕・口の名の表に引き出しの口・系ごとの指紋)。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/economy_stage2.py`(新) | 腕と部品(`arm`・`set_arm`・`parts`・`set_parts`・`active_parts`)・状態のファイルの見出し `header_fields` と再開の突き合わせ `check_resume`(検収 A5)・ATM の表 `AtmTable`(OSM から `build_atm_table`=ATM・店の中・銀行の支店 55 点・営業時間 `parse_opening_hours`・時間の無い支店は `BANK_DEFAULT_HOURS`・`open_cells`・配列は読み取り専用)・組み立ての物 `Stage2Plan`(暦の口の給料日・日付・締めの刻み・雇用の行=権利台帳 `Rights.pairs`・原因 `Process("payroll"/"atm"/"register")` と `llm_cause(call_id)`=`LlmCall`・組み立ての後は `runner` の外は書けない)・`weekly_work_hours`(W17 の勤務 → 月の時間)・`attach`(組み立てが呼ぶ)・`atm_open_cells`・試験の切替口 `set_atm_table` |
| `src/shibuya/economy/stage2.py`(新) | `MoneyStage2`(初期の預金 `endow`=来街者は持ち込みを分ける・支払い `purchase`/`can_pay`/`pay_fares`・引き出し `withdraw`(口が選んだ行・呼の原因)・呼の控え `note_calls`/`purchase_causes`(検収 A1)・賃金 `before_close`/`payroll`・店の外界の売上 `external_sales`(額 0)・見張り `day_record`/`manifest_record`・成長の宣言・組み立ての後は書けない)・`tax_of`・`payroll_deductions`(器)・expedient の値・バイト予算の定数 |
| `src/shibuya/economy/credit.py`(新) | 信用の器 `CreditBook`(種類 4・借り手・限度・残高・返済日・返済額・延滞・組み立ての後は行の数の外は書けない)と `repay_due`(口座から自動・不足は延滞の記録)=呼び手なし |
| `src/shibuya/economy/ops.py` | `transfer(..., method=)`(`METHOD_CASH`=既定/`METHOD_ACCOUNT`=世帯の脚を預金で・銀行の決済の行を 1 行足す)・行ごとの原因(`cause` に `list`=None の行は出来事なし・計器 `uncaused`=検収 A1)・生ログの列 `_raw_method`・`MONEY_EXTRA_WHAT`(`金:引き出し`・`金:カード`)・`code_of_what`・段階 2 の組(`ledger._stage2_pairs`) |
| `src/shibuya/economy/ledger.py` | `_raw_method` の列と `raw_methods()`・`transfer_many(..., method=, what=)`(口座の払い手は預金で残高を見る・行ごとの原因は通った行の分)・`attach_stage2`・`_stage2_pairs`(読み取り専用=挿したかから導く)・`purchase_many`/`endow_households` を段階 2 に委ねる(腕のランだけ・購入と食事の原因は呼の控えから)・`can_pay_many`/`withdraw_many`/`pay_fares_many`/`note_calls_many`(委ねるだけ)・`on_day_end` で給料日の賃金(締めの前)と保存則の検算(締めの後・腕によらず)・manifest の `economy.stage2`・成長の宣言・輪の係数 `rows_per_agent_day`(腕のランだけ 16.0) |
| `src/shibuya/economy/accounts.py` | 段階 2 の組 `STAGE2_PAIRS`(外界 → 店舗・外界 → 雇用主の消費支出・`MappingProxyType`)・`is_allowed(..., stage2=)`・`faucet_sink_table(stage2=False)`(既定=許された組だけ・`True` で段階 2 の組を末尾に=検収 L6)・名前のある流れの全登録 `FLOW_REGISTRY`・`registered_cells`・`flow_registry_table` |
| `src/shibuya/economy/checks.py` | `conservation_check(close, cells=None)` |
| `src/shibuya/economy/anchors.py` | `min_wage_hourly(asof)`・`consumption_tax_rate(asof)`(規則の表の読み手)・`monthly_wage_amounts(..., hourly=)`・`monthly_wages(..., hourly=, payer_sector=, method=, cause=)`(最初の呼び手=給料日) |
| `src/shibuya/economy/__init__.py` | docstring に `stage2`・`credit` |
| `src/shibuya/engine/resolve.py` | `_payable`(購入・食事の前提「払えるか」=腕の payment のランだけ現金か口座)・`_stage2_note_calls`(列の捌きと行為の適用の前に、金に触れる行為の呼の id と支払いの答えを台帳に控える=検収 A1)・`_stage2_withdraw`(`apply` の行為の適用の後に、この刻みに判断した体のうち営業中の ATM のセルの体を台帳に渡す・口が選んだ行と呼の id も) |
| `src/shibuya/engine/processes/rail.py` | `pay_fares`: 腕の payment のランだけ `pay_fares_many`(IC 既定) |
| `src/shibuya/engine/decision/layer.py`・`port.py` | 腕 port: 営業中の ATM のセルで候補「お金を下ろす」(源 affordance)・購入と食事の候補の文に「支払いは現金かカード」・計器 `decision_port.stage2`・口の答え(お金を下ろす・`Choice.payment`=現金/カード)を印にして控える `take_stage2_hint`(検収 A1) |
| `src/shibuya/engine/commit.py` | `IntentBatch` の任意の 2 列 `call_id`・`s2_flags`(既定 None=今のまま・連結・抜き出しで運ぶ)と印 `S2_*`(検収 A1) |
| `src/shibuya/engine/systems/decide.py`・`judge.py` | 口の印を保留の組の末尾へ(印があるときだけ)・腕のランだけ LLM の意図に呼の id(保留の組の `call_id`)と印を付ける(検収 A1) |
| `src/shibuya/engine/systems/state_io.py`・`allow.py` | 状態のファイルの見出しに `economy_stage2`(腕のランだけ=検収 A5)・口の名の表 `TRANSFER_PORTS_HOUSEHOLD` に `withdraw_many`(検収 A7) |
| `src/shibuya/engine/events/links.py` | `MoneyEventLink` が行ごとの原因を受ける(None の行は書かない=検収 A1) |
| `src/shibuya/engine/rights/ledger.py` | 読み口 `Rights.pairs(kind, holder_kind, object_kind, t_ns)` |
| `src/shibuya/engine/events/vocab.py` | 金の語 2 つ(`MONEY_EXTRA_WORDS`)を表の末尾に・原因の名 `ECONOMY_PROCESSES` を末尾に・版 `events-vocab/2-1` |
| `src/shibuya/engine/systems/build.py` | 腕の組み立て(`_ES2.attach`=初期の財布の前)・`Stage2Plan.runner`・`Fixtures.atms`・候補の口へ組み立ての物・再開で見出しの腕を突き合わせる(検収 A5) |
| `src/shibuya/engine/systems/boxes.py` | `Fixtures.atms`(既定 None) |
| `src/shibuya/engine/systems/table.py` | 系の宣言: phase_c・day_close・close_final に `EC:ledger.* EM:ledger.*`・world に `EM:ledger.*` |
| `src/shibuya/engine/systems/report.py`・`engine/run.py` | `RunResult.money_stage2_in`(引き出し+口座の購入・食事+IC の運賃)を `conserved` の式の左辺に足す(腕の無いランは 0) |
| `src/shibuya/engine/state_ledger.py` | 行 `EC`・`ATM`・`CR`・`EM`(§9)と除外 1 つ(注に検収 A1・L1・L3) |
| `src/shibuya/engine/manifest_sections.py` | `economy.stage2`(設定 8・観測 14)・`decision_port.stage2`(観測) |
| `src/shibuya/cli.py` | `--economy-stage2`・`--economy-stage2-parts`・腕のランだけ雇用主の口を W6 の組織の数(`load_employers`=9,872)・輪の係数 16.0(腕の無いランは台帳の作り方を今のまま) |
| `docs/design/bridging-ledger.json` | 文書の行 `DOC-ec21-*` 18 行(§10)・`DOC-money-uncaused-rows` を removed に(検収 A1) |
| `tests/economy/stage2/`(新) | 試験 11 ファイル(§8) |

## 2. 部品ごとの流れ(文字の図)

```
賃金(wages・日の締め=給料日 25 日・土休なら前の営業日)
  権利台帳 employ(体 → 組織 W16 org_id / 体 → 店=担当従業者)─ 体ごとに最初の 1 行
  外界 ──消費支出(外界の売上=原資・払う額と同じ・faucet)──▶ 雇用主(組織)/店舗
  雇用主/店舗 ──賃金(口座)──▶ 世帯の預金  [行 2: 本体 → 決済(世帯 → 銀行の預金純増)]
  原因 Process("payroll")・額=月の時間(W17 の勤務 × 52/12)× 最低賃金(規則の表 asof)・天引き=0(器)

引き出し(withdraw・行為の解決=この刻みに判断した体の副の判断)
  営業中の ATM・銀行の支店のセル(OSM 55 点)&(財布 < 1 日の消費 か 口が「お金を下ろす」を選んだ)
    → 銀行 ──預金純増(金:引き出し)──▶ 世帯の現金
  額=min(預金, 1 日の消費 × 3) の千円単位・原因 LlmCall(この刻みの判断の呼)/呼の無い体は Process("atm")

支払い(payment)
  購入・食事(原因 LlmCall=その体の最後の金に触れる行為の呼・口の答えがあれば先に従う):
     財布 ≥ 価格 → 現金(世帯 → 店)/ 財布 < 価格 & 預金 ≥ 価格 → 口座:
     銀行 ──預金純増(金:カード)──▶ 世帯 ──消費支出──▶ 店舗  [世帯の現金は動かない・方法の列=1]
  運賃: 預金 ≥ 運賃 → IC(口座)/ 足りなければ現金(世帯 → 外界の持ち出し)

税(tax・レジ)
  店舗 ──税(税込の額 × 10/110 の切り捨て)──▶ 政府  原因 Process("register")=店の手元は税抜き

来街者(visitors・組み立て)
  来街者(種別 1・6・7)の持ち込み(初期の財布)を分ける: 世帯の現金 ──預金純増──▶ 預金 =財布 × 0.5(合計は不変)
  (腕 on なら部品によらず、来街者でない体の預金=1 日の消費 × 30 日)
```

## 3. 本人の判断の代役の規則(mock と古典=expedient)と腕 port

- 引き出しは主の行為(語彙の 12 語)に添える**副の判断**(行為の語彙を変えない形)。`apply` の行為の適用の後に、この刻みに判断した体(エンジン継続でない)のうち営業中の ATM のセルの体を台帳に渡し、台帳が規則「財布 < 1 日の消費 × 1」で下ろす(腕 legacy・port の両方で同じ=mock と古典の番号は今と同じ)。
- 腕 port: 営業中の ATM のセルで候補「お金を下ろす(ここでできる)」を源 affordance で足す・購入と食事の候補の文に「(支払いは現金かカード)」を添える。計器 `decision_port.stage2`(出した数・選んだ数・注を添えた数・支払いを答えた数)。mock は行為の語彙の候補だけを選ぶ=選んだ数 0・final は腕 legacy と同じ(試験)。〔検収 A1〕口の答えは行為の解決へ運ぶ: 「お金を下ろす」=印 `S2_WITHDRAW`(規則を通さず下ろす)・購入と食事の `Choice.payment`(現金/カード)=印 `S2_PAY_*`(その方法で足りれば先に従う)。印は保留の組の末尾 → `IntentBatch.s2_flags` → `resolve.apply` → 台帳。J0 の 3 つの実装は答えない(LLM の文は今のまま=候補と注を見せない)ので、試験は mock の口の答えを試験の中だけ差し替えて確かめた(§13)。
- 支払いの方法: 財布が足りれば現金・足りなければ口座(本人の属性があれば優先=今は無い)。運賃は IC が既定。口座も足りなければ今の結果コード(残高不足=`MONEY_SHORT`・`FARE_SHORT`)のまま。

## 4. faucet/sink の全登録と保存則の検算

名前のある流れ(`accounts.FLOW_REGISTRY`・区分は `flow_kind` の規則と同じ=試験):

| 名前 | 科目 | 払い手 | 受け手 | 区分 | 段 |
|---|---|---|---|---|---|
| 初期の財布 | 来街者持込 | 外界 | 世帯 | FAUCET | 1 |
| 参入資本(外界) | 参入資本 | 外界 | 店舗 | FAUCET | 1 |
| 購入・食事 | 消費支出 | 世帯 | 店舗 | INTERNAL | 1 |
| 運賃 | 持ち出し | 世帯 | 外界 | SINK | 1 |
| 補充の代金(域外仕入) | 域外仕入 | 店舗 | 外界 | SINK | 1 |
| 逸脱比例コスト | 逸脱比例コスト | 店舗 | 政府 | SINK | 1 |
| 域外雇用主の賃金 | 賃金 | 外界 | 世帯 | FAUCET | 1 |
| 預け入れ・口座の入金 | 預金純増 | 世帯 | 銀行 | INTERNAL | 1 |
| 引き出し・口座の決済 | 預金純増 | 銀行 | 世帯 | INTERNAL | 1 |
| 初期の預金 | 来街者持込 | 外界 | 世帯 | FAUCET | 2 |
| 来街者の持ち込みの口座の分(預け入れ) | 預金純増 | 世帯 | 銀行 | INTERNAL | 2 |
| 賃金(雇用主) | 賃金 | 雇用主 | 世帯 | INTERNAL | 2 |
| 賃金(店の担当従業者) | 賃金 | 店舗 | 世帯 | INTERNAL | 2 |
| 賃金の原資(雇用主の外界の売上) | 消費支出 | 外界 | 雇用主 | FAUCET | 2 |
| 外界の売上(店・賃金の原資と範囲の外の取引先) | 消費支出 | 外界 | 店舗 | FAUCET | 2 |
| 消費税 | 税 | 店舗 | 政府 | SINK | 2 |
| 給与の天引き(器) | 税 | 世帯 | 政府 | SINK | 2 |

- 17 行・組 15 欄(来街者持込 外界 → 世帯 に名前が 2 つ・預金純増 世帯 → 銀行 に 2 つ)。`faucet_sink_table()`(許された組の全部)は 77 行のまま・`faucet_sink_table(stage2=True)` で 79 行(段階 2 の組 2 行を末尾に・タグ `段階 2:expedient`=検収 L6)。
- 検算(`checks.conservation_check`・日の締めの後): ΔM(世帯・店舗・雇用主の現金+預金の合計の変化)− (登録の faucet − 登録の sink) = `residual`(残差の科目の名)= 0・登録の外の組の額 `unregistered` = 0・科目「残差科目」の額 = 0 で `ok`。銀行との流れは預金純増だけが M に効かない(登録)・利子などは登録の外=落ちる(信用の返済は呼び手を作る段で登録する)。
- 腕 off の 19 構成・腕 on の 7 本の 2 日のラン・合成の世界の 2 日の全部で毎日 `ok`(残差 0)。

## 5. 結果不変(腕 off)

| 確かめ | やり方 | 結果 |
|---|---|---|
| byte-check 19 構成([byte_check_ec21_off.json](byte_check_ec21_off.json)) | `cp2/tools/byte_check_cp2.py`(5,000 体・seed 1・1 日・テープつき)。a=本体 HEAD `f2405e3` の src の写し・b=作業木の src(腕 off=既定) | **final 19/19 同じ・36 欄が 19/19 で全部同じ**(full-hash・生ログの行の sha・帳簿の残高・物の台帳を含む)。manifest の `economy` も同じ(`stage2` の鍵は立たない) |
| 合成の世界・世界資産の腕 off のラン | 試験 `test_arm_off_changes_nothing_on_the_ledger`・`test_world_two_days_without_the_arm` | 段階 2 の中身・信用の器・段階 2 の組は無い・生ログの方法の列は 0・保存則の検算は毎日 ok |

- 腕 off で増える記録の欄: 日次の記録の `economy.conservation`(保存則の検算=腕によらず)・manifest の `decision_port.stage2`(腕 legacy は null)・manifest の表 `manifest_sections`(`economy.stage2` と `decision_port.stage2` の道筋)・つなぎの台帳の件数 `bridges_count`(行が 14 増えた)・`bridges_version`。既存の欄の名と順は変えていない。
- byte-check は最終の src(輪の係数の分を含む=腕 off には効かない)で回し直した結果(§12 の 1)。manifest の `economy` も 19/19 で同じ・日次の記録の `economy` は `conservation` を足しただけで残りは同じ(全部 ok)・出来事の行の数も同じ。

## 6. 腕 on の動いた量(世界資産・5,000 体・seed 1・既定 v3・2026-08-24 → 25・`tools/stage2_two_day.py`)

生の結果: 検収の直しの後 [two_day_ec21_fix.json](two_day_ec21_fix.json)(8 本=7 本+腕 on × 候補の口の腕 port・輪の係数 16.0)・検収の前 [two_day_ec21.json](two_day_ec21.json)(7 本・輪の係数 13.5 の版=溢れの欄は §12 の 16.0 の版 [two_day_ec21_on16.json](two_day_ec21_on16.json) で 0 に)。開始日は暦の口(`start_sim_datetime`)で指定した(開始日の検査=月曜・連続する平日を通る。2026-08-24・25 の影(W9)は無く、いちばん近い 07-28 の影を読む警告が出る=10e の既存の expedient)。

検収の直しの後(輪の係数 16.0):

| 腕・部品 | final | 呼数 | 行/体/日(0・1 日目) | 溢れ | 保存則 残差 | 賃金(人・円) | 引き出し(回・円) | 口座の購入・食事(行・円) | IC(行) | 税(円) | 来街者の口座(体) | 世帯の現金の 1 体の増減(0・1 日目) | conserved |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 17f89bf0a109f2dd | 145,049 | 4.124・2.066 | 0 | 0・0 | 0・0 | 0・0 | 0・0 | 0 | 0 | 0 | −1,625.5・−1,168.4 | True |
| on(全部) | 5a40399e189c7a1e | 144,954 | 8.632・5.408 | 0 | 0・0 | 2,392・112,838,004 | 463・7,043,000 | 29・27,100 | 7,290 | 1,151,765 | 1,042 | −735.9・−406.4 | True |
| on − wages | 5a40399e189c7a1e | 144,954 | 8.632・4.176 | 0 | 0・0 | 0・0 | 463・7,043,000 | 29・27,100 | 7,290 | 1,151,765 | 1,042 | −735.9・−406.4 | True |
| on − withdraw | 9659e0e4bcd7a4cf | 144,889 | 8.587・5.409 | 0 | 0・0 | 2,392・112,838,004 | 0・0 | 124・111,600 | 7,329 | 1,155,948 | 1,042 | −1,503.3・−1,038.3 | True |
| on − payment | e740a18fab29299e | 145,201 | 7.928・4.679 | 0 | 0・0 | 2,392・112,838,004 | 479・7,369,000 | 0・0 | 0 | 1,157,024 | 1,042 | −830.5・−525.3 | True |
| on − tax | 7d82d2a16cb00885 | 144,954 | 6.685・4.112 | 0 | 0・0 | 2,392・112,838,004 | 463・7,043,000 | 29・27,100 | 7,290 | 0 | 1,042 | −735.9・−406.4 | True |
| on − visitors | 8d820f2b61ec8eb5 | 144,954 | 8.300・5.285 | 0 | 0・0 | 2,392・112,838,004 | 269・4,833,000 | 27・24,800 | 6,256 | 1,151,765 | 0 | −1,033.4・−588.6 | True |
| on(全部)× 候補の口の腕 port(mock の口) | 5a40399e189c7a1e | 144,954 | 8.632・5.408 | 0 | 0・0 | 2,392・112,838,004 | 463・7,043,000 | 29・27,100 | 7,290 | 1,151,765 | 1,042 | −735.9・−406.4 | True |

検収の前(来街者の預金は持ち込みに上乗せ・ATM 43 点・呼の配線なし・輪の係数 13.5):

| 腕・部品 | final | 呼数 | 行/体/日(0・1 日目) | 溢れ(係数 13.5) | 保存則 残差 | 賃金(人・円) | 引き出し(回・円) | 口座の購入・食事(行・円) | IC(行) | 税(円) | 来街者の口座(体) | 世帯の現金の 1 体の増減(0・1 日目) | conserved |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| off | 17f89bf0a109f2dd | 145,049 | 4.124・2.066 | 0 | 0・0 | 0・0 | 0・0 | 0・0 | 0 | 0 | 0 | −1,625.5・−1,168.4 | True |
| on(全部) | c64b7f6cc6a4e280 | 144,954 | 8.824・5.402 | 3,630 | 0・0 | 2,392・112,838,004 | 305・5,950,000 | 28・25,600 | 7,339 | 1,151,765 | 1,042 | −838.6・−520.8 | True |
| on − wages | c64b7f6cc6a4e280 | 144,954 | 8.824・4.171 | 0 | 0・0 | 0・0 | 305・5,950,000 | 28・25,600 | 7,339 | 1,151,765 | 1,042 | −838.6・−520.8 | True |
| on − withdraw | 87d9cd8c42cbe317 | 144,889 | 8.795・5.409 | 3,521 | 0・0 | 2,392・112,838,004 | 0・0 | 121・107,800 | 7,329 | 1,155,948 | 1,042 | −1,503.3・−1,039.0 | True |
| on − payment | 57723bec2e35f7b9 | 145,197 | 8.116・4.669 | 0 | 0・0 | 2,392・112,838,004 | 328・6,374,000 | 0・0 | 0 | 1,157,088 | 1,042 | −930.1・−624.9 | True |
| on − tax | e17b652a714d4135 | 144,954 | 6.876・4.107 | 0 | 0・0 | 2,392・112,838,004 | 305・5,950,000 | 28・25,600 | 7,339 | 0 | 1,042 | −838.6・−520.8 | True |
| on − visitors | 595e91a29382792c | 144,954 | 8.302・5.285 | 437 | 0・0 | 2,392・112,838,004 | 279・5,042,000 | 28・25,600 | 6,256 | 1,151,765 | 0 | −989.8・−590.2 | True |

- **部品を 1 つ止めると当該の流れが 0**: wages → 賃金 0・withdraw → 引き出し 0・payment → 口座の購入と IC 0・tax → 税 0・visitors → 来街者の口座 0。どの本も保存則の残差 0・`conserved` 真。
- wages を止めても final は同じ(賃金は 1 日目の締めに口座へ入る=2 日のランの行動には効かない)。tax を止めると呼数は同じで final は動く(税の分だけ店と政府の現金=帳簿の残高 O57(軸 1 behavior)が違う)。〔前の版の「tax を止めても final は同じ」は表と合わない誤りだった=直した〕withdraw・payment・visitors は財布(行動の前提)を変えるので呼数と final が動く。腕 port(mock の口)は腕 legacy と final・呼数が同じ(mock は「お金を下ろす」を選ばず支払いも答えない)。
- 賃金: W6 の組織の雇用の行 2,392 人(雇用の行 2,421 人のうち勤務の時間 0 が 29 人)・1 億 1,284 万円(1 人 4.7 万円=月 38 時間 × 1,226 円)・原資の外界の売上も同じ額・天引き 0・雇用主の口の外 0。最低賃金は asof 2026-08-25=表に版が無い=直書き 1,226 円(`anchors.MIN_WAGE_HOURLY`)。
- 引き出し(検収の直しの後): OSM の 55 点(42 セル・写せない点 0・種類=単独の ATM 7・店の中 25・銀行の支店 23・営業時間=要素の印 26・無い 9 は 24 時間・時間の無い銀行の支店 20 は平日 9:00-15:00)。判断した体のうち営業中の ATM・支店のセルに居た延べ 23,079 回のうち、規則「財布 < 1 日の消費」に当たった 667 回のうち 463 回が下ろした(預金の不足 204=来街者は持ち込みの半分しか預金が無い)。原因は 440 回が `LlmCall`(その刻みの判断の呼)・23 回が `Process("atm")`(呼の無い体=着いて実行する意図など)。〔検収の前〕43 点(37 セル・銀行 11)・延べ 25,229 回・305 回が下ろした(預金の不足 0)。
- 支払い(検収の直しの後): 購入と食事 16,212 行(全部が原因 `LlmCall`)のうち口座 29 行(財布の中央値 1.8 万円>価格)。IC の運賃 7,290 行・現金の運賃 49 行(預金の足りない来街者)。消費税 115 万円(税込 1,277 万円 × 10/110 の切り捨て)。〔検収の前〕口座 28 行・IC 7,339 行・現金の運賃 0 行。
- 財布と預金(1 日目の終わり・1 体・検収の直しの後): 財布 p10 7,501・p50 18,358・p90 39,603 円(財布 0 の体 0)・預金 p10 20,576・p50 194,464・p90 234,752 円。貨幣供給量は給料日に 1 体 +22,280 円。〔検収の前〕財布 p10 7,789・p50 20,025・p90 52,604 円・預金 p10 35,320 円・世帯の現金+預金は 0 日目の終わり 1 体 181,013 円 → 1 日目の終わり 202,399 円(給料日 +21,385 円)。
- **v1 の「1 日 1 体 536 円ずつ減る」**(〔検収 M1〕): 世帯の現金は腕 off で 1 体 −1,625・−1,168 円/日(10-03 の 536 円・10d の 1,171 円と版と日が違う)。減り方は緩んだが止まってはいない(off −1,625/−1,168 → on −839/−521 円/体/日・月の見込み(推測)=支出 約 3.55 万円/体に対し賃金 2.26 万円=現金+預金は月に約 1.29 万円/体 減る=月の時間が短い(A3)ため)。見込みの材料: 1 日目の世帯の支出=購入と食事 5,227,600 円+運賃 683,100 円=1 体 1,182 円/日 × 30 日=35,464 円・月の賃金 112,838,004 ÷ 5,000=22,568 円(2 日の外挿=推測)。検収の直しの後は on −736/−406 円/体/日(1 日目の支出と賃金は同じ=月の見込みも同じ)。2 日で財布 0 の体が 0 なのは腕 off も同じ(尽きる型が止まったかの区別にはならない)。
- 生ログ: 腕 on は 0 日目 8.824 行/体(初期の預金 2 行・IC 2 行/乗車・税 1 行/購入)・1 日目 5.402 行/体(給料日の賃金 2 行/人と原資)。腕のランの輪の係数を 13.5 → 16.0 に上げた後の溢れ 0 は §12。

## 7. バイト予算

| 物 | 腕 off(既定) | 腕 on | 宣言の場所 |
|---|---|---|---|
| 生ログの支払いの方法の列 `_raw_method`(int8) | 1 B/行=輪の 1 行 23 B の切り上げの空き(`RAW_ROW_BYTES` 24 は不変・`bytes_total` も不変)。5,000 体 32,500 B・39 万体 2,535,436 B(実の確保は 1 B/行ぶん増える=宣言の 24 B/行の中) | 輪は 16.0 行/体/日(§11)=5,000 体 80,000 行(36 B/行=24+目印 12 で 2.88 MB)・39 万体 6,241,072 行=224.7 MB(係数 6.5 の 91.3 MB の約 2.5 倍) | `ledger.RAW_ROW_BYTES` の注・`stage2.STAGE2_TRANSFERS_PER_AGENT_PER_DAY`・成長の宣言 `transfer_log`/`transfer_log_event_ids`(係数を台帳から渡す) |
| 段階 2 の中身(体あたり) | 0(作らない) | 107 B/体(中身 4 列 25 B+組み立ての物 2 列 16 B+〔検収 A1〕呼の控え 2 列 66 B=呼の id への参照 8+文字列 57+支払いの答え 1)=5,000 体 535 KB・39 万体 41.7 MB(呼の id の文字列は全部の体が持つときの上限) | `stage2.BYTES_PER_AGENT`・成長の宣言 `economy_stage2`(伸びない・実測の増分 0) |
| ATM の表 | 0 | 55 点 × 66 B=3,630 B | `stage2.ATM_ROW_BYTES` |
| 雇用主の口 | 1 口(今のまま) | 9,872 口 × 44 B=434,368 B | `stage2.EMPLOYER_ROW_BYTES` |
| 信用の器 | 0 | 0 行(9 列 × 長さ 0) | — |

- 逐次ループの新設: なし(どの口も配列演算。Python のループは部門 2 つ・登録の行・ATM の点・候補の数・OSM の要素=組み立てで 1 回)。出来事を 1 行ずつ書くループ(原因つきの行の数ぶん)は 1-9 のまま(段階 2 で原因つきの行が増える=税・引き出し・賃金・IC の運賃)。

## 8. 試験

新しい試験 `tests/economy/stage2/`(70 本=66 本+`slow` 4 本・data の要る試験は印 `requires_data`。検収の直しで 3 ファイル 14 本を足した):

- `test_stage2_account_and_conservation.py`(15): 口座の方法(受け手=預金に入り世帯の現金は動かない・払い手=預金から・決済の行・預金の不足は残高不足で数える・検算①②と流れの表の和と保存則の検算・**世帯の現金の書き込み窓の外でも口座の脚は書ける**=日の締めの賃金・意味の無い組は例外)・方法の列 0(現金)・金の語 2 つと語彙表と原因の名・段階 2 の組は腕の台帳だけ・faucet/sink 表の末尾・登録の区分=`flow_kind`・保存則の検算の欄と値・**負の対照 2 本**(登録の無い流れ=利子・登録を 1 行外す)・腕なしでも日次に検算。
- `test_stage2_rules_credit_atm.py`(12): **規則の表の読み手**(最低賃金 2026-09-30=1,226・2026-10-01=1,280・消費税 10%・版の前は 0)・月の賃金の式・天引きの器・信用の器(行・自動返済・延滞・返済の流れは登録の外=検算が落ちる)・腕と部品の切替口・座標の定数=build の写し・営業時間の読み・ATM の表の営業中のセル・(data)OSM の 55 点(ATM 7・店の中 25・銀行の支店 23・時間の無い支店 20 は平日 9-15)・暦の口の給料日(8/25(火)・7/25(土)→ 7/24(金))・`Rights.pairs`。
- `test_stage2_money_rules.py`(10): 初期の預金と来街者の口座(持ち込みを分ける=合計は不変)・支払いの方法の規則とレジの税・どちらも足りなければ今の結果コード・**負の対照**(預金が足りなければカードでなく現金に戻る)・引き出しの規則と額と原因の出来事・部品と預金の要る条件・IC の運賃と現金に戻る(`RailProcess.pay_fares` の口)・給料日の賃金(口座・外生の原資・保存則)・部品 off で賃金 0・挿し直しと知らない部品は例外。
- `test_stage2_runs.py`(11): 合成の世界の 2 日(2026-08-24 → 25): 全部の部品で賃金・引き出し・カード・税・来街者の口座・保存則・`conserved`・見張りの分位と表/**部品を 1 つずつ止めると当該の流れが 0**(5 本)/**負の対照**(営業時間の外の ATM では引き出せない)/腕 off は何も変えない/腕 off で部品だけ指定しても無視/腕 port で候補と注が出て mock の行為と final は腕 legacy と同じ/`Fixtures.atms`。
- `test_stage2_writers.py`(4): 新しいモジュールはお金の列を書かない(1-9 の AST の道具)・台帳の窓と残高の配列に触れない・resolve の段階 2 の口の呼び手は phase_c の閉包の中(`writes.soa` に `agents.money`)・引き出しの口は口の名の表の中(`_stage2_withdraw` が AST で引かれる=検収 A7)・基本操作を直に呼ばない。
- `test_stage2_guards.py`(4・検収 L1): 負の対照=ATM の表の配列と出どころ・段階 2 の組の表・`Stage2Plan`(`runner` は 1 回だけ)・`MoneyStage2`・`CreditBook`・`Ledger._stage2_pairs` を書くと落ちる。
- `test_stage2_calls.py`(8・検収 A1): 基本操作の行ごとの原因(None の行は出来事なし・計器 `uncaused`・長さと型の違いは落ちる・却下の行の原因は書かない)・`IntentBatch` の任意の 2 列が連結と抜き出しで運ばれる・呼の控え → 購入・食事の原因 `LlmCall`・支払いの答え(カード=口座・預金が無ければ現金に戻る)・口が選んだ引き出しは規則を通らず原因は呼・判断の口の層の印は 1 回だけ取り出せる・合成の世界の 1 日(腕 legacy=呼の id が運ばれ購入・食事のほとんどが原因を持つ/腕 port で mock の口の答えを試験の中だけ差し替え=引き出しと口座の支払いが行為に届く・保存則の残差 0)。
- `test_stage2_resume_arm.py`(2・検収 A5): 腕 on の状態のファイルの見出しに腕と部品・部品か腕が違う再開は止まる・そろえた再開は通しと同じ final/腕 off の見出しは今のまま・腕 on で再開すると止まる。
- `test_stage2_world_two_day.py`(`slow`・data・2): 世界資産 5,000 体・2 日・腕 on(雇用主の口 9,872・組織の賃金・ATM の引き出し・IC・税・来街者の口座・毎日 残差 0・`conserved`・ATM 55 点・輪 80,000 行で溢れ 0)/腕 off(段階 2 の欄なし・検算 ok・方法の列 0)。
- `test_stage2_resume.py`(`slow`・data・2): 腕 on の 300 体 2 日を日の境目と 1 日目の昼で止めて再開=final・日の終わりの 2 つのハッシュ・残高・保存則の検算(日の境目なら段階 2 の日の欄も)が通しと同じ。

既存の試験(本書の作業木・data あり):

- 全体 `-m "not gpu and not slow" -n 4 --dist loadfile`: **4,632 passed・4 failed・1 xfailed(39 分 20 秒・ほかの作業木と同時)**。落ちた 4 件: ① `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`=作業木の `data` の junction 由来の既知の落ち。② `tests/engine/rules/test_rules_table_schema.py::test_only_the_manifest_and_the_daily_record_import_the_table`=規則の表の読み手の一覧(凍結)に最初の読み手 `economy/anchors.py` を足した。③ `tests/c8/test_sensitivity_ledger.py::test_read_graph_matches_the_source`=C8 の読み口のグラフ(src の文字列で W16 の出力名を探す)に `engine/economy_stage2.py` が当たった → 名の直書きをやめ `agents.population.POPULATION_FILE` を読む形に直した(グラフは元のまま)。④ `tests/engine/bridging/test_manifest_rules_bridges.py::test_values_match_the_ledger_and_the_table`=全体を回している間に私がつなぎの台帳の行(輪の係数)を書き換えた=ランの頭と試験の読みで sha が違った(作業の手順の誤り)。②〜④のファイルを回し直して 122 passed。
- `slow`: `tests/economy/cp2`(22 本)は 20 passed・2 failed → `cli.build_ledger_bundle` が腕 off でも引数を足して台帳を作っていた(HEAD の台帳の写しを差し込む 1-9 の試験の口が受けない)→ 腕 off は今の呼び方のままに直して 2 passed。`tests/economy/stage2` の `slow` 4 本も通った(再開の試験の最後の確かめを 300 体の抽出に雇用の行が無いことに合わせて直した)。
- 再開・診断・系の試験(`tests/engine/test_resume_10d.py`・`tests/c6/test_t9_diagnostics.py`・`tests/engine/systems`): 169 passed。
- `lint-imports`: 5 契約とも守られている。秘密の走査(変えたファイルと新しいファイル 42 本): CLEAN。

## 9. 触った共有ファイル(親の rebase 用)

- `src/shibuya/engine/systems/table.py`: world の `writes.paths` の末尾に `EM:ledger.*`・phase_c・day_close・close_final の末尾に `EC:ledger.* EM:ledger.*` と docstring の 1 段落。
- `src/shibuya/engine/state_ledger.py`: 行 `EC`・`ATM`・`CR`・`EM` を `J0` の後に・`EXCLUDED` に 1 行(`decision.money_stage2`=参照。`ledger.money._stage2_pairs`=設定の行は検収 L1 で読み取り専用の属性にして消した)・docstring の行の数(197)。版は上げない(4 行ともどちらのハッシュにも状態のファイルにも入らない=1-3・1-6・1-9・1-8 と同じ仮採用)。
- `src/shibuya/engine/manifest_sections.py`: `economy.stage2`(混ざった辞書=設定 8・観測 14)・`decision_port` の観測に `stage2`。
- `src/shibuya/engine/events/vocab.py`: 表の末尾に `金:引き出し`・`金:カード`(56 → 58 語)・`CAUSE_PROCESS_NAMES` の末尾に `payroll`・`atm`・`register`・版 `events-vocab/1-5` → `events-vocab/2-1`。
- `src/shibuya/cli.py`: 引数 2 つ(`--economy-stage2`・`--economy-stage2-parts`)と切替口の 2 行・`build_ledger_bundle` の雇用主の口の数と輪の係数(腕のランだけ)・`_HouseholdWalletLedger` の引数 2 つ(既定は今のまま)・import 3 行。
- `src/shibuya/engine/systems/build.py`(腕の組み立て 1 呼び・`runner` の後付け・`Fixtures.atms`・候補の口の引数・再開の見出しの突き合わせ 3 行=2-2 の近接の腕と同じ場所)・`boxes.py`(`Fixtures.atms`)・`report.py`(`money_stage2_in`)・`engine/run.py`(`RunResult.money_stage2_in`・`conserved` の式)・`engine/resolve.py`(`_payable`・`_stage2_note_calls`・`_stage2_withdraw`・`apply` の数行・commit の import 4 語)・`engine/processes/rail.py`(`pay_fares` の分岐)・`engine/decision/layer.py`(候補と計器と口の印)・`engine/decision/port.py`(`Choice.payment`・`PAYMENT_ANSWERS`)・`engine/rights/ledger.py`(`pairs`)。
- 〔検収の直し〕`src/shibuya/engine/commit.py`(`IntentBatch` の任意の 2 列・`S2_*`・`_concat_s2`)・`engine/systems/judge.py`(`_stage2_on`・`_with_stage2_calls`・`import dataclasses`)・`engine/systems/decide.py`(口の印を保留の組の末尾へ=2 行)・`engine/systems/state_io.py`(見出しの `economy_stage2`・`_stage2_plan`=2-2 の `proximity` と同じ場所)・`engine/systems/allow.py`(`TRANSFER_PORTS_HOUSEHOLD` に `withdraw_many`)・`engine/systems/table.py`(apply_responses の reads に `layers.ledger`)・`engine/events/links.py`(`MoneyEventLink` の行ごとの原因)。2-2 の作業木も `commit.py`・`judge.py`・`state_io.py`・`build.py`・`table.py`・`resolve.py` を触っている(親の rebase の順で衝突の箇所)。
- 規則の表の読み手の一覧(凍結): `tests/engine/rules/test_rules_table_schema.py`(読み手に `economy/anchors.py` を足した=発注の「規則の表の最初の読み手」)。
- 凍結の表(増えた分だけ): `tests/economy/cp2/money_writers_frozen.json`(`Ledger.__init__` の列に `_raw_method`=注「2-1・親の承認」=検収 A2)・`tests/economy/cp2/test_cp2_transfer_only_writer.py`(口の名の表に `withdraw_many`・呼び手に `_stage2_withdraw`=検収 A7・親の承認)・`tests/engine/decision/test_j0_port_schema.py`(`Choice` の欄に `payment`=検収 A1)・`tests/engine/test_env_and_sections_10f.py` の `CONFIG_PATHS_SHA256`(`economy.stage2` の設定の 8 道筋=外すと前の値 `89e426b3…dae50b9065` に戻ることを確かめた)。
- 数の試験(行・語の追加で必ず動く所だけ): `tests/engine/test_state_ledger_10b.py`(外の状態 102 → 106・全体 193 → 197・鍵の末尾 `EC`・`ATM`・`CR`・`EM`)・`tests/engine/events/test_e_vocab_is_closed.py`(56 → 58 語・版)・`tests/engine/rights/test_rights_events.py`(`V.VOCAB[-1] == 許可のない行動` → `V.VOCAB[55]`=1-5 の語のコード 55 は動かない)。
- つなぎの台帳 `docs/design/bridging-ledger.json`: 行を足した(286 → 304・`DOC-ec21-*` 18 行・§10)と、`DOC-money-uncaused-rows` の `status` を removed に・`why` の末尾に外した段と残り(検収 A1=親の指示)。active の行は 286 → 303。
- 規則の表 `docs/design/rules-table.json` は変えていない(最低賃金の 1,226 円の版は表に無い=読み手が直書きに戻す)。

## 10. expedient の一覧とつなぎの台帳に足した行

コードの印は「未リサーチ(expedient)」の注記(1-4 の走査の 6 形の外=1-9 の `ops.py` と同じ書き方)。台帳の行は文書で宣言(`declared_in`=本書)・`conf` expedient・`remove_basis` inferred・`code_at` つき。

| 行の id | 中身 | 外す段 |
|---|---|---|
| `DOC-ec21-payday-25` | 給料日=毎月 25 日(土休なら前の営業日)・出典なし | 4-2 |
| `DOC-ec21-atm-fixture` | ATM の表は組み立てで OSM から(`Fixtures.atms`・55 点) | 2-4(W6 の POI に ATM の行) |
| `DOC-ec21-atm-hours-and-cells` | 営業時間の無い ATM(単独・店の中)は 24 時間(55 点のうち 9 点)・祝日は曜日の規則・地上の層のセルを先に | 2-4 |
| `DOC-ec21-bank-branch-default-hours`(検収 L3) | 営業時間の無い銀行の支店(20 点)は平日 9:00-15:00・土日は閉・`atm` の印の無い支店も入れる | 2-4 |
| `DOC-ec21-withdraw-rule` | 引き出しの規則(財布 < 1 日の消費 × 1・額=min(預金, 1 日の消費 × 3) の千円単位)・副の判断の形・口が選んだ答えは印で運ぶ(J0 の 3 つの実装は選ばない=規則が代役) | 6-1 |
| `DOC-ec21-payment-rule` | 支払いの方法の規則(財布が足りれば現金・足りなければ口座)・運賃は IC 既定・口の答えがあれば先に従う(J0 の 3 つの実装は答えない) | 6-1 |
| `DOC-ec21-initial-deposit` | 初期の預金=1 日の消費 × 30 日・来街者=持ち込み(初期の財布)の 0.5 を預け入れ(合計は不変=検収 L2)・来街者でない体の財布は `initial_wallets` のまま | 4-1 |
| `DOC-ec21-wage-hours-and-rate` | 月の時間=W17 の勤務 × 52/12 週(W17 の無いランは 160 時間)・時給=最低賃金・〔検収 A3〕現実の 1/4 程度の見込み=月の時間の出どころは親が PENDING の判断待ちに | 4-1 |
| `DOC-ec21-employer-funding-exogenous` | 雇用主の原資=外界の売上(払う賃金と同じ額・外生=第 1 陣のまま) | 4-2 |
| `DOC-ec21-payroll-deduction-blank` | 給与の天引きは器だけ(0)・自営業の納税なし | 4-2 |
| `DOC-ec21-register-tax-rounding` | レジの税=税込 × 率/(1+率) の切り捨て(1 行ごと)・軽減税率なし | 4-2 |
| `DOC-ec21-external-store-sales-zero` | 店の外界の売上の額は 0・縮小ランの比を manifest に宣言(`plan.population_scale`=0.0128) | 7 |
| `DOC-ec21-account-two-rows` | 口座の決済を「預金純増の行+本体の行」の 2 行で書く | 2-4 |
| `DOC-ec21-consumption-pair-for-outside-sales` | 域外の取引先の支払いを科目「消費支出」に載せる(段階 2 の組) | 2-4 |
| `DOC-ec21-ring-coefficient` | 腕のランの生ログの輪の係数 16.0 行/体/日(2 日の和の最大 14.226 の 1.1 倍以上・1 日の最大 8.824 の 1.5 倍以上・係数は 2-4 で決める=検収 A4) | 2-4 |
| `DOC-ec21-revenue-tax-inclusive`(検収 A6) | 店の売上の写し `pois.revenue` は税込のまま(腕 on のときだけ帳簿の店の現金=税抜きと食い違う) | 2-4 |
| `DOC-ec21-uncaused-rows-arm-off`(検収 A1) | 原因の無い金の行の残り(腕 off の購入・食事・組み立ての行・呼の控えの無い体の購入と食事) | 2-4 |
| `DOC-ec21-call-memo-not-saved`(検収 A1) | 呼の控え(`last_call`・`pay_answer`)は状態のファイルに入れない=再開で空から | 6-1 |

- ほかの expedient(台帳の行は既存): 最低賃金の版の前の日は直書き 1,226 円(`BR-MIN-WAGE-HOURLY-1226`・外す段 4-2)。購入と食事の原因なし(`DOC-money-uncaused-rows`)は外した(removed・2-1・2026-10-14=検収 A1・残りは `DOC-ec21-uncaused-rows-arm-off`)。
- 印だけ(行なし): 口の名の書き方・`where` の決め方は 1-9 のまま。`ATM_UNIT_YEN`(千円)・`DEFAULT_MONTHLY_HOURS`(160)・`VISITOR_KINDS`(1・6・7)は上の行に含めた。

## 11. 限界・仮採用・親に確かめてほしい点

- **仮採用(10-13b §0-3)**: 既定(腕 off)の final・帳簿・台帳の行は動かない(§5)。戻すときは腕の物と試験を外すだけ(本体の既定の道には段階 2 の分岐が `stage2 is not None` の 1 行ずつしか無い)。
  1. 口座の決済の形(`ops.transfer` の `method`・決済の行を 1 行足す・世帯の現金は動かない)。日の締めの賃金(世帯の現金の書き込み窓の外)もこの形で書く。
  2. 引き出しを主の行為に添える副の判断にした(行為の語彙 12 語・`ACTION_CODES` を変えない)。
  3. 段階 2 の組(`STAGE2_PAIRS`)を腕の台帳だけで許す(科目は増やさない=流れの表の形 6 × 6 × 15 は不変)。
  4. 保存則の検算は腕によらず日次の記録の `economy.conservation` に置いた(記録の欄が増えるだけ・腕 off でも動く)。
  5. 雇用主の口は腕のランだけ W6 の組織の数(9,872)・腕 off は今の 1 口のまま。
  6. 状態台帳の 4 行は版を上げない(どれもハッシュと状態のファイルに入らない)。
  7. `RunResult.conserved` の式に `money_stage2_in` を足した(腕 off は 0)。
  8. 腕のランの生ログの輪の係数 16.0(実測 1 本・保持窓 1 日の輪が持つ 2 日の和の最大の 1.1 倍以上)。
- **親に確かめてほしい点**:
  1. 〔検収 A1 で入れた〕`DOC-money-uncaused-rows` の配線(購入と食事の呼の `call_id` を `IntentBatch` → resolve → `purchase_many`)は腕 on のランで入れた(§13)。
  2. 〔検収 A2=親の承認〕凍結の表 `money_writers_frozen.json` の `Ledger.__init__` に `_raw_method`(注「2-1・親の承認」)。
  3. **W17 の「勤務」の時間が短い**(〔検収 A3〕expedient のまま・月の時間の出どころは親が PENDING の判断待ちに=W17 の勤務ブロックか統計=毎月勤労統計の所定内労働時間): 雇用の行のある体(5,000 体のうち 2,421)の月の労働時間は平均 38.0・中央値 39.7・p90 52.0 時間(W17 の週の勤務の分 × 52/12)。賃金は 1 人 4.7 万円/月(最低賃金 1,226 円)。W17 の勤務の行が範囲の中の時間だけか・短時間の勤務が多いのかは調べていない(空欄)。賃金構造基本統計調査の所定内の時間(月 160 時間前後)との差は大きい。月の時間の出どころを W17 にするか、統計の値(EC2 の資産の段)にするかの判断。
  4. 腕 on では口座の購入・食事がまれ(2 日で 28 行): 財布(p10 約 8 千円・中央値 2 万円)が価格より大きい日がほとんど=規則「財布が足りれば現金」の結果。支払いの好みの属性が入る段(4-1)と判断モデルの段(6-1)で見直す。
  5. 〔検収 A4=係数は 2-4 で決める・数は記録に残す〕腕 on の 2 日では 0 日目の生ログが 8.824 行/体/日(初期の預金の 2 行・IC の運賃の 2 行・税の行)・1 日目 5.402。保持窓 1 日の輪は前の日と今日の行を持つ(2 日の和の最大 14.226 行/体)ので、6.5 の輪は 38,630 行・13.5 の輪も 3,630 行溢れた。腕のランだけ係数 16.0 にした(溢れ 0・§12)。39 万体の腕 on の輪は 224.7 MB(係数 6.5 の 91.3 MB の約 2.5 倍)。腕 off の輪(6.5)も 2 日の和の最大は 6.19 行/体で余裕が 5% しかない(0 日目に初期の財布と参入資本の行がある)。既定の係数を変えるか(版上げ 2 回目)の判断。
  6. 〔検収 A6=宣言して今のまま〕店の売上の写し `pois.revenue` は税込のまま(診断・`conserved` の式が読む・腕 on だけ)。帳簿の店の現金は税抜き(税を政府へ移した後)。つなぎの台帳 `DOC-ec21-revenue-tax-inclusive`(外す段 2-4)。
  7. 〔検収 A6=宣言して今のまま〕給料日の規則は暦の口 `SimCalendar.is_payday` を使い、ランの暦(`fx.calendar`)の `payday_day_of_month` は None のまま(manifest の `calendar.payday_day_of_month` は null)。段階 2 の組み立ての物 `Stage2Plan.payday_calendar` が 25 日の写しの暦を持つ(manifest の `economy.stage2.payday_day_of_month`=25)。
  8. 〔検収の直しで出た新しい問い〕`Choice.payment` を足したが口の形の版 `PORT_SCHEMA`(`port/1`)は上げていない(上げると腕 legacy の manifest の `decision_port.schema` も動く=既定のランの記録が変わる。1-8b の `utterance` と同じ扱い)。版を上げるかの判断。
  9. 〔同〕腕 port でも規則(財布 < 1 日の消費で下ろす・財布が足りれば現金)は口の答えの無い体の代役のまま残した(LLM の文は候補と注を見せないので、LLM の口でも答えは来ない)。LLM に候補を見せる段(6-1)で、口の答えの無い体に規則を当てるかを決める。
- **限界**:
  1. 〔検収 A1〕口の答え(お金を下ろす・支払いの方法)は行為の解決へ運ぶ。ただし J0 の 3 つの実装は答えない(LLM の文は今のまま=候補と注を見せない・mock と古典は語彙の候補だけ)=今のランで運ばれる口の答えは 0(§13 の数)。呼の控えは再開で空から(`DOC-ec21-call-memo-not-saved`)。
  2. 〔検収 A7=親の承認〕引き出しの口 `withdraw_many` を `TRANSFER_PORTS_HOUSEHOLD` に足した(`_stage2_withdraw` は「世帯の現金を書く関数」として AST で引かれる・凍結の `writes_soa_frozen.json` は変わらない)。
  3. 信用の器は呼び手なし(返済の流れは保存則の登録の外=呼ぶと検算が落ちる・試験で確かめた)。審査と総量規制は 4-2 の規則の表の後。
  4. 給与の天引き・自営業の納税・軽減税率・レジの端数は 4-2(規則の表の中身)。家計調査との比較(見張り)は検証専用=本段では出さない。
  5. EC2(最初の資産を統計から)は親が e-Stat の表を取ってから=本段は今の `initial_wallets` のまま。雇用の内生化は第 2 陣の後。
  6. 合成の世界には OSM の ATM の点が乗らない(セルの格子が違う)=合成の世界の試験は切替口で ATM を置く。世界資産のランは OSM の 55 点(42 セル・写せない点 0=検収 L3 の後)。
- **回していないもの**: manifest の 7 本の比べ(10f)・39 万体(容量は式だけ)。系ごとの指紋は検収の直しで回した(§13・検収 L5)。
- **用語集**: 新しい語は「口座(の方法)」「決済の行」「副の判断」「段階 2 の組」(用語集との照合はしていない)。

## 12. 最後の確かめ(検収の前の最後の src)

1. byte-check 19 構成([byte_check_ec21_off.json](byte_check_ec21_off.json)・腕 off・a=本体 HEAD `f2405e3` の写し): **final 19/19・36 欄 19/19 が同じ**。その後に `cli.build_ledger_bundle` を「腕 off は今の呼び方のまま」に直した src で 4 構成(w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel)を回し直し、**final 4/4・36 欄 4/4 が同じ**([byte_check_ec21_off_last4.json](byte_check_ec21_off_last4.json))。
2. 腕 on(全部)を輪の係数 16.0 で回し直した([two_day_ec21_on16.json](two_day_ec21_on16.json)): final `c64b7f6cc6a4e280`・144,954 呼(13.5 の版と同じ=輪は診断)・**輪 80,000 行・溢れ 0**・保存則 毎日 ok。
3. 試験: `tests/economy/stage2`(56 本・`slow` 4 本を含む)・`tests/test_cli.py`・`tests/engine/bridging` で 120 passed(3 分 33 秒)。`tests/engine/time`・`tests/engine/rules`・C8 の読み口・`tests/economy/cp2`(slow でないもの)で 206 passed。cp2 の `slow` の HEAD との同値 2 本 passed。`lint-imports` 5 契約とも守られている。
4. 生の出力(作業木の `_bc/`): `head.json`・`ec21_off_final.json`・`ec21_off_last.json`(byte-check の両側)・`two_day_ec21_final.json`・`two_day_ec21_on16.json`・`full_suite.log`。

## 13. 検収の直しと親の判断

検収([review.md](review.md))=条件つき受入(中 1・低 6)。親の指示(A1〜A9・M1・L1〜L6)で直した。commit・rebase はしていない(2-2 との順は親)。

| 項 | 直したこと(親の判断) | 場所 | 確かめ |
|---|---|---|---|
| 中 M1 | §0・§6 の文言を「減り方は緩んだが止まってはいない(off −1,625/−1,168 → on −839/−521 円/体/日・月の見込み(推測)=支出 約 3.55 万円/体に対し賃金 2.26 万円=現金+預金は月に約 1.29 万円/体 減る=月の時間が短い(A3)ため)」に。「財布 0 の体 0」は腕 off も同じと明記 | §0・§6 | 見込みの材料(1 日目の支出 1 体 1,182 円/日・賃金 22,568 円/月)を記録に |
| 低 L1 | 実行時の守り: `AtmTable` の配列は写しを読み取り専用・出どころは `MappingProxyType`/`STAGE2_PAIRS` を `MappingProxyType`/`Stage2Plan`(組み立ての後は `runner` を 1 回置く外は書けない)・`MoneyStage2`・`CreditBook`(行の数 `n` の外は書けない)に `__setattr__`・`__delattr__` の守り/`Ledger._stage2_pairs` は読み取り専用の属性(腕を挿したかから導く=状態台帳の除外の行 `ledger.money._stage2_pairs` は消した) | `engine/economy_stage2.py`・`economy/accounts.py`・`economy/stage2.py`・`economy/credit.py`・`economy/ledger.py` | `test_stage2_guards.py`(負の対照 4 本) |
| 低 L2 | 来街者の預金は持ち込みを**分ける**: 初期の財布(持ち込み)× 0.5 を世帯の現金 → 預金(預金純増 世帯 → 銀行・合計は不変)。登録の行を「来街者の持ち込みの口座の分(預け入れ)」(預金純増・INTERNAL)に | `economy/stage2.py` `endow`・`economy/accounts.py` | 試験(合計が持ち込みのまま)・動いた量は下 |
| 低 L3 | `amenity=bank` 23 を全部(`atm` の印に関わらず=窓口の引き出し)・営業時間の無い支店 20 は既定の平日 9:00-15:00・土日は閉(`BANK_DEFAULT_HOURS`・つなぎの台帳 `DOC-ec21-bank-branch-default-hours`)。「窓口だけの銀行」の文言は消した | `engine/economy_stage2.py` `build_atm_table` | 55 点(ATM 7・店の中 25・銀行の支店 23)・42 セル・写せない点 0(試験) |
| 低 L4 | 新しい関数の引数 `tick` → `step`(`withdraw_many`・`pay_fares_many`・`_stage2_withdraw`) | `economy/ledger.py`・`engine/resolve.py` | — |
| 低 L5 | 系ごとの指紋を 3 構成で比べた(1-3 の `probe_e13.py` の形=`tools/probe_ec21.py`・作業木の土台 `f2405e3` と本体の HEAD `42cd8f0` の 2 つ) | [probe_ec21.json](probe_ec21.json)・[probe_ec21_keys.json](probe_ec21_keys.json)・[probe_ec21_head42.json](probe_ec21_head42.json) | §13-2 の 3 |
| 低 L6 | `faucet_sink_table(stage2=False)` を既定に(許された組だけ=77 行) | `economy/accounts.py` | 試験 |
| A1 | 呼の id の配線: 判断の系が保留の組の `call_id`(12 番)を `IntentBatch.call_id` に付け(腕 on のランだけ)、`resolve.apply` が金に触れる行為(購入・食事・並ぶ=元の LLM の語・遠い店へ歩く移動に変えた行も)の呼を台帳に控え(`note_calls_many`)、`Ledger.purchase_many` が行ごとの原因 `LlmCall(call_id)` で書く(着いて実行する意図・列から席へ入った体も同じ呼)。引き出しは呼のある行の原因を `LlmCall`。腕 port の口の答え(お金を下ろす=`S2_WITHDRAW`・購入と食事の `Choice.payment`=`S2_PAY_*`)は保留の組の末尾 → `IntentBatch.s2_flags` → 台帳(規則を通さず下ろす・その方法で足りれば先に従う)。基本操作は行ごとの原因の `list` を受ける。`DOC-money-uncaused-rows` を removed(2-1・2026-10-14)・残りは `DOC-ec21-uncaused-rows-arm-off`・呼の控えは再開で空から(`DOC-ec21-call-memo-not-saved`) | `engine/commit.py`・`systems/judge.py`・`systems/decide.py`・`decision/layer.py`・`decision/port.py`・`resolve.py`・`economy/ops.py`・`economy/ledger.py`・`economy/stage2.py`・`events/links.py` | `test_stage2_calls.py`(8 本)・腕 legacy の既定は byte-check で不変 |
| A2 | 凍結の表 `money_writers_frozen.json` の注を「2-1・親の承認」に | `tests/economy/cp2/` | — |
| A3 | W17 の勤務の時間は expedient のまま。つなぎの台帳 `DOC-ec21-wage-hours-and-rate` の `why` に「現実の 1/4 程度の見込み=月の時間の出どころは親が PENDING の判断待ちに(W17 の勤務ブロックか統計=毎月勤労統計の所定内労働時間)」 | 台帳・§11 | — |
| A4 | 輪の係数は 2-4 で決める。数(8.824・5.402・14.226・溢れ 38,630/3,630/0)は記録に残す | §11・§12・`DOC-ec21-ring-coefficient` | 直しの後も溢れ 0(8.632・5.408 行/体/日) |
| A5 | 腕と部品を状態のファイルの見出し `economy_stage2` に書き(腕 on のランだけ)、再開で今の腕・部品と違えば止める(2-2 の M1 と同じ形・設定の指紋は不変) | `engine/economy_stage2.py` `header_fields`/`check_resume`・`systems/state_io.py`・`systems/build.py` | `test_stage2_resume_arm.py`(2 本) |
| A6 | 給料日の暦は今のまま宣言(§11 の 7)。`pois.revenue` は税込のまま宣言(腕 on だけ)+つなぎの台帳 `DOC-ec21-revenue-tax-inclusive`(外す段 2-4) | §11・台帳 | — |
| A7 | `withdraw_many` を `TRANSFER_PORTS_HOUSEHOLD` に足した(親の承認)。`_stage2_withdraw` が書き込みの許可の表(AST で引く呼び手)に入る・凍結の `writes_soa_frozen.json` は変わらない | `engine/systems/allow.py`・cp2 の試験 2 か所・`test_stage2_writers.py` | `tests/engine/systems`・`tests/economy/cp2` |
| A8 | `src_is_worktree` の検査は親が足す・EC2 は親 | — | 本書の byte-check は b 側の `run_meta.json` の `environment.code`(作業木の `f2405e3`・dirty)で作業木の src を確かめた |
| A9 | 300 体の抽出に雇用の行が無い理由: 10e の二層抽出は定員先取り層(乗務員・職務者 273 体・指令 10 体)を先に取り、統計層は居住者 17 体だけ。W16 の `org_id` を持つのは通勤者と従業者だけ(どちらも 0 体)・従業者が 0 なので店の担当従業者の行も 0。1,000 体で通勤者 129 体(雇用の行 129)・5,000 体で 2,421 | `test_stage2_resume.py` の docstring と同じ | 抽出を数えた(`agents.population.sample_population`・seed 1) |

親に確かめてほしい新しい点(§11 の 8・9 と同じ): `Choice.payment` を足したが `PORT_SCHEMA` は上げていない/腕 port でも口の答えの無い体には規則が代役のまま/段階 2 の中身のバイト予算 41 → 107 B/体(呼の控え)。

### 13-1. 動いた量(世界資産・5,000 体・2 日・腕 on 全部・腕 legacy)

| 版 | final | 引き出し(延べの機会・回・円) | 預金の不足 | 口座の購入・食事 | IC・現金の運賃 | 世帯の現金の 1 体の増減 | 最初の世帯の現金 |
|---|---|---|---|---|---|---|---|
| 検収の前([two_day_ec21_on16.json](two_day_ec21_on16.json)) | c64b7f6cc6a4e280 | 25,229・305・5,950,000 | 0 | 28 | 7,339・0 | −838.6・−520.8 | 139,548,230 |
| L2 だけ(ATM の表は前の作り方=[split_l2_l3.json](split_l2_l3.json)・`tools/split_l2_l3.py`) | 80e6fe737a6ffa40 | 25,229・472・7,243,000 | 201 | 30 | 7,290・49 | −687.1・−415.0 | 113,062,205 |
| L2+L3(直しの後=[two_day_ec21_fix.json](two_day_ec21_fix.json)) | 5a40399e189c7a1e | 23,079・463・7,043,000 | 204 | 29 | 7,290・49 | −735.9・−406.4 | 113,062,205 |

- **来街者(L2)**: 来街者 1,042 体の持ち込みのうち 26,486,025 円が財布 → 預金(前は外界から 36,991,000 円を預金に上乗せ=その faucet は無くなった・最初の世帯の現金は −26,486,025 円・0 日目の終わりの貨幣供給量は −36,991,000 円)。財布が半分になった来街者が下ろす=引き出し +167 回・+1,293,000 円・預金の足りない来街者の現金の運賃 49 行(IC −49)。呼数は同じ(144,954)・final は動く。
- **銀行の支店(L3)**: 点 43 → 55・セル 37 → 42。`atm=yes` の支店 7 は 24 時間 → 平日 9:00-15:00 になり、夜と土日に開いているセルが減った=判断した体が営業中のセルに居た延べ 25,229 → 23,079 回・引き出し 472 → 463 回(−200,000 円)。呼数は同じ・final は動く。
- **呼の id(A1・腕 legacy で挙動は不変)**: 購入と食事 16,212 行の全部が原因 `LlmCall(call_id)`(控えた呼 27,155 行=金に触れる行為の LLM の答え)・引き出し 463 回のうち 440 回が `LlmCall`・23 回が `Process("atm")`(呼の無い体)。原因の無い金の行(計器 `economy.transfers_uncaused`)は 33,577 → 16,295(残りは組み立ての行=初期の財布・参入資本・初期の預金と決済の行)・金の出来事の行 37,553 → 53,903。
- **腕 port(候補の口・mock の口)で運ばれる判断**: 呼の id で運ばれるのは腕 legacy と同じ(購入・食事 16,212 行・引き出し 440 回)。口の答え(お金を下ろす・支払いの方法)は 0(候補「お金を下ろす」を出した 25,166 回・購入と食事の文に注を添えた 289,908 回・mock は選ばず答えない)=final `5a40399e189c7a1e` と呼数は腕 legacy と同じ。口の答えが運ばれることは試験(mock の口の答えを試験の中だけ差し替え・合成の世界の 1 日)で確かめた。

### 13-2. 直しの後の確かめ

1. byte-check 4 構成(w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel・5,000 体・1 日・腕 off=既定)・a=本体 HEAD `42cd8f0` の src の写し・b=作業木の src(`PYTHONPATH=src`・b 側の `run_meta.json` の `environment.code` が作業木の `f2405e3`+dirty=作業木の src を読んだ): **final 4/4・全部の欄 4/4 が同じ**([byte_check_ec21_fix.json](byte_check_ec21_fix.json))。
2. 腕 on の 2 日 8 本([two_day_ec21_fix.json](two_day_ec21_fix.json)): §6 の表。保存則の残差 毎日 0・`conserved` 真・輪 80,000 行で溢れ 0。腕 off は前と同じ final `17f89bf0a109f2dd`・145,049 呼。
3. 系ごとの指紋(L5・`tools/probe_ec21.py`・全部の刻み・`PYTHONHASHSEED=0`・両側から状態台帳の行 E・EC・ATM・CR・EM・S8・S8M と日次の `economy.conservation`・`bridges_count`・`rules_version`・`events` と `RunResult.money_stage2_in` と ActualLog の目印の 3 欄を外した・腕 off):
   - **作業木の土台 `f2405e3` との比べ**([probe_ec21.json](probe_ec21.json)): final と呼数と並びの長さは 3/3 で同じ(5,945・14,159・16,271)。合成の世界 80 体は**全部の系・全部の刻みで同じ**。世界資産 300 体の 2 構成は並びの最後の 1 つ前の境目(close_final)だけが違う。どの欄かを `keys`(ランの終わりの境目だけの欄ごとの digest)で名指すと([probe_ec21_keys.json](probe_ec21_keys.json))、違うのは `A:ledger.money.meter`(計器の `last_day` に保存則の検算 `conservation` が入る=腕によらず日の締めに書く=§5 の「記録の欄が増えるだけ」・行 A は診断)だけで、ほかは壁時計の道筋(`O34:norm_meter.seconds`・`tick_ms_max`・`O73:runner.phase_seconds`・`O19:rel_layer.wall`=probe の `NONDET_PATHS`)と、作業木だけにある道筋 `J0:decision._s2_hints`(腕 legacy は持ち主が None=値は変わらない)。
   - **本体の HEAD `42cd8f0` との比べ**([probe_ec21_head42.json](probe_ec21_head42.json)): final と呼数と並びの長さは 3/3 で同じ。系の指紋は刻み 0 の perceive_prepare の `O63:renderer._tickc` から違う=HEAD に先に入った 1-8b(発話の口)の描画の物の違い(作業木の土台に無い)。2-1 の差だけを見るのは土台との比べ(上)。rebase の後に HEAD との比べを回し直す(親)。
   - 回した時点の src は J0 の行に `decision._s2_hints` を足す前(状態台帳の宣言だけの違い=値は変わらない)。
4. 試験: 親の指定の 8 か所(`tests/economy tests/engine/systems tests/engine/events tests/engine/rights tests/engine/decision tests/engine/rules tests/engine/time tests/engine/bridging`・`-m "not gpu and not slow"`)=**785 passed**。広げて `tests/engine`(全部)・`tests/test_cli.py`・`tests/c8`・`tests/c6` を回すと 2,274 passed・3 failed(状態台帳の持ち主の属性の網羅=`DecisionLayer._s2_hints` が台帳に無い)→ 行 J0 に足して、最後の src で 8 か所+`tests/engine/test_state_ledger_10b.py`+`tests/engine/memory/test_m0_store_schema.py` が **879 passed**。`tests/economy` の `slow`(段階 2 の 4 本=世界資産の 2 日・再開と cp2 の 22 本=HEAD との同値)は **26 passed**。`lint-imports` 5 契約とも守られている。秘密の走査(変えたファイルと新しいファイル 64 本): CLEAN。
5. 生の出力(作業木の `_bc/`=git の外): `bc_head42.json`・`bc_ec21fix.json`(byte-check の両側)・`two_day_ec21_fix.json`・`split_l2_l3.json`・`probe2_*.json`・`keys_*.json`(系ごとの指紋の両側)・`tests_fix*.log`。本体の HEAD の src の写しは `head42_src/`(`git archive 42cd8f0`+暦の CSV)・土台は `head_src/`。

### 13-3. 親の判断(2026-10-14・直しの受け取りの後)

1. `Choice.payment` を足しても口の形の版 `PORT_SCHEMA`(`port/1`)は上げない(1-8b の `utterance` と同じ扱い)。
2. 腕 port で口が答えを出さない体には古い規則(財布 < 1 日の消費で引き出し・財布が足りれば現金)が代役のまま=6-1(候補を LLM に見せる段)まで。つなぎの台帳の行 `DOC-ec21-withdraw-rule`・`DOC-ec21-payment-rule`(どちらも外す段 6-1)の `why` の末尾に「〔親の判断 2026-10-14〕腕 port で口が答えを出さない体には、この規則が代役のまま=6-1(候補を LLM に見せる段)まで。」を足した(行は足さない)。
3. 段階 2 の体あたりのバイト 41 → 107 B(呼の控え 66 B=呼の id への参照 8+文字列 57+支払いの答え 1)は予算の宣言に親が書く。記録の数は §7 のまま(5,000 体 535 KB・39 万体 41.7 MB=呼の id の文字列は全部の体が持つときの上限)。
4. 呼の控えは状態のファイルに保存しない=宣言 `DOC-ec21-call-memo-not-saved` のまま。再開は腕の見出しで止まる(A5)ので今は矛盾しない。

## 14. rebase(本体の HEAD `df9e2ed` の上へ)と再確認

作業木の土台 `f2405e3` の後に本体へ入った 1-7(道具の台帳 C0)・2-3b・2-0b・1-8b(発話の口)・2-2(近接)と文書の上へ載せ直した。commit・git add はしていない(`_bc/` は載せない)。手順は 1-7 と同じ: 変えたファイルとの新しいファイルを `_bc/rebase/` に控える → `git checkout -- <変えたファイル>` で土台に戻す → `git merge --ff-only df9e2ed`(早送り)→ 変えたファイルごとに 3 方向の `git merge-file`(土台 `f2405e3`・2-1・本体 `df9e2ed` の 3 つを LF にそろえて)→ 衝突を「本体の分 → 2-1 の分」の順で解く。新しいファイル(2-1 だけ)は本体に同じ道筋が無いことを確かめて元のまま。

| ファイル | 衝突 | 解き方 |
|---|---|---|
| `engine/decision/layer.py` | 2(引数・`__init__`) | 本体の `tools`(1-7)→ 2-1 の `money_stage2`・`_s2_hints` |
| `engine/systems/boxes.py` | 1(`Fixtures`) | 本体の `tools` → 2-1 の `atms` |
| `engine/systems/state_io.py` | 2(import・見出し) | 本体の `proximity`(2-2)→ 2-1 の `economy_stage2`(見出しに両方) |
| `engine/systems/build.py` | 3(再開の検査・候補の口の引数・`Fixtures`) | 再開の検査は本体の近接の腕 → 2-1 の経済の腕(両方)・`DecisionLayer(..., tools=…, money_stage2=…)`・`Fixtures(..., tools=…, atms=…)` |
| `engine/events/vocab.py` | 6 | 1-8b の 57 `行為:発話` の後ろに **58 `金:引き出し`・59 `金:カード`**(別の組)・`CAUSE_PROCESS_NAMES` は …+`PERCEPTION_PROCESSES`(1-7)+`ECONOMY_PROCESSES`(2-1)・版 `events-vocab/2-1`・`__all__` の末尾に 2 つ |
| `engine/manifest_sections.py` | 1 | `decision_port` の観測の末尾に `stage2` → 本体の `speech_port`(1-8b)・`proximity`(2-2)。`economy.stage2` は `decision_port` の前の既存の位置(衝突なし) |
| `engine/state_ledger.py` | 3(docstring・行・除外) | 行は … `J0`・`CT5`・`S8`・`S8M`・`PX`・`PX0` → **`EC`・`ATM`・`CR`・`EM`**(198 → 202・外の状態 107 → 111)・J0 の注の末尾(2-1 の `_s2_hints`)は残す・除外は本体の 1-8b・2-2 の行 → 2-1 の `decision.money_stage2`。2-1 は `OWNER_NAMES`・`SCRATCH_FIELDS` を触っていない |
| `tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/rights/test_rights_events.py` | 2・1 | 60 語・末尾 5 語・コード 56/57/58/59・版 2-1 |
| `tests/engine/test_env_and_sections_10f.py` | 1 | `CONFIG_PATHS_SHA256`: 本体の値 `1ec094a4…` は 2-1 の設定の道筋 8 つ(`economy.stage2.*`)で `f78dd574…` に変わる(**親の見込み「変わらない」と違う**: 2-1 の腕は引数ではないが manifest の `economy.stage2` の設定の子が道筋に入る=rebase の前も `89e426b3…` → `494d6d4c…` に変えていた)。8 つを外すと本体の値 `1ec094a4…` に戻ることを確かめた |
| `tests/engine/test_state_ledger_10b.py` | 2 | 外の状態 111・全体 202・鍵の末尾 `PX0` の後ろに `EC`・`ATM`・`CR`・`EM` |
| `docs/design/bridging-ledger.json` | (JSON で合わせた) | 本体の 310 行(active 303)はそのまま・2-1 の 18 行を末尾に・`DOC-money-uncaused-rows` を removed に(本体でも変わっていないことを確かめた)=328 行・active 320 |
| `cli.py` | 0(自動) | 2-1 の引数と切替口を 2-2 の `--proximity`・`--proximity-d` の後ろへ移した(本体の分 → 2-1 の分) |

衝突の無かった共有のファイル(3 方向で自動に合わさった=中身を見た): `engine/commit.py`・`systems/judge.py`・`systems/decide.py`・`systems/table.py`・`systems/allow.py`・`systems/report.py`・`engine/resolve.py`・`engine/run.py`・`decision/port.py`・`events/links.py`・`processes/rail.py`・`rights/ledger.py`・`economy/*`・cp2 の試験 2 本・`test_j0_port_schema.py`・`test_rules_table_schema.py`。

rebase の後に直した試験(本体の末尾の並びの試験が 2-1 の語と原因の名で動く=コードは動かない): `tests/engine/tools/test_c0_tool_registry.py`(原因の名の末尾=`perception` → 位置で確かめ、末尾 3 つは `ECONOMY_PROCESSES`)・`tests/engine/speech/test_speech_port_schema.py`(`行為:発話` は末尾でなくなった=コード 57・末尾 2 語は金・版 2-1)。

### 14-1. rebase の後の再確認(作業木の src=`df9e2ed`+2-1・`PYTHONPATH=src`)

1. 試験(親の指定の範囲=`tests/economy tests/engine/proximity tests/engine/speech tests/engine/tools tests/engine/systems tests/engine/events tests/engine/rights tests/engine/decision tests/engine/rules tests/engine/time tests/engine/bridging tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py tests/perception tests/llm tests/test_cli.py`・`-m "not gpu and not slow"`): 1 回目 1,935 passed・3 failed(`CONFIG_PATHS_SHA256` と 1-7・1-8b の末尾の試験 2 本=上の表)→ 直して **1,938 passed**。`tests/economy` の `slow`(段階 2 の世界資産の 2 日・腕 on の再開 2 本=日の境目と 1 日目の昼・cp2 の HEAD との同値 22 本)**26 passed**。腕の見出しの再開(`test_stage2_resume_arm.py`)は範囲の中で passed。`lint-imports` 5 契約とも守られている。秘密の走査(変えたファイルと新しいファイル 70 本): CLEAN。
2. byte-check 4 構成(w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel・5,000 体・1 日・腕 off=既定)・a=本体 HEAD `df9e2ed` の src の写し(`git archive`・錨はエンジンが開く 3 本だけ+暦の CSV)・b=作業木の src(子プロセスに `PYTHONPATH=src`・b 側の `run_meta.json` の `environment.code` が `df9e2ed`+dirty=作業木の src を読んだ): **final 4/4・36 欄(10e の 25 欄+帳簿の 11 欄)4/4 が同じ**([byte_check_ec21_rebased.json](byte_check_ec21_rebased.json))。
3. 系ごとの指紋(L5 の再実行・本体 `df9e2ed` と 3 構成・`PROBE_EC21_SKIP_S8` なし=1-8b の S8・S8M も比べる・[probe_ec21_rebased.json](probe_ec21_rebased.json)): final・呼数・並びの長さ 3/3 で同じ。合成の世界 80 体は**全部の系・全部の刻みで同じ**。世界資産 300 体の 2 構成は close_final だけが違い、欄を名指すと([probe_ec21_keys_rebased.json](probe_ec21_keys_rebased.json))`A:ledger.money.meter`(計器の `last_day` の保存則の検算=腕によらず日の締めに書く・診断)だけ・ほかは壁時計の道筋と作業木だけの道筋 `J0:decision._s2_hints`(腕 legacy は持ち主が None)。rebase の前の土台 `f2405e3` との比べ(§13-2 の 3)と同じ形。
4. 腕 on の 2 日 8 本([two_day_ec21_rebased.json](two_day_ec21_rebased.json)): rebase の前の 8 本([two_day_ec21_fix.json](two_day_ec21_fix.json))と**壁時計の欄の外は全部の欄が同じ**(final・呼数・賃金・引き出し・支払い・税・来街者の口座・呼の配線の計器・分位・日ごとの保存則の検算)。腕 on(全部)は `5a40399e189c7a1e`・144,954 呼・保存則の残差 毎日 0・輪 80,000 行で溢れ 0・腕 off は `17f89bf0a109f2dd`・145,049 呼。
5. つなぎの台帳: 328 行・active 320(本体 303+2-1 の 18−removed 1)。`tests/engine/bridging` の数(expedients・docstring・heading など)は 2-1 で変わらない(2-1 の行は文書の宣言=`declared_in` が本書)。
6. 生の出力(`_bc/`=git の外): `rebase/`(控え・3 方向の写し・解き方の道具 `merge3.py`・`resolve.py`・`merge_ledger.py`・`cli_order.py`・`fix_tail_tests.py`)・`headdf_src/`・`bc_headdf.json`・`bc_ec21rb.json`・`probe_headdf.json`・`probe_ec21rb.json`・`keys_headdf.json`・`keys_ec21rb.json`・`two_day_ec21_rebased.json`・`tests_rebased*.log`・`tests_slow_rebased.log`。
