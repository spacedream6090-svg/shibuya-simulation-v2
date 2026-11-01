# R-102 答申: 予定の変更の頻度ときっかけ・変えたがらない傾向・性格と時間厳守と遅刻(B1・B3・B5)

<!-- hdr:v1 -->
- **分野**: 交通工学(活動の予定づくりの調査・ADAPTS) #2 / 社会心理学(サンクコスト・現状維持・誘いを断る) #13 / 性格心理学(誠実性と時間厳守) #14 / 認知心理学(計画を続ける偏り) #12 / ABM方法論 #21 | **重要度**: P1(指示書 10-06 夜 §2 B 群の B1・B3・B5。決定記録 09-25 §8 のリサーチ 6・7。カレンダーの草案 CA5・AT1〜AT3 の宛先)
- **一次確認**: **B**(サブの自己評価。本文を自分で抽出した原典 8・取得ツール経由の本文 6・抄録または二次 19・未読 6(計 39)。空欄は §空欄)・**親検収 済(第324・2026-10-06)**: Roth・Robbert・Straus 2015 の本文を標準出力で読み「k = 100 effect sizes … ESSM = 0.496」・表 2 の CI 0.364〜0.628・利用 0.581/進行 0.443・抄録の「98 effect sizes」を逐語確認。Jackson 2010 の付録 A を PMC で確認=「Get to appointments on time」.32・「Late for a meeting (r)」−.34・「Cancel or switch plans at the last minute (r)」−.27(ほかに「Miss appointments (r)」−.44・「Back out on appointments (r)」−.36)。**未確認(△扱い)**: Ruiz & Roorda 2011 の表 1 からの再計算(14.4%・41.5%・15.0%・50.0%)・Chen 2001 の CHASE 1997 の 79/17/4%・UTRACS の 57〜62%・Orasanu 1998 の 38/51・Xiao 2021 の h と OR・遅刻の調査の割合(CareerBuilder・日本の n=103)。等級 **B**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-06・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ。PDF は標準出力か取得ツールが自動で残した写しを pymupdf で抽出した(リポの `data/` には何も取得していない。`data/research_cache/r102/` は作っていない)。コミットなし・台帳/設計書/草案/src 未編集。
> 既存答申との関係: 展望記憶・時間厳守・遅刻の日本の調査・鉄道の遅延・活動計画の先行例 = [R-89](v2-r89-prospective-memory-punctuality.md)(本書では「R-89 #番号」で参照し、値を再掲しない)/ 葛藤が熟考の引き金(Hofmann 2012) = [R-39](v2-r39-judgment-share-research.md) / 熟考の頻度・習慣 = [R-88](v2-r88-llm-humanlikeness-deliberation-vision.md) / 誠実性と時間厳守の r の空欄 K-1 = [性格の答申](v2-personality-traits-research.md) §7-1。
> 対象の草案: [時刻とカレンダーの設計ラウンドの草案](../design/v2-calendar-timing-design-round-draft.md) の CA5(予定の考え直し)・AT1〜AT3(行動の時刻)。決定記録 09-25 §8 の項目 6・7。**草案と設計書の決定項は書き換えない。**
> 世界の基準の日付(未決・候補は W13 の実日 2026-07-28 の週)に対し、本書のデータの時点は 1997〜2026 年で、北米の調査が中心です。日本の予定の変更を測った調査は見つかりませんでした(§1-6)。

## 結論(5 行)

1. **予定は多くが当日に決まり、決めた予定の 1〜2 割が実行前に変わる**: トロントの 1 週間の予定づくりの調査(CHASE・2002〜03 年・40,020 件)では、実行前に変更か削除された活動は 14.4% [再計算]、当日か思いつきで決めた活動は 41.5% [再計算] でした(Ruiz & Roorda 2011 の著者原稿・表 1)。変わりやすさは活動の種類で 12.0〜20.4% の幅があり、仕事・学校がいちばん変わりやすい(20.4%)です。シカゴの調査(UTRACS)では、1 時間前より後に決めた活動が 55 歳以上で約 37〜38%、当日中に決めた活動を合わせると 57〜62% です。
2. **変更の中身は時刻が中心で、削除は少ない**: CHASE の最初の試行(ハミルトン・1997 年・成人 61 人)では、操作の 79% が追加・17% が変更・4% が削除で、変更の 73% は開始か終了の時刻でした(Chen 2001 の学位論文が Doherty 2000 を要約)。予定と実際の差は、開始時刻(仕事で平均 17 分)より長さ(仕事で平均 70 分)の方が大きい、という観測もあります(Chen 2001 表 4.2・4.3)。予定がぶつかったときの解き方の割合(相手の活動を動かす・自分のを動かす・消す)は、本文が読めず**空欄**です(二次では「完全に重なった衝突の 6 割超で元の活動を消す」)。
3. **変えたがらない傾向の効果量**: サンクコストの効果はメタ分析で ES = 0.496(95% CI 0.364〜0.628・k = 100)、使うかの判断で 0.581、続けるかの判断で 0.443(Roth ほか 2015)。現状維持は事前登録の追試で Cohen の h = 0.38〜0.57・オッズ比 2.16〜4.83(4 場面のうち 3 場面で再現)です。計画を続ける偏りは、航空事故の戦術的な判断の誤り 51 件のうち 38 件(74.5% [再計算])でした(Orasanu ほか 1998)。目標の遮蔽と、約束の取り消しの効果量は**空欄**です。
4. **相手のいる約束は「変えにくいと本人が思い込む」側に偏る**: 誘いを断る側は、相手の怒りを実際より大きく見積もります(Givi & Kirk 2024・5 実験 2,000 人超)。予備調査では 77%(51 人)が断るのを恐れて行きたくない誘いを受けた経験を持ちます。一方、相手のいる活動が実際に変わりにくいかを直接比べた数値は見つかりません(**空欄**)。
5. **誠実性と時間厳守の r は、自己申告の行動の項目でなら取れた**: 「約束の時刻に着く」r = .32・「会議に遅れる」r = −.34・「直前に予定を取り消すか変える」r = −.27・「カレンダーで予定を立てる」r = .34(Jackson ほか 2010・N = 484〜841)。Back ほか 2006 の行動の測定の r は今回も**空欄**です。仕事の遅刻は、米国で月 1 回以上が 23〜29%・週 1 回以上が 12〜16%(CareerBuilder・2012〜2018 年の自己申告)、日本で月 1 回以上が 13%(n = 103・2019 年)です。

## §0 出典の表

等級: **◎** 原典本文で数値まで逐語確認(本文を自分で抽出) / **○** 取得ツール経由の本文(逐語の一部は取得ツールの要約を含む) / **△** 抄録・二次 / **×** 未読(空欄)

| # | 出典 | URL | 等級 | 読んだ範囲・何に使ったか |
|---|---|---|---|---|
| 1 | Ruiz T., Roorda M.J. 2011「Assessing planning decisions by activity type during the scheduling process」Transportmetrica 7(6):417-442(著者原稿) | https://doi.org/10.1080/18128602.2010.520276 / 著者原稿 https://riunet.upv.es/handle/10251/77665 | ◎ | 著者原稿 28 頁の §2(データ)・表 1・結論。B1 の変更率と当日の割合 |
| 2 | Chen Q. 2001「An Exploration of Activity Scheduling and Rescheduling Processes」博士論文 UC Davis(指導 北村隆一) | https://escholarship.org/uc/item/9kb4q6vt | ◎ | 抄録・§2 の Doherty 2000a の要約(57 頁)・第 4 章 表 4.1〜4.4。B1 の操作の内訳・予定と実際の差 |
| 3 | Mohammadian K. ほか 2013「Modeling Seniors' Activity-Travel Data」Illinois Center for Transportation FHWA-ICT-13-026(UTRACS) | https://apps.ict.illinois.edu/projects/getfile.asp?id=3101 | ◎ | §2.1・§2.3・§3.1・表 3.5。B1 の計画の時間幅 |
| 4 | Doherty S.T., Miller E.J. 2000「A computerized household activity scheduling survey」Transportation 27:75-97 | https://doi.org/10.1023/A:1005231926405 | △ | 抄録(41 世帯・成人 66 人)。本文は有料 |
| 5 | Doherty S.T., Nemeth E., Roorda M., Miller E.J. 2004「Computerized Household Activity-Scheduling Survey for Toronto」TRR 1894:140-149 | https://doi.org/10.3141/1894-15 | △ | 抄録(271 世帯) |
| 6 | Doherty S.T. 2005「How Far in Advance Are Activities Planned?」TRR 1926:41-49 | https://doi.org/10.3141/1926-06 | △ | 抄録(373 人)。割合は本文で**未読** |
| 7 | Ruiz T., Roorda M.J. 2008「Analysis of Planning Decisions during the Activity-Scheduling Process」TRR 2054:46-55 | https://doi.org/10.3141/2054-06 | △ | 抄録(OpenAlex) |
| 8 | Clark A.F., Doherty S.T. 2008「Examining the Nature and Extent of the Activity-Travel Preplanning Decision Process」TRR 2054:83-92 | https://doi.org/10.3141/2054-10 | △ | 抄録 |
| 9 | Clark A.F., Doherty S.T. 2009「Activity Rescheduling Strategies and Decision Processes in Day-to-Day Life」TRR 2134:143-152 | https://doi.org/10.3141/2134-17 | △ | 抄録(きっかけの種類) |
| 10 | Clark A.F., Doherty S.T. 2010「A multi-instrumented approach to observing the activity rescheduling decision process」Transportation 37:165-181 | https://doi.org/10.1007/s11116-009-9225-9 | △ | 抄録 |
| 11 | Auld J., Mohammadian A., Doherty S.T. 2008「Analysis of Activity Conflict Resolution Strategies」TRR 2054:10-19 | https://doi.org/10.3141/2054-02 | △ | 抄録(衝突の解き方の型) |
| 12 | Auld J., Mohammadian A., Roorda M.J. 2009「Implementation of Scheduling Conflict Resolution Model in Activity-Scheduling System」TRR 2135 | https://doi.org/10.3141/2135-12 | △ | 抄録。Roorda & Miller 2005 の割合は検索結果の要約にだけ現れた二次 |
| 13 | Roorda M.J., Miller E.J. 2005「Strategies for resolving activity scheduling conflicts: an empirical analysis」(Timmermans 編 Progress in Activity-Based Analysis pp.203-222) | なし | × | 未読。値は #12 経由の二次 |
| 14 | van Bladel K., Bellemans T., Janssens D., Wets G. 2009「Activity Travel Planning and Rescheduling Behavior」TRR 2134 | https://doi.org/10.3141/2134-16 | △ | 抄録。リポジトリ(hdl 1942/10700)は 500 エラー |
| 15 | Clark A.F. 2008 博士論文「The Human Activity-Travel Rescheduling Decision Process」Wilfrid Laurier University | https://scholars.wlu.ca/etd/885/ | × | 403(Cloudflare)。未読 |
| 16 | Roth S., Robbert T., Straus L. 2015「On the sunk-cost effect in economic decision-making: a meta-analytic review」Business Research 8:99-138 | https://www.econstor.eu/bitstream/10419/156273/1/861682238.pdf | ◎ | §6.1・表 2・時間の遅れの節 |
| 17 | Arkes H.R., Blumer C. 1985「The psychology of sunk cost」OBHDP 35:124-140 | https://doi.org/10.1016/0749-5978(85)90049-4 | △ | 二次(劇場の回数 4.11 対 3.32・3.29、スキー旅行 54%) |
| 18 | Xiao Q., Lam C.S., Piara M., Feldman G. 2021「Revisiting the status quo bias: Replication of Samuelson and Zeckhauser (1988)」Meta-Psychology 5 | https://doi.org/10.15626/MP.2020.2470 | ◎ | 抄録・検出力の節・第 1 段の結果 |
| 19 | Samuelson W., Zeckhauser R. 1988「Status quo bias in decision making」J Risk Uncertain 1:7-59 | https://doi.org/10.1007/BF00055564 | △ | 二次(Harvard の保険の乗り換え年 3%・TIAA-CREF の配分変更 2.5% 未満) |
| 20 | Orasanu J., Martin L., Davison J. 1998「Errors in Aviation Decision Making: Bad Decisions or Bad Luck?」NASA Ames | https://ntrs.nasa.gov/api/citations/20020063485/downloads/20020063485.pdf | ◎ | 抄録・本文・図 1 |
| 21 | Winter S.R. ほか 2020「An analysis of a pilot's adherence to their personal weather minimums」Safety Science 123:104576 | https://doi.org/10.1016/j.ssci.2019.104576 | △ | 二次(検索結果の抄録の写し) |
| 22 | Walmsley S., Gilbey A. 2016「Cognitive Biases in Visual Pilots' Weather-Related Decision Making」Appl Cogn Psychol 30(4):532-543 | https://doi.org/10.1002/acp.3225 | △ | 抄録(OpenAlex) |
| 23 | Shah J.Y., Friedman R., Kruglanski A.W. 2002「Forgetting all else: On the antecedents and consequences of goal shielding」JPSP 83(6):1261-1280 | https://doi.org/10.1037/0022-3514.83.6.1261 | △ | 抄録。効果量は**空欄**(academia.edu は 403) |
| 24 | Givi J., Kirk C.P. 2024「Saying no: The negative ramifications from invitation declines are less severe than we think」JPSP 126(6):1103-1115 | https://doi.org/10.1037/pspi0000443 | △ | APA の PDF は取得できず、ScienceDaily の報道で数値を確認 |
| 25 | Givi J. ほか「People Underestimate the Acceptability of Canceling Plans with Others」(未刊の原稿) | https://www.researchgate.net/publication/399098953 | × | 403。存在と要旨は二次だけ |
| 26 | Jackson J.J. ほか 2010「What do conscientious people do? Development and validation of the Behavioral Indicators of Conscientiousness (BIC)」J Res Pers 44(4):501-511 | https://pmc.ncbi.nlm.nih.gov/articles/PMC3028204/ | ◎ | 付録 A(項目と誠実性の r)・表 2・標本 |
| 27 | Harber K.D., Zimbardo P.G., Boyd J.N. 2003「Participant Self-Selection Biases as a Function of Individual Differences in Time Perspective」Basic Appl Soc Psychol 25(3):255-264(著者版) | https://doi.org/10.1207/S15324834BASP2503_08 | ◎ | 研究 1・2 の結果 |
| 28 | Werner L., Geisler J., Randler C. 2015「Morningness as a Personality Predictor of Punctuality」Curr Psychol | https://doi.org/10.1007/s12144-014-9246-1 | △ | 抄録(Springer の頁) |
| 29 | Koslowsky M. ほか 1997「Correlates of employee lateness」J Appl Psychol 82(1):79-88 | https://doi.org/10.1037/0021-9010.82.1.79 | △ | 抄録 |
| 30 | Back M.D., Schmukle S.C., Egloff B. 2006「Who is late and who is early?」J Res Pers 40:841-848 | https://doi.org/10.1016/j.jrp.2005.11.003 | × | 本文有料。r は**空欄**(R-89 #27・性格の答申 K-1 と同じ) |
| 31 | CareerBuilder(Harris Poll)2018 年 3 月 22 日の報道発表 | https://www.prnewswire.com/news-releases/this-years-most-bizarre-excuses-for-being-late-to-work-according-to-new-careerbuilder-survey-300615920.html | ○ | 本文。2012〜2017 年版は検索結果の要約だけ(△) |
| 32 | YouGov(米国)2021-10-12 の日次調査「running a few minutes late」 | https://yougov.com/en-us/daily-results/20211012-546f6-2 | ○ | 本文 |
| 33 | YouGov(米国)2025-08-29「Younger Americans have a harder time reading clocks」 | https://yougov.com/en-us/articles/52878-younger-americans-hard-time-reading-clocks | ○ | 本文 |
| 34 | ベースメントアップス「仕事に関する意識調査」(PR TIMES・2019) | https://prtimes.jp/main/html/rd/p/000000009.000045126.html | ○ | 本文 |
| 35 | セイコーグループ「セイコー時間白書 2026」 | https://www.seiko.co.jp/csr/stda/archive/2026/ (詳細 detail.html) | ○ | 調査概要・図 14〜18 |
| 36 | Rogelberg S.G. ほか 2013「Lateness to meetings」Eur J Work Organ Psychol | https://doi.org/10.1080/1359432x.2012.745988 | △ | 抄録 |
| 37 | Manser P. ほか 2022「Estimating flexibility preferences to resolve temporal scheduling conflicts in activity-based modelling」Transportation | https://pmc.ncbi.nlm.nih.gov/articles/PMC9569421/ | ○ | 序論(衝突の解き方の割合は書かれていない、を確認)・表 3 の罰の係数 |
| 38 | Mohammadian A., Doherty S.T. 2006「Modeling activity scheduling time horizon」TR Part A 40(6):475-490 | https://doi.org/10.1016/j.tra.2005.08.005 | × | 抄録も取れず。未読 |
| 39 | Auld J., Mohammadian A. 2012「Activity planning processes in the ADAPTS model」TR Part A 46(8):1386-1403 | https://doi.org/10.1016/j.tra.2012.05.017 | × | 抄録も取れず。計画の時間幅の 4 段(思いつき・当日・同じ週・前もって)は二次 |

## §1 B1 予定の変更の頻度ときっかけ

### 1-1 何をどれだけ変えるか(CHASE の 2 回の調査)

**トロント(2002〜03 年・CHASE 第 1 波・#1 ◎)**。271 世帯に 1 週間ノート PC を貸し、成人が毎日、新しい予定・変わった予定・予定どおりでなかった実行を入力した調査です。#1 §2 の逐語: 「Each day, respondents were asked to update their activity diary with any new activities that had been planned, any plans for future activities that had changed, and any changes to activities done that day that were not executed as originally planned」「After data cleaning, the total number of activity records in the Toronto Wave 1 survey was 40055, including activity additions, modifications and deletions」。

表 1(#1・活動の種類ごと。割合は原稿の値。[再計算] は私が件数から計算した値):

| 活動の種類 | 件数 | 実行前に変更・削除 | 当日か思いつきで決めた |
|---|---|---|---|
| 基本の用事(食事・睡眠など) | 15,555 | 12.0% | 33.3% |
| 仕事・学校 | 4,036 | **20.4%**(最大) | 28.4% |
| 家事 | 5,463 | 14.9% | 47.5% |
| 送り迎え | 1,675 | 17.3% | 35.9% |
| 買い物 | 1,428 | 14.4% | **68.1%** |
| サービス | 670 | 16.6% | 44.3% |
| 余暇・娯楽 | 7,876 | 原稿は 12%。件数からは **15.0%** [再計算] | 原稿は 12%。件数からは **50.0%** [再計算] |
| 交際 | 2,005 | 15.3% | 55.3% |
| その他 | 1,312 | 13.0% | 59.5% |
| **合計** | 40,020 | **14.4%** [再計算 5,762/40,020] | **41.5%** [再計算 16,624/40,020] |

- 余暇・娯楽の行は、原稿の割合(88/12・88/12)が件数(6,698/1,178・3,940/3,936)と合いません。件数の方を正として再計算しました。親の写し検査で確かめてください。
- 原稿の結論の逐語: 「All types of activities are more frequently executed as planned. Basic needs activities are least likely to be modified or deleted prior to their execution and work/school activities are most likely to be modified or deleted prior to their execution」。
- 「当日か思いつき」は、原稿が 6 区分(思いつき・当日・数日前・数週〜数年前・いつもの・不明)を 2 つにまとめた値です(#1 §2)。
- 早く決めた予定ほど変わりやすい、という向きの記述があります。逐語: 「there are strong, consistent and sensible negative correlations between preplanning and activity rescheduling. The earlier an activity is planned, the more opportunity there is to reschedule that activity」(#1 §3.2)。相関の係数そのものは多変量プロビットの誤差項の相関で、ここには写しません。
- 1 日の予定の数が多い人ほど変更・削除が多い(#1 §3.3 が Ruiz ほか 2005 を引く)。
- **フロア**: 種類ごとの変更・削除の率は 12.0〜20.4%(8.4 ポイントの幅)。人ごと・日ごとのばらつきは原稿に無く**空欄**です。

**ハミルトン(1997 年・CHASE の最初の試行・#2 ◎ が Doherty 2000a を要約)**。41 世帯・成人 61 人・1 週間。#2 57 頁の逐語: 「Overall, for 61 adults recorded in the sample, adding actions were about 79% (6,044) of the total actions; modifying actions about 17% (1,290); and deleting actions about 4% (305). Among all modifications, 73% were related to starting and ending times of activities; 8% to accompanying persons; 7% to activity type; 6% to location; 4% to travel time; and 2% to travel modes」。
- 成人 1 人 1 日あたりの操作は約 17.9 回 [再計算 7,639/61/7]。ただし入力の誤りの訂正を含みます(「About 1,595 activity modifications and deletions were made for tangible reasons and another 1,043 were made as the result of input errors」)。実質の変更・削除は 1 人 1 日あたり約 3.7 回 [再計算 1,595/61/7] です。
- 時期: 「51% of the adding actions, 21% of the modifications, and 19% of the deletions were recorded before the actual occurrence」「about 30% were scheduled impulsively ... about one half of the activities which were scheduled one or more days before the execution; 60% of the modifications were occurring at the moment; and 41% of the deletions were also occurring at the moment」。
- 追加の 79% は「予定を後から書き足した」ものを含みます。これは「人は 1 日の多くを予定なしで決めている」ことの表れで、予定の変更の多さと読むのは誤りです(推測)。

**Chen 2001 自身の調査(UC Davis・一人暮らしとひとり親・#2 ◎)**。前日に翌日の予定を書かせ、翌晩に電話で実際を聞いた調査です(表 4.1):
- 予定した活動 300 件のうち実行されなかったもの 67 件(22.3% [再計算])。実行した活動 476 件のうち前もって予定していたもの 233 件(48.9% [再計算])。抄録の逐語: 「Scheduled activities take place less than 50% of all executed activities」。
- 種類で大きく違います。仕事は予定どおり実行 81.2%・予定なしの実行 7.1%。子の世話は予定なしの実行 73.7%。
- 予定と実際の開始時刻の差(表 4.3・平均): 仕事 17 分(SD 34)・学校など 11 分(SD 10)・家事 35 分(SD 47)。長さの差(表 4.2): 仕事 70 分(SD 97)。
- 標本は小さく、人数は本文で確かめていません(**空欄**)。北米の大学町の値です。

### 1-2 どれくらい先まで決めるか(計画の時間幅)

UTRACS(シカゴ・GPS と事後の質問・14 日間・112 人・#3 ◎)。
- 65 歳未満: いつもの 35.8%・1 時間前より後に決めた(思いつき)24.6%・当日中に決めたものを合わせて「約 46%」(#3 §3.1 逐語「Around 46% of the activities conducted had a planning horizon shorter than one full day」)。65 歳以上: いつもの 25.5%・思いつき 21.4%・1 週間より前 9.1%(65 歳未満は 6.0%)。
- 表 3.5(55〜64 歳と 65〜74 歳): 1 時間未満 37.3% / 37.9%・当日 19.6% / 23.7%・前日 6.1% / 7.6%・2 日以上前 11.8% / 15.4%・いつもの 25.2% / 15.4%。
- 図 3.1 の 65 歳未満の「思いつき 24.6%」と表 3.5 の 55〜64 歳の「1 時間未満 37.3%」は、母数か対象の活動が違うと読めます(本文に説明なし)。どちらを錨にするかは親の判断です。
- 短い活動ほど思いつきで決まる(#3 §3.3.4 逐語「people appear to impulsively plan their short activities」。1.5 時間を超えると長さへの感度が小さい)。
- 調査の年は報告書から確かめていません(報告は 2013 年。**空欄**)。

CHASE トロントの割合(二次・△): 「30% 超が思いつき・約 20% が当日・約 25% がそれより前・残りはずっと前かいつもの」(Doherty 2005・#6 の値として検索結果に出た要約)。本文の図は**未読**です。#6 の抄録の逐語は「ranging from decisions made long ago that establish an initial skeleton schedule to continued preplanning in the days leading up to the event day and impulsive decisions made the day of the event」。

属性ごとの時間幅(#8・#10 抄録 △): 前もって決める属性は、活動の種類が最も多く、場所・開始時刻・同行者・終了時刻の順。「tentative decisions on each attribute are often made and then revisited at some point closer to execution」(#8)。

### 1-3 きっかけの種類

- #9(抄録 △): 予定と実行を比べて変更・削除・思いつきの追加を自動で拾い、面接で理由を聞いた調査。逐語「far more rescheduling decisions and scheduling conflicts were identified compared with previous studies」「there were many more varied causes of rescheduling decisions beyond those typically captured in existing rescheduling conflict models」「adding and deleting activities requires more talking in person, that personal need is a common cause for adding shopping activities, and that the more people involved in a decision, the longer the duration of the added activity」「sociodemographics had little effect on aspects of rescheduling decisions compared with activity variables」。
- Doherty & Miller の系の要約(二次): 変更のきっかけには、従来のモデルが扱う「衝突」より、人づきあいと個人の事情が多い。
- Chen 2001 の実験室の思考発話(#2 ◎・仮想の予定に想定外の出来事を与えた課題): 変更の約 60% が時間の不足か余りによるもの、22.5% が予定の合理化(6.1 節)。逐語「subjects rarely assess the overall situation before rescheduling operations; rarely evaluate multiple alternatives」。
- **きっかけの種類ごとの割合(実生活)は空欄**です(#9・#10 の本文と #15 の学位論文が読めない)。

### 1-4 予定がぶつかったときの解き方

- 型(#11・#12 抄録 △): 新しい活動が元の活動に重なったとき、「元を動かす・新しい方を動かす・両方を動かす・元を消す」。「動かす」はずらす・縮める・分けるを含む。新しい方を消す解き方は CHASE で観測されなかった、と二次は書きます。抄録の逐語(#11)「Many current scheduling models use an assumed priority for each activity type ... research has shown that these activity type-based priority assumptions often do not hold in actuality」。
- 割合(二次・検索結果の要約で #12 が Roorda & Miller 2005 を引く・△): 「完全に重なる衝突は全体の 23%、そのうち 60% 超で元の活動を消す」「仕事か学校の活動の 28.5% 超が別の日に動くか取りやめ」。**原典 #13 は未読**で、親の確認待ちです。
- 解き方を決めるのは活動の種類より、ぶつかった活動の属性と周りの予定でした(#11 抄録)。決定木のモデルで 72% 超を正しく当てた、という値は二次です。
- Manser ほか 2022(#37 ○)は、衝突の解き方を「早着・遅着・短縮・延長の罰」の重みで表します。フルタイムの勤労者(スイス・10,110 日)では昼食が最も動かしにくく(短縮の罰 −7.614)、仕事の総時間はほぼ自由(−0.022)でした。序論に、解き方の観測割合の数値は**ありません**。

### 1-5 使える形の錨(B1)

| 錨 | 値 | 範囲 | フロア |
|---|---|---|---|
| 実行前に変更・削除される予定の割合 | 14.4%(#1・トロント・1 週間) | 入力された全活動。北米 | 種類で 12.0〜20.4% |
| 前日までに決めていた予定が実行されない割合 | 22.3%(#2・Davis・1 日) | 小標本 | 種類で 6.9%(身の回り)〜50.0%(子の世話)[再計算・表 4.1 の件数から。表の行の % は別の母数] |
| 当日か思いつきで決めた活動 | 41.5%(#1)・46%(#3・65 歳未満)・57〜62%(#3・55〜74 歳の表 3.5) | 調査で定義が違う | 種類で 28.4〜68.1%(#1) |
| 予定していた活動が実行の中に占める割合 | 48.9%(#2)・「30〜45%」(#2 の要約) | 前日に書いた予定 | **空欄** |
| 変更のうち時刻の変更 | 73%(#2 が Doherty 2000a を要約) | 1997 年の試行 | **空欄** |
| 予定と実際の開始時刻の差(仕事) | 平均 17 分・SD 34(#2) | 小標本 | 種類で 11〜44 分 |

### 1-6 日本の調査

- パーソントリップ調査・社会生活基本調査は実行した行動だけを記録し、予定や変更を測りません(本書で読んだ範囲。推測を含む)。
- 羽藤 2010(TR Part C 18:55-67)は入力の要らない行動ロガーで、予定の変更の測定ではありません(#1 の序論が言及。本文は未読)。
- 日本で予定の変更・取り消しの頻度を測った調査は見つかりませんでした(**空欄**)。民間の「ドタキャン」の調査(マッチングアプリの利用者など)は母集団が偏るため、本書では使いません。

## §2 B3 予定を変えたがらない傾向

### 2-1 サンクコスト

- Roth ほか 2015(#16 ◎・§6.1 と表 2): 「On the basis of k = 100 effect sizes, we find that the overall effect of sunk costs on decision-making has a moderate effect size (ESSM = 0.496; p < 0.01)」。表 2: 平均 0.496・SE 0.068・95% CI 0.364〜0.628・Q = 1,337.21(異質性が大きい)。使うかの判断(utilization)0.581(k = 38)、続けるかの判断(progress)0.443(k = 62)、両者の差は有意でない(Q = 0.954)。
  - 抄録は「98 effect sizes」、本文の結果は「k = 100」です。親の写し検査で注意してください。
  - 支払いからの時間が延びると効果が小さくなる(中程度の遅れで β = −0.342、長い遅れで −0.283)。年齢が高いほど小さい(β = −0.339)。経済学に詳しくても有意には減らない。
  - ES は標準化平均差(d に相当)です。
- Arkes & Blumer 1985(#17 △・二次): 劇場の通し券を定価(15 ドル)で買った人は、割引で買った人より前半の公演に多く通った(平均 4.11 回 対 2 ドル引き 3.32・7 ドル引き 3.29)。スキー旅行の質問では 54% が高い方(楽しめない方)を選んだ。原典の本文は未読です。
- v2 への含み: 「すでに払った・移動した」ことが予定を続ける理由になる向きは錨があります。ただし金銭の場面の値で、時間や移動の手間に同じ大きさが当てはまるかは**空欄**です。

### 2-2 現状維持

- Xiao ほか 2021(#18 ◎): 米国の MTurk・2 実験(n = 311・316)で Samuelson & Zeckhauser の 4 場面を事前登録で追試。3 場面で再現、車の色の場面は再現せず。第 1 段の予算配分の場面: 現状として示した選択肢は、現状でない選択肢として示したときより選ばれやすい(χ² ≥ 9.38・最小のオッズ比 2.47・最小の Cohen の h = 0.44)。中立の提示との比較ではオッズ比 2.16〜4.83・h = 0.38〜0.57(1 選択肢は有意でない)。原典の検出力は平均 .57 で、原典は検出力が足りなかった、と著者は書きます。
- 原典 #19 の実地の値(二次・△): Harvard の職員の保険の乗り換えは年 3%(Neipp & Zeckhauser 1985 の値)、TIAA-CREF の加入 12 年以上の人で配分を変えたのは年 2.5% 未満。
- 範囲の注意: 仮想の選択の場面の効果で、日々の予定の変更に当てはめる研究は見つかりません(**空欄**)。

### 2-3 計画を続ける偏り(plan continuation)

- Orasanu ほか 1998(#20 ◎): NTSB(1994)が乗員の行動が原因に関わったと判断した 37 件の事故のうち 25 件に戦術的な判断の誤りがあり、その誤り 51 件を分類。逐語「when we sorted the decision errors into those that supported plan-continuation from all others, we found that 38 (or almost 75%) of the errors fell into this category」。最多は着陸のやり直しをしなかった誤り(19/51)。計画を続けた誤りの 3 分の 2 は「すべきことをしなかった」型でした。
  - 二次の文献には「37 件の事故の 75%」と書くものがあります。原典は「51 件の判断の誤りの 74.5% [再計算 38/51]」です。
- Winter ほか 2020(#21 △・二次): 計器飛行の資格を持つ 112 人のシミュレーターで、着陸してはならない天候にしたところ 96.4% が自分の決めた最低の高度より下まで降り、81.5% が法の最低の高度より下まで降りた。乗客の約束などの外の圧力の操作は効かなかった(全て p > .05)。
- Walmsley & Gilbey 2016(#22 △): 出発前の天気の情報が飛行中の判断を引きずる(係留)、結果がよければ同じ判断を高く評価する(結果の偏り)。
- **人に当てはめる範囲**: 航空の研究は、安全上の手順と高い負荷のもとでの専門家の判断です。日常の予定(買い物・待ち合わせ)で「続ける偏り」の大きさを測った研究は見つかりません(**空欄**)。医療の研究も今回は読めていません(**空欄**)。v2 で使えるのは「目標に近いほど計画を変えにくい」「誤りの多くは何もしないこと」という向きまでです(推測)。

### 2-4 目標の遮蔽(goal shielding)

- Shah ほか 2002(#23 △・抄録): 6 研究。目標に打ち込むほど、他の目標が思い浮かびにくくなる。強める要因は目標への関与・不安・抑うつ・結論を急ぐ傾向・粘り強さ。同じ上位の目的に仕える代わりの目標ほど強く抑えられ、目標の達成を助ける目標は抑えられにくい。遮蔽は目標の達成に役立った。
- **効果量は空欄**です(本文は有料。著者のサイトにも PDF が見当たらない)。
- R-39 の葛藤の研究(Hofmann ほか 2012)と合わせると、「今の予定に打ち込んでいる間は代わりの誘いが目に入りにくい」「ぶつかると熟考が起きる」という 2 つの向きになります(推測)。

### 2-5 相手のいる約束と自分だけの予定

- 断る側の見積りの偏り(#24 △・報道で確認): Givi & Kirk は 5 実験・2,000 人超で、誘いを断る人は、誘った人の怒りや失望を実際より大きく見積もることを示しました。予備調査では「77% of our 51 respondents had accepted an invitation to an event that they didn't want to attend」(二次の引用)。夫婦や恋人の実験(160 人)でも、付き合いの長さに関係なく同じ偏りが出ました。効果量(d など)は本文が読めず**空欄**です。
- 取り消す側の見積りの偏り(#25 ×・二次): 予定を取り消す人は、相手が取り消しを受け入れる度合いを過小評価する、という未刊の原稿があります。数値は**空欄**です。
- 予定づくりの調査で同行者を見たもの: CHASE の最初の試行で、変更の 8% が同行者の変更でした(§1-1)。van Bladel ほか 2009(#14 抄録 △)は「個人ごとの計画と変更の好み」が強く効くと書き、二次の要約は「世帯の外の人がいることが変更に効く」とします。Ruiz & Roorda 2011(#1)は「Commitments to others (as represented in the "with whom" variable) surely influence the planning horizon and the difficulty of rescheduling」と仮説を書きますが、表 1 は「誰と」を一部の活動にしか持たず、相手のいる予定と自分だけの予定の変更率を並べた数値は**ありません**。
- 性格の側(#26 ◎): 「直前に予定を取り消すか変える」は誠実性と r = −.27、「約束を取りやめる」は r = −.36(§3-1)。
- **相手のいる約束が自分だけの予定より何倍変わりにくいか、の数値は空欄**です。手元の材料で言えるのは「本人は相手の反応を過大に見積もる(だから変えにくいと感じる)」と「実際の相手は思ったより寛容」の 2 つです。

### 2-6 使える形の錨(B3)

| 錨 | 値 | 範囲 | 注意 |
|---|---|---|---|
| サンクコストの効果量 | ES 0.496(CI 0.364〜0.628) | 金銭の場面中心・k = 100 | 異質性が大きい(Q = 1,337) |
| 現状維持の効果量 | h = 0.38〜0.57・OR 2.16〜4.83 | 仮想の選択・米国 | 4 場面中 1 場面は再現せず |
| 計画を続ける誤りの割合 | 38/51(74.5%) | 航空事故・乗員の判断 | 日常への当てはめは推測 |
| 断ると怒らせると思い込む偏り | 向きのみ(77% は n = 51 の予備調査) | 米国・実験と夫婦 | 効果量は空欄 |
| 直前の取り消しと誠実性 | r = −.27 | 自己申告・学生中心 | 行動の測定ではない |

## §3 B5 性格と時間厳守・人の遅刻

### 3-1 誠実性と時間厳守

- **Jackson ほか 2010(#26 ◎)**。誠実性の行動の項目を自己申告で集め、各項目と誠実性の r を付録 A に載せています(研究 2・N = 484〜841・女性 63%・平均 20.2 歳)。付録の注の逐語「r = item correlation with conscientiousness from Study 2」。

| 項目(原文) | 因子 | r |
|---|---|---|
| Get to appointments on time | 時間厳守 | .32 |
| Miss appointments (r) | 時間厳守 | −.44 |
| Late for a meeting (r) | 時間厳守 | −.34 |
| Get to work on time | 時間厳守 | .31 |
| Leave for work at the exact time I had planned | 時間厳守 | .24 |
| Show up for work more than 5 min early | 時間厳守 | .21 |
| Allow extra time for getting lost when going to new places | 時間厳守 | .28 |
| Forget about an appointment (r) | 時間厳守 | −.39 |
| Miss the bus (r) | 時間厳守 | −.32 |
| Back out on appointments (r) | 他 | −.36 |
| Cancel or switch plans at the last minute (r) | 衝動の抑え | −.27 |
| Use a calendar or date book to plan my activities | 整理 | .34 |
| Make lists | 整理 | .35 |

  - 因子と誠実性の相関(表 2): 時間厳守の因子 .52(AB5C)・.62(CAC)、整理の因子 .56・.45。
  - **これは自己申告どうしの相関**です。行動を測った値(Back ほか 2006)より大きく出やすい、と読むのが安全です(推測)。
- Back ほか 2006(#30 ×): 誠実性は到着時刻・早さ・遅さの全てに関係(二次)。**r は空欄**(R-89 K-1・性格の答申 K-1 のまま)。Ellis & Jenkins 2015 の「Back の相関より自分たちの効果量がはるかに大きい」という記述(R-89 #2)から、行動の r は小さいと読めます(推測)。
- Werner ほか 2015(#28 △・抄録): 大学の朝 8:15 の授業への到着を観察(267 人)。自己申告の時間厳守は朝型と誠実性に関係したが、実際の到着時刻に効いたのは朝型の傾向だけで、説明できた分散は 1.6%。交通手段と曜日が効いた(徒歩と自転車は遅い)。**行動で測ると性格の効き目は小さい**、の傍証です。
- Rogelberg ほか 2013(#36 △・抄録): 会議への遅刻は頻度が高く、誠実性・年齢・仕事の満足と関係。数値は**空欄**。
- Koslowsky ほか 1997(#29 △・抄録): 遅刻と欠勤の補正後の相関 .40、遅刻と離職 .27(30 標本・118 相関)。性格は扱っていない。

### 3-2 計画の立て方の個人差(時間の向き)

- Harber ほか 2003(#27 ◎): 未来志向の学生は、実験への参加を現在志向の学生より早く始め(7.25 日早い・F(1, 79) = 3.72・p < .06)、中間の実験を 7.78 日早く終えた(F(1, 79) = 4.26・p < .05)。研究 2(複数回の日記の提出): 現在志向の学生は締切に平均 3.5 回遅れ(SD 2.50)、未来志向は 0.89 回(F(1, 35) = 12.92・p < .001・η = .28)。
  - 人ごとの遅れの回数に大きな差がある例として使えます。ただし学生の締切で、待ち合わせではありません。
- 予定を立てる道具の個人差: カレンダーの使用と誠実性 r = .34(#26)。日本の予定管理の手段は R-89 #15(デジタルで管理 44.9%)。

### 3-3 仕事の遅刻の頻度

| 調査 | 対象・時点 | 月 1 回以上 | 週 1 回以上 | 等級 |
|---|---|---|---|---|
| CareerBuilder 2018 発表(#31) | 米国の常勤の被雇用者 809 人・2017-11-28〜12-20・Harris Poll のネット調査 | 25%(18〜34 歳 38%・35〜44 歳 36%・45 歳以上 14%) | 12% | ○ |
| CareerBuilder 2012〜2017 発表 | 同上の各年 | 23〜29% | 13〜16% | △(検索結果の要約) |
| YouGov(米国・年不明) | 成人 | (「遅刻しない」48%) | 20% | △(検索結果の要約) |
| ベースメントアップス 2019(#34) | 社会人 103 人・2019-07-01〜08・ネット | 13%(1 回 6%・2 回以上 7%) | **空欄** | ○ |

- 遅刻の理由(#31・複数回答): 交通 51%・寝坊 31%・悪天候 28%・疲れて起きられない 23%・忘れ物 13%。
- **フロア**: 米国の月 1 回以上は年ごとに 23〜29%(6 ポイントの幅)。年齢で 14〜38%。日本の値は n = 103 で、比べるには小さすぎます。
- 日本の新入社員の遅刻の経験(22.0%)と始業前の到着は R-89 #12・#14 にあります(再掲しません)。
- 勤怠の記録から測った遅刻の頻度(自己申告でない値)は**空欄**です(R-89 K-9 のまま)。

### 3-4 私的な待ち合わせの遅刻

- YouGov 2021(#32 ○・米国成人 5,051 人・2021-10-12): 「少し遅れる」と連絡が来たとき何分遅れると思うか。時間どおり 6%・5 分未満 9%・**5〜10 分 51%**・10〜30 分 23%・30 分超 3%・わからない 9%。
- YouGov 2025(#33 ○・米国 1,128 人): 自分は他人より時間どおりに着く 68%・同じ 23%・他人より遅い 6%。パーティーには早く着く 32%・遅れて着く 31%。演奏会・面接・スポーツ観戦は過半が早く着く。
- セイコー時間白書 2026(#35 ○・全国 15〜69 歳 1,200 人・2026-04-06〜09・マクロミル): 「少し早め」は何分前か: 10 分前 52.6%・5 分前 10.6%・20 分以上前 8.4%(残りの内訳は頁に無い)。他人と時間の感覚が合わない経験 88.7%(よくある 13.1%・時々 42.8%・たまに 32.9%)。遅刻そのものの設問は**ありません**。
- 日本の待ち合わせの遅刻の経験・許す遅れは R-89 #12・#13・#28(シチズン)。**注意**: 検索結果の要約が、シチズンの 2020 年の調査(許す遅れ「10 分」最多)を「セイコー時間白書 2020」と取り違えていました。@DIME の記事(R-89 #28)の出典はシチズン時計です(本書で確認)。R-89 の帰属は正しいままです。
- **私的な待ち合わせの遅刻の頻度と、遅れの分の分布(実測)は空欄**です。

### 3-5 いつも遅れる人の割合(人ごとの差の形)

- 米国の自己申告: 他人より遅いと答える人 6%(#33)、仕事で週 1 回以上遅れる人 12〜16%(#31)。
- 「人口の約 17% が慢性的に遅れる」という値は、一般向けの記事が学術の研究として引く二次の値で、原典を確かめていません(**空欄**。書籍が出どころらしい=推測)。
- 人ごとの差の形(分布)を示す値: Harber ほか 2003 の締切の遅れ回数(現在志向 3.5 回・SD 2.50 対 未来志向 0.89 回)、R-89 #2 の到着時刻の SD 5.95 分。どれも小さい学生の標本です。遅刻の回数が少数の人に集中するか(偏った分布か)を示す実データは**空欄**です。
- Koslowsky ほか 1997 は遅刻を「増えていく慢性・安定した周期・避けられない」の 3 型に分けます(二次)。

### 3-6 通勤の到着時刻の分布

- Small 1982 の遅着の罰と、早着・遅着の費用比は R-89 #32・#33・§4 にあります。本書では新しい値を足していません。通勤の到着時刻の分布の原典の値は**空欄**です(R-89 K-12 のまま)。

## §空欄

| # | 空欄 | 理由 | 次の手 |
|---|---|---|---|
| R102-1 | 予定の変更のきっかけの種類ごとの割合(実生活) | #9・#10 が抄録だけ。#15 の学位論文は 403 | ブラウザで #15 を開いて読む(Cloudflare の確認が要る。ユーザーの手作業) |
| R102-2 | 衝突の解き方の割合(元を動かす・新しい方・両方・削除) | #11・#12・#13 の本文が読めない。二次の値(23%・60% 超・28.5%)は未確認 | 図書館か著者の原稿。Auld の博士論文(UIC 2011・UMI 3484958)は ProQuest で有料 |
| R102-3 | CHASE トロントの計画の時間幅の割合(Doherty 2005 の図) | #6 は有料 | 同上 |
| R102-4 | 人ごと・日ごとの変更回数のばらつき | どの原典にも見当たらない | 公開の個票(CHASE は非公開)。親の判断で「空欄のまま宣言」 |
| R102-5 | 相手のいる予定と自分だけの予定の変更率の比 | 表として出した研究が見つからない | van Bladel 2009 の本文(リポジトリが 500) |
| R102-6 | 日本の予定の変更・取り消しの頻度 | 見つからない | 和文誌(土木計画学研究・論文集)の検索 |
| R102-7 | 目標の遮蔽の効果量 | #23 は有料 | 著者版を探す |
| R102-8 | 誘いを断る・取り消す研究の効果量 | #24 の APA の PDF が取れない。#25 は 403 | ブラウザで #24 を読む |
| R102-9 | 日常の予定での計画を続ける偏りの大きさ・医療の研究 | 航空以外は読めていない | 次の依頼で医療(手術の続行など)を探す |
| R102-10 | Back ほか 2006 の r | 有料(R-89 K-1・性格の答申 K-1) | 図書館。代わりに Jackson 2010 の自己申告の r を使うかは親の判断 |
| R102-11 | 私的な待ち合わせの遅刻の頻度と遅れの分の分布(実測) | 自己申告の「経験の有無」と「許す遅れ」しかない | 空欄のまま宣言 |
| R102-12 | 遅刻が少数の人に集中するかの分布 | 見つからない | 勤怠データの公開例 |
| R102-13 | 「慢性的に遅れる人 17%」の原典 | 書籍らしく、学術の原典を確かめていない | 使わない |
| R102-14 | UTRACS の調査年・Chen 2001 の人数 | 報告書・論文から確かめていない | 親が #2・#3 の該当頁を確認 |
| R102-15 | Clark & Doherty 2010 の「1 人 1 日 16.4 回の変更」という値 | 検索結果の要約にだけ現れ、出典の頁が確かめられない | 使わない(写し検査の注意) |

**ユーザーの判断や手作業が要るもの**: R102-1(ブラウザで学位論文を読む)・R102-8(ブラウザで APA の PDF を読む)の 2 つ。どちらも読むだけで、取得はしません。データの予算の外(有料)のものは、存在と条件だけを記録しました(R102-2・3・7・10)。

## §v2 への当てはめ(案・未決。親が判断する材料)

草案の CA5 の親推奨は「判断モデルが入るまで、モックの分布に『考え直す・そのまま』を足し、既定は『そのまま』に寄せる」です。以下はその既定に錨を当てるための材料で、決定ではありません。

1. **「そのまま」に寄せる強さの錨**: 実行前に変わる予定は全体の約 14%(#1)、前日に決めた予定が実行されないのは約 22%(#2)。「考え直す」の既定の確率を置くなら、この桁(1〜2 割)が目安になります。ただし #1 は「1 週間に入力された全活動」に対する率で、v2 の 1 回の判断ごとの率ではありません。判断の回数に割り直す材料(1 日に何回考え直す機会があるか)は**空欄**で、置くなら expedient と宣言する必要があります(推測)。
2. **活動の種類で変わりやすさを変える**: 仕事・学校が最も変わりやすく(20.4%)、基本の用事と余暇が最も変わりにくい(12.0%・15.0%)、という向きは錨があります。ただし幅は 8 ポイントで、種類より「本人の好み」が強く効くという報告(#14)もあります。種類で差を付けるかは親の判断です。
3. **当日に決まる予定の多さ**: 予定にない活動が実行の約半分(#2)、当日か思いつきの決定が 4〜6 割(#1・#3)。「予定を前もって全部作る」より「骨組み(仕事・学校・送り迎え)だけ前もって作り、残りは当日に足す」形が観測に合います(推測)。CA1 の「勤務と授業の約束を実データから作る」と同じ向きです。
4. **変更の中身**: 変更の 7 割強が時刻で(#2 経由の Doherty 2000a)、開始より長さがずれやすい(#2)。v2 で「考え直す」の中身を選ぶなら、時刻をずらす・縮めるが主、取りやめは少数、という分け方に錨があります。
5. **変えたがらない傾向の入れ方**: サンクコストと現状維持の効果量は中程度(0.4〜0.6)です。ただし金銭と仮想の選択の値で、日常の予定に直接写す研究はありません。判断モデルに渡す入力として「すでに移動した」「相手がいる」を事実のまま渡す(草案 CA5 の (a))ことは、これらの研究と矛盾しません(推測)。数値の重みとして入れる錨はありません。
6. **相手のいる約束**: 本人は取り消しの悪影響を過大に見積もる(#24)。一方、実データで相手のいる予定が変わりにくいかは空欄です。v2 の LLM が「誘いを断らない」偏り(B7・R-104 の担当)と重なるので、計器を読むときに注意が要ります(推測)。
7. **誠実性の腕(性格の答申の P8・腕 4)**: 行動の r は空欄のままですが、自己申告の項目の r(.21〜.44)と、行動で測ると小さい(説明できた分散 1.6%・#28)という傍証は揃いました。「誠実性が高いほど遅れにくい・直前に変えにくい」の向きだけを持たせ、強さは expedient と宣言する、が材料から言える範囲です(推測)。
8. **遅刻の照合(CA8・AT3)**: 仕事の遅刻は米国の自己申告で月 1 回以上 23〜29%・週 1 回以上 12〜16%(#31)。日本は n = 103 で月 1 回以上 13%(#34)。「少し遅れる」の想定は 5〜10 分が過半(#32)。これらは自己申告で、v2 の計器と比べるなら診断の欄に留めるのが安全です(推測)。較正にも holdout にも使っていない外部の値です。
