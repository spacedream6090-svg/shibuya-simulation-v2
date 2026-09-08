"""W12 外界ノード(§1 W12・D-W14・境界経済設計書 §1 U10)。

**役割の限定(D-W14)**: 本段階の集計表は**エージェントの来街を抽選する装置ではない**。
来街は各 persistent_id の週次スケジュール表(T0)→T1差分→T2 LLM で決まる。ここで作る重みの
用途は ①W16/W17 の**生成入力** ②**較正** ③**検証**(コードン流量)の3つに限る。

出力
  - ``w12_external_nodes.parquet``: 方面別ノード 10(鉄道8・徒歩1・道路1)。
  - ``w12_generation_weights.parquet``: 方面×目的×手段×時刻の重み(用途は上記3つのみ)。
  - ``w12_timetables.parquet``: 路線×方向×平日/土休の発時刻(メトロ3線=実・他=等間隔 expedient)。

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
  - JR・東急・京王=等間隔ダイヤ(F10)。ピーク本数は国交省 資料3(**朝ピークのみ**=夕ピークは
    朝と同数に置く)、オフピーク比は**平日/土休それぞれの**メトロ実ダイヤから、ダイヤ端は
    メトロ平日ダイヤから導く。方向別の内訳が非公開なので上下同数と仮定。
  - 湘南新宿ラインのピーク本数は資料3に行が無い=**ダイヤ生成の対象外**(空欄)。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from typing import Any, Sequence

import numpy as np

from . import common as C

STAGE = "W12"
STAGE_VERSION = "1.0.0"

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
        vec = [0.0] * 24
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
    v = int(h) * 60 + int(m)
    return v + 1440 if v < SERVICE_DAY_CUT_MIN else v


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
    t = first_min
    while t <= last_min:
        out.append(C.min_to_hhmm(t))
        hour = (t // 60) % 24
        if hour in PEAK_HOURS_AM:
            tph = float(peak_tph)
        elif hour in PEAK_HOURS_PM:
            tph = float(pm)
        else:
            tph = peak_tph * offpeak_ratio
        tph = max(tph, 1.0)
        t += max(int(round(60.0 / tph)), 1)
    return out


def offpeak_ratio_from(rows: Sequence[dict[str, Any]]) -> tuple[float, int, float]:
    """メトロ実ダイヤの発時刻行 → (オフピーク比, 朝ピーク本数, 昼平均本数)。

    比 = 昼(10-15時)の1時間あたり平均本数 ÷ 朝ピーク(7-9時)の最大本数。
    行が無い/ピークが 0 のときは比 1.0(=一様)を返す。
    """
    if not rows:
        return 1.0, 0, 0.0
    per_hour: Counter = Counter(_minute(r["departure"]) // 60 for r in rows)
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
    metro_paths = [ctx.path("odpt", f) for _line, f in METRO_TIMETABLES]
    for p in [*paths, pt_path, *metro_paths]:
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
    for line, fname in METRO_TIMETABLES:
        doc = C.load_json(ctx.path("odpt", fname))
        for r in parse_metro_timetable(doc):
            metro_rows.append({**r, "line": line})
    for r in sorted(metro_rows, key=lambda d: (d["line"], d["calendar"], d["direction"], d["departure"])):
        tt_line.append(r["line"])
        tt_operator.append("東京メトロ")
        tt_direction.append(r["direction"])
        tt_calendar.append("Weekday" if r["calendar"] == "Weekday" else "SaturdayHoliday")
        tt_dep.append(r["departure"])
        tt_src.append("real")

    weekday_metro = [r for r in metro_rows if r["calendar"] == "Weekday"]
    holiday_metro = [r for r in metro_rows if r["calendar"] != "Weekday"]
    n_metro_dirs = len({(r["line"], r["direction"]) for r in weekday_metro})
    # 平日と土休で**別の**オフピーク比を実ダイヤから導く(同じ導出式・別の行集合)。
    offpeak_ratio, peak_am, offpeak_mean = offpeak_ratio_from(weekday_metro)
    ratio_holiday, peak_am_holiday, offpeak_mean_holiday = offpeak_ratio_from(holiday_metro)
    offpeak_ratio_by_calendar = {
        "Weekday": offpeak_ratio,
        "SaturdayHoliday": ratio_holiday,
    }
    metro_mins = sorted(_minute(r["departure"]) for r in weekday_metro)
    first_min = metro_mins[0] if metro_mins else 300
    last_min = metro_mins[-1] if metro_mins else 1500
    if last_min < first_min:
        last_min += 1440

    expedient_lines = {
        "田園都市線": "東急電鉄",
        "東横線": "東急電鉄",
        "井の頭線": "京王電鉄",
        "山手線": "JR東日本",
        "埼京線": "JR東日本",
        "湘南新宿ライン": "JR東日本",
    }
    for line, operator in sorted(expedient_lines.items()):
        tph = PEAK_TRAINS_PER_HOUR.get(line)
        if not tph:
            continue
        for calendar in ("Weekday", "SaturdayHoliday"):
            ratio = offpeak_ratio_by_calendar[calendar]
            for direction in ("上り", "下り"):
                for dep in equal_interval_departures(
                    tph,
                    ratio,
                    first_min,
                    last_min,
                    peak_tph_pm=None if PM_PEAK_ASSUMED_EQUAL_TO_AM else tph,
                ):
                    tt_line.append(line)
                    tt_operator.append(operator)
                    tt_direction.append(direction)
                    tt_calendar.append(calendar)
                    tt_dep.append(dep)
                    tt_src.append("equal_interval_expedient")

    tt_cols = {
        "line": tt_line,
        "operator": tt_operator,
        "direction": tt_direction,
        "calendar": tt_calendar,
        "departure": tt_dep,
        "departure_min": np.array([_minute(t) for t in tt_dep], dtype=np.int32),
        "source": tt_src,
    }

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
    res = C.StageResult(
        stage=STAGE,
        stage_version=STAGE_VERSION,
        input_hash=C.input_hash([*paths, pt_path, *metro_paths, exits_p, nodes_p, edges_p]),
        param_hash=C.param_hash(params),
        params=params,
        catalog_classes=["外界ノード(方面)", "鉄道運行(計画データ)", "駅・出口", "境界流量"],
        expedients=[
            "時間帯配分=time_dist_12(2015)を 2018/2021 総量へ当てる(時点混合)",
            "time_dist_12 の ～6時台→5,6時・0時台～→0,1時 の等分",
            "目的×手段の構成は全ノード共通(方面別の目的構成は未取得)",
            "JR・東急・京王=等間隔ダイヤ(F10)・上下同数",
            "山手線ピーク本数=資料3の 16-20 本/h の中央 18",
            "オフピーク比はメトロ実ダイヤから移植(平日は平日ダイヤ・土休は土休ダイヤ)",
            "夕ピーク本数=朝ピークと同数(資料3は朝ピークのみ=D-W14 の空欄)",
            "初終発時刻はメトロ**平日**ダイヤから移植(土休の初終発は別に測っていない)",
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
            "metro_timetable_rows": sum(1 for s in tt_src if s == "real"),
            "metro_timetable_source": "ODPT odpt:StationTimetable JSON(GTFS zip は未使用)",
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
            "timetable_lines_skipped": [
                ln for ln, v in PEAK_TRAINS_PER_HOUR.items() if v is None
            ],
            "generation_weight_rows": len(w_val),
        },
    )
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
        C.Gate("metro_timetable_rows", sum(1 for s in tt_src if s == "real"), None, passed=any(s == "real" for s in tt_src)),
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
            peak_am_holiday,
            None,
            passed=peak_am_holiday > 0,
        ),
        C.Gate(
            "generation_weights_sum_to_1",
            round(float(weights.sum()), 9),
            None,
            passed=abs(float(weights.sum()) - 1.0) < 1e-6,
        ),
        C.Gate("timetable_rows", len(tt_dep), None),
    ]
    return res
