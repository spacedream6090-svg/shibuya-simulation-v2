"""第 4 期 4-1 段 1〜3: W16(本体の v2)と W21(``v2_stage_4-1``)の対応の表(参考・合否なし・集計だけ)。

    python docs/bench/analysis/wallbounce-1012/pop41/tools/w16_vs_w21.py --w16 data/world/v2 \
        --w21 data/world/v2_stage_4-1 --out docs/bench/analysis/wallbounce-1012/pop41/w16_vs_w21.json

- 層ごとの人数(W16 の kind ごと・W21 は住民だけ=ほかの層は段 7)・世帯の形(人員の分布・W21 は家族類型も)・
  住民の属性の分布(年齢 16 階級 × 男女・外国人・``industry_key``)の差(SRMSE・JSD)。
- 個人の行は書かない(集計だけ)。``agent_id`` の対応は決めない(親)。絶対パスは書かない。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / "src"))

from shibuya.build.pop import fitting as F  # noqa: E402
from shibuya.build.pop import w16_population as W16  # noqa: E402

EDGES = np.asarray(W16.AGE_EDGES)


def _age_sex(age: np.ndarray, sex: np.ndarray) -> np.ndarray:
    k = np.searchsorted(EDGES, age, side="right") - 1
    out = np.zeros((EDGES.size, 2))
    np.add.at(out, (k, np.clip(sex, 0, 1)), 1.0)
    return out


def _dist(v: np.ndarray) -> dict[str, int]:
    u, c = np.unique(np.asarray(v).astype(str), return_counts=True)
    return {str(a): int(b) for a, b in zip(u, c)}


def _cmp(a: dict[str, int], b: dict[str, int]) -> dict[str, float]:
    keys = sorted(set(a) | set(b))
    x = np.array([a.get(k, 0) for k in keys], dtype=float)
    y = np.array([b.get(k, 0) for k in keys], dtype=float)
    return {"srmse": round(F.srmse(y, x), 6), "jsd": round(F.jsd(y, x), 6)}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--w16", default="data/world/v2")
    ap.add_argument("--w21", default="data/world/v2_stage_4-1")
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    w16 = pq.read_table(Path(a.w16) / "w16_population.parquet",
                        columns=["kind", "age", "sex", "household_id", "industry_key", "is_foreign", "synthetic"])
    kind = np.asarray(w16.column("kind"))
    names = W16.KIND_NAMES
    res16 = np.isin(kind, [W16.KIND_RESIDENT, W16.KIND_WORKER]) & (np.asarray(w16.column("household_id")) >= 0)
    hh16 = pq.read_table(Path(a.w16) / "w16_households.parquet", columns=["size"])
    p21 = pq.read_table(Path(a.w21) / "w21_persons.parquet",
                        columns=["age", "sex", "industry_key", "is_foreign", "employment_status", "relation"])
    h21 = pq.read_table(Path(a.w21) / "w21_households.parquet", columns=["size", "family_type", "family_group"])
    age16, sex16 = np.asarray(w16.column("age"))[res16], np.asarray(w16.column("sex"))[res16]
    age21, sex21 = np.asarray(p21.column("age")), np.asarray(p21.column("sex"))
    as16, as21 = _age_sex(age16, sex16), _age_sex(age21, sex21)
    size16 = np.asarray(hh16.column("size"))
    ft21 = np.asarray(h21.column("family_type")).astype(str)
    gen21 = ft21 != "institution"
    size21 = np.asarray(h21.column("size"))[gen21]
    ik16 = np.asarray(w16.column("industry_key")).astype(str)[res16]
    ik21 = np.asarray(p21.column("industry_key")).astype(str)
    doc = {
        "schema": "pop41.w16_vs_w21/1",
        "note": "参考(合否なし)。W16=本体の v2・W21=v2_stage_4-1。W21 は住民だけ(通勤・通学・来街・乗り換えだけ・通過は段 7)",
        "layers": {
            "w16_by_kind": {names[k]: int((kind == k).sum()) for k in range(len(names))},
            "w16_synthetic": int(np.asarray(w16.column("synthetic")).sum()),
            "w16_residents_with_household": int(res16.sum()),
            "w21_residents": int(p21.num_rows),
            "w21_synthetic": 0,
        },
        "household_shape": {
            "w16_households": int(size16.size),
            "w16_size_share": {str(s): round(float((size16 == s).mean()), 4) for s in np.unique(size16)},
            "w21_general_households": int(gen21.sum()),
            "w21_institution_persons": int((~gen21).sum()),
            "w21_size_share": {str(s): round(float((size21 == s).mean()), 4) for s in np.unique(size21)},
            "w21_family_group": _dist(np.asarray(h21.column("family_group"))[gen21]),
        },
        "residents_age16_sex": {
            "w16": as16.astype(int).tolist(), "w21": as21.astype(int).tolist(),
            "srmse_w21_vs_w16": round(F.srmse(as21, as16), 6), "jsd_w21_vs_w16": round(F.jsd(as21, as16), 6),
            "male_share": {"w16": round(float((sex16 == 0).mean()), 4), "w21": round(float((sex21 == 0).mean()), 4)},
            "mean_age": {"w16": round(float(age16.mean()), 2), "w21": round(float(age21.mean()), 2)},
        },
        "residents_foreign": {"w16": int(np.asarray(w16.column("is_foreign"))[res16].sum()),
                              "w21": int(np.asarray(p21.column("is_foreign")).sum())},
        "residents_industry_key": {
            "w16": _dist(ik16), "w21": _dist(ik21),
            "among_nonblank": _cmp({k: v for k, v in _dist(ik16).items() if k},
                                   {k: v for k, v in _dist(ik21).items() if k}),
            "note": "W16 の住民の industry_key は舞台の中の組織の席に座った人(kind 2)だけ・W21 は区のどこで働く人も(段 4 で席に結ぶ)",
        },
        "w21_employment_status": _dist(np.asarray(p21.column("employment_status"))),
    }
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({k: doc[k] for k in ("layers", "residents_foreign")}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
