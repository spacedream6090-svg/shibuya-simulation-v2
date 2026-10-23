"""W10 の主の物差し(診断・第330 B4・答え 10-12b 1-6 の 3・指示書 10-03 §9-4 の 4)。

「実測の地点と同じ距離で ASJ の式を評価する」。交通量は**騒音場がその道路の辺に当てた値**
(ON+Q7=路線の区間の中央値・OFF=klass 既定)。W10 の段には結線しない(``w10_ruler.py`` と同じ扱い・
値は 10e の記録に書く・W10 のヘッダには入れない)。

**循環であること(必ず読む)**: ON の辺に当てる値は較正 ``calibrate()`` と同じ規則(路線名で引いた
センサスの区間の中央値 ``median_section``)なので、ON の残差は較正の残差と**ほぼ同じ計算**になる
(違いは舗装の区分・車線と幅員の出どころ・区間を引く区の順だけ)。現実との照合にはならない。
意味があるのは OFF(klass 既定)と ON の差だけ。現実との照合は、較正に使っていない別の測定点で
行う(リサーチ F6・10e の外)。

規則(expedient=未リサーチ):
- 測れる点 = 較正点のうち、その路線の辺が世界の中で ON+Q7 の対応表に立つもの(``w10_edge_section``
  の ``traffic_from_census`` が真で ``census_route`` が点の路線)。見込みは No.61(都道 423)と No.79(環六)。
- 辺ごとに、その辺に当てた区間の諸元(交通量・大型車混入率・速度・幅員・車線)で、距離
  d = 実測の車道端距離 + 辺の区間の幅員/2 の LAeq を ``laeq_at`` で評価する。舗装は騒音場と同じ
  ``nonsteady_dense``(較正は点の CSV の低騒音舗装欄を使う=ここが較正と違う)。
- 路線の辺が複数あるので、辺ごとの値の**中央値**(下側)を点の値にする(親案・expedient)。

    python docs/bench/analysis/wallbounce-1012/10e/w10_primary_ruler.py \\
        --world data/world/v2 --data data --out docs/bench/analysis/wallbounce-1012/10e/b4_w10_primary_ruler.json
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import pyarrow.parquet as pq

from shibuya.build.field import common as C
from shibuya.build.field import w10_noise as W

#: 点 → 世界の対応表の路線ラベル(``census_route``)。点の CSV の路線名とセンサスの路線を結ぶ。
POINT_ROUTE = {"61": "6:423:渋谷経堂線", "79": "4:317:環状六号線"}


def census_defaults(sections: list[dict]) -> dict[str, dict[str, float]]:
    """``w10_noise.run`` の klass 既定表と同じ作り方(渋谷区の実測行 → primary/secondary・他は倍率)。"""
    shibuya = [s for s in sections if s["city"] == "13113"]
    out: dict[str, dict[str, float]] = {}
    for klass, rule in W.KLASS_DEFAULT_RULE.items():
        if "from_census" in rule:
            kinds = {str(k) for k in rule["from_census"]}
            out[klass] = W.median_section([s for s in shibuya if s["road_kind"] in kinds])
    for klass, rule in W.KLASS_DEFAULT_RULE.items():
        if "scale_of" in rule:
            base = out[rule["scale_of"]]
            out[klass] = {
                "q12": base["q12"] * rule["q"], "q24": base["q24"] * rule["q"],
                "heavy_pct": base["heavy_pct"], "v_kmh": float(rule["v"]),
                "width_m": float(rule["width_m"]), "lanes": float(rule["lanes"]), "n": 0.0,
            }
    return out


def lower_median(xs: list[float]) -> float:
    s = sorted(xs)
    return s[(len(s) - 1) // 2]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--data", default="data")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    world, data = Path(args.world), Path(args.data)
    header = json.loads((world / "W10.header.json").read_text(encoding="utf-8"))
    sections = W.read_kasyo(data.joinpath(*W.KASYO))
    points = {p["no"]: p for p in W.read_r5_points(data.joinpath(*W.R5_POINTS))}
    defaults = census_defaults(sections)
    # 検算: 作り直した klass 既定表が W10 のヘッダの notes と一致すること(丸め 3 桁)
    for k, v in header["notes"]["census_defaults"].items():
        assert {kk: round(vv, 3) for kk, vv in defaults[k].items()} == v, k
    route_secs = {k: v for k, v in header["notes"]["road_name_route_sections"].items()}
    t = pq.read_table(world / "w10_edge_section.parquet").to_pydict()
    applied = bool(header["notes"]["road_name_match_applied"])
    if not applied:
        raise SystemExit("ON の世界(W10 の対応表を当てた資産)で回す。OFF の値は同じ辺の klass 既定で並べて出す")
    rows = []
    for no, label in POINT_ROUTE.items():
        p = points[no]
        edges = [
            (int(e), k)
            for e, k, r, on in zip(t["edge_idx"], t["klass"], t["census_route"], t["traffic_from_census"])
            if r == label and on
        ]
        if not edges:
            rows.append({"no": no, "route": label, "status": "NOT_MEASURABLE", "n_edges": 0})
            continue
        row = {"no": no, "route": label, "status": "OK", "n_edges": len(edges),
               "klass_of_edges": dict(sorted(Counter(k for _e, k in edges).items())),
               "measured_day_db": p["measured_day_db"], "measured_night_db": p["measured_night_db"]}
        for mode in ("on", "off"):
            vals = []
            for _e, klass in edges:
                sec = route_secs[label] if mode == "on" else defaults[klass]
                d = float(p["dist_from_carriageway_m"]) + float(sec["width_m"]) / 2.0
                vals.append(W.laeq_at(sec, d, "nonsteady_dense"))
            day = lower_median([v[0] for v in vals])
            night = lower_median([v[1] for v in vals])
            row[f"{mode}_model_day_db"] = round(day, 1)
            row[f"{mode}_model_night_db"] = round(night, 1)
            row[f"{mode}_residual_day_db"] = round(day - p["measured_day_db"], 1)
            row[f"{mode}_residual_night_db"] = round(night - p["measured_night_db"], 1)
            row[f"{mode}_edge_day_db_range"] = [round(min(v[0] for v in vals), 1), round(max(v[0] for v in vals), 1)]
        rows.append(row)
    calib = {r["no"]: (r.get("residual_day_db"), r.get("residual_night_db")) for r in header["notes"]["calibration_rows"]}
    out = {
        "what": "W10 の主の物差し(診断・循環=ON は較正とほぼ同じ計算)",
        "world_w10_stage_version": header["stage_version"],
        "road_name_match_applied": applied,
        "require_named_same_class": header["params"]["road_name_match"]["require_named_same_class"],
        "edge_set_rule": (
            "ON の世界の対応表で census_route=点の路線 かつ traffic_from_census の辺。on=その辺に当てた路線の区間・"
            "off=同じ辺の klass 既定(OFF の騒音場がその辺に当てる値)"
        ),
        "rows": rows,
        "calibration_residuals_same_points": {no: calib.get(no) for no in POINT_ROUTE},
        "circularity_note": (
            "ON の辺に当てる値は較正と同じ median_section(路線名で引いたセンサスの区間の中央値)。"
            "較正との違いは舗装(ここは nonsteady_dense・較正は点の CSV の低騒音舗装欄)と幅員・車線の出どころだけ。"
            "現実との照合は較正に使っていない別の測定点で行う(リサーチ F6・10e の外)。"
        ),
        "expedients": ["路線の辺が複数あるときは辺ごとの値の下側中央値(親案)", "舗装は騒音場と同じ密粒"],
    }
    Path(args.out).write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(rows, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
