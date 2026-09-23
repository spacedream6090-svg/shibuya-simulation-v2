# Gilbert & Karahalios 2009 — Predicting Tie Strength With Social Media

- リンク: https://doi.org/10.1145/1518701.1518736 (本文 PDF: https://userpages.umbc.edu/~skane/classes/is760/fall2011/c3/PredictTieStrength.pdf) | 分野: 社会ネットワーク科学 #14 / 計算社会科学 #25 | 重要度: **P1**
- **一次確認**: **実読**(2026-09-17・リサーチサブが WebFetch で PDF 取得 → システム python の pymupdf で本文抽出。**親未確認**)。CHI 2009, April 4–9, Boston。著者版 eegilbert.org は ECONNRESET。

## 主張(claim)

社会メディアの痕跡から紐帯の強さ(tie strength)を連続量として予測できる。**70 超の変数を投げたとき、標準化 β が最大の 2 つは「最終接触からの日数」と「初回接触からの日数」**——すなわち **recency と duration**。情動語は上位 15 の 12 位にとどまる。

## 機構(mechanism)

Granovetter 1973 の 4 要素を先行研究 4 系統に照らして **7 次元**(Intensity / Intimacy / Duration / Reciprocal Services / Structural / Emotional Support / Social Distance)に展開し、Facebook の観測量を各次元に割り当てる。参加者が自分の友人をスライダで評定した値を目的変数に、変数はすべて対数変換して重回帰。次元間の交互作用も入れる。自我中心設計の非独立性に対して**自由度を半分に切る**保守的な補正。

## 数値(出所つき)

- 標本(逐語): "Table 1. Thirty-two of over seventy variables used to predict tie strength, collected for each of the **2,184 friendships** in our dataset." 参加者 **35 名**。
- 性能(逐語): "the model fits the data very well: **Adj. R2 = 0.534, p < 0.001**. It achieves a **Mean Absolute Error of 0.0994** on a continuous 0–1 scale"
- **Table 3 上位 15(β / F / p)**: Days since last communication **−0.76** / 453 / <0.001 ・ Days since first communication **0.755** / 7.55 / <0.001 ・ Intimacy×Structural 0.4 / 12.37 ・ Wall words exchanged 0.299 / 11.51 ・ Mean strength of mutual friends 0.257 / 188.2 ・ Educational difference −0.22 / 29.72 ・ Structural×Structural 0.195 ・ Recip.Serv.×Recip.Serv. −0.19 ・ Participant-initiated wall posts 0.146 / 119.7 ・ Inbox thread depth −0.14 / 1.09 / 0.29 ・ Participant's number of friends −0.14 ・ **Inbox positive emotion words 0.135 / 3.64 / 0.05** ・ Social Distance×Structural 0.13 ・ Participant's number of apps −0.12 / 2.32 / 0.12 ・ Wall intimacy words 0.111。
- 逐語: "The utility distribution of the predictive variables forms a power-law distribution: **with only these fifteen variables, the model has over half of the information it needs**"
- Granovetter の定義(本論文が引く逐語): "The strength of a tie is a (probably linear) combination of **the amount of time, the emotional intensity, the intimacy (mutual confiding), and the reciprocal services** which characterize the tie."
- 交互作用(逐語): Intimacy×Structural F₁,₉₇₁=12.37 ・ Social Distance×Structural F=34 ・ Recip.×Recip. F=14.4 ・ Structural×Structural F=12.41(いずれも p<0.001)。

## 効く箇所(seam)

**C10 R9/R9′ の「辺の増減 Δ」**。recency と duration が支配するなら、Δ を種類ごとに重みづける必要はなく、**エピソードの時刻列を持てばよい**=ACT-R 基底活性 `A=ln Σ(Δt+1)^(−d)`(認知設計書 §4 の既決式)がそのまま辺の強さになる。

## 「結論でなく機構として」の入れ方

借りるのは β の値ではなく **「辺の強さは接触の時刻列の関数である」という形**。加えて **7 次元のうち Structural(共通の友人・グループ)が交互作用でしか効かない**という知見は、三者閉包(台帳 B2)を線形の加点でなく**乗法の修飾**として入れるべきことを示唆する。

## コスト/スケール含意

予測側は回帰なので安い。本 repo にとって重要なのは**保持コスト**: recency を使うには辺ごとに **最終相互作用時刻**が要る(uint32 4 B/辺)。duration を使うには **初回時刻**も要る(さらに 4 B)。40 万体 × k=15 で +47 MB。M5(6 KB/体)内。

## 批判・限界

- **著者自身の但し書きが重い**(逐語): "The two Days since variables have such high coefficients due to **friends that never communicated via Facebook**. Those observations were assigned outlying values: zero in one case and twice the maximum in the other."
  → β=−0.76 は「recency が連続的に効く」証拠ではなく、**「接触 0 回 / 1 回以上」の段差**の効果を多く含む。**この但し書きを落として引いてはいけない**。
- 2009 年の Facebook・**大学コミュニティの便宜標本**(著者注: "that may reflect the university community from which we sampled participants")。対面・日本・都市の雑談には外挿していない。
- 目的変数は**自己申告のスライダ**。行動ではない。
- Inbox thread depth が**負**(同じ話題でやり取りが長いほど弱い)など、直観に反する符号が残る。

## 関連

[[relations__dunbar2020_structure-function]] ・ [[relations__robertsdunbar2015_relationship-decay]] ・ [[relations__zhao2012_actr-dunbar-network]] ・ `../v2-c10-initial-relations-research.md` §1-2
