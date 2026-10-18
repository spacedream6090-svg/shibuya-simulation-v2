"""ラン manifest(``RunResult.run_manifest_fields``)の欄を「設定」「観測」「環境」に分ける表(10f・K22 (a))。

欄の名前と値は変えない。manifest に表(``manifest_sections``)を 1 つ足し、どの欄がどの節かを道筋で書く。

- **設定(config)**: ランの前に決まる値(引数・データの同定・コードの定数の写し)。同じ設定なら seed が違っても同じ。
  seed の交換可能性の検査(``tools/c7/seed_exchangeability.py``)はこの節だけを比べる。
- **観測(observed)**: ランの結果(件数・分布・状態のハッシュ・再開の記録)。seed で違って当然。比べない(報告だけ)。
- **環境(environment)**: 環境の欄と ``env_id``(10f)。比べるが、違っても警告だけ(交換可能性は落とさない)。

道筋は ``a.b.c``(入れ子の辞書の鍵を ``.`` でつなぐ)。**最も長く一致する道筋**の節を使う。manifest の一番上の欄は
すべて表に載せる(``tests/engine/test_env_and_sections_10f.py`` が全部の欄が載っているかを確かめる=新しい欄を
足したら節を決める)。観測と設定が混ざった辞書(``MIXED``)は**子の鍵を全部**表に書く(10f 検収 N3)。混ざった
辞書の下の葉が混ざった辞書そのものの道筋にしか当たらない(=表に無い新しい鍵)ときは、同じテストが落ちる
(新しい鍵を足したら節を決めさせる)。子が中身ごと観測(または設定)の辞書(``energy.counts`` など・鍵が動的な
ものを含む)は、その子の道筋 1 つで中身全部を表す。

形を「節ごとの入れ子」(``{"config": {...}, "observed": {...}}``)にしなかった理由: 欄の名前と場所を変えると
``run_manifest_fields()["rng_scheme"]`` の形で読む 150 か所あまりのテストと道具(``tools/c8`` など)が全部
変わる。表を足す形なら欄は 1 つも動かず、表を読まない読み手には今と同じ manifest に見える。

**未リサーチ(expedient)**: 節の振り分けは実行役が欄の中身を読んで決めた。確かめ方: mock 5,000 体・世界資産・1 日の
既定 v3・記憶+関係・classical+記憶+関係・記憶+店の記憶の seed 1 と 2 で、設定の葉が seed で動かないこと
(関係の初期化が実際に走る構成=10f 検収 N1。300 体では関係の初期化が空になり試験にならない)。
"""

from __future__ import annotations

from typing import Any, Final, Mapping

#: 表の形式の版。
SECTIONS_SCHEMA: Final[str] = "shibuya.engine/manifest-sections/1"
CONFIG: Final[str] = "config"
OBSERVED: Final[str] = "observed"
ENVIRONMENT: Final[str] = "environment"
SECTION_VALUES: Final[tuple[str, ...]] = (CONFIG, OBSERVED, ENVIRONMENT)

_C, _O, _E = CONFIG, OBSERVED, ENVIRONMENT

#: 観測と設定が混ざった辞書の道筋(子の鍵を全部表に書く=10f 検収 N3)。``_mixed`` が足す。
MIXED: Final[list[str]] = []


def _mixed(root: str, *, config: tuple[str, ...], observed: tuple[str, ...]) -> dict[str, str]:
    """混ざった辞書 ``root`` の表の行(``root`` そのものは観測・子は書いたとおり)。"""
    dup = set(config) & set(observed)
    if dup:
        raise ValueError(f"{root}: 設定と観測の両方にある鍵 {sorted(dup)}")
    MIXED.append(root)
    return {root: OBSERVED, **{f"{root}.{k}": CONFIG for k in config}, **{f"{root}.{k}": OBSERVED for k in observed}}


#: 道筋 → 節。一番上の欄は全部載せる。
PATHS: Final[dict[str, str]] = {
    # ---- 環境(10f) ----
    "env_id": _E, "environment": _E,
    # ---- 表そのもの(コードが同じなら同じ=設定として比べる) ----
    "manifest_sections": _C,
    # ---- データ・暦・時間 ----
    "registry_hash": _C, "replay_date": _C, "tick_seconds": _C, "start_sim_datetime": _C, "sim_days": _C,
    "calendar": _C, "response_delay": _C, "rng_scheme": _C, "hash_scheme": _C, "template_sha256": _C, "catalog_sha16": _C,
    "frozen_sources": _C, "process_ids": _C, "ablations": _C, "fleet": _C,
    # ---- 10f 第 2 段(K21 (a)): 母集団の seed(salt の比較では揃える=設定) ----
    "population_seed": _C,
    # ---- 10f 第 2 段の直し(S1): 環境の seed(気象・大きな催し・道路工事) ----
    "environment_seed": _C,
    # ---- 〔第330・RET〕10e(B1)の旧資産の切替口の欄 world_assets_pre10e は切替口と一緒に消した ----
    # ---- 10e(B6・第330): 天気の規則と日ごとの暦の日付・再生日・層・影(replay_date と同じ設定) ----
    "weather": _C,
    # ---- 第 1 期 1-1 T0(TM9・GPU 無しの欄): 時計の種類と幅・つなぎの台帳の数は設定、呼び出し数(判断モデル/LLM)は観測 ----
    "clock_kind": _C, "step_seconds": _C, "bridges_count": _C, "calls_by_model": _O,
    # ---- 第 1 期 1-4: 規則の表の版(表の sha=CP10)・ランの種類(CP5-5)。どちらもランの前に決まる=設定 ----
    "rules_version": _C, "run_kind": _C,
    # ---- 1-4 検収 L1: つなぎの台帳の中身の sha(設定) ----
    "bridges_version": _C,
    # 第 1 期 1-2: Percept の形・欄の数・空の欄(コードで決まる=設定)
    "percept": _C,
    # ---- 第 1 期 1-5: 権利台帳の行数と分布・許可のない行動の数(計器=観測。権利は行動で変わる段=2-1 で動く) ----
    "rights": _O,
    # ---- 第 1 期 1-7: 道具の台帳の数・グループの数・連絡先の印の数・店の番号の表・看板の印(計器=観測。連絡先の印は関係辺の
    # 押し出しで動く・グループと台帳は C1 で本人の行動で動く) ----
    "tools": _O,
    # ---- 状態のハッシュ・再開・日ごとの締め(観測) ----
    "state_hashes": _O, "state_hashes.ledger_version": _C,
    "state_hashes_end_of_day": _O,
    "resume": _O, "finished": _O, "parent_run": _O, "resumed_at_T": _O, "daily": _O, "day_heads": _O,
    # ---- L4 の監査(線は設定・呼数と超過は観測) ----
    "budget_mode": _C, "l4_scale": _C, "budget_per_tick": _C, "l4_line": _C, "l4_notes": _C,
    "l4_conversation_line": _C,
    "llm_calls_total": _O, "llm_calls_per_agent_day": _O, "l4_exceeded": _O, "l4_conversation_share": _O,
    "l4_conversation_exceeded": _O,
    # ---- 腕(設定) ----
    "p_notice_ablation": _C, "p_notice_d50_scale": _C, "refractory_scale": _C, "signage": _C, "signage_p_see": _C,
    "intent_mode": _C, "vocab_version": _C, "role_words": _C, "activity": _C, "eatery": _C, "chooser": _C,
    "poi_target": _C, "move_search_radius": _C, "mock_move_target_p": _C, "intent_max_ticks": _C,
    "mock_out_of_cell_target_p": _C, "familiarity": _C, "familiarity_k": _C, "hunger_model": _C, "energy_rate": _C,
    "meal_sleep_defer": _C, "home_meal": _C, "hunger_words": _C, "policy": _C, "memory": _C, "memory_n": _C,
    "store_memory": _C, "synonym_table_version": _C, "sleep_suppression": _C, "plan_sleep": _C,
    "plan_executor": _C, "exit_mode": _C, "attendance_rate": _C, "derive_rule": _C, "outside_suppression": _C,
    "geometry": _C, "area_source": _C, "seat_area_eatery_m2": _C, "seat_area_retail_m2": _C, "attention": _C,
    # ---- 計数・分布(観測) ----
    "activity_kind_counts": _O, "target_resolution": _O, "move_resolution": _O, "intero_crossings": _O,
    "calls_by_condition": _O, "action_usage": _O, "t3_ok": _O,
    # ---- 観測と設定が混ざった辞書(MIXED): 子の鍵を全部書く(10f 検収 N3) ----
    **_mixed("state_hashes", config=("ledger_version",),
             observed=("behavior_hash", "full_hash", "full_external_bytes", "full_external_bytes_by_row")),
    **_mixed("intent", config=("max_ticks",), observed=(
        "proposed", "proposed_by_kind", "set", "set_by_action", "set_failed", "set_failed_by_result", "arrived", "done",
        "done_queued", "done_by_action", "failed", "failed_by_result", "too_far", "dropped", "kept",
        "latest_activity_used", "bed_skipped_sleep_pending", "exec_not_applied", "cell_block_suppressed",
        "expiry_suppressed", "mean_ticks", "b5_lines", "b5_lines_over_budget", "b6_named_closed_notes")),
    **_mixed("familiarity_summary", config=("k", "d"), observed=(
        "counts", "rows_used_per_agent", "full_agents", "visits_per_agent", "exposures_per_agent", "rows_by_kind",
        "rows_visit_only", "rows_exposure_only", "rows_both", "A", "A_visit_only", "A_exposure_only", "A_both",
        "top3_kinds", "exposures_signage_entry_by_kind")),
    # 空腹の要約: 定数の表(METs・窓・錨)は設定、食事・収支・体の分布は観測
    **_mixed("energy", config=(
        "rate", "avg_mets", "mets", "mets_out_of_area", "hunger_ratio_edges", "hunger_stage_values",
        "meal_windows_min", "share_source", "drink_share", "default_meal_min", "initial_since_meal", "eer_floor_pal",
        "anchors", "anchors_md5"), observed=(
        "counts", "intake_kcal", "census", "census_per_agent", "balance_kcal", "balance_kcal_by_meals",
        "balance_over_eer_by_meals", "agents_with_three_meals", "meals_per_agent", "breakfast_skip", "stage_time_share",
        "stage_ticks_awake_by_hour", "meal_start_in_15min", "meal_start_out_15min", "snack_start_15min",
        "out_of_area_schedule", "weight_kg", "eer_kcal", "home_meal")),
    **_mixed("energy.home_meal", config=("mode",), observed=(
        "rows", "agents_with_rows", "not_at_home", "asleep", "meal_start_home_15min")),
    **_mixed("classical", config=("policy", "prior", "meal_gate", "social", "multipliers_identity", "activity_map"),
             observed=("counts", "calls", "decisions_by_hour")),
    **_mixed("chooser_stats", config=("name", "p_h", "tau", "activity_region"), observed=("counts",)),
    **_mixed("decision_layers", config=("definition", "entrances"), observed=(
        "totals", "share", "by_entrance", "by_hour", "by_hour_layer_entrance", "conversation_origins")),
    # 〔第 1 期 1-2〕看板の注視の活動の乗数は消した=値は null(設定)
    "p_see_activity": _C,
    # 〔第 6 期 6-5・検収 L1〕mr65_arms=記憶の腕の名・埋め込みのモデルの名と版・行の上限(既定と違う腕のランだけ出る=設定)
    **_mixed("memory_summary", config=("n_rows", "d", "w_r", "w_i", "row_bytes_declared", "row_bytes_actual",
                                       "mr65_arms"),
             observed=("recall", "k2_motif_repeats", "k5_failure_avoidance", "counts", "rows_used_per_agent",
                       "full_agents", "agents_with_rows", "rows_by_kind", "failure_rows_by_result", "importance",
                       "n_per_row", "A", "A_by_kind", "score", "gists", "gist_agents", "gist_bytes", "render")),
    **_mixed("memory_summary.recall", config=("tau", "k_conversation", "k_other"), observed=(
        "counts", "filled_call_share", "empty_table_share", "zero_recall_share", "recalled_call_share",
        "recalled_rows_per_call", "candidate_below_tau_share", "used_below_tau_share")),
    # 〔第 1 期 1-6 M0〕記憶の器の計器(腕 --memory-store events のランだけ出る)。中身ごと観測(設定の節の golden は
    # 変えない=腕の名・行の幅も計器の一部として観測に置いた)
    "memory_summary.memory_store": _O,
    **_mixed("store_memory_summary", config=(
        "n_rows", "sigma", "precision_per_event", "decay", "tau", "d", "row_bytes_actual", "row_bytes_declared"),
        observed=("counts", "rows_used_per_agent", "rows_used_total", "full_agents", "agents_with_rows",
                  "rows_by_source", "rows_with_source_bit", "valence_sign", "precision", "n_per_row", "A",
                  "recallable_rows", "recallable_rows_per_agent", "recallable_share", "distinct_pois_known",
                  "top_pois_by_agents")),
    **_mixed("wom", config=("source", "text_fields", "weight_addressee", "dictionary_keys"), observed=(
        "counts", "extracted_share", "with_valence_share", "unmatched_share", "top_pois", "top_unmatched_words",
        "store_rows_with_wom", "store_events_wom")),
    **_mixed("store_choice", config=("reasons", "storefront_reasons", "recall_first", "reference", "intent_max_ticks",
                                     "arms"), observed=(
        "counts", "choices_by_reason", "choices_by_hour", "visits", "visits_by_reason", "first_visit_no_row",
        "first_visit_no_row_share", "first_visit_no_self", "first_visit_no_self_share",
        "first_visit_no_self_by_reason", "storefront_share_of_first_no_self", "storefront_share_of_first_no_row",
        "walk_m_per_tick_mean")),
    **_mixed("relations", config=("k", "tau", "d", "s", "row_bytes_actual", "row_bytes_declared", "copresent",
                                  "acquaintance_wake", "invite_weights"), observed=(
        "init", "counts", "edges_live_per_agent", "edges_live_total", "edges_below_tau", "agents_with_edges",
        "degree_histogram", "degree_regular", "kinds", "signs", "A", "P", "n_per_edge", "dunbar_layers",
        "lifetime_days", "wall_seconds_nondeterministic", "origins")),
    # 10f 検収 N1: 関係の初期化は観測(群の数・候補の対・τ で落ちた辺は seed で動く・壁時計)。定数だけ設定
    **_mixed("relations.init", config=("density", "k", "slot_minutes", "tiebreak", "tenure_weeks", "tenure_hash",
                                       "w17_single_day"), observed=(
        "groups", "candidate_pairs_all", "candidate_pairs", "candidate_pairs_copresent", "capped_out",
        "edges_before_tau", "dropped_by_tau", "init_seconds_nondeterministic", "reason")),
    **_mixed("presence_exit", config=("exit_mode",), observed=(
        "departures", "deferred", "forced_after_defer", "shopping_interrupted", "queue_balked",
        "exit_cell_in_area_by_hour", "platform_cell_in_area_by_hour", "exit_cell_density_stage_max_by_hour",
        "immediate")),
    **_mixed("leave_effects", config=("enabled", "seat_release"), observed=(
        "leave", "released_indoor", "left_queue", "was_conversing", "sessions_closed",
        "released_on_walk")),  # 〔第 2 期 2-4 V3〕在席の印を歩き出しで解く腕(設定)と解いた数(観測)
    **_mixed("near_tiebreak", config=("mode", "order"), observed=("ties_broken", "tie_candidates", "order_ties")),
    **_mixed("group_norms", config=("enabled", "declared"), observed=(
        "cowalk", "instant_group_walk", "conversation_group_size_a1", "context_entropy", "role_words",
        "propagation")),
    # 〔第 2 期 2-4 V5・3-3 の検収 2〕計器の費用 cost の刻みの数 ticks は再開のランで必ず動く(再開の時刻からの数)=観測。
    # 注 note(定数の文)だけ設定。前は cost ごと設定の節(反実仮想の分岐の入力の一致が RESUME_DERIVED で許していた)
    **_mixed("group_norms.cost", config=("note",), observed=("ticks",)),
    **_mixed("waste_sink", config=("band_store_t", "expected_store_t", "band_basis", "band_check",
                                   "ward_total_comparison"), observed=("total_t", "breakdown_t", "band_ok")),
    # ---- 第 1 期 1-9(K17): 金の生ログの輪の容量(体数と係数で決まる=設定)と溢れ・transfer の計器(観測) ----
    **_mixed("economy", config=("raw_capacity", "raw_rows_per_agent_day", "raw_row_bytes", "raw_link_bytes",
                                "raw_overflow_policy"), observed=(
        "raw_overflow", "transfers_total", "transfers_amount", "transfers_uncaused", "transfer_events")),
    # ---- 第 2 期 2-1: 経済の段階 2 の腕(--economy-stage2 on のランだけ欄が立つ)。腕・部品・給料日・expedient の値・
    # 労働時間の出どころ・組み立ての宣言(縮小の比)・登録の流れの表・ATM の表=設定/規則の asof と値・計器・流れの欄の額・
    # 信用の器・財布と預金の分位=観測 ----
    **_mixed("economy.stage2", config=("arm", "parts", "payday_day_of_month", "expedients", "hours_source", "plan",
                                       "faucet_sink_registry", "atms"), observed=(
        "rules", "endow", "wages", "withdraw", "payment", "tax", "external_sales", "faucet_sink_by_cell", "credit",
        "wallet", "deposit", "wallet_mean", "deposit_mean", "wallet_zero", "calls")),  # calls=検収 A1(呼の id の配線)
    # ---- 第 1 期 1-8 J0: 候補の口(腕の名・口の実装・源の一覧・「その他」の既定=設定/判断の数・源の分布・「その他」の割合・
    # 選んだ番号の分布・今の道との食い違い・判断の出来事=観測。腕 legacy のランは観測の子が null) ----
    **_mixed("decision_port", config=("schema", "arm", "port", "sources", "bridge_source", "other_share_default",
                                      "other_share_basis"), observed=(
        "decisions", "late", "fleet_legacy", "presented_by_source", "chosen_by_source", "other", "other_ratio",
        "chosen_number", "n_candidates", "mismatch", "events", "events_unlogged",
        "stage2")),  # 第 2 期 2-1: 経済の段階 2 の候補の計器(お金を下ろす・支払いの注)
    # ---- 第 1 期 1-8b: 発話の口(腕の名・口の実装・届く範囲・道具・出力の欄の指示・未読の窓と上限・mock の決まった文=設定/
    # 会話の番・発話にしなかった数・発話・出来事の行・届いた数・口コミに渡った数ほか=観測。腕 off のランは観測の子が null) ----
    **_mixed("speech_port", config=("schema", "arm", "port", "reach", "via", "field_line", "heard_ttl_steps",
                                    "heard_max_per_addressee", "mock_utterance"), observed=(
        "turns", "silent", "no_session", "to_inviter", "said", "events", "zero_mora", "posted", "delivered",
        "all_imperative", "dropped_budget", "expired", "overflow", "wom_passed", "pending")),
    # ---- 第 2 期 2-2 段 11a: 近接の判定の切替口(腕の名・d・離脱の距離・B5 の半径と出典・気づく曲線と出典・B5 の単位・索引の
    # 格子・位置の出どころ・「暫定」の印=設定/索引と B5 の単位の在室人数の計器=観測。腕 cell のランは観測の子が null) ----
    **_mixed("proximity", config=("schema", "mode", "d_m", "d_arms", "leave_m", "b5_radius_m", "b5_radius_source",
                                  "notice", "unit_source", "index_cell_m", "position_source", "marks"), observed=(
        "index_builds", "indexed_max", "unit_occupancy_max", "units_occupied_max", "unit_occupancy_hist")),
    # ---- 第 3 期 3-3: 反実仮想の申込書(形式・申込書の指紋・種類・水準・A/A か・決定の名・T0・終わり・告知の有無・登録と封印の
    # 指紋・分岐の T0=設定/効かせた・効かせていない改変の数と行・計器・T0 より前の再生の計器・4 つの確認の結果=観測。申込書を
    # 渡さないランは null。子の鍵は engine.experiment.layer の MANIFEST_CONFIG・MANIFEST_OBSERVED と同じ=試験が突き合わせる) ----
    **_mixed("experiment", config=(
        "schema", "form_sha256", "kind", "level", "aa", "decisions", "t0_ns", "t0_step", "end_ns", "notice",
        "registration_sha256", "preregistration_sha256", "seal_sha256", "branch_t0_step", "member", "half", "aa_of",
        # 〔第 3 期 3-3b〕T からの切り替えの口・CP5-1 の点検・CP5-3 の混入の疑いの自己申告・慣らしの規則(末尾に足しただけ)
        "switch", "start0", "known_to_model", "warmup"),
        observed=(
        "applied", "unapplied", "applied_rows", "unapplied_rows", "meter", "replay", "checks")),
    # ---- 第 3 期 3-2: 計算のまとめの窓(形の版・幅・既定の幅・刻みの幅・上限・窓の中の順・世界の番号・事象の種類=設定/
    # 窓の数・窓に事象のあった数・事象の数・処理の呼び数・窓の中で続けた予約・持ち越し・上限に当たった数・窓の最大の事象の数・
    # 境目で届けた数と遅れ・終わりに残った数=観測。進行役を通らない結果は null。子の鍵は engine.batching の config_keys・
    # observed_keys と同じ=試験が突き合わせる) ----
    **_mixed("batching", config=(
        "schema", "width_s", "default_width_s", "step_s", "cap_events", "order", "world_id", "kinds"), observed=(
        "windows", "windows_with_events", "events", "dispatches", "in_window", "carried", "cap_hits",
        "max_events_window", "boundary_events", "boundary_delay_ns_max", "boundary_delay_ns_sum", "pending_at_end")),
    # ---- 第 3 期 3-5: 本人の体の層(形式・持ち主・腕・規則の出典の表・expedient の宣言・器だけの 3 件=設定/体の刻みの回数・
    # 規則に通した体の延べ・予約・引き直し・体感温度の窓・生きている予約・段の境目の数と列の鎖のハッシュ=観測。子の鍵は
    # engine.body.model の CONFIG_KEYS・OBSERVED_KEYS と同じ=試験が突き合わせる) ----
    **_mixed("body", config=("schema", "owner", "arm", "arms", "rules", "expedients", "reserve_expedients", "system1"),
             observed=("steps", "agent_evals", "due", "replans", "reservations", "felt_frames", "felt_evals", "felt_due",
                       "felt_moved", "felt_reservations", "felt_tables", "pending", "boundaries", "boundary_digest")),
    # ---- 第 3 期 3-1: 暦 1a の影(源 w17/1a・W20 の版・週の数=設定/日ごとの記録・影の数・空欄の数=観測。腕 w17 のランは
    # 観測の子が null。子の鍵は engine.calendar_shadow の MANIFEST_CONFIG・MANIFEST_OBSERVED と同じ=試験が突き合わせる) ----
    **_mixed("calendar_shadow", config=("schema", "source", "w20", "weeks"), observed=("days", "shadows", "blanks")),
    # ---- 第 6 期 6-2: カレンダー 1b(腕 1b のランだけ欄がある=既定の manifest には無い。形の版・腕・口の実装・W20 の版・置き場所・
    # 仮採用の値・実感の形・つなぎの台帳の行=設定/日ごとの計器・合計・エンジンがしないこと 3 つの検査=観測。子の鍵は
    # engine.calendar_self の MANIFEST_CONFIG・MANIFEST_OBSERVED と同じ=試験が突き合わせる) ----
    **_mixed("calendar_1b", config=("schema", "mode", "port", "w20", "placements", "look_interval_min", "margins_min",
                                    "recent_k", "round_min", "approx_round_min", "felt", "bridges"),
             observed=("days", "totals", "checks")),
    # ---- 第 6 期 6-3: 時計の段 T2〜T4 の腕の節(腕のランだけ出る=既定のランの manifest には無い)。子の鍵は
    # engine.speech_clock・engine.step_scope・engine.regional_clock の CONFIG_KEYS・OBSERVED_KEYS と同じ=試験が突き合わせる ----
    # T2 会話の時計(形の版・腕・錨の出典の表・導いた幅・間・考える時間を数える側・モーラの規則・道具・上限・事象の種類と順位・
    # 計器の区切り=設定/会話の番・発言・持ち越し・上限・束・モーラと長さと話す速さ・区域またぎの聞こえ・会話の長さ・区切りごとの
    # 数=観測)
    **_mixed("talk_clock", config=(
        "schema", "arm", "anchors", "sigma_between", "sigma_within", "familiar_delta", "gap_ns", "think_time",
        "mora_rule", "modalities", "cap_per_window", "kind", "rank", "bins"), observed=(
        "turns", "utterances", "silent", "no_session", "lang_other", "chat_blank", "familiar", "unfamiliar",
        "familiar_unknown", "persons", "carried", "lag_ns_sum", "lag_ns_max", "ahead", "cap_hits", "dispatches",
        "batch_max", "batch_sum", "mora_sum", "speech_ns_sum", "utterance_ns_max", "gap_ns_sum", "heard", "cross_heard",
        "hear_delay_ns_sum", "hear_delay_ns_max", "conversations", "conv_silent", "conv_open_at_end", "conv_tm3_ns_sum",
        "conv_table_s_sum", "conv_span_s_sum", "pending_at_end", "mean_utterance_s", "mean_mora", "mean_rate_mora_per_s",
        "person_rate_mean", "person_rate_min", "person_rate_max", "mean_conv_tm3_s", "mean_conv_table_s",
        "mean_conv_span_s", "hist")),
    # T3 何かあった体だけ(形の版・腕・絞る処理と絞らない処理・印の列・体の反映の腕=設定/検出の回数・全員を見た回数・印の
    # 延べと最大・跨いだ体・全員を見る版の延べ・壁時計(非決定)・印の平均と割合=観測)
    **_mixed("step_scope", config=("schema", "arm", "narrowed", "not_narrowed", "mark_columns", "body_schedule"),
             observed=("steps", "full_steps", "marked", "marked_max", "crossed", "full_equiv",
                       "detect_seconds_nondeterministic", "marked_mean", "marked_share")),
    # T4 場所ごとの時計(形の版・腕・時計の種類・区域の幅と作り方と数・舞台の外の区域・窓の幅・メッセージと待ち合わせと混合の
    # 宣言=設定/窓・区域の窓・事象・区域をまたぐ事象と遅れ・境目の移動・聞く人の区域またぎ・遅刻・メッセージの遅れ・待ち合わせ
    # (欄だけ)=観測)
    **_mixed("clock", config=("schema", "arm", "clock_kind", "region_size_m", "regions_from", "n_regions",
                              "outside_region", "width_s", "messages", "meeting_note", "mixed"), observed=(
        "windows", "region_windows", "events", "dispatches", "cross_events", "cross_delay_ns_sum", "cross_delay_ns_max",
        "boundaries", "cross_moves", "cross_move_delay_ns_max", "hear", "hear_cross", "hear_delay_ns_sum",
        "hear_delay_ns_max", "planned_arrivals", "late_arrivals", "late_minutes_sum", "late_minutes_max",
        "message_delay_ns_max", "pending_at_end", "meeting")),
    # ---- 〔第 6 期 6-4 C1〕連絡の道具(腕 c1 のランだけ欄が立つ)。形の版・腕と下の腕・宛先の出どころ・窓の境目の種類・気づきの門の
    # 段・道具の状態と目と心の向きの値・口・スタンプ・定型の文・長さの上限・チャットの沈黙の閾値・仮の値の宣言=設定/計器・判断の
    # 数・読むまでの時間・通話の長さ・チャット・通話・届いた箱・道具・向き・周りの出来事・記憶に残ったか・体の無い人=観測。
    # 子の鍵は engine.contact.layer の CONFIG_KEYS・OBSERVED_KEYS と同じ=試験が突き合わせる ----
    **_mixed("contact_c1", config=(
        "schema", "arm", "unnoticed_arm", "send_arm", "contacts_source", "queue_kinds", "notice_min_level", "device",
        "attention", "port", "stamps", "mock_text", "message_max_chars", "chat_silence_steps", "provisional"),
        observed=("meter", "decisions", "read_delay_minutes", "call_steps", "screen_minutes", "chats", "calls", "mail",
                  "devices", "attention_now", "salient", "remembered", "bodiless_dropped", "rendered")),
}


def section_of(path: str, paths: Mapping[str, str] | None = None) -> str | None:
    """道筋(``a.b.c``)の節。最も長く一致する表の道筋の節。どれにも当たらなければ ``None``。"""
    table = PATHS if paths is None else paths
    best: str | None = None
    best_len = -1
    for p, sec in table.items():
        if (path == p or path.startswith(p + ".")) and len(p) > best_len:
            best, best_len = sec, len(p)
    return best


def sections_table() -> dict[str, Any]:
    """manifest に置く表(``manifest_sections``)。"""
    return {"schema": SECTIONS_SCHEMA, "rule": "longest-prefix", "paths": dict(sorted(PATHS.items()))}


def split(manifest: Mapping[str, Any], paths: Mapping[str, str] | None = None) -> dict[str, dict[str, Any]]:
    """manifest の一番上の欄を節ごとに分けた写し(入れ子の中は分けない=読み手の便利のため)。表に無い欄は ``unlisted``。"""
    out: dict[str, dict[str, Any]] = {s: {} for s in (*SECTION_VALUES, "unlisted")}
    for k, v in manifest.items():
        out[section_of(k, paths) or "unlisted"][k] = v
    return out


def leaf_paths(v: Any, prefix: str = "") -> list[str]:
    """入れ子の辞書の葉の道筋(辞書でない値・空の辞書が葉。list は 1 つの葉)。"""
    if isinstance(v, Mapping) and v:
        out: list[str] = []
        for k, x in v.items():
            out.extend(leaf_paths(x, f"{prefix}.{k}" if prefix else str(k)))
        return out
    return [prefix] if prefix else []


def unlisted_in_mixed(manifest: Mapping[str, Any], paths: Mapping[str, str] | None = None) -> list[str]:
    """混ざった辞書の下の葉のうち、表の道筋が混ざった辞書そのものにしか当たらないもの(=節の決まっていない鍵)。

    混ざった辞書が空(腕が立っていない)なら葉は無い。10f 検収 N3 のテストが空であることを確かめる。
    """
    table = PATHS if paths is None else paths
    mixed = set(MIXED)
    out: list[str] = []
    for root in sorted({m.split(".")[0] for m in mixed}):
        if root not in manifest:
            continue
        for leaf in leaf_paths(manifest[root], root):
            best = max((p for p in table if leaf == p or leaf.startswith(p + ".")), key=len, default=None)
            if best == leaf and leaf in mixed:  # 空の混ざった辞書(腕が立っていない)=葉が無い
                continue
            if best is None or best in mixed:
                out.append(leaf)
    return sorted(out)


def config_paths(paths: Mapping[str, str] | None = None) -> list[str]:
    """表の設定の節の道筋(昇順)。golden で固定する(10f 検収 N3 の 3)。"""
    table = PATHS if paths is None else paths
    return sorted(p for p, s in table.items() if s == CONFIG)
