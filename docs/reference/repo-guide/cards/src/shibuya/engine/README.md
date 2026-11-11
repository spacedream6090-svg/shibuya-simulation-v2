# src/shibuya/engine

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 16 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [bridging](bridging/README.md)・[calendar2](calendar2/README.md)・[calendar3](calendar3/README.md)・[contact](contact/README.md)・[duties](duties/README.md)・[events](events/README.md)・[systems](systems/README.md)・[tools](tools/README.md)

## [__init__.py](../../../../../../../src/shibuya/engine/__init__.py)

(冒頭の説明なし)

- 読む試験(道筋で): `tests/tools/test_bytecheck.py`・`tests/tools/test_pkgmove.py`

## [arbiter.py](../../../../../../../src/shibuya/engine/arbiter.py)

engine.arbiter — 繰り延べアービタ(知覚契約書 §6 の裁定規則)。

- 公開の関数とクラス
  - `Arbiter`(クラス): 毎tick の裁定+保留の持ち越し+診断計数の積み上げ(1 シミュ日ぶん)。
  - `ArbiterDecision`(クラス): 1 tick 分の裁定結果(純関数 ``arbitrate`` の出力)。
  - `WakeCandidates`(クラス): 1 tick 分の起床候補(全て同じ長さの配列)。
  - `arbitrate`(関数): 繰り延べアービタの**純関数**本体(入力の並び順に依存しない)。
  - `call_budget_per_tick`(関数): 予算行 L4 を tick あたり・当該規模へ按分した呼数。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.hashing`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.judge`
- 読む試験: `tests/bench/test_refr20b_tool.py`・`tests/c6/test_l4_l6_budget.py`・`tests/c8/test_ablations_ab8.py`・`tests/c8/test_ablations_l4_pin.py`・`tests/economy/test_entry_capital.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_arbiter.py`・`tests/engine/test_l4_budget.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_two_layer_activity.py`・`tests/test_cli_l4_scale.py`
- 読む試験(道筋で): `tests/engine/test_add_at_guard.py`・`tests/engine/test_two_phase.py`・`tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `arbiter`(`Arbiter`)
    - `O42` Arbiter _pending・_pool・queue・_last_tick(挙動 behavior・復元 required) 道筋 `arbiter._last_tick`・`arbiter._pending`・`arbiter._pool`・`arbiter.queue` 書ける系: arbiter
    - `O71` Arbiter の計数(挙動 diag・復元 discardable) 道筋 `arbiter._diag_total`・`arbiter._merged_total`・`arbiter._outside_total`・`arbiter._sleep_total`・`arbiter.budget_unused`・`arbiter.n_calls_total` 書ける系: arbiter
- 決定の ID: 09-25・D-56・D-66・D-99・D-110

## [calendar.py](../../../../../../../src/shibuya/engine/calendar.py)

engine.calendar — 暦の口(指示書 10-03 §3-1 A1・A1-1・A1-2・A1-3)。

- 公開の関数とクラス
  - `CalendarWarning`(クラス): 暦の口の警告(祝日 CSV が無い)。
  - `HolidayTable`(クラス): 祝日の表(日付 → 名称)と出どころ。
  - `SimCalendar`(クラス): ランの暦(``start_sim_datetime`` と T から日付・曜日・祝日・季節・給料日・営業日を返す)。
  - `holidays_between`(関数): ``lo``〜``hi``(両端を含む)の祝日(ISO の日付 → 名称)。
  - `load_holidays`(関数): 内閣府の祝日 CSV を読む(cp932)。無ければ空の表を返し、警告を 1 回だけ出す。
  - `parse_school_holidays`(関数): 学校の長期休みの区間の一覧(manifest の欄 ``school_holidays``)を ``(始, 終)`` の組に直す。
  - `parse_start`(関数): 開始日の欄(``--start-date``)→ ``datetime``。``None``/空は ``None``(既定の導き方)。
  - `ticks_per_day`(関数): 1 日の tick 数(``tick_seconds`` が 1 日を割り切らなければ ``ValueError``)。
- import している内部モジュール: `shibuya.foundation.paths`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`
- 呼び手: `shibuya.act.activity`・`shibuya.engine.run`・`shibuya.mind.judge.classical`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`・`shibuya.world.body.energy`・`shibuya.world.laws.environment`・`shibuya.world.laws.opening`・`shibuya.world.laws.rail`・`shibuya.world.laws.runner`
- 読む試験: `tests/build_field/test_field_units.py`・`tests/build_field/test_w12_real_timetables.py`・`tests/economy/stage2/test_stage2_guards.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/calendar3/test_ca3_units.py`・`tests/engine/experiment/_x33.py`・`tests/engine/experiment/test_x33_branch.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_calendar.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_weather_calendar_10e.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: 10-03/§3-1・第 330

## [calendar_self.py](../../../../../../../src/shibuya/engine/calendar_self.py)

engine.calendar_self — カレンダー 1b「勤務の出入りを本人へ」(第 6 期 6-2・腕 ``--calendar 1b``)。

- 公開の関数とクラス
  - `CalendarSelf`(クラス): カレンダー 1b の層(状態台帳の腕の行 ``C1B``・``C1BM``・腕 ``--calendar 1b`` のランだけ)。
  - `CommuteClassicalPort`(クラス): 仮のモデル(古典=見積りの幅の真ん中を使う)。ほかは mock と同じ規則(判断モデルまでのつなぎ)。
  - `CommuteMockPort`(クラス): 仮のモデル(mock・判断モデルまでのつなぎ=CA5 問い 2「モックはそのまま寄り」)。
  - `Estimate`(クラス): 見積りの幅[分]\(``lo``〜``hi``)。
  - `Observation`(クラス): 今の観測(本人が見たもの)。``time_min``=本人が読んだその日の時刻[分]\(おおよそなら丸めた値)。
  - `Prediction`(クラス): 本人が知っている予想(約束の時刻と場所の言葉・見積りの幅・余裕・時計を見る間隔)。時刻はその日の分。
  - `arm`(関数): いまの腕(``w17``=既定・``1b``=出入りを本人へ)。組み立てのときに読む。
  - `build`(関数): 組み立ての口: 腕 1b のランの層を作り、0 日目を張り、計画実行層に口を挿す(腕 w17 は ``None``)。
  - `commute_candidates`(関数): 出入りの候補(J0 の候補の形・番号は口が振る)。行き=出発する/まだ出ない/よく考える・帰り=帰る/まだ残る/よく考える。
  - `duration_words`(関数): 本人に渡す長さの言葉(``ROUND_MIN`` 分に丸める・最小は「5 分ほど」)。
  - `felt_minutes`(関数): 経過時間の実感[分]\(R-111 §1 の形): 待ちは 1.9+0.72×実際(出典の範囲 3〜15 分の中だけ=外は比 1)・待ち以外は比 1
  - `first_entering_train`(関数): 検査の口(実装の ``CalendarSelf.first_train`` と別に鉄道の表を直に引く): 路線 ``line`` で ``ready_T`` 以降に最初に
  - `hop_walk_steps`(関数): 節の数 → 歩く刻み(〔第 5 期 空間の段 1・検収 M5〕)。``hop_steps`` が None なら 1 刻み 1 節(legacy の見積り=B8)・
  - `is_on`(関数)
  - `manifest_fields`(関数): manifest の末尾に足す欄(腕 1b のランだけ ``{"calendar_1b": …}``・既定は空=manifest は今のまま)。
  - `observe_time`(関数): 本人が読む時刻(TM8): 時計やスマホを見れば分単位・見なければ ``APPROX_ROUND_MIN`` 分に丸めた「ごろ」。
  - `route_steps`(関数): 歩行グラフ(W3 の next-hop)で src → dst の節の数(着かなければ −1)。体はベクトル・ループは道のりの節の数ぶん。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--calendar``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
  - `update_estimate`(関数): 直近の実感の値の平均で見積りを作り直す(記憶の仕組みまでのつなぎ)。幅=直近の最小と最大(2 回より少なければ最初の幅)。
  - `validate_commitments`(関数): 1 人の約束の列を確かめる(CA4 (d))。返り値=(壊れた行の印, 重なりの組の一覧)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar_shadow`・`shibuya.engine.presence`・`shibuya.engine.resolve`・`shibuya.engine.tools.registry`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.hashing`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`・`shibuya.mind.judge.decision.sources`
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/space/test_nav1_units.py`
- 読む試験(道筋で): `tests/engine/test_salt_seed_split_10f.py`
- 状態台帳の行
  - 持ち主 `calendar_self`(`CalendarSelf`)
    - `C1B` CalendarSelf.cal_store(本人の予定の器=その日の約束・置き場所・見積り・機会・行き来の時刻・第 6 期 6-2)(挙動 behavior・復元 required・腕 calendar) 道筋 `calendar_self.cal_store` 書ける系: close_final・day_close・day_head・presence・world
    - `C1BM` CalendarSelf.cal_meter(判断の記録と計器=日ごとの記録・エンジンがしないこと 3 つの検査・第 6 期 6-2)(挙動 diag・復元 required・腕 calendar) 道筋 `calendar_self.cal_meter` 書ける系: day_head・presence
- 環境変数: `SHIBUYA_CALENDAR`
- 決定の ID: 10-12/§1-3・10-12/§2-1・10-12/§4-1・10-13b/§0-3・11-01・R-111・R-111 §1-1 #1・R-111 §1-2 #1・第 340

## [calendar_shadow.py](../../../../../../../src/shibuya/engine/calendar_shadow.py)

engine.calendar_shadow — 暦 1a の影(第 3 期 3-1・決定 10-12 §4-1 CA2 (a)・CA8)。

- 公開の関数とクラス
  - `CalendarShadow`(クラス): 暦 1a の影(状態台帳の行 ``CAL``・軸 1 diag・軸 2 derivable・中身は hash_skip)。
  - `CalendarTable`(クラス): ランの体の並びに引き直した W20 の週の表(配列は ``(体, 週, 曜日)``)と版の記録。
  - `arm`(関数): いまの腕(``w17``=既定・``1a``=影を W20 から作る)。組み立てのときに読む。
  - `build`(関数): 組み立ての口: 腕 1a のランの影を作り、0 日目を張る(腕 w17 は ``None``)。
  - `is_on`(関数)
  - `load_table`(関数): W20 の週の表を読み、ランの体の並び(``agent_ids``=W16 の ``agent_id``)に引き直す。
  - `manifest_fields`(関数): manifest の ``calendar_shadow``(腕 w17 のランは源だけ・ほかの子は null)。
  - `resolve_path`(関数): W20 の週の表の道筋(環境変数 ``SHIBUYA_CALENDAR_W20`` があればそれ・無ければ ``<world_dir>/w20_calendar_1a.parquet``)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--calendar-shadow``・試験の切替口)。組み立ての時に読む。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.world.facts.weekly_reader`
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar3.roster`・`shibuya.engine.calendar_self`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/build_sched/test_w20_calendar_1a.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/calendar/test_calendar_shadow.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `calendar_shadow`(`CalendarShadow`)
    - `CAL` CalendarShadow(暦 1a の影=その日の勤務と授業の約束と日ごとの計器・第 3 期 3-1)(挙動 diag・復元 derivable) 道筋 `calendar_shadow.shadow_day_log`・`calendar_shadow.today` 書ける系: day_head
- 環境変数: `SHIBUYA_CALENDAR_SHADOW`・`SHIBUYA_CALENDAR_W20`
- 決定の ID: 10-12/§4-1

## [change_detect.py](../../../../../../../src/shibuya/engine/change_detect.py)

engine.change_detect — 起床条件 (i)(ii) の検出器(予算行 **P6**)。

- 公開の関数とクラス
  - `B5Crossing`(クラス): 1 変数ぶんの閾値跨ぎ(``resolve`` が段を書き戻すための最小情報)。
  - `ChangeDetector`(クラス): B4 ハッシュと B5 閾値の変化検出器(scratch を持ち回して確保を避ける)。
  - `DetectResult`(クラス): 1 tick 分の検出結果(**世界には書かない**)。
  - `b4_block_hashes`(関数): B4 描画欄の行ごとの xxh64(``perception.hashes.field_row_hashes`` に委譲)。
  - `b4_block_raw`(関数): セル動的ブロック B4 の**描画欄** ``(n_cells, 4)`` int32(``B4_FIELD_COLUMNS`` の順)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.text.hashes`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.engine.resolve`・`shibuya.runtime.clocks.step_scope`・`shibuya.runtime.systems.assemble`・`shibuya.world.body.rules`・`shibuya.world.model.geometry`
- 読む試験: `tests/engine/body/body_fixtures.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_change_detect_p6.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`
- 読む試験(道筋で): `tests/engine/test_two_phase.py`・`tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `detector`(`ChangeDetector`)
    - `O45` ChangeDetector _prev_raw(挙動 behavior・復元 required) 道筋 `detector._prev_raw` 書ける系: detect
- 決定の ID: 10-13b/§4-2

## [chooser.py](../../../../../../../src/shibuya/engine/chooser.py)

engine.chooser — 選択器の口 ``Chooser.probs``(段 2a・D-114 (a)・2026-09-28)。

- 公開の関数とクラス
  - `ChoiceContext`(クラス): 1 回の選択の文脈(選び手が読んでよいものだけ)。
  - `Chooser`(クラス): 選択器の口。``probs`` は候補と同じ長さの確率(和 1・候補が空なら空)を返す。
  - `ClassicalChooser`(クラス): D-119 の DestinationChooser(5b・L3 (a)+L8 (a))。分布を返す(one-hot ではない)。
  - `NearestChooser`(クラス): 既定の選び手(**憲法⑥の宣言つき暫定**・expedient)。
  - `check_chooser`(関数): 選び手の名前を検査して返す。
  - `draw_index`(関数): 確率 ``p`` から 1 つ引く(``core.rng.stream(seed, "engine.chooser", tick, agent_id)``)。
  - `entropy_bits`(関数): 分布のエントロピー[bit]\(one-hot なら 0)。
  - `hunger_stage_of`(関数): ``hunger`` → 空腹の語の段 0〜3(energy は写し 1/5/8/10・v1 は 0〜10 を同じ刻みで読む=宣言)。
  - `make_chooser`(関数): 名前 → 選び手(``classical`` は p_h・τ を取る)。
- import している内部モジュール: `shibuya.foundation.rng`
- 呼び手: `shibuya.cli`・`shibuya.engine.poi_target`・`shibuya.engine.run`・`shibuya.mind.judge.classical`・`shibuya.mind.judge.store_choice`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/space/test_nav1_units.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `poi_resolver.chooser`(`ClassicalChooser`)
    - `O25` ClassicalChooser last_habit・stats(挙動 diag・復元 discardable) 道筋 `poi_resolver.chooser.last_habit`・`poi_resolver.chooser.stats` 書ける系: apply_responses
  - 持ち主 `poi_resolver.chooser` の別のクラス `NearestChooser`(行は `shibuya.engine.chooser` のカードを見る)
- 決定の ID: 09-25・D-114・D-118・D-119・D-120・第 292

## [commit.py](../../../../../../../src/shibuya/engine/commit.py)

engine.commit — 二相コミットの Phase A(intent 収集)と Phase B(資源ごとの裁定)。

- 公開の関数とクラス
  - `CommitPlan`(クラス): Phase B の出力。
  - `IntentBatch`(クラス): Phase A の出力(SoA)。1 個体につき 1 件までに畳んである。
  - `ResourceSpace`(クラス): 資源 ID の名前空間(POI / 会話相手 / 就寝スロット)。
  - `arbitrate_resources`(関数): Phase B: 資源ごとに pk 昇順で確定する(**世界は書き換えない**)。
  - `delta_perc_ns`(関数): 起床条件 → δ_perc[ns]\(予期クラス別の定数・expedient)。
  - `engine_continuations`(関数): Phase A のエンジン内部分: 移動中の個体の「経路の1歩」。
  - `focus_codes`(関数): (ヒント, 名指しの個体, 解決した POI) → ``agents.focus_target`` の符号化。
  - `intents_from_responses`(関数): Phase A の LLM 由来分: 行動コード → 対象と資源を**エンジンが**決めて intent にする。
  - `pair_partners`(関数): 同一セルに居る**起床中の**個体から会話相手を決める(決定論・ループなし)。
  - `parse_action`(関数): 2行形から行動語を取り出してコードにする(**正典パーサへの薄い委譲**)。
  - `talk_partners`(関数): 会話の相手を決める(**LLM の「対象」欄を第一**・C6 の設計準拠化 09-09)。
  - `target_hint_code`(関数): 対象ヒントの語 → 索引(未知の語は ``TARGET_HINT_NONE``)。
  - `tick_start_ns`(関数): tick 開始のナノ秒(δ_perc を足す基準)。
  - `undefined_fallback_code`(関数): 未定義行動の落ち先コード(v1/v2=待機・**v3=なし**=アジェンダ §1-1)。
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.agents.state`・`shibuya.foundation.hashing`・`shibuya.foundation.types`・`shibuya.foundation.vocab.actions`・`shibuya.llm.undefined`・`shibuya.world.model.proximity`
- 呼び手: `shibuya.act.activity`・`shibuya.act.intent`・`shibuya.engine.poi_target`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.memory.memory`・`shibuya.runtime.systems.act`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.judge`・`shibuya.runtime.systems.talk`
- 読む試験: `tests/c6/test_t5_order_bias.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_vocab_v2_eat.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: D-71・D-112・D-114・D-116・第 275

## [llm_bridge.py](../../../../../../../src/shibuya/engine/llm_bridge.py)

engine.llm_bridge — エンジンと LLM クライアントの**唯一の接点**(録画/リプレイ・δ_think・解釈)。

- 公開の関数とクラス
  - `BridgeResult`(クラス): 1呼の結果(エンジンが intent を組むのに必要なものだけ)。
  - `CallStart`(クラス): 〔第 1 期 1-8 J0〕1 呼の前半(知覚の事実まで)。``LLMBridge.begin`` が作り ``finish`` が残りを行う。
  - `LLMBridge`(クラス): エンジン ↔ LLM の一本道。``mode="record"`` は実クライアント/mock、``"replay"`` はテープ。
  - `PerceptionRendererAdapter`(クラス): ``perception.renderer.Renderer`` を bridge の ``Renderer`` 契約へ橋渡しする。
  - `RenderedPrompt`(クラス): レンダラの出力。
  - `Renderer`(クラス): 観測ブロック(B0-B6)→プロンプト本文の契約。本物は ``perception.renderer.Renderer``。
  - `StubRenderer`(クラス): 決定論の最小プロンプト(``prompt_hash`` が (agent, cell, tick//5, wake_class) で決まる)。
  - `delta_think_ticks`(関数): レーン → δ_think[tick]\(**分tickへ切り上げ**・運用設計書 §2.4)。
- import している内部モジュール: `shibuya.act.intake.parser`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.runtime.inference.tape`
- 呼び手: `shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.llm_io`・`shibuya.runtime.systems.run_end`
- 読む試験: `tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/memory/test_m0_render_bytes.py`・`tests/engine/rights/test_no_permission_count.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_undefined_action.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/llm/test_fleet.py`・`tests/llm/test_fleet_contract.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `bridge`(`LLMBridge`)
    - `O85` LLMBridge _interned(テープへ書いた共有ブロック)(挙動 no・復元 required) 道筋 `bridge._interned` 書ける系: close_final・decide
    - `O86` LLMBridge の計数(挙動 diag・復元 discardable) 道筋 `bridge.n_calls`・`bridge.n_deferred`・`bridge.n_dictionary_mapped`・`bridge.n_label_alias`・`bridge.n_parse_errors`・`bridge.n_parse_errors_strict`・`bridge.n_positional`・`bridge.n_role_actions`・`bridge.n_role_unauthorized`・`bridge.n_role_unjudged`・`bridge.n_tape_misses`・`bridge.n_tape_rows`・`bridge.n_undefined_mapped`・`bridge.n_unknown_action` 書ける系: close_final・decide
- 決定の ID: D-58・D-59・D-71

## [poi_target.py](../../../../../../../src/shibuya/engine/poi_target.py)

engine.poi_target — 購入/食事/並ぶの対象を**候補 → 選び手**で決める(段 2a・D-114 (a))。

- 公開の関数とクラス
  - `TargetResolver`(クラス): 対象欄の読み・候補の絞り込み・選び手の抽選(1 ランに 1 つ・世界は読むだけ)。
  - `move_resolution_summary`(関数): 段 2b の計数 → manifest ``move_resolution`` の形。
  - `resolution_summary`(関数): 計数 → manifest ``target_resolution`` の形((i)〜(iv)+エントロピーの平均)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.chooser`・`shibuya.engine.commit`・`shibuya.world.assets`・`shibuya.world.model.state`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.mind.memory.wom`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.report`
- 読む試験: `tests/engine/test_classical_policy.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `poi_resolver`(`TargetResolver`)
    - `O26` TargetResolver _cat_mask_cache・stats・entropy_sum・named_closed・move_stats(挙動 diag・復元 discardable) 道筋 `poi_resolver._cat_mask_cache`・`poi_resolver.entropy_sum`・`poi_resolver.move_stats`・`poi_resolver.stats` 書ける系: apply_responses・phase_c
    - `O94` TargetResolver named_closed(名指しの店の即時閉店の控え)(挙動 behavior・復元 required) 道筋 `poi_resolver.named_closed` 書ける系: apply_responses・phase_c
- 決定の ID: D-112・D-114・D-120・第 270・第 286

## [presence.py](../../../../../../../src/shibuya/engine/presence.py)

engine.presence — 計画実行層(Presence & Plan Executor・D-66 第1段)。

- 公開の関数とクラス
  - `EventType`(クラス): 日次イベントの種(設計書 §3 の表)。値は表の番号。
  - `PlanBlocks`(クラス): **在圏ブロック**(その体がその日「舞台に居る」連続区間)の CSR。
  - `PlanExecutor`(クラス): 計画実行層(D-66 第1段)。日次でイベント列を組み、tick ごとに resolve を叩く。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.foundation.time_consts`・`shibuya.world.facts.weekly_reader`・`shibuya.world.laws.switch_rate`・`shibuya.world.model.state`
- 呼び手: `shibuya.engine.calendar_self`・`shibuya.engine.run`・`shibuya.runtime.systems.assemble`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_presence_derive_v2.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_resume_10d.py`
- 読む試験(道筋で): `tests/economy/cp2/test_cp2_transfer_only_writer.py`・`tests/engine/body/test_body_guard.py`・`tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `presence`(`PlanExecutor`)
    - `O35` PlanExecutor 退出の歩行 _walk_since・_walk_line・_plan_rider・_rewalked・_rewalk_*(挙動 behavior・復元 required) 道筋 `presence._plan_rider`・`presence._rewalk_deadline`・`presence._rewalk_ids`・`presence._rewalk_line`・`presence._rewalked`・`presence._walk_line`・`presence._walk_since` 書ける系: close_final・day_close・day_head・decide・plan_boundary・presence・world
    - `O36` PlanExecutor _defer_ids・_defer_deadline・_defer_line・_defer_walk・_extra・_skip_depart_at(挙動 behavior・復元 required) 道筋 `presence._defer_deadline`・`presence._defer_ids`・`presence._defer_line`・`presence._defer_walk`・`presence._extra`・`presence._skip_depart_at` 書ける系: close_final・day_close・day_head・plan_boundary・presence・world
    - `O37` PlanExecutor _pulled_in_today(挙動 diag・復元 required) 道筋 `presence._pulled_in_today` 書ける系: close_final・day_close・day_head・plan_boundary・presence・world
    - `O38` PlanExecutor ev_*・arrival_*・absent・blocks(挙動 no・復元 derivable) 道筋 `presence.absent`・`presence.arrival_cell`・`presence.arrival_tick`・`presence.arrival_train`・`presence.arrival_train_e1`・`presence.blocks`・`presence.ev_act`・`presence.ev_agent`・`presence.ev_arg`・`presence.ev_place`・`presence.ev_tick`・`presence.ev_type` 書ける系: close_final・day_close・day_head・plan_boundary・presence
    - `O70` PlanExecutor の計数と時別の控え(挙動 diag・復元 discardable) 道筋 `presence.exit_cell_by_hour`・`presence.exit_stage_max_by_hour`・`presence.fallback_minutes`・`presence.in_area_by_hour`・`presence.lost_why`・`presence.match_in_den`・`presence.match_in_num`・`presence.match_out_den`・`presence.match_out_num`・`presence.n_arrivals`・`presence.n_arrive_skipped`・`presence.n_arrive_skipped_in_area`・`presence.n_arrive_skipped_pulled`・`presence.n_depart_dropped`・`presence.n_depart_skipped`・`presence.n_departed_by_llm`・`presence.n_departures`・`presence.n_exit_deferred`・`presence.n_exit_forced`・`presence.n_exit_gate_immediate`・`presence.n_exit_lost`・`presence.n_exit_lost_deferred`・`presence.n_exit_lost_final`・`presence.n_exit_no_platform`・`presence.n_exit_rewalk_forced`・`presence.n_exit_rewalk_gone`・`presence.n_exit_rewalk_queued`・`presence.n_exit_rewalk_started`・`presence.n_exit_too_far`・`presence.n_exit_walk_boarded`・`presence.n_exit_walk_departed`・`presence.n_exit_walk_gone`・`presence.n_exit_walk_restarted`・`presence.n_exit_walk_started`・`presence.n_exit_walk_waiting_at_start`・`presence.n_gate_arrivals`・`presence.n_home_out_slept_inside`・`presence.n_placed_at_start`・`presence.n_pulled_in`・`presence.n_pushed_out`・`presence.n_queue_balked`・`presence.n_rearmed`・`presence.n_returned_to_block`・`presence.n_shopping_interrupted`・`presence.n_spread_moved`・`presence.n_spread_overflow`・`presence.n_walk_calls`・`presence.n_walk_wakes_suppressed`・`presence.platform_cell_by_hour`・`presence.sample_hours`・`presence.sample_in_area`・`presence.sleep_counts`・`presence.wake_in_area_by_hour`・`presence.walk_minutes` 書ける系: close_final・day_close・day_head・decide・observe・plan_boundary・presence・wake_filter・world
- 決定の ID: 11-01・11-01/§2・11-02・D-51・D-61・D-62・D-66・D-115・第 145・第 170・第 302・第 330

## [relations.py](../../../../../../../src/shibuya/engine/relations.py)

engine.relations — **関係辺の表と導出**(C10 8a・第299)+**会話の起点と相手選択**(C10 8b)。

- 公開の関数とクラス
  - `InitialEdges`(クラス): 機械的初期化の辺(体の行番号の組・有向)と監査の材料。
  - `RelationEdges`(クラス): 1 体の生きている辺(A ≥ τ_rel・A の降順)。
  - `RelationLayer`(クラス): 関係辺の書き手と読み口(``MemoryLayer`` が持つ・``--relations on`` のランだけ)。
  - `check_rel_tenure_hash`(関数): 在職期間のハッシュの版を検める(関係の部品の単体の口・〔第 2 部〕ランの口の切替口 --rel-tenure-hash は消した)。
  - `copresence`(関数): ``(g, 枠)`` のセル → ``(共在の分(g×g), 共在のブロック数(g×g))``(同じセル・同じ枠・行列積)。
  - `copresence_days`(関数): ``(g, 7×96)`` のセル → ``(g, g)`` の「共在のあった曜日の数」(0〜7・同じセル・同じ枠が 1 枠でもある日)。
  - `initial_edges`(関数): W16(世帯・組織・学校セル)+W17(共在)→ 初期辺(有向・体ごとに上位 k − 世帯)。
  - `slot_cells`(関数): 体行の配列 → ``(体, 7×96)`` の「その 15 分に居るセル」(W17 の解決済みセル・無ければ −1)。
  - `tau_from_edges`(関数): τ の逆算: 体ごとの k 番目に強い辺の A(k 本に満たない体は −∞)の中央値(=半分の体が k 本残る τ)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.foundation.hashing`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.contact_flags`・`shibuya.world.model.proximity`
- 呼び手: `shibuya.engine.run`・`shibuya.mind.memory.memory`・`shibuya.mind.relations.people`・`shibuya.runtime.systems.assemble`
- 読む試験: `tests/engine/memory/test_m4_m5_people.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`
- 読む試験(道筋で): `tests/engine/tools/contacts_writers.py`・`tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `rel_layer`(`RelationLayer`)
    - `CT5` RelationLayer contact_flags(個人の連絡先の手段ごとの印・第 1 期 1-7)(挙動 diag・復元 derivable) 道筋 `rel_layer._contact_flags` 書ける系: memory
    - `O16` RelationLayer _prev_cell(挙動 behavior・復元 required) 道筋 `rel_layer._prev_cell` 書ける系: memory・relations_wake
    - `O17` RelationLayer _acq_until(挙動 behavior・復元 required) 道筋 `rel_layer._acq_until` 書ける系: decide・memory・relations_wake
    - `O18` RelationLayer _co_since・_co_day・_co_active(挙動 behavior・復元 required) 道筋 `rel_layer._co_active`・`rel_layer._co_day`・`rel_layer._co_since` 書ける系: memory・relations_wake
    - `O19` RelationLayer _invite_salt・chosen_count・origin_of・stats ほか(挙動 diag・復元 discardable) 道筋 `rel_layer._invite_salt`・`rel_layer.chosen_count`・`rel_layer.init_audit`・`rel_layer.origin_of`・`rel_layer.stats`・`rel_layer.wall` 書ける系: apply_responses・conversation・decide・memory・relations_wake
- 決定の ID: 10-12/§4-4・R-36・R-62・D-31・D-93・第 299・第 300

## [removed_switches.py](../../../../../../../src/shibuya/engine/removed_switches.py)

engine.removed_switches — 消した旧道の切替口の一覧と、渡されたら止める口(第346 旧道の切替口の削除)。

- 公開の関数とクラス
  - `check_environment`(関数): 消した切替口の環境変数(:data:`REMOVED_ENV` の全部)のどれかが置かれていれば止める(ランの入口で呼ぶ)。
  - `message`(関数): 止めるときの文(名・消した段・安定版のタグ)。
  - `stop_if_set`(関数): ``names`` の環境変数のどれかが置かれていれば(空でない値)止める(``ValueError``)。
- 呼び手: `shibuya.cli`・`shibuya.economy.rules_bind`・`shibuya.runtime.switch_defects`・`shibuya.runtime.systems.assemble`・`shibuya.world.laws.switch_seat`・`shibuya.world.model.proximity`
- 読む試験: `tests/engine/test_removed_switches_346.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 環境変数: `SHIBUYA_DEFECT_FIXES_1103`・`SHIBUYA_PROXIMITY`・`SHIBUYA_RULES_42`・`SHIBUYA_RULES_42B`・`SHIBUYA_SEAT_RELEASE`・`os.environ` をまるごと使う
- 決定の ID: 第 346

## [resolve.py](../../../../../../../src/shibuya/engine/resolve.py)

engine.resolve — **世界状態への唯一の書き込み口**(二相コミットの Phase C)。

- 公開の関数とクラス
  - `ResolveOutcome`(クラス): Phase C の結果(診断行の素材)。
  - `advance_body`(関数): 内受容 3 変数の自然変動(**C4 の世界過程が入るまでの駆動源**・expedient)。
  - `apply`(関数): Phase C: 確定した intent だけを世界へ適用する(**唯一の書き手**)。
  - `apply_detection`(関数): ``change_detect`` が返した新しい B4 ハッシュと内受容段を書き込む。
  - `balk_queue`(関数): 待ち行列からの離脱(離脱閾値・``INTERRUPTED``=「途中打ち切り(混雑・閉鎖)」)。
  - `begin_exit_walk`(関数): **9a 退出を歩かせる**(D-115 ①): 計画の退出の体に**その体の路線のホーム**への乗車の意図を立てる。
  - `begin_planned_sleep`(関数): **就寝境界に達した体を寝かせる**(D-62 (a)「就寝は計画の実行」・2026-09-10 決定)。
  - `begin_walk_to`(関数): 〔第 6 期 6-2 カレンダー 1b〕本人が決めた行き先のセルへ歩き出す(体の基本動作「歩く」=決定 10-12 §1-4 D1)。
  - `clear_board_intent`(関数): 乗車の意図(``board_line``/``board_since``)を落とす(9a: 計画の退出を即時に切り替えた体)。
  - `clear_intent`(関数): 意図を消す(計画境界・割り込み・経路の行き止まり=段 2c)。結果コードは書かない。
  - `clear_refractory`(関数): 呼んだ個体×条件の不応期タイマーを**戻す**(艦隊の繰り延べ=「呼が成立しなかった」)。
  - `collect_waste`(関数): 廃棄物収集(店舗の廃棄ビン→bbox 外)。搬出質量[g]を返す(棚は動かない)。
  - `consume`(関数): 消費(世帯の所持 → sink)。個体側は ``holdings``(個数)、SKU 別は台帳側の合計。
  - `discard_to_bin`(関数): 売れ残りを廃棄ビンへ(棚→ビン)。**棚が減るので写しの書き戻しが要る**。
  - `end_conversation`(関数): 〔11-03 M10〕終わったセッションの参加者を解放する(行動契約書 §3「終了はエンジン」)。
  - `energy_home_meal`(関数): **第2波 §2B 項 2(Q35 (a))** 範囲内の自宅の食事行=予定の実行(``engine.energy.HomeMeals.due``)。
  - `energy_out_of_area_meal`(関数): 範囲外の食事(K9 (a)): 域外に居る体の予定の食事=時間帯の比 × EER・``since_meal=0``。
  - `fail_intent`(関数): 意図を**失敗で終える**(段 2c の満了=``TOO_FAR``)。
  - `initialize`(関数): 個体を自宅セルに置き、所持金・種別・内受容の初期段を設定する(**ランの最初に1回**)。
  - `initialize_energy`(関数): 体の定数(体重・EER)を抽選し、食後の消費・収支・``hunger`` の写しと段を置く(ラン開始時 1 回)。
  - `intent_kept_by`(関数): 意図を持つ体に適用する行為が意図を**保つ**か(段 2c・親決定 Q20・**読むだけ**)。
  - `join_conversation`(関数): **3 人目の参加**(C10 8a・D-93 (d)・``--conv-max-participants 3`` のランだけ)。
  - `nav_place`(関数): ランの頭(nav1): 体を節の点へ置き、セルと層を面から導く(初期化と域外の配置の後に 1 回・再開では呼ばない)。
  - `normalized_refractory_scale`(関数): ``refractory_scale`` を manifest 欄用に正規化する(``{条件名: 倍率}``・名前昇順)。
  - `place_at_external`(関数): 域外ノードに個体を置く(U10 §1.1「域外は方面別の外界ノード」・ランの最初)。
  - `rail_arrive`(関数): 列車の到着で域外ノードの個体をホームのセルへ降ろす(域外→bbox)。
  - `rail_depart`(関数): 列車の発車で乗客を域外ノードへ運び出す(bbox→域外)。
  - `refractory_ticks`(関数): **ランの実効不応期表**[tick]\(知覚契約書 §6 の 11 行)。
  - `relabel_intent_failure`(関数): 既に書かれた失敗(移動の ``UNREACHABLE``)の**主語を意図の行為に**して意図を消す(段 2c)。
  - `release_indoor`(関数): 在席の解除(回転率=滞在上限・16行表 行2 の expedient)。
  - `request_open_close`(関数): 役割行動「開閉店」(行動契約書 §2.2)。権利=当該 POI の担当従業者(権利台帳の ``employ`` の行)。
  - `restock`(関数): 店舗補充・納品(外界→棚)。代金は域外仕入(店舗→外界)で払う。
  - `restore_items`(関数): 10d: 保存した外の状態(``engine.resume.collect_items`` の形)を持ち主の属性へ戻す。返り値=戻した数。
  - `restore_soa`(関数): 10d: 保存した SoA の列(``engine.resume.collect_soa`` の形)を戻す。返り値=戻した列の数。
  - `revert_conversation`(関数): 招待が不応答/ゲート却下だったとき、resolve が CONVERSING にした招待側を IDLE へ戻す。
  - `set_activity`(関数): **活動の持続と種別**を書く(二層の段 2・``engine.activity`` が値を決める・書き手は本関数)。
  - `set_activity_until`(関数): ``activity_until`` だけを書き換える(到着・会話成立の満了=二層の段 2)。
  - `set_conversing`(関数): 会話成立時に**両側**を CONVERSING にする(C6・09-09)。
  - `set_initial_activity`(関数): tick 0 の ``activity`` を**計画(W17)の 0:00 時点の活動**から立てる(D-62 (b))。
  - `set_intent`(関数): **意図を立てる**(段 2c・値は ``engine.intent`` が決める)。
  - `set_notice_state`(関数): 知覚側 SoA(M12: 向き量子化+課題従事フラグ)を書く(**書き込み口は resolve 一本**)。
  - `set_open_flags`(関数): POI の営業フラグ上書き欄を書く(-1=上書きなし / 0=閉 / 1=開)。
  - `set_plan_state`(関数): ``plan_flags``(D-66 計画実行層の欄)への**唯一の書き込み口**(〔第330・RET〕K15 で ``plan_activity`` を消した)。
  - `set_refractory`(関数): 呼んだ個体×条件の不応期タイマーを張る(知覚契約書 §6 運用規定②)。
  - `set_thermal`(関数): 体感温度(内受容3変数の1本)を一括代入する(知覚契約書 §3 内受容・日陰係数0.86)。
  - `sync_transit_activity`(関数): ``transit_state`` を正として ``activity`` を整える(乗車中=``RIDING``)。
  - `talk_within_reach`(関数): 会話が届くか(**C9b G7**)。``by_distance=False`` は現行の「同一セル代理」。
  - `wake_condition_index`(関数): ``refractory_scale`` の鍵 → ``WakeCondition`` の列番号。
  - `wake_from_plan`(関数): **非就寝の計画境界に達した体を起こす**(D-62 (a) の対称形)。
  - `write_familiarity`(関数): **親しみの表の行を書く**(4 段目・値と行の選び方は ``engine.familiarity`` が決める)。
  - `write_memory`(関数): **記憶の表の行を書く**(6 段目 6a・値と行の選び方は ``engine.memory`` が決める)。
  - `write_relations`(関数): **関係辺を書く**(C10 8a・値と辺の選び方は ``engine.relations`` が決める)。
  - `write_store_memory`(関数): **店の評価の記憶の行を書く**(D-120 7a・値と行の選び方は ``engine.memory`` が決める)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.economy.stage2_bind`・`shibuya.engine.change_detect`・`shibuya.engine.commit`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`・`shibuya.runtime.state.hashes`・`shibuya.runtime.state.ledger`・`shibuya.runtime.state.resume`・`shibuya.world.body.energy`・`shibuya.world.body.rules`・`shibuya.world.model.geometry`・`shibuya.world.model.state`
- 呼び手: `shibuya.act.activity`・`shibuya.act.intent`・`shibuya.cli`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar_self`・`shibuya.engine.duties.layer`・`shibuya.engine.presence`・`shibuya.engine.relations`・`shibuya.engine.run`・`shibuya.engine.systems.static_check`・`shibuya.mind.memory.familiarity`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.store_memory`・`shibuya.runtime.systems.act`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.body`・`shibuya.runtime.systems.decide`・`shibuya.runtime.systems.judge`・`shibuya.runtime.systems.perceive`・`shibuya.runtime.systems.talk`・`shibuya.world.laws.civic`・`shibuya.world.laws.crowd`・`shibuya.world.laws.environment`・`shibuya.world.laws.goods_flow`・`shibuya.world.laws.opening`・`shibuya.world.laws.rail`・`shibuya.world.laws.runner`・`shibuya.world.laws.salient`・`tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c7/attr_arms.py`・`tools/c7/occupancy_series.py`
- 読む試験: `tests/bench/test_refr20b_tool.py`・`tests/c6/test_t3_parallel_invariance.py`・`tests/c7/test_attr_arms.py`・`tests/economy/test_single_write_path.py`・`tests/engine/body/test_body_same_values.py`・`tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/discard_probe.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/processes/conftest.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_goods_flow.py`・`tests/engine/processes/test_opening.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/proximity/test_rule.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/rights/test_no_permission_count.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_staff_of_poi_equivalence.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/systems/test_systems_table.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_add_at_guard.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/llm/test_fleet_contract.py`
- 読む試験(道筋で): `tests/economy/cp2/test_cp2_write_window.py`・`tests/economy/stage2/test_stage2_writers.py`・`tests/engine/systems/test_fix_guards.py`・`tests/test_places_guard.py`・`tests/tools/test_pkgmove.py`
- 書きの許可
  - `_advance_focus`: 直接の書き `agents.focus_target`・`agents.focus_ttl`
  - `_apply_alight`: 直接の書き `agents.activity`・`agents.node`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`
  - `_apply_board`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.queue_poi`・`agents.queue_since`・`agents.target_node`
  - `_apply_buy`: 直接の書き `agents.activity`・`agents.queue_poi`・`agents.queue_since`
  - `_apply_eat`: 直接の書き `agents.activity`・`agents.queue_poi`・`agents.queue_since`
  - `_apply_engine_step`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.edge_id`・`agents.edge_s`・`agents.node`・`agents.path_next_node`・`agents.sleep_pending`・`agents.target_node`
  - `_apply_leave`: 直接の書き `agents.activity`・`agents.talk_partner`
  - `_apply_move`: 直接の書き `agents.activity`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`agents.queue_since`・`agents.target_node`
  - `_apply_rest`: 直接の書き `agents.activity`・`agents.fatigue`
  - `_apply_sleep`: 直接の書き `agents.activity`・`agents.target_node`
  - `_apply_talk`: 直接の書き `agents.activity`・`agents.talk_partner`
  - `_apply_wait`: 直接の書き `agents.activity`
  - `_board_riders`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.money`・`agents.node`・`agents.poi_ref`・`agents.queue_poi`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`
  - `_clear_focus`: 直接の書き `agents.focus_target`・`agents.focus_ttl`
  - `_clear_intent_fields`: 直接の書き `agents.intent_action`・`agents.intent_kind`・`agents.intent_since`・`agents.intent_target`
  - `_complete_buy`: 直接の書き `agents.activity`・`agents.holdings`・`agents.hunger`・`agents.money`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`pois.revenue`・`pois.stock`
  - `_complete_eat`: 直接の書き `agents.activity`・`agents.hunger`・`agents.money`・`agents.poi_ref`・`agents.poi_since`・`agents.queue_poi`・`pois.revenue`
  - `_energy_meal`: 直接の書き `agents.energy_balance`・`agents.hunger`・`agents.since_meal_kcal`
  - `_energy_snack`: 直接の書き `agents.energy_balance`・`agents.hunger`・`agents.since_meal_kcal`
  - `_enter_board_queue`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.target_node`
  - `_fail`: 直接の書き `agents.last_result`・`agents.last_result_tick`
  - `_nav_positions`: 直接の書き `agents.band`・`agents.cell`・`agents.nav_fi`・`agents.nav_node`・`agents.nav_t`・`agents.nav_tgt`・`agents.nav_wait`・`agents.xy`
  - `_nav_step`: 直接の書き `agents.nav_fi`・`agents.nav_node`・`agents.nav_of`・`agents.nav_ox`・`agents.nav_oy`・`agents.nav_t`・`agents.nav_tgt`・`agents.nav_wait`・`agents.node`・`agents.xy`
  - `_nav_stop`: 直接の書き `agents.nav_node`・`agents.nav_t`・`agents.nav_tgt`・`agents.nav_wait`・`agents.node`・`agents.xy`
  - `_ok`: 直接の書き `agents.last_result`・`agents.last_result_tick`
  - `_serve_board_queue`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`
  - `_serve_poi_queue`: 直接の書き `agents.activity`・`agents.queue_poi`・`agents.queue_since`
  - `_set_focus`: 直接の書き `agents.focus_target`・`agents.focus_ttl`
  - `_settle_approach`: 直接の書き `agents.focus_target`・`agents.focus_ttl`
  - `_stage2_withdraw`: 直接の書き `agents.money`
  - `advance_body`: 直接の書き `agents.energy_balance`・`agents.fatigue`・`agents.hunger`・`agents.since_meal_kcal` 口として持つ系: body
  - `apply`: 直接の書き `agents.band`・`agents.board_line`・`agents.board_since`・`agents.cell`・`agents.edge_id`・`agents.edge_s`・`agents.last_action`・`agents.last_result`・`agents.last_result_tick`・`agents.node`・`agents.path_next_node`・`agents.sleep_pending`・`agents.xy`・`cells.density`・`cells.density_stage`・`cells.open_count` 口として持つ系: phase_c
  - `apply_detection`: 直接の書き `agents.fatigue_stage`・`agents.hunger_stage`・`agents.thermal_stage`・`cells.b4_hash` 口として持つ系: detect
  - `balk_queue`: 直接の書き `agents.activity`・`agents.last_result`・`agents.last_result_tick`・`agents.queue_poi`・`agents.queue_since` 口として持つ系: plan_boundary・presence・world
  - `begin_exit_walk`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.target_node` 口として持つ系: plan_boundary・presence
  - `begin_planned_sleep`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.sleep_pending`・`agents.target_node` 口として持つ系: plan_boundary・presence
  - `begin_walk_to`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.sleep_pending`・`agents.target_node` 口として持つ系: calendar_2・presence
  - `clear_board_intent`: 直接の書き `agents.board_line`・`agents.board_since` 口として持つ系: presence
  - `clear_intent`: 直接の書き (なし) 口として持つ系: activity_intent
  - `clear_refractory`: 直接の書き `agents.refractory_until` 口として持つ系: wake_filter
  - `collect_waste`: 直接の書き (なし) 口として持つ系: world
  - `consume`: 直接の書き `agents.holdings` 口として持つ系: world
  - `discard_to_bin`: 直接の書き `pois.stock` 口として持つ系: duties・world
  - `end_conversation`: 直接の書き `agents.activity`・`agents.talk_partner` 口として持つ系: apply_responses・conversation
  - `energy_home_meal`: 直接の書き `agents.hunger_stage` 口として持つ系: home_meal
  - `energy_out_of_area_meal`: 直接の書き (なし) 口として持つ系: body
  - `fail_intent`: 直接の書き `agents.activity`・`agents.last_action`・`agents.last_result`・`agents.last_result_tick`・`agents.target_node` 口として持つ系: activity_intent
  - `initialize`: 直接の書き `agents.activity`・`agents.age`・`agents.band`・`agents.cell`・`agents.fatigue`・`agents.hunger`・`agents.kind`・`agents.money`・`agents.node`・`agents.sex`・`agents.thermal`・`agents.xy`・`cells.density`・`cells.density_stage`・`cells.open_count` 口として持つ系: build
  - `initialize_energy`: 直接の書き `agents.eer_kcal`・`agents.energy_balance`・`agents.hunger`・`agents.hunger_stage`・`agents.since_meal_kcal`・`agents.weight_kg` 口として持つ系: build
  - `intent_kept_by`: 直接の書き (なし) 口として持つ系: phase_a
  - `join_conversation`: 直接の書き `agents.activity`・`agents.last_result`・`agents.last_result_tick`・`agents.talk_partner` 口として持つ系: conversation
  - `nav_place`: 直接の書き `cells.density`・`cells.density_stage`
  - `place_at_external`: 直接の書き `agents.activity`・`agents.board_line`・`agents.board_since`・`agents.cell`・`agents.node`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state` 口として持つ系: build
  - `rail_arrive`: 直接の書き `agents.activity`・`agents.band`・`agents.cell`・`agents.node`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state`・`agents.xy` 口として持つ系: build・close_final・day_close・plan_boundary・presence・world
  - `rail_depart`: 直接の書き `agents.activity`・`agents.cell`・`agents.node`・`agents.target_node`・`agents.transit_ref`・`agents.transit_state` 口として持つ系: close_final・day_close・plan_boundary・presence・world
  - `relabel_intent_failure`: 直接の書き `agents.last_action` 口として持つ系: activity_intent
  - `release_indoor`: 直接の書き `agents.activity`・`agents.poi_ref`・`agents.poi_since` 口として持つ系: plan_boundary・presence・world
  - `request_open_close`: 直接の書き `agents.last_result`・`agents.last_result_tick`・`pois.open_now` 口として持つ系: duties・world
  - `restock`: 直接の書き `pois.stock` 口として持つ系: duties・world
  - `restore_items`: 直接の書き (なし) 口として持つ系: build
  - `restore_soa`: 直接の書き (なし) 口として持つ系: build
  - `revert_conversation`: 直接の書き `agents.activity`・`agents.talk_partner`
  - `set_activity`: 直接の書き `agents.activity_kind`・`agents.activity_until` 口として持つ系: activity_intent・presence
  - `set_activity_until`: 直接の書き `agents.activity_until` 口として持つ系: activity_intent
  - `set_conversing`: 直接の書き `agents.activity`・`agents.talk_partner` 口として持つ系: apply_responses・conversation
  - `set_initial_activity`: 直接の書き `agents.activity` 口として持つ系: build
  - `set_intent`: 直接の書き `agents.intent_action`・`agents.intent_kind`・`agents.intent_since`・`agents.intent_target` 口として持つ系: activity_intent
  - `set_notice_state`: 直接の書き `perception.heading`・`perception.task_flag` 口として持つ系: world
  - `set_open_flags`: 直接の書き `pois.open_now` 口として持つ系: world
  - `set_plan_state`: 直接の書き `agents.plan_flags` 口として持つ系: build・close_final・day_close・day_head・plan_boundary・presence・world
  - `set_refractory`: 直接の書き `agents.refractory_until` 口として持つ系: decide
  - `set_thermal`: 直接の書き `agents.thermal` 口として持つ系: world
  - `sync_transit_activity`: 直接の書き `agents.activity` 口として持つ系: close_final・day_close・world
  - `talk_within_reach`: 直接の書き (なし) 口として持つ系: apply_responses・conversation・decide
  - `wake_from_plan`: 直接の書き `agents.activity`・`agents.sleep_pending` 口として持つ系: plan_boundary・presence
  - `write_familiarity`: 直接の書き `agents.fam_exposures`・`agents.fam_first`・`agents.fam_last`・`agents.fam_thing`・`agents.fam_visits` 口として持つ系: familiarity
  - `write_memory`: 直接の書き `agents.mem_cell`・`agents.mem_importance`・`agents.mem_kind`・`agents.mem_last`・`agents.mem_n`・`agents.mem_object`・`agents.mem_partner`・`agents.mem_result`・`agents.mem_tick` 口として持つ系: decide・llm_receive・memory
  - `write_relations`: 直接の書き `agents.rel_first`・`agents.rel_kind`・`agents.rel_last`・`agents.rel_n`・`agents.rel_partner`・`agents.rel_sign` 口として持つ系: build・memory・relations_wake
  - `write_store_memory`: 直接の書き `agents.sm_first`・`agents.sm_last`・`agents.sm_n`・`agents.sm_poi`・`agents.sm_precision`・`agents.sm_source`・`agents.sm_valence` 口として持つ系: decide・llm_receive・memory
- 決定の ID: 10-12/§1-4・11-03・11-03/§2・11-03/§3・11-09・D-49・D-51・D-56・D-62・D-66・D-71・D-93・D-112・D-113・D-115・D-116・D-118・D-120・第 263・第 266・第 267・第 268・第 275・第 275 #2・第 288・第 288 #54・第 302・第 330・第 346

## [rng_audit.py](../../../../../../../src/shibuya/engine/rng_audit.py)

K19 の検査(10f・K25 (a)): ``core.rng`` の流れが 1 ブロック(4 語)を超えて引き、隣の鍵の流れとブロックが重なるか。

- 公開の関数とクラス
  - `DomainStats`(クラス)
  - `StreamRecorder`(クラス): ``core.rng.philox`` を包んで、作った流れを全部覚える(``install`` で入れ、``uninstall`` で戻す)。
  - `StreamSite`(クラス)
  - `check_overlaps`(関数): 実行時の数えの検査(空なら合格)。
  - `check_sites`(関数): 静的な一覧の検査(空なら合格)。
  - `recreated_for`(関数): ``check_overlaps`` に渡す作り直しの許可(既定の腕=``K19_RECREATED`` だけ・腕 port のラン=口の分を足す)。
  - `scan_sites`(関数): ``root``(= ``src/shibuya``)の下の ``stream()``・``philox()`` の呼び手(``core/rng.py`` と ``build/`` を除く)。
- import している内部モジュール: `shibuya.foundation.rng`
- 読む試験: `tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/proximity/test_rule.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_version_bump_10e.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 決定の ID: 第 330・第 346

## [run.py](../../../../../../../src/shibuya/engine/run.py)

engine.run — 1 シミュ日の mock ラン(予算行 **W2**)と CLI。

- 公開の関数とクラス
  - `Checkpoint`(クラス): checkpoint 1 点の状態ハッシュ(T1/T2 の一致判定)。
  - `RunResult`(クラス): 1 ランの結果。
  - `add_calendar_args`(関数): 暦の口の引数(10a・A1-1・A1-2。``engine.run`` と ``shibuya.cli`` で同じ綴りにするため 1 か所に置く)。
  - `add_fleet_args`(関数): 実艦隊の共通引数(``engine.run`` と ``shibuya.cli`` で同じ綴りにするため 1 か所に置く)。
  - `calendar_kwargs_from_args`(関数): ``add_calendar_args``(10d の ``--sim-days``・``--resume-from``・``--state-out``・10e の ``--weather-perturb`` を含む)の
  - `check_replay_tape`(関数): 〔第330・RET〕再生するテープが今の版で録られたかを確かめる(違えば止める=警告ではなく例外)。
  - `classical_acq_addressable`(関数): 第2波 §2A 項 3-1(検収後): 古典の交際の候補の A から、話しかけられない相手(会話中・就寝中=
  - `decision_layers_summary`(関数): 5b(L4 (a)): 時 × 層 × 起床入口 の判断数 → manifest の形(割合つき)。
  - `fleet_from_args`(関数): ``add_fleet_args`` の結果 → ``FleetClient``(``--llm mock`` なら ``None``)。
  - `main`(関数): ``python -m shibuya.engine.run --agents 5000 --seed 1 --world data/world/v2``。
  - `resolve_environment_seed`(関数): 10f 第 2 段の直し(S1): 環境の seed(``resolve_sub_seed`` と同じ)。
  - `resolve_population_seed`(関数): 10f(K21 (a)): 母集団の seed(``resolve_sub_seed`` と同じ)。
  - `resolve_sub_seed`(関数): 10f: 母集団・環境の seed(``None`` なら ``seed`` と同じ値=今と同じ)。
  - `run_day`(関数): 1 シミュ日(既定 1,440 tick)の mock ランを回す。
  - `run_salt_for`(関数): ``blake3(master_seed ‖ 0x1f ‖ "engine")`` の先頭 16 バイト(親の指定)。
- import している内部モジュール: `shibuya.act.activity`・`shibuya.act.intent`・`shibuya.agents.state`・`shibuya.engine.arbiter`・`shibuya.engine.calendar`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar_self`・`shibuya.engine.calendar_shadow`・`shibuya.engine.chooser`・`shibuya.engine.commit`・`shibuya.engine.contact.layer`・`shibuya.engine.duties.layer`・`shibuya.engine.llm_bridge`・`shibuya.engine.poi_target`・`shibuya.engine.presence`・`shibuya.engine.relations`・`shibuya.engine.resolve`・`shibuya.experiments.port.layer`・`shibuya.experiments.port.run_kind`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.growth`・`shibuya.foundation.manifest.schema`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.ports.percept`・`shibuya.foundation.queues.batching`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.rng`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.foundation.vocab.actions`・`shibuya.llm.fleet`・`shibuya.llm.mock`・`shibuya.llm.undefined`・`shibuya.mind.judge.classical`・`shibuya.mind.judge.decision.layer`・`shibuya.mind.memory.familiarity`・`shibuya.mind.memory.memory`・`shibuya.mind.memory.store_memory`・`shibuya.mind.memory.wom`・`shibuya.perception.renderer`・`shibuya.runtime.clocks.regional`・`shibuya.runtime.clocks.speech`・`shibuya.runtime.clocks.step_scope`・`shibuya.runtime.inference.tape`・`shibuya.runtime.state.growth_decl`・`shibuya.runtime.state.hashes`・`shibuya.runtime.state.ledger`・`shibuya.runtime.systems.conductor`・`shibuya.society.speech.layer`・`shibuya.world.assets`・`shibuya.world.body.energy`・`shibuya.world.body.model`・`shibuya.world.facts.population_reader`・`shibuya.world.facts.rights.record`・`shibuya.world.facts.rules.table`・`shibuya.world.laws.opening`・`shibuya.world.model.geometry`・`shibuya.world.model.proximity`・`shibuya.world.model.space.nav1`・`shibuya.world.model.state`
- 呼び手: `shibuya.cli`・`shibuya.runtime.systems.act`・`shibuya.runtime.systems.assemble`・`shibuya.runtime.systems.body`・`shibuya.runtime.systems.decide`・`shibuya.runtime.systems.judge`・`shibuya.runtime.systems.llm_io`・`shibuya.runtime.systems.observe`・`shibuya.runtime.systems.perceive`・`shibuya.runtime.systems.report`・`shibuya.runtime.systems.run_end`・`shibuya.runtime.systems.state_io`・`tools/c6/run_hash.py`・`tools/c7/occupancy_series.py`・`tools/instruments/anchor_gauge.py`
- 読む試験: `tests/build_pop/test_pop_pipeline.py`・`tests/c6/test_l4_l6_budget.py`・`tests/c6/test_t5_order_bias.py`・`tests/c6/test_t9_diagnostics.py`・`tests/economy/cp2/test_cp2_flow_sum.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_writes_declared.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/engine/batching/test_conductor_windows.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/body/test_body_reserve.py`・`tests/engine/body/test_meal_default_w17.py`・`tests/engine/body/test_system1_placeholders.py`・`tests/engine/bridging/test_bridging_ledger.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/test_c1_event_log_onoff.py`・`tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/decision/test_j0_cause_columns.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_other_ratio_field.py`・`tests/engine/decision/test_j0_shuffle_invariance.py`・`tests/engine/decision/test_j0_writes_declared.py`・`tests/engine/discard_probe.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_log_invariance.py`・`tests/engine/events/test_e_log_links_actual.py`・`tests/engine/events/test_e_log_schema.py`・`tests/engine/events/test_e_manifest_events.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_recall_equivalence.py`・`tests/engine/memory/test_m0_render_bytes.py`・`tests/engine/memory/test_m0_shown_recorded.py`・`tests/engine/memory/test_m0_writes_declared.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/multiday/test_md23_resume.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/rights/test_rights_manifest.py`・`tests/engine/speech/_s8b.py`・`tests/engine/speech/test_speech_writes_declared.py`・`tests/engine/state/shaped_names.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/systems/test_boxes.py`・`tests/engine/systems/test_guard_runs.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_activation_10e.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_assets_10e_b0_b1.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_calendar_10e_e3.py`・`tests/engine/test_calendar_sites.py`・`tests/engine/test_census_out.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_conversation.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_determinism_t1_t2_t4.py`・`tests/engine/test_eatery_place_food.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_familiarity.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_intent_mode_open.py`・`tests/engine/test_l4_budget.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_mock_day_w2.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_norm_meter.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_executor.py`・`tests/engine/test_processes_run.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_tenure.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_sleep_suppression_d56.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_t3_manifest.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/test_vocab_v2_eat.py`・`tests/engine/test_wom.py`・`tests/engine/time/test_t0_tickctx_equivalence.py`・`tests/engine/time/test_t0_tm9_fields.py`・`tests/engine/time/test_v30a_key_sites.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/engine/tools/test_c0_phone_table_empty_and_declared.py`・`tests/engine/tools/test_c0_signboard_mark_invariance.py`・`tests/llm/test_mock_v3.py`・`tests/perception/facts/test_coef_removed_or_armed.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/perception/facts/test_percept_schema.py`・`tests/perception/test_ablation1.py`・`tests/perception/test_ablation6_signage.py`・`tests/perception/test_b6_invite.py`・`tests/perception/test_near_tiebreak.py`・`tests/perception/test_p_see_activity.py`・`tests/perception/test_signage_p_see_gate.py`・`tests/test_cli_l4_scale.py`
- 読む試験(道筋で): `tests/engine/rules/test_rules_table_schema.py`・`tests/engine/test_two_phase.py`・`tests/test_places_guard.py`・`tests/tools/test_bytecheck.py`・`tests/tools/test_commit_check.py`・`tests/tools/test_pkgmove.py`
- CLI の引数
  - `--ablate`: 止める過程(過程 id か AB-* の感度試験 id・複数可)
  - `--agents`
  - `--area-source`: 歩行可能面積の出所(C9c-1 G8 (b))。legacy=街路点×6.25 m²(既定・バイト不変)/ plateau=c9c_walkable_area.parquet(PLATEAU 歩道部+OSM×道路構造令の実測)
  - `--cells`: 合成世界のセル数
  - `--checkpoint-every`
  - `--day`: 曜日(0=月曜)
  - `--derive-rule`: 在圏ブロックの読み口(v2=§2 追補・v1=原則のまま)
  - `--endpoints`: カンマ区切り http://host:port(既定艦隊は 7 本=xxhash(call_id) mod 7)
  - `--environment-seed`: 10f 環境の seed(気象・大きな催し・道路工事。省略=--seed と同じ)
  - `--exit-mode`: 退出の実行形(immediate のみ実装・他は予約)
  - `--fleet-debug-dir`: 書式の原因分析用 jsonl の置き場(既定 off・診断のみ)。初回パースが落ちた呼の プロンプト/初回の生応答/再生成の生応答/実効・厳密の判定/理由 を 1 行 1 呼で書く
  - `--fleet-queue-capacity`: 艦隊の受理待ち+実行中の合計上限(既定 0=FleetConfig の既定 max_in_flight×4)。C7 本番(D-55/D-58): 計画呼数 2,709/tick に対し既定 1,792 だと 33.8%% が queue full で繰り延べ→テープに残らず再生不能。計画呼数以上(例 4096)にすると繰り延べ ≈0
  - `--fleet-wait-s`: ④′ で未応答が残るとき tick ごとに最大この秒数だけ艦隊を待つ(既定 0=純非ブロッキング・本番の運用は 120)
  - `--geometry`: 位置幾何(C9 G1/G2)。node=1 tick 1 ノード(既定・バイト不変)/edge=辺上の連続位置+希望速度 1.00〜1.60 m/s+Kladek 減速
  - `--group-norms`: 群・規範の計器(D-107 (a)・読むだけ)を回すか(第309 Q150・既定 on)
  - `--growth-yaml`: 状態成長宣言 YAML を出力して終了
  - `--holiday-csv`: 内閣府の祝日 CSV(cp932)。読めなければ開始日の検査で止める(既定 data/calendar/syukujitsu.csv)
  - `--llm`: LLM 経路(fleet=実 vLLM 艦隊・--endpoints 必須)
  - `--max-tokens`: T1 の max_tokens(既定 96=2 行形の最大 ≒70 tok に余裕・expedient)
  - `--mode`: 実行モード(cache_salt の勘定分離・record/replay とは別物)
  - `--model`: served-model-name(空なら /v1/models の先頭)
  - `--no-outside-suppression`: D-66 域外抑止を切る(=D-66 前の挙動・帰無腕)
  - `--no-plan-executor`: D-66 計画実行層(engine.presence)を切る(=現行挙動・帰無腕)
  - `--no-plan-sleep`: D-62「就寝は計画の実行」を切る(=D-62 前の挙動・帰無腕。就寝境界も LLM に判断させ・tick 0 は全員 SLEEPING)
  - `--no-population`: W16 母集団を使わず合成個体で回す(下限対照)
  - `--no-processes`: 世界過程(C4 第1陣)を止める(ablation の下限対照)
  - `--no-sleep-suppression`: D-56 就寝抑止を切る(=D-56 前の挙動・帰無腕)
  - `--population-seed`: 10f(K21 (a))母集団の seed(省略=--seed と同じ)。--seed は動きの seed(salt)
  - `--resume-from`: 再開する状態のファイル(10d・state-T<T>.npz)。設定は親と同じにする(違えば止める)
  - `--run-id`: manifest の run_id(cache_salt の第2要素)
  - `--school-holidays`: 学校の長期休みの区間 YYYY-MM-DD:YYYY-MM-DD をカンマ区切り(開始日の検査・既定は空)
  - `--seed`
  - `--sim-days`: 通しで回す日数(10d)。2 以上では各日の終わりに締め・日の頭の初期化は走らせない(既定 1)
  - `--start-date`: 開始日 YYYY-MM-DD(A1-1・manifest の start_sim_datetime)。空=2026-07-13(月)+ --day-index 日
  - `--state-out`: 状態の書き出し先のディレクトリ(10d)。各日の締めの後とランの最後に state-T<T>.npz を書く
  - `--tape`: 録画テープの出力先ディレクトリ
  - `--temperature`: T1 の温度(既定 0.7=知覚契約書 §2.5/卒業条件表・運用設計書 §1.3 の本番値。運用設計書 §1.2 の設定節は欄形だけで数値を持たない)
  - `--ticks`
  - `--weather-perturb`: 天気を揺らす(10e B6・アンサンブル)。窓の中でも同じ季節 × 平日/土休の層から天候型を日数の割合で引く(鍵は --environment-seed)。既定は付けない=その日の実際の天気
  - `--world`: 世界資産ディレクトリ(無ければ合成小世界へ落ちる)
- 決定の ID: 10-12/§1-6・11-01・11-02r・11-02r/§1・11-02r/§1 #7・11-03・11-03/§3・R-8・D-28・D-51・D-55・D-56・D-58・D-59・D-61・D-62・D-66・D-71・D-84・D-85・D-93・D-96・D-99・D-107・D-110・D-112・D-113・D-114・D-115・D-116・D-117・D-118・D-119・D-120・第 266・第 267・第 268・第 269・第 299・第 300・第 304・第 308・第 309・第 330・第 346
