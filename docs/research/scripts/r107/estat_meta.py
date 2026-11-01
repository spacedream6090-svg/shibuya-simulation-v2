"""R-107: e-Stat API の表のメタ情報(分類と項目)を表示する(読むだけ)。

使い方: python estat_meta.py <statsDataId> [最大表示件数/分類]
"""
import json
import os
import sys
import urllib.parse
import urllib.request

sid = sys.argv[1]
nmax = int(sys.argv[2]) if len(sys.argv) > 2 else 60
params = {"appId": os.environ["ESTAT_APP_ID"], "statsDataId": sid}
url = "https://api.e-stat.go.jp/rest/3.0/app/json/getMetaInfo?" + urllib.parse.urlencode(params)
with urllib.request.urlopen(url, timeout=60) as r:
    js = json.load(r)
m = js["GET_META_INFO"]["METADATA_INF"]
ti = m["TABLE_INF"]
print(ti.get("STATISTICS_NAME"), "|", ti.get("TITLE"))
objs = m["CLASS_INF"]["CLASS_OBJ"]
if isinstance(objs, dict):
    objs = [objs]
for o in objs:
    cls = o["CLASS"]
    if isinstance(cls, dict):
        cls = [cls]
    print(f'## {o["@id"]} {o["@name"]} ({len(cls)})')
    for c in cls[:nmax]:
        print("  ", c["@code"], c["@name"], c.get("@unit", ""))
