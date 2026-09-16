# Yu et al. 2024 — Affordable Generative Agents (AGA)

- リンク: https://arxiv.org/abs/2402.02053 | 分野: 計算社会科学 #25 / 認知科学(記憶・習慣)#12 / 自然言語処理 #27 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが abs + `arxiv.org/html/2402.02053v2` 本文 §3.1/§5.1〜5.3/Fig.3/Fig.7/Table 1/2/4/5・付録 A/F を取得)。**親未確認**。v1 2024-02-03 / v2 2024-08-28。著者 Yangbin Yu, Qin Zhang, Junyou Li, Qiang Fu, Deheng Ye。

## 主張(claim)

生成エージェントの長時間運用は高い。**繰り返しの LLM 推論を学習済みの方策に置き換える**(エージェント↔環境)+ 社会関係のモデル化と対話情報の圧縮(エージェント↔エージェント)で安くできる。副産物として——**固定環境では、エージェントが生み出す行動は有限**。

## 機構(mechanism)

### 1. Lifestyle Policy(行動の再利用)— §3.1

- 2 段: Plan Decomposition(未知の状況で LLM)/ Policy Reuse(既知なら検索)。
- 「The functionality of Lifestyle Policy is to minimize costs by reusing the similar inference processes of an LLM.」
- **同一判定の閾値**: 「When the cosine similarity exceeds a set threshold, we consider it a match for the same plan.」/「**In our implementation, we set the threshold at 0.97.**」(埋め込みは text-embedding-ada-002)

### 2. 行動語彙の飽和 — §5.3 / Fig.7

- 「**An intriguing observation is that after numerous trials, the agents cease to generate new activities.**」
- 「This implies that agents can only generate believable behaviors within a certain range.」
- 「When executed sufficiently, the Lifestyle Policy could encompass all activities within this range」
- 抄録: 「agents can only generate finite behaviors in fixed environments」
- 乱数(温度)の効果は「the variability in text descriptions rather than **the diversity of behaviors**」——**表層の言い換えが増えるだけで行動は増えない**。
- Fig.7 caption: 「Cumulative number of activity types over run iterations in Generative Agents.」(3 体分の累積曲線。**飽和点の数値は図にしかなく本文に無い**=空欄)

### 3. 新しい行動を出す方法 — §5.3・付録 F

- 新オブジェクトでも新エージェントでもなく、**注意の摂動**:「mind wandering」=「In each interaction, we influence the agent's decision-making by randomly sampling events from the agent's memory」。
- 実例: 「The Mind Wandering injects a randomly retrieved event: "toilet is idle".」→ パーティ前にトイレ掃除を足す。
- 「Compared to the original implementation, the LLM agents exhibit a broader range of activities.」費用は大きく変わらない(3 人・2 ゲーム日で 1.478M±0.166M tok)。

## 数値(出所つき)

- Fig.3(3 人・GPT-3.5 の ablation): Lifestyle Policy 単体 **40.2%** / Social Memory 単体 **58.6%** / 全部入り **31.1%**(原実装比のトークン)。
- Table 1: 3 人 **4.548M → 1.417M(31.1%)** / 25 人 **25.41M → 10.86M(42.7%)**。
- Table 4(VirtualHome): **34,327 → 1,189 tok**、「AGA costs only 3.4% of the baseline」。成功率はほぼ不変(S_LLM 87.0% vs 85.0%)。
- Table 2: 入力トークンが支配的。

## 効く箇所(seam)

- **D-71 / AB7**: 「入口を自由にしたのに行動が 2 語に集中した」の解釈。**8B の癖だけでなく、固定環境での飽和が効いている可能性**。→ 語彙を増やす前に**環境側の affordance を増やす**べきという読み。
- **AB7-b(ヒント腕)・C9(位置と注意)**: mind wandering は「オブジェクトを注意に上げると行動が生まれる」の実例。**ヒント腕は語のヒントだが、AGA は状況のヒント**——別の腕になりうる。
- **費用**: 方策再利用は v2 の「W17 日課テープ」と同じ位置。ただし v2 は**多様性が目的**なので、再利用は多様性を下げる向きに働く(トレードオフの明示が要る)。

## 「結論でなく機構として」の入れ方

- **借りない**: 0.97 という数値、Lifestyle Policy の実装、コスト削減率。
- **借りる**: (1) **「固定環境 → 行動は飽和する」**を**測る形**(累積の新規行動種類数 vs 反復)。v2 の C8 感度台帳に **「累積の未定義行動種類数」曲線**として置ける——飽和していれば「語彙を増やしても伸びない」の証拠になる。(2) **温度は表層を変えるが行動を増やさない**=多様性を温度で買おうとしない根拠。(3) **注意の摂動で新行動が出る**=語彙追加の代替手段。(4) **「in our implementation」と閾値を明記する作法**(指紋の宣言)。

## コスト/スケール含意

25 人で 42.7% と、**規模が大きいほど削減率は悪化**(共有できる計画が減る)。v2 の 5,000 体規模ではさらに悪化すると読むのが自然=**方策再利用を費用対策として当てにしない**。

## 批判・限界

- 飽和の数値が図にしか無い(**何種類で頭打ちかが本文に無い**)。
- Generative Agents(GPT-3.5・25 体・2 日)という小さい舞台での観察。
- 「believable behaviors within a certain range」の range が何で決まるか(モデルか環境か)を**分離していない**——v2 が知りたいのはまさにそこ。
- cosine 0.97 は**計画の同一判定**であって、語彙の重複排除ではない。流用するなら別の検証が要る。

## 関連

[[agents__ahn2022_saycan]] ・ [[agents__zhao2024_learnact]] ・ [[memory__lu2026_procedural-graphs]] ・ [D-71 答申](../v2-d71-vocab-growth-research.md) §1.3・§1.6 ・ [AB7 親報告](../../bench/c8/ablation/ab7_s1_parent_report.md)
