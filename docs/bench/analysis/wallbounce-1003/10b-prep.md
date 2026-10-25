# 10b の準備: 状態台帳の 2 軸の表・2 つのハッシュの材料・原因の欄の場所とバイト(2026-10-03)

> 実行役(Opus 5.5)の調査と見積り。親の検収前。**src・tests・既存の docs は編集していない**。ランは mock だけ。
> 読んだ基準: `git archive HEAD`(a08109a)の写し。作業木で 10a の実装役が編集中の `environment.py`・`rail.py`・`runner.py`・`schedule.py`・`calendar.py` の途中の変更は読んでいない。行番号はすべて HEAD の値。パスは `src/shibuya/` を省略。
> 指示書: [壁打ちの決定 10-03](../../../design/v2-wallbounce-decisions-2026-10-03.md) §3 A2・A3・A4・§3-8・§10-2 の 3。既存のアジェンダ: [D-102 の土台の実装アジェンダ](../../../design/v2-d102-foundation-implementation-agenda.md) §2。棚卸し: [状態と乱数の棚卸し(09-30)](../wallbounce-0930/state-inventory-refresh.md)。R-72: [出来事の記録の形式](../../../research/v2-r72-event-log-formats.md) §7-4。
> 道具と結果(どれも argv で入出力・絶対パスは書かない):
> - [10b/soa_readers_ast.py](10b/soa_readers_ast.py) → [10b/soa_readers_ast.json](10b/soa_readers_ast.json): SoA の列名の読み手と書き手を AST で数える(追加 C の検査の試作)。
> - [10b/cause_counts.py](10b/cause_counts.py) → [10b/cause_counts_default.json](10b/cause_counts_default.json)・[10b/cause_counts_mem_rel_store.json](10b/cause_counts_mem_rel_store.json): 5,000 体 mock 1 日の書き込みの件数を既存の出力から数える。ハッシュの計算の時間も測る。
> - [10b/hash_order_check.py](10b/hash_order_check.py) → [10b/hash_order_check.json](10b/hash_order_check.json): 「behavior-hash を既定にしてから列を消せば final が動かない」をハッシュの関数の上で確かめる。
> 推奨は書かない。§3-1 の型の案・§2-2 の計算の形・§4 のテストの形は実行役の自前の構成=**未リサーチ(expedient)**。

## 0. 結論

1. **表の行数は 163 行**: SoA の列 98 行(agents 79・cells 5・pois 9・知覚 5)+SoA の外の状態 65 行。A2 (b)(どれかの腕が読めば入れる)で分けると、SoA で behavior-hash に**入れない列は 15 本**(agents 9・world 3・知覚 3)。うち死蔵が 6 本(agents の Q9 の 3 本・知覚の `last_b2_hash`・`last_b4_hash`・知覚の条件付きの `invocation_distance`)。
2. **「不明」は 6 件**(SoA 2・外の状態 4)。§1-7 に親への問いとして並べた。
3. **構成で読み手が変わる列**(`age`・`sex`・`talk_partner`・`weight_kg`・`sm_last`、加えて描画だけの `mem_last`)は A2 (b) により全部 behavior-hash に入れる。**挙動に効かないが保存則・センサスの項**の `revenue`・`energy_balance` は「挙動=入れない・復元=要る」。
4. **今の final** は `blake3(agents_hash ‖ world_hash ‖ 母集団 ‖ 予定表 [‖ 活動と意図])` で、知覚 SoA と SoA の外の状態は入らない(`run.py:465-485,3606-3622`)。**知覚の死蔵 2 列(A4)は今の final に入っていない**ので、消しても final は動かない。agents の死蔵 3 列(Q9)は入っているので、behavior-hash を既定にしてから消す順が要る。この順で final が動かないことを、ハッシュの関数の上で確かめた(§2-3・4 項目とも期待どおり)。
5. **ハッシュの費用**: blake3 は 0.37 ns/B(実測)。39 万体で既定の構成は 1 回 19 ms、全腕は 1 回 0.77 s(推計)。behavior-hash は全腕で 5,045 B/体(full の 94%)なので、2 本を別々に計算すると費用はほぼ 2 倍。
6. **AST の読み手の検査は実現できる**。ただし (i) 属性 `r.列名` だけを数えると、名前の表を回す読み(`INTERO_VARS`・`INTEROCEPTION_FIELDS`)で 5 列を見落とす。表を解決する処理を足すと 0 件になった。(ii) 走査の範囲を `engine/` だけにすると、読み手が `world/`・`perception/` にある 3 列(`noise_stage`・`open_from`・`open_to`)を見落とす。**全体の走査で手読みと食い違ったのは 2 列**(`band`=資産の表の文字列の誤検出、`b4_hash`=呼び手 0 のプロパティ)。ほかに「AST では読み手ありだが、手読みでは診断だけ」が 2 列(`revenue`・`energy_balance`)。
7. **原因の欄の口は 51**(resolve の公開の書き口 42+economy の台帳の書き口 9)。今どの口も call_id を受け取っていない。`apply` に届く前に、保留の組(`run.py:2696`)が発射の tick を落としている(残るのは適用の tick・体・級)。既に原因を持つ記録は 2 本(ActualLog の過程の id・テープの call_id)。
8. **1 日のバイト**(原因の欄=種類 u1+参照 u4 の 5 B/行・列のまま・圧縮前): 既に行があるログ(金 20,362 行+物 8,205 行)に足す分は 5,000 体で 143 KB・39 万体で 11.1 MB。新しい出来事の行に欄を持たせる分は、行為と取引だけなら 0.44 MB・34 MB。体の閾値越え・1 歩ずつの移動・活動の設定まで含めると 2.5 MB・196 MB。記憶の腕を ON にすると、さらに 0.53 MB・42 MB。39 万体の値は 5,000 体からの線形の外挿(推測)。
9. **ついでに見つけたこと**(直していない): 金の台帳の生ログは、5,000 体 1 日で 20,362 行を追記していた。宣言は 3.0 行/体/日で、実測は 4.07 行/体/日。リングの容量 16,384 行を超え、最初の 3,978 行が落ちている(`cause_counts_default.json` の `money_ledger.dropped`)。

## 1. 状態台帳の 2 軸の表

### 1-0 凡例と判定の規則

- **軸 1「挙動」**(behavior-hash に入れるか): A2 (b) に従う。**どれかの腕・どれかの構成で、分岐・計算・プロンプトの描画に使う読み手があれば「入れる」**。読み手が診断・要約・保存則の検査・日次センサスだけなら「入れない」。構成によって読み手が変わる列は「入れる(A2 b)」と書いた。
- **軸 2「復元が要る」**(日境界の再開で保存するか): **要る**=保存しないと再開後の挙動か full-hash が変わる/**導出できる**=資産・母集団・予定の表・ほかの列から再計算できる/**捨ててよい**=死蔵・tick の中だけの作業の値・キャッシュ・診断の計数(日の初めに 0 に戻すと宣言されたもの)/**不明**=親に問う(§1-5)。
- **AST 読み(engine / 全体)**: [10b/soa_readers_ast.json](10b/soa_readers_ast.json) の `read_strict` の数。`engine/` の中だけの数と `src/shibuya` 全体(`build/` を除く)の数。規則は §2-4。agents と pois の `cell`・`node` は同じ名前なので、AST の数は両方で同じ値になる(区別できない)。
- **書き手**と**読み手**は手で読んだ代表の場所。根拠の欄の先頭は宣言の場所。

### 1-1 agents(79 列・`agents/state.py:505-716`)

| 列 | 型・B/体 | 確保 | 書き手 | 読み手(腕・構成) | AST 読み(engine / 全体) | 軸 1 挙動 | 軸 2 復元 | 死蔵 | 根拠 |
|---|---|---|---|---|---|---|---|---|---|
| `cell` | i4・4 | 既定 | resolve(移動・乗降) | 全構成(候補・描画・関係・群れ) | 79 / 85 | 入れる | 要る |  | `agents/state.py:505`・resolve.py:1432 ほか |
| `node` | i4・4 | 既定 | resolve | 全構成(移動) | 21 / 21 | 入れる | 要る |  | `agents/state.py:507`・resolve.py:1432,1479 |
| `band` | i1・1 | 既定 | resolve.py:508,1483,1509,2821 | なし(2821 は dtype の参照) | 0 / 1 | 入れない | 導出できる(`cell_band[cell]`) |  | `agents/state.py:509`・resolve.py:1483 |
| `xy` | f4×2・8 | 既定 | resolve・geometry | 全構成(同席 2 m・群れ・顕著・描画) | 13 / 14 | 入れる | 要る |  | `agents/state.py:511`・salient.py:215・renderer.py:1252 |
| `path_next_node` | i4・4 | 既定 | resolve | 全構成 | 7 / 7 | 入れる | 要る |  | `agents/state.py:513`・resolve.py:1429 |
| `target_node` | i4・4 | 既定 | resolve | 全構成 | 9 / 9 | 入れる | 要る |  | `agents/state.py:515`・commit.py:554 |
| `kind` | i1・1 | 既定 | resolve.initialize | 全構成 | 11 / 14 | 入れる | 導出できる(母集団・ラン中不変) |  | `agents/state.py:535`・resolve.py:512・classical.py:350 |
| `age` | u1・1 | 既定 | resolve.initialize(母集団のときだけ) | **energy の空腹(CLI 既定)・classical のときだけ**。v1 空腹+mock(ライブラリ既定)では読まれない | 9 / 9 | 入れる(A2 b) | 導出できる(母集団・ラン中不変) |  | `agents/state.py:538`・resolve.py:1171,1182・classical.py:508 |
| `sex` | i1・1 | 既定 | 同上 | 同上 | 9 / 9 | 入れる(A2 b) | 導出できる(母集団・ラン中不変) |  | `agents/state.py:540`・resolve.py:1171・classical.py:508 |
| `hunger` | u1・1 | 既定 | resolve(advance_body・食事) | 全構成(変化検出・描画・classical) | 12 / 14 | 入れる | 要る |  | `agents/state.py:542`・change_detect.py:305・renderer.py:1796 |
| `fatigue` | u1・1 | 既定 | resolve.advance_body | 全構成(名前の表 `INTERO_VARS`・`INTEROCEPTION_FIELDS` 経由) | 2 / 4 | 入れる | 要る |  | `agents/state.py:544`・change_detect.py:77-81,305 |
| `thermal` | u1・1 | 既定 | resolve.set_thermal(環境の過程) | 全構成(同上) | 2 / 4 | 入れる | 要る |  | `agents/state.py:546`・change_detect.py:305・renderer.py:2374 |
| `hunger_stage` | i1・1 | 既定 | resolve.apply_detection | 全構成(段の前回値=ヒステリシス) | 2 / 2 | 入れる | 要る(履歴で決まる) |  | `agents/state.py:550`・change_detect.py:305 |
| `fatigue_stage` | i1・1 | 既定 | 同上 | 同上 | 2 / 2 | 入れる | 要る(履歴で決まる) |  | `agents/state.py:552`・change_detect.py:305 |
| `thermal_stage` | i1・1 | 既定 | 同上 | 同上 | 2 / 2 | 入れる | 要る(履歴で決まる) |  | `agents/state.py:554`・change_detect.py:305 |
| `money` | i4・4 | 既定 | resolve・台帳(世帯の現金の配列を共有) | 全構成(予算・購入) | 9 / 10 | 入れる | 要る |  | `agents/state.py:567`・run.py:2208・resolve.py:2170 |
| `holdings` | u1・1 | 既定 | resolve.py:2230 | 全構成(描画の手・世帯の消費) | 2 / 2 | 入れる | 要る |  | `agents/state.py:569`・goods_flow.py:473・renderer.py:1815 |
| `activity` | i1・1 | 既定 | resolve | 全構成 | 44 / 46 | 入れる | 要る |  | `agents/state.py:572`・activity.py:432 ほか |
| `plan_cursor` | i2・2 | 既定 | なし | なし | 0 / 0 | 入れない | 捨ててよい(Q9 で消す) | **死蔵** | `agents/state.py:574`・宣言 1 件のみ |
| `talk_partner` | i4・4 | 既定 | resolve(会話) | **記憶の腕(想起の相手)・店の記憶の腕(口コミの宛先)のときだけ**。既定の構成では読まれない | 2 / 2 | 入れる(A2 b) | 要る(会話が日をまたぐとき) |  | `agents/state.py:576`・memory.py:355・run.py:2639 |
| `invocation_distance` | u2・2 | 既定 | なし | なし | 0 / 0 | 入れない | 捨ててよい(Q9 で消す) | **死蔵** | `agents/state.py:578`・宣言のみ |
| `transit_state` | i1・1 | 既定 | resolve・rail | 全構成 | 38 / 38 | 入れる | 要る |  | `agents/state.py:581`・activity.py:433 ほか |
| `transit_ref` | i4・4 | 既定 | resolve | 全構成 | 3 / 3 | 入れる | 要る |  | `agents/state.py:584`・rail.py:650・civic.py:496 |
| `board_line` | i1・1 | 既定 | resolve | 全構成 | 6 / 6 | 入れる | 要る |  | `agents/state.py:588`・presence.py:1422 |
| `board_since` | i4・4 | 既定 | resolve | 全構成 | 4 / 4 | 入れる | 要る(tick 値) |  | `agents/state.py:591`・resolve.py:2003 |
| `sleep_pending` | i1・1 | 既定 | resolve | 全構成 | 6 / 6 | 入れる | 要る |  | `agents/state.py:595`・commit.py:868 |
| `intent_action` | i1・1 | 既定 | resolve.set_intent | 全構成 | 13 / 14 | 入れる | 要る |  | `agents/state.py:599`・intent.py:178 |
| `intent_target` | i4・4 | 既定 | 同 | 全構成(記憶の腕の照合・描画) | 3 / 4 | 入れる | 要る |  | `agents/state.py:603`・intent.py:194・memory.py:358 |
| `intent_kind` | i1・1 | 既定 | 同 | 全構成 | 3 / 4 | 入れる | 要る |  | `agents/state.py:605`・intent.py:193 |
| `intent_since` | i4・4 | 既定 | 同 | 全構成(TOO_FAR) | 2 / 2 | 入れる | 要る(tick 値) |  | `agents/state.py:607`・intent.py:263,438 |
| `poi_ref` | i4・4 | 既定 | resolve | 全構成 | 15 / 15 | 入れる | 要る |  | `agents/state.py:610`・crowd.py:231・classical.py:416 |
| `poi_since` | i4・4 | 既定 | resolve | 全構成(回転率) | 1 / 1 | 入れる | 要る(tick 値) |  | `agents/state.py:612`・crowd.py:231 |
| `queue_poi` | i4・4 | 既定 | resolve | 全構成 | 9 / 9 | 入れる | 要る |  | `agents/state.py:614`・memory.py:366・presence.py:1321 |
| `queue_since` | i4・4 | 既定 | resolve | 全構成 | 2 / 2 | 入れる | 要る(tick 値) |  | `agents/state.py:616`・crowd.py:242 |
| `refractory_until` | i4×11・44 | 既定 | resolve.py:816-818 | 全構成(アービタ) | 3 / 3 | 入れる | 要る(tick 値) |  | `agents/state.py:702`・run.py:3108,3160 |
| `wake_pending_class` | i1・1 | 既定 | 初期値 −1 だけ | なし | 0 / 0 | 入れない | 捨ててよい(Q9 で消す) | **死蔵** | `agents/state.py:705`・agents/state.py:724 |
| `last_action` | i1・1 | 既定 | resolve | 全構成 | 5 / 5 | 入れる | 要る |  | `agents/state.py:708`・intent.py:394 |
| `last_result` | i1・1 | 既定 | resolve | 全構成 | 12 / 12 | 入れる | 要る |  | `agents/state.py:711`・activity.py:297 |
| `last_result_tick` | i4・4 | 既定 | resolve | 全構成 | 7 / 8 | 入れる | 要る(tick 値) |  | `agents/state.py:713`・activity.py:296・renderer.py:2504 |
| `fail_streak` | u1・1 | 既定 | resolve.py:1074,1465,1526,1538,3054,3099 | なし(自分の +1 だけ) | 0 / 0 | 入れない | **不明**(問 1) |  | `agents/state.py:715`・AST: 読み 0・自己更新 4 |
| `edge_id` | i4・4 | 腕 edge | resolve | edge の腕 | 5 / 5 | 入れる | 要る |  | `agents/state.py:519`・resolve.py:1432 |
| `edge_s` | f4・4 | 腕 edge | resolve | edge の腕 | 5 / 5 | 入れる | 要る |  | `agents/state.py:522`・resolve.py:1432 |
| `focus_target` | i4・4 | 腕 attention | resolve | attention の腕(描画も) | 3 / 4 | 入れる | 要る |  | `agents/state.py:527`・resolve.py:1622・renderer.py:1130 |
| `focus_ttl` | u1・1 | 腕 attention | resolve | attention の腕 | 2 / 2 | 入れる | 要る |  | `agents/state.py:531`・resolve.py:1805 |
| `weight_kg` | f4・4 | 腕 energy(CLI 既定) | resolve.initialize_energy(1 回) | **energy の腕の初期化だけ**(`bmr` を作る)+要約。ランの途中では読まれない | 2 / 2 | 入れる(A2 b) | 導出できる(母集団+seed・ラン中不変) |  | `agents/state.py:558`・resolve.py:1182・energy.py:983 |
| `eer_kcal` | f4・4 | 腕 energy | resolve.initialize_energy(1 回) | energy の腕 | 8 / 8 | 入れる | 導出できる(ラン中不変) |  | `agents/state.py:560`・resolve.py:1153 |
| `since_meal_kcal` | f4・4 | 腕 energy | resolve | energy の腕(空腹の段) | 4 / 4 | 入れる | 要る |  | `agents/state.py:562`・resolve.py:1156 |
| `energy_balance` | f4・4 | 腕 energy | resolve.py:1155,1175,1205,1232 | **日次センサスと要約だけ**(`energy.py:903`) | 1 / 1 | 入れない | 要る(センサスの項) |  | `agents/state.py:564`・energy.py:903 |
| `plan_activity` | i1・1 | 腕 plan(実資産の既定) | resolve.set_plan_state | なし | 0 / 0 | 入れない | **不明**(問 2) |  | `agents/state.py:620`・AST: 読み 0 |
| `plan_flags` | i1・1 | 腕 plan | resolve.set_plan_state | plan の腕 | 3 / 3 | 入れる | 要る |  | `agents/state.py:623`・presence.py:1560 |
| `activity_until` | i4・4 | 腕 activity(v3 既定) | activity | activity の腕 | 6 / 6 | 入れる | 要る(tick 値) |  | `agents/state.py:628`・activity.py:350 |
| `activity_kind` | i1・1 | 腕 activity | activity | activity の腕(p_see の乗数・描画) | 4 / 6 | 入れる | 要る |  | `agents/state.py:631`・resolve.py:1133・renderer.py:1572 |
| `fam_thing` | i4×64・256 | 腕 familiarity | resolve.write_familiarity | familiarity の腕 | 9 / 9 | 入れる | 要る |  | `agents/state.py:636`・familiarity.py:199 |
| `fam_first` | i4×64・256 | 同 | 同 | 同 | 2 / 2 | 入れる | 要る(tick 値) |  | `agents/state.py:638`・familiarity.py:187 |
| `fam_last` | i4×64・256 | 同 | 同 | なし(書くだけ) | 0 / 0 | 入れない | 要る(表の行の一部・将来の読み手) |  | `agents/state.py:640`・AST: 読み 0 |
| `fam_visits` | u2×64・128 | 同 | 同 | 同 | 5 / 5 | 入れる | 要る |  | `agents/state.py:642`・familiarity.py:186 |
| `fam_exposures` | u2×64・128 | 同 | 同 | 同 | 4 / 4 | 入れる | 要る |  | `agents/state.py:644`・familiarity.py:186 |
| `mem_kind` | u1×128・128 | 腕 memory | resolve.write_memory | memory の腕(描画) | 11 / 11 | 入れる | 要る |  | `agents/state.py:649`・memory.py:333 |
| `mem_tick` | i4×128・512 | 同 | 同 | 同 | 5 / 5 | 入れる | 要る(tick 値) |  | `agents/state.py:651`・memory.py:309 |
| `mem_last` | i4×128・512 | 同 | 同 | memory の腕の**描画だけ**(B5 の時刻) | 3 / 3 | 入れる(A2 b) | 要る(tick 値) |  | `agents/state.py:653`・memory.py:403,485 |
| `mem_cell` | i4×128・512 | 同 | 同 | 同(想起の照合) | 4 / 4 | 入れる | 要る |  | `agents/state.py:655`・memory.py:376 |
| `mem_partner` | i4×128・512 | 同 | 同 | 同 | 6 / 6 | 入れる | 要る |  | `agents/state.py:657`・memory.py:372 |
| `mem_object` | i4×128・512 | 同 | 同 | 同 | 6 / 6 | 入れる | 要る |  | `agents/state.py:659`・memory.py:369 |
| `mem_result` | u1×128・128 | 同 | 同 | 同 | 9 / 9 | 入れる | 要る |  | `agents/state.py:661`・memory.py:378 |
| `mem_importance` | u1×128・128 | 同 | 同 | 同(score) | 4 / 4 | 入れる | 要る |  | `agents/state.py:663`・memory.py:310 |
| `mem_n` | u2×128・256 | 同 | 同 | 同 | 7 / 7 | 入れる | 要る |  | `agents/state.py:665`・memory.py:309 |
| `sm_poi` | i4×32・128 | 腕 store_memory | resolve.write_store_memory | store_memory の腕(店の選び) | 12 / 12 | 入れる | 要る |  | `agents/state.py:670`・store_choice.py:141 |
| `sm_valence` | f4×32・128 | 同 | 同 | 同 | 2 / 2 | 入れる | 要る |  | `agents/state.py:672`・store_memory.py:303 |
| `sm_precision` | f4×32・128 | 同 | 同 | 同 | 6 / 6 | 入れる | 要る |  | `agents/state.py:674`・store_choice.py:148 |
| `sm_first` | i4×32・128 | 同 | 同 | 同 | 2 / 2 | 入れる | 要る(tick 値) |  | `agents/state.py:676`・store_memory.py:306 |
| `sm_last` | i4×32・128 | 同 | 同 | **減衰 ga/citysim の腕だけ**+B5 の描画 | 4 / 4 | 入れる(A2 b) | 要る(tick 値) |  | `agents/state.py:678`・store_memory.py:330,346・memory.py:486 |
| `sm_n` | u2×32・64 | 同 | 同 | 同 | 4 / 4 | 入れる | 要る |  | `agents/state.py:680`・store_memory.py:305 |
| `sm_source` | u1×32・32 | 同 | 同 | 同 | 6 / 6 | 入れる | 要る |  | `agents/state.py:682`・store_choice.py:149 |
| `rel_partner` | i4×15・60 | 腕 relations | resolve.write_relations | relations の腕 | 10 / 10 | 入れる | 要る |  | `agents/state.py:689`・relations.py:709 |
| `rel_kind` | u1×15・15 | 同 | 同 | 同 | 7 / 7 | 入れる | 要る |  | `agents/state.py:691`・relations.py:733 |
| `rel_sign` | i1×15・15 | 同 | 同 | 同 | 4 / 4 | 入れる | 要る |  | `agents/state.py:693`・relations.py:736 |
| `rel_first` | i4×15・60 | 同 | 同 | 同 | 6 / 6 | 入れる | 要る(tick 値) |  | `agents/state.py:695`・relations.py:737 |
| `rel_last` | i4×15・60 | 同 | 同 | なし(書くだけ) | 0 / 0 | 入れない | 要る(表の行の一部・将来の読み手) |  | `agents/state.py:697`・AST: 読み 0 |
| `rel_n` | u2×15・30 | 同 | 同 | 同 | 7 / 7 | 入れる | 要る |  | `agents/state.py:699`・relations.py:738 |

### 1-2 world の cells(5 列・`world/state.py:121-130`・B/セル)

| 列 | 型 | 確保 | 書き手 | 読み手(腕・構成) | AST 読み(engine / 全体) | 軸 1 挙動 | 軸 2 復元 | 死蔵 | 根拠 |
|---|---|---|---|---|---|---|---|---|---|
| `density` | i4 | 既定 | resolve(毎 tick 再計算) | 全構成 | 7 / 10 | 入れる | 導出できる(`agents.cell` から) |  | `world/state.py:121`・resolve.py:1487,1511 |
| `density_stage` | u1 | 既定 | resolve(毎 tick 再計算) | 全構成 | 2 / 2 | 入れる | 導出できる |  | `world/state.py:123`・salient.py:484・presence.py:1715 |
| `noise_stage` | u1 | 既定 | 書き手 0(動的上書きの欄) | 全構成(描画 B4) | 0 / 3 | 入れる | 導出できる(いまは初期値のまま) |  | `world/state.py:125`・world/state.py:418・renderer.py:1219 |
| `open_count` | i4 | 既定 | resolve.py:541,1515 | なし | 0 / 0 | 入れない | 導出できる(`open_count_per_cell(tick)`) |  | `world/state.py:128`・AST: 読み 0 |
| `b4_hash` | u8 | 既定 | resolve.py:783 | なし(プロパティ `World.b4_hash` の呼び手 0) | 0 / 1 | 入れない | 導出できる(B4 の欄から再計算) |  | `world/state.py:130`・world/state.py:221 |

### 1-3 world の pois(9 列・`world/state.py:134-150`・B/POI)

| 列 | 型 | 確保 | 書き手 | 読み手(腕・構成) | AST 読み(engine / 全体) | 軸 1 挙動 | 軸 2 復元 | 死蔵 | 根拠 |
|---|---|---|---|---|---|---|---|---|---|
| `cell` | i4 | 既定 | 初期化 | 全構成 | 79 / 85 | 入れる | 導出できる(資産) |  | `world/state.py:134`・資産 |
| `node` | i4 | 既定 | 初期化 | 全構成 | 21 / 21 | 入れる | 導出できる(資産) |  | `world/state.py:136`・資産 |
| `stock` | i4 | 既定 | resolve(販売・補充) | 全構成 | 7 / 8 | 入れる | 要る |  | `world/state.py:138`・resolve.py:2167 |
| `price` | i4 | 既定 | 初期化だけ(world/state.py:158) | 全構成 | 4 / 6 | 入れる | 導出できる(資産・ラン中不変) |  | `world/state.py:140`・resolve.py:2166 |
| `revenue` | i8 | 既定 | resolve(販売) | **保存則の検査とラン要約だけ**(`run.py:3993` → `run.py:1118`) | 1 / 1 | 入れない | 要る(保存則の項) |  | `world/state.py:142`・run.py:1118,3993 |
| `capacity` | i4 | 既定 | 初期化だけ | 全構成(資源裁定) | 1 / 1 | 入れる | 導出できる(資産) |  | `world/state.py:144`・run.py:3316 → commit.py:413 |
| `open_from` | i2 | 既定 | 初期化だけ | 全構成(営業時間・描画) | 0 / 3 | 入れる | 導出できる(資産) |  | `world/state.py:146`・world/state.py:393・renderer.py:1546 |
| `open_to` | i2 | 既定 | 初期化だけ | 同 | 0 / 2 | 入れる | 導出できる(資産) |  | `world/state.py:148`・world/state.py:393 |
| `open_now` | i1 | 既定 | resolve(開閉の過程) | 全構成 | 3 / 4 | 入れる | 要る |  | `world/state.py:150`・opening.py:181・world/state.py:389 |

`pois.cell`・`pois.node` の AST の数は agents の同名の列と区別できない(上の凡例)。`pois.capacity` の AST の厳しい数 1 は `run.py:3316`(`arbitrate_resources` に渡す読み)。緩い数の残り 4 は `space.capacity(...)` のような同名の別物。

### 1-4 知覚 SoA(5 列・`perception/state.py:98-108`・今の checkpoint に入っていない)

| 列 | 型 | 確保 | 書き手 | 読み手(腕・構成) | AST 読み(engine / 全体) | 軸 1 挙動 | 軸 2 復元 | 死蔵 | 根拠 |
|---|---|---|---|---|---|---|---|---|---|
| `heading` | u1 | 既定(知覚 SoA) | resolve.set_notice_state | 顕著行為の p_notice | 1 / 1 | 入れる | 導出できる(事象の直前に毎回貼り直す) |  | `perception/state.py:98`・salient.py:205-214,400-414 |
| `task_flag` | u1 | 既定(知覚 SoA) | 同 | 同 | 1 / 1 | 入れる | 導出できる(同) |  | `perception/state.py:100`・同 |
| `last_b2_hash` | u8 | 既定(知覚 SoA) | なし | なし | 0 / 0 | 入れない | 捨ててよい(A4 で消す) | **死蔵** | `perception/state.py:103`・宣言のみ |
| `last_b4_hash` | u8 | 既定(知覚 SoA) | なし | なし | 0 / 0 | 入れない | 捨ててよい(A4 で消す) | **死蔵** | `perception/state.py:105`・宣言のみ |
| `invocation_distance` | u2 | 単体ベンチの条件付き | なし | なし | 0 / 0 | 入れない | 捨ててよい | **死蔵** | `perception/state.py:108`・perception/state.py:108 |

### 1-5 SoA の外の状態(tick をまたいで Python のオブジェクトが持つもの)

棚卸し(09-30)の表 2 を HEAD で確かめ直し、その後に入った状態(第 2 波 A・B=IMPLEMENTED #77〜#79)を足した。足した行は備考に「新」と書いた。棚卸しの後に変わったファイルは `classical.py`・`energy.py`・`relations.py`・`resolve.py`・`run.py`・`wom.py`・`perception/renderer.py` だけで、ほかのファイルの行番号は棚卸しと同じ。軸 1・軸 2 の規則は §1-0 と同じ。この表の状態はどれも今の checkpoint に入っていない(ただし O1・O4 は `activity_hash` に入る)。

| # | オブジェクト・属性 | 場所 | 型・大きさ | 読み手(腕・構成) | 軸 1 挙動 | 軸 2 復元 | 備考 |
|---|---|---|---|---|---|---|---|
| O1 | ActivityLayer `text`・`until_kind` | activity.py:178-179 | list[str]・配列(体数) | activity の腕(描画・満了) | 入れる | 要る | 今の `activity_hash` に入る |
| O2 | ActivityLayer `text_id`・`_texts`・`_text_ids`・`_digest_cache` | activity.py:181-184 | intern 表 | 派生 | 入れない | 導出できる | |
| O3 | ActivityLayer `_bt_agent`・`_bt_tick`・`_bt_start` | activity.py:189-191 | 予定の表 | activity の腕 | 入れない(入力の表) | 導出できる(予定の表) | |
| O4 | IntentLayer `_payload` | intent.py:139 | dict | 全構成(活動の控え) | 入れる | 要る | 今の `activity_hash` に入る(intent.py:471-482) |
| O5 | IntentLayer `_proposals`・`_executing`・`_kept_walk` | intent.py:135-141 | tick の中だけ | tick の中 | 入れない | 捨ててよい(tick の境で空) | |
| O6 | IntentLayer `stats`・`ticks_sum`・`ticks_n` | intent.py:142-144 | 計数 | 診断 | 入れない | 捨ててよい | |
| O7 | FamiliarityLayer `prev_cell` | familiarity.py:168,253 | i8・8 B/体 | familiarity の腕 | 入れる | 要る | 無いと tick 0 に全員が「入った」扱い |
| O8 | MemoryLayer `gist`・`_gist_order` | memory.py:242-243 | dict(40 字) | memory の腕(描画 B5) | 入れる(A2 b) | 要る | 5,000 体 1 日で 13,872 B(`cause_counts_mem_rel_store.json`) |
| O9 | MemoryLayer `_session_key`・`_gist_done` | memory.py:245-246 | dict・set | memory の腕 | 入れる | 要る | |
| O10 | MemoryLayer `_next_session`・`_next_join` | memory.py:247,257 | 整数 | memory の腕 | 入れる | 要る | 会話の管理の番号と揃える必要がある |
| O11 | MemoryLayer `_target`・`stats`・`recall_stats` | memory.py:240,248,252 | tick の中・計数 | 診断 | 入れない | 捨ててよい | |
| O12 | StoreMemory `stats` | store_memory.py:207 | 計数 | 診断 | 入れない | 捨ててよい | |
| O13 | StoreChoice `choice_poi`・`choice_reason`・`stats`・`by_hour` | store_choice.py:105-110 | 配列・計数 | 診断(決め手の控え) | 入れない | 捨ててよい | |
| O14 | StoreChoice `_b_tick`・`_b_off` | store_choice.py:97-99 | 予定の表 | store_choice の腕 | 入れない | 導出できる | |
| O15 | WomExtractor `stats`・`top`・`unmatched_words` | wom.py:244-246 | Counter | 診断 | 入れない | 捨ててよい | |
| O16 | RelationLayer `_prev_cell` | relations.py:646,1003 | i4・4 B/体 | relations の腕(知人の出現) | 入れる | 要る | |
| O17 | RelationLayer `_acq_until` | relations.py:644,986 | i4 体×k・60 B/体 | relations の腕 | 入れる | 要る(tick 値) | |
| O18 | RelationLayer `_co_since`・`_co_day`・`_co_active` | relations.py:635-637,938-939 | i4/i2 体×k・90 B/体+可変 | relations の腕(同席) | 入れる | 要る(tick 値と日番号) | |
| O19 | RelationLayer `_invite_salt`・`chosen_count`・`origin_of`・`stats` ほか | relations.py:628-633,826,884-895 | 設定・計数・tick の中 | 診断(`chosen_count` は足すだけ・`origin_of` は tick ごとに空にする run.py:3492) | 入れない | 捨ててよい(salt は設定から) | |
| O20 | ClassicalPolicy `_prev` | classical.py:371 | i8・8 B/体 | classical の腕で乗数 `m_prev` が 1 でないときだけ | 入れる(A2 b) | 要る | |
| O21 | ClassicalPolicy `_gate_hazard`(= EnergyLayer `meal_reset` と同じ配列) | classical.py:390・energy.py:804 | f4・4 B/体 | classical の腕 × 食事の門 `per_hour` | 入れる | 要る | 新(#79) |
| O22 | ClassicalPolicy `_condition`・`_tick`・`_eating_tick`・`_eating_cells`・`_ipf_cache` | classical.py:372-378 | tick の中・キャッシュ | tick の中 | 入れない | 捨ててよい | |
| O23 | ClassicalPolicy `_b_tick`・`_b_off`・`counts`・`by_hour` | classical.py:357 | 予定の表・計数 | 表/診断 | 入れない | 導出できる(表)・捨ててよい(計数) | |
| O24 | ClassicalPolicy `home_cell`・`acq_fn` | classical.py:344,385 | 設定・関数 | classical の腕 | 入れない | 導出できる(母集団・配線) | 新 |
| O25 | ClassicalChooser `last_habit`・`stats` | chooser.py:180,189 | 控え・計数 | 診断(決め手の記録) | 入れない | 捨ててよい | |
| O26 | TargetResolver `_cat_mask_cache`・`stats`・`entropy_sum`・`named_closed`・`move_stats` | poi_target.py:270,373,472,536,763 | キャッシュ・計数 | キャッシュ/診断 | 入れない | 導出できる・捨ててよい | |
| O27 | EnergyLayer `bmr` | energy.py:806・resolve.py:1182 | 配列(体数) | energy の腕 × `--energy-rate bmr` | 入れる | 導出できる(`weight_kg` から) | |
| O28 | EnergyLayer `meal_bits`・`n_meals`・`n_snacks`・`counts`・`intake_kcal`・`meal_start_*`・`stage_ticks*` | energy.py:810-831 | 配列・計数 | 日次センサスと要約だけ | 入れない | 捨ててよい(日ごとに 0 から=宣言) | |
| O29 | OutOfAreaMeals の予定 `tick`・`agent`・`slot`・`from_row`・`_start` | energy.py:610-616 | 予定の表 | energy の腕 | 入れない | 導出できる | |
| O30 | OutOfAreaMeals の遅らせの表 `d_agent`・`d_slot`・`d_arm_tick`・`d_eat_tick`・`d_wake_min` | energy.py:626-630 | 予定の表 | `meal_sleep_defer on` | 入れない | 導出できる | 新(#79) |
| O31 | OutOfAreaMeals `d_armed`(就寝中の食事を起床時に回す印) | energy.py:631,681-688 | bool(行数) | `meal_sleep_defer on` | 入れる | **不明**(問 3) | 新(#79) |
| O32 | HomeMeals の予定 `tick`・`agent`・`slot`・`_start`・`home_cell` | energy.py:738-758 | 予定の表 | `--home-meal plan` | 入れない | 導出できる | 新(#79) |
| O33 | HomeMeals `n_not_home`・`n_asleep`・OutOfAreaMeals の計数 `n_armed` ほか | energy.py:633-639,760 | 計数 | 診断 | 入れない | 捨ててよい | 新 |
| O34 | GroupNormMeter `_prev_xy`・`_pair_keys`・`_pair_len`・計数 | norm_meter.py:111-131 | 配列 | 計器(読むだけ) | 入れない | 捨ててよい(計器の連続性だけ) | |
| O35 | PlanExecutor 退出の歩行 `_walk_since`・`_walk_line`・`_plan_rider`・`_rewalked`・`_rewalk_*` | presence.py:715-730 | i4 ほか(体数) | walk_to_platform の腕 | 入れる | 要る(tick 値) | |
| O36 | PlanExecutor `_defer_ids`・`_defer_deadline`・`_defer_line`・`_defer_walk`・`_extra`・`_skip_depart_at` | presence.py:707-711,752-755 | 配列・辞書 | plan の腕 | 入れる | 要る | |
| O37 | PlanExecutor `_pulled_in_today` | presence.py:756 | bool(体数) | plan の腕 | 入れる | 捨ててよい(日ごとに作り直す前提。今は `run_day` ごとに新しく作る) | |
| O38 | PlanExecutor `ev_*`・`arrival_*`・`absent`・`blocks` | presence.py:661-666,990-1108 | 予定の表 | plan の腕 | 入れない | 導出できる | |
| O39 | ConversationManager `sessions`・`_of_agent`・`_refusal_until`・`_next_id`・`pending_invites`・`_pair_invite_until`・`_speaker_invite_until` | conversation.py:280-313 | dataclass・辞書 | 全構成 | 入れる | 要る(tick 値) | 直列化の書き手が要る |
| O40 | ConversationManager `join_events` | conversation.py:280-313 | list | memory の腕(`_next_join` で読む) | 入れる(A2 b) | 要る | |
| O41 | ConversationManager `origin_counts` ほかの計数 | conversation.py:280-313 | 計数 | 診断 | 入れない | 捨ててよい | |
| O42 | Arbiter `_pending`・`_pool`・`queue`・`_last_tick` | arbiter.py:535-543 | 配列・float・辞書 | 全構成 | 入れる | 要る(tick 値) | |
| O43 | run_day の局所 `pending`(適用待ちの応答) | run.py:2696 | list[11 要素の組] | 全構成 | 入れる | 要る | `ParseResult`・`Target` を持つので直列化が難しい。発射の tick を持たない(§3-2) |
| O44 | run_day の局所 `fleet_deferred`・`fleet_waiting`・`replay_inbox` | run.py:2393-2402 | list・set・dict | 艦隊・再生のランだけ | 入れる(A2 b) | 要る | |
| O45 | ChangeDetector `_prev_raw` | change_detect.py:274,299 | i4 セル×4 | 全構成 | 入れる | 要る | None だと日の頭に全セル起床 |
| O46 | SalientProcess `rng`・`event_seen_tick`・`budget` | salient.py:153-176 | Generator・i4 体数 | 全構成 | 入れる | 要る | 10c でカウンタ型にする |
| O47 | PublicServiceDispatchProcess `rng`・`pending` | civic.py:116-117 | Generator・list | 全構成 | 入れる | 要る | 10c |
| O48 | HotelProcess `rooms_occupied`・`bed_cell` | civic.py:271,278 | 配列 | 全構成(寝床の空き) | 入れる | 要る | |
| O49 | LargeEventProcess `_inside` | civic.py:449 | 配列 | 全構成 | 入れる | 要る | |
| O50 | RailProcess `occupancy`・`peak_ratio`・`_return_queue`・`_inbound`・`_inbound_ready` | rail.py:283-298 | 配列・辞書 | 全構成(満員) | 入れる | 要る | 日境界では空のはず(未検証) |
| O51 | CrowdProcess `queue_action` | crowd.py:184 | i1 体数 | 全構成 | 入れる | 要る | |
| O52 | ShelfRestockProcess `backroom`・`_acted_today` | goods_flow.py:171,182 | 配列 | 全構成(補充量の上限) | 入れる | 要る | `_acted_today` は分 0 で 0 に戻る |
| O53 | WasteCollection `_cursor`・`waste_g_collected`/StreetCleaning `litter_g`・`swept_g` | goods_flow.py:426-432,565-568 | 配列・float | この過程と要約だけ(ビン `_bin` はエージェントの側から読まれない) | 入れない | 要る(物の流れの続き・保存則の項) | |
| O54 | RoadWorks `blocked_cells`・`occupied_edges` | logistics.py:285-286 | 配列 | 過程の外の読み手 0 | 入れない | 要る(工事の続き) | |
| O55 | LastMile `delivered`・`_cum`/BusTaxi・Traffic(`cell_hourly`・`cell_vehicles`)・Infra(`power_kwh`)・Press・Opening・DeliveryInbound の計数 | logistics.py:121-124,211・traffic.py:100-103・civic.py:200,382・opening.py:127-129・goods_flow.py:346-349 | 計数・日ごとの場 | 要約だけ | 入れない | 捨ててよい(計数)・導出できる(日ごとの場と遅れの表) | |
| O56 | EnvironmentProcess `replay_date`・`stratum`・`_row`・`_shade` | environment.py:144-157 | 値 | 全構成(描画の日付・日陰) | 入れる | 導出できる(seed と日番号から選ぶ) | 10a で日ごとに進める |
| O57 | MoneyLedger `_lines`・`_day` | economy/ledger.py:222-269 | 5 科目 × 6 部門の配列 | 全構成(世帯の現金は `agents.money` と同じ配列 `run.py:2208`・店の現金は補充の支払い) | 入れる | 要る | |
| O58 | MoneyLedger 生ログのリング・`_flow_daily`・`_snap` | economy/ledger.py:222-269・:662-690 | 24 B/行・容量 N 比例(下限 16,384) | 日次センサス・保存則 | 入れない | **不明**(問 4) | 5,000 体 1 日で 20,362 行を追記し 3,978 行が落ちた |
| O59 | GoodsLedger `_shelf`・`_bin`・`_sold_today`・`_day` | economy/goods.py:330-406 | 配列 | 全構成(棚=販売の可否) | 入れる | 要る | |
| O60 | GoodsLedger 配達ログのリング | economy/goods.py:936-958 | 16 B/行 | 日次センサス | 入れない | **不明**(問 4) | 5,000 体 1 日で 8,205 行(落ち 0) |
| O61 | WorldProcessRunner `log`(ActualLog) | world/processes/actual_log.py:162-166 | 31 B/行(見積り) | 遵守率の計算・要約 | 入れない | **不明**(問 4) | 5,000 体 1 日で 29,032 行 |
| O62 | UndefinedActionRegistry `log`・`counts`・`precedents` | llm/undefined.py:697-705 | 辞書 | run_day は裁定器なし=効かない | 入れない | 捨ててよい | |
| O63 | PerceptionRenderer のキャッシュ `_b1_cache`〜`_b4_cache`・`_rank_cell_cache`・`_acq_cache`・`_tickc` | perception/renderer.py:1115,1146-1152 | キャッシュ | 描画(派生) | 入れない | 導出できる | |
| O64 | PerceptionRenderer の口 `acquaintance_fn`・`memory_recall`・`session_partner_fn`・`named_closed_lookup`・`signage_exposures` | perception/renderer.py:1171 ほか・run.py の配線 | 関数・tick の中 | 配線 | 入れない | 捨ててよい | |
| O65 | LLMBridge・TapeWriter・FleetBridge の計数・行・処理中の呼 | llm_bridge.py:537-554・tape.py:242-278・llm/fleet.py | 計数・ファイル | 記録 | 入れない | テープはファイルに出る・処理中の呼は O44 と同じ扱い | |

O28 は日次センサスの項だが、日の締めで読み終わってから 0 に戻す宣言なので「捨ててよい」にした。日の途中で再開するなら「要る」に変わる(今の決定は日境界の再開だけ=A9)。

### 1-6 構成で読み手が変わる列と、挙動に効かない保存則の列の扱い

| 列 | 読む構成 | 読まない構成 | 軸 1 | 軸 2 | 理由 |
|---|---|---|---|---|---|
| `age`・`sex` | energy の空腹(CLI 既定)・classical | v1 の空腹+mock(ライブラリの既定) | 入れる | 導出できる(母集団) | A2 (b)。母集団から入るので値はラン中不変 |
| `talk_partner` | 記憶の腕(想起の相手 `memory.py:355`)・店の記憶の腕(口コミの宛先 `run.py:2639`) | 既定 | 入れる | 要る | A2 (b) |
| `weight_kg` | energy の腕の**初期化だけ**(`resolve.py:1182` で `bmr` を作る) | 途中では読まれない | 入れる | 導出できる(母集団+seed) | A2 (b)。ランの途中で値を揺らしても挙動は変わらないので、追加 C の揺らし試験では「揺らしても何も変わらない入れる列」になる(陽性対照には使えない) |
| `sm_last` | 店の記憶の減衰 `ga`・`citysim`(`store_memory.py:330,346`)と B5 の描画(`memory.py:486`) | 減衰 `actr`(既定)で描画を読まない mock | 入れる | 要る | A2 (b) |
| `mem_last` | 記憶の腕の描画だけ(B5 の時刻) | mock(描画を読まない) | 入れる | 要る | 描画も挙動に数える(§1-0)。mock では final に効かないので、追加 C では prompt_hash の比較が要る |
| `revenue` | 保存則の検査 `run.py:1118`・要約 `run.py:3993` | 挙動の読み手は無い | **入れない** | **要る** | 保存則 `Σmoney+Σrevenue+運賃=Σmoney_start` の項。再開で 0 に戻すと保存則が壊れる |
| `energy_balance` | 日次センサス・要約 `energy.py:903` | 挙動の読み手は無い | **入れない** | **要る** | センサスの項。日をまたいで足していく値 |

追加 C の揺らし試験(棚卸し 表 7)では、`revenue`・`energy_balance` は揺らすと保存則とセンサスが壊れるので、「揺らすが保存則とセンサスの比較は外す」か「揺らさない」の別扱いが要る(棚卸しの案のまま)。

### 1-7 親への問い(「不明」6 件+確認 1 件)

| 問 | 対象 | 何が分からないか | 選択肢 |
|---|---|---|---|
| 1 | `fail_streak`(SoA) | 読み手 0。書き手は自分に 1 を足すか 0 に戻すだけ(`resolve.py:1074,1465,1526,1538,3054,3099`) | (a) 捨ててよい(再開で 0 から。full-hash からも外す) (b) 要る(full-hash に入れて数え続ける) (c) Q9 と一緒に死蔵として消す |
| 2 | `plan_activity`(SoA・plan の腕) | 読み手 0。書き手 `set_plan_state` は予定の行の活動を書く。日をまたぐ予定の行で値が導出できるかを確かめていない | (a) 導出できる(予定の表と T から) (b) 要る (c) 死蔵として消す |
| 3 | OutOfAreaMeals `d_armed` | 夜中に印が付き、翌日の起床で食べる場合に、印が日をまたぐか確かめていない(表は日ごとに作り直す) | (a) 要る(持ち越す) (b) 日の締めで落とす(宣言) |
| 4 | 金の生ログ・物の配達ログ・ActualLog のリング(O58・O60・O61=3 行) | 挙動は読まない。日の締めのセンサスで読み終わる。指示書 10-03 §6 ① の出来事の記録がこれらをファイルに出すかで変わる | (a) 捨ててよい(ファイルに出す前提) (b) 要る(リングごと保存) |
| 5(確認・不明の数に入れない) | 知覚 SoA の `heading`・`task_flag` | A2 (b) では読まれるので「入れる」。ただし事象の直前に毎回貼り直す派生の値で、今の final にも入っていない。入れると 10e の張り替えに含まれる | (a) behavior-hash に入れる (b) 派生として入れない(宣言) |

## 2. 2 つのハッシュの設計の材料

### 2-1 今の final が含むもの

- **組み立て**: `Checkpoint`(`run.py:465-485`)。`combined = blake3("\x1f".join([agents_hash, world_hash, population_hash, schedule_hash] (+ activity_hash があれば)))`。`final_hash` は最後の checkpoint の `combined`(`run.py:895-896`)。
- **頻度**: `checkpoint_every=360`(`run.py:1583`)。`(tick+1) % 360 == 0` か最後の tick のとき(`run.py:3606`)。1 日 1,440 tick で 4 回。
- **agents_hash**: `Registry.state_hash()`(`core/soa.py:382-406`)。見出し `shibuya.core.soa/v1`・kind・個体数のあと、**宣言順に**全列の「名前・dtype・形・生バイト」を区切り `_SEP` で連結して blake3。見出しに**列の数は入らない**(§2-3 で効く)。腕の列は、その腕のランでは宣言されるので入る。
- **world_hash**: `blake3(cells.state_hash() ‖ "\x1f" ‖ pois.state_hash())`(`world/state.py:456-460`)。cells 5 列+pois 9 列。
- **population_hash・schedule_hash**: W16 母集団と W17 予定表の同定(ラン中不変)。
- **activity_hash**: 活動層の文と「まで」の型。意図の層があれば `blake3(活動 ‖ "\x1f" ‖ 意図の控え)`(`run.py:3613-3621`)。活動層の無いランでは混ぜない。
- **入らないもの**: 知覚 SoA(`heading`・`task_flag`・死蔵 3 列)・§1-5 の外の状態の全部(O1・O4 を除く)・金と物の台帳。

### 2-2 behavior-hash と full-hash に分けたときの列とバイトと費用

| 範囲 | 今の final(= full の SoA 部分) | behavior-hash(軸 1 の列だけ) | 外す列 |
|---|---|---|---|
| agents 既定 | 40 列・137 B/体 | 35 列・130 B/体 | `band`・Q9 の 3 列・`fail_streak` |
| agents 全腕 | 79 列・5,373 B/体 | 70 列・5,045 B/体(94%) | 上の 5 列+`energy_balance`・`plan_activity`・`fam_last`(256 B)・`rel_last`(60 B) |
| cells | 5 列・18 B/セル | 3 列・6 B/セル | `open_count`・`b4_hash` |
| pois | 9 列・33 B/POI | 8 列・25 B/POI | `revenue` |
| 知覚 SoA | 入っていない | 問 5 次第(2 B/体) | 死蔵 3 列 |
| 外の状態 | 入っていない | 軸 1 が「入れる」の行(O1・O4・O7〜O10 ほか) | 「入れない」の行 |

**計算の時間**(`cause_counts_default.json` の `hash_cost`・この機械の 1 回の実測・numpy の配列を blake3 に通す時間): 全腕 5 万体(268.7 MB)で 0.098 s=**0.37 ns/B**。既定 5,000 体のランの 4 回の checkpoint は合計 5.4 ms(`phase_checkpoint_s`)。

39 万体への推計(0.37 ns/B で線形・推測):

| 構成 | full(今の定義) 1 回 | behavior 1 回 | 両方を別々に計算 1 日(4 回) |
|---|---|---|---|
| 既定 | 53 MB → 20 ms | 51 MB → 19 ms | 0.16 s |
| 全腕 | 2.10 GB → 0.77 s | 1.97 GB → 0.73 s | 6.0 s |

計算の形の候補(未リサーチ):
- (a) **10b の形**: final は今のまま `state_hash()`、behavior は `state_hash(exclude=軸 1 で入れない列)` をもう 1 回。費用はほぼ 2 倍。既定の final は 1 バイトも動かない。
- (b) **列ごとの digest を 1 回だけ取り、2 通りに束ねる**: 費用は約 1 倍。ただしハッシュの定義が変わるので final が動く。10e の版上げでしか選べない。
- 外の状態の full-hash への足し方: `to_state()` の配列を宣言順に同じ形で混ぜる。大きさは全腕で体あたり約 200 B(O7・O16〜O18・O20・O21・O35・O46・O48・O51 ほかの和・推測)+台帳。会話の管理(O39)と保留の応答(O43)は直列化の書き手が要り、大きさは未計測。

**full-hash の範囲の決め方**(未リサーチ): 軸 2 が「捨ててよい」の行(診断の計数・キャッシュ)まで full-hash に入れると、再開のあとそれらは 0 から始まるので `resume == straight` が成り立たない。full-hash に入れるのは軸 2 が「要る」と「導出できる」の行に限る、という形が要る(導出できる行は再計算して入れると、導出の誤りも捕まえられる)。

### 2-3 死蔵の列を消しても final が動かないことの確認

**事実**: 知覚の死蔵 2 列(A4 の `last_b2_hash`・`last_b4_hash`)は**今の final に入っていない**(§2-1)。だから、いつ消しても final は動かない。動くのは知覚 SoA のバイトの宣言と、その列を見る試験だけ(棚卸し 表 8 の `tests/perception/test_hashes_state.py:67-73` など)。ただし 10b で知覚 SoA を full-hash に足すなら、足した後に消すと full-hash が動く。**消すのを先にするか、full-hash に足すのを後にするか**の順を決める必要がある。

agents の死蔵 3 列(Q9)は `agents_hash` に入っているので、消せば今の final は 15 腕とも動く。behavior-hash を既定にしてから消せば動かない。これをハッシュの関数の上で確かめた([10b/hash_order_check.json](10b/hash_order_check.json)・全腕 2,000 体・全列を乱数で埋めた合成の状態):

| 消す列の組 | (a) 消す前の `state_hash(exclude=組)` = 消した後の `state_hash()` | (b) 消す前の `state_hash()` ≠ 消した後 | (c) 除外した列を書き換えても behavior は不変(陰性対照) | (d) `hunger` を 1 要素変えると behavior が動く(陽性対照) |
|---|---|---|---|---|
| Q9 の 3 列 | 一致 | 食い違う | 不変 | 動く |
| 軸 1 で入れない agents の 9 列 | 一致 | 食い違う | 不変 | 動く |
| 何も消さない | 一致 | 一致(期待どおり) | (対象なし) | 動く |

理由: `state_hash` の見出しに列の数が入らず、除外は名前で飛ばすだけなので、「除外して計算」と「宣言から消して計算」は同じバイト列になる(`core/soa.py:393-406`)。**この性質は 10e の手順の前提**なので、`Registry.state_hash` の見出しに列の数や列名の一覧を足す変更を入れると崩れる。10b の試験でこの性質を固定しておくのがよい(§4 の T2)。

### 2-4 追加 C の AST 検査の実現性

[10b/soa_readers_ast.py](10b/soa_readers_ast.py) で、宣言から列名を取り(手で列挙しない)、`src/shibuya` を AST で走査して列ごとに読み手と書き手を数えた。

**数え方の規則**(実行役の自前の構成=未リサーチ):
- 属性 `X.列名` を書き(代入の左辺・`X.c[...] = `・`np.*.at(X.c, ...)` の第 1 引数・`X.c.fill`・`out=X.c`)と読みに分ける。`X.c.dtype` などの型の参照と、同じ列への代入の右辺に出る読み(`X.c[a] = X.c[a] + 1`=自己更新)は読みから外す。
- 文字列は `field("c")`(`f = r.field` の別名も)・`getattr(r, "c")`・`arrays["c"]` の形だけを読みとし、`field("c")[...] = ` は書きにする。
- 名前の表を回す読み(`for v, sf in INTERO_VARS: r.field(sf)`)は、頂上で定義した文字列の表を解決して、表の中の全列の読みに数える。解決できない `field(変数)` は場所を出す。
- 一般的な名前(`cell`・`kind` など)は別のオブジェクトの属性と衝突するので、手前の式が SoA を指していそうなもの(末尾が `registry`・`r`・`reg`・`agents`・`cells`・`pois` など)だけを数えた「厳しい数」を表 1 の AST 欄に使った。

**手読み(§1 の表)との突き合わせ**(読み手の有無で比べた):

| 走査の範囲・規則 | 食い違い | 内訳 |
|---|---|---|
| 全体(`src/shibuya`・`build/` を除く)・名前の表を解決 | **2 列** | `band`: `world/assets.py:368` の `cells["band"]`(資産の表の列)を誤って読みに数えた。`b4_hash`: `world/state.py:221` のプロパティの中の読みを数えたが、プロパティの呼び手は 0 |
| `engine/` だけ | 3 列 | `noise_stage`・`open_from`・`open_to` を見落とす(読み手は `world/state.py:389-418`・`perception/renderer.py` にある)。`band`・`b4_hash` は engine の中では 0 で、手読みと一致 |
| 属性だけ(名前の表を解決しない) | +5 列 | `fatigue`・`thermal`・`hunger_stage`・`fatigue_stage`・`thermal_stage` の読みを見落とす(`hunger` は別の読み手があるので有無は一致) |
| 分類(有無ではない) | 2 列 | `revenue`・`energy_balance`: AST は読み手ありと数えるが、手読みでは診断・保存則・センサスだけ。AST は「挙動の読み」と「診断の読み」を区別できない |

解決できない `field(変数)` は engine に 4 か所あった: `resolve.py:534`(初期化で式の中のタプルを回す)・`resolve.py:538`(同・書き)・`resolve.py:786`(閾値越えの段の書き)・`run.py:353`(診断の読み)。ほかに `agents/state.py:772`・`perception/state.py:117`(`__getattr__` の転送)。

**検査の形の案**(未リサーチ):
1. 宣言に 2 軸を持たせる(`declare(..., behavior=, restore=)`)。表と検査と揺らし試験を同じ宣言から作る。
2. 走査は `src/shibuya` 全体にする(`engine/` だけでは 3 列を見落とす)。
3. `behavior=False` の列は「厳しい数の読み=0」を求める。ただし診断の読み手は**許す場所の一覧**(`run.py` の要約・`energy.py` のセンサスなど、関数名か `path:行` で)に載っていれば許す。
4. 解決できない `field(変数)` は 0 か許す一覧に載っていることを求める(名前の表は登録制)。
5. 限界: 配列を関数に渡した先の読み・`getattr(obj, 変数)`・描画の文字列の組み立ての中の読みは静的には追い切れない。だから追加 C の揺らし試験(動的)と組にする。

## 3. 原因の欄(§10-2 の 3)を入れる場所とバイト

### 3-1 欄の型の案(未リサーチ)

| 欄 | 型 | 中身 |
|---|---|---|
| `cause_kind` | u1 | 0=なし・1=呼(LLM の応答)・2=古典の決定(LLM なしの選び)・3=エンジンの継続(前の呼の続き。歩行の 1 歩・並びの順番が来た)・4=予定(W17・退出・範囲外の食事)・5=世界の過程・6=体(閾値越え)・7=境界(初期化・域外からの入り) |
| `cause_ref` | u4 | 種類 1・3 → **呼の通し番号**(ランの中で 0 から。テープの calls の行番号と一致させる)/種類 5 → 過程の id(ActualLog が持つ過程の小さな整数の表 `actual_log.py:165-166` をそのまま使う)/それ以外 → 0 |

1 行 5 B(列のまま・圧縮前)。u4 の通し番号は、39 万体 × 6.94 呼/体/日(c7-day-4)で約 1,580 日、mock の 14.0 呼/体/日で約 790 日もつ。call_id の文字列(`"{T}:{体}:{級}"`)は通し番号からテープで引く。比べた案: R-72 §7-4 の「種類 1 B+参照 8 B=9 B」。参照に (T, 体, 級) をそのまま詰めるなら 8 B が要る。

### 3-2 書き口の一覧(51 口)

**今どの口も call_id を受け取っていない**。LLM の応答は `run.py:3014,3046,3220` で保留の組 `pending`(`run.py:2696`)に入るが、組に入るのは適用の tick・級・体・起床条件・応答の中身で、**発射の tick を落としている**。call_id(`"{発射の tick}:{体}:{級}"`=`run.py:3251`)は適用の時点では組み直せない。さらに `apply` に渡る `IntentBatch`(`commit.py:216-231`)は体・行動・対象・資源・時刻の 5 配列だけで、呼の出どころを持たない。原因の欄を足すには、(i) 保留の組に呼の通し番号を足す (ii) `IntentBatch` に同じ長さの配列を 1 本足す (iii) `apply` の中の各処理と台帳の書き口に、その配列(か過程の id)を渡す、の 3 か所の配線が要る。

件数は 5,000 体 mock 1 日(既定の腕=v3+活動層・final `993276d5e5bb5cbe`・69,978 呼=10a-prep と一致)を回し、既存の出力から数えた([10b/cause_counts_default.json](10b/cause_counts_default.json))。記憶の腕は記憶・関係辺・店の記憶を ON にしたラン(final `1e28c8ce3f80d888`・72,930 呼=10a-prep と一致・[10b/cause_counts_mem_rel_store.json](10b/cause_counts_mem_rel_store.json))。書き口にカウンタは挿していない。数えられないものは「未計測」。

**(A) 台帳の書き口(economy・9 口)**: 行のログを既に持つので、行に 2 欄を足すだけで済む。

| # | 書き口 | 呼び手 | 原因の種類 | call_id | 1 日の件数(5,000 体) | 出どころ |
|---|---|---|---|---|---|---|
| E1 | `Ledger.purchase_many`(economy/ledger.py:507) | resolve.py:2223(購入)・2350(食事) | 呼 | 持たない | 9,573(消費支出・= 購入 5,076+食事 4,497) | 金の生ログ |
| E2 | `Ledger.transfer_many`(ledger.py:447) | rail.py:590(運賃) | 過程 `rail_operation_static`(元は乗車の呼) | 過程の id は渡せる | 3,409(持ち出し) | 金の生ログ |
| E3 | `Ledger.endow_households`(ledger.py:516) | resolve.py:522(初期化) | 境界 | 不要 | 3,359(来街者持込・残った行)+落ちた行の一部 | 金の生ログ |
| E4 | `Ledger.endow_stores`(ledger.py:530) | cli.py:289 | 境界 | 不要 | 落ちた 3,978 行の内数(推測) | 金の生ログ |
| E5 | `GoodsLedger.restock_many`(goods.py:650・金の脚 goods.py:680) | resolve.py:2654 ← goods_flow.py:264 | 過程 `shelf_stock_restock`(設計上は店員の行為) | 過程の id は渡せる | 物 43+金 43(域外仕入) | 両ログ |
| E6 | `GoodsLedger.sell_many`(goods.py:602) | resolve.py:2245 | 呼(購入) | 持たない | 5,076(販売) | 配達ログ |
| E7 | `GoodsLedger.to_bin_many`(goods.py:706) | resolve.py:2683 ← goods_flow.py:465 | 過程 `waste_collection` | 渡せる | 1,543(廃棄ビンへ) | 配達ログ |
| E8 | `GoodsLedger.collect_waste`(goods.py:730) | resolve.py:2726 ← goods_flow.py:506 | 過程 `waste_collection` | 渡せる | 1,543(廃棄搬出) | 配達ログ |
| E9 | `GoodsLedger.consume_many`(goods.py:767) | resolve.py:2713 ← goods_flow.py:485 | 過程(世帯の消費) | 渡せる | 未計測(この口は配達ログに行を書かない) | (対象なし) |

engine から今は呼ばれていない口: `move_goods`(goods.py:515)・`deliver`(:698)・`stocktake`(:789)・`depreciate`(ledger.py:542)・`revalue_inventory`(:560)。

**(B) SoA を書く口(resolve の公開の書き口・42 口)**: 行のログが無い。原因の欄を持たせるには 指示書 10-03 §6 ① の出来事の行が要り、欄はその行の 2 列になる。

| # | 書き口(resolve.py) | 呼び手(代表) | 原因の種類 | call_id | 1 日の件数(5,000 体) |
|---|---|---|---|---|---|
| R1 | `initialize` :480 | run.py:2213 | 境界 | 不要 | 1 回 |
| R2 | `set_initial_activity` :544 | run.py:2435 | 境界 | 不要 | 1 回 |
| R3 | `initialize_energy` :1160 | run.py:2245 | 境界 | 不要 | 1 回 |
| R4 | `set_plan_state` :571 | presence.py:1130 ほか 12 か所 | 予定 | 不要 | 未計測 |
| R5 | `begin_planned_sleep` :628 | run.py:2954・presence.py:554,1225 | 予定 | 不要 | 未計測(予定の就寝の内訳 `planned_sleep_counts` は slept 12・asleep 710 ほか) |
| R6 | `wake_from_plan` :753 | run.py:2963・presence.py:1241 | 予定 | 不要 | 830(woke) |
| R7 | `apply_detection` :779 | run.py:2906 | 体 | 不要 | 102,020(内受容の閾値越え・上げ下げの和) |
| R8 | `set_refractory` :792 | run.py:3183 | 過程(アービタ・元は呼) | 持たない | 未計測(呼ごとに 1 回なら 69,978・推測) |
| R9 | `clear_refractory` :822 | run.py:3069 | 過程(アービタ) | 持たない | 未計測 |
| R10 | `set_activity` :851 | activity.py:311,336 | 呼(v3 の活動欄)/エンジン(満了・ぶらつき) | 持たない | 70,163(`activity_set`) |
| R11 | `set_activity_until` :870 | activity.py:363,370・intent.py:461 | 同 | 持たない | 未計測 |
| R12 | `write_familiarity` :910 | familiarity.py:355 | 知覚(露出)/行為の呼 | 持たない | 未計測(腕を回していない) |
| R13 | `write_memory` :935 | memory.py:539 | 行為の呼/看板の露出 | 持たない | 75,448(記憶の腕・新しい行 57,807+統合 17,641) |
| R14 | `write_store_memory` :962 | store_memory.py:317 | 行為の呼/口コミ(話し手の呼)/看板 | 持たない | 30,999(記憶の腕・自分 14,736+看板 16,263) |
| R15 | `write_relations` :986 | relations.py:672,743,976 | 会話の呼/同席(エンジン)/初期の辺(境界) | 持たない | 525(記憶の腕)+初期の辺 9,198 |
| R16 | `join_conversation` :1007 | run.py:3432 | 招いた呼 | 持たない | 未計測 |
| R17 | `set_intent` :1027 | intent.py:400 | 呼(応答の提案) | 持たない | 394 |
| R18 | `clear_intent` :1049 | intent.py:452,467 | エンジン(到着・中断) | 持たない | 未計測(到着 197+取り下げ 172 の内数) |
| R19 | `fail_intent` :1059 | intent.py:459 | エンジン | 持たない | 0(`failed`) |
| R20 | `relabel_intent_failure` :1081 | intent.py:421,464 | エンジン | 持たない | 未計測 |
| R21 | `advance_body` :1101 | run.py:2728 | 体 | 不要 | 1,440 回(全員を一括。体ごとの行にすると 720 万) |
| R22 | `energy_out_of_area_meal` :1246 | run.py:2736,2742 | 予定(範囲外の食事) | 不要 | 7,785 |
| R23 | `energy_home_meal` :1265 | run.py:2982 | 予定(自宅) | 不要 | 0(既定の腕では予定が無い・推測) |
| R24 | `apply` :1291(Phase C) | run.py:3322・geometry.py:168 | 呼+エンジンの継続 | **持たない** | 行動の適用 313,879(下の内訳) |
| R25 | `revert_conversation` :2425 | run.py:1494,3494,3509 | エンジン(会話の管理) | 持たない | 未計測 |
| R26 | `set_conversing` :2441 | run.py:1488,3469 | 招いた呼 | 持たない | 未計測(会話の開始 205 の近く・推測) |
| R27 | `restock` :2634 | goods_flow.py:264 | 過程 `shelf_stock_restock` | 渡せる | 43 |
| R28 | `discard_to_bin` :2664 | goods_flow.py:465 | 過程 `waste_collection` | 渡せる | 1,543 |
| R29 | `consume` :2693 | goods_flow.py:485 | 過程(世帯の消費) | 渡せる | 未計測 |
| R30 | `collect_waste` :2720 | goods_flow.py:506 | 過程 `waste_collection` | 渡せる | 1,543 |
| R31 | `set_thermal` :2732 | environment.py:256,266 | 過程 `weather` | 渡せる | 288 回(全員を一括) |
| R32 | `set_notice_state` :2744 | salient.py:414 | 過程(顕著行為) | 渡せる | 0(事象 0) |
| R33 | `set_open_flags` :2770 | opening.py:208 | 過程 `store_opening`(代わりの規則) | 渡せる | 未計測 |
| R34 | `request_open_close` :3057 | opening.py:195 | 店員の行為(エンジンの役割の行為) | 渡せる | 未計測 |
| R35 | `place_at_external` :2788 | presence.py:1133,1150・runner.py:307 | 予定(退出)/境界 | 不要 | 未計測(退出 4,271 の近く・推測) |
| R36 | `rail_arrive` :2809 | presence.py:1147,1269・rail.py:640・civic.py:477 | 過程 rail/予定(到着) | 渡せる | 未計測 |
| R37 | `rail_depart` :2827 | presence.py:1332,1352,1357・rail.py:655・civic.py:497 | 過程 rail/予定 | 渡せる | 未計測(乗って出た 3,409 を含む) |
| R38 | `sync_transit_activity` :2843 | rail.py:682 | 過程 rail | 渡せる | 毎 tick 一括 |
| R39 | `release_indoor` :2857 | presence.py:1319・crowd.py:233 | 予定(退出)/過程 crowd | 渡せる | 409(退去による)+未計測(crowd) |
| R40 | `begin_exit_walk` :2968 | presence.py:1355 | 予定(退出の歩行の腕) | 不要 | 0(既定は immediate) |
| R41 | `clear_board_intent` :3031 | presence.py:1441 | 予定 | 不要 | 未計測 |
| R42 | `balk_queue` :3042 | presence.py:1323・crowd.py:245 | 予定/過程 crowd | 渡せる | 2(退出の並び離れ)+未計測(crowd) |

R24 `apply` の中の行動ごとの処理(1 日の適用の件数・`action_usage`): エンジンの継続(`_apply_engine_step` :1542)243,261・移動(`_apply_move` :1641)9,639・乗車(`_apply_board` :1883・乗れたのは 3,409)5,910・購入(`_apply_buy` :2154)5,029・食事(`_apply_eat` :2289・成立 4,497)5,153・会話(`_apply_talk` :2491)4,915・退去(`_apply_leave` :2521)5,892・通報(`_apply_report` :2562)5,817・手伝い(`_apply_help` :2586)5,787・断る 5,823・就寝(`_apply_sleep` :2601)5,669・並ぶ(`_apply_queue` :2384)5,034・なし 5,950。並びと乗車の待ちの順番が来たときの処理(`_serve_poi_queue` :2883・`_serve_board_queue` :1979)は「エンジンの継続」で、元の呼は並んだときの呼になる。

**(C) 既に原因を持つ記録(2 本)**: ActualLog(過程の id を i4 で持つ・`actual_log.py:67-71`・1 日 29,032 行)とテープの calls(call_id の文字列・69,978 行)。欄を足す必要は無い。テープの行番号が `cause_ref` の参照先になる。

### 3-3 1 日のバイトの見積り

5 B/行(`cause_kind` u1+`cause_ref` u4)で、列のまま・圧縮前。39 万体は 5,000 体の件数 × 78.01 の線形の外挿(推測)。R-72 の 9 B の案も並べた。

| 範囲 | 件数/日(5,000 体) | 5 B: 5,000 体 | 5 B: 39 万体 | 9 B: 39 万体 |
|---|---|---|---|---|
| (A) 既に行があるログ(金 20,362+物 8,205) | 28,567 | 143 KB | 11.1 MB | 20.1 MB |
| (B-最小) 行為と取引だけ: LLM の応答の適用 69,978・会話の開閉 410・意図 394・乗車 3,409・退出 4,271・範囲外の食事 7,785・予定の就寝と起床 842 | 87,089 | 435 KB | 34.0 MB | 61.1 MB |
| (B-最大) 最小+エンジンの継続の 1 歩 243,261・体の閾値越え 102,020・活動の設定 70,163 | 502,533 | 2.51 MB | 196 MB | 353 MB |
| 記憶の腕の上乗せ(記憶 75,448・店の記憶 30,999・関係辺 525) | 106,972 | 535 KB | 41.7 MB | 75.1 MB |

- (B) の欄のバイトは**欄だけ**の値で、出来事の行そのもの(体・時刻・種類・値など)は 指示書 10-03 §6 ① の別の見積り(R-72 §7-5)に入る。
- mock の呼数は 14.0 呼/体/日で、c7-day-4 の実テープ(6.94 呼/体/日)の約 2 倍。呼に由来する行(B-最小の大半)は実 LLM では半分程度になる見込み(推測)。
- 圧縮後の増分は測っていない(空欄)。同じ呼の続きは同じ `cause_ref` が並ぶので、列ごとの zstd ではよく縮むと見込む(推測)。
- 別の置き方(未リサーチ): ログではなく SoA に「最後に書いた原因」を 1 列(5 B/体・39 万体で 1.95 MB の状態)持たせる案もある。履歴は残らないが、状態のスナップショットと一緒に見られる。

### 3-4 ついでに見つけたこと(直していない)

- 金の台帳の生ログは、宣言 3.0 行/体/日(`economy/ledger.py:40` 付近の宣言・リングの容量は `raw_capacity_for`=3.0 × N × 保持日数・下限 16,384 行)に対して、5,000 体 mock 1 日の実測は 20,362 行=**4.07 行/体/日**だった。容量 16,384 行を超え、最初の 3,978 行が落ちた(`money_ledger.dropped`)。落ちたのは日の最初の行=初期の注入(E3・E4)と推測している(確かめていない)。39 万体でも 3.0 × N で切ると同じことが起きる見込み。原因の欄の見積りの (A) は落ちる前の追記の総数で数えた。
- 運賃は科目「持ち出し」(世帯 → 外界)として記録されている(`rail.py:587-598`)。原因の欄で「運賃」と「持ち出し」を分けたいなら、科目ではなく `cause_ref`(過程 rail)で分かれる。

## 4. 10b のテストの一覧(答えの分かっている場面)

形は実行役の自前の構成(未リサーチ)。既知の答えは HEAD の値。

| # | テスト | 既知の答え | 失敗のときに捕まえるもの |
|---|---|---|---|
| T1 | **死蔵の列の削除で呼数と行動の件数が動かない**: Q9 の 3 列と A4 の 2 列を消す前後で、既定 15 腕+classical+記憶と関係の腕の `llm_calls`・`calls_by_condition`・`action_usage`・`diagnostics` の合計・各呼の `prompt_hash` の列を比べる | 例: v3 既定 5,000 体で 69,978 呼・行動の適用 313,879(本書 §3-2)。記憶の腕で 72,930 呼 | 死蔵と思った列に読み手があった |
| T2 | **behavior-hash を既定にしても final が HEAD と一致する手順の固定**: (i) 10b では final は今の定義のままで HEAD と一致(v3 既定 `993276d5e5bb5cbe`・golden 13 値) (ii) 10b で記録した behavior-hash の値が、10e で列を消して既定を切り替えた後の final と一致 (iii) `state_hash(exclude=S)` と「S を宣言から消した state_hash()」が一致する性質を固定(本書 §2-3 の (a)〜(d)) | §2-3 の表(4 項目とも期待どおり) | 見出しに列の数を足すなどの変更で 10e の手順が壊れる |
| T3 | **追加 C の AST 検査がわざと列を落としたときに失敗する**: (i) 表から `hunger`(読み手 14)を behavior=False にすると失敗 (ii) 名前の表 `INTERO_VARS` 経由の列(`fatigue`)を False にしても失敗(名前の表の解決が効いている) (iii) 一時の source に `r.fail_streak[a] > 3` を足すと失敗 (iv) 解決できない `field(変数)` を足すと失敗 (v) 今の表では通る | (v) は §2-4 の全体の走査の結果(誤検出 2 列は許す一覧に入れる前提) | 検査が配線されていない・範囲が `engine/` だけ |
| T4 | **full-hash が外の状態の変更を検出する**: `to_state` を持つ各オブジェクトについて、軸 2 が「要る」の値を 1 要素だけ変えると full-hash が動く。軸 1 が「入れる」の行だけ behavior-hash も動く。「捨ててよい」の行(診断の計数)を変えても両方とも動かない | 例: `ConversationManager._refusal_until`・`Arbiter._pool`・`RelationLayer._acq_until` で動く。`WomExtractor.stats` で動かない | 外の状態の書き出し漏れ・full-hash の範囲の誤り |
| T5 | **揺らし試験(追加 C・棚卸し 表 7 の形)**: 軸 1 が「入れない」の列をランの途中で乱数と端の値で揺らしても behavior-hash・呼数・行動の件数・prompt_hash が変わらない。陽性対照に `hunger` を揺らすと変わる。`weight_kg` は初期化だけで読まれるので陽性対照に使わない(§1-6) | 合成 200 体 × 240 tick と実資産 1,000 体 × 1 日 | 分類の誤り(静的に追い切れない読み) |
| T6 | **構成によらない表**: 構成を変えても behavior の列の集合が変わらない(A2 (b))。`age`・`sex` は v1 空腹の構成でも behavior に入っている | `age`・`sex`・`talk_partner`・`weight_kg`・`sm_last`・`mem_last` が常に入る | 腕を足したときの分類の揺れ |
| T7 | **ハッシュの費用の予算**: 既定 5,000 体の 4 回の checkpoint が、behavior と full の両方を計算しても宣言の上限の中 | 今は 5.4 ms(1 本だけ) | 外の状態の直列化が重すぎる |

## 5. 限界

- 件数は 1 seed・1 日・5,000 体・mock だけ。39 万体は線形の外挿で、同席に由来する行(会話・関係辺)は体数に比例しない可能性がある(R-72 §7-5 の注意と同じ)。
- 件数が「未計測」の口が 21 ある(§3-2。うち 2 口は一部だけ数えた)。書き口にカウンタを挿せば数えられるが、今回は挿していない(指示どおり)。
- AST の検査は静的なので、配列を関数に渡した先の読み・描画の文字列の組み立ての中の読みは追い切れない。手読みの「読み手」の欄も代表の場所で、全部の読み手を列挙してはいない。
- 外の状態の大きさ(full-hash の費用)は配列の分だけ推計した。会話の管理と保留の応答は直列化の形が決まっていないので測れない。
- 知覚 SoA を behavior-hash に入れるか(問 5)で、10e の張り替えの範囲が変わる。
