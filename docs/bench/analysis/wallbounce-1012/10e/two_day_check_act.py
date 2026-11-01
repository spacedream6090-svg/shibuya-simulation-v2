"""第330 ACT(版上げ 1 回目の活性化): 2 日のラン(5,000 体・seed 1・sim_days=2・世界資産・既定 v3・テープつき)の控え。

``one`` は 1 本回して 1 行の JSON を出す: 暦の日付(manifest の ``calendar.days``)・天気の日ごとの記録(``weather.days``)・
各日の再生日の W13 の行(天候型・平日/土休・日最高気温・日降水量)を資産から直に引いた値・final・呼数・テープの calls と
blocks の中身の sha256。``check`` は ACT の約束(日付が 07-13 → 07-14 と進み、各日の再生日=暦の日付=その日の観測・
影も暦の日付)を確かめる。絶対パスは書かない。

    python $D/two_day_check_act.py one --label act --tape <作業用> > act.json      # 作業木(ACT)
    python $D/two_day_check_act.py check act.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path


def _sha_table(path: Path) -> str:
    import pyarrow.parquet as pq

    t = pq.read_table(path)
    h = hashlib.sha256()
    for n in t.column_names:
        h.update(n.encode("utf-8"))
        h.update(json.dumps(t.column(n).to_pylist(), ensure_ascii=False, default=str).encode("utf-8"))
    return h.hexdigest()[:16]


def cmd_one(args: argparse.Namespace) -> int:
    import pyarrow.parquet as pq

    import shibuya
    from shibuya import cli

    t0 = time.perf_counter()
    kw = json.loads(args.kw or "{}")
    res = cli.run(n_agents=args.agents, seed=args.seed, world_dir=args.world, sim_days=2, vocab_version="v3",
                  activity=True, tape_path=args.tape, **kw)
    man = res.run_manifest_fields()
    cal = dict(man.get("calendar", {}) or {})
    weather = man.get("weather", {}) or {}
    days = pq.read_table(Path(args.world) / "w13_weather_days.parquet").to_pydict()
    idx = {str(d): i for i, d in enumerate(days["date"])}
    cols = [c for c in ("weather_type", "weekday_kind", "stratum", "temp_max_c", "precip_total_mm", "sunrise", "sunset") if c in days]
    w13 = {}
    for d in weather.get("days", []):
        r = idx.get(str(d.get("replay_date", "")))
        w13[str(d.get("replay_date", ""))] = {c: days[c][r] for c in cols} if r is not None else None
    src_root = Path(shibuya.__file__).resolve().parents[1]
    print(json.dumps({
        "label": args.label, "kw": kw, "src_is_worktree": src_root == Path(__file__).resolve().parents[5] / "src",
        "start_sim_datetime": str(man.get("start_sim_datetime", "")),
        "calendar_weekday": cal.get("calendar_weekday", ""),
        "calendar_days": [{k: d.get(k) for k in ("day", "date", "weekday", "is_holiday", "is_rest_day")}
                          for d in cal.get("days", [])],
        "weather_scheme": weather.get("scheme", "(欄なし)"), "weather_perturbed": weather.get("perturbed"),
        "weather_days": weather.get("days", []), "weather_warnings": weather.get("warnings", []),
        "w13_rows_of_replay_dates": w13,
        "final": res.final_hash[:16], "calls": int(res.llm_calls),
        "calls_sha": _sha_table(Path(args.tape) / "calls.parquet"),
        "blocks_sha": _sha_table(Path(args.tape) / "blocks.parquet"),
        "wall_s": round(time.perf_counter() - t0, 1),
    }, ensure_ascii=False, default=str))
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    row = json.loads(Path(args.json).read_text(encoding="utf-8").strip().splitlines()[-1])
    problems = []
    dates = [d["date"] for d in row["calendar_days"]]
    if dates != ["2026-07-13", "2026-07-14"]:
        problems.append(f"暦の日付 {dates}")
    for d in row["weather_days"]:
        if d["replay_date"] != d["calendar_date"] or d["how"] != "actual":
            problems.append(f"{d['calendar_date']}: 再生日 {d['replay_date']}・{d['how']}(その日の観測でない)")
        if d["shadow_date"] != d["calendar_date"] or d["shadow_fallback"]:
            problems.append(f"{d['calendar_date']}: 影 {d['shadow_date']}(暦の日付でない)")
        w = row["w13_rows_of_replay_dates"].get(d["replay_date"])
        if w is None or not d["stratum"].endswith("|" + str(w.get("weather_type"))):
            problems.append(f"{d['calendar_date']}: 層 {d['stratum']} と W13 の行 {w} が合わない")
    print(json.dumps({"ok": not problems, "problems": problems}, ensure_ascii=False))
    return 0 if not problems else 1


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("one")
    o.add_argument("--label", required=True)
    o.add_argument("--tape", required=True)
    o.add_argument("--world", default="data/world/v2")
    o.add_argument("--agents", type=int, default=5_000)
    o.add_argument("--seed", type=int, default=1)
    o.add_argument("--kw", default="")
    c = sub.add_parser("check")
    c.add_argument("json")
    args = ap.parse_args(argv)
    return cmd_one(args) if args.cmd == "one" else cmd_check(args)


if __name__ == "__main__":
    sys.exit(main())
