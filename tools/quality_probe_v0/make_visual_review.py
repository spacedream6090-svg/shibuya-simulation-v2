# -*- coding: utf-8 -*-
"""make_visual_review.py — ユーザー目視12問の提示用 Markdown を probes.jsonl から生成する。

python make_visual_review.py                       # 空欄の用紙を作る
python make_visual_review.py --ledger quality_ledger.csv   # 測定後に3モデルの出力を流し込む
"""
import argparse, csv, io, json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import scorer

HERE = os.path.dirname(os.path.abspath(__file__))
PICK = ["F1-01", "F1-03", "F1-04", "F1-05", "F1-07", "F1-08",
        "F4-01", "F4-02", "F4-03", "F4-04", "F4-05", "F4-06"]

HEAD = """# ユーザー目視 12問(品質プローブv0)

> 生成元: probes.jsonl(item_set_hash = {hash})
> 内訳: 系統① T1行動判断から6問 / 系統④ T2内省から6問

## なぜ目視が要るのか(これだけは読んでほしい)

**日本語の品質劣化は、自動採点ではほとんど見えません。** 多言語量子化の研究では、日本語で
自動指標が **−1.7%** しか落ちていないのに、母語話者の人手評価では **−16.0%** 落ちていました
(約10倍の乖離)。しかも非ラテン文字の言語ほど悪化が大きく、難しいタスクほど早く壊れます。

機械判定が保証できるのは「壊れていないこと」だけで、「自然な日本語かどうか」は見ていません。
**この12問が、量子化による日本語劣化を見られる唯一の計器です。**

## 見かた(1問あたり1分)

各問について次の3つだけを記入してください。順位は「どれが一番人間らしいか」であって
「どれが一番正しいか」ではありません。

1. **順位**: 3つの出力を1位・2位・3位で並べる(同順位可)。
2. **壊れているか**: 明らかに日本語が壊れている・中国語や英語が混ざっている出力があれば
   その列に ✗ を付ける(**これが最も重要な情報です**)。
3. **ひとこと**: 気になった点があれば1行。

判定に使う基準は「渋谷にいる普通の人が書いた/言ったものとして自然か」。
長さの差、丁寧さの多さは理由にしないでください。

---
"""

FOOT = """
---

## 集計欄(記入後にここへ)

| 指標 | 8B INT8 | 14B INT8 | 32B AWQ |
|---|---|---|---|
| 1位になった問数(12問中) |  |  |  |
| 壊れている(✗)と付いた問数 |  |  |  |

**判断の目安**: ✗が1問でも付いたモデルは、機械判定の点数がよくても採用の再考が要る
(自動指標は日本語劣化を10倍過小評価するため)。
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--probes", default=os.path.join(HERE, "probes.jsonl"))
    ap.add_argument("--ledger", default=None)
    ap.add_argument("--out", default=os.path.join(HERE, "visual_review_12.md"))
    a = ap.parse_args()

    P = scorer.load_probes(a.probes)
    hp = os.path.join(HERE, "item_set_hash.txt")
    h = io.open(hp, encoding="utf-8").read().split("=")[-1].split("\n")[0].strip() if os.path.exists(hp) else "?"

    outputs = {}
    models = []
    if a.ledger and os.path.exists(a.ledger):
        with io.open(a.ledger, encoding="utf-8", newline="") as f:
            for r in csv.DictReader(f):
                if r["probe_id"] in PICK and r.get("variant") in ("main", ""):
                    m = r["model"]
                    if m not in models:
                        models.append(m)
                    p = os.path.join(HERE, r.get("raw_output_path") or "")
                    txt = io.open(p, encoding="utf-8").read().strip() if os.path.exists(p) else "(出力ファイルなし)"
                    outputs[(r["probe_id"], m)] = txt
    if not models:
        models = ["モデルA(8B INT8)", "モデルB(14B INT8)", "モデルC(32B AWQ)"]

    L = [HEAD.format(hash=h)]
    for n, pid in enumerate(PICK, 1):
        p = P[pid]
        fam = "① T1行動判断" if p["family"] == 1 else "④ T2内省"
        L.append("## %d. %s — %s(%s)" % (n, pid, p["title"], fam))
        L.append("")
        L.append("<details><summary>場面(クリックで展開)</summary>")
        L.append("")
        L.append("```")
        L.append(p["observation"])
        L.append("")
        L.append("問い: " + p["question"])
        L.append("```")
        L.append("")
        L.append("</details>")
        L.append("")
        L.append("**問い**: " + p["question"])
        L.append("")
        for m in models:
            L.append("**%s の出力**" % m)
            L.append("")
            L.append("```")
            L.append(outputs.get((pid, m), "(ここに出力を貼る)"))
            L.append("```")
            L.append("")
        L.append("| 記入欄 | %s |" % " | ".join(models))
        L.append("|---|%s" % ("---|" * len(models)))
        L.append("| 順位(1-3) | %s |" % " | ".join([" "] * len(models)))
        L.append("| 壊れている(✗) | %s |" % " | ".join([" "] * len(models)))
        L.append("")
        L.append("ひとこと: ")
        L.append("")
        L.append("---")
        L.append("")
    L.append(FOOT)
    with io.open(a.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(L))
    print("wrote", a.out, "(%d問)" % len(PICK))


if __name__ == "__main__":
    main()
