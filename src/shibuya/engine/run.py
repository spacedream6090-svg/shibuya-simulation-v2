"""engine.run — 1 シミュ日の mock ラン(予算行 **W2**)と CLI。

正典
- 予算宣言表 **W2**: 「壁時計/シミュ日(Phase 2・**5千体・CPU・mock LLM**)**≤10分**。
  mock は呼び出しコストゼロ級=**エンジン性能の検収値**」。
- 運用設計書 §2.2/§2.4: tick の骨格 =
  ① 前 tick までに届いた LLM 応答を **apply_key 昇順**で適用(=Phase A の intent 源)
  ⓪ 知覚の tick 前計算(``Renderer.prepare_tick``・**B4 描画欄はここで 1 本作る**)
  ② 変化検出(P6)→ 起床候補(⓪ の欄をそのまま読む=描画と検出が同じ 1 本)
  ③ 繰り延べアービタ(§6)→ 呼ぶ個体
  ④ LLM 呼(応答は ``pending_apply`` へ・t_apply=起床+δ_perc+δ_think を分tickへ切り上げ)
  ⑤ Phase A(LLM 由来 intent + エンジン継続)→ ⑥ Phase B(資源裁定)→ ⑦ Phase C(resolve)
- 運用設計書 §1.4 T1/T2: 「同一 manifest×2 で**全 checkpoint ハッシュ一致**」。
- 運用設計書 §1.4 T4: 「n=5,000 と 5,001 で既存個体の乱数列が不変」(``agents.schedule``)。
- 世界過程設計書 §6 D-R2-6: 状態成長宣言の 24step→1日/30日 外挿ゲート。

**run_salt**(親の指定): ``blake3(master_seed の正規表現 ‖ 0x1f ‖ "engine")`` の先頭 16 バイト。
**RNG カウンタの class_rank**: ``class_rank + 1``(INSTITUTION −1 → 0)。

逐次ループ宣言(P4)
1. ``run_day``: **tick 数**ぶんのループ(1,440)。1 tick の中身は全て配列演算。
2. ``_call_llm``: **選抜された呼数**ぶんのループ(平均 35/tick・L4 の制御目標)。
   LLM クライアントは 1 呼=1 関数呼び出しの契約(``llm.LLMClient``)なので束ねられない。
   実艦隊では httpx の並行発射(C6)に置き換わる。

**C3 の結線(第3弾)**
- LLM 呼は ``engine.llm_bridge.LLMBridge`` 一本を通る(録画テープ・δ_think レーン・
  2行形パース・未定義行動5段が1か所に集まる)。``mode="replay"`` はテープ完全一致で回し、
  テープ外は**計数して待機へ落とす**(実LLMへは落とさない=運用設計書 §2.5)。
- 会話は ``engine.conversation.ConversationManager``(行動契約書 §3)。resolve が作った
  会話成立を招待として受け、話者に**会話ターン起床(不応期0)**を毎tick出す。終了はエンジン。

expedient(本モジュール分)
- δ_think は認知設計書 §1 のレーン表を分tickへ切り上げ(L1=**1 tick**=2.6秒の切り上げ)。
  既存定数 ``DELTA_THINK_TICKS=1`` と同値。①(応答適用)が④(LLM呼)より前にあるため
  ``t_apply=tick`` と ``tick+1`` は同じ tick で適用される(親指示「L1=0 tick」との差分を報告済み)。
- プロンプトは既定で**本物の ``perception.renderer.Renderer``**(B0-B6)。``renderer="stub"``
  で ``StubRenderer``(``[a<agent>|c<cell>|t5<tick//5>|w<class>]``)へ落とせる(安いテスト用)。
- 世界内日時は暦の口(``engine.calendar.SimCalendar.datetime_of``)= ``start_sim_datetime +
  T × tick_seconds``。``start_sim_datetime`` を渡さないランは今までどおり ``DEFAULT_START_DATETIME +
  day_index 日``(気象の再生実日があればその日)。manifest に ``tick_seconds``・``start_sim_datetime`` を書く(10a)。
- **通しの時刻 T**(10a・A1): ループの変数 ``tick`` は ``T = 日 × 1 日の tick 数 + 日の中の tick``。乱数とハッシュの
  鍵・call_id・テープの tick 欄・tick を値に持つ状態は T を使い、日の中の時刻で引く表(計画境界・食事の予定など)は
  ``T % 1 日の tick 数`` で引く。1 日のラン(既定)では T = tick なので値は今と同じ。
- 顕著行為(B4 の「顕著行為の到達」)は C3 では**常に空**(世界過程が C4)。流れも 0。
- 会話の招待は「resolve が ``会話`` を成立させた対」を入口にする(契約書 §3 の順序
  「招待→応答判定」の応答判定を resolve の直後に置いた)。相手側の ``activity`` は
  resolve が変えないため、相手の離脱は ``cell`` 監視で検出する。
- 週の曜日は ``day_index``(既定 0=月曜)。週 7 日表は C4 の PlanSpec。10a からは曜日・土休・祝日を引く箇所は
  すべて暦の口を通す(``--calendar-weekday day_index`` が既定=今の値)。
- **応答の遅れ**(10a・A9): 既定 ``response_delay=1``=艦隊/再生の到着の受け取りを①(反映)の直前に置き、
  下限を ``max(t_apply, tick)`` にする=tick T に発射した呼は T+1 の①で反映される。``2`` は旧(受け取りは
  ④′・下限 ``tick + 1``=T+2)で、旧い実 LLM テープ(17 本)の再生のために残す。mock は同期で既に +1。
"""

from __future__ import annotations

import argparse
import time
import warnings
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Final, Mapping

import blake3 as _blake3
import numpy as np

import dataclasses

from shibuya.agents.population import Population, load_population, sample_population
from shibuya.agents.weekly import apply_to_mock_schedule, load_weekly
from shibuya.agents.schedule import synthesize
from shibuya.agents.state import (
    FOCUS_NONE,
    N_WAKE_CONDITIONS_ALL,
    WAKE_CONDITION_CLASS,
    Activity,
    AgentState,
    ResultCode,
    WakeCondition,
)
from shibuya.core.growth import GrowthReport, check_growth
from shibuya.core.hashing import apply_key_array, blake3_hex
from shibuya.core.types import DEFAULT_TICK_SECONDS, MINUTES_PER_SIM_DAY
from shibuya.engine import commit as C
from shibuya.engine import growth_decl as GD
from shibuya.engine import resolve as R
from shibuya.engine.activity import ActivityLayer, payload_of
from shibuya.engine.calendar import (
    DEFAULT_HOLIDAY_CSV,
    DEFAULT_WEEKDAY_MODE,
    WEEKDAY_MODES,
    SimCalendar,
    check_weekday_mode,
    load_holidays,
    parse_school_holidays,
    parse_start,
)
from shibuya.engine.intent import INTENT_MAX_TICKS, IntentLayer
from shibuya.engine.familiarity import FAMILIARITY_K, FAMILIARITY_MODES, FamiliarityLayer
from shibuya.engine.memory import MEMORY_MODES, MEMORY_N, RECALL_TAU, MemoryLayer
from shibuya.engine.wom import DEFAULT_WOM_SOURCE, WomExtractor, check_wom_source
from shibuya.engine.store_choice import StoreChoice
from shibuya.engine.store_choice import walk_m_per_tick as _walk_m_per_tick
from shibuya.engine.memory import STORE_RECALL_SCOPES
from shibuya.engine.relations import (
    REL_D,
    REL_INIT_DENSITIES,
    REL_K,
    REL_MODES,
    REL_ORIGINS,
    REL_TENURE_WEEKS,
    initial_edges as _rel_initial_edges,
    DEFAULT_REL_TENURE_HASH,
    REL_TAU_BY_TENURE_HASH,
    check_rel_tenure_hash,
)
from shibuya.engine.wom import hear as wom_hear
from shibuya.engine.store_memory import (
    DEFAULT_STORE_DECAY,
    STORE_MEMORY_MODES,
    STORE_MEMORY_N,
    check_store_decay,
    check_store_sigma,
)
from shibuya.engine.energy import (
    DEFAULT_ENERGY_RATE,
    EnergyLayer,
    EnergyModel,
    DEFAULT_HOME_MEAL,
    DEFAULT_MEAL_SLEEP_DEFER,
    HomeMeals,
    OutOfAreaMeals,
    check_energy_rate,
    check_home_meal,
    check_hunger_model,
    check_meal_sleep_defer,
    load_anchors,
)
from shibuya.engine.arbiter import (
    L4_LINE_PER_AGENT_DAY,
    Arbiter,
    WakeCandidates,
    call_budget_per_tick,
)
from shibuya.engine.change_detect import ChangeDetector
from shibuya.engine.chooser import (
    DEFAULT_CHOOSER,
    HABIT_P,
    RANK_TAU,
    check_chooser,
    make_chooser,
)
from shibuya.engine.classical import (
    DEFAULT_ACTIVITY_REGION,
    DEFAULT_CLASSICAL_SOCIAL,
    DEFAULT_MEAL_GATE,
    DEFAULT_POLICY,
    ActivityPrior,
    ClassicalPolicy,
    check_activity_region,
    check_classical_social,
    check_meal_gate,
    check_policy,
    load_activity_prior,
)
from shibuya.engine.conversation import ConversationManager
from shibuya.engine.geometry import (
    DEFAULT_GEOMETRY,
    DESIRED_SPEED_MAX_MS,
    DESIRED_SPEED_MIN_MS,
    GEOMETRY_MODES,
    EdgeGeometry,
    check_geometry,
)
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.processes.crowd import SEAT_AREA_M2
from shibuya.engine.processes.runner import WorldProcessRunner
from shibuya.engine.processes.salient import (
    ablation_name as _pnotice_ablation_name,
    check_d50_scale as _check_d50_scale,
)
from shibuya.engine.presence import DERIVE_RULES as PRESENCE_DERIVE_RULES
from shibuya.engine.presence import EXIT_MODES as PRESENCE_EXIT_MODES
from shibuya.engine.presence import PlanExecutor
from shibuya.engine.poi_target import (
    DEFAULT_POI_TARGET,
    MOVE_SEARCH_RADIUS_CELLS,
    TargetResolver,
    check_poi_target,
    move_resolution_summary,
    resolution_summary,
)
from shibuya.engine.llm_bridge import (
    DEFAULT_LANE,
    LLMBridge,
    PerceptionRendererAdapter,
    StubRenderer,
    delta_think_ticks,
)
from shibuya.engine.scheduler import DIAG_COLUMNS
from shibuya.engine.tape import Replay, TapeRow, TapeWriter, read_run_meta
from shibuya.llm.contract import TargetKind
from shibuya.llm.fleet import (
    Deferred as FleetDeferred,
    FleetBridge,
    FleetClient,
    LLMCall,
    split_system_user,
)
from shibuya.llm.mock import MockLLM
from shibuya.perception.channels import BudgetMode
from shibuya.perception.renderer import (
    DEFAULT_HUNGER_WORDS,
    check_hunger_words,
    DEFAULT_NEAR_ORDER,
    DEFAULT_NEAR_TIEBREAK,
    DEFAULT_START_DATETIME,
    NEAR_ORDERS,
    NEAR_TIEBREAKS,
    SIGNAGE_P_SEE_DEFAULT,
    check_near_order,
    check_near_tiebreak,
    PerceptionAssets,
    Renderer as PerceptionRenderer,
    check_signage_p_see,
    check_p_see_activity,
    P_SEE_ACTIVITY_KINDS,
)
from shibuya.perception.templates import (
    INTENT_MODES,
    VOCAB_VERSIONS,
    check_intent_mode,
    check_role_words,
    check_vocab_version,
)
from shibuya.world.assets import (
    AREA_SOURCES,
    DEFAULT_AREA_SOURCE,
    check_area_source,
    load_process_assets_or_synthetic,
    load_walkable_area_m2,
)
from shibuya.world.state import World, check_eatery_mode

__all__ = [
    "DIAG_RUN_COLUMNS",
    "DIAG_DAY_ROWS",
    "DELTA_THINK_TICKS",
    "Checkpoint",
    "RunResult",
    "run_salt_for",
    "run_day",
    "add_fleet_args",
    "fleet_from_args",
    "main",
]

#: δ_think(分tickへ切り上げ後)。既定レーン L1=2.6 秒 → 1 tick(認知設計書 §1)。
DELTA_THINK_TICKS: Final[int] = delta_think_ticks(DEFAULT_LANE, DEFAULT_TICK_SECONDS)

#: ``action_usage`` で ``ENGINE_STEP``(−1)に付ける名(行動語ではない=括弧つき)。
ENGINE_STEP_LABEL: Final[str] = "(エンジン継続)"

#: 診断表の列(``DIAG_COLUMNS`` の 4 列 + 運用列)。
#: 艦隊の順序制御グループ「時間帯」の刻み[tick](知覚契約書 §2.4 ⑨「時刻表記は5分丸め」)。
#: 同一(セル, 5分帯)の呼は同時に発射し、同一 GPU に寄せない(実装計画書 §7・BN-4)。
TIME_BUCKET_TICKS: Final[int] = 5

DIAG_RUN_COLUMNS: Final[tuple[str, ...]] = (
    "tick",
    *DIAG_COLUMNS,
    "merged",
    "candidates",
    "calls",
    "pending_wakes",
    "pending_apply",
    "intents",
    "conflicts",
    "unresolved",
    "moved",
    "arrived",
    "purchases",
    "conversations",
    "reflections",
    "undefined_actions",
    "parse_errors",
    "tape_misses",
    "conversations_opened",
    #: D-56 就寝抑止(``suppressed``=不応期 とは**別列**)。
    "sleep_suppressed",
    #: D-66 域外抑止(舞台に居ない体を呼ばない。上の 2 列とも**排他**)。
    "outside_suppressed",
)

#: 診断行「シミュ日あたり」の必須行(§9.1 C3 受け入れ「診断行5本」+ 運用列)。
DIAG_DAY_ROWS: Final[tuple[str, ...]] = (
    *DIAG_COLUMNS,  # 繰り延べ / 昇格 / 縮退 / 抑止
    "parse_error_rate",
    "undefined_action_count",
    "tape_miss_count",
    "conversation_sessions",
)


#: 5b 層の記録の起床入口(``engine.run`` の診断と同じ 6 つ)。
_ENTRANCES: Final[tuple[str, ...]] = ("場所", "体", "日課", "会話", "満了", "社会")
_ENTRANCE_PLAN: Final[int] = 2
_ENTRANCE_EXPIRY: Final[int] = 4
#: 起床条件 → 起床入口の索引。
_ENTRANCE_OF_CONDITION: Final[np.ndarray] = np.array(
    [
        {
            "CELL_BLOCK": 0, "INTEROCEPTION": 1,
            "PLAN_SLEEPING": 2, "PLAN_WORKING": 2, "PLAN_GENERAL": 2, "PLAN_TRANSIT": 2,
            "CONVERSATION_TURN": 3, "ACTIVITY_EXPIRY": 4,
        }.get(WakeCondition(i).name, 5)
        for i in range(N_WAKE_CONDITIONS_ALL)
    ],
    dtype=np.int64,
)
#: 層の名(SOFAI 形式の記録の鍵)。
DECISION_LAYERS: Final[tuple[str, ...]] = ("system1", "system1_5", "system2")


#: C10 8b(R13): 会話クラス(会話ターン起床)の呼の割合の監査線(宣言=超えたら記録・絞らない=D-110)。
L4_CONVERSATION_SHARE_LINE: Final[float] = 0.15


#: 応答の遅れの切替口(10a・A9)。1=新(既定・発射 +1 tick で反映)/ 2=旧(+2 tick・旧テープの再生用)。
RESPONSE_DELAYS: Final[tuple[int, ...]] = (1, 2)
DEFAULT_RESPONSE_DELAY: Final[int] = 1


def check_response_delay(value: int) -> int:
    """``--response-delay`` の値を検査して返す。"""
    v = int(value)
    if v not in RESPONSE_DELAYS:
        raise ValueError(f"response_delay は {RESPONSE_DELAYS} のどれか(いま {value!r})")
    return v


class ResponseDelayWarning(UserWarning):
    """再生するテープに応答の遅れの値が無い(10a より前の録画)ときの警告。"""


#: 「値が無いので 2 とみなす」の警告を出したテープ(1 回だけ出すため)。
_WARNED_DELAY: set[str] = set()


def _resolve_response_delay(value: int | None, mode: str, replay: Any) -> int:
    """応答の遅れの値を決める(検収後 P3)。

    - 録画・mock: 渡された値(``None`` は既定 1)。
    - 再生: テープの脇の meta(``run_meta.json``)の ``response_delay`` と突き合わせ、違えば止める
      (文言に両方の値)。meta に値が無いテープ(10a より前の録画)は **2 とみなし**、警告を 1 回出す。
      このとき値を渡していなければ 2 で再生する(旧テープを既定のままで正しく回すため)。
    """
    given = value is not None
    v = check_response_delay(value if given else DEFAULT_RESPONSE_DELAY)
    if mode != "replay" or replay is None:
        return v
    if isinstance(replay, Replay):
        tape_dir = replay.tape.path
    else:
        tape_dir = getattr(replay, "path", None) or Path(replay)
    rec = read_run_meta(tape_dir).get("response_delay")
    if rec is None:
        key = str(tape_dir)
        if key not in _WARNED_DELAY:
            _WARNED_DELAY.add(key)
            warnings.warn(
                f"再生するテープに response_delay の記録が無い(10a より前の録画): 2 とみなす({Path(key).name})",
                ResponseDelayWarning, stacklevel=3,
            )
        rec = 2
        if not given:
            v = 2
    if int(rec) != v:
        raise ValueError(
            f"応答の遅れがテープと違う: テープは response_delay={int(rec)}・今の設定は {v}"
            "(--response-delay を録画と同じ値にする)"
        )
    return v


def decision_layers_summary(counts: np.ndarray) -> dict[str, Any]:
    """5b(L4 (a)): 時 × 層 × 起床入口 の判断数 → manifest の形(割合つき)。"""
    c = np.asarray(counts, dtype=np.int64)
    tot = c.sum(axis=(0, 2))
    all_ = int(tot.sum())
    by_hour = []
    for h in range(c.shape[0]):
        row = {DECISION_LAYERS[k]: int(c[h, k].sum()) for k in range(c.shape[1])}
        n = sum(row.values())
        row["share"] = {k: (round(v / n, 4) if n else 0.0) for k, v in list(row.items())}
        by_hour.append(row)
    return {
        "definition": "system1=engine executed a plan without a call (planned sleep, intent "
                      "arrival, presence arrival/departure); system1_5=call answered by the "
                      "classical policy; system2=call answered by LLM or mock",
        "entrances": list(_ENTRANCES),
        "totals": {DECISION_LAYERS[k]: int(tot[k]) for k in range(c.shape[1])},
        "share": {DECISION_LAYERS[k]: (round(int(tot[k]) / all_, 4) if all_ else 0.0)
                  for k in range(c.shape[1])},
        "by_entrance": {
            DECISION_LAYERS[k]: {e: int(c[:, k, j].sum()) for j, e in enumerate(_ENTRANCES)}
            for k in range(c.shape[1])
        },
        "by_hour": by_hour,
        "by_hour_layer_entrance": c.tolist(),
    }


def _count_intero_crossings(det: Any, agents: AgentState, acc: np.ndarray) -> None:
    """5 段目 5a(診断): この tick の内受容の跨ぎを 変数 × 上げ/下げ × 全体/起きて範囲内 で数える。

    ``apply_detection`` の**前**に呼ぶ(前回段=``<var>_stage`` がまだ書き戻されていない)。
    読むだけ=挙動に効かない。逐次ループ宣言: 内受容 3 変数ぶん(体数に比例しない)。
    """
    r = agents.registry
    for c in det.crossings:
        if not c.agent_id.size:
            continue
        ids = c.agent_id
        old = np.asarray(r.field(c.stage_field))[ids].astype(np.int16)
        up = np.asarray(c.new_stage).astype(np.int16) > old
        awake = (np.asarray(r.activity)[ids] != int(Activity.SLEEPING)) & (
            np.asarray(r.transit_state)[ids] == 0
        )
        acc[c.var, 0, 0] += int(np.count_nonzero(up))
        acc[c.var, 1, 0] += int(np.count_nonzero(~up))
        acc[c.var, 0, 1] += int(np.count_nonzero(up & awake))
        acc[c.var, 1, 1] += int(np.count_nonzero(~up & awake))


def _named_closed_lookup(
    resolver: Any, runner: Any, calendar: "SimCalendar | int", tick_seconds: int
) -> Callable[[int], tuple[int, int, int] | None]:
    """段 2c Q25: 体 → ``(POI, 即時閉店の tick, 次の開店の分)`` を引く関数(描画が読む)。

    開店の分=W7 の営業時間過程(``OpeningProcess``)の当日の行列で、失敗の分より後の最初の営業分。
    当日に無ければ翌日の W7 区間の最初の開始分。翌日の曜日の行は暦の口から引く(10a #8:
    失敗の通しの時刻 T の日番号 + 1 の ``table_weekday``。``day_index`` モードでは ``(day_index + 日 + 1) % 7``
    =1 日のランでは今の ``(day_index + 1) % 7`` と同じ)。W7 が無い(合成世界)・区間が無い店は
    ``-1``(時刻を出さない)。逐次ループ宣言: なし(引くのは描画 1 回につき 1 件)。
    ``calendar`` に整数を渡したときは旧い口(``day_index``)として ``SimCalendar.legacy`` で包む。
    """
    if not isinstance(calendar, SimCalendar):
        calendar = SimCalendar.legacy(int(calendar), tick_seconds=int(tick_seconds))
    opening = getattr(runner, "opening", None) if runner is not None else None
    om = getattr(opening, "open_matrix", None)
    pa = getattr(opening, "assets", None)

    def look(agent_id: int) -> tuple[int, int, int] | None:
        got = resolver.named_closed.get(int(agent_id))
        if got is None:
            return None
        poi, t = int(got[0]), int(got[1])
        nxt = -1
        if om is not None and om.size and 0 <= poi < om.shape[0]:
            minute = int(t * int(tick_seconds) // 60) % om.shape[1]
            later = np.flatnonzero(om[poi, minute + 1:])
            if later.size:
                nxt = minute + 1 + int(later[0])
            elif pa is not None and getattr(pa, "plan_poi", None) is not None:
                nxt_wd = calendar.table_weekday(calendar.day_of(t) + 1)  # 10a #8: 翌日の曜日の行
                sel = (np.asarray(pa.plan_poi) == poi) & (np.asarray(pa.plan_day) == int(nxt_wd))
                if bool(np.any(sel)):
                    nxt = int(np.asarray(pa.plan_start)[sel].min()) % 1_440
        return poi, t, nxt

    return look


def _default_mock(
    seed: int | str, vocab_version: str, move_target_p: float = 0.0,
    out_of_cell_target_p: float = 0.0,
) -> Any:
    """``llm`` を注入しないランの既定 mock(``MockLLM``)。**語彙版に語彙を合わせる**。

    ``MockLLM`` はプロンプト本文を読まない(=B0 に 13 語目を載せても出力は変わらない)ので、
    語彙 v2 のランで「食事」を 1 件も出せない。mock は**書式と決定論を通す配管**であって
    振る舞いのモデルではない(``llm.mock`` の expedient 節)から、**提示した語彙から一様に
    引く**という既存の規約をそのまま版に従わせる。既定 ``"v1"`` では
    ``MockLLM(master_seed=seed)`` と**同一**(引数も乱数列も同じ)。
    """
    from shibuya.llm.contract import cross_action_words

    if str(vocab_version) == VOCAB_VERSIONS[0]:
        return MockLLM(master_seed=seed)
    if str(vocab_version) == "v3":
        # 二層の段 3: 5 ラベル形(行為=11 語+なし の一様・活動・まで・あたり)=``llm.mock``
        # 段 2b: ``move_target_p`` > 0 で移動の対象にカテゴリ語/見えている名を出す(既定 0=不変)
        # 段 2c: ``out_of_cell_target_p`` > 0 で購入/食事/並ぶの対象に B2 に見える名を出す(既定 0=不変)
        return MockLLM(
            master_seed=seed, vocab=cross_action_words("v3"), form="v3",
            move_target_p=float(move_target_p),
            out_of_cell_target_p=float(out_of_cell_target_p),
        )
    return MockLLM(master_seed=seed, vocab=cross_action_words(vocab_version))


def _synonym_table_version(vocab_version: str) -> str:
    """語彙版 → 段0 辞書の版文字列(``llm.undefined`` の表が正典)。"""
    from shibuya.llm.undefined import synonym_table_version

    return synonym_table_version(str(vocab_version))


def _action_usage(per_action: Mapping[int, int], vocab_version: str) -> dict[str, int]:
    """``ResolveOutcome.per_action``(コード別)→ **行動語別**の件数(D-71 §3 J)。

    ``ENGINE_STEP``(−1・経路の1歩)は行動語ではないので ``"(エンジン継続)"`` の名で残す
    (落とすと合計が ``n_confirmed`` と合わなくなる)。並びは**契約表の順**に固定する
    (dict の挿入順=再実行でバイト一致)。

    逐次ループ宣言(P4): 行動語ぶん(v1=13 / v2=14)。個体数にも tick 数にも比例しない。
    """
    from shibuya.engine.llm_bridge import ACTION_WORD_BY_CODE

    out: dict[str, int] = {}
    order = R._ACTION_ORDER_BY_VOCAB[check_vocab_version(vocab_version)]
    for code in order:
        n = int(per_action.get(int(code), 0))
        if not n:
            continue
        out[ACTION_WORD_BY_CODE.get(int(code), ENGINE_STEP_LABEL)] = n
    for code, n in sorted(per_action.items()):  # 表に無いコード(将来の語)も落とさない
        if int(code) not in order and int(n):
            out[ACTION_WORD_BY_CODE.get(int(code), f"({int(code)})")] = int(n)
    return out


def run_salt_for(master_seed: int | str) -> bytes:
    """``blake3(master_seed ‖ 0x1f ‖ "engine")`` の先頭 16 バイト(親の指定)。"""
    text = f"i:{int(master_seed)}" if not isinstance(master_seed, str) else f"s:{master_seed}"
    return _blake3.blake3(f"{text}\x1fengine".encode("utf-8")).digest(length=16)


@dataclass(frozen=True)
class Checkpoint:
    """checkpoint 1 点の状態ハッシュ(T1/T2 の一致判定)。"""

    tick: int
    agents_hash: str
    world_hash: str
    #: W16 母集団の同定ハッシュ(母集団なしのランは ``""``)。T1/T2 の一致判定に混ぜる。
    population_hash: str = ""
    #: W17 週次表の同定ハッシュ(週次表なしのランは ``""``)。版の取り違え検出用。
    schedule_hash: str = ""
    #: **活動層**(二層の段 2)の Python 側状態(活動の文・「まで」の型)のハッシュ。
    #: 活動層の無いラン(v1/v2・``--activity off``)は ``""`` で ``combined`` に**混ぜない**
    #: =既定の checkpoint は 1 バイトも動かない。
    activity_hash: str = ""

    @property
    def combined(self) -> str:
        parts = [self.agents_hash, self.world_hash, self.population_hash, self.schedule_hash]
        if self.activity_hash:
            parts.append(self.activity_hash)
        return blake3_hex("\x1f".join(parts).encode("utf-8"))


@dataclass
class RunResult:
    """1 ランの結果。"""

    n_agents: int
    n_cells: int
    seed: int | str
    ticks: int
    world_source: str
    checkpoints: list[Checkpoint] = field(default_factory=list)
    diagnostics: np.ndarray = field(default_factory=lambda: np.zeros((0, len(DIAG_RUN_COLUMNS)), dtype=np.int64))
    phase_seconds: dict[str, float] = field(default_factory=dict)
    wall_seconds: float = 0.0
    llm_calls: int = 0
    #: 世界内時刻の**時**別の発射数(24 要素・D-56 の検証欄)。Σ = ``llm_calls``。
    #: 時 = ``(tick // 60) % 24``(開始 00:00=テープ meta の ``start_hour`` と同じ約束)。
    calls_by_hour: list[int] = field(default_factory=lambda: [0] * 24)
    arbiter_counters: dict[str, Any] = field(default_factory=dict)
    money_start: int = 0
    money_end: int = 0
    revenue_end: int = 0
    min_stock: int = 0
    growth_report: GrowthReport | None = None
    growth_measured: dict[str, int] = field(default_factory=dict)
    #: ``engine.llm_bridge.LLMBridge.counters()``(書式エラー率・テープ外率・未定義行動)。
    bridge_counters: dict[str, float] = field(default_factory=dict)
    #: ``engine.conversation.ConversationManager.counters()``(会話セッションの開閉)。
    conversation_counters: dict[str, int] = field(default_factory=dict)
    #: 知覚レンダラの診断(キャッシュ命中率・グループ別平均トークン・切り詰め数)。
    renderer_counters: dict[str, float] = field(default_factory=dict)
    #: 使ったレンダラの名前(``perception.Renderer`` / ``StubRenderer`` / 注入クラス名)。
    renderer_name: str = ""
    #: 知覚のトークン配分(知覚契約書 §3.2 の義務 ablation ①)。``fixed_slots`` / ``single_ranking``。
    budget_mode: str = BudgetMode.FIXED_SLOTS.value
    #: **L4 呼数予算の倍率**(PENDING D-99 (a)・腕 AB8-L4-SCALE)。``1.0``=予算宣言表 L4 の
    #: とおり(400 万呼/日を体数按分=既定・現行のバイト)/``0.5``・``2.0``=半分・倍/
    #: ``0.0``=**無制限**(1 tick の上限を体数に置く=起床候補は合流後に高々 1 件/体なので
    #: 繰り延べが起きない)。``budget`` を直に渡したランでは倍率は 1.0 のまま。
    l4_scale: float = 1.0
    #: このランで**実際に使った** 1 tick の呼数上限(``Arbiter.budget``)。既定のランでは
    #: ``arbiter.call_budget_per_tick(n_agents)``(5,000 体で 34.72)。
    budget_per_tick: float = 0.0
    #: 3 段目(D-99 (a′)・D-110): L4 の監査の注記(例: 艦隊×無制限で受理待ち枠が未指定=D-55)。
    l4_notes: list[str] = field(default_factory=list)
    #: 1 tick の秒数(呼/体/日の日数換算に使う)。
    tick_seconds: int = DEFAULT_TICK_SECONDS
    #: p_notice の ablation(§3.1 A0-A4)。既定 ``A4``=完成形。
    p_notice_ablation: str = "A4"
    #: ablation ②(§8 第1陣)。``p_notice`` の d50 の倍率。既定 1.0=§3.1 の 40 m。
    p_notice_d50_scale: float = 1.0
    #: ablation ③(§8 第1陣)。§6 不応期表の倍率 ``{条件名: 倍率}``。既定 {}=表どおり。
    refractory_scale: dict[str, float] = field(default_factory=dict)
    #: ablation ⑥(§8 第1陣)。看板・広告面(B2.signage)を描いたか。既定 True。
    signage: bool = True
    #: **看板の注視ゲート**(知覚契約書 §4 段1 の p_see・D-59 (b)・腕 AB6b-AD-NOTICE)。
    #: 既定 1.0=在圏セルの看板行が必ず観測に入る(=現行のバイト)。
    signage_p_see: float = SIGNAGE_P_SEE_DEFAULT
    #: **AB7 自由意図の腕**。``"vocab"``=24 語提示(既定)/``"open"``=自由文/
    #: ``"hint"``=語彙を例として見せつつ自由文も許す(AB7b)。
    #: 仕様書 docs/design/v2-open-intent-arm-spec.md §2。
    intent_mode: str = INTENT_MODES[0]
    #: **行動語彙の版**(D-71 §3 F・2026-09-17 ユーザー決定)。``"v1"``=現行 24 語(既定)/
    #: ``"v2"``=24 語 + 横断語「食事」(飲食店オブジェクトの affordance)。
    vocab_version: str = VOCAB_VERSIONS[0]
    #: **D-113 ④(第269)** B0 の末尾に役割語 12 語の 1 行を足したか(既定 True)。False は
    #: 第268 以前の B0(テープ再生用・帰無腕)。
    role_words: bool = True
    #: **行為と活動の二層**(段 2・D-116)の活動層が立ったか(= ``vocab_version="v3"`` かつ
    #: ``activity=True``)。v1/v2 では常に False(活動欄が来ない=実質無効)。
    activity: bool = False
    #: **飲食店の切替口**(段 1b・D-96 nightlife (b))。``food``=現行(既定)/``place_food``=
    #: W17 の場所語「飲食店」と同じ集合(``World.eatery_mask``)。
    eatery: str = "food"
    #: **選び手**(段 2a・D-114 (a)・``engine.chooser``)。既定 ``nearest``(憲法⑥の宣言つき暫定)。
    chooser: str = DEFAULT_CHOOSER
    #: 購入/食事/並ぶの対象の決め方(段 2a・親決定 Q13)。``candidates``=候補 → 選び手(既定)/
    #: ``legacy``=現在セルの最小 id(旧 checkpoint の再現)。
    poi_target: str = DEFAULT_POI_TARGET
    #: 購入/食事/並ぶの対象の解決の内訳(段 2a・``engine.poi_target.resolution_summary``)。
    #: ``legacy`` のランは空 dict(数えない)。
    #: 段 2b: 移動の行き先の解決の内訳(``engine.poi_target.move_resolution_summary``)。
    move_resolution: dict[str, Any] = field(default_factory=dict)
    #: 段 2b: カテゴリ語の近傍探索で見る近いセルの数(``--move-search-radius``)。
    move_search_radius: int = MOVE_SEARCH_RADIUS_CELLS
    #: 段 2b: mock の移動の対象にセル ID/カテゴリ語/見えている名を出す確率(既定 0=不変)。
    mock_move_target_p: float = 0.0
    #: 段 2c: 意図の保持の計数(``engine.intent.intent_summary``)。層が無いランは空 dict。
    intent: dict[str, Any] = field(default_factory=dict)
    #: 段 2c: 意図の上限[tick](``--intent-max-ticks``・宣言 60・感度腕 30/120)。
    intent_max_ticks: int = INTENT_MAX_TICKS
    #: 段 2c: mock の購入/食事/並ぶの対象に B2 に見える名を出す確率(既定 0)。
    mock_out_of_cell_target_p: float = 0.0
    #: 4 段目(M13+M17): 親しみの表を確保したか(``--familiarity on``)・行数 K・要約。
    familiarity: bool = False
    familiarity_k: int = FAMILIARITY_K
    familiarity_summary: dict[str, Any] = field(default_factory=dict)
    #: 5 段目 5a(D-118): 空腹のモデル(``v1``=旧規則 / ``energy``=エネルギー収支)・消費の式・要約。
    hunger_model: str = "v1"
    energy_rate: str = ""
    energy: dict[str, Any] = field(default_factory=dict)
    #: 第2波 §2B(食事の束・既定は旧): 項 1 就寝中の既定の食事・項 2 自宅の食事行・項 3 B5 の空腹の語。
    meal_sleep_defer: str = DEFAULT_MEAL_SLEEP_DEFER
    home_meal: str = DEFAULT_HOME_MEAL
    hunger_words: str = "hungry"
    #: 5 段目 5b(D-119): 方策(``mock``/``classical``)・方策の要約・選び手の計数・層の記録(SOFAI 形式)。
    policy: str = DEFAULT_POLICY
    classical: dict[str, Any] = field(default_factory=dict)
    chooser_stats: dict[str, Any] = field(default_factory=dict)
    decision_layers: dict[str, Any] = field(default_factory=dict)
    #: 5 段目 5c(D-117): 看板の注視 p_see の活動の種別の乗数表・活動の種別ごとの計数・実効 p_see の分布。
    p_see_activity: dict[str, Any] = field(default_factory=dict)
    #: 6 段目 6a(記憶 第 1 段の記録): 表を確保したか(``--memory on``)・行数 N・要約。
    memory: bool = False
    memory_n: int = MEMORY_N
    memory_summary: dict[str, Any] = field(default_factory=dict)
    #: D-120 7a(店の評価の記憶): 表を確保したか(``--store-memory on``)・要約(行数 M・σ・減衰の形を含む)。
    store_memory: bool = False
    store_memory_summary: dict[str, Any] = field(default_factory=dict)
    #: D-120 7b(会話からの抽出): 発話・抽出・向き・照合できない語・照合できた店の上位(店の記憶 on のランだけ)。
    wom: dict[str, Any] = field(default_factory=dict)
    #: D-120 7c(想起優先の候補合成・決め手・初回率・店頭の割合・腕の切替口の値)。店の記憶 on のランだけ。
    store_choice: dict[str, Any] = field(default_factory=dict)
    #: C10 8a(関係辺): 辺/体・種別・符号・A/P・τ で落ちた辺・押し出し・初期網の監査。関係 on のランだけ。
    relations: dict[str, Any] = field(default_factory=dict)
    #: 5 段目 5a(診断): 内受容の段の跨ぎの延べ(変数 × 上げ/下げ × 全体/起きて範囲内)。
    #: 起床入口「体の状態」の内訳を空腹と疲労・体感温度に分けて読むため(挙動には効かない)。
    intero_crossings: dict[str, int] = field(default_factory=dict)
    #: 段 2b: 移動の失敗の内訳(``resolve._apply_move``)。
    move_bad_target: int = 0
    move_unreachable: int = 0
    target_resolution: dict[str, Any] = field(default_factory=dict)
    #: 活動層の計数(``engine.activity.ActivityLayer.counters``)。層が無いランは空 dict。
    activity_counters: dict[str, int] = field(default_factory=dict)
    #: 活動の種別ごとの設定件数(``ActivityLayer.kind_distribution``)。層が無いランは空 dict。
    activity_kind_counts: dict[str, int] = field(default_factory=dict)
    #: **発射した呼**の起床条件ごとの件数(``WakeCondition`` の名 → 件数・満了入口
    #: ``ACTIVITY_EXPIRY`` の列を含む=起床の内訳)。
    calls_by_condition: dict[str, int] = field(default_factory=dict)
    #: 語彙 v2「食事」が成立した件数(v1 のランでは常に 0)。
    meals: int = 0
    #: 食事で店舗へ移った金額[円](売上の内数)。
    meal_yen: int = 0
    #: **解決後の行動語ごとの件数**(D-71 §3 J「語ごとの使用率」の分子)。
    #: 鍵は行動語(``ENGINE_STEP`` は ``"(エンジン継続)"``)・値は ``resolve`` が適用した件数。
    action_usage: dict[str, int] = field(default_factory=dict)
    #: D-56 就寝抑止を効かせたか。既定 True(ユーザー決定 (a)・2026-09-10)。
    sleep_suppression: bool = True
    #: D-62「就寝は計画の実行」を効かせたか。既定 True(ユーザー決定 (a)+(b)・2026-09-10)。
    plan_sleep: bool = True
    #: D-66 計画実行層(``engine.presence``)が**実際に立ったか**(W16+W17 のあるランだけ)。
    plan_executor: bool = False
    #: 退出の実行形(設計書 §10-3)。第1段は ``immediate`` のみ実装。
    exit_mode: str = "immediate"
    #: 出勤率(D-67 (b)・expedient E6)。既定 1.0=全員来る。
    attendance_rate: float = 1.0
    #: 在圏ブロックの読み口(``engine.presence.DERIVE_RULES``・既定 v2)。
    derive_rule: str = "v2"
    #: **C9 位置幾何の腕**(G1・2026-09-17 ユーザー決定)。``"node"``=現行の 1 tick=1 ノード
    #: (既定・バイト不変)/``"edge"``=辺上の連続位置+希望速度 1.00〜1.60 m/s+Kladek 減速。
    geometry: str = DEFAULT_GEOMETRY
    #: edge 幾何の診断(ホップ反復の延べ回数=P4 実測・詰め込み密度で歩けなかった延べ体数)。
    #: node では 0。
    geometry_hops: int = 0
    geometry_jammed: int = 0
    #: **C9c-1 歩行可能面積の出所**(G8 (b)・D-84 (c))。``"legacy"``=街路点 × 6.25 m²
    #: (既定・バイト不変)/``"plateau"``=PLATEAU 歩道部 + OSM × 道路構造令の実測値。
    area_source: str = DEFAULT_AREA_SOURCE
    #: 歩行可能面積[m²]の要約(実測に切り替えたランの診断。legacy でも埋まる)。
    walkable_area_median_m2: float = 0.0
    walkable_area_min_m2: float = 0.0
    #: **1 人あたり床面積の感度腕**(``None``=現行の ``crowd.SEAT_AREA_M2`` のまま)。
    seat_area_eatery_m2: float | None = None
    seat_area_retail_m2: float | None = None
    #: **C9b 対象と注意**(G3/G4/G7)が立ったか(= ``geometry="edge"`` かつ
    #: ``vocab_version="v2"``)。False のランでは下の 6 本は 0 のまま。
    attention: bool = False
    #: 「近づく」が立った件数 / 対象に届いた件数 / 着いたのに居なかった件数(``TARGET_GONE``)。
    n_approach: int = 0
    n_approach_done: int = 0
    n_target_gone: int = 0
    #: 注意の焦点を取得した件数 / 消えた件数(寿命切れ+喪失距離)。
    n_focus: int = 0
    n_focus_lost: int = 0
    #: **実距離**で成立した会話招待の件数(G7)。
    n_talk_by_distance: int = 0
    #: D-113 ②: 通報の前提検査(成立 / 知覚済みの事象なしで失敗)。
    n_report_ok: int = 0
    n_report_no_event: int = 0
    #: D-113 ③: 満席の列から席へ入れた件数 / 閉店で列を解散した件数。
    n_served_from_queue: int = 0
    n_queue_closed: int = 0
    #: 計画実行層の診断(``PlanExecutor.counters()``)。層が休んだランは空 dict。
    presence_counters: dict[str, float] = field(default_factory=dict)
    #: 9a(D-115 ①): 退出の形・内訳・所要時間・出口セルの時別在圏(``PlanExecutor.exit_summary()``)。
    presence_exit: dict[str, Any] = field(default_factory=dict)
    #: 9a(D-112 ④): 退去の効果=所属解除の件数(退去・在店を解いた・列を離れた・会話を閉じた)。
    leave_effects: dict[str, int] = field(default_factory=dict)
    #: 小さいもの①(第300 Q107): B5 近接行の距離の同点の切り方と、撹拌で切った描画の数(列追加のみ)。
    near_tiebreak: dict[str, Any] = field(default_factory=dict)
    #: 第308 D-107 (a): 群・規範の計器(同行・文脈別エントロピー・役割語/NO_PERMISSION・伝播到達=読むだけ)。
    group_norms: dict[str, Any] = field(default_factory=dict)
    #: D-66 域外抑止を効かせたか(既定 True)。False = **帰無腕**。
    outside_suppression: bool = True
    #: **発射した呼**のうち域外(``transit_state != 0``)の体宛てだった延べ数。
    #: 抑止が効いていれば 0(監査点)。
    outside_wake_candidates: int = 0
    #: 計画実行層の要約 1 行(``c7lib.parse_run_summary`` に当たらない書式)。
    presence_summary: str = ""
    #: **在圏の体だけ**で測った「起きている割合」/時(24 要素・D-66 の補助欄)。
    #: ``wake_rate_by_hour`` は D-62 の定義で**域外滞在・乗車中も「起きている」に数える**ので、
    #: 層が入って深夜の 9 割が域外に居るランではその欄が自動的に上がる。a(h)(社会生活基本調査)
    #: と並べるならこちらが分母の揃った値。層が休んだランは空(``[]``)。
    wake_rate_in_area_by_hour: list[float] = field(default_factory=list)
    #: 世界内時刻の**時**別の「起きている割合」(24 要素・D-62 の検証欄)。
    #: 各 tick の ``activity != SLEEPING`` の割合を、その時の 60 tick で平均した値。
    wake_rate_by_hour: list[float] = field(default_factory=lambda: [0.0] * 24)
    #: D-62 の計数(``resolve.begin_planned_sleep`` の内訳 ``slept``/``walking``/``riding``/
    #: ``outside``/``conversing``/``asleep``/``unreachable`` + ``arrived``(就寝地へ着いて寝た)+
    #: ``woke``(非就寝の計画境界で起こした))。``plan_sleep=False`` のランは空 dict。
    planned_sleep_counts: dict[str, int] = field(default_factory=dict)
    #: 凍結静的文の版(W14/W15 の parquet: ファイル名→sha256)。凍結文なしのランは空(層2 指摘 09-09)。
    frozen_sources: dict[str, str] = field(default_factory=dict)
    #: 録画テープの置き場(記録したときだけ)。
    tape_path: str = ""
    #: ``record`` / ``replay``。
    mode: str = "record"
    # ---- C4: 世界過程(第1陣) ----
    #: 世界側台帳の blake3(manifest の同定欄・``WorldRegistry.registry_hash``)。
    registry_hash: str = ""
    #: 憲法5(D-R2-4)のビルド時検査を通ったか。
    constitution_ok: bool = False
    #: 気象の再生実日(D-W15 実日ブートストラップ)。世界過程が無ければ空。
    replay_date: str = ""
    #: 過程別の壁時計[秒]。
    process_seconds: dict[str, float] = field(default_factory=dict)
    #: 過程別の診断カウンタ(``<過程>.<欄>``)。
    process_counters: dict[str, float] = field(default_factory=dict)
    #: 支払われた運賃の合計[円](世帯→外界の sink)。
    fares_paid: int = 0
    #: 乗車・降車・待ち行列の件数。
    n_boarded: int = 0
    n_alighted: int = 0
    n_queued: int = 0
    #: 乗車待ち(D-51): ホームに立った延べ人数と、列車が来ずに打ち切った件数。
    n_board_waiting: int = 0
    n_board_timeout: int = 0
    #: PlanSpec の遵守率(``ActualLog`` の SCHEDULED 率)。
    compliance_rate: float = float("nan")
    #: ``ActualLog`` の追記総件数。
    actual_log_rows: int = 0
    # ---- C4 後半 ----
    #: 日次センサスの 1 行(``economy.census.daily_census``。注入されたときだけ埋まる)。
    #: **締めた日の実数**(faucet/sink/廃棄は締める前の当日値)。
    census_row: dict[str, Any] = field(default_factory=dict)
    #: ``census_row`` が指す日(``LedgerBundle.end_of_day`` で畳んだ日)。-1=台帳なし。
    day_closed: int = -1
    #: 日次ゲートの合否(§2.4「残差>閾値・純資産≠実物資産はゲート失敗」)。**例外にしない**。
    census_pass: bool = False
    #: ``census_out`` を渡したランが書いたファイル(日次センサス・月次 MER)。既定は空
    #: =**何も書いていない**。run manifest には**載せない**(既定経路のバイトを動かさない)。
    census_paths: tuple[str, ...] = ()
    #: T3(SFC の冗長方程式の検算・D-85 (a))の合否。``None``=**未実行**
    #: (月次センサスが立たなかったラン=1 日ランなど・台帳の無いラン)。manifest に出る。
    t3_ok: bool | None = None
    #: T3 の内訳(3検査の合否と残差の大きさ・``economy.checks.T3Check.as_dict``)。
    #: 未実行なら空 dict。manifest には合否(``t3_ok``)だけを載せる。
    t3_report: dict[str, Any] = field(default_factory=dict)
    #: 顕著行為(人物③)の件数と、``p_notice`` で気づいた延べ人数。
    salient_events: int = 0
    noticed: int = 0
    #: 公共サービスの出動件数。
    dispatches: int = 0
    #: 補充・納品・宅配・バス到着・ホテル泊の件数(受入報告の数値欄)。
    restocks: int = 0
    deliveries: int = 0
    parcels: int = 0
    bus_arrivals: int = 0
    hotel_checkins: int = 0
    #: その日の廃棄 sink[t/日](物の台帳 + 街路清掃)と W1 band。
    waste_tonnes_per_day: float = 0.0
    #: 第304 Q135 (a): **店だけの静的な帯**(店舗の期限切れ在庫の静的期待 ±30%)。旧=区の総排出量 119.6 t/日 ±30%。
    waste_band: tuple[float, float] = (0.0, 0.0)
    #: 第304 Q135: 廃棄 sink の内訳 3 つ(店・世帯の消費・街路)と帯の出所(``runner.waste_sink_report``・報告だけ)。
    waste_sink: dict[str, Any] = field(default_factory=dict)
    # ---- C6-a 実艦隊 ----
    #: ``llm.fleet.FleetConfig.manifest_fields()``(``cache_salt``・``prefix_caching_hash_algo``・
    #: ルーティング規則・in-flight 上限)。**ランが導出して押す**(親決定 09-09)。
    fleet_fields: dict[str, Any] = field(default_factory=dict)
    #: ラン終端の ``drain`` で拾った件数(=最後の tick 以降に届いた応答)。
    fleet_drained_at_end: int = 0
    #: ラン終端でも答えが返らなかった呼(**次ランへ持ち越す=破棄しない**の監査点)。
    fleet_unanswered_at_end: int = 0
    # ---- 10a: 通しの時刻 T・暦の口・応答の遅れ ----
    #: 暦の欄(``SimCalendar.manifest_fields``: 開始日・曜日の決め方・祝日 CSV の場所と md5・学校の休み・日ごとの暦)
    #: と開始日の検査の警告(``start_check``)。manifest の ``calendar`` に載る。
    calendar_fields: dict[str, Any] = field(default_factory=dict)
    #: 応答の遅れの切替口(``RESPONSE_DELAYS``・既定 1)。manifest に載る。
    response_delay: int = DEFAULT_RESPONSE_DELAY
    #: 回した日数(``run_day(sim_days=…)``・既定 1)。
    sim_days: int = 1

    # ---- 便利参照 ----
    def column(self, name: str) -> np.ndarray:
        return self.diagnostics[:, DIAG_RUN_COLUMNS.index(name)]

    @property
    def parse_error_rate(self) -> float:
        """**実効**書式エラー率(``format_ok`` が偽だった呼の割合)。MockLLM なら 0.0。

        C6(09-09)で ``llm.parser`` にラベル別名(「目的地:」「目的:」等)の許容が入った。
        本欄は**別名を許容した後**の率=世界に実際に届いた intent の書式健全性。
        受入指標の定義を動かさない側は ``parse_error_rate_strict``。
        """
        calls = int(self.column("calls").sum()) if self.diagnostics.size else 0
        errs = int(self.column("parse_errors").sum()) if self.diagnostics.size else 0
        return (errs / calls) if calls else 0.0

    @property
    def parse_error_rate_strict(self) -> float:
        """**厳密**書式エラー率(C6 以前の別名表だけで見た判定=B11 と同じ物差し)。

        知覚契約書 §2 卒業条件表の「書式エラー率 ≤0.10」は**この物差しで定義された**ので、
        受入判定は実効を主・厳密を併記で読む(親判断 D-28・PENDING)。
        """
        c = self.bridge_counters
        return float(c.get("parse_error_rate_strict", c.get("parse_error_rate", 0.0)))

    @property
    def label_alias_rate(self) -> float:
        """C6 ラベル別名で読めた応答の割合(別名許容が実際に効いた量)。"""
        return float(self.bridge_counters.get("label_alias_rate", 0.0)) or float(
            self.bridge_counters.get("fleet_label_alias_rate", 0.0)
        )

    @property
    def positional_rate(self) -> float:
        """ラベルを省いた並びを**位置**で読んだ応答の割合(``positional_used``)。"""
        return float(self.bridge_counters.get("positional_rate", 0.0)) or float(
            self.bridge_counters.get("fleet_positional_rate", 0.0)
        )

    @property
    def dictionary_mapped_rate(self) -> float:
        """語彙外の行動語を §7 段0 の辞書写像で救えた割合。"""
        return float(self.bridge_counters.get("dictionary_mapped_rate", 0.0)) or float(
            self.bridge_counters.get("fleet_dictionary_mapped_rate", 0.0)
        )

    @property
    def tape_miss_count(self) -> int:
        return int(self.column("tape_misses").sum()) if self.diagnostics.size else 0

    @property
    def undefined_action_count(self) -> int:
        return int(self.column("undefined_actions").sum()) if self.diagnostics.size else 0

    @property
    def conversation_sessions(self) -> int:
        return int(self.column("conversations_opened").sum()) if self.diagnostics.size else 0

    @property
    def sleep_suppressed_count(self) -> int:
        """就寝抑止(D-56)で落とした候補の総数。"""
        if not self.diagnostics.size or "sleep_suppressed" not in DIAG_RUN_COLUMNS:
            return 0
        return int(self.column("sleep_suppressed").sum())

    @property
    def outside_suppressed_count(self) -> int:
        """域外抑止(D-66)で落とした候補の総数。"""
        if not self.diagnostics.size or "outside_suppressed" not in DIAG_RUN_COLUMNS:
            return 0
        return int(self.column("outside_suppressed").sum())

    def calls_by_hour_text(self) -> str:
        """``呼/時`` の 1 行(24 個・D-56 の検証欄)。

        受入(``tools/c7``)は深夜 0〜5 時の合計/昼 12〜19 時の合計を取り、東京都の
        起床率 a(h)(0 時 20.5% … 3 時 3.5% … 12〜19 時 97.8〜98.9%)と並べる。
        """
        cb = list(self.calls_by_hour) + [0] * max(0, 24 - len(self.calls_by_hour))
        return "呼/時 " + " ".join(f"{h:02d}:{int(cb[h])}" for h in range(24))

    def wake_rate_in_area_by_hour_text(self) -> str:
        """``起床率(在圏)/時 00:0.xxx …``(D-66 の補助欄・**在圏の体の非就寝率**)。"""
        return "起床率(在圏)/時 " + " ".join(
            f"{h:02d}:{self.wake_rate_in_area_by_hour[h]:.3f}" for h in range(24)
        )

    def wake_rate_by_hour_text(self) -> str:
        """``起床率/時`` の 1 行(24 個・**D-62 の検証欄**)。

        「起床率」= その時の各 tick の ``activity != Activity.SLEEPING`` の割合の平均
        (域外滞在・乗車中も「起きている」に数える=在圏かどうかとは別の量)。
        東京都 平日の a(h)(令和 3 年社会生活基本調査 第 4-1 表)は
        0 時 **20.5%** / 1 時 11.1 / 2 時 5.7 / 3 時 **3.5** / 4 時 5.3 / 5 時 15.3 / 6 時 40.7 /
        12〜19 時 **97.8〜98.9** で、**一律に掛けない**(交替制勤務 12.9%)——ここは
        照合の材料であって目標値ではない(D-56 の注記と同じ扱い)。
        """
        wr = list(self.wake_rate_by_hour) + [0.0] * max(0, 24 - len(self.wake_rate_by_hour))
        return "起床率/時 " + " ".join(f"{h:02d}:{float(wr[h]):.3f}" for h in range(24))

    def diagnostics_day(self) -> dict[str, float]:
        """シミュ日あたりの診断行(``DIAG_DAY_ROWS`` を必ず全て含む)。"""
        out: dict[str, float] = {
            col: float(self.column(col).sum()) if self.diagnostics.size else 0.0
            for col in DIAG_COLUMNS
        }
        out["parse_error_rate"] = self.parse_error_rate
        out["undefined_action_count"] = float(self.undefined_action_count)
        out["tape_miss_count"] = float(self.tape_miss_count)
        out["conversation_sessions"] = float(self.conversation_sessions)
        return out

    @property
    def final_hash(self) -> str:
        return self.checkpoints[-1].combined if self.checkpoints else ""

    def _waste_breakdown_text(self) -> str:
        """要約の廃棄の内訳(店・世帯の消費・街路)。内訳の無い結果は空。"""
        b = self.waste_sink.get("breakdown_t") if self.waste_sink else None
        if not b:
            return ""
        return (f"(店 {b['store_expired_stock']:.3f}・世帯の消費 {b['household_consumption']:.3f}・"
                f"街路 {b['street_litter']:.3f})店の帯")

    def _waste_band_note(self) -> str:
        if not self.waste_sink:
            return ""
        return (f"(自己整合性の検査=店の回収量 vs 静的期待 {self.waste_sink.get('expected_store_t', 0.0):.3f} t/日 ±30%・"
                "現実との照合ではない・体数に依らない・"
                "区の総排出量との比較は保留)")

    @property
    def waste_band_ok(self) -> bool:
        """第304 Q135 (a): **店の収集量**を店だけの帯と比べる(内訳の無い結果は従来どおり総量で比べる)。"""
        lo, hi = self.waste_band
        v = self.waste_sink.get("breakdown_t", {}).get("store_expired_stock") if self.waste_sink else None
        return bool(hi > 0.0 and lo <= (self.waste_tonnes_per_day if v is None else float(v)) <= hi)

    def run_manifest_fields(self) -> dict[str, Any]:
        """ラン manifest の同定欄(C6 が読む)。

        Returns:
            ``registry_hash``(世界側台帳)・``replay_date``(D-W15 の実日)・
            ``template_sha256``(知覚テンプレ v1 の凍結ハッシュ)・
            ``budget_mode``(知覚契約書 §3.2 ablation ① の腕)・
            ``l4_scale``/``budget_per_tick``(L4 呼数予算の腕=D-99 (a)・AB8-L4-SCALE。
            既定 ``1.0`` と ``call_budget_per_tick(n_agents)``)・
            ``p_notice_ablation``/``p_notice_d50_scale``/``refractory_scale``/``signage``
            (§8 第1陣 ②③⑥ の腕。既定は ``A4``/``1.0``/``{}``/``True``)・
            ``signage_p_see``(看板の注視ゲート=§4 段1 の p_see・D-59 (b)・腕
            AB6b-AD-NOTICE。既定 ``1.0``=常に見る=現行のバイト)・
            ``intent_mode``(AB7 自由意図の腕。既定 ``vocab``)・
            ``vocab_version``/``synonym_table_version``/``action_usage``
            (語彙 v2 の版・段0 辞書の版・語ごとの使用件数。D-71 §3 F/J。既定は
            ``v1``/``undefined-synonyms-v2``)・
            ``sleep_suppression``(D-56 就寝抑止の腕。既定 ``True``)・
            ``plan_sleep``(D-62「就寝は計画の実行」の腕。既定 ``True``)・
            ``plan_executor``/``exit_mode``/``attendance_rate``(D-66 計画実行層の腕。
            既定 ``True``(ただし W16+W17 のあるランだけ立つ)/``immediate``/``1.0``)・
            ``t3_ok``(T3=冗長方程式の検算の合否。``None``=月次センサスが立たなかった
            ラン=**未実行**。D-85 (a))・``catalog_sha16``(世界カタログ v0.2 の凍結 SHA)・
            ``process_ids``(実際に回した過程 id の昇順)・``ablations``(切った過程/感度試験 id)。
        """
        from shibuya.perception import templates as _T

        runner = getattr(self, "runner", None)
        catalog_sha16 = ""
        process_ids: tuple[str, ...] = ()
        ablations: tuple[str, ...] = ()
        if runner is not None:
            catalog_sha16 = str(getattr(runner.registry.catalog, "sha16", ""))
            process_ids = tuple(
                sorted(
                    {
                        pid
                        for key in runner.enabled
                        for pid in getattr(runner._procs[key], "process_ids", ())
                    }
                )
            )
            ablations = tuple(sorted(runner.disabled_ids))
        return {
            "registry_hash": self.registry_hash,
            "replay_date": self.replay_date,
            # ---- 10a(A1): tick の長さと T=0 の世界内日時・暦の欄・応答の遅れ(列追加のみ) ----
            "tick_seconds": int(self.tick_seconds),
            "start_sim_datetime": str(self.calendar_fields.get("start_sim_datetime", "")),
            "sim_days": int(self.sim_days),
            "calendar": dict(self.calendar_fields),
            "response_delay": int(self.response_delay),
            # 第2波 §2B: ``--hunger-words all``(energy のラン)は実際に描いた段の下限 0 で指紋を計算する
            # (hungry・v1 のランは既存の凍結値のまま=既定は不変)
            "template_sha256": (
                _T.template_sha256(hunger_draw_min_stage=0)
                if (str(self.hunger_words) == "all" and str(self.hunger_model) == "energy")
                else _T.template_sha256()
            ),
            "budget_mode": self.budget_mode,
            # ---- D-99 (a) L4 呼数予算の腕(既定 1.0=宣言どおりの按分)。腕 AB8-L4-SCALE ----
            "l4_scale": float(self.l4_scale),
            "budget_per_tick": float(self.budget_per_tick),
            # ---- 3 段目(D-99 (a′)・D-110): L4 は監査線。総呼数と線の超過を**必ず**書く ----
            **self.l4_audit_fields(),
            # ---- ablation 第1陣(§8)の腕。既定値のランでも欄は常に出る ----
            "p_notice_ablation": self.p_notice_ablation,
            "p_notice_d50_scale": float(self.p_notice_d50_scale),
            "refractory_scale": dict(self.refractory_scale),
            "signage": bool(self.signage),
            # ---- D-59 (b) 看板の注視ゲート(既定 1.0=現行)。腕 AB6b-AD-NOTICE ----
            "signage_p_see": float(self.signage_p_see),
            # ---- AB7 自由意図の腕(既定 vocab)。列追加のみ=既存欄の値は動かない ----
            "intent_mode": str(self.intent_mode),
            # ---- 語彙 v2(D-71 §3 F/J)。既定 v1 では語彙も辞書も現行のまま ----
            "vocab_version": str(self.vocab_version),
            # ---- D-113 ④ 役割語の提示(既定 True)。列追加のみ ----
            "role_words": bool(self.role_words),
            # ---- 二層の段 2(D-116): 活動層が立ったか・種別の分布・起床の内訳。列追加のみ ----
            "activity": bool(self.activity),
            "activity_kind_counts": dict(self.activity_kind_counts),
            # ---- 段 1b(D-96 nightlife (b)): 飲食店の切替口(既定 food=現行)。列追加のみ ----
            "eatery": str(self.eatery),
            # ---- 段 2a(D-114 (a)): 選び手と対象の解決の内訳 (i)〜(iv)。列追加のみ ----
            "chooser": str(self.chooser),
            "poi_target": str(self.poi_target),
            "target_resolution": dict(self.target_resolution),
            # ---- 段 2b(D-112 ②): 移動の行き先の解決の内訳。列追加のみ ----
            "move_resolution": dict(self.move_resolution),
            "move_search_radius": int(self.move_search_radius),
            "mock_move_target_p": float(self.mock_move_target_p),
            # ---- 段 2c(D-112 ①・D-114 案 A): 意図の保持の計数。列追加のみ ----
            "intent": dict(self.intent),
            "intent_max_ticks": int(self.intent_max_ticks),
            "mock_out_of_cell_target_p": float(self.mock_out_of_cell_target_p),
            # ---- 4 段目(M13 訪問+M17 露出): 親しみの表の腕。列追加のみ ----
            "familiarity": bool(self.familiarity),
            "familiarity_k": int(self.familiarity_k),
            "familiarity_summary": dict(self.familiarity_summary),
            # ---- 5 段目 5a(D-118 K1〜K9): 空腹のモデル・エネルギー収支の要約。列追加のみ ----
            "hunger_model": str(self.hunger_model),
            "energy_rate": str(self.energy_rate),
            "energy": dict(self.energy),
            # ---- 第2波 §2B(食事の束の切替口・既定は旧)。列追加のみ ----
            "meal_sleep_defer": str(self.meal_sleep_defer),
            "home_meal": str(self.home_meal),
            "hunger_words": str(self.hunger_words),
            "intero_crossings": dict(self.intero_crossings),
            # ---- 5 段目 5b(D-119 L1〜L8): 方策・選び手の計数・層の記録。列追加のみ ----
            "policy": str(self.policy),
            "classical": dict(self.classical),
            "chooser_stats": dict(self.chooser_stats),
            "decision_layers": dict(self.decision_layers),
            # ---- 5 段目 5c(D-117 M1〜M4): 活動 → 知覚の乗数。列追加のみ ----
            "p_see_activity": dict(self.p_see_activity),
            # ---- 6 段目 6a(記憶 第 1 段の記録): 腕。列追加のみ ----
            "memory": bool(self.memory),
            "memory_n": int(self.memory_n),
            "memory_summary": dict(self.memory_summary),
            # ---- D-120 7a(店の評価の記憶): 腕。列追加のみ ----
            "store_memory": bool(self.store_memory),
            "store_memory_summary": dict(self.store_memory_summary),
            # ---- D-120 7b(会話からの抽出): 列追加のみ ----
            "wom": dict(self.wom),
            # ---- D-120 7c(想起優先・決め手): 列追加のみ ----
            "store_choice": dict(self.store_choice),
            # ---- C10 8a(関係辺): 列追加のみ ----
            "relations": dict(self.relations),
            "calls_by_condition": dict(self.calls_by_condition),
            "synonym_table_version": _synonym_table_version(self.vocab_version),
            "action_usage": dict(self.action_usage),
            # ---- D-56 就寝抑止(既定 True)。False = D-56 前の挙動 ----
            "sleep_suppression": bool(self.sleep_suppression),
            # ---- D-62 就寝は計画の実行(既定 True)。False = D-62 前の挙動 ----
            "plan_sleep": bool(self.plan_sleep),
            # ---- D-66 計画実行層(既定 True・W16+W17 のあるランだけ立つ) ----
            "plan_executor": bool(self.plan_executor),
            "exit_mode": str(self.exit_mode),
            # ---- 9a: 退出の形の内訳と退去の効果(列追加のみ) ----
            "presence_exit": dict(self.presence_exit),
            "leave_effects": dict(self.leave_effects),
            "near_tiebreak": dict(self.near_tiebreak),
            # ---- 第308 D-107 (a): 群・規範の計器(列追加のみ・判定しない) ----
            "group_norms": dict(self.group_norms),
            # ---- 第304 Q135 (a): 廃棄 sink の内訳と店だけの帯(列追加のみ・報告だけ) ----
            "waste_sink": dict(self.waste_sink),
            "attendance_rate": float(self.attendance_rate),
            "derive_rule": str(self.derive_rule),
            "outside_suppression": bool(self.outside_suppression),
            # ---- C9 位置幾何(既定 node=現行のバイト。edge=辺上の連続位置) ----
            "geometry": str(self.geometry),
            # ---- C9c-1 歩行可能面積の出所(既定 legacy=現行式。資産 SHA は frozen_sources) ----
            "area_source": str(self.area_source),
            # ---- C9c-1 席面積の感度腕(既定 None=現行の 飲食 2.0 / その他 4.0) ----
            "seat_area_eatery_m2": self.seat_area_eatery_m2,
            "seat_area_retail_m2": self.seat_area_retail_m2,
            # ---- C9b 対象と注意(edge × 語彙 v2 の積でだけ立つ・G3/G4/G5/G6/G7) ----
            "attention": bool(self.attention),
            # ---- T3(冗長方程式の毎期検算・D-85 (a))。None=月次センサスが立たなかったラン ----
            "t3_ok": self.t3_ok,
            "catalog_sha16": catalog_sha16,
            "process_ids": process_ids,
            "ablations": ablations,
            "frozen_sources": dict(self.frozen_sources),
            # 実艦隊(C6-a)。mock/tape ランでは空 dict(欄は常にある)。
            "fleet": dict(self.fleet_fields),
        }

    def l4_audit_fields(self) -> dict[str, Any]:
        """L4 の監査欄(D-110「ランごとの総呼数を必ず記録」)。

        ``llm_calls_total``=発射した呼の数(再送も 1 呼=``llm_calls``)・``llm_calls_per_agent_day``=
        総呼数 ÷ 体数 ÷ シミュ日数(``ticks × tick_seconds / 86,400``)・``l4_line``=監査線
        ``L4_LINE_PER_AGENT_DAY``(10 呼/体/日)・``l4_exceeded``=線を超えたか・``l4_notes``=注記。
        """
        days = float(self.ticks) * float(self.tick_seconds) / 86_400.0
        per = (
            float(self.llm_calls) / float(self.n_agents) / days
            if (self.n_agents and days > 0.0)
            else 0.0
        )
        conv_calls = int(self.calls_by_condition.get("CONVERSATION_TURN", 0))
        all_calls = int(sum(int(v) for v in self.calls_by_condition.values()))
        conv_share = round(conv_calls / all_calls, 6) if all_calls else 0.0
        return {
            "llm_calls_total": int(self.llm_calls),
            "llm_calls_per_agent_day": round(per, 6),
            "l4_line": float(L4_LINE_PER_AGENT_DAY),
            "l4_exceeded": bool(per > float(L4_LINE_PER_AGENT_DAY)),
            "l4_notes": list(self.l4_notes),
            # ---- C10 8b(R13): 会話クラスの呼の割合の監査線(超えても絞らない=記録だけ) ----
            "l4_conversation_share": conv_share,
            "l4_conversation_line": float(L4_CONVERSATION_SHARE_LINE),
            "l4_conversation_exceeded": bool(conv_share > float(L4_CONVERSATION_SHARE_LINE)),
        }

    @property
    def conserved(self) -> bool:
        """保存則: Σ所持金 + Σ売上 + **Σ運賃(外界への sink)** が不変。

        運賃は境界・経済設計書 §2.2 の sink(世帯→外界・科目「持ち出し」)なので、
        bbox 内の現金合計からは正しく消える。C4 以前(列車なし)は ``fares_paid=0`` で
        C2 の等式そのまま。
        """
        return self.money_start == self.money_end + self.revenue_end + self.fares_paid

    #: ``phase_seconds`` を要約行に出す順(大きい順ではなく **tick の骨格の順**)。
    PHASE_ORDER: tuple[str, ...] = (
        "presence", "phase_a", "detect", "fleet_wait", "llm", "arbiter", "phase_b",
        "phase_c", "movement", "checkpoint",
    )  # ``movement_cpu`` は壁時計の内訳ではないので別行(下の summary)に出す

    def phase_breakdown(self) -> str:
        """位相別の壁時計[ms/tick](P2 の切り分け=どこに時間が入ったか)。

        ``fleet_wait`` は ``--fleet-wait-s`` の待ちで、``llm``(描画+発射+到着処理)とは
        別に数える。``movement`` は ``resolve`` の「位置確定+密度」区間(予算行 P2)。
        """
        n = max(1, self.ticks)
        parts = [
            f"{k} {self.phase_seconds.get(k, 0.0) / n * 1000.0:.2f}"
            for k in self.PHASE_ORDER
            if self.phase_seconds.get(k, 0.0) > 0.0
        ]
        return " / ".join(parts) + f" / 合計 {self.wall_seconds / n * 1000.0:.2f}"

    @property
    def movement_ms_per_tick(self) -> float:
        """予算行 P2(移動+密度更新)の実測[ms/tick]。**壁時計**。"""
        return self.phase_seconds.get("movement", 0.0) / max(1, self.ticks) * 1_000.0

    @property
    def movement_cpu_ms_per_tick(self) -> float:
        """同区間の**スレッド CPU 時間**[ms/tick](``time.thread_time``)。

        ``movement_ms_per_tick`` との差が大きい = **仕事が増えたのではなく待たされた**
        (艦隊クライアントの asyncio スレッドとの GIL 競合)。実装計画書 §4 の
        「httpx イベントループと計算の干渉が出たら LLM クライアントを別プロセスへ」の判定材料。
        """
        return self.phase_seconds.get("movement_cpu", 0.0) / max(1, self.ticks) * 1_000.0

    @property
    def movement_gil_wait_ratio(self) -> float:
        """movement 区間の「待ち」割合 = 1 − CPU/壁時計(0 なら純粋に計算だけ)。"""
        wall = self.phase_seconds.get("movement", 0.0)
        if wall <= 0.0:
            return 0.0
        return max(0.0, 1.0 - self.phase_seconds.get("movement_cpu", 0.0) / wall)

    def summary(self) -> str:
        calls = self.column("calls").sum() if self.diagnostics.size else 0
        lines = [
            f"[run] n={self.n_agents} cells={self.n_cells} seed={self.seed} "
            f"ticks={self.ticks} world={self.world_source}",
            f"  壁時計 {self.wall_seconds:.2f}s (W2 上限 600s) / "
            f"移動+密度 {self.movement_ms_per_tick:.3f} ms/tick (P2 上限 5 ms)",
            f"  LLM呼 {int(calls):,} = {calls / max(1, self.n_agents):.2f} 呼/体/日 "
            f"(L4 制御目標 10)",
            f"  書式エラー率 実効 {self.parse_error_rate:.3f} / 厳密 "
            f"{self.parse_error_rate_strict:.3f} (受入 ≤0.10) ・別名 "
            f"{self.label_alias_rate:.3f} ・位置読み {self.positional_rate:.3f}"
            f" ・辞書写像 {self.dictionary_mapped_rate:.3f}",
            f"  保存則 Σmoney {self.money_end:,} + Σrevenue {self.revenue_end:,} "
            f"+ Σ運賃 {self.fares_paid:,} "
            f"= {self.money_end + self.revenue_end + self.fares_paid:,} "
            f"(初期 {self.money_start:,}) "
            f"{'OK' if self.conserved else 'NG'} / 最小在庫 {self.min_stock}",
            f"  checkpoint {len(self.checkpoints)} 点 最終 {self.final_hash[:16]}…",
            "  内訳[ms/tick] " + self.phase_breakdown(),
            f"  movement 壁 {self.movement_ms_per_tick:.3f} / CPU "
            f"{self.movement_cpu_ms_per_tick:.3f} ms/tick (P2 上限 5) ・待ち割合 "
            f"{self.movement_gil_wait_ratio:.2f}",
        ]
        # 5 段目 5a: エネルギー収支のランだけ 1 行(v1 の summary は 1 文字も変わらない)
        if str(self.hunger_model) == "energy" and self.energy:
            _c = self.energy.get("counts", {})
            _pa = self.energy.get("census_per_agent", {})
            lines.append(
                f"  空腹 energy({self.energy_rate}) 食事 範囲内 {int(_c.get('meals_in_area', 0)):,}"
                f" / 範囲外 {int(_c.get('meals_out_of_area', 0)):,} / 軽食 "
                f"{int(_c.get('snacks', 0)):,} / 飲料 {int(_c.get('drinks', 0)):,} ・収支/体 摂取 "
                f"{_pa.get('intake_kcal', 0.0):,.0f} − 消費 {_pa.get('expenditure_kcal', 0.0):,.0f}"
                f" = {_pa.get('balance_kcal', 0.0):,.0f} kcal(EER {_pa.get('eer_kcal', 0.0):,.0f})"
            )
        # C9: edge 幾何のランだけ 1 行(既定 node の summary は 1 文字も変わらない)
        if str(self.geometry) != DEFAULT_GEOMETRY:
            lines.append(
                f"  幾何 {self.geometry}(希望速度 "
                f"{DESIRED_SPEED_MIN_MS:.2f}〜{DESIRED_SPEED_MAX_MS:.2f} m/s・Kladek 減速)"
                f"/ ホップ反復 {self.geometry_hops:,} / 詰まり {self.geometry_jammed:,}"
            )
        # C9c-1: 面積を実測に切り替えたランだけ 1 行(既定 legacy の summary は不変)
        if str(self.area_source) != DEFAULT_AREA_SOURCE:
            lines.append(
                f"  歩行可能面積 {self.area_source}(中央値 {self.walkable_area_median_m2:,.0f}"
                f" m² / 最小 {self.walkable_area_min_m2:,.1f} m²)"
            )
        # 二層の段 2: 活動層が立ったランだけ 1 行(v1/v2 と --activity off の summary は不変)
        if self.activity:
            ac = self.activity_counters
            lines.append(
                f"  活動層(二層) 設定 {ac.get('activity_set', 0):,} / 満了候補 "
                f"{ac.get('expiry_candidates', 0):,}(呼 "
                f"{self.calls_by_condition.get('ACTIVITY_EXPIRY', 0):,}) / 場所起床の抑止 "
                f"{ac.get('cell_block_suppressed', 0):,} / 到着満了 "
                f"{ac.get('arrival_expired', 0):,} / 相手満了 {ac.get('partner_expired', 0):,}"
                f" / 失敗即時 {ac.get('fail_immediate', 0):,} / あたり歩数 "
                f"{ac.get('wander_steps', 0):,} / 種別 "
                + " ".join(f"{k}:{v}" for k, v in self.activity_kind_counts.items())
            )
        # C9b: 対象と注意の腕だけ 1 行(既定の 4 腕では出ない)
        if self.attention:
            lines.append(
                f"  対象と注意(C9b) 近づく {self.n_approach:,}"
                f"(到達 {self.n_approach_done:,} / 対象不在 {self.n_target_gone:,})"
                f" / 焦点 取得 {self.n_focus:,} 消失 {self.n_focus_lost:,}"
                f" / 会話 実距離成立 {self.n_talk_by_distance:,}"
            )
        # D-113 ③: 列を捌いたランだけ 1 行(列が立たないランでは summary は不変)
        if self.n_served_from_queue or self.n_queue_closed:
            lines.append(
                f"  待ち行列の捌き(D-113 ③) 席へ {self.n_served_from_queue:,}"
                f" / 閉店で解散 {self.n_queue_closed:,}"
            )
        # D-113 ②: 通報があったランだけ 1 行(通報 0 のランでは summary は不変)
        if self.n_report_ok or self.n_report_no_event:
            lines.append(
                f"  通報(D-113 ② 前提検査) 成立 {self.n_report_ok:,}"
                f" / 知覚済みの事象なし {self.n_report_no_event:,}"
            )
        # D-58: 繰り延べを記録/再現したランだけ 1 行(mock ランは従来どおり出ない)
        _bd = float(self.bridge_counters.get("tape_deferred_rows", 0.0)) or float(
            self.bridge_counters.get("tape_deferred", 0.0)
        )
        if _bd:
            lines.append(
                f"  テープ繰り延べ行 {int(_bd):,}(D-58・応答なしの呼)/ 再投入 "
                f"{int(self.bridge_counters.get('fleet_reinjected', 0)):,} / 再送 "
                f"{int(self.bridge_counters.get('fleet_resent', 0)):,} / 終端未応答 "
                f"{self.fleet_unanswered_at_end:,}"
            )
        if self.frozen_sources:
            lines.append("  凍結静的文 " + " ".join(f"{k}={v[:16]}" for k, v in sorted(self.frozen_sources.items())))
        if self.registry_hash:
            lines.append(
                f"  世界過程 台帳 {self.registry_hash[:16]}… 憲法5 "
                f"{'OK' if self.constitution_ok else 'NG'} / 再生日 "
                f"{self.replay_date or '(合成)'} / 乗車 {self.n_boarded:,} 降車 "
                f"{self.n_alighted:,} 待ち行列 {self.n_queued:,} 乗車待ち "
                f"{self.n_board_waiting:,}(打ち切り {self.n_board_timeout:,}) 乗り残し "
                f"{int(self.process_counters.get('rail.left_behind', 0)):,}"
                f"({self.process_counters.get('rail.left_behind_rate', 0.0):.4f}) / ActualLog "
                f"{self.actual_log_rows:,} 行 遵守率 {self.compliance_rate:.3f}"
            )
            lines.append(
                f"  C4後半: 補充 {self.restocks:,} / 納品 {self.deliveries:,} / 宅配 "
                f"{self.parcels:,} / バス到着 {self.bus_arrivals:,} / ホテル泊 "
                f"{self.hotel_checkins:,} / 顕著行為 {self.salient_events:,}(気づき "
                f"{self.noticed:,}・出動 {self.dispatches:,}) / 廃棄 "
                f"{self.waste_tonnes_per_day:.3f} t/日{self._waste_breakdown_text()} (band {self.waste_band[0]:.2f}-"
                f"{self.waste_band[1]:.2f}) {'OK' if self.waste_band_ok else 'NG'}{self._waste_band_note()}"
            )
            if self.census_row:
                lines.append(
                    f"  日次センサス(§2.4・締めた day={self.day_closed}): 残差 "
                    f"{self.census_row.get('residual', 0):,} / 貨幣供給 "
                    f"{self.census_row.get('money_supply', 0):,} / faucet "
                    f"{self.census_row.get('faucet_total', 0):,} / sink "
                    f"{self.census_row.get('sink_total', 0):,} / 棚卸差異 "
                    f"{self.census_row.get('goods_residual_units', 0):,} / 廃棄 "
                    f"{self.census_row.get('waste_g', 0.0):,.0f}g / ゲート "
                    f"{'PASS' if self.census_pass else 'FAIL(診断の赤)'}"
                )
            lines.append(
                "  過程別[s]: "
                + ", ".join(f"{k}={v:.3f}" for k, v in sorted(self.process_seconds.items()))
            )
        if self.renderer_counters:
            c = self.renderer_counters
            lines.append(
                f"  レンダラ {self.renderer_name}: 描画 {int(c.get('render_calls', 0)):,} "
                f"命中率 {c.get('render_cache_hit_rate', 0.0):.3f} / "
                f"平均tok 共有静的 {c.get('tokens_shared_static_mean', 0.0):.1f}/750 "
                f"セル {c.get('tokens_cell_mean', 0.0):.1f}/250 "
                f"個体 {c.get('tokens_individual_mean', 0.0):.1f}/300 "
                f"(合計 {c.get('prompt_tokens_mean', 0.0):.1f}) "
                f"切り詰め {int(c.get('render_truncations', 0)):,}"
            )
        for col in DIAG_COLUMNS:
            lines.append(f"  診断 {col}: {int(self.column(col).sum()):,}")
        lines.append(f"  診断 sleep_suppressed: {self.sleep_suppressed_count:,}")
        lines.append(f"  診断 outside_suppressed: {self.outside_suppressed_count:,}")
        lines.append(
            f"  域外宛ての呼 {self.outside_wake_candidates:,}"
            f"(抑止 {self.outside_suppressed_count:,}"
            f"・抑止腕 {'on' if self.outside_suppression else 'off'})"
        )
        lines.append("  " + self.calls_by_hour_text())
        lines.append("  " + self.wake_rate_by_hour_text())
        if len(self.wake_rate_in_area_by_hour) == 24:
            lines.append("  " + self.wake_rate_in_area_by_hour_text())
        if self.planned_sleep_counts:
            c = self.planned_sleep_counts
            lines.append(
                f"  D-62 計画就寝 その場 {int(c.get('slept', 0)):,} + 着いて "
                f"{int(c.get('arrived', 0)):,}(歩行中 {int(c.get('walking', 0)):,})"
                f" / 計画起床 {int(c.get('woke', 0)):,}"
                f" / 寝かせなかった 乗車中 {int(c.get('riding', 0)):,}"
                f"・域外 {int(c.get('outside', 0)):,}"
                f"・会話中 {int(c.get('conversing', 0)):,}"
                f"・就寝済 {int(c.get('asleep', 0)):,}"
                f"・行けない {int(c.get('unreachable', 0)):,}"
            )
        if self.presence_summary:
            lines.append("  " + self.presence_summary)
        lines.append(
            f"  診断 parse_error_rate: {self.parse_error_rate:.4f} / "
            f"undefined_action_count: {self.undefined_action_count:,} / "
            f"tape_miss_count: {self.tape_miss_count:,} / "
            f"conversation_sessions: {self.conversation_sessions:,}"
        )
        if self.growth_report is not None:
            lines.append("  " + self.growth_report.as_text().replace("\n", "\n  "))
        return "\n".join(lines)


def _resolve_population(
    population: "Population | bool | None",
    world_dir: str | Path | None,
    n_agents: int,
    seed: int | str,
    n_cells: int,
) -> "Population | None":
    """``population`` 引数 → 実体(``None``=資産が無い/切っている)。

    ``False`` は「母集団を使わない」の明示。``None``(既定)は ``world_dir`` に W16 の
    出力があれば読む。既に ``Population`` なら体数だけ合わせる(二層抽出)。
    """
    if population is False:
        return None
    if isinstance(population, Population):
        pop = population
        _check_population_fits(pop, n_cells)
    else:
        if world_dir is None:
            return None
        pop = load_population(world_dir, n=None, seed=seed)
        if pop is None:
            return None
        if not _population_fits(pop, n_cells):
            # ``world_dir`` は知覚資産の置き場として渡されているが、世界そのものは
            # 合成小世界(セル数が違う)。**自動読み込みは黙って見送る**
            # (明示的に population= を渡したときだけ食い違いを例外にする)。
            return None
    if pop.n > n_agents:
        pop = sample_population(pop, n_agents, seed)
    return pop


def _population_fits(pop: "Population", n_cells: int) -> bool:
    """母集団のセル索引が世界のセル数に収まるか。"""
    for arr in (pop.home_cell, pop.work_cell, pop.school_cell):
        if arr.size and int(arr.max()) >= int(n_cells):
            return False
    return True


def _check_population_fits(pop: "Population", n_cells: int) -> None:
    if not _population_fits(pop, n_cells):
        raise ValueError(
            f"母集団のセル索引が世界のセル数({n_cells})を超える。世界資産と母集団の版が違う"
        )


def _schedule_with_population(
    schedule, pop: "Population", n_cells: int, *, keep_outside_home: bool = False
):
    """mock 日課の拠点・種別を **W16 母集団**で置き換える(時刻帯は W17 まで mock のまま)。

    体数が母集団より多いときは、足りない分は mock の合成個体のまま残す(縮小ランの保険)。
    ``home_cell`` を持たない体(域外常住)は ``Population.start_cell`` の規約で置く
    (勤務→通学→mock の自宅セル)=W17 が入るまでの繋ぎ・expedient。

    Args:
        keep_outside_home: **D-66 計画実行層のラン**で True。域外常住の ``home_cell`` を
            ``-1`` のまま残し(=自宅=職場の代入をやめ)、``np.clip`` で −1 を潰さない。
            自宅のない体は計画実行層が起動時に ``place_at_external`` で外へ置く。
            既定 False = **帰無腕の挙動そのまま**(1 バイトも変わらない)。
    """
    n = int(schedule.n_agents)
    m = min(n, pop.n)
    home = np.asarray(schedule.home_cell).copy()
    work = np.asarray(schedule.work_cell).copy()
    # C9b G5: 学校セルは W16 が持っている(mock 側に対応する欄は無い)。対象ヒント
    # ``school`` の解決先としてそのまま運ぶ(**-1 のまま**=学校なしはヒントが効かない)。
    school = np.full(n, -1, dtype=np.int32)
    school[:m] = np.asarray(pop.school_cell, dtype=np.int64)[:m].astype(np.int32)
    kind = np.asarray(schedule.kind).copy()
    age = np.zeros(n, dtype=np.uint8)
    sex = np.full(n, -1, dtype=np.int8)
    direction = np.full(n, -1, dtype=np.int32)
    if keep_outside_home:
        ph = np.asarray(pop.home_cell, dtype=np.int64)[:m]
        home[:m] = np.where(ph >= 0, ph, -1)  # 域外常住は −1 のまま(I6 のガードが受ける)
    else:
        start = pop.start_cell(fallback=-1)[:m]
        home[:m] = np.where(start >= 0, start, home[:m])
    pw = pop.work_cell[:m]
    work[:m] = np.where(pw >= 0, pw, work[:m])
    kind[:m] = pop.kind[:m]
    age[:m] = pop.age[:m]
    sex[:m] = pop.sex[:m]
    direction[:m] = pop.direction_node[:m]
    home_out = np.clip(home, 0, n_cells - 1) if not keep_outside_home else np.where(
        home >= 0, np.clip(home, 0, n_cells - 1), -1
    )
    return dataclasses.replace(
        schedule,
        home_cell=home_out.astype(np.int32),
        work_cell=np.clip(work, 0, n_cells - 1).astype(np.int32),
        school_cell=np.where(school >= 0, np.clip(school, 0, n_cells - 1), -1).astype(np.int32),
        kind=kind,
        age=age,
        sex=sex,
        direction_node=direction,
        population_hash=pop.population_hash(),
    )


def _settle_pending_invites(
    conv, agents, tick, agent_ids, codes, named, R, np, by_distance: bool = False
) -> set[int]:
    """返事待ちの招待を**Phase C の前に**確定する(層2 中-1・09-09)。

    正典
    - 行動契約書 §1-2 対象スロット: 承諾は「行動: 会話 **対象: 招待者**」。
    - 同 §6「直前の結果」: 承諾を intent のまま Phase C へ流すと、招待者は待ちで
      CONVERSING なので ``resolve._apply_talk`` が ``PARTNER_BUSY`` を書き、被招待の
      B6 に**偽の失敗**が載る(層2 再現: 51 セッション中 45 件)。ここで消費して防ぐ。

    承諾の規則(中-2・**expedient**: 契約書に承諾の対象規則は無い)
      - 返事が **会話** かつ 対象が **招待者 A**(または **名指しなし**)→ **承諾**。
      - 返事が 会話 でも 対象が **第三者 C** → A へは**拒否**。B の行は intent に残し、
        C への新しい招待として通す。
      - それ以外の行動 → 拒否。

    Returns:
        **intent から外す**個体(=承諾した被招待。承諾は新しい招待ではない)。
    """
    if conv is None or not conv.pending_invites:
        return set()
    consumed: set[int] = set()
    accepted: list[tuple[int, int]] = []
    reverted: list[int] = []
    # 逐次ループ宣言: この tick に応答した個体のうち返事待ちの数ぶん(≤ 1 tick の呼数)。
    for k in range(int(agent_ids.size)):
        b = int(agent_ids[k])
        if b not in conv.pending_invites:
            continue
        a = conv.pending_inviter_of(b)
        # C9b G7: ``by_distance`` の腕では「同一セル」に実距離 2 m が加わる。
        same_cell = bool(
            a >= 0
            and R.talk_within_reach(agents, np.int64(a), np.int64(b), by_distance=by_distance)
        )
        aimed_at_inviter = int(named[k]) in (a, -1)
        ok = bool(codes[k] == C.ACT_TALK) and aimed_at_inviter and same_cell
        opened = conv.resolve_pending(b, tick, accepted=ok)
        if opened is not None:
            accepted.append((a, b))
            consumed.add(b)  # 承諾は新しい招待ではない=intent から外す
        elif a >= 0 and not conv.is_busy(a):
            reverted.append(a)
    if accepted:
        R.set_conversing(
            agents,
            np.array([x for x, _ in accepted], dtype=np.int64),
            np.array([y for _, y in accepted], dtype=np.int64),
        )
    if reverted:
        R.revert_conversation(agents, np.array(sorted(set(reverted)), dtype=np.int64))
    return consumed


def _inviter_of(conv: Any, agent_id: int, condition: int = -1) -> int:
    """**返事待ちの招待**があれば招待者の個体 id、無ければ -1(知覚契約書 §6 起床(ii))。

    起床条件では絞らない(``condition`` は診断用に受けるだけ)。``_settle_pending_invites``
    は**その tick に答えた全員**の中から返事待ちを拾うので、被招待が別の条件
    (一般活動など)で起きた呼も承諾/拒否として消費される。会話ターン起床に限ると
    その分の呼に招待者が載らず、**答えようがないのに拒否と数えられる**(実測: 200体600tick で
    招待文が載った呼は 4 件しかなかった)。

    会話ターン起床には「セッションの話者」と「返事待ちの被招待」の 2 種類が同じ
    ``WakeCondition.CONVERSATION_TURN`` で来る(``conversation.wake_candidates``)が、
    話者には返事待ちが無いので ``pending_inviter_of`` が -1 を返して切り分けになる。
    """
    if conv is None:
        return -1
    return int(conv.pending_inviter_of(int(agent_id)))


def _target_person(target: Any) -> int:
    """``llm.contract.Target`` → 個体 id(``P-nnn`` 以外は ``-1``)。

    行動契約書 §1-2 の「対象: <セルID|物カテゴリ|**個体ID**>」を会話の相手として使う
    (C6・09-09)。パーサは素の整数も PERSON と読むので、そのまま個体 id にする。
    """
    kind = getattr(target, "kind", None)
    if kind is None or int(kind) != int(TargetKind.PERSON):
        return -1
    pid = getattr(target, "person_id", None)
    return -1 if pid is None else int(pid)


def _target_poi(target: Any) -> int:
    """``llm.contract.Target`` → 目印 POI 索引(解決できていなければ ``-1``)。

    C9b G6 a′: ``parse_target(..., landmarks=...)`` を通った応答だけが ``poi_id`` を持つ。
    """
    pid = getattr(target, "poi_id", None)
    return -1 if pid is None else int(pid)


def _pending_extra(res: Any) -> tuple[int, int, Any, Any]:
    """応答 → ``(対象ヒント索引, 目印 POI 索引, 活動, 対象)``。

    C9b G5/G6(腕が立っていなければ ``(0, -1)``)+ **二層の段 2** の活動
    (``engine.activity.payload_of``・語彙 v3 の応答だけ・それ以外は ``None``)+
    **段 2a** の対象(``llm.contract.Target``・購入/食事/並ぶの候補の絞り込みが読む)。
    """
    return (
        C.target_hint_code(getattr(res, "target_hint", "")),
        _target_poi(getattr(res, "target", None)),
        payload_of(res),
        getattr(res, "target", None),
    )


def classical_acq_addressable(agents: Any, aid: int, ids: "list[int]", A: np.ndarray, *,
                               by_distance: bool) -> np.ndarray:
    """第2波 §2A 項 3-1(検収後): 古典の交際の候補の A から、話しかけられない相手(会話中・就寝中=
    ``resolve._UNADDRESSABLE``)と、このランの設定で会話が届かない相手(``resolve.talk_within_reach`` が偽)を
    −inf にする(``resolve._apply_talk`` が PARTNER_BUSY/PARTNER_GONE で落とす相手を先に除く)。

    逐次ループ宣言(P4): なし(近接行の人数ぶんの配列演算)。
    """
    A = np.asarray(A, dtype=np.float64)
    if A.size == 0:
        return A
    p = np.asarray(ids, dtype=np.int64)
    ok = (p >= 0) & (p < agents.n) & (p != int(aid))
    pc = np.clip(p, 0, max(0, agents.n - 1))
    ok &= ~np.isin(np.asarray(agents.registry.activity)[pc], R._UNADDRESSABLE)
    ok &= R.talk_within_reach(agents, np.full(p.size, int(aid), dtype=np.int64), pc, by_distance=by_distance)
    return np.where(ok, A, -np.inf)


def run_day(
    n_agents: int = 5_000,
    seed: int | str = 1,
    world: World | None = None,
    *,
    tick_seconds: int = DEFAULT_TICK_SECONDS,
    ticks: int = MINUTES_PER_SIM_DAY,
    llm: Any | None = None,
    fleet: "FleetClient | None" = None,
    fleet_wait_s: float = 0.0,
    fleet_debug_dir: str | Path | None = None,
    checkpoint_every: int = 360,
    day_index: int = 0,
    budget: float | None = None,
    l4_scale: float = 1.0,
    n_cells: int = 139,
    mode: str = "record",
    tape_path: str | Path | None = None,
    replay: Any | None = None,
    renderer: Any | None = None,
    world_dir: str | Path | None = None,
    conversations: bool = True,
    lane: str = DEFAULT_LANE,
    ledger: "LedgerBundle | None" = None,
    processes: bool = True,
    processes_enabled: "list[str] | tuple[str, ...] | None" = None,
    processes_disabled: "list[str] | tuple[str, ...] | None" = None,
    p_notice_ablation: str | int = "A4",
    p_notice_d50_scale: float = 1.0,
    refractory_scale: Mapping[Any, float] | None = None,
    signage: bool = True,
    signage_p_see: float = SIGNAGE_P_SEE_DEFAULT,
    intent_mode: str = INTENT_MODES[0],
    vocab_version: str = VOCAB_VERSIONS[0],
    role_words: bool | str = True,
    near_tiebreak: str = DEFAULT_NEAR_TIEBREAK,
    near_order: str = DEFAULT_NEAR_ORDER,
    group_norms: bool | str = True,
    budget_mode: str | BudgetMode = BudgetMode.FIXED_SLOTS,
    salient_rate_per_10k: float | None = None,
    report_precondition: bool = True,
    queue_service: bool = True,
    leave_effect: bool = True,
    population: "Population | bool | None" = None,
    occupancy_every: int = 0,
    occupancy_path: "str | Path | None" = None,
    sleep_suppression: bool = True,
    plan_sleep: bool = True,
    plan_executor: bool = True,
    exit_mode: str = "immediate",
    attendance_rate: float = 1.0,
    outside_suppression: bool = True,
    derive_rule: str = "v2",
    geometry: str = DEFAULT_GEOMETRY,
    area_source: str = DEFAULT_AREA_SOURCE,
    seat_area_eatery_m2: float | None = None,
    seat_area_retail_m2: float | None = None,
    census_out: str | Path | None = None,
    activity: bool | str = True,
    eatery: str = "food",
    chooser: str = DEFAULT_CHOOSER,
    poi_target: str = DEFAULT_POI_TARGET,
    move_search_radius: int = MOVE_SEARCH_RADIUS_CELLS,
    mock_move_target_p: float = 0.0,
    intent_max_ticks: int = INTENT_MAX_TICKS,
    mock_out_of_cell_target_p: float = 0.0,
    familiarity: bool | str = False,
    familiarity_k: int = FAMILIARITY_K,
    hunger_model: str = "v1",
    energy_rate: str = DEFAULT_ENERGY_RATE,
    meal_sleep_defer: str = DEFAULT_MEAL_SLEEP_DEFER,
    home_meal: str = DEFAULT_HOME_MEAL,
    hunger_words: str = DEFAULT_HUNGER_WORDS,
    policy: str = DEFAULT_POLICY,
    activity_region: str = DEFAULT_ACTIVITY_REGION,
    classical_social: str = DEFAULT_CLASSICAL_SOCIAL,
    meal_gate: str = DEFAULT_MEAL_GATE,
    classical_habit_p: float = HABIT_P,
    classical_tau: float = RANK_TAU,
    p_see_activity: "Mapping[str, float] | str | None" = None,
    memory: bool | str = False,
    memory_n: int = MEMORY_N,
    memory_tau: float = RECALL_TAU,
    store_memory: bool | str = False,
    store_memory_n: int = STORE_MEMORY_N,
    store_sigma: "Mapping[str, float] | str | None" = None,
    store_decay: str = DEFAULT_STORE_DECAY,
    store_wom: bool | str = True,
    store_signage: bool | str = True,
    store_recall_scope: str = "all",
    wom_source: str = DEFAULT_WOM_SOURCE,
    relations: bool | str = False,
    rel_k: int = REL_K,
    rel_tau: float | None = None,
    rel_d: float = REL_D,
    rel_init_density: float = 1.0,
    conv_max_participants: int = 2,
    rel_tenure_weeks: float = REL_TENURE_WEEKS,
    rel_tenure_hash: str = DEFAULT_REL_TENURE_HASH,
    rel_invite: bool | str = True,
    rel_acq_wake: bool | str = True,
    rel_copresent: bool | str = False,
    sim_days: int = 1,
    start_sim_datetime: "datetime | str | None" = None,
    calendar_weekday: str = DEFAULT_WEEKDAY_MODE,
    holiday_csv: "str | Path" = DEFAULT_HOLIDAY_CSV,
    school_holidays: Any = (),
    response_delay: int | None = None,
) -> RunResult:
    """1 シミュ日(既定 1,440 tick)の mock ランを回す。

    Args:
        n_agents: 個体数。
        seed: manifest の ``master_seed``。
        world: 世界(None なら ``World.synthetic(n_cells, seed)``)。
        tick_seconds: 1 tick の秒数。
        ticks: tick 数。
        llm: ``LLMClient``(None なら ``MockLLM(seed)``)。
        fleet: 実 vLLM 艦隊(``llm.fleet.FleetClient``)。**渡すと LLM 経路が非同期になる**:
            ④ で 1 tick 分をまとめて発射(非ブロッキング)し、④′ で届いた分を拾う。
            繰り延べ(タイムアウト・キュー満杯・接続エラー枯渇)は**次 tick の起床候補へ
            再投入**する(不応期は免除=``resolve.clear_refractory``)。``None`` なら従来の
            同期 1 呼経路(``llm``=mock/tape)で、**挙動は 1 バイトも変わらない**。
        fleet_wait_s: ④′(艦隊の受け取り)で未応答が残っているとき**最大この秒数だけ待つ**。既定 0.0=
            純非ブロッキング。**本番の運用は 120**(障壁 120 s=c7 の本番ラン。1 tick に発射した呼が
            次の tick の受け取りで全部届くように待つ)。0 のままだと応答がラン終端にまとめて届き
            δ_think の契約(``t_apply``=起床+δ_perc+δ_think)が観測できない(スモークやテストのように
            エンジンが LLM より桁違いに速いランでも同じ)。受け取りの位置は ``response_delay`` を参照。
        fleet_debug_dir: 書式の原因分析用 jsonl の置き場(``None``=off が既定)。初回パースが
            落ちた呼だけ {プロンプト・初回の生応答・再生成の生応答・実効/厳密の判定・理由} を
            1 行 1 呼で落とす。**テープ形式は変えない**(テープは最終応答 1 行のまま)。
        checkpoint_every: checkpoint 間隔[tick]。
        day_index: 曜日(0=月曜)。
        budget: 1 tick の呼数上限(None なら L4 按分)。
        l4_scale: **manifest に載せるだけ**の同定欄(PENDING D-99 (a)・腕 AB8-L4-SCALE)。
            倍率から ``budget`` を作るのは ``cli.run``(``l4_scale>0`` なら
            ``call_budget_per_tick(n_agents)×倍率``・``0`` なら ``n_agents``=無制限)。
            **3 段目(D-99 (a′)・D-110)**: CLI と ``cli.run`` の既定は **0=無制限**
            (``cli.CLI_DEFAULT_L4_SCALE``)。本関数の既定(``budget=None``=L4 按分)は
            ライブラリの切替口として残す(``--l4-scale 1`` と同じ=旧挙動)。L4 は監査線=
            manifest の ``llm_calls_total``/``llm_calls_per_agent_day``/``l4_line``/``l4_exceeded``。
            ここでは**計算に一切使わない**=既定 1.0 のランのバイトは 1 つも動かない。
        n_cells: 合成世界を作るときのセル数。
        mode: ``"record"``(``llm`` を呼ぶ)/ ``"replay"``(テープ完全一致・テープ外は計数)。
        tape_path: 録画テープの出力先(None なら記録しない)。
        replay: ``mode="replay"`` のときのテープ(``Replay`` かパス)。
        renderer: プロンプト生成。**None なら本物の ``perception.renderer.Renderer``**
            (C3 結線)。``"stub"`` で ``StubRenderer``(安い決定論テスト用)。
        world_dir: 世界資産ディレクトリ(``PerceptionAssets.load`` の入口。None または
            資産が無ければ ``PerceptionAssets.synthetic`` へ落ちる)。
        conversations: 会話プロトコル(行動契約書 §3)を回すか。
        lane: δ_think のレーン(認知設計書 §1)。
        ledger: 金/物の台帳(``engine.ledger_api.LedgerBundle``・economy が実装を注入する)。
            ``None`` なら C2 と同じ直接更新の経路。世帯の現金は**個体 SoA の ``money``
            そのもの**を採用するので、run は ``AgentState`` を作った直後に
            ``attach_household_cash`` を呼ぶ(台帳の世帯数は ``n_agents`` と一致が必要)。
        census_out: 日次センサス/月次 MER の**出力先ディレクトリ**(境界・経済設計書 §2.4)。
            ``None``(既定)なら**何も書かない**=manifest・checkpoint・出力ファイルは
            1 バイトも動かない。渡すと日の締めのあとに ``LedgerBundle.write_census``
            (economy 側が注入する書き手)を 1 回呼び、書いたパスを
            ``RunResult.census_paths`` に置く。台帳を渡していないランでは何も起きない。
        processes: 世界過程(C4 第1陣)を回すか(既定 True)。資産が無い合成世界では
            混雑場だけが動き、他の過程は「休む」。
        processes_enabled / processes_disabled: 過程 id か感度試験 id(``AB-*``)で
            過程単位に切る(ablation)。
        budget_mode: 知覚契約書 §3.2 の**義務 ablation ①**「チャネル固定枠 vs 同一総トークンの
            単一ランキング」の腕。``"fixed"``(既定=現行の描画・1 バイトも変わらない)/
            ``"ranking"``(チャネル別の上限表を使わず群予算だけを守る)。
            ``renderer`` を明示注入したランでは**このフラグは効かない**(注入側が持つ)。
        p_notice_ablation: 顕著行為の到達 ``p_notice`` の ablation(知覚契約書 §3.1 の
            ``A0``-``A4``。既定 ``A4``=完成形)。``processes_enabled`` に
            ``AB-PNOTICE-A2`` のように書いても効く。**``--ablate AB-PNOTICE-A0`` は
            ``salient`` 過程ごと止まる**(過程トグルと id を共有するため)ので、A0-A4 の
            腕を選ぶときは必ずこの引数を使う。
        p_notice_d50_scale: 知覚契約書 §8 第1陣 **② の腕**「p_notice の d50 を 0.5×/2×」。
            §3.1 の d50(既定 40 m・事象クラス別の表も同じ倍率)に掛ける正の倍率。
            既定 1.0=現行の抽選で**1 ビットも変わらない**。打ち切り 80 m は動かさない
            (2.0× は d50=打ち切りと同値になる=報告に明記する)。
        refractory_scale: 知覚契約書 §8 第1陣 **③ の腕**「近接入替の不応期 15 分 ±50%」。
            ``{起床条件: 倍率}``(鍵は ``WakeCondition``・列番号・条件名)。§6 不応期表を
            ランごとに振る(``engine.resolve.refractory_ticks``)。既定 ``None``=表どおり。
        signage: 知覚契約書 §8 第1陣 **⑥ の腕**「広告ゼロ」。``False`` で看板・広告面
            (B2.signage)を全セルで空にする(W14 凍結文も合成文も載せない)。既定 True。
            ``renderer`` を明示注入したランでは**このフラグは効かない**(注入側が持つ)。
        signage_p_see: **看板の注視ゲート**(知覚契約書 §4 段1 の視認確率 p_see・
            D-59 (b) ユーザー決定 2026-09-17・腕 ``AB6b-AD-NOTICE``)。在圏セルの
            看板行を観測へ入れるかを**体×看板×tick の決定論的ベルヌーイ**で決める
            (``core.rng`` の Philox・ドメイン ``perception.attention.p_see``・
            カウンタ ``(tick, agent_id, poi_id)``=テープから再現できる)。
            既定 1.0=常に載せる=**1 バイトも変わらない**(抽選も引かない)。
            0.0 は ⑥「広告ゼロ」と同じ描画になる(ただし ⑥ は ``signage=False`` が正典)。
            0.0〜1.0 の外は ``ValueError``。``renderer`` を明示注入したランでは
            **効かない**(注入側が持つ)。
        intent_mode: **AB7 自由意図の腕**(仕様書 §2)。``"vocab"``(既定)は
            現行どおり B0 に 24 語のホワイトリストを見せる。``"open"`` は ``行動:`` の 1 行だけを
            「いま自分がしたいことを10字以内の動詞句で」に差し替える(理由・対象・ひと言・
            2 行形・JSON 禁止は同文)。``"hint"``(AB7b)は同じ 1 行を「語彙から選ぶのが基本・
            当てはまる語が無いときだけ 10 字以内の動詞句」にする中間の腕。接地はどの腕でも
            エンジン側(§7 段0 辞書写像 → 段1 記録+待機)。
        role_words: **D-113 ④(第269)** B0 の末尾に役割語 12 語の 1 行(「自分の役割に権限が
            あるときだけ成立」)を足す(既定 True=行動契約書 §2.2「語彙自体は全員に見せる」)。
            ``False`` は第268 以前の B0(prompt_hash が変わるので、それ以前に録ったテープの
            再生では ``False`` を渡す)。mock の checkpoint は B0 を読まないので不変。
            既定では**1 バイトも変わらない**(テンプレ本体・``template_sha256`` も不変)。
            ``INTENT_MODES`` 以外は ``ValueError``。
        near_tiebreak: **小さいもの①(第300 Q107)** B5 近接行の距離の同点の切り方。``"hash"``(既定)=
            run_salt の決定論ハッシュ(観る体 × 相手)で撹拌 / ``"id"`` = 旧挙動(セル内の並び=行番号の順=
            旧 golden)。文面・近接行の並び(id 昇順)は変えない=採る人だけ。``NEAR_TIEBREAKS`` 以外は ``ValueError``。
        near_order: **小さいもの 第 2 批①(第304 Q130)** B5 近接行の並び。``"distance"``(既定)= 距離の昇順・
            同点は ``near_tiebreak`` の順 / ``"id"`` = 旧挙動(行番号の昇順=旧 golden)。焦点の先頭・知人の常時掲載・
            文面は変えない。mock は B5 を読まないので final は動かない(プロンプトは動く)。
            ``renderer`` を明示注入したランでは**このフラグは効かない**(注入側が持つ)。
        group_norms: **第309(Q150)** 群・規範の計器(D-107 (a)・``engine.norm_meter``=読むだけ)を回すか。
            ``True``/``"on"``(既定=第308 のまま)/ ``False``/``"off"`` で計器の 3 つの口を通さない(manifest
            ``group_norms`` は ``{"enabled": False}``)。計器は状態・乱数・テープに触れないので**どちらでも final は同じ**。
        vocab_version: **行動語彙の版**(D-71 §3 F・2026-09-17 ユーザー決定)。
            ``"v1"``(既定)は現行の 24 語(横断 12 + 役割 12)で、**1 バイトも変わらない**。
            ``"v2"`` は横断語「食事」(飲食店オブジェクトの affordance・コード 24)を足し、
            ① B0 の出力規約が 13 語提示になる ② 段0 辞書が v3 になる
            (``食べる``/``飲む`` → ``食事``)③ ``resolve`` に「食事」の分岐が増える。
            **``llm`` を注入しないランでは mock の語彙もこの版に従う**(``MockLLM`` は
            プロンプトを読まないので、ここを合わせないと mock では「食事」が 1 件も出ない)。
            ``renderer`` を明示注入したランでは B0 側だけ注入側が持つ。
            ``VOCAB_VERSIONS`` 以外は ``ValueError``。
        population: W16 母集団(``agents.population.Population``)。``None``(既定)は
            **``world_dir`` に ``w16_population.parquet`` があれば自動で読む**
            (``n_agents`` 体へ二層抽出)。``False`` で明示的に切る(合成個体のまま)。
            資産が無ければ静かに合成個体へ落ちる。
        salient_rate_per_10k: 「倒れる」の発生率[件/10,000体/日](``None`` で既定
            ``salient.COLLAPSE_PER_10K_PER_DAY``=3.0)。5,000 体・1 日では期待値 1.5 件なので
            **引かない日がある**(P(0)=22%)。感度試験・結線テストで上げるための口。
        report_precondition: **D-113 ②(第267)** 通報の前提「当該事象を知覚済み」(直近 5 tick に
            自分のセルの B4 に顕著行為の行が出た)を検査する(既定 True)。``False`` は従来どおり
            通報が必ず成功する挙動(=帰無腕・第266 以前の checkpoint ``ba01bd0b`` を再現)。
        leave_effect: **9a(D-112 ④)** 退去=所属解除(在店・待ち行列・会話を解く・活動欄「なし」なら次の tick に
            満了)。既定 True=欠陥の修正。``False`` は第301 以前の挙動(IDLE 化と会話相手の解除だけ=旧 golden)。
        queue_service: **D-113 ③(第268)** 満席で並んだ体を、席が空いた分だけ並んだ順に席へ
            入れて購入/食事を完了させる(既定 True)。``False`` は第267 以前の挙動(誰も捌かず
            15 tick で ``INTERRUPTED``)。既定の mock 5,000 では列が立たないので checkpoint 不変。
        sleep_suppression: **D-56 就寝抑止**(既定 True=ユーザー決定 (a))。``activity ==
            Activity.SLEEPING`` の個体の起床候補を、計画境界・顕著行為・会話ターン以外は
            アービタに入れない。``False`` は **D-56 前の挙動**(=ablation の帰無腕)。
            エンジンは tick 0 で全員を ``SLEEPING`` に置く(``resolve.initialize``=世界内
            00:00 の種。**週次表があるランは D-62 (b) が 0:00 の活動から立て直す**)ので、
            **深夜だけを回す短いラン**は既定のままだと呼が 0 になる。
            LLM 配管そのものを見るテスト(艦隊・テープ・パーサ)は ``False`` で回す。
        plan_sleep: **D-62 就寝は計画の実行**(既定 True=ユーザー決定 (a)+(b))。
            (a) 計画境界のうち**就寝境界**(``WakeCondition.PLAN_SLEEPING``)はエンジンが
            実行する——``activity=SLEEPING``(就寝地に居なければ歩かせて着いたら寝る)+
            **その境界では LLM を呼ばない**(候補にしない)。非就寝の計画境界は逆に
            ``SLEEPING`` の体を起こしてから呼ぶ。(b) 週次表(W17)があるランは tick 0 の
            ``activity`` を**0:00 時点の活動**から立てる(``resolve.set_initial_activity``)。
            ``False`` は **D-62 前の挙動**(=帰無腕。就寝境界も LLM に判断させ、tick 0 は
            全員 ``SLEEPING``)。週次表を持たない合成世界/mock 日課でも (a) は効く
            (mock 日課の第 5 境界=就寝)。
        plan_executor: **D-66 計画実行層**(``engine.presence.PlanExecutor``・既定 True)。
            W17 週次表を在圏ブロックに畳み、到着・退出・就寝・起床を**エンジンが実行する**。
            有効になるのは「W16 母集団 + W17 週次表があるラン」だけ(合成世界・
            ``--no-population`` では静かに休む=既存の下限対照は無傷)。
            ``False`` = **帰無腕**(rail の乱数 12% + D-61 帰りの便 + D-62 の run.py 発火=
            現行挙動。checkpoint も 1 バイト変わらない)。
        exit_mode: 退出の実行形(設計書 §10-3)。既定 ``"immediate"``(即時 ``rail_depart``)・
            **9a(D-115 ①)** ``"walk_to_platform"``=その体の路線のホームへ歩いて受容関数を通して乗る
            (上限 ``intent_max_ticks``・超えたら即時)。``"board_intent"`` は予約(``NotImplementedError``)。
        attendance_rate: 出勤率(D-67 (b)・expedient E6・既定 1.0)。通勤・通学の体のうち
            ``1 - rate`` の割合を ``_mix64(agent_id)`` の決定論でその日「終日域外」にする。
            **1.0 では 1 ビットも変わらない**。
        outside_suppression: **D-66 域外抑止**(既定 True)。``transit_state != 0``
            (域外滞在・乗車中)の体の起床候補をアービタに入れない——舞台に居ない体は
            B0-B6 の描画欄が全て空で、プロンプトが「どこにも居ない」になるため。
            D-56 の就寝抑止と同型だが**例外を作らない**(計画境界・顕著行為・会話ターンも落ちる)。
            ``False`` = **帰無腕**(``--no-outside-suppression``)。**計画実行層が立つラン
            でだけ効く**(``--no-plan-executor`` の帰無腕は現行挙動のまま=checkpoint 不変)。
        geometry: **C9 位置幾何の腕**(G1/G2・2026-09-17 ユーザー決定)。
            ``"node"``(既定)= 現行の 1 tick=1 ノード(実資産で ≒2.3 km/h)。
            **checkpoint も manifest 既存欄も 1 バイト動かない**。
            ``"edge"`` = 体が辺上の連続位置(``edge_id`` / ``edge_s`` / 向き=
            ``path_next_node``・+8 B/体)を持ち、1 tick に
            「希望速度 ``Uniform(1.00,1.60)`` m/s × Kladek 減速 × 60 s」の距離だけ進む。
            ``xy`` は両端ノードの線形補間・セルは近い方の端点・密度段は人/m² の
            Fruin LOS 段。``GEOMETRY_MODES`` 以外は ``ValueError``。
        area_source: **C9c-1 歩行可能面積の出所**(G8 (b)・D-84 (c)・2026-09-17)。
            ``"legacy"``(既定)= 現行の「W10 街路点数 × 6.25 m²・床 1,500 m²」
            (**expedient**・6.25 は 2.5 m 格子の目の面積)。**checkpoint も manifest 既存欄も
            1 バイト動かない**。``"plateau"`` = ``c9c_walkable_area.parquet``(PLATEAU tran の
            歩道部の面 + OSM 線 × 道路構造令の既定幅員・``tools/build_geo/walkable_area.py``)
            を読み、**密度の分母を 1 本だけ差し替える**(``PerceptionAssets.walkable_area_m2``
            = B4 の LOS 段・``ChangeDetector`` の起床条件 (i)・``EdgeGeometry`` の Kladek 減速が
            **同じ値**を見る)。読み込みは起動時 1 回で tick ループに新しい逐次ループを作らない。
        seat_area_eatery_m2 / seat_area_retail_m2: **1 人あたり床面積[m²]の感度腕**
            (C9c-1・R-8 ③)。``None``(既定)= ``processes.crowd.SEAT_AREA_M2``
            (飲食 2.0 / 物販その他 4.0)のまま=**1 バイトも変わらない**。法定の帯は
            ``world.assets.SEAT_AREA_M2_FIRE_CODE``(消防法施行規則 1 条の 3・飲食 **3.0** /
            物販 **4.0**)と ``SEAT_AREA_M2_BUILDING_NOTICE``(建告1441・飲食 1.43 / 売場 2.0)。
            ``eatery`` は ``food``/``nightlife``、``retail`` は**表に無い全カテゴリ**に効く。
        activity: **行為と活動の二層の活動層**(段 2・D-116・既定 True=``--activity on``)。
            立つのは ``vocab_version="v3"`` のときだけ(v1/v2 では活動欄が来ない=**実質無効**で
            checkpoint も 1 バイト動かない)。立つと ① ``activity_until``/``activity_kind`` の
            2 欄(+5 B/体)② 満了入口(``WakeCondition.ACTIVITY_EXPIRY``)③ 活動中は場所の変化
            (CELL_BLOCK)で起こさない ④「移動 対象: あたり」の近傍歩行 ⑤ 同セルの B4b に
            活動の 1 行 ⑥ 休んでいる体の疲労回復(10 tick ごとに −1)⑦ 活動の文を checkpoint に
            混ぜる。``False``/``"off"`` は抑止も満了も無効=現行の挙動。
        eatery: **飲食店の切替口**(段 1b・D-96 nightlife (b)・``World.eatery_mask``)。
            ``"food"``(既定)=現行の ``cat`` の価格帯「飲食」(実資産 823 件)=**checkpoint は
            1 バイトも動かない**。``"place_food"``=W17 の場所語「飲食店」と同じ集合(``food`` ∨
            ``nightlife`` のうち subcat が club/karaoke/sauna/net_cafe でないもの・実資産 1,042 件)。
            価格(``poi_price``)は動かさない。``EATERY_MODES`` 以外は ``ValueError``。
        chooser: **選び手**(段 2a・D-114 (a)・``engine.chooser``)。購入/食事/並ぶの対象を
            「現在セルの営業中・意図に合う POI の候補」→ 選び手の分布 → 抽選
            (``core.rng.stream(seed, "engine.chooser", tick, agent_id)``)で決める。既定
            ``"nearest"``=可視(W8 の視点数)の降順 → POI 索引(憲法⑥の宣言つき暫定)。
            それまでの「現在セルの最小 id」から**既定 checkpoint が動く**(版の台帳
            ``docs/bench/analysis/intent-chooser-2026-09-28/``)。
        poi_target: **対象の決め方の切替口**(親決定 Q13)。``"candidates"``(既定)=上の
            候補 → 選び手 / ``"legacy"``=段 2a 前の「現在セルの最小 id」(``commit._poi_in_cell``)
            をそのまま通す=**旧 checkpoint(02bd0312 等)を再現する**。``legacy`` では
            ``target_resolution`` を数えない(空 dict)。**段 2b の移動の行き先も従来のまま**。
        move_search_radius: **段 2b**(行き先を対象欄から・D-112 ②)のカテゴリ語の近傍探索で
            見る近いセルの数(現在セル・見えている POI の次に ``cell_dist`` の昇順で R 個・宣言・
            既定 5)。0 なら近傍探索をしない。
        mock_move_target_p: 既定 mock(語彙 v3)の移動の対象にカテゴリ語か B2 に見えている名を
            出す確率(段 2b の経路を mock で通す腕・既定 0=golden 不変)。
        intent_max_ticks: **段 2c(意図の保持・D-112 ①・D-114 案 A)** の上限[tick]。購入/食事/
            並ぶ/会話/就寝の対象が現在セルに無く解決できるとき、行為を意図(SoA 4 欄・既定で確保)に
            保存して目的地つき移動を始め、着いたら LLM を呼ばずに実行する。歩いてこの tick を
            超えたら ``TOO_FAR``(宣言 60・expedient・感度腕 30/120)。意図の層は**活動層が立ち
            (語彙 v3・``activity=True``)かつ ``poi_target="candidates"``** のランだけ働く
            (v1/v2・``--activity off``・``legacy`` は欄を確保するだけ=挙動は段 2b のまま)。
        mock_out_of_cell_target_p: 既定 mock(語彙 v3)の購入/食事/並ぶの対象に B2 の「見えるもの」
            の名(括弧内の店名があればそれ)を出す確率(段 2c の経路を mock で通す腕・既定 0)。
        familiarity: **4 段目(記憶の先行部品=M13 訪問+M17 露出)**。``True``/``"on"`` で体×K 行の
            親しみの表(``AgentState(familiarity_columns=True)``・16 B/行)を確保し、訪問(購入/食事の
            成立)・看板の露出(B2 に看板行が載った)・場所(セルに入った回)を書く。**本段では誰も
            読まない**。既定 ``False``=表を確保しない=**既定 checkpoint 不変**。
        familiarity_k: 体あたりの行数(既定 ``FAMILIARITY_K``=64・宣言・感度 32/128)。
        hunger_model: **5 段目 5a(D-118 K1〜K9)**。``"energy"`` で体のエネルギー収支
            (``AgentState(energy_columns=True)``・+16 B/体・``engine.energy``)=体重と EER を抽選し、
            毎 tick 活動の METs で消費・食事/軽食/飲料で摂取・``hunger`` は語の段の写し・B5 は語・
            範囲外の食事は W17 の食事行か既定の時刻。``"v1"``(**ライブラリの既定**)は旧規則
            (+1/30 分・購入/食事で −4)=**旧 checkpoint をそのまま再現**。CLI と ``cli.run`` の既定は
            ``energy``(``cli.CLI_DEFAULT_HUNGER_MODEL``・K5 (a))。
        energy_rate: 消費の式(``"eer"``=K1 (c)・既定 / ``"bmr"``=K1 (a) の感度腕)。``hunger_model=
            "energy"`` のときだけ効く。
        meal_sleep_defer: **第2波 §2B 項 1(Q34 (b))** ``"off"``(**既定**=旧)/ ``"on"``=範囲外の既定の食事時刻に
            W17 で就寝中の体は、起床の時刻(窓の中なら)へ遅らせて食べる(``engine.energy.OutOfAreaMeals``)。
            ``hunger_model="energy"`` のときだけ効く。
        home_meal: **第2波 §2B 項 2(Q35 (a))** ``"off"``(**既定**=旧)/ ``"plan"``=W17 の自宅の食事行(自宅が
            範囲内の体)を、行の開始に自宅に居て起きていれば「予定の実行」として食べさせる(金と物は動かさない・
            照合の分布と店の集計から外す・``engine.energy.HomeMeals``)。``hunger_model="energy"`` のときだけ効く。
        hunger_words: **第2波 §2B 項 3(Q31 (b))** B5 の空腹の語。``"hungry"``(**既定**=旧=空腹以上だけ描く)/
            ``"all"``=満腹・ふつうも描く(``energy_columns`` のランだけ効く)。
        policy: **5 段目 5b(D-119 L5 (a))**。``"classical"`` で LLM(mock)を呼ばず、起床ごとに
            食事の門+ActivityChooser(社会生活基本調査の事前分布)から 5 ラベルの応答文を作る
            (``engine.classical.ClassicalPolicy``・語彙 v3 だけ)。既定 ``"mock"``=凍結の mock
            (**既定 checkpoint 不変**)。``llm`` の注入・再生・艦隊とは併用できない。
        activity_region: 事前分布の地域(``"kanto"``=関東大都市圏・既定 / ``"national"``=全国)。
        classical_social: **第2波 §2A 項 3-1(Q42 (b))** 方策 classical の交際・付き合い(符号 18)の相手。
            ``"acquaintance"``(既定)=B5 近接行の知人(生きている関係辺の相手)のうち A が最大の人・居なければ
            「なし・待つ」(関係 off のランでは会話を始めない)/ ``"near_first"``=旧(近接行の最初の人=見知らぬ人・
            関係 on は C10 8b の重みつき抽選)。``policy="classical"`` のときだけ効く。
        meal_gate: **第2波 §2A 項 4(Q48 (a))** 方策 classical の食事の門の確率の読み方。``"per_wake"``(**既定**=旧・
            起床ごと)/ ``"per_hour"``=1 時間あたりと読み、前回の門の後に範囲内で起きていた各 tick の語の段で
            ハザードを積算して換算(**第2波 §2B の規則**・体ごとの H 4 B/体・``engine.classical``)。既定の切り替えは食事の束の版上げで確認する(指示書 §8-2)。
        classical_habit_p / classical_tau: ``chooser="classical"`` の習慣の確率 p_h(宣言 0.5)と
            満足化の揺らぎ τ(宣言 1.0)。
        p_see_activity: **5 段目 5c(D-117・M1 (a)・M2 (b)・M4 (a))**。看板の注視ゲート p_see に掛ける
            活動の種別の乗数表(``perception.renderer.P_SEE_ACTIVITY_KINDS`` の鍵 → 乗数・欠けた鍵は 1.0・
            辞書か JSON 文字列)。実効 p_see=min(1, p_see × 乗数)。**p_see にだけ**掛ける(B2 の可視の行は
            変えない)=注視ゲートと親しみの表の露出(入った回)が変わる。既定 ``None``=全部 1.0=
            **描画バイトも checkpoint も 1 バイトも変わらない**。
        memory: **6 段目 6a(記憶 第 1 段の記録)**。``True``/``"on"`` で体 × N 行の記憶の表
            (``AgentState(memory_columns=True)``・実 25 B/行・宣言 32 B/行)を確保し、行動の成否・会話・
            気づき・強い看板(初見)を書く(``engine.memory``)。読み手は 6b の想起(下)。既定 ``False``=
            表を確保しない=**既定 checkpoint 不変**。
        memory_n: 体あたりの行数(既定 ``MEMORY_N``=128・宣言・感度 64/256)。
            **6b(想起)**: on のランは、各呼の描画で q(起床の級・セル・直前の結果・相手・対象)に ID で
            合う行を score 順に k 件(会話 3・他 2)想起し、B5 の最後に「記憶」の 1 行(≤60 tok)を載せる
            (テンプレ v1.2・テープ版 3 の ``recalled_rows``)。off は描画バイトが 1 バイトも変わらない。
        memory_tau: 想起の閾値 τ(A ≥ τ の行だけ想起・既定 ``RECALL_TAU``)。
        store_memory: **D-120 7a(店の評価の記憶)**。``True``/``"on"`` で体 × M 行の店の評価の表
            (``AgentState(store_memory_columns=True)``・実 23 B/行・宣言 24 B/行)を確保し、記憶の
            エピソード(購入/食事/並ぶの成否・看板の初見)から店の行を書く(``engine.store_memory``)。
            **``memory`` が on のランでだけ**使える(書き手がエピソードの書き手に乗る)。本段では誰も
            読まない。既定 ``False``=表を確保しない=**既定 checkpoint 不変**。
        store_memory_n: 体あたりの店の行数(既定 ``STORE_MEMORY_N``=32・宣言・感度 16/64)。
        store_sigma: 出どころ別の σ(辞書か JSON・既定 自分 1/伝聞 2/看板 4/ネット 2・感度腕)。
        store_decay: 減衰の形(``actr`` 既定・``ga``/``citysim`` は感度腕の口)。
        store_wom / store_signage: **D-120 7c(N8 の腕)**。口コミ(7b の聞き手への転写)と看板(N2 (iii))の
            書き手を使うか(既定 どちらも on・``"on"``/``"off"`` か bool)。店の記憶 on のランだけ効く。
        store_recall_scope: 7c: B5 の想起で店の行を候補にする入口(``all`` 既定・``conversation``=会話だけ=感度腕)。
        wom_source: **第2波 §2A 項 1(Q57 の確認)** 口コミの抽出の源。``"utterance"``(既定)=発話の欄(ひと言)だけ
            (いまの語彙 v3 にはひと言欄が無い=抽出 0)/ ``"reason-target"``=旧(v3 で理由欄+対象欄=内心が聞き手に
            漏れる欠陥・旧 golden の再現用)。店の記憶 on のランだけ効く。manifest ``wom.source``。
        relations: **C10 8a(関係辺)**。``True``/``"on"`` で体 × k 辺の関係の表(``AgentState(relation_columns=
            True)``・16 B/辺)を確保し、W16+W17 の機械的初期化と、記憶のエピソード(会話・手伝い)から辺を書く
            (``engine.relations``)。B5 近接行の「知人」の印に結線する(v1.4)。**``memory`` が on のランでだけ**。
            既定 ``False``=表を確保しない=**既定 checkpoint 不変**。
        rel_k / rel_tau / rel_d / rel_init_density: 辺の数(既定 15・感度 5/50)・閾値 τ_rel(既定 None=``rel_tenure_hash`` の版ごとの再逆算 v2 −2.322 / v1 −2.346・感度
            ±0.5)・減衰 d(既定 0.5・感度 0.25/0.75)・初期網の密度の腕(0.5/1.0/2.0)。
        conv_max_participants: **C10 8a(D-93 (d))の 3 人会話の口**。3 なら会話中の相手に話しかけた体が
            そのセッションに加わる(``talk_partner``=名指しした相手=主相手・参加者はセッション表)。既定 2=不変。
        rel_tenure_weeks: C10 8b(第299 Q89/Q90): 初期辺の在職期間 T_uv の上限[週](既定 13・感度 26)。
        rel_tenure_hash: **第2波 §2A 項 2** 初期辺の在職期間のハッシュの版。``"v2"``(既定)=同点の順のハッシュと
            独立な混ぜ合わせ / ``"v1"``=旧(元 id_u < 元 id_v の辺で同点の順と同じ値=在職の短い相手ほど選ばれる欠陥)。
            ``rel_tau`` を渡さない(``None``)ときの τ_rel は版ごとの再逆算値(``REL_TAU_BY_TENURE_HASH``: v2 −2.322・
            v1 −2.346=旧)。関係 on のランだけ効く。
        rel_invite / rel_acq_wake / rel_copresent: **C10 8b**(``relations`` が on のランだけ効く)。
            ``rel_invite``(既定 on)=名指しの無い会話の相手を関係辺の重み(内側 5 人 40%・次の 10 人 20%・残り
            40%・居る層で再正規化)+seed つき乱択で引く・2 m 内の知人を第一候補(偶然)・classical 方策の相手も
            同じ重み。``rel_acq_wake``(既定 on)=知人出現の起床(``WakeCondition.ACQUAINTANCE``・同一相手 60 分)。
            ``rel_copresent``(既定 off=第299 Q91)=同席の書き手(同セル・2 m 内・連続 5 分で 1 本・相手ごと
            1 日 1 本・表に居る相手だけ)。起点の診断行(招待/偶然/知人出現)は関係 on のランでいつも数える。
            想起優先の候補合成(N6)は選び手 ``classical`` のランだけ(``engine.store_choice``)。
        sim_days: **10a の複数日の口(mock 用)**。既定 1。2 以上では ``ticks`` を 1 日の tick 数にして、
            同じプロセスで状態を保存せずに T = 0〜``sim_days × 1 日の tick 数``−1 を続けて回す(再開=10d の
            先取りではない)。日の頭の初期化(A11)と日ごとの表の作り直し(10g)が無いので、2 日目からも
            **0 日目の表**(計画境界・食事の予定・営業時間・天気の実日・mock 日課)を繰り返し、時刻表と
            計画実行層のイベントは 0 日目の座標のまま(1 日目以降に新しい便・出入りは無い)。そのため
            合成世界(``world_dir=None``)・台帳なし・艦隊なし・再生でないランだけに限る(違えば止める)。
        start_sim_datetime: **10a(A1-1)の開始日の欄**(``datetime``・``date``・``"YYYY-MM-DD"``)。``None``
            (既定)は今までどおり ``DEFAULT_START_DATETIME + day_index 日``(気象の再生実日があればその日)。
            渡すと T=0 の世界内日時(プロンプトの日付)と暦の日付になる。``calendar_weekday="real"`` では必須。
        calendar_weekday: **10a の曜日の切替口**。``"day_index"``(既定)=今の約束(``day_index=0`` を月曜・
            祝日は見ない)/ ``"real"``=``start_sim_datetime`` の実の曜日と祝日(祝日は土休・曜日 7 日の表では
            日曜の行)。曜日・土休・祝日を引く 18 か所は暦の口(``engine.calendar.SimCalendar``)を通す。
        holiday_csv: 祝日 CSV の場所(既定 ``data/calendar/syukujitsu.csv``)。無ければ祝日を空にして警告 1 回。
            読んだ md5 を manifest の ``calendar.holiday_csv_md5`` に書く。
        school_holidays: 学校の長期休みの区間の一覧(``"YYYY-MM-DD:YYYY-MM-DD,…"`` か組の列)。開始日の検査で
            当たれば止める(``real``)/ 警告(``day_index``)。既定は空(表の中身は K7 の判断待ち)。
        response_delay: **10a(A9)の応答の遅れの切替口**(``None``=未指定は 1。再生ではテープの脇の meta の値と
            突き合わせて違えば止め、値の無い旧テープは 2 とみなす=検収後 P3)。``1``=艦隊/再生の到着の受け取りを①の
            直前に置き下限 ``max(t_apply, tick)``(発射 +1 tick で反映)/ ``2``=旧(受け取りは④′・下限
            ``tick + 1``=+2 tick)。旧い実 LLM テープの再生は ``2`` で回す。mock(``fleet=None`` かつ再生の
            到着が無い)はこの分岐を通らない=結果は動かない。

    Returns:
        ``RunResult``。
    """
    t_start = time.perf_counter()
    budget_mode_enum = BudgetMode.parse(budget_mode)
    # ---- 10a(A1・A1-1・A1-2・A1-3・A9): 暦の口・通しの時刻 T・応答の遅れ(世界を触る前に検査) ----
    calendar_weekday = check_weekday_mode(calendar_weekday)
    response_delay = _resolve_response_delay(response_delay, mode, replay)
    sim_days = int(sim_days)
    if sim_days < 1:
        raise ValueError(f"sim_days は 1 以上(いま {sim_days})")
    start_given = parse_start(start_sim_datetime)
    if calendar_weekday == "real" and start_given is None:
        raise ValueError("calendar_weekday='real' には start_sim_datetime(開始日)が要る(A1-1)")
    calendar = SimCalendar(
        start_given if start_given is not None
        else DEFAULT_START_DATETIME + timedelta(days=int(day_index)),
        tick_seconds=int(tick_seconds),
        weekday_mode=calendar_weekday,
        day_index=int(day_index),
        holidays=load_holidays(holiday_csv),
        school_holidays=parse_school_holidays(school_holidays),
    )
    tpd = calendar.ticks_per_day
    if sim_days > 1:
        if int(ticks) != tpd:
            raise ValueError(f"sim_days > 1 では ticks は 1 日の tick 数 {tpd}(いま {ticks})")
        _not_yet = [
            name for name, bad in (
                ("世界資産(world_dir)", world_dir is not None),
                ("台帳(ledger)", ledger is not None),
                ("艦隊(fleet)", fleet is not None),
                ("再生(replay)", mode == "replay" or replay is not None),
            ) if bad
        ]
        if _not_yet:
            raise ValueError(
                "sim_days > 1(10a の mock 用の口)は日の頭の初期化(A11・10g)の前なので "
                + "・".join(_not_yet) + " と一緒に使えない"
            )
    elif int(ticks) > tpd:
        raise ValueError(f"ticks は 1 日の tick 数 {tpd} 以下(複数日は sim_days で回す・いま {ticks})")
    total_ticks = int(ticks) if sim_days == 1 else sim_days * tpd
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
    world = world if world is not None else World.synthetic(n_cells=n_cells, seed=seed)
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
    # 検収後 P3: テープの脇の meta に応答の遅れを書く(再生で突き合わせる・テープの版と列は変えない)
    tape_writer = (TapeWriter(Path(tape_path), run_meta={"response_delay": int(response_delay)})
                   if tape_path is not None else None)
    conv = (ConversationManager(seed, max_participants=int(conv_max_participants))
            if conversations else None)
    schedule = synthesize(n_agents, seed, world.n_cells)
    pop = _resolve_population(population, world_dir, n_agents, seed, world.n_cells)
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
    if pop is not None:
        schedule = _schedule_with_population(
            schedule, pop, world.n_cells, keep_outside_home=plan_exec_on
        )
    R.initialize(agents, world, schedule, day_index=day_index, ledger=ledger)
    # ---- 5 段目 5a: 体のエネルギー収支(値を決める層・書き手は resolve) ----
    energy_layer: EnergyLayer | None = None
    if energy_on:
        _anc, _anc_md5 = load_anchors()
        _emodel = EnergyModel(
            _anc, _anc_md5, rate=energy_rate, minutes_per_tick=float(tick_seconds) / 60.0
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
        R.initialize_energy(agents, energy_layer, seed)
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
            day_index=day_index,
            tick_seconds=tick_seconds,
            calendar=calendar,  # 10a: #2・#3・#7・#10・#11・#20 は暦の口から
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
        presence.initialize()  # その時刻に在圏でない体を域外へ(I1 の分母)
        if runner is not None:
            runner.attach_presence(presence)  # hotel の母数・civic の引き込み候補

    # ---- 10a #1: T=0 の世界内日時(暦の開始日)。渡されたらその日・無ければ今までどおり
    # 「既定の開始日 + day_index」を気象の再生実日(D-W15)で置き換える(day_index モードの既定=今の値)。
    if start_given is not None:
        world_start = start_given
    else:
        world_start = DEFAULT_START_DATETIME + timedelta(days=int(day_index))
        if runner is not None and runner.replay_date:
            world_start = datetime.fromisoformat(runner.replay_date)
    calendar = calendar.with_start(world_start)
    #: 開始日の検査(real は違反で止める・day_index は警告だけ・祝日表の範囲外はどちらも止める)。
    #: 検収後 P1: 気象の再生実日へ置き換えた後の暦で走らせる(manifest の ``start_sim_datetime`` と同じ日を見る)。
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
        # 世界内日時 = 暦の口(10a #1)= ``world_start + T × tick_seconds``(tick_seconds=60 では
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
    #: 次 tick の起床候補へ**そのまま再投入**する(破棄禁止=憲法1)。
    fleet_deferred: list[tuple[int, int, int, int]] = []
    n_fleet_reinjected = 0
    n_fleet_resent = 0
    #: 繰り延べ中の個体(再送を数えるためだけの集合。呼数 L4 は**発射数**で数える)。
    fleet_waiting: set[int] = set()
    #: **再生モードの艦隊の代役**(D-58)。``observed_tick`` → その tick で「届く」項目。
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
    #: このランの 1 tick の呼数上限(``None`` なら L4 按分)。manifest の ``budget_per_tick``。
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
        # ---- D-62 (b): tick 0 の activity を W17 の 0:00 時点の活動から立てる ----
        # ``initialize`` は全員 SLEEPING(週次表の無い世界の既定)。ここで立て直す。
        if plan_sleep:
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
    # ---- 4 段目: 親しみの表(値を決める層・書き手は resolve.write_familiarity) ----
    _fam_renderer = getattr(perception, "renderer", None) if perception is not None else None
    _fam_has_renderer = _fam_renderer is not None and hasattr(_fam_renderer, "signage_exposures")
    fam_layer: FamiliarityLayer | None = (
        FamiliarityLayer(
            n_agents, int(familiarity_k), minutes_per_tick=float(tick_seconds) / 60.0,
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
        MemoryLayer(n_agents, int(memory_n), minutes_per_tick=float(tick_seconds) / 60.0)
        if memory_on
        else None
    )
    if (fam_layer is not None or mem_layer is not None) and _fam_has_renderer:
        _fam_renderer.signage_exposures = []  # 描画による露出の控え(tick ごとに取り出す)
    # ---- 記憶 第 1 段 6b: 想起の口(on のランだけ描画に差し込む・off は None=描画バイト不変) ----
    if mem_layer is not None:
        mem_layer.tau = float(memory_tau)
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
                minutes_per_tick=float(tick_seconds) / 60.0,
            )
    # ---- C10 8a: 関係辺(機械的初期化=W16+W17 の共在・書き手は記憶のエピソード・知人の結線) ----
    rel_layer = None
    if mem_layer is not None and relations_on:
        rel_layer = mem_layer.enable_relations(int(rel_k), tau=float(rel_tau), d=float(rel_d))
        _t_rel = time.perf_counter()
        _init = _rel_initial_edges(
            pop, weekly, n_agents, k=int(rel_k), day_index=int(calendar.table_weekday(0)),  # 10a #19
            density=float(rel_init_density),
            minutes_per_tick=float(tick_seconds) / 60.0, d=float(rel_d), tau=float(rel_tau),
            tenure_weeks=float(rel_tenure_weeks), tenure_hash=str(rel_tenure_hash),
        ) if pop is not None else None
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

    def _utter(agent_id: int, t_now: int, action: Any, comment: str, reason: str = "",
               parse: Any = None) -> None:
        """会話ターンの発話 1 回(``conv.utterance``)。6a: 記憶の会話の行と要旨(on のときだけ)。

        6b(第294 Q57 暫定): 要旨の源=ひと言が空/「なし」なら理由欄の先頭 40 字(語彙 v3)。
        7b(D-120 N3 (a)): 店の記憶 on のランだけ、発話(``wom_source``: 既定=ひと言だけ・旧=v3 で理由+対象)から店名と評価語を
        抽出し、**宛先**(会話の相手=``talk_partner``・セッションの参加者)の店の行へ伝聞として書く。
        """
        partner_before = int(agents.registry.talk_partner[int(agent_id)]) if wom_ex is not None else -1
        s = conv.utterance(agent_id, t_now, action=action, comment=comment)
        if mem_layer is not None:
            mem_layer.note_utterance(agents, int(agent_id), int(t_now), s, comment, reason)
        if wom_ex is not None and s is not None:
            tgt = getattr(parse, "target", None)
            text = wom_ex.utterance_text(
                vocab_version,
                comment=str(getattr(parse, "raw_comment", "") or comment or ""),
                reason=str(getattr(parse, "raw_reason", "") or reason or ""),
                target=str(getattr(tgt, "raw", "") or ""),
            )
            ex = wom_ex.extract(text, int(agents.registry.cell[int(agent_id)]))
            wom_ex.observe(ex)
            others = [int(p) for p in s.participants if int(p) != int(agent_id)]
            listener = partner_before if partner_before in others else (others[0] if others else -1)
            if store_wom_on:  # 7c の腕: 口コミ off=抽出は数えるが転写しない
                wom_hear(mem_layer.store, agents, int(t_now), listener, ex)
    #: 発射した呼の起床条件ごとの件数(起床の内訳・満了入口の列を含む)。
    calls_by_cond = np.zeros(N_WAKE_CONDITIONS_ALL, dtype=np.int64)

    result = RunResult(
        n_agents=n_agents,
        n_cells=world.n_cells,
        seed=seed,
        ticks=total_ticks,  # 10a: 回した通しの tick 数(1 日のランでは ``ticks``)
        world_source=world.assets.source,
        tape_path=str(tape_path) if tape_path is not None else "",
        mode=mode,
    )
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
    #  **target_hint**, **target_poi**, **activity**)
    # ``activity`` = 二層の段 2 の活動(``engine.activity.ActivityPayload``・v3 以外は None)。
    # ``target_person`` = LLM が「対象」欄に書いた個体 id(-1=名指しなし・C6 09-09)。
    # ``target_hint`` = 段0 辞書 v4 の対象ヒント索引(C9b G5・0=なし)。
    # ``target_poi`` = 「対象」欄が目印 POI に解決できたときの索引(C9b G6 a′・-1=なし)。
    pending: list[tuple[int, int, int, int, str, int, int, int, int, Any, Any]] = []
    #: この tick に適用した応答の (体, 行動コード, 活動)。``resolve.apply`` の後に活動層が書く。
    applied_activity: tuple[list[int], list[int], list[Any]] = ([], [], [])
    #: C9b G3/G4: この tick に LLM が言った**焦点の要求**(-1=なし)。使い回す 1 本の
    #: バッファ(毎 tick 触った行だけ戻す=個体数ぶんの確保は 1 回きり)。
    focus_request = (
        np.full(n_agents, int(FOCUS_NONE), dtype=np.int64) if attention_on else None
    )
    #: この tick に応答を適用した個体 → 行動コード(会話の被招待の返事を読むのに使う)。
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
    #: 世界内時刻の**時**別「起きている体」の延べ数と tick 数(起床率/時 の分子・分母)。
    awake_sum = [0] * 24
    awake_ticks = [0] * 24
    #: 5 段目 5a(診断): 内受容の跨ぎ(変数 3 × 上げ/下げ × 全体/起きて範囲内)。
    intero_cross = np.zeros((3, 2, 2), dtype=np.int64)

    def _receive_arrivals(tick: int, floor: int) -> int:
        """④′ 艦隊(と再生の代役)の到着を受け取る(10a・A9)。返り値=書式エラーの件数。

        届いた応答は ``max(t_apply, floor)`` で ``pending`` へ入る。``response_delay=1``(既定)は①の直前で
        ``floor=tick``(=発射 +1 tick の①で反映)、``2`` は旧の位置(②〜会話ターン起床の後)で
        ``floor=tick + 1``(=+2 tick)。mock(``fleet_bridge is None`` かつ ``replay_inbox`` が空)は何もしない。
        """
        n_err = 0
        if fleet_bridge is None and replay_inbox:
            # ---- ④′-r 再生モードの「到着」(D-58)。**艦隊経路と同じ位置・同じ扱い** ----
            # 逐次ループ宣言: この tick に届く件数ぶん(本番の poll と同じ件数)。
            t0 = time.perf_counter()
            for is_deferred, item in replay_inbox.pop(tick, ()):
                if is_deferred:
                    fleet_deferred.append(item)
                    continue
                res = item
                fleet_waiting.discard(int(res.agent_id))
                pending.append((
                    max(res.t_apply, floor), res.wake_class, res.agent_id,
                    res.condition, res.text, res.action_code, _target_person(res.target),
                    *_pending_extra(res),
                ))
                if not res.format_ok:
                    n_err += 1
                if conv is not None and res.condition == int(WakeCondition.CONVERSATION_TURN):
                    _utter(res.agent_id, tick, res.parse.action, res.parse.comment,
                           res.parse.reason, res.parse)
            phase["llm"] += time.perf_counter() - t0
        if fleet_bridge is not None:
            t0 = time.perf_counter()
            if fleet_wait_s > 0.0 and fleet_bridge.client.outstanding:
                fleet_bridge.client.wait_idle(timeout=fleet_wait_s)
                phase["fleet_wait"] += time.perf_counter() - t0
                t0 = time.perf_counter()
            for res in fleet_bridge.poll(now_tick=tick):
                if isinstance(res, FleetDeferred):
                    fleet_deferred.append(
                        (
                            int(res.call.agent_id),
                            int(res.call.condition),
                            int(res.call.wake_class),
                            int(res.call.wake_since),
                        )
                    )
                    continue
                fleet_waiting.discard(int(res.agent_id))
                # t_apply = 起床 + δ_perc + δ_think(§2.4)。到着が遅れたぶんは
                # **破棄せず**この tick 以降へ(締切超過=繰り延べアービタの趣旨)。
                t_apply = res.tick + delta_think_ticks(res.lane, tick_seconds)
                pending.append((
                    max(t_apply, floor), res.wake_class, res.agent_id,
                    res.condition, res.text, res.action_code, _target_person(res.target),
                    *_pending_extra(res),
                ))
                if not res.format_ok:
                    n_err += 1
                if conv is not None and res.condition == int(WakeCondition.CONVERSATION_TURN):
                    _utter(res.agent_id, tick, res.parse.action, res.parse.comment,
                           res.parse.reason, res.parse)
            phase["llm"] += time.perf_counter() - t0
        return n_err

    # 逐次ループ宣言1: tick 数ぶん(10a: ``tick`` は通しの時刻 T・``td`` はその日の中の tick)
    for tick in range(total_ticks):
        td = tick % tpd  # 日の中の時刻で引く表(計画境界)はこれで引く。1 日のランでは td == tick
        R.advance_body(agents, tick, energy_layer)
        if classical_policy is not None:  # 第2波 §2A 項 4: per_hour の門の「範囲内で起きていた分」(他の腕は no-op)
            classical_policy.accrue_awake()
        # ---- 5 段目 5a(K9 (a)): 範囲外の食事(W17 の食事行の開始・既定の時刻に域外に居る体) ----
        if energy_layer is not None and energy_layer.out_of_area is not None:
            if meal_sleep_defer == DEFAULT_MEAL_SLEEP_DEFER:
                _ea, _es, _ef = energy_layer.out_of_area.due(tick, agents.registry.transit_state)
                if _ea.size:
                    R.energy_out_of_area_meal(agents, energy_layer, _ea, _es, _ef, tick)
            else:  # 第2波 §2B 項 1: 起床時に遅らせた既定の食事を含む
                _ea, _es, _ef, _ed = energy_layer.out_of_area.due_with_deferred(
                    tick, agents.registry.transit_state
                )
                if _ea.size:
                    R.energy_out_of_area_meal(agents, energy_layer, _ea, _es, _ef, tick, deferred=_ed)

        # ---- ⓪a 世界過程(昼夜・天候・鉄道・営業時間・混雑場・断面交通) ----
        # 流れ(B4 の「流れ方向」欄)を作るのが混雑場なので、**⓪ の前**に置く。
        # 親指示は「⓪ の直後」だったが、それだと同じ tick の流れが描画に載らない(報告済み)。
        if runner is not None:
            runner.step(tick)

        # ---- ⓪a-2 計画実行層(D-66): 到着・退出(§3)。世界過程と同じ位置で回す ----
        if presence is not None:
            t0 = time.perf_counter()
            _pres0 = int(presence.n_arrivals) + int(presence.n_departures)
            presence.step(tick)
            layer_counts[(tick * tick_seconds // 3600) % 24, 0, _ENTRANCE_PLAN] += (
                int(presence.n_arrivals) + int(presence.n_departures) - _pres0
            )
            # 9a: 歩いて乗る退出の体の活動=目的地つき移動・到着まで(段 2c の意図と同じ形)
            if act_layer is not None and presence.walk_started_now.size:
                act_layer.force_arrival(agents, presence.walk_started_now, tick, count=False)
            phase["presence"] += time.perf_counter() - t0

        # ---- ⓪ 知覚の tick 前計算(セル配列+B4 描画欄・**1 tick 1 回**) ----
        # 顕著行為(salient_events)は人物③(第2陣)が入るまで空。騒音段は
        # ``world.noise_stage_for_tick``(W10 静的昼夜場 or 動的上書き)を**1 本**渡し、
        # 描画と変化検出が同じ値を見るようにする。
        field_rows = None
        if perception is not None:
            perception.prepare_tick(
                tick,
                salient_events=None if runner is None else runner.salient_events,
                flow=None if runner is None else runner.flow,
                noise_stage=world.noise_stage_for_tick(tick, tick_seconds),
                queues=None if runner is None else runner.queue_rows(3),
                # 二層の段 2: 同セルの活動の 1 行の材料(層が無いランでは渡さない=バイト不変)
                **(
                    {"activity_rows": act_layer.cell_rows(agents, tick)}
                    if act_layer is not None
                    else {}
                ),
            )
            field_rows = perception.b4_field_rows

        # ---- ④′(10a・A9 の新しい位置): 艦隊/再生の到着の受け取りと待ちを①の直前で ----
        # 下限 ``max(t_apply, tick)``=前の tick に発射した呼はこの tick の①で反映(+1 tick)。
        n_parse_errors_fleet = _receive_arrivals(tick, tick) if response_delay == 1 else 0

        # ---- ① 前 tick までに届いた応答を apply_key 昇順で適用(§2.4) ----
        t0 = time.perf_counter()
        llm_intents = C.IntentBatch.empty()
        n_undefined = 0
        applied_activity = ([], [], [])
        if pending:
            due = [p for p in pending if p[0] <= tick]
            pending = [p for p in pending if p[0] > tick]
            if due:
                t_apply = np.fromiter((p[0] for p in due), dtype=np.int64, count=len(due))
                ev_class = np.fromiter((p[1] for p in due), dtype=np.int64, count=len(due))
                ag = np.fromiter((p[2] for p in due), dtype=np.int64, count=len(due))
                cond = np.fromiter((p[3] for p in due), dtype=np.int64, count=len(due))
                ak = apply_key_array(salt, t_apply, ag)
                order = np.lexsort((ag, ak, ev_class, t_apply))
                # 行動コードは④(呼の時点)で正典パーサが決めている(二重パースしない)
                codes = np.fromiter(
                    (due[int(i)][5] for i in order),
                    dtype=np.int64,
                    count=order.size,
                )
                n_undefined = int(np.count_nonzero(codes == C.UNDEFINED_ACTION))
                n_undefined_total += n_undefined
                tgt_person = np.fromiter(
                    (due[int(i)][6] for i in order), dtype=np.int64, count=order.size
                )
                # C9b: 対象ヒント(辞書 v4)と目印 POI。腕が立っていないランでは
                # 全行 0 / -1 なので ``intents_from_responses`` へは渡さない(=バイト不変)。
                tgt_hint = np.fromiter(
                    (due[int(i)][7] for i in order), dtype=np.int64, count=order.size
                )
                tgt_poi = np.fromiter(
                    (due[int(i)][8] for i in order), dtype=np.int64, count=order.size
                )
                agents_in_order = ag[order]
                if norm_meter is not None:
                    norm_meter.observe_actions(tick, agents_in_order, codes)  # 第308 D-107 (a)(読むだけ)
                # 二層の段 2: 活動(v3 の応答だけ)と「あたり」の行き先
                payloads = [due[int(i)][9] for i in order]
                # 段 2a: 対象(``Target``)=購入/食事/並ぶの候補の絞り込みが読む
                parsed_targets = [due[int(i)][10] for i in order]
                move_dest: np.ndarray | None = None
                if act_layer is not None:
                    applied_activity = (
                        agents_in_order.tolist(), codes.tolist(), payloads
                    )
                    wmask = np.fromiter(
                        (p is not None and p.wander for p in payloads),
                        dtype=bool, count=order.size,
                    ) & (codes == C.ACT_MOVE)
                    if wmask.any():
                        move_dest = np.full(order.size, -1, dtype=np.int64)
                        move_dest[wmask] = act_layer.wander_destinations(
                            agents_in_order[wmask],
                            np.asarray(agents.registry.cell)[agents_in_order[wmask]],
                            tick,
                        )
                # 個体 → (行動コード, **LLM が名指しした**対象)。会話の承諾/相互指名の判定に使う
                # (エンジンが解決した対象ではない=「誰に向けた返事か」は名指しにしか無い)。
                applied_now = {
                    int(agents_in_order[k]): (int(codes[k]), int(tgt_person[k]))
                    for k in range(order.size)
                }
                # ---- ①-b 会話: **返事待ちの解決を Phase C より前に**(層2 中-1) ----
                # 被招待 B の承諾「会話 対象: P-A」を intent のまま Phase C へ流すと、
                # A は招待して CONVERSING なので ``_apply_talk`` が PARTNER_BUSY を書き、
                # B の「直前の結果」(B6)に**偽の失敗**が載る。承諾はここで消費し、
                # B の行を intent から外す(承諾は新しい招待ではない)。
                consumed = _settle_pending_invites(
                    conv, agents, tick, agents_in_order, codes, tgt_person, R, np,
                    attention_on,
                )
                keep = (
                    np.array(
                        [int(a) not in consumed for a in agents_in_order.tolist()], dtype=bool
                    )
                    if consumed
                    else np.ones(order.size, dtype=bool)
                )
                llm_intents = C.intents_from_responses(
                    agents, world, space, tick, agents_in_order[keep], cond[order][keep],
                    codes[keep],
                    home_cell=schedule.home_cell, work_cell=schedule.work_cell,
                    school_cell=(
                        getattr(schedule, "school_cell", None)
                        if (attention_on or v3_hints)
                        else None
                    ),
                    target_person=tgt_person[keep],
                    # 語彙 v3 は「対象: 自宅/職場/学校」の対象ヒントを運ぶ(v1/v2 は従来どおり)
                    target_hint=tgt_hint[keep] if (attention_on or v3_hints) else None,
                    target_poi=tgt_poi[keep] if attention_on else None,
                    stats=talk_stats, run_salt=salt,
                    vocab_version=vocab_version,
                    move_dest=None if move_dest is None else move_dest[keep],
                    targets=[t for t, k in zip(parsed_targets, keep.tolist()) if k],
                    poi_resolver=poi_resolver,
                    intent_hold=intent_layer,
                    talk_chooser=rel_layer,
                )
                # ---- C9b G3/G4: 焦点の要求を 1 本のバッファへ散らす ----
                if focus_request is not None:
                    focus_request[:] = int(FOCUS_NONE)
                    kept_agents = agents_in_order[keep]
                    if kept_agents.size:
                        focus_request[kept_agents] = C.focus_codes(
                            tgt_hint[keep], tgt_person[keep], tgt_poi[keep], int(agents.n)
                        )
            else:
                applied_now = {}
                if focus_request is not None:
                    focus_request[:] = int(FOCUS_NONE)
        else:
            applied_now = {}
            if focus_request is not None:
                focus_request[:] = int(FOCUS_NONE)
        phase["phase_a"] += time.perf_counter() - t0

        # ---- ② 変化検出(P6) ----
        t0 = time.perf_counter()
        det = detector.detect(world, agents, tick, field_rows=field_rows)
        _count_intero_crossings(det, agents, intero_cross)
        R.apply_detection(agents, world, det)
        d_agent, d_cond, d_class = det.candidates()
        # ---- 二層の段 2: 活動中は場所の変化で起こさない+満了入口 ----
        if act_layer is not None:
            if intent_layer is not None:
                # 段 2c: 意図を持つ体(歩いている・着いた)は場所の変化で起こさない(件数を数える)
                d_agent, d_cond, d_class = intent_layer.suppress_wakes(
                    agents, tick, d_agent, d_cond, d_class
                )
            d_agent, d_cond, d_class = act_layer.suppress_cell_block(
                agents, tick, d_agent, d_cond, d_class
            )
            e_agent, e_cond, e_class = act_layer.expiry_candidates(agents, tick)
            if intent_layer is not None:
                # 段 2c: 着いた体の到着満了は LLM を呼ばない(エンジンが意図の行為を実行する)
                e_agent, e_cond, e_class = intent_layer.suppress_wakes(
                    agents, tick, e_agent, e_cond, e_class
                )
        else:
            e_agent = np.empty(0, dtype=np.int64)
            e_cond = np.empty(0, dtype=np.int8)
            e_class = np.empty(0, dtype=np.int64)
        phase["detect"] += time.perf_counter() - t0

        # ---- 計画境界の起床候補 ----
        lo, hi = int(b_start[td]), int(b_start[td + 1])  # 10a: 日の中の tick で引く
        if hi > lo:
            p_agent = b_agent[lo:hi]
            p_cond = b_cond[lo:hi]
            # ---- D-62 (a): 就寝境界は**エンジンが実行する**(LLM を呼ばない) ----
            # 非就寝の境界は逆に「起こしてから呼ぶ」(呼が繰り延べ・抑止で落ちても起きる)。
            if plan_sleep:
                to_bed = p_cond == int(WakeCondition.PLAN_SLEEPING)
                # 5b 層の記録: 就寝境界はエンジンが実行する(System 1=予定で呼ばない)
                layer_counts[(tick * tick_seconds // 3600) % 24, 0, _ENTRANCE_PLAN] += int(
                    np.count_nonzero(to_bed)
                )
                if presence is not None:
                    # **D-66**: 発火元は計画実行層(同じ位置・同じ resolve の口)。
                    # 就寝地の既定は層が持つ ``home_cell``(域外常住は −1 のまま=職場で寝ない)。
                    t0 = time.perf_counter()
                    presence.step_plan_boundaries(tick)
                    phase["presence"] += time.perf_counter() - t0
                    if to_bed.any():
                        p_agent = p_agent[~to_bed]
                        p_cond = p_cond[~to_bed]
                else:
                    if to_bed.any():
                        got = R.begin_planned_sleep(
                            agents, world, p_agent[to_bed], b_cell[lo:hi][to_bed], tick,
                            schedule=schedule,
                        )
                        for k, v in got.items():
                            sleep_counts[k] = sleep_counts.get(k, 0) + int(v)
                        p_agent = p_agent[~to_bed]
                        p_cond = p_cond[~to_bed]
                    if p_agent.size:
                        sleep_counts["woke"] = sleep_counts.get("woke", 0) + R.wake_from_plan(
                            agents, p_agent
                        )
            p_class = np.fromiter(
                (int(WAKE_CONDITION_CLASS[int(c)]) for c in p_cond),
                dtype=np.int64,
                count=p_cond.size,
            )
        else:
            p_agent = np.empty(0, dtype=np.int64)
            p_cond = np.empty(0, dtype=np.int8)
            p_class = np.empty(0, dtype=np.int64)

        # ---- 第2波 §2B 項 2(Q35 (a)): 範囲内の自宅の食事行=予定の実行(計画境界の起床の後=
        # 行の境界で起こされた体は起きている)。起床は足さない。既定(off)は何もしない ----
        if energy_layer is not None and energy_layer.home_meals is not None:
            _hr = agents.registry
            _ha, _hs = energy_layer.home_meals.due(tick, _hr.transit_state, _hr.cell, _hr.activity)
            if _ha.size:
                R.energy_home_meal(agents, energy_layer, _ha, _hs, tick)

        # ---- 会話ターン起床(行動契約書 §3・不応期0)----
        if conv is not None:
            c_agent, c_cond, c_class = conv.wake_candidates(tick)
        else:
            c_agent = np.empty(0, dtype=np.int64)
            c_cond = np.empty(0, dtype=np.int8)
            c_class = np.empty(0, dtype=np.int64)

        # ---- 顕著行為の到達(起床条件 (i)・知覚契約書 §6)----
        # **アービタを通す**=顕著行為由来の呼も L4 の予算の中に入る(呼の抜け道を作らない)。
        if runner is not None:
            s_agent, s_cond, s_class = runner.salient_wake_candidates(tick)
        else:
            s_agent = np.empty(0, dtype=np.int64)
            s_cond = np.empty(0, dtype=np.int8)
            s_class = np.empty(0, dtype=np.int64)

        # ---- ④′ 艦隊からの到着(前 tick 以前に発射した分)・**非ブロッキング** ----
        # ③ の前に置く: 繰り延べになった呼をこの tick の起床候補へ合流させるため。
        # 10a(A9): 既定(``response_delay=1``)は①の直前で受け取り済み。``2``(旧・旧テープの再生用)だけ
        # ここ(旧の位置)で受け取り、下限 ``max(t_apply, tick + 1)``(=+2 tick)で ``pending`` へ入れる。
        if response_delay == 2:
            n_parse_errors_fleet = _receive_arrivals(tick, tick + 1)

        # ---- 艦隊の繰り延べを起床候補へ再投入(不応期は免除・親決定 (a)・09-09) ----
        if fleet_deferred:
            f_agent = np.fromiter((x[0] for x in fleet_deferred), dtype=np.int64,
                                  count=len(fleet_deferred))
            f_cond = np.fromiter((x[1] for x in fleet_deferred), dtype=np.int8,
                                 count=len(fleet_deferred))
            f_class = np.fromiter((x[2] for x in fleet_deferred), dtype=np.int64,
                                  count=len(fleet_deferred))
            f_since = np.fromiter((x[3] for x in fleet_deferred), dtype=np.int64,
                                  count=len(fleet_deferred))
            # 「答えが来なかった」呼は起床の抑止対象ではない=張った不応期を戻す。
            R.clear_refractory(agents, f_agent, f_cond)
            n_fleet_reinjected += len(fleet_deferred)
            fleet_deferred.clear()
        else:
            f_agent = np.empty(0, dtype=np.int64)
            f_cond = np.empty(0, dtype=np.int8)
            f_class = np.empty(0, dtype=np.int64)
            f_since = np.empty(0, dtype=np.int64)

        # ---- 就寝抑止の例外印(D-56・ユーザー決定 (a)・09-10) ----
        # **源で決める**(条件では区別できない: 顕著行為も変化検出も ``CELL_BLOCK``)。
        # 計画境界 p / 会話 c / 顕著行為 s = 通す・変化検出 d = 落とす。
        # 艦隊の再投入 f は源を持ち帰れないので**条件**で判定する(会話ターン 0 と
        # ``PLAN_*`` 1-4 は通す)。顕著行為由来の再投入は ``CELL_BLOCK`` なので
        # 就寝中なら落ちる(**過剰抑止をここに明記**・実害は「答えの返らなかった呼を
        # 寝ている間は蒸し返さない」だけ)。
        f_exempt = f_cond.astype(np.int64) <= int(WakeCondition.PLAN_TRANSIT)

        # ---- 9a: 歩いて乗る退出の体は場所の変化・到着満了・計画境界で起こさない(意図保持と同じ・既定は通らない) ----
        if presence is not None and presence.exit_mode == "walk_to_platform":
            d_agent, d_cond, d_class = presence.suppress_walker_wakes(d_agent, d_cond, d_class)
            p_agent, p_cond, p_class = presence.suppress_walker_wakes(p_agent, p_cond, p_class)
            e_agent, e_cond, e_class = presence.suppress_walker_wakes(e_agent, e_cond, e_class)

        # ---- C10 8b: 同席の書き手(腕)と知人出現の起床(R7 (a))=前 tick の終わりの位置で ----
        a_agent = None
        if rel_layer is not None and (rel_layer.copresent_on or rel_layer.acq_wake_on):
            t0 = time.perf_counter()
            if rel_layer.copresent_on:
                rel_layer.copresent_step(agents, tick)
            if rel_layer.acq_wake_on:
                _elig = np.ones(n_agents, dtype=bool)
                if sleep_suppression:
                    _elig &= np.asarray(agents.registry.activity) != int(Activity.SLEEPING)
                if outside_suppression and plan_exec_on:
                    _elig &= np.asarray(agents.registry.transit_state) == 0
                a_agent, a_cond, a_class = rel_layer.acquaintance_candidates(agents, tick, _elig)
                if a_agent.size:
                    rel_layer.stats["acq_agent_refractory"] += int(np.count_nonzero(
                        np.asarray(agents.registry.refractory_until)[a_agent, int(WakeCondition.ACQUAINTANCE)]
                        > int(tick)
                    ))
            rel_layer.wall["detect"] += time.perf_counter() - t0
        if a_agent is not None and a_agent.size:
            e_agent = np.concatenate([e_agent, a_agent])
            e_cond = np.concatenate([e_cond, a_cond.astype(e_cond.dtype)])
            e_class = np.concatenate([e_class, a_class.astype(e_class.dtype)])

        cands = WakeCandidates(
            np.concatenate([p_agent, d_agent, c_agent, s_agent, f_agent, e_agent]),
            np.concatenate(
                [p_cond, d_cond.astype(np.int8), c_cond, s_cond, f_cond, e_cond]
            ),
            np.concatenate([p_class, d_class, c_class, s_class, f_class, e_class]),
            np.concatenate(
                [
                    np.full(
                        p_agent.size + d_agent.size + c_agent.size + s_agent.size,
                        tick, dtype=np.int64,
                    ),
                    f_since,  # 再投入は**元の待ち始め**を保つ(昇格が巻き戻らない)
                    np.full(e_agent.size, tick, dtype=np.int64),  # 満了入口(二層の段 2)
                ]
            ),
            np.concatenate(
                [
                    np.ones(p_agent.size, dtype=bool),    # 計画境界(眠りから覚める境界を含む)
                    np.zeros(d_agent.size, dtype=bool),   # 変化検出(内受容・セル変化)
                    np.ones(c_agent.size, dtype=bool),    # 会話ターン
                    np.ones(s_agent.size, dtype=bool),    # 顕著行為
                    f_exempt,                             # 艦隊の再投入
                    np.zeros(e_agent.size, dtype=bool),   # 満了入口(就寝中は起こさない)
                ]
            ),
        )

        # ---- ③ 繰り延べアービタ(§6)+ 就寝抑止(D-56) ----
        t0 = time.perf_counter()
        asleep_now = np.asarray(agents.registry.activity) == int(Activity.SLEEPING)
        # ---- 起床率/時 の計測(D-62 の検証欄・a(h) との照合用) ----
        # 測る場所は**アービタの直前**(この tick の候補を絞る時点の「起きている割合」)。
        _h = (td // 60) % 24  # 10a: 日の中の tick から(1 日のランでは今と同じ)
        awake_sum[_h] += n_agents - int(np.count_nonzero(asleep_now))
        awake_ticks[_h] += 1
        asleep = asleep_now if sleep_suppression else None
        # D-66 域外抑止: 舞台に居ない体(域外滞在 2 / 乗車中 1)は呼ばない
        outside_now = np.asarray(agents.registry.transit_state) != 0
        # **層が立つランだけ**効かせる(帰無腕 ``--no-plan-executor`` は現行挙動のまま=
        # rail の乱数 12% で外に居る 600 体にも従来どおり呼が出る。checkpoint 不変の約束)。
        outside_mask = outside_now if (outside_suppression and plan_exec_on) else None
        decision = arbiter.step(
            tick, cands, agents.registry.refractory_until, asleep=asleep,
            outside=outside_mask,
        )

        phase["arbiter"] += time.perf_counter() - t0

        # ---- ④ LLM 呼(応答は pending_apply へ) ----
        t0 = time.perf_counter()
        sel = decision.selected
        # D-66 の監査点: **実際に発射した呼**のうち舞台に居ない体宛てだった数
        # (抑止が効いていれば 0。帰無腕では 53% 前後まで上がる=層2 指摘の実測)。
        if len(sel):
            n_outside_calls += int(
                np.count_nonzero(outside_now[sel.agent_id.astype(np.int64)])
            )
        n_parse_errors = 0
        if presence is not None and presence.exit_mode == "walk_to_platform" and len(sel):
            presence.note_calls(sel.agent_id)
        if rel_layer is not None and rel_layer.acq_wake_on and len(sel):
            _acq_sel = np.asarray(sel.condition, dtype=np.int64) == int(WakeCondition.ACQUAINTANCE)
            if bool(_acq_sel.any()):
                rel_layer.stamp_acquaintance(np.asarray(sel.agent_id, dtype=np.int64)[_acq_sel], tick)
        if len(sel):
            R.set_refractory(agents, sel.agent_id, sel.condition, tick, refractory_table)
            cell = agents.registry.cell
            act = agents.registry.activity
            hun = agents.registry.hunger
            last_act = agents.registry.last_action
            if fleet_bridge is None:
                # 逐次ループ宣言2: 選抜された呼数ぶん(平均 35/tick)
                for i in range(len(sel)):
                    a = int(sel.agent_id[i])
                    cls = int(decision.selected_eff_class[i])
                    cond = int(sel.condition[i])
                    if classical_policy is not None:
                        classical_policy.set_call(a, cond, _inviter_of(conv, a, cond))
                    res = bridge.call(
                        a, tick, cls, cond,
                        cell=int(cell[a]), activity=int(act[a]), hunger=int(hun[a]),
                        last_action=int(last_act[a]),
                        inviter=_inviter_of(conv, a, cond),
                    )
                    if res.deferred or res.observed_tick >= 0:
                        # 艦隊で録ったテープの再生(D-58)。本番と同じ「発射→後で届く」形に戻す。
                        if a in fleet_waiting:
                            n_fleet_resent += 1
                        fleet_waiting.add(a)
                        if res.deferred:
                            item = (a, cond, cls, int(sel.since_tick[i]))
                            if res.observed_tick > tick:
                                # タイムアウト等=**観測した tick** の ④′ で再投入される
                                replay_inbox.setdefault(res.observed_tick, []).append((True, item))
                            else:
                                # キュー満杯=発射のその場で判明 → 翌 tick の再投入枠へ
                                fleet_deferred.append(item)
                            continue
                        if res.observed_tick > tick:
                            replay_inbox.setdefault(res.observed_tick, []).append((False, res))
                            continue
                        fleet_waiting.discard(a)  # 同 tick で届いた=待ちにならない
                    pending.append((
                        res.t_apply, cls, a, cond, res.text, res.action_code,
                        _target_person(res.target), *_pending_extra(res),
                    ))
                    if not res.format_ok:
                        n_parse_errors += 1
                    if conv is not None and cond == int(WakeCondition.CONVERSATION_TURN):
                        # 会話ターンの応答は**発話ブロック**(1呼=1ブロック・§3)
                        _utter(a, tick, res.parse.action, res.parse.comment, res.parse.reason,
                               res.parse)
            else:
                # 逐次ループ宣言2′: 同じ呼数ぶん(描画は同じ・往復だけ非同期になる)
                calls: list[LLMCall] = []
                for i in range(len(sel)):
                    a = int(sel.agent_id[i])
                    cls = int(decision.selected_eff_class[i])
                    cond = int(sel.condition[i])
                    rendered = bridge.renderer.render(
                        agent_id=a, tick=tick, cell=int(cell[a]), activity=int(act[a]),
                        hunger=int(hun[a]), wake_class=cls, condition=cond,
                        last_action=int(last_act[a]),
                        inviter=_inviter_of(conv, a, cond),
                    )
                    sys_txt, usr_txt = split_system_user(
                        rendered.text, rendered.blocks[0][1] if rendered.blocks else ""
                    )
                    if a in fleet_waiting:
                        n_fleet_resent += 1
                    fleet_waiting.add(a)
                    calls.append(
                        LLMCall(
                            call_id=f"{tick}:{a}:{cls}",
                            agent_id=a, tick=tick, wake_class=cls, condition=cond,
                            prompt=rendered.text, system=sys_txt, user=usr_txt,
                            blocks=rendered.blocks, lane=lane, cell=int(cell[a]),
                            time_bucket=tick // TIME_BUCKET_TICKS,
                            since_tick=int(sel.since_tick[i]),
                            prompt_hash_hint=rendered.prompt_hash,
                            recalled_rows=tuple(getattr(rendered, "recalled_rows", ())),
                        )
                    )
                # 発射は**非ブロッキング**。返るのは「キューに入らなかった」分だけ。
                for d in fleet_bridge.submit(calls, now_tick=tick):
                    fleet_deferred.append(
                        (int(d.call.agent_id), int(d.call.condition),
                         int(d.call.wake_class), int(d.call.wake_since))
                    )
            result.llm_calls += len(sel)  # L4 の呼数=**発射数**(再送も 1 呼・親決定 09-09)
            calls_by_cond += np.bincount(
                np.asarray(sel.condition, dtype=np.int64), minlength=N_WAKE_CONDITIONS_ALL
            )[:N_WAKE_CONDITIONS_ALL]
            result.calls_by_hour[(td // 60) % 24] += len(sel)  # D-56 の検証欄(10a: 日の中の tick から)
            # 5b 層の記録: 発射した呼=System 1.5(方策 classical)か 2(LLM/mock)× 起床入口
            np.add.at(
                layer_counts[(tick * tick_seconds // 3600) % 24, _call_layer],
                _ENTRANCE_OF_CONDITION[np.asarray(sel.condition, dtype=np.int64)],
                1,
            )
        # 艦隊経路の書式エラーは ④′(到着時)で数える=選抜が 0 の tick でも計上する
        n_parse_errors += n_parse_errors_fleet
        peak_pending = max(peak_pending, len(pending))
        peak_backlog = max(peak_backlog, arbiter.n_pending())
        phase["llm"] += time.perf_counter() - t0

        # ---- ⑤ Phase A(エンジン継続との合流) ----
        t0 = time.perf_counter()
        # 二層の段 2: 「あたり」で着いた体の次の行き先(LLM 応答のある体は除く)
        wander_intents = (
            act_layer.wander_intents(agents, tick, exclude=llm_intents.agent_id)
            if act_layer is not None
            else C.IntentBatch.empty()
        )
        # 段 2c: 着いた体の意図の行為(LLM を呼ばない=System 1・この tick に応答が来た体は除く)
        # (親決定 Q20: なし/待機/同じ行き先の移動は意図を保つ=着いた体のその応答の行は外して実行)
        if intent_layer is not None:
            arrival_intents, llm_intents = intent_layer.arrival_intents(
                agents, space, tick, llm=llm_intents
            )
            # 5b 層の記録: 着いた意図の行為はエンジンが実行する(System 1・入口=満了)
            layer_counts[(tick * tick_seconds // 3600) % 24, 0, _ENTRANCE_EXPIRY] += len(
                arrival_intents
            )
        else:
            arrival_intents = C.IntentBatch.empty()
        intents = C.IntentBatch.concat(
            [llm_intents, wander_intents, arrival_intents,
             C.engine_continuations(agents, space, tick)]
            if act_layer is not None
            else [llm_intents, C.engine_continuations(agents, space, tick)]
        ).one_per_agent()
        peak_intents = max(peak_intents, len(intents))
        phase["phase_a"] += time.perf_counter() - t0

        # ---- ⑥ Phase B(資源裁定) ----
        t0 = time.perf_counter()
        plan = C.arbitrate_resources(
            intents, tick, salt, space, world.pois.stock, world.pois.capacity
        )
        phase["phase_b"] += time.perf_counter() - t0

        # ---- ⑦ Phase C(resolve=唯一の書き手) ----
        t0 = time.perf_counter()
        outcome = R.apply(
            plan.confirmed,
            plan.losers,
            agents,
            world,
            tick,
            schedule=schedule,
            ledger=ledger,
            rail=None if runner is None or not runner.is_enabled("rail") else runner.rail,
            crowd=None if runner is None or not runner.is_enabled("crowd") else runner.crowd,
            hotel=None if runner is None or not runner.is_enabled("hotel") else runner.hotel,
            salient=None if runner is None or not runner.is_enabled("salient") else runner.salient,
            report_precondition=bool(report_precondition),
            queue_service=bool(queue_service),
            leave_effect=bool(leave_effect),
            vocab_version=vocab_version,
            geometry=geom,
            focus_request=focus_request,
            talk_by_distance=attention_on,
            track_visits=(fam_layer is not None or mem_layer is not None),
            energy=energy_layer,
            track_events=mem_layer is not None,
        )
        phase["phase_c"] += time.perf_counter() - t0
        if norm_meter is not None:
            norm_meter.observe_results(tick)  # 第308 D-107 (a): 役割語の結果(読むだけ)
        phase["movement"] += outcome.movement_seconds
        phase["movement_cpu"] += outcome.movement_cpu_seconds
        geometry_hops += outcome.n_hops
        geometry_jammed += outcome.n_jammed
        result.fares_paid += outcome.fare_paid
        result.n_boarded += outcome.n_boarded
        result.n_alighted += outcome.n_alighted
        result.n_queued += outcome.n_queued
        result.n_board_waiting += outcome.n_board_waiting
        result.n_board_timeout += outcome.n_board_timeout
        result.meals += outcome.n_meals
        result.move_bad_target += outcome.n_move_bad_target
        result.move_unreachable += outcome.n_move_unreachable
        result.meal_yen += outcome.meal_yen
        # C9b(対象と注意)。腕が立っていないランでは 4 本とも 0 のまま。
        result.n_approach += outcome.n_approach
        result.n_approach_done += outcome.n_approach_done
        result.n_target_gone += outcome.n_target_gone
        result.n_focus += outcome.n_focus
        result.n_focus_lost += outcome.n_focus_lost
        result.n_talk_by_distance += outcome.n_talk_by_distance
        for _k in ("n_leave", "n_leave_indoor", "n_leave_queue", "n_leave_conversing"):  # 4 本
            leave_counts[_k] += int(getattr(outcome, _k))
        result.n_report_ok += outcome.n_report_ok
        result.n_report_no_event += outcome.n_report_no_event
        result.n_served_from_queue += outcome.n_served_from_queue
        result.n_queue_closed += outcome.n_queue_closed
        # D-71 §3 J: 語ごとの使用件数(**解決後**=エンジンが適用した行動)。
        for _code, _n in outcome.per_action.items():
            per_action_total[int(_code)] = per_action_total.get(int(_code), 0) + int(_n)

        # ---- 会話セッション(行動契約書 §3・C6 で設計準拠化 09-09) ----
        # ①返事待ちの被招待が答えていれば成立/不成立を確定 → ②新しい招待を捌く
        # → ③期限切れの返事待ちを落とす。相手は **LLM が「対象」欄で名指しした個体**
        # (``C.talk_partners``)。相手が同じ適用バッチに居なければ次 tick に
        # ``WakeCondition.CONVERSATION_TURN`` で起こして本人の呼で答えさせる。
        if conv is not None:
            cell_now = agents.registry.cell
            act_now = agents.registry.activity
            reverted: list[int] = []

            def _revert(a: int) -> None:
                """招待が流れた側を IDLE へ戻す候補に積む。

                **すでに別のセッションに入っている個体は戻さない**(相互招待で
                A→B と B→C が同時に立つと、B の招待が流れたときに B が A との
                セッションから引き剥がされて片側だけ CONVERSING が残る)。
                """
                if a >= 0 and not conv.is_busy(int(a)):
                    reverted.append(int(a))

            # ①(返事待ちの解決)は **Phase C の前**に済んでいる(``_settle_pending_invites``)。

            # ---- 9a(D-112 ④): 退去した会話中の体のセッションを閉じる(理由「退去」→ CLOSING → TERMINAL) ----
            if leave_effect and outcome.leave_conversing:
                for _lv in np.unique(np.concatenate(outcome.leave_conversing)).tolist():
                    # 逐次ループ宣言: この tick に退去した会話中の体の数ぶん(≤ 1 tick の呼数)
                    if conv.close_now(int(_lv), tick, "退去") is not None:
                        leave_closed += 1

            # ---- ② 新しい招待(resolve が通した 会話 を入口にする) ----
            talk = np.flatnonzero(plan.confirmed.action_code == C.ACT_TALK)
            if talk.size:
                inviters = plan.confirmed.agent_id[talk].astype(np.int64)
                invitees = plan.confirmed.target_id[talk].astype(np.int64)
                # 逐次ループ宣言3b: 会話成立数ぶん(≤ 1 tick の呼数)。個体数に比例しない。
                for j in range(inviters.size):
                    inviter = int(inviters[j])
                    invitee = int(invitees[j])
                    if invitee < 0 or invitee >= agents.n:
                        _revert(inviter)
                        continue
                    if int(act_now[inviter]) != int(Activity.CONVERSING):
                        # C10 8a(D-93 (d)): 相手が会話中(PARTNER_BUSY)で、そのセッションに空きがあれば加わる
                        if (
                            conv.max_participants > 2
                            and int(agents.registry.last_result[inviter]) == int(ResultCode.PARTNER_BUSY)
                            and int(act_now[invitee]) == int(Activity.CONVERSING)
                            and not conv.is_busy(inviter)
                        ):
                            s_join = conv.session_of(invitee)
                            if s_join is not None and bool(R.talk_within_reach(
                                agents, np.int64(inviter), np.int64(invitee), by_distance=attention_on,
                            )) and conv.join(s_join, inviter, tick):
                                R.join_conversation(agents, np.array([inviter]), np.array([invitee]), tick)
                        continue  # resolve が失敗させた(相手が会話中/去った)
                    same_cell = bool(
                        R.talk_within_reach(
                            agents,
                            np.int64(inviter),
                            np.int64(invitee),
                            by_distance=attention_on,
                        )
                    )
                    b_code, b_named = applied_now.get(invitee, (-1, -1))
                    # C10 8b: 招待の起点(招待/偶然/知人出現)=commit の選び手が控えた値(関係 on のランだけ)
                    origin = rel_layer.pop_origin(inviter) if rel_layer is not None else -1
                    # **相互指名**= 相手も自分の呼で**こちらを名指しして** 会話 と答えた。
                    # (エンジンが解決した対象ではなく LLM が書いた対象で見る=中-2)
                    mutual = b_code == C.ACT_TALK and b_named == inviter
                    if mutual and conv.invite_blocked_by_refractory(inviter, invitee, tick):
                        conv.n_invite_refractory_blocked += 1  # 軽-5: 相互指名も不応期の対象
                        conv.note_origin(origin, "rejected")
                        _revert(inviter)
                        continue
                    if mutual:
                        # その場で成立。相手の意思は相手自身の呼に出ているので抽選は引かない。
                        conv.n_invites += 1
                        conv.note_origin(origin, "invites")
                        conv.stamp_invite_refractory(inviter, invitee, tick)
                        opened = conv.invite(
                            inviter, invitee, tick, int(cell_now[inviter]),
                            same_cell=same_cell, partner_idle=True, answered=True,
                        )
                        if opened is None:
                            conv.note_origin(origin, "rejected")
                            _revert(inviter)  # 内訳は ``conv.invite`` が数える
                        else:
                            conv.n_accepted += 1
                            conv.note_origin(origin, "accepted")
                            opened.origin = int(origin)
                            R.set_conversing(
                                agents,
                                np.array([inviter], dtype=np.int64),
                                np.array([invitee], dtype=np.int64),
                            )
                    else:
                        # 相手はまだ**招待を見ていない**(この tick の相手の応答は
                        # 招待の載っていないプロンプトへの答え)→ **次 tick に被招待で
                        # 起こして本人に答えさせる**(知覚契約書 §6 起床(ii))。
                        # 招待側は CONVERSING のまま待つ。
                        if not conv.register_pending(
                            inviter, invitee, tick, int(cell_now[inviter]),
                            same_cell=same_cell, origin=origin,
                        ):
                            conv.note_origin(origin, "rejected")
                            _revert(inviter)
                        else:
                            conv.note_origin(origin, "invites")

            # ---- ③ 期限切れの返事待ち(「無視された」=呼を消費しない) ----
            for stale in conv.expire_pending(tick):
                _revert(stale)
            if rel_layer is not None:
                rel_layer.origin_of.clear()  # C10 8b: この tick の起点の控えを捨てる(招待に使わなかった行)
            if reverted:
                R.revert_conversation(agents, np.array(sorted(set(reverted)), dtype=np.int64))
            finished = conv.step(
                tick,
                cell=agents.registry.cell,
                # C9b G7: 離脱は**実距離 3 m**(成立 2 m より広い=ヒステリシス)。
                xy=agents.registry.xy if attention_on else None,
                leave_distance_m=R.TALK_LEAVE_METERS if attention_on else None,
            )
            if finished:
                # 終了したセッションの参加者を解放する(行動契約書 §3「終了はエンジン」)。
                # C3 では CLOSING→TERMINAL のあと ``activity`` が CONVERSING のまま残っていた
                # (退去でしか解けなかった)=会話状態の取り残し。書き手は resolve。
                done = np.array(
                    sorted({int(p) for s in finished for p in s.participants}), dtype=np.int64
                )
                R.revert_conversation(agents, done)
            conv.purge_terminal()

        # ---- 二層の段 2: この tick に適用した応答の活動を書き、到着・会話成立で満了させる ----
        # **resolve.apply と会話の後**(行為の成否と会話セッションが確定してから)。
        if act_layer is not None:
            if applied_activity[0]:
                act_layer.after_resolve(agents, tick, *applied_activity)
            act_layer.settle_events(agents, tick, conv)
            if intent_layer is not None:
                # 段 2c: 実行した意図の結果・意図を立てる・掃除(TOO_FAR・計画境界)
                intent_layer.after_apply(
                    agents, tick, act_layer, applied_activity if applied_activity[0] else None
                )
        _exp = None
        if (fam_layer is not None or mem_layer is not None) and _fam_renderer is not None and getattr(
            _fam_renderer, "signage_exposures", None
        ):
            _exp = list(_fam_renderer.signage_exposures)
            _fam_renderer.signage_exposures.clear()
        # ---- 6 段目 6a: 記憶の記録(行動の成否・会話・気づき・強い看板)。親しみの表の**前**
        # (看板の初見=親しみの表にまだその POI の行が無い、をこの tick の書き込みの前に見る) ----
        if mem_layer is not None:
            mem_layer.after_tick(
                agents, tick,
                applied=(
                    (plan.confirmed.agent_id, plan.confirmed.target_id),
                    (plan.losers.agent_id, plan.losers.target_id),
                ),
                visits=(outcome.visit_agents, outcome.visit_pois),
                arrived=outcome.arrived_agents,
                conv=conv,
                salient_events=(
                    getattr(runner.salient, "events", ())
                    if (runner is not None and runner.is_enabled("salient"))
                    else ()
                ),
                signage=_exp,
            )
        # ---- 4 段目: 親しみの表(訪問・看板の露出・セルに入った回)。Phase C と活動層の後 ----
        if fam_layer is not None:
            fam_layer.after_tick(
                agents, tick, (outcome.visit_agents, outcome.visit_pois), _exp
            )
        # ---- 5 段目 5a: 語の段の時間の延べ(診断・読むだけ) ----
        if energy_layer is not None:
            energy_layer.after_tick(agents, tick, int(tick * tick_seconds // 60))

        diag_rows.append(
            (
                tick,
                *(int(decision.diag[r].sum()) for r in range(len(DIAG_COLUMNS))),
                int(decision.merged_per_class.sum()),
                len(cands),
                decision.n_calls,
                arbiter.n_pending(),
                len(pending),
                len(intents),
                plan.n_conflicts,
                plan.n_unresolved,
                outcome.n_moved,
                outcome.n_arrived,
                outcome.n_purchases,
                outcome.n_conversations,
                outcome.n_reflections,
                n_undefined,
                n_parse_errors,
                bridge.n_tape_misses - prev_tape_misses,
                (conv.n_opened - prev_sessions) if conv is not None else 0,
                decision.n_sleep_suppressed,  # D-56
                decision.n_outside_suppressed,  # D-66
            )
        )
        prev_tape_misses = bridge.n_tape_misses
        prev_sessions = conv.n_opened if conv is not None else 0
        if outcome.n_planned_sleep:  # 就寝地へ着いて寝たぶん(D-62 意図の保持)
            sleep_counts["arrived"] = (
                sleep_counts.get("arrived", 0) + int(outcome.n_planned_sleep)
            )

        if presence is not None:
            presence.sample(tick)  # 正時の在圏・計画一致率(在圏 journal と同じ位置)
        if norm_meter is not None:
            norm_meter.observe_tick(tick)  # 第308 D-107 (a): 同行の検出(位置が確定した後・読むだけ)
        if occupancy_every and tick % occupancy_every == 0:
            occ_ticks.append(int(tick))
            occ_counts.append(np.asarray(world.cells.density, dtype=np.int32).copy())
            _k = np.asarray(agents.registry.field("kind"), dtype=np.int64)
            _c = np.asarray(agents.registry.cell, dtype=np.int64)
            _ok = (_c >= 0) & (_c < world.n_cells)
            _kc = np.bincount(_k[_ok] * world.n_cells + _c[_ok], minlength=9 * world.n_cells)[: 9 * world.n_cells]
            occ_kind.append(_kc.reshape(9, world.n_cells).astype(np.int32))
            # D-66: 種別 × 在圏/乗車中/域外(9×3)。**既存キーは 1 本も変えない**
            # (``tools/c7`` は無改造で読める=知らないキーは無視される)。
            _ts = np.clip(np.asarray(agents.registry.transit_state, dtype=np.int64), 0, 2)
            _tk = np.bincount(_k * 3 + _ts, minlength=27)[:27]
            occ_transit.append(_tk.reshape(9, 3).astype(np.int32))
        if checkpoint_every and ((tick + 1) % checkpoint_every == 0 or tick == total_ticks - 1):
            t0 = time.perf_counter()
            result.checkpoints.append(
                Checkpoint(
                    tick, agents.state_hash(), world.state_hash(),
                    schedule.population_hash,
                    schedule_hash,
                    (
                        act_layer.state_hash()
                        if intent_layer is None
                        else blake3_hex(
                            f"{act_layer.state_hash()}\x1f{intent_layer.state_hash()}".encode()
                        )
                    )
                    if act_layer is not None
                    else "",
                )
            )
            phase["checkpoint"] += time.perf_counter() - t0

    # ---- 艦隊の残りを吸い切る(**捨てない**)。テープを閉じる前に置く ----
    if fleet_bridge is not None:
        n_late = 0
        # ``now_tick=total_ticks``= ラン終端(最後の tick の 1 つ先)。再生側はこの値の項目を
        # 「tick ループ中には届かなかった」として同じ位置で処理する(D-58)。
        for res in fleet_bridge.drain(now_tick=total_ticks):
            if isinstance(res, FleetDeferred):
                fleet_deferred.append(
                    (int(res.call.agent_id), int(res.call.condition),
                     int(res.call.wake_class), int(res.call.wake_since))
                )
                continue
            n_late += 1
            pending.append((
                res.tick + delta_think_ticks(res.lane, tick_seconds), res.wake_class,
                res.agent_id, res.condition, res.text, res.action_code,
                _target_person(res.target), *_pending_extra(res),
            ))
        result.fleet_drained_at_end = n_late
        # ラン終端でも答えが返らなかった呼(**次ランへ持ち越す**の監査点。0 が正常)
        result.fleet_unanswered_at_end = len(fleet_deferred)
        fleet_bridge.close()
    elif replay_inbox:
        # ---- 再生の終端処理(D-58): tick ループ中に届かなかった分=本番の drain 相当 ----
        n_late = 0
        for t in sorted(replay_inbox):  # 逐次ループ宣言: 残件数ぶん(通常 0)
            for is_deferred, item in replay_inbox[t]:
                if is_deferred:
                    fleet_deferred.append(item)
                    continue
                n_late += 1
                pending.append((
                    item.t_apply, item.wake_class, item.agent_id, item.condition,
                    item.text, item.action_code, _target_person(item.target),
                    *_pending_extra(item),
                ))
        replay_inbox.clear()
        result.fleet_drained_at_end = n_late
        result.fleet_unanswered_at_end = len(fleet_deferred)

    bridge.close()
    result.runner = runner  # type: ignore[attr-defined]
    # AB7 の M1-M3(接地率・未定義率・上位未定義語)は §7 の台帳が持つ。``runner`` と同じく
    # **後付けの属性**として渡すだけ(RunResult の欄は増やさない=既存の出力は不変)。
    result.undefined_registry = bridge.undefined  # type: ignore[attr-defined]
    if runner is not None:
        # D-R2-6: ActualLog は O(t) が本質 → 保持窓を過ぎた生ログを日次集約行へ畳む
        runner.end_of_day(max(0, total_ticks - 1))
        result.registry_hash = runner.registry_hash
        result.constitution_ok = runner.constitution_ok
        result.replay_date = runner.replay_date
        result.process_seconds = dict(runner.phase_seconds)
        result.process_counters = runner.counters()
        result.actual_log_rows = int(runner.log.n_appended)
        result.compliance_rate = float(runner.compliance().rate)
        result.salient_events = int(runner.salient.n_events)
        result.noticed = int(runner.salient.n_noticed)
        result.dispatches = int(runner.dispatch.n_dispatched)
        result.restocks = int(runner.shelf.n_role_actions + runner.shelf.n_fallback)
        result.deliveries = int(runner.delivery_inbound.n_runs)
        result.parcels = int(runner.last_mile.delivered.sum())
        result.bus_arrivals = int(runner.bus_taxi.n_arrivals)
        result.hotel_checkins = int(runner.hotel.n_checkin)
        result.waste_tonnes_per_day = float(runner.projected_waste_tonnes_per_day())
        _ws = runner.waste_sink_report()  # 第304 Q135 (a): 店だけの静的な帯+内訳 3 つ(報告だけ)
        if _ws is not None:
            result.waste_sink = dict(_ws)
            result.waste_band = (float(_ws["band_store_t"][0]), float(_ws["band_store_t"][1]))
    ledger_growth: tuple[dict[str, Any], dict[str, int]] = ({}, {})
    if ledger is not None:
        # 日次の畳み込み(D-R2-6: 生ログは保持窓・取引行列は日次集約行へ)。
        # **締めを捨てない**——締めると取引行列も当日の廃棄も 0 に戻るので、締めたあとに
        # 現在値でセンサスを回すと faucet/sink/廃棄が全部 0 の空虚な行になり、ゲートが
        # 素通りする(層2レビュー指摘)。``daily_census`` は ``day_index`` の締めを読む。
        # 10a #21: 締めの日番号は暦の口の ``day_key``(day_index モードでは今の ``day_index``)。台帳は 1 日のランだけ。
        _close_day = calendar.day_key(sim_days - 1)
        closes = ledger.end_of_day(_close_day)
        result.day_closed = int(closes.day)
        ledger_growth = ledger.growth_parts()
        # 日次(軽量)センサス+ゲート(境界・経済設計書 §2.4)。
        # engine は economy を import できない(層契約)ので、行の作り手は
        # ``LedgerBundle.census``(economy 側が注入する呼び出し可能)。**失敗しても raise しない**
        # =診断の赤(§2.4「ゲート失敗=較正・holdout 照合に使わない」)。
        row = ledger.daily_census(_close_day)
        if row is not None:
            result.census_row = dict(row)
            result.census_pass = bool(row.get("gate_ok", False))
        # 月次センサスの T3(冗長方程式の検算・D-85 (a)・ユーザー決定 2026-09-17)。
        # 月次が立たない日は None(=未実行)。**``census_out`` とは無関係に**毎日呼ぶ
        # ——書き出しの有無で manifest が動くと「観測が世界を変えない」が崩れるため。
        t3 = ledger.monthly_t3(_close_day)
        if t3 is not None:
            result.t3_report = dict(t3)
            result.t3_ok = bool(t3.get("ok", False))
        # 日次センサス/月次 MER の出力口(§2.4)。**``census_out`` を渡したときだけ**書く。
        # 書き手は economy 側の注入(engine は economy を import できない=層契約)。
        if census_out is not None:
            result.census_paths = ledger.write_census(_close_day, str(census_out))
    result.bridge_counters = dict(bridge.counters())
    if fleet_bridge is not None:
        result.bridge_counters.update(fleet_bridge.counters())
        result.bridge_counters["fleet_reinjected"] = float(n_fleet_reinjected)
        result.bridge_counters["fleet_resent"] = float(n_fleet_resent)
        result.fleet_fields = dict(fleet.config.manifest_fields())
    elif n_fleet_reinjected or n_fleet_resent:
        # 再生が艦隊テープの繰り延べを再現したときだけ出す(D-58)。
        # mock ランは従来どおり ``fleet_*`` の欄を持たない(退化検査の約束)。
        result.bridge_counters["fleet_reinjected"] = float(n_fleet_reinjected)
        result.bridge_counters["fleet_resent"] = float(n_fleet_resent)
    result.conversation_counters = dict(conv.counters()) if conv is not None else {}
    if conv is not None:
        # 会話の相手の由来(行動契約書 §1-2 の対象スロットが効いているかの監査点)。
        result.conversation_counters["conv_target_named"] = int(talk_stats.get("talk_named", 0))
        result.conversation_counters["conv_fallback_same_batch"] = int(
            talk_stats.get("talk_fallback", 0)
        )
        result.conversation_counters["conv_target_absent"] = int(talk_stats.get("talk_absent", 0))
    if conv is not None:
        # 層2指摘の固定: 日末に CONVERSING の個体は活動セッションの参加者だけ(被招待側は C4 まで IDLE)
        result.conversation_counters["conversing_agents_end"] = int(
            np.count_nonzero(agents.registry.activity == int(Activity.CONVERSING))
        )
    result.renderer_counters = dict(perception.counters()) if perception is not None else {}
    result.frozen_sources = frozen_sources_map
    result.renderer_name = (
        "perception.Renderer" if perception is not None else type(renderer_obj).__name__
    )
    # 実際に描いた腕(注入レンダラなら**そちらの値**が正)。§3.2 ablation ① の同定欄。
    result.budget_mode = BudgetMode.parse(
        getattr(getattr(perception, "renderer", None), "budget_mode", budget_mode_enum)
        if perception is not None
        else budget_mode_enum
    ).value
    # D-99 (a): L4 呼数予算の腕(倍率は申告・``budget_per_tick`` は**実際に使った値**)。
    result.l4_scale = float(l4_scale)
    result.budget_per_tick = float(arbiter.budget)
    result.tick_seconds = int(tick_seconds)
    # ---- 10a: 暦の欄・応答の遅れ・日数(manifest の ``calendar``・``response_delay``・``sim_days``) ----
    result.calendar_fields = {**calendar.manifest_fields(sim_days), "start_check": list(start_check)}
    result.response_delay = int(response_delay)
    result.sim_days = int(sim_days)
    # ablation 第1陣 ②③⑥ の腕(manifest の同定欄)。⑥ は**実際に描いた側**が正。
    result.p_notice_ablation = _pnotice_ablation_name(
        runner.salient.ablation if runner is not None else p_notice_ablation
    )
    result.p_notice_d50_scale = (
        float(runner.salient.d50_scale) if runner is not None else float(p_notice_d50_scale)
    )
    result.refractory_scale = dict(refractory_scale_norm)
    result.signage = bool(
        getattr(getattr(perception, "renderer", None), "signage_enabled", signage)
        if perception is not None
        else signage
    )
    # D-59 (b): 注視ゲートも**実際に描いた側**が正(注入レンダラならそちらの値)。
    result.signage_p_see = float(
        getattr(getattr(perception, "renderer", None), "signage_p_see", signage_p_see)
        if perception is not None
        else signage_p_see
    )
    # AB7: 実際に描いた腕(注入レンダラなら**そちらの値**が正)。
    result.role_words = bool(
        getattr(getattr(perception, "renderer", None), "role_words", role_words)
    )
    result.intent_mode = str(
        getattr(getattr(perception, "renderer", None), "intent_mode", intent_mode)
        if perception is not None
        else intent_mode
    )
    # 語彙 v2: 実際に使った版(注入レンダラでも**エンジン側の版**が正=行動の解決はこちら)。
    result.vocab_version = str(vocab_version)
    result.action_usage = _action_usage(per_action_total, vocab_version)
    # 二層の段 2: 活動層と起床の内訳(満了入口の列は全ランで出る=層が無ければ 0)
    result.activity = bool(activity_on)
    result.eatery = str(eatery)
    result.chooser = str(chooser)
    result.policy = str(policy)
    result.classical = (
        {**classical_policy.manifest_fields(),
         "decisions_by_hour": {"meal": classical_policy.by_hour[:, 0].tolist(),
                               "activity": classical_policy.by_hour[:, 1].tolist()}}
        if classical_policy is not None
        else {}
    )
    _cs = getattr(getattr(poi_resolver, "chooser", None), "stats", None)
    result.chooser_stats = (
        {"name": str(chooser), "p_h": float(classical_habit_p), "tau": float(classical_tau),
         "activity_region": str(activity_region), "counts": dict(sorted(_cs.items()))}
        if isinstance(_cs, dict)
        else {}
    )
    result.decision_layers = decision_layers_summary(layer_counts)
    _psr = getattr(perception, "renderer", None) if perception is not None else None
    result.p_see_activity = (
        _psr.p_see_activity_summary()
        if (_psr is not None and hasattr(_psr, "p_see_activity_summary"))
        else {"table": dict(p_see_activity_table), "identity": bool(p_see_activity_identity)}
    )
    result.poi_target = str(poi_target)
    result.target_resolution = (
        resolution_summary(poi_resolver.stats, poi_resolver.entropy_sum)
        if poi_resolver is not None
        else {}
    )
    result.move_search_radius = int(move_search_radius)
    result.mock_move_target_p = float(mock_move_target_p)
    result.intent = intent_layer.counters() if intent_layer is not None else {}
    result.familiarity = bool(familiarity_on)
    result.familiarity_k = int(familiarity_k)
    result.familiarity_summary = (
        fam_layer.summary(agents, max(0, int(total_ticks) - 1)) if fam_layer is not None else {}
    )
    result.memory = bool(memory_on)
    result.memory_n = int(memory_n)
    result.memory_summary = (
        {
            **mem_layer.summary(agents, max(0, int(total_ticks) - 1)),
            "gist_bytes": mem_layer.gist_bytes(),
            # 6b: 描画側の計数(記憶の行を載せた描画・項の件数・行の tok の分布・予算で削った数)
            "render": (
                _fam_renderer.memory_summary()
                if _fam_renderer is not None and hasattr(_fam_renderer, "memory_summary")
                else {}
            ),
        }
        if mem_layer is not None
        else {}
    )
    result.store_memory = bool(store_memory_on)
    result.store_memory_summary = (
        mem_layer.store.summary(agents, max(0, int(total_ticks) - 1), mem_layer.tau)
        if mem_layer is not None and mem_layer.store is not None
        else {}
    )
    result.wom = (
        {
            **wom_ex.summary(tuple(getattr(world.assets, "poi_name", ()) or ())),
            "store_rows_with_wom": int(
                result.store_memory_summary.get("rows_with_source_bit", {}).get("wom", 0)
            ),
            "store_events_wom": int(mem_layer.store.stats.get("events:wom", 0)),
        }
        if wom_ex is not None and mem_layer is not None and mem_layer.store is not None
        else {}
    )
    result.relations = (
        rel_layer.summary(agents, max(0, int(total_ticks) - 1)) if rel_layer is not None else {}
    )
    if rel_layer is not None and conv is not None and conv.origin_names is not None:
        # C10 8b 診断行: 起点ごとの 招待/承諾/断り/期限切れ/門で落ちた(decision_layers の入口にも同じ表)
        result.relations["origins"] = conv.origin_summary()
        result.decision_layers["conversation_origins"] = conv.origin_summary()
    _sc = getattr(poi_resolver, "store_choice", None) if poi_resolver is not None else None
    result.store_choice = (
        {**_sc.summary(), "arms": {"store_wom": bool(store_wom_on), "store_signage": bool(store_signage_on),
                                   "store_recall_scope": str(store_recall_scope),
                                   "chooser": str(getattr(poi_resolver.chooser, "name", ""))}}
        if _sc is not None
        else {}
    )
    if fam_layer is not None and result.familiarity_summary:
        # 5c: 入った回の露出を活動の種別の名で(索引 → 名)
        _fs = dict(result.familiarity_summary)
        _by = {
            P_SEE_ACTIVITY_KINDS[int(k.rsplit(":", 1)[1])]: int(v)
            for k, v in fam_layer.stats.items()
            if str(k).startswith("exposures_signage_entry_by_kind:")
        }
        if _by:
            _fs["exposures_signage_entry_by_kind"] = _by
        result.familiarity_summary = _fs
    result.hunger_model = str(hunger_model)
    result.intero_crossings = {
        f"{var}_{d}{suffix}": int(intero_cross[v, k, s])
        for v, var in enumerate(("hunger", "fatigue", "thermal"))
        for k, d in enumerate(("up", "down"))
        for s, suffix in enumerate(("", "_awake_in_area"))
    }
    result.energy_rate = str(energy_rate) if energy_on else ""
    result.meal_sleep_defer = str(meal_sleep_defer)
    result.home_meal = str(home_meal)
    result.hunger_words = str(hunger_words)
    result.energy = (
        {**energy_layer.model.manifest_fields(), **energy_layer.summary(agents)}
        if energy_layer is not None
        else {}
    )
    if intent_layer is not None:
        # B5「いま <行為> のため <対象> へ向かっている」を載せた回数(描画のあるランだけ)
        _rr = getattr(perception, "renderer", None) if perception is not None else None
        result.intent["b5_lines"] = int(getattr(_rr, "intent_lines", 0))
        result.intent["b5_lines_over_budget"] = int(getattr(_rr, "intent_lines_over_budget", 0))
        # Q25: 名指しの即時閉店の B6 補足を載せた回数
        result.intent["b6_named_closed_notes"] = int(getattr(_rr, "named_closed_notes", 0))
    result.intent_max_ticks = int(intent_max_ticks)
    _nr = getattr(perception, "renderer", None) if perception is not None else None
    result.near_tiebreak = {
        "mode": str(near_tiebreak),
        "ties_broken": int(getattr(_nr, "near_tie_breaks", 0)),
        "tie_candidates": int(getattr(_nr, "near_tie_candidates", 0)),
        # 第304 Q130: 近接行の並び(distance/id)と、並べた行に距離の同点があった描画の数
        "order": str(near_order),
        "order_ties": int(getattr(_nr, "near_order_ties", 0)),
    }
    result.group_norms = (  # 第308 D-107 (a)・第309 Q150 の切替口
        {"enabled": True, **norm_meter.summary(conv=conv, result=result)} if norm_meter is not None
        else {"enabled": False}
    )
    result.mock_out_of_cell_target_p = float(mock_out_of_cell_target_p)
    result.move_resolution = move_resolution_summary(
        poi_resolver.move_stats if poi_resolver is not None else Counter(),
        result.move_bad_target,
        result.move_unreachable,
    )
    result.calls_by_condition = {
        WakeCondition(i).name: int(calls_by_cond[i]) for i in range(N_WAKE_CONDITIONS_ALL)
    }
    if act_layer is not None:
        result.activity_counters = dict(act_layer.counters())
        result.activity_kind_counts = dict(act_layer.kind_distribution())
    result.sleep_suppression = bool(sleep_suppression)
    result.plan_sleep = bool(plan_sleep)
    result.wake_rate_by_hour = [
        (awake_sum[h] / (awake_ticks[h] * n_agents)) if (awake_ticks[h] and n_agents) else 0.0
        for h in range(24)
    ]
    if presence is not None:
        for _k, _v in presence.sleep_counts.items():
            sleep_counts[_k] = sleep_counts.get(_k, 0) + int(_v)
    result.planned_sleep_counts = dict(sleep_counts)
    result.plan_executor = bool(plan_exec_on)
    result.outside_suppression = bool(outside_suppression and plan_exec_on)
    result.outside_wake_candidates = int(n_outside_calls)
    result.exit_mode = str(exit_mode)
    result.attendance_rate = float(attendance_rate)
    result.derive_rule = str(derive_rule)
    result.geometry = str(geometry)
    result.geometry_hops = int(geometry_hops)
    result.geometry_jammed = int(geometry_jammed)
    result.area_source = str(area_source)
    result.seat_area_eatery_m2 = (
        None if seat_area_eatery_m2 is None else float(seat_area_eatery_m2)
    )
    result.seat_area_retail_m2 = (
        None if seat_area_retail_m2 is None else float(seat_area_retail_m2)
    )
    if walkable is not None:
        _wk = np.asarray(walkable, dtype=np.float64).ravel()
        if _wk.size:
            result.walkable_area_median_m2 = float(np.median(_wk))
            result.walkable_area_min_m2 = float(_wk.min())
    result.attention = bool(attention_on)
    result.leave_effects = {"enabled": bool(leave_effect), "leave": int(leave_counts["n_leave"]),
                            "released_indoor": int(leave_counts["n_leave_indoor"]),
                            "left_queue": int(leave_counts["n_leave_queue"]),
                            "was_conversing": int(leave_counts["n_leave_conversing"]),
                            "sessions_closed": int(leave_closed)}
    if presence is not None:
        result.presence_exit = dict(presence.exit_summary())
        result.presence_counters = dict(presence.counters())
        result.presence_summary = presence.summary()
        # 標本の無かった時(短いラン)は NaN のまま来るので 0.0 に落とす(推測で埋めない)
        result.wake_rate_in_area_by_hour = [
            (0.0 if v != v else round(float(v), 6)) for v in presence.wake_in_area_by_hour
        ]
    result.diagnostics = np.asarray(diag_rows, dtype=np.int64).reshape(-1, len(DIAG_RUN_COLUMNS))
    result.phase_seconds = phase
    if norm_meter is not None:
        result.phase_seconds["group_norms"] = float(norm_meter.seconds)  # 第308: 計器の費用(壁時計)
        result.phase_seconds["group_norms_tick_ms_max"] = float(norm_meter.tick_ms_max)  # 第309: 1 tick の最大
    result.wall_seconds = time.perf_counter() - t_start
    result.arbiter_counters = {k: dict(v) for k, v in arbiter.counters().items()}
    result.money_end = int(agents.registry.money.astype(np.int64).sum())
    result.revenue_end = int(world.pois.revenue.astype(np.int64).sum())
    result.min_stock = int(world.pois.stock.min()) if world.n_poi else 0

    # ---- 状態成長宣言の検査(D-R2-6) ----
    # エンジンの 5 バッファ + **O(t) ログ本体**(ActualLog・取引ログ・納品ログ)。
    # 層2レビュー指摘: 5 バッファだけを外挿しても、D-R2-6 が名指しした「O(t) が本質」の
    # ログ(ActualLog と同型)は 1 バイトも測っていなかった。診断表(``diagnostics_rows``)は
    # 元から測っている(tick あたり 1 行)。
    declarations: dict[str, Any] = dict(GD.declarations())
    measured: dict[str, int] = {
        "pending_apply": peak_pending * GD.PENDING_APPLY_ROW_BYTES,
        "arbiter_backlog": peak_backlog * GD.ARBITER_PENDING_ROW_BYTES,
        "intent_buffer": peak_intents * GD.INTENT_ROW_BYTES,
        "diagnostics_rows": len(diag_rows) * GD.DIAG_ROW_BYTES,
        "tape_rows": result.llm_calls * GD.TAPE_ROW_BYTES,
    }
    if runner is not None:
        log_decls = dict(runner.log.growth_declarations())
        raw = log_decls.get(f"{runner.log.log_id}_raw")
        agg = log_decls.get(f"{runner.log.log_id}_daily")
        raw_bytes = len(runner.log) * int(raw.bytes_per_unit) if raw is not None else 0
        if raw is not None:
            declarations[raw.name] = raw
            measured[raw.name] = raw_bytes
        if agg is not None:
            # ``ActualLog.nbytes`` = 生ログ+索引+日次集約行。生ログぶんを引けば畳み先の実測。
            declarations[agg.name] = agg
            measured[agg.name] = max(0, int(runner.log.nbytes) - raw_bytes)
    led_decls, led_measured = ledger_growth
    declarations.update(led_decls)
    measured.update(led_measured)
    if act_layer is not None:
        # 二層の段 2: 活動の文(体ごとに上書き=日をまたいで伸びない・O(体数))
        _ad = GD.activity_declaration()
        declarations[_ad.name] = _ad
        measured[_ad.name] = int(
            sum(len(t.encode("utf-8")) for t in act_layer.text)
            + act_layer.until_kind.nbytes + act_layer.text_id.nbytes
        )
    result.growth_measured = measured
    result.growth_report = check_growth(
        declarations,
        measured,
        steps=total_ticks,  # 10a: 回した通しの tick 数(1 日のランでは ticks)
        minutes_per_step=max(1, tick_seconds // 60),
        n_entities=n_agents,
    )
    result.agents = agents  # type: ignore[attr-defined]
    result.world = world  # type: ignore[attr-defined]
    result.schedule = schedule  # type: ignore[attr-defined]
    result.ledger = ledger  # type: ignore[attr-defined]
    if occupancy_path and occ_ticks:
        import json as _json
        np.savez_compressed(
            str(occupancy_path),
            ticks=np.asarray(occ_ticks, dtype=np.int64),
            cell_counts=np.stack(occ_counts),
            kind_cell_counts=np.stack(occ_kind),
            transit_kind_counts=np.stack(occ_transit),
            meta=np.asarray(_json.dumps({"tick_seconds": int(tick_seconds), "start_hour": 0, "day_index": int(day_index)}, ensure_ascii=False)),
        )
    return result


# ------------------------------------------------------------------ CLI
def add_fleet_args(ap: "argparse.ArgumentParser") -> None:
    """実艦隊の共通引数(``engine.run`` と ``shibuya.cli`` で同じ綴りにするため 1 か所に置く)。

    ``--mode`` は **run manifest の実行モード**(smoke/calibration/holdout/ablation/production・
    運用設計書 §1.2)であって、``run_day(mode=...)`` の record/replay ではない。
    ``cache_salt`` の勘定分離(較正と holdout が prefix キャッシュを共有しない)に効く。
    """
    from shibuya.llm.fleet import DEFAULT_T1_MAX_TOKENS, DEFAULT_TEMPERATURE
    from shibuya.manifest.schema import Mode as _Mode

    ap.add_argument("--llm", choices=("mock", "fleet"), default="mock",
                    help="LLM 経路(fleet=実 vLLM 艦隊・--endpoints 必須)")
    ap.add_argument("--endpoints", type=str, default="",
                    help="カンマ区切り http://host:port(既定艦隊は 7 本=xxhash(call_id) mod 7)")
    ap.add_argument("--model", type=str, default="",
                    help="served-model-name(空なら /v1/models の先頭)")
    ap.add_argument("--mode", choices=[m.value for m in _Mode], default="smoke",
                    help="実行モード(cache_salt の勘定分離・record/replay とは別物)")
    ap.add_argument("--run-id", type=str, default="",
                    help="manifest の run_id(cache_salt の第2要素)")
    ap.add_argument("--tape", type=str, default="", help="録画テープの出力先ディレクトリ")
    ap.add_argument(
        "--temperature", type=float, default=DEFAULT_TEMPERATURE,
        help=("T1 の温度(既定 0.7=知覚契約書 §2.5/卒業条件表・運用設計書 §1.3 の本番値。"
              "運用設計書 §1.2 の設定節は欄形だけで数値を持たない)"),
    )
    ap.add_argument(
        "--max-tokens", type=int, default=DEFAULT_T1_MAX_TOKENS,
        help="T1 の max_tokens(既定 96=2 行形の最大 ≒70 tok に余裕・expedient)",
    )
    ap.add_argument(
        "--fleet-debug-dir", type=str, default="",
        help=("書式の原因分析用 jsonl の置き場(既定 off・診断のみ)。初回パースが落ちた呼の "
              "プロンプト/初回の生応答/再生成の生応答/実効・厳密の判定/理由 を 1 行 1 呼で書く"),
    )
    ap.add_argument("--fleet-wait-s", type=float, default=0.0,
                    help="④′ で未応答が残るとき tick ごとに最大この秒数だけ艦隊を待つ(既定 0=純非ブロッキング・本番の運用は 120)")
    ap.add_argument("--response-delay", type=int, choices=RESPONSE_DELAYS, default=None,
                    help=("応答の遅れ(10a・A9)。1=発射 +1 tick で反映(既定・受け取りを①の直前へ)/"
                          " 2=旧(+2 tick)。再生ではテープの記録と突き合わせ、違えば止める。記録の無い旧テープは"
                          " 2 とみなす(未指定なら 2 で再生)"))
    ap.add_argument("--fleet-queue-capacity", type=int, default=0,
                    help=("艦隊の受理待ち+実行中の合計上限(既定 0=FleetConfig の既定 max_in_flight×4)。"
                          "C7 本番(D-55/D-58): 計画呼数 2,709/tick に対し既定 1,792 だと 33.8%% が queue full で"
                          "繰り延べ→テープに残らず再生不能。計画呼数以上(例 4096)にすると繰り延べ ≈0"))


def add_calendar_args(ap: "argparse.ArgumentParser") -> None:
    """暦の口の引数(10a・A1-1・A1-2。``engine.run`` と ``shibuya.cli`` で同じ綴りにするため 1 か所に置く)。"""
    ap.add_argument("--calendar-weekday", choices=WEEKDAY_MODES, default=DEFAULT_WEEKDAY_MODE,
                    help=("曜日の決め方(10a)。day_index=今の約束(day 0=月曜・祝日を見ない・既定)/"
                          " real=開始日の実の曜日と内閣府の祝日(--start-date が要る)"))
    ap.add_argument("--start-date", type=str, default="",
                    help="開始日 YYYY-MM-DD(A1-1・manifest の start_sim_datetime)。空=今までの導き方")
    ap.add_argument("--holiday-csv", type=str, default=DEFAULT_HOLIDAY_CSV,
                    help="内閣府の祝日 CSV(cp932)。無ければ祝日を空にして警告(既定 data/calendar/syukujitsu.csv)")
    ap.add_argument("--school-holidays", type=str, default="",
                    help="学校の長期休みの区間 YYYY-MM-DD:YYYY-MM-DD をカンマ区切り(開始日の検査・既定は空)")


def calendar_kwargs_from_args(args: Any) -> dict[str, Any]:
    """``add_calendar_args`` と ``--response-delay`` の結果 → ``run_day`` の引数。"""
    return {
        "calendar_weekday": str(getattr(args, "calendar_weekday", DEFAULT_WEEKDAY_MODE)),
        "start_sim_datetime": (getattr(args, "start_date", "") or None),
        "holiday_csv": str(getattr(args, "holiday_csv", DEFAULT_HOLIDAY_CSV)),
        "school_holidays": str(getattr(args, "school_holidays", "") or ""),
        # None=未指定(録画・mock は 1、再生はテープの記録に合わせる=``_resolve_response_delay``)
        "response_delay": getattr(args, "response_delay", None),
    }


def fleet_from_args(args: Any, ap: "argparse.ArgumentParser | None" = None) -> FleetClient | None:
    """``add_fleet_args`` の結果 → ``FleetClient``(``--llm mock`` なら ``None``)。"""
    from shibuya.llm.fleet import FleetConfig
    from shibuya.manifest.schema import Mode as _Mode

    if getattr(args, "llm", "mock") != "fleet":
        return None
    eps = tuple(e.strip() for e in str(args.endpoints).split(",") if e.strip())
    if not eps:
        msg = "--llm fleet には --endpoints(カンマ区切り http://host:port)が要る"
        if ap is not None:
            ap.error(msg)
        raise SystemExit(msg)
    from shibuya.llm.fleet import DEFAULT_T1_MAX_TOKENS, DEFAULT_TEMPERATURE

    return FleetClient(
        FleetConfig(
            endpoints=eps,
            model=str(args.model),
            mode=_Mode(args.mode),
            run_id=str(getattr(args, "run_id", "")),
            run_seed=int(getattr(args, "seed", 0)),
            temperature=float(getattr(args, "temperature", DEFAULT_TEMPERATURE)),
            t1_max_tokens=int(getattr(args, "max_tokens", DEFAULT_T1_MAX_TOKENS)),
            # 0/未指定なら None=既定(max_in_flight×4)。C7 D-58 の回し直しで計画呼数以上を渡す。
            queue_capacity=(int(getattr(args, "fleet_queue_capacity", 0) or 0) or None),
        )
    )


def main(argv: list[str] | None = None) -> int:
    """``python -m shibuya.engine.run --agents 5000 --seed 1 --world data/world/v2``。"""
    ap = argparse.ArgumentParser(description="C2 エンジンの 1 シミュ日 mock ラン(予算行 W2)")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--world", type=str, default="data/world/v2",
                    help="世界資産ディレクトリ(無ければ合成小世界へ落ちる)")
    ap.add_argument("--cells", type=int, default=139, help="合成世界のセル数")
    ap.add_argument("--ticks", type=int, default=MINUTES_PER_SIM_DAY)
    ap.add_argument("--checkpoint-every", type=int, default=360)
    ap.add_argument("--day", type=int, default=0, help="曜日(0=月曜)")
    ap.add_argument("--growth-yaml", action="store_true", help="状態成長宣言 YAML を出力して終了")
    ap.add_argument("--no-processes", action="store_true",
                    help="世界過程(C4 第1陣)を止める(ablation の下限対照)")
    ap.add_argument("--no-population", action="store_true",
                    help="W16 母集団を使わず合成個体で回す(下限対照)")
    ap.add_argument("--ablate", action="append", default=[],
                    help="止める過程(過程 id か AB-* の感度試験 id・複数可)")
    ap.add_argument("--no-sleep-suppression", action="store_true",
                    help="D-56 就寝抑止を切る(=D-56 前の挙動・帰無腕)")
    ap.add_argument("--no-plan-sleep", action="store_true",
                    help="D-62「就寝は計画の実行」を切る(=D-62 前の挙動・帰無腕。"
                         "就寝境界も LLM に判断させ・tick 0 は全員 SLEEPING)")
    ap.add_argument("--no-plan-executor", action="store_true",
                    help="D-66 計画実行層(engine.presence)を切る(=現行挙動・帰無腕)")
    ap.add_argument("--group-norms", choices=("on", "off"), default="on",
                    help="群・規範の計器(D-107 (a)・読むだけ)を回すか(第309 Q150・既定 on)")
    ap.add_argument("--near-order", choices=NEAR_ORDERS, default=DEFAULT_NEAR_ORDER,
                    help="B5 近接行の並び(第304 Q130)。distance=距離の昇順・同点は --near-tiebreak の順(既定)/ id=旧挙動")
    ap.add_argument("--near-tiebreak", choices=NEAR_TIEBREAKS, default=DEFAULT_NEAR_TIEBREAK,
                    help="B5 近接行の距離の同点の切り方(第300 Q107)。hash=run_salt で撹拌(既定)/ id=旧挙動")
    ap.add_argument("--exit-mode", choices=PRESENCE_EXIT_MODES, default="immediate",
                    help="退出の実行形(immediate のみ実装・他は予約)")
    ap.add_argument("--attendance-rate", type=float, default=1.0, metavar="RATE",
                    help="出勤率(D-67 (b)・expedient E6・既定 1.0)")
    ap.add_argument("--derive-rule", choices=PRESENCE_DERIVE_RULES, default="v2",
                    help="在圏ブロックの読み口(v2=§2 追補・v1=原則のまま)")
    ap.add_argument("--no-outside-suppression", action="store_true",
                    help="D-66 域外抑止を切る(=D-66 前の挙動・帰無腕)")
    ap.add_argument("--geometry", choices=GEOMETRY_MODES, default=DEFAULT_GEOMETRY,
                    help="位置幾何(C9 G1/G2)。node=1 tick 1 ノード(既定・バイト不変)/"
                         "edge=辺上の連続位置+希望速度 1.00〜1.60 m/s+Kladek 減速")
    ap.add_argument("--area-source", choices=AREA_SOURCES, default=DEFAULT_AREA_SOURCE,
                    help="歩行可能面積の出所(C9c-1 G8 (b))。legacy=街路点×6.25 m²(既定・"
                         "バイト不変)/ plateau=c9c_walkable_area.parquet(PLATEAU 歩道部+"
                         "OSM×道路構造令の実測)")
    add_fleet_args(ap)
    add_calendar_args(ap)
    args = ap.parse_args(argv)

    if args.growth_yaml:
        print(GD.to_yaml())
        return 0

    world = World.load_or_synthetic(Path(args.world), n_cells=args.cells, seed=args.seed)
    res = run_day(
        n_agents=args.agents,
        seed=args.seed,
        world=world,
        ticks=args.ticks,
        checkpoint_every=args.checkpoint_every,
        day_index=args.day,
        world_dir=args.world,
        fleet=fleet_from_args(args, ap),
        fleet_wait_s=float(args.fleet_wait_s),
        fleet_debug_dir=args.fleet_debug_dir or None,
        tape_path=args.tape or None,
        processes=not args.no_processes,
        processes_disabled=tuple(args.ablate) or None,
        population=False if args.no_population else None,
        sleep_suppression=not args.no_sleep_suppression,
        plan_sleep=not args.no_plan_sleep,
        plan_executor=not args.no_plan_executor,
        exit_mode=str(args.exit_mode),
        near_tiebreak=str(args.near_tiebreak),
        near_order=str(args.near_order),
        group_norms=str(args.group_norms),
        attendance_rate=float(args.attendance_rate),
        derive_rule=str(args.derive_rule),
        outside_suppression=not args.no_outside_suppression,
        geometry=str(args.geometry),
        area_source=str(args.area_source),
        **calendar_kwargs_from_args(args),
    )
    print(res.summary())
    return 0 if (res.conserved and res.min_stock >= 0) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
