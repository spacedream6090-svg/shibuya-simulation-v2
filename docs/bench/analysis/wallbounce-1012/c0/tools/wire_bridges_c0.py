"""第 1 期 1-7(1-8 への結線): つなぎの台帳の行の出し入れ(``--check`` で済んでいるか見る)。

- ``HD-engine.decision.layer-2d3672ba``(1-8 J0 の見出し「expedient(周りが示すできること=1-7 の道具の台帳で外す)」)を
  ``status: removed`` にする(外した段 1-7・2026-10-14。候補の源 affordance は道具の台帳から読む形に結んだ。場所の種類と
  営業時間と知覚の読みは世界の状態の読み=つなぎではない)。ほかの欄は変えない(``why`` の末尾に外した記録を足す)。
- 新しい見出し「expedient(道具を使う行為の語は判断の語彙に無い=道具 → 語の表は空・6-4 C1 で語を足す)」の行を 1 本足す
  (第 4 形・id は 1-4 の規則=``HD-<モジュール>-<見出しの文の sha8>``・外す段 6-4・inferred)。

使い方(リポの根で): ``python <この置き場>/wire_bridges_c0.py [--check]``(src を ``PYTHONPATH`` に)。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
SINCE = "2026-10-14"
OLD = "HD-engine.decision.layer-2d3672ba"
REMOVED_NOTE = ("〔2026-10-14・第 1 期 1-7 で外した(status removed)〕候補の源 affordance は道具の台帳(Fixtures.tools の "
                "ToolRegistry)から読む形に結んだ。場所の種類と営業時間と知覚の読みは世界の状態の読み=つなぎではない(親の判断)。"
                "道具を使う行為の語が語彙に無い点は新しい見出しの行(外す段 6-4)へ")


def new_row() -> dict:
    from shibuya.engine.bridging import scan as S

    path = "src/shibuya/engine/decision/layer.py"
    hits = [d for d in S.scan_package() if d.path == path and d.form == S.FORM_HEADING]
    if len(hits) != 1:
        raise SystemExit(f"{path} の見出しが 1 つでない({len(hits)})")
    d = hits[0]
    key = d.declared_in.rsplit(":", 1)[-1]
    return {
        "id": f"HD-engine.decision.layer-{key}",
        "what": f"{path} の docstring の見出し「{d.text}」の下の項 {d.items} 個: 道具を使う行為の語は判断の語彙に無い"
                "=道具 → 語の表(engine.tools.registry.TOOL_ACTION_WORDS)は空",
        "why": "コードの宣言(第 4 形=docstring の expedient(…) の見出し・見出し単位で 1 行=親の判断 第334)。第 1 期 1-7 の 1-8 への"
               "結線で足した: 候補の源 affordance(周りが示すできること)は道具の台帳から読む形になったが、道具を使う行為の語"
               "(看板を読む・電話をかける等)は判断の語彙に無い=6-4 C1 で語を足すまで候補に出ない(持ち物の台帳も無い=要るものの"
               "ある道具は満たされない扱い)。外す段: 6-4(CT C1)",
        "remove_at": "6-4",
        "declared_in": d.declared_in,
        "conf": "expedient",
        "since": SINCE,
        "status": "active",
        "remove_basis": "inferred",
    }


def apply(doc: dict) -> dict:
    rows = doc["bridges"]
    old = [r for r in rows if r["id"] == OLD]
    if len(old) != 1:
        raise SystemExit(f"{OLD} が台帳に 1 行でない({len(old)})")
    o = old[0]
    o["status"] = "removed"
    if REMOVED_NOTE not in o["why"]:
        o["why"] = o["why"] + "。" + REMOVED_NOTE
    nr = new_row()
    if not any(r["id"] == nr["id"] for r in rows):
        rows.append(nr)
    return doc


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    if args.check:
        want = apply(json.loads(json.dumps(doc)))
        ok = want == doc
        print("台帳は結線の後の形" if ok else "違う(まだ出し入れしていない)")
        return 0 if ok else 1
    doc = apply(doc)
    LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"台帳 {len(doc['bridges'])} 行(active {sum(1 for r in doc['bridges'] if r['status'] == 'active')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
