"""R-107: e-Stat API の統計表一覧を引く(読むだけ)。appId は環境変数 ESTAT_APP_ID。

使い方: python estat_list.py <statsCode> <検索語> [surveyYears]
出力は表 ID・調査年月・表題(標準出力)。
"""
import json
import os
import sys
import urllib.parse
import urllib.request

code, word = sys.argv[1], sys.argv[2]
params = {"appId": os.environ["ESTAT_APP_ID"], "statsCode": code, "searchWord": word, "limit": "200"}
if len(sys.argv) > 3:
    params["surveyYears"] = sys.argv[3]
url = "https://api.e-stat.go.jp/rest/3.0/app/json/getStatsList?" + urllib.parse.urlencode(params)
with urllib.request.urlopen(url, timeout=60) as r:
    js = json.load(r)
res = js["GET_STATS_LIST"]
print("STATUS", res["RESULT"]["STATUS"], res["RESULT"].get("ERROR_MSG", ""))
tabs = res.get("DATALIST_INF", {}).get("TABLE_INF", [])
if isinstance(tabs, dict):
    tabs = [tabs]
for t in tabs:
    title = t.get("TITLE")
    if isinstance(title, dict):
        title = f'{title.get("@no", "")} {title.get("$", "")}'
    st = t.get("STATISTICS_NAME", "")
    print(t["@id"], t.get("SURVEY_DATE"), t.get("OPEN_DATE"), "|", st[:40], "|", title)
