"""R-112 (v): OSM の形を持つ物(街路の設備)と屋内タグを W1 の範囲で数える。

使い方: python docs/research/scripts/r112/r112_osm_objects.py fetch   # Overpass から取得して保存(1 回だけ)
        python docs/research/scripts/r112/r112_osm_objects.py count   # 保存したファイルを数える
保存先: data/research_cache/r112/osm_objects_w1_<日付>.json(ODbL・gitignore 下)
"""
import collections, datetime, hashlib, json, pathlib, sys, urllib.parse, urllib.request

BBOX = (35.6505, 139.6905, 35.6685, 139.7115)  # W1(src/shibuya/build/geo/w11_station_exits.py の BBOX)
OUT_DIR = pathlib.Path("data/research_cache/r112")
KEYS = [
    ("amenity", "bench"), ("leisure", "picnic_table"), ("amenity", "waste_basket"), ("amenity", "recycling"),
    ("amenity", "vending_machine"), ("amenity", "bicycle_parking"), ("amenity", "motorcycle_parking"),
    ("amenity", "parking_entrance"), ("amenity", "telephone"), ("amenity", "post_box"), ("amenity", "toilets"),
    ("amenity", "drinking_water"), ("amenity", "smoking_area"), ("amenity", "shelter"), ("amenity", "atm"),
    ("amenity", "clock"), ("amenity", "fountain"), ("man_made", "street_cabinet"), ("highway", "street_lamp"),
    ("highway", "traffic_signals"), ("highway", "bus_stop"), ("natural", "tree"), ("barrier", "bollard"),
    ("barrier", "fence"), ("barrier", "turnstile"), ("barrier", "gate"), ("tourism", "information"),
    ("emergency", "fire_hydrant"), ("emergency", "defibrillator"), ("man_made", "surveillance"),
]
QUERY_ANY = ["advertising", "indoor", "level", "repeat_on", "door", "entrance", "highway=elevator", "conveying"]


def build_query():
    s, w, n, e = BBOX
    b = f"({s},{w},{n},{e})"
    parts = [f'nwr["{k}"="{v}"]{b};' for k, v in KEYS]
    parts += [f'nwr["advertising"]{b};', f'nwr["indoor"]{b};', f'nwr["highway"="elevator"]{b};',
              f'nwr["conveying"]{b};', f'nwr["entrance"]{b};', f'nwr["door"]{b};', f'nwr["repeat_on"]{b};',
              f'nwr["shop"]["level"]{b};', f'nwr["amenity"]["level"]{b};']
    return "[out:json][timeout:120];(" + "".join(parts) + ");out tags center;"


def fetch():
    q = build_query()
    data = urllib.parse.urlencode({"data": q}).encode()
    req = urllib.request.Request("https://overpass-api.de/api/interpreter", data=data,
                                 headers={"User-Agent": "shibuya-sim-research/R-112 (read-only count)"})
    raw = urllib.request.urlopen(req, timeout=180).read()
    day = datetime.date.today().strftime("%Y%m%d")
    out = OUT_DIR / f"osm_objects_w1_{day}.json"
    out.write_bytes(raw)
    (OUT_DIR / f"osm_objects_w1_{day}.query.txt").write_text(q + "\n", encoding="utf-8", newline="\n")
    print(out, hashlib.md5(raw).hexdigest(), len(raw))


def count(path):
    d = json.loads(pathlib.Path(path).read_text(encoding="utf-8"))
    els = d["elements"]
    res = {"osm_base": d.get("osm3s", {}).get("timestamp_osm_base"), "elements": len(els), "by_key": {}, "extra": {}}
    for k, v in KEYS:
        es = [x for x in els if x.get("tags", {}).get(k) == v]
        kinds = collections.Counter(x["type"] for x in es)
        res["by_key"][f"{k}={v}"] = {"n": len(es), "types": dict(kinds),
                                      "with_level": sum(1 for x in es if "level" in x.get("tags", {}))}
    t = lambda x: x.get("tags", {})
    adv = [x for x in els if "advertising" in t(x)]
    res["extra"]["advertising"] = dict(collections.Counter(t(x)["advertising"] for x in adv))
    res["extra"]["advertising_with_text"] = sum(1 for x in adv if any(k in t(x) for k in ("name", "message", "inscription", "description")))
    res["extra"]["indoor"] = dict(collections.Counter(t(x)["indoor"] for x in els if "indoor" in t(x)))
    res["extra"]["highway=elevator"] = sum(1 for x in els if t(x).get("highway") == "elevator")
    res["extra"]["conveying"] = dict(collections.Counter(t(x)["conveying"] for x in els if "conveying" in t(x)))
    res["extra"]["entrance"] = dict(collections.Counter(t(x)["entrance"] for x in els if "entrance" in t(x)))
    res["extra"]["door"] = dict(collections.Counter(t(x)["door"] for x in els if "door" in t(x)))
    res["extra"]["shop_or_amenity_with_level"] = sum(1 for x in els if "level" in t(x) and ("shop" in t(x) or "amenity" in t(x)))
    res["extra"]["inscription_any"] = sum(1 for x in els if "inscription" in t(x))
    vm = [x for x in els if t(x).get("amenity") == "vending_machine"]
    res["extra"]["vending_machine_vending"] = dict(collections.Counter(t(x).get("vending", "(なし)") for x in vm))
    bp = [x for x in els if t(x).get("amenity") == "bicycle_parking"]
    res["extra"]["bicycle_parking_capacity_tagged"] = sum(1 for x in bp if "capacity" in t(x))
    caps = [int(t(x)["capacity"]) for x in bp if t(x).get("capacity", "").isdigit()]
    res["extra"]["bicycle_parking_capacity_sum"] = sum(caps)
    out = pathlib.Path("docs/research/scripts/r112/r112_osm_objects.json")
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(res, ensure_ascii=False, indent=1))


if __name__ == "__main__":
    if sys.argv[1] == "fetch":
        fetch()
    else:
        count(sys.argv[2])
