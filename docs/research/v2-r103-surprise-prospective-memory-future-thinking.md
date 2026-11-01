# R-103 答申: 驚きと熟考・予定を思い出す仕組みと実行意図・いつ未来のことを考えるか(B2・B4・B6)

<!-- hdr:v1 -->
- **分野**: 認知科学(記憶・習慣) #12 / 人格心理学 #13 / ABM 方法論 #21 | **重要度**: P1(発注 10-06 §2 B2・B4・B6。指示書 10-03 §7-3 4-2 の驚き駆動、09-25 §4.2 の入口 3 つ、09-25 §8 のリサーチ 2・3・5)
- **一次確認**: **B**(サブの自己評価。本文を自分で読んだ原典 11(うち PDF を自分で抽出 8・画像の頁を目で読んだ 1・取得ツール経由 2)・抄録または二次 22・未読 4。空欄は §空欄)・**親検収 済(第324・2026-10-06)**: 親が原典で逐語確認=Daw 2011(PMC・17 人・表 1 の w 中央値 0.39・25/75 百分位 0.29/0.59・本文「model-free 61%・model-based 39%」)/ Milkman 2021(PMC・N=47,306・「2.1 percentage points or 5% (P = 0.024)」・最良「4.6 percentage point … 11%」。縮小推定 2.8 pp・6.7% も本文にある)/ Song & Wang 2012(PLOS・24.4%(SD 43.0)・episodic 60.8%・そのうち未来 40.53%=「全体の約 6.0%」は積の再計算で原典の値ではない)/ Anderson & McDaniel 2019(Springer の PDF を標準出力で抽出・「PM occupies our thoughts approximately 13–15%」「future … 30% compared to 13%」「61% were internally cued」「OR = 1.87」一人のとき)/ Gollwitzer & Sheeran 2006(KOPS の抄録で k=94・d=.65 を確認。**N=8,461 と 95% CI .60〜.70・課題ごとの d は画像の頁の読みで親は未確認**=△扱い)。Reisenzein 2019 の r=.78/.65〜.73・Horstmann 2006 の 22%・Marsh 1998 の 13%/29% は親未確認(△)。等級は **B** のまま
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-06・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(論文の PDF は標準出力かスクラッチに置いて pymupdf で抽出。画像だけの PDF 1 本は頁を画像にして目で読んだ)。`data/research_cache/r103/` への取得はなし(許可ドメインのデータは使っていない)。コミットなし・台帳/設計書/草案/src は未編集。
> 既存答申との関係: 展望記憶の自然な課題・リマインダー・Rogers & Milkman 2016・Gilbert 2023 = [R-89](v2-r89-prospective-memory-punctuality.md)(本書は R-89 の §7 空欄 K-2・K-3・K-4 の続き)/ Hofmann 2012・Type 2 は既定で発火しない・Lee 2014 の抄録・Milli 2017・Kahneman & Klein 2009 = [R-39](v2-r39-judgment-share-research.md)(本書は R-39 §3 所見の空欄「期待違反の一般的な一次資料」の続き)/ Killingsworth 2010 の 46.9%・Kane 2017 の人ごとの幅・Seli 2018 = [R-88](v2-r88-llm-humanlikeness-deliberation-vision.md) / 思考頻度 H1〜H9 = [思考頻度ノート](v2-thought-frequency-anchors-note.md)。重なる値は再掲せず番号で参照する。
> 宛先: [時刻とカレンダーの草案](../design/v2-calendar-timing-design-round-draft.md) AT1・CA5・CA7 / [記憶の作り直しの草案](../design/v2-memory-rework-design-round-draft.md) MR7 / 指示書 10-03 §7-3 4-2(驚き駆動)/ 決定記録 09-25 §4.2(入口 3 つ)・§4.5(内省)。決定項は書き換えない。

## 結論(5 行)

1. **驚き(B2)**: 驚きの強さは「その出来事の起こりにくさ」とともに単調に増え、人の中では r = .78、人の間では r = .65〜.73 で結びつきます(Reisenzein ほか 2019 の総説・原典)。驚くと今の動作が約 0.2 秒で止まり、注意が移り、原因の分析と考え直しが続くことが多い、という流れは実証されています。ただし予想外の出来事を見ても動作が止まらない人が 22% いました(Horstmann 2006・抄録)。**「どのくらいのずれで考え直すか」の閾値は、理論上は置かれていますが数値で測った研究はありません(空欄)**。実験の時間の尺度はミリ秒から数試行で、日常の予定(分から時間)とは違います。
2. **習慣と熟考の切り替え(B2)**: 予測の信頼度で切り替える仕組み(Lee ほか 2014・原典)は、課題の試行の単位で示されたものです。人ごとの熟考の重み w は中央値 0.39・四分位 0.29〜0.59 とばらつきます(Daw ほか 2011・17 人・原典)。どちらの研究にも「熟考が何%の場面で支配したか」の値は無く、v2 の「よく考える」の割合の錨にはなりません。
3. **実行意図の d = .65 の内訳(B4)**: 94 件・8,461 人・95% CI .60〜.70(Gollwitzer & Sheeran 2006・原典の頁を目で読んだ)。「やることを思い出す」に限ると d = .54(11 件・983 人)、「機会を逃さない」.61、「気の進まなさを越える」.65 です。38 件は実験室の課題です。重みは分散の逆数で、健康と実験室の分野では異質性が有意でした。リマインダーの現場の効果は、予約前の SMS で接種が平均 2.1 ポイント(5%)増、最良の文面で 4.6 ポイント(11%)増でした(Milkman ほか 2021・47,306 人・原典)。
4. **思い出す過程(B4)**: 自分で立てた 1 週間の予定(平均 15.5 件)のうち、やらなかった理由で「忘れた」は約 13% だけでした。約 58%(再計算)は優先順位の付け替え、約 29% は相手の取り消しや不可能でした(Marsh ほか 1998・原典)。予定を見直す回数は 3 日で 29〜40 回(1 日 10〜13 回・再計算)で、手帳を使う人のほうが少ない。職場の課題では 1 日 4.4 回思い出し、廊下や階段のような移動の場所で思い出しやすい(Sellen ほか 1997・二次)。**目標の時刻から何分前・何分後に思い出すかの分布は、今回も空欄です。**
5. **未来を考える時間(B6)**: 経験サンプリングの瞬間のうち、展望記憶(やることの考え)が 13〜15%、未来の考え全体が 30% でした(Anderson & McDaniel 2019・原典)。やることの考えは 61% が内側のきっかけで、一人のとき(オッズ比 1.41〜1.87)と朝に多い。日記では未来の考えが 1 日約 60 回(約 16 分に 1 回・二次)。中国の学生では心のさまよい 24.4%・そのうち場面を思い描く考えが 60.8%・その 40.5% が未来でした(Song & Wang 2012・原典)。心のさまよいの割合は測り方と人で大きく動きます(R-88)。

## §0 出典の表

印: **○** 本文を読んだ(「自抽出」= PDF を自分で pymupdf で抽出・「画像」= 頁を画像にして目で読んだ・「取得ツール」= WebFetch の要約経由の本文) / **△** 抄録・二次だけ / **×** 読めなかった

| # | 出典 | URL | 印 | 読んだ範囲・使った所 |
|---|---|---|---|---|
| 1 | Reisenzein R., Horstmann G., Schützwohl A. 2019「The Cognitive-Evolutionary Model of Surprise: A Review of the Evidence」Topics in Cognitive Science 11(1):50-74 | https://doi.org/10.1111/tops.12292 (Bielefeld 大学の著者ページの出版版 PDF) | ○ 自抽出 | 全文 25 頁。B2 の仕組み・相関・量的モデル・中断の時間 |
| 2 | Horstmann G. 2006「Latency and duration of the action interruption in surprise」Cognition & Emotion 20(2):242-273 | https://doi.org/10.1080/02699930500262878 | △ | 抄録(OpenAlex)。78%・214 ms・995 ms |
| 3 | Horstmann G. 2015「The surprise-attention link: a review」Ann NY Acad Sci 1339:106-115 | https://doi.org/10.1111/nyas.12679 | △ | 抄録(OpenAlex)。注意の係留 約 400 ms |
| 4 | Meyer W.-U., Reisenzein R., Schützwohl A. 1997「Toward a process analysis of emotions: The case of surprise」Motivation and Emotion 21:251-274 | https://doi.org/10.1023/A:1024422330338 | × | 抄録も取れず。中身は #1 の要約で代える |
| 5 | Reisenzein R. 2000「Exploring the strength of association between the components of emotion syndromes: The case of surprise」Cognition & Emotion 14(1):1-38 | https://doi.org/10.1080/026999300378978 | △ | 抄録(OpenAlex)。r = .78 は #1 の本文の引用 |
| 6 | Foster M.I., Keane M.T. 2015「Why some surprises are more surprising than others」Cognitive Psychology 81:74-116 | https://doi.org/10.1016/j.cogpsych.2015.08.004 | △ | 二次(#1 の §5.4 と検索の要約)。出版社 403・UCD の保管庫は 405 |
| 7 | Lee S.W., Shimojo S., O'Doherty J.P. 2014「Neural computations underlying arbitration between model-based and model-free learning」Neuron 81(3):687-699 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3968946/ | ○ 取得ツール | PMC 本文(方法・図の凡例・結果)。補足表 S2 の当てはめ値は未読 |
| 8 | Daw N.D., Niv Y., Dayan P. 2005「Uncertainty-based competition between prefrontal and dorsolateral striatal systems for behavioral control」Nat Neurosci 8:1704-1711 | https://doi.org/10.1038/nn1560 | △ | 抄録(Europe PMC) |
| 9 | Daw N.D., Gershman S.J., Seymour B., Dayan P., Dolan R.J. 2011「Model-based influences on humans' choices and striatal prediction errors」Neuron 69(6):1204-1215 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3077926/ | ○ 自抽出 | Europe PMC の全文 XML。方法・表 1(w の四分位) |
| 10 | Shenhav A., Botvinick M.M., Cohen J.D. 2013「The expected value of control」Neuron 79(2):217-240 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3767969/ | △ | 抄録(Europe PMC) |
| 11 | Lieder F., Griffiths T.L. 2020「Resource-rational analysis」Behavioral and Brain Sciences 43:e1 | https://doi.org/10.1017/S0140525X1900061X | △ | 抄録(OpenAlex)。R-39 #5-1 と同じ |
| 12 | Kool W., Gershman S.J., Cushman F.A. 2017「Cost-benefit arbitration between multiple reinforcement-learning systems」Psychological Science 28(9):1321-1333 | https://doi.org/10.1177/0956797617708288 | △ | 抄録(OpenAlex) |
| 13 | Gollwitzer P.M., Sheeran P. 2006「Implementation intentions and goal achievement: A meta-analysis of effects and processes」Adv Exp Soc Psychol 38:69-119 | https://kops.uni-konstanz.de/handle/123456789/10973 (KOPS の PDF) | ○ 画像 | 文字の無い PDF。92・95・96 頁を画像にして目で読んだ(結果 1・表 III・表 IV)。R-89 #25(△)の続き |
| 14 | Gollwitzer P.M., Sheeran P.「Implementation Intentions」(米国国立がん研究所の構成概念の解説、2020 年掲載) | https://cancercontrol.cancer.gov/sites/default/files/2020-06/goal_intent_attain.pdf | ○ 自抽出 | 全文。d = .61・.77・.65 の要約 |
| 15 | Marsh R.L., Hicks J.L., Landau J.D. 1998「An investigation of everyday prospective memory」Memory & Cognition 26(4):633-643 | https://doi.org/10.3758/BF03211383 | ○ 自抽出 | 全文 11 頁(実験 1〜3)。表 1 は OCR の崩れで数値の行と列の対応が読めない(本文の逐語の値だけ使う) |
| 16 | Anderson F.T., McDaniel M.A. 2019「Hey buddy, why don't we take it outside: An experience sampling study of prospective memory」Memory & Cognition 47:47-62 | https://doi.org/10.3758/s13421-018-0849-x | ○ 自抽出 | 全文 16 頁(研究 1・2)。R-89 #21(△)の続き |
| 17 | Sellen A.J., Louie G., Harris J.E., Wilkins A.J. 1997「What brings intentions to mind? An in situ study of prospective memory」Memory 5(4):483-507 | なし | △ | 二次(#16 の序論の要約) |
| 18 | Harris J.E., Wilkins A.J. 1982「Remembering to do things: A theoretical framework and an illustrative experiment」Human Learning 1:123-136 | なし | △ | 二次(抄録の要約を検索結果で読んだ) |
| 19 | Ceci S.J., Bronfenbrenner U. 1985「"Don't forget to take the cupcakes out of the oven"」Child Development 56(1):152-164 | https://doi.org/10.2307/1130182 | △ | 抄録(OpenAlex) |
| 20 | McDaniel M.A., Einstein G.O. 2000「Strategic and automatic processes in prospective memory retrieval: a multiprocess framework」Appl Cogn Psychol 14:S127-S144 | https://doi.org/10.1002/acp.775 | △ | 抄録(OpenAlex) |
| 21 | Smith R.E., Bayen U.J. 2004「A multinomial model of event-based prospective memory」JEP:LMC 30(4):756-777 | https://doi.org/10.1037/0278-7393.30.4.756 | △ | 抄録(OpenAlex) |
| 22 | Einstein G.O., McDaniel M.A., Richardson S.L., Guynn M.J., Cunfer A.R. 1995「Aging and prospective memory: Examining the influences of self-initiated retrieval processes」JEP:LMC 21(4):996-1007 | https://doi.org/10.1037/0278-7393.21.4.996 | × | 抄録が取れず(R-89 #17 の二次のまま) |
| 23 | Milkman K.L. ほか 2021「A megastudy of text-based nudges encouraging patients to get vaccinated at an upcoming doctor's appointment」PNAS 118(20):e2101165118 | https://pmc.ncbi.nlm.nih.gov/articles/PMC8157982/ | ○ 自抽出 | Europe PMC の全文 XML。2025-10 に補足資料の訂正あり(本文の値ではない・訂正の中身は未読) |
| 24 | Kane M.J. ほか 2007「For whom the mind wanders, and when」Psychological Science 18(7):614-621 | https://doi.org/10.1111/j.1467-9280.2007.01948.x | △ | 抄録(OpenAlex)。値は R-88 #23 |
| 25 | Smallwood J., Schooler J.W. 2015「The science of mind wandering」Annu Rev Psychol 66:487-518 | https://doi.org/10.1146/annurev-psych-010814-015331 | △ | 抄録(OpenAlex) |
| 26 | Baird B., Smallwood J., Schooler J.W. 2011「Back to the future: Autobiographical planning and the functionality of mind-wandering」Consciousness and Cognition 20(4):1604-1611 | https://doi.org/10.1016/j.concog.2011.08.007 | △ | 抄録(Europe PMC)。割合の数値は未読 |
| 27 | Stawarczyk D. ほか 2011「Mind-wandering: Phenomenology and function as assessed with a novel experience sampling method」Acta Psychologica 136(3):370-381 | https://orbi.uliege.be/bitstream/2268/87733/1/Stawarczyk%20et%20al.%20-%202011%20-%20ActaPsychologica.pdf | ○ 自抽出 | 著者稿の全文。未来の割合は図 4 だけで数値の本文なし |
| 28 | D'Argembeau A., Renaud O., Van der Linden M. 2011「Frequency, characteristics and functions of future-oriented thoughts in daily life」Appl Cogn Psychol 25(1):96-103 | https://doi.org/10.1002/acp.1647 | △ | 抄録(OpenAlex)。1 日の回数は #29・#16 の二次。ジュネーブ大の保管庫はログイン要 |
| 29 | Barsics C., Van der Linden M., D'Argembeau A. 2016「Frequency, characteristics, and perceived functions of emotional future thinking in daily life」QJEP 69(2):217-233 | https://orbi.uliege.be/handle/2268/190599 | ○ 自抽出 | 著者稿の全文(ORBi) |
| 30 | Song X., Wang X. 2012「Mind wandering in Chinese daily lives - an experience sampling study」PLoS ONE 7(9):e44423 | https://doi.org/10.1371/journal.pone.0044423 | ○ 自抽出 | 全文 9 頁 |
| 31 | Berntsen D., Jacobsen A.S. 2008「Involuntary (spontaneous) mental time travel into the past and future」Consciousness and Cognition 17(4):1093-1104 | https://doi.org/10.1016/j.concog.2008.03.001 | △ | 抄録(Europe PMC) |
| 32 | Gardner R.S., Ascoli G.A. 2015「The natural frequency of human prospective memory increases with age」Psychol Aging 30(2):209-219 | https://doi.org/10.1037/a0038876 | △ | 抄録(Europe PMC)。R-89 #22 と同じ |
| 33 | Macedo L., Cardoso A., Reisenzein R. ほか(対比のモデル 2004・2009、総説 2017 Topics in Cognitive Science) | https://doi.org/10.1111/tops.12310 | △ | 抄録と #1 の要約 |
| 34 | Teigen K.H., Keren G. 2003「Surprises: low probabilities or high contrasts?」Cognition 87:55-71 | なし | △ | 二次(#1 の要約) |
| 35 | Stiensmeier-Pelster J., Martini A., Reisenzein R. 1995(驚きと原因の探索) | なし | △ | 二次(#1 の要約) |
| 36 | Gillan C.M. ほか 2016「Characterizing a psychiatric symptom dimension related to deficits in goal-directed control」eLife 5:e11305 | https://elifesciences.org/articles/11305 | × | 1,413 人の w の分布は補足資料 1B にあると検索の要約。未読 |
| 37 | Kliegel M. ほか(展望記憶の段階の研究)・Smith & Bayen の PAM の続報 | なし | × | 未読 |

数え: ○ 11(#1・7・9・13・14・15・16・23・27・29・30)/ △ 22 / × 4(#4・22・36・37)。R-88・R-89・R-39 の出典は番号で参照し、上の数に入れていない。

## §1 B2 驚きと熟考

### 1-1 仕組み(スキーマのずれの説明)

- 驚きの装置は無意識に、意図とは関係なく、今の状況のスキーマと新しい情報を比べ続けると仮定されます(#1 の §2、逐語「continuously and automatically (without the person's intention) compares the currently activated cognitive schemas」)。ずれの信号が「a certain threshold」を超えると、処理が自動的に中断し、注意が移り、驚きの感じとして意識に上ります(#1 §2)。**この閾値の値は総説のどこにも数値で書かれていません。**
- 驚きの強さを決めるのはずれの大きさで、新しさや快不快は独立には効かないと総説は結論しています(#1 の抄録)。
- 驚きの後に続く処理(#1 §2・§4): 中断と注意の移動のあと、原因などの分析に移り、分析しだいでスキーマを直す。分析の強さと長さは「情報を探す費用と利益、分析の難しさ、使える時間」で変わる(逐語「the estimated costs and benefits of information search, the difficulty of the event analysis and the available time」#1 §2、Stiensmeier-Pelster ほか 1995・#35 と Foster & Keane 2015・#6 を引く)。驚きが原因の探索の強さを媒介する(Stiensmeier-Pelster 1995・Gendolla & Koller 2001、#1 §4 の要約)。
- 説明の難しさの仮説(#6・△): 驚きの感じは「説明の難しさのメタ認知的な感覚」で、説明がすぐ見つかれば驚きは小さい(#1 §5.4 の要約。逐語「metacognitive sense of explanatory difficulty」Foster & Keane 2015 p.78)。#1 はこれに反対の材料も挙げています(驚きと説明の難しさが同じ向きに動くので区別できない、など)。

### 1-2 どのくらいのずれで驚くか(量)

| 量 | 値 | 出典 | フロア・注意 |
|---|---|---|---|
| 起こりにくさと驚きの相関(人の間) | 成功 r = .65・失敗 r = .73(思い出した学業の成功と失敗) | Stiensmeier-Pelster ほか 1995 実験 1(#1 §3.1.2 の要約) | 1 研究の値 |
| 起こりにくさと驚きの相関(人の中) | 平均 r = .78(クイズの正解の意外さと驚き) | Reisenzein 2000(#1 §3.1.2 の要約・#5 の抄録は「strong association only between the cognitive and the experiential component」) | 人ごとの r の散らばりは #1 に無い(空欄) |
| 最も単純な量のモデル | 驚き S(A) は 1 − p(A) に比例。クイズの正解と二択のくじでよく当てはまる | #1 §3.1.3 | 逐語「This model fits many surprise situations very well」 |
| 対比のモデル | S(A) = log2(1 + p(M) − p(A))(M は最も起こりそうだった結果) | Macedo ほか 2004(#1 §3.1.3・#33) | 複数の結果がある場面向け |
| 驚きの表情と驚きの感じの結びつき | 人の中で平均 r = .46 | Reisenzein 2000(#1) | 表情は驚きの指標にならない |
| 動作の中断 | 予想外の物体の出現で 78% が打鍵を止めた。潜時 平均 214 ms・長さ 平均 995 ms | Horstmann 2006(#2・抄録) | **22% は止めなかった**(人による差のフロア) |
| 注意の係留 | 驚いた刺激への最初の視線は 約 400 ms | #1 §4.1・#3 の抄録 | 100 ms しか出さない変化では注意も反応時間も変わらなかった(#1 §4.1) |
| 繰り返し | 前の試行ですでに起きた変化には驚かない | #1 §3.1.1(Meyer ほか 1991・Schützwohl 1998) | 慣れの速さの数値は空欄 |

### 1-3 予測の信頼度で習慣と熟考を切り替える研究

- Lee ほか 2014(#7・○): 22 人・5 回 × 約 80 試行。状態の遷移確率が (0.9, 0.1) の区画(3〜5 試行)と (0.5, 0.5) の区画(5〜7 試行)を混ぜた課題で、モデルに基づく系の信頼度は状態予測誤差から、モデルなしの系の信頼度は報酬予測誤差の絶対値から計算し、その信頼度を遷移の速さとして 2 状態のどちらが支配するかを決めます(#7 図 2 の凡例「The computed reliability functions as a transition rate」)。習慣側に偏る項があり、閾値が動く版が最もよく当てはまりました。
  - **使える数値は少ない**: 条件ごとのモデルに基づく支配の確率の値は本文に無く、補足表 S2 の当てはめ値は未読(空欄)。モデルに基づく支配の確率と反応時間の相関は中央値 0.13 で、22 人中 16 人で有意(#7)。
  - 時間の尺度: 区画は 3〜7 試行で、切り替わりの試行数は本文に書かれていません。日常の予定の分・時間の尺度には写せません。
- Daw ほか 2005(#8・抄録): 2 つの系を「その時点で最も正確であるべき方」に任せる、不確かさによる調停の規範的な説明。
- Daw ほか 2011(#9・○): 17 人・201 試行。モデルに基づく重み w の中央値 0.39(25 パーセンタイル 0.29・75 パーセンタイル 0.59)(表 1)。逐語「Across subjects, the median weighting for model-free RL values was 61% (with model-based RL at 39%)」。**人ごとの熟考の重みは四分位で 0.3 の幅に散る**のがフロアです。大きな標本(Gillan 2016 の 1,413 人・#36)の分布は未読。
- Kool ほか 2017(#12・抄録): モデルに基づく制御の精度が高いとき、とくに報酬が大きいときに人は熟考を増やす。精度が同じなら報酬を増やしても変わらない(費用と利益の調停)。
- Shenhav ほか 2013(#10・抄録)の制御の期待値: 制御から得る見込みの利益・必要な制御の量・努力の費用の 3 つを合わせて、制御をかけるか・どこに・どれだけを決める。数値の錨ではなく枠組み。
- Lieder & Griffiths 2020(#11・抄録)は R-39 §5-1 のとおり。

### 1-4 驚き駆動の設計に使えない理由・注意

- **時間の尺度**: 驚きの実験はミリ秒から秒(#2・#3)、調停の実験は数試行の区画(#7・#9)です。v2 の驚き(「友人が 10 分来ない」など)は分から時間の尺度で、予想も本人が書いたカレンダーから来ます。実験の値は「起こりにくさとともに単調に強まる」「止まらない人もいる」「慣れると驚かない」という形にだけ使えます。
- **閾値の数値は無い**: 理論は閾値を置きますが値は測られていません。v2 の「驚きを考え直しとするかは本人(判断モデル)が決める」(10-03 §7-3 4-2)は、閾値の値を置かずに済む形で、原典と食い違いません(推測)。
- **確信度の注意**: Kahneman & Klein 2009(R-39 §4)は、速い判断の主観的な確信度は任せてよいかの指標にならないとしています。判断モデルが自分の驚きの点数で上の層を呼ぶ形を検証するときの反証の材料です。

### 1-5 B2 の空欄・次に頼むこと

- 日常の場面で、予想とのずれの大きさと「考え直した割合」を同時に測った研究(空欄)。次の手: 日常の驚きの日記研究(Noordewier & Breugelmans の驚きの時間経過など)の本文。
- 驚きの強さの人による差(不安・神経症傾向など)の効果量(空欄)。#16 は神経症傾向(不安の側面)が高い人ほど展望記憶の考えが多いと報告(§2-4)。
- Lee 2014 の補足表 S2、Gillan 2016 の補足資料 1B(w の分布)。

## §2 B4 予定を思い出す仕組みと実行意図

### 2-1 時刻がきっかけと出来事がきっかけ

- 多過程の枠組み(#20・抄録): 思い出す道は、環境を能動的に見張る道と、予想した場面が意図をほぼ自動的に呼び戻す道の 2 つ。どちらに頼るか、自動の道でどれだけ成功するかは、課題・手がかり・今の作業・人の特徴で変わる。R-89 §1-1 のとおり、時刻がきっかけの課題は手がかりが焦点に無く、見張り(時計を見る)に頼ります。
- PAM(#21・抄録): 出来事がきっかけの展望記憶を「準備的な注意」と「何をするかの記憶」の 2 つの値に分ける多項モデル。値は課題ごとに推定するもので、日常の既定値は無い。
- Harris & Wilkins 1982(#18・二次): 映画を見ながら決まった時刻に反応する課題で、目標の時刻が近づくと時計を見る回数が増え、その増え方が反応の正確さと関係した。忘れた人も目標の直前に時計を見ていたことが多い(確認と待ちを繰り返す TWTE の形)。
- Ceci & Bronfenbrenner 1985(#19・抄録): 子どもが 30 分待って行動する課題で、時計の確認は家のほうが実験室より戦略的(はじめに合わせ、途中は減り、終わりに増える形は二次の要約。抄録は「strategic time-monitoring occurred less frequently in the laboratory than in the home」)。
- Einstein ほか 1995(#22)は今回も抄録が取れず、R-89 §1-1 の扱いのまま。

### 2-2 思い出すまでの時間・回数の分布(R-89 K-2 の続き)

| 量 | 値 | 出典 | 時間の尺度・注意 |
|---|---|---|---|
| 自然な場面で約束の時刻 ±10 分 | 53〜74% | R-89 §1-2(Kvavilashvili & Fisher 2007) | 7 日後の電話。分単位の遅れの全分布は無い |
| 職場の課題を思い出す回数 | 1 日 4.4 回・成功 約 42%・週の間に減る・廊下や階段などの移動の場所で多い | Sellen ほか 1997(#17・#16 の序論の二次) | 課題を押すバッジで記録 |
| 1 週間の予定を見直す回数 | 火曜の朝〜木曜の夜の 3 日で、手帳なし 40.1 回(CI 30.6〜49.6)・手帳あり 29.3 回(CI 22.4〜36.2)。リストバンドで約 50% 増(手帳なし 62.2・あり 41.7) | Marsh ほか 1998 実験 2 の表 3(#15・○) | 1 日あたり 約 13.4 回と 約 9.8 回 [再計算]。予定は 5 日で 14〜18 件 |
| 時計を見る回数の形 | 目標の時刻の近くで増える | #18・#19(△) | 数分〜30 分の課題 |

- **「目標の時刻から何分前・何分後に思い出したか」の分単位の分布は、今回も見つかりません(空欄)**。実験室の時刻の課題は数分の間隔で、日常の研究(R-89 #1・#17)は日単位か回数です。

### 2-3 予定をやらなかった理由(日常)

Marsh ほか 1998 実験 1(#15・○)。学部生 135 人が翌週の予定を書き、1 週間後にやったかと、やらなかった理由を答えました。
- 予定の数: 平均 15.5 件(SD 5.34)。手帳を使う人 57.8%・使わない人 42.2% で数は同じ(15.5・15.4)。
- やらなかった理由(本文の逐語): 「the participants actually overtly forgot very few of their intentions (i.e., approximately 13% in the "Column Averages" row of Table 1). Rather, reprioritization and rescheduling dominated」「approximately 29% of the participants' failures were not directly under their voluntary control (i.e., cancelled and impossible)」。残りの優先順位の付け替えは 約 58% [再計算: 100 − 13 − 29]。
- 未完了の率は分類で違い、相手とすでに約束した予定(約束・予約、宿題)は低く、未確定の意図(連絡する、何かを済ませる)は高い(本文の逐語)。表 1 の数値は OCR が崩れて行と列の対応が読めないため使いません。#16 の序論は Marsh 1998 の完了率を「approximately 70-75%」と要約しています(二次)。
- 手帳を使う人と使わない人で、未完了の率も忘れの率も違いませんでした。実験 3 では手帳を持たせると忘れが減りました(F(1,167) = 9.56, p < .01)。
- 1 週間の全予定のうち「忘れてやらなかった」は 約 3〜4% [推測: 0.13 × 未完了 25〜30%]。

### 2-4 実行意図の効果量(R-89 K-3 を埋める)

Gollwitzer & Sheeran 2006(#13・○ 画像で読んだ頁)。

- 全体(92 頁・逐語): 「The overall impact of forming implementation intentions on goal achievement was d = .65 based on k = 94 tests that involved 8461 participants. This effect had a 95% confidence interval from .60 to .70.」。平均は「each d weighted by the reciprocal of its variance」(91〜92 頁)。

表 IV(96 頁)自己調整の課題ごと:

| 課題 | N | k | d | 95% CI | Q |
|---|---|---|---|---|---|
| やることを思い出す | 983 | 11 | .54 | .45〜.72 | 16.79 |
| 機会を逃さない | 2,270 | 20 | .61 | .52〜.70 | 23.75 |
| 気の進まなさを越える | 2,588 | 21 | .65 | .56〜.72 | 72.82*** |
| 始めること 全体 | 5,841 | 52 | .61 | .56〜.67 | 114.21*** |
| 望まない影響から守る 全体 | 1,396 | 21 | .77 | .67〜.87 | 27.60 |
| 見込みの無い目標から降りる | 370 | 3 | .47 | .26〜.70 | 0.22 |
| 自己調整の力を保つ | 93 | 3 | 1.28 | .77〜1.76 | 3.08 |

表 III(95 頁)目標の分野ごと: 消費 .41(k 2)・環境 1.12(k 3)・反人種差別 .87(k 3)・向社会 1.01(k 5)・学業 .72(k 9)・個人の目標 .58(k 11・N 1,391)・健康 .59(k 23・N 2,861)・実験室の課題 .70(k 38・N 2,428)。表の見出しは χ² だが注は Q。環境(17.07***)・健康(47.92***)・実験室(59.90*)で異質性が有意。

- 読み方: 94 件のうち 38 件は実験室の課題、23 件は健康です。「やることを思い出す」の d = .54 は 11 件で、時刻がきっかけか出来事がきっかけかの区別は表に無い(空欄)。展望記憶に限った値は R-89 §2-1 の Chen 2015(若年 d = 0.445)のまま。時刻がきっかけに限った値(R-89 K-4)は空欄のまま。
- #14(○)の要約は「始めること d = .61・脱線を防ぐ d = .77・全体 d = .65」で表 IV と一致します。

### 2-5 リマインダー・アラームの効果

- 実験室: 自分の記憶だけで忘れ 約 45%、リマインダーで 約 5%(R-89 §2-2・Gilbert 2023)。
- 現場の大規模実験(#23・○): 予約の前に送る SMS の 19 種類を 47,306 人で比べた(通常の予約通知だけの対照 2,389 人)。逐語「The 19 treatments boosted vaccination levels by an average of 2.1 percentage points or 5% (P = 0.024)」「The top-performing intervention in our study showed a 4.6 percentage point boost in vaccination (an 11% increase; P < 0.01)」、最大値の膨らみを直すと「2.8 percentage point boost in vaccination or a 6.7% increase from baseline」。19 の効果が同じという帰無仮説は棄却できない(χ² = 21.277, df = 18, P = 0.266)。最良の文面は 2 回送り、「あなたの分を取ってある」と書いたもの。驚かせる・くだけた・やりとりを求める文面は効きが悪かった。
- 手がかりを物に結びつける方法(Rogers & Milkman 2016)は R-89 §2-2 のとおり。
- 読み方: 現場の効き目は実験室よりずっと小さい(数ポイント)。もともと予約があり行くつもりの人への上乗せだからです(推測)。

### 2-6 B4 の空欄・次に頼むこと

- 思い出す時刻の分単位の分布(空欄・R-89 K-2 は一部だけ埋まった)。次の手: Sellen 1997(#17)の本文、時刻の課題の反応の遅れの分布を報告した研究の検索。
- 時刻がきっかけの展望記憶に限った実行意図の効果量(R-89 K-4・空欄)。
- Marsh 1998 表 1 の数値(OCR の崩れ)。親が PDF の頁を画像で確かめれば読めます。

## §3 B6 いつ未来のことを考えるか

### 3-1 心のさまよいの割合(フロアつき)

| 研究 | 値 | 方法 | フロア |
|---|---|---|---|
| Killingsworth & Gilbert 2010 | 標本の 46.9% | 2,250 人・スマホ | R-88 B5(親検収済)。測り方で 10〜60%(Seli 2018)・人で 2〜97%(Kane 2017)は R-88 §2-1 |
| Kane ほか 2007 | 約 30% | 学部生 124 人・7 日・1 日 8 回 | 抄録は割合を書かない。値は R-88 #23 |
| Song & Wang 2012(#30・○) | 24.4%(SD 43.0%・範囲 100%) | 中国の学部生 165 人・3 日・1 日 6 回(7:30〜23:30) | 逐語「with considerable variation around the mean」 |
| Stawarczyk ほか 2011(#27・○) | 刺激と無関係で作業とも無関係な考え 21.6%(SD 15.14) | 実験室の SART | 日常ではない |

### 3-2 そのうち未来の予定を考える割合

| 研究 | 値 | 印 |
|---|---|---|
| Anderson & McDaniel 2019(#16) | 研究 2(122 人): 今のこと 55%・未来 30%・過去 14%。展望記憶(やることの考え)は全体の 13〜15%。展望記憶を選んだとき、意図を作っている 46%・やっている最中 25%・ただ考えている 29%。きっかけは内側 61%・外側 39% | ○ |
| 同(研究 1・61 人・1,531 回答) | 一人のときに展望記憶の考えが多い(OR = 1.87、研究 2 は 1.41)。1 時間遅くなるごとに OR = .96〜.97(朝に多い)。不安の高い人に多い | ○ |
| Song & Wang 2012(#30) | 心のさまよいのうち場面を思い描く考え 60.84%。その時間の向き: 未来 40.53%・今 15.92%・過去 21.53%・向きなし 22.02%。88.17% はきっかけを言えた。そのうち 49.43% が内側のきっかけ | ○ |
| 同(再計算) | 全標本のうち「未来の場面を思い描く心のさまよい」約 6.0% [再計算: 0.244 × 0.6084 × 0.4053。人ごとの平均の積なので推測] | ○ の値から再計算 |
| Stawarczyk ほか 2011(#27) | 作業と無関係な考えは未来向きが最も多い(F(3,132) = 16.54)。自分の目標を事前に書かせると未来向きが増える。数値は図だけ | ○ |
| Baird ほか 2011(#26) | 心のさまよいは主に未来向きで、自分の予定の計画を含むことが多い。作業記憶の容量が大きい人ほど未来向きが多い | △ |
| Gardner & Ascoli 2015(#32) | 過去の回想は全年齢で約 10%。若年は展望記憶と回想が同程度、高齢は展望記憶が 2 倍 | △ |
| Cameron 1972・Klinger & Cox 1987(#16 の序論の二次) | 今 67%・未来 25%・過去 8%(Cameron)。今 67%・過去か未来 12%(Klinger & Cox) | △ |

- 研究どうしのフロア: 未来の考えの割合は、日常で 12〜30%(Klinger & Cox・Cameron・#16)と方法で倍以上ずれます。#16 自身が「when people were not focused on the present ... there appears to be a prospective bias in the laboratory, but results are inconclusive when sampling outside the laboratory」と書いています。

### 3-3 1 日の回数(「約 59 回」の確認)

- D'Argembeau ほか 2011(#28): 抄録に回数は無い(△)。同じ研究室の Barsics ほか 2016(#29・○)の逐語: 「on average, during a typical day, young adults might experience sixty future-oriented thoughts, that is, about one future-oriented thought every sixteen minutes」「around sixty future-oriented thoughts were experienced each day」。**発注の「約 59 回」は、今回読めた範囲では「約 60 回」までしか確かめられません。** 59 という値は原典の本文で確かめる必要があります(空欄)。
- #16 の序論(二次): D'Argembeau 2011 の未来の考えのうち 52.5% が行動の計画に使われた。
- 検索の要約に「1 日 100 回」と書く二次資料がありました(Gardner & Ascoli を引く文脈)。原典で確かめていないので使いません。
- Barsics ほか 2016(#29・○): 感情を伴う未来の考えは 3 日で平均 28 回(SD 18.7・最小 2・最大 83)、1 日 約 9 回。日記の方法で「記録を頼まれたので少し多めに考えた」と答えた(7 段階で 2.87)。

### 3-4 どこで・何をしているときに起きるか

| 場面 | 値 | 出典 |
|---|---|---|
| 場所(感情を伴う未来の考え) | 家 52%・職場 25%・移動中 11%・公共の場 8%・知人の家 3% | #29(○) |
| 活動(同) | 仕事 29%・休み 21%・食事や身支度 13%・映像やゲームやネット 11%・運転 8%・会話 7%・家事 6%・余暇 3%。一人のとき 49% | #29(○) |
| 職場の課題を思い出す場所 | 机より廊下や階段などの移動の場所 | Sellen 1997(#17・二次) |
| 展望記憶の考え | 一人のとき・朝に多い | #16(○) |
| 心のさまよいが減る場面 | 周りに注意を向けている・前向きな気分・作業に集中し得意なとき。重要な作業の最中には増える | Song & Wang 2012 表 1(#30・○) |
| 心のさまよい | 性行為を除くどの活動でも 30% 以上 | R-88 B5(Killingsworth) |

- 待ち時間そのものの割合を測った値は見つかりません(空欄)。#29 の「移動中 11%」は割合で、移動している時間の長さで割った率ではありません。
- Berntsen & Jacobsen 2008(#31・△): 不随意の未来の考えは不随意の思い出と同じくらい多く、きっかけと主観の質も似ている。

### 3-5 B6 の空欄・次に頼むこと

- D'Argembeau 2011 の 1 日の回数の原典の値(59 か 60 か)と、活動・場所の内訳(空欄。Wiley の本文は有償・ジュネーブ大の保管庫はログイン要)。
- 活動の切れ目・待ち時間に未来の考えがどれだけ増えるかの率(空欄)。
- Killingsworth 2010 の活動ごとの心のさまよいの表(補足資料。R-88 も原文 403)。

## §空欄

| # | 空欄 | 理由 | 次の手 |
|---|---|---|---|
| K-1 | 考え直しを起こす「ずれの大きさ」の閾値(日常の予定) | 理論は閾値を置くが値を測った研究が無い | 日常の驚きの日記研究の本文 |
| K-2 | 驚きの起こりにくさの相関の人ごとの散らばり(SD・四分位) | #1 は平均の r だけ | Reisenzein 2000 の本文(有償) |
| K-3 | Lee 2014 の当てはめ値・条件ごとの支配の確率 | 補足表 S2 未読 | PMC の補足資料 |
| K-4 | 熟考の重み w の大きな標本の分布 | Gillan 2016 の補足 1B 未読 | eLife の補足資料(読むだけ) |
| K-5 | 思い出す時刻の分単位の分布(R-89 K-2) | 自然な研究は日単位か回数・実験室は数分 | Sellen 1997 本文 |
| K-6 | 時刻がきっかけに限った実行意図の効果量(R-89 K-4) | G&S 2006 の表に区別が無い | Chen 2015 本文 |
| K-7 | Marsh 1998 表 1 の数値 | OCR の崩れ | 親が頁を画像で確認 |
| K-8 | D'Argembeau 2011 の 1 日の回数(59/60)と内訳 | 本文は有償・保管庫はログイン要 | 大学図書館か著者稿 |
| K-9 | 待ち時間・活動の切れ目での未来の考えの率 | 見つからない | 経験サンプリングの活動別の表 |
| K-10 | Foster & Keane 2015 の数値 | 出版社 403・保管庫 405 | ブラウザで UCD の保管庫(ユーザーの手) |
| K-11 | Meyer ほか 1997・Einstein ほか 1995 の本文 | 抄録も取れず | 大学図書館 |
| K-12 | Milkman 2021 の補足資料の訂正(2025-10)の中身 | 未読 | PMC12582327 |

- ユーザーの判断や手作業が要るもの: 有償の本文(K-2・K-8・K-11)を大学図書館で読むか、K-10 をブラウザで開くか。ドメインの許可が要る取得は無い。

## §v2 への当てはめ(案・未決。親が判断する材料)

### A 驚き駆動(10-03 §7-3 4-2)

- 驚きの点数(0〜5)と、本人が書いた予想の起こりにくさの関係を記録すれば、人の値(人の中 r = .78・人の間 .65〜.73)と比べる診断の欄になります(推測)。ただし人の値は実験室とクイズの値で、日常の予定の値ではありません。
- 予想外を見ても止まらない人が 22% いること(#2)と、熟考の重みが人で四分位 0.29〜0.59 に散ること(#9)は、「全員が同じ割合でよく考える」なら画一性の兆し、という監視(R-88 の person_spread)の材料になります。値そのものを目標にはしません。
- 考え直しの強さが「探す費用と利益・難しさ・使える時間」で変わる(#1・#35)ことと、費用と利益で熟考を増やす(#12)ことは、閾値をコードに置かず判断モデルに任せる 10-03 の線と同じ向きです(推測)。
- 慣れ(前に起きた変化には驚かない・#1)は、記憶に「前にもあった」が載れば自然に出るはずです。驚きの点数が同じ出来事の繰り返しで下がるかを検査の欄にできます(推測)。

### B 予定を思い出す仕組み(AT1・CA5・CA7・MR7)

- やらなかった予定の理由の照合値: 忘れ 約 13%・付け替え 約 58%・相手の取り消しや不可能 約 29%(#15)。CA5 で「予定の変更」を計器にするなら、変更の大半が付け替えであることと、約束済みの予定ほど守られることが形の錨です(推測)。
- 予定を見直す回数: 1 日 約 10〜13 回(#15・再計算)・職場の課題は 1 日 4.4 回(#17)。B5 に近い予定を載せる回数や、判断のついでに思い出す回数の桁の目安になります(推測)。手帳(カレンダー)を持つ人は見直す回数が少ないので、v2 の本人がカレンダーを持つ形では、思い出しは少なめでよい向きです(推測)。
- 実行意図(本人が書く「もし〜なら」)の効き目は「思い出す」で d = .54(k 11)。アラームの現場の上乗せは数ポイント(#23)。v2 で実行意図とアラームを入れたとき、守られる率が上がる向きと大きさの桁の照合に使えます(推測)。d を確率に直す式は本書では作りません(expedient になるため)。

### C 入口 3「内側の圧力」(09-25 §4.2・§4.5)

- 未来の考えは 1 日 約 60 回(約 16 分に 1 回・二次)、経験サンプリングでは展望記憶 13〜15%・未来全体 30%(#16)。一人のとき・朝・移動の場所で多い(#16・#17・#29)。09-25 §4.5 の「暇な時間 × 内側の圧力」の形と同じ向きです(推測)。
- 展望記憶の考えの 61% は内側のきっかけ(#16)、心のさまよいの 88% はきっかけを言えて半分が内側(#30)。内側の入口だけで予定を思い出させる形と、外の手がかりで思い出す形(R-89 §1-2 の 45%)の両方が要る、という材料です(推測)。
- 回数の錨はどれも学生の自己申告で、測り方で倍以上ずれます。値に合わせるより、幅と形(一人・朝・移動で多い)で監視するのが原典に合う扱いです(推測)。
