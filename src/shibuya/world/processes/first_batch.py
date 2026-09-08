"""world.processes.first_batch — **第1陣の宣言(データのみ・振る舞い無し)**。

正典
- 世界過程設計書 §6 **D-R2-5(決定・2026-09-07)**: 「**第1陣**=昼夜(日照=B3)・天候(気象庁実測の
  特定日を再生=B3・体感温度)・鉄道運行(ODPT静的ダイヤ=U10第1陣)・混雑場(密度段階=B4・人物①)・
  営業時間(PlanSpec=看板(a))・静的騒音場(B4段階)」。
- §7.1/§7.2 **U-Goods**(決定・2026-09-07・「陣分けは可能な限り初回実装へ前倒し」):
  初回実装(第1陣)=物の保存則骨格/店舗補充・棚在庫/納品/廃棄物収集/屋内占有の集約/断面自動車交通。
  初回実装へ前倒し(第2陣分)=宅配ラストマイル/バス・タクシー/公共サービス出動/街路清掃/
  インフラ日負荷/ホテル客室在庫/道路工事・占用/報道・公式発信/大規模イベント。
- §4 16行表(executor の割り当て)・§5 D-R2-4(reaches/contributes)・§2(関係4本)。

**§1 の線引きとの関係**: 「bbox 内に運転主体がいる過程(店の棚の補充・開店閉店・接客)は
世界過程では**なく**、層2(役割の知識を持つエージェント)の仕事」。棚在庫・納品・収集・清掃を
本ファイルが台帳へ載せるのは「エンジンが動かす」という意味ではなく、**保存則(§7.1)・門前条件・
状態成長宣言(D-R2-6)を一元管理するため**で、実際の駆動主体は ``executor=llm_agent`` が示す。
``executor=engine_rule`` の行だけが §1 末尾のフォールバック台帳(返済期限つき)に載る。

**PROPOSED(=ユーザー承認が要る設計追加)**
D-R2-5 は昼夜・天候を「B3」と書くが、知覚契約書 §3 のチャネル仕様表に **ブロック B3 を持つ行が
1つも無い**(表のブロック列は B2/B4/B4b/B5 のみ)。本ファイルは黙ってチャネルを発明せず、
昼夜=「内受容(体感温度・日陰係数0.86)」+「人物③(p_notice の照明係数 m_light 昼1.0/夜0.68)」、
天候=「内受容」で (a) を満たす。B3 用チャネル行の新設案は
``constitution.PROPOSED_CHANNEL_IDS`` に置いてある(既定の検査集合には**入れない**)。
"""

from __future__ import annotations

from typing import Final, Mapping

from shibuya.core.growth import GrowthDeclaration, Retention
from shibuya.world.processes.constitution import PROPOSED_CHANNEL_IDS
from shibuya.world.processes.records import (
    AnnouncementScope,
    Clock,
    DetailDeclaration,
    Executor,
    Modality,
    NormKind,
    PlanSpec,
    ProcessKind,
    Validity,
    Violability,
    WorldProcess,
)
from shibuya.world.processes.registry import WorldRegistry
from shibuya.world.processes.relations import (
    CountsAs,
    Realizes,
    Records,
    Relation,
    SubjectType,
)

__all__ = [
    "BATCH_FIRST",
    "BATCH_PULLED_FORWARD",
    "ACTUAL_LOG_ID",
    "DECLARATIONS",
    "PULLED_FORWARD_DECLARATIONS",
    "PLAN_SPECS",
    "DETAILS",
    "RELATIONS",
    "PROPOSED_CHANNEL_IDS",
    "build_registry",
    "growth_declarations",
]

BATCH_FIRST: Final[str] = "第1陣(D-R2-5 / §7.2 初回実装)"
BATCH_PULLED_FORWARD: Final[str] = "初回実装へ前倒し(§7.2 第2陣分)"
ACTUAL_LOG_ID: Final[str] = "actual_log"

#: cap の割当元(予算表)。M8=RSS総額 ≤24GB・S1=恒久記録 ≤5GB/シミュ日。
_CAP_1MB: Final[int] = 1 * 1024 * 1024
_CAP_16MB: Final[int] = 16 * 1024 * 1024
_CAP_64MB: Final[int] = 64 * 1024 * 1024


def _g(
    name: str,
    *,
    ops: int,
    cap: int,
    per_agent: int = 0,
    per_cell: int = 0,
    note: str = "",
) -> GrowthDeclaration:
    """第1陣の成長宣言(D-R2-6 の5欄)。

    第1陣の世界過程は**全て O(1)**(SoA 配列・リングバッファ・場)であり、日をまたいで伸びない。
    §2「**O(t) 成長する唯一の型は ActualLog**」——伸びる分は ``actual_log`` の宣言が持つ。
    """
    return GrowthDeclaration(
        name=name,
        per_agent_bytes=per_agent,
        per_cell_bytes=per_cell,
        per_day_growth="O(1)",
        per_day_growth_coef=0.0,
        retention=Retention(None, ""),
        worst_case_ops_per_tick=int(ops),
        cap=int(cap),
        cap_budget_row="M8",
        mechanism=True,
        note=note or "O(1): 場・状態配列で保持し日をまたいで伸びない(§2・O(t) は ActualLog だけ)",
    )


# ================================================================== 第1陣: D-R2-5 の6本
_DAYNIGHT = WorldProcess(
    id="daynight_solar",
    kind=ProcessKind.NATURAL,
    state_vars=("solar_altitude_deg", "solar_azimuth_deg", "is_daylight", "shadow_grid_version"),
    update_rule=(
        "天文計算で太陽高度・方位を1分tickごとに評価し、時間帯ごとに前計算した影グリッド"
        "(2.5m格子)の版を切り替える。書き込み口は resolve 1本(§3 実装原則3)"
    ),
    clock=Clock.PHYSICAL,
    modality=Modality.ENGINE_DRIVEN,
    executor=Executor.NONE,
    growth=_g("daynight_solar", ops=2_000, cap=_CAP_1MB, per_cell=8),
    catalog_classes=("昼夜・日照・影",),
    gate_condition=(
        "日照と影が体感温度(内受容・日陰係数0.86)と夜間の視認距離"
        "(人物③ p_notice の m_light=夜0.68)を動かす — 知覚契約書 §3/§3.1"
    ),
    reaches=("内受容", "人物③"),
    norm_kind=NormKind.BRUTE_PHYSICAL,
    violability=Violability.REGIMENTED,
    batch=BATCH_FIRST,
    note=(
        "D-R2-5 は「昼夜(日照=B3)」と書くが §3 に B3 のチャネル行が無いため、"
        f"届き先は内受容・人物③ を使う。B3 チャネル新設案は PROPOSED: {PROPOSED_CHANNEL_IDS}"
    ),
)

_WEATHER = WorldProcess(
    id="weather",
    kind=ProcessKind.NATURAL,
    state_vars=("temp_c", "precip_mm", "wind_ms", "humidity_pct", "apparent_temp_c"),
    update_rule=(
        "気象庁実測の特定日を再生(D-R2-5)。tick 単位に線形補間し、"
        "体感温度=気温×影グリッド(日陰0.86)で内受容へ渡す"
    ),
    clock=Clock.PHYSICAL,
    modality=Modality.ENGINE_DRIVEN,
    executor=Executor.NONE,
    growth=_g("weather", ops=2_000, cap=_CAP_1MB, per_cell=16),
    catalog_classes=("天候・気温(+生成器)",),
    gate_condition="実測日の再生が体感温度(内受容 0-10・閾値割れのみ B5)を動かす — D-R2-5",
    reaches=("内受容",),
    norm_kind=NormKind.BRUTE_PHYSICAL,
    violability=Violability.REGIMENTED,
    batch=BATCH_FIRST,
    note="D-R2-5「天候(気象庁実測の特定日を再生=B3・体感温度)」。B3 は §3 に行が無い(上と同じ)",
)

_RAIL = WorldProcess(
    id="rail_operation_static",
    kind=ProcessKind.AGENT_FALLBACK,
    state_vars=("trip_id", "trip_phase", "next_stop_idx", "headway_s"),
    update_rule=(
        "ODPT 静的ダイヤ(1,810本)を PlanSpec として参照し、便を予定どおり進める。"
        "遅延・運休・増発は第2陣(運行連動)でエージェント判断へ移す"
    ),
    clock=Clock.INSTITUTIONAL,
    modality=Modality.PLAN_REFERENCE,
    executor=Executor.ENGINE_RULE,
    growth=_g("rail_operation_static", ops=8_000, cap=_CAP_1MB),
    catalog_classes=("鉄道運行(静的→運行連動)",),
    gate_condition=(
        "駅の乗降絶対量(D10)と朝ピーク混雑率(D10′)で境界フローを照合する"
        "=U10「流入エージェント決定」の直接検証装置"
    ),
    contributes=("D10", "D10′"),
    mechanism=False,
    sensitivity_test_id="AB-RAIL-EXECUTOR",
    conf=0.6,
    coverage="ODPT 静的ダイヤ 1,810 本の全便(乗務員エージェント未実装ぶん=100%)",
    repayment_due="第2陣(運行連動)で乗務員・指令エージェントへ移す(§1 D-R2-1・§6 D-R2-5)",
    norm_kind=NormKind.REGULATIVE,
    violability=Violability.ENFORCED,
    revisability="指令エージェント(各社・数体)が revises(指令, PlanSpec) で改訂(§1 追補)",
    batch=BATCH_FIRST,
    note="§1「域外区間の進行のみ B 類」。第1陣は bbox 内も engine_rule で回す=返済対象",
)

_CROWD = WorldProcess(
    id="crowd_field",
    kind=ProcessKind.AGGREGATE,
    state_vars=("density_per_m2", "flow_dir_rad", "los_stage"),
    update_rule=(
        "個体位置をセルへ集計し Fruin LOS 型の段階へ量子化(世界側 DENSITY_STAGE_EDGES)。"
        "SoA のベクトル演算1本/tick・逐次ループ新設なし"
    ),
    clock=Clock.PHYSICAL,
    modality=Modality.DERIVED_FROM_ACTIONS,
    executor=Executor.NONE,
    growth=_g("crowd_field", ops=400_000, cap=_CAP_1MB, per_cell=64),
    catalog_classes=("混雑場(密度)",),
    gate_condition=(
        "セル密度段階が時刻別滞在人口カーブ(D1′)と3街路の日内プロファイル分化(D4′)に一致する"
    ),
    reaches=("人物①", "聴覚: 密度項"),
    contributes=("D1′", "D4′"),
    norm_kind=NormKind.BRUTE_PHYSICAL,
    violability=Violability.REGIMENTED,
    batch=BATCH_FIRST,
    note="§3「聴覚: 密度項 … 源=混雑場上のミップ畳み込み」=この場が2チャネルを養う",
)

_OPENING = WorldProcess(
    id="store_opening",
    kind=ProcessKind.AGENT_FALLBACK,
    state_vars=("poi_is_open", "poi_open_min", "poi_close_min"),
    update_rule=(
        "営業時間 PlanSpec を参照して POI の開閉フラグを日次で切り替える。"
        "本来は店主エージェントの開閉店行動(§1 D-R2-1「層2が正」)"
    ),
    clock=Clock.INSTITUTIONAL,
    modality=Modality.PLAN_REFERENCE,
    executor=Executor.ENGINE_RULE,
    growth=_g("store_opening", ops=20_000, cap=_CAP_1MB, per_cell=24),
    catalog_classes=("営業(開閉店)",),
    gate_condition="開閉が看板(a)(店舗基本属性・B2)としてセル観測に載る — D-R2-5「営業時間(PlanSpec=看板(a))」",
    reaches=("看板(a)",),
    mechanism=False,
    sensitivity_test_id="AB-OPENING-EXECUTOR",
    conf=0.5,
    coverage="bbox 内 POI の営業時間表(センサス由来の既定表)による開閉=全 POI",
    repayment_due="Phase 3(店主エージェントの開閉店行動へ返済・§1 D-R2-1「一時的にフォールバック側」)",
    norm_kind=NormKind.REGULATIVE,
    violability=Violability.UNENFORCED,
    revisability="店主エージェント(revises)。営業時間変更は §2 の revises で発火",
    batch=BATCH_FIRST,
)

_NOISE = WorldProcess(
    id="static_noise_field",
    kind=ProcessKind.AGGREGATE,
    state_vars=("l_aeq_day_db", "l_aeq_night_db", "noise_stage"),
    update_rule=(
        "ASJ RTN-Model 2018 の非定常式 L_WA=a+b·lg V(a=82.3/88.8・b=10)で断面交通量から"
        "前計算し、街渓谷反射 +6-8 dB を足して法定境界の段階語彙へ量子化(§3)"
    ),
    clock=Clock.PHYSICAL,
    modality=Modality.ENGINE_DRIVEN,
    executor=Executor.NONE,
    growth=_g("static_noise_field", ops=2_000, cap=_CAP_16MB, per_cell=32),
    catalog_classes=("騒音場",),
    gate_condition=(
        "静的騒音場が都環境局R5の道路沿道 LAeq 7点(D12′)に残差≤3 dB で一致する"
    ),
    reaches=("聴覚: 静的場",),
    contributes=("D12′",),
    norm_kind=NormKind.BRUTE_PHYSICAL,
    violability=Violability.REGIMENTED,
    batch=BATCH_FIRST,
    note="段階境界は法定/LOS 境界に釘付け(§2.4 正規化規約⑤)=mechanism",
)

# ================================================================== 第1陣: U-Goods 骨格(§7.1/§7.2)
_GOODS = WorldProcess(
    id="goods_conservation",
    kind=ProcessKind.AGGREGATE,
    state_vars=("sku_stock", "faucet_ledger", "sink_ledger", "residual_stocktake_diff", "hoarding"),
    update_rule=(
        "move_goods(from, to, qty, sku, account_code) 単一 API。在庫の直接代入は静的禁止。"
        "日次で検算①(全 SKU で 期首在庫+流入−流出=期末在庫・O(N) 総和)"
    ),
    clock=Clock.INSTITUTIONAL,
    modality=Modality.ENGINE_DRIVEN,
    executor=Executor.NONE,
    growth=_g("goods_conservation", ops=50_000, cap=_CAP_64MB, per_cell=256),
    catalog_classes=("商品(SKU)・棚在庫",),
    gate_condition="検算②=廃棄 sink の月次総量が渋谷区ごみ実数(119.6 t/日)の band(W1)に入る(§7.1)",
    contributes=("W1",),
    norm_kind=NormKind.BRUTE_PHYSICAL,
    violability=Violability.REGIMENTED,
    batch=BATCH_FIRST,
    note="金の U11(transfer 単一 API)と同型。faucet=域外仕入/sink=消費・廃棄搬出・返品(§7.1)",
)

_SHELF = WorldProcess(
    id="shelf_stock_restock",
    kind=ProcessKind.AGGREGATE,
    state_vars=("shelf_qty_by_sku", "reorder_point", "reorder_lot", "shrinkage"),
    update_rule=(
        "客の購買(エンジン resolve)が棚を減らし、店員 T0 行動(LLM)が補充閾値割れで補充する。"
        "SKU 別在庫は店舗 POI 側(per_cell_bytes)に置き個体 M1 には載せない(§7.1)"
    ),
    clock=Clock.PHYSICAL,
    modality=Modality.DERIVED_FROM_ACTIONS,
    executor=Executor.LLM_AGENT,
    growth=_g("shelf_stock_restock", ops=50_000, cap=_CAP_64MB, per_cell=512),
    catalog_classes=("商品(SKU)・棚在庫", "補充・納品"),
    gate_condition=(
        "「棚が減る=店員が補充する」(CLAUDE.md §3)が閉じた収支として検証できる"
        "=消費支出アンカー(E5)と廃棄 sink(W1)の両方に接続する"
    ),
    reaches=("看板(a)",),
    contributes=("W1", "E5"),
    dilatable=True,
    mechanism=False,
    sensitivity_test_id="AB-SHELF-REORDER",
    repayment_due="Phase 3(SKU 粒度・棚卸閾値・初期在庫・補充閾値/ロットの較正データ取得後)",
    norm_kind=NormKind.BRUTE_PHYSICAL,
    violability=Violability.REGIMENTED,
    batch=BATCH_FIRST,
    note="§7.2 expedient 欄「SKU粒度・棚卸閾値・初期在庫・補充閾値/ロット」",
)

_DELIVERY_IN = WorldProcess(
    id="delivery_inbound",
    kind=ProcessKind.AGGREGATE,
    state_vars=("inbound_trip_id", "inbound_qty_by_sku", "dock_slot"),
    update_rule="納品ドライバー(層2・早朝帯)が域外仕入(faucet)を店舗へ運ぶ。実績は ActualLog へ記録",
    clock=Clock.PHYSICAL,
    modality=Modality.DERIVED_FROM_ACTIONS,
    executor=Executor.LLM_AGENT,
    growth=_g("delivery_inbound", ops=6_000, cap=_CAP_16MB),
    catalog_classes=("補充・納品",),
    gate_condition="納品量の日次総和が消費支出アンカー(E5)と棚在庫の収支に整合する(§7.1 検算①)",
    reaches=("可視性",),
    contributes=("E5",),
    dilatable=True,
    mechanism=False,
    sensitivity_test_id="AB-DELIVERY-FREQ",
    repayment_due="Phase 3(納品頻度・時間帯の実データ取得後)",
    batch=BATCH_FIRST,
)

_WASTE = WorldProcess(
    id="waste_collection",
    kind=ProcessKind.AGGREGATE,
    state_vars=("waste_stock_kg", "waste_class", "collection_day", "truck_load_kg"),
    update_rule=(
        "世帯・事業所の排出(C 類集約)が集積所ストックを増やし、清掃員(層2)の収集行動が"
        "bbox 外へ運び出す=廃棄 sink への計上"
    ),
    clock=Clock.INSTITUTIONAL,
    modality=Modality.DERIVED_FROM_ACTIONS,
    executor=Executor.LLM_AGENT,
    growth=_g("waste_collection", ops=6_000, cap=_CAP_16MB, per_cell=32),
    catalog_classes=("廃棄物収集", "廃棄物ストック"),
    gate_condition="廃棄 sink の月次総量が渋谷区ごみ実数 119.6 t/日の band(W1)に入る(§7.1 検算②)",
    reaches=("可視性",),
    contributes=("W1",),
    dilatable=True,
    mechanism=False,
    sensitivity_test_id="AB-WASTE-ROUTE",
    repayment_due="Phase 3(区の収集ルート・積載の実データ取得後)",
    batch=BATCH_FIRST,
)

_INDOOR = WorldProcess(
    id="indoor_occupancy",
    kind=ProcessKind.AGGREGATE,
    state_vars=("seats_total", "seats_used", "queue_len", "balk_threshold"),
    update_rule=(
        "施設の容量 c と M/M/c 近似で在席・待ち行列を集約(16行表 行2=エンジン全部)。"
        "離脱閾値超で待たずに去る"
    ),
    clock=Clock.PHYSICAL,
    modality=Modality.DERIVED_FROM_ACTIONS,
    executor=Executor.NONE,
    growth=_g("indoor_occupancy", ops=20_000, cap=_CAP_16MB, per_cell=48),
    catalog_classes=("建物内フロア・区画",),
    gate_condition="行列・人だかり(人物②)がセル観測に載り、商業滞在時間(D8)の形で照合される",
    reaches=("人物②",),
    contributes=("D8",),
    mechanism=False,
    sensitivity_test_id="AB-OCCUPANCY-CAPACITY",
    repayment_due="Phase 3(渋谷の実店舗席数=現在空欄・取得後に較正)",
    batch=BATCH_FIRST,
    note="16行表 行2「席数換算式・回転率・離脱閾値=全部 expedient(渋谷の実店舗席数は空欄)」",
)

_TRAFFIC = WorldProcess(
    id="vehicle_cross_section",
    kind=ProcessKind.EXTERNAL_SYSTEM,
    state_vars=("cross_section_id", "vehicle_count_per_hour", "heavy_ratio", "mean_speed_kmh"),
    update_rule=(
        "bbox 外で発生する通過交通(B 類)を断面ごとの時間帯別交通量として外生投入し、"
        "静的騒音場の V(速度・台数)を駆動する"
    ),
    clock=Clock.PHYSICAL,
    modality=Modality.ENGINE_DRIVEN,
    executor=Executor.ENGINE_RULE,
    growth=_g("vehicle_cross_section", ops=5_000, cap=_CAP_16MB, per_cell=32),
    catalog_classes=("自動車(通過交通・OD)",),
    gate_condition=(
        "断面自動車交通が道路交通センサス令和3年度の箇所別時間帯別交通量(D5′)と"
        "日内二峰性(D5)に一致する"
    ),
    reaches=("聴覚: 静的場",),
    contributes=("D5′", "D5"),
    mechanism=False,
    sensitivity_test_id="AB-THROUGH-TRAFFIC-RATIO",
    conf=0.4,
    coverage="bbox 断面を通過する自動車交通の全量(自動車運転者をエージェント化しないぶん=100%)",
    repayment_due="第3陣(自動車運転者のエージェント化・§7.2)",
    batch=BATCH_FIRST,
    note="§7.2 expedient 欄「通過交通比率」",
)

#: D-R2-5 の6本 + U-Goods 骨格6本。
DECLARATIONS: Final[tuple[WorldProcess, ...]] = (
    _DAYNIGHT,
    _WEATHER,
    _RAIL,
    _CROWD,
    _OPENING,
    _NOISE,
    _GOODS,
    _SHELF,
    _DELIVERY_IN,
    _WASTE,
    _INDOOR,
    _TRAFFIC,
)


# ================================================================== 初回実装へ前倒し(§7.2 第2陣分)
PULLED_FORWARD_DECLARATIONS: Final[tuple[WorldProcess, ...]] = (
    WorldProcess(
        id="delivery_last_mile",
        kind=ProcessKind.AGGREGATE,
        state_vars=("parcel_id", "parcel_state", "courier_id", "attempt_count"),
        update_rule="配達員(層2)が宅配便を世帯・事業所へ配る。再配達は attempt_count で数える",
        clock=Clock.PHYSICAL,
        modality=Modality.DERIVED_FROM_ACTIONS,
        executor=Executor.LLM_AGENT,
        growth=_g("delivery_last_mile", ops=6_000, cap=_CAP_16MB),
        catalog_classes=("宅配・出前",),
        gate_condition="日次個数が全国50億3,147万個の区按分(W2・≈2.7万個/日)の上界 band に収まる",
        reaches=("可視性",),
        contributes=("W2",),
        dilatable=True,
        mechanism=False,
        sensitivity_test_id="AB-PARCEL-ALLOCATION",
        repayment_due="Phase 3(区別実績の取得後・按分係数を返済)",
        batch=BATCH_PULLED_FORWARD,
    ),
    WorldProcess(
        id="bus_taxi_operation",
        kind=ProcessKind.AGENT_FALLBACK,
        state_vars=("vehicle_id", "vehicle_phase", "occupancy", "dispatch_state"),
        update_rule=(
            "運転手(層2)が PlanSpec(バス時刻表)に従って運行し、タクシーは配車状態で動く。"
            "営業所・配車の指令エージェントが PlanSpec を改訂(§1 追補「業種横断の一般パターン」)"
        ),
        clock=Clock.INSTITUTIONAL,
        modality=Modality.PLAN_REFERENCE,
        executor=Executor.LLM_AGENT,
        growth=_g("bus_taxi_operation", ops=8_000, cap=_CAP_16MB),
        catalog_classes=("バス", "タクシー"),
        gate_condition="トリップ原単位2.61/人日(D6)・外出率0.766(D7)の上界 band に収まる",
        reaches=("可視性",),
        contributes=("D6", "D7"),
        dilatable=True,
        mechanism=False,
        sensitivity_test_id="AB-DISPATCH",
        repayment_due="Phase 3(配車アルゴリズムの較正データ取得後)",
        revisability="営業所・配車の指令エージェント(revises)",
        norm_kind=NormKind.REGULATIVE,
        violability=Violability.ENFORCED,
        batch=BATCH_PULLED_FORWARD,
    ),
    WorldProcess(
        id="public_service_dispatch",
        kind=ProcessKind.AGGREGATE,
        state_vars=("unit_id", "unit_state", "incident_id", "response_delay_min"),
        update_rule="救急隊・警察(層2の隊)が規則ゲート(通報→出動可否)を通って出動する",
        clock=Clock.PHYSICAL,
        modality=Modality.DERIVED_FROM_ACTIONS,
        executor=Executor.LLM_AGENT,
        growth=_g("public_service_dispatch", ops=4_000, cap=_CAP_16MB),
        catalog_classes=("救急・警察出動",),
        gate_condition="出場頻度が東京消防庁 令和6年 935,373件の都→区按分(W3)の band に収まる",
        reaches=("人物③",),
        contributes=("W3",),
        dilatable=True,
        mechanism=False,
        sensitivity_test_id="AB-DISPATCH-DELAY",
        repayment_due="Phase 3(署別実績が未取得=空欄・取得後に返済)",
        batch=BATCH_PULLED_FORWARD,
        note="§3 人物③「顕著な行為(倒れる・叫び・警察)」=出動そのものが到達チャネルを持つ",
    ),
    WorldProcess(
        id="street_cleaning",
        kind=ProcessKind.AGGREGATE,
        state_vars=("litter_stock_kg", "cleaning_shift", "swept_cell_count"),
        update_rule="清掃員(層2)が街路のごみストックを減らす。回収分は廃棄 sink へ計上",
        clock=Clock.INSTITUTIONAL,
        modality=Modality.DERIVED_FROM_ACTIONS,
        executor=Executor.LLM_AGENT,
        growth=_g("street_cleaning", ops=4_000, cap=_CAP_16MB, per_cell=16),
        catalog_classes=("街路清掃・美化",),
        gate_condition="回収量が廃棄物の月次総量(W1)の内訳として収支に載る(§7.1)",
        reaches=("可視性",),
        contributes=("W1",),
        dilatable=True,
        mechanism=False,
        sensitivity_test_id="AB-CLEANING-RATE",
        repayment_due="Phase 3(原単位が空欄=取得後に返済)",
        batch=BATCH_PULLED_FORWARD,
    ),
    WorldProcess(
        id="infra_daily_load",
        kind=ProcessKind.AGGREGATE,
        state_vars=("power_kwh_per_hour", "water_m3_per_hour"),
        update_rule="在席・営業・世帯の集約から電力・水の日負荷を原単位で積む(集約のみ・網は持たない)",
        clock=Clock.INSTITUTIONAL,
        modality=Modality.DERIVED_FROM_ACTIONS,
        executor=Executor.NONE,
        growth=_g("infra_daily_load", ops=2_000, cap=_CAP_1MB, per_cell=16),
        catalog_classes=("インフラ日負荷(電力・水)",),
        gate_condition="日負荷の形状が W5(電力・水の日内形状)に一致する(値は形状のみ)",
        contributes=("W5",),
        mechanism=False,
        sensitivity_test_id="AB-INFRA-INTENSITY",
        repayment_due="Phase 3(W5 の実数が空欄=都環境局・区別データの探索後)",
        batch=BATCH_PULLED_FORWARD,
        note="§7.2 保留欄「配電網・水道管網は憲法5(a)(b)不成立=停電/断水は離散事象フラグのみ」",
    ),
    WorldProcess(
        id="hotel_room_inventory",
        kind=ProcessKind.AGENT_FALLBACK,
        state_vars=("rooms_total", "rooms_occupied", "adr_yen"),
        update_rule="客室在庫を日次で更新(フロント業務のエージェント化前はエンジン規則で代替)",
        clock=Clock.INSTITUTIONAL,
        modality=Modality.ENGINE_DRIVEN,
        executor=Executor.ENGINE_RULE,
        growth=_g("hotel_room_inventory", ops=1_000, cap=_CAP_1MB, per_cell=16),
        catalog_classes=("ホテル客室",),
        gate_condition="客室稼働が観光庁宿泊旅行統計(都・月次)の band(W6)に収まる=U10 来街者の裏付け",
        contributes=("W6",),
        mechanism=False,
        sensitivity_test_id="AB-HOTEL-ROOMS",
        conf=0.4,
        coverage="bbox 内ホテルの客室在庫(フロント業務をエージェント化しないぶん=100%)",
        repayment_due="Phase 3(フロント業務のエージェント化・客室数の実データ取得後)",
        batch=BATCH_PULLED_FORWARD,
    ),
    WorldProcess(
        id="road_works_occupancy",
        kind=ProcessKind.AGGREGATE,
        state_vars=("work_id", "occupied_edges", "work_phase"),
        update_rule="作業員(層2)が道路占用 PlanSpec の期間に従って車線・歩道を塞ぐ",
        clock=Clock.INSTITUTIONAL,
        modality=Modality.PLAN_REFERENCE,
        executor=Executor.LLM_AGENT,
        growth=_g("road_works_occupancy", ops=1_000, cap=_CAP_1MB, per_cell=8),
        catalog_classes=("道路工事・占用",),
        gate_condition="占用が可視物(柵・案内)としてセル観測に載り、通行可能性(B2 近接路面)を変える",
        reaches=("可視性",),
        dilatable=True,
        mechanism=False,
        sensitivity_test_id="AB-ROADWORK-FREQ",
        repayment_due="Phase 3(工事頻度が空欄=占用許可データの取得後)",
        norm_kind=NormKind.REGULATIVE,
        violability=Violability.ENFORCED,
        batch=BATCH_PULLED_FORWARD,
    ),
    WorldProcess(
        id="press_official_release",
        kind=ProcessKind.AGGREGATE,
        state_vars=("release_id", "topic", "issued_tick", "reach_kinds"),
        update_rule="広報・報道の担い手(層2)が運行情報・公式発信を出す。伝播は SNS/口づて側が担う",
        clock=Clock.PHYSICAL,
        modality=Modality.DERIVED_FROM_ACTIONS,
        executor=Executor.LLM_AGENT,
        growth=_g("press_official_release", ops=500, cap=_CAP_1MB),
        catalog_classes=("報道・公式発信(運行情報)",),
        gate_condition=(
            "公式発信を起点にしてもカスケードの99%が1世代で終わる(C1)ことを崩さない"
            "=情報伝播の過大を検出する門"
        ),
        contributes=("C1",),
        dilatable=True,
        mechanism=False,
        sensitivity_test_id="AB-PRESS-REACH",
        repayment_due="Phase 3(発信頻度・到達範囲の較正後)",
        norm_kind=NormKind.DESCRIPTIVE_ONLY,
        violability=Violability.UNENFORCED,
        batch=BATCH_PULLED_FORWARD,
    ),
    WorldProcess(
        id="large_event",
        kind=ProcessKind.AGENT_FALLBACK,
        state_vars=("event_id", "event_window", "visitor_delta", "affected_cells"),
        update_rule="報道ベースの大規模イベントを外生投入し、来街者の増分と占有セルを与える",
        clock=Clock.INSTITUTIONAL,
        modality=Modality.ENGINE_DRIVEN,
        executor=Executor.ENGINE_RULE,
        growth=_g("large_event", ops=1_000, cap=_CAP_1MB),
        catalog_classes=("大規模イベント",),
        gate_condition="イベント日の滞在人口カーブ(D1′)と3街路プロファイル(D4′)が実測側の形に近づく",
        contributes=("D1′", "D4′"),
        mechanism=False,
        sensitivity_test_id="AB-EVENT-DELTA",
        conf=0.3,
        coverage="報道で確認できる大規模イベント(主催者・参加者をエージェント化しないぶん=100%)",
        repayment_due="Phase 3(イベント来街増分の実データ取得後・§7.2「expedient 強」)",
        batch=BATCH_PULLED_FORWARD,
    ),
)


# ================================================================== PlanSpec(§2 レコード型2)
PLAN_SPECS: Final[tuple[PlanSpec, ...]] = (
    PlanSpec(
        id="plan.rail_timetable",
        content="ODPT 実ダイヤ 1,810 本(路線・便・停車時刻)=計画データの初期値(§1 D-R2-1)",
        validity=Validity(valid_from=0, valid_to=None),
        version=1,
        transaction_tick=0,
        revising_authority="指令エージェント(各社・層2)",
        norm_kind=NormKind.REGULATIVE,
        violability=Violability.ENFORCED,
        announcement_scope=AnnouncementScope(
            kinds=("住民", "通勤者", "来街者", "従業者", "乗務員", "指令"),
            cells=("駅セル(地上/駅地下)",),
            blocks=("B2",),
            channel_ids=("看板(a)",),
        ),
        compliance_field="rail_ontime_rate",
        catalog_classes=("ダイヤ・営業時間・価格表(PlanSpec)", "鉄道運行(静的→運行連動)"),
        gate_condition="遵守率(ActualLog 一致率)の分布が現実の遅延データ(D10′・ODPT)と突き合う",
        contributes=("D10′",),
        batch=BATCH_FIRST,
        note="§1 追補: 障害時は指令員が計画そのものを書き換え、乗務員が改訂版に従う",
    ),
    PlanSpec(
        id="plan.opening_hours",
        content="POI 別の営業時間表(経済センサス由来の既定表。POI の営業時間は実データ0件)",
        validity=Validity(valid_from=0, valid_to=None),
        version=1,
        transaction_tick=0,
        revising_authority="店主エージェント(層2)",
        norm_kind=NormKind.REGULATIVE,
        violability=Violability.UNENFORCED,
        announcement_scope=AnnouncementScope(
            kinds=("住民", "通勤者", "来街者", "従業者"),
            cells=("店舗 POI を含む全セル",),
            blocks=("B2",),
            channel_ids=("看板(a)",),
        ),
        compliance_field="opening_hours_compliance_rate",
        catalog_classes=("ダイヤ・営業時間・価格表(PlanSpec)", "営業(開閉店)"),
        gate_condition="開閉が看板(a)としてセル観測に載る(D-R2-5「営業時間(PlanSpec=看板(a))」)",
        mechanism=False,
        sensitivity_test_id="AB-OPENING-TABLE",
        repayment_due="Phase 3(POI 営業時間の実データ取得後・既定表は expedient)",
        batch=BATCH_FIRST,
    ),
    PlanSpec(
        id="plan.bus_timetable",
        content="ODPT GTFS(バス)の時刻表=バス運行の計画データ",
        validity=Validity(valid_from=0, valid_to=None),
        version=1,
        transaction_tick=0,
        revising_authority="営業所の指令エージェント(層2)",
        norm_kind=NormKind.REGULATIVE,
        violability=Violability.ENFORCED,
        announcement_scope=AnnouncementScope(
            kinds=("住民", "通勤者", "来街者", "従業者", "乗務員"),
            cells=("バス停を含むセル",),
            blocks=("B2",),
            channel_ids=("看板(a)",),
        ),
        compliance_field="bus_ontime_rate",
        catalog_classes=("ダイヤ・営業時間・価格表(PlanSpec)", "バス"),
        gate_condition="バス分担率がトリップ原単位(D6)・外出率(D7)の band に収まる",
        contributes=("D6",),
        batch=BATCH_PULLED_FORWARD,
    ),
    PlanSpec(
        id="plan.road_works",
        content="道路工事・占用の期間と区間(占用許可=公示される計画)",
        validity=Validity(valid_from=0, valid_to=None),
        version=1,
        transaction_tick=0,
        revising_authority="道路管理者エージェント(層2)",
        norm_kind=NormKind.REGULATIVE,
        violability=Violability.ENFORCED,
        announcement_scope=AnnouncementScope(
            kinds=("住民", "通勤者", "来街者", "従業者"),
            cells=("占用区間を含むセル",),
            blocks=("B2",),
            channel_ids=("可視性",),
        ),
        compliance_field="road_works_schedule_compliance_rate",
        catalog_classes=("ダイヤ・営業時間・価格表(PlanSpec)", "道路工事・占用"),
        gate_condition="占用が可視物としてセル観測に載り、通行可能性(B2 近接路面)を変える",
        mechanism=False,
        sensitivity_test_id="AB-ROADWORK-FREQ",
        repayment_due="Phase 3(占用許可データの取得後)",
        batch=BATCH_PULLED_FORWARD,
    ),
)


# ================================================================== 細部(憲法5 の細部側の例)
DETAILS: Final[tuple[DetailDeclaration, ...]] = (
    DetailDeclaration(
        id="detail.shadow_grid",
        owner_process_id="daynight_solar",
        description="2.5m 格子の日陰フラグ(時間帯ごとの前計算版)",
        reaches=("内受容",),
        note="v1 教訓(精緻な屋内 SFM 座標を知覚が一度も読まなかった)の再発防止=届き先を型で持つ",
    ),
    DetailDeclaration(
        id="detail.noise_stage",
        owner_process_id="static_noise_field",
        description="法定境界に釘付けした騒音段階語彙(B4)",
        reaches=("聴覚: 静的場",),
        contributes=("D12′",),
    ),
    DetailDeclaration(
        id="detail.sku_stock",
        owner_process_id="shelf_stock_restock",
        description="店舗 POI 側の SKU 別棚在庫(個体 M1 には載せない)",
        reaches=("看板(a)",),
        contributes=("W1",),
    ),
)


# ================================================================== 関係(§2 の第1級4本)
RELATIONS: Final[tuple[Relation, ...]] = (
    Realizes(
        subject_id="rail_operation_static",
        subject_type=SubjectType.WORLD_PROCESS,
        plan_spec_id="plan.rail_timetable",
        executor=Executor.ENGINE_RULE,
        conf=0.6,
        coverage="ODPT 静的ダイヤ 1,810 本の全便",
        coverage_ratio=1.0,
        repayment_due="第2陣(運行連動)で乗務員・指令エージェントへ",
        note="フォールバックの正体=この executor の切り替え(§2)",
    ),
    Realizes(
        subject_id="store_opening",
        subject_type=SubjectType.WORLD_PROCESS,
        plan_spec_id="plan.opening_hours",
        executor=Executor.ENGINE_RULE,
        conf=0.5,
        coverage="bbox 内 POI の営業時間表による開閉",
        coverage_ratio=1.0,
        repayment_due="Phase 3(店主エージェントの開閉店行動)",
    ),
    Records(
        actual_log_id=ACTUAL_LOG_ID,
        target_id="rail_operation_static",
        target_type=SubjectType.WORLD_PROCESS,
        note="逸脱語彙 SCHEDULED/CANCELED/REPLACEMENT/SKIPPED/NO_DATA/DELAY",
    ),
    Records(
        actual_log_id=ACTUAL_LOG_ID,
        target_id="store_opening",
        target_type=SubjectType.WORLD_PROCESS,
    ),
    Records(
        actual_log_id=ACTUAL_LOG_ID,
        target_id="delivery_inbound",
        target_type=SubjectType.WORLD_PROCESS,
    ),
    Records(
        actual_log_id=ACTUAL_LOG_ID,
        target_id="waste_collection",
        target_type=SubjectType.WORLD_PROCESS,
    ),
    CountsAs(
        physical_fact="駅の制服を着て改札内にいる個体",
        institutional_fact="駅員(案内・誘導の権限を持つ)として扱われる",
        context="当該事業者の駅構内・営業時間内",
        note="§2 の例そのもの(SAI/Searle の構成的規則)",
    ),
    CountsAs(
        physical_fact="区の収集車が集積所の廃棄物を積載し bbox 外へ出る",
        institutional_fact="廃棄 sink への計上(物の保存則 §7.1)",
        context="渋谷区の収集日・可燃/不燃/資源の区分",
    ),
)

#: 前倒し分の関係(``build_registry(include_pulled_forward=True)`` のときだけ入る)。
PULLED_FORWARD_RELATIONS: Final[tuple[Relation, ...]] = (
    Realizes(
        subject_id="bus_taxi_operation",
        subject_type=SubjectType.WORLD_PROCESS,
        plan_spec_id="plan.bus_timetable",
        executor=Executor.LLM_AGENT,
        note="運転手(層2)が実行=フォールバック台帳に載らない",
    ),
    Realizes(
        subject_id="road_works_occupancy",
        subject_type=SubjectType.WORLD_PROCESS,
        plan_spec_id="plan.road_works",
        executor=Executor.LLM_AGENT,
    ),
    Records(
        actual_log_id=ACTUAL_LOG_ID,
        target_id="delivery_last_mile",
        target_type=SubjectType.WORLD_PROCESS,
    ),
    Records(
        actual_log_id=ACTUAL_LOG_ID,
        target_id="bus_taxi_operation",
        target_type=SubjectType.WORLD_PROCESS,
    ),
    Records(
        actual_log_id=ACTUAL_LOG_ID,
        target_id="public_service_dispatch",
        target_type=SubjectType.WORLD_PROCESS,
    ),
)


def growth_declarations(
    include_pulled_forward: bool = True,
) -> Mapping[str, GrowthDeclaration]:
    """宣言済み世界過程の成長宣言(名前 → 宣言)。``core.growth.check_growth`` に渡す。"""
    procs = DECLARATIONS + (PULLED_FORWARD_DECLARATIONS if include_pulled_forward else ())
    return {p.growth.name: p.growth for p in procs}


def build_registry(
    include_pulled_forward: bool = True, **registry_kwargs: object
) -> WorldRegistry:
    """第1陣(+前倒し分)を積んだ ``WorldRegistry`` を作る。

    Args:
        include_pulled_forward: §7.2「初回実装へ前倒し(第2陣分)」も積むか。
        **registry_kwargs: ``WorldRegistry`` へそのまま渡す(``catalog`` の差し替え等)。

    Returns:
        登録済みレジストリ(登録時に憲法5・カタログ・門前条件の検査を通っている)。
    """
    reg = WorldRegistry("v2-world-ledger:first-batch", **registry_kwargs)  # type: ignore[arg-type]
    for p in DECLARATIONS:
        reg.add_process(p)
    if include_pulled_forward:
        for p in PULLED_FORWARD_DECLARATIONS:
            reg.add_process(p)
    for s in PLAN_SPECS:
        if s.batch == BATCH_PULLED_FORWARD and not include_pulled_forward:
            continue
        reg.add_plan_spec(s)
    for d in DETAILS:
        reg.add_detail(d)
    for r in RELATIONS:
        reg.add_relation(r)
    if include_pulled_forward:
        for r in PULLED_FORWARD_RELATIONS:
            reg.add_relation(r)
    return reg
