# Schneider, Tian & Rizoiu 2025 — Learning to Make Friends: Coaching LLM Agents toward Emergent Social Ties

- リンク: https://arxiv.org/abs/2510.19299 | 分野: 計算社会科学 #25 / 自然言語処理・機械学習 #27 / 社会ネットワーク科学 #14 | 重要度: **P2**
- **一次確認**: **実読**(2026-09-17・リサーチサブが v2 PDF を WebFetch → pymupdf で本文抽出。**親未確認**)。**CC BY 4.0**。EPFL + UTS。査読の記載なし。

## 主張(claim)

LLM エージェントを**関係ゼロ(E₀ = ∅)から**相互作用させ、行動報酬(social interaction / information seeking / self-presentation / coordination / emotional support)と in-context 学習で回すと、**実在のオンライン共同体に似た網構造が創発する**。

## 機構(mechanism)

- 逐語(冷スタート): "Once the personas are initialized and their distinct personalities verified through a **pre-survey assessment**, we initiate the simulation. Each agent engages in a conversation on a predefined topic. At time t = 0, we observe the social network G₀ = (V, E₀, A₀) with **E₀ = ∅**, indicating that there are **no edges and no prior knowledge** among users in V ... Our objective is to characterize the network structure G_T that emerges after the agents' interactions."
- 開幕(逐語): "In the opening round (t = 1), agents are **unaware of one another** and are therefore required to make a public post (POST). In subsequent rounds, they may choose to post (POST), comment (COM), send a direct message (DM), or take no action (NOT)."
- **辺の更新式(逐語・親案②との直接比較対象)**:
  > "the tie strength is updated using a **gated update rule** that differentiates between active and passive rounds. On active rounds, the tie is strengthened based on a scalar evidence score e_t(u→v) ∈ [0,1], which aggregates the quality of the interaction. On passive rounds—when no directed interaction from u to v occurs—the tie strength decays."
  > `[A_{t+1}]_uv := [A_t]_uv + min( Δmax, (1−[A_t]_uv)[e_t(u→v) − ξ]_+ )` if ζ_t(u→v) = 1 ; `(1−δ)·[A_t]_uv` if ζ_t(u→v) = 0
  > "where **ξ ∈ [0,1) is a minimum-evidence threshold, Δmax ≥ 0 caps the per-round increase, δ ∈ [0,1) controls decay**, and [x]₊ = max{0,x}. The scaling term 1−[A_t]_uv ensures that increases become smaller as the tie approaches its maximum value, while decay acts multiplicatively to gradually fade inactive ties. **To interpret δ, one can parameterize it via a half-life h such that δ = 1 − 2^{−1/h}**."
- 活性化のチャネル(逐語): `ADDRESS`(DM または mention)と `ENGAGE`(コメントまたは投票)の OR。
- 評価指標: 最大弱連結成分の相対サイズ LCC・平均最短路長 L(G)・**コミュニティ modularity Q**。

## 数値(出所つき)

- モデル(逐語・脚注 2): "Due to API rate limits, the experiments presented in this work were conducted using **OpenAI's GPT-4o mini**."
- 学習の傾向(逐語): "the information-seeking (INF) policy is typically the easiest to learn ... Emotional support (EMO) attains comparatively high values, reflecting the generally positive behavior of most agents. Self-presentation (PRE) can be partially controlled through personal posts, whereas **policies that depend on coordination (SOC, COORD) are more difficult to learn**."
- コーチの効果(逐語): "the coach **accelerates early learning** for some policies but **does not yield a uniform late-round improvement**"。
- **体数・ラウンド数は本文の抽出では確定できなかった(空欄)**。

## 効く箇所(seam)

**C10 の着手条件②(Δ と半減期)と R2(初期化)**。本論文は「2025 年の最先端でも、辺の更新は**設計者の数 4 個**(ξ・Δmax・δ、そして半減期 h)で書かれている」ことを示す。親案②(会話+1・同席+0.5・約束+2・断る−1・すっぽかし−2・半減期 30 日 = 数 6 個)は**分野の標準の範囲内**であり、異常ではない。

## 「結論でなく機構として」の入れ方

- **借りないほうがよい部分**: 式 (1) をそのまま採ると数が 4 個増える。本 repo は認知設計書 §4 で **ACT-R 基底活性 d=0.5 を既に決定済み**なので、同じ式を再利用すれば新しい数は検索閾値 τ だけになる([[relations__zhao2012_actr-dunbar-network]])。
- **借りるべき部分**: (a) **飽和項 (1−A)**(強い辺ほど伸びにくい)は Gilbert の「逓減」と整合し、行動契約 §5 の「強度 +Δ 逓減(expedient)」の一次的裏づけになる。(b) **active / passive の二値ゲート**という考え方(「何もしなかった」ことも状態遷移である)。(c) **評価を LCC / 平均最短路 / modularity で見る**という測り方。
- **冷スタートの位置づけ**: 本論文は「関係網が創発するか」が研究目的なので E₀=∅ が正しい。**本 repo は関係網を前提に別のもの(渋谷の再現)を測るので、冷スタートは目的が違う**(v1 資産の「コールドスタートは我々の規模では不可」と同じ結論)。

## コスト/スケール含意

小規模・GPT-4o mini・API レート制限で実験規模が制約された、と著者が明記している。**39 万体にスケールした事例ではない**。

## 批判・限界

- **査読の記載がない**(v2・2025-10)。
- **体数・ラウンド数・実データとの定量比較が本文抽出では確認できなかった**。「mirror properties of real online communities」という主張の強さは未検証(親確認対象)。
- 4 個のハイパーパラメータ(ξ・Δmax・δ・h)の**値が本文に書かれていない**(抽出範囲内では)。
- オンライン(投稿・コメント・DM)の設定であり、**対面の同席・偶然の遭遇が無い**。本 repo の C9 幾何とは前提が違う。

## 関連

[[relations__zhao2012_actr-dunbar-network]] ・ [[relations__bougie2025_citysim-social]] ・ `../v2-c10-initial-relations-research.md` §3-1
