# Wang ほか 2026 — LLM Agents as Social Scientists(S-Researcher / YuLan-OneSim)

- リンク: https://arxiv.org/abs/2604.01520 | 分野: 計算社会科学 #25 / ABM方法論 #21 | 重要度: P0
- **一次確認**: **実読(サブ・2026-09-17・arXiv HTML v1 の Results と Discussion)・親未確認**
- 主張(claim): **「LLM エージェントの応答のばらつきは人間の 20〜300 倍小さい」**。中心傾向と主効果は再現できるが、**異質性・意図感受性・分布の裾は再現できない**。
- 機構(mechanism): 同一のプロンプト・同一の意思決定枠を与えたエージェント集団は、観測可能な量(リーダーの拠出額)に過剰に反応し、解釈が要る量(意図・決定機構)にほとんど反応しない。人間は逆に意図への感受性が高い。**見せた量に寄る**ので、分散は「何を見せたか」で決まる。
- 効く箇所(seam): D-68 の問い「エージェントが全員同じに見える」に対する**外部からの定量的な裏書き**。検証設計で**裾の指標を単独ゲートにしない**という判断の根拠。第2陣の記憶・習慣で「何を観測ブロックに書くか」が分散を決めるという設計原則。
- 「結論でなく機構として」の入れ方: **20〜300 倍を目標値にしない**(算出根拠が本文に無い)。使うのは「**桁で足りていない**」という方向と「**中心は合うが裾は合わない**」という切り分け、そして「見せた量に過剰反応する」という機構。
- 数値(節・図番号まで):
  - **Discussion「Capabilities and boundaries of LLM simulation」の逐語**: 「LLM agents exhibit substantially lower behavioral heterogeneity than humans: **their response variability is 20–300 times smaller**, and they produce more extreme distributional patterns.」
  - 続く逐語: 「research involving **behavioral heterogeneity, intention sensitivity, or distributional tails should incorporate human participants**.」
  - 将来課題の逐語: 「developing methods to **calibrate agent behavioral heterogeneity against known human population parameters**」
  - 対応する実験(公共財ゲーム・abductive): 2×3 被験者間(自発/強制 × 低 2 / 中 5 / 高 8 トークン)、**条件あたり 100 エージェント × 3 反復**、並行して**人間 N=120・3 ラウンド**。4 人ゲーム・元本 10 トークン・倍率 1.6×
  - 効果量(Fig.5g): リーダー拠出額 β_agent = **0.794** / β_human = **0.491**。決定機構 β_agent = **0.104** / β_human = **0.251**。マクロ整合 Pearson **r = 0.915**(6 条件)
  - 文化伝播(inductive): 100 ラウンドで平均ペア類似度 0.20→0.24(**+21.0%**)、文化多様性 **1.0→0.65**(≈65 の「島」)、sim ≥ 0.6 の近傍対が **12.0%→50.0%**、支配的価値のシェアが一様基準 20%→**32〜37%**
  - 規模: 「a distributed architecture supporting **up to 100,000 concurrent agents**」
  - 専門家評価: 帰納 3.89/5・アブダクション 3.82/5・演繹 3.47/5(1〜5 尺度・パラダイムあたり査読者 3 名)
- コスト/スケール含意: 10 万体同時の主張は**アーキテクチャの主張**であって実測ではない(実験は条件あたり 100 体)。D-70 の比較表には入れられない。
- 批判・限界: ①**20–300 倍の算出根拠が本文に無い**。裏づけの SD 表も補足も示されず、対応するのは箱ひげ図 Fig.5d/f のみ②幅が一桁以上あるので目標値には使えない③人間側 N=120 は小さい(著者も限界として記載)④検証は認知・推論寄りの行動に限られ、感情・文化的に埋め込まれた行動は未検証(著者の記載)⑤プラットフォーム論文なので、分散比は主結果ではなく副産物。
- 関連: [[nlp__springer2026_annotation-anchoring]]・[[mas__li2026_agents-not-sufficient]]・[[validation__larooij2025_generative-abm-validation]]・既存答申 v2-d68-behavioral-diversity-research §8-6(この数値を探していた)
