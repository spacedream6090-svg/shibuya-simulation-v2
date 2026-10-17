"""第 4 期 4-1 段 9(W21c): 人物の文を 6-1 の器(``tools/instruments/dm_eval``)の計器で測る・合成の 1 人の例。

    python docs/bench/analysis/wallbounce-1012/pop41c/tools/persona_meter.py --stage data/world/v2_stage_4-1c \\
        --out docs/bench/analysis/wallbounce-1012/pop41c/persona_meter.json

1. 「数字はお金と時刻だけ」の計器(``dm_eval.situations.numbers_outside_money_time``)を全員の短い版・長い版にかける。
   名(なじみの場所と勤め先)を ``◇`` に伏せた文(同じ組み立て ``w21_persona.build_tables(mask_names=True)``)にもかけ、
   名の中の数字の分を分ける。
2. 判断の入力の長さ: 1-10 の評価セットの状況(先頭 20 件)に人物の文を ``w21_persona.compose_blocks`` で足し、
   ``dm_eval.situations.render``(長さの腕 t300/t1000 × 短い版/長い版)で字数・目安を超えた件数・数字の計器を測る
   (人物の文を足さない同じ状況と並べる)。人は日本語の型の体から 500 人(番号の等間隔)。
3. CP5-3: なじみの場所の上位 3(短い版に載る 3 つ=人ごとの最初の POI 3 行)に最も多く出る POI 5 つを「改変した物」と
   見立て、**番号で**照らす口 ``naming_check_ids``(本則)と、名で照らす口 ``naming_check``(補助)の両方で名指しした長い版の
   文の数を数える。名の照合は同じ名のチェーンの別の店も数える=差が出る(記録には POI の番号と数だけ)。
4. 合成の 1 人の例(:func:`example`)=記録に載せる唯一の文(個人の文は写さない)。

文は記録に写さない(数だけ)。絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
for _p in (str(REPO / "src"), str(REPO / "tools" / "instruments")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from shibuya.build.pop import w21_build_c as BC  # noqa: E402
from shibuya.build.pop import w21_persona as P  # noqa: E402
from shibuya.build.pop import w21_sources as S  # noqa: E402


def example() -> dict[str, str]:
    """合成の 1 人(実在の体ではない=値は手で置いた)の文: 日本語の短い版・長い版・英語の長い版。"""
    cols = {k: np.asarray(v) for k, v in {
        "person_id": [0], "kind": ["resident"], "age": [34], "sex": [1], "nationality": ["日本"],
        "first_language": ["ja"], "japanese_level": [-1], "home_chome": ["例町一丁目"], "institution": [False],
        "origin_name": [""], "tenure": ["private_rent"], "residence_period": ["y5_10"], "residence_years": [6.2],
        "labour": ["employed"], "emp_status": ["regular"], "occupation": ["C"], "industry": ["G"], "org_role": ["正社員"],
        "duty_role": [""], "org_name": ["(株)例示サンプル"], "org_sector": ["業務SaaS"], "org_size": ["10-19"],
        "work_area": ["stage"], "work_chome": ["例町二丁目"], "is_org_head": [False], "is_dept_head": [False],
        "dept_mates": [6], "has_supervisor": [True], "weekly_hours": [37.4], "school_kind": ["none"], "school_place": [""],
        "commute_mode": ["walk"], "commute_m": [900], "wage_monthly": [312_000], "wage_annual": [4_620_000],
        "savings": [3_870_000], "debt": [0], "consumer_credit": [0], "hh_size": [2], "hh_savings": [7_740_000],
        "outside_places": [8], "org_index": [0]}.items()}
    cols["sex"] = cols["sex"].astype(np.int64)
    members = {"owner": np.array([0]), "cat": np.array([0]), "age": np.array([36]), "sex": np.array([0])}
    places = {"owner": np.zeros(5, dtype=np.int64), "rank": np.arange(3, 8), "poi_index": np.arange(5), "name": np.array(
        ["例の喫茶店", "例の書店", "例の公園", "例の食堂", "例のコンビニ"], dtype=object),
        "cat_ja": np.array(["飲食店", "書店", "公園", "飲食店", "コンビニ"], dtype=object),
        "cat_en": np.array(["restaurant", "bookshop", "park", "restaurant", "convenience store"], dtype=object)}
    f = P.PersonaFacts(cols, members, places)
    return {"ja_short": str(P.render(f, "ja", "short")[0]), "ja_long": str(P.render(f, "ja", "long")[0]),
            "en_long": str(P.render(f, "en", "long")[0])}


def _meter(texts: np.ndarray, fn) -> dict:
    t = [str(x) for x in np.asarray(texts, dtype=object).tolist() if x]  # 逐次: 文の数(道具=ランの外)
    v = np.array([fn(x) for x in t], dtype=np.int64)
    return {"texts": int(v.size), "texts_with_numbers": int((v > 0).sum()), "numbers_total": int(v.sum()),
            "max": int(v.max()) if v.size else 0}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="data/world/v2_stage_4-1c")
    ap.add_argument("--data", default="data")
    ap.add_argument("--base", default="data/world/v2_stage_4-1b")
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--out", default="")
    ap.add_argument("--people", type=int, default=500)
    ap.add_argument("--situations", type=int, default=20)
    a = ap.parse_args(argv)
    import pyarrow.parquet as pq
    from dm_eval import situations as DS

    stage = Path(a.stage)
    tabs = {v: pq.read_table(stage / f"w21_persona_{v}.parquet").to_pydict() for v in P.VERSIONS}
    doc: dict = {"schema": "pop41c.persona_meter/1", "numbers_outside_money_time": {}, "compose": {}, "cp5_3": {}}
    # 1 数字の計器(名のまま・名を伏せた文)
    guard = S.W21Guard.for_build(Path(a.data), world=Path(a.world), out=None, extra_dirs=(Path(a.base),),
                                 extra_sources=S.SOURCES_C)
    inp = BC.load_inputs(guard, Path(a.data), Path(a.base), Path(a.world))
    lang = BC.language_columns(inp, BC.W.DEFAULT_SEED)
    masked = P.build_tables(BC.persona_facts(inp, lang), mask_names=True)
    for v in P.VERSIONS:
        same = np.array_equal(np.asarray(masked[v]["person_id"]), np.asarray(tabs[v]["person_id"]))
        doc["numbers_outside_money_time"][v] = {
            "as_built": _meter(tabs[v]["text"], DS.numbers_outside_money_time),
            "names_masked": _meter(masked[v]["text"], DS.numbers_outside_money_time), "same_people": bool(same)}
    # 2 判断の入力の長さ(1-10 の状況 × 人物の文)
    sits = DS.load_situations()[: int(a.situations)]
    built = np.flatnonzero((np.asarray(tabs["long"]["lang"]) == "ja"))
    pick = built[np.linspace(0, built.size - 1, int(a.people)).astype(np.int64)]
    acc: dict = {}
    for k, i in enumerate(pick.tolist()):  # 逐次: 人の数(500=道具)
        s = sits[k % len(sits)]
        pres = DS.orders(DS.candidates_for(s), s.sid, n_orders=1)[0]
        for length in P.VERSIONS:
            blocks = P.compose_blocks(s.blocks, tabs["short"]["text"][i], tabs["long"]["text"][i], length)
            s2 = DS.Situation(sid=s.sid, blocks=blocks, missing=s.missing, facts=s.facts)
            for arm in DS.LENGTH_ARMS:
                r = DS.render(s2, pres, length=length, arm=arm)
                r0 = DS.render(s, pres, length=length, arm=arm)
                e = acc.setdefault(f"{arm}/{length}", {"chars": [], "chars_without": [], "over": 0, "over_without": 0,
                                                        "nums": [], "nums_without": []})
                e["chars"].append(r.chars)
                e["chars_without"].append(r0.chars)
                e["over"] += int(r.over_budget)
                e["over_without"] += int(r0.over_budget)
                e["nums"].append(r.numbers_outside_money_time)
                e["nums_without"].append(r0.numbers_outside_money_time)
    for key, e in acc.items():
        doc["compose"][key] = {
            "n": len(e["chars"]), "chars_median": float(np.median(e["chars"])), "chars_max": int(np.max(e["chars"])),
            "chars_median_without_persona": float(np.median(e["chars_without"])),
            "budget_chars": int(DS.LENGTH_ARMS[key.split("/")[0]] * DS.CHARS_PER_TOKEN),
            "over_budget": e["over"], "over_budget_without_persona": e["over_without"],
            "numbers_outside_money_time_median": float(np.median(e["nums"])),
            "numbers_outside_money_time_median_without_persona": float(np.median(e["nums_without"]))}
    doc["compose"]["note"] = ("状況=1-10 の評価セットの先頭の件(B5・B6 は材料に無い=人物の文が個体の部分の全部)・人=日本語の型の"
                              "体から等間隔に選んだ人。目安の字数=トークン × 1.0(6-1 の器の CHARS_PER_TOKEN)")
    # 3 CP5-3(名指しの検査)
    facts = BC.persona_facts(inp, lang)
    own = np.asarray(facts.places["owner"])
    pi = np.asarray(facts.places["poi_index"])
    first = np.r_[True, own[1:] != own[:-1]]
    starts = np.flatnonzero(first)
    pos = np.arange(own.size) - np.repeat(starts, np.diff(np.r_[starts, own.size]))
    u, c = np.unique(pi[pos < 3], return_counts=True)
    top = u[np.argsort(-c, kind="stable")[:5]]
    names = [str(inp.poi["name"][int(j)]) for j in top.tolist()]
    same_name = {int(j): int(sum(1 for x in inp.poi["name"] if str(x) == names[q])) for q, j in enumerate(top.tolist())}
    rec = P.naming_check(tabs["long"], names)
    ids = P.naming_check_ids(tabs["long"], poi=top.tolist())
    hits_by = {int(j): sum(1 for h in rec["hits"] if names[q] in h["hits"]) for q, j in enumerate(top.tolist())}
    doc["cp5_3"] = {"pois": len(names), "poi_index": [int(j) for j in top.tolist()], "texts": rec["texts"],
                    "by_id": {"texts_with_hits": ids["hits"], "by_poi_index": ids["by_poi"]},
                    "by_name": {"texts_with_hits": len(rec["hits"]), "by_poi_index": hits_by},
                    "pois_with_the_same_name": same_name,
                    "note": ("なじみの場所の上位 3 に多い POI 5 つを改変の対象と見立てた例。番号の照合=その POI を文に載せた体・名の"
                             "照合=同じ名の別の POI(チェーン)を載せた体も数える(名は記録に写さない)")}
    doc["example_synthetic"] = example()
    text = json.dumps(doc, ensure_ascii=False, indent=1) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8", newline="\n")
    print(text[:4000])
    return 0


if __name__ == "__main__":
    sys.exit(main())
