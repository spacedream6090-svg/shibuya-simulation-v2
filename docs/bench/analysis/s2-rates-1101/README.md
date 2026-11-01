# 11-01 段 2 の 3・4 率の形の規則を外す(s2-rates-1101)の記録

> 実行役(Opus 5.5)の記録。作業木の枝 `stage/s2rates-1101`(土台 `c0729a4`=指示書の土台 `a09809c` の 3 つ後・`docs/design/v2-answers-2026-11-01.md` と `docs/reference/` の 3 本を含む)。commit は親。
> 正: [回答 11-01](../../../design/v2-answers-2026-11-01.md) §2(率の 5 件+同じ形の 4 件)・§3(循環 3 件)・[指示書 11-01](../../../design/prompt-2026-11-01.md) 段 2 の 3・4・[回答 10-13b](../../../design/v2-answers-2026-10-13b.md) §0-6(小さな版上げ=切替口は次の版上げで消す)。根拠と行番号は [棚卸し](../../../reference/decision-inventory-2026-10-31.md) §1(#2・#3・#10・#22・#42・#83・#99・#101・#105)・[行き先](../../../reference/decision-routing-2026-11-01.md) §6-B・[先例と現状](../../../reference/a1-research-2026-10-31.md) §6(#8・#9・#16・#17・#19)。
> 測った機械: Windows 11・x86-64・論理 CPU 20。比べたランは mock・5,000 体・seed 1・1 シミュ日・CLI の既定(`--llm mock` だけ)。絶対パス・ホスト名・個人名は書かない。

## 0. 結論

- 小さな版上げ 1 回分として、率の形の規則 8 件を**既定から外した**。旧道は切替口 1 つ `--rate-rules {off,legacy}`(環境変数 `SHIBUYA_RATE_RULES`・既定 off)で 1 版だけ残した。出勤率のくじは**道ごと消した**(旧の既定 1.0=全員出勤なので旧値は変わらない)。Calvo は結線していないことを確かめ、結線しなかった。
- **legacy は前の版と 1 バイトも変わらない**: 5,000 体 × 1 日の final `7bfe215641b792ac` は前の版(土台)・legacy・T7 の golden(`T7_V3_FINAL`)の 3 つで一致した。呼数 62,176 も同じ。golden の 4 本(`test_presence_executor` の null arm・v3 既定・l4×1・hunger v1)も `SHIBUYA_RATE_RULES=legacy` で通った。
- **既定(off)は結果が動く**: final は `73aa01d9afb206d0`、呼数は 62,176 → 61,066(−1,110・−1.8%)。〔検収の後・親の決定〕golden 12 本は off の値に更新した(10-13b §0-6=旧値は安定版のタグで再現)。t7 だけは旧道で旧値 `7bfe215641b792ac` を固定する 1 本を残した(§5-3・次の版上げで消す)。
- 独立の検収([review.md](review.md)=条件つき受入・高 0・中 3・低 7)の直しは §10。
- 5,000 体では E8(到着の分散)と乗車の受け入れ確率は**前も今も発火しない**(便の容量を超えないため・分散で動いた体 0・乗り残し 0)。この 2 件の効き目は 35 万体の全規模でしか測れない(回答 11-01 §12)。

## 1. 外したもの

| 名(`engine.rate_rules`) | 棚卸し | 外したもの(コード) | 既定 off の挙動=宣言 | 旧道 legacy | 計器(manifest の `rate_rules`) |
|---|---|---|---|---|---|
| `attendance` | #2 | 出勤率のくじ E6(`presence.attendance_draw`・`ATTENDANCE_KINDS`・`PlanExecutor`/`run_day` の引数 `attendance_rate`・CLI `--attendance-rate`・manifest の `attendance_rate`。〔検収 L7〕くじだけが読んでいた `PlanExecutor` の引数 `kind`・`agent_id` も消した) | 全員出勤(判断モデルの口ができるまで)。口 `PlanExecutor.absent_on(day)` は全員 False(カレンダー 1b も同じ口を読む) | 戻らない(道ごと消した=旧の既定 1.0 と同じ) | `counts.attendance_absent`(0) |
| `event_injection` | #10 | `civic.LargeEventProcess` の 18:00 の注入(200 人)と 21:00 の退出 | 催しの人の注入は無い。会場 3 セルの抽選と開催の記録(ActualLog の SCHEDULED の行=18:00・21:00)は残す | 前のまま | `counts.event_injection_arrived` |
| `arrival_spread` | #3 | `presence._spread_arrivals`(E8 ±8 便) | 全員が E1(間に合う最も遅い便)に乗る=`arrival_train == arrival_train_e1` | 前のまま | `counts.arrival_spread_moved` |
| `board_accept` | #22 | `rail.accept_quota` の受け入れ確率(150〜200% で 1.0→0.7) | 200% の上限(実効容量=定員×2.0)だけ物理として残す=上限までは全員乗る | 前のまま(`accept_rate` の関数は残す) | `counts.board_accept_refused`(=`rail.left_behind_by_rate`) |
| `litter` | #42 | `goods_flow.StreetCleaningProcess` の 0.05 g/人/刻み | ポイ捨ては無い(掃除の巡回は残す=拾う物が無い) | 前のまま | `counts.litter_generated_g` |
| `leftover_waste` | #99 | `goods_flow.WasteCollectionProcess` の 05:00 の売れ残りの廃棄率 | 売れ残りの廃棄は無い。腕 `--duties arm` の担当の体が捨てる分(`bin_by_staff`)は残る | 前のまま | `counts.leftover_waste_bin_rows` |
| `parcels` | #105 | `logistics.LastMileProcess` の区按分 27,000 個/日 | 宅配は無い(その日の予定 0=過程が動かない)。W2 は錨に残す | 前のまま | `counts.parcels_delivered` |
| `collapse` | #83 | `salient.SalientProcess` の倒れる率(`body/rules.py` の 3.0 件/万体/日のポアソン) | 体の式ができるまで倒れる人は無い(率 0)。出動の過程(`civic.PublicServiceDispatchProcess`)は残す=発火しない。W3 は錨に残す | 前のまま(3.0) | `counts.collapse_events`・`counts.collapse_rate_per_10k` |
| `calvo` | #101 | 価格の改定確率(`economy/pricing.py`) | 結線しない=価格は固定(§2) | 同じ(もとから結線していない) | `counts.calvo_draws`(0) |

切替口の扱いは `seat_release` と同じ形にした: 腕は組み立てのときに 1 回読み(`run_day` の引数にしない=設定の指紋に入れない)、`WorldProcessRunner`・`PlanExecutor` と各過程は引数 `rate_rules`(`None`=今の腕)で受ける。腕が既定と違えばランの種類は `arm`(`cli.run` の判定)。状態のファイルの見出しには、既定 off のランだけ `rate_rules: {"mode": "off"}` を書く(見出しに無い=legacy=版上げの前のラン)。再開のときに今の腕と違えば止める。

manifest の一番上の鍵に `rate_rules` を末尾(5-1 の `space` の後)に足した。中身は、設定が `schema`・`mode`・`rules`(規則ごとの棚卸しの行・外した後の文・錨に残す系)・`removed`(規則ごとの `rate_rule_<名>_removed`=1 は外した・0 は旧道で動く。腕だけで決まる)、観測が `counts`(旧道の件数=off のランでは 0)。一番上の鍵 `attendance_rate` は消した。過程の `counters()` にも `rate_rule_<名>_removed` と旧道の件数(`rail.left_behind_by_rate`・`street_cleaning.litter_generated_g`・`salient.collapse_rate_per_10k`)を足した(`process_counters` は manifest に入らない)。

倒れる率を直に渡す試験の口(`run_day(salient_rate_per_10k=…)`・`SalientProcess(rate_per_10k_per_day=…)`)は、〔検収 L3〕**旧道(legacy)でだけ効く**。腕 off では無視して率 0 にした(`removed` の印と食い違わない)。出動の経路を見る試験と道具(`tools/c7/salt_runs.py` の腕 `sal` ほか)はこの口を使うので、その試験は旧道で回す(§5-2)。口は次の版上げで旧道と一緒に消す(台帳 `DOC-s2rates-collapse-test-knob`)。

〔検収 M1〕店の廃棄の帯(`runner.waste_sink_report` の `band_ok`・月次 MER の `waste_band_ok`)は、腕 off では**非該当**(`None`)にした。帯は初期在庫 × SKU の廃棄率の静的な期待(外した #99)で、比べる相手が無い。値(帯・内訳・店の回収量)は残し、理由を `waste_sink.band_na`・`waste_band_na`(=`rate_rules.WASTE_BAND_NA`「非該当(売れ残りの廃棄率を外した=11-01 §2)」)に書く。要約の文は OK/NG の代わりにこの理由を出す。`tools/c7/c7lib.py` は「非該当」を `None` と読む(NG に数えない)。月次 MER は呼び手(`cli.write_census_files`)が腕を `waste_band_applies` で渡す(economy は engine を import しない)。legacy のランは前のまま(`band_na` の鍵も足さない)。

## 2. 価格の改定確率(Calvo)は結線していない

src の中で `economy/pricing.py` の Calvo の口(`calvo_draw`・`calvo_daily_probability`・`apply_r`・`deviation_cost`・`book_deviation_cost`・`propose_price`・`PriceProposal`・`CALVO_MONTHLY`・`DEVIATION_BETA`・`floor_price`・`clearing`)を呼ぶ所を grep した(`pricing.py` の外)。結果は **0 件**(当たったのは本段の `rate_rules.py` の鍵の名 `calvo_draws` だけ)。`pricing` を import するのは `economy/goods.py:60` だけで、使うのは内生フロアの係数 `K_VOLUME`・`K_AVERAGE`・`K_PREMIUM`(`goods.py:181-183`=店の初期の値付け=初期化)。`economy/accounts.py:373` は勘定の名前の文字列 `"pricing.deviation_cost"`(呼び出しではない)。同じ検査を試験 `test_calvo_is_not_wired_into_the_engine`(AST)にした。〔検収 L1〕別名の import(`import shibuya.economy.pricing as P`・`from shibuya.economy import pricing as P`・相対の `from . import pricing`)と完全修飾の呼び出し(`shibuya.economy.pricing.calvo_draw`)も見る形にした: `pricing` を import するモジュールの集合が `{economy/goods.py}`・そこで別名から引く名が `K_*` だけ・Calvo の名の属性の参照 0 件。負の対照 `test_negative_calvo_wiring_is_caught_through_aliases`(4 通りを植えると捕まる)。

設計書 `docs/design/v2-world-process-design.md` §8 の H-5(逸脱比例コストの β を E7 で較正する予定)の文に「〔11-01 §3 で取り下げ=E7 は検証に残す〕」の注を足した(この 1 文だけ)。

## 3. 前後の比べ(5,000 体 × 1 日・mock・seed 1・CLI の既定)

道具 [tools/compare_s2rates.py](tools/compare_s2rates.py)。「前」は土台のコード、「後」は本段の既定(off)、「legacy」は本段の切替口。

| 量 | 前 | 後(off) | legacy |
|---|---:|---:|---:|
| final(behavior-hash の先頭) | `7bfe215641b792ac` | `73aa01d9afb206d0` | `7bfe215641b792ac` |
| 呼数 | 62,176 | 61,066 | 62,176 |
| 壁時計[秒](3 本を同時に回した) | 51.8 | 50.8 | 51.7 |
| 到着: 鉄道で着く在圏ブロック/ゲート | 5,789 / 624 | 5,789 / 624 | 5,789 / 624 |
| 到着: E1 便から動かした体(E8) | 0 | 0 | 0 |
| 到着の時別(0〜23 時) | 3 本とも同じ: 468・0・0・1・12・108・352・951・1,018・899・232・58・92・90・109・109・106・220・346・260・146・97・63・52 | ← | ← |
| 在圏の人数 03・09・12 時 | 849・2,507・3,384 | 849・2,510・3,382 | 849・2,507・3,384 |
| 欠席(出勤率) | 0 | 0 | 0 |
| 催しの人出(注入した体・会場 3 セル) | 200 | 0 | 200 |
| 乗車の申込/乗り残し/確率で断られた | 4,202 / 0 / — | 4,051 / 0 / 0 | 4,202 / 0 / 0 |
| 街路ごみの発生/掃いた量[g] | —(141,658)/ 81,911 | 0 / 0 | 141,658 / 81,911 |
| 売れ残りのビンの行/収集[g] | 1,544 / 910,750 | 0 / 0 | 1,544 / 910,750 |
| 当日の廃棄 sink[g](世帯の消費を含む) | 1,308,400 | 395,850 | 1,308,400 |
| 廃棄の射影[t/日](W1 の欄) | 1.390 | 0.396 | 1.390 |
| 宅配の予定/配達[個] | 9,292 / 7,967 | 0 / 0 | 9,292 / 7,967 |
| 倒れた人/出動/顕著行為の事象 | 5 / 5 / 10 | 0 / 0 / 0 | 5 / 5 / 10 |
| ActualLog の行 | 27,886 | 25,276 | 27,886 |
| manifest に `attendance_rate` | ある | 無い | 無い |

- 「前」の街路ごみの発生量は前の版に計器が無い(—)。legacy の 141,658 g は前の版と同じ式の値(掃いた量と残りの和 81,911+59,747 と一致)。
- 呼数の差(−1,110)は、催しの注入(域外の体 200 人を 18〜21 時に舞台へ入れていた)と倒れる事象(顕著行為の起床)が無くなった分(推測・内訳は測っていない)。
- 世帯の消費(19:00 に持ち物のある全員が 1 個)は残る=当日の sink の 395,850 g はその分だけ(§4 の #41)。既定のランでは duties が腕なので、担当の体が捨てる分は 0(検収 §2-1 の指摘のとおり)。
- 店の廃棄の帯は、前と legacy は OK、off は非該当(§1・検収 M1)。

### 3-1 性能(〔検収 M3〕版上げの記録=10-13b §0-7)

5,000 体 × 1 日・mock・seed 1・CLI の既定(`--llm mock` だけ)・1 本ずつ単独で回した(Windows 11・x86-64・論理 CPU 20)。道具 [tools/perf_s2rates.py](tools/perf_s2rates.py)。刻みあたりは壁時計 ÷ 1,440 刻み。最大メモリは Windows の最大の作業集合(`GetProcessMemoryInfo` の `PeakWorkingSetSize`・10^6 B を MB とした)。

| 版 | 壁時計[秒] | 刻みあたり[ms] | 最大メモリ[MB] | 呼数(LLM・判断モデル 0) | final |
|---|---:|---:|---:|---:|---|
| 土台(`c0729a4`) | 42.5(検収役 42.5) | 29.5(検収役 29.5) | 543.4(検収役 503.8) | 62,176 | `7bfe215641b792ac` |
| 本段の既定(off) | 41.8(検収役 41.6) | 29.1(検収役 28.9) | 534.4(検収役 502.3) | 61,066 | `73aa01d9afb206d0` |
| 本段の legacy | 41.7(検収役 43.0) | 29.0(検収役 29.9) | 524.4(検収役は測り損ね=測り直した) | 62,176 | `7bfe215641b792ac` |

退化は無い(off は土台より壁時計 −0.7 秒・メモリ −9 MB)。最大メモリの値が検収役より約 40 MB 大きいのは、測り方の違い(本書は `cli.main` の後のプロセス全体の最大の作業集合・検収役の測り方は review.md に書かれていない)と見る(推測)。3 本の差は同じ測り方の中で比べる。

## 4. 疑いの 5 行(エンジンの出力がその錨の系に入っているか=読んだだけ・変更なし)

| 行 | エンジン側の出力 | 錨の系に入るか(`contributes` と計器) | 読み |
|---|---|---|---|
| #31・32 席 30 分 → D8 | `crowd.DWELL_MAX_TICKS=30`(`crowd.py:96`・`:231` で在席の印を 30 刻みで解く) | 過程 `indoor_occupancy` の `contributes=("D8",)`・`gate_condition`「商業滞在時間(D8)の形で照合」(`first_batch.py:368-370`)。D8 は holdout(パターン台帳 `:77`)。D8 を測る計器・判定関数は src と tools に無い(grep で 0 件) | 宣言上は入る(30 分の上限が滞在時間の分布の上端を決める)。いまは測っていないので循環は起きていないが、D8 の判定を作る前に L1.5 へ移すか、30 分を D8 の判定から外す必要がある |
| #98 補充 → W1/E5 | 補充(`ShelfRestockProcess`・10:00 の代打)が棚を満たし代金を店 → 外界へ払う | `shelf_stock_restock` の `contributes=("W1","E5")`(`first_batch.py:301`)。W1 へは棚の物が売れ残り・消費を経て廃棄 sink に入る道。本段で売れ残りの廃棄率を外したので、既定ではビンへの道は担当の体(腕 duties)だけ。E5(消費支出・**較正**の錨=台帳 `:88`)へは補充の代金は入らない(家計の支出ではない) | W1 は弱く入る(消費の量を決めるのは購入側)。E5 は宣言だけで出力は入らない(読み)。E5 が較正の錨なのは別の問題(§8 問い 5) |
| #41 家で使う → W1 | `WasteCollectionProcess._household_consumption`(19:00 に持ち物のある全員が 1 個・`goods.consume_many` → 廃棄 sink) | `waste_collection` の `contributes=("W1",)`。当日の sink(射影 `projected_tonnes_per_day`=W1 の欄)にそのまま入る(本段の後は sink の全部=395,850 g) | **入る**。全員が 1 日 1 個の規則の出力が W1 の欄を直に作る=率の形(19 時・全員)。外すかは同じ規則で判断が要る(§8 問い 4) |
| 車 → D5′ | `traffic.py`(道路交通センサス R3 の Q12・Q24 から断面の台数を作る=W10 の構築段と同じ行を定数表として写す) | `vehicle_cross_section` の `contributes=("D5′","D5")`(`first_batch.py:396`)。D5′ の台帳の行は「断面交通の較正・錨(較正→検証へ)」(`:213`) | **入る(循環)**: 駆動の値と照合の値が同じセンサスの行。回答 11-01 §10-1 のとおり通過交通を入力の欄にし、D5′ を検証へ移すなら、入力に使った箇所と照合に使う箇所を分ける(burned)必要がある |
| バス → D11′ | `logistics.BusTaxiProcess`(等間隔の到着だけ・乗降は作らない=`boardings` 0) | `bus_taxi_operation` の `contributes=("D6","D7")`(`first_batch.py:459`)。D11′(着トリップの手段の構成・バス 3.8%)への `contributes` は無い。出力に人の乗降が無いので D11′ にも D6・D7 にも何も入らない | 入らない。運転士が母集団に居るかは未確認(段 3 の 5) |

## 5. 試験

### 5-1 新しい試験

`tests/engine/processes/test_rate_rules_1101.py`(21 本・全部 passed。〔検収の後〕Calvo の負の対照を足し、ランの manifest の 2 本を 1 日の 1 本にまとめた): 切替口(既定 off・名の検査・印・見出しと再開)/E8(off=全員 E1 便・席より多くても散らさない/legacy=散らす)/乗車(off=180% で全員・195% で 200% の上限だけ/legacy=受け入れ確率で断る数を数える)/催し(off=注入 0・開催の記録は残る/legacy=注入と退出)/売れ残り(off=ビン 0/legacy=ビンへ)/ポイ捨て(off=0/legacy=人数 × 0.05 g)/宅配(off=予定 0・動かない/legacy=配る)/倒れる率(off=0・legacy=3.0・試験の口は腕に依らない・1 日分の引きで off は 0 件)/Calvo が結線されていない(AST・別名と完全修飾も・負の対照つき)/〔検収 L2〕ランの manifest=世界資産の 200 体 × 1 日(05:00 の売れ残り・05〜08 時の納品・08〜21 時の宅配・18:00 と 21:00 の催しを含む)を off と legacy で 1 本ずつ回し、legacy で催し・売れ残り・ポイ捨て・宅配の件数が立ち、off で全部 0・会場は立つ(合成の世界は鉄道が休みで域外の体が居ない=催しの注入が起きないので世界資産にした)/倒れる率の試験の口は off で無視(〔検収 L3〕)/`attendance_rate` が `run_day` と CLI から消えた・`--rate-rules` の名の検査。

### 5-2 直した既存の試験(機械的=消した口を参照していた・旧道の規則そのものを見る試験に legacy を明示した)

| 試験 | 理由 | 直し方 |
|---|---|---|
| `tests/engine/test_presence_executor.py`(助けの `make_layer` ほか 17 本が `TypeError`) | 消した引数 `attendance_rate` を `PlanExecutor` に渡していた | 引数を外した。E6 の試験は「全員出勤」の試験に書き換え・範囲外の値の試験は `TypeError` を見る形に。E8 の 3 本(容量・±8 便・最終便)と催しの経路の 1 本は `rate_rules="legacy"` を明示 |
| `tests/engine/test_calendar_sites.py`(モジュールごと import で落ちる) | `attendance_draw` を import していた | 「くじが消えた」ことを見る試験に書き換え |
| `tests/engine/calendar/test_ca1b_runs.py::test_attendance_lottery_below_one_is_kept` | `cli.run(attendance_rate=0.5)` | 「全員出勤・除いた理由の数 0」を見る試験に書き換え |
| `tests/engine/test_env_and_sections_10f.py`(3 本) | 設定の欄の変え方に `attendance_rate` を使っていた/一番上の鍵の末尾の並び/設定の節の道筋の指紋 `CONFIG_PATHS_SHA256` | 変え方を `signage_p_see`・`exit_mode` に・末尾に `RR11_KEYS=("rate_rules",)`・指紋を `94e8ae4c…` に(道筋の差は `attendance_rate` が消え `rate_rules.mode/removed/rules/schema` が足されただけ=前後の一覧の diff で確かめた) |
| `tests/engine/test_salt_seed_split_10f.py::test_seeded_hash_sites_are_classified` の表 | `("engine/presence.py","attendance_draw")` の行(関数を消した) | 行を消した(`run.py` の `MOTION_SALTS` の `attendance` も消した) |
| `tests/engine/systems/test_boxes.py`(2 本) | `run_day` の引数の数(108 → 107)と箱の欄 `cfg.attendance_rate` | `REMOVED_PARAMS`・`REMOVED_FIELDS` に足した |
| `tests/engine/time/manifest_keys_frozen.json`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py` | manifest の一番上の鍵の並び(末尾に `rate_rules`・`attendance_rate` を消した) | 凍結の一覧と末尾の並びを直した(凍結の JSON の注に理由を足した)。**一番上の鍵の凍結の更新は親が確かめてほしい**(golden の扱いか) |
| `tests/engine/processes/test_rng_scheme_10c.py`(モジュール全体)・`tests/engine/processes/test_salient.py`(モジュール全体) | 倒れる率の流れと試験の口(〔検収 L3〕口は旧道でだけ効く) | モジュールに旧道の autouse の fixture(どちらも前の版の挙動=legacy で通っていた試験) |
| `tests/engine/test_ablation23_switches.py`(助けの `spread_scene` と `test_d50_scale_reaches_the_salient_process_through_run_day`)・`tests/engine/test_resume_10d.py::test_counter_rng_resume_draws_once`・`tests/engine/test_salt_seed_split_10f.py`(3 本=子のプロセスの道具 `tools/c7/salt_runs.py` には環境変数も)・`tests/engine/test_state_checks_10f.py` の助け `_record`(率を渡すランだけ)と `test_k19_runtime_overlaps_only_in_the_allow_list` の比べるラン・`tests/engine/test_version_bump_10e.py::test_e4_l1_tape_meta_carries_the_rng_layout_and_old_counter_tapes_stop` | 試験の口 `salient_rate_per_10k` で出動の経路を見る(〔検収 L3〕) | 旧道を明示 |
| `tests/engine/test_waste_sink_report.py`(2 本) | 店の帯の判定(〔検収 M1〕off は非該当) | off と legacy の両方で回す形に(off=`None`・理由・要約の文・c7lib の読み/legacy=前のまま) |
| `tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`・新しい試験 | 〔検収 L7〕`PlanExecutor` の引数 `kind`・`agent_id` を消した | 呼び手の引数を外した |
| `tests/engine/processes/test_civic.py`・`test_goods_flow.py`(3 本)・`test_logistics.py`(3 本)・`test_rail_return.py`(2 本) | 旧道の規則そのもの(注入・廃棄率・ポイ捨て・宅配)を見る試験 | 過程に `rate_rules="legacy"` を明示(off の側は新しい試験 §5-1) |
| `tests/engine/duties/test_du_runs.py::test_discard_is_a_closing_task_and_the_morning_bridge_skips_it` | 05:00 のつなぎと担当の体の分け方を見る(つなぎは旧道だけ) | 旧道を明示(`monkeypatch` で腕を legacy) |
| `tests/economy/cp2/test_cp2_event_links.py::test_run_rows_and_events_are_one_to_one` | 200 体では廃棄率を外すと棚が補充点を割らず、補充の行が 0(補充の行の目印を見られない) | 旧道を明示(同じ試験が経済の段階 2 を off に固定しているのと同じ形) |
| `tests/engine/test_resume_10d.py::test_daily_tables_are_relaid_from_the_calendar_day` | 2 日目の宅配の配達(張り直し)を見る | 旧道を明示 |
| `tests/engine/test_ledger_wiring.py::test_goods_processes_change_the_world` | 「売れ残りがビンへ落ちる」 | 既定ではビン 0 を見る形に(納品と棚の変化は今のまま) |
| `tests/engine/test_processes_run.py::test_c4_second_half_on_the_real_world` | 宅配と収集の ActualLog の行・`parcels > 0`・`large_event.n_in > 0` | 既定では行が立たない(無い)こと・`parcels == 0`・`n_in == 0` かつ会場 3 セルを見る形に(負の対照) |

### 5-3 golden(既定の結果の固定)=〔検収の後・親の決定〕off の値に更新した

全体試験(`tests/engine tests/economy tests/c8 tests/tools`・`--ignore=tests/c7`・`-n 10`)の 1 回目は **22 failed・3,891 passed・1 skipped**(32 分)。§5-2 の直しの後に落ちたのは次の 12 本(golden)と、並列の負荷で落ちる性能の試験だけだった。golden は親の決定で off の値に更新した(値の注に前の値と「SHIBUYA_RATE_RULES=legacy で戻る」を書いた)。写しの検査(`test_env_and_sections_10f.py::test_golden_tables_are_keyed_by_platform_and_values_unchanged` の v3 既定・帰無腕・関係 on の 3 行)も同じ値に直した。差し替えの世界(W17 の md5 `02114fb577f3`)の行だけを更新し、W16 の世界の行(`3113e9ba7abb`)はそのまま。

| 試験 | 何の golden か | 新しい値(off) | 前の値(legacy で戻る) |
|---|---|---|---|
| `test_presence_executor.py::test_null_arm_reproduces_the_recorded_checkpoint` | D-62 の帰無腕 `null_arm_final`/呼数 | `2767525651ddb7ce`/101,035 | `872136c8ef8115f3`/99,453 |
| `test_presence_executor.py::test_v3_default_reproduces_the_recorded_checkpoint` | `v3_default_final`/呼数 | `73aa01d9afb206d0`/61,066 | `7bfe215641b792ac`/62,176 |
| `test_presence_executor.py::test_l4_scale_1_reproduces_the_stage_2c_checkpoints` | `null_arm_final_l4x1`・`v3_default_final_l4x1`/呼数 | `9df2be95f55a809a`/40,835・`335f80ac58b648e0`/36,350 | `9c5b3b6d353b7767`/40,983・`c50febb360d57315`/36,541 |
| `test_presence_executor.py::test_hunger_model_v1_reproduces_the_stage_3_checkpoints` | `null_arm_final_hunger_v1`・`v3_default_final_hunger_v1`/呼数 | `37fe9e3db225e9a8`/97,047・`09ff5fd88bb4bc09`/60,375 | `1e31a0c273bb60c0`/98,856・`b47d44e750e93dc3`/61,072 |
| `test_state_ledger_10b.py::test_t7_hash_cost_within_the_declared_cap[v3_default]` | `T7_V3_FINAL` | `73aa01d9afb206d0` | `7bfe215641b792ac` |
| `test_state_checks_10f.py::test_k19_runtime_default_v3_5000_known_counts` | `K19_V3_FINAL_COUNTER` | `73aa01d9afb206d0` | `7bfe215641b792ac` |
| `space/test_nav1_world.py::test_nav1_golden_w6_v3_default_on_the_activated_world[None/cell/unscaled]`(3 本) | `NAV1_GOLDEN`(final の先頭/呼数) | `73aa01d9afb206d0`/61,066・`7b976b2272ef57e4`/62,600・`7a27bf218610714c`/60,191 | `7bfe215641b792ac`/62,176・`6cc4f835866c1ebd`/63,853・`ef9999b0d56e50da`/61,234 |
| `test_classical_social.py::test_run_golden_and_arms` | `CLASSICAL_1500_GOLDEN_ACQ`(final/呼数) | `c56b731cc9b70f4a…53cc4`/23,917 | `9219b4a3810a1388…1ff01`/25,632 |
| `test_relations_tenure.py::test_relations_on_arm_golden_old_and_new` | `REL_ON_5000_GOLDEN` の (v2, behavior) | `8db3f95a61228c92`/63,710 | `140f365398ad4172`/64,500 |
| `proximity/test_runs.py::test_cell_arm_equals_the_head_golden` | `HEAD_GOLDEN`(final/呼数) | `2b342b34994d1963…ea90a6`/2,422 | `6acaa4cea49d0990…778707`/2,651 |

前の値は、更新の前に `SHIBUYA_RATE_RULES=legacy` で 13 本(nav1 は 3 本)を回して全部通った(3 分 11 秒)=前の値が legacy で再現することを確かめてから更新した。新しい値は off の 5,000 体のラン(帰無腕・空腹 v1・l4×1・k19 の 6 構成)を回して集め、t7・nav1・classical・関係・近接はランの値(落ちたときの値)を使った。

**旧道の固定 1 本**: `test_state_ledger_10b.py::test_t7_legacy_switch_reproduces_the_pre_bump_final`(`SHIBUYA_RATE_RULES=legacy` で final `7bfe215641b792ac`/62,176 と `rate_rules.mode == "legacy"`)。次の版上げで切替口と一緒に消す。

性能の 2 本(`test_change_detect_p6.py::test_p6_change_detection_under_2ms_at_400k_agents`=4.0 ms/刻み > 2 ms・`test_geometry_c9.py::test_p2_edge_geometry_under_300ms_at_400k_agents`=332 ms/刻み > 300 ms)は 10 並列の負荷で落ちた。単独で回すと本段と土台のどちらも通った(2 passed・35.5 秒と 35.7 秒)=本段の変更とは無関係。

設定の節の道筋の指紋 `CONFIG_PATHS_SHA256` は、〔検収 M1〕で `waste_sink.band_na` が設定の節に足されたので `fc5174c7…3308fca73` に改めた(土台との差=`attendance_rate` が消え `rate_rules.mode/removed/rules/schema` と `waste_sink.band_na` が足されただけ=一覧の diff で確かめた)。

### 5-4 最終の全体試験

§5-2 の直しの後の全体試験(同じ範囲・`-n 8`)は **13 failed・3,900 passed・1 skipped**(29 分 12 秒)。落ちたのは §5-3 の golden 12 本と、並列の負荷の P6(単独では通る)。

〔検収の後の直しの後〕全体試験(同じ範囲・`-n 8`)は **1 failed・3,915 passed・1 skipped**(30 分 41 秒)。落ちた 1 本 `test_state_checks_10f.py::test_k19_runtime_overlaps_only_in_the_allow_list` は、記録したラン(助け `_record`=旧道)と比べる包まないラン(既定 off)の腕が違った(〔検収 L3〕で試験の口が off で効かなくなったため)。比べるランも旧道にして直し、ファイルごと回して 25 本とも通った。合わせて **0 failed・3,916 passed・1 skipped**。skipped の 1 本は前からのもの(data 以外の理由 0 件=土台と同じ)。

## 6. 宣言に要る変更(S2-ledger へ・`src/shibuya/world/processes/` は本段で触っていない)

〔検収 M2・親の決定〕宣言(`world/processes/`)は S2-ledger の段で合わせる。取り込みの順は **規則の表 → 率の規則(本段)→ 台帳(S2-ledger)**。「宅配=過程を外す」は、本版では「組んだまま予定 0(`active` が偽)」で満たすと親が決めた。登録から外すのは台帳の段。

| 過程(`first_batch.py`) | いまの宣言 | 本段の後の実際 | 要る変更(案) |
|---|---|---|---|
| `large_event`(`:589-605`) | `update_rule`「報道ベースの大規模イベントを外生投入し、来街者の増分と占有セルを与える」・executor engine_rule・conf 0.3・`contributes=("D1′","D4′")`・`coverage`「主催者・参加者をエージェント化しないぶん=100%」 | 会場 3 セルの抽選と開催の記録だけ。人は動かさない | 「人の注入は無い」と宣言(回答 11-01 §10-3 の「催しの人の注入」)。`drives_from` は無し。D1′・D4′ を動かさない(催しの情報を入力にするのは段 3)。フォールバック台帳の行 `FB-large_event` の被覆の文 |
| `delivery_last_mile`(`:426-441`) | executor llm_agent・`gate_condition`「日次個数が W2 の上界 band に収まる」・`contributes=("W2",)` | 既定では動かない(予定 0) | 「宅配は無い」と宣言。W2 は錨に残す(`drives_from` から W2 を外す=循環の解消)。`gate_condition` の文 |
| `public_service_dispatch`(`:466-485`) | `gate_condition`「出場頻度が W3 の band に収まる」・`contributes=("W3",)` | 引き金(倒れる)が無い=出動 0 | 「救急と警察の出動は無い」(10-3 の一覧)と、倒れる率は体の式(B8)まで無い。W3 は錨に残す(回答 §3「体の式に置くまで W3 を検証から外す」と指示書「W3 は錨に残す」の両方=§8 問い 2) |
| `street_cleaning`(`:488-503`) | `gate_condition`「回収量が W1 の内訳として収支に載る」 | ごみが生じない=回収 0 | 「ポイ捨ては無い」と宣言(街路の清掃の過程そのものは 10-3 で「無い」の候補) |
| `waste_collection`(`:333-350`) | 「清掃員行動+C 類排出」・`contributes=("W1",)` | 売れ残りの廃棄率は外した。世帯の消費(#41)と収集は残る | 「売れ残りの廃棄は無い(duties を既定にするまで)」と宣言 |
| `rail_operation_static`(`:158-185`) | conf 0.6・`update_rule` は便の運行だけ(受け入れ確率の文は無い) | 受け入れ確率を外し 200% の上限だけ | 宣言の文の変更は不要(読み)。受け入れの上限を物理(式)として区分の列に書くなら `machine` |
| 計画実行層 E6・E8 | (台帳の行 `BR-ATTENDANCE-LOTTERY`・見出しの行 `HD-engine.presence-…`) | E6 は消した・E8 は既定から外した | 宣言の一覧(10-3)に「全員出勤」「全員が E1 の便」を足す |

## 7. つなぎの台帳の行(親が取り込みのときに回す)

[tools/add_bridges_s2rates.py](tools/add_bridges_s2rates.py)(何度回しても同じ台帳。写しの台帳で 2 回回して md5 が同じことを確かめた=673 行 → 677 行)。

- 閉じる: `BR-ATTENDANCE-LOTTERY` → `removed`(閉じた注つき)。
- 注を足す(active のまま=コードの宣言が旧道のために残る): `BR-BODY-COLLAPSE-RATE`・`PR-large_event`・`FB-large_event`・`PR-delivery_last_mile`・見出しの行 5 つ(presence・civic・goods_flow・logistics・rail=項の数は変えていない)・`DOC-tt23c-rail-congestion`・`DOC-du1-unstaffed-bridge`。
- 足す: `DOC-s2rates-legacy-switch`(next-bump・〔検収 L5〕次の版上げで書き直す旧道に固定した試験の一覧つき)・`DOC-s2rates-event-held-log`(6-1=仮・§8 問い 6)・`DOC-s2rates-collapse-test-knob`(next-bump・〔検収 L3〕旧道でだけ効く)・`DOC-s2rates-waste-band-na`(6-6=仮・〔検収 M1〕店の帯の非該当)。

写しの木(本段の src と試験+道具を回した台帳)で `tests/engine/bridging` を回すと、本書が無い間は `test_declared_places_exist` だけが落ちた(宣言の場所=本書)。本書を置いた後は写しの木で `tests/engine/bridging` と新しい試験が 69 本とも通った。本段はコードの宣言(6 形)を足しも変えもしていない=取り込みの前の台帳のままでも `tests/engine/bridging` は 49 本とも通る。

## 8. 親への問い

1. 〔解決=親の決定〕golden は off の値に更新し、t7 だけ旧道の 1 本を残した(§5-3)。
2. **W3 の扱い**: 回答 11-01 §3 は「倒れる率=体の式に置くまで **W3 を検証から外す**」、指示書は「W3 は錨に残す」。本段は数字を動かさず、両方を満たす読み(錨の行は残し、体の式の前は照合に使わない)で宣言の表(§6)に書いた。台帳の書き方は S2-ledger と合わせてほしい。
3. 〔解決=親の決定〕倒れる率の試験の口は旧道でだけ効かせ、次の版上げで消す(§1)。
4. **#41 家で使う**(19 時に全員が 1 個)は率の形で、W1 の欄を直に作る。同じ規則(回答 §2)で外すか。外すと既定のランの廃棄 sink は 0 になる。
5. **E5 が較正の錨**(パターン台帳 `:88`)で、`shelf_stock_restock` と `delivery_inbound` の `contributes` に入っている。§4 の読みでは出力は入らないが、`drives_from` の検査を作るときに較正と検証のどちらに置くかを決めてほしい。
6. **11-01p の段の番号が台帳の `PLAN_STAGES` に無い**(「段 3」で外す行を書けない)。仮に 6-1 を当てた。段 0〜5 を表に足すか、旧の番号へ読み替える表を作るか。
7. **催しの開催の記録**(注入の無い 18:00 と 21:00 にも ActualLog の SCHEDULED の行を書く)は本段の判断。開催の記録も消すと ActualLog の行が 6 行/日 減る。

## 9. 自己申告の欠陥と空欄

- 呼数の差の内訳(催しと倒れる事象のどちらがどれだけ)は測っていない。
- E8 と受け入れ確率の効き目は 5,000 体では 0(前も今も発火しない)=35 万体で測るまで空欄。
- 性能は §3-1(単独・3 本)。最大メモリの測り方が検収役と違い、値が約 40 MB ずれる(推測の理由は §3-1)。
- `tests/c7` は回していない(指示どおり)。`tools/c7/presence_yardstick.py` は錨のファイルの `attendance_rate`(現実の値)を読むだけで、manifest の欄は読まない=直していない。

## 10. 検収の後の直し(review.md=条件つき受入・高 0・中 3・低 7)

| 番号 | 直したこと | 場所 |
|---|---|---|
| M1 | 腕 off の店の廃棄の帯を非該当(`None`・理由つき・値は残す)。要約の文・月次 MER(呼び手が腕を渡す)・c7lib の読み。legacy は前のまま | `engine/processes/runner.py`・`engine/run.py`・`economy/census.py`・`cli.py`・`tools/c7/c7lib.py`・`engine/manifest_sections.py`・`engine/rate_rules.py`・試験 `tests/engine/test_waste_sink_report.py` |
| M2 | 宣言は S2-ledger の段で合わせる(取り込みの順と宅配の読みを §6 に) | 本書 §6 |
| M3 | 性能の記録(単独・3 本・壁時計・刻みあたり・最大メモリ・呼数・検収役の値の併記・legacy のメモリを測り直した) | 本書 §3-1・`tools/perf_s2rates.py` |
| golden | 12 本を off の値に更新・写しの検査も・t7 の旧道の 1 本を足した | §5-3 |
| L1 | Calvo の AST の試験に別名・相対・完全修飾の import と呼び出し・負の対照 | 新しい試験 |
| L2 | ランの manifest の試験を世界資産の 200 体 × 1 日(催し・廃棄・納品・宅配の時間帯を含む)で off と legacy を比べる 1 本に | 新しい試験 |
| L3 | 倒れる率の試験の口は旧道でだけ効く(off は 0)・その口を使う試験は旧道に固定 | `engine/processes/salient.py`・`engine/rate_rules.py`・§5-2 |
| L6 | 新しい名 `tick` を `step_no`(`civic._log_held` の引数)と `arr_min`(道具の局所)に | `engine/processes/civic.py`・`tools/compare_s2rates.py` |
| L7 | `PlanExecutor` の死んだ引数 `kind`・`agent_id` を消した(呼び手と試験も) | `engine/presence.py`・`engine/systems/build.py`・試験 3 本 |
| L4・L5 | 直さない(L4=規則ごとの腕は 35 万体のときに決める・L5=旧道に固定した試験の一覧を台帳の行 `DOC-s2rates-legacy-switch` に書いた) | 台帳の道具 |

直しの後の legacy は前の版と 1 バイトも変わらない(5,000 体 × 1 日の final `7bfe215641b792ac`・呼数 62,176=§3-1 と t7 の旧道の試験)。off の final は `73aa01d9afb206d0`(直しの前と同じ=M1・L3・L6・L7 は既定のランの結果を変えない)。
