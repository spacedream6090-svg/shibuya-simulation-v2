"""R-106: e-Gov 法令 API v2 の改正履歴(law_revisions)から、改正法の公布日と施行日の差を出す(読むだけ)。
使い方: python egov_revisions.py <law_id> [施行日の年の下限]"""
import sys, json, urllib.request, datetime as dt
law_id = sys.argv[1]; ymin = int(sys.argv[2]) if len(sys.argv) > 2 else 2000
url = f"https://laws.e-gov.go.jp/api/2/law_revisions/{law_id}"
with urllib.request.urlopen(url, timeout=60) as r:
    d = json.load(r)
print("==", d.get("law_info", {}).get("law_num"), url)
for rv in d.get("revisions", []):
    e, p = rv.get("amendment_enforcement_date"), rv.get("amendment_promulgate_date")
    if not e or not p or int(e[:4]) < ymin: continue
    days = (dt.date.fromisoformat(e) - dt.date.fromisoformat(p)).days
    print(f"  公布 {p} → 施行 {e} ({days} 日) 改正法 {rv.get('amendment_law_num')} {rv.get('amendment_law_title') or ''}"[:200])
