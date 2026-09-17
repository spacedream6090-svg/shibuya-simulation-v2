# Saramäki, Leicht, López, Roberts, Reed-Tsochas & Dunbar 2014 — Persistence of social signatures in human communication

- リンク: https://doi.org/10.1073/pnas.1308540110 (実読した版: https://arxiv.org/abs/1204.5602) | 分野: 社会ネットワーク科学 #14 / 計算社会科学 #25 | 重要度: **P1**
- **一次確認**: **実読**(2026-09-17・リサーチサブが **arXiv v2 (2013-12-16) の PDF** を WebFetch → pymupdf で本文抽出。**PNAS 本体・Europe PMC はいずれも 403 で取得不能**。**親未確認**)。*PNAS* 111(3):942–947。

## 主張(claim)

**個体が「誰に」通話するかは 18 か月で大きく入れ替わるが、「どの順位にどれだけの割合を配るか」という形(social signature)は、その個体固有のまま保たれる。** 新しい相手が入ると、古い相手が置き換わるか通話が減り、**全体の配分が保存される**。

## 機構(mechanism)

有限の資源(通信に使える時間・親密な関係を維持する認知と情動の努力・情動投資の能力)が配分の形を決める、と著者らは解釈する。相手の同一性は状況で変わるが、**配分の形は個体の性質**。

## 数値(出所つき)

- 標本(逐語): "tracked changes in the ego networks of **24 students over 18 months** as they made the transition from school to university or work"。通話記録 + 3 時点の質問紙(t1 / 9 か月 / 18 か月)。18 か月を **6 か月 × 3 区間(I1/I2/I3)**に分割。24 名中 **18 名**が大学へ進学。
- 手続き: 各区間で相手ごとの通話数を数え → 順位づけ → 順位ごとの通話割合 = social signature。区間間の Jensen–Shannon 距離で自己距離 d_self、他者との距離 d_ref を比較。
- **持続(逐語)**: "On average, for each ego, **82% ± 12%** of the distances to others d_ref were greater than d_self." 平均 "⟨d_self⟩ = **0.036 ± 0.014**" vs "⟨d_ref⟩ = **0.086 ± 0.055**"(⟨d_self⟩ < ⟨d_ref⟩, p < 10⁻⁴, Welch's t-test)。ℓ2 ノルムでも同様(0.096±0.039 vs 0.154±0.084)。
- **入替(逐語)**: "for the entire networks of participants, **⟨J(I1, I2)⟩ = 0.22 ± 0.09 and ⟨J(I2, I3)⟩ = 0.27 ± 0.09**" / 上位 20 位に限っても "**⟨J(I1, I2)⟩ = 0.36 ± 0.13**"。最大の入替は I1→I2(p=0.001, paired t-test)= 卒業と進学の時期。
- **順位の保持(逐語)**: "**even of the highest-ranked alters, only 42% retain their top rank from interval I1 to I2, and 54% from I2 to I3**."
- 抄録の要旨(逐語): "as new network members are added, some old network members are either replaced or receive fewer calls, **preserving the overall distribution of calls across network members**. This is likely to reflect the consequences of finite resources such as the time available for communication, the **cognitive and emotional effort required to sustain close relationships**, and the ability to make emotional investments."

## 効く箇所(seam)

- **C10 の holdout 候補**。d_self < d_ref の割合(82%±12%)と Jaccard(0.22 / 0.27)は、**初期網の与え方に依存しにくい**(形の保存は入替と独立に成立するのが主張)ので、ウォームアップの採否で結論が動きにくい良い物差し。
- 行動契約 §5 の「激変時 18 か月で 40%」の**原典**。**Dunbar 2020 の要約 40% でなく Jaccard を引くべき**。

## 「結論でなく機構として」の入れ方

- 借りるのは「形が保たれる」でなく **「有限資源の配分として辺を持つ」**。基底活性方式(`A=ln Σ(Δt+1)^(−d)` + 検索閾値 τ)は、まさに**総エピソード数が有限なら順位 - 割合曲線が決まる**構造なので、この論文の機構と両立する。
- 測り方も借りる: **区間を切り、順位 - 割合曲線を作り、自己距離と他者距離を JSD で比べる**。本 repo の JSD 集計(AB7 の語彙比較で既に使っている道具)がそのまま使える。

## コスト/スケール含意

測定は集計だけ(呼数 0 増)。ただし **区間を切るには最低 2 区間 = 2 期間分のラン**が要る。6 か月 × 3 = 18 か月は不可能なので、**シミュ日を区間として短縮する**(例: 7 日 × 3 区間)しかない。**時間スケールの読み替えが expedient になる**ことを宣言する必要がある。

## 批判・限界

- **標本 24 名**。しかも全員が「学校から大学・就職へ」という同じ激変を経験した若年層。定常期の一般人口ではない。
- **通話記録のみ**。対面・SNS・同居者は入らない。渋谷の来街者にはほぼ当たらない。
- 「形が保たれる」は **JSD の自己 < 他者**という相対的な主張。絶対的な形の一致ではない(⟨d_self⟩=0.036 はゼロではない)。
- arXiv v2 を読んでおり **PNAS 掲載版との差分は未確認**(親確認対象)。

## 関連

[[relations__dunbar2020_structure-function]] ・ [[relations__robertsdunbar2015_relationship-decay]] ・ `../../design/v2-pattern-ledger.md` B3/B4 ・ `../v2-c10-initial-relations-research.md` §1-5
