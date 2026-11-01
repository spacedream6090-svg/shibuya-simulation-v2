"""11-02r §1 #7(「無い」の過程 5 件を止める): つなぎの台帳(docs/design/bridging-ledger.json)を本段に合わせて直す(何度でも)。

- 注を足す行: 既定で止めたが、旧道の切替口 ``--absent-processes legacy`` のためにコードの宣言が残る世界過程の行
  (``PR-waste_collection``・``PR-street_cleaning``・``PR-road_works_occupancy``・``PR-plan.road_works``・
  ``PR-public_service_dispatch``・``PR-infra_daily_load``)。``status`` と ``remove_at`` はそのまま(宣言がコードにある=1 対 1 の
  試験・外す段は世界過程の返済の段)。注は印 ``〔11-02r §1 #7〕`` で 1 回だけ足す。
- 足す行: ``DOC-s2e-absent-legacy-switch``(next-bump・宣言は記録 s2e-1102/README.md)。判断の行(``DEC-``)は台帳の末尾に
  まとめる約束(tests/bridging/test_decision_rows_1101.py)なので、最初の ``DEC-`` の行の前に置く。同じ id の行があれば、
  その位置のまま中身を今の文に置き換える。
- 判断の行(``DEC-43``・``DEC-103``・``DEC-104``・``DEC-106``・``DEC-110``)は tools/ledger/add_decision_rows_1101.py が作る
  (本段で外す段と決定の ID と注をその道具に足した)=本道具は触らない。
- 台帳の形(indent 1・ensure_ascii False・LF)は前のまま。

使い方(リポの根で): ``python docs/bench/analysis/s2e-1102/tools/add_bridges_s2e.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
DECL = "docs/bench/analysis/s2e-1102/README.md"
SINCE = "2026-11-02"
MARK = "〔11-02r §1 #7〕"

_STOPPED = (MARK + "既定(--absent-processes stopped)で止めた={what}(宣言 world/processes/absent.py の {aid}・"
            "engine/absent_processes.py)。旧道(切替口 legacy)だけが動かす=次の版上げで消す(記録 " + DECL + ")")

#: 注を足す行(id → 足す注)。
NOTE = {
    "PR-waste_collection": _STOPPED.format(
        what="06〜10 時の収集は無い(収集員の体が居ない・ビンに溜まる一方)。世帯の消費(#41・11-02r §1 #8)と担当の体の"
             "廃棄(腕 duties)は残す", aid="absent.waste_collection"),
    "PR-street_cleaning": _STOPPED.format(what="掃除の巡回は無い(清掃員の体が居ない・街路のごみは残る)",
                                          aid="absent.street_cleaning"),
    "PR-road_works_occupancy": _STOPPED.format(what="夜の占用は無い(業者の体が居ない)", aid="absent.road_works"),
    "PR-plan.road_works": _STOPPED.format(what="工事の予定を実行しない(辺の抽選は残す=記録しない)", aid="absent.road_works"),
    "PR-public_service_dispatch": _STOPPED.format(
        what="通報を受けた出動は無い(隊員と指令の体が居ない・倒れた人は運ばれない)", aid="absent.public_service_dispatch"),
    "PR-infra_daily_load": _STOPPED.format(what="電気と水の負荷の集計は無い", aid="absent.power_water"),
}


def _row(rid: str, what: str, why: str, code_at: list[str], *, remove_at: str = "next-bump",
         basis: str = "plan") -> dict:
    return {"id": rid, "what": what, "why": why, "remove_at": remove_at, "declared_in": DECL, "conf": "expedient",
            "since": SINCE, "status": "active", "remove_basis": basis, "code_at": code_at}


#: 足す行。
ROWS = [
    _row("DOC-s2e-absent-legacy-switch",
         "切替口 --absent-processes legacy(環境変数 SHIBUYA_ABSENT_PROCESSES=legacy)は 11-02r §1 #7 の版上げの前の値の再現の"
         "ためだけの道(ごみの収集 06〜10 時・街路の掃除の巡回・道路工事の夜の占用・救急と警察の出動・電気と水の負荷)",
         "回答 10-13b §0-6(版上げで新しい道を既定にしたら古い道の切替口は次の版上げで消す・旧値の再現は安定版のタグで)。"
         "legacy の 5,000 体 × 1 日 mock は前の版と final と呼数と過程の件数が一致(記録 " + DECL + ")。次の版上げで切替口を"
         "消すときに書き直す試験(旧道に固定した試験): tests/engine/processes/test_absent_processes_1102.py の legacy の側・"
         "旧道の過程の挙動を見る試験(test_goods_flow・test_logistics・test_civic・test_processes_run ほか=記録 §4 の一覧)",
         ["src/shibuya/engine/absent_processes.py", "src/shibuya/cli.py"]),
]


def _note(row: dict, text: str) -> bool:
    if MARK in row["why"]:
        return False
    row["why"] = row["why"] + text
    return True


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = data["bridges"]
    pos = {r["id"]: i for i, r in enumerate(rows)}
    missing = [k for k in NOTE if k not in pos]
    if missing:
        print(f"台帳に無い行(止める): {missing}")
        return 1
    changed = 0
    for rid, text in NOTE.items():
        changed += int(_note(rows[pos[rid]], text))
    added = 0
    for r in ROWS:
        if r["id"] in pos:
            rows[pos[r["id"]]] = r
            continue
        first_dec = next((i for i, x in enumerate(rows) if x["id"].startswith("DEC-")), len(rows))
        rows.insert(first_dec, r)
        pos = {x["id"]: i for i, x in enumerate(rows)}
        added += 1
    LEDGER.write_bytes((json.dumps(data, ensure_ascii=False, indent=1) + "\n").encode("utf-8"))
    print(f"直した行 {changed}・足した行 {added}・台帳 {len(rows)} 行")
    return 0


if __name__ == "__main__":
    sys.exit(main())
