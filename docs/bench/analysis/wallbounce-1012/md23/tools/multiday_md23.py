"""第 2 期 2-3 複数日の mock(10g)の道具: 7 日のランの日ごとの量・再開=通し・W9 の窓の資産の版の表(記録を出すだけ)。

エンジンは変えない。関数を包んで参照を控えるだけ(``engine.systems.state_io.day_record`` の後に日の終わりの体の SoA と層を読む・
2-0 の計器と同じ ``AgentCellRecorder`` で刻みごとのセルと域外の状態を控える・母集団の参照を控える)。戻り値は変えない。

段(どれも作業木の src・``PYTHONPATH`` に作業木の ``src``):

    python $D/multiday_md23.py run --config default --days 5 --scratch $W --out $W/md23_default.json
    python $D/multiday_md23.py side --configs default,a,b,c,d --days 5 --scratch $W --out-dir $W --jobs 2
    python $D/multiday_md23.py side --days 7 --allow-rest-days ...   # 付録(test_only)
    python $D/multiday_md23.py resume --config default --scratch $W --out $W/resume_default.json
    python $D/multiday_md23.py w9 --a data/world/v2 --b data/world/v2_stage_2-3 --out $D/w9_stage_2-3.json
    python $D/multiday_md23.py table --runs $W/md23_default.json $W/md23_a.json ... --out $D/days7.json

構成(``CONFIGS``): 土台=byte-check の ``v3_mem_rel``(語彙 v3・記憶 on・関係 on=記憶の行と関係辺を測るため)・腕は全部 off。
``a``=``--memory-store events``・``b``=``--proximity distance``・``c``=``--economy-stage2 on``・``d``=a+b+c。

日ごとの量(``day_rows``): 呼数(日次の記録 ``calls_by_model.llm``)・会話(開いた/閉じたセッション)・関係辺(埋まった欄・
生きている辺 A ≥ τ_rel・15 欄が埋まった体の割合=満杯率・生きている辺が 15 本の体の割合・知人の辺・τ_rel の逆算=体ごとの
15 番目の辺の A の中央値)・記憶の行(表の行・満杯の体・器の出どころ legacy/記録)・財布(世帯の現金の 1 体あたりの分位と
平均・前の日からの増減)・段階 2 の日の欄(引き出し・賃金・預金の分位=c・d)・出来事の記録(行・語の分布)・在圏のピークと
到着の波(2-0 の計器の式=``anchor_gauge`` の関数を日ごとの刻みに当てる)・状態のファイルの大きさ・壁時計・影の日。
**曜日の比較はしない**(K9=W17 v2 は月曜の行しか無い=火〜日も月曜の予定・``BR-K9-MONDAY``)。

**開始日の検査(A1-3)**: エンジンは複数日のランを連続する平日に限る(決定 10-03 A1-3 (a)・CA10 (c)=分析用の週末の
ランはカレンダー化の第 1 段の後)。正の表は 5 日(月〜金・検査を外さない=親の判断 M1)。``--allow-rest-days`` のときだけ、
この道具が ``SimCalendar.check_start`` を包み、規則の違反(土休を含む)を止めずに記録の ``start_check_waived`` に写す
(止める違反=祝日の表の外・表が読めない は今のまま止める)=付録の 7 日(参考)。エンジンの検査は変えていない。記録の印は
``test_only``(試験用=分析に使わない印)。

絶対パスは JSON に書かない。逐次ループ宣言: 日の数ぶん(日の終わりの読み)・刻みの数(計器の記録=2-0 と同じ)。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Mapping, Sequence

import numpy as np

HERE = Path(__file__).resolve()
REPO = HERE.parents[6]
SCHEMA = "shibuya.md23/multiday/1"
#: 土台の構成(byte-check の v3_mem_rel)と腕の組。
BASE: dict[str, Any] = {"vocab_version": "v3", "memory": "on", "relations": "on"}
CONFIGS: dict[str, dict[str, str]] = {
    "default": {},
    "a": {"memory_store": "events"},
    "b": {"proximity": "distance"},
    "c": {"economy_stage2": "on"},
    "d": {"memory_store": "events", "proximity": "distance", "economy_stage2": "on"},
}
QUANTS: tuple[int, ...] = (10, 50, 90)


def _paths() -> None:
    for p in (str(REPO / "src"), str(REPO / "tools" / "instruments"), str(REPO / "tools" / "c7")):
        if p not in sys.path:
            sys.path.insert(0, p)


def set_arms(config: str) -> dict[str, str]:
    """腕を選ぶ(組み立てが読む切替口)。このプロセスの中だけ。"""
    _paths()
    from shibuya.engine import economy_stage2 as ES2
    from shibuya.engine import memory_store as MS
    from shibuya.engine import proximity as PX

    arms = CONFIGS[config]
    MS.set_arm(arms.get("memory_store", "mem"))
    PX.set_arm(arms.get("proximity", "cell"))
    ES2.set_arm(arms.get("economy_stage2", "off"))
    return dict(arms)


def _q(x: np.ndarray) -> dict[str, float]:
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return {}
    return {f"p{q}": round(float(np.percentile(x, q)), 1) for q in QUANTS} | {"mean": round(float(x.mean()), 1)}


# ====================================================================== 日の終わりの読み(状態は書かない)
def relation_view(agents: Any, tick: int, minutes_per_tick: float) -> dict[str, Any] | None:
    """関係辺の表(``rel_*``)の日の終わりの量。関係 off のランは ``None``。"""
    from shibuya.engine.memory import activation_rows
    from shibuya.engine.relations import REL_D, REL_K, REL_KINDS, REL_TAU, tau_from_edges

    r = agents.registry
    if "rel_partner" not in r:
        return None
    part = np.asarray(r.rel_partner, dtype=np.int64)
    filled = part >= 0
    A = activation_rows(np.asarray(r.rel_n), np.asarray(r.rel_first), int(tick), float(minutes_per_tick), REL_D)
    A = np.where(filled, A, -np.inf)
    live = filled & (A >= REL_TAU)
    k = part.shape[1]
    u = np.nonzero(filled)
    cal = tau_from_edges(u[0], A[u], int(part.shape[0]), k=REL_K)
    kind = np.asarray(r.rel_kind, dtype=np.int64)
    return {
        "k": int(k), "tau_rel": float(REL_TAU),
        "edges_filled": int(filled.sum()), "edges_live": int(live.sum()),
        "edges_per_agent": round(float(filled.sum()) / max(1, part.shape[0]), 3),
        "full_rate": round(float((filled.sum(axis=1) == k).mean()), 4),
        "full_live_rate": round(float((live.sum(axis=1) == k).mean()), 4),
        "acquaintance_edges": int((filled & (kind == REL_KINDS["acquaintance"])).sum()),
        "by_kind": {name: int((filled & (kind == c)).sum()) for name, c in REL_KINDS.items()},
        "tau_recalibrated": (None if not math.isfinite(cal["tau"]) else round(float(cal["tau"]), 4)),
        "share_with_k_edges": cal["share_with_k_edges"],
    }


def memory_view(agents: Any, mem_layer: Any) -> dict[str, Any] | None:
    """記憶の表と器の日の終わりの量。記憶 off のランは ``None``。"""
    if mem_layer is None:
        return None
    r = agents.registry
    used = np.asarray(r.mem_kind) != 0
    per = used.sum(axis=1)
    out: dict[str, Any] = {"rows": int(used.sum()), "rows_per_agent": _q(per),
                           "full_agents": int((per == int(mem_layer.n_rows)).sum()),
                           "evictions": int(mem_layer.stats.get("evictions", 0))}
    ms = getattr(mem_layer, "memory_store", None)
    if ms is not None:
        s = ms.summary()
        out["store"] = {"rows": s["rows"], "origins": s["origins"], "targets_log_live": s.get("targets_log_live"),
                        "targets_log_gone": s.get("targets_log_gone")}
    return out


def money_view(agents: Any) -> dict[str, Any]:
    cash = np.asarray(agents.registry.money, dtype=np.int64)
    return {"cash_total": int(cash.sum()), "cash_per_agent": _q(cash), "cash_zero": int((cash <= 0).sum())}


class DayProbe:
    """``state_io.day_record`` を包み、日の締めの記録の後に日の終わりの量を控える(書かない)。"""

    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []
        self.t0 = time.perf_counter()
        self._orig: Any = None
        self._mod: Any = None

    def attach(self) -> "DayProbe":
        from shibuya.engine.systems import state_io as SIO

        self._mod, self._orig = SIO, SIO.day_record
        probe = self

        def _wrapped(b: Any, d: int) -> None:
            probe._orig(b, d)
            probe.rows.append(probe.snapshot(b, int(d)))

        SIO.day_record = _wrapped
        return self

    def detach(self) -> None:
        if self._mod is not None:
            self._mod.day_record = self._orig
        self._mod = None

    def snapshot(self, b: Any, d: int) -> dict[str, Any]:
        agents, L = b.soa.agents, b.layers
        tpd, step_s = int(b.cfg.tpd), int(b.cfg.tick_seconds)
        tick = (d + 1) * tpd - 1
        conv = L.conv
        now = time.perf_counter()
        out = {
            "day": d, "wall_s_nondeterministic": round(now - self.t0, 1),
            "conv": None if conv is None else {"opened": int(conv.n_opened),
                                               "closed": int(sum(conv.closed_by_reason.values())),
                                               "joined": int(len(getattr(conv, "join_events", ())))},
            "relations": relation_view(agents, tick, step_s / 60.0),
            "memory": memory_view(agents, L.mem_layer),
            "money": money_view(agents),
        }
        self.t0 = now
        return out


# ====================================================================== 2-0 の計器を日ごとに
def gauge_days(rec: Any, pop: Any, n_days: int, tpd: int) -> list[dict[str, Any]] | None:
    """2-0 の計器の式(在圏のピーク 3-1 の本則=sim/sum/θ1・到着の波 3-3)を日ごとの刻みに当てる。"""
    if pop is None or not rec.ticks:
        return None
    import anchor_gauge as AG

    paths = AG.resolve_paths()
    guard = AG.make_guard(paths)
    S = AG.load_static(guard, paths)
    ticks = np.asarray(rec.ticks, dtype=np.int64)
    cells = np.stack(rec.cells).astype(np.int64)
    transit = np.stack(rec.transit).astype(np.int64)
    n = cells.shape[1]
    kind = np.asarray(pop.kind, dtype=np.int64)[:n]
    omega = AG.expansion_factors(S.w16["kind"], kind)
    keep = AG.population_masks(kind, np.asarray(pop.age)[:n], np.asarray(pop.is_foreign)[:n])["P_prime"]
    dn = np.asarray(pop.direction_node, dtype=np.int64)[:n]
    nn = len(AG.node_ids(S))
    out: list[dict[str, Any]] = []
    for d in range(n_days):  # 逐次ループ宣言: 日の数ぶん
        sel = np.flatnonzero((ticks >= d * tpd) & (ticks < (d + 1) * tpd))
        if sel.size == 0:
            continue
        area_s, stage_s = AG.area_and_stage(cells[sel], transit[sel], S.area_of_cell)
        hm, best = AG.hour_minutes(area_s, stage_s, ticks[sel])
        q = AG.daily_qualified(hm, best, "sum")
        N = AG.presence_hourly(hm, q, omega, keep, AG.THETA_MAIN)
        pk = AG.peaks_block(N)
        lo = sel[0] - 1 if sel[0] > 0 else sel[0]  # 日の頭の刻みに着いた体も数える(前の日の最後の刻みから)
        idx = np.arange(lo, sel[-1] + 1)
        A, n_arr = AG.arrivals_table(transit[idx], ticks[idx], dn, omega, nn)
        tot = A[:nn].sum(axis=0)
        out.append({"day": d, "presence_peak": {c: pk["peak"][c] for c in ("stage", "total5")},
                    "presence_level": {c: pk["level"][c] for c in ("stage", "total5")},
                    "presence_peak_value": {c: round(float(N[AG.COLS.index(c)].max()), 1) for c in ("stage", "total5")},
                    "arrivals_n": int(n_arr), "arrivals_weighted": round(float(tot.sum()), 1),
                    "arrivals_peak_hour": AG.peak_hour(tot)})
    return out


# ====================================================================== 1 本のラン
def run_collect(config: str, *, days: int, agents: int, seed: int, world: str | None, scratch: Path | None,
                gauge: bool = True, extra: Mapping[str, Any] | None = None,
                allow_rest_days: bool = False) -> dict[str, Any]:
    """1 本回して日ごとの量の JSON を返す(同じプロセスで腕を選ぶ)。"""
    _paths()
    arms = set_arms(config)
    from shibuya import cli
    from shibuya.engine import run as RUN

    kw: dict[str, Any] = dict(BASE, n_agents=agents, seed=seed, sim_days=days, world_dir=world)
    kw.update(dict(extra or {}))
    state_dir = None
    if scratch is not None:
        state_dir = Path(scratch) / f"state_md23_{config}"
        state_dir.mkdir(parents=True, exist_ok=True)
        kw["state_out"] = str(state_dir)
    from shibuya.engine import calendar as CAL

    waived: list[str] = []
    orig_cs = CAL.SimCalendar.check_start

    def _check_start(self: Any, sim_days: int = 1) -> list[str]:  # A1-3 の規則の違反だけを記録に写す(止める違反は止める)
        fatal, rule = self.start_problems(sim_days)
        if fatal:
            raise ValueError("開始日の検査で止めた: " + " / ".join(fatal))
        waived.extend(rule)
        return []

    if allow_rest_days:
        CAL.SimCalendar.check_start = _check_start  # type: ignore[method-assign]
    probe = DayProbe().attach()
    rec = None
    cap: dict[str, Any] = {}
    orig_pop = RUN._resolve_population
    if gauge and world is not None:
        import attr_arms as AA

        rec = AA.AgentCellRecorder(every=1).attach()

        def _pop(*a: Any, **k: Any) -> Any:
            got = orig_pop(*a, **k)
            cap.setdefault("pop", got)
            return got

        RUN._resolve_population = _pop
    t0 = time.perf_counter()
    try:
        res = cli.run(**kw)
    finally:
        probe.detach()
        if rec is not None:
            rec.detach()
        RUN._resolve_population = orig_pop
        CAL.SimCalendar.check_start = orig_cs  # type: ignore[method-assign]
    wall = time.perf_counter() - t0
    man = res.run_manifest_fields()
    from shibuya.core.time_consts import STEPS_PER_DAY

    tpd = int(STEPS_PER_DAY)
    g = gauge_days(rec, cap.get("pop"), days, tpd) if rec is not None else None
    del rec
    files = []
    if state_dir is not None:
        for p in sorted(state_dir.glob("*")):
            if p.is_file():
                files.append({"name": p.name, "bytes": p.stat().st_size})
    weather = [{k: d.get(k) for k in ("day", "calendar_date", "replay_date", "how", "shadow_date", "shadow_fallback")}
               for d in ((man.get("weather") or {}).get("days") or [])]
    daily = []
    for d in man.get("daily", []):
        e = d.get("economy") or {}
        daily.append({"day": d["day"], "llm_calls": (d.get("calls_by_model") or {}).get("llm"),
                      "money": d.get("money"), "events": d.get("events"),
                      "stage2": e.get("stage2")})
    return {
        "schema": SCHEMA, "config": config, "arms": arms, "base": dict(BASE), "agents": agents, "seed": seed,
        "days": days, "world": None if world is None else str(world).replace("\\", "/"),
        "final": str(res.final_hash)[:16], "calls": int(res.llm_calls),
        "money_start": int(getattr(res, "money_start", 0)),
        "memory_store": (man.get("memory_summary") or {}).get("memory_store"),
        "start_check_waived": waived, "test_only": bool(waived),
        "daily": daily, "probe": probe.rows, "gauge": g, "weather": weather, "state_files": files,
        "wall_s_nondeterministic": round(wall, 1),
    }


def cmd_run(args: argparse.Namespace) -> int:
    doc = run_collect(args.config, days=args.days, agents=args.agents, seed=args.seed, world=args.world,
                      scratch=Path(args.scratch), gauge=not args.no_gauge, allow_rest_days=args.allow_rest_days)
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"config": args.config, "final": doc["final"], "calls": doc["calls"],
                      "wall_s": doc["wall_s_nondeterministic"]}, ensure_ascii=False))
    return 0


def cmd_side(args: argparse.Namespace) -> int:
    env = dict(os.environ)
    env["PYTHONIOENCODING"] = "utf-8"
    env["PYTHONPATH"] = str(REPO / "src")
    names = [c for c in args.configs.split(",") if c]
    out_dir = Path(args.out_dir)

    def _one(c: str) -> tuple[str, int, str]:
        cmd = [sys.executable, str(HERE), "run", "--config", c, "--days", str(args.days), "--agents", str(args.agents),
               "--seed", str(args.seed), "--world", args.world, "--scratch", args.scratch,
               "--out", str(out_dir / f"md23_{c}.json")] + (["--allow-rest-days"] if args.allow_rest_days else [])
        p = subprocess.run(cmd, env=env, cwd=str(REPO), capture_output=True, text=True, encoding="utf-8")
        return c, p.returncode, (p.stdout[-2000:] + p.stderr[-4000:])

    with cf.ThreadPoolExecutor(max_workers=int(args.jobs)) as ex:
        for c, rc, tail in ex.map(_one, names):
            print(f"== {c} rc={rc}\n{tail}")
    return 0


# ====================================================================== 再開=通し(日の境目)
def cmd_resume(args: argparse.Namespace) -> int:
    """2 日の通しと、1 日目の終わり(日の境目)で保存 → 2 日目を再開の final・checkpoint を比べる(同じプロセスで腕を選ぶ)。"""
    _paths()
    arms = set_arms(args.config)
    from shibuya import cli

    from shibuya.core.time_consts import STEPS_PER_DAY

    tpd = int(STEPS_PER_DAY)
    kw: dict[str, Any] = dict(BASE, n_agents=args.agents, seed=args.seed, sim_days=2, world_dir=args.world)
    base = Path(args.scratch) / f"resume_md23_{args.config}"
    base.mkdir(parents=True, exist_ok=True)
    t0 = time.perf_counter()
    straight = cli.run(**kw)
    a = cli.run(**kw, state_out=str(base / "a"), stop_at_tick=tpd)
    sf = [f for f in a.resume["state_files"] if int(f.get("T", -1)) == tpd] or a.resume["state_files"][-1:]
    b = cli.run(**kw, resume_from=str(base / "a" / sf[-1]["file"]))
    cp = lambda r: [(int(c.tick), str(c.behavior_hash)[:16], str(c.full_hash)[:16])  # noqa: E731
                    for c in r.checkpoints if int(c.tick) >= tpd]
    doc = {"config": args.config, "arms": arms, "agents": args.agents, "seed": args.seed,
           "straight_final": str(straight.final_hash)[:16], "resumed_final": str(b.final_hash)[:16],
           "same_final": straight.final_hash == b.final_hash,
           "checkpoints_after_boundary_same": cp(straight) == cp(b), "n_checkpoints_compared": len(cp(b)),
           "state_file": sf[-1]["file"], "calls": [int(straight.llm_calls), int(a.llm_calls) + int(b.llm_calls)],
           "wall_s_nondeterministic": round(time.perf_counter() - t0, 1)}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc, ensure_ascii=False))
    return 0 if doc["same_final"] and doc["checkpoints_after_boundary_same"] else 1


# ====================================================================== W9 の窓の資産の版の表
def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for blk in iter(lambda: f.read(1 << 20), b""):
            h.update(blk)
    return h.hexdigest()


def cmd_w9(args: argparse.Namespace) -> int:
    """資産 2 つ(前=HEAD の v2・後=v2_stage_2-3)の W9 の版の表と、動いたファイルの一覧(sha256 の先頭 16 桁)。"""
    A, B = Path(args.a), Path(args.b)
    names = sorted({p.name for p in A.iterdir() if p.is_file()} | {p.name for p in B.iterdir() if p.is_file()})
    moved, same, only_a, only_b = [], 0, [], []
    for n in names:  # 逐次ループ宣言: ファイルの数ぶん
        pa, pb = A / n, B / n
        if not pa.exists():
            only_b.append(n)
        elif not pb.exists():
            only_a.append(n)
        elif _sha(pa) != _sha(pb):
            moved.append({"name": n, "a": _sha(pa)[:16], "b": _sha(pb)[:16]})
        else:
            same += 1
    ha = json.loads((A / "W9.header.json").read_text(encoding="utf-8"))
    hb = json.loads((B / "W9.header.json").read_text(encoding="utf-8"))
    mb = json.loads((B / "build_manifest.json").read_text(encoding="utf-8"))
    shadows = [{"date": p.name[len("w9_shadow_"):-len(".npy")], "bytes": p.stat().st_size, "sha256_16": _sha(p)[:16],
                "same_as_a": (A / p.name).exists() and _sha(A / p.name) == _sha(p)}
               for p in sorted(B.glob("w9_shadow_2*.npy"))]
    doc = {"a": str(args.a).replace("\\", "/"), "b": str(args.b).replace("\\", "/"),
           "w9": {k: {"stage_version": h.get("stage_version"), "param_hash": str(h.get("param_hash", ""))[:16],
                      "input_hash": str(h.get("input_hash", ""))[:16],
                      "shadow_dates": (h.get("params") or {}).get("shadow_dates"),
                      "failed_gates": sorted(g for g, v in (h.get("gates") or {}).items() if not v.get("pass", True))}
                  for k, h in (("a", ha), ("b", hb))},
           "b_build_hash": str(mb.get("build_hash", ""))[:16], "b_kept": mb.get("kept"),
           "shadows_b": shadows, "files_moved": moved, "files_same": same, "only_a": only_a, "only_b": only_b}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("b_build_hash", "files_same", "only_b")}, ensure_ascii=False))
    return 0


# ====================================================================== 表(記録の材料)
def day_rows(doc: Mapping[str, Any]) -> list[dict[str, Any]]:
    """1 本のランの JSON → 日ごとの行(記録の表の材料)。財布の増減は前の日の終わり(1 日目はランの頭)からの 1 体あたり。"""
    n = int(doc["agents"])
    probe = {int(p["day"]): p for p in doc.get("probe") or []}
    gauge = {int(g["day"]): g for g in doc.get("gauge") or []}
    # 状態のファイル: 日の境目ごとに見出し(.json)と配列(.npz)の 2 本=刻みの番号でまとめて足す
    by_t: dict[str, int] = {}
    for f in doc.get("state_files") or []:
        stem = f["name"].rsplit(".", 1)[0]
        by_t[stem] = by_t.get(stem, 0) + int(f["bytes"])
    files = [{"name": k, "bytes": v} for k, v in sorted(by_t.items())]
    prev_cash = int(doc.get("money_start") or 0)
    rows = []
    prev_conv = {"opened": 0, "closed": 0}
    for i, d in enumerate(doc.get("daily") or []):  # 逐次ループ宣言: 日の数ぶん
        day = int(d["day"])
        p = probe.get(day, {})
        cash = int(((d.get("money") or {}).get("households")) or 0)
        conv = p.get("conv") or {}
        rel = p.get("relations") or {}
        mem = p.get("memory") or {}
        ev = d.get("events") or {}
        s2 = d.get("stage2") or {}
        g = gauge.get(day) or {}
        body = {k: v for k, v in (ev.get("by_what") or {}).items()
                if k.startswith("行為:") or k.startswith("知覚:") or k == "道具:看板"}
        row = {
            "day": day, "llm_calls": d.get("llm_calls"),
            "conv_opened": (conv.get("opened", 0) - prev_conv["opened"]) if conv else None,
            "conv_closed": (conv.get("closed", 0) - prev_conv["closed"]) if conv else None,
            "edges_live": rel.get("edges_live"), "edges_filled": rel.get("edges_filled"),
            "full_rate": rel.get("full_rate"), "full_live_rate": rel.get("full_live_rate"),
            "acquaintance_edges": rel.get("acquaintance_edges"), "tau_recalibrated": rel.get("tau_recalibrated"),
            "mem_rows": mem.get("rows"), "mem_full_agents": mem.get("full_agents"),
            "store_origins": (mem.get("store") or {}).get("origins"),
            "cash_per_agent_change": round((cash - prev_cash) / n, 1) if n else None,
            "cash_per_agent": (p.get("money") or {}).get("cash_per_agent"),
            "withdraw": (s2.get("withdraw") or {}).get("amount") if s2 else None,
            "withdraw_count": (s2.get("withdraw") or {}).get("count") if s2 else None,
            "wages": (s2.get("wages") or {}).get("amount") if s2 else None,
            "deposit": s2.get("deposit") if s2 else None,
            "events_rows": ev.get("rows"), "body_events": sum(body.values()) if body else 0,
            "presence_peak_stage": (g.get("presence_peak") or {}).get("stage"),
            "presence_peak_value_stage": (g.get("presence_peak_value") or {}).get("stage"),
            "arrivals_n": g.get("arrivals_n"), "arrivals_peak_hour": g.get("arrivals_peak_hour"),
            "state_file_bytes": files[i]["bytes"] if i < len(files) else None,
            "wall_s_nondeterministic": p.get("wall_s_nondeterministic"),
        }
        prev_cash = cash
        if conv:
            prev_conv = {"opened": conv.get("opened", 0), "closed": conv.get("closed", 0)}
        rows.append(row)
    return rows


def days_to_full(rows: Sequence[Mapping[str, Any]], key: str = "full_rate") -> dict[str, Any]:
    """満杯率の系列 → 1.0 に届いた最初の日(届かなければ最後の 3 日の平均の増えから外挿した日数=推測)。"""
    xs = [(int(r["day"]), float(r[key])) for r in rows if r.get(key) is not None]
    if not xs:
        return {"reached_day": None, "extrapolated_days": None}
    hit = next((d for d, v in xs if v >= 1.0), None)
    if hit is not None:
        return {"reached_day": hit, "extrapolated_days": None}
    tail = xs[-4:]
    slope = (tail[-1][1] - tail[0][1]) / max(1, tail[-1][0] - tail[0][0])
    ext = None if slope <= 0 else round(tail[-1][0] + (1.0 - tail[-1][1]) / slope, 1)
    return {"reached_day": None, "extrapolated_days": ext, "slope_per_day": round(slope, 5),
            "last": tail[-1][1]}


def cmd_table(args: argparse.Namespace) -> int:
    out = {}
    for f in args.runs:
        doc = json.loads(Path(f).read_text(encoding="utf-8"))
        rows = day_rows(doc)
        out[doc["config"]] = {"final": doc["final"], "calls": doc["calls"], "arms": doc["arms"], "rows": rows,
                              "days_to_full": days_to_full(rows), "days_to_full_live": days_to_full(rows, "full_live_rate"),
                              "memory_store": doc.get("memory_store"), "weather": doc.get("weather"),
                              "wall_s_nondeterministic": doc.get("wall_s_nondeterministic")}
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--config", choices=list(CONFIGS), required=True)
    r.add_argument("--days", type=int, default=5)
    r.add_argument("--agents", type=int, default=5_000)
    r.add_argument("--seed", type=int, default=1)
    r.add_argument("--world", default="data/world/v2")
    r.add_argument("--scratch", required=True)
    r.add_argument("--out", required=True)
    r.add_argument("--no-gauge", action="store_true")
    r.add_argument("--allow-rest-days", action="store_true", help="A1-3 の規則の違反を記録に写して回す(付録・test_only)")
    s = sub.add_parser("side")
    s.add_argument("--configs", default="default,a,b,c,d")
    s.add_argument("--days", type=int, default=5)
    s.add_argument("--agents", type=int, default=5_000)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--world", default="data/world/v2")
    s.add_argument("--scratch", required=True)
    s.add_argument("--out-dir", required=True)
    s.add_argument("--jobs", type=int, default=2)
    s.add_argument("--allow-rest-days", action="store_true")
    rs = sub.add_parser("resume")
    rs.add_argument("--config", choices=list(CONFIGS), required=True)
    rs.add_argument("--agents", type=int, default=5_000)
    rs.add_argument("--seed", type=int, default=1)
    rs.add_argument("--world", default="data/world/v2")
    rs.add_argument("--scratch", required=True)
    rs.add_argument("--out", required=True)
    w = sub.add_parser("w9")
    w.add_argument("--a", required=True)
    w.add_argument("--b", required=True)
    w.add_argument("--out", required=True)
    t = sub.add_parser("table")
    t.add_argument("--runs", nargs="+", required=True)
    t.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    return {"run": cmd_run, "side": cmd_side, "resume": cmd_resume, "w9": cmd_w9, "table": cmd_table}[a.cmd](a)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    raise SystemExit(main())
