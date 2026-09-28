# 小さいもの 4 件の台帳 — B5 近接行の同点・艦隊の受理待ち枠・年商アンカー・廃棄帯(2026-09-29)

正典: PENDING §2-9(小さいもの)・第300 Q107・第289 Q28(D-55)・D-16・D-52(第263 の内訳)。実装役 Opus 5.5。**件ごとに節を分ける**(親が件ごとに検収して 1 commit にまとめるか分けるかを決める)。計測スクリプト [small_fixes_measure.py](small_fixes_measure.py)(サブコマンド `t5`・`arms15`・`bytecheck`・`fleet`・`waste`)。計測は mock/classical 5,000 体・seed 1・W17 v2・語彙 v3・空腹 energy・`cli.run`。壁時計は同じ PC の 1 回の値(決定論でない)。holdout は触らない。

## ① 第300 Q107: B5 近接行の距離の同点を run_salt の決定論ハッシュで撹拌

### 入れたもの

| 口 | 中身 |
|---|---|
| 同点の切り方 `--near-tiebreak {hash,id}`(既定 `hash`・`id`=旧 golden) | `perception/renderer._nearby_items` の近接 k 人(密度逓減 3/2/1)の採り方。旧: `np.argpartition` がセル内の並び(=行番号の順)で同点を切る=同じノードに居る人のうち**行番号の小さい k 人**がいつも載る。新(`_near_take`): k 人目の距離 `thr` より近い人は全員・`thr` と同点の人から足りない分を**撹拌鍵の小さい順**に。鍵 = `near_tie_keys(salt64, 観る体, 相手)`(splitmix64 の仕上げ・配列演算)・`salt64 = blake3(run_salt ‖ b"nt\x00")` の先頭 8 バイト(`core.hashing` の 3 バイト用途タグの規約)。**tick は混ぜない**(位置が変わらない間は同じ人が見え続ける=宣言)。**文面・近接行の並び(id 昇順)・焦点の先頭・知人常掲・会話の参加者は変えない**=採る人だけ(v1.4 の SHA 不変) |
| 同点の無い描画 | k 人目の境に同点が無ければ採る集合は一意=両モードで**ビットまで同じ**(`test_hash_mode_equals_id_when_no_tie_sits_on_the_boundary`=連続座標の混雑世界・固定枠/ランキング両方) |
| salt | `engine.run` は `run_salt_for(seed)` を渡す。レンダラ単体は `seed` から同じ式で作る(テストで一致を固定) |
| manifest | `near_tiebreak`: `{mode, ties_broken(撹拌で切った描画の数), tie_candidates(そのときの同点の人数の延べ)}`(列追加のみ) |
| CLI | `shibuya.cli` と `shibuya.engine.run` に `--near-tiebreak`(`run_day(near_tiebreak=…)`・範囲外は `ValueError`) |

### 既定が動くか(byte-check・golden)

**HEAD bb44474 との byte 比較**([q107_byte_check.json](q107_byte_check.json)・git archive の src と作業木で同じラン・テープの blocks と calls 14 列):

| 構成 | HEAD | 作業木 `id` | 作業木 `hash`(既定) | hash でプロンプトが違う呼 ⊆ 同点を撹拌した描画の呼 |
|---|---|---|---|---|
| v3 既定(mock) | 993276d5 / 69,978 | **全部一致** | final・呼数・blocks は一致。calls の違いは `prompt_hash` と `tokens_in` の 2 列だけ | 53,103 ⊆ 54,489 **成り立つ** |
| classical | 18ed5c82 / 102,008 | **全部一致** | **e7e212ce / 102,189 に動く**(14 列) | (呼の並びが変わる=対象外) |
| v1 既定(mock) | 0a52a4d3 / 60,970 | **全部一致** | 同上(2 列) | 43,837 ⊆ 45,471 成り立つ |
| v3 + memory + relations(mock) | e4f84d1d / 72,940 | **全部一致** | 同上(2 列) | 55,124 ⊆ 56,847 成り立つ |

- **mock の checkpoint は動かない**: mock の応答は B5 の人物を読まない。動くのはプロンプト(近接行の人の id)と `tokens_in`(id の桁数)だけ。「同点の無い描画の呼」は 1 バイトも変わらない(差のある呼は全部、同点を撹拌した描画の呼)。
- **同点は多い**: mock v3 の呼の 78%(54,489 / 69,978)が k 人目の境に同点を持つ描画だった(同じノードに居る人の距離が同じ・同点の人数の平均 61)。
- **classical の checkpoint は動く**(近接行を読んで相手を選ぶ)。
- **golden**: 全体テストで落ちた golden は無い(mock の W17 golden 帰無腕 72cb9cd5・v3 993276d5 は不変・classical の checkpoint を固定したテストは無かった)。classical の動きを固定する golden を新設した: `tests/perception/test_near_tiebreak.py` の `CLASSICAL_1500_GOLDEN`(classical 1,500 体・seed 1・v3)= `hash` e0a6f3f9…/26,845・**`classical_tie_id` 803f0441…/26,753 = HEAD bb44474 の既定と一致**(HEAD の src で回して確認)。

**15 腕 × hash/id**([q107_arms15.json](q107_arms15.json)): **15/15 で final と呼数が一致**(全部 mock)。撹拌した描画は 40,147〜66,111 / 腕。

| 腕 | final(id = hash) | 呼数 | 撹拌した描画 |
|---|---|---|---|
| v3_default | 993276d5 | 69,978 | 54,489 |
| v3_activity_off | f746406e | 58,570 | 43,641 |
| v1_default | 0a52a4d3 | 60,970 | 45,471 |
| v1_derive_v2_1 | faada6a9 | 54,285 | 40,147 |
| v2 | f4382c82 | 60,901 | 46,153 |
| v1_edge | 6db51cbd | 54,150 | 40,243 |
| v2_edge | d61923ed | 54,170 | 40,305 |
| v1_edge_plateau | e32d69e9 | 55,173 | 41,157 |
| old_*(6 腕) | e1fcd39b / 46ca40a1 / 7c7d2423 / 951af158 / cf019588 / b94df1eb | 上と同じ | 上と同じ |
| golden_null_arm | 72cb9cd5 | 100,439 | 66,111 |

### T5(相手 ID の相関 ≤0.05)

C10 8b の計測道具(`c10-relations-2026-09-28/rel8b_measure.py` の `one`=層化 5,000 体・seed 1・v3・`--memory on`)に腕を足して回した([q107_t5.json](q107_t5.json))。**判定の 3 条件 = 呼数加重 |ρ|・部分相関・最大の層がどれも ≤0.05**(第300 の T5)。

| 腕 | 近接の同点 | final | 呼数 | 相手の選び(件) | 呼数加重 \|ρ\| | 部分相関 | 最大の層 ρ | セル内の ID 順位の平均 | 撹拌した描画 |
|---|---|---|---|---|---|---|---|---|---|
| mock 関係 off | hash | 35b23703 | 71,400 | 0 | — | — | — | — | 55,700 |
| mock 関係 off | id | 35b23703 | 71,400 | 0 | — | — | — | — | 0 |
| mock 関係 on | hash | 0fe0e65b | 85,110 | 5,060 | 0.0358 | −0.0143 | COMMUTER −0.0079 | 0.4700 | 65,476 |
| mock 関係 on | id | 0fe0e65b | 85,110 | 5,060 | 0.0358 | −0.0143 | COMMUTER −0.0079 | 0.4700 | 0 |
| classical 関係 off | hash | de372752 | 103,124 | 954 | 0.1794 | −0.1589 | COMMUTER −0.1991 | 0.1917 | 77,123 |
| classical 関係 off | id | b9f47df7 | 102,700 | 933 | **0.2278** | −0.1520 | COMMUTER −0.1649 | 0.0809 | 0 |
| **classical 関係 on** | **hash** | a377d8f4 | 142,542 | 1,300 | **0.0271** | **−0.0264** | COMMUTER **−0.0341** | 0.5013 | 107,546 |
| classical 関係 on | id | 02a30aa9 | 143,750 | 1,344 | **0.0625** | −0.0452 | COMMUTER −0.0379 | 0.4446 | 0 |
| (計測だけ)classical 関係 off・**並びも撹拌** | hash | 22201d4c | 102,575 | 941 | **0.0227** | −0.0087 | COMMUTER +0.0045 | 0.5004 | 76,810 |

- **classical 関係 on**(8b の相手選び)は 0.0625 → **0.0271**(3 条件とも ≤0.05)。`id` の腕は第301 の記録 0.0625 を再現する(classical 関係 off の `id` 0.2278/−0.1520/−0.1649/0.0809 も 8b の記録と一致)。
- **mock**(エンジンの経路)は T5 が動かない(相手選びは B5 を読まない=final も同じ)。mock の関係 off は相手選びの記録が 0 件(8b の道具は関係 on と classical の経路だけを数える)。
- **classical 関係 off** は 0.2278 → 0.1794 に下がるが 0.05 を越えたまま: 相手は「近接行の**最初の人**」で、近接行の**並び**が id 昇順だから(載る人を撹拌しても、その中の最小 id を選ぶ)。**計測だけの腕**(近接行の並びも同じ鍵で撹拌=描画の包み・実装していない)では 0.0227。並びの撹拌は「同点の無い描画」も変える(近接行に 2 人以上いる全描画)ので本件の範囲外=問い Q130。

### テスト

`tests/perception/test_near_tiebreak.py`(新規 9 本): 切替口と既定/`id` は旧実装(C7 前の逐語)と同点ありでも一致/`hash` は載る人を散らし文面・並び・距離は同じ(選ばれた回数と行番号の相関 <0.2)/同点の無い混雑世界で両モードがビット一致(固定枠・ランキング)/一番近い人は salt に依らず必ず載る/鍵は観る体・salt で変わり id と相関しない/既定の salt = `run_salt_for(seed)`/CLI と `run_day` の範囲検査/classical 1,500 体の golden(hash・`classical_tie_id`)。

## ② 第289 Q28(D-55): 艦隊 × 無制限 × 受理待ち枠 未指定 → 既定=体数

### 入れたもの

| 口 | 中身 |
|---|---|
| `cli.apply_fleet_queue_default(fleet, l4_scale, n_agents)` | 艦隊 × 呼数無制限(`l4_scale=0`)× `FleetConfig.queue_capacity` 未指定で、既定の枠(`max_in_flight×4`)が**体数より小さいときだけ**枠を体数にする(`FleetConfig` を `dataclasses.replace` で差し替え=manifest の `llm_fleet.queue_capacity` に載る・クライアントの `queue_capacity` も揃える)。既定の枠が体数以上なら狭めない(何もしない)。明示した枠・上限ありのラン・mock は変えない。**同期の経路(mock・`llm_bridge`)は触らない** |
| `cli.run` | 旧: 上の条件で `RuntimeWarning`+`l4_notes` に注記(挙動は変えない)。新: 枠を直して**警告なし**・`l4_notes` に「受理待ち枠の既定を体数 N にした」。枠を差し替えられない艦隊(`config` を持たない等)だけ従来の警告と注記 |
| `cli.fleet_queue_note` | 既定の枠が体数以上なら注記しない(繰り延べは起きない)を足した |

### 既定が動くか

- mock(艦隊なし)のランは通らない経路=**既定 checkpoint 不変**(全体テストの W17 golden 帰無腕 72cb9cd5・v3 993276d5 が通る)。
- 艦隊のスモーク([q28_fleet.json](q28_fleet.json)・偽 vLLM 2 本・300 体・24 tick・`max_in_flight` 8=既定の枠 32 < 300):

| 場合 | 受理待ち枠 | 繰り延べ(受理待ちあふれ) | 送った呼 | 警告 | `l4_notes` |
|---|---|---|---|---|---|
| 枠 未指定(**新しい既定=体数**) | **300** | **0** | 300 | なし | 「既定を体数 300 にした」 |
| 枠 32 を明示(=旧既定の再現) | 32 | 6,432 | 6,464 | なし | なし |

- 既存の艦隊スモーク(`test_fleet_smoke_unlimited_keeps_real_concurrency_within_l6_and_notes_the_queue`・300 体・既定の枠 64×2×4=512 ≥ 300)は「警告と注記が出る」を固定していた → 「枠を変えず・警告も注記も無い・繰り延べ 0」に直した(512 ≥ 300 なので繰り延べは元から起きない)。

### テスト

`tests/test_cli_l4_scale.py`(注記の検査を「直せない艦隊だけ」に直し+既定=体数の単体検査 1 本=差し替え・manifest・狭めない・明示/上限ありは不変・差し替えられない艦隊)・`tests/c6/test_l4_l6_budget.py`(既存スモークの期待を直し+枠の狭い艦隊のスモーク 1 本=既定で繰り延べ 0・枠 32 の明示で繰り延べ > 0)。

## ③ D-16: 年商アンカーの 1/10 を生値に訂正

### 入れたもの(出典の行)

令和3年経済センサス‐活動調査 事業所に関する集計 産業横断的集計 表 2-1(e-Stat 統計表 **0004006322**)・表章項目 **156-2021**「1事業所当たり売上(収入)金額」[万円]・area 13113(渋谷区)・経営組織 cat02=0(総数)。ローカルの取得ファイル(`data/realworld/estat/` の経済センサス 2021 渋谷区の JSON)で読み直した:

| 大分類 | 156-2021[万円] | 旧 `SALES_PER_ESTABLISHMENT` | 新(生値 × 10,000) | 検算: 155-2021 売上総額 ÷ 156-2021 = 売上を計上した事業所数(≤ 102-2021 事業所数) |
|---|---|---|---|---|
| M 宿泊・飲食 | 8,532 | 85,320,000 | 85,320,000(一致) | 227,810 百万円 ÷ 8,532 万円 = 2,670(≤ 3,366) |
| I 卸売・小売 | 131,523 | 131,520,000(**1/10**) | **1,315,230,000** | 7,143,009 百万円 ÷ 131,523 万円 = 5,431(≤ 6,311) |
| N 生活関連・娯楽 | 22,527 | 22,530,000(**1/10**) | **225,270,000** | 446,930 百万円 ÷ 22,527 万円 = 1,984(≤ 2,286) |

変えた場所: `src/shibuya/economy/anchors.py`(`SALES_PER_ESTABLISHMENT`・先頭の正典コメント・`ANCHORS` の出典文字列・出典の行のコメント)・`tests/economy/test_anchors.py`・`docs/design/v2-boundary-economy-design.md` §2.5 の表(「1億3,152万円」「2,253万円」→「13億1,523万円」「2億2,527万円」+訂正注記)・`src/shibuya/economy/entry_capital.py` の docstring(「親判断待ち 1.」→「訂正済み」)・`tests/economy/test_entry_capital.py`(docstring と、`anchors` と `entry_capital` の値の一致の検査を足した)。

### エンジンの挙動に効くか

**効かない=照合の物差しだけ**。`SALES_PER_ESTABLISHMENT` を読むのは `anchors.py` 自身(`ANCHORS` の表)とテストだけ(`src`・`tools`・`docs/bench` を grep)。`ANCHORS` の表もランは読まない(`cli` が読むのは `initial_wallets` だけ)。店舗の参入資本(`entry_capital`)は元から生値の別表(`SALES_PER_ESTABLISHMENT_BY_INDUSTRY`)を使っている。全体テストの W17 golden(帰無腕・v3)は不変。

### 訂正の伝播(grep「1億3,152万」「131,52」「2,253万」「22,530,000」・記録 docs/log を除く)

- 直した: 上の 5 ファイル。
- **直していない**(問い Q134): `docs/design/v2-implementation-plan.md:175`(「親判断待ち ①」として誤りを説明している行=解消済みになった)・`docs/research/v2-world-process-inventory-research.md:67`(答申の本文「1事業所当たり年商1億3,152万円」)・`docs/bench/analysis/notable-events-2026-09-24/README.md:101` と `sub_f_consumption_economy.md:61`(第263 の記録=「未訂正のまま」と書いた時点の事実)。

## ④ D-52: 廃棄帯の付け替え(宣言)

### 内訳(記録・[d52_waste.json](d52_waste.json))

廃棄 sink の日量 = 物の台帳の廃棄(**店舗の売れ残り → ビン → 収集**+**世帯の消費**)+ 街路清掃の回収分。コードで確認した発生源は **3 つ**:

| 発生源 | 規則(コード) | パラメータ(出典) | mock 5,000 体(実測) | 390,067 体 c7-day-4(記録と推定) |
|---|---|---|---|---|
| 店舗の期限切れ在庫 | 05:00 に棚 × SKU 廃棄率(切り捨て)→ ビン(`goods_flow._sell_leftovers_to_bin`)・06〜10 時に収集(`_collect_batch`) | 初期在庫 64 個/POI(`world/assets.py`)・SKU 廃棄率 0〜8% と質量(`economy/goods.py` CATEGORY_SKUS=**expedient・出典なし**)・2,337 POI | **0.9104 t**(収集) | 約 0.91 t(推定=静的な期待値と同じ POI・同じ棚) |
| 世帯の消費(購入した物の質量) | 19:00 に所持品を 1 個ずつ sink へ(`goods_flow._household_consumption` → `goods.consume_many` が `_day_waste_g` に**質量を足す**) | 購入した SKU の質量(弁当 350 g 等)=行動の結果 | **0.4319 t**(1,234 個) | 約 2.88 t(推定=物の台帳の廃棄 3.788 t − 店舗 0.91 t) |
| 街路ごみ | 在圏 × 0.05 g/人/tick(`goods_flow.py` の `LITTER_G_PER_PERSON_TICK`=**expedient・原単位は空欄**)・05〜07 時と 13〜15 時に 8 セル/tick を掃く | 同左 | **0.0831 t**(回収)・日末に 0.0612 t が路上に残る | 6.979 t(回収=記録)・発生は約 12.07 t(在圏 journal の 24 標本 × 60 分 × 0.05 g=近似) |
| 計 | | | **1.4254 t/日** | 10.767 t/日(記録) |

- **第263 の「店の廃棄 3.79 t」は店舗だけではない**: 物の台帳の廃棄には**世帯の消費**(19:00・購入した物の質量)が入る(`consume_many`・確定=コード)。c7-day-4 の 3.788 t のうち店舗の売れ残りは約 0.91 t(静的な期待値)で、残り約 2.88 t は世帯の消費(推定=引き算)。sub_f が空欄にしていた「世帯消費が廃棄の質量に入るか」は**入る**。
- **店舗の期限切れ在庫の静的な期待値**: 0.911 t/日(棚 64 個を使用スロットへ均等割り × 廃棄率 × 質量の総和=コンビニ 0.252 t・飲食 0.658 t・物販 0。**体数に依らない**)。mock 5,000 体の実測 0.9104 t と 350 g 差(05:00 前の販売 1 個分)。

### 付け替え(宣言=変えた文書と行)

| 文書・行 | 変更 |
|---|---|
| `docs/design/v2-pattern-ledger.md` §9 の W1 行(用途の欄) | **D-52 (a) 宣言**を足した: 区の総量(119.6 t/日)は世帯ごみ(第 2 陣)を入れるまで照合しない=「歪む場所」。検算②の帯は「モデル化した発生源のみの期待値」へ付け替え(**expedient・未リサーチ**・自己整合=現実照合ではない): 店舗の期限切れ在庫 **0.911 t/日 ±30% = 0.64〜1.18 t/日**(体数に依らない)。世帯の消費と街路ごみは行動・在圏に依存=**記録のみ**(帯の形は問い Q135)。**行は新設しない**(台帳の行 ID は `tests/world/processes/test_constitution.py` が凍結している=初版で W1′ を足して 1 件落ちたので W1 の注記に畳んだ) |
| `docs/design/v2-world-process-design.md` §7.1 の検算② | 「(D-52 (a) 宣言・小さいもの④: 区の総量は世帯ごみ=第 2 陣を入れるまで照合しない。②の帯は「モデル化した発生源のみの期待値」へ付け替え=パターン台帳 W1 行の注記・expedient)」を足した |

- **エンジン不変・checkpoint 不変**: コードは変えていない。ランの要約の「廃棄 … t/日 (band 83.7-155.5) NG」(`goods.waste_band` が `anchors.WASTE_TONNES_PER_DAY` ±30% を使う)と `RunResult.waste_band` はそのまま=**要約の帯は W1(区の総量)のまま**(要約を W1′ に切り替えるかは問い Q135・切り替えても報告だけで checkpoint は動かない)。
- **変えていない文書**: `docs/bench/c7/prereg_arms_v1.md:64`(事前登録 v1 の「歪む場所 D-52: 廃棄 1/5〜1/9」=開封前に凍結した行)・`docs/design/v2-redesign.md:451`(決定台帳)・答申(`docs/research/`)・`src/shibuya/economy/anchors.py` の W1 の値と正典コメント(区の総量は W1 の実数として正しい)・`docs/ops/build-report-*`(記録)。

## テスト本数と全体

全体(`-m "not gpu and not slow"`・p6 400k を除く・junit): **3,283 件・failures 0・errors 0・skipped 1(既存の W10 較正)・exit 0**(第303 の 3,272 件 + 新規 11 件=① 9・② 2)。途中の 1 回は④の W1′ 行の新設で `test_pattern_ledger_ids_match_the_frozen_list` が落ちた→ W1 行の注記に畳んで再実行=全部通過。① だけを入れた時点の全体も 3,272 件 exit 0(既存の golden は 1 本も動かない)。

## 宣言と問い

宣言: ① 撹拌鍵に tick を混ぜない・近接行の並び(id 昇順)は変えない・同点の無い描画はビット不変 ② 既定=体数は既定の枠が体数より小さいときだけ(狭めない)・`cli.run` は渡された艦隊の設定を差し替える(同じクライアントを体数の違うランに使い回すと最初のランの枠が残る) ③ 出典の行は表 0004006322 の 156-2021 総数 ④ W1′ の帯は店舗の期限切れ在庫だけ(宣言パラメータの静的な期待値)・世帯の消費と街路ごみは記録のみ。問いは報告の Q130〜。

## 再現

```
D=docs/bench/analysis/small-fixes-2026-09-29
python $D/small_fixes_measure.py t5 --out $D/q107_t5.json
python $D/small_fixes_measure.py arms15 --out $D/q107_arms15.json
python $D/small_fixes_measure.py bytecheck --head-src <HEAD bb44474 の src と docs/bench/anchors を展開した場所の src> --scratch <作業用の場所> --out $D/q107_byte_check.json
python $D/small_fixes_measure.py fleet --out $D/q28_fleet.json
python $D/small_fixes_measure.py waste --out $D/d52_waste.json
```

(Windows で HEAD の展開先のパスが長いと numba のキャッシュ書き込みが失敗する。`NUMBA_CACHE_DIR` と HEAD の src を短いパスにして回した。)

---

# 第 2 批(第304 の問いの決め → Q130・Q134・Q135・Q136)

第 1 批は第304(3c86b6b)でコミット済み。親の決め: Q130 近接行の並びを距離順に/Q131・Q132 承認/Q134 伝播/Q135 (a) 店だけの静的な帯を仮置き+ラン要約の帯も新しい物差しへ(報告だけ)・(c) 実単価のリサーチは繰り延べ/Q136 伝播+言い方を「世帯の一般ごみ(消費した財の質量以外)は第 2 陣」に。

## 第 2 批① 第304 Q130: B5 近接行の並びを距離順に

### 入れたもの

| 口 | 中身 |
|---|---|
| 並び `--near-order {distance,id}`(既定 `distance`・`id`=第304 の既定=旧 golden) | `perception/renderer._nearby_items` の並び。旧: 載る人を行番号の昇順。新(`_near_sort`): **距離の昇順**・距離の同点は `near_tiebreak` の順(`hash`= Q107 と同じ `near_tie_keys`・`id`= 行番号)。**焦点の先頭・知人の常時掲載・会話の参加者の掲載・載る人・文面は変えない**(v1.4 の SHA 不変)。距離は `d2`(旧と同じ値)で比べる。載る数人だけの Python の sort(numpy の呼び出しより速い) |
| manifest | `near_tiebreak` に `order`(distance/id)と `order_ties`(並べた行に距離の同点があった描画の数)を足した(列追加のみ) |
| CLI | `shibuya.cli` と `shibuya.engine.run` に `--near-order`(`run_day(near_order=…)`・範囲外は `ValueError`) |

### 既定が動くか(byte-check・golden)

**HEAD 3c86b6b との byte 比較**([q130_byte_check.json](q130_byte_check.json)・git archive の src と作業木・テープの blocks と calls 14 列):

| 構成 | HEAD | 作業木 `--near-order id` | 作業木 既定(距離順) | プロンプトが違う呼 = 並びが変わった描画の呼 |
|---|---|---|---|---|
| v3 既定(mock) | 993276d5 / 69,978 | **全部一致** | final・呼数・blocks は一致。calls の違いは `prompt_hash` の 1 列だけ(`tokens_in` は同じ=同じ人) | 52,088 = 52,088(⊆ が成り立ち、しかも等しい) |
| classical | e7e212ce / 102,189 | **全部一致** | **動く**(14 列) | (呼の並びが変わる=対象外) |
| v1 既定(mock) | 0a52a4d3 / 60,970 | **全部一致** | 同上(1 列) | 45,191 = 45,191 |
| v3 + memory + relations(mock) | e4f84d1d / 72,940 | **全部一致** | 同上(1 列) | 55,638 = 55,638 |

- **mock の checkpoint は動かない**(15/15・下の表)。動くのはプロンプト(近接行に 2 人以上いて並びが変わった描画)だけ。v3 既定では呼の 74%(52,088 / 69,978)。
- **golden の更新**:
  - 参照場面の描画の指紋 `GOLDEN_FIXED_PROMPT_HASH`(5 ファイル: `test_ablation1`・`test_ablation6_signage`・`test_intent_mode_open`・`test_signage_p_see_gate`・`test_vocab_v2_templates`)= bb23f7c6… → **f6a44b2b…**(参照場面の B5 が「P-1、P-9」→「P-9、P-1」)。旧値は `GOLDEN_FIXED_PROMPT_HASH_ORDER_ID` に残し、`test_ablation1` で `near_order="id"` が旧値を再現することを固定。
  - `CLASSICAL_1500_GOLDEN`(classical 1,500 体・seed 1・v3): `hash`(既定)= e0a6f3f9…/26,845 → **91732f34…/26,869**。旧値は `hash_order_id`(=第304 の既定)と `classical_tie_id`(=bb44474 の既定 803f0441…/26,753)で固定(3 本とも回して確認)。
  - `test_nearby_vectorized` の比較基準(C7 前の実装=行番号の昇順)は `crowd(near_order="id")` に固定した(ベクトル化の不変の検査なので)。距離順の検査は `test_near_tiebreak` に足した。
  - mock の W17 golden(帰無腕 72cb9cd5・v3 993276d5)は不変。

**15 腕 × 距離順/id 順**([q130_arms15.json](q130_arms15.json)): **15/15 で final と呼数が一致**。並べた行に距離の同点があった描画は 44,106〜79,350 / 腕(v3_default 60,112・golden_null_arm 79,350)。

### T5(層化 5,000 体・seed 1・v3・memory on・[q130_t5.json](q130_t5.json))

| 腕 | 並び | final | 呼数 | 相手の選び | 呼数加重 \|ρ\| | 部分相関 | 最大の層 ρ | セル内の ID 順位の平均 | k 番目の境界の同点を撹拌した描画(同点の人数の延べ) | 並びの同点のあった描画 | 壁時計[s] |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mock 関係 on | 距離順 | 0fe0e65b | 85,110 | 5,060 | 0.0358 | −0.0143 | COMMUTER −0.0079 | 0.4700 | 65,476(3,219,982) | 74,591 | 40.6 |
| mock 関係 on | id 順(第304) | 0fe0e65b | 85,110 | 5,060 | 0.0358 | −0.0143 | COMMUTER −0.0079 | 0.4700 | 65,476(3,219,982) | 0 | 39.0 |
| **classical 関係 off** | **距離順** | 424733dd | 102,616 | 961 | **0.0233** | **+0.0008** | COMMUTER **+0.0360** | 0.5225 | 76,882(6,405,988) | 87,238 | 45.5 |
| classical 関係 off | id 順(第304) | de372752 | 103,124 | 954 | 0.1794 | −0.1589 | COMMUTER −0.1991 | 0.1917 | 77,123(6,417,965) | 0 | 44.2 |
| classical 関係 on | 距離順 | a377d8f4 | 142,542 | 1,300 | 0.0271 | −0.0264 | COMMUTER −0.0341 | 0.5013 | 107,546(8,309,431) | 124,753 | 65.7 |
| classical 関係 on | id 順(第304) | a377d8f4 | 142,542 | 1,300 | 0.0271 | −0.0264 | COMMUTER −0.0341 | 0.5013 | 107,546(8,309,431) | 0 | 66.3 |

- **classical 関係 off は 0.1794 → 0.0233**(3 条件とも ≤0.05・第 1 批の「並びも撹拌」の計測だけの腕 0.0227 とほぼ同じ)。相手=近接行の最初の人=**一番近い人**になった(同点なら鍵の順)。
- **classical 関係 on は動かない**(final も同じ a377d8f4): 8b の相手選び(`pick_rest`)は近接行の「未知」の人を集合で受けて並びを見ない。
- **mock** は B5 を読まない=final・T5 とも同じ。
- **k 番目の境界の同点**(Q107 の撹拌)は並びと無関係=数は同じ。並びの同点(同じ距離の人が 2 人以上載った描画)は classical 関係 off で 87,238(呼 102,616 の 85%)。
- **壁時計**: 同じ PC・並べて 1 回ずつ=ラン全体では差が雑音の内(+1.6 s / +1.3 s / −0.6 s)。描画 1 回の費用(`_nearby_items`・合成の混雑世界・5 回の最良): 同点なし 16.9 → 20.3 µs(+3.4 µs)・全員同点 26.2 → 36.7 µs(+10.5 µs=撹拌鍵を作る分)。最初の実装(`np.lexsort`+`np.unique`)は +17 µs だったので Python の sort に替えた(並びは同じ=テストと T5 の final の一致で確認・byte-check は替えた後に回し直した)。15 腕の表の壁時計は最初の実装のもの(+1.1〜2.1 s/腕)。

### テスト

`tests/perception/test_near_tiebreak.py`(+5 本=切替口と既定/距離順は同じ人・同じ文面・同じ距離を並べ替えただけ(固定枠・ランキング)/全員同点なら鍵の順・焦点は距離に関係なく先頭/`id` は旧の並びを再現/CLI と `run_day` の範囲検査・classical golden を 3 本に)・参照場面の golden 5 ファイル・`test_nearby_vectorized`(基準を id 順に固定)。

## 第 2 批② 第304 Q134: D-16 の伝播

| 文書・行 | 変更 |
|---|---|
| `docs/design/v2-implementation-plan.md:175`(設計書) | 「親判断待ち ①」を**訂正済み**に書き換えた: 生値 1,315,230,000 円(131,523 万円)・225,270,000 円(22,527 万円)・M 85,320,000 円は元から一致・出典 表 0004006322 の 156-2021 総数 |
| `docs/research/v2-world-process-inventory-research.md:67`(答申・G1 行) | 本文は変えず、行末の値の欄に「〔第304 注記: D-16 で訂正=生値 1,315,230,000 円 / 225,270,000 円・表 0004006322 の 156-2021〕」 |
| `docs/bench/analysis/notable-events-2026-09-24/README.md:101`(第263 の記録) | 同じ注記を足した(本文「未訂正のまま」は当時のまま) |
| `docs/bench/analysis/notable-events-2026-09-24/sub_f_consumption_economy.md:61`(F-13) | 同じ注記を足した |

## 第 2 批③ 第304 Q136: D-52 の伝播

| 文書・行 | 変更 |
|---|---|
| `notable-events-2026-09-24/README.md:44`(E-22)・`:97`(廃棄 10.767 t の行) | 「店の廃棄 3.79 t」の後に「〔第304 注記(再計測): 物の台帳の廃棄 3.79 t = 店の売れ残り 約 0.91 t+世帯の消費 約 2.88 t(19:00・購入した物の質量=`goods.consume_many`)〕」 |
| `sub_f_consumption_economy.md:38`(6.「日次センサスの物の廃棄は 3.788 t」)・`:56`(F-8)・`:142`(「物の台帳 = センサスの waste_g と同じ量と仮定」) | 同じ注記 |
| `sub_f_consumption_economy.md:141`(② 世帯消費「これが廃棄の質量に入るかは確認していない=空欄」) | 「〔第304 注記: **はい**=`goods.consume_many` が消費した物の質量を当日の廃棄 `_day_waste_g` に足す〕」 |
| `sub_f_consumption_economy.md:201`(空欄の一覧「世帯消費(19:00)が廃棄の質量に入るか」) | 「〔第304 注記: **はい**(`goods.consume_many`)〕」 |
| `docs/design/v2-pattern-ledger.md` §9 W1 行 | 「世帯ごみ(第 2 陣)」→「**世帯の一般ごみ(消費した財の質量以外)**(第 2 陣)」・「(帯の形は親判断待ち)」→「(第304 Q135 (a): 店だけの静的な帯で仮置き・ラン要約の帯もこの物差し=報告だけ・実単価のリサーチは繰り延べ)」 |
| `docs/design/v2-world-process-design.md` §7.1 検算② | 「世帯ごみ=第 2 陣」→「世帯の一般ごみ(消費した財の質量以外)=第 2 陣」 |

記録(notable-events・答申)の本文は書き換えず、注記だけを足した。`docs/design` と `src` に「世帯ごみ」の語はもう無い(grep)。

## 第 2 批④ 第304 Q135 (a): ラン要約の廃棄帯=店だけの静的な帯+内訳 3 つ

### 入れたもの

| 口 | 中身 |
|---|---|
| `GoodsLedger.static_store_waste_g` | 店舗の期限切れ在庫の**静的な期待値**[g/日]= Σ 初期在庫 × SKU 廃棄率(切り捨て)× 質量(05:00 の売れ残り → ビンと同じ式を初期在庫に当てる)。構築時に 1 回。状態ではない(checkpoint に入らない)。体数に依らない |
| `GoodsLedger.store_waste_band()` | `(期待値, 下限, 上限)`[t/日] = 静的期待 × (1 ± `WASTE_BAND_RATIO` 30%)。**層契約**(engine は economy を import しない=`test_engine_does_not_import_economy`・`test_process_modules_do_not_import_build_or_economy`)のため帯の計算は物の台帳側に置いた(初版は runner が `economy.anchors` を import して 2 件落ちた→直した) |
| `WasteCollectionProcess.consumed_g` | 世帯の消費で廃棄 sink へ入った質量[g](`consume_many` が足す分と同じ・カウンタ `waste.consumed_g`) |
| `ProcessRunner.waste_sink_report()` | 内訳 3 つ(店=収集した質量・世帯の消費・街路=掃いた質量)+物の台帳のその他(棚卸差異など・ふつう 0)・**店だけの帯** = 静的期待 × (1 ± 30%)・`band_ok` = **店の収集量**が帯に入るか・帯の出所・「区の総排出量との比較は保留」 |
| `RunResult` | `waste_band` = 店だけの帯(旧=区 119.6 t/日 ±30%)・`waste_sink`(上の辞書・manifest に `waste_sink` として列追加)・`waste_band_ok` は店の収集量で判定(内訳の無い結果は従来どおり総量)。`waste_tonnes_per_day`(総量)は変えない |
| 要約の行 | 「廃棄 1.425 t/日(店 0.910・世帯の消費 0.432・街路 0.083)店の帯 (band 0.64-1.18) OK(帯=店の静的期待 0.911 t/日 ±30%・体数に依らない・区の総排出量との比較は保留)」。受入表の読み口(`c7lib.parse_run_summary` の「廃棄 N t/日」と「band a-b) OK」)はそのまま読める(テストで固定)。世界過程の要約(`runner.summary`)の「廃棄 sink(検算②)」行も同じ形に |

### 既定が動くか

**報告だけ=checkpoint 不変**: ①の byte-check の `id` 側(作業木に④が入った状態)が HEAD 3c86b6b と全構成で一致・mock の W17 golden も不変。

### 数値([q135_waste.json](q135_waste.json)・mock 5,000 体・seed 1・v3)

| 欄 | 値 |
|---|---|
| 総量 | 1.4254 t/日 |
| 店(期限切れ在庫の収集) | 0.9104 t |
| 世帯の消費 | 0.4319 t |
| 街路 | 0.0831 t |
| 物の台帳のその他 | 0.0 |
| 店だけの帯 | 0.6375〜1.1840(静的期待 0.91075 t/日 ±30%) → **OK** |
| 体数に依らない | 5,000 体と 390,067 体で静的期待は同じ 910,750 g(テストで固定) |

- 変えていない: **物の台帳の `waste_band`(W1=区の総量 119.6 t/日 ±30%)** と、それを使う**月次センサス**(`economy/census.monthly_census` の `waste_band_ok`)。今回の決めは「ラン要約」なので月次センサスの帯は区の総量のまま=問い Q137。

### テスト

`tests/engine/test_waste_sink_report.py`(新規 3 本=静的期待の式と W1 の帯は不変/合成世界のランで内訳 3 つ・帯・判定・manifest・要約の文と受入表の読み口/実世界で 0.911 t/日・体数に依らない)・`tests/test_cli.py` のコメント。

## 第 2 批 テスト本数と全体

全体(`-m "not gpu and not slow"`・p6 400k を除く・junit): **3,291 件・failures 0・errors 0・skipped 1(既存の W10 較正)・exit 0**(第304 の 3,283 件 + 新規 8 件=① 5・④ 3)。途中の 1 回は④の層契約で 2 件落ちた(runner が `economy.anchors` を import)→ 帯の計算を `GoodsLedger.store_waste_band` へ移して再実行=全部通過。

## 第 2 批 宣言と問い

宣言: ① 並びの同点は `near_tiebreak` の順(`id` を選べば行番号)・焦点は距離に関係なく先頭・並びは描画の Python の sort ④ 店の判定は収集量(05:00 → 06〜10 時の収集=1 日ランで当日に入る)・内訳の「その他」は物の台帳 − 店 − 世帯の消費。問いは報告の Q137〜。

## 第 2 批 再現

```
D=docs/bench/analysis/small-fixes-2026-09-29
python $D/small_fixes_measure.py t5 --only mock_rel_on_dist,mock_rel_on_hash,classical_off_dist,classical_off_hash,classical_on_dist,classical_on_hash --out $D/q130_t5.json
python $D/small_fixes_measure.py arms15 --axis order --out $D/q130_arms15.json
python $D/small_fixes_measure.py bytecheck --axis order --head-src <HEAD 3c86b6b の src と docs/bench/anchors を展開した場所の src> --head-label 3c86b6b --scratch <作業用の場所> --out $D/q130_byte_check.json
python $D/small_fixes_measure.py waste --out $D/q135_waste.json
```

(第 1 批のコマンドは第 2 批の後も同じ結果になるよう、並びを旧(`near_order="id"`)に固定して回す=`--axis tiebreak` が既定・T5 の第 1 批の腕も同じ。)
