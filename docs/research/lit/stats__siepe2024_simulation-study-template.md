# Siepe, Bartoš, Morris, Boulesteix, Heck & Pawel 2024 — Simulation Studies for Methodological Research in Psychology: A Standardized Template for Planning, Preregistration, and Reporting

- リンク: https://doi.org/10.1037/met0000695(全文 https://pmc.ncbi.nlm.nih.gov/articles/PMC7616844/)| 分野: 統計学・因果推論 #23 / 検証と V&V #22 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-16・第200・サブが PMC 全文を実読 → 親が同ページを再取得し逐語一致)。*Psychological Methods* 2024-11-14 オンライン先行(著者原稿版・PMCID PMC7616844)。

## 主張(claim)

「**When planning a simulation study, researchers should choose a number of simulation repetitions that ensures a desired precision for estimating the chosen performance measures.**」反復回数は **Monte Carlo 標準誤差(MCSE)の目標から逆算**し、事前登録(ADEMP-PreReg)で宣言する。

## 機構(mechanism)— Table 3

- 一般統計量 G の平均: MCSE=√(S_G²/n_sim)・**n_sim = S_G² / MCSE\*²**
- 検出力・第 1 種誤り: n_sim = p̂(1−p̂)/MCSE\*²(最悪値 p=0.5)
- 未知量は (a) 慣習値を仮定 (b) 最悪値 (c) **小規模パイロットで推定**。
- 「**the number of repetitions must be chosen large enough such that the MCSE is sufficiently small compared to the relevant effect of interest** … as to our knowledge **there are no standards**」= 目標精度は「意味のある差」から研究者が決める。
- 作例: 0.50×(1−0.50)/0.005² = **10,000** 反復。

## 数値(文献調査・§Design)

反復回数は **1〜1,000,000**・**中央値 900**・最頻 1,000 次いで 500。**根拠を書いた研究は 8%・計算までしたのは 3%**。

## 効く箇所(seam)

- 8 seed の相対 MCSE = CV/√8 = **0.354·CV**。MCSE 1% には N=(CV/0.01)²(CV 10% で 100 本)。
- **「割合 p に p(1−p) を当てるのは誤り」**(親注): 我々は 1 seed が 39 万体から p を推定するので、使う分散は **seed 間の p の分散**(測って確かめる項目)。
- 事前登録 v1.2 に「目標 MCSE と根拠」の欄を足す。

## 「結論でなく機構として」の入れ方

反復回数を「文献の中央値 900」に合わせるのではなく、**n=(CV/r)² を指標ごとに解いて表にし、r を現実整合アンカーの許容幅から決める**(答申 §5 の 3 手の 2 つ目)。

- 関連: [[stats__lee2015_abm-output-analysis]] [[stats__ritter2011_number-of-runs]] [[validation__operational-validity-overview]]
