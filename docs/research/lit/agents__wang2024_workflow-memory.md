# Wang, Mao, Fried & Neubig 2024 — Agent Workflow Memory (AWM)

- リンク: https://arxiv.org/abs/2409.07429 | 分野: 自然言語処理 #27 / ABM 方法論 #21 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが `arxiv.org/html/2409.07429v1` 本文 §2.2/§2.3/§3.2.2/付録 A.1・B を取得。`v2` の HTML は 404)。**親未確認**。投稿 2024-09-11。著者 Zora Zhiruo Wang, Jiayuan Mao, Daniel Fried, Graham Neubig。ICML 2025 掲載と後続論文が記載(**本書では未確認**)。

## 主張(claim)

過去の軌跡から**繰り返し使う手順(workflow)を誘導**して記憶に入れ、以後の生成に渡すと、長い行動列の課題が解ける。**オフラインでもオンラインでも同じ枠で成立する**。

## 機構(mechanism)

- **workflow の形**(§2.2): 「a workflow comprises two components: first, a textual description of the workflow」/「…second, a series of steps to finish the workflow」。各 step = 自然言語の環境状態 + 推論 + 「an action represented as an executable program over the environment」。
- **オフライン**(§2.3): 「AWM first takes in all training examples from a website by concatenating them into a single prompt」→ 得た workflow を推論時にまとめて記憶へ。入力は「data annotated by humans or synthesized by models」を前提にしており、**別の検査は無い**。
- **オンライン**(§2.3): 「Agents with AWMonline process test queries in a streaming fashion」。1 課題ごとに「induce, integrate, and utilize workflows」。**成功ゲートあり**:「If e^t is predicted as success, i.e., 1, we then transform it into workflow(s)」。判定は LM 評価器(Pan et al. 2024)で「supervision-free setting」(§1)。
- **頻度閾値は無い**。誘導プロンプトは「find the repetitive subset of actions across multiple tasks」と言うだけで、**「何回繰り返したら」は LM の判断に委ねられている**。形の制約は「Each workflow should have at least two steps.」のみ。
- **重複排除もプロンプト**: 「Do not generate similar or overlapping workflows.」。出力は二重改行で分割して個別保存。オンラインでは M^t + {w^t} → M^{t+1} と**単に追記**。
- 規則ベース版(付録 B): 「We group experiences by their action sequence and randomly select n (n=1 by default) experiences from each group.」

## 数値(出所つき)

- 抄録: Mind2Web で相対成功率 **+24.6%**、WebArena で **+51.1%**、WebArena では手数も減る。
- 抄録: オンライン版は訓練/評価の乖離が大きいほど強く、ベースライン比 **+8.9〜14.0 絶対点**。
- 評価規模: 「1000+ tasks, 200+ domains」(抄録)。

## 効く箇所(seam)

[行動契約書 §7](../../design/v2-action-contract.md) 段2 の**オンライン/オフラインの分岐**。D-71 のユーザー決定(オフライン)を評価するための唯一の「同一手法で両方やった」比較材料。

## 「結論でなく機構として」の入れ方

- **借りない**: 数値、workflow のテキスト表現、LM 評価器による自己採点。
- **借りる**: (1) **オフライン=訓練事例を一括で渡す / オンライン=1 件ずつ流す**という**同一手法の 2 モード**という整理。D-71 の「オフライン裁定バッチ」は AWM-offline の形。(2) **§3.2.2 の警告**——オンラインでは自己評価が誤ると「incorrect workflows that degrade model performance」。**ラン内で語彙を増やすと世界が壊れうる**ことの外部根拠。(3) **重複排除をプロンプトに任せている**=自動 dedup の先行が無いことの実例(D-71 答申 §1.6)。

## コスト/スケール含意

オフラインは訓練事例を 1 プロンプトに連結するので**文脈長が律速**。v2 の未定義台帳は語ごとに集約済み(N≥10 の語のみ)なので、連結しても短い。オンラインは 1 課題ごとに誘導呼が増える=**ランの呼数予算に直撃**。

## 批判・限界

- Web エージェント専用。**世界状態の保存則が無い領域**なので、誤獲得の代償が v2 より小さい。
- 「繰り返し」の判定が LM 任せで、再現性の保証が無い。
- **獲得の停止条件が無い**(記憶は増え続ける)。
- オフラインの入力は人手注釈または合成データを前提=v2 の「観測から」とは出所が違う。

## 関連

[[agents__wang2023_voyager]] ・ [[agents__wang2025_programmatic-skill-induction]] ・ [[agents__zhao2024_learnact]] ・ [D-71 答申](../v2-d71-vocab-growth-research.md) §1.1・§2-D
