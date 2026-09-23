# de Montjoye et al. 2013 — Unique in the Crowd: The privacy bounds of human mobility

- リンク: https://pmc.ncbi.nlm.nih.gov/articles/PMC3607247/ | 分野: 研究倫理・情報法 #31 / 人間移動科学 #3 | 重要度: **P1**
- **一次確認**: **サブ実読**(2026-09-17・PMC 本文を取得して抄録・Results・Methods から逐語採取)。**親未確認**。
  - 書誌: *Scientific Reports* **3**:1376(2013)、**doi:10.1038/srep01376**。著者 de Montjoye, Hidalgo, Verleysen, Blondel。
  - **nature.com の原典ページは認証にリダイレクトされて読めなかった**(303 → idp.nature.com)。本メモは **PMC 版**による。**図は未読・式の再計算は未了**。

## 主張(claim)

**移動の軌跡は極めて一意である**。時間解像度 1 時間・アンテナ単位という粗いデータでも、**4 つの時空間点があれば 95% の個人が一意に定まる**。そして**解像度を粗くしても特定性は 1/10 乗でしか落ちない**——つまり「粒度を落として匿名にする」は効かない。

## 逐語(≤125 字)

- 抄録: "**four spatio-temporal points are enough to uniquely identify 95% of the individuals**"
- 抄録: "**fifteen months of human mobility data for one and a half million individuals**"
- 抄録: "a spatial resolution equal to that given by the carrier's antennas"
- 抄録: "**the uniqueness of mobility traces decays approximately as the 1/10 power of their resolution**"
- 抄録: "**Hence, even coarse datasets provide little anonymity.**"
- 序: "**A simply anonymized dataset does not contain name, home address, phone number or other obvious identifier.**"
- 序: "if individual's patterns are unique enough, **outside information can be used to link the data back to an individual**"
- 結果: "mobility datasets are likely to be **re-identifiable using information only on a few outside locations**"
- Results: "**Our unicity test estimates the number of points p needed to uniquely identify the mobility trace of an individual.**"
- Results: "A trace is unique if |S(Ip)| = 1, containing only one trace."

## 機構(mechanism)— unicity ε の測り方

1. 各利用者の交信記録から **p 個の時空間点を無作為に選ぶ**(集合 Ip)。
2. データセット D の中で、その p 点すべてに合致する軌跡の部分集合 S(Ip) を取る。
3. |S(Ip)| = 1 なら一意。**ε_p = 2,500 本の無作為軌跡のうち一意だった割合**。

解像度を粗くしたときの形: **ε = α − (νh)^β**(h = 時間の粗さ、ν = アンテナの束ね数)、**指数は p に線形に落ちる: β = 0.157 − 0.007p**。

## 数値(出所つき)

| 量 | 値 |
|---|---|
| 母集団 | **150 万人**・**15 か月**(2006-04〜2007-06)・西側のある国の 1 事業者 |
| 空間解像度 | アンテナ **≈6,500 基**(1 基あたり平均 ≈2,000 人・**0.15〜15 km²**) |
| 時間解像度 | **1 時間** |
| 交信頻度 | 1 人あたり **≈114 回/月** |
| p=4 | **ε ≈ 95%** |
| p=2 | **ε > 0.5**(半数超) |
| 粗化の効き | p=4 で解像度を半分にしても特定性は **9.3%** しか落ちない(p=10 なら **6.2%**) |
| 帯 | p=4 なら **h=5 時間・ν=5 アンテナでも ε > 0.5** |
| 上限 | 試した全軌跡で **高々 11 点**あれば一意 |

著者は「無作為点を使う本手法は ε を**過小評価**している」と注記(狙った攻撃者は自宅・職場や特異な行動を使うのでもっと少ない点で済む)。

## 効く箇所(seam)

- **個体カルテの形(時刻 × 場所の点列)は、実データであれば 4 点で 95% が一意になる形そのもの**。我々の体は合成(統計から作った架空個体)なので**この脅威モデルは直接は当たらない**——しかし、**「この粒度は実データなら公開できない粒度だ」という事実は公開時の説明責任として先に書く**べき。
- **「粒度を落として安全にする」は効かない道**(1/10 乗則)。したがって公開は**粒度でなく体数を絞る**方向に倒すべき(答申 §2 O18)。
- 場所カルテ側は逆に、**集計してしまえばこの議論の外**に出られる(個人の軌跡ではなくなる)。

## 「結論でなく機構として」の入れ方

- **借りない**: 攻撃手法そのもの・実データへの適用。
- **借りる**: (1) **粗化の効きが 1/10 乗であるという形**——「粒度を落とせば安全」という直観の否定。(2) **unicity という言い方**(何点で一意になるか)を、公開する個体カルテの粒度を議論する語彙として使う。(3) **「単に匿名化されたデータセット」の定義**——識別子を消しただけでは足りない。

## コスト/スケール含意

計算は軽い(2,500 本の無作為抽出で足りる)。**v2 の個体カルテに対して同じ unicity テストを自分で回すことができる**——「我々のカルテは何点で一意になるか」を測れば、公開の線を数値で引ける。**これは追加ラン 0 本でできる**(既存テープから)。

## 批判・限界

- **実データの話であり、合成個体の話ではない**。v2 の体は実個人レコードから学習した生成物ではないので、再識別の脅威モデルは同じでない。**この区別を消して引用してはいけない**。
- 2006〜2007 年の通話・SMS 記録が母集団。**スマートフォン以降のデータではない**。
- 国名・事業者名は伏せられている。**再現性の意味では弱い**。
- 図と式の導出は未読(**空欄**)。β = 0.157 − 0.007p は本文の記述による。

## 関連

[[agents__park2023_generative-agents-replay]](公開される個体記録の形)・`../v2-micro-observation-research.md` §1-6 ・ 残務 R-15(公開・論文化の制度側。本メモと重複しない)
