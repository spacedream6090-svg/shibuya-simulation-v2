# -*- coding: utf-8 -*-
"""bytecheck.configs — byte-check の構成の表・構成の組・比べる 25 欄・記録に残す切替口の環境変数。

出典(写した): 構成の表は ``docs/bench/analysis/wave2-2026-09-30/wave2_bytecheck.py`` の ``configs()`` と
``docs/bench/analysis/w6-regen-2026-09-28/w6_regen_measure.py`` の ``ARMS``(現行 8・旧 6・golden の帰無腕 1)。
比べる欄と切替口の一覧は ``docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py`` の ``COMPARE_KEYS``・
``SWITCH_ENV``。構成の組 ``parent4``・``arms`` は ``docs/bench/analysis/v3-2026-11/v30a/README.md`` §4・§7
(親の 4 構成と腕 on の追加の確かめ)。試験 ``tests/tools/test_bytecheck.py`` が元の表と同じであることを確かめる。
"""

from __future__ import annotations

from typing import Any, Final

#: 古典の方策と選び手(``wave2_bytecheck.CLS``)。
_CLS: Final[dict[str, str]] = {"policy": "classical", "chooser": "classical"}

#: W6 の現行の腕(``w6_regen_measure.CURRENT_ARMS``)。
_W6_CURRENT: Final[dict[str, dict[str, Any]]] = {
    "v3_default": {"vocab_version": "v3", "activity": True},
    "v3_activity_off": {"vocab_version": "v3", "activity": False},
    "v1_default": {"vocab_version": "v1"},
    "v1_derive_v2_1": {"vocab_version": "v1", "derive_rule": "v2.1"},
    "v2": {"vocab_version": "v2"},
    "v1_edge": {"vocab_version": "v1", "geometry": "edge"},
    "v2_edge": {"vocab_version": "v2", "geometry": "edge"},
    "v1_edge_plateau": {"vocab_version": "v1", "geometry": "edge", "area_source": "plateau"},
}


def _w6_arms() -> dict[str, dict[str, Any]]:
    """W6 の 15 腕(現行 8・旧 6=``report_precondition=False``・golden の帰無腕 1)。"""
    old = {f"old_{k}": {**v, "report_precondition": False} for k, v in _W6_CURRENT.items() if not k.startswith("v3_")}
    golden = {"golden_null_arm": {"plan_executor": False, "report_precondition": False}}
    return {**_W6_CURRENT, **old, **golden}


def configs() -> dict[str, dict[str, Any]]:
    """19 構成(名 → ``shibuya.cli.run`` に渡す引数)。並びは ``wave2_bytecheck.configs()`` と同じ。"""
    out = {f"w6_{k}": dict(v) for k, v in _w6_arms().items()}
    out.update({
        "v3_mem_store": {"vocab_version": "v3", "memory": "on", "store_memory": "on"},
        "v3_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on"},
        "v3_classical": {"vocab_version": "v3", **_CLS},
        "v3_classical_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on", **_CLS},
    })
    return out


#: 腕 on の追加の確かめで両側に置く環境変数(v30a の README §4・記録 ``v30a_arms.json`` の ``env``)。
ARMS_ENV: Final[dict[str, str]] = {
    "SHIBUYA_CALENDAR": "1b",
    "SHIBUYA_DECISION_PORT": "port",
    "SHIBUYA_CONTACT": "c1",
    "SHIBUYA_CONTACT_HABIT": "on",
    "SHIBUYA_CALENDAR_2": "arm",
    "SHIBUYA_CALENDAR_3": "arm",
    "SHIBUYA_DUTIES": "arm",
}

#: 構成の組(名 → 構成の並びと両側に置く環境変数)。
SETS: Final[dict[str, dict[str, Any]]] = {
    "all19": {"configs": tuple(configs()), "env": {},
              "about": "19 構成(W6 の 15 腕+店の記憶・関係・古典・古典+記憶+関係)"},
    "parent4": {"configs": ("w6_v3_default", "v3_mem_store", "v3_classical", "v3_classical_mem_rel"), "env": {},
                "about": "親の 4 構成(v30a の README §7)"},
    "arms": {"configs": ("w6_v3_default", "v3_classical"), "env": dict(ARMS_ENV),
             "about": "腕 on の追加の確かめ(判断の口・連絡と習慣・カレンダー 1b/2/3・店の仕事の 7 変数を両側に置く=v30a の README §4)"},
}


def set_configs(name: str) -> tuple[str, ...]:
    """構成の組の構成の並び(無い組の名は ``KeyError``)。"""
    return tuple(SETS[name]["configs"])


def set_env(name: str) -> dict[str, str]:
    """構成の組が両側に置く環境変数(写し)。"""
    return dict(SETS[name]["env"])


#: 比べる 25 欄(壁時計・時間・テープのバイト数は比べない)。``byte_check_10e.COMPARE_KEYS`` と同じ並び。
COMPARE_KEYS: Final[tuple[str, ...]] = (
    "final", "calls", "blocks_rows", "blocks_sha", "calls_rows", "calls_column_names", "calls_columns_sha",
    "action_usage_total", "action_usage_sha", "calls_by_condition", "salient_events", "collapse",
    "noticed", "dispatches", "arrived", "mean_delay_min", "meals", "behavior_last", "full_last",
    "end_of_day", "start_sim_datetime", "replay_date", "calendar_weekday", "rng_scheme",
    "frozen_sources",
)

#: side の JSON に値を残す切替口の環境変数(値に道筋・ホスト・鍵を持たないもの)。``byte_check_10e.SWITCH_ENV`` から
#: ``SHIBUYA_CALENDAR_W20``(値が道筋)を :data:`HIDDEN_ENV` へ移し、src が読むのに一覧に無かった 4 本
#: (``SHIBUYA_ABSENT_PROCESSES``・``SHIBUYA_BODY_BOUNDARY_GAUGE``・``SHIBUYA_DEFECT_FIXES_1103``・``SHIBUYA_RATE_RULES``)を足した。
SWITCH_ENV: Final[tuple[str, ...]] = (
    "SHIBUYA_PROXIMITY_D", "SHIBUYA_ECONOMY_STAGE2",
    "SHIBUYA_ECONOMY_STAGE2_PARTS", "SHIBUYA_MEMORY_STORE", "SHIBUYA_EVENTS", "SHIBUYA_TOOL_EVENTS",
    "SHIBUYA_WRITE_GUARD", "SHIBUYA_SYSTEMS_CHECK", "SHIBUYA_WARD_AREA_M2",
    "SHIBUYA_BATCH_WIDTH_S", "SHIBUYA_CALENDAR_SHADOW", "SHIBUYA_BODY_SCHEDULE",
    "SHIBUYA_MEMORY_MODEL", "SHIBUYA_MEMORY_CUE", "SHIBUYA_MEMORY_PEOPLE", "SHIBUYA_MEMORY_GRAIN", "SHIBUYA_MEMORY_EMBED_MODEL",
    "SHIBUYA_CALENDAR", "SHIBUYA_DECISION_PORT", "SHIBUYA_SPEECH_PORT",
    "SHIBUYA_TALK_CLOCK", "SHIBUYA_STEP_SCOPE", "SHIBUYA_CLOCK",
    "SHIBUYA_CONTACT", "SHIBUYA_CONTACT_SEND", "SHIBUYA_CONTACT_UNNOTICED", "SHIBUYA_CONTACT_HABIT",
    "SHIBUYA_CALENDAR_2", "SHIBUYA_CALENDAR_3", "SHIBUYA_CALENDAR_3_TRIAL",
    "SHIBUYA_MEAL_DEFAULT", "SHIBUYA_WAGE", "SHIBUYA_DUTIES",
    "SHIBUYA_SPACE", "SHIBUYA_SLOPE", "SHIBUYA_TURN_WEIGHT", "SHIBUYA_NAV1_DENSITY",
    "SHIBUYA_ABSENT_PROCESSES", "SHIBUYA_BODY_BOUNDARY_GAUGE", "SHIBUYA_DEFECT_FIXES_1103", "SHIBUYA_RATE_RULES",
)

#: 〔第346 旧道の切替口の削除〕消した切替口の環境変数(src は名を持つ=与えると読み込みで止まる。:data:`SWITCH_ENV` から外した
#: =値を残す欄が無い。置かれていれば名だけを ``env_hidden`` に残す)。記録 ``docs/bench/analysis/delete-346/README.md``。
REMOVED_ENV: Final[tuple[str, ...]] = (
    "SHIBUYA_RULES_42B", "SHIBUYA_RULES_42", "SHIBUYA_SEAT_RELEASE", "SHIBUYA_PROXIMITY",
)

#: 値を記録しない環境変数(道筋・鍵)。置かれていれば名だけを side の JSON の ``env_hidden`` に残す。
HIDDEN_ENV: Final[tuple[str, ...]] = (
    "SHIBUYA_CALENDAR_W20", "SHIBUYA_BUDGET_MD", "SHIBUYA_PATTERN_LEDGER_MD", "SHIBUYA_PERCEPTION_MD",
    "SHIBUYA_FLEET_API_KEY",
)


def switch_env(env: dict[str, str]) -> dict[str, str]:
    """``env`` のうち :data:`SWITCH_ENV` の値(置かれていたものだけ・一覧の並び)。"""
    return {k: env[k] for k in SWITCH_ENV if k in env}


def hidden_env_names(env: dict[str, str]) -> list[str]:
    """``env`` に置かれた ``SHIBUYA_`` の変数のうち、値を記録しないもの(:data:`SWITCH_ENV` の外)の名。"""
    return sorted(k for k in env if k.startswith("SHIBUYA_") and k not in SWITCH_ENV)
