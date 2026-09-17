# Lipsitch, Tchetgen Tchetgen & Cohen 2010 — Negative Controls: A Tool for Detecting Confounding and Bias in Observational Studies

- リンク: https://doi.org/10.1097/EDE.0b013e3181d61eeb | 分野: 統計学・因果推論 #23 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-17・サブが PMC 全文 PMC3053408 を取得し、Experimental biology / Choice of negative controls to detect confounding in epidemiology / 図 2・3 の説明 / Discussion を逐語照合)。**親未確認**。*Epidemiology* 21(3):383–388(訂正 21(4):589 あり)。

## 主張(claim)

**正解(真の因果効果)が分からない観察研究でも、「効果が出ないはずの条件」を 1 つ走らせれば、偏りの存在を検出できる**。実験生物学の陰性対照を疫学に移植したもの。

逐語(≤125 字):
- 実験生物学の原型: "**to repeat the experiment under conditions in which it is expected to produce a null result**"(Experimental biology)
- 一般化: "**to reproduce a condition that cannot involve the hypothesized causal mechanism**"(同)

## 機構(mechanism)— 2 種類と 1 つの条件

| 種 | 定義(逐語) | 図 |
|---|---|---|
| **負の対照アウトカム** N | "a negative control outcome is connected to A through all possible confounding routes but **not causally**" | 図2: "N should ideally have the same incoming arrows as Y, except that A does not cause N" |
| **負の対照曝露** B | "a negative control exposure is connected to Y through all possible confounding routes but **not causally**" | 図3: "B should ideally have the same incoming arrows as A; to the extent this criterion is met, B is called U-comparable to A" |

- **条件 = U-comparability**: "we call the negative control outcome N 'U-comparable' to Y"。曝露側は "the common causes of A and Y are as nearly identical as possible to the common causes of B and Y"。
- **判定**: "an association A-N when analyzed according to the same procedure used to analyze A-Y would indicate bias" / 逆に "**a null finding of A-N implies that the A-Y association is not likely biased**"。
- **同じ解析手続きを使うこと**が肝(別の手続きで見たら意味がない)。

## 効く箇所(seam)

- **到達点 C(反実仮想)には正解が無い**。本論文は「正解が無いときに何を測るか」の唯一の一次的な答え。
- 我々への写像(親案・未リサーチ):
  - **負の対照介入** = 現実で在圏や行動分布を動かさないはずの改変(建物の**内部**レイアウトだけ変える・施設名だけ変える・エリア外の店を開閉する・提示順だけ入れ替える)。これで出力が動いたら、**その分は機構でなく実装の漏れ(プロンプト長・トークン順・乱数消費のずれ)**。
  - **既に持っている最小形** = **A/A(同構成・seed だけ違う)**。seed 間 JSD 0.000162 bits(在圏)/ 0.00007(行動 24 語)がその測定値。
  - **U-comparability の写像** = 「負の対照介入は、本物の介入と**同じ経路で系に入る**こと」(同じ affordance 表を通る・同じプロンプト枠を通る)。ここを外すと検出力が落ちる。
- **D-44 の 0 ラン規則(入力側 JSD が帰無参照内なら駆動しえない)は、負の対照の論理と同型**(片側でしか結論できない点まで同じ)。

## 「結論でなく機構として」の入れ方

- **借りない**: 疫学の作例(インフルエンザワクチンと非季節性死亡など)。
- **借りる**: (1) **2 種類の対照(アウトカム側 / 曝露側)の分類**。(2) **U-comparability という 1 つの条件**——対照は「因果の矢だけが無く、他の矢は同じ」であること。(3) **同じ解析手続きで見る**という規律。(4) **片側の解釈**(帰無なら偏りが無さそう / 非帰無なら偏りがある、ただし**どの偏りかは分からない**)。

## 数値(そのまま使う値)

**数値は無い**(方法論の論文)。効果量・閾値の提案は本文に無い。

## コスト/スケール含意

- **負の対照は 1 腕追加**=我々では 1 ラン(39 万体で 9.17 h、5,000 体で 0.5 h)。**A/A は既存の seed 2/3 で足りているので追加費用ゼロ**。
- 「同じ解析手続きで」なので、受入表・holdout 比較のコードをそのまま流用できる。

## 批判・限界(著者自身が明記)

- "**Negative control outcomes in practice will be only approximately U-comparable, at best.**"
- "finding an unexpected association between A and N does not prove unequivocally that the A-Y association is biased"
- "**A properly selected negative control is a sensitive, but blunt, tool to probe the credibility of a study.**" — 失敗しても "does not identify what form of bias is operating"
- "the magnitude of bias due to uncontrolled confounding cannot generally be inferred from the magnitude of a detected A-N" — **偏りの大きさは測れない**。
- 因果の仮定を間違えていると "the analysis involving negative controls may be misleading"。

## 関連

[[causal__shah2026_agent-replay]](介入代数・do_resample は「null intervention」= 負の対照の手番版)・[[validation__hut2026_simulated-rct]](A/A シミュレーションを較正の第1相に置く実例)・`../v2-statistics-causal-research.md` §1-3(b)
