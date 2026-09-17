# Zhao, Kaulakis, Morgan, Hiam & Ritter 2012 — Modeling a Cognitively Limited Network in an Agent-Based Simulation

- リンク: https://escholarship.org/uc/item/85t2040s | 分野: 社会ネットワーク科学 #14 / 認知科学(記憶・習慣)#12 / ABM方法論 #21 | 重要度: **P1**
- **一次確認**: **実読**(2026-09-17・リサーチサブが WebFetch で PDF 取得 → pymupdf で本文抽出。**親未確認**)。*Proceedings of the 34th Annual Meeting of the Cognitive Science Society (CogSci 2012)*, pp.2603–2608。Penn State College of IST。査読は CogSci の短報。

## 主張(claim)

**社会的紐帯を ACT-R の宣言的記憶チャンクとして持たせ、その基底活性(base-level activation)と検索閾値だけで、Dunbar 数に似た上限が創発する。** ナビゲーション戦略と地図の複雑さは**網の形成速度**を変えるが、**平衡時に維持できる関係数は変えない**。

## 機構(mechanism)

- 40 体を部屋つきの格子世界に置き、遭遇するたびに相手のチャンクを再学習(リハーサル)させる。**Δ の重みも半減期も置かない**——1 遭遇 = 1 リハーサル。
- 逐語: "Examining different **memory activation thresholds for links between agents** enables us to model not only the effects of memory retention on network formation but also provides us a means of representing **differences in the modeled social ties' quality**, as Dunbar defines this term (Dunbar, 1998, pp. 76-77)."
- 逐語: "In other words, **higher quality relationships are associated with greater cognitive investment and higher memory strength**."
- 逐語: "According to the ACT-R theory, the activation threshold represents a memory limitation, meaning that **memory chunks with an activation value lower than the threshold cannot be retrieved**. ... **multiple exposures are required to remember another agent**."
- 正規化の提案(逐語): "Activations are not portable or easily interpretable in social terms. ... This normalization recasts activations as statements about the **'probability of recall' within a particular timeframe**." (Anderson et al. 2004 の Probability of Recall 式から導出。式 1・式 2 は本文中で**画像**になっておりテキスト抽出できなかった)

## 数値(出所つき)

- 体数 **40**。4 ラン × 18 標本時点 → **2,880 の自我中心記憶網**、**72 の統合記憶網**。
- 閾値なしの網: **1,336 リンクで平衡**(理論上限 40×39 = 1,560)。逐語 "flattens when it reaches 1,336 ties"。
- 閾値 0.0 の網: **800 リンクで平衡** = **1 体あたり平均 20 本**。逐語 "the final size of our thresholded networks **remains at 800 links**"。
- 逐語(結論): "our results also imply, at least for our world, that **navigation strategies and environmental complexity do not significantly influence the number of friends that a person can maintain in memory (Dunbar's number)**, as the average number of relations were same for both networks. They do, however, suggest the **ecological factors significantly contribute to the degree of localization**"
- 逐語(残課題): "We suspect that one possible way to adjust the final size of the network is by changing the cognitive parameters in ACT-R, for instance **adjusting memory decay speed or base level learning activation**."
- 実装の規模: 逐語 "This reduces the cost of a single ACT-R thread from 50 Mb to less than 20MB, which allows us to run **1,000 agents on one machine**."
- 時間スケールの注記(逐語): 部屋間移動間隔を 16 秒に設定した理由 = "**over 80 percent of the decay happens in the first 16 seconds** according to the ACT-R decay equation"

## 効く箇所(seam)

**C10 の R1(関係の表現)・R9(関係の更新)・着手条件の指紋②**。本 repo はすでに認知設計書 §4 で ACT-R 基底活性 `A(m)=ln Σ(Δt_j+1)^(−d)`・**d=0.5** を記憶側に決定している。**同じ式を「相互作用エピソード」に当てれば、辺の強さが 1 個の新しい数(検索閾値 τ)だけで定義できる**。

## 「結論でなく機構として」の入れ方

- 借りるのは「Dunbar 数が出た」ではなく **「辺 = 記憶チャンク / 辺の強さ = 基底活性 / 辺の有無 = 検索閾値」という 3 行の定義**。
- **生の活性値を `rel_strength: uint8` に入れてはいけない**(値域が不定)。著者の指摘どおり **想起確率に正規化してから量子化**する。
- 「地図と経路は上限数を変えない」は、**C10 のウォームアップで「誰と誰を組ませるか」を C9 の幾何に任せてよい**ことの部分的な根拠(ただし 40 体・机上格子での結果)。

## コスト/スケール含意

- 厳密な ACT-R は**全エピソードの時刻**を保持する。40 万体 × k=15 × エピソード数では不可能 → 最近 k 本を厳密・残りを (n, 経過時間) で近似する標準的な最適化を使う。**近似 = expedient タグ + 感度試験が必須**。
- 著者らの ACT-R は 1 体 20 MB。**本 repo は ACT-R を動かさない**(式だけ借りる)ので、この費用は発生しない。1 辺 11〜12 B で済む。

## 批判・限界

- **40 体・格子世界・CogSci 短報**。Dunbar 数の「再現」は **20 本/体**であって 150 ではない。著者も "an effect **similar to** that of Dunbar's number" としか書かない。
- **τ が結果を決めている**(閾値なし 1,336 vs 閾値 0.0 で 800)。τ は最大の感度対象。
- 時間スケールが非現実的(移動間隔 16 秒)。著者自身が "this interval is still not long enough to be realistic" と認める。
- 「関係の質」は活性値で表すが、**好悪(符号)はまったく扱っていない**。喧嘩相手も活性は高い。

## 関連

[[relations__gilbert2009_tie-strength-prediction]] ・ [[relations__dunbar2020_structure-function]] ・ `../../design/v2-cognition-design.md` §4 ・ `../v2-c10-initial-relations-research.md` §1-6
