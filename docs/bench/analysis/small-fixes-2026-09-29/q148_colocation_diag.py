"""第 6 批の診断(第309 Q148 の値の読み方・計器は変えない): 瞬間の群れ歩きの組・群が「同じ点に重なった体」でできているかを数える。

``GroupNormMeter`` の ``_components`` を外から包んで、条件(2 m 内 ∧ 同方向 ∧ 両方が歩く)を満たした組の距離と、
群の成員の座標(1 cm に丸め)の重なりを数える。エンジン・計器の本体は触らない(final は計器 on のランと同じ)。

    python docs/bench/analysis/small-fixes-2026-09-29/q148_colocation_diag.py \
        --out docs/bench/analysis/small-fixes-2026-09-29/q148_colocation.json      # node: 5,000 体 1 日 + 39 万体の最初の 60 tick / edge: 5,000 体 1 日
"""
import json
import numpy as np
from shibuya.engine import norm_meter as nm
from shibuya import cli

st = {"pairs_ok": 0, "pairs_ok_zero_dist": 0, "pairs_ok_lt_0_5m": 0, "big": [], "grp_members": 0, "grp_members_in_stack": 0}
_cur = {}
_orig_init = nm.GroupNormMeter.__init__
def _init(self, *a, **k):
    _orig_init(self, *a, **k)
    _cur["m"] = self
nm.GroupNormMeter.__init__ = _init
_orig_comp = nm.GroupNormMeter._components
def _comp(a, b):
    members, lab = _orig_comp(a, b)
    xy = np.asarray(_cur["m"].agents.registry.xy, dtype=np.float64)
    d = np.sqrt(((xy[a] - xy[b]) ** 2).sum(axis=1))
    if a.size and _cur.get("inst"):
        st["pairs_ok"] += int(a.size)
        st["pairs_ok_zero_dist"] += int((d < 1e-6).sum())
        st["pairs_ok_lt_0_5m"] += int((d < 0.5).sum())
        # members の位置の重なり: 同じ座標(1 cm 丸め)に 2 体以上いる体の割合
        q = np.round(xy[members] * 100).astype(np.int64)
        key = q[:, 0] * (1 << 32) + q[:, 1]
        _u, inv, cnt = np.unique(key, return_inverse=True, return_counts=True)
        st["grp_members"] += int(members.size)
        st["grp_members_in_stack"] += int((cnt[inv] >= 2).sum())
        uu, sz = np.unique(lab, return_counts=True)
        big = int(sz.max())
        if big >= 20:
            sel = members[lab == uu[int(np.argmax(sz))]]
            qq = np.round(xy[sel] * 100).astype(np.int64)
            ndist = len({(int(x), int(y)) for x, y in qq})
            st["big"].append([big, ndist])
    return members, lab
nm.GroupNormMeter._components = staticmethod(_comp)
_orig_inst = nm.GroupNormMeter._observe_instant
def _inst(self, tick):
    _cur["inst"] = True
    try:
        return _orig_inst(self, tick)
    finally:
        _cur["inst"] = False
nm.GroupNormMeter._observe_instant = _inst

def _one(n: int, ticks: int, geometry: str) -> dict:
    for k in ("pairs_ok", "pairs_ok_zero_dist", "pairs_ok_lt_0_5m", "grp_members", "grp_members_in_stack"):
        st[k] = 0
    st["big"] = []
    res = cli.run(n_agents=n, seed=1, world_dir="data/world/v2", ticks=ticks, checkpoint_every=ticks, vocab_version="v3",
                  geometry=geometry)
    gn = res.run_manifest_fields()["group_norms"]
    g = gn["instant_group_walk"]
    big = st["big"]
    s = {k: st[k] for k in ("pairs_ok", "pairs_ok_zero_dist", "pairs_ok_lt_0_5m", "grp_members", "grp_members_in_stack")}
    return {"n_agents": n, "ticks": ticks, "geometry": geometry, "final_hash": res.final_hash, "grouped_share": g["grouped_share"], "walker_minutes": g["walker_minutes"],
            "cowalk_share_5min": gn["cowalk"]["cowalk_share_of_moving_minutes"],
            "cowalk_episodes_5min": gn["cowalk"]["episodes_5min"], **s,
            "share_pairs_zero_dist": round(s["pairs_ok_zero_dist"] / max(1, s["pairs_ok"]), 6),
            "share_members_stacked_same_point": round(s["grp_members_in_stack"] / max(1, s["grp_members"]), 6),
            "groups_ge20_count": len(big),
            "groups_ge20_top5_size_and_distinct_points": sorted(big, reverse=True)[:5]}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    rows = []
    for n, ticks, geometry in ((5_000, 1_440, "node"), (390_067, 60, "node"), (5_000, 1_440, "edge")):
        rows.append(_one(n, ticks, geometry))
        print(json.dumps(rows[-1], ensure_ascii=False), flush=True)
    doc = {"schema": "shibuya.bench/small-fixes/q148-colocation/1",
           "note": "mock v3・seed 1・geometry=node(既定)と edge(C9 edge=辺の上の位置)。pairs_ok=瞬間の群れ歩きの条件を満たした組(tick ごとの延べ)。"
                   "zero_dist=座標が 1e-6 m 未満で一致。stacked=群の成員のうち同じ座標(1 cm)に 2 体以上いる体。"
                   "39 万体は初期化+最初の 60 tick だけ(深夜)。",
           "rows": rows}
    open(args.out, "w", encoding="utf-8", newline="\n").write(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
