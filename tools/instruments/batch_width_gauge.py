# -*- coding: utf-8 -*-
"""batch_width_gauge — 第 3 期 3-2 **TM4 の既定の幅の試験の道具**(計算のまとめの幅 W の列 × salt の対)。

正典
    決定 10-12 §4-2 TM4(既定の幅は試験で決める・まとめ無しの時刻順を正解とし、差が salt のばらつきに入る一番大きい幅に
    する・目標はメッセージの遅れ 10 秒以下・60 秒は今との比較の足場・合格線は (f) 単調に減る かつ (g) 既定の幅の差が
    salt 間のばらつきの中・指標に遅刻と待ち合わせの成否を足す)。TM6 の T1(試験の道具)。記録
    ``docs/bench/analysis/wallbounce-1012/tm32/README.md`` §7。

正解(まとめ無しの時刻順)
    窓の幅を事象の時刻の最小の粒度まで細かくしたラン(それより細かくしても窓の中の事象の並びが変わらない)。T1 の世界の事象は
    刻みの事象だけ(粒度 60 秒)なので **今は W=60 が正解**(``--ref-width`` の既定)。T2 で粒度が細かくなったら正解の幅を
    その粒度に下げる(表の形はそのまま効く)。

段(どちらも src を変えない)
    ``run``: 幅の列(``--widths 60,30,10,5``)× salt の列(``--salts 1,2,3,4,5,6``=動きの seed・母集団の seed は
    ``--population-seed`` で固定=共通乱数)で ``shibuya.cli.run`` を子プロセスで 1 本ずつ回し(環境変数
    ``SHIBUYA_BATCH_WIDTH_S``)、final・呼数・行動の件数・manifest の ``batching`` を JSONL に 1 行ずつ書く。
    ``table``: 記録から幅ごとの表を作る(下の列)。合否は書かない(記述)。既定の幅の候補だけを書く。

表の列(幅ごと・指標ごと)
    - ``final_equal``: 正解の幅と final が同じ salt の割合(T1 では全部 1.0)。
    - 指標 m の ``diff``=salt の対の差 m(W) − m(正解) の平均・``salt_width``=正解の腕の salt 間の幅
      t(1 − α/2, n − 1)·s/√n(``tools/c7/salt_compare.paired_stats`` の ``width_base``)・``diff_over_width``・
      ``within``(|diff| ≤ salt_width=(g))。**(g) の幅に正解の腕の salt 間の SD を使うのは実装役の構成(未リサーチ=
      expedient)**: salt_compare の「幅」は対の差の SD(差が全部 0 の幅 0)なので、「salt 間のばらつきの中」の読みに
      各腕の幅 ``width_base`` を当てた。対の差の幅 ``paired_width`` も並べる。
    - (f) ``monotone``: |diff| が W を細かくするほど増えない(幅の大きい順に並べて単調非増加)。
    - 指標の既定: ``calls``(LLM の呼数)・``actions``(行動の件数)・``message_delay_max_s``(境目で届けた事象の遅れの最大
      [秒]=TM1 の電話・T1 の世界では 0)・``lateness``・``meeting``(**置き場**=遅刻と待ち合わせの成否。計る口がまだ無い
      =値は null・T2 以降に manifest の道筋を足す)。
    - 既定の幅の候補 ``default_candidate``: (g) を測れた指標で全部満たし final の一致も 1.0 の、一番大きい幅(記述)。

使い方(リポの根で・作業木の src)::

    python tools/instruments/batch_width_gauge.py run --widths 60,30,10,5 --salts 1,2,3,4,5,6 --agents 300 \\
        --out <作業用>/records.jsonl
    python tools/instruments/batch_width_gauge.py table --records <作業用>/records.jsonl --out-json <…>.json \\
        --out-md <…>.md

逐次ループ宣言: 幅 × salt のラン(子プロセス)・表は幅 × 指標(数十)。体の数に比例するループは無い。
絶対パスは出力に書かない。
"""

from __future__ import annotations

import argparse
import concurrent.futures as cf
import importlib.util
import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

HERE = Path(os.path.abspath(__file__)).parent
REPO = HERE.parent.parent
if str(REPO / "src") not in sys.path:  # pragma: no cover - 実行時の経路(時間の定数を core.time_consts から)
    sys.path.insert(0, str(REPO / "src"))

from shibuya.core.time_consts import STEP_SECONDS  # noqa: E402
SCHEMA = "shibuya.tools.instruments/batch_width_gauge/1"
#: 正解の幅の既定(T1 の世界の事象の時刻の粒度=刻みの幅 ``STEP_SECONDS``=60 秒)。
DEFAULT_REF_WIDTH = STEP_SECONDS
#: 指標(名 → manifest の中の道筋か、記録の欄。None=置き場)。
DEFAULT_METRICS: dict[str, str | None] = {
    "calls": "calls",
    "actions": "actions",
    "message_delay_max_s": "message_delay_max_s",
    "lateness": None,
    "meeting": None,
}
PLACEHOLDER_NOTE = "置き場(計る口がまだ無い=T2 以降に manifest の道筋を足す)"


def _salt_compare() -> Any:
    name = "salt_compare"
    if name in sys.modules:
        return sys.modules[name]
    spec = importlib.util.spec_from_file_location(name, REPO / "tools" / "c7" / "salt_compare.py")
    mod = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------- 表(純粋)
def metric_value(record: Mapping[str, Any], path: str | None) -> float | None:
    """記録の欄(``a.b`` で入れ子)から指標の値。道筋が None か値が無ければ None。"""
    if path is None:
        return None
    v: Any = record
    for k in path.split("."):
        if not isinstance(v, Mapping) or k not in v:
            return None
        v = v[k]
    return None if v is None else float(v)


def _num(v: float | None) -> float | None:
    return None if v is None or not math.isfinite(float(v)) else float(v)


def table(records: Sequence[Mapping[str, Any]], *, ref_width: int = DEFAULT_REF_WIDTH,
          metrics: Mapping[str, str | None] | None = None, alpha: float = 0.05) -> dict[str, Any]:
    """記録(1 行=1 本のラン: ``width_s``・``salt``・``final``・指標の欄)から幅ごとの表を作る。

    正解の幅の記録が無い salt は対にしない(その salt は数えない)。同じ (幅, salt) の記録が 2 つあれば ``ValueError``。
    """
    mets = dict(DEFAULT_METRICS if metrics is None else metrics)
    by: dict[tuple[int, Any], Mapping[str, Any]] = {}
    for r in records:
        key = (int(r["width_s"]), r["salt"])
        if key in by:
            raise ValueError(f"同じ幅と salt の記録が 2 つ: {key}")
        by[key] = r
    widths = sorted({w for w, _s in by}, reverse=True)
    if ref_width not in widths:
        raise ValueError(f"正解の幅 {ref_width} 秒の記録が無い(ある幅 {widths})")
    salts = sorted({s for w, s in by if w == ref_width}, key=str)
    sc = _salt_compare()
    rows: list[dict[str, Any]] = []
    for w in widths:
        paired = [s for s in salts if (w, s) in by]
        ref = [by[(ref_width, s)] for s in paired]
        arm = [by[(w, s)] for s in paired]
        row: dict[str, Any] = {
            "width_s": w, "is_ref": w == ref_width, "n_salts": len(paired),
            "final_equal": (sum(1 for a, b in zip(arm, ref) if a.get("final") == b.get("final")) / len(paired)
                            if paired else None),
            "metrics": {},
        }
        for name, path in mets.items():
            rv = [metric_value(x, path) for x in ref]
            av = [metric_value(x, path) for x in arm]
            if path is None or any(v is None for v in rv + av) or not paired:
                row["metrics"][name] = {"diff": None, "salt_width": None, "paired_width": None,
                                        "diff_over_width": None, "within": None,
                                        "note": PLACEHOLDER_NOTE if path is None else "値の無い記録がある"}
                continue
            st = sc.paired_stats(rv, av, alpha=alpha, family_size=1)
            diff = float(st["diff"])
            sw = _num(st.get("width_base"))
            within = None if sw is None else bool(abs(diff) <= sw)
            row["metrics"][name] = {
                "diff": diff, "salt_width": sw, "paired_width": _num(st.get("width")),
                "diff_over_width": (None if not sw else diff / sw), "within": within,
                "mean_ref": float(st["mean_base"]), "mean_arm": float(st["mean_arm"]),
            }
        rows.append(row)
    monotone: dict[str, bool | None] = {}
    for name in mets:
        seq = [r["metrics"][name]["diff"] for r in rows]
        if any(d is None for d in seq):
            monotone[name] = None
            continue
        ab = [abs(float(d)) for d in seq]  # 幅の大きい順=W を細かくする向き
        monotone[name] = all(ab[i + 1] <= ab[i] + 1e-12 for i in range(len(ab) - 1))
    cand = None
    for r in rows:  # 幅の大きい順
        ws = [m["within"] for m in r["metrics"].values() if m["within"] is not None]
        if r["final_equal"] == 1.0 and all(ws):
            cand = r["width_s"]
            break
    return {"schema": SCHEMA, "ref_width_s": ref_width, "alpha": alpha, "salts": [str(s) for s in salts],
            "metrics": {k: v for k, v in mets.items()}, "rows": rows, "monotone": monotone,
            "default_candidate_s": cand,
            "note": ("記述(合否は書かない)。(g)=|diff| ≤ salt_width(正解の腕の salt 間の幅=実装役の構成・expedient)・"
                     "(f)=|diff| が W を細かくするほど増えない。T1 の世界の事象の時刻の粒度は 60 秒=どの幅でも同じ")}


def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "中" if v else "外"
    if isinstance(v, float):
        return f"{v:.4g}"
    return str(v)


def markdown(tab: Mapping[str, Any]) -> str:
    """表の Markdown(幅の行 × 指標の列=差/salt の幅/中か)。"""
    names = list(tab["metrics"])
    head = "| 幅 W[秒] | salt の数 | final が同じ | " + " | ".join(
        f"{n} 差 / salt の幅 / (g)" for n in names) + " |"
    sep = "|" + "---|" * (3 + len(names))
    lines = [head, sep]
    for r in tab["rows"]:
        cells = []
        for n in names:
            m = r["metrics"][n]
            cells.append(f"{_fmt(m['diff'])} / {_fmt(m['salt_width'])} / {_fmt(m['within'])}")
        ref = "(正解)" if r["is_ref"] else ""
        lines.append(f"| {r['width_s']}{ref} | {r['n_salts']} | {_fmt(r['final_equal'])} | " + " | ".join(cells) + " |")
    lines.append("")
    lines.append("(f) 単調: " + "・".join(f"{n} {_fmt(v) if v is None else ('はい' if v else 'いいえ')}"
                                         for n, v in tab["monotone"].items()))
    lines.append(f"既定の幅の候補(記述): {_fmt(tab['default_candidate_s'])} 秒")
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------- ラン(子プロセス)
_CHILD = r"""
import json, sys
from shibuya import cli
from shibuya.core.time_consts import NS_PER_SECOND
kw = json.loads(sys.argv[1])
res = cli.run(**kw)
m = res.run_manifest_fields()
b = m.get("batching") or {}
au = dict(getattr(res, "action_usage", {}) or {})
print(json.dumps({"final": res.final_hash[:16], "calls": int(res.llm_calls),
                  "actions": int(sum(int(v) for v in au.values())), "batching": b,
                  "message_delay_max_s": (b.get("boundary_delay_ns_max", 0) or 0) / NS_PER_SECOND,
                  "run_kind": m.get("run_kind")}, ensure_ascii=False))
"""


def run_one(width_s: int, salt: int, *, kw: Mapping[str, Any], src: Path) -> dict[str, Any]:
    env = dict(os.environ, PYTHONIOENCODING="utf-8", SHIBUYA_BATCH_WIDTH_S=str(int(width_s)))
    env["PYTHONPATH"] = str(src) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    args = dict(kw, seed=int(salt))
    r = subprocess.run([sys.executable, "-c", _CHILD, json.dumps(args, ensure_ascii=False)], capture_output=True,
                       text=True, encoding="utf-8", env=env, cwd=str(REPO))
    if r.returncode != 0:
        return {"width_s": int(width_s), "salt": int(salt), "error": r.stderr[-2000:]}
    out = json.loads(r.stdout.strip().splitlines()[-1])
    out.update({"width_s": int(width_s), "salt": int(salt)})
    return out


def _ints(s: str) -> list[int]:
    return [int(x) for x in str(s).split(",") if x.strip()]


def cmd_run(a: argparse.Namespace) -> int:
    kw: dict[str, Any] = {"n_agents": a.agents, "world_dir": a.world, "population_seed": a.population_seed}
    kw.update(json.loads(a.kw or "{}"))
    src = Path(a.src).resolve() if a.src else (REPO / "src")
    jobs = [(w, s) for w in _ints(a.widths) for s in _ints(a.salts)]
    out = Path(a.out)
    if out.exists():
        print(f"既にある: {out.name}(上書きしない)", file=sys.stderr)
        return 2
    rows = []
    with cf.ThreadPoolExecutor(max_workers=int(a.jobs)) as ex:
        for row in ex.map(lambda ws: run_one(ws[0], ws[1], kw=kw, src=src), jobs):
            rows.append(row)
            print(row["width_s"], row["salt"], row.get("final"), row.get("calls"), (row.get("error") or "")[-200:],
                  flush=True)
    out.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8", newline="\n")
    return 1 if any("error" in r for r in rows) else 0


def read_records(path: Path) -> list[dict[str, Any]]:
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def cmd_table(a: argparse.Namespace) -> int:
    recs = [r for r in read_records(Path(a.records)) if "error" not in r]
    tab = table(recs, ref_width=int(a.ref_width), alpha=float(a.alpha))
    if a.out_json:
        Path(a.out_json).write_text(json.dumps(tab, ensure_ascii=False, indent=1) + "\n", encoding="utf-8",
                                    newline="\n")
    md = markdown(tab)
    if a.out_md:
        Path(a.out_md).write_text(md, encoding="utf-8", newline="\n")
    print(md)
    return 0


def main(argv: Iterable[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="TM4 のまとめの幅の試験の道具(第 3 期 3-2)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--widths", default="60,30,10,5")
    r.add_argument("--salts", default="1,2,3,4,5,6")
    r.add_argument("--population-seed", type=int, default=1)
    r.add_argument("--agents", type=int, default=300)
    r.add_argument("--world", default="data/world/v2")
    r.add_argument("--kw", default="", help="cli.run に足す引数(JSON)")
    r.add_argument("--src", default="", help="子プロセスの src(既定=この道具のリポの src)")
    r.add_argument("--jobs", type=int, default=4)
    r.add_argument("--out", required=True)
    t = sub.add_parser("table")
    t.add_argument("--records", required=True)
    t.add_argument("--ref-width", type=int, default=DEFAULT_REF_WIDTH)
    t.add_argument("--alpha", type=float, default=0.05)
    t.add_argument("--out-json", default="")
    t.add_argument("--out-md", default="")
    a = ap.parse_args(None if argv is None else list(argv))
    return {"run": cmd_run, "table": cmd_table}[a.cmd](a)


if __name__ == "__main__":
    sys.exit(main())
