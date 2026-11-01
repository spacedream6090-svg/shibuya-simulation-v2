"""R-107: e-Stat API の getSimpleStatsData で CSV を取り、data/research_cache/r107/ に保存する。

使い方: python estat_get.py <statsDataId> <出力ファイル名> [key=value ...]
  key=value は API の絞り込み(例 cdTab=07 cdCat02=0)。appId は環境変数 ESTAT_APP_ID。
標準出力に、記録用の URL(appId を伏せたもの)・md5・行数を出す。
"""
import hashlib
import os
import sys
import urllib.parse
import urllib.request

sid, out = sys.argv[1], sys.argv[2]
extra = dict(a.split("=", 1) for a in sys.argv[3:])
params = {"appId": os.environ["ESTAT_APP_ID"], "statsDataId": sid, "sectionHeaderFlag": "2"}
params.update(extra)
url = "https://api.e-stat.go.jp/rest/3.0/app/getSimpleStatsData?" + urllib.parse.urlencode(params)
with urllib.request.urlopen(url, timeout=120) as r:
    body = r.read()
path = os.path.join("data", "research_cache", "r107", out)
with open(path, "wb") as f:
    f.write(body)
shown = url.replace(urllib.parse.quote(os.environ["ESTAT_APP_ID"]), "(環境変数)").replace(os.environ["ESTAT_APP_ID"], "(環境変数)")
print("URL", shown)
print("MD5", hashlib.md5(body).hexdigest(), "BYTES", len(body), "LINES", body.count(b"\n"))
