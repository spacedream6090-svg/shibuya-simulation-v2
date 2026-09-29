# R-54 自コード読み: 前提検査・実現可能性の判定の棚卸し(空間系/ルール系)

> 位置づけ: 設計者の依頼「エンジン内の前提検査・実現可能性の判定を全部列挙し、空間系とルール系に分類して件数と場所を表で出す」への**コードの事実だけ**の答申。物理エンジン粒度の空間層(D-122)の検討材料。推奨は書かない。
> 基準コミット: `31645d8`(`git log --oneline -1`・branch design/memory-net-draft)。読み役 Opus 5.5・読み専用。**親検収 済(第281)**: 主張 5 件(到達=`resolve.py:1198-1219` の `good = ok_cell & ((nxt >= 0) | same)`・退出=`presence.py:77-78` EXIT_MODES は immediate のみ+`resolve.py:2284-2285`・満席=`crowd.py:212/134/67`+`assets.py:126`+`resolve.py:1699-1701`・遮蔽=`w8_visibility.py:13-18`+`w8_t2.npy` の読み手は build だけ・書かれない結果コード=`ResultCode.REFUSED/UNDEFINED_ACTION/INSUFFICIENT_ABILITY` は表にしか無く NO_PERMISSION は `opening.py:202` が `permitted=ones`)を親が同じ行を印字して一致。設計への写し先=D-122 草案。
> 分類の約束(読み役の定義=expedient): **空間系**=判定に位置・距離・経路・密度・面積・席数・視線・セル隣接を使う / **ルール系**=時刻・所持金・在庫・状態・権限・件数・tick 数だけを使う / **両方**=同じ判定で両方を使う。「結果コード」欄の「なし」は結果コードを書かない判定(計数・抑止・掃除)。
> 手元資産の数値(セル数など)は `data/world/v2` を読み専用で数えた値(§2 に明記)。

## 1. 棚卸し表(71 件)

### 1-A 行為の前提検査(`engine/resolve.py`・`engine/commit.py`=Phase B/C)

| ID | 何を判定するか | 分類 | 使う量 | 結果コード | 場所 | 引用 1 行 | 手書き定数(タグ) |
|---|---|---|---|---|---|---|---|
| A01 | 移動「あたり」の行き先が解決できない(域外の体) | 空間 | cell<0 | BAD_TARGET | resolve.py:1192 / activity.py:374 | `bad = tgt == WANDER_BAD_TARGET` | — |
| A02 | 移動: 行き先セルの範囲・近づく対象ノード・経路(next-hop)の存在 | 空間 | W3 next_hop | UNREACHABLE | resolve.py:1198,1203,1206,1219 | `good = ok_cell & ((nxt >= 0) \| same)` | — |
| A03 | 移動の行き先の既定(対象欄なし=職場/自宅のうち今いない方) | 空間 | セル | —(行き先決定) | commit.py:671 | `dest = np.where(cell == wc, hc, wc)` | 規則自体が expedient(commit.py:665「mock」) |
| A04 | エンジン継続(node 幾何・既定): 1 tick 1 ノード前進・前進不能 | 空間 | next_hop | UNREACHABLE | resolve.py:1096-1097,1139 / graph.py:84 | `stuck = (new_node...== r.node[aid]...) & (~arrived)` | 1 tick=1 ノード(graph.py:10 expedient) |
| A05 | エンジン継続(edge 幾何): 場外・目的なし・次ホップ無し | 空間 | next_hop | UNREACHABLE | geometry.py:323,335 | `stuck \|= (~arrived) & ((nd < 0) \| (tgt < 0))` | — |
| A06 | edge: 歩ける距離=希望速度×Kladek f(ρ)×60 s。ρ≥5.4 で 0=止まる(失敗ではない) | 空間 | 人/m²(セル在席数÷歩行可能面積) | なし(`n_jammed`) | geometry.py:145,277 / resolve.py:1100-1101 | `return v * f * float(self.tick_seconds)` | γ 1.913・ρmax 5.4(Kretz 2015)・希望速度 U(1.00,1.60)(一様=expedient) |
| A07 | edge: 1 tick に跨げる辺の上限・超過距離は捨てる | 空間 | ホップ数 | なし | geometry.py:99,328 | `for _ in range(MAX_HOPS_PER_TICK):` | 32(expedient) |
| A08 | 「近づく」到着時に対象が近くに居るか | 空間 | 距離 | TARGET_GONE | resolve.py:1172 | `near = present & (d <= APPROACH_DONE_M) & (node >= 0)` | 2.0 m(expedient) |
| A09 | 「見る」焦点の取得距離(待機そのものは成功) | 空間 | 距離 | なし | resolve.py:1316 | `want = want & (np.sqrt(...) <= FOCUS_ACQUIRE_M)` | 20 m(expedient) |
| A10 | 焦点の喪失(距離または寿命) | 両方 | 距離・tick | なし | resolve.py:1350 | `far = np.sqrt((d * d).sum(axis=1)) > FOCUS_LOSE_M` | 30 m・10 tick(expedient) |
| A11 | 乗車: 鉄道過程なし/非稼働・乗車中/域外・今日の便なし | ルール | 状態・時刻表 | NO_TRAIN | resolve.py:1441,1445,1451 | `can_try = r.transit_state[aid] == 0` | — |
| A12 | 乗車: 現在セルがホームセルか(→列 / →歩く) | 空間 | 同一セル | —(OK) | resolve.py:1462 | `on_plat \|= cell_now == cells[j]` | — |
| A13 | 乗車: 最寄りホーム=**直線距離**昇順で最初に経路のあるもの | 空間 | 直線距離・next_hop | NO_TRAIN | resolve.py:1488,1511 | `good = (nxt >= 0) \| (dn == rnode[todo])` | 経路長でない(resolve.py:1475 expedient) |
| A14 | 乗車待ち: 停車中の便 × 同じホームセル(FIFO) | 両方 | 時刻・停車時分・セル | —(待つ) | resolve.py:1532-1550 / rail.py:512 | `here = np.flatnonzero((~served) & (cell == plat[k]))` | 停車 1 tick(mechanism 上界)・終端 2 tick(expedient) |
| A15 | 乗車: 所持金 ≥ 運賃 | ルール | 所持金 | FARE_SHORT | resolve.py:1556(台帳拒否 1615) | `pay_ok = r.money[ids].astype(np.int64) >= fare` | 180 円(rail.py:137 expedient) |
| A16 | 乗車: 混雑率の受容関数(≤150%=1・〜200% で 0.7・>200%=0) | 空間(混雑) | 乗車人数÷定員 | TRAIN_FULL(待ち続け) | rail.py:536,556 / resolve.py:1561 | `hard = int(np.floor(ACCEPT_MAX_RATIO * self.capacity100[t] - ...))` | 1.50/2.00/0.70(expedient)・定員 5 線 mechanism/3 線 expedient |
| A17 | 乗車待ちの打ち切り | ルール | tick | NO_TRAIN | resolve.py:1578 | `stale = held[bl & (bs >= 0) & (int(tick) - bs >= BOARD_WAIT_LIMIT_TICKS)]` | 30 tick(expedient) |
| A18 | 宙に浮いた乗車意図の掃除 | ルール | 状態 | なし | resolve.py:1593 | `inert = held[bl & (bs < 0) & (r.activity[held] != ...MOVING)]` | — |
| A19 | 降車: 乗車中 ∧ 当該便が停車中 | ルール | 状態・時刻 | NO_STOP | resolve.py:1646,1650 | `riding = r.transit_state[aid] == 1` | — |
| A20 | 購入/並ぶの対象=**現在セルの最小 id の POI**(無ければ対象なし) | 空間 | 同一セル | BAD_TARGET | commit.py:589,718,726 / resolve.py:1676,1873 | `return np.where(found & (c >= 0), order[pos_c], -1)` | 「最小 id」規則(commit.py:567) |
| A21 | 購入/食事/列: 営業中 | ルール | 時刻 | CLOSED | resolve.py:1679,1803,2357 / world/state.py:284,286 | `is_open = has_target & open_mask[poi]` | W7 が無ければ 10:00-22:00(assets.py:99-100) |
| A22 | 購入/列: 在庫>0(棚台帳 `can_sell`・スロット回し) | ルール | 在庫 | OUT_OF_STOCK | resolve.py:1681,1683,1748,2381 | `in_stock = is_open & (world.pois.stock[poi] > 0)` | 初期在庫 64(assets.py:401) |
| A23 | 購入/食事/列: 所持金 ≥ 価格(台帳拒否を含む) | ルール | 所持金 | MONEY_SHORT | resolve.py:1684,1805,1723,2377 | `can_pay = in_stock & (r.money[aid]... >= price)` | 価格 300/800/1,500(assets.py:95・カテゴリ帯) |
| A24 | 食事: 対象が飲食店(`hash_free_cat_code==1`)で同一セル | 両方 | セル・カテゴリ | NOT_IN_EATERY | commit.py:737 / resolve.py:1802 / world/state.py:225 | `in_eatery = in_eatery & np.asarray(world.eatery_mask...)[poi]` | — |
| A25 | **満席**: 在席+今 tick 受入+群内順位 < 席数 | 空間 | 席数=想定床面積÷m²/人 | —(列へ・OK) | crowd.py:212 / resolve.py:1695,1815,2399 | `out[idx] = (used + rank) < self.seats[pi]` | 飲食 2.0・他 4.0 m²/人・床面積表(全 expedient・crowd.py:67-94) |
| A26 | 列の離脱 | ルール | tick | INTERRUPTED | crowd.py:241 / resolve.py:2421 | `waiting & (r.queue_since... + WAIT_MAX_TICKS <= t)` | 15 tick(expedient) |
| A27 | 在席の回転(解除) | ルール | tick | なし | crowd.py:231 | `seated & (r.poi_since... + DWELL_MAX_TICKS <= t)` | 30 tick(expedient) |
| A28 | 会話: 対象あり・自分でない | ルール | id | BAD_TARGET | resolve.py:1973 | `has = (tgt >= 0) & (tgt < agents.n) & (tgt != aid)` | — |
| A29 | 会話: 同一セル(G7 腕は ∧ 実距離) | 空間 | セル・距離 | PARTNER_GONE | resolve.py:1958,1963 | `return ok & (np.sqrt(...) <= TALK_OPEN_METERS)` | 2.0 m(expedient・外部裏づけ 1 件) |
| A30 | 会話: 相手が会話中/就寝中でない | ルール | 状態 | PARTNER_BUSY | resolve.py:1981 | `addressable = same_cell & ~np.isin(pact, _UNADDRESSABLE)` | 対象状態 2 値(expedient) |
| A31 | 会話の相手: 名指し ∧ 同一セル、否なら同セルの撹拌順の先頭 | 空間 | 同一セル | —(相手なし=不成立) | commit.py:504,541 | `ok = ok & (pc[np.clip(nm, ...)] == c)` | フォールバック(expedient) |
| A32 | 会話ゲート: 在セッション・拒否/無視の記憶・呼予算 | ルール | 状態・tick | なし(招待不成立) | conversation.py:349-361 | `if self.refused_recently(inviter, invitee, tick):` | 記憶 60 tick(expedient) |
| A33 | 相手別不応期(同一相手・同一話者) | ルール | tick | なし | conversation.py:461 | `if int(tick) < self._speaker_invite_until.get(...)` | 60/30 tick |
| A34 | 応答確率(被招待の返事が無いときだけ) | ルール | 乱数 | なし | conversation.py:374 | `return bool(g.random() < self.accept_probability)` | 0.8(expedient) |
| A35 | 会話の離脱: 実距離(G7)またはセル離脱 | 空間 | 距離・セル | なし(終了) | conversation.py:709,712 | `if self._left_distance(s, xy_arr, float(leave_distance_m)):` | 3.0 m(expedient) |
| A36 | 会話の終了: 沈黙・寿命・歩み寄り tick | ルール | tick | なし | conversation.py:704,718,721 | `if int(tick) - s.opened_tick >= self.max_session_ticks:` | 5/60 tick(expedient) |
| A37 | 通報: 自セルの B4 に事象行が出てから窓以内 | 両方 | 同一セル・tick | BAD_TARGET | resolve.py:2025 / salient.py:272 | `fresh = (seen >= 0) & (int(tick) - seen <= REPORT_WINDOW_TICKS)` | 5 tick(レーン表から導出) |
| A38 | 手伝い: 常に失敗 | ルール | — | BAD_TARGET | resolve.py:2035 | `_fail(agents, aid, ResultCode.BAD_TARGET, tick, out)` | — |
| A39 | 就寝: 対象セル=自宅セル ∧ 現在セル=自宅セル | 両方 | セル・所有 | NO_BED | resolve.py:2053,2057 / commit.py:770 | `ok = (tgt >= 0) & ... & (tgt == home) & (r.cell[aid]... == home)` | — |
| A40 | 就寝: ホテルの寝床(`bed_cell`=現在セル) | 両方 | セル | (NO_BED を回避) | civic.py:291 / resolve.py:2065 | `return (self.bed_cell[a] >= 0) & (self.bed_cell[a] == c)` | — |
| A41 | Phase B 資源裁定: POI=min(1 tick 受入, 在庫)・相手 1・就寝 200/セル | 両方 | 容量・在庫 | LOST_ARBITRATION | commit.py:332-337,416 / resolve.py:1006 | `admitted = rank < cap` | 受入 4/tick(assets.py:97)・200(commit.py:159)(expedient) |
| A42 | 未定義行動→待機(v3=なし)・役割語→安全弁 | ルール | 語彙 | (OK 扱い) | commit.py:656 / llm_bridge.py:684 | `code == UNDEFINED_ACTION, undefined_fallback_code(vocab_version), code` | — |
| A43 | 待機/なし・退去・断る・休憩: 検査なし=常に成功 | ルール | — | OK | resolve.py:1887,1996,2004,2038 | `"""待機: **常に可能=安全弁**(失敗しない)。` | — |

### 1-B 計画実行層・世界過程・活動層の判定

| ID | 何を判定するか | 分類 | 使う量 | 結果コード | 場所 | 引用 1 行 | 手書き定数(タグ) |
|---|---|---|---|---|---|---|---|
| B01 | 計画就寝: 就寝地セルに居る→寝る / 経路あり→歩く / 無し→起きたまま | 両方 | セル・next_hop | なし(`unreachable` 計数) | resolve.py:626,653,668,687 | `good = (nxt >= 0) \| same` | — |
| B02 | 到着 ARRIVE: 域外の体だけ・出口セル有効 | ルール | 状態 | なし(skipped 計数) | presence.py:1188 | `(np.asarray(r.transit_state)[ids] == 2)` | 降車セル=W11 出口の round-robin(presence.py:926) |
| B03 | 到着がブロック終了以後ならそのブロックに来ない | ルール | tick | なし | presence.py:959 | `keep_arrive &= arr_tick < b_end` | E1(expedient) |
| B04 | 退出 DEPART: 在圏のみ・会話中は繰り延べ・買物/列は解除→即時 `rail_depart` | ルール | 状態・tick | なし | presence.py:1226,1244,1248,1252,1265 | `R.rail_depart(self.agents, ids, lines)` | 繰り延べ上限 30 tick(expedient) |
| B05 | E12 復帰: 残り ≥60 分 ∧ 戻る便あり | ルール | tick | なし | presence.py:1361 | `& ((end_cur - t) >= RETURN_MIN_AWAY_MIN)` | 60 分(expedient) |
| B06 | 鉄道到着: 予約の便の体がまだ域外か | ルール | 状態 | なし | rail.py:624 | `still = self.agents.registry.transit_state[arriving] == 2` | — |
| B07 | ホテル受付: 来街者∧域外居住∧在圏∧21:00∧セルにホテル∧部屋空き | 両方 | セル・部屋数 | なし(`n_no_bed`) | civic.py:299-338 | `room = (self.rooms_occupied[h] + rank) < self.rooms_total[h]` | 120 室/POI・21:00/9:00(civic.py:76-78) |
| B08 | 開閉店の権限: 担当∧従業者∧同一セル(否→engine_rule 代打) | 両方 | セル・権限 | (NO_PERMISSION は実行時に出ない=§5) | opening.py:159-171,187-208 / resolve.py:2456 | `same_cell = ...cell[a[ok]] == self.world.pois.cell[p[ok]]` | — |
| B09 | 補充: 在庫<発注点∧営業中∧担い手が同一セル∧バックヤード>0 | 両方 | セル・在庫・時刻 | なし(`n_no_backroom`) | goods_flow.py:228,234,245 | `low = np.flatnonzero((stock < self.reorder_point) & open_mask)` | — |
| B10 | 「あたり」の候補: 同じ層・格子 Chebyshev ≤2・代表ノードあり | 空間 | 格子距離 | (域外は A01) | activity.py:140-143,384 | `& (band[:, None] == band[None, :])` | 半径 2 セル(expedient) |
| B11 | 「まで」: 上限 480 分・最短 1 tick・相手待ち 60 分 | ルール | tick | なし | activity.py:246 / contract.py:1165 | `return np.clip(out, t + 1, cap)` | 480/60 分(expedient) |
| B12 | 行為失敗 ∧ 活動なし→次 tick 満了 | ルール | 結果コード | なし | activity.py:296 | `now = failed & no_text` | — |
| B13 | 到着満了: 「まで: 到着」∧ 非移動・非乗車 | ルール | 状態 | なし | activity.py:321 | `& (uk == int(UntilKind.ARRIVAL))` | — |

### 1-C 起床・知覚の判定

| ID | 何を判定するか | 分類 | 使う量 | 結果コード | 場所 | 引用 1 行 | 手書き定数(タグ) |
|---|---|---|---|---|---|---|---|
| C01 | 域外抑止(乗車中・域外は呼ばない・例外なし) | ルール | transit_state | なし | arbiter.py:335 | `if outside is not None:` | — |
| C02 | 就寝抑止(例外=計画境界・顕著・会話) | ルール | 状態 | なし | arbiter.py:361 | `blocked_sleep = sl[...] & ~ex` | — |
| C03 | 不応期(体×条件 11 列) | ルール | tick | なし | arbiter.py:396 | `blocked = ru[agent, cond] > int(tick)` | state.py:268-280(expedient 多数) |
| C04 | 呼数の上限 L4(floor で頭打ち) | ルール | 呼数 | なし | arbiter.py:465 | `n_sel = min(n_sel, int(np.floor(float(budget) + 1e-9)), agent.size)` | 34.72 呼/tick@5,000(L4 按分) |
| C05 | 活動中は場所の変化(CELL_BLOCK)で起こさない | ルール | tick | なし | activity.py:357 | `drop = (...cond... == CELL_BLOCK) & (au[...] > int(tick))` | — |
| C06 | 場所の変化: B4 欄(LOS 段・騒音・流れ・顕著)が変わったセルの在席者を起こす | 空間 | 在席数÷歩行可能面積 | なし | change_detect.py:161,297,375 | `los = PN.peg_stage_array(per_m2, PT.DENSITY_LOS_EDGES_PER_M2)` | LOS 境界 mechanism・分母 expedient |
| C07 | 内受容段の跨ぎ(ヒステリシス) | ルール | 値 0-10 | なし | change_detect.py:73,303 | `INTERO_UP_EDGES: Final[tuple[int, ...]] = (4, 7, 9)` | 4/7/9・幅 1(expedient) |
| C08 | 顕著行為の候補=同セル+4 近傍(80 m の代用) | 空間 | セル隣接 | なし | salient.py:395 | `cells = [int(cell)] + [int(c) for c in self._neighbours[int(cell)] if c >= 0]` | 十字近傍(expedient) |
| C09 | p_notice: 打ち切り距離・d50・偏心・照明・密度・負荷・社会伝播 | 空間 | 直線距離・向き・密度 | なし | p_notice.py:441,472 | `idx = np.flatnonzero(d_all <= prm.cutoff_m)` | 80 m・40 m・15 m・密度 1/0.5/0.2(expedient)・E2 6.22°(mechanism) |
| C10 | 顕著事象の上限/tick | ルール | 件数 | なし | salient.py:222 | `if not self.budget.admit(int(tick)):` | 200(宣言値) |
| C11 | p_notice の密度クラス(density_stage を 2/4 で 3 値) | 空間 | 密度段 | なし | salient.py:485 | `np.searchsorted(np.asarray([2, 4]), stage, side="right")` | 境界 2/4(expedient) |
| C12 | B2 可視物: W8 T1 のセル集約・視点数降順・POI ≤8・目印/出口 ≤4 | 空間 | 前計算の視線 | なし | renderer.py:504-509 | `elif len(pois) < 8:` | 8/4 件 |
| C13 | 看板の注視 p_see(体×看板×tick のベルヌーイ・既定 1.0=抽選なし) | 空間(名目・距離も向きも使わない) | 確率 | なし | renderer.py:1175,1184 | `if self.signage_p_see >= 1.0:` | 既定 1.0 |
| C14 | 近接 k: **同セル在席者だけ**を距離で上位 k(LOS≤1→3・≤3→2・他 1)+知人+焦点 | 空間 | 同一セル・距離 | なし | renderer.py:1403 | `k = 3 if los <= 1 else (2 if los <= 3 else 1)` | 境界(expedient) |
| C15 | 注意段 2: 顕著行為は上位 2 件 | ルール | 件数 | なし | salient.py:376 | `kept = AT.apply_budget(ranked, AT.BUDGET_SALIENT)` | 2 |

**件数**(71 件): **空間系 25**(A01-A09・A12・A13・A16・A20・A25・A29・A31・A35・B10・C06・C08・C09・C11・C12・C13・C14)/ **ルール系 35** / **両方 11**(A10・A14・A24・A37・A39・A40・A41・B01・B07・B08・B09)。空間を含む=36・ルールを含む=46。
結果コードを書くのは 1-A の判定だけ(B/C 群は計数・抑止・掃除)。**空間系の判定が出す失敗コードは UNREACHABLE・TARGET_GONE・PARTNER_GONE・TRAIN_FULL・BAD_TARGET(あたり/対象なし)・NO_TRAIN(行けるホームなし)の 6 種**。

## 2. 位置と空間の表現(事実)

- **tick = 60 秒**: `core/types.py:93` `DEFAULT_TICK_SECONDS: Final[int] = 60`。
- **セル**: 100 m 格子 × 層(`world/assets.py:78` BAND_CODES UG=-1/GL=0/DECK=1・`:80` CELL_SIZE_M=100.0)。手元資産 `w2_cells.parquet` = **520 セル**(GL 453・DECK 39・UG 28)。ノード→セルは格子式(assets.py:375)。代表ノード=セル内ノード重心に最も近いノード(build/geo/w2_cells.py:17)。
- **ノード/辺**: W1 = **3,499 ノード**(GL 3,163・DECK 200・UG 136)・**4,944 辺**(長さ 最小 1.0・中央 21.75・最大 1,030 m)。経路は **W3 全点対 next-hop 表**(3,499²・int32・mmap・assets.py:381)を 1 回のファンシー添字で引く(graph.py:69)。W3 のセル間距離 `cell_dist`(520² uint16)は読み込まれるが(assets.py:382)**engine からは読まれない**。
- **個体の位置の欄**(agents/state.py): `cell` int32(:375)・`node` int32(:377)・`band` int8(:379)・`xy` float32×2 [m](:381)・`path_next_node` int32(:383)・`target_node` int32(:385)。edge 腕だけ `edge_id` int32(:389)・`edge_s` float32 [m](:392)。
- **node 幾何(既定)**: 1 tick に 1 ノード(graph.py:75-88・resolve.py:1096)。`xy` は毎 tick ノード座標で上書き=位置は 3,499 点に量子化(resolve.py:1029)。中央辺長 21.75 m/tick は 0.36 m/s 相当(読み役の計算・graph.py:11-12 が「実資産ではもっと遅い」と宣言)。
- **edge 幾何(C9a・`--geometry edge`)**: 体は辺 `edge_id` 上・`node` から `edge_s` m・向き `node→path_next_node`。`xy` は両端ノードの線形補間・セル/層は近い方の端点(geometry.py:394)。新しい行動を選ぶと近い端点へ吸着(resolve.py:970-985・geometry.py:414)。
- **速度モデル**: 希望速度 `desired_speeds`=seed×id の決定論で U(1.00, 1.60) m/s(geometry.py:93-95,148-162)。減速 `kladek_speed_factor` v/v0=1−exp(−1.913(1/ρ−1/5.4))(geometry.py:129-145)。ρ は**前 tick 末のセル在席数÷セルの歩行可能面積**(geometry.py:263-277=セル内で一様)。
- **1 tick の最大ホップ**: 32(geometry.py:99)。超過分は捨てる(geometry.py:39-40 注記)。
- **可視表 W8**(build/vis/w8_visibility.py): 視点=W10 街路点(2.5 m 格子・手元 **356,732 点**)・対象=POI 2,337/駅出口 45/建物 7,210。眼高 1.5 m・最大視程 150 m(:59 expedient)・**建物 footprint の 2.5 m ラスタ×DEM による 2.5D 遮蔽**を前計算(:13-18)。実行時に読むのは `w8_t1_cell.parquet`(セル×対象×**視点数** 43,479 行)だけ(renderer.py:477-514)。`w8_t2.npy`(520×520 float16・セル→セル)は src の実行時コードから読まれない。
- **歩行可能面積(密度の分母)**: 既定 `legacy`=max(W10 街路点数×6.25 m², 1,500 m²)(renderer.py:621・expedient)/ `--area-source plateau`=`c9c_walkable_area.parquet`(C9c-1・assets.py:155-199・手元 520 行・中央値 999.7 m²)。同じ 1 本がレンダラ・変化検出・EdgeGeometry に渡る(run.py:1559,1621,1629)。
- **遮蔽(C9c-2)**: 未実装(§3-2)。
- **密度の段階**: `world.cells.density`=セル在席数の bincount(world/state.py:192-196)。checkpoint に入る `density_stage` は node 幾何=人/セルの自前 7 境界(world/state.py:65 `(1, 5, 20, 60, 150, 400, 1_000)` expedient)・edge 幾何=**Fruin LOS 人/m²**(world/state.py:72・geometry.py:283)。知覚の B4 LOS 段は幾何によらず人/m²(change_detect.py:161・templates.py:172)。
- **未接続の物理定数**: ホーム滞留 3.30 人/m²・整列乗車 4.00-4.50・通路 3.33 人/m²(assets.py:131-140「未接続」)。

## 3. 設計者が挙げた 6 項目の現状

### 3-1 D-94 席数
- 実行時の既定: `SEAT_AREA_M2 = {"food": 2.0, "nightlife": 2.0}`(crowd.py:67)・それ以外 4.0(:71)。席数=`max(1, int(床面積 // m²/人))`(:134)。床面積は**カテゴリ別の想定値**(crowd.py:74-94・food 60 m²→30 席)。
- 法定 3.0: `SEAT_AREA_M2_FIRE_CODE = {"eatery": 3.0, "retail": 4.0}`(assets.py:126)は**定数として在るが既定ではない**。建告 1.43/2.0 も同様(:130)。感度腕 `--seat-area-eatery`(cli.py:688→run.py:1407-1410)は food と nightlife の**両方**を上書きする。
- 食い違い(事実): 「食事」の前提は `hash_free_cat_code==1`(food/飲食/restaurant/cafe・assets.py:499)、席面積の表は cat 名の完全一致("food","nightlife")。nightlife は食事の対象外だが席面積 2.0。
- 物理層が置き換えるなら、いま担っているもの: `CrowdProcess.can_admit` の整数比較 1 本(crowd.py:212)+想定床面積表(crowd.py:74-94)。

### 3-2 C9c-2 遮蔽表
- **実装なし**。仕様の所在: docs/design/v2-c9-geometry-agenda.md:22(G7 (c) 遮蔽表=PLATEAU 足跡の事前計算)・:56(G13 (iii) レイキャストを事前計算した表)・:70(空欄: 遮蔽表=C9c-2)・:72(第228 決定: C10 の被注視/傍受の結線に束ねる)。
- 既に在る遮蔽: W8 の**街路点→POI/出口/建物**の 2.5D 視線(build 時のみ)。人→人・音の遮蔽は無い: 近接 k は同一セル在席者を直線距離で並べるだけ(renderer.py:1390-1403)・p_notice は直線距離と向きだけ(p_notice.py:440-472)・会話は同一セル/直線距離(resolve.py:1958-1963)。
- 被注視・傍受・近接入替・知人出現の起床(WakeCondition 6-9)を発生させるコードは無い(§5)。

### 3-3 D-120 到達可能性(現状の到達判定)
- 到達=**next-hop 表に経路があるか**だけ。時間・距離の上限は見ない。`UNREACHABLE` の条件: 行き先セルが範囲外/近づく対象ノードが取れない/`next_hop<0` かつ同一ノードでない(resolve.py:1198-1219)・継続中に前進できない(node: resolve.py:1097・edge: geometry.py:323,335)。
- 「次の予定までに歩ける範囲」の判定は無い。乗車のホーム選択は直線距離順(A13)。

### 3-4 D-115 退出を歩かせる(現状=その場で消える)
- 計画実行層の DEPART → `_depart_now`(presence.py:1239-1254)→ `resolve.rail_depart`(resolve.py:2274-2288)が `transit_state=2`・`cell=-1`・`node=-1`(:2284-2285)を**その tick にその場で**書く。退出の形は `immediate` のみ実装(presence.py:77-78,602)。
- 到着は W11 出口セルへ round-robin(presence.py:922-926)→ `rail_arrive` がセル代表ノードへ直置き(resolve.py:2256-2271)。
- LLM の「乗車」はホームまで歩いて列に並び、便の発車で運び出される(resolve.py:1418-1511・rail.py:640-657)=こちらは歩く。

### 3-5 D-106 マイクロ層
- 既定は 1 tick=1 ノード跳び(A04)。edge 腕でも「辺上の 1 次元位置+セル一様の密度減速」で、個体間の衝突・回避・レーン・列の幾何は無い。密度はセル(100 m)単位の bincount(world/state.py:192-196)。サブ tick の群衆層は無い。
- 物理層が置き換えるなら、いま担っているもの: `WalkGraph.step_once`(graph.py:75-88)/ `EdgeGeometry.advance`・`tick_budget_m`(geometry.py:268-366)。

### 3-6 満席の列(IMPLEMENTED #43)
- `_serve_poi_queue`(resolve.py:2330-2408)を `apply` の**先頭**で回す(:968)。順序=`(queue_since, agent_id)` 昇順の FIFO(:2352-2354)。閉店→CLOSED・払えない→MONEY_SHORT・棚空→OUT_OF_STOCK で列を離れ(:2357-2393)、空席ぶん `can_admit` で入れて購入/食事を完了(:2399-2407)。並んだ目的は `CrowdProcess.queue_action`(crowd.py:184)に `_remember_queue_action`(resolve.py:2323-2327)で控える。切替口 `queue_service`(resolve.py:900)。
- 列に**位置は無い**: 並んだ体は `activity=WAITING`・`queue_poi`/`queue_since` を持つだけで元のノードに居る(resolve.py:1699-1701)。列の長さは件数(crowd.py:254)で、B4b に「行列: <店名>に<人数>人」(`queue_rows`・crowd.py:309)。離脱 15 tick(A26)。

## 4. checkpoint に混ざる空間の欄と既定 checkpoint の作り方

- `Checkpoint`(engine/run.py:260-280): `tick`・`agents_hash`・`world_hash`・`population_hash`・`schedule_hash`・`activity_hash`。`combined`=blake3(`"\x1f".join`)で、`activity_hash` は空でないときだけ混ぜる(:276-280)。生成は run.py:2427-2435(`agents.state_hash()`・`world.state_hash()`・`act_layer.state_hash()`)。
- `agents_hash`=`Registry.state_hash`(core/soa.py:382-399): **宣言順に 名前・dtype・形・生バイト**。位置系の欄: `cell` int32・`node` int32・`band` int8・`xy` float32(2,)・`path_next_node` int32・`target_node` int32(常設)/ `edge_id` int32・`edge_s` float32(edge 腕)/ `focus_target` int32・`focus_ttl` uint8(edge∧v2 腕・run.py:1453)。位置に従う欄: `transit_state` int8・`transit_ref` int32・`board_line` int8・`sleep_pending` int8・`poi_ref` int32・`queue_poi` int32・`talk_partner` int32。
- `world_hash`=blake3(cells ‖ pois)(world/state.py:349): cells=`density` int32・`density_stage` uint8・`noise_stage` uint8・`open_count` int32・`b4_hash` uint64(LOS 段を含む)/ pois=`cell` int32・`node` int32 ほか(world/state.py:93-122)。
- checkpoint に**直接は入らない**空間の状態: `CrowdProcess` の席数・在席・列(crowd.py:173-184)・`EdgeGeometry.v_desired`(geometry.py:195)・列車の乗車人数・ホテルの `bed_cell`・`SalientProcess.event_seen_tick`。
- 既定 checkpoint(docs/bench/analysis/two-layer-2026-09-27/README.md:15,21,51-52): いずれも mock 5,000 体・seed 1・`data/world/v2`・1 日・final=tick 1439。**2f3969cf**=`--vocab-version v1`(node 幾何・edge/焦点/活動の欄なし・`activity_hash` 空)。**02bd0312**=旗なし=v3+活動層 on(`activity_until` int32・`activity_kind` int8 と `activity_hash` が加わる・golden は tests/engine/test_presence_executor.py:60)。両方とも W16/W17 が在るので `plan_activity`/`plan_flags` を確保(run.py:1446,1454-1460)。

## 5. 見つからなかったもの(探した場所)

- **年齢による前提**(未成年・飲酒など): `age` は宣言・初期化されるが(state.py:408・resolve.py:454-455)、engine/perception/world で読む判定は無い(`age` を src/shibuya の build 以外で grep)。
- **品揃えの一致**(欲しい物と店のカテゴリ): 購入の対象は現在セルの最小 id の POI(A20)・在庫は総数(A22)。カテゴリを照合する検査は無い(commit.py・resolve.py)。
- **移動の「途中打ち切り(混雑・閉鎖)」**: INTERRUPTED は列の離脱(resolve.py:2421 `balk_queue`)だけが書く。移動からは出ない(resolve.py・geometry.py)。
- **一度も書かれない結果コード**: REFUSED(11)・UNDEFINED_ACTION(16)・INSUFFICIENT_ABILITY(18)は state.py と renderer.py の表にしか現れない(`ResultCode.` を src 全体で grep)。NO_PERMISSION(14)は `request_open_close` だけが書き、唯一の呼び手が `permitted=np.ones(...)` を渡す(opening.py:195-202)。
- **契約の前提のうち engine に検査の無いもの**: 移動の「同層で連結」「現行動が中断可」(contract.py:202 → `_apply_move` は next-hop だけ)・退去の「所属中」(contract.py:281 → resolve.py:1996 は常に OK)・通報の「通報先が存在」(contract.py:295)。
- **被注視・傍受・近接入替・知人出現の起床**: `WakeCondition.BEING_WATCHED/OVERHEARD/PROXIMITY_SWAP/ACQUAINTANCE` を発生させる行は src に無い(commit.py:150-153 の予期クラス表だけ)。`watched_by=` を渡す行も run.py に無い(B5 被注視は常に 0)。
- **人→人・音の遮蔽**: 無い(§3-2)。`w8_t2.npy` と `cell_dist` は実行時に読まれない。
- **ボトルネックの流量容量**(改札・階段・横断歩道・ホーム面積): 無い。ホーム密度の定数は未接続(assets.py:131-140)。W11 駅内グラフは「ホーム→セル」の対応にだけ使う(assets.py:1050-1070)。W4 建物・W5 入口は実行時に読まれない(`w4_`/`w5_` を build 以外で grep)。
- 注記(文書のずれ): resolve.py:37 の docstring「乗車は列車が無いので必ず NO_TRAIN」は現行コード(鉄道過程があれば乗れる・resolve.py:1418-1511)と食い違う。PENDING の D-115 行(pending-archive-2026-09-28.md:151)が引く `resolve.py:2098` は、現行では `rail_depart` 本体 resolve.py:2274-2288。
