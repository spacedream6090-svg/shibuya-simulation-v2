# Bougie & Watanabe 2025 — CitySim: Modeling Urban Behaviors and City Dynamics with Large-Scale LLM-Driven Agent Simulation

- リンク: <https://arxiv.org/abs/2506.21805>(v1・2025-06-26・PDF 13 頁) | 分野: 計算社会科学 #25 / 小売科学・商業立地論 #17 / 人間移動科学 #3 | 重要度: P1
- **一次確認**: **実読(サブ・2026-09-17・PDF 全 13 頁を pymupdf 抽出)・親未確認**
- 主張(claim): **渋谷の POI 人気を LLM エージェントの訪問数で予測した、本書の探索範囲では唯一の先行**。エージェントのペルソナに **hobbies** を持たせるが、その分布は**非公開の自社調査**由来で再現できない。そして **LLM エージェントは有名・ブランド POI を過大に選ぶ**。
- 機構(mechanism): ① 日次スケジュールを「recursive value-driven approach that balances mandatory activities, personal habits, and situational factors」で生成 ② POI への信念 `b_i ∈ R^K`(次元 = price / atmosphere / satisfaction / convenience)を訪問結果から **Kalman フィルタ**で更新する空間記憶。→ **選好を静的に配るのではなく、訪問経験で育てる**という別解。
- 効く箇所(seam): (a) 我々のパターン台帳候補 **L6「POI 人気の順位相関」**の先行・かつ**既知の汚染源**。(b) 「選好ベクトル(カテゴリ×重み)」の代替案 C(POI 属性 4 次元の信念)。(c) 「1,000 体・東京」という規模の対照(v2 は 39 万体)。
- 「結論でなく機構として」の入れ方: 「LLM は POI を選べる」ではなく「**LLM に POI 名を見せるとブランドへ偏る**」という**失敗様式**として入れる。→ 我々が POI 名を観測に出すなら、**POI 名を隠した対照ラン**が照合の前提条件になる。
- 数値(出所の節まで):
  - 規模(§実験設定の逐語):「All agents are powered by the GPT-4o-mini version of ChatGPT, except when specified differently, with the number of agents set to **1,000** located in **Tokyo metropolitan area**」。基盤は AgentSociety(Piao et al., 2025)。
  - ペルソナ(§Persona Module の逐語):「**Demographic Attributes**: Name, age, gender, occupation, income, **hobbies**, education, household composition, and life stage. These modulate the agent's activity space (e.g., children attend school; retirees prefer daytime leisure) and shape patterns in daily routines.」+ Spatial Anchors(home, work/school)+ Psych(Big Five を 3 点尺度に離散化)。
  - 出所(§実験設定の逐語):「All agent attributes in the persona module are initialized from **a proprietary survey-based dataset**, conducted in Japan. The attribute distributions closely match those observed in recent Japanese census statistics and lifestyle surveys (Statistics Bureau of Japan, 2021).」→ **趣味の分布は非公開**。
  - 引用している公的統計: 「Statistics Bureau of Japan. 2021. Survey on time use and leisure activities, 2021. `https://www.e-stat.go.jp/en/stat-search/files?page=1&toukei=00200533&tstat=000001158160`. Accessed July 2024.」= **社会生活基本調査**。ただし**照合(§4.1)に使っており、趣味を引いたとは書いていない**。
  - §4.1 マクロ生活時間: 2 か月分を生成し「high-level activity categories used in the survey (e.g., Work, Commute, Housework, Personal Care & Sleep)」へ写像、年齢群別に share of day を比較。**定量値は Figure 1 のみ・本文に数値なし**。
  - §4.4 **渋谷の POI 人気**(逐語):「we evaluate CitySim's as a predictive tool for real-world POI popularity in **Shibuya (Tokyo, Japan)**. **Ground-truth was estimated using ratings from Google Maps.** Simulated popularity was measured by counting agent visits to each POI over a simulated month.」指標は **Spearman rank correlation**。**値は Figure 4 のみ**。
  - §4.4 **失敗様式(逐語)**:「Notably, **CitySim agents exhibit a positive bias toward well-known or branded POIs, leading to an inflated estimate of their real-world popularity.**」
  - §4.5 well-being 5 クラス予測 Macro F1(Table 1・proprietary な 1,200 件の調査回答): **GBDT 0.45±0.04 / CitySim 0.36±0.02 / AgentSociety 0.28±0.02 / HumanoidAgent 0.22±0.03 / AGA 0.20±0.03 / MobileCity 0.21±0.02 / GeAn 0.19±0.03**。→ **LLM エージェントは勾配ブースティングに負けている**。
  - §4.2 人間らしさ: GPT-4o による対戦形式(Naturalness / Coherence / Plausibility)15 試行。**勝率の数値は Figure 2 のみ**。
  - §4.3 移動: ground truth は「a proprietary city-scale dataset」。**非公開**。
  - POI 情報源: 参考文献に `openstreetmap`(付録で引用)= **我々の W6 と同じ OSM**。
- コスト/スケール含意: 1,000 体 × 2 か月を GPT-4o-mini で回す規模。v2 の 39 万体・8B ローカルとは桁も体制も違う。**「実用」の基準としては使えない**(既存 lit `compute__agentsociety2025_parallel_framework` の枠組みで見るべき)。
- 批判・限界:
  ① **再現不能**。ペルソナも移動 ground truth も well-being も **proprietary**。公開されているのは手法だけ。
  ② **POI 人気の ground truth が Google Maps の「評価」**。評価は訪問数ではない(人気店ほど低評価が付く現象すらある)。**我々が L6 を採るなら別の ground truth が要る**。
  ③ **定量値が本文に無い**(Figure だけ)。生活時間の一致度も Spearman ρ も数字で引けない = **空欄**。
  ④ 1,000 体で「tens of thousands of agents」と抄録が言うのは別実験を指す可能性(本文と抄録に差がある)。
  ⑤ **2025-06 公刊**=LLM の学習データに入りうる。渋谷 POI 人気を照合行にするなら**混入の疑い=高**。
- 関連: [[mas__yang2024_oasis]] ・ [[compute__agentsociety2025_parallel_framework]] ・ [[timeuse__estat2021_leisure-participation]] ・ [[agents__park2023_generative-agents-replay]] ・ 答申 `v2-hobby-preference-research.md` §6-3・§8(L6)
