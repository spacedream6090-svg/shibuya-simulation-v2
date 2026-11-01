# R-61 答申: 経路選択の錨 — 最短経路からの外れ・角度(スペースシンタックス)・曲がる回数/坂/横断/屋根/緑/店の並びの距離換算・慣れ・散策(回遊)・地図アプリ

<!-- hdr:v1 -->
- **分野**: 交通工学(活動ベース) #2 / 歩行者動力学 #18 / 地理情報科学 #9 / 認知科学(記憶・習慣) #12 | **重要度**: P0([壁打ちの決定 09-30](../design/v2-wallbounce-decisions-2026-09-30.md) §1-4「経路選択 = (c)+(d)」の重みの錨)
- **一次確認**: **B** = サブ実読(原典本文 7・抄録/要約 5・二次 6・空欄 = §9)・親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: ユーザー決定「経路コスト = 所要時間(混雑・坂・信号・縦の接続の待ち)+ 重み(曲がる回数・慣れた道・雨天の屋根・人ごとの急ぎ)。錨のある要素から重みを入れ、無いものは既定 0+感度腕。散策のモードは別モード」の **重みの錨** を原典で並べる。設計の決定はしない(§8 の「既定に入れてよいか」はサブの判断 = 未リサーチ(expedient))。
> 既存答申で済んでいるものは引用だけ: 歩行速度・密度-速度(Weidmann/Kladek)・日本の目的別速度(Zanlungo 2017: 仕事 1.27・余暇 1.12 m/s)・渋谷の信号周期 140 s = [R-52](v2-r52-crowd-model-calibration-shibuya-research.md) §6 A1〜A8・§4-1 / 「歩行者は最短経路を選ばない」の要約 = [移動の場の答申](v2-mobility-field-research.md) §2 / PLATEAU uc22-040(道玄坂の経路選択非集計モデル・GAUSS)の存在 = R-52 §4-2 / 店・広告の注意 = [R-47](v2-r47-classical-choice-attention-research.md)。
> 規律: 子サブ未起動・Web は読むだけ(PDF は OS の一時ディレクトリへ取得して pymupdf で抽出・リポに置かない)・コミットなし・台帳/設計書/コード未編集・本書と R-62 の新規作成のみ。

---

## 結論(5 行)

1. **人は最短経路を外れる。外れは距離とともに増え、約 1 km までで大半が出る**(Bongiorno ほか 2021・ボストン/SF・14,380 人の GPS)。95% の経路は最短の 1.8 倍以内(同論文の前処理の閾値)。**外れの量(平均の比)は原典の図にしかなく、本文の数値は取れなかった**(二次の「約 9%(迂回比 1.09)」は未照合)。
2. **曲がる回数は、錨が最も揃っている重み**: 1 回 = **SF 62.3 m**(一次)・ボストン 34.4 m・ポートランド約 50 m・トロント 32.4 m(二次)・**岡山(日本) 女性 約 48 m [再計算]・男性は有意でない**(一次)。都市でほぼ 2 倍の幅があり、これがフロア。
3. **坂(1 m 登る = 3.8 m)・歩道幅(10 ft 広い = −83.7 m)・店(1 軒 = −1.8 m)・交通量/車速** は SF で距離換算の一次がある。**緑は SF で有意でなく、東京・豊洲では正で有意**=都市で割れる。**屋根(雨)の距離換算の一次は見つからなかった**(NYC の足場の 25 人の画像調査で大雨時 74.4% が屋根側・シンガポールの日陰 0.86 倍が近い錨)。
4. **角度(スペースシンタックス)は、日本の駅周辺では弱い**: 局所統合値と歩行者数の相関は **−0.2 台〜+0.3 台**、主要駅までの距離との相関(**−0.35〜−0.66**)より弱い(新宿・栄・名駅・梅田・AIJ 2025)。渋谷駅の実測(2008)は「視野範囲の広さ・ターン回数の少なさ・最短距離」が効くと要約。**角度は「曲がる回数」の重みで足り、統合値の場は別に要らない**というのがサブの読み(未リサーチ)。
5. **空欄**: 信号待ちの重み(時間とは別の嫌悪)・慣れた道の距離換算(歩行者の数値は無し)・人ごとの急ぎ・渋谷の回遊(立ち寄り回数・歩行距離)・地図アプリの案内に従う割合 = **いずれも一次の数値が見つからなかった → 既定 0+感度腕**。

---

## §0 出典表

等級: **◎** 原典本文で数値まで逐語確認 / **○** 原典は読めたが図の読み取り・査読前・小標本 / **△** 抄録・検索要約・二次 / **×** 未確認(本文に数値を写さない)。**[再計算]** はサブの計算。

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | Bongiorno, Zhou, Kryven, Theurel, Rizzo, Santi, Tenenbaum, Ratti 2021「Vector-based pedestrian navigation in cities」*Nat Comput Sci* 1:678-685(arXiv 2103.07104) | https://arxiv.org/abs/2103.07104 | ◎(本文)/ 外れの量は図のみ | PDF 全文(本文・Methods) |
| 2 | Sevtsuk, Basu, Li, Kalvo 2021「A big data approach to understanding pedestrian route choice preferences: Evidence from San Francisco」*Travel Behaviour and Society* 25:41-51 | https://doi.org/10.1016/j.tbs.2021.05.010(著者稿 = MIT DSpace) | ◎ | 著者稿 PDF 全文・Table 2・Table 3・§2・§4 |
| 3 | Basu & Sevtsuk 2022「How do street attributes affect willingness-to-walk?」*Transp Res A* 163:1-19 | https://doi.org/10.1016/j.tra.2022.06.007 | △ | 検索要約のみ(ボストン 34.4 m/曲がり は二次) |
| 4 | Broach & Dill 2015「Pedestrian Route Choice Model Estimated from Revealed Preference GPS Data」TRB 94th Annual Meeting | https://trid.trb.org/View/1338221 | △ | TRID 抄録(要約経由)・数値は二次 |
| 5 | Tong & Bode 2022「The principles of pedestrian route choice」*J R Soc Interface* 19:20220061 | https://doi.org/10.1098/rsif.2022.0061 | ◎(レビューの記述として) | PMC 本文 §2.5 |
| 6 | Zhang Yufan・太田明・兼田敏之 2025「都心駅周辺地区における市街地構成ならびに歩行者数の空間分布を検討するためのスペース・シンタックス理論の適用に関する研究」日本建築学会計画系論文集 90(828):276-283 | https://doi.org/10.3130/aija.90.276 | ◎ | PDF 本文 §1・§4.1・§4.2 |
| 7 | 上野純平・岸本達也 2008「スペース・シンタックスを用いた複雑多層空間における歩行者流動の分析 — 渋谷駅を対象として」都市計画論文集 43.3:49-54 | https://doi.org/10.11361/journalcpij.43.3.49 | △ | J-STAGE 抄録(要約経由)。PDF は埋め込みフォントが壊れ本文抽出不能 |
| 8 | Cooper, Harvey, Orford, Chiaradia 2018「Testing the ability of Multivariate Hybrid Spatial Network Analysis to predict the effect of a major urban redevelopment on pedestrian flows」(arXiv 1803.10500) | https://arxiv.org/abs/1803.10500 | ◎ | PDF 本文・Table 3 |
| 9 | 関・越智・岩舘・菊池・石神・茂木・石井 2018「滞在時間を考慮した回遊性向上施策の評価手法」土木計画学研究・講演集 57 | http://library.jsce.or.jp/jsce/open/00039/201806_no57/57-16-05.pdf | ◎ | PDF 本文・表-3 |
| 10 | 木崎・柳沼・大山・寺部・鈴木 2024「街路景観を考慮した歩行者経路選択モデルに基づく街路空間整備評価」土木学会論文集 80(20):24-20064 | https://www.jstage.jst.go.jp/article/jscejj/80/20/80_24-20064/_article/-char/ja/ | ◎ | PDF 本文・表-3 |
| 11 | Melnikov ほか 2022「Behavioural thermal regulation explains pedestrian path choices in hot urban environments」*Sci Rep* 12:2441 | https://doi.org/10.1038/s41598-022-06383-5 | ◎(抄録の数値) | PMC 抄録 |
| 12 | 「Exploring Sidewalk Sheds in New York City through Chatbot Surveys and Human Computer Interaction」(arXiv 2601.23095) | https://arxiv.org/abs/2601.23095 | ○(n = 25・画像上の選択) | PDF 本文 §4 |
| 13 | Olszewski & Wibowo 2005「Using Equivalent Walking Distance to Assess Pedestrian Accessibility to Transit Stations in Singapore」*TRR* 1927 | https://doi.org/10.3141/1927-05 | △(二次 = #2 の引用) | #2 §2 の記述 |
| 14 | 香港の横断(信号待ち vs 歩道橋/地下道)の表明選好 2023 *Transport Policy* | https://www.sciencedirect.com/science/article/abs/pii/S0967070X23001233 | △ | 検索要約のみ |

---

## §1 最短経路からどれだけ外れるか(問い 1)

- **#1 Bongiorno 2021**(ボストン・SF・スマホアプリの GPS)
  - 規模: 「GPS traces of 552,478 pseudo-anonymised human paths undertaken by 14,380 pedestrians in two major US cities – Boston and San Francisco」。前処理後は「165,645 trajectories by 4,879 pedestrians from Boston, and 189,075 trajectories by 7,372 pedestrians from San Francisco」(Methods)。
  - 向き: 「human paths recorded in our dataset were consistently longer than the shortest distance path」/「most of the relative deviation from shortest path is achieved by paths of length around 1 km, while only a modest further increasing deviation is observed for longer paths」(§Results)。
  - 分布の尾: 前処理で「a paths was not more than 80% longer than the shortest possible path … The 80% cutoff was taken as the 95% quantile」= **95% の経路は最短の 1.8 倍以内**。「excluded paths having their shortest network distance smaller than 200 meters」。
  - 非対称: 「chosen paths are statistically different when origin and destination are swapped」。
  - 型: **向きの一致(ベクトル)で経路を決める模型**が距離最小化+雑音より良く当てる。方向優勢率(DPF)は「68% at 150 m separation … to 53% at 1 Km separation」。
  - **外れの平均の比は図 1B にしか無い**(本文に数値なし)。検索要約が引く「約 9% 長い(迂回比 1.09)」は #2 系の二次で、**原典では照合できていない = ×**。
- **#2 Sevtsuk 2021(SF)**: 推定用の前処理で「we eliminated routes that deviated more than 50% longer than the shortest paths. The latter were deemed more likely to include additional stops」・「routes that were shorter than 200 meters … as well as routes longer than 1,000 meters」。= **「目的地へ向かう歩行」と「寄り道を含む歩行」を 1.5 倍で切っている**(散策モードの切れ目の先行)。
- **都市と目的による違い**: #5 Tong & Bode 2022 が「Tourists for sightseeing purposes may emphasize the quality of visual attraction … Commuters … tend to choose the shortest possible route without inclines」「hedonic shoppers like to stroll around … while utilitarian shoppers prefer more efficient routes」(§2.5.1・レビュー)。#4 Broach & Dill は「Joint travelers may prefer more direct routes than solo travelers」「no significant differences … for female pedestrians」(抄録・要約経由 = △)。
- **フロア**: 同じ SF で、経路の重なり補正(path size)の有無だけで距離換算が平均 17.7% 動く(#2 Table 3「Mean 17.7%」)。

## §2 角度変化の少ない道(問い 2)

| 出典 | 対象 | 逐語・値 | 等級 |
|---|---|---|---|
| #6 AIJ 2025 | 新宿・栄・名駅・梅田の主要動線(携帯位置データの歩行者数) | 「歩行者数と局所統合値の相関係数は-0.2 台から+0.3 台である」/「歩行者数と主要駅までの距離の相関係数の絶対値が0.3 台から0.6 台であるのに比べ、歩行者数と局所統合値の相関は弱い傾向となった」/ 距離との相関「西新宿では平日-0.350、休日-0.356、栄では平日-0.662、休日-0.593、名駅では平日-0.405、休日-0.367、梅田では平日-0.489、休日-0.460」/ R=400 m「平日：西新宿0.299、栄0.381」/ 梅田 R=1200 m「平日：0.028、休日：0.102」 | ◎ |
| #6 の先行の再掲 | ロンドン King's Cross ほか・イスラエル 4 都市 14 地区 | 「Hillier らは…軸線分析における統合値を市街地構成指標とし、歩行者数との相関係数が0.488 であることを報告」/ Omer ら 2015「局所統合値は歩行者数との相関係数が+0.3 台から+0.6 台の範囲」 | △(二次) |
| #7 上野・岸本 2008 | **渋谷駅**(複雑多層空間)・歩行者流動の実測+重回帰 | 抄録(要約経由): 経路選択に効く要因は「視野範囲の広さ」「ターン回数の少なさ」「最短距離で歩けること」 | △ |
| #8 Cooper 2018 | カーディフ中心部(英国)・角度/ユークリッドの混成距離の媒介+小売床面積 | 交差検証 r² 「0.49 including outliers」/ 翌年以降の予測「direct model is good at 0.72 in 2010」/ **フロア**: 前年の実測をそのまま使う null 模型の r² が **0.79(2008)・0.85(2009)・0.81(2010)・0.63(2011)**(Table 3) | ◎ |
| #1 Bongiorno 2021 | ボストン・SF | 角度の模型(ベクトル型)が距離最小化+雑音より良い(§1)。コスト例「P |θi|li = 400m·rad」 | ◎ |
| Hillier & Iida 2005(COSIT, LNCS) | ロンドン 4 地区 | **原典は取得できず**(UCL Discovery・JISCMail がボット対策で拒否)。角度 vs 距離の r² は **空欄** | × |

- **含意(サブの読み・未リサーチ)**: 日本の駅周辺では「駅からの距離(= OD 需要)」が「形の中心性」より強い。v2 は OD を個体の行き先として持つので、**統合値の場を別に入れる理由は弱い**。角度の効果は「曲がる回数」の重み(§3)で入る。**フロア**: 前年同地点の実測で r² 0.63〜0.85(#8)= 形の模型が 0.7 前後なら上限近い。

## §3 要素ごとの効き(離散選択の係数・距離換算)(問い 3)

### 3-1 SF の一次(#2 Table 3「Equivalent walking distance」・M4 = path size あり / M5 = なし)

| 要素 | 逐語(Table 3) | M4 | M5 | 差 |
|---|---|---:|---:|---:|
| 曲がる(45°以上の向き変化) | 「One extra turn along the route is perceived as:」 | **62.3 m** | 70.1 | 12% |
| 坂 | 「One meter of elevation gain along the route is perceived as:」 | **3.8 m** | 4.2 | 8% |
| 店(路面の店) | 「Passing one extra amenity is perceived as:」 | **−1.8 m** | −2.1 | 15% |
| 歩道幅 | 「A 10ft increase of avg sidewalk width along the route is perceived as:」 | **−83.7 m** | −82.8 | 1% |
| 空の見え率 | 「An average increase in SVF by 10% along the route is perceived as:」 | 8.1 m | 4.9 | 39% |
| 車速 | 「A 10mph increase in avg traffic speed along route is perceived as:」 | 56.3 m | 45.4 | 19% |
| 交通量 | 「A 1000 cars per hour increase in avg traffic volume along the route is perceived as:」 | 61.5 m | 79.5 | 29% |

- 条件: 「N = 14,760 traces」・2014-05〜2015-05・200〜1,000 m・曲がり 2〜7 回・迂回 50% 以内。「A turn is determined as at least a 45-degree change in direction along TIGER street centerlines」。適合「adjusted rho-squared of 0.679」。
- **有意でなかったもの**: 緑(GVI)「GVI also remained insignificant in M3 (robust t-statistic of -1.43)」・公共の芸術・高速道路沿い。
- **30 軒の店 = 54 m 短く感じる**(本文「A route that passes 30 amenities is perceived as 54 meters shorter」)。

### 3-2 曲がる回数の都市間の幅(フロア)

| 都市 | 1 回あたり | 出典 | 等級 |
|---|---:|---|---|
| サンフランシスコ | 62.3 m | #2 Table 3 | ◎ |
| ボストン | 34.4 m | #3(検索要約) | △ |
| ポートランド | 53.9 m / 約 50 m | #4(二次・値が 2 通り) | △ |
| トロント | 32.4 m | Lue 2017(検索要約の二次) | △ |
| **岡山(日本)女性** | 0.1598 / 0.0033 ≈ **48 m** [再計算] | #9 表-3(右左折回数 0.1598・t 2.9645 / 経路長(m) 0.0033・t 3.6203) | ◎(係数)/ 換算はサブ |
| **岡山(日本)男性** | 0.0594 / 0.0044 ≈ 13.5 m [再計算]・**t 0.9948 で有意でない** | #9 表-3 | ◎(係数) |

- 岡山の条件: 平成 27 年のプローブパーソン調査・中心市街地の「買い物」「散歩・回遊」の徒歩トリップ・選択肢は最短の 1.5 倍未満の 6 経路・男女別 MNL・初期対数尤度 185(男)/274(女)= **小標本**。
- **フロア = 32〜62 m(約 2 倍)**。日本の一次は岡山の女性 48 m が 1 本だけ。

### 3-3 横断・信号・階段

- **横断 1 回**: シンガポール「Crossing a single road, for instance, was found to be equivalent to extending the walk by 55m, while the presence of an elevated road crossing (with 32 ascending steps) was perceived as equivalent to extending the walk by 90 meters」(#2 §2 が #13 を引用 = △ 二次)。
- **信号のない幹線の横断**: ポートランド「over 70 metres」(#4 の検索要約の二次 = △)。
- **信号待ち**: 香港の表明選好「Pedestrians are more sensitive to an increase in waiting time at signalized crossings than to an increase in walking time to footbridges and underpasses」(#14・検索要約 = △)。**待ち 1 秒 = 歩き何秒 の比は取れなかった = 空欄**。
- **階段**: 上の「32 段の歩道橋 = 90 m」(二次)のみ。

### 3-4 屋根(雨天)・日陰

- **#12 NYC の足場(sidewalk shed)**: 「During normal weather, the majority of participants (81%) preferred the unsheltered side … Under harsh sunlight, shed-side use increased to 31.4%. Moreover, this pattern reversed in heavy rain: 74.4% of participants chose the shed side」。条件 = 「dataset (n = 25)」・画像上で歩道の側を選ぶ調査 = ○(実の歩行ではない)。
- **#11 シンガポールの日陰**: 「the distance walked in the shade is discounted by a factor of 0.86 compared to the distance walked in the sun, and that shadows cast by buildings have a stronger effect than trees」(抄録)。
- **香港の地下の歩行路**(Transport Geography 2024・検索要約 = △): 雨・暑さが天候から守られた地下経路を選ぶ主因。
- **日本**: 雨天の屋根/地下経路の選択率の一次は **見つからなかった = 空欄**(J-STAGE・土木学会の検索で表面化せず)。

### 3-5 混雑

- 札幌の LOS(歩道幅・障害物・他の歩行者の密度・自転車)で「people were consistently willing to choose longer paths when the overall LOS was higher」「the relative impact of LOS was notably higher on short routes」(#2 §2 が Muraleetharan & Hagiwara 2013 を引用 = △ 二次)。**密度そのものの距離換算は空欄**。v2 では混雑は所要時間(Weidmann の減速)として入るので、重みを別に足すかは感度腕で。

### 3-6 緑・店の並び(にぎわい)の日本の一次

- **#10 豊洲(東京)**: Recursive Logit・PP データ 311 人・「サンプル数 3340」・「対数尤度比 0.0910」。表-3「Treelen 0.242 t 3.61 **」(緑地の長さ = 正で有意)/「Shopsky 0.00275 t 0.0370」(店の見え = 有意でない)/「Closure −1.99 t −2.48 *」「Fencewidth −3.01 t −3.24 **」(圧迫感 = 負)/「Width −0.227 t −0.86」。本文「道路上の緑地の長さと建物が立ち並ぶ街路における樹木効果はポジティブに働く」。
- **#9 岡山**: 「商店街の比率(%)」女性 1.9840(t 2.7899)・男性 1.5586(t 1.8875)/「沿道の店舗の状況」女性 0.5132(t 1.6809)。本文「沿道に店舗が集積している道路，商店街が多い経路の方が選択されやすい」。**「比率(%)」の単位が 0〜1 か 0〜100 か本文から確定できない → 距離換算しない**。
- **割れ**: 緑は SF で有意でない(§3-1)が豊洲で有意。店は SF で有意(1.8 m/軒)・岡山で商店街の比率が有意・豊洲で店の見えが有意でない。

## §4 慣れた道と初めての人(問い 4)

- **#5 Tong & Bode 2022**(レビュー §2.5.2): 「pedestrians tend to follow exit routes they are familiar with … This preference for familiar routes can persist even when other available exits are closer」「when pedestrians are not familiar with an environment, they have to seek clues for their route choice. Landmarks [83], signs [84] and the movement of others [85]」/ §2.3「other people who are not familiar with a building may tend to follow the crowd」。**根拠は避難と建物内が中心**。
- **#2 SF**: 同じ人が同じ道を繰り返す分は「we eliminated all identical trajectories … many of the duplicate trajectories could be routinely walked by the same individual(s)」= **習慣の反復を意図的に除いて推定**している(= SF の係数は「慣れ」を含まない側)。
- **歩行者の「慣れた道」の距離換算・反復率の一次は見つからなかった = 空欄**。車・公共交通の習慣の研究(検索要約: 公共交通の通勤者は中央値で 4 トリップ中 3 が同じ経路)は歩行者に写さない。
- 既存: 場所の反復(Lu 2013 Π 0.88)= [D-68 残](v2-d68-remaining-research.md)。**経路の反復は別の量**。

## §5 散策・回遊(問い 5)

- **#9 岡山(PP 調査 平成 27 年)**: 回遊を「回遊継続選択・目的ゾーン選択・目的施設選択・経路選択・滞留時間選択」の段に分けた模型(本文)。経路選択の現況再現は「相関係数は0.99程度」(推定に使った実績データとの比較 = 標本内)。評価指標は「歩行者数だけでなく立ち寄り箇所数や歩行距離，滞在時間」。**立ち寄り箇所数・歩行距離の分布の数値は図のみで抽出できず = 空欄**。
- **#10 が引く 大山・羽藤**(二次): プローブパーソン調査で「現在歩行している街路景観と類似性が高い街路が選択されている」「逐次的な経路選択を活用して面的な回遊行動を記述できる可能性」= 散策モードを **交差点ごとの逐次選択(Recursive Logit)** で書く先行。
- **渋谷の回遊の一次**: 見つからなかった = 空欄。東京都 繁華街利用実態調査(平成 13 年・[R-52](v2-r52-crowd-model-calibration-shibuya-research.md) #25)は通行量と出向先で、立ち寄り回数は無い(本調査で PDF を再読して確認)。
- **切れ目の先行**: SF が「50% より長い = 寄り道を含む」で切り(#2)、ボストン/SF が 80% を 95 パーセンタイルとした(#1)。**散策モードへの切り替えを「最短比 1.5 超」で観測側から判定する**のは先行と同じ作法(サブ案・未リサーチ)。

## §6 地図アプリの案内に従う割合(問い 6)

- **#1 Bongiorno**: 「we compared human paths to paths planned by the most widely used routing app - Google Map. Results show that Google paths are significantly different from human paths」(Methods・長さ分布・Jaccard・Hausdorff)。= **人は案内経路どおりには歩いていない**(従う割合の数値は無い)。
- **従う割合の一次は見つからなかった = 空欄**。日本の地図アプリ利用率は民間の Web 調査(利用頻度・用途)だけで、徒歩で案内に従う割合は無い。関連: 待ち合わせの待機者の 8 割超がスマホ操作(一宮・松村 2026 = [C9 答申](v2-c9-position-attention-research.md) §1.6)。

## §7 未確認・空欄の一覧

1. 最短経路からの外れの平均比(#1 は図のみ・「1.09」は二次)。
2. Hillier & Iida 2005 の角度 vs 距離の r²(原典取得不能)。
3. ボストン 34.4 m・ポートランド 50〜53.9 m・トロント 32.4 m(二次)。#3・#4 の本文(有料・Cloudflare)。
4. 信号待ちの重み(待ち時間と歩行時間の比)。
5. 屋根(雨天)の距離換算・日本の雨天経路。
6. 混雑そのものの距離換算。
7. 慣れた道の距離換算・経路の反復率(歩行者)。
8. 人ごとの急ぎ(時間価値のばらつき)の歩行者の分布。
9. 渋谷の回遊(立ち寄り回数・歩行距離・滞在)。岡山の分布の数値(図のみ)。
10. 地図アプリの案内に従う割合。
11. 上野・岸本 2008(渋谷駅)の係数(PDF のフォント破損)。
12. 岡山「比率(%)」の単位。

## §8 まとめ表(要素 × 錨 × 値 × 条件 × 既定に入れてよいか)

「既定に入れてよいか」は **サブの判断 = 未リサーチ(expedient)**。決定は親とユーザー。

| 要素 | 錨 | 値 | 条件 | 既定に入れてよいか(サブ案) |
|---|---|---|---|---|
| 所要時間(距離/速度) | 既存(R-52) | v_f 1.34 m/s・密度で減速 | — | 既にコストの本体 |
| 曲がる回数 | **あり(一次 2 本+二次 3 本)** | 32〜62 m/回(SF 62.3・岡山女性 48) | 45° 以上の向き変化(SF) | **入れる**: 既定 ≈ 50 m/回(フロアの中ほど)・腕 30/65。日本の一次が小標本なので腕は必須 |
| 坂(登り) | あり(一次) | 1 m 登る = 3.8 m | SF | **入れる**(登りだけ・Broach「急な登りだけ効く」とも整合) |
| 歩道幅 | あり(一次) | 10 ft(3.05 m)広い = −83.7 m | SF | 入れてよい(道路 LOD3 で幅が取れてから) |
| 店(路面の店) | あり(一次・日本は商店街の比率が有意) | −1.8 m/軒 | SF | **散策モードに入れる**・目的地つき移動は 0+腕(R-47 の「目的で見る物が変わる」と整合) |
| 緑 | 割れる(SF 有意でない・豊洲 有意) | 換算値なし | — | 0+腕 |
| 交通量・車速 | あり(一次) | 1,000 台/h = 61.5 m・10 mph = 56.3 m | SF | 保留(車の層が無い) |
| 横断の回数 | 二次のみ | 55 m/回(シンガポール) | 駅へのアクセス | 0+腕(腕の値 55 m) |
| 信号待ち | 向きのみ(要約) | 空欄 | 香港 | **時間だけ入れる**(周期 140 s・R-52)・余分な重みは 0+腕 |
| 階段・縦の接続 | 二次のみ | 32 段の歩道橋 = 90 m | シンガポール | 時間(容量・待ち)で入れる・重みは 0+腕 |
| 混雑 | 向きのみ(二次) | 空欄 | 札幌 LOS | 時間(減速)で入れる・重みは 0+腕 |
| 屋根(雨天) | 向きのみ(○/△) | 大雨で屋根側 74.4%(n = 25)・日陰 0.86 倍 | NYC 画像・シンガポール | 0+腕(腕 = 屋根の区間を ×0.86 など・値は expedient) |
| 慣れた道 | 定性のみ | 空欄 | 避難・建物内 | 0+腕 |
| 人ごとの急ぎ | なし | 空欄 | — | 0+腕(目的別速度 R-52 A4 とは別) |
| 角度(統合値) | あり(日本は弱い) | 相関 −0.2〜+0.3 | 4 駅周辺 | **入れない**(曲がる回数で代える)・照合の指標としてだけ使える |
| 散策モードの切れ目 | 前処理の先行 | 最短の 1.5 倍(SF)/ 1.8 倍 = 95%(ボストン/SF) | — | 観測側の判定に使う |
| 地図アプリ | 向きのみ | 案内 ≠ 実経路 | ボストン/SF | 将来の口・既定なし |

---

## §9 INDEX に足す行の案(**本書では追記しない** — 親が入れる)

```
| 09-30 | [r61-route-choice-anchors](v2-r61-route-choice-anchors.md) | ~200 | **B** | 交通工学 #2 / 歩行者動力学 #18 / 地理情報科学 #9 | 経路選択の重みの錨(§1-4): 最短からの外れ(Bongiorno 2021・95% は 1.8 倍以内)・曲がる 1 回 = SF 62.3 m/岡山女性 48 m [再計算](フロア 32〜62 m)・坂 1 m = 3.8 m・店 1 軒 = −1.8 m・日本の駅周辺で統合値の相関は −0.2〜+0.3(AIJ 2025)・屋根/信号待ち/慣れ/急ぎ/渋谷の回遊/地図アプリは空欄 |
```
