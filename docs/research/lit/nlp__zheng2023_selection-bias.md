# Zheng, Zhou, Meng, Zhou & Huang 2023 — Large Language Models Are Not Robust Multiple Choice Selectors

- リンク: <https://arxiv.org/abs/2309.03882> / 本文 <https://arxiv.org/html/2309.03882v4> | 分野: 自然言語処理・機械学習 #27 | 重要度: **P1**
- **一次確認**: **実読(サブ・2026-09-17・arXiv HTML v4)・親未確認**。v1 2023-09-07 / v4 2024-02-22。**ICLR 2024 Spotlight**。
- **なぜ引くか**: **「候補を並べて選ばせる」ときの偏りが、小さいモデルほど大きい**ことの一次。R-37 の H(候補提示型)を 8B で回すときの最大の交絡。

## 主張(claim)

LLM は選択肢問題で「特定の選択肢 ID(A/C など)を選びやすい」という**選択バイアス**を持つ。主因は**位置**ではなく**トークン**である。ID の事前分布を推定して除くだけで、精度も頑健性も上がる。

## 機構(mechanism)

- **選択バイアス(逐語・定義)**: 「selection bias is defined as the model's **behavioral bias to select specific option IDs** as answers.」
- **トークンバイアス(逐語・原因)**: 「the model may **a priori assign more probabilistic mass to specific ID tokens** (such as A or C).」
- **位置バイアス(対比・逐語)**: 「The model may favor options presented at specific ordering positions (such as the first or last one)」——著者の結論では「somewhat present but **quite irregular**」。
- **PriDe**: 少数の標本(5%〜80%)で選択肢 ID の事前分布を推定し、推論時に予測分布から除く。ラベル不要。

## 数値(表番号まで)

**指標 RStd = 選択肢 ID ごとの recall の標準偏差**(大きいほど偏っている)。著者(逐語)「we use the **standard deviation of recalls (RStd)** as a quantitative metric」。

**Table 3・0-shot・MMLU / ARC / CSQA**

| モデル | MMLU | ARC | CSQA |
|---|---|---|---|
| llama-7B | 18.5 | 9.9 | 21.6 |
| llama-13B | 17.4 | 14.2 | 19.9 |
| llama-30B | 8.5 | 4.6 | 11.2 |
| llama-65B | 8.3 | 8.8 | 15.3 |
| **llama-2-7B** | **23.0** | 27.4 | 28.4 |
| llama-2-13B | 7.5 | 6.0 | 10.2 |
| **llama-2-70B** | **4.1** | 2.3 | 7.3 |
| falcon-7B | 24.2 | 29.2 | 29.9 |
| falcon-inst-7B | 28.7 | 23.4 | 25.7 |
| falcon-40B | 6.7 | 6.8 | 15.9 |
| gpt-3.5-turbo | 5.5 | 3.3 | 2.2 |

→ **同一系列で 7B は 70B の約 5.6 倍(23.0 vs 4.1)。** ただし著者自身は「**we do not observe consistent patterns of selection bias within the same model family**」とも書き、falcon-7B 系は「undertrained」(MMLU 精度が無作為 ~25% 近辺)と注記している。**「小さいほど偏る」を法則として引いてはいけない**(値としては引ける)。

**Table 1「answer-moving attack」(正解を特定位置へ寄せる・0-shot MMLU)**: llama-30B 53.1 → **68.2(A・+15.2)/ 41.2(D・−11.9)**。gpt-3.5-turbo 67.2 → 74.2(C・+6.9)/ 60.9(D・−6.3)。falcon-inst-40B 51.5 → 38.3(A・−13.3)/ 69.1(D・+17.6)。

**PriDe の効果(Table 3・20 LLM の平均 Δ・RStd 変化 / 精度変化)**: MMLU 5%(費用 ×1.15)−7.6 / +1.2、40%(×2.2)−8.9 / +2.6、80%(×3.4)−9.1 / +4.1。総当り置換(×4)−8.7 / +4.9。個別例: **llama-2-7B の MMLU は RStd 23.0 → 5.5、精度 35.8 → 40.2**(PriDe 5%)。

- 選択肢数: MMLU・ARC は **4 択**、CSQA は **5 択**(2 択・3 択の ablation もあり)。

## 効く箇所(seam)

- **R-37 §5-1「番号ラベル」**: **候補に「1 2 3 4」「A B C D」を振らない**。v2 の「対象」欄は自由文なので、ラベルなしで項目そのものを書かせられる。
- **R-37 §4-3 A3 腕**: 位置バイアスは「somewhat present but irregular」なので、**順序撹拌で消えるとは限らない**。A2/A3 の差が小さくても「偏りが無い」ことにはならない(P-7 で提示順位別選択率を直接測る理由)。
- **8B 据置(第205 等)の追加の代価**として登録できる。

## 「結論でなく機構として」の入れ方

- **借りる**: ラベルを付けないという形・順位別選択率を必ず測るという形。
- **借りない**: RStd の絶対値(尺度が MCQ 固有)・PriDe(**v2 の対象欄は自由文でロジット後処理をしていないので適用先が無い**=答申 §6 ④)。

## コスト/スケール含意

PriDe は費用 ×1.15〜×3.4。**v2 では採れない**(400 万呼/日)。

## 批判・限界

1. タスクは全部 **MCQ ベンチ**(MMLU・ARC・CSQA)。**POI 候補のような意味のある選択肢での検証ではない**(そちらは [[mobility__feng2024_llm-move-candidate-order]])。
2. Qwen 系は対象に入っていない(**本 repo の 8B は Qwen3-8B INT8**)=**直接の値は無い**。
3. 「小さいほど偏る」は著者の主張ではない(値の傾向にすぎない)。

## 関連

[[mobility__feng2024_llm-move-candidate-order]] ・ [[nlp__turpin2023_unfaithful-cot]] ・ [[nlp__springer2026_annotation-anchoring]] ・ 答申 `../v2-destination-choice-llm-research.md` §3-1・§3-2
