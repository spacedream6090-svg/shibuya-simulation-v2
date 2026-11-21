"""第346 旧道の切替口と死んだ道の削除(返事その 6 §3-2 の 1・2): つなぎの台帳の行を閉じる(冪等)。

    python docs/bench/analysis/delete-346/tools/ledger_delete346.py [--dry-run]

- 閉じる行(``status=removed``・why の末尾に理由と「旧値の再現は安定版のタグ」): :data:`CLOSE` の行。切替口を 1 本消す
  たびに行を足す(行の無い切替口=vb24 の 3 腕は台帳に行を足さず、記録の README に書くだけ=親の仮採用 Q12)。
- 書き方は台帳の今の形(indent 1・``ensure_ascii=False``・末尾の改行)。本段の注は外して足し直す(冪等=2 回目は変化 0)。
- 前例: ``docs/bench/analysis/wallbounce-1012/pop43/tools/ledger_pop43_part2.py``。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[4]

LEDGER = REPO / "docs" / "design" / "bridging-ledger.json"
REC = "docs/bench/analysis/delete-346/README.md"
TAG = "〔第346 旧道の切替口と死んだ道の削除〕"
STABLE = "stable-v2-before-switch-removal-346"
#: 文を改める行(id → (古い文の一部, 新しい文の一部, why に足す理由))。見出しの項の数が変わった行など。
EDIT = {
    "HD-engine.conversation-1af925f4": ("の下の項 7 個", "の下の項 6 個",
                                        "応答確率 0.8 の項を消した(死んだ道=抽選ごと消した・行 DOC-fix4-dead-accept-probability)"
                                        "=項 7 → 6"),
}
CLOSE = {
    "DOC-rules42b-legacy-switch": "規則の表の空欄 3 件の腕の切替口 SHIBUYA_RULES_42B=off(4-2 の値の再現)を消した(環境変数を"
                                  "与えると読み込みで止まる)。4-2 の値は部品の単体試験の基準の口として残した"
                                  "(PayrollInputs.rules_42b を偽にして直に作る物・taxes.payroll_tables(r42b=False))",
    "DOC-rules42-legacy-switch": "規則の表の中身の腕の切替口 SHIBUYA_RULES_42=off(4-2 の前の値の再現)を消した(環境変数を与えると"
                                 "読み込みで止まる・組み立ては常に規則の表の中身を挿す)。4-2 の前の値は law の無い Stage2Plan を"
                                 "直に作る部品の単体試験の基準の口として残した",
    "DOC-fix4-defect-legacy-switch": "欠陥 4 件の直しの切替口 --defect-fixes-1103 legacy(環境変数 SHIBUYA_DEFECT_FIXES_1103)と"
                                     "会話の系の旧道の分かれ(全員を IDLE に戻す)を消した(環境変数を与えると読み込みで止まる・"
                                     "CLI は引数の誤り・設定の箱の欄も消した)。部品の関数の既定(resolve.apply の defect_fixes=False"
                                     "・_settle_pending_invites の drop_unreachable/keep_activity=False・ConversationManager の "
                                     "count_unreachable=False)は部品の単体試験の基準の口として残した",
    "DOC-fix4-dead-accept-probability": "死んだ道=会話の応答率 0.8 の抽選(ACCEPT_PROBABILITY・ConversationManager._accepts・"
                                        "accept_probability と domain の引数と状態台帳の欄・乱数の静的な呼び手の表の 1 行・乱数の用途名 "
                                        "conversation.invite)を消した。invite の "
                                        "answered は必ず渡す(呼び手は全部 answered=True だった=既定のランは 1 バイト不変)",
    "DOC-fix4-dead-important-extra-turns": "死んだ道=会話の重要度上位の +2 呼(IMPORTANT_EXTRA_TURNS・ConversationManager の "
                                           "important と extra_turns_for_important の引数と状態台帳の欄)を消した。ハード上限は"
                                           "全員 max_turns(組み立ては対象を渡さなかった=既定のランは 1 バイト不変)",
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
    missing = sorted((set(CLOSE) | set(EDIT)) - set(have))
    if missing:
        print("台帳に無い行:", missing, file=sys.stderr)
        return 2
    closed, touched = [], []
    for rid, (old, new, reason) in EDIT.items():
        r = have[rid]
        what = r["what"].replace(old, new)
        why = _strip(r["why"]) + f"{TAG}{reason}(記録 {REC}・取り込みの commit は親)"
        if (what, why) != (r["what"], r["why"]):
            touched.append(rid)
        r["what"], r["why"] = what, why
    for rid, reason in CLOSE.items():
        r = have[rid]
        why = _strip(r["why"]) + f"{TAG}閉じた: {reason}。旧値の再現は安定版のタグ {STABLE}(記録 {REC}・取り込みの commit は親)"
        if why != r["why"]:
            touched.append(rid)
        r["why"] = why
        if r["status"] != "removed":
            r["status"] = "removed"
            closed.append(rid)
    print(f"閉じた {len(closed)}・why を書いた {len(touched)}・行 {len(rows)}")
    for x in closed:
        print("  -", x)
    if not a.dry_run:
        LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
