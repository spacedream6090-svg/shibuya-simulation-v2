# v2-d68-remaining-research — D-68 経路 3(記憶・習慣)の残 10 件を一次資料で埋める(答申・実装なし)

<!-- hdr:v1 -->
- **分野**: 人間移動科学 #3 / 時間利用研究 #4 / 認知科学(記憶・習慣)#12 | **重要度**: P0
- **一次確認**: **B** = サブが本文/表/API を実読・数値は再計算できる形で提示。**親の一次確認前**。取得不能は §3 に空欄として残す **→ 親確認 3 件(第212)**: e-Stat 時間帯編 第15-4表(手元 xlsx `a015_4`・親 openpyxl 再計算)平日・雇用者・仕事の 0:00 行動者率=全国 交替制(会社都合 122)8.82 / 固定 1.83(比 4.82)・東京都 8.25 / 0.59(比 14.0)=一致 / REAL Sampling(arXiv 2406.07735 PDF)Appendix J「Wikipedia validation set (around 9M tokens)」「90.2% contexts … Pythia LM (70M) has a larger next-token entropy compared to … (6.9B)」/ Springer 2026(arXiv 2605.09995 HTML 本文)「Larger base models are not less diverse, but larger post-trained models are」。**表58-2-1 の通勤時間分位(43.7 分/33.0 分/5.07%)・Lu 2013・Pseudo-PFLOW・2604.01520 は親未確認**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **進行状況**: [RESEARCH-STATE.md](RESEARCH-STATE.md) ・ **親答申**: [v2-d68-behavioral-diversity-research.md](v2-d68-behavioral-diversity-research.md)

> 2026-09-17・リサーチサブ(Opus 5)。レーン **R-3**。対象は [v2-d68-behavioral-diversity-research.md](v2-d68-behavioral-diversity-research.md) **§8 の残 10 件**([RESEARCH-STATE.md](RESEARCH-STATE.md) §2-C)。
> 規律: 子サブ未起動・コミットなし・既存ファイルの編集は[ライセンス台帳](../data-license-ledger.md)の追記 1 行のみ・holdout 未開封。
> 表記: **[実読]** = 本文/表/API を実際に読んだ。**[要旨]** = 抄録のみ。**[二次]** = 他文献の引用経由。逐語は「」で括り 125 字以内。

---

## §0 10 件の帰結(先に結論)

| # | §8 の問い | 帰結 | 等級 |
|---|---|---|---|
| ① | 日本の始業時刻の分布表 | **存在しない**(e-Stat 全数検索で「始業時刻」0 件)。最も近い公的代理を**新規に特定・計算**(時間帯編 第15-4表) | 解決(代理) |
| ② | 片道通勤時間の分布(令和3年 社会生活基本調査) | **令和3年には無い**(分類事項が平成23年で終了)。代替を**新規に特定**=令和5年 住宅・土地統計調査 表58-2-1(**渋谷区まで**) | 解決(差し替え) |
| ③ | Schneider 2013 Fig.3 の p(ID) | **本文に数値なし**(棒グラフのみ)。順位と「2 地点モチーフが約半数」は逐語で取得。追試 3 件の被覆率を代替値として取得 | 部分 |
| ④ | Schlich & Axhausen 2003 原典 | **有料のまま**(ETH の Download は DOI へ転送)。抄録は逐語取得。「36 通り中 8.6」の出所は**特定できず** | 空欄 |
| ⑤ | inverse scaling と REAL Sampling の本文 | **両方とも本文実読**。両者は**逆を言っている**(測っているものが違う)ことを確認 | 解決 |
| ⑥ | arXiv 2604.01520 の考察節 | **実読**。探していた分散比が逐語で存在=「**20〜300 倍小さい**」 | 解決 |
| ⑦ | Song 2010 の追試値 | **Lu 2013 を本文実読**(88%・500,000 人・MC 0.91)。Haiti 85% は Lu 2013 の逐語引用で確認(原典未読)。Smith 81-85% は抄録の別表現を取得 | 部分 |
| ⑧ | 交替制勤務の出勤時刻分布 | **出勤時刻 × 交替制の表は存在しない**(平均時刻編 67 表に勤務形態軸ゼロ)。時間帯編 第15-4表で**時刻像を計算**(深夜率 4.8 倍) | 解決(代理) |
| ⑨ | 日本の PT へのモチーフ適用研究 | **2 件特定**。Pseudo-PFLOW(実読・図のみ)と CUPUM 2021 章(有料)。「都市圏で差が無い/役割で差が出る」を逐語で取得 | 部分 |
| ⑩ | TrajLLM の定量評価 | **定量評価は存在しない**(節構成に実験節が無い・数値ゼロ・10 体のデモのみ) | 解決(否定) |

---

## §1 10 件の表

### ① 日本の始業時刻の分布表 — 公的統計には無い。代理は時間帯編 第15-4表

- **一次確認**: e-Stat API `getStatsList`(全統計横断・`searchWord=始業時刻`)= **0 件**。`始業時間` = 289 件だが全て社会生活基本調査の**分類事項名**(勤務形態の選択肢)であって時刻分布ではない。**[実読・API]**
- **平均時刻編 67 表の軸を全数確認**: `stat-search/files` の素の HTTP GET で 67 表の表番号を取得し「勤務形態」を含む表 = **0 件**、「出勤」を含む表 = **6 件**(29-1・29-2・30・31・32・33)。既存答申 §2-3 の「出勤 ≠ 始業」はそのまま残る。**[実読]**
- **代理(新規)**: **令和3年社会生活基本調査 時間帯編 第15-4表**(statInfId `000032224355`・xlsx・シート `a015_4`)。軸 = 曜日 × 地域区分(全国+47 都道府県)× 男女 × 従業上の地位 × **勤務形態(7 区分)** × 行動の種類(24)× **時刻区分(15 分・96 区分)**、値 = 行動者率(%)。
- **計算法(再現可能)**: 行(曜日=`1_平日`, 地域=`13_東京都`, 男女=`0_総数`, 地位=`1_うち雇用されている人`, 行動=`05_仕事`)の時刻区分別行動者率 v(t) をとり、**朝の窓 04:00–12:00 の正の階差 Δv(t)=max(0, v(t)−v(t−1)) を始業時刻の密度とみなす**。
- **数値(親が再計算できる形)**:

| 勤務形態(平日・雇用されている人・「仕事」) | 地域 | 朝の純増合計 | p10 / p50 / p90 | `:00+:30` 率 | H(32 区分) |
|---|---|---|---|---|---|
| 0_総数 | 全国 | 69.01 pt | 7:00 / 8:15 / 9:15 | 67.0% | 3.801 bit |
| 0_総数 | 東京都 | 71.33 pt | 7:15 / 8:45 / 10:00 | 66.4% | 3.892 bit |
| 11_始業時間が固定されている | 東京都 | 82.49 pt | 7:30 / 8:30 / 9:30 | 65.8% | 3.810 bit |
| 121_選択できる(裁量/フレックス) | 東京都 | 87.78 pt | 7:30 / 8:45 / 10:00 | 67.3% | 3.762 bit |
| 122_会社の都合(交替制勤務など) | 東京都 | 44.32 pt | **5:45** / 8:30 / 10:00 | 70.6% | 3.969 bit |

- **限界(expedient として登録すべき)**: 行動者率の階差は「始業」だけでなく**短い中断からの復帰**を含む(13:00 に +21〜32 pt の巨大な山が出るのは昼休み明けであって始業ではない。だから窓を 04:00–12:00 に切っている)。また母数は当日働いていない有業者を含む。**「始業時刻の分布」そのものではない**。
- **含意(記憶・習慣の設計へ)**: ① D-68 の M3(開始分)の現実アンカーは**出勤(第30表)の 4.680 bit / 67.5%** に加えて**始業代理(第15-4表)の 3.8〜3.9 bit / 66%** を持てる。`:00+:30` はどちらでも **66〜68%** に収束する=「:00/:30 を禁じるのは過補正」という第155 の親判断を**独立の表で再確認**した。② 勤務形態で分位は動くが `:00+:30` 率はほぼ動かない(65.8〜70.6%)=**丸めの強さは勤務制度の属性ではない**。習慣の表現を制度で分岐させても時刻の丸みは直らない。

### ② 片道通勤時間の分布 — 令和3年には無い。令和5年 住宅・土地統計調査 表58-2-1 へ差し替え

- **令和3年に無いことの確認**: e-Stat API で社会生活基本調査(statsCode `00200533`)× `searchWord=通勤時間` = 297 表。調査年別内訳 **平成8年 72 / 平成13年 79 / 平成18年 122 / 平成23年 24 / 平成28年 0 / 令和3年 0**。分類事項「ふだんの片道の通勤時間」は**平成23年で終了**している。**[実読・API]**
- **代替(新規に特定)**: **令和5年住宅・土地統計調査 住宅及び世帯に関する基本集計 表58-2-1**、statsDataId **`0004021722`**。題名「通勤時間 住宅の所有の関係(5区分)、家計を主に支える者の男女別通勤時間(8区分)別家計を主に支える者が雇用者である主世帯数－全国、都道府県、**市区町村**」。地域 1,283 件に**渋谷区(13113)が含まれる**。**[実読・API]**
- **数値(cat01=0 総数・cat02=0 総数・時間軸 2023 年)**:

| 通勤時間 | 全国 | 東京都 | 渋谷区 |
|---|---|---|---|
| 総数(世帯) | 21,957,400 | 2,386,200 | 32,530 |
| 自宅・住み込み | 2.20% | 3.53% | **5.07%** |
| 15 分未満 | 21.19% | 9.05% | 10.24% |
| 15〜30 分未満 | 29.19% | 17.42% | 25.64% |
| 30〜45 分未満 | 16.18% | 19.26% | **29.17%** |
| 45 分〜1 時間未満 | 14.01% | 23.86% | 15.80% |
| 1 時間〜1 時間 30 分未満 | 11.37% | 17.89% | 6.42% |
| 1 時間 30 分〜2 時間未満 | 2.72% | 3.60% | 0.98% |
| 2 時間以上 | 0.79% | 0.69% | 0.31% |
| 不詳 | 2.35% | 4.69% | 6.36% |

- **派生(不詳を除き級内一様で線形補間・親が再計算可)**: 平均(級中央値) **全国 34.8 分 / 東京都 44.6 分 / 渋谷区 34.2 分**。p10/p25/p50/p75/p90(分)= 全国 **5.4 / 15.5 / 28.1 / 49.8 / 73.5**、東京都 **9.9 / 24.7 / 43.7 / 59.0 / 81.2**、渋谷区 **6.3 / 19.7 / 33.0 / 45.1 / 58.4**。60 分以上の比率 = 全国 15.23% / 東京都 23.28% / 渋谷区 8.24%。
- **限界**: 世帯単位(**家計を主に支える者**のみ)であって個人分布ではない。母集団は「家計を主に支える者が雇用者である主世帯」。2 時間以上は上限なしなので平均は下振れする(上表は 120–150 分と置いた)。**丸め注**: 値は 100 世帯単位に丸められており、9 区分の和は総数欄と **全国 −100 / 東京都 +100** ずれる(渋谷区は一致)。上の構成比は総数欄を分母にしている。
- **含意**: ① 下見設計書 §2-3 の `arrival_lead_min`(プールの p10/p50/p90 = **14/40/66 分**)は、**東京都 9.9/43.7/81.2 と p50 がほぼ一致**し(43.7 対 40)、**渋谷区 6.3/33.0/58.4 とは中央で 7 分ずれる**。候補 (a) を採ったことに独立の裏づけができ、「意味が通勤時間か余裕時間か未確認」というリスク 5 は**中央値の一致という形で部分的に消える**。② 出勤時刻 → 始業時刻のオフセットを**一律 30 分**にすると東京都の実測中央値 43.7 分より 14 分短い。**分布から個体ごとに引く**のが現実側。③ 渋谷区は「自宅・住み込み 5.07%」が全国の 2.3 倍=**在宅の体を最初から持つべき**(D-67 の出勤率 0.88 とは別の口)。

### ③ Schneider et al. 2013 Fig.3 の p(ID) — 数値は図のみ。順位と代替値を取得

- 出典: Schneider, Belik, Couronné, Smoreda, González (2013) *J. R. Soc. Interface* 10(84):20130246, doi:10.1098/rsif.2013.0246。PMC 全文を実読。**[実読]**
- **本文は順位しか書いていない**(逐語): 「The most common motif (ID 2) consists of two visited locations and two trips among them, followed by a motif with only a single location (ID 1).」続いて ID 3(3 地点 4 トリップ・全て同一地点発着)、ID 4(1 往復)。**p(ID) の数値は Figure 3 の棒の高さにしかない**。図の凡例逐語:「The probability p (ID) to find one of these 17 motifs in the surveys (cyan, Paris; blue, Chicago), the phone data (orange, Paris), and the model … is presented.」
- **本文にある閾値と数え上げ(逐語)**: 「we call motifs the daily networks which are found on average more often than 0.5 per cent in the datasets」/ N_f(1)=1, N_f(2)=1, N_f(3)=5, N_f(4)=83, N_f(5)=5048, **N_f(6)=1 047 008** / 「up to 90 per cent of the measured trips can be described with only 17 different daily networks」。**[実読・§2]**
- **自己相関(M6 に効く逐語)**: 「the highest correlation of each motif is the self-correlation C_ii which is usually **10–30 times more likely** than expected by selecting individual motifs according to the observed distribution」。観測期間は携帯 **6 か月**。**[実読・§2]**
- **代替の数値(追試 3 件)**:
  - **約半数が 2 地点モチーフ**: arXiv 2012.06920 が Schneider 2013 を引いて逐語「nearly half of the population follows a simple two-location mobility motif」。**[実読・二次]**
  - **シカゴ/大ボストン(Twitter・地物つき)**: 「16 types of LBM are significant and consistent between Chicago and Greater Boston. In fact, **14 (out of 16) LBMs are identical** to the ones identified by Schneider, Belik, et al. (2013)」。被覆率 = **シカゴ 83% / 大ボストン 85%**。ID 13・16・17 は非有意、新規 2 型(ID 18・19)が有意。**[実読]**
  - **シンガポール**: 「**11 (out of 17) LBMs were identified**」(Jiang, Ferreira & González 2017 として引用)。**[二次]**
- **含意**: **M1(モチーフ種類率)の合格線を「17 個で 90%」に固定してはいけない**。独立の追試は **16 型で 83〜85%**、シンガポールでは **11 型**。データ源と閾値(0.5%)で型数が変わる。M1 は上限側の門番という第155 の親判断は正しいが、**帯を「11〜17 型 / 被覆 83〜90%」に広げる**のが一次資料の姿。自己相関 10–30 倍は**個人内一貫性の現実側アンカーとして M6 に直接使える**(ただし複数日の下見が要る)。

### ④ Schlich & Axhausen 2003 — 原典は有料のまま。抄録のみ逐語

- 出典: Schlich, R. & Axhausen, K. W. (2003) "Habitual travel behaviour: Evidence from a six-week travel diary", *Transportation* 30(1):13–36, doi:10.1023/A:1021230507071。**[要旨]**
- ETH IVT の Mobidrive アーカイブに「Download」表記があるが、リンク先は **DOI(Springer 有料)**であり無料 PDF は置かれていない(HTML の href を直接確認)。IVT Arbeitsbericht 版の PDF も当該番号では取得できなかった(ETH の配信パスは 404)。
- **抄録の逐語(要点)**: 「the day-to-day behaviour is more variable if measured with trip-based methods instead of methods based on time budgets」/「travel behaviour is neither totally repetitious nor totally variable」/「**two days always have some common elements**」/「Travel behaviour is clearly more stable on work days」。標本 = 6 週間(42 日)のトラベルダイアリー(Mobidrive)。
- **「36 通り中 平均 8.6 通り/42 日」の出所は特定できなかった**(抄録に無く、引用元も辿れなかった)。§3 の空欄に残す。
- **含意**: M6(個人内一貫性)の**定性的な形**は原典の抄録で確認できる=「**完全同一でも無関係でもない**」「**任意の 2 日は必ず共通要素を持つ**」「**勤務日ほど安定**」。この 3 点は第155 の M6 合格条件(J≈1 も J≈0 も不合格)の直接の根拠になる。**数値(8.6/36)は使わない**。

### ⑤ inverse scaling と REAL Sampling — 両方本文実読。両者は逆を言っている

**(a) REAL Sampling(Chang, Peng, Bansal, Ramakrishna, Chung 2024・arXiv:2406.07735・Amazon AGI Foundations)** **[実読・HTML v1]**

- 探していた数値は **Appendix J「Why does the Entropy Decay as the Model Size Increases?」**にある。逐語: 「the average entropy across our Wikipedia validation set (**around 9M tokens**) steadily decreases as the model size increases. Furthermore, there are **90.2% contexts** given which the smallest Pythia LM (70M) has a larger next-token entropy compared to Pythia LLM (6.9B).」
- 対象は **Pythia の de-duplicated 系列(70M / 160M / 410M / 1B / 1.4B / 2.8B / 6.9B)= 事前学習のみのベースモデル**。測っているのは**次トークンのエントロピー**(意味的多様性ではない)。Figure 2 が対数モデルサイズ対エントロピー。
- 本文の説明(逐語要約): 小さい LM は理想分布を学べず多くの語に確率を散らすので一様に近く、エントロピーが高い。n-gram LM の凸性による形式的証明も付す。

**(b) Annotations Mitigate Post-Training Mode Collapse(Springer ほか・arXiv:2605.09995・ICML 2026)** **[実読・HTML v1]**

- 逐語: 「**Crucially, we find this trade-off worsens with scale.**」/「**Larger base models are not less diverse, but larger post-trained models are.**」/「This is not because base models are less diverse: **before post-training, diversity increases with model size.**」
- 出所の明示(逐語): 「Building on the **inverse-scaling effect first reported by NoveltyBench** (Zhang et al., 2025b), we reproduce and broaden the finding」。
- 実験: **Qwen2.5(0.5B/3B/14B/72B)と Llama 3(1B/3B/8B/70B)**、各サイズの公開ベースと公式 instruct を対で比較。ベンチは Stories(意味エントロピー・LLM 判定ラベル)+ NoveltyBench / WildChat / InfinityChat(Qwen3-Embedding-0.6B の平均ペア余弦非類似度)。**Figure 3 が本体で、サイズ別の数値表は本文に無い**(§3 の空欄)。
- 提案手法の数値: 「**6× less diversity collapse** than models trained with SFT」、Stories で 2.5B 版が「closes the semantic diversity gap with the base model by roughly **85%**」。
- 機構(逐語要約): 事後学習の検証 log-likelihood が高い(= 訓練分布に近い)モデルほど生成が単調。**事後学習の例数を増やすとさらに悪化する**という反直感的予測を実測で確認。

**(c) 2 本の関係 — 矛盾ではなく測っている層が違う**

| | REAL Sampling(2406.07735) | Annotations(2605.09995) |
|---|---|---|
| 対象 | **ベースのみ**(Pythia 7 サイズ) | **ベース対 instruct の対**(Qwen2.5 / Llama 3) |
| 測るもの | **次トークンのエントロピー** | **意味的エントロピー / 埋め込み非類似度** |
| 結果 | 大きいほど**下がる**(90.2% の文脈で 70M > 6.9B) | ベースは大きいほど**上がる**・instruct は大きいほど**下がる** |

**含意(8B 判断の再確認)**: 既存答申 §3-4 が「二次・未確認」として置いていた 2 文は、**一方(REAL)はベースの語レベル、もう一方(Annotations)は事後学習後の意味レベル**の話であり、**同じ「多様性」ではない**。v2 が使うのは **instruct モデルの意味的多様性**なので効くのは (b) 側=「**8B から 32B へ上げると意味的多様性はむしろ下がる**」。第155 の親判断「8B を上げる根拠なし」は**強化される**(2507.16076 の 7B > 70B と同方向)。加えて (b) は「プロンプトの工夫では埋まらない」と明言(逐語:「it does not close the gap between base and post-trained models, nor does it remove the residual inverse scaling」)=**同一性文の型を変えるだけでは上限がある**。

### ⑥ arXiv 2604.01520 の考察節 — 探していた分散比が存在した

- 出典: Wang, Li, Wu, Gao, Bo, Chen, Wen (2026) "LLM Agents as Social Scientists: A Human-AI Collaborative Platform for Social Science Automation", arXiv:2604.01520(2026-04-02)。S-Researcher / YuLan-OneSim。**[実読・HTML v1]**
- **考察節「Capabilities and boundaries of LLM simulation」の逐語**: 「LLM agents exhibit substantially lower behavioral heterogeneity than humans: **their response variability is 20–300 times smaller**, and they produce more extreme distributional patterns.」
- 続く逐語: 「research involving **behavioral heterogeneity, intention sensitivity, or distributional tails should incorporate human participants**.」/ 将来課題として「developing methods to **calibrate agent behavioral heterogeneity against known human population parameters**」。
- **根拠の所在**: 20–300 倍は**考察節にしか現れない**。裏づけの SD 表は本文に無く、対応する実験は公共財ゲーム(2×3 被験者間・条件あたり **100 エージェント × 3 反復** vs **人間 N=120・3 ラウンド**)の箱ひげ図 Fig.5 d/f と効果量 Fig.5 g のみ。効果量の逐語: β_agent=0.794 / β_human=0.491(リーダー拠出額)、β_agent=0.104 / β_human=0.251(決定機構)。マクロ整合 r=0.915。
- 規模の逐語: 「a distributed architecture supporting **up to 100,000 concurrent agents**」。
- **含意**: ① D-68 の問い「エージェントが全員同じに見える」に対する**外部からの定量的な裏書き**が初めて得られた。ただし **20–300 倍は幅が広すぎ、算出根拠が本文に無い**ので、**目標値には使えない**。使えるのは「**桁で足りていない**」という方向と「**中心傾向は合うが裾と異質性は合わない**」という切り分け。② 「分布の裾の研究には人間を入れよ」は v2 の検証設計(**裾の指標を単独ゲートにしない**)への警告として引ける。③ β の比較(エージェントは観測可能な量に過剰に寄り、意図に鈍い)は、**記憶・習慣の設計で「何を見せるか」が分散を決める**ことの実例。

### ⑦ Song 2010 の追試値 — Côte d'Ivoire 88% を本文実読。Haiti 85% は逐語引用で確認

- **Lu, Wetter, Bharti, Tatem, Bengtsson (2013) "Approaching the Limit of Predictability in Human Mobility", *Scientific Reports* 3:2923** **[実読]**
  - 標本: Orange の CDR から無作為 **500,000 人**(2011-12-01〜2012-04-28・コートジボワール)。位置は基地局の属する **sous-préfecture**(19 州・255 サブプレフェクチャ・うち 237 に基地局)。予測可能性の解析は「2 つ以上のサブプレフェクチャを訪問し 120 日超観測された **208,288 人**」。**1 日 1 点**の粒度。
  - 逐語: 「the theoretical maximum predictability is as high as **88%**」/「the average predictability increases to <Π_unc> ≈ **0.84** and <Π_max> ≈ **0.88**」/ L_i のみなら「cannot exceed **0.35**」/ S_rand の中央値 **2.0**。
  - 実アルゴリズム: MC(1)〜MC(7) の平均精度 **<γ> ≈ 0.91**、頻度のみの MC(0) は **0.85**。定常軌跡 **0.87** / 非定常 **0.95**。相関: S_real と <γ_i> が **−0.849**、Π_max と <γ_i> が **0.802**。
  - r_g 依存: 「<Π_max> stays around **0.85** for a wide range of r_g ∈ [20, 300]」= Song 2010 の「距離に依らない」を再現。ただし**訪問地点数が増えると Π は線形に下がる**(Fig.4E)。
- **Haiti 85%**: Lu 2013 本文の逐語「Lu et al analyzed a complete mobile phone dataset of **2.9 million** anonymous subscribers after the earthquake in Haiti in 2010 and found that … the predictability of people's movements remained as high as **85%**」(原典 = Lu, Bengtsson & Holme 2012 PNAS。**原典は未読**=§3)。
- **Smith, Wieser, Goulding, Barrack (2014) "A refined limit on the predictability of human mobility", IEEE PerCom, pp.88–94, doi:10.1109/PerCom.2014.6813948** **[要旨]**: 到達可能性(topological constraints)を入れると上界が下がる。抄録の逐語は「this upper bound is **between 11-24% less than previously claimed** at a spatial resolution of approx. 100m×100m」。**「81–85%」は原典の表現ではなく Cuttone et al. 2018 による要約**。著者版 PDF は取得できなかった(§3)。
- **含意**: ① **Π_max ≈ 0.93 は上限ではなく設定依存**。粒度・データ源で **0.85(Haiti)/ 0.88(CIV)/ 0.93(Song)**、制約を入れると **11–24 ポイント下**。**M5 の合格線を 0.93 に固定してはいけない**。② Lu 2013 の「**実アルゴリズムが 0.91 まで届く**(理論上界 0.88 を超えることさえある)」は、v2 の「記憶・習慣で個人内規則性を作る」に**達成可能性の下限**を与える。③ 「訪問地点数が増えると予測可能性が下がる」は **M4(1 日の訪問地点数分布)と M5(体ごとのエントロピー)が独立でない**ことを意味する=ゲートを両方置くと二重に罰する。

### ⑧ 交替制勤務の出勤時刻分布 — 出勤時刻の表は無い。時間帯編で時刻像を計算

- **無いことの確認**: 平均時刻編 67 表のうち**勤務形態を軸に持つ表は 0**(§1-① と同じ全数確認)。「出勤」を持つ 6 表の軸は 年齢 / ライフステージ / 都道府県 / 従業上の地位・雇用形態 / 世帯類型 / 育児支援 のみ。既存答申 §8-8 の記述を**全数で確定**した。
- **代理**: 同じ **時間帯編 第15-4表**(`000032224355`)の勤務形態 7 区分。**`122_始業時間などが会社の都合で決められている(交替制勤務など)`** が交替制に対応する唯一の公的軸。
- **数値(平日・雇用されている人・行動=05_仕事・行動者率 %)**:

| 時刻 | 全国 11_固定 | 全国 122_交替制 | 東京都 11_固定 | 東京都 122_交替制 |
|---|---|---|---|---|
| 00:00 | 1.83 | **8.82** | 0.59 | **8.25** |
| 03:00 | 1.60 | 7.56 | 0.34 | 6.05 |
| 06:00 | 3.85 | 12.54 | 3.91 | 12.31 |
| 09:00 | 77.39 | 47.63 | 67.19 | 39.36 |
| 12:00 | 43.31 | 39.99 | 47.13 | 42.46 |
| 18:00 | 36.04 | 36.03 | 45.76 | 46.36 |
| 22:00 | 3.55 | **12.95** | 4.93 | **19.51** |
| 最大値 | 83.28% @10:45 | **57.08% @15:45** | 83.10% @16:00 | **57.87% @16:00** |

- 再計算できる比: **深夜 0 時の仕事率は交替制が固定の 4.8 倍(全国 8.82/1.83)・東京都では 14.0 倍(8.25/0.59)**。22 時は全国 3.6 倍・東京都 4.0 倍。**朝のピークは交替制のほうが 26 ポイント低く、山が 15:45〜16:00 へ移る**。
- 始業代理の分位(§1-① の方法): 交替制は **p10 = 5:45(東京都)/ 6:00(全国)**、固定は 7:30 / 7:00。**裾が 1 時間半早い**。
- **含意**: ① 交替制 12.9%(既存答申 §2-4)は「出勤時刻が広い」のではなく「**深夜帯に別の山を持ち、朝の山が低い**」形。W17 の勤務窓に交替制を入れるなら、**時刻の分散を広げるのではなく別の型を持たせる**(22–06 の窓は既にプールの `shift_pattern` に 9,072 件ある)。② 深夜の在圏はこの層が作る。**深夜違反ゲート(0〜4 時に支度/乗車を置かない)を全体に一律で掛けると交替制の体を殺す**=第2陣の記憶・習慣設計で例外口が要る。③ 判定表としては第15-4表(東京都)を使い、投入は第31表(全国・雇用形態別)のまま=**較正と検証の分離が保てる**(第147 の分離規約と両立)。

### ⑨ 日本の PT へのモチーフ適用研究 — 2 件

- **(a) Pseudo-PFLOW(arXiv:2205.00657)** **[実読・PDF]**: 全国合成人流データ(約 1 億 3,000 万人)の作成手法。**旅客流動の検証にモチーフ解析を使用**。逐語: 「First, a **motif analysis [7] was performed** to characterize people's movement patterns.」/「The results in Figure 3 show the **differences in travel patterns by people's roles; however, there are no differences by metropolitan area**.」。対象 = **東京都市圏・近畿都市圏・東駿河都市圏**。参考文献 [7] は Schneider et al. 2013(doi 記載を確認)。**モチーフ比率の数値は Figure 3 のみで表は無い**。関連して「trip purpose の都市圏差は **1〜2%**」。
- **(b) Wang, Osaragi, Tagashira (2021) "Sequential Patterns of Daily Human Activity Extracted from Person Trip Survey Data", CUPUM 2021 / *Urban Informatics and Future Cities*, Springer, pp.257–275, doi:10.1007/978-3-030-76059-5_14** **[二次]**: Schneider 2013 を引用し PT データへ活動系列パターンを適用。**Springer 有料で本文未読**(§3)。二次情報として「限られた数のパターンが大多数を覆う」「都心からの距離と年齢でパターン構成比が変わる」。
- **含意**: ① 「日本の PT にモチーフを当てた研究は無い」ではなく**ある**。ただし **17 型の被覆率を日本で数値化した公表値は見つからない**。② Pseudo-PFLOW の「**都市圏では差が出ず、役割(属性)で差が出る**」は v2 に直接効く=**多様性は地理でなく体の属性から出るべき**。W17 が「1 つの型を地理でばらす」構図(MobiGeaR 型)を避けるという既存答申 §4 の判断と同じ方向。③ Pseudo-PFLOW は**現実整合アンカー台帳の候補**にもなる(全国合成人流・PT 由来・公開)。

### ⑩ TrajLLM の定量評価 — 存在しない

- 出典: Ju, Liu, Sinha, Xue, Salim (2025) "TrajLLM: A Modular LLM-Enhanced Agent-Based Framework for Realistic Human Trajectory Simulation", arXiv:2502.18712(2025-02-26)、**WWW 2025 Demo Paper**。**[実読・HTML v1 全文]**
- **節構成**: 1 Introduction / 2 Framework Architecture(2.1 Persona / 2.2 Activity / 2.3 Destination / 2.4 Memory)/ **3 Demonstration** / 4 Conclusion / 5 Ethical Use of Data。**実験節・結果節が無い**。
- **本文中の数値を全数抽出した結果、評価に関わる数値は 1 つも無い**(現れるのは節番号と arXiv ID と DOI のみ)。逐語: 「**Preliminary results indicate** that LLM-driven simulations align with observed real-world patterns」— 何と比べて何が一致したかは書かれていない。
- デモの規模(逐語): 「the visualization presents a sample of **one-day trajectories for ten agents in Tokyo**」。POI は「the public check-ins dataset of Tokyo」、ペルソナは「population statistics collected from local government」+ Big Five。
- 記憶モジュール(第2陣に効く): 日次→週次→月次の階層要約 + 重み付き情報密度(events / entities / actions / attributes に重み)× 新近性 × 参照頻度 を sigmoid で正規化した重要度で剪定。逐語の自己申告: 「the actual **numerical values were determined independently during development**」= **重みは根拠なし**。
- **含意**: ① §8-10 の問い「TrajLLM に個体多様性の指標があるか」の答えは**無い**。既存答申 §4 の表の「未確認」は「**評価そのものが存在しない**」に確定できる。② 既存答申 §4 の結論「LLM 人流生成の先行研究は集計分布のみで評価している」は、TrajLLM に限れば**集計分布でさえ評価していない**=より強い形で成立。**v2 が事前登録で個体指標を凍結する方法論的新規性は維持される**。③ 階層要約 + 重要度剪定は第2陣の記憶設計の**採らない道の基準線**として使える(重みが expedient であることを著者自身が書いている)。

---

## §2 設計アジェンダの候補(第2陣 3 番目=記憶・習慣。判断はユーザー)

> 以下は**候補の提示**であって決定ではない。番号は本答申内のローカル番号。

### K-1 習慣の表現 — 何を状態として持つか

| 選択肢 | 根拠 | 費用 | リスク |
|---|---|---|---|
| (a) **訪問履歴のカウンタのみ**(場所 ID → 訪問回数・最終訪問) | Schneider の自己相関 10–30 倍は「同じ形に戻る」だけで足りる。エンジン側で閉じる | 最小(バイト・呼数ともゼロ増) | LLM が履歴を見ないと行動に効かない |
| (b) **観測ブロックに「馴染みの場所」上位 k を書く**(LLM に見せる) | 2507.16076 の「個体固有の事実が効く」。⑥ の「見せたものに過剰に寄る」も同じ機構 | プロンプト長 +k 行 | ⑥ の β 比較どおり**見せた量に過剰反応**する恐れ |
| (c) **手続きグラフ**(lit `memory__lu2026_procedural-graphs` の辺に条件・助言) | 先行あり | 呼数が倍(助言呼) | D-70 の予算に当たる |
| (d) **階層要約 + 重要度剪定**(TrajLLM 型) | 先行あり | 中 | **重みが expedient(著者自身が根拠なしと明記)**=設計者の指紋 |

推奨の形(親の判断待ち): **(a) を土台に (b) を切替口で**。⑥ の警告があるので **(b) は腕として測ってから**入れる。(d) は採らない道として記録。

### K-2 日々の変動の幅 — どこを合格とするか

- 現実側の逐語アンカー(④): 「**neither totally repetitious nor totally variable**」「**two days always have some common elements**」「**more stable on work days**」。
- 数値側アンカー(③): モチーフの**自己相関は期待値の 10–30 倍**(携帯 6 か月)。
- **候補**: M6 の合格帯を「**J(1 日差)が高く γ とともに緩やかに減る**」に加えて「**同一モチーフの再出現が無作為期待の 10 倍以上**」を足す。勤務日 / 非勤務日で**別々に**測る(④ の第 3 の逐語)。
- **未決**: 複数日の下見を回すか。第161 の決定で W17 v2 は 1 日分のみ=**現状 M6 は測れない**。記憶・習慣を入れる回は**最低 2 日**が要る。

### K-3 モチーフ数 — 上限側の門番の帯をどう置くか

- 一次資料は**単一の値を与えない**(③): Schneider 17 型 / 90%(パリ・シカゴ・携帯)、シカゴ・大ボストン 16 型 / 83〜85%、シンガポール 11 型、カリフォルニア NHTS 16 型 / 83.05%(二次)。
- **候補**: M1 の帯を「**出現率 0.5% 以上の形が 11〜17 個で、累積被覆 83〜90%**」に広げる。**下限側(多様性不足)の判定には使わない**(第155 の親判断を維持)。
- **未決**: 日本の PT でこの帯が成り立つかは**公表値が無い**(⑨)。自前で PT から計算するか、帯をそのまま輸入するか。

### K-4 予測可能性の上限 — 多様性の物差しをどこに置くか

- 一次資料の幅(⑦): Π_max = **0.93(Song・基地局・1 時間刻み)/ 0.88(CIV・サブプレフェクチャ・1 日刻み)/ 0.85(Haiti)**、到達可能性制約で **11–24 ポイント下**(Smith)。
- **候補**: M5 を「**0.93 に合わせる**」ではなく「**同じ粒度で測った現実標本と突き合わせる**」に変える。v2 の粒度(セル・15 分)は Song より細かいので **Smith の警告どおり上界は下がるはず**。粒度を揃えずに 0.93 と比べると**必ず不合格になる**。
- **候補(追加)**: Lu 2013 の「**実アルゴリズムの到達点 0.87〜0.95**」を**下限側の門番**に使う(体の系列が MC(1) で 0.8 も当たらないなら、それは規則性が足りない)。
- **未決**: M4(訪問地点数)と M5(エントロピー)は**独立でない**(⑦ Fig.4E)。両方をゲートにすると二重に罰する。どちらを主にするか。

### K-5 時刻の投入 — ①②⑧ の 3 表をどう組むか

- **候補**: 投入 = 第31表(全国・雇用形態別・出勤時刻)+ **片道通勤時間は令和5年 住宅・土地統計調査 表58-2-1 の東京都分布から個体ごとに引く**(いまの一律/`arrival_lead_min` の代わり、または `arrival_lead_min` の妥当性検査として)。判定 = 第30表(東京都・出勤)+ **第15-4表(東京都・仕事の朝の階差)**。
- **効果**: 判定側の指標が 1 本から 2 本になり、`:00+:30` 率が **66〜68%** の 2 つの独立な表で挟める。
- **未決**: 第15-4表を判定に足すなら**事前登録の改版**が要る(prereg v1.3 の起票中)。

---

## §3 空欄(推測で埋めていない)

1. **Schneider 2013 Fig.3 の p(ID) の数値そのもの** — 本文になく図のみ。電子付録は royalsocietypublishing のダウンロード口が HTML を返して取得できず、PMC 側にも付録ファイルのリンクが無い。**「ID 2 → ID 1 → ID 3 → ID 4」の順位と「2 地点モチーフが約半数」(二次)までが限界**。
2. **Schlich & Axhausen 2003 の本文** — Springer 有料。ETH IVT の「Download」は DOI へ転送。**「36 通り中 平均 8.6 通り/42 日」の出所は特定できなかった**(抄録に無く、引用チェーンも辿れず)。
3. **Susilo & Axhausen(HHI による個人内反復)の本文** — ETH Research Collection が 2 回とも 429(Too Many Requests)。M6 の HHI 側の数値は未取得。
4. **Smith et al. 2014 の本文** — 著者版 PDF(大学サーバ)が本文を返さず。抄録の「11-24% less」までは取得。**「81–85%」は Cuttone et al. 2018 の要約表現**であって Smith の原典表現ではない。
5. **Lu, Bengtsson & Holme 2012 PNAS(Haiti 85%・2.9M)の原典** — PNAS が 403、PMC が reCAPTCHA。Lu 2013 本文の**逐語引用**で確認したのみ。
6. **arXiv 2605.09995 の Figure 3 のサイズ別数値** — 図のみで表が無い。**Llama 3 の 8B と 70B の意味エントロピーの具体値は未取得**(8B 判断の直接数値にはならない)。
7. **arXiv 2604.01520 の「20–300 倍」の算出根拠** — 考察節の断定のみ。対応する SD の表・補足は本文に無い。
8. **Wang, Osaragi, Tagashira (2021) CUPUM 章の本文** — Springer 有料。日本の PT でのパターン被覆率の数値は未取得。
9. **日本の PT に Schneider 定義(0.5% 閾値)を当てた 17 型の被覆率** — ⑨ の 2 件はいずれも図のみ/有料で、**公表数値が存在しない可能性が高い**。
10. **NHK 国民生活時間調査(15 分刻みの時刻別行為者率)** — ①の代替候補として名前は挙がるが、公的統計ではないため本レーンでは取得していない。

---

## §4 lit README への追加行(8 本)

| メモ | 分野 | 一次確認 | 何のために引くか |
|---|---|---|---|
| [timeuse__estat2021_timeslot-shiftwork](lit/timeuse__estat2021_timeslot-shiftwork.md) | 時間利用研究 #4 / 人口学 #1 | **実読(サブ・xlsx 取得と再計算)・親未確認** | **日本に始業時刻の分布表は無い**ことの全数確認と、唯一の代理(時間帯編 第15-4表)。**交替制の深夜率は固定の 4.8〜14.0 倍** |
| [stats__estat2023_commute-time](lit/stats__estat2023_commute-time.md) | 人口学 #1 / 交通工学 #2 | **実読(サブ・API 取得と再計算)・親未確認** | 片道通勤時間の**分布**(東京都 p50 43.7 分 / 渋谷区 33.0 分)。`arrival_lead_min` の裏づけ。社会生活基本調査は平成23年で終了 |
| [mobility__lu2013_predictability-civ](lit/mobility__lu2013_predictability-civ.md) | 人間移動科学 #3 | **実読(サブ)・親未確認** | **Π_max = 0.93 は上限でなく設定依存**(0.88 / 0.85)。**実アルゴリズムは 0.91 まで届く**=規則性の下限側の門番 |
| [mobility__pflow2022_japan-motifs](lit/mobility__pflow2022_japan-motifs.md) | 人間移動科学 #3 / GIScience #9 | **実読(サブ・PDF)・親未確認** | **日本の PT にモチーフを当てた唯一の公開実例**。「**都市圏では差が出ず役割で差が出る**」= 多様性は地理でなく属性から |
| [mobility__trajllm2025_demo-eval](lit/mobility__trajllm2025_demo-eval.md) | 人間移動科学 #3 / 自然言語処理 #27 | **実読(サブ・全文)・親未確認** | **定量評価が存在しない**ことの確定。記憶の重みが著者自身の申告で expedient = 採らない道の基準線 |
| [nlp__chang2024_real-sampling](lit/nlp__chang2024_real-sampling.md) | 自然言語処理 #27 | **実読(サブ・HTML 付録 J)・親未確認** | 「大きいほどエントロピーが低い」は**ベースの次トークン**の話(90.2% / 9M トークン)。意味的多様性とは別層 |
| [nlp__springer2026_annotation-anchoring](lit/nlp__springer2026_annotation-anchoring.md) | 自然言語処理 #27 / 人格心理学 #13 | **実読(サブ・HTML)・親未確認** | **ベースは大きいほど多様・事後学習後は大きいほど単調**(inverse scaling)。**プロンプトでは埋まらない**=8B 据置の最強の根拠 |
| [mas__wang2026_s-researcher](lit/mas__wang2026_s-researcher.md) | 計算社会科学 #25 / ABM方法論 #21 | **実読(サブ・HTML)・親未確認** | **「LLM の応答分散は人間の 20–300 倍小さい」の唯一の出所**(考察節・裏づけ表なし)。裾の研究には人間を入れよ |

---

## §5 親が最初に一次確認すべき 3 件(再現手順つき)

1. **時間帯編 第15-4表の交替制の深夜率と始業代理の分位**(§1-①/⑧)
   `data/research_cache/estat_r3_jikantai_000032224355.xlsx` → シート `a015_4`。ヘッダは 7 行目(0 起点 index 6)に `01_0:00 - 0:15` … `96_23:45 - 24:00`、値は 8 列目(index 7)以降。行キーは A〜F 列 = 曜日 / 地域区分 / 男女 / 従業上の地位 / 勤務形態 / 行動の種類。確認項目 ①(`1_平日`, `00_全国`, `0_総数`, `1_うち雇用されている人`, `122_始業時間などが会社の都合で決められている(交替制勤務など)`, `05_仕事`)の 0:00 区分 = **8.82**、同じ行の `11_始業時間が固定されている` = **1.83**(比 4.82)②東京都で 8.25 / 0.59(比 14.0)③朝の窓 04:00–12:00 の正の階差の合計と累積分位 = 東京都 交替制 p10 **5:45** / 固定 p10 **7:30**。**「勤務窓を制度で分岐しても丸みは直らない」という §2 K-1 の前提がここに乗っている**。

2. **令和5年住宅・土地統計調査 表58-2-1 の東京都/渋谷区の通勤時間分布**(§1-②)
   e-Stat API `getStatsData`・`statsDataId=0004021722`・`cdCat01=0`(男女総数)・`cdCat02=0`(所有関係総数)・`cdArea=00000,13000,13113`。確認項目 ①東京都の総数 **2,386,200** と 8 区分 + 不詳の合計が一致 ②不詳を除く母数 **2,274,500** で級内一様の線形補間 → p50 = **43.7 分** ③渋谷区の「自宅・住み込み」= **5.07%**(全国 2.20% の 2.3 倍)。**下見設計書 §2-3 のリスク 5(`arrival_lead_min` の意味が未確認)がここで部分的に消える**ので、K-5 の投入方法の判断に直結する。

3. **arXiv 2605.09995 の inverse scaling と 2406.07735 の 90.2% が「別の層の話」であること**(§1-⑤)
   前者 `arxiv.org/html/2605.09995v1` の §1 と §3 →「**Larger base models are not less diverse, but larger post-trained models are.**」「Building on the **inverse-scaling effect first reported by NoveltyBench**」、モデル系列が Qwen2.5(0.5B/3B/14B/72B)と Llama 3(1B/3B/8B/70B)であること。後者 `arxiv.org/html/2406.07735v1` の **Appendix J** →「around **9M tokens**」「**90.2% contexts**」と対象が **Pythia のベース系列**であること。**既存答申 §3-4 の二次引用 2 文は、片方がベースの次トークン・片方が事後学習後の意味であり、同じ主張ではない**。8B を上げない判断の根拠がどちらに乗っているかを親が確定する必要がある。
