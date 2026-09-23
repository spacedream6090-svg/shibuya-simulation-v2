# Li, Dou, Shao, Chen & Hu 2025/2026 — Evaluating Scoring Bias in LLM-as-a-Judge

- リンク: https://arxiv.org/abs/2506.22316 | 分野: 自然言語処理・機械学習 #27 / 検証とV&V #22 | 重要度: **P1**(**8B に数値尺度を書かせない**判断の直接根拠)
- **一次確認**: **実読**(2026-09-17・リサーチサブが v4 PDF を WebFetch → pymupdf で本文抽出。**親未確認**)。v4 = 2026-02-03・**DASFAA 2026 採択**・CC BY 4.0・コード github.com/KMdsy/scoring_bias。

## 主張(claim)

LLM に**絶対評点**を書かせる側のバイアスは、比較評価(pairwise)側より研究されていない。採点規準の並び順・スコア ID の表記・参照解答の点数という 3 つの摂動で、**最先端モデルでも評点が大きく壊れる**。**小型モデルほど壊れ方が激しい。**

## 機構(mechanism)

同じ回答に対し、判定プロンプトだけを摂動する:
- **rubric order bias**: 採点規準を昇順 → 降順 / ランダム順に並べ替える。
- **score ID bias**: スコアの表記をアラビア数字 → 英字(Letter-Grades)/ ローマ数字に変える。
- **reference answer score bias**: 参照解答に 1〜5 点の札をつけて見せる(Ref-1 〜 Ref-5)。
指標は **FR(flip rate・点が変わった割合)** と **MAD(平均絶対差)**、および人間の金標準との Spearman ρ / Pearson r。

## 数値(出所つき)

- 判定モデル(逐語): "They are **GPT-4o, DeepSeek-V3-671B, Qwen3-32B, Qwen3-8B, and Mistral-Small-24B-Instruct-2501**." ベンチは BiGGen Bench と FLASK(いずれも 5 段階)。
- **核心の逐語**: "An exception is **Qwen3-8B, whose score distribution is more significantly influenced by biases, possibly due to its small size**."
- **核心の数値(逐語)**: "Qwen3-8B, for example, suffers a **46.22% FR** on BiGGen Bench under a simple rubric reordering. The larger Qwen3-32B is far more stable (**28.56% FR**) under the same perturbation, confirming the link to model scale."
  Table 3 の該当セル: Qwen3-8B / Descending-Numeric = **FR 46.22・MAD 0.5296**(5 段階で平均 0.53 点ずれる)。Qwen3-32B = 28.56 / 0.3281。GPT-4o は "FRs less than 25% and MADs less than 0.3 under perturbation in most cases"。
- **中心化・偏りの逐語**: "Under unbiased conditions, **DeepSeek-V3-671B assigns a score of 5 to more than half** of the instruction-response pairs. Compared to the human scoring distribution, **Mistral-Small-24B-Instruct has a stronger tendency to assign a score of 4**" / "GPT-4o demonstrates a preference for a score of 4"。
- 摂動が**精度を上げる**場合もある(逐語): GPT-4o はローマ数字にすると金標準との相関が上がるが、"when DeepSeek-V3-671B, Qwen3-32B and Qwen3-8B are employed as judge models, the use of Roman numerals generally exerts a **negative effect** on their scoring accuracy."
- 対策(逐語): "for high-stakes evaluations, selecting a powerful model like GPT-4o is a primary strategy"(= **規模を上げる**のが第 1 の対策)。

## 効く箇所(seam)

- **C10 R9′(i) の尺度(3 値か 5 値か)**。本 repo の本番 LLM は **8B INT8**。この論文の Qwen3-8B と同じ級。**「会話応答に `関係: +1/0/−1` を書かせる」は、この壊れ方の直撃圏内**。
- 併せて **T2 のオフライン抽出**(R9′ (ii))で点を書かせる設計にも同じ警告が当たる。

## 「結論でなく機構として」の入れ方

- 借りるのは「8B は駄目」ではなく **「同じ意味の書式を変えて、答えが変わるかを測る」という検査手順**。C10 の受入に **「欄の並びを入れ替えた腕で辺の分布が変わらないか」** を 1 本入れれば、本 repo 版の FR が測れる(呼数は 1 腕ぶん)。
- **回避策は「LLM に数を書かせない」**: 符号をエンジンの `ResultCode`(REFUSED / PARTNER_NO_SHOW / 成立)から取れば、この全バイアスが構造的に効かない。

## コスト/スケール含意

対策の第 1 が「大きいモデルを使う」であることは、本 repo にとって**使えない対策**(L4 400 万呼/日 × 8B が前提)。したがって**設計で回避する**しかない。

## 批判・限界

- 判定対象は**指示応答の品質**であって「会話相手への好悪」ではない。本 repo の用途への外挿は**類推**。
- Qwen3-8B であって本 repo の 8B と同一モデルではない。
- 「並び替えで 46% が変わる」は**摂動下**の値。無摂動で安定していれば実害が小さい可能性は残る(ただし分布そのものが人間とずれている、と同論文の図 5 が示す)。
- 3 値と 5 値の**直接比較はしていない**。5 段階での結果である。

## 関連

[[personality__contreras2026_llm-selfreport-behavior-gap]] ・ [[relations__bougie2025_citysim-social]] ・ `../v2-personality-traits-research.md` §3-2/§3-3 ・ `../v2-c10-initial-relations-research.md` §2-2 ・ メモリ `fewshot-time-anchoring-8b`
