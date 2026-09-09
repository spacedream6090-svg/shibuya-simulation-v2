# -*- coding: utf-8 -*-
"""occupancy_series.py — C7 の**在圏時系列**(5エリア×24時)を作る。

なぜ要るか
    実装計画書 §9.1 **C7** の受入は「holdout 照合(KDDI 形状5指標)」を含む。KDDI 側は
    **渋谷駅周辺5エリア×1時間刻み24区分**の滞在人口なので、ラン側にも同じ形の
    「エリア×時刻の在圏プロファイル」が要る。エンジンは ``world.cells.density``
    (セル別在席数)を毎 tick 計算しているが、**保存していない**(RunResult は
    tick 集計の診断表だけ)。本ツールがその欠けを埋める。

3 つの入口
    A. ``--build-map``: W2 セル → 5 エリアの写像表を作る(``area_axes_v0.json`` の
       折れ線から・**expedient**。公的ポリゴンは存在しない=登録簿 E-C7-2)。
    B. ``--record``: ``run_day`` を回しつつ **``engine.resolve.apply`` をモジュール属性で
       包んで**在圏を標本化する(**エンジンのソースは触らない**)。C7 本ランでは
       親が入れるエンジン側フック(``--journal``)に置き換わる。
    C. ``--journal``: エンジン側フックが出した ``c7_occupancy.npz`` を読む(推奨経路)。

出力
    ``c7_occupancy.json``(``area_hour_share`` = **形状のみ**・``area_attr_counts``)と
    ``c7_occupancy.npz``(標本の生配列)。holdout 照合はこの JSON だけを読む。

例(親)::

    python tools/c7/occupancy_series.py --build-map --world data/world/v2 --out docs/bench/c7
    python tools/c7/occupancy_series.py --journal runs/c7/c7_occupancy.npz \\
        --area-map docs/bench/c7/c7_area_map.json --out docs/bench/c7
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c7lib  # noqa: E402

AREA_IDS = c7lib.AREA_IDS
ATTR_IDS = c7lib.ATTR_IDS

#: 既定の標本間隔[tick](1 tick=1分 → 60=毎正時)。
DEFAULT_EVERY = 60
#: ``AgentKind`` の値域(0..8)。journal の kind 軸の長さ。
N_KINDS = 9


# ---------------------------------------------------------------- A: 写像表


def cells_from_world(world_dir: str | Path) -> dict[str, Any]:
    """``w2_cells.parquet`` を**エンジンと同じ行順で**読む(place_id / ix / iy)。"""
    import pyarrow.parquet as pq

    t = pq.read_table(Path(world_dir) / "w2_cells.parquet", columns=["place_id", "ix", "iy"])
    d = t.to_pydict()
    return {
        "place_ids": [str(v) for v in d["place_id"]],
        "ix": np.asarray(d["ix"], dtype=np.int64),
        "iy": np.asarray(d["iy"], dtype=np.int64),
    }


def build_map(
    world_dir: str | Path,
    axes_path: str | Path | None = None,
    *,
    dilate_m: float = 0.0,
) -> tuple[c7lib.AreaMap, dict[str, Any]]:
    """W2 セル → ``AreaMap`` と自己検査(面積帯)。"""
    axes = c7lib.load_axes(axes_path)
    cells = cells_from_world(world_dir)
    amap = c7lib.build_area_map(cells["place_ids"], cells["ix"], cells["iy"], axes,
                                dilate_m=dilate_m)
    amap.meta["world_dir"] = str(world_dir)
    amap.meta["axes_path"] = str(axes_path or c7lib.DEFAULT_AXES_PATH)
    gate = c7lib.area_ha_gate(amap, axes)
    return amap, gate


def sensitivity(world_dir: str | Path, axes_path: str | Path | None = None,
                deltas: Sequence[float] = (-50.0, 0.0, 50.0)) -> dict[str, Any]:
    """境界 ±50m の膨張/収縮で写像がどれだけ動くか(地図読み取り答申の要求「④ expedient 登録:
    感度=境界を±50m膨張/収縮してD1′判定が動かないこと」の測定装置)。"""
    base, _ = build_map(world_dir, axes_path, dilate_m=0.0)
    rows = []
    for d in deltas:
        amap, gate = build_map(world_dir, axes_path, dilate_m=float(d))
        moved = int((amap.area_of_cell != base.area_of_cell).sum())
        rows.append({
            "dilate_m": float(d),
            "counts": amap.counts(),
            "area_ha": amap.area_ha(),
            "cells_changed_vs_0m": moved,
            "cells_changed_ratio": round(moved / max(1, base.n_cells), 6),
            "area_ha_gate_ok": gate["ok"],
        })
    return {"base_counts": base.counts(), "rows": rows}


# ---------------------------------------------------------------- B: ラン中の標本化


def agent_field(agents: Any, name: str) -> np.ndarray:
    """個体 SoA の欄を取る。

    ``AgentState.registry`` は ``SoARegistry`` で、``registry.kind`` は**レジストリ自身の種別**
    (``"agent"``)を指す別物。欄は ``registry.field(name)`` で引くのが正しい
    (``agents/state.py`` の docstring「``agents.kind`` か ``agents.registry.field("kind")`` を
    使う」)。テストの偽オブジェクト(``field`` を持たない)にも当たるよう 3 段で落とす。
    """
    reg = getattr(agents, "registry", agents)
    getter = getattr(reg, "field", None)
    if callable(getter):
        try:
            return np.asarray(getter(name))
        except (KeyError, AttributeError):
            pass
    value = getattr(reg, name, None)
    if value is None:
        value = getattr(agents, name)
    return np.asarray(value)


class OccupancyRecorder:
    """``engine.resolve.apply`` を包んで在圏を標本化する(**ソース非改変**)。

    ``resolve.apply`` は 1 tick に 1 回だけ呼ばれ、その中で
    ``world.cells.density[:] = world.compute_density(r.cell)`` が走る(位置の確定=予算行 P2 の
    測定区間)。本クラスは**戻ってきた直後**に密度配列と種別を読むだけで、世界も乱数も触らない。

    expedient(登録簿 E-C7-3)
        モジュール属性の差し替えは **計器側の便法**。C7 本ランでは親がエンジンへ入れる
        フック(``--journal``)を使う。差し替えの有無で状態ハッシュは変わらない
        (書き込みをしないこと・呼び出し順を変えないことを ``tests/c7`` で固定する)。
    """

    def __init__(self, every: int = DEFAULT_EVERY, *, with_kind: bool = True) -> None:
        self.every = int(every)
        self.with_kind = bool(with_kind)
        self.ticks: list[int] = []
        self._counts: list[np.ndarray] = []
        self._kind: list[np.ndarray] = []
        self._orig = None
        self._module = None

    # -- 標本化そのもの(純粋な読み取り) --
    def sample(self, agents: Any, world: Any, tick: int) -> None:
        if self.every <= 0 or int(tick) % self.every != 0:
            return
        self.ticks.append(int(tick))
        self._counts.append(np.asarray(world.cells.density, dtype=np.int32).copy())
        if self.with_kind:
            n_cells = int(np.asarray(world.cells.density).size)
            cell = agent_field(agents, "cell").astype(np.int64)
            kind = np.clip(agent_field(agents, "kind").astype(np.int64), 0, N_KINDS - 1)
            ok = (cell >= 0) & (cell < n_cells)
            flat = np.bincount(
                kind[ok] * n_cells + cell[ok], minlength=N_KINDS * n_cells
            )[: N_KINDS * n_cells]
            self._kind.append(flat.reshape(N_KINDS, n_cells).astype(np.int32))

    # -- 取り付け/取り外し --
    def attach(self, module: Any | None = None) -> "OccupancyRecorder":
        if module is None:
            from shibuya.engine import resolve as module  # type: ignore
        self._module = module
        self._orig = module.apply
        rec = self

        def _wrapped(plan_confirmed, losers, agents, world, tick, **kw):
            out = rec._orig(plan_confirmed, losers, agents, world, tick, **kw)
            rec.sample(agents, world, tick)
            return out

        module.apply = _wrapped
        return self

    def detach(self) -> None:
        if self._module is not None and self._orig is not None:
            self._module.apply = self._orig
        self._module = None
        self._orig = None

    def __enter__(self) -> "OccupancyRecorder":
        return self if self._module is not None else self.attach()

    def __exit__(self, *exc: object) -> None:
        self.detach()

    # -- 取り出し --
    def series(self, amap: c7lib.AreaMap | None = None, *, tick_seconds: int = 60,
               start_hour: int = 0, meta: Mapping[str, Any] | None = None) -> c7lib.OccupancySeries:
        counts = (np.stack(self._counts) if self._counts
                  else np.zeros((0, 0), dtype=np.int32))
        kinds = np.stack(self._kind) if self._kind else None
        area_attr = None
        if kinds is not None and amap is not None:
            area_attr = kind_cell_to_area_attr(kinds, amap)
        return c7lib.OccupancySeries(
            ticks=np.asarray(self.ticks, dtype=np.int64),
            cell_counts=counts,
            area_attr=area_attr,
            tick_seconds=int(tick_seconds),
            start_hour=int(start_hour),
            meta={"source": "recorder(resolve.apply wrap)", **(dict(meta) if meta else {})},
        )

    def kind_cell_counts(self) -> np.ndarray | None:
        return np.stack(self._kind) if self._kind else None

    def cell_counts(self) -> np.ndarray:
        return np.stack(self._counts) if self._counts else np.zeros((0, 0), dtype=np.int32)


def checkpoints_json(result: Any, **meta: Any) -> dict[str, Any]:
    """``RunResult`` → T2 用 checkpoint JSON(``c7_accept.py --determinism/--partial`` の入力)。

    ``tools/c6/run_hash.py`` の payload と互換(``checkpoints`` を持つ)だが、こちらは
    **tick と部分ハッシュを残す**ので前方一致(T2-b)と自己整合(T2-c)が測れる。
    """
    return {
        "schema": "shibuya.tools.c7/checkpoints/1",
        "final_hash": result.final_hash,
        "checkpoints": [
            {
                "tick": int(c.tick),
                "combined": c.combined,
                "agents_hash": c.agents_hash,
                "world_hash": c.world_hash,
                "population_hash": c.population_hash,
                "schedule_hash": c.schedule_hash,
            }
            for c in result.checkpoints
        ],
        "conserved": bool(result.conserved),
        "diagnostics_day": {k: float(v) for k, v in result.diagnostics_day().items()},
        "run_manifest_fields": result.run_manifest_fields(),
        "meta": dict(meta),
    }


def kind_cell_to_area_attr(kind_cell: np.ndarray, amap: c7lib.AreaMap,
                           attr_map: Mapping[int, str] | None = None) -> np.ndarray:
    """``(T, K, C)`` 種別×セル → ``(T, 5, 3)`` エリア×属性。**純関数**。"""
    m = dict(c7lib.KIND_TO_ATTR if attr_map is None else attr_map)
    attr_idx = {name: i for i, name in enumerate(ATTR_IDS)}
    arr = np.asarray(kind_cell, dtype=np.int64)
    t, k, c = arr.shape
    if c != amap.n_cells:
        raise ValueError(f"セル数が違う: journal {c} vs map {amap.n_cells}")
    out = np.zeros((t, len(AREA_IDS), len(ATTR_IDS)), dtype=np.int64)
    for kind in range(k):
        a = attr_idx.get(m.get(kind, ""), None)
        if a is None:
            continue
        for i in range(len(AREA_IDS)):
            sel = amap.area_of_cell == i
            if sel.any():
                out[:, i, a] += arr[:, kind, sel].sum(axis=1)
    return out


# ---------------------------------------------------------------- C: journal


def write_journal(path: str | Path, ticks: np.ndarray, cell_counts: np.ndarray,
                  kind_cell_counts: np.ndarray | None = None, **meta: Any) -> Path:
    """エンジン側フックと本ツールが共有する journal 形式(``.npz``)。

    配列
      ``ticks``            ``(T,)`` int64(標本 tick・昇順)
      ``cell_counts``      ``(T, C)`` int32(セル別在圏数=``world.cells.density``)
      ``kind_cell_counts`` ``(T, K, C)`` int32(種別×セル・任意)
      ``meta``             JSON 文字列(tick_seconds・start_hour・world_dir・run_id など)
    """
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    arrs: dict[str, np.ndarray] = {
        "ticks": np.asarray(ticks, dtype=np.int64),
        "cell_counts": np.asarray(cell_counts, dtype=np.int32),
        "meta": np.asarray(json.dumps(meta, ensure_ascii=False)),
    }
    if kind_cell_counts is not None:
        arrs["kind_cell_counts"] = np.asarray(kind_cell_counts, dtype=np.int32)
    np.savez_compressed(p, **arrs)
    return p


def load_journal(path: str | Path, amap: c7lib.AreaMap | None = None,
                 attr_map: Mapping[int, str] | None = None) -> c7lib.OccupancySeries:
    """journal(``.npz``)→ ``OccupancySeries``。"""
    with np.load(Path(path), allow_pickle=False) as z:
        ticks = np.asarray(z["ticks"], dtype=np.int64)
        counts = np.asarray(z["cell_counts"], dtype=np.int32)
        kinds = np.asarray(z["kind_cell_counts"]) if "kind_cell_counts" in z.files else None
        meta = json.loads(str(z["meta"])) if "meta" in z.files else {}
    area_attr = (kind_cell_to_area_attr(kinds, amap, attr_map)
                 if (kinds is not None and amap is not None) else None)
    return c7lib.OccupancySeries(
        ticks=ticks,
        cell_counts=counts,
        area_attr=area_attr,
        tick_seconds=int(meta.get("tick_seconds", 60)),
        start_hour=int(meta.get("start_hour", 0)),
        meta={"source": f"journal:{path}", **meta},
    )


# ---------------------------------------------------------------- 報告


def report_markdown(series: c7lib.OccupancySeries, amap: c7lib.AreaMap,
                    gate: Mapping[str, Any] | None = None) -> str:
    tbl = series.area_hour_table(amap)
    share = c7lib.hour_share(tbl)
    peaks = c7lib.peak_hours(share)
    night = c7lib.night_residual(share)
    comp = c7lib.area_share(tbl)
    rows = []
    for i, name in enumerate(AREA_IDS):
        rows.append([
            name, c7lib.AREA_JA[name],
            amap.counts()[name], f"{amap.area_ha()[name]:.1f}",
            int(peaks[i]), f"{night[i]:.3f}", f"{comp[i]:.4f}",
        ])
    out = ["## ラン側の在圏プロファイル(形状のみ)", "",
           c7lib.markdown_table(
               ["area", "名称", "セル数", "面積[ha]", "ピーク時", "深夜残存率", "エリア構成シェア"],
               rows)]
    if gate is not None:
        out += ["", "## セル→エリア写像の自己検査(面積帯・expedient)", "",
                c7lib.markdown_table(
                    ["area", "ha", "帯", "判定"],
                    [[r["area"], r["ha"], f"{r['band'][0]}-{r['band'][1]}",
                      "OK" if r["ok"] else "NG"] for r in gate["per_area"]]),
                "", f"合計 {gate['total_ha']} ha(帯 {gate['total_band'][0]}-"
                f"{gate['total_band'][1]}) → {'OK' if gate['total_ok'] else 'NG'}"]
    at = series.attr_table()
    if at is not None:
        s = at / np.maximum(at.sum(axis=1, keepdims=True), 1e-12)
        out += ["", "## 属性構成(ラン側)", "",
                c7lib.markdown_table(
                    ["area"] + [c7lib.ATTR_JA[a] for a in ATTR_IDS],
                    [[AREA_IDS[i]] + [f"{v:.3f}" for v in s[i]] for i in range(len(AREA_IDS))])]
    return "\n".join(out)


# ---------------------------------------------------------------- CLI


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="C7: 5エリア×24時の在圏時系列を作る")
    ap.add_argument("--world", default="data/world/v2", help="世界資産ディレクトリ")
    ap.add_argument("--axes", default=None, help="境界定義 JSON(既定 tools/c7/area_axes_v0.json)")
    ap.add_argument("--out", default="docs/bench/c7", help="出力ディレクトリ")
    ap.add_argument("--build-map", action="store_true", help="セル→エリア写像表を作る")
    ap.add_argument("--sensitivity", action="store_true", help="境界 ±50m の感度を測る")
    ap.add_argument("--area-map", default=None, help="既存の写像表 JSON(無ければ --world から作る)")
    ap.add_argument("--journal", default=None, help="エンジン側フックが出した .npz")
    ap.add_argument("--record", action="store_true", help="その場で run_day を回して標本化する")
    ap.add_argument("--agents", type=int, default=5_000)
    ap.add_argument("--ticks", type=int, default=1_440)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--every", type=int, default=DEFAULT_EVERY, help="標本間隔[tick]")
    ap.add_argument("--checkpoint-every", type=int, default=120,
                    help="checkpoint 間隔[tick](T2-b の部分再ランと**同じ値**にすること)")
    ap.add_argument("--dilate-m", type=float, default=0.0, help="境界の膨張/収縮[m](感度用)")
    args = ap.parse_args(argv)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.sensitivity:
        res = sensitivity(args.world, args.axes)
        print(json.dumps(res, ensure_ascii=False, indent=1))
        (out_dir / "c7_area_map_sensitivity.json").write_text(
            json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
        return 0

    if args.area_map:
        amap = c7lib.AreaMap.from_json(json.loads(Path(args.area_map).read_text(encoding="utf-8")))
        gate = None
    else:
        amap, gate = build_map(args.world, args.axes, dilate_m=args.dilate_m)

    if args.build_map:
        doc = amap.to_json()
        doc["area_ha_gate"] = gate
        (out_dir / "c7_area_map.json").write_text(
            json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print(json.dumps({"counts": amap.counts(), "area_ha": amap.area_ha(),
                          "gate_ok": None if gate is None else gate["ok"]},
                         ensure_ascii=False, indent=1))
        if not (args.journal or args.record):
            return 0

    if args.journal:
        series = load_journal(args.journal, amap)
    elif args.record:
        from shibuya.engine.run import run_day
        from shibuya.world.state import World

        world = World.load_or_synthetic(Path(args.world), n_cells=139, seed=args.seed)
        rec = OccupancyRecorder(every=args.every)
        with rec:
            res = run_day(n_agents=args.agents, seed=args.seed, world=world, ticks=args.ticks,
                          checkpoint_every=args.checkpoint_every, world_dir=args.world)
        series = rec.series(amap, meta={"agents": args.agents, "seed": args.seed,
                                        "ticks": args.ticks, "every": args.every})
        write_journal(out_dir / "c7_occupancy.npz", rec.ticks, rec.cell_counts(),
                      rec.kind_cell_counts(), tick_seconds=60, start_hour=0,
                      world_dir=str(args.world), agents=args.agents, seed=args.seed)
        (out_dir / "c7_checkpoints.json").write_text(
            json.dumps(checkpoints_json(res, agents=args.agents, seed=args.seed,
                                        ticks=args.ticks,
                                        checkpoint_every=args.checkpoint_every),
                       ensure_ascii=False, indent=1), encoding="utf-8")
        print(res.summary())
    else:
        ap.error("--journal か --record か --build-map のどれかが要る")
        return 2

    doc = series.to_json(amap)
    (out_dir / "c7_occupancy.json").write_text(
        json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
    md = report_markdown(series, amap, gate)
    (out_dir / "c7_occupancy.md").write_text(md, encoding="utf-8")
    print(md)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
