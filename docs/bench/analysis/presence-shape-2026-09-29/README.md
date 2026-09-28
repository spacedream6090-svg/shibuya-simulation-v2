# 在圏の形の台帳 — 退出を歩かせる・退去の効果・KDDI 写像の感度腕(2026-09-29)

正典: [実装アジェンダ](../../../design/v2-presence-shape-implementation-agenda.md)(§0 の 9a 行・§1 の 1〜6・§3)・上位=[壁打ちの決定記録](../../../design/v2-wallbounce-decisions-2026-09-25.md) §2 D-112 ④/D-115(09-25 ユーザー決定=「カレンダー化までの中間段として作り込みすぎない」)。前提=計画実行層(D-66・[presence.py](../../../../src/shibuya/engine/presence.py))・D-51 乗車の意図・段 2c の意図保持(#54)。
計測は mock 5,000 体・seed 1・W17 v2・語彙 v3・空腹 energy・`cli.run`(呼数無制限)。スクリプト [presence_measure.py](presence_measure.py) → [arms15_leave.json](arms15_leave.json)(15 腕 × 退去の効果 on/off・欄ごとの差)・[leave_byte_check.json](leave_byte_check.json)(HEAD e784f65 との byte 一致)・[exit_arms.json](exit_arms.json)(immediate / walk_to_platform・在圏 journal の形)。壁時計は同じ PC の 1 回の値(決定論でない)。**holdout(KDDI)は判定しない**=開封済みの c7-day-4 の比較記録を並べるだけ。

## §9a 退出を歩かせる(D-115 ①)+退去の効果(D-112 ④)(実装役 Opus 5.5・第302)

### 0. 入れたもの

| 口 | 中身 |
|---|---|
| 退出の形 `--exit-mode walk_to_platform`(既定 `immediate`=不変) | 計画実行層の DEPART で、即時 `rail_depart` の代わりに**その体の路線(`line_of_agent`)のホーム**への乗車の意図(D-51 の `board_line`=段 2c の乗車の意図の経路・Q19 のとおり別経路)を立てる(`resolve.begin_exit_walk`)。ホームに居れば乗車待ちへ・居なければそのホームの代表ノードへ歩く。着けば `_serve_board_queue` が受容関数 `accept_quota` を通して乗せる(満員=待ち続ける・運賃不足=`FARE_SHORT`・列車なし=待ちの打ち切り `NO_TRAIN`=既存の失敗コード)。**会話中は従来どおり繰り延べ**(≤ `EXIT_DEFER_LIMIT` 30 tick・解けたら歩き出す)・**買物/待ち行列は解いてから歩く**(`_depart_now` の前半を `_release_affiliations` に切り出して共有)。活動層は「目的地つき移動・到着まで」(`force_arrival`) |
| 即時への切り替え(作り込みすぎない) | ① 歩き出しから `walk_max_ticks`(=段 2c の意図の上限 `intent_max_ticks`・既定 60)を超えて乗れない → **その場で `rail_depart`**(TOO_FAR)② 乗車の意図が落ちた(LLM が保つ行為以外を選んだ・待ちの打ち切り・運賃不足・経路が途切れた)→ その場で `rail_depart`(会話中なら繰り延べてから)③ 非鉄道ゲートの体(線 −1)と、その線の便/ホーム/経路の無い体 → 即時(E3 と同じ=所要時間なし)。`board_intent` は未実装のまま(`NotImplementedError`) |
| 歩いている間の起床 | 歩いて乗る退出の体は**場所の変化(CELL_BLOCK)・到着満了(ACTIVITY_EXPIRY)・計画境界(PLAN_*)で起こさない**(段 2c の意図保持と同じ=着いたらエンジンが乗せる・退出そのものが計画境界の実行=即時の形で呼ばないのと揃える)。体(内受容)・会話・顕著行為・知人出現では起こす。`plan_flags` のビット `EXIT_WALK_FLAG`(1<<4)=歩いている間の「待機/なし」は歩みを止めない(`_apply_wait`・段 2c の Q20 と同じ) |
| 列車で出たとき | `RailProcess` の発車で、計画の退出で乗った体(`plan_exit_mask`)を LLM の乗車と分ける: 帰りの便(D-61)を付けず・`notify_departed_by_llm` で張り直さない(当日の DEPART は消費済み)→ `notify_departed_by_plan`。既定(immediate)ではマスクが空=従来の 2 行のまま |
| 到着側 | 変えない(出口セル round-robin のまま=D-115 ① の決め) |
| 退去の効果(D-112 ④・欠陥の修正=既定が動く) | `_apply_leave`=契約どおり**所属解除**: 在店(`poi_ref`)→ `release_indoor`・待ち行列(`queue_poi`)→ `balk_queue`(結果は OK に戻す=失敗しない行動)・会話中 → `engine.run` が会話マネージャの終了経路 `close_now(理由「退去」)`→ CLOSING → TERMINAL で閉じる・活動層=応答の活動欄が「なし」なら次の tick に満了(考え直す)。「帰る」の意味は持たない(域外へは出ない・語彙の説明はそのまま)。**切替口 `--leave-effect {on,off}`**(既定 on・off=第301 以前=旧 golden の再現) |
| manifest | `presence_exit`(`exit_mode`・内訳=歩き出し/ホームで待ちから/乗った/列車で出た/TOO_FAR で即時/意図が落ちて即時/繰り延べてから即時/ゲートで即時/便・経路なしで即時/日末に歩いている・乗って発車待ち・その他で域外/歩き直し・所要時間(歩き出し→乗車)と即時までの時間の分布・歩いている間に落とした起床と呼ばれた数・意図が落ちた体の直前の結果/行為・**出口セル/ホームセルの時別在圏と出口セルの密度段の最大**(両方の形で数える))・`leave_effects`(退去・在店を解いた・列を離れた・会話中だった・閉じたセッション)・活動層 `leave_expired` |
| CLI | `--exit-mode walk_to_platform`(説明の更新)・`--leave-effect` |

### 1. 既定の動き方(退去の分だけ)の証拠

**(i) 15 腕 × 退去の効果 on/off**([arms15_leave.json](arms15_leave.json)): off の final と呼数は **15/15 が 5 段目の記録と一致**(=動いたのは退去の効果だけ)。on は 15 腕とも動く(mock は 12 語から一様に引く=1/12 が退去)。

| 腕 | off=5 段目 | on | 呼数 off → on | 退去 | 在店を解いた | 列 | 会話中 | 閉じた(run の経路) | 「退去」で閉じた会話 off → on |
|---|---|---|---|---|---|---|---|---|---|
| v3_default | c9ab0538 = | 993276d5 | 69,603 → 69,978 | 5,892 | 409 | 8 | 13 | 1 | 83 → 94 |
| v3_activity_off | 69acc68c = | f746406e | 59,088 → 58,570 | 4,909 | 338 | 0 | 6 | 1 | 57 → 68 |
| v1_default | 91c33e23 = | 0a52a4d3 | 60,987 → 60,970 | 5,111 | 141 | 0 | 9 | 1 | 53 → 54 |
| v1_derive_v2_1 | 3f2f032f = | faada6a9 | 55,057 → 54,285 | 4,556 | 111 | 0 | 7 | 2 | 58 → 64 |
| v2 | 8858670b = | f4382c82 | 61,095 → 60,901 | 4,757 | 221 | 0 | 4 | 1 | 45 → 53 |
| v1_edge | 29c6f7e4 = | 6db51cbd | 54,189 → 54,150 | 4,502 | 103 | 0 | 5 | 1 | 47 → 48 |
| v2_edge | 43c4b776 = | d61923ed | 54,158 → 54,170 | 4,278 | 190 | 0 | 5 | 1 | 28 → 27 |
| v1_edge_plateau | 7e703865 = | e32d69e9 | 55,186 → 55,173 | 4,603 | 106 | 0 | 6 | 2 | 48 → 49 |
| old_*(6 腕) | 全部 = | 全部動く | 上の対応する腕と同じ呼数 | — | — | — | — | — | — |
| golden_null_arm | 18f88072 = | 72cb9cd5 | 100,509 → 100,439 | 8,414 | 167 | 0 | 12 | 6 | 90 → 104 |

- **欄ごとの差**(on と off の終わりの SoA を欄ごとにハッシュ): v1_default・v1_edge_plateau は 10〜11 欄(`energy_balance`・`fail_streak`・`fatigue`・`holdings`・`last_action`・`last_result`・`last_result_tick`・`money`・`refractory_until`・`since_meal_kcal`(・`transit_ref`))=**位置は動かない**(在店を解いただけで買物/食事の成否と金・空腹が変わる)。v3・v2・edge は 26〜35 欄(位置・活動・意図・乗車の意図まで)=解かれた体が別の行為をして軌跡が分かれる。38 欄の和集合は JSON の各行 `fields_changed_by_leave_effect`。
- 会話の「退去」での終了は**会話ターンの応答が退去**のときは既存の経路(`ConversationManager.utterance`)で既に閉じていた(off でも 83)。新しい経路(会話中の体が会話ターン以外の呼で退去を選んだ)は 1〜6 件/日。

**(ii) HEAD e784f65 との byte 比較**([leave_byte_check.json](leave_byte_check.json)):

| 構成 | HEAD → 作業木 | 呼数 | blocks | calls 14 列 |
|---|---|---|---|---|
| v3 既定 | c9ab05383accca2e → 993276d5e5bb5cbe **≠**(記録) | 69,603 → 69,978 | 5,389 → 5,394 行 | 全列が違う(退去の後の軌跡) |
| **v3 `--leave-effect off`** | c9ab05383accca2e → c9ab05383accca2e = | 69,603 = | 5,389 = | 全列 = |
| **classical**(退去を選ばない) | 18ed5c8261ee2e9c = | 102,008 = | 8,423 = | 全列 = |
| v1 既定 | 91c33e23b27f5865 → 0a52a4d3a90fa79f **≠**(記録) | 60,987 → 60,970 | 759 = | 全列が違う |
| **v1 `--leave-effect off`** | 91c33e23b27f5865 = | 60,987 = | 759 = | 全列 = |

- `--exit-mode immediate`(既定)の経路は `leave_effect` を off にすれば 1 バイトも変わらない=9a の退出の口は既定では通らない。
- **golden 更新**(`tests/engine/test_presence_executor.py` の `W17_GOLDEN`): 帰無腕 18f8807264d04018 / 100,509 → **72cb9cd52982da74 / 100,439**・v3 既定 c9ab05383accca2e / 69,603 → **993276d5e5bb5cbe / 69,978**。旧値は `*_leave_off` と `test_leave_effect_off_reproduces_the_stage_5_checkpoints` で固定。段 2c/3 段目/段 2a 前の再現テストには `leave_effect=False` を明示した(`test_l4_scale_1_…`・`test_hunger_model_v1_…`・`test_poi_target_legacy_…`)。

### 2. 歩いて乗る退出の腕([exit_arms.json](exit_arms.json)・mock v3 と classical)

| 腕 | final | 呼数 | 退出(DEPART) | 歩き出し(ホームで待ちから) | 乗った | TOO_FAR で即時 | 意図が落ちて即時(うち繰り延べ) | ゲートで即時 | 日末に歩いている | 所要[分] p10/p50/p90 | 歩く間に落とした起床/呼ばれた | 壁時計 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| mock_immediate | 993276d5 | 69,978 | 4,271 | — | — | — | — | — | — | — | — | 22.6 秒 |
| **mock_walk** | 70052476 | 70,533 | 4,189 | 3,981(148) | **3,035(76%)** | 25 | 847(45) | 208 | 68 | 9 / **21** / 40 | 5,057 / 1,069 | 23.0 秒 |
| mock_walk_leave_off | 51f55bb3 | 71,072 | 4,197 | 3,990(144) | 3,042 | 25 | 854(41) | 207 | 63 | 9 / 21 / 39 | 5,128 / 1,061 | 23.2 秒 |
| mock_walk_max30 | ebc406d4 | 71,108 | 4,202 | 3,996(146) | 2,475(62%) | **766** | 681(27) | 206 | 70 | 7 / 19 / 27 | 4,887 / 877 | 23.4 秒 |
| classical_immediate | 18ed5c82 | 102,008 | 5,087 | — | — | — | — | — | — | — | — | 32.1 秒 |
| **classical_walk** | 5c6dbde2 | 101,785 | 4,911 | 4,677(3) | **3,737(80%)** | 37 | 814(15) | 234 | 78 | 13 / **24** / 42 | 6,624 / 1,648 | 32.3 秒 |

- **意図が落ちた理由**(直前の行為): mock は 12 語ほぼ一様(移動 107・会話 93・就寝 91・通報 89・退去 84 …)=歩いている間の体/会話の起床で mock が別の行為を選んだ。classical は 移動 491・食事 268=方策の活動表が歩いている体に「移動/食事」を返す。運賃不足 4〜7・待ちの打ち切り 4 だけ。
- **歩く間の呼**: 起床を落とした件数(場所の変化・到着満了・計画境界)mock 5,057・classical 6,624。それでも呼ばれた(体・会話・顕著行為)mock 1,069・classical 1,648。呼数の総数は mock +555(+0.8%)・classical −223。
- **運賃**: 歩いて乗った体は `_board_riders` で運賃を払う(即時は払わない=非対称・保存則は全腕 `conserved=True`)。鉄道の `boarded_from_queue` は計画の退出を含む(mock 3,409 → 6,465)。`departed_by_llm`(LLM の乗車)は 3,409 → 3,430 で混ざらない。
- **計画一致率(域外側)**: mock 0.991 → 0.968・classical 0.989 → 0.959(歩いている間は計画上は域外)。日末の「計画在圏なのに域外」は 198 → 243(mock)。

### 3. 在圏の形(journal・判定しない)

5 エリアの時別在圏は journal(毎正時)から `tools/c7`(`build_map`・`area_hour_table`)で集計。central の時別在圏(体数・5,000 体):

| 時 | 08 | 10 | 11 | 12 | 14 | 16 | 17 | 18 | 19 | 20 | 21 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| mock immediate | 551 | 956 | 971 | 892 | 819 | 751 | 684 | 651 | 566 | 475 | 355 |
| **mock walk** | 552 | 949 | 960 | 913 | 904 | 776 | 742 | **750** | **683** | **555** | 423 |
| classical immediate | 422 | 482 | 411 | 340 | 235 | 223 | 230 | 229 | 264 | 265 | 205 |
| **classical walk** | 429 | 483 | 421 | 349 | 328 | 242 | 263 | **346** | **448** | **351** | 282 |

| 腕 | central 17〜20 時の在圏の割合(終日) | 08〜12 時 | 5 エリアのピーク時刻 c/nw/ne/se/sw | central の深夜残存率 |
|---|---|---|---|---|
| mock immediate | 0.207 | 0.359 | 11/12/18/10/14 | 0.194 |
| mock walk | **0.223** | 0.339 | 11/12/18/10/13 | 0.182 |
| classical immediate | 0.182 | 0.390 | 10/12/18/10/13 | 0.366 |
| classical walk | **0.223** | 0.344 | 9/12/18/12/13 | 0.316 |
| (検証の記録)KDDI c7-day-4 の obs | — | — | 18/18/15/17/16 | 0.140 |

- **夕方に central を通る流れが出た**(第263 の「退出=その場で消える」の非対称): central の 17〜20 時の割合 mock 0.207 → 0.223・classical 0.182 → 0.223。classical の 19 時は 264 → 448。
- **ピーク時刻は動かない**(mock central 11 時・classical 10 → 9 時=午前の 2 点の差 491 vs 483 の入れ替わり)。KDDI の 18 時とは離れたまま=ピークの外れの主因は W17 の来街者の時刻形状(第263 §2-2 の (1))で、退出の形ではない(推定のまま・判定はしない)。
- 出口セルの密度段の最大は変わらない(mock 5・classical 6 の時間帯は同じ)。出口セルの在圏は夕方に +2〜7%(mock 18 時 1,476 → 1,561・classical 19 時 784 → 876)。ホームセルの在圏は classical の 19 時 8 → 41。

### 4. 検証中に直したもの(事後報告)

1. **歩き出した体が計画境界の起床で呼ばれ、ほぼ全員の意図が落ちていた**(初版): DEPART の tick は W17 の計画境界(PLAN_*)と重なり、即時の形では体が域外に居るので呼ばれないが、歩く形では在圏のまま起こされ mock が一様な行為で意図を上書きした(4,028 中 2,758=68% が 2 分で即時へ)。計画境界も歩いている間は起こさない形にした(上の表=21%)。
2. **待機/なしで歩みが止まる**: `_apply_wait` は段 2c の意図を持つ体だけを歩かせ続けていた。計画の退出の体は `plan_flags` のビットで同じ扱いにした(ビットは walk_to_platform のランだけ立つ=既定不変)。

### 5. 宣言と問い

宣言: 行き先=その体の路線のホーム(代表ノード)・歩き出しの上限=`intent_max_ticks`(60)・会話の繰り延べの上限は歩く時間を含まない・意図が落ちたら即時(会話中は繰り延べてから)・ゲート/便なしは即時・歩いている間は場所の変化/到着満了/計画境界で起こさない・所要時間=歩き出し→乗車(繰り延べの時間は含まない)・退去の活動欄「なし」は次の tick に満了・`--leave-effect` の切替口。問いは報告の Q114〜Q121。

### 6. 再現

```
D=docs/bench/analysis/presence-shape-2026-09-29
python $D/presence_measure.py arms15 --out $D/arms15_leave.json
python $D/presence_measure.py bytecheck --head-src <HEAD e784f65 の src と docs/bench/anchors を展開した場所の src> --scratch <作業用の場所> --out $D/leave_byte_check.json
python $D/presence_measure.py arms --scratch <作業用の場所> --out $D/exit_arms.json
```
