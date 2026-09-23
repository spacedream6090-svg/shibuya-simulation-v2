# Hoad, Robinson & Davies 2007 / Law 2020 — 反復回数の信頼区間(相対精度)法と Law の教科書の位置

- リンク: Hoad et al. "Automating DES Output Analysis: How Many Replications to Run", WSC 2007 https://www.informs-sim.org/wsc07papers/060.pdf / Law "Statistical Analysis of Simulation Output Data: The Practical State of the Art", WSC 2020 https://informs-sim.org/wsc20papers/134.pdf | 分野: 統計学・因果推論 #23 / OR・離散事象シミュレーション | 重要度: P1
- **一次確認**: **実読**(2026-09-16・第200・両 PDF を親が pymupdf で本文抽出し逐語一致)。**Law の教科書 *Simulation Modeling and Analysis*(5th ed. 2015)の逐次手続きの原文・式番号は未確認**(オンラインで読めず)。ここでは Law 本人の tutorial と、教科書を引く査読論文(Hoad)で代替=**二次**。

## 主張(claim)

- Hoad: 「Law and McComas (1990) recommend running at least **3 to 5 replications**. … However, **it makes no allowance for the characteristics of a model's output**」。相対精度 d_n=100·t_{n−1,α/2}·s_n/(√n·x̄_n) が d_required 以下になった n を採り、**kLimit 本先読み**して維持を確認(n≤100 なら kLimit 本)。「Let n = 3」から始める。
- Law 2020: 「**If we increase the sample size from n to 4n, then the half-length of the confidence interval … will decrease by a factor of approximately 2**」。例: 半幅 0.9→0.3 に「**approximately 450 (= 9 × 50) replications**」。

## 効く箇所(seam)

- **d_8 = 100·t_{7,0.975}/√8 · CV = 83.6·CV**。±5% を主張できるのは seed 間 CV ≤ 6.0% のとき。CV 10%・±5% なら N≈18。
- 先読み kLimit=5 なら 8 を認定するのに 13 本(+45.9 h)。
- 精度 3 倍 → 本数 9 倍(n ∝ 1/精度²)= D-70 の「2 h/シミュ日」投資の算術に直結。

## 「結論でなく機構として」の入れ方

**8 本の CV から d_8 を全指標で表にし、束縛は最大値**(Lee)。d_8 が精度線に入る指標と入らない指標を分けて台帳に書く。

- 関連: [[stats__lee2015_abm-output-analysis]] [[stats__siepe2024_simulation-study-template]] [[compute__matsim2020_hermes]]
