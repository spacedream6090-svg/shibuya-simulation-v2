"""R-106: e-Gov 法令 API v2 で法令の現行版を読み、条を標準出力に出す(読むだけ)。
使い方: python egov.py <law_id> <条番号...>   例: python egov.py 358AC1000000032 13 13_2
全文 XML は環境変数 R106_CACHE(スクラッチの場所)に置く。リポの data/ には置かない。
出力: 法令名・法令番号・版の ID・改正の施行日・条の本文(空白を詰めたもの)。
"""
import os, re, sys, urllib.request
import xml.etree.ElementTree as ET

CACHE = os.environ.get("R106_CACHE", ".")

def load(law_id):
    path = os.path.join(CACHE, f"{law_id}.xml")
    if not os.path.exists(path):
        url = f"https://laws.e-gov.go.jp/api/2/law_data/{law_id}?response_format=xml"
        with urllib.request.urlopen(url, timeout=120) as r:
            data = r.read()
        with open(path, "wb") as f:
            f.write(data)
    return ET.parse(path).getroot()

def main():
    law_id, arts = sys.argv[1], sys.argv[2:]
    root = load(law_id)
    ri = root.find("revision_info")
    get = lambda k: (ri.findtext(k) if ri is not None else None)
    print("法令:", get("law_title"), "/", root.findtext("law_info/law_num"))
    print("版:", get("law_revision_id"), "/ 改正の施行日:", get("amendment_enforcement_date"),
          "/ 状態:", get("current_revision_status"))
    main_prov = root.find(".//MainProvision")
    for a in arts:
        hits = [x for x in main_prov.iter("Article") if x.get("Num") == a]
        if not hits:
            print(f"-- 第{a}条: 見つからない"); continue
        txt = re.sub(r"\s+", " ", "".join(hits[0].itertext())).strip()
        print(f"-- [{a}]", txt[:int(os.environ.get("R106_MAX", "3500"))])

if __name__ == "__main__":
    main()
