"""空腹のエネルギー収支(D-118・5 段目 5a)の錨を **追跡ファイル**へ書き出す(決定論)。

入力: ``data/calib/hunger/*.json``(gitignore 下・取得役が MANIFEST つきで取得・親検収済)。
出力: ``docs/bench/anchors/hunger_energy_anchors_v0.json``(追跡)。**エンジンとテストはこの
追跡ファイルだけを読む**(``data/`` が無い機械でも動く=アジェンダ §1-9・第291)。

中身は **数値とコードだけ**(表の文言=活動名の和文・表題などは入れない)。各値に出典のセル/頁・
原 JSON と原ファイルの md5・出典表記(PDL1.0 / 政府標準利用規約 2.0 の記載例どおり「…を加工して
作成」)を添える。

同じ入力からは同じバイト列が出る(鍵の順序は固定・浮動小数は丸めを明示・時刻を書かない)。

使い方::

    python tools/hunger/build_hunger_anchors.py            # 生成して上書き
    python tools/hunger/build_hunger_anchors.py --check    # 生成物と追跡ファイルが一致するか(exit 1=不一致)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[2]
SRC_DIR = REPO / "data" / "calib" / "hunger"
OUT = REPO / "docs" / "bench" / "anchors" / "hunger_energy_anchors_v0.json"

SCHEMA = "shibuya.anchors/hunger-energy/v0"

#: 出典表記(親の発注文の文言どおり。URL は原 JSON の source.url)。
ATTRIBUTION_DRI = "「日本人の食事摂取基準(2025年版)」(厚生労働省)({url})を加工して作成"
ATTRIBUTION_NHNS = "「令和6年国民健康・栄養調査」(厚生労働省)・政府統計の総合窓口(e-Stat)を加工して作成"
ATTRIBUTION_SSB = "「令和3年社会生活基本調査結果」(総務省統計局)を加工して作成"
ATTRIBUTION_METS = "「改訂版『身体活動のメッツ(METs)表』」(国立研究開発法人医薬基盤・健康・栄養研究所)({url})"

#: 表3/表4 の年齢階級(食事摂取基準 2025・12 階級)。鍵=原 JSON の鍵(ASCII)。
DRI_CLASSES = ("1-2", "3-5", "6-7", "8-9", "10-11", "12-14", "15-17",
               "18-29", "30-49", "50-64", "65-74", "75+")
DRI_CLASS_LO = (1, 3, 6, 8, 10, 12, 15, 18, 30, 50, 65, 75)

#: 第14表の行(1〜25 歳は各歳・26-29・30-39・…・70 歳以上)。(原 JSON の鍵, 錨の鍵, 下端の歳)。
T14_ROWS = tuple([(f"{a}歳", str(a), a) for a in range(1, 26)] + [
    ("26-29歳", "26-29", 26), ("30-39歳", "30-39", 30), ("40-49歳", "40-49", 40),
    ("50-59歳", "50-59", 50), ("60-69歳", "60-69", 60), ("70歳以上", "70+", 70),
])

#: 第13表の年齢階級(20 歳以上・再掲 65-74/75+ は使わない)。
T13_CLASSES = (("20-29歳", "20-29", 20), ("30-39歳", "30-39", 30), ("40-49歳", "40-49", 40),
               ("50-59歳", "50-59", 50), ("60-69歳", "60-69", 60), ("70-79歳", "70-79", 70),
               ("80歳以上", "80+", 80))
T13_TOTAL = "総数"
MEALS = ("breakfast", "lunch", "dinner", "snack")

#: 第10表の年齢階級(再掲を除く)。
T10_CLASSES = (("総数", "total", -1), ("1-6歳", "1-6", 1), ("7-14歳", "7-14", 7),
               ("15-19歳", "15-19", 15), ("20-29歳", "20-29", 20), ("30-39歳", "30-39", 30),
               ("40-49歳", "40-49", 40), ("50-59歳", "50-59", 50), ("60-69歳", "60-69", 60),
               ("70歳以上", "70+", 70))

#: METs(改訂版メッツ表 2012)で使うコード(アジェンダ §1-9 の 6 本+速歩 17200=テストの 4.3)。
METS_CODES = ("07030", "07011", "07020", "17170", "17190", "17200", "11600")

#: 第18-1表の地域(原 JSON の鍵 → 錨の鍵)。
T18_REGIONS = (("全国", "national"), ("東京都", "tokyo"))
T18_ITEMS = ("getting_up", "breakfast_start", "dinner_start", "going_to_bed")

#: 15 分刻み 96 値の 3 本(錨の鍵, 原 JSON の表, 軸の値)。
RATE_SERIES = (
    ("t8_1_weekday_national_total", "8-1",
     {"曜日": "1_平日", "地域区分": "00_全国", "男女": "0_総数",
      "ふだんの就業状態": "0_総数", "年齢": "00_総数"}),
    ("t8_1_weekday_kanto_total", "8-1",
     {"曜日": "1_平日", "地域区分": "03_関東大都市圏(11都市圏)", "男女": "0_総数",
      "ふだんの就業状態": "0_総数", "年齢": "00_総数"}),
    ("t7_1_weekday_tokyo_total", "7-1",
     {"曜日": "1_平日", "地域区分": "13_東京都", "人口集中地区・人口集中地区以外": "0_総数",
      "男女": "0_総数"}),
)


def _md5(path: Path) -> str:
    return hashlib.md5(path.read_bytes()).hexdigest()


def _load(name: str) -> tuple[dict[str, Any], str]:
    p = SRC_DIR / name
    return json.loads(p.read_text(encoding="utf-8")), _md5(p)


def _r(x: float, nd: int = 6) -> float:
    return float(round(float(x), nd))


def _hm_to_min(hm: str) -> int:
    h, m = hm.split(":")
    return int(h) * 60 + int(m)


def _shares(b: float, lu: float, d: float, s: float) -> dict[str, float]:
    """朝昼夕=3 食で 1.0 に正規化・間=4 つの和に対する比(アジェンダ §1-3・第291)。"""
    three = b + lu + d
    four = three + s
    return {"breakfast": _r(b / three), "lunch": _r(lu / three), "dinner": _r(d / three),
            "snack_of_four": _r(s / four)}


def build() -> dict[str, Any]:
    bmr, bmr_md5 = _load("bmr_pal_2025.json")
    hw, hw_md5 = _load("nhns_r6_height_weight.json")
    mk, mk_md5 = _load("nhns_r6_meal_kcal.json")
    sk, sk_md5 = _load("nhns_r6_skip_breakfast.json")
    mets, mets_md5 = _load("mets_selected.json")
    ssb, ssb_md5 = _load("ssb2021_meal_rate_15min.json")

    # ---- 食事摂取基準 2025: 表3・表4・個人差 ----
    t3 = bmr["table3_bmr_reference"]["rows"]
    t4 = bmr["table4_pal"]["rows"]
    dri = {
        "age_classes": list(DRI_CLASSES),
        "age_lo": list(DRI_CLASS_LO),
        "bmr_per_kg_kcal": {sx: [t3[c][sx]["bmr_per_kg_kcal"] for c in DRI_CLASSES]
                            for sx in ("male", "female")},
        "ref_weight_kg": {sx: [t3[c][sx]["ref_weight_kg"] for c in DRI_CLASSES]
                          for sx in ("male", "female")},
        "bmr_ref_kcal_day": {sx: [t3[c][sx]["bmr_ref_kcal_day"] for c in DRI_CLASSES]
                             for sx in ("male", "female")},
        "pal_normal": [t4[c]["normal"] for c in DRI_CLASSES],
        "eer_sd_kcal_day": {
            "male": bmr["individual_difference"]["eer_sd_kcal_day"]["male_adult"],
            "female": bmr["individual_difference"]["eer_sd_kcal_day"]["female_adult"],
        },
        "_src": {
            "table3": {c: {k: t3[c]["_src"][k] for k in ("pdf_page", "printed_page", "y")}
                       for c in DRI_CLASSES},
            "table4": {c: {k: t4[c]["_src"][k] for k in ("pdf_page", "printed_page", "y")}
                       for c in DRI_CLASSES},
            "eer_sd": {k: bmr["individual_difference"]["_src"][k]
                       for k in ("pdf_page", "printed_page")},
        },
    }

    # ---- 国民健康・栄養調査 第14表: 体重 ----
    rows14 = hw["table14_height_weight"]["rows"]
    t14 = {
        "rows": [k for _, k, _ in T14_ROWS],
        "age_lo": [lo for _, _, lo in T14_ROWS],
        "weight_kg": {
            sx: {
                "n": [rows14[src][sx]["weight_kg"]["n"] for src, _, _ in T14_ROWS],
                "mean": [rows14[src][sx]["weight_kg"]["mean"] for src, _, _ in T14_ROWS],
                "sd": [rows14[src][sx]["weight_kg"]["sd"] for src, _, _ in T14_ROWS],
                "_cells": [rows14[src][sx]["weight_kg"]["_cells"] for src, _, _ in T14_ROWS],
            }
            for sx in ("male", "female")
        },
    }

    # ---- 国民健康・栄養調査 第13表: 朝昼夕間の平均(欠食者含む)と比 ----
    meals = mk["meals"]
    t13_mean: dict[str, dict[str, list[float]]] = {}
    t13_cells: dict[str, dict[str, list[str]]] = {}
    for sx in ("total", "male", "female"):
        t13_mean[sx] = {}
        t13_cells[sx] = {}
        for meal in MEALS:
            bs = meals[meal]["by_sex"][sx]
            t13_mean[sx][meal] = [bs[src]["mean_kcal"] for src, _, _ in T13_CLASSES]
            t13_cells[sx][meal] = [bs[src]["_cells"] for src, _, _ in T13_CLASSES]
    t13_total20 = {sx: {meal: meals[meal]["by_sex"][sx][T13_TOTAL]["mean_kcal"] for meal in MEALS}
                   for sx in ("total", "male", "female")}
    shares = {
        sx: {
            k: [
                _shares(*(t13_mean[sx][m][i] for m in MEALS))[k]
                for i in range(len(T13_CLASSES))
            ]
            for k in ("breakfast", "lunch", "dinner", "snack_of_four")
        }
        for sx in ("total", "male", "female")
    }
    shares_total20 = {sx: _shares(*(t13_total20[sx][m] for m in MEALS))
                      for sx in ("total", "male", "female")}
    t13 = {
        "age_classes": [k for _, k, _ in T13_CLASSES],
        "age_lo": [lo for _, _, lo in T13_CLASSES],
        "mean_kcal": t13_mean,
        "mean_kcal_20plus": t13_total20,
        "shares": shares,
        "shares_20plus": shares_total20,
        "_share_rule": "breakfast/lunch/dinner = meal / (breakfast+lunch+dinner); "
                       "snack_of_four = snack / (breakfast+lunch+dinner+snack)",
        "_cells": t13_cells,
        "_note": "means include skippers as 0 kcal (source note 2)",
    }

    # ---- 国民健康・栄養調査 第10表: 朝食の欠食率 ----
    sv = sk["breakfast_skip"]["values"]
    t10 = {
        "age_classes": [k for _, k, _ in T10_CLASSES],
        "pct": {sx: [sv[sx][src]["pct"] for src, _, _ in T10_CLASSES]
                for sx in ("total", "male", "female")},
        "n": {sx: [sv[sx][src]["n"] for src, _, _ in T10_CLASSES]
              for sx in ("total", "male", "female")},
        "denom_n": {sx: [sv[sx][src]["denom_n"] for src, _, _ in T10_CLASSES]
                    for sx in ("total", "male", "female")},
        "_cells": {sx: [sv[sx][src]["_cells"] for src, _, _ in T10_CLASSES]
                   for sx in ("total", "male", "female")},
    }

    # ---- METs(改訂版メッツ表 2012・コードと値だけ) ----
    by_code = {r["code"]: r for r in mets["rows"]}
    mets_out = {
        "mets": {c: by_code[c]["mets"] for c in METS_CODES},
        "estimated_italic": {c: bool(by_code[c]["estimated_mets_italic"]) for c in METS_CODES},
        "_src": {c: {"pdf_page": by_code[c]["pdf_page"], "printed_page": by_code[c]["printed_page"],
                     "row_on_page": by_code[c]["row_on_page"]} for c in METS_CODES},
    }

    # ---- 社会生活基本調査 第18-1表(平日・15 歳以上・平均時刻) ----
    t18 = ssb["main_table_18-1"]
    t18_out: dict[str, Any] = {}
    for src, key in T18_REGIONS:
        row = t18["rows"][src]
        t18_out[key] = {
            it: {"rate_pct": row[it]["rate_pct"], "mean_time": row[it]["mean_time"],
                 "mean_min": _hm_to_min(row[it]["mean_time"])}
            for it in T18_ITEMS
        }
        t18_out[key]["_cells"] = row["_cells"]
        t18_out[key]["sample_size"] = row["sample_size"]

    # ---- 社会生活基本調査 時間帯編: 食事の行動者率 15 分 96 値 ×3 ----
    rates: dict[str, Any] = {}
    for key, tb, axes in RATE_SERIES:
        hit = [r for r in ssb["tables"][tb]["rows"] if all(r.get(k) == v for k, v in axes.items())]
        if len(hit) != 1:
            raise SystemExit(f"{key}: 行が 1 本に決まらない({len(hit)})")
        r = hit[0]
        if len(r["rate_pct"]) != 96:
            raise SystemExit(f"{key}: 96 値でない")
        rates[key] = {
            "table": tb,
            "statInfId": ssb["tables"][tb]["statInfId"],
            "xlsx_row": r["xlsx_row"],
            "rate_pct": r["rate_pct"],
            "symbols": r.get("symbols", {}),
            "stratum_sample_size": r["stratum_sample_size"],
        }
    tokyo = rates["t7_1_weekday_tokyo_total"]["rate_pct"]
    vals = [(-1.0 if x is None else float(x)) for x in tokyo]
    peak = max(range(96), key=lambda i: (vals[i], -i))
    lunch_default = {
        "series": "t7_1_weekday_tokyo_total",
        "rule": "argmax over the 96 slots (earliest on ties); start of that slot",
        "slot_index": peak,
        "start_min": peak * 15,
        "rate_pct": tokyo[peak],
    }

    sources = {
        "bmr_pal_2025.json": {"json_md5": bmr_md5, "source_md5": bmr["source"]["md5"],
                              "url": bmr["source"]["url"]},
        "nhns_r6_height_weight.json": {"json_md5": hw_md5,
                                       "source_md5": [s["md5"] for s in hw["source"]],
                                       "url": [s["url"] for s in hw["source"]]},
        "nhns_r6_meal_kcal.json": {"json_md5": mk_md5, "source_md5": mk["source"]["md5"],
                                   "url": mk["source"]["url"]},
        "nhns_r6_skip_breakfast.json": {"json_md5": sk_md5, "source_md5": sk["source"]["md5"],
                                        "url": sk["source"]["url"]},
        "mets_selected.json": {"json_md5": mets_md5, "source_md5": mets["source"]["md5"],
                               "url": mets["source"]["url"]},
        "ssb2021_meal_rate_15min.json": {
            "json_md5": ssb_md5,
            "source_md5": {**{tb: ssb["tables"][tb]["md5"] for tb in ("8-1", "7-1")},
                           "18-1": t18["md5"]},
            "url": {**{tb: ssb["tables"][tb]["url"] for tb in ("8-1", "7-1")}, "18-1": t18["url"]},
        },
    }
    return {
        "schema": SCHEMA,
        "generated_by": "tools/hunger/build_hunger_anchors.py",
        "attribution": [
            ATTRIBUTION_DRI.format(url=bmr["source"]["url"]),
            ATTRIBUTION_NHNS,
            ATTRIBUTION_SSB,
            ATTRIBUTION_METS.format(url=mets["source"]["url"]),
        ],
        "usage": "D-118 5a: constants of the energy balance (DRI table 3/4, individual SD, "
                 "NHNS table 14/13, METs) and validation-only anchors (NHNS table 10, "
                 "SSB table 18-1, 15-min meal rates) that are never used for calibration (K6 (i))",
        "sources": sources,
        "dri2025": dri,
        "nhns_t14_weight": t14,
        "nhns_t13_meal_kcal": t13,
        "nhns_t10_breakfast_skip": t10,
        "mets_2012": mets_out,
        "ssb2021_t18_1_weekday": t18_out,
        "ssb2021_meal_rate_15min": {"slot_minutes": 15, "series": rates},
        "derived": {"lunch_default": lunch_default},
    }


def dumps(obj: dict[str, Any]) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=1, sort_keys=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="D-118 5a の錨を追跡ファイルへ書く")
    ap.add_argument("--check", action="store_true", help="追跡ファイルと一致するかだけ見る")
    args = ap.parse_args(argv)
    text = dumps(build())
    if args.check:
        cur = OUT.read_text(encoding="utf-8") if OUT.exists() else ""
        if cur != text:
            print("不一致: 追跡ファイルは再生成が要る")
            return 1
        print("一致")
        return 0
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(text.encode("utf-8"))
    print(f"書いた: {OUT.relative_to(REPO).as_posix()} ({len(text.encode('utf-8')):,} B)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
