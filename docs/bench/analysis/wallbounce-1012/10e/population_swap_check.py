"""10e E4 の住人の入れ替わり(5,000 体のうち 4,191 体)の属性の分布の比較(第330・発注 E)。

旧 = ``load_population(world, 5000, seed=1, rng_scheme="stateful")``
新 = ``load_population(world, 5000, seed=1, rng_scheme="counter")``(10e の既定)
全体 = W16 の母集団(``data/world/v2/w16_population.parquet`` の全行)

フロア = 同じ抽出(``sample_population``)を別の seed(既定 2..101 の 100 本)で、stateful と counter の両方で回した
ときの各区分の割合の分布(2.5〜97.5%)。旧は stateful のフロア、新は counter のフロアと照らす。

使い方(リポの根で):
    PYTHONPATH=src .venv/Scripts/python.exe docs/bench/analysis/wallbounce-1012/10e/population_swap_check.py \
        --world data/world/v2 --out docs/bench/analysis/wallbounce-1012/10e/population_swap_check.json

コード・資産は読むだけ(書くのは --out の json だけ)。scipy は使わない(カイ二乗の p は不完全ガンマ関数を自前で計算)。
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

from shibuya.agents.population import (
    AGE_EDGES,
    POPULATION_FILE,
    load_population,
    sample_population,
)
from shibuya.agents.state import AgentKind

PURPOSE_NAMES = ("勤務", "通学", "業務", "私事", "居住", "職務")  # build.pop.w16_population.PURPOSE_NAMES の写し
N_SAMPLE = 5000
SEED = 1


# ---------------------------------------------------------------- カイ二乗の上側確率(scipy なし)
def _gammq(a: float, x: float) -> float:
    """正則化上側不完全ガンマ Q(a, x)(Numerical Recipes の gser / gcf)。"""
    if x <= 0:
        return 1.0
    gln = math.lgamma(a)
    if x < a + 1.0:
        ap, s, d = a, 1.0 / a, 1.0 / a
        for _ in range(10_000):
            ap += 1.0
            d *= x / ap
            s += d
            if abs(d) < abs(s) * 1e-15:
                break
        return max(0.0, 1.0 - s * math.exp(-x + a * math.log(x) - gln))
    b = x + 1.0 - a
    c = 1.0 / 1e-300
    d = 1.0 / b
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = 1e-300 if abs(d) < 1e-300 else d
        c = b + an / c
        c = 1e-300 if abs(c) < 1e-300 else c
        d = 1.0 / d
        de = d * c
        h *= de
        if abs(de - 1.0) < 1e-15:
            break
    return math.exp(-x + a * math.log(x) - gln) * h


def chi2_sf(stat: float, dof: int) -> float:
    return _gammq(dof / 2.0, stat / 2.0) if dof > 0 else float("nan")


# ---------------------------------------------------------------- 属性の作り方
def build_attributes(world: Path, full) -> tuple[dict[str, np.ndarray], dict[str, dict[str, str]]]:
    """全体の行(agent_id 昇順)ごとの属性コード(文字列)と、コード→表示名。"""
    table = pq.read_table(world / POPULATION_FILE, columns=["agent_id", "chome_key", "industry_key"])
    aid = table.column("agent_id").to_numpy()
    if not np.array_equal(aid, full.source_agent_id):
        raise SystemExit("parquet の行順と load_population の行順が違う")
    chome = np.asarray(table.column("chome_key").to_pylist(), dtype=object)
    industry = np.asarray(table.column("industry_key").to_pylist(), dtype=object)

    ch = pq.read_table(world / "w16_chome.parquet", columns=["key_code", "s_name"]).to_pylist()
    chome_name = {r["key_code"]: r["s_name"] for r in ch}
    hh = pq.read_table(world / "w16_households.parquet", columns=["household_id", "size"]).to_pylist()
    hh_size = {int(r["household_id"]): int(r["size"]) for r in hh}

    kind_name = {str(int(k)): f"{int(k)}:{k.name}" for k in AgentKind}
    age_bin = full.age_bin()
    age_lbl = {}
    for i, lo in enumerate(AGE_EDGES.tolist()):
        hi = AGE_EDGES[i + 1] - 1 if i + 1 < AGE_EDGES.size else None
        age_lbl[f"{i:02d}"] = f"{lo}-{hi}" if hi is not None else f"{lo}+"

    org = full.org_id.astype(np.int64)
    org_sz = np.bincount(org[org >= 0]) if (org >= 0).any() else np.zeros(1, np.int64)
    size_of = np.where(org >= 0, org_sz[np.clip(org, 0, None)], 0)
    org_bucket = np.select(
        [org < 0, size_of < 10, size_of < 100, size_of < 1000],
        ["なし", "1-9", "10-99", "100-999"], default="1000+")

    hsize = np.array(
        ["なし" if h < 0 else str(hh_size.get(int(h), -1)) for h in full.household_id.tolist()], dtype=object)

    def cell_code(a: np.ndarray) -> np.ndarray:
        return np.where(a < 0, "域外/なし", a.astype(str)).astype(object)

    attrs = {
        "kind(種類)": full.kind.astype(int).astype(str).astype(object),
        "purpose(目的)": np.asarray([PURPOSE_NAMES[int(p)] for p in full.purpose.tolist()], dtype=object),
        "age_bin(年齢 5 歳階級)": np.char.zfill(age_bin.astype(str), 2).astype(object),
        "sex(性別)": full.sex.astype(int).astype(str).astype(object),
        "chome(住所の町丁目)": np.where(chome == "", "域外常住", chome).astype(object),
        "industry(勤め先の産業)": np.where(industry == "", "なし", industry).astype(object),
        "duty_role(職務の役割)": np.where(full.duty_role == "", "なし", full.duty_role).astype(object),
        "pool_layer(プール層)": full.pool_layer.astype(int).astype(str).astype(object),
        "synthetic(合成体)": full.synthetic.astype(str).astype(object),
        "is_foreign(外国籍)": full.is_foreign.astype(str).astype(object),
        "direction(方面の節点)": full.direction_node.astype(int).astype(str).astype(object),
        "household_size(世帯人数)": hsize,
        "org_size(勤め先の組織の体数)": org_bucket.astype(object),
        "has_home_cell(舞台内に住む)": (full.home_cell >= 0).astype(str).astype(object),
        "has_work_cell(舞台内に勤める)": (full.work_cell >= 0).astype(str).astype(object),
        "has_school_cell(舞台内に通う)": (full.school_cell >= 0).astype(str).astype(object),
        "home_cell(住むセル)": cell_code(full.home_cell),
        "work_cell(勤めるセル)": cell_code(full.work_cell),
        "school_cell(通うセル)": cell_code(full.school_cell),
    }
    labels = {
        "kind(種類)": kind_name,
        "age_bin(年齢 5 歳階級)": age_lbl,
        "sex(性別)": {"0": "0", "1": "1"},
        "chome(住所の町丁目)": {k: f"{k} {v}" for k, v in chome_name.items()},
    }
    return attrs, labels


# ---------------------------------------------------------------- 集計
def shares(codes: np.ndarray, cats: np.ndarray) -> np.ndarray:
    idx = np.searchsorted(cats, codes)
    return np.bincount(idx, minlength=cats.size) / codes.size


def counts(codes: np.ndarray, cats: np.ndarray) -> np.ndarray:
    return np.bincount(np.searchsorted(cats, codes), minlength=cats.size).astype(np.float64)


def cohen_h(p1: np.ndarray, p2: np.ndarray) -> np.ndarray:
    return 2 * np.arcsin(np.sqrt(p1)) - 2 * np.arcsin(np.sqrt(p2))


def design_expected_shares(full, codes: np.ndarray, cats: np.ndarray, rows_any: np.ndarray) -> np.ndarray:
    """二層抽出の期待の割合=定員先取り層の全員+層ごとの (定員/層の体数)×層の構成。

    層の定員は seed に依らない(最大剰余法)ので、どの seed の標本でも層ごとの体数は同じ。``rows_any`` はその
    体数を数えるための任意の標本の行。
    """
    reserved = full.reserved_mask
    rest = ~reserved
    strata_key = (full.kind.astype(np.int64) * (AGE_EDGES.size * 2) + full.age_bin() * 2
                  + np.clip(full.sex.astype(np.int64), 0, 1))
    strata_key = np.where(rest, strata_key, -1)
    exp = counts(codes[reserved], cats)
    in_sample = np.zeros(full.n, bool)
    in_sample[rows_any] = True
    for k in np.unique(strata_key[rest]):
        m = strata_key == k
        q = int((m & in_sample).sum())
        if q:
            exp += counts(codes[m], cats) * (q / int(m.sum()))
    return exp / exp.sum()


def chi2_vs_expected(obs_counts: np.ndarray, exp_share: np.ndarray, n: int) -> tuple[float, int]:
    """期待の体数が 5 未満の区分は 1 つに束ねてからのカイ二乗(適合度)。期待 0 の区分は観測も 0 のはず。"""
    exp = exp_share * n
    small = exp < 5
    o = list(obs_counts[~small])
    e = list(exp[~small])
    if small.any() and exp[small].sum() > 0:
        o.append(obs_counts[small].sum())
        e.append(exp[small].sum())
    o_a, e_a = np.asarray(o), np.asarray(e)
    pos = e_a > 0
    stat = float((((o_a - e_a) ** 2)[pos] / e_a[pos]).sum())
    return stat, int(pos.sum() - 1)


def tvd(p: np.ndarray, q: np.ndarray) -> float:
    return float(0.5 * np.abs(p - q).sum())


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--out", default="docs/bench/analysis/wallbounce-1012/10e/population_swap_check.json")
    ap.add_argument("--floor-seeds", default="2:102", help="フロアの seed の範囲 start:stop(stop は含まない)")
    args = ap.parse_args(argv)
    world = Path(args.world)
    lo, hi = (int(x) for x in args.floor_seeds.split(":"))
    floor_seeds = list(range(lo, hi))

    full = load_population(world)
    attrs, labels = build_attributes(world, full)
    row_of = {int(a): i for i, a in enumerate(full.source_agent_id.tolist())}

    def rows_of(p) -> np.ndarray:
        return np.fromiter((row_of[int(a)] for a in p.source_agent_id.tolist()), np.int64, count=p.n)

    old = load_population(world, N_SAMPLE, SEED, rng_scheme="stateful")
    new = load_population(world, N_SAMPLE, SEED, rng_scheme="counter")
    r_old, r_new = rows_of(old), rows_of(new)
    # load_population と sample_population(全体, …) が同じ標本か(フロアは後者で回す)
    assert np.array_equal(r_old, rows_of(sample_population(full, N_SAMPLE, SEED, rng_scheme="stateful")))
    assert np.array_equal(r_new, rows_of(sample_population(full, N_SAMPLE, SEED, rng_scheme="counter")))

    floor_rows = {sch: [rows_of(sample_population(full, N_SAMPLE, s, rng_scheme=sch)) for s in floor_seeds]
                  for sch in ("stateful", "counter")}

    reserved = full.reserved_mask
    n_res = int(reserved.sum())
    rest_rows = np.flatnonzero(~reserved)

    # ---- 共通の体数(809)と期待
    common = int(np.intersect1d(r_old, r_new).size)
    common_res = int(np.intersect1d(np.intersect1d(r_old, r_new), np.flatnonzero(reserved)).size)
    strata_key = (full.kind.astype(np.int64) * (AGE_EDGES.size * 2) + full.age_bin() * 2
                  + np.clip(full.sex.astype(np.int64), 0, 1))
    in_old = np.zeros(full.n, bool)
    in_old[r_old] = True
    exp_stat, var_stat = 0.0, 0.0
    strata_rows = []
    for k in np.unique(strata_key[~reserved]):
        m = (strata_key == k) & ~reserved
        Nk = int(m.sum())
        q = int((m & in_old).sum())
        if q == 0:
            continue
        exp_stat += q * q / Nk  # 超幾何の平均: q × (q / Nk)
        if Nk > 1:
            var_stat += q * (q / Nk) * (1 - q / Nk) * (Nk - q) / (Nk - 1)
        strata_rows.append({"stratum_key": int(k), "N": Nk, "quota": q})
    common_floor = [int(np.intersect1d(a, b).size) for a, b in zip(floor_rows["stateful"], floor_rows["counter"])]
    overlap = {
        "observed_common": common,
        "observed_common_reserved": common_res,
        "observed_common_statistical": common - common_res,
        "naive_srs_expectation_5000sq_over_N": N_SAMPLE ** 2 / full.n,
        "design_expectation": n_res + exp_stat,
        "design_expectation_statistical_layer": exp_stat,
        "design_sd_statistical_layer": math.sqrt(var_stat),
        "z_statistical_layer": (common - common_res - exp_stat) / math.sqrt(var_stat) if var_stat > 0 else None,
        "floor_common_stateful_s_vs_counter_s": {
            "seeds": f"{lo}..{hi - 1}",
            "min": int(min(common_floor)), "p2_5": float(np.percentile(common_floor, 2.5)),
            "median": float(np.median(common_floor)), "p97_5": float(np.percentile(common_floor, 97.5)),
            "max": int(max(common_floor)), "mean": float(np.mean(common_floor)),
        },
        "n_strata_with_quota": len(strata_rows),
    }

    # ---- 属性ごと
    out_attrs = {}
    summary = []
    for name, codes in attrs.items():
        cats = np.unique(codes)
        p_full = shares(codes, cats)
        p_full_rest = shares(codes[rest_rows], cats)
        p_old, p_new = shares(codes[r_old], cats), shares(codes[r_new], cats)
        stat_rows_old = r_old[~reserved[r_old]]
        stat_rows_new = r_new[~reserved[r_new]]
        p_old_stat, p_new_stat = shares(codes[stat_rows_old], cats), shares(codes[stat_rows_new], cats)
        F = {sch: np.stack([shares(codes[r], cats) for r in floor_rows[sch]]) for sch in floor_rows}
        D = np.abs(F["counter"] - F["stateful"])  # 同じ seed の旧と新の差の床
        exp_share = design_expected_shares(full, codes, cats, r_old)

        def attr_stats(rows: np.ndarray) -> dict:
            c = counts(codes[rows], cats)
            st, dof = chi2_vs_expected(c, exp_share, rows.size)
            return {"chi2": st, "dof": dof, "tvd": tvd(c / rows.size, exp_share)}

        s_old, s_new = attr_stats(r_old), attr_stats(r_new)
        fl = {sch: [attr_stats(r) for r in floor_rows[sch]] for sch in floor_rows}
        fl_tvd = {sch: np.array([x["tvd"] for x in fl[sch]]) for sch in fl}
        fl_chi = {sch: np.array([x["chi2"] for x in fl[sch]]) for sch in fl}
        diff_tvd_obs = tvd(p_old, p_new)
        diff_tvd_floor = np.array([tvd(a, b) for a, b in zip(F["stateful"], F["counter"])])

        def emp_p(obs: float, arr: np.ndarray) -> float:
            return float((1 + (arr >= obs - 1e-15).sum()) / (1 + arr.size))

        cats_out = []
        n_out_old = n_out_new = n_out_diff = 0
        lbl = labels.get(name, {})
        for j, c in enumerate(cats.tolist()):
            lo_s, hi_s = np.percentile(F["stateful"][:, j], [2.5, 97.5])
            lo_c, hi_c = np.percentile(F["counter"][:, j], [2.5, 97.5])
            d_hi = float(np.percentile(D[:, j], 95))
            in_old_f = bool(lo_s - 1e-12 <= p_old[j] <= hi_s + 1e-12)
            in_new_f = bool(lo_c - 1e-12 <= p_new[j] <= hi_c + 1e-12)
            in_diff = bool(abs(p_new[j] - p_old[j]) <= d_hi + 1e-12)
            n_out_old += not in_old_f
            n_out_new += not in_new_f
            n_out_diff += not in_diff
            cats_out.append({
                "code": c, "label": lbl.get(c, c),
                "full": float(p_full[j]), "full_nonreserved": float(p_full_rest[j]),
                "expected_design": float(exp_share[j]),
                "old": float(p_old[j]), "new": float(p_new[j]),
                "old_statistical_layer": float(p_old_stat[j]), "new_statistical_layer": float(p_new_stat[j]),
                "floor_stateful_p2_5": float(lo_s), "floor_stateful_p97_5": float(hi_s),
                "floor_counter_p2_5": float(lo_c), "floor_counter_p97_5": float(hi_c),
                "floor_absdiff_same_seed_p95": d_hi,
                "old_in_floor": in_old_f, "new_in_floor": in_new_f, "absdiff_in_floor": in_diff,
                "h_old_vs_full": float(cohen_h(p_old[j:j + 1], p_full[j:j + 1])[0]),
                "h_new_vs_full": float(cohen_h(p_new[j:j + 1], p_full[j:j + 1])[0]),
                "h_new_vs_old": float(cohen_h(p_new[j:j + 1], p_old[j:j + 1])[0]),
                "h_oldstat_vs_full_nonreserved": float(cohen_h(p_old_stat[j:j + 1], p_full_rest[j:j + 1])[0]),
                "h_newstat_vs_full_nonreserved": float(cohen_h(p_new_stat[j:j + 1], p_full_rest[j:j + 1])[0]),
            })
        # 抽出の仕組みそのものの偏り: 100 本の平均が二層抽出の期待の割合からずれるか(z = 差 / (標準偏差/√本数))
        bias = {}
        for sch in F:
            mu = F[sch].mean(axis=0)
            sd = F[sch].std(axis=0, ddof=1)
            # 100 本が全部同じ値(層の定員で決まる区分・一度も引かれない希な区分)は sd=0 なので、二項の sd
            # √(p(1−p)/n) で代える(浮動小数の丸めの差は 1e-12 未満を 0 とみなす)
            zero = sd < 1e-12
            sd_use = np.where(zero, np.sqrt(exp_share * (1 - exp_share) / N_SAMPLE), sd)
            dev = mu - exp_share
            dev = np.where(np.abs(dev) < 1e-12, 0.0, dev)
            z = np.zeros(cats.size)
            ok = sd_use > 0
            z[ok] = dev[ok] / (sd_use[ok] / math.sqrt(F[sch].shape[0]))
            zero_bad = int((zero & (dev != 0)).sum())
            bias[sch] = {"max_abs_z": float(np.abs(z).max()), "n_abs_z_gt_3": int((np.abs(z) > 3).sum()),
                         "n_zero_width_off_expectation": zero_bad}
            for j in range(cats.size):
                cats_out[j][f"floor_{sch}_mean"] = float(mu[j])
                cats_out[j][f"floor_{sch}_bias_z"] = float(z[j])
        rec = {
            "n_categories": int(cats.size),
            "floor_mean_vs_design_expectation": bias,
            "old": {**s_old, "p_chi2_multinomial": chi2_sf(s_old["chi2"], s_old["dof"]),
                    "p_empirical_chi2_vs_stateful_floor": emp_p(s_old["chi2"], fl_chi["stateful"]),
                    "p_empirical_tvd_vs_stateful_floor": emp_p(s_old["tvd"], fl_tvd["stateful"])},
            "new": {**s_new, "p_chi2_multinomial": chi2_sf(s_new["chi2"], s_new["dof"]),
                    "p_empirical_chi2_vs_counter_floor": emp_p(s_new["chi2"], fl_chi["counter"]),
                    "p_empirical_tvd_vs_counter_floor": emp_p(s_new["tvd"], fl_tvd["counter"])},
            "floor_tvd": {sch: {"median": float(np.median(fl_tvd[sch])),
                                "p97_5": float(np.percentile(fl_tvd[sch], 97.5)),
                                "max": float(fl_tvd[sch].max())} for sch in fl_tvd},
            "floor_chi2": {sch: {"median": float(np.median(fl_chi[sch])),
                                 "p97_5": float(np.percentile(fl_chi[sch], 97.5))} for sch in fl_chi},
            "tvd_old_vs_new": diff_tvd_obs,
            "floor_tvd_old_vs_new_same_seed": {"median": float(np.median(diff_tvd_floor)),
                                               "p97_5": float(np.percentile(diff_tvd_floor, 97.5)),
                                               "max": float(diff_tvd_floor.max())},
            "p_empirical_tvd_old_vs_new": emp_p(diff_tvd_obs, diff_tvd_floor),
            "max_abs_h_new_vs_old": float(np.max(np.abs(cohen_h(p_new, p_old)))),
            "max_abs_h_newstat_vs_oldstat": float(np.max(np.abs(cohen_h(p_new_stat, p_old_stat)))),
            "n_cat_old_outside_floor": n_out_old,
            "n_cat_new_outside_floor": n_out_new,
            "n_cat_absdiff_outside_floor": n_out_diff,
            "floor_width_zero_categories": int(sum(
                1 for j in range(cats.size)
                if F["stateful"][:, j].min() == F["stateful"][:, j].max()
                and F["counter"][:, j].min() == F["counter"][:, j].max())),
            "categories": cats_out,
        }
        out_attrs[name] = rec
        summary.append((name, rec))

    # 年齢の平均(標準化平均差)
    age = full.age.astype(np.float64)

    def smd(a: np.ndarray, b: np.ndarray) -> float:
        s = math.sqrt((a.var(ddof=1) + b.var(ddof=1)) / 2)
        return float((a.mean() - b.mean()) / s) if s > 0 else 0.0

    age_floor = {sch: np.array([age[r].mean() for r in floor_rows[sch]]) for sch in floor_rows}
    age_rec = {
        "mean_full": float(age.mean()), "mean_old": float(age[r_old].mean()), "mean_new": float(age[r_new].mean()),
        "smd_old_vs_full": smd(age[r_old], age), "smd_new_vs_full": smd(age[r_new], age),
        "smd_new_vs_old": smd(age[r_new], age[r_old]),
        "floor_mean_stateful": [float(np.percentile(age_floor["stateful"], 2.5)),
                                float(np.percentile(age_floor["stateful"], 97.5))],
        "floor_mean_counter": [float(np.percentile(age_floor["counter"], 2.5)),
                               float(np.percentile(age_floor["counter"], 97.5))],
    }

    # 素材の重なり: 合成体は同じセルの素材(v1 プールの行=pool_layer×pool_index)の複製なので、標本の中で
    # 同じ素材を持つ体の数(標本の体数 − 異なる素材の数)を数える
    src_key = full.pool_layer.astype(np.int64) * 10_000_000 + full.pool_index.astype(np.int64)

    def dup_src(rows: np.ndarray) -> int:
        return int(rows.size - np.unique(src_key[rows]).size)

    dup_floor = {sch: np.array([dup_src(r) for r in floor_rows[sch]]) for sch in floor_rows}
    dup_rec = {
        "old": dup_src(r_old), "new": dup_src(r_new),
        **{f"floor_{sch}": [float(np.percentile(dup_floor[sch], 2.5)), float(np.median(dup_floor[sch])),
                            float(np.percentile(dup_floor[sch], 97.5))] for sch in dup_floor},
    }

    total_cats = sum(r["n_categories"] for r in out_attrs.values())
    result = {
        "what": "10e E4 の住人の入れ替わり(旧 stateful / 新 counter・seed 1・5,000 体)の属性の分布の比較",
        "inputs": {
            "world": args.world, "population_file": POPULATION_FILE, "N_full": int(full.n),
            "n_reserved": n_res, "n_sample": N_SAMPLE, "seed": SEED,
            "floor_seeds": f"{lo}..{hi - 1}", "n_floor_seeds": len(floor_seeds),
            "population_hash_old": old.population_hash(), "population_hash_new": new.population_hash(),
            "population_hash_full": full.population_hash(),
        },
        "overlap": overlap,
        "age_mean": age_rec,
        "shared_source_material": dup_rec,
        "totals": {
            "n_attributes": len(out_attrs), "n_categories": total_cats,
            "n_cat_old_outside_floor": sum(r["n_cat_old_outside_floor"] for r in out_attrs.values()),
            "n_cat_new_outside_floor": sum(r["n_cat_new_outside_floor"] for r in out_attrs.values()),
            "n_cat_absdiff_outside_floor": sum(r["n_cat_absdiff_outside_floor"] for r in out_attrs.values()),
            "n_cat_floor_width_zero": sum(r["floor_width_zero_categories"] for r in out_attrs.values()),
            "scheme_bias_n_abs_z_gt_3": {sch: sum(r["floor_mean_vs_design_expectation"][sch]["n_abs_z_gt_3"]
                                                  for r in out_attrs.values()) for sch in ("stateful", "counter")},
            "scheme_bias_max_abs_z": {sch: max(r["floor_mean_vs_design_expectation"][sch]["max_abs_z"]
                                               for r in out_attrs.values()) for sch in ("stateful", "counter")},
        },
        "attributes": out_attrs,
    }
    Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")

    # 画面への要約
    print(f"N_full={full.n} reserved={n_res} common={common} (reserved {common_res})")
    print(json.dumps(overlap, ensure_ascii=False))
    print(json.dumps(age_rec, ensure_ascii=False))
    print(json.dumps(dup_rec, ensure_ascii=False))
    print(json.dumps(result["totals"], ensure_ascii=False))
    for name, r in summary:
        print(f"{name}: k={r['n_categories']} old tvd={r['old']['tvd']:.4f} p_emp={r['old']['p_empirical_tvd_vs_stateful_floor']:.3f}"
              f" chi2p={r['old']['p_chi2_multinomial']:.3f} | new tvd={r['new']['tvd']:.4f}"
              f" p_emp={r['new']['p_empirical_tvd_vs_counter_floor']:.3f} chi2p={r['new']['p_chi2_multinomial']:.3f}"
              f" | old-new tvd={r['tvd_old_vs_new']:.4f} floor97.5={r['floor_tvd_old_vs_new_same_seed']['p97_5']:.4f}"
              f" p={r['p_empirical_tvd_old_vs_new']:.3f} | out old/new/diff={r['n_cat_old_outside_floor']}/"
              f"{r['n_cat_new_outside_floor']}/{r['n_cat_absdiff_outside_floor']} zero={r['floor_width_zero_categories']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
