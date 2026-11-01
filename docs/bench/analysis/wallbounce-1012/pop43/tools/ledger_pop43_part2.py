"""第 4 期 4-3 版上げ 3 回目の第 2 部(旧道の切替口の削除): つなぎの台帳の行を閉じる・文を改めた宣言の行を足す(冪等)。

    python docs/bench/analysis/wallbounce-1012/pop43/tools/ledger_pop43_part2.py [--dry-run]

- 閉じる行(``status=removed``・why の末尾に理由と「再現は安定版のタグ」): 賃金の切替口 ``--wage w17``
  (``DOC-wage_occ-legacy-switch``)・既定の食事時刻の旧値の腕(``BR-MEAL-DEFAULT-VALIDATION-ARM``=宣言の文を
  ``engine.energy.MEAL_DEFAULT_EXPEDIENTS`` から消した)・W12 の等間隔の道の宣言の旧い文(切替口 ``USE_REAL_TIMETABLES`` の
  言及=文を改めた=後継の行)。
- 足す行: W12 の等間隔の道の宣言の改めた文(``EX-build.field.w12_external_nodes-<sha8>``・外す段は前の行のまま)。
- 書き方は台帳の今の形(indent 1・``ensure_ascii=False``・末尾の改行)。本段の注は外して足し直す(冪等)。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[5]
sys.path.insert(0, str(REPO / "src"))

from shibuya.engine.bridging import scan as S  # noqa: E402

LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
REC = "docs/bench/analysis/wallbounce-1012/pop43/README.md §19"
SINCE = "2026-10-21"
TAG = "〔第 4 期 4-3 版上げ 3 回目の第 2 部・pop43〕"
W12_PATH = "src/shibuya/build/field/w12_external_nodes.py"
W12_PREFIX = "EX-build.field.w12_external_nodes-"
W12_OLD = "EX-build.field.w12_external_nodes-f2cc7f0a"
CLOSE = {
    "DOC-wage_occ-legacy-switch": "賃金の切替口 --wage w17(環境変数 SHIBUYA_WAGE)と W17 の勤務時間 × 最低賃金の道を消した"
                                  "(環境変数を与えると止まる)。旧値の再現は安定版のタグ stable-v2-before-wage-occupation",
    "BR-MEAL-DEFAULT-VALIDATION-ARM": "既定の食事時刻の旧値の腕 --meal-default validation(環境変数 SHIBUYA_MEAL_DEFAULT)と検証側の錨を"
                                      "読む道を消した(宣言の文も消した・環境変数を与えると止まる)。旧値の再現は安定版のタグ "
                                      "stable-v2-before-meal-default-w17",
}


def _strip(why: str) -> str:
    return why.split(TAG, 1)[0]


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args(argv)
    doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    rows = doc["bridges"]
    have = {r["id"]: r for r in rows}
    decls = [d for d in S.scan_package()
             if d.form == S.FORM_EXPEDIENTS and d.path == W12_PATH and d.text.startswith("等間隔ダイヤ(F10)の道=")]
    ids = [f"{W12_PREFIX}{d.declared_in.rsplit(':', 1)[-1]}" for d in decls]
    added, closed = [], []
    old = have[W12_OLD]
    for d, rid in zip(decls, ids):
        if rid in have:
            continue
        row = {"id": rid, "what": d.text,
               "why": (f"{TAG}W12 の等間隔の道の宣言の文を改めた(切替口 USE_REAL_TIMETABLES=False を消した=実データの無い線"
                       f"だけの道)。前の行 {W12_OLD} の外す段のまま(記録 {REC})。前の行の理由: " + _strip(old["why"])),
               "remove_at": old["remove_at"], "declared_in": d.declared_in, "conf": old.get("conf", "expedient"),
               "since": SINCE, "status": "active", "remove_basis": old.get("remove_basis", "inferred")}
        rows.append(row)
        have[rid] = row
        added.append(rid)
    succ = next((rid for rid in ids if rid != W12_OLD), "")
    reasons = dict(CLOSE)
    if W12_OLD not in ids:
        reasons[W12_OLD] = (f"切替口 USE_REAL_TIMETABLES=False(1.1.0 の時刻表の再現)を消し、宣言の文を改めた=後継 {succ}。"
                            "旧値の再現は安定版のタグ")
    for rid, reason in reasons.items():
        r = have[rid]
        r["why"] = _strip(r["why"]) + f"{TAG}閉じた: {reason}(記録 {REC}・取り込みの commit は親)"
        if r["status"] != "removed":
            r["status"] = "removed"
            closed.append(rid)
    print(f"足した {len(added)}・閉じた {len(closed)}・行 {len(rows)}")
    for x in added:
        print("  +", x)
    for x in closed:
        print("  -", x)
    if not a.dry_run:
        LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
