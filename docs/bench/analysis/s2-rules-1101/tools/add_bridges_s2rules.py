"""段 2 の 5(回答 11-01 §5・指示書 11-01 段 2 の 5): つなぎの台帳(docs/design/bridging-ledger.json)に 1 行を足す(何度でも同じ台帳)。

- 足す行(末尾): ``DOC-s2rules-min-wage-floor-bridge``=最低賃金の行(規則の表 ``minimum_wage.tokyo`` の 3 版)を human に直し、
  給料日の床を machine のつなぎ(行の ``params.bridge``)で残した分。
- 同じ id の行があれば中身を置き換える(位置はそのまま)。台帳の形(indent 1・ensure_ascii False・LF)は前のまま。
- ``rule_id: minimum_wage.tokyo``(親の判断・試験 ``test_rule_ids_point_to_the_rules_table`` の固定の一覧に足した)。
  規則の表の ``params.bridge`` の ``remove_at`` と ``ledger_id`` はこの行と同じ値(7・本行の id)。

使い方(リポの根で): ``python docs/bench/analysis/s2-rules-1101/tools/add_bridges_s2rules.py``
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[5]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
DECL = "docs/bench/analysis/s2-rules-1101/README.md"
REC = "記録 docs/bench/analysis/s2-rules-1101/README.md"
AN = "src/shibuya/economy/anchors.py"
WG = "src/shibuya/economy/wages.py"
S2 = "src/shibuya/economy/stage2.py"
SINCE = "2026-11-01"

ADD = [
    {
        "id": "DOC-s2rules-min-wage-floor-bridge",
        "what": "最低賃金の床(最賃法 4 条 2 項=給料日に時給が最低賃金を下回る体の月の賃金を、最低賃金 × 月の時間の目安に上げる)"
                "を machine のつなぎで残す。規則の表の minimum_wage.tokyo(3 版)は kind: human・床を当てるのは行の "
                "params.bridge が machine の間だけ(economy.anchors.min_wage_terms・economy.wages.floor_with_shortfall)。"
                "床を当てる直前に下回った体と額を economy.stage2 の rules.minimum_wage_shortfall に数える(床がある間は "
                "violation_rows=0)",
        "why": "回答 11-01 §5(判定は「現実でその場で物理的に止まるか」=最低賃金に足りない賃金は機械では止まらず事後の監督。"
               "検知と反応の口(気づいた人・本人・監督)ができるまで machine をつなぎとして残す)・指示書 11-01 段 2 の 5"
               "(違反が起きたら記録する器だけ先に)・10-12 §1-4(法に反する行動は起きたことにする)。外す段=検知と反応の口が"
               f"できる段(計画の段の番号が無い=7 を当てた・実装役が当てた)({REC})",
        "remove_at": "7",
        "declared_in": DECL,
        "conf": "expedient",
        "since": SINCE,
        "status": "active",
        "remove_basis": "inferred",
        "code_at": [AN, WG, S2],
        "rule_id": "minimum_wage.tokyo",
    },
]


def main() -> int:
    data = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = data["bridges"]
    pos = {r["id"]: i for i, r in enumerate(rows)}
    added = 0
    for r in ADD:
        if r["id"] in pos:
            rows[pos[r["id"]]] = r
            continue
        rows.append(r)
        added += 1
    LEDGER.write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    act = sum(1 for r in rows if r["status"] == "active")
    print(f"足した行 {added}・台帳 {len(rows)} 行(active {act})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
