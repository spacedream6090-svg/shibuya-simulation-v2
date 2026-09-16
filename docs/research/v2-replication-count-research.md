# 答申: 確率的シミュレーションの反復回数(seed 数)は文献でどう決めるか — 我々の「初回 8 seed」の位置(2026-09-16・第200・レーン L-B)

<!-- hdr:v1 -->
- **分野**: 統計学・因果推論 #23 / ABM 方法論 #21 / 検証と V&V #22 | **重要度**: P0(D-70 性能ゲート・D-44 感度試験の算術・G-8「初回 seed 群 8 本」の expedient に直結)
- **一次確認**: **A**(サブ Opus 5 が 8 文献を実読し逐語採取 → 親が **9 出典を再取得**: Lee 2015・Siepe 2024・ten Broeke 2016・ECMWF Newsletter 153 は WebFetch で逐語一致、Ritter 2011・Hoad 2007・Law 2020・Leutbecher 2017・Secchi & Seri 2017 は PDF を pymupdf で本文抽出して逐語一致。**空欄**: Lorscheid 2012 の原典(有料・OA 無し)・Law 教科書の逐次手続きの原文・Secchi & Seri の経験式 (2) の係数(PDF のテキスト層に無い=図版)・Leutbecher の QJRMS 査読版。親が全数値を再計算(§2))
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **lit**: [lit/README.md](lit/README.md)(stats__lee2015 / stats__siepe2024 / stats__tenbroeke2016 / stats__ritter2011 / stats__secchi-seri2017 / stats__hoad2007-law2020 / ensemble__ecmwf_ensemble-size) ・ **判断**: PENDING D-70・D-44

> **問い**: 初回アンサンブルの seed 数 **8**(G-8・expedient)を文献の手続きで置き換えるには何を測ればよいか。1 seed = 1 シミュ日 = **9.17 h**(7 GPU)。
> **答え(要旨)**: 文献の系譜は 3 つ。(i) **統計方法論・ABM 出力分析**(Siepe・Lee・Lorscheid・ten Broeke)は 10²〜10⁴ 本が標準で、**8 は 2〜3 桁足りない**。(ii) **検出力**(Ritter・Secchi & Seri)では 8 seed/腕は「seed 間 SD の **1.65 倍**(power .90)以上の差しか見えない」設定。(iii) **気象アンサンブル**(ECMWF)は運用 51 だが、**R&D では「2〜4 で足りる(交換可能性+fair score が条件)」と ECMWF 自身が言っている**=8 を文献準拠で正当化できる唯一の枠。**追加ラン 0 本で今日できる 3 手**が §5。

---

## 1. 一次確認の結果(逐語・URL・確認状態)

| # | 文献 | URL | 逐語引用(原文のまま・抜粋) | 反復回数の決め方の要点 | 確認 |
|---|---|---|---|---|---|
| 1 | **Lorscheid, Heine & Meyer (2012)** CMOT 18(1):22–62 | https://doi.org/10.1007/s10588-011-9097-3 | 抄録のみ。本文の CV 手続きは原典未読(Unpaywall `is_oa:false`・Semantic Scholar `CLOSED`) | — | **原典=空欄**(サブ・親とも抄録のみ) |
| 1′ | (1 を逐語で引く二次)**Lee et al. (2015)** JASSS 18(4)4 | https://jasss.soc.surrey.ac.uk/18/4/4.html (DOI 10.18564/jasss.2897) | "Lorscheid et al.'s method eschews those assumptions by employing the coefficient of variation and a fixed epsilon (E) limit of that metric." / "**The sample size at which the difference between consecutive c_V's falls below a criterion, E, and remains so is considered a minimum sample size or minimum number of ABM runs.**" / 例: n∈{10,500,1000,5000,10000} で c_V {0.42,0.28,0.21,0.21,0.21}・E=0.01 → "we would consider the third sample size (n = 1000) as the point of stability" | 統計量 c_V=σ/μ・閾値 E は解析者が固定・連続する c_V の差が E 未満で**以後も維持**・多指標は最大値 | **親再取得・逐語一致** |
| 1″ | (同・別の二次)**ten Broeke et al. (2016)** | https://jasss.soc.surrey.ac.uk/19/1/5.html | "The stabilization of the coefficient of variation, c_v=σ(n)/μ(n) … indicates the required number of replicates to obtain a proper estimate of the distribution of the model output (Lorscheid et al. 2012)." (§5.4 式 7) | 同上 | **親再取得・逐語一致** |
| 2 | **Law / Law & Kelton** *Simulation Modeling and Analysis*(逐次手続き `n_r*(β)` の原文) | — | — | — | **見つからず**(教科書本文はオンラインで読めず。式番号・章は記憶で埋めない) |
| 2′ | (2 を引く二次)**Hoad, Robinson & Davies (2007)** WSC | https://www.informs-sim.org/wsc07papers/060.pdf | "Law and McComas (1990) recommend running at least 3 to 5 replications. This rule of thumb is useful for telling users that relying upon the results of only one run is unwise. However, **it makes no allowance for the characteristics of a model's output**" / 停止則 "to stop as soon as d_n is first found to be less than or equal to the set desired precision, d_required (user defined)" / "the algorithm is designed to look ahead … We call this 'look ahead' value kLimit." / "Let n = 3" | 相対精度 d_n=100·t·s/(√n·x̄) が d_required 以下になった n を採り、kLimit 本**先読み**して維持を確認(n≤100 なら kLimit 本) | **親 PDF 実読・逐語一致** |
| 2″ | (Law 本人)**Law (2020)** "Statistical Analysis of Simulation Output Data: The Practical State of the Art", WSC 2020 | https://informs-sim.org/wsc20papers/134.pdf | "**If we increase the sample size from n to 4n, then the half-length of the confidence interval … will decrease by a factor of approximately 2**, since there is an n in the denominator under the square-root sign." / "If we want to reduce the half-length from 0.9 to, say, 0.3, then a total of approximately **450 (= 9 × 50) replications** will be required." / 参考文献 "Law, A. M. 2015. Simulation Modeling and Analysis, 5th ed. New York: McGraw-Hill." | n ∝ 1/精度²。教科書は 5 版(2015)が現行 | **親 PDF 実読・逐語一致** |
| 3 | **Siepe, Bartoš, Morris, Boulesteix, Heck & Pawel (2024)** *Psychological Methods* | https://doi.org/10.1037/met0000695 (全文 https://pmc.ncbi.nlm.nih.gov/articles/PMC7616844/) | "**When planning a simulation study, researchers should choose a number of simulation repetitions that ensures a desired precision for estimating the chosen performance measures.** The last column of Table 3 gives simple formulae" / "**the number of repetitions must be chosen large enough such that the MCSE is sufficiently small compared to the relevant effect of interest** … as to our knowledge **there are no standards**." / Table 3「Mean of generic statistic G」: MCSE=√(S_G²/n_sim)・**n_sim=S_G²/MCSE\*²** / 作例 "0.50 × (1 − 0.50) / 0.005² = 10,000" / 調査 "**The number of repetitions per simulation condition ranged between 1 and 1,000,000** … **The median number was 900** … **Only 8% of the studies provided a justification** … **only 3% of these actually performed a calculation**" | **目標 MCSE から逆算**して事前登録で宣言。未知量は最悪値かパイロット | **親再取得・逐語一致** |
| 4 | **ten Broeke, van Voorn & Ligtenberg (2016)** JASSS 19(1)5 | https://jasss.soc.surrey.ac.uk/19/1/5.html (DOI 10.18564/jasss.2857) | "**We perform 10,000 replicate runs** in the default parameter set to estimate the distribution of the output." / "the coefficient of variation is **largely stabilised after a few hundred replicates**." / OFAT "we use 10 replicates per parameter setting" / 回帰 "5 replicates" / Sobol "We therefore do not use any replicates." / "**The mean output variance over replicates is 0.88% of the output variance over all samples.**" → "we do not need to increase the number of replicate runs per parameter setting." | 二段構え: 分布推定は CV 安定(数百)・感度解析は 10/5/0・**seed 間分散 ÷ 条件間分散が小さいことを測って追加不要を証明** | **親再取得・逐語一致**(「do not need」の文は 0.88% の 2 文後) |
| 5 | **Lee et al. (2015)** JASSS 18(4)4(本体) | 同 1′ | "For those large and complex ABMs whose longer run times prohibit the production of large samples, **the relevant question is the minimum number of required runs.**" / "sample sizes to be too low, conveniently selected (**sample sizes of 100 or less are common**), or exorbitantly high" / "**we urge some caution in using c_V** to determine the minimum sample size" / 窓付き分散 "our **semi-subjective criterion (of 0.20)**" / 検出力 n_min ≥ 2(s²/δ)(t_{ν,1−α/2}+t_{ν,1−β/2})² / "**a predetermination of test sensitivity (e.g., effect size) must be made before calculating a minimum number of runs. However, the stability of outcome variance needs to be secured**" | 2 段階: (i) 出力分散の安定(CV or 窓付き分散 0.20)→(ii) 効果量を先に決めて検出力で n_min。μ≈0 の指標に c_V は不向き | **親再取得・逐語一致** |
| 6 | **Buizza & Richardson (2017)** "25 years of ensemble forecasting at ECMWF", ECMWF Newsletter 153 | https://www.ecmwf.int/en/newsletter/153/meteorology/25-years-ensemble-forecasting-ecmwf (doi 10.21957/bv418o) | "**Theoretical work done in the 1970s and 1980s suggested that one needs at least about 10 members for a good ensemble-mean forecast**" / "**increasing the ensemble size from say 10 to about 50 was found to have a clear and detectable impact** … **Further increases beyond 50 have a smaller effect, on average, but can still have a detectable impact** [if one wants to predict rare events]" / "**Resolution, forecast length and the number of ensemble members are key cost drivers of ensemble production.**" / Box A: Dec 1992 "ENS includes 33 members"・Dec 1996 "the number of members was increased from 33 to 51" | 10 で平均・50 で確率分布・50 超は逓減(稀事象は別)+計算資源との妥協 | **親再取得・逐語一致**(著者名はサブ空欄→親が確認) |
| 6′ | **Leutbecher (2017)** "Ensemble size: How suboptimal is less than infinity?" ECMWF Annual Seminar(査読版 QJRMS 145 Suppl.1, DOI 10.1002/qj.3387=未読) | https://www.ecmwf.int/en/elibrary/80289-ensemble-size-how-suboptimal-less-infinity (PDF `…/elibrary/2017/17621-ensemble-size-how-suboptimal-less-infinity.pdf`) | スライド 2 "50 member since Dec 1996 / **Why 50?** / Are the benefits of more than 50 members marginal?" / "ensemble size was increased from **32 to 50** members" / スライド 15 "**1 + 1/M** … CRPS(M)/fairCRPS(M) … **50 and 200 members are 2% and 0.5% worse than ∞**, respectively" / 24 "Small ensemble sizes • Can be used for R&D if evaluation uses fair scores … • Current ensemble generation at ECMWF not fully consistent with exchangeability" / 26 "Operational ensemble forecasts: **50 members are too few**" / "Research & Development: Small ensembles are highly efficient. **Two to four members may be enough for standard evaluations** (provided exchangeability in the ensemble generation and use of fair scores)" | **交換可能なアンサンブルでは CRPS_M=(1+1/M)·CRPS_∞**=メンバー数の罰は 1/M。fair score で偏りを除けば少数で比較可 | **親 PDF 実読・逐語一致**(32→50 と Newsletter の 33→51 は摂動 vs 摂動+コントロールの数え方の差) |
| 7a | **Ritter, Schoelles, Quigley & Klein (2011)** in *Human-in-the-Loop Simulations* pp.97–116 | https://doi.org/10.1007/978-0-85729-883-6_5 (著者版 https://acs.ist.psu.edu/papers/ritterSQKip.pdf・"Draft of 24 December 2010") | "**because the simulation is a theory, not data, it should not so much be sampled but run enough times to provide stable predictions of performance and of the variance of performance.**" / "3.60/sqrt(N) = 0.255. Solving for N gives us **199 runs**." / "**we recommend 150 runs** as a reasonable number that provided very stable predictions for medium to large effects." / "We suggest that **a power of 0.90** for the expected effect size can provide a suggestion of how many runs are required when runs are expensive, and **a power of 0.99** when runs are inexpensive." / Table 4(δ=ES·√(N/2)・power .90・δ=3.30): ES 0.1→**2,178** / 0.2→**545** / 0.5→**88** / 0.8→**34** ; Table 5(power .99・δ=4.20): 0.1→**3,528** / 0.2→**882** / 0.5→**142** / 0.8→**56** | SEM が用途上十分小さくなるまで。費用高=power .90・安=.99。**150 本を推奨** | **親 PDF 実読・逐語一致**(著者版。Springer 版は有料=未確認) |
| 7b | **Secchi & Seri (2017)** "Controlling for false negatives in agent-based models: a review of power analysis in organizational research", CMOT 23(1):94–121・Open Access CC BY 4.0 | https://doi.org/10.1007/s10588-016-9218-0 | "**We suggest the reference for every ABM should be to reach power of 0.95 and higher at a 0.01 significance level.**" / Table 2: ES=0.1・α=0.01 の平均検出力 **0.415**(SD 0.395)/ 抄録 "Findings show that **most studies are underpowered**, with some being overpowered." / 経験式 (2) **n(J,ES) ≃ 14.091·J^−0.640·ES^−1.986**(α=0.01・β=0.05・ES=Cohen の f) | 検出力で決める。J 群・ES を先に宣言し α=0.01/power 0.95 を ABM の標準に。**多すぎるのも害** | **親 PDF 実読**: 0.95/0.01・0.415・CC BY・underpowered は逐語一致。**式 (2) の係数はテキスト層に無く親未確認**(サブ逐語) |

## 2. 我々の 8 seed に当てるとどうなるか(親が再計算)

記法: N=seed 数・1 seed=9.17 h・X_i=seed i の出力を 1 スカラーに畳んだ指標(例: 08–09 時のピーク在圏・行動分布 JSD)・CV=s_N/x̄_N。**今日ある 8 本から追加費用ゼロで測れるのは x̄_8・s_8・CV の 3 つ**で、以下の全手続きの入力はこれで足りる。

| 枠組み | 式 | N=8 を代入 | 逆算 |
|---|---|---|---|
| **(A) Siepe** MCSE 目標 | n_sim=S²/MCSE\*² ⇔ N=(CV/r)²(r=目標相対 MCSE) | **r_8 = CV/√8 = 0.354·CV**(CV 10% → seed 平均の MCSE 3.5%) | MCSE 1% には N=(0.10/0.01)²=**100**・0.5% なら 400 |
| **(B) Law/Hoad** 逐次 CI | d_N[%]=100·t_{N−1,0.975}·CV/√N | t_{7,0.975}=2.3646・√8=2.8284 → **d_8 = 83.6·CV**。**±5% を主張できるのは CV ≤ 6.0% のときだけ**(±10% なら ≤12%) | CV 10%・d 5% → N≈(1.96·0.10/0.05)²=15.4 → t で反復 **≈18**。Hoad の先読み kLimit=5 なら 8 の認定に 13 本(+45.9 h)。Law「n→4n で半幅 1/2」と同値 |
| **(C) Lorscheid/Lee** CV 安定 | 複数 n での c_V の梯子・連続差 < E で以後も維持 | **実行不能**: 8 本では梯子は n∈{2,4,8} の入れ子までで、n=8 が右端=「以後も維持」が原理的に検証できない | 最小の梯子 {2,4,8,16,32} で 32 本=**293 h=12.2 日**(既存 8 込みなら +24 本=220 h=9.2 日)。Lee の警告=μ≈0 の指標(稀な行動・深夜在圏)で n_min を過大評価 |
| **(D) Ritter** 検出力 | δ=ES·√(N/2) | √(8/2)=2 → **power .90 なら ES=3.30/2=1.65・power .99 なら 2.10** → **seed 間 SD の 1.65 倍より小さい条件差は 8 seed では検出できない** | ES 0.8(large)→34 本=311.8 h=13.0 日 / 0.5→88 本=807 h=33.6 日 / 0.2→545 本=4,998 h=208 日 / Ritter 推奨 150 本=1,375 h=**57.3 日** |
| **(E) Secchi & Seri** 経験式 | n(J,ES)≃14.091·J^−0.640·ES^−1.986(α=.01・power .95) | J=2: 14.091·2^−0.640=9.04 → n=8 で **f≈(9.04/8)^(1/1.986)≈1.06**(Cohen の large 0.4 の 2.6 倍) | f=0.4→56/群=112 本=1,027 h=42.8 日 / 0.25→142/群=284 本=108 日 / 0.1→876/群=1,752 本=670 日 |
| **(F) ECMWF/Leutbecher** fair score | 交換可能なら CRPS_M=(1+1/M)·CRPS_∞ | **M=8 → +12.5%**(16→6.25%・32→3.13%・50→2.0%=実測と一致・200→0.5%)。偏りは**ラン数を増やさず解析的に除ける**: fair 化の補正係数 1/(2M²(M−1))=**1/896** | 条件 2 つ=(1) seed の**交換可能性**(同一分布からの draw か。ECMWF 自身も「完全には満たしていない」)(2) proper score を fair 化して使う。R&D 用途は「2〜4 で足りる」 |
| **(G) ten Broeke** 追加不要の証明 | seed 間分散(条件固定)÷ 全サンプル分散 ≪ 1 | 既存 8 本と条件間の差(例: c7-day-2/3/4 の腕)から**追加ラン 0 本で計算できる**。0.88% 級なら「シナリオの順位づけには 8 で足りる」を文献の手続きで示せる | — |

### 位置づけ

| 枠組み | その分野の標準 | 我々の 8 |
|---|---|---|
| 心理方法論(Siepe) | 中央値 900・作例 10,000 | 2〜3 桁不足。**手続き(MCSE 目標から逆算し宣言)はそのまま使える** |
| ABM 出力分析(Lee/Lorscheid/ten Broeke) | 数百〜10,000 | 2〜3 桁不足。CV 安定法は梯子が作れず判定不能 |
| ABM 検出力(Ritter/Secchi & Seri) | 34〜3,528(ES 依存)・推奨 150 | 床 ES≈1.65 SD(d)/f≈1.06=「特大の差専用」 |
| 気象アンサンブル運用(ECMWF ENS) | 51(摂動 50+コントロール 1) | 1 桁不足(ただし 50 超は逓減) |
| **気象アンサンブル R&D(Leutbecher)** | **2〜4**(fair score+交換可能性) | **余裕で上回る** |
| rule of thumb(Law & McComas 1990) | 3〜5 | 上回る(Hoad「モデルの出力の性質を見ていない」) |

## 3. 含意(D-70・D-44・G-8)

- **G-8「初回 seed 群 8 本」は、ABM/統計方法論の系譜では正当化できない**(2〜3 桁不足)。これは D-44 の算術(122 expedient × 2 seed = 93 日)と同じ壁で、**現在のラン費用(9.17 h/seed)では到達不能**。
- **正当化できる唯一の枠= ECMWF の R&D 枠(小アンサンブル+fair score)**。そのために要るのはランを増やすことではなく、(i) seed の交換可能性の検査(温度・初期配置・母集団抽出が同一分布からの draw か)(ii) 使うスコア(JSD 等)の fair 化=有限 M 由来の正のバイアス項を解析的に引く (iii) **検出可能効果量の床(≈1.6〜2.1 seed 間 SD)を台帳に明示宣言**すること。
- **D-70(2 h/シミュ日への投資)の判定は「8 本の CV」1 回の測定で決まる**(第191 の見立てを文献で裏づけ): CV が小さければ (B) の d_8 が精度線に収まり 8 で足りる。大きければ (A)/(B) の逆算 N が出て、N×9.17 h が予算に収まらないことが 2 h/日への投資の根拠になる。
- **待ち合わせ等「稀な行動」を指標にするなら c_V は不向き**(Lee)。分母が 0 に近い指標は窓付き分散か検出力設計に切り替える。

## 4. 見つからず・空欄

Lorscheid 2012 本文(推奨 E・error variance matrix の原文)/ Law 教科書の逐次手続きの原文(版・章・式番号)/ Secchi & Seri 式 (2) の係数の逐語(PDF テキスト層に無い・図版)/ Leutbecher (2019) QJRMS 査読版本文 / ECMWF が「51」を選んだことを説明する明示文書(「10→50 で明確な改善・50 超は逓減・資源との妥協」と「Why 50?」が唯一。**51=摂動 50+コントロール 1・摂動は特異ベクトルの ± 対で偶数**という構造制約のみ)。

## 5. 親の見立て(未リサーチ・判断の材料)— 追加ラン 0 本で今日できる 3 手

1. **既存の seed 違いから各指標の CV を出し d_8=83.6·CV を表にする**(Hoad 式)。C6 T7 の seed 違い(JSD 0.0035 bits)と C8 AB6 seed 2 は既にある。Lee §2.18 に従い**束縛するのは全指標の最大値**。
2. **同じ CV から N=(CV/r)² を解く**(Siepe 式)。目標 r は**現実整合アンカーの許容幅**から決める(Siepe「関連する効果より MCSE を小さく。標準は無い」)。
3. **seed 間分散 ÷ 条件間分散**(ten Broeke §5.9)。数 % 以下なら 8 を文献準拠で擁護できる。
- S1 の初アンサンブル 8 seed は、この 3 手を**事前登録 v1.2 に書いてから**回す(何を測って 8 の可否を言うかを先に固定)。JSD を指標にするなら fair 化(有限標本バイアスの解析的除去)を同時に入れる。
- **D-44 への追記材料**: 検出力の系譜(Ritter・Secchi & Seri)では 2 seed の感度試験は f≈1 以上の効果しか検出できない=「結果を駆動していない」の証明にはならず、「特大の駆動が無い」の証明にしかならない。→ D-44 の方法論ゲートの文言を「検出可能効果量の床つき」に書き直す必要(判断)。

## 6. 空欄 → 残務台帳へ

§4 の 5 件。lit メモ 7 本(本答申と同じ第200)。Lorscheid 原典は図書館経由でしか読めない=R- 番号で保留。
