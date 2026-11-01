"""R-112 (v): 手元の PLATEAU 2025 渋谷区の都市設備(frn)を function ごとに数える(W1 に掛かる 2 メッシュ・ファイル全体)。

使い方: python docs/research/scripts/r112/r112_plateau_frn.py
入力: data/realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op/udx/frn/*.gml と codelists/CityFurniture_function.xml
出力: docs/research/scripts/r112/r112_plateau_frn.json
"""
import collections, json, pathlib, re

ROOT = pathlib.Path("data/realworld/plateau_2025/13113_shibuya-ku_pref_2025_citygml_1_op")
MESHES = ["53393586", "53393596"]  # W1 の中心 2 メッシュ(R-82 と同じ)

code = {}
cl = (ROOT / "codelists/CityFurniture_function.xml").read_text(encoding="utf-8")
for m in re.finditer(r"<gml:description>(.*?)</gml:description>\s*<gml:name>(.*?)</gml:name>", cl, re.S):
    code[m.group(2).strip()] = m.group(1).strip()
if not code:
    for m in re.finditer(r"<gml:name>(.*?)</gml:name>.*?<gml:description>(.*?)</gml:description>", cl, re.S):
        code[m.group(1).strip()] = m.group(2).strip()

res = {}
for mesh in MESHES:
    t = (ROOT / f"udx/frn/{mesh}_frn_6697_op.gml").read_text(encoding="utf-8")
    objs = t.split("<frn:CityFurniture")[1:]
    c = collections.Counter()
    lod = collections.Counter()
    for o in objs:
        f = re.search(r"<frn:function[^>]*>(.*?)</frn:function>", o)
        c[f.group(1) if f else "(なし)"] += 1
        for L in ("lod1Geometry", "lod2Geometry", "lod3Geometry"):
            if L in o:
                lod[L] += 1
    res[mesh] = {"objects": len(objs), "lod": dict(lod),
                 "function": {f"{k} {code.get(k, '?')}": v for k, v in c.most_common()}}
out = pathlib.Path("docs/research/scripts/r112/r112_plateau_frn.json")
out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
print(json.dumps(res, ensure_ascii=False, indent=1))
