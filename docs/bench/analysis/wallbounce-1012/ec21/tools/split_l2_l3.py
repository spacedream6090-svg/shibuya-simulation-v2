"""第 2 期 2-1(ec21・検収の直し): 来街者の預金(L2)と銀行の支店(L3)の動いた量を分ける道具。

腕 on(全部)の 2 日のラン(``stage2_two_day.py one`` と同じ構成)を、ATM の表だけ検収の前の作り方(``amenity=atm`` か
``atm=yes``・営業時間の無い点は 24 時間=銀行の支店の既定の時間なし)に戻して 1 本回す(切替口 ``set_atm_table``)。
検収の前の版(``two_day_ec21_on16.json``)→ この本=L2(と A1=呼の配線は腕 legacy の挙動を変えない)の分・この本 →
検収の直しの後の版(``two_day_ec21_fix.json``)=L3 の分。

    PYTHONPATH=src python $D/split_l2_l3.py --out $W/split_l2_l3.json

絶対パスは JSON に書かない。逐次ループ宣言: なし(道具)。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()


def old_atm_table(world):  # noqa: ANN001, ANN201
    """検収の前の作り方(``amenity=atm`` か ``atm=yes``・営業時間の無い点と読めない点は 24 時間)。"""
    import math

    import numpy as np

    from shibuya.engine import economy_stage2 as ES2
    from shibuya.engine.calendar import resolve_repo_path

    tp = resolve_repo_path(ES2.OSM_TAGS_RELPATH)
    hp = resolve_repo_path(ES2.OSM_HOURS_RELPATH)
    by, n_cells = ES2._cell_lookup(world)
    els = json.loads(tp.read_text(encoding="utf-8")).get("elements", [])
    hours_map = {}
    for e in json.loads(hp.read_text(encoding="utf-8")).get("elements", []):
        oh = (e.get("tags") or {}).get("opening_hours")
        if oh:
            hours_map[(str(e.get("type")), int(e.get("id")))] = str(oh)
    full = ES2.parse_opening_hours("24/7")
    cells, kinds, hours, hfrom = [], [], [], []
    for e in els:
        t = e.get("tags") or {}
        if not (t.get("amenity") == "atm" or t.get("atm") == "yes"):
            continue
        kind = 0 if t.get("amenity") == "atm" else (2 if t.get("amenity") == "bank" else 1)
        lat, lon = (float(e["lat"]), float(e["lon"])) if "lat" in e else (float(e["center"]["lat"]),
                                                                          float(e["center"]["lon"]))
        x = (lon - ES2.ORIGIN_LATLON[1]) * ES2.M_PER_DEG_LON
        y = (lat - ES2.ORIGIN_LATLON[0]) * ES2.M_PER_DEG_LAT
        cand = sorted(by.get((int(math.floor(x / ES2.CELL_M)), int(math.floor(y / ES2.CELL_M))), []),
                      key=lambda bc: (bc[0] != 0, -bc[0]))
        if not cand:
            continue
        oh = t.get("opening_hours") or hours_map.get((str(e.get("type")), int(e.get("id"))))
        parsed = ES2.parse_opening_hours(oh) if oh else None
        cells.append(int(cand[0][1]))
        kinds.append(kind)
        hours.append(full if parsed is None else parsed)
        hfrom.append(0 if parsed is not None else 2)
    return ES2.AtmTable(cell=np.asarray(cells, dtype=np.int64), kind=np.asarray(kinds, dtype=np.int8),
                        hours=np.stack(hours).astype(np.int16), hours_from=np.asarray(hfrom, dtype=np.int8),
                        n_cells=n_cells)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    from shibuya.engine import economy_stage2 as ES2
    from shibuya.world.state import World

    sys.path.insert(0, str(HERE.parent))
    import stage2_two_day as T

    ES2.set_atm_table(old_atm_table(World.load("data/world/v2")))
    import contextlib
    import io

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        T.main(["one", "--arm", "on", "--parts", ""])
    row = json.loads(buf.getvalue().strip().splitlines()[-1])
    row["atm_table"] = "検収の前の作り方(amenity=atm か atm=yes・時間の無い点は 24 時間)"
    Path(a.out).write_text(json.dumps(row, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(row["final"], row["calls"], (row.get("stage2") or {}).get("withdraw"), (row.get("stage2") or {}).get("atms"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
