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
    "calendar": _C, "response_delay": _C, "rng_scheme": _C, "template_sha256": _C, "catalog_sha16": _C,
    "frozen_sources": _C, "process_ids": _C, "ablations": _C, "fleet": _C,
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
    **_mixed("p_see_activity", config=("table", "identity", "signage_p_see", "applies_to"),
             observed=("by_kind", "effective_p_see")),
    **_mixed("memory_summary", config=("n_rows", "d", "w_r", "w_i", "row_bytes_declared", "row_bytes_actual"),
             observed=("recall", "k2_motif_repeats", "k5_failure_avoidance", "counts", "rows_used_per_agent",
                       "full_agents", "agents_with_rows", "rows_by_kind", "failure_rows_by_result", "importance",
                       "n_per_row", "A", "A_by_kind", "score", "gists", "gist_agents", "gist_bytes", "render")),
    **_mixed("memory_summary.recall", config=("tau", "k_conversation", "k_other"), observed=(
        "counts", "filled_call_share", "empty_table_share", "zero_recall_share", "recalled_call_share",
        "recalled_rows_per_call", "candidate_below_tau_share", "used_below_tau_share")),
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
    **_mixed("leave_effects", config=("enabled",), observed=(
        "leave", "released_indoor", "left_queue", "was_conversing", "sessions_closed")),
    **_mixed("near_tiebreak", config=("mode", "order"), observed=("ties_broken", "tie_candidates", "order_ties")),
    **_mixed("group_norms", config=("enabled", "declared", "cost"), observed=(
        "cowalk", "instant_group_walk", "conversation_group_size_a1", "context_entropy", "role_words",
        "propagation")),
    **_mixed("waste_sink", config=("band_store_t", "expected_store_t", "band_basis", "band_check",
                                   "ward_total_comparison"), observed=("total_t", "breakdown_t", "band_ok")),
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
