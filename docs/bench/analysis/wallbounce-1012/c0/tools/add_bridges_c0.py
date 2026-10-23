"""第 1 期 1-7: つなぎの台帳に 1-7 の行を足す(行を足すだけ=既存の行は変えない)。``--check`` で足した後の台帳と同じか見る。

足す行(記録 c0/README.md §4):

- ``HD-engine.tools.contacts-…``: 1-7 で書いた docstring の ``expedient(本モジュール分)`` の見出し(第 4 形・見出し単位で
  1 行・id は 1-4 の規則=``HD-<モジュール>-<見出しの文の sha8>``)。
- ``BR-PHONE-TABLE-BLANK``: 店の番号の場所の表は空(版上げ 2 回目=計画 2-4 で OSM の ``phone`` タグから埋める)。

看板の文の作り物の印は 1-4 の ``BR-SIGNAGE-FICTION`` に結ぶ(行は足さない=``engine.tools.registry.SIGNAGE_BRIDGE``)。

使い方(リポの根で): ``python <この置き場>/add_bridges_c0.py [--check]``(src を ``PYTHONPATH`` に)。
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
    mod = "engine/tools/contacts"
    path = f"src/shibuya/{mod}.py"
    hits = [d for d in decls.values() if d.path == path and d.form == S.FORM_HEADING]
    if len(hits) != 1:
        raise SystemExit(f"{path} の見出しが 1 つでない({len(hits)})")
    d = hits[0]
    key = d.declared_in.rsplit(":", 1)[-1]
    rows.append({
        "id": f"HD-{mod.replace('/', '.')}-{key}",
        "what": f"{path} の docstring の見出し「{d.text}」の下の項 {d.items} 個",
        "why": "コードの宣言(第 4 形=docstring の expedient(…) の見出し・このファイルの 1 個目・見出し単位で 1 行=親の判断 第334)。"
               "第 1 期 1-7 で足した: 個人の連絡先の手段の印の 4 つ(通話・メッセージ・メール・職場の連絡)・初めの印の値(世帯の辺="
               "通話・メッセージ・メール/職場の辺=それに職場の連絡)・学校・常連・知人の辺は初めの印なし。手段ごとに「知っている」の"
               "錨は空欄(R-85 §5-1・§9)。外す段: 6-4(CT C1=連絡先を調べる・保存する・交換するが本人の行動になり、印を読む段)",
        "remove_at": "6-4",
        "declared_in": d.declared_in,
        "conf": "expedient",
        "since": SINCE,
        "status": "active",
        "remove_basis": "inferred",
    })
    rows.append({
        "id": "BR-PHONE-TABLE-BLANK",
        "what": "店の番号の場所の表(engine.tools.places.PhoneTable)は空。読み口 phone_of は全部 None。OSM の phone タグを持つ要素の数は数えた(記録 c0/README.md §5)。w6_poi.parquet には OSM の番号の列が無いが、元の JSON(shibuya_osm_wide_v8.json の pois)の行の並びで OSM の番号に結べる見込み(2,259 行・phone 477 行=記録 c0/README.md §5)。2-4 で確かめる",
        "why": "口の約束 1-7〔決定(回答 10-13b §3)〕店の番号の場所の表は OSM の phone タグから作る(ライセンスを増やさない)。発注(第 1 期 1-7)=データの資産は本段では作らず、構築の段(W6 の POI)に欄を足す形で版上げ 2 回目に埋める(OSM の番号で結べない行の扱いはその前に決める)。外す段: 2-4(版上げ 2 回目)",
        "remove_at": "2-4",
        "declared_in": "docs/design/v2-foundation-contracts-2026-10-13.md §1-7",
        "conf": "expedient",
        "since": SINCE,
        "status": "active",
        "remove_basis": "inferred",
        "code_at": ["src/shibuya/engine/tools/places.py"],
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
