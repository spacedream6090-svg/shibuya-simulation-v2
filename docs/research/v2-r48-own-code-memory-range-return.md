# R-48 自前コードの読み取り: 記憶の現状・範囲外の予定・戻ってきたときの状態

- 種別: コード読み(推測なし。各主張に `path:line` と引用を付ける)。書き手=読み役サブ(Opus 5.5)。**親検収 済(第278)**: 「親への注意」の主張 5 件(`resolve.py:838` の分岐なし加算・`rail_arrive` `resolve.py:2256-2271` の書く欄・`change_detect.py:302-310` に在圏条件なし+`arbiter.py:335-351` の域外抑止・`conversation.py:151` の「本数だけ」・`commit.py:566-589` `_poi_in_cell` の最小 id と `state.py:459-460`/`resolve.py:2311` の `poi_ref`)を親が同じ行を印字して一致。設計への写し=[空腹・判断層・注意の草案 v1](../design/v2-hunger-choice-attention-draft.md) §5(表)と K9。
- 対象コミット: `42e8c9e`(第277・ブランチ build/vocab-v3・作業木 clean)
- 読んだファイル(主なもの): `src/shibuya/agents/state.py`・`agents/weekly.py`・`agents/schedule.py`・`engine/resolve.py`・`engine/run.py`・`engine/presence.py`・`engine/conversation.py`・`engine/activity.py`・`engine/arbiter.py`・`engine/change_detect.py`・`engine/commit.py`・`engine/tape.py`・`engine/llm_bridge.py`・`engine/processes/salient.py`・`engine/processes/rail.py`・`engine/processes/crowd.py`・`perception/renderer.py`・`perception/templates.py`・`perception/state.py`・`perception/attention.py`・`economy/ledger.py`・`llm/mock.py`・`build/sched/w17_schedule.py`・`build/sched/pool_facts.py`・`build/sched/trial.py`/ 文書: `docs/design/v2-action-contract.md`・`v2-c10-relations-brief.md`・`v2-two-layer-implementation-agenda.md`・`v2-memory-agenda.md`・`PENDING.md`
- 実行確認 2 件(リポの `.venv` の python・ファイルは書かない): ① `advance_body` を 3 体(在圏で就寝/域外で待機/在圏で idle)に tick 0〜510 回した ② v3 の休息回復が域外の体に掛かるか。結果は §B2-3 に書く。
- 以下、`src/shibuya/` を省いて `engine/resolve.py` のように書く。

---

## §B1 エージェントの記憶の現状

### B1-0 総論
- **「記憶」を名乗るモジュール・レジストリは src に無い**。`find src tests -iname "*memory*" -o -iname "*episode*" -o -iname "*recall*" -o -iname "*reflect*"` は 0 件。`grep "episode|エピソード"` も src で 0 件。
- 体の SoA は、記憶を別のレジストリに置く予定だと自分で書いている: `agents/state.py:8`「(T0習慣 M3・記憶 M4・関係 M5・プロフィール M6 は C3 以降の別レジストリ)」。その別レジストリの宣言は見つからなかった。
- `engine/resolve.py:38`「会話は**セッションレコードを作るだけ**(発話ブロック・終了判定・記憶転写は C3/C4)」。

### B1-1 「記憶らしきもの」の総当たりと分類
| 分類 | 実体(欄・場所) | 書き手 | 読み手 |
|---|---|---|---|
| (A) 直近 1 件を上書きで持つ体の欄 | `last_action`・`last_result`・`last_result_tick`・`fail_streak`(`agents/state.py:489-497`) | `resolve._ok/_fail`(`resolve.py:1065-1083`)・`balk_queue`(`resolve.py:2411-2423`) | B6「直前の結果」(`perception/renderer.py:1795-1817`)・活動層の失敗即時満了(`engine/activity.py:292`) |
| (A) 現在の状態 | `activity`(`state.py:432-433`)。B5 の「直近」行はこれを描くだけ: `renderer.py:1336-1338` `T.TEMPLATES["B5.recent"].format(activity=_activity_word(int(a.activity[i]), ...))`(文面 `templates.py:630`「直近の行動は{activity}です。」) | resolve | B5 |
| (A) 活動(v3・二層) | `activity_until`/`activity_kind`(`state.py:476-481`)+ Python 側の `ActivityLayer.text`(体ごとの活動文・上書き。`activity.py:178` `self.text: list[str] = [NO_TARGET] * self.n`・`activity.py:302-307`) | `resolve.set_activity`(`resolve.py:791-807`)・`ActivityLayer.after_resolve` | B4b の同セル 1 行・満了入口(`activity.py:340-348`) |
| (B) 一時的な在席・行列 | `poi_ref`/`poi_since`/`queue_poi`/`queue_since`(`state.py:459-466`) | 購入/食事の完了で書く(`resolve.py:1766-1770`・`1853-1857`)。解除=`release_indoor`(`resolve.py:2304-2316`)を 30 tick の回転率で(`processes/crowd.py:96` `DWELL_MAX_TICKS = 30`・`crowd.py:231-233`)、退出時にも(`presence.py:1239-1254`) | 屋内占有の集約(crowd) |
| (C) 起床判定用のタイマー | `refractory_until`(体×条件・`state.py:483-485`)/ 会話の拒否記憶 `_refusal_until`(対→tick・`conversation.py:89-90` `REFUSAL_MEMORY_TICKS = 60`・`conversation.py:558-559`)/ 同一相手 60・同一話者 30(`conversation.py:107,110`)/ 顕著行為を見た最後の tick `event_seen_tick`(`processes/salient.py:164-167`) | resolve・ConversationManager・SalientProcess | アービタ・会話の開始ゲート・通報の前提(`resolve.py:2019-2025`・窓 `REPORT_WINDOW_TICKS = 5` `resolve.py:208`) |
| (D) 体が読まない外部記録 | テープ `response` 列(`engine/tape.py:111`・1 呼 1 行・応答全文)/ 経済台帳の生ログ(`economy/ledger.py:662-690`: tick・払い手・受け手・金額・科目のリングバッファ)/ 会話 `Session` 表(`conversation.py:276`) | TapeWriter・MoneyLedger・ConversationManager | エンジン・知覚からの読み手は見つからなかった(`raw_rows` の参照は `ledger.py` 内のみ。テープの再生 `Replay` は同じ呼の応答を引くだけ) |
| (E) 宣言だけで使われていない | `perception/state.py:103-106` の `last_b2_hash`/`last_b4_hash`(dormant 再送抑止用)/ 文面 `templates.py:635-636` の `B5.overheard`・`B5.ad`/ 知人表 `Renderer(acquaintances=...)`(`renderer.py:754`) | 書き手なし(grep で宣言以外 0 件)/ renderer に `B5.overheard`・`B5.ad` を使う行は 0 件 / `run.py:1546-1557` の `PerceptionRenderer(...)` は `acquaintances` を渡さない=**本番ランの知人表は空** | — |

結論(B1): **自由文ログも、構造化されたエピソード欄も無い**。体が次の判断で読めるのは「直前 1 件の結果」「現在の状態・所持金・所持数・内受容」「活動文(v3)」だけで、どれも上書き。

### B1-(i) 「最近行った店」「最後に購入した店」の欄
- **無い**。SoA で店に関わる欄は `poi_ref`(「在席中の POI 索引(-1=なし)」`state.py:459-460`)と `queue_poi`(`state.py:463-464`)だけ。どちらも在席・行列が終われば −1 に戻る(`resolve.py:2311` `r.poi_ref[a] = -1`)。
- 店を**選ぶ処理も履歴を読まない**: 購入・食事の対象は「自分のセルにある POI の最小 id」(`engine/commit.py:566-589` の `_poi_in_cell`・docstring「各体のセルにある POI の**最小 id**」)。使う箇所は `commit.py:716-718`(購入)と `735-737`(食事・`keep=world.eatery_mask`)。
- 購入の事実は経済台帳の生ログ(払い手=体 id・受け手=店)に残るが(`ledger.py:507-514` `purchase_many` → `_record`)、体の側からそれを読む処理は無い(B1-1 (D))。
- mock 方策も履歴を読まない: `llm/mock.py:14-16`「行動語の**一様**抽選、対象の選び方は全て自前」。

### B1-(ii) 会話の内容はどこに残るか
- **体の欄・Session・manifest には残らない**。`Session` は話題の本数しか持たない: `conversation.py:151`「topics: 話題スタック(本数だけを持つ・中身は使わない)」・`conversation.py:166` `topics: int = 0`。
- `ConversationManager.utterance(..., comment="")`(`conversation.py:611-647`)は docstring で「comment: 「ひと言」欄(発話本文)」として受け取るが、本体に `comment` を参照する行は無い(呼数・話者交替・終了判定だけ)。呼んでいる側は `run.py:2150` `conv.utterance(a, tick, action=res.parse.action, comment=res.parse.comment)`。
- 残る唯一の場所は**テープの `response` 列**(`tape.py:111`)。LLM の 2 行応答の全文が入る(テープを書くランだけ)。艦隊の debug jsonl に残るのは初回パースに失敗した呼だけ(`run.py` の `fleet_debug_dir` の docstring)。
- 相手の発話は**相手の観測にも出ない**: 傍受の文面 `B5.overheard` は定義されているだけで、描画には使われていない(B1-1 (E))。
- 会話が残す「記憶」は、拒否/無視した対 → 期限 tick(`conversation.py:558-559`)と招待の不応期だけ。どちらも 1 ランの `ConversationManager` の中にしか無い(`run.py:1432` でランごとに新しく作る)。

### B1-(iii) 看板の注視・顕著行為の注意の結果はどこに残るか
- **看板(p_see・D-59 (b))**: 体×看板×tick の決定論ベルヌーイ(`renderer.py:1158-1193`)。結果は「その呼の B2 に看板行を載せるか」に使われたら捨てられ、体の欄には残らない。残るのは全体の計数 `signage_gate_draws`/`signage_gate_shown`(`renderer.py:801-803`)だけで、診断行に出る(`engine/llm_bridge.py:375-384`)。既定 `SIGNAGE_P_SEE_DEFAULT = 1.0`(`renderer.py:116`)では抽選そのものを引かない(`renderer.py:1175-1176`)。
- **顕著行為(p_notice)**: 気づいた体は tick ごとに作り直す配列 `noticed_agents` に入る(`salient.py:186` で毎 tick 空にし `salient.py:257` で埋める)。この配列は起床条件 (i) `CELL_BLOCK` の候補になる(`salient.py:280-300`)。体ごとに残るのは「事象の行が自分のセルの B4 に出た最後の tick」`event_seen_tick` だけで(`salient.py:167`・`_mark_seen` `salient.py:262-272`)、読むのは通報の前提検査だけ(`resolve.py:2019-2025`・5 tick の窓)。
- `perception/attention.py:119-121` の `MEMORY_CAP_RECOGNITION = 0.40`・`MEMORY_CAP_RECALL = 0.08` は定数を宣言しているだけで、これを使う記憶の実装は見つからなかった。

### B1-(iv) 文書が「未実装」と宣言しているもの(引用)
- 行動契約書 §4(`docs/design/v2-action-contract.md:53-54`): 「基準値: 宛先=発話全文1レコード(重み1.0)/非宛先=要約1文(0.5)/傍受=3段ゲート通過分のみ要約1文(0.2)。**ユーザー決定: パラメータは個体で可変**」。§8 登録簿(`:85`)「記憶転写の重みと個体差写像 | 1.0/0.5/0.2×個体係数 | 第2陣」。§4 本文には「未実装」という語は無い。
- C10 ブリーフ(`docs/design/v2-c10-relations-brief.md:58`): 「**発話の内容はどこにも保存されていない**: `Session` は `blocks`(生成数)しか持たず要約も逐語も記録しない。行動契約 §4「記憶転写の規則」…は**未実装**」。
- 二層の実装アジェンダ(`docs/design/v2-two-layer-implementation-agenda.md:120`): 「活動文の記憶転写は**実装していない**: 行動契約書 §4 の記憶転写…がエンジンに**存在しない**」。同 `:153`「記憶 第 1 段(D-93・M1〜M16)で活動文を転写の対象に含める」。
- `PENDING.md:130`(D-93 の末尾・第276 の追記): 「二層の活動文の記憶転写(草案 §4-4)は行動契約書 §4 の転写がエンジンに無いため空欄=記憶 第 1 段で扱う」。
- `PENDING.md:132`(D-95): 「設計は認知設計 §4 で決定済み…だが**コードは無い**(src に記憶モジュール無し…)」。記憶アジェンダ `docs/design/v2-memory-agenda.md:1`「記憶の実装アジェンダ v0(…ユーザー Q&A 待ち)」、同 `:29` の M13「(a) 訪問カウンタだけ先」。
- **番号の注意**: D-93 の本題は「C10 着手条件(指紋 3)の置き換え」で、記憶の実装そのものの行は **D-95**。「記憶 第 1 段」という語は、D-93 の追記とアジェンダ `:153`(`D-93・M1〜M16` と表記)に出てくる。

---

## §B2 範囲外の予定

### B2-1 何から「範囲外」が決まるか(W17 のあるラン)
- 計画実行層 `engine/presence.py`(D-66)が W17 週次表を「在圏ブロック」にまとめる。在圏とみなす行は「場所≠域外 ∧ 活動≠乗車 ∧ 域外居住者の自宅行でない」: `presence.py:483` `live = pk != PLACE_KIND_OUTSIDE`・`presence.py:486` `live &= ~(ho[rows] & (pk == PLACE_KIND_HOME))  # 域外居住者の「自宅」行は域外`。読み方の既定は v2(`presence.py:101-102`)。
- **範囲外の時間=在圏ブロック以外の時間**。範囲外の中身を別に生成・模擬するコードは無い。tick 0 に在圏でない体は `place_at_external` で外に置かれ(`presence.py:1066-1080`)、以後は ARRIVE/DEPART イベントで出入りする。
- 範囲外の間、W17 の行の活動語は `plan_activity`(計画の写し・`state.py:469-471`)にだけ書かれる: WAKE/SLEEP イベントは域外の行も含めて全行積まれ(`presence.py:1029-1031`)、`presence.py:1176-1180` `R.set_plan_state(self.agents, ids[upd], activity=act[upd])` で書かれる。実際の `activity` は `WAITING` のまま(`resolve.py:2251`・`2287`)。
- 範囲外の体には LLM を呼ばない: `run.py:2085-2091`(`outside_mask`)→ アービタが例外なく落とす(`engine/arbiter.py:335-351`)。落とした候補は保留にも入らない(`arbiter.py:591` `self._store(decision.deferred)`=繰り延べ分だけを保存)。就寝も実行されない(`resolve.py:628` の `(st == 0)` 条件・`resolve.py:640` `zero["outside"]`)。

### B2-2 W17 はどんな入力から作られたか(`build/sched/w17_schedule.py`)
- 入力ファイル: `w16_population.parquet`・`w7_plan_spec.parquet`・`w6_poi.parquet`・`w12_generation_weights.parquet`(`w17_schedule.py:117-122`)+ ペルソナプール `persona_pool_v2`(`:124`。読むのは `build/sched/pool_facts.py:1-9` の職業・シフト・勤務日・来訪頻度・就寝時刻など)。
- 生成は LLM: `w17_schedule.py:66` `MODEL_HINT = "Qwen3-8B-INT8"`・`:68` `TEMPERATURE = 0.7`。種別ごとの system 行で「域外」の書き方を指示している(`:240-270`。例: 通勤者「帰りは 移動 駅 と 乗車 域外 で書く。…休みの日も…(自宅と域外で過ごす)」)。user プロンプトには「自宅: 域外」「勤務: 渋谷の外(域外)」が載る(`user_prompt` `:542-`)。場所語「域外」を書けるのは、域外常住・域外通勤通学・来街種別の体だけ(`place_set` `:592-615`)。無職は `:522`「域外へは出ない」。
- 後処理: 整合の修復 + **骸格**による補完(`skeleton_day` `:905`・「全て expedient」)+ raking。raking に使う時間帯カーブは **W12 の hour 重み=第12回大都市交通センサス time_dist_12(2015)** で、**PT の時間帯別表は未取得**(`w17_schedule.py:18-22`)。
- **社会生活基本調査は本番 W17 に入っていない**。src に出てくるのは、D-68 下見の別経路 `build/sched/trial.py:341-345`(令和3年 平均時刻編 第31/36表=P1 腕の勤務時間帯)と、アービタの検証用 a(h) の注記 `engine/arbiter.py:71-74`(「a(h) は**検証**…にだけ使う」)の 2 か所だけ。
- **範囲外の間に何をしているか(食べた・寝た・働いた)を統計から与える入力は、エンジン側では見つからなかった**。W17 の域外行の活動語は `plan_activity` と計画一致率の分母にしか使われない。

### B2-3 範囲外の間、空腹は更新されているか
- **更新されている(在圏と同じ規則・分岐なし)**。`resolve.py:821-858` の `advance_body` は配列全体に掛かる: `resolve.py:838` `r.hunger[:] = np.minimum(r.hunger.astype(np.int16) + 1, 10)`。`transit_state` を見る行は無い。毎 tick の先頭で呼ばれる(`run.py:1737-1738`)。
- 空腹 v1 の規則(数値を確認した): 周期 `BODY_TICK_PERIOD = 30`(`resolve.py:148`・1 tick = 60 秒 `engine/clock.py:10`)ごとに +1・上限 10/購入で −4(`BUY_HUNGER_RELIEF = 4` `resolve.py:150`・適用 `resolve.py:1762-1764`)/食事も同じ量(`EAT_HUNGER_RELIEF = BUY_HUNGER_RELIEF` `resolve.py:188`・適用 `:1850-1852`)/初期値 2(`resolve.py:466`)。**睡眠中も空腹は上がる**(睡眠で下がるのは疲労だけ `resolve.py:840-845`)。
- 空腹で起こす条件(D-111 の根拠側): 空腹専用の起床条件は無い。空腹・疲労・体感温度の 3 変数が共通の `WakeCondition.INTEROCEPTION`(`state.py:254`)を使う。段の閾値は `INTERO_UP_EDGES = (4, 7, 9)`・ヒステリシス 1(`engine/change_detect.py:73-75`)・不応期 45 分(`state.py:275`)。B5 は 4 以上で「空腹は{v}で閾値を超えています」を描く(`renderer.py:1321-1322`)。
- **段の跨ぎは範囲外の体でも検出され、段の値も書き換わる**(`change_detect.py:302-345` に在圏の条件が無く、`resolve.py:719-728` の `apply_detection` が段を書く)。ただし起床候補は域外抑止で捨てられる(B2-1)。
- 疲労も範囲外で +1/30 tick 上がり、睡眠による回復は掛からない(`activity` が `WAITING` なので `resolve.py:840` の `sleeping = r.activity == int(Activity.SLEEPING)` に入らない)。例外: v3 の休息回復(`resolve.py:846-858`)は `transit_state` を見ない。域外に出る前の `IN_SHOP`/`IN_PLACE` 活動の `activity_until` が残っている体には、域外でも −1/10 tick が掛かる(`rail_depart`/`place_at_external` は `activity_until` を触らない `resolve.py:2235-2287`)。
- 実行確認(`advance_body` だけを回した・3 体・初期値 空腹 2/疲労 2): tick 0 で空腹 3(tick 0 も `0 % 30 == 0` で加算される)、tick 210 で 3 体とも空腹 10。疲労は 在圏で就寝 0/域外で待機 10/在圏で idle 10。v3 の確認: 域外・`IN_PLACE`・until 100 の体は tick 1〜29 で疲労が 8→6、活動なしの体は 8 のまま。

### B2-4 W17 が無いラン(mock 日課)
- `agents/schedule.py:1-8`「**mock 専用**の合成 T0 週次スケジュール」・1 日 5 境界(`:61-62`)で、範囲外の概念は無い。計画実行層が立たないランでは、rail が乱数で 12% を域外居住にする(`processes/rail.py:147` `EXTERNAL_HOME_PERMILLE = 120`・`rail.py:354-362`。計画実行層のランではこの抽選をしない)。

---

## §B3 渋谷に戻ってきたとき

### B3-1 戻る経路と、戻る時に書き換わる欄
- 経路: 計画実行層の ARRIVE(`presence.py:1182-1204` → `R.rail_arrive`)/ LLM の乗車・退去で出た体を次の在圏ブロックへ入れ直す処理(`presence.py:1324-` `_rearm_after_leaving`・最短外出 `RETURN_MIN_AWAY_MIN = 60` `presence.py:75`)/ 計画実行層なしのランの rail 到着(`processes/rail.py` の step 内の `R.rail_arrive`)/ civic の引き込み。
- `rail_arrive` が書く欄はこれだけ(`resolve.py:2256-2271`): `transit_state=0`・`transit_ref=-1`・`node`/`cell`/`band`/`xy`=降車セル・`activity=IDLE`・`target_node=-1`。
- 降車セルは駅出口セルを順番に割り当てる(`presence.py:926` `arr_cell = exits[rank % exits.size]`)。乱数の再抽選でも、記憶に基づく選択でもない。
- ARRIVE イベントは `plan_activity` をブロック先頭行の活動語にする(`presence.py:1176-1180`)。

### B3-2 状態ごとの扱い(初期化/再抽選/凍結/継続)
| 状態 | 範囲外の間 | 戻った時点 | 根拠 |
|---|---|---|---|
| 空腹 | **進み続ける**(+1/30 tick・上限 10・食べる手段なし) | そのまま(初期化も再抽選もしない) | `resolve.py:838`・`resolve.py:2256-2271` |
| 疲労 | **進み続ける**(睡眠の回復なし。v3 で活動が残っている体だけ例外) | そのまま | `resolve.py:839-858` |
| 内受容の段 | 範囲外でも更新される=**跨ぎは外で消費済み** | 戻っても同じ段なら、新しい INTEROCEPTION 起床は出ない | `change_detect.py:302-345`・`resolve.py:719-728`・`arbiter.py:591` |
| 所持金・所持数 | 変わらない(域外の体の所持金を書く行が無い。運賃を引くのは在圏で乗車した時だけ `resolve.py:1621`) | そのまま | 所持金の全書き手 = `resolve.py:461,464,1621,1729,1847` |
| 活動 | `WAITING`(`resolve.py:2251,2287`) | `IDLE` に置き直す | `resolve.py:2270` |
| 活動層(v3) | `activity_until`/`activity_kind` は残る。満了は `activity_until == tick` のときだけ起きる(`activity.py:340-342`)ので、外にいる間に過ぎた満了は起きない | 残った値のまま(未来の値なら `CELL_BLOCK` の抑止が続く `activity.py:350-364`) | `resolve.py:2235-2287` |
| 直前の結果 | 残る | B6 が経過時間に関係なく描く(`renderer.py:1798` が見るのは `last_result_tick < 0` だけ) | `renderer.py:1795-1817` |
| 記憶 | 無い(§B1) | 無い | — |

- **初期化はランの最初の 1 回だけ**: `resolve.initialize`(`resolve.py:420-481`・空腹 2・疲労 2・体感 5・所持金=日課の `initial_money`)を `run.py:1468` で呼ぶ。`run_day` は 1 シミュ日を回す関数(`run.py:1151-1206`)で、呼んでいるのは `cli.py:331` と `run.py:2840` だけ。**日をまたいで状態を持ち越す経路は見つからなかった**(=翌日のランは空腹 2、所持金は初期値から始まる)。
- 数値から言えること[計算・実行確認つき]: 空腹は tick 0 に 3 になり、tick 210(03:30)で 10 に達する。範囲外の体は食べられないので、**tick 0 から範囲外にいた域外居住者は、03:30 以降に戻ると空腹 10・疲労 10 で降りる**。空腹の段の跨ぎ(4/7/9)は外にいる間に起きて捨てられているので、戻った時点で内受容の起床は鳴らない(B5 の表示は、別の理由で呼ばれたときに出る)。
- 到着そのものを起床のきっかけにする専用の経路は見つからなかった(`run.py` の起床候補は 変化検出・計画境界・会話・顕著行為・満了・艦隊の繰り延べ=`run.py:1883-1960`)。戻った体が次に呼ばれるのは、このどれかによる。

---

## §まとめ表
| 問い | 答え | 根拠 |
|---|---|---|
| B1 記憶の形 | 記憶モジュールは無い。直前 1 件(結果・行動)と現在の状態の上書き欄だけ | `state.py:8`・`state.py:489-497`・`renderer.py:1336-1338` |
| B1(i) 最近行った店 | 欄は無い。在席中を示す `poi_ref` は解除で −1 に戻る。店選びは同じセルの最小 id | `state.py:459-460`・`resolve.py:2304-2316`・`commit.py:566-589` |
| B1(ii) 会話の中身 | 体・Session・manifest には残らない。残るのはテープの `response` 列だけ | `conversation.py:151,166,611-647`・`tape.py:111` |
| B1(iii) 看板の注視 | 体には残らない。全体の計数だけ(既定 1.0 では抽選しない)。p_notice は tick ごとの配列+`event_seen_tick` | `renderer.py:801-803,1158-1193`・`salient.py:167,186,262-272` |
| B1(iv) 文書 | §4 の転写は C10 ブリーフと二層アジェンダが「未実装」と明記。D-95 は「コードは無い」。記憶アジェンダは Q&A 待ち | 本書 §B1-(iv) の引用 |
| B2 範囲外の予定の出所 | W17(8B・温度 0.7・W16/プール/W6/W7/W12)の「域外」行を除いた残り(在圏ブロック)の外側。範囲外の中身は模擬しない | `presence.py:483-486`・`w17_schedule.py:66-68,117-122` |
| B2 統計の入力 | 本番 W17 は大都市交通センサス 2015(W12)で raking。PT の時間帯別表は未取得。社会生活基本調査は下見と検証だけ | `w17_schedule.py:18-22`・`trial.py:341-345`・`arbiter.py:71-74` |
| B2 範囲外の空腹 | 更新される(分岐なし)。段も書き換わるが、起床は捨てられる | `resolve.py:821-858`・`change_detect.py:302-345`・`arbiter.py:335-351,591` |
| B3 戻った時の状態 | 書き換わるのは位置と活動(IDLE)だけ。空腹・疲労は外にいた間も進んだ値、所持金は変わらない。初期化・再抽選・凍結はしない | `resolve.py:2256-2271` |

## §見つからなかったもの
- 記憶(エピソード)レジストリ・想起・内省の本体(探した場所: `src/` 全体を find/grep「memory|recall|episode|reflect|記憶|転写」)。
- 「最近行った店」「最後に購入した店」「訪問回数」の欄(探した場所: `agents/state.py` の全 `declare`・`perception/state.py`・`engine/activity.py`)。
- 会話の発話本文を体や Session に保存する行(探した場所: `engine/conversation.py` 全体・`run.py` の `conv.utterance` 呼び出し 3 か所)。
- 看板を見た結果を体ごとに保存する欄(探した場所: `perception/renderer.py`・`perception/attention.py`・`agents/state.py`)。
- 範囲外の間の活動(食事・睡眠・勤務)を状態に反映するコード、`advance_body` の在圏による分岐(探した場所: `engine/resolve.py`・`engine/presence.py`・`engine/processes/`)。
- 戻る時の初期化・再抽選・凍結(探した場所: `resolve.rail_arrive`・`presence._do_arrive`・`presence._rearm_after_leaving`・`rail.step`)。
- 複数日を続けて回して状態を持ち越す経路(探した場所: `run_day` を呼んでいる `cli.py`・`run.py`。`tools/` の grep でも単日の呼び出しだけ)。

## 親への注意(写し検査の材料)
- `PENDING.md:145`(D-111)に書かれた行番号 `resolve.py:140-142,746-753,1628`・`renderer.py:1202` は現行コードとずれている。現行は `resolve.py:148-150`(定数)・`821-858`(`advance_body`)・`1762-1764`(購入の −4)・`renderer.py:1321`(B5 の閾値表示)。
- D-93 と D-95 を取り違えないこと(§B1-(iv))。
