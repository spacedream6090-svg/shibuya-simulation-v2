# presence.py の docstring と実装の食い違い(11-02)

- 発注: 指示書 [prompt-2026-11-02-research.md](../../../design/prompt-2026-11-02-research.md) の 6・[回答 10-25](../../../design/v2-answers-2026-10-25.md) §9 の 2。
- 対象: `src/shibuya/engine/presence.py`(HEAD `86d6424` で 1,960 行)。
- 改訂: 第 1 版(初回の報告)のあと、別の検収役の判定(条件つき受入・中 6・低 9)を受けて直した(本書の #1〜#3・#12・#21 の書き直し、#23・#24 の追加、§1-2 の設計書の表、§5 の ③ の測定の条件)。初回は Read の行数の上限で H1819〜1960(`plan_stranded_eod`・`plan_match_*`・`day_night_ratio`・`counters`・`exit_summary`・`summary`)を読み落としていた。改訂で読み、食い違いは無かった。
- 変えたもの: docstring と `#` の注釈だけ(コードは 1 バイトも変えていない=下の §4 の構文木の検査)。設計書 `docs/design/v2-plan-executor-design.md` は変えていない(設計書にも及ぶ食い違いは表の「直す段」に「設計書も」と書いた)。
- 瞬間移動そのものの修正は本作業の外(段 2)。
- 行番号は **HEAD `86d6424` の presence.py** の行(書き直した版では docstring が延びて行がずれる)。

## 1. 食い違いの表

「直す段」の「本作業」は、今回 docstring を実装に合わせて直したもの。「段 2」は挙動の穴で、docstring には「〔既知の穴・11-02〕」の印を付けた(PENDING §2 の presence.py の行を指す)。

| # | docstring の文(旧・行) | 実装(行・何をしているか) | 影響(誰がどこに現れるか・距離・頻度) | 直し方の案 | 直す段 |
|---|---|---|---|---|---|
| 1 | E3「非鉄道ゲート(方面 8/9)は所要時間なし=開始 tick ちょうどに**ゲートセル**へ。」(L29) | `_build_events` L1043 でゲートの体のセルを −1 にした後、L1048-1052 で `arr_cell = exits[rank % exits.size]` が**全員**を上書きする。`exits` は `_exit_cells`(L864-878)=W11 駅出口。W12 の門のセル(`ext_walk_gate` 58 セル・`ext_road_gate` 37 セル=`attached_place_ids`)はエンジンでは読まない(build 側の `w21_build_b.py` L541 は読む) | 方面 8/9 の域外居住者 5,275 体(徒歩 1,513・道路 3,762=母集団 345,858 の 1.53%)が、区界ではなく駅の出口セルに現れる。方面 −1 の住民 25,139 体も、域外から戻るときは同じ(線 −1=ゲート扱い)。門のセルから最寄りの出口セルまでの中央値は 609.9 m(道路)/ 623.4 m(徒歩)。門のセルから最も遠い出口セルまでは最大 2,508.4 m(代表ノード間) | W12 の `attached_place_ids` を `ProcessAssets` に載せ、ゲートの体は門のセルへ置く(または区界から歩かせる)。設計書 §6 の切替口 `--gate-mode instant\|walk` は実装に無い | 段 2・設計書も(§3 の「ゲートセルへ置く」・§6 の `--gate-mode`) |
| 2 | (旧 docstring に記述なし。設計書 §3「ホームセル 8 個 → W11 の出口セルへ round-robin」) | L1048-1052: 降りるセルは**ブロックの通し番号** `rank % 25` で選ぶ。線・方面・ホームとは結び付けない。`_exit_cells` は 45 行を `np.unique` で **25 セル**にする(10-25 の「45 セル」は 45 行・25 セル)。25 セルのうち 6 セルは `station_title` が表参道(4)・明治神宮前〈原宿〉(2)の出口 | 鉄道の体も含めて到着の約 6/25(24%)が、表参道・明治神宮前の出口のセルに降りる。距離はセルの重心で W0 の原点から 1.01〜1.18 km、最寄りの渋谷の出口セルから 0.72〜0.91 km。ホームのセル(`rail.platform_cell`)は出口セルがあると使わない(ホームから出口までの所要時間も無い)。ほかに `g-7_-3_GL`(西口・南口・北口・`station_title` は渋谷・原点から約 700 m 西)が入っている=神泉駅の出口の名寄せの誤りかもしれない(推測) | 出口を `station_title == 渋谷` に絞り、W11 の出口を線(改札)に結び付けて、その線の出口から選ぶ。均等の round-robin ではなく出口の重みを使う | 段 2・設計書も(§3 は渋谷以外の駅の出口を含むことを書いていない) |
| 3 | `_TYPE_ORDER` の注釈「同一 tick 内の実行順(**退出 → 到着**の順にする=同 tick に両方ある体を取りこぼさない)」(L144)。瞬間移動の記述なし | L1061 `arr_tick = np.maximum(arr_tick, prev_end)`: 次のブロックの E1 の便が前のブロックの終了より前にホームへ入ると、到着が前の終了の tick へ切り上がる。同じ tick の中では DEPART(`_depart_now` L1414 → `resolve.rail_depart` で cell=−1)→ ARRIVE(`_do_arrive` L1343 → `resolve.rail_arrive` で出口セルへ)の順に実行する。`step` の ③ 繰り延べの解除(L1244)→ ⑤ ARRIVE も同じ形になりうる | 体が今いるセルから消え、同じ tick に駅の出口セルへ現れる。**測定の条件**: sp1(2026-10-21〜23)・`--space nav1` の腕・旧既定=E8 の到着の分散あり(今の `--rate-rules legacy` の腕。既定から外れたのは ce52662・第340)。分散で早い便へ送られた到着ほど L1061 で前の終了へ切り上がるので、今の既定 off では件数が違いうる(未計測・測り直していない)。その条件で 5,000 体 1 日 18〜20 件(sp1 の `accept_345.json`=18 件・再検収の自前の道具=19 件・review=20 件)・最大 1,355 m・階が変わる 9 件。345,858 体なら線形で約 1,250〜1,380 件/日(同じ条件での推測・未計測)。経路ごとの内訳は未計測 | 同じ tick の DEPART の後の ARRIVE を次の tick 以降へ送る。または退出を駅へ歩かせ、到着をホームから出口へ歩かせる(存在の連続性・10-12 §1-3 の 1) | 段 2(台帳 `DOC-nav1-presence-same-step-depart-arrive`・10-25 §9 の 2) |
| 4 | E4 の 9a「意図が落ちた(LLM が別の行為を選んだ・運賃不足・待ちの打ち切り・経路なし)ら**その場で `rail_depart`**」(L34-36) | `_flush_walkers` L1538-1550: LLM の別の行為で落ちた 1 回目は歩き直しの待ちに入れる(第302 Q117 (b)・`_flush_rewalks` L1458-1490)。その場で `rail_depart` するのは `NO_TRAIN`・`FARE_SHORT`・`UNREACHABLE` と 2 回目だけ | `walk_to_platform` のランだけ。docstring どおりに読むと歩き直しが無いことになる | docstring に歩き直しを書いた | 本作業 |
| 5 | P4「到着の山の分散(`_spread_arrivals`)が**便数**ぶんのループを 1 本持つ(線ごとに、その線の便を時刻の降順に 1 回走る)」・「tick ごと: イベント種(5)ぶんの `flatnonzero`」(L20-24) | `_spread_arrivals` は線ごとに降順・昇順の 2 本(L972・L1003。関数の docstring L920 は 2 本と書く)。〔11-01 段 2 の 4〕から腕 `--rate-rules legacy` のときだけ呼ぶ(L1032)。`_run_tick` は 1 回の呼び出しで 2 種(`step`=DEPART・ARRIVE / `step_plan_boundaries`=SLEEP・WAKE)=計 4 種。ほかに `_assign_trains` の線数のループ(L890)・`from_weekly` の乗車行の飛ばし(L526・≤ 8)・`_rearm_after_leaving` の体数ぶんのループ(L1745・L1769)が宣言に無い | 宣言の数字の誤りと漏れ(性能は変わらない) | docstring の P4 を書き直した | 本作業 |
| 6 | 書き込み口の一覧「`rail_arrive` / `rail_depart` / `begin_planned_sleep` / `wake_from_plan` / `release_indoor` / `balk_queue` / `place_at_external` / `set_plan_state`」(L11-13) | 9a の `walk_to_platform` で `R.begin_exit_walk`(L1437)と `R.clear_board_intent`(L1523)も叩く | 宣言の漏れ(既定の `immediate` では叩かない) | 一覧に足した | 本作業 |
| 7 | expedient の一覧が E1〜E9 で終わる(L26-43) | 同じファイルに E12(`RETURN_MIN_AWAY_MIN`・L81-86)と E13(読み口 v2・`DERIVE_RULES`=設計書 §6 の E13)がある | 登録簿の漏れ | 一覧に足した | 本作業 |
| 8 | `_rearm_after_leaving`「次のブロックの到着 tick が既に過ぎていれば `tick+1` に張り直し」(L1703) | L1766 `when = max(start, tl+1)`。次のブロックの start は常に tick より後なので、張り直す時刻は**そのブロックの開始 tick**(注釈 L1763 の文が正しい)。セルは `arrival_cell`(駅の出口セル)。注釈の「ゲートから入る」(L1763)も実際は出口セル | 文の誤り(挙動は注釈どおり)。セルの穴は #1・#2 と同じ | docstring と注釈を直した | 本作業(セルは段 2) |
| 9 | `_rearm_after_leaving`「逐次ループ宣言(P4): なし(`searchsorted` 1 本)」(L1706) | L1745・L1769 に体数ぶんの Python ループ(行の注釈では宣言している) | 宣言の不一致 | docstring を注釈に合わせた | 本作業 |
| 10 | (記述なし) | E12 の戻り(L1744)と `initialize` の I6 の降ろし(L1216)は `exits[np.arange(k) % 25]`=**呼ぶたびに出口セルの先頭(セル索引の最小)から**割り振る | 戻りと 0 時の降ろしが先頭の出口セル(`g-1_-1_DECK` から)に偏る。件数は未計測 | 到着と同じく線・出口の重みで選ぶ(#2 と一緒に) | 段 2 |
| 11 | クラスの Note「層のイベント列は**0 日目の座標**で組む。1 日目からの在圏の出入りは日の頭の初期化(10g・A11)で張り直す(それまでは 1 日目以降のイベントは無い=宣言)」(L586-588) | `relay_day`(L808-836・10d)が日の頭に表を張り直し、`_t0` で日の中の分と T を換算する(`engine.systems.state_io` L175 が毎日呼ぶ) | 古い記述(1 日目からもイベントは出る) | Note を書き直した | 本作業 |
| 12 | Args「`ticks`: ラン長[tick]」(L578) | 組み立て(`engine.systems.build` L305-308・L843)は `ticks` をそのまま渡す。1 日のランは `ticks <= tpd`=ラン長(スモークなどの短いランを含む)、複数日のランは 1 日の tick 数(`sim_days > 1` では `ticks == tpd` を求める) | 複数日のランでは文が誤り(初回の直し「1 日の tick 数」は 1 日の短いランで誤りだった=検収の中) | 「層の表の長さ。1 日のランはラン長(≤ 1 日)・複数日は 1 日の tick 数」に直した | 本作業 |
| 13 | Args に `mode`・`derive_rule` が無い(L570-585) | `__init__` が受ける(L608-609) | 記述の漏れ | 足した | 本作業 |
| 14 | `_mix64`「出勤率(E6)の『その日来ない 12%』を `agent_id` だけから決めるのに使う」(L162) | presence.py の中に呼び手は無い(〔11-01 段 2 の 4〕でくじを消した)。`tests/engine/test_geometry_c9.py` が import して式の一致を検査するので残っている | 古い記述 | 直した(消すかは別の判断) | 本作業 |
| 15 | `from_weekly`「`exclude`: True の体は**ブロック 0 本**にする(E6 出勤率)」(L441) | `PlanExecutor` は `absent_on`=全員 False を渡す(L788-796) | 古い記述(今は誰も外れない) | 直した | 本作業 |
| 16 | `step`「在圏の出入り(到着・退出・**計画活動**)を実行する」(L1235) | `step` は 9a の始末・歩き直し・繰り延べ・張り直した到着・DEPART・ARRIVE だけ。計画活動の欄 `plan_activity` は K15 で消した。就寝・起床は `step_plan_boundaries` | 文の誤り | 実行の順を書いた | 本作業 |
| 17 | `sample`「**run.py が**在圏 journal と同じ位置で呼ぶ」(L1789)・`step_plan_boundaries`「run.py から層へ移した」・`_BOUNDARY_TYPES` の注釈「run.py の『計画境界の起床候補』の所」(L1231) | 呼び手は `engine.systems.observe`(L73)と `engine.systems.body`(L67・L114) | 古い記述 | 直した | 本作業 |
| 18 | `EventType`「日次イベントの種(設計書 §3 の表)」(L134) | 設計書 §3 の表は ARRIVE の引数を「便索引」と書くが、実装はセルを積む(L1132-1133)。WORK_START・AT_HOME は値だけで積まない | 設計書との食い違い | docstring に実装の引数を書いた | 本作業・設計書も(§3 の表) |
| 19 | `PlanBlocks` の Note「`place_kind ≠ 域外` ∧ `活動 ≠ 乗車` の連続行を 1 本に畳む」(L367-371) | 実装は Note どおり(域内居住者の自宅行は在圏)。設計書 §2 の `derive` の行は「`place_kind ∉ {自宅, 域外}`」と書く。既定の読み口 v2 はさらに `_apply_derive_v2` で選ぶ | 設計書との食い違い(docstring は実装どおり) | v2・v2.1 の段を Note に足した | 本作業・設計書も(§2) |
| 20 | (記述なし) | `_lines_of_direction` L780-785: `rail` はあるが `lines_present` が無いか空なら全員 −1(全員ゲート扱い)。`rail` が None なら表の値のまま(到着は `_assign_trains` が全員ゲートにする) | 組み立ての形によって全員が #1 の扱いになる(本番の世界では 8 線とも便がある) | docstring に書いた | 本作業 |
| 21 | E7「その日の在圏ブロックが 0 本の体は終日域外」(L40) | 0 日目は `initialize` が域外へ置く。1 日目からは位置を持ち越す(A11)。DEPART は `b_end < ticks` のときだけ出る(L1122)ので、日の終わりまで続いたブロックの体は日をまたいで在圏のまま | 0 本の体については K9(毎日月曜の行)の間は毎日同じなので成り立つ。曜日の行が変わると、前の日の終わりに在圏だった体が 0 本の日も在圏のまま残りうる(推測・未計測)。ブロックのある体の日の境目のずれは #23 | 日の頭に「今日 0 本で在圏」の体を数える計器を足す | K9 を解く段(親の判断) |
| 22 | E4「退出は即時 `rail_depart`」(L30) | DEPART の tick に今いるセルから消える(`rail_depart` は cell=−1・駅へ歩かない) | 10-12 §1-3 の 1 で「外す」と決まった既知の項(存在の連続性) | docstring に「今いるセルから・歩かない」と書いた | カレンダーの段 1b(設計書 §3 の改訂注のとおり) |
| 23 | (記述なし。E7「その日の在圏ブロックが 0 本の体は終日域外」・`_build_events` の「0 日の頭から在圏の最初のブロック」は 0 日目だけの話のように読める) | DEPART は `b_end < ticks` のときだけ積む(L1122)。ARRIVE は「最初のブロックが 0 時開始」なら毎日積まない(L1080-1082)。1 日目からは位置を持ち越す(A11・`state_io` の `start_day`/`relay_day`) | K9 の下でも計画と在圏がずれる。(a) 最後のブロックが 24 時まで続き最初のブロックが 0 時より後に始まる域外居住者 **32,065 体**は夜通し在圏のまま残り、最初の ARRIVE は I2 で捨てられる。(b) 最初のブロックが 0 時開始で最後のブロックが 24 時前に終わる域外居住者 **4,281 体**は 0 時から次のブロックまで域外。読み口 v2・day0 の表から数えた静的な数(検収役の値をこちらでも `PlanBlocks.from_weekly` で再計算して一致)。ランでは未計測 | 日の頭に、持ち越した在圏と今日の計画の食い違いを数える計器を足し、ARRIVE/DEPART の積み方を日をまたぐ形に直す | K9/A11 の親の判断(〔既知の穴・11-02〕の印を付けた) |
| 24 | `_flush_walkers`「意図が落ちた(即時・会話中は繰り延べてから即時)。逐次ループ宣言: なし(歩いている体のマスク=体数の配列 1 本)」(L1493-1494) | #4 と同じ: LLM の別の行為で落ちた 1 回目は歩き直し(L1538-1550)。L1535 に値の種類ぶん(≤ 25)のループがある | `walk_to_platform` のランだけ。#4 で直した誤りが関数の docstring に残っていた | 歩き直しとループを書いた | 本作業 |

### 1-2 設計書との食い違い(設計書 `v2-plan-executor-design.md` は変えていない=直すかは親)

| 設計書の節 | 設計書の文 | 今の実装 | 表の行 |
|---|---|---|---|
| §3 E3 | 方面 8/9 は「開始 tick ちょうどにゲートセルへ置く」・「徒歩 2,339・道路 5,893 = 2.4%」 | 駅の出口セルへ置く。今の母集団では 1,513・3,762=1.53% | #1 |
| §3 降車セルの分散 | 「ホームセル 8 個 → W11 の出口セルへ round-robin」 | 25 セルに表参道・明治神宮前の出口を含む・線と結び付けない | #2 |
| §3 表 | ARRIVE の引数は「便索引」 | セルを積む | #18 |
| §3 tick 処理 | 「逐次ループは type 数 ≤6」 | 積むのは 4 種(WORK_START・AT_HOME は積まない) | #5・#18 |
| §3 山の分散・§6 E8 | 山の分散を常に行う・切替口 `ARRIVAL_SPREAD_MAX_TRAINS` | 〔11-01 段 2 の 4〕既定 off=分散しない・`--rate-rules legacy` の腕だけ | #5 |
| §2 derive | 「`place_kind ∉ {自宅, 域外}`」 | 域内居住者の自宅行は在圏 | #19 |
| §6 E3 | 切替口 `--gate-mode instant\|walk` | 無い | #1 |
| §6 E6 | 「出勤率 0.88・`--attendance-rate`(既定 1.0)」 | 〔11-01 段 2 の 4〕くじと旗を消した(`cli.py` L973・`rate_rules.py`) | (docstring は直す前から一致) |
| §6 登録簿 | E12 の行が無い | `RETURN_MIN_AWAY_MIN`=60 分(E12) | #7 |
| §6 E1・E7・§8 | 切替口 `--arrival-train`・`--visit-rate-mode`・`--exit-spread` | src/ に無い(grep 0 件) | (presence.py の docstring は主張していない) |

## 2. 1,355 m の検算

- 道具: [exit_distance_1102.py](exit_distance_1102.py)(pyarrow と numpy)。結果: [exit_distance_1102.json](exit_distance_1102.json)。
- 方法:
  1. 到着のセルの集合を `world.assets.load_process_assets` と同じ写し方で作った(`w11_station_exits` の `own_grid_place_id` を先に引き、無ければ `place_id`。`w2_cells.place_id` の行番号へ。`np.unique`=`PlanExecutor._exit_cells`)。45 行 → **25 セル**。本物のローダ(`load_process_assets`)でも 45 行・重複を除いて 25 を確かめた。
  2. 座標は 2 通りで測った。(a) `w2_cells` の `centroid_x`・`centroid_y`(W0 の原点 `ORIGIN_LATLON=(35.6595, 139.70062)`・`M_PER_DEG_LAT=111132.9`・`M_PER_DEG_LON=111320·cos(35.6595°)` で作ったローカル平面 [m]。520 セルすべての重心が自分の 100 m の升に入ることを確かめた)。(b) `rail_arrive` が書く xy=`w1_nodes` の (x, y) をセルの代表ノード(`rep_node_idx`)で引いたもの。
  3. 出口セルどうしの距離の行列を作り、最大と 1,355 m ±15 m の対を探した。退出は今いるセルから起きるので、全 520 セル × 出口 25 セルの最大も上限として測った。
- 値:

| 測ったもの | 重心(a) | 代表ノード(b) | 対 |
|---|---|---|---|
| 1,355 m ±15 m に入る出口セルの対 | 1,362.2 m | **1,355.0 m** | `g3_-5_GL`(新南口・渋谷)↔ `g3_9_GL`(明治神宮前駅)(向きは分からない) |
| 出口セルどうしの最大 | 1,846.6 m | 1,853.8 m | `g-7_-3_GL`(西口・南口・北口)↔ `g9_7_GL`(表参道) |
| 渋谷の出口セル(19)どうしの最大 | 988.6 m | 982.8 m | `g-7_-3_GL` ↔ `g3_-5_GL` |
| 全セル → 出口セルの最大(上限) | 2,515.1 m | 2,508.4 m | `g-9_-11_GL` → `g9_7_GL` |

- 10-25 の 1,355 m との照合: **一致する**。sp1 の受入の道具(`docs/bench/analysis/spatial-2026-10/sp1/tools/accept_345.py`)は刻みの終わりどうしの xy の距離を測り、最大 1,355.0 m を出した(`accept_345.json`)。代表ノードの xy で測った 25 セルの中で、1,355 m ±15 m に入る対は `g3_-5_GL` ↔ `g3_9_GL` の 1 つだけで、値は 1,355.0 m。測られた 1,355 m はこの 2 セルの間の移動だった、と読める。ただし受入の記録は対のセルを残していないので、これは値の一致からの推測。
- 含意: 1,355 m は旧既定(E8 の分散あり)・nav1 の腕の 5,000 体 1 日の標本の最大で、出口セルどうしでは 1,853.8 m まで起こりうる。渋谷の出口だけに絞れば最大は 982.8 m。1,000 m を超える分は、表参道・明治神宮前の出口が到着の候補に入っていること(#2)から来ている。

## 3. 試験の結果

- 呼び方: `python -m pytest -q -p no:cacheprovider -o addopts="" -rf tests/engine -k "presence or plan_exec or executor"`(`PYTHONIOENCODING=utf-8`・`PYTHONPATH=<作業木>/src`。本体の venv は editable install で本体の src を指すため、作業木の src を読ませるのに `PYTHONPATH` を付けた=`shibuya.__file__` が作業木を指すことを確かめた)。
- 直す前(作業木=HEAD): **70 passed**・3,045 deselected(315 秒)。
- 直した後(第 1 版・作業木): **70 passed**・3,045 deselected(296 秒)・failed 0。数は直す前と同じ。
- 検収の指摘を直した後(改訂・作業木): **70 passed**・3,045 deselected(322 秒)・failed 0。構文木の検査も EQUAL(sha256 は同じ)。

## 4. 差分の統計と構文木の検査

- `git diff --stat`(改訂の後): `src/shibuya/engine/presence.py | 229`(1 file changed, 179 insertions(+), 50 deletions(-)・作業木の版は 2,089 行)。新しいファイルは本ディレクトリの 4 本(README・`check_ast_equal.py`・`exit_distance_1102.py`・`exit_distance_1102.json`)。
- 構文木の検査: [check_ast_equal.py](check_ast_equal.py)(標準ライブラリだけ・引数に 2 つのパス)。両版を `ast.parse` で読み、モジュール・クラス・関数(async を含む)の先頭の文字列の文を外してから `ast.dump`(行番号なし)を比べる。`#` の注釈は構文木に入らないので比べる対象の外。
  - HEAD の presence.py と作業木の presence.py(改訂の後にも回した): **EQUAL**(docstring 54 本を外した後の節点 17,397・dump の sha256 `b4e85417ffac785bc87c3770d88d1e25cdd494ee9f82d6c3cba2a39dc4c52d55` が両方で同じ)。
  - 陰性対照: 作業木の版の `EXIT_DEFER_LIMIT = 30` を 31 に変えた写しと比べると **DIFFERENT**(sha256 `9b280f86…`)・exit 1=検査はコードの変化を拾う。
- 構文: `python -m py_compile src/shibuya/engine/presence.py` が通る。CR は 0(LF のまま)。

## 5. PENDING「決定済みで実装待ち」に載せる 3 行の案

- 〔11-02/6〕`presence.py` の到着と退出の場所(docstring は実装に合わせた=記録 docs/bench/analysis/presence-docstring-1102): ① 方面 8/9 の体が門(W12)でなく駅の出口に現れる ② 到着の約 6/25 が表参道・明治神宮前の出口のセル(線と結び付けない round-robin)
- ③ 同じ刻みの退出と到着=旧既定(E8 の分散あり=今の legacy の腕)・nav1 の腕の 5,000 体で 18〜20 件/日・最大 1,355 m(新南口 ↔ 明治神宮前のセルの代表ノード間と一致=推測・出口どうしの上限 1,853.8 m)。今の既定 off では未計測。台帳 `DOC-nav1-presence-same-step-depart-arrive`
- 直すのは段 2(①②③と、戻りの割り振りの偏り #10)。日の境目の穴 #23 は K9/A11 の親の判断。設計書にも及ぶ食い違い(§3 の E3・降車セルの分散・ARRIVE の引数・type 数・§2 の derive の定義・§6 の `--gate-mode`・E6・E8・E12=§1-2)は親が設計書を直すかを決める
