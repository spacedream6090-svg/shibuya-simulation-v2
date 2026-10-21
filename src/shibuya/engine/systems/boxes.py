"""engine.systems.boxes — ``run_day`` の状態の箱(第 1 期 1-0・草案 §2-3)。

``run_day`` の局所の名前(HEAD ``ee3abc7`` で 450 個)を、次の箱のどれかか「系の中だけの一時」に割り当てる(割り当ての表は
``docs/bench/analysis/wallbounce-1012/run-day-decomp/local-assignment.json``・漏れ 0 が段 C の門)。

| 箱 | 中身 | 状態台帳 |
|---|---|---|
| ``RunConfig``(凍結) | 検査済みの腕と値・tpd・``total_ticks``・t_begin/t_end・設定の指紋 | 対象外(設定) |
| ``SoAState`` | agents・world | SoA |
| ``Layers`` | 台帳の持ち主(名は ``hash_owners`` の鍵と同じ・``undefined``・``run_day`` は導く) | 外の状態 |
| ``LlmIo`` | pending・fleet_deferred・fleet_waiting・fleet_inflight・replay_inbox | O43・O44・O96(持ち主の名 ``run_day``) |
| ``DayTables`` | 計画境界の表 b_*・w17_substituted | 対象外(資産と暦から作り直せる) |
| ``Buffers`` | 使い回すバッファ ``focus_request``(刻みの頭で空にしない=R1) | 対象外 |
| ``TickScratch`` | 刻みの中の受け渡し(刻みの頭で空にする・試験では番兵) | 対象外 |
| ``RunStats`` | 診断の積算・``RunResult``・記録 | 対象外(診断) |
| ``Fixtures``(草案に足した) | 組み立てで作り、ランの間は読むだけの物(暦・日課・週次表・資源の空間・幾何・描画の口・艦隊) | 対象外 |

〔草案と違えた点〕(1) ``Fixtures`` を足した: 草案の 8 箱に入らない「組み立てで作り読むだけの物」(``calendar``・
``schedule``・``weekly``・``space``・``geom``・``perception`` ほか)の置き場。(2) ``prev_sessions``・``prev_tape_misses`` は
``LlmIo`` でなく ``RunStats`` に置いた(どちらも診断の行の差分の基準)。

物の同一性(草案 §2-1 の 6): 箱は組み立ての物をそのまま指す(写しを作らない)。

逐次ループ宣言: ``TickScratch.reset`` は欄の数ぶん(36=1-0 の 34+第 1 期 1-2 の ``percepts``+第 2 期 2-2 の ``near_index``・
刻みに 1 回)。
"""

from __future__ import annotations

from dataclasses import dataclass, field, fields
from typing import Any

from shibuya.core.time_consts import NS_PER_SECOND, STEP_SECONDS

__all__ = [
    "RunConfig", "SoAState", "Layers", "LlmIo", "DayTables", "Buffers", "TickScratch", "TickScratchStrict",
    "RunStats", "Fixtures", "Box", "TickCtx", "SCRATCH_FIELDS", "UNSET", "OWNER_NAMES",
]

#: 状態台帳の外の状態の持ち主の名(``hash_owners`` の鍵・HEAD の ``_hash_owners`` と同じ順)。
#: 〔第 1 期 1-3〕末尾に ``events``(出来事の記録=状態台帳の行 ``E``・軸 1 diag・軸 2 discardable)を足した。既存の 21 個の
#: 名と順は変えない。2 つのハッシュは軸で選んだ行の道筋だけを読む(``full_items``・``behavior_items``)ので、持ち主を
#: 足してもハッシュの値は変わらない。〔第 1 期 1-8 J0〕末尾に ``decision``(候補の口の層=状態台帳の行 ``J0``・腕 port の
#: ランだけ・既定 None)を足した(同じ理由で値は変わらない)。〔第 1 期 1-8b〕末尾に ``speech``(発話の口=状態台帳の腕の行
#: ``S8``・``S8M``・腕 on のランだけ・既定 None)を足した(腕の行は持ち主が None のランではハッシュに入らない=値は変わらない)。
#: 〔第 3 期 3-3〕末尾(2-2 の ``proximity`` の後)に ``experiment``(申込書の持ち主=状態台帳の行 ``X``・軸 1 diag・軸 2 discardable・申込書を渡したランだけ・
#: 既定 None)を足した(どちらのハッシュにも状態のファイルにも入らない=値は変わらない)。
#: 〔第 3 期 3-2〕末尾(3-3 の ``experiment`` の後)に ``batching``(計算のまとめの窓=状態台帳の行 ``BW``・軸 1 diag・
#: 軸 2 discardable・進行役が窓のループの前に置く)を足した(どちらのハッシュにも状態のファイルにも入らない=値は変わらない)。
#: 〔第 3 期 3-5〕末尾(3-2 の ``batching`` の後)に ``body``(本人の体の層=状態台帳の行 ``BD``・軸 1 diag・軸 2 discardable)を足した
#: (同じ理由で値は変わらない)。
OWNER_NAMES: tuple[str, ...] = (
    "act_layer", "intent_layer", "fam_layer", "mem_layer", "poi_resolver", "wom", "rel_layer", "classical",
    "energy", "norm_meter", "presence", "conv", "arbiter", "detector", "runner", "ledger", "undefined",
    "renderer", "bridge", "fleet_bridge", "run_day", "events", "decision", "speech", "proximity", "experiment",
    "batching",
    "body",
    "calendar_shadow",  # 〔第 3 期 3-1〕暦 1a の影(状態台帳の行 CAL・腕 1a のランだけ・中身は hash_skip=値は変わらない)
    "calendar_self",  # 〔第 6 期 6-2〕カレンダー 1b(状態台帳の腕の行 C1B・C1BM・腕 1b のランだけ=既定は None で値は変わらない)
    # 〔第 6 期 6-3〕時計の段 T2〜T4 の腕の持ち主(状態台帳の腕の行 TCR・TCC・T3M・T4W=軸 1 diag・軸 2 discardable・腕のランだけ)
    "talk_clock", "step_scope", "clock",
    "contact",  # 〔第 6 期 6-4 C1〕連絡の道具(状態台帳の腕の行 CT1*・腕 c1 のランだけ=既定は None=値は変わらない)
    "calendar2",  # 〔第 6 期 6-2 カレンダー 2〕会話から生まれる予定(状態台帳の腕の行 CA2*・腕 arm のランだけ=既定は None)
)


@dataclass(frozen=True)
class TickCtx:
    """系が受け取る時刻。ランの単位の系は ``T=None``(ほかの欄も ``None``)。

    - ``T``=通しの刻みの番号・``td``=日の中の刻みの番号・``day``=日番号(1-0 のまま。値も意味も変えない)。
    - 〔第 1 期 1-1 T0・TM7〕``t_ns``=通しの時刻のナノ秒(``core.types.SimTime``・``t_sim_ns(T)`` と同じ値)=
      ``T × 刻みの幅[秒] × 1e9``。``tod_s``=その日の中の秒=``td × 刻みの幅[秒]``。幅はランの設定(``RunConfig`` の
      ``tick_seconds``)から進行役が渡す。T0 では系はまだ読まない(足しただけ=結果不変)。
    - 名の ``TickCtx`` は 1-0 の箱の名のまま(識別子の置き換えは段階的=``tests/engine/time/tick_word_allow.json``)。
    """

    T: int | None
    td: int | None = None
    day: int | None = None
    t_ns: int | None = None
    tod_s: int | None = None

    @staticmethod
    def of(T: int, tpd: int, step_seconds: int = STEP_SECONDS) -> "TickCtx":
        """通しの刻みの番号 ``T``・1 日の刻みの数 ``tpd``・刻みの幅 ``step_seconds``[秒] → 時刻(整数だけ)。"""
        t, n, w = int(T), int(tpd), int(step_seconds)
        td = t % n
        return TickCtx(T=t, td=td, day=t // n, t_ns=t * w * NS_PER_SECOND, tod_s=td * w)


@dataclass(frozen=True)
class RunConfig:
    """検査済みの腕と値(組み立ての S0〜S1 の結果)と、ランの範囲(凍結)。"""

    # ---- 引数(検査と正規化の後の値) ----
    n_agents: int
    seed: Any
    tick_seconds: int
    ticks: int
    fleet_wait_s: float
    checkpoint_every: int
    day_index: int
    l4_scale: float
    mode: str
    lane: str
    census_out: Any
    attendance_rate: float
    exit_mode: str
    derive_rule: str
    checkpoint_detail: bool
    classical_habit_p: float
    classical_tau: float
    familiarity_k: int
    intent_max_ticks: int
    memory_n: int
    move_search_radius: int
    occupancy_every: int
    occupancy_path: Any
    outside_suppression: bool
    p_notice_ablation: Any
    p_notice_d50_scale: float
    plan_sleep: bool
    queue_service: bool
    report_precondition: bool
    response_delay: int
    run_id: str
    seat_area_eatery_m2: Any
    seat_area_retail_m2: Any
    signage: bool
    signage_p_see: float
    sim_days: int
    sleep_suppression: bool
    state_out: Any
    store_recall_scope: str
    vocab_version: str
    activity_region: str
    area_source: str
    chooser: str
    eatery: str
    energy_rate: str
    geometry: str
    home_meal: str
    hunger_model: str
    hunger_words: str
    intent_mode: str
    meal_sleep_defer: str
    mock_move_target_p: float
    mock_out_of_cell_target_p: float
    policy: str
    role_words: Any
    # ---- 組み立てで決めた値 ----
    pop_seed: Any
    env_seed: Any
    tpd: int
    total_ticks: int
    t_begin: int
    t_end: int
    activity_on: bool
    energy_on: bool
    familiarity_on: bool
    memory_on: bool
    store_memory_on: bool
    store_signage_on: bool
    store_wom_on: bool
    plan_exec_on: bool
    attention_on: bool
    v3_hints: bool
    salt: bytes
    refractory_table: Any
    refractory_scale_norm: Any
    budget_mode_enum: Any
    #: 〔第 1 期 1-2〕看板の注視の活動の乗数は消した=表は None・恒等は True(1-0 の割り当ての欄として残す)
    p_see_activity_table: Any
    p_see_activity_identity: bool
    call_layer: int
    fp: Any
    parent_run: Any
    #: 〔第 2 期 2-4 V3〕在席の印を歩き出しで解く腕(``engine.seat_release``・組み立てで 1 回読む=``walk`` 既定・``legacy`` 切替口)。
    seat_release: str = "legacy"

    @property
    def stopped(self) -> bool:
        """``stop_at_tick`` で止めたラン(残りは再開のランが回す)。HEAD の ``_stopped``。"""
        return self.t_end < self.total_ticks


@dataclass
class SoAState:
    agents: Any
    world: Any


@dataclass
class Layers:
    """状態台帳の外の状態の持ち主(名は ``hash_owners`` の鍵と同じ)。``undefined``・``run_day`` は導く。"""

    act_layer: Any
    intent_layer: Any
    fam_layer: Any
    mem_layer: Any
    poi_resolver: Any
    wom: Any
    rel_layer: Any
    classical: Any
    energy: Any
    norm_meter: Any
    presence: Any
    conv: Any
    arbiter: Any
    detector: Any
    runner: Any
    ledger: Any
    renderer: Any
    bridge: Any
    fleet_bridge: Any
    #: 〔第 1 期 1-3〕出来事の記録(``engine.events.log.EventLog``・状態台帳の行 ``E``)。組み立てが置く。
    events: Any = None
    #: 〔第 1 期 1-8 J0〕候補の口の層(``engine.decision.layer.DecisionLayer``・状態台帳の行 ``J0``)。腕
    #: ``--decision-port port`` のランだけ組み立てが置く(既定 None=今の道)。
    decision: Any = None
    #: 〔第 1 期 1-8b〕発話の口(``engine.speech.port.SpeechPort``・状態台帳の行 ``S8``・``S8M``)。腕 ``--speech-port on`` の
    #: ランだけ組み立てが置く(既定 None=今の道)。
    speech: Any = None
    #: 〔第 2 期 2-2 段 11a〕近接の層(``engine.proximity.ProximityLayer``・状態台帳の行 ``PX``)。腕
    #: ``--proximity distance`` のランだけ組み立てが置く(〔2-4 V2〕既定。切替口 cell は None=同じセル)。
    proximity: Any = None
    #: 〔第 3 期 3-3〕申込書の持ち主(``engine.experiment.layer.ExperimentLayer``・状態台帳の行 ``X``)。申込書を渡したランだけ
    #: 組み立てが置く(既定 None=系 ``experiment`` が立たない=今の道)。
    experiment: Any = None
    #: 〔第 3 期 3-2〕計算のまとめの窓(``engine.batching.WindowQueue``・状態台帳の行 ``BW``)。進行役が窓のループの前に置く
    #: (組み立ての間は None)。
    batching: Any = None
    #: 〔第 3 期 3-5〕本人の体の層(``engine.body.BodyModel``・状態台帳の行 ``BD``)。組み立てがどの腕でも置く(腕 sweep でも
    #: 段の境目の計器と manifest の ``body`` のため)。None=体の層の無い呼び方(全員を見る版の同じ値)。
    body: Any = None
    #: 〔第 3 期 3-1〕暦 1a の影(``engine.calendar_shadow.CalendarShadow``・状態台帳の行 ``CAL``)。腕 ``--calendar-shadow 1a``
    #: で母集団のあるランだけ組み立てが置く(既定 None=今の道・影は計器だけ)。
    calendar_shadow: Any = None
    #: 〔第 6 期 6-2〕カレンダー 1b 出入りを本人へ(``engine.calendar_self.CalendarSelf``・状態台帳の腕の行 ``C1B``・``C1BM``)。
    #: 腕 ``--calendar 1b`` で母集団と計画実行層のあるランだけ組み立てが置く(既定 None=今の道)。
    calendar_self: Any = None
    #: 〔第 6 期 6-3 T2〕会話の時計(``engine.speech_clock.TalkClock``・状態台帳の腕の行 ``TCR``・``TCC``)。腕 ``--talk-clock mora``
    #: のランだけ組み立てが置く(既定 None=今の 1 ターンの長さの表)。
    talk_clock: Any = None
    #: 〔第 6 期 6-3 T3〕何かあった体の印(``engine.step_scope.StepScope``・状態台帳の腕の行 ``T3M``)。腕 ``--step-scope changed``
    #: のランだけ組み立てが置く(既定 None=全員を毎回見る版)。
    step_scope: Any = None
    #: 〔第 6 期 6-3 T4〕場所ごとの時計(``engine.regional_clock.RegionalClock``・状態台帳の腕の行 ``T4W``)。腕 ``--clock regional``
    #: のランだけ進行役が窓のループの前に置く(既定 None=全体で 1 つの時計)。
    clock: Any = None
    #: 〔第 6 期 6-4 C1〕連絡の道具の持ち主(``engine.contact.layer.ContactLayer``・状態台帳の腕の行 ``CT1*``)。腕 ``--contact c1``
    #: のランだけ組み立てが置く(既定 None=系 ``contact`` が立たない=今の道)。
    contact: Any = None
    #: 〔第 6 期 6-2 カレンダー 2〕会話とメッセージから生まれる予定の持ち主(``engine.calendar2.layer.Calendar2Layer``・状態台帳の
    #: 腕の行 ``CA2*``)。腕 ``--calendar-2 arm`` のランだけ組み立てが置く(既定 None=系 ``calendar_2`` が立たない=今の道)。
    calendar2: Any = None

    @property
    def undefined(self) -> Any:
        return self.bridge.undefined


@dataclass
class LlmIo:
    """LLM の往復の状態(状態台帳 O43・O44・O96・持ち主の名 ``run_day``)。``pending`` は束縛し直す(①)。"""

    pending: list
    fleet_deferred: list
    fleet_waiting: set
    fleet_inflight: dict
    replay_inbox: dict


@dataclass
class DayTables:
    """計画境界の表(日の頭で張り直す・HEAD の ``_relay_tables`` の nonlocal 5 つ)と W17 の曜日の代用の記録。"""

    b_agent: Any
    b_cond: Any
    b_tick: Any
    b_cell: Any
    b_start: Any
    w17_substituted: list


@dataclass
class Buffers:
    """使い回すバッファ(物は 1 回だけ作る・刻みの頭で空にしない=草案 R1)。

    段 C(段 FIX・検収 L5・草案 §2-6 の C): 書きの検査が入っているとき、いまの系の ``writes.buffers`` に無い欄の差し替え
    (``b.buffers.focus_request = …``)を落とす。中身のその場の書き(``focus_request[:] = …``)は見ない=段 B(試験)が見る。
    """

    focus_request: Any

    def __setattr__(self, name: str, value: Any) -> None:
        from shibuya.engine.systems import guard as _G

        p = _G.BUFFERS_PERMIT
        if p is not None and name not in p:
            raise AttributeError(f"系 {_G.CURRENT} は buffers.{name} を書く宣言を持たない(段 C)")
        object.__setattr__(self, name, value)


#: 刻みの中の受け渡しの欄(書き手の系 → 読み手の系)。名は HEAD の ``run_day`` の局所の名と同じ。
SCRATCH_FIELDS: tuple[str, ...] = (
    "field_rows",            # perceive_prepare → detect
    "n_parse_errors_fleet",  # llm_receive → decide
    "llm_intents",           # apply_responses → phase_a
    "n_undefined",           # apply_responses → observe
    "applied_activity",      # apply_responses → activity_intent
    "applied_now",           # apply_responses → conversation
    # 〔名の衝突〕HEAD の d_agent ほか・n_parse_errors は外の状態の行の属性の名(O30 ``energy.out_of_area.d_agent``・
    # O86 ``bridge.n_parse_errors``)と同じなので欄の名を変えた(系の中の局所の名は HEAD のまま)
    "det_agent", "det_cond", "det_class",   # detect → wake_filter・wake_assemble(HEAD の d_*)
    "e_agent", "e_cond", "e_class",   # detect → wake_filter・relations_wake・wake_assemble
    "p_agent", "p_cond", "p_class",   # plan_boundary → wake_filter・wake_assemble
    "c_agent", "c_cond", "c_class",   # wake_sources → wake_assemble
    "s_agent", "s_cond", "s_class",   # wake_sources → wake_assemble
    "f_agent", "f_cond", "f_class", "f_since", "f_exempt",  # wake_filter → wake_assemble
    "cands",                 # wake_assemble → arbiter・observe
    "outside_now",           # arbiter → decide
    "decision",              # arbiter → decide・observe
    "parse_errors",          # decide → observe(HEAD の n_parse_errors)
    "intents",               # phase_a → phase_b・observe
    "plan",                  # phase_b → phase_c・conversation・memory・observe
    "outcome",               # phase_c → conversation・memory・familiarity・observe
    "exposures",             # memory → familiarity(HEAD の ``_exp``)
    # 〔第 1 期 1-2〕知覚の事実 ``perception.facts.Percept``(体 → その刻みに描いた Percept・HEAD の局所ではない)。decide が書く
    # =判断の入力の形(1-8 の DecisionPort.choose(ctx, …))。状態台帳の行 P(軸 1 no・軸 2 discardable)。刻みの頭で空になる
    "percepts",              # decide → (1-8 の判断の口)
    # 〔第 2 期 2-2 段 11a〕近傍の索引 ``engine.proximity.SpatialIndex``(腕 --proximity distance の刻みだけ・既定 None)。
    # perceive_prepare が書く(B5 の近接行は描画の前計算に渡す)。状態台帳の行 PX0(軸 1 no・軸 2 discardable)
    "near_index",            # perceive_prepare → (描画の前計算)
)


class _Unset:
    """番兵(試験のとき刻みの頭で scratch をこれで埋める=T4)。"""

    __slots__ = ()

    def __repr__(self) -> str:
        return "<UNSET>"


UNSET = _Unset()


class TickScratch:
    """刻みの中の受け渡し(刻みの頭で空にする)。

    段 C(実行時): 書きの検査が入っているとき(``guard.scratch_permit`` が置かれているとき)、いまの系の
    ``writes.scratch`` に無い欄への代入を落とす。
    """

    __slots__ = SCRATCH_FIELDS

    def __init__(self) -> None:
        for f in SCRATCH_FIELDS:
            object.__setattr__(self, f, None)

    def reset(self, value: Any = None) -> None:
        for f in SCRATCH_FIELDS:
            object.__setattr__(self, f, value)

    def __setattr__(self, name: str, value: Any) -> None:
        from shibuya.engine.systems import guard as _G

        p = _G.SCRATCH_PERMIT
        if p is not None and name not in p:
            raise AttributeError(f"系 {_G.CURRENT} は scratch.{name} を書く宣言を持たない(段 C)")
        object.__setattr__(self, name, value)

    def as_dict(self) -> dict[str, Any]:
        return {f: getattr(self, f) for f in SCRATCH_FIELDS}


class TickScratchStrict(TickScratch):
    """試験の番兵つき(T4): 刻みの頭で ``UNSET`` を置き、その刻みに書かれる前に読むと落ちる。"""

    __slots__ = ()

    def __getattribute__(self, name: str) -> Any:
        v = object.__getattribute__(self, name)
        if v is UNSET:
            raise AttributeError(f"scratch.{name} をこの tick に書かれる前に読んだ(T4: 前の tick の古い束縛を読む所)")
        return v

    def as_dict(self) -> dict[str, Any]:
        return {f: object.__getattribute__(self, f) for f in SCRATCH_FIELDS}


@dataclass
class RunStats:
    """診断の積算・ランの結果・記録(試験のときだけ指紋に入れる=草案 §2-7)。"""

    result: Any
    phase: dict
    diag_rows: list
    layer_counts: Any
    leave_counts: dict
    #: HEAD の局所 ``sleep_counts``(名の衝突=計画実行層の ``presence.sleep_counts`` と同じ名を避けた)
    sleep_tally: dict
    awake_sum: list
    awake_ticks: list
    calls_by_cond: Any
    per_action_total: dict
    talk_stats: dict
    intero_cross: Any
    occ_ticks: list
    occ_counts: list
    occ_kind: list
    occ_transit: list
    daily_records: list
    day_heads: list
    state_files: list
    frozen_sources_map: dict
    leave_closed: int = 0
    geometry_hops: int = 0
    geometry_jammed: int = 0
    n_fleet_reinjected: int = 0
    n_fleet_resent: int = 0
    n_outside_calls: int = 0
    n_undefined_total: int = 0
    peak_backlog: int = 0
    peak_intents: int = 0
    peak_pending: int = 0
    prev_sessions: int = 0
    prev_tape_misses: int = 0
    t_start: float = 0.0
    read_seconds: float = 0.0
    restore_seconds: float = 0.0
    #: 系ごとの壁時計(進行役の計時。``phase`` の鍵の集合は変えない=草案 §3-3 の 22)。
    system_seconds: dict = field(default_factory=dict)
    #: 最後の日の台帳の締めの成長の宣言と実測(close_final → report)。HEAD の局所 ``ledger_growth``。
    ledger_growth: Any = None


@dataclass
class Fixtures:
    """組み立てで作り、ランの間は読むだけの物。"""

    calendar: Any
    schedule: Any
    schedule_hash: str
    weekly: Any
    space: Any
    geom: Any
    perception: Any
    renderer_obj: Any
    walkable: Any
    env_fields: Any
    start_check: Any
    fleet: Any
    #: 〔第 1 期 1-7〕道具の一式(``engine.tools.record.ToolsFixture``=道具の台帳・グループの一覧・店の番号の表・看板の口)。
    tools: Any = None
    #: 〔第 2 期 2-1〕ATM の表(``engine.economy_stage2.AtmTable``・腕 ``--economy-stage2 on`` のランだけ・既定 ``None``)。
    atms: Any = None
    #: 〔第 3 期 3-3〕申込書(``engine.experiment.form.ExperimentForm``・凍結)。申込書を渡したランだけ(既定 None)。
    experiment: Any = None


@dataclass
class Box:
    """状態の箱の全部(系は ``(ctx, box)`` を受け取る)。"""

    cfg: RunConfig
    soa: SoAState
    layers: Layers
    llm: LlmIo
    day: DayTables
    buffers: Buffers
    scratch: TickScratch
    #: 〔草案と違えた点〕名は ``stats`` でなく ``runstats``(``stats`` は層の診断の属性=外の状態の行 O6 ほかと同じ名で、
    #: 状態台帳の外の軸 1 の AST の名の衝突になる)
    runstats: RunStats
    fx: Fixtures

    def tally_view(self) -> dict[str, Any]:
        """指紋の材料(HEAD の局所の名 → 値。``RunStats.sleep_tally`` は HEAD の名 ``sleep_counts``)。"""
        rs = self.runstats
        out = {f.name: getattr(rs, f.name) for f in fields(rs)}
        out["sleep_counts"] = out.pop("sleep_tally")
        return out
