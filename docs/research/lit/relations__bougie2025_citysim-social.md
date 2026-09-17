# Bougie & Watanabe 2025 — CitySim: Modeling Urban Behaviors and City Dynamics with Large-Scale LLM-Driven Agent Simulation(社会モジュールに限る)

- リンク: https://arxiv.org/abs/2506.21805 | 分野: 計算社会科学 #25 / 人間移動科学 #3 / 小売科学・商業立地論 #17 | 重要度: **P1**(**渋谷の POI 人気と群集密度を照合対象にしている直接の競合**)
- **一次確認**: **実読**(2026-09-17・リサーチサブが PDF を WebFetch → pymupdf で本文抽出。**親未確認**)。arXiv:2506.21805v1。**AgentSociety (Piao et al. 2025) の枠組みの上に実装**。

## 主張(claim)

1,000 体の LLM エージェントを東京都市圏に置き、**辺ごとに {affinity, trust, familiarity} の「社会的信念ベクトル」**を持たせる。**初期値は人口統計的類似(homophily)と既存関係から与え、会話のたびに positive / neutral / negative の 3 分類で更新する。**

## 機構(mechanism)

- 逐語(§3.3): "The foundation of our social module is a weighted social network where each edge encodes an agent's evolving social beliefs about others. Each agent u maintains a social belief vector b_{u,v} for every contact v, capturing dimensions: ∈ {**affinity, trust, familiarity**}. These beliefs are **initialized at simulation start based on demographic similarity and relationships**, then updated continuously."
- 逐語: "After an interaction, b_{u,v} is updated using **observed outcome (positive, neutral, negative)** for each dimension."
- 逐語(付録 B): "Following each interaction, beliefs are updated by evaluating the sentiment and outcome of the exchange: **positive, neutral, or negative signals are extracted from the conversation** and used to **incrementally adjust** the affinity, trust, and familiarity scores between agents."
- 相手選択(逐語): "Agent u selects a conversation partner v according to their current belief score, with probability: **p_v = b_{u,v} / Σ_{v'∈V} b_{u,v'}**, where V is the set of eligible **co-located** agents"
- 会話の起点(逐語): "social interactions are not statically scheduled. Instead, **unmet social needs dynamically trigger acquaintance search and interaction planning**. For instance, when social satisfaction falls below a threshold, agents proactively evaluate whom to contact and whether the mode of interaction should be face-to-face or online. This decision process is handled by a **single LLM call**, producing both the modality and the target agent in structured form."
- 需要側: 4 つの需要 {hunger, energy, safety, **social**} ∈ [0,1]⁴ を毎日 LLM が初期化し、速度 α_n で減衰、閾値 T_n で優先。
- 空間記憶は POI 信念 b_i ∈ ℝᴷ {price, atmosphere, satisfaction, convenience} を **Kalman フィルタ**で更新し、日ごとに `b_{i,d} ← (1−λ)b_{i,d} + λ b_{0,d}`(中立値 0.5)で減衰。

## 数値(出所つき)

- 逐語: "All agents are powered by the **GPT-4o-mini** ... with the number of agents set to **1,000 located in Tokyo metropolitan area**."
- 渋谷(逐語): "we evaluate CitySim's as a predictive tool for real-world **POI popularity in Shibuya (Tokyo, Japan)**. Ground-truth was estimated using ratings from **Google Maps**." / "CitySim's ability to reproduce real-world patterns of pedestrian concentration across **Shibuya (Japan)**"
- 幸福度 5 クラス分類の macro F1(Table 1): GeAn 0.19 / AGA 0.20 / HumanoidAgent 0.22 / **AgentSociety 0.28** / MobileCity 0.21 / **CitySim 0.36** / **GBDT(勾配ブースティング)0.45**。
- 著者自身の限界(逐語): "These simulation-based approaches are limited by **incomplete agent background knowledge and imperfect persona initialization**, which restrict their ability to fully replicate the nuances of human well-being."
- 性格は Big Five を **1〜3 の 3 段階**で持つ。

## 効く箇所(seam)

- **C10 の着手条件 ①「3 値尺度(−1/0/+1)」**。親案は「未リサーチ(expedient)」と宣言されていたが、**同じ渋谷を狙う直近の先行が同じ 3 分類を採っている**=先例がある。
- **R2(初期化)**: 「人口統計的類似で初期化」は本 repo の W16(組織・世帯・学校・町丁目)でそのまま置ける。
- **R12(相手選択)**: `p_v = b_{u,v}/Σ b` は D-31 のフォールバック(セル内最小 id)の置き換えに使える形。ただし**共在集合 V の定義**が本 repo では C9 の距離 2 m になる。

## 「結論でなく機構として」の入れ方

- 借りるのは「3 値がよい」ではなく **「符号は語のカテゴリで持ち、量は別に持つ」という分離**。CitySim は量(incrementally adjust の刻み)を**論文に書いていない**=空欄なので、量まで真似てはいけない。
- 本 repo はさらに一歩進められる: **符号を LLM の抽出でなくエンジンの `ResultCode`(REFUSED / PARTNER_NO_SHOW / 成立)から取る**。CLAUDE.md §3「状態と集約はエンジン」に一致し、Contreras 2026 の「自己申告と LLM 審査の共有分散」の罠も避けられる。

## コスト/スケール含意

- 「社会需要が閾値を割ったら相手を探す」= **1 LLM 呼で相手と様式を決める**。本 repo の L4 に当てると、社会需要の起床が増えるだけ呼が増える(D-49 の近接入替と同じ暴発源になりうる)。
- 1,000 体・GPT-4o-mini。**本 repo の 39 万体・8B とは 2 桁と 1 段違う**。CitySim の設計がそのままスケールする保証はない。

## 批判・限界

- **社会網の検証をしていない**。Dunbar 層も会話グループサイズも三者閉包も照合していない。照合しているのは POI 人気(Spearman)・群集密度(ヒートマップ)・時間利用・幸福度分類。→ **「3 値でよい」の根拠にはなるが「3 値で正しく動く」の根拠にはならない**。
- **更新量が空欄**("incrementally adjust" 以上の記述がない)。再現不能。
- 幸福度分類では **GBDT(0.45)に負けている**(0.36)。著者も認める。
- POI 人気の ground truth が **Google Maps の評価**=来訪者数ではない。
- 8B ではない。本 repo の写し・書式縮退の問題は CitySim には出ていない可能性が高い。

## 関連

[[relations__schneider2025_llm-emergent-ties]] ・ [[relations__li2026_scoring-bias-8b]] ・ `../v2-c10-initial-relations-research.md` §2-1, §3-1 ・ メモリ `market-landscape-2026-09`(CitySim = 渋谷密度再現主張)
