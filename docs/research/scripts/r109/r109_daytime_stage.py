"""R-109 A9 (i): 東京都「令和2年国勢調査による東京都の昼間人口」第11表(町丁・字等別昼間人口(推計))を、
W16 の町丁目の被覆率で舞台へ按分する。読むだけ。

入力: data/research_cache/tokyo_tj20zv1100_chocho_daytime.csv(既存答申 d66 §4 が取得済み)
      data/world/v2/w16_chome.parquet(被覆率)
出力: data/research_cache/r109/r109_daytime_stage.json
実行: python docs/research/scripts/r109/r109_daytime_stage.py
注意: 被覆率は面積の割合。昼間人口が町丁目の中で均一でないので、按分は粗い(推測の幅)。
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]
CSV = ROOT / "data/research_cache/tokyo_tj20zv1100_chocho_daytime.csv"
OUT = ROOT / "data/research_cache/r109/r109_daytime_stage.json"
KANJI = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6"}
ZEN = str.maketrans("０１２３４５６７８９", "0123456789")
AREA13 = {"渋谷1丁目", "渋谷2丁目", "渋谷3丁目", "渋谷4丁目", "道玄坂1丁目", "道玄坂2丁目", "宇田川町",
          "神南1丁目", "神南2丁目", "桜丘町", "南平台町", "円山町", "神泉町"}


def norm(s: str) -> str:
    s = str(s).strip().translate(ZEN).replace("松涛", "松濤").replace("ケ谷", "ヶ谷").replace("鶯", "鴬")
    return re.sub("([一二三四五六])丁目", lambda m: KANJI[m.group(1)] + "丁目", s)


def num(v: str) -> float:
    v = v.strip().replace(",", "")
    try:
        return float(v)
    except ValueError:
        return 0.0


def main() -> None:
    rows = list(csv.reader(CSV.read_text(encoding="utf-8-sig").splitlines()))
    hdr = rows[0]
    i_name = len(hdr) - 6  # 末尾 6 列 = 名称(階層なし)・昼間人口・面積・密度・常住人口・昼夜間比率
    day = {}
    for r in rows[1:]:
        if len(r) < len(hdr) or r[2] != "113":
            continue
        name = norm(r[i_name])
        day[name] = {"day": num(r[i_name + 1]), "night": num(r[i_name + 4]), "area_km2": num(r[i_name + 2])}
    ch = pq.read_table(ROOT / "data/world/v2/w16_chome.parquet").to_pylist()
    out_rows = []
    miss = []
    for c in ch:
        if c["coverage"] <= 0:
            continue
        n = norm(c["s_name"])
        d = day.get(n)
        if d is None:
            miss.append(n)
            continue
        out_rows.append({"chome": n, "coverage": round(c["coverage"], 4), "daytime": d["day"],
                         "night": d["night"], "in_area13": n in AREA13})
    res = {
        "ward_row": day.get("渋谷区"),
        "unmatched": miss,
        "stage_daytime_x_cov": round(sum(r["daytime"] * r["coverage"] for r in out_rows)),
        "stage_night_x_cov": round(sum(r["night"] * r["coverage"] for r in out_rows)),
        "area13_daytime_full": round(sum(r["daytime"] for r in out_rows if r["in_area13"])),
        "outside13_daytime_x_cov": round(sum(r["daytime"] * r["coverage"] for r in out_rows if not r["in_area13"])),
        "rows": sorted(out_rows, key=lambda r: -r["daytime"] * r["coverage"]),
    }
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for k in ("ward_row", "unmatched", "stage_daytime_x_cov", "stage_night_x_cov", "area13_daytime_full",
              "outside13_daytime_x_cov"):
        print(k, res[k])


if __name__ == "__main__":
    main()
