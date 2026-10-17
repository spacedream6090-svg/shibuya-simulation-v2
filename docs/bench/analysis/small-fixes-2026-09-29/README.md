# 小さいもの 4 件の台帳 — B5 近接行の同点・艦隊の受理待ち枠・年商アンカー・廃棄帯(2026-09-29)

> **〔第311 印: 暫定・node 座標〕** この項の近接系の数値(B5 近接行・T5・同行・瞬間の群れ歩き・39 万体の組の候補数)は、体の位置がノードの座標に重なる条件で測った値である(node 幾何の全員。edge 幾何でも立ち止まっている体はノードに戻される=`resolve.py:1388-1404,1455-1472`)。2 m 内の組の 99.9% 以上が距離 0 ちょうど([読み直しの記録](../proximity-edge-2026-09-30/README.md))。連続位置が既定になるまで結論に使わない(指示書 09-30 §1-2 追加 B)。

正典: PENDING §2-9(小さいもの)・第300 Q107・第289 Q28(D-55)・D-16・D-52(第263 の内訳)。実装役 Opus 5.5。**件ごとに節を分ける**(親が件ごとに検収して 1 commit にまとめるか分けるかを決める)。計測スクリプト [small_fixes_measure.py](small_fixes_measure.py)(サブコマンド `t5`・`arms15`・`bytecheck`・`fleet`・`waste`・`norms`・`norms-full`)。計測は mock/classical 5,000 体・seed 1・W17 v2・語彙 v3・空腹 energy・`cli.run`。壁時計は同じ PC の 1 回の値(決定論でない)。holdout は触らない。

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

---

# 第 3 批(第305 の問いの決め → Q137・R-23 第3批の残り 15 件・D-44 (a))

第 2 批は第305(8e3aa9c)でコミット済み。親の決め: Q137 月次センサスの帯も店だけへ(この回)/Q138 帯は「自己整合性の検査(店の回収量 vs 静的期待・壊れの検知)」と明記(現実との照合ではない)/Q139 実 LLM で T5 と相手の距離分布を測る(GPU 後の項目)。

## 第 3 批① Q137: 月次センサスの廃棄帯=店だけの帯(+Q138 の明記)

| 口 | 中身 |
|---|---|
| `GoodsLedger.store_waste_g_total` | **店の回収量**[g]=ビン → bbox 外(`collect_waste`)の質量の累計(報告だけ・状態ではない=checkpoint に入らない)。世帯の消費・棚卸差異は入らない |
| `GoodsLedger.STORE_WASTE_BAND_NOTE` | 帯の意味の文(Q138): 「自己整合性の検査(店の回収量 vs 静的期待・壊れの検知)=現実との照合ではない・区の総排出量(W1 119.6 t/日)との比較は保留(世帯の一般ごみ(消費した財の質量以外)=第 2 陣の後)」 |
| `census.monthly_mer`(月次 MER) | `waste_band` = 店だけの帯(`store_waste_band()`)・`waste_band_ok` = **店の回収量 t/日**(`store_waste_g_total` ÷ 日数)が帯に入るか。足した鍵: `waste_store_tonnes_per_day`・`waste_band_check`(上の文)。**固定表 parquet の列は変えない**・`waste_tonnes`/`waste_tonnes_per_day`(物の台帳の総量)は従来のまま |
| ラン要約・manifest(Q138) | `waste_sink.band_check` に同じ文・要約の行の注記を「(自己整合性の検査=店の回収量 vs 静的期待 0.911 t/日 ±30%・現実との照合ではない・体数に依らない・区の総排出量との比較は保留)」に |

- **報告だけ=checkpoint 不変**(全体テストの W17 golden・帰無腕が通る)。
- W1(区の総量 119.6 t/日 ±30%)の帯は `goods.waste_band` に残した(参照用・月次センサスはもう使わない)。
- テスト: `tests/economy/test_census.py`(固定表の鍵の検査に足した 2 鍵を除く・小世界の月次で帯=店だけ・判定=店の回収量・文の明記)・`tests/engine/test_waste_sink_report.py`(+1 本=合成世界のランで月次センサスの判定がラン要約と一致・文の明記)。

## 第 3 批② R-23 第3批の残り 15 件(#1・#2・#6〜#18)の反映(D-86)

作法: 設計書(`docs/design`)は本文を直した(「現在」→「直す案」)/答申(`docs/research`)は本文を書き換えず、該当行に「〔第306 訂正(R-23 第3批 #N): …〕」の注記を足した/`v2_design_slides.html` は本文のテキストだけ/#16 は evidence map の該当行を消した。**根拠は答申 §5 の根拠欄を写しただけで新しい主張は足していない**。行番号は変更前の行(単一行の置き換え=変更後も同じ行。#16 の削除だけ行が 1 つ減る)。全文の前後は [r23_batch3_changes.json](r23_batch3_changes.json)。

| # | 場所(ファイル:行) | 方式 | 変更前 | 変更後 | 根拠(答申 §5 の根拠欄の写し) |
|---|---|---|---|---|---|
| 1 | `design/v2-architecture-roadmap.md:45` | 設計書=本文 | 記憶:習慣:判例=時定数1:5:25・ | 習慣:記憶統合:判例=時定数1:5:25 以上([推測]: 2 段のカスケード制御則=内ループは外ループの 5 倍以上速く、を 3 段へ再帰適用したもの。実務則の幅は 3:1〜20:1・3 段の先行は無い・第306 訂正=R-23 第3批 #1)・ | 答申 :187-188・P1P2 監査 :254・ControlGlobal / OptiControls |
| 1 | `design/v2_design_slides.html:175` | スライド=本文テキスト | 記憶(個人):習慣(個人):判例(世界)=時定数1:5:25で分離。 | 習慣(個人):記憶統合(個人):判例(世界)=時定数1:5:25 以上で分離([推測]: 2 段のカスケード制御則=内ループは外ループの 5 倍以上速く、を 3 段へ再帰適用したもの。実務則の幅は 3:1〜20:1・3 段の先行は無い)。 | 答申 :187-188・P1P2 監査 :254・ControlGlobal / OptiControls |
| 2 | `design/v2-c10-relations-agenda.md:26` | 設計書=本文 | Δ と時定数は expedient 宣言(1:5:25 の中間) | Δ と時定数は expedient 宣言(**第306 訂正・R-23 第3批 #2**: 旧「1:5:25 の中間」の 1:5:25 は習慣:記憶統合:判例の時定数比 [推測](#1 の順序訂正)で、半減期 30 日が「中間」かはどの層を 1 とするかで変わる=**再確認待ち**) | 同上(#1) |
| 2 | `design/v2-c10-relations-agenda.md:53` | 設計書=本文 | **半減期 30 日**(Dunbar 層の 1:5:25 の中間・現実アンカー無し) | **半減期 30 日**(現実アンカー無し。**第306 訂正・R-23 第3批 #2**: 旧「Dunbar 層の 1:5:25 の中間」の 1:5:25 は習慣:記憶統合:判例の時定数比 [推測]=「中間」かはどの層を 1 とするかで変わる=**再確認待ち**・下の第230 追記も参照) | 同上(#1) |
| 6 | `design/v2-redesign.md:196` | 設計書=本文 | 無検証のLLM自作ルールは効果ゼロの実測(SkillsBench)。 | 無検証のLLM自作ルールは効果ゼロの実測(**SkillsBench arXiv 2602.12670 v1**・86 タスク/11 領域/7 構成/7,308 軌跡。**現行版は self-generated 条件を抄録から外している**ので版を固定して引く=第306 訂正・R-23 第3批 #6)。 | https://arxiv.org/abs/2602.12670・`v2-precedent-system-deep-research.md:84` が現行版 +16.6pp を引いている |
| 7 | `design/v2-redesign.md:402` | 設計書=本文 | 34行(4階層・世界側38%→再取得で4割強へ)+封印2+診断5・強5本(A1会話グループ/C1カスケード/D1滞在カーブ/D4休日平日比/E2成長率ラプラス) | **36行**(4階層・世界側 **42-44%**)+封印2+診断5・強5本(A1・C1・**D1′ 滞在人口カーブ**(09-03 差し替え)・**D4′ 3街路の日内プロファイル分化**(09-01 追補⑤)・E2)。**D1′ と D4′ は同一パネル=実効強 4.5 本**(第306 訂正・R-23 第3批 #7=`v2-pattern-ledger.md:5,136,164,166`・旧「34行・世界側38%→4割強・D1滞在カーブ/D4休日平日比」) | `v2-pattern-ledger.md:5,136,164,166` |
| 8 | `design/v2-budget-declaration.md:58` | 設計書=本文 | \| 方法論答申(Phase 0で先取り確保・「余力があれば」にしない=v1失敗⑤の処方箋) \| | \| **expedient(一次なし)**。`v2-methodology.md` の工程判断であり、答申の裏づけは無い(第306 訂正・R-23 第3批 #8=旧「方法論答申」)。Phase 0で先取り確保・「余力があれば」にしない=v1失敗⑤の処方箋 \| | `docs/research/` に該当答申なし |
| 9 | `research/v2-benchmark-standards-research.md:13` | 答申=注記(本文は当時のまま) | 英DMRB=**「交通量の85%がGEH<5」**が較正基準。 | 英DMRB=**「交通量の85%がGEH<5」**が較正基準。〔**第306 訂正(R-23 第3批 #9)**: この較正基準は**英DfT TAG Unit M3.1 Table 2 Guideline 2**=『GEH<5 を >85% のケースで』(GEH 統計そのものは DMRB 由来)。出典 TAG M3.1 PDF〕 | TAG M3.1 PDF |
| 10 | `research/v2-benchmark-standards-research.md:39` | 答申=注記(本文は当時のまま) | 目的別カバレッジ93-104%=「都市規模人流の現実的合格ライン」。 | 目的別カバレッジ93-104%=「都市規模人流の現実的合格ライン」。〔**第306 訂正(R-23 第3批 #10)**: **東京(=行動モデルの生成に使った域)93-104%・Kinki 97-113%・East Suruga 83-102%**。**外部検証域は Kinki と East Suruga** で、East Suruga は通勤 R²<0.5・通勤量 17% 過少。『合格ライン』を引くなら外部検証域の値を使う。出典 arXiv 2205.00657 §4.2・§4.2.3・Table 5〕 | arXiv 2205.00657 §4.2・§4.2.3・Table 5 |
| 11 | `research/v2-llm-serving-deep-research.md:16` | 答申=注記(本文は当時のまま) | **Model Runner V2(2026-03)=小モデル×高リクエストで+56%** | **Model Runner V2(2026-03)=小モデル×高リクエストで+56%**〔**第306 訂正(R-23 第3批 #11)**: MRV2 は **Qwen3-0.6B × 1×GB200** のホスト側オーバーヘッド強調条件で **16K→25K tok/s(+56.2%)**。**既定ではなく実験的**(`VLLM_USE_V2_MODEL_RUNNER=1`・v0.17+・LoRA 等未対応)。**8B × A5000 への外挿は未実証**。出典 https://vllm.ai/blog/2026-03-24-mrv2〕 | https://vllm.ai/blog/2026-03-24-mrv2 |
| 12 | `design/v2-redesign.md:465` | 設計書=本文 | =**Qwen3-32B AWQ・TP4・温度0**(TP4 の非再現 4.1% は凍結で吸収) | =**Qwen3-32B AWQ・TP4・温度0**(TP4 の非再現 4.1% は凍結で吸収。**AutoAWQ は 2025-05-11 にアーカイブ済み**なので量子化は **llm-compressor** の AWQ レシピで行う(推論側は vLLM が AWQ 形式を継続サポート)=第306 訂正・R-23 第3批 #12) | AutoAWQ repo・vLLM docs |
| 13 | `research/v2-data-contract-research.md:48` | 答申=注記(本文は当時のまま) | `create_memory`/`search_memory`の語彙あり。 | `create_memory`/`search_memory`の語彙あり。〔**第306 訂正(R-23 第3批 #13)**: `gen_ai.operation.name` の既知値は 9 個(`chat`/`create_agent`/`embeddings`/`execute_tool`/`generate_content`/`invoke_agent`/`invoke_workflow`/`retrieval`/`text_completion`)。**記憶操作の値は無い**ので `retrieval` か独自値を宣言する。**仕様は opentelemetry.io から GenAI 専用リポへ移設済み**。出典 OTel 属性レジストリ〕 | OTel 属性レジストリ |
| 14 | `research/v2-game-tech-import-research.md:41` | 答申=注記(本文は当時のまま) | 全DLなし検索**)・SC2(.SC2Replay=game.events/tracker.events/message.eventsの分離収録)・ | 全DLなし検索**)・SC2(.SC2Replay=game.events/tracker.events/message.eventsの分離収録)・〔**第306 訂正(R-23 第3批 #14)**: **Epic の DemoNetDriver 公式ドキュメントにイベント検索の記述は無い**(text tags は**リプレイ一覧の検索**用)。タグ付きイベント索引の先行は **SC2 の game.events / tracker.events / message.events 分離**の方。UE 側は HTTP Streamer REST API を一次で当たる(残務)。出典 Epic DemoNetDriver ページ〕 | Epic DemoNetDriver ページ |
| 15 | `research/v2-game-tech-import-research.md:17` | 答申=注記(本文は当時のまま) | Hitman Absolution(群衆1200体・必要時に本物NPCへ昇格)・ | Hitman Absolution(群衆1200体・必要時に本物NPCへ昇格)〔**第306 訂正(R-23 第3批 #15)**: 群衆 **1200 体/1 群衆・同画面 500 体**・30fps(GDC Europe 2012)。公開資料の目標は『**プレイヤーが群衆と NPC を見分けられないこと**』で、**on-demand 昇格の明記は見つからない**(昇格機構の先行は AC Unity のプール入替)。出典 GDC Vault / Fauerby スライド〕・ | GDC Vault / Fauerby スライド |
| 16 | `design/v2-decision-evidence-map.md:244` | 設計書=行の削除と件数・★ | \| L458 \| R15 可視化 \| 決定行が「既存答申(v2-game-frontend-research.md・**親検収済み**)」と書くが、INDEX の等級は **D**(出典 URL ゼロ)= **記載と等級の食い違い** \| 決定行・INDEX §1・batch1 §1 \| | (行を削除) | `v2-redesign.md:458`(現 459 行) |
| 16 | `design/v2-decision-evidence-map.md:222` | 設計書=行の削除と件数・★ | ## 5. 要写し検査(★)— 19 行 | ## 5. 要写し検査(★)— 18 行(第306: L458 行は `v2-redesign.md` の R15 行が「出典の一次確認は未・INDEX 等級 D(第218)」と自己訂正済みのため消した=R-23 第3批 #16) | `v2-redesign.md:458`(現 459 行) |
| 16 | `design/v2-decision-evidence-map.md:128` | 設計書=行の削除と件数・★ | \| L458 \| R15 可視化 \| 09-08 \| 初回=計器盤WebUI+deck.gl 2D・GlassBox 規律 \| v2-game-frontend-research(決定行がリンク) \| **D** \| 答申あり(親未確認) \| ★ \| | \| L458 \| R15 可視化 \| 09-08 \| 初回=計器盤WebUI+deck.gl 2D・GlassBox 規律 \| v2-game-frontend-research(決定行がリンク) \| **D** \| 答申あり(親未確認) \| (第306: ★解消=R-23 第3批 #16) \| | `v2-redesign.md:458`(現 459 行) |
| 17 | `research/v2-pattern-ledger-deep-research.md:74` | 答申=注記(本文は当時のまま) | - **POM適用の実録**: 半乾燥放牧地=**10^9通り→11,316組(0.001%)が生存**・ | - **POM適用の実録**: 半乾燥放牧地=**10^9通り→11,316組(0.001%)が生存**〔**第306 訂正(R-23 第3批 #17)**: 出典 *Ecological Modelling* 275:78–88 (2014), doi:10.1016/j.ecolmodel.2013.12.009(「Pattern-oriented parameterization of general models for ecological application」)〕・ | 抄録逐語 |
| 18 | `research/v2-game-frontend-research.md:46` | 答申=注記(本文は当時のまま) | (ビューアが独自に補間・演出したものは描かない)。 | (ビューアが独自に補間・演出したものは描かない)。〔**第306 訂正(R-23 第3批 #18)**: 原典の逐語は「**every aspect of the game is an agent that reports back to the underlying simulation**」(表示物がシムへ報告する向き)。v2 の運用「ビューアは演出しない」は**裏返しの含意=v2 側の規律として宣言**する。出典 EA 公式・GDC 2012〕 | EA 公式・GDC 2012 |
| 18 | `design/v2-redesign.md:459` | 設計書=本文 | 介入UIは「pause/速度/イベント注入1種」に限定しGlassBox規律(見えるもの=シムの1:1・介入は記録される実験条件)。 | 介入UIは「pause/速度/イベント注入1種」に限定しGlassBox規律(見えるもの=シムの1:1・介入は記録される実験条件)。(第306 訂正・R-23 第3批 #18: GlassBox 規律は **v2 側の規律として宣言**する=原典 SimCity GlassBox の逐語は「every aspect of the game is an agent that reports back to the underlying simulation」で向きが逆) | EA 公式・GDC 2012 |

**反映しなかった部分(§5 の「場所」に書かれているが、いまの行に該当文が無い)**:

| # | §5 の場所 | いまの行 | 理由 |
|---|---|---|---|
| 11 | `v2-budget-declaration.md` | — | MRV2 の記述が無い(grep「MRV2」「+56」)=答申への注記だけ |
| 13 | L389(決定台帳) | `v2-redesign.md:390`(6 データ契約) | 「llm_calls=OTel GenAI準拠」だけで記憶操作の語彙の主張は無い=答申への注記だけ |
| 14 | L394(決定台帳) | `v2-redesign.md:395`(U3 データ契約追記2点) | 「タグ付きイベント索引+checkpoint 時間スライスを採用」だけで UE のイベント検索の主張は無い=答申への注記だけ |
| 15 | L397(決定台帳) | `v2-redesign.md:398`(U6 認知LOD) | Hitman の主張は無い=答申への注記だけ |

§5 の行番号は答申を書いた時点のもので、いまの決定台帳は 1 行ずれている(#7 L401 → 402・#12 L464 → 465・#18 L458 → 459。#3〜#5 を反映した第229 の注記で行が動いた)。

## 第 3 批③ D-44 (a): build_manifest の expedient の一括判定(既存の記録だけ)

**出力**: `tools/c8/sensitivity_v1.json`(台帳=正)と `docs/bench/c8/sensitivity_v1.{json,md}`(`python tools/c8/sensitivity.py --judge-manifest --out docs/bench/c8` の出力)に鍵 `build_manifest_judgment` を足した。**既存の 19 行・過程の id 22 本・旧 `build_manifest_expedients`(09-09 の 122 行の注記)は 1 バイトも変えていない**(鍵ごとの一致で確認)。表の頭に規則の文言(片側・第229 決定)と**検出可能効果量の床(第200: 2 seed では f≈1 未満を検出できない=「特大の駆動が無い」の証明にとどまる)**を載せた。

**数え**(build_manifest の build_hash 09571e85…):

| | 行数 |
|---|---|
| build_manifest の expedient(いま) | **121**(09-09 の台帳の注記は 122=段階の改版で W6 +1・W7 +5(D-72)・W10 +1・W17 −8(v2)=差し引き −1) |
| 既存の台帳行が扱う行 | **16**(下の表=設計書の感度宣言 14 アンカーのうち 12 アンカーが 15 行に当たる+実装計画書の RAKE が W17#3 に当たる) |
| 判定した行 | **105** |
| └ 駆動しえない(帰無参照内) | **0** |
| └ ラン対照へ(超える) | **0** |
| └ **判定不能(JSD 無し)** | **105** |

- **判定不能が 105 行全部**: 構築の記録(`acceptance/summary.json`・`W*.header.json`・`sensitivity_v1`)に「宣言 vs 対照」の入力側 JSD があるのは既存の台帳行(5 本が実行済み)だけだった。記録にある JSD は 2 つあったが、どちらも**目標への当てはまり**で対照との差ではない(W16#13 の方面の抽出 0.000139・W17#3 の raking 0%/12% の PT 目標への JSD 0.3585/0.2531)=備考に記録した。
- **既存の台帳行が扱う 16 行**: W1#1(S-W3-LAYER)・W2#1(S-W2-GRID)・W4#1/#2(S-W5-HEIGHT)・W5#1(S-W6-ENTRANCE)・W6#1(S-W7-ORGALLOC)・W7#1(S-W8-HOURS)・W8#1(S-W9-BUFFER)・W10#1(S-W11-AADT)・W11#1(S-W13-CONCOURSE)・W12#1(S-W14-HOURUNIFORM=ラン対照が要る)・W12#4(S-W14-JRPHASE=駆動していない)・W13#1/#2(S-W15-TEMP=ラン対照が要る)・W16#3(S-W16-FLOOR=ラン対照が要る)・W17#3(S-W17-RAKE=ラン対照が要る。ただし台帳行の測定は W17 v1 の「適応 vs 固定 12%」で、いまの W17 v2 は「0% を採用」)。
- **台帳行のうち build_manifest に対応行が無い**: S-W10-SHADOW(影グリッドの時刻刻み 5 分=W9 の expedient 欄に無い)・S-W17-T2(T1 選択=W17 v2 の欄に無い)・S-AB1-BUDGET・S-C7-BOUNDARY・S-C7-KINDATTR(構築外)。
- 対応の照合は本文の書き出し(`sensitivity.COVERED_EXPEDIENTS`)で、実データがあれば manifest から作り直した判定列が台帳と一致することをテストで固定(行番号は段階の版で動くため)。

テスト: `tests/c8/test_sensitivity_ledger.py`(+4 本=判定列の集計・3 値の整合・規則の文言(片側・f≈1・第200)・既存の 19 行と旧注記は不変/検査器が不正な判定と集計のずれを捕まえる/Markdown に規則と表/実データの manifest から作り直すと一致・既存行の書き出しは 1 行ずつに当たる)。

## 第 3 批 テスト本数と全体

全体(`-m "not gpu and not slow"`・p6 400k を除く・junit): **3,296 件・failures 0・errors 0・skipped 1(既存の W10 較正)・exit 0**(第305 の 3,291 件 + 新規 5 件=① 1・③ 4)。

## 第 3 批 宣言と問い

宣言: ① 月次センサスの判定=店の回収量 ÷ 日数(ラン要約と同じ量)・W1 の帯は参照用に残す ② 答申は注記だけ・根拠は §5 の写し・§5 の場所にいま該当文が無い行は変えない ③ D-44 の判定は既存の記録だけ(構築の再実行もしない)・既存行の照合は本文の書き出し。問いは報告の Q140〜。

## 第 3 批 再現

```
python tools/c8/sensitivity.py --judge-manifest --out docs/bench/c8   # D-44 (a) の判定列(台帳 tools/c8/sensitivity_v1.json に書く)
```

---

# 第 4 批(第306 の問いの決め → Q141・Q142・D-44 (c))

第 3 批は第306(815d00a)でコミット済み。親の決め: Q140 D-44 の次はユーザー判断へ(親推奨=(c) 依存グラフで読まれない行を除く → 残りは (a) 構築段階の対照=再構築の許可が要る)/Q141 直す/Q142 伝播する/Q143 親が直した/Q144 承認。本批は文書と解析だけ(エンジン不変・新しいランや再構築なし)。

## 第 4 批① Q141: 感度台帳の旧注記の行数を現行へ

`tools/c8/sensitivity_v1.json`(と出力 `docs/bench/c8/sensitivity_v1.{json,md}`)の `build_manifest_expedients`:

| 欄 | 前 | 後 |
|---|---|---|
| `count` | 122 | **121** |
| `note` | 「122 行の自由文(… W6 2・W7 8・… W10 9・… W17 14 …)。本台帳の 14 行は…」 | 「121 行の自由文(… W6 3・W7 13・… W10 10・… W17 6 …)。**第306 更新(Q141・第307)**: 09-09 の 122 行から段の改版で W6 +1・W7 +5・W10 +1・W17 −8(差し引き −1)。本台帳の 14 行は設計書が感度試験を宣言したものだけ(build_manifest の 15 行に当たる+RAKE が 1 行)で、残り 105 行は…未宣言の穴。判定は build_manifest_judgment(D-44 (a)・(c))」 |
| `note_2026_09_09`(新) | — | 旧 `note` をそのまま残した |
| `open_questions` の 2 本目 | 「122 行のうち…14 行だけ。残り 108 行の扱い…=親判断」 | 「121 行(09-09 は 122・第306 の段の改版で −1)のうち…14 アンカー(build_manifest の 15 行)+RAKE 1 行だけ。残り 105 行の扱い=D-44 (a)(第229 決定)で一括判定・(c) 依存グラフ(第307)の次はユーザー判断」 |

既存の 19 行・過程の id・`build_manifest_judgment` の判定列は触っていない。

## 第 4 批② Q142: R-23 第3批 §5 の外への伝播 5 か所

作法は第 3 批と同じ(設計書は本文を直し「第307 訂正・R-23 第3批 #N」の印・`v2_draft_proposal.md` も設計書扱い)。根拠は答申 §5 の写しだけ。全文の前後は [r23_batch3_propagation.json](r23_batch3_propagation.json)。

| # | 場所(ファイル:行) | 変更前 | 変更後 | 根拠 |
|---|---|---|---|---|
| 15 | `design/v2_draft_proposal.md:60` | 根拠: AC Unity/Hitmanの商用実証=LLM予算配分則そのもの・憲法1の実装形。 | 根拠: AC Unity の商用実証(プール入替=昇格機構の先行)=LLM予算配分則そのもの・憲法1の実装形。(**第307 訂正・R-23 第3批 #15**: Hitman Absolution の公開資料は群衆 1200 体/1 群衆・同画面 500 体・目標は「プレイヤーが群衆と NPC を見分けられないこと」で、**on-demand 昇格の明記は見つからない**=昇格の先行は AC Unity) | §5 #15(GDC Vault / Fauerby スライド) |
| 14 | `design/v2_draft_proposal.md:72` | (全ログを読まずに種別検索——UE Replayのイベント索引と同型・kind列+チャンク統計で実現) | (全ログを読まずに種別検索——**SC2 の game.events / tracker.events / message.events 分離**と同型・kind列+チャンク統計で実現。**第307 訂正・R-23 第3批 #14**: 旧「UE Replayのイベント索引と同型」=Epic の DemoNetDriver 公式ドキュメントにイベント検索の記述は無い(text tags はリプレイ一覧の検索用)) | §5 #14(Epic DemoNetDriver ページ) |
| 18 | `design/v2_draft_proposal.md:79` | - **GlassBox規律**: 画面に見えるものは常にシムの1:1表現。ビューアの独自演出・補間は禁止。 | - **GlassBox規律**: 画面に見えるものは常にシムの1:1表現。ビューアの独自演出・補間は禁止。(**第307 訂正・R-23 第3批 #18**: **v2 の自前の規律として宣言**する。原典 SimCity GlassBox の逐語は「every aspect of the game is an agent that reports back to the underlying simulation」=表示物がシムへ報告する向きで、向きが逆) | §5 #18(EA 公式・GDC 2012) |
| 18 | `design/v2-redesign.md:387` | ・GlassBox規律(見えるもの=シムの1:1)。段階=deck.gl 2D | ・GlassBox規律(見えるもの=シムの1:1・**v2 側の規律として宣言**=原典 SimCity GlassBox の逐語は向きが逆(第307 訂正・R-23 第3批 #18))。段階=deck.gl 2D | §5 #18(EA 公式・GDC 2012) |
| 14 | `design/v2-inventory-and-bottlenecks.md:21` | リプレイ(UE Replay/SC2/LoLの三層収束・checkpoint時間スライス・タグ付き索引) | リプレイ(UE Replay/SC2/LoLの三層収束・checkpoint時間スライス・タグ付き索引。**第307 訂正・R-23 第3批 #14**: タグ付きイベント索引の先行は SC2 の events 分離で、Epic の DemoNetDriver 公式ドキュメントにイベント検索の記述は無い) | §5 #14(Epic DemoNetDriver ページ) |

## 第 4 批③ D-44 (c): 依存グラフ(判定不能 105 行に「エンジンが読むか」)

**方法**(`tools/c8/sensitivity.py` の `engine_read_graph`・`attach_read_graph`・`python tools/c8/sensitivity.py --read-graph --out docs/bench/c8`):

1. 各構築段の出力ファイル(build_manifest の `outputs`・日付つきの `w9_shadow_<日付>.npy` は `w9_shadow_` で探す)を、`src/shibuya` の全 `.py` の**コードの文字列リテラル**(AST=docstring と式文の文字列は除く)で探す。
2. エンジン側(`engine`・`perception`・`agents`・`economy`・`world`)に名指しがあれば「読む(直接)」。構築モジュール(`build/`)の名指しは、そのモジュールの段(ファイル名 `wN_`・補助モジュールは `BUILD_MODULE_STAGE` の表)が**下流の段としてその出力を読む**辺にする。
3. 推移: 下流の段がエンジンに届くなら上流も「読む(推移)」。
4. 「読まない」=エンジン側の読み口が無く、出力を読むのが構築の検査・画像の段(W18〜W20)だけで、その段自身も検査・画像の段。**読み口が見つからないだけなら「不明」**(推測で読まないにしない)。
5. **段の単位**で判定する(段のどれか 1 つの出力が読まれれば、その段の行は全部「読む」=除きすぎない側)。

**結果**(判定不能 105 行):

| 判定 | 行数 |
|---|---|
| エンジンが読む | **96**(直接 95・推移 1=W5#2 が W5 → W11) |
| **読まない** | **9** |
| 不明 | **0** |

段ごと(判定不能の行のある段と、推移の経路の段):

| 段(判定不能の行) | 判定 | 届き方 | エンジン側の読み口(ファイルごとの最初の行) | 出力を読む下流の構築段 |
|---|---|---|---|---|
| W0(0) | 読む | 直接 | `world_crs.json ← world/assets.py:748` | — |
| W1(2) | 読む | 直接 | `w1_edges.parquet ← world/assets.py:90`・`w1_nodes.parquet ← world/assets.py:89` | W2・W3・W5・W6・W10・W11・W12・W18・W20 |
| W2(3) | 読む | 直接 | `w2_cells.parquet ← perception/renderer.py:653`・`w2_cells.parquet ← world/assets.py:91` | W3・W5・W6・W8・W11・W15・W16・W18・W20 |
| W3(3) | 読む | 直接 | `w3_cell_dist.npy ← world/assets.py:93`・`w3_next_hop.npy ← world/assets.py:92` | — |
| W4(0) | 読む | 推移 W4→W6 | — | W6・W8・W9・W16・W18 |
| W5(1) | 読む | 推移 W5→W11 | — | W11 |
| W6(2) | 読む | 直接 | `w6_org.parquet ← economy/ledger.py:163`・`w6_poi.parquet ← perception/renderer.py:654`・`w6_poi.parquet ← world/assets.py:94` | W7・W8・W14・W15・W16・W17・W18・W20 |
| W7(12) | 読む | 直接 | `w7_plan_spec.parquet ← world/assets.py:737` | W14・W17・W18 |
| W8(8) | 読む | 直接 | `w8_t1_cell.parquet ← perception/renderer.py:656`・`w8_t1_cell.parquet ← world/assets.py:471`・`w8_targets.parquet ← perception/renderer.py:655`・`w8_targets.parquet ← world/assets.py:471` | W15・W18・W20 |
| W9(5) | 読む | 直接 | `w9_shadow_2026-07-28.npy ← world/assets.py:882` | W18・W20 |
| W10(9) | 読む | 直接 | `w10_noise_stage_day.npy ← perception/renderer.py:864`・`w10_noise_stage_day.npy ← world/assets.py:553`・`w10_noise_stage_night.npy ← perception/renderer.py:864`・`w10_noise_stage_night.npy ← world/assets.py:553`・`w10_street_points.parquet ← perception/renderer.py:657`・`w10_street_points.parquet ← world/assets.py:552` | W8・W9・W18・W20 |
| W11(4) | 読む | 直接 | `w11_station_exits.parquet ← perception/renderer.py:658`・`w11_station_exits.parquet ← world/assets.py:735`・`w11_station_graph_nodes.parquet ← world/assets.py:734` | W8・W12・W15・W16・W18・W20 |
| W12(6) | 読む | 直接 | `w12_external_nodes.parquet ← world/assets.py:736`・`w12_timetables.parquet ← world/assets.py:733` | W16・W17・W18 |
| W13(5) | 読む | 直接 | `w13_weather_days.parquet ← world/assets.py:731`・`w13_weather_hourly.parquet ← perception/renderer.py:659`・`w13_weather_hourly.parquet ← world/assets.py:732` | W9・W18 |
| W14(7) | 読む | 直接 | `w14_signage.parquet ← perception/renderer.py:759` | — |
| W15(10) | 読む | 直接 | `w15_cell_static.parquet ← perception/renderer.py:762` | — |
| W16(14) | 読む | 直接 | `w16_population.parquet ← agents/population.py:53` | W17・W18 |
| W17(5) | 読む | 直接 | `w17_schedule.parquet ← agents/weekly.py:58` | — |
| W18(5) | 読まない | — | — | W20 |
| W19(2) | 読まない | — | — | W20 |
| W20(2) | 読まない | — | — | — |

**読まない 9 行**(=構築の検査・画像の段=W18 カタログ索引・W19 凍結記録・W20 受入画像/表。どれもエンジン側に読み口が無く、出力を読むのは W20 だけ):

| 行 | expedient |
|---|---|
| W18#1 | 深度=カタログ宣言値(実測ではない) |
| W18#2 | 重み関数 w=1+log10(1+N_real) 上限6・N_real 不明は w=1 |
| W18#3 | クラス名の別名表(段階ヘッダの表記ゆれ吸収)は手書き |
| W18#4 | N_sim の単位突合(quantity_comparable)は手書き |
| W18#5 | VERIFIED は構築時に評価しない(全 false) |
| W19#1 | sealed_utc は固定パラメータ(実行時刻ではない) |
| W19#2 | データ資産表は各段階モジュールの入力定数から組む(段階が定数を持たない入力は落ちる) |
| W20#1 | 画像の配色・分解能(5m/画素)は目視用で判断には使わない |
| W20#2 | 騒音場の階調範囲 40-85 dB に固定(自動スケールにしない) |

- 出力は `build_manifest_judgment` に列を足した: 判定不能の行に `engine_reads`(reads/not_read/unknown)・`engine_reads_via`(直接/推移 W5→W11/構築の検査・画像の段だけ)・ブロック `read_graph`(規則の文言・集計・読まない行の一覧・段ごとの読み口と下流の段)。**既存の判定列(verdict など)は 1 バイトも変えていない**(行ごとに比べて確認)。Markdown の表の「判定」欄に「/エンジンが読む(直接)」などを足した。
- 参考(エンジン側 5 パッケージの外の名指し): 無し(`llm/contract.py` の `w2_cells.parquet` は docstring とコメントだけ=AST で外れる)。
- テスト: `tests/c8/test_sensitivity_ledger.py`(+4 本=3 値・集計・直接+推移=読む・読まないは W18〜W20 だけ・段の証拠(読み口か推移)/検査器が不正な値を捕まえる/AST が docstring と式文の文字列を数えない・日付つきの名前の字句/いまの src から作り直すと台帳と一致)・Q141 の検査(`count` 121・旧注記・open_questions)。

**ついでの修正(事後報告)**: `tools/c6/c6lib.write_outputs` が Windows で CRLF を書いていた(第306 で `docs/bench/c8/sensitivity_v1.{json,md}` を手で LF に直した原因)。`newline="\n"` を足して LF で書くようにした(出力の中身は同じ・`tools/c6` の他の計器の出力も同じ関数)。

## 第 4 批 テスト本数と全体

全体(`-m "not gpu and not slow"`・p6 400k を除く・junit): **3,300 件・failures 0・errors 0・skipped 1(既存の W10 較正)・exit 0**(第306 の 3,296 件 + 新規 4 件=③ 4・①は既存の検査を直した)。

## 第 4 批 宣言と問い

宣言: ① 旧注記は `note_2026_09_09` に残す ② 伝播は §5 の写しだけ ③ 依存グラフは段の単位・読み口=コードの文字列リテラル(AST)・「読まない」は W18〜W20 に限る。問いは報告の Q145〜。

## 第 4 批 再現

```
python tools/c8/sensitivity.py --read-graph --out docs/bench/c8   # D-44 (c)(台帳 tools/c8/sensitivity_v1.json に書く)
```

---

# 第 5 批(第307 の問いの決め → Q146・D-107 (a))

第 4 批は第307(c034d58)でコミット済み。親の決め: Q145 出力単位の細分は繰り延べ/**Q146 3 分類を作る(この回)**/Q147 読まない 9 行の登録は構築仕様書 §0-7 の文言に触るのでユーザーへ。本批は解析と計器(エンジンの挙動は不変・新しい再構築なし)。

## 第 5 批① Q146: エンジンが読む 96 行の 3 分類(**実装役の自前の構成=未リサーチ**)

**表**: `tools/c8/expedient_triage_v1.json`(96 行=行ごとに 3 分類・対照の候補(何を何と比べるか)・費用の見込み[秒])。`python tools/c8/sensitivity.py --triage --out docs/bench/c8` で台帳 `build_manifest_judgment` の**読む行だけ**に列 `triage`(class/control/cost_seconds_estimate)と集計 `triage_summary` を足した。**既存の列(判定・依存グラフ)は 1 バイトも変えていない**(行ごとに比べて確認)。Markdown の表の「判定」欄に「/(i) 構築の再計算」など・「備考」欄に対照の候補と費用。

**分け方(自前・未リサーチ)**:
- **(i) 構築段階の再計算で対照が測れる**=既存の 5 本のランナーの形(宣言値 vs 対照で、入力側の分布の JSD を比べる)。LLM の呼びは要らない。実データの対照が無い行は、宣言値をずらす対照(±50 m・±10%・±5 歳など=S-W15-TEMP の +1.5℃ と同じ形)を置いた。
- **(ii) ランが要る**=入力側の JSD では効きが決まらない(権限・違反の可否・指令の数・世帯の効きのように**行為の結果**で効く行)か、対照を作るのに **LLM の再生成**が要る行(W14/W15 の文の長さ・枠・W17 の型)。5,000 体の CSB 対照へ。
- **(iii) 対照を定義できない**=門(検査の規則・閾値)・文面(プロンプト・語彙の割当)・範囲の宣言(1 日モード・報告しない指標)・コードの形(二重定義)。

**集計**:

| 分類 | 行数 | 段の内訳 |
|---|---|---|
| (i) 構築の再計算 | **66** | W1 2・W2 3・W3 3・W5 1・W6 2・W7 9・W8 8・W9 5・W10 8・W11 4・W12 6・W13 4・W16 10・W17 2 |
| (ii) ランが要る | **13** | W7#3・#4・#12・#13(権限・違反の可否・騒音 dB の機構)/W14#2・W15#2〜#6(LLM の再生成)/W16#10(指令の数)・#14(世帯)/W17#1(週次表の型=再生成) |
| (iii) 対照を定義できない | **17** | W10#8・W13#4(語彙の割当)/W14#1・#3・#4・W15#1・#9(文面)/W14#5・#6・#7・W15#7・#10・W16#6・#15(門・閾値・報告の定義)/W15#8(二重定義)/W17#2・#6(範囲の宣言) |

**(i) の費用の見込み(未測)**: 既存の記録(構築の通し 12.3 s・W8 前計算 1.15 s・W9 影 数分・W16 対照 0.29 s・W17 再取り込み 約 90 s)から置いた目安。
- 1 行ずつ(OFAT)なら **計 3,607 秒(約 60 分)**。うち W9(影)が 2,700 秒(5 行・1 行 300 秒・細かいラスタは 1,200 秒)。
- 段ごとの最大(同じ段の行をまとめて 1 回の再計算に畳めるなら): W1 35・W2 35・W3 30・W5 5・W6 5・W7 2・W8 10・W9 1,200・W10 20・W11 5・W12 1・W13 1・W16 60・W17 90 秒。
- 対照の値そのもの(±50 m・DECK 眼高 +6 m・夕ピーク −20% など)も**未リサーチの仮の値**。

テスト: `tests/c8/test_sensitivity_ledger.py`(+2 本=読む行だけに 3 値・集計・(i) だけが費用を持ち合計が合う・未リサーチの明記・表の鍵が読む行と一致/検査器が不正な分類を捕まえる)。

## 第 5 批② D-107 (a): 群・規範の計器(manifest `group_norms`・**読むだけ**)

**入れたもの**: `src/shibuya/engine/norm_meter.py`(`GroupNormMeter`)を `engine.run` の tick の骨格の 3 か所で呼ぶ(① 応答の適用の直前=`observe_actions`・⑦ `resolve.apply` の後=`observe_results`・在圏の標本の後=`observe_tick`)。manifest に `group_norms`(列追加のみ)・費用は `phase_seconds["group_norms"]`(壁時計=manifest には載せない)。

| 計器 | 定義(宣言) |
|---|---|
| (a) 同行検出 | 同セル ∧ 同じ移動先(`activity` MOVING かつ `target_node` ≥ 0 が同じ)∧ 距離 ≤2 m が**連続 5 分以上**の組(R-36 の同席と同じ粒度)。5 分に達した回数・異なる組の数・同行中の体・分 ÷ 目的地つき移動の体・分・群の大きさ(組の連結成分)× 分。照合値 Moussaïd 2010(55%/70%)は並べるだけ。A1 会話グループの大きさ(`ConversationManager.size_hist`)も記録だけ(holdout) |
| (b) 文脈別行動エントロピー | 場所の種別(店=在店か列/駅=駅出口セル(W11)かホームのセル=27 セル/街路=それ以外の在圏)× 時(1 時間)ごとの、**適用した行為**の分布のエントロピー[bit]と最頻行為の占有率(D-68 の M3b と同じ計算)。舞台外・乗車中は数えない |
| (c) 役割語/NO_PERMISSION | 役割語の行為(語彙の版の役割語コード)の件数と `resolve.apply` の後の結果(成立/権限なし/その他)・種別の内訳 |
| (d) 伝播到達 | 看板の露出(`familiarity_summary` の露出の鍵)・口コミ(`wom` の数)・顕著行為の社会伝播(`salient_events`・`noticed`・`dispatches`)の**既存の計数の集約** |
| 規範の 2 層 | 経験的期待((b))は測る/規範的期待(逸脱への反応)は機構が無く測れない=**「慣習」と宣言**(規範とは言わない) |

逐次ループの新設なし: 対の列挙は (セル, 移動先) の群ごとの対を**配列で**作る(1 tick の対の候補が 2,000,000 を超えたら同行の計数を飛ばして数える=宣言)・群の連結成分はラベルの伝播(群の直径ぶんの反復)・行為は `np.unique` と `bincount`(行為コードの種類ぶん ≤26 の反復)・役割語の結果は役割語の行の数ぶん(1 tick に数件)。

**既定が動くか**: **動かない**(読むだけ)。
- **HEAD c034d58 との byte 比較**([d107_byte_check.json](d107_byte_check.json)・`--axis plain`=既定どうし・作業木は 2 回): v3 既定・classical・v1 既定・v3+memory+relations の **4 構成すべてで final・呼数・blocks・calls 14 列が一致**(2 回とも)。
- テスト `test_the_meter_only_reads_the_run_state`: 計器の 3 つの口を空にしたランと final・呼数が一致・同じランを 2 回回すと `group_norms` が一致(決定論)。
- mock の W17 golden(帰無腕 72cb9cd5・v3 993276d5)と classical の golden は全体テストで通る。
- **費用**: 計器の壁時計 **0.34〜0.37 秒/ラン**(mock 5,000 体×1,440 tick=ラン全体 33〜47 秒の約 1%)。HEAD と作業木を交互に 2 回ずつ回したラン全体の壁時計は 32.9/33.9 秒 vs 32.8/33.0 秒(差は雑音の内)。1 tick の対の候補は最大 1,166(mock)・941(classical)=上限 2,000,000 の 0.06%。

**値**([d107_norms.json](d107_norms.json)・5,000 体・seed 1・v3・判定しない。mock は 12 語から一様に引く=エントロピーは log2(12)=3.585 bit に張り付く):

| 計器 | mock v3 既定 | classical v3 | mock v3 層 on(伝播の腕) |
|---|---|---|---|
| final・呼数 | 993276d5・69,978 | 60e72227・102,021 | 6516d90d・73,806 |
| (a) 同行 5 分に達した回数(異なる組) | 4,198(4,182) | 1,681(1,623) | 4,226(4,201) |
| (a) 同行中の体・分 ÷ 目的地つき移動の体・分 | 30,584 ÷ 249,781 = **0.122** | 14,205 ÷ 348,202 = **0.041** | 29,923 ÷ 247,878 = **0.121** |
| (a) 同行の群の大きさ(群 × 分) | 群・分 12,034: 2 人 70.0%・≤4 人 94.7%・最大 15 人 | 群・分 6,354: 2 人 83.6%・≤4 人 98.9%・最大 9 人 | 群・分 12,099: 2 人 72.5%・≤4 人 95.7%・最大 13 人 |
| (a) A1 会話グループの大きさ(記録だけ) | 2 人 205 | 2 人 671 | 2 人 222 |
| (b) 街路(終日) | n 20,872・H 3.584 bit・最頻 就寝 0.086(時別の H 中央 3.58) | n 60,075・H 1.497 bit・最頻 なし 0.650(時別の H 中央 1.52) | n 21,498・H 3.585 bit・最頻 並ぶ 0.086(時別の H 中央 3.58) |
| (b) 店(終日) | n 4,949・H 3.584 bit・最頻 なし 0.087(時別の H 中央 3.55) | n 7,626・H 1.409 bit・最頻 なし 0.671(時別の H 中央 1.32) | n 5,441・H 3.584 bit・最頻 購入 0.089(時別の H 中央 3.55) |
| (b) 駅(終日) | n 44,034・H 3.585 bit・最頻 なし 0.086(時別の H 中央 3.58) | n 34,162・H 1.490 bit・最頻 なし 0.613(時別の H 中央 1.33) | n 46,717・H 3.585 bit・最頻 なし 0.086(時別の H 中央 3.58) |
| (c) 役割語の行為・NO_PERMISSION | 0・0 | 0・0 | 0・0 |
| (d) 伝播到達 | 看板の露出 —(層 off) / 口コミ —(層 off) / 顕著行為 0・気づき 0・出動 0 | 看板の露出 —(層 off) / 口コミ —(層 off) / 顕著行為 0・気づき 0・出動 0 | 看板の露出(入った回)85,189・描画 73,246 / 口コミ 発話 1,038・抽出率 0.0 / 顕著行為 27・気づき 736・出動 14 |
| 計器の壁時計(ラン全体) | 0.346 秒(32.27 秒) | 0.328 秒(47.07 秒) | 0.372 秒(55.75 秒) |

- **(c) 役割語**: mock・classical とも役割語の行為は **0 件**(mock は横断語 12 から引き、classical は役割語を返さない)=NO_PERMISSION も 0。**実 LLM(GPU)でしか値が出ない**。
- **(d) 伝播到達**: 既定のランは看板の露出(親しみの層)・口コミ(記憶の層)が**切れている**ので空・顕著行為は seed 1 で 0 件(5,000 体・1 日の期待値 1.5 件)。**伝播の腕**(親しみ・記憶・店の記憶・関係 on・顕著行為の発生率 30/万体/日)では集約が動く: 看板の露出(入った回)85,189・描画 73,246・顕著行為 27 件 → 気づき 736・出動 14。口コミは mock の発話から店名が抽出されない(発話 1,038・抽出率 0.0)=実 LLM で値が出る。

テスト: `tests/engine/test_norm_meter.py`(新規 7 本=エントロピーの式/同行は同セル・同じ移動先・2 m・連続 5 分が要る(3 m 離れた体・別の移動先は数えない・群の大きさ)/途切れたら数え直す/場所 × 時の数え方(店・駅・街路・舞台外)/役割語の結果と NO_PERMISSION/「慣習」の宣言と判定しない/読むだけ=計器を空にしても final 一致・決定論)。

## 第 5 批 テスト本数と全体

全体(`-m "not gpu and not slow"`・p6 400k を除く・junit): **3,309 件・failures 0・errors 0・skipped 1(既存の W10 較正)・exit 0**(第307 の 3,300 件 + 新規 9 件=① 2・② 7)。byte-check は計器の要約だけの直し(1 種だけのときのエントロピーを −0.0 でなく 0.0 に・伝播の集約の鍵)の後にも回し直した(同じ結果)。

## 第 5 批 宣言と問い

宣言: ① 3 分類・対照の候補・費用の見込みは実装役の自前の構成(未リサーチ・未測)② 場所の種別は 店=在店か列/駅=駅出口セルかホームのセル/街路=それ以外 ③ 同行は連続 5 分・2 m・同じ移動先(R-36 と同じ粒度)④ 規範は「慣習」と宣言(逸脱への反応を測る機構が無い)。問いは報告の Q148〜。

## 第 5 批 再現

```
python tools/c8/sensitivity.py --triage --out docs/bench/c8
D=docs/bench/analysis/small-fixes-2026-09-29
python $D/small_fixes_measure.py norms --out $D/d107_norms.json
python $D/small_fixes_measure.py bytecheck --axis plain --head-src <HEAD c034d58 の src と docs/bench/anchors を展開した場所の src> --head-label c034d58 --scratch <作業用の場所> --out $D/d107_byte_check.json
```

---

# 第 6 批(第308 の問いの決め → Q148・Q150)

第 5 批は第308(5eabb42)でコミット済み。親の決め: Q148 足す(この回)/Q149 GPU 後の項目に追加済み/Q150 on/off の口を足し候補数を実測(39 万体の丸 1 日は回さない)/Q151 (i) 66 行の再構築はユーザーの許可待ち。本批は計器だけ(エンジンの挙動不変・再構築なし)。

## 第 6 批① Q148: 瞬間の群れ歩きの計器(`norm_meter` に追加・読むだけ)

**定義(宣言)**: 同じ tick に「2 m 内 ∧ 同方向(進行方向=**直前の tick からの変位**の向き・角度差 ≤45°)∧ 両方が歩いている(`activity` MOVING かつ変位 > 0・在圏)」の相手が 1 人以上いる歩行者の割合=**体・分 ÷ 歩行者の体・分**、と群の大きさ(同じ条件の組の連結成分)の分布。Moussaïd 2010 の「集団で歩く歩行者の割合(55%/70%)」に寄せた**瞬間の**指標。node 幾何では、同じノードに居て同じ辺を進む体が距離 0・角度 0 になる。

- **第308 の同行検出(同セル ∧ 同じ移動先 ∧ 2 m 内 ∧ 連続 5 分)はそのまま残した**。manifest `group_norms` に両方(`cowalk` と `instant_group_walk`)を載せ、`instant_group_walk.definition` に定義の違い(瞬間/持続・方向/行き先)を書いた。Moussaïd の 55%/70% は参照(`reference_moussaid_2010_group_share`)=判定しない。
- 組の候補: 2 m 格子で自分の格子と前向き 4 格子(計 5)だけを配列で突き合わせる(格子をまたぐ 2 m 内の組も拾う=テストで固定)。候補が 2,000,000 を超える tick は数えない(第308 と同じ宣言)。群は第308 と同じラベルの伝播(`_components` に切り出して両方で使う)。

**値**([q148_norms.json](q148_norms.json)・5,000 体・seed 1・v3・判定しない):

| 計器 | mock v3 既定 | classical v3 | mock v3 層 on |
|---|---|---|---|
| final・呼数 | 993276d5・69,978 | 60e72227・102,021 | 6516d90d・73,806 |
| **瞬間の群れ歩き**: 群れて歩く歩行者の割合(体・分) | **0.290** | **0.214** | 0.292 |
| 歩行者の体・分の内訳 独り/2/3/4+ | 0.710 / 0.152 / 0.061 / 0.077 | 0.786 / 0.141 / 0.042 / 0.031 | 0.708 / 0.157 / 0.062 / 0.074 |
| 群(群・分)のうち 2 人の割合 | 0.683(群・分 25,850) | 0.776(28,412) | 0.691(26,061) |
| 1 tick の組の候補の最大 | 974 | 1,026 | 929 |
| 同行(5 分連続・同じ移動先)の割合(第308・不変) | 0.122 | 0.041 | 0.121 |
| 参照 Moussaïd 2010 | 0.55 / 0.70 | 同 | 同 |

- 瞬間の割合は 5 分連続の割合より 2.4〜5.2 倍大きい(瞬間は「いまたまたま 2 m 内で同じ向き」も数える)。どちらも 0.55/0.70 より小さい(判定しない)。
- 計器の壁時計は第 5 批の 0.33〜0.37 → **0.68〜0.74 秒/ラン**(瞬間の指標の分で約 2 倍・1,440 tick の平均 0.47〜0.51 ms/tick・ラン全体 34〜56 秒の約 1.3〜2%)。

### ①′ 値の読み方の診断: 既定の node 幾何では「2 m 内」がほぼ「同じノードに重なる」になる

既定の幾何(`--geometry node`)では位置の確定が `r.xy = node_xy[node]`(`engine/resolve.py`)=**歩く体はいつもどこかのノードの座標の上に居る**(辺の途中の位置を持たない)。そこで、条件を満たした組の距離と群の成員の重なりを外から数えた([q148_colocation_diag.py](q148_colocation_diag.py) → [q148_colocation.json](q148_colocation.json)・計器の本体は変えない・final は計器 on のランと同じ)。比較のため C9 edge 幾何(`--geometry edge`=辺の上の位置を持つ・既存の腕)も 1 本回した。

| 欄 | node・5,000 体・1 日 | node・39 万体・最初の 60 tick | edge・5,000 体・1 日 |
|---|---|---|---|
| final | 993276d5 | 2e5d3efa | 25814475 |
| 瞬間の群れ歩きの割合 | 0.290 | 0.627 | **0.022** |
| 条件を満たした組(tick ごとの延べ) | 76,554 | 128,251 | 1,178 |
| そのうち**距離 0(同じ座標)** | **95.4%** | **99.7%** | 0.3% |
| 群の成員のうち同じ座標に 2 体以上いる体 | 98.9% | 99.7% | 0.6% |
| 20 人以上の群(回数・上位の大きさ/座標の数) | 2 回・24 人/2 点・20 人/2 点 | 56 回・152 人/1 点・120 人/1 点・118 人/1 点 | 0 回 |
| 5 分連続の同行の割合(第308 の計器) | 0.122(4,198 回) | 0.318(6,260 回) | **0.0009(16 回)** |
| 歩行者の体・分 | 232,518 | 22,611 | 96,686 |

- **読み方**: 既定の node 幾何での瞬間の群れ歩き(0.29)は、ほぼ全部が「同じ tick に同じノードに、ほぼ同じ向きから着いた体」の数=**並んで歩く集団の検出ではなく、ノードでの重なりの計数**。39 万体の 152 人の群は 1 点に重なった 152 体。第308 の 5 分連続の同行(0.122)も同じ理由で node 幾何の重なりに支配されている(edge 幾何では 0.0009)。
- edge 幾何では瞬間 0.022・5 分連続 0.0009 で、Moussaïd の 0.55/0.70 の桁に届かない(判定しない)。edge の歩行者の体・分が node の 4 割なのは、変位 0 の体(辺の上で止まった体等)を歩行者に数えないため(未検証の推定)。
- 計器の定義・既定は**変えていない**(どちらで読むか・注記の仕方は問い Q153)。

テスト: `tests/engine/test_norm_meter.py`(① の分 +2 本=2 m 内 ∧ 同方向 ∧ 両方が歩く(遠い体・逆向きは数えない・最初の tick は方向が無い・独り/群の大きさ)/格子をまたぐ 2 m 内の組を拾う・動かない体は歩行者に数えない)。

## 第 6 批② Q150: `--group-norms {on,off}` と 39 万体の候補数の実測

**切替口**: `run_day(group_norms=…)`・`shibuya.cli` と `shibuya.engine.run` の `--group-norms {on,off}`(既定 on=第308 のまま)。off は計器を作らず 3 つの口を通さない(manifest `group_norms` = `{"enabled": False}`・`phase_seconds` に計器の欄が無い)。on の manifest に `"enabled": True` を足した(列追加)。`phase_seconds["group_norms_tick_ms_max"]`(1 tick の最大・壁時計=manifest には載せない)。

**byte 一致**:
- **on と off**: テスト `test_group_norms_switch_off_is_byte_identical`(final・呼数が一致・off の manifest が `{"enabled": False}`・`"maybe"` は ValueError・2 つの CLI に口がある=② の分 +1 本)・39 万体の 60 tick でも on/off の final が一致(下)。
- **HEAD 5eabb42 との byte 比較**([q148_byte_check.json](q148_byte_check.json)・`--axis plain`=既定どうし・作業木は 2 回): v3 既定(993276d5・69,978)・classical(60e72227・102,021)・v1 既定(0a52a4d3・60,970)・v3+memory+relations(e4f84d1d・72,940)の **4 構成すべてで final・呼数・blocks・calls 14 列が一致**(2 回とも)。

**39 万体の実測**([q150_norms_full.json](q150_norms_full.json)・W16 全母集団 390,067 体・mock v3 既定・**初期化+最初の 60 tick だけ**=0:00〜1:00 の深夜・丸 1 日は回していない=宣言):

| 欄 | on | off |
|---|---|---|
| final・呼数 | 2e5d3efa…・7,991 | **同じ**・7,991 |
| 初期化+60 tick の壁時計 | 20.4 秒 | 21.7 秒 |
| 計器の費用 | **平均 11.3 ms/tick・最大 17.9 ms/tick**(60 tick で 0.68 秒) | — |
| 同行(5 分連続)の組の候補/tick の最大 | **5,611** | — |
| 瞬間の群れ歩きの組の候補/tick の最大 | **12,290** | — |
| 上限 2,000,000 を超えて飛ばした tick | 0・0 | — |
| 参考の値(深夜 1 時間だけ) | 同行の割合 0.318・瞬間の群れ歩き 0.627(独り 0.373・4 人以上 0.485・最大の群 152 人) | — |

- 候補数は上限の **0.3%(5,611)と 0.6%(12,290)**。ただし**深夜 0 時台だけ**の値(歩行者の体・分 22,611/60 tick)で、昼の歩行者は桁が増え、1 点に重なった k 体の群は組の候補を k(k−1)/2 個つくる(152 体で 11,476)=昼の最大は測っていない(問い Q152)。
- 深夜の 39 万体では瞬間の群れ歩きが 0.63 で、4 人以上の群が歩行者の体・分の 48% を占め、152 人の群がある=**1 点に重なった 152 体**(①′ の診断で確認・組の 99.7% が距離 0)。

## 第 6 批 テスト本数と全体

全体(`-m "not gpu and not slow"`・p6 400k を除く・junit): **3,312 件・failures 0・errors 0・skipped 1(既存の W10 較正)・exit 0**(第308 の 3,309 件 + 新規 3 件=① 2・② 1)。byte-check(HEAD 5eabb42 との比較)は全体テストの前に回した。

## 第 6 批 宣言と問い

宣言: ① 進行方向=直前の tick からの変位(0 の体は歩行者に数えない)・同方向=角度差 ≤45°・2 m・両方が MOVING ② 5 分連続の同行はそのまま・両方を載せて定義の違いを注記 ③ `--group-norms` の既定は on ④ 39 万体は最初の 60 tick だけ(深夜)⑤ ①′ の診断は計器を外から包むだけ(本体・既定は変えない)・edge の歩行者の体・分の差の理由は未検証。問いは報告の Q152〜。

## 第 6 批 再現

```
D=docs/bench/analysis/small-fixes-2026-09-29
python $D/small_fixes_measure.py norms --out $D/q148_norms.json
python $D/small_fixes_measure.py norms-full --out $D/q150_norms_full.json      # 39 万体・初期化+60 tick
python $D/q148_colocation_diag.py --out $D/q148_colocation.json                # ①′ node/edge の重なりの診断
python $D/small_fixes_measure.py bytecheck --axis plain --head-src <HEAD 5eabb42 の src と docs/bench/anchors を展開した場所の src> --head-label 5eabb42 --scratch <作業用の場所> --out $D/q148_byte_check.json
```
