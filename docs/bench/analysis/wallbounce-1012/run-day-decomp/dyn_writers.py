"""run_day の tick ループの区間ごとに「実際に値が変わった状態」を測る(HEAD 0389689・コードは変えない)。

sys.monitoring(3.12)の LINE 事象を run_day の code だけに張り、区間の先頭の行(ループ本体の
最上位の文)に来るたびに状態の digest を取り、直前の区間に差を帰属させる。

状態 = SoA の全列(agents・cells・pois・知覚)+ 状態台帳の外の状態の全行の items(軸 1・軸 2 を問わない)。
窓の tick だけ測る(測らない tick は素通し)。測るだけで状態・乱数・テープに触れない(ハッシュを読むだけ)。

使い方: python dyn_writers.py <構成名> <体数> <日数> <出力 json>
"""
from __future__ import annotations

import json
import sys
import time
from collections import defaultdict
from pathlib import Path

import blake3
import numpy as np

import shibuya.engine.run as RUN
from shibuya import cli
from shibuya.engine import state_hashes as SH
from shibuya.engine import state_ledger as SL

CONFIGS = {
    "v3_default": {"vocab_version": "v3", "activity": True},
    "v3_mem_rel_store": {"vocab_version": "v3", "memory": "on", "relations": "on", "store_memory": "on",
                         "rel_copresent": "on"},
    "v3_classical_mem_rel": {"vocab_version": "v3", "memory": "on", "relations": "on",
                             "policy": "classical", "chooser": "classical"},
    "v1_edge": {"vocab_version": "v1", "geometry": "edge"},
    "v2_edge_attention": {"vocab_version": "v2", "geometry": "edge"},
    "golden_null_arm": {"plan_executor": False, "report_precondition": False},
}
BOUNDS = [  # (系, 先頭の行)= ループ本体の最上位の文のうち系の最初のもの(HEAD 0389689)。〔改訂(第330・検収 K5 (a))〕区間でなく草案 §2-2 の系の境目で切る
    ("day_head", 3632), ("body", 3636), ("world", 3655), ("presence", 3659), ("perceive_prepare", 3675),
    ("llm_receive_A", 3694), ("apply_responses", 3697), ("detect", 3814), ("plan_boundary", 3842),
    ("home_meal", 3889), ("wake_sources", 3896), ("llm_receive_B", 3916), ("wake_filter", 3920),
    ("relations_wake", 3955), ("wake_assemble", 3973), ("arbiter", 4007), ("decide", 4028),
    ("phase_a", 4156), ("phase_b", 4185), ("phase_c", 4192), ("conversation", 4255),
    ("activity_intent", 4386), ("memory", 4395), ("familiarity", 4421), ("energy_after", 4426),
    ("observe", 4429), ("checkpoint", 4478), ("day_close", 4528),
    ("drain", 4534), ("close_final", 4582), ("report", 4624), ("END", 4979),
]
RUN_END = {"drain", "close_final", "report", "END"}
#: 〔改訂(第330・検収 K5 (c))〕試験のときだけ指紋に入れる診断の積算(RunStats に当たる run_day の局所・result の積算の欄)。
STATS_LOCALS = ("layer_counts", "sleep_counts", "awake_sum", "awake_ticks", "calls_by_cond", "per_action_total",
                "leave_counts", "talk_stats", "n_undefined_total", "n_fleet_reinjected", "n_fleet_resent",
                "n_outside_calls", "geometry_hops", "geometry_jammed", "leave_closed", "peak_pending",
                "peak_intents", "peak_backlog", "prev_sessions", "prev_tape_misses", "intero_cross")
RESULT_FIELDS = ("llm_calls", "calls_by_hour", "fares_paid", "n_boarded", "n_alighted", "n_queued",
                 "n_board_waiting", "n_board_timeout", "meals", "move_bad_target", "move_unreachable", "meal_yen",
                 "n_approach", "n_approach_done", "n_target_gone", "n_focus", "n_focus_lost", "n_talk_by_distance",
                 "n_report_ok", "n_report_no_event", "n_served_from_queue", "n_queue_closed")
LINE2SEG = {ln: s for s, ln in BOUNDS}

cfg_name, n_agents, sim_days, out_path = sys.argv[1], int(sys.argv[2]), int(sys.argv[3]), Path(sys.argv[4])
TPD = 1440
WIN = set()
for d in range(sim_days):
    for a, b in ((0, 3), (420, 440), (720, 740), (1080, 1100), (1437, 1440)):
        WIN |= {d * TPD + t for t in range(a, b)}

code = RUN.run_day.__code__
TOOL = sys.monitoring.PROFILER_ID
state = {"idx": -1, "tick": -1, "last": None, "n_snap": 0, "snap_s": 0.0}
seg_changes: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))
seg_visits: dict[str, int] = defaultdict(int)
ext_rows = [(r.key, p, r.behavior, r.restore) for r in SL.external_rows() for p in r.items]
row_meta = {f"{k}:{p}": (b, rs) for k, p, b, rs in ext_rows}
soa_meta = {}
for r in SL.LEDGER:
    if r.is_soa:
        soa_meta[f"{r.place}.{r.name}"] = (r.behavior, r.restore)


def _h(arr) -> str:
    a = np.ascontiguousarray(np.asarray(arr))
    return blake3.blake3(a.view(np.uint8).reshape(-1) if a.size else b"").hexdigest()[:24] + str(a.shape)


def _plain(v):
    if isinstance(v, np.ndarray):
        return ("nd", v.shape, v.tobytes())
    if isinstance(v, dict):
        return sorted((repr(k), _plain(x)) for k, x in v.items())
    if isinstance(v, (list, tuple)):
        return [_plain(x) for x in v]
    return v


def snapshot(frame) -> dict[str, str]:
    t0 = time.perf_counter()
    loc = frame.f_locals
    agents, world = loc["agents"], loc["world"]
    pst = loc["_pst_now"]()
    owners = loc["_hash_owners"]()
    out: dict[str, str] = {}
    for place, reg in (("agents", agents.registry), ("cells", world.cells), ("pois", world.pois),
                       ("perception", None if pst is None else pst.registry)):
        if reg is None:
            continue
        for name, arr in reg.arrays.items():
            out[f"{place}.{name}"] = _h(arr)
    for key, path, _b, _r in ext_rows:
        try:
            d, _n = SH.item_digest(owners, key, path)
            out[f"{key}:{path}"] = d.hex()[:24]
        except Exception as e:  # noqa: BLE001
            out[f"{key}:{path}"] = f"ERR:{type(e).__name__}"
    for nm in STATS_LOCALS:
        if nm in loc:
            out[f"stats.{nm}"] = blake3.blake3(repr(_plain(loc[nm])).encode()).hexdigest()[:24]
    dr = loc.get("diag_rows")
    if dr is not None:
        out["stats.diag_rows"] = blake3.blake3(repr((len(dr), dr[-1] if dr else None)).encode()).hexdigest()[:24]
    res = loc.get("result")
    if res is not None:
        out["stats.result"] = blake3.blake3(repr([_plain(getattr(res, f, None)) for f in RESULT_FIELDS]).encode()).hexdigest()[:24]
    state["n_snap"] += 1
    state["snap_s"] += time.perf_counter() - t0
    return out


def on_line(c, line):
    if c is not code:
        return sys.monitoring.DISABLE
    seg = LINE2SEG.get(line)
    if seg is None:
        return sys.monitoring.DISABLE
    frame = sys._getframe(1)
    if frame.f_code is not code:
        raise RuntimeError("frame mismatch")
    state["idx"] += 1
    if seg == "day_head":
        state["tick"] += 1
    tick = state["tick"]
    in_win = (tick in WIN) or seg in RUN_END
    if not in_win:
        return None
    snap = snapshot(frame)
    last = state["last"]
    if last is not None and last[0] == state["idx"] - 1:
        prev_seg = last[1]
        seg_visits[prev_seg] += 1
        for k, v in snap.items():
            if last[2].get(k) != v:
                seg_changes[prev_seg][k] += 1
    state["last"] = (state["idx"], seg, snap)
    return None


sys.monitoring.use_tool_id(TOOL, "decomp-probe")
sys.monitoring.register_callback(TOOL, sys.monitoring.events.LINE, on_line)
sys.monitoring.set_local_events(TOOL, code, sys.monitoring.events.LINE)
t0 = time.perf_counter()
kw = dict(CONFIGS[cfg_name])
res = cli.run(n_agents=n_agents, seed=1, sim_days=sim_days, ticks=TPD, **kw)
wall = time.perf_counter() - t0
sys.monitoring.set_local_events(TOOL, code, 0)
sys.monitoring.free_tool_id(TOOL)

order = [s for s, _ in BOUNDS]
segs = {}
for s in order:
    if s not in seg_visits:
        continue
    ch = seg_changes.get(s, {})
    segs[s] = {
        "visits": seg_visits[s],
        "soa": {k: v for k, v in sorted(ch.items()) if "." in k and ":" not in k and not k.startswith("stats.")},
        "stats": {k: v for k, v in sorted(ch.items()) if k.startswith("stats.")},
        "external": {k: v for k, v in sorted(ch.items()) if ":" in k},
    }
out = {
    "config": cfg_name, "kw": kw, "n_agents": n_agents, "sim_days": sim_days, "seed": 1,
    "head": "0389689", "final": res.final_hash[:16], "calls": int(res.llm_calls),
    "window_ticks": len(WIN), "n_snapshots": state["n_snap"], "snapshot_seconds": round(state["snap_s"], 1),
    "wall_seconds": round(wall, 1),
    "n_soa_keys": sum(1 for k in soa_meta), "n_ext_items": len(ext_rows),
    "segments": segs,
    "soa_meta": {k: list(v) for k, v in soa_meta.items()},
    "ext_meta": {k: list(v) for k, v in row_meta.items()},
}
out_path.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
print(json.dumps({k: out[k] for k in ("config", "final", "calls", "n_snapshots", "snapshot_seconds", "wall_seconds")},
                 ensure_ascii=False))
