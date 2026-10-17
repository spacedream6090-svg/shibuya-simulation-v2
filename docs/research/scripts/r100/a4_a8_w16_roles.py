"""R-100 A4(資産側)と A8: W16 の職務者と組織の席の重なり・外で働く職業の体数。読むだけ。

入力
- data/world/v2/w16_population.parquet(390,067 体)
- data/world/v2/w6_org.parquet(9,872 組織)
- data/persona_pool_v2/L1..L5(pool_layer/pool_index から職業と shift_pattern を引く)
出力: 標準出力と data/research_cache/r100/a4_a8_w16_roles.json

実行: .venv/Scripts/python.exe docs/research/scripts/r100/a4_a8_w16_roles.py
"""

from __future__ import annotations

import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[4]
WORLD = ROOT / "data" / "world" / "v2"
POOL = ROOT / "data" / "persona_pool_v2"
OUT = ROOT / "data" / "research_cache" / "r100" / "a4_a8_w16_roles.json"
LAYERS = ("L1", "L2", "L3", "L4", "L5")
KIND_NAMES = {0: "通勤", 1: "来街", 2: "従業(在区就業の住民)", 3: "住民", 4: "指令", 5: "通学",
              6: "定期来街", 7: "訪日", 8: "乗務"}

# A8 の拾い方(発注 §A8)。職業名だけで判断できるものを 3 群に分ける。根拠は答申 §4-1。
A8_GROUPS: dict[str, list[str]] = {
    "A 乗り物・路上が主(運転・配達・回収・巡回・路上の警備)": [
        "宅配ドライバー", "トラック運転手", "深夜配送", "回収", "設備巡回", "警備員",
    ],
    "B 外回りの営業(屋外の移動と訪問先が主・推測を含む)": [
        "不動産営業", "営業", "金融営業", "証券営業", "保険外交員", "リース営業", "人材営業",
        "卸売営業担当", "派遣コーディネーター",
    ],
    "C 現場・施設の巡回(屋外か屋内か職業名だけでは決まらない)": [
        "土木施工管理技士", "施工管理技士", "設備施工管理技士", "内装施工管理者",
        "常駐警備", "夜間清掃", "カメラマン", "撮影アシスタント", "警備司令",
        "設備保守員", "設備管理員", "不動産管理員",
    ],
}
DUTY_OUTDOOR = ["タクシー運転手", "バス運転士", "警察官", "納品ドライバー", "清掃作業員",
                "ティッシュ配り", "募金スタッフ", "街頭演説者", "路上占い師", "ストリートミュージシャン",
                "キッチンカー営業者", "配信者", "路上支援員", "路上生活者", "消防士", "救急隊員",
                "電車運転士", "車掌", "駅員", "夜間清掃員"]


def read_pool_cols() -> dict[str, dict[str, list]]:
    cols: dict[str, dict[str, list]] = {}
    for L in LAYERS:
        occ, sp = [], []
        for f in sorted((POOL / L).glob("part-*.jsonl")):
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    if not line.strip():
                        continue
                    d = json.loads(line)
                    occ.append(d.get("occupation") or "")
                    s = d.get("shift_pattern")
                    sp.append(f"{s.get('open')}-{s.get('close')} {s.get('days')}" if s else "")
        cols[L] = {"occupation": occ, "shift": sp}
        print(L, len(occ), flush=True)
    return cols


def main() -> None:
    pop = pq.read_table(WORLD / "w16_population.parquet",
                        columns=["agent_id", "kind", "org_id", "industry_key", "duty_role",
                                 "pool_layer", "pool_index", "synthetic"]).to_pydict()
    n = len(pop["agent_id"])
    kind = np.asarray(pop["kind"])
    org = np.asarray(pop["org_id"])
    duty = np.asarray(pop["duty_role"], dtype=object)
    ind = np.asarray(pop["industry_key"], dtype=object)
    layer = np.asarray(pop["pool_layer"])
    pidx = np.asarray(pop["pool_index"])
    syn = np.asarray(pop["synthetic"])
    res: dict = {"n_agents": n}

    # ---- A4: 職務者と組織の席 -------------------------------------------------
    is_duty = duty != ""
    res["duty_total"] = int(is_duty.sum())
    res["duty_role_counts"] = dict(Counter(duty[is_duty].tolist()).most_common())
    res["duty_with_org_seat"] = int((is_duty & (org >= 0)).sum())
    res["duty_with_industry_key"] = int((is_duty & (ind != "")).sum())
    res["duty_kind"] = {KIND_NAMES[int(k)]: int(c) for k, c in
                        zip(*np.unique(kind[is_duty], return_counts=True))}
    res["duty_pool_layer"] = {int(k): int(c) for k, c in
                              zip(*np.unique(layer[is_duty], return_counts=True))}
    seated = org >= 0
    res["seated_total"] = int(seated.sum())
    res["seated_kind"] = {KIND_NAMES[int(k)]: int(c) for k, c in
                          zip(*np.unique(kind[seated], return_counts=True))}
    res["seated_pool_layer"] = {int(k): int(c) for k, c in
                                zip(*np.unique(layer[seated], return_counts=True))}
    res["seated_by_industry"] = dict(Counter(ind[seated].tolist()).most_common())

    # W6 の TR(運輸業・郵便業)組織: 細目と人数
    w6 = pq.read_table(WORLD / "w6_org.parquet").to_pydict()
    tr = defaultdict(lambda: [0, 0])
    tr_orgs = []
    for i in range(len(w6["org_id"])):
        if w6["industry_key"][i] == "TR":
            tr[w6["sector_detail"][i]][0] += 1
            tr[w6["sector_detail"][i]][1] += int(w6["employees"][i])
            tr_orgs.append((int(w6["employees"][i]), w6["org_id"][i], w6["sector_detail"][i],
                            w6["size_band"][i]))
    tr_orgs.sort(reverse=True)
    res["w6_tr_by_sector"] = {k: {"orgs": v[0], "employees": v[1]} for k, v in tr.items()}
    res["w6_tr_top_orgs"] = tr_orgs[:8]

    cols = read_pool_cols()

    def occ_of(i: int) -> str:
        L = int(layer[i])
        if L <= 0 or pidx[i] < 0:
            return ""
        return cols[f"L{L}"]["occupation"][int(pidx[i])]

    occ = np.array([occ_of(i) for i in range(n)], dtype=object)
    res["w16_occupation_counts"] = dict(Counter(occ.tolist()).most_common())
    tr_seat = seated & (ind == "TR")
    res["tr_seated_n"] = int(tr_seat.sum())
    res["tr_seated_occupations"] = dict(Counter(occ[tr_seat].tolist()).most_common(15))
    # 職務の役割名を職業に持つ体が席にも座っていないか(名前の重なり)
    duty_names = set(res["duty_role_counts"])
    res["seated_with_duty_like_occupation"] = dict(
        Counter(o for o in occ[seated].tolist() if o in duty_names).most_common())
    # ---- A8 ------------------------------------------------------------------
    meta = json.loads((POOL / "meta.json").read_text(encoding="utf-8"))
    pool_occ = meta["occupations"]
    w16c = res["w16_occupation_counts"]
    a8 = {}
    for g, names in A8_GROUPS.items():
        rows = []
        for nm in names:
            m = occ == nm
            rows.append({"occupation": nm, "pool": int(pool_occ.get(nm, 0)),
                         "w16": int(w16c.get(nm, 0)),
                         "w16_by_kind": {KIND_NAMES[int(k)]: int(c) for k, c in
                                         zip(*np.unique(kind[m], return_counts=True))},
                         "w16_synthetic": int((m & syn).sum())})
        a8[g] = rows
    res["a8"] = a8
    res["a8_duty_reference"] = {nm: {"pool": int(pool_occ.get(nm, 0)),
                                     "w16_duty_role": int(res["duty_role_counts"].get(nm, 0))}
                                for nm in DUTY_OUTDOOR}
    res["pool_occupations_not_in_w16"] = sorted(k for k in pool_occ if k not in w16c)

    # ---- shift_pattern の確認(設計書 C5-b の「L2 全件が 09:00-18:00 mon-fri の縮退値」) ------
    l2_all = Counter(cols["L2"]["shift"])
    l2_w16 = Counter(cols["L2"]["shift"][int(pidx[i])] for i in np.flatnonzero(layer == 2))
    res["shift_L2_pool_top"] = l2_all.most_common(12)
    res["shift_L2_used_in_w16_top"] = l2_w16.most_common(12)
    res["shift_L2_used_in_w16_n"] = int((layer == 2).sum())

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")
    for k, v in res.items():
        if k in ("w16_occupation_counts",):
            print(k, "distinct", len(v), "top", list(v.items())[:10])
            continue
        print(k, json.dumps(v, ensure_ascii=False)[:1500])


if __name__ == "__main__":
    sys.exit(main())


def seat_industry_mismatch() -> None:
    """追加の確認: 席に座った体の「プール上の産業キー」と「W16 の席の産業キー」の一致率。

    実行: .venv/Scripts/python.exe -c "import runpy,sys; m=runpy.run_path(
    'docs/research/scripts/r100/a4_a8_w16_roles.py'); m['seat_industry_mismatch']()"
    """
    pop = pq.read_table(WORLD / "w16_population.parquet",
                        columns=["org_id", "industry_key", "pool_layer", "pool_index"]).to_pydict()
    keys = {}
    for L in ("L1", "L2"):
        ks = []
        for f in sorted((POOL / L).glob("part-*.jsonl")):
            with open(f, encoding="utf-8") as fh:
                for line in fh:
                    if line.strip():
                        ks.append(json.loads(line).get("industry_key") or "")
        keys[L] = ks
    same = tot = 0
    by_seat = defaultdict(lambda: [0, 0])
    for o, ik, L, i in zip(pop["org_id"], pop["industry_key"], pop["pool_layer"], pop["pool_index"]):
        if o < 0:
            continue
        pk = keys[f"L{L}"][i]
        tot += 1
        by_seat[ik][1] += 1
        if pk == ik:
            same += 1
            by_seat[ik][0] += 1
    print("seated", tot, "pool industry == seat industry", same, round(same / tot, 4))
    for k, (s, t) in sorted(by_seat.items(), key=lambda x: -x[1][1]):
        print(k, t, round(s / t, 4))
