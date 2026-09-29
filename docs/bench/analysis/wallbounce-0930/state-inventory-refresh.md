# 状態・乱数・checkpoint の棚卸しの更新(R-55 → 現行コード・D-102 の実装アジェンダの材料)

- 日付 2026-09-30 / 読み役 Opus 5.5(実行役サブ)/ **推奨は書かない**(§7 の試験の形と §4・§5 の「案」だけは実装役の自前の構成=**未リサーチ(expedient)**と明記)
- 対象 commit `f9a3c97`(branch `build/spatial-d102-prep`)。同じ作業木で他のサブが動いているので、ここに書く行番号は読んだ時点の値。
- 比較元: [R-55](../../../research/v2-r55-own-code-state-checkpoint-rng-resume.md)(第281・commit 31645d8)。その後に入った実装 #49〜#75(IMPLEMENTED.md)を反映した。
- パスは `src/shibuya/` を省略(`tests/`・`tools/` はそのまま)。[実行確認] = `.venv` の Python(numpy 2.5.3)で import・AST 走査・小さな計算をして確かめた箇所。全体テストは回していない。
- 読み手の判定の基準は R-55 と同じ: `src/shibuya`(build/ を除く)を列名で走査し(属性 `.名前`・文字列 `"名前"` の両方・書き込み行を除く)、**読んで分岐・計算・描画に使う箇所**があれば「挙動」。描画(プロンプト)だけに効く読み手は「挙動(描画)」と分けた=mock は描画を読まないので final は動かないが、実 LLM では効く。

---

## §0 R-55 からの差分の要約

| 項目 | R-55(第281) | 現行 | 根拠 |
|---|---|---|---|
| SoA の列(agents・既定) | 36 列 127 B/体 | **40 列 137 B/体**(+意図の 4 欄 10 B) | [実行確認] `AgentState(10)`・`agents/state.py:599-608` |
| SoA の列(agents・全腕) | 44 列 147 B/体 | **79 列 5,373 B/体**(K=64・N=128・M=32・k=15) | [実行確認] 全旗 True |
| CLI の v3 既定(energy+activity+plan) | — | 48 列 160 B/体 | [実行確認] |
| 死蔵 | 3 列 | **3 列のまま**+知覚側 `last_b2_hash`・`last_b4_hash` は**書き手も無い**=死蔵(R-55 は「読み手未検出」) | 表 1 |
| 分類が変わった列 | — | `age`・`sex`(未検出 → 挙動: energy/classical)・`talk_partner`(未検出 → 挙動: 記憶/店の記憶の腕)・`revenue`(挙動 → 診断・監査) | 表 1 |
| **腕で分類が変わる列** | 議論なし | `age`/`sex`/`talk_partner`/`weight_kg`/`sm_last` は**構成によって読み手の有無が変わる** | 表 1・問い 1 |
| SoA の外の状態 | 18 行 | **+30 行前後**(意図・親しみ・記憶・店の記憶・関係辺・古典・エネルギー・計器・退出の歩行) | 表 2 |
| 状態を持つ乱数 | 2 本 | **2 本のまま**(`salient.py:160`・`civic.py:116`) | 表 3 |
| 呼ごとの乱数の用途 | 4 | **8**(+`policy.classical`・`engine.chooser`・mock の移動/店の 2 本) | 表 3 |
| run_salt のハッシュの用途 | 4(pk/ak/wk/wd) | **6**(+`ri`・`ri|rest`)+`near_tie_keys`(tick も day も入れない=宣言) | 表 3 |
| 日番号が鍵に無いもの | 呼ごとの流れ・salt・call_id・テープの鍵 | **呼ごとの乱数 8・salt のハッシュ 6(+near_tie)・call_id・テープの鍵・艦隊の seed・天気の種別と再生日・出勤率・mock 日課**=19 件 | 表 3・表 4 |
| tick を値に持つ状態(日をまたぐと Δt が壊れる) | 言及なし | **SoA 15 列+SoA の外 7 行**(不応期は `np.maximum.at` で**戻らない**) | 表 4 |
| テープの版 | 2(Q7 で「版 3」の予定) | **既に 3**(記憶の `recalled_rows`・#61)=Q7 の鍵の変更は**版 4** | `engine/tape.py:91` |
| checkpoint のハッシュ | 5 本 | 5 本のまま。**`activity_hash` に意図の控え `_payload` が混ざるようになった**・腕の列は on のとき `agents_hash` に入る | 表 6 |
| 再開の口 | 無い | 無いまま(`parent_run` は欄だけ・`save_registry` の呼び手は tests だけ) | §6 |
| 新しく見つかった複数日の障害 | — | **W17 v2 は曜日 0 の行しか無い**(1〜6 は 0 行)・天気の再生日が曜日の種別ごとに毎日同じ・出勤率の欠席が毎日同じ体・日の頭の初期化(活動・域外配置・空腹)が持ち越しを上書き | 表 5 |

---

## 表 1 SoA の全列(agents 79 列+world 14 列+知覚 4 列)

凡例: 確保=既定(常に)/腕名(その腕のランだけ)。タグ M=mechanism / E=expedient。分類: **挙動**=final か呼数を動かしうる読み手あり/**挙動(描画)**=プロンプトにだけ効く/**挙動(腕)**=特定の腕の中だけ読まれる/**診断・監査**=manifest・要約・保存則の検査だけが読む/**読み手未検出**=書くだけ/**死蔵**=宣言(と初期値)以外に参照 0。R-55 列: 同=分類同じ/新=R-55 以後に追加/変=分類が変わった。

### 1-a agents(`agents/state.py:505-716`)

| 列 | dtype | B/体 | 宣言 | 確保 | タグ | 書き手(代表) | 挙動に効く読み手(代表) | 分類 | R-55 |
|---|---|---|---|---|---|---|---|---|---|
| cell | i4 | 4 | :505 | 既定 | M | resolve | change_detect・commit・renderer・relations 他多数 | 挙動 | 同 |
| node | i4 | 4 | :507 | 既定 | M | resolve | resolve(移動) | 挙動 | 同 |
| band | i1 | 1 | :509 | 既定 | M | `resolve.py:508,1449,1475,2787` | なし(`world.assets.cell_band` は読まれるが SoA の band は読まれない) | 読み手未検出 | 同 |
| xy | f4×2 | 8 | :511 | 既定 | M | resolve・geometry | relations(同席 2 m)・norm_meter・salient・renderer | 挙動 | 同 |
| path_next_node | i4 | 4 | :513 | 既定 | M | resolve | `resolve.py:1395,1460` | 挙動 | 同 |
| target_node | i4 | 4 | :515 | 既定 | M | resolve | `commit.py:554-560` | 挙動 | 同 |
| edge_id / edge_s | i4/f4 | 8 | :519/:522 | 腕 edge | M | resolve | `resolve.py:1398,1465,1472` | 挙動(腕) | 同 |
| focus_target | i4 | 4 | :527 | 腕 attention | M | resolve | commit・resolve・renderer | 挙動(腕) | 同 |
| focus_ttl | u1 | 1 | :531 | 腕 attention | E | resolve | `resolve.py:1771-1778` | 挙動(腕) | 同 |
| kind | i1 | 1 | :535 | 既定 | M | initialize | renderer・classical・過程 | 挙動 | 同 |
| age | u1 | 1 | :538 | 既定 | M | `resolve.py:515`・`run.py:1397` | **`resolve.py:1171,1182,1200,1202,1227`(energy)・`classical.py:386,409`** | **挙動(energy/classical のとき)**・v1 空腹かつ mock では読まれない | **変**(D-118・D-119) |
| sex | i1 | 1 | :540 | 既定 | M | `resolve.py:517`・`run.py:1398` | 同上 | 同上 | **変** |
| hunger / fatigue / thermal | u1 | 3 | :542-546 | 既定 | M | resolve(advance_body・energy) | change_detect・bridge・renderer・classical | 挙動 | 同 |
| hunger_stage / fatigue_stage / thermal_stage | i1 | 3 | :550-554 | 既定 | E | `resolve.apply_detection` | `change_detect.py:77-80` の文字列表 | 挙動 | 同 |
| weight_kg | f4 | 4 | :558 | 腕 energy(CLI 既定) | M | `resolve.py:1172` | `resolve.py:1182`(**初期化時だけ** BMR を作る)・`energy.py:671`(要約) | 挙動(腕・初期化時)=派生値 `EnergyLayer.bmr` は SoA の外 | 新 |
| eer_kcal | f4 | 4 | :560 | 腕 energy | M | `resolve.py:1173` | `resolve.py:1153,1156,1203,1230` | 挙動(腕) | 新 |
| since_meal_kcal | f4 | 4 | :562 | 腕 energy | M | `resolve.py:1174,1204,1231` | `resolve.py:1156,1206,1234`(空腹の段) | 挙動(腕) | 新 |
| energy_balance | f4 | 4 | :564 | 腕 energy | M | `resolve.py:1155,1175,1205,1232` | `energy.py:593`(日次センサス・要約)だけ | **診断・監査** | 新 |
| money | i4 | 4 | :567 | 既定 | M | resolve・台帳 | resolve・chooser(予算) | 挙動 | 同 |
| holdings | u1 | 1 | :569 | 既定 | E | `resolve.py:2230` | `renderer.py:1793,2375`(手)・`goods_flow.py:473`(世帯の消費) | 挙動 | 同 |
| activity | i1 | 1 | :572 | 既定 | M | resolve | 多数 | 挙動 | 同 |
| **plan_cursor** | i2 | 2 | :574 | 既定 | M | なし | なし(走査で宣言 1 件のみ) | **死蔵** | 同 |
| talk_partner | i4 | 4 | :576 | 既定 | M | `resolve.py:1022,2404,2424-2425,2482,2502,2519` | **`memory.py:355`(想起の相手=描画)・`run.py:2525`(口コミの宛先)** | **挙動(腕: 記憶/店の記憶)**・既定の構成では読まれない | **変** |
| **invocation_distance** | u2 | 2 | :578 | 既定 | E | なし | なし(宣言 2 件=agents と `perception/state.py:108` の単体ベンチ用の条件付き宣言) | **死蔵** | 同 |
| transit_state | i1 | 1 | :581 | 既定 | M | resolve・rail | presence・arbiter(域外抑止)・rail | 挙動 | 同 |
| transit_ref | i4 | 4 | :584 | 既定 | M | resolve | `resolve.py:2099`・`rail.py:650`・`civic.py:496` | 挙動 | 同 |
| board_line | i1 | 1 | :588 | 既定 | M | resolve | `presence.py:1422,1436`・`resolve.py:1363` | 挙動 | 同 |
| board_since | i4 | 4 | :591 | 既定 | E | resolve | `resolve.py:1830,1969,1986,2008` | 挙動 | 同 |
| sleep_pending | i1 | 1 | :595 | 既定 | M | resolve | `commit.py:868`・`intent.py:243,433` | 挙動 | 同 |
| intent_action | i1 | 1 | :599 | **既定** | M | `resolve.py:883,1043` | `intent.py:178,221,260…`・`presence.py:1392`・`resolve.py:1071,1377` | 挙動 | 新(#54) |
| intent_target | i4 | 4 | :603 | 既定 | M | resolve.set_intent | `intent.py:194,261`・`memory.py:358`・`renderer.py:1830` | 挙動 | 新 |
| intent_kind | i1 | 1 | :605 | 既定 | M | 同 | `intent.py:193,262`・`renderer.py:1829` | 挙動 | 新 |
| intent_since | i4 | 4 | :607 | 既定 | E | `resolve.py:886,1046` | `intent.py:263,438`(TOO_FAR の判定 `(t − since) > max_ticks`) | 挙動 | 新 |
| poi_ref | i4 | 4 | :610 | 既定 | E | resolve | `crowd.py:231`・`classical.py:340,351`・memory | 挙動 | 同 |
| poi_since | i4 | 4 | :612 | 既定 | E | resolve | `crowd.py:231`(回転率) | 挙動 | 同 |
| queue_poi | i4 | 4 | :614 | 既定 | E | resolve | crowd・`memory.py:366,680` | 挙動 | 同 |
| queue_since | i4 | 4 | :616 | 既定 | E | resolve | `crowd.py:242`・`resolve.py:2870` | 挙動 | 同 |
| plan_activity | i1 | 1 | :620 | 腕 plan(実資産の既定) | M | `resolve.py:606,608` | なし | 読み手未検出 | 同 |
| plan_flags | i1 | 1 | :623 | 腕 plan | M | `resolve.py:617-625` | `presence.py:1560`・`resolve.py:2035,2384`(`EXIT_WALK_FLAG`) | 挙動 | 同 |
| activity_until | i4 | 4 | :628 | 腕 activity(v3 既定) | M | activity | `activity.py:350,376,390,431`・`resolve.py:1137` | 挙動 | 同 |
| activity_kind | i1 | 1 | :631 | 腕 activity | M | activity | `renderer.py:1549-1566`(p_see の乗数)・`resolve.py:1133` | 挙動 | 同 |
| fam_thing | i4×K | 4K | :636 | 腕 familiarity | M | `resolve.write_familiarity`(:910) | `poi_target.py:302-304`(習慣)・familiarity | 挙動(腕) | 新(#56) |
| fam_first | i4×K | 4K | :638 | 同 | M | 同 | `familiarity.py:187`(A の L) | 挙動(腕) | 新 |
| fam_last | i4×K | 4K | :640 | 同 | E | 同 | なし(書くだけ) | 読み手未検出 | 新 |
| fam_visits / fam_exposures | u2×K | 4K | :642/:644 | 同 | M | 同 | `familiarity.py:186`・`poi_target.py:304` | 挙動(腕) | 新 |
| mem_kind | u1×N | N | :649 | 腕 memory | M | `resolve.write_memory`(:935) | `memory.py:311,333,445,516,764` | 挙動(描画) | 新(#60) |
| mem_tick | i4×N | 4N | :651 | 同 | M | 同 | `memory.py:309,351`(A の L) | 挙動(描画) | 新 |
| mem_last | i4×N | 4N | :653 | 同 | E | 同 | `memory.py:403,485` → `renderer.py:1872-1873`(B5 の時刻 HH:MM) | 挙動(描画) | 新 |
| mem_cell / mem_partner / mem_object / mem_result | i4/i4/i4/u1 ×N | 13N | :655-661 | 同 | M | 同 | `memory.py:369-378`(想起の照合)・描画 | 挙動(描画) | 新 |
| mem_importance | u1×N | N | :663 | 同 | E | 同 | `memory.py:310,352`(score) | 挙動(描画) | 新 |
| mem_n | u2×N | 2N(宣言 9N) | :665 | 同 | M | 同 | `memory.py:309,351,534` | 挙動(描画) | 新 |
| sm_poi / sm_valence / sm_precision / sm_first / sm_n / sm_source | 各 ×M | 23M 相当 | :670-682 | 腕 store_memory | M | `resolve.write_store_memory`(:962) | `store_choice.py:141-149`(想起優先の候補)・`store_memory.py:290-370` | 挙動(腕) | 新(#62) |
| sm_last | i4×M | 4M | :678 | 同 | E | 同 | `store_memory.py:330,346`(**減衰 ga/citysim の腕だけ**)・`memory.py:486`(B5 の時刻) | 挙動(腕・描画) | 新 |
| rel_partner / rel_kind / rel_sign / rel_first / rel_n | 各 ×k | 13k | :689-699 | 腕 relations | M | `resolve.write_relations`(:986) | `relations.py:654,709,726,745,795,869,965`(知人・招待の重み・知人出現) | 挙動(腕) | 新(#65) |
| rel_last | i4×k | 4k | :697 | 同 | E | 同 | なし(書くだけ) | 読み手未検出 | 新 |
| refractory_until | i4×11 | 44 | :702 | 既定 | M | `resolve.py:815-818`(`np.maximum.at`) | `arbiter.py:393-396`・`run.py:2977` | 挙動 | 同 |
| **wake_pending_class** | i1 | 1 | :705 | 既定 | M | 初期値 −1(`state.py:724`)だけ | なし | **死蔵** | 同 |
| last_action | i1 | 1 | :708 | 既定 | M | resolve | bridge・`intent.py:394`・`memory.py:367` | 挙動 | 同 |
| last_result | i1 | 1 | :711 | 既定 | M | resolve | `activity.py:297`・`intent.py:338,393`・renderer | 挙動 | 同 |
| last_result_tick | i4 | 4 | :713 | 既定 | M | resolve | `activity.py:296`・`intent.py:337,392,416,448`・`memory.py:666`・`renderer.py:2427,2481` | 挙動 | 同 |
| fail_streak | u1 | 1 | :715 | 既定 | E | `resolve.py:1074,1431,1492,1504,3020,3065` | なし(閾値比較 0) | 読み手未検出 | 同 |

死蔵 3 列の確認(探し方): `src/shibuya`(build/ を除く)と `tools/` を列名で走査。`plan_cursor` は宣言 1 件、`invocation_distance` は宣言 2 件(agents と知覚の条件付き宣言)、`wake_pending_class` は宣言+初期値 1 件だけ。tests には `tests/agents/test_state.py:99`(`wake_pending_class == -1`)と `tests/perception/test_hashes_state.py:67-73`(`invocation_distance` の二重宣言の検査)がある。

### 1-b world(`world/state.py:121-150`)と知覚(`perception/state.py:98-108`)

| 列 | dtype | 宣言 | タグ | 読み手 | 分類 | R-55 |
|---|---|---|---|---|---|---|
| cells.density | i4 | :121 | M | change_detect・crowd(毎 tick `agents.cell` から再計算=派生) | 挙動(派生) | 同 |
| cells.density_stage | u1 | :123 | E | `salient.py:484`・`presence.py:1715`(再計算=派生) | 挙動(派生) | 同 |
| cells.noise_stage | u1 | :125 | E | `world/state.py:418`→`renderer.py:1197`・change_detect(動的上書き欄・いまは書き手 0) | 挙動 | 同 |
| cells.open_count | i4 | :128 | M | なし(`resolve.py:541,1481` が書くだけ) | 読み手未検出 | 同 |
| cells.b4_hash | u8 | :130 | M | なし(`resolve.py:783` が書く・`World.b4_hash` プロパティ `world/state.py:220-221` の呼び手 0) | 読み手未検出 | 同 |
| pois.cell / node | i4 | :134/:136 | M | 候補解決・renderer | 挙動 | 同 |
| pois.stock / price | i4 | :138/:140 | M | commit(資源裁定)・chooser(予算)・poi_target | 挙動 | 同 |
| pois.revenue | i8 | :142 | M | `run.py:3859` → **保存則の検査 `run.py:1091`** とラン要約だけ | **診断・監査**(挙動には効かないが保存則の項) | **変** |
| pois.capacity | i4 | :144 | E | `commit.py:413` | 挙動 | 同 |
| pois.open_from / open_to | i2 | :146/:148 | E | `world/state.py:393`(open_mask)・`renderer.py:1524-1525,2500` | 挙動 | 同 |
| pois.open_now | i1 | :150 | M | `world/state.py:389`・opening | 挙動 | 同 |
| 知覚 heading / task_flag | u1 | :98/:100 | M | `salient.py:213-214`(p_notice) | 挙動(checkpoint 外) | 同 |
| 知覚 last_b2_hash / last_b4_hash | u8 | :103/:105 | M | **書き手も読み手も 0**(宣言だけ) | **死蔵** | **変**(R-55 は読み手未検出) |

---

## 表 2 SoA の外の状態(tick をまたいで Python オブジェクトが持つもの)

凡例: 効く=挙動に効くか(描画=プロンプトだけ)。持ち越し=日をまたいで持ち越すべきか(日境界の再開で要るか)。外部化=`to_state` のしやすさ(配列=ndarray をそのまま / 辞書=dict・list を直列化 / 難しい=理由)。R-55=同/新。

| オブジェクト | 属性 | 場所 | 効く | 持ち越し | 外部化 | R-55 |
|---|---|---|---|---|---|---|
| ActivityLayer | `text`(list[str]・体数)・`until_kind` | `activity.py:178-179` | 効く(activity_hash に入る) | 要る(活動が日をまたぐ) | 辞書(文字列の list)+配列 | 同 |
| ActivityLayer | `text_id`・`_texts`・`_text_ids`(intern)・`_digest_cache` | `activity.py:181-184` | 派生(並べ替えは文で決まる) | 再計算可 | 不要 | 同 |
| ActivityLayer | `_bt_agent/_bt_tick/_bt_start`(次の予定) | `activity.py:189-191` | 効く | **日ごとの表**(持ち越さず作り直す) | 不要 | 新 |
| **IntentLayer** | `_payload`(dict 体 → 活動の控え) | `intent.py:139` | 効く(activity_hash に入る `intent.py:471-482`) | 要る | 辞書 | 新(#54) |
| IntentLayer | `_proposals`・`_executing`・`_kept_walk` | `intent.py:135,137,141` | tick 内で消費(`after_apply`・`:220,365-369`) | 不要(tick 境界で空) | — | 新 |
| IntentLayer | `stats`・`ticks_sum/n` | `intent.py:142-144` | 診断 | 任意 | 辞書 | 新 |
| **FamiliarityLayer** | `prev_cell`(体数・前 tick のセル) | `familiarity.py:168,252-253` | 効く(腕: 入った回の露出 → 表 → classical の習慣) | 要る(無いと tick 0 に全員「入った」扱い) | 配列 | 新(#56) |
| **MemoryLayer** | `gist`(dict (体,行) → 40 字)・`_gist_order` | `memory.py:242-243` | 描画(B5 の会話の要旨) | 要る | 辞書(文字列) | 新(#60) |
| MemoryLayer | `_session_key`(dict (体,セッション) → (相手,店))・`_gist_done`(set) | `memory.py:245-246` | 効く(要旨の書き先) | 要る(セッションが日をまたぐとき) | 辞書 | 新 |
| MemoryLayer | `_next_session`・`_next_join`(会話の `n_opened`/`join_events` への読み位置) | `memory.py:247,257,730,748` | 効く(記憶の会話の行) | 要る+**会話マネージャの番号と整合が要る**(会話を作り直すと 0 に戻る) | 整数 | 新 |
| MemoryLayer | `_target`(その tick の散らし先)・`stats`・`recall_stats` | `memory.py:248,240,252` | tick 内/診断 | 不要 | — | 新 |
| StoreMemory | `stats` だけ(表は SoA) | `store_memory.py:207` | 診断 | 任意 | 辞書 | 新(#62) |
| StoreChoice | `choice_poi`・`choice_reason`(決め手の控え)・`stats`・`by_hour` | `store_choice.py:105-110,187-198` | 診断(決め手の記録) | 任意 | 配列 | 新(#64) |
| StoreChoice | `_b_tick/_b_off`(次の予定) | `store_choice.py:97-99` | 効く | 日ごとの表 | 不要 | 新 |
| WomExtractor | `stats`・`top`・`unmatched_words` | `wom.py:222-224` | 診断 | 任意 | 辞書 | 新(#63) |
| **RelationLayer** | `_prev_cell`(知人出現の前回欄) | `relations.py:591,947-950` | 効く(腕: None の tick は候補を出さない) | 要る | 配列 | 新(#66) |
| RelationLayer | `_acq_until`(体 × k・同一相手の不応期 tick) | `relations.py:589,931,962` | 効く(腕) | 要る(**tick 値**) | 配列 | 新 |
| RelationLayer | `_co_since`(i4)・`_co_day`(i2)・`_co_active`(同席の連続) | `relations.py:580-582,883-910` | 効く(腕 copresent) | 要る(**tick 値と日番号**) | 配列 | 新 |
| RelationLayer | `_invite_salt`・`chosen_count`・`origin_of`・`_hits`・`_acq_pending`・`stats`・`wall` | `relations.py:576-594` | 設定/診断/tick 内 | 不要(salt は設定から) | — | 新 |
| **ClassicalPolicy** | `_prev`(体ごとの直前の活動) | `classical.py:305,392,414,482` | 乗数 `m_prev` が 1 でない腕だけ効く(既定は全部 1.0) | 要る(腕のとき) | 配列 | 新(#58) |
| ClassicalPolicy | `_condition`(呼の起床条件)・`_tick`・`_eating_tick/_eating_cells`・`_ipf_cache` | `classical.py:306-317,338-347,400-418` | tick 内/キャッシュ(`_ipf_cache` は 15 分帯ごとの派生) | 不要 | — | 新 |
| ClassicalPolicy | `_b_tick/_b_off`(次の予定)・`counts`・`by_hour` | `classical.py:291-293,483-484` | 日ごとの表/診断 | 表は作り直す | — | 新 |
| ClassicalChooser | `last_habit`(直前の probs の習慣候補)・`stats` | `chooser.py:180,189,227` | 診断(決め手の記録 `poi_target.py:539`) | 不要 | — | 新 |
| TargetResolver | `_cat_mask_cache`・`stats`・`entropy_sum`・`named_closed`・`move_stats` | `poi_target.py:270,373,472,536,763` | キャッシュ(資産の純関数)/診断 | 不要 | — | 新(#52) |
| **EnergyLayer** | `bmr`(体ごとの基礎代謝・`weight_kg` からの派生) | `energy.py:521`・`resolve.py:1182` | 効く(腕 `--energy-rate bmr`) | 再計算可(SoA の weight から) | 配列 | 新(#57) |
| EnergyLayer | `meal_bits`・`n_meals`・`n_snacks`・`counts`・`intake_kcal`・`stage_ticks…` | `energy.py:528-586` | 診断(センサス `:614-617`) | 日ごとに 0 から(翌日持ち越しなし=宣言) | 配列 | 新 |
| OutOfAreaMeals | `tick/agent/slot/from_row/_start`(範囲外の食事の予定) | `energy.py:482-488` | 効く | **日ごとの表**(`tick < ticks` だけ残す) | 不要 | 新 |
| **GroupNormMeter** | `_prev_xy`(瞬間の群れ歩きの前回位置)・`_pair_keys/_pair_len`・計数 | `norm_meter.py:111-131,229,345` | 診断(読むだけ) | 任意(計器の連続性だけ) | 配列 | 新(#74/#75) |
| **PlanExecutor(退出の歩行)** | `_walk_since`(tick)・`_walk_line`・`_plan_rider`・`_rewalked`・`_rewalk_ids/_line/_deadline` | `presence.py:715-730` | 効く(腕 walk_to_platform) | 要る(**tick 値**) | 配列 | 新(#68/#69) |
| PlanExecutor | `_defer_ids/_defer_deadline/_defer_line/_defer_walk`・`_extra`・`_skip_depart_at`・`_pulled_in_today` | `presence.py:707-711,752-756` | 効く | 要る(`_pulled_in_today` は日で 0 に) | 配列+辞書 | 同(+`_defer_walk`) |
| PlanExecutor | `ev_tick/ev_agent/…/_ev_start`・`arrival_*`・`absent`・`blocks` | `presence.py:661-666,990-1108` | 効く | **日ごとの表** | 不要 | 同 |
| ConversationManager | `sessions`・`_of_agent`・`_refusal_until`・`_next_id`・`pending_invites`・`_pair_invite_until`・`_speaker_invite_until`・`join_events`・`origin_counts` | `conversation.py:280-313` | 効く | 要る(セッション・拒否記憶は **tick 値**) | 辞書(dataclass の直列化の書き手が要る) | 同(+`join_events`・`origin_*`) |
| Arbiter | `_pending`(WakeCandidates)・`_pool`(float)・`queue`・`_last_tick` | `arbiter.py:535-543` | 効く | 要る(`since_tick` は **tick 値**) | 配列+float+辞書 | 同 |
| run_day の局所 | `pending`(適用待ち・`t_apply`)・`fleet_deferred`・`fleet_waiting`・`replay_inbox` | `run.py:2582,2295-2304` | 効く | 要る(ラン終端で最終 tick 以降の `pending` を捨てる) | 辞書(tuple の list・`ParseResult` を含む=**難しい**: 応答の解析結果と Target を持つ) | 同 |
| ChangeDetector | `_prev_raw`(セル × 4) | `change_detect.py:274,299` | 効く(**None のとき全セル変化扱い**) | 要る(日の頭に全セル起床の嵐) | 配列 | 同 |
| SalientProcess | `rng`(状態つき)・`event_seen_tick`(体数・**tick 値**)・`budget`・`pstate`(知覚 SoA) | `salient.py:153-176` | 効く | 要る | Generator の dict+配列 | 同 |
| PublicServiceDispatchProcess | `rng`・`pending`(到着予定 tick) | `civic.py:116-117` | 効く | 要る | Generator の dict+list | 同 |
| HotelProcess | `rooms_occupied`・`bed_cell` | `civic.py:271,278` | 効く(寝床の空き) | 要る | 配列 | 同 |
| LargeEventProcess | `_inside` | `civic.py:449` | 効く | 要る | 配列 | 同 |
| RailProcess | `occupancy`・`peak_ratio`・`_return_queue`(dict → list[ndarray])・`_inbound`・`_inbound_ready` | `rail.py:283-298` | 効く(満員) | 要る(便は日ごとの表=日境界では空のはず・未検証) | 辞書 | 同 |
| CrowdProcess | `queue_action`(体数) | `crowd.py:184` | 効く | 要る | 配列 | 同 |
| ShelfRestockProcess | `backroom`・`_acted_today` | `goods_flow.py:171,182` | **効く**(補充量の上限 `qty = min(want, backroom)`・R-55 は未確認) | 要る(`_acted_today` は分 0 で 0 に) | 配列 | 同(判定を追加) |
| WasteCollection / StreetCleaning | `_cursor`・`waste_g_collected`・`litter_g`・`swept_g` | `goods_flow.py:426-432,565-568` | 読み手はこの過程と要約だけ(走査で他 0) | 監査 | 配列 | 同 |
| LastMile / RoadWorks | `delivered`・`_cum`・`blocked_cells`・`occupied_edges` | `logistics.py:121-124,285-286` | **読み手未検出**(resolve・geometry・world・renderer を走査して 0) | 監査 | 配列 | 同(判定を追加) |
| EnvironmentProcess | `replay_date`・`stratum`・`_row`・`_shade` | `environment.py:144-157` | 効く(描画の日付・日陰) | 日ごとに選び直す(下の表 4 の穴) | 値 | 同 |
| MoneyLedger / GoodsLedger | `_lines`・`_flow_daily`・`_snap`・`_day`・生ログリング/`_shelf`・`_bin`・`_sold_today`・`_day`・納品リング | `economy/ledger.py:222-269`・`economy/goods.py:330-406` | 効く(残高・棚) | 要る | 配列+辞書 | 同 |
| UndefinedActionRegistry | `log`・`counts`・`precedents` | `llm/undefined.py:697-705` | run_day は裁定器なし=効かない | 任意 | 辞書 | 同 |
| PerceptionRenderer | `_b1/_b2/_b3/_b4_cache`・`_rank_cell_cache`・`_acq_cache`・`_tickc` | `renderer.py:1096,1124-1133` | キャッシュ(`_acq_cache` は関係辺 on のとき使わない `:2062-2066`) | 不要 | — | 同 |
| PerceptionRenderer | 口 `acquaintance_fn`・`memory_recall`・`session_partner_fn`・`named_closed_lookup`・`signage_exposures` | `renderer.py:1120-1122`・`run.py:2406,2443,2476,2505,2511` | 関数(状態でない)・`signage_exposures` は tick 内 | 不要 | — | 新 |
| LLMBridge / TapeWriter / FleetBridge | 計数・`_rows`・`_blocks`・in-flight | `llm_bridge.py:537-554`・`tape.py:242-278`・`llm/fleet.py` | 計数/ファイル/外部 | テープは日ごとのファイル | — | 同 |

---

## 表 3 乱数と決定論ハッシュの全数

探し方: `stream(`・`philox(`・`derive_key(`・`default_rng`・`random.`・`self.rng`・`*_key_array(`・`xxh64(`・`_mix64(`・`splitmix` を `src/shibuya`(build/ を除く)で走査。`np.random.default_rng`・組み込み `hash()`・`import random` は 0 件(R-55 と同じ)。Generator を属性に持ち続けるのは下の 2 本だけ(他の `stream(` はすべて局所 `g =` かその場で使い捨て)。

| # | 名前(domain / tag) | 鍵の引数 | 日番号 | 状態 | 場所 | R-55 |
|---|---|---|---|---|---|---|
| 1 | `world.salient` | seed, day_index | あり(先頭) | **持つ**(毎 tick poisson・choice) | `salient.py:160,308,314` | 同 |
| 2 | `world.public_service_dispatch` | seed, day_index | あり | **持つ**(出動ごと lognormal) | `civic.py:116,132` | 同 |
| 3 | `llm.mock` | seed, tick, agent, 起床級 | **なし** | なし | `llm/mock.py:170,185` | 同 |
| 4 | `llm.mock`+移動の対象 | seed, tick, agent, 起床級 | **なし** | なし | `llm/mock.py:215` | 新(#53) |
| 5 | `llm.mock`+店の対象 | seed, tick, agent, 起床級 | **なし** | なし | `llm/mock.py:231` | 新(#54) |
| 6 | `policy.classical` | seed, tick, agent, 条件 | **なし** | なし | `classical.py:464` | 新(#58) |
| 7 | `engine.chooser`(`draw_index`) | seed, tick, agent | **なし** | なし | `chooser.py:269`(呼び手 `poi_target.py:532,661`・`store_choice.py:177`) | 新(#52・#64) |
| 8 | `conversation.invite` | seed, tick, inviter | **なし** | なし | `conversation.py:384` | 同 |
| 9 | `perception.attention.p_see` | seed, tick, agent, poi | **なし** | なし | `perception/attention.py:225` ← `renderer.py:1637-1641`・`familiarity.py:311,319` | 同(+親しみの表) |
| 10 | `perception.p_notice` | seed, その tick の事象番号, tick | **なし**(事象そのものは #1 で日ごとに違う) | なし | `p_notice.py:478`・事象番号は `enumerate(raw)` `salient.py:221` | 同 |
| 11 | `body.weight` / `body.eer` | seed, 体 | なし(**個体の素性**=日で変えない) | なし(起動時) | `energy.py:272-273` | 新(#57) |
| 12 | `geometry.desired_speed` | derive_key(seed)+splitmix64(体) | なし(素性) | なし | `geometry.py:154-158` | 同 |
| 13 | `engine.processes.rail`(域外居住の選び) | seed, 0 | **なし** | なし(起動時・計画実行層の無いランだけ) | `rail.py:367` | 同 |
| 14 | `engine.processes.environment` | seed, 0(種別)/ seed, blake3(層名)(再生日) | **なし**(曜日の種別は層名に入る) | なし(起動時) | `environment.py:102,194` | 同 |
| 15 | `world.large_event`・`world.delivery_inbound`・`world.road_works`・`world.delivery_last_mile`(予約) | seed, day_index | あり | なし(起動時) | `civic.py:441`・`goods_flow.py:336`・`logistics.py:291,125` | 同 |
| 16 | `agent.schedule`(mock 日課) | seed, 体 × ブロック | **なし**(平日/休日の 2 形だけ) | なし(起動時) | `agents/schedule.py:75,88` | 同 |
| 17 | `w16.sample.*`・`wallet.initial`・`world.synthetic` | seed(, 層) | なし(起動時) | なし | `population.py:315,334`・`cli.py:235`・`world/assets.py:691` | 同 |
| H1 | run_salt `pk`(資源の優先度) | salt, tick, 資源, 体 | **なし** | なし | `commit.py:408` | 同 |
| H2 | run_salt `ak`(適用順) | salt, t_apply, 体 | **なし** | なし | `run.py:2674` | 同 |
| H3 | run_salt `wk`(起床のタイブレーク) | salt, tick, 級, 体 | **なし** | なし | `arbiter.py:438`・`commit.py:807` | 同 |
| H4 | run_salt `wd`(あたりの行き先) | salt, tick, 体 | **なし** | なし | `activity.py:412` | 同 |
| H5 | run_salt `ri`(招待の相手) | salt, tick, 体 | **なし** | なし | `relations.py:815` | 新(#66) |
| H6 | run_salt `ri`+`|rest`(残りの人の順) | salt+"|rest", tick, 体 | **なし** | なし | `relations.py:852` | 新(#66) |
| H7 | `near_tie_keys`(B5 近接行の同点) | salt64, 観る体, 相手 | なし(**tick も混ぜない=宣言** Q131) | なし | `renderer.py:919-938,2026,2048` | 新(#70) |
| H8 | `_pair_mix`(初期辺の同点・在職期間) | 体の元 id の組(seed なし) | なし(起動時・資産の関数) | なし | `relations.py:319-344,405,458` | 新(#65) |
| H9 | 出勤率の欠席 `_mix64(agent_id)` | 体だけ(**seed も日もなし**) | **なし** | なし | `presence.py:792` | 同 |
| H10 | 艦隊のデコード seed `xxh64(call_id, run_seed)`・振り分け `xxh64(call_id) % n` | call_id = `"{tick}:{a}:{cls}"` | **なし** | なし | `llm/fleet.py:272,279`・`run.py:3120`・`llm_bridge.py:608` | 同 |
| H11 | B4 変化検出・prefix 鍵(xxh64) | 描画バイト | —(内容の指紋) | なし | `renderer.py:1212,1221`・`perception/hashes.py` | 同 |

**状態を持つ乱数はいまも 2 本だけ**(#49〜#75 で増えていない)。呼ごとの乱数は 4 → 8、salt のハッシュは 4 → 6(+H7)に増え、**増えたものはどれも日番号を持たない**。

[実行確認] Philox の鍵の余りは 0 で埋まる(`core/rng.py:58-65`)ので、`stream(1,"llm.mock",100,5,3)` と `stream(1,"llm.mock",100,5,3,0)` は同じ列を返した。`stream(1,"world.salient",0)` と `(0,0)` も同じ。**blake3 の `_pack` は末尾に 0 を足すとバイト列が変わる**(`apply_key(s,10,3)` ≠ 末尾に i64 の 0 を足したもの)。現行の呼ごとの乱数はどれも 3 語以下(4 語の上限に 1 語の余りがある)。

---

## 表 4 鍵に日番号が無いもの・tick を値に持つ状態 — 複数日で何が起きるか

前提(事実): `run_day` のループは `for tick in range(ticks)`(`run.py:2613`)=tick は日の中の番号 0〜1439。日をまたぐ経路は無い(§6)。下の「起きること」は、**いまの鍵のまま日境界で状態を持ち越して tick を 0 から回した場合**の読み(推測を含む=実行はしていない)。

### 4-a 鍵

| 鍵 | 場所 | 複数日で起きること |
|---|---|---|
| 呼ごとの乱数 #3〜#10 | 表 3 | **同じ (tick, 体) に毎日同じ乱数列**: mock の応答・古典の方策・選び手・招待・p_see・p_notice が日ごとに同じ値を引く=日の間の独立性がない(同じ状態なら同じ選択を毎日繰り返す) |
| salt のハッシュ H1〜H6 | 表 3 | 同じ (tick, 体) で毎日同じ優先度・適用順・タイブレーク・あたりの行き先・招待の相手の順 |
| call_id `"{tick}:{a}:{cls}"` | `run.py:3120`・`llm_bridge.py:608` | 艦隊のデコード seed が毎日同じ(温度 > 0 のとき日ごとの独立性がない)・レプリカの振り分けも毎日同じ |
| テープの鍵 (agent_id, tick, wake_class, prompt_hash) | `tape.py:222-224,494-524` | テープを日ごとに別ファイルにすれば衝突しない。**1 本のテープに複数日を入れると衝突しうる**: プロンプトの日付は再生日(天気)から作られ、再生日が毎日同じ(下)なので prompt_hash も同じになりうる。**版は既に 3**(`tape.py:91` `shibuya.tape/3`・記憶の `recalled_rows`)=鍵に日を足すなら**版 4** |
| prompt_hash | `llm_bridge.py:30-39,625` | プロンプトの時刻は `clock_fn(t) = start + t 分`(`run.py:2223-2229`)。`start` は天気の再生日があればそれ(`runner.replay_date`)=**日番号が変わっても同じ曜日の種別なら同じ日付** |
| 天気の種別と再生日 | `environment.py:102,194-197` | 鍵が seed と層名(平日/土休 × 種別)だけ=**平日は毎日同じ天気・同じ実日**(D-102 草案 §4-4 の「天気の実日も day で進める」の対象) |
| 出勤率の欠席 H9 | `presence.py:792` | **毎日同じ体が「終日域外」**(seed にも日にも依らない) |
| mock 日課 #16 | `agents/schedule.py:75,88` | 平日は毎日同じ日課(W17 の無いランだけ) |
| run_salt の用途鍵(全体) | `run.py:445-448` | salt 自体は seed だけ=日で変わらない(上の各行の原因) |

### 4-b tick を値に持つ状態(Δt = tick − 値 を計算するもの)

| 状態 | 場所 | 計算 | 日をまたぐと |
|---|---|---|---|
| `refractory_until`(SoA) | 書き `resolve.py:815-818`(`np.maximum.at`)・読み `arbiter.py:393-396` | 「次に起床してよい tick」> tick なら抑止 | **前日 23:50 に張った値(例 1,450)が翌日 tick 0〜1,449 を抑止**。`np.maximum.at` なので小さい値で上書きもされない=**丸 1 日その条件で起きない** |
| `activity_until`(SoA) | `activity.py:229-244,350,376`・`resolve.py:1137` | `== tick` で満了・`> tick` で持続 | 「まで」の解決は日付を越える値を作る(`activity.py:241-244` の `% 1440`+`t + delta`)。翌日は `== tick` に当たらない=**満了しない**・`> tick` が丸 1 日真 |
| `last_result_tick`(SoA) | `activity.py:296`・`intent.py:337,392,416,448`・`memory.py:666`・`renderer.py:2427,2481` | `== tick` を「いまの結果」とみなす | 前日の同じ tick の結果を**今日の結果と取り違える**(失敗の即時満了・意図の実行結果・記憶の書き手・B6 の直前の結果) |
| `intent_since`(SoA) | `intent.py:438` | `(t − since) > max_ticks` で TOO_FAR | 負の Δt=**意図が満了しない** |
| `poi_since`・`queue_since`・`board_since`(SoA) | `crowd.py:231,242`・`resolve.py:2008-2009` | `since + 上限 <= t` | 回転・離脱・待ちの打ち切りが翌日まで起きない |
| `mem_tick`・`mem_last`(SoA) | `memory.py:224`(`np.maximum(0, …)`)・描画 `renderer.py:1872-1873` | A の L・B5 の時刻 | L が 0 に切られ**記憶が減衰しない(最新扱い)**・描画の HH:MM は時刻だけ(日付なし)=「昨日」が区別できない |
| `fam_first`・`fam_last`(SoA) | `familiarity.py:187`(`activation_approx` で L ≥ 0 に切る `:133`) | A の L | 同上(**親しみが減衰しない**) |
| `sm_first`・`sm_last`(SoA) | `store_memory.py:330,335,346` | A の L・ga の時間・citysim の日数 | 同上(`np.maximum(0, …)`) |
| `rel_first`・`rel_last`(SoA) | `relations.py:188-190,998` | A の L(初期辺は負の過去 tick) | 同上。初期辺の first は「−T 週」の負の値で、**絶対時刻の座標で書かれている**(日の中の番号ではない)=ラン中の辺と座標が混ざる |
| `event_seen_tick`(salient) | `salient.py:167`・`resolve.py:2543-2544` | `seen ≥ 0 ∧ tick − seen ≤ 窓` | 負の Δt は窓の内側=**前日に見た事象で今日の通報が通る**(誤って成功) |
| `_acq_until`(関係辺) | `relations.py:962` | `≤ tick` なら再度起こす | 前日遅くに張ると翌日の同時刻まで同じ相手で起きない |
| `_co_since`・`_co_day`(同席) | `relations.py:909-919` | `day = tick × 分 // 1440` | **tick が毎日 0 から始まると day は常に 0**=`_co_day != day` が偽のまま=**2 日目以降は同席の辺が 1 本も書かれない** |
| 会話 `_refusal_until`・`_pair_invite_until`・`_speaker_invite_until`・セッションの開始 tick | `conversation.py:282-290` | `until > tick` | 不応期の食い違い(上と同じ形) |
| アービタ `_pending` の `since_tick`・`pending` の `t_apply`・`replay_inbox` の鍵 | `arbiter.py:542`・`run.py:2582,2304` | 昇格(待ち時間)・適用の時刻 | 前日の値との差が負 |
| 退出の歩行 `_walk_since`・`_rewalk_deadline`・`_defer_deadline` | `presence.py:707-730,1422` | `(tick − since) ≥ walk_max` | 満了しない |
| 出動 `pending` の到着 tick | `civic.py:117,155-157` | `row[0] <= tick` | 前日の予定が翌日の tick 0 に全部着く |

**数え**: 日番号の無い鍵 = 呼ごとの乱数 8(#3〜#10)+salt のハッシュ 6(H1〜H6)+call_id・テープの鍵・艦隊の seed・天気・出勤率 = **19**(near_tie H7 と素性の #11・#12 は日で変えない宣言として除いた)。tick を値に持つ状態 = SoA 15 列(`refractory_until`・`activity_until`・`last_result_tick`・`intent_since`・`poi_since`・`queue_since`・`board_since`・`mem_tick`・`mem_last`・`fam_first`・`fam_last`・`sm_first`・`sm_last`・`rel_first`・`rel_last`)+SoA の外 7 行(上の表の `event_seen_tick` 以下)。

**案(実装役の自前の構成=未リサーチ)**: Q7 の「(day, tick) を鍵に」を **絶対 tick `T = day × ticks_per_day + tick`** で表す形も取りうる。(i) day=0 では T = tick なので Philox のカウンタ・blake3 の `_pack`・call_id の文字列・テープの tick 欄が**すべてバイト一致**(条件分岐なしで既定 checkpoint を保てる)(ii) SoA と SoA の外の tick 値(表 4-b)を**そのまま絶対時刻として持ち越せる**(Δt の穴がまとめて消える・`_co_day` の穴も消える)。代わりに(iii)日ごとの表(表 5 の b_tick・予定・時刻表・範囲外の食事・次の予定の CSR)を `T − day × ticks_per_day` で引くか、表を day ぶんずらす必要がある。「末尾に day を足す」形では Philox は不変だが blake3 と call_id は条件付き(day ≠ 0 のときだけ足す)にしないと既定が動き、表 4-b は別に直す必要がある。

---

## 表 5 1 tick=日の中の番号(0〜1439)を前提にした計算

| 箇所 | 場所 | 前提 | 日をまたぐと/複数日で |
|---|---|---|---|
| 計画境界の表 `b_agent/b_cond/b_tick/b_cell`・`b_start = searchsorted(b_tick, arange(ticks+1))` | `run.py:2332,2339,2351`・`agents/weekly.py:304-305`(「tick=活動の開始分 0-1439」) | tick=分・日の中 | 日ごとに作り直す表。絶対 tick にするなら引き方を変える。`tick_seconds` を見ていない(tick=分)=§1-10 の 10〜15 秒 tick の腕では合わない |
| **W17 v2 の曜日** | [実行確認] `load_weekly('data/world/v2')` の曜日ごとの行数 = 0: 3,461,954・1〜6: **0** | W17 v2 は 1 日ぶんの資産 | **`day_index` 1〜6 で回すと計画が空**(`_day_bounds` は `day % 7` `agents/weekly.py:271-276`)=日番号と「どの曜日の予定を使うか」を分ける必要 |
| 日の頭の初期化 | `R.initialize`(`run.py:2127`)・`initialize_energy`(`:2148`・`since_meal` を前夜の夕食から作り直す `energy.py:378`)・`set_initial_activity`(`:2337`・W17 の 0:00 の活動で上書き)・`presence.initialize()`(`:2202`・在圏でない体を域外へ)・財布(`cli.py:235`) | 1 ラン=1 日 | 持ち越した位置・活動・空腹・所持金を**上書きする**=日境界の再開では通らない形に分ける必要 |
| 時刻 → 描画の日時 `clock_fn` | `run.py:2223-2229`(`start + timedelta(minutes=int(t))`) | tick=分 | 絶対 tick を渡すと日付が二重に進む。`tick_seconds` を見ていない |
| 営業時間 `open_mask` | `world/state.py:392`(`t = tick % 1440`)・`opening.py:130-136`(曜日 × 1440 分の表) | tick=分 | `% 1440` なので絶対 tick でも回る。`tick_seconds` は見ていない |
| 範囲外の食事の予定 | `energy.py:421-501`(`tick = minute × 60 // tick_seconds`・`tick < ticks` だけ残す) | 日の中 | 日ごとに作り直す表。**日付を越える食事行は落ちる** |
| 食事の窓・語の段の時間帯 | `energy.py:130,202,550,586`・`resolve.py:1186`(`% 1440`) | 分 % 1440 | 絶対 tick でも回る |
| 次の予定(活動層・古典・想起優先) | `activity.py:185-191`・`classical.py:288-293`・`store_choice.py:97-99` | その日の境界 | 23 時台の「次の予定」は翌日の境界が表に無い=「予定なし」扱い(推定) |
| 活動の「まで」 | `activity.py:241-244` | `% 1440` の時計・`t + delta` | 日付を越える値を作る(表 4-b) |
| 同席の「1 日 1 本」 | `relations.py:913` | `tick × 分 // 1440` | tick が毎日 0 からなら常に day 0(表 4-b) |
| 棚の補充の「今日やった」 | `goods_flow.py:122-123,219-221`(分 0 で 0 に) | 分 % 1440 | 回る |
| 体の時間経過 | `resolve.py:1115-1118`(`tick % 30`・`tick % REST`) | 1440 が 30 の倍数 | 回る |
| 時別の計数 | `run.py:3019,3140`(`(tick // 60) % 24`)・`run.py:2632`・`presence.py:1695,1706`・`norm_meter.py:153`・`store_choice.py:189` | tick=分(一部) | 回る(集計は日ごとに分ける必要) |
| 曜日 | `classical.py:168-170`(`day_kind_of`)・`environment.py:163`・`rail.py:312`・`agents/schedule.py:134-136`・`relations.py:285,307` | `day_index % 7` | 1 ランに 1 曜日を固定(`ActivityPrior` は起動時に曜日を読む `run.py:2072`) |
| 呼数の予算(L4 按分) | `arbiter.py:126,141-150` | 1,440 tick/日 | 監査線の単位 |
| 鉄道の時刻表・入域の予定 | `rail.py:312-352,375,414` | 日の表 | 日ごとに作り直す。**日付を越える便(終電後の帰り)**の扱いは未確認 |

関連の既存記録: 同じフォルダの `tick-constants-inventory.md`(tick 単位の定数の棚卸し・別のサブ)と重なる箇所がある=本表は「日をまたぐ」観点だけに絞った。

---

## 表 6 checkpoint のハッシュの現状

| 欄 | 混ぜるもの | 混ぜないもの | 場所 | R-55 からの変化 |
|---|---|---|---|---|
| `agents_hash` | `Registry.state_hash`=見出し(版・kind・個体数)+**宣言順の全列**(名前・dtype・形・生バイト)。**腕の列は、その腕のランでは宣言されるので入る**(親しみ・記憶・店の記憶・関係辺・エネルギー・活動・計画・edge・注意) | 知覚 SoA(`PerceptionState`)・SoA の外の全部(表 2) | `run.py:3479`・`agents/state.py:812-814`・`core/soa.py:382-406` | 列が 36 → 40(既定)・全腕 79。`exclude=` の引数が増えた(監査用・既定は空=不変 `core/soa.py:388-391`) |
| `world_hash` | cells 5 列+pois 9 列 | 世界の遅延キャッシュ(`world/state.py:166-179`)・過程の状態・台帳 | `world/state.py:456-460` | 同 |
| `population_hash` | W16 母集団の同定(ラン中不変) | — | `run.py:1412,3480` | 同 |
| `schedule_hash` | W17 の同定(ラン中不変) | — | `run.py:2352,3481` | 同 |
| `activity_hash` | 活動層の文(体順の sha256 の連結)+`until_kind`。**意図の層があれば `blake3(活動 ‖ 0x1f ‖ 意図の控え _payload)`** | intern 表 | `run.py:3482-3490`・`activity.py:481-493`・`intent.py:471-482` | **意図の控えが混ざるようになった**(#54) |
| `combined`(= `final_hash`) | 上の 4〜5 本の blake3 | — | `run.py:467-472,878-879` | 同 |

混ざらないもの(事実・探し方=`run.py` の `Checkpoint(` の組み立てと `state_hash(` の呼び手を走査): 金と物の台帳(`MoneyLedger.state_hash` は run から呼ばれない)・会話・アービタ・変化検出の前回欄・保留中の応答・過程の Python 状態・**#49〜#75 で増えた SoA の外の状態の全部**(記憶の要旨・関係辺の不応期/前回欄・親しみの前回欄・古典の `_prev`・退出の歩行・EnergyLayer の `bmr`)。

**behavior-hash の分類で注意が要る事実**(問い 1 の材料):
- 読み手の有無が**構成で変わる**列がある: `age`/`sex`(energy か classical のときだけ)・`talk_partner`(記憶/店の記憶の腕だけ)・`weight_kg`(energy・初期化時だけ)・`sm_last`(減衰 ga/citysim の腕と描画)・`mem_last`(描画だけ)。
- 挙動に効かないが**保存則・日次センサスの項**になる列がある: `revenue`(保存則 `run.py:1091`)・`energy_balance`(日次センサス)。behavior-hash から外しても、**再開では復元が要る**(除外=保存不要ではない)。

---

## 表 7 追加 C の試験の形(案・実装役の自前の構成=未リサーチ)

目的: behavior-hash から外した列(診断・監査・読み手未検出)を**ランの途中で乱数で揺らしても**、final(behavior-hash)・呼数・行動の列・プロンプトが変わらないこと=分類の誤りを捕まえる。

| 項目 | 案 | 理由 |
|---|---|---|
| 揺らす場所 | 2 点: ① 各 tick の最初(`R.advance_body` を包む=`run.py:2614` の直前)② Phase C の直後(`R.apply` を包む=`run.py:3191` の後)。書き込みは `agents.writable()` の中で | ① は tick 内のすべての読み手の前・② は会話・活動層・記憶の書き手・計器・checkpoint の前。包む口の前例=`tools/c7/attr_arms.py` の `AgentCellRecorder`(`resolve.apply` を包む) |
| 揺らす値 | 別の流れ `stream(試験の seed, "test.perturb", tick, 列の番号)` で dtype の全域から一様+端の値(−1・0・最大)を混ぜる。多次元の列(×K 等)は全要素 | 端の値は「−1=なし」の判定を持つ読み手を捕まえる |
| 揺らす列 | 分類表(状態台帳の `behavior=False` の行)から**機械的に**取る=手で列挙しない。構成ごとに宣言されている列だけ。死蔵 3 列は Q9 で消えるので対象外。`revenue`・`energy_balance` は揺らすと保存則/センサスが壊れるので「監査」として**別扱い**(揺らさない or 保存則の比較を外す)。world の `open_count`・`b4_hash` も含める。知覚 SoA の未使用 2 列も対象 | 分類と試験を 1 本の表から作る=表の誤りがそのまま試験で出る |
| 比べるもの | (a) 各 checkpoint の behavior-hash (b) 呼数・起床条件別の呼数 (c) 行動コード別の適用件数 `per_action_total` (d) **各呼の prompt_hash の列**(bridge の呼を記録する口か、テープの `calls.parquet` の列) (e) `conserved`(監査列を揺らさない構成で) | mock はプロンプトを読まないので (d) が無いと描画だけの読み手(`mem_last`・`holdings`)を見逃す |
| 陽性対照 | 同じ仕組みで**挙動の列を 1 本**(例 `hunger` か `mem_last`)揺らすと (a) か (d) が変わることを確かめる | 試験に検出力があることの証明(揺らしが効いていない配線の誤りを捕まえる) |
| 構成 | 3 本: (1) v3 既定(CLI 既定=energy・activity・plan)(2) **全部 on の統合腕**(記憶・店の記憶・関係辺(同席・3 人会話)・親しみ・classical・edge 幾何・walk_to_platform・減衰 citysim)=§7 の統合腕と同じ構成 (3) ライブラリ既定(v1・空腹 v1=`age`/`sex` が読まれない構成) | 構成で分類が変わる列(表 6)をそれぞれの構成で試す |
| 規模 | 2 段: (i) 常に回る=合成世界 200 体 × 240 tick(CI 用・数秒) (ii) 実資産があるとき=1,000 体 × 1,440 tick(食事・就寝・鉄道・退出を通る・`@real_data` で skip 可)。揺らしの seed 2 本 | 1 日を通さないと夜だけ・食事時だけ読む読み手を通らない。5,000 体は既存の golden と重なり重い |
| 静的検査との併用 | Q4 の AST 検査に「除外列の名前を**読む**式(代入の左辺以外の Subscript/Attribute の Load)が src に無い」を足す | 動的試験は通った経路しか見ない=静的な全数と組にする |
| 既存の型 | `tests/engine/test_familiarity.py:224-236` などの「`AgentState.state_hash` を `exclude=` で差し替えて on/off を比べる」形(9 か所・表 8)が、列を**足しても**挙動が変わらないことの試験。追加 C は「**値を変えても**」なので別物 | — |

---

## 表 8 版上げ 1 回に束ねたときに動くもの(見積り)

見積りの根拠は下の ファイル:行。「変わる」はコードの形から確実なもの、「見込み」は実行していない推定。

| 変更 | 既定 checkpoint(15 腕) | golden(tests) | テープ | 凍結 ablation 表の SHA | その他のテスト・道具 |
|---|---|---|---|---|---|
| **Q9 死蔵 3 列の削除** | **15 腕とも final が変わる**(3 列は全構成で宣言=`agents_hash` の入力が変わる)。呼数・行動は変わらない(読み手 0) | `W17_GOLDEN` の final 8 値(`tests/engine/test_presence_executor.py:87-97`)・`test_intent_chooser.py:298,302`(legacy 2 値)・`CLASSICAL_1500_GOLDEN` 3 値(`tests/perception/test_near_tiebreak.py:154-156`)=**13 値の張り替え**。呼数の値は不変 | 不変 | 不変(腕定義を触らない) | `tests/agents/test_state.py:99`・`tests/perception/test_hashes_state.py:67-73` の書き換え。予算表の B/体(137 → 132)。知覚の `last_b2/b4_hash` も消すなら `tests/engine/processes/test_salient.py:149`・`tests/perception/test_hashes_state.py:59`(18 B)も |
| **Q1 (i) behavior-hash を既定に** | 15 腕とも final が変わる(定義が変わる)。full-hash は Q9 の分だけ変わる | 同じ 13 値(Q9 と同じ回なら 1 回の張り替え) | 不変 | 不変 | **`state_hash` を `exclude=` で差し替える on/off 試験 9 か所**が片側だけ差し替わって食い違う見込み: `test_familiarity.py:231`・`test_intent_chooser.py:291`・`test_memory_recall.py:297`・`test_memory_record.py:223`・`test_relations.py:332`・`test_store_memory.py:220,227`・`test_wom.py:229,248`。CLI の checkpoints JSON(`cli.py:470-482` `shibuya.cli/checkpoints/1`)に欄が増える=版 2。道具 `tools/c6/run_hash.py:73-74`・`tools/c7/occupancy_series.py:235-236`・`tools/c7/seed_exchangeability.py:36`(`HASH_KEYS`)・`tests/c7/test_seed_exchangeability.py:18` |
| **Q8 状態を持つ乱数 2 本をカウンタ型に** | 顕著行為の発生列が変わる=**過程が on の構成(15 腕すべて=`run.py:1550` `processes=True`)で final が変わる**。既定の率(3/万/日)・seed 1 では現行 0 件(IMPLEMENTED #60)=新しい鍵で事象が出れば**呼数と行動も変わる見込み**(要実測) | 同じ 13 値+**呼数の値も変わりうる**(`*_llm_calls`) | 不変(鍵の形は変わらない) | 不変 | `tests/engine/processes/test_civic.py:28-35`(400 件の出動が同じ (tick, セル) を繰り返す=**鍵を (day, tick, セル) にすると同じ遅れを 25 回引く**=事象 ID が要る)・`test_salient.py:125-141`(件数の下限・率 100,000 の腕) |
| **Q7 day=0 で不変にできるか** | Philox の用途(#3〜#10)は**末尾に day を足しても day=0 で不変**([実行確認])。blake3 の H1〜H6 は末尾に足すと変わる=条件付き(day ≠ 0 のときだけ)か絶対 tick(表 4 の案)なら不変。call_id は mock では使われない(艦隊だけ) | 不変にできる(上の形なら) | **版 3 → 4**(`tape.py:91`)。既存テープ(実 LLM 17 本)は day=0 として読む口が要る。版を見る試験 `tests/engine/test_memory_recall.py`・`tests/engine/test_tape_deferred.py` | 不変 | 天気の再生日を day で進めるなら day=0 の選びを今と同じに保つ必要(`environment.py:194-197`) |
| **(参考)旧挙動を腕で再現する口を残す場合** | — | 旧値を `*_v1hash` 等として残すなら golden は増える | — | 旧挙動を腕定義に pin(例 `hash_scheme`・`rng_scheme`)すると**腕行の SHA256 が動く**=`tests/c8/test_ablations_ab7.py:32-42` の 9 本+`tests/c8/test_ablations_ab8.py:43`(Q29 と同じ形の張り替え) | — |

動かないもの(根拠): テンプレの SHA(`tests/engine/test_two_layer_activity.py:207` 40af870e)と参照場面の prompt_hash(`tests/perception/test_ablation6_signage.py:30-32`・`test_signage_p_see_gate.py:45-47`)は描画の関数で、checkpoint の定義にも day=0 の鍵にも依らない。記録済みの checkpoint を読む試験(`tests/c7/test_accept_table.py:52` 043a630f)はファイルを読むだけ。

---

## §6 再開の口の現状(R-55 §6 の再確認)

- `parent_run` は `manifest/schema.py:395-397` の欄だけ(走査で他の参照 0)。`save_registry`/`load_registry` の呼び手は tests だけ(`tools/vocab/adjudicate.py:293` の `load_registry` は別の関数)。`resume`・`start_tick`・`to_state`・`from_state` の走査で engine の口は 0 件(`engine/scheduler.py:183` の `start_tick` は未使用の Scheduler・`p_notice.py:239` は別物)。
- `run_day` は 1 日を 0 から作る(`run.py:1526`・`:2104-2150` で SoA を作り直し・`:2613` `for tick in range(ticks)`)。

## 見つからなかったもの(探した場所)

- #49〜#75 で増えた**状態を持つ Generator**(`stream(` の結果を属性に代入する箇所を `src/shibuya` で走査=salient と dispatch の 2 か所だけ)。
- `band`・`plan_activity`・`fail_streak`・`fam_last`・`rel_last`・`open_count`・`b4_hash` を読んで分岐する箇所(列名の属性・文字列の両方で走査・書き込み行を除く)。
- `blocked_cells`・`occupied_edges`・`litter_g` を過程の外で読む箇所(`engine/resolve.py`・`engine/geometry.py`・`world/state.py`・`perception/renderer.py` を走査)。
- 日をまたぐ便・日付を越える食事行・日付を越える会話セッションの扱い(**未確認**=読んでいない、ではなく該当の分岐を見つけられなかった。実行で確かめていない)。
- 機種をまたぐ浮動小数のビット一致の記録(R-55 と同じく無い)。
