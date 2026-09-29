# -*- coding: utf-8 -*-
"""attr_arms.py — **KDDI 写像の感度腕**(在圏の形 9b・D-115 ③・解析側・エンジン不変)。

正典: ``docs/design/v2-presence-shape-implementation-agenda.md`` §2(9b の 1〜6)・
``docs/research/v2-r56-kddi-attribute-definition-check.md`` §3/§4(親の一次確認=KDDI の 3 区分は**集計エリアに対する**
推定居住地/推定勤務地の内外で決まる・居住地優先・滞在 30 分以上・20 歳未満は除く)。

なぜ要るか
    現行の写像 ``c7lib.KIND_TO_ATTR`` は**種別 → 属性の固定**(舞台の内外)で、STUDENT は来街者・WORKER は居住者。
    KDDI の「エリア X の勤務者」は**推定勤務地がエリア X の人**なので、舞台内の別エリアに勤める通勤者はエリア X では
    来街者。写像を変えると H5(属性構成)が動く=モデルの欠点と定義のずれを分けるための腕。

腕(``--attr-map`` / ``--dwell-min`` / ``--exclude-under20``・既定=従来)
    ``kind``(既定)= ``c7lib.KIND_TO_ATTR``。``kind_student_worker`` = 同じで STUDENT → 勤務者。
    ``area`` = KDDI の判定順: ① 自宅エリア == 集計エリア → 居住者 ② 職場/学校エリア == 集計エリア → 勤務者
    ③ それ以外 → 来街者(エリアは 5 エリア写像 ``area_axes_v0.json`` で判定・5 エリア外/域外は −1)。
    ``dwell_min`` 0(既定)= 毎正時の標本(従来の journal と同じ数え方)。> 0 = 時間帯別に「その 1 時間帯に
    そのエリアに**連続** dwell_min 分以上」居た体だけを数える(KDDI の時間帯別=1 時間ごと・連続と読む=宣言)。
    ``exclude_under20`` = 20 歳未満を分母から除く。

入力
    体ごとの journal(``record`` サブコマンドが ``engine.resolve.apply`` を包んで毎 tick の ``cell`` を控える=
    **ソース非改変**・``occupancy_series.OccupancyRecorder`` と同じ便法)。エンジンの在圏 journal(種別 × セル ×
    正時)は体の軸を持たないので ``kind`` / ``kind_student_worker`` × 滞在 0 だけが出せる(``--kind-journal``)。

KDDI 側(開封済みの記録=検証・**判定しない**)
    ``docs/bench/c7/holdout/c7-day-4/c7_holdout_compare.json`` の obs(H2 のピーク時刻・H3 の深夜残存率・
    H4 のエリア構成・H5 の属性構成)を並べるだけ。H1 は obs の時刻シェアが記録に無い=空欄(封印は開けない)。

逐次ループ宣言: 滞在の腕だけ 時間帯 24 × エリア 5 × 1 時間の tick 60 のベクトル演算(体数に比例しない)。
"""

from __future__ import annotations

import argparse
import json
import math
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c7lib  # noqa: E402
import occupancy_series as occ  # noqa: E402

AREA_IDS = c7lib.AREA_IDS
ATTR_IDS = c7lib.ATTR_IDS
REPO_ROOT = c7lib.REPO_ROOT
ATTR_MAPS: tuple[str, ...] = ("kind", "area", "kind_student_worker")
#: 開封済みの KDDI の比較記録(c7-day-4)。obs のシェアと順位だけを読む(実数は載っていない)。
HOLDOUT_RECORD = REPO_ROOT / "docs" / "bench" / "c7" / "holdout" / "c7-day-4" / "c7_holdout_compare.json"
#: 現実同士のずれ(フロア): PT 2018 の日中ピーク内訳 所属なし/勤務通学 = 0.16(業務を足して 0.27)vs KDDI 1.66
#: (sub_e §2-3・anchors v0)。
FLOOR_PT_VISITOR_PER_WORKER: tuple[float, float] = (0.16, 0.27)
STUDENT_KIND = 5
UNDER20_AGE = 20


def kind_to_attr_map(mode: str) -> dict[int, str]:
    """種別の写像(``kind`` / ``kind_student_worker``)。"""
    m = dict(c7lib.KIND_TO_ATTR)
    if mode == "kind_student_worker":
        m[STUDENT_KIND] = "worker"
    elif mode != "kind":
        raise ValueError(f"種別の写像は kind / kind_student_worker(いま {mode!r})")
    return m


@dataclass(frozen=True)
class AgentAxes:
    """体の軸(起動時 1 回の写像)。エリアは ``AREA_IDS`` の索引・5 エリア外/域外は −1。"""

    kind: np.ndarray
    age: np.ndarray
    home_area: np.ndarray
    work_area: np.ndarray
    school_area: np.ndarray


def cells_to_area(cells: np.ndarray, area_of_cell: np.ndarray) -> np.ndarray:
    c = np.asarray(cells, dtype=np.int64)
    ok = (c >= 0) & (c < area_of_cell.size)
    return np.where(ok, np.asarray(area_of_cell, dtype=np.int64)[np.where(ok, c, 0)], -1)


def agent_axes(pop: Any, area_of_cell: np.ndarray, *, kind: np.ndarray | None = None) -> AgentAxes:
    """W16 の体の行 → 軸(自宅/職場/学校のセル → エリア)。起動時 1 回。

    ``kind`` = ラン中の種別(journal が控えた ``registry.kind``)。体数が母集団より多い縮小ランの保険として、
    母集団に行の無い体は 自宅/職場/学校 = −1(=どのエリアでも来街者)・年齢 = 不明(20 歳以上として残す)。
    行のある体の種別が母集団と食い違えば例外(行 i = 体 i の規約が崩れている)。
    """
    pk = np.asarray(pop.kind, dtype=np.int64)
    n = pk.size if kind is None else int(np.asarray(kind).size)
    m = min(n, pk.size)
    k = pk[:n].copy() if kind is None else np.asarray(kind, dtype=np.int64).copy()
    if kind is not None and not np.array_equal(k[:m], pk[:m]):
        raise ValueError("journal の種別が母集団の行と食い違う(行 i = 体 i の規約が崩れている)")

    def _col(values: Any, fill: int) -> np.ndarray:
        out = np.full(n, fill, dtype=np.int64)
        out[:m] = np.asarray(values, dtype=np.int64)[:m]
        return out

    return AgentAxes(
        kind=k,
        age=_col(pop.age, 255),
        home_area=cells_to_area(_col(pop.home_cell, -1), area_of_cell),
        work_area=cells_to_area(_col(pop.work_cell, -1), area_of_cell),
        school_area=cells_to_area(_col(pop.school_cell, -1), area_of_cell),
    )


def attr_matrix(axes: AgentAxes, mode: str) -> np.ndarray:
    """``(n, 5)`` の「体がエリア X に居るときの属性」(``ATTR_IDS`` の索引)。"""
    n = axes.kind.size
    idx = {a: i for i, a in enumerate(ATTR_IDS)}
    if mode in ("kind", "kind_student_worker"):
        m = kind_to_attr_map(mode)
        per = np.asarray([idx[m.get(int(k), "visitor")] for k in range(9)], dtype=np.int64)
        a = per[np.clip(axes.kind, 0, 8)]
        return np.repeat(a[:, None], len(AREA_IDS), axis=1)
    if mode != "area":
        raise ValueError(f"--attr-map は {ATTR_MAPS} のどれか(いま {mode!r})")
    x = np.arange(len(AREA_IDS))[None, :]
    home = axes.home_area[:, None] == x
    work = (axes.work_area[:, None] == x) | (axes.school_area[:, None] == x)
    out = np.full((n, len(AREA_IDS)), idx["visitor"], dtype=np.int64)
    out[work] = idx["worker"]
    out[home] = idx["resident"]  # 居住地優先(KDDI の判定順 ①→②)
    return out


def _longest_runs(in_area: np.ndarray) -> np.ndarray:
    """``(T, n)`` bool → 体ごとの最長の連続 True の長さ(T 行のベクトル演算)。"""
    cur = np.zeros(in_area.shape[1], dtype=np.int64)
    best = np.zeros(in_area.shape[1], dtype=np.int64)
    for row in in_area:  # 逐次ループ宣言: 1 時間帯の tick の数ぶん(60)
        cur = np.where(row, cur + 1, 0)
        best = np.maximum(best, cur)
    return best


def area_attr_hour(ticks: np.ndarray, cells: np.ndarray, area_of_cell: np.ndarray, attr: np.ndarray, *,
                   dwell_min: int = 0, keep: np.ndarray | None = None, tick_seconds: int = 60) -> np.ndarray:
    """体の journal → ``(24, 5, 3)`` の 時 × エリア × 属性 の在圏数。

    ``dwell_min == 0``: 毎正時の標本(同じ時の標本が複数あれば平均=``OccupancySeries.area_hour_table`` と同じ)。
    ``dwell_min > 0``: 時間帯ごとに「そのエリアに連続 ``dwell_min`` 分以上」居た体を 1 と数える。
    """
    t = np.asarray(ticks, dtype=np.int64)
    area = cells_to_area(cells, area_of_cell)  # (T, n)
    n = area.shape[1]
    k = np.ones(n, dtype=bool) if keep is None else np.asarray(keep, dtype=bool)
    minutes = t * int(tick_seconds) // 60
    hour = (minutes // 60) % 24
    out = np.zeros((24, len(AREA_IDS), len(ATTR_IDS)), dtype=np.float64)
    rows = np.arange(n)
    if int(dwell_min) <= 0:
        on_hour = (minutes % 60) == 0
        nh = np.zeros(24, dtype=np.float64)
        for j in np.flatnonzero(on_hour).tolist():  # 逐次ループ宣言: 正時の標本の数ぶん(≤ 24)
            a = area[j]
            ok = k & (a >= 0)
            at = attr[rows[ok], a[ok]]
            np.add.at(out[hour[j]], (a[ok], at), 1.0)
            nh[hour[j]] += 1.0
        return out / np.maximum(nh, 1.0)[:, None, None]
    need = int(math.ceil(float(dwell_min) * 60.0 / float(tick_seconds)))
    for h in range(24):  # 逐次ループ宣言: 時間帯 24
        sel = np.flatnonzero(hour == h)
        if sel.size == 0:
            continue
        win = area[sel]
        for x in range(len(AREA_IDS)):  # エリア 5
            stay = _longest_runs(win == x) >= need
            ok = stay & k
            if ok.any():
                np.add.at(out[h, x], attr[rows[ok], x], 1.0)
    return out


# ---------------------------------------------------------------- H2〜H5(開封済みの記録と並べる=判定しない)
def recorded_obs(path: Path = HOLDOUT_RECORD) -> dict[str, Any]:
    if not path.exists():
        return {}
    m = json.loads(path.read_text(encoding="utf-8")).get("metrics", {})
    return {"peak_hour": m.get("H2", {}).get("obs_peak_hour", {}),
            "night_residual": m.get("H3", {}).get("obs_night_residual", {}),
            "area_share": m.get("H4", {}).get("obs_share", {}),
            "attr_share": m.get("H5", {}).get("obs_share", {})}


def shape_metrics(table3: np.ndarray, obs: Mapping[str, Any], *, base_hour_share: np.ndarray | None = None
                  ) -> dict[str, Any]:
    """``(24, 5, 3)`` → H2〜H5 の値(sim)と開封済みの obs との差。**判定しない**(合否は書かない)。"""
    table = table3.sum(axis=2)            # (24, 5)
    share = c7lib.hour_share(table)       # (5, 24)
    peaks = c7lib.peak_hours(share)
    night = c7lib.night_residual(share)
    attr = table3.sum(axis=0)             # (5, 3)
    attr_share = attr / np.maximum(attr.sum(axis=1, keepdims=True), 1e-12)
    total = attr.sum(axis=0)
    total_share = total / max(float(total.sum()), 1e-12)
    wi, vi = ATTR_IDS.index("worker"), ATTR_IDS.index("visitor")
    out: dict[str, Any] = {
        "H1": {"measured": False, "reason": "obs の時刻シェアが開封済みの記録に無い(封印は開けない)=空欄"},
        "sim_peak_hour": {a: int(peaks[i]) for i, a in enumerate(AREA_IDS)},
        "sim_night_residual": {a: round(float(night[i]), 4) for i, a in enumerate(AREA_IDS)},
        "sim_area_share": {a: round(float(v), 4) for a, v in zip(AREA_IDS, c7lib.area_share(table))},
        "sim_attr_share": {a: [round(float(v), 4) for v in attr_share[i]] for i, a in enumerate(AREA_IDS)},
        "sim_total_attr_share": [round(float(v), 4) for v in total_share],
        "sim_visitor_per_worker": round(float(total[vi] / max(total[wi], 1e-12)), 4),
    }
    if base_hour_share is not None:
        out["hour_share_jsd_vs_kind_dwell0"] = {
            a: round(float(c7lib.jsd(share[i], base_hour_share[i])), 6) for i, a in enumerate(AREA_IDS)}
    if obs:
        op = np.asarray([obs["peak_hour"].get(a, 0) for a in AREA_IDS], dtype=np.int64)
        d = np.minimum(np.abs(peaks - op), 24 - np.abs(peaks - op))
        tau2 = c7lib.kendall_tau(peaks.tolist(), op.tolist())
        on = np.asarray([obs["night_residual"].get(a, 0.0) for a in AREA_IDS], dtype=np.float64)
        tau3 = c7lib.kendall_tau(night.tolist(), on.tolist())
        oa = np.asarray([obs["area_share"].get(a, 0.0) for a in AREA_IDS], dtype=np.float64)
        sa = c7lib.area_share(table)
        o5 = np.asarray([obs["attr_share"].get(a, [0, 0, 0]) for a in AREA_IDS], dtype=np.float64)
        per5 = [float(c7lib.jsd(attr_share[i], o5[i])) for i in range(len(AREA_IDS))]
        kd_total = (o5 * (oa / max(oa.sum(), 1e-12))[:, None]).sum(axis=0)
        out |= {
            "H2": {"abs_hour_diff": {a: int(d[i]) for i, a in enumerate(AREA_IDS)},
                   "n_within_1h": int((d <= 1).sum()), "kendall_tau": None if math.isnan(tau2) else round(tau2, 4)},
            "H3": {"abs_diff_max": round(float(np.max(np.abs(night - on))), 4),
                   "kendall_tau": None if math.isnan(tau3) else round(tau3, 4)},
            "H4": {"jsd": round(float(c7lib.jsd(sa, oa)), 6), "abs_share_diff_max": round(float(np.max(np.abs(sa - oa))), 4)},
            "H5": {"per_area_jsd": {a: round(per5[i], 6) for i, a in enumerate(AREA_IDS)},
                   "jsd_mean": round(float(np.mean(per5)), 6),
                   "abs_share_diff_max": round(float(np.max(np.abs(attr_share - o5))), 4),
                   "kddi_total_attr_share_h4_weighted": [round(float(v), 4) for v in kd_total],
                   "kddi_visitor_per_worker": round(float(kd_total[vi] / max(kd_total[wi], 1e-12)), 4),
                   "floor_pt_visitor_per_worker": list(FLOOR_PT_VISITOR_PER_WORKER)},
        }
    return out


# ---------------------------------------------------------------- 体の journal(record)
class AgentCellRecorder:
    """``engine.resolve.apply`` を包み、毎 tick の ``cell`` を控える(**ソース非改変**・書き込みなし)。"""

    def __init__(self, every: int = 1) -> None:
        self.every = int(every)
        self.ticks: list[int] = []
        self.cells: list[np.ndarray] = []
        self.transit: list[np.ndarray] = []
        self.kind: np.ndarray | None = None
        self._orig = None
        self._module = None

    def attach(self) -> "AgentCellRecorder":
        from shibuya.engine import resolve as module

        self._module = module
        self._orig = module.apply
        rec = self

        def _wrapped(plan_confirmed, losers, agents, world, tick, **kw):
            out = rec._orig(plan_confirmed, losers, agents, world, tick, **kw)
            if rec.every > 0 and int(tick) % rec.every == 0:
                reg = agents.registry
                if rec.kind is None:
                    rec.kind = np.asarray(reg.field("kind"), dtype=np.int8).copy()  # reg.kind は別物(SoA の種類名)
                rec.ticks.append(int(tick))
                rec.cells.append(np.asarray(reg.cell, dtype=np.int16).copy())
                rec.transit.append(np.asarray(reg.transit_state, dtype=np.int8).copy())
            return out

        module.apply = _wrapped
        return self

    def detach(self) -> None:
        if self._module is not None:
            self._module.apply = self._orig
        self._module = None


def save_agent_journal(path: Path, rec: AgentCellRecorder, **meta: Any) -> Path:
    """体の journal(``ticks`` (T,)・``cells`` (T, n) int16・``transit`` (T, n) int8・``kind`` (n,) int8・``meta``)。"""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(p, ticks=np.asarray(rec.ticks, dtype=np.int64), cells=np.stack(rec.cells).astype(np.int16),
                        transit=np.stack(rec.transit).astype(np.int8),
                        kind=np.asarray(rec.kind, dtype=np.int8),
                        meta=np.asarray(json.dumps(meta, ensure_ascii=False)))
    return p


def load_agent_journal(path: Path) -> dict[str, Any]:
    with np.load(Path(path), allow_pickle=False) as z:
        return {"ticks": np.asarray(z["ticks"], dtype=np.int64), "cells": np.asarray(z["cells"], dtype=np.int16),
                "transit": np.asarray(z["transit"], dtype=np.int8) if "transit" in z.files else None,
                "kind": np.asarray(z["kind"], dtype=np.int64) if "kind" in z.files else None,
                "meta": json.loads(str(z["meta"])) if "meta" in z.files else {}}


def kind_journal_table(ticks: np.ndarray, kind_cell: np.ndarray, amap: Any, mode: str) -> np.ndarray:
    """エンジンの在圏 journal(種別 × セル・正時)→ ``(24, 5, 3)``(``kind`` / ``kind_student_worker`` だけ)。"""
    aa = occ.kind_cell_to_area_attr(kind_cell, amap, kind_to_attr_map(mode)).astype(np.float64)
    hours = (np.asarray(ticks, dtype=np.int64) // 60) % 24  # tick = 60 秒(journal の meta と同じ)
    t3 = np.zeros((24, len(AREA_IDS), len(ATTR_IDS)))
    nh = np.zeros(24)
    np.add.at(t3, hours, aa)
    np.add.at(nh, hours, 1.0)
    return t3 / np.maximum(nh, 1.0)[:, None, None]


def population_for(world: str, n_agents: int, seed: int) -> Any:
    """``engine.run._resolve_population`` と同じ規約で体の行を取る(行 i = 体 i)。"""
    from shibuya.agents.population import load_population, sample_population

    pop = load_population(world, n=None, seed=seed)
    return sample_population(pop, n_agents, seed) if pop.n > n_agents else pop


def arms_grid(ticks: np.ndarray, cells: np.ndarray, axes: AgentAxes, area_of_cell: np.ndarray,
              obs: Mapping[str, Any], *, attr_maps: Sequence[str] = ATTR_MAPS, dwells: Sequence[int] = (0, 30),
              under20: Sequence[bool] = (False, True)) -> list[dict[str, Any]]:
    """腕の格子(写像 × 滞在 × 20 歳未満)の H2〜H5。"""
    base = area_attr_hour(ticks, cells, area_of_cell, attr_matrix(axes, "kind"))
    base_share = c7lib.hour_share(base.sum(axis=2))
    rows = []
    for mode in attr_maps:
        att = attr_matrix(axes, mode)
        for dw in dwells:
            for u20 in under20:
                keep = axes.age >= UNDER20_AGE if u20 else None
                t3 = area_attr_hour(ticks, cells, area_of_cell, att, dwell_min=int(dw), keep=keep)
                rows.append({"attr_map": mode, "dwell_min": int(dw), "exclude_under20": bool(u20),
                             "person_hours": round(float(t3.sum()), 1),
                             **shape_metrics(t3, obs, base_hour_share=base_share)})
    return rows


def kind_journal_rows(path: Path, amap: Any, obs: Mapping[str, Any]) -> dict[str, Any]:
    """エンジンの在圏 journal だけから出せる腕(``kind`` / ``kind_student_worker`` × 滞在 0 × 20 歳未満を含む)。"""
    with np.load(Path(path), allow_pickle=False) as z:
        ticks = np.asarray(z["ticks"], dtype=np.int64)
        kinds = np.asarray(z["kind_cell_counts"])
        meta = json.loads(str(z["meta"])) if "meta" in z.files else {}
    if int(meta.get("tick_seconds", 60)) != 60 or int(meta.get("start_hour", 0)) != 0:
        raise ValueError("journal の tick_seconds / start_hour が 60 / 0 でない(この入口は未対応)")
    rows = []
    for mode in ("kind", "kind_student_worker"):
        t3 = kind_journal_table(ticks, kinds, amap, mode)
        rows.append({"attr_map": mode, "dwell_min": 0, "exclude_under20": False,
                     "person_hours": round(float(t3.sum()), 1), **shape_metrics(t3, obs)})
    return {"rows": rows, "n_samples": int(ticks.size),
            "not_computable": ["attr_map=area(体の自宅/職場の軸が無い)", "dwell_min=30(正時の標本しか無い)",
                               "exclude_under20(年齢の軸が無い)"]}


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="KDDI 写像の感度腕(9b・解析側)")
    ap.add_argument("--journal", default="", help="体の journal(.npz・record で作る)")
    ap.add_argument("--kind-journal", default="", help="エンジンの在圏 journal(種別 × セル・kind の 2 腕だけ)")
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--n-agents", type=int, default=5_000)
    ap.add_argument("--seed", type=int, default=1)
    ap.add_argument("--attr-map", choices=ATTR_MAPS, default="kind")
    ap.add_argument("--dwell-min", type=int, default=0)
    ap.add_argument("--exclude-under20", action="store_true")
    ap.add_argument("--all-arms", action="store_true", help="写像 3 × 滞在 0/30 × 20 歳未満 off/on の格子")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    amap, _gate = occ.build_map(args.world)
    area_of_cell = np.asarray(amap.area_of_cell, dtype=np.int64)
    obs = recorded_obs()
    doc: dict[str, Any] = {"schema": "shibuya.tools.c7/attr-arms/1", "obs_source": "c7-day-4 開封済みの比較記録"}
    if args.kind_journal:
        doc["kind_journal"] = kind_journal_rows(Path(args.kind_journal), amap, obs)
    if args.journal:
        j = load_agent_journal(Path(args.journal))
        ticks, cells, meta = j["ticks"], j["cells"], j["meta"]
        pop = population_for(args.world, int(meta.get("n_agents", args.n_agents)), int(meta.get("seed", args.seed)))
        axes = agent_axes(pop, area_of_cell, kind=j["kind"])
        if args.all_arms:
            doc["rows"] = arms_grid(ticks, cells, axes, area_of_cell, obs)
        else:
            keep = axes.age >= UNDER20_AGE if args.exclude_under20 else None
            t3 = area_attr_hour(ticks, cells, area_of_cell, attr_matrix(axes, args.attr_map),
                                dwell_min=args.dwell_min, keep=keep)
            doc["rows"] = [{"attr_map": args.attr_map, "dwell_min": args.dwell_min,
                            "exclude_under20": bool(args.exclude_under20), **shape_metrics(t3, obs)}]
        doc["journal_meta"] = meta
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
