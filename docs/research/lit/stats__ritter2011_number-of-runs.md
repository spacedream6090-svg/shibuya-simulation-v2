# Ritter, Schoelles, Quigley & Klein 2011 — Determining the number of simulation runs: Treating simulations as theories by not sampling their behavior

- リンク: https://doi.org/10.1007/978-0-85729-883-6_5(著者版 PDF https://acs.ist.psu.edu/papers/ritterSQKip.pdf・"Draft of 24 December 2010")| 分野: 統計学・因果推論 #23 / 認知科学 | 重要度: P1
- **一次確認**: **実読(著者版)**(2026-09-16・第200・サブが著者版を実読 → 親が同 PDF を pymupdf で本文抽出し逐語一致)。Springer 版(*Human-in-the-Loop Simulations* pp.97–116)は有料=未確認。

## 主張(claim)

「**because the simulation is a theory, not data, it should not so much be sampled but run enough times to provide stable predictions of performance and of the variance of performance.**」費用が高いときは power .90、安いときは .99 で必要本数を括る。

## 数値

- SEM=SD/√N。作例: SD 3.6・95% で ±0.5 → SEM 0.255 → **199 runs**。
- 「Although we used 100 runs … **we recommend 150 runs** as a reasonable number that provided very stable predictions for medium to large effects.」
- 検出力表(δ=ES·√(N/2)・t 検定 α=.05 両側): power .90(δ=3.30): ES 0.1→**2,178**・0.2→**545**・0.5→**88**・0.8→**34**。power .99(δ=4.20): 0.1→3,528・0.2→882・0.5→142・0.8→56。

## 効く箇所(seam)

- **8 seed の床**: √(8/2)=2 → power .90 で **ES=1.65**、.99 で 2.10。**seed 間 SD の 1.65 倍より小さい条件差は 8 seed では検出できない**。
- 費用換算(9.17 h/seed): ES 0.8 → 34 本=13.0 日 / 0.5 → 88 本=33.6 日 / 150 本=**57.3 日**。
- **D-44** の「2 seed の感度試験」は f≈1 以上しか検出しない=「結果を駆動していない」の証明にならず「特大の駆動が無い」の証明。

## 「結論でなく機構として」の入れ方

「150 本」を借りるのではなく、**検出可能効果量の床を台帳に宣言**する(ES=δ/√(N/2))。

- 関連: [[stats__secchi-seri2017_power-abm]] [[stats__siepe2024_simulation-study-template]]
