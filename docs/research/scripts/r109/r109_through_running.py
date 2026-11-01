"""R-109 A9 (iii): 第13回大都市交通センサス(2021・COVID 下)の「初乗り・最終降車駅間移動人員」(首都圏)から、
渋谷で降りずに直通運転の電車で通り過ぎる人(田園都市線⇄半蔵門線・東横線⇄副都心線)の数の幅を推計する。読むだけ。

入力: data/realworld/transport_census/raw/station_od13_13.xlsx(既存資産・e-Stat statInfId 000040443413)
出力: data/research_cache/r109/r109_through_running.json
実行: python docs/research/scripts/r109/r109_through_running.py

推測の置き方(親が確かめる点):
- 駅の路線は駅名で決める(下の表)。出発駅が片方の路線の駅、到着駅が相手の路線の駅(渋谷を除く)の OD を、
  渋谷を電車に乗ったまま通る人とみなす。乗り換えの別経路(JR 経由など)を取る人も入るので上限側に寄る。
- 下限 = 相手側の駅を「その路線にしかない駅」に絞る。上限 = 共用の大きな駅(池袋・大手町など)と直通先の他社線の駅を足す。
- 一件明細調査の人員の単位(1 日あたり・定期と普通の別)は表の注記に従う(本スクリプトは表の値をそのまま足す)。
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[4]
SRC = ROOT / "data/realworld/transport_census/raw/station_od13_13.xlsx"
OUT = ROOT / "data/research_cache/r109/r109_through_running.json"

DENTOSHI = ["池尻大橋", "三軒茶屋", "駒沢大学", "桜新町", "用賀", "二子玉川", "二子新地", "高津", "溝の口",
            "梶が谷", "宮崎台", "宮前平", "鷺沼", "たまプラーザ", "あざみ野", "江田", "市が尾", "藤が丘",
            "青葉台", "田奈", "長津田", "つくし野", "すずかけ台", "南町田グランベリーパーク", "南町田",
            "つきみ野", "中央林間"]
TOYOKO = ["代官山", "中目黒", "祐天寺", "学芸大学", "都立大学", "自由が丘", "田園調布", "多摩川", "新丸子",
          "武蔵小杉", "元住吉", "日吉", "綱島", "大倉山", "菊名", "妙蓮寺", "白楽", "東白楽", "反町", "横浜"]
MINATOMIRAI = ["新高島", "みなとみらい", "馬車道", "日本大通り", "元町・中華街"]
# 半蔵門線: 下限=半蔵門線だけの駅、上限=他線と共用の駅も足す
HANZO_ONLY = ["半蔵門", "水天宮前"]
HANZO_SHARED = ["表参道", "青山一丁目", "永田町", "九段下", "神保町", "大手町", "三越前", "清澄白河", "住吉",
                "錦糸町", "押上"]
FUKU_ONLY = ["北参道", "東新宿", "西早稲田", "雑司が谷"]
FUKU_SHARED = ["明治神宮前", "新宿三丁目", "池袋", "要町", "千川", "小竹向原", "氷川台", "平和台",
               "地下鉄赤塚", "地下鉄成増", "和光市"]


def split(name: str) -> tuple[str, str]:
    s = str(name)
    i = s.rfind(" ")
    return (s[:i], s[i + 1:]) if i > 0 else ("", s)


def main() -> None:
    wb = openpyxl.load_workbook(SRC, read_only=True)
    ws = wb["首都圏"]
    tok_dt = set(DENTOSHI)
    tok_ty = set(TOYOKO)
    acc = defaultdict(float)
    n = 0
    for r in ws.iter_rows(min_row=3, values_only=True):
        if not r or r[2] is None or not isinstance(r[2], (int, float)):
            continue
        n += 1
        (fo, fs), (to, ts), v = split(r[0]), split(r[1]), float(r[2])
        # 田園都市線 ⇄ 半蔵門線
        if fo == "東急電鉄" and fs in tok_dt and to == "東京地下鉄":
            if ts in HANZO_ONLY:
                acc["dt_to_hz_only"] += v
            if ts in HANZO_ONLY or ts in HANZO_SHARED:
                acc["dt_to_hz_all"] += v
        if to == "東急電鉄" and ts in tok_dt and fo == "東京地下鉄":
            if fs in HANZO_ONLY:
                acc["hz_only_to_dt"] += v
            if fs in HANZO_ONLY or fs in HANZO_SHARED:
                acc["hz_all_to_dt"] += v
        if fo == "東急電鉄" and fs in tok_dt and to == "東武鉄道":
            acc["dt_to_tobu"] += v
        if to == "東急電鉄" and ts in tok_dt and fo == "東武鉄道":
            acc["tobu_to_dt"] += v
        # 東横線(+みなとみらい線)⇄ 副都心線
        f_ty = (fo == "東急電鉄" and fs in tok_ty) or (fo == "横浜高速鉄道" and fs in MINATOMIRAI)
        t_ty = (to == "東急電鉄" and ts in tok_ty) or (to == "横浜高速鉄道" and ts in MINATOMIRAI)
        if f_ty and to == "東京地下鉄":
            if ts in FUKU_ONLY:
                acc["ty_to_fk_only"] += v
            if ts in FUKU_ONLY or ts in FUKU_SHARED:
                acc["ty_to_fk_all"] += v
        if t_ty and fo == "東京地下鉄":
            if fs in FUKU_ONLY:
                acc["fk_only_to_ty"] += v
            if fs in FUKU_ONLY or fs in FUKU_SHARED:
                acc["fk_all_to_ty"] += v
        if f_ty and to in ("西武鉄道", "東武鉄道"):
            acc["ty_to_seibu_tobu"] += v
        if t_ty and fo in ("西武鉄道", "東武鉄道"):
            acc["seibu_tobu_to_ty"] += v
    lo = acc["dt_to_hz_only"] + acc["hz_only_to_dt"] + acc["ty_to_fk_only"] + acc["fk_only_to_ty"]
    hi = (acc["dt_to_hz_all"] + acc["hz_all_to_dt"] + acc["dt_to_tobu"] + acc["tobu_to_dt"]
          + acc["ty_to_fk_all"] + acc["fk_all_to_ty"] + acc["ty_to_seibu_tobu"] + acc["seibu_tobu_to_ty"])
    res = {"n_rows": n, "parts": {k: round(v) for k, v in acc.items()}, "lower": round(lo), "upper": round(hi),
           "note": "2021 年度(COVID 下)。表の値を足しただけ。経路の当てはめは推測。"}
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()
