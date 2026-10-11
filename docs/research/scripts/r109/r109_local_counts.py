"""R-109 A9: 手元の資産と公開集計から、舞台(W2 の GL 453 セル)の人数の目安を集計する。読むだけ。

入力(すべて既存・変えない):
  data/world/v2/w16_chome.parquet        町丁目 80 行の被覆率(W16 の出力)
  data/world/v2/w16_population.parquet   体の kind・synthetic
  data/realworld/census_r3/raw/ka21_dai.xlsx  経済センサス R3 第28表(町丁目 × 大分類・民営)
  data/realworld/pt_tokyo/H30_zonecode.xlsx   PT 2018 のゾーン表
  data/calib/pt2018/pt6_b-4.csv・pt6_c-2.csv   PT 2018 の基礎集計(e-Stat)
  data/realworld/transport_census/station_flow_12.json  第12回大都市交通センサス 表3(渋谷の行)
出力: data/research_cache/r109/r109_local_counts.json
実行: システムの python(openpyxl・pyarrow が要る)
    python docs/research/scripts/r109/r109_local_counts.py
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from pathlib import Path

import openpyxl
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "data" / "research_cache" / "r109" / "r109_local_counts.json"

KANJI = {"一": "1", "二": "2", "三": "3", "四": "4", "五": "5", "六": "6", "七": "7"}
ZEN = str.maketrans("０１２３４５６７８９", "0123456789")


def norm(name: str) -> str:
    s = str(name).strip().translate(ZEN)
    s = s.replace("松涛", "松濤").replace("ケ谷", "ヶ谷").replace("鶯谷", "鴬谷")
    s = re.sub("([一二三四五六七])丁目", lambda m: KANJI[m.group(1)] + "丁目", s)
    return s


def census_employees() -> dict[str, dict]:
    wb = openpyxl.load_workbook(ROOT / "data/realworld/census_r3/raw/ka21_dai.xlsx", read_only=True)
    ws = wb[wb.sheetnames[0]]
    rows = list(ws.iter_rows(values_only=True))
    out: dict[str, dict] = {}
    town = None
    town_has_child: dict[str, bool] = {}
    seen = set()
    for r in rows[6:]:
        if r[0] == "渋谷区":
            continue
        if r[1]:
            town = norm(r[1])
            key = ("town", town)
            if key in seen:
                continue
            seen.add(key)
            out.setdefault(town, {"est": r[3], "emp": r[4], "leaf": True})
        elif r[2]:
            ch = norm(r[2])
            if ("ch", ch) in seen:
                continue
            seen.add(("ch", ch))
            out[ch] = {"est": r[3], "emp": r[4], "leaf": True, "town": town}
            town_has_child[town] = True
    for t in town_has_child:
        if t in out:
            out[t]["leaf"] = False
    return out


def main() -> None:
    res: dict = {}
    # ---- 町丁目の被覆率 × 夜間人口 × 従業者 --------------------------------
    ch = pq.read_table(ROOT / "data/world/v2/w16_chome.parquet").to_pylist()
    emp = census_employees()
    area13 = ["渋谷1丁目", "渋谷2丁目", "渋谷3丁目", "渋谷4丁目", "道玄坂1丁目", "道玄坂2丁目",
              "宇田川町", "神南1丁目", "神南2丁目", "桜丘町", "南平台町", "円山町", "神泉町"]
    rows = []
    miss = []
    for r in ch:
        n = norm(r["s_name"])
        e = emp.get(n)
        if e is None or not e["leaf"]:
            if r["coverage"] > 0:
                miss.append(n)
            e_emp = None
        else:
            e_emp = e["emp"] if isinstance(e["emp"], (int, float)) else None
        rows.append({"chome": n, "coverage": round(r["coverage"], 4), "jinko": r["jinko"],
                     "employees_2021": e_emp, "in_area13": n in area13})
    cov = [x for x in rows if x["coverage"] > 0]
    res["chome_rows_covered"] = sorted(cov, key=lambda x: -x["coverage"])
    res["chome_unmatched"] = miss
    res["sum_jinko_x_cov"] = round(sum(x["jinko"] * x["coverage"] for x in cov), 1)
    res["sum_emp_area13_full"] = sum(x["employees_2021"] or 0 for x in rows if x["in_area13"])
    res["sum_emp_area13_x_cov"] = round(sum((x["employees_2021"] or 0) * x["coverage"] for x in rows if x["in_area13"]), 1)
    res["sum_emp_all42_x_cov"] = round(sum((x["employees_2021"] or 0) * x["coverage"] for x in cov), 1)
    res["sum_emp_outside13_x_cov"] = round(sum((x["employees_2021"] or 0) * x["coverage"] for x in cov if not x["in_area13"]), 1)
    res["ward_employees_2021"] = 581127
    # ---- PT ゾーン ⇄ 町丁目 ---------------------------------------------------
    wb = openpyxl.load_workbook(ROOT / "data/realworld/pt_tokyo/H30_zonecode.xlsx", read_only=True)
    zone_chome: dict[str, list[str]] = defaultdict(list)
    big_names: dict[str, set] = defaultdict(set)
    for sn in wb.sheetnames[1:]:
        for r in wb[sn].iter_rows(values_only=True):
            if r[0] and isinstance(r[0], str) and r[0].isdigit() and r[4]:
                big_names[r[0]].add(str(r[4]))
                if r[0] == "02" and r[1] == "4":
                    z = "024" + str(r[2])
                    for c in str(r[5]).split("、"):
                        zone_chome[z].append(norm(c))
    res["pt_zone_chome"] = zone_chome
    res["pt_bigzone_names"] = {k: sorted(v) for k, v in sorted(big_names.items())}
    by = {x["chome"]: x for x in rows}
    zshare = {}
    for z, lst in zone_chome.items():
        j = sum(by[c]["jinko"] for c in lst if c in by)
        jc = sum(by[c]["jinko"] * by[c]["coverage"] for c in lst if c in by)
        e = sum((by[c]["employees_2021"] or 0) for c in lst if c in by)
        ec = sum((by[c]["employees_2021"] or 0) * by[c]["coverage"] for c in lst if c in by)
        zshare[z] = {"jinko": j, "jinko_in_stage": round(jc), "emp": e, "emp_in_stage": round(ec),
                     "share_jinko": round(jc / j, 4) if j else None,
                     "share_emp": round(ec / e, 4) if e else None,
                     "missing": [c for c in lst if c not in by]}
    res["pt_zone_stage_share"] = zshare
    # ---- PT b-4(時刻別滞留人口)と c-2(着の目的別)-----------------------
    def read_csv(p):
        raw = (ROOT / p).read_bytes().decode("cp932")
        return list(csv.reader(raw.splitlines()))
    b4 = read_csv("data/calib/pt2018/pt6_b-4.csv")
    hdr = b4[3]
    b4z = {}
    for r in b4:
        if r and r[0].strip() in (":0240", ":0241", ":0242", ":0243"):
            b4z[r[0].strip()[1:]] = {hdr[j]: float(r[j].replace(",", "")) for j in range(1, len(r)) if r[j].strip()}
    res["pt_b4_header"] = hdr[1:]
    res["pt_b4"] = b4z
    c2 = read_csv("data/calib/pt2018/pt6_c-2.csv")
    res["pt_c2_header_rows"] = c2[:5]
    c2z = defaultdict(dict)
    for r in c2:
        if r and r[0].strip() in (":0240", ":0241", ":0242", ":0243") and r[1].strip() == "合計":
            c2z[r[0].strip()[1:]] = r
    res["pt_c2_total_rows"] = c2z
    # ---- W16 の体の内訳 ---------------------------------------------------------
    t = pq.read_table(ROOT / "data/world/v2/w16_population.parquet", columns=["kind", "synthetic", "pool_layer"])
    k = t.column("kind").to_pylist()
    s = t.column("synthetic").to_pylist()
    cnt = defaultdict(lambda: [0, 0])
    for a, b in zip(k, s):
        cnt[a][0] += 1
        cnt[a][1] += int(b)
    res["w16_kind_n_synthetic"] = {str(a): v for a, v in sorted(cnt.items())}
    # ---- 大都市交通センサス 2015: 渋谷で降りずに乗ったまま通る人(JR)------------
    sf = json.loads((ROOT / "data/realworld/transport_census/station_flow_12.json").read_text(encoding="utf-8"))["data"]
    f = defaultdict(dict)
    for r in sf:
        if r["ticket"].startswith("合計"):
            f[(r["line"], r["direction"])][r["measure"]] = r["value"]
    # 表3 の「通過」= その駅と下り側の隣の駅の間の区間の人数(東京駅・新橋駅の行で確認)。
    # 下り: 通過 = 出ていく区間 → 乗ったまま = 通過 − 乗車。上り: 通過 = 入ってくる区間 → 乗ったまま = 通過 − 降車。
    stay = {}
    for (line, d), v in f.items():
        if d == "下り":
            stay[f"{line}/{d}"] = v["通過"] - v["乗車"]
        else:
            stay[f"{line}/{d}"] = v["通過"] - v["降車"]
    res["census12_onboard_through"] = stay
    res["census12_onboard_through_jr_total"] = sum(v for k2, v in stay.items() if k2.split("/")[0] in ("山手線", "埼京線", "湘南新宿ライン"))
    res["census12_board_alight"] = {f"{a}/{b}": v for (a, b), v in f.items()}
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for kk in ("chome_unmatched", "sum_jinko_x_cov", "sum_emp_area13_full", "sum_emp_area13_x_cov",
               "sum_emp_all42_x_cov", "sum_emp_outside13_x_cov", "pt_zone_stage_share",
               "census12_onboard_through", "census12_onboard_through_jr_total", "w16_kind_n_synthetic"):
        print(kk, json.dumps(res[kk], ensure_ascii=False))


if __name__ == "__main__":
    main()


def stage_presence_from_pt() -> dict:
    """PT b-4(ゾーン別時刻別滞留人口)を舞台へ按分した幅(下=夜間人口の割合・上=従業者の割合)。推測の按分。"""
    d = json.loads(OUT.read_text(encoding="utf-8"))
    sh = d["pt_zone_stage_share"]
    hours = d["pt_b4_header"]
    lo, hi = {}, {}
    for h in hours:
        a = b = 0.0
        for z, v in d["pt_b4"].items():
            a += v.get(h, 0) * min(sh[z]["share_jinko"], sh[z]["share_emp"])
            b += v.get(h, 0) * max(sh[z]["share_jinko"], sh[z]["share_emp"])
        lo[h], hi[h] = round(a), round(b)
    c2 = d["pt_c2_total_rows"]
    purposes = ["自宅－勤務", "自宅－通学", "自宅－業務", "自宅－私事", "帰宅", "勤務・業務", "私事", "不明", "計"]
    arr = {}
    for z, r in c2.items():
        vals = [float(x.replace(",", "")) for x in r[11:20]]
        arr[z] = dict(zip(purposes, vals))
    arr_lo = {p: round(sum(arr[z][p] * min(sh[z]["share_jinko"], sh[z]["share_emp"]) for z in arr)) for p in purposes}
    arr_hi = {p: round(sum(arr[z][p] * max(sh[z]["share_jinko"], sh[z]["share_emp"]) for z in arr)) for p in purposes}
    return {"b4_stage_lo": lo, "b4_stage_hi": hi, "c2_arrive_by_zone": arr,
            "c2_arrive_stage_lo": arr_lo, "c2_arrive_stage_hi": arr_hi}


if __name__ == "__main__" and True:
    extra = stage_presence_from_pt()
    d0 = json.loads(OUT.read_text(encoding="utf-8"))
    d0.update(extra)
    OUT.write_text(json.dumps(d0, ensure_ascii=False, indent=1), encoding="utf-8")
    print("b4_stage_lo", extra["b4_stage_lo"])
    print("b4_stage_hi", extra["b4_stage_hi"])
    print("c2_arrive_stage_lo", extra["c2_arrive_stage_lo"])
    print("c2_arrive_stage_hi", extra["c2_arrive_stage_hi"])
