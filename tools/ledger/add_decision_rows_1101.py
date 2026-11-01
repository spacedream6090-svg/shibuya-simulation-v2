# -*- coding: utf-8 -*-
"""add_decision_rows_1101 — つなぎの台帳に判断ごとの行(``DEC-…``)を足す(第340 段 2 の 2)。

決定: 回答 11-01 §3(つなぎの台帳と WorldProcess に ``drives_from``)・§10(routing §1 の表を正とする)・指示書 11-01
段 2 の 2(台帳には判断ごとの行が無い=棚卸し §5 → routing §1 の 112 行を元に行を起こす)。

- **既存の行は 1 バイトも変えない**。``DEC-<#>-<英数の短い名>`` の 112 行を ``bridges`` の末尾に置く。
- 〔検収 中-1 の土台・親の指示〕欄は ``Bridge`` の欄(``engine.bridging.ledger``)に入れた。前の版の頭の鍵 ``row_fields``・
  ``row_fields_note`` は消す。既存の行には欄を足さない(空=未記入)。前の版で既存の行に書いた値は、同じものの DEC の行へ
  移した(BR-BODY-COLLAPSE-RATE→DEC-83・BR-ATTENDANCE-LOTTERY→DEC-2・BR-W17-IO-SLEEP→DEC-1/63/69/71・BR-DELIVERY-INBOUND→
  DEC-102・HD-economy.pricing→DEC-101)。PR-/FB- の行と世界過程の結びは ``declared_in`` から引く(``circularity``)。
- **冪等**: ``DEC-`` の行を作り直して同じ位置(末尾・routing の番号の順)に置く。本体の版の上で何度回しても同じ。
- DEC の行の欄: ``what``=判断(routing §1 の「判断」)・``why``=いまの決め手・行き先・根拠・移すのに要るもの・
  外すまでのつなぎ(routing §1 のセルの写し)・``remove_at``=下の ``stage_of``(``remove_basis=inferred``=親が確かめる)・
  ``conf``=L1 残すで仕組みも値も裏付けのある行は mechanism・ほかは expedient・``status=active``・``declared_in``=routing の
  節と行・``routing_row``・``drives_from``(書いていない行は未記入)・``world_process``・``contributes``・
  ``calibration_declined``・``decided``(回答 11-01 の節の ID=中身は写さない)・``drives_note``(値の出典)。

使い方: ``python tools/ledger/add_decision_rows_1101.py [台帳] [routing]``(既定はリポの道筋)。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
LEDGER = ROOT / "docs" / "design" / "bridging-ledger.json"
ROUTING = ROOT / "docs" / "reference" / "decision-routing-2026-11-01.md"
ROUTING_REL = "docs/reference/decision-routing-2026-11-01.md"
SINCE = "2026-11-01"
PREFIX = "DEC-"

_ROW_FIELDS_OLD = ("row_fields", "row_fields_note")  # 前の版の頭の鍵(作り直すときに消す)

#: routing §1 の行の番号 → 英数の短い名(識別子に open・tick を含めない)。
NAMES: dict[int, str] = {
    1: "comeToday", 2: "skipWork", 3: "leaveTrain", 4: "arriveMode", 5: "goHomeTime", 6: "homeDetour",
    7: "talkAtPlanEnd", 8: "dropAtLeave", 9: "returnLater", 10: "bigEvent", 11: "whereToGo", 12: "categoryTarget",
    13: "wanderArea", 14: "giveUpFar", 15: "routeChoice", 16: "stairsLift", 17: "walkSpeed", 18: "crowdAvoid",
    19: "boardTrain", 20: "linePlatform", 21: "skipTrain", 22: "crowdedBoard", 23: "stopWaiting", 24: "whatAction",
    25: "whichStore", 26: "habitStore", 27: "recalledStore", 28: "queueIfFull", 29: "joinQueue", 30: "leaveQueue",
    31: "leaveSeat", 32: "mealLength", 33: "walkOut", 34: "seeSign", 35: "signText", 36: "buyOrNot",
    37: "itemQty", 38: "priceBalk", 39: "payMethod", 40: "atmWithdraw", 41: "homeUse", 42: "litter",
    43: "powerWater", 44: "startTalk", 45: "talkWhom", 46: "acceptInvite", 47: "reinviteWait", 48: "turnTaking",
    49: "utterance", 50: "backchannel", 51: "endTalk", 52: "closingLine", 53: "thirdJoiner", 54: "refuse",
    55: "help", 56: "report", 57: "noticeAcquaintance", 58: "tieStrength", 59: "messaging", 60: "noticeCall",
    61: "chargePhone", 62: "appointment", 63: "weeklyPlan", 64: "replan", 65: "activityUntil", 66: "nextThink",
    67: "noThinkAsleepOut", 68: "noWakeInActivity", 69: "sleepOnPlan", 70: "sleepSelf", 71: "wakeUp",
    72: "sleepPlace", 73: "hotelStay", 74: "holidayCalendar", 75: "checkPlan", 76: "hunger", 77: "fatigue",
    78: "eatInside", 79: "eatOutside", 80: "eatHome", 81: "rest", 82: "feelHeat", 83: "collapse",
    84: "noticeSalient", 85: "reactChange", 86: "thresholdRethink", 87: "loudSound", 88: "lombard", 89: "gaze",
    90: "surprise", 91: "memorize", 92: "recall", 93: "storeMemory", 94: "reflectDay", 95: "deliberate",
    96: "planFixSurprise", 97: "storeHoursRun", 98: "restock", 99: "discardUnsold", 100: "serveCustomer",
    101: "changePrice", 102: "inboundDelivery", 103: "wastePickup", 104: "streetSweep", 105: "parcelDelivery",
    106: "roadWorks", 107: "runTrains", 108: "runBuses", 109: "driveCars", 110: "dispatch", 111: "pressRelease",
    112: "shiftPlan",
}

#: 行き先 → 外す段(当てた値=remove_basis inferred・検収 中-4 と低-6 の当て直し)。
#: L1.5=11-01p-3(語彙と判断の口=指示書 11-01 段 3)・初期の予定=6-2(カレンダー 1b=BR-W17-IO-SLEEP と同じ)・代打と無いと
#: 宣言=6-6(② 人の仕事を働く人へ)・L2=6-7(熟考の形)。§1-8 の L2(#100 接客・#101 値段)は店の仕事=6-6・発話の L2
#: (#49・50・52)は会話の段=6-4・#79(範囲外の食事)は輪の段が要る=7。L1 残すと要判断=7。
#: ただし回答 11-01 §2 で外す率の行(#2・3・10・22・42・83・99・105 と Calvo=#101)と、routing の「外すまでのつなぎ」が
#: 「すぐ外」と書く行は next-bump(次の版上げ)。「すぐ外すか」(問いの形=#108)は除く。
_STAGE = {"L1.5": "11-01p-3", "初期の予定": "6-2", "代打(つなぎ)": "6-6", "無いと宣言": "6-6", "L2": "6-7", "要判断": "7",
          "L1 残す": "7"}
_STAGE_ROW = {100: "6-6", 101: "6-6", 49: "6-4", 50: "6-4", 52: "6-4", 79: "7"}
#: 回答 11-01 §2 で外す 9 件(#101 は Calvo の改定確率と β を結線しない行)。
NEXT_BUMP_ROWS = frozenset({2, 3, 10, 22, 42, 83, 99, 105, 101})

#: L1 残すで仕組みも値も裏付けのある行=mechanism(検収 低-5: #76 の語の区切り・#85 の不応期 30 分・#88 の器だけ・
#: #83 の率の置き換えは expedient)。
_MECHANISM_L1 = {17, 58, 84, 87, 92}

#: 回答 11-01 で決めた節(中身は写さない=CLAUDE.md §6 決定の写し)。
DECIDED: dict[int, str] = {
    **{n: "11-01/§10-1" for n in (55, 56, 66, 67, 68, 102, 73, 109)},
    **{n: "11-01/§10-2(6-1)" for n in (18, 34, 60, 77, 82, 86)},
    **{n: "11-01/§10-2(6-3)" for n in (91, 93)},
    **{n: "11-01/§10-2(6-4)" for n in (57, 89, 90)},
    48: "11-01/§10-2(6-6)",
    **{n: "11-01/§10-2(6-7)" for n in (35, 107, 108, 111, 112)},
    **{n: "11-01/§10-2(6-8)" for n in (4, 43, 74)},
    **{n: "11-01/§2" for n in (2, 3, 10, 22, 42, 99, 101, 105, 83)},
    **{n: "11-01/§3" for n in (31, 32, 41, 98)},
}

#: DEC の行の drives_from と結ぶ世界過程(分かる行だけ。a1-research §6 と routing §1 から)。
_SSB = ("data:ssb", "data:pt2018")
_SSB_NOTE = ("W17 の週の表の元=社会生活基本調査(a1-research §6 #20)・PT 2018 で較正(パターン台帳 §9 D11′ の用途欄"
             "「W17較正」)。出力が D1′ に入るかは未確認")
_W17_SLEEP = ("A5", "A6")  # 就寝と起床の時刻・睡眠の長さ=実装役の読み(検収 中-1)
DEC_FIELDS: dict[int, dict[str, Any]] = {
    1: {"drives_from": _SSB, "drives_note": _SSB_NOTE},
    2: {"drives_from": ("none",), "drives_note": "出勤率のくじは既定 1.0=働いていない(a1-research §6 #19・routing #2)"},
    3: {"drives_from": ("none",), "drives_note": "E1 と E8 ±8 便は自前の規則(routing #3)"},
    5: {"drives_from": _SSB, "drives_note": _SSB_NOTE},
    10: {"drives_from": ("none",), "world_process": "large_event",
         "drives_note": "200 人は自前の定数(集計の量=a1-research §6 #17)"},
    22: {"drives_from": ("none",), "world_process": "rail_operation_static",
         "drives_note": "150〜200% で 1.0→0.7 は自前の関数(a1-research §6 #21)。混雑率 D10′ は照合の対象(routing §4-2)"},
    28: {"world_process": "indoor_occupancy"},
    30: {"world_process": "indoor_occupancy"},
    31: {"drives_from": ("none",), "world_process": "indoor_occupancy",
         "drives_note": "30 刻みは回転率から置いた exp・出典なし(routing §4-2 #30・31・32)"},
    32: {"drives_from": ("none",), "world_process": "indoor_occupancy",
         "drives_note": "宣言は 20 分・実際は 30 分の席の規則(routing #32)"},
    41: {"drives_from": ("none",), "world_process": "goods_conservation",
         "drives_note": "19 時に 1 個ずつは自前(routing #41)。物の流れは goods_conservation の W1 に入る疑い(routing §4-2)"},
    42: {"drives_from": ("none",), "world_process": "street_cleaning",
         "drives_note": "0.05 g/人/刻みの原単位は空欄(a1-research §6 #15)"},
    43: {"drives_from": ("none",), "world_process": "infra_daily_load", "drives_note": "原単位は出典なし(routing #43)"},
    63: {"drives_from": _SSB, "contributes": ("A5", "A6", "A7"), "drives_note": _SSB_NOTE},
    69: {"drives_from": _SSB, "contributes": _W17_SLEEP, "drives_note": _SSB_NOTE},
    71: {"drives_from": _SSB, "contributes": _W17_SLEEP, "drives_note": _SSB_NOTE},
    73: {"drives_from": ("none",), "world_process": "hotel_room_inventory", "drives_note": "1 軒 120 室は自前(a1-research §6 #18)"},
    74: {"drives_from": ("data:cao_syukujitsu",), "drives_note": "内閣府の祝日 CSV(routing #74・ライセンス台帳)"},
    79: {"drives_from": _SSB, "drives_note": _SSB_NOTE},
    83: {"drives_from": ("W3",), "contributes": ("W3",),
         "drives_note": "倒れる率 3.0 件/万人日は救急の出場件数から置いた値=W3 と同系(a1-research §6 #8)。倒れた人は出動"
                 "(public_service_dispatch の contributes=W3)を通して W3 に入る"},
    97: {"world_process": "store_opening"},
    98: {"drives_from": ("none",), "world_process": "shelf_stock_restock",
         "drives_note": "補充点・ロットは自前(a1-research §6 #14)。contributes=W1・E5(routing §4-2)"},
    99: {"drives_from": ("none",), "world_process": "waste_collection",
         "drives_note": "SKU 別の廃棄率(a1-research §6 #15)。W1 の帯は同じ定数から作った自己整合(パターン台帳 §9 W1)"},
    101: {"drives_from": ("none",), "calibration_declined": ("E7",),
          "drives_note": "価格は構築時の値で固定・Calvo の改定確率と β は結線しない・β を E7 に合わせない(回答 11-01 §3・routing #101)"},
    102: {"drives_from": ("none",), "world_process": "delivery_inbound",
          "drives_note": "05〜08 時の乱数・15% 遅れは自前(goods_flow.py)。納品=入力(回答 11-01 §10-1)"},
    103: {"drives_from": ("none",), "world_process": "waste_collection"},
    104: {"drives_from": ("none",), "world_process": "street_cleaning"},
    105: {"drives_from": ("W2",), "world_process": "delivery_last_mile",
          "drives_note": "区按分 27,000 個/日=W2 の値(a1-research §6 #16)"},
    106: {"drives_from": ("none",), "world_process": "road_works_occupancy"},
    107: {"drives_from": ("data:timetables_w12",), "world_process": "rail_operation_static",
          "drives_note": "実ダイヤ 8 線(W12)"},
    108: {"drives_from": ("none",), "world_process": "bus_taxi_operation",
          "drives_note": "06〜23 時 10 分おきは自前(logistics.py BUS_HEADWAY_MIN)"},
    109: {"drives_from": ("data:road_census_r3",), "world_process": "vehicle_cross_section",
          "drives_note": "道の種類の既定交通量=W10 が道路交通センサス R3 の同じ行から作った klass 既定(traffic.py の docstring)"
                  "=D5′ と同じ調査"},
    110: {"drives_from": ("W3",), "world_process": "public_service_dispatch",
          "drives_note": "出動の回数は倒れる率(W3 と同系)で決まる(a1-research §6 #8)"},
    111: {"drives_from": ("none",), "world_process": "press_official_release", "drives_note": "07・12・18 時の定型文"},
}



def parse_routing(path: Path) -> list[list[str]]:
    """routing §1(「## §1」から「## §2」の前まで)の 112 行(7 つのセル)。"""
    text = path.read_text(encoding="utf-8")
    sec = text.split("## §1 行き先の表", 1)[1].split("## §2", 1)[0]
    rows = []
    for line in sec.split("\n"):
        if re.match(r"^\| \d+ \|", line):
            cells = [c.strip() for c in line.strip()[1:-1].split("|")]
            if len(cells) != 7:
                raise ValueError(f"routing §1 の行のセルが 7 つでない: {line[:40]!r}")
            rows.append(cells)
    nums = [int(c[0]) for c in rows]
    if nums != list(range(1, 113)):
        raise ValueError(f"routing §1 の行が 1〜112 でない({len(nums)} 行)")
    return rows


def _dest_key(dest: str) -> str:
    return "L1 残す" if dest.startswith("L1 残す") else dest


def stage_of(n: int, dest: str, bridge: str) -> str:
    """DEC の行の外す段(上の表の規則)。"""
    if n in NEXT_BUMP_ROWS or ("すぐ外" in bridge and "すぐ外すか" not in bridge):
        return "next-bump"
    if n in _STAGE_ROW:
        return _STAGE_ROW[n]
    return _STAGE[_dest_key(dest)]


#: DEC の行の欄の順(``Bridge.as_dict`` と同じ順)。
_OPT_ORDER = ("drives_from", "routing_row", "world_process", "decided", "contributes", "calibration_declined",
              "drives_note")


def dec_row(cells: list[str]) -> dict[str, Any]:
    n = int(cells[0])
    _, what, now, dest, basis, need, bridge = cells
    key = _dest_key(dest)
    conf = "mechanism" if (key == "L1 残す" and n in _MECHANISM_L1) else "expedient"
    row: dict[str, Any] = {
        "id": f"{PREFIX}{n}-{NAMES[n]}",
        "what": f"判断 #{n}: {what}",
        "why": (f"いまの決め手: {now}。行き先: {dest}(根拠 {basis})。移すのに要るもの: {need}。"
                f"外すまでのつなぎ: {bridge}"),
        "remove_at": stage_of(n, dest, bridge),
        "declared_in": f"{ROUTING_REL} §1 行 {n}",
        "conf": conf,
        "since": SINCE,
        "status": "active",
        "remove_basis": "inferred",
    }
    f: dict[str, Any] = {"routing_row": n, **DEC_FIELDS.get(n, {})}
    if n in DECIDED:
        f["decided"] = DECIDED[n]
    for k in _OPT_ORDER:
        if k in f and f[k]:
            v = f[k]
            row[k] = list(v) if isinstance(v, tuple) else v
    return row


def build(doc: dict[str, Any], routing_rows: list[list[str]]) -> dict[str, Any]:
    kept = [r for r in doc["bridges"] if not r["id"].startswith(PREFIX)]
    decs = [dec_row(c) for c in routing_rows]
    out: dict[str, Any] = {}
    for k, v in doc.items():
        if k in _ROW_FIELDS_OLD:
            continue
        out[k] = kept + decs if k == "bridges" else v
    return out


def dumps(doc: dict[str, Any]) -> str:
    """台帳の書式(1 字下げ・ensure_ascii=False・末尾に改行=既存のファイルと同じ)。"""
    return json.dumps(doc, ensure_ascii=False, indent=1) + "\n"


def main(argv: list[str]) -> int:
    ledger = Path(argv[1]) if len(argv) > 1 else LEDGER
    routing = Path(argv[2]) if len(argv) > 2 else ROUTING
    raw = ledger.read_bytes()
    if b"\r" in raw:
        raise SystemExit("台帳に CR がある(LF の版で回す)")
    doc = json.loads(raw)
    new = dumps(build(doc, parse_routing(routing)))
    ledger.write_bytes(new.encode("utf-8"))
    n_dec = sum(1 for r in json.loads(new)["bridges"] if r["id"].startswith(PREFIX))
    print(f"DEC の行 {n_dec}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
