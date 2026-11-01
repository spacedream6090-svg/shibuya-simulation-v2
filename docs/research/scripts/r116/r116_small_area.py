"""R-116 段 0「材料」: 令和2年国勢調査 小地域集計(東京都)の渋谷区の行を読み、
区の合計と「舞台」(W16 の町丁目の被覆率で按分)の合計を表ごとに出す(読むだけ)。

入力(すべて構築側=パターン台帳 §10 に無い表):
- data/research_cache/r116/census2020_sa_*.csv(e-Stat・cp932)
- data/world/v2/w16_chome.parquet(町丁目の被覆率=W16 の expedient W16#1/#2 と同じ按分)
出力: docs/research/scripts/r116/r116_small_area.json(区の合計・舞台の按分・秘匿の数)

使い方: .venv の python で `python docs/research/scripts/r116/r116_small_area.py`
(標準ライブラリ+pyarrow。値は書き換えない・資産は変えない)
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]
CACHE = ROOT / "data" / "research_cache" / "r116"
OUT = Path(__file__).with_suffix(".json")
WARD = "13113"


def md5(p: Path) -> str:
    h = hashlib.md5()
    with p.open("rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def num(s: str):
    s = s.strip()
    if s in ("-", ""):
        return 0
    if s == "X":
        return None  # 秘匿
    try:
        return int(s)
    except ValueError:
        try:
            return float(s)
        except ValueError:
            return s


def load_cov() -> dict[str, float]:
    t = pq.read_table(ROOT / "data" / "world" / "v2" / "w16_chome.parquet").to_pylist()
    return {r["key_code"]: float(r["coverage"]) for r in t}


def read_table(p: Path, cov: dict[str, float]) -> dict:
    with p.open(encoding="cp932", newline="") as f:
        rows = list(csv.reader(f))
    title = rows[1][1] if len(rows) > 1 and len(rows[1]) > 1 else ""
    hi = next(i for i, r in enumerate(rows) if "市区町村コード" in r)
    head = rows[hi]
    group = rows[hi - 1]  # 表章項目(列の上の段)
    c_city = head.index("市区町村コード")
    c_code = head.index("町丁字コード")
    c_lvl = head.index("地域階層レベル")
    c_hide = head.index("秘匿処理")
    c_sum = head.index("合算地域")
    c_town = head.index("大字・町名")
    c_chome = head.index("字・丁目名")
    # 行の次元(男女・世帯員の年齢による世帯の種類 など)は「総数」の行だけを使う
    c_sex = c_city - 1 if c_city >= 2 and head[c_city - 1] else None
    vcols = list(range(c_chome + 1, len(head)))
    labels = [(group[j] + "/" if group[j] else "") + head[j] for j in vcols]

    ward_total = None
    leaves = []
    for r in rows[hi + 1:]:
        if len(r) <= c_chome or r[c_city] != WARD:
            continue
        if c_sex is not None and r[c_sex] != "総数":
            continue
        vals = [num(r[j]) for j in vcols]
        if r[c_lvl] == "1":
            ward_total = vals
            continue
        key = WARD + r[c_code]
        if key in cov:  # 葉(町丁目)=W16 の鍵と同じ形
            leaves.append({"key": key, "name": r[c_town] + r[c_chome], "lvl": r[c_lvl],
                           "hidden": r[c_hide], "merged": r[c_sum], "vals": vals})
    stage = [0.0] * len(vcols)
    x_cov = []
    for lf in leaves:
        w = cov.get(lf["key"], 0.0)
        if w <= 0:
            continue
        if all(v is None for v in lf["vals"]):
            x_cov.append((lf["name"], round(w, 4)))
            continue
        for k, v in enumerate(lf["vals"]):
            if isinstance(v, (int, float)):
                stage[k] += w * v
    n_x = sum(1 for lf in leaves if all(v is None for v in lf["vals"]))
    n_xcell = sum(1 for lf in leaves for v in lf["vals"] if v is None)
    return {
        "file": p.name,
        "md5": md5(p),
        "title": title,
        "columns": labels,
        "ward_total": dict(zip(labels, ward_total)) if ward_total else None,
        "stage_by_coverage": {lab: round(v, 1) for lab, v in zip(labels, stage)},
        "n_leaf_units": len(leaves),
        "n_leaf_all_hidden": n_x,
        "n_hidden_cells": n_xcell,
        "hidden_units_in_stage": x_cov,
        "secret_marked_units": [lf["name"] for lf in leaves if lf["hidden"]],
        "merged_units": [(lf["name"], lf["merged"]) for lf in leaves if lf["merged"]],
    }


def main() -> int:
    cov = load_cov()
    out = {"note": "令和2年国勢調査 小地域集計(東京都)の渋谷区。stage_by_coverage は W16 の町丁目の"
                   "被覆率(面積の割合)で按分した舞台の値(推測の按分・秘匿の町丁目は 0 として足していない)。",
           "n_chome_with_coverage": sum(1 for v in cov.values() if v > 0),
           "tables": []}
    for p in sorted(CACHE.glob("census2020_sa_*.csv")):
        out["tables"].append(read_table(p, cov))
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    for t in out["tables"]:
        print(t["file"], t["md5"], "| leaves", t["n_leaf_units"], "| all-X", t["n_leaf_all_hidden"],
              "| X cells", t["n_hidden_cells"], "| X in stage", t["hidden_units_in_stage"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
