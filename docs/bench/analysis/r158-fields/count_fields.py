# -*- coding: utf-8 -*-
"""R-158(返事その 9 §5-7)住民が自分について知っている事実の要素: 世界資産の欄の総ざらいと種別ごとの埋まり。

count-347 の ``count_a07.py``(``docs/bench/analysis/count-347/talk-kinds-tape/``)の表を広げる。読むのは
W16・W17・W20・W21 の parquet の欄の名・型・行の数と、種別(``AgentKind`` の 9 値)ごとの集計だけ。
住民の文(``w21_persona_*`` の ``text``・``text_original``)の列は読まない。個々の住民の値は出さない
(出すのは型・異なる値の数・埋まっている割合・語ごとの割合・中央値などの要約だけ)。

母集団は 2 つ: 全体(``w16_population.parquet`` の全行)と、標準のラン(5,000 体・seed 1)が抽出する体
(``world.facts.population_reader.load_population(world, n=5000, seed=1)`` で作り直す。count-347 の
ランの種別の数と突き合わせる)。

使い方: python count_fields.py --world <世界資産の置き場> --out <数の JSON>
重さ: parquet を読むだけ(最大の表は W17 の約 300 万行・W20 の約 240 万行・関係の約 150 万行)。ランは回さない。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq

KINDS = ("COMMUTER", "VISITOR", "WORKER", "RESIDENT", "DISPATCHER", "STUDENT", "REGULAR_VISITOR",
         "FOREIGN_VISITOR", "CREW")
#: count-347 の a07_counts.json の run の種別の数(抽出の作り直しの突き合わせ)
RUN_KIND_COUNTS_347 = {"COMMUTER": 2254, "VISITOR": 765, "WORKER": 128, "RESIDENT": 431, "DISPATCHER": 24,
                       "STUDENT": 435, "REGULAR_VISITOR": 261, "FOREIGN_VISITOR": 228, "CREW": 474}
#: 読まない列(住民の文)
TEXT_COLUMNS = {"text", "text_original"}
#: 語ごとの割合を出す列(語の種類が少ないもの)。値の数が多い列は異なる値の数だけ出す
MAX_VOCAB = 40
ACTIVITY_WORDS = ("就寝", "支度", "移動", "乗車", "勤務", "通学", "食事", "買物", "娯楽", "用事", "交流", "休憩")
PLACE_WORDS_W17 = ("自宅", "職場", "学校", "駅", "飲食店", "物販店", "公園", "娯楽施設", "宿泊施設", "医療施設",
                   "路上", "域外")
PURPOSE_NAMES = ("勤務", "通学", "業務", "私事", "居住", "職務")
COMMIT_WORDS = ("なし", "勤務", "授業")


def filled(col: np.ndarray, typ: str) -> np.ndarray:
    """埋まっている印(count_a07.py と同じ定義: 整数=0 以上・文字列=空でない・真偽=真・小数=NaN でない)。"""
    if typ.startswith("bool"):
        return col.astype(bool)
    if typ.startswith(("int", "uint")):
        return col >= 0
    if typ in ("float", "double"):
        return ~np.isnan(col.astype(np.float64))
    if typ.startswith("list"):
        return np.array([x is not None and len(x) > 0 for x in col], dtype=bool)
    return np.array([x is not None and str(x) != "" for x in col], dtype=bool)


def read(path: Path, cols: list[str] | None = None) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    names = pq.read_schema(path).names
    want = [c for c in (cols or names) if c not in TEXT_COLUMNS]
    t = pq.read_table(path, columns=want)
    out, typ = {}, {}
    for name in t.column_names:
        typ[name] = str(t.schema.field(name).type)
        c = t.column(name)
        if typ[name].startswith(("string", "list", "struct")):
            out[name] = np.array(c.to_pylist(), dtype=object)
        else:
            out[name] = c.to_numpy(zero_copy_only=False)
    return out, typ


def by_kind(values: np.ndarray, kind: np.ndarray, sel: np.ndarray, fn) -> dict[str, Any]:
    return {kn: (fn(values[sel & (kind == k)]) if (sel & (kind == k)).any() else None) for k, kn in enumerate(KINDS)}


def share_true(v: np.ndarray) -> float:
    return round(float(np.mean(v)), 4)


def vocab_share(v: np.ndarray) -> dict[str, float]:
    s = np.asarray([("" if x is None else str(x)) for x in v], dtype=object)
    u, c = np.unique(s, return_counts=True)
    order = np.argsort(-c)
    return {(str(u[i]) if u[i] != "" else "(空)"): round(float(c[i] / s.size), 4) for i in order}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    W = Path(a.world)
    doc: dict[str, Any] = {"about": "R-158 欄の総ざらい(値は出さない=型・異なる値の数・埋まり・語ごとの割合・要約だけ)"}

    # ---- A. 表の一覧(欄の名・型・行の数) ----
    inv = {}
    for f in sorted(W.glob("*.parquet")):
        if not f.name.startswith(("w16_", "w17_", "w20_", "w21")):
            continue
        s = pq.read_schema(f)
        inv[f.name] = {"rows": pq.read_metadata(f).num_rows,
                       "columns": {n: str(s.field(n).type) for n in s.names}}
    doc["inventory"] = inv

    # ---- 母集団と標準のランの抽出 ----
    pop, ptyp = read(W / "w16_population.parquet")
    aid = pop["agent_id"].astype(np.int64)
    kind = pop["kind"].astype(np.int64)
    n_all = aid.size
    from shibuya.world.facts.population_reader import load_population  # 遅延(読み口だけ)
    sample = load_population(W, n=5000, seed=1)
    run_ids = np.asarray(sample.source_agent_id, dtype=np.int64)
    order = np.argsort(aid)
    pos = order[np.searchsorted(aid[order], run_ids)]
    in_run = np.zeros(n_all, dtype=bool)
    in_run[pos] = True
    all_sel = np.ones(n_all, dtype=bool)
    run_counts = {kn: int((in_run & (kind == k)).sum()) for k, kn in enumerate(KINDS)}
    doc["kind_counts"] = {"all": {kn: int((kind == k).sum()) for k, kn in enumerate(KINDS)}, "run": run_counts,
                          "run_matches_count347": run_counts == RUN_KIND_COUNTS_347}
    sels = (("all", all_sel), ("run", in_run))

    def fill_table(cols: dict[str, np.ndarray], typ: dict[str, str], hit: np.ndarray, rows_of: np.ndarray,
                   skip: set[str]) -> dict[str, Any]:
        """表の各列を体に結び、種別ごとの埋まりを出す(結べない体は埋まっていない)。"""
        out: dict[str, Any] = {}
        for name, col in cols.items():
            if name in skip:
                continue
            ft = filled(col, typ[name])
            f = np.zeros(n_all, dtype=bool)
            f[hit] = ft[rows_of[hit]]
            nd = -1 if typ[name].startswith(("list", "struct")) else int(len(set(col.tolist())))
            out[name] = {"type": typ[name], "n_distinct_table": nd,
                         **{"fill_" + sn: by_kind(f, kind, sel, share_true) for sn, sel in sels}}
        return out

    def join(keys_body: np.ndarray, keys_table: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        o = np.argsort(keys_table, kind="stable")
        sk = keys_table[o]
        i = np.clip(np.searchsorted(sk, keys_body), 0, max(0, sk.size - 1))
        hit = (keys_body >= 0) & (sk[i] == keys_body) if sk.size else np.zeros(keys_body.size, dtype=bool)
        return hit, o[i]

    # ---- B. 埋まり(体に結べる表の全部の列) ----
    fills: dict[str, Any] = {}
    ident = np.arange(n_all)
    fills["w16_population"] = fill_table(pop, ptyp, np.ones(n_all, dtype=bool), ident, {"agent_id", "kind"})
    hh16 = pop["household_id"].astype(np.int64)
    pid = pop["w21_person_id"].astype(np.int64)
    for fname, key, body_key in (("w16_households.parquet", "household_id", hh16),
                                 ("w21_households.parquet", "household_id", hh16),
                                 ("w21_money_households.parquet", "household_id", hh16),
                                 ("w21_people.parquet", "person_id", pid),
                                 ("w21_persons.parquet", "person_id", pid),
                                 ("w21_money.parquet", "person_id", pid),
                                 ("w21_persona_long.parquet", "person_id", pid),
                                 ("w21c_status_split.parquet", "person_id", pid)):
        t, ty = read(W / fname)
        hit, rows_of = join(body_key, t[key].astype(np.int64))
        fills[fname.replace(".parquet", "")] = {
            "joined_" + sn: by_kind(hit, kind, sel, share_true) for sn, sel in sels}
        fills[fname.replace(".parquet", "")]["columns"] = fill_table(t, ty, hit, rows_of, {key})
    doc["fill"] = fills

    # ---- C. 語ごとの割合(全体・種別ごと)と数の要約 ----
    dist: dict[str, Any] = {}
    age = pop["age"].astype(np.int64)
    age10 = np.where(age >= 70, "70+", np.char.add((age // 10 * 10).astype(str), "代"))
    dist["age10"] = by_kind(age10.astype(object), kind, all_sel, vocab_share)
    dist["sex"] = by_kind(pop["sex"].astype(np.int64).astype(str).astype(object), kind, all_sel, vocab_share)
    dist["purpose"] = by_kind(np.asarray([PURPOSE_NAMES[p] if 0 <= p < 6 else str(p)
                                          for p in pop["purpose"].astype(np.int64)], dtype=object),
                              kind, all_sel, vocab_share)
    for c in ("duty_role", "persona_occupation", "persona_employment", "is_foreign"):
        dist["w16." + c] = by_kind(pop[c].astype(object), kind, all_sel, vocab_share)
    dist["w16.industry_key.n_distinct"] = by_kind(pop["industry_key"], kind, all_sel,
                                                  lambda v: int(len(set(v.tolist()))))

    def joined_vocab(fname: str, key: str, body_key: np.ndarray, cols: list[str]) -> None:
        t, ty = read(W / fname, [key, *cols])
        hit, rows_of = join(body_key, t[key].astype(np.int64))
        for c in cols:
            v = np.full(n_all, "(結べない)", dtype=object)
            v[hit] = t[c][rows_of[hit]]
            if ty[c].startswith(("int", "uint", "float", "double")) and c not in ("size", "head_sex"):
                vv = v.copy()
                dist[f"{fname.split('.')[0]}.{c}.summary"] = by_kind(
                    vv, kind, all_sel & hit,
                    lambda x: {"p10": float(np.nanpercentile(x.astype(float), 10)),
                               "median": float(np.nanmedian(x.astype(float))),
                               "p90": float(np.nanpercentile(x.astype(float), 90)),
                               "share_nan_or_negative": round(float(np.mean(~(x.astype(float) >= 0))), 4)})
                continue
            nd = len(set(t[c].tolist()))
            if nd > MAX_VOCAB:
                dist[f"{fname.split('.')[0]}.{c}.n_distinct"] = by_kind(
                    v[hit], kind[hit], np.ones(int(hit.sum()), dtype=bool), lambda x: int(len(set(x.tolist()))))
                continue
            dist[f"{fname.split('.')[0]}.{c}"] = by_kind(v, kind, all_sel, vocab_share)

    joined_vocab("w21_people.parquet", "person_id", pid,
                 ["occupation_major", "labour_status", "employment_status", "commute_mode", "relation", "persona_kind",
                  "origin_muni", "residence_years", "known_places"])
    joined_vocab("w21_persons.parquet", "person_id", pid,
                 ["marital", "relation", "residence_period", "school_kind", "school_place", "workplace_kind",
                  "nationality_group"])
    joined_vocab("w21_households.parquet", "household_id", hh16,
                 ["family_type", "family_group", "tenure", "building_type", "size"])
    joined_vocab("w16_households.parquet", "household_id", hh16, ["size"])
    joined_vocab("w21_money.parquet", "person_id", pid, ["kind", "wallet_cash", "card_holding", "account_holding",
                                                         "money_basis"])
    joined_vocab("w21_persona_long.parquet", "person_id", pid, ["first_language", "lang", "tipi_extraversion"])
    doc["distribution_all"] = dist

    # ---- D. 関係(初期)の数: 家族と職場 ----
    rel, _ = read(W / "w21_relations_initial.parquet", ["u", "kind"])
    ru = rel["u"].astype(np.int64)
    rk = rel["kind"].astype(np.int64)
    rels: dict[str, Any] = {}
    for kcode, kname in ((1, "household"), (2, "work")):
        uu, cc = np.unique(ru[rk == kcode], return_counts=True)
        hit, rows_of = join(pid, uu)
        deg = np.where(hit, cc[rows_of], 0)
        rels[kname] = {"share_with_any_" + sn: by_kind(deg > 0, kind, sel, share_true) for sn, sel in sels}
        rels[kname]["median_degree_all_if_any"] = by_kind(deg, kind, all_sel & (deg > 0),
                                                          lambda x: float(np.median(x)))
    doc["relations_initial"] = rels

    # ---- E. 予定の表(W17 の日課・W20 のカレンダー) ----
    s17, _ = read(W / "w17_schedule.parquet", ["agent_id", "day", "activity_code", "place_kind"])
    a17 = s17["agent_id"].astype(np.int64)
    sched: dict[str, Any] = {"w17_days_present": sorted(set(s17["day"].astype(int).tolist()))}

    def any_by_body(mask: np.ndarray) -> np.ndarray:
        u = np.unique(a17[mask])
        hit, _ = join(aid, u)
        return hit

    sched["w17_share_with_activity_run"] = {
        ACTIVITY_WORDS[c]: by_kind(any_by_body(s17["activity_code"].astype(int) == c), kind, in_run, share_true)
        for c in range(len(ACTIVITY_WORDS))}
    sched["w17_share_with_place_run"] = {
        PLACE_WORDS_W17[c]: by_kind(any_by_body(s17["place_kind"].astype(int) == c), kind, in_run, share_true)
        for c in range(len(PLACE_WORDS_W17))}
    s20, _ = read(W / "w20_calendar_1a.parquet", ["agent_id", "week", "weekday", "commit"])
    sched["w20_weeks_present"] = sorted(set(s20["week"].astype(int).tolist()))
    sched["w20_weekdays_present"] = sorted(set(s20["weekday"].astype(int).tolist()))
    a20 = s20["agent_id"].astype(np.int64)
    for c in (1, 2):
        u = np.unique(a20[s20["commit"].astype(int) == c])
        hit, _ = join(aid, u)
        sched[f"w20_share_with_commit_{COMMIT_WORDS[c]}_run"] = by_kind(hit, kind, in_run, share_true)
    doc["schedule"] = sched

    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"n_population": n_all, "n_run": int(in_run.sum()),
                      "run_matches_count347": doc["kind_counts"]["run_matches_count347"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
