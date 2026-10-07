# R-79 答申: 気づく要因と会話の距離(視力・親しさ・明るさ・遮るもの・注意の状態・2 段の分け方・近接学)

<!-- hdr:v1 -->
- **分野**: 知覚心理学・精神物理学 #5 / 歩行者動力学 #18 / 照明工学(防犯照明) / 社会心理学(近接学) | **重要度**: P1(指示書 [v2-wallbounce-decisions-2026-10-03](../design/v2-wallbounce-decisions-2026-10-03.md) §4-2「気づく確率」・§11 第 2 群「気づく要因と会話の距離」)
- **一次確認**: **B**(サブ実読。原典本文 13・一部推測 4・抄録/二次 11・未読 4・空欄は §9)・既存答申(R-62・p_notice・C9・R-78)との重複を避けて照合・親検収 済(第317・2026-10-03: Hyman 2010 の 25/51/71%・警察庁の 20/50/3 lx・Loftus & Harley の 43 ft は既知の値と一致。遮蔽の指数式と視力の距離換算は推測と明記されていることを確認。Burton 1999・Hahn 2016 の原典は親未読。等級 B+)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(PDF は WebFetch が保存したものをローカルの pymupdf で文字抽出)・コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係(引用だけで重ねない): 視野の外周 ±107°・知人 75% = 10.4 m / 25% = 23.5 m・見知らぬ人の再認(Nyman 2023)・スマホの文字と音声(Silva 2019)= [R-62](v2-r62-field-of-view-anchors.md) / 他の歩行者を注視する距離 中央値 10.3 m(昼 13.0・夜 8.9)・検出と識別の比 1:4(Johnson の基準からの導出)・夜の係数 0.68 = [p_notice 答申](v2-p-notice-research.md) / 選好距離 見知らぬ人 1.35 m・知人 0.92 m(Sorokowska 2017・日本なし)= [C9 答申](v2-c9-position-attention-research.md) §1.5 / 声の大きさ・距離の減衰・明瞭度・ロンバード効果 = [R-78](v2-r78-speech-propagation-intelligibility.md) / Fruin の LOS の境(A ≥ 35 sq ft/人・F ≤ 5)= [R-7](v2-crowd-physics-research.md)。本書は、これらで済んでいない要因(視力・親しさ・明るさ・遮るもの・注意の状態・2 段の分け方・会話の距離の原典と騒音)を足す。

## 結論(5 行)

1. **視力は、距離の物差しを縮める形で入れられる**。Loftus & Harley 2005 は、顔が 43 ft(13.1 m)で視角 1° になり、見える細かさ(周波数/顔)が距離に反比例して落ちることを式で示した。顔の識別に効く帯域としては 8〜16 周波数/顔を挙げている。ここから「視力 V の人は、距離を V 倍に縮めたのと同じ」と置ける(推測)。日本の分布の錨は、裸眼 1.0 未満が小学校 37.79%・中学校 60.93%・高校 67.80%(令和 5 年度)。成人は、運転免許の基準(矯正を含め両眼 0.7 以上)と、多治見の 40 歳以上のロービジョン 0.39〜0.98% しかない。成人の年代別の分布は空欄。
2. **親しさは「見分ける段」に効くが、効く量を距離で示した値は空欄**。よく知る人は、質の悪い防犯カメラの映像でもほぼ全員が当て、知らない人は外した(Burton ほか 1999・要約)。頭を隠すと大きく落ち、体や歩き方を隠しても少ししか落ちない。体による識別は距離で変わらず、顔は近いほど良くなる(Hahn ほか 2016・抄録)。来ると分かっている相手は約 1.32 倍遠くから見分けられる(R-62 の Loftus & Harley の 24.5% から再計算)。親しい人を後ろ姿で何 m から見分けられるかの一次は見つからなかった。
3. **明るさの錨は、日本の公的基準 2 本と実験 3 本がある**。警察庁の要綱は、10 m 先の人の顔と行動が識別できる明るさを 20 lx、明確に識別できる明るさを 50 lx、4 m 先の人の挙動と姿勢が分かる明るさを 3 lx とする(平均水平面照度)。防犯設備協会は、4 m 先の顔の概要が分かる明るさを 5 lx とする。Rombauts 1989 は、半円筒面照度 0.4 lx で 4 m、3.0 lx で 10 m 先の人を識別でき、20〜25 lx で頭打ちになるとした(Lin & Fotios 2015 による要約)。渋谷の街路の照度の実測は空欄。
4. **遮るものは「視線の通り道に人が 1 人もいない確率」で近似できる**。人を円柱と見る通信工学のモデルでは、見通せる確率は exp(−密度 × 遮る幅 × 距離)の形になる(Gapeyenko ほか 2016 の考え方からの推測)。遮る幅 0.5 m・距離 10 m で計算すると、0.31 人/m²(Fruin の LOS A の境)で 0.21、1 人/m² で 0.007 になる(推測)。目の高さでは頭だけが遮るので、幅はもっと小さい可能性がある。群衆の中で人と人の見通しを人で測った一次は空欄。
5. **注意の状態は乗数で入れられ、連れと話しながら歩く人の気づきは下がらない**。歩きながら通話していた人で一輪車のピエロに気づいたのは 25%、一人で歩いていた人は 51%、2 人連れは 71% だった(Hyman ほか 2010)。トレッドミルで歩きながら文字を打つと、画面の外の合図の 48.3% を見落とした(Lim ほか 2015・抄録)。急いでいる人の気づきを測った一次は無く、Darley & Batson 1973 の援助率(10% と 63%)は気づきの値ではない。会話の距離は、Hall の社会距離の近い側が 1.2〜2.1 m(二次)、西出の会話域が 0.5〜1.5 m(二次)で、11a の 2 m はこの両方を覆う。騒音が 1 dB 上がると、立ち話の 2 人は 2.0 cm 近づく(Miles ほか 2023)。

---

## §0 出典の表

等級: **◎** 原典本文で数値まで逐語確認 / **○** 一部推測を含む(要約モデル経由の逐語・本人以外の再掲・査読なし)/ **△** 抄録・二次 / **×** 未読(空欄)。**[再計算]** はサブの計算、**(推測)** はサブの試算。

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | 文部科学省「令和 5 年度学校保健統計(学校保健統計調査の結果)確定値」2024-11-27 | https://www.mext.go.jp/content/20241127-mxt_chousa02-000038854_1.pdf | ◎ | PDF 全文(調査内容・ポイントの表) |
| 2 | Iwase A ほか 2006「Prevalence and causes of low vision and blindness in a Japanese adult population: the Tajimi Study」Ophthalmology 113(8):1354-62 | https://doi.org/10.1016/j.ophtha.2006.04.022 | △ | 抄録(Europe PMC 経由の要約と検索要約) |
| 3 | 日本眼科医会「日本における視覚障害の社会的コスト」2009(研究班報告 2006〜2008 の公表資料) | http://www.gankaikai.or.jp/info/20091115_socialcost.pdf | ◎ | PDF 全文(定義・人数・年代) |
| 4 | 道路交通法施行規則 第 23 条(適性試験)(e-Gov 法令 API) | https://laws.e-gov.go.jp/law/335M50000002060 | ◎ | 条文 |
| 5 | Loftus G.R. & Harley E.M. 2005「Why is it easier to identify someone close than far away?」Psychon Bull Rev 12(1):43-65 | https://faculty.washington.edu/gloftus/Downloads/LoftusHarleyDistance.pdf | ◎ | 著者 PDF の式 1〜2 の節・図 5 の説明 |
| 6 | Burton A.M., Wilson S., Cowan M., Bruce V. 1999「Face recognition in poor-quality video: Evidence from security surveillance」Psychol Sci 10(3):243-248 | https://doi.org/10.1111/1467-9280.00144 | △ | 抄録の検索要約。条件別の正答率は未読 |
| 7 | Bruce V., Henderson Z., Newman C., Burton A.M. 2001「Matching identities of familiar and unfamiliar faces caught on CCTV images」J Exp Psychol Appl 7(3):207-218 | http://www.jonathandnelson.com/Bruceetal2001JEPApplied.pdf | ○ | PDF 本文の序論(#6 の再掲) |
| 8 | Hahn C.A., O'Toole A.J., Phillips P.J. 2016「Dissecting the time course of person recognition in natural viewing environments」Br J Psychol 107:117-134 | https://doi.org/10.1111/bjop.12125 | △ | 抄録(Europe PMC 経由の要約) |
| 9 | Cutting J.E. & Kozlowski L.T. 1977「Recognizing friends by their walk」Bull Psychon Soc 9(5):353-356 | https://doi.org/10.3758/BF03337021 | △ | 抄録と、後発論文による 38% の再掲(検索要約) |
| 10 | 日本防犯設備協会 技術標準 SES E1901-4「防犯灯の照度基準」2015 年改正 | https://ssaj.or.jp/pubdoc/pdf/sese/E1901-4.pdf | ◎ | PDF 全文(表 1・解説) |
| 11 | 警察庁「安全・安心まちづくり推進要綱」の改正通達(警察庁丙生企発第 38 号・令和 2 年) | https://www.npa.go.jp/laws/notification/seian/seiki/R020317_youkoukaisei.pdf | ◎ | PDF 全文の注 1〜4(照度の定義) |
| 12 | Lin Y. & Fotios S. 2015「Investigating methods for measuring face recognition under lamps of different spectral power distribution」Lighting Res Technol 47(2)(著者稿) | https://eprints.whiterose.ac.uk/id/eprint/85180/ | ◎ | 著者稿 PDF の序論(Rombauts と 4 m の由来) |
| 13 | Rombauts P., Vandewyngaerde H., Maggetto G. 1989「Minimum semicylindrical illuminance and modelling in residential area lighting」Lighting Res Technol 21(2):49-55 | https://doi.org/10.1177/096032718902100201 | △ | 抄録の検索要約と #12 の要約 |
| 14 | Yang B. & Fotios S. 2015「Lighting and recognition of emotion conveyed by facial expressions」Lighting Res Technol 47(8):964-975 | https://eprints.whiterose.ac.uk/id/eprint/93526/ | ◎ | PDF 抄録・結果 |
| 15 | 東京都街路照明基準(昭和 21 年告示第 458 号) | https://www.reiki.metro.tokyo.lg.jp/reiki/reiki_honbun/g101RG00001209.html | ○ | 例規集の本文(要約モデル経由の逐語) |
| 16 | Gapeyenko M. ほか 2016「Analysis of human-body blockage in urban millimeter-wave cellular communications」IEEE ICC 2016 | https://arxiv.org/abs/1604.04743 | ◎ | arXiv PDF 本文(モデル・表 II) |
| 17 | Hyman I.E. Jr ほか 2010「Did you see the unicycling clown? Inattentional blindness while walking and talking on a cell phone」Appl Cognit Psychol 24:597-607 | https://doi.org/10.1002/acp.1638 | ◎ | PDF 全文(表 1・表 2・方法) |
| 18 | Simons D.J. & Chabris C.F. 1999「Gorillas in our midst: sustained inattentional blindness for dynamic events」Perception 28:1059-1074 | https://doi.org/10.1068/p281059(著者 PDF = chabris.com) | ◎ | PDF 本文の結果 |
| 19 | Lim J., Amado A., Sheehan L., Van Emmerik R.E.A. 2015「Dual task interference during walking: The effects of texting on situational awareness and gait stability」Gait Posture 42(4):466-471 | https://doi.org/10.1016/j.gaitpost.2015.07.060 | △ | 抄録(Europe PMC 経由の要約) |
| 20 | 小塚一宏「見えてない!『歩きスマホ』◆実験データで検証」時事ドットコム 2022(本人の寄稿) | https://www.jiji.com/jc/v8?id=2022arukisumaho-shakaibuhatu | ○ | 寄稿の本文(要約モデル経由の逐語・査読なし) |
| 21 | ソフトバンクニュース「ながらスマホ(歩きスマホ)の危険性を視線計測で検証」2019-11-01 | https://www.softbank.jp/sbnews/entry/20191101_01 | △ | 記事本文(小塚氏の談話の伝聞) |
| 22 | Darley J.M. & Batson C.D. 1973「From Jerusalem to Jericho」J Pers Soc Psychol 27(1):100-108 | https://doi.org/10.1037/h0034449 | △ | 検索要約のみ |
| 23 | Hall E.T. 1963「A system for the notation of proxemic behavior」American Anthropologist 65(5):1003-1026 | https://doi.org/10.1525/aa.1963.65.5.02a00020 | ◎ | 公開されている JSTOR 版 PDF の声の大きさの節(段組の右端が欠けた抽出) |
| 24 | Hall E.T. 1966『The Hidden Dimension』 | (書籍。archive.org の全文は貸出制限) | △ | 二次(Brown「CSISS Classics」・Wikipedia「Proxemics」の検索要約) |
| 25 | Miles K. ほか 2023「Behavioral dynamics of conversation, (mis)communication and coordination in noisy environments」Sci Rep 13:20271 | https://doi.org/10.1038/s41598-023-47396-y(PMC10662155) | ○ | PMC 本文(要約モデル経由の逐語) |
| 26 | 井上京子 2025「ソーシャル・ディスタンスの世界統一基準がもたらしたコミュニケーション時対人距離の変化」社会言語科学 28(1):159-169 | https://www.jstage.jst.go.jp/article/jajls/28/1/28_159/_pdf | ◎ | PDF 本文 §2.1〜2.2(西出 1985 の再掲) |
| 27 | 西出和彦 1985「人と人との間の距離」建築と実務 No.5:95-99 | https://cir.nii.ac.jp/crid/1573387450637909632 | × | 書誌のみ。「相互認識域 3〜20 m」は検索要約(Wikipedia「パーソナルスペース」ほか)の二次 |
| 28 | Kendon A. & Ferber A. 1973「A description of some human greetings」(Michael & Crook 編『Comparative Ecology and Behaviour of Primates』) | (書籍の章) | △ | 後発のロボット研究の総説の再掲(検索要約) |
| 29 | Jarudi I.N. ほか 2023「Recognizing distant faces」Vision Res 205:108184 | https://doi.org/10.1016/j.visres.2023.108184 | △ | 抄録(Europe PMC 経由の要約) |
| 30 | 角舘政英 2008 博士論文「街路空間における防犯性・安全性を高めるための照明環境に関する研究」 | http://bonbori.com/dr/dr.pdf | × | 取得できず(容量超過) |
| 31 | 松本隆太郎・金利昭 2013「街路照明における照度と視認性に関する基礎的研究」土木計画学研究・講演集 48 | http://library.jsce.or.jp/jsce/open/00039/201311_no48/pdf/7.pdf | × | 取得できず(接続拒否) |
| 32 | 伊藤ほか 1997「繁華街における光環境と『顔の見え』に関する研究」日本建築学会大会学術講演梗概集 | (未特定) | × | #30 の参考文献に名前があるだけ |

---

## §1 視力の分布と、視力から見分けられる距離を出す式(問い 1)

### 1-1 日本の視力の分布

- **子ども(裸眼)**(#1・逐語): 「裸眼視力1.0 未満の者の割合は、小学校で３割を超えて、中学校では約６割、高等学校では７割近くとなっています」。ポイントの表の令和 5 年度の値は、幼稚園 22.92%・小学校 37.79%・中学校 60.93%・高等学校 67.80%。条件は「満５歳から17 歳まで」の抽出調査で、健康状態は「25.2％（ 3,209,192 人）」。調査期間を年度末まで延ばしたため「過去の数値と比較することはできません」。区分別(0.3 未満など)と年齢別の値は e-Stat の詳細表にあり、本書では未取得(空欄)。
- **成人(矯正後の下限)**: 運転免許の適性試験(#4・逐語)は普通免許などで「視力（万国式試視力表により検査した視力で、矯正視力を含む。以下同じ。）が両眼で〇・七以上、かつ、一眼でそれぞれ〇・三以上」、大型・二種で「両眼で〇・八以上」。免許を持つ人は矯正を含めて 0.7 以上ある、という構造上の錨になる。
- **成人(視覚障害の側)**: 多治見スタディ(#2・抄録)は 40 歳以上 2,977 人の最高矯正視力で、ロービジョンが WHO 基準 0.39%・米国基準 0.98%、失明 0.14%。女性と高齢側で高い。日本眼科医会(#3・逐語)は「2007年の時点で本邦には、164万人の視覚障害者」「視覚障害者の半数は70歳以上、72％が60歳以上」。定義は「視覚障害全体（良い方の視力＜0.5）」「ロービジョン（0.1＜良い方の視力＜0.5）」「失明（良い方の視力≦0.1）」。
- **成人の裸眼・矯正視力の年代別の全国分布**は見つからなかった(空欄)。多治見の年代別の表は本文にあり未読。

### 1-2 視力と見分けられる距離の式

- **Loftus & Harley 2005 の式**(#5・逐語): 「Because 43 ft is the approximate distance at which a face subtends 1 deg, it is clear that f=F*(43/D) where D is the face's distance from the observer.」 ここで f は周波数/顔、F は周波数/度。顔の大きさは高さで定義している(「we define face size as face height」・幅は高さの約 3/4)。
  - 目の通す上限の例(逐語): 「assume a low-pass MTF that approaches zero around F = 30 cycles/deg」「at a distance of 172 feet, details smaller than about (1/30)x4 = 2/15 of the face's extent will be lost」。
  - 顔の識別に効く帯域(逐語): 「between 8 and 16 cycles/face, an approximation of which has been suggested as being important for face recognition (e.g., Morrison & Schyns, 2001)」。
  - 識別と再認を分ける倍率(抄録の要旨): 2 つの課題は「same general mathematical description but that differ in scale by a factor of approximately 0.75」。
- **視力を入れる形(推測)**: 小数視力 V = 1.0 は最小分離角 1 分で、通せる上限はおよそ 30 周波数/度に当たる。視力 V の人の上限を 30·V 周波数/度と置くと、上の式から「距離 d を d/V に置き換える」のと同じになる。つまり 11a の曲線の距離を d/V にすれば、視力が入る。例: V = 0.5 の人は、75% で見分けられる距離が 10.4 m から 5.2 m になる [再計算]。この置き方は L&H の「距離はフィルタと同じ」という仮説の延長で、視力ごとに見分けの距離を測った一次は見つからなかった(空欄)。
- **遠くでは輪郭と髪が効く**(#29・抄録): 距離が増えると、目・鼻・口の配置より「relationships between these features and external head contours」が識別に効く。距離の m 単位の値は抄録に無い(空欄)。

## §2 親しさと見分け(問い 2)

- **よく知る人は質の悪い映像でも当たる**(#6・抄録の要約・#7 の再掲): #7 の序論(逐語)「Participants familiar with the items used in this study performed almost perfectly at the task, whereas people unfamiliar ...」。#6 の実験 2 は、頭・体・歩き方をそれぞれ隠した映像で、頭を隠すと識別が大きく落ち、体や歩き方を隠しても少ししか落ちなかった(抄録の要約)。**条件別の正答率は未読(空欄)**。
  - 含意(サブの読み): 親しい人でも決め手は顔。後ろ姿で顔が見えないときの見分けは、体や歩き方の手がかりに頼るので、顔が見えるときより弱いと読める。
- **体の手がかりは距離で落ちにくい**(#8・抄録の要約): 体による識別は距離にかかわらず安定し、顔による識別は近いほど良い。体が独立に効いたのは一番遠い距離だけ。距離の m の値は未読(空欄)。R-62 の検索要約では刺激は約 13 m 先から近づく映像(二次)。
- **歩き方だけで友人を当てる**(#9・二次): 光点だけの映像で、6 人の友人から当てた正答は 38%(偶然は 1/6 = 16.7% [再計算])。原典の本文は未読。
- **来ると分かっている相手**(R-62 #4 の逐語「24.5%±6.4% smaller」から): 見分けられる像の大きさが 24.5% 小さくてよい = 距離にして 1/(1 − 0.245) = **1.32 倍** [再計算]。待ち合わせの相手や、ふだん同じ場所で会う相手に当てはまる。
- **依頼にあった「Hahn ほか 2016 の 100 m 超」**: 該当する記述は見つからなかった(空欄)。
- **親しさで見分けの距離が何倍になるかの一次は見つからなかった(空欄)**。顔写真の模擬距離(L&H)は有名人(よく知る顔)で測った値で、11a の 10.4 m / 23.5 m は、すでに「知っている顔」の値である点に注意。

## §3 明るさと見分け(問い 3)

### 3-1 日本の公的基準

- **警察庁の要綱**(#11・逐語): 「（注１）「人の顔及び行動を明確に識別できる程度以上の照度」とは、10 メートル先の人の顔、行動が明確に識別できる程度以上の照度をいい、平均水平面照度（床面又は地面における平均照度。以下同じ。）がおおむね50 ルクス以上のものをいう。」/「（注２）「人の顔及び行動を識別できる程度以上の照度」とは、10 メートル先の人の顔及び行動が識別できる程度以上の照度をいい、平均水平面照度がおおむね20 ルクス以上のものをいう。」/「（注３）「人の行動を視認できる程度以上の照度」とは、４メートル先の人の挙動、姿勢等が識別できる程度以上の照度をいい、平均水平面照度がおおむね３ルクス以上のものをいう。」 通達の表紙の有効期間は「令和7年3月31日まで」で、現行版かは未確認。
- **防犯設備協会**(#10・逐語): 表 1「A 4 m 先の歩行者の顔の概要が識別できる 5 lx 以上 1 lx 以上」「B 4 m 先の歩行者の挙動・姿勢などがわかる 3 lx 以上 0.5 lx 以上」(平均水平面照度・道路中心線上の鉛直面照度の最小値)。解説「観測距離4mにおいて、鉛直面照度1lx以上の照度で目、鼻、口の位置など「顔の概要」がわかることが確認できる」。図 1 の出典は「街路照明の適正化に関する調査分析（その2）…昭和62年3月(社）照明学会関西支部」。
  - 注意: 依頼文の「4 m 先の人の顔・行動が識別できる 3 lx」は、両基準とも「挙動・姿勢」の段で、顔の概要は 5 lx(協会)、顔の識別は 10 m で 20 lx(警察庁)。
- **東京都街路照明基準**(#15・昭和 21 年): 商業地域で幅員 20 m 以上・11〜20 m が 1.5 lx 以上、店舗地区 2.0 lx 以上、消費歓興地区 5〜10 lx 以上。古い基準で、今の渋谷の実際の明るさとは別物。

### 3-2 実験

- **Rombauts 1989**(#13・△ / #12 の逐語): 「their results suggest a non-linear relationship between semi-cylindrical illuminance (ESC) and identification distance, with 0.4 lx required for identification at 4 m, approximately 3.0 lx for identification at 10 m, and an asymptote of around 20 lx to 25 lx beyond which higher ESC did not lead to better recognition.」 原典の抄録(検索要約)では 4 m の推奨最小値が 0.6 lx、頭打ちの距離は「physiological limit at 17 m」。#12 は 4 m の由来について「4 m might not be a well-founded nor precise estimate」と書く。
  - フロア: 同じ原典でも、要約によって 4 m の値が 0.4 lx(曲線の読み)と 0.6 lx(推奨値)で 1.5 倍違う。
- **Yang & Fotios 2015**(#14・逐語): 「A luminance of 1.0 cd/m2 permits facial expressions to be identified with a 50% probability of correct identification at a distance of 15 m.」/「At luminances in the range 0.01–0.10 cd/m2, facial expression recognition at 15 m was no better than chance level.」 4 m では 0.33 cd/m² 以上で正答が約 83.3% の頭打ち。これは表情の判定で、知人の識別ではない。値は顔の輝度(cd/m²)で照度ではない。
- **既存**: 他人を注視する距離は昼 13.0 m・夜 8.9 m(比 0.68)= p_notice 答申。
- **含意(サブの読み)**: 明るさの効き方は「暗いと見分けの距離が縮み、20〜25 lx より明るいと変わらない」形で、頭打ちの 17 m は 11a の曲線の 50% 点(16.95 m [再計算])と近い。渋谷の繁華街の夜は、大型ビジョンや店の明かりで頭打ちの側にいる場所が多いと考えられるが、**渋谷の街路の照度の実測は見つからなかった(空欄)**。

## §4 遮るもの(問い 4)

- **人を円柱と見るモデル**(#16・逐語): 「We model the blockers as cylinders [8] with a certain height, H, and the base diameter of D.」/「The centers of cylinder bases follow a Matern hard-core point process on the plane with the intensity λI.」/「the Matern process can be replaced by the equivalent Poisson process for a wide range of intensities λI.」 視線を遮れるのは、その位置で視線より背の高い人だけ(式 1: λ(x) = λI·g(x), g(x) = Pr{H > hm(x)})。表 II の値は「Height of a blocker … N(1.7m, 0.1m)」「Diameter of a blocker, U(dmin, dmax) U(0.2m, 0.8m)」「Initial intensity of blockers 0.3 blockers/m2」。結果は「Blockage probability rises with both human density and Tx–Rx separation」(抄録の要旨)。
- **人と人の見通しに当てはめた式(推測)**: 見る人と見られる人の目の高さがほぼ同じなら、間の人のうち視線より背の高い人の割合 g、遮る幅 w、密度 ρ(人/m²)、距離 d として、見通せる確率 ≈ exp(−ρ·g·w·d)。g = 1 として計算した例 [再計算]:

| 密度 ρ(人/m²) | w = 0.2 m: 2 / 5 / 10 / 20 m | w = 0.5 m: 2 / 5 / 10 / 20 m |
|---|---|---|
| 0.1 | 0.96 / 0.90 / 0.82 / 0.67 | 0.90 / 0.78 / 0.61 / 0.37 |
| 0.31(Fruin LOS A の境) | 0.88 / 0.73 / 0.54 / 0.29 | 0.73 / 0.46 / 0.21 / 0.05 |
| 1.0 | 0.67 / 0.37 / 0.14 / 0.02 | 0.37 / 0.08 / 0.01 / 0.00 |
| 2.15(LOS F の境) | 0.42 / 0.12 / 0.01 / 0.00 | 0.12 / 0.01 / 0.00 / 0.00 |

  - w の値: 目の高さでは肩より上の頭だけが遮るので、肩幅(0.5 m 前後)より頭の幅に近い可能性がある。**頭の幅と、目の高さで有効な遮る幅の値は本書で取っていない(空欄)**。背の高い人は人越しに見え、低い人は見えにくい(g が見る人の身長で変わる)ので、身長(人ごとの性質)が遮蔽に効く(推測)。
  - 既存: p_notice 答申は群衆の遮蔽を「解析式(密度→遮蔽係数)で近似するしかない」とし、遮蔽度 4 段の分類は検索要約のみ。本書の式はその解析式の候補。
- **群衆の中で人と人の見通しを人で測った一次は見つからなかった(空欄)**。Fujiyama 2006 の「awareness area」の作業論文は書誌のみ(未読)。
- **建物の角**: 幾何の判定(視線が建物の多角形と交わるか)で足り、文献の値は要らない。指示書の G13 の視線の遮蔽の表と W8 の建物の形で入れる。

## §5 注意の状態(問い 5)

- **通話・音楽・連れ・一人**(#17・逐語): 表 2「General question 8.3 / 32.1 / 32.1 / 57.1」「Did you see the clown? 25.0 / 51.3 / 60.7 / 71.4」(通話・一人・音楽・2 人連れの順、%)。本文「Only 25% of the cell phone users had noticed the clown … In essence, 75% of the cell phone users experienced inattentional blindness」。条件: 大学の広場・晴れた春の午後 1 時間・「We interviewed 151 individuals」(一人 78・通話 24・音楽 28・2 人連れ 21)。研究 1(317 人)の表 1: 方向転換 通話 29.8%・一人 4.7%、他人への会釈 通話 2.1%・一人 11.6%、ニアミス 通話 4.3%・一人 0.0%、横断時間 通話 82.53 s・一人 74.81 s。
  - 2 人連れについて(逐語): 「Their rate of seeing the clown is essentially equal to what one would expect by combining the performance of two individuals.」= **連れと話しながら歩くと、1 人あたりの気づきが下がるとは言えない**(面接したのは近い側の 1 人)。
  - 乗数 [再計算]: 通話 25.0/51.3 = **0.49**(直接の問い)・8.3/32.1 = 0.26(自発の報告)。音楽 60.7/51.3 = 1.18(差は有意でない扱いでよいかは未確認)。
- **文字を打ちながら歩く**(#19・抄録): 20 人・トレッドミル・「nearly half of visual cues "were not perceived (48.3%)"」。視野が広い課題ほど、細かさが要る課題ほど見落としが多い。乗数にすると 1 − 0.483 = 0.52 [再計算]。条件別の値は未読(空欄)。
- **「歩きスマホで視野が 20 分の 1」**(#21・#20): ソフトバンクの記事の談話「画面を凝視している状態では、視界が20分の1になるという実験結果があります。つまり95%も視野を失っているんです」。本人の寄稿(#20)には 20 分の 1 の値は無く、測った量は視線の動く範囲(通常歩行は「視線の移動範囲が左右３mずつ合わせて６m位」、ツイッター歩行は「左右には全く視線が移動しない」)。横断歩道(約 23 m)を渡る速さは「通常歩行に比べて約２０～３０％遅く」。**「20 分の 1」は視線の動く範囲の比を言い換えた値の可能性があり、視野の角度として使える一次ではない**(サブの読み)。
- **課題の難しさ**(#18・逐語): 「Out of all 192 observers across all conditions, 54% noticed the unexpected event and 46% failed to notice」「More observers noticed the unexpected event in the Easy (64%) than in the Hard (45%) condition」= 頭の負荷が重いと 45/64 = 0.70 倍 [再計算]。p_notice 答申で空欄だった Easy/Hard の内訳はこれで埋まる(**伝播の対象**: p_notice の 4-2 と「補足: 親が追加で潰すべき空欄」)。
- **急いでいる**(#22・二次): 援助した割合は、急がない 63%・中くらい 45%・急ぐ 10%(検索要約・原典未読)。これは助けたかどうかで、気づいたかどうかではない。**急いでいるときの気づきの低下を測った一次は見つからなかった(空欄)**。
- **既存との関係**: Silva 2019(文字は接近の検出を遅らせ、音声は遅らせない)= R-62。Hyman の通話(見落とし 75%)と Silva の音声(遅れない)は課題が違う(R-62 の読み)。本書の Hyman 表 2 で、通話の乗数 0.49 を錨にできる。

## §6 2 段の分け方: 「誰かがいる」と「知り合いだと見分ける」(問い 6)

- **既存の錨**: 視野の外周 ±107° で検出、文字の再認は直径 46° × 32°(R-62)。検出に要る細かさは識別の約 1/4(Johnson の基準からの導出・p_notice 答申)= 同じ明るさなら、検出は識別の約 4 倍の距離まで届く(導出・一次ではない)。
- **知り合いを見分ける段の値**: 11a の 75% 10.4 m / 25% 23.5 m(R-62・有名人の写真)。日本の建築計画では西出 1985 の「相互認識域 3〜20 m」(知り合いかどうかが分かり、表情も分かる距離・挨拶が起きる距離。特に 3〜7 m では知り合いを無視できない)が広く引かれるが、**原典は未読で二次(#27)**。L&H の 25% 点(23.5 m)と西出の外側(20 m)は近い。
- **挨拶の段**(#28・二次): Kendon & Ferber 1973 は、互いを見つける → 遠くからの挨拶 → 近づく → 近くでの挨拶、の段に分けた。最後の近づきは 2 人が 3.5 m より近いとき(後発の総説の再掲)。原典の距離の値は未読(空欄)。
- **含意(サブの読み)**: 段 1「誰かがいる」は昼の街路では距離より視野と遮るもので決まり、段 2「知り合いだ」は距離・視力・明るさ・親しさで決まる、という分け方が既存の錨と合う。**歩行者が別の歩行者の存在に気づく距離を直接測った一次は見つからなかった(空欄)**。

## §7 会話の距離(近接学)(問い 7)

- **Hall 1966 の 4 区分**(#24・二次): 親密 近 0〜15 cm・遠 15〜46 cm / 個体 近 46〜76 cm・遠 76〜120 cm / 社会 近 1.2〜2.1 m(4〜7 ft)・遠 2.1〜3.7 m(7〜12 ft)/ 公衆 近 3.7〜7.6 m・遠 7.6 m 超(Wikipedia「Proxemics」の検索要約。CSISS の解説(#24 の写し)は「people engaged in conversation will assume a social distance of roughly 4–7'」)。**原典の逐語は未確認(空欄)**。
  - C9 答申 §3 の 6 の「Sorokowska の再掲は社会 122〜210 cm で、依頼文の 3.6 m と帯が違う」という食い違いは、**Sorokowska が社会距離の近い側(close phase)だけを書いた**と読むと解ける(推測。原典で確認が要る)。
- **Hall 1963 と声と騒音**(#23・逐語): 「The loudness of the voice is modified to conform to culturally prescribed norms for a) distance, b) relationship between the parties involved, and c) the situation or subject being discussed.」 声の大きさの 7 段(silent 0・very soft 1・soft 2・normal 3・normal+ 4・loud 5・very loud 6)。騒音について、抽出した本文には「Research in proxemics has been restricted to cu…」「…as noise level, temperature, and personality variab…」とあり(段組の右端が欠けた抽出)、Hall 自身は騒音の効果を測っていないと読める(○)。
- **騒音で距離が変わる実測**(#25・逐語): 「Data of 44 participants in 22 pairs were analyzed.」 立ち話は「pairs began by standing in front of each other at a distance of 2.5 m」から始めた。背景の騒音は 53 dB SPL(図書館)から 92 dB SPL(音楽のあるパーティー)までの 7 段。距離の変化は「0.70 cm … when seated」「2.0 cm … when standing, for every 1 dB increase in the level of background noise」。声は「speech levels increased by a mean of 0.32 dB … for every 1 dB increase in background noise level」。「Approximately 78 dB SPL defined a threshold where behavioral processes were no longer sufficient」。会話が途切れると「pairs moved 5 cm closer, and the talkers' speech levels increased by 3.2 dB」。
  - [再計算] 53 → 92 dB(39 dB)で、立ち話は 39 × 2.0 = 78 cm 近づく(始めの 2.5 m からの変化。絶対の距離は図だけで本文に無い = 空欄)。
  - **既存との食い違い(併記)**: R-78 のロンバード効果は「背景 1 dB あたり声が約 0.5 dB 上がる」(Rindel の式)。本書の実測は 0.32 dB/dB。測り方(会話する 2 人の自然な声 vs 飲食店の式)が違う。どちらを使うかは R-78 の側で宣言が要る(**伝播の対象**)。
- **日本人の値**(#26・逐語・西出 1985 の再掲): 「日本人にとって会話が成立するのはpersonal distance に当たる会話域5 cm～150 cm，そして気づまりを感じない程度の距離は近接域150 cm～300 cm」。「5 cm」は他の二次(会話域 50 cm〜1.5 m・排他域 50 cm 以下)と合わず、誤記の可能性がある(サブの読み)。**西出 1985 の原典は未読(空欄)**。Sorokowska 2017 は日本を含まない(C9 答申)。
- **渋谷のような雑踏での会話の距離の実測**・**立ち話を始める距離の実測**・**F-formation(Kendon)の o 空間の寸法の実測**は、いずれも見つからなかった(空欄)。

## §8 v2 への当てはめ(親の案として明記・すべて未決)

以下は**サブの試算と親への提案**で、決定ではない。係数は錨のあるものと空欄を分けて書く。

### 8-1 11a の曲線(既決の形)の確認

- 2 点(10.4 m で 0.75・23.5 m で 0.25)を通るロジスティック: p(d) = 1 / (1 + exp((d − 16.95) / 5.96)) [再計算: 50% 点 = (10.4 + 23.5)/2 = 16.95 m、尺度 = 6.55 / ln 3 = 5.96 m]。2 m で 0.925・5 m で 0.88・30 m で 0.10・40 m で 0.02 [再計算]。近くでも 1 にならない(2 m で 0.925)点は、写真の模擬距離の実験の天井の影響もありうるので、11a で上限を 1 に寄せるかは宣言が要る。

### 8-2 段 3 の式の候補(推測)

```
段 1(誰かがいると気づく)
  P_detect = 視野(θ) × 見通し(ρ, w, d) × 注意(状態)
    視野(θ)   = |θ| ≤ 107° なら 1、それより後ろは 0          # R-62(錨あり)
    見通し    = exp(−ρ·g·w·d)                               # 本書 §4(形は錨あり・w は空欄)
    注意      = 一人 1.0 / 通話 0.49 / 文字 0.52 / 連れ 1.0 以上 / 重い考えごと 0.70 / 急ぐ 空欄
段 2(知り合いだと見分ける)= 段 1 を通った後だけ判定
  P_recog = 1 / (1 + exp((d_eff − 16.95) / 5.96))
    d_eff = d / (V × 明るさ(E) × 予期 × 親しさ)
      V        = 人ごとの視力(小数視力)                       # §1-2(形は推測・分布は子どもだけ錨)
      明るさ(E) = min(1, D_R(E) / 17)。D_R は Rombauts の 0.4 lx→4 m・3.0 lx→10 m・20〜25 lx で頭打ち  # §3(○〜△)
      予期     = 来ると分かっている相手なら 1.32、それ以外 1.0  # R-62(錨あり)
      親しさ   = 空欄(既定 1.0。11a の曲線がすでに「よく知る顔」の値)
  後ろ姿(相手の顔が見る人に向いていない)のとき: 体と歩き方だけの別の曲線が要るが、値は空欄
```

- 掛け方の注意: 注意の乗数(Hyman・Lim・Simons)は「気づいたか」を測った値で、距離の曲線とは別の段に掛けるのが測り方と合う(サブの読み)。視力と明るさは「距離を縮める」形にすると、L&H の「距離はフィルタと同じ」の考え方と合う。
- 2 段の判定の順: 段 1(視野 → 見通し → 注意)→ 段 2(距離と視力と明るさ)→ 本人が声をかけるか、気づかないふりをするかを決める(指示書 §4-2)。
- 係数ごとの錨の有無:

| 要因 | 入れ方 | 値 | 等級 |
|---|---|---|---|
| 視野 | 0/1 の門 | ±107° | 既存 R-62(◎) |
| 遮るもの | exp(−ρ·g·w·d) | 形は Gapeyenko・w は空欄 | 形 ◎・値 空欄 |
| 通話 | 段 1 の乗数 | 0.49 | ◎(Hyman 表 2) |
| 文字 | 段 1 の乗数 | 0.52 | △(Lim 抄録) |
| 連れと会話 | 段 1 の乗数 | 1.0 以上(連れ 71% / 一人 51%) | ◎(Hyman 表 2) |
| 考えごとの負荷 | 段 1 の乗数 | 0.70 | ◎(Simons & Chabris) |
| 急いでいる | 段 1 の乗数 | 空欄 | なし |
| 視力 | 距離を d/V に | 形は推測・子どもの分布は ◎・成人は空欄 | 推測 |
| 明るさ | 距離を縮める | 0.4 lx→4 m・3 lx→10 m・17 m で頭打ち | △〜○ |
| 予期 | 距離を伸ばす | 1.32 倍 | 既存 R-62(○) |
| 親しさ | 距離を伸ばす | 空欄 | なし |
| 後ろ姿 | 別の曲線 | 空欄 | なし |

### 8-3 11a の 2 m との整合

- 2 m は、Hall の社会距離の近い側(1.2〜2.1 m・二次)の内側、西出の近接域(1.5〜3 m・二次)の中にあり、西出の会話域(〜1.5 m)と Sorokowska の見知らぬ人 1.35 m・知人 0.92 m(既存)を覆う側。
- 腕の 2.5 m は Miles 2023 が立ち話を始めさせた距離と同じで、騒音が上がると 2 人はそこから近づいた(1 dB あたり 2.0 cm)。1 m の腕は知人の選好距離 0.92 m に近い。
- 段 3 で R-78 の聞き取りの式に置き換えると、会話の距離は騒音で縮む結果として出てくる。Miles 2023 の「2.0 cm/dB」と「78 dB SPL で会話が途切れ始める」は、その置き換えの後に結果を照らす物差しに使える(推測)。

---

## §9 未確認・空欄の一覧

1. 子どもの視力の区分別(0.3 未満など)・年齢別の値(e-Stat の詳細表は未取得)。
2. 成人の裸眼視力の全国分布(年代別)。
3. 成人の矯正視力の年代別の分布(多治見の本文の表は未読)。
4. 視力ごとに顔の見分けの距離を測った一次(本書の d/V は推測)。
5. 親しい人を後ろ姿・歩き方で見分けられる距離(m)。
6. Burton ほか 1999 の条件別(頭・体・歩き方を隠す)の正答率。
7. Hahn ほか 2016 の距離の値と、依頼文の「100 m 超」の出どころ。
8. Jarudi ほか 2023 の距離の値。
9. 親しさで見分けの距離が何倍になるか。
10. 渋谷の街路の夜の照度の実測(角舘 2008・松本と金 2013・伊藤ほか 1997 は取得できず)。
11. CIE 115 / CIE 136 の推奨値の本文(有料)。
12. Rombauts 1989 の原典の本文(4 m の値 0.4 lx と 0.6 lx の食い違いの確認)。
13. 群衆の中で人と人の見通しを人で測った一次(密度 × 距離)。
14. 目の高さで有効な遮る幅 w(頭の幅)の値。
15. 急いでいるときの気づきの低下の一次。
16. Lim ほか 2015 の条件別(視野の広さ・細かさ)の見落とし率。
17. 「歩きスマホで視野 20 分の 1」の一次(測った量と角度の定義)。
18. 歩行者が別の歩行者の存在に気づく距離の一次(段 1)。
19. Hall 1966 の原典の逐語(4 区分と近い側・遠い側の値)。
20. 西出 1985 の原典(会話域・近接域・相互認識域の値と測り方)。
21. Kendon & Ferber 1973 の原典の距離の値。
22. 渋谷のような雑踏での会話の距離・立ち話を始める距離・F-formation の寸法の実測。
23. Miles ほか 2023 の絶対の距離(図だけ)。
24. 各要因を同時に入れたときの係数(要因どうしの重なり)を推定した研究。

## §10 INDEX に足す行の案(**本書では追記しない**。親が入れる)

```
| 10-03 | [r79-noticing-factors-conversation-distance](v2-r79-noticing-factors-conversation-distance.md) | ~230 | **B** | 知覚心理学・精神物理学 #5 / 歩行者動力学 #18 / 照明工学 / 近接学 | 気づく要因と会話の距離(§4-2・§11 第 2 群): 視力は距離を d/V に(Loftus & Harley の式からの推測)・裸眼 1.0 未満 小 37.79%/中 60.93%/高 67.80%(令和 5)・警察庁 10 m 先の顔 20 lx/明確 50 lx/4 m 先の挙動 3 lx・Rombauts 0.4 lx→4 m・3 lx→10 m・17 m 頭打ち・見通し exp(−ρgwd)(Gapeyenko の形)・通話で気づき 25%/一人 51%/連れ 71%(Hyman 表 2)・Easy 64%/Hard 45%(Simons & Chabris)・騒音 1 dB で立ち話 2.0 cm 近づく・声 0.32 dB/dB(Miles 2023)・親しさ・後ろ姿・急ぐ・渋谷の照度は空欄 |
```

伝播の対象(親の判断): p_notice 答申の Simons & Chabris の Easy/Hard の空欄(§5 で埋まる)/ R-78 のロンバードの傾き 0.5 と本書の実測 0.32 の併記 / C9 答申 §3 の 6 の Hall の社会距離の帯の食い違い(§7 の読み)。
