"""社会生活基本調査 R3 調査票B 第1-7表(statInfId 000032261363)から、平日・男女総数・健康状態総数・年齢総数の
行動の種類別 総平均時間(主行動・10 歳以上・全国)を取り出して JSON にする。R-86。

使い方: python ssb_b_weekday.py <xlsx> <出力 json>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from xlsx_min import read_rows  # noqa: E402


def main(src: str, dst: str) -> None:
    rows = read_rows(src)
    head = rows[6]
    out = {"source": "e-Stat statInfId=000032261363 第1-7表 総平均時間(主行動)10歳以上 全国", "unit": "分/日",
           "filter": "曜日=平日・男女=総数・健康状態=総数・年齢=総数", "items": []}
    days = set()
    for r in rows[9:]:
        if len(r) < 5 or r[0] is None:
            continue
        days.add(r[0])
        if str(r[0]).endswith("平日") and r[1] == "0_総数" and r[2] == "0_総数" and r[3] == "00_総数":
            for j in range(5, len(r)):
                name = head[j] if j < len(head) else None
                if name is None:
                    continue
                v = r[j]
                code, _, label = name.partition("_")
                level = {1: "大", 2: "中", 3: "小", 4: "小"}.get(len(code), "?")
                if code == "0":
                    level = "総"
                out["items"].append({"code": code, "name": label, "level": level, "minutes": v})
            out["population_10k"] = r[4]
            break
    out["days_seen"] = sorted(days)
    lv = {}
    for it in out["items"]:
        lv[it["level"]] = lv.get(it["level"], 0) + 1
    out["counts_by_level"] = lv
    Path(dst).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(lv, out.get("population_10k"), out["days_seen"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
