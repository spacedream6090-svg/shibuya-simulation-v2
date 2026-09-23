# Amano & Yamaguchi 2026 — Distilling Aggregate Mobility Statistics into a Language Model Policy for Post-Event Crowd Simulation

- リンク: <https://arxiv.org/abs/2608.19778> / 本文 <https://arxiv.org/html/2608.19778> | 分野: 計算社会科学 #25 / 検証とV&V #22 / 人間移動科学 #3 | 重要度: **P1**
- **一次確認**: **実読(サブ・2026-09-17・arXiv HTML)・親未確認**。v1 2026-08-20・cs.MA。**ACM SIGSPATIAL 2026**(Riverside, CA・11/03-06)。著者所属は大阪大学 / RIKEN R-CCS。
- **なぜ引くか**: **「集計指標は方策を区別しない」**ことを、LLM 方策・規則シミュレータ・古典重力則の総当りで示した唯一の先行。R-37 の腕(基線 / EPR 単独 / H)の**合否指標の選び方**を決める。

## 主張(claim)

集計統計(格子ごとの人数)に合わせて較正すると、**行動の前提がまったく違う方策でも格子相関はほぼ同じ値に落ち着く**。方策を分けるのは**行き先の構成比**である。

## 機構(mechanism)

イベント後の群衆を模擬する言語モデル方策を、集計統計(セル人数)から蒸留する。比較は 8 方策(逐語): 「four LLM-based variants (**no grounding, naive SFT, IPF at inference, and GRPO**)」+「a **rule simulator tuned by CMA-ES**」+「an LLM prompting agent (**LLMob**)」+「a **classical gravity model**」(Wilson 1971)。

## 数値(節・図番号まで)

- **図 3 のキャプション(逐語)**: 「**Grid correlation is insensitive across calibrated policies, whereas destination-share error separates them.**」
- **§5(逐語)**: 「the grid correlation is similar across all behavioural priors, landing near **0.75**」——「for the rule, the uniform policy, and the LLM alike」。
- **§1(逐語)**: 較正後は「so this metric alone **leaves them indistinguishable**」。**§6**: 「grid-count correlation alone can **hide important behavioural differences** between policies.」
- **分けた指標**: 行き先クラス(station / mall / other)の構成比の絶対差の和。観測比 **0.744 / 0.064 / 0.192**。20:00〜22:10・**500 体 × 10 seed**。
- **効果**: 微調整方策は mall 比を **0.02 → 0.09**(観測 **0.06**)へ持ち上げ、構成比誤差を**約 25%** 削減(さらに推論時 IPF 補正に対して **15%**)。
- **負の結果**: 「naive SFT **amplifies the dominant class** and performs worse than the untuned baseline」。GRPO も微調整方策より構成比誤差が大きい。
- 数値表は **図 3(b) の画像のみ**で、方策ごとの構成比誤差の数値は本文に無い(**空欄**)。

## 効く箇所(seam)

- **R-37 §4-2(最重要)**: **v2 の在圏カーブ(D1′)や密度段階では、基線 / EPR 単独 / H の差は出ない可能性が高い。** H の合否に D1′ を使ってはいけない。差が出るのは「**どの店が選ばれたか**」の構成比=答申の **P-6(到達 POI 被覆率)・P-8(店あたり訪問者数の Zipf 傾き)**。
- **パターン台帳ゲート**: 「1 つのパターンは間違った理由でも合う」([[abm__grimm-railsback2012_pom-multiscope]] の equifinality)の、**LLM 方策での具体例**。
- **蒸留の警告**: naive SFT が多数クラスを増幅して**無調整より悪くなる**= GenWorld 型の蒸留を採らない判断の補強材料。

## 「結論でなく機構として」の入れ方

- **借りる**: 「較正した集計指標では方策を分けられない → **構成比で分ける**」という検証設計の形。
- **借りない**: 0.75 という値(イベント後の群衆・500 体・大阪の設定に固有)。IPF・GRPO などの手法(v2 は較正を holdout に触れさせない)。

## コスト/スケール含意

500 体 × 10 seed。規模は小さい。**v2 の 5,000 体 × 1 日の腕と同じ桁**なので、腕設計の参考になる。

## 批判・限界

1. **行き先クラスが 3 つだけ**(station / mall / other)。v2 の 2,337 POI とは粒度が違う。
2. 方策ごとの数値表が本文に無い(図のみ)。
3. イベント後の群衆という**特殊な場面**。日常の行き先選択に外挿できるかは未確認。
4. 2026-08 公刊。

## 関連

[[mobility__santos2026_unconstrained-poi]] ・ [[abm__grimm-railsback2012_pom-multiscope]] ・ [[causal__lipsitch2010_negative-controls]] ・ 答申 `../v2-destination-choice-llm-research.md` §4-2
