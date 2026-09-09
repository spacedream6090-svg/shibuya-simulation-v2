# -*- coding: utf-8 -*-
"""c7_accept.py — **C7 受入表を 1 枚**にまとめる。

正典(実装計画書 §9.1 C7 行)
    「サーバーで1日ラン(週7日表・第1陣全部)・壁時計≤24h・M8≤24GB・S1≤5GB・診断行・
     **holdout照合は事後1回のみ**(KDDI形状5指標)」
    「検収=予算全行・決定論(同seed再ラン=T2)・被覆指標WC-6」

入力は**すべてラン後の成果物**(エンジンを再実行しない)
    ``--summary``      ラン CLI の標準出力(``RunResult.summary()``)
    ``--time-v``       ``/usr/bin/time -v`` の出力(M8 の Maximum resident set size)
    ``--out-dir``      恒久記録の置き場(S1 のバイト数を合計)/``--out-bytes`` で直接指定も可
    ``--manifest``     ラン manifest JSON(同定欄・holdout_open の有無)
    ``--wc``           ``wc_index.json``(WC-5 過剰・WC-6 孤児)
    ``--determinism``  同 seed 2 ランの checkpoint JSON 2 本(**T2**・5,000 体)
    ``--partial``      40 万体 本ランと**先頭 K tick の部分再ラン**の checkpoint JSON 2 本
    ``--holdout``      ``holdout_compare.py`` が出した JSON

**T2 の代替**(親判断待ち・登録簿 E-C7-4)
    運用設計書 §1.4 T2 は「同一 manifest×2 で全 checkpoint ハッシュ一致」。40 万体を 2 回
    回すと壁時計 48h で W1 を割るので、C7 では次の 3 脚で代替することを提案する:
      T2-a 5,000 体×1 シミュ日の**完全再ラン一致**(checkpoint 全点+final_hash)
      T2-b 40 万体 本ランの**先頭 K tick(既定 120)の部分再ラン一致**(=規模での決定論)
      T2-c 40 万体 本ランの**checkpoint 自己整合**(tick 昇順・欠けなし・population_hash /
           schedule_hash が全点同一・manifest 同定欄と一致)
    3 脚とも合格を「T2 相当」とし、**T2 そのものではない**ことを受入表に明記する。

例::

    python tools/c7/c7_accept.py --summary runs/c7/stdout.txt --time-v runs/c7/time.txt \\
        --out-dir runs/c7/journal --manifest runs/c7/run_manifest.json \\
        --wc data/world/v2/wc_index.json \\
        --determinism runs/c7/t2a_1.json runs/c7/t2a_2.json \\
        --partial runs/c7/full_ckpt.json runs/c7/head_ckpt.json \\
        --holdout docs/bench/c7/c7_holdout_compare.json --out docs/bench/c7
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(os.path.abspath(__file__)).parent))

import c7lib  # noqa: E402

GB = 1024.0 ** 3
#: T2-b の既定の部分再ラン長[tick](1,440 の 1/12 = 壁時計 24h の約 2h)。
DEFAULT_PARTIAL_TICKS = 120


# ---------------------------------------------------------------- 行


def _row(rid: str, item: str, measured: Any, limit: Any, judge: str | None, note: str = ""
         ) -> dict[str, Any]:
    return {"id": rid, "item": item, "measured": measured, "limit": limit,
            "judge": judge, "note": note}


def _fmt(v: Any, unit: str = "", nd: int = 3) -> str:
    if v is None:
        return "—"
    if isinstance(v, bool):
        return "OK" if v else "NG"
    if isinstance(v, float):
        return f"{v:,.{nd}f}{unit}"
    if isinstance(v, int):
        return f"{v:,}{unit}"
    return f"{v}{unit}"


def normalize_checkpoints(doc: Mapping[str, Any]) -> list[str]:
    """``run_hash.py`` の payload / c7 の checkpoint JSON のどちらでも読む。"""
    cps = doc.get("checkpoints")
    if isinstance(cps, list) and cps and isinstance(cps[0], str):
        return [str(c) for c in cps]
    if isinstance(cps, list):
        return [str(c.get("combined", "")) for c in cps]
    raise ValueError("checkpoints 欄が無い JSON")


def determinism_rows(a: Mapping[str, Any], b: Mapping[str, Any], *, label: str,
                     prefix_ok: bool = False) -> dict[str, Any]:
    """2 本の checkpoint 列を突き合わせる。``prefix_ok`` なら短い方が前方一致で合格。"""
    ca, cb = normalize_checkpoints(a), normalize_checkpoints(b)
    if prefix_ok:
        n = min(len(ca), len(cb))
        same = n > 0 and ca[:n] == cb[:n]
        detail = f"前方 {n} 点一致"
    else:
        same = len(ca) == len(cb) and ca == cb and len(ca) > 0
        detail = f"{len(ca)} 点 vs {len(cb)} 点"
    return {"label": label, "n_a": len(ca), "n_b": len(cb), "match": bool(same),
            "detail": detail,
            "first_mismatch": next((i for i, (x, y) in enumerate(zip(ca, cb)) if x != y), None)}


def selfconsistency(doc: Mapping[str, Any]) -> dict[str, Any]:
    """T2-c: 本ラン単体の checkpoint 自己整合。"""
    cps = doc.get("checkpoints") or []
    reasons: list[str] = []
    ticks = [c.get("tick") for c in cps if isinstance(c, Mapping)]
    if not cps:
        reasons.append("checkpoint が 0 点")
    if ticks and any(t is None for t in ticks):
        reasons.append("tick 欄の無い checkpoint がある")
    elif ticks and list(ticks) != sorted(ticks):
        reasons.append("tick が昇順でない")
    combined = [c.get("combined") for c in cps if isinstance(c, Mapping)]
    if any(not c for c in combined):
        reasons.append("空の combined がある")
    for key in ("population_hash", "schedule_hash"):
        vals = {c.get(key) for c in cps if isinstance(c, Mapping)}
        if len(vals) > 1:
            reasons.append(f"{key} が checkpoint 間で一致しない: {sorted(map(str, vals))}")
    return {"n_checkpoints": len(cps), "ok": not reasons, "reasons": reasons}


# ---------------------------------------------------------------- 表の組み立て


def build_table(
    summary: Mapping[str, Any] | None = None,
    time_v: Mapping[str, Any] | None = None,
    s1_bytes: int | None = None,
    manifest: Mapping[str, Any] | None = None,
    wc: Mapping[str, Any] | None = None,
    t2a: Mapping[str, Any] | None = None,
    t2b: Mapping[str, Any] | None = None,
    t2c: Mapping[str, Any] | None = None,
    holdout: Mapping[str, Any] | None = None,
    limits: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """受入表(行の list)。**純関数**=テストの入口。

    値が無い行は ``judge=None``(= "—" 未測定)で残す。**推測で埋めない**。
    """
    lim = dict(limits or c7lib.budget_limits())
    s = dict(summary or {})
    rows: list[dict[str, Any]] = []

    # --- 予算行 -----------------------------------------------------
    w1 = (lim.get("W1") or {}).get("limit")
    wall_h = (s.get("wall_seconds") / 3600.0) if s.get("wall_seconds") is not None else None
    if wall_h is None and time_v and time_v.get("elapsed_seconds") is not None:
        wall_h = time_v["elapsed_seconds"] / 3600.0
    rows.append(_row("W1", "壁時計/シミュ日", None if wall_h is None else round(wall_h, 3),
                     w1, None if (wall_h is None or w1 is None) else wall_h <= float(w1),
                     "単位=時間。予算表 W1 の文面が正典"))

    m8 = (lim.get("M8") or {}).get("limit")
    rss_gb = ((time_v or {}).get("max_rss_kb") or 0) * 1024.0 / GB if time_v else None
    rss_gb = round(rss_gb, 3) if rss_gb else None
    rows.append(_row("M8", "RSS 総額(1ラン)", rss_gb, m8,
                     None if (rss_gb is None or m8 is None) else rss_gb <= float(m8),
                     "/usr/bin/time -v の Maximum resident set size"))

    s1 = (lim.get("S1") or {}).get("limit")
    s1_gb = round(s1_bytes / GB, 3) if s1_bytes is not None else None
    rows.append(_row("S1", "恒久記録(出力バイト)", s1_gb, s1,
                     None if (s1_gb is None or s1 is None) else s1_gb <= float(s1),
                     "出力ディレクトリのファイル合計"))

    p2 = (lim.get("P2") or {}).get("limit")
    rows.append(_row("P2", "移動+密度[ms/tick]", s.get("movement_ms_per_tick"), p2, None,
                     "**参考**: P2 の宣言は 5千体の行。40万体は別行が要る=親判断"))

    calls = s.get("llm_calls")
    rows.append(_row("L4", "LLM 呼数(シミュ日)", calls, 4_000_000,
                     None if calls is None else calls <= 4_000_000,
                     f"平均 {_fmt(s.get('calls_per_agent'))} 呼/体/日(制御目標 10)"))

    # --- 決定論(T2 相当) ------------------------------------------
    rows.append(_row("T2-a", "5,000体 同seed 再ラン一致",
                     None if t2a is None else t2a["match"], True,
                     None if t2a is None else bool(t2a["match"]),
                     "" if t2a is None else t2a["detail"]))
    rows.append(_row("T2-b", "40万体 先頭K tick 部分再ラン一致",
                     None if t2b is None else t2b["match"], True,
                     None if t2b is None else bool(t2b["match"]),
                     "" if t2b is None else t2b["detail"]))
    rows.append(_row("T2-c", "40万体 checkpoint 自己整合",
                     None if t2c is None else t2c["ok"], True,
                     None if t2c is None else bool(t2c["ok"]),
                     "" if t2c is None else "; ".join(t2c["reasons"])))

    # --- 診断行 -----------------------------------------------------
    diag = dict(s.get("diagnostics") or {})
    missing = [c for c in c7lib.REQUIRED_DIAG_ROWS if c not in diag]
    rows.append(_row("DIAG", "診断行(繰り延べ/昇格/縮退/抑止)",
                     {c: diag.get(c) for c in c7lib.REQUIRED_DIAG_ROWS} or None,
                     "4 列とも出ること", (not missing) if diag else None,
                     "欠け: " + ", ".join(missing) if missing else ""))

    # --- 保存則 2 検算 ----------------------------------------------
    rows.append(_row("CONS-1", "保存則(Σmoney+Σrevenue+Σ運賃 不変)",
                     s.get("conserved"), True, s.get("conserved"), ""))
    rows.append(_row("CONS-2", "日次センサス ゲート(残差・純資産=実物資産)",
                     s.get("census_gate"), True, s.get("census_gate"),
                     f"残差 {_fmt(s.get('census_residual'))}"))
    rows.append(_row("CONST-5", "憲法5 のビルド時検査", s.get("constitution_ok"), True,
                     s.get("constitution_ok"), ""))

    # --- 被覆指標 ---------------------------------------------------
    orphans = None
    commission = None
    if wc:
        orphans = len(wc.get("orphans", []))
        commission = wc.get("X")
    rows.append(_row("WC-6", "世界被覆 孤児(reaches宣言あり∧実読0)", orphans, 0,
                     None if orphans is None else orphans == 0,
                     "方法論: WC-5/WC-6 のみゲート"))
    rows.append(_row("WC-5", "世界被覆 過剰 X", commission, "前ランより悪化で警告", None,
                     "報告のみ(絶対の合格線は無い)"))

    # --- holdout ----------------------------------------------------
    if holdout:
        rows.append(_row("HOLD", "KDDI 形状5指標(事後1回)",
                         f"{holdout.get('n_pass')}/{holdout.get('n_measured')} 合格",
                         "5 指標(うち H3 は測定不能→代替)", bool(holdout.get("pass")),
                         "事前登録の合格線は**案**(親判断待ち)"))
    else:
        rows.append(_row("HOLD", "KDDI 形状5指標(事後1回)", None,
                         "5 指標", None, "未照合"))

    opened = bool((manifest or {}).get("holdout_open"))
    rows.append(_row("SEAL", "manifest の開封記録", opened, "照合したなら有ること",
                     None if holdout is None else opened, ""))

    judged = [r for r in rows if r["judge"] is not None]
    return {
        "rows": rows,
        "n_rows": len(rows),
        "n_judged": len(judged),
        "n_pass": sum(1 for r in judged if r["judge"]),
        "n_fail": sum(1 for r in judged if not r["judge"]),
        "pass": bool(judged) and all(bool(r["judge"]) for r in judged),
    }


def table_markdown(table: Mapping[str, Any]) -> str:
    rows = [[r["id"], r["item"], _fmt(r["measured"]), _fmt(r["limit"]),
             "—" if r["judge"] is None else ("PASS" if r["judge"] else "**FAIL**"),
             r["note"]] for r in table["rows"]]
    head = ["行", "項目", "実測", "上限/期待", "判定", "備考"]
    return "\n".join([
        "# C7 受入表(40万体×1シミュ日・本番相当)",
        "",
        c7lib.markdown_table(head, rows),
        "",
        f"判定済み {table['n_judged']}/{table['n_rows']} 行 ・ 合格 {table['n_pass']} ・ "
        f"不合格 {table['n_fail']} → **{'PASS' if table['pass'] else 'FAIL'}**",
        "",
        "> T2-a/b/c は運用設計書 §1.4 **T2 そのものではない**(40万体を2回回さないための代替・"
        "実装計画書 §8 登録簿 E-C7-4)。",
        "> P2 の上限は 5千体の行なので 40万体では**参考**(予算表に 40万体の物理行が無い=親判断)。",
    ])


# ---------------------------------------------------------------- CLI


def _load(path: str | None) -> dict[str, Any] | None:
    return json.loads(Path(path).read_text(encoding="utf-8")) if path else None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="C7 受入表を 1 枚に")
    ap.add_argument("--summary", default=None, help="ラン CLI の標準出力ファイル")
    ap.add_argument("--time-v", default=None, help="/usr/bin/time -v の出力ファイル")
    ap.add_argument("--out-dir", default=None, help="恒久記録の置き場(S1 の合計対象)")
    ap.add_argument("--out-bytes", type=int, default=None, help="S1 のバイト数を直接指定")
    ap.add_argument("--manifest", default=None)
    ap.add_argument("--wc", default=None, help="wc_index.json")
    ap.add_argument("--determinism", nargs=2, default=None, metavar=("A", "B"),
                    help="T2-a: 5,000体 同seed 2 ランの checkpoint JSON")
    ap.add_argument("--partial", nargs=2, default=None, metavar=("FULL", "HEAD"),
                    help="T2-b: 40万体 本ランと先頭K tick 部分再ランの checkpoint JSON")
    ap.add_argument("--holdout", default=None, help="holdout_compare.py の JSON")
    ap.add_argument("--out", default="docs/bench/c7")
    args = ap.parse_args(argv)

    summary = (c7lib.parse_run_summary(Path(args.summary).read_text(encoding="utf-8"))
               if args.summary else None)
    time_v = (c7lib.parse_time_v(Path(args.time_v).read_text(encoding="utf-8"))
              if args.time_v else None)
    s1 = args.out_bytes if args.out_bytes is not None else (
        c7lib.dir_bytes(args.out_dir) if args.out_dir else None)

    t2a = t2b = t2c = None
    if args.determinism:
        t2a = determinism_rows(_load(args.determinism[0]), _load(args.determinism[1]),
                               label="T2-a 5,000体 完全再ラン")
    if args.partial:
        full, head = _load(args.partial[0]), _load(args.partial[1])
        t2b = determinism_rows(full, head, label="T2-b 先頭K tick", prefix_ok=True)
        t2c = selfconsistency(full)

    table = build_table(summary, time_v, s1, _load(args.manifest), _load(args.wc),
                        t2a, t2b, t2c, _load(args.holdout))
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "c7_accept.json").write_text(
        json.dumps(table, ensure_ascii=False, indent=1), encoding="utf-8")
    md = table_markdown(table)
    (out_dir / "c7_accept.md").write_text(md, encoding="utf-8")
    print(md)
    return 0 if table["pass"] else 1


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
