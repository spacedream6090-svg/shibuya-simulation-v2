# R-63 答申: 坂・階段と歩行速度・消耗(疲労 Q37 の設計の錨)

<!-- hdr:v1 -->
- **分野**: 歩行者動力学 #18 / 運動生理学(身体活動・エネルギー) / 交通工学 #2 | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-09-30](../design/v2-wallbounce-decisions-2026-09-30.md) §1-7 坂・§4 Q37)
- **一次確認**: **B**(サブ実読。原典本文 9・抄録 3・二次 3・空欄は §8)・親検収 未
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-09-30・実行役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(PDF は OS の一時ディレクトリへ取得して pymupdf で抽出・リポに置かない)・コミットなし・台帳/設計書/src 未編集。
> 既存答申で済んでいる錨は引用だけ: 平地の自由速度 1.34 m/s・Weidmann/Kladek・Bosina & Weidmann(希望速度 1.00〜1.60 m/s)= [C9 §1.2](v2-c9-position-attention-research.md)・[R-52](v2-r52-crowd-model-calibration-shibuya-research.md)/Fruin の歩道 LOS と階段流量 18.9/20.0 人/分/ft = [R-7](v2-crowd-physics-research.md)(本書で原典を再照合・§2)/告示 1441 旧版の避難歩行速度(階段上り 27・下り 36 m/分 ほか)= R-52 §3/改訂版メッツ表(2012)と 2024 版の歩行・在店のコード = [R-46 §3](v2-r46-hunger-energy-anchors-research.md)。

## 結論(5 行)

1. **坂の速度の式は 2 本が使える**: Tobler(1993・Imhof 1950 のデータに当てた山歩きの式・式の本体は原典では図の中=式の文字列は二次)と、Wood ら 2023(英国の GPS 88,000 km・**舗装路の係数あり**)。渋谷の坂の勾配(2〜4%)では速度の低下は **Wood 舗装路で 2〜4%・Tobler で 8〜13%** と、式の選び方で差が 3 倍ある=感度腕が要る。「Pedestrian dynamics on slopes 2024」(Xie ら・Safety Science 172:106429)は**抄録だけ読めた**(本文は有料):緩い下り(3°・7°)は平地より速い・上りは勾配とともに遅い・下りの流量は平地より低い。数値は空欄。
2. **階段の速度**: Fujiyama & Tyler 2004(原典の表)で**水平成分 0.44〜0.87 m/s(ふつうの速さ・勾配 24.6〜38.8°・高齢群/若年群)**。駅の実測(山本・吉村 2014)は上りの群集で**自由時 1.0〜1.5 → 混雑で 0.5 m/s(水平成分)に収束**。流量は Fruin の階段 LOS(原典再照合)と東京メトロの設計式(階段 51 人/m・分)。
3. **消耗の単位はリポと同じ改訂版メッツ表(2012)でそろう**(原典 PDF で照合): 平地 4.0 km/h 3.0・上り坂 1〜5% 5.3・6〜15% 8.0・下り坂 3.3・階段上り ゆっくり 4.0/速い 8.8・階段下り 3.5・**立位で列に並ぶ 1.3**(エスカレーターと行列に使える)。2012 表には「階段・全般」のコードは無い(R-46 の未確認 1 件が解消)。
4. **疲労の回復の錨は弱い**: 生理の錨は心拍の回復の時定数(高齢者の 6 分間歩行の後 **τ 19±10 s・MRT 25±9 s**)=分の単位で戻る。行動の錨は「休まずに歩ける距離」の公的な分布(全国都市交通特性調査 H27: **非高齢 64%/65 歳以上 48%/75 歳以上 39% が 1.5 km 以上**・100 m までが 1/10/17%)と、国交省の道路の指針(抵抗なく歩ける距離 200〜400 m・高齢者の希望するベンチ間隔 100〜200 m)。**買い物中の休憩の頻度・時間の実測は見つからなかった(空欄)**。
5. **渋谷の坂の勾配の公表値は無い**(区の公式は由来だけ)。坂学会(非公的)の平均値: 道玄坂 570 m・高低差 13 m(≈2.3%)/宮益坂 260 m・10 m(≈3.8%)/スペイン坂 90 m・3 m(≈3.3%・下は 23 段の階段)。手元の PLATEAU の DEM(TIN)から計算できる=局所の最大勾配はその方が正しい。

## §0 出典の表

等級: **◎** 原典本文で数値まで逐語確認 / **○** 原典は読めたが一部推測(図・文字化け)を含む / **△** 抄録・二次 / **×** 未読(空欄)

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | Tobler W. 1993「Three presentations on geographical analysis and modeling」NCGIA TR 93-1 | https://escholarship.org/uc/item/05r820mz (PDF は 403)/ 本文 HTML: https://geodyssey.neocities.org/papers/tobler93 | ○ | 本文 HTML の「Non-Isotropic Geographic Modeling」節。**式は図 II の中でテキスト無し** |
| 2 | Wood A. ほか 2023「Improved prediction of hiking speeds using a data driven approach」arXiv 2303.16065v7 | https://arxiv.org/abs/2303.16065 | ◎ | PDF 全文・式(1)・表 2・表 3・Tobler 式の引用 |
| 3 | Xie W. ほか 2024「Pedestrian dynamics on slopes: Empirical analysis of level, uphill, and downhill walking」Safety Science 172:106429 | https://doi.org/10.1016/j.ssci.2024.106429 | △ | 抄録のみ(CoLab の書誌ページの抄録)。本文は有料・Unpaywall で OA なし |
| 4 | Minetti A.E. ほか 2002「Energy cost of walking and running at extreme uphill and downhill slopes」J Appl Physiol 93:1039 | https://doi.org/10.1152/japplphysiol.01177.2001 | △ | 抄録(NCBI E-utilities)。本文(5 次式の係数)は 403 で未読 |
| 5 | 国立健康・栄養研究所「改訂版 身体活動のメッツ(METs)表」2012-04-11 | https://www.nibn.go.jp/eiken/programs/2011mets.pdf | ◎ | PDF のコード 07040・17070〜17270 |
| 6 | Fujiyama T. & Tyler N. 2004「An explicit study on walking speeds of pedestrians on stairs」UCL | https://discovery.ucl.ac.uk/1243/1/2004_21.pdf | ◎ | PDF 全文・表 1〜3・表 6 |
| 7 | 山本昌和・吉村英祐 2014「駅の階段における一方向群集流動の特性の定量的把握」日本建築学会計画系論文集 79(701):1515 | https://www.jstage.jst.go.jp/article/aija/79/701/79_1515/_article/-char/ja/ | ○ | 英文抄録と数値。**和文本文はフォントの符号化で文字化け**(数値と単位のみ判読) |
| 8 | Fruin J.J. 1971「Designing for pedestrians: A level-of-service concept」HRR 355 | https://onlinepubs.trb.org/Onlinepubs/hrr/1971/355/355-001.pdf | ◎ | 階段 LOS A〜E の定義・最大流量(R-7 の親照合を本書で再照合) |
| 9 | 国交省 道路局「道路の移動円滑化整備ガイドライン」第 9 章 休憩施設 | https://www.mlit.go.jp/road/sign/data/chap9.pdf | ◎ | 全 4 頁 |
| 10 | 国交省「高齢者の生活・外出特性について」(全国都市交通特性調査 H27 の図) | https://www.mlit.go.jp/common/001176318.pdf | ◎ | 「無理なく休まずに歩ける距離」の図の数値ラベル |
| 11 | 薄井宏行・樋野公宏 2019「高齢者の歩行特性を考慮した休憩施設の密度と最長継続歩行距離」日本建築学会計画系論文集 84(762):1779 | https://www.jstage.jst.go.jp/article/aija/84/762/84_1779/_article/-char/ja/ | ○ | 英文抄録・英文要旨・表の数値。和文本文は文字化け |
| 12 | Font-Farré M. ほか 2021「Cardiac autonomic modulation response before, during, and after submaximal exercise in older adults with intellectual disability」Front Physiol 12:702418 | https://doi.org/10.3389/fphys.2021.702418 (PMC8554113) | ◎ | Europe PMC 全文 XML・抄録・表 1・方法 |
| 13 | Borg G. 1982「Psychophysical bases of perceived exertion」MSSE 14:377 | https://pubmed.ncbi.nlm.nih.gov/7154893/ | × | 検索要約のみ。本文未読 |
| 14 | 坂学会「坂のプロフィール」道玄坂・宮益坂・スペイン坂(非公的・個人) | http://www.sakagakkai.org/profile/shibuya/dogenzaka.html ほか 2 頁 | ◎(非公的) | 各頁(Shift_JIS) |
| 15 | 渋谷区「通りの名前」「地名の由来」・大山街道ニュース 2・6 | https://www.city.shibuya.tokyo.jp/bunka/bunkazai/bunkazai/street.html ほか | ◎ | 勾配の数値が**無い**ことの確認 |
| 16 | Ronchi E., Reneke P., Peacock R. 2016「A conceptual fatigue-motivation model…」Appl Math Model 40:4380 | https://doi.org/10.1016/j.apm.2015.11.040 | × | OA だが ScienceDirect が 403。検索要約のみ |
| 17 | Aghabayk K. ほか 2021 Safety Science 133:105012(勾配 0・±6・±12%・220 名) | https://doi.org/10.1016/j.ssci.2020.105012 | × | 未読(OA なし) |

## §1 坂の勾配と歩行速度

### 1-1 Tobler の式(#1・#2)
- 原典(#1)の逐語: 「I … have worked out a simple example for walking in variable terrain using the hiking function (Figure II) estimated from empirical data given by Imhof (1950, pp 217-220). In order to use this function one simply calculates the slope of the terrain, and then converts this to a walking velocity.」=**データの出所は Imhof 1950**・**式は図 II にあり本文テキストに無い**(HTML に画像の参照も無い)。
- 式の文字列は Wood ら 2023(#2)の引用で読んだ(=二次): 「W = 6 ∗exp(−3.5|S + 0.05|), where W = velocity (km/h) S = gradient of slope」「this gives a speed of 5 km/h on flat ground, with a maximum speed of 6 km/h on a mild descent (around 3 degrees)」「a factor of 0.6 is applied to the calculated speed for all off-road travel」「it predicts a sharp peak in walking speed on mild descents, which may be unrealistic」。
- 適用範囲: 山歩き(ハイキング)のデータから作った式。**都市の舗装路・買い物の歩行に作られた式ではない**。平地 5.04 km/h = 1.40 m/s は Weidmann の 1.34 に近い。

### 1-2 Wood ら 2023(#2)の舗装路の式
- 逐語: 「v = exp(a + bφ + cθ + dθ2) (1) where v = walking speed (km/h) φ = hill slope angle (degrees) θ = walking slope angle (degrees)」/表 2「Paved road 1.580 -0.00389 -0.00726 -0.00218」/「The critical gradient for this model is between 14 – 16 degrees when walking uphill and -16 – -18 degrees when walking downhill」/データ「almost 88,000 km and over 7,600 tracks across the UK, with a mean speed of 4.64 km/h」/表 3 の RMSE: 新モデル 1.10・Naismith 1.27・Tobler 1.24・Campbell 1.26(R² 0.09 / −0.22 / −0.16 / −0.19)。
- 注意: R² 0.09=**個人差が大きく、式は平均の傾向だけ**。データはハイキングの GPS(英国)で、舗装路は係数で区別しているが都市の買い物歩行ではない。

### 1-3 勾配 × 速度の表 [再計算]
坂の向きに真っすぐ歩く(φ = |θ|)と仮定した値。勾配 S = 勾配[%]/100・θ = atan(S)。

| 勾配 | 角度 | Tobler km/h(m/s) | Wood 舗装路 km/h(m/s) |
|---|---|---|---|
| −8% | −4.57° | 5.40(1.50) | 4.71(1.31) |
| −4% | −2.29° | 5.79(1.61) | 4.84(1.34) |
| −2% | −1.15° | 5.40(1.50) | 4.86(1.35) |
| 0% | 0° | 5.04(1.40) | 4.86(1.35) |
| +2.3%(道玄坂の平均) | 1.32° | 4.65(1.29) | 4.77(1.32) |
| +3.3%(スペイン坂の平均) | 1.89° | 4.49(1.25) | 4.72(1.31) |
| +3.85%(宮益坂の平均) | 2.20° | 4.40(1.22) | 4.69(1.30) |
| +6% | 3.43° | 4.08(1.13) | 4.55(1.27) |
| +8% | 4.57° | 3.81(1.06) | 4.41(1.22) |
| +12% | 6.84° | 3.31(0.92) | 4.06(1.13) |

- **フロア(式の間のばらつき)**: 渋谷の坂の範囲(+2〜4%)で平地比の低下は Tobler 7.8〜13.1%・Wood 1.7〜3.6%。2 式の差は同じ勾配で 3〜4 倍。個人差(Wood の R² 0.09)はこの差より大きい。
- Xie ら 2024(#3・抄録)逐語: 「A wide range of slope inclinations was considered, namely 0°, 3°, 7°, 12°, 17°, and 22°」「walking speeds uphill are lower than those on flat terrains, and uphill speeds decrease with increasing inclination. In contrast, increased slope inclinations do not always correspond to reduced downhill speeds. Notably, at inclinations of 3° and 7°, the downhill speed exceeds that of level walking」「the average flow rate during downhill walking is lower than those observed on flat ground and uphill terrain」。条件: 実験 48 名。**速度の数値は本文(有料)で未読=空欄**。3° = 5.2%・7° = 12.3% [再計算]。

## §2 階段の速度と流量

### 2-1 自由歩行の速度(Fujiyama & Tyler 2004・#6・表 3 水平成分 m/s)
条件: 高齢群 18 名(71±5.9 歳)・若年群 15 名(34.5±12.7 歳)・UCL 構内の 1 フライトの階段 4 種・ストップウォッチ・手すりは任意・ふつう/速いの指示。

| 階段(勾配) | ふつう上り 高齢/若年 | ふつう下り 高齢/若年 | 速い上り 高齢/若年 | 速い下り 高齢/若年 |
|---|---|---|---|---|
| 1(38.8°) | 0.44/0.48 | 0.47/0.59 | 0.61/0.78 | 0.62/0.87 |
| 2(35.0°) | 0.52/0.56 | 0.58/0.65 | 0.69/0.91 | 0.70/0.92 |
| 3(30.5°) | 0.59/0.63 | 0.64/0.74 | 0.79/0.97 | 0.84/1.08 |
| 4(24.6°) | 0.73/0.76 | 0.80/0.87 | 1.00/1.16 | 1.01/1.18 |
| 平地 | ふつう 1.31/1.40・速い 1.71/1.84 | | | |

- 逐語: 「the stair-gradient has a linear relationship with horizontal walking speeds on stairs」「No obvious relation was suggested between age and walking speeds in either group」「LEP showed a strong correlation with all speeds in Group 1」「Fruin's result was slower than ours for the elderly group. One possible reason is the difference between individual laboratory experiments and observation in actual facilities」。
- 駅の階段(蹴上げ 16〜17 cm・踏面 33〜34 cm = 約 26〜27° [再計算])は表の階段 4(24.6°)に近い。国交省のバリアフリー指針の標準は蹴上げ 16 cm 程度以下・踏面 30 cm 程度以上([R-64 §4](v2-r64-vertical-connector-values.md))。
- 年齢: 本研究では群間の差は「ふつう」で小さく(有意差なし多数)、「速い」で大きい。

### 2-2 駅の実測(山本・吉村 2014・#7)
- 英文抄録逐語: 「we conducted surveys of upward crowds on stairs in real stations」「Walking speeds are almost constant during "stable state"」。
- 本文の数値(判読できた部分): 階段の幅 1.6〜3.2 m・蹴上げ 160〜170 mm・踏面 330〜340 mm/標本 A 駅 127・153 人・B 駅 168・162 人・C 駅 461 人/「歩行速度は約 1.0〜1.5 m/sec(水平成分)の値を示し、その後…約 0.5 m/sec(水平成分)付近に収束」(先頭集団の速度の約半分)。条件: 首都圏の終端駅 3 駅・ホームとコンコースを結ぶ上りの一方向群集・降車直後。**和文は文字化けで、流動係数の値は図の中=空欄**。

### 2-3 流量(Fruin 1971・#8 原典再照合)
- 逐語: 「The maximum flow volumes of 18.9 persons per minute per foot of stair width ascending and 20.0 descending」/LOS A「20 or more sq ft per person and a volume of approximately 5 or fewer pedestrians per minute per foot width of stairway」/B「15 and 20 sq ft … 5 to 7」/C「10 to 15 sq ft … 7 to 10」/D「7 to 10 sq ft … 10 to 13」/E「4 to 7 sq ft … 13 to 17」。
- [再計算] 人/分/m: A ≤16.4・B 16.4〜23.0・C 23.0〜32.8・D 32.8〜42.7・E 42.7〜55.8。面積: A ≥1.86 m²/人(≤0.54 人/m²)・B 1.39〜1.86・C 0.93〜1.39・D 0.65〜0.93・E 0.37〜0.65 m²/人。最大 18.9/20.0 人/分/ft = 62.0/65.6 人/分/m。
- 日本の値(引用のみ・R-8/R-64): 鈴木ほか 2012 の階段上り 65.7 人/分・m(待ち行列時)・東京メトロ「駅の基本設計」の階段 51 人/m・分(R-64 §1)。
- 混雑の影響: 鈴木ほか 2012 は「待ち行列発生時は…歩行速度の差異が少ない」(R-7 の親照合)。

## §3 エネルギー消費(リポの単位 = 改訂版メッツ表 2012)

リポの `engine/energy.py` は改訂版メッツ表 2012(`mets_2012`)のコードを引く。以下は #5 の原典 PDF で照合した値(2024 版の値は R-46 §3 のサブ値)。

| 動作 | コード | 2012 METs | 原典の活動名(逐語) |
|---|---|---|---|
| 立位で列に並ぶ・エスカレーターに立つ | 07040 | **1.3** | 「立位で静かにする：列に並ぶ」 |
| 平地 3.2 km/h | 17152 | 2.8 | 「歩行：3.2km/時、ゆっくり、平らで固い地面」 |
| 平地 4.0 km/h | 17170 | 3.0 | 「歩行：4.0km/時、平らで固い地面」 |
| 平地 4.5〜5.1 km/h | 17190 | 3.5 | 「歩行：4.5-5.1km/時、ほどほどの速さ、平らで固い地面」 |
| 下り坂 4.0 km/h | 17180 | **3.3** | 「歩行：4.0km/時、下り坂」 |
| 上り坂 1〜5% | 17210 | **5.3** | 「歩行：4.7-5.6km/時、上り坂、1-5%の勾配」 |
| 上り坂 6〜15% | 17211 | **8.0** | 「歩行：4.7-5.6km/時、上り坂、6-15%の勾配」 |
| 上り坂 3%・8.0 km/h | 17235 | 9.8 | 「歩行：8.0km/時、上り坂、3%の勾配」 |
| 階段上り ゆっくり | 17133 | **4.0** | 「階段を上る：ゆっくり」 |
| 階段上り 速い | 17134 | **8.8** | 「階段を上る：速い」 |
| 階段下り | 17070 | **3.5** | 「階段を降りる」 |
| 駅・車と目的地の間の歩行 | 17161 | 2.5 | 「家から車やバスまで歩く…」(リポの `walk_dest`) |

- 注意 1: 17210/17211 は**速度 4.7〜5.6 km/h の条件**。平地の同速度(17190: 3.5)との比は 1.5 倍(1〜5%)・2.3 倍(6〜15%)[再計算]。渋谷の坂(2〜4%)は 17210 の範囲。
- 注意 2: 2012 表には「階段・全般」のコードが無い(17130 はハシゴ 8.0)。R-46 §9 の未確認「2024 版 17131 に対応する 2012 版の値」は**「無い」が答え**。
- 連続式の候補(Minetti 2002・#4・抄録): 「The minimum Cw was 1.64 +/- 0.50 J. kg(-1). m(-1) at a 1.0 +/- 0.3 m/s speed on the level. It increased on positive slopes, attained 17.33 +/- 1.11 … at +0.45, and was reduced to 0.81 +/- 0.37 … at -0.10」。条件: トレッドミル・ランナー 10 名・勾配 −0.45〜+0.45。[再計算] 1 MET = 1 kcal/kg/h = 1.162 W/kg とすると平地 1.64 J/kg/m × 1.0 m/s ≈ **1.41 MET 相当**(安静分を含むか否か=本文未読で空欄)。5 次式の係数は本文未読=空欄(検索要約に出る係数は記憶由来の可能性があり採らない)。
- 使い方の形(案・expedient): 1 tick の消費 = 既存どおり METs の表引き。坂は勾配の帯(下り/0〜1%/1〜5%/6〜15%)で 17180・17170/17190・17210・17211 を選ぶ。階段は 17133/17070。連続の勾配依存が要るときは Minetti の形(本文の係数が読めたら)。

## §4 疲労の蓄積と回復(Q37 の錨)

### 4-1 生理(分の単位で戻る)
- #12 逐語: 「During the recovery period, HR kinetics time variables showed significant better results in non-ID participants (TD: 6±5s vs. 15±11s; τ: 19±10s vs. 35±17s; and MRT: 25±9s vs. 50±11s, all p <0.050)」「At rest and recovery periods, the participants remained sited」。条件: 6 分間歩行試験の後・座位で回復・非 ID 群 24 名(60 歳以上)・HR ピーク 109 bpm(予測最大の 71%)。[再計算] 単一指数で 3τ ≈ 1 分・5τ ≈ 1.6 分=**中強度の歩行の後の心拍はおおむね 1〜2 分で戻る**。
- Fujiyama & Tyler(#6)は測定の間に「took a rest sitting on a chair for more than two minutes so that fatigue would not affect the results」=実験の手順としての 2 分(証拠ではない)。
- 自覚的運動強度(Borg RPE 6〜20・#13): 本文未読=空欄。「RPE × 10 ≈ 心拍」は二次(Wikipedia 系)で採らない。

### 4-2 行動(どれだけ歩いたら休むか)
- 全国都市交通特性調査 H27(#10・図の数値・全国 70 市): 「無理なく休まずに歩ける距離」

| 区分 | 100 m まで | 300 m | 500 m | 1 km | 1.5 km | 1.5 km 以上 |
|---|---|---|---|---|---|---|
| 非高齢 | 1% | 2% | 5% | 17% | 11% | 64% |
| 65 歳以上 | 10% | 6% | 10% | 16% | 9% | 48% |
| 75 歳以上 | 17% | 8% | 13% | 14% | 9% | 39% |

  [再計算] 各行の合計 100/99/100。三大都市圏の 1.5 km 以上: 非高齢 67%・65 歳以上 51%・75 歳以上 43%。本文逐語「無理なく休まずに歩ける距離が100ｍまでとする人が高齢者の１割、75歳以上は17％」「高齢者の歩行速度は約60～70m/分程度」。条件: 自己申告。
- 道路の移動円滑化整備ガイドライン(#9)逐語: 「高齢者が望むベンチの設置間隔は「100～200ｍ程度」が最も多く、また､都市内における通常の状況のもとで歩行者が抵抗なく歩ける距離は200～400ｍ程度といわれている」(参考文献: 三星・北川ほか 1999 土木計画学研究・論文集)。休憩施設を整備することが望ましい箇所に「商業地等の建物前面のスペース ウィンドウショッピング､小休憩､待ち合わせ等」。
- 薄井・樋野 2019(#11)英文要旨逐語: 「According to the technical advice from the government of Japan, continuous walking distance tends to range from 500 m to 700 m and the distance tends to be shortened as people get older」「65% of elderly persons are satisfied if the interval between resting places is shorter than 100 m」。本文の数値: 国交省都市局 2014「健康・医療・福祉のまちづくりの推進ガイドライン」によると平均継続歩行距離は概ね **500 m(75 歳以上)〜700 m(65〜74 歳)**(和文は文字化け・数値と括弧のみ判読)。東京駅・大手町の休憩施設の第 6 近傍距離が 100 m を超える確率 0.98。
- **買い物中の休憩の頻度・時間の実測**: 空欄(探した場所は §8)。

### 4-3 設計の錨の組み立て(案・expedient と明示)
- 収支の形(案): 疲労 F は METs の超過分(たとえば METs − 1.3)× 分を積み上げ、座位・立位の休息で指数的に戻す。**回復の時定数の錨は心拍の τ(数十秒)しか無く、主観的な疲れ・脚の疲れの時定数は空欄**。
- 休む閾値の錨: 上の「休まずに歩ける距離」の分布(年齢別)を**連続歩行の距離の閾値の分布**として使える(自己申告=照合より較正向き)。平地の歩行 3.0〜3.5 METs で 1.5 km ≈ 18〜22 分 [再計算・1.34 m/s]。
- 坂・階段の寄与: §3 の METs 比で重みづけ(上り坂 1〜5% は平地の 1.5 倍・階段上りゆっくり 4.0)。

## §5 渋谷の坂の勾配

| 坂 | 長さ | 高低差 | 平均斜度(出典の値) | [再計算] 勾配 | 出典 |
|---|---|---|---|---|---|
| 道玄坂 | 570 m | 13 m | 1.3° | 2.28% | #14(坂学会・2010 報告) |
| 宮益坂 | 260 m | 10 m | 2.2° | 3.85% | 同 |
| スペイン坂 | 90 m | 3 m | 1.9° | 3.33%(坂下は 23 段の階段) | 同 |

- 区の公式(#15)には勾配・高低差の数値は無い(由来と位置のみ)。
- 平均は局所の最大を隠す。**手元の PLATEAU 渋谷区の DEM(`udx/dem/533935_dem_6697_op.gml`・TIN 約 110 万三角形・EPSG:6697)から道の中心線に沿って勾配を計算できる**(本書では計算していない=坂の端点の座標は記憶で置かない)。

## §6 まとめ(量 × 式か値 × 条件 × 等級)

| 量 | 式か値 | 条件 | 等級 |
|---|---|---|---|
| 坂の速度 | Tobler W = 6 exp(−3.5|S+0.05|) km/h | 山歩き(Imhof 1950)・式は二次 | ○ |
| 坂の速度 | Wood 舗装路 v = exp(1.580 − 0.00389φ − 0.00726θ − 0.00218θ²) km/h | 英国 GPS・R² 0.09 | ◎ |
| 坂の速度(定性) | 緩い下り 3°・7° は平地より速い・下りの流量は低い | 実験 48 名 | △ |
| 階段の速度(自由) | 水平 0.44〜0.87 m/s(ふつう)・0.61〜1.18(速い) | 24.6〜38.8°・高齢/若年 | ◎ |
| 階段の速度(駅の群集) | 1.0〜1.5 → 0.5 m/s(水平) | 上り・終端駅 3 駅 | ○ |
| 階段の流量 | 18.9/20.0 人/分/ft・LOS A〜E | Fruin 1971 | ◎ |
| METs | 表 §3 | 改訂版 2012 | ◎ |
| 歩行の正味コスト | 平地 1.64 J/kg/m・最小 0.81(−10%) | トレッドミル | △ |
| 心拍の回復 | τ 19±10 s・MRT 25±9 s | 60 歳以上・6 分間歩行後・座位 | ◎ |
| 休まず歩ける距離 | 表 §4-2 | 自己申告・H27 | ◎ |
| 抵抗なく歩ける距離・ベンチ間隔 | 200〜400 m・100〜200 m | 国交省指針(1999 研究の引用) | ◎(二次の性格) |
| 継続歩行距離 | 500 m(75+)〜700 m(65〜74) | 国交省 2014 の技術的助言(論文経由) | ○ |
| 渋谷の坂 | 2.3〜3.9%(平均) | 非公的 | ◎(非公的) |

## §7 v2 への含意(サブの所見・採否は親とユーザー)
- **速度の式は 2 本を腕に**(既定の選択は物差しを決めてから): 差が 3〜4 倍あり、渋谷の緩い坂では個人差のほうが大きい。R-52 の照合(KDDI の宮益坂・道玄坂の通行量)は速度を直接測っていないので、坂の式の照合データは空欄。
- 疲労の単位は既存の METs に乗せられる(コードの追加は 07040・17070・17133・17134・17180・17210・17211)。
- 回復の時定数は生理(心拍)の錨しか無い=**「疲れ」の回復は expedient 宣言+感度腕**。

## §8 未確認・空欄の一覧
1. Xie ら 2024 の勾配別の速度・流量の数値(本文有料)。Nong ら 2025 Physica A 668:130589・Aghabayk ら 2021 の本文(未読・「7° が閾値」「±6% は影響小」は検索要約のみ)。
2. Tobler の式の原典の図 II(本文テキストに式が無い)。Imhof 1950 は未読。
3. Minetti 2002 の 5 次式の係数・コストが安静分を含むか(本文 403)。ACSM の歩行の式(教科書・未読)。
4. Borg RPE の本文・RPE と METs の対応。
5. 買い物・都市の歩行での休憩の頻度・時間・場所の実測(探した場所: Web 検索「shopping mall rest behavior」「pedestrian fatigue model rest」・「買い物 休憩 頻度 調査」・国交省の歩行量調査ガイドライン一覧・J-STAGE の検索結果の題名)=見つからず。
6. 疲労(主観・脚)の回復の時定数(心拍以外)。Ronchi ら 2016 の疲労—動機モデルの本文(403)。
7. 山本・吉村 2014 と薄井・樋野 2019 の和文本文(文字化け)・流動係数の値。
8. 渋谷の坂の局所の勾配(DEM から計算していない)。

## §9 ライセンス台帳と INDEX に足す行の案

**ライセンス台帳**: 本答申はデータファイルを取得していない(PDF は OS の一時ディレクトリで読んだだけ・リポに無い)=**追加行なし**。

**INDEX 行の案**:
`| 09-30 | [r63-slopes-stairs-speed-exertion](v2-r63-slopes-stairs-speed-exertion.md) | — | **B** | 歩行者動力学 #18 / 運動生理 | R-63 坂・階段と速度・消耗(Q37 の錨): 坂の式 2 本(Tobler=式は二次・Wood 2023 舗装路の係数)・渋谷の坂 2〜4% で低下 2〜13%(式で 3 倍差)・階段 0.44〜0.87 m/s(Fujiyama 2004)・駅の群集 0.5 m/s・METs 2012 の 7 コード(立位列 1.3・上り坂 5.3/8.0・階段 4.0/8.8/3.5)・回復は心拍 τ 19 s のみ・休まず歩ける距離 H27・買い物の休憩は空欄 |`
