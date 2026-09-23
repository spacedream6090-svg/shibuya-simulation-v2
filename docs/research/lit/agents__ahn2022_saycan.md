# Ahn et al. 2022 — Do As I Can, Not As I Say: Grounding Language in Robotic Affordances (SayCan)

- リンク: https://arxiv.org/abs/2204.01691 | 分野: 自然言語処理 #27 / ABM 方法論 #21 / 知覚心理学 #5 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが abs + `ar5iv.labs.arxiv.org/html/2204.01691` 本文 §3・Algorithm 1・§4・§5 を取得。**付録 D は取得が切れている**)。**親未確認**。v1 2022-04-04 / v2 2022-08-16。著者 45 名(Michael Ahn ほか, Google/Everyday Robots)。

## 主張(claim)

LLM は「何をすべきか」を知っているが「いまここで何ができるか」を知らない。**技能ごとの価値関数(= affordance)を掛け合わせて、実行可能な行動だけを選ばせる**。

## 機構(mechanism)— 「動詞 × オブジェクト」で行動空間が決まる

- **affordance の定義**(§3): 「p(cπ|s,ℓπ) means 'if I ask the robot to do ℓπ, will it do it?'」/「p(cπ|s,ℓπ) is the value function for the skill if we take the reward to be 1 for successful completion and 0 otherwise.」/「cπ is a Bernoulli random variable.」
- **選択則**(§3・Algorithm 1。**式番号は無い**): 「p(ci|i,s,ℓπ) ∝ p(cπ|s,ℓπ)p(ℓπ|i)」/「π = argmax_{π∈Π} p(cπ|s,ℓπ) p(ℓπ|i)」。Algorithm 1 行 8「p_π^combined = p_π^affordance p_π^LLM」。
- **LLM は採点器**(§3): 「the decoding of the instruction obtained in this way always consists of skills that are available to the robot」/「score a candidate completion selected from a set of options」。§1「constraining the completions to the skill descriptions makes the LLM aware of the robot's capabilities」。**自由生成させない**。
- **行動空間の作り方**(§4・§5): 「we propose **551 skills that span seven skill families and 17 objects**」/「we test across **101 instructions from 7 instruction families**」/「We use 15 objects commonly found in an office kitchen and 5 known locations」。

## 数値(出所つき)

- **551 技能 = 7 技能族 × 17 オブジェクト**(§4)。ただし「実際に使うのは部分集合」と §4 にあり、内訳は付録 D(未取得)。
- **101 指示 / 7 指示族**(§5)。オブジェクト 15・場所 5(§5 設定)。

## 効く箇所(seam)

[行動契約書 §2](../../design/v2-action-contract.md)(横断 12 + 役割 12 = 24 語)と、決定台帳 2026-09-17 の原則「**行動はオブジェクトの affordance 由来**」。

## 「結論でなく機構として」の入れ方

- **借りない**: 価値関数の学習、ロボット実装、掛け算による選択(v2 の前提条件はエンジンの決定論検査であって確率ではない)。
- **借りる**:
  1. **「動詞は 7 語で足りる。語彙の規模を決めるのはオブジェクトの数」**という構造。v2 の 24 語は SayCan の「7 族」に相当する層で、**足りないのは語ではなくオブジェクト側の affordance 宣言**という読みが立つ。→ 「食事」を**動詞として足す**のか、**飲食店オブジェクトの affordance として足す**のかは、この論文が最初に分けた線。
  2. **affordance = 「頼んだらやれるか」の指標**という定義。v2 の「前提条件(エンジン検査)」は、この Bernoulli を**決定論に退化させたもの**と位置づけられる。
  3. **LLM を固定集合の採点器として使う**構え=AB7 の vocab 腕と同型。**SayCan は自由生成を採っていない**——open 腕を本番に使わない判断の外部先行。

## コスト/スケール含意

551 技能を毎回採点するので、**候補数 × LLM 採点**が費用。v2 で「(対象クラス, affordance)の直積」を全部見せるとプロンプトが破裂する(世界カタログ 57 クラス × 数十 affordance)。**見せるのは「いまここで前提を満たす行」だけ**という射影が要る=知覚契約の仕事。

## 批判・限界

- 単一ロボット・単一環境(オフィスキッチン)。**社会シミュではない**。
- 551 のうち何を実際に使ったかが本文に無い(付録 D)。
- affordance は**学習した価値関数**なので、v2 の「規則で書いた前提条件」とは信頼性の性質が違う(v2 の方が硬いが、硬すぎて学習しない)。
- 「動詞族 7」は**設計者が決めた**もので、この論文も動詞側の指紋を消してはいない。

## 関連

[[agents__yu2024_affordable-generative-agents]] ・ [[agents__wang2023_voyager]] ・ [D-71 答申](../v2-d71-vocab-growth-research.md) §1.3・§2-E ・ [語彙政策 v0](../../design/v2-synonym-policy-v0.md)
