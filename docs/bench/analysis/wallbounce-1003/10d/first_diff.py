"""10d: 通しのランと再開のラン(と止めたラン)を比べて、**最初に食い違う tick・列・持ち主の行**を出す道具。

検収役も使う。2 つの使い方:

1. ライブラリ: ``dump(res, path, tape=...)`` で ``run_day``/``cli.run`` の結果を JSON に落とし、``compare`` で比べる。
2. コマンド::

       python first_diff.py compare --straight S.json --segments A.json B.json [--out report.json]

   ``--segments`` は止めたランと再開のランを時刻の順に並べる(重なる tick は後のものを使う)。

比べるもの(どれも通しのランと同じ tick だけ):

- checkpoint ごとの ``combined``(今の final)・behavior-hash・full-hash。食い違えば、その tick の
  ``checkpoint_details``(``run_day(checkpoint_detail=True)`` のときだけ)から、値の違う SoA の列と外の状態の
  道筋を、状態台帳の行(鍵・名前・軸 1・軸 2)つきで出す。
- tick ごとの診断の行の**全列**(呼数を含む・10d 検収 T1。累計の列は無い=差分の基準も保存から戻す)。
- 日の締めの後の 2 つのハッシュと日次センサスの行(``daily``)。
- テープの呼ごとの ``(tick, 体, 級, prompt_hash)``(``dump(..., tape=テープの置き場)`` のときだけ)。

絶対パスは JSON に書かない(ファイル名だけ)。
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

FORMAT = "shibuya.bench/10d/run-dump/1"


def dump(res: Any, path: str | Path, *, label: str = "", tape: str | Path | None = None) -> dict[str, Any]:
    """``RunResult`` を比べるための JSON に落とす(返り値=書いた中身)。"""
    import numpy as np

    doc: dict[str, Any] = {
        "format": FORMAT,
        "label": label,
        "resume": {k: v for k, v in dict(res.resume).items() if k != "state_files"},
        "state_files": [{k: v for k, v in f.items() if k != "seconds"} for f in res.resume.get("state_files", [])],
        "final": res.final_hash,
        "llm_calls": int(res.llm_calls),
        "checkpoints": [[int(c.tick), c.combined, c.behavior_hash, c.full_hash] for c in res.checkpoints],
        "details": {str(int(d["tick"])): {"soa": d["soa"], "items": d["items"]} for d in res.checkpoint_details},
        "calls_by_tick": {},
        "diag_columns": [],
        "diag_by_tick": {},
        "daily": [
            {"day": r["day"], "end_T": r["end_T"],
             "eod": r.get("state_hashes_end_of_day", {}),
             "census_pass": r.get("census_pass"), "census_row": r.get("census_row", {}),
             "money": r.get("money"), "bodies": r.get("bodies")}
            for r in res.daily
        ],
        "day_heads": list(res.day_heads),
        "tape": [],
    }
    if res.diagnostics.size:
        t = res.column("tick").astype(np.int64)
        c = res.column("calls").astype(np.int64)
        doc["calls_by_tick"] = {str(int(a)): int(b) for a, b in zip(t.tolist(), c.tolist())}
        from shibuya.engine.run import DIAG_RUN_COLUMNS

        doc["diag_columns"] = list(DIAG_RUN_COLUMNS)
        doc["diag_by_tick"] = {str(int(row[0])): [int(x) for x in row] for row in res.diagnostics.tolist()}
    if tape is not None:
        from shibuya.engine.tape import Tape

        doc["tape"] = sorted(
            [int(r.tick), int(r.agent_id), int(r.wake_class), str(r.prompt_hash)]
            for r in Tape(Path(tape)).rows() if not getattr(r, "is_deferred", False)
        )
    Path(path).write_text(json.dumps(doc, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
    return doc


def _load(path: str | Path) -> dict[str, Any]:
    doc = json.loads(Path(path).read_text(encoding="utf-8"))
    if doc.get("format") != FORMAT:
        raise ValueError(f"{Path(path).name}: 形式が違う({doc.get('format')!r})")
    return doc


def _row_info(key: str) -> dict[str, Any]:
    """``agents.cell`` か ``O10:mem_layer._next_session`` → 状態台帳の行の鍵・名前・軸。"""
    from shibuya.engine import state_ledger as SL

    rk = key.split(":", 1)[0]
    try:
        r = SL.row(rk)
    except KeyError:
        return {"key": key, "row": None}
    return {"key": key, "row": r.key, "name": r.name, "behavior": r.behavior, "restore": r.restore}


def _merge(segments: list[dict[str, Any]]) -> dict[str, Any]:
    ck: dict[int, list[Any]] = {}
    det: dict[str, Any] = {}
    calls: dict[str, int] = {}
    diag: dict[str, list[int]] = {}
    daily: dict[int, dict[str, Any]] = {}
    tape: dict[tuple[int, int, int], str] = {}
    for s in segments:  # 後のランが同じ tick を持てば後のもの
        for c in s["checkpoints"]:
            ck[int(c[0])] = c
        det.update(s.get("details", {}))
        calls.update(s.get("calls_by_tick", {}))
        diag.update(s.get("diag_by_tick", {}))
        for r in s.get("daily", []):
            daily[int(r["day"])] = r
        for t, a, w, h in s.get("tape", []):
            tape[(int(t), int(a), int(w))] = h
    return {"checkpoints": ck, "details": det, "calls": calls, "diag": diag, "daily": daily, "tape": tape}


def compare(straight: dict[str, Any], segments: list[dict[str, Any]], *, from_T: int | None = None
            ) -> dict[str, Any]:
    """通しのラン ``straight`` と、止めたラン+再開のラン ``segments`` を比べる。

    ``from_T`` を渡すとその時刻以降だけ(既定=最後の区間の始めの T。止めたランの区間は通しと同じ処理なので
    比べるまでもないが、渡せば止める前から比べられる)。
    """
    seg = _merge(segments)
    if from_T is None:
        from_T = int(segments[-1].get("resume", {}).get("start_T", 0))
    s_ck = {int(c[0]): c for c in straight["checkpoints"]}
    out: dict[str, Any] = {"from_T": int(from_T), "checkpoints_compared": 0, "first_mismatch": None,
                           "mismatched_checkpoints": 0}
    for t in sorted(k for k in seg["checkpoints"] if k >= from_T):
        if t not in s_ck:
            continue
        out["checkpoints_compared"] += 1
        a, b = s_ck[t], seg["checkpoints"][t]
        same = {"combined": a[1] == b[1], "behavior": a[2] == b[2], "full": a[3] == b[3]}
        if all(same.values()):
            continue
        out["mismatched_checkpoints"] += 1
        if out["first_mismatch"] is None:
            fm: dict[str, Any] = {"tick": int(t), "same": same, "differs": []}
            sd, bd = straight.get("details", {}).get(str(t)), seg["details"].get(str(t))
            if sd is not None and bd is not None:
                for part in ("soa", "items"):
                    for k in sd[part]:
                        if sd[part][k] != bd[part].get(k):
                            fm["differs"].append(_row_info(k))
            else:
                fm["differs"] = "(この tick の digest が無い: run_day(checkpoint_detail=True) で回す)"
            out["first_mismatch"] = fm
    # 呼数(tick ごと)
    s_calls = straight.get("calls_by_tick", {})
    bad_calls = [int(t) for t, v in seg["calls"].items() if int(t) >= from_T and s_calls.get(t) != v]
    out["calls_ticks_compared"] = sum(1 for t in seg["calls"] if int(t) >= from_T)
    out["first_calls_mismatch"] = min(bad_calls) if bad_calls else None
    want_ticks = {int(t) for t in s_calls if int(t) >= from_T}
    got_ticks = {int(t) for t in seg["calls"] if int(t) >= from_T}
    out["calls_ticks_missing"] = sorted(want_ticks - got_ticks)[:10]
    # 診断の行の全列(10d 検収 T1)
    cols = list(straight.get("diag_columns", []))
    s_diag = straight.get("diag_by_tick", {})
    first_diag = None
    for t in sorted((int(k) for k in seg["diag"] if int(k) >= from_T)):
        a, b = s_diag.get(str(t)), seg["diag"][str(t)]
        if a != b:
            first_diag = {"tick": t, "columns": [cols[i] if i < len(cols) else i
                                                 for i in range(max(len(a or []), len(b)))
                                                 if (a or [None] * len(b))[i] != b[i]]}
            break
    out["first_diag_mismatch"] = first_diag
    # 日の締め
    s_daily = {int(r["day"]): r for r in straight.get("daily", [])}
    days = []
    for d, r in sorted(seg["daily"].items()):
        if int(r["end_T"]) <= from_T or d not in s_daily:
            continue
        s = s_daily[d]
        days.append({"day": d,
                     "eod_full_same": s["eod"].get("full_hash") == r["eod"].get("full_hash"),
                     "eod_behavior_same": s["eod"].get("behavior_hash") == r["eod"].get("behavior_hash"),
                     "census_pass": [s.get("census_pass"), r.get("census_pass")],
                     "census_row_differs": sorted(k for k in set(s.get("census_row", {})) | set(r.get("census_row", {}))
                                                  if s.get("census_row", {}).get(k) != r.get("census_row", {}).get(k))})
    out["daily"] = days
    # テープ(呼ごとの prompt_hash)
    if straight.get("tape") and seg["tape"]:
        s_tape = {(int(t), int(a), int(w)): h for t, a, w, h in straight["tape"] if int(t) >= from_T}
        b_tape = {k: h for k, h in seg["tape"].items() if k[0] >= from_T}
        diff = sorted(k for k in set(s_tape) | set(b_tape) if s_tape.get(k) != b_tape.get(k))
        out["tape"] = {"rows_straight": len(s_tape), "rows_segments": len(b_tape), "rows_differ": len(diff),
                       "first_differ": list(diff[0]) if diff else None}
    out["ok"] = bool(out["first_mismatch"] is None and out["first_calls_mismatch"] is None
                     and out["first_diag_mismatch"] is None
                     and not out["calls_ticks_missing"]
                     and all(d["eod_full_same"] and d["eod_behavior_same"] and not d["census_row_differs"]
                             and d["census_pass"][0] == d["census_pass"][1] for d in days)
                     and (out.get("tape") is None or out["tape"]["rows_differ"] == 0))
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    sp = sub.add_parser("compare")
    sp.add_argument("--straight", required=True)
    sp.add_argument("--segments", nargs="+", required=True)
    sp.add_argument("--from-T", type=int, default=None)
    sp.add_argument("--out", default="")
    args = ap.parse_args(argv)
    rep = compare(_load(args.straight), [_load(p) for p in args.segments], from_T=args.from_T)
    text = json.dumps(rep, ensure_ascii=False, indent=1)
    if args.out:
        Path(args.out).write_text(text + "\n", encoding="utf-8", newline="\n")
    print(text)
    return 0 if rep["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
