# 賃金を職業ごとの実データから(小さな版上げ・2026-10-17)の記録

正: ユーザー決定 2026-10-17([回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §7 の 3・§0-6・§0-7)・決定 10-12 §4-11(EC2)・答申 R-107 §1-1・記録 [pop41b](../pop41b/README.md) §4・記録 [ec21](../ec21/README.md) §6・§11。

## 0. 結論

- 2-1 の月の賃金(雇用の行のある体)を「W17 の勤務時間 × 最低賃金」から「職業 × 性 × 年齢 × 雇用形態の実データ(賃金構造基本統計調査 令和 7 年=R-107)」に置き換えた。式は 4-1 段 5 の `attr_fns.wage_monthly` と同じ物で、二重に作らず実行時の `economy/wages.py` に移した。build の側はそこを呼ぶ。W21b の資産の `w21b_build_hash` は変わらない(golden の試験が通る)。
- 切替口 `--wage {occupation,w17}`(環境変数 `SHIBUYA_WAGE`)を足した。既定は `occupation`。`w17` は旧値の再現のためだけの道で、次の版上げで消す(§0-6)。
- 5,000 体・2 日(給料日 2026-08-25)で、雇用の行のある 2,421 体の月の賃金の中央値は 48,699 円から 274,243 円になった(平均は 4.66 万円から 31.1 万円)。職種 × 性の中央値は R-107 第18表の中位数の 0.83〜1.04 倍。「賃金が現実の 1/4」の宣言(`DOC-ec21-wage-hours-and-rate`)は閉じた。
- 〔検収の直し・§13〕最低賃金法の床を入れた(規則の表 `minimum_wage.tokyo`=machine の行・給料日に効いている版・版の無い日は床なし)。〔13-7〕親の一次確認で規則の表に前の 2 版(1,226 円=2025-10-03〜・1,163 円=2024-10-01〜)を足したので、世界の時点の給料日(2026-08-25)にも 1,226 円の床が効く: 5,000 体の雇用の行のある 2,421 体のうち 463 体(19.1%)が床に当たり、上げた額は 16,915,883 円。
- byte-check 19 構成は、既定 occupation も w17 も HEAD `32fb262` と 25 欄すべて同じ(19/19)。1 日のランは給料日を含まないので、既定でも動かない。給料日をまたぐ 2 日のランで動くのは賃金の 3 欄(賃金・原資・預金純増)だけで、ほかの科目は同じ。保存則の残差は毎日 0。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/core/wage_formula.py`(新・〔検収の後〕) | `economy/wages.py` の純粋な式と表を移した(numpy と `core.rng` だけを読む)。build が economy の包みを読むと engine と llm まで読まれ、4-1 段 8〜9 の `test_persona_build_does_not_import_or_call_llm` が落ちたため。`economy/wages.py` は同じ物を名前で見せる(二重に作らない)。`month_hours`・`apply_floor` もここ |
| `src/shibuya/economy/wages.py`(新) | 賃金の表の読み解き `parse_wage_tables`(`w21_money.load_wage_tables` から移した)・分位と額の式 `wage_quantile`・`wage_values`(`attr_fns._wage_quantile`・`_wage` から移した)・実行時の読み口 `load_wage_tables`(構築側の写し 4 本を md5 と元の md5 で照らす)・分位の乱数 `wage_uniform`(用途名 `economy.wage`)・W16 の写像の表・`occupation_wages`(写せない体の平均・与えた値)・計器 `median_check`・注記の型 `WageTablesAbsentWarning` |
| `src/shibuya/build/pop/attr_fns.py` | `WAGE_OCCUPATIONS`・`WAGE_AGE_EDGES`・`_wage_quantile` は `economy.wages` の同じ物を指す。`_wage` は語を番号にして u を引き、`wage_values` を呼ぶだけ |
| `src/shibuya/build/pop/w21_money.py` | `load_wage_tables` は写しを読み口で読み、`parse_wage_tables` を呼ぶだけ。`WAGE_CLASS_FLOOR_YEN`・`WAGE_TOP_FACTOR` は移した値を指す |
| `src/shibuya/economy/stage2.py` | `MoneyStage2` に賃金の腕・体ごとの月の賃金・出どころ・点検の記録を足した。給料日は腕 occupation なら月の賃金をそのまま払う。表の写しが無い写しは注記して 2-1 の道に戻す。計器 `rules.wage_model`(給料日)と `rules.wage_build`(組み立て)・manifest の `plan.wage_path`・体あたりの足し分 `WAGE_BYTES_PER_AGENT`(24 B → 〔検収 M1〕32 B) |
| `src/shibuya/economy/anchors.py` | `monthly_wages` に `amounts=`(行ごとの額を渡す口)を足した。既定 `None` は今までどおり |
| `src/shibuya/engine/economy_stage2.py` | 切替口(`WAGE_ARMS`・`set_wage_arm`)・`WageInputs`・ペルソナの在庫の読み口 `persona_words`・`wage_inputs`・`Stage2Plan` の `wage_model`/`wage_inputs`・見出しの `wage` と再開の検査。腕 occupation では W17 の週次表を読まない |
| `src/shibuya/cli.py` | `--wage` の 1 つ(引数・設定・ランの種類の判定に 1 行) |
| `src/shibuya/engine/state_ledger.py` | 〔検収 L5〕行 EC の dtype の文(配列の本数)だけ |
| `src/shibuya/engine/run.py`・`src/shibuya/engine/rng_audit.py` | 用途名 `economy.wage` を母集団の側の表と静的に安全な呼び手の表に 1 行ずつ(§9) |
| `docs/design/bridging-ledger.json` | 3 行を足し、1 行を閉じた(§8) |
| `tests/economy/test_wage_occupation.py`(新)・`tests/economy/stage2/test_wage_occupation_runs.py`(新) | §10 |

## 2. 置き換えの中身と写像

- 体ごとの月の賃金=第18表の職種 × 性の所定内給与額の階級の度数の分位 u の値 × 年齢の比(第6表)× 雇用形態の比(第9表)。短時間の体は第2表の時給 × 形 × 1 日の時間 × 日数。式・宣言(`EX-build.pop.w21_build_b-dc566aac`・`-18118af0`)は 4-1 段 5 と同じ。
- u は体ごとに `philox_array(母集団の seed, "economy.wage", k19(W16 の agent_id))` の 1 語。抽出の大きさに依らず、同じ W16 の体は同じ額になる。母集団の seed は `schedule.master_seed`。
- W16 の体はペルソナの在庫(`data/persona_pool_v2` の L1・L2・L3・L5)から `occupation_major` と `employment` の語を読む。L4(来街者・730 MB)は読まない。

写像の表(**未リサーチ(expedient)**・`DOC-wage_occ-persona-map`):

| ペルソナの語 | 写し先 |
|---|---|
| `occupation_major` の 11 語(管理的職業従事者 … 運搬・清掃・包装等従事者) | 同じ名の職種(賃金構造の職種の名と同じ語) |
| `occupation_major` の「非就業」「通学」・空 | 写せない=雇用形態と年齢(と性)だけの平均(`DOC-wage_occ-unmapped-average`) |
| `employment` 正規 | 一般の正社員・正職員 |
| `employment` 非正規 | 一般の正社員・正職員以外(W16 の語に短時間の印は無い) |
| `employment` 役員・自営業主・家族従業者 | 賃金構造の対象外なので正社員・正職員の表 |
| `employment` 非就業・空 | 正社員・正職員の表(雇用の行がある体だけが払われる) |

- 写せない体の平均: 職種ごとの値(同じ u・雇用形態・年齢)を第18表の職種 × 性の労働者数で重みづけした平均。性が分からなければ男女も平均し、年齢が分からなければ年齢の比を 1 にする。
- W21 への差し替え(段 10=4-3): 母集団が `wage_monthly` の列を持てば、その値をそのまま使う(`WageInputs.given`)。

写せなかった体(5,000 体・雇用の行のある 2,421 体): 16 体(非就業 12・通学 4)。39 万体の母集団では 222,849 体のうち 1,379 体(非就業 1,001・通学 378)。雇用の語の内訳(2,421 体): 正規 1,292・非正規 871・役員 237・非就業 16・自営業主 5。

## 3. 月の賃金の分布の前後と R-107 の中位数(構築側=点検だけ)

5,000 体・seed 1・既定 v3・2 日(2026-08-24 → 25)・給料日 2026-08-25 に払った額(円/月):

| | 体 | 平均 | p10 | p25 | p50 | p75 | p90 | 合計 |
|---|---|---|---|---|---|---|---|---|
| 前(`--wage w17`=W17 の勤務 × 1,226 円) | 2,392(時間 0 の 29 体は 0) | 46,608 | 21,251 | 37,012 | 48,699 | 58,262 | 63,752 | 112,838,004 |
| 後(既定 occupation) | 2,421 | 311,362 | 165,632 | 209,358 | 274,243 | 369,122 | 509,906 | 753,808,200 |

職種 × 性の中央値(雇用の行のある体・写せた体・一般の雇用形態・30 体以上の欄)と第18表の中位数(一般労働者):

| 職種 | 性 | 体 | 中央値 | R-107 中位数 | 比 |
|---|---|---|---|---|---|
| 専門的・技術的職業従事者 | 男 | 350 | 355,691 | 364,200 | 0.977 |
| 専門的・技術的職業従事者 | 女 | 249 | 265,490 | 297,000 | 0.894 |
| 事務従事者 | 男 | 608 | 298,520 | 358,200 | 0.833 |
| 事務従事者 | 女 | 415 | 245,097 | 264,700 | 0.926 |
| 販売従事者 | 男 | 245 | 286,664 | 337,500 | 0.849 |
| 販売従事者 | 女 | 148 | 239,636 | 248,400 | 0.965 |
| サービス職業従事者 | 男 | 160 | 242,470 | 269,500 | 0.900 |
| サービス職業従事者 | 女 | 111 | 224,199 | 235,700 | 0.951 |
| 建設・採掘従事者 | 男 | 31 | 278,923 | 310,700 | 0.898 |

39 万体の母集団の雇用の行に当たる 222,849 体では、20 欄の比は 0.836〜1.037(〔検収 L7〕数え方=雇用の行に当たる体(`org_id ≥ 0` か種別 従業者)・写せた体・一般の雇用形態・30 体以上の欄=20 欄。前の版の「22 欄」は 30 体未満の欄も数えた誤り)(管理的 男 0.995・事務 男 0.836・運搬 女 1.037)。比が 1 を下回る主な理由は、W16 のペルソナの非正規の割合(871 / 2,163=40%)が高く、雇用形態の比で下がること(推測)。第18表の中位数は一般労働者の正社員と正社員以外を合わせた値。

## 4. 収支(紙上の閉じ方)

給料日の締めに、雇用主ごとに次の 2 行が同じ額で立つ(第 1 陣の「外生」のまま=`DOC-ec21-employer-funding-exogenous`)。

1. 外界 → 雇用主(科目 消費支出・faucet=登録済み): 払う賃金の和。
2. 雇用主 → 世帯の口座(科目 賃金・口座の方法)=帳簿の上では世帯 → 銀行の預金純増の行が同じ額で立つ(預金=銀行の負債)。

雇用主の手元は 0 のまま、世帯の預金と銀行の負債が同じ額だけ増える。faucet の額は払う賃金と同じなので、残差の科目は 0 のまま閉じる。新しい科目・部門・登録の行は無い(額が増えるだけ)。2 日のランの検算は両腕とも毎日 `ok`・残差 0・`RunResult.conserved`。

2 日のランの科目ごとの流れ(円・0 日目/1 日目)で両腕が違うのは次の 3 欄だけ。ほかの 7 欄(参入資本・域外仕入・持ち出し・来街者持込・消費支出 世帯 → 店舗・税・預金純増 銀行 → 世帯)は同じ。

| 欄 | occupation | w17 |
|---|---|---|
| 消費支出 外界 → 雇用主(原資) | 0 / 753,808,200 | 0 / 112,838,004 |
| 賃金 雇用主 → 世帯 | 0 / 753,808,200 | 0 / 112,838,004 |
| 預金純増 世帯 → 銀行 | 763,196,025 / 753,808,200 | 763,196,025 / 112,838,004 |

月の見込み(推測・1 日目の値 × 30.44 日・5,000 体の平均): 支出(消費支出 5,253,800 円+運賃 667,620 円)は 1 体 約 3.60 万円/月。賃金は 1 体あたり occupation 15.08 万円/月(w17 は 2.26 万円/月)。現金+預金は w17 では月に約 1.3 万円/体 減っていたが、occupation では月に約 11.5 万円/体 増える。来街者を含む 5,000 体の平均で、支出の側は家計の全部を表していない(家賃・光熱などの支出は範囲の外=空欄)。

## 5. 19 構成の差の表と旧値の再現

HEAD `32fb262` の写し(`git archive`+data へのつなぎ=回し終えてつなぎを外した)と作業木を `byte_check_10e.py side` で比べた(5,000 体・seed 1・1 シミュ日・mock/classical)。`--kw` は空。賃金の腕は環境変数で渡した(`SHIBUYA_WAGE` は道具の `SWITCH_ENV` に無い=side の JSON の `env` には残らない)。

| 比べ | 構成 | final が同じ | 25 欄が全部同じ |
|---|---|---|---|
| HEAD vs 作業木 既定(occupation) | 19 | 19 | 19 |
| HEAD vs 作業木 `SHIBUYA_WAGE=w17`(旧値の再現) | 19 | 19 | 19 |

既定でも 19 構成が動かない理由: 1 日のラン(開始 2026-07-13)は給料日(7 月は 24 日の金曜日)を含まない。段階 2 の中身(状態台帳の行 EC)は `hash_skip` で、組み立てで足した配列はハッシュに入らない。給料日をまたぐ 2 日のランの差は §4 のとおり、賃金の 3 欄だけが動く。2 日のランでは final が両腕で同じ(`21e62930e8e51822`)だった。〔検収 L1〕理由は `hash_skip` ではない: 2 日のランの給料日の支払いは最後の日の締め(`close_final`)で、最後の checkpoint(刻み 2879)の後に起きる。給料日が途中の日の締めに来る 3 日のラン(検収役の 1,000 体)では、帳簿の残高(行 O57=軸 1 behavior)が final に入り、両腕で final が違う(`43d1db79…` と `34ec1f8b…`)=版上げの差として期待どおり。〔検収 L2〕19 構成(1 日)は給料日を通らないので、旧値の再現の根拠にならない。旧値の再現の根拠は給料日を含む 2 日のランの HEAD と w17 の比べ(§13)。19 構成の side は、manifest の点検の欄を plan から rules へ移す前の src で回した(移したのは manifest の中の辞書の置き場だけ=状態とハッシュには入らない)。

## 6. 性能の記録(§0-7)

条件: 手元の Windows 機(20 論理コア・RAM 31 GB)。ほかの作業木のランが同時に動いていた=壁時計は決定論でない。

| ラン | 体 | 日 | seed | 壁時計 | 1 刻み | 最大の作業集合 | 判断と LLM の呼び出し |
|---|---|---|---|---|---|---|---|
| w6_v3_default HEAD(2 回) | 5,000 | 1 | 1 | 43.7・47.5 s | 0.030・0.033 s | 489・479 MiB | 64,528(mock) |
| w6_v3_default 既定 occupation(2 回) | 5,000 | 1 | 1 | 45.9・46.2 s | 0.032・0.032 s | 474・473 MiB | 64,528 |
| w6_v3_default w17(2 回) | 5,000 | 1 | 1 | 52.9・52.9 s | 0.037・0.037 s | 478・480 MiB | 64,528 |
| 2 日 既定 occupation | 5,000 | 2 | 1 | 208.8 s | 0.072 s | 476 MiB(499,077,120 B) | 143,744 |
| 2 日 w17 | 5,000 | 2 | 1 | 210.7 s | 0.073 s | 492 MiB(515,919,872 B) | 143,744 |

- HEAD・occupation・w17 の順に 2 回ずつ続けて回した。w17 の道は HEAD と同じ処理だが毎回遅く出た。差は同時に動いていたほかのランの負荷による見込み(推測)。既定 occupation の組み立ての足し分は下の 0.46 秒。前の版より悪くなった量は無い。
- 組み立ての足し分: 5,000 体の `wage_inputs`(ペルソナの在庫の 4,135 行)0.46 秒・表の読み 0.003 秒・額 0.006 秒。39 万体の全部では 6.8 秒(205,919 行)と 4.8 秒(負荷のある機で 1 回)。
- バイト: 腕 occupation のランの体あたり +24 B(月の賃金 8・出どころ 1・入力 5 列 15)=39 万体で約 9.4 MB。〔検収 M1〕月の時間の目安 8 B を足して +32 B=約 12.5 MB。日をまたいで伸びない。予算の宣言の文書(2-1 の行=107 B)の更新は親(§11 の 2)。
- 〔検収 L8〕性能の数はどれもほかのランの負荷の下で測った=決定論でない(検収役の 2 日 5,000 体は HEAD 87 秒・w17 95 秒・occupation 189 秒・3 日 1,000 体は順が逆)。退化の判断はできない=親が空いた機械で測り直す。
- 19 構成の side の壁時計の和: HEAD 1,162.7 s・occupation 1,396.1 s・w17 1,361.8 s。作業木の 2 つの side は同時に回したので、和は比べられない(参考)。

## 7. 計器(manifest と日次の記録)

- `economy.stage2.plan.wage_model`・`wage_path`(設定の節の中=腕と道=`occupation`・`tables_absent`)。`hours_source` は `none(wage=occupation)`。
- `economy.stage2.rules.wage_build`(観測=組み立てで決まるが、母集団の抽出=seed で動く): 道・出どころの表と md5・体の数・出どころの内訳(`occupation`・`average`・`given`)・値の無い体・月の賃金の分位・職種 × 性の中央値と R-107 の中位数の比(30 体以上の欄)・入力の記録 `inputs`(語の出どころ・読んだ行・語の種類・性と年齢の分からない体の数・読んだ層)。はじめは設定の節(plan の中)に置いたが、seed の入れ替えの試験(10f の `test_seed_exchangeability_*`)で設定の葉が seed で動いたので観測に移した。
- `economy.stage2.rules.wage_model`(観測=給料日): 雇用の行のある体の数・払った体の出どころの内訳・値の無い体・払った額の分位と平均。
- 腕 w17 のランの manifest は今のまま(足した欄は立たない)。
- 〔検収 L6〕**版上げの差**(既定の腕 occupation のランで manifest の既存の欄の値が変わる・欄が足される): `economy.stage2.plan.hourly_source`(「最低賃金(規則の表・asof)」→「使わない(月の賃金=職業 × 性 × 年齢 × 雇用形態の実データ)」)・`economy.stage2.hours_source` と `plan.hours_source`(`w17_work` → `none(wage=occupation)`)・足した欄 `plan.wage_model`・`plan.wage_path`・`rules.wage_build`・`rules.wage_model`。byte-check の 25 欄には入らない。新しい manifest の道筋は無い(`CONFIG_PATHS_SHA256` は不変)。

## 8. つなぎの台帳

| id | 状態 | 中身 | 外す段 |
|---|---|---|---|
| `DOC-wage_occ-separate-from-w17-hours` | 足した | 2-1 の月の賃金は W17 の勤務時間と別に入れた(体が舞台で働く時間と払われる賃金が対応しない) | 3-1(inferred) |
| `DOC-wage_occ-persona-map` | 足した | W16 の体の写像(§2 の表) | 4-3(plan) |
| `DOC-wage_occ-unmapped-average` | 足した | 写せない体=雇用形態と年齢(と性)だけの平均 | 4-3(plan) |
| `DOC-wage_occ-legacy-switch` | 足した(〔検収 L4〕) | 切替口 `--wage w17` と、賃金の表の写しが無い写しの戻り道(月 160 時間 × 最低賃金)=次の版上げで消す | 4-3(inferred) |
| `EX-build.pop.w21_build_b-dc566aac`・`-18118af0` | 注と `code_at` を足した(〔検収 M2〕・status と外す段 7 は不変) | 構築側の近似が実行時の既定の賃金(`economy/wages.py`)にも入った・dc566aac には最低賃金を下回る 19.3% の内訳(約 11 ポイントは独立の仮定から・全国の表そのものは約 9%) | 7 |
| `DOC-ec21-wage-hours-and-rate` | 閉じた(`removed`) | 「月の賃金=W17 の勤務 × 最低賃金・現実の 1/4 程度」。根拠=§3 の中央値の比 | — |

rebase の後(本体 13e9c90 の台帳 483 行・active 472)に足し直した: 487 行・active 475。

## 9. 触った共有ファイル

- `docs/design/bridging-ledger.json`: 末尾に 3 行・`DOC-ec21-wage-hours-and-rate` の `status` と `why`。
- `src/shibuya/cli.py`: `--wage` の引数・`set_wage_arm` の呼び・ランの種類の判定の 1 行。
- `src/shibuya/engine/run.py`: `POPULATION_RNG_DOMAINS` に `economy.wage` の 1 行。
- `src/shibuya/engine/state_ledger.py`: 行 EC の dtype の文(〔検収 L5〕・軸と道筋は不変)。
- `src/shibuya/engine/rng_audit.py`: `SAFE_SITES` に `("core/wage_formula.py", "wage_uniform", "economy.wage")`(〔検収の後〕置き場を core へ移した) の 1 行と注の数(16 → 17 か所)。
  - この 2 つは発注の「編集してよい」の一覧の外。用途名を表に載せないと、試験 `test_every_rng_domain_in_src_is_classified` と `check_sites` が落ちる(6-5 の `memory.forgetting_rate` と同じ形)。
- 既存の試験 3 本の期待値: `tests/economy/stage2/test_stage2_default_2_4.py`・`test_stage2_resume_arm.py`(見出しの `wage`)・`tests/engine/test_state_checks_10f.py`(`SAFE_SITES` の数 17)。
- 触っていない: 状態台帳・凍結の表・manifest の表(`manifest_sections`)・`CONFIG_PATHS_SHA256`・段 1〜7 の資産。

## 10. 試験

- `tests/economy/test_wage_occupation.py`(14 件): 共有(同じ物・`attr_fns` の 3 関数と実行時の式が同じ鍵で同じ値・u は `AttrKey.uniform` と同じ・実データの写しの読み解きが構築の読み口と同じ=data・md5 が違えば止める)・純粋(`open` 0 回・同じ値・入力不変)・W17 を読まない(AST+負の対照)・写像と平均と与えた値・ペルソナの読み口(空の行・同じ行・L4 を読まない)・入力の組み立て(母集団なし・在庫なしの注記)・給料日(額・原資・残差 0・計器・バイト)・w17 の額は今のまま・表の写しが無い写しの注記・切替口と見出しと再開の検査・CLI。
- `tests/economy/stage2/test_wage_occupation_runs.py`(slow・data): 5,000 体 2 日の両腕(残差 0・0 日目は同じ・1 日目は賃金の 3 欄だけ・occupation の賃金は w17 の 4 倍を超える)・中央値の比 0.75〜1.15・1,000 体の再開=通し(両腕・腕を変えた再開は止まる)。
- 範囲の試験の件数は §12。`tests/c7` は回していない。

## 11. 限界・仮採用・親に確かめてほしいこと

1. **最低賃金を下回る体**〔検収 M1・親の判断=床を今入れた=§13〕: 5,000 体の写せた 2,405 体のうち 459 体(19%)は時間あたりの額(月 ÷ 第9表の所定内時間)が東京都の最低賃金 1,226 円を下回る(1,280 円なら 539 体)。理由は全国の表だからだけではない: 全国の分布そのもの(第18表の 11 職種 × 男女)では約 9%(分位の値だけなら 7.8%)で、残りの約 11 ポイントは、年齢と雇用形態をすでに混ぜた第18表の分布に第6表と第9表の比をさらにかける形(独立の仮定=`EX-build.pop.w21_build_b-dc566aac`)で下の裾が広がった分(検収役の再計算)。比のかけ合わせはそのまま(expedient)。東京都の表(`data/calib/wage/`)は較正側の置き場なので使っていない。
2. **予算の宣言の文書**(`docs/design/v2-budget-declaration.md` の 2-1 の行=107 B): 腕 occupation の +32 B の書き足しは親(本書は docs/design を触らない)。
3. **byte-check の道具**: `HEAD_TREE_FILES` に、エンジンが新しく開く `data/persona_pool_v2` と `data/research_cache/pop41b/derived/wage_t*.json` は無い(data はつなぎでそろう=今回の比べは影響なし)。`SWITCH_ENV` に `SHIBUYA_WAGE` は無い。
4. **2 日のランの final**〔検収 L1 で閉じた〕: 給料日の支払いが最後の checkpoint の後だから(§5)。
5. 仮採用(expedient): 写像の表(§2)・役員と自営業主を正社員の表で払う・非正規は正社員以外の表(短時間の表を使う W16 の体は無い)・写せない体の平均の重み(第18表の労働者数)・L4 を読まない・表の写しが無い写しは 2-1 の道へ戻す(`WageTablesAbsentWarning`)。
6. `run_kind` の判定: `--wage w17` のランは腕のランに数える。
7. 次の版上げで `--wage w17` の道(`weekly_work_hours` の呼び・時給 × 時間の道)を消す。消す前に安定版のタグを付ける(§0-7)。

## 12. 範囲の試験の結果

作業木の src(`PYTHONPATH=src`)・pytest `-q -p no:cacheprovider -o addopts="" -rf`・`tests/c7` は回していない。ほかの作業木のランと同時に回した。

| 範囲 | 結果 |
|---|---|
| `tests/economy`(slow を含む・1 回目) | 324 passed・3 failed → 下の 3 件を直した |
| 直した 3 件と 10f の 3 件・新しい試験(`tests/economy/test_wage_occupation.py`・`stage2/test_wage_occupation_runs.py`・`stage2/test_stage2_default_2_4.py`・`stage2/test_stage2_resume_arm.py`・`tests/engine/test_state_checks_10f.py`・`test_env_and_sections_10f.py`) | 69 passed・1 failed(新しい試験の数え方の誤り=w17 は勤務 0 時間の 29 体に払わない)→ 直して 2 passed |
| `tests/engine/bridging`+`tests/economy`(slow を除く・最後の src) | 346 passed |
| `tests/engine/bridging`・`tests/c8`・`tests/build_pop`(実データの golden を含む)・`test_state_ledger_10b`・10f の 4 本・`test_salt_seed_split_10f`・`test_version_bump_10e` | 576 passed・3 failed(10f の 2 件と K19 の数=下の直し・bridging は記録の README が無かった 1 件)→ 直した後の再実行で通った |
| `lint-imports` | 5 kept・0 broken |

1 回目に落ちた試験と直し:

- `test_stage2_default_2_4::test_resume_check_uses_the_effective_arm`・`test_stage2_resume_arm::test_resume_stops_when_the_arm_or_parts_differ`: 腕 on の状態のファイルの見出しが `wage` を持つようになった(既定 occupation)。試験の期待する見出しに `wage` を足した(w17 のときは今のまま)。
- `test_state_checks_10f::test_k19_static_sites_are_frozen`: `SAFE_SITES` の数 16 → 17(注を足した)。
- 10f の `test_seed_exchangeability_*` 2 件: 賃金の点検の値(分位・出どころの内訳・読んだ行)を設定の節(plan の中)に置いたため、seed で設定の葉が動いた。観測の `rules.wage_build` に移した(§7)。
- `economy/stage2.py` が engine の段階 2 の組み立てから `DataAbsentWarning` を import して層の契約(economy は agents/llm を import しない)を破った。economy の側に `WageTablesAbsentWarning`(UserWarning の系)を置いて直した。


## 13. 検収の直し(条件つき受入=中 2・低 8)と rebase(2026-10-17)

### 13-1. 直しの表

| # | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| M1 | `economy/anchors.py`(`min_wage_floor`=規則の表の読み手は anchors だけ=`test_only_the_manifest_and_the_daily_record_import_the_table`)・`core/wage_formula.py`(`month_hours`・`apply_floor`)・`economy/stage2.py`(`payroll`・`_floor_record`) | 最低賃金法の床(4 条 2 項)を給料日に当てる。床の値は規則の表 `minimum_wage.tokyo`(kind machine)の、その給料日に効いている版だけ(直書きに戻さない・版の無い日は床なし=宣言)。時給=月 ÷ 月の時間の目安(一般=第9表の所定内実労働時間・短時間=第2表の 1 日の時間 × 日数・写せない体は平均と同じ重み)が床を下回る体は、床 × 月の時間の目安に上げる。床に当たった体を計器に(`rules.wage_model.floor`=給料日・`rules.wage_build.floor_at_start`=ランの最初の日の版で数えた点検)。比のかけ合わせ(独立の仮定)はそのまま=台帳の注。体あたりのバイト 24 → 32 B(月の時間 8 B) | `test_min_wage_floor_reads_only_the_rules_table`・`test_apply_floor_and_month_hours`・`test_payroll_applies_the_floor_on_a_payday_with_the_rule_in_force`・`test_payroll_has_no_floor_before_the_rule_is_in_force` |
| M2 | `bridging-ledger.json` の `EX-build.pop.w21_build_b-dc566aac`・`-18118af0` | `code_at` に `src/shibuya/economy/wages.py`・「実行時の既定の賃金にも使う」の注(status・外す段 7 は不変) | `tests/engine/bridging` |
| L1 | 記録 §5・§11 の 4 | final が両腕で同じ理由=給料日が `close_final`(最後の checkpoint の後)・3 日のランでは final が違う=版上げの差 | — |
| L2 | 記録 §5 | 19 構成(1 日)は給料日を通らない=旧値の再現の根拠は給料日を含む 2 日のラン(13-3) | — |
| L3 | 記録・`bc19_*.json`・`bc4_*.json` | 最終の src で 19 構成を両腕で回し直した(1 本ずつ=`--jobs 1`) | 13-2 |
| L4 | `bridging-ledger.json` | `DOC-wage_occ-legacy-switch`(切替口と表の無い写しの戻り道・外す段 4-3) | `tests/engine/bridging` |
| L5 | `engine/state_ledger.py` の行 EC | dtype の文を実際の本数に | 状態台帳の試験(範囲の試験) |
| L6 | 記録 §7 | 既定で値が変わる既存の欄と足した欄を「版上げの差」として書いた | — |
| L7 | 記録 §3 | 22 欄 → 20 欄(数え方を書いた) | — |
| L8 | 記録 §6 | 性能は負荷の下で揺れる=親が空いた機械で測り直す | — |

### 13-2. byte-check(最終の src・5,000 体・seed 1・1 シミュ日・1 本ずつ)

| 比べ | 構成 | 25 欄が全部同じ | JSON |
|---|---|---|---|
| 本体 13e9c90 の写し vs 既定 occupation | 4(`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`) | 4 | `bc4_head_vs_occ.json` |
| 本体 13e9c90 の写し vs `SHIBUYA_WAGE=w17` | 4 | 4 | `bc4_head_vs_w17.json` |
| 土台 32fb262 の写し vs 既定 occupation | 19 | 19 | `bc19_head_vs_occ.json` |
| 土台 32fb262 の写し vs `SHIBUYA_WAGE=w17` | 19 | 19 | `bc19_head_vs_w17.json` |

19 構成の HEAD の側は前の回(32fb262 の写し)の side をそのまま使った。32fb262 と 13e9c90 で engine・economy・cli の src は同じ(差は build の側と記録・文書)。道具は本体の版で、`SHIBUYA_WAGE` が side の `env` に残る。

### 13-3. 給料日を含む 2 日のラン(5,000 体・seed 1・既定 v3・1 本ずつ)

| ラン | 開始 | final | 帳簿の流れ・残高の sha・段階 2 の計器・保存則 |
|---|---|---|---|
| 本体 13e9c90 の写し | 2026-08-24 | `21e62930…` | — |
| 作業木 w17 | 2026-08-24 | `21e62930…` | HEAD と全部同じ(流れ・残高 12 欄の sha・計器・保存則) |
| 作業木 occupation | 2026-08-24 | `21e62930…` | 流れは賃金の 3 欄だけ違う(外界 → 雇用主・賃金・預金純増 世帯 → 銀行)・残高は 3 欄(銀行の現金・外界の現金・世帯の預金)・床 なし(2026-08-25 は表に版が無い) |
| 作業木 occupation(床の効く給料日) | 2027-05-24 | `ba6b34d1…` | 給料日 2027-05-25・床 1,280 円(`rules:minimum_wage.tokyo@2026-10-01`)・残差 0 |

### 13-4. 床の計器(1,280 円=2026-10-01 からの版・雇用の行に当たる体)

| | 体 | 床に当たる体 | 割合 | p10 前 → 後 | p50 | 平均 前 → 後 |
|---|---|---|---|---|---|---|
| 5,000 体(2 日のランの給料日 2027-05-25 の計器と同じ) | 2,421 | 543 | 22.4% | 165,632 → 200,960 | 274,243(不変) | 311,362 → 320,121 |
| 39 万体の母集団 | 222,849 | 50,047 | 22.5% | 164,335 → 200,960 | 275,887(不変) | 314,527 → 323,254 |

参考(1,226 円で数えた場合): 5,000 体 463(19.1%)・39 万体 42,863(19.2%)。給料日に上げた額の和は 5,000 体で 21,203,966 円(払った賃金 775,012,166 円)。組み立ての点検 `floor_at_start` は値のある全部の体(5,000)で数える=1,009(20.2%)。

### 13-5. rebase

- 控え(`attr_fns.py`・台帳)→ 2 本を戻して `git merge --ff-only build/spatial-d102-prep`(13e9c90)→ `attr_fns.py` は `git merge-file`(本体の版・土台・控え)=衝突なし → 台帳は本体の版に本段の行を足し直した(控えの 3 行+切替口の 1 行・閉じる 1 行・注の 2 行)。
- 範囲の試験の結果は 13-6。

### 13-6. 範囲の試験(最終の src)

作業木の src(`PYTHONPATH=src`)・`-o addopts=""`・`tests/c7` は回していない。

| 範囲 | 結果 |
|---|---|
| `tests/economy tests/engine tests/build_pop tests/c8`(`tests/engine/bridging` を含む)・`-n 2 -m "not slow"`(`--dist` 無し) | 3,280 passed・1 skipped・5 failed |
| 落ちた 5 件の 4 ファイル(proximity `test_runs`・`test_intent_chooser`・`test_resume_10d`・`test_state_ledger_10b`)を `-n 2 --dist loadfile`(CI と同じ並べ方) | 144 passed |
| 同じ 5 件を 1 本ずつ | 10 passed(パラメータの分を含む) |
| `tests/economy/stage2/test_wage_occupation_runs.py`(slow・5,000 体 2 日の両腕・1,000 体の再開 両腕) | 4 passed |
| `lint-imports` | 5 kept・0 broken |

5 件は `--dist loadfile` を付けずに回したとき、同じファイルの試験が 2 つの作業者に分かれて、腕の切替口の状態(近接の腕 cell など)が入れ替わった分(1 回目の範囲の試験でも同じ 5 件)。CI と同じ並べ方と 1 本ずつでは通る。1 回目の範囲の試験では、ほかに `test_only_the_manifest_and_the_daily_record_import_the_table`(規則の表の読み手=床の値を anchors に移した)と `test_persona_build_does_not_import_or_call_llm`(式を `core/wage_formula.py` に移した)の 2 件が落ち、直した。

### 13-7. 規則の表に最低賃金の前の 2 版を足した(第337・親の一次確認 2026-10-18)

- `docs/design/rules-table.json` の `minimum_wage.tokyo` に同じ id の版を 2 つ足した: 1,163 円(asof 2024-10-01=効力 2024-10-01〜2025-10-02)・1,226 円(asof 2025-10-03=効力 2025-10-03〜2026-09-30)。1,280 円の版(2026-10-01)はそのまま。出典は厚生労働省「平成14年度から令和8年度までの地域別最低賃金改定状況」(xlsx・東京の行)と「令和8年度地域別最低賃金全国一覧」(PDF・東京の行=1,280 円・改定前 1,226 円・引上げ 54 円・4.4%・令和 8 年 10 月 1 日)・最低賃金法 4 条・14 条・retrieved 2026-10-18。note に「親が一次確認 ○(第337)」。1,280 円の版の note の「R-106 では △」は「一次確認で解消」に直した。表の読み口は今のまま(その日に効いている版=asof が日以下で最も新しい行)。
- 既存の読み手 `anchors.min_wage_hourly`(w17 の道の時給)も表の版を読むようになった: 値は同じ 1,226 円・出どころの文字が `anchors.MIN_WAGE_HOURLY` から `rules:minimum_wage.tokyo@2025-10-03` に変わる(manifest の `rules.minimum_wage.source`)。直書きは版の無い日(2024-10-01 より前)の戻り道だけに残る(台帳 `BR-MIN-WAGE-HOURLY-1226` の why に注)。
- 試験: `test_payroll_has_no_floor_before_the_rule_is_in_force` は 2024-08-26(表に版の無い日)で確かめる形にした(合成の帳簿の試験の日も同じ)。`test_min_wage_floor_reads_only_the_rules_table` に 2024-09-30(なし)・2024-10-01(1,163)・2026-08-25(1,226)を足した。規則の表の試験は、行の数 4 → 6・版の並び・世界の時点の版(`test_the_repo_minimum_wage_has_the_version_on_the_world_date`)・写し検査に親の一次確認の出典の表(`PARENT_PRIMARY_CHECK`=取得日)を足した。`test_stage2_rules_credit_atm`・`test_stage2_money_rules` の出どころの文字を直した。

世界の時点の給料日を含む 2 日のラン(5,000 体・seed 1・既定 v3・開始 2026-08-24・1 本ずつ):

| | 値 |
|---|---|
| 床 | 1,226 円(`rules:minimum_wage.tokyo@2025-10-03`) |
| 床に当たった体 | 463 / 2,421(19.1%)・上げた額 16,915,883 円 |
| 払った賃金 | 770,724,083 円(床の前 753,808,200 円) |
| 月の賃金 p10 / p50 / 平均 | 165,632 → 193,708 円 / 274,243 円(不変)/ 311,362 → 318,349 円 |
| 組み立ての点検 `floor_at_start` | 値のある全部の体 5,000 のうち 840(16.8%) |
| final | `21e62930…`(床の前と同じ=給料日の支払いは最後の checkpoint の後) |
| 保存則 | 毎日 残差 0 |
| w17 | 本体 13e9c90 の写しと final・帳簿の流れ・残高の sha・計器・保存則が全部同じ |
| occupation と w17 の違い | 流れは賃金の 3 欄だけ |

1 日の構成 `w6_v3_default`(給料日を含まない)を既定 occupation で回し直し、本体 13e9c90 の写しと 25 欄が同じ(`bc1_head_vs_occ_rules.json`)。39 万体では 1,226 円の床に 42,863 体(19.2%)が当たる(§13-4 の参考の行)。

### 13-8. TM の commit 80742bc への rebase(2026-10-18)

- 手順: 重なる 6 本(台帳・`cli.py`・`rng_audit.py`・`run.py`・`state_ledger.py`・`tests/engine/test_state_checks_10f.py`)を控え、戻して `git merge --ff-only 80742bc` → `git merge-file`(80742bc の版・13e9c90・控え)。`cli.py`・`state_ledger.py` は衝突なし。衝突は 4 か所で、どれも末尾の並び: `rng_audit.py` の `SAFE_SITES` の注の数と行(本体の T2 の 2 行の後ろに本段の 1 行=18 → 19 か所)・`run.py` の `POPULATION_RNG_DOMAINS`(本体の `talk.rate` の後ろに `economy.wage`)・`test_state_checks_10f.py` の数(18 → 19)。台帳は本体の版(522 行・active 511)に、本段の 4 行を足し 4 行を本段の版にした(閉じた 1 行・注の 3 行)=526 行・active 514。`CONFIG_PATHS_SHA256`(本体 ffbed6e3…)と規則の表は本体で変わっていない=本段の版のまま。
- 範囲の試験(`tests/economy tests/engine tests/build_pop tests/c8`・`-n 2 --dist loadfile -m "not slow"`): 3,388 passed・1 skipped・1 failed(`test_classical_social::test_run_golden_and_arms`=並列でだけ落ちる順序依存=TM の記録の申告と同じ・単独とファイル単位では通る)。`lint-imports` 5 kept・0 broken。
- byte-check(`w6_v3_default`・5,000 体・1 本ずつ): TM 80742bc の写し vs 既定 occupation・vs w17 とも 25 欄が同じ(`bc1_tm80_vs_occ.json`・`bc1_tm80_vs_w17.json`・final `b8eadcb5…`)。
- 給料日を含む 2 日のラン(5,000 体・occupation・開始 2026-08-24): rebase の前(13-7)と final `21e62930…`・帳簿の流れ・残高の sha・計器・床(463 体・19.1%・16,915,883 円)・保存則が全部同じ。
