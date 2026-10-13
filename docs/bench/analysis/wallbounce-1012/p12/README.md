# 第 1 期 1-2 知覚の分離(§1-13・B0〜B6 の構造化)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `1-2/percept`(HEAD `136fdbb`=T0 と 1-3 を取り込んだ後)。commit は親。
- 正: [口の約束 1-2](../../../../design/v2-foundation-contracts-2026-10-13.md)・[計画 1-2](../../../../design/v2-implementation-plan-2026-10-12.md)・[決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §1-13・§1-6・§4-4 CT2・[回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §4-2・§0-3・§3。先例は [R-113](../../../../research/v2-r113-e1-foundations-existing-implementations.md) §6(UE の `FAIStimulus`=誰が・どこで・どの感覚で、の欄の形だけ・強さの係数は持たない/SOTOPIA=共有の記録 → 見る人ごとの絞り込み → 文の 3 段・MIT)。借りたのは形だけで、コードは写していない。
- 数は実測。生の出力(テープ・side の JSON)は git の外の作業用の置き場(作業木の `_bc/`)に置いた。比べた結果と道具だけをこのフォルダに置く(道具は `tools/`・絶対パスなし)。
- 道具(`tools/`・使い方は各ファイルの冒頭): `coef_patch_head_copy.py`(係数を 1.0 にした HEAD の写しを作る=最初の計測)・`probe_p12.py`(系ごとの指紋を HEAD と作業木で比べる・e13 の道具の写しを 1-2 に合わせた)・`shadow_counts.py`(19 構成のランの中の描画を全部 HEAD の描画の写しと比べ、件数を出す)・`render_cost.py`(描画 1 回の時間)。byte-check と 2 日のランは既存の道具(`10e/byte_check_10e.py`・`10e/two_day_check_act.py`)。

## 0. 結論

- 知覚の事実 `Percept`(`src/shibuya/perception/facts.py`・凍結の dataclass・slots・25 欄)を作り、描画を「状態 → `Percept`(`Renderer.perceive`)→ 文(`Renderer.render_percept`)」の 2 段に分けた。`render` は 2 つを続けて呼ぶ口のまま(`perceive(agent_id, step, …)` の刻みの引数は `step`=T0 の規則)。描く側(`render_percept`)は `Percept` と状態でない物(テンプレ・静的資産・時計の関数・キャッシュ)だけを読む(§3)。
- **描画のバイトは不変**: byte-check 19/19 構成で 25 欄とも HEAD と同じ(テープの全部の呼の `prompt_hash` の列の sha を含む)。HEAD の `renderer.py` のバイトそのままの写しを「双子」にして、合成の場面 13 種 × 4 刻み × 全員と、19 構成 × ランの中の全部の描画(300 体・1,032 刻み=試験/1,000 体・1 日=道具)で本文・ブロック・指紋・トークン・切り詰め・想起と知人の列・計数まで一致(§5)。
- **係数の計測(〔決定〕=最初に測る)**: 歩きスマホ 0.46 と看板の注視の活動の乗数(通話 0.49 など)を 1.0 にした HEAD の写しの byte-check は 19/19 構成・25 欄とも HEAD と同じ=**既定の結果は動かない**(▲ ではない)。どちらも既定のランで効く道が無い(PHONE の旗を立てる口が無い・乗数表は既定で全部 1.0)。
- **係数は消した**(親の判断=〔決定〕「動かなければ消す」): 歩きスマホの負荷の係数 `M_LOAD`・看板の注視の活動の乗数の表と検査の関数と腕(`--p-see-activity`)・親しみの層の乗数つきの p_see の口・種別ごとの注視の計数を消した。途中で入れた腕 `percept_coefs`(`SHIBUYA_PERCEPT_COEFS`・`--percept-coefs`)も消した。manifest の `p_see_activity` は欄を残して値は null。消した後の byte-check 4 構成は 25 欄とも HEAD と同じ(§4)。
- **起床 3 種と知人出現は知覚の事実の欄**(`watched_by`・`heard_speech`=`EventRef` の列・`nearby_change`・`acquaintance_seen`)。目の向き・心の向き・持ち物・道具の状態・本人の予想と合わせて 9 欄は値が空(None=仕組みがまだ無い)。
- **刻みの中の一時**: `TickScratch` の欄 `percepts`(体 → `Percept`・読むだけの写し)を decide だけが書く(宣言 `writes.scratch`)。状態台帳に行 `P`(軸 1 no・軸 2 discardable・道筋なし)。刻みの頭で空になり、どちらのハッシュにも状態のファイルにも入らない(§2・§6)。
- **判断の入力の形**: `PerceptCarrier`(`ctx.percept` を持つ形=1-8 の `DecisionPort.choose(ctx, …)` の `ctx`)・`Percept.prediction`(本人の予想の欄)・`with_prediction`。描き方の口は `PerceptDrawing`(`draw(percept) -> str`=`Renderer.draw`)。
- **計器**: manifest の一番上に `percept`(形の版・欄の数 25 と名・空の欄 9 の一覧)。TM9 の 4 欄を末尾に保つため、その前に足した。既存の欄は `p_see_activity` の値を null にした(係数の削除=段の決定から動く所)ほかは変えていない。
- 試験: 新しい試験 88 本(`tests/perception/facts/`)。既存の試験 3 本(`test_p_notice.py`・`test_p_see_activity.py`・`test_nearby_vectorized.py`)を段の決定に合わせて直した。§7。
- **独立検収(review.md)=条件つき受入 → 直した**(§13): M1(艦隊で録ったテープの再生で `BridgeResult.percept` が到着待ち O96 に残り full-hash が HEAD と違った)は、結果に欄を足さない形にして、HEAD の写しとの再生の比べ(10/10 同じ)と負の対照(欄を戻すと 6/10 違う)を試験と記録に。低い指摘 L1〜L9 も直した。直した後の byte-check 4 構成は 25 欄とも HEAD と同じ。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/perception/facts.py`(新) | `Percept` と下の記録(`SeenObject`・`SeenPerson`・`Sound`・`TimeView`・`BodyView`・`SelfView`・`IntentView`・`WakeView`・`SceneView`。どれも凍結・slots)・`EventRef`(=`engine.events.log.EventId` と同じ形)・`EMPTY_FIELDS`・`PerceptCarrier`・`PerceptDrawing`・`with_prediction`・`percept_manifest`。標準ライブラリだけ |
| `src/shibuya/perception/renderer.py` | `perceive`(状態 → `Percept`)・`render_percept`/`draw`(`Percept` → 文)・`render`=2 つを続けて呼ぶ。B1〜B6 の描き方を `Percept` から読む形に(`_b5`・`_b5_ranked`・`_b6`・`_observation`・`_intent_text`・`_with_intent_line`・`_with_memory_line`・`_cell_candidates`・`_cell_blocks_ranked` の引数を `Percept`/`SceneView` に)。`_nearby_people`(見えた人の構造=1-2 の前の `_nearby_items` の本体)と `_nearby_items`(その文の形・同じ値)・`_scene`(その場の事実・刻みにセルごと 1 回)・`_time_view`(時刻の見方・B3 の鍵ごと)・`_wake_view`・`_intent_view`。`_TickCache` に `tod_s`・`t_ns`・`day_kind`・`scenes`・`time_views`・`b3_text`。`Rendered.percept`。`day_kind_fn`(暦の日の種類の口)。**看板の注視の活動の乗数を消した**(`P_SEE_BY_ACTIVITY`・`check_p_see_activity`・引数 `p_see_activity`・`effective_p_see`・`p_see_activity_summary`・種別ごとの計数 `signage_by_kind`・`signage_effective_p`)。活動の種別 `P_SEE_ACTIVITY_KINDS` と `activity_classes` は親しみの層の露出の計数の鍵として残した |
| `src/shibuya/perception/p_notice.py` | **負荷の係数を消した**(`M_LOAD`・`PNoticeParams.m_load`・`p1_primary` の `m_load`)。課題従事の旗 `task_flag` は受けるだけ(確率に効かない) |
| `src/shibuya/engine/familiarity.py`・`src/shibuya/engine/systems/report.py` | 親しみの層の乗数つきの p_see の口 `p_see_fn` を消した・manifest の `p_see_activity` は null |
| `src/shibuya/engine/run.py`・`src/shibuya/engine/systems/build.py` | `run_day(p_see_activity=…)` は `None` 以外を止める(引数は設定の指紋と 1-0 の引数の数 113 を変えないため残す)・`RunResult.p_see_activity` は None・箱 `RunConfig` の 2 欄は 1-0 の割り当てのまま「表は無い」の値 |
| `src/shibuya/engine/llm_bridge.py` | `RenderedPrompt.percept`(既定 None・テープには書かない・アダプタが渡す)・`LLMBridge.call(…, percept_out=)`(呼び手の列に `Percept` を 1 つ足す=刻みの中だけの道)。**結果 `BridgeResult` には欄を足さない**(検収 M1=再生の到着待ち O96 に残るため) |
| `src/shibuya/engine/systems/decide.py` | 呼ごとに描いた `Percept` を集め(mock/再生の道=`bridge.call(…, percept_out=局所の列)`・艦隊の道=描画の結果から直に)、刻みの終わりに `scratch.percepts = MappingProxyType(…)` |
| `src/shibuya/engine/systems/boxes.py` | `SCRATCH_FIELDS` の末尾に `percepts`(34 → 35) |
| `src/shibuya/engine/systems/table.py` | decide の `scratch_w` に `percepts`・`reads` に `scratch.percepts` |
| `src/shibuya/engine/systems/build.py` | 描画に `day_kind_fn`(暦の `SimCalendar.day_kind`)を渡す(1 行) |
| `src/shibuya/engine/state_ledger.py` | 行 `P`(`TickScratch.percepts`・軸 1 no・軸 2 discardable・道筋なし)・除外に `renderer.day_kind_fn`(参照)。版は上げない(§9) |
| `src/shibuya/engine/run.py`・`src/shibuya/engine/manifest_sections.py` | manifest の `percept`(設定の節)・`p_see_activity` は混ざった辞書の子の道筋を消して欄そのものを設定に(値は null) |
| `src/shibuya/cli.py` | `--p-see-activity` を消した(1-2 の途中で足した `--percept-coefs` も消した) |
| `tests/perception/test_p_notice.py`・`tests/perception/test_p_see_activity.py` | 段の決定から動く所: 係数の釘を「係数が無い」の形に(`M_LOAD` の釘を消し、負荷の係数が無いことと歩きスマホの旗が確率に効かないことを見る試験を足した)・活動の乗数の試験は「表・腕・CLI の旗が無い・ゲートは p_see 1 つ・manifest は null」の形に書き直した |
| `tests/perception/test_nearby_vectorized.py` | 空振りの試験を直した: 差し替えの的を描画が通る `_nearby_people` に移し、呼ばれた回数で効きを確かめる・負の対照を 1 本足した |
| `tests/perception/facts/`(新) | 試験 4 本(88 件・§7)・道具 `scenes.py`(HEAD の写しの読み込み・双子・合成の場面)・HEAD の描画の写し `head_renderer_136fdbb.py`(本体 `136fdbb` の `src/shibuya/perception/renderer.py` のバイトそのまま・sha256 `b1d82c4f…586cbfe`) |
| `tests/engine/test_state_ledger_10b.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/time/manifest_keys_frozen.json`・`docs/bench/analysis/wallbounce-1012/run-day-decomp/local-assignment.json` | 凍結の表(§8) |

## 2. `Percept` の欄

| 欄 | 中身 | 値 |
|---|---|---|
| `agent_id`・`step`・`t_ns`・`cell` | 体・通しの刻みの番号 T・通しの時刻[ns](時計の原点との差)・セル | 状態から |
| `self_view` | 種別・所持金・手がふさがっているか・今の行為 | 状態から |
| `seen_objects` | 見えた物(id・種類 `poi`/`landmark`/`signage`・距離・向き・名)。セルの代表点から見える店と目印+注視のゲートを通った看板 | 距離と向きは None(空間の段) |
| `seen_people` | 見えた人(id・向き・行為=相手の `activity`・距離・知人か)。並びは B5 の近接行と同じ | 向きは None |
| `sounds` | 音(種類 `noise`・段) | 騒音の段 |
| `time_view` | `tod_s`(その日の中の秒)・`day_kind`(暦の日の種類=`weekday`/`saturday`/`sunday`)・5 分帯・時と分(5 分に切り捨て)・天候・日照・暑さの語 | 暦の口が無い描画は `day_kind` が None |
| `body` | 空腹・疲れ・暑さの値(0〜10)と段(閾値 4・7・9 を何本越えたか) | 状態から |
| `wake` | 起床の理由・招待者・直前の結果・結果があるか・直前の行動の語・観測値(最も安い品・次の開店・名指しの閉店の 1 句) | 状態と層の口から |
| `intent` | 意図(行為・対象の種類・対象) | 無ければ None |
| `memories` | 想起した記憶の行(記憶の層の `RecallItem`) | 想起の口が無いランは None |
| `signage_shown`・`watched_n` | 看板の注視のゲートを通ったか・被注視の人数(構築の時に渡す配列=ランでは渡さない=0) | |
| `scene` | その場(`SceneView`=同じセルの全員で同じ・刻みに 1 回作る): 見える物・看板の POI・密度の段・流れ・音・顕著な出来事・近景の項目・B4 の欄の指紋 | |
| `eye_dir`・`mind_dir`・`belongings`・`tool_state`・`watched_by`・`heard_speech`・`nearby_change`・`acquaintance_seen`・`prediction` | **欄だけ**(目の向き・心の向き=CT2/持ち物・道具の状態=1-7/誰が見ているか・聞こえる会話=`EventRef` の列・顔ぶれの変化・知人の出現=空間の段/本人の予想=1-8) | **None**(仕組みがまだ無い=未計測。空の tuple=「測ったが無かった」とは分ける) |

## 3. 描画の分離の範囲(残した直接読み)

`render_percept` の中で個体 SoA・世界の動く状態・層の口を読む所は 0(grep `self.agents`・`a.registry`・口の呼び出し)。読むのは次だけ:

| 描く所 | 読む物 | 種類 | 次の段 |
|---|---|---|---|
| B0・B1 | 設定の文・種別の語のキャッシュ(鍵=`Percept.self_view.kind`) | テンプレ | — |
| B2 | 場所の ID・帯・歩ける面・W15 の凍結文・見える店と目印の名・W14 の看板の文か店の営業時間(`world.pois.open_from/open_to`・`world.assets.cell_band`・`world.n_poi`)。キャッシュの鍵=(`cell`, `signage_shown`) | 静的な資産(ランの間は変わらない=初期化で写す値) | 見える物の文を `seen_objects` から組む形へ(名は `SeenObject.name` に入れてある) |
| B3 | `Percept.time_view` だけ(描いた文は刻みの中だけ `TimeView` の値で引く) | — | — |
| B4 | `Percept.scene` だけ(キャッシュの鍵=(セル, B4 の欄の指紋)) | — | 顕著な出来事は世界過程が作る**文**の材料(`scene.salient`)=構造は世界過程の側の段で |
| **B4b** | **`prepare_tick` が描いた文をセルで引く(`_tickc.b4b`)**。行列と活動の行は変化検出器のダイジェストに混ぜるため前計算で描く | 刻みの前計算のキャッシュ(同じ刻みの物だけ=`render_percept` は刻みの違う `Percept` を断る) | 行列(店・人数)と活動の行(文・人数)を `SceneView` に構造で持つ(今は行列の項目の文 `near_items` だけ) |
| B5・B6 | `Percept` だけ(意図の対象の名・想起の行の場所の名と時刻=静的な資産と時計の関数) | — | — |
| 単一ランキング(ablation ①) | `Percept`・`SceneView`・静的な資産 | — | — |

`Percept` の中に文のまま残した物(構造にしていない): 名指しの閉店の 1 句 `wake.closed_note`(既存の試験 `test_resume_10d.py` が `_named_closed_text` を差し替えて覗くので、その口を `perceive` の中に残した)・顕著な出来事 `scene.salient`・行列の項目 `scene.near_items`・天候と日照と暑さの語(`time_view`)。

## 4. 係数の計測と削除

1. **最初に測った**(作業木の実装の前): HEAD の src の写しを `tools/coef_patch_head_copy.py` で書き換え(`M_LOAD=(1.0, 1.0, 1.0)`・`check_p_see_activity` が全部 1.0)、byte-check の 19 構成を HEAD の写しと比べた=[coefs_measure_head_copy.json](coefs_measure_head_copy.json): **19/19 構成で 25 欄とも同じ=動かない**。
2. 効く道が無い理由: 歩きスマホ(`TaskLoad.PHONE`)の旗を立てる口が無い(顕著行為の過程は会話中=TALKING・ほか=FREE だけを貼る)。看板の注視の乗数表は既定で全部 1.0(19 構成のどれも `--p-see-activity` を渡さない)。
3. 最初の報告では、既存の試験 2 本と CLI の旗が編集の範囲の外だったので腕 `percept_coefs`(既定 on)で止めた。腕 off の byte-check も 19/19 で HEAD と同じだった([byte_check_p12_coefs_off.json](byte_check_p12_coefs_off.json)=履歴)。
4. **親の判断で消した**(〔決定〕「動かなければ消す」・試験 2 本と CLI の旗と manifest の欄は段の決定から動く所): §1 の一覧のとおり。消した値の数のリテラルは src に 1 つも無い(試験 `test_coef_removed_or_armed.py` が AST で見る)。課題従事の旗(`TaskLoad`・知覚 SoA の `task_flag`)と活動の種別(`P_SEE_ACTIVITY_KINDS`)は事実・計数の鍵として残した(係数ではない)。
5. **消した後の byte-check**([byte_check_p12_coefs_removed_4cfg.json](byte_check_p12_coefs_removed_4cfg.json)・4 構成 `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`・HEAD `136fdbb` の src と作業木の src): **4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`)。
6. **消した値と出どころ**(パターン台帳 §10 の検証専用へ=親が設計書に書く): 0.46=歩きスマホの気づきの比(Hyman 2010・知覚契約書 §3.1 の `m_load`・`p_notice.M_LOAD`)/0.49=通話中の気づきの比(Hyman 2010 表 2 の 25.0/51.3)・1.39=連れとの会話の比(同 71.4/51.3)=どちらも `--p-see-activity` の例と試験だけにあった値(草案 `v2-hunger-choice-attention-draft.md` §3-2)。目的地つき移動 0.5 は錨の無い感度腕の 1 点(検証の値ではない)。

## 5. 結果不変

| 確かめ | 方法 | 結果 |
|---|---|---|
| byte-check([byte_check_p12.json](byte_check_p12.json)) | `10e/byte_check_10e.py`・19 構成・5,000 体・seed 1・1 日・テープつき。HEAD の側=本体 HEAD `136fdbb` の src の写し・p12 の側=作業木の src(`src_is_worktree` 真)・腕は既定 on | 19/19 構成で 25 欄とも同じ(final・呼数・blocks・calls の全部の列の sha=全部の呼の `prompt_hash` を含む・行動の件数・起床の内訳・顕著行為・出動・食事・behavior/full の最後・締めの後の 2 本・暦・frozen_sources ほか)。既定 v3 の final `5f7ae9ff24005314`(T0・1-3 の記録と同じ) |
| 腕 off([byte_check_p12_coefs_off.json](byte_check_p12_coefs_off.json)=履歴) | 同じ道具・作業木の src(腕を消す前)・`SHIBUYA_PERCEPT_COEFS=off` | 19/19 構成で 25 欄とも HEAD と同じ |
| **係数を消した後**([byte_check_p12_coefs_removed_4cfg.json](byte_check_p12_coefs_removed_4cfg.json)) | 同じ道具・4 構成・作業木の最後の src | **4/4 構成で 25 欄とも HEAD と同じ** |
| 双子の比べ(試験) | `tests/perception/facts/test_render_from_percept_bytes.py`: HEAD の描画の写しを同じ物・同じ前計算の材料・同じ引数で描かせて全欄を比べる。(A) 合成の場面 13 種 × 4 刻み × 120 体(起床の理由・直前の結果・直前の行動・招待者を振る)と計数 17 種・(B) 19 構成 × 300 体 × 1,032 刻みの全部の描画 | 全部同じ。負の対照(描き方を 1 文字変える)は落ちる |
| 双子の比べ(道具・[shadow_counts_p12.json](shadow_counts_p12.json)) | `tools/shadow_counts.py`・19 構成 × 1,000 体 × 1,440 刻み | 19 構成とも違い 0。比べた描画は合わせて 201,536(構成ごとに 8,310〜18,481・描画のあった刻みは 1,024〜1,226)。代表の窓(朝 7:00〜・昼 12:00〜・夕 17:00〜 の各 12 刻み)にはどの構成も 11〜12 刻みの描画がある |
| 2 日のラン([two_day_p12.json](two_day_p12.json)) | `10e/two_day_check_act.py`・5,000 体・seed 1・既定 v3・HEAD の写しと作業木の src | HEAD の写しと全部の欄が同じ(final `912446bd2b42b6ab`=1-3 の記録と同じ・140,913 呼・テープの calls と blocks の中身の sha・暦の日付・天気の日ごとの記録) |
| 系ごとの指紋([probe_p12.json](probe_p12.json)) | `tools/probe_p12.py`(1-0 の probe・全部の刻み・系ごとの全欄の差と指紋・scratch は入れない)。3 構成(合成 80 体 720 刻み 記憶+関係+店・世界資産 300 体の既定 v3・記憶+関係)。両側とも描画のキャッシュの 2 本(O63 の `renderer._tickc`・`renderer._b3_cache`=1-2 で中身の形を変えた・full-hash でも中身を入れない道筋)を外した | 3 構成とも全部の系(18〜20)の指紋と全部の刻みの差の並び(5,944・14,158・16,270 件)が同じ・final と呼数も同じ |
| **検収の直しの後**([byte_check_p12_review_fix_4cfg.json](byte_check_p12_review_fix_4cfg.json)) | 同じ道具・4 構成(`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel`)・HEAD `136fdbb` の src の写しと作業木の最後の src | **4/4 構成で 25 欄とも同じ**(final `5f7ae9ff24005314`・`e0054a837c6ec4c1`・`24375ee3dab349e8`・`73a78288ab5e1498`) |
| 艦隊のテープの再生(検収 M1・試験 `test_replay_full_hash_matches_the_head_copy`) | 偽 vLLM 2 台(受理枠 8・遅れ 0.02 秒)で合成 120 体・40 刻み・語彙 v3・予算 30・本物の描画を作業木の src で録り、同じテープを HEAD の写しと作業木の src で別々のプロセスで再生(4 刻みごとの checkpoint) | full-hash 10/10・behavior-hash 10/10・final が同じ。**負の対照**(作業木の写しの `BridgeResult` に `percept` の欄を戻す)は full-hash が 4/10 しか同じでない=検収役の実測と同じ(behavior と final は同じ) |
| (注) | 19 構成の byte-check(on/off)と全体の試験は係数を消す前の src(腕あり・既定 on=今の値)。双子の比べの道具・2 日・系ごとの指紋はその少し前の src(`t_ns` の式と `FleetBridgeResult` の欄の直しの前=描画・ハッシュ・テープに入らない所だけの違い)。係数を消した後は 4 構成の byte-check と指定の試験の集合(§7)と、試験 (B) の 19 構成 × 300 体の双子の比べ(HEAD の写しは乗数の表が既定の全部 1.0)で確かめた | — |
| 再開 | 既存の試験(`tests/engine/test_resume_10d.py` ほか)と、`Percept` を捨てても final・checkpoint の full-hash が同じ試験 | 通った |

## 6. 刻みの中の一時(段 C の守り)

- `TickScratch.percepts` は decide だけが書く(`writes.scratch`)。宣言の外の系(observe・memory・perceive_prepare)が書くと段 C が止める(試験)。
- 刻みの頭で `reset` が空にする(各刻みの最初の系の前に None=試験で 480 刻みを見た)。番兵の scratch(T4)と段 B(`SHIBUYA_SYSTEMS_CHECK=1`)の上でもランが通る。
- `render_percept` は刻みの違う `Percept` を描かない(`ValueError`)。ランの後の描画の属性に `Percept` は無い(刻みの前計算の `SceneView` と `TimeView` は今の刻みの物だけ)。
- 状態台帳の行 `P` は軸 1 no(描画は Percept から文を描くが、刻みの中で状態から作り直す派生=知覚 SoA の heading・task_flag と同じ扱い)・軸 2 discardable・道筋なし。`full_items`・`behavior_items` に入らない。
- 〔検収 M1〕呼の結果(`BridgeResult`・`FleetBridgeResult`)に `Percept` の欄は無い。艦隊で録ったテープの再生では、後の刻みに届く結果が `run_day.replay_inbox`(O96=軸 2 required)に残るため、結果に欄があると `Percept` が刻みの外まで残り full-hash が変わる(検収役の実測 6/10)。`Percept` は `bridge.call` の引数 `percept_out`(decide の局所の列)で渡す。試験: 到着待ち・保留・艦隊の在途の箱と、その直列化(`state_hashes.to_state`)と状態のファイルに `Percept` も欄の名も無い・再生の full-hash が「Percept を作らない形」と全部同じ・HEAD の写しの再生と全部の checkpoint で同じ。
- 〔検収 L9〕`Percept.t_ns` と `time_view.tod_s` は進行役の刻みの時刻(`TickCtx.t_ns`・`tod_s`)と同じ値(480 刻みの全部の Percept で試験)。

## 7. 試験

- 新しい試験(`tests/perception/facts/`・88 件): `test_percept_schema.py`(23・欄と並びの凍結・凍結と slots・空の欄・事実が状態と描画に合う・暦の口・`EventRef`・判断の入力の形・描き方の口・manifest)・`test_render_from_percept_bytes.py`(49・§5)・`test_coef_removed_or_armed.py`(5・消した値のリテラルが src に無い・名が残らない・歩きスマホの旗が確率に効かない・注視は p_see 1 つ・manifest)・`test_percept_is_scratch.py`(11・§6=検収 M1 の 3 本・L8・L9 を足した)。所要約 110 秒(1 プロセス・うち 19 構成の双子の比べが約 95 秒・艦隊の再生が約 10 秒)。
- 段の決定に合わせて直した既存の試験: `test_p_notice.py`(21・係数の釘から `M_LOAD` を消し、負荷の係数が無い試験を足した)・`test_p_see_activity.py`(8・書き直し)・`test_nearby_vectorized.py`(8・的を `_nearby_people` に移し負の対照を足した)。
- **係数を消した後**(最後の src): `tests/perception tests/engine/systems tests/engine/time tests/test_cli.py tests/engine/test_env_and_sections_10f.py`+触った所の試験(`test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_familiarity.py`・`tests/llm/test_fleet_contract.py`)=**719 passed**(4 並列・6 分 47 秒・ほかの作業木と同時)。
- **検収の直しの後**(最後の src): `tests/perception tests/engine/systems tests/engine/time tests/test_cli.py tests/engine/test_env_and_sections_10f.py tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py`+触った所の試験(`test_state_checks_10f.py`・`tests/llm/test_fleet_contract.py`・`tests/engine/test_tape_deferred.py`)=**755 passed**(4 並列・8 分 50 秒)。`lint-imports` 5 kept。
- 係数を消す前の全体(`-m "not gpu and not slow" -n 4 --dist loadfile`): 4,186 passed・1 failed(junction 由来の既知 `test_ab7_seed1_open_matches_the_parent_report`)・1 xfailed(29 分 37 秒)。係数を消した後の全体は回していない(親の指定の集合だけ)。
- 1 回目の全体の試験で落ちた 4 本は直した: `tests/llm/test_fleet_contract.py::test_bridge_result_fields_mirror_engine_bridge_result`(そのときは `BridgeResult.percept` を `FleetBridgeResult` にも足した=検収 M1 の直しで両方とも欄を外した)・`tests/engine/test_state_checks_10f.py` の 3 本(`timedelta` の `.seconds` の読みが状態台帳の AST の検査で `norm_meter.seconds` と同じ名に当たった=§9)。

## 8. 触った共有ファイル

| ファイル | 触った所(親が取り込み順に rebase するときの目印) |
|---|---|
| `src/shibuya/engine/systems/table.py` | decide の `scratch_w`(`parse_errors percepts`)と `reads`(`scratch.percepts`)と注釈 1 行だけ |
| `src/shibuya/engine/systems/boxes.py` | `SCRATCH_FIELDS` の末尾に `percepts`(注釈 2 行)・docstring の欄の数 34 → 35・`RunConfig.p_see_activity_table` の上に注釈 1 行 |
| `src/shibuya/engine/state_ledger.py`(状態台帳) | 外の状態の末尾(行 `E` の後)に行 `P`・除外 `_x("renderer", REF, …, "day_kind_fn")` を 1 行・docstring と版の注釈に 1 行ずつ・**係数の削除で**: O84 の道筋から `renderer.signage_by_kind`・`renderer.signage_effective_p`、除外から `renderer` の `p_see_activity`・`_p_see_mult`・`_p_see_identity` と `fam_layer` の `p_see_fn` を消した |
| `src/shibuya/cli.py` | `--p-see-activity` の定義と `run(...)` への 1 行を消した |
| `src/shibuya/engine/run.py` | import 1 行・`run_manifest_fields` の `weather` と TM9 の間に `percept`・`p_see_activity` は None・`RunResult.p_see_activity` の型と既定・`run_day` の docstring |
| `src/shibuya/engine/manifest_sections.py` | TM9 の行の後に `percept`・`_mixed("p_see_activity", …)` を `"p_see_activity": _C` に |
| `src/shibuya/engine/systems/build.py` | 描画の組み立ての引数に `day_kind_fn` を 1 行・`check_p_see_activity` の import と検査を「None 以外は止める」に・描画の `p_see_activity=` と親しみの層の `p_see_fn=` を消した |
| `src/shibuya/engine/familiarity.py`・`src/shibuya/engine/systems/report.py` | `p_see_fn` の引数と分岐を消した・`result.p_see_activity = None` |
| `src/shibuya/engine/systems/decide.py`・`src/shibuya/engine/llm_bridge.py` | §1 のとおり(`llm/fleet.py` は検収 M1 の直しで HEAD のまま=触っていない) |
| `src/shibuya/engine/systems/table.py`(検収 L5) | report の `reads` から使わない `cfg.p_see_activity_identity cfg.p_see_activity_table` を外した(`report.py` の死んだ局所 2 行も消した) |
| `src/shibuya/engine/resolve.py`・`src/shibuya/perception/state.py`(検収 L4) | docstring と宣言の説明の `m_load` の文だけ |
| 凍結の表 | `tests/engine/time/manifest_keys_frozen.json`(`percept` を TM9 の前に 1 つ・注に「1-2 で係数を消した=`p_see_activity` は null」)・`tests/engine/test_env_and_sections_10f.py`(`P12_KEYS`・末尾の鍵の並びの式・`CONFIG_PATHS_SHA256` を `e6a25217…a343b78f` に=`percept` を足し、`p_see_activity` の子の道筋 4 つを消して欄そのものを設定に)・`tests/engine/test_state_ledger_10b.py`(外の状態 97 → 98・全体 188 → 189・鍵の列の末尾に `P`・行 `P` の軸)・`docs/bench/analysis/wallbounce-1012/run-day-decomp/local-assignment.json`(`locals` に `percepts`=HEAD の局所ではない印 `note` つき・`n_locals` と `kinds` は HEAD の値のまま) |

## 9. 限界と仮採用(10-13b §0-3=戻せる形・PENDING §1-1 の候補)

1. 状態台帳の行 `P` は軸 1 no・道筋なし(親の答え=no のままでよい)。版 `state-ledger/10e-ret` は上げない(行 `E` と同じ理由=どちらのハッシュにも状態のファイルにも入らず、上げると前の版の状態のファイルから再開できない)。行の鍵は `P`(O の通し番号でない)。
2. manifest の `percept` は TM9 の 4 欄の前に置いた(T0 の試験が TM9 を末尾に釘付け・10f の試験が末尾の鍵の並びを見る)。並びの式を 10f の試験で 1 か所直した。
3. `local-assignment.json` に HEAD の局所ではない `percepts` を足した(試験が scratch の欄の集合と表を突き合わせるため)。`note` で印を付け、`n_locals`(450)と `kinds` は HEAD の値のまま。
4. B3 のキャッシュ `_b3_cache` の値を「描いた文」から「天候・日照・暑さの語」に変えた(描いた文は刻みの中だけ `TimeView` の値で引く)。命中と外れの計数は 1 描画に 1 回で 1-2 の前と同じ(試験)。
5. `Percept` の中に文のまま残した物がある(§3 の最後)。名指しの閉店の 1 句は既存の試験の差し替えの口(`_named_closed_text`)を保つため。
6. 係数の削除で残した物: `run_day` の引数 `p_see_activity`(None 以外は止める=設定の指紋と 1-0 の引数の数 113 を変えないため)・箱 `RunConfig` の `p_see_activity_table`(None)と `p_see_activity_identity`(True)=1-0 の局所の割り当ての欄・`notice_event` の引数 `task_flag`(受けるだけ=知覚 SoA の `task_flag` の読み手と状態台帳の AST の許可を変えないため)・活動の種別 `P_SEE_ACTIVITY_KINDS` と `activity_classes`(親しみの層の露出の種別ごとの計数=`familiarity_summary`)。どれも係数ではない。過去の測りの道具 `docs/bench/analysis/energy-classical-2026-09-28/p_see_activity_measure.py` は今の src では動かない(履歴のまま)。
7. 描画 1 回の時間が延びた(§10)。`Percept` と下の記録を毎回作るぶん。**性能の宣言と回帰の試験は無い**(検収 L7): P4 の「ms/シミュ分@基準規模」の宣言と、描画の時間の回帰の試験は足していない(2-0 の計器で宣言する)。古典+記憶+関係の壁時計は 2 回とも +9%(HEAD 58.1・57.1 秒/後 63.2・62.5 秒)で、cProfile の全体の差(+0.04 秒)と描画の累計の差(+1.3 秒)も食い違う=負荷の揺れが 1 秒より大きい機械での測りで、増えた量は確かめられていない(静かな機械で測り直すのが残り)。
8. 通しの時刻 `t_ns` は `(世界内日時 − 時計の原点) // 1 µs × 1,000` で作る(`timedelta` の `.seconds` を読むと、状態台帳の AST の検査が `norm_meter.seconds`=軸 1 no の道筋と同じ名の読み手として拾うため・`tests/engine/test_state_checks_10f.py`)。

## 10. 性能

- 描画 1 回(合成の世界・5,000 体・139 セル・4,000 描画 × 11 回の中央値・`tools/render_cost.py`=[render_cost_p12.json](render_cost_p12.json)): 1-2 の後 112.2 µs・1-2 の前(HEAD の写しの双子)98.2 µs=**+14 µs(+14%)**。内訳は `perceive` 36.6 µs・`render_percept` 54.2 µs(別々に回した値)。5,000 体・1 日の既定 v3(65,597 呼)では約 0.9 秒=ランの壁時計(約 30 秒)の 3% 程度の見込み。B3 の文を刻みの中で 1 回だけ描く形と、看板つきの見える物をその場で 1 回だけ作る形にして、最初の版(+22 µs)から縮めた
- ランの壁時計(5,000 体・1 日・1 本ずつ HEAD と交互に 2 回・ほかの作業木の負荷と同時): 既定 v3 は HEAD 29.5・29.3 秒/1-2 の後 31.3・29.7 秒、classical+記憶+関係は HEAD 58.1・57.1 秒/1-2 の後 63.2・62.5 秒。負荷の揺れが大きいので、同じ構成を 2,000 体で cProfile にかけて比べた: ラン全体 44.83 秒(1-2 の後)と 44.79 秒(HEAD)・描画の `render` の累計 18.2 秒と 16.9 秒(+1.3 秒・35,759 回)。増えた分の半分ほどは `_scene`(0.73 秒)=呼の少ない刻みではセルごとのその場の事実を毎回作るため。見える物の列は静的な資産から決まるので、セルごとに 1 回だけ作る形にすれば縮む(状態台帳の O63 にキャッシュの道筋を 1 つ足す=1-2 ではやっていない)
- byte-check の壁時計(19 本の和・4 並列)は負荷の違いが大きく比べられない(HEAD 510 秒=先に回した・1-2 の後 633〜685 秒=ほかの道具や全体の試験と同時)

## 11. 親に確かめてほしいこと

1. 係数を消した後の全体の試験は回していない(指定の集合 719 passed と 4 構成の byte-check だけ)。消した道(活動の乗数・負荷の係数)はどちらも既定のランで効く道が無かったので、19 構成の byte-check は回し直していない(親の指示)。
2. 並べて進んでいるほかの段(1-4・1-6・1-9)も manifest の一番上の鍵・scratch の欄・状態台帳の行を足すなら、取り込みの順で同じ所がぶつかる(§8)。
3. `_scene` をセルごとの静的なキャッシュにすれば描画のコストはさらに縮む見込み(状態台帳の O63 に道筋を 1 つ足す・§10)。
4. 取り込み(1-4・1-6 の後への rebase)で合わせる所(検収役の「親に確かめてほしいこと」2〜4): 1-4 のつなぎの台帳の `p_notice` の見出しの項数(1-2 で expedient の項 `m_load` を消して 6 → 5)・manifest の末尾の並び(1-4 の `rules_version` ほかと 1-2 の `percept`=`test_percept_schema.py` の `keys.index("percept")`・10f の `_tail`・凍結の鍵の表・`CONFIG_PATHS_SHA256`)・状態台帳の行の数と並び(1-6 の M0・M0R と 1-2 の P)と `local-assignment.json`。M1 の試験の比べる相手 `BASE_COMMIT = "136fdbb"`(`test_percept_is_scratch.py`)も rebase の後の土台に合わせる。

## 12. 再現の手順(リポの根で・`$D`=このフォルダ・`$W`=作業用の短いディレクトリ)

    git archive 136fdbb src docs/bench/anchors docs/design/v2-budget-declaration.md \
        docs/bench/analysis/w6-regen-2026-09-28 | tar -x -C $W/head_src
    mkdir -p $W/head_src/data/calendar && cp data/calendar/syukujitsu.csv $W/head_src/data/calendar/
    B=docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py
    python $B side --src $W/head_src/src --label head --scratch $W --out $W/head.json
    # 係数の計測(最初): HEAD の写しの写しを書き換えて回す
    cp -r $W/head_src $W/coef1_src && python $D/tools/coef_patch_head_copy.py $W/coef1_src
    python $B side --src $W/coef1_src/src --label coef1 --scratch $W --out $W/coef1.json
    python $B compare --a $W/head.json --b $W/coef1.json --out $D/coefs_measure_head_copy.json
    # 係数を消した後(4 構成・HEAD の側は head.json から同じ 4 構成を抜いた head4.json)
    python $B side --src src --label p12rm --only w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel \
        --scratch $W --out $W/p12rm.json
    python $B compare --a $W/head4.json --b $W/p12rm.json --out $D/byte_check_p12_coefs_removed_4cfg.json
    # (履歴)腕を消す前の作業木: byte_check_p12.json(既定 on)・byte_check_p12_coefs_off.json(SHIBUYA_PERCEPT_COEFS=off)

## 14. 親の検収(第334・2026-10-14)

- 親の byte-check 4 構成(本体 HEAD bf00c2f の src=1-4・1-6 取り込み済み vs 作業木の src・係数を消した後): final が同じ 4/4・動いた欄 0(parent_head_vs_p12_4cfg.json)。
- 係数を消す判断は親(口の約束 1-2 の〔決定〕=計測で動かなければ消す)。消した値(0.46・0.49・1.39・Hyman 2010)はパターン台帳 §10 の検証専用へ親が書く。独立検収(review.md)=条件つき受入 → M1(BridgeResult の percept の欄が再生の箱=O96 に残り艦隊の再生で full-hash が動く)を実装役が直し(欄を外し decide の局所の列で渡す・再生の full-hash が HEAD と 10/10 同じ・負の対照 4/10)、低 L1〜L9 も直した(§13)。直しの後の試験 755 passed・byte-check 4 構成 同じ(実装役)。

## 13. 独立検収(review.md)の指摘と直し

| # | 直したこと | 確かめ |
|---|---|---|
| M1 | `BridgeResult`・`FleetBridgeResult` に `percept` の欄を足さない(`llm/fleet.py` は HEAD のまま)。`LLMBridge.call(…, percept_out=)` で呼び手(decide)の局所の列に渡し、decide が `TickScratch.percepts` に書く | 試験 3 本(`test_percept_is_scratch.py`): 到着待ち・その直列化・状態のファイルに `Percept` と欄の名が無い/再生の full-hash が「Percept を作らない形」と全部同じ/HEAD の写しの再生と全部の checkpoint で full・behavior・final が同じ(10/10)。負の対照(欄を戻した写し)は 4/10 しか同じでない |
| L1 | 試験の数を実数に(88=5+11+23+49)・§8 の `manifest_keys_frozen.json` の重複を 1 つに | — |
| L2 | `run.py`・`manifest_sections.py` の注釈から「係数の腕」を消した | — |
| L3 | `_b3_cache` の型注釈を `dict[tuple, tuple[str, str, str]]` に(値は天候・日照・暑さの語) | — |
| L4 | `resolve.py` の `set_notice_state` の docstring と `perception/state.py` の `task_flag` の説明から「p_notice の m_load が読む」を直した(説明の文字列はハッシュに入らない) | — |
| L5 | `report.py` の死んだ局所 2 行を消し、`table.py` の report の `reads` から 2 語を外した | `tests/engine/systems` |
| L6 | `Renderer.perceive(agent_id, step, …)`(新しい口の刻みの引数を `step` に・`render` は凍結の名 `tick` のまま) | `tests/engine/time`(tick の語の検査) |
| L7 | 記録の限界に書いた(§9 の 7) | — |
| L8 | 「刻みの外で残らない」の試験に、到着待ち・保留・艦隊の在途の箱と状態のファイルを足した | M1 の試験と同じ |
| L9 | `Percept.t_ns`・`time_view.tod_s` が `TickCtx.t_ns`・`tod_s` と同じ値の試験を足した | 480 刻みの全部の Percept |

## 15. 本体への rebase(`a3a8104`=1-4・1-6・1-9 を取り込んだ後)の衝突の解き方と合わせ

衝突は 6 本。どれも**両方の追加を残した**(git の操作=`git add`・`rebase --continue`・commit は親)。

| ファイル | 解き方 |
|---|---|
| `src/shibuya/engine/manifest_sections.py` | 1-4 の `rules_version`・`run_kind`・`bridges_version` の行と 1-2 の `percept` の行を両方 |
| `src/shibuya/engine/systems/table.py` | decide の `paths` に 1-6 の `M0*:mem_layer.memory_store.*`、`scratch_w` に 1-2 の `percepts` |
| `src/shibuya/engine/state_ledger.py` | docstring の行の数を 192 に(E・M0・M0R・A・P)・版の注釈は 1-6 と 1-2 の両方・行は 1-6 の M0・M0R、1-9 の A の後に 1-2 の P |
| `tests/engine/test_state_ledger_10b.py` | 外の状態 101 行・全体 192 行・鍵の末尾 `E`・`M0`・`M0R`・`A`・`P`・各行の軸の確かめは全部 |
| `tests/engine/test_env_and_sections_10f.py` | `R14_KEYS`・`C19_KEYS` と `P12_KEYS` を両方・末尾の並び `T0 → R14 → C19 → P12`・`CONFIG_PATHS_SHA256` を解いた後に計算し直した(`4d75732b…92174dc5`=1-9 の `1b0edc6d…` に 1-2 の `percept` の道筋と `p_see_activity` の子の道筋の削除を足した値) |
| `tests/engine/time/manifest_keys_frozen.json` | 注は 1-4・1-9 の文に 1-2 の文をつないだ。鍵は 113 個(1-9 の 112+`percept`) |

**manifest の末尾の並び**: 「T0 の TM9 → 1-4 の欄 → 1-9 の `economy` → 1-2 の `percept`」にそろえた(1-2 の枝では TM9 の前に置いていた)。`engine/run.py` の `run_manifest_fields` で `percept` を `economy` の後へ移し、末尾の並びを見る試験 3 本を合わせた: `tests/perception/facts/test_percept_schema.py`(`keys[-1] == "percept"`)・`tests/engine/time/test_t0_tm9_fields.py`(TM9 の後ろが `rules_version`・`run_kind`・`bridges_version`・`economy`・`percept`)・`tests/engine/bridging/test_manifest_rules_bridges.py`(1-4 の 3 欄は末尾の 2 つ前まで・末尾 2 つが `economy`・`percept`)。

**合わせ**:

1. 1-4 のつなぎの台帳 `docs/design/bridging-ledger.json` の行 `HD-perception.p_notice-16ea5cb3` の `what` を「項 6 個」→「項 5 個」に(1-2 で `p_notice.py` の docstring の expedient の見出しの項 `m_load` を消した)。`tests/engine/bridging/test_bridging_ledger.py` の見出しの項の合計 338 → 337(注つき)。
2. 新しい試験 `test_percept_is_scratch.py` の `BASE_COMMIT` を `136fdbb` → `a3a8104` に。HEAD の写し(`a3a8104` の src)と作業木の src で同じ艦隊のテープを再生した full-hash・behavior-hash・final は全部の checkpoint で同じ(試験 `test_replay_full_hash_matches_the_head_copy` が通った=飛ばしていない)。
3. 描画の写し `tests/perception/facts/head_renderer_136fdbb.py` はそのまま: 本体 `a3a8104` の `src/shibuya/perception/renderer.py` の sha256 は `b1d82c4f…586cbfe`=写しと同じ(1-4・1-6・1-9 で変わっていない)。
4. `run-day-decomp/local-assignment.json` の `percepts` は残した(自動で合わさった)。`SCRATCH_FIELDS` は 35(1-4・1-6・1-9 は scratch の欄を足していない)。

**試験**(解いた後・作業木): `tests/perception tests/engine/systems tests/engine/time tests/engine/events tests/engine/memory tests/engine/bridging tests/engine/rules tests/economy tests/engine/test_state_ledger_10b.py tests/engine/test_env_and_sections_10f.py tests/engine/test_state_checks_10f.py tests/engine/test_resume_10d.py tests/test_cli.py`(`-m "not gpu and not slow" -n 4 --dist loadfile`)=**1,151 passed**(11 分 8 秒・飛ばした 0 件)。byte-check は親が回す。
