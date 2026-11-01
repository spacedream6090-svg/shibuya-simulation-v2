"""第 2 期 2-4 V1: C8 の感度の台帳(``tools/c8/sensitivity_v1.json``)の注記と数を活性化の後の build_manifest に合わせる。

``build_manifest_expedients`` の ``count``・``note``(前の注記は ``note_2026_10_14_pre_2_4`` に残す)と、``open_questions`` の
「123 行」の問い(前の文は ``open_questions_pre_2_4`` に残す)。判定の列(``build_manifest_judgment``)は
``tools/c8/sensitivity.py`` の ``--judge-manifest → --read-graph → --triage → --d44`` で作り直す(本道具は触らない)。
書いた後に ``tools/c8/sensitivity.py --manifest <活性化の後の build_manifest>`` を回すと ``docs/bench/c8/`` にも写る。
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
LEDGER = REPO / "tools" / "c8" / "sensitivity_v1.json"


def main(argv: list[str]) -> int:
    manifest = json.loads(Path(argv[0]).read_text(encoding="utf-8"))
    per = Counter()
    for s in manifest["stages"]:
        per[s["stage"]] += len(s.get("expedients") or ())
    total = sum(per.values())
    doc = json.loads(LEDGER.read_text(encoding="utf-8"))
    be = doc["build_manifest_expedients"]
    if be.get("count") == total and "note_2026_10_14_pre_2_4" in be:
        print("書き換え済み")
        return 0
    stages = "・".join(f"{st} {n}" for st, n in sorted(per.items(), key=lambda kv: int(kv[0][1:])) if n)
    be["note_2026_10_14_pre_2_4"] = be["note"]
    be["note"] = (
        f"〔改訂(第 2 期 2-4・V1 の活性化)〕data/world/v2/build_manifest.json の各段階 expedients 欄に {total} 行の自由文がある"
        f"({stages})。2-3b の W12 1.2.0(実ダイヤ)で 123 行から 8 行増え 5 行消えた(等間隔の推定の 5 行=前の W12#4〜#8 → "
        "実ダイヤの宣言 8 行=W12#4〜#11)。W9 は 5 行のまま(SHADOW_DATES の文言は同じ)。増えた行の 3 分類は実装役の案"
        "(未リサーチ)・D-44 の列は未判定の印(D44_PENDING)。前の注記は note_2026_10_14_pre_2_4(と note_2026_10_12_pre_act)。"
    )
    be["count"] = total
    qs = doc["open_questions"]
    old = [q for q in qs if "123 行" in q]
    if len(old) != 1:
        raise RuntimeError(f"123 行の問いが 1 つでない: {len(old)}")
    i = qs.index(old[0])
    judged = int(doc["build_manifest_judgment"]["judged"])  # 既存の台帳行の外(--judge-manifest で作り直した後の値)
    qs[i] = (
        f"build_manifest の expedient {total} 行(〔改訂(第 2 期 2-4)〕W12 の実ダイヤで 123 行から +8・−5。〔改訂(第330 ACT)〕"
        "10e の構築側で 121 行から +6・−4。09-09 は 122・第306 の段の改版で −1)のうち、設計書が感度試験を宣言しているのは"
        " 14 アンカー(build_manifest の 14 行・S-W14-JRPHASE の行=等間隔ダイヤは消えた)+RAKE 1 行だけ。"
        f"残り {judged} 行の扱い=D-44 (a)(第229 決定)で一括判定(build_manifest_judgment)・(c) 依存グラフ(第307)の次は"
        "ユーザー判断。増えた行(10e の 6 行・2-4 の W12 8 行)の D-44 は未判定。"
    )
    doc.setdefault("open_questions_pre_2_4", []).append(old[0])
    LEDGER.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"count {total}・問いの文を直した")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
