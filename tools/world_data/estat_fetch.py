#!/usr/bin/env python3
"""estat_fetch — e-Stat API(getStatsData)を **ページング付き** で取得し、
data/realworld/estat/ の既存 JSON と同じ形 {"meta","classes","values"} で保存する(親レーン用)。

CLAUDE.md §7 の公的ドメイン例外(e-stat.go.jp)に基づく読み取り取得。APIキーは環境変数 ESTAT_APP_ID のみ。
既存の 09-07 取得分は 1 応答(値 1,500 件)で切れており、年齢 5 歳階級の 70-74・75 歳以上・男女別(cat01 0160-0600)が
欠けていた(W16 の年齢 raking が 14 階級止まり=サブ J の親判断待ち 3)。本ツールは startPosition で全件を取る。

使い方::

    python tools/world_data/estat_fetch.py --stats-data-id 8003006792 \
        --area-from 131130000 --area-to 131139999 --area-extra 13113 \
        --out data/realworld/estat/国勢調査2020_小地域_年齢5歳階級男女別人口_東京都_渋谷区_全階級.json

逐次ループ宣言(P4): API ページング(limit 100,000)。構築段階ではない。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import time
import urllib.parse
import urllib.request

API = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsData"


def _get(params: dict) -> dict:
    url = API + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=120) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_all(app_id: str, stats_data_id: str, extra: dict) -> tuple[dict, list[dict], dict]:
    values: list[dict] = []
    classes: dict = {}
    table_inf: dict = {}
    start = 1
    while True:
        params = {"appId": app_id, "statsDataId": stats_data_id, "limit": 100000, "startPosition": start,
                  "metaGetFlg": "Y", "cntGetFlg": "N", "sectionHeaderFlg": "1", **extra}
        d = _get(params)
        g = d["GET_STATS_DATA"]
        res = g["RESULT"]
        if int(res.get("STATUS", -1)) != 0:
            raise RuntimeError(f"e-Stat API error: {res}")
        sd = g["STATISTICAL_DATA"]
        table_inf = sd.get("TABLE_INF", table_inf)
        for c in sd["CLASS_INF"]["CLASS_OBJ"]:
            items = c["CLASS"] if isinstance(c["CLASS"], list) else [c["CLASS"]]
            classes[c["@id"]] = {it["@code"]: it["@name"] for it in items}
        vals = sd["DATA_INF"].get("VALUE", [])
        if isinstance(vals, dict):
            vals = [vals]
        values.extend(vals)
        ri = sd["RESULT_INF"]
        nxt = ri.get("NEXT_KEY")
        print(f"  got {len(vals)} (total so far {len(values)}) next={nxt}", flush=True)
        if not nxt:
            break
        start = int(nxt)
        time.sleep(1.0)  # 低速・1回限り(自動化抑止)
    return table_inf, values, classes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--stats-data-id", required=True)
    ap.add_argument("--area-from", default="")
    ap.add_argument("--area-to", default="")
    ap.add_argument("--area-extra", default="", help="範囲外で追加取得する cdArea(カンマ区切り・例 区計 13113)")
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    app_id = os.environ.get("ESTAT_APP_ID", "")
    if not app_id:
        print("ESTAT_APP_ID が未設定", file=sys.stderr)
        return 2
    extra: dict = {}
    if args.area_from and args.area_to:
        extra = {"cdAreaFrom": args.area_from, "cdAreaTo": args.area_to}
    print(f"[estat_fetch] statsDataId={args.stats_data_id} {extra}")
    table_inf, values, classes = fetch_all(app_id, args.stats_data_id, extra)
    for a in [x for x in args.area_extra.split(",") if x]:
        print(f"[estat_fetch] extra area {a}")
        _, v2, c2 = fetch_all(app_id, args.stats_data_id, {"cdArea": a})
        values.extend(v2)
        for k, m in c2.items():
            classes.setdefault(k, {}).update(m)
    out = {
        "meta": {
            "statsDataId": args.stats_data_id,
            "source": "e-Stat API (getStatsData 3.0)",
            "license": "政府標準利用規約2.0",
            "fetched": dt.date.today().isoformat(),
            "params": {**extra, "area_extra": args.area_extra, "paged": True},
            "table": {k: table_inf.get(k) for k in ("STAT_NAME", "TITLE", "SURVEY_DATE", "GOV_ORG") if k in table_inf},
            "n_values": len(values),
        },
        "classes": classes,
        "values": values,
    }
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False)
    areas = {v.get("@area") for v in values}
    cats = {v.get("@cat01") for v in values}
    print(f"[estat_fetch] wrote {args.out}: values={len(values)} areas={len(areas)} cat01={len(cats)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
