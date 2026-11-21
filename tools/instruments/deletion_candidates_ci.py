# -*- coding: utf-8 -*-
"""削除候補を CI の出力と成果物に出す(D-R2-4・仕様 WD-05・11-16 §1-3 の 5)。

世界過程の設計書 §5 の確定文「宣言した届き先が消えた細部は、削除候補として台帳に自動的に載る」を機械で残す道。
``runs/`` は git に入らないので、台帳ファイルを commit する代わりに、CI の検査の出力(と CI の成果物)に
数と名前を出す。**CI を落とす条件にはしない**(候補が何件あっても終了コードは 0)。

    python tools/instruments/deletion_candidates_ci.py [--out runs/deletion_candidates.json]

やること: 第 1 陣の台帳(``first_batch.build_registry()``)に憲法 5 の検査(``check_constitution5``)を当て、
削除候補を ``deletion_candidates.append_candidates`` で台帳ファイルへ足し(同じ行は重ねない)、数と名前を出す。
``GITHUB_STEP_SUMMARY`` が在れば、同じ表を CI の要約にも書く。data は要らない(台帳はコードの宣言だけで作る)。

終了コード: 0=出した(候補の数に依らない)・2=道具そのものの誤り(台帳を作れない・書けない)。
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any, Callable, Iterable, Sequence

ROOT = Path(__file__).resolve().parents[2]


def collect() -> tuple[Any, ...]:
    """今のコードの宣言から、削除候補の一覧を作る。"""
    src = str(ROOT / "src")
    if src not in sys.path:
        sys.path.insert(0, src)
    from shibuya.world.ledger.first_batch import build_registry

    report = build_registry().check_constitution5()
    return tuple(report.deletion_candidates)


def render(rows: Iterable[Any]) -> list[str]:
    """数と名前の行(人が読む形)。"""
    rows = list(rows)
    lines = [f"削除候補 {len(rows)} 件(D-R2-4・落とす条件ではない)"]
    for r in rows:
        vanished = "・".join(r.vanished_targets) if r.vanished_targets else "なし"
        lines.append(f"  {r.subject_type} {r.subject_id}: {r.reason}(消えた届き先: {vanished})")
    return lines


def summary_markdown(rows: Iterable[Any]) -> str:
    rows = list(rows)
    out = [f"### 削除候補 {len(rows)} 件(D-R2-4・落とす条件ではない)", ""]
    if rows:
        out += ["| 種類 | 名前 | 理由 | 消えた届き先 |", "|---|---|---|---|"]
        for r in rows:
            out.append(f"| {r.subject_type} | {r.subject_id} | {r.reason} | {'・'.join(r.vanished_targets)} |")
    else:
        out.append("届き先が消えた細部は無い。")
    return "\n".join(out) + "\n"


def main(argv: Sequence[str] | None = None, collect_fn: Callable[[], Sequence[Any]] | None = None) -> int:
    ap = argparse.ArgumentParser(description="削除候補を CI の出力と成果物に出す(落とす条件にしない)")
    ap.add_argument("--out", default="runs/deletion_candidates.json", help="台帳ファイル(docs/ の下は不可)")
    ns = ap.parse_args(argv)
    try:
        found = tuple((collect_fn or collect)())
        src = str(ROOT / "src")
        if src not in sys.path:
            sys.path.insert(0, src)
        from shibuya.validation.static.deletion_candidates import append_candidates

        rows = append_candidates(ns.out, found)
    except Exception as e:
        print(f"[deletion_candidates_ci] 誤り: {type(e).__name__}: {e}", file=sys.stderr)
        return 2
    for line in render(rows):
        print(line)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as f:
            f.write(summary_markdown(rows))
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
