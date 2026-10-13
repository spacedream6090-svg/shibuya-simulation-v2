# 第 1 期 1-9 お金の基本操作(CP2 の段階 1)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `1-9/money-transfer`(HEAD `136fdbb`=T0 と 1-3 を取り込んだ後)。commit は親。
- 正: [口の約束 1-9](../../../../design/v2-foundation-contracts-2026-10-13.md)・[計画 1-9](../../../../design/v2-implementation-plan-2026-10-12.md)・[決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-5 CP1・CP2・CP3・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §3(K17)・§0-3(仮採用)・[10b-prep](../../wallbounce-1003/10b-prep.md) §3-2(帳簿の 9 口 E1〜E9)・§3-4(4.07 行/体/日)。先例は [R-113](../../../../research/v2-r113-e1-foundations-existing-implementations.md) §10(TigerBeetle=口の残高は transfer でしか変わらず transfer は変えない記録・Apache-2.0/ftrace と OTel=捨てた数を必ず出す)。借りたのは形だけで、コードは写していない。
- 数は実測。生の出力(テープ・side の JSON)は git の外の作業用の置き場(作業木の `_bc/`)に置いた。比べた結果と道具だけをこのフォルダに置く(道具は `tools/`・絶対パスなし)。
- 道具: `tools/byte_check_cp2.py`(10e の byte-check の 19 構成に帳簿の残高と金・物の台帳の行の sha と manifest の `economy` を足す・`--rate` で輪の係数を上書き)・`tools/k17_numbers.py`(K17 の容量・バイト・宣言の投影)。2 日のランは既存の `10e/two_day_check_act.py`。

## 0. 結論

- 基本操作 **`economy/ops.py` の `transfer(ledger, src, dst, amount, what, cause, t_ns) -> TransferId`** を作った。帳簿の口(`Ledger.transfer`・`transfer_many`・`purchase_many`・`endow_households`・`endow_stores`・`depreciate`)は検査(行ごとの `TransferStatus`)までを受け持ち、通った行を `transfer` に渡す。**残高・流れの表・生ログを書くのは `transfer` だけ**(旧 `_apply_cash`・`_record` は消して中身を `transfer` に移した)。
- **AST の検査**(`tests/economy/cp2/test_cp2_transfer_only_writer.py`): src の全部で、お金の列(`agents.money`・`pois.revenue`・帳簿の残高・流れの表・最後に動いた日・`_raw_*`)の書き手は `transfer` と凍結の表の 8 関数(組み立て 2・締め 1・評価替え 1・段階 2 の 4)だけ。負の対照 5 本(発注の 3 本=別名・`np.add.at`・属性の鎖+ops.py の transfer の外・実物の ledger.py に足した書き+`out=`・`field`・`fill`・`copyto`)。1-0 の別名の表 `ALIAS_WRITES` から `_apply_cash` の 4 行が消えた(帳簿の口の名から AST で引く規則 1 つに閉じた・閉包は不変)。
- **K17**: `TRANSFERS_PER_AGENT_PER_DAY` 3.0 → **6.5**(≥ 4.07 × 1.5 = 6.105)。5,000 体の容量 16,384 → 32,500 行。溢れた件数を計器・manifest の `economy.raw_overflow`・日次の記録 `economy.overflow` に出し、溢れても止めない。**19 構成(5,000 体)で溢れ 0 件**(1 日の行は 11,375〜20,183=2.28〜4.04 行/体/日)。
- **目印の列**: 金の生ログ(`_raw_event_t_ns`・`_raw_event_seq`)と物の納品ログ(`_dl_event_*`)に出来事の id の列。原因を渡した行は `transfer` が 1 行ごとに出来事(`what=金:<科目>`)を書き、その id を入れる(1 対 1)。いま原因を渡すのは**運賃(過程 rail)と補充の代金(過程 shelf)**。購入・食事・初期の財布・参入資本は原因が届かないので目印は空(数は計器 `transfers_uncaused`)=§11 の仮採用 5。
- **締めの検算**(新しい 1 本): その日の transfer の額の和=流れの表の和。日次の記録 `economy.flow_sum_ok`。既存の四重記入の検算はそのまま通る。
- **結果不変**: byte-check 19/19 構成で **final が同じ**。輪の係数を HEAD と同じ 3.0 に戻すと **19/19 構成で 36 欄(10e の 25 欄+帳簿の残高と台帳の行の 11 欄)が全部同じ**。既定(6.5)で動いた欄は輪の容量と、HEAD で輪が溢れていた 5 構成の生ログの行数・落ちた行の数・**full-hash(最後の checkpoint と締めの後)**だけ=K17 の結果(§8・親に確かめてほしい点 1)。帳簿の残高・流れの集約行・取引の件数・却下の計数・物の台帳・世帯の現金・生ログの末尾 16,384 行は 19/19 で同じ。2 日のラン(final `912446bd2b42b6ab`・140,913 呼・テープの sha)も HEAD の記録と同じ。
- 試験: 新しい試験 80 本(`tests/economy/cp2/`・76 本+`slow` 4 本・独立検収の直しの後は 109 本=87 本+`slow` 22 本=§12)。全体は 4,175 passed・1 failed(junction 由来の既知)・1 xfailed(29 分・§9)。`lint-imports` 5 契約とも守られている。仮採用は §11(12 件)。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/economy/ops.py`(新) | 基本操作 `transfer`・`TransferId`(生ログの通し番号の範囲)・計器 `TransferMeter`(行・額・原因の無い行・出来事の行・溢れ・日の締めの検算)・お金の列の宣言 `MONEY_PATHS`/`MONEY_ATTRS`・金の語 `MONEY_WHAT`(`金:<科目>`)・口の名 `account_name` |
| `src/shibuya/economy/ledger.py` | 6 つの口が検査の後に `ops.transfer` を呼ぶ(`cause` を足した=既定 None)・`_apply_cash`/`_record` を消した・K17 の係数 6.5 と `raw_capacity_for`(1 日ぶんを切り上げ × 日数)・目印の列 2 本・`attach_events`・`raw_position`・`raw_event_ids`・`event_ids_between`・`economy_record`・締めで計器の検算・目印の列の宣言 `transfer_log_event_ids`・`bytes_total` に目印の列 |
| `src/shibuya/economy/goods.py` | 納品ログの目印の列 2 本・`restock_many`/`deliver` に `cause`(代金の transfer へ渡し、代金の行の id を物の行に写す)・`delivery_event_ids`・宣言 `delivery_log_event_ids` |
| `src/shibuya/economy/__init__.py` | docstring に `ops` |
| `src/shibuya/engine/events/links.py` | `MoneyEventLink`(金の生ログの口: 行ごとに出来事を書いて id を返す=`ActualLogLink` と同じ依存逆転。economy は `engine.events` を import できない=§2) |
| `src/shibuya/engine/ledger_api.py` | Protocol の口に `cause`・`LedgerBundle.attach_events`(口を台帳へ渡すだけ)・`economy_record`・`economy_day_record` |
| `src/shibuya/engine/systems/build.py` | 出来事の記録を作った後に `MoneyEventLink` を作って台帳に挿す |
| `src/shibuya/engine/processes/rail.py` | 運賃の原因 `FARE_CAUSE = Process("rail")` を `transfer_many` に渡す |
| `src/shibuya/engine/processes/goods_flow.py` | 補充の原因 `RESTOCK_CAUSE = Process("shelf")` を `R.restock` に渡す |
| `src/shibuya/engine/resolve.py` | `restock` に `cause`(物の台帳へ渡すだけ)・docstring の `_apply_cash` の参照 |
| `src/shibuya/engine/systems/state_io.py` | 日次の記録に `economy`(`events` の前) |
| `src/shibuya/engine/run.py` | manifest の `economy`(〔rebase の後〕末尾=T0 の TM9 → 1-4 の欄 → 1-9)と `RunResult.economy_fields` |
| `src/shibuya/engine/state_ledger_ast.py` | 外の状態の軸 1 の AST(10f)の診断の出口 `DIAG_EXITS` に 2 行(`economy/ops.py` の `transfer`=台帳の書き手・`LedgerBundle.economy_day_record`=計器)。旧 `_apply_cash`/`_record` は持ち主のファイルの中だったので当たらなかった |
| `src/shibuya/engine/manifest_sections.py` | `economy` の節(容量・係数・行のバイト・溢れの扱い=設定/溢れ・transfer の計器=観測) |
| `src/shibuya/engine/systems/table.py` | `C:ledger.*` を world・phase_c・day_close・close_final に・`E:events.*` を phase_c に |
| `src/shibuya/engine/systems/allow.py` | `ALIAS_WRITES` から `_apply_cash` の 4 行を消し、`TRANSFER_WRITES`・`TRANSFER_PORTS_HOUSEHOLD` と `ResolveIndex.transfer_callers`(帳簿の口の呼び出しから AST で引く) |
| `src/shibuya/engine/state_ledger.py` | 行 `A`(〔検収 L3〕前は `C`・軸 1 diag・軸 2 discardable・道筋 5)・除外 3 つ(`_events`=参照・`_step_ns`/`raw_rows_per_agent_day`=設定) |
| `tests/economy/cp2/`(新) | 試験 7 ファイル(§9・〔検収 M2〕`test_cp2_write_window.py` を足した)・道具 3 本(`money_writers.py`=お金の列の書きを集める AST・`head_copies.py`=HEAD の写しの読み込みと状態の突き合わせ)・HEAD の写し 2 本(`head_ledger_136fdbb.py`・`head_goods_136fdbb.py`=`git show 136fdbb:` のまま・blob の名で確かめる)・凍結の表 `money_writers_frozen.json` |
| 既存の試験(発注の一覧の外=§10) | `tests/economy/test_ledger.py`・`tests/engine/test_ledger_wiring.py`(K17 の数)・`tests/economy/test_single_write_path.py`(残高の配列に触れてよいのに ops.py)・`tests/engine/systems/test_stage_a_guard.py`(別名の表の 4 行)・`tests/engine/test_two_phase.py`(hot path に ops.py=発注どおり)・`tests/engine/test_state_ledger_10b.py`(行の数)・凍結の表 2 つ(manifest の鍵・`E:events.*` の系) |

## 2. 基本操作 `transfer` の口と約束

- 口: `transfer(ledger, src, dst, amount, what, cause, t_ns) -> TransferId`。`src`/`dst` は口の id=`(部門, 索引)`(索引は整数か配列・行数を揃える)。外界・銀行・政府も部門の口=湧かせない。`amount` は正の整数の円。`what` は 1-3 の語彙の族「金」の語(`金:消費支出` など 15 語=科目)。`cause` は 1-3 の原因(`LlmCall`・`Process`・実験の条件)か `None`。`t_ns` は通しの時刻(刻みの頭)。戻りは生ログの通し番号の範囲 `TransferId(first, n)`。
- 約束(TigerBeetle の形): (1) 1 行は 2 脚(同じ額)。`預金純増` は四重記入の 2 脚目(預金と銀行の借入)も書く。`減価償却` は自己ループ(固定資産だけ・`src == dst`)。(2) 前提が崩れていたら例外=口が先に検査する: 語彙の外の `what`・退蔵項・許されない組(`is_allowed`)・参入資本の出所(ex nihilo)・範囲の外の索引・0 以下の額・刻みの頭でない時刻・世帯の現金が書き込み窓の外(`np.add.at` が `writeable=False` を無視する穴を自前で塞ぐ=旧 `_apply_cash` と同じ)。(3) 生ログ(輪)へ追記・溢れたら古い行を上書きして数える。(4) 原因つきの行は出来事を 1 行ずつ書いて id を目印の列へ。(5) 計器。
- 業務の失敗(残高不足・組・額)は口が行ごとの状態で返す(今まで通り)。`transfer` は通った行だけを受け取る。
- **層の契約**: economy は `engine.events` を import しない(`pyproject` の forbidden「economy → llm」: 語彙表 `engine.events.vocab` が `llm.contract` を読む=初版で import して `lint-imports` が落ちたので直した)。出来事を書く口 `MoneyEventLink` は engine の側(build)が作って台帳に挿す。金の語の族の名「金」と原因の種類の名は economy に写しで持ち、試験が 1-3 の表と突き合わせる。`lint-imports` は 5 契約とも守られている。
- 逐次ループ宣言: 原因を渡した行の数ぶんのループ(出来事を 1 行ずつ=`EventLog.append` が 1 行の口)。ほかはベクトル演算。`tests/engine/test_two_phase.py` の hot path に `economy/ops.py` を足した(個体数ぶんのループ無し・宣言あり)。

## 3. 帳簿の 9 口の載せ替え

10b-prep §3-2 の E1〜E9(「帳簿 9 口」の出どころ)。

| # | 口 | 呼び手 | 金を動かすか | 載せ替え | 原因(1-9) |
|---|---|---|---|---|---|
| E1 | `Ledger.purchase_many` | resolve `_complete_buy`・`_complete_eat` | 世帯 → 店舗(消費支出) | `transfer_many` → `ops.transfer` | なし(呼の id が適用に届かない=仮採用 5) |
| E2 | `Ledger.transfer_many`(と 1 件の `Ledger.transfer`) | `rail.pay_fares`(運賃)・`goods.restock_many`(代金)・anchors/pricing の口 | 任意の組 | 検査の後 `ops.transfer` | 運賃=`Process("rail")` |
| E3 | `Ledger.endow_households` | resolve `initialize` | 外界 → 世帯(来街者持込) | `transfer_many` → `ops.transfer` | なし(組み立て・出来事の記録がまだ無い) |
| E4 | `Ledger.endow_stores` | `cli.build_ledger_bundle` | 外界ほか → 店舗(参入資本) | `transfer_many` → `ops.transfer` | なし(同上) |
| E5 | `GoodsLedger.restock_many`(金の脚) | resolve `restock` ← 過程 shelf | 店舗 → 外界(域外仕入) | 代金は E2 → `ops.transfer`・物の行に代金の行の id | `Process("shelf")` |
| E6 | `GoodsLedger.sell_many` | resolve `_complete_buy` | 動かさない(物だけ) | 物の行に目印の列(空) | — |
| E7 | `GoodsLedger.to_bin_many` | 過程 waste | 動かさない | 同上 | — |
| E8 | `GoodsLedger.collect_waste` | 過程 waste | 動かさない | 同上 | — |
| E9 | `GoodsLedger.consume_many` | 過程(世帯の消費) | 動かさない(行も書かない) | — | — |
| (付) | `Ledger.depreciate` | engine からは呼ばれていない | 自己ループ(固定資産) | `ops.transfer`(自己ループ) | 渡せる(既定 None) |

- 値は不変: HEAD の `ledger.py`・`goods.py` の写しと、乱数で作った口の呼び出しの列(24 本 × 160 回・不正な行・残高不足・小さな輪の溢れ・締め・預金の 2 脚・減価償却・評価替え・物の口と代金・書けない世帯の現金)で毎回の戻り値と全部の状態(残高・流れ・締め・生ログの中身と位置・計数・`state_hash`・物の在庫と納品ログ)が同じ(`test_cp2_nine_ops_equivalence.py`)。5,000 体 mock の 1 日(既定 v3)を HEAD の台帳と今の台帳で回して final・呼数・残高・生ログ・物の台帳が同じ(`slow`・輪の係数 6.5 と 3.0 の 2 通り)。
- E6〜E9 は金を動かさない(物=CP1 の A のうち物)ので `transfer`(金)には載せていない。物の基本操作の段で載せ替える(§11 の仮採用 4・親に確かめてほしい点 3)。

## 4. AST の検査の範囲と別名の表

- お金の列(`economy.ops.MONEY_PATHS`): `agents.money`(世帯の現金=帳簿の世帯の現金の行と同じ配列)・`pois.revenue`(店の売上の写し・診断)・`ledger.money._lines`(帳簿の残高)・`ledger.money._flow`(流れの表)・`ledger.money._last_change_day`・`ledger.money._raw_*`(生ログの 9 列と位置)。
- 書きの形(道具 `tests/economy/cp2/money_writers.py`): 添字への代入と `+=`(添字の鎖の根)・`np.<ufunc>.at`・`fill` など中身を書くメソッド・`np.copyto/put/place/putmask`・`out=`・`field("money")`・台帳の中の名の差し替え。局所の別名(代入・添字・ビュー・`np.asarray`・`for`・`enumerate`・`.items()` を通す)。書きは一番外の関数に帰属。
- src の全部で見つかった書き手: `economy/ops.py` の `transfer`(帳簿の全部の列=正の対照)と、凍結の表 `money_writers_frozen.json` の 8 関数だけ。

| 置き場 | 関数 | 列 | 種類 | 理由 |
|---|---|---|---|---|
| economy/ledger.py | `Ledger.__init__` | 全部の配列 | 組み立て | 配列を作る(0 と -1) |
| economy/ledger.py | `Ledger.attach_household_cash` | `_lines` | 組み立て | 世帯の現金の行に `agents.money` を採用 |
| economy/ledger.py | `Ledger.on_day_end` | `_flow`・`_raw_head` | 締め | 流れの表を畳んで 0・保持窓の先頭 |
| economy/ledger.py | `Ledger.revalue_inventory` | `_lines` | 評価替え | 在庫の評価額(金は動かない・engine から呼ばれない) |
| engine/resolve.py | `initialize` | `money` | 段階 2 | 台帳の経路は 0 にしてから transfer・台帳の無い経路(C2)は直に書く |
| engine/resolve.py | `_board_riders` | `money` | 段階 2 | 台帳の無い経路(C2)の運賃 |
| engine/resolve.py | `_complete_buy` | `money`・`revenue` | 段階 2 | C2 の購入の現金と売上の写し(両方の経路) |
| engine/resolve.py | `_complete_eat` | `money`・`revenue` | 段階 2 | 同上(食事) |

- 試験: 表の外の書き 0・表の行は実際の書きと同じ(減るだけ)・`ops.transfer` を呼ぶのは `Ledger.transfer`/`transfer_many`/`depreciate` だけ・負の対照 5 本。
- 別名の表の差(1-0 の `engine/systems/allow.py` の `ALIAS_WRITES`): **前** `_complete_buy`・`_complete_eat`・`_board_riders`・`initialize`(どれも `_apply_cash` 経由の `agents.money`)と `apply_detection` の 5 行 → **後** `apply_detection` の 1 行。消した 4 行の代わりに、帳簿の口の名の表 `TRANSFER_PORTS_HOUSEHOLD`(`purchase_many`・`endow_households`・`pay_fares`)を呼ぶ resolve の関数が `TRANSFER_WRITES = ("agents.money",)` を書く規則 1 つ(AST で引く・引いた関数=前の 4 行と同じ 4 つ)。系の `writes.soa`(`tests/engine/systems/writes_soa_frozen.json`)は変わらない。
- 発注の `tests/engine/systems/alias_writes.json` は無い。1-0 の別名の JSON は記録 `run-day-decomp/alias_writes.json`(試作の出力)で、実行時の表は `allow.py` の `ALIAS_WRITES`。記録の JSON は 1-0 の記録として変えていない(親に確かめてほしい点 4)。

## 5. K17 の数([k17_numbers.json](k17_numbers.json))

| 量 | HEAD(3.0) | 1-9(6.5) |
|---|---|---|
| 係数(行/体/日) | 3.0 | 6.5(実測 4.07 × 1.5 = 6.105 以上) |
| 容量 5,000 体 | 16,384 行(下限) | 32,500 行 |
| 容量 390,067 体 | 1,170,201 行 | 2,535,436 行(⌈6.5 × N⌉) |
| 輪 7 列のバイト 5,000 体 / 390,067 体 | 393,216 B / 28,084,824 B | 780,000 B / 60,850,464 B |
| 目印の列(12 B/行)5,000 体 / 390,067 体 | — | 390,000 B / 30,425,232 B |
| 物の目印の列 390,067 体 | — | 9,361,608 B(納品ログの容量 780,134 行 × 12 B) |
| 宣言の係数 `transfer_log` | 72 B/体/日 | 156 B/体/日 |
| 宣言の投影 390,067 体(`transfer_log`・`transfer_log_event_ids`) | 28,084,824 B | 60,850,452 B(cap より 12 B 小さい)・30,425,226 B |
| `declared_over_cap` | なし | なし(4 通りとも・成長の門は通る) |

- 39 万体の金と物の輪の合計(7 列+目印の列): HEAD 40.6 MB(金 28.1+物 12.5)→ 1-9 113.1 MB(金 60.9+金の目印 30.4+物 12.5+物の目印 9.4)= +72.6 MB。M8(24 GB)の 0.47%。設計書 `v2-budget-declaration.md` の行(72 B/体/日・28.1 MB)の更新は親。
- 溢れ: byte-check の 19 構成(5,000 体・1 日)で **0 件**。1 日の行は 11,375〜20,183(2.28〜4.04 行/体/日・最大は `v3_mem_rel`)。HEAD の係数 3.0 では 5 構成(v3 の既定・記憶+店・記憶+関係・古典・古典+記憶+関係)で 1,827〜3,799 行が溢れていた(`byte_check_cp2_rate3.json` の `economy.raw_overflow`=溢れても続けて final と全部の欄が HEAD と同じ)。
- 溢れの扱い: 古い行を上書きして続け、上書きで失った行の数を `meter.overflow`(manifest `economy.raw_overflow`・日次 `economy.overflow`)に数える。保持窓で落とした行は溢れに数えない(`n_raw_dropped` は今まで通り両方の和)。先例は ftrace の overrun(上書きで失った数)。
- `raw_capacity_for` は「1 日ぶんを切り上げて × 日数」(6.5 × 奇数の N が整数でないため。日数に比例=既存の試験の形)。係数 3.0 では前と同じ値。

## 6. 目印の列と出来事

- 金の生ログ: 行ごとに `(t_ns, seq)` の 2 列(出来事の無い行は -1・輪の使い回しで前の行の id を残さない)。`Ledger.raw_event_ids()` は `raw_rows()` と同じ並び。物の納品ログも同じ 2 列(`delivery_event_ids()`)。
- 出来事の中身: `what=金:<科目>`・`how_much=額`・`who`=払い手・`whom`=受け手(世帯は体の id・ほかは `部門:索引`=`外界:0`・`店舗:12`)・`where`=店の側の POI(無ければ空)・`cause`・`t_ns`=刻みの頭(台帳の刻みの幅は build が渡す)。
- 1 対 1(`test_cp2_event_links.py`): 単体(原因つきの行だけ・欄の中身・刻みの幅・記録 off・原因なし・輪の上書き・補充の物の行=代金の行の id)と、世界資産 200 体の 1 日(目印のある行=記録の金の行・id の集合が同じ・欄が行と合う・原因は rail か shelf・計器の数と日次の分布が合う・補充の物の行の目印=代金の行)。
- 配線した系: phase_c(運賃=過程 rail)・world(補充の代金=過程 shelf)。day_close・close_final は計器の締め(出来事は書かない=1-3 の日の締めの行のまま)。5,000 体の既定 v3 で 1 日の出来事の行は 28,835 → 32,158(金の行 3,323=運賃と補充の代金)。

## 7. 1 日の締めの検算

- `Ledger.on_day_end` が流れの表を畳む前に `TransferMeter.close_day(day, Σ流れの表)` を呼ぶ: `flow_sum_ok = (Σ流れの表 == 起点+その日の transfer の額の和)`。起点はその日の最初の transfer のときの流れの表の和(新しい台帳=0・日の途中から再開した台帳=戻した流れの表の和)。計器だけ(締めは止めない)。
- 試験(`test_cp2_flow_sum.py`): 預金の 2 脚・減価償却・参入資本を含む 3 日で成り立つ・既存の四重記入の検算(`checks.flow_matrix_balanced`・日次センサスの `flow_ok`)も通る・transfer の外で流れの表を書くと落ちる(負の対照)・再開した台帳・合成の世界の 2 日で毎日成り立ち、生ログの日の行の額の和とも合う。byte-check の 19 構成でも `flow_sum_ok` はどれも真。

## 8. 結果不変の確かめ

| 確かめ | やり方 | 結果 |
|---|---|---|
| byte-check([byte_check_cp2.json](byte_check_cp2.json)) | `tools/byte_check_cp2.py`(10e の 19 構成・5,000 体・seed 1・1 日・テープつき・+11 欄)。HEAD は本体 HEAD `136fdbb` の src の写し、cp2 は作業木の src(既定=係数 6.5・出来事の記録 on) | **final は 19/19 で同じ**。動いた欄: 全構成で `money_core` の `raw_capacity`(16,384 → 32,500)だけ(取引の件数・却下の計数は同じ)。HEAD で輪が溢れていた 5 構成だけ生ログの行数・その sha・落ちた行の数・**`full_last` と `end_of_day`(full-hash)**。帳簿の残高・世帯の現金・流れの集約行・`state_hash`・物の台帳・**生ログの末尾 16,384 行**・呼数・テープの列・行動の件数・behavior-hash は 19/19 で同じ |
| 係数を戻した byte-check([byte_check_cp2_rate3.json](byte_check_cp2_rate3.json)) | 同じ道具で作業木の src を `--rate 3.0`(HEAD の係数)で回した | **19/19 構成で 36 欄が全部同じ**(10e の 25 欄+帳簿の 11 欄)。載せ替えそのものは full-hash も含めて不変 |
| 2 日のラン([two_day_cp2.json](two_day_cp2.json)) | `10e/two_day_check_act.py one`・5,000 体・2 日・既定 v3・作業木の src | final `912446bd2b42b6ab`・140,913 呼・テープの calls `cb330e76b4b8a573`・blocks `7f09f3dc78d84ac4`(1-0・T0・1-3 の記録の HEAD の値と同じ) |
| 帳簿の残高と台帳の行 | byte-check の 11 欄と `test_cp2_nine_ops_equivalence.py`(乱数の列 24+6 本・5,000 体 mock の 1 日 × 2 通り) | 同じ(上) |
| 再開 | 既存の `tests/engine/test_resume_10d.py`(全部) | 通った(行 A は discardable=状態のファイルにも full-hash にも入らない) |

- **full-hash が動く理由**: 状態台帳の O92(`_raw_head`・`n_raw_dropped`=軸 2 required)と O77(`_last_close` の `raw_rows_kept`)は full-hash に入る。輪を広げると溢れが無くなり、この 3 つの値が変わる(例 `w6_v3_default`: 落ちた行 3,671 → 0・保持窓の行 16,384 → 20,055)。behavior-hash(=既定の final)は軸 1 で選ぶので動かない。口の約束の「final は不変(輪は診断=軸 1 diag)」のとおりだが、「全欄が同じ」には full-hash が入らない=親に確かめてほしい点 1。
- 系ごとの指紋(1-3 の `probe_e13.py`)と manifest の 7 本の比べ(10f)は回していない(§11)。

## 9. 試験

新しい試験 `tests/economy/cp2/`(80 本=76 本+`slow` 4 本・76 本で 約 90 秒(ほかの作業木のランと同時)・data が要るのは 6 本=`slow` 4 本を含む・`slow` 4 本は 108 秒で通った):

- `test_cp2_transfer_only_writer.py`(12): お金の列の書き手(表の外 0・表の行は実際の書きと同じ・正の対照・宣言・`ops.transfer` の呼び手は Ledger の 3 つ・`_apply_cash`/`_record` は無い)・別名の表の 4 行が消えて規則で引ける・口の名の表が economy の口と合う・負の対照 5 本。
- `test_cp2_nine_ops_equivalence.py`(32+slow 2): HEAD の写しの blob の名・乱数の口の列 24 本・出来事 on で同じ 6 本・溢れる輪・(slow)5,000 体 mock の 1 日 × 係数 6.5/3.0。
- `test_cp2_k17_capacity_and_overflow.py`(15+slow 2): 係数・容量の式 7 通り・宣言と cap 3 通り・溢れを数えて続ける(単体と 64 行の輪のラン=manifest と日次の記録・final は同じ)・既定で溢れ 0・台帳の無いランは空・(slow)世界資産 300 体の 19 構成と 5,000 体の既定で溢れ 0。
- `test_cp2_event_links.py`(9): 1 対 1・店の側・刻みの幅・原因なしと記録 off・輪の上書き・補充・economy の写しが 1-3 の表と同じ・economy と ledger_api が engine.events を読まない・(data)世界資産 200 体のラン。
- `test_cp2_flow_sum.py`(4)・`test_cp2_writes_declared.py`(4: 宣言・段 B の正と負の対照・(data)phase_c から `E:events.*` を外すと運賃で `PermissionError`)。

既存の試験(1-9 に関わるもの): `tests/economy`(cp2 を含む)・`tests/engine/test_two_phase.py`・`test_state_ledger_10b.py`・`test_ledger_wiring.py`・`tests/engine/systems`・`tests/engine/events`・`tests/engine/time`・`test_mock_day_w2.py`・`test_resume_10d.py` は 607 本が通った(途中の版・4 並列 9 分)。`lint-imports` は 5 契約とも守られている(190 ファイル)。秘密の走査(`tools/scan_secrets.py`・変えたファイルと新しいファイル 43 本)は CLEAN。

### 9-1. 全体の試験

`-m "not gpu and not slow" -n 4 --dist loadfile`(data あり・作業木):

- 1 回目: 4,170 passed・6 failed・1 xfailed(49 分 31 秒・ほかの作業木の試験と同時)。落ちた 6 件のうち 5 件は 1-9 の直し漏れ: 10f の外の状態の軸 1 の AST 3 件(`transfer` が台帳の診断の属性を持ち主のファイルの外で読む → `DIAG_EXITS` に 2 行=仮採用 12)・10f の manifest 2 件(末尾の欄の並びの試験=`economy` を `weather` の後に置いていた → `fleet` の後へ移した・設定の節の golden の更新)。
- 直した後に落ちたファイルと関わる試験(10f の 2 ファイル・`tests/engine/time`・1-3 の manifest・cp2)を回して 169 passed。
- 2 回目(最終): **4,175 passed・1 failed・1 xfailed(28 分 59 秒)**。落ちた 1 件は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(テープの道筋が `data/tape/` で始まらない)=作業木の `data` が本体への junction であることで起きる既知の落ち(1-0・T0・1-3 の記録と同じ・本体では通る)。

## 10. 触った共有ファイルの一覧(親の rebase 用)

- `src/shibuya/engine/systems/table.py`: world・phase_c・day_close・close_final の `writes.paths` の末尾に `A:ledger.*`(phase_c は `E:events.*` も)と docstring の 1 段落。
- `src/shibuya/engine/state_ledger.py`: 行 `A` を行 `E` の後に・`EXCLUDED` の `ledger.money` に 2 行・docstring の行の数(189)。
- 〔検収 L4〕`src/shibuya/engine/events/links.py`(`MoneyEventLink` を末尾に)・`src/shibuya/engine/ledger_api.py`(Protocol の口に `cause`・`MoneyLedger` から `unlocked` を外した・`LedgerBundle` に 3 つ)・`src/shibuya/engine/processes/rail.py`(`FARE_CAUSE`・`pay_fares` の `cause`)・`src/shibuya/engine/processes/goods_flow.py`(`RESTOCK_CAUSE`)・`src/shibuya/engine/resolve.py`(`restock` の `cause`・docstring)。
- 凍結の表: `tests/engine/time/manifest_keys_frozen.json`(〔rebase の後〕`economy` を末尾=1-4 の欄の後に)・`tests/engine/events/writes_paths_events.json`(`phase_c` を `world` の後に)。
- 状態台帳の行の数の試験 `tests/engine/test_state_ledger_10b.py`(外の状態 97 → 98・全体 188 → 189・鍵の末尾 `E`・`A`)。
- `src/shibuya/engine/run.py`(manifest の `economy` を末尾に・`economy_fields`)・`src/shibuya/engine/systems/state_io.py`(日次の記録の `economy` を `events` の前に)・`src/shibuya/engine/manifest_sections.py`(`economy` の節を末尾に)・`src/shibuya/engine/systems/build.py`(出来事の記録を作った後の 2 行)・`src/shibuya/engine/systems/allow.py`・`src/shibuya/engine/state_ledger_ast.py`(`DIAG_EXITS` の末尾に 2 行)。
- 10f の golden `tests/engine/test_env_and_sections_10f.py` の `CONFIG_PATHS_SHA256`(設定の節に `economy` の 5 つ=前の値を注に残した)。
- `cli.py` は触っていない。
- 発注の「編集してよい」一覧の外の既存の試験: `tests/economy/test_ledger.py`(K17 で 3.0 × N の整数を前提にした 2 か所=切り上げ)・`tests/engine/test_ledger_wiring.py`(39 万体の cap の数を 6.5 の値に・目印の列の cap を足した)・`tests/economy/test_single_write_path.py`(残高の配列に触れてよい置き場に ops.py)・`tests/engine/systems/test_stage_a_guard.py`(別名の表の 4 行が消えたことを確かめる形に)・`tests/engine/test_two_phase.py`(hot path に ops.py=発注どおり)。どれも発注の決定(K17・`_apply_cash` の別名を消す・transfer を ops.py に)から必ず動く所だけ。〔検収 M2〕台帳の窓を内部の名 `_unlocked` にしたので、窓を意図して開ける既存の試験 4 ファイル(`test_ledger.py`・`test_goods.py`・`test_single_write_path.py`・`test_t3_redundant_equation.py`=検算が残高の直の書きを捕まえる試験)の `led.unlocked()` を `led._unlocked()` に直した(8 か所)。

## 11. 限界・空欄・仮採用・親に確かめてほしい点

- **仮採用(10-13b §0-3)**: 既定の final は動かない(§8)。戻すときは記録の物と試験を直すだけ。
  1. `transfer` の口の形: `src`/`dst` は `(部門, 索引)`(索引は配列可)・戻りは生ログの通し番号の範囲 `TransferId(first, n)`。
  2. お金の列の範囲(`MONEY_PATHS` の 6 道筋)と「書き」の形(§4)。`transfer` の外の書き手 8 関数を凍結の表で宣言(減るだけ)。
  3. 別名の表の 4 行の代わりに、帳簿の口の名から引く規則(engine は economy を import できないので口の名を engine 側に持つ)。
  4. 物だけの口(E6〜E9)は `transfer`(金)に載せない(物の行に空の目印の列)。補充(E5)の物の行には代金の行の id を写す。
  5. 原因: 運賃=`Process("rail")`・補充の代金=`Process("shelf")`。購入・食事(E1)・初期の財布(E3)・参入資本(E4)は原因なし=出来事を書かず目印は空・数を計器 `transfers_uncaused` に。理由: 購入の呼の id(`call_id`)は適用の口(`IntentBatch`)に届かない(1-8 の配線)・1-3 の検収 M2(`LlmCall` を配線する前に原因の表を列にする)・組み立ての「境界」の名は語彙表に無い(足すのは語彙の版上げ=1-3 の凍結の試験が変わる)。5,000 体の既定 v3 で原因つきの行は 3,323/20,055(16.6%)。
  6. K17 の係数は実測 1 本(10b-prep の 5,000 体 1 日)から決めた 6.5(expedient)。容量は 1 日ぶんを切り上げて × 日数。
  7. 目印の列は別の成長の宣言 2 本(`transfer_log_event_ids`・`delivery_log_event_ids`)にした(輪の 7 列の 24 B/行の宣言は係数だけ変えた)。ランの成長の報告の行が 2 本増える(manifest には出ない)。
  8. 状態台帳の行の鍵を `A`(CP1 の A=湧かないもの=お金・系の宣言 `A:ledger.*`・〔検収 L3〕前は `C`=1-5 の権利と取り違えるので改めた)にし、版は上げない(行 `E` と同じ理由=どちらのハッシュにも状態のファイルにも入らない)。
  9. manifest の一番上に `economy`(〔rebase の後・親の指示〕末尾=T0 の TM9 → 1-4 の 3 欄 → 1-9。前は `fleet` の後に置いていた)・日次の記録の `economy` は `events` の前(「`events` が末尾」の試験を保つ)。
  10. 計器は discardable=再開したランは 0 から数える(1-3 の L6 と同じ)。締めの検算の起点はその日の最初の transfer で決める(日の途中から再開しても成り立つ)。
  11. 出来事を書く口 `MoneyEventLink` を engine 側に置き、economy は語の族の名と原因の種類の名を写しで持つ(層の契約)。
  12. 10f の外の状態の軸 1 の AST で、`transfer` が台帳の診断の属性(流れの表・生ログの位置・計器)を持ち主のファイルの外で読む所は「診断の出口」に足して許した(`DIAG_EXITS`)。持ち主の範囲を ops.py まで広げる形は取らなかった(検査の道具を変える方が大きい)。
- **親に確かめてほしい点**:
  1. **K17 で full-hash が動く**(§8): O92(`_raw_head`・`n_raw_dropped`)と O77(`_last_close.raw_rows_kept`)が軸 2 required のため、HEAD で輪が溢れていた 5 構成で `full_last`・`end_of_day` の full が HEAD と違う(behavior-hash=final は同じ・係数 3.0 に戻すと 36 欄とも同じ)。前の版の状態のファイルから再開すると、戻した位置(`_raw_pos`・`_raw_head`)と新しい容量は矛盾しない(位置は通し番号・保持窓の行数 ≤ 容量)が、full-hash は同じ値にならない。受け入れるか(K17 の決定の結果として記録)、O92 の位置を discardable に分けるかの判断。
  2. 原因の無い金の行(購入・食事・財布・参入資本)を残した(仮採用 5)。1-8 の `call_id` の配線のときに `purchase_many` へ `LlmCall` を渡す形でよいか。境界(組み立て)の原因の名を語彙に足すか。
  3. 「帳簿 9 口(`economy/ledger.py` の口)」を 10b-prep の E1〜E9 と読んだ。E6〜E9 は物の口なので金の `transfer` には載らない(仮採用 4)。発注の「9 口の全部をこの 1 つに」と違う読みなら指示がほしい。
  4. 発注の `tests/engine/systems/alias_writes.json` は無かった。実行時の表 `allow.py` の `ALIAS_WRITES` から行を消した。1-0 の記録の JSON(`run-day-decomp/alias_writes.json`)は変えていない。
  5. `pois.revenue`(店の売上の写し)と台帳の無い経路(C2)の `agents.money` は resolve に残した(凍結の表の「段階 2」)。engine は economy を import できず、台帳の経路の売上の写しは物の脚(販売)の後に足すので、`transfer` の中へ移すと「払った後に物が出なかった行」で値が変わりうる。段階 2(行動の適用)で決める。
  6. manifest の観測の値が増える・変わる: 日次の記録の `events`(金の行の分だけ行数が増える=例 28,835 → 32,158)・成長の報告の行 2 本。既存の欄の名と順は変えていない。
- **限界(検収 L7・L9)**: (L7)CP1 の「A〜D は基本操作からしか書けない」のうち、検査は金だけ(発注どおり)。物の「移す」(E6〜E9 と E5 の物の脚)と消費は **CP2 の段階 1(帳簿 9 口)の残り**(段階 2 の行動の適用ではない)=PENDING に段階 1 の残りとして残す。(L9)1-3 の出来事の id `(t_ns, seq)` は刻みの中の書いた順なので、金の出来事が同じ刻みの seq を先に使うと、同じ刻みの ActualLog の行の目印(出来事の id)の値が HEAD とずれる(中身・行数・final は同じ)。系ごとの指紋は ActualLog の目印の列を外して比べる。書き手をまたいで id を安定させるかは 1-3 の id の作り方の問題(親が決める)。
- **回していないもの**: manifest の 7 本の比べ(10f)・39 万体の実測(容量は式だけ)。系ごとの指紋と独立検収は検収役が回した(review.md)。
- **用語集**: 新しい語は「基本操作」「目印」「溢れ」(口の約束と回答の語)。用語集との照合はしていない(親の検収で)。

## 12. 独立検収(review.md)の直し(第334・2026-10-14・親の判断で)

- **M1(中・宣言つきの直し)**: 汎用の口(`Ledger.transfer`・`transfer_many`)に科目「減価償却」を渡すと、HEAD は現金の脚で動かしていた(別の口なら現金が移り、同じ口なら差し引き 0 で取引の件数だけ増える=減価償却は「現金を動かさない」に反する潜在の欠陥)。1-9 の初版は別の口で `ValueError`・同じ口で固定資産が減った。直し: `_validate_pair` が減価償却を **行の状態 `FORBIDDEN_PAIR`** で返す(例外にしない・状態は却下の計数だけ)。自己ループの入口は `depreciate` だけ(`ops.transfer` の自己ループの道は `depreciate` からしか来ない)。engine からの呼び手は無い=到達しない入力。試験: 決定的な 3 本(検収役の seed 5012・5030・5098 で落ちた形=店 0 → 店 1・店 2 → 店 2 のベクトルの口・店 0 → 店 0 の 1 件の口。HEAD の写しの値と 1-9 の値を両方固定・`depreciate` は HEAD と同じ)。乱数の列は汎用の口に減価償却を渡さない形にし(この入力だけ HEAD と値が違うため)、seed 5012・5030・5098 も列に足した(`test_cp2_nine_ops_equivalence.py`)。
- **M2(中)**: 公開の `Ledger.unlocked()`+`balance()` で transfer の外から残高を書けた。直し: 窓を内部の名 `Ledger._unlocked` にし(公開の `unlocked` は無い・`MoneyLedger` の口からも外した)、**src の全部で窓の名(`_unlocked`・旧 `unlocked`)の参照と `self` 以外の受け手の `_open` は `economy/ops.py` の `transfer` の中だけ**を AST で縛った(呼び出し・別名・属性の鎖・`getattr` などの名前の文字列=`tests/economy/cp2/test_cp2_write_window.py`)。書き手の AST に名前の文字列で書く形(`setattr`・`object.__setattr__`・`vars(X)[...]`・`X.__dict__[...]`)を足した。負の対照: 窓+`balance` の書き(新旧の名・別名・属性の鎖・`getattr`・外からの `_open`・ops.py の transfer の外)と `setattr` ほか 4 形。試験(tests/)は窓を開けてよい(検算が残高の直の書きを捕まえる試験のため)。
- **L1**: `economy/goods.py` の docstring の「expedient(本モジュール分)」の項に足した 1-9 の説明を、冒頭の段落へ移した(1-4 のつなぎの台帳の走査が項の数を数える)。
- **L2**: `test_nineteen_configs_do_not_overflow` を `test_nineteen_configs_stay_under_the_coefficient` に改めた: 19 構成を引数にし、構成ごとに **5,000 体**で「行/体/日 < 6.5」「溢れ 0」「行 ≤ 容量 32,500」。300 体では店の参入資本の行(POI ごと 2,337 行)が行/体/日を押し上げ(10.85)、輪の下限 16,384 行が受け持つので、係数の確かめは 5,000 体で行う(`slow`・1 構成 約 40〜60 秒)。
- **L3**: 状態台帳の行の鍵 `C` → **`A`**(CP1 の A=湧かないもの=お金)・系の宣言 `A:ledger.*`・注を直した。
- **L4**: §10 の共有ファイルの一覧に 5 本を足した。
- **L5**: `ops.transfer` の順を「検査(世帯の現金の窓を含む)→ 出来事を書く → 金を書く(残高・流れの表・輪と目印の列)」にした。記録の口が例外を出したとき、金だけが動いた状態と輪の古い目印は残らない。
- **L6**: `TRANSFER_PORTS_HOUSEHOLD` を `MappingProxyType` に(限界=名前のある 3 つの口だけを見る・注に書いた)。
- **L7・L9**: §11 の限界に書いた。**L8**(1-4 のつなぎの台帳の行=運賃の原因・原因の無い金の行・K17 の係数)は rebase の後に足した(§12-2)。
- 結果: §12-1。

### 12-1. 直しの後の試験と byte-check

- 指定の範囲 `tests/economy tests/engine/test_ledger_wiring.py tests/engine/systems tests/engine/events tests/engine/time tests/engine/test_two_phase.py tests/engine/test_state_ledger_10b.py tests/engine/test_env_and_sections_10f.py`(`-m "not gpu and not slow" -n 4 --dist loadfile`): **596 passed**(3 分)。
- cp2 の `slow` 22 本(19 構成 × 5,000 体の係数の確かめ・5,000 体 mock の HEAD との同値 × 2・5,000 体の既定): **22 passed**(4 並列 3 分 5 秒)。cp2 は 109 本(87 本+`slow` 22 本)。
- `lint-imports`: 5 契約とも守られている。秘密の走査(変えたファイルと新しいファイル)は CLEAN。
- byte-check 4 構成([byte_check_cp2_fix_4cfg.json](byte_check_cp2_fix_4cfg.json)・HEAD `136fdbb` の src の写し vs 作業木の src・w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel): **final は 4/4 で同じ**。帳簿の残高・世帯の現金・流れの集約行・`state_hash`・物の台帳・生ログの末尾 16,384 行・呼数・テープの列も 4/4 で同じ。動いた欄は K17 の分だけ(4 構成とも `money_core` の容量 16,384 → 32,500=取引の件数と却下の計数は同じ・HEAD で輪が溢れていた w6_v3_default と v3_mem_rel だけ`full_last`・`end_of_day`・生ログの行数とその sha・落ちた行の数)=直しの前の 19 構成の結果と同じ形。溢れは 4 構成とも 0。

### 12-2. 本体(1-4・1-6 取り込み済み `9dd7dde`)への rebase の衝突の解き方と L8(第334・2026-10-14)

衝突 5 本は両方の追加を残した(git の操作=`add`・`rebase --continue` は親)。

| ファイル | 解き方 |
|---|---|
| `src/shibuya/engine/state_ledger.py` | docstring の行の数を 191(1-3 の `E`・1-6 の `M0`・`M0R`・1-9 の `A`)。行は 1-6 の `M0`・`M0R` の後に 1-9 の `A` |
| `src/shibuya/engine/systems/table.py` | docstring の段落を両方(1-6 の記憶の器・1-9 の金)。宣言(`M0*:…`・`M0R:…`・`A:ledger.*`・`E:events.*`)は自動で合わさっていた |
| `tests/engine/test_state_ledger_10b.py` | 外の状態 100 行・全体 191 行(1-6 の +2 と 1-9 の +1)・鍵の末尾 `E`・`M0`・`M0R`・`A`・注を両方 |
| `tests/engine/time/manifest_keys_frozen.json` | 鍵は本体の 111 個+末尾に `economy`=112 個(T0 の TM9 → 1-4 の `rules_version`・`run_kind`・`bridges_version` → 1-9 の `economy`)・注を両方 |
| `tests/engine/test_env_and_sections_10f.py` | 注を両方・`CONFIG_PATHS_SHA256` を再計算 `1b0edc6d…3dbf9d09`(`economy` の設定の 5 道筋を外すと 1-4 の値 `d8a9a21d…d629dcd6c4b8` に戻ることを確かめた=増えたのは 1-9 の分だけ) |

- manifest の `economy` を末尾へ移した(親の指示の並び)ので、末尾の並びを固定する試験を 1-9 の分だけ直した: `tests/engine/time/test_t0_tm9_fields.py`(TM9 の後ろ=1-4 の 3 欄+`economy`)・`tests/engine/test_env_and_sections_10f.py`(末尾の組に `C19_KEYS = ("economy",)`)・`tests/engine/bridging/test_manifest_rules_bridges.py`(一番上の鍵=1-4 の 3 欄は末尾の 1 つ前まで・最後が `economy`/日次の記録の末尾=`bridges_count`・`rules_version`・`economy`・`events`)。
- **L8**: `docs/design/bridging-ledger.json` に文書の行を 3 つ足した(274 → 277 行。欄は `id`・`what`・`why`・`remove_at`・`declared_in`・`conf`・`since`・`status`・`remove_basis` だけ=`code_at`/`rule_id` は書かない・`declared_in` は本書・`conf` expedient・`remove_basis` inferred):
  - `DOC-money-fare-cause-rail`(運賃の原因=過程 rail・外す段 1-8)
  - `DOC-money-uncaused-rows`(原因の無い金の行=購入・食事・初期の財布・参入資本・外す段 1-8)
  - `DOC-k17-raw-ring-coefficient`(K17 の係数 6.5 行/体/日・外す段 7=主張の前の感度試験)
- 1-4 の見出しの項の数の試験(`tests/engine/bridging`)は台帳の行を足す前から通った(`goods.py` の 1-9 の説明は L1 で項の外へ移してある・`ledger.py` は既存の項の続きの行=項の数は同じ)。
- 試験(指定の範囲 `tests/engine/systems tests/engine/time tests/engine/events tests/engine/memory tests/engine/bridging tests/economy tests/engine/test_state_ledger_10b.py tests/engine/test_env_and_sections_10f.py tests/engine/test_state_checks_10f.py`・`-n 4`): **681 passed**(4 分 52 秒)。`tests/engine/test_two_phase.py`・`test_ledger_wiring.py`: 31 passed。`lint-imports` 5 契約とも守られている。byte-check は親。

## 13. 親の検収(第334・2026-10-14)

- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src): final が同じ 4/4。動いた欄は HEAD で輪が溢れていた v3 の 2 構成(w6_v3_default・v3_mem_rel)の end_of_day と full_last だけ=K17 で輪を 3.0 → 6.5 行/体/日に広げ、落ちていた行が残るようになった意図した効果(O92/O77 が軸 2 required のため full-hash に入る)。w6_v3_activity_off と w6_v1_default は 25 欄とも同じ(parent_head_vs_cp2_4cfg.json)。
- 親の判断: K17 の効果として受け入れる(final・帳簿の残高・金と物の台帳の行は不変=口の約束 1-9 の約束 (1) は満たす)。O92/O77 の軸は変えない(輪の中身を正直に full-hash に入れておく)。予算宣言(v2-budget-declaration.md)の輪の数は親が改訂。独立検収(review.md)=条件つき受入 → M1(汎用の口の減価償却=FORBIDDEN_PAIR の行の状態・宣言つきの直し)と M2(台帳の窓を _unlocked に・AST で呼び手を ops.transfer の中だけに・負の対照 2 系統)を実装役が直し、低 L1・L2・L3(行の鍵 C → A)・L5・L6 も直した(§12)。親の答え: E6〜E9(物の基本操作)は CP2 の段階 1 の残りとして 2-1 の前に(PENDING §2)・原因の無い金の行に LlmCall を渡すのは 1-8・L8(つなぎの台帳の行)は rebase の後に足す。直しの後の試験 596 passed+slow 22 passed・byte-check 4 構成=final と残高 同じ・動く欄は K17 の分だけ(実装役)。
- **rebase の後(第334)**: 枝を本体(1-4・1-6 取り込み済み 9dd7dde)に rebase(衝突 5 本=状態台帳・系の宣言の表・凍結の鍵・10f の試験・台帳の行数の試験=両方の追加を残す形で実装役が解き、親が add と continue)。rebase 後に親が試験の一部 742 passed(5 分 21 秒)と byte-check 4 構成(新しい本体の src と比べて final 同じ・動いた欄は K17 の分=溢れていた 2 構成の end_of_day/full_last だけ=parent_head_vs_cp2_rebased_4cfg.json)を確かめた。
