# -*- coding: utf-8 -*-
"""seed の交換可能性の検査(D-83 ⑦・第217)— 「seed 以外は同一構成か」を機械で確かめる。

小アンサンブル(3 seed)+ fair score が正当化できる唯一の枠(L-B 答申)であり、その前提は
**seed 群が交換可能**=構成・母集団・世界・規則が同一で、違うのは乱数列だけ、ということ。
本ツールは各 seed の ``checkpoints.json``(``shibuya.cli/checkpoints/1``)を並べ、

1. ``n_agents``/``ticks``/checkpoint の tick 列が一致する(**必須**)
2. manifest(入れ子を ``a.b.c`` に平坦化)の差を 3 種に分ける:
   **許容**(seed 由来で違って当然: ``fleet.cache_salt`` 等)/
   **宣言済み同値**(``--equivalent key=v1|v2:理由`` で親が根拠つきに宣言したもの。例 ``intent_mode=None|vocab``
   = AB7 以後の既定名の変更で挙動は同一)/ **未説明**(1 件でもあれば FAIL)
3. 母集団・世界・日課のハッシュが seed 間で同一かを**報告**(同一でも別でも可。同一=母集団は seed に依らない
   =交換可能性はより強い。別なら「母集団の抽出が seed に依る」ことを事前登録に書く)
4. 任意で ``occupancy.npz`` を渡すと 00 時の 5 エリア合計が seed 間で一致するか(初期配置の同一性)を報告

holdout には触らない。出力は JSON(既存ファイルへは書かない)。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Mapping, Sequence

SCHEMA = "shibuya.tools.c7/seed_exchangeability/1"
#: seed が違えば違って当然の欄(平坦化キー)。ここに無い差は「宣言済み同値」か「未説明」。
ALLOWED_DIFF: frozenset[str] = frozenset({
    "seed", "run_id", "final_hash",
    "manifest.fleet.cache_salt",   # salt は run_id/seed から作る(C6-a)
    "manifest.fleet.run_id",
})
#: 一致が必須の欄(違えば構成が違う=FAIL)。
MUST_MATCH: tuple[str, ...] = ("n_agents", "ticks", "schema")
HASH_KEYS: tuple[str, ...] = ("population_hash", "schedule_hash", "world_hash", "agents_hash")


def flatten(d: Mapping[str, Any], prefix: str = "") -> dict[str, Any]:
    """入れ子 dict を ``a.b.c`` に平坦化(list は JSON 文字列で 1 値扱い)。"""
    out: dict[str, Any] = {}
    for k, v in d.items():
        key = f"{prefix}{k}"
        if isinstance(v, Mapping):
            out.update(flatten(v, key + "."))
        elif isinstance(v, list):
            out[key] = json.dumps(v, ensure_ascii=False, sort_keys=True)
        else:
            out[key] = v
    return out


def parse_equivalents(items: Sequence[str] | None) -> dict[str, dict[str, Any]]:
    """``key=v1|v2|...:理由`` → {key: {"values": {...}, "reason": str}}。値 ``None`` は JSON null と同一視。"""
    out: dict[str, dict[str, Any]] = {}
    for it in items or ():
        key, _, rest = it.partition("=")
        vals, _, reason = rest.partition(":")
        if not key or not vals or not reason:
            raise SystemExit(f"--equivalent は key=v1|v2:理由 の形: {it!r}")
        out[key] = {"values": {v.strip() for v in vals.split("|")}, "reason": reason.strip()}
    return out


def _norm(v: Any) -> str:
    return "None" if v is None else str(v)


def compare(docs: Sequence[Mapping[str, Any]], labels: Sequence[str],
            equivalents: Mapping[str, Mapping[str, Any]] | None = None) -> dict[str, Any]:
    """純関数。checkpoints.json の dict を N 本受けて判定 dict を返す。"""
    if len(docs) < 2:
        raise ValueError("seed は 2 本以上")
    equivalents = dict(equivalents or {})
    flats = [flatten({k: v for k, v in d.items() if k != "checkpoints"}) for d in docs]
    keys = sorted(set().union(*[set(f) for f in flats]))
    must_fail = [k for k in MUST_MATCH if len({_norm(f.get(k)) for f in flats}) > 1]
    allowed, declared, unexplained = [], [], []
    for k in keys:
        vals = [_norm(f.get(k)) for f in flats]
        if len(set(vals)) <= 1:
            continue
        row = {"key": k, "values": dict(zip(labels, vals))}
        if k in ALLOWED_DIFF:
            allowed.append(row)
        elif k in equivalents and set(vals) <= set(equivalents[k]["values"]):
            row["reason"] = equivalents[k]["reason"]; declared.append(row)
        else:
            unexplained.append(row)
    # checkpoint の tick 列とハッシュ
    ticks = [[c.get("tick") for c in d.get("checkpoints", [])] for d in docs]
    ticks_match = all(t == ticks[0] for t in ticks)
    hashes: dict[str, Any] = {}
    if ticks_match and ticks[0]:
        for hk in HASH_KEYS:
            per_tick = []
            for i in range(len(ticks[0])):
                vals = {_norm(d["checkpoints"][i].get(hk)) for d in docs}
                per_tick.append(len(vals) == 1)
            hashes[hk] = {"identical_all_ticks": all(per_tick), "identical_by_tick": per_tick}
    ok = not must_fail and not unexplained and ticks_match
    return {
        "schema": SCHEMA,
        "labels": list(labels),
        "n_seeds": len(docs),
        "seeds": [d.get("seed") for d in docs],
        "must_match_failures": must_fail,
        "checkpoint_ticks": ticks[0] if ticks_match else ticks,
        "checkpoint_ticks_match": ticks_match,
        "diff_allowed": allowed,
        "diff_declared_equivalent": declared,
        "diff_unexplained": unexplained,
        "hash_identity": hashes,
        "population_seed_independent": hashes.get("population_hash", {}).get("identical_all_ticks"),
        "exchangeable": ok,
        "note": ("交換可能=seed 以外の構成差が無い(未説明の差 0・必須欄一致・tick 列一致)。母集団ハッシュの同一性は"
                 "報告のみ(同一なら母集団は seed に依らない・別なら抽出が seed に依ることを事前登録に書く)。"),
    }


def hour0_equality(occupancy_paths: Mapping[str, str], world: str = "data/world/v2",
                   axes: str = "tools/c7/area_axes_v0.json") -> dict[str, Any]:
    """任意: 00 時の 5 エリア合計(初期配置)が seed 間で一致するか。"""
    import numpy as np
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import seed_ensemble as se  # noqa: E402
    tables = se.load_tables(occupancy_paths, world, axes)
    rows = {k: np.asarray(t)[0].tolist() for k, t in tables.items()}
    first = next(iter(rows.values()))
    return {"hour0_area_totals": rows, "hour0_identical": all(np.allclose(v, first) for v in rows.values())}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--checkpoints", action="append", required=True, metavar="LABEL=checkpoints.json")
    ap.add_argument("--equivalent", action="append", metavar="key=v1|v2:理由",
                    help="親が根拠つきで同値と宣言する差(例 intent_mode=None|vocab:AB7 以後の既定名・挙動同一)")
    ap.add_argument("--occupancy", action="append", metavar="LABEL=occupancy.npz", help="任意: 00 時の初期配置の一致")
    ap.add_argument("--world", default="data/world/v2")
    ap.add_argument("--axes", default="tools/c7/area_axes_v0.json")
    ap.add_argument("--out", required=True, help="JSON の出力先(既存ファイルへは書かない)")
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists():
        print(f"refuse: {out} は既にある", file=sys.stderr); return 2
    labels, docs = [], []
    for it in a.checkpoints:
        label, _, path = it.partition("=")
        if not path:
            raise SystemExit(f"--checkpoints は LABEL=path の形: {it!r}")
        labels.append(label); docs.append(json.loads(Path(path).read_text(encoding="utf-8")))
    res = compare(docs, labels, parse_equivalents(a.equivalent))
    if a.occupancy:
        occ = dict(it.partition("=")[::2] for it in a.occupancy)
        res["hour0"] = hour0_equality(occ, a.world, a.axes)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(f"exchangeable={res['exchangeable']} seeds={res['seeds']} allowed={len(res['diff_allowed'])} "
          f"declared={len(res['diff_declared_equivalent'])} unexplained={len(res['diff_unexplained'])} "
          f"population_seed_independent={res['population_seed_independent']}"
          + (f" hour0_identical={res['hour0']['hour0_identical']}" if 'hour0' in res else ""))
    for r in res["diff_unexplained"]:
        print("  UNEXPLAINED", r["key"], r["values"])
    return 0 if res["exchangeable"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
