# -*- coding: utf-8 -*-
"""手順 0 の比べ: off と none の JSON の欄ごとの一致。"""
import json
import sys

a = json.load(open(sys.argv[1], encoding="utf-8"))
b = json.load(open(sys.argv[2], encoding="utf-8"))
same, diff = [], []
for k in sorted(set(a) | set(b)):
    (same if a.get(k) == b.get(k) else diff).append(k)
print("同じ", len(same), ":", ", ".join(same))
print("違う", len(diff))
for k in diff:
    print("  ", k, "| off:", json.dumps(a.get(k), ensure_ascii=False)[:300], "| none:", json.dumps(b.get(k), ensure_ascii=False)[:300])
