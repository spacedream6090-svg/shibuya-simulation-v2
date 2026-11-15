# -*- coding: utf-8 -*-
"""count-347 talk-kinds-tape: A07(記録 2-53)種別ごとの事実を数える(返事その 8 §6-1 の 4)。

世界資産(W16 の母集団=差し替えの版・W21 の人・W16 の持ち場の表・参考に W17 の日課と W20 のカレンダー)を読み、
9 種別(``agents.state.AgentKind``)ごとに、事実の欄が埋まっている割合を出す。母集団は 2 つ:
全体(``w16_population.parquet`` の全行)と、標準のラン(5,000 体・seed 1)が抽出した体(``run_m10.py`` が控えた番号)。

出すのは欄の名・型・異なる値の数・埋まっている割合だけ(個々の住民の値は出さない)。

使い方: python count_a07.py --world <世界資産の置き場> --pop-json <抽出した番号の JSON> --out <数の JSON>
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


def _filled(col: np.ndarray, typ: str) -> np.ndarray:
    """埋まっている印(整数の番号=0 以上・文字列=空でない・真偽=真・小数=NaN でない)。"""
    if typ.startswith("bool"):
        return col.astype(bool)
    if typ.startswith(("int", "uint")):
        return col >= 0
    if typ in ("float", "double"):
        return ~np.isnan(col.astype(np.float64))
    if typ.startswith("list"):
        return np.array([x is not None and len(x) > 0 for x in col], dtype=bool)
    return np.array([x is not None and str(x) != "" for x in col], dtype=bool)


def _read(path: Path, cols: list[str] | None = None) -> tuple[dict[str, np.ndarray], dict[str, str]]:
    t = pq.read_table(path, columns=cols)
    out, typ = {}, {}
    for name in t.column_names:
        f = t.schema.field(name)
        typ[name] = str(f.type)
        c = t.column(name)
        if str(f.type).startswith(("string", "list", "struct")):
            out[name] = np.array(c.to_pylist(), dtype=object)
        else:
            out[name] = c.to_numpy(zero_copy_only=False)
    return out, typ


def _n_distinct(col: np.ndarray, typ: str) -> int:
    if typ.startswith(("list", "struct")):
        return -1
    return int(len(set(col.tolist())))


def table_rows(cols: dict[str, np.ndarray], typ: dict[str, str], kind: np.ndarray, sel: np.ndarray,
               skip: set[str]) -> dict[str, Any]:
    """欄 → {型・異なる値の数(全行)・種別ごとの埋まっている割合}。``sel`` は数える行の印。"""
    out: dict[str, Any] = {}
    for name, col in cols.items():
        if name in skip:
            continue
        fill = _filled(col, typ[name])
        row: dict[str, Any] = {"type": typ[name], "n_distinct_all": _n_distinct(col, typ[name])}
        per: dict[str, Any] = {}
        for k, kn in enumerate(KINDS):
            m = sel & (kind == k)
            n = int(m.sum())
            per[kn] = None if n == 0 else round(float(fill[m].mean()), 4)
        row["fill_by_kind"] = per
        out[name] = row
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--world", required=True)
    ap.add_argument("--pop-json", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    W = Path(a.world)

    pop, ptyp = _read(W / "w16_population.parquet")
    aid = pop["agent_id"].astype(np.int64)
    kind = pop["kind"].astype(np.int64)
    n_all = aid.size
    order = np.argsort(aid)
    run = json.loads(Path(a.pop_json).read_text(encoding="utf-8"))
    run_ids = np.asarray(run["source_agent_id"], dtype=np.int64)
    pos = order[np.searchsorted(aid[order], run_ids)]
    if not np.array_equal(aid[pos], run_ids):
        raise SystemExit("抽出の番号が母集団に無い")
    if not np.array_equal(kind[pos], np.asarray(run["kind"], dtype=np.int64)):
        raise SystemExit("抽出の種別が母集団と違う")
    in_run = np.zeros(n_all, dtype=bool)
    in_run[pos] = True
    all_sel = np.ones(n_all, dtype=bool)

    def kind_counts(sel: np.ndarray) -> dict[str, int]:
        return {kn: int((sel & (kind == k)).sum()) for k, kn in enumerate(KINDS)}

    doc: dict[str, Any] = {
        "about": "A07 種別ごとの事実(返事その 8 §6-1 の 4)。値は出さない(型・異なる値の数・埋まっている割合だけ)",
        "n_population": n_all, "n_run": int(in_run.sum()),
        "kind_counts": {"all": kind_counts(all_sel), "run": kind_counts(in_run)},
        "w16_population": {"all": table_rows(pop, ptyp, kind, all_sel, {"agent_id", "kind"}),
                           "run": table_rows(pop, ptyp, kind, in_run, {"agent_id", "kind"})},
    }
    # 目的(purpose)の値の割合(W16 の 6 語の表=build.pop.w16_population.PURPOSE_NAMES の索引)
    pur = pop["purpose"].astype(np.int64)
    doc["w16_purpose_share"] = {
        sname: {kn: ({str(p): round(float(((sel & (kind == k)) & (pur == p)).sum() / max(1, (sel & (kind == k)).sum())), 4)
                      for p in sorted(set(pur[sel & (kind == k)].tolist()))} if (sel & (kind == k)).any() else None)
                for k, kn in enumerate(KINDS)}
        for sname, sel in (("all", all_sel), ("run", in_run))}

    # ---- W21 の人(w21_person_id → person_id) ----
    pid = pop["w21_person_id"].astype(np.int64)
    has21 = pid >= 0
    doc["w21_linked_share"] = {
        sname: {kn: (round(float(has21[sel & (kind == k)].mean()), 4) if (sel & (kind == k)).any() else None)
                for k, kn in enumerate(KINDS)} for sname, sel in (("all", all_sel), ("run", in_run))}

    def join_person_table(fname: str, key: str = "person_id", cols: list[str] | None = None) -> dict[str, Any]:
        t, ty = _read(W / fname, cols)
        pk = t[key].astype(np.int64)
        o = np.argsort(pk)
        spk = pk[o]
        idx = np.searchsorted(spk, pid)
        idx = np.clip(idx, 0, max(0, spk.size - 1))
        hit = has21 & (spk[idx] == pid) if spk.size else np.zeros(n_all, dtype=bool)
        rows_of = o[idx]
        out: dict[str, Any] = {"rows": int(pk.size), "joined_all": int(hit.sum()), "joined_run": int((hit & in_run).sum())}
        cols_out: dict[str, Any] = {}
        for name, col in t.items():
            if name == key:
                continue
            fill_t = _filled(col, ty[name])
            fill = np.zeros(n_all, dtype=bool)
            fill[hit] = fill_t[rows_of[hit]]
            row: dict[str, Any] = {"type": ty[name], "n_distinct_table": _n_distinct(col, ty[name])}
            for sname, sel in (("all", all_sel), ("run", in_run)):
                row["fill_by_kind_" + sname] = {
                    kn: (round(float(fill[sel & (kind == k)].mean()), 4) if (sel & (kind == k)).any() else None)
                    for k, kn in enumerate(KINDS)}
            cols_out[name] = row
        out["columns"] = cols_out
        return out

    doc["w21_people"] = join_person_table("w21_people.parquet")
    doc["w21_persons"] = join_person_table("w21_persons.parquet")
    doc["w21_persona_short"] = join_person_table(
        "w21_persona_short.parquet", cols=["person_id", "version", "lang", "first_language", "lang_basis", "text",
                                           "text_status", "text_source", "chars", "named_poi", "named_org"])
    # W21c の段 10 の材料: 欄の名は agent_id だが中身は人の番号(下の id_matches の確かめ)=人の番号で引く
    doc["w21c_w20_attributes_by_person"] = join_person_table("w21c_w20_attributes.parquet", key="agent_id")
    # 開始前の経験(なじみの場所): 人ごとの行の数
    pp, _ = _read(W / "w21_prior_places.parquet", ["person_id"])
    ppk, ppn = np.unique(pp["person_id"].astype(np.int64), return_counts=True)
    i2 = np.clip(np.searchsorted(ppk, pid), 0, max(0, ppk.size - 1))
    pp_rows = np.where(has21 & (ppk[i2] == pid), ppn[i2], 0)
    doc["w21_prior_places_rows_per_person"] = {
        sname: {kn: ({"share_with_rows": round(float((pp_rows[sel & (kind == k)] > 0).mean()), 4),
                      "median_rows": float(np.median(pp_rows[sel & (kind == k)]))} if (sel & (kind == k)).any() else None)
                for k, kn in enumerate(KINDS)} for sname, sel in (("all", all_sel), ("run", in_run))}

    # ---- 体の番号で引く表(W16 の持ち場の表・W21c の段 10 の材料・W21 の権利・W17・W20) ----
    def by_agent(fname: str, key: str, cols: list[str] | None = None) -> dict[str, Any]:
        t, ty = _read(W / fname, cols)
        ak = t[key].astype(np.int64)
        uk, first = np.unique(ak, return_index=True)
        i3 = np.clip(np.searchsorted(uk, aid), 0, max(0, uk.size - 1))
        hit = uk[i3] == aid
        out: dict[str, Any] = {"rows": int(ak.size), "agents": int(uk.size),
                               "share_with_rows": {sname: {kn: (round(float(hit[sel & (kind == k)].mean()), 4)
                                                                if (sel & (kind == k)).any() else None)
                                                           for k, kn in enumerate(KINDS)}
                                                   for sname, sel in (("all", all_sel), ("run", in_run))}}
        rows_of = first[i3]
        cols_out = {}
        for name, col in t.items():
            if name == key:
                continue
            fill_t = _filled(col, ty[name])
            fill = np.zeros(n_all, dtype=bool)
            fill[hit] = fill_t[rows_of[hit]]
            cols_out[name] = {"type": ty[name], "n_distinct_table": _n_distinct(col, ty[name]),
                              "fill_by_kind_run": {kn: (round(float(fill[in_run & (kind == k)].mean()), 4)
                                                        if (in_run & (kind == k)).any() else None)
                                                   for k, kn in enumerate(KINDS)}}
        out["columns_first_row"] = cols_out
        return out

    doc["w16_duty_roster"] = by_agent("w16_duty_roster.parquet", "agent_id")
    doc["w21c_w20_attributes"] = by_agent("w21c_w20_attributes.parquet", "agent_id")
    doc["w21_rights_run"] = by_agent("w21_rights_run.parquet", "holder_agent_id",
                                     ["holder_agent_id", "object_kind", "kind", "block"])
    doc["w17_schedule"] = by_agent("w17_schedule.parquet", "agent_id",
                                   ["agent_id", "day", "start_min", "end_min", "activity_code", "place_kind",
                                    "target_cell", "block_kind"])
    doc["w20_calendar_1a"] = by_agent("w20_calendar_1a.parquet", "agent_id",
                                      ["agent_id", "commit", "start_min", "end_min", "place_kind", "target_cell",
                                       "certainty", "recurrence"])
    # 日課とカレンダーは体ごとに複数行=「その条件の行を 1 つでも持つ体の割合」と「体あたりの行の数の中央値」
    def per_agent_any(fname: str, cols: list[str], conds: dict[str, Any]) -> dict[str, Any]:
        t, _ = _read(W / fname, cols)
        ak = t["agent_id"].astype(np.int64)
        uk, cnt = np.unique(ak, return_counts=True)
        i5 = np.clip(np.searchsorted(uk, aid), 0, max(0, uk.size - 1))
        hit = uk[i5] == aid
        rows = np.where(hit, cnt[i5], 0)
        out: dict[str, Any] = {"median_rows_per_agent_run": {
            kn: (float(np.median(rows[in_run & (kind == k)])) if (in_run & (kind == k)).any() else None)
            for k, kn in enumerate(KINDS)}}
        for cname, fn in conds.items():
            m = fn(t)
            have = np.zeros(n_all, dtype=bool)
            u2 = np.unique(ak[m])
            i6 = np.clip(np.searchsorted(u2, aid), 0, max(0, u2.size - 1))
            have = (u2.size > 0) & (u2[i6] == aid) if u2.size else have
            out[cname] = {kn: (round(float(have[in_run & (kind == k)].mean()), 4) if (in_run & (kind == k)).any() else None)
                          for k, kn in enumerate(KINDS)}
        return out

    doc["w17_schedule_per_agent"] = per_agent_any(
        "w17_schedule.parquet", ["agent_id", "target_cell", "start_min"],
        {"share_any_target_cell": lambda t: t["target_cell"] >= 0, "share_any_start_min": lambda t: t["start_min"] >= 0})
    doc["w20_calendar_1a_per_agent"] = per_agent_any(
        "w20_calendar_1a.parquet", ["agent_id", "start_min", "target_cell"],
        {"share_any_timed_commit": lambda t: t["start_min"] >= 0, "share_any_target_cell": lambda t: t["target_cell"] >= 0})
    # W21c の段 10 の材料の番号の空間(体の番号か人の番号か)
    wa, _ = _read(W / "w21c_w20_attributes.parquet", ["agent_id"])
    wk = np.unique(wa["agent_id"].astype(np.int64))
    i7 = np.clip(np.searchsorted(wk, pid), 0, max(0, wk.size - 1))
    doc["w21c_w20_attributes"]["id_matches_w21_person_id_run"] = int((in_run & has21 & (wk[i7] == pid)).sum())
    i8 = np.clip(np.searchsorted(wk, aid), 0, max(0, wk.size - 1))
    doc["w21c_w20_attributes"]["id_matches_population_agent_id_run"] = int((in_run & (wk[i8] == aid)).sum())
    # 持ち場の表の番号が母集団の同じ体か(種別・年齢・男女の一致)
    dr, _ = _read(W / "w16_duty_roster.parquet", ["agent_id", "kind", "age", "sex"])
    dk = dr["agent_id"].astype(np.int64)
    i4 = np.clip(np.searchsorted(aid[order], dk), 0, n_all - 1)
    p4 = order[i4]
    same = (aid[p4] == dk) & (kind[p4] == dr["kind"].astype(np.int64)) & (pop["age"][p4].astype(np.int64) == dr["age"].astype(np.int64)) \
        & (pop["sex"][p4].astype(np.int64) == dr["sex"].astype(np.int64))
    doc["w16_duty_roster"]["id_matches_population_kind_age_sex"] = int(same.sum())
    Path(a.out).write_text(json.dumps(doc, ensure_ascii=False, indent=1, sort_keys=True), encoding="utf-8")
    print(json.dumps({"n_population": n_all, "n_run": int(in_run.sum())}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
