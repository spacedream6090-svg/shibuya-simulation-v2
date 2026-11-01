"""R-106: e-Gov 法令 API v2 で法令名から law_id と最新の版(施行日)を探す(読むだけ)。"""
import sys, json, urllib.request, urllib.parse
for title in sys.argv[1:]:
    url = "https://laws.e-gov.go.jp/api/2/laws?law_title=" + urllib.parse.quote(title) + "&limit=3"
    with urllib.request.urlopen(url, timeout=60) as r:
        d = json.load(r)
    print("==", title, d.get("total_count"))
    for law in d.get("laws", [])[:5]:
        li = law.get("law_info", {}); ri = law.get("revision_info", {}) or law.get("current_revision_info", {})
        print(" ", li.get("law_id"), li.get("law_num"), ri.get("law_title"), "rev:", ri.get("law_revision_id"), "amend_enforce:", ri.get("amendment_enforcement_date"), "status:", ri.get("current_revision_status"))
