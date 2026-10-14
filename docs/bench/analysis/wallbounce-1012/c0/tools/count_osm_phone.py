"""第 1 期 1-7: OSM の ``phone`` タグを持つ要素の数を数える(店の番号の場所の表の出どころ=回答 10-13b §3)。

数える規則は ``shibuya.engine.tools.places.osm_phone_of``(``phone`` を先に・無ければ ``contact:phone``)。読むのは手元の
Overpass の抽出(ODbL・ライセンス台帳にある既存の取得物)だけで、ネットは使わない:

- ``data/realworld/osm/poi_tags_overpass_20260928.json``(amenity・shop・leisure・tourism・office・craft・healthcare の
  要素=W6 の POI の元と同じ範囲の取り直し)
- ``data/realworld/osm/poi_opening_hours_overpass_20260907.json``(W7 の営業時間の取得)
- ``data/realworld/osm/shibuya_osm_wide_v8.json`` の ``pois``(W6 の POI の元・タグがあれば)

使い方(リポの根で・src を ``PYTHONPATH`` に): ``python <この置き場>/count_osm_phone.py [--out <json>]``。
絶対パスは出力に書かない。
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
OSM = REPO / "data" / "realworld" / "osm"
FILES = ("poi_tags_overpass_20260928.json", "poi_opening_hours_overpass_20260907.json")


def _count_elements(elements: list, phone_of) -> dict:  # noqa: ANN001
    n = len(elements)
    by_key: Counter = Counter()
    hit = 0
    by_type: Counter = Counter()
    by_main: Counter = Counter()
    for e in elements:
        tags = e.get("tags") or {}
        if phone_of(tags) is None:
            continue
        hit += 1
        by_type[str(e.get("type", "?"))] += 1
        for k in ("phone", "contact:phone"):
            if isinstance(tags.get(k), str) and tags[k].strip():
                by_key[k] += 1
        main = next((k for k in ("amenity", "shop", "tourism", "leisure", "office", "craft", "healthcare") if k in tags),
                    "other")
        by_main[main] += 1
    return {"elements": n, "with_phone": hit, "by_tag": dict(sorted(by_key.items())), "by_type": dict(sorted(by_type.items())),
            "by_main_key": dict(sorted(by_main.items())), "share": round(hit / n, 4) if n else None}


def main(argv: list[str] | None = None) -> int:
    from shibuya.engine.tools.places import osm_phone_of

    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="")
    args = ap.parse_args(argv)
    out: dict = {"rule": "engine.tools.places.osm_phone_of(phone → contact:phone)", "files": {}}
    for name in FILES:
        p = OSM / name
        if not p.exists():
            out["files"][name] = None
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        out["files"][name] = _count_elements(list(d.get("elements") or []), osm_phone_of)
    wide = OSM / "shibuya_osm_wide_v8.json"
    if wide.exists():
        d = json.loads(wide.read_text(encoding="utf-8"))
        pois = d.get("pois") or []
        sample = pois[0] if pois else {}
        keys = sorted(sample.keys()) if isinstance(sample, dict) else []
        tags_field = "tags" if "tags" in keys else None
        n_phone = 0
        if tags_field:
            n_phone = sum(1 for x in pois if osm_phone_of(x.get(tags_field)) is not None)
        else:
            n_phone = sum(1 for x in pois if isinstance(x, dict) and osm_phone_of(x) is not None)
        out["files"]["shibuya_osm_wide_v8.json:pois"] = {"elements": len(pois), "with_phone": n_phone,
                                                         "poi_keys": keys}
        # W6 の POI(行 i=wide_v8 の pois[i]・名で全行を確かめる)の id ``p_n<node>``・``p_w<way>`` から OSM の要素へ結ぶ
        # (2-4 で場所の表を埋めるときの突き合わせの材料=名前と位置で突き合わせなくても番号で結べる行の数)
        tags_p = OSM / FILES[0]
        w6_p = REPO / "data" / "world" / "v2" / "w6_poi.parquet"
        if tags_p.exists() and w6_p.exists():
            import pyarrow.parquet as pq

            kinds = {"n": "node", "w": "way", "r": "relation"}

            def key(s: str):  # noqa: ANN202
                return (kinds[s[2]], int(s[3:])) if s.startswith("p_") and s[2:3] in kinds and s[3:].isdigit() else None

            els = {(e["type"], e["id"]): e for e in json.loads(tags_p.read_text(encoding="utf-8")).get("elements") or []}
            names = pq.read_table(w6_p, columns=["name"]).column("name").to_pylist()
            same = sum(1 for i, x in enumerate(pois) if i < len(names) and names[i] == x.get("name"))
            ks = [key(str(x.get("id", ""))) for x in pois]
            matched = [k for k in ks if k is not None and k in els]
            out["w6_match"] = {
                "w6_rows": len(names), "same_name_at_same_row": same,
                "osm_id_rows": sum(1 for k in ks if k is not None), "non_osm_rows": sum(1 for k in ks if k is None),
                "matched_in_poi_tags_20260928": len(matched),
                "matched_with_phone": sum(1 for k in matched if osm_phone_of(els[k].get("tags")) is not None),
            }
    txt = json.dumps(out, ensure_ascii=False, indent=1)
    print(txt)
    if args.out:
        Path(args.out).write_text(txt + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
