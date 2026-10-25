"""第 2 期 2-4 V1: C8 の 3 分類の表(``tools/c8/expedient_triage_v1.json``)の W12 の行を活性化の後の build_manifest に合わせる。

活性化で W12 の expedient が 8 → 11 行になる(等間隔の推定の 5 行=前の W12#4〜#8 が消え、実ダイヤの宣言 8 行=
``w12_external_nodes.REAL_TIMETABLE_EXPEDIENTS`` が W12#4〜#11 に入る)。鍵は段の中の番号なので、前の W12#5〜#8 の
対照(等間隔の推定の行のもの)を新しい文言の行に当てない。前の値は ``note`` に残す(10e ACT と同じ書き方)。
3 分類と対照は**実装役の案=未リサーチ(expedient)・費用は目安で未測**。

    python docs/bench/analysis/wallbounce-1012/vb24/tools/triage_w12_2_4.py   # 表を書き換える(1 回だけ)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
TRIAGE = REPO / "tools" / "c8" / "expedient_triage_v1.json"
TAG = "〔第 2 期 2-4・実装役の案=未リサーチ(expedient)・費用は目安で未測〕"

NEW_ROWS: dict[str, dict] = {
    "W12#4": {"class": "ii", "control": TAG + "渋谷の発車の表だけ vs 到着の表で降りる便を作る(井の頭線は到着の表が手元にある)"
                                              "→ 5,000 体の CSB 対照(エンジンに到着の便の口が要る=2-3c)",
              "cost_seconds_estimate": None},
    "W12#5": {"class": "i", "control": TAG + "山手線 内回り=上り・外回り=下り vs 逆 → 向きごとの便の時刻分布 JSD"
                                             "(エンジンは向きを便の並びの決め方にだけ使う=tt23b §11 の 6)",
              "cost_seconds_estimate": 1},
    "W12#6": {"class": "ii", "control": TAG + "湘南新宿ラインを埼京線に畳む vs 別の線(エンジンの線別の定員・混雑率の表と方面ノードの"
                                              "線を同じ版で足す口が要る=6-2)→ 5,000 体の CSB 対照",
              "cost_seconds_estimate": None},
    "W12#7": {"class": "i", "control": TAG + "土休の ◆ 特急 4 本を外す vs 残す → 土休の便の時刻分布 JSD",
              "cost_seconds_estimate": 1},
    "W12#8": {"class": "iii", "control": TAG + "JR の版の宣言(2026-03-14 改正と推測)=別の版の表が手元に無く対照を定義できない",
              "cost_seconds_estimate": None},
    "W12#9": {"class": "i", "control": TAG + "銀座線=9 月改正の版 vs 7 月の取得(2026-07-07・世界の時点の版・手元にある)"
                                             "→ 便の時刻分布 JSD",
              "cost_seconds_estimate": 1},
    "W12#10": {"class": "iii", "control": TAG + "井の頭線の版の宣言(dct:issued が世界の時点に効いていたと推測)=別の版の表が無く"
                                                "対照を定義できない",
               "cost_seconds_estimate": None},
    "W12#11": {"class": "ii", "control": TAG + "直通の二重(東横線・田園都市線の上り=副都心線・半蔵門線と同じ列車)vs 二重を除く"
                                               "→ 5,000 体の CSB 対照(直通のまとめ方は 2-3c)",
               "cost_seconds_estimate": None},
}


def main() -> int:
    doc = json.loads(TRIAGE.read_text(encoding="utf-8"))
    rows = doc["rows"]
    if all(rows.get(k) == v for k, v in NEW_ROWS.items()):
        print("書き換え済み")
        return 0
    prev = {k: rows[k] for k in sorted(NEW_ROWS, key=lambda s: int(s.split("#")[1])) if k in rows}
    for k, v in NEW_ROWS.items():
        rows[k] = v
    doc["rows"] = dict(sorted(rows.items(), key=lambda kv: (int(kv[0][1:].split("#")[0]), int(kv[0].split("#")[1]))))
    doc["note"] += (
        "〔改訂(第 2 期 2-4・V1 の活性化)〕W12 の expedient が 8 → 11 行(等間隔の推定の 5 行=前の W12#4〜#8 が消え、実ダイヤの"
        "宣言 8 行が W12#4〜#11 に入る・build_manifest は 123 → 126 行)。W12#4〜#11 の 3 分類と対照は実装役の案(未リサーチ)。"
        "前の行の値(等間隔の推定の行のもの): " + json.dumps(prev, ensure_ascii=False)
    )
    TRIAGE.write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    print(f"書き換えた {len(NEW_ROWS)} 行(前の値 {len(prev)} 行は note に残した)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
