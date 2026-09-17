# Hut & Masoero 2026 — Can AI Agents Simulate A/B Test Outcomes? A Validation Framework for Agentic Experimentation

- リンク: https://arxiv.org/abs/2608.02345 | 分野: 検証と V&V #22 / 計算社会科学 #25 / 統計学・因果推論 #23 | 重要度: **P0**(到達点 C「反実仮想の精度」の物差し)
- **一次確認**: **実読**(2026-09-17・サブが abs 頁と HTML 本文 v3 を取得し、§2.1・§2.2・§3・§4.2・§4.3・§5・付録 A を逐語照合)。**親未確認**。arXiv:2608.02345・v1 2026-08-03 / v2 2026-08-13 / **v3 2026-09-11**・CC BY 4.0・cs.CL。**査読会議名は頁に無く、ワークショップ採択の記載のみ**。著者 2 名。

## 主張(claim)

**LLM エージェントに A/B 試験の結果を予測させられるか**を、**実施済みの試験 67 件で逆行検証**した初めての枠組み。結論は否定寄り: **素の基盤モデルは向きを 0.70 で当てるが、それは「無内容の予測」が達する 0.75 を下回る**。効果の大きさは系統的に過大。ただし**事前期での較正**と**被験者内設計**で大きく改善する。

逐語(≤125 字):
- "**A Simulated Randomized Controlled Trial (S-RCT) replaces live traffic with computational surrogates**"(§2.1)
- "**sign overlap 0.70 falls below the 0.75 a no-conviction forecast attains**"(§3 Results)

## 機構(mechanism)

### (1) S-RCT の定式化(§2.1)
シミュレータに「ペルソナ・文脈・課題」を与え、模擬結果を出す。推定量は模擬平均の差(式 2)。

### (2) 誤差の 2 層分解(§2.1・式 4)— **本論文の中核**
- 第 1 層 = **エージェント近似誤差**: "The approximation error is the gap between the simulator's population-level prediction and the true ATE"
- 第 2 層 = **部分標本誤差**: "the finite-sample gap between the realized N_agt-agent estimate and the simulator-population ATE"
- "**These two layers are independently addressable: calibration targets the first; principled agent selection targets the second**"

### (3) 較正(§4.2)— 2 相
- Phase 1(較正): 事前期で、**両腕に対照の文脈を流す**。"both arms render the control context (**an A/A simulation with zero treatment effect by construction**)"
- Phase 2(予測): 本来の特徴と実際の割付で回す。
- Platt scaling で写像を学習。

### (4) 被験者内設計(§4.3)
"a within-subject design where every agent is exposed to both treatment and control" / "**each agent serves as its own control**"

## 効く箇所(seam)

- **到達点 C の物差しとして、いま世界にある最も近い先行**。3 点が直接効く:
  1. **「反実仮想の精度」の操作的定義** = **実施済みの介入を当てられるか**(逆行検証)。我々なら「渋谷で実際に起きた開業・閉業・工事・イベント」を当てる設計を、**次の封印データ取得の前に**作る必要がある。
  2. **誤差の 2 層分解**。**いま我々が測っている seed 間 JSD は第 2 層(部分標本誤差)であって、第 1 層(エージェント近似誤差)ではない**。計器盤 G-8 の「分散分解(seed 間 / 条件間)」はこの 2 層と対応するが、**第 1 層は現実データが無いと測れない**——ここが holdout を開ける本当の理由。
  3. **A/A シミュレーションを較正の第 1 相に置く**。我々は既に A/A(同構成・別 seed)を持っている(seed 間 JSD 0.000162)。これを「第 1 相」と位置づけ直せば、追加費用ゼロで枠に乗る。
- **「向きと桁に留める」作法に実測の裏づけが付いた**。向きですら無内容予測に負けうるので、**向きを主張するときも基準線(no-conviction forecast)との比較を併記する**必要がある。

## 「結論でなく機構として」の入れ方

- **借りない**: Platt scaling の実装・マーケティング CTR の作例・ペルソナ書式。
- **借りる**: (1) **S-RCT という呼び名と 2 層分解**を到達点 C の語彙にする。(2) **A/A を第 1 相に置く**手順。(3) **「向き」の評価に基準線を置く**(sign overlap を出すなら no-conviction の値も出す)。(4) **被験者内設計**——同じ体を両腕に通す(我々のテープ再生+介入代数で原理的に可能。→ [[causal__shah2026_agent-replay]])。

## 数値(出所つき)

- **ベンチ**: "a benchmark of **I=67** historical marketing A/B test treatment pairs run on a large e-commerce service"(§3)。指標は CTR。
- **紐づけ**: "**every agent is bound to a specific real customer who participated in the historical experiment**"(§2.2)
- **素の基盤モデル**: sign accuracy **0.70** / sign overlap **0.70**。基準線 = no-conviction forecast の **0.75**(= **負けている**)。効果量は系統的に過大。
- **較正の効果**: "On **16 experiments** from the benchmark using Platt scaling, calibration compresses the squared prediction error by **~77×**"(§4.2)。**67 件ではなく 16 件の部分集合であることに注意**。
- **被験者内設計**: "standard errors shrink by **~2.4×** on average"(§4.3)。

## コスト/スケール含意

- 逆行検証は**実施済みの介入が要る**。我々は渋谷の介入履歴を持っていない = **データ収集の新項目**。
- 被験者内設計(同一体を両腕に)は、我々のテープ再生と介入代数(`do_context`)があれば**1 体単位で安く**できる(体あたり 6.94 呼/日)。
- 較正は事前期のランが要る = **A/A を 1 本余計に回すだけ**。

## 批判・限界(著者が明記)

- "**a single-domain benchmark (marketing CTR)**"
- "the ground truth is **noisy**"(§3)——historical ATE 自体に測定誤差がある。
- "potential correlation in agent responses from a shared model that could understate variance" —— **同一モデルから出た応答は相関しており分散を過小評価しうる**。我々の 39 万体も同じ 1 モデルから出ている。
- "in a prospective setting, the triggering population is unknown and **no ground truth is available for calibration**" —— **前向きには較正できない**。
- "Assumption 1 is strong, and likely violated in practice"
- 抄録自身が、向きの一致は "not clear evidence of directional signal on this noisy set" と述べている。
- ワークショップ論文・v3 まで改訂・**査読の強度は不明**。

## 関連

[[causal__lipsitch2010_negative-controls]](A/A = 負の対照の最小形)・[[causal__shah2026_agent-replay]](被験者内設計の実装手段)・[[validation__larooij2025_generative-abm-validation]](主観のみの検証 15/35)・[[mas__li2026_agents-not-sufficient]]・`../v2-statistics-causal-research.md` §1-3(b)・PENDING 到達点 C
