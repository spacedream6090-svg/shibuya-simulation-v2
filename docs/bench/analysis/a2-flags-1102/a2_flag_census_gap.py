"""A2 の旗 3 欄の初期化(OSM の brand)と経済センサスの法人の割合のずれを数える(11-02r §3 の 2・7 (ア))。

読むだけの補助スクリプト(src/ と tools/ に触らない・世界の資産は変えない)。
リポの根から `.venv/Scripts/python docs/bench/analysis/a2-flags-1102/a2_flag_census_gap.py` で回す
(pyarrow が要る。システムの python には無い)。出力は同じ場所の `a2_flag_census_gap.json`。

入力(読むだけ):
- data/world/v2/w6_poi.parquet(W6 の POI 2,337 行・brand の欄は無い)
- data/realworld/osm/poi_tags_overpass_20260928.json(OSM の生タグ 3,516 要素)
- data/realworld/estat/経済センサス2021_事業所ベース_産業大分類_従業者売上_渋谷区.json(e-Stat 0004006322)
- data/realworld/estat/経済センサス2021_事業所数従業者数_渋谷区.json(e-Stat 0003449701・参考)

物差し 3 つ(R-134 §7 題 5 の (a)(b)(c)・どれを採るかはユーザー):
- (a) brand・brand:ja・brand:en・brand:wikidata のどれかがある
- (b) brand:wikidata がある
- (c) (a) から shop=convenience と「operator が brand と別の名」を値付けだけ店に戻す
  (operator の比べ方は文字の正規化+包含=expedient。日本の OSM では operator はほぼ本社の法人名か
  入居する建物の名なので、加盟者の印にはならない=README §3)
"""
from __future__ import annotations

import hashlib
import json
import re
import statistics
import unicodedata
from collections import Counter, defaultdict
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]
OUT = Path(__file__).resolve().parent / "a2_flag_census_gap.json"

W6_POI = "data/world/v2/w6_poi.parquet"
OSM_TAGS = "data/realworld/osm/poi_tags_overpass_20260928.json"
CENSUS_EST = "data/realworld/estat/経済センサス2021_事業所ベース_産業大分類_従業者売上_渋谷区.json"
CENSUS_ENT = "data/realworld/estat/経済センサス2021_事業所数従業者数_渋谷区.json"

#: 主のタグを探す順(最初に当たった鍵を主とする)。
PRIMARY_KEYS = ("shop", "amenity", "tourism", "leisure", "healthcare", "office", "craft")
BRAND_KEYS = ("brand", "brand:ja", "brand:en", "brand:wikidata")
BRAND_NAME_KEYS = ("brand", "brand:ja", "brand:en")

#: 経済センサスの大分類の符号(e-Stat 0004006322 の cat01)。
MAJOR_NAMES = {
    "E": "製造業", "G": "情報通信業", "I": "卸売業，小売業", "J": "金融業，保険業",
    "K": "不動産業，物品賃貸業", "L": "学術研究，専門・技術サービス業", "M": "宿泊業，飲食サービス業",
    "N": "生活関連サービス業，娯楽業", "O": "教育，学習支援業", "P": "医療，福祉", "Q": "複合サービス事業",
    "R": "サービス業（他に分類されないもの）",
}
#: 値付け・品揃え・営業時間の旗が主に効く「店」の大分類(小売・飲食と宿泊・生活関連と娯楽)。
CORE_MAJORS = ("I", "M", "N")
#: 対象外の印(センサスの民営事業所に入らない・店でない・業種が決まらない)。
EXCL_PUBLIC = "excluded:public"        # 公務・公営(センサスの民営の表に入らない)
EXCL_NOT_STORE = "excluded:not_store"  # 公園・像・案内所など(事業所でない)
EXCL_OFFICE = "excluded:office_unknown_industry"  # office=company など業種が決まらない事務所
EXCL_VACANT = "excluded:vacant"
NO_TAGS = "no_raw_tags"

# ---------------------------------------------------------------- 写像の表(OSM の値 → 大分類)
# 既定: shop=* は I(小売)。以下は例外。JSIC(日本標準産業分類 第 13 回改定)の大分類への読み。
# 「推測」の印の行は JSIC の項目の当てはめを親が確かめていない。
SHOP_OVERRIDES = {
    "hairdresser": "N", "beauty": "N", "massage": "N", "dry_cleaning": "N", "laundry": "N",
    "travel_agency": "N",
    "copyshop": "R",           # 推測(事業サービス業)
    "printing": "E",           # 推測(印刷業=製造業)
    "money_lender": "J", "pawnbroker": "J",
    "estate_agent": "K",
    "vacant": EXCL_VACANT,
}
AMENITY_MAP = {
    "restaurant": "M", "cafe": "M", "fast_food": "M", "ice_cream": "M", "pub": "M", "bar": "M",
    "food_court": "M", "nightclub": "M", "love_hotel": "M",
    "internet_cafe": "N",      # 推測
    "karaoke_box": "N", "cinema": "N", "theatre": "N", "events_venue": "N", "arts_centre": "N",
    "gambling": "N", "public_bath": "N",
    "studio": "G",             # 推測(放送・映像の制作)
    "bank": "J",
    "pharmacy": "I",
    "dentist": "P", "clinic": "P", "hospital": "P", "doctors": "P",
    "kindergarten": "O", "school": "O", "college": "O", "university": "O",
    "post_office": "Q",
    "place_of_worship": "R",
    "library": EXCL_PUBLIC,    # 区立が主(民営の表の外)=推測
    "police": EXCL_PUBLIC,
    "bicycle_parking": EXCL_NOT_STORE,
}
TOURISM_MAP = {
    "hotel": "M", "guest_house": "M", "hostel": "M",
    "museum": "O", "gallery": "O",
    "artwork": EXCL_NOT_STORE, "attraction": EXCL_NOT_STORE, "theme_park": EXCL_NOT_STORE,
    "information": EXCL_NOT_STORE,
}
LEISURE_MAP = {
    "fitness_centre": "N", "sports_centre": "N", "amusement_arcade": "N", "adult_gaming_centre": "N",
    "sauna": "N", "karaoke": "N", "stadium": "N",
    "park": EXCL_NOT_STORE, "garden": EXCL_NOT_STORE, "pitch": EXCL_NOT_STORE,
}
OFFICE_MAP = {
    "estate_agent": "K", "lawyer": "L", "architect": "L", "insurance": "J",
    "religion": "R",
    "government": EXCL_PUBLIC, "diplomatic": EXCL_PUBLIC,
}
CRAFT_MAP = {"glaziery": "E"}  # 推測


def major_of(tags: dict[str, str]) -> tuple[str, str]:
    """(大分類の符号か対象外の印, 主のタグ 'key=value')。"""
    for k in PRIMARY_KEYS:
        if k not in tags:
            continue
        v = tags[k]
        pk = f"{k}={v}"
        if k == "shop":
            return SHOP_OVERRIDES.get(v, "I"), pk
        if k == "amenity":
            return AMENITY_MAP.get(v, EXCL_NOT_STORE), pk
        if k == "tourism":
            return TOURISM_MAP.get(v, EXCL_NOT_STORE), pk
        if k == "leisure":
            return LEISURE_MAP.get(v, EXCL_NOT_STORE), pk
        if k == "healthcare":
            return "P", pk
        if k == "office":
            return OFFICE_MAP.get(v, EXCL_OFFICE), pk
        if k == "craft":
            return CRAFT_MAP.get(v, "E"), pk
    return EXCL_NOT_STORE, "<no primary key>"


def norm(s: str) -> str:
    s = unicodedata.normalize("NFKC", s).casefold()
    for tok in ("株式会社", "(株)", "ホールディングス", "ジャパン", "japan"):
        s = s.replace(tok, "")
    for ch in " ・-‐－_.,()（）&＆":
        s = s.replace(ch, "")
    return s


def soft(s: str) -> str:
    """名の照合用(空白を残す)。"""
    return " ".join(unicodedata.normalize("NFKC", s).casefold().split())


def build_brand_vocab(tags_by: dict[str, dict[str, str]]) -> tuple[set[str], set[str]]:
    """(ASCII の brand 名=語の境で当てる 4 字以上, それ以外=含むで当てる 3 字以上)。"""
    ascii_b, other_b = set(), set()
    for t in tags_by.values():
        for n in brand_names(t):
            b = soft(n)
            if b.isascii():
                if len(b) >= 4:
                    ascii_b.add(b)
            elif len(b) >= 3:
                other_b.add(b)
    return ascii_b, other_b


def name_hits(name: str, vocab: tuple[set[str], set[str]]) -> list[str]:
    n = soft(name)
    if not n:
        return []
    ascii_b, other_b = vocab
    hits = [b for b in other_b if b in n]
    hits += [b for b in ascii_b if re.search(r"(?<![a-z0-9])" + re.escape(b) + r"(?![a-z0-9])", n)]
    return sorted(hits)


def brand_names(tags: dict[str, str]) -> list[str]:
    return [tags[k] for k in BRAND_NAME_KEYS if tags.get(k)]


def operator_differs(tags: dict[str, str]) -> bool | None:
    """operator が brand と別の名か(None=operator か brand が無い)。正規化+包含で同じとみる(expedient)。"""
    op = tags.get("operator")
    names = brand_names(tags)
    if not op or not names:
        return None
    o = norm(op)
    for n in names:
        b = norm(n)
        if b and (b in o or o in b):
            return False
    return True


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def load_census_est() -> dict:
    sd = json.loads((ROOT / CENSUS_EST).read_text(encoding="utf-8"))["GET_STATS_DATA"]["STATISTICAL_DATA"]
    cells: dict[str, dict[str, str]] = defaultdict(dict)
    for v in sd["DATA_INF"]["VALUE"]:
        if v["@tab"] == "102-2021":  # 事業所数
            cells[v["@cat01"]][v["@cat02"]] = v["$"]
    out = {}
    for code in list(MAJOR_NAMES) + ["AR"]:
        c = cells[code]

        def num(x: str) -> int:
            return int(x) if x.isdigit() else 0

        total, indiv, company, other = num(c["0"]), num(c["1"]), num(c["2"]), num(c["3"])
        out[code] = {
            "total": total, "individual": indiv, "company": company, "non_company_corp": other,
            "raw": c,
            "corp_pct": round(100.0 * (company + other) / total, 2) if total else None,
            "individual_pct": round(100.0 * indiv / total, 2) if total else None,
            "sum_check": total == indiv + company + other,
        }
    return {"table_id": sd["TABLE_INF"]["@id"], "title": sd["TABLE_INF"]["TITLE"]["$"],
            "published_date": sd["TABLE_INF"]["OPEN_DATE"], "by_major": out}


def load_census_ent() -> dict:
    sd = json.loads((ROOT / CENSUS_ENT).read_text(encoding="utf-8"))["GET_STATS_DATA"]["STATISTICAL_DATA"]
    cells: dict[tuple[str, str, str], str] = {}
    for v in sd["DATA_INF"]["VALUE"]:
        if v["@tab"] == "201-2021":  # 企業等数
            cells[(v["@cat01"], v["@cat02"], v["@cat03"])] = v["$"]
    out = {}
    for code in list(MAJOR_NAMES) + ["AR"]:
        def num(k: tuple[str, str, str]) -> int:
            x = cells.get(k, "-")
            return int(x) if x.isdigit() else 0

        tot, multi = num((code, "0", "0")), num((code, "0", "2"))
        out[code] = {"enterprises": tot, "multi_establishment": multi,
                     "multi_pct": round(100.0 * multi / tot, 2) if tot else None}
    return {"table_id": sd["TABLE_INF"]["@id"], "title": sd["TABLE_INF"]["TITLE"]["$"], "by_major": out}


def count(scope_ids: list[str], tags_by: dict[str, dict[str, str]],
          brand_vocab: tuple[set[str], set[str]]) -> dict:
    per_major: dict[str, Counter] = defaultdict(Counter)
    per_value: dict[str, Counter] = defaultdict(Counter)
    excluded: Counter = Counter()
    pairs: Counter = Counter()
    missed_list: list[dict] = []
    for pid in scope_ids:
        t = tags_by.get(pid)
        if t is None:
            excluded[NO_TAGS] += 1
            continue
        major, pk = major_of(t)
        if major.startswith("excluded:"):
            excluded[major] += 1
            continue
        has_a = any(t.get(k) for k in BRAND_KEYS)
        has_b = bool(t.get("brand:wikidata"))
        opd = operator_differs(t)
        conv = t.get("shop") == "convenience"
        has_c = has_a and not conv and opd is not True
        # 網羅の下限の目安(expedient): brand の無い POI の名が、ほかの要素の brand の名を含むか
        hits = [] if has_a else name_hits(t.get("name", "") or t.get("name:ja", ""), brand_vocab)
        missed = bool(hits)
        if missed:
            missed_list.append({"poi_id": pid, "primary": pk, "name": t.get("name", ""), "matched_brand": hits})
        for bucket in (per_major[major], per_value[pk]):
            bucket["n"] += 1
            bucket["brand_any"] += has_a
            bucket["brand_wikidata"] += has_b
            bucket["brand_c_pricing_hq"] += has_c
            bucket["convenience"] += conv
            bucket["operator_present_with_brand"] += opd is not None
            bucket["operator_differs"] += opd is True
            bucket["name_matches_other_brand_no_tag"] += missed
        if has_a and t.get("operator"):
            pairs[(t.get("brand") or t.get("brand:ja") or "", t["operator"])] += 1
    return {"per_major": per_major, "per_value": per_value, "excluded": excluded, "pairs": pairs,
            "missed": missed_list}


def pct(a: int, n: int) -> float | None:
    return round(100.0 * a / n, 2) if n else None


def gap_table(per_major: dict[str, Counter], est: dict, ent: dict) -> list[dict]:
    rows = []
    for code in MAJOR_NAMES:
        c = per_major.get(code, Counter())
        n = c["n"]
        cen = est["by_major"][code]
        row = {
            "major": code, "name": MAJOR_NAMES[code], "poi_n": n,
            "brand_any_n": c["brand_any"], "brand_any_pct": pct(c["brand_any"], n),
            "brand_wikidata_pct": pct(c["brand_wikidata"], n),
            "brand_c_pricing_hq_pct": pct(c["brand_c_pricing_hq"], n),
            "census_establishments": cen["total"], "census_corp_pct": cen["corp_pct"],
            "census_individual_pct": cen["individual_pct"],
            "census_multi_establishment_enterprise_pct_ref": ent["by_major"][code]["multi_pct"],
            "operator_differs_n": c["operator_differs"], "convenience_n": c["convenience"],
            "name_matches_other_brand_no_tag_n": c["name_matches_other_brand_no_tag"],
        }
        for m in ("brand_any", "brand_wikidata", "brand_c_pricing_hq"):
            p = row[f"{m}_pct"]
            row[f"gap_{m}_minus_corp_pt"] = (round(p - cen["corp_pct"], 2)
                                            if p is not None and cen["corp_pct"] is not None else None)
        rows.append(row)
    return rows


def summary(rows: list[dict], key: str, min_n: int) -> dict:
    sel = [r for r in rows if r["poi_n"] >= min_n and r[key] is not None]
    gaps = [r[key] for r in sel]
    if not gaps:
        return {"n_majors": 0}
    absg = [abs(g) for g in gaps]
    worst = max(sel, key=lambda r: abs(r[key]))
    return {
        "min_poi_n": min_n, "n_majors": len(sel),
        "median_gap_pt": round(statistics.median(gaps), 2),
        "median_abs_gap_pt": round(statistics.median(absg), 2),
        "max_abs_gap_pt": round(max(absg), 2), "max_abs_gap_major": worst["major"],
        "min_gap_pt": round(min(gaps), 2), "max_gap_pt": round(max(gaps), 2),
        "majors_abs_gap_ge_20pt": [r["major"] for r in sel if abs(r[key]) >= 20.0],
    }


def to_plain(c: dict[str, Counter]) -> dict:
    return {k: dict(v) for k, v in sorted(c.items(), key=lambda kv: -kv[1]["n"])}


def main() -> None:
    osm = json.loads((ROOT / OSM_TAGS).read_text(encoding="utf-8"))
    tags_by = {f"p_{e['type'][0]}{e['id']}": {k: str(v) for k, v in (e.get("tags") or {}).items()}
               for e in osm["elements"]}
    w6_ids = pq.read_table(ROOT / W6_POI, columns=["poi_id"]).column("poi_id").to_pylist()
    brand_vocab = build_brand_vocab(tags_by)

    est = load_census_est()
    ent = load_census_ent()

    scopes = {"w6_poi": w6_ids, "osm_all_elements": sorted(tags_by)}
    result: dict = {
        "what": "A2 の旗 3 欄の初期化(OSM brand)と経済センサス 2021 の法人の割合のずれ(11-02r §3 の 2)",
        "script": "docs/bench/analysis/a2-flags-1102/a2_flag_census_gap.py",
        "inputs": {p: {"sha256": sha256(ROOT / p)} for p in (W6_POI, OSM_TAGS, CENSUS_EST, CENSUS_ENT)},
        "definitions": {
            "brand_any": "brand・brand:ja・brand:en・brand:wikidata のどれか(R-134 題 5 (a)=A2 の 2 の文)",
            "brand_wikidata": "brand:wikidata(題 5 (b))",
            "brand_c_pricing_hq": "(a) から shop=convenience と operator≠brand(正規化+包含で比べる)を除いた=値付けの旗が本社の数(題 5 (c))",
            "census_corp_pct": "(会社+会社以外の法人)/総数(事業所数・民営)=100−個人の割合",
            "census_multi_establishment_enterprise_pct_ref": "参考=渋谷区に本所のある企業等のうち複数事業所企業の割合(企業産業・0003449701)",
            "gap": "OSM の割合 − センサスの法人の割合(ポイント)",
            "name_matches_other_brand_no_tag": "brand の無い POI の名が、ほかの要素の brand の名を含む数(ASCII は語の境で 4 字以上・ほかは 3 字以上)=タグの抜けの目安(expedient・誤当たりを含みうる=一覧を JSON に)",
            "mapping": "major_of() の表(JSIC 大分類への読み・推測の行はスクリプトに印)",
        },
        "census_establishment": est,
        "census_enterprise_ref": ent,
        "scopes": {},
    }
    for name, ids in scopes.items():
        c = count(ids, tags_by, brand_vocab)
        rows = gap_table(c["per_major"], est, ent)
        tot = Counter()
        for v in c["per_major"].values():
            tot.update(v)
        core = [r for r in rows if r["major"] in CORE_MAJORS]
        cn = sum(r["poi_n"] for r in core)
        cb = sum(r["brand_any_n"] for r in core)
        ce = sum(est["by_major"][m]["total"] for m in CORE_MAJORS)
        ci = sum(est["by_major"][m]["individual"] for m in CORE_MAJORS)
        core_row = {"majors": list(CORE_MAJORS), "poi_n": cn, "brand_any_n": cb,
                    "brand_any_pct": pct(cb, cn), "census_establishments": ce,
                    "census_corp_pct": pct(ce - ci, ce),
                    "gap_brand_any_minus_corp_pt": round(pct(cb, cn) - pct(ce - ci, ce), 2)}
        bound_ok = [r["major"] for r in rows if r["brand_any_pct"] is not None
                    and r["census_corp_pct"] is not None and r["brand_any_pct"] <= r["census_corp_pct"]]
        result["scopes"][name] = {
            "n_ids": len(ids),
            "core_store_majors_IMN": core_row,
            "upper_bound_check_brand_le_corp": {"majors_ok": bound_ok,
                                                "n_ok": len(bound_ok), "n_rows": len(rows)},
            "excluded": dict(c["excluded"]),
            "in_scope_total": dict(tot),
            "gap_rows": rows,
            "summary": {
                f"{m}_all": summary(rows, f"gap_{m}_minus_corp_pt", 1)
                for m in ("brand_any", "brand_wikidata", "brand_c_pricing_hq")
            } | {
                f"{m}_n_ge_10": summary(rows, f"gap_{m}_minus_corp_pt", 10)
                for m in ("brand_any", "brand_wikidata", "brand_c_pricing_hq")
            },
            "per_osm_value": to_plain(c["per_value"]),
            "name_matches_other_brand_no_tag_list": c["missed"],
            "brand_operator_pairs": [{"brand": b, "operator": o, "n": n}
                                     for (b, o), n in c["pairs"].most_common()],
        }
    OUT.write_text(json.dumps(result, ensure_ascii=False, indent=1, sort_keys=False) + "\n",
                   encoding="utf-8", newline="\n")
    print(f"wrote {OUT.relative_to(ROOT).as_posix()}")


if __name__ == "__main__":
    main()
