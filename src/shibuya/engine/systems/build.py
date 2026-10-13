"""engine.systems.build — 組み立て(R1・S0〜S8 と再開の復元)(第 1 期 1-0・段 F)。

``build(_call_args)`` は HEAD ``ee3abc7`` の ``run_day`` の頭(``_call_args = dict(locals())`` の次の文)から刻みのループの
前までを、そのままの文で回して状態の箱(``Box``)を返す。前置きは run_day の引数 113 個を ``_call_args`` から結ぶ行だけ
(``_call_args`` の写し方・設定の指紋 ``RS.fingerprint(_call_args)`` は HEAD と同じ=草案 §3-3 の 3)。
HEAD の入れ子の関数のうち状態と日の口(``_hash_owners`` ほか 14)は ``engine.systems.state_io`` の箱を受け取る関数にした。
描画と方策へ差し込む関数(``_classical_acq``・``_classical_partner``・``_session_partners``・``_b3_words``・無名関数 3 つ)は
組み立ての中の入れ子の def のまま(捕まえる物の同一性を保つ=草案 §3-3 の 6)。

試験の差し替えの的: 層の組み立ての名前(``FleetBridge``・``PerceptionRendererAdapter``・``WorldProcessRunner``・
``Arbiter``・``ConversationManager``)は**このモジュール**の名前(HEAD は ``engine.run``)。``engine.run`` で定義された
補助(``_resolve_population`` など)は呼ぶ時に ``engine.run`` から引く。

逐次ループ宣言: HEAD の組み立てのまま(各文の注を見る)。
"""

from __future__ import annotations

import copy
import dataclasses
import time
from datetime import datetime
from datetime import timedelta
from pathlib import Path
from typing import Any

import numpy as np

from shibuya.agents.schedule import synthesize
from shibuya.agents.state import AgentState
from shibuya.agents.state import FOCUS_NONE
from shibuya.agents.state import N_WAKE_CONDITIONS_ALL
from shibuya.agents.state import WakeCondition
from shibuya.agents.weekly import apply_to_mock_schedule
from shibuya.agents.weekly import load_weekly
from shibuya.core.rng import RNG_SCHEME
from shibuya.engine import commit as C
from shibuya.engine import resolve as R
from shibuya.engine import resume as RS
from shibuya.engine.activity import ActivityLayer
from shibuya.engine.arbiter import Arbiter
from shibuya.engine.arbiter import call_budget_per_tick
from shibuya.engine.calendar import DEFAULT_WORLD_START
from shibuya.engine.calendar import SimCalendar
from shibuya.engine.calendar import WEATHER_SCHEME
from shibuya.engine.calendar import WEEKDAY_MODE
from shibuya.engine.calendar import load_holidays
from shibuya.engine.calendar import parse_school_holidays
from shibuya.engine.calendar import parse_start
from shibuya.engine.change_detect import ChangeDetector
from shibuya.engine.chooser import check_chooser
from shibuya.engine.chooser import make_chooser
from shibuya.engine.classical import ActivityPrior
from shibuya.engine.classical import ClassicalPolicy
from shibuya.engine.classical import check_activity_region
from shibuya.engine.classical import check_classical_social
from shibuya.engine.classical import check_meal_gate
from shibuya.engine.classical import check_policy
from shibuya.engine.classical import load_activity_prior
from shibuya.engine.conversation import ConversationManager
from shibuya.engine.energy import EnergyLayer
from shibuya.engine.energy import EnergyModel
from shibuya.engine.energy import HomeMeals
from shibuya.engine.energy import OutOfAreaMeals
from shibuya.engine.energy import check_energy_rate
from shibuya.engine.energy import check_home_meal
from shibuya.engine.energy import check_hunger_model
from shibuya.engine.energy import check_meal_sleep_defer
from shibuya.engine.energy import load_anchors
from shibuya.engine.familiarity import FAMILIARITY_MODES
from shibuya.engine.familiarity import FamiliarityLayer
from shibuya.engine.geometry import EdgeGeometry
from shibuya.engine.geometry import check_geometry
from shibuya.engine.intent import IntentLayer
from shibuya.engine.llm_bridge import LLMBridge
from shibuya.engine.llm_bridge import PerceptionRendererAdapter
from shibuya.engine.llm_bridge import StubRenderer
from shibuya.engine.memory import MEMORY_MODES
from shibuya.engine.memory import MemoryLayer
from shibuya.engine.memory import STORE_RECALL_SCOPES
from shibuya.engine.poi_target import TargetResolver
from shibuya.engine.poi_target import check_poi_target
from shibuya.engine.presence import DERIVE_RULES as PRESENCE_DERIVE_RULES
from shibuya.engine.presence import EXIT_MODES as PRESENCE_EXIT_MODES
from shibuya.engine.presence import PlanExecutor
from shibuya.engine.processes.crowd import SEAT_AREA_M2
from shibuya.engine.processes.runner import WorldProcessRunner
from shibuya.engine.processes.salient import check_d50_scale as _check_d50_scale
from shibuya.engine.relations import REL_INIT_DENSITIES
from shibuya.engine.relations import REL_MODES
from shibuya.engine.relations import REL_ORIGINS
from shibuya.engine.relations import REL_TAU_BY_TENURE_HASH
from shibuya.engine.relations import check_rel_tenure_hash
from shibuya.engine.relations import initial_edges as _rel_initial_edges
from shibuya.engine.store_choice import StoreChoice
from shibuya.engine.store_choice import walk_m_per_tick as _walk_m_per_tick
from shibuya.engine.store_memory import STORE_MEMORY_MODES
from shibuya.engine.store_memory import check_store_decay
from shibuya.engine.store_memory import check_store_sigma
from shibuya.engine.systems import boxes as _BX
from shibuya.engine.systems import state_io as _SIO
from shibuya.engine.tape import TapeRow
from shibuya.engine.tape import TapeWriter
from shibuya.engine.tape import read_run_meta
from shibuya.engine.wom import WomExtractor
from shibuya.engine.wom import check_wom_source
from shibuya.llm.fleet import FleetBridge
from shibuya.perception.channels import BudgetMode
from shibuya.perception.renderer import PerceptionAssets
from shibuya.perception.renderer import Renderer as PerceptionRenderer
from shibuya.perception.renderer import check_hunger_words
from shibuya.perception.renderer import check_near_order
from shibuya.perception.renderer import check_near_tiebreak
from shibuya.perception.renderer import check_p_see_activity
from shibuya.perception.renderer import check_signage_p_see
from shibuya.perception.templates import check_intent_mode
from shibuya.perception.templates import check_role_words
from shibuya.perception.templates import check_vocab_version
from shibuya.world.assets import DEFAULT_AREA_SOURCE
from shibuya.world.assets import check_area_source
from shibuya.world.assets import load_process_assets_or_synthetic
from shibuya.world.assets import load_walkable_area_m2
from shibuya.world.state import World
from shibuya.world.state import check_eatery_mode
from shibuya.core.time_consts import HOURS_PER_DAY, SECONDS_PER_MINUTE


__all__ = ["build"]


def build(_call_args: dict[str, Any]) -> Any:
    """組み立て(R1): 腕の検査・世界と SoA と層の組み立て・状態の箱・再開の復元。返り値=``Box``。"""
    from shibuya.engine import run as _RUN

    RNG_LAYOUT = _RUN.RNG_LAYOUT
    RunResult = _RUN.RunResult
    _ENTRANCES = _RUN._ENTRANCES
    _default_mock = _RUN._default_mock
    _named_closed_lookup = _RUN._named_closed_lookup
    _replay_tape_dir = _RUN._replay_tape_dir
    _resolve_population = _RUN._resolve_population
    _resolve_response_delay = _RUN._resolve_response_delay
    _same_seed = _RUN._same_seed
    _schedule_with_population = _RUN._schedule_with_population
    check_replay_tape = _RUN.check_replay_tape
    classical_acq_addressable = _RUN.classical_acq_addressable
    resolve_environment_seed = _RUN.resolve_environment_seed
    resolve_population_seed = _RUN.resolve_population_seed
    run_salt_for = _RUN.run_salt_for

    # ---- run_day の引数(``_call_args`` は run_day の頭で ``dict(locals())`` した写し=設定の指紋の材料) ----
    n_agents = _call_args['n_agents']
    seed = _call_args['seed']
    world = _call_args['world']
    population_seed = _call_args['population_seed']
    environment_seed = _call_args['environment_seed']
    tick_seconds = _call_args['tick_seconds']
    ticks = _call_args['ticks']
    llm = _call_args['llm']
    fleet = _call_args['fleet']
    fleet_wait_s = _call_args['fleet_wait_s']
    fleet_debug_dir = _call_args['fleet_debug_dir']
    checkpoint_every = _call_args['checkpoint_every']
    day_index = _call_args['day_index']
    budget = _call_args['budget']
    l4_scale = _call_args['l4_scale']
    n_cells = _call_args['n_cells']
    mode = _call_args['mode']
    tape_path = _call_args['tape_path']
    replay = _call_args['replay']
    renderer = _call_args['renderer']
    world_dir = _call_args['world_dir']
    conversations = _call_args['conversations']
    lane = _call_args['lane']
    ledger = _call_args['ledger']
    processes = _call_args['processes']
    processes_enabled = _call_args['processes_enabled']
    processes_disabled = _call_args['processes_disabled']
    p_notice_ablation = _call_args['p_notice_ablation']
    p_notice_d50_scale = _call_args['p_notice_d50_scale']
    refractory_scale = _call_args['refractory_scale']
    signage = _call_args['signage']
    signage_p_see = _call_args['signage_p_see']
    intent_mode = _call_args['intent_mode']
    vocab_version = _call_args['vocab_version']
    role_words = _call_args['role_words']
    near_tiebreak = _call_args['near_tiebreak']
    near_order = _call_args['near_order']
    group_norms = _call_args['group_norms']
    budget_mode = _call_args['budget_mode']
    salient_rate_per_10k = _call_args['salient_rate_per_10k']
    report_precondition = _call_args['report_precondition']
    queue_service = _call_args['queue_service']
    leave_effect = _call_args['leave_effect']
    population = _call_args['population']
    occupancy_every = _call_args['occupancy_every']
    occupancy_path = _call_args['occupancy_path']
    sleep_suppression = _call_args['sleep_suppression']
    plan_sleep = _call_args['plan_sleep']
    plan_executor = _call_args['plan_executor']
    exit_mode = _call_args['exit_mode']
    attendance_rate = _call_args['attendance_rate']
    outside_suppression = _call_args['outside_suppression']
    derive_rule = _call_args['derive_rule']
    geometry = _call_args['geometry']
    area_source = _call_args['area_source']
    seat_area_eatery_m2 = _call_args['seat_area_eatery_m2']
    seat_area_retail_m2 = _call_args['seat_area_retail_m2']
    census_out = _call_args['census_out']
    activity = _call_args['activity']
    eatery = _call_args['eatery']
    chooser = _call_args['chooser']
    poi_target = _call_args['poi_target']
    move_search_radius = _call_args['move_search_radius']
    mock_move_target_p = _call_args['mock_move_target_p']
    intent_max_ticks = _call_args['intent_max_ticks']
    mock_out_of_cell_target_p = _call_args['mock_out_of_cell_target_p']
    familiarity = _call_args['familiarity']
    familiarity_k = _call_args['familiarity_k']
    hunger_model = _call_args['hunger_model']
    energy_rate = _call_args['energy_rate']
    meal_sleep_defer = _call_args['meal_sleep_defer']
    home_meal = _call_args['home_meal']
    hunger_words = _call_args['hunger_words']
    policy = _call_args['policy']
    activity_region = _call_args['activity_region']
    classical_social = _call_args['classical_social']
    meal_gate = _call_args['meal_gate']
    classical_habit_p = _call_args['classical_habit_p']
    classical_tau = _call_args['classical_tau']
    p_see_activity = _call_args['p_see_activity']
    memory = _call_args['memory']
    memory_n = _call_args['memory_n']
    memory_tau = _call_args['memory_tau']
    store_memory = _call_args['store_memory']
    store_memory_n = _call_args['store_memory_n']
    store_sigma = _call_args['store_sigma']
    store_decay = _call_args['store_decay']
    store_wom = _call_args['store_wom']
    store_signage = _call_args['store_signage']
    store_recall_scope = _call_args['store_recall_scope']
    wom_source = _call_args['wom_source']
    relations = _call_args['relations']
    rel_k = _call_args['rel_k']
    rel_tau = _call_args['rel_tau']
    rel_d = _call_args['rel_d']
    rel_init_density = _call_args['rel_init_density']
    conv_max_participants = _call_args['conv_max_participants']
    rel_tenure_weeks = _call_args['rel_tenure_weeks']
    rel_tenure_hash = _call_args['rel_tenure_hash']
    rel_invite = _call_args['rel_invite']
    rel_acq_wake = _call_args['rel_acq_wake']
    rel_copresent = _call_args['rel_copresent']
    sim_days = _call_args['sim_days']
    start_sim_datetime = _call_args['start_sim_datetime']
    holiday_csv = _call_args['holiday_csv']
    school_holidays = _call_args['school_holidays']
    response_delay = _call_args['response_delay']
    state_out = _call_args['state_out']
    stop_at_tick = _call_args['stop_at_tick']
    resume_from = _call_args['resume_from']
    run_id = _call_args['run_id']
    checkpoint_detail = _call_args['checkpoint_detail']
    weather_perturb = _call_args['weather_perturb']

    # 10f(K21 (a)): 母集団の seed(省略時は seed と同じ)。指紋には seed と違うときだけ載せる(省略と、seed と同じ値の
    # 明示は同じラン=指紋も今と同じ。状態のファイルの見出しは既定のランでは 1 欄も増えない)
    pop_seed = resolve_population_seed(seed, population_seed)
    env_seed = resolve_environment_seed(seed, environment_seed)
    _call_args.pop("population_seed", None)
    _call_args.pop("environment_seed", None)
    if not _same_seed(pop_seed, seed):
        _call_args["population_seed"] = pop_seed
    if not _same_seed(env_seed, seed):
        _call_args["environment_seed"] = env_seed

    weather_perturb = bool(weather_perturb)
    if not weather_perturb:
        _call_args.pop("weather_perturb", None)

    t_start = time.perf_counter()
    budget_mode_enum = BudgetMode.parse(budget_mode)
    # ---- 第 1 期 1-4(検収 L10): つなぎの台帳と規則の表をランの始めに 1 回読む(壊れていればここで落ちる=1 日回した
    # 後の日の締めで落ちない。無い写しは警告して null。読むだけ=状態にも指紋にも入らない) ----
    from shibuya.engine.bridging import ledger as _BR
    from shibuya.engine.rules import table as _RT

    _BR.bridges_count()
    _RT.rules_version()
    # ---- 10a(A1・A1-1・A1-2・A1-3・A9): 暦の口・通しの時刻 T・応答の遅れ(世界を触る前に検査) ----
    check_replay_tape(mode, replay)  # 〔第330・RET〕10e より前・活性化より前の録画は止める
    response_delay = _resolve_response_delay(response_delay, mode, replay)

    if mode == "replay" and replay is not None:  # 10f: 録画した環境が違えば警告を 1 行(挙動は変えない)
        _rtd = _replay_tape_dir(replay)
        RS.warn_if_other_environment(read_run_meta(_rtd).get("environment"), f"再生するテープ {_rtd.name}")
    sim_days = int(sim_days)
    if sim_days < 1:
        raise ValueError(f"sim_days は 1 以上(いま {sim_days})")
    start_given = parse_start(start_sim_datetime)
    # 10e(E3): 暦の 0 日目。渡されたらその日・渡さなければ既定の開始日 2026-07-13 + day_index 日
    calendar = SimCalendar(
        start_given if start_given is not None else DEFAULT_WORLD_START + timedelta(days=int(day_index)),
        tick_seconds=int(tick_seconds),
        day_index=int(day_index),
        holidays=load_holidays(holiday_csv),
        school_holidays=parse_school_holidays(school_holidays),
    )
    tpd = calendar.ticks_per_day
    #: 10d: 状態の口(書き出し・止める・再開)を使うラン。
    _state_mode = state_out is not None or stop_at_tick is not None or resume_from is not None
    if sim_days > 1 and int(ticks) != tpd:
        raise ValueError(f"sim_days > 1 では ticks は 1 日の tick 数 {tpd}(いま {ticks})")
    if sim_days == 1 and int(ticks) > tpd:
        raise ValueError(f"ticks は 1 日の tick 数 {tpd} 以下(複数日は sim_days で回す・いま {ticks})")
    if (sim_days > 1 or _state_mode) and (mode == "replay" or replay is not None):
        raise ValueError("複数日のランと状態の口(10d)は再生(replay)と一緒に使えない(10d の範囲の外)")
    total_ticks = int(ticks) if sim_days == 1 else sim_days * tpd
    # ---- 10d: 再開の読み込み(世界を触る前に見出しを検査する)・止める時刻・ラン ID ----
    _fp = RS.fingerprint(_call_args)
    _bundle: "RS.StateBundle | None" = None
    t_begin = 0
    parent_run: dict[str, Any] | None = None
    _read_seconds = 0.0
    if resume_from is not None:
        _t_read = time.perf_counter()
        _bundle = RS.read_state(resume_from)
        _read_seconds = time.perf_counter() - _t_read
        _h = _bundle.header
        # 10f: 親を書いた環境が違えば警告を 1 行(挙動は変えない)
        RS.warn_if_other_environment(_h.get("platform"), f"状態のファイル {Path(resume_from).name}")
        if bool(_h.get("finished", False)):
            raise ValueError(
                f"finished: true のランへは再開しない(親 {_h.get('run_id')}・T={_h.get('progress', {}).get('next_T')})"
            )
        _diff = RS.fingerprint_diff(_h.get("fingerprint", {}), _fp)
        if _diff:
            raise ValueError(f"再開の設定が親と違う(欄 {_diff[:8]})")
        t_begin = int(_h["progress"]["next_T"])
        if not (0 < t_begin < total_ticks):
            raise ValueError(f"再開の時刻 T={t_begin} がこのランの範囲 0〜{total_ticks} の内側に無い(sim_days を見る)")
        parent_run = {
            "run_id": str(_h.get("run_id", "")),
            "resume_T": int(t_begin),
            "state_file": Path(resume_from).name,
            "state_full_hash": str(_h.get("hashes", {}).get("full_hash", "")),
        }
    t_end = total_ticks
    if stop_at_tick is not None:
        if state_out is None:
            raise ValueError("stop_at_tick には state_out(状態の書き出し先)が要る")
        if not (t_begin < int(stop_at_tick) < total_ticks):
            raise ValueError(f"stop_at_tick は {t_begin} より大きく {total_ticks} より小さい(いま {stop_at_tick})")
        t_end = int(stop_at_tick)
    _resuming = _bundle is not None
    # 10d 検収 L6: ラン ID は実行ごとに一意(時刻の印を含む)。状態の口を使わないランでは作らない(空)=manifest を
    # 決定論のまま保つ(同じ設定の 2 回のランの manifest が一致する約束・tests/engine/test_census_out.py)。
    run_id = str(run_id) or (
        RS.run_id_of(_fp, start_T=t_begin, parent=(parent_run or {}).get("run_id", "")) if _state_mode else ""
    )
    # ---- ablation ②③: 腕の値をここで検査する(過程を切ったランでも manifest が嘘をつかない) ----
    p_notice_d50_scale = _check_d50_scale(p_notice_d50_scale)
    # ---- D-66 計画実行層の腕: 値の検査は**層が休むランでも**する(manifest が嘘をつかない) ----
    if str(exit_mode) not in PRESENCE_EXIT_MODES:
        raise ValueError(f"exit_mode は {PRESENCE_EXIT_MODES} のどれか(いま {exit_mode!r})")
    near_tiebreak = check_near_tiebreak(near_tiebreak)
    near_order = check_near_order(near_order)
    if isinstance(group_norms, str) and group_norms not in ("on", "off"):
        raise ValueError(f"group_norms は 'on'/'off' か bool(いま {group_norms!r})")
    group_norms_on = (group_norms == "on") if isinstance(group_norms, str) else bool(group_norms)
    if not (0.0 <= float(attendance_rate) <= 1.0):
        raise ValueError(f"attendance_rate は 0.0〜1.0(いま {attendance_rate})")
    if str(derive_rule) not in PRESENCE_DERIVE_RULES:
        raise ValueError(f"derive_rule は {PRESENCE_DERIVE_RULES} のどれか(いま {derive_rule!r})")
    # ---- C9 位置幾何の腕: 値の検査は**SoA を確保する前**にする(欄が 1 本変わるため) ----
    geometry = check_geometry(geometry)
    # ---- C9c-1 歩行可能面積の出所: 資産を読む前に検査(manifest が嘘をつかない) ----
    area_source = check_area_source(area_source)
    # ---- C9c-1 席面積の感度腕: **None なら表に触らない**(既定は 1 バイトも変わらない) ----
    seat_area_table: dict[str, float] | None = None
    if seat_area_eatery_m2 is not None:
        if float(seat_area_eatery_m2) <= 0.0:
            raise ValueError(f"seat_area_eatery_m2 は正の値(いま {seat_area_eatery_m2})")
        seat_area_table = {k: float(seat_area_eatery_m2) for k in SEAT_AREA_M2}
    if seat_area_retail_m2 is not None and float(seat_area_retail_m2) <= 0.0:
        raise ValueError(f"seat_area_retail_m2 は正の値(いま {seat_area_retail_m2})")
    # ---- D-59 (b) 看板の注視ゲート: 同上(過程を切ったランでも腕の値を検査する) ----
    signage_p_see = check_signage_p_see(signage_p_see)
    p_see_activity_table = check_p_see_activity(p_see_activity)
    p_see_activity_identity = all(v == 1.0 for v in p_see_activity_table.values())
    # ---- AB7 自由意図の腕: 値の検査は**レンダラを作る前**にする(manifest が嘘をつかない) ----
    intent_mode = check_intent_mode(intent_mode)
    role_words = check_role_words(role_words)
    # ---- 語彙 v2 の版: 同上(mock・レンダラ・bridge の前で確定させる) ----
    vocab_version = check_vocab_version(vocab_version)
    # ---- 二層の段 2: 活動層は**語彙 v3 のときだけ**立つ(SoA を確保する前に決める=欄が 2 本変わる) ----
    activity = check_role_words(activity)  # "on"/"off"/bool を bool へ(同じ正規化)
    activity_on = bool(activity) and vocab_version == "v3"
    # ---- 4 段目: 親しみの表の腕(SoA を確保する前に決める=欄が 5 本変わる) ----
    if isinstance(familiarity, str):
        if familiarity not in FAMILIARITY_MODES:
            raise ValueError(f"familiarity は {FAMILIARITY_MODES} か bool(いま {familiarity!r})")
        familiarity_on = familiarity == "on"
    else:
        familiarity_on = bool(familiarity)
    if int(familiarity_k) < 1:
        raise ValueError(f"familiarity_k は 1 以上(いま {familiarity_k})")
    # ---- 6 段目 6a: 記憶の表の腕(SoA を確保する前に決める=欄が 9 本変わる) ----
    if isinstance(memory, str):
        if memory not in MEMORY_MODES:
            raise ValueError(f"memory は {MEMORY_MODES} か bool(いま {memory!r})")
        memory_on = memory == "on"
    else:
        memory_on = bool(memory)
    if int(memory_n) < 1:
        raise ValueError(f"memory_n は 1 以上(いま {memory_n})")
    if not np.isfinite(float(memory_tau)):
        raise ValueError(f"memory_tau は有限の実数(いま {memory_tau})")
    # ---- D-120 7a: 店の評価の記憶の腕(SoA を確保する前に決める=欄が 7 本変わる) ----
    if isinstance(store_memory, str):
        if store_memory not in STORE_MEMORY_MODES:
            raise ValueError(f"store_memory は {STORE_MEMORY_MODES} か bool(いま {store_memory!r})")
        store_memory_on = store_memory == "on"
    else:
        store_memory_on = bool(store_memory)
    if int(store_memory_n) < 1:
        raise ValueError(f"store_memory_n は 1 以上(いま {store_memory_n})")
    store_sigma_table = check_store_sigma(store_sigma)
    store_decay = check_store_decay(store_decay)
    if store_memory_on and not memory_on:
        raise ValueError("store_memory は memory='on' のランでだけ使える(書き手がエピソードの書き手に乗る)")

    def _onoff(v: bool | str, name: str) -> bool:
        if isinstance(v, str):
            if v not in ("on", "off"):
                raise ValueError(f"{name} は 'on'/'off' か bool(いま {v!r})")
            return v == "on"
        return bool(v)

    # ---- C10 8a: 関係辺の腕(SoA を確保する前に決める=欄が 6 本変わる) ----
    if isinstance(relations, str):
        if relations not in REL_MODES:
            raise ValueError(f"relations は {REL_MODES} か bool(いま {relations!r})")
        relations_on = relations == "on"
    else:
        relations_on = bool(relations)
    if relations_on and not memory_on:
        raise ValueError("relations は memory='on' のランでだけ使える(書き手がエピソードの書き手に乗る)")
    if int(rel_k) < 1:
        raise ValueError(f"rel_k は 1 以上(いま {rel_k})")
    rel_tenure_hash = check_rel_tenure_hash(rel_tenure_hash)
    if rel_tau is None:  # 第2波 §2A 項 2: 既定の τ は在職期間ハッシュの版ごとの再逆算値
        rel_tau = REL_TAU_BY_TENURE_HASH[rel_tenure_hash]
    if not (0.0 < float(rel_d) < 1.0) or not np.isfinite(float(rel_tau)):
        raise ValueError(f"rel_d は 0〜1・rel_tau は有限(いま d={rel_d}・τ={rel_tau})")
    if float(rel_init_density) not in REL_INIT_DENSITIES:
        raise ValueError(f"rel_init_density は {REL_INIT_DENSITIES} のどれか(いま {rel_init_density})")
    if int(conv_max_participants) not in (2, 3):
        raise ValueError(f"conv_max_participants は 2 か 3(いま {conv_max_participants})")
    rel_invite_on = _onoff(rel_invite, "rel_invite")
    rel_acq_wake_on = _onoff(rel_acq_wake, "rel_acq_wake")
    rel_copresent_on = _onoff(rel_copresent, "rel_copresent")
    if rel_copresent_on and not relations_on:
        raise ValueError("rel_copresent は relations='on' のランでだけ使える")
    if not (np.isfinite(float(rel_tenure_weeks)) and float(rel_tenure_weeks) >= 1.0):
        raise ValueError(f"rel_tenure_weeks は 1 以上(いま {rel_tenure_weeks})")
    store_wom_on = _onoff(store_wom, "store_wom")
    wom_source = check_wom_source(wom_source)
    store_signage_on = _onoff(store_signage, "store_signage")
    if str(store_recall_scope) not in STORE_RECALL_SCOPES:
        raise ValueError(f"store_recall_scope は {STORE_RECALL_SCOPES} のどれか(いま {store_recall_scope!r})")
    # ---- 5 段目 5a: 空腹のモデル(SoA を確保する前に決める=欄が 4 本変わる) ----
    hunger_model = check_hunger_model(hunger_model)
    energy_rate = check_energy_rate(energy_rate)
    energy_on = hunger_model == "energy"
    meal_sleep_defer = check_meal_sleep_defer(meal_sleep_defer)
    home_meal = check_home_meal(home_meal)
    hunger_words = check_hunger_words(hunger_words)
    # ---- 段 1b: 飲食店の切替口(値の検査は世界を触る前・既定 food=現行のバイト) ----
    eatery = check_eatery_mode(eatery)
    # ---- 段 2a: 選び手と対象の決め方(値の検査は世界を触る前) ----
    chooser = check_chooser(chooser)
    # ---- 5 段目 5b: 方策と事前分布の地域(値の検査は世界を触る前) ----
    policy = check_policy(policy)
    activity_region = check_activity_region(activity_region)
    classical_social = check_classical_social(classical_social)
    meal_gate = check_meal_gate(meal_gate)
    if policy == "classical":
        if llm is not None:
            raise ValueError("policy='classical' と llm の注入は併用できない")
        if mode == "replay" or replay is not None or fleet is not None:
            raise ValueError("policy='classical' は再生・艦隊と併用できない")
        if vocab_version != "v3":
            raise ValueError("policy='classical' は語彙 v3 だけ(5 ラベルの応答文)")
    poi_target = check_poi_target(poi_target)
    #: 語彙 v3 の対象ヒント(「対象: 自宅/職場/学校」→ 拠点セル)は活動層と独立に効かせる。
    v3_hints = vocab_version == "v3"
    # ---- ablation ③: **ランの実効不応期表**を 1 本組む(既定=§6 の表そのもの) ----
    refractory_table = R.refractory_ticks(refractory_scale)
    refractory_scale_norm = R.normalized_refractory_scale(refractory_scale)
    world = world if world is not None else World.synthetic(n_cells=n_cells, seed=pop_seed)  # 10f: 母集団の側
    # 渡された World を使い回しても前のランの切替口が残らないよう、**毎ラン必ず書く**。
    world.set_eatery_mode(eatery)
    # ---- 段 2a: 購入/食事/並ぶの対象=候補 → 選び手(1 ランに 1 つ・世界は読むだけ) ----
    # ``legacy``(Q13)は resolver を作らない=``intents_from_responses`` が従来の最小 id を通す。
    poi_resolver = (
        TargetResolver(
            world=world,
            chooser=make_chooser(chooser, p_h=float(classical_habit_p), tau=float(classical_tau)),
            seed=seed,
            move_search_radius=int(move_search_radius),
        )
        if poi_target == "candidates"
        else None
    )
    mock_move_target_p = float(mock_move_target_p)
    if not (0.0 <= mock_move_target_p <= 1.0):
        raise ValueError(f"mock_move_target_p は 0.0〜1.0(いま {mock_move_target_p})")
    mock_out_of_cell_target_p = float(mock_out_of_cell_target_p)
    if not (0.0 <= mock_out_of_cell_target_p <= 1.0):
        raise ValueError(
            f"mock_out_of_cell_target_p は 0.0〜1.0(いま {mock_out_of_cell_target_p})"
        )
    if int(intent_max_ticks) < 1:
        raise ValueError(f"intent_max_ticks は 1 以上(いま {intent_max_ticks})")
    classical_policy: ClassicalPolicy | None = None
    if policy == "classical":
        _prior_doc, _prior_md5 = load_activity_prior()
        classical_policy = ClassicalPolicy(
            seed=seed,
            prior=ActivityPrior(_prior_doc, calendar.day_kind(0), activity_region),  # 10a #18
            prior_md5=_prior_md5,
            social=classical_social,
            meal_gate=meal_gate,
        )
        llm = classical_policy
    llm = llm if llm is not None else _default_mock(
        seed, vocab_version, mock_move_target_p, mock_out_of_cell_target_p
    )
    salt = run_salt_for(seed)
    # 検収後 P3・10c: テープの脇の meta に応答の遅れと乱数の方式を書く(再生で突き合わせる・テープの版と列は変えない)
    # 10f(K26 (a)): 環境の欄と env_id(manifest・状態の見出しと同じ値)もテープの脇の meta に書く
    _env_fields = RS.environment_fields()
    tape_writer = (TapeWriter(Path(tape_path), run_meta={"response_delay": int(response_delay),
                                                            "rng_scheme": RNG_SCHEME,
                                                            "rng_layout": RNG_LAYOUT,  # 10e(検収 L1)
                                                            # 〔第330・ACT・RET〕暦の規則(再生では check_replay_tape が確かめる)
                                                            "calendar_weekday": WEEKDAY_MODE,
                                                            "weather_scheme": WEATHER_SCHEME,
                                                            "env_id": str(_env_fields["env_id"]),
                                                            "environment": copy.deepcopy(_env_fields)})
                   if tape_path is not None else None)
    conv = (ConversationManager(seed, max_participants=int(conv_max_participants))
            if conversations else None)
    # 10f(K21 (a)): mock 日課・W16 の抽出は母集団の seed から(既定は seed と同じ値)
    schedule = synthesize(n_agents, pop_seed, world.n_cells)
    pop = _resolve_population(population, world_dir, n_agents, pop_seed, world.n_cells)
    # ---- D-66: 週次表(W17)は SoA を確保する前に読む(層の有無で列が 1 本変わるため) ----
    # ``load_weekly`` / ``restrict_to`` は純粋な読み込み(乱数を 1 語も引かない)なので、
    # ここへ繰り上げても帰無腕のバイト列は動かない。
    weekly = load_weekly(world_dir) if (world_dir is not None and pop is not None) else None
    if weekly is not None:
        weekly = weekly.restrict_to(pop.source_agent_id)
    # ``--ablate AB-PLAN-EXECUTOR`` / ``--ablate plan_execution`` でも切れる(台帳の約束)。
    # 層は ``engine/processes`` の下に居ないので ``WorldProcessRunner`` のトグルには載らない。
    _ablated = {str(x) for x in (processes_disabled or ())}
    if _ablated & set(PlanExecutor.process_ids) | (_ablated & {PlanExecutor.ablation_id}):
        plan_executor = False
    plan_exec_on = bool(plan_executor) and weekly is not None and pop is not None
    # ---- C9b(対象と注意・G3〜G7)が立つ条件 ----
    # **辺上の連続位置(距離が定義できる)**と**語彙 v2(段0 辞書 v4 が対象ヒントを運ぶ)**の
    # 両方が要る: 焦点の取得/喪失距離も会話の成立/離脱距離も「距離」抜きには意味が無く、
    # 「近づく/見る」という対象そのものは辞書 v4 でしか入って来ない。したがって**積**で立てる。
    # 既定の 4 腕(node/v1・--derive-rule v2.1・--vocab-version v2・--geometry edge)は
    # どれも片方しか持たないので **checkpoint は 1 バイトも動かない**。
    attention_on = (geometry == "edge") and (vocab_version == "v2")
    agents = AgentState(
        n_agents,
        plan_columns=plan_exec_on,
        edge_columns=(geometry == "edge"),
        attention_columns=attention_on,
        activity_columns=activity_on,
        familiarity_columns=familiarity_on,
        familiarity_k=int(familiarity_k),
        energy_columns=energy_on,
        memory_columns=memory_on,
        memory_n=int(memory_n),
        store_memory_columns=store_memory_on,
        store_memory_n=int(store_memory_n),
        relation_columns=relations_on,
        rel_k=int(rel_k),
    )
    if ledger is not None and ledger.money is not None:
        # 世帯の現金行 = 個体 SoA の money(写しを作らない・台帳の書き込み窓は resolve が持つ)
        ledger.money.attach_household_cash(agents.registry.money)
        if _resuming and int(getattr(ledger.money, "n_transfers", 0)) != 0:
            # 10d(A11): 再開に渡す台帳で参入資本や財布をもう入れていたら、お金が無から湧く(自動補充)
            raise ValueError(
                "再開に渡す台帳は、参入資本や初期の財布を入れる前の新しい台帳にする"
                "(cli.build_ledger_bundle(endow=False)・A11 のお金の自動補充の禁止)"
            )
    if pop is not None:
        schedule = _schedule_with_population(
            schedule, pop, world.n_cells, keep_outside_home=plan_exec_on
        )
    if not _resuming:  # 10d(A11・親の答え 2): 再開では日の頭の初期化を呼ばない(保存した状態を読む)
        R.initialize(agents, world, schedule, day_index=day_index, ledger=ledger)
    # ---- 5 段目 5a: 体のエネルギー収支(値を決める層・書き手は resolve) ----
    energy_layer: EnergyLayer | None = None
    if energy_on:
        _anc, _anc_md5 = load_anchors()
        _emodel = EnergyModel(
            _anc, _anc_md5, rate=energy_rate, minutes_per_tick=float(tick_seconds) / SECONDS_PER_MINUTE
        )
        energy_layer = EnergyLayer(
            model=_emodel,
            n_agents=n_agents,
            out_of_area=OutOfAreaMeals(
                _emodel, n_agents, ticks, weekly=weekly, day_index=calendar.table_weekday(0),  # 10a #15
                tick_seconds=tick_seconds, sleep_defer=meal_sleep_defer,
            ),
            # 第2波 §2B 項 2: 自宅が範囲内(W16 の home_cell >= 0)の体の自宅の食事行(既定 off=None)
            home_meals=(
                HomeMeals(
                    n_agents, ticks, weekly,
                    np.asarray(pop.home_cell, dtype=np.int64) if pop is not None
                    else np.full(n_agents, -1, dtype=np.int64),
                    day_index=calendar.table_weekday(0), tick_seconds=tick_seconds,  # 10a #15
                )
                if home_meal == "plan"
                else None
            ),
            poi_intake=EnergyModel.poi_intake_kind(
                getattr(world.assets, "poi_cat", None),
                getattr(world.assets, "poi_subcat", None),
                world.n_poi,
            ),
        )
        if not _resuming:  # 10d(A11): 空腹の初期値・体の定数は保存した状態から
            R.initialize_energy(agents, energy_layer, pop_seed)  # 10f: 体の定数は母集団の側・10e: 鍵の並べ方
    agents.freeze()
    world.freeze()

    # ---- ⓪a 世界過程(C4 第1陣・世界過程設計書 §3 実装原則3=書き込みは resolve 経由) ----
    runner: WorldProcessRunner | None = None
    if processes:
        runner = WorldProcessRunner(
            world=world,
            agents=agents,
            assets=load_process_assets_or_synthetic(world_dir, world.assets),
            seed=seed,
            population_seed=pop_seed,  # 10f: 域外居住は母集団の側
            environment_seed=env_seed,  # 10f 第 2 段の直し(S1): 気象・大きな催し・道路工事は環境の側
            day_index=day_index,
            tick_seconds=tick_seconds,
            calendar=calendar,  # 10a: #2・#3・#7・#10・#11・#20 は暦の口から
            weather_perturb=weather_perturb,  # 10e(B6): 天気を揺らす(アンサンブル)
            initial_placement=not _resuming,  # 10d(A11): 再開では域外へ置かない
            schedule=schedule,
            ledger=ledger,
            enabled=processes_enabled,
            disabled=processes_disabled,
            p_notice_ablation=p_notice_ablation,
            p_notice_d50_scale=p_notice_d50_scale,
            salient_rate_per_10k=salient_rate_per_10k,
            plan_executor=plan_exec_on,
            seat_area_m2=seat_area_table,
            default_seat_area_m2=seat_area_retail_m2,
        )

    # ---- ⓪a-2 計画実行層(D-66・engine.presence)。W17 + W16 のあるランだけ立つ ----
    presence: PlanExecutor | None = None
    if plan_exec_on:
        presence = PlanExecutor(
            world,
            agents,
            weekly,
            day_index=calendar.table_weekday(0),  # 10a #16
            home_cell=pop.home_cell,
            direction_node=pop.direction_node,
            kind=pop.kind,
            agent_id=pop.source_agent_id,
            rail=(
                runner.rail
                if (runner is not None and runner.is_enabled("rail"))
                else None
            ),
            assets=(
                runner.assets
                if runner is not None
                else load_process_assets_or_synthetic(world_dir, world.assets)
            ),
            ticks=ticks,
            exit_mode=exit_mode,
            attendance_rate=attendance_rate,
            derive_rule=str(derive_rule),
            walk_max_ticks=int(intent_max_ticks),
            seed=seed,  # 10a ◐ #19: 出勤率の抽選の 1 日目からの塩
        )
        if _resuming:  # 10d(A11): 再開では域外の配置をしない(配置の数の控えだけ作る)
            presence.initialize_caches()
        else:
            presence.initialize()  # その時刻に在圏でない体を域外へ(I1 の分母)
        if runner is not None:
            runner.attach_presence(presence)  # hotel の母数・civic の引き込み候補

    # ---- 10a #1・10e(E3): T=0 の世界内日時=暦の開始日(世界の日付は暦・天気の行を引く再生日とは別)。
    # 〔第330・RET〕10e より前の「既定の開始日 + day_index を気象の再生実日で置き換える」導き方(legacy)は消した。
    #: 開始日の検査(違反で止める・祝日表の範囲外・祝日の表が読めないも止める)。
    start_check = calendar.check_start(sim_days)

    # ---- 知覚レンダラ(C3 結線・B0-B6 の本物) ----
    perception: PerceptionRendererAdapter | None = None
    frozen_sources_map: dict[str, str] = {}
    #: C9c-1: 実測面積の資産 SHA(``area_source="plateau"`` のときだけ入る)。
    walkable_sources: dict[str, str] = {}
    if renderer is None:
        assets = PerceptionAssets.load_or_synthetic(world_dir, world)
        # ---- C9c-1: 歩行可能面積を実測に差し替える(**分母は 1 本**=二重定義を作らない) ----
        # ``PerceptionAssets`` は frozen なので ``dataclasses.replace`` で作り直す。差し替えは
        # レンダラを作る**前**なので、B4 の LOS 段・起床条件 (i)・Kladek 減速が同じ値を見る。
        if area_source != DEFAULT_AREA_SOURCE:
            new_area, area_sha = load_walkable_area_m2(world_dir, assets.place_ids)
            assets = dataclasses.replace(assets, walkable_area_m2=new_area)
            walkable_sources = dict(area_sha)
        frozen_sources_map = dict(getattr(assets, "frozen_sources", {}) or {})
        frozen_sources_map.update(walkable_sources)
        # 10e(B0): 知覚が読んだ騒音の地図(W10)と天気(W13)の sha256・集約後の段の指紋(``perception:``)
        frozen_sources_map.update(
            {f"perception:{k}": v for k, v in (getattr(assets, "asset_sources", {}) or {}).items()}
        )
        # 世界内日時 = 暦の口(10a #1)= ``world_start + T × tick_seconds``(``tick_seconds=60`` では
        # 今の ``start + T 分`` と同じ値)。``world_start`` は上で決めた(既定は気象の再生実日)。
        perception = PerceptionRendererAdapter(
            PerceptionRenderer(
                world, agents, assets,
                clock_fn=calendar.datetime_of,
                seed=seed,
                budget_mode=budget_mode_enum,
                signage_enabled=signage,
                signage_p_see=signage_p_see,
                p_see_activity=p_see_activity_table,
                intent_mode=intent_mode,
                vocab_version=vocab_version,
                role_words=role_words,
                near_tiebreak=near_tiebreak,
                near_salt=run_salt_for(seed),
                near_order=near_order,
                hunger_words=hunger_words,
            )
        )
        renderer_obj: Any = perception
        walkable = assets.walkable_area_m2
    elif isinstance(renderer, str):
        if renderer != "stub":
            raise ValueError("renderer は None / 'stub' / Renderer 実装")
        if area_source != DEFAULT_AREA_SOURCE:
            raise ValueError("area_source='plateau' は注入レンダラ('stub')では使えない")
        renderer_obj = StubRenderer()
        walkable = None
    else:
        if area_source != DEFAULT_AREA_SOURCE:
            # 注入された資産を黙って書き換えない(呼び手が自分で差し替える口を持っている)。
            raise ValueError("area_source='plateau' は注入レンダラでは使えない(資産は呼び手のもの)")
        renderer_obj = renderer
        # 注入されたものが本物のアダプタなら、前計算(⓪)と B4 欄の受け渡しも同じ道を通す
        perception = renderer if isinstance(renderer, PerceptionRendererAdapter) else None
        walkable = getattr(getattr(renderer, "assets", None), "walkable_area_m2", None)

    # ---- C9b G6 a′: 目印(landmark 56 + attraction 12)の「名 → POI 索引」表 ----
    # パーサはこれを渡されたときだけ固有名を POI まで解決する(``target.poi_id``)。
    landmarks = world.landmark_targets() if attention_on else None
    bridge = LLMBridge(
        llm,
        renderer=renderer_obj,
        tape=tape_writer,
        mode=mode,
        replay=replay,
        lane=lane,
        tick_seconds=tick_seconds,
        params={"max_tokens": 64, "temperature": 0.0},
        vocab_version=vocab_version,
        landmarks=landmarks,
    )

    # ---- 実艦隊(C6-a)。テープ・未定義行動台帳・デコード設定は bridge と**同じものを共有** ----
    # ``params``(=テープ列 ``params_hash``)は**艦隊の実デコード設定**から作る
    # (``FleetBridge`` の既定)。mock の {max_tokens:64, temperature:0.0} を引きずらない。
    fleet_bridge = (
        FleetBridge(
            fleet,
            tape=tape_writer,
            tape_row_factory=TapeRow,
            undefined=bridge.undefined,
            debug_dir=fleet_debug_dir,
            vocab_version=vocab_version,  # 第214: 渡し忘れ=実 LLM の v2 応答が v1 で解析されていた
            landmarks=landmarks,
        )
        if fleet is not None
        else None
    )
    #: 艦隊で繰り延べになった呼 ``(agent, condition, class_rank, since_tick)``。
    #: 次の刻みの起床候補へ**そのまま再投入**する(破棄禁止=憲法1)。
    fleet_deferred: list[tuple[int, int, int, int]] = []
    n_fleet_reinjected = 0
    n_fleet_resent = 0
    #: 繰り延べ中の個体(再送を数えるためだけの集合。呼数 L4 は**発射数**で数える)。
    fleet_waiting: set[int] = set()
    #: 10d(A10): 艦隊へ**出したが返っていない呼**(call_id → ``LLMCall``・発射の順)。状態を書くときに保存し、
    #: 再開のときに同じ call_id(=同じ seed)で出し直す。艦隊の無いランでは空のまま。
    fleet_inflight: dict[str, Any] = {}
    #: **再生モードの艦隊の代役**(D-58)。``observed_tick`` → その刻みで「届く」項目。
    #: 項目は ``(繰り延べか, ペイロード)``。繰り延べは ``(agent, cond, class, since_tick)``、
    #: 応答は ``BridgeResult`` そのもの。テープが版1(``observed_tick=-1``)なら常に空
    #: =mock 経路は 1 バイトも変わらない。
    replay_inbox: dict[int, list[tuple[bool, Any]]] = {}

    detector = ChangeDetector(n_agents, world.n_cells, walkable_area_m2=walkable)
    # ---- C9 位置幾何(G1 (b))。``node``(既定)では作らない=resolve は現行の経路 ----
    # 密度の分母(歩行可能面積)は**変化検出と同じ値**を使う(二重定義を作らない)。
    geom: EdgeGeometry | None = (
        EdgeGeometry(
            world.assets,
            seed=seed,
            population_seed=pop_seed,  # 10f: 希望歩行速度は母集団の側
            n_agents=n_agents,
            walkable_area_m2=walkable,
            tick_seconds=tick_seconds,
        )
        if geometry == "edge"
        else None
    )
    #: edge 幾何の診断(ラン通算)。node では 0 のまま。
    geometry_hops = 0
    geometry_jammed = 0
    #: このランの 1 刻みの呼数上限(``None`` なら L4 按分)。manifest の ``budget_per_tick``。
    effective_budget = float(budget) if budget is not None else call_budget_per_tick(n_agents)
    arbiter = Arbiter(n_agents, salt, effective_budget)
    space = C.ResourceSpace(world.n_poi, n_agents, world.n_cells)

    # 計画境界。W17 週次表(w17_schedule.parquet)があればそれを使い、無ければ mock 日課の 5 境界へ落ちる
    # (C5-b 結線・09-09)。mock 経路は --no-population と合成世界の下限対照としてそのまま残す。
    if weekly is not None:
        # D-62: 就寝境界で「どこで寝るか」が要るので行き先セルも一緒に取る(並びは同じ)
        # 10a #13・#14: W17 の曜日の行は暦の口から(day_index モードでは ``day_index % 7``)
        _wd0 = calendar.table_weekday(0)
        b_agent, b_cond, b_tick, b_cell = weekly.boundary_events_full(_wd0)
        schedule = apply_to_mock_schedule(schedule, weekly, _wd0)  # 拠点セル(自宅/職場)の上書き
        # ---- D-62 (b): 刻み 0 の activity を W17 の 0:00 時点の活動から立てる ----
        # ``initialize`` は全員 SLEEPING(週次表の無い世界の既定)。ここで立て直す。
        if plan_sleep and not _resuming:  # 10d(A11): 再開では初期の活動を立てない
            R.set_initial_activity(agents, weekly.initial_activity(_wd0))
    else:
        # 10a #12: mock 日課の平日/休日は暦の口の土休から
        b_agent, b_slot, b_tick = schedule.events_of_day(
            calendar.table_weekday(0), rest_day=calendar.is_rest_day(0)
        )
        b_cell = np.full(b_agent.size, -1, dtype=np.int32)  # mock 日課の就寝地=自宅セル
        b_cond = np.array(
            [
                int(WakeCondition.PLAN_GENERAL),
                int(WakeCondition.PLAN_TRANSIT),
                int(WakeCondition.PLAN_GENERAL),
                int(WakeCondition.PLAN_TRANSIT),
                int(WakeCondition.PLAN_SLEEPING),
            ],
            dtype=np.int8,
        )[b_slot]
    b_start = np.searchsorted(b_tick, np.arange(ticks + 1), side="left")
    schedule_hash = weekly.schedule_hash() if weekly is not None else ""
    # ---- 5 段目 5b: 方策 classical を SoA・世界・計画境界に結ぶ(読むだけ) ----
    if classical_policy is not None:
        _has_work = np.zeros(n_agents, dtype=bool)
        if pop is not None:
            _m = min(n_agents, int(pop.n))
            _has_work[:_m] = np.asarray(pop.work_cell, dtype=np.int64)[:_m] >= 0
        _pa = getattr(runner, "assets", None) if runner is not None else None
        classical_policy.bind(
            agents=agents,
            world=world,
            home_cell=np.asarray(schedule.home_cell),
            work_cell=np.asarray(schedule.work_cell),
            school_cell=getattr(schedule, "school_cell", None),
            has_work=_has_work,
            boundary_agent=b_agent,
            boundary_tick=b_tick,
            tick_seconds=tick_seconds,
            station_cells=getattr(_pa, "line_platform_cell", None),
        )
        if energy_layer is not None:  # 第2波 §2B Q-2B-6 (ii): 食事で per_hour の門の H を 0 に(per_wake は None)
            energy_layer.meal_reset = classical_policy.meal_reset_array()
    #: 5 段目 5b(L4 (a)・SOFAI 形式): 時 × 層(0=System 1 予定/習慣で呼ばない・1=System 1.5 選択器・
    #: 2=System 2 LLM/mock)× 起床入口 の判断数。層 1/2 は発射した呼(方策で分ける)・層 0 は
    #: エンジンが予定を実行した件(計画の就寝・意図の到着・計画実行層の到着/退出)。
    layer_counts = np.zeros((24, 3, len(_ENTRANCES)), dtype=np.int64)
    #: 9a(D-112 ④): 退去の効果の件数(診断だけ)。
    leave_counts: dict[str, int] = {"n_leave": 0, "n_leave_indoor": 0, "n_leave_queue": 0,
                                    "n_leave_conversing": 0}
    leave_closed = 0
    _call_layer = 1 if classical_policy is not None else 2
    # ---- 二層の段 2: 活動層(「次の予定」は上の計画境界の表から引く) ----
    act_layer: ActivityLayer | None = (
        ActivityLayer(
            n_agents, world, salt, tick_seconds=tick_seconds,
            boundary_agent=b_agent, boundary_tick=b_tick,
        )
        if activity_on
        else None
    )
    if act_layer is not None:
        act_layer.leave_effect = bool(leave_effect)  # 9a: 退去の効果の切替口と揃える
    # ---- 段 2c: 意図の保持(活動層+候補の解決がある=語彙 v3・activity on・candidates) ----
    intent_layer: IntentLayer | None = (
        IntentLayer(n_agents, world, max_ticks=int(intent_max_ticks))
        if (act_layer is not None and poi_resolver is not None)
        else None
    )
    # ---- 段 2c Q25: 名指しの即時閉店の B6 補足(店名・閉店中・W7 の開店時刻) ----
    _q25_renderer = getattr(perception, "renderer", None) if perception is not None else None
    if (
        intent_layer is not None
        and poi_resolver is not None
        and _q25_renderer is not None
        and hasattr(_q25_renderer, "named_closed_lookup")
    ):
        _q25_renderer.named_closed_lookup = _named_closed_lookup(
            poi_resolver, runner, calendar, tick_seconds
        )
    # ---- 10d 検収 D1: B3 の天候は世界過程の「その日の再生の実日」で引く(体の暑さと同じ行・日付の語は暦) ----
    if (
        _q25_renderer is not None and hasattr(_q25_renderer, "weather_date_fn")
        and runner is not None and runner.replay_date
    ):
        _env = runner.environment
        _q25_renderer.weather_date_fn = lambda: (_env.replay_date or None)
        # ---- 10e(B6): 天気の規則 calendar では B3 の語を環境の過程と同じ規則で作る(天候=再生日の行・日照=暦の日付の
        # 日の出と日の入り・暑さ=体感温度と同じ暑さ段)。天候の語はレンダラの W13 の表を再生日で引く(欠けた時の扱いも今と同じ)
        if runner.assets.has_weather and hasattr(_q25_renderer, "weather_words_fn"):
            _wr = _q25_renderer

            def _b3_words(when: datetime) -> tuple[str, str, str]:
                rd = _env.replay_date
                wd = (datetime.strptime(rd, "%Y-%m-%d").replace(hour=int(when.hour)) if rd else when)
                daylight, heat = _env.b3_sun_heat(int(when.hour))
                return _wr.assets.weather(wd)[0], daylight, heat

            _wr.weather_words_fn = _b3_words
            _wr.weather_words_key_fn = lambda when: (_env.replay_date, when.date().isoformat())
    # ---- 4 段目: 親しみの表(値を決める層・書き手は resolve.write_familiarity) ----
    _fam_renderer = getattr(perception, "renderer", None) if perception is not None else None
    _fam_has_renderer = _fam_renderer is not None and hasattr(_fam_renderer, "signage_exposures")
    fam_layer: FamiliarityLayer | None = (
        FamiliarityLayer(
            n_agents, int(familiarity_k), minutes_per_tick=float(tick_seconds) / SECONDS_PER_MINUTE,
            # 親決定 (f): 入った回 × そのセルで B2 に載る看板 × p_see(描画と同じ集合・同じ流れ)
            signage_poi_by_cell=(
                _fam_renderer.signage_poi_by_cell() if _fam_has_renderer else None
            ),
            p_see=float(getattr(_fam_renderer, "signage_p_see", 1.0)) if _fam_has_renderer else 1.0,
            seed=getattr(_fam_renderer, "seed", seed) if _fam_has_renderer else seed,
            # 5c: 乗数表が全部 1.0(既定)なら渡さない=従来のスカラー p_see の経路のまま
            p_see_fn=(
                _fam_renderer.effective_p_see
                if (_fam_has_renderer and not p_see_activity_identity)
                else None
            ),
            kind_fn=(
                _fam_renderer.activity_classes
                if (_fam_has_renderer and hasattr(_fam_renderer, "activity_classes"))
                else None
            ),
        )
        if familiarity_on
        else None
    )
    # ---- 6 段目 6a: 記憶の表(値を決める層・書き手は resolve.write_memory) ----
    mem_layer: MemoryLayer | None = (
        MemoryLayer(n_agents, int(memory_n), minutes_per_tick=float(tick_seconds) / SECONDS_PER_MINUTE)
        if memory_on
        else None
    )
    if (fam_layer is not None or mem_layer is not None) and _fam_has_renderer:
        _fam_renderer.signage_exposures = []  # 描画による露出の控え(刻みごとに取り出す)
    # ---- 記憶 第 1 段 6b: 想起の口(on のランだけ描画に差し込む・off は None=描画バイト不変) ----
    if mem_layer is not None:
        mem_layer.tau = float(memory_tau)
    # ---- 第 1 期 1-6 記憶の器 M0(腕 --memory-store events・既定 mem=器を作らない)。器は記憶の表と同じ規則の写しで、
    # 表に書く所で同じ出来事を書き、想起を器から引く。見せた行の録画(描画の口)とテープの列 recalled_event_ids
    # (版 4 の中・腕のランだけ)。状態台帳の行 M0(作り直せる)・M0R(録画と計数=捨ててよい) ----
    from shibuya.engine import memory_store as _MS

    if mem_layer is not None and _MS.arm() == _MS.ARM_EVENTS:
        _m0 = mem_layer.enable_memory_store(step_seconds=int(tick_seconds))
        if perception is not None:
            perception.memory_shown = mem_layer.on_shown
        if tape_writer is not None:
            tape_writer.arm_columns[_MS.TAPE_COLUMN] = mem_layer.tape_event_ids
            _m0.attach_tape()
    # ---- D-120 7a: 店の評価の記憶(エピソードの書き手に乗る・本段では誰も読まない) ----
    if mem_layer is not None and store_memory_on:
        mem_layer.enable_store(int(store_memory_n), sigma=store_sigma_table, decay=store_decay,
                               signage=store_signage_on, poi_cell=np.asarray(world.pois.cell),
                               recall_scope=str(store_recall_scope))
        # ---- D-120 7c: 想起優先の候補合成(選び手 classical のとき)と決め手の記録 ----
        if poi_resolver is not None:
            poi_resolver.store_choice = StoreChoice(
                mem_layer, world, n_agents, seed=seed,
                boundary_agent=b_agent, boundary_tick=b_tick,
                walk_m_per_tick=_walk_m_per_tick(world, n_agents, geometry=str(geometry), geom=geom,
                                                  tick_seconds=int(tick_seconds)),
                intent_max_ticks=int(intent_max_ticks),
                minutes_per_tick=float(tick_seconds) / SECONDS_PER_MINUTE,
            )
    # ---- C10 8a: 関係辺(機械的初期化=W16+W17 の共在・書き手は記憶のエピソード・知人の結線) ----
    rel_layer = None
    if mem_layer is not None and relations_on:
        rel_layer = mem_layer.enable_relations(int(rel_k), tau=float(rel_tau), d=float(rel_d))
        _t_rel = time.perf_counter()
        _init = _rel_initial_edges(
            pop, weekly, n_agents, k=int(rel_k), day_index=int(calendar.table_weekday(0)),  # 10a #19
            density=float(rel_init_density),
            minutes_per_tick=float(tick_seconds) / SECONDS_PER_MINUTE, d=float(rel_d), tau=float(rel_tau),
            tenure_weeks=float(rel_tenure_weeks), tenure_hash=str(rel_tenure_hash),
        ) if (pop is not None and not _resuming) else None  # 10d(A11): 再開では初期の辺を作らない
        if _init is not None:
            rel_layer.seed_initial(agents, _init)
            rel_layer.init_audit["init_seconds_nondeterministic"] = round(time.perf_counter() - _t_rel, 3)
        if _fam_renderer is not None and hasattr(_fam_renderer, "acquaintance_fn"):
            _fam_renderer.acquaintance_fn = lambda i_, t_: rel_layer.acquaintances(agents, i_, t_)
        if classical_policy is not None:
            def _classical_acq(aid_: int, tick_: int, ids_: list[int]) -> np.ndarray:
                # 第2波 §2A 項 3-1: 近接行の人 → 生きている辺の A(辺が無い/τ 未満は −inf)。
                # 検収後: 話しかけられない相手(会話中・就寝中=resolve._UNADDRESSABLE)と、このランの設定で会話が
                # 届かない相手(talk_within_reach が偽)も −inf(resolve._apply_talk が PARTNER_BUSY/GONE で落とす相手)。
                # 逐次ループ宣言: 近接行の人数ぶん(≤ 数人)× 呼数=呼ごとの小さな表引き
                e_ = rel_layer.edges(agents, int(aid_), int(tick_))
                lut_ = dict(zip(e_.partner.tolist(), e_.A.tolist()))
                A_ = np.asarray([lut_.get(int(p_), -np.inf) for p_ in ids_], dtype=np.float64)
                return classical_acq_addressable(agents, int(aid_), ids_, A_, by_distance=attention_on)

            classical_policy.acq_fn = _classical_acq
        # ---- C10 8b: 会話の起点と相手選択・知人出現の起床・同席(腕) ----
        if rel_invite_on:
            rel_layer.enable_invite(salt)
            if classical_policy is not None:
                def _classical_partner(aid_: int, tick_: int, strangers_: list[int]) -> int:
                    # 残りの層=近接行の「未知」の人から seed つきハッシュ順(D-31 (a)=行の先頭=id の小さい人にしない)
                    stranger_ = rel_layer.pick_rest(int(tick_), int(aid_), strangers_)
                    got_, _o = rel_layer.choose_talk_partners(
                        agents, int(tick_), np.asarray([int(aid_)]), np.asarray([int(stranger_)]),
                        np.asarray([False]), np.asarray([-1]), record_origin=False,
                    )
                    return int(got_[0])

                classical_policy.partner_fn = _classical_partner
        if rel_acq_wake_on:
            rel_layer.enable_acquaintance_wake()
        if rel_copresent_on:
            rel_layer.enable_copresent()
        if conv is not None:
            conv.track_origins(REL_ORIGINS)
    if (
        conv is not None and int(conv_max_participants) > 2 and _fam_renderer is not None
        and hasattr(_fam_renderer, "session_partner_fn")
    ):
        def _session_partners(i_: int) -> list[int]:
            s_ = conv.session_of(int(i_))
            return [int(q) for q in s_.participants if int(q) != int(i_)] if s_ is not None else []

        _fam_renderer.session_partner_fn = _session_partners
    # ---- D-120 7b: 会話からの抽出(店名の辞書=W6 の店・評価語の辞書 v0・呼数 0) ----
    wom_ex: WomExtractor | None = (
        WomExtractor.from_world(world, source=wom_source)
        if mem_layer is not None and mem_layer.store is not None
        else None
    )
    if _fam_renderer is not None and hasattr(_fam_renderer, "memory_recall"):
        _fam_renderer.memory_recall = (
            (lambda i_, t_, c_, inv_: mem_layer.recall(agents, i_, t_, c_, inv_))
            if mem_layer is not None
            else None
        )

    # 1-0 段 E: 会話ターンの発話 ``_utter`` は engine.systems.llm_io.utter へ移した(箱を受け取る関数)
    #: 発射した呼の起床条件ごとの件数(起床の内訳・満了入口の列を含む)。
    calls_by_cond = np.zeros(N_WAKE_CONDITIONS_ALL, dtype=np.int64)

    result = RunResult(
        n_agents=n_agents,
        n_cells=world.n_cells,
        seed=seed,
        population_seed=pop_seed,  # 10f(K21 (a))
        environment_seed=env_seed,  # 10f 第 2 段の直し(S1)
        ticks=t_end - t_begin,  # 10a: 回した通しの刻みの数(1 日のランでは ``ticks``)・10d: 再開・止めたランはその区間
        world_source=world.assets.source,
        tape_path=str(tape_path) if tape_path is not None else "",
        mode=mode,
    )
    result.env_fields = _env_fields  # 10f: manifest の environment・env_id
    result.money_start = int(agents.registry.money.astype(np.int64).sum())
    #: D-71 §3 J: 行動コード別の適用件数(``ResolveOutcome.per_action`` のラン合計)。
    per_action_total: dict[int, int] = {}
    # 第308 D-107 (a): 群・規範の計器(**読むだけ**=状態・乱数・テープに触れない)
    from shibuya.engine.llm_bridge import ACTION_WORD_BY_CODE as _AWBC
    from shibuya.engine.norm_meter import GroupNormMeter, role_code_table

    norm_meter = (GroupNormMeter(agents, world, role_codes=role_code_table(vocab_version),
                                 code_words=_AWBC, tick_seconds=int(tick_seconds),
                                 process_assets=getattr(runner, "assets", None) if runner is not None else None)
                  if group_norms_on else None)  # 第309 Q150: --group-norms off で計器を通さない
    # 在圏 journal(C7 受入計器 tools/c7・holdout 照合の入力)。既定 0=書かない(状態・診断・テープに影響なし)。
    occ_ticks: list[int] = []
    occ_counts: list[np.ndarray] = []
    occ_kind: list[np.ndarray] = []
    occ_transit: list[np.ndarray] = []
    # ``fleet_wait`` は ``--fleet-wait-s`` の待ち(``llm`` から分離して数える=P2 の切り分け用)。
    # ``movement_cpu`` は movement 区間の**スレッド CPU 時間**(壁時計との差=GIL 待ち)。
    phase = {k: 0.0 for k in ("presence", "detect", "arbiter", "llm", "fleet_wait", "phase_a",
                              "phase_b", "phase_c", "movement", "movement_cpu", "checkpoint")}
    diag_rows: list[tuple[int, ...]] = []
    # (t_apply, class, agent, condition, text, action_code, target_person,
    #  **target_hint**, **target_poi**, **activity**, **target**, **``fire_tick``**, **call_id**)
    # ``activity`` = 二層の段 2 の活動(``engine.activity.ActivityPayload``・v3 以外は None)。
    # ``target_person`` = LLM が「対象」欄に書いた個体 id(-1=名指しなし・C6 09-09)。
    # ``target_hint`` = 段0 辞書 v4 の対象ヒント索引(C9b G5・0=なし)。
    # ``target_poi`` = 「対象」欄が目印 POI に解決できたときの索引(C9b G6 a′・-1=なし)。
    # 10b(① の前提): 末尾に**発射の刻み** と **call_id**(``"{発射の刻み}:{体}:{級}"``=テープの call_id)。
    # 読む側は今は無い(原因の欄は ① の記録で)=組の形が変わるだけで既定の結果は動かない。
    pending: list[tuple[int, int, int, int, str, int, int, int, int, Any, Any, int, str]] = []
    #: この刻みに適用した応答の (体, 行動コード, 活動)。``resolve.apply`` の後に活動層が書く。
    applied_activity: tuple[list[int], list[int], list[Any]] = ([], [], [])
    #: C9b G3/G4: この刻みに LLM が言った**焦点の要求**(-1=なし)。使い回す 1 本の
    #: バッファ(毎刻み触った行だけ戻す=個体数ぶんの確保は 1 回きり)。
    focus_request = (
        np.full(n_agents, int(FOCUS_NONE), dtype=np.int64) if attention_on else None
    )
    #: この刻みに応答を適用した個体 → 行動コード(会話の被招待の返事を読むのに使う)。
    applied_now: dict[int, int] = {}
    #: 会話の相手の由来(``conv_*`` 診断行の素材)。
    talk_stats: dict[str, int] = {}
    prev_tape_misses = 0
    prev_sessions = 0
    peak_pending = 0
    peak_intents = 0
    peak_backlog = 0
    n_undefined_total = 0
    #: D-66: **発射した呼**のうち域外の体宛てだった延べ数(抑止が効いていれば 0)。
    n_outside_calls = 0
    # ---- D-62「就寝は計画の実行」の計数(診断列は増やさない=診断表の形を変えない) ----
    #: ``resolve.begin_planned_sleep`` の内訳 + ``arrived``(就寝地へ着いて寝た)+
    #: ``woke``(非就寝の計画境界で起こした)。
    sleep_counts: dict[str, int] = {}
    #: 世界内時刻の**時**別「起きている体」の延べ数と刻みの数(起床率/時 の分子・分母)。
    awake_sum = [0] * HOURS_PER_DAY
    awake_ticks = [0] * HOURS_PER_DAY
    #: 5 段目 5a(診断): 内受容の跨ぎ(変数 3 × 上げ/下げ × 全体/起きて範囲内)。
    intero_cross = np.zeros((3, 2, 2), dtype=np.int64)

    # 1-0 段 E: ④′ の到着の受け取り ``_receive_arrivals`` は engine.systems.llm_io.receive_arrivals へ移した


    # ================================================================ 10d: 日の頭・日の締め・状態の書き出しと読み込み
    #: 日ごとの締めの記録(締めの回数=日数・保存則・体の数・日の終わりのお金と 2 つのハッシュ)。manifest の ``daily``。
    daily_records: list[dict[str, Any]] = []
    #: 日の頭(1 日目から)の記録(日の頭のお金=前の日の終わりと同じか=自動補充が無いか)。manifest の ``day_heads``。
    day_heads: list[dict[str, Any]] = []
    #: K9 (a) のつなぎで W17 の曜日の行を月曜(0)に置き換えた日。
    w17_substituted: list[int] = []
    #: 書いた状態のファイル(名前・T・バイト・``finished``・書くのにかかった秒=壁時計)。
    state_files: list[dict[str, Any]] = []

    # ---- 第 1 期 1-3: 出来事の記録(CP12・既定 on・切替口 SHIBUYA_EVENTS=off/CLI --events off)。状態台帳の行 E
    # (軸 1 diag・軸 2 discardable)=ハッシュにも状態のファイルにも入らない。再開のランは空から書く(id は (t_ns, seq)
    # なので刻みの境目からの再開でも通しのランと同じ id になる)。ActualLog の行に id の目印を付ける口を実行器に挿す ----
    from shibuya.engine.events import log as _EV

    events = _EV.EventLog(enabled=_EV.enabled())
    if runner is not None:
        runner.attach_events(events)
    if ledger is not None:  # 第 1 期 1-9: 原因を渡した金の移動が出来事を書き、金と物の台帳の行に id の目印を付ける
        from shibuya.engine.events.links import MoneyEventLink

        ledger.attach_events(MoneyEventLink(events), step_seconds=int(tick_seconds))

    # ---- 1-0 段 C: 状態の箱(局所の割り当ての表 local-assignment.json・草案 §2-3)。物はそのまま指す(写しを作らない) ----
    box = _BX.Box(
        cfg=_BX.RunConfig(
            n_agents=n_agents, seed=seed, tick_seconds=tick_seconds, ticks=ticks, fleet_wait_s=fleet_wait_s,
            checkpoint_every=checkpoint_every, day_index=day_index, l4_scale=l4_scale, mode=mode, lane=lane,
            census_out=census_out, attendance_rate=attendance_rate, exit_mode=exit_mode, derive_rule=derive_rule,
            checkpoint_detail=checkpoint_detail, classical_habit_p=classical_habit_p, classical_tau=classical_tau,
            familiarity_k=familiarity_k, intent_max_ticks=intent_max_ticks, leave_effect=leave_effect,
            memory_n=memory_n, move_search_radius=move_search_radius, occupancy_every=occupancy_every,
            occupancy_path=occupancy_path, outside_suppression=outside_suppression,
            p_notice_ablation=p_notice_ablation, p_notice_d50_scale=p_notice_d50_scale, plan_sleep=plan_sleep,
            queue_service=queue_service, report_precondition=report_precondition, response_delay=response_delay,
            run_id=run_id, seat_area_eatery_m2=seat_area_eatery_m2, seat_area_retail_m2=seat_area_retail_m2,
            signage=signage, signage_p_see=signage_p_see, sim_days=sim_days, sleep_suppression=sleep_suppression,
            state_out=state_out, store_recall_scope=store_recall_scope, vocab_version=vocab_version,
            activity_region=activity_region, area_source=area_source, chooser=chooser, eatery=eatery,
            energy_rate=energy_rate, geometry=geometry, home_meal=home_meal, hunger_model=hunger_model,
            hunger_words=hunger_words, intent_mode=intent_mode, meal_sleep_defer=meal_sleep_defer,
            mock_move_target_p=mock_move_target_p, mock_out_of_cell_target_p=mock_out_of_cell_target_p,
            near_order=near_order, near_tiebreak=near_tiebreak, poi_target=poi_target, policy=policy,
            role_words=role_words,
            pop_seed=pop_seed, env_seed=env_seed, tpd=tpd, total_ticks=total_ticks, t_begin=t_begin, t_end=t_end,
            activity_on=activity_on, energy_on=energy_on, familiarity_on=familiarity_on, memory_on=memory_on,
            store_memory_on=store_memory_on, store_signage_on=store_signage_on, store_wom_on=store_wom_on,
            plan_exec_on=plan_exec_on, attention_on=attention_on, v3_hints=v3_hints, salt=salt,
            refractory_table=refractory_table, refractory_scale_norm=refractory_scale_norm,
            budget_mode_enum=budget_mode_enum, p_see_activity_table=p_see_activity_table,
            p_see_activity_identity=p_see_activity_identity, call_layer=_call_layer, fp=_fp, parent_run=parent_run,
        ),
        soa=_BX.SoAState(agents=agents, world=world),
        layers=_BX.Layers(
            act_layer=act_layer, intent_layer=intent_layer, fam_layer=fam_layer, mem_layer=mem_layer,
            poi_resolver=poi_resolver, wom=wom_ex, rel_layer=rel_layer, classical=classical_policy,
            energy=energy_layer, norm_meter=norm_meter, presence=presence, conv=conv, arbiter=arbiter,
            detector=detector, runner=runner, ledger=ledger,
            renderer=getattr(perception, "renderer", None) if perception is not None else None,
            bridge=bridge, fleet_bridge=fleet_bridge, events=events,
        ),
        llm=_BX.LlmIo(pending=pending, fleet_deferred=fleet_deferred, fleet_waiting=fleet_waiting,
                      fleet_inflight=fleet_inflight, replay_inbox=replay_inbox),
        day=_BX.DayTables(b_agent=b_agent, b_cond=b_cond, b_tick=b_tick, b_cell=b_cell, b_start=b_start,
                          w17_substituted=w17_substituted),
        buffers=_BX.Buffers(focus_request=focus_request),
        scratch=_BX.TickScratch(),
        runstats=_BX.RunStats(
            result=result, phase=phase, diag_rows=diag_rows, layer_counts=layer_counts, leave_counts=leave_counts,
            sleep_tally=sleep_counts, awake_sum=awake_sum, awake_ticks=awake_ticks, calls_by_cond=calls_by_cond,
            per_action_total=per_action_total, talk_stats=talk_stats, intero_cross=intero_cross,
            occ_ticks=occ_ticks, occ_counts=occ_counts, occ_kind=occ_kind, occ_transit=occ_transit,
            daily_records=daily_records, day_heads=day_heads, state_files=state_files,
            frozen_sources_map=frozen_sources_map, leave_closed=leave_closed, geometry_hops=geometry_hops,
            geometry_jammed=geometry_jammed, n_fleet_reinjected=n_fleet_reinjected, n_fleet_resent=n_fleet_resent,
            n_outside_calls=n_outside_calls, n_undefined_total=n_undefined_total, peak_backlog=peak_backlog,
            peak_intents=peak_intents, peak_pending=peak_pending, prev_sessions=prev_sessions,
            prev_tape_misses=prev_tape_misses, t_start=t_start, read_seconds=_read_seconds,
        ),
        fx=_BX.Fixtures(
            calendar=calendar, schedule=schedule, schedule_hash=schedule_hash, weekly=weekly, space=space,
            geom=geom, perception=perception, renderer_obj=renderer_obj, walkable=walkable,
            env_fields=_env_fields, start_check=start_check, fleet=fleet,
        ),
    )
    del pending, n_undefined_total, n_fleet_reinjected, n_fleet_resent, n_outside_calls, geometry_hops
    del geometry_jammed, leave_closed, peak_pending, peak_intents, peak_backlog, prev_sessions, prev_tape_misses
    del b_agent, b_cond, b_tick, b_cell, b_start, t_start, _read_seconds

    # ---- 10d: 再開(保存した状態を読む=日の頭の初期化は上で呼んでいない) ----
    #: 読み込み(ファイルを読む)と戻す(表の張り直し・SoA と外の状態・full-hash の検算)の秒(壁時計=記録だけ)。
    if _bundle is not None:
        _t_r = time.perf_counter()
        # 再開の時刻より前に頭が来た日の表を張り直す(便の索引を通しのランと同じにする)。日の境目からの再開では
        # その日の頭はループの先頭で張る(通しのランと同じ位置)。
        for _d in range(1, (t_begin - 1) // tpd + 1):
            _SIO.relay_tables(box, _d)
        R.restore_soa(agents, world, _SIO.pst_now(box), _bundle.soa)
        _SIO.rebuild_derived(box)  # 10d(親の答え 2): 起動時に SoA から作る表を、戻した SoA から作り直す
        RS.check_item_kinds(_SIO.hash_owners(box), _bundle.items)  # 10f(K23 (a)): 戻す前に今の値の型と突き合わせる
        R.restore_items(_SIO.hash_owners(box), _bundle.items)
        if mem_layer is not None and mem_layer.memory_store is not None:
            mem_layer.rebuild_memory_store(agents)  # 1-6 M0: 器は戻した記憶の表と要旨から作り直す(台帳の行 M0)
        _full_r, _ = _SIO.full_state_hash(agents, world, _SIO.pst_now(box), schedule.population_hash, schedule_hash,
                                     _SIO.hash_owners(box), memo={})
        if _full_r != str(_bundle.header.get("hashes", {}).get("full_hash", "")):
            raise RuntimeError(
                "再開で戻した状態の full-hash が保存したときと違う(戻し忘れか戻し違い・"
                f"保存 {str(_bundle.header.get('hashes', {}).get('full_hash', ''))[:16]}・戻した後 {_full_r[:16]})"
            )
        result.money_start = int(agents.registry.money.astype(np.int64).sum())
        # 10d 検収 L1: 診断の行の差分の基準(前の刻みの終わりの値)を戻した状態から置く(通しと同じ差分になる)
        box.runstats.prev_sessions = conv.n_opened if conv is not None else 0
        box.runstats.prev_tape_misses = bridge.n_tape_misses
        box.runstats.restore_seconds = time.perf_counter() - _t_r
        if _bundle.inflight:
            if fleet_bridge is None:
                raise ValueError("保存に艦隊の未着の呼があるが、再開のランに艦隊が無い")
            # 出したが返っていない呼を同じ call_id(=艦隊の seed は call_id とランの seed から決まる)で出し直す
            _calls_r = list(_bundle.inflight)
            for c_ in _calls_r:
                fleet_inflight[str(c_.call_id)] = c_
            for d_ in fleet_bridge.submit(_calls_r, now_tick=t_begin - 1):
                fleet_inflight.pop(str(d_.call.call_id), None)
                fleet_deferred.append(
                    (int(d_.call.agent_id), int(d_.call.condition), int(d_.call.wake_class), int(d_.call.wake_since))
                )
    return box
