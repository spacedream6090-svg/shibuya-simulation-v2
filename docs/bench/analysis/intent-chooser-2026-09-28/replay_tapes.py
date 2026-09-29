"""段 2a のリプレイ計測: 実 LLM テープの「対象」欄を新しい候補解決に通す(**エンジンは回さない**・GPU 不要)。

使い方(リポジトリの根から)::

    python docs/bench/analysis/intent-chooser-2026-09-28/replay_tapes.py \\
        --world data/world/v2 --out docs/bench/analysis/intent-chooser-2026-09-28/replay_tapes.json

手順(第270 ``v3_d114.py`` と同じ材料・同じ腕の選び方)
- テープ ``data/tape/c8_*/*/calls.parquet`` のうち **open 腕を除く**(vocab/hint)。語彙版は腕名の
  ``_v2`` で決める(それ以外は v1)。繰り延べ・空応答は数えない。
- 応答を現行パーサ ``parse_two_line(resp, 版)`` で読み、行為が **購入/食事** の呼だけを取る
  (並ぶ は語彙 v3 の語でテープに無い)。
- 体の現在セル = その呼の B2 の「現在地はセル<place_id>」。時刻 = 呼の ``tick``(月曜=day 0 の
  W7 営業行列で開閉を決める)。**棚在庫は見ない**(テープに在庫の状態が無い=全部在庫あり扱い)。
- ``engine.poi_target.TargetResolver``(既定の選び手 nearest)で (i)〜(iv) と候補 0 の理由を数える。
- **比較(従来の規則)**: 同じ呼を「現在セルの最小 id の POI(食事は飲食店の最小 id)」で解いたときの
  結果(対象なし/閉店/成立)と、新旧で対象の店が変わった件数・従来は成立していたが新しい規則では
  カテゴリ/名指しが合わず候補 0 になった件数も数える。
- 複製テープ(応答が同じ=第270 の注意 1)は結果の組で束ねた ``total_unique`` も出す。

出力は腕ごと+全体の件数(呼数・複製テープを含む=第270 と同じ数え方)。絶対パスは書かない。
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
ACTIONS = ("購入", "食事")


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
    from shibuya.engine.poi_target import TargetResolver, resolution_summary
    from shibuya.engine.processes.opening import build_open_matrix
    from shibuya.llm.parser import parse_two_line
    from shibuya.world import assets as WA
    from shibuya.world.state import World

    world = World.load_or_synthetic(args.world, n_cells=139, seed=1)
    pa_ = WA.load_process_assets(Path(args.world), world.assets)
    openm = build_open_matrix(world.n_poi, pa_.plan_poi, pa_.plan_day, pa_.plan_start, pa_.plan_end, 0)
    place_ids = pq.read_table(Path(args.world) / "w2_cells.parquet", columns=["place_id"]).column(0).to_pylist()
    cell_of = {str(p): i for i, p in enumerate(place_ids)}

    rows_out: list[dict[str, Any]] = []
    total = Counter()
    legacy_total: Counter = Counter()
    uniq: Counter = Counter()
    uniq_legacy: Counter = Counter()
    uniq_by_action: dict[str, Counter] = {a: Counter() for a in ACTIONS}
    uniq_tapes: list[str] = []
    seen_sig: set[str] = set()
    total_by_action: dict[str, Counter] = {a: Counter() for a in ACTIONS}
    ent_total = 0.0
    for p in sorted(glob.glob(args.tapes)):
        pp = Path(p)
        arm = pp.parent.name
        run = pp.parent.parent.name
        if "__open" in arm:
            continue
        ver = "v2" if arm.endswith("_v2") else "v1"
        blocks = pq.read_table(pp.parent / "blocks.parquet", columns=["block_id", "text"]).to_pydict()
        cell_by_block: dict[str, str] = {}
        for bid, tx in zip(blocks["block_id"], blocks["text"]):
            if "[B2 場所]" in tx:
                m = PLACE_RE.search(tx)
                if m:
                    cell_by_block[bid] = m.group(1)
        t = pq.read_table(p, columns=["tick", "response", "deferred", "block_ids"]).to_pydict()
        calls: dict[int, list[tuple[int, int, bool, Any]]] = {}
        n_no_cell = 0
        for tick, resp, d, bids in zip(t["tick"], t["response"], t["deferred"], t["block_ids"]):
            if d or not resp:
                continue
            pr = parse_two_line(resp, ver)
            if pr.action not in ACTIONS:
                continue
            place = next((cell_by_block[b] for b in bids if b in cell_by_block), None)
            cell = cell_of.get(place, -1) if place else -1
            if cell < 0:
                n_no_cell += 1
            code = C.ACT_EAT if pr.action == "食事" else C.ACT_BUY
            calls.setdefault(int(tick), []).append((cell, code, pr.action == "食事", pr.target))
        res = TargetResolver(world=world, chooser=NearestChooser(), seed=1)
        by_action: dict[str, Counter] = {a: Counter() for a in ACTIONS}
        legacy: Counter = Counter()
        with world.writable():
            for tick in sorted(calls):  # 逐次: テープの tick
                batch = calls[tick]
                world.pois.open_now[:] = openm[:, int(tick) % 1440].astype(np.int8)
                cell = np.array([b[0] for b in batch], dtype=np.int64)
                codes = np.array([b[1] for b in batch], dtype=np.int64)
                eat = np.array([b[2] for b in batch], dtype=bool)
                is_open = np.asarray(world.open_mask(int(tick)), dtype=bool)
                eatery = np.asarray(world.eatery_mask, dtype=bool)
                for k, b in enumerate(batch):  # 行為ごとの内訳(1 行ずつ数える)
                    before = Counter(res.stats)
                    new_t = int(res.resolve(_Agents(cell[k : k + 1]), tick, np.array([0]), codes[k : k + 1],
                                [b[3]], is_eat=eat[k : k + 1], is_buy_like=~eat[k : k + 1])[0])
                    diff = Counter(res.stats)
                    diff.subtract(before)
                    diff = Counter({kk: v for kk, v in diff.items() if v})  # 0 の鍵を落とす
                    act = "食事" if b[2] else "購入"
                    by_action[act].update(diff)
                    # 従来の規則(最小 id)
                    old_t = int(C._poi_in_cell(world, cell[k : k + 1], eatery if b[2] else None)[0])
                    if old_t < 0:
                        old = "not_in_eatery" if b[2] else "bad_target"
                    elif not is_open[old_t]:
                        old = "closed"
                    else:
                        old = "ok"
                    legacy[f"{act}:{old}"] += 1
                    new_ok = any(kk.startswith("resolved:") for kk in diff)
                    if old == "ok" and new_ok and new_t != old_t:
                        legacy[f"{act}:target_changed"] += 1
                    if old == "ok" and not new_ok:
                        legacy[f"{act}:ok_then_no_candidate"] += 1
                    if old == "closed" and new_ok:
                        legacy[f"{act}:closed_then_resolved"] += 1
            world.pois.open_now[:] = -1
        summ = resolution_summary(res.stats, res.entropy_sum)
        rows_out.append({
            "tape": f"{run}/{arm}", "vocab": ver, "no_cell_calls": n_no_cell,
            "summary": summ,
            "by_action": {a: dict(c) for a, c in by_action.items()},
            "legacy_min_id": dict(legacy),
        })
        total.update(res.stats)
        ent_total += res.entropy_sum
        legacy_total.update(legacy)
        sig = json.dumps(summ, sort_keys=True)
        if sig not in seen_sig:
            seen_sig.add(sig)
            uniq.update(res.stats)
            uniq_legacy.update(legacy)
            uniq_tapes.append(f"{run}/{arm}")
            for a in ACTIONS:
                uniq_by_action[a].update(by_action[a])
        for a in ACTIONS:
            total_by_action[a].update(by_action[a])
        print(f"{run}/{arm}: {summ['i_named']} / {summ['ii_category']} / {summ['iii_none']} / "
              f"{summ['iv_no_candidate']}", flush=True)
    doc = {
        "schema": "shibuya.bench/intent-chooser-2026-09-28/replay/1",
        "tapes": rows_out,
        "total": resolution_summary(total, ent_total),
        "total_by_action": {a: dict(c) for a, c in total_by_action.items()},
        "total_legacy_min_id": dict(legacy_total),
        "total_unique": resolution_summary(uniq, 0.0),
        "total_unique_by_action": {a: dict(c) for a, c in uniq_by_action.items()},
        "total_unique_legacy_min_id": dict(uniq_legacy),
        "unique_tapes": uniq_tapes,
        "note": "呼数(複製テープを含む)。棚在庫は見ない。月曜 day 0 の W7 営業行列。",
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
