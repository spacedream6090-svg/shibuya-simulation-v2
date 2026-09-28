"""PENDING §2-9 小さいもの 4 件の計測(第300 Q107・第289 Q28・D-16・D-52)。

使い方(リポジトリの根から)::

    D=docs/bench/analysis/small-fixes-2026-09-29
    python $D/small_fixes_measure.py t5 --out $D/q107_t5.json              # ① T5(classical/mock × 関係 on/off × hash/id)
    python $D/small_fixes_measure.py arms15 --out $D/q107_arms15.json      # ① 15 腕 × hash/id(final・呼数・撹拌した描画)
    python $D/small_fixes_measure.py bytecheck --head-src <HEAD bb44474 の src と docs/bench/anchors を展開した src> \\
        --scratch <作業用の場所> --out $D/q107_byte_check.json            # ① HEAD と作業木(id=一致・hash=同点の描画だけ)
    python $D/small_fixes_measure.py fleet --out $D/q28_fleet.json         # ② 艦隊スモーク(偽 vLLM)の繰り延べと警告
    python $D/small_fixes_measure.py waste --out $D/d52_waste.json         # ④ 廃棄の内訳(店のビン・世帯の消費・街路ごみ)

- ``t5``: C10 8b の計測道具(``c10-relations-2026-09-28/rel8b_measure.py`` の ``one``=層化 5,000 体・seed 1・v3・
  ``--memory on``)に ``near_tiebreak`` の腕を足して回す。T5 = 相手に選ばれた回数と ID の層内相関(呼数加重 |ρ|・
  部分相関・最大の層)とセル内の ID 順位。**計測だけの腕** ``classical_off_order_hash`` は近接行の**並び**
  (id 昇順)も撹拌したら関係 off の classical の T5 がどうなるかを見る(描画を包むだけ・実装していない=問い)。
- ``arms15``: W6 再生成の 15 腕を ``--near-tiebreak hash``(既定)と ``id``(旧)で回す。
- ``bytecheck``: HEAD の git archive と作業木で同じラン(mock 5,000・seed 1)のテープを列ごとに突き合わせる。
  作業木の ``id`` は HEAD と全部一致すること。作業木の ``hash``(既定)は、mock なら final は同じで、
  プロンプトが違う呼は**同点を撹拌した描画の呼だけ**であること(``(tick, 体)`` の集合の包含で示す)。
- ``fleet``: 偽 vLLM 2 本の艦隊 × 呼数無制限 × 受理待ち枠 未指定のスモーク。枠を狭めた設定(``max_in_flight``
  小)で、修正前(枠=既定の max_in_flight×4)なら繰り延べが出る条件で 0 になること・警告が出ないこと。

絶対パスは書かない。壁時計は決定論でない。holdout は触らない。
"""

from __future__ import annotations

import argparse
import contextlib
import hashlib
import importlib.util
import io
import json
import os
import re
import subprocess
import sys
import time
import warnings
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
REL8B = HERE.parent / "c10-relations-2026-09-28" / "rel8b_measure.py"
W6 = HERE.parent / "w6-regen-2026-09-28" / "w6_regen_measure.py"
CLS = {"policy": "classical", "chooser": "classical"}
#: T5 の腕(名前: (抽出, 引数))。BASE(v3・memory on)は rel8b の既定。
T5_ARMS: dict[str, tuple[str, dict[str, Any]]] = {
    "mock_off_hash": ("stratified", {}),
    "mock_off_id": ("stratified", {"near_tiebreak": "id"}),
    "mock_rel_on_hash": ("stratified", {"relations": "on"}),
    "mock_rel_on_id": ("stratified", {"relations": "on", "near_tiebreak": "id"}),
    "classical_off_hash": ("stratified", CLS),
    "classical_off_id": ("stratified", {**CLS, "near_tiebreak": "id"}),
    "classical_on_hash": ("stratified", {**CLS, "relations": "on"}),
    "classical_on_id": ("stratified", {**CLS, "relations": "on", "near_tiebreak": "id"}),
    # 計測だけ(実装していない): 近接行の並び(id 昇順)も撹拌したら
    "classical_off_order_hash": ("stratified", CLS),
}
ORDER_HASH_ARMS = ("classical_off_order_hash",)
BYTE_CONFIGS: dict[str, dict[str, Any]] = {
    "v3_default": {"vocab_version": "v3"},
    "v3_classical": {"vocab_version": "v3", **CLS},
    "v1_default": {"vocab_version": "v1"},
    "v3_memory_relations": {"vocab_version": "v3", "memory": "on", "relations": "on"},
}
PERSON = re.compile(r"P-(\d+)")


def _load(path: Path, name: str) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def _h(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, ensure_ascii=False, default=str).encode("utf-8")).hexdigest()[:16]


def _capture_result() -> dict[str, Any]:
    """``shibuya.cli.run`` を包んで結果を控える(rel8b の ``one`` は結果を返さないため)。"""
    from shibuya import cli

    got: dict[str, Any] = {}
    orig = cli.run

    def wrapped(*a: Any, **k: Any) -> Any:
        res = orig(*a, **k)
        got["res"] = res
        return res

    cli.run = wrapped  # type: ignore[assignment]
    return got


def _patch_display_order() -> None:
    """計測だけ: 近接行の並びを撹拌鍵の順にする(焦点の先頭は保つ)。描画の包みで、エンジンは変えない。"""
    from shibuya.perception import renderer as RD

    orig = RD.Renderer._nearby_items

    def items(self: Any, i: int, cell: int, tc: Any) -> list[tuple[str, float]]:
        out = orig(self, i, cell, tc)
        if len(out) <= 1:
            return out
        ids = np.asarray([int(PERSON.search(t).group(1)) if PERSON.search(t) else -1 for t, _d in out], dtype=np.int64)
        head = 0
        f = self._focus_target
        if f is not None and int(f[i]) == int(ids[0]) and int(ids[0]) >= 0:
            head = 1  # 焦点は先頭のまま
        key = RD.near_tie_keys(self._near_salt64, i, np.maximum(ids[head:], 0))
        order = np.argsort(key, kind="stable")
        return out[:head] + [out[head + int(k)] for k in order]

    RD.Renderer._nearby_items = items  # type: ignore[method-assign]


# ------------------------------------------------------------------ ① T5
def cmd_t5_one(args: argparse.Namespace) -> int:
    rel = _load(REL8B, "rel8b_measure")
    rel.ARMS[args.arm] = T5_ARMS[args.arm]
    got = _capture_result()
    if args.arm in ORDER_HASH_ARMS:
        _patch_display_order()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rel.cmd_one(argparse.Namespace(arm=args.arm, world=args.world, agents=args.agents, seed=args.seed))
    row = json.loads(buf.getvalue().strip().splitlines()[-1])
    res = got.get("res")
    row["near_tiebreak"] = res.run_manifest_fields().get("near_tiebreak", {}) if res is not None else {}
    row["measurement_only"] = args.arm in ORDER_HASH_ARMS
    print(json.dumps(row, ensure_ascii=False, default=str))
    return 0


def cmd_t5(args: argparse.Namespace) -> int:
    rows = []
    for name in (args.only.split(",") if args.only else list(T5_ARMS)):
        cmd = [sys.executable, str(Path(__file__)), "t5-one", "--arm", name, "--world", args.world,
               "--agents", str(args.agents), "--seed", str(args.seed)]
        r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True)
        row = json.loads(r.stdout.strip().splitlines()[-1])
        rows.append(row)
        t5 = row.get("t5", {})
        cc = t5.get("chosen_count_vs_id", {})
        print(name, row["final_hash"][:8], row["llm_calls"], t5.get("picks"), cc.get("weighted_abs_rho"),
              cc.get("partial"), cc.get("largest_stratum"), t5.get("within_cell_id_rank", {}).get("mean"),
              row["near_tiebreak"], row["wall_seconds_nondeterministic"], flush=True)
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/small-fixes/q107-t5/1",
                                          "base": "rel8b_measure one(層化 5,000 体・seed 1・v3・memory on)",
                                          "rows": rows}, ensure_ascii=False, indent=1) + "\n",
                              encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ ① 15 腕
def cmd_arms15(args: argparse.Namespace) -> int:
    from shibuya import cli

    w6 = _load(W6, "w6_regen_measure")
    rows = []
    for name, kw in w6.ARMS.items():
        got = {}
        for mode in ("hash", "id"):
            t0 = time.perf_counter()
            res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, near_tiebreak=mode, **kw)
            calls = int(res.column("calls").sum()) if res.diagnostics.size else 0
            got[mode] = {"final": res.final_hash, "llm_calls": calls,
                         "near_tiebreak": res.run_manifest_fields().get("near_tiebreak", {}),
                         "wall_seconds_nondeterministic": round(time.perf_counter() - t0, 2)}
        row = {"arm": name, "args": kw, "hash": got["hash"], "id": got["id"],
               "final_equal": got["hash"]["final"] == got["id"]["final"],
               "calls_equal": got["hash"]["llm_calls"] == got["id"]["llm_calls"]}
        rows.append(row)
        print(f"{name}: id {got['id']['final'][:8]} hash {got['hash']['final'][:8]} "
              f"{'=' if row['final_equal'] else '≠'} calls {got['id']['llm_calls']:,}→{got['hash']['llm_calls']:,} "
              f"ties {got['hash']['near_tiebreak'].get('ties_broken')}", flush=True)
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/small-fixes/q107-arms15/1", "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ ① bytecheck
def cmd_bytecheck_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    from shibuya import cli

    kw = dict(BYTE_CONFIGS[args.config])
    if args.near:
        kw["near_tiebreak"] = args.near
    tie_calls: list[tuple[int, int]] = []
    if args.near == "hash":
        from shibuya.perception import renderer as RD

        orig = RD.Renderer._nearby_items

        def items(self: Any, i: int, cell: int, tc: Any) -> Any:
            before = self.near_tie_breaks
            out = orig(self, i, cell, tc)
            if self.near_tie_breaks != before:
                tie_calls.append((int(tc.tick), int(i)))
            return out

        RD.Renderer._nearby_items = items  # type: ignore[method-assign]
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, tape_path=args.tape, **kw)
    calls = pq.read_table(Path(args.tape) / "calls.parquet")
    blocks = pq.read_table(Path(args.tape) / "blocks.parquet")
    keys = list(zip(calls.column("tick").to_pylist(), calls.column("agent_id").to_pylist()))
    Path(args.tape, "keys.json").write_text(json.dumps({"keys": keys,
                                                         "prompt_hash": calls.column("prompt_hash").to_pylist(),
                                                         "tie_calls": sorted(set(tie_calls))}),
                                            encoding="utf-8")
    print(json.dumps({
        "config": args.config, "near": args.near or "(HEAD 既定)", "final": res.final_hash[:16],
        "calls": int(res.llm_calls), "blocks_rows": int(blocks.num_rows),
        "blocks_sha": _h({n: blocks.column(n).to_pylist() for n in blocks.column_names}),
        "calls_columns_sha": {n: _h(calls.column(n).to_pylist()) for n in calls.column_names},
        "near_tiebreak": res.run_manifest_fields().get("near_tiebreak", {}),
    }, ensure_ascii=False, default=str))
    return 0


def cmd_bytecheck(args: argparse.Namespace) -> int:
    scratch = Path(args.scratch)
    got: dict[tuple[str, str], dict[str, Any]] = {}
    sides = (("head", args.head_src, ""), ("work_id", "", "id"), ("work_hash", "", "hash"))
    for name in BYTE_CONFIGS:
        for side, src, near in sides:
            env = dict(os.environ)
            if src:
                env["PYTHONPATH"] = src
                env["SHIBUYA_BUDGET_MD"] = "docs/design/v2-budget-declaration.md"
            cmd = [sys.executable, str(Path(__file__)), "bytecheck-one", "--config", name, "--world", args.world,
                   "--agents", str(args.agents), "--seed", str(args.seed), "--tape", str(scratch / f"{side}_{name}")]
            if near:
                cmd += ["--near", near]
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", check=True, env=env)
            got[(side, name)] = json.loads(r.stdout.strip().splitlines()[-1])
    runs = []
    for name in BYTE_CONFIGS:
        h, wi, wh = got[("head", name)], got[("work_id", name)], got[("work_hash", name)]
        row: dict[str, Any] = {"run": name, "head": h, "work_id": wi, "work_hash": wh}
        for tag, w in (("id", wi), ("hash", wh)):
            diff = sorted(k for k in h["calls_columns_sha"] if h["calls_columns_sha"][k] != w["calls_columns_sha"].get(k))
            row[f"{tag}_final_equal"] = h["final"] == w["final"]
            row[f"{tag}_calls_equal"] = h["calls"] == w["calls"]
            row[f"{tag}_blocks_equal"] = (h["blocks_sha"], h["blocks_rows"]) == (w["blocks_sha"], w["blocks_rows"])
            row[f"{tag}_calls_columns_differ"] = diff
        # hash: プロンプトが違う呼 ⊆ 同点を撹拌した描画の呼(呼の並びが同じとき=final と呼数が同じとき)
        kh = json.loads((scratch / f"head_{name}" / "keys.json").read_text(encoding="utf-8"))
        kw_ = json.loads((scratch / f"work_hash_{name}" / "keys.json").read_text(encoding="utf-8"))
        if kh["keys"] == kw_["keys"]:
            differ = {tuple(k) for k, a, b in zip(kh["keys"], kh["prompt_hash"], kw_["prompt_hash"]) if a != b}
            ties = {tuple(x) for x in kw_["tie_calls"]}
            row["hash_prompt_differs_calls"] = len(differ)
            row["hash_tie_render_calls"] = len(ties & {tuple(k) for k in kw_["keys"]})
            row["hash_prompt_differs_subset_of_tie_renders"] = differ <= ties
            row["hash_calls_without_tie_identical"] = differ <= ties
        else:
            row["hash_call_sequence_differs"] = True
        runs.append(row)
        print(name, {k: v for k, v in row.items() if k.endswith(("equal", "differ", "subset_of_tie_renders",
                                                                  "differs_calls", "tie_render_calls"))}, flush=True)
    doc = {"schema": "shibuya.bench/small-fixes/q107-byte-check/1", "head": args.head_label,
           "how": ("same runs (mock/classical 5,000, seed 1) with the committed source (git archive) and the working "
                   "tree with --near-tiebreak id and hash. id must equal HEAD everywhere. hash: when the call "
                   "sequence is the same (mock), the calls whose prompt differs must be a subset of the calls whose "
                   "B5 render broke a distance tie."),
           "runs": runs}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ ② 艦隊
def cmd_fleet(args: argparse.Namespace) -> int:
    sys.path.insert(0, str(REPO / "tests" / "c6"))
    sys.path.insert(0, str(REPO / "tests"))
    from c6._fake_vllm import FakeVLLM  # type: ignore[import-not-found]

    from shibuya import cli
    from shibuya.llm.fleet import FleetClient, FleetConfig
    from shibuya.manifest.schema import Mode

    rows = []
    for label, qcap in (("unset(既定=体数)", None), ("explicit_old_default", "old")):
        fakes = [FakeVLLM(), FakeVLLM()]
        try:
            cfg = FleetConfig(endpoints=tuple(f.endpoint for f in fakes), mode=Mode("smoke"), run_seed=1,
                              temperature=0.0, t1_max_tokens=64, stream=False, max_in_flight=8,
                              queue_capacity=(8 * 4 if qcap == "old" else None))
            client = FleetClient(cfg)
            try:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter("always")
                    res = cli.run(n_agents=args.agents, seed=args.seed, ticks=args.ticks, world_dir=None,
                                  fleet=client, sleep_suppression=False)
            finally:
                client.close()
            m = res.run_manifest_fields()
            fl = dict(getattr(res, "fleet_fields", {}) or {})
            rows.append({
                "case": label, "n_agents": args.agents, "ticks": args.ticks, "l4_scale": m.get("l4_scale"),
                "queue_capacity": fl.get("queue_capacity"), "max_in_flight": fl.get("in_flight_cap_total"),
                "deferred_queue_full": int(client.n_deferred_queue_full),
                "submitted": int(client.n_submitted),
                "runtime_warnings": [str(w.message)[:80] for w in caught if issubclass(w.category, RuntimeWarning)],
                "l4_notes": m.get("l4_notes", []), "final": res.final_hash[:16], "llm_calls": int(res.llm_calls),
                "client_queue_capacity": int(client.queue_capacity),
            })
            print(rows[-1], flush=True)
        finally:
            for f in fakes:
                f.close()
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/small-fixes/q28-fleet/1", "rows": rows},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


# ------------------------------------------------------------------ ④ 廃棄の内訳(D-52)
def _static_store_waste_g(world_dir: str, n_agents: int) -> dict[str, float]:
    """店舗の期限切れ在庫の**静的な期待値**[g/日] = Σ 棚(初期在庫)× SKU 廃棄率(切り捨て)× 質量。

    05:00 の売れ残り → ビン(``goods_flow._sell_leftovers_to_bin``)と同じ式を、初期在庫(補充で戻る水準)に当てる。
    """
    from shibuya.economy.goods import CATEGORY_NAMES, GoodsLedger
    from shibuya.world.assets import hash_free_cat_code
    from shibuya.world.state import World

    w = World.load_or_synthetic(Path(world_dir), n_cells=139, seed=1)
    cats = np.array([hash_free_cat_code(c) for c in w.assets.poi_cat], dtype=np.int64)
    g = GoodsLedger.from_pois(cats, np.asarray(w.pois.stock), np.asarray(w.pois.price), n_agents=n_agents)
    shelf = np.asarray(g.shelf, dtype=np.int64)
    sku = np.asarray(g.poi_sku, dtype=np.int64)
    rate = np.where(sku >= 0, np.asarray(g.sku.waste_rate)[np.maximum(sku, 0)], 0.0)
    mass = np.where(sku >= 0, np.asarray(g.sku.mass_g)[np.maximum(sku, 0)], 0.0)
    grams = np.floor(shelf * rate) * mass
    return {"total_g": float(grams.sum()), "n_poi": int(g.n_poi),
            "stock0_values": sorted({int(x) for x in np.asarray(w.pois.stock).tolist()}),
            "by_category_g": {CATEGORY_NAMES[c]: float(grams[cats == c].sum()) for c in range(len(CATEGORY_NAMES))}}


def cmd_waste(args: argparse.Namespace) -> int:
    from shibuya import cli
    from shibuya.engine.processes.goods_flow import CLEANING_WINDOWS, LITTER_G_PER_PERSON_TICK

    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, vocab_version="v3")
    pc = dict(res.process_counters)
    total_g = float(res.waste_tonnes_per_day) * 1_000_000.0
    swept = float(pc.get("street_cleaning.swept_g", 0.0))
    collected = float(pc.get("waste.collected_g", 0.0))
    goods_g = total_g - swept
    store = _static_store_waste_g(args.world, args.agents)
    row = {
        "run": {"n_agents": args.agents, "seed": args.seed, "vocab": "v3", "final": res.final_hash[:16],
                "waste_tonnes_per_day": round(float(res.waste_tonnes_per_day), 6),
                "band_now": list(res.waste_band)},
        "breakdown_g": {
            "store_bins_collected": collected,
            "household_consumption": goods_g - collected,
            "street_litter_swept": swept,
            "street_litter_left_at_end": float(pc.get("street_cleaning.litter_now_g", 0.0)),
            "household_consumption_rows": float(pc.get("waste.consumed", 0.0)),
        },
        "static_store_expectation": store,
        "params": {"LITTER_G_PER_PERSON_TICK": LITTER_G_PER_PERSON_TICK, "CLEANING_WINDOWS": CLEANING_WINDOWS},
    }
    # c7-day-4(39 万体)の在圏 journal から在圏の人・分 → 街路ごみの発生量(0.05 g/人/tick × 人・分)
    j = REPO / "data" / "runs" / "c7-day-4" / "occupancy.npz"
    if j.exists():
        with np.load(j, allow_pickle=False) as z:
            counts = np.asarray(z["cell_counts"], dtype=np.float64)
        pm = float(counts.sum()) * 60.0  # 毎正時の標本 24 点 × 60 分(正時の在圏が 1 時間続くと置く=近似)
        row["c7_day_4"] = {"person_minutes_in_stage_approx": pm,
                           "litter_generated_g_approx": pm * LITTER_G_PER_PERSON_TICK,
                           "recorded": {"total_t": 10.767, "goods_ledger_t": 3.78755, "street_litter_t": 6.979}}
    print(json.dumps(row, ensure_ascii=False, indent=1))
    Path(args.out).write_text(json.dumps({"schema": "shibuya.bench/small-fixes/d52-waste/1", **row},
                                         ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="小さいもの 4 件の計測")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("t5", "t5-one", "arms15", "bytecheck", "bytecheck-one", "fleet", "waste"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--agents", type=int, default=300 if name == "fleet" else 5_000)
        sp.add_argument("--seed", type=int, default=1)
        if name in ("t5", "arms15", "bytecheck", "fleet", "waste"):
            sp.add_argument("--out", required=True)
        if name == "t5":
            sp.add_argument("--only", default="")
        if name == "t5-one":
            sp.add_argument("--arm", required=True, choices=tuple(T5_ARMS))
        if name == "bytecheck":
            sp.add_argument("--head-src", required=True)
            sp.add_argument("--head-label", default="bb44474")
            sp.add_argument("--scratch", required=True)
        if name == "bytecheck-one":
            sp.add_argument("--config", required=True, choices=tuple(BYTE_CONFIGS))
            sp.add_argument("--tape", required=True)
            sp.add_argument("--near", default="", choices=("", "hash", "id"))
        if name == "fleet":
            sp.add_argument("--ticks", type=int, default=24)
    args = ap.parse_args(argv)
    return {"t5": cmd_t5, "t5-one": cmd_t5_one, "arms15": cmd_arms15, "bytecheck": cmd_bytecheck,
            "bytecheck-one": cmd_bytecheck_one, "fleet": cmd_fleet, "waste": cmd_waste}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
