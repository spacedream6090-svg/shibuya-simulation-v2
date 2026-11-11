# src/shibuya/engine

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 58 本・その他 0 本(このディレクトリの直下)

下のディレクトリ: [body](body/README.md)・[bridging](bridging/README.md)・[calendar2](calendar2/README.md)・[calendar3](calendar3/README.md)・[contact](contact/README.md)・[decision](decision/README.md)・[duties](duties/README.md)・[events](events/README.md)・[experiment](experiment/README.md)・[processes](processes/README.md)・[rights](rights/README.md)・[rules](rules/README.md)・[space](space/README.md)・[speech](speech/README.md)・[systems](systems/README.md)・[tools](tools/README.md)

## [__init__.py](../../../../../../../src/shibuya/engine/__init__.py)

engine: 時計/スケジューラ/繰り延べアービタ/resolve/二相コミット=世界状態への唯一の書き込み口。

- import している内部モジュール: `shibuya.engine.arbiter`・`shibuya.engine.change_detect`・`shibuya.engine.clock`・`shibuya.engine.commit`・`shibuya.engine.tape`
- 読む試験(道筋で): `tests/tools/test_bytecheck.py`・`tests/tools/test_pkgmove.py`

## [absent_processes.py](../../../../../../../src/shibuya/engine/absent_processes.py)

engine.absent_processes — 「無い」と宣言した世界過程 5 件を止める切替口(指示書 11-02 返事その 2 §1 #7・小さな版上げ 1 回分)。

- 公開の関数とクラス
  - `arm`(関数): いまの腕(``stopped``=既定・``legacy``=切替口)。組み立てのときに読む。
  - `check_resume`(関数): 再開のときに、保存したランの腕(見出しの ``absent_processes``・無ければ legacy)と今の腕が同じかを確かめる(違えば止める)。
  - `header_fields`(関数): 状態のファイルの見出しの ``absent_processes``(legacy のランは書かない=None=版上げの前の見出しのまま)。
  - `is_legacy`(関数): ``mode``(省略=今の腕)が旧道(5 件の過程を動かす)か。
  - `manifest_fields`(関数): manifest の ``absent_processes``(設定=形の版・腕・過程の宣言・止めた印/観測=旧道の件数)。
  - `resolve`(関数): 過程の引数の腕(``None``=今の腕)を名に直す(名の誤りは止める)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--absent-processes``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
  - `stopped_flags`(関数): 過程ごとの ``absent_<名>_stopped``(1=止めた・0=旧道)。腕だけで決まる印(設定)。
- 呼び手: `shibuya.cli`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.logistics`・`shibuya.engine.processes.runner`・`shibuya.engine.systems.build`・`shibuya.engine.systems.report`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/bridging/test_drives_from_vs_scoring.py`・`tests/engine/processes/test_absent_processes_1102.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/processes/test_salient.py`・`tests/engine/test_resume_10d.py`
- 環境変数: `SHIBUYA_ABSENT_PROCESSES`
- 決定の ID: 10-13b/§0-6・11-01/§2・11-02・11-02r・11-02r #7・11-02r/§1・11-02r/§1 #7・11-02r/§1 #8・11-02r/§2-2

## [activity.py](../../../../../../../src/shibuya/engine/activity.py)

engine.activity — 行為と活動の二層の**活動層**(二層の実装 段 2・D-116・第276)。

- 公開の関数とクラス
  - `ActivityLayer`(クラス): 活動層(``engine.run`` が ``vocab_version="v3"`` かつ ``activity=True`` のときだけ作る)。
  - `ActivityPayload`(クラス): 1 応答ぶんの活動(パーサ v3 の欄を運ぶだけ)。
  - `activity_kind_of`(関数): 行動コード(と「あたり」の印)→ ``ActivityKind``(expedient・モジュール注記)。
  - `displayable_activity`(関数): B4b に出せる活動文か(なし・空・§2.4 ⑧ の個体依存語・⑥ の省略記法を含む文は出さない)。
  - `payload_of`(関数): ``BridgeResult``/艦隊の ``Outcome`` → 活動(語彙 v3 の応答だけ・それ以外は ``None``)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.foundation.hashing`・`shibuya.foundation.text.normalize`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.engine.intent`・`shibuya.engine.run`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/space/test_nav1_units.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/time/test_t0_time_consts.py`
- 状態台帳の行
  - 持ち主 `act_layer`(`ActivityLayer`)
    - `O1` ActivityLayer text・until_kind(挙動 behavior・復元 required) 道筋 `act_layer.text`・`act_layer.until_kind` 書ける系: activity_intent・presence
    - `O2` ActivityLayer text_id・_texts・_text_ids・_digest_cache(挙動 no・復元 derivable) 道筋 `act_layer._digest_cache`・`act_layer._text_ids`・`act_layer._texts`・`act_layer.text_id` 書ける系: activity_intent・checkpoint・close_final・day_close・presence
    - `O3` ActivityLayer _bt_agent・_bt_tick・_bt_start(挙動 no・復元 derivable) 道筋 `act_layer._bt_agent`・`act_layer._bt_start`・`act_layer._bt_tick` 書ける系: activity_intent
    - `O66` ActivityLayer の計数(挙動 diag・復元 discardable) 道筋 `act_layer.kind_counts`・`act_layer.n_arrival_expired`・`act_layer.n_cell_suppressed`・`act_layer.n_expiry_candidates`・`act_layer.n_fail_immediate`・`act_layer.n_intent_moves`・`act_layer.n_leave_expired`・`act_layer.n_partner_expired`・`act_layer.n_set`・`act_layer.n_wander_bad`・`act_layer.n_wander_steps` 書ける系: activity_intent・apply_responses・detect・phase_a・phase_c・presence
- 決定の ID: D-62・D-112・D-116・第 275・第 276

## [arbiter.py](../../../../../../../src/shibuya/engine/arbiter.py)

engine.arbiter — 繰り延べアービタ(知覚契約書 §6 の裁定規則)。

- 公開の関数とクラス
  - `Arbiter`(クラス): 毎tick の裁定+保留の持ち越し+診断計数の積み上げ(1 シミュ日ぶん)。
  - `ArbiterDecision`(クラス): 1 tick 分の裁定結果(純関数 ``arbitrate`` の出力)。
  - `WakeCandidates`(クラス): 1 tick 分の起床候補(全て同じ長さの配列)。
  - `arbitrate`(関数): 繰り延べアービタの**純関数**本体(入力の並び順に依存しない)。
  - `call_budget_per_tick`(関数): 予算行 L4 を tick あたり・当該規模へ按分した呼数。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.hashing`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`
- 呼び手: `shibuya.cli`・`shibuya.engine`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.judge`
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
- 呼び手: `shibuya.engine.activity`・`shibuya.engine.classical`・`shibuya.engine.energy`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.opening`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.runner`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.report`
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
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar_shadow`・`shibuya.engine.decision.sources`・`shibuya.engine.presence`・`shibuya.engine.resolve`・`shibuya.engine.tools.registry`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.hashing`・`shibuya.foundation.journal.log`・`shibuya.foundation.ports.decision`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.run`・`shibuya.engine.systems.build`
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
- import している内部モジュール: `shibuya.agents.weekly`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar3.roster`・`shibuya.engine.calendar_self`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`tools/instruments/anchor_gauge.py`
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
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.text.hashes`・`shibuya.foundation.text.normalize`・`shibuya.foundation.text.templates`・`shibuya.perception.renderer`・`shibuya.world.assets`・`shibuya.world.state`
- 呼び手: `shibuya.engine`・`shibuya.engine.body.rules`・`shibuya.engine.geometry`・`shibuya.engine.resolve`・`shibuya.engine.step_scope`・`shibuya.engine.systems.build`
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
- 呼び手: `shibuya.cli`・`shibuya.engine.classical`・`shibuya.engine.poi_target`・`shibuya.engine.run`・`shibuya.engine.store_choice`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/space/test_nav1_units.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_intent_chooser.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `poi_resolver.chooser`(`ClassicalChooser`)
    - `O25` ClassicalChooser last_habit・stats(挙動 diag・復元 discardable) 道筋 `poi_resolver.chooser.last_habit`・`poi_resolver.chooser.stats` 書ける系: apply_responses
  - 持ち主 `poi_resolver.chooser` の別のクラス `NearestChooser`(行は `shibuya.engine.chooser` のカードを見る)
- 決定の ID: 09-25・D-114・D-118・D-119・D-120・第 292

## [class_ids.py](../../../../../../../src/shibuya/engine/class_ids.py)

engine.class_ids — クラスの名の固定の表(移す段 1・返事その 7 §4-2 の 3)。

- 公開の関数とクラス
  - `class_id`(関数): 型の凍結の名。表 → クラスの宣言(:data:`DECLARED_ATTR`)の順に引く。どちらにも無い ``shibuya`` の型は止める。
  - `class_path`(関数): 凍結の名 → 今の「モジュール.クラス名」(状態のファイルを読むときに import する先。表に無い名はそのまま)。
- 呼び手: `shibuya.engine.resume`・`shibuya.engine.state_codec`・`shibuya.engine.state_hashes`・`shibuya.engine.systems.probe`
- 読む試験: `tests/engine/state/test_class_ids.py`・`tests/engine/test_state_format_10f.py`

## [classical.py](../../../../../../../src/shibuya/engine/classical.py)

engine.classical — System 1.5 の古典的選択モデル=方策 ``classical``(5 段目 5b・D-119 L1〜L8・第292)。

- 公開の関数とクラス
  - `ActivityPrior`(クラス): 錨 → 配列 ``rates[性 2, 就業 2, 年齢 16(0=総数), 活動 19, 時刻 96]``(行動者率 %)。
  - `ClassicalPolicy`(クラス): 方策 ``classical``(LLM 0 呼)。``bind`` のあとで ``complete`` が使える。
  - `check_activity_region`(関数)
  - `check_classical_social`(関数)
  - `check_meal_gate`(関数)
  - `check_policy`(関数)
  - `day_kind_of`(関数): ``day_index``(0=月曜)→ 錨の曜日の鍵(平日/土曜/日曜)。
  - `ipf_constants`(関数): 1 次元 IPF(L7 (a)): 乗数を掛けたあとの**集団の周辺**を事前分布の周辺に戻す定数 c(活動ごと)。
  - `load_activity_prior`(関数): 事前分布の錨(追跡ファイル)を読む → ``(辞書, md5)``。
  - `meal_gate_interval_p`(関数): 1 時間あたりの確率 ``p_hour`` → 経過 ``dt_minutes`` 分の間に 1 回以上通る確率 ``1 − (1 − p)^(Δt/60)``。
  - `ok_self`(関数): 体 ``aid`` 自身が食事中か(同じセルの食事中の人数から自分を引くため)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.calendar`・`shibuya.engine.chooser`・`shibuya.foundation.paths`・`shibuya.foundation.rng`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`・`shibuya.llm`・`shibuya.llm.mock`
- 呼び手: `shibuya.cli`・`shibuya.engine.experiment.branch`・`shibuya.engine.experiment.switch`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`tools/instruments/dm_eval/judge.py`
- 読む試験: `tests/engine/space/test_nav1_units.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_on_reaches_addressee.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_calendar.py`・`tests/engine/test_classical_policy.py`・`tests/engine/test_classical_social.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_state_checks_10f.py`
- 状態台帳の行
  - 持ち主 `classical`(`ClassicalPolicy`)
    - `O20` ClassicalPolicy _prev(挙動 behavior・復元 required) 道筋 `classical._prev` 書ける系: decide
    - `O21` ClassicalPolicy _gate_hazard(EnergyLayer meal_reset と同じ配列)(挙動 behavior・復元 required) 道筋 `classical._gate_hazard` 書ける系: body・decide・home_meal・phase_c
    - `O22` ClassicalPolicy _condition・_tick・_eating_tick・_eating_cells(挙動 no・復元 discardable) 道筋 `classical._condition`・`classical._eating_cells`・`classical._eating_tick`・`classical._tick` 書ける系: decide
    - `O23` ClassicalPolicy _b_tick・_b_off・counts・by_hour(挙動 no・復元 derivable) 道筋 `classical._b_off`・`classical._b_tick`・`classical.by_hour`・`classical.counts` 書ける系: decide
    - `O24` ClassicalPolicy home_cell・acq_fn(挙動 no・復元 derivable) 道筋 `classical.acq_fn`・`classical.home_cell` 書ける系: decide
    - `O69` ClassicalPolicy n_calls(挙動 diag・復元 discardable) 道筋 `classical.n_calls` 書ける系: decide
    - `O90` ClassicalPolicy _ipf_cache(15 分帯ごとの c_t の覚え書き)(挙動 behavior・復元 required) 道筋 `classical._ipf_cache` 書ける系: decide
- 決定の ID: D-31・D-119・第 292

## [clock.py](../../../../../../../src/shibuya/engine/clock.py)

engine.clock — シミュレーション時計(壁時計に一切依存しない)。

- 公開の関数とクラス
  - `SimClock`(クラス): 開始時刻と tick 長だけを持つ不変の時計。
- import している内部モジュール: `shibuya.foundation.time_consts`・`shibuya.foundation.types`
- 呼び手: `shibuya.engine`
- 読む試験: `tests/engine/test_clock.py`
- 読む試験(道筋で): `tests/engine/test_state_checks_10f.py`・`tests/tools/test_pkgmove.py`

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
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.proximity`・`shibuya.foundation.hashing`・`shibuya.foundation.types`・`shibuya.foundation.vocab.actions`・`shibuya.llm.parser`・`shibuya.llm.undefined`
- 呼び手: `shibuya.engine`・`shibuya.engine.activity`・`shibuya.engine.decision.layer`・`shibuya.engine.intent`・`shibuya.engine.memory`・`shibuya.engine.poi_target`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.systems.act`・`shibuya.engine.systems.build`・`shibuya.engine.systems.judge`・`shibuya.engine.systems.talk`
- 読む試験: `tests/c6/test_t5_order_bias.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/engine/processes/test_civic.py`・`tests/engine/processes/test_crowd.py`・`tests/engine/processes/test_rail.py`・`tests/engine/processes/test_rail_board_intent.py`・`tests/engine/processes/test_rail_return.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_intent_hold.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_move_destination.py`・`tests/engine/test_parser_contract.py`・`tests/engine/test_plan_sleep_d62.py`・`tests/engine/test_presence_exit_walk.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_resolve.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_stage3_small_fixes.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_two_phase.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_vocab_v2_eat.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 決定の ID: D-71・D-112・D-114・D-116・第 275

## [conversation.py](../../../../../../../src/shibuya/engine/conversation.py)

engine.conversation — 会話プロトコル(行動契約書 §3)のセッション状態機械。

- 公開の関数とクラス
  - `ConvState`(クラス): セッションの状態(契約書 §3「invited/walkingOver/participating」+ 終了2段)。
  - `ConversationManager`(クラス): 会話セッションの生成・進行・終了(**終了はLLMに決めさせない**)。
  - `GateResult`(クラス): 開始ゲートの判定(契約書 §3 の5条件)。
  - `PendingInvite`(クラス): **返事待ちの招待**(C6・09-09)。
  - `Session`(クラス): 1会話セッション。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.types`
- 呼び手: `shibuya.engine.contact.calls`・`shibuya.engine.contact.chat_state`・`shibuya.engine.contact.layer`・`shibuya.engine.speech.port`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/contact/test_c1_fixes.py`・`tests/engine/contact/test_c1_flow.py`・`tests/engine/contact/test_c1_units.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/speech/test_speech_empty_text_errors.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_conversation.py`・`tests/engine/test_conversation_invite.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_version_bump_10e.py`
- 読む試験(道筋で): `tests/economy/cp2/test_cp2_write_window.py`
- 状態台帳の行
  - 持ち主 `contact.calls`(`ConversationManager`)
    - `CT1K` CallManager(電話の会話=ConversationManager のセッションと表・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.calls._next_id`・`contact.calls._of_agent`・`contact.calls._pair_invite_until`・`contact.calls._refusal_until`・`contact.calls._speaker_invite_until`・`contact.calls._video`・`contact.calls.join_events`・`contact.calls.n_opened`・`contact.calls.pending_invites`・`contact.calls.sessions` 書ける系: calendar_3・contact
    - `CT1M` 連絡の道具の計器(層・チャット・通話・通話の発話の口の計数と分布・通話の切った判断の控え・第 6 期 6-4 C1)(挙動 diag・復元 discardable・腕 contact-c1) 道筋 `contact.calls.closed_by_reason`・`contact.calls.ignored_events`・`contact.calls.n_accepted`・`contact.calls.n_backchannels`・`contact.calls.n_blocks`・`contact.calls.n_declined`・`contact.calls.n_end_kept_activity`・`contact.calls.n_expired_purged`・`contact.calls.n_gate_rejected`・`contact.calls.n_ignored_invites`・`contact.calls.n_interrupts`・`contact.calls.n_invite_refractory_blocked`・`contact.calls.n_invites`・`contact.calls.n_pending_expired`・`contact.calls.n_pending_unreachable`・`contact.calls.n_revert_kept_activity`・`contact.calls.origin_counts`・`contact.calls.size_hist` 書ける系: calendar_3・contact
  - 持ち主 `contact.chats`(`ConversationManager`)
    - `CT1C` ChatBook(チャットの会話の状態=対面の会話の器 ConversationManager の子・第 6 期 6-4 C1)(挙動 behavior・復元 required・腕 contact-c1) 道筋 `contact.chats._next_id`・`contact.chats._of_agent`・`contact.chats._of_key`・`contact.chats._pair_invite_until`・`contact.chats._refusal_until`・`contact.chats._speaker_invite_until`・`contact.chats.join_events`・`contact.chats.n_opened`・`contact.chats.pending_invites`・`contact.chats.sessions` 書ける系: calendar_3・contact
    - `CT1M` 連絡の道具の計器(層・チャット・通話・通話の発話の口の計数と分布・通話の切った判断の控え・第 6 期 6-4 C1)(挙動 diag・復元 discardable・腕 contact-c1) 道筋 `contact.chats._chat_meter`・`contact.chats.closed_by_reason`・`contact.chats.ignored_events`・`contact.chats.n_accepted`・`contact.chats.n_backchannels`・`contact.chats.n_blocks`・`contact.chats.n_declined`・`contact.chats.n_end_kept_activity`・`contact.chats.n_expired_purged`・`contact.chats.n_gate_rejected`・`contact.chats.n_ignored_invites`・`contact.chats.n_interrupts`・`contact.chats.n_invite_refractory_blocked`・`contact.chats.n_invites`・`contact.chats.n_pending_expired`・`contact.chats.n_pending_unreachable`・`contact.chats.n_revert_kept_activity`・`contact.chats.origin_counts`・`contact.chats.size_hist` 書ける系: calendar_3・contact
  - 持ち主 `conv`(`ConversationManager`)
    - `O39` ConversationManager sessions・_of_agent・_refusal_until・_next_id・pending_invites・_pair_invite_until・_speaker_invite_until(挙動 behavior・復元 required) 道筋 `conv._next_id`・`conv._of_agent`・`conv._pair_invite_until`・`conv._refusal_until`・`conv._speaker_invite_until`・`conv.pending_invites`・`conv.sessions` 書ける系: apply_responses・conversation・decide・llm_receive・wake_sources
    - `O40` ConversationManager join_events(挙動 behavior・復元 required) 道筋 `conv.join_events` 書ける系: apply_responses・conversation・decide・llm_receive
    - `O41` ConversationManager origin_counts ほかの計数(挙動 diag・復元 discardable) 道筋 `conv.closed_by_reason`・`conv.ignored_events`・`conv.n_accepted`・`conv.n_backchannels`・`conv.n_blocks`・`conv.n_declined`・`conv.n_end_kept_activity`・`conv.n_expired_purged`・`conv.n_gate_rejected`・`conv.n_ignored_invites`・`conv.n_interrupts`・`conv.n_invite_refractory_blocked`・`conv.n_invites`・`conv.n_pending_expired`・`conv.n_pending_unreachable`・`conv.n_revert_kept_activity`・`conv.origin_counts`・`conv.size_hist` 書ける系: apply_responses・conversation・decide・llm_receive・wake_sources
    - `O91` ConversationManager n_opened(開いたセッションの数)(挙動 behavior・復元 required) 道筋 `conv.n_opened` 書ける系: apply_responses・conversation・decide・llm_receive
- 決定の ID: 11-03・11-03/§2・11-03/§3・D-93・第 346

## [defect_fixes_1103.py](../../../../../../../src/shibuya/engine/defect_fixes_1103.py)

engine.defect_fixes_1103 — 棚卸し B で見つけた欠陥 4 件の直しの宣言・計器・見出し(指示書 11-03 §3・小さな版上げ 1 回分)。

- 公開の関数とクラス
  - `check_resume`(関数): 再開のときに、保存したランの見出しの ``defect_fixes_1103``(無ければ legacy=版上げの前のラン)が on かを確かめる(違えば止める)。
  - `empty_counts`(関数): 計器の空の形(活動の名ごとの dict 2 本と整数 5 本)。
  - `header_fields`(関数): 状態のファイルの見出しの ``defect_fixes_1103``(ランは常に ``{"mode": "on"}``・on の外の名は None)。
  - `is_legacy`(関数): ``mode``(省略=ランの腕 on)が旧道(版上げの前の挙動=部品の口だけ)か。
  - `is_on`(関数): ``mode``(省略=ランの腕 on)が直した道か。
  - `manifest_fields`(関数): manifest の ``defect_fixes_1103``(設定=形の版・腕・4 件の宣言・直した印/観測=計器)。
  - `resolve`(関数): 引数の腕(``None``=ランの腕 ``on``)を名に直す(名の誤りは止める)。
- import している内部モジュール: `shibuya.engine.removed_switches`
- 呼び手: `shibuya.engine.systems.build`・`shibuya.engine.systems.report`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/engine/test_defect_fixes_1103.py`
- 環境変数: `SHIBUYA_DEFECT_FIXES_1103`
- 決定の ID: 10-13b/§0-6・11-02r/§2-2・11-03・11-03/§3・第 346

## [economy_rules.py](../../../../../../../src/shibuya/engine/economy_rules.py)

engine.economy_rules — 第 4 期 4-2 の規則の表の中身を経済の段階 2 に挿す組み立ての材料(給与の天引きの加入の判定の材料)。

- 公開の関数とクラス
  - `PayrollInputs`(クラス): 給与の天引きの加入の判定の材料(体ごと・読むだけ)。
  - `payroll_inputs`(関数): 体ごとの加入の判定の材料を組み立てる(:class:`PayrollInputs`)。表の無い世界・母集団の無いランは材料なし。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.economy_stage2`・`shibuya.engine.removed_switches`
- 呼び手: `shibuya.engine.economy_stage2`
- 読む試験: `tests/economy/test_rules42_ledger.py`・`tests/economy/test_rules42_payroll.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_rules42b_payroll.py`
- 環境変数: `SHIBUYA_RULES_42`・`SHIBUYA_RULES_42B`
- 決定の ID: 10-12・R-118・第 346

## [economy_stage2.py](../../../../../../../src/shibuya/engine/economy_stage2.py)

engine.economy_stage2 — 経済の段階 2 の腕と engine の側の組み立て(第 2 期 2-1・CP2 の段階 2)。

- 公開の関数とクラス
  - `AtmTable`(クラス): ATM の表(``Fixtures.atms``・状態台帳の行 ATM=軸 1 behavior・軸 2 derivable・中身は hash_skip)。銀行名は持たない。
  - `DataAbsentWarning`(クラス): 取得物(data/ の下)が無い写しで出す注記。〔第335・CI の直し〕data の無い CI でも経済の段階 2 は既定 on なので、
  - `Stage2Plan`(クラス): engine の側の段階 2 の組み立ての物(``Ledger.attach_stage2`` に渡す・``MoneyStage2.plan``)。
  - `WageInputs`(クラス): 賃金の関数(``economy.wages.occupation_wages``)に渡す体ごとの属性(engine の側が読む・額は economy が出す)。
  - `active_parts`(関数): 腕が on のときの部品(off なら空)。
  - `arm`(関数): いまの腕(``off``=既定・``on``)。組み立てのときに読む。
  - `atm_open_cells`(関数): 刻み ``step`` に営業中の ATM のあるセル(``(n_cells,)`` bool・ATM の表が無ければ全部 False)。
  - `attach`(関数): 腕が on なら段階 2 を組み立てて金の台帳に挿す(世帯の初期の財布の前=``resolve.initialize`` の前に呼ぶ)。
  - `build_atm_table`(関数): OSM の取得物から引き出しの場所の表を作る(``amenity=atm``・``atm=yes``・``amenity=bank``=銀行の支店は全部)。
  - `check_resume`(関数): 〔検収 A5〕再開のときに、保存したランの腕と部品(見出しの ``economy_stage2``・無ければ off)と今の腕が同じかを
  - `header_fields`(関数): 〔検収 A5〕状態のファイルの見出しの ``economy_stage2``(腕 off のランは書かない=None=今の見出しのまま)。
  - `money_stage2`(関数): 台帳の束から economy の段階 2 の中身(``MoneyStage2``)を引く(腕の無いランは ``None``)。
  - `parse_opening_hours`(関数): OSM の ``opening_hours`` → 曜日 × 区間の ``(7, 2, 2)`` int16(``[曜日, 区間, (始め, 終わり)]`` の分・空は -1)。
  - `parse_parts`(関数): 部品の指定(``"wages,withdraw"``・並び・空=全部)→ 部品の並び(``PARTS`` の順)。
  - `parts`(関数): いまの部品(腕が off でも指定は持つ=腕が on のときだけ効く)。
  - `persona_words`(関数): ペルソナの在庫の ``(pool_layer, pool_index)`` の行の語の欄(行の順=引数の並び・無い行は "")と読んだ行の数。
  - `population_total`(関数): W16 母集団の体の数(縮小ランの比の分母・Parquet の見出しだけを読む)。無ければ ``None``。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--economy-stage2``・試験の切替口)。
  - `set_atm_table`(関数): 試験の切替口(合成の世界の ATM の表を渡す)。``None`` で OSM から作る既定に戻す。
  - `set_parts`(関数): 部品を選ぶ(CLI ``--economy-stage2-parts``・試験の切替口)。
  - `wage_arm`(関数): 賃金の道(``occupation`` だけ)。
  - `wage_inputs`(関数): 賃金の関数の入力を組み立てる(母集団の体=ペルソナの職業と雇用の語+W16 の性と年齢・母集団の無いラン=語も性も年齢も
- import している内部モジュール: `shibuya.agents.population`・`shibuya.engine.economy_rules`・`shibuya.engine.rights.ledger`・`shibuya.foundation.journal.log`・`shibuya.foundation.paths`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.decision.layer`・`shibuya.engine.economy_rules`・`shibuya.engine.resolve`・`shibuya.engine.systems.build`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/economy/cp2/test_cp2_event_links.py`・`tests/economy/cp2/test_cp2_k17_capacity_and_overflow.py`・`tests/economy/cp2/test_cp2_nine_ops_equivalence.py`・`tests/economy/stage2/test_stage2_atm_absent_warning.py`・`tests/economy/stage2/test_stage2_calls.py`・`tests/economy/stage2/test_stage2_default_2_4.py`・`tests/economy/stage2/test_stage2_guards.py`・`tests/economy/stage2/test_stage2_resume.py`・`tests/economy/stage2/test_stage2_resume_arm.py`・`tests/economy/stage2/test_stage2_rules_credit_atm.py`・`tests/economy/stage2/test_stage2_runs.py`・`tests/economy/stage2/test_stage2_world_two_day.py`・`tests/economy/stage2/test_wage_occupation_runs.py`・`tests/economy/test_rules42_runs.py`・`tests/economy/test_rules42b_ledger.py`・`tests/economy/test_wage_occupation.py`・`tests/engine/multiday/_md.py`・`tests/engine/test_ledger_wiring.py`・`tests/engine/test_pop_w21_world.py`
- 読む試験(道筋で): `tests/economy/stage2/test_stage2_writers.py`
- 環境変数: `SHIBUYA_ECONOMY_STAGE2`・`SHIBUYA_ECONOMY_STAGE2_PARTS`・`SHIBUYA_WAGE`
- 決定の ID: 10-13b/§7・第 335・第 346

## [energy.py](../../../../../../../src/shibuya/engine/energy.py)

engine.energy — 体のエネルギー収支(5 段目 5a・D-118 K1〜K9・第291)。

- 公開の関数とクラス
  - `EnergyLayer`(クラス): ラン 1 本ぶんの エネルギー収支(模型+範囲外の予定+診断)。
  - `EnergyModel`(クラス): 錨から組んだ表と式(純関数)。書き込みはしない。
  - `HomeMeals`(クラス): **第2波 §2B 項 2(Q35 (a))** 範囲内の自宅の食事行=「予定の実行」(``--home-meal plan``)。
  - `MealStartDistribution`(クラス): **既定の食事時刻の分布**(腕 ``w17``・回答 10-13b §7 の 2)。時間帯(朝・昼・夕)ごとに、W17 の食事の行の開始の
  - `OutOfAreaMeals`(クラス): 範囲外の食事の予定(K9 (a))。起動時に 1 日ぶんの (tick, 体, 時間帯) を組む。
  - `anchors_paths`(関数): エンジンが読む錨のファイル=構築側の 1 本だけ(〔第 2 部〕検証側を読む旧値の腕は消した)。
  - `anchors_rel`(関数): manifest の ``energy.anchors`` の道筋。
  - `check_energy_rate`(関数)
  - `check_home_meal`(関数)
  - `check_hunger_model`(関数)
  - `check_meal_default`(関数)
  - `check_meal_sleep_defer`(関数)
  - `load_anchors`(関数): 錨の追跡ファイルを読む → ``(辞書, md5)``。
  - `meal_default`(関数): 既定の食事時刻の出どころ(``w17`` だけ=〔第 2 部〕旧値の腕と切替口は消した)。
  - `meal_start_distribution`(関数): 組み立ての口: 週次表(全員)から分布を作る(週次表が無ければ凍結の表)。
  - `minute_slot`(関数): その日の分 → 時間帯(朝 0 / 昼 1 / 夕 2 / その他 3)。
  - `w17_wake_minute`(関数): 体 ``agent`` がその日の ``minute`` に W17 の「就寝」の行の中に居れば、**起床の分**
- import している内部モジュール: `shibuya.agents.state`・`shibuya.agents.weekly`・`shibuya.engine.calendar`・`shibuya.foundation.paths`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.body.rules`・`shibuya.engine.body.schedule`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.systems.body`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/body/body_fixtures.py`・`tests/engine/body/test_body_reserve.py`・`tests/engine/body/test_meal_default_w17.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_energy_balance.py`・`tests/engine/test_meal_bundle_2b.py`・`tests/engine/test_meal_gate_per_hour.py`・`tests/engine/test_sim_time_T.py`
- 読む試験(道筋で): `tests/engine/state/test_names_frozen.py`・`tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主 `energy.home_meals`(`HomeMeals`)
    - `O32` HomeMeals の予定 tick・agent・slot・_start・home_cell(挙動 no・復元 derivable) 道筋 `energy.home_meals._start`・`energy.home_meals.agent`・`energy.home_meals.home_cell`・`energy.home_meals.slot`・`energy.home_meals.tick` 書ける系: body・home_meal
    - `O33` HomeMeals n_not_home・n_asleep・OutOfAreaMeals の計数 n_armed ほか(挙動 diag・復元 discardable) 道筋 `energy.home_meals.n_asleep`・`energy.home_meals.n_not_home` 書ける系: body・energy_after・home_meal
  - 持ち主 `energy.out_of_area`(`OutOfAreaMeals`)
    - `O29` OutOfAreaMeals の予定 tick・agent・slot・from_row・_start(挙動 no・復元 derivable) 道筋 `energy.out_of_area._start`・`energy.out_of_area.agent`・`energy.out_of_area.from_row`・`energy.out_of_area.slot`・`energy.out_of_area.tick` 書ける系: body・home_meal・phase_c
    - `O30` OutOfAreaMeals の遅らせの表 d_agent・d_slot・d_arm_tick・d_eat_tick・d_wake_min(挙動 no・復元 derivable) 道筋 `energy.out_of_area.d_agent`・`energy.out_of_area.d_arm_tick`・`energy.out_of_area.d_eat_tick`・`energy.out_of_area.d_slot`・`energy.out_of_area.d_wake_min` 書ける系: body・home_meal
    - `O31` OutOfAreaMeals d_armed(就寝中の食事を起床時に回す印)(挙動 behavior・復元 required) 道筋 `energy.out_of_area.d_armed` 書ける系: body・home_meal
    - `O33` HomeMeals n_not_home・n_asleep・OutOfAreaMeals の計数 n_armed ほか(挙動 diag・復元 discardable) 道筋 `energy.out_of_area.n_armed`・`energy.out_of_area.n_deferred_not_out`・`energy.out_of_area.n_skipped_past_window` 書ける系: body・energy_after・home_meal
  - 持ち主 `energy`(`EnergyLayer`)
    - `O27` EnergyLayer bmr(挙動 behavior・復元 derivable) 道筋 `energy.bmr` 書ける系: body・home_meal・phase_c
    - `O28` EnergyLayer meal_bits・n_meals・n_snacks・counts・intake_kcal・meal_start_*・stage_ticks*(挙動 diag・復元 discardable) 道筋 `energy.ate_default`・`energy.counts`・`energy.intake_kcal`・`energy.meal_bits`・`energy.meal_start_home`・`energy.meal_start_in`・`energy.meal_start_out`・`energy.n_meals`・`energy.n_snacks`・`energy.snack_start`・`energy.stage_ticks`・`energy.stage_ticks_awake_by_hour` 書ける系: body・energy_after・home_meal・phase_c
- 環境変数: `SHIBUYA_MEAL_DEFAULT`
- 決定の ID: 10-03/§7-1・10-13b/§7・D-111・D-118・第 291

## [familiarity.py](../../../../../../../src/shibuya/engine/familiarity.py)

engine.familiarity — **親しみの表**(4 段目・記憶の先行部品=M13 訪問カウンタ+M17 露出カウンタ・第290)。

- 公開の関数とクラス
  - `FamiliarityLayer`(クラス): 親しみの表の値を決める層(書き手は ``resolve.write_familiarity``)。
  - `activation_approx`(関数): 最適化学習の近似 ``A = ln(n/(1−d)) − d·ln(L+1)``(n ≤ 0 は :data:`ACTIVATION_ABSENT`)。
  - `activation_exact`(関数): 厳密式 ``ln Σ_j (Δt_j + 1)^(−d)``(Δt_j=各接触からの経過分・比較と記録のためだけ)。
  - `person_thing`(関数): 体 → 人の ``thing_id``(``1<<30 | id``・本段では書かない)。
  - `place_thing`(関数): セル → 場所の ``thing_id``(``−(cell+2)``=空行 −1 と衝突しない・cell ≥ 0)。
  - `thing_kind`(関数): ``thing_id`` → 種類(``"empty"`` / ``"poi"`` / ``"place"`` / ``"person"``)の文字列配列。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.resolve`・`shibuya.perception.attention`
- 呼び手: `shibuya.cli`・`shibuya.engine.memory`・`shibuya.engine.memory_store`・`shibuya.engine.run`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/test_familiarity.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_store_memory.py`・`tests/perception/test_p_see_activity.py`
- 状態台帳の行
  - 持ち主 `fam_layer`(`FamiliarityLayer`)
    - `O7` FamiliarityLayer prev_cell(挙動 behavior・復元 required) 道筋 `fam_layer.prev_cell` 書ける系: familiarity
    - `O67` FamiliarityLayer stats(挙動 diag・復元 discardable) 道筋 `fam_layer.stats` 書ける系: familiarity
- 決定の ID: D-95・D-119・第 290

## [geometry.py](../../../../../../../src/shibuya/engine/geometry.py)

engine.geometry — C9 位置幾何(辺上の連続位置・歩行速度)の**切替口**。

- 公開の関数とクラス
  - `EdgeGeometry`(クラス): 辺上の連続位置(G1 (b))と歩行速度(G2 (b))の**前計算した表**+解析式。
  - `check_geometry`(関数): 幾何モードの検査(``run_day`` が**世界を作る前**に呼ぶ=manifest が嘘をつかない)。
  - `desired_speeds`(関数): 個体の希望歩行速度[m/s]\(**seed と agent_id だけの決定論**・float32)。
  - `kladek_speed_factor`(関数): 密度 → 自由速度に対する比 ``v/v0``(Kladek/Weidmann・**解析式 1 本**)。
- import している内部モジュール: `shibuya.engine.change_detect`・`shibuya.foundation.rng`・`shibuya.world.assets`・`shibuya.world.state`
- 呼び手: `shibuya.cli`・`shibuya.engine.resolve`・`shibuya.engine.run`・`shibuya.engine.space.nav1`・`shibuya.engine.systems.build`
- 読む試験: `tests/build_pop/test_w21_stage8_9.py`・`tests/engine/space/test_nav1_density.py`・`tests/engine/space/test_nav1_units.py`・`tests/engine/test_area_source_c9c.py`・`tests/engine/test_c9b_targets_attention.py`・`tests/engine/test_geometry_c9.py`・`tests/engine/test_salt_seed_split_10f.py`

## [growth_decl.py](../../../../../../../src/shibuya/engine/growth_decl.py)

engine.growth_decl — エンジン側の**状態成長宣言**(D-R2-6 の YAML 5 欄・データ非依存の定数)。

- 公開の関数とクラス
  - `activity_declaration`(関数): **二層の段 2** の活動の文(``engine.activity.ActivityLayer``)の成長宣言。
  - `declarations`(関数): エンジン側 5 構造体の成長宣言(名前 → 宣言)。
  - `to_yaml`(関数): D-R2-6 の YAML 5 欄を文字列で返す(manifest / 検収パックへ貼る用)。
- import している内部モジュール: `shibuya.foundation.growth`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.run`・`shibuya.engine.systems.report`
- 読む試験: `tests/engine/test_mock_day_w2.py`・`tests/engine/time/test_t0_time_consts.py`

## [intent.py](../../../../../../../src/shibuya/engine/intent.py)

engine.intent — **意図の保持**(段 2c・D-112 ①・D-114 案 A・第288)。

- 公開の関数とクラス
  - `IntentLayer`(クラス): 意図の保持(``engine.run`` が活動層と一緒に作る=語彙 v3・``--activity on``・``candidates``)。
  - `intent_summary`(関数): 計数 → manifest ``intent`` の形(アジェンダ §3-6)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.activity`・`shibuya.engine.commit`・`shibuya.engine.resolve`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/space/test_nav1_units.py`・`tests/engine/test_intent_hold.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`
- 状態台帳の行
  - 持ち主 `intent_layer`(`IntentLayer`)
    - `O4` IntentLayer _payload(挙動 behavior・復元 required) 道筋 `intent_layer._payload` 書ける系: activity_intent・apply_responses・phase_a・phase_c
    - `O5` IntentLayer _proposals・_executing・_kept_walk(挙動 no・復元 discardable) 道筋 `intent_layer._executing`・`intent_layer._kept_walk`・`intent_layer._proposals` 書ける系: activity_intent・apply_responses・phase_a・phase_c
    - `O6` IntentLayer stats・ticks_sum・ticks_n(挙動 diag・復元 discardable) 道筋 `intent_layer.stats`・`intent_layer.ticks_n`・`intent_layer.ticks_sum` 書ける系: activity_intent・apply_responses・detect・phase_a・phase_c
- 決定の ID: D-51・D-62・D-112・D-114・D-122・第 288

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
- import している内部モジュール: `shibuya.engine.tape`・`shibuya.foundation.text.templates`・`shibuya.foundation.vocab.actions`・`shibuya.llm`
- 呼び手: `shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.llm_io`・`shibuya.engine.systems.run_end`
- 読む試験: `tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/decision/_j0.py`・`tests/engine/decision/test_j0_mock_equivalence.py`・`tests/engine/decision/test_j0_port_schema.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/memory/test_m0_render_bytes.py`・`tests/engine/rights/test_no_permission_count.py`・`tests/engine/rights/test_rights_events.py`・`tests/engine/test_renderer_wiring.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_two_layer_activity.py`・`tests/engine/test_undefined_action.py`・`tests/engine/tools/test_c0_affordance_from_registry.py`・`tests/llm/test_fleet.py`・`tests/llm/test_fleet_contract.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 読む試験(道筋で): `tests/test_places_guard.py`
- 状態台帳の行
  - 持ち主 `bridge`(`LLMBridge`)
    - `O85` LLMBridge _interned(テープへ書いた共有ブロック)(挙動 no・復元 required) 道筋 `bridge._interned` 書ける系: close_final・decide
    - `O86` LLMBridge の計数(挙動 diag・復元 discardable) 道筋 `bridge.n_calls`・`bridge.n_deferred`・`bridge.n_dictionary_mapped`・`bridge.n_label_alias`・`bridge.n_parse_errors`・`bridge.n_parse_errors_strict`・`bridge.n_positional`・`bridge.n_role_actions`・`bridge.n_role_unauthorized`・`bridge.n_role_unjudged`・`bridge.n_tape_misses`・`bridge.n_tape_rows`・`bridge.n_undefined_mapped`・`bridge.n_unknown_action` 書ける系: close_final・decide
- 決定の ID: D-58・D-59・D-71

## [memory.py](../../../../../../../src/shibuya/engine/memory.py)

engine.memory — 記憶 第 1 段の **記録**(6 段目 6a・D-95・記憶アジェンダ v1 M1〜M4・M13・M16・修正 1・第294)。

- 公開の関数とクラス
  - `MemoryLayer`(クラス): 記憶の表の書き手と読み口(記録だけ・本段では誰も読まない)。
  - `RecallItem`(クラス): 想起した 1 行(描画の材料=``perception.renderer`` が文にする)。
  - `activation_rows`(関数): A = ln(n/(1−d)) − d·ln(L+1)(L=(tick − first)×分/tick・#56 と同じ近似)。n=0 の行は −inf。
  - `importance_of`(関数): 事象 → importance(固定表・配列演算)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.commit`・`shibuya.engine.familiarity`・`shibuya.engine.memory_embed`・`shibuya.engine.memory_m1`・`shibuya.engine.memory_shops`・`shibuya.engine.memory_store`・`shibuya.engine.relations`・`shibuya.engine.relations_people`・`shibuya.engine.resolve`・`shibuya.engine.store_memory`・`shibuya.foundation.types`
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar2.recall`・`shibuya.engine.decision.sources`・`shibuya.engine.memory_store`・`shibuya.engine.run`・`shibuya.engine.store_memory`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/memory/test_m0_recall_equivalence.py`・`tests/engine/memory/test_m0_shown_recorded.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m1_strength.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_memory_record.py`・`tests/engine/test_relations.py`・`tests/engine/test_relations_8b.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/test_wom.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/perception/facts/test_render_from_percept_bytes.py`
- 状態台帳の行
  - 持ち主 `mem_layer`(`MemoryLayer`)
    - `O8` MemoryLayer gist・_gist_order(挙動 behavior・復元 required) 道筋 `mem_layer._gist_order`・`mem_layer.gist` 書ける系: decide・llm_receive・memory
    - `O9` MemoryLayer _session_key・_gist_done(挙動 behavior・復元 required) 道筋 `mem_layer._gist_done`・`mem_layer._session_key` 書ける系: decide・llm_receive・memory
    - `O10` MemoryLayer _next_session・_next_join(挙動 behavior・復元 required) 道筋 `mem_layer._next_join`・`mem_layer._next_session` 書ける系: decide・llm_receive・memory
    - `O11` MemoryLayer _target・stats・recall_stats(挙動 diag・復元 discardable) 道筋 `mem_layer._target`・`mem_layer.recall_stats`・`mem_layer.stats` 書ける系: decide・llm_receive・memory
- 決定の ID: D-93・D-95・D-120・第 294・第 295・第 298

## [memory_embed.py](../../../../../../../src/shibuya/engine/memory_embed.py)

engine.memory_embed — 記憶 MR2 の意味の手がかり(埋め込み)の口(第 6 期 6-5・腕 ``--memory-cue embed``)。

- 公開の関数とクラス
  - `CueState`(クラス): 意味の手がかりの状態(記憶の器の子の持ち主 ``mem_layer.memory_store.cue``・状態台帳の腕の行 ``M0C``)。
  - `EmbedUnavailable`(クラス): 埋め込みのモデルが使えない(重みが置き場に無い・torch/transformers が無い)。
  - `Embedder`(クラス): 埋め込みの口(``encode`` は L2 で正規化した ``(件, dim)`` の float32)。
  - `NgramEmbedder`(クラス): 試験用の代わり ``ngram-test``(文字の 1〜3-gram を crc32 で ``dim`` 次元に足して正規化・意味の手がかりではない)。
  - `RuriEmbedder`(クラス): Ruri-v3(``cl-nagoya/ruri-v3-30m``・``130m``)を CPU で(重みは :data:`MODEL_ROOT` の版の置き場から読む)。
  - `RuriPin`(クラス): Ruri-v3 の版の固定(huggingface のリポ・commit・重みの sha256=X-Linked-ETag・大きさ・ライセンス)。
  - `make_embedder`(関数): 腕のモデルの名 → 埋め込みの口(``ngram-test`` は試験用の代わり・Ruri は重みが無ければ :class:`EmbedUnavailable`)。
  - `model_identity`(関数): 〔検収 L1〕埋め込みのモデルの名 → 版の同定(設定の指紋と manifest の設定の節に入れる=再開で取り違えを止める)。
- 呼び手: `shibuya.engine.memory`・`shibuya.engine.memory_m1`・`shibuya.engine.memory_store`
- 読む試験: `tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`
- 状態台帳の行
  - 持ち主 `mem_layer.memory_store.cue`(`CueState`)
    - `M0C` CueState(意味の手がかり=手がかりの文と行の埋め込み・第 6 期 6-5)(挙動 behavior・復元 required・腕 memory-cue) 道筋 `mem_layer.memory_store.cue._heard`・`mem_layer.memory_store.cue._own`・`mem_layer.memory_store.cue._qcache`・`mem_layer.memory_store.cue._vec` 書ける系: decide・llm_receive・memory
    - `M0X` M1State・CueState の計数(第 6 期 6-5)(挙動 diag・復元 discardable) 道筋 `mem_layer.memory_store.cue._cue_stats` 書ける系: decide・llm_receive・memory
- 決定の ID: 10-12/§4-6・R-87

## [memory_impression.py](../../../../../../../src/shibuya/engine/memory_impression.py)

engine.memory_impression — 記憶 M3 の器(印象の履歴と、本人が寝たときの書き直し・第 6 期 6-5)。

- 公開の関数とクラス
  - `ImpressionBook`(クラス): 印象の履歴と意味の記憶の器(M3)。書く口は :meth:`after_conversation`・:meth:`on_sleep`・:meth:`add_conclusion`。
  - `ImpressionEntry`(クラス): 履歴の 1 件(足すだけ)。``cause`` は LLM の呼び(原因つき)。
- import している内部モジュール: `shibuya.foundation.journal.log`
- 読む試験: `tests/engine/memory/test_m3_impression_and_trace.py`・`tests/engine/memory/test_mr65_guards.py`
- 決定の ID: 10-12・10-12/§4-6

## [memory_m1.py](../../../../../../../src/shibuya/engine/memory_m1.py)

engine.memory_m1 — 記憶 MR 第 6 期 6-5 の GPU の前に作る分(強さの式 M1・個人差・思い浮かぶ/見覚え・腕の切替口)。

- 公開の関数とクラス
  - `KindSpec`(クラス): 種類ごとの忘れる速さと足す項(MR1 (d)・MR12 (a))。``additive``: ``importance``・``none``。
  - `M1State`(クラス): M1 の強さの状態(記憶の器の子の持ち主 ``mem_layer.memory_store.m1``・状態台帳の腕の行 ``M0M``=腕 memory-model)。
  - `MemoryArms`(クラス): 6-5 の腕のいまの値(組み立てが 1 回読む)。
  - `arms`(関数): いまの腕(既定は ``m0``・``id``・``table``・``ruri-v3-30m``・``each``)。
  - `arms_on`(関数): 既定と違う腕が 1 つでもあるか(``cli.run`` のランの種類=結果を変える腕は「腕」に数える)。
  - `base_level`(関数): 行の配列 → 基底の強さ B(ACT-R の折衷形・秒)。``n == 0`` の行は −inf。
  - `check_arms`(関数): 組み立ての前の検査(器の無いランで既定と違う腕・people=memory で model=m0)→ いまの腕。違えば ``ValueError``。
  - `clarity_words`(関数): 強さ → 言葉(MR-0): ``A ≥ τ + margin`` は「はっきり」・``A ≥ τ`` は「うろ覚え」・それ以外は空文字。
  - `config_of`(関数): 〔検収 L1〕腕の値 → 設定の節と設定の指紋に入れる値(既定の腕なら空=既定のランの指紋と manifest の欄は前のまま)。
  - `exact_base_level`(関数): 正確な式 ``ln Σ t_j^(−d)``(試験の参照=全部の回の時刻)。
  - `forget_mask`(関数): 忘れる(消す)=手がかりがあっても見覚えに ``margin`` だけ届かない(上限なしの腕だけが使う)。
  - `forgetting_scale`(関数): 体の鍵の配列 → 忘れる速さの倍率 ``1 + cv·z``(z は標準正規=Philox の 2 語から Box-Muller・±``clip_sigma`` で切る)。
  - `recall_mask`(関数): 思い浮かぶ=``A ≥ τ``。
  - `recognize_mask`(関数): 見覚え=親しみの強さに目の前の手がかりを足すと ``τ`` を超える(手がかりの無い行は偽)。
  - `set_arm`(関数): 腕を選ぶ(CLI・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
  - `tau_from_m0`(関数): M1 の境目 τ の仮の値(expedient・人のデータで較正しない=検証側)。
  - `touch_times`(関数): ``recent_ns[rows]`` の直近の時刻に ``t_ns`` を足す(新しい順に 1 つずらす・空きは :data:`NO_TIME`)。その場で書く。
- import している内部モジュール: `shibuya.engine.memory_embed`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.calendar2.recall`・`shibuya.engine.memory`・`shibuya.engine.memory_store`・`shibuya.engine.memory_trace`・`shibuya.engine.relations_people`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/memory/_mr65.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m1_strength.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`
- 状態台帳の行
  - 持ち主 `mem_layer.memory_store.m1`(`M1State`)
    - `M0M` M1State(記憶の強さ M1 の直近の時刻と人ごとの忘れる速さの倍率・第 6 期 6-5)(挙動 behavior・復元 required・腕 memory-model) 道筋 `mem_layer.memory_store.m1._scale`・`mem_layer.memory_store.m1._t_ns` 書ける系: decide・llm_receive・memory
    - `M0X` M1State・CueState の計数(第 6 期 6-5)(挙動 diag・復元 discardable) 道筋 `mem_layer.memory_store.m1._m1_stats` 書ける系: decide・llm_receive・memory
- 環境変数: `SHIBUYA_MEMORY_CUE`・`SHIBUYA_MEMORY_EMBED_MODEL`・`SHIBUYA_MEMORY_GRAIN`・`SHIBUYA_MEMORY_MODEL`・`SHIBUYA_MEMORY_PEOPLE`・名前を読めない所 1 か所
- 決定の ID: 10-12・10-12/§4-6・R-68・R-87

## [memory_shops.py](../../../../../../../src/shibuya/engine/memory_shops.py)

engine.memory_shops — 人も記憶の一つの腕の店の評価の行(第 6 期 6-5・検収 M4・腕 ``--memory-people memory``)。

- 公開の関数とクラス
  - `ShopTable`(クラス): 店の評価の行の表(記憶の器の子の持ち主 ``mem_layer.memory_store.shops``・状態台帳の腕の行 ``M0S``)。
  - `UncappedStoreMemory`(クラス): 人も記憶の一つの腕の店の評価の記憶(``StoreMemory`` の子=行の口だけ差し替える・行は :class:`ShopTable`)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.memory_store`・`shibuya.engine.store_memory`
- 呼び手: `shibuya.engine.memory`
- 読む試験: `tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_guards.py`
- 状態台帳の行
  - 持ち主 `mem_layer.memory_store.shops`(`ShopTable`)
    - `M0S` ShopTable(人も記憶の一つの腕の店の評価の行・第 6 期 6-5 検収 M4)(挙動 behavior・復元 required・腕 memory-people) 道筋 `mem_layer.memory_store.shops._first`・`mem_layer.memory_store.shops._last`・`mem_layer.memory_store.shops._n`・`mem_layer.memory_store.shops._poi`・`mem_layer.memory_store.shops._precision`・`mem_layer.memory_store.shops._source`・`mem_layer.memory_store.shops._valence` 書ける系: decide・llm_receive・memory
    - `M0X` M1State・CueState の計数(第 6 期 6-5)(挙動 diag・復元 discardable) 道筋 `mem_layer.memory_store.shops._shop_stats` 書ける系: decide・llm_receive・memory
  - 持ち主 `mem_layer.store` の別のクラス `UncappedStoreMemory`(行は `shibuya.engine.store_memory` のカードを見る)
- 決定の ID: 10-12・10-12/§4-6

## [memory_store.py](../../../../../../../src/shibuya/engine/memory_store.py)

engine.memory_store — 記憶の器 M0(第 1 期 1-6・MR-0・MR11 (b)・MR16)。

- 公開の関数とクラス
  - `Cue`(クラス): 想起の手がかり(System 1 が体の状態から作る=今の 6b の q・ID の一致)。負/0 は「無し」。
  - `LegacyEvent`(クラス): 出来事の記録に無い出来事(仮の行の中身)。配列か整数。``t_ns`` はその回の時刻。
  - `LoggedEvent`(クラス): 〔第 2 期 2-3〕出来事の記録にある出来事への目印(``(t_ns, seq)``)と中身の写し。配列か整数。
  - `MemoryStore`(クラス): 記憶の器 M0(体ごとの行の範囲・SoA の列)。書く口は :meth:`remember` と :meth:`mark_shown`。
  - `MemoryView`(クラス): LLM に見せる形(MR-0): 言葉(``clarity``)と中身の粗さ(``grain``)と中身の ID。**強さの数は持たない**。
  - `RecallReport`(クラス): 1 回の想起の計数(``MemoryLayer`` が manifest の ``memory_summary.recall.counts`` に足す)。
  - `ShopPool`(クラス): ほかの表の候補(M0 は 7c の店の評価の行=今の ``sm_*``)。器の行と同じ score の順で競わせる。
  - `arm`(関数): いまの腕(``mem``=既定・``events``=記憶の器)。組み立てのときに読む。
  - `clarity_of`(関数): 強さ A → 言葉(MR-0)。A ≥ τ=はっきり・それ以外=うろ覚え(境目は expedient)。
  - `event_id_text`(関数): 目印 → テープの列の文字列 ``"t_ns:seq"``(無ければ空文字)。
  - `render_memories`(関数): ``MemoryView`` の組 → B5「記憶」の 1 行(今の描き方=``perception.renderer`` の項と行の組み立て・テンプレ v1.3)。
  - `row_caps`(関数): いまの種類ごとの行の上限(写し)。
  - `rows0`(関数)
  - `set_arm`(関数): 腕を選ぶ(CLI ``--memory-store``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
  - `set_row_caps`(関数): 上限なしの腕の種類ごとの行の上限(``episode``・``person``・``shop``・``None``=既定の値に戻す)。試験と感度の腕の口
  - `set_rows0`(関数): 上限なしの腕の最初の行の幅(``None``=記憶の表と同じ)。試験と測りの切替口(組み立ての時に読む)。
  - `to_item`(関数): ``MemoryView`` → 今の描き方が読む ``RecallItem``(刻みの番号に戻す=今の表と同じ値)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.events.body`・`shibuya.engine.familiarity`・`shibuya.engine.memory`・`shibuya.engine.memory_embed`・`shibuya.engine.memory_m1`・`shibuya.foundation.journal.log`・`shibuya.foundation.text.normalize`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.events`・`shibuya.foundation.write_guard`・`shibuya.perception.renderer`
- 呼び手: `shibuya.cli`・`shibuya.engine.memory`・`shibuya.engine.memory_shops`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/memory/_m0.py`・`tests/engine/memory/_mr65.py`・`tests/engine/memory/test_m0_render_bytes.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/multiday/_md.py`・`tests/engine/multiday/test_md23_body_events.py`
- 読む試験(道筋で): `tests/engine/memory/test_mr65_guards.py`
- 状態台帳の行
  - 持ち主 `mem_layer.memory_store`(`MemoryStore`)
    - `M0` MemoryStore(記憶の器 M0・第 1 期 1-6)の行・仮の出来事の表・注釈(挙動 no・復元 derivable) 道筋 `mem_layer.memory_store._lg_cell`・`mem_layer.memory_store._lg_kind`・`mem_layer.memory_store._lg_object`・`mem_layer.memory_store._lg_partner`・`mem_layer.memory_store._lg_result`・`mem_layer.memory_store._ms_ev_seq`・`mem_layer.memory_store._ms_ev_t_ns`・`mem_layer.memory_store._ms_first_ns`・`mem_layer.memory_store._ms_imp`・`mem_layer.memory_store._ms_n`・`mem_layer.memory_store._ms_note`・`mem_layer.memory_store._ms_note_order`・`mem_layer.memory_store._ms_origin` 書ける系: decide・llm_receive・memory
    - `M0L` MemoryStore の記録の目印の seq(第 2 期 2-3)(挙動 no・復元 required・腕 memory-store) 道筋 `mem_layer.memory_store._ms_log_seq` 書ける系: decide・llm_receive・memory
    - `M0R` MemoryStore の録画(見せた時刻)・テープの列への控え・計数(第 1 期 1-6)(挙動 diag・復元 discardable) 道筋 `mem_layer.memory_store._ms_last`・`mem_layer.memory_store._ms_shown_ns`・`mem_layer.memory_store._ms_stats`・`mem_layer.memory_store._ms_tape` 書ける系: decide・drain・llm_receive・memory
- 環境変数: `SHIBUYA_MEMORY_STORE`
- 決定の ID: 10-12/§4-6・10-13b/§3・R-113

## [memory_trace.py](../../../../../../../src/shibuya/engine/memory_trace.py)

engine.memory_trace — 注意を向けずに見ていた人の浅い痕跡(第 6 期 6-5・MR6 の後段「注意を向けずに見ていた人が話題に出たとき」)。

- 公開の関数とクラス
  - `TraceView`(クラス): 浅い痕跡(保存しない=手がかりが来たときに組み立てる)。``places`` は ``(場所の種類, id, 回数)`` の組。
  - `played_along_share`(関数): 「LLM が覚えていないのに話を合わせた割合」=聞き手の記憶に指された相手が無い行のうち、話を合わせた行の割合
  - `shallow_trace`(関数): 出来事の記録から ``viewer`` が ``target`` を同じ場所の近い時刻で見ていた回を組み立てる(読むだけ)。
  - `trace_word`(関数): 聞き手に見せる言葉: 注意を向けた記憶=空文字(普通に描く)・浅い痕跡だけ=「見たような気もする」・何も無い=空文字。
- import している内部モジュール: `shibuya.engine.memory_m1`・`shibuya.foundation.time_consts`
- 読む試験: `tests/engine/memory/test_m3_impression_and_trace.py`・`tests/engine/memory/test_mr65_guards.py`
- 決定の ID: 10-12・10-12/§4-6

## [norm_meter.py](../../../../../../../src/shibuya/engine/norm_meter.py)

engine.norm_meter — **群・規範の計器**(D-107 (a)・第255 決定・第256 R-42 Q4 親検収)。**読むだけ**。

- 公開の関数とクラス
  - `GroupNormMeter`(クラス): 群・規範の計器(読むだけ)。``engine.run`` が tick の骨格の決まった位置で呼ぶ。
  - `entropy_bits`(関数): 度数 → シャノンエントロピー[bit]\(D-68 の M3b と同じ計算)。度数 0 は 0。
  - `role_code_table`(関数): 語彙の版 → 役割語 → 行動コード(``llm.contract``)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.engine.systems.build`
- 読む試験: `tests/engine/test_norm_meter.py`
- 状態台帳の行
  - 持ち主 `norm_meter`(`GroupNormMeter`)
    - `O34` GroupNormMeter _prev_xy・_pair_keys・_pair_len・計数(挙動 no・復元 discardable) 道筋 `norm_meter._cowalk_pairs_seen`・`norm_meter._ctx`・`norm_meter._pair_keys`・`norm_meter._pair_len`・`norm_meter._prev_xy`・`norm_meter._role_rows`・`norm_meter.cowalk_agent_minutes`・`norm_meter.cowalk_episodes`・`norm_meter.cowalk_pairs_max_tick`・`norm_meter.cowalk_ticks_skipped`・`norm_meter.group_size_minutes`・`norm_meter.inst_group_count`・`norm_meter.inst_grouped_minutes`・`norm_meter.inst_pairs_max_tick`・`norm_meter.inst_size_minutes`・`norm_meter.inst_ticks_skipped`・`norm_meter.inst_walker_minutes`・`norm_meter.moving_agent_minutes`・`norm_meter.n_actions_counted`・`norm_meter.n_actions_off_stage`・`norm_meter.n_ticks`・`norm_meter.no_permission_total`・`norm_meter.role_by_kind`・`norm_meter.role_result`・`norm_meter.seconds`・`norm_meter.tick_ms_max` 書ける系: apply_responses・observe・phase_c
- 決定の ID: R-36・R-42・D-68・D-107・第 255・第 256・第 309

## [owner_guard.py](../../../../../../../src/shibuya/engine/owner_guard.py)

engine.owner_guard — 外の状態の持ち主の実行時の守り(第 6 期 6-3 検収 M2・3-2 の ``WindowQueue`` と同じ形を共通の口に)。

- 公開の関数とクラス
  - `closed`(関数): ``obj`` の欄を書けない間(書く口の中から外のコード=処理の関数を呼ぶ間)。
  - `frozen_array`(関数): 配列に書けない印を付けて返す(持ち主が新しい配列で置き換える)。
  - `guarded_delattr`(関数)
  - `guarded_setattr`(関数)
  - `hidden`(関数): 持ち主の中身を書く辞書(無ければ作る)。持ち主の書く口の中だけで使う。
  - `writing`(関数): ``obj`` の欄を書ける間(入れ子可)。
- 呼び手: `shibuya.engine.regional_clock`・`shibuya.engine.speech_clock`・`shibuya.engine.step_scope`

## [poi_target.py](../../../../../../../src/shibuya/engine/poi_target.py)

engine.poi_target — 購入/食事/並ぶの対象を**候補 → 選び手**で決める(段 2a・D-114 (a))。

- 公開の関数とクラス
  - `TargetResolver`(クラス): 対象欄の読み・候補の絞り込み・選び手の抽選(1 ランに 1 つ・世界は読むだけ)。
  - `move_resolution_summary`(関数): 段 2b の計数 → manifest ``move_resolution`` の形。
  - `resolution_summary`(関数): 計数 → manifest ``target_resolution`` の形((i)〜(iv)+エントロピーの平均)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.chooser`・`shibuya.engine.commit`・`shibuya.world.assets`・`shibuya.world.state`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.report`・`shibuya.engine.wom`
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
- import している内部モジュール: `shibuya.agents.state`・`shibuya.agents.weekly`・`shibuya.engine.rate_rules`・`shibuya.engine.resolve`・`shibuya.foundation.time_consts`・`shibuya.world.state`
- 呼び手: `shibuya.engine.calendar_self`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`tools/instruments/anchor_gauge.py`
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

## [proximity.py](../../../../../../../src/shibuya/engine/proximity.py)

engine.proximity — 会話と近接を実距離で判定する(第 2 期 2-2・段 11a)。

- 公開の関数とクラス
  - `NearView`(クラス): 描画の前計算に渡す物(規則・この刻みの索引・気づいた印の読み口)。
  - `ProximityLayer`(クラス): 腕 ``distance`` の層(判定の規則・計器・気づいた印の読み口)。組み立てが作る(既定の distance で作る・旧道の cell では作らない=None)。
  - `ProximityRule`(クラス): 腕 ``distance`` の判定の規則(組み立てで 1 回作る・ランの間は変えない)。``seed``=動きの側の seed。
  - `batch_partners`(関数): 適用の束 ``batch`` の中で、``rows``(束の中の位置)の体に届く束の体のうち並びの鍵が最小の体(届く体が無ければ −1)。
  - `check_resume`(関数): 再開のときに、保存したランの腕(見出しの ``proximity``・無ければ cell=2-2 までのラン)と今の腕が同じかを確かめる
  - `d`(関数): いまの会話の距離 d[m]\(ランの近接の規則=``distance`` の距離)。
  - `header_fields`(関数): 状態のファイルの見出しの ``proximity``(層の無い物は書かない=None・ランは常に層を持つ)。
  - `manifest_fields`(関数): manifest の ``proximity``(層の無い物は観測の子が null・ランは常に層を持つ=mode は distance)。
  - `marks_for`(関数): 「暫定」の印(B6・B8)。B6 は位置の出どころ(node と edge の幾何は立っている体は node・nav1 は面の上の点)・B8 は
  - `notice_p`(関数): R-62 の 2 点を通るロジスティック p(d)(距離[m] → 気づく確率)。
  - `rule_from`(関数): 組み立ての口(``seed``=動きの側の seed=気づく抽選の counter の流れの鍵・``poi_cell``=``world.pois.cell``・
  - `set_d`(関数): 会話の距離 d の感度の腕を選ぶ(CLI ``--proximity-d``・試験の切替口)。
- import している内部モジュール: `shibuya.engine.removed_switches`・`shibuya.engine.spatial_index`・`shibuya.foundation.rng`
- 呼び手: `shibuya.cli`・`shibuya.engine.commit`・`shibuya.engine.relations`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/engine/proximity/test_rule.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/proximity/test_switch_sites.py`・`tests/engine/space/test_nav1_units.py`・`tests/perception/facts/test_render_from_percept_bytes.py`
- 読む試験(道筋で): `tests/engine/test_state_ledger_10b.py`
- 状態台帳の行
  - 持ち主 `proximity`(`ProximityLayer`)
    - `PX` ProximityLayer(近接の層の計器・第 2 期 2-2 段 11a)(挙動 diag・復元 discardable) 道筋 `proximity._meter` 書ける系: perceive_prepare
- 環境変数: `SHIBUYA_PROXIMITY`・`SHIBUYA_PROXIMITY_D`
- 決定の ID: 10-03/§4・10-13b/§0-3・R-62・R-79・第 346

## [rate_rules.py](../../../../../../../src/shibuya/engine/rate_rules.py)

engine.rate_rules — 率の形の規則を外す切替口(指示書 11-01 段 2 の 3・4・回答 11-01 §2・§3・小さな版上げ 1 回分)。

- 公開の関数とクラス
  - `arm`(関数): いまの腕(``off``=既定・``legacy``=切替口)。組み立てのときに読む。
  - `check_resume`(関数): 再開のときに、保存したランの腕(見出しの ``rate_rules``・無ければ legacy)と今の腕が同じかを確かめる(違えば止める)。
  - `header_fields`(関数): 状態のファイルの見出しの ``rate_rules``(legacy のランは書かない=None=版上げの前の見出しのまま)。
  - `is_legacy`(関数): ``mode``(省略=今の腕)が旧道(率の形の規則を動かす)か。
  - `manifest_fields`(関数): manifest の ``rate_rules``(設定=形の版・腕・規則の宣言・外した印/観測=旧道の件数)。
  - `removed_flags`(関数): 規則ごとの ``rate_rule_<名>_removed``(1=外した・0=旧道)。腕だけで決まる印(設定)。
  - `resolve`(関数): 過程の引数の腕(``None``=今の腕)を名に直す(名の誤りは止める)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--rate-rules``・試験の切替口)。組み立ての時に読む(ランの途中で変えても、そのランは変わらない)。
- 呼び手: `shibuya.cli`・`shibuya.engine.presence`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.logistics`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.runner`・`shibuya.engine.processes.salient`・`shibuya.engine.systems.build`・`shibuya.engine.systems.report`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/bridging/test_drives_from_vs_scoring.py`・`tests/economy/cp2/test_cp2_event_links.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/processes/test_rate_rules_1101.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/processes/test_salient.py`・`tests/engine/test_ablation23_switches.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/test_waste_sink_report.py`
- 環境変数: `SHIBUYA_RATE_RULES`
- 決定の ID: 10-13b/§0-6・11-01・11-01/§2

## [regional_clock.py](../../../../../../../src/shibuya/engine/regional_clock.py)

engine.regional_clock — 場所ごとの時計(第 6 期 6-3 時計の段 T4・TM1・腕 ``--clock regional``)。

- 公開の関数とクラス
  - `RegionalClock`(クラス): 場所ごとの時計(状態台帳の腕の行 ``T4W``・持ち主の名 ``clock``)。腕 regional のランだけ進行役が作る。
  - `arm`(関数): いまの腕(``global``=既定・``regional``・``mixed``=口だけ)。進行役と組み立てが読む。
  - `clock_kind`(関数): TM9 の欄 ``clock_kind``(区域ごとの時計の持ち主があれば ``regional``・無ければ今の ``steps``)。
  - `is_default`(関数)
  - `make`(関数): 進行役の口: 腕 regional のときだけ区域ごとの時計を作る(既定 global は None・mixed は止める=口だけ)。
  - `manifest_fields`(関数): manifest の ``clock``(腕 regional のランだけ・既定の腕は None=節を出さない)。
  - `region_of_cells`(関数): セル → 区域の番号(int64・0 から)と作り方の名。重心を 500 m の格子で塊にする(格子の (x, y) の昇順に番号)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--clock``・試験の切替口)。ランの始めに読む。
- import している内部モジュール: `shibuya.engine.owner_guard`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.conductor`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/engine/clock/test_tm4_regional_clock.py`
- 状態台帳の行
  - 持ち主 `clock`(`RegionalClock`)
    - `T4W` RegionalClock の区域ごとの窓・区域の事象・体の区域の写し・遅刻の日の表・計器(第 6 期 6-3 T4)(挙動 diag・復元 discardable・腕 clock-regional) 道筋 `clock._rc_events`・`clock._rc_head`・`clock._rc_late`・`clock._rc_meter`・`clock._rc_seq`・`clock._rc_snap` 書ける系: decide・llm_receive
- 環境変数: `SHIBUYA_CLOCK`
- 決定の ID: 10-12/§4-2・R-73

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
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.proximity`・`shibuya.engine.resolve`・`shibuya.foundation.hashing`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.contact_flags`
- 呼び手: `shibuya.engine.memory`・`shibuya.engine.relations_people`・`shibuya.engine.run`・`shibuya.engine.systems.build`
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

## [relations_people.py](../../../../../../../src/shibuya/engine/relations_people.py)

engine.relations_people — 人も記憶の一つ(第 6 期 6-5・腕 ``--memory-people memory``)の関係の読み口。

- 公開の関数とクラス
  - `PeopleRelationLayer`(クラス): 人も記憶の一つの腕の関係の読み口(器の人の行・関係の表を読まない)。``store`` は ``MemoryStore``(上限なし・M1)。
- import している内部モジュール: `shibuya.engine.memory_m1`・`shibuya.engine.relations`・`shibuya.foundation.vocab.contact_flags`
- 呼び手: `shibuya.engine.contact.book`・`shibuya.engine.memory`
- 読む試験: `tests/engine/memory/test_m4_m5_people.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`
- 状態台帳の行
  - 持ち主 `rel_layer` の別のクラス `PeopleRelationLayer`(行は `shibuya.engine.relations` のカードを見る)
- 決定の ID: 10-12/§4-6

## [removed_switches.py](../../../../../../../src/shibuya/engine/removed_switches.py)

engine.removed_switches — 消した旧道の切替口の一覧と、渡されたら止める口(第346 旧道の切替口の削除)。

- 公開の関数とクラス
  - `check_environment`(関数): 消した切替口の環境変数(:data:`REMOVED_ENV` の全部)のどれかが置かれていれば止める(ランの入口で呼ぶ)。
  - `message`(関数): 止めるときの文(名・消した段・安定版のタグ)。
  - `stop_if_set`(関数): ``names`` の環境変数のどれかが置かれていれば(空でない値)止める(``ValueError``)。
- 呼び手: `shibuya.cli`・`shibuya.engine.defect_fixes_1103`・`shibuya.engine.economy_rules`・`shibuya.engine.proximity`・`shibuya.engine.seat_release`・`shibuya.engine.systems.build`
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
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.body.rules`・`shibuya.engine.change_detect`・`shibuya.engine.commit`・`shibuya.engine.economy_stage2`・`shibuya.engine.energy`・`shibuya.engine.geometry`・`shibuya.engine.resume`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`・`shibuya.world.state`
- 呼び手: `shibuya.cli`・`shibuya.engine.activity`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar_self`・`shibuya.engine.duties.layer`・`shibuya.engine.familiarity`・`shibuya.engine.intent`・`shibuya.engine.memory`・`shibuya.engine.presence`・`shibuya.engine.processes.civic`・`shibuya.engine.processes.crowd`・`shibuya.engine.processes.environment`・`shibuya.engine.processes.goods_flow`・`shibuya.engine.processes.opening`・`shibuya.engine.processes.rail`・`shibuya.engine.processes.runner`・`shibuya.engine.processes.salient`・`shibuya.engine.relations`・`shibuya.engine.run`・`shibuya.engine.store_memory`・`shibuya.engine.systems.act`・`shibuya.engine.systems.body`・`shibuya.engine.systems.build`・`shibuya.engine.systems.decide`・`shibuya.engine.systems.judge`・`shibuya.engine.systems.perceive`・`shibuya.engine.systems.static_check`・`shibuya.engine.systems.talk`・`tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c7/attr_arms.py`・`tools/c7/occupancy_series.py`
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

## [resume.py](../../../../../../../src/shibuya/engine/resume.py)

日境界の再開と複数日の通しラン(10d・D-102 Q3・Q5・A10・A11)の状態の書き出しと読み込み。

- 公開の関数とクラス
  - `EnvironmentMismatchWarning`(クラス): 再開・再生の元(状態のファイル・テープ)を書いた環境の ``platform_id`` が今の環境と違う(10f・§8 の 6)。
  - `StateBundle`(クラス): 状態のまとまり 1 つ(見出し・SoA・外の状態・艦隊の未着の呼)。
  - `canonical_json`(関数): 正準の JSON(鍵を昇順・区切りを ``,`` ``:`` に固定・ASCII 以外もそのまま)。
  - `check_bundle`(関数): 読んだ中身を状態台帳の宣言と突き合わせる(壊れた値・取り違えた値で動き出さない)。
  - `check_item_kinds`(関数): 再開で戻す前に、保存の値と今の値の型を突き合わせる(10f・K23 (a))。違えば ``ValueError``。
  - `collect_items`(関数): 外の状態の値(台帳の ``full_items`` の道筋 → 値・宣言順)。持ち主が無い道筋は ``ABSENT_MARK``。
  - `collect_soa`(関数): SoA の列のうち軸 2 が ``discardable`` でない列の写し(置き場 → 列名 → 配列)。宣言順。
  - `declared_dtype`(関数): 台帳の SoA の行の型の略記(``i4``・``f4x2``・``u1x128``)→ (dtype, 2 次元目の長さ。1 次元なら ``None``)。
  - `environment_fields`(関数): 環境の欄(10f・K26 (a))。``platform``・``runtime`` はプロセスごとに 1 回だけ集める(``refresh=True`` で
  - `fingerprint`(関数): ``run_day`` の引数から設定の指紋を作る(再開で親と同じでなければ止める)。
  - `fingerprint_diff`(関数): 2 つの指紋で値の違う鍵(昇順)。
  - `path_identity`(関数): パス → 中身の同定(置き場所・書き方・OS に依らない)。ファイルは sha256、ディレクトリは
  - `platform_fields`(関数): 同じ環境かを見るための欄(決定論の方針: 同じ環境・同じ設定で同じ結果)。10f で ``environment_fields`` に広げた。
  - `read_state`(関数): 状態のまとまりを読む。npz+json だけ(外から来たファイルでもコードを動かさない)。
  - `run_id_of`(関数): ラン ID(実行ごとに一意・10d 検収 L6)。指紋・始めの T・親のラン ID に、実行の時刻とプロセス番号の印を混ぜる。
  - `state_path`(関数)
  - `warn_if_other_environment`(関数): 記録の環境の欄(``platform_id`` を持つ辞書)が今の環境と違えば警告を 1 行出す。返り値=警告したか。
  - `write_state`(関数): 状態のまとまりを 1 ファイル(npz+json・圧縮)に書く(一時ファイル → ``os.replace``)。返り値=ファイルのバイト数。
- import している内部モジュール: `shibuya.engine.class_ids`・`shibuya.engine.state_codec`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.foundation.hashing`・`shibuya.foundation.paths`
- 呼び手: `shibuya.engine.resolve`・`shibuya.engine.systems.build`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/economy/stage2/test_stage2_resume_arm.py`・`tests/economy/test_rules42_runs.py`・`tests/engine/batching/test_conductor_windows.py`・`tests/engine/calendar/test_ca1b_runs.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/clock/test_tm3_step_scope.py`・`tests/engine/clock/test_tm4_regional_clock.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/proximity/test_runs.py`・`tests/engine/speech/test_speech_arm_rows_resume.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/test_defect_fixes_1103.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_salt_seed_split_10f.py`・`tests/engine/test_seat_release_2_4.py`・`tests/engine/test_state_format_10f.py`・`tests/golden_env.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 環境変数: `NUMBA_NUM_THREADS`
- 決定の ID: D-102・第 330

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
- import している内部モジュール: `shibuya.agents.population`・`shibuya.agents.state`・`shibuya.engine.activity`・`shibuya.engine.arbiter`・`shibuya.engine.body.model`・`shibuya.engine.calendar`・`shibuya.engine.calendar2.layer`・`shibuya.engine.calendar3.layer`・`shibuya.engine.calendar_self`・`shibuya.engine.calendar_shadow`・`shibuya.engine.chooser`・`shibuya.engine.classical`・`shibuya.engine.commit`・`shibuya.engine.contact.layer`・`shibuya.engine.decision.layer`・`shibuya.engine.duties.layer`・`shibuya.engine.energy`・`shibuya.engine.experiment.layer`・`shibuya.engine.familiarity`・`shibuya.engine.geometry`・`shibuya.engine.growth_decl`・`shibuya.engine.intent`・`shibuya.engine.llm_bridge`・`shibuya.engine.memory`・`shibuya.engine.poi_target`・`shibuya.engine.presence`・`shibuya.engine.processes.opening`・`shibuya.engine.proximity`・`shibuya.engine.regional_clock`・`shibuya.engine.relations`・`shibuya.engine.resolve`・`shibuya.engine.rights.record`・`shibuya.engine.rules.table`・`shibuya.engine.run_kind`・`shibuya.engine.space.nav1`・`shibuya.engine.speech.layer`・`shibuya.engine.speech_clock`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger`・`shibuya.engine.step_scope`・`shibuya.engine.store_memory`・`shibuya.engine.systems.conductor`・`shibuya.engine.tape`・`shibuya.engine.wom`・`shibuya.foundation.decl.bridging`・`shibuya.foundation.growth`・`shibuya.foundation.manifest.schema`・`shibuya.foundation.manifest.sections`・`shibuya.foundation.ports.ledger`・`shibuya.foundation.ports.percept`・`shibuya.foundation.queues.batching`・`shibuya.foundation.queues.scheduler`・`shibuya.foundation.rng`・`shibuya.foundation.text.channels`・`shibuya.foundation.text.templates`・`shibuya.foundation.time_consts`・`shibuya.foundation.types`・`shibuya.foundation.vocab.actions`・`shibuya.llm.fleet`・`shibuya.llm.mock`・`shibuya.llm.undefined`・`shibuya.perception.renderer`・`shibuya.world.assets`・`shibuya.world.state`
- 呼び手: `shibuya.cli`・`shibuya.engine.systems.act`・`shibuya.engine.systems.body`・`shibuya.engine.systems.build`・`shibuya.engine.systems.decide`・`shibuya.engine.systems.judge`・`shibuya.engine.systems.llm_io`・`shibuya.engine.systems.observe`・`shibuya.engine.systems.perceive`・`shibuya.engine.systems.report`・`shibuya.engine.systems.run_end`・`shibuya.engine.systems.state_io`・`tools/c6/run_hash.py`・`tools/c7/occupancy_series.py`・`tools/instruments/anchor_gauge.py`
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

## [run_kind.py](../../../../../../../src/shibuya/engine/run_kind.py)

engine.run_kind — ランの種類(第 1 期 1-4・決定 10-12 §4-5 CP5-5「ランの種類を manifest に記録」)。

- 公開の関数とクラス
  - `check`(関数): 種類の名の検査(4 つの外は ``ValueError``)。
  - `decide`(関数): ``cli.run`` の規則: 試験 > 反実仮想(〔3-3〕申込書を渡した)> 腕 > 再現 の順。``testing`` を省くと ``in_test()``。
  - `in_test`(関数): pytest の試験の中か(``PYTEST_CURRENT_TEST`` が立っているか)。
  - `resolve`(関数): manifest に書く種類(``None``=決めていない=null のまま)。
- 呼び手: `shibuya.cli`・`shibuya.engine.run`
- 読む試験: `tests/engine/batching/test_conductor_windows.py`・`tests/engine/body/test_body_manifest.py`・`tests/engine/bridging/test_manifest_rules_bridges.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/speech/test_speech_cli.py`
- 環境変数: `PYTEST_CURRENT_TEST`
- 決定の ID: 10-12/§4-5

## [seat_release.py](../../../../../../../src/shibuya/engine/seat_release.py)

engine.seat_release — 在席の印を歩き出しで解く(第 2 期 2-4 V3・版上げ 2 回目)の見出しと再開の検査。

- 公開の関数とクラス
  - `check_resume`(関数): 再開のときに、保存したランの見出しの ``seat_release``(無ければ legacy=2-4 より前のラン)が walk かを確かめる(違えば止める)。
  - `header_fields`(関数): 状態のファイルの見出しの ``seat_release``(ランは常に ``{"mode": "walk"}``・walk の外の名は None)。
- import している内部モジュール: `shibuya.engine.removed_switches`
- 呼び手: `shibuya.engine.systems.build`・`shibuya.engine.systems.state_io`
- 読む試験: `tests/engine/test_seat_release_2_4.py`
- 環境変数: `SHIBUYA_SEAT_RELEASE`
- 決定の ID: 第 346

## [solar.py](../../../../../../../src/shibuya/engine/solar.py)

engine.solar — 太陽の位置(日の出・日の入り・太陽高度)と WBGT の推定(10e B6・第330)。

- 公開の関数とクラス
  - `daylight_phase`(関数): 日照の 3 値(構築段の ``daylight_phase`` と同じ規則)。
  - `heat_stage`(関数): WBGT → 暑さ段(0〜4)。
  - `hourly_wbgt`(関数): ``date`` の太陽高度(時の中ほど)と、その時の気象(再生日の行)から WBGT の推定値(丸めない)。
  - `solar_elevation_deg`(関数): 地方時 ``local_min``(0 時からの分)の太陽高度 [deg]。
  - `sun_minutes`(関数): 日の出・日の入りを**分に丸めた値**(W13 の ``sunrise``/``sunset`` 列の ``HH:MM`` と同じ丸め=``round``)。
  - `sun_times`(関数): 日の出・日の入り(地方時の 0 時からの分)。極夜・白夜は ``(None, None)``。
  - `wbgt_estimate`(関数): WBGT の推定式(屋外・実況が無いときの代わり=expedient)。
- import している内部モジュール: `shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.processes.environment`
- 読む試験: `tests/engine/test_weather_calendar_10e.py`
- 決定の ID: 第 330

## [spatial_index.py](../../../../../../../src/shibuya/engine/spatial_index.py)

engine.spatial_index — 近傍の索引(第 2 期 2-2 段 11a・セル廃止の役割 ①「近傍の索引」の最初の部品)。

- 公開の関数とクラス
  - `SpatialIndex`(クラス): 近傍の索引(層ごとの ``cell_m`` の格子・刻みごとに作って捨てる・組み立ての後は読むだけ)。
  - `expand_ranges`(関数): 範囲 ``[lo, hi)`` の並び → (範囲の番号, 位置)(``np.repeat`` の形・ループなし)。
- 呼び手: `shibuya.engine.proximity`
- 読む試験: `tests/engine/proximity/test_index.py`

## [speech_clock.py](../../../../../../../src/shibuya/engine/speech_clock.py)

engine.speech_clock — 会話の時計(第 6 期 6-3 時計の段 T2・TM3・腕 ``--talk-clock mora``)。

- 公開の関数とクラス
  - `ChatTiming`(クラス): 打つ道具(``チャット``)の時間=C1(チャットの会話の状態)が刺す口。値は空欄(None)=C1 で入れる。
  - `QueueRouter`(クラス): 全体で 1 つの時計(``engine.batching.WindowQueue``)に発言の事象を置く口(区域ごとの時計は
  - `SpeechTiming`(クラス): 話す道具(``対面``)の時間: 発言の長さ = モーラ数 × モーラの長さ × 揺れ × 相手の項・間 = 日本語の平均。
  - `TalkClock`(クラス): 会話の時計(状態台帳の腕の行 ``TCR``・``TCC``・持ち主の名 ``talk_clock``)。腕 ``mora`` のランだけ組み立てが作る。
  - `arm`(関数): いまの腕(``table``=既定・``mora``)。組み立てのときに読む。
  - `is_default`(関数)
  - `language_of`(関数): 本文の言語(仮名か漢字がある=``ja``・英数字だけ=``other``・どちらも無い=``none``)。
  - `make`(関数): 組み立ての口: 腕 mora のときだけ会話の時計を作る(既定 table は None=今の道)。
  - `manifest_fields`(関数): manifest の ``talk_clock``(腕 mora のランだけ・既定の腕は None=節を出さない)。
  - `person_mora_len_s`(関数): 体 ``agent`` のモーラの長さ[秒]\(規則 2=切った対数正規・母集団の seed と体の番号の Philox・状態を持たない)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--talk-clock``・試験の切替口)。組み立ての時に読む(ランの途中で変えてもそのランは変わらない)。
  - `utterance_jitter`(関数): 発言ごとの揺れ(規則 3=平均 1 の対数正規・CV 0.42)。鍵=話し手・発言を作った時刻[ns]・会話の番号(TM7 (d))。
- import している内部モジュール: `shibuya.engine.owner_guard`・`shibuya.engine.speech.port`・`shibuya.foundation.rng`・`shibuya.foundation.time_consts`・`shibuya.foundation.vocab.actions`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`shibuya.engine.systems.conductor`
- 読む試験: `tests/engine/clock/test_tm2_talk_clock.py`・`tests/engine/clock/test_tm4_regional_clock.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主 `talk_clock`(`TalkClock`)
    - `TCC` TalkClock の会話の時計・予約した発言・計器(第 6 期 6-3 T2)(挙動 diag・復元 discardable・腕 talk-clock) 道筋 `talk_clock._tc_line`・`talk_clock._tc_meter`・`talk_clock._tc_pending` 書ける系: conversation・decide・llm_receive
    - `TCR` TalkClock の話す速さの控え(体 → モーラの長さ・第 6 期 6-3 T2)(挙動 diag・復元 discardable・腕 talk-clock) 道筋 `talk_clock._tc_rate` 書ける系: decide・llm_receive
- 環境変数: `SHIBUYA_TALK_CLOCK`
- 決定の ID: 10-12/§4-2・R-73・R-73 #30・R-73 #32・R-111・R-111 #38・R-111 #42・R-111 #44

## [state_codec.py](../../../../../../../src/shibuya/engine/state_codec.py)

状態のファイルの直列化 npz+json(10f・K23 (a))。読むだけでコードが動く経路を持たない。

- 公開の関数とクラス
  - `Decoder`(クラス): (JSON の木, 配列の読み口) → 値の木。許可の表の外は ``StateFormatError``。
  - `Encoder`(クラス): 値の木 → (JSON にできる木, 配列の辞書)。
  - `StateFormatError`(クラス): 状態のファイルの中身が形式・許可の表・台帳の宣言に合わない(読まない)。
  - `allowed_class`(関数): 許可の表の名前 → クラス(表に無ければ ``StateFormatError``)。import するのは表に書いたモジュールだけ。
  - `declared_fields`(関数): 許可したクラス(``object`` の形)の欄の集合。dataclass は ``fields``・ほかは ``CLASS_FIELDS``。
  - `dumps`(関数): 値の木 → npz のバイト列(圧縮)。
  - `loads`(関数): npz のバイト列 → 値の木。``np.load(allow_pickle=False)`` と許可したクラスの表だけで組み立てる。
  - `qualname`(関数): 型の凍結の名(〔移す段 1〕``engine.class_ids`` の固定の表から引く)。
- import している内部モジュール: `shibuya.engine.class_ids`
- 呼び手: `shibuya.engine.resume`
- 読む試験: `tests/engine/state/test_class_ids.py`・`tests/engine/test_state_format_10f.py`

## [state_hashes.py](../../../../../../../src/shibuya/engine/state_hashes.py)

behavior-hash と full-hash(10b・A2・A3)。表は ``engine.state_ledger`` だけから読む。

- 公開の関数とクラス
  - `behavior_hash`(関数): behavior-hash。
  - `component_digests`(関数): 列ごと(``置き場.列名``)と外の状態の道筋ごと(``行の鍵:道筋``)の digest(16 進 32 字)。読むだけ。
  - `external_digest`(関数): 外の状態の digest と、行ごとの直列化のバイト数(``items`` の既定=full に入る行)。
  - `full_hash`(関数): full-hash と、外の状態の行ごとのバイト数(``sizes``・記録用)。
  - `item_digest`(関数): 属性 1 本の digest(32 B)と直列化のバイト数(「無い」は印 1 B)。行の ``ordered`` の印を見る。
  - `resolve_item`(関数): ``"runner.salient.rng"`` → 値。途中の持ち主が ``None`` なら ``_ABSENT``。
  - `to_state`(関数): 値を決定論のバイト列にする(外の状態の直列化の書き手)。``ordered`` は辞書の挿入順を保つ。
- import している内部モジュール: `shibuya.engine.class_ids`・`shibuya.engine.state_ledger`・`shibuya.foundation.hashing`
- 呼び手: `shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.state_io`・`tools/bytecheck/check.py`
- 読む試験: `tests/engine/discard_probe.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/speech/test_speech_arm_rows_resume.py`・`tests/engine/state/shaped_names.py`・`tests/engine/state/test_class_ids.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/perception/facts/test_percept_is_scratch.py`
- 決定の ID: 第 330

## [state_ledger.py](../../../../../../../src/shibuya/engine/state_ledger.py)

状態台帳の宣言(10b・A3「挙動」と「復元」の 2 軸・機械可読の 1 ファイル)。

- 公開の関数とクラス
  - `AstAllow`(クラス): AST の検査で「読み手」として数えても許す場所(``path`` と、その行に含まれる文字列で引く)。
  - `Excluded`(クラス): 台帳の行に入れない属性(``owner`` の ``attrs``・分類 ``kind``・理由)。
  - `LedgerRow`(クラス): 状態台帳の 1 行。
  - `arm_items`(関数): 〔第 1 期 1-8b〕腕の行のうち根の持ち主が居る(腕が立っている)行の ``(行の鍵, 属性の道筋)``(宣言順・``hash_skip`` を除く)。
  - `arm_rows`(関数): 〔第 1 期 1-8b〕腕の行(``LedgerRow.arm`` のある外の状態の行・宣言順)。
  - `behavior_columns`(関数)
  - `behavior_excluded`(関数): behavior-hash で ``state_hash(exclude=…)`` に渡す列名(軸 1 が ``no``/``diag`` の列)。
  - `behavior_items`(関数): behavior-hash に入れる外の状態の ``(行の鍵, 属性の道筋)``(軸 1 が behavior の行・``hash_skip`` を除く)。
  - `counts`(関数): 行の数(記録と試験が読む)。
  - `excluded_attrs`(関数): 持ち主 → 属性 → 除外の項。
  - `external_rows`(関数)
  - `full_excluded`(関数): full-hash で除く列名(軸 2 が ``discardable`` の列)。
  - `full_items`(関数): full-hash に入れる外の状態の ``(行の鍵, 属性の道筋)``(台帳の宣言順)。〔1-8b〕腕の行は入れない(``arm_items``)。
  - `item_attrs`(関数): 持ち主 → 台帳の行の ``items`` に載る属性(持ち主そのものが ``items`` に載る行は ``"*"``)。
  - `row`(関数)
  - `rows`(関数): 台帳の行(``place`` を渡せばその置き場だけ)。
  - `soa_rows`(関数)
- 呼び手: `shibuya.engine.resolve`・`shibuya.engine.resume`・`shibuya.engine.run`・`shibuya.engine.state_hashes`・`shibuya.engine.state_ledger_ast`・`shibuya.engine.systems.probe`・`shibuya.engine.systems.state_io`・`tools/bytecheck/check.py`
- 読む試験: `tests/economy/cp2/test_cp2_writes_declared.py`・`tests/engine/calendar/test_ca1b_unit.py`・`tests/engine/calendar/test_calendar_shadow.py`・`tests/engine/calendar2/test_ca2_runs.py`・`tests/engine/calendar3/test_ca3_runs.py`・`tests/engine/contact/test_c1_runs.py`・`tests/engine/contact/test_c2_runs.py`・`tests/engine/discard_probe.py`・`tests/engine/duties/test_du_runs.py`・`tests/engine/events/test_e_writes_declared.py`・`tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/memory/test_mr65_review_fixes.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/speech/test_speech_arm_rows_resume.py`・`tests/engine/speech/test_speech_default_off_invariance.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/systems/test_systems_table.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_version_bump_10e.py`・`tests/engine/tools/test_c0_contacts_in_relations.py`・`tests/perception/facts/test_percept_is_scratch.py`・`tests/tools/test_repo_guide.py`
- 読む試験(道筋で): `tests/tools/test_pkgmove.py`
- 状態台帳の行
  - 持ち主を引けない行(道筋が `OWNER_CLASSES` に無い・道筋なし)
    - `O43` run_day の局所 pending(適用待ちの応答)(挙動 behavior・復元 required) 道筋 `run_day.pending` 書ける系: apply_responses・decide・drain・llm_receive
    - `O44` run_day の局所 fleet_deferred・fleet_waiting(挙動 behavior・復元 required) 道筋 `run_day.fleet_deferred`・`run_day.fleet_waiting` 書ける系: decide・drain・llm_receive・wake_filter
    - `O65` LLMBridge・TapeWriter・FleetBridge の計数・行・処理中の呼(挙動 no・復元 discardable) 書ける系: (宣言なし)
    - `O96` run_day の局所 replay_inbox(再生の到着待ち)(挙動 no・復元 required) 道筋 `run_day.replay_inbox` 書ける系: decide・drain・llm_receive
    - `P` TickScratch.percepts(知覚の事実 Percept・第 1 期 1-2)(挙動 no・復元 discardable) 書ける系: (宣言なし)
    - `PX0` TickScratch.near_index(近傍の索引 SpatialIndex・第 2 期 2-2 段 11a)(挙動 no・復元 discardable) 書ける系: (宣言なし)
- 決定の ID: 10-12/§4-4・10-12/§4-11・11-01・11-03・11-03/§3・第 330・第 346

## [state_ledger_ast.py](../../../../../../../src/shibuya/engine/state_ledger_ast.py)

追加 C の静的な検査: SoA の列ごとの読み手を AST で数え、状態台帳の軸 1 と食い違えば知らせる(10b)。

- 公開の関数とクラス
  - `DiagExit`(クラス): 診断の出口の関数(``qualname`` は ``クラス.メソッド`` か関数名。末尾の ``.*`` はそのクラスの全メソッド)。
  - `ExtAllow`(クラス): 外の状態の軸 1 の場所ごとの許可(属性の名前・当たる数・場所と理由・当たる行の関数の名前)。
  - `ExtScan`(クラス)
  - `ExtSite`(クラス): 持ち主の外の読みの場所(``func`` は ``クラス.メソッド`` か関数名・入れ子は ``.`` でつなぐ)。
  - `ScanResult`(クラス)
  - `Site`(クラス): 読みの場所(``path`` は ``src/shibuya`` からの相対・``text`` はその行の文字列)。
  - `check`(関数): 台帳の軸 1 と AST の読み手の食い違い(空なら合格)。
  - `check_external`(関数): 外の状態の軸 1 の検査(空なら合格)。場所ごとの許可は当たる数が宣言と同じであること(U5)。
  - `class_attrs`(関数): クラス ``cls`` の属性(メソッドの中の ``self.x = …``・``self.x += …``・``self.x[...] = …`` とクラスの欄)。
  - `class_defined_names`(関数): 属性の名前 → それを持つクラス(``path:Class``)。``self.x = …``(どのメソッドでも)・クラスの本体の代入と注釈・
  - `coverage`(関数): ``(持ち主 → 台帳にも除外にも無い属性, 食い違い)``。食い違い=除外と行の両方に載る・クラスに無い属性を載せた。
  - `declared_columns`(関数): ``declare("名前", ...)`` の列名(置き場 ``agents``・``cells``・``pois``・``perception`` → 宣言順)。
  - `ext_attr_rows`(関数): 外の状態の行が指す持ち主のクラスの属性の名前 → (持ち主, 行の鍵, 軸 1)。``run_day`` の局所の行は除く。
  - `ext_reason`(関数): 規則で許す理由の種類(``generic``・``exit``・``result``・``collision``)。``None`` なら規則では許さない。
  - `reader_counts`(関数): 台帳の SoA の行ごとの読み手の数(記録用)。
  - `runtime_uncovered`(関数): 実行時の網羅(検収 2-6): 各持ち主の**インスタンス**の ``vars()``(と ``__slots__``)を台帳+除外の一覧に
  - `scan`(関数): ``root``(= ``src/shibuya``)の下を走査する。``files``・``names`` を渡せばその範囲だけ(試験用)。
  - `scan_external`(関数): ``root``(= ``src/shibuya``)の下で、軸 1 が no/diag の外の状態の属性の「持ち主の外の読み」を集める。
  - `source_files`(関数): 走査の対象(``src/shibuya`` 全体・``build/`` を除く)。
- import している内部モジュール: `shibuya.engine.state_ledger`
- 呼び手: `shibuya.engine.systems.allow`
- 読む試験: `tests/engine/experiment/test_x33_run.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_mr65_guards.py`・`tests/engine/state/test_move_prep_stage2.py`・`tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_state_format_10f.py`・`tests/engine/test_state_ledger_10b.py`
- 決定の ID: 第 304

## [step_scope.py](../../../../../../../src/shibuya/engine/step_scope.py)

engine.step_scope — 何かあった体だけ(第 6 期 6-3 時計の段 T3・腕 ``--step-scope changed``)。

- 公開の関数とクラス
  - `StepScope`(クラス): 何かあった体の印(状態台帳の腕の行 ``T3M``・持ち主の名 ``step_scope``)。腕 changed のランだけ組み立てが作る。
  - `arm`(関数): いまの腕(``all``=既定・``changed``)。組み立てのときに読む。
  - `is_default`(関数)
  - `make`(関数): 組み立ての口: 腕 changed のときだけ印の持ち主を作る(既定 all は None=今の道)。
  - `manifest_fields`(関数): manifest の ``step_scope``(腕 changed のランだけ・既定の腕は None=節を出さない)。
  - `set_arm`(関数): 腕を選ぶ(CLI ``--step-scope``・試験の切替口)。組み立ての時に読む。
- import している内部モジュール: `shibuya.engine.change_detect`・`shibuya.engine.owner_guard`
- 呼び手: `shibuya.cli`・`shibuya.engine.run`・`shibuya.engine.systems.build`
- 読む試験: `tests/engine/clock/test_tm3_step_scope.py`
- 状態台帳の行
  - 持ち主 `step_scope`(`StepScope`)
    - `T3M` StepScope の変化の印(内受容の値と段の写し・前に跨いだ体・計器・第 6 期 6-3 T3)(挙動 diag・復元 discardable・腕 step-scope) 道筋 `step_scope._ss_copy`・`step_scope._ss_crossed`・`step_scope._ss_meter` 書ける系: detect
- 環境変数: `SHIBUYA_STEP_SCOPE`
- 決定の ID: 10-12/§4-2

## [store_choice.py](../../../../../../../src/shibuya/engine/store_choice.py)

engine.store_choice — **想起優先の候補合成**と**決め手の記録**(D-120 7c・N6 (a)・N7 (a)・N8 (a)・第298)。

- 公開の関数とクラス
  - `StoreChoice`(クラス): 想起優先の候補合成と決め手の記録(1 ランに 1 つ・``TargetResolver`` が持つ)。
  - `walk_m_per_tick`(関数): 体ごとの歩速[m/tick]\(エンジンの移動の物差し)。node=W1 の辺長の平均・edge と nav1=希望速度 × tick 秒。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.chooser`・`shibuya.engine.store_memory`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.engine.systems.build`
- 読む試験: `tests/engine/test_sim_time_T.py`・`tests/engine/test_store_choice.py`
- 読む試験(道筋で): `tests/engine/systems/test_fix_guards.py`・`tests/engine/systems/test_stage_a_guard.py`
- 状態台帳の行
  - 持ち主 `poi_resolver.store_choice`(`StoreChoice`)
    - `O13` StoreChoice choice_poi・choice_reason・stats・by_hour(挙動 diag・復元 discardable) 道筋 `poi_resolver.store_choice.by_hour`・`poi_resolver.store_choice.choice_poi`・`poi_resolver.store_choice.choice_reason`・`poi_resolver.store_choice.stats` 書ける系: apply_responses・memory
    - `O14` StoreChoice _b_tick・_b_off(挙動 no・復元 derivable) 道筋 `poi_resolver.store_choice._b_off`・`poi_resolver.store_choice._b_tick` 書ける系: memory
    - `O68` StoreChoice first_by_reason・visits_by_reason(挙動 diag・復元 discardable) 道筋 `poi_resolver.store_choice.first_by_reason`・`poi_resolver.store_choice.visits_by_reason` 書ける系: apply_responses・memory
- 決定の ID: D-120・D-121・第 296・第 298

## [store_memory.py](../../../../../../../src/shibuya/engine/store_memory.py)

engine.store_memory — **店の評価の記憶**(D-120 7a・N1 (a)・N2 (i)(iii)・N4 (a)・N5 (a)・第296)。

- 公開の関数とクラス
  - `StoreColumns`(クラス): 〔第 6 期 6-5・検収 M4〕店の評価の行の列(``(体, 幅)``)。既定=体の表の ``sm_*`` そのもの(読む口=書かない)。
  - `StoreMemory`(クラス): 店の評価の記憶の書き手と読み口(``MemoryLayer`` が持つ・``--store-memory on`` のランだけ)。
  - `StoreRows`(クラス): 1 体の店の評価の行(空でない行だけ・行番号の順)。本段では誰も読まない(7c の読み口)。
  - `check_store_decay`(関数): 減衰の形を検査して返す(:data:`STORE_DECAY_MODES` のどれか)。
  - `check_store_sigma`(関数): 出どころ別の σ の表を検査して、全部の鍵を持つ辞書で返す(欠けた鍵は既定値)。
  - `valence_of_result`(関数): 結果コード → 向き(``OK`` +1・:data:`STORE_VALENCE_NEGATIVE` −1・それ以外 0)。
- import している内部モジュール: `shibuya.agents.state`・`shibuya.engine.memory`・`shibuya.engine.resolve`・`shibuya.foundation.time_consts`
- 呼び手: `shibuya.cli`・`shibuya.engine.memory`・`shibuya.engine.memory_shops`・`shibuya.engine.run`・`shibuya.engine.store_choice`・`shibuya.engine.systems.build`・`shibuya.engine.wom`
- 読む試験: `tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_store_choice.py`・`tests/engine/test_store_memory.py`・`tests/engine/test_wom.py`
- 状態台帳の行
  - 持ち主 `mem_layer.store`(`StoreMemory`)
    - `O12` StoreMemory stats(挙動 diag・復元 discardable) 道筋 `mem_layer.store.stats` 書ける系: decide・llm_receive・memory
- 決定の ID: R-49・D-120・D-121・第 296

## [tape.py](../../../../../../../src/shibuya/engine/tape.py)

engine.tape — LLM 録画テープ(1呼=1行 Parquet/zstd)と完全一致リプレイ。

- 公開の関数とクラス
  - `Replay`(クラス): テープからの完全一致リプレイ。**テープ外は必ず失敗**(実LLMへ落とさない)。
  - `Tape`(クラス): テープの読み出し(``calls.parquet`` + ``blocks.parquet``)。
  - `TapeDeferred`(クラス): 引いた行が**繰り延べ行**だった(=この呼に応答は無い・D-58)。
  - `TapeHit`(クラス): ``Replay.lookup_row`` の戻り(1行ぶんの再生に要る欄だけ)。
  - `TapeMiss`(クラス): テープに無い呼び出しを引いた(=リプレイ失敗。実LLMへは落とさない)。
  - `TapeRow`(クラス): 1呼=1行(``deferred=1`` なら「答えの返らなかった 1 呼」=D-58)。
  - `TapeWriter`(クラス): テープ書き出し(Parquet/zstd)。``with`` で使うか ``close()`` を呼ぶこと。
  - `block_id_for`(関数): 共有プロンプトブロックの内容アドレス ``blake3(text)[:16]`` の16進32桁。
  - `read_run_meta`(関数): テープの脇の meta を読む(無ければ空 dict=10a より前の録画)。
  - `tape_v4_fields`(関数): テープ版 4(10e・E5)の 7 列の値を、描画の出力(``RenderedPrompt``)か艦隊の呼(``LLMCall``)から作る。
- import している内部モジュール: `shibuya.foundation.hashing`・`shibuya.foundation.text.channels`
- 呼び手: `shibuya.engine`・`shibuya.engine.experiment.branch`・`shibuya.engine.llm_bridge`・`shibuya.engine.run`・`shibuya.engine.systems.build`・`tools/c6/ablation1_fixed_vs_ranking.py`・`tools/c6/c6lib.py`・`tools/c6/format_role_rates.py`・`tools/c6/t6_bit_reproduce.py`・`tools/c6/t7_distribution.py`・`tools/c8/ablation_runner.py`・`tools/fig/fig_ab7_actions.py`・`tools/fig/fig_ab7c_vocab.py`・`tools/fig/fig_d91_ride_chain.py`・`tools/vocab/registry_from_tape.py`
- 読む試験: `tests/c6/test_c6lib_scenes.py`・`tests/engine/experiment/test_cf33b_switch.py`・`tests/engine/memory/test_m0_cli.py`・`tests/engine/memory/test_m0_recall_equivalence.py`・`tests/engine/memory/test_m0_shown_recorded.py`・`tests/engine/memory/test_m0_store_schema.py`・`tests/engine/memory/test_m1_runs.py`・`tests/engine/memory/test_m2_cue.py`・`tests/engine/memory/test_mr65_grain_and_cli.py`・`tests/engine/multiday/test_md23_body_events.py`・`tests/engine/multiday/test_md23_resume.py`・`tests/engine/processes/test_rng_scheme_10c.py`・`tests/engine/tape_analysis.py`・`tests/engine/test_10a_review_fixes.py`・`tests/engine/test_activation_10e.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/test_fleet_wiring.py`・`tests/engine/test_llm_mock.py`・`tests/engine/test_memory_recall.py`・`tests/engine/test_response_delay.py`・`tests/engine/test_resume_10d.py`・`tests/engine/test_sim_time_T.py`・`tests/engine/test_tape.py`・`tests/engine/test_tape_deferred.py`・`tests/engine/test_tape_wiring.py`・`tests/engine/test_undefined_action.py`・`tests/engine/test_version_bump_10e.py`・`tests/llm/test_fleet.py`
- 状態台帳の行
  - 持ち主 `bridge.tape`(`TapeWriter`)
    - `O87` TapeWriter の書き出し待ちの行と計数(挙動 no・復元 discardable) 道筋 `bridge.tape._arm_values`・`bridge.tape._blocks`・`bridge.tape._n_deferred`・`bridge.tape._n_written`・`bridge.tape._rows` 書ける系: close_final・decide・drain・llm_receive
- 決定の ID: 10-13b/§3・D-58・第 295

## [wom.py](../../../../../../../src/shibuya/engine/wom.py)

engine.wom — **会話からの店の抽出**(D-120 7b・N3 (a)・口コミ=伝聞の書き手・第297)。

- 公開の関数とクラス
  - `WomExtraction`(クラス): 1 発話の抽出結果。
  - `WomExtractor`(クラス): 店名の辞書と評価語の辞書(1 ランに 1 つ・世界は読むだけ)。
  - `check_wom_source`(関数): ``--wom-source`` の値を検める。
  - `hear`(関数): 抽出した店を聞き手(宛先)の店の行へ(出どころ=伝聞・精度 +重み × 1/σ²)→ 書いた行の数。
  - `normalize_v0`(関数): 正規化 v0: NFKC(全角/半角)・英字は小文字・空白を全部消す。
- import している内部モジュール: `shibuya.engine.poi_target`・`shibuya.engine.store_memory`
- 呼び手: `shibuya.engine.run`・`shibuya.engine.speech.layer`・`shibuya.engine.systems.build`・`shibuya.engine.systems.llm_io`
- 読む試験: `tests/engine/speech/test_wom_from_utterance_roundtrip.py`・`tests/engine/test_wom.py`
- 状態台帳の行
  - 持ち主 `wom`(`WomExtractor`)
    - `O15` WomExtractor stats・top・unmatched_words(挙動 diag・復元 discardable) 道筋 `wom.stats`・`wom.top`・`wom.unmatched_words` 書ける系: decide・llm_receive・memory
- 決定の ID: D-120・第 297・第 298・第 312
