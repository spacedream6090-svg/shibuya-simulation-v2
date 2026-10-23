"""W12 外界ノード(§1 W12・D-W14・境界経済設計書 §1 U10)。

**役割の限定(D-W14)**: 本段階の集計表は**エージェントの来街を抽選する装置ではない**。
来街は各 persistent_id の週次スケジュール表(T0)→T1差分→T2 LLM で決まる。ここで作る重みの
用途は ①W16/W17 の**生成入力** ②**較正** ③**検証**(コードン流量)の3つに限る。

出力
  - ``w12_external_nodes.parquet``: 方面別ノード 10(鉄道8・徒歩1・道路1)。
  - ``w12_generation_weights.parquet``: 方面×目的×手段×時刻の重み(用途は上記3つのみ)。
  - ``w12_timetables.parquet``: 路線×方向×平日/土休の発時刻。**1.2.0(第 2 期 2-3b)から全 8 線が実ダイヤ**
    (JR・東急=ユーザーが入手した公式の時刻表の読み取り・京王=ODPT チャレンジ枠・銀座線=ODPT オープン枠の
    静的データ版 1〈9 月改正=世界の時点より後の版〉・半蔵門線/副都心線=今の 7 月の取得)。読み口と方面の
    写像の表は :mod:`shibuya.build.field.w12_real_timetables`。等間隔の推定は実データの無い線が出たときだけ
    使う(今は 0 線=ゲート ``equal_interval_lines_remaining``)。〔第 4 期 4-3 版上げ 3 回目の第 2 部〕旧値(1.1.0=メトロ
    3 線=実・他=等間隔 expedient)を作る切替口 ``USE_REAL_TIMETABLES=False`` は消した(再現は安定版のタグ)。
  - ``w12_timetable_versions.json``(1.2.0・実ダイヤのときだけ): 線ごとの版の宣言(世界の時点との前後)と
    入力の md5。``source`` の列とは別に置く。〔1.3.0〕節 ``rail_events`` に発着の表の要約と直通のまとめの規則(conf つき)。
  - ``w12_rail_events.parquet``(1.3.0・実ダイヤのときだけ): 渋谷の発着の表(発車の行=``w12_timetables`` の行と 1 対 1+
    到着の行・直通で結んだ列車の鍵・数える印)。:mod:`shibuya.build.field.w12_rail_events`。**エンジンは読まない**
    (``w12_timetables.parquet`` は 1.2.0 とバイト一致=活性化しても結果は変わらない)。

版の注
  - 1.1.0(第330 B3): 等間隔ダイヤの丸め。
  - 1.2.0(第 2 期 2-3b・回答 10-13 の 7・10-13b §2): 等間隔の 5 線(山手線・埼京線〈湘南新宿ラインを畳む〉・
    東横線・田園都市線・井の頭線)を実ダイヤに置き換え、銀座線を 9 月改正の版に。オフピーク比・ピーク本数の
    派生は実ダイヤ(全線)から計算し直す(等間隔の線が残ったときだけ使う)。方面ノード・生成の重み・
    時間帯配分(``time_dist_12``)・流量(``station_flow_12``)は変えない。
  - 1.3.0(第 2 期 2-3c・計画 2-3c の行): 渋谷の到着(銀座線・半蔵門線・副都心線=ODPT オープン枠の列車時刻表・
    井の頭線=チャレンジ枠の列車時刻表)と直通の二重計上のまとめ(東急の上り=地下鉄の行と同じ列車・下りの直通の結び・
    成田エクスプレス ⊂ 湘南新宿ライン・相鉄線直通)を別の表 ``w12_rail_events.parquet`` に。発車の表は変えない。

流量の作り方(D-W14)
  - 鉄道: 大都市交通センサス第12回(2015)駅別発着表(ticket=合計)の **降車 − 当該路線発の改札内乗換**
    = 街への流入、**乗車 − 当該路線着の改札内乗換** = 街からの流出。
    乗換表は「乗換行列と乗換比率にだけ使う」という一次資料の注意書きに従い、行列としてのみ使う
    (``gate_entry``/``gate_exit`` の絶対水準は使わない)。
  - 徒歩・道路: 第6回東京都市圏PT 表d-1(2018)の 0241 着トリップから**域内々を差し引いた**
    手段別トリップ(徒歩・自転車 → 徒歩ゲート、自動車・バス・２輪車 → 道路ゲート)。
  - ODPT PassengerSurvey(最新年度)は**単位差**(JR=乗車のみ・他=乗降)を列に持たせて併記する。

expedient
  - 時間帯配分=time_dist_12(2015)を 2021/2018 の総量に当てる(時点混合)。
  - time_dist_12 の ``～6時台`` を 5・6時へ、``0時台～`` を 0・1時へ等分。
  - 目的×手段の構成は全ノード共通(方面別の目的構成は未取得)。
  - (1.1.0 まで・切替口 False のとき)JR・東急・京王=等間隔ダイヤ(F10)。ピーク本数は国交省 資料3
    (**朝ピークのみ**=夕ピークは朝と同数に置く)、オフピーク比は**平日/土休それぞれの**メトロ実ダイヤから、
    ダイヤ端はメトロ平日ダイヤから導く。方向別の内訳が非公開なので上下同数と仮定。
  - (1.1.0 まで)湘南新宿ラインのピーク本数は資料3に行が無い=**ダイヤ生成の対象外**(空欄)。
  - (1.2.0)実ダイヤの宣言(方面の写像・湘南新宿ラインの畳み・土休の臨時の特急を外す・版の推測)は
    :mod:`shibuya.build.field.w12_real_timetables` の docstring とヘッダの expedients。
"""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from fractions import Fraction
from typing import Any, Sequence

import numpy as np

from . import common as C
from . import w12_rail_events as RE
from . import w12_real_timetables as RT
from shibuya.core.time_consts import HOURS_PER_DAY, MINUTES_PER_DAY, MINUTES_PER_HOUR

STAGE = "W12"
#: 1.1.0(第330 B3): 等間隔ダイヤの丸めを「小数で積み切り捨て」に直した(時刻表の行が変わる)。
#: 1.2.0(第 2 期 2-3b): 等間隔の 5 線を実ダイヤに置き換え・銀座線を 9 月改正の版に(時刻表の行が変わる)。
#: 1.3.0(第 2 期 2-3c): 渋谷の発着の表 ``w12_rail_events.parquet`` を足す(時刻表の行は変えない=バイト一致)。
STAGE_VERSION = "1.3.0"

#: 〔2-3b〕実ダイヤのとき ODPT の駅の時刻表(7 月の取得)から読む線(銀座線は 9 月改正の列車時刻表から)。
METRO_LINES_KEPT_WITH_REAL: tuple[str, ...] = ("半蔵門線", "副都心線")
#: 〔2-3b〕実ダイヤのときの版の表のファイル名(資産の隣)。
VERSIONS_FILE = "w12_timetable_versions.json"

#: 〔2-3b・検収 H1〕実ダイヤの時刻表の expedient(モジュールの表=つなぎの台帳の走査器 ``engine/bridging/scan.py`` の
#: 形 B が要素を 1 つずつ数える。台帳 ``docs/design/bridging-ledger.json`` の ``EX-build.field.w12_external_nodes-*`` の行)。
#: 文を書き換えると台帳の行の同定が変わる(試験 ``tests/engine/bridging`` が落ちて知らせる)。
REAL_TIMETABLE_EXPEDIENTS: tuple[str, ...] = (
    "実ダイヤ(2-3b)は渋谷の発車の表だけ(到着の表は使わない=着く体も発車の便から降りる・終点の到着は 2-3c)",
    "方面の上り/下りの写像: JR 山手線 内回り=上り・外回り=下り(線路名称の品川起点による推測・未リサーチ)・"
    "相鉄線直通の表は題名の『下り』ではなく向き(南行)で上りに",
    "湘南新宿ラインの便は埼京線に畳む(エンジンの方面ノード E2 と同じ畳み方・線別の定員表に行が無い)",
    "土休の ◆ 特急 4 本(踊り子・サフィール踊り子)は ODPT に無いので臨時と見て外す(推測)",
    "JR の版=2026-03-14 改正と同じと推測(頁は JR 時刻表 2026 年 10 月号に基づく・改正日の記載なし)",
    "銀座線=世界の時点(2026-07-13)より後の版(2026-09-19 改正・回答 10-13b §2 のユーザー決定)",
    "井の頭線の版=ODPT チャレンジ枠の dct:issued 2025-03-15/17 が世界の時点に効いていたと推測(改正日の欄は空欄)",
    "東横線・田園都市線の上り=直通の副都心線・半蔵門線と同じ列車(W12 では線ごとに 1 回ずつ現れる=直通の二重は 2-3c)",
)
#: 〔2-3c〕発着の表(``w12_rail_events``)の宣言(モジュールの表=走査器の形 B・台帳の ``EX-build.field.w12_external_nodes-*``)。
#: 規則 ``down_through``(``w12_rail_events.RULE_CONF`` で conf=expedient)の宣言の文。
RAIL_EVENT_EXPEDIENTS: tuple[str, ...] = (
    "下りの直通の結び(2-3c): 地下鉄の渋谷着と東急の下りの渋谷発(当駅始発の印の無い便)を同じ暦・同じ行き先ごとに"
    "時刻の順に 1 対 1 で結ぶ=同じ行き先の便は渋谷で追い越さないと見る(推測・東急の表に列車番号が無い)",
)
#: 〔2-3b・検収 H1〕等間隔ダイヤの道の宣言(切替口 False=1.1.0 の時刻表の再現と、実データの無い線だけで足す)。
#: 1.1.0 の 5 行(台帳 W12#4〜#8=2-3b で removed)をこの 1 行にまとめた。動的な中身(残る線の名・夕ピークの規則)は
#: notes(``equal_interval_lines``・``equal_interval_pm_rule``・``pm_peak_note``)に書く。
EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS: tuple[str, ...] = (
    "等間隔ダイヤ(F10)の道=実データの無い線だけ"
    "(2-3b の既定では 0 線)。上下同数・ピーク本数は資料3(山手線は 16-20 本/h の中央 18・夕は朝と同数か引数の表)・"
    "オフピーク比と初終発は切替口 False でメトロ実ダイヤ(初終発は平日)・残る線では実ダイヤ全線(平日/土休それぞれ)から",
)

STATION_FLOW = ("realworld", "transport_census", "station_flow_12.json")
TIME_DIST = ("realworld", "transport_census", "time_dist_12.json")
TRANSFER = ("realworld", "transport_census", "transfer_12.json")
PASSENGER_SURVEY = ("realworld", "odpt_passenger_survey", "shibuya.json")
PT_CORE = ("..", "docs", "bench", "pt_shibuya", "pt6_summary_core0241.json")

METRO_TIMETABLES: tuple[tuple[str, str], ...] = (
    ("銀座線", "station_timetable_metro_ginza.json"),
    ("半蔵門線", "station_timetable_metro_hanzomon.json"),
    ("副都心線", "station_timetable_metro_fukutoshin.json"),
)


def metro_timetables_in_use() -> tuple[tuple[str, str], ...]:
    """W12 が実際に読む ODPT の駅の時刻表(線, ファイル名)=半蔵門線・副都心線だけ(銀座線は実ダイヤの読み口)。"""
    return tuple((ln, f) for ln, f in METRO_TIMETABLES if ln in METRO_LINES_KEPT_WITH_REAL)


#: 方面別外界ノード(U10: 8-10ノード)。lines はセンサス駅別発着表の路線名。
NODE_DEFS: tuple[dict[str, Any], ...] = (
    {
        "node_id": "ext_rail_tokyu_denentoshi",
        "through_running_with": "半蔵門線",
        "kind": "rail",
        "operator": "東急電鉄",
        "station": "渋谷",
        "lines": ("田園都市線",),
        "direction_label": "三軒茶屋・二子玉川・中央林間方面",
    },
    {
        "node_id": "ext_rail_tokyu_toyoko",
        "through_running_with": "副都心線",
        "kind": "rail",
        "operator": "東急電鉄",
        "station": "渋谷",
        "lines": ("東横線",),
        "direction_label": "中目黒・自由が丘・横浜方面",
    },
    {
        "node_id": "ext_rail_keio_inokashira",
        "through_running_with": "",
        "kind": "rail",
        "operator": "京王電鉄",
        "station": "渋谷",
        "lines": ("井の頭線",),
        "direction_label": "下北沢・吉祥寺方面",
    },
    {
        "node_id": "ext_rail_jr_yamanote",
        "through_running_with": "",
        "kind": "rail",
        "operator": "JR東日本",
        "station": "渋谷",
        "lines": ("山手線",),
        "direction_label": "新宿・池袋/恵比寿・品川方面",
    },
    {
        "node_id": "ext_rail_jr_saikyo_shonan",
        "through_running_with": "",
        "kind": "rail",
        "operator": "JR東日本",
        "station": "渋谷",
        "lines": ("埼京線", "湘南新宿ライン"),
        "direction_label": "新宿・大宮/大崎・横浜方面",
    },
    {
        "node_id": "ext_rail_metro_hanzomon",
        "through_running_with": "田園都市線",
        "kind": "rail",
        "operator": "東京メトロ",
        "station": "渋谷",
        "lines": ("半蔵門線",),
        "direction_label": "表参道・大手町・押上方面",
    },
    {
        "node_id": "ext_rail_metro_fukutoshin",
        "through_running_with": "東横線",
        "kind": "rail",
        "operator": "東京メトロ",
        "station": "渋谷",
        "lines": ("副都心線",),
        "direction_label": "新宿三丁目・池袋・和光市方面",
    },
    {
        "node_id": "ext_rail_metro_ginza",
        "through_running_with": "",
        "kind": "rail",
        "operator": "東京メトロ",
        "station": "渋谷",
        "lines": ("銀座線",),
        "direction_label": "表参道・赤坂見附・浅草方面",
    },
    {
        "node_id": "ext_walk_gate",
        "through_running_with": "",
        "kind": "walk",
        "operator": "",
        "station": "",
        "lines": (),
        "direction_label": "徒歩・自転車(区界のゲートノード)",
    },
    {
        "node_id": "ext_road_gate",
        "through_running_with": "",
        "kind": "road",
        "operator": "",
        "station": "",
        "lines": (),
        "direction_label": "自動車・バス・二輪(区界のゲートノード)",
    },
)

#: ノード種別 → 許す代表交通手段(PT 表d-1 の手段語彙)。
MODES_BY_KIND: dict[str, tuple[str, ...]] = {
    "rail": ("鉄道",),
    "walk": ("徒歩", "自転車"),
    "road": ("自動車", "バス", "２輪車"),
}

#: PT の目的(8) → 大都市交通センサス time_dist_12 の目的(5+合計)。
PT_PURPOSE_TO_TIMEDIST: dict[str, str] = {
    "自宅－勤務": "通勤",
    "自宅－通学": "通学",
    "自宅－業務": "業務",
    "自宅－私事": "私事",
    "帰宅": "帰宅",
    "勤務・業務": "業務",
    "私事": "私事",
    "不明": "合計",
}

#: 国交省 令和6年度 資料3「最混雑区間における混雑率」の**ピーク1時間本数**(F10/D-W14)。
#: 資料3が載せるのは**朝ピーク**(最混雑1時間)だけで、夕ピークの本数はどの入手済み資料にも
#: 無い。よって夕ピーク=朝ピークと**置く**(expedient・``PM_PEAK_ASSUMED_EQUAL_TO_AM``)。
#: 湘南新宿ラインは資料3に行が無い=空欄(ダイヤ生成の対象外)。
PEAK_TRAINS_PER_HOUR: dict[str, int | None] = {
    "田園都市線": 27,
    "東横線": 24,
    "井の頭線": 27,
    "山手線": 18,  # 資料3 は 16-20 本/h の幅 → 中央値 18(expedient)
    "埼京線": 19,
    "湘南新宿ライン": None,
}
#: 等間隔ダイヤのピーク時間帯(朝・夕)。
PEAK_HOURS_AM: tuple[int, ...] = (7, 8, 9)
PEAK_HOURS_PM: tuple[int, ...] = (17, 18, 19)
#: D-W14 の本数表は朝ピークのみ=夕ピーク本数を朝と同じに置く(expedient・宣言)。
PM_PEAK_ASSUMED_EQUAL_TO_AM = True
#: 〔改訂(第330)・答え 10-12b 1-2〕夕ピーク(17-19時)の本数の表(線 → 本/時)。
#: ``PM_PEAK_ASSUMED_EQUAL_TO_AM`` が False のときだけ読む。**既定の表は無い**(None)=
#: 夕ピークの本数はどの入手済み資料にも無い。他社の比(例 メトロの夕/朝 0.79)を当てはめて
#: 埋めない(他社のダイヤの推定になる)。False で表が None か、表に無い線があれば ValueError
#: (False が黙って夕=朝に戻る=第330 B2 で直した欠陥の再発を防ぐ)。本当の直しは実際の時刻表(答え §2)。
PM_PEAK_TRAINS_PER_HOUR: dict[str, int] | None = None


def pm_peak_for_line(
    line: str,
    assumed_equal_to_am: bool,
    pm_table: dict[str, int] | None,
) -> int | None:
    """線ごとに :func:`equal_interval_departures` へ渡す ``peak_tph_pm``。

    True(既定)= None(夕=朝)。False = 表の値(表が無い・線が無いときは ValueError)。
    """
    if assumed_equal_to_am:
        return None
    if pm_table is None:
        raise ValueError(
            "PM_PEAK_ASSUMED_EQUAL_TO_AM=False には夕ピークの本数の表 PM_PEAK_TRAINS_PER_HOUR が要る"
            "(既定の表は無い・他社の比で埋めない)"
        )
    if line not in pm_table:
        raise ValueError(f"夕ピークの本数の表に {line} の行が無い(黙って夕=朝にしない)")
    return int(pm_table[line])
#: オフピーク比を測る時間帯(昼)。
OFFPEAK_HOURS: tuple[int, ...] = (10, 11, 12, 13, 14, 15)


def _pt_bin_to_hours(label: str) -> list[int]:
    """time_dist_12 の時間帯ラベル → 時刻(複数なら等分)。"""
    if label.startswith("～"):
        return [5, 6]  # 始発〜6時台(expedient)
    if label.endswith("時台～") or label.startswith("0時台～"):
        return [0, 1]  # 0時台以降(expedient)
    return [int(label.replace("時台", ""))]


def hour_shares(time_dist_rows: Sequence[dict], flow: str) -> dict[str, list[float]]:
    """time_dist_12 → 目的 → 24 時間の構成比(合計 1)。"""
    out: dict[str, list[float]] = {}
    by_purpose: dict[str, list[dict]] = defaultdict(list)
    for r in time_dist_rows:
        if r["flow"] == flow:
            by_purpose[r["purpose"]].append(r)
    for purpose, rows in by_purpose.items():
        vec = [0.0] * HOURS_PER_DAY
        for r in rows:
            hours = _pt_bin_to_hours(r["bin"])
            for h in hours:
                vec[h] += float(r["share"]) / len(hours)
        total = sum(vec)
        out[purpose] = [v / total for v in vec] if total > 0 else vec
    return out


def rail_flows(
    flow_rows: Sequence[dict], transfer_rows: Sequence[dict]
) -> tuple[dict[str, dict[str, float]], dict[str, float], dict[str, float]]:
    """駅別発着表+乗換行列 → 路線別の (乗車/降車, 乗換流出, 乗換流入)。"""
    board: dict[str, float] = defaultdict(float)
    alight: dict[str, float] = defaultdict(float)
    for r in flow_rows:
        if r["ticket"] != "合計":
            continue
        if r["measure"] == "乗車":
            board[r["line"]] += float(r["value"])
        elif r["measure"] == "降車":
            alight[r["line"]] += float(r["value"])
    tr_out: dict[str, float] = defaultdict(float)  # その路線で着いて他線へ乗換
    tr_in: dict[str, float] = defaultdict(float)  # 他線から乗換えてその路線に乗る
    for r in transfer_rows:
        if r["kind"] != "transfer":
            continue
        tr_out[r["from_line"]] += float(r["daily"])
        tr_in[r["to_line"]] += float(r["daily"])
    lines = {"board": dict(board), "alight": dict(alight)}
    return lines, dict(tr_out), dict(tr_in)


def parse_metro_timetable(doc: dict) -> list[dict[str, Any]]:
    """ODPT StationTimetable JSON → 発時刻行。"""
    rows: list[dict[str, Any]] = []
    for table in doc.get("data", []):
        calendar = str(table.get("odpt:calendar", "")).split(":")[-1]
        direction = str(table.get("odpt:railDirection", "")).split(":")[-1]
        railway = str(table.get("odpt:railway", "")).split(":")[-1]
        for obj in table.get("odpt:stationTimetableObject", []):
            t = obj.get("odpt:departureTime")
            if not t:
                continue
            rows.append(
                {
                    "railway": railway,
                    "calendar": calendar,
                    "direction": direction,
                    "departure": str(t),
                }
            )
    return rows


#: 運行日(サービスデー)の切れ目 [分]。これ未満の時刻は前日の続き=+1440 として扱う。
SERVICE_DAY_CUT_MIN = 240  # 04:00


def _minute(hhmm: str) -> int:
    """``HH:MM`` → **運行日**の分(00:02 の終電は 24:02 = 1442 になる)。"""
    h, m = hhmm.split(":")
    v = int(h) * MINUTES_PER_HOUR + int(m)
    return v + MINUTES_PER_DAY if v < SERVICE_DAY_CUT_MIN else v


def equal_interval_departures(
    peak_tph: int,
    offpeak_ratio: float,
    first_min: int,
    last_min: int,
    peak_tph_pm: int | None = None,
) -> list[str]:
    """等間隔ダイヤ(expedient)。朝ピーク=``peak_tph``・夕ピーク=``peak_tph_pm``・他は比を掛ける。

    ``peak_tph_pm=None`` は「夕ピークの本数が資料に無いので朝と同じに置く」
    (D-W14・``PM_PEAK_ASSUMED_EQUAL_TO_AM``)。
    """
    if peak_tph <= 0:
        return []
    pm = peak_tph if peak_tph_pm is None else peak_tph_pm
    out: list[str] = []
    # 〔改訂(第330)・答え 10-12b 1-1 (i)〕時刻を**小数で積み**、出す分だけ切り捨てる。旧は間隔を
    # 整数分に丸めて積んでいた(`round(60/tph)`=偶数への丸めで 24 本/時が 2.5→2 分=30 本/時)。
    # 有理数で積むので浮動小数の誤差で 1 時間の本数がずれない(間隔が一定の時間帯は本数=宣言)。
    t = Fraction(first_min)
    while t <= last_min:
        minute = math.floor(t)
        out.append(C.min_to_hhmm(minute))
        hour = (minute // MINUTES_PER_HOUR) % HOURS_PER_DAY
        if hour in PEAK_HOURS_AM:
            tph = float(peak_tph)
        elif hour in PEAK_HOURS_PM:
            tph = float(pm)
        else:
            tph = peak_tph * offpeak_ratio
        tph = max(tph, 1.0)
        t += Fraction(MINUTES_PER_HOUR) / Fraction(tph)
    return out


def offpeak_ratio_from(rows: Sequence[dict[str, Any]]) -> tuple[float, int, float]:
    """メトロ実ダイヤの発時刻行 → (オフピーク比, 朝ピーク本数, 昼平均本数)。

    比 = 昼(10-15時)の1時間あたり平均本数 ÷ 朝ピーク(7-9時)の最大本数。
    行が無い/ピークが 0 のときは比 1.0(=一様)を返す。
    """
    if not rows:
        return 1.0, 0, 0.0
    per_hour: Counter = Counter(_minute(r["departure"]) // MINUTES_PER_HOUR for r in rows)
    peak = max((per_hour[h] for h in PEAK_HOURS_AM), default=0)
    off = [per_hour[h] for h in OFFPEAK_HOURS]
    off_mean = sum(off) / len(off) if off else 0.0
    return ((off_mean / peak) if peak > 0 else 1.0), peak, off_mean


def run(ctx: C.Ctx) -> C.StageResult:
    paths = [
        ctx.path(*STATION_FLOW),
        ctx.path(*TIME_DIST),
        ctx.path(*TRANSFER),
        ctx.path(*PASSENGER_SURVEY),
    ]
    pt_path = ctx.data.joinpath(*PT_CORE).resolve()
    metro_in_use = metro_timetables_in_use()
    metro_paths = [ctx.path("odpt", f) for _line, f in metro_in_use]
    # 〔2-3b〕実ダイヤの入力
    real_paths = [ctx.data.joinpath(*rel.split("/")) for rel in RT.all_input_rel_paths()]
    for p in [*paths, pt_path, *metro_paths, *real_paths]:
        if not p.exists():
            raise FileNotFoundError(f"W12 入力が無い: {p}")
    exits_p = ctx.out / "w11_station_exits.parquet"
    nodes_p = ctx.out / "w1_nodes.parquet"
    edges_p = ctx.out / "w1_edges.parquet"
    for p in (exits_p, nodes_p, edges_p):
        if not p.exists():
            raise FileNotFoundError(f"W12 は W1/W11 の出力を必要とする: {p}")

    flow_doc = C.load_json(paths[0])
    time_doc = C.load_json(paths[1])
    transfer_doc = C.load_json(paths[2])
    survey_doc = C.load_json(paths[3])
    pt = C.load_json(pt_path)

    lines, tr_out, tr_in = rail_flows(flow_doc["data"], transfer_doc["data"])
    hour_share_alight = hour_shares(time_doc["data"], "降車")
    hour_share_board = hour_shares(time_doc["data"], "乗車")

    survey_by_line: dict[str, dict[str, Any]] = {}
    line_of_railway = {
        "DenEnToshi": "田園都市線",
        "Toyoko": "東横線",
        "Inokashira": "井の頭線",
        "Yamanote": "山手線",
        "SaikyoKawagoe": "埼京線",
        "ShonanShinjuku": "湘南新宿ライン",
        "Hanzomon": "半蔵門線",
        "Fukutoshin": "副都心線",
        "Ginza": "銀座線",
    }
    for rec in survey_doc["data"]:
        for rw in rec.get("railways", []):
            key = line_of_railway.get(rw.split(".")[-1])
            if key:
                survey_by_line[key] = {
                    "value": float(rec["latest_value"]),
                    "year": int(rec["latest_year"]),
                    "measure": rec["measure"],
                    "operator": rec["operator_label"],
                    "shared_record": len(rec.get("railways", [])) > 1,
                }

    # --- PT: 手段別の外来トリップ(域内々を控除)---
    arrive = pt["arrive_purpose_x_mode"]
    internal = pt["arrive_internal(発着とも渋谷)"]
    mode_external: dict[str, float] = {}
    for mode in ("鉄道", "バス", "自動車", "２輪車", "自転車", "徒歩"):
        mode_external[mode] = max(float(arrive["計"][mode]) - float(internal[mode]), 0.0)

    # --- 出口・ゲートの束縛セル ---
    exits = C.read_parquet_columns(exits_p, ["exit_id", "station_title", "place_id"])
    exits_by_station: dict[str, list[str]] = defaultdict(list)
    for st, pid in zip(exits["station_title"], exits["place_id"]):
        exits_by_station[st].append(pid)
    nd = C.read_parquet_columns(nodes_p, ["node_id", "is_gateway", "x", "y", "band"])
    ed = C.read_parquet_columns(edges_p, ["u_id", "v_id", "klass"])
    klass_of_node: dict[str, set[str]] = defaultdict(set)
    for u, v, k in zip(ed["u_id"], ed["v_id"], ed["klass"]):
        klass_of_node[u].add(k)
        klass_of_node[v].add(k)
    CAR = {"primary", "secondary", "tertiary", "residential", "unclassified", "service", "living_street"}
    gate_cells_walk: list[str] = []
    gate_cells_road: list[str] = []
    n_gate = 0
    for nid, gw, x, y, band in zip(nd["node_id"], nd["is_gateway"], nd["x"], nd["y"], nd["band"]):
        if not gw:
            continue
        n_gate += 1
        pid = C.place_id(*C.grid_ij(float(x), float(y)), band)
        gate_cells_walk.append(pid)
        if klass_of_node[nid] & CAR:
            gate_cells_road.append(pid)

    # --- ノード行 ---
    rows: list[dict[str, Any]] = []
    for spec in NODE_DEFS:
        if spec["kind"] == "rail":
            inflow = sum(
                lines["alight"].get(ln, 0.0) - tr_out.get(ln, 0.0) for ln in spec["lines"]
            )
            outflow = sum(
                lines["board"].get(ln, 0.0) - tr_in.get(ln, 0.0) for ln in spec["lines"]
            )
            cells = sorted(set(exits_by_station.get(spec["station"], [])))
            survey = [survey_by_line[ln] for ln in spec["lines"] if ln in survey_by_line]
            survey_value = sum(s["value"] for s in survey) if survey else 0.0
            survey_measure = "/".join(sorted({s["measure"] for s in survey})) if survey else ""
            survey_year = max((s["year"] for s in survey), default=0)
            flow_src = "transport_census_12_2015 (alight - transfer_out)"
        elif spec["kind"] == "walk":
            inflow = mode_external["徒歩"] + mode_external["自転車"]
            outflow = float(pt["depart_home_by_mode"]["徒歩"]) + float(
                pt["depart_home_by_mode"]["自転車"]
            )
            cells = sorted(set(gate_cells_walk))
            survey_value, survey_measure, survey_year = 0.0, "", 0
            flow_src = "PT6 d-1 2018 (0241 arrivals - internal)"
        else:
            inflow = mode_external["自動車"] + mode_external["バス"] + mode_external["２輪車"]
            outflow = (
                float(pt["depart_home_by_mode"]["自動車"])
                + float(pt["depart_home_by_mode"]["バス"])
                + float(pt["depart_home_by_mode"]["２輪車"])
            )
            cells = sorted(set(gate_cells_road))
            survey_value, survey_measure, survey_year = 0.0, "", 0
            flow_src = "PT6 d-1 2018 (0241 arrivals - internal)"
        rows.append(
            {
                **spec,
                "daily_inflow": round(inflow, 1),
                "daily_outflow": round(outflow, 1),
                "flow_src": flow_src,
                "flow_unit": "persons_per_weekday",
                "odpt_survey_value": round(survey_value, 1),
                "odpt_survey_measure": survey_measure,
                "odpt_survey_year": survey_year,
                "attached_place_ids": cells,
            }
        )

    total_inflow = sum(r["daily_inflow"] for r in rows)
    rail_inflow = sum(r["daily_inflow"] for r in rows if r["kind"] == "rail")

    node_cols = {
        "node_id": [r["node_id"] for r in rows],
        "kind": [r["kind"] for r in rows],
        "operator": [r["operator"] for r in rows],
        "station": [r["station"] for r in rows],
        "lines": [C.json_text(list(r["lines"])) for r in rows],
        "direction_label": [r["direction_label"] for r in rows],
        "through_running_with": [r["through_running_with"] for r in rows],
        "modes": [C.json_text(list(MODES_BY_KIND[r["kind"]])) for r in rows],
        "daily_inflow": np.array([r["daily_inflow"] for r in rows], dtype=np.float64),
        "daily_outflow": np.array([r["daily_outflow"] for r in rows], dtype=np.float64),
        "flow_unit": [r["flow_unit"] for r in rows],
        "flow_src": [r["flow_src"] for r in rows],
        "odpt_survey_value": np.array([r["odpt_survey_value"] for r in rows], dtype=np.float64),
        "odpt_survey_measure": [r["odpt_survey_measure"] for r in rows],
        "odpt_survey_year": np.array([r["odpt_survey_year"] for r in rows], dtype=np.int32),
        "n_attached_cells": np.array([len(r["attached_place_ids"]) for r in rows], dtype=np.int32),
        "attached_place_ids": [C.json_text(r["attached_place_ids"]) for r in rows],
    }

    # --- 生成用重み(方面×目的×手段×時刻)---
    node_share = {
        r["node_id"]: (r["daily_inflow"] / total_inflow if total_inflow > 0 else 0.0) for r in rows
    }
    purposes = [p for p in arrive if p != "計"]
    w_node: list[str] = []
    w_purpose: list[str] = []
    w_mode: list[str] = []
    w_hour: list[int] = []
    w_val: list[float] = []
    for r in rows:
        modes = MODES_BY_KIND[r["kind"]]
        mode_tot = sum(float(arrive["計"][m]) for m in modes)
        if mode_tot <= 0 or node_share[r["node_id"]] <= 0:
            continue
        for mode in modes:
            mshare = float(arrive["計"][mode]) / mode_tot
            ptot = sum(float(arrive[p][mode]) for p in purposes)
            if ptot <= 0:
                continue
            for purpose in purposes:
                pshare = float(arrive[purpose][mode]) / ptot
                if pshare <= 0:
                    continue
                hvec = hour_share_alight[PT_PURPOSE_TO_TIMEDIST[purpose]]
                for hour, hs in enumerate(hvec):
                    if hs <= 0:
                        continue
                    w_node.append(r["node_id"])
                    w_purpose.append(purpose)
                    w_mode.append(mode)
                    w_hour.append(hour)
                    w_val.append(node_share[r["node_id"]] * mshare * pshare * hs)
    w_sum = float(sum(w_val))
    weights = np.array(w_val, dtype=np.float64) / (w_sum if w_sum > 0 else 1.0)

    # --- ダイヤ ---
    tt_line: list[str] = []
    tt_operator: list[str] = []
    tt_direction: list[str] = []
    tt_calendar: list[str] = []
    tt_dep: list[str] = []
    tt_src: list[str] = []
    metro_rows: list[dict[str, Any]] = []
    metro_docs: dict[str, Any] = {}
    for line, fname in metro_in_use:
        doc = C.load_json(ctx.path("odpt", fname))
        metro_docs[line] = doc
        for r in parse_metro_timetable(doc):
            metro_rows.append({**r, "line": line})
    expedient_lines = {
        "田園都市線": "東急電鉄",
        "東横線": "東急電鉄",
        "井の頭線": "京王電鉄",
        "山手線": "JR東日本",
        "埼京線": "JR東日本",
        "湘南新宿ライン": "JR東日本",
    }
    real: RT.RealTimetables | None = None
    remaining_lines: list[str] = []
    real_notes: dict[str, Any] = {}
    real = RT.load_real_timetables(ctx.data)
    # 銀座線(9 月改正)もメトロの派生(metro_* の欄・ゲート)に入れる=メトロ 3 線の意味を保つ
    metro_rows = metro_rows + [
        {"railway": "Ginza", "calendar": r["calendar"], "direction": r["direction"],
         "departure": r["departure"], "line": r["line"]}
        for r in real.rows if r["line"] == RT.GINZA_SPEC.line
    ]

    weekday_metro = [r for r in metro_rows if r["calendar"] == "Weekday"]
    holiday_metro = [r for r in metro_rows if r["calendar"] != "Weekday"]
    n_metro_dirs = len({(r["line"], r["direction"]) for r in weekday_metro})
    # 平日と土休で**別の**オフピーク比を実ダイヤから導く(同じ導出式・別の行集合)。
    offpeak_ratio, peak_am, offpeak_mean = offpeak_ratio_from(weekday_metro)
    ratio_holiday, peak_am_holiday, offpeak_mean_holiday = offpeak_ratio_from(holiday_metro)
    holiday_peak_for_gate = peak_am_holiday
    metro_mins = sorted(_minute(r["departure"]) for r in weekday_metro)
    first_min = metro_mins[0] if metro_mins else 300
    last_min = metro_mins[-1] if metro_mins else 1500
    if last_min < first_min:
        last_min += MINUTES_PER_DAY
    first_last_by_calendar = {"Weekday": (first_min, last_min), "SaturdayHoliday": (first_min, last_min)}

    if real is not None:
        # 〔2-3b〕実ダイヤの全線の行(メトロ 2 線=7 月の取得+実ダイヤの読み口)。派生(オフピーク比・ピーク本数・
        # 初終発)は**全線の実ダイヤ**から計算し直す(等間隔の線が残ったときだけ使う・今は 0 線)。
        all_rows: list[dict[str, Any]] = [
            {"line": r["line"], "operator": "東京メトロ", "direction": r["direction"],
             "calendar": "Weekday" if r["calendar"] == "Weekday" else "SaturdayHoliday",
             "departure": r["departure"], "source": "real"}
            for r in metro_rows if r["line"] in METRO_LINES_KEPT_WITH_REAL
        ] + list(real.rows)
        wd_all = [r for r in all_rows if r["calendar"] == "Weekday"]
        ho_all = [r for r in all_rows if r["calendar"] != "Weekday"]
        offpeak_ratio, real_peak_wd, real_off_wd = offpeak_ratio_from(wd_all)
        ratio_holiday, real_peak_ho, real_off_ho = offpeak_ratio_from(ho_all)
        holiday_peak_for_gate = real_peak_ho
        for cal, rs in (("Weekday", wd_all), ("SaturdayHoliday", ho_all)):
            mins = sorted(_minute(r["departure"]) for r in rs)
            if mins:
                first_last_by_calendar[cal] = (mins[0], mins[-1])
        covered = {r["line"] for r in all_rows}
        covered |= {raw for raw, tgt in real.fold_lines.items() if tgt in covered}
        remaining_lines = [ln for ln in sorted(expedient_lines) if ln not in covered]
        real_notes = {
            "real_peak_am_trains": real_peak_wd,
            "real_offpeak_mean_trains": round(real_off_wd, 2),
            "real_peak_am_trains_holiday": real_peak_ho,
            "real_offpeak_mean_trains_holiday": round(real_off_ho, 2),
        }
    else:
        all_rows = []
    offpeak_ratio_by_calendar = {
        "Weekday": offpeak_ratio,
        "SaturdayHoliday": ratio_holiday,
    }

    # 等間隔の推定: 1.1.0 は 5 線(湘南新宿ラインは本数が無い=対象外)。実ダイヤでは実データの無い線だけ。
    eq_lines = sorted(expedient_lines.items()) if real is None else [
        (ln, expedient_lines[ln]) for ln in remaining_lines
    ]
    eq_rows: list[dict[str, Any]] = []
    for line, operator in eq_lines:
        tph = PEAK_TRAINS_PER_HOUR.get(line)
        if not tph:
            continue
        for calendar in ("Weekday", "SaturdayHoliday"):
            ratio = offpeak_ratio_by_calendar[calendar]
            f_min, l_min = first_last_by_calendar[calendar] if real is not None else (first_min, last_min)
            for direction in ("上り", "下り"):
                for dep in equal_interval_departures(
                    tph,
                    ratio,
                    f_min,
                    l_min,
                    peak_tph_pm=pm_peak_for_line(
                        line, PM_PEAK_ASSUMED_EQUAL_TO_AM, PM_PEAK_TRAINS_PER_HOUR
                    ),
                ):
                    eq_rows.append({"line": line, "operator": operator, "direction": direction,
                                    "calendar": calendar, "departure": dep,
                                    "source": "equal_interval_expedient"})
    if real is None:
        out_rows = eq_rows  # 1.1.0 の並び(メトロの行の後に等間隔の行)
    else:
        out_rows = sorted(
            [*all_rows, *eq_rows],
            key=lambda d: (d["line"], d["calendar"], d["direction"], _minute(d["departure"]), d["source"]),
        )
    for r in out_rows:
        tt_line.append(r["line"])
        tt_operator.append(r["operator"])
        tt_direction.append(r["direction"])
        tt_calendar.append(r["calendar"])
        tt_dep.append(r["departure"])
        tt_src.append(r["source"])

    tt_cols = {
        "line": tt_line,
        "operator": tt_operator,
        "direction": tt_direction,
        "calendar": tt_calendar,
        "departure": tt_dep,
        "departure_min": np.array([_minute(t) for t in tt_dep], dtype=np.int32),
        "source": tt_src,
    }
    # 線 × 暦の本数(平日と土休の逆転=第330 §6 の欠陥の検査)
    by_line_cal: dict[str, dict[str, int]] = defaultdict(lambda: {"Weekday": 0, "SaturdayHoliday": 0})
    for ln, cal in zip(tt_line, tt_calendar):
        by_line_cal[ln][cal] += 1
    by_line_cal = {k: dict(v) for k, v in sorted(by_line_cal.items())}
    lines_holiday_gt_weekday = [ln for ln, v in by_line_cal.items() if v["SaturdayHoliday"] > v["Weekday"]]
    lines_missing_calendar = [ln for ln, v in by_line_cal.items() if min(v.values()) <= 0]
    # 〔2-3c〕渋谷の発着の表(発車の行はこの時刻表の行と 1 対 1・時刻表は変えない)
    events: RE.RailEvents | None = None
    if real is not None:
        events = RE.build_rail_events(ctx.data, tt_cols, metro_docs)

    params: dict[str, Any] = {
        "nodes": [
            {**{k: (list(v) if isinstance(v, tuple) else v) for k, v in spec.items()}}
            for spec in NODE_DEFS
        ],
        "modes_by_kind": {k: list(v) for k, v in MODES_BY_KIND.items()},
        "pt_purpose_to_timedist": PT_PURPOSE_TO_TIMEDIST,
        "peak_trains_per_hour": PEAK_TRAINS_PER_HOUR,
        "peak_hours_am": list(PEAK_HOURS_AM),
        "peak_hours_pm": list(PEAK_HOURS_PM),
        "offpeak_hours": list(OFFPEAK_HOURS),
        "pm_peak_assumed_equal_to_am": PM_PEAK_ASSUMED_EQUAL_TO_AM,
        "offpeak_ratio_rule": (
            "平日/土休それぞれのメトロ実ダイヤから 昼(10-15時)平均本数 ÷ 朝(7-9時)最大本数"
        ),
        "time_bin_mapping": {"～6時台": [5, 6], "0時台～": [0, 1]},
        "pt_source": "docs/bench/pt_shibuya/pt6_summary_core0241.json",
        "generation_weights_usage": "用途=W16/W17生成入力・較正・検証のみ(D-W14)",
    }
    if not PM_PEAK_ASSUMED_EQUAL_TO_AM:
        # 〔改訂(第330)〕既定(True)の params には鍵を足さない=既定の param_hash は不変。
        params["pm_peak_trains_per_hour"] = dict(sorted((PM_PEAK_TRAINS_PER_HOUR or {}).items()))
    if real is not None:
        # 〔2-3b〕実ダイヤのときだけ変える・足す(切替口 False の params は 1.1.0 と同じ)。
        params["offpeak_ratio_rule"] = (
            "平日/土休それぞれの実ダイヤ(全線)から 昼(10-15時)平均本数 ÷ 朝(7-9時)最大本数"
            "(等間隔の線が残ったときだけ使う)"
        )
        params["real_timetables"] = {
            "stage": RT.STAGE_TAG,
            "world_time_point": RT.WORLD_TIME_POINT,
            "tables": RT.spec_rows(),
            "fold_lines": dict(sorted(real.fold_lines.items())),
            "temporary_train_types": list(RT.TEMPORARY_TRAIN_TYPES),
            "temporary_mark": RT.TEMPORARY_MARK,
            "metro_lines_kept": list(METRO_LINES_KEPT_WITH_REAL),
            "odpt_static_dir": "/".join(RT.ODPT_STATIC_DIR),
            "ginza": {
                "railway": RT.GINZA_SPEC.railway,
                "origin_station": RT.GINZA_SPEC.origin_station,
                "source": RT.GINZA_SPEC.source,
            },
            "versions_file": VERSIONS_FILE,
        }
        # 〔2-3c〕発着の表の規則(conf つき)と出力の名
        params["rail_events"] = {
            "stage": RE.STAGE_TAG,
            "file": RE.EVENTS_FILE,
            "columns": list(RE.COLUMNS),
            "rules": {rid: {"rule": RE.THROUGH_RULES[rid], "conf": RE.RULE_CONF[rid]} for rid in RE.THROUGH_RULES},
            "through_dwell_max_min": RE.THROUGH_DWELL_MAX_MIN,
            "tokyu_origin_marks": "/".join((*RT.USER_TIMETABLE_DIR, RT.TOKYU_MARKS_FILE)),
            "nex_tables": [list(x) for x in RT.NEX_TABLES],
            "keio_arrival_stem": RT.KEIO_ARRIVAL_STEM,
        }
    pm_expedient = (
        "夕ピーク本数=朝ピークと同数(資料3は朝ピークのみ=D-W14 の空欄)"
        if PM_PEAK_ASSUMED_EQUAL_TO_AM
        else "夕ピーク本数=引数の表 PM_PEAK_TRAINS_PER_HOUR(出典は表を渡した側が宣言する)"
    )
    metro_rows_count = (
        sum(1 for s in tt_src if s == "real") if real is None else len(metro_rows)
    )
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([*paths, pt_path, *metro_paths, *real_paths, exits_p, nodes_p, edges_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["外界ノード(方面)", "鉄道運行(計画データ)", "駅・出口", "境界流量"],
        expedients=[
            "時間帯配分=time_dist_12(2015)を 2018/2021 総量へ当てる(時点混合)",
            "time_dist_12 の ～6時台→5,6時・0時台～→0,1時 の等分",
            "目的×手段の構成は全ノード共通(方面別の目的構成は未取得)",
        ],
        notes={
            "generation_weights_usage": "用途=W16/W17生成入力・較正・検証のみ(D-W14)",
            "rail_line_board": {k: round(v, 1) for k, v in sorted(lines["board"].items())},
            "rail_line_alight": {k: round(v, 1) for k, v in sorted(lines["alight"].items())},
            "transfer_out_by_line": {k: round(v, 1) for k, v in sorted(tr_out.items())},
            "transfer_in_by_line": {k: round(v, 1) for k, v in sorted(tr_in.items())},
            "transfer_total_daily": round(sum(tr_out.values()), 1),
            "node_daily_inflow": {r["node_id"]: r["daily_inflow"] for r in rows},
            "total_daily_inflow": round(total_inflow, 1),
            "rail_daily_inflow": round(rail_inflow, 1),
            "station_alight_total_before_transfer_deduction": round(
                sum(lines["alight"].values()), 1
            ),
            "pt_rail_external_arrivals_2018": round(mode_external["鉄道"], 1),
            "pt_total_external_arrivals_2018": round(sum(mode_external.values()), 1),
            "rail_inflow_over_pt_ratio": (
                round(rail_inflow / mode_external["鉄道"], 2) if mode_external["鉄道"] else None
            ),
            "through_running_caveat": (
                "田園都市線↔半蔵門線・東横線↔副都心線は**直通運転**で、渋谷を通過する客が"
                "一方の路線の『降車』と他方の『乗車』に二重に現れる。transfer_12 は"
                "改札内の**歩く乗換**しか数えないので、この通過分は控除できない"
                "(直通の実数はどの入手済ファイルにも無い=空欄)。よって鉄道ノードの"
                "daily_inflow は**街への流入の上限**であり、PT(2018・0241着 鉄道 264,036/平日)"
                "の約5.5倍になる。W16/W17 で使うときは**方面の相対重みとしてのみ**用い、"
                "絶対水準は PT 側で較正すること。"
            ),
            "unit_difference_note": (
                "ODPT PassengerSurvey は JR=乗車のみ(include_alighting=false)・"
                "東急/京王/メトロ=乗降。センサス由来の daily_inflow とは数え方が違うので"
                "odpt_survey_* 列は併記のみ(足し引きしない)。"
                "メトロ半蔵門/副都心は改札共用で1レコード=按分せず両ノードに同値が入る点に注意。"
            ),
            "gateway_nodes": n_gate,
            "gate_cells_walk": len(set(gate_cells_walk)),
            "gate_cells_road": len(set(gate_cells_road)),
            "exits_by_station": {k: len(v) for k, v in sorted(exits_by_station.items())},
            "metro_timetable_rows": metro_rows_count,
            "metro_timetable_source": (
                "ODPT odpt:StationTimetable JSON(GTFS zip は未使用)"
                if real is None
                else "半蔵門線・副都心線=ODPT odpt:StationTimetable(7 月の取得)・銀座線=ODPT odpt:TrainTimetable"
                "(オープン枠の静的データ版 1・9 月改正)"
            ),
            "metro_directions": n_metro_dirs,
            "metro_peak_am_trains": peak_am,
            "metro_offpeak_mean_trains": round(offpeak_mean, 2),
            "offpeak_ratio": round(offpeak_ratio, 4),
            "metro_peak_am_trains_holiday": peak_am_holiday,
            "metro_offpeak_mean_trains_holiday": round(offpeak_mean_holiday, 2),
            "offpeak_ratio_holiday": round(ratio_holiday, 4),
            "offpeak_ratio_by_calendar": {
                k: round(v, 4) for k, v in sorted(offpeak_ratio_by_calendar.items())
            },
            "offpeak_ratio_holiday_note": (
                "土休のメトロ実ダイヤに『朝ピーク』の制度的な定義は無い(資料3は朝ラッシュのみ)。"
                "平日と同じ導出(7-9時の最大本数を分母・10-15時の平均を分子)を土休の行集合に"
                "当てた実測値をそのまま使う=土休は平日より比が1に近い(昼と朝の差が小さい)。"
                if real is None
                else "〔2-3b〕オフピーク比は実ダイヤ(全線)の平日/土休それぞれの行集合から同じ導出で計算し直す"
                "(7-9時の最大本数を分母・10-15時の平均を分子)。等間隔の線が残ったときだけ使う。"
                "metro_* の欄はメトロ 3 線(銀座線は 9 月改正)の値。"
            ),
            "pm_peak_assumed_equal_to_am": PM_PEAK_ASSUMED_EQUAL_TO_AM,
            "pm_peak_note": (
                "D-W14 の本数表(資料3=最混雑区間)は**朝ピークのみ**。夕ピーク(17-19時)の"
                "本数はどの入手済み資料にも無いので朝と同数に置く(expedient)。"
            ),
            "metro_first_departure": C.min_to_hhmm(first_min),
            "metro_last_departure": C.min_to_hhmm(last_min),
            "expedient_timetable_rows": sum(
                1 for s in tt_src if s == "equal_interval_expedient"
            ),
            "timetable_lines_skipped": (
                [ln for ln, v in PEAK_TRAINS_PER_HOUR.items() if v is None]
                if real is None
                else [ln for ln in remaining_lines if not PEAK_TRAINS_PER_HOUR.get(ln)]
            ),
            "generation_weight_rows": len(w_val),
        },
    )
    # 〔2-3b・検収 H1〕時刻表の宣言はモジュールの表から足す(星付きの要素で渡さない=走査器が数える形)。
    if real is not None:
        res.expedients.extend(REAL_TIMETABLE_EXPEDIENTS)
    if events is not None:
        res.expedients.extend(RAIL_EVENT_EXPEDIENTS)
    if real is None or remaining_lines:
        res.expedients.extend(EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS)
    if real is not None and remaining_lines:
        # 動的な中身(残る線の名・夕ピークの規則)は notes に分ける(宣言の文は固定=台帳の行と 1 対 1)
        res.notes["equal_interval_lines"] = list(remaining_lines)
        res.notes["equal_interval_pm_rule"] = pm_expedient
    if not PM_PEAK_ASSUMED_EQUAL_TO_AM:
        res.notes["pm_peak_note"] = (
            "夕ピーク(17-19時)の本数は引数の表 PM_PEAK_TRAINS_PER_HOUR から(既定の表は無い・"
            "他社の比で埋めない=答え 10-12b 1-2)。"
        )
        res.notes["pm_peak_trains_per_hour"] = params["pm_peak_trains_per_hour"]
    if real is not None:
        res.notes.update({
            "timetable_rows_by_source": dict(sorted(Counter(tt_src).items())),
            "timetable_rows_by_line_calendar": by_line_cal,
            "lines_holiday_gt_weekday": lines_holiday_gt_weekday,
            "equal_interval_lines_remaining": remaining_lines,
            "real_timetable_table_counts": real.table_counts,
            "temporary_trains_excluded": real.temporary_excluded,
            "dedup_removed": real.dedup_removed,
            "ginza_check": real.ginza_check,
            "fold_lines": dict(sorted(real.fold_lines.items())),
            "real_first_last_by_calendar": {
                cal: [C.min_to_hhmm(a), C.min_to_hhmm(b)] for cal, (a, b) in sorted(first_last_by_calendar.items())
            },
            **real_notes,
            "timetable_versions_file": VERSIONS_FILE,
        })
    if events is not None:
        # 〔2-3c〕発着の表の要約(時刻は書かない)。規則と空欄の文は版の表と params にある。
        res.notes["rail_events"] = {k: v for k, v in events.summary.items() if k not in ("rules", "blanks")}
    res.outputs.append(C.write_parquet(ctx.out, "w12_external_nodes.parquet", node_cols))
    res.outputs.append(
        C.write_parquet(
            ctx.out,
            "w12_generation_weights.parquet",
            {
                "node_id": w_node,
                "purpose": w_purpose,
                "mode": w_mode,
                "hour": np.array(w_hour, dtype=np.int16),
                "weight": weights,
            },
        )
    )
    res.outputs.append(C.write_parquet(ctx.out, "w12_timetables.parquet", tt_cols))
    if real is not None:
        versions = timetable_versions_doc(
            ctx, real, by_line_cal, tt_line, tt_operator, tt_src, metro_docs, metro_in_use, remaining_lines
        )
        if events is not None:
            versions["rail_events"] = events.summary  # 〔2-3c〕規則(conf つき)・本数・空欄の宣言
        res.outputs.append(C.write_json(ctx.out, VERSIONS_FILE, versions, rows=len(versions["lines"])))
    if events is not None:
        res.outputs.append(C.write_parquet(ctx.out, RE.EVENTS_FILE, events.columns))

    share_sums_ok = all(
        abs(sum(v) - 1.0) < 1e-6 for v in list(hour_share_alight.values()) + list(hour_share_board.values())
    )
    res.gates = [
        C.Gate("external_nodes", len(rows), 10),
        C.Gate("every_node_has_cell", int(all(len(r["attached_place_ids"]) >= 1 for r in rows)), 1),
        C.Gate("total_daily_inflow", round(total_inflow, 1), None),
        C.Gate("rail_daily_inflow", round(rail_inflow, 1), None),
        C.Gate(
            "station_alight_total",
            round(sum(lines["alight"].values()), 1),
            None,
        ),
        C.Gate(
            "rail_inflow_over_pt_rail_arrivals",
            round(rail_inflow / mode_external["鉄道"], 2) if mode_external["鉄道"] else None,
            None,
        ),
        C.Gate("metro_timetable_rows", metro_rows_count, None, passed=metro_rows_count > 0),
        C.Gate("metro_first_departure_plausible", C.min_to_hhmm(first_min), None, passed=270 <= first_min <= 330),
        C.Gate(
            "metro_last_departure_plausible",
            C.min_to_hhmm(last_min),
            None,
            passed=1410 <= last_min <= 1530,
        ),
        C.Gate("hour_share_vectors_sum_to_1", share_sums_ok, True),
        C.Gate("offpeak_ratio_weekday", round(offpeak_ratio, 4), None),
        C.Gate("offpeak_ratio_holiday", round(ratio_holiday, 4), None),
        C.Gate(
            "holiday_timetable_has_own_peak",
            holiday_peak_for_gate,
            None,
            passed=holiday_peak_for_gate > 0,
        ),
        C.Gate(
            "generation_weights_sum_to_1",
            round(float(weights.sum()), 9),
            None,
            passed=abs(float(weights.sum()) - 1.0) < 1e-6,
        ),
        C.Gate("timetable_rows", len(tt_dep), None),
    ]
    if real is not None:
        n_temp = sum(sum(v.values()) for v in real.temporary_excluded.values())
        res.gates += [
            # 〔2-3b〕等間隔の推定で残る線(実データの無い線)=0 を検査する。
            C.Gate("equal_interval_lines_remaining", len(remaining_lines), 0),
            C.Gate("real_lines_have_both_calendars", not lines_missing_calendar, True),
            # 第330 §6 の欠陥(等間隔の推定で土休 > 平日)が実ダイヤで消えたことの検査。
            C.Gate("lines_holiday_gt_weekday", len(lines_holiday_gt_weekday), 0),
            C.Gate("temporary_trains_excluded", n_temp, None),
            C.Gate("dedup_removed", int(sum(real.dedup_removed.values())), None),
            C.Gate("ginza_departures_from_shibuya", real.ginza_check.get("n_departures_from_origin", 0), None,
                   passed=real.ginza_check.get("n_departures_from_origin", 0) > 0),
        ]
    if events is not None:
        n_dep_ev = int(events.summary["rows_by_event"].get(RE.EVENT_JA[RE.EVENT_DEPARTURE], 0))
        n_arr_ev = int(events.summary["rows_by_event"].get(RE.EVENT_JA[RE.EVENT_ARRIVAL], 0))
        res.gates += [
            # 〔2-3c〕発着の表の発車の行は時刻表の行と 1 対 1・到着の行がある・残った疑わしい組 0
            C.Gate("rail_events_departure_rows_match", n_dep_ev == len(tt_dep), True),
            C.Gate("rail_events_arrival_rows", n_arr_ev, None, passed=n_arr_ev > 0),
            C.Gate("rail_events_suspicious_pairs", RE.suspicious_total(events.summary), 0),
            # 〔検収 M1・L2〕同じ分の 2 便で潰れた属性・始発の印の食い違い(どちらも上の和にも入る)
            C.Gate("rail_events_attr_collapsed", int(events.summary["attr_collapsed"]), 0),
            C.Gate("rail_events_origin_flag_mismatch",
                   int(events.summary["metro_dep_join"]["origin_flag_mismatch_station_vs_train_timetable"]), 0),
        ]
    return res


def timetable_versions_doc(
    ctx: C.Ctx,
    real: RT.RealTimetables,
    by_line_cal: dict[str, dict[str, int]],
    tt_line: Sequence[str],
    tt_operator: Sequence[str],
    tt_src: Sequence[str],
    metro_docs: dict[str, Any],
    metro_in_use: Sequence[tuple[str, str]],
    remaining_lines: Sequence[str],
) -> dict[str, Any]:
    """〔2-3b〕``w12_timetable_versions.json``: 線ごとの版の宣言(世界の時点との前後)と入力の md5。

    時刻の一覧は書かない(本数と版だけ=チャレンジ枠の生の行を写さない)。
    """
    sources: dict[str, set[str]] = defaultdict(set)
    operator_of: dict[str, str] = {}
    for ln, op, s in zip(tt_line, tt_operator, tt_src):
        sources[ln].add(s)
        operator_of[ln] = op
    folded_into: dict[str, list[str]] = defaultdict(list)
    for raw, tgt in sorted(real.fold_lines.items()):
        folded_into[tgt].append(raw)
    lines_doc: dict[str, Any] = {}
    for ln in sorted(by_line_cal):
        decl = RT.VERSION_DECLARATIONS.get(ln, {"declared": "(宣言なし)", "relation_to_world_time": "unknown"})
        if ln in remaining_lines:  # 〔2-4〕実データの無い線(京王の切替口 False の井の頭線など)=等間隔の推定
            decl = {"declared": "実データなし=等間隔の推定(EQUAL_INTERVAL_TIMETABLE_EXPEDIENTS)",
                    "relation_to_world_time": "unknown"}
        d: dict[str, Any] = {
            "operator": operator_of.get(ln, ""),
            "sources": sorted(sources[ln]),
            "rows": by_line_cal[ln],
            **decl,
            "version_text_in_tables": list(real.version_texts.get(ln, [])),
        }
        if ln in metro_docs:
            d["odpt_station_timetable"] = RT.metro_station_versions(metro_docs[ln])
        if ln == RT.GINZA_SPEC.line:
            d["odpt_train_timetable"] = {
                "dct_issued": real.ginza_check.get("dct_issued", {}),
                "dc_date": real.ginza_check.get("dc_date", {}),
            }
        if folded_into.get(ln):
            d["folded_lines"] = folded_into[ln]
        lines_doc[ln] = d
    inputs: list[dict[str, Any]] = []
    for fam in RT.INPUT_FAMILIES:
        for rel in RT.input_rel_paths(fam):
            p = ctx.data.joinpath(*rel.split("/"))
            inputs.append({"family": fam, "path": rel, "md5": RT.md5_file(p), "bytes": p.stat().st_size})
    for _ln, fname in metro_in_use:
        p = ctx.path("odpt", fname)
        inputs.append({"family": "odpt_open_station_timetable", "path": f"odpt/{fname}",
                       "md5": RT.md5_file(p), "bytes": p.stat().st_size})
    return {
        "schema": "shibuya.build.field/w12_timetable_versions/1",
        "stage": RT.STAGE_TAG,
        "stage_version": STAGE_VERSION,
        "world_time_point": RT.WORLD_TIME_POINT,
        "relation_codes": {
            "before": "世界の時点より前の版(頁か ODPT に改正日の記載)",
            "before_inferred": "世界の時点より前の版と推測(改正日の記載なし)",
            "after": "世界の時点より後の版(宣言)",
            "unknown": "宣言なし",
        },
        "lines": lines_doc,
        "inputs": inputs,
        "temporary_trains_excluded": real.temporary_excluded,
        "dedup_removed": real.dedup_removed,
        "equal_interval_lines_remaining": list(remaining_lines),
        "note": "時刻の一覧は載せない(本数と版だけ)。ODPT チャレンジ枠の生の行は再配布しない。",
    }
