"""第 1 期 1-5: つなぎの台帳に 1-5 の行を足す(行を足すだけ=既存の行は変えない)。``--check`` で足した後の台帳と同じか見る。

足す行(記録 r15/README.md §3):

- ``HD-engine.rights.initial-…``・``HD-engine.rights.record-…``: 1-5 で書いた docstring の ``expedient(本モジュール分)``
  の見出し(第 4 形・見出し単位で 1 行・id は 1-4 の規則=``HD-<モジュール>-<見出しの文の sha8>``)。
- ``BR-RIGHTS-LICENCE-BLANK``: 営業許可の行は 0(空欄)。
- ``BR-RIGHTS-DWELLING-BLANK``: 住まいの行は 0(空欄)。

家賃の空欄は 1-4 の ``BR-RENT-BLANK`` に結ぶ(行は足さない=``engine.rights.initial.BLANK_BRIDGES``)。

使い方(リポの根で): ``python <この置き場>/add_bridges_r15.py [--check]``(src を ``PYTHONPATH`` に)。
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


def new_rows() -> list[dict]:
    from shibuya.engine.bridging import scan as S

    decls = {d.declared_in: d for d in S.scan_package()}
    rows: list[dict] = []
    for mod, why in (
        ("engine/rights/initial",
         "コードの宣言(第 4 形=docstring の expedient(…) の見出し・このファイルの 1 個目・見出し単位で 1 行=親の判断 第334)。"
         "第 1 期 1-5 で足した: 権利台帳の最初の中身の近似(担当従業者の丸振り=HEAD の opening._assign_staff の規則を移した・"
         "店の賃借=すべての POI を店とし区画は POI の番号で代用・最初の行の時刻は開始前から終わりなし)。外す段: 4-1(組織の"
         "データ=人+関係+権利台帳。丸振りの項は HD-engine.processes.opening の項 1 と同じつなぎ=検収 L6 でそろえた。"
         "賃借と時刻の項は 4-2 の中身と一緒に外す)"),
        ("engine/rights/record",
         "コードの宣言(第 4 形=docstring の expedient(…) の見出し・このファイルの 1 個目・見出し単位で 1 行=親の判断 第334)。"
         "第 1 期 1-5 で足した: 役割語の権利の判定(雇用の行を 1 つでも持てば許可・対象の店を見ない・職務の語は判定しない)と"
         "許可のない行動の出来事の欄。外す段: 6-6 ②(人の仕事を働く人のエージェントへ=役割語の効果と対象の解決を作る段)"),
    ):
        path = f"src/shibuya/{mod}.py"
        hits = [d for k, d in decls.items() if d.path == path and d.form == S.FORM_HEADING]
        if len(hits) != 1:
            raise SystemExit(f"{path} の見出しが 1 つでない({len(hits)})")
        d = hits[0]
        key = d.declared_in.rsplit(":", 1)[-1]
        rows.append({
            "id": f"HD-{mod.replace('/', '.')}-{key}",
            "what": f"{path} の docstring の見出し「{d.text}」の下の項 {d.items} 個",
            "why": why,
            "remove_at": "4-1" if mod.endswith("initial") else "6-6",
            "declared_in": d.declared_in,
            "conf": "expedient",
            "since": SINCE,
            "status": "active",
            "remove_basis": "inferred",
        })
    rows.append({
        "id": "BR-RIGHTS-LICENCE-BLANK",
        "what": "権利台帳の営業許可(licence)の行は 0(空欄)。渋谷区の「食品等営業許可・届出一覧」(SHIBUYA OPEN DATA・"
                "CC BY 4.0・39,304 件)は記録の上ではあるが取得していない。POI と突き合わせる規則も決まっていない",
        "why": "口の約束 1-5〔決定(回答 10-13b §3)〕営業許可のオープンデータは許可の一覧の中で探し、無ければ空。記録(R-76 #17・"
               "R-106 §2-1 の表)では一覧はあるが data/ に取得の記録が無い=空にして宣言(取得は親に頼む・記録 r15/README.md §2)。"
               "中身は 4-2(権利台帳の中身=営業許可・計画 4-2)",
        "remove_at": "4-2",
        "declared_in": "docs/design/v2-foundation-contracts-2026-10-13.md §1-5",
        "conf": "expedient",
        "since": SINCE,
        "status": "active",
        "remove_basis": "plan",
        "code_at": ["src/shibuya/engine/rights/initial.py"],
    })
    rows.append({
        "id": "BR-RIGHTS-DWELLING-BLANK",
        "what": "権利台帳の住まい(持ち家=所有・借家=賃借)の行は 0(空欄)。国勢調査の住宅の所有の関係(表 18-4・町丁目)は"
                "表の場所だけ分かり、値は未取得",
        "why": "計画 1-5 の最初の中身「住まい=国勢調査の割合」(決定 10-12 §4-5 CP4)。割合の出どころが無いので行を作らない"
               "(R-106 §2-1 の表 #40 △=値は未取得)。発注: 住まいの権利は 4-2 で(賃貸借=計画 4-2・持ち家の所有は計画の文に"
               "段が無い=実装役が当てた)",
        "remove_at": "4-2",
        "declared_in": "docs/design/v2-implementation-plan-2026-10-12.md 第 1 期 1-5",
        "conf": "expedient",
        "since": SINCE,
        "status": "active",
        "remove_basis": "inferred",
        "code_at": ["src/shibuya/engine/rights/initial.py"],
    })
    return rows


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    raw = LEDGER.read_text(encoding="utf-8")
    doc = json.loads(raw)
    have = {r["id"] for r in doc["bridges"]}
    add = new_rows()
    if args.check:
        missing = [r["id"] for r in add if r["id"] not in have]
        same = all(r in doc["bridges"] for r in add)
        print("足す行が台帳にある" if not missing and same else f"違う(無い {missing}・中身が同じ {same})")
        return 0 if not missing and same else 1
    dup = [r["id"] for r in add if r["id"] in have]
    if dup:
        raise SystemExit(f"もう台帳にある行: {dup}")
    doc["bridges"].extend(add)
    LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"{len(add)} 行を足した(台帳 {len(doc['bridges'])} 行)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
