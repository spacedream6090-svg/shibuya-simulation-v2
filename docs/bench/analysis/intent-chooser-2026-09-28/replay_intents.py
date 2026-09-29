"""段 2c のリプレイ計測: 実 LLM テープの購入/食事/会話/就寝のうち「対象が現在セルに無い」呼を数え、
意図になる件数・行き先までの距離(``cell_dist``)・歩数(経路のノード数=1 tick 1 ノード)を出す
(**エンジンは回さない**・GPU 不要)。

使い方(リポジトリの根から)::

    python docs/bench/analysis/intent-chooser-2026-09-28/replay_intents.py \\
        --world data/world/v2 --out docs/bench/analysis/intent-chooser-2026-09-28/replay_intents.json

材料と束ね方は ``replay_tapes.py`` と同じ(open 腕を除く 23 本・内容が同じテープは結果の組で束ねて
``total_unique``)。現在セル=B2 の「現在地はセル…」・開閉=呼の tick の月曜(day 0)の W7 営業行列・
**棚在庫は見ない**(全部在庫あり扱い)。

- **購入/食事**: ``TargetResolver.resolve(..., intent_out=…)`` で (a) 名指しの店がセルに無い呼の内訳
  (見えて営業中=意図になる / 見えるが閉店=即時の ``CLOSED``(親決定 Q21)/ 見えない / 意図に合わない /
  域外)と (b) カテゴリ語で現在セルに営業中の候補が
  無く近傍から選べた呼(=意図になる)を数える。意図の行き先=選んだ店のセル。
- **会話**: 対象が人 ID の呼。相手の居場所=**同じテープの相手自身の直近の呼の B2**(呼の tick 以前で
  最も新しいもの・60 tick より古ければ「不明」)=近似(宣言)。別セルなら意図になる。
- **就寝**: 寝床=自宅セル。自宅は**いまのコードで同じ体数・seed の母集団を組み直した値**
  (``cli.run(ticks=1)`` の ``schedule.home_cell``・テープのランと同じ W16/W17 の前提=近似・宣言)。
  自宅が別セルなら意図になる・域外常住(−1)は意図にならない。
- 歩数: 出発セルの代表ノード → 行き先セルの代表ノードの経路のノード数(``WalkGraph.step_once`` を
  着くまで回す)=node 幾何の 1 tick 1 ノードで「着くまでの tick」。``INTENT_MAX_TICKS``(60)以内の割合。

絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import bisect
import glob
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

PLACE_RE = re.compile(r"現在地はセル([^\s()()]+)")
SEED_RE = re.compile(r"_s(\d+)$")
DIST_BINS_M = (0, 100, 200, 400, 800, 1600)
HOP_BINS = (0, 10, 20, 30, 45, 60)
PARTNER_STALE_TICKS = 60
MAX_TICKS = 60


class _Reg:
    def __init__(self, cell: np.ndarray) -> None:
        self.cell = cell
        self.node = np.zeros(cell.size, dtype=np.int64)
        self.hunger = np.zeros(cell.size, dtype=np.int64)


class _Agents:
    def __init__(self, cell: np.ndarray) -> None:
        self.registry = _Reg(cell)


def _bin(v: int, bins: tuple[int, ...]) -> str:
    for lo, hi in zip(bins, bins[1:]):
        if lo <= v < hi:
            return f"{lo}-{hi}"
    return f"{bins[-1]}+"


class _Hops:
    """セル → セルの歩数(代表ノード間の経路のノード数・記憶つき)。"""

    def __init__(self, world: Any) -> None:
        self.w = world
        self.rep = np.asarray(world.assets.cell_rep_node, dtype=np.int64)
        self.memo: dict[tuple[int, int], int] = {}

    def __call__(self, a: int, b: int) -> int:
        key = (int(a), int(b))
        got = self.memo.get(key)
        if got is not None:
            return got
        node = np.array([self.rep[a]], dtype=np.int64)
        tgt = np.array([self.rep[b]], dtype=np.int64)
        k = 0
        if node[0] == tgt[0]:
            self.memo[key] = 0
            return 0
        while k < 2_000:  # 逐次: 経路のノード数ぶん
            nn, arr = self.w.graph.step_once(node, tgt)
            k += 1
            if bool(arr[0]):
                break
            if int(nn[0]) == int(node[0]):
                k = -1
                break
            node = np.asarray(nn, dtype=np.int64)
        self.memo[key] = k
        return k


def _trip(c: Counter, prefix: str, dist: int, hops: int) -> None:
    c[f"{prefix}:n"] += 1
    c[f"{prefix}:dist:{_bin(dist, DIST_BINS_M)}"] += 1
    c[f"{prefix}:dist_sum"] += int(dist)
    if hops < 0:
        c[f"{prefix}:no_route"] += 1
        return
    c[f"{prefix}:hops:{_bin(hops, HOP_BINS)}"] += 1
    c[f"{prefix}:hops_sum"] += int(hops)
    c[f"{prefix}:hops_n"] += 1
    if hops <= MAX_TICKS:
        c[f"{prefix}:within_max"] += 1


def _trip_summary(c: Counter, prefix: str) -> dict[str, Any]:
    n = int(c.get(f"{prefix}:n", 0))
    hn = int(c.get(f"{prefix}:hops_n", 0))
    return {
        "n": n,
        "dist_m": {_l: int(c.get(f"{prefix}:dist:{_l}", 0)) for _l in _labels(DIST_BINS_M)},
        "dist_mean_m": round(c.get(f"{prefix}:dist_sum", 0) / n, 1) if n else 0.0,
        "hops": {_l: int(c.get(f"{prefix}:hops:{_l}", 0)) for _l in _labels(HOP_BINS)},
        "hops_mean": round(c.get(f"{prefix}:hops_sum", 0) / hn, 2) if hn else 0.0,
        "no_route": int(c.get(f"{prefix}:no_route", 0)),
        "within_max_ticks": int(c.get(f"{prefix}:within_max", 0)),
        "within_max_ticks_share": round(c.get(f"{prefix}:within_max", 0) / n, 4) if n else 0.0,
    }


def _labels(bins: tuple[int, ...]) -> list[str]:
    return [f"{lo}-{hi}" for lo, hi in zip(bins, bins[1:])] + [f"{bins[-1]}+"]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--tapes", default="data/tape/c8_*/*/calls.parquet")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    from shibuya import cli
    from shibuya.engine import commit as C
    from shibuya.engine.chooser import NearestChooser
    from shibuya.engine.poi_target import TargetResolver
    from shibuya.engine.processes.opening import build_open_matrix
    from shibuya.llm.parser import parse_two_line
    from shibuya.world import assets as WA
    from shibuya.world.state import World

    world = World.load_or_synthetic(args.world, n_cells=139, seed=1)
    pa_ = WA.load_process_assets(Path(args.world), world.assets)
    openm = build_open_matrix(world.n_poi, pa_.plan_poi, pa_.plan_day, pa_.plan_start, pa_.plan_end, 0)
    place_ids = pq.read_table(Path(args.world) / "w2_cells.parquet", columns=["place_id"]).column(0).to_pylist()
    cell_of = {str(p): i for i, p in enumerate(place_ids)}
    poi_cell = np.asarray(world.pois.cell, dtype=np.int64)
    cell_dist = world.assets.cell_dist
    hops = _Hops(world)
    homes: dict[int, np.ndarray] = {}

    def home_of(seed: int) -> np.ndarray:
        if seed not in homes:
            r = cli.run(n_agents=args.agents, seed=seed, world_dir=args.world, ticks=1,
                        checkpoint_every=0)
            homes[seed] = np.asarray(r.schedule.home_cell, dtype=np.int64).copy()
        return homes[seed]

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
        m_seed = SEED_RE.search(run)
        seed = int(m_seed.group(1)) if m_seed else 1
        blocks = pq.read_table(pp.parent / "blocks.parquet", columns=["block_id", "text"]).to_pydict()
        cell_by_block: dict[str, str] = {}
        for bid, tx in zip(blocks["block_id"], blocks["text"]):
            if "[B2 場所]" in tx:
                m = PLACE_RE.search(tx)
                if m:
                    cell_by_block[bid] = m.group(1)
        t = pq.read_table(p, columns=["agent_id", "tick", "response", "deferred", "block_ids"]).to_pydict()
        seen_at: dict[int, list[tuple[int, int]]] = defaultdict(list)  # 体 → [(tick, セル)]
        shop: dict[int, list[tuple[int, bool, Any]]] = {}
        talks: list[tuple[int, int, int, Any]] = []
        sleeps: list[tuple[int, int, int]] = []
        for aid, tick, resp, d, bids in zip(t["agent_id"], t["tick"], t["response"], t["deferred"],
                                           t["block_ids"]):
            if d or not resp:
                continue
            place = next((cell_by_block[b] for b in bids if b in cell_by_block), None)
            cell = cell_of.get(place, -1) if place else -1
            if cell >= 0:
                seen_at[int(aid)].append((int(tick), int(cell)))
            pr = parse_two_line(resp, ver)
            if pr.action in ("購入", "食事"):
                shop.setdefault(int(tick), []).append((cell, pr.action == "食事", pr.target))
            elif pr.action == "会話":
                talks.append((int(aid), int(tick), cell, pr.target))
            elif pr.action == "就寝":
                sleeps.append((int(aid), int(tick), cell))
        for v in seen_at.values():
            v.sort()
        c: Counter = Counter()
        # ---- 購入/食事 ----
        res = TargetResolver(world=world, chooser=NearestChooser(), seed=1)
        with world.writable():
            for tick in sorted(shop):  # 逐次: テープの tick
                world.pois.open_now[:] = openm[:, int(tick) % 1440].astype(np.int8)
                for cell, eat, tg in shop[tick]:  # 逐次: 呼ごと
                    act = "食事" if eat else "購入"
                    c[f"{act}:calls"] += 1
                    before = Counter(res.stats)
                    io: dict[int, tuple[int, int]] = {}
                    res.resolve(_Agents(np.array([cell])), tick, np.array([0]),
                                np.array([C.ACT_EAT if eat else C.ACT_BUY]), [tg],
                                is_eat=np.array([eat]), is_buy_like=np.array([not eat]),
                                intent_out=io)
                    diff = Counter(res.stats)
                    diff.subtract(before)
                    for k, v in diff.items():
                        if v and (k.startswith("named_out_of_cell:") or k.startswith("intent")
                                  or k == "no_candidate:named_out_of_cell"):
                            c[f"{act}:{k}"] += v
                    if io:
                        poi, kind = io[0]
                        dest = int(poi_cell[poi])
                        kname = "named" if kind == 1 else "category"
                        _trip(c, f"{act}:{kname}", int(cell_dist[cell, dest]), hops(cell, dest))
            world.pois.open_now[:] = -1
        # ---- 会話 ----
        for aid, tick, cell, tg in talks:
            c["会話:calls"] += 1
            pid = getattr(tg, "person_id", None) if tg is not None else None
            if getattr(getattr(tg, "kind", None), "name", "") != "PERSON" or pid is None:
                c["会話:not_person"] += 1
                continue
            c["会話:person"] += 1
            if cell < 0:
                c["会話:self_offmap"] += 1
                continue
            hist = seen_at.get(int(pid), [])
            k = bisect.bisect_right(hist, (tick, 1 << 30)) - 1
            if k < 0 or tick - hist[k][0] > PARTNER_STALE_TICKS:
                c["会話:partner_unknown"] += 1
                continue
            pcell = hist[k][1]
            if pcell == cell:
                c["会話:partner_same_cell"] += 1
                continue
            c["会話:partner_other_cell"] += 1
            _trip(c, "会話:intent", int(cell_dist[cell, pcell]), hops(cell, pcell))
        # ---- 就寝 ----
        if sleeps:
            home = home_of(seed)
            for aid, tick, cell in sleeps:
                c["就寝:calls"] += 1
                h = int(home[aid]) if 0 <= aid < home.size else -1
                if h < 0:
                    c["就寝:home_offmap"] += 1
                elif cell < 0:
                    c["就寝:self_offmap"] += 1
                elif h == cell:
                    c["就寝:at_home"] += 1
                else:
                    c["就寝:home_other_cell"] += 1
                    _trip(c, "就寝:intent", int(cell_dist[cell, h]), hops(cell, h))
        summ = _summary(c)
        rows_out.append({"tape": f"{run}/{arm}", "vocab": ver, "seed": seed, "summary": summ})
        total.update(c)
        sig = json.dumps(summ, sort_keys=True)
        if sig not in seen:
            seen.add(sig)
            uniq.update(c)
            uniq_tapes.append(f"{run}/{arm}")
        print(f"{run}/{arm}: 購入 {summ['購入']['calls']:,} 意図 {summ['購入']['intent_named']}+"
              f"{summ['購入']['intent_category']} / 食事 {summ['食事']['calls']:,} 意図 "
              f"{summ['食事']['intent_named']}+{summ['食事']['intent_category']} / 会話 "
              f"{summ['会話']['partner_other_cell']} / 就寝 {summ['就寝']['home_other_cell']}",
              flush=True)
    doc = {
        "schema": "shibuya.bench/intent-chooser-2026-09-28/replay-intents/1",
        "max_ticks": MAX_TICKS,
        "tapes": rows_out,
        "total": _summary(total),
        "total_unique": _summary(uniq),
        "unique_tapes": uniq_tapes,
        "note": ("呼数(total=複製テープを含む 23 本・total_unique=結果の組で束ねた本数)。棚在庫は見ない。"
                 "月曜 day 0 の W7 営業行列。歩数=代表ノード間の経路のノード数(node 幾何の tick)。"
                 "会話の相手の居場所=相手の直近の呼の B2(60 tick 以内)。自宅=いまのコードで組み直した母集団。"),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    return 0


def _summary(c: Counter) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for act in ("購入", "食事"):
        out[act] = {
            "calls": int(c.get(f"{act}:calls", 0)),
            "named_out_of_cell": int(c.get(f"{act}:intent:named", 0))
            + int(c.get(f"{act}:no_candidate:named_out_of_cell", 0))
            + int(c.get(f"{act}:named_out_of_cell:closed", 0))
            + int(c.get(f"{act}:named_out_of_cell:out_of_stock", 0)),
            "intent_named": int(c.get(f"{act}:intent:named", 0)),
            # 親決定 Q21: 見える名指しの店が閉店/在庫切れ=歩かずに即時の失敗
            "named_closed_now": int(c.get(f"{act}:named_out_of_cell:closed", 0)),
            "named_out_of_stock_now": int(c.get(f"{act}:named_out_of_cell:out_of_stock", 0)),
            "named_not_visible": int(c.get(f"{act}:named_out_of_cell:not_visible", 0)),
            "named_not_fit": int(c.get(f"{act}:named_out_of_cell:not_fit", 0)),
            "named_offmap": int(c.get(f"{act}:named_out_of_cell:offmap", 0)),
            "intent_category": int(c.get(f"{act}:intent:category", 0)),
            "category_none_nearby": int(c.get(f"{act}:intent_miss:category_none_nearby", 0)),
            "trip_named": _trip_summary(c, f"{act}:named"),
            "trip_category": _trip_summary(c, f"{act}:category"),
        }
    out["会話"] = {
        "calls": int(c.get("会話:calls", 0)),
        "person": int(c.get("会話:person", 0)),
        "partner_same_cell": int(c.get("会話:partner_same_cell", 0)),
        "partner_other_cell": int(c.get("会話:partner_other_cell", 0)),
        "partner_unknown": int(c.get("会話:partner_unknown", 0)),
        "self_offmap": int(c.get("会話:self_offmap", 0)),
        "trip": _trip_summary(c, "会話:intent"),
    }
    out["就寝"] = {
        "calls": int(c.get("就寝:calls", 0)),
        "at_home": int(c.get("就寝:at_home", 0)),
        "home_other_cell": int(c.get("就寝:home_other_cell", 0)),
        "home_offmap": int(c.get("就寝:home_offmap", 0)),
        "self_offmap": int(c.get("就寝:self_offmap", 0)),
        "trip": _trip_summary(c, "就寝:intent"),
    }
    return out


if __name__ == "__main__":
    sys.exit(main())
