"""world.processes.inputs — 入力の宣言の一覧(第340 段 2 の 7・回答 11-01 §1・§8)。

正典
- 回答 11-01 §1 の入力の宣言の型(A1-8・案 b): 変数の名と単位/出典と版と取得日/時間の細かさと補間/内部から
  影響を受けない一方向であること/較正か検証かの期間/揺らし方/**代理している未構築の層と、内生化の条件**。
- 回答 11-01 §8 の流すもの(訪日の母集団の数・景気と物価・区の政策の決定・運行の乱れ・イベントの開催情報・暦・
  通過交通・現実の看板の文)。指示書 段 2 の 7: 既存の入力 5 つ(気象・ダイヤ・暦・外界ノード・外の売上)に
  既存の文書から書く(出典の行を付ける)。新しい入力 7 つは欄だけ(値は段 0 の取得の後)。
- 納品=入力(回答 11-01 §10-1・指示書 段 2 の 6)は 13 本目として欄だけ置いた。

既存の文書に書いていない欄は「空欄(理由)」と書いた(推測で埋めない)。「代理している未構築の層」と「内生化の
条件」は routing §2-3 の表と回答 11-01 §1・§10-1 から写した(写せないものは空欄)。

本モジュールは**宣言だけ**(挙動を変えない)。気象・ダイヤ・通過交通・納品・催しの情報・区の政策の決定の宣言は
``first_batch`` の過程と PlanSpec の ``input_decl`` にも付けた(同じ物)。
"""

from __future__ import annotations

from typing import Final

from shibuya.world.processes.records import InputDecl

__all__ = [
    "WEATHER",
    "TIMETABLE",
    "CALENDAR",
    "EXTERNAL_NODES",
    "ROW_SALES",
    "EXISTING",
    "VISITOR_POPULATION",
    "ECONOMY_PRICES",
    "WARD_POLICY",
    "SERVICE_DISRUPTION",
    "EVENT_INFO",
    "THROUGH_TRAFFIC",
    "SIGNAGE_TEXT",
    "INBOUND_GOODS",
    "NEW",
    "INPUTS",
    "by_id",
]

_LICENSE = "docs/data-license-ledger.md"
_ROUTING = "docs/reference/decision-routing-2026-11-01.md §2-3"
_ANS = "docs/design/v2-answers-2026-11-01.md"
_FIELDS_ONLY_NOTE = "欄だけ(値は段 0 の取得の後=指示書 11-01 段 2 の 7)"

# ================================================================== 既存の入力 5 つ(filled)
WEATHER: Final[InputDecl] = InputDecl(
    id="input.weather",
    name="気象(再生日の時別の暑さ段と WBGT=W13 の行の気温・湿度・天候型から)",
    unit="暑さ段(WBGT 21/25/28/31 の段=公的指針)・WBGT[℃]",
    source="気象庁 過去の気象データ検索(etrn)東京 47662 の 10 分値(主)と時別値(欠けの補完)=W13",
    version="W13 の年間化(窓 2025-09-01〜2026-08-31)",
    fetched="2026-10-12(ライセンス台帳 その 13)",
    resolution="時別(1 日 24 の配列)。エンジンは 5 分ごと(THERMAL_STEP_MINUTES)に、その時の値を引く",
    interpolation="無し(時の値を次の 5 分の更新まで保つ=environment.py の _heat_now。〔検収 中-2〕first_batch の weather の"
    "更新規則の文「tick 単位に線形補間」はエンジンと違う=文の直しは registry_hash に効くので次の版上げ)",
    one_way="再生日の実測を読むだけ。世界の内部の状態は気象に返らない(D-W15 の実日ブートストラップ)",
    period="空欄(較正か検証かの期間の宣言なし。再生日は季節×曜日種別×天候型の層から引く)",
    perturbation="再生日を層の中から manifest の seed で乱択(D-W15・合成の乱数気象は不採用)",
    proxies_layer="大気(範囲の外の自然)",
    endogenize_when="内生化しない(人が関わらない自然=CLAUDE.md §3 の例外)",
    source_rows=(
        f"{_LICENSE} その 13(data/realworld/jma_etrn)",
        "src/shibuya/engine/processes/environment.py(D-W15・再生日・_heat_now=時別の暑さ段と WBGT を 5 分ごとに引く)",
        "src/shibuya/world/processes/first_batch.py(weather の update_rule)",
    ),
    world_process_id="weather",
)

TIMETABLE: Final[InputDecl] = InputDecl(
    id="input.timetable",
    name="鉄道のダイヤ(便ごとの発車・到着の時刻・種別・行き先)",
    unit="時刻(分)・便",
    source=(
        "各社の公式の時刻表(ユーザーが手で入手=data/user_timetables)・ODPT オープン枠の静的データ(銀座線・"
        "半蔵門線・副都心線)・ODPT チャレンジ枠(京王 井の頭線)=W12 の実ダイヤの表"
    ),
    version="W12 の 2-3b・2-3c の表(ODPT 静的データ版 1。銀座線は 9 月改正の版=世界の時点 2026-07-13 より後と宣言)",
    fetched="2026-10-12(公式の時刻表・チャレンジ枠)・2026-10-13(ODPT 静的データ版 1)",
    resolution="分(便ごと)",
    interpolation="無し(便の時刻そのもの)",
    one_way="ダイヤは外からの決定で、遅れは作らない(routing #107)。世界の内部はダイヤを書き換えない",
    period="空欄(較正か検証かの期間の宣言なし。運行情報 odpt_rt は検証専用=パターン台帳 §10 の注)",
    perturbation="空欄(運行の乱れは新しい入力 input.service_disruption で入れる=回答 11-01 §8)",
    proxies_layer="鉄道事業者の指令と乗務員(routing §2-3)",
    endogenize_when="乗務員と指令のエージェント(rail.py の返済=第 2 陣)ができたら(routing §2-3)",
    source_rows=(
        f"{_LICENSE} その 11・その 15・(2026-10-14/15 の W12 の行)",
        _ROUTING,
        "src/shibuya/world/processes/first_batch.py(plan.rail_timetable)",
    ),
    world_process_id="plan.rail_timetable",
)

CALENDAR: Final[InputDecl] = InputDecl(
    id="input.calendar",
    name="暦(日付・曜日・祝日・季節)",
    unit="日",
    source="内閣府「国民の祝日」CSV(syukujitsu.csv・1955/1/1〜2027/11/23)",
    version="md5 733fabb6b488794a0cd3d94df4b1f24a(Last-Modified 2026-02-02)",
    fetched="2026-10-03",
    resolution="日",
    interpolation="無し",
    one_way="社会の決まり(CLAUDE.md §3 の例外)。世界の内部から変わらない",
    period="空欄(較正と検証の区別の宣言なし)",
    perturbation="開始日(start_sim_datetime)を変える",
    proxies_layer="国の祝日の決定(範囲の外の制度)",
    carrier="engine/calendar.py の SimCalendar(暦の口・祝日の表)",
    endogenize_when="内生化しない(社会の決まり=CLAUDE.md §3 の例外)",
    source_rows=(
        f"{_LICENSE}(data/calendar/syukujitsu.csv の行)",
        "src/shibuya/engine/calendar.py",
        f"{_ANS} §10-2(6-8 祝日=暦を入力)",
    ),
)

EXTERNAL_NODES: Final[InputDecl] = InputDecl(
    id="input.external_nodes",
    name="方面別の外界ノード(鉄道 8・徒歩 1・道路 1)と境界の流量",
    unit="人(方面ごと・時間帯ごと)",
    source="W12 外界ノード(大都市交通センサスの駅別発着・乗換と ODPT の乗降人員)",
    version="空欄(W12 の構築の版=外界ノードの表の版を本欄に写していない)",
    fetched="空欄(取得物ごとに別=ライセンス台帳の各行)",
    resolution="空欄(W12 の構築の規則を本欄に写していない)",
    interpolation="空欄(同上)",
    one_way="方面ごとの節点と量は構築時の表(W12)で決まり、ランの中の状態(混雑・店・住人)はその表を書き換えない"
    "(域外の地理を持たない=境界経済設計書 §1.1)",
    period="較正=PT の目的別時間帯カーブ・大都市交通センサス・定期券/検証=KDDI の形 5 指標ほか(境界経済設計書 §1.4)",
    perturbation="空欄(宣言なし)",
    proxies_layer="範囲の外の都市圏(域外の地理と住人)",
    endogenize_when="範囲外の人の判断(輪の段)ができたら(routing §2-3 の訪日の母集団の行と同じ形)",
    carrier="W12 の外界ノードの表(world/assets.py の PROCESS_FILES の external_nodes・ext_node_line_idx)",
    source_rows=(
        "src/shibuya/build/field/w12_external_nodes.py",
        "docs/design/v2-boundary-economy-design.md §1.1・§1.4",
        _ROUTING,
    ),
)

ROW_SALES: Final[InputDecl] = InputDecl(
    id="input.row_sales",
    name="範囲の外の取引先からの売上(外界の口座からの faucet)",
    unit="円",
    source="外の決定(指示書 10-12 §4-11 EC5)。実体は economy/stage2.py の external_sales(1 店 1 日の額)",
    version="EXTERNAL_STORE_SALES_YEN=0(資料なし・腕だけ=いまは流れていない=stage2.py)",
    fetched="空欄(宣言なし)",
    resolution="日(1 店 1 日の額=stage2.py external_sales)",
    interpolation="無し(値が 0 の間は流れない)",
    one_way="外の決定として外界の口座から入れる(faucet)。内部の取引は外の売上を変えない(EC5)",
    period="空欄(宣言なし)",
    perturbation="空欄(宣言なし)",
    proxies_layer="範囲の外の経済(RoW)(routing §2-3 の景気と物価の行)",
    endogenize_when="境界の外の経済を内に入れる段(routing §2-3=空欄)",
    carrier="economy/stage2.py の external_sales(EXTERNAL_STORE_SALES_YEN)",
    source_rows=(
        "docs/design/v2-wallbounce-decisions-2026-10-12.md §4-11 EC5",
        "src/shibuya/economy/stage2.py(external_sales・EXTERNAL_STORE_SALES_YEN=0)",
        "src/shibuya/economy/accounts.py(EC5 の faucet)",
        _ROUTING,
    ),
)

EXISTING: Final[tuple[InputDecl, ...]] = (WEATHER, TIMETABLE, CALENDAR, EXTERNAL_NODES, ROW_SALES)


# ================================================================== 新しい入力 7 つ(fields_only)
def _new(iid: str, name: str, *, proxies: str = "", endo: str = "", period: str = "", wp: str = "",
         rows: tuple[str, ...] = (), note: str = "") -> InputDecl:
    return InputDecl(
        id=iid,
        name=name,
        period=period,
        proxies_layer=proxies,
        endogenize_when=endo,
        source_rows=rows or (f"{_ANS} §8",),
        status="fields_only",
        world_process_id=wp,
        note=(note + "・" if note else "") + _FIELDS_ONLY_NOTE,
    )


VISITOR_POPULATION: Final[InputDecl] = _new(
    "input.visitor_population", "訪日の母集団の数(来るか・どこへ・何を買うかは判断)",
    proxies="国の外の旅行者の行き先選び", endo="範囲外の人の判断(輪の段)ができたら",
    rows=(f"{_ANS} §8", _ROUTING))
ECONOMY_PRICES: Final[InputDecl] = _new(
    "input.economy_prices", "景気と物価(家計の予算の感覚・店主の値付けに情報として)",
    proxies="範囲の外の経済(RoW)", endo="「粗い東京圏の層」ができたら内生へ(回答 11-01 §1 の例)",
    rows=(f"{_ANS} §1・§8", _ROUTING))
WARD_POLICY: Final[InputDecl] = _new(
    "input.ward_policy", "区の政策の決定(介入の窓口と同じ形)",
    proxies="区役所と議会", endo="空欄(区の主体を置く段=routing §2-3 の空欄)",
    wp="press_official_release", rows=(f"{_ANS} §8・§10-2(6-7 報道=区の発信を入力)", _ROUTING))
SERVICE_DISRUPTION: Final[InputDecl] = _new(
    "input.service_disruption", "運行の乱れ(揺らし)",
    proxies="鉄道事業者の指令", endo="乗務員と指令のエージェント(rail.py の返済=第 2 陣)",
    rows=(f"{_ANS} §8", _ROUTING))
EVENT_INFO: Final[InputDecl] = _new(
    "input.event_info", "イベントの開催情報(外の人に届く情報)",
    proxies="主催者", endo="空欄(主催者のエージェント=routing §2-3 の空欄)",
    wp="large_event", rows=(f"{_ANS} §2・§8", _ROUTING))
THROUGH_TRAFFIC: Final[InputDecl] = _new(
    "input.through_traffic", "通過交通(範囲の外で発生する車の断面の量)",
    proxies="範囲の外の運転者", endo="域内の運転者の体は段 2 の後(回答 11-01 §10-1)",
    period="D5′ は較正から検証へ(回答 11-01 §8・§10-1)", wp="vehicle_cross_section",
    rows=(f"{_ANS} §8・§10-1",))
SIGNAGE_TEXT: Final[InputDecl] = _new(
    "input.signage_text", "現実の看板の文",
    proxies="店主(看板を書く主体)", endo="空欄(店主の体ができたら店主の L2=routing §6-7 の (b))",
    rows=(f"{_ANS} §8・§10-2(6-7 看板の文=入力)",))

NEW: Final[tuple[InputDecl, ...]] = (
    VISITOR_POPULATION, ECONOMY_PRICES, WARD_POLICY, SERVICE_DISRUPTION, EVENT_INFO, THROUGH_TRAFFIC, SIGNAGE_TEXT,
)

#: 納品=入力(回答 11-01 §10-1・指示書 段 2 の 6)。量は錨から外す。
INBOUND_GOODS: Final[InputDecl] = _new(
    "input.inbound_goods", "納品(境界の外から来る物の流れ・配送員は外から入る人)",
    proxies="範囲の外の卸と配送", endo="発注=店主の口(A2)ができたら本人の判断へ(回答 11-01 §10-1)",
    wp="delivery_inbound", rows=(f"{_ANS} §10-1", "docs/design/prompt-2026-11-01.md 段 2 の 6"),
    note="納品の量は錨から外す")

#: 全部(計器の並びの順)。
INPUTS: Final[tuple[InputDecl, ...]] = EXISTING + NEW + (INBOUND_GOODS,)


def by_id() -> dict[str, InputDecl]:
    out = {d.id: d for d in INPUTS}
    if len(out) != len(INPUTS):
        raise ValueError("input の id が重なる")
    return out
