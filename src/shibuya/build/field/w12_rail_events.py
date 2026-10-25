"""W12 の渋谷の発着の表(第 2 期 2-3c・計画 2-3c の行=2-3b の検収 3)。

2-3b の W12(1.2.0)は渋谷の**発車**の表だけを持つ(``w12_timetables.parquet``=エンジンが読む)。本モジュールは、その
発車の行を 1 行も変えずに、渋谷の**到着**の行と、直通の二重計上を 1 本に結ぶ列を、別の表
``w12_rail_events.parquet`` に組む(W12 1.3.0)。**エンジンはこの表を読まない**(読む口の器は
``engine.processes.rail_events``・既定は読まない)=活性化しても結果は変わらない(発車の表がバイト一致)。

表の 1 行=渋谷での 1 つの出来事(GTFS の ``stop_times`` の到着/発車の時刻を 1 行ずつに分けた形・記憶による比較=
未リサーチ・ネットワーク不可)。

    ======================  =======================================================================================
    列                      中身
    ======================  =======================================================================================
    event                   ``departure``(発車=``w12_timetables.parquet`` の行と 1 対 1)/ ``arrival``(到着)
    call_kind               ``origin``(渋谷始発)/ ``terminal``(渋谷止まり)/ ``through``(直通=別の線から着いて別の線
                            として発つ同じ列車)/ ``unknown``(表に無い=JR の途中駅の発車)
    line・operator・        W12 の語彙(到着の向きは到着する列車の向き=地下鉄 ``TokyoMetro.Shibuya``・京王 ``上り``)
    direction・calendar
    time・time_min          ``HH:MM`` と運行日の分(``w12_external_nodes._minute``=04:00 の切れ目)
    source                  出どころ(発車の行は発車の表と同じ・地下鉄の到着=``real_odpt_open_metro_2026-03`` か
                            ``…_2026-09``・京王の到着=``real_odpt_challenge_keio``)
    train_id                元の列車の id(地下鉄=ODPT の ``owl:sameAs``・京王=チャレンジ枠の列車番号 ``keio:<番号>``・
                            JR と東急の表=空=頁に列車番号が無い)
    train_key               1 本の列車の鍵(直通で結んだ行どうしは同じ=地下鉄の id・結べない行は ``train_id``)
    train_type・destination 種別と行き先(表の語のまま・地下鉄は日本語に写す)
    through_partner_line    直通の相手の線(到着=渋谷から先の線・発車=渋谷へ来た線/行く線・相鉄線直通の表=``相鉄線``)
    departure_row           発車の表の行の番号(到着は -1)
    merged_into_row         同じ列車の発車の行が 2 つあるとき(東急の上り=地下鉄の行と同じ列車)代表の行の番号(他は -1)
    counted                 1 本として数える行か(東急の上りの行は False=地下鉄の行で数える)
    ======================  =======================================================================================

直通のまとめの規則(``THROUGH_RULES``・版の表 ``w12_timetable_versions.json`` の ``rail_events`` に conf つきで書く):

- ``up_merge``(mechanism): 東急の上り(東急が出す副都心線・半蔵門線の標準時刻表)と地下鉄の駅の時刻表の渋谷発を、同じ暦・
  同じ発車の分・同じ行き先・同じ種別(F ライナー=急行)で 1 対 1 に結ぶ(extraction-tokyu-metro.md §5 で 995/995 一致)。
- ``down_through``(expedient=``w12_external_nodes.RAIL_EVENT_EXPEDIENTS``): 地下鉄の渋谷着(ODPT オープン枠の列車
  時刻表・行き先が東急の先)と、東急の下りの渋谷発のうち当駅始発の印(●・⑤・②=``東急_印.final.csv``・2-3c の読み取り)
  の無い便を、同じ暦・同じ行き先ごとに時刻の順に 1 対 1 で結ぶ(同じ行き先の便は渋谷で追い越さないと見る=推測)。
  発車−到着が 0〜:data:`THROUGH_DWELL_MAX_MIN` 分の外は疑わしい組。
- ``nex_in_shonan``(mechanism): 成田エクスプレスの表の便は湘南新宿ラインの表の同じ暦・時刻・行き先・種別の便と同じ
  (W12 は成田エクスプレスの表を読まない=二重に数えない)。
- ``sotetsu``(mechanism): 相鉄線直通の表の便は埼京線の上りの行に相手の線「相鉄線」を付ける。大崎方面の表と同じ分の便は
  疑わしい組として数える(まとめる組は無い見込み=extraction-jr.md §6 で 0)。相鉄線から来て北へ行く便は大宮方面の表から
  見分けられない(空欄)。

ODPT チャレンジ枠(京王)の生の行は資産の外(記録・版の表・試験の golden)に写さない(本数と版だけ)。

逐次ループ宣言: 発車の行(1 万行規模)・ODPT の列車(1 万本規模)・印(約 200)を 1 回ずつ。構築時だけ。
"""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

from . import w12_real_timetables as RT

#: 段の印。
STAGE_TAG = "2-3c"
#: 出力(資産の隣)。エンジン側の読む口の器 ``engine.processes.rail_events.RAIL_EVENTS_FILE`` と同じ名(試験で照らす)。
EVENTS_FILE = "w12_rail_events.parquet"

#: 列の順(版の表と記録に書く)。
COLUMNS: tuple[str, ...] = (
    "event", "call_kind", "line", "operator", "direction", "calendar", "time", "time_min", "source", "train_id",
    "train_key", "train_type", "destination", "through_partner_line", "departure_row", "merged_into_row", "counted",
)
EVENT_DEPARTURE = "departure"
EVENT_ARRIVAL = "arrival"
KIND_ORIGIN = "origin"
KIND_TERMINAL = "terminal"
KIND_THROUGH = "through"
KIND_UNKNOWN = "unknown"
#: 要約(版の表・ヘッダの notes)での出来事の名(版の表に語 departure を書かない=2-3b の検収 L3 の検査)。
EVENT_JA: dict[str, str] = {EVENT_DEPARTURE: "発車", EVENT_ARRIVAL: "到着"}

#: 地下鉄の到着(ODPT オープン枠の列車時刻表)の ``source``。半蔵門線・副都心線は 2026-03-14 の版(駅の時刻表と同じ版)。
SRC_METRO_ARRIVAL_0314 = "real_odpt_open_metro_2026-03"

#: 等間隔の推定の行の ``source``(``w12_external_nodes`` の等間隔の道)。
EQUAL_INTERVAL_SOURCE = "equal_interval_expedient"

#: 〔下りの直通〕発車−到着の上限[分](これを超える組は疑わしい組=ゲート)。実データの組は 0〜7 分(記録 tt23c §3)。
THROUGH_DWELL_MAX_MIN = 10


@dataclass(frozen=True)
class MetroLine:
    line: str
    railway: str
    shibuya: str
    #: 直通の相手の東急の線(渋谷の先)。銀座線は無し。
    tokyu_line: str
    #: 発車の表の地下鉄の行の ``direction``(渋谷発の向き)。
    dep_direction: str
    #: 到着の行の ``source``。
    arrival_source: str


METRO_LINES: tuple[MetroLine, ...] = (
    MetroLine("銀座線", "odpt.Railway:TokyoMetro.Ginza", "odpt.Station:TokyoMetro.Ginza.Shibuya", "",
              "TokyoMetro.Asakusa", RT.SRC_GINZA),
    MetroLine("半蔵門線", "odpt.Railway:TokyoMetro.Hanzomon", "odpt.Station:TokyoMetro.Hanzomon.Shibuya", "田園都市線",
              "TokyoMetro.Oshiage", SRC_METRO_ARRIVAL_0314),
    MetroLine("副都心線", "odpt.Railway:TokyoMetro.Fukutoshin", "odpt.Station:TokyoMetro.Fukutoshin.Shibuya", "東横線",
              "TokyoMetro.Wakoshi", SRC_METRO_ARRIVAL_0314),
)
METRO_BY_LINE: dict[str, MetroLine] = {m.line: m for m in METRO_LINES}
#: 東急の線 → 直通の相手の地下鉄の線。
TOKYU_PARTNER: dict[str, str] = {m.tokyu_line: m.line for m in METRO_LINES if m.tokyu_line}

#: ODPT の駅 id の末尾 → 行き先の名(手で書いた写しの表・知らない id は止まる)。
STATION_NAME: dict[str, str] = {
    "Shibuya": "渋谷", "Asakusa": "浅草", "Ueno": "上野",
    "Oshiage": "押上", "MinamiKurihashi": "南栗橋", "Kuki": "久喜", "KiyosumiShirakawa": "清澄白河",
    "KitaKoshigaya": "北越谷", "TobuDobutsuKoen": "東武動物公園", "Nagatacho": "永田町", "AoyamaItchome": "青山一丁目",
    "Hanzomon": "半蔵門",
    "Wakoshi": "和光市", "Kotesashi": "小手指", "Ikebukuro": "池袋", "ShinrinKoen": "森林公園",
    "ShakujiiKoen": "石神井公園", "Kawagoeshi": "川越市", "ShinjukuSanchome": "新宿三丁目", "Shiki": "志木",
    "Kiyose": "清瀬", "Hanno": "飯能", "Tokorozawa": "所沢", "Hoya": "保谷", "Ogawamachi": "小川町",
    "SeibuChichibu": "西武秩父",
    "ChuoRinkan": "中央林間", "Nagatsuta": "長津田", "Saginuma": "鷺沼",
    "MotomachiChukagai": "元町・中華街", "Shonandai": "湘南台", "MusashiKosugi": "武蔵小杉", "Ebina": "海老名",
    "Kikuna": "菊名", "Nishiya": "西谷", "Yokohama": "横浜", "Motosumiyoshi": "元住吉", "Yamato": "大和",
    "ShinYokohama": "新横浜", "Jiyugaoka": "自由が丘",
}
#: ODPT の種別 id の末尾 → 表の種別の語。
TRAIN_TYPE_NAME: dict[str, str] = {
    "Local": "各停", "Express": "急行", "SemiExpress": "準急", "CommuterExpress": "通勤急行", "F-Liner": "Fライナー",
    "S-TRAIN": "Sトレイン",
}
#: 突き合わせのときに同じと見る種別(東急の表は F ライナーを「急行」に F の印で載せる=第330 の読み取り)。
TYPE_KEY: dict[str, str] = {"Fライナー": "急行"}

#: 規則の id → conf。expedient の規則は ``w12_external_nodes.RAIL_EVENT_EXPEDIENTS`` に宣言の文がある(試験で照らす)。
RULE_CONF: dict[str, str] = {"up_merge": "mechanism", "down_through": "expedient", "nex_in_shonan": "mechanism",
                             "sotetsu": "mechanism"}
THROUGH_RULES: dict[str, str] = {
    "up_merge": "東急の上り(東急が出す副都心線・半蔵門線の標準時刻表)と地下鉄の駅の時刻表の渋谷発を、同じ暦・同じ発車の分・"
                "同じ行き先・同じ種別(F ライナー=急行)で 1 対 1 に結ぶ。数えるのは地下鉄の行の 1 回",
    "down_through": "地下鉄の渋谷着(ODPT オープン枠の列車時刻表・行き先が東急の先)と、東急の下りの渋谷発のうち当駅始発の印"
                    "(●・⑤・②)の無い便を、同じ暦・同じ行き先ごとに時刻の順に 1 対 1 で結ぶ(同じ行き先の便は渋谷で"
                    "追い越さないと見る=推測)。発車−到着が上限の分を超える組は疑わしい組",
    "nex_in_shonan": "成田エクスプレスの表の便は湘南新宿ラインの表の同じ暦・時刻・行き先・種別の便と同じ(読まない=二重に数えない)",
    "sotetsu": "相鉄線直通の表の便(渋谷から相鉄線へ)は埼京線の上りの行に相手の線を付ける。大崎方面の表と同じ分の便は"
               "疑わしい組として数える(行は消さない)。相鉄線から来て北へ行く便は大宮方面の表から見分けられない(空欄)",
}

#: 空欄の宣言(作り物の時刻を入れない)。
BLANKS: tuple[dict[str, str], ...] = (
    {"what": "JR(山手線・埼京線〈湘南新宿ライン・相鉄線直通を含む〉)の渋谷着の時刻と渋谷始発かどうか",
     "why": "渋谷は途中駅。手持ちの表は渋谷の発車だけで、着く時刻も始発駅も頁に無い(発車の行は call_kind=unknown)"},
    {"what": "東急から地下鉄へ直通する便(東横線→副都心線・田園都市線→半蔵門線)の渋谷着の時刻",
     "why": "地下鉄の列車時刻表は渋谷発から始まり、東急の列車時刻表は手元に無い(発車の行は call_kind=through)"},
    {"what": "東急の渋谷止まり(東横線・田園都市線の上り方面から渋谷で終わる便)の渋谷着の時刻",
     "why": "東急の到着の表は無い(手前の駅の表は各停だけ・急行は手前の駅に停まらない)"},
    {"what": "相鉄線から来て北へ行く埼京線の便の相手の線",
     "why": "大宮方面の表の行き先(新宿など)からは見分けられない(列車番号は頁に無い)"},
    {"what": "折り返しの結び付け(どの到着がどの渋谷始発の発車になるか)",
     "why": "銀座線・京王の列車時刻表と東急の表に次の列車への結び付けの欄が無い"},
)


# ---------------------------------------------------------------------- 入力
def _minute(hhmm: str) -> int:
    from .w12_external_nodes import _minute as m  # noqa: PLC0415(同じ段の運行日の分)

    return m(hhmm)


def station_name(station_id: str) -> str:
    """ODPT の駅 id → 名(知らない id は ValueError=黙って通さない)。"""
    key = str(station_id).split(".")[-1]
    if key not in STATION_NAME:
        raise ValueError(f"行き先の写しの表に無い駅: {station_id}")
    return STATION_NAME[key]


def type_name(train_type_id: str) -> str:
    key = str(train_type_id).split(".")[-1]
    if key not in TRAIN_TYPE_NAME:
        raise ValueError(f"種別の写しの表に無い種別: {train_type_id}")
    return TRAIN_TYPE_NAME[key]


def _timetable_id(train: str, calendar: str) -> str:
    """``odpt.Train:TokyoMetro.X.N`` と暦 → 列車時刻表の id(``owl:sameAs`` の形)。"""
    return "odpt.TrainTimetable:" + str(train).split(":", 1)[-1] + "." + calendar


def metro_trains(doc: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """ODPT オープン枠の列車時刻表 → (渋谷発の列車, 渋谷着の列車)=銀座線・半蔵門線・副都心線。"""
    data = doc.get("data", []) if isinstance(doc, Mapping) else list(doc)
    deps: list[dict[str, Any]] = []
    arrs: list[dict[str, Any]] = []
    by_rw = {m.railway: m for m in METRO_LINES}
    for tr in data:
        m = by_rw.get(str(tr.get("odpt:railway", "")))
        if m is None:
            continue
        objs = tr.get("odpt:trainTimetableObject") or []
        if not objs:
            continue
        first, last = objs[0], objs[-1]
        is_dep = str(first.get("odpt:departureStation", "")) == m.shibuya and bool(first.get("odpt:departureTime"))
        is_arr = str(last.get("odpt:arrivalStation", "")) == m.shibuya and bool(last.get("odpt:arrivalTime"))
        if not (is_dep or is_arr):
            continue  # 渋谷を発着しない列車(読まない)
        cal = str(tr.get("odpt:calendar", "")).split(":")[-1]
        if cal not in ("Weekday", "SaturdayHoliday"):
            raise ValueError(f"暦が Weekday/SaturdayHoliday の外: {tr.get('odpt:calendar')!r}")
        dests = tr.get("odpt:destinationStation") or [""]
        origins = tr.get("odpt:originStation") or [""]
        base = {"line": m.line, "calendar": cal, "train_id": str(tr.get("owl:sameAs", "")),
                "train_type": type_name(tr.get("odpt:trainType", "")), "destination": station_name(dests[0]),
                "origin_is_shibuya": str(origins[0]) == m.shibuya, "issued": str(tr.get("dct:issued", "")),
                "direction": str(tr.get("odpt:railDirection", "")).split(":")[-1]}
        if is_dep:
            deps.append({**base, "time": str(first["odpt:departureTime"])})
        if is_arr:
            arrs.append({**base, "time": str(last["odpt:arrivalTime"])})
    return deps, arrs


def metro_station_rows(doc: Mapping[str, Any], line: str) -> list[dict[str, Any]]:
    """ODPT の駅の時刻表(今の 7 月の取得・半蔵門線/副都心線)→ 発車の行の属性(列車の id・行き先・種別・始発の印)。"""
    out: list[dict[str, Any]] = []
    for t in doc.get("data", []):
        cal = str(t.get("odpt:calendar", "")).split(":")[-1]
        direction = str(t.get("odpt:railDirection", "")).split(":")[-1]
        for o in t.get("odpt:stationTimetableObject", []):
            if not o.get("odpt:departureTime"):
                continue
            dests = o.get("odpt:destinationStation") or [""]
            out.append({"line": line, "direction": direction, "calendar": cal, "departure": str(o["odpt:departureTime"]),
                        "train_id": _timetable_id(o.get("odpt:train", ""), cal), "destination": station_name(dests[0]),
                        "train_type": type_name(o.get("odpt:trainType", "")), "is_origin": bool(o.get("odpt:isOrigin"))})
    return out


def user_table_rows(data_root: Path) -> list[dict[str, Any]]:
    """読む表(:func:`RT.tables_in_use`)の行 → 発車の行の属性(表・種別・行き先)。畳んだ後の線で返す。"""
    out: list[dict[str, Any]] = []
    for spec in RT.tables_in_use():
        for cal_ja, cal in RT.CALENDARS:
            p = Path(data_root).joinpath(*spec.rel_dir(), spec.file_name(cal_ja))
            for r in RT.read_csv_rows(p):
                out.append({"line": RT.FOLD_LINES.get(spec.line, spec.line), "direction": spec.direction,
                            "calendar": cal, "departure": RT.hhmm(int(r["時"]), int(r["分"])), "table": spec.stem,
                            "train_type": str(r.get("種別", "")), "destination": str(r.get("行き先", ""))})
    return out


def keio_arrivals(data_root: Path) -> list[dict[str, Any]]:
    """京王 井の頭線の渋谷着(チャレンジ枠の列車時刻表から作った CSV)。切替口 ``USE_ODPT_CHALLENGE`` が False なら空。"""
    if not RT.USE_ODPT_CHALLENGE:
        return []
    out: list[dict[str, Any]] = []
    for cal_ja, cal in RT.CALENDARS:
        p = Path(data_root).joinpath(*RT.ODPT_CHALLENGE_DIR, f"{RT.KEIO_ARRIVAL_STEM}_{cal_ja}_odpt.csv")
        for i, r in enumerate(RT.read_csv_rows(p)):
            if (r.get("会社"), r.get("路線"), r.get("駅"), r.get("平日土休")) != ("京王", "井の頭線", "渋谷", cal_ja):
                raise ValueError(f"{p.name} の {i} 行目: 会社・路線・駅・暦が違う")
            out.append({"line": "井の頭線", "calendar": cal, "time": RT.hhmm(int(r["時"]), int(r["分"])),
                        "train_id": f"keio:{r['列車番号']}", "train_type": str(r.get("種別", "")),
                        "destination": str(r.get("行き先", ""))})
    return out


def tokyu_origin_marks(data_root: Path) -> dict[tuple[str, str, str], str]:
    """``東急_印.final.csv``(東急 渋谷の下りの 2 表の当駅始発の印)→ (表, 暦, HH:MM) → 印。"""
    p = Path(data_root).joinpath(*RT.USER_TIMETABLE_DIR, RT.TOKYU_MARKS_FILE)
    out: dict[tuple[str, str, str], str] = {}
    for r in RT.read_csv_rows(p):
        key = (str(r["表"]), RT.CALENDAR_OF[str(r["平日土休"])], RT.hhmm(int(r["時"]), int(r["分"])))
        if key in out:
            raise ValueError(f"印の表に同じ分が 2 行: {key[0]} {key[1]}")
        out[key] = str(r["印"])
    return out


def nex_rows(data_root: Path) -> list[dict[str, Any]]:
    """成田エクスプレスの表(読まない=湘南新宿ラインの表に含まれることの確かめだけ)。"""
    out: list[dict[str, Any]] = []
    for stem, heading_table in RT.NEX_TABLES:
        for cal_ja, cal in RT.CALENDARS:
            p = Path(data_root).joinpath(*RT.USER_TIMETABLE_DIR, f"{stem}_{cal_ja}_final.csv")
            for r in RT.read_csv_rows(p):
                out.append({"table": stem, "into": heading_table, "calendar": cal,
                            "departure": RT.hhmm(int(r["時"]), int(r["分"])), "train_type": str(r.get("種別", "")),
                            "destination": str(r.get("行き先", ""))})
    return out


# ---------------------------------------------------------------------- 組み立て
@dataclass
class RailEvents:
    columns: dict[str, Any]
    summary: dict[str, Any] = field(default_factory=dict)


def _key4(r: Mapping[str, Any]) -> tuple[str, str, str, str]:
    return (str(r["line"]), str(r["direction"]), str(r["calendar"]), str(r["departure"]))


def build_rail_events(
    data_root: Path,
    departures: Mapping[str, Sequence[Any]],
    metro_station_docs: Mapping[str, Any],
) -> RailEvents:
    """発車の表(``w12_timetables.parquet`` の列・行の順)+入力 → 発着の表と要約(時刻は要約に入れない)。"""
    root = Path(data_root)
    n_dep = len(departures["line"])
    dep_rows = [{k: departures[k][i] for k in ("line", "operator", "direction", "calendar", "departure", "source")}
                for i in range(n_dep)]
    for i, r in enumerate(dep_rows):
        r["row"] = i
    # 発車の行の鍵は一意(同じ線・向き・暦・分の便は 1 本=2-3b の重複の除去)
    dup = [k for k, c in Counter(map(_key4, dep_rows)).items() if c > 1]
    if dup:
        raise ValueError(f"発車の表に同じ線・向き・暦・分の行が {len(dup)} 組")

    # ---- 属性: 東急・JR・京王の表/地下鉄の駅の時刻表/銀座線の列車時刻表 ----
    # 〔検収 M1〕同じ線・向き・暦・分に 2 便ある生の行(発車の表では 1 行に潰れる=属性は先の 1 便だけ残る)を数える
    attrs: dict[tuple, dict[str, Any]] = {}
    attr_collapsed = 0
    user_raw = user_table_rows(root)
    for a in user_raw:
        k = _key4(a)
        if k in attrs:
            attr_collapsed += 1
            continue
        attrs[k] = a
    for line, doc in metro_station_docs.items():
        for a in metro_station_rows(doc, line):
            k = _key4(a)
            attr_collapsed += int(k in attrs)
            attrs[k] = a
    static = RT.load_odpt_static(root.joinpath(*RT.ODPT_STATIC_DIR, RT.ODPT_STATIC_METRO_TRAIN_TIMETABLE))
    m_deps, m_arrs = metro_trains(static)
    static_dep_by_id = {d["train_id"]: d for d in m_deps}
    for d in m_deps:
        if d["line"] == "銀座線":
            k = (d["line"], d["direction"], d["calendar"], d["time"])
            attr_collapsed += int(k in attrs)
            attrs[k] = {**d, "departure": d["time"]}
    # 等間隔の推定の行(京王の切替口 False の井の頭線など)は表の属性を持たない=call_kind unknown のまま
    missing_attr = [r["row"] for r in dep_rows if _key4(r) not in attrs and r["source"] != EQUAL_INTERVAL_SOURCE]
    if missing_attr:
        raise ValueError(f"属性の無い発車の行 {len(missing_attr)} 行")

    ev: list[dict[str, Any]] = []
    for r in dep_rows:
        a = attrs.get(_key4(r), {})
        tid = str(a.get("train_id", ""))
        ev.append({"event": EVENT_DEPARTURE, "call_kind": KIND_UNKNOWN, "line": r["line"], "operator": r["operator"],
                   "direction": r["direction"], "calendar": r["calendar"], "time": r["departure"],
                   "source": r["source"], "train_id": tid, "train_key": tid,
                   "train_type": str(a.get("train_type", "")), "destination": str(a.get("destination", "")),
                   "through_partner_line": "", "departure_row": r["row"], "merged_into_row": -1, "counted": True,
                   "_table": str(a.get("table", "")), "_is_origin": a.get("is_origin")})

    # ---- 終点の線(銀座線・井の頭線)の発車=渋谷始発 ----
    for e in ev:
        if e["line"] in ("銀座線", "井の頭線") and e["source"] != EQUAL_INTERVAL_SOURCE:
            e["call_kind"] = KIND_ORIGIN

    # ---- 地下鉄(半蔵門線・副都心線)の発車: 始発か直通か(列車時刻表の originStation・駅の時刻表の isOrigin と照らす) ----
    static_join_missing = 0
    origin_flag_mismatch = 0
    for e in ev:
        m = METRO_BY_LINE.get(e["line"])
        if m is None or not m.tokyu_line:
            continue
        sd = static_dep_by_id.get(e["train_id"])
        if sd is None or sd["time"] != e["time"]:
            static_join_missing += 1
            continue
        if bool(sd["origin_is_shibuya"]) != bool(e["_is_origin"]):
            origin_flag_mismatch += 1
        if sd["origin_is_shibuya"]:
            e["call_kind"] = KIND_ORIGIN
        else:
            e["call_kind"] = KIND_THROUGH
            e["through_partner_line"] = m.tokyu_line

    # ---- up_merge: 東急の上り ↔ 地下鉄の渋谷発 ----
    metro_dep_key: dict[tuple, list[dict]] = defaultdict(list)
    for e in ev:
        m = METRO_BY_LINE.get(e["line"])
        if m is not None and m.tokyu_line:
            metro_dep_key[(m.tokyu_line, e["calendar"], e["time"], e["destination"],
                           TYPE_KEY.get(e["train_type"], e["train_type"]))].append(e)
    up_merged: Counter = Counter()
    up_unmatched: Counter = Counter()
    for e in ev:
        if e["line"] in TOKYU_PARTNER and e["direction"] == "上り" and e["source"] == RT.SRC_TOKYU:
            k = (e["line"], e["calendar"], e["time"], e["destination"], TYPE_KEY.get(e["train_type"], e["train_type"]))
            hit = metro_dep_key.get(k) or []
            if len(hit) != 1:
                up_unmatched[f"{e['line']}|{e['calendar']}"] += 1
                continue
            twin = hit.pop()
            e["train_key"] = twin["train_id"]
            e["merged_into_row"] = twin["departure_row"]
            e["counted"] = False
            e["call_kind"] = twin["call_kind"]
            e["through_partner_line"] = TOKYU_PARTNER[e["line"]] if twin["call_kind"] == KIND_THROUGH else ""
            up_merged[f"{e['line']}|{e['calendar']}"] += 1
    metro_left = sum(len(v) for v in metro_dep_key.values())

    # ---- 到着: 地下鉄(銀座線・半蔵門線・副都心線) ----
    arr: list[dict[str, Any]] = []
    for a in m_arrs:
        m = METRO_BY_LINE[a["line"]]
        terminal = a["destination"] == "渋谷"
        arr.append({"event": EVENT_ARRIVAL, "call_kind": KIND_TERMINAL if terminal else KIND_THROUGH,
                    "line": a["line"], "operator": "東京メトロ", "direction": a["direction"],
                    "calendar": a["calendar"], "time": a["time"], "source": m.arrival_source,
                    "train_id": a["train_id"], "train_key": a["train_id"], "train_type": a["train_type"],
                    "destination": a["destination"], "through_partner_line": "" if terminal else m.tokyu_line,
                    "departure_row": -1, "merged_into_row": -1, "counted": True, "_issued": a["issued"]})
    # ---- 到着: 京王(チャレンジ枠) ----
    for a in keio_arrivals(root):
        arr.append({"event": EVENT_ARRIVAL, "call_kind": KIND_TERMINAL, "line": a["line"], "operator": "京王電鉄",
                    "direction": "上り", "calendar": a["calendar"], "time": a["time"], "source": RT.SRC_KEIO,
                    "train_id": a["train_id"], "train_key": a["train_id"], "train_type": a["train_type"],
                    "destination": a["destination"], "through_partner_line": "", "departure_row": -1,
                    "merged_into_row": -1, "counted": True})

    # ---- down_through: 地下鉄の渋谷着(直通)↔ 東急の下りの渋谷発(当駅始発の印の無い便) ----
    marks = tokyu_origin_marks(root)
    mark_rows_found = 0
    down_dep: dict[tuple, list[dict]] = defaultdict(list)
    for e in ev:
        if e["line"] in TOKYU_PARTNER and e["direction"] == "下り" and e["source"] == RT.SRC_TOKYU:
            if (e["_table"], e["calendar"], e["time"]) in marks:
                e["call_kind"] = KIND_ORIGIN
                mark_rows_found += 1
                continue
            down_dep[(TOKYU_PARTNER[e["line"]], e["calendar"], e["destination"])].append(e)
    down_arr: dict[tuple, list[dict]] = defaultdict(list)
    for a in arr:
        if a["line"] in METRO_BY_LINE and a["call_kind"] == KIND_THROUGH:
            down_arr[(a["line"], a["calendar"], a["destination"])].append(a)
    paired: Counter = Counter()
    unpaired = 0
    out_of_window = 0
    swappable = 0
    gaps: Counter = Counter()
    type_pairs: Counter = Counter()
    for key in sorted(set(down_dep) | set(down_arr)):
        aa = sorted(down_arr.get(key, []), key=lambda x: (_minute(x["time"]), x["train_id"]))
        dd = sorted(down_dep.get(key, []), key=lambda x: (_minute(x["time"]), x["departure_row"]))
        if len(aa) != len(dd):
            unpaired += abs(len(aa) - len(dd))
            continue
        for k, (a, d) in enumerate(zip(aa, dd)):
            gap = _minute(d["time"]) - _minute(a["time"])
            gaps[gap] += 1
            if not 0 <= gap <= THROUGH_DWELL_MAX_MIN:
                out_of_window += 1
            a["train_key"] = d["train_key"] = a["train_id"]
            d["call_kind"] = KIND_THROUGH
            d["through_partner_line"] = a["line"]
            type_pairs[f"{a['train_type']}→{d['train_type']}"] += 1
            paired[f"{a['line']}→{d['line']}|{a['calendar']}"] += 1
            # 追い越しで入れ替わりうる組(次の組と入れ替えても 0〜上限に収まる)
            if k + 1 < len(aa):
                a2, d2 = aa[k + 1], dd[k + 1]
                g1 = _minute(d2["time"]) - _minute(a["time"])
                g2 = _minute(d["time"]) - _minute(a2["time"])
                if 0 <= g1 <= THROUGH_DWELL_MAX_MIN and 0 <= g2 <= THROUGH_DWELL_MAX_MIN:
                    swappable += 1

    # ---- nex_in_shonan: 成田エクスプレスの表 ⊂ 湘南新宿ラインの表(〔検収 M1〕表の生の行で数える) ----
    shonan = Counter((a["table"], a["calendar"], a["departure"], a["destination"], a["train_type"]) for a in user_raw
                     if a["table"].startswith("JR_湘南新宿ライン"))
    nex_merged = 0
    nex_unmatched = 0
    for r in nex_rows(root):
        k = (r["into"], r["calendar"], r["departure"], r["destination"], r["train_type"])
        if shonan[k] > 0:
            shonan[k] -= 1
            nex_merged += 1
        else:
            nex_unmatched += 1

    # ---- sotetsu: 相鉄線直通の表の便 ----
    # 〔検収 M1〕重なりは表の生の行で数える(発車の表は 2-3b で同じ分の 2 便を 1 行にしたので、発車の行で数えると
    # 作りの上で 0 しか出ない)。相手の線は発車の行(属性が相鉄線直通の表のもの)に付ける。
    sot_raw = Counter((a["calendar"], a["departure"]) for a in user_raw if a["table"] == RT.SOTETSU_TABLE)
    osk_raw = Counter((a["calendar"], a["departure"]) for a in user_raw if a["table"] == RT.OSAKI_TABLE)
    sotetsu_overlap = int(sum((sot_raw & osk_raw).values()))
    sotetsu = [e for e in ev if e["_table"] == RT.SOTETSU_TABLE]
    for e in sotetsu:
        e["through_partner_line"] = "相鉄線"

    # ---- 並べる(発車=行の順・到着=線・暦・分・id) ----
    arr.sort(key=lambda x: (x["line"], x["calendar"], _minute(x["time"]), x["train_id"]))
    rows = ev + arr
    cols: dict[str, Any] = {c: [] for c in COLUMNS}
    for r in rows:
        for c in COLUMNS:
            if c == "time_min":
                cols[c].append(_minute(r["time"]))
            else:
                cols[c].append(r[c])
    cols["time_min"] = np.array(cols["time_min"], dtype=np.int32)
    cols["departure_row"] = np.array(cols["departure_row"], dtype=np.int32)
    cols["merged_into_row"] = np.array(cols["merged_into_row"], dtype=np.int32)
    cols["counted"] = np.array(cols["counted"], dtype=bool)

    # ---- 要約(時刻は書かない) ----
    by_line: dict[str, dict[str, dict[str, int]]] = {}
    for r in rows:
        d = by_line.setdefault(r["line"], {}).setdefault(r["calendar"], Counter())
        ja = EVENT_JA[r["event"]]
        d[ja] += 1
        if r["event"] == EVENT_DEPARTURE:
            d["発車(数える)"] += int(bool(r["counted"]))
        d[f"{ja}_{r['call_kind']}"] += 1
    by_line_out = {ln: {cal: dict(sorted(c.items())) for cal, c in sorted(v.items())} for ln, v in sorted(by_line.items())}
    arrival_versions: dict[str, Counter] = defaultdict(Counter)
    for r in arr:
        arrival_versions[r["line"]][str(r.get("_issued", "")) or r["source"]] += 1
    summary = {
        "stage": STAGE_TAG,
        "file": EVENTS_FILE,
        "rows": len(rows),
        "rows_by_event": dict(sorted(Counter(EVENT_JA[r["event"]] for r in rows).items())),
        "by_line_calendar": by_line_out,
        "arrivals_by_source": dict(sorted(Counter(r["source"] for r in arr).items())),
        "arrival_versions": {k: dict(sorted(v.items())) for k, v in sorted(arrival_versions.items())},
        "rules": [{"id": rid, "rule": THROUGH_RULES[rid], "conf": RULE_CONF[rid]} for rid in THROUGH_RULES],
        "through_dwell_max_min": THROUGH_DWELL_MAX_MIN,
        "up_merge": {"merged": dict(sorted(up_merged.items())), "unmatched_tokyu_rows": dict(sorted(up_unmatched.items())),
                     "metro_rows_without_tokyu_twin": metro_left},
        "metro_dep_join": {"static_join_missing": static_join_missing,
                             "origin_flag_mismatch_station_vs_train_timetable": origin_flag_mismatch},
        "down_through": {"paired": dict(sorted(paired.items())), "unpaired": unpaired, "out_of_window": out_of_window,
                         "swappable_adjacent_pairs": swappable, "dwell_min_hist": {str(k): v for k, v in sorted(gaps.items())},
                         "type_pairs": dict(sorted(type_pairs.items())),
                         "origin_marks": len(marks), "origin_marks_on_rows": mark_rows_found},
        "nex_in_shonan": {"merged": nex_merged, "unmatched": nex_unmatched},
        "sotetsu": {"rows_with_partner": len(sotetsu), "overlap_with_osaki_table": sotetsu_overlap,
                    "raw_rows": int(sum(sot_raw.values()))},
        "attr_collapsed": attr_collapsed,
        "blanks": list(BLANKS),
        "note": "時刻の一覧は載せない(本数と版だけ)。ODPT チャレンジ枠の生の行は再配布しない。",
    }
    return RailEvents(columns=cols, summary=summary)


def suspicious_total(summary: Mapping[str, Any]) -> int:
    """残った疑わしい組の数(ゲートの値): 結べない東急の上り・下りの対の数の食い違い・上限の外・成田エクスプレスの外れ・
    相鉄線直通と大崎方面の重なり(表の生の行)・印の分が発車の行に無い・地下鉄の発車と列車時刻表の結び損ね・始発の印の
    食い違い(駅の時刻表 vs 列車時刻表)・同じ分の 2 便で潰れた属性(〔検収 M1・L2〕)。"""
    up = summary["up_merge"]
    dn = summary["down_through"]
    return int(sum(up["unmatched_tokyu_rows"].values()) + up["metro_rows_without_tokyu_twin"] + dn["unpaired"]
               + dn["out_of_window"] + (dn["origin_marks"] - dn["origin_marks_on_rows"])
               + summary["nex_in_shonan"]["unmatched"] + summary["sotetsu"]["overlap_with_osaki_table"]
               + summary["metro_dep_join"]["static_join_missing"]
               + summary["metro_dep_join"]["origin_flag_mismatch_station_vs_train_timetable"]
               + summary["attr_collapsed"])
