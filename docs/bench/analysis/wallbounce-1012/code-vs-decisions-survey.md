# 指示書 10-12 と今のコードの食い違い・依存関係の調べ(実装の計画の材料)

- 作成 2026-10-12・調査役サブ(Opus 5.5)・**親の検収前**。src・tests・資産は読んだだけで 1 文字も変えていない(テストは collect だけ)。
- 対象: [指示書 10-12](../../../design/v2-wallbounce-decisions-2026-10-12.md)(以下「本書」)の §0-3 の土台 8 つ・§1-3〜1-5・§4-1〜4-11。コードは作業ブランチ `build/spatial-d102-prep` の HEAD(`f08444e`+未コミットの文書のみ)。
- 行番号は grep/read で確かめた値。`src/shibuya/` から先の相対パスで書く(例: `engine/run.py:3589` は `src/shibuya/engine/run.py`)。10-06 の洗い出し・10b-prep の行番号を引いた所は「(10b-prep)」「(洗い出し)」と書き、今のコードで ±数行のずれを確かめた。
- 「食い違いの種類」は 3 つ: **そのまま**=決定どおりに使える / **直せば**=形は合っていて足すか直せば使える / **作り直し**=決定の最後の形と構造が合わない。判定は本調査の読み(決定ではない)。
- GPU の列: 不要 / 測るのは要(器は CPU で作れて、評価に実 LLM か判断モデルが要る)/ 要。

## 要約

1. **時計**: 1 分 tick の一斉ループ(`engine/run.py:3589-4476`・888 行)が `run_day`(`engine/run.py:1891` から約 3,000 行)の中にある。ナノ秒の型 `t_sim_ns`(int64)と事象の待ち行列 `Scheduler`(`engine/scheduler.py`)は**既にあるが run は使っていない**。tick を単位にした定数は名前で数えて約 70・`1440` の直書き 55 か所(26 ファイル)・`// 60` 30 か所・tick 値の SoA 15 列+外 7 行。T0(秒化)は byte-check で守れる量、T1(まとめ)はループ本体の作り直し。
2. **出来事の記録**: 共通の出来事ログは**無い**。あるのは ActualLog(過程・対象・tick・逸脱・遅れの 5 列)・金と物の生ログ(リング)・テープ(呼の本文)・各記憶の表。**原因の ID はどの書き口にも無い**(書き口 51=resolve 42+台帳 9・10b-prep)。CP1/CP12 は新設。
3. **権利台帳**: 無い。雇用は W16 の `org_id`・`work_cell`(母集団の表)と、店の担当を `kind=従業者` の丸振りで決める `staff_of_poi`(`engine/processes/opening.py:146-157`)に分かれ、両者はつながっていない。権限が無いと**止める**形(`engine/resolve.py:3088-3102`・役割語は待機へ落とす `engine/llm_bridge.py:683`)で、CP3(止めずに記録)と逆。
4. **記憶**: 4 つの別々の表(記憶 128・店 32・親しみ 64・関係 15)が固定の容量と追い出しを持ち、強さの式は 3 か所で同じ「分+1」の近似(`engine/memory.py:226` ほか)。「関係 50+保管」(10-03 C6)は**未実装**(今は 15・感度 5/50)。MR1・MR5・MR11 は 1 つの器への作り直し。
5. **判断の入口**: 起こす体はアービタ(不応期 11 種)が決め、LLM/mock/古典はどれも「プロンプトの文 → 2 行形の文 → パーサ → 語彙」の 1 本道。番号で返す口・候補 5 つ・連続値は**無い**。古典方策はプロンプトの文を正規表現で読み直している(`engine/classical.py:676-708`)。`Chooser.probs`(店の選択だけ)が DM の口の芽。
6. **知覚**: 描画は B0〜B6 を**直接バイト列**で作る(`perception/renderer.py:1286`・`Rendered` は文のバイト)。構造のある知覚の中身は無い。p_see × 0.49 は既定 off の腕(`perception/renderer.py:154`・`cli.py:713`)、歩きスマホの 0.46 は旗を立てる処理が無く死蔵(`perception/p_notice.py:101`)。目の向きは移動方向の 16 区分だけ・心の向きは無い(焦点の列は腕のみ)。
7. **カレンダー・経済・反実仮想**: 予定は W17(月曜の行だけ=K9 のつなぎ)を計画実行層が実行する。賃金の関数はあるが**どこからも呼ばれない**・引き出し・ATM・税・信用は無い。反実仮想の申込書・改変の入口・「T まで再生して T から実 LLM」は**無い**(腕は CLI の切替口・salt の道具・日の境目と任意の tick の状態保存はある)。
8. **試験**: 全体 3,769 件(196 ファイル)・byte-check 19 構成・golden は環境ごとの行(`tests/golden_env.py`)。T0・T1・C0・CP2 の各段の「結果不変」は、この byte-check と 2 日のランの照合でそのまま門にできる。

## 1. 時計(TM・§4-2)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| 「tick」の語を使わない・一斉の 1 分の刻みを廃止 | `engine/run.py:3589`(`for tick in range(t_begin, t_end)`)〜`:4476`。`run_day` は `engine/run.py:1891` | 1 分ごとに全段(体の更新・世界過程 18 本・在圏・知覚の前計算・応答の反映・変化検出・計画境界・アービタ・判断・Phase A〜C・会話)を順に回す。`tick` の語は src(build 除く)で 2,161 回・75 ファイル・`tick` を含む識別子 159 種。tests では 1,039 回 | 作り直し(T1 で事象の待ち行列と窓に) | 時計 | 不要 |
| TM7 時刻はナノ秒の整数 | `core/types.py:77-78`(`TICK_DTYPE`・`T_SIM_NS_DTYPE` とも int64)・`core/types.py:159`(`t_sim_ns`)・`engine/clock.py`(`SimClock`) | 型はある。ただし「**世界時刻は tick でしか進まない**」(`core/types.py:12`)で、ns は tick 内の順序専用 | 直せば | 時計 | 不要 |
| TM7 乱数は出来事の時刻と中身に結びつける | `core/rng.py:106`(`run_tick_key(day_key0, T, tick_seconds)`)・`engine/rng_audit.py`(K25) | 鍵は T(分の通し番号)。10c の counter は (T, 場所, k)。K19(4 語超えで隣の流れと重なる)は未修正=10e | 直せば | 時計 | 不要 |
| TM8 一括で秒に(60 秒で今と同じ・byte-check) | 定数: 名前に TICKS/MIN/MINUTES/MINUTE を含む時間の定数 **約 70**(例 `agents/state.py:305` `REFRACTORY_MINUTES`・`engine/arbiter.py:106` `T_MAX_TICKS`・`engine/conversation.py:84-110`・`engine/processes/crowd.py:96-98`・`engine/resolve.py:185-238`・`engine/intent.py:99`)。`1440`/`1_440` の直書き **55 か所・26 ファイル**。`// 60` **30 か所**。`minutes_per_tick` 61 参照・`tick_seconds` 246 参照 | 09-30 の棚卸し([tick-constants-inventory](../wallbounce-0930/tick-constants-inventory.md) §4)は「tick を変えると挙動が変わる定数 約 30・分=tick の軸 23 行」。名前は分で中身は tick の定数がある(`REFRACTORY_MINUTES`・`RETURN_MIN_AWAY_MIN`) | 直せば(機械的な置き換え+換算 1 行。分=tick の軸 4 種=在圏ブロック・W17 の境界・鉄道の時刻表・知覚の時計は設計の判断つき) | 時計 | 不要 |
| TM8 の意味の判断 6 件のうち 5 件は吸収 | 棚卸し #9・#12・#21・#22・#42 は決定に吸収。残る #38(5 分ごとの間引きが 4 回走る) | `engine/processes/opening.py:50` `STEP_MINUTES=5`・`engine/processes/goods_flow.py:85` `RESTOCK_STEP_MINUTES=5` など | 直せば(#38 の扱いは本書に無い=親が決めるか聞く) | 時計 | 不要 |
| tick を値に持つ状態 | SoA 15 列 int32(`refractory_until` `agents/state.py:702`・`activity_until` :628・`last_result_tick` :713・`intent_since` :607・`poi_since` :612・`queue_since` :616・`board_since` :591・`mem_tick`/`mem_last` :651/653・`fam_first`/`fam_last` :638/640・`sm_first`/`sm_last` :676/678・`rel_first`/`rel_last` :695/697)+外の 7 行(10a の記録 §2-4) | 値は T(分)。int64 にすると 1 体 60 B 増(TM 草案の算術) | 直せば | 時計・記憶の器 | 不要 |
| T1 まとめ(バッチ)の導入・幅 60 秒で結果不変 | 事象の待ち行列 `engine/scheduler.py`(`Scheduler`・`TickState`・`ordered_events`=(t_sim_ns, class_rank, blake3, id) の順)。**run は `DIAG_COLUMNS` と `DeferralQueue` しか import しない**(`engine/run.py:207`・`engine/arbiter.py:88`) | 事象の順序づけの純関数と heap はあるが未使用 | 直せば(器は流用できる・ループ側は作り直し) | 時計 | 不要 |
| TM2 考えている間も体は動く・待つのはその人の新しい判断だけ | 応答の反映 `engine/run.py:3226`(保留の組 `pending`)・`_split_due`(`engine/run.py:1867`)・`DELTA_THINK_TICKS`(`engine/run.py:269`)・`--response-delay {1,2}` | 反映を tick 単位で遅らせる。「考え中」の状態は無い | 直せば | 時計・候補の口 | 不要(換算の錨 B8 は後) |
| TM3 会話の時計(モーラ × 話す速さ・1 通ずつ) | `engine/conversation.py:84`(`MAX_TURNS=3`)・`:92`(`SILENCE_TICKS=5`)・`:94`(`MAX_SESSION_TICKS=60`)・`:225`(`ConversationManager`) | 1 ターン=1 tick・終わりはエンジンが決める(洗い出し D15) | 作り直し(T2) | 時計・出来事の記録 | 測るのは要 |
| TM5 体の変化は次に段の境目を越える時刻を予約 | `engine/resolve.py:1102`(`advance_body`・毎 tick 全員を一括で更新・30 分ごとに +1) | 全員を毎 tick 見る形 | 作り直し(T3。「全員を毎回見る版と一致」が受入) | 時計 | 不要 |
| TM9 GPU 無しの計算量の欄 | `engine/manifest_sections.py`(10f の節)・`engine/resume.py`(`environment_fields`) | 呼数・診断の行はある。判断モデルと LLM を分けた呼数・時計の種類・つなぎの台帳の数の欄は無い | 直せば | 規則の表(つなぎの台帳) | 不要 |

作業量の見立て(件数): T0 は「時間の定数 約 70+直書き 1440 の 55 か所+`// 60` 30 か所+分=tick の軸 4 種(棚卸しで 23 行)+tests の `tick` 1,039 回の一部」。T1 は `run_day` のループ本体 888 行と、その中で呼ぶ 18 本の世界過程の `step(tick)`(`engine/processes/runner.py:86` の `PROCESS_ORDER`)の呼び方の作り直し。

## 2. 出来事の記録(CP1・CP12・§4-5)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| CP1 記録は 5W1H+誰に+どれだけ(なぜ=原因の ID と本人の理由)。A〜D は毎回、E は意味のある区切り | **共通の出来事ログは見つからず**。部分: ActualLog `world/processes/actual_log.py:67-76`(subject_id・tick・process・deviation・delay_min の 23 B)・金の生ログ `economy/ledger.py:254-260`(tick・払い手・受け手・額・科目のリング)・物の配達ログ `economy/goods.py:392-396`・テープ `engine/tape.py:106`(`shibuya.tape/3`・call_id・prompt_hash・本文・`recalled_rows`)・記憶の表(本人の中) | どれも別の形・別の時刻の単位。「誰に」「どれだけ」は金と物のログだけ。本人の理由はテープの本文の中 | 作り直し(新設。既存のログは新しい記録から作る写しに) | 時計 | 不要 |
| CP12 原因は 3 種類(呼・過程・実験の条件)。書くその場で直接の原因だけ | 書き口 51(resolve の公開の書き口 42+台帳 9。表は [10b-prep §3-2](../wallbounce-1003/10b-prep.md))。**どれも call_id を受け取らない**。`IntentBatch`(`engine/commit.py:216-231`)は体・行動・対象・資源・時刻の 5 配列だけ。保留の組には 10b で call_id が入った(IMPLEMENTED #81 ④) | 原因を持つのは ActualLog(過程の id)とテープ(call_id)の 2 本だけ。10b-prep §3-1 に `cause_kind`(u1・8 種)+`cause_ref`(u4)の案(未リサーチ)がある=CP12 の 3 種類とは数が違う | 作り直し(配線 3 か所: 保留の組 → `IntentBatch` → 各書き口) | 出来事の記録 | 不要 |
| CP12 実験が世界に入る口をコードで 1 か所・ほかから書けないことを試験で強制 | **見つからず**。似た強制: 単一書き込み口(`engine/resolve.py` の外から書けない=`tests/economy/test_single_write_path.py`+`writeable=False`)・import-linter の契約 5 本(`pyproject.toml`) | 実験は CLI の切替口と `--ablate`(過程を切る)で入る | 直せば(AST 検査の仕組みは流用できる) | 出来事の記録・規則の表 | 不要 |
| CP1 A〜D は基本操作からだけ・E は物理の法則のコードからだけ(コードの検査で強制) | `engine/resolve.py` の公開関数 49(うち書き口 42)・台帳の口 `economy/ledger.py:414`(`transfer`)・`:447`・`:507`・`:516`・`:530`、`economy/goods.py:602`・`:650`・`:706`・`:730`・`:767`。呼ばれていない口 5(`move_goods` `economy/goods.py:515` ほか) | 書き口は行動ごと・過程ごとに 51 本。4 つの基本操作の形ではない | 作り直し(CP2 の段階で載せ替え) | 出来事の記録・権利台帳 | 不要 |
| manifest の節 | `engine/manifest_sections.py`(384 の道筋・設定 151)・`manifest/schema.py`(13 節) | ランの同定・設定・観測・環境。ランの種類(CP5-5)・版とハッシュ(CP10 は 10f で一部) | 直せば | — | 不要 |

## 3. 権利台帳(CP4・§4-5・§1-4)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| CP4 1 行=誰が・何に・どんな権利・いつからいつまで・相手・出どころ・原因 | **見つからず**(権利を行で持つ表は無い) | — | 作り直し(新設) | 出来事の記録・規則の表 | 不要 |
| 雇用(初期は W16) | W16 の列 `org_id`・`work_cell`・`duty_role`(`agents/population.py:86-121`)。店の担当は `staff_of_poi`=`kind=従業者` を POI 番号で丸振り(`engine/processes/opening.py:146-157`・expedient)。古典の `employed`(`engine/classical.py`)。台帳の雇用主の口座は 1 つ(`cli.py:286-288` が `n_employers` を渡さない) | 母集団の表・過程の内部・方策の内部の 3 か所に散る。`staff_of_poi` は `org_id` とつながっていない | 作り直し | 権利台帳 | 不要 |
| 営業許可(区のオープンデータ) | **見つからず**。営業時間は W7 の PlanSpec(`build/field/w7_planspec.py`・`engine/processes/opening.py:198`) | — | 作り直し | 権利台帳・規則の表 | 不要 |
| 店の賃借=区画にいること | `world/state.py:134`(`pois.cell`) | POI がセルに居るだけ。持ち主・賃借の行は無い | 直せば(初期の行を作る材料にはなる) | 権利台帳 | 不要 |
| 財布の所有 | `agents/state.py:567`(`money` int32・体の番号が持ち主)・店の `revenue`(`world/state.py:141`)・台帳の部門別の残高(`economy/ledger.py:190`) | 持ち主は配列の番号で暗に決まる | そのまま(お金の持ち主は台帳の行でなく残高でよい=推測) | — | 不要 |
| 住まい | W16 `home_cell`・`home_building`(`agents/population.py:86`)・ホテルの寝床 `engine/processes/civic.py:334`(`has_bed`) | 属性の列 | 直せば | 権利台帳 | 不要 |
| CP3 権利に反する行動は止めず記録 | 開閉店の権限 `engine/resolve.py:3058-3104`(権限なしは `NO_PERMISSION` で効果なし)・補充の権限 `engine/processes/goods_flow.py:189`(`has_permission`)・役割語は「待機+権限検査待ち」に落とす `engine/llm_bridge.py:73`・`:683` | **止める**形 | 作り直し(記録して事後の反応へ) | 権利台帳・出来事の記録 | 不要 |
| PlanSpec の改訂権者 | `world/processes/records.py:381`(`revising_authority`・自由文) | 「指揮の権限」に当たる唯一の欄。自由文で照合は文字列一致(`records.py:451-458`) | 直せば | 規則の表・権利台帳 | 不要 |

## 4. 記憶の器(MR・§4-6)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| MR1 時刻は秒・+1 をやめる・最短の符号化時間・τ を較正 | 強さの式 `engine/memory.py:226`・`engine/store_memory.py:337`・`engine/relations.py:211`(いずれも `ln(n/(1−d)) − d·ln(L+1)`・L は分)。親しみ `engine/familiarity.py:91`(d=0.5) | 3 か所で同じ近似を別々に持つ。単位は分(`× 分/tick`) | 作り直し(共通の式 1 つ) | 時計・記憶の器 | 不要(τ の較正の照合は複数日ランの後) |
| MR5 人も記憶の一つ・関係の表 50 と保管をやめる・店 32/出来事 128 の上限をなくす | 記憶 `engine/memory.py:110`(`MEMORY_N=128`・追い出し `:527-532`)・店 `engine/store_memory.py:86`(`STORE_MEMORY_N=32`・追い出し `:298`)・親しみ `engine/familiarity.py:88`(64)・関係 `engine/relations.py:112`(`REL_K=15`・感度 5/50)。会話の要旨 `engine/memory.py:119-120`(16 件 × 40 字) | **4 つの固定の表**(SoA の 2 次元列 `agents/state.py:636-699`)。各表が自前の容量と追い出しと式を持つ。10-03 C6 の「関係 50+保管」は**実装されていない**(今は 15) | 作り直し(共有ログ+一人ずつの目印・注釈・強さ) | 出来事の記録・時計 | 不要 |
| MR11 記憶の行は出来事ログへの目印だけ | 記憶の行は中身を自分で持つ(`MEMORY_FIELDS` `agents/state.py:374`=種類・時刻・セル・相手・物・結果・重要度・回数) | 目印の先(共有の出来事ログ)が無い | 作り直し | 出来事の記録 | 不要 |
| MR16 System 1 と判断モデルが使った親しみまで録画 | テープ版 3 の `recalled_rows`(`engine/tape.py:36`・B5 に載せた記憶の行番号だけ)。テープ版 4(K1)は 10e に束ねる予定で未実装 | 親しみ・店の記憶・関係の強さは録画されない | 直せば | 出来事の記録・記憶の器 | 不要 |
| MR6 気づいたときを 1 回触れたと数える・同席で書くのは人の記憶だけ | 同席の辺 `engine/relations.py:944`(`copresent_step`・2 m・5 分の同席で辺を書く)・露出のカウンタ `engine/familiarity.py`(セルに入った回 × 看板) | 気づき(注意)ではなく距離と時間の規則で数える | 作り直し | 知覚の分離・記憶の器 | 不要 |
| MR2 手がかりは ID の一致を既定・埋め込みは腕 | 想起 `engine/memory.py:324`(`recall`)・score の重み `:115-116`(w_v=0=埋め込み無し) | ID 一致の形は既にある | そのまま(器を移せば使える) | 記憶の器 | 不要(Ruri-v3 の腕は CPU) |
| MR3・MR13 寝たときに印象を書き直す・昼の結論はその場で意味の記憶へ | 日次の内省は 0 回(本番で発火しない・設計の穴として記録済み) | 無い | 作り直し(新設) | 記憶の器・候補の口 | 要 |

## 5. 候補の口・判断モデル(DM・C-2・§4-7・§4-12)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| DM8 変化の検出+カレンダーの時刻を入口に | 起こす体: アービタ `engine/arbiter.py:293`(`arbitrate`)・`:507`・不応期 `agents/state.py:305-317`(11 種・ほぼ expedient)・変化検出 `engine/change_detect.py:245`・呼枠 `engine/arbiter.py:136` | 起床条件 11 種 × 不応期 × 4 クラスの繰り延べで「誰に LLM を呼ぶか」をエンジンが決める | 作り直し(判断モデルが LLM を呼ぶかを決める形へ) | 候補の口・時計 | 不要(器)/要(実測) |
| DM-0 候補は 5 つの源(経験・周りのできること・近い予定・続ける・よく考える) | `engine/chooser.py:115`(`NearestChooser`)・`ClassicalChooser`・`Chooser.probs(candidates, context)`。候補は**店(POI)だけ**で、作るのは `engine/poi_target.py`(可視の店) | 店選び 1 種類の口 | 直せば(口の形は流用できる。候補の源は新設) | 候補の口・記憶の器・知覚の分離・カレンダー | 不要(器) |
| C-2 番号で返す口を判断モデルと LLM で共通に 1 つ | `llm/__init__.py:140-192`(`LLMRequest.prompt` の文・`LLMResponse.text`)→ パーサ `llm/parser.py`(2 行形・882 行)→ 語彙 `llm/contract.py:593`(v1/v2/v3)→ 未定義の 5 段 `llm/undefined.py` | 自由な文を語彙へ写す 1 本道。番号で返す口は**見つからず** | 作り直し | 候補の口 | 不要(器)/要(偏りの試験) |
| 判断の代役 | mock `llm/mock.py:113`(一様な乱数)・古典 `engine/classical.py:305`(`ClassicalPolicy` は `LLMClient` として文を書く。近接の人は**プロンプトの文を正規表現で読み直す** `engine/classical.py:676-708`) | 古典も文を経由する | 作り直し(候補の口の別実装として並べる=DM6) | 候補の口・知覚の分離 | 不要 |
| DM4 短い版と長い版を 1 つの仕組みで・共通部分を前に | 描画 `perception/renderer.py:1286`(B0〜B6・群の予算 `perception/templates.py:160`・版 `:130` v1.4) | 長い版 1 つだけ。人物像は種別の語だけ(`perception/renderer.py:1397-1406`)・persona の文を読むコードは src に 0(`perception/templates.py:26` の注記だけ) | 作り直し(知覚の中身から 2 つの描き方) | 知覚の分離 | 測るのは要 |
| DM13 行動の細かい数値は連続値 | 「まで」の分 `llm/contract.py:1163-1165`(既定 60・上限 480)・活動の持続の既定 `engine/activity.py` | 離散の語と分の整数 | 作り直し | 候補の口 | 不要 |
| DM5 驚き 0〜5・迷い(1 位と 2 位の差+エントロピー) | エントロピー `engine/chooser.py`(`entropy_bits`) | 店選びの分布のエントロピーだけ | 直せば | 候補の口 | 不要(器) |
| 熟考の形(1 ランで LLM 固定・思考モードの切替) | 艦隊 `llm/fleet.py:760`(`FleetClient`)・`max_tokens_for` `:232`・出力 o64 既定 | 1 段の LLM・思考モードの欄は無い | 直せば | 候補の口 | 要 |
| 時刻の 5 分丸め | `perception/normalize.py:77`(`TIME_ROUND_MINUTES=5`)・`:132-135`(`format_time`)・使う所 `perception/renderer.py:1685` | B3 の時刻は 5 分丸め | 直せば(TM8 の「時計を見れば分単位」へ) | 時計・知覚の分離 | 不要 |

## 6. 規則の表・道具の台帳・つなぎの台帳(§1-12・CT0・§0-3 の 3)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| 法と制度は「出典と版つきの規則の表」(機械が守らせるもの/人が知っていて取り締まるもの) | `world/processes/records.py:365`(`PlanSpec`: 内容・有効期間・版+`transaction_tick`・改訂権者・規範の種類・違反の可否・公示範囲・遵守率の欄)・登録簿 `world/processes/registry.py:101`(`WorldRegistry`)・宣言 `world/processes/first_batch.py` | 型と登録の口はある。中身は営業時間(W7)など世界過程の計画だけ。税・社会保険・信用・条例の行は無い | 直せば(CP4 は PlanSpec を参照と決定済み) | 規則の表 | 不要 |
| つなぎを台帳に載せ、外す段を書く | 過程のフォールバック台帳 `world/processes/registry.py:265`(`fallback_ledger`=conf・被覆・返済期限)・`world/processes/relations.py:242`(`FallbackRow`)・expedient の判定 `tools/c8/expedient_triage_v1.json`・感度 `tools/c8/sensitivity_v1.json`・腕 `tools/c8/ablations_v1.json`。計画実行層の E1〜E9 は docstring だけ(`engine/presence.py:24-41`) | 世界過程のつなぎだけが行を持つ。カレンダー(K9・出勤率・W17 の就寝)・会話の終わり・不応期などのつなぎは**台帳の行が無い** | 直せば(行の型を広げる) | 規則の表 | 不要 |
| CT0 道具の台帳(知っている/知らない/要るもの/体と知覚への影響/誰が持つか/中身を書くのは誰か) | **見つからず**(src に道具・連絡先・メッセージの語は無い。`message` の当たりはログの文言だけ) | — | 作り直し(新設) | 出来事の記録・権利台帳・知覚の分離 | 不要(器 C0) |
| CP8 の代わり「世界の部品を足した記録の台帳」 | **見つからず**。近いもの: 未定義行動の記録 `llm/undefined.py`・オフラインの裁定 `tools/vocab/adjudicate.py` | 語彙の成長の台帳(段 0〜4) | 直せば(D3 の洗練の段階の記録へ) | 出来事の記録 | 不要 |
| 状態の台帳(再開・ハッシュ) | `engine/state_ledger.py:49`(版 `state-ledger/10f`・193 行=SoA 98+外 95・behavior 119/no 41/diag 33) | 10b〜10f で完成。土台を変えるたびに行の追加が要る | そのまま(新しい土台の状態を行で足す) | — | 不要 |

## 7. 知覚(§1-13・§1-6・CT0)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| §1-13 知覚の約束の出力は構造のある事実・文章はその描き方の 1 つ | `perception/renderer.py:527`(`Rendered`=ブロック id → **バイト列**・本文・ハッシュ)・`:1397-2433`(`_b1`〜`_b6` が直接バイト列を作る)・チャネルの切り詰めはトークン数で(`perception/channels.py`)。構造を持つのは顕著行為 `perception/attention.py:150`(`SalientItem`)など一部 | 中身と描き方が分かれていない(2,596 行)。古典方策が文を読み直す(§5)のはこの結果 | 作り直し(知覚の中身の層を足し、今の描画はその描き方の 1 つに=プロンプトのバイトは不変にできる見込み・推測) | 知覚の分離 | 不要 |
| D-121 p_see × 0.49 を係数で掛けない | `perception/renderer.py:148-154`(`P_SEE_ACTIVITY_KINDS`・`P_SEE_BY_ACTIVITY` 既定は全部 1.0)・切替口 `cli.py:713-720`(`--p-see-activity`・例 `{"phone": 0.49}`)。スマホの旗は無い(`perception/renderer.py:1567`) | 0.49 は**既定 off の腕**。既定のランには入っていない | 直せば(腕を消すか検証用に回すだけ) | — | 不要 |
| 係数で持たない(§1-6) | 歩きスマホの負荷 `perception/p_notice.py:101`(`M_LOAD=(1.0, 0.46, 1.0)`)・密度 `:99`・照明 `:96-97`。`TaskLoad.PHONE`(`:122`)を立てる処理は無い(`engine/processes/salient.py:36`・`:437-441` は会話か手空きだけ) | 0.46 は死蔵の係数 | 直せば(目と心の向きから出す形へ) | 知覚の分離 | 不要 |
| 目の向き(視線の先を状態に) | `perception/state.py:98-99`(`heading` 1 B・16 区分)・書き手 `engine/processes/salient.py:427-441`(移動の向きから)・`engine/resolve.py:2745`(`set_notice_state`) | 「歩く向き」であって視線ではない。画面を見ている状態は無い | 直せば | 知覚の分離・道具の台帳 | 不要 |
| 心の向き(関心の的を状態に) | 焦点の列 `agents/state.py:527-531`(`focus_target`・`focus_ttl`)・寿命 `engine/resolve.py:202`(`FOCUS_TTL_TICKS=10`)。**腕 attention のときだけ確保**(`engine/state_ledger.py:209-210`) | UE の焦点の型(人/POI・10 分) | 直せば(既定の状態へ・関心の的の種類を広げる) | 知覚の分離・時計 | 不要 |
| 割り込めなかった出来事の載せ方 3 腕 | **見つからず** | — | 作り直し(新設) | 知覚の分離 | 測るのは要 |

## 8. カレンダー(CA・AT・§4-1・§1-3)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| CA1 W17 から写さない・W17 は旧版として凍結 | 読み口 `agents/weekly.py:196`(`WeeklySchedule`)・`:296`(`boundary_events`)・計画実行層 `engine/presence.py:581`(`PlanExecutor`・1,969 行)・`:370`(`PlanBlocks`=在圏ブロック) | W17 の行を在圏ブロックに畳み、到着・退出・就寝・起床の事象を組む | 作り直し(本人の約束+本人の判断へ。1a は影として並走) | 時計・権利台帳(雇用)・候補の口 | 不要(1a)/要(1b 以降の判断) |
| K9 月曜の行を毎日使う(つなぎ) | `engine/run.py:3339`・`:3382`(`_relay_tables` の中)・`engine/presence.py:841` | 宣言つきのつなぎ。台帳の行は無い | 直せば(つなぎの台帳へ) | 規則の表 | 不要 |
| §1-3 E4(退出の途中で別の行動を選ぶと範囲外へ消す)を外す | `engine/presence.py:30-36`(docstring)・`:87`(`EXIT_MODES`)・`:1429`(`_depart_now`)・`:1513`(`_flush_walkers`)。既定は `immediate`(予定の終わりにその場で `rail_depart`) | 既定でも体がその場で範囲外へ移る | 作り直し(体は境界を歩くか乗り物で越える) | 時計・候補の口 | 不要(器) |
| W17 による出入りと就寝(1b・疲労の後) | 就寝と起床 `engine/run.py:3816-3832`(`step_plan_boundaries`・`begin_planned_sleep`・`wake_from_plan`)・`engine/resolve.py:629`・`:754` | 予定の境界でエンジンが寝かせ、起こす | 作り直し | 候補の口・時計(TM5) | 要(判断) |
| CA5 出勤率のくじ(つなぎで残す) | `engine/presence.py:177`(`attendance_draw`)・`:813`(`_attendance_absent`)・既定 1.0(`cli` の `--attendance-rate`) | 既定 off | そのまま(つなぎの台帳へ載せる) | 規則の表 | 不要 |
| CA3 二人の約束は各自の理解・置き場所・確かさ・元の会話 | **見つからず**(予定の構造は W17 の行=開始・終了・活動・場所・対象セル・順番 `agents/weekly.py:1-20`) | — | 作り直し(新設) | 出来事の記録・道具の台帳・記憶の器 | 不要(器) |
| CA11 日付・曜日・祝日は全員が知る | 暦の口 `engine/calendar.py:244`(`SimCalendar`)・祝日 `:159`(内閣府の CSV) | 日付・曜日・祝日・給料日・営業日を返す口がある | そのまま | — | 不要 |
| AT2 時間の見積り(経験・乗換案内・推測) | **見つからず**(到着便はエンジンが「間に合う最も遅い便」を選ぶ=E1 `engine/presence.py:913` `_assign_trains`) | エンジンが逆算する(AT3 で禁止) | 作り直し | 記憶の器・道具の台帳 | 不要(器) |
| 範囲外の食事の予定 | `engine/energy.py:531`(`OutOfAreaMeals`)・使う所 `engine/run.py:3597-` | 既定の時刻に域外の体の空腹を戻す | 直せば(CA6 の本人の計画へ) | カレンダー | 不要 |

## 9. 経済(EC・CP2・§4-11)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| CP2 お金から基本操作へ(帳簿 9 口 → 行動の適用 → 残り・各段で結果不変) | 帳簿 9 口(10b-prep §3-2 の E1〜E9): `economy/ledger.py:507`・`:447`・`:516`・`:530`、`economy/goods.py:650`・`:602`・`:706`・`:730`・`:767`。部門 6・科目 15(`economy/accounts.py:59`・`:109`) | 9 口は行のログを持つ=原因の欄を足すだけで済む(10b-prep) | 直せば | 出来事の記録 | 不要 |
| 財布の初期値(EC2: 統計から) | `economy/anchors.py:179`(`WALLET_DAYS=3.0`)・`:181-184`・`:193`(`initial_wallets`=日の消費 × 3 日の対数正規)・`cli.py:208`(`household_wallets`)・入れる口 `engine/resolve.py:519-524`(外界 → 世帯の来街者持込) | 消費 3 日ぶんの財布(D11)。預金の行は台帳にあるが世帯の口座の経路は無い | 作り直し(統計からの資産) | 権利台帳(口座) | 不要 |
| EC4 給料は雇用契約に基づき給料日に・引き出しは本人・ATM は実データ | 賃金の関数 `economy/anchors.py:211`(`monthly_wage_amounts`)・`:217`(`monthly_wages`・雇用主 → 世帯の `transfer_many`)。**engine と cli から呼ばれていない**(grep で `anchors.py` の外に呼び手なし)。引き出し・ATM は見つからず | 賃金 0・引き出しの口なし=1 日 1 体 536 円ずつ減る(10-03 実測) | 作り直し(雇用契約の行 → 給料日の機械の動き) | 権利台帳・規則の表・カレンダー(給料日 `engine/calendar.py`) | 不要 |
| レジ・消費税 | 購入 `economy/ledger.py:507`(`purchase_many`)・値段 `world/state.py:139`(`pois.price`)・値段の形成 `economy/pricing.py`(engine につながっていない=洗い出し §4-6) | 税の科目 `TAX`(`economy/accounts.py:119`)は**どこからも使われない** | 直せば | 規則の表 | 不要 |
| 運賃(実際の運賃表) | `engine/processes/rail.py:138`(`FARE_YEN=180`)・`:717`(`pay_fares`・持ち出し科目で外界へ) | 一律 180 円 | 直せば | 規則の表 | 不要 |
| EC5 店の売上は客から・範囲外は外の決定として faucet | 参入資本 `economy/entry_capital.py`・`cli.py:186`。「域外売上」の科目は無い(賃金のアジェンダ W3) | — | 直せば | 規則の表 | 不要 |
| 信用(カード・ローン・総量規制) | 借入の行 `economy/accounts.py:92`(`LOAN`)・検算 `economy/checks.py:314` | 残高の行だけ。貸す側・審査・返済は無い | 作り直し(新設) | 権利台帳・規則の表 | 不要 |
| 保存則の式 | `engine/run.py:1416`(`RunResult.conserved`=Σ所持金+Σ売上+Σ運賃=初期)・終了コード `engine/run.py:5147` | 賃金が入ると必ず NG(賃金のアジェンダ §0) | 作り直し(帳簿の検算へ=W8 (A)) | — | 不要 |
| 見張り(財布と預金の分布を毎日) | センサス `economy/census.py`(日次・月次 MER) | 残差・貨幣供給量はある。分布の欄は無い | 直せば | — | 不要 |

## 10. 洗い出しの 55 件の扱い(§1-5)

[洗い出し](../wallbounce-1006/agentless-outcomes-inventory.md) の 55 行を §1-5 の 3 群と例外に振った(本調査の読み。群に迷った行は「推測」)。

| 群 | 件数 | 行 |
|---|---|---|
| ① 人の選択 → 判断モデル | **21** | C7 世帯の消費・C9 ポイ捨て・C14 電力と水・C18 席を空ける・C19 列を離れる・C20 乗車の受け入れ・C21 乗車待ちの打ち切り・C22 意図の打ち切り・C23 到着・C24 退出・C25 戻り・C26 出勤率・C27 鉄道の帰無腕の域外居住・C28 相槌と締めの一言(中身は LLM・推測)・C29 古典方策・D4 W17・D5 在圏ブロック・D6 就寝と起床・D7 範囲外の食事(推測)・D15 会話の終わり・D16 mock |
| ② 他の人の仕事 → 働く人のエージェント | **20** | C1 車の流れ・C2 騒音(本書は「車の流れと騒音」を②に置く)・C3 開閉店・C4 補充・C5 納品・C6 廃棄・C8 収集・C10 清掃・C11 宅配・C12 道路工事・C13 ホテル・C15 報道・C16 催し・C17 出動・D1 鉄道の運行・D2 鉄道の制度と車両の値(運賃は規則の表・定員は物理=推測)・D3 バス・D13 店の初期の数値(値段は②・在庫と席数は初期状態=推測)・D14 営業時間・D19 看板(作り物の印で残し実データで置き換え=§1-5 の 6) |
| ③ 体と System 1 → コードに残す | **3** | A2 体感温度(本書の③に名指し)・D8 空腹と疲れ・D9 倒れる |
| 例外(自然・人口・社会の決まり・初期状態) | **11** | 自然 A1・A3・A4/人口 B1・B2・B3・D10/社会の決まり D17/初期状態 D11 財布・D12 参入資本・D18 tick 0 の体の状態 |
| 一覧の外(①に当たる) | 2 | S1 店の選択(最寄り)`engine/poi_target.py:385`・`engine/chooser.py:115`/S2 会話の相手 `engine/commit.py:825-852` |

主要 15 件のコードの場所(ファイルの行数の多い順と効きの大きさで選んだ):

| # | 行 | 場所 | 群 | 備考 |
|---|---|---|---|---|
| 1 | C23・C24・C25・D5 | `engine/presence.py:913`(`_assign_trains`)・`:935`(`_spread_arrivals`)・`:1352`(`_do_arrive`)・`:1376`(`_do_depart`)・`:1704`(`_rearm_after_leaving`)=1,969 行 | ① | E1〜E9 の expedient を含む層全体 |
| 2 | D1・D2・C20 | `engine/processes/rail.py:734`(`step`)・`:667`(`accept_rate`)・`:138`(運賃)=891 行 | ②(C20 は①) | 乗務員 60・車掌 40・駅員 300 は母集団に居る(洗い出し §0) |
| 3 | D15・C28 | `engine/conversation.py:84-110`・`:225`=866 行 | ① | 終わりは LLM に決めさせない設計(16 行表 行7) |
| 4 | C3・D14 | `engine/processes/opening.py:198`(`step`)・`:146`(`_assign_staff`)=263 行 | ② | 6,546 件のうち代打 6,520 |
| 5 | C4・C5・C6・C7・C8・C9・C10 | `engine/processes/goods_flow.py:216`・`:364`・`:462`・`:480`・`:504`・`:583`=610 行 | ②(C7・C9 は①) | 補充の権限 `:189` |
| 6 | C13・C14・C15・C16・C17 | `engine/processes/civic.py:342`・`:432`・`:254`・`:507`・`:156`=580 行 | ②(C14 は①) | — |
| 7 | C11・C12・D3 | `engine/processes/logistics.py:135`・`:321`・`:226`=360 行 | ② | 世界の状態にもプロンプトにも出ない |
| 8 | C18・C19 | `engine/processes/crowd.py:231`(`DWELL_MAX_TICKS=30` の解除)・`:241`(`WAIT_MAX_TICKS=15`) | ① | 定数 `:96-98` |
| 9 | D6 | `engine/run.py:3816-3832`・`engine/resolve.py:629`・`:754` | ① | 疲労の後(CA9) |
| 10 | D8 | `engine/resolve.py:1102`(`advance_body`)・`engine/energy.py:321`(`EnergyModel`) | ③ | TM5 の予約の形へ |
| 11 | D9・C17 の引き金 | `engine/processes/salient.py:324`(`_collapse_events`)・`:355` | ③(出動は②) | 倒れる率の出典はリサーチ |
| 12 | C21・C22 | `engine/resolve.py:238`(`BOARD_WAIT_LIMIT_TICKS=30`)・`engine/intent.py:439`(`too_far`) | ① | — |
| 13 | C1 | `engine/processes/traffic.py:111`・`:141`=173 行 | ② | 計算した台数を読む処理は無い |
| 14 | D16・C29 | `llm/mock.py:113`・`engine/classical.py:305` | ① | 判断モデルの基準として残す(DM6) |
| 15 | C26 | `engine/presence.py:177`・`:813` | ① | つなぎとして残す(CA5) |

## 11. 反実仮想の器(CP5・§4-5)

| 決定 | 今のコードの場所 | 今の形 | 種類 | 依存する土台 | GPU |
|---|---|---|---|---|---|
| CP5-4 申込書(種類・対象・中身・始まり・終わり・告知・問い・比べる指標) | **見つからず**。今の「腕」は CLI の引数の JSON(`tools/c7/salt_runs.py:222` `--arms`)・過程を切る `--ablate` | 腕は設定の差。「決定」を世界に入れる形ではない | 作り直し(新設) | 出来事の記録(CP12 の入口)・規則の表 | 不要 |
| CP6 実験が入れるのは「決定」だけ・実行は世界の中の人 | **見つからず** | — | 作り直し | 出来事の記録・権利台帳・候補の口(実行する人)・道具の台帳(告知が届く) | 要(実行は人の判断) |
| CP5-2 日の境目の状態+T まではテープを再生・T から実 LLM | 状態の保存 `engine/resume.py`(日の終わりと任意の tick・npz+json `engine/state_codec.py`)・再開の口(`--resume-from`・`--stop-at-tick`)。再生 `engine/llm_bridge.py:472-527`(`mode` は `record`/`replay` の 2 つだけ) | 「T まで再生して T から実 LLM」の切り替えは**無い**。テープ外は空応答で数える | 直せば(ブリッジに切り替えの時刻を足す) | 時計・出来事の記録 | 不要(器)/要(T からの実 LLM) |
| T までの一致を共通乱数の確認で毎回確かめる(R-71 の 4 つ) | `tools/c7/salt_runs.py`(A/A `--aa` `:235`・`--T0` `:234`・最初の食い違いの 2 段探索 `:93`・`:100`)・`tools/c7/salt_compare.py`(CRN の健全性 ok/fail/未検査) | 道具はある | そのまま | — | 不要 |
| 複数ラン(初期状態 × モデル × 偶然) | seed の 3 分割(`--population-seed`・`--environment-seed`・動き=IMPLEMENTED #85) | 初期状態の揺らし(ヒストリーマッチングで世界を何通りか作る)は無い | 直せば | — | 不要 |
| 探索と確認(アンサンブルの半分を封印) | 封印は holdout 3 層(W19)と事前登録 `docs/bench/c7/prereg_arms_v1.md` | アンサンブルを半分に分けて封印する仕組みは無い | 直せば | — | 不要 |
| CP14 予測の封印とハッシュ | **見つからず** | — | 作り直し(新設) | — | 不要 |
| 録画(テープ) | `engine/tape.py:106`(版 3)。版 4(鍵に日・記憶の同定・出どころの欄・B5/B6 の本文)は 10e の予定 | 呼の本文と結果の照合 | 直せば | 出来事の記録 | 不要 |

## 12. 既存の試験と、結果不変を守る門

| 項目 | 場所 | 値 |
|---|---|---|
| 全体のテスト | `tests/`(`.venv` の python で `pytest --collect-only -q tests` を数えた) | **3,769 件・196 ファイル**(engine 1,402・llm 344・perception 299・build_sched 229・c8 185・c7 168 ほか)=IMPLEMENTED #86 の件数と一致 |
| byte-check | 道具 `docs/bench/analysis/wallbounce-1003/10b/byte_check_10b.py`・`10c/byte_check_10c.py`・`docs/bench/analysis/wave2-2026-09-30/wave2_bytecheck.py`。最新の結果 `docs/bench/analysis/wallbounce-1006/10f/byte_check_stage3_fix.json` | **19 構成**(W6 の 15 腕+店の記憶・関係・古典・古典+記憶+関係・mock/classical 5,000 体・seed 1・1 日)。比べるのは final・呼数・blocks・calls の 14 列 |
| 2 日のラン | `docs/bench/analysis/wallbounce-1006/10f/two_day_check_stage3_fix.json` | final `47e0a85b02797e23`・142,043 呼(10f 第 3 段) |
| golden | `tests/golden_env.py`(環境 `platform_id` ごとの行・未登録の環境は A/A)・`tests/engine/test_presence_executor.py:107`(`W17_GOLDEN`)・`tests/engine/test_presence_derive_v2.py:61`(`REAL_GOLDEN`)・`tests/engine/test_relations_tenure.py:177`(`REL_ON_5000_GOLDEN`)・`tests/perception/test_near_tiebreak.py:164`(`CLASSICAL_1500_GOLDEN`)・`tests/perception/test_renderer_golden.py`(描画のバイト) | 10e で張り替える予定の 13 値(D-102 のアジェンダ §5) |
| 再開と状態 | `tests/engine/test_resume_10d.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/discard_probe.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_determinism_t1_t2_t4.py` | `resume == straight`・捨てて同じか・2 日目の鍵 |
| 書き込み口の強制 | `tests/economy/test_single_write_path.py`・import-linter の契約 5 本(`pyproject.toml`) | CP1/CP12 の AST 検査の下地 |

各段の門の対応(本調査の読み):

| 段 | 使える門 | 足りないもの |
|---|---|---|
| T0(秒化) | byte-check 19 構成+2 日のラン+golden | 「秒の定数 → tick の換算」の性質の試験(tick_seconds=60 で今の整数と一致) |
| T1(まとめ幅 60 秒で不変) | 同上+`test_resume_10d`(日の途中の 3 点) | まとめ無しの時刻順を正解にする収束の試験(TM4)は新設 |
| C0(道具の器) | byte-check 19 構成 | 道具の台帳の行の試験は新設 |
| CP2 の各段(帳簿 9 口 → apply → 残り) | byte-check 19 構成(呼数・行動の件数・final)+金と物の検算 `economy/checks.py` | 原因の欄が全行で埋まることの試験・ミューテーション試験(CP11)は新設 |
| 出来事の記録・権利台帳・知覚の分離(どれも既定不変で入れる前提) | byte-check+`test_renderer_golden`(描画のバイト)+状態台帳の AST 検査(新しい状態の行) | 新しいログが観測だけで世界を変えないことの試験(状態の書き出しの有無で manifest が動かない=`engine/run.py:3461` の注と同じ形) |

## 依存関係の案(親が計画を作る材料・決定ではない)

### 土台 8 つの間の依存

| 土台 | 先に要るもの | これに乗るもの |
|---|---|---|
| ① 時計(TM7 型・TM8 秒化=T0) | 10e(K19 の重なり・テープ版 4 は鍵の形が同じ所を触る) | ほぼ全部(記録の時刻・記憶の秒・予定の時刻) |
| ② 出来事の記録(CP1・CP12) | ①(時刻の型) | ③④⑦・CP2・CP5・CA3・MR11・CT9 |
| ⑥ 規則の表(PlanSpec の拡張・つなぎの台帳) | ②(改訂を外の決定として記録・推測) | ③・EC の税と天引き・運賃・CP5 の L1 の改変 |
| ③ 権利台帳(CP4) | ②(原因の欄)・⑥(条件の中身は PlanSpec を参照) | EC4 の賃金・CP3 の「許可のない行動」・開閉店の担当・CA1 の勤務・CT の持ち物 |
| ④ 記憶の器(共有ログ+目印) | ②(目印の先)・①(秒) | MR M0〜・DM-0 の候補 1(経験)・CT5 の連絡先・AT2 の見積り |
| ⑧ 知覚の中身と描き方の分離 | 構造上は無し(描画のバイト不変が門) | ⑤(短い版と長い版)・CT0 の目と心の向き・MR6・古典方策の文の読み直しの解消 |
| ⑦ 道具の台帳(CT0) | ②・③(誰が持つか)・⑧(道具が返す知覚) | C0〜C6・CA3 の置き場所・AT1 の思い出し方 |
| ⑤ 候補の口(DM-0・C-2) | ⑧・④・カレンダー(近い予定)・⑦(道具も候補)。ただし口の形と記録の欄は mock で先に作れる(DM の J0) | DM の J1〜J4・55 件の①群・CA 1b 以降・TM の T3(驚き駆動) |

推測の順(GPU 不要の土台を先に): **10e →(①T0 と ⑧ を並べて・どちらも既定不変)→ ② → ⑥ → ③ → ④ → ⑦ → ⑤ の口(J0)**。①T1 は ② の後に入れると、まとめの導入と記録の時刻の付け方を 1 回で決められる(推測)。

### 各ラウンドの段がどの土台に乗るか

| 段 | 乗る土台 | 既定 | GPU |
|---|---|---|---|
| TM T0 | ① | 不変 | 不要 |
| TM T1 | ①・② | 不変 | 不要 |
| TM T2(会話の時計) | ①・②・⑤ | 動く(版上げ) | 測るのは要 |
| TM T3(何かあった人だけ・驚き駆動) | ①・⑤・カレンダー 1b | 動く | 要(判断モデル) |
| TM T4(場所ごとの時計) | ①・T1〜T3 | 一致が条件 | 一致の確認は不要・速さの実測は要 |
| カレンダー 1a 影 | ①・③(雇用)・規則の表(K9 のつなぎ) | 不変 | 不要 |
| カレンダー 1b 出入り | 1a・⑤・T3 | 動く | 要 |
| カレンダー 2(C1 と束ねる) | ②・④・⑦ | 動く | 要 |
| カレンダー 3 雇い主・祝日 | ③・⑥・CT C3 | 動く | 要 |
| CT C0 器 | ②・③・⑦・⑧ | 不変 | 不要 |
| CT C1〜C6 | C0・⑤・TM T2 | 動く | 要 |
| CP2 の段階(9 口 → apply → 残り) | ② | 各段で不変 | 不要 |
| CP4 権利台帳の中身 | ③・⑥ | 台帳は早めに・権利を変える行動は経済の段で | 不要 |
| CP5 申込書・入口・T からの実 LLM | ②・⑥・tape 版 4 | 腕 | 器は不要・実験は要 |
| MR M0〜M5(中身は本書・草案とも見つからず=下の「見つからなかったもの」) | ①・②・④ | M0 は最初の版上げと一緒・残りは腕で入れて 1 回で既定 | M0 不要・印象と固定は要 |
| DM J0(口と記録と評価の器) | ⑤・⑧ | 不変 | 不要 |
| DM J1〜J4(本命の選定・較正・置き換え) | J0 | J3 から動く | 要(判断モデルの実測・LoRA は DM3) |
| PS(ペルソナの作り直し) | 規則の表(検証専用の一覧 §5) | 動く(母集団) | 不要(構築)・測るのは要 |
| EC1〜EC6 | ②・③・⑥・暦の口 | 動く | 不要 |
| 55 件の①群 | ⑤・カレンダー・TM T3 | 動く | 要 |
| 55 件の②群 | ③(雇用)・⑤・CT C3・カレンダー 3 | 動く | 要 |
| 55 件の③群 | ①(TM5 の予約)・⑧ | 動く(T3) | 不要 |

GPU が要るもの: 判断モデルの実測と本命の選定(DM1)・LoRA(DM3)・実 LLM の段(カレンダー 1b 以降・TM T2 の測定・CT C1〜C6・MR の印象と固定・熟考の形)・反実仮想の T からの実 LLM・T4 の速さの実測。要らないもの: 土台 8 つの器・10e・T0・T1・T4 の一致の確認・カレンダー 1a・C0・CP1/CP2/CP4/CP12・M0・DM J0・EC・10g の mock。

## 見つからなかったもの

- 共通の出来事ログ・原因の ID の欄(§2)。実験の入口の 1 か所・申込書・予測の封印(§2・§11)。
- 権利を行で持つ台帳・営業許可・賃借・雇用契約の行(§3)。
- 道具・連絡先・メッセージ・電話のコード(§6・§7)。src に該当する語は無い。
- 番号で返す共通の口・候補 5 つの源・連続値の行動の数値(§5)。persona の文を読むコード(src で 0)。
- 構造のある知覚の中身の層・スマホを見ている状態・割り込めなかった出来事の載せ方の腕(§7)。
- 二人の約束の構造(置き場所・確かさ・元の会話)・時間の見積り(§8)。
- 賃金の呼び手・引き出し・ATM・税の取引・信用(§9)。
- 「T までテープを再生して T から実 LLM」の切り替え(§11)。
- **MR M0〜M5 の段の中身**: 本書 §4-6 MR10 は「段を M0〜M5 に組み直す・M0 は最初の版上げと一緒」とだけ書き、記憶の草案(`docs/design/v2-memory-rework-design-round-draft.md:270-285`)は R0〜R7 のまま。M0〜M5 の中身は本調査で読んだ文書には無い(経緯の控えは指示どおり読んでいない)。
- **TM8 の意味の判断の残り 1 件**: 6 件のうち本書が吸収を書いたのは 5 件(会話 1 ターン・応答 +2・招待の返事待ち・停車時間・1 ノード/刻み)。棚卸しの #38(5 分ごとの間引き)の扱いは本書に無い。
- **「関係の表 50+保管」**: 本書 MR5 が「やめる」とした 10-03 C6 の形は、今のコードには入っていない(関係は 15 辺・`engine/relations.py:112`)。やめる対象は文書の決定だけで、コードの撤去は無い。
- 実装の計画のファイル `docs/design/v2-implementation-plan-2026-10-12.md` は PENDING から引かれているが、まだ無い(親がこれから作るものと読んだ)。
