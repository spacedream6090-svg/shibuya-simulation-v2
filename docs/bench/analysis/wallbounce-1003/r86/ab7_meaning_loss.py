# -*- coding: utf-8 -*-
"""R-86: 手の分類(ab7_labels.py)と段0 辞書の写像(ab7_sample300.json)を突き合わせ、意味が落ちた割合を出す。

使い方: python ab7_meaning_loss.py <ab7_sample300.json> <out_json>
分母: 段0 辞書で既存の語に写された行(stage == "stage0")。既存の値「約 37%」も同じ分母
(段0 を通った 34,272 行のうち意味の損失を伴う約 12,700 行)。
"""
from __future__ import annotations

import json
import math
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from ab7_labels import labels  # noqa: E402


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    d = 1 + z * z / n
    c = p + z * z / (2 * n)
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return ((c - h) / d, (c + h) / d)


def main(src: str, dst: str) -> None:
    s = json.loads(Path(src).read_text(encoding="utf-8"))
    lab = labels()
    rows = s["sample"]
    assert len(rows) == len(lab)
    for r, (p, l) in zip(rows, lab):
        r["purpose"], r["loss"] = p, l
        # 整合の検査: 損失コード v/u と、写像の段が食い違っていないか
        if l == "v":
            assert r["stage"] == "vocab", r
        elif l == "u":
            assert r["stage"] == "undefined", r
        else:
            assert r["stage"] == "stage0", r
    st0 = [r for r in rows if r["stage"] == "stage0"]
    n = len(st0)
    cnt = Counter(r["loss"] for r in st0)
    m = cnt["m"]
    mk = cnt["m"] + cnt["k"]
    mkt = mk + cnt["t"]
    # 辞書の政策表(語彙政策 v0)での分類を、同じ行に当てた場合(比較用): 食べる/飲む・観察系=意味の損失
    policy_meaning = {"食べる", "飲む", "様子を見る", "知らせる", "対応する", "観察", "眺める", "見物", "見学",
                      "確認", "調べる", "調べ", "調査", "チェック"}
    pol = sum(1 for r in st0 if any(w in r["raw_action"] for w in policy_meaning))
    purpose_all = Counter(r["purpose"] for r in rows)
    by_raw = Counter((r["raw_action"], r["stage0"], r["loss"]) for r in st0)
    out = {
        "n_sample": len(rows),
        "stage_counts": dict(Counter(r["stage"] for r in rows)),
        "stage0_n": n,
        "loss_counts_stage0": dict(cnt),
        "meaning_loss_strict": {"k": m, "rate": m / n, "wilson95": wilson(m, n)},
        "meaning_loss_incl_minor": {"k": mk, "rate": mk / n, "wilson95": wilson(mk, n)},
        "meaning_or_target_loss": {"k": mkt, "rate": mkt / n, "wilson95": wilson(mkt, n)},
        "policy_table_rate_same_rows": {"k": pol, "rate": pol / n},
        "purpose_counts_all300": dict(purpose_all),
        "purpose_not_expressible_v1": {
            "note": "目的が語彙 v1(24 語)の語で表せない行(E 食事・D 喫茶で飲食店に座る・O 観察・A 雨宿り)。行く→移動のように動詞は落ちていなくても、目的の行為はその後に表す語が無い",
            "k": sum(1 for r in rows if r["purpose"] in ("E", "O", "A")),
        },
        "by_raw_mapped_loss": [{"raw": a, "stage0": b, "loss": c, "n": v} for (a, b, c), v in by_raw.most_common()],
        "sample": rows,
    }
    Path(dst).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8", newline="\n")
    print(json.dumps({k: out[k] for k in list(out)[:9]}, ensure_ascii=False, indent=1))
    print(out["by_raw_mapped_loss"])


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
