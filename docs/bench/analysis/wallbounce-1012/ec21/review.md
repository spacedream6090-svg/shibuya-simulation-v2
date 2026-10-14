# 第 2 期 2-1 経済 EC(CP2 の段階 2)の検収の記録

- 検収役 Opus 5.5(実装は見ていない)。対象=作業木の枝 `2-1/economy` の未 commit の差分(土台 `f2405e3`)・実装役の記録 [README.md](README.md) と byte-check の JSON。本体は HEAD `533846b`(1-7・2-3b・2-0b を含む)を読むだけ。
- 正: 決定 10-12 §4-11・口の約束 1-9(約束 (3))・経済の設計 §2・発注文(親の scratch・要件の正)・1-0/T0/1-3 の規則。
- 生の出力は作業木の `_bc_review/`(git の外・検収の後に消した)。道具は検収役の scratch(リポに置かない)。数は全部実測。
- 判定: **条件つき受入**(高 0・中 1・低 6)。結果不変・保存則・税・書き手の数え直しは独立に一致した。条件=中 1(記録の文言)を直す・低は直すか親が仮採用として残す。

## 0. やったこと(一覧)

| 確かめ | やり方 | 結果 |
|---|---|---|
| byte-check 4 構成(自分) | `cp2/tools/byte_check_cp2.py`(10e の 25 欄+帳簿の 11 欄=36 欄)。a=本体 HEAD `533846b` の src の写し(`git archive`)・b=作業木の src(`PYTHONPATH`=作業木の src)。5,000 体・seed 1・1 日 | **final 4/4・36 欄 4/4 が同じ** |
| 2 日のラン(腕 off) | 2026-08-24 → 25・5,000 体・v3。HEAD の src と作業木の src | final・呼数・日の終わりの 2 つのハッシュ・帳簿の 11 欄・世帯の現金の sha が全部同じ |
| manifest 全体(1 構成) | `w6_v3_default` の `run_manifest_fields()` を両側で書き出して木で比べる | 既存の欄の値は不変(差は §5) |
| 独立の再計算(腕 on/off・2 日) | `Ledger.__init__`・`endow_households`・`on_day_end` に写しを取る口を挟み、計器のコード(`conservation_check`・`FLOW_REGISTRY`・`s2_meter`)を使わずに配列と流れの表と生ログから数え直す | 保存則・税・引き出し・IC・口座の購入・賃金・分位が全部一致(§6) |
| 系の宣言(腕 on) | 段 B の `declared_check`(全部の族)を腕 on の合成の世界 2 日(財布 1/50・ATM 8 セルに 1 つ)で | 5 刻みごと 11,606 回の写しで宣言の外 0 |
| 植えた負の対照 | ① phase_c の宣言から `EC:ledger.*` を外す ② `EM:ledger.*` を外す ③ AST の走査器に直書き 4 形 ④ 登録の外の流れを 1 本 ⑤ 実行時の書き換え | ① 70 件 ② 25 件の宣言の外が出た ③ 4 形とも拾う ④ 検算が落ちる ⑤ §4 |
| 試験 | 発注の範囲(`not slow`・`-n 2`)+ `tests/economy/stage2` の slow 4 本・`lint-imports` | §7 |

注(道具の罠): 最初の b 側を `PYTHONPATH` なしで回したら、venv の editable install が本体の src を指していて b 側も本体の src になった(`src_is_worktree` が偽・日次の記録に `conservation` が無い)。捨てて回し直した。実装役の JSON は b 側 19 本とも `src_is_worktree` が真で正しい。byte-check の道具の b 側に `src_is_worktree` の検査を足すと防げる(親へ)。

## 1. 結果不変 ✓

- 実装役の [byte_check_ec21_off.json](byte_check_ec21_off.json): 19 構成・36 欄とも「動いた」0・b 側の `src_is_worktree` は 19/19 真・`economy_b` の輪の係数 6.5・`stage2` の鍵なし(腕の既定が今の道)。[byte_check_ec21_off_last4.json](byte_check_ec21_off_last4.json) も 4/4・36 欄が同じ。
- 自分の 4 構成(本体 HEAD `533846b` の src ↔ 作業木の src): final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`、呼数 65,597・50,301・51,835・69,111 が両側で同じ。36 欄・manifest の `economy`・日次の出来事の行数・テープのバイト・full-hash の外の行ごとのバイトも同じ。日次の記録の `economy` は末尾に `conservation` が足されただけ(残りの欄と順は同じ・4 構成とも `ok`・残差 0)。
- 2 日のラン(腕 off): final `17f89bf0a109f2dd`・145,049 呼・`state_hashes_end_of_day`・最後の checkpoint の 2 つのハッシュ・帳簿の 11 欄が HEAD と同じ。
- 本体 HEAD は土台から 1-7・2-3b・2-0b が進んでいるが、既定の道では 4 構成とも final が同じ(発注の「違えば記録に」=違いなし)。

## 2. 口と約束

口の違い(1-9 の口に足したもの・名と欄):

- `ops.transfer(ledger, src, dst, amount, what, cause, t_ns, *, method=METHOD_CASH)`: キーワードだけの `method` を足した。`what` に科目の名でない語 2 つ(`MONEY_EXTRA_WHAT`=`金:引き出し`・`金:カード`=科目は預金純増)。口座の方法は世帯の脚を預金で動かし決済の行を 1 行足す=戻りの `TransferId.n` は 2 倍。基本操作は 1 つのまま・湧かせない(§6 で部門ごとの Δ現金と ΔM を数え直して確かめた)。
- `Ledger.transfer_many(..., method=, what=)`・新しい口 `attach_stage2`・`can_pay_many`・`withdraw_many`・`pay_fares_many`・`raw_methods`・`Ledger(…, rows_per_agent_day=)`・`raw_capacity_for(…, rate=)`。
- `accounts.is_allowed(…, stage2=False)`・`STAGE2_PAIRS`・`faucet_sink_table(stage2=True)`(**既定が段階 2 の組を含む**=77 → 79 行)・`FLOW_REGISTRY`(17 行・組 15)・`registered_cells`・`flow_registry_table`。`checks.conservation_check(close, cells=None)`(欄 faucet・sink・internal・unregistered・delta_money・residual・residual_code・ok)。
- `anchors.min_wage_hourly(asof)`・`consumption_tax_rate(asof)`・`monthly_wage_amounts(…, hourly=)`・`monthly_wages(…, hourly=, payer_sector=, method=, cause=)`(既定は今の呼び方)。`Rights.pairs`・`Fixtures.atms`・`RunResult.money_stage2_in`(`conserved` の式の左辺)。

約束と試験:

| 約束 | 試験 | 判定 |
|---|---|---|
| 1-9 (1) final・帳簿・台帳の行が 19 構成で不変 | byte-check(道具)・cp2 の slow の HEAD との同値 2 本(実装役) | ✓(自分は 4 構成) |
| 1-9 (2) 別名の書きは transfer の中 | `tests/economy/cp2`(自分の実行で通過) | ✓ |
| 1-9 (3) 保存則の検算を全登録に(2-1 で) | `test_stage2_account_and_conservation.py`(検算の欄と値・負の対照 2 本・腕なしでも日次に) | ✓ |
| 共通 ◎ 2 日 | 実装役は腕 off の 2 日を回したが HEAD と比べていない | ✓(自分が比べた=同じ) |
| 共通 ◎ 再開 | `test_stage2_resume.py`(腕 on・slow 2 本)・`test_resume_10d.py` | ✓ |
| 共通 ◎ 系ごとの指紋(HEAD と) | **無い**(実装役の §11「回していないもの」) | ✗ → 代わりに腕 on の段 B の宣言の検査と植えた負の対照を回した(宣言の外 0・外すと出る)。HEAD との系ごとの指紋の比べは残る |

〔決定〕10-12 §4-11 の反映: EC1 の賃金・買い物・運賃・預け入れと引き出し・税は入った。家賃・年金・社会保険料の天引き・借金の返済は入っていない(天引きは器・信用は器だけ=宣言どおり)。EC3・EC4・EC5 は規則(expedient)で入った。税の「納め先は国・都・区」は政府の部門 1 つ(分けていない=4-2 の段の範囲と読む)。見張りの財布と預金の分位は日次と manifest に出る(家計調査との比較は出さない=検証専用)。

## 3. 発注文の各項

| 番号 | 判定 | 根拠 |
|---|---|---|
| 腕と部品 | ✓ | `--economy-stage2 {off,on}`・`SHIBUYA_ECONOMY_STAGE2`・`--economy-stage2-parts`。組み立てで読む・`run_day` の引数と設定の指紋の外 |
| 1 賃金 | ✓ | 権利台帳 `employ` → 世帯の預金・`Process("payroll")`・月の時間 × 最低賃金(規則の表 asof)・給料日 25 日(土休は前の営業日・`DOC-ec21-payday-25`=出典なし)・原資=外界 → 雇用主(登録)・25 日をまたぐ 2 日の試験 |
| 2 引き出し | △ | 規則・営業時間・預金 ≥ 額・`Process("atm")`・`Fixtures.atms`(`DOC-ec21-atm-fixture` 外す段 2-4)は ✓。(i) 規則は mock/古典の方策の中でなく台帳の「副の判断」(仮採用 2・宣言あり)。(ii) 腕 port の「お金を下ろす」の答えは行為へ運ばれない(限界 1・申告あり)。(iii) `atm` の印の無い銀行の支店 12/23 を場所から外した(発注は「ATM か銀行の支店のセル」=L3) |
| 3 支払い方法 | ✓ | 口座=世帯の預金 → 店・方法の列 1 B・規則(財布が足りれば現金)・IC 既定・預金不足で現金に戻る(負の対照)・port で候補の文に注 |
| 4 税 | ✓ | 規則の表の 7.8%×(1+22/78)=10%・レジで店 → 政府・`Process("register")`・帳簿の店の現金は税抜き。天引きは器(0・`DOC-ec21-payroll-deduction-blank` 外す段 4-2)。`pois.revenue` の写しは税込のまま(申告 §11-6) |
| 5 来街者と外界 | △ | 口座 ✓・外界の売上の faucet は登録(額 0・縮小の比 0.0128 を manifest に)✓。ただし来街者の預金は持ち込みを「分ける」のでなく財布に**上乗せ**(L2) |
| 6 信用 | ✓ | `CreditBook`(4 種・限度・残高・返済日・延滞)・`repay_due`(口座から・不足は延滞)=呼び手なし・試験だけ |
| 7 保存則 | ✓ | `FLOW_REGISTRY` と `conservation_check`(腕の有無によらず日次)・残差の科目 `residual`・負の対照 2 本 |
| 8 見張り | ✓ | 日次と manifest の `economy.stage2`(腕・部品・件数と額・方法の内訳・税・登録の表・分位)。既存の欄は不変(§5) |
| 9 語彙と出来事 | ✓ | `金:引き出し`・`金:カード` を表の末尾(版 `events-vocab/2-1`)・`payroll`・`atm`・`register` を `CAUSE_PROCESS_NAMES` の末尾(`金:賃金`・`金:税` は既存) |
| 10 状態台帳・凍結・manifest | ✓ | 行 EC・ATM・CR・EM・テープの列は不変(byte-check の `calls_column_names` が同じ) |

「できなかったこと」の申告(§11)は実態と合う: call_id の配線なし(引き出しの原因は `Process("atm")`)・port の答えを運ばない・`TRANSFER_PORTS_HOUSEHOLD` の外の口・信用は呼び手なし・天引きと EC2 は後・系ごとの指紋と manifest の 7 本の比べと 39 万体は回していない。

## 4. 守り

- 書く口: お金の列の書き手は `transfer` と凍結の 8 関数のまま(cp2 の AST の試験が通る)。凍結の表の増分は `Ledger.__init__` の `_raw_method` だけ(表の約束=親の承認が要る)。新しい 3 モジュールは `Ledger.transfer_many` を呼ぶだけ(`_lines`・`_flow[`・窓を開く口の文字列なし)。植えた負の対照: `economy/stage2.py` の写しに `ledger._lines[0][0][0] = 1`・`ledger._raw_method[0] = 1`・`agents.registry.money[0] -= 1`・別名 `x = ledger._lines; x[0][0][0] = 1` を足すと走査器が 4 つとも拾う(元の写しは 0 件)。
- 世帯の現金を書く新しい口 `withdraw_many`(resolve の `_stage2_withdraw` が呼ぶ)は 1-9 の口の名の表の外。閉包の系(phase_c)の `writes.soa` が `agents.money` を持つことを試験が見る(申告の限界 2=親の判断)。
- 実行時の守り(**低 L1**): `AtmTable` は凍結の dataclass で属性は書けないが、配列は書ける(`t.cell[0] = 9` が通る・`writeable=True`)。`accounts.STAGE2_PAIRS` は普通の dict で、ランの中で `STAGE2_PAIRS[家賃] = ((外界, 雇用主),)` とすると `is_allowed(家賃, 外界, 雇用主, stage2=True)` が偽 → 真になる(1-3 の教訓「表は MappingProxyType」。既存の `ACCOUNTS` も dict)。`Stage2Plan`・`MoneyStage2`・`CreditBook` に `__setattr__` の守りは無く、`Ledger._stage2_pairs` も書ける。
- 負の対照(試験): 登録の無い流れ(利子 銀行 → 世帯)・登録を 1 行外す・営業時間の外の ATM・預金不足のカード → 現金。植えた負の対照(自分): 登録の外の組(利子 世帯 → 銀行・123 円)を流すと `ok=False`・`unregistered=123`・`residual=-123`。

## 5. 宣言と凍結

- 系の宣言: phase_c・day_close・close_final に `EC:ledger.* EM:ledger.*`・world に `EM:ledger.*`。腕 on の段 B の検査で宣言の外 0、phase_c から EC か EM を外すとそれぞれ 70 件・25 件の宣言の外(宣言は要るものだけで足りている)。build(挿す・初期の預金)は宣言の検査の外(今の約束どおり)。
- 状態台帳: EC(behavior・derivable・hash_skip)・ATM(behavior・derivable・hash_skip)・CR(diag・derivable・hash_skip)・EM(diag・discardable)。腕 off で ATM の表と信用の器は作られない(`attach` が先に返る)。`_raw_method` は腕 off でも輪と同じ長さで作られる(5,000 体で 32,500 B)が、full-hash・日の終わりのハッシュ・状態のファイルの外の行のバイトは HEAD と同じ(§1)。腕が設定の指紋にも状態のファイルの頭にも入らない=腕を変えて再開しても気づけない(1-3・1-6・1-8 の腕と同じ形・親へ)。
- 凍結の表: `money_writers_frozen.json`(`_raw_method` を 1 つ)・`CONFIG_PATHS_SHA256`(`economy.stage2` の設定の 8 道筋)・規則の表の読み手の一覧(`economy/anchors.py`)・数の試験(状態台帳 193 → 197・語彙 56 → 58・`V.VOCAB[55]`)。増えた分だけ。
- manifest(`w6_v3_default`・HEAD ↔ 作業木): 既存の欄の値は不変。差は `tools` が無い(作業木の土台に 1-7 が無い=rebase で戻る)・`bridges_count` 291 → 300 と `bridges_version`(台帳の行の差)・新しい欄(日次の `economy.conservation`・`manifest_sections` の `economy.stage2.*` と `decision_port.stage2`・`decision_port.stage2` は null)。環境の欄(git の印・env_id)はラン環境の差。

## 6. 同値と独立の再計算

試験で読んだ同値: 腕 off は台帳に何も挿さない・方法の列 0・検算 ok(合成 2 日)/ 腕 port と legacy の final と呼数が同じ(mock)/ 腕 on の再開(日の境目と 1 日目の昼)が通しと同じ(final・日の終わりのハッシュ・残高・検算)/ cp2 の HEAD の台帳の写しとの同値(slow・実装役)。

独立の再計算(世界資産 5,000 体・seed 1・v3・2026-08-24 → 25・腕 on(全部)と off)。やり方: `Ledger` の 3 つの口に写しを取る口を挟み、台帳の生成の直後(全部 0 を確かめた)・初期の財布の後・毎日の締めの後の、部門ごとの現金・預金・借入の和、世帯の現金と預金の配列、その日の流れの表、生ログの行と方法の列を写す。計器のコードは使わない。

| 量 | 腕 on(0 日目・1 日目) | 記録・計器の値 | 一致 |
|---|---|---|---|
| final・呼数 | `c64b7f6cc6a4e280`・144,954 | 同じ | ✓ |
| 部門ごとの Δ現金 − (流れの表の入り − 出・全科目) | 6 部門とも 0・0 | — | ✓ |
| ΔM(世帯・店舗・雇用主の現金+預金)− 境界をまたぐ流れ(預金純増を除く) | 1,198,147,865 − 1,198,147,865 = 0・111,401,530 − 111,401,530 = 0 | delta_money 同じ・residual 0 | ✓ |
| 銀行の Δ現金 = Δ借入(預金負債)= 世帯の預金の増え | 769,710,980・109,531,404 | — | ✓ |
| 流れの表の欄 | 0 日目 8 欄・1 日目 8 欄、全部 `FLOW_REGISTRY` の組 | unregistered 0 | ✓ |
| 税 = Σ⌊税込 × 10/110⌋(購入・食事の行ごと) | 680,277+471,488 = 1,151,765(行 9,736+6,476) | 1,151,765・16,212 行 | ✓ |
| 引き出し(預金純増 銀行 → 世帯・方法 0) | 166+139 = 305 回・5,950,000 円・千円の倍数でない額 0 | 305・5,950,000 | ✓ |
| IC の運賃(持ち出し・方法 1)・現金の運賃 | 3,544+3,795 = 7,339・0 | 7,339・0 | ✓ |
| 口座の購入・食事(方法 1) | 5+23 = 28 行・25,600 円 | 28・25,600 | ✓ |
| 賃金(雇用主 → 世帯)・原資(外界 → 雇用主) | 2,392 行・112,838,004 円・原資 同額 | 同じ | ✓ |
| 賃金 = Σ rint(月の時間 × 1,226)(雇用の行 2,421・時間 0 は 29・全部 組織・索引の最大 9,871 < 9,872) | 112,838,004 | 同じ | ✓(時間は台帳の `monthly_hours` を使った=半独立) |
| 方法 1 の行: 決済の行 = 本体の行 | 8,549 = 8,549・6,210 = 6,210 | — | ✓ |
| 財布 p10/p50/p90(1 日目の終わり) | 7,789・20,025・52,604 | 同じ | ✓ |
| 預金 p10/p50/p90(1 日目の終わり) | 35,320・194,464・234,752 | 同じ | ✓ |
| 世帯の現金の 1 体の増減 | −838.6・−520.8(off −1,625.5・−1,168.4) | 同じ | ✓ |
| 世帯の現金+預金の 1 体あたり(日の終わり) | 181,013.2 → 202,398.7(+21,385.5) | 同じ | ✓ |
| 貨幣供給量の 1 体あたりの増え(1 日目) | +22,280.3 | +22,280 | ✓ |

腕 off でも同じ式で部門ごとの Δ現金・ΔM の残差は 0・0(ΔM 425,121,562・−954,424)。

## 7. 試験

- 発注の範囲(作業木・`PYTHONPATH`=作業木の src・`-m "not slow" -n 2 --dist loadfile`): `tests/economy`・`tests/engine/systems`・`events`・`rights`・`decision`・`rules`・`time`・`bridging`・`test_resume_10d.py`・`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`tests/perception` → **1,312 passed**(15 分 56 秒・data が無くて飛ばした試験 0)。`tests/c7` は回していない。
- `tests/economy/stage2` の slow 4 本(世界資産の 2 日の腕 on/off・腕 on の再開 2 本)→ **4 passed**(3 分 38 秒)。新しい試験は 56 本(52+slow 4)で記録 §8 と合う。
- `lint-imports`(作業木の src): 5 契約とも守られている(210 ファイル・777 の依存)。economy → engine(`anchors` が `engine.rules.table` を読む)は層の契約の向きのとおり。
- 全体(`not gpu and not slow`・`-n 4`)は親が回す。

## 8. 抜け道と記録

- (a) 既定 off の結果不変 ✓(§1・§5)。
- (b) 保存則 ✓。発注の 6 つ(賃金の原資・外界の売上・初期の財布と預金・参入資本・来街者の持ち込み・税の sink)は全部 `FLOW_REGISTRY` にある。2 日のランで残差 0 を自分で再計算した(§6)。負の対照は試験 2 本+植えた 1 本。注: 許された組 76(表の 77 行は退蔵項の測度の 1 行を含む)+段階 2 の 2 のうち、既定の 76 組の 63 組(残差科目 36・利子 5・参入資本 5・家賃 4・配当 4・預金純増の店と雇用主 4・減価償却の自己ループ 3・域外仕入 雇用主 → 外界 1・税 雇用主 → 政府 1)は登録の外=呼び手ができた日に検算が落ちる(記録 §4「呼び手を作る段で登録する」の規則どおり。減価償却の呼び手が入る段で登録を忘れないこと)。
- (c) お金の列の書き手 ✓(§4)。`economy/stage2.py`・`engine/economy_stage2.py`・`credit.py` は `transfer_many` を通す。
- (d) 規則の表の読み手 ✓。2026-09-30=1,226・2026-10-01=1,280 の試験・消費税 10%(表の `combined_rate` と突き合わせ)・天引き 0(表に行が無い=宣言)。`MIN_WAGE_HOURLY` 1,226 は既定の道では使われない(呼び手は腕 on の賃金だけ・版の前の日の戻り先=`BR-MIN-WAGE-HOURLY-1226`)。2 日のラン(8/25)は 1,226 円を使った(2025-10 〜 2026-09 の東京都の値と合う)。
- (e) 部品ごとの動き ✓(△ は §3 の 2・5)。ATM の表: OSM の `amenity=atm` は 7 要素・`atm=yes` は 36(コンビニ 25・銀行 11)=合わせて 43(発注の「`amenity=atm` 43 要素」は言い方の誤りで、実装の読みが正しい)。営業時間は要素の印 26(24/7 が 23・Mo-Fr 09:00-15:00 が 3)・取得物 2026-09-07 の 25 要素は全部 43 点と重なり印を足さない・無い 17 点は 24 時間(銀行の支店 8 点を含む=宣言)。部品を 1 つ止めると当該の流れが 0 の試験 5 本を読んだ。
- (f) v1 の原因への手当て ✗(**中 M1**・記録の文言)。数え直しの値は記録と同じ(§6)。しかし記録 §6 の「2 日の範囲で尽きる型は止まった(財布 0 の体 0)」は言いすぎ: 腕 off でも 2 日で財布 0 の体は 0(区別にならない)。世帯の現金は腕 on でも −839・−521 円/体/日で減り続ける。月の収支の見込み(推測=2 日の外挿): 1 日目の世帯の支出(購入・食事 5,227,600+運賃 683,100)= 1 体 1,182 円/日 ≈ 30 日で 35,464 円に対し、月の賃金は 112,838,004 ÷ 5,000 = 1 体 22,568 円 → 現金+預金は月に 1 体 約 1.29 万円(1 日 約 430 円)減る。減り方は緩むが止まらない(原因は月の労働時間の短さ=記録の親に確かめてほしい点 3 と同じ)。
- (g) 語彙・原因・manifest ✓。金の 2 語は表の末尾・原因の名は `CAUSE_PROCESS_NAMES` の末尾・`economy.stage2` は `economy` の中の末尾(腕 on だけ)・`decision_port.stage2` は観測の末尾・既存の欄は不変。
- (h) 共有ファイルの当たり: 触った共有ファイルの一覧(記録 §9)は `git diff --stat` の 26 ファイル+新規(src 3・試験 8・記録)と合う。記録に絶対パス・ホスト名なし・LF(README・道具・JSON 4 本)。rebase の後の並びの案(本体 HEAD は 1-7 を含む):
  - `engine/events/vocab.py`: 1-7 の `道具:看板`(コード 56)の後に `金:引き出し`(57)・`金:カード`(58)。`CAUSE_PROCESS_NAMES = PROCESS_NAMES + CHECK_PROCESSES + PERCEPTION_PROCESSES + ECONOMY_PROCESSES`。版 `events-vocab/2-1`。試験の数は 12+20+15+8+1+1+2 = 59。`test_rights_events.py` は両方が同じ行(`V.VOCAB[55]`)に直した=注の文だけを合わせる。1-8b が先に入れば語はその後ろ。
  - `engine/state_ledger.py`: J0 → CT5(1-7)→ EC・ATM・CR・EM。外の状態 107・全体 198。`test_state_ledger_10b.py` の鍵の並びと数を合わせる。
  - `engine/systems/boxes.py`・`build.py`: `Fixtures(…, tools=…, atms=…)`・`DecisionLayer(…, tools=…, money_stage2=…)` を両方残す。`decision/layer.py` は 1-7 の `tools` と本段の `money_stage2` の引数が隣り合う。
  - `engine/run.py`・`systems/report.py`: 1-7 の `RunResult.tools` と本段の `money_stage2_in` の行が近い=両方残す。
  - `engine/manifest_sections.py`: 1-7 の `tools` と本段の `economy.stage2`・`decision_port.stage2` は別の塊。`CONFIG_PATHS_SHA256` は 1-7 の `tools` が観測だけなので本段の値 `494d6d4c…` のままのはず(rebase の後に試験で確かめる)。`test_env_and_sections_10f.py` は 1-7 の `C07_KEYS` と本段の sha の行が別。
  - `docs/design/bridging-ledger.json`: 本体の末尾の後ろに `DOC-ec21-*` 14 行(本体 291 → 305 の見込み)。
  - `engine/systems/table.py`: 同じ系の `writes.paths` の文字列に 1-7 の追記がある所は両方の語を残す。
  - 1-8b・2-2 が先に入る場合も、語彙・状態台帳の行・manifest の末尾は「後から入る方がさらに後ろ」で並べる。

## 9. 欠陥(重さ順)と直し方

| 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|
| 中 M1 | 記録 [README.md](README.md) §6 の「v1 の 1 日 1 体 536 円ずつ減る」の段 | 「2 日の範囲で尽きる型は止まった(財布 0 の体 0)」は腕 off でも同じ(財布 0 の体 0)で区別にならない。現金は腕 on でも減り続け、月の収支の見込みは 1 体 約 −1.29 万円(推測) | 「減り方は緩んだ(−1,168 → −521 円/体/日)・止まってはいない(月の賃金 1 体 2.26 万円 < 支出 約 3.5 万円=2 日の外挿・推測)」に直す。§0 の要約も合わせる |
| 低 L1 | `engine/economy_stage2.py` `AtmTable`・`economy/accounts.py` `STAGE2_PAIRS`・`Stage2Plan`・`MoneyStage2`・`Ledger._stage2_pairs` | 実行時の守りが無い(配列が書ける・dict が書ける・属性が書ける)。植えて確かめた(§4) | `build_atm_table` の配列を `setflags(write=False)`・`STAGE2_PAIRS` を `MappingProxyType`・組み立ての物に `__setattr__` の守り(組み立ての後は `runner` だけ) |
| 低 L2 | `economy/stage2.py` `MoneyStage2.endow` | 来街者の預金=持ち込み × 0.5 を財布(日の消費 × 3 の対数正規)に**上乗せ**。発注は「持ち込みを財布と預金に分ける割合」 | 分ける(財布を減らす)か、上乗せを仮採用として記録 §10 と `DOC-ec21-initial-deposit` に書く(親の判断) |
| 低 L3 | `engine/economy_stage2.py` `build_atm_table` | `amenity=bank` 23 のうち `atm` の印の無い 12 を引き出しの場所から外した。発注は「ATM か銀行の支店のセル」。記録の「窓口だけの銀行」は印が無いだけで確かめていない | 支店を窓口の営業時間つきで入れるか、外す理由を「印が無い」と書き直して親の承認を取る |
| 低 L4 | `economy/ledger.py` `withdraw_many`・`pay_fares_many`、`engine/resolve.py` `_stage2_withdraw` | 新しい関数の引数に `tick` の名(許可の表にある名なので T0 の試験は通る)。T0「新しいコードは刻み系の名」に反する | 新しい 3 つの引数を `step` に(既存の口 `transfer_many` の `tick` は今のまま) |
| 低 L5 | 記録 §11「回していないもの」 | 系ごとの指紋の HEAD との比べ(1-0 の共通の約束 ◎)が無い。検収では腕 on の宣言の検査と植えた負の対照で代えた | 親が取り込みの後に 1 構成で回すか、残りとして PENDING に |
| 低 L6 | `economy/accounts.py` `faucet_sink_table` | 既定が `stage2=True`=腕 off のランでは許されない 2 組も「表」に出る | 名の意味(許された組の全部か・段階 2 も含む全登録か)を docstring と記録 §4 に 1 行 |

## 10. 親に確かめてほしいこと

1. 凍結の表 `money_writers_frozen.json` の `Ledger.__init__` に `_raw_method`(表の約束=親の承認)。
2. `withdraw_many` を 1-9 の口の名の表 `TRANSFER_PORTS_HOUSEHOLD` に足すか(記録の限界 2)。
3. 月の労働時間(W17 の勤務・雇用の行の体で平均 38.0 時間)を使い続けるか、統計の値にするか(M1 の結論に効く)。
4. 腕のランの輪の係数 16.0(39 万体で 224.7 MB)と、腕 off の輪 6.5 の余裕 5%(2 日の和の最大 6.19)。予算の宣言の文書(`v2-budget-declaration.md`)の更新は親の範囲。
5. 腕が設定の指紋にも状態のファイルの頭にも入らない=腕を変えて再開しても気づけない(ほかの腕と同じ形)。
6. byte-check の道具の b 側に `src_is_worktree` の検査を足す(§0 の注)。
7. 来街者の預金(L2)・銀行の支店(L3)の扱い。
