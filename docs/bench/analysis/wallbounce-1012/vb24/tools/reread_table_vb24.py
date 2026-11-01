"""第 2 期 2-4: 2-2 の 11c の読み直しの表(``prox22/tools/reread_11c.py table`` の JSON)から主な量を Markdown の表にする。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/reread_table_vb24.py <v2_reread_11c.json> [--cols distance/node,cell/node]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROWS = (
    ("会話の成立時の距離が 2 m 超の割合(関係 on)", "conv_open_share_gt_2m", "rel_on"),
    ("同・10 m 超の割合(関係 on)", "conv_open_share_gt_10m", "rel_on"),
    ("同・最大[m](関係 on)", "conv_open_max_m", "rel_on"),
    ("会話のセッション(関係 off / on)", "sessions", None),
    ("知人出現の起床の呼(関係 on)", "acq_wake_calls", "rel_on"),
    ("知人出現の時点の距離の中央値[m](関係 on)", "acq_appear_distance_p50", "rel_on"),
    ("B5 の近接行の項/描画(関係 on)", "b5_items_per_render(rel_on)", "rel_on"),
    ("B5 の近接行の 2 m 内の割合(関係 on)", "b5_share_le_2m(rel_on)", "rel_on"),
    ("B5 の近接行の 10 m 超の割合(関係 on)", "b5_share_gt_10m(rel_on)", "rel_on"),
    ("B5 の単位の在室人数の最大(絞った単位・関係 on)", "b5_unit_max_in_room", "rel_on"),
    ("同・絞る前の在席の印の最大(関係 on)", "b5_unit_max_in_room_raw", "rel_on"),
    ("在席の体 × 刻みのうち店のセルの外(関係 on)", "b5_seated_out_of_store_cell", "rel_on"),
    ("同じ点に重なる体の最大(関係 on)", "same_xy_max", "rel_on"),
)


def _v(x):
    if isinstance(x, float):
        return f"{x:.4g}"
    if isinstance(x, int):
        return f"{x:,}"
    return "—" if x is None else str(x)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("path")
    ap.add_argument("--cols", default="distance/node,cell/node")
    a = ap.parse_args(argv)
    T = json.loads(Path(a.path).read_text(encoding="utf-8"))["tables"]
    cols = [c for c in a.cols.split(",") if c in T]
    head = ["量"] + [f"{c} {p}" for c in cols for p in ("mock", "classical")]
    print("| " + " | ".join(head) + " |")
    print("|" + "---|" * len(head))
    for label, key, arm in ROWS:
        cells = []
        for c in cols:
            for p in ("mock", "classical"):
                t = T[c].get(p, {})
                if key == "sessions":
                    cells.append(f"{_v(t.get('sessions_off', {}).get('off'))} / {_v(t.get('sessions_rel_on', {}).get('rel_on'))}")
                    continue
                v = t.get(key, {})
                cells.append(_v(v.get(arm) if isinstance(v, dict) else v))
        print(f"| {label} | " + " | ".join(cells) + " |")
    return 0


if __name__ == "__main__":
    sys.exit(main())
