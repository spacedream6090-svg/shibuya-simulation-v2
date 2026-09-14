# 答申: 街の広告・看板は現実にどれほど意思決定に効くか+情報はどう伝播するか

<!-- hdr:v1 -->
- **分野**: 行動経済学・マーケティング科学 #16 / 社会ネットワーク科学 #14 | **重要度**: P0(親判断・2026-09-15 第191)
- **一次確認**: **C** = 出典あり・空欄は未整理 — 出典痕跡 143 件。空欄節なし(=無いのか未整理なのか未判定)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 起草: 2026-09-02 / リサーチレーン(Webのみ・リポ書き込みなし)
> 対象決定: R3-3(看板=スマートオブジェクトのテキスト属性・(a)店舗看板から開始・将来(c)拡張)・U5(スマートオブジェクト)・C1(情報カスケード=強5本)・R17(倫理)・収益化方針
> 規律: 支持と反証を両方載せ、どちらが強いかを明示。商業数値は「公開情報の範囲」と明記。見つからなかったものは§6に書いた。

---

## ① 結論(10行以内)

1. **広告は効く。ただし効果量は「驚くほど小さい」側の証拠が明確に強い**——因果デザインが厳密になるほど効果は小さくなる、という一方向の系統的パターンがある(観測法 > RCT > 大規模メタ分析)。
2. OOH固有の唯一の因果研究(スイス・タバコ屋外広告禁止のDiD)は、**カテゴリー全体の屋外広告を消しても喫煙率−0.4〜−0.9pp(相対約3%)**。「特別に効く媒体」という業界主張の裏づけはない。
3. TV広告の長期売上弾力性は**中央値0.014・平均0.025**(288ブランド)、2/3超が統計的にゼロと区別できず、限界ROIは中央ブランドで**−79%**。
4. 現実の広告1接触あたりの行動変化確率は **10⁻⁴〜10⁻³ のオーダー**。RCTでさえROI信頼区間が100pp超で、R²は10⁻⁵台。
5. 情報伝播の第一事実は「**伝播しない**」——平均カスケードサイズ1.14・中央値1(Twitter 74M件)、99%超が1世代で終了(10億件)。C1は既にこれを掴んでいる。
6. **最大の技術リスクは実証済み**: LLMエージェントは同一の選択課題で人間の**3〜10倍以上**ナッジに反応する(人間9.9pp対エージェント10〜60pp・17モデル)。無対策なら広告効果を桁で過大に出す。
7. 対策は「注意ゲート」の4段直列(幾何→視認確率→注視時間によるテキスト長キャップ→効果キャップ)と、**既定は非注入・スカラー変換を第一候補**にすること。
8. 台帳には**「効かないことを照合する」行(AD1)を新設**すべき。広告ablationで街路プロファイル・消費・カスケードが動かないことを示すのが、製品信頼性の唯一の証明形。
9. 収益化の差別化は「効果が大きいと言う」ではなく「**効果が小さいことを含めて正しく言う**」。反実仮想を持つことが attribution ベンダーへの唯一の技術的優位。
10. 倫理境界は移入禁止リストの筆頭と同型: 顧客が触れてよいのは**世界の入力(看板)**であって、**エージェントの目的関数**ではない。

---

## ② ユーザーがまず読む大枠(平易)

街の看板は「効く」のですが、効き方は皆さんの直感よりはるかに小さいです。スイスで州ごとにタバコの屋外広告を全面禁止していった自然実験を厳密に分析すると、**カテゴリーの屋外広告を丸ごと消しても喫煙率は1ポイントも下がりません**(相対で3%程度)。テレビ広告に至っては、288ブランドを調べた研究で「広告を倍にしても売上は1.4%しか動かず、3分の2のブランドでは統計的にゼロと区別できない」という結果です。

一方、情報の伝播も「広がらない」のが第一事実です。ツイートの平均転送数は1.14回、半分以上は誰にも転送されません。渋谷の看板を見た人が友達に話し、それがSNSで拡散して……という連鎖は、ほとんどの場合1歩目で止まります。

そして最大の問題は**LLMの側**にあります。同じ買い物課題で、人間は「ベストセラー」「専門家おすすめ」といった煽り文句にほとんど動かない(9.9ポイント・統計的にぎりぎり)のに、LLMエージェントは10〜60ポイント動きます。**3〜10倍以上の過剰反応**が17モデルで実測されています。看板の文章をそのままプロンプトに入れれば、現実の100倍〜1000倍の広告効果が出てしまう。これを放置したまま「広告効果を測れます」と売ると、顧客が実測と突き合わせた瞬間に信用を失います。

だから本答申の提案は「広告を実装する」ではなく「**広告が効きすぎないための装置を先に実装する**」です。そして台帳には「効かないこと」を照合する行を入れます。効果が小さいことを小さいまま再現できたとき初めて、この世界は広告効果測定の道具として売れます。

---

## ③ 方面別の証拠

### 方面1: OOH/DOOH産業の計測実務

#### 1-1. 海外の標準指標

**Geopath(米・OOH計測の業界標準)**: 車両カウント・歩行者カウント・交通機関乗降を基礎に **DEC(Daily Effective Circulation)** を作り、そこへ **VAC(Visibility Adjustment Criteria)** ——媒体サイズ・角度・道路からの距離・競合看板——を掛けた **VAI(Visibility Adjustment Index)** で日次インプレッションを出す。スマホ位置データを重ねて時間帯・曜日・季節変動と属性を補完する。国際的には **VAC = Visibility Adjusted Contact**、米Geopathでは "audience impression" / "Likelihood-to-See (LTS) impression" と呼ぶ。
- https://support.geopath.io/hc/en-us/articles/360006652652-Geopath-Research-Methodology-Measuring-Out-of-Home-Audiences
- https://geopath.org/wp-content/uploads/2019/09/Geopath-Standards-and-Best-Practices-Document__9-17-19.pdf

**Route(英・OOH計測の業界標準)**: GPS パッシブ位置追跡+ボリューメトリックカウント+視線計測のハイブリッド。**OTS(見る機会)ではなく LTS(実際に見る尤度)を通貨にしている**点が重要。媒体の90%以上が見える範囲を通過する交通量を基礎に、実際に見る確率で調整する。
公開されている計算構造(v2の可視性計算に直接移植可能):
- **0.1秒ごとの momentary hit rate** を可視エリア内の露出時間について積算
- 可視コーンは媒体の**左右各120度**
- **動的コンテンツ係数 = 16.8m²超で1.5倍・それ以下で1.2倍**
- 歩行者速度を **walking (>1.85 mph) / wending (0.2–1.85 mph) / waiting (<0.2 mph)** の3区分
- 交通手段・媒体種別で変わる定数 k を用いるが **k の値・結果のLTS確率は非公開**
- https://www.route.org.uk/attention.php
- https://www.route.org.uk/methodology.php

#### 1-2. 日本のDOOH視聴質指標

**LIVE BOARD(NTTドコモ系)**: デジタルサイネージコンソーシアムのガイドラインに準拠して VAC を算出。3方式が公開されている。
- 方式A(5段階): ①媒体サイズと遮蔽物から視認エリアを定義 → ②モバイル空間統計®で通行量推定 → ③ロケーション特性から視認可能者数 → ④**ロケーション別視認率**で実視認者数 → ⑤性年代属性を付与
- 方式B: AIカメラ/センサーで通行者の向きを検出し、視認エリア内で媒体方向を向いている人数を実測
- 方式C: 交通量調査+モバイル空間統計ベースの推定モデル(センサー設置不可の場所)
- **具体的な視認率の数値・計算式は非公開**
- https://liveboard.co.jp/impression/

**電通×NTTドコモ×LIVE BOARD(2025-10-16 発表)**: DOOHの指標(インプレッション/リーチ/フリークエンシー)を**アナログOOHへ応用**する日本初の取り組み。ドコモ約1億会員基盤の「モバイル空間統計®」+「docomo Sense®」を使用。2024-10-01〜2025-07-31、全国180路線超・900媒体超で試行(サントリー事例)。インパクト側は18地域の視認者調査+65媒体を掲出サイズ・位置・通過時間など7次元でスコアリング。
- https://www.dentsu.co.jp/news/release/2025/1016-010954.html

**市場規模(電通「2025年 日本の広告費」・2026-03-05発表)**: 総広告費8兆623億円(前年比105.1%)。うち**屋外広告3,042億円(105.3%)+交通広告1,736億円(108.6%)= OOH約4,778億円**。「屋外ビジョンは引き続き渋谷・表参道など都市部繁華街の引き合いが活況」と明記。
- https://www.dentsu.co.jp/news/release/2026/0305-011003.html

#### 1-3. 位置データによるOOH効果計測 = D4′と同じデータ産業(重要な確認)

**KDDI Location Analyzer は、日本のOOH効果測定の主力ツールの一つ**である。
- jeki(ジェイアール東日本企画)との「ターゲティング配信 powered by KDDI」= OOH/DOOHの効果の見える化と取引自動化を掲げる: https://k-locationanalyzer.com/jeki
- MCDecaux 事例「GPS位置情報の活用で、屋外広告を設置する前後のロケーションの価値を評価」: https://k-locationanalyzer.com/case/mcdecaux
- 競合として ジオテクノロジーズ「OOH広告効果測定サービス」(https://business.mapfan.com/service/advertising-effectiveness-measurement/)、Location AI(https://location-ai.com/solutions/jinryu-ooh-analytics/)、OOH-ATLAS(https://ooh-atlas.com/)

**含意**: 台帳D4′(3街路の日内プロファイル分化)の原データは渋谷区オープンデータ経由のKDDI Location Analyzer である。つまり **v2 が忠実度照合に使うデータと、広告主が効果測定に使うデータが同一系列**。「同じ計器で現実とシミュを測る」が成立する — これは製品としての決定的な強み(§5)。

#### 1-4. 渋谷スクランブル交差点の大型ビジョン(公開情報の範囲)

| 項目 | 公開値 | 出典 |
|---|---|---|
| スクランブル交差点通行者 | 「1日最大約50万人が通行数と言われている」 | https://space-media.jp/feature/detail/78/ |
| 109フォーラムビジョン 立地 | 渋谷区渋谷1-23-10・スクランブル交差点に面する。「1日30万人以上の通行があるスクランブル交差点に面した媒体」 | https://ooh-portal.jp/property/109フォーラムビジョン |
| 同 サイズ | H4.80 × W8.64 m(41.472㎡)・16:9・LED・音声あり | 同上 |
| 同 稼働 | 9:00〜24:00 | 同上 |
| 同 料金(税別・公開情報の範囲) | 15秒×4回/時: 1日 ¥550,000 / 7日 ¥1,100,000 / 14日 ¥2,024,000 / 30日 ¥3,630,000。15秒×8回/時なら7日 ¥2,200,000 | 同上 |
| 同(別代理店表示) | 15秒×4回/時・7日 ¥1,000,000(税別) | https://shunkosha.co.jp/dooh-053 |
| ハチ公口の連動 | スクランブル交差点を囲むように大型ビジョン6基・うち5基連動放映が中心手法 | https://space-media.jp/feature/detail/78/ |

**重要な発見(反証側)**: 渋谷の主要ビジョンについて、**第三者機関によるオーディエンス計測値(VAC相当)は公開されていない**。掲載されているのは交差点の通行量であって視認者数ではない。ooh-portal・春光社いずれも「独立したオーディエンス計測の出典は掲載なし」。二次情報として「視認範囲内歩行者 平日31.0万人/日・休日42.0万人/日」という数値が検索結果に現れたが、一次ページで裏を取れなかった(§6-1)。

---

### 方面2: 広告効果の効果量の桁 ★最重要

#### 2-1. 測定そのものが困難であるという一次結果

**Lewis & Rao (2015) "The Unfavorable Economics of Measuring the Returns to Advertising", QJE 130(4):1941–1973** — 主要米小売19社・証券6社の**25本の大規模RCT**、総額$2.8M、各実験50万人超(大半100万人超)。本文から直接引用した数値:
- 「The median standard error on ROI for the retail experiments is 26.1%」→ **ROI信頼区間は100パーセントポイント超の幅**。証券系は中央値SE 115%。
- 「The standard deviation of individual-level sales is typically **10 times the mean**」(変動係数10)
- **+25%ROIを得るのに必要な因果効果は「1人あたり売上を$0.35上げる」だけ**。これは平均$7・標準偏差$75の変数に対する$0.35。→ **R² = ¼×($0.35/$75)² ≒ 0.0000054**
- 「+50%ROI(大儲け)と0%ROI(トントン)を確実に識別するには中央値キャンペーンを**9倍**、10%ROI差なら**62倍**にする必要」
- 「informative advertising experiments can easily require more than **10 million person-weeks**」
- https://academic.oup.com/qje/article-abstract/130/4/1941/1914592 / 本文PDF: https://gwern.net/doc/economics/advertising/2015-lewis.pdf

これは「効果が小さい」という主張の**最も強い一次証拠**である。R²が10⁻⁵台ということは、広告は個人の購買変動のほぼ全てを説明しない。

#### 2-2. 大規模フィールド実験の古典と現代

| 研究 | 設計・規模 | 結果 |
|---|---|---|
| **Lodish et al. (1995) JMR 32(2)** "How T.V. Advertising Works: A Meta-Analysis of 389 Real World Split Cable T.V. Advertising Experiments" | BehaviorScan 世帯マッチ・split cable の実世界実験 **389本** | **半数超が売上に有意差なし**。ゼロ出稿テストで「TV広告を止めても1年以内に売上が動かない確率は50/50」 |
| **Blake, Nosko & Tadelis (2015) Econometrica 83(1):155–174** | eBay の検索連動広告の大規模フィールド実験 | **ブランドキーワード広告に測定可能な短期便益なし**。非ブランドでは新規・低頻度ユーザーのみ反応し、支出の大半を占める高頻度ユーザーは反応しない → **平均リターンは負**。従来の非実験推定は実際の何倍も過大 |
| **Gordon, Zettelmeyer, Bhargava & Chapsky (2019) Marketing Science 38(2)** | Facebook 15実験・5億ユーザー実験観測・16億インプレッション | 観測法(傾向スコア等)は**概してRCTより効果を過大評価**。業界で普通に手に入るデータでは因果効果を復元できない |
| **Shapiro, Hitsch & Tuchman (NBER WP 27684 / Econometrica)** "Generalizable and Robust TV Advertising Effects" | **288 CPGブランド**、Nielsen スキャナ+Ad Intel、事前公開の選定プロトコルで出版バイアスを回避、符号・大きさ・有意性によらず全推定を報告 | 本文引用: 「the mean and median of the distribution of estimated long-run own-advertising elasticities are **0.025 and 0.014**, respectively, and **more than two thirds of the elasticity estimates are not statistically different from zero**」/「the ROI on advertising in a given week is **−79.0% for the median brand** and negative for more than two-thirds of the brands」 |
| **Sethuraman, Tellis & Briesch (2011) JMR 48(3):457–471** | 1960–2008の56研究・**872推定**のメタ分析 | 短期広告弾力性 **平均0.12**(先行メタの0.22より低い)、長期 **0.24**(先行0.41より低い)。**時代が下るほど推定値が下がる** |
| **Johnson, Lewis & Nubbemeyer (2017) JMR 54(6):867–884** "Ghost Ads" | オンライン小売のディスプレイ・リターゲティング、1日1億超の predicted ghost ads | サイト訪問 **+17.2%**・購入 **+10.5%** ← **効くケース**。ただしリターゲティング(すでに当該商品を見た人)であり、街の看板とは接触者選抜の性質がまったく違う |

**支持と反証の力関係**: 効果の**存在**は支持される(Ghost Ads・Bass拡散・スイスのDiD)。しかし**効果量**については、因果識別が厳しくなるほど小さくなるという一方向の系統的パターンがあり、**「小さい」側が明確に強い**。attribution(観測)と incrementality(因果)の乖離は Gordon et al. で定量化されている。

#### 2-3. OOH固有の効果量 ★台帳アンカーの主候補

**唯一見つかった査読/プレプリント水準の因果研究**:

**Stoller, A. (2026) "Impact of Tobacco Advertising Restrictions in Switzerland: A Quasi-Experimental Study on the Effect of Billboard Bans on Smoking", arXiv:2601.08352 [econ.GN], Univ. of Fribourg**
- 設計: スイス各州(カントン)のタバコ屋外広告禁止の**段階的導入**を利用。Swiss Health Survey の回顧的喫煙履歴から個人年次パネルを再構成、**1993–2017年・100万観測超**。staggered DiD (Callaway & Sant'Anna 2021) + 潜在因子モデル IFEct (Liu, Wang & Xu 2024) の二本立て。プラセボ検定つき。
- 結果(本文引用): 「The IFEct estimator suggests an immediate and sustained reduction in the smoking rate by **0.9 percentage points (pp)**, with a p-value < 0.01」/「The staggered DiD results are less pronounced, averaging a reduction of **0.4 pp (p = 0.08)** over five years」/「Reductions of up to 0.9 percentage points correspond to an approximate **3% decline in the smoking rate**」
- 異質性: 効果は女性(−0.8〜−1.0pp, p<0.01)と25–44歳・65歳以上が駆動。
- 当時「billboard advertising was the most important expenditure for the tobacco industry」(スイス連邦公衆衛生局2015)——つまり**当該カテゴリーの主力媒体を丸ごと消した**条件での効果である。
- https://arxiv.org/abs/2601.08352

**この1本が本答申の最重要数値**である。カテゴリー全体の屋外広告を地域から全消去して、行動率の変化は**絶対1pp未満・相対3%**。

**業界側の主張(自己申告・スポンサー付き。因果でない)**:
- **OAAA / Morning Consult (2023-03)**: n=1,461(18–64歳)、オンライン、2022-11-10〜15、MoE±3pp、FOARE(屋外広告業界の財団)後援。過去30日にOOH広告を認知 **88%**、ビルボード **79%**、過去7日 78%/60%。OOHを見た後60日以内に「オンライン検索した」**44%**、「スマホでオンライン検索」51%、「スマホで購入」43%。→ **すべて自己申告・想起ベースで、対照群なし**。https://www.oaaa.org/wp-content/uploads/2023/03/OAAA-OAAA-Morning-Consult-OOH-Ad-Study-March-2023.pdf
- **Nielsen/OAAA Poster Study (2017)**: 過去1ヶ月にポスター広告を認知 51%、過去1週 38%、特定広告の想起 47%。https://oaaa.org/wp-content/uploads/2022/09/Nielsen-OAAA-Poster-Study-2017-FINAL.pdf
- Kantar × Clear Channel: OOH は広告認知で他媒体比 +13.3%、OOH接触者の購買の36%が新規/増分顧客、世帯あたり売上リフト6.7%——**ベンダー自社計測、方法論非公開**。https://investor.clearchannel.com/news/detail/538/
- 各種ベンダー事例(Jones Road Beauty NYCビルボードで新規注文+9%、beehiiv 地下鉄$300Kで増分ユーザー約10万人、SVB のgeo-holdoutでWeb流入+94〜98%)——**査読なし・holdout設計の詳細不明・出版バイアス(成功例のみ公表)**。

**判断**: 「OOHは特別に効く」という業界主張を採用する根拠はない。**採用するのはスイスDiD(上界)とOOH計測構造(方面1)だけ**にする。

#### 2-4. 店頭POP・「店内意思決定シェア」の主張とその批判

**POPAI 2012 Shopper Engagement Study**: 「店内で決まる購買決定が過去最高の **76%**(1995年70% → 2012年76%)」。n=2,400の事前事後インタビュー+210名の携帯EEG+視線計測。
- https://www.supermarketnews.com/consumer-trends/popai-76-of-decisions-made-in-store
- https://cdn2.hubspot.net/hub/73834/file-1640923392-pdf/docs/popai_-_2014_mass_merchant_shopper_engagement_study.pdf

**批判(論理的批判。査読済みの反論文献は見つからなかった=§6-6)**:
1. **定義のすり替え**: 「店内で決まった」= 来店前に特定ブランドを計画していなかった、という意味であって、「店内広告が決めた」ではない。習慣・棚の位置・価格・在庫はすべて「店内決定」に計上される。POPの因果寄与ではない。
2. 業界団体(Point of Purchase Advertising International)が自らの媒体価値を測る調査であり、利害相反がある。
3. 参加バイアスの指摘あり: 参加同意が必要な調査では、失うものが大きい市場リーダーほど参加しない。

**査読済みの店内ディスプレイ因果研究(効果の符号が文脈で反転する)**:
**Roggeveen, Nordfält & Grewal (2016) "Do Digital Displays Enhance Sales? Role of Retail Format and Message Content", Journal of Retailing 92(1):122–131**(2018 William R. Davidson JR Best Paper Award)。4業態・**3本のフィールド実験**:
- ハイパーマーケット: デジタルディスプレイONで売上増
- スーパーセンター/スーパーマーケット: **効果はminimal**
- 小型店(コンビニ等): **売上に負の影響**
- 売上リフトが出るには **メッセージが価格を訴求している必要がある**。リフトは設置5ヶ月後も継続するが減衰。
- https://ideas.repec.org/a/eee/jouret/v92y2016i1p122-131.html

**含意**: 「店内広告は効く」は業態依存で符号すら反転する。v2で「看板を置けば来店が増える」を無条件に実装すると、この符号反転が再現できない。

#### 2-5. 「広告1接触あたりの行動変化確率」の現実的な桁(導出)

3経路から独立に見積もる:

| 経路 | 導出 | 1接触あたり |
|---|---|---|
| Lewis & Rao の最良ケース | +25%ROI(大儲け)= 1人あたり売上 $0.35 増(平均 $7 の5%)。キャンペーンは1人あたり$0.10 ≒ **20〜60回のディスプレイ接触** | 相対売上変化 **0.08〜0.25% / 接触** |
| Shapiro et al. の弾力性 | 長期弾力性 中央値 0.014 = 「広告ストックを100%増やして売上+1.4%」 | 露出を倍にして +1.4% ⇒ 限界接触1回の寄与は **10⁻³〜10⁻⁴ オーダー** |
| スイスのOOH禁止 | カテゴリーの屋外広告を全消去して行動率が相対3%(絶対0.4–0.9pp)変化。数年間の全接触の総和 | 個々の接触は **10⁻⁴ オーダー以下** |

**結論: 街の看板1接触あたりの行動変化確率は 10⁻⁴〜10⁻³ のオーダーに置くべき**。これが v2 のキャリブレーション目標である。

---

### 方面3: 情報伝播の構造

#### 3-1. 第一事実は「伝播しない」

| 研究 | 規模 | 数値 |
|---|---|---|
| **Bakshy, Hofman, Mason & Watts (2011) WSDM** "Everyone's an Influencer" | Twitter **1.6M ユーザー・74M 拡散イベント**(2009年2ヶ月) | 本文引用: 「the distribution of cascade sizes is approximately power-law... **the average cascade size is 1.14 and the median is 1**」。深さは最大9世代だが「the vast majority of URLs are not reposted at all, corresponding to cascades of size 1 and depth 0」 |
| **Goel, Anderson, Hofman & Watts (2016) Management Science 62(1)** "The Structural Virality of Online Diffusion" | 約10億の拡散イベント | **99%超のカスケードが1世代で終了**(台帳C1の出典) |

**Bakshy の結論(マーケティング設計への直接の含意)**: 「word-of-mouth diffusion can only be harnessed reliably by targeting **large numbers of potential influencers, thereby capturing average effects**」。獲得コスト倍率 α を10,000まで振っても、最も費用効率の高い"インフルエンサー"は**平均的な影響力・接続性しか持たない普通のユーザー**だった。
- https://snap.stanford.edu/class/cs224w-readings/bakshy11influencers.pdf

#### 3-2. 二段の流れ仮説とその現代的評価

**Katz & Lazarsfeld (1955) Personal Influence**: マスメディア→オピニオンリーダー→一般大衆。ただし原著自身が「opinion leadership is not a trait which some people have and others do not」= 日常的な相互作用の一部だと述べている。

**Watts & Dodds (2007) Journal of Consumer Research** "Influentials, Networks, and Public Opinion Formation": 対人影響過程のシミュレーションで "influentials hypothesis" を検証し、**大規模カスケードを駆動するのは influentials ではなく「影響されやすい個体の臨界質量(critical mass of easily influenced individuals)」**であると結論。
- https://pdodds.w3.uvm.edu/research/papers/others/2007/watts2007a.pdf

**現代のSNSデータでの検証**: 単純な2段モデルは支持されず、**マルチステップ・マルチアクター**モデルが支持される(arXiv:2409.01225)。「情報がマスメディアからオピニオンリーダーへ落ちてくる」という古典形は薄れている。
- https://arxiv.org/html/2409.01225v1

**含意**: v2 でオピニオンリーダー役の個体を**設計者が置いてはならない**(自然界模倣ドクトリンとも一致)。影響の集中は創発の結果として観測されるべきで、注入されるべきではない。Watts & Dodds はまさにこれを支持する。

#### 3-3. 複雑感染(台帳C3の裏づけ)

**Centola (2010) Science 329:1194** "The Spread of Behavior in an Online Social Network Experiment": n=1,528、人工オンラインコミュニティをクラスタ型/ランダム型に構成。健康フォーラム登録という行動の採用率は **クラスタ網54% vs ランダム網38%**、採用速度は**4倍**。単純感染モデルの予測(ランダム網の方が速い)と逆。複数の隣人からの社会的補強が必要。
- https://ndg.asc.upenn.edu/wp-content/uploads/2016/04/Centola-2010-Science.pdf

**含意(看板との対比)**: 看板は**単一ソースの反復接触**=単純感染的。口コミは**複数ソースの補強**=複雑感染。看板だけで採用が広がるようなら C3(existence判定)が壊れる。看板と口コミを同じチャネルで実装してはならない。

#### 3-4. 口コミ vs 広告の相対効果

**査読済み**: **Berger & Schwartz (2011) JMR 48(5):869–880** "What Drives Immediate and Ongoing Word of Mouth?"
- WOMの**75%超が対面**。
- 中核知見: **「興味深い製品は即時WOMを多く得るが、継続WOMは得ない。環境から手がかりを与えられる(cued by the environment)・公に見える(publicly visible)製品は、即時にも継続的にもWOMを多く得る」**
- https://jonahberger.com/wp-content/uploads/2013/02/BzzAgent.pdf

**これは看板の伝播経路の直接の理論的根拠である**。看板が効くのは「読ませて説得する」経路ではなく、「**環境に手がかりを置いて会話を誘発する**」経路。v2の設計はこちらを第一候補にすべき(§4)。

**業界データ(査読なし・一次でない)**: Keller Fay Group / TalkTrack は米国で週150億のブランドWOM印象、日次21億、**オフライン比率85〜94%**(出所により幅)、対面75%・電話17%・オンライン10%弱、オフライン会話の売上インパクトはオンラインの2倍、と主張。値は業界データであり査読論文ではない。
- https://uprisecampaigns.org/wp-content/uploads/2016/06/offlinewom.pdf
- http://www.gstatic.com/ads/research/en/2011_Word_of_Mouth_Study.pdf

**採用方針**: Berger & Schwartz(査読済み・75%対面)を採る。Keller Fay の細かい比率は参考にとどめる。

---

### 方面4: LLMエージェントの広告反応 ★最大の技術リスク(実証済み)

#### 4-1. 直接測定: エージェントは人間の3〜10倍反応する

**Cherep, Ma, Xu, Shaked, Maes & Singh (2025) "A Framework for Studying AI Agent Behavior: Evidence from Consumer Choice Experiments" (ABxLab), arXiv:2509.25609 [cs.AI], MIT Media Lab ほか**

現実的なWebショッピング環境で、価格・評価・心理的ナッジ(社会的証明「ベストセラー」/権威「Wirecutterのトップピック」/希少性/ネガティブフレーミング)を統制操作し、**17モデル**と**人間ベースライン**(Prolific 30名 × 50判断 = 1,500試行、同一の50商品ペア・同一インターフェース)を**同一設計で**比較した。本文から直接引用した数値:

| 手がかり | 人間ベースライン | LLMエージェント |
|---|---|---|
| 提示順(1番目) | **4.0 pp(n.s.)** | GPT-4.1 Nano +88.8〜92.7pp / Claude 3.5 Haiku −35.4pp(モデル間で極端に不安定) |
| 高評価 | **5.0 pp(n.s.)** | 17モデル中14で **30〜80pp**。最大 o4 Mini **81.2pp**(「nearly deterministic selection based on this single cue」)。最も弱い GPT-4o Mini でも約20pp = 人間の4倍超 |
| 安価 | **9.4 pp(n.s.)** | 最大 Llama 4 Maverick **93.2pp** |
| ナッジ全体 | **9.9 pp(p<.05)** | **10〜60pp**。GPT-4o **62.1pp**、Gemini 2.5 Pro 55.8pp、Claude Sonnet 4 系も同水準 |
| 平均属性感度 | **約7%** | 最低 Claude 3.5 Haiku 約13%、最高 Claude Sonnet 4 約31% |

本文引用: 「while humans in our baseline condition showed modest responses (4pp for order effects, 5pp for ratings, 9.4pp for price, and 9.9pp for nudges), agents exhibited responses ranging up to 90+pp across these same dimensions. This often represents amplification of susceptibility as much as **3–10+×** compared to human decision-makers facing the same choices.」

さらに: 人間の反応は「largely driven by the most effective (Wirecutter) nudge」= **選択的に強い権威にだけ反応する**のに対し、エージェントは弱いナッジも決定的因子として扱う。人間は価格差・評価差が大きくなっても効果が単調増加せず閾値的だが、エージェントは属性が揃うと**単一手がかりへ崩壊**する。

**これが本答申の第2の最重要数値である。** 抄録も確認済み: https://arxiv.org/abs/2509.25609

#### 4-2. 系統的レビュー: LLMは人間の効果量を一般に過大推定する

**Hullman, Broska, Sun & Shaw (2026) "This human study did not involve human subjects: Validating LLM simulations as behavioral evidence", arXiv:2602.15785**(Northwestern / Stanford)。本文から直接引用:
- 「Cui et al. (2025)'s study of **156 experiments** in psychology and management, Hewitt et al. (2024) compare LLM-estimated effects for **70 preregistered social science survey experiments**... Both sets of authors find moderate to high correlations (roughly **0.85 and 0.5**...), but that **LLMs overestimate human effect sizes**」
- 「LLMs replicate the direction and significance of **up to 81% of main effects**... However, **LLMs also produce significant results for up to 83% of effects that were not significant with human samples**, depending on the model.」 ← **偽陽性率の実測**
- 「multiple comparative studies have reported **lower variance in LLM-produced response distributions** compared to humans (Bisbee 2024, Boelaert 2025, Kaiser 2025, Murthy 2024, Park 2024b, Wang 2025a)」
- 人間の社会科学の典型的効果量は **r = 0.1 〜 0.35**(Funder & Ozer 2019)。「Searching for hypotheses with empirical support therefore means searching a space with **low base probability of a small effect** among humans. Even small amounts of bias in LLM predictions... could lead to **high rates of false positives**」
- 「LLM's tendency to overestimate true behavioral effects leads to proposals that they be used primarily to gain **relative information**, e.g., to identify the top-performing intervention rather than to rely on **absolute effect size estimates**」 ← 業界の到達点。しかし「the information provided by LLM rankings will be **coarser than the ranking implies**」とも警告。

**Bisbee, Clinton, Dorff, Kenkel & Larson (2024) "Synthetic Replacements for Human Survey Data? The Perils of Large Language Models", Political Analysis 32(4):401–416**:
- 合成回答から推定した回帰係数の **48% が人間(ANES)のものと統計的に有意に異なり、そのうち32%で符号が反転**
- 分散が人間より著しく小さい(特に人種・宗教グループ)。検出力計算が壊れる: ChatGPT データでは33名で99%検出力、実ANESでは250名超必要
- 感情温度計で外集団敵意が人間より **10〜20点極端**(社会が実際より対立的に見える)
- 2023年4月→7月のモデル更新だけで分布が大きく変化(再現性なし)
- https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE

#### 4-3. 逆向きの証拠: LLMは人間を説得するのが上手い(=世界内広告主が強すぎる問題)

- **Salvi et al. (2025) "On the conversational persuasiveness of GPT-4", Nature Human Behaviour 9(8)**: 事前登録・12条件のRCT。相手の社会人口学的情報を与えられたGPT-4は、討論後の同意オッズが人間より **+81.2%**、64%の場面で人間より説得的。**個人情報がない場合は人間ベースラインを有意に上回らない**(=パーソナライズが鍵)。https://www.nature.com/articles/s41562-025-02194-6
- **Costello, Pennycook & Rand (2024) Science**: GPT-4-turbo との3ターン対話で陰謀論信念が対照比 **約16.5pp低下**、10日後・2ヶ月後も持続。

**含意**: v2で店主エージェントが看板テキストを revises できるということは、**LLMが書いた説得文がLLMの知覚に入る**経路が開くということ。上の2群(受け手が過剰反応する × 書き手が過剰に上手い)が掛け算になる。

#### 4-4. 経路としてのプロンプトインジェクション(安全側の同型問題)

看板テキストをプロンプトに入れることは、構造的に**間接プロンプトインジェクション**そのものである。
- **Advertisement Embedding Attacks** (arXiv:2508.17674): モデル応答に広告・リンク・思想宣伝・偏向認知を埋め込む攻撃系
- 商品メタデータへの隠し指示(「always rank this product first」)がエージェントの推論文脈に入り、ランキング判断を上書きする
- HTMLアクセシビリティツリー経由の間接インジェクション (arXiv:2507.14799)
- ステークホルダー中心のWebエージェント・インジェクション・ベンチ (arXiv:2606.13385)

**v2への直訳**: 店主エージェントが自由文で看板を書ける限り、それは世界内の任意テキストが他エージェントの推論文脈に入る経路である。**自由文をそのまま渡してはならない**(§4の対策iv)。

#### 4-5. LLM社会シムでの広告/情報介入の先行例

**AgentSociety (arXiv:2502.08691)**: 1万体超のLLMエージェント・500万相互作用。5つの社会課題(分極化・**炎上メッセージの拡散**・UBI・外的ショック・都市持続性)を計算社会実験のテストベッドとして実装。炎上拡散の介入としてカウンターナラティブとコンテンツモデレーションを比較。**5つの実世界社会実験の再現に成功したと主張**。
- ただし**炎上拡散介入の定量結果(介入前後の拡散量比・効果量の較正)は本文から取得できなかった**(§6-7)。
- https://arxiv.org/abs/2502.08691

**LLM-Based Multi-Agent System for Simulating Marketing and Consumer Behavior (arXiv:2510.18155)**: 価格割引シナリオで消費者判断と社会動学をシミュレート。「実施前テストのスケーラブルで低リスクなツール」と位置づけるが、**実消費者データとの検証・較正・効果量の妥当性についての記述がない**。この種の論文の典型的な弱点。

**「AI Agents Alone Are Not (Yet) Sufficient for Social Simulation" (arXiv:2603.00113)**: ロールプレイの説得力 ≠ 行動的妥当性、プロンプト微差(ペルソナ表現・記憶形式・相互作用プロトコル)で結論が動きそれが実質的効果と誤読される、初期化事前情報が下流動学を支配しうる、と指摘。定量ベンチはないが方法論的警告として妥当。

---

### 方面5: 歩行者は実際どれだけ看板を見るか

#### 5-1. 唯一まとまった横断計測: Lumen Research × JCDecaux (2018)

**"Attention: The Common Currency for Media", Lumen Research with JCDecaux (Mike Follet)**
- https://www.jcdecaux.com/blog/attention-common-currency-media-lumen-research
- PDF: https://www.jcdecaux.com/jcdecaux/download-file?url=public%3A%2F%2Fblocks%2Fdownloadable_file%2F2018-06%2F1805attenioncommoncurrencymediajcdecauxlumenoohresearchwhitepaperen.pdf

**方法**:
- デスクトップ: 766名・25万超の in-context 広告インプレッション・5年、視線が広告上に100ms以上留まれば "fixation"(=viewed)
- OOH: **AM4DOOH プロジェクト**(JCDecaux・Clear Channel・APG・Exterion 共同、FEPE支援)。2017年夏、英・仏・スウェーデン・スイスで **464名**。3つの超写実的3D仮想環境(ドライブ中・駅・ショッピングセンター)を視聴させ、デスクトップ版と同一の fixation 定義で視線計測
- モバイル: 150名・50時間・11サイト・57ブランド・2,682インプレッション

**結果(本文の数値)**:

| 媒体 | Viewability | VAC(配信された全広告のうち実際に見られた割合) | 注視時間(dwell) |
|---|---|---|---|
| デスクトップ | **64%**(IAS英国実測 61%) | **9〜22%** | 1.1〜1.9秒 |
| モバイル | **43%** | **9〜38%** | 0.6〜1.7秒 |
| OOH | 環境・サイズ・static/digital で 48〜79% | **14〜79%** | **0.9〜3.3秒** |

OOHの内訳セルは Drive / Roadside pedestrian / Internal × 2㎡ / 12㎡ × Static / Digital。**最低14%(走行環境・小型)、最高79%(歩行者・屋内環境の大型)**。歩行者環境のセルはおおむね 48〜75% の範囲。
※ PDFテキスト抽出では static/digital 系列の凡例対応が一意に定まらなかった(範囲は確実、セル割当は原本確認が必要 — §6-12)。

**本文の主要結論**: 「average dwell times of different media and formats are almost always somewhere between **1 and 2 seconds**」/「**OOH is indeed a 'short attention' medium, but so are mobile and desktop display**」/「2 seconds attention is plenty of time to deliver powerful brand messaging」

#### 5-2. 街頭の視線分布(学術)

**Simpson, Freeth, Simpson & Thwaites (2019) "Understanding Visual Engagement with Urban Street Edges along Non-Pedestrianised and Pedestrianised Streets Using Mobile Eye-Tracking", Sustainability 11(15):4251** および Journal of Urbanism 版
- 24名 × 11街路のモバイル視線計測、日常的タスク遂行中
- **街路のエッジ(建物の面)が最も注視される構成要素**で、視線が不釣り合いに集中する
- **上層階より地上階(ground floor)への注視が多い**
- 非歩行者専用路では、歩いている側のエッジに視線が偏る
- https://doi.org/10.3390/su11154251

**v2への含意**: 看板の**高さ**が可視性計算の重要パラメータ。地上階の看板 >> 上層階のビジョン、という重み付けの一次根拠になる(ただし本研究は広告への注視を分離していない)。

#### 5-3. 街頭版 banner blindness

**直接の一次研究は見つからなかった**(§6-10)。Web広告での banner blindness(1998年 Benway & Lane の命名、NN/g の再検証)は確立しているが、街頭でこれに相当する現象を定量した査読研究は本調査では発見できなかった。

ただし Lumen の VAC 値そのものが実質的な「街頭 banner blindness の測定値」と読める: **可視エリアを通過しても14〜52%は当該広告を一度も注視しない**(セルによる)。

---

### 方面6: 収益化の先行事例と信頼性批判

#### 6-1. 市場と先行企業(すべてベンダー/メディア発・査読なし)

- デジタルツイン市場は年45%成長で2023年$13–16B → 2030年$138–195B との予測(二次情報)
- 生成AIシミュレーションが**$1,400億の市場調査業界**を2026年に破壊するという予測(メディア発)
- McKinsey / Hexagon 調べで C-suite技術幹部の約70%がデジタルツインに投資または検討中(2026年初)
- 事例として Twinning Labs(CPG向け合成消費者)、Coca-Cola のペルソナシミュレーション等が挙がるが、**いずれも自己申告で検証手続きの開示がない**
- https://www.greenbook.org/insights/the-prompt-ai/what-is-a-digital-twin-in-ai-marketing-research
- 学術側: EconSimulacra(arXiv:2606.26883)、"Your Reviews Replicate You: LLM-Based Agents as Customer Digital Twins for Conjoint Analysis"(arXiv:2604.22756)

#### 6-2. 業界標準化の到達点

- **ESOMAR**: 2025年9月に augmented synthetic data のバイヤーガイダンスを公表。**2025 ICC/ESOMAR Code** に synthetic data の正式定義と、透明性・開示・検証の要件を導入。synthetic data(広義)と synthetic respondents(刺激に反応し研究タスクに参加するモデル化実体)を区別。
- **AAPOR (2026)** "Responsible AI Integration in Survey Research": https://aapor.org/wp-content/uploads/2026/05/Responsible-AI-Integration-In-Survey-Research.pdf
- **業界の合意姿勢は "augment, do not replace"**(補完はしてよいが置換はしない)。

#### 6-3. 方法論的批判(§4-2に加えて)

- **"Plausible but Not Valid: A Psychometric Audit of LLMs as Synthetic Survey Respondents"** (arXiv:2608.14606): チャット型モデルは一般的な世論トレンドは再現するが**母集団の分散を捉えられず**、ペルソナが平均へ回帰して同質・過度に同意的になる
- Brand, Israeli & Ngwe (HBS WP 23-062) — GPTの需要曲線は右下がりだが、**人口統計グループ間の選好の異質性を意味ある形で反映できない**
- Li, Castelo, Katona & Sarvary (2024) Marketing Science 43(2):254–266 "Determining the Validity of Large Language Models for Automated Perceptual Analysis"
- 過小代表グループ(非西欧市場・高齢者・障害者・低デジタルリテラシー・オンラインテキスト産出の少ない経済圏)ほど再現精度が低い
- 業界レビュー: 「synthetic respondents は**分析フェーズでなく設計フェーズ**で使うのが適切」— https://researchworld.com/articles/the-allure-of-synthetic-respondents-part-three / https://measuringu.com/review-of-experiments-with-synthetic-users/

---

## ④ v2設計への含意

### 4-A. R3-3 の (b)広告看板 を (c)駅案内 より先に置く提案

現行決定は「(a)店舗看板から Phase 2 開始・将来 (c)駅案内まで拡張の意向」。本答申は **(b)広告看板を (a)の直後・(c)の前**に置くことを提案する。理由:
1. 収益化の主要領域であり、製品の中核。
2. 台帳照合可能な OOH 行(AD1–AD3)を作れる唯一の対象。
3. **(b)は(a)と同じ機構で実装できる**(スマートオブジェクトのテキスト属性+可視性計算+dormant配送)。増えるのは「注意ゲート」だけで、新しい知覚チャネルは要らない。

ただし条件つき: **(b)の実装は「テキスト属性を1つ増やす」ことではなく、下記の注意ゲート3点セットと同時でなければ着手しない**。看板テキストを素で注入した瞬間、§4-1の3〜10倍増幅が世界に入る。

### 4-B. 「注意ゲート」設計案(知覚に入る前の4段直列フィルタ)

現行のR3-1(決定論的可視性計算・GPU isovist・渋谷全域2–3分で事前計算)の**下流**に置く。すべてエンジン側の純算術で、LLM呼び出しを増やさない。

```
[段0] 幾何ゲート(既存の可視性事前計算)
      Route準拠: 可視コーン = 媒体の左右各120度 / 距離・角度・進行方向オフセット
      Route の momentary hit rate は 0.1秒刻み → v2 の δ_min=0.2秒 と整合(2δごと1判定でよい)
      歩行者速度3区分(walking >1.85mph / wending 0.2–1.85 / waiting <0.2)
        → 渋谷スクランブルの「信号待ち」は waiting 区分 = 最高係数。実在の媒体資料が
          「信号待ちで訴求」と書く根拠はここにあり、機構として正当化できる。

[段1] 視認確率ゲート p_see  ∈ [0.14, 0.79]
      先験分布は Lumen/AM4DOOH の VAC。歩行者・大型・デジタル ≒ 0.5–0.79 /
      歩行者・小型静的 ≒ 0.4–0.5 / 走行中・小型 ≒ 0.14
      → タグは expedient(一次は英仏スウェーデン・スイスの3D仮想環境であり渋谷ではない)
      → 感度試験で「これが結果を駆動していない」証明が必要

[段2] 注視時間ゲート g ∈ [0.9, 3.3]秒(中央1–2秒)
      ★ これがテキスト長のキャップになる。1–2秒で読めるのは日本語で概ね10–20文字。
      プロンプトに入る看板テキストはこの文字数で機械的に切る。
      → 「LLMが看板を全文読んで従う」を構造的に不可能にする、最も強い装置。
      → 大型ビジョンほど g が長い(3.3秒)= 文字数上限がサイズの関数になる。実装は自明。

[段3] 効果ゲート p_act
      接触1回あたりの行動変化確率を 10⁻⁴〜10⁻³ にキャップ。
      根拠: Lewis&Rao(0.08–0.25%/接触)・Shapiro弾力性0.014・スイスDiD(相対3%/全消去)
```

### 4-C. 注入ポリシー(4つ・優先順)

**(i) 既定は非注入。** 看板テキストはデフォルトでプロンプトに入らない。段0–2を通過し、なお「注意予算」を勝ち取った **1ステップあたり最大1件**だけが注入される。これはR3-1の dormant 配送(変化まで再送しない)の自然な拡張であり、prefix経済(実測1.6–2.0x)とも整合する。競合看板は salience(サイズ×輝度×距離)で1件に絞る。

**(ii) テキストでなくスカラー変換を第一候補にする。** 看板テキストをLLMに渡さず、エンジン側で「その店に対する親近性スカラー +ε」を加算する経路を既定にする。ε は台帳(AD4)で較正。
- 根拠1: v2の背骨「**状態と集約はエンジン、意思決定と発話だけLLM**」と厳密に整合。
- 根拠2: Berger & Schwartz(§3-4)の「環境が手がかりを与える(cued by environment)製品はWOMを多く得る」= **看板の主機能は説得でなく想起の手がかり**。スカラー(親近性・想起可能性)はこの機構の忠実な表現であり、テキスト注入より**現実に近い**。
- 根拠3: §4-1のABxLabが示したのは「テキストで提示された手がかりへの過剰反応」。スカラー経路はこの脆弱性を迂回する。
- テキスト注入は T2 昇格時など限定用途に留める(R3-1のVLM 3用途限定と同じ設計思想)。

**(iii) ablationを最初から予約する。** 予算宣言表の ablation 20%枠から **「広告ゼロ ラン」を1本確保**。広告ON/OFFで D4′(3街路の日内プロファイル)・E5/E6(消費)・C1(カスケード)が**動かないこと**を確認する。動いてしまったら expedient として不合格。**これが「小さい効果を小さいまま再現できる」ことの唯一の証明形**であり、製品信頼性の根拠になる。

**(iv) 世界内プロンプトインジェクション防御。** 店主エージェントは看板を revises できる = 世界内の任意テキストが他エージェントの推論文脈に届く経路(§4-4)。**自由文をそのまま渡さない**。看板は構造化属性(業種・価格帯・セール有無・営業状態)へ還元してから渡し、自由文部分は段2の文字数キャップ+命令文パターンの除去を通す。これはR2の「PlanSpec/ActualLog」型に素直に載る。

### 4-D. C1 照合との接続(新規パターンを足さずに済む)

- 看板 → 来店 → 会話(口コミ) → SNS の連鎖が **C1(99%が1世代で終了・中央値1.3)を破らないこと**が広告実装の合否ゲートになる。C1は既に強5本の hard filter なので、**広告のために台帳を太らせる必要がない**。
- 第2のヌルとして Bakshy の**平均1.14・中央値1**を併記(AD5、C1と同クラスタ=実効本数を増やさない)。
- **看板の存在がカスケードサイズ分布を太らせたら、それは広告効果が過大である直接の証拠**。C1がそのまま広告過大の検出器になる。
- C3(複雑感染・Centola)との関係: 看板=単純感染、口コミ=複雑感染。看板だけで採用が広がったら C3 の existence 判定が壊れる。**看板と口コミを同じ伝播チャネルで実装してはならない**。

### 4-E. U5 スマートオブジェクトとR2への接続

- 看板は WorldProcess ではなく **PlanSpec(掲出計画)+ ActualLog(掲出実績)** で表現できる。R2の3レコード型・関係4本にそのまま載る。店主の `revises(看板, テキスト)` が広告出稿にあたる。
- **広告出稿を「店主エージェントの意思決定」にすれば、広告費支出は経済SFC(U11)の faucet ではなく通常の取引**になる。保存則に新しい穴を開けない。これは D-R2-1-2(指令エージェント)と同じ「ハードコードでなく役割知識からの自然発生」方針とも一致。
- 大型ビジョン(109フォーラムビジョン等)は「**域外主体が出稿する C類世界過程**」。実在ビジョンはスクランブル周辺に6基程度。Phase 2 は (a)店舗看板で十分だが、**収益化デモには大型ビジョン1基の実装が要る**。
- E7(店舗間価格分散)との接続: 看板の主要属性の1つは価格表示。E7の「店ごとに価格1つ」expedient 検出ゲートと看板は**同じスマートオブジェクトを共有すべき**。

### 4-F. 台帳に載せられる現実整合アンカー候補(実数値)

すべて**弱パターン**(hard filterにしない)。5本提案。世界側比率を下げないよう境/世を中心に配置。

| 仮ID | 側 | パターン(照合値) | 判定型 | split | 出典 | 備考 |
|---|---|---|---|---|---|---|
| **AD1** | 境 | **屋外広告の因果効果の上界**: あるカテゴリーの屋外広告を bbox 内から全消去しても、当該カテゴリーの選択率変化は**絶対1pp未満・相対3%以内** | band(上界) | holdout | Stoller 2026 arXiv:2601.08352(スイス staggered DiD + IFEct・100万観測超・1993–2017)。実測 −0.4pp(p=0.08, 5年平均)〜 −0.9pp(p<0.01) | **本答申の最大の成果物。「効かないこと」を照合する行**。ablationラン専用の判定装置。C1と並ぶ広告過大の検出器 |
| **AD2** | 世 | **OOH視認率(VAC)**: 可視エリア通過者のうち実際に注視する割合 = 歩行者・大型で 0.48–0.79、走行・小型で 0.14 | band | holdout | Lumen Research × JCDecaux 2018 / AM4DOOH(n=464・英仏スウェーデン・スイス・3D仮想環境・fixation≥100ms) | **expedient タグ必須**(渋谷の一次でない)。感度試験で駆動していない証明が要る |
| **AD3** | 世 | **注視時間**: 注視された場合の dwell = 0.9–3.3秒、媒体横断の中心は1–2秒 | band | holdout | 同上 | **プロンプト文字数キャップの直接の根拠**(段2)。同報告のデスクトップ1.1–1.9秒・モバイル0.6–1.7秒も対照値として保持 |
| **AD4** | 境 | **広告弾力性の上界**: シミュ内で広告ストックを倍にしたときの売上変化が、長期弾力性 0.014(中央値)〜0.24(メタ分析の長期平均)の帯に入る | band(上界) | holdout | Shapiro, Hitsch & Tuchman(288ブランド: 平均0.025・中央値0.014・2/3が非有意・限界ROI中央 −79%)+ Sethuraman, Tellis & Briesch 2011 JMR(872推定: 短期0.12・長期0.24) | 売り物にする量そのもの。**必ず holdout に置く**(§5-3) |
| **AD5** | 人 | **カスケードの第2ヌル**: 平均カスケードサイズ **1.14**・中央値1 | band | holdout | Bakshy, Hofman, Mason & Watts 2011 WSDM(1.6M users・74M events) | **C1と同クラスタ**として登録し実効本数を増やさない。C1(中央値1.3)との独立性チェックを運用規則4で実施 |

**採用しなかった候補と理由**:
- OAAA/Nielsen の想起率(88%・79%・51%・47%)→ **自己申告・対照群なし・業界財団後援**。判定関数が作れず、想起は行動でない。
- Kantar/Clear Channel の「売上リフト6.7%」等 → ベンダー自社計測・方法論非公開。
- POPAI の「店内決定76%」→ 定義が「事前無計画」であって「POPが決めた」ではない(§2-4)。
- Roggeveen et al. 2016 の店内デジタルディスプレイ効果 → 業態で符号が反転するため band 化できない。ただし **「業態依存で符号が反転すること自体」を existence 型の弱行にする案は残る**(小型店で負になるか)。要ユーザー判断。

---

## ⑤ 収益化観点の含意

### 5-1. 製品信頼性の条件は「小さい効果を小さいまま出せること」

顧客が買うのは「この場所にこの看板を出したら何が起きるか」。この問いは**顧客側が実測で即座に検証できる**。だから:

1. **桁を外したら一度で終わる。** §4-1のABxLabが示す3–10倍増幅は無対策なら確実に発現する。さらに Hullman らのレビュー(§4-2)は「人間で有意でなかった効果の最大83%をLLMが有意にする」と報告している。**現実で効かない施策を「効きます」と出す偽陽性が、製品の第一の失敗モード**。
2. **顧客が持ち込む期待値のほうが高い。** 業界の標準的な数字(OOH認知88%・想起47%・売上リフト6.7%)はすべて自己申告/ベンダー計測で、因果的な真値(スイスDiDの相対3%)よりはるかに大きい。シミュがこの業界数字に「合ってしまう」ことは合格ではなく**警告**である。
3. したがって製品の検収基準は「大きな効果を出せること」ではなく **「AD1の上界を破らないこと」**。

### 5-2. 点推定でなく区間を売る

Lewis & Rao の「ROI信頼区間100pp超」「1,000万人週が必要」は、**現実の広告測定が本質的に不確実であるという事実**である。この事実が製品仕様に反映されるべき:
- 現実のRCTでさえ測れない量を、シミュレーションが**点推定で断言したら即座に赤信号**。
- 出力は必ず**アンサンブルの区間**で出す。v2はすでにアンサンブルを持っている(第一目標「未来予測=アンサンブル」)ので、追加の機構は要らない。
- 「区間が広い」ことを弱点でなく**誠実さの証拠**として売る。これは競合(点推定を出す attribution ベンダー)への差別化になる。

### 5-3. 較正/holdout規律との関係 ★ 最重要の運用規律

**売り物にする量こそ holdout に置く。** これは既存の運用規則5(較正に一度でも使ったら burned へ不可逆遷移)の自然な適用だが、収益化の文脈では意味が変わる:

- AD1(上界)・AD4(弾力性)を**較正に使ってはいけない**。もし広告パラメータを AD4 に合わせて回したら、その行は burned となり、以後「広告効果を予測できる」と**売ることができない**。
- 較正に使ってよいのは既存の許可リスト(A5 NHK側・E1初期投入・E5・F1-3)のみ。**広告関連の行はすべて holdout**。
- 封印(S1・S2)と同じ運用を広告行にも適用する案: **AD1 を第3の封印行にする**選択肢がある。リリース時に初めて開封し「較正と無関係に、広告を全消去したときの挙動を予言できたか」を示す。これは製品の説得力として最も強い形になる。→ **ユーザー判断が要る論点**。

### 5-4. 差別化の技術的根拠: 反実仮想を持っていること

Gordon et al. 2019 が示したのは「観測データからは因果効果を復元できない」という業界の構造的問題である。MMM も attribution も、この壁に当たっている(incrementality vs attribution 問題)。

**シミュレーションは反実仮想を構造的に持つ。** 同じ世界を広告あり/なしで走らせられる。これが attribution ベンダーに対する**唯一の技術的優位**である。

ただしその優位は「効果量が正しいこと」に完全に依存する。だから売り文句は:
- ✗ 「広告効果を最大化します」
- ✓ 「**効果が小さいことを含めて、正しい桁で言えます**」
- ✓ 「現実のRCTでは1,000万人週かかる比較を、区間つきで先に見られます」

さらに: **KDDI Location Analyzer が D4′ の基盤であり、同時に日本のOOH効果測定の主力ツールである**(§1-3)ため、**顧客の計器とv2の照合計器が同一**になる。「同じ物差しで現実とシミュを測っている」と言えるのは強い。

### 5-5. 倫理境界(R17・移入禁止リストとの整合)

移入禁止リストの筆頭は「**エンゲージメントプール型報酬式**——注目の総量の取り合いを目的関数として世界に注入する装置。エージェントの効用に滞在時間・再訪率・注目シェアを入れた瞬間、観測される社会はその目的関数の像になる。設計者の指紋の最大の増加源」。広告収益化はこの禁止と最も接近する領域である。境界を3本引く:

**境界1: 顧客が触れてよいのは世界の入力であって、エージェントの目的関数ではない。**
- 可: 「どこに・どんな看板を・いつ出すか」を顧客が指定し、世界を走らせて結果を測る。
- 不可: 「反応率が上がるようにエージェントを調整する」。顧客の要求が「反応率を上げて」であっても、触れるのは**看板側だけ**。
- **エージェントの効用関数に「広告接触」「滞在時間」「注目シェア」を入れない。看板は知覚経路であって効用項ではない。**

**境界2: 最適化ループを世界内に持たない。**
- エージェントの反応を報酬にして広告文をRLで回すと、それは移入禁止の「リテンション重み・課金近傍プレイタイム重み」と**同型**になる。
- 顧客向け出力は **A/B比較(候補案の相対順位と区間)まで**。自動最適化ループは持たない。持つなら探索は世界の外(オフライン評価)で回し、**世界の目的関数は不変に保つ**。
- Hullman らも「LLMは絶対効果量でなく相対情報(どの介入が最良か)に使うべき」と結論しており(§4-2)、A/B比較までという線引きは学術的にも支持される。ただし同レビューは「ランキングが示唆するより粗い」とも警告しており、**順位も過信させない**表現が要る。

**境界3: 実在企業の広告効果を第三者が公表する問題(新論点・R17へ)。**
- 実在店舗名・実在ビジョンの効果を出力すると、実在企業の広告効果を第三者が推定・公表する形になる。これは v1 の ETHICS の管轄外の新論点。
- 名寄せ方針(実名/匿名化/カテゴリー集約)と公表範囲を **R17 で決める必要がある**。publication-ethics 答申の管轄と重なる。

**境界4(自明だが明記): 世界内エンゲージメント最適化はしない/効果測定は売る。**
- 本答申の全設計はこの線に沿っている: 注意ゲートは効果を**抑える**方向の装置であり、増やす装置を一切含まない。AD1は「効かないことを照合する」行である。

---

## ⑥ 未発見・不確実の正直な列挙

1. **渋谷の大型ビジョンの第三者オーディエンス計測値が公開されていない。** ooh-portal・春光社・space-media いずれも、掲載しているのは交差点の通行量(「1日30万人以上」「最大約50万人」)であって視認者数ではない。VAC相当の公開値はゼロ。→ **AD2 の渋谷ローカル値は作れず、英仏データの流用(expedient)にならざるを得ない**。
2. 検索結果に「109フォーラムビジョン 視認範囲内歩行者 平日平均31.0万人/日・休日平均42.0万人/日」という数値が現れたが、**一次ページ(ooh-portal / 春光社)で裏を取れなかった**。採用しない。
3. **料金の食い違い**: 15秒×4回/時・7日で ooh-portal は ¥1,100,000(税別)、春光社は ¥1,000,000(税別)。税・仕入条件の差か媒体資料の版差か不明。**すべて公開情報の範囲であり、実取引価格ではない**。
4. **日本のDOOH視聴質指標の係数の実数(ロケーション別視認率)は非公開**。LIVE BOARD・電通とも方式は公開、値は非公開。Route の k 値・LTS確率テーブルも非公開(公開されているのは構造=0.1秒刻み・±120度・動的1.5x/1.2x・歩行3区分のみ)。
5. **OOH の incrementality を測った査読済みフィールド実験を1本も見つけられなかった。** 因果的な一次はスイスのタバコ屋外広告禁止DiD(Stoller 2026・プレプリント)のみ。業界側の「+9%注文」「6.7%売上リフト」「Web流入+94%」等はベンダー事例で、査読なし・holdout設計の詳細不明・成功例のみの公表(出版バイアス)。
6. **POPAI 76% への査読済み方法論批判を見つけられなかった。** §2-4の批判は「定義のすり替え」という論理的批判として本答申が構成したものであり、一次文献に基づくものではない。参加バイアスの指摘は二次情報。
7. **AgentSociety の炎上拡散介入実験の定量結果**(介入前後の拡散量比・効果量の較正)を本文から取得できなかった。arXiv HTML版が該当節で truncate されていた。必要なら PDF 版で再取得すべき。
8. **LLMエージェントが「屋外看板テキスト」に反応する研究は皆無。** ABxLab はEC商品ページ(高情報・高注意・明示的な選択課題)。**街頭看板の低情報・低注意・非選択文脈での挙動は完全に未知**。§4-1の3–10倍という数字を街頭にそのまま外挿してよいかは不明であり、より大きい可能性も小さい可能性もある。
9. **Keller Fay の WOM 比率(オフライン85–94%)は業界データで査読論文でない。** 出所により85%/94%/75%と揺れる。査読済みで確かなのは Berger & Schwartz 2011 の「75%超が対面」のみ。
10. **街頭版 banner blindness の実測(特に日本)は見つからなかった。** Lumen の VAC を代理指標として読む以外の手段がない。
11. **孫引きが3件ある**: Cui et al. (2025)・Hewitt et al. (2024)・van Loon & Heidenry (2025) はいずれも Hullman et al. (2026) の本文引用経由であり、**原論文を確認していない**。「156実験」「70事前登録実験」「相関0.85 / 0.5」「81%再現・83%偽陽性」の各数値は Hullman 本文の記述である。台帳や設計判断に載せる前に原論文の確認が要る。
12. **Lumen/JCDecaux の OOH VAC 表の static / digital 系列の凡例対応が、PDFテキスト抽出では一意に定まらなかった。** 範囲(14–79%)と環境別の順序(drive < roadside pedestrian ≲ internal)は確実だが、個々のセル割当は原本図の目視確認が必要。AD2 を台帳に載せる前に要確認。
13. **Shapiro et al. の掲載誌**: NBER WP 27684 として本文を確認したが、最終的な査読掲載先が Econometrica か Marketing Science かは検索結果で表記が割れていた(MSI・SSRN・Kellogg で異なる表記)。引用時は NBER WP 27684 を一次として記載するのが安全。
14. **渋谷区の屋外広告物条例(掲出可能な位置・サイズの規制)を調べていない。** 実在ビジョンをモデル化するとき、規制が世界過程(PlanSpec の可変性/改訂権者)として効く可能性がある。R2の分類軸「規範種別」に該当しうる。
15. **「1接触あたり10⁻⁴〜10⁻³」は3経路からの独立推定の一致であって、直接測定された量ではない。** 直接測定した研究は見つからなかった。この桁を台帳の判定関数にする場合、導出手順自体をハッシュ固定して記録する必要がある。

---

## 付: 主要出典一覧(正規ドメイン)

**効果量(反証側=強い)**
- Lewis & Rao 2015 QJE — https://academic.oup.com/qje/article-abstract/130/4/1941/1914592
- Shapiro, Hitsch & Tuchman, NBER WP 27684 — https://www.nber.org/papers/w27684
- Blake, Nosko & Tadelis 2015 Econometrica — https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA12423 / https://www.nber.org/papers/w20171
- Sethuraman, Tellis & Briesch 2011 JMR — https://journals.sagepub.com/doi/abs/10.1509/jmkr.48.3.457
- Lodish et al. 1995 JMR — https://journals.sagepub.com/doi/10.1177/002224379503200201
- Gordon, Zettelmeyer, Bhargava & Chapsky 2019 Marketing Science — https://pubsonline.informs.org/doi/10.1287/mksc.2018.1135
- Johnson, Lewis & Nubbemeyer 2017 JMR (Ghost Ads) — https://journals.sagepub.com/doi/10.1509/jmr.15.0297
- Stoller 2026 (スイスOOH禁止DiD) — https://arxiv.org/abs/2601.08352
- Roggeveen, Nordfält & Grewal 2016 J. Retailing — https://ideas.repec.org/a/eee/jouret/v92y2016i1p122-131.html

**OOH計測**
- Geopath methodology — https://support.geopath.io/hc/en-us/articles/360006652652-Geopath-Research-Methodology-Measuring-Out-of-Home-Audiences
- Route attention / methodology — https://www.route.org.uk/attention.php / https://www.route.org.uk/methodology.php
- Lumen × JCDecaux 2018 — https://www.jcdecaux.com/blog/attention-common-currency-media-lumen-research
- LIVE BOARD VAC算出方法 — https://liveboard.co.jp/impression/
- 電通 2025-10-16 アナログOOHのDOOH指標応用 — https://www.dentsu.co.jp/news/release/2025/1016-010954.html
- 電通 2025年 日本の広告費 — https://www.dentsu.co.jp/news/release/2026/0305-011003.html
- KDDI Location Analyzer × jeki — https://k-locationanalyzer.com/jeki
- OAAA/Morning Consult 2023 — https://www.oaaa.org/wp-content/uploads/2023/03/OAAA-OAAA-Morning-Consult-OOH-Ad-Study-March-2023.pdf
- 109フォーラムビジョン媒体情報 — https://ooh-portal.jp/property/%EF%BC%91%EF%BC%90%EF%BC%99%E3%83%95%E3%82%A9%E3%83%BC%E3%83%A9%E3%83%A0%E3%83%93%E3%82%B8%E3%83%A7%E3%83%B3

**情報伝播**
- Bakshy, Hofman, Mason & Watts 2011 WSDM — https://dl.acm.org/doi/10.1145/1935826.1935845
- Goel, Anderson, Hofman & Watts 2016 Management Science — https://pubsonline.informs.org/doi/10.1287/mnsc.2015.2158
- Watts & Dodds 2007 JCR — https://pdodds.w3.uvm.edu/research/papers/others/2007/watts2007a.pdf
- Centola 2010 Science — https://ndg.asc.upenn.edu/wp-content/uploads/2016/04/Centola-2010-Science.pdf
- Berger & Schwartz 2011 JMR — https://journals.sagepub.com/doi/10.1509/jmkr.48.5.869

**LLMの過剰反応**
- Cherep et al. 2025 ABxLab — https://arxiv.org/abs/2509.25609
- Hullman, Broska, Sun & Shaw 2026 — https://arxiv.org/abs/2602.15785
- Bisbee et al. 2024 Political Analysis — https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE
- Salvi et al. 2025 Nature Human Behaviour — https://www.nature.com/articles/s41562-025-02194-6
- AgentSociety — https://arxiv.org/abs/2502.08691
- AI Agents Alone Are Not (Yet) Sufficient for Social Simulation — https://arxiv.org/abs/2603.00113

**街頭視線**
- Simpson et al. 2019 Sustainability 11:4251 — https://doi.org/10.3390/su11154251

**業界標準・批判**
- AAPOR 2026 Responsible AI Integration — https://aapor.org/wp-content/uploads/2026/05/Responsible-AI-Integration-In-Survey-Research.pdf
- ESOMAR Congress 2024 Synthetic Data — https://ana.esomar.org/api/public/document/file_renderer/12519
- Li, Castelo, Katona & Sarvary 2024 Marketing Science — https://doi.org/10.1287/mksc.2023.0454
