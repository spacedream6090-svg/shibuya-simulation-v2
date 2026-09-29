"""Q111(関係辺の表の容量 50+(c))の解析計算(ランは回さない・エンジンの関数で初期網を作り式で数える)。

サブコマンド:
  check   — 検算(手計算の 3 例と ``relations._activation``/``RelationLayer.activation``/``lifetime_days`` の一致・
            容量 50 の表で「新しい辺を 35 本積むまで押し出しが起きない」ことを実際の書き手で確かめる)
  analyze — 全母集団(W16+W17)と 5,000 体の抽出 2 通りで、初期辺の分布・寿命・「満杯の体のうち τ 未満の辺を
            1 本以上持つ割合」(1・7・14・30 日・仮定 A/B)・メモリの検算

仮定(本書 README の §2 と同じ):
  A = 初期辺に相互作用が一度も足されない(n 不変・A は L とともに下がるだけ)。
  B = 平日(ラン 0 日目=月曜=``engine.run`` の既定 day_index 0)ごとに、全初期辺(世帯/職場/学校)へ 1 本ずつ
      足される(n+1・first は不変=書き手 ``copresent_step`` と同じ)。足す時刻は各平日の 12:00(宣言)。
  「t 日目」の時点=ラン開始から t×1440 分(t 日目の終わり=24:00)。

再現:
  python docs/bench/analysis/q111-capacity-2026-09-30/q111_measure.py check   --out docs/bench/analysis/q111-capacity-2026-09-30/q111_check.json
  python docs/bench/analysis/q111-capacity-2026-09-30/q111_measure.py analyze --out docs/bench/analysis/q111-capacity-2026-09-30/q111_analysis.json
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path
from typing import Any

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[3]
sys.path.insert(0, str(HERE.parent / "c10-relations-2026-09-28"))  # 層化抽出の口(rel8b_measure.stratified_sample)

DAYS = (1, 7, 14, 30)
ADD_MINUTE = 720          # 仮定 B: 平日の 12:00 に足す(宣言)
WEEKDAYS = (0, 1, 2, 3, 4)  # day_index 0=月曜(engine.run の既定)


def _q(x: np.ndarray, qs=(0, 10, 50, 90, 100)) -> dict[str, float]:
    x = np.asarray(x, dtype=np.float64)
    if x.size == 0:
        return {}
    return {f"p{q}": round(float(np.percentile(x, q)), 3) for q in qs}


# ---------------------------------------------------------------------------- 式
def life_minutes_from_birth(n: np.ndarray, tau: float, d: float) -> np.ndarray:
    """A=ln(n/(1−d))−d·ln(L+1) ≥ τ の上端 L*[分](first から数えた経過)。"""
    with np.errstate(over="ignore"):
        return np.exp((np.log(np.asarray(n, dtype=np.float64) / (1.0 - d)) - tau) / d) - 1.0


def additions_before(t_min: float) -> int:
    """仮定 B: 時刻 t[分](ラン開始から)より前に足された本数(平日 12:00 ごとに 1)。"""
    c = 0
    day = 0
    while day * 1440 + ADD_MINUTE < t_min:  # 日の数ぶん(≤ 31)
        if day % 7 in WEEKDAYS:
            c += 1
        day += 1
    return c


def addition_times(t_end: float) -> list[float]:
    out = []
    day = 0
    while day * 1440 + ADD_MINUTE < t_end:
        if day % 7 in WEEKDAYS:
            out.append(float(day * 1440 + ADD_MINUTE))
        day += 1
    return out


# ---------------------------------------------------------------------------- check
def cmd_check(args: argparse.Namespace) -> int:
    from shibuya.agents.state import AgentState
    from shibuya.engine import relations as RL

    tau, d = RL.REL_TAU, RL.REL_D
    out: dict[str, Any] = {"schema": "shibuya.bench/q111/check/1", "tau": tau, "d": d,
                           "units": {"L": "分(= (tick − rel_first) × minutes_per_tick・既定 1 分/tick)",
                                     "n": "共在のあった日数(初期辺=日数/週 × 在職週)・ラン中=会話 1 セッション 1・同席 1 日 1",
                                     "first": "tick(初期辺は −在職週 × 7 × 1440)"}}
    # 手計算の 3 例(math で独立に書いた値)
    cases = [
        # (名前, n, first[分], 手計算の A(0), 手計算の寿命[分]=first からの L* − (−first))
        ("会話 1 回の新しい辺 n=1・first=0", 1, 0),
        ("職場の初期辺 在職 1 週 n=5・first=−10080", 5, -10080),
        ("職場の初期辺 在職 13 週 n=65・first=−131040(8a の最下段)", 65, -131040),
    ]
    rows = []
    for name, n, first in cases:
        # 手計算(math・独立)
        A0_hand = math.log(n / (1 - d)) - d * math.log(-first + 1)
        Lstar_hand = math.exp((math.log(n / (1 - d)) - tau) / d) - 1
        life_hand = Lstar_hand + first  # ラン開始(tick 0)から τ を下回るまでの分
        # 実装: 関数
        A0_impl = float(RL._activation(np.array([n]), np.array([first]), 0, 1.0, d)[0])
        A_at = float(RL._activation(np.array([n]), np.array([first]), int(math.floor(life_hand)), 1.0, d)[0])
        A_after = float(RL._activation(np.array([n]), np.array([first]), int(math.floor(life_hand)) + 1, 1.0, d)[0])
        # 実装: RelationLayer(実の表に書いて activation と lifetime_days)
        ag = AgentState(2, memory_columns=True, memory_n=1, relation_columns=True, rel_k=15)
        lay = RL.RelationLayer(2, 15, minutes_per_tick=1.0)
        init = RL.InitialEdges(np.array([0]), np.array([1]), np.array([2]), np.array([n]), np.array([first]),
                               np.array([-1]), np.array([0]), {})
        lay.seed_initial(ag, init)
        A0_layer = float(lay.activation(ag, np.array([0]), 0)[0, 0])
        lt = lay.lifetime_days(ag, 0)
        rem_layer_days = lt.get("initial", {}).get("p50")
        rows.append({
            "case": name, "n": n, "first_min": first,
            "A0_hand": round(A0_hand, 6), "A0_impl": round(A0_impl, 6), "A0_layer": round(A0_layer, 6),
            "life_from_start_min_hand": round(life_hand, 2), "life_from_start_hours_hand": round(life_hand / 60, 3),
            "life_from_start_days_hand": round(life_hand / 1440, 3),
            "lifetime_days_layer_p50": rem_layer_days,
            "A_at_floor(life)": round(A_at, 6), "A_at_floor(life)+1": round(A_after, 6),
            "crosses_tau_there": bool(A_at >= tau > A_after),
            "match": bool(abs(A0_hand - A0_impl) < 1e-9 and abs(A0_hand - A0_layer) < 1e-9
                          and abs(life_hand / 1440 - float(rem_layer_days)) < 1e-3),
        })
    out["hand_cases"] = rows

    # 容量 50: 初期辺 15 本の体に新しい相手を 1 本ずつ書く → 35 本目までは押し出し 0・36 本目で押し出し
    k = 50
    n_ag = 60
    ag = AgentState(n_ag, memory_columns=True, memory_n=1, relation_columns=True, rel_k=k)
    lay = RL.RelationLayer(n_ag, k, minutes_per_tick=1.0)
    init = RL.InitialEdges(np.zeros(15, dtype=np.int64), np.arange(1, 16), np.full(15, 2), np.full(15, 5),
                           np.full(15, -10080), np.full(15, -1), np.zeros(15), {})
    lay.seed_initial(ag, init)
    TALK, OK = 7, 0
    from shibuya.agents.state import ResultCode
    OK = int(ResultCode.OK)
    trace = []
    used35 = None
    for j in range(36):  # 新しい相手 36 人(16..51)
        if j == 35:
            used35 = int(np.count_nonzero(np.asarray(ag.registry.rel_partner)[0] != -1))
        before = lay.stats["evictions"]
        lay.on_episodes(ag, 10 + j, np.array([0]), np.array([TALK]), np.array([16 + j]), np.array([OK]))
        trace.append({"new_partner_no": j + 1, "evicted": int(lay.stats["evictions"] - before),
                      "newcomer_dropped_total": int(lay.stats["newcomer_dropped"])})
    first_evict = next((t["new_partner_no"] for t in trace if t["evicted"]), None)
    out["capacity50_writer"] = {
        "setup": "体 0 に初期辺 15 本(n=5・在職 1 週)・容量 50・会話(OK)で新しい相手を 1 tick に 1 人",
        "evictions_after_35": int(sum(t["evicted"] for t in trace[:35])),
        "first_new_partner_that_evicts": first_evict,
        "used_slots_after_35": used35, "note": "36 人目で初めて押し出し(いまの規則=A 最小の辺)",
    }
    assert out["capacity50_writer"]["evictions_after_35"] == 0 and first_evict == 36
    out["all_hand_cases_match"] = all(r["match"] and r["crosses_tau_there"] for r in rows)
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(out, ensure_ascii=False, indent=1))
    return 0 if out["all_hand_cases_match"] else 1


# ---------------------------------------------------------------------------- analyze
def _population(world: str, n: int | None, seed: int, sample: str) -> Any:
    from shibuya.agents.population import load_population, sample_population

    full = load_population(world, n=None, seed=seed)
    if n is None:
        return full
    if sample == "stratified":
        from rel8b_measure import stratified_sample  # type: ignore[import-not-found]
        return stratified_sample(full, n, seed)
    return sample_population(full, n, seed)


def _one(label: str, pop: Any, wk: Any, engine_check: bool) -> dict[str, Any]:
    from shibuya.agents.state import AgentKind, AgentState
    from shibuya.engine import relations as RL

    tau, d, K = RL.REL_TAU, RL.REL_D, RL.REL_K
    names = {int(k): k.name for k in AgentKind}
    kind_names = RL.REL_KIND_NAMES
    w = wk.restrict_to(pop.source_agent_id)
    t0 = time.perf_counter()
    init = RL.initial_edges(pop, w, pop.n)           # エンジンと同じ既定(k 15・τ −2.346・13 週・密度 1)
    secs = time.perf_counter() - t0
    u = init.u.astype(np.int64)
    n0 = init.n.astype(np.float64)
    T = -init.first.astype(np.float64)               # 分(=tick・1 分/tick)
    ek = init.kind.astype(np.int64)
    m = int(pop.n)
    deg = np.bincount(u, minlength=m)
    full = deg >= K
    akind = np.asarray(pop.kind, dtype=np.int64)
    res: dict[str, Any] = {"agents": m, "edges": int(u.size), "init_seconds_nondeterministic": round(secs, 1),
                           "audit": {k: v for k, v in init.audit.items() if k in (
                               "edges_before_tau", "dropped_by_tau", "capped_out", "w17_single_day", "tenure_weeks")}}
    # 1. 本数の分布
    res["degree_hist"] = {str(i): int(c) for i, c in enumerate(np.bincount(deg, minlength=K + 1))}
    res["full_agents"] = int(full.sum())
    res["full_share"] = round(float(full.mean()), 4)
    by_ak = {}
    for k in np.unique(akind).tolist():
        s = akind == k
        by_ak[names.get(int(k), str(k))] = {"agents": int(s.sum()), "full": int((full & s).sum()),
                                            "full_share": round(float(full[s].mean()), 4),
                                            "mean_edges": round(float(deg[s].mean()), 3)}
    res["full_by_agent_kind"] = by_ak
    fe = full[u]
    res["edges_of_full_agents_by_edge_kind"] = {kind_names[int(k)]: int(c) for k, c in
                                                zip(*np.unique(ek[fe], return_counts=True))}
    # 満杯の体の辺の種別の組み合わせ(世帯を含むか)
    has_hh = np.zeros(m, dtype=bool)
    has_hh[u[ek == 1]] = True
    res["full_agents_with_household_edge"] = int((full & has_hh).sum())

    # 2. 寿命(仮定 A=相互作用なし)
    life_A = (life_minutes_from_birth(n0, tau, d) - T) / 1440.0   # ラン開始から τ を下回るまで[日]
    res["lifetime_days_A"] = {"all": _q(life_A) | {"n": int(u.size)}}
    for k in np.unique(ek).tolist():
        s = ek == k
        res["lifetime_days_A"][kind_names[int(k)]] = _q(life_A[s]) | {"n": int(s.sum())}
    res["lifetime_days_A"]["edges_of_full_agents"] = _q(life_A[fe]) | {"n": int(fe.sum())}
    res["n_quantiles"] = _q(n0)
    res["tenure_weeks_quantiles"] = _q(T / 10080.0)
    res["min_A_at_start"] = round(float(RL._activation(n0, -T, 0, 1.0, d).min()), 4)

    # 3. 満杯の体のうち τ 未満の辺を 1 本以上持つ割合
    #   仮定 A: 時刻 t の A(n0)=_activation(エンジンの関数)と、寿命の式(life_A < t)の 2 通りで数えて一致を確かめる
    #   仮定 B: 平日 12:00 に +1(n0 + 足された本数)。スナップショット(t 日目の終わり)と「t までに一度でも τ 未満」
    tab: dict[str, Any] = {}
    add_all = addition_times(max(DAYS) * 1440.0 + 1)
    for D in DAYS:
        t = D * 1440
        A_A = RL._activation(n0, -T, t, 1.0, d)
        below_A = A_A < tau
        below_A_formula = life_A * 1440.0 < t
        agree = int(np.count_nonzero(below_A != below_A_formula))
        nb = additions_before(t)
        A_B = RL._activation(n0 + nb, -T, t, 1.0, d)
        below_B = A_B < tau
        # 一度でも(B): 各追加の直前と t の A の最小(A は追加の間で単調に下がる)
        ever_B = below_B.copy()
        for j, ta in enumerate([x for x in add_all if x < t]):   # 追加の回数ぶん(≤ 22)
            ever_B |= RL._activation(n0 + j, -T, int(ta) - 0, 1.0, d) < tau  # 直前=j 本足した状態で時刻 ta
        row = {}
        for name, below in (("A", below_A), ("B_snapshot", below_B), ("B_ever", ever_B)):
            cnt = np.bincount(u[below], minlength=m)
            share_full = float((cnt[full] >= 1).mean()) if full.any() else float("nan")
            row[name] = {
                "full_agents_with_ge1_below": int((cnt[full] >= 1).sum()),
                "share_of_full_agents": round(share_full, 4),
                "share_of_all_agents_with_edges": round(float((cnt[deg > 0] >= 1).mean()), 4) if (deg > 0).any() else None,
                "edges_below_share_all": round(float(below.mean()), 4),
                "edges_below_share_full_agents": round(float(below[fe].mean()), 4) if fe.any() else None,
                "below_edges_per_full_agent_mean": round(float(cnt[full].mean()), 3) if full.any() else None,
                "by_agent_kind_share_of_full": {
                    names.get(int(k), str(k)): round(float((cnt[full & (akind == k)] >= 1).mean()), 4)
                    for k in np.unique(akind[full]).tolist()},
            }
            # 独立を仮定した見積り(chat 側の式の推定)=1−(1−p)^15(p=満杯の体の辺の τ 未満の割合)
            p = float(below[fe].mean()) if fe.any() else float("nan")
            row[name]["independent_estimate_1-(1-p)^15"] = round(1 - (1 - p) ** K, 4)
        row["A_formula_vs_activation_disagree_edges"] = agree
        row["B_additions_before_t"] = nb
        tab[str(D)] = row
    res["share_full_with_below_tau"] = tab
    # 仮定 B の「一度でも」は 0 日目の最初の追加より前の落ち込みだけで決まる(本計算で day 1〜30 が同じ)。
    # 足す時刻の宣言(12:00)への感度: 0 日目の hh:mm までに τ を下回る辺を持つ満杯の体の割合(=その時刻の仮定 A)
    sens = {}
    for hm in (0, 6 * 60, 9 * 60, 12 * 60, 18 * 60, 24 * 60):
        cnt = np.bincount(u[life_A * 1440.0 < hm], minlength=m)
        sens[f"{hm // 60:02d}:00"] = round(float((cnt[full] >= 1).mean()), 4) if full.any() else None
    res["B_ever_day0_dip_by_add_time"] = sens

    # 仮定 B の計器の検算: 無作為 300 辺(満杯の体の辺)を 1 分刻みで 30 日ぶん総当たり(n は分ごとに数え直す)
    rng = np.random.default_rng(0)
    idx = np.flatnonzero(fe)
    if idx.size:
        # 寿命の短い辺を多めに(τ を下回る例を含めるため): 半分は寿命 < 30 日の辺から
        short = idx[life_A[idx] < 30]
        pick = np.concatenate([rng.choice(idx, size=min(150, idx.size), replace=False),
                               rng.choice(short, size=min(150, short.size), replace=False) if short.size else idx[:0]])
        tmin = np.arange(0, max(DAYS) * 1440 + 1, dtype=np.int64)
        day = tmin // 1440
        is_add = ((tmin % 1440) == ADD_MINUTE) & np.isin(day % 7, WEEKDAYS)
        nadd = np.cumsum(is_add) - is_add           # 時刻 t より前(t ちょうどの追加は含まない)に足された本数
        mism = {"snapshot": 0, "ever": 0}
        for e in pick.tolist():  # 検算の辺の数ぶん(300)
            A = np.log((n0[e] + nadd) / (1 - d)) - d * np.log(tmin + T[e] + 1.0)  # 独立に書いた式
            for D in DAYS:  # 4
                t = D * 1440
                snap_bf = bool(A[t] < tau)
                ever_bf = bool((A[: t + 1] < tau).any())
                snap = bool(RL._activation(np.array([n0[e] + additions_before(t)]), np.array([-T[e]]), t, 1.0, d)[0] < tau)
                ever = snap or any(bool(RL._activation(np.array([n0[e] + j]), np.array([-T[e]]), int(ta), 1.0, d)[0] < tau)
                                   for j, ta in enumerate([x for x in add_all if x < t]))
                mism["snapshot"] += int(snap != snap_bf)
                mism["ever"] += int(ever != ever_bf)
        res["B_bruteforce_check"] = {"edges": int(pick.size), "mismatches": mism}

    # 4. 容量 50: 初期辺 ≤15 なので空き ≥35(満杯の体)
    res["capacity50_free_slots"] = {"full_agents_free": 50 - K, "min_free_any_agent": int(50 - deg.max())}

    # エンジンの表での検算(抽出だけ): 表に書いて RelationLayer.activation で同じ数になるか
    if engine_check:
        ag = AgentState(m, memory_columns=True, memory_n=1, relation_columns=True, rel_k=K)
        lay = RL.RelationLayer(m, K, minutes_per_tick=1.0)
        lay.seed_initial(ag, init)
        ids = np.arange(m, dtype=np.int64)
        chk = {}
        for D in DAYS:
            A = lay.activation(ag, ids, D * 1440)
            used = np.asarray(ag.registry.rel_partner) != -1
            cntb = ((A < tau) & used).sum(axis=1)
            fullx = used.sum(axis=1) >= K
            chk[str(D)] = {"full_agents": int(fullx.sum()),
                           "share_of_full_agents_A": round(float((cntb[fullx] >= 1).mean()), 4) if fullx.any() else None}
        res["engine_table_check_A"] = chk
    return res


def cmd_analyze(args: argparse.Namespace) -> int:
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL

    wk = load_weekly(args.world)
    doc: dict[str, Any] = {"schema": "shibuya.bench/q111/analysis/1", "tau": RL.REL_TAU, "d": RL.REL_D,
                           "k": RL.REL_K, "tenure_weeks": RL.REL_TENURE_WEEKS, "days": list(DAYS),
                           "assumption_B": {"add_minute_of_day": ADD_MINUTE, "weekdays_day_index_mod7": list(WEEKDAYS),
                                            "day0": "月曜(engine.run の既定 day_index 0)"},
                           "rows": {}}
    for label, n, sample, chk in (("full_population", None, "default", False),
                                  ("default_sample_5000", 5000, "default", True),
                                  ("stratified_sample_5000", 5000, "stratified", True)):
        pop = _population(args.world, n, 1, sample)
        doc["rows"][label] = _one(label, pop, wk, chk)
        r = doc["rows"][label]
        print(label, r["agents"], r["edges"], r["full_agents"],
              {D: (r["share_full_with_below_tau"][str(D)]["A"]["share_of_full_agents"],
                   r["share_full_with_below_tau"][str(D)]["B_snapshot"]["share_of_full_agents"]) for D in DAYS},
              flush=True)
    # 6. メモリ(体数は W16 の全母集団の実数)
    N = doc["rows"]["full_population"]["agents"]
    B = RL.REL_ROW_BYTES_ACTUAL
    doc["memory"] = {
        "agents_W16": N, "bytes_per_edge": B,
        "per_agent_k15": 15 * B, "per_agent_k50": 50 * B, "increment_per_agent": 35 * B,
        "total_k50_MB_1e6": round(N * 50 * B / 1e6, 1), "total_k15_MB_1e6": round(N * 15 * B / 1e6, 1),
        "increment_MB_1e6": round(N * 35 * B / 1e6, 1), "increment_MiB": round(N * 35 * B / 2 ** 20, 1),
        "total_k50_MiB": round(N * 50 * B / 2 ** 20, 1),
    }
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["memory"]))
    return 0


def cmd_tenure_bias(args: argparse.Namespace) -> int:
    """見つけた偏り(在職期間の hash と同点の順の hash が同じ)の診断と、偏りの無い在職期間での反実仮想(仮定 A)。

    エンジンは変えない: 初期網(u・v・種別・共在)はエンジンのまま、在職期間だけを塩を足した組の hash で引き直し、
    n=max(1, round(日数/週 × T′))・first=−round(T′ × 10080) を式で作る(日数/週=世帯 7・職場/学校 5=W17 が 1 日ぶん
    の実資産での ``initial_edges`` と同じ・密度 1)。τ は据え置き(−2.346)と、同じ網で再逆算した値の 2 通り。
    """
    from shibuya.agents.population import load_population
    from shibuya.agents.weekly import load_weekly
    from shibuya.engine import relations as RL

    tau0, d, K = RL.REL_TAU, RL.REL_D, RL.REL_K
    pop = load_population(args.world, n=None, seed=1)
    w = load_weekly(args.world).restrict_to(pop.source_agent_id)
    doc: dict[str, Any] = {"schema": "shibuya.bench/q111/tenure-bias/1"}
    src = np.asarray(pop.source_agent_id, dtype=np.int64)
    m = int(pop.n)
    # 診断: 向き(元 id の大小)ごとの T<2 週の割合(一様なら 1/12=0.083)
    init = RL.initial_edges(pop, w, m)
    T = -init.first.astype(np.float64) / 10080.0
    su, sv = src[init.u], src[init.v]
    diag = {}
    for k in (1, 2, 3):
        s = init.kind == k
        diag[RL.REL_KIND_NAMES[k]] = {
            name: {"edges": int((s & msk).sum()), "share_T_lt_2w": round(float((T[s & msk] < 2).mean()), 4),
                   "median_T_w": round(float(np.median(T[s & msk])), 3)}
            for name, msk in (("src_u<src_v", su < sv), ("src_u>src_v", su > sv)) if (s & msk).any()}
    doc["diagnosis_default"] = diag
    doc["uniform_expectation_share_T_lt_2w"] = round(1 / 12, 4)
    # 反実仮想: 網は τ なし(全部)で取り、在職期間を塩つきの hash で引き直す
    allx = RL.initial_edges(pop, w, m, tau=None)
    lo = np.minimum(src[allx.u], src[allx.v])
    hi = np.maximum(src[allx.u], src[allx.v])
    salt = np.int64(0x5DEECE66D)
    x = RL._pair_mix(lo ^ salt, hi + np.int64(0x2545F491))
    unit = (x >> np.uint64(11)).astype(np.float64) / float(1 << 53)
    Tn = 1.0 + (RL.REL_TENURE_WEEKS - 1.0) * unit
    perday = np.where(allx.kind == 1, 7.0, 5.0)
    n_cf = np.maximum(1, np.round(perday * Tn)).astype(np.float64)
    first_cf = -np.round(Tn * 10080.0)
    A0 = RL._activation(n_cf, first_cf, 0, 1.0, d)
    tau_re = float(RL.tau_from_edges(allx.u, A0, m)["tau"])
    doc["counterfactual"] = {"salted_T_share_lt_2w_by_kind": {
        RL.REL_KIND_NAMES[k]: round(float((Tn[allx.kind == k] < 2).mean()), 4) for k in (1, 2, 3)},
        "tau_rederived": round(tau_re, 4), "rows": {}}
    for label, tau in (("tau_declared", tau0), ("tau_rederived", tau_re)):
        live = A0 >= tau
        u = allx.u[live]
        deg = np.bincount(u, minlength=m)
        full = deg >= K
        life = (life_minutes_from_birth(n_cf[live], tau, d) + first_cf[live]) / 1440.0
        row = {"tau": round(tau, 4), "edges": int(live.sum()), "full_agents": int(full.sum()),
               "full_share": round(float(full.mean()), 4), "lifetime_days": _q(life), "share_of_full_agents": {}}
        for D in DAYS:
            below = life * 1440.0 < D * 1440
            cnt = np.bincount(u[below], minlength=m)
            row["share_of_full_agents"][str(D)] = round(float((cnt[full] >= 1).mean()), 4)
        doc["counterfactual"]["rows"][label] = row
        print(label, row["tau"], row["full_share"], row["share_of_full_agents"], flush=True)
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["diagnosis_default"], ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Q111 の解析計算")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name in ("check", "analyze", "tenure-bias"):
        sp = sub.add_parser(name)
        sp.add_argument("--world", default="data/world/v2")
        sp.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    return {"check": cmd_check, "analyze": cmd_analyze, "tenure-bias": cmd_tenure_bias}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
