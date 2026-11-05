# src/shibuya/perception

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 11 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../../src/shibuya/perception/__init__.py)

perception: レンダラ/ハッシュ三役/注意ゲート/p_notice → Observation DTO。world/agents/core に依存。

- import している内部モジュール: `shibuya.perception.attention`・`shibuya.perception.channels`・`shibuya.perception.hashes`・`shibuya.perception.normalize`・`shibuya.perception.p_notice`・`shibuya.perception.renderer`・`shibuya.perception.state`・`shibuya.perception.templates`

## [attention.py](../../../../../../../src/shibuya/perception/attention.py)

perception.attention — 注意ゲート 段0-段3(知覚契約書 §4)。「届く」→「気づく」。

- 公開の関数とクラス
  - `SalientItem`(クラス): 顕著性順位づけの入力(1件)。
  - `StripReport`(クラス): 命令文除去の記録(黙って消さない=診断行へ)。
  - `apply_budget`(関数): 段2 の件数上限(既定は**非注入**=枠に入らなければ載せない)。
  - `content_cap_chars`(関数): 注視秒 → 日本語字数の上限 ``round(7.5×秒)``(下限4・上限30)。
  - `feature_tag`(関数): 素性タグの固定文言(§1 条6)。
  - `gate_stage1`(関数): 段1 の一発ベルヌーイ(決定論・``core.rng.stream`` のドメイン分離)。
  - `p_see`(関数): 媒体 → 視認確率(§4 段1)。
  - `rank_by_saliency`(関数): 顕著性=**視角×局所コントラスト(+動き・逸脱度)**の降順に並べ替える。
  - `strip_imperatives`(関数): 世界内テキストから**命令文を文単位で除去**する(§1 条6・§4 段3)。
  - `tag_world_text`(関数): 世界内テキスト → (素性タグ+命令文除去+内容キャップ済みの本文, 除去記録)。
- import している内部モジュール: `shibuya.core.rng`
- 呼び手: `shibuya.build.lang.common`・`shibuya.engine.familiarity`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.salient`・`shibuya.perception`・`shibuya.perception.renderer`
- 読む試験: `tests/build_lang/test_w14_signage.py`・`tests/engine/processes/test_salient.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/test_familiarity.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/test_attention.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_signage_p_see_gate.py`
- 決定の ID: 11-03

## [channels.py](../../../../../../../src/shibuya/perception/channels.py)

perception.channels — チャネル別トークン上限表(知覚契約書 §3.2)と有界化(切り詰め)。

- 公開の関数とクラス
  - `BudgetMode`(クラス): §3.2 の**義務 ablation**「固定枠 vs 単一ランキング」の切替。
  - `ChannelLimit`(クラス): 1チャネルの上限(§3.2 の表の1行)。
  - `Grade`(クラス): 根拠等級(知覚契約書 §3.2 凡例)。
  - `RankingPrior`(クラス): 単一ランキングでチャネルに与える顕著性の既定素性(**全て expedient**)。
  - `TruncationReport`(クラス): 切り詰めの記録(診断行へ出す)。
  - `block_channel_total`(関数): あるブロックのチャネル上限の合計(§3.2 の「| ブロック | 内訳 |」の縦計)。
  - `estimate_tokens`(関数): 粗いトークン数見積り(expedient: UTF-8 文字数 ÷ 2、最低 1)。
  - `pool_token_budget`(関数): §3.2「**同一総トークン**」= そのブロック群のチャネル上限の総和。
  - `take_within_pool`(関数): **順位順**に並んだ行列から、池の予算に収まる**先頭 n 件**を返す。
  - `truncate_lines`(関数): チャネル上限までの行を残す(**行の途中では絶対に切らない**)。
- 呼び手: `shibuya.build.lang.common`・`shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.report`・`shibuya.engine.tape`・`shibuya.perception`・`shibuya.perception.renderer`・`tools/c6/ablation1_fixed_vs_ranking.py`
- 読む試験: `tests/build_lang/test_w14_signage.py`・`tests/build_lang/test_w15_cell_static.py`・`tests/build_lang/test_wiring.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_two_layer_activity.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_channels.py`・`tests/perception/test_nearby_vectorized.py`・`tests/perception/test_templates.py`
- 決定の ID: 11-03・11-03/§2

## [contact_view.py](../../../../../../../src/shibuya/perception/contact_view.py)

perception.contact_view — 連絡の道具 C1 の知覚の事実の値(目と心の向き・道具の状態)と描き方の行(第 6 期 6-4・腕 c1 だけ)。

- 公開の関数とクラス
  - `AttentionView`(クラス): 目と心の向き(``Percept.mind_dir`` の値=腕 c1 のランだけ)。
  - `DeviceView`(クラス): 道具の状態と通知(``Percept.tool_state`` の値=腕 c1 のランだけ)。返すのは現実の道具が知り得ることだけ(CT0 の 4)。
  - `contact_lines`(関数): B6 の末尾に足す行(通話 → 着信 → 通知 → 未読 → 割り込めなかった出来事の順)。
  - `people_hint_word`(関数): 人の気配の数 → 粗い語(周辺視=数えない)。
- 呼び手: `shibuya.engine.contact.attention`・`shibuya.engine.contact.calls`・`shibuya.engine.contact.deliver`・`shibuya.engine.contact.layer`・`shibuya.perception.renderer`
- 読む試験: `tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c1_world.py`・`tests/engine/contact/test_c2_video.py`
- 決定の ID: 10-12/§4-4

## [facts.py](../../../../../../../src/shibuya/perception/facts.py)

perception.facts — 知覚の事実 ``Percept``(第 1 期 1-2 知覚の分離)。

- 公開の関数とクラス
  - `BodyView`(クラス): 体の段(空腹・疲れ・暑さ)。``hunger``・``fatigue``・``thermal`` は内受容の値(0〜10)、``*_stage`` は閾値
  - `IntentView`(クラス): いまの意図(行為のコード・対象の種類=``agents.state.IntentKind``・対象の番号)。
  - `Percept`(クラス): 1 体・1 刻みの知覚の事実(構造のある事実。文は ``Renderer.render_percept`` が描く)。
  - `PerceptCarrier`(クラス): 1-8 の ``DecisionPort.choose(ctx, candidates)`` の ``ctx`` が満たす形(知覚の事実を持つ)。
  - `PerceptDrawing`(クラス): 知覚の事実の描き方(文章はその 1 つ=``perception.renderer.Renderer``)。
  - `SceneView`(クラス): その場(セルと刻みで決まる事実=同じセルの全員で同じ・刻みごとに 1 回作る)。
  - `SeenObject`(クラス): 見えた物 1 つ(id・種類・距離・向き)。今はセルの代表点から見える物=距離と向きは空間の段で入る(None)。
  - `SeenPerson`(クラス): 見えた人 1 人(id・向き・行為)。並びは描画の近接行と同じ(焦点が先頭・ほかは距離の順か id の順)。
  - `SelfView`(クラス): 自分の状態(種別・所持金・手がふさがっているか・今の行為)。持ち物の中身は ``Percept.belongings``(空=1-7)。
  - `Sound`(クラス): 聞こえる音 1 つ(段)。
  - `TimeView`(クラス): 時刻の見方(同じ刻みの全員で同じ)。
  - `WakeView`(クラス): 起きた理由と直前の結果(B6 の材料)。
  - `percept_fields`(関数): ``Percept`` の欄の名(宣言順)。
  - `percept_manifest`(関数): manifest の ``percept``(計器): 形の版・欄の数と名・空の欄の一覧。
  - `with_prediction`(関数): 本人の予想を並べた ``Percept`` の写し(1-8 の口が使う)。
- 呼び手: `shibuya.engine.body.system1`・`shibuya.engine.run`・`shibuya.perception.renderer`
- 読む試験: `tests/engine/body/test_system1_placeholders.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/contact/test_c2_video.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/memory/test_m3_impression_and_trace.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/test_nearby_vectorized.py`
- 決定の ID: 10-03/§7・10-12/§1-6・10-12/§1-13・10-12/§4-4・10-13b/§4-2・R-113

## [hashes.py](../../../../../../../src/shibuya/perception/hashes.py)

perception.hashes — **ハッシュ三役**(知覚契約書 §2.2/§5)。

- 公開の関数とクラス
  - `b4_field_row`(関数): B4 の**描画に使う欄**を ``(n_cells, 4)`` int32 に並べる(欄ハッシュの素)。
  - `block_hash`(関数): 描画済みブロックのバイト列 → xxh64(三役の 1 本目=prefix キャッシュ鍵)。
  - `block_hashes`(関数): バイト列の列 → uint64 配列。
  - `field_row_hash`(関数): 1 行の欄 → xxh64。
  - `field_row_hashes`(関数): ``(n, k)`` int32 の行ごとの xxh64。
  - `hash_report`(関数): 診断行用の 1 行(``B2=0x… B4=0x…``)。
  - `prefix_key`(関数): ブロックハッシュの列 → prefix キャッシュ鍵(1 本の u64)。
  - `should_resend`(関数): dormant 再送抑止(三役の 3 本目)。
- import している内部モジュール: `shibuya.core.hashing`
- 呼び手: `shibuya.engine.change_detect`・`shibuya.perception`・`shibuya.perception.renderer`
- 読む試験: `tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_render_from_percept_bytes.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_hashes_state.py`・`tests/perception/test_renderer_golden.py`
- 読む試験(道筋で): `tests/engine/test_salt_seed_split_10f.py`

## [normalize.py](../../../../../../../src/shibuya/perception/normalize.py)

perception.normalize — バイト一致の正規化規約 9 項(知覚契約書 §2.4)を関数にしたもの。

- 公開の関数とクラス
  - `AgentDependentWordError`(クラス): B0-B4 に個体依存語が混入した(§2.4 ⑧ 違反)。
  - `assert_no_abbreviation`(関数): ⑥ 省略記法が入っていないことを検査する。
  - `assert_no_agent_dependent_words`(関数): ⑧ B0-B4 に個体依存語が無いことを検査する(混入したら例外)。
  - `canonical_whitespace`(関数): 空白・改行の正準形(§2.4 ③)。
  - `format_meters`(関数): 距離[m]の固定桁表記(④ 単位固定・① 固定桁丸め)。
  - `format_minutes`(関数): 時間[分]の固定表記。
  - `format_money`(関数): 金額[円]の固定表記(3 桁区切り・v0 文面「所持金は1,200円です」に合わせる)。
  - `format_time`(関数): (時, 分) の**固定桁なし**表記(v0 文面「現在時刻は12時40分です」に合わせる)。
  - `join_lines`(関数): 1行1事実の行列 → ブロック本文(空行は落とし、LF 固定で連結)。
  - `or_empty`(関数): ⑦ 空要素は固定文言。非空なら読点で連結する。
  - `peg_stage`(関数): ⑤ 段階語彙の釘付け: 値 → 段番号(``edges`` は昇順の**法定/LOS 境界**)。
  - `peg_stage_array`(関数): ``peg_stage`` のベクトル版(セル配列にそのまま掛ける)。
  - `round_fixed`(関数): ① 固定桁丸め(段階語彙を持たない量に使う)。
  - `round_time_5min`(関数): 世界内日時 → (時, 分) を 5 分**切り捨て**で丸める(§2.4 ⑨)。
  - `sort_ids`(関数): 列挙は **ID 昇順**(§2.4 ②)。数値 ID は数として、文字列 ID はコードポイント順。
  - `time_band`(関数): 世界内日時 → 5 分帯の番号(0..287)。共有ブロックのキャッシュ鍵。
- import している内部モジュール: `shibuya.core.time_consts`
- 呼び手: `shibuya.build.lang.common`・`shibuya.engine.activity`・`shibuya.engine.change_detect`・`shibuya.engine.memory_store`・`shibuya.perception`・`shibuya.perception.renderer`
- 読む試験: `tests/build_lang/test_wiring.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_normalize.py`・`tests/perception/test_renderer_golden.py`

## [p_notice.py](../../../../../../../src/shibuya/perception/p_notice.py)

perception.p_notice — 人物③「顕著な行為」への確率的到達(知覚契約書 §3.1・案B 2段ヒル型)。

- 公開の関数とクラス
  - `Ablation`(クラス): §3.1 の ablation A0-A4(A4=完成形)。
  - `Counters`(クラス): 診断行に出す計数(§6 運用規定「診断行に常設」)。
  - `DensityClass`(クラス): 密度クラス(``m_density`` の索引)。
  - `EventBudget`(クラス): 顕著イベントの 1 tick 上限(§3.1「顕著イベント上限200/tick(宣言値)」)。
  - `NoticeResult`(クラス): 1イベント×候補群の結果。
  - `PNoticeParams`(クラス): §3.1 の係数一式(ablation で振るのはこの dataclass を差し替える)。
  - `TaskLoad`(クラス): 課題従事フラグ(M12 の 1 byte)。〔第 1 期 1-2〕負荷の係数は消した=値は事実として残す(心の向きの仕組みの入力の候補)。
  - `combine`(関数): ``p = 1 − (1−P1')(1−P2)``。
  - `eccentricity_deg`(関数): 事象方向と視線方向の角度差 ``|E_ang|``[度・0..180]。
  - `heading_to_degrees`(関数): 量子化された向き(0..sectors-1 の uint8)→ 度[0,360)。セクタ0 = +x 方向。
  - `notice_event`(関数): 1つの顕著イベントについて、候補群の「気づいた/気づかない」を引く(§3.1)。
  - `p1_primary`(関数): TTPF 一次検出 ``P1``。``d50_eff=0``(背後)は 0 を返す(〔1-2〕負荷の係数 ``m_load`` は消した)。
  - `p2_social`(関数): 社会伝播 ``P2 = a·N^b/(n50^b + N^b)``(N=0 なら 0)。
  - `social_counts`(関数): 各点の半径 ``radius_m`` 内にある「既に気づいた点」の数(自分自身は数えない)。
- import している内部モジュール: `shibuya.core.rng`
- 呼び手: `shibuya.engine.processes.salient`・`shibuya.perception`・`shibuya.perception.state`
- 読む試験: `tests/engine/processes/test_salient.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_processes_run.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/test_p_notice.py`
- 決定の ID: 10-12/§1-6

## [renderer.py](../../../../../../../src/shibuya/perception/renderer.py)

perception.renderer — 観測レコード → B0-B6 の決定論描画(知覚契約書 §2)。

- 公開の関数とクラス
  - `PerceptionAssets`(クラス): 描画に要る静的資産(セル代表点からの可視物・名称・歩行可能面積・天候表)。
  - `Rendered`(クラス): 1 起床ぶんの描画結果。
  - `Renderer`(クラス): 観測レンダラ(1 起床=1 呼び出し)。
  - `acquaintance_ids_in`(関数): 10e(E5・A8): B5 の本文に「(知人)」の印つきで出た相手の体 id(出た順・重複なし)=テープ版 4 の列。
  - `activity_line`(関数): 活動の (文, 人数) の列(人数降順→文字列順・上位 2)→ B4b の 1 行(無ければ ``""``)。
  - `check_hunger_words`(関数)
  - `check_near_order`(関数)
  - `check_near_tiebreak`(関数)
  - `check_signage_p_see`(関数): 看板の注視確率を検査して返す(0.0〜1.0 の外は ``ValueError``)。
  - `compose_memory_line`(関数): 項(順位の高い順)→ B5「記憶」の 1 行と載せた項の数(6b・M4)。0 件なら ``("", 0)``。
  - `intent_line`(関数): 意図の 1 行(``INTENT_LINE_MAX_TOKENS`` に収まるよう対象の名を末尾から切り詰める)。
  - `memory_item_text`(関数): 想起した 1 行(``engine.memory.RecallItem`` と同じ欄を持つもの)→ B5「記憶」の項 1 件(6b・v1.2)。
  - `named_closed_note`(関数): Q25 の補足の 1 句(店名 + 閉店中 + あれば「HH:MM に開く」・≤ 15 tok)。
  - `near_person_text`(関数): 見えた人(``facts.SeenPerson``)→ B5 近接行の項(``P-<id>(未知/知人)``・1-2 の前と同じ表層)。
  - `near_tie_keys`(関数): 観る体 ``observer`` から見た相手 ``ids`` の撹拌鍵(u64・splitmix64 の仕上げ・配列演算)。
  - `near_tie_salt64`(関数): ``blake3(run_salt ‖ b"nt\x00")`` の先頭 8 バイト(u64)。1 ランに 1 回だけ作る。
  - `person_word`(関数): 個体 id → 観測に出る人 ID の表層(``P-17``)。
  - `strip_speech_imperatives`(関数): 発話の本文 → 看板と同じ表(``strip_imperatives``)で落とした後、発話だけの型(``SPEECH_IMPERATIVE_PATTERNS``)の文も落とす。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.core.hashing`・`shibuya.core.time_consts`・`shibuya.perception.attention`・`shibuya.perception.channels`・`shibuya.perception.contact_view`・`shibuya.perception.facts`・`shibuya.perception.hashes`・`shibuya.perception.normalize`・`shibuya.perception.templates`・`shibuya.world.assets`・`shibuya.world.state`
- 呼び手: `shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.memory_store`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.report`・`shibuya.perception`・`tools/c6/ablation1_fixed_vs_ranking.py`
- 読む試験: `tests/build_lang/test_wiring.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_relations.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_weather_calendar_10e.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/facts/test_render_from_percept_bytes.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_b4b_queue_feed.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_intent_mode_open.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_nearby_vectorized.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_renderer_golden.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`
- 読む試験(道筋で): `tests/engine/test_salt_seed_split_10f.py`
- 状態台帳の行
  - 持ち主 `renderer`(`Renderer`)
    - `O63` PerceptionRenderer のキャッシュ _b1_cache〜_b4_cache・_rank_cell_cache・_acq_cache・_tickc(挙動 no・復元 derivable) 道筋 `renderer._acq_cache`・`renderer._b1_cache`・`renderer._b2_cache`・`renderer._b3_cache`・`renderer._b4_cache`・`renderer._rank_cell_cache`・`renderer._tickc` 書ける系: decide・perceive_prepare・world
    - `O64` PerceptionRenderer の口 acquaintance_fn・memory_recall・session_partner_fn・named_closed_lookup・signage_exposures(挙動 no・復元 discardable) 道筋 `renderer.acquaintance_fn`・`renderer.memory_recall`・`renderer.named_closed_lookup`・`renderer.session_partner_fn`・`renderer.signage_exposures` 書ける系: decide・memory
    - `O84` PerceptionRenderer の計数(挙動 diag・復元 discardable) 道筋 `renderer.cache_hits`・`renderer.cache_misses`・`renderer.contact_lines`・`renderer.contact_lines_over_budget`・`renderer.contact_unnoticed_renders`・`renderer.intent_lines`・`renderer.intent_lines_over_budget`・`renderer.memory_items`・`renderer.memory_items_dropped_for_budget`・`renderer.memory_items_dropped_for_channel`・`renderer.memory_line_tokens`・`renderer.memory_lines`・`renderer.memory_lines_over_budget`・`renderer.named_closed_notes`・`renderer.near_order_ties`・`renderer.near_tie_breaks`・`renderer.near_tie_candidates`・`renderer.renders`・`renderer.signage_gate_draws`・`renderer.signage_gate_shown`・`renderer.speech_lines`・`renderer.speech_lines_over_budget`・`renderer.truncation_count` 書ける系: decide・perceive_prepare
- 決定の ID: 10-12/§1-6・10-12/§1-13・11-03・D-59・D-60・D-71・D-111・D-113・D-117・D-118・第 269・第 300・第 304

## [state.py](../../../../../../../src/shibuya/perception/state.py)

perception.state — 知覚側が持つ個体 SoA(予算行 **M12** と prefix 抑止の前回ハッシュ)。

- 公開の関数とクラス
  - `PerceptionState`(クラス): 知覚側の個体 SoA。
  - `heading_from_vector`(関数): 進行方向ベクトル → 量子化された向き(0..sectors-1 の uint8)。
- import している内部モジュール: `shibuya.core.soa`・`shibuya.core.write_permit`・`shibuya.perception.p_notice`
- 呼び手: `shibuya.engine.processes.salient`・`shibuya.perception`
- 読む試験: `tests/engine/systems/test_stage_a_guard.py`・`tests/engine/test_state_ledger_10b.py`・`tests/perception/test_hashes_state.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`・`tests/tools/test_repo_guide.py`
- 状態台帳の行
  - SoA の列 `perception`
    - `perception.heading` heading(挙動 no・復元 derivable) 書ける系: world
    - `perception.invocation_distance` invocation_distance(挙動 no・復元 discardable・死蔵) 書ける系: (宣言なし)
    - `perception.task_flag` task_flag(挙動 no・復元 derivable) 書ける系: world
- 決定の ID: D-102

## [templates.py](../../../../../../../src/shibuya/perception/templates.py)

perception.templates — **凍結された観測テンプレ v1**(知覚契約書 §1 条5「文面凍結」)。

- 公開の関数とクラス
  - `b0_sha256`(関数): B0 本文そのものの版ハッシュ(**腕の切替が効いたかの指紋**)。
  - `b0_system`(関数): 腕(``intent_mode``)と語彙版(``vocab_version``)に応じた B0(system)の全文。
  - `block_group`(関数): ブロック id → 予算グループ名。
  - `check_intent_mode`(関数): ``intent_mode`` を検査して正規化する(不正値は ``ValueError``)。
  - `check_role_words`(関数): ``role_words`` を検査して bool に正規化する(``"on"/"off"`` も受ける)。
  - `check_vocab_version`(関数): ``vocab_version`` を検査して正規化する(不正値は ``ValueError``)。
  - `role_words_line`(関数): 語彙版 → B0 の末尾に足す役割語の 1 行(v3 は 11 語)。
  - `template_sha256`(関数): テンプレ全体の版ハッシュ(§1 条5「ハッシュで版管理」)。
- import している内部モジュール: `shibuya.core.hashing`
- 呼び手: `shibuya.cli`・`shibuya.engine.change_detect`・`shibuya.engine.classical`・`shibuya.engine.contact.device`・`shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.perception`・`shibuya.perception.renderer`
- 読む試験: `tests/build_lang/test_wiring.py`・`tests/c6/test_c6lib_scenes.py`・`tests/c8/test_ablations_ab7.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_relations.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_two_layer_activity.py`・`tests/perception/facts/head_renderer_136fdbb.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b4_detector_gap.py`・`tests/perception/test_b4b_queue_feed.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_channels.py`・`tests/perception/test_intent_mode_open.py`・`tests/perception/test_normalize.py`・`tests/perception/test_renderer_golden.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/perception/test_templates.py`・`tests/perception/test_vocab_v2_templates.py`・`tests/test_cli_intent_mode.py`・`tests/test_cli_vocab_version.py`
- 決定の ID: 11-03・11-03/§2・D-38・D-71・D-73・D-89・D-113・D-116・D-118・D-120・第 268・第 269・第 274・第 291・第 295・第 298・第 299
