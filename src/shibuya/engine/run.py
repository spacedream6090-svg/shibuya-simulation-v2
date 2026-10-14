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
  T × tick_seconds``。``start_sim_datetime`` を渡さないランは ``DEFAULT_WORLD_START``(2026-07-13)+ ``day_index`` 日
  (〔第330・RET〕10e より前の「気象の再生実日を世界の日付にする」導き方は消した)。manifest に ``tick_seconds``・
  ``start_sim_datetime`` を書く(10a)。
- **通しの時刻 T**(10a・A1): ループの変数 ``tick`` は ``T = 日 × 1 日の tick 数 + 日の中の tick``。乱数とハッシュの
  鍵・call_id・テープの tick 欄・tick を値に持つ状態は T を使い、日の中の時刻で引く表(計画境界・食事の予定など)は
  ``T % 1 日の tick 数`` で引く。1 日のラン(既定)では T = tick なので値は今と同じ。
- 顕著行為(B4 の「顕著行為の到達」)は C3 では**常に空**(世界過程が C4)。流れも 0。
- 会話の招待は「resolve が ``会話`` を成立させた対」を入口にする(契約書 §3 の順序
  「招待→応答判定」の応答判定を resolve の直後に置いた)。相手側の ``activity`` は
  resolve が変えないため、相手の離脱は ``cell`` 監視で検出する。
- 週の曜日は ``day_index``(既定 0=月曜)。週 7 日表は C4 の PlanSpec。10a からは曜日・土休・祝日を引く箇所は
  すべて暦の口を通す(〔第330・ACT〕既定は ``--calendar-weekday real``・``--weather-scheme calendar``・開始日
  2026-07-13(月)=``engine.calendar.CALENDAR_UNIFIED``)。
- **応答の遅れ**(10a・A9): 既定 ``response_delay=1``=艦隊/再生の到着の受け取りを①(反映)の直前に置き、
  下限を ``max(t_apply, tick)`` にする=tick T に発射した呼は T+1 の①で反映される。``2`` は旧(受け取りは
  ④′・下限 ``tick + 1``=T+2)で、旧い実 LLM テープ(17 本)の再生のために残す。mock は同期で既に +1。
"""

from __future__ import annotations

import argparse
import copy
import warnings
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Final, Mapping

import blake3 as _blake3
import numpy as np

import dataclasses

from shibuya.agents.population import Population, load_population, sample_population
from shibuya.agents.state import (
    N_WAKE_CONDITIONS_ALL,
    Activity,
    AgentState,
    WakeCondition,
)
from shibuya.core.growth import GrowthReport
from shibuya.core.rng import RNG_SCHEME
from shibuya.core.types import DEFAULT_TICK_SECONDS, MINUTES_PER_SIM_DAY
from shibuya.engine import commit as C
from shibuya.engine import growth_decl as GD
from shibuya.engine import resolve as R
from shibuya.engine.activity import payload_of
from shibuya.engine.calendar import (
    DEFAULT_HOLIDAY_CSV,
    WEATHER_SCHEME,
    WEEKDAY_MODE,
    SimCalendar,
)
from shibuya.engine.intent import INTENT_MAX_TICKS
from shibuya.engine.familiarity import FAMILIARITY_K
from shibuya.engine.memory import MEMORY_N, RECALL_TAU
from shibuya.engine.wom import DEFAULT_WOM_SOURCE
from shibuya.engine.relations import (
    REL_D,
    REL_K,
    REL_TENURE_WEEKS,
    DEFAULT_REL_TENURE_HASH,
)
from shibuya.engine.store_memory import DEFAULT_STORE_DECAY, STORE_MEMORY_N
from shibuya.engine.energy import DEFAULT_ENERGY_RATE, DEFAULT_HOME_MEAL, DEFAULT_MEAL_SLEEP_DEFER
from shibuya.engine.arbiter import L4_LINE_PER_AGENT_DAY
from shibuya.engine.chooser import DEFAULT_CHOOSER, HABIT_P, RANK_TAU
from shibuya.engine.classical import (
    DEFAULT_ACTIVITY_REGION,
    DEFAULT_CLASSICAL_SOCIAL,
    DEFAULT_MEAL_GATE,
    DEFAULT_POLICY,
)
from shibuya.engine.geometry import (
    DEFAULT_GEOMETRY,
    DESIRED_SPEED_MAX_MS,
    DESIRED_SPEED_MIN_MS,
    GEOMETRY_MODES,
)
from shibuya.engine.ledger_api import LedgerBundle
from shibuya.engine.processes.opening import rows_of_day as _opening_rows_of_day
from shibuya.engine.presence import DERIVE_RULES as PRESENCE_DERIVE_RULES
from shibuya.engine.presence import EXIT_MODES as PRESENCE_EXIT_MODES
from shibuya.engine.poi_target import DEFAULT_POI_TARGET, MOVE_SEARCH_RADIUS_CELLS
from shibuya.engine.llm_bridge import DEFAULT_LANE, delta_think_ticks
from shibuya.engine.scheduler import DIAG_COLUMNS
from shibuya.engine.state_hashes import FINAL_DEFINITION
from shibuya.engine.tape import Replay, read_run_meta
from shibuya.llm.contract import TargetKind
from shibuya.llm.fleet import FleetClient
from shibuya.llm.mock import MockLLM
from shibuya.perception.channels import BudgetMode
from shibuya.perception.facts import percept_manifest as _percept_manifest
from shibuya.engine.decision import layer as _DECISION
from shibuya.perception.renderer import (
    DEFAULT_HUNGER_WORDS,
    DEFAULT_NEAR_ORDER,
    DEFAULT_NEAR_TIEBREAK,
    NEAR_ORDERS,
    NEAR_TIEBREAKS,
    SIGNAGE_P_SEE_DEFAULT,
)
from shibuya.perception.templates import INTENT_MODES, VOCAB_VERSIONS, check_vocab_version
from shibuya.world.assets import AREA_SOURCES, DEFAULT_AREA_SOURCE
from shibuya.world.state import World
from shibuya.core.time_consts import CLOCK_KIND, HOURS_PER_DAY, MINUTES_PER_DAY, SECONDS_PER_DAY, SECONDS_PER_MINUTE

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
    tape_dir = _replay_tape_dir(replay)
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


def _replay_tape_dir(replay: Any) -> Path:
    """再生の入力(``Replay`` かテープのディレクトリ)→ テープのディレクトリ。"""
    if isinstance(replay, Replay):
        return Path(replay.tape.path)
    return Path(getattr(replay, "path", None) or replay)


#: 10e(検収 L1): テープの脇の meta に書く乱数の鍵の配置の印。10c〜10f の counter(K19 の並べ方の前)と見分ける。
RNG_LAYOUT: Final[str] = "10e"


def check_replay_tape(mode: str = "record", replay: Any = None) -> None:
    """〔第330・RET〕再生するテープが今の版で録られたかを確かめる(違えば止める=警告ではなく例外)。

    テープの脇の meta(``run_meta.json``)が ``rng_scheme="counter"``・``rng_layout="10e"``・``calendar_weekday="real"``・
    ``weather_scheme="calendar"`` を持つテープだけを再生する。10e より前の録画(乱数 stateful・10c〜10f の counter の
    並べ方・記録の無いテープ)と、版上げ 1 回目の活性化より前の録画(暦の規則の記録が無い・day_index・legacy)は、
    それを再現する切替口(``--rng-scheme stateful``・``--calendar-weekday day_index``・``--weather-scheme legacy``)を
    版上げ 1 回目の後に消したので再生できない。手元の実テープ(版 1〜2・52 本)はどれも 10e より前の録画
    (10e の記録 §RET)。録画・mock では何もしない。
    """
    if mode != "replay" or replay is None:
        return
    tape_dir = _replay_tape_dir(replay)
    meta = read_run_meta(tape_dir)
    got = {k: meta.get(k) for k in ("rng_scheme", "rng_layout", "calendar_weekday", "weather_scheme")}
    want = {"rng_scheme": RNG_SCHEME, "rng_layout": RNG_LAYOUT, "calendar_weekday": WEEKDAY_MODE,
            "weather_scheme": WEATHER_SCHEME}
    if got != want:
        bad = ", ".join(f"{k}={got[k]!r}(要 {want[k]!r})" for k in want if got[k] != want[k])
        raise ValueError(
            f"このテープは 10e より前(または版上げ 1 回目の活性化より前)の録画で、今の版では再生できない"
            f"({tape_dir.name}: {bad})。旧値の再現の切替口は版上げ 1 回目の後に消した"
        )


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
    ``calendar`` に整数を渡したときは ``SimCalendar.default``(2026-07-13 + その日数)で包む(〔第330・RET〕旧い口 legacy を消した)。
    """
    if not isinstance(calendar, SimCalendar):
        calendar = SimCalendar.default(int(calendar), tick_seconds=int(tick_seconds))
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
            minute = int(t * int(tick_seconds) // SECONDS_PER_MINUTE) % om.shape[1]
            later = np.flatnonzero(om[poi, minute + 1:])
            if later.size:
                nxt = minute + 1 + int(later[0])
            elif pa is not None and getattr(pa, "plan_poi", None) is not None:
                nxt_wd = calendar.opening_row(calendar.day_of(t) + 1)  # 10a #8: 翌日の行(〔第330〕祝日は PH)
                sel = (np.asarray(pa.plan_poi) == poi) & _opening_rows_of_day(
                    pa.plan_poi, pa.plan_day, int(nxt_wd), getattr(pa, "plan_ph_poi", None))
                if bool(np.any(sel)):
                    nxt = int(np.asarray(pa.plan_start)[sel].min()) % MINUTES_PER_DAY
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


#: **10f(K21 (a))母集団の側の乱数**(用途名 → 何を決めるか)。``run_day(population_seed=…)`` の値から引く。
#: 振り分けの規則(実行役の構成=未リサーチ(expedient)): 体の属性(誰が居るか・体の定数・財布・日課)と、その体が
#: 暮らす舞台の構造(合成小世界の店の配置と在庫=世界資産の代わり)を決める流れ。salt(動きの seed)を変えても動かない。
#: ``world.synthetic`` を環境の側にしない理由: 世界資産(固定のデータ)の代わりの構造で、日ごとに変わる出来事ではない。
#: 環境の側に置くと「天気も変える」salt の比較で地図そのものが変わる(mock の拠点はセルの上に引くので母集団と組)。
POPULATION_RNG_DOMAINS: dict[str, str] = {
    "w16.sample.reserved": "W16 母集団の定員先取り層の抽出(agents.population.sample_population)",
    "w16.sample.stratum": "W16 母集団の統計層の抽出(同上・層ごとの流れ)",
    "wallet.initial": "世帯の初期財布(cli.household_wallets・母集団の種別から)",
    "agent.schedule": "mock 日課(拠点・境界の時刻・mock の初期所持金。W16 の体は拠点と種別を上書き)",
    "body.weight": "体重(engine.energy.draw_bodies・体ごと)",
    "body.eer": "推定エネルギー必要量のばらつき(同上)",
    "geometry.desired_speed": "希望歩行速度(engine.geometry.desired_speeds・--geometry edge のときだけ)",
    "engine.processes.rail": "域外居住の通勤者の抽選と路線(計画実行層の無いランだけ)",
    "world.synthetic": "合成小世界の店の種別と在庫(世界資産が無いときだけ・舞台の構造)",
}
#: **10f 第 2 段の直し(S1・ユーザー決定 2026-10-07)環境の側の乱数**。``run_day(environment_seed=…)`` の値から引く。
#: 外から与える舞台の出来事(気象・大きな催し・道路工事)。「天気は同じで動きだけ変える」比較では固定し、
#: 「天気も変える」比較では salt と一緒に変える(``tools/c7/salt_runs.py --environment-mode``)。
ENVIRONMENT_RNG_DOMAINS: dict[str, str] = {
    "engine.processes.environment": "気象の再生実日の層と日(manifest の replay_date・start_sim_datetime・calendar)",
    "world.large_event": "大きな催しの会場の抽選(日ごと)",
    "world.road_works": "道路工事の辺の抽選(日ごと)",
}
#: **10f(K21 (a))動きの側の乱数**(用途名 → 何を決めるか)。``seed`` から引く(salt)。
#: ``world.delivery_inbound`` は動きの側(ユーザー決定 2026-10-07): 配送は本来、店の発注と配達員(エージェントの
#: 行動)で決まるもので、今のエンジンの処理は**つなぎ**(つなぎの台帳に載せる扱い)。
MOTION_RNG_DOMAINS: dict[str, str] = {
    "engine.chooser": "店・行き先の候補の選び手(poi_target・store_choice も同じ流れ)",
    "policy.classical": "古典の方策の抽選",
    "conversation.invite": "会話の招待の抽選",
    "llm.mock": "mock の応答(行為の抽選)",
    "decision.present": "候補の口の提示の並べ替え(第 1 期 1-8 J0・腕 --decision-port port のランだけ)",
    "llm.mock.move_target": "mock の移動の対象",
    "llm.mock.out_of_cell_target": "mock のセル外の店の対象",
    "perception.attention.p_see": "注視ゲート(看板・親しみの露出)",
    "perception.p_notice": "顕著行為に気づくか",
    # 〔第330・RET〕stateful の 2 本(world.salient・world.public_service_dispatch)は切替口と一緒に消した
    "world.salient.counter": "顕著行為の発生(counter)",
    "world.public_service_dispatch.counter": "出動の遅れ(counter)",
    "world.delivery_inbound": "入荷の抽選(つなぎ: 本来は店の発注と配達員の行動)",
    "world.delivery_last_mile": "配達の予約(引くだけ)",
}
#: 動きの側の、``core.rng`` の用途名を持たない塩(``seed`` から作る)。
MOTION_SALTS: dict[str, str] = {
    "run_salt": "blake3(seed‖engine): アービタの同点・適用の順・近接行の同点・歩きの行き先・関係の招待の重み",
    "attendance": "blake3(attendance‖seed‖日): 出勤率の抽選(engine.presence.attendance_draw)",
    "fleet.call_seed": "xxh64(call_id, seed): 艦隊の呼ごとのデコードの種",
}


def resolve_sub_seed(seed: int | str, sub_seed: int | str | None) -> int | str:
    """10f: 母集団・環境の seed(``None`` なら ``seed`` と同じ値=今と同じ)。

    渡したときだけ ``core.rng`` の master_seed と同じ型と範囲の検査をする(bool・負・空の文字列を止める)。
    """
    if sub_seed is None:
        return seed
    from shibuya.core.rng import derive_key

    derive_key(sub_seed, "seed.check")  # 検査だけ(鍵は使わない)
    return sub_seed


def resolve_population_seed(seed: int | str, population_seed: int | str | None) -> int | str:
    """10f(K21 (a)): 母集団の seed(``resolve_sub_seed`` と同じ)。"""
    return resolve_sub_seed(seed, population_seed)


def resolve_environment_seed(seed: int | str, environment_seed: int | str | None) -> int | str:
    """10f 第 2 段の直し(S1): 環境の seed(``resolve_sub_seed`` と同じ)。"""
    return resolve_sub_seed(seed, environment_seed)


def _same_seed(a: int | str, b: int | str) -> bool:
    """2 つの seed が ``core.rng`` で同じ鍵になるか(``1`` と ``"1"`` は別=``i:1`` と ``s:1``)。"""
    return type(a) is type(b) and a == b


def run_salt_for(master_seed: int | str) -> bytes:
    """``blake3(master_seed ‖ 0x1f ‖ "engine")`` の先頭 16 バイト(親の指定)。"""
    text = f"i:{int(master_seed)}" if not isinstance(master_seed, str) else f"s:{master_seed}"
    return _blake3.blake3(f"{text}\x1fengine".encode("utf-8")).digest(length=16)


@dataclass(frozen=True)
class _RunDayLocals:
    """10b: ``run_day`` の局所の状態(状態台帳 O43・O44)を full-hash の持ち主として渡す入れ物。"""

    pending: list
    fleet_deferred: list
    fleet_waiting: set
    replay_inbox: dict


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
    #: 10b(A2・A3): **behavior-hash**(``engine.state_hashes.behavior_hash``=``combined`` と同じ組み立てで、
    #: SoA は状態台帳の軸 1 が behavior の列だけ+外の状態の軸 1 が behavior の行)。記録と manifest に出すだけで ``combined`` には**混ぜない**。
    behavior_hash: str = ""
    #: 10b: **full-hash**(SoA+知覚 SoA+外の状態のうち軸 2 が要る・導出できる・不明の行)。``combined`` には混ぜない。
    full_hash: str = ""

    @property
    def combined(self) -> str:
        """final(T1/T2 の一致判定)=behavior-hash(10e E1)。〔第330・RET〕旧い組み立て(``--hash-scheme full``・
        ``legacy_combined``)は版上げ 1 回目の後に消した。"""
        if not self.behavior_hash:
            raise ValueError("checkpoint に behavior_hash が無い(final は behavior-hash)")
        return self.behavior_hash


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
    calls_by_hour: list[int] = field(default_factory=lambda: [0] * HOURS_PER_DAY)
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
    #: 〔第 1 期 1-2〕看板の注視の活動の乗数は消した=値は常に None(manifest の欄は残す)。
    p_see_activity: Any = None
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
    wake_rate_by_hour: list[float] = field(default_factory=lambda: [0.0] * HOURS_PER_DAY)
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
    #: 10c・10e: 乱数の方式の名前(manifest の ``rng_scheme``=``counter`` だけ・〔第330・RET〕stateful は消した)。
    rng_scheme: str = RNG_SCHEME
    #: 10e(E1): final の定義(manifest の ``hash_scheme``)。〔第330・RET〕切替口を消したので常に ``behavior``(記録だけ)。
    hash_scheme: str = FINAL_DEFINITION
    #: 第 1 期 1-4(CP5-5): ランの種類(``engine.run_kind``)。``cli.run`` が決めて置く(``cli.main`` も同じ)。``None``=
    #: 決めていない(``run_day`` を直に呼んだラン=manifest は null)。記録だけ(状態にも指紋にも入らない)。
    run_kind: str | None = None

    #: 10e(B6): 天気の規則と日ごとの暦の日付・再生日・層・影・警告(``EnvironmentProcess.weather_manifest``)。
    #: 世界過程の無いランは規則だけ。manifest の ``weather``(設定の節)。
    weather: dict[str, Any] = field(default_factory=dict)
    # ---- 10b: 状態台帳の 2 つのハッシュ(final には混ぜない) ----
    #: 最後の checkpoint の full-hash の外の状態の行ごとの直列化のバイト数(台帳の鍵 → B)。
    full_hash_bytes: dict[str, int] = field(default_factory=dict)
    #: 検収後 P2: 日の締めの**後**の behavior-hash・full-hash・外の状態のバイト(10d の再開の判定はこちら)。
    state_hashes_end_of_day: dict[str, Any] = field(default_factory=dict)
    #: checkpoint ごとの時間[s](壁時計=決定論でない・T7 の最大を見る診断。manifest には出さない)。
    checkpoint_seconds: list[float] = field(default_factory=list)
    # ---- 10d: 複数日のランと再開 ----
    #: 日ごとの締めの記録(日・終わりの T・お金・体の数・台帳のセンサスの行・締めの後の 2 つのハッシュ)。
    #: 締めの回数=このランで締めた日の数(manifest の ``daily``)。
    daily: list[dict[str, Any]] = field(default_factory=list)
    #: 日の頭(1 日目から)の記録(お金・体の数)。manifest の ``day_heads``。
    day_heads: list[dict[str, Any]] = field(default_factory=list)
    #: 再開の欄(ラン ID・親のラン・始めと終わりの T・``finished``・書いた状態のファイル・K9 のつなぎの日)。
    resume: dict[str, Any] = field(default_factory=dict)
    #: 10f(K26 (a)): 環境の欄(``engine.resume.environment_fields``)。manifest の ``environment``・``env_id``。
    env_fields: dict[str, Any] = field(default_factory=dict)
    #: 10f(K21 (a)): 母集団の seed(``None``=``seed`` と同じ値。``run_day`` が実際に使った値を入れる)。
    #: manifest の ``population_seed``(設定の節)。
    population_seed: int | str | None = None
    #: 10f 第 2 段の直し(S1): 環境の seed(``None``=``seed`` と同じ値)。manifest の ``environment_seed``(設定の節)。
    environment_seed: int | str | None = None
    #: checkpoint ごとの列・外の状態の行の digest(``checkpoint_detail=True`` のときだけ・manifest には出さない)。
    checkpoint_details: list[dict[str, Any]] = field(default_factory=list)
    #: 〔第 1 期 1-7〕道具の台帳 C0 の計器(``engine.tools.record.manifest_fields``)。manifest の ``tools``(観測)。組み立てを
    #: 通らない結果は ``None``。
    tools: dict[str, Any] | None = None

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

    def state_hashes_fields(self) -> dict[str, Any]:
        """10b: 状態台帳の版・最後の checkpoint の behavior-hash と full-hash・外の状態の直列化のバイト数。"""
        from shibuya.engine.state_ledger import LEDGER_VERSION

        last = self.checkpoints[-1] if self.checkpoints else None
        return {
            "ledger_version": LEDGER_VERSION,
            "behavior_hash": last.behavior_hash if last is not None else "",
            "full_hash": last.full_hash if last is not None else "",
            "full_external_bytes": int(sum(self.full_hash_bytes.values())),
            "full_external_bytes_by_row": dict(self.full_hash_bytes),
        }

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
            第 1 期 1-4: 末尾に ``bridges_count``(つなぎの台帳の active の行の数)・``rules_version``(規則の表の
            sha)・``run_kind``(ランの種類=``engine.run_kind``・``run_day`` を直に呼んだランは ``None``)・
            ``bridges_version``(台帳の中身の sha)。台帳と表のファイルが無い写しでは台帳と表の欄は ``None``。
            第 1 期 1-5: 末尾に ``rights``(権利台帳の行数と種類の分布・空欄のつなぎの台帳の行・許可のない行動の数。
            世界過程の無いランは ``None``)。
            第 1 期 1-7: 末尾に ``tools``(道具の台帳の数と名・グループの数・連絡先の印の数・店の番号の表・看板の作り物の
            印。組み立てを通らない結果は ``None``)。
        """
        from shibuya.engine import manifest_sections as _MS
        from shibuya.engine import run_kind as _RK
        from shibuya.engine.rights import record as _RR
        from shibuya.engine.bridging import ledger as _BR
        from shibuya.engine.rules import table as _RT
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
            # ---- 10c(Q8): 顕著行為の発生と出動の遅れの乱数の方式(列追加のみ) ----
            "rng_scheme": str(self.rng_scheme),
            # ---- 10b(A2・A3): 状態台帳の 2 つのハッシュ(最後の checkpoint の値・列追加のみ・final は今の定義) ----
            "state_hashes": self.state_hashes_fields(),
            # 検収後 P2: 日の締めの後の 2 本(10d はこちら。最後の checkpoint の値=上とは別物)
            "state_hashes_end_of_day": dict(self.state_hashes_end_of_day),
            # ---- 10d: 再開の欄(ラン ID・親のラン・区間・finished・状態のファイル)と日ごとの締め(列追加のみ) ----
            "resume": dict(self.resume),
            "finished": bool(self.resume.get("finished", True)),
            "parent_run": self.resume.get("parent_run"),
            "resumed_at_T": (self.resume.get("parent_run") or {}).get("resume_T"),
            "daily": [dict(r) for r in self.daily],
            "day_heads": [dict(r) for r in self.day_heads],
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
            "p_see_activity": None,  # 〔第 1 期 1-2〕活動の乗数は消した(欄は残して null)
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
            # ---- 10f(K26 (a)・K22 (a)): 環境の欄と、欄の節(設定・観測・環境)の表。列追加のみ ----
            "env_id": str(self.env_fields.get("env_id", "")),
            "environment": copy.deepcopy(self.env_fields),  # 10f 検収 N9: 深い写し
            "manifest_sections": _MS.sections_table(),
            # ---- 10f 第 2 段(K21 (a)): 母集団の seed(動きの seed は checkpoints の JSON の ``seed``)。列追加のみ ----
            "population_seed": (self.seed if self.population_seed is None else self.population_seed),
            # ---- 10f 第 2 段の直し(S1): 環境の seed(気象・大きな催し・道路工事)。列追加のみ ----
            "environment_seed": (self.seed if self.environment_seed is None else self.environment_seed),
            # ---- 10e(E1): final の定義(behavior=behavior-hash が既定・full=旧い組み立て)。列追加のみ ----
            "hash_scheme": str(self.hash_scheme),

            # ---- 10e(B6): 天気の規則と日ごとの暦の日付・再生日・層・影(列追加のみ) ----
            "weather": copy.deepcopy(self.weather),
            # ---- 第 1 期 1-1 T0(TM9・GPU 無しの欄・10f と一体): 呼び出し数を判断モデルと LLM に分けた欄(判断モデルは
            # まだ無い=0)・時計の種類と幅・つなぎの台帳の数。列追加のみ ----
            "calls_by_model": {"judge_model": 0, "llm": int(self.llm_calls)},
            "clock_kind": CLOCK_KIND,
            "step_seconds": int(self.tick_seconds),
            # ---- 第 1 期 1-4: つなぎの台帳の件数(T0 で null にした欄を件数に)・規則の表の版(表の sha=CP10)・
            # ランの種類(CP5-5)。どれも記録だけ(final・behavior-hash は manifest を読まない)。列追加のみ ----
            "bridges_count": _BR.bridges_count(),
            "rules_version": _RT.rules_version(),
            "run_kind": _RK.resolve(self.run_kind),
            # 1-4 検収 L1: つなぎの台帳の中身の sha(件数が同じ書き換えも見分ける=CP10 の版とハッシュ)。列追加のみ
            "bridges_version": _BR.bridges_version(),
            # ---- 第 1 期 1-9(CP2 の段階 1・K17): 金の生ログの輪の容量と溢れ・transfer の計器(台帳が無いランは空)。
            # 末尾=T0 の TM9 → 1-4 の欄 → 1-9。列追加のみ ----
            "economy": self.economy_fields(),
            # ---- 第 1 期 1-2(知覚の分離): Percept の形の版・欄の数と名・空の欄の一覧(計器・設定)。末尾=T0 の TM9 →
            # 1-4 の欄 → 1-9 の economy → 1-2。列追加のみ ----
            "percept": _percept_manifest(),
            # ---- 第 1 期 1-5: 権利台帳の行数と種類の分布・空欄のつなぎの台帳の行・許可のない行動の数(計器・CP4・CP3)。
            # 世界過程の無いランは None。記録だけ(final・behavior-hash は manifest を読まない)。列追加のみ ----
            "rights": _RR.manifest_fields(getattr(self, "runner", None), self.bridge_counters),
            # ---- 第 1 期 1-8 J0(候補の口): 腕の名・口の実装・候補の源の分布・「その他」の割合・選んだ番号(計器)。末尾=
            # T0 の TM9 → 1-4 の欄 → 1-9 の economy → 1-2 の percept → 1-5 の rights → 1-8。腕 legacy のランは観測の子が
            # null。列追加のみ ----
            "decision_port": _DECISION.manifest_fields(getattr(self, "decision_layer", None)),
            # ---- 第 1 期 1-7(道具の台帳 C0・CT0・CT5・CT10): 道具の数・グループの数・連絡先の印の数・店の番号の表・看板の
            # 作り物の印(計器)。末尾=… → 1-5 の rights → 1-8 の decision_port → 1-7。記録だけ(final・behavior-hash は
            # manifest を読まない)。列追加のみ ----
            "tools": copy.deepcopy(self.tools),
        }

    def economy_fields(self) -> dict[str, Any]:
        """第 1 期 1-9: manifest の ``economy``(K17 の輪の容量 ``raw_capacity``・溢れ ``raw_overflow``・transfer の行
        ``transfers_total`` ほか=``LedgerBundle.economy_record``)。台帳の無いランは空。計器はこのランの中で数えた分。"""
        led = getattr(self, "ledger", None)
        fn = getattr(led, "economy_record", None) if led is not None else None
        return dict(fn()) if fn is not None else {}

    def l4_audit_fields(self) -> dict[str, Any]:
        """L4 の監査欄(D-110「ランごとの総呼数を必ず記録」)。

        ``llm_calls_total``=発射した呼の数(再送も 1 呼=``llm_calls``)・``llm_calls_per_agent_day``=
        総呼数 ÷ 体数 ÷ シミュ日数(``ticks × tick_seconds / 86,400``)・``l4_line``=監査線
        ``L4_LINE_PER_AGENT_DAY``(10 呼/体/日)・``l4_exceeded``=線を超えたか・``l4_notes``=注記。
        """
        days = float(self.ticks) * float(self.tick_seconds) / SECONDS_PER_DAY
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
        _frozen_text = {k: v for k, v in self.frozen_sources.items() if ":" not in k}  # 10e(B0): 資産の指紋は除く
        if _frozen_text:
            lines.append("  凍結静的文 " + " ".join(f"{k}={v[:16]}" for k, v in sorted(_frozen_text.items())))
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
        pop = sample_population(pop, n_agents, seed)  # 10e(E4・K19): 層の鍵の並べ方
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


def _call_ref(res: Any) -> tuple[int, str]:
    """応答 → ``(発射の tick, call_id)``(10b・保留の組の末尾 2 要素)。

    call_id は ``LLMBridge.call``・艦隊の発射と同じ式 ``"{tick}:{agent}:{wake_class}"``(テープの call_id 列と一致)。
    """
    t = int(res.tick)
    return t, f"{t}:{int(res.agent_id)}:{int(res.wake_class)}"


def _split_due(pending: list, tick: int) -> tuple[list, list]:
    """保留の組を「この tick に適用する分」と「残り」に分ける(元の並びを保つ・10b で関数に出しただけ)。"""
    return [p for p in pending if p[0] <= tick], [p for p in pending if p[0] > tick]


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
    population_seed: int | str | None = None,
    environment_seed: int | str | None = None,
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
    holiday_csv: "str | Path" = DEFAULT_HOLIDAY_CSV,
    school_holidays: Any = (),
    response_delay: int | None = None,

    state_out: "str | Path | None" = None,
    stop_at_tick: int | None = None,
    resume_from: "str | Path | None" = None,
    run_id: str = "",
    checkpoint_detail: bool = False,

    weather_perturb: bool = False,
) -> RunResult:
    """1 シミュ日(既定 1,440 tick)の mock ランを回す。

    Args:
        n_agents: 個体数。
        seed: manifest の ``master_seed``。10f(K21 (a))からは**動きの seed**(salt)。``population_seed`` を
            渡さないときは母集団の側にも同じ値を使う(既定の結果は今と同じ)。
        population_seed: **10f(K21 (a))母集団の seed**。``None``(既定)= ``seed`` と同じ値。母集団の側の乱数
            (W16 の抽出 ``w16.sample.*``・mock 日課 ``agent.schedule``・体の定数 ``body.*``・希望歩行速度
            ``geometry.desired_speed``・域外居住 ``engine.processes.rail``・合成世界 ``world.synthetic``)はこの値から
            引く。気象・大きな催し・道路工事は ``environment_seed`` から引く。ほかの乱数(選び手・mock の応答・知覚・
            会話・顕著行為や入荷などの世界の出来事・``run_salt``・出勤の抽選など)は ``seed`` から引く。用途名ごとの表は
            ``POPULATION_RNG_DOMAINS``。salt の比較では母集団を固定して ``seed`` だけを変える。
        environment_seed: **10f 第 2 段の直し(S1)環境の seed**。``None``(既定)= ``seed`` と同じ値。気象の再生実日
            (``engine.processes.environment``)・大きな催し(``world.large_event``)・道路工事(``world.road_works``)
            はこの値から引く(``ENVIRONMENT_RNG_DOMAINS``)。
        world: 世界(None なら ``World.synthetic(n_cells, population_seed)``)。
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
        p_see_activity: 〔第 1 期 1-2・決定 10-12 §1-6「係数で持たない」〕5 段目 5c(D-117)の看板の注視 p_see に
            掛ける活動の種別の乗数は**消した**(既定のランで効く道が無かった=byte-check 19 構成で結果不変)。引数は
            設定の指紋(``_call_args``)と 1-0 の引数の数を変えないため残し、``None`` 以外は ``ValueError``。
            manifest の欄 ``p_see_activity`` は残して値は null。
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
        sim_days: **複数日の通しラン**(10a の口・10d で世界資産・台帳・艦隊にも広げた)。既定 1。2 以上では
            ``ticks`` を 1 日の tick 数にして、同じプロセスで T = 0〜``sim_days × 1 日の tick 数``−1 を続けて回す。
            各日の終わりに日次の締め(``runner.end_of_day``・台帳の締め・日次センサス)を 1 回走らせ、締めの後の
            2 つのハッシュを日ごとに ``RunResult.daily`` に記録する。次の日の頭の初期化(``initialize``・初期の
            活動・域外の配置・空腹の初期値・初期の財布・店舗の参入資本・帳簿の作り直し)は**走らせない**(A11)。
            日の頭で張り直すのは、鉄道の時刻表(T の座標で末尾に足す)・計画実行層の在圏ブロックとイベント
            (出勤率は日番号つきの鍵で引き直す)・計画境界の表(W17 は K9 のつなぎ=月曜の行)・天気の実日。
            営業時間(W7)・世界過程の日ごとの乱数の表・食事の予定は 0 日目の表を繰り返す(宣言・10d README)。
            再生(replay)とは一緒に使えない。
        start_sim_datetime: **10a(A1-1)の開始日の欄**(``datetime``・``date``・``"YYYY-MM-DD"``)。``None``
            (既定)は ``DEFAULT_WORLD_START``(2026-07-13・月)+ ``day_index`` 日。渡すと T=0 の世界内日時(プロンプトの
            日付)と暦の日付になる。曜日・土休・祝日は日付と内閣府の祝日から(祝日は土休・曜日 7 日の表では日曜の行・W7 は
            PH の行)。曜日・土休・祝日を引く 18 か所は暦の口(``engine.calendar.SimCalendar``)を通す。〔第330・RET〕10e
            より前の曜日の決め方 ``day_index`` と切替口 ``calendar_weekday`` は消した。
        holiday_csv: 祝日 CSV の場所(既定 ``data/calendar/syukujitsu.csv``)。読めなければ開始日の検査で止める。
            読んだ md5 を manifest の ``calendar.holiday_csv_md5`` に書く。
        school_holidays: 学校の長期休みの区間の一覧(``"YYYY-MM-DD:YYYY-MM-DD,…"`` か組の列)。開始日の検査で
            当たれば止める。既定は空(表の中身は K7 の判断待ち)。
        response_delay: **10a(A9)の応答の遅れの切替口**(``None``=未指定は 1。再生ではテープの脇の meta の値と
            突き合わせて違えば止め、値の無い旧テープは 2 とみなす=検収後 P3)。``1``=艦隊/再生の到着の受け取りを①の
            直前に置き下限 ``max(t_apply, tick)``(発射 +1 tick で反映)/ ``2``=旧(受け取りは④′・下限
            ``tick + 1``=+2 tick)。旧い実 LLM テープの再生は ``2`` で回す。mock(``fleet=None`` かつ再生の
            到着が無い)はこの分岐を通らない=結果は動かない。
        (乱数: 10c・10e の counter=顕著行為の発生を ``(seed, 名前, T)``・出動の遅れを ``(seed, 名前, T, セル, k)`` から毎回
        作る・K19 の鍵の並べ方。〔第330・RET〕10e より前の ``stateful`` と切替口 ``rng_scheme`` は消した。manifest の
        ``rng_scheme`` は ``counter`` の記録)
        state_out: **10d の状態の書き出し先**(ディレクトリ)。渡すと各日の締めの後(複数日のランの途中の日)と、
            ``stop_at_tick`` で止めたとき、ランの最後(``finished: true``)に、状態のまとまりを 1 ファイルずつ
            書く(``engine.resume``・名前は ``state-T<次に回す T>.npz``=10f の npz+json。10d の ``.pkl`` は 10e で読み口を消した)。``None``(既定)=書かない。
        stop_at_tick: **10d の止める時刻**(通しの時刻 T・その tick の手前で止める)。日の境目(1 日の tick 数の
            倍数)なら直前の日の締めの後、日の途中(試験用・A10)なら締めずにそこで状態を書いて止める。
            ``state_out`` が要る。止めたランは ``finished: false``。
        resume_from: **10d の再開**(状態のファイル)。日の頭の初期化(``initialize``・初期の活動・域外の配置・
            空腹の初期値・初期の財布・関係の初期の辺)を走らせず、保存した状態を読んで続ける(A11)。設定の指紋が
            親と違う・親が ``finished: true``・状態台帳の版が違う ならば止める。台帳を渡すときは初期の入れ直しを
            していない新しい台帳(``cli.build_ledger_bundle(endow=False)``)。``sim_days`` は親と同じ通しの日数。
        run_id: manifest のラン ID(空なら設定の指紋・始めの T・親のラン ID から作る)。
        checkpoint_detail: checkpoint ごとに列ごと・外の状態の行ごとの digest も控える(食い違いの場所を探す道具
            ``docs/bench/analysis/wallbounce-1003/10d/first_diff.py`` 用・既定 off=費用 0)。
        (天気と暦の規則: 世界の日付は暦・天気は再生日の行・日の出と日の入りと太陽高度と影は暦の日付=ユーザーの答え 1-3・
        ``engine.processes.environment``。〔第330・RET〕10e より前の ``legacy`` と切替口 ``weather_scheme`` は消した)
        weather_perturb: **10e(B6)天気を揺らす**(アンサンブル・既定 ``False``)。``True`` では暦の日付が窓の中でも
            実際の天気を使わず、同じ季節 × 平日/土休の層から天候型を日数の割合で引く(鍵は環境の seed)。アンサンブルは
            これを付けて ``environment_seed`` を変えて回す。
            「環境の seed を動きの seed と別の値にしたら揺らす」にしなかった理由: salt の比較(10f)は環境の seed を
            固定して動きの seed だけを変えるので、salt ごとに天気が揺れて共通の乱数(CRN)が崩れる。

    Returns:
        ``RunResult``。
    """
    _call_args = dict(locals())  # 10d: 設定の指紋(先頭で引数だけを写す)
    # 1-0 段 F: 組み立て・tick のループ・ランの終わりは engine.systems(状態の箱+系+進行役)。結果は HEAD と同じ。
    from shibuya.engine.systems.conductor import conduct

    return conduct(_call_args)


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
    ap.add_argument("--start-date", type=str, default="",
                    help="開始日 YYYY-MM-DD(A1-1・manifest の start_sim_datetime)。空=2026-07-13(月)+ --day-index 日")
    ap.add_argument("--holiday-csv", type=str, default=DEFAULT_HOLIDAY_CSV,
                    help="内閣府の祝日 CSV(cp932)。読めなければ開始日の検査で止める(既定 data/calendar/syukujitsu.csv)")
    ap.add_argument("--school-holidays", type=str, default="",
                    help="学校の長期休みの区間 YYYY-MM-DD:YYYY-MM-DD をカンマ区切り(開始日の検査・既定は空)")
    # 10d(親の答え 7): 複数日の通しランと再開の口(同じ綴りを engine.run と shibuya.cli で使う)
    ap.add_argument("--sim-days", type=int, default=1,
                    help="通しで回す日数(10d)。2 以上では各日の終わりに締め・日の頭の初期化は走らせない(既定 1)")
    ap.add_argument("--resume-from", type=str, default="",
                    help="再開する状態のファイル(10d・state-T<T>.npz)。設定は親と同じにする(違えば止める)")
    ap.add_argument("--state-out", type=str, default="",
                    help="状態の書き出し先のディレクトリ(10d)。各日の締めの後とランの最後に state-T<T>.npz を書く")
    # 10e(B6): 天気を揺らす(同じ綴りを engine.run と shibuya.cli で使う)
    ap.add_argument("--weather-perturb", action="store_true",
                    help=("天気を揺らす(10e B6・アンサンブル)。窓の中でも同じ季節 × 平日/土休の層から天候型を日数の"
                          "割合で引く(鍵は --environment-seed)。既定は付けない=その日の実際の天気"))



def calendar_kwargs_from_args(args: Any) -> dict[str, Any]:
    """``add_calendar_args``(10d の ``--sim-days``・``--resume-from``・``--state-out``・10e の ``--weather-perturb`` を含む)と
    ``--response-delay`` の結果 → ``run_day`` の引数。"""
    out: dict[str, Any] = {
        "start_sim_datetime": (getattr(args, "start_date", "") or None),
        "holiday_csv": str(getattr(args, "holiday_csv", DEFAULT_HOLIDAY_CSV)),
        "school_holidays": str(getattr(args, "school_holidays", "") or ""),
        # None=未指定(録画・mock は 1、再生はテープの記録に合わせる=``_resolve_response_delay``)
        "response_delay": getattr(args, "response_delay", None),
    }
    # 10d: 複数日と再開の口(既定のときは欄を足さない=既定の引数は今のまま)
    if int(getattr(args, "sim_days", 1) or 1) != 1:
        out["sim_days"] = int(args.sim_days)
    if getattr(args, "resume_from", ""):
        out["resume_from"] = str(args.resume_from)
    if getattr(args, "state_out", ""):
        out["state_out"] = str(args.state_out)
    # 10e(B6): 天気を揺らす(未指定のときは欄を足さない=既定の引数は今のまま)
    if getattr(args, "weather_perturb", False):
        out["weather_perturb"] = True
    return out


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
    ap.add_argument("--population-seed", type=int, default=None,
                    help="10f(K21 (a))母集団の seed(省略=--seed と同じ)。--seed は動きの seed(salt)")
    ap.add_argument("--environment-seed", type=int, default=None,
                    help="10f 環境の seed(気象・大きな催し・道路工事。省略=--seed と同じ)")
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

    _pop_seed = resolve_population_seed(args.seed, args.population_seed)  # 10f: 合成世界は母集団の側
    world = World.load_or_synthetic(Path(args.world), n_cells=args.cells, seed=_pop_seed)
    res = run_day(
        n_agents=args.agents,
        seed=args.seed,
        population_seed=args.population_seed,
        environment_seed=args.environment_seed,
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
