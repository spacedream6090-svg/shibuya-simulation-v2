"""第 2 波 §2A 項 3-2: 古典の腕の「まで」の長さの候補 (a)(b) の比較(**実装していない**・親に問う材料)。

使い方(リポのルートで・openpyxl のあるシステムの python): ``python $D/until_candidates.py --out $D/item3_until_candidates.json``

(a) 錨 ``docs/bench/anchors/ssb2021_activity_prior_v0.json``(平日・関東大都市圏・4 層=性 × 就業の年齢総数の行を
    推定人口で加重)の 15 分帯の行動者率 s(b) から c(b)=min(1, s(b+1)/s(b))(流入 0 と置く)。
    - 集計の平均の長さ=15 分 × Σ s / Σ max(0, s(b+1) − s(b))(始まりの数=正味の流入)。
    - 事前分布どおりに始めた場合の平均の長さ=帯 b から始めて 15 分 × Σ_k Π_{j<k} c(b+j)(上限 480 分)を s(b) で加重。
(b) 令和3年社会生活基本調査 生活時間編 第4-1表(総平均時間)÷ 第4-3表(行動者率)=**行動者平均時間(1 日の合計)**
    (平日・全国・15 歳以上・男女/就業/健康/一緒にいた人=総数)。1 日 1 回と置いた場合の平均の長さ=その値(=上限)。
    1 日の回数の表は手元に無い(data/calib/hunger/ と data/research_cache/r69/ を確認)。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

ANCHOR = Path("docs/bench/anchors/ssb2021_activity_prior_v0.json")
T41 = Path("data/research_cache/r69/ssb2021_seikatsu_t4-1_000032223881.xlsx")
T43 = Path("data/research_cache/r69/ssb2021_seikatsu_t4-3_000032223883.xlsx")
NAMES = {"01": "睡眠", "02": "身の回りの用事", "04": "通勤・通学", "05": "仕事", "06": "学業", "07": "家事",
         "08": "介護・看護", "09": "育児", "10": "買い物", "11": "移動(通勤・通学を除く)",
         "12": "テレビ・ラジオ・新聞・雑誌", "13": "休養・くつろぎ", "14": "学習・自己啓発・訓練", "15": "趣味・娯楽",
         "16": "スポーツ", "17": "ボランティア・社会参加", "18": "交際・付き合い", "19": "受診・療養", "20": "その他"}


def candidate_a() -> dict[str, dict[str, float]]:
    d = json.loads(ANCHOR.read_text(encoding="utf-8"))
    block = d["tables"]["weekday"]["03"]
    s = np.zeros((len(d["activity_codes"]), int(d["n_slots"])))
    w = 0.0
    for k in block:
        st = block[k]["00"]
        s += float(st["pop_k"]) * np.asarray(st["rates"], dtype=np.float64)
        w += float(st["pop_k"])
    s /= w
    out = {}
    for a, code in enumerate(d["activity_codes"]):
        x = s[a]
        nxt = np.roll(x, -1)
        starts = float(np.maximum(0.0, nxt - x).sum())
        c = np.where(x > 0, np.minimum(1.0, nxt / np.where(x > 0, x, 1.0)), 0.0)
        el = np.zeros(x.size)
        for b0 in range(x.size):  # 帯の数ぶん(96)× 32
            p, length = 1.0, 0.0
            for j in range(32):
                length += p
                p *= c[(b0 + j) % x.size]
            el[b0] = length
        out[code] = {"aggregate_mean_min": round(15.0 * x.sum() / starts, 1) if starts > 0 else None,
                     "prior_weighted_mean_min": round(15.0 * float((el * x).sum() / x.sum()), 1),
                     "median_c": round(float(np.median(c[x > x.max() * 0.01])), 3)}
    return out


def candidate_b() -> dict[str, dict[str, float]]:
    import openpyxl

    got = {}
    for tag, f in (("total", T41), ("rate", T43)):
        ws = openpyxl.load_workbook(f, read_only=True).worksheets[0]
        hdr = None
        for i, row in enumerate(ws.iter_rows(values_only=True)):
            if i == 6:
                hdr = [str(x) for x in row]
            if i < 9:
                continue
            k = [str(x) for x in row[:6]]
            if k[0] == "2_平日" and all(x == "0_総数" for x in k[1:5]) and k[5] == "00_総数":
                got[tag] = dict(zip(hdr[9:29], row[9:29]))
                break
    out = {}
    for j, col in enumerate(got["total"]):  # 02_睡眠 … 21_その他(表の番号=錨の符号 + 1・食事 04 を飛ばす)
        num = int(col.split("_")[0])
        code = f"{num - 1:02d}" if num <= 3 else (None if num == 4 else f"{num - 1:02d}")
        if code is None:
            continue
        t, r = float(got["total"][col]), float(got["rate"][col])
        out[code] = {"table_column": col, "total_mean_min": t, "doer_rate_pct": r,
                     "doer_mean_daily_min": round(t / r * 100.0, 1) if r > 0 else None}
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    a = candidate_a()
    b = candidate_b()
    rows = []
    for code, name in NAMES.items():
        ra, rb = a.get(code, {}), b.get(code, {})
        rows.append({"code": code, "name": name, **{f"a_{k}": v for k, v in ra.items()},
                     **{f"b_{k}": v for k, v in rb.items()},
                     "a_over_b": (round(ra["prior_weighted_mean_min"] / rb["doer_mean_daily_min"], 2)
                                  if rb.get("doer_mean_daily_min") else None)})
        print(code, name, ra.get("prior_weighted_mean_min"), ra.get("aggregate_mean_min"),
              rb.get("doer_mean_daily_min"), rows[-1]["a_over_b"])
    doc = {"schema": "shibuya.bench/wave2-2026-09-30/until-candidates/1",
           "a_source": "docs/bench/anchors/ssb2021_activity_prior_v0.json(平日・関東大都市圏・4 層の年齢総数を推定人口で加重)",
           "b_source": "令和3年社会生活基本調査 生活時間編 第4-1表・第4-3表(平日・全国・15 歳以上・総数の行)",
           "note": "(b) は 1 日 1 回と置いた上限。1 日の回数の表は手元に無い。実装していない",
           "rows": rows}
    Path(args.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
