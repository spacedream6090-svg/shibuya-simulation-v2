"""1-0: 「同じ列を複数の系が書いている所」の一覧(ユーザーの条件 2026-10-13・草案 §1-5 の 28 列・27 行を実装の宣言から作り直す)。

2 つの見方を並べる:

- **宣言**(上限): ``engine.systems.table.SYSTEMS`` の ``writes.soa``(resolve の口の静的な閉包)と ``writes.paths``(外の状態の
  道筋の宣言を状態台帳の項目に当てた)。閉包は上限なので、本当は書かない系も入る(草案〔親の注〕(3))。
- **観測**: 系ごとの全欄の差(``probe_run.py`` の 1-0 のランの JSON・6 構成・1,000 体・全 tick)で、実際に値を変えた系。

使い方(リポの根で): ``python $D/multi_writers.py <probe の JSON …> --out $D/multi-writer-columns``(.json と .md を書く)。
絶対パスは書かない。
"""

from __future__ import annotations

import argparse
import fnmatch
import json
from collections import defaultdict
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("probes", nargs="*")
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    from shibuya.engine import state_ledger as SL
    from shibuya.engine.systems.table import SYSTEMS

    order = [s.name for s in SYSTEMS]
    pos = {n: i for i, n in enumerate(order)}
    soa_rows = {f"{r.place}.{r.name}": r for r in SL.LEDGER if r.is_soa}
    items = [(r.key, it, r) for r in SL.external_rows() for it in r.items]
    decl_soa: dict[str, list[str]] = defaultdict(list)
    decl_ext: dict[str, list[str]] = defaultdict(list)
    for s in SYSTEMS:
        if s.name == "build":
            continue  # 組み立ては全部を書く(守らない)
        for c in sorted(s.writes.soa):
            decl_soa[c].append(s.name)
        for key, it, _r in items:
            k = f"{key}:{it}"
            if any(fnmatch.fnmatchcase(k, p) or k == p for p in s.writes.paths):
                decl_ext[k].append(s.name)
    obs_soa: dict[str, set[str]] = defaultdict(set)
    obs_ext: dict[str, set[str]] = defaultdict(set)
    configs = []
    for f in args.probes:
        d = json.loads(Path(f).read_text(encoding="utf-8"))
        configs.append(d.get("config"))
        for _t, sname, _dg, keys in d["entries"]:
            for k in keys:
                if k.startswith(("stats.", "buffers.", "scratch.")):
                    continue
                (obs_ext if ":" in k else obs_soa)[k].add(sname)

    def srt(xs):
        return sorted(set(xs), key=lambda n: pos.get(n, 999))

    rows_soa = []
    for c in sorted(set(decl_soa) | set(obs_soa)):
        r = soa_rows.get(c)
        rows_soa.append({"key": c, "axis1": r.behavior if r else "?", "declared": srt(decl_soa.get(c, [])),
                         "observed": srt(obs_soa.get(c, set()))})
    rows_ext = []
    for k in sorted(set(decl_ext) | set(obs_ext), key=lambda x: (int(x.split(":")[0][1:]), x)):
        key = k.split(":")[0]
        r = next((r for kk, _it, r in items if kk == key), None)
        rows_ext.append({"key": k, "axis1": r.behavior if r else "?", "declared": srt(decl_ext.get(k, [])),
                         "observed": srt(obs_ext.get(k, set()))})
    multi_soa_decl = [r for r in rows_soa if len(r["declared"]) >= 2]
    multi_soa_obs = [r for r in rows_soa if len(r["observed"]) >= 2]
    multi_ext_decl = [r for r in rows_ext if len(r["declared"]) >= 2]
    multi_ext_obs = [r for r in rows_ext if len(r["observed"]) >= 2]
    # 行(鍵)の単位の観測(草案 §1-5 の「27 行」と同じ単位)
    by_row_obs: dict[str, set[str]] = defaultdict(set)
    for r in rows_ext:
        by_row_obs[r["key"].split(":")[0]] |= set(r["observed"])
    multi_rows_obs = {k: srt(v) for k, v in sorted(by_row_obs.items(), key=lambda kv: int(kv[0][1:])) if len(v) >= 2}
    doc = {
        "format": "shibuya.bench/1-0/multi-writer/1",
        "order": order,
        "probe_configs": configs,
        "counts": {"soa_declared_multi": len(multi_soa_decl), "soa_observed_multi": len(multi_soa_obs),
                   "ext_paths_declared_multi": len(multi_ext_decl), "ext_paths_observed_multi": len(multi_ext_obs),
                   "ext_rows_observed_multi": len(multi_rows_obs)},
        "soa": rows_soa, "ext": rows_ext, "ext_rows_observed_multi": multi_rows_obs,
    }
    out = Path(args.out)
    out.with_suffix(".json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                        newline="\n")
    md = ["# 複数の系が書く列の一覧(1-0)", "",
          "- ユーザーの条件(2026-10-13): 同じ列を複数の区間(系)が書いている所を、後で話題ごとにまとめ直すときの課題として記録する。",
          "- 作り方: `multi_writers.py`(このフォルダ)。**宣言**=系の表 `SYSTEMS` の書く欄(SoA は resolve の口の静的な閉包=上限・"
          "外の状態は道筋の宣言を台帳の項目に当てた)。**観測**=系ごとの全欄の差(1-0 のラン・"
          f"{len(set(configs))} 構成・ラン {len(configs)} 本・1,000 体・seed 1・全 tick: "
          f"{', '.join(dict.fromkeys(c for c in configs if c))})で実際に値を変えた系。"
          "段 FIX の後は段 DEF の測り(`1-0_probe`)と段 FIX の測り(`1-0_probe_fix2`=scratch の中身と digest できない"
          "外の道筋の代わりの digest つき・1 日)の和。",
          "- 並びは呼ぶ順(表の順)。後の系が前の系の書いた値を上書きする=系の順を入れ替えると結果が動く(草案 §3-3 の 12)。",
          f"- 数: SoA の列で 2 系以上が書く=宣言 {len(multi_soa_decl)}・観測 {len(multi_soa_obs)}。外の状態の道筋で 2 系以上="
          f"宣言 {len(multi_ext_decl)}・観測 {len(multi_ext_obs)}(行の単位の観測 {len(multi_rows_obs)})。"
          "草案 §1-5 の測り(HEAD・6 構成・窓の tick)は SoA 28 列・外の行 27。", "",
          "## SoA の列(観測で 2 系以上)", "", "| 列 | 軸 1 | 観測の書き手(順) | 宣言の書き手(閉包=上限) |", "|---|---|---|---|"]
    for r in multi_soa_obs:
        md.append(f"| `{r['key']}` | {r['axis1']} | {' → '.join(r['observed'])} | {' → '.join(r['declared'])} |")
    md += ["", "## SoA の列(宣言だけで 2 系以上・観測では 1 系以下)", "",
           "| 列 | 軸 1 | 観測 | 宣言 |", "|---|---|---|---|"]
    for r in multi_soa_decl:
        if len(r["observed"]) < 2:
            md.append(f"| `{r['key']}` | {r['axis1']} | {' → '.join(r['observed']) or '—'} | {' → '.join(r['declared'])} |")
    md += ["", "## 外の状態(行の単位・観測で 2 系以上)", "", "| 行 | 観測の書き手(順) |", "|---|---|"]
    for k, v in multi_rows_obs.items():
        md.append(f"| {k} | {' → '.join(v)} |")
    md += ["", "## 外の状態(道筋の単位・観測で 2 系以上)", "", "| 道筋 | 軸 1 | 観測の書き手(順) | 宣言の書き手 |",
           "|---|---|---|---|"]
    for r in multi_ext_obs:
        md.append(f"| `{r['key']}` | {r['axis1']} | {' → '.join(r['observed'])} | {' → '.join(r['declared'])} |")
    out.with_suffix(".md").write_text("\n".join(md) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps(doc["counts"], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
