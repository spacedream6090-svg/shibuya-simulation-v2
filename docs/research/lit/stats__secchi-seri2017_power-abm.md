# Secchi & Seri 2017 — Controlling for false negatives in agent-based models: a review of power analysis in organizational research

- リンク: https://doi.org/10.1007/s10588-016-9218-0(CMOT 23(1):94–121・Open Access **CC BY 4.0**・オンライン 2016-05-03)| 分野: 統計学・因果推論 #23 / ABM 方法論 #21 | 重要度: P1
- **一次確認**: **実読**(2026-09-16・第200・サブ全文実読 → 親が Springer の PDF を stdout 経由で pymupdf 抽出し、0.95/0.01・0.415・CC BY・"underpowered" を逐語確認)。**経験式 (2) の係数はテキスト層に無く(図版)親未確認**=サブ逐語。

## 主張(claim)

「**We suggest the reference for every ABM should be to reach power of 0.95 and higher at a 0.01 significance level.**」管理・組織研究の ABM は「most studies are underpowered, with some being overpowered」。

## 機構(mechanism)

- 理論式 (1): ANOVA(J 群・効果量 ES=Cohen の f)の非心 χ² から n\*。
- 経験式 (2)(α=0.01・β=0.05 に限定・**「formula (2) is empirical」**): **n(J,ES) ≃ 14.091·J^−0.640·ES^−1.986**(サブ逐語・親未確認)。N=n·J。
- Table 2: ES=0.1・α=0.01 の平均検出力 **0.415**(SD 0.395)=「well below any known standard」。
- **過剰検出力の警告**: 「Excessively large samples … oversensitivity to trivial or irrelevant findings」= 多すぎるのも害。

## 効く箇所(seam)

- J=2: 14.091·2^−0.640=9.04 → **n=8/群なら f≈(9.04/8)^(1/1.986)≈1.06**(Cohen の large 0.4 の 2.6 倍)。f=0.4 → 56/群=112 本=42.8 日。
- Ritter の d=1.65 と整合(答申 §2 (D)(E))。
- 「多すぎるのも害」は、D-44 で全 122 expedient を高検出力で回す発想への反証にもなる。

## 「結論でなく機構として」の入れ方

**効果量と α・power を事前登録に宣言**し、n はそこから導く。8 は「f≈1 以上の差を見る実験」として登録するなら文献準拠。

- 関連: [[stats__ritter2011_number-of-runs]] [[stats__lee2015_abm-output-analysis]]
