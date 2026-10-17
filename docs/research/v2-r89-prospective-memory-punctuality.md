# R-89 答申: 展望記憶・実行意図・時間厳守と遅刻・活動計画の先行例(行動の時刻 AT1〜AT3・CA8 の材料)

<!-- hdr:v1 -->
- **分野**: 認知心理学(展望記憶) #12 / 社会心理学(実行意図・計画錯誤) #13 / 交通工学(出発時刻の選択・鉄道の遅延) #2 / 性格心理学 #14 / ABM方法論 #21 | **重要度**: P1(指示書 10-03 §7-2・§7-3 4-1 の保留の議題 H1「行動の時刻」。決定記録 09-25 §8 のリサーチ 2・6・7)
- **一次確認**: **B**(サブ実読。本文を自分で抽出した原典 7・取得ツール経由の本文 8・抄録または二次 23・未読 2・空欄は §7)・親検収 済(第320・2026-10-03: 国交省 令和 6 年度の遅延「見える化」PDF(取得済み)から対象路線平均 10.0 日(10 分以下 6.3・10〜30 分 3.0・30 分超 0.5)と埼京線 19.8 日を抽出して一致。Kvavilashvili & Fisher 2007 の 59/74%・Gollwitzer & Sheeran 2006 の d=.65 は既知の値と一致。△ 23 本の抄録は親未読。等級 B+)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-03・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ(PDF は取得ツールが保存した写しか標準出力を pymupdf で抽出。国交省の PDF 1 本だけ `data/research_cache/r89/` に取得・MANIFEST.md に URL・日時・md5)・コミットなし・台帳/設計書/src 未編集。
> 既存答申との関係: 熟考の頻度・習慣 35〜43% = [R-88](v2-r88-llm-humanlikeness-deliberation-vision.md) / 習慣の錨・Lally の 66 日の不在 = [R-68](v2-r68-memory-rework-anchors.md) / 経路選択の錨 = [R-61](v2-r61-route-choice-anchors.md) / 時間の解像度 = [R-73](v2-r73-time-model-des.md) / 誠実性と時間厳守(C2・K-1) = [性格の答申](v2-personality-traits-research.md) / スマホを手に取る回数・遅刻の連絡の手段 = R-85。本書は重なる値を再掲せずリンクし、足りない値だけを足す。
> 対象の草案: [時刻とカレンダーの設計ラウンドの草案](../design/v2-calendar-timing-design-round-draft.md) AT1・AT2・AT3・CA8。

## 結論(5 行)

1. **思い出し方(AT1)には錨がある**: 7 日後の決まった時刻に電話をかける自然な課題(Kvavilashvili & Fisher 2007・原典本文)では、外部のリマインダーを使わない条件で ±10 分以内にかけた人は 59%(研究 1)と 74%(研究 2)でした。遅れた人の多くは「忘れていて後で思い出した」と答えています。研究 1 で思い出したきっかけは、偶然の外の手がかり 45%・偶然の内の連想 22%・きっかけなし 24% で、自分から計画して思い出したのは 9% だけでした。思い出す回数は当日に増えます(J 字)。「前もって何分前に思い出すか」の分布は**空欄**です。
2. **アラームと「もし〜なら」の効き目(AT1 (b))**: 実験室の課題では、自分の記憶だけだと約 45% を忘れ、リマインダーを使うと忘れは約 5% になります(Gilbert ほか 2023 のレビュー)。実行意図は目標達成に d = .65(94 件・Gollwitzer & Sheeran 2006 の抄録)、展望記憶に対しては若年成人で d = 0.445(36 比較・Chen ほか 2015 の抄録)。日本の 20〜69 歳では予定をデジタルで管理する人が 44.9%(紙との併用を含む)です。リマインダーそのものの利用率は**空欄**です。
3. **移動時間の見積り(AT2)は「過小評価」と決められない**: 計画錯誤の古典は卒論の完了日数で予測 33.9 日・実際 55.5 日です(Buehler ほか 1994・二次)。ただしこれは移動の値ではありません。通勤の所要時間は、申告が実測の平均 1.5 倍でした(Peer ほか 2014・抄録)。短い通勤は過大に、長い通勤は過小に申告されるという報告もあります(二次)。日本の就業者は前もって着く人が多く、始業前に出社する人のうち 43.8% が 30 分以上前に着きます。移動時間の見積りの錨は「誤差の向きと大きさ」より「余裕の取り方」の側にあります。
4. **遅刻の出方(AT3)の照合値**: 東京圏 46 路線では、5 分以上の遅延証明書が出た平日は 20 日あたり平均 10.0 日です(10 分以下 6.3・10〜30 分 3.0・30 分超 0.5)。路線で 1.3〜19.8 日の幅があり、渋谷の路線では山手線 14.9・副都心線 15.1・銀座線 1.9 日です(国交省 令和 6 年度・原典)。ただし証明書は路線単位の最大の遅れで、個々の乗客の遅れとは一致しません。2024 年春入社の新入社員のうち、自分の失敗で始業に遅刻したことがある人は 22.0%、待ち合わせでは 23.0% です。連絡なしの遅れを何分まで許すかは「10 分」が最多です。
5. **先行例の時刻の決め方**: 活動ベースの交通モデルの多くは、出発時刻を観測分布からの抽選(TASHA)、決定木(ALBATROSS)、ハザードモデル(CEMDAP)、効用の中の遅刻の罰(MATSim・Small 1982 の 1:0.61:2.4)で決めます。Generative Agents は計画を 1 日 → 1 時間 → 5〜15 分と細かくします。読んだ範囲では、どれも「本人が思い出し損ねる」過程を持っていません。誠実性と時間厳守の r(Back ほか 2006)は今回も**空欄**です。

## §0 出典の表

等級: **◎** 原典本文で数値まで逐語確認(本文を自分で抽出) / **○** 取得ツール経由の本文(逐語の一部は取得ツールの要約を含む) / **△** 抄録・二次 / **×** 未読(空欄)

| # | 出典 | URL | 等級 | 読んだ範囲 |
|---|---|---|---|---|
| 1 | Kvavilashvili L., Fisher L. 2007「Is time-based prospective remembering mediated by self-initiated rehearsals?」J Exp Psychol: General 136(1):112-132 | https://uhra.herts.ac.uk/id/eprint/2323/1/103120.pdf (著者版) / https://doi.org/10.1037/0096-3445.136.1.112 | ◎ | 著者版 PDF 全文(研究 1〜3 の結果) |
| 2 | Ellis D.A., Jenkins R. 2015「Watch-wearing as a marker of conscientiousness」PeerJ 3:e1210 | https://doi.org/10.7717/peerj.1210 (Europe PMC PMC4556152 の全文 XML) | ◎ | 全文(研究 3 の到着時刻) |
| 3 | 国土交通省 鉄道局「東京圏の鉄道路線の遅延「見える化」(令和 6 年度)」令和 8 年 4 月 10 日 | https://www.mlit.go.jp/report/press/content/001995846.pdf | ◎ | 20 頁 PDF の資料 1-1・資料 2・留意点(`data/research_cache/r89/`) |
| 4 | Levine R.V., Norenzayan A. 1999「The Pace of Life in 31 Countries」J Cross-Cult Psychol 30(2):178-205 | https://www2.psych.ubc.ca/~ara/Manuscripts/Levine&Norenzayan%20POL.pdf / https://doi.org/10.1177/0022022199030002003 | ◎ | 方法・表 1 |
| 5 | MATSim User Guide(2014-09-12 版)§6.4・§7.3.2 | https://svn.vsp.tu-berlin.de/repos/public-svn/publications/vspwp/2014/14-20/user-guide-0.6.0-2014-09-12.pdf | ◎ | 採点関数の既定値・TimeAllocationMutator の節 |
| 6 | Park J.S. ほか 2023「Generative Agents: Interactive Simulacra of Human Behavior」 | https://arxiv.org/abs/2304.03442 | ◎ | §4.3 計画と再計画 |
| 7 | Taatgen N., van Rijn H., Anderson J.R. 2005「The ACT-R 6.0 temporal module」(文書) | https://www.ai.rug.nl/~niels/oldwww/temporal-ACTR6/temporal.pdf | ◎ | 全文(式と既定値) |
| 8 | McDaniel M.A., Einstein G.O. 2011「The neuropsychology of prospective memory in normal aging: A componential approach」Neuropsychologia 49(8):2147-2155 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3095717/ | ○ | 多過程理論・時間ベースの定義(脚注 2)・年齢差の数値 |
| 9 | Niedźwieńska A. ほか 2020「Everyday memory failures across adulthood」PLoS ONE 15(9):e0239581 | https://doi.org/10.1371/journal.pone.0239581 | ○ | 方法・結果(表 2 は画像で未読) |
| 10 | Gilbert S.J. ほか 2023「Outsourcing memory to external tools: A review of 'intention offloading'」Psychon Bull Rev 30(1):60-76 | https://pmc.ncbi.nlm.nih.gov/articles/PMC9971128/ | ○ | 序論・リマインダーの効果の節 |
| 11 | Rogers T., Milkman K.L. 2016「Reminders Through Association」Psychol Sci 27(7):973-986 | https://pmc.ncbi.nlm.nih.gov/articles/PMC5510470/ | ○ | 抄録(逐語)・研究 1〜5 の数値 |
| 12 | シチズン時計「社会人 1 年目の仕事と時間意識」調査(2024-12-13 公開) Q7・調査概要 | https://www.citizen.co.jp/research/20241213/07.html | ○ | 本文(遅刻時間の全分布は画像で未読) |
| 13 | シチズン時計「「時の記念日」100 周年に聞く、ビジネスパーソンの時間遵守調査」Q3(2020) | https://www.citizen.co.jp/research/20200521/03.html | ○ | 本文(全分布は画像で未読) |
| 14 | カオナビ タレントインテリジェンス総研「始業前の出社についての疑問」(2024-07-18) | https://ri.kaonavi.jp/20240718/ | ○ | 調査概要・問 3 |
| 15 | クロス・マーケティング「手帳に関する調査(2026 年)」 | https://www.cross-m.co.jp/report/trend-eye/20260115schedulebook | ○ | 調査概要・予定管理の手段 |
| 16 | Einstein G.O., McDaniel M.A. 1990「Normal aging and prospective memory」JEP:LMC 16(4):717-726 | https://doi.org/10.1037/0278-7393.16.4.717 | △ | 抄録(PubMed) |
| 17 | Einstein G.O. ほか 1995(時間ベースと事象ベースの年齢差) | なし | △ | 二次(検索結果の要約)のみ |
| 18 | Rendell P.G., Craik F.I.M. 2000「Virtual week and actual week」Appl Cogn Psychol 14:S43-S62 | https://doi.org/10.1002/acp.770 | △ | 抄録(OpenAlex) |
| 19 | Crovitz H.F., Daniel W.F. 1984「Measurements of everyday memory」Bull Psychon Soc 22(5):413-414 | https://doi.org/10.3758/BF03333861 | △ | 抄録(Springer のメタデータ) |
| 20 | Terry W.S. 1988「Everyday forgetting: Data from a diary study」Psychol Rep 62(1):299-303 | https://doi.org/10.2466/pr0.1988.62.1.299 | △ | 抄録(OpenAlex) |
| 21 | Anderson F.T., McDaniel M.A. 2019「Hey buddy, why don't we take it outside」Mem Cogn 47:47-62 | https://doi.org/10.3758/s13421-018-0849-x | △ | 抄録(Springer のメタデータ) |
| 22 | Gardner R.S., Ascoli G.A. 2015「The natural frequency of human prospective memory increases with age」Psychol Aging 30(2):209-219 | https://doi.org/10.1037/a0038876 | △ | 抄録(Europe PMC) |
| 23 | Harris J.E., Wilkins A.J. 1982「Remembering to do things」Human Learning 1:123-136 | なし | △ | 二次(後続論文の記述)のみ |
| 24 | Sellen A.J. ほか 1997(バッジを押す自然な時間ベース課題) | なし | △ | 二次(#1 の本文と検索結果の要約) |
| 25 | Gollwitzer P.M., Sheeran P. 2006「Implementation intentions and goal achievement: A meta-analysis」Adv Exp Soc Psychol 38:69-119 | https://kops.uni-konstanz.de/entities/publication/2e749bfb-8533-437c-8203-7e788c910c5f | △ | 抄録(KOPS)。PDF は画像のみで本文未読 |
| 26 | Chen X.-J. ほか 2015「The effect of implementation intention on prospective memory」Psychiatry Res 226(1):14-22 | https://doi.org/10.1016/j.psychres.2015.01.011 | △ | 抄録(PubMed) |
| 27 | Back M.D., Schmukle S.C., Egloff B. 2006「Who is late and who is early?」J Res Pers 40:841-848 | https://doi.org/10.1016/j.jrp.2005.11.003 | △ | 抄録の要約(二次)。r は空欄 |
| 28 | @DIME「社内会議や取引先との打ち合わせの遅刻、何分までなら許せる?」(シチズン時計 2020 の Q4 の紹介記事) | https://dime.jp/genre/936462/ | △ | 二次(記事本文) |
| 29 | Buehler R., Griffin D., Ross M. 1994「Exploring the "planning fallacy"」JPSP 67(3):366-381 | https://doi.org/10.1037/0022-3514.67.3.366 | △ | 抄録(OpenAlex)。数値は二次。PDF は画像のみ |
| 30 | Peer S., Knockaert J., Koster P., Verhoef E.T. 2014「Over-reporting vs. overreacting」Transp Res A 69:476-494 | https://doi.org/10.1016/j.tra.2014.07.005 | △ | 抄録(RePEc) |
| 31 | Carrion C., Levinson D. 2019「Over- and Under-Estimation of Travel Time on Commute Trips」Urban Sci 3(3):70 | https://doi.org/10.3390/urbansci3030070 | △ | 抄録(Crossref)。閾値の数値は二次 |
| 32 | Small K.A. 1982「The Scheduling of Consumer Activities: Work Trips」Am Econ Rev 72(3):467-479 | https://www.jstor.org/stable/1831545 | △ | 二次(引用する論文の記述)のみ |
| 33 | Parthasarathi P., Srivastava A., Geroliminis N., Levinson D. 2011「The importance of being early」Transportation 38:227 | https://doi.org/10.1007/s11116-010-9301-1 | △ | 抄録 |
| 34 | Miller E.J., Roorda M.J. 2003 TASHA, TRR 1831:114-121 | なし | △ | 二次のみ |
| 35 | Arentze T., Timmermans H. ほか ALBATROSS(TRR 1706 2000・Transp Res B 2004) | なし | △ | 二次のみ |
| 36 | Bhat C.R. ほか CEMDAP(2004)・Bhat & Steed 2002 | なし | △ | 二次のみ |
| 37 | Piao J. ほか 2025 AgentSociety | https://arxiv.org/abs/2502.08691 | △ | 二次(検索結果の要約)のみ |
| 38 | Taatgen N., van Rijn H., Anderson J. 2007「An integrated theory of prospective time interval estimation」Psychol Rev 114(3):577-598 | https://doi.org/10.1037/0033-295X.114.3.577 | △ | 抄録(OpenAlex) |
| 39 | Kahneman D., Tversky A. 1979(計画錯誤の命名) | なし | × | 未読(空欄) |
| 40 | FEATHERS(フランダースの活動ベースモデル) | なし | × | 未読(空欄) |

## §1 展望記憶(prospective memory)

### 1-1 時間ベースと事象ベース
- Einstein & McDaniel 1990(#16・抄録)の実験は「目標の出来事が起きたら行動する」課題、つまり**事象ベースだけ**です。抄録の逐語: 「both experiments showed no age deficits in prospective memory」「external aids and unfamiliar target events benefit prospective memory performance」。時間ベースと事象ベースの区別をこの論文に帰すのは後続の文献の慣行で、時間ベースの年齢差を直接調べたのは Einstein ほか 1995(#17・二次)です。設計書でこの区別を引くときは「1990 で区別・1995 で時間ベースを検証」と書くのが正確です。
- 時間ベースの定義(#8 脚注 2・○): 「typically involves monitoring a clock for the appropriate time for performing an intention」「We assume that time-based tasks are nonfocal」「substantial age differences are generally found with time-based prospective memory tasks」。
- 多過程理論(#8・○、McDaniel & Einstein 2000 を引く): 思い出す道は 2 つです。目標の出来事が記憶から自発的に呼び起こす道(spontaneous retrieval)と、環境を能動的に見張る道(strategic monitoring)。手がかりが今の作業の焦点に無い(nonfocal)ときは見張りに頼ります。
- 実験室の数値(#8・○): 遅延実行課題で高齢者は「93% remembering when they could perform the task immediately to 45%」(5 秒の遅れの後)、若年は 97% → 90%。18 研究の平均で、焦点の手がかりでは年齢差 11%・非焦点では 23%。

### 1-2 自然な場面の時間ベースの課題(本書の中心の錨)
Kvavilashvili & Fisher 2007(#1・◎)。月曜に会い、7 日目の日曜の決まった時刻に実験者へ電話をかける課題です。待つ間に「意図が頭に浮かんだ回数ときっかけ」を日記に書きます。研究 1 の手続きの説明は「how people remember to carry out an everyday task in the future without the help of external reminders」で、外部のリマインダーを使わない条件です。

| 研究 | 対象 | ±10 分以内(HIT) | 10〜60 分遅れ | 1 時間超の遅れ | 完全に忘れた | 思い出した回数(7 日) |
|---|---|---|---|---|---|---|
| 研究 1 | 心理学の学部生 39 人(18〜47 歳) | 23 人 59% | 6 人 15% [再計算] | 10 人 26% [再計算](最大 8 時間) | 0 | 平均 8.38(範囲 2〜26) |
| 研究 2 | 若年 34・高齢 36(計 70) | 52 人 74% [再計算] | 6 人 9% [再計算] | 9 人 13% [再計算](最大 7 時間 20 分) | 3 人 4% [再計算] | 平均 12.40(範囲 2〜26) |
| 研究 3(時間ベース) | 19 人 | 10 人 53% | 4 人 21% [再計算] | 5 人 26% [再計算](最大 深夜 0 時) | 0 | 平均 9.37(最終日だけで 1.84) |
| 研究 3(事象ベース=携帯の文字メッセージを受けたら) | 20 人 | 16 人 80% | 3 人 | 1 人(1 時間 10 分) | 0 | 平均 6.75(最終日だけで 0.95) |

逐語(研究 1): 「23 participants (59%) remembered to call within the 10 minutes of critical time (which was counted as on-time response), and 16 participants (41%) were more than 10 minutes late」「out of 16 late callers only three indicated that they remembered but were unable to make a phone call at a designated time. The other participants who were late admitted they had forgotten about the task and remembered only at some later point」。
- 遅れの主因は**忘れ**です。研究 1 では遅れた 16 人のうち 13 人(参加者全体の 33% [再計算])が「忘れていて後で思い出した」と答えました。研究 3 の時間ベースでも 9 人中 8 人が忘れでした。
- 思い出したきっかけ(研究 1・327 回): 「only 9% (N=29) were coded as being cued by self-initiated planning thoughts. Forty-five percent were coded as being triggered by incidental external (N=147) and 22% by incidental internal cues (N=71). In 24% of cases (N=80) the rehearsals were reported to have no apparent triggers」。
- 思い出す時期: 時刻どおりにかけた群は「a clear J-shaped pattern of rehearsals」で、最終日(日曜)の割合が他のどの日より高い。遅れた群には J 字がありません。研究 2 では日曜の 1 時間あたりの割合(.44)が月曜(.24)の約 2 倍でした。
- 年齢: 研究 2 で時刻どおりは若年 68%・高齢 81%(χ²=1.52・p=.21・有意差なし)。
- 動機づけの操作は成績に効きませんでした(研究 2・全て F<1)。
- 事象ベースは時間ベースより成績が良い(研究 3・自己申告を考慮すると事象ベース 100%・時間ベース 58%・χ²=8.19・p<.005)。

### 1-3 日常の記憶の失敗のうち展望記憶の割合(「約半分」の出どころ)
- Crovitz & Daniel 1984(#19・抄録): 若年 47 人の日記・1,000 件の「忘れ」。抄録は「A table of the 33 types of forgetting that cover 492 of the 1,000 instances is given」までで、**展望記憶の割合の数値は抄録に無い**。「約 50%」「半分以上」は後続の文献の要約です。
- Terry 1988(#20・抄録): 50 人・750 件。「Most failures involved the forgetting to perform a future action ... as opposed to forgetting facts, names, or other information once known」。割合の数値は抄録に無い(後続の文献が「70%」と書く例あり・二次)。
- Gilbert ほか 2023(#10・○)の序論: 「diary studies suggest that 50-70% of everyday memory failures reflect a failure to remember delayed intentions」(Crovitz & Daniel 1984・Terry 1988 を引く)。設計書で「約半分」と書くなら、この 2 本の原典の割合は未確認と添える必要があります。
- 本文まで読めた日記研究: Niedźwieńska ほか 2020(#9・○)。19〜80 歳の 152 人・7 日間・1,319 件(1 人平均 8.68 件・SD 5.12・範囲 2〜25、1 日あたり約 1.24 件 [再計算])。うち「838 (64%) were PM failures」、回想の失敗 20%、うっかり 16%。若年が中年・高齢より展望記憶の失敗を多く報告しました(中年と高齢の差なし p=0.981)。時間ベースと事象ベースの内訳は表 2(画像)で**未読=空欄**。

### 1-4 年齢の逆説
- Rendell & Craik 2000(#18・抄録): 実験室の盤上ゲーム(Virtual Week)では若年が上、実生活の同様の課題(Actual Week)では「the older adults were generally superior to their younger counterparts」。
- #9 も自然な場面での高齢者の優位を支持しています。#1 の研究 2 は数値上は高齢が上でしたが有意ではありません。
- v2 への含み: 年齢で「忘れやすさ」を下げる向きの錨は、実験室と日常で逆になります。片方だけ写すと向きを誤ります。

### 1-5 思い出す頻度(日常)
- Anderson & McDaniel 2019(#21・抄録): 「PM occupies our thoughts approximately 13-15% of the time」「Of those PM thoughts, participants reported that 61% were internally cued」。一人のときと、1 日の早い時間に多い。
- Gardner & Ascoli 2015(#22・抄録): 回想は全年齢で約 10%。若年は展望記憶と回想が同程度、高齢は展望記憶が 2 倍。
- 時計を見る回数が目標の時刻の近くで増える(Harris & Wilkins 1982・#23・二次。TWTE モデル)。#1 は長い遅れでも J 字を再現した、と自ら書いています(#1 本文)。
- **「予定の何分前に思い出すか」の分布(分単位)は空欄**です。#1 は日単位、Harris & Wilkins は 3・9 分の課題です。

## §2 実行意図・リマインダー

### 2-1 実行意図(implementation intentions)
- Gollwitzer & Sheeran 2006(#25・抄録): 「Findings from 94 independent tests showed that implementation intentions had a positive effect of medium-to-large magnitude (d = .65) on goal attainment」。働きは「initiation of goal striving」など 4 つ。結果の種類ごとの d(「始めること」「機会を逃さないこと」)は本文が画像の PDF で**未読=空欄**。
- Chen ほか 2015(#26・抄録): 展望記憶への効果。36 比較。「for healthy young adults ... medium effect size (d = 0.445)」「combined verbal and imagery form ... (d = 0.590)」「For older adults ... (d = 0.680)」「implementation intention seemed to reduce ongoing task performances in young adults as reflected by longer reaction time (d = 0.224)」。全体の d = 0.508 という値は二次の要約にだけあり、抄録には無いので使いません。
- 時間ベースの展望記憶に限った実行意図の効果量は**空欄**です。

### 2-2 リマインダー・外部の手がかり
- Gilbert ほか 2023(#10・○): 自分で選んでリマインダーを置く実験で「mean accuracy using internal memory is typically around 50-60%」「accuracy is typically 90-100%」(リマインダーあり)。Gilbert ほか 2020 では「a forgetting rate of about 45% when using their own memory but only around 5% using external reminders」。人は最適より多くリマインダーを置く偏りを持ちます。実生活でどれだけの意図をリマインダーに預けているかの率は、このレビューに**無い**。
- Rogers & Milkman 2016(#11・○): 目立つ物に意図を結びつける手がかり。研究 1 は実行 74% 対 対照 42%(N=77)。研究 3 は手がかり 92%・書いたリマインダー 78%・対照 71%(書いたリマインダーと対照の差は有意でない p=.413)。抄録の逐語: 「they can be more effective than written or electronic reminder messages」。補足研究 S1 では予定の時刻に届くデジタルのリマインダーより効いた例もありますが、著者は「digital reminders may be a superior technology in some contexts」とも書いています。
- 日本の予定管理の道具(#15・○): 20〜69 歳 1,100 人(2026 年 1 月)。「紙の手帳のみ利用」14.8%・「紙・デジタル併用」16.2%・「デジタルツールのみ利用」28.7%。残りの約 40% [再計算] の内訳は本文に無い(画像)。**通知・リマインダーの利用率は空欄**です。

## §3 時間厳守と遅刻

### 3-1 誠実性と時間厳守
- Back ほか 2006(#27・抄録の要約): 実験への到着時刻・早さ・遅さの 3 指標で、誠実性は 3 つ全てと関係、協調性は到着時刻と早さ、神経症傾向は早さと関係。**r は今回も空欄**(本文は有料。性格の答申 K-1 は解けていない)。
- Ellis & Jenkins 2015(#2・◎)の研究 3: 学部の実験に来た 90 人のうち ±15 分を超えた 5 人を除き、「On average, the remaining participants arrived 2.19 min before the appointed time (SD = 5.95)」。腕時計をする 34 人は「M = 4.12, SD = 5.45」分早く、しない 51 人は「M = .90, SD = 5.96」(t(83)=2.52・p=.01・d=.55)。著者は自分たちの効果量が Back ほか 2006 の誠実性と時間厳守の相関より「far higher」と書いており、Back の r は小さいと読めます(推測。値は空欄)。

### 3-2 日本の遅刻と到着の調査(ネット調査・自己申告)
| 調査 | 対象 | 値(本文の逐語) | 等級 |
|---|---|---|---|
| シチズン 2024(#12) | 2024 年春入社の正社員 400 人(男女 200 ずつ)・2024 年 10 月 11〜21 日 | 始業: 自分の失敗の遅刻経験「ある」22.0%・最多の遅刻時間「5分」(5.3%)・「1 時間以上」5.7%。待ち合わせ: 「ある」23.0%・最多「10分」(6.8%)。交通機関の遅れなど自分の失敗でないものは除く | ○ |
| シチズン 2020(#13) | ビジネスパーソン 400 人・2020 年 4 月 3〜6 日(調査概要は #28 の記事による) | 「予定時刻の何分前に到着しますか」。5 分前までに着く: 始業 92.8%・社内の会議 77.2%・取引先 92.4%・家族や友人 77.4%。最多は始業「30分前」32.3%・会議「5分前」39.3%・取引先「10分前」32.5%・家族友人「5分前」31.8% | ○ |
| シチズン 2020 Q4(#28 の紹介記事) | 同上 | 連絡なしの遅刻を何分まで許すか: 社内の会議「10分」29.3%・「5分」28.5%・「10分まで」に 7 割以上。取引先「10分」25.5%・「10分まで」57.1%。家族や友人「10分」27.5%・「遅れても気にしない」13.3% | △ |
| カオナビ 2024(#14) | 20〜59 歳の有業者 1,000 人(自由業を除く)・2024 年 3 月 18〜25 日 | 始業前に出社する人のうち「30分以上前」43.8%・「15〜30分未満」32.9%・「10〜15分未満」12%。「始業前に出社しない」人は集計から除く | ○ |

- 全分布(遅刻時間の各区分の割合)は画像で**未読=空欄**です。
- 1 人が 1 か月に何回遅刻するか、という頻度の公的な実測は見つかりません(**空欄**)。

### 3-3 鉄道の遅延(東京圏・国交省・#3 ◎)
資料 1-1 の注: 「対象４６路線の令和６年度（平日）の１年間の遅延証明書発行日数を１か月（平日20日間）当たりの平均に換算した日数」。留意点の逐語: 「各鉄道事業者で遅延証明書の発行条件に違いがある」「遅延証明書は、路線単位の最大遅延時間に基づいており、個々の列車の遅延時間や個々の利用者の遅延時間とは必ずしも一致しない」。

| 路線 | 合計(日/平日 20 日) | 10 分以下 | 10 分超〜30 分以下 | 30 分超 |
|---|---|---|---|---|
| **対象路線平均(46 路線)** | **10.0** | 6.3 | 3.0 | 0.5 |
| JR 山手線 | 14.9 | 9.7 | 4.8 | 0.4 |
| JR 埼京線・川越線 | 19.8 | 5.7 | 11.3 | 2.8 |
| 東京メトロ 銀座線 | 1.9 | 1.7 | 0.2 | 0.1 |
| 東京メトロ 半蔵門線 | 9.2 | 7.0 | 2.0 | 0.2 |
| 東京メトロ 副都心線 | 15.1 | 10.5 | 4.3 | 0.3 |
| 東急 東横線 | 5.0 | 3.6 | 1.4 | 0.0 |
| 東急 田園都市線 | 3.6 | 2.6 | 0.8 | 0.2 |
| 京王 井の頭線 | 2.8 | 2.5 | 0.3 | 0.1 |

- 46 路線の最小は東急大井町線 1.3 日、最大は埼京線 19.8 日です(同表)。
- 証明書の発行時間帯は事業者で違います(例: 東急 初電〜9:00、京王・東京メトロ・都営 初電〜10:00。JR 東日本は表の配置から初電〜10:00 と読んだ=○)。**夕方以降の遅れはこの表に入っていません**。
- 遅延の原因(資料 2): 10 分未満の小規模な遅延(令和 6 年 11 月の平日 20 日・延べ 349 件)は旅客関係 63.9%・他社他線区の影響 23.2%。30 分以上(令和 6 年度・延べ 309 件)は旅客関係 55.0%・他社他線区 20.4%。
- 証明書は 5 分以上の遅れで出る、という一般的な説明は検索結果の二次情報にあり、本 PDF では「発行条件に違いがある」とだけ書かれています。

### 3-4 文化差(Levine & Norenzayan 1999・#4 ◎)
- 31 か国の大都市で、歩く速さ(60 フィート)・郵便局の窓口の速さ・銀行の時計 15 個の正確さを 1992〜1995 年の夏に測りました。
- 日本(東京)は総合 4 位(-2.68)・歩く速さ 12.11 秒(7 位)・郵便 18.61 秒(4 位)・時計のずれ 35.00 秒(6 位)。1 位はスイス(時計のずれ 19.29 秒)、最下位はメキシコ。
- 約束への遅れそのものは測っていません。

### 3-5 計画錯誤と移動時間の見積り
- Buehler ほか 1994(#29): 抄録の逐語「Ss' predictions of their completion times were too optimistic for a variety of academic and nonacademic tasks」「In Study 5, observer Ss overestimated others' completion times」。研究 1 の数値は**二次**で、卒論 37 人・予測 33.9 日・最良 27.4 日・最悪 48.6 日・実際 55.5 日・予測どおり約 30%(実際/予測 = 1.64 [再計算])。本文 PDF は画像のみで未読。
- Peer ほか 2014(#30・抄録): 朝の通勤の車内時間の申告は実測の平均「overstated by a factor of 1.5」。ただし「In neither case did they find robust evidence that drivers act as though they misperceive travel times to the degree they misreport them」(取得ツールの要約)。**申告の誤差と行動の誤差は別**です。
- Carrion & Levinson 2019(#31・抄録): ミネアポリス・セントポールの通勤で、申告と GPS の差に道路網の形・到着の融通・交通情報の有無が効く。短い通勤(20 分未満)は過大、長い通勤(25 分超)は過小に申告、という閾値は**二次**の記述です。
- 移動時間の見積りの研究で「出発の判断に使う見積り」(行動の誤差)を測ったものは見つかりません(**空欄**)。日本の通勤者の見積り誤差も**空欄**です。

## §4 活動計画の先行例(出発時刻の決め方・遅れの扱い)

| 先行例 | 出発・開始時刻の決め方 | 遅れの扱い | 等級 |
|---|---|---|---|
| Small 1982(#32) | 出発時刻を、移動時間 α・早着 β・遅着 γ・遅刻の固定罰 δ の費用の最小で選ぶ。比は 1 : 0.61 : 2.4 | 遅刻は 1 分あたり移動時間の 2.4 倍の費用(+固定罰) | △ |
| Parthasarathi ほか 2011(#33) | 早着と遅着の費用比を 6 都市の調査と交通データから推定 | 「earliness being less expensive than lateness」が地域と年をまたいで成り立つ | △ |
| MATSim(#5) | 時刻は進化的な再計画(TimeAllocationMutator が終了時刻をランダムにずらし、良いものが選ばれる) | 遅着の罰 βlate = -18/時(既定)。逐語「The "typical" parameters of the Vickrey scenario are β̂early = -6, β̂travel = -12, and β̂late = -18 ... this translates into βperf = 6, βtravel = -6, and βlate = -18」「introduced ... for a lack of estimated parameters」 | ◎ |
| TASHA(#34) | 開始時刻・長さを観測の同時分布から抽選。優先順(仕事→学校→…)で予定に挿入 | 衝突は優先順だけで解く(Roorda & Miller 2005 の実証で合わない例が多い) | △ |
| ALBATROSS(#35) | 日誌データから学習した決定木(CHAID)で開始時刻などを決め、モンテカルロで抽選 | 削除後の再計画ができない、との指摘 | △ |
| CEMDAP(#36) | 出発時刻・滞在の長さを連続時間のハザードモデルで決める | 空欄 | △ |
| FEATHERS(#40) | 空欄 | 空欄 | × |
| Generative Agents(#6) | LLM が 1 日の大筋を書き、1 時間単位、さらに 5〜15 分単位に分解。逐語「we only generate the high-level plan in advance and then recursively decompose the near future into the moment-to-moment action plan just in time」 | 各 tick で知覚し、反応するかを LLM が決め、必要なら計画を作り直す(§4.3.1) | ◎ |
| AgentSociety(#37) | 欲求(マズロー)の優先度から行動計画を作る | 空欄 | △ |
| ACT-R 時間モジュール(#7・#38) | 時間は間隔が少しずつ伸びる「tick」で数える。tn = a·tn-1 + 雑音(sd = b·a·tn-1)。既定値 a = 1.1・b = 0.015・starttick = 1.1(単位は文書に無い=空欄) | 長い間隔ほど見積りが粗い(スカラー性) | ◎(文書)・△(論文) |

- どの交通モデルも、予定を「思い出し損ねる」過程と、見積りを経験で直す過程を持っていません(本書で読んだ範囲。推測を含む)。遅れは「渋滞・乗り遅れ」と「遅着の罰」で表されます。

## §5 v2 への当てはめ(本書の案=親が判断する材料。未決)

草案の方針: エンジンが「ちょうどいい時刻」を計算して本人を起こす形は避ける。以下は選択肢ごとの錨の有無で、既定値の候補は**推測**を含みます。

### 5-1 AT1 思い出すタイミング
| 選択肢 | 錨 | 既定値の候補(推測) |
|---|---|---|
| (a) 性質から決まる「前もって思い出す時間」 | **分単位の分布は空欄**。性格との結びつき(誠実性 r)も空欄 | 置けない。置くなら expedient と宣言 |
| (b) 本人が置くアラーム | あり: リマインダーで忘れ 45% → 5%(#10・実験室)、実行意図 d = 0.445(若年・#26)。日本の予定のデジタル管理 44.9%(#15) | アラームを置く人の割合は「デジタル管理 44.9%」を上限の目安にできる(推測。リマインダーの利用率そのものは空欄) |
| (c) 専用の知らせなし(他の理由の判断の時に思い出す) | **強い**: 自然な時間ベース課題で、思い出すきっかけの 91% が偶然の外・内の手がかりかきっかけなし、自分で計画したのは 9%(#1)。思い出す回数は当日に増える(J 字) | 外部のリマインダーなしの単発の約束で、±10 分以内 53〜74%・忘れて 1 時間超遅れ 13〜26%(#1 の 3 研究)を照合値にできる |
| (d) (b) を主・無ければ (a)・どちらも無ければ (c) | (b) と (c) は錨あり、(a) は空欄 | (a) の段を外し「(b) か (c)」にすると錨の無い値を置かずに済む(推測) |

- #1 の結果は「思い出す機会を作るのは偶然の手がかりと当日の想起の増加」と読めます。v2 の (c)「他の理由の判断のついでに思い出す」は、この偶然の手がかりの役に近い形です(推測)。

### 5-2 AT2 移動時間の見積り
| 選択肢 | 錨 | 既定値の候補(推測) |
|---|---|---|
| (a) 最短の所要時間 × 本人の係数 | 係数の向きは決まらない。課題の完了は 1.64 倍の過小評価(#29・二次・移動ではない)、通勤の申告は 1.5 倍の過大(#30・申告であり行動ではない)、短い通勤は過大・長い通勤は過小(#31・二次) | 係数の中心を 1.0 とし、ばらつきは expedient。感度試験で結果を駆動していないことを示す |
| (b) 通勤は片道通勤時間の分布 | D-68 の残りの答申(東京都・渋谷区の p10/p50/p90)。本書で新しい錨は無い | 変更なし |
| (c) LLM が初回に見積る | 錨なし | 空欄 |
| 更新 (d)(e)(f) | 経験で見積りを直す速さの錨は空欄。#29 の抄録は「過去の経験を予測に結びつけると楽観の偏りが消えた(研究 4)」 | 回数・係数は expedient |
| (補) 余裕の取り方 | あり: 始業 5 分前までに 92.8%(#13)、始業前に出社する人の 43.8% が 30 分以上前(#14)。大学の実験への到着は平均 2.19 分前・SD 5.95 分(#2) | 見積りの誤差より「余裕(早めに出る幅)」を本人の性質に持たせるほうが錨に合う(推測) |

### 5-3 AT3 遅刻の出方
| 原因 | 錨 | v2 での出し方(本書の案・推測) |
|---|---|---|
| 忘れる | **強い**: 外部の手がかりなしの単発の約束で遅れの大半が忘れ(研究 1: 遅れた 16 人中 13 人)。日常の記憶の失敗の 64% が展望記憶(#9) | AT1 の (c) から自然に出る |
| 見積りの甘さ | 弱い(§3-5)。日本では早めに出る人が多い | AT2 の余裕から出る。単独の照合値は空欄 |
| 会話の長引き | **空欄**(会話が長引いて遅れる率の研究は見つからない) | 強制退出をやめれば出るが、照合値は無い |
| 寄り道 | 空欄 | 本人の判断として自然に出る |
| 電車の遅れ | **あり**: 東京圏 46 路線で 5 分以上の遅延証明書が出る平日は平均 10.0 日/20 日。渋谷の路線で 1.9〜19.8 日。30 分超は平均 0.5 日(#3) | (d) 第 1 段で入れるなら、路線ごとに「その日の朝に遅れがある確率」と遅れの区分を引ける。ただし路線の最大の遅れで個人の遅れではない・朝の時間帯だけ |

- 草案の「エンジンがしないこと」(逆算して起こす・間に合う便に乗せる・時刻で強制退出)は、先行例の交通モデルが全てエンジン側で時刻を最適化している(§4)ことと対照的です。LLM 社会シミュの Generative Agents も計画の時刻は LLM が書きます(#6)。v2 の線に合う先行例は見つかりません(推測)。

### 5-4 CA8 照合と計器(遅刻の欄)
| 照合の欄 | 値 | 使える範囲 | フロア(実データ同士のばらつき) |
|---|---|---|---|
| 単発の約束を時刻どおりに守る率(±10 分) | 53%・59%・74%(#1) | 外部の手がかりなし・英国の学生と高齢者・7 日後の電話 | 研究どうしで 53〜74%(21 ポイント) |
| 約束に遅れた人のうち忘れが原因の割合 | 13/16(研究 1)・8/9(研究 3 時間ベース)(#1) | 同上 | 小さい標本 |
| 到着の早さ | 平均 2.19 分前・SD 5.95 分(#2・大学の心理学部の実験の参加者 17〜48 歳・±15 分外を除く) | 実験への来訪 | 腕時計の有無で 0.90〜4.12 分 |
| 予定の 5 分前までに着く割合 | 77.2〜92.8%(#13・日本・自己申告) | 場面で違う | 場面どうしで 15.6 ポイント |
| 遅刻経験(自分の失敗) | 始業 22.0%・待ち合わせ 23.0%(#12・新入社員・入社から調査まで約半年=推測) | 「経験の有無」で頻度ではない | 2017 年版は「4 人に 1 人」(二次) |
| 許す遅れ | 「10 分」が最多(#28・二次) | 遅刻と見なす線の目安 | 場面で 25.5〜29.3% |
| 鉄道の遅れ(日) | 平均 10.0 日/平日 20 日・30 分超 0.5 日(#3) | 朝の時間帯・路線単位 | 路線で 1.3〜19.8 日 |

- 遅刻の頻度(1 人 1 か月あたり)と、遅れの分の分布(日本の実測)は**空欄**です。CA8 (c) は「計器だけを置いて照合はしない」草案の線のままでよいと読めます。#1 の 3 研究と #3 の鉄道の値は、診断の欄として置けます(推測)。
- これらは較正にも holdout にも使っていない外部の値です。較正に使うかは親とユーザーが決めます。

## §6 写し検査用の注記
- 「日常の忘れの約半分が展望記憶」: 原典 2 本(Crovitz & Daniel 1984・Terry 1988)の抄録に割合の数値は無い。50〜70% はレビュー(#10)の要約。本文まで読めた値は Niedźwieńska 2020 の 64%。
- 「d = .65」: Gollwitzer & Sheeran 2006 の抄録の逐語で、目標達成全般の値。展望記憶に限った値は Chen 2015 の d = 0.445(若年)・0.680(高齢)。
- 「Einstein & McDaniel 1990 が時間ベースと事象ベースを区別」: 1990 の実験は事象ベースだけ。時間ベースの年齢差の検証は 1995(二次)。
- 「Rogers & Milkman 2016 は cue-based reminders」: 論文の語は「reminders-through-association」。
- 「Peer ほか 2014 の bus time estimation」(依頼文の記載): 読んだ抄録は車の朝の通勤の車内時間で、バスではない。
- 鉄道の遅延の値は「路線単位の最大の遅れ」で、個人の遅刻の率ではない。

## §7 空欄の一覧
| # | 空欄 | 理由 | 次の手 |
|---|---|---|---|
| K-1 | Back ほか 2006 の r(誠実性 × 到着時刻・早さ・遅さ) | 本文は有料。抄録にも二次にも値が無い | 大学図書館か著者への依頼(性格の答申 K-1 と同じ) |
| K-2 | 「予定の何分前に思い出すか」の分単位の分布 | 自然な場面の研究は日単位(#1)、実験室は 3〜9 分の課題 | 経験抽出法の研究の本文(#21 の研究 2)を読む |
| K-3 | Gollwitzer & Sheeran 2006 の結果の種類ごとの d | PDF が画像のみ | OCR できる版を探す |
| K-4 | 時間ベースの展望記憶に限った実行意図の効果量 | Chen 2015 の抄録に分けた値が無い | Chen 2015 本文 |
| K-5 | Buehler 1994 の数値の原典確認 | PDF が画像のみ | 別の写しを探す |
| K-6 | 日本の通勤者の移動時間の見積り誤差 | 見つからない | 交通工学の和文誌を検索 |
| K-7 | 出発の判断に使う見積りの誤差(行動の誤差) | 申告の誤差の研究しか見つからない | Peer 2014 の本文 |
| K-8 | 日本のリマインダー・通知の利用率 | 予定管理の道具の調査に通知の設問が無い | MMD 研究所などの調査の本文 |
| K-9 | 遅刻の頻度(1 人 1 か月)・遅れの分布の日本の実測 | 自己申告の「経験の有無」しかない | 勤怠データの公開例を探す |
| K-10 | シチズン調査の遅刻時間・到着時刻の全分布 | 画像 | 画像の読み取り(親の判断) |
| K-11 | 会話が長引いて遅れる率 | 研究が見つからない | 空欄のまま宣言 |
| K-12 | Small 1982 の原典の値 | JSTOR・TRB の PDF が画像 | 別の写し |
| K-13 | MATSim の TimeAllocationMutator のずらし幅の既定値 | 利用者の手引きは「設定の節を見よ」とだけ書く | MATSim の設定の既定値の文書 |
| K-14 | ACT-R 時間モジュールの starttick の単位 | 文書に単位が無い | Taatgen 2007 本文 |
| K-15 | FEATHERS・CEMDAP の遅れの扱い | 未読 | 原典 |
| K-16 | Kahneman & Tversky 1979 の原典 | 未読 | 原典 |
| K-17 | Niedźwieńska 2020 の時間ベース・事象ベースの内訳 | 表 2 が画像 | 画像の読み取り |

## §8 取得したデータ
- `data/research_cache/r89/mlit_001995846_delay_r6.pdf`(国交省・公共データ利用規約 第 1.0 版に準拠と同省のサイトが記載)。URL・日時・md5 は同フォルダの MANIFEST.md。ライセンス台帳への行の追加は親の作業。
