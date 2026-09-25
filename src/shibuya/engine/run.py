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
- 世界内日時は ``DEFAULT_START_DATETIME + day_index 日 + tick 分``(manifest の
  ``start_sim_datetime`` を run_day が受けていないため・expedient)。
- 顕著行為(B4 の「顕著行為の到達」)は C3 では**常に空**(世界過程が C4)。流れも 0。
- 会話の招待は「resolve が ``会話`` を成立させた対」を入口にする(契約書 §3 の順序
  「招待→応答判定」の応答判定を resolve の直後に置いた)。相手側の ``activity`` は
  resolve が変えないため、相手の離脱は ``cell`` 監視で検出する。
- 週の曜日は ``day_index``(既定 0=月曜)。週 7 日表は C4 の PlanSpec。
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Final, Mapping

import blake3 as _blake3
import numpy as np

import dataclasses

from shibuya.agents.population import Population, load_population, sample_population
from shibuya.agents.weekly import apply_to_mock_schedule, load_weekly
from shibuya.agents.schedule import synthesize
from shibuya.agents.state import (
    FOCUS_NONE,
    WAKE_CONDITION_CLASS,
    Activity,
    AgentState,
    WakeCondition,
)
from shibuya.core.growth import GrowthReport, check_growth
from shibuya.core.hashing import apply_key_array, blake3_hex
from shibuya.core.types import DEFAULT_TICK_SECONDS, MINUTES_PER_SIM_DAY
from shibuya.engine import commit as C
from shibuya.engine import growth_decl as GD
from shibuya.engine import resolve as R
from shibuya.engine.arbiter import Arbiter, WakeCandidates, call_budget_per_tick
from shibuya.engine.change_detect import ChangeDetector
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
from shibuya.engine.llm_bridge import (
    DEFAULT_LANE,
    LLMBridge,
    PerceptionRendererAdapter,
    StubRenderer,
    delta_think_ticks,
)
from shibuya.engine.scheduler import DIAG_COLUMNS
from shibuya.engine.tape import TapeRow, TapeWriter
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
    DEFAULT_START_DATETIME,
    SIGNAGE_P_SEE_DEFAULT,
    PerceptionAssets,
    Renderer as PerceptionRenderer,
    check_signage_p_see,
)
from shibuya.perception.templates import (
    INTENT_MODES,
    VOCAB_VERSIONS,
    check_intent_mode,
    check_vocab_version,
)
from shibuya.world.assets import (
    AREA_SOURCES,
    DEFAULT_AREA_SOURCE,
    check_area_source,
    load_process_assets_or_synthetic,
    load_walkable_area_m2,
)
from shibuya.world.state import World

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


def _default_mock(seed: int | str, vocab_version: str) -> Any:
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

    @property
    def combined(self) -> str:
        return blake3_hex(
            "\x1f".join(
                (self.agents_hash, self.world_hash, self.population_hash, self.schedule_hash)
            ).encode("utf-8")
        )


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
    #: 計画実行層の診断(``PlanExecutor.counters()``)。層が休んだランは空 dict。
    presence_counters: dict[str, float] = field(default_factory=dict)
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
    waste_band: tuple[float, float] = (0.0, 0.0)
    # ---- C6-a 実艦隊 ----
    #: ``llm.fleet.FleetConfig.manifest_fields()``(``cache_salt``・``prefix_caching_hash_algo``・
    #: ルーティング規則・in-flight 上限)。**ランが導出して押す**(親決定 09-09)。
    fleet_fields: dict[str, Any] = field(default_factory=dict)
    #: ラン終端の ``drain`` で拾った件数(=最後の tick 以降に届いた応答)。
    fleet_drained_at_end: int = 0
    #: ラン終端でも答えが返らなかった呼(**次ランへ持ち越す=破棄しない**の監査点)。
    fleet_unanswered_at_end: int = 0

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

    @property
    def waste_band_ok(self) -> bool:
        lo, hi = self.waste_band
        return bool(hi > 0.0 and lo <= self.waste_tonnes_per_day <= hi)

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
            "template_sha256": _T.template_sha256(),
            "budget_mode": self.budget_mode,
            # ---- D-99 (a) L4 呼数予算の腕(既定 1.0=宣言どおりの按分)。腕 AB8-L4-SCALE ----
            "l4_scale": float(self.l4_scale),
            "budget_per_tick": float(self.budget_per_tick),
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
            "synonym_table_version": _synonym_table_version(self.vocab_version),
            "action_usage": dict(self.action_usage),
            # ---- D-56 就寝抑止(既定 True)。False = D-56 前の挙動 ----
            "sleep_suppression": bool(self.sleep_suppression),
            # ---- D-62 就寝は計画の実行(既定 True)。False = D-62 前の挙動 ----
            "plan_sleep": bool(self.plan_sleep),
            # ---- D-66 計画実行層(既定 True・W16+W17 のあるランだけ立つ) ----
            "plan_executor": bool(self.plan_executor),
            "exit_mode": str(self.exit_mode),
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
        # C9b: 対象と注意の腕だけ 1 行(既定の 4 腕では出ない)
        if self.attention:
            lines.append(
                f"  対象と注意(C9b) 近づく {self.n_approach:,}"
                f"(到達 {self.n_approach_done:,} / 対象不在 {self.n_target_gone:,})"
                f" / 焦点 取得 {self.n_focus:,} 消失 {self.n_focus_lost:,}"
                f" / 会話 実距離成立 {self.n_talk_by_distance:,}"
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
                f"{self.waste_tonnes_per_day:.3f} t/日 (band {self.waste_band[0]:.1f}-"
                f"{self.waste_band[1]:.1f}) {'OK' if self.waste_band_ok else 'NG'}"
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


def _pending_extra(res: Any) -> tuple[int, int]:
    """応答 → ``(対象ヒント索引, 目印 POI 索引)``(C9b G5/G6・腕が立っていなければ ``(0, -1)``)。"""
    return C.target_hint_code(getattr(res, "target_hint", "")), _target_poi(
        getattr(res, "target", None)
    )


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
    budget_mode: str | BudgetMode = BudgetMode.FIXED_SLOTS,
    salient_rate_per_10k: float | None = None,
    report_precondition: bool = True,
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
        fleet_wait_s: ④′ で未応答が残っているとき**最大この秒数だけ待つ**。既定 0.0=
            純非ブロッキング。本番(予算行 W1: 1 シミュ日 ≤24 h ⇒ 1 tick ≈ 37 秒の壁時計)
            では LLM の往復(数秒)が 1 tick の壁時計に収まるので 0 でよい。**スモークや
            テストのようにエンジンが LLM より桁違いに速いラン**では、0 のままだと応答が
            全部ラン終端に届き δ_think の契約(``t_apply``=起床+δ_perc+δ_think)が
            観測できないので、ここで艦隊に歩調を合わせる(**expedient**・本番経路は変えない)。
        fleet_debug_dir: 書式の原因分析用 jsonl の置き場(``None``=off が既定)。初回パースが
            落ちた呼だけ {プロンプト・初回の生応答・再生成の生応答・実効/厳密の判定・理由} を
            1 行 1 呼で落とす。**テープ形式は変えない**(テープは最終応答 1 行のまま)。
        checkpoint_every: checkpoint 間隔[tick]。
        day_index: 曜日(0=月曜)。
        budget: 1 tick の呼数上限(None なら L4 按分)。
        l4_scale: **manifest に載せるだけ**の同定欄(PENDING D-99 (a)・腕 AB8-L4-SCALE)。
            倍率から ``budget`` を作るのは ``cli.run``(``l4_scale>0`` なら
            ``call_budget_per_tick(n_agents)×倍率``・``0`` なら ``n_agents``=無制限)。
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
            既定では**1 バイトも変わらない**(テンプレ本体・``template_sha256`` も不変)。
            ``INTENT_MODES`` 以外は ``ValueError``。
            ``renderer`` を明示注入したランでは**このフラグは効かない**(注入側が持つ)。
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
        exit_mode: 退出の実行形(設計書 §10-3)。``"immediate"`` のみ実装、
            ``"board_intent"`` / ``"walk_to_platform"`` は**切替口だけ予約**
            (``NotImplementedError``)。
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

    Returns:
        ``RunResult``。
    """
    t_start = time.perf_counter()
    budget_mode_enum = BudgetMode.parse(budget_mode)
    # ---- ablation ②③: 腕の値をここで検査する(過程を切ったランでも manifest が嘘をつかない) ----
    p_notice_d50_scale = _check_d50_scale(p_notice_d50_scale)
    # ---- D-66 計画実行層の腕: 値の検査は**層が休むランでも**する(manifest が嘘をつかない) ----
    if str(exit_mode) not in PRESENCE_EXIT_MODES:
        raise ValueError(f"exit_mode は {PRESENCE_EXIT_MODES} のどれか(いま {exit_mode!r})")
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
    # ---- AB7 自由意図の腕: 値の検査は**レンダラを作る前**にする(manifest が嘘をつかない) ----
    intent_mode = check_intent_mode(intent_mode)
    # ---- 語彙 v2 の版: 同上(mock・レンダラ・bridge の前で確定させる) ----
    vocab_version = check_vocab_version(vocab_version)
    # ---- ablation ③: **ランの実効不応期表**を 1 本組む(既定=§6 の表そのもの) ----
    refractory_table = R.refractory_ticks(refractory_scale)
    refractory_scale_norm = R.normalized_refractory_scale(refractory_scale)
    world = world if world is not None else World.synthetic(n_cells=n_cells, seed=seed)
    llm = llm if llm is not None else _default_mock(seed, vocab_version)
    salt = run_salt_for(seed)
    tape_writer = TapeWriter(Path(tape_path)) if tape_path is not None else None
    conv = ConversationManager(seed) if conversations else None
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
    )
    if ledger is not None and ledger.money is not None:
        # 世帯の現金行 = 個体 SoA の money(写しを作らない・台帳の書き込み窓は resolve が持つ)
        ledger.money.attach_household_cash(agents.registry.money)
    if pop is not None:
        schedule = _schedule_with_population(
            schedule, pop, world.n_cells, keep_outside_home=plan_exec_on
        )
    R.initialize(agents, world, schedule, day_index=day_index, ledger=ledger)
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
            day_index=day_index,
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
        )
        presence.initialize()  # その時刻に在圏でない体を域外へ(I1 の分母)
        if runner is not None:
            runner.attach_presence(presence)  # hotel の母数・civic の引き込み候補

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
        # 世界内日時 = 気象の再生実日(D-W15)。世界過程が無ければ既定の開始日 + day_index。
        start = DEFAULT_START_DATETIME + timedelta(days=int(day_index))
        if runner is not None and runner.replay_date:
            start = datetime.fromisoformat(runner.replay_date)
        perception = PerceptionRendererAdapter(
            PerceptionRenderer(
                world, agents, assets,
                clock_fn=lambda t: start + timedelta(minutes=int(t)),
                seed=seed,
                budget_mode=budget_mode_enum,
                signage_enabled=signage,
                signage_p_see=signage_p_see,
                intent_mode=intent_mode,
                vocab_version=vocab_version,
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
        b_agent, b_cond, b_tick, b_cell = weekly.boundary_events_full(day_index)
        schedule = apply_to_mock_schedule(schedule, weekly, day_index)  # 拠点セル(自宅/職場)の上書き
        # ---- D-62 (b): tick 0 の activity を W17 の 0:00 時点の活動から立てる ----
        # ``initialize`` は全員 SLEEPING(週次表の無い世界の既定)。ここで立て直す。
        if plan_sleep:
            R.set_initial_activity(agents, weekly.initial_activity(day_index))
    else:
        b_agent, b_slot, b_tick = schedule.events_of_day(day_index)
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

    result = RunResult(
        n_agents=n_agents,
        n_cells=world.n_cells,
        seed=seed,
        ticks=ticks,
        world_source=world.assets.source,
        tape_path=str(tape_path) if tape_path is not None else "",
        mode=mode,
    )
    result.money_start = int(agents.registry.money.astype(np.int64).sum())
    #: D-71 §3 J: 行動コード別の適用件数(``ResolveOutcome.per_action`` のラン合計)。
    per_action_total: dict[int, int] = {}
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
    #  **target_hint**, **target_poi**)
    # ``target_person`` = LLM が「対象」欄に書いた個体 id(-1=名指しなし・C6 09-09)。
    # ``target_hint`` = 段0 辞書 v4 の対象ヒント索引(C9b G5・0=なし)。
    # ``target_poi`` = 「対象」欄が目印 POI に解決できたときの索引(C9b G6 a′・-1=なし)。
    pending: list[tuple[int, int, int, int, str, int, int, int, int]] = []
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

    # 逐次ループ宣言1: tick 数ぶん
    for tick in range(ticks):
        R.advance_body(agents, tick)

        # ---- ⓪a 世界過程(昼夜・天候・鉄道・営業時間・混雑場・断面交通) ----
        # 流れ(B4 の「流れ方向」欄)を作るのが混雑場なので、**⓪ の前**に置く。
        # 親指示は「⓪ の直後」だったが、それだと同じ tick の流れが描画に載らない(報告済み)。
        if runner is not None:
            runner.step(tick)

        # ---- ⓪a-2 計画実行層(D-66): 到着・退出(§3)。世界過程と同じ位置で回す ----
        if presence is not None:
            t0 = time.perf_counter()
            presence.step(tick)
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
            )
            field_rows = perception.b4_field_rows

        # ---- ① 前 tick までに届いた応答を apply_key 昇順で適用(§2.4) ----
        t0 = time.perf_counter()
        llm_intents = C.IntentBatch.empty()
        n_undefined = 0
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
                        getattr(schedule, "school_cell", None) if attention_on else None
                    ),
                    target_person=tgt_person[keep],
                    target_hint=tgt_hint[keep] if attention_on else None,
                    target_poi=tgt_poi[keep] if attention_on else None,
                    stats=talk_stats, run_salt=salt,
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
        R.apply_detection(agents, world, det)
        d_agent, d_cond, d_class = det.candidates()
        phase["detect"] += time.perf_counter() - t0

        # ---- 計画境界の起床候補 ----
        lo, hi = int(b_start[tick]), int(b_start[tick + 1])
        if hi > lo:
            p_agent = b_agent[lo:hi]
            p_cond = b_cond[lo:hi]
            # ---- D-62 (a): 就寝境界は**エンジンが実行する**(LLM を呼ばない) ----
            # 非就寝の境界は逆に「起こしてから呼ぶ」(呼が繰り延べ・抑止で落ちても起きる)。
            if plan_sleep:
                to_bed = p_cond == int(WakeCondition.PLAN_SLEEPING)
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
        n_parse_errors_fleet = 0
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
                    max(res.t_apply, tick + 1), res.wake_class, res.agent_id,
                    res.condition, res.text, res.action_code, _target_person(res.target),
                    *_pending_extra(res),
                ))
                if not res.format_ok:
                    n_parse_errors_fleet += 1
                if conv is not None and res.condition == int(WakeCondition.CONVERSATION_TURN):
                    conv.utterance(
                        res.agent_id, tick, action=res.parse.action, comment=res.parse.comment
                    )
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
                    max(t_apply, tick + 1), res.wake_class, res.agent_id,
                    res.condition, res.text, res.action_code, _target_person(res.target),
                    *_pending_extra(res),
                ))
                if not res.format_ok:
                    n_parse_errors_fleet += 1
                if conv is not None and res.condition == int(WakeCondition.CONVERSATION_TURN):
                    conv.utterance(
                        res.agent_id, tick, action=res.parse.action, comment=res.parse.comment
                    )
            phase["llm"] += time.perf_counter() - t0

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

        cands = WakeCandidates(
            np.concatenate([p_agent, d_agent, c_agent, s_agent, f_agent]),
            np.concatenate([p_cond, d_cond.astype(np.int8), c_cond, s_cond, f_cond]),
            np.concatenate([p_class, d_class, c_class, s_class, f_class]),
            np.concatenate(
                [
                    np.full(
                        p_agent.size + d_agent.size + c_agent.size + s_agent.size,
                        tick, dtype=np.int64,
                    ),
                    f_since,  # 再投入は**元の待ち始め**を保つ(昇格が巻き戻らない)
                ]
            ),
            np.concatenate(
                [
                    np.ones(p_agent.size, dtype=bool),    # 計画境界(眠りから覚める境界を含む)
                    np.zeros(d_agent.size, dtype=bool),   # 変化検出(内受容・セル変化)
                    np.ones(c_agent.size, dtype=bool),    # 会話ターン
                    np.ones(s_agent.size, dtype=bool),    # 顕著行為
                    f_exempt,                             # 艦隊の再投入
                ]
            ),
        )

        # ---- ③ 繰り延べアービタ(§6)+ 就寝抑止(D-56) ----
        t0 = time.perf_counter()
        asleep_now = np.asarray(agents.registry.activity) == int(Activity.SLEEPING)
        # ---- 起床率/時 の計測(D-62 の検証欄・a(h) との照合用) ----
        # 測る場所は**アービタの直前**(この tick の候補を絞る時点の「起きている割合」)。
        _h = (tick // 60) % 24
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
                        conv.utterance(a, tick, action=res.parse.action, comment=res.parse.comment)
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
                        )
                    )
                # 発射は**非ブロッキング**。返るのは「キューに入らなかった」分だけ。
                for d in fleet_bridge.submit(calls, now_tick=tick):
                    fleet_deferred.append(
                        (int(d.call.agent_id), int(d.call.condition),
                         int(d.call.wake_class), int(d.call.wake_since))
                    )
            result.llm_calls += len(sel)  # L4 の呼数=**発射数**(再送も 1 呼・親決定 09-09)
            result.calls_by_hour[(tick // 60) % 24] += len(sel)  # D-56 の検証欄
        # 艦隊経路の書式エラーは ④′(到着時)で数える=選抜が 0 の tick でも計上する
        n_parse_errors += n_parse_errors_fleet
        peak_pending = max(peak_pending, len(pending))
        peak_backlog = max(peak_backlog, arbiter.n_pending())
        phase["llm"] += time.perf_counter() - t0

        # ---- ⑤ Phase A(エンジン継続との合流) ----
        t0 = time.perf_counter()
        intents = C.IntentBatch.concat(
            [llm_intents, C.engine_continuations(agents, space, tick)]
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
            vocab_version=vocab_version,
            geometry=geom,
            focus_request=focus_request,
            talk_by_distance=attention_on,
        )
        phase["phase_c"] += time.perf_counter() - t0
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
        result.meal_yen += outcome.meal_yen
        # C9b(対象と注意)。腕が立っていないランでは 4 本とも 0 のまま。
        result.n_approach += outcome.n_approach
        result.n_approach_done += outcome.n_approach_done
        result.n_target_gone += outcome.n_target_gone
        result.n_focus += outcome.n_focus
        result.n_focus_lost += outcome.n_focus_lost
        result.n_talk_by_distance += outcome.n_talk_by_distance
        result.n_report_ok += outcome.n_report_ok
        result.n_report_no_event += outcome.n_report_no_event
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
                    # **相互指名**= 相手も自分の呼で**こちらを名指しして** 会話 と答えた。
                    # (エンジンが解決した対象ではなく LLM が書いた対象で見る=中-2)
                    mutual = b_code == C.ACT_TALK and b_named == inviter
                    if mutual and conv.invite_blocked_by_refractory(inviter, invitee, tick):
                        conv.n_invite_refractory_blocked += 1  # 軽-5: 相互指名も不応期の対象
                        _revert(inviter)
                        continue
                    if mutual:
                        # その場で成立。相手の意思は相手自身の呼に出ているので抽選は引かない。
                        conv.n_invites += 1
                        conv.stamp_invite_refractory(inviter, invitee, tick)
                        opened = conv.invite(
                            inviter, invitee, tick, int(cell_now[inviter]),
                            same_cell=same_cell, partner_idle=True, answered=True,
                        )
                        if opened is None:
                            _revert(inviter)  # 内訳は ``conv.invite`` が数える
                        else:
                            conv.n_accepted += 1
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
                            same_cell=same_cell,
                        ):
                            _revert(inviter)

            # ---- ③ 期限切れの返事待ち(「無視された」=呼を消費しない) ----
            for stale in conv.expire_pending(tick):
                _revert(stale)
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
        if checkpoint_every and ((tick + 1) % checkpoint_every == 0 or tick == ticks - 1):
            t0 = time.perf_counter()
            result.checkpoints.append(
                Checkpoint(
                    tick, agents.state_hash(), world.state_hash(),
                    schedule.population_hash,
                    schedule_hash,
                )
            )
            phase["checkpoint"] += time.perf_counter() - t0

    # ---- 艦隊の残りを吸い切る(**捨てない**)。テープを閉じる前に置く ----
    if fleet_bridge is not None:
        n_late = 0
        # ``now_tick=ticks``= ラン終端(最後の tick の 1 つ先)。再生側はこの値の項目を
        # 「tick ループ中には届かなかった」として同じ位置で処理する(D-58)。
        for res in fleet_bridge.drain(now_tick=ticks):
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
        runner.end_of_day(max(0, ticks - 1))
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
        band = runner.waste_band_report()
        if band is not None:
            result.waste_band = (float(band.low), float(band.high))
    ledger_growth: tuple[dict[str, Any], dict[str, int]] = ({}, {})
    if ledger is not None:
        # 日次の畳み込み(D-R2-6: 生ログは保持窓・取引行列は日次集約行へ)。
        # **締めを捨てない**——締めると取引行列も当日の廃棄も 0 に戻るので、締めたあとに
        # 現在値でセンサスを回すと faucet/sink/廃棄が全部 0 の空虚な行になり、ゲートが
        # 素通りする(層2レビュー指摘)。``daily_census`` は ``day_index`` の締めを読む。
        closes = ledger.end_of_day(day_index)
        result.day_closed = int(closes.day)
        ledger_growth = ledger.growth_parts()
        # 日次(軽量)センサス+ゲート(境界・経済設計書 §2.4)。
        # engine は economy を import できない(層契約)ので、行の作り手は
        # ``LedgerBundle.census``(economy 側が注入する呼び出し可能)。**失敗しても raise しない**
        # =診断の赤(§2.4「ゲート失敗=較正・holdout 照合に使わない」)。
        row = ledger.daily_census(day_index)
        if row is not None:
            result.census_row = dict(row)
            result.census_pass = bool(row.get("gate_ok", False))
        # 月次センサスの T3(冗長方程式の検算・D-85 (a)・ユーザー決定 2026-09-17)。
        # 月次が立たない日は None(=未実行)。**``census_out`` とは無関係に**毎日呼ぶ
        # ——書き出しの有無で manifest が動くと「観測が世界を変えない」が崩れるため。
        t3 = ledger.monthly_t3(day_index)
        if t3 is not None:
            result.t3_report = dict(t3)
            result.t3_ok = bool(t3.get("ok", False))
        # 日次センサス/月次 MER の出力口(§2.4)。**``census_out`` を渡したときだけ**書く。
        # 書き手は economy 側の注入(engine は economy を import できない=層契約)。
        if census_out is not None:
            result.census_paths = ledger.write_census(day_index, str(census_out))
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
    result.intent_mode = str(
        getattr(getattr(perception, "renderer", None), "intent_mode", intent_mode)
        if perception is not None
        else intent_mode
    )
    # 語彙 v2: 実際に使った版(注入レンダラでも**エンジン側の版**が正=行動の解決はこちら)。
    result.vocab_version = str(vocab_version)
    result.action_usage = _action_usage(per_action_total, vocab_version)
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
    if presence is not None:
        result.presence_counters = dict(presence.counters())
        result.presence_summary = presence.summary()
        # 標本の無かった時(短いラン)は NaN のまま来るので 0.0 に落とす(推測で埋めない)
        result.wake_rate_in_area_by_hour = [
            (0.0 if v != v else round(float(v), 6)) for v in presence.wake_in_area_by_hour
        ]
    result.diagnostics = np.asarray(diag_rows, dtype=np.int64).reshape(-1, len(DIAG_RUN_COLUMNS))
    result.phase_seconds = phase
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
    result.growth_measured = measured
    result.growth_report = check_growth(
        declarations,
        measured,
        steps=ticks,
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
                    help="④′ で未応答が残るとき tick ごとに最大この秒数だけ艦隊を待つ(既定 0=純非ブロッキング・スモーク用)")
    ap.add_argument("--fleet-queue-capacity", type=int, default=0,
                    help=("艦隊の受理待ち+実行中の合計上限(既定 0=FleetConfig の既定 max_in_flight×4)。"
                          "C7 本番(D-55/D-58): 計画呼数 2,709/tick に対し既定 1,792 だと 33.8%% が queue full で"
                          "繰り延べ→テープに残らず再生不能。計画呼数以上(例 4096)にすると繰り延べ ≈0"))


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
        attendance_rate=float(args.attendance_rate),
        derive_rule=str(args.derive_rule),
        outside_suppression=not args.no_outside_suppression,
        geometry=str(args.geometry),
        area_source=str(args.area_source),
    )
    print(res.summary())
    return 0 if (res.conserved and res.min_stock >= 0) else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
