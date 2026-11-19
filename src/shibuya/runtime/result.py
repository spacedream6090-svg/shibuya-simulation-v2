"""runtime.result — 割る段で ``engine/run.py`` を割った割り先(全ファイルの表 §4・名の表は
``tools/pkgmove/map.toml`` の割る行)。

中身は元のファイルの頂上の文を、元の順と元の字面のまま写した(1 バイト不変の整理)。決定の記録・逐次ループの宣言・時間の
方針は、主な割り先 ``runtime/run.py`` に残した元の docstring を読むこと。
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field
from typing import Any, Final, Mapping
import numpy as np
from shibuya.foundation.growth import GrowthReport
from shibuya.foundation.rng import RNG_SCHEME
from shibuya.foundation.types import DEFAULT_TICK_SECONDS
from shibuya.act import apply as R
from shibuya.act.intent import INTENT_MAX_TICKS
from shibuya.mind.memory.familiarity import FAMILIARITY_K
from shibuya.mind.memory.memory import MEMORY_N
from shibuya.world.body.energy import DEFAULT_HOME_MEAL, DEFAULT_HUNGER_MODEL, DEFAULT_MEAL_SLEEP_DEFER
from shibuya.runtime.arbiter import L4_LINE_PER_AGENT_DAY
from shibuya.mind.judge.chooser import DEFAULT_CHOOSER
from shibuya.mind.judge.classical import DEFAULT_POLICY
from shibuya.world.model.geometry import DEFAULT_GEOMETRY, DESIRED_SPEED_MAX_MS, DESIRED_SPEED_MIN_MS
from shibuya.act.target import MOVE_SEARCH_RADIUS_CELLS
from shibuya.foundation.queues.scheduler import DIAG_COLUMNS
from shibuya.runtime.state.hashes import FINAL_DEFINITION
from shibuya.foundation.text.channels import BudgetMode
from shibuya.foundation.ports.percept import percept_manifest as _percept_manifest
from shibuya.mind.judge.decision import layer as _DECISION
from shibuya.society.speech import layer as _SPEECH
from shibuya.world.model import proximity as _PROX
from shibuya.world.model.space import nav1 as _NAV1
from shibuya.society import calendar_shadow as _CALENDAR_SHADOW
from shibuya.interim_bundles import calendar_self as _CALENDAR_SELF
from shibuya.experiments.port import layer as _EXPERIMENT
from shibuya.foundation.queues import batching as _BATCHING
from shibuya.runtime.clocks import regional as _REGIONAL_CLOCK  # 〔第 6 期 6-3 T4〕
from shibuya.runtime.clocks import speech as _SPEECH_CLOCK  # 〔第 6 期 6-3 T2〕
from shibuya.runtime.clocks import step_scope as _STEP_SCOPE  # 〔第 6 期 6-3 T3〕
from shibuya.world.body import model as _BODY_MODEL
from shibuya.perception.renderer import SIGNAGE_P_SEE_DEFAULT
from shibuya.foundation.text.templates import INTENT_MODES, check_vocab_version
from shibuya.world.model.assets import DEFAULT_AREA_SOURCE
from shibuya.foundation.time_consts import CLOCK_KIND, HOURS_PER_DAY, SECONDS_PER_DAY

__all__ = [
    "DIAG_RUN_COLUMNS", "Checkpoint", "RunResult", "RUN_DEFAULT_VOCAB_VERSION", "RUN_DEFAULT_L4_SCALE",
]


#: ``action_usage`` で ``ENGINE_STEP``(−1)に付ける名(行動語ではない=括弧つき)。
ENGINE_STEP_LABEL: Final[str] = "(エンジン継続)"

#: 〔Q13・返事その 8 §1-2〕ランの既定の語彙の版=CLI の既定(``run_day``・``RunResult``・``cli.CLI_DEFAULT_VOCAB_VERSION``
#: がここから引く)。空腹のモデルの既定は ``world.body.energy.DEFAULT_HUNGER_MODEL``(energy)。
RUN_DEFAULT_VOCAB_VERSION: Final[str] = "v3"
#: 〔Q13〕ランの既定の呼数の倍率=CLI の既定(0=無制限・D-99 (a′)・D-110。``cli.CLI_DEFAULT_L4_SCALE`` がここから引く)。
#: 予算を渡さず倍率も渡さないランの倍率(``resolve_l4_scale``)。
RUN_DEFAULT_L4_SCALE: Final[float] = 0.0

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


#: 5b 層の記録の起床入口(``engine.run`` の診断と同じ 6 つ)。
_ENTRANCES: Final[tuple[str, ...]] = ("場所", "体", "日課", "会話", "満了", "社会")
#: 層の名(SOFAI 形式の記録の鍵)。
DECISION_LAYERS: Final[tuple[str, ...]] = ("system1", "system1_5", "system2")


#: C10 8b(R13): 会話クラス(会話ターン起床)の呼の割合の監査線(宣言=超えたら記録・絞らない=D-110)。
L4_CONVERSATION_SHARE_LINE: Final[float] = 0.15
DEFAULT_RESPONSE_DELAY: Final[int] = 1


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


def _synonym_table_version(vocab_version: str) -> str:
    """語彙版 → 段0 辞書の版文字列(``llm.undefined`` の表が正典)。"""
    from shibuya.act.intake.undefined import synonym_table_version

    return synonym_table_version(str(vocab_version))


def _action_usage(per_action: Mapping[int, int], vocab_version: str) -> dict[str, int]:
    """``ResolveOutcome.per_action``(コード別)→ **行動語別**の件数(D-71 §3 J)。

    ``ENGINE_STEP``(−1・経路の1歩)は行動語ではないので ``"(エンジン継続)"`` の名で残す
    (落とすと合計が ``n_confirmed`` と合わなくなる)。並びは**契約表の順**に固定する
    (dict の挿入順=再実行でバイト一致)。

    逐次ループ宣言(P4): 行動語ぶん(v1=13 / v2=14)。個体数にも tick 数にも比例しない。
    """
    from shibuya.runtime.inference.bridge import ACTION_WORD_BY_CODE

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


def _calls_by_model(llm: int, contact: Any, before: tuple[int, int] = (0, 0), *, calendar2: Any = None,
                    before2: tuple[int, int] = (0, 0), calendar3: Any = None,
                    before3: tuple[int, int] = (0, 0), duties: Any = None,
                    before_du: tuple[int, int] = (0, 0)) -> dict[str, Any]:
    """TM9 の呼び出し数(判断モデル/LLM)。〔第 6 期 6-4 C1 検収 M5 (ii)〕腕 c1 のランは連絡の判断(判断モデル)と文の口(LLM)を
    足し、内訳を ``contact`` に出す(既定のランは今のまま=判断モデル 0)。``before`` は前の日次の記録までの連絡の分。
    〔第 6 期 6-2 カレンダー 2〕腕 arm のランはカレンダー 2 の判断と文の口を同じ形で足し、内訳を ``calendar_2`` に出す
    (``before2``=前の日次の記録までのカレンダー 2 の分・腕の無いランは今のまま)。〔第 6 期 6-2 カレンダー 3〕腕 arm のランは
    カレンダー 3 の判断(雇い主の枠・働く人の書く/申し出る/休みにする/遅れ)を同じ形で足し、内訳を ``calendar_3`` に出す
    (C3 の連絡の送る判断と文は C1 の口=内訳 ``contact`` に入る・``before3``=前の日次の記録までの分)。〔第 6 期 6-6 ② 第 1 部〕
    腕 --duties arm のランは店の仕事の判断(開閉・補充・廃棄)を同じ形で足し、内訳を ``duties`` に出す(``before_du``)。"""
    if contact is None and calendar2 is None and calendar3 is None and duties is None:
        return {"judge_model": 0, "llm": int(llm)}
    out: dict[str, Any] = {"judge_model": 0, "llm": int(llm)}
    for key, layer, b0 in (("contact", contact, before), ("calendar_2", calendar2, before2),
                           ("calendar_3", calendar3, before3), ("duties", duties, before_du)):  # 逐次: 腕の数(4)
        if layer is None:
            continue
        j, t = layer.model_calls()
        j, t = int(j) - int(b0[0]), int(t) - int(b0[1])
        out["judge_model"] += j
        out["llm"] += t
        out[key] = {"judge_model": j, "llm": t}
    return out


def _calendar2_field(layer: Any) -> dict[str, Any]:
    """〔第 6 期 6-2 カレンダー 2〕manifest の ``calendar_2``(会話から生まれる予定の層のあるラン=腕 arm だけ・ほかは空)。"""
    if layer is None:
        return {}
    from shibuya.interim_bundles.calendar2.layer import manifest_fields as _ca2_manifest

    return _ca2_manifest(layer)


def _calendar3_field(layer: Any) -> dict[str, Any]:
    """〔第 6 期 6-2 カレンダー 3〕manifest の ``calendar_3``(雇い主・祝日の層のあるラン=腕 arm だけ・ほかは空)。"""
    if layer is None:
        return {}
    from shibuya.interim_bundles.calendar3.layer import manifest_fields as _ca3_manifest

    return _ca3_manifest(layer)


def _duties_field(layer: Any) -> dict[str, Any]:
    """〔第 6 期 6-6 ② 第 1 部〕manifest の ``duties``(店の仕事の層のあるラン=腕 --duties arm だけ・ほかは空)。"""
    if layer is None:
        return {}
    from shibuya.interim_bundles.duties.layer import manifest_fields as _du_manifest

    return _du_manifest(layer)


def _contact_c1_field(layer: Any) -> dict[str, Any]:
    """〔第 6 期 6-4 C1〕manifest の ``contact_c1``(連絡の道具の層のあるラン=腕 c1 だけ・ほかは空=欄を出さない)。"""
    if layer is None:
        return {}
    from shibuya.interim_bundles.contact.layer import manifest_fields as _ct_manifest

    return {"contact_c1": _ct_manifest(layer)}


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


def _tm234_sections(res: Any) -> dict[str, Any]:
    """〔第 6 期 6-3〕manifest の末尾の時計の段の節(腕の持ち主が居るランだけ・既定のランは空=節を出さない)。"""
    out: dict[str, Any] = {}
    tc = getattr(res, "talk_clock_layer", None)
    if tc is not None:
        out["talk_clock"] = _SPEECH_CLOCK.manifest_fields(tc)
    ss = getattr(res, "step_scope_layer", None)
    if ss is not None:
        out["step_scope"] = _STEP_SCOPE.manifest_fields(
            ss, body_schedule=str(getattr(getattr(res, "body_layer", None), "arm", "")))
    ck = getattr(res, "clock_layer", None)
    if ck is not None:
        out["clock"] = _REGIONAL_CLOCK.manifest_fields(ck)
    return out


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
    #: とおり(400 万呼/日を体数按分)/``0.5``・``2.0``=半分・倍/
    #: ``0.0``=**無制限**(〔Q13〕既定=1 tick の上限を体数に置く=起床候補は合流後に高々 1 件/体なので
    #: 繰り延べが起きない)。
    l4_scale: float = RUN_DEFAULT_L4_SCALE
    #: このランで**実際に使った** 1 tick の呼数上限(``Arbiter.budget``)。既定のランでは
    #: 体数(〔Q13〕無制限。倍率 1.0 のランは ``arbiter.call_budget_per_tick(n_agents)``=5,000 体で 34.72)。
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
    #: **行動語彙の版**(D-71 §3 F・2026-09-17 ユーザー決定)。``"v1"``=24 語/
    #: ``"v2"``=24 語 + 横断語「食事」(飲食店オブジェクトの affordance)/``"v3"``=二層(〔Q13〕既定)。
    vocab_version: str = RUN_DEFAULT_VOCAB_VERSION
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
    #: 購入/食事/並ぶの対象の解決の内訳(段 2a・``engine.poi_target.resolution_summary``)。
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
    #: 5 段目 5a(D-118): 空腹のモデル(``v1``=旧規則 / ``energy``=エネルギー収支=〔Q13〕既定)・消費の式・要約。
    hunger_model: str = DEFAULT_HUNGER_MODEL
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
    #: 〔11-01 段 2 の 3・4〕率の形の規則を外した節(``engine.rate_rules.manifest_fields``=腕・外した印・旧道の件数)。
    #: 出勤率の欄 ``attendance_rate`` は消した(くじの道ごと消した=全員出勤の宣言)。
    rate_rules: dict[str, Any] = field(default_factory=dict)
    #: 〔11-02r §1 #7〕「無い」と宣言した過程 5 件を止めた節(``engine.absent_processes.manifest_fields``=腕・止めた印・旧道の件数)。
    absent_processes: dict[str, Any] = field(default_factory=dict)
    #: 〔11-03 §3〕棚卸し B の欠陥 4 件(M10・M11・M28・M16)の直しの節(``engine.defect_fixes_1103.manifest_fields``=腕・
    #: 直した印・計器)。
    defect_fixes_1103: dict[str, Any] = field(default_factory=dict)
    #: 在圏ブロックの読み口(``engine.presence.DERIVE_RULES``・既定 v2)。
    derive_rule: str = "v2"
    #: **C9 位置幾何の腕**(G1・2026-09-17 ユーザー決定)。``"node"``=現行の 1 tick=1 ノード
    #: (既定・バイト不変)/``"edge"``=辺上の連続位置+希望速度 1.00〜1.60 m/s+Kladek 減速。
    geometry: str = DEFAULT_GEOMETRY
    #: 〔第 5 期 空間の段 1〕切替口 ``--space``(頼んだ値・実際の値・実際の値が違う理由)。
    space: str = _NAV1.DEFAULT_SPACE
    space_effective: str = "legacy"
    space_reason: str = ""
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
    #: 〔第 2 期 2-1〕経済の段階 2 の腕のランで、世帯の現金の外から入った額と現金を通らずに払った額の和[円](引き出し+口座の
    #: 購入・食事+IC の運賃=``economy.stage2.MoneyStage2.cash_terms``)。腕の無いランは 0(``conserved`` の式は今のまま)。
    money_stage2_in: int = 0
    #: 〔第 4 期 4-2・検収 L4〕店の預かり消費税の検算(積んだ − 移した − 残高=0・``MoneyStage2.tax_deposit_ok``)。
    #: 腕の無いラン・腕 off のランは真(``conserved`` の式は今のまま)。
    money_stage2_deposit_ok: bool = True
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
    def waste_band_ok(self) -> bool | None:
        """第304 Q135 (a): **店の収集量**を店だけの帯と比べる(内訳の無い結果は従来どおり総量で比べる)。

        〔11-01 段 2 の 4・検収 M1〕腕 off のラン(``waste_sink.band_ok`` が ``None``)は ``None``=非該当(帯は外した売れ残りの
        廃棄率の期待=比べる相手が無い)。"""
        if self.waste_sink and "band_ok" in self.waste_sink and self.waste_sink["band_ok"] is None:
            return None
        lo, hi = self.waste_band
        v = self.waste_sink.get("breakdown_t", {}).get("store_expired_stock") if self.waste_sink else None
        return bool(hi > 0.0 and lo <= (self.waste_tonnes_per_day if v is None else float(v)) <= hi)

    def state_hashes_fields(self) -> dict[str, Any]:
        """10b: 状態台帳の版・最後の checkpoint の behavior-hash と full-hash・外の状態の直列化のバイト数。"""
        from shibuya.runtime.state.ledger import LEDGER_VERSION

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
            ``plan_executor``/``exit_mode``(D-66 計画実行層の腕。
            既定 ``True``(ただし W16+W17 のあるランだけ立つ)/``immediate``。〔11-01〕出勤率の欄は消した)・
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
            第 3 期 3-2: 末尾に ``batching``(計算のまとめの窓の幅・上限・窓の中の順と、窓の数・持ち越し・上限に当たった数。
            進行役を通らない結果は ``None``)。
        """
        from shibuya.foundation.manifest import sections as _MS
        from shibuya.experiments.port import run_kind as _RK
        from shibuya.world.facts.rights import record as _RR
        from shibuya.foundation.decl import bridging as _BR
        from shibuya.world.facts.rules import table as _RT
        from shibuya.foundation.text import templates as _T

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
            "calls_by_model": _calls_by_model(int(self.llm_calls), getattr(self, "contact_layer", None),
                                              calendar2=getattr(self, "calendar2_layer", None),
                                              calendar3=getattr(self, "calendar3_layer", None),
                                              duties=getattr(self, "duties_layer", None)),
            # 〔第 6 期 6-3 T4〕区域ごとの時計のランだけ regional(既定は今の steps)
            "clock_kind": (CLOCK_KIND if getattr(self, "clock_layer", None) is None
                           else _REGIONAL_CLOCK.CLOCK_KIND_REGIONAL),
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
            # ---- 第 1 期 1-8b(発話の口): 腕の名・届く範囲・出力の欄の指示(設定)と、会話の番・発話・届いた数・口コミに
            # 渡った数(計器)。末尾=… → 1-5 の rights → 1-8 の decision_port → 1-7 の tools → 1-8b。腕 off のランは観測の子が null。
            # 列追加のみ ----
            "speech_port": _SPEECH.manifest_fields(getattr(self, "speech_layer", None)),
            # ---- 第 2 期 2-2 段 11a(近接の判定の切替口): 腕の名・会話の距離 d・B5 の半径・気づく曲線と出典・B5 の単位・
            # 位置の出どころと「暫定」の印(設定)/索引と B5 の単位の在室人数の計器(観測)。末尾=… → 1-8 の decision_port →
            # 1-7 の tools → 1-8b の speech_port → 2-2。腕 cell のランは観測の子が null。列追加のみ ----
            "proximity": _PROX.manifest_fields(getattr(self, "proximity_layer", None)),
            # ---- 第 3 期 3-3(反実仮想の器): 申込書の指紋・種類・水準・T0・決定・登録と封印の指紋(設定)と、効かせた/効かせて
            # いない改変の数と行・計器・T0 より前の再生の計器・4 つの確認の結果(観測)。末尾=… → 1-8b の speech_port → 2-2 の proximity → 3-3。
            # 申込書を渡さないランは null。記録だけ(final・behavior-hash は manifest を読まない)。列追加のみ ----
            "experiment": _EXPERIMENT.manifest_fields(getattr(self, "experiment_layer", None),
                                                      finished=bool(self.resume.get("finished", True))),
            # ---- 第 3 期 3-2(計算のまとめの窓・時計の段 T1): 形の版・幅・既定の幅・刻みの幅・上限・窓の中の順・世界の番号・
            # 事象の種類(設定)と、窓の数・事象の数・持ち越し・上限に当たった数・境目で届けた遅れ(観測)。末尾=… → 3-3 の
            # experiment → 3-2。進行役を通らない結果は null。記録だけ(final・behavior-hash は manifest を読まない)。列追加のみ ----
            "batching": _BATCHING.manifest_fields(getattr(self, "batching_layer", None)),
            # ---- 第 3 期 3-5(本人の体の層・③ 群・TM5 の予約の口): 持ち主・腕・規則の出典の表(conf)・expedient の宣言・器だけの
            # 3 件(設定)と、体の刻みの回数・規則に通した体の延べ・予約・引き直し・段の境目の数と列の鎖のハッシュ(=腕の一致の
            # 計器・観測)。末尾=… → 3-3 の experiment → 3-2 の batching → 3-5。記録だけ(final・behavior-hash は manifest を
            # 読まない)。列追加のみ ----
            "body": _BODY_MODEL.manifest_fields(getattr(self, "body_layer", None)),
            # ---- 第 3 期 3-1(暦 1a の影・CA2 (a)・CA8): 源(w17/1a)・W20 の版・週の数(設定)と、日ごとの影の数・空欄の数・
            # 出勤と始業と終業と帰宅の 15 分の分布・通勤時間・15 分ごとの約束の行動者率・W17 との差(参考)(観測)。末尾=… →
            # 3-3 の experiment → 3-2 の batching → 3-5 の body → 3-1。腕 w17(既定)のランは源だけで観測の子は null。記録だけ(final・
            # behavior-hash は manifest を読まない)。列追加のみ ----
            "calendar_shadow": _CALENDAR_SHADOW.manifest_fields(getattr(self, "calendar_shadow_layer", None)),
            # ---- 〔第 6 期 6-2〕カレンダー 1b(CA2 (b)・CA8): 腕 1b のランだけ末尾に ``calendar_1b``(設定=形の版・腕・口の実装・
            # W20 の版・置き場所・仮採用の値・つなぎの台帳の行/観測=日ごとの計器・合計・エンジンがしないこと 3 つの検査)。
            # 既定(w17)のランは欄を足さない=manifest は今のまま。記録だけ(final・behavior-hash は manifest を読まない) ----
            **_CALENDAR_SELF.manifest_fields(getattr(self, "calendar_self_layer", None)),
            # ---- 〔第 6 期 6-3〕時計の段 T2(会話の時計)・T3(何かあった体だけ)・T4(場所ごとの時計)の節。腕のランだけ出す
            # (既定のランは節を出さない=既定の manifest は不変)。末尾=… → 3-5 の body → 3-1 の calendar_shadow → 6-3。記録だけ
            # (final・behavior-hash は manifest を読まない) ----
            **_tm234_sections(self),
            # ---- 〔第 6 期 6-4 C1〕連絡の道具(腕 c1 のランだけ欄が立つ=既定のランの一番上の鍵は今のまま)。腕の名・下の腕・
            # 宛先の出どころ・窓の境目の種類・気づきの門の段・道具の状態の値・目と心の向きの値(設定)と、届いた・気づいた・読んだ・
            # 返した・無視した・通話・スマホを見た・割り込めなかった出来事・記憶に残ったか・チャットの状態の計器(観測)。末尾=… →
            # 3-1 の calendar_shadow → 6-4。記録だけ(final・behavior-hash は manifest を読まない) ----
            **_contact_c1_field(getattr(self, "contact_layer", None)),
            # ---- 〔第 6 期 6-2 カレンダー 2〕会話とメッセージから生まれる予定(腕 arm のランだけ欄が立つ=既定のランの一番上の鍵は
            # 今のまま)。末尾=… → 6-4 の contact_c1 → 6-2 の calendar_2。記録だけ(final・behavior-hash は manifest を読まない) ----
            **_calendar2_field(getattr(self, "calendar2_layer", None)),
            # ---- 〔第 6 期 6-2 カレンダー 3〕雇い主・祝日(腕 arm のランだけ欄が立つ=既定のランの一番上の鍵は今のまま)。
            # 末尾=… → calendar_2 → calendar_3。記録だけ(final・behavior-hash は manifest を読まない) ----
            **_calendar3_field(getattr(self, "calendar3_layer", None)),
            # ---- 〔第 6 期 6-6 ② 第 1 部〕店の仕事(腕 --duties arm のランだけ欄が立つ=既定のランの一番上の鍵は今のまま)。
            # 末尾=… → calendar_3 → duties。記録だけ(final・behavior-hash は manifest を読まない) ----
            **_duties_field(getattr(self, "duties_layer", None)),
            # ---- 〔第 5 期 空間の段 1〕ナビメッシュの移動の切替口(頼んだ値・実際の値・理由・坂の式・曲がる重み・ナビメッシュの
            # 大きさ=設定/経路と接続口と歩いた長さの計器=観測)。末尾=… → 6-2 の calendar_2 → 5-1。記録だけ(final・
            # behavior-hash は manifest を読まない) ----
            "space": _NAV1.manifest_section(str(self.space), str(self.space_effective), str(self.space_reason),
                                            getattr(self, "space_layer", None)),
            # ---- 〔11-01 段 2 の 3・4〕率の形の規則を外した節(形の版・腕・規則の宣言・外した印=設定/旧道の件数=観測)。
            # 末尾=… → 5-1 の space → 11-01。記録だけ(final・behavior-hash は manifest を読まない)。列追加のみ ----
            "rate_rules": dict(self.rate_rules),
            # ---- 〔11-02r §1 #7〕「無い」と宣言した過程 5 件を止めた節(形の版・腕・過程の宣言・止めた印=設定/旧道の件数=観測)。
            # 末尾=… → 11-01 の rate_rules → 11-02r。記録だけ(final・behavior-hash は manifest を読まない)。列追加のみ ----
            "absent_processes": dict(self.absent_processes),
            # ---- 〔11-03 §3〕棚卸し B の欠陥 4 件の直しの節(形の版・腕・4 件の宣言・直した印=設定/計器=観測)。
            # 末尾=… → 11-02r の absent_processes → 11-03。記録だけ(final・behavior-hash は manifest を読まない)。列追加のみ ----
            "defect_fixes_1103": dict(self.defect_fixes_1103),
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
        C2 の等式そのまま。〔第 2 期 2-1〕経済の段階 2 の腕のランは、現金の外から入った額と現金を通らずに払った額
        (``money_stage2_in``)を左辺に足す(腕の無いランは 0=今の等式)。帳簿の保存則の検算は日次の記録の
        ``economy.conservation``。〔第 4 期 4-2・検収 L4〕店の預かり消費税の検算(``money_stage2_deposit_ok``)も入れる。
        """
        return (self.money_start + self.money_stage2_in == self.money_end + self.revenue_end + self.fares_paid
                and bool(self.money_stage2_deposit_ok))

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
        # 〔第 5 期 空間の段 1〕ナビメッシュの移動のランだけ 1 行
        if str(self.space_effective) == "nav1":
            lines.append("  " + _NAV1.summary_line(getattr(self, "space_layer", None)))
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
                f"{self.waste_band[1]:.2f}) "
                f"{self.waste_sink.get('band_na', '') if self.waste_band_ok is None else ('OK' if self.waste_band_ok else 'NG')}"
                f"{self._waste_band_note()}"
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
