# R-62 答申: 視野と見分けの錨 — 視野の角度・歩行中の注視の範囲・知人/見知らぬ人を見分ける距離・目の高さ・下を見る・スマホ/連れ・目的による注意・会話の距離

<!-- hdr:v1 -->
- **分野**: 知覚心理学・精神物理学 #5 / 歩行者動力学 #18 / 認知科学(記憶・習慣) #12 | **重要度**: P0([壁打ちの決定 09-30](../design/v2-wallbounce-decisions-2026-09-30.md) §1-6「知覚の個人化」の幾何と注意の錨 ・ [近接と距離の実装アジェンダ](../design/v2-proximity-distance-implementation-agenda.md) §6 B3・B4)
- **一次確認**: **B** = サブ実読(原典本文 8・抄録/要約 4・二次 4・空欄 = §9)・親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: 知覚を個人化するときの **位置・向き(視野)・目の高さと階** の幾何の値と、**注意の乗数**(既定 1.0)を錨のある要素から既定へ移すための材料。問い B4(知人出現の起床のきっかけ)に効く「知人を見分けられる距離」を含む。設計の決定はしない。
> **既存答申で済んでいる錨は引用だけ(重複させない)**: 他の歩行者を注視する距離 中央値 10.3 m(IQR 8.3-12.3・昼 13.0/夜 8.9)・注視 480 ms・TTPF の Hill 型・d50・背後 |E| > 110° を 0 = [p_notice 答申](v2-p-notice-research.md) / 歩行中の視線配分(物体・環境 37-56% > 路面 24-51% > 人 3-21%・視野に入った人を 1 回以上見る確率 0.86・人が多いほど下がる r = −0.40)= [チャネル予算答申](v2-channel-budget-attention-research.md) 問い 2 / スマホ通話で一輪車ピエロに気づく 25%(Hyman 2010)・活発な店先で停止 7 倍・頭の動き +71%(Gehl・Hillnhütter)・目的は顕著性でなく対象を変える(Wenczel)= [R-47](v2-r47-classical-choice-attention-research.md) §3 / 知人の顔は pop out しない(直列探索)= [人物知覚の検証](v2-person-perception-verification.md) 1-D / 会話の選好距離(見知らぬ人 1.35 m・知人 0.92 m・親しい人 0.32 m・Hall の二次再掲)= [C9 答申](v2-c9-position-attention-research.md) §1.5 / 2 人連れの並び幅 0.58〜0.72 m(Zanlungo 2017)= [R-52](v2-r52-crowd-model-calibration-shibuya-research.md) §6 A4。
> 規律: 子サブ未起動・Web は読むだけ(PDF・画像は OS の一時ディレクトリへ取得して抽出・リポに置かない)・コミットなし・台帳/設計書/コード未編集。

---

## 結論(5 行)

1. **視野の外周は片側約 107°(左右で約 214°)**。Strasburger ほか 2011 の「180°」は著者自身が 2024 年に「This number is wrong」と訂正した。**既存の p_notice 答申の「前方 ~200°」は 214° に直すのが正**(背後 |E| > 110° を 0 にする実装は ±107° と整合)。一方、**目そのものは ±16.8° の内に 95% の時間**(日常生活 27 人・2025)・歩行中は水平 SD 7.6°/垂直は地平線の上 10°・SD 5.3°(Foulsham 2011 の二次)= 「見える範囲」と「見ている範囲」は 1 桁違う。
2. **知人(既知の顔)を見分ける距離**: 有名人の写真を距離に相当する大きさにした実験で **75% 当たる 10.4 m(34 ft)・25% 当たる 23.5 m(77 ft)**(Loftus & Harley 2005・実験 3 本の平均)。**見知らぬ人の再認**(実人物・日中の明るさ・18-44 歳で選んだ人)は **5 m で .96・12.5 m で .58・20 m で .42**(Nyman ほか 2023)。経験則「15 m・15 lux」(Wagenaar 1996・二次)。**B4 (b) の R の候補 = 10 m(75%)・腕 5 m/20 m**(サブ案)。
3. **表情は 30〜45 m でも全員が当てた**(Hager & Ekman 1979・要約のみ)=「知人かどうか」より「表情」の方が遠くまで届く。**性別の判別距離の一次は見つからなかった**。
4. **目の高さ = 身長 −約 11〜12 cm**(AIST 1991-92: 若年男性 身長 1714.0 / 内眼角高 1596.4 mm・若年女性 1591.3 / 1476.3 mm・比 0.93)。**街路での視線は 1 階に集中**(建物の縁を見るうち 1 階が 90〜92%・通り全体では 34〜35%・シェフィールド 24 人)。**デッキ・吹き抜けから下を見る研究は見つからなかった**。
5. **目的による注意**: 空腹と食べ物への注意の偏りの相関は **r = .048(k = 98)** と小さい(渇望は r = .134・食べた量は r = .085・Hardman ほか 2021 のメタ分析)。**仕組みとして入れてよいが、乗数の値は小さく置き感度腕で**。スマホで**文字を読む**と接近する人の検出が遅れ、**音声のメッセージでは遅れない**(Silva ほか 2019・VR・33 人)。

---

## §0 出典表

等級: **◎** 原典本文で数値まで逐語確認 / **○** 原典は読めたが条件が限定(単一被験者・模擬距離・VR 等)/ **△** 抄録・検索要約・二次 / **×** 未確認。**[再計算]** はサブの計算。

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | Strasburger, Rentschler & Jüttner 2024「Corrections to: Peripheral vision and pattern recognition: A review」*J Vision* 24(4):15 | https://doi.org/10.1167/jov.24.4.15 | ◎ | PMC 本文全文 |
| 2 | Strasburger, Rentschler & Jüttner 2011「Peripheral vision and pattern recognition: A review」*J Vision* 11(5):13 | https://doi.org/10.1167/11.5.13 | ○(図 14 は 1 被験者) | 著者配布 PDF の図 14 の説明文 |
| 3 | Zheng ほか 2025「Distribution of Globe Excursions Within the Orbits Monitored by Eye Tracking Glasses in Ambulatory Subjects Engaged in Their Normal Daily Activities」*IOVS* 66(3):20 | https://doi.org/10.1167/iovs.66.3.20 | ◎(本人のデータ)/ Foulsham 2011 の再掲は △ | PMC 本文(抄録・序論・結果) |
| 4 | Loftus & Harley 2005「Why is it easier to identify someone close than far away?」*Psychon Bull Rev* 12(1):43-65 | https://doi.org/10.3758/BF03196348(著者 PDF = ワシントン大学) | ○(写真を縮めた模擬距離) | 著者 PDF 本文(「Recognizing Faces at a Distance」節) |
| 5 | Nyman, Korkman, Lampinen, Antfolk & Santtila 2023「The masked villain: the effects of facial masking, distance, lighting, and eyewitness age on eyewitness identification accuracy」*Psychol Crime Law* | https://doi.org/10.1080/1068316X.2023.2242999(CC BY・レディング大学リポジトリ) | ◎ | PDF 抄録・序論・結果 |
| 6 | Wagenaar & Van der Schrier 1996 *Psychol Crime Law* 2(4) / De Jong ほか 2005 *Psychol Crime Law* 11:87-97 | https://doi.org/10.1080/10683169608409787 | △(#5 の再掲・検索要約) | #5 序論 |
| 7 | Hager & Ekman 1979「Long-distance transmission of facial affect signals」*Ethology and Sociobiology* 1:77-82 | https://doi.org/10.1016/0162-3095(79)90007-4 | △ | 抄録(検索要約経由)。著者サイトの PDF は画像のみで抽出不能 |
| 8 | Hahn, O'Toole & Phillips 2016 *Br J Psychol* 107:117-134 / Hahn & O'Toole 2017 *NeuroImage* 146:859-868 | https://doi.org/10.1111/bjop.12125 | △ | 抄録(検索要約経由)のみ |
| 9 | 河内まき子・持丸正明 2005「AIST 人体寸法データベース 1991-92」産業技術総合研究所 | https://www.airc.aist.go.jp/dhrt/91-92/data/search2.html | ◎ | 統計表の画像 B1(身長)・B2(内眼角高) |
| 10 | Simpson, Thwaites & Freeth 2019「Understanding Visual Engagement with Urban Street Edges along Non-Pedestrianised and Pedestrianised Streets Using Mobile Eye-Tracking」*Sustainability* 11(15):4251 | https://doi.org/10.3390/su11154251(White Rose の PDF) | ◎ | PDF 本文 §2.1・§3.1・§4 |
| 11 | Silva, McFadyen ほか 2019「Phone messages affect the detection of approaching pedestrians in healthy young and older adults immersed in a virtual community environment」*PLoS ONE* 14(5):e0217062 | https://doi.org/10.1371/journal.pone.0217062 | ○(着座・VR) | PMC 本文(抄録・方法・結果) |
| 12 | Hardman ほか 2021「Food-related attentional bias and its associations with appetitive motivation and body weight: A systematic review and meta-analysis」*Appetite* 157:104986 | https://pubmed.ncbi.nlm.nih.gov/33039507/(著者稿 = White Rose) | ◎ | 著者稿 PDF 抄録・結果・考察 |

---

## §1 歩行中の有効な視野の角度・注視の範囲(問い 1)

- **視野の外周**(#1・逐語): 「We said it is about 90° of visual angle from the point of fixation. This number is wrong—the actual extent is much larger. According to the classic text by Traquair (1927), the lateral extent in each eye is around 107° of visual angle (and the horizontal extent of the entire field, from left to right, is twice that number).」 / 訂正後の本文「Peripheral vision would then occur within the area from 60° (i.e., ±30°) up to around 214° horizontal diameter.」
  - **既存答申との差**: [p_notice 答申](v2-p-notice-research.md) の「人間の水平視野は物理的に前方 ~200°(両眼)止まり」は **~214°(±107°)に訂正が要る**。「背後 |E| > 110° を 0」はこの値と整合(**訂正の伝播検査の対象**)。
- **見分けられる範囲(文字の再認)**(#2 図 14 の説明): 「The 100%-contrast ellipse represents a maximum field of recognition obtained by extrapolation; its diameter is 46°×32°.」= **検出(±107°)と再認(直径 46° × 32°)は別の範囲**。条件 = 「for one subject (CH)」・文字の再認・外挿 = ○。
- **目の向き(日常生活)**(#3・逐語): 「horizontal gaze angle remains within ±16.8° of primary gaze 95% of the time」/「mean vertical gaze position is shifted downward (−5.19°)」/「the standard deviation of vertical eye position (11.63°) was greater than that of horizonal eye position (8.41°)」/「less than 1% of eye positions were recorded more than 25° from primary gaze」。条件 = 「Twenty-seven normal subjects with a mean age of 23.6 years (range, 4–68 years)」「328 min/person」・頭の動きは測っていない(目の中の位置)。
- **歩行中(Foulsham 2011 の再掲・#3 序論 = △)**: 「Foulsham et al. recorded horizontal and vertical eye positions in 14 subjects wearing an eye tracker while walking around a university campus. Horizontal gaze position was normally distributed around primary orbital position, with a standard deviation of 7.6°. Vertical gaze position was centered 10° above the horizon, with a standard deviation of only 5.3°. … Gaze angle deviated beyond 15° only about 5% of the time.」
- **頭が回り始める角度**(#3 序論が Stahl を引用 = △): 「if horizontal saccades from primary gaze are less than 20°, there is generally little head movement. Gaze shifts beyond ±20°, however, are accompanied by increasing head swivel.」
- **中心視と周辺視で何が見えるか**: 検出は周辺まで(±107°)・文字の再認は直径 46° × 32° まで(#2)・顔の注視は他人に 10.3 m で 480 ms(既存)。**歩行中の「有効視野(UFOV)」の角度を歩行者で測った一次は本調査で当たっていない = 空欄**。

## §2 看板・店頭・他人に気づく距離と角度(問い 2)

- 既存で足りている: 他人を注視する距離(Fotios 2015)・距離→検出の Hill 型(TTPF)・背後 0・視線配分・視野に入った人を見る確率 0.86(上の既存答申)・大型ビジョン VR 視認率 70.3%(チャネル予算答申)。
- **足りない部分(本調査で埋めたもの)**: **縦方向**。#10 Simpson 2019「90%–92% of people's visual engagement takes place with the ground floor of street edges. However, ground floor engagement was shown to be less, at 34%–35%, when taking into account visual engagement with the entirety of the whole street.」/ 表 1 表題「The amount of visual engagement with street edge ground and upper floors」。条件 = 「24 adult study participants (n = 12 female; n = 12 male) with a mean age of 35 years」・シェフィールド中心部・歩行者専用と一般の街路・目的つき/任意の活動。= **2 階以上の看板は 1 階の約 1/10 しか見られない**(縁を見るうちの割合として・[再計算] 8〜10% / 90〜92%)。
- **看板に気づく角度の一次**: 本調査では当たっていない = 空欄(既存の顕著性・d50 で扱う)。

## §3 知人を見分けられる距離・見知らぬ人の表情/性別・混雑の中の探索(問い 3)

### 3-1 知っている顔(有名人)

- **#4 Loftus & Harley 2005**: 「Celebrity identification provides a good paradigm for investigating the ability to identify people who are known to the observer.」/「Averaged across the three experiments the 25% and 75% identification-level distances, D, were 77 and 34 feet」= **75% = 34 ft(10.4 m)・25% = 77 ft(23.5 m)**[再計算: 1 ft = 0.3048 m]。
  - 条件: 写真を「shrinking」で模擬距離にした画面実験(実験 2〜4 の比較できる条件の平均)・有名人の顔のみ(体・歩き方・服なし)・時間制限なし = ○。
  - 事前知識の効果: 「Primed celebrities could be recognized at a point that was 24.5%±6.4% smaller and 22.8%±11.8% more blurred than unprimed celebrities」= **来ると分かっている相手は約 1/4 遠くから見分けられる**(待ち合わせの相手に当たる)。
- **#8 Hahn 2016 / Hahn & O'Toole 2017**(抄録のみ・△): 近づいてくる人の再認は顔・体・動きの順に効き、参加者は「meta-knowledge of the optimal proximity for recognition from faces versus bodies」を持つ。2017 の刺激は検索要約で「approaching from about 13 m」(二次)。**距離別の正答率は取れていない**。
- **歩き方・服装**: 一次は本調査で当たっていない(Cutting & Kozlowski 1977・Burton 1999 は書誌のみ)= 空欄。

### 3-2 見知らぬ人(目撃者の再認)

- **#5 Nyman 2023**(実人物を約 20 秒見る → 8 人の写真から選ぶ・屋内の 22 m の走路・約 300 lux と約 2 lux): 抄録「TP identification accuracy, with no facial masking, for all participants was .69 (.96 for only 18-44-year-old choosers) at 5m, .34 (.58) at 12.5m, and .17 (.42) at 20m. TA rejection accuracy for all participants was .63 (.60 for only 18-44-year-olds) at 5m, .42 (.54) at 12.5m, and .46 (.46) at 20m.」 条件 = 「N = 1325 … Age range: 5–90」。偶然の水準 = 「(i.e., .125)」。
- **#5 の序論の再掲(△)**: Wagenaar & Van der Schrier 1996「lighting should be above 15 lux and distance below 15 m to achieve a diagnostic value of 15」/ Lockamyeir 2020「target present identification accuracy fell in Experiment 1 from .50 at 3 m to .15 at 20 m」/ Nyman, Antfolk 2019「accuracy reached chance level (i.e. .125) at 20 meters in low lighting」。
- **フロア**: 同じ 20 m・明るい条件でも、全年齢 .17・18-44 歳で選んだ人 .42(#5)= 母集団と「選んだ人だけか」で 2.5 倍動く。

### 3-3 表情・性別

- **#7 Hager & Ekman 1979**(要約のみ・△): 6 つの感情の表情を「30, 35, 40, and 45 meters」の 4 群(49 人)が判定し、「Every observer was able to label the expressions accurately although accuracy declined as distance increased」。
- **性別の判別距離**: 一次は見つからなかった = 空欄。

### 3-4 混雑の中の探索

- 既存: 知人の顔は pop out しない(直列探索・[人物知覚の検証](v2-person-perception-verification.md) 1-D)・1 回の注視で走査できる人数は 10 人前後が上限(p_notice 答申の独自導出)。**本調査で追加の一次は無し**。

## §4 目の高さ・下を見たときの見え方(問い 4)

- **#9 AIST 1991-92**(統計表の画像を読んだ・mm):

| 群 | 人数 | 身長 平均(SD) | 内眼角高 平均(SD) | 差 [再計算] | 比 [再計算] |
|---|---:|---:|---:|---:|---:|
| 若年 男(18-29) | 217 | 1714.0(62.55) | 1596.4(61.04) | 117.6 | 0.931 |
| 若年 女 | 203 / 202 | 1591.3(53.03) | 1476.3(51.38) | 115.0 | 0.928 |
| 高齢 男(60+) | 46 | 1589.0(41.96) | 1476.1(40.79) | 112.9 | 0.929 |
| 高齢 女 | 49 / 48 | 1467.8(53.63) | 1362.5(54.40) | 105.3 | 0.928 |

  - 定義(表の注記): 身長「床面から頭頂点までの高さ」・内眼角高「床面から内眼角点までの高さ」・姿勢「立位…耳眼面水平」。**計測は 1991-92 年**。**現行の身長分布**は国民健康・栄養調査(厚労省)で取れるが本調査では取得していない = 空欄。「目の高さ = 身長 × 0.93」を当てるのはサブ案(未リサーチ)。
- **下を見る**: 日常生活の目の垂直位置は平均 −5.19°・SD 11.63°(#3)。**デッキ・吹き抜けから下の通りを見る研究は見つからなかった = 空欄**。[再計算] デッキ高 6 m から水平距離 20 m の歩道を見る俯角 = atan(6/20) ≈ 16.7° = #3 の分布の約 1 SD 下。**「下の通りは見える範囲に入るが、見ている範囲の中心からは外れる」**(サブの読み)。
- **階の影響**: 1 階の縁に 90〜92%(#10)= 上の階の人・看板は地上から見られにくい。

## §5 スマホ・会話・連れで視野が狭まる(問い 5)

- 既存(重複しない): Hyman 2010(通話で気づく 25%)・駅構内でスマホを使う 55.5%(jeki・R-47)・待機者の 8 割超がスマホ(一宮・松村 2026)。
- **#11 Silva 2019**(新規): 「Findings indicate that text messages prolong the detection of approaching pedestrians」/「In both groups, audio messages yielded no difference in obstacle detection time or accuracy of message report compared to the no message condition」/「central approaching obstacles led to faster ODT across all tested conditions compared to diagonal approaches」。条件 = 「Eighteen healthy young (24 ± 2.9 years) and 15 older adults (68 ± 4.2 years)」・着座で HMD の地下鉄駅・歩行者は 0° と ±40° から接近 = ○。
  - 含意(サブの読み): **「画面を読む」と「話す(音声)」は別の乗数にする**のが先行と整合。Hyman(通話で見落とし)と Silva(音声で検出は遅れない)は課題が違う(見落とし vs 接近の検出)ので、**通話の乗数は腕で幅を持つ**。
  - **正面より斜め(±40°)の検出が遅い** = 視野の中心からの角度で検出を下げる根拠(乗数の値は無い)。
- **連れがいるときの視野**: 一次は本調査で当たっていない = 空欄(2 人連れの並び幅・速度は R-52)。

## §6 目的による注意(空腹なら飲食店が目に入る)(問い 6)

- **#12 Hardman 2021**(逐語・抄録): 「Food-related AB was robustly associated with craving (r = .134 (95% CI .061, .208); p < .001), food intake (r = .085 (95% CI .038, .132); p < .001), and hunger (r = .048 (95% CI .016, .079); p = .003), but these correlations were small」/ 結果「Attentional bias predicted < 1% of variance in hunger (r2 = .002)」/ 考察「In many of the included studies, participants were fasted for a few hours or overnight, and more extensive periods of food restriction may be needed to promote larger differences in AB」。条件 = 実験室の注意課題(ドット・プローブ・視線計測等)のメタ分析・k = 98(空腹)。
- **反対・再現**: 「No effect of hunger on attentional capture by food cues: Two replication studies」(Appetite 2023・題名のみ = △)。
- 既存(R-47): 目的は顕著性でなく「何を見るか」を変える(Wenczel 2017・抄録)・広告の情報価値は目的に依存(Pieters & Wedel 2007・要約)。
- **街路で「空腹だと飲食店に気づく率が何倍か」を測った一次は見つからなかった = 空欄**。
- 含意(サブの読み): ユーザー決定の「目的による注意は仕組みとして先に入れる(値は宣言+感度腕)」と整合。**実験室の効果は小さい(r ≈ .05)ので、既定の乗数は 1.0 に近い値(例 1.1)で置き、腕で 1.0/1.5**(値は expedient)。渇望(r = .134)の方が空腹(r = .048)より強い = 「食べたい物がある」状態の方が効く。

## §7 会話の距離(1 m・2 m・2.5 m)の錨(1 行)

- 既存のみで足りる: **見知らぬ人 1.35 m・知人 0.92 m・親しい人 0.32 m**(Sorokowska 2017・42 か国 8,943 人・回答尺度の上限 220 cm・日本は含まれない)・Hall の社会距離 122-210 cm(二次再掲・原典未取得)= [C9 答申](v2-c9-position-attention-research.md) §1.5。歩きながらの 2 人連れの並び幅 0.58〜0.72 m(Zanlungo 2017・大阪)= [R-52](v2-r52-crowd-model-calibration-shibuya-research.md) §6 A4。**屋外・群衆での会話距離の実測は依然なし**。→ B3 の 2 m は「知人 0.92・見知らぬ人 1.35・社会距離の上端 2.1」を覆う側、1 m は知人の選好に近い側、2.5 m は Hall の二次再掲の社会距離(〜2.1 m)より外。

## §8 まとめ表(要素 × 錨の有無 × 値 × 条件)

| 要素 | 錨 | 値 | 条件 | 既定への扱い(サブ案・未リサーチ) |
|---|---|---|---|---|
| 視野の外周(水平) | **あり(一次)** | ±107°(全幅 ~214°) | Traquair 1927 を著者が訂正で引用 | 幾何の外枠に使う。既存「~200°」を訂正 |
| 見分けの範囲(再認) | あり(1 被験者) | 直径 46° × 32° | 文字・外挿 | 「気づく」と「見分ける」を分ける根拠。値は腕 |
| 目の向き(注視の範囲) | **あり(一次)** | 水平 95% が ±16.8°・垂直 平均 −5.19°(SD 11.63°) | 日常生活 27 人 | 向きのばらつきの分布に使える |
| 歩行中の注視 | 二次 | 水平 SD 7.6°・垂直 +10°(SD 5.3°) | 大学構内 14 人 | 同上(二次) |
| 頭が回る閾 | 二次 | ±20° を超えると頭も回る | 実験室 | 参考 |
| 他人に気づく距離 | 既存 | 中央値 10.3 m | Fotios 2015 | 既存どおり |
| **知人を見分ける距離** | **あり(模擬距離)** | 75% = 10.4 m・25% = 23.5 m・来ると分かっていると約 1/4 遠く | 有名人の写真を縮小 | **B4 (b) の R 候補 = 10 m・腕 5/20 m** |
| 見知らぬ人の再認 | **あり(一次・実人物)** | 5 m .96 → 12.5 m .58 → 20 m .42(18-44 歳・明るい) | 屋内走路・N = 1,325 | 「同じ人だと分かる」の減衰の形に使える |
| 表情 | 要約のみ | 30〜45 m で全員が判定 | 49 人 | 腕 |
| 性別 | なし | 空欄 | — | 空欄 |
| 目の高さ | **あり(一次)** | 身長 −105〜118 mm(比 0.93) | AIST 1991-92 | 身長 × 0.93(身長分布は別途) |
| 上の階を見る | **あり(一次)** | 縁を見るうち 1 階 90〜92% | シェフィールド 24 人 | 2 階以上の看板・人の顕著性を下げる根拠 |
| デッキから下を見る | なし | 空欄 | — | 幾何だけ(視線を通す)・乗数 1.0 |
| スマホ(文字) | 既存+新規 | 気づく 25%(Hyman)・接近の検出が遅れる | 大学広場 / VR | 既存の m_load |
| 音声・通話 | 割れる | 見落とし(Hyman)/ 検出は遅れない(Silva) | 課題が違う | 腕で幅 |
| 連れ | なし | 空欄 | — | 1.0+腕 |
| 目的による注意(空腹) | **あり(メタ分析)** | r = .048(渇望 r = .134) | 実験室・k = 98 | 仕組みは入れる・乗数は小さく(例 1.1)・腕 1.0/1.5 |
| 会話の距離 | 既存 | 0.92 / 1.35 m・社会距離 〜2.1 m | 42 か国(日本なし) | B3 の 2 m を支持 |

---

## §9 未確認・空欄の一覧

1. 視野の上下の外周(度)。NCBI Bookshelf の臨床の章がボット対策で読めず = 空欄。
2. 歩行者の有効視野(UFOV)の角度。
3. Foulsham 2011 の原典(本書の値は #3 の再掲 = 二次)。
4. 知人を見分ける距離の **実人物・屋外** の一次(#4 は模擬距離・#8 は抄録のみ)。
5. 歩き方・服装で見分ける距離。
6. 性別の判別距離。
7. Hager & Ekman 1979 の距離別の正答率(PDF が画像のみ)。
8. Wagenaar 1996・De Jong 2005 の本文(有料)。
9. 現行の日本人の身長分布(国民健康・栄養調査は未取得)。
10. デッキ・吹き抜けから下を見る研究。
11. 連れ・会話中の視野の狭まり。
12. 街路で目的(空腹)が気づきを変える倍率。
13. 看板に気づく角度の一次。

## §10 INDEX に足す行の案(**本書では追記しない** — 親が入れる)

```
| 09-30 | [r62-field-of-view-anchors](v2-r62-field-of-view-anchors.md) | ~200 | **B** | 知覚心理学・精神物理学 #5 / 歩行者動力学 #18 | 視野と見分けの錨(§1-6・B4): 視野の外周 ±107°(Strasburger 2024 の訂正 = 既存の ~200° を直す)・目は ±16.8° に 95%・知人(有名人)75% = 10.4 m/25% = 23.5 m(Loftus & Harley 2005)・見知らぬ人 5 m .96→20 m .42(Nyman 2023)・目の高さ = 身長 −11〜12 cm(AIST)・1 階に 90〜92%(Simpson 2019)・空腹と注意 r = .048(Hardman 2021)・文字は検出を遅らせ音声は遅らせない(Silva 2019) |
```
