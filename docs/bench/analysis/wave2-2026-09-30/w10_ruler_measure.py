"""§W10(2026-09-30): W10 の Q6 の物差しと ON+Q7 の資産(別の出力先)の計測。

使い方(リポジトリの根から・出力先はリポの外=OS の一時ディレクトリ)::

    # 1) 検算 → W10 を OFF と ON+Q7 で別の出力先に構築 → OFF が昇格版とバイト一致か →
    #    ON+Q7 の §1c′ の値 → 物差し(OFF / ON+Q7)→ w10_ruler.json
    python docs/bench/analysis/wave2-2026-09-30/w10_ruler_measure.py build --tmp <一時ディレクトリ>
    # 2) 15 腕のランに使う世界の写し(data/world/v2 の直下のファイルを複写し、onq7 は W10 の出力を差し替え)
    python docs/bench/analysis/wave2-2026-09-30/w10_ruler_measure.py world --tmp <一時ディレクトリ> --variant onq7
    # 3) 15 腕の新旧を束ねる(w6_regen_measure.py の run/collect の出力 2 つ)
    python docs/bench/analysis/wave2-2026-09-30/w10_ruler_measure.py checkpoint \\
        --before <OFF の出力先> --after <ON+Q7 の出力先>

- 世界資産(data/world/v2)は**読むだけ**(W1 の 2 ファイルと build_manifest.json と、手順 2 の複写元)。
- 切替口は ``w10_noise`` のモジュール定数をこのプロセスの中でだけ書き換える(既定は OFF のまま)。
- JSON に絶対パス・OSM の生の名前の一覧を書かない(路線はセンサスのラベル=番号と路線名)。
- 物差しの構成(代表点・半径・代表値)は**未リサーチ(expedient)**(``build/field/w10_ruler.py``)。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from collections import Counter
from pathlib import Path
from typing import Any

import numpy as np

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO / "src"))

from shibuya.build.field import common as C  # noqa: E402
from shibuya.build.field import road_names as RN  # noqa: E402
from shibuya.build.field import w10_noise as W  # noqa: E402
from shibuya.build.field import w10_ruler as R  # noqa: E402

DATA = REPO / "data"
WORLD = DATA / "world" / "v2"
HERE = Path(__file__).resolve().parent
OUT_JSON = HERE / "w10_ruler.json"
CKPT_JSON = HERE / "w10_checkpoint.json"

VARIANTS: dict[str, dict[str, bool]] = {
    "off": {"USE_ROAD_NAME_MATCH": False, "ROAD_NAME_REQUIRE_NAMED_SAME_CLASS": False,
            "ROAD_NAME_REQUIRE_SAME_BAND": False},
    "onq7": {"USE_ROAD_NAME_MATCH": True, "ROAD_NAME_REQUIRE_NAMED_SAME_CLASS": True,
             "ROAD_NAME_REQUIRE_SAME_BAND": False},
}
W10_OUTPUTS = (
    "w10_street_points.parquet", "w10_noise_day.npy", "w10_noise_night.npy",
    "w10_noise_stage_day.npy", "w10_noise_stage_night.npy", "w10_edge_section.parquet",
)
STAGE_VOCAB = W.NOISE_STAGE_VOCAB


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def write_json(path: Path, obj: Any) -> None:
    """UTF-8・LF(Windows でも CR を入れない)。"""
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(json.dumps(obj, ensure_ascii=False, indent=1) + "\n")


def manifest_w10() -> dict[str, str]:
    m = json.loads((WORLD / "build_manifest.json").read_text(encoding="utf-8"))
    st = next(s for s in m["stages"] if s["stage"] == "W10")
    return {o["path"]: o["sha256"] for o in st["outputs"]}


# ------------------------------------------------------------------ 検算
def self_check() -> dict[str, Any]:
    """答えの分かっている合成の場面で物差しを検算する(tests/build_field/test_w10_ruler.py と同じ場面)。"""
    ring = np.array([[-100, -100], [100, -100], [100, 100], [-100, 100]], dtype=np.float64)
    from shibuya.build.pop import shapefile as SH

    ch = R.Chome("t", "テスト町一丁目", SH.Polygon(np.array([0]), ring, (-100, -100, 100, 100)), (0.0, 0.0), 40000.0)
    xs = np.arange(-100.0, 101.0, 10.0)
    gx = np.concatenate([xs, xs, [0.0]])
    gy = np.concatenate([np.full(xs.size, 50.0), np.full(xs.size, -50.0), [80.0]])
    gday = np.concatenate([np.full(xs.size, 70.0), np.full(xs.size, 55.0), [90.0]])
    gklass = ["primary"] * xs.size + ["residential"] * xs.size + ["service"]
    seg = (np.array([-100.0]), np.array([52.0]), np.array([100.0]), np.array([52.0]), np.array([0]))
    pts = [{"no": "1", "address": "渋谷区テスト町1丁目2", "road_kind": "4",
            "measured_day_db": 65.0, "measured_night_db": 60.0}]
    row = R.ruler_rows(pts, {ch.s_name: ch}, gx, gy, gday, gday - 4.0, gklass, lambda k: seg)[0]
    expect = {
        ("estat", "max", "25"): None, ("estat", "max", "50"): [5.0, 6.0],
        ("estat", "max", "100"): [25.0, 26.0], ("estat", "road", "100"): [5.0, 6.0],
        ("road_facing", "max", "25"): [5.0, 6.0], ("road_facing", "max", "50"): [25.0, 26.0],
        ("road_facing", "road", "50"): [5.0, 6.0],
    }
    got = {k: row["diff"][k[0]][k[1]][k[2]] for k in expect}
    ok = got == expect
    if not ok:
        raise SystemExit(f"検算が合わない(止める): {got} != {expect}")
    return {"passed": True, "cases": len(expect)}


# ------------------------------------------------------------------ 構築
def build_variant(tmp: Path, name: str) -> tuple[C.StageResult, Path]:
    out = tmp / name
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    for f in ("w1_edges.parquet", "w1_edge_geometry.npz"):
        shutil.copyfile(WORLD / f, out / f)
    saved = {k: getattr(W, k) for k in VARIANTS[name]}
    try:
        for k, v in VARIANTS[name].items():
            setattr(W, k, v)
        res = W.run(C.Ctx(data=DATA, out=out))
        C.write_header(out, res)
    finally:
        for k, v in saved.items():
            setattr(W, k, v)
    return res, out


def cell_stages(out: Path) -> tuple[np.ndarray, np.ndarray]:
    """W10 の街路点の段階 → セル(w2_cells の ix, iy, band)ごとの最頻値(知覚の集約と同じ規則)。"""
    import pyarrow.parquet as pq

    cells = pq.read_table(WORLD / "w2_cells.parquet", columns=["ix", "iy", "band"]).to_pydict()
    code = {"UG": -1, "GL": 0, "DECK": 1}

    def key(a, b, c):
        return (np.asarray(a, np.int64) + 1_000_000) * 8_000_000 + (np.asarray(b, np.int64) + 1_000_000) * 4 + (
            np.asarray(c, np.int64) + 1
        )

    ck = key(cells["ix"], cells["iy"], [code[b] for b in cells["band"]])
    order = np.argsort(ck, kind="stable")
    sk = ck[order]
    d = pq.read_table(out / "w10_street_points.parquet", columns=["x", "y", "band"]).to_pydict()
    q = key(np.floor(np.asarray(d["x"]) / 100.0), np.floor(np.asarray(d["y"]) / 100.0), [code[b] for b in d["band"]])
    pos = np.clip(np.searchsorted(sk, q), 0, sk.size - 1)
    cop = np.where(sk[pos] == q, order[pos], -1)
    valid = cop >= 0
    res = []
    for f in ("w10_noise_stage_day.npy", "w10_noise_stage_night.npy"):
        st = np.load(out / f).astype(np.int64)
        tab = np.bincount(cop[valid] * 4 + np.clip(st[valid], 0, 3), minlength=ck.size * 4).reshape(ck.size, 4)
        res.append(tab.argmax(axis=1))
    return res[0], res[1]


def refine_stats(res: C.StageResult, out: Path, off_out: Path) -> dict[str, Any]:
    """§1c′ の値(当てた辺・primary+secondary・階級の不一致・既定比の最大・騒音段階の変わるセル)。"""
    import pyarrow.parquet as pq

    t = pq.read_table(out / "w10_edge_section.parquet").to_pydict()
    gates = {g.name: g.to_json() for g in res.gates}
    applied = [i for i, a in enumerate(t["traffic_from_census"]) if a]
    mismatch = Counter(
        f"{t['klass'][i]}->{t['way_highway'][i]}"
        for i in applied
        if RN.CLASS_TIER.get(t["klass"][i], "") != RN.CLASS_TIER.get(t["way_highway"][i], "?")
    )
    routes = res.notes["road_name_route_sections"]
    defaults = res.notes["census_defaults"]
    ratios = [routes[t["census_route"][i]]["q24"] / defaults[t["klass"][i]]["q24"] for i in applied]
    d_off, n_off = cell_stages(off_out)
    d_on, n_on = cell_stages(out)

    def trans(a, b):
        return dict(sorted(Counter(
            f"{STAGE_VOCAB[x]}->{STAGE_VOCAB[y]}" for x, y in zip(a.tolist(), b.tolist()) if x != y
        ).items()))

    return {
        "applied_edges": len(applied),
        "primary_secondary_applied": gates["primary_secondary_sections_matched"]["value"],
        "primary_secondary_gate_pass": gates["primary_secondary_sections_matched"]["pass"],
        "applied_klass_tier_mismatch": sum(mismatch.values()),
        "applied_mismatch_detail": dict(mismatch),
        "applied_ratio_to_klass_default_max": round(max(ratios), 2) if ratios else None,
        "applied_by_route": dict(sorted(Counter(t["census_route"][i] for i in applied).items())),
        "day_db_percentiles": res.notes["day_db_percentiles"],
        "night_db_percentiles": res.notes["night_db_percentiles"],
        "cells_total": int(d_off.size),
        "cells_stage_changed_vs_off": {"day": int((d_off != d_on).sum()), "night": int((n_off != n_on).sum())},
        "cell_day_transitions": trans(d_off, d_on),
        "cell_night_transitions": trans(n_off, n_on),
        "calibration_residuals": {
            r["no"]: [r["residual_day_db"], r["residual_night_db"]] for r in res.notes["calibration_rows"]
        },
    }


def ruler(out: Path) -> list[dict[str, Any]]:
    """構築した W10 の騒音場で物差しを測る。"""
    import pyarrow.parquet as pq

    rows = R.ruler_from_world(out, DATA)
    d = pq.read_table(out / "w10_street_points.parquet", columns=["x", "y", "band", "nearest_edge_idx"]).to_pydict()
    gl = np.asarray([b == "GL" for b in d["band"]], dtype=bool)
    gx = np.asarray(d["x"], np.float64)[gl]
    gy = np.asarray(d["y"], np.float64)[gl]
    # 代表点がどの道の上か(最寄りの格子点の最寄りの辺の klass と、その変種の対応表の路線ラベル)
    sec = pq.read_table(out / "w10_edge_section.parquet",
                        columns=["edge_idx", "klass", "census_route", "traffic_from_census"]).to_pydict()
    row_of = {int(e): i for i, e in enumerate(sec["edge_idx"])}
    ne = np.asarray(d["nearest_edge_idx"])[gl]
    for r in rows:
        if r["status"] != "OK":
            continue
        r["rep_edge"] = {}
        for rep, xy in r["rep_xy"].items():
            if xy is None:
                r["rep_edge"][rep] = None
                continue
            k = int(np.argmin(np.hypot(gx - xy[0], gy - xy[1])))
            i = row_of[int(ne[k])]
            r["rep_edge"][rep] = {
                "klass": sec["klass"][i], "census_route": sec["census_route"][i],
                "traffic_from_census": bool(sec["traffic_from_census"][i]),
            }
    return rows


def centerline_offset(calib_rows: list[dict[str, Any]]) -> dict[str, Any]:
    """騒音場は道路の上(車道中心線から 8 m 以内)の格子で評価される一方、実測は車道端から 2.4〜6.8 m・
    高さ 1.2 m。同じ式・同じ区間で「中心線上(d=0=半車線幅の床)− 実測の位置」を出す(物差しの系統差の目安)。
    区間の値は較正行の丸めた値(旅行速度 0.1 km/h)を使う=近似。"""
    out: dict[str, Any] = {}
    for r in calib_rows:
        if r.get("status") != "OK":
            continue
        sec = {k: float(r[k]) for k in ("q12", "q24", "heavy_pct", "v_kmh", "width_m", "lanes")}
        d_meas = float(r["dist_from_carriageway_m"]) + sec["width_m"] / 2.0
        c_day, c_night = W.laeq_at(sec, 0.0, r["regime"])
        m_day, m_night = W.laeq_at(sec, d_meas, r["regime"])
        out[r["no"]] = {
            "centerline_minus_roadside_db": [round(c_day - m_day, 1), round(c_night - m_night, 1)],
            "roadside_distance_from_centerline_m": round(d_meas, 1),
            "beyond_street_grid_buffer_8m": d_meas > 8.0,
        }
    return out


def ruler_summary(rows: list[dict[str, Any]]) -> dict[str, Any]:
    ok = [r for r in rows if r["status"] == "OK"]
    out: dict[str, Any] = {}
    for rep in R.REPRESENTATIVES:
        for s in R.STATISTICS:
            for rad in R.RADII_M:
                k = str(int(rad))
                out[f"{rep}/{s}/r{k}"] = R.summarize_diffs([r["diff"][rep][s][k] for r in ok])
        # road のうち距離が格子の帯(8 m)の中のものだけ(帯の外=道路の値ではない)
        for rad in R.RADII_M:
            k = str(int(rad))
            out[f"{rep}/road_within_band/r{k}"] = R.summarize_diffs([
                r["diff"][rep]["road"][k] for r in ok if r["road_beyond_band"][rep].get(k) is False
            ])
    return out


def cmd_build(args: argparse.Namespace) -> int:
    tmp = Path(args.tmp)
    doc: dict[str, Any] = {
        "schema": "shibuya.bench/wave2-2026-09-30/w10_ruler/1",
        "self_check": self_check(),
        "expedient": (
            "物差しの構成(代表点 estat/road_facing・半径 25/50/100 m・代表値 max/road・道路種別→階級の表)は"
            "未リサーチ(expedient)。build/field/w10_ruler.py の docstring。"
        ),
        "radii_m": list(R.RADII_M),
        "representatives": list(R.REPRESENTATIVES),
        "statistics": list(R.STATISTICS),
        "measured_road_klasses": {k: list(v) for k, v in R.MEASURED_ROAD_KLASSES.items()},
    }
    promoted = manifest_w10()
    built: dict[str, Path] = {}
    results: dict[str, C.StageResult] = {}
    for name in VARIANTS:
        res, out = build_variant(tmp, name)
        built[name] = out
        results[name] = res
        sha = {o["path"]: o["sha256"] for o in res.outputs}
        doc[name] = {"switches": VARIANTS[name], "outputs_sha256": sha,
                     "gates": {g.name: g.to_json() for g in res.gates}}
        print(f"[{name}] built; outputs {len(sha)}", flush=True)
    off_equal = doc["off"]["outputs_sha256"] == promoted
    doc["off"]["equals_promoted_manifest"] = off_equal
    if not off_equal:
        write_json(OUT_JSON, doc)
        print("OFF の W10 の出力が昇格版の build_manifest と一致しない(止める)", file=sys.stderr)
        return 3
    doc["onq7"]["refine"] = refine_stats(results["onq7"], built["onq7"], built["off"])
    doc["onq7"]["noise_outputs_differ_from_off"] = {
        f: doc["onq7"]["outputs_sha256"][f] != doc["off"]["outputs_sha256"][f] for f in W10_OUTPUTS
    }
    for name in VARIANTS:
        rows = ruler(built[name])
        doc[name]["ruler_rows"] = rows
        doc[name]["ruler_summary"] = ruler_summary(rows)
    doc["centerline_offset"] = centerline_offset(results["off"].notes["calibration_rows"])
    write_json(OUT_JSON, doc)
    print(f"wrote {OUT_JSON.name}")
    return 0


def cmd_world(args: argparse.Namespace) -> int:
    """15 腕のランに使う世界の写し(直下のファイルだけ・サブディレクトリは複写しない)。

    置き場所は ``<tmp>/data/world/v2_<変種>``=リポと同じ並び。エンジンは街路施設の JSON を
    ``world_dir.parent.parent / realworld / osm`` に探し、無ければ**黙ってバス運行を休む**
    (``world/assets.py`` の ``_street_features_path``)ので、その 1 ファイルも同じ並びに複写する。
    """
    tmp = Path(args.tmp)
    dst = tmp / "data" / "world" / f"v2_{args.variant}"
    dst.mkdir(parents=True, exist_ok=True)
    osm = tmp / "data" / "realworld" / "osm"
    osm.mkdir(parents=True, exist_ok=True)
    sf = DATA / "realworld" / "osm" / "street_features_overpass_20260907.json"
    if not (osm / sf.name).exists():
        shutil.copyfile(sf, osm / sf.name)
    for f in sorted(WORLD.iterdir()):
        if f.is_file() and not (dst / f.name).exists():
            shutil.copyfile(f, dst / f.name)
    if args.variant != "off":
        src = tmp / args.variant
        for f in (*W10_OUTPUTS, "W10.header.json"):
            shutil.copyfile(src / f, dst / f)
    # 差し替えの確認(W10 の出力の sha256)
    rep = {f: sha256(dst / f)[:12] for f in W10_OUTPUTS}
    print(json.dumps(rep, ensure_ascii=False))
    return 0


def cmd_checkpoint(args: argparse.Namespace) -> int:
    def load(d: str) -> dict[str, dict[str, Any]]:
        doc = json.loads((Path(d) / "summary.json").read_text(encoding="utf-8"))
        return {r["arm"]: r for r in doc["arms"]}

    before, after = load(args.before), load(args.after)
    rows = []
    for name in before:
        b, a = before[name], after.get(name)
        if a is None:
            continue
        rows.append({
            "arm": name, "args": b["args"],
            "final_off": b["final_hash"][:16], "final_onq7": a["final_hash"][:16],
            "moved": b["final_hash"] != a["final_hash"],
            "calls_off": b["llm_calls"], "calls_onq7": a["llm_calls"],
            "calls_by_condition_delta": {
                k: a["calls_by_condition"].get(k, 0) - b["calls_by_condition"].get(k, 0)
                for k in sorted(set(a["calls_by_condition"]) | set(b["calls_by_condition"]))
                if a["calls_by_condition"].get(k, 0) != b["calls_by_condition"].get(k, 0)
            },
            "conserved_onq7": a["conserved"],
            "frozen_sources_equal": a.get("frozen_sources") == b.get("frozen_sources"),
        })
    write_json(CKPT_JSON, {"schema": "shibuya.bench/wave2-2026-09-30/w10_checkpoint/1", "n_agents": 5000,
                           "seed": 1, "src": args.src_note, "rows": rows})
    for r in rows:
        print(f"{r['arm']:24s} {r['final_off'][:8]} -> {r['final_onq7'][:8]} calls {r['calls_off']:,} -> {r['calls_onq7']:,}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    b = sub.add_parser("build")
    b.add_argument("--tmp", required=True)
    w = sub.add_parser("world")
    w.add_argument("--tmp", required=True)
    w.add_argument("--variant", choices=list(VARIANTS), required=True)
    k = sub.add_parser("checkpoint")
    k.add_argument("--before", required=True)
    k.add_argument("--after", required=True)
    k.add_argument("--src-note", default="")
    args = ap.parse_args(argv)
    return {"build": cmd_build, "world": cmd_world, "checkpoint": cmd_checkpoint}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
