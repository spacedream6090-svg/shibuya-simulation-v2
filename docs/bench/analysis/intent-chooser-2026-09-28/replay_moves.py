"""段 2b のリプレイ計測: 実 LLM テープの**移動**の「対象」欄を新しい行き先の解決に通す(エンジンは回さない)。

使い方(リポジトリの根から)::

    python docs/bench/analysis/intent-chooser-2026-09-28/replay_moves.py \\
        --world data/world/v2 --out docs/bench/analysis/intent-chooser-2026-09-28/replay_moves.json

手順(``replay_tapes.py`` と同じ材料・腕・束ね方)
- open 腕を除く ``data/tape/c8_*/*/calls.parquet``。語彙版は腕名の ``_v2`` で決める(それ以外は v1)。
- 行為が **移動** の呼(段0 辞書で 移動 に写る語=探す・探索・行く… を含む=エンジンと同じ写像)。
- 現在セル = B2 の「現在地はセル…」・開閉 = 呼の tick の月曜(day 0)の W7 営業行列。
- ``TargetResolver.resolve_move``(既定の選び手 nearest・近傍 R=5)で内訳を数える。
  **従来の規則**(このテープのラン=語彙 v1/v2・注意の腕なし)では移動の行き先は常に
  「職場/自宅のうち今いない方」=**新しい規則で対象欄が行き先を決めた呼**(セル/名指し/目印/
  カテゴリ)はすべて「従来は既定に落ちていた」呼。
- 内容が同じテープは結果の組で束ねる(``total_unique``)。絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import glob
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

PLACE_RE = re.compile(r"現在地はセル([^\s()()]+)")


class _Reg:
    def __init__(self, cell: np.ndarray) -> None:
        self.cell = cell
        self.node = np.zeros(cell.size, dtype=np.int64)
        self.hunger = np.zeros(cell.size, dtype=np.int64)


class _Agents:
    def __init__(self, cell: np.ndarray) -> None:
        self.registry = _Reg(cell)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--tapes", default="data/tape/c8_*/*/calls.parquet")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    from shibuya.engine import commit as C
    from shibuya.engine.chooser import NearestChooser
    from shibuya.engine.poi_target import TargetResolver, move_resolution_summary
    from shibuya.engine.processes.opening import build_open_matrix
    from shibuya.llm.parser import parse_two_line
    from shibuya.llm.undefined import map_synonym
    from shibuya.world import assets as WA
    from shibuya.world.state import World

    world = World.load_or_synthetic(args.world, n_cells=139, seed=1)
    pa_ = WA.load_process_assets(Path(args.world), world.assets)
    openm = build_open_matrix(world.n_poi, pa_.plan_poi, pa_.plan_day, pa_.plan_start, pa_.plan_end, 0)
    place_ids = pq.read_table(Path(args.world) / "w2_cells.parquet", columns=["place_id"]).column(0).to_pylist()
    cell_of = {str(p): i for i, p in enumerate(place_ids)}

    rows_out: list[dict[str, Any]] = []
    total: Counter = Counter()
    uniq: Counter = Counter()
    uniq_tapes: list[str] = []
    seen: set[str] = set()
    for p in sorted(glob.glob(args.tapes)):
        pp = Path(p)
        arm, run = pp.parent.name, pp.parent.parent.name
        if "__open" in arm:
            continue
        ver = "v2" if arm.endswith("_v2") else "v1"
        blocks = pq.read_table(pp.parent / "blocks.parquet", columns=["block_id", "text"]).to_pydict()
        cell_by_block = {}
        for bid, tx in zip(blocks["block_id"], blocks["text"]):
            if "[B2 場所]" in tx:
                m = PLACE_RE.search(tx)
                if m:
                    cell_by_block[bid] = m.group(1)
        t = pq.read_table(p, columns=["tick", "response", "deferred", "block_ids"]).to_pydict()
        calls: dict[int, list[tuple[int, Any, str]]] = {}
        via = Counter()
        for tick, resp, d, bids in zip(t["tick"], t["response"], t["deferred"], t["block_ids"]):
            if d or not resp:
                continue
            pr = parse_two_line(resp, ver)
            act = pr.action
            if act is None and pr.raw_action:
                act = map_synonym(pr.raw_action, None, ver)[0]
                if act == "移動":
                    via["synonym"] += 1
            if act != "移動":
                continue
            place = next((cell_by_block[b] for b in bids if b in cell_by_block), None)
            cell = cell_of.get(place, -1) if place else -1
            calls.setdefault(int(tick), []).append((cell, pr.target, pr.raw_action))
        res = TargetResolver(world=world, chooser=NearestChooser(), seed=1)
        with world.writable():
            for tick in sorted(calls):  # 逐次: テープの tick
                batch = calls[tick]
                world.pois.open_now[:] = openm[:, int(tick) % 1440].astype(np.int8)
                cell = np.array([b[0] for b in batch], dtype=np.int64)
                res.resolve_move(
                    _Agents(cell), tick, np.arange(len(batch)),
                    np.full(len(batch), C.ACT_MOVE), [b[1] for b in batch],
                    np.ones(len(batch), dtype=bool),
                )
            world.pois.open_now[:] = -1
        summ = move_resolution_summary(res.move_stats)
        summ["moves"] = int(sum(len(v) for v in calls.values()))
        summ["via_synonym"] = int(via["synonym"])
        rows_out.append({"tape": f"{run}/{arm}", "vocab": ver, "summary": summ})
        total.update(res.move_stats)
        total["moves"] += summ["moves"]
        sig = json.dumps(summ, sort_keys=True)
        if sig not in seen:
            seen.add(sig)
            uniq.update(res.move_stats)
            uniq["moves"] += summ["moves"]
            uniq_tapes.append(f"{run}/{arm}")
        print(f"{run}/{arm}: moves {summ['moves']:,} cell {summ['cell']} named {summ['named']}+"
              f"{summ['named_landmark']} cat {summ['category_in_cell']}/{summ['category_visible']}/"
              f"{summ['category_nearby']} none {summ['none_default']} bad {summ['bad_target']}", flush=True)

    def final(c: Counter) -> dict[str, Any]:
        s = move_resolution_summary(c)
        s["moves"] = int(c["moves"])
        decided = s["cell"] + s["named"] + s["named_landmark"] + s["category_in_cell"] + \
            s["category_visible"] + s["category_nearby"]
        s["decided_by_target_field"] = int(decided)
        s["was_default_now_bad_target"] = int(sum(s["bad_target"].values()))
        return s

    doc = {
        "schema": "shibuya.bench/intent-chooser-2026-09-28/replay-moves/1",
        "tapes": rows_out,
        "total": final(total),
        "total_unique": final(uniq),
        "unique_tapes": uniq_tapes,
        "note": "呼数(複製テープを含む=total)。月曜 day 0 の W7 営業行列。従来の行き先は常に職場/自宅の既定。",
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
