# R-45 答申: 行動の粒度・持続・効果の解決の先行研究(二層仮説の検証材料)

<!-- hdr:v1 -->
- **分野**: 自然言語処理・機械学習 #27 / 交通工学(活動ベース需要予測) #2 / ゲームエンジン工学・CG #30 / 計算社会科学 #25 / オペレーションズリサーチ #20 / ソフトウェア工学 #29 | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **B** = サブ実読(原典 21・抄録のみ 3・空欄 4)・**親検収 済(第272・下の欄)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: ユーザーの問い(09-26「いまの思考の頻度では行動の粒度が小さすぎる・なぜエンジンで行動を規定するのか・待つなどは不要では」)と、親の二層仮説(世界に触れる行為だけ契約で規定/待つ・見る・散歩は**活動=自由文+持続**)を設計ラウンドに出す前に、先行が **粒度・持続・意図の保持・決定の頻度・効果の解決者** をどう扱ったかを一次で並べる。設計の決定はしない(§9 は選択肢と根拠だけ)。
> 規律: 子サブ未起動・Web は読むだけ・コミットなし・台帳未編集・本書の新規作成のみ。

---

> **親検収(2026-09-27・第272・Fable 5.1)**: 結論を変える逐語 11 か所を原典(arXiv HTML / 著者公開 PDF を標準出力に流して文字列照合・保存なし)で確認した。**全一致・訂正なし**。
> - ✓ Lyfe Agents(arXiv:2310.02172 v1 HTML): 「the termination condition for an option is checked by fast, non-LLM methods, such as time-based triggers or, for agents in conversations, repetition detection」/ 抄録「10-100 times lower than existing alternatives」/ 序論「cost about 30-100 times less than that of Park et al. (2023)」(§11-1 の不一致は実在)/ 「0.5 US dollar per agent per human hour」/ 「70.348 ± 13.189 seconds (n=9) for Lyfe Agents and 23.802 ± 1.463 seconds (n=4) for ablated agents」。
> - ✓ AgentSociety(arXiv:2502.08691 HTML): 「Other simple behaviors such as sleeping are directly handled by LLMs.」/「By offloading tasks such as numerical computations, where LLMs cannot guarantee absolute accuracy」。
> - ✓ Wang ら 2024(arXiv:2406.06485 HTML): 「model accuracy does not exceed 59.9% for transitions in which a non-trivial change in the world state occurs」。
> - ✓ Project Sid(arXiv:2411.00114 v1 HTML): 「Bob might then attempt to mine using an imaginary pickaxe. This kind of miscommunication … leads to dysfunctional behavior」。
> - ✓ Concordia(arXiv:2312.03664 v2 PDF): 「(concurrent_action flag), but it often leads to in-consistencies, although greatly speeds up the sim-ulation. Use at your own risk.」(行またぎのハイフン)/ 図「Update to grounded variables」。
> - ✓ Sutton, Precup & Singh 1999(著者公開 PDF): 「Sometimes it is useful for options to “timeout”, to terminate after some period of time has elapsed even if they have failed to reach any particular state. This is not possible with Markov options」/「a set of options defined over an MDP constitutes a semi-Markov decision process (SMDP)」。
> - ✓ Erol, Hendler & Nau 1994(AAAI PDF): 「the compound task of making a round trip to New York cannot easily be expressed as a single goal task, because the initial and final states would be the same.」
> - ✓ Graham 2013(Game AI Pro 第 9 章 PDF): 「On The Sims Medieval, a Sim would only attempt to make a decision when their interaction queue was empty. Once they chose an action, they would commit to performing that action. Once the Sim completed (or failed to complete) their action, they wou[ld …]」。
> - ✓ Shao & Terzopoulos 2007(著者公開 PDF): 「preconditions (e.g., target must be within 0.5 m), and expiration time (e.g., for 3 s, until finished)」(§11-7 のとおり例示)。
> - △ 親未確認のまま: Rao & Georgeff 1995 の drop-impossible・Isla 2005(Halo 2)・MATSim ユーザーガイドの頁・Forbus & Wright 2001・Buss 2010(いずれもサブ実読・結論の向きを変えないため次回)。§9 の「待つの一部は世界に触れる」はサブの読み [推測] のまま採用(v2 では D-113 ③ の待ち行列が実装上の裏づけ)。

## §0 等級と調べ方

- arXiv は HTML(arxiv.org/html または ar5iv)を読み、**本書に載せた英語の逐語は生 HTML/PDF 本文への文字列一致で再確認した**(要約モデル経由の文面は使っていない。一致しなかった 4 件は文脈を出して原文の語形に直した)。PDF は curl → 標準出力 → pymupdf で抽出(ローカル保存なし)。Concordia の PDF だけは WebFetch が自動保存した一時ファイルを抽出した。
- **R-41 で親確認済みの Kinny & Georgeff 1991・Schut & Wooldridge 2001・PIANO §2 は再確認せず参照のみ**([r41](v2-r41-cognitive-architecture-precedents.md) §2・§4-2)。

| # | 出典 | 種別 | 取れた範囲 |
|---|---|---|---|
| 1 | Sutton, Precup & Singh 1999, AIJ 112:181–211(doi:10.1016/S0004-3702(99)00052-1) | 原典 | 著者公開 PDF 全文(§2・§3 Thm 1・§4 Thm 2) |
| 2 | Erol, Hendler & Nau 1994, AAAI-94 pp.1123–1128 | 原典 | 著者公開 PDF(定義の節) |
| 3 | Rao & Georgeff 1995, ICMAS-95 "BDI Agents: From Theory to Practice" | 原典 | AAAI 公開 PDF(commitment・インタプリタ) |
| 4 | Bratman, Israel & Pollack 1988, Computational Intelligence 4 | 抄録のみ | SRI の公開ページの抄録 |
| 5 | Kaiya ら 2023 Lyfe Agents(arXiv:2310.02172 v1) | 原典 | HTML 本文+付録 A・C・E・F |
| 6 | Altera.AL 2024 Project Sid(arXiv:2411.00114 v1) | 原典 | HTML §1.3・§2・§3.1・§5.1・§8.2・付録 C |
| 7 | Park ら 2023 Generative Agents(arXiv:2304.03442)+公式 README | 原典 | ar5iv HTML 本文(付録は未読)・README の step 長 |
| 8 | Wang ら 2023 Humanoid Agents(arXiv:2310.05418) | 原典 | ar5iv HTML §3・§4・付録 A.3 |
| 9 | Vezhnevets ら 2023 Concordia(arXiv:2312.03664 v2) | 原典 | PDF 本文+付録 A(A.3.1・A.5 含む) |
| 10 | Piao ら 2025 AgentSociety(arXiv:2502.08691) | 原典 | HTML §1〜§5(一部切断) |
| 11 | Yang ら 2024 OASIS(arXiv:2411.11581) | 原典 | HTML §2・§3.5・付録 D.1 |
| 12 | Zhou ら 2023 Sotopia(arXiv:2310.11667) | 原典 | ar5iv HTML §2.2・付録 C.1 |
| 13 | Affordable Generative Agents(AGA, arXiv:2402.02053・TMLR) | 原典 | HTML の Lifestyle Policy 節・表 1・図 3 の本文 |
| 14 | AgentSims(arXiv:2308.04026) | 抄録のみ | arXiv 抄録 |
| 15 | MATSim(Horni, Nagel & Axhausen 編 2016, doi:10.5334/baw)公式ユーザーガイド=同書の抜粋更新版(2026/08/25 編集) | 原典 | 1 章・2 章・4.6 節・14 章(採点) |
| 16 | ActivitySim 公式ドキュメント v1.0.4「Models」 | 原典 | Tour/Trip Scheduling の節 |
| 17 | Bowman & Ben-Akiva 2001, TR-A 35(1):1–28(doi:10.1016/S0965-8564(99)00043-9) | 抄録のみ | IDEAS/RePEc の抄録 |
| 18 | Forbus & Wright 2001 "Some notes on programming objects in The Sims"(5/31/01 版) | 原典 | Northwestern QRG 公開 PDF 全 16 頁 |
| 19 | Graham 2013 "An Introduction to Utility Theory"(Game AI Pro 第 9 章) | 原典 | gameaipro.com 公開 PDF 全文 |
| 20 | Isla 2005 "Handling Complexity in the Halo 2 AI"(GDC 2005 講演録) | 原典 | gamedeveloper.com 本文 |
| 21 | Shao & Terzopoulos 2007 "Autonomous pedestrians", Graphical Models 69:246–274(doi:10.1016/j.gmod.2007.09.001) | 原典 | 著者公開 PDF 全 29 頁 |
| 22 | Fikes & Nilsson 1971 STRIPS, AIJ 2:189–208(doi:10.1016/0004-3702(71)90010-5) | 原典 | 著者公開 PDF(AIJ 版)+IJCAI-71 版 |
| 23 | Wang ら 2024 "Can Language Models Serve as Text-Based World Simulators?"(ACL 2024, arXiv:2406.06485) | 原典 | 抄録+HTML 本文(§1・§2・表 2) |
| 24 | Buss & Al Rowaei 2010, WSC pp.1468–1477 | 原典 | informs-sim.org 公開 PDF(抄録・結論) |
| — | Bratman 1987(書籍)/ S3・RecAgent / Wright の GDC 講演 / Dill 2011(dual utility 原典) | 空欄 | §10 |

(原典 21 = #1〜3・5〜13・15・16・18〜24。抄録のみ 3 = #4・14・17。空欄 4 = 最終行)

## §1 Q1 時間的に伸びた行動の形式

**1-1 Sutton, Precup & Singh 1999(options / semi-MDP)**
- §2 定義: 「Options consist of three components: a policy π : S × A → [0,1], a termination condition β : S+ → [0,1], and an initiation set I ⊆ S.」「If the option is taken, then actions are selected according to π until the option terminates stochastically according to β.」例「open-the-door might consist of a policy for reaching, grasping and turning the door knob, a termination condition for recognizing that the door has been opened, and an initiation set restricting consideration of open-the-door to states in which a door is present.」
- §2 時限: 「Sometimes it is useful for options to "timeout", to terminate after some period of time has elapsed even if they have failed to reach any particular state. This is not possible with Markov options」→ 履歴に依存する **semi-Markov option** を導入。
- 抄録: 「Examples of options include picking up an object, going to lunch, and traveling to a distant city, as well as primitive actions such as muscle twitches and joint torques.」/ Thm 1「the decision process that selects only among those options, executing each to termination, is an SMDP.」
- §4 割込み: 「treating options as indivisible units, as SMDP methods do, is limiting in an unnecessary way.」Thm 2(Interruption)は Q(h,o) < V(s) のとき β′(h)=1 にしてよく、その方策は元より悪くならない(V^µ′ ⩾ V^µ)。
- **v2 との対応**: 親の「活動+持続(到着・相手が来る・N 分・次の予定)」は (I, π, β) と同形で、「N 分」は semi-Markov option の timeout そのもの=**一致**。primitive action も option の特殊例=一つの型で両層を書けるのが形式側の答え。ただし先行は「終了まで走らせる」より「価値が下がれば割り込む」ほうが良いと定理で示す=**持続は上限であって拘束ではない**(部分一致の注意)。

**1-2 Erol, Hendler & Nau 1994(HTN)**
- 「Primitive tasks are the tasks we can directly achieve by executing the corresponding action, such as moving a block, or turning a switch on.」「Compound tasks denote desired changes that involve several goal tasks and primitive tasks」
- 「A set of "operators" Op telling the effects of each primitive task (action).」「A set of "methods" Me telling how to perform various non-primitive tasks.」
- 「the compound task of making a round trip to New York cannot easily be expressed as a single goal task, because the initial and final states would be the same.」
- 時間・持続の記述は本論文に無い(記述の不在)。
- **v2 との対応**: 効果(operator)は末端の primitive にだけ付き、上位は分解の手続き=「効果を持つのは世界に触れる末端の行為だけ」と同形=**一致**。「散歩」型(始点=終点)の活動は**状態変化の目標では書けない**と 1994 年に明記=活動を効果で定義しない根拠の一つ=**一致**。

**1-3 BDI の intention(Rao & Georgeff 1995・Bratman ら 1988)**
- Rao & Georgeff: 「reconsidering the choice of action at each step is potentially too expensive and the chosen action possibly invalid, whereas unconditional commitment to the chosen course of action can result in the system failing to achieve its objectives.」
- 「A commitment usually has two parts to it: one is the condition that the agent is committed to maintain, called the commitment condition, and the second is the condition under which the agent gives up the commitment, called the termination condition.」型は blindly-committed / single-minded / open-minded の 3 つ。
- インタプリタ: `options := option-generator(event-queue); … execute(); get-new-external-events(); drop-successful-attitudes(); drop-impossible-attitudes();`/「the outputs of the agent--actions--are also assumed to be atomic.」
- Bratman ら 1988 抄録(抄録のみ): 「a major role of the agent's plans is to constrain the amount of further practical reasoning she must perform.」
- Kinny & Georgeff 1991・Schut & Wooldridge 2001 は R-41 §2 で親逐語確認済み(「何でも再考」は盲目的コミットより悪い・計画費が上がるほどコミットを強めるのが最適)=参照のみ。
- **v2 との対応**: 行為は atomic・意図は持続し、終了は「達成(drop-successful)」と「不可能(drop-impossible)」の 2 系統=二層と**一致**。親の終了条件 4 種(到着・相手が来る・N 分・次の予定)には**「不可能になった/失敗」が無い**=先行は必ず持つ(**部分一致・追加候補**)。

**1-4 Lyfe Agents(arXiv:2310.02172)— option–action の LLM 版**
- §2.1: 認知制御器が「Using an LLM call, it then outputs an option along with a subgoal」→「actions are chosen within that option over subsequent steps until a termination condition is met」→ 終了は「checked by fast, non-LLM methods, such as time-based triggers」(会話では意味的な新しさが落ちたら抜ける反復検出)。
- 付録 A.1: 「obviates the need for making a new LLM call at each time step to decide the next action.」付録 C: 「Agents can pursue two groups of actions within the simulated environment: move and talk.」
- 数値: §4.3「0.5 US dollar per agent per human hour」。**抄録「10-100 times lower than existing alternatives」と序論「30-100 times less than that of Park et al.」が論文内で不一致**。比較相手の「25 US dollar per agent per human hour」は付録 F の**推定**(Park の総額「thousands of dollars」を 2,000 USD と置き、「Assuming that agents make a new plan every one minute in-real-life」+10 倍速を仮定)で実測ではない。
- ablation(付録 E.1 は制御器を毎 step 呼ぶ): ablation は会話を「three times faster」に抜ける(付録 A.1: 連続会話 70.348±13.189 s(n=9)vs 23.802±1.463 s(n=4))。要約更新は「only triggered by new observations」(Marta は「updated a total of 35 times」)。
- 「idle / wait」の語は本文に無い(記述の不在)。
- **v2 との対応**: **LLM は活動(option)と下位目標を選び、持続の終了は非 LLM が判定**=親仮説の「持続はエンジンが監視」と**一致**。外部行為は move/talk の 2 群だけ=世界に触れる語は極小・中身は LLM。

**1-5 Project Sid(arXiv:2411.00114)— 粒度の追加分のみ(PIANO 構成は R-41 §4-2)**
- §8.2: 「These intentions are then translated to low-level actions executable in Minecraft.」§5.1: 目標を「every 5-10 seconds (such as mine oak planks for shelter)」生成。付録 C のプロンプト: 「Keep the same subgoal unless you don't have one or it's already been accomplished.」§3.1: 「agents often hallucinate and get stuck in action loops.」
- 行動が自由文かコード化スキルか・1 行動の持続・制御器の決定頻度は**本文に無い**。
- **v2 との対応**: 目標は自由文・実行は Minecraft のエンジン=二層と**一致**。意図の保持をプロンプト上の規範で実現した例(エンジン側の持続ではない)。

## §2 Q2 LLM 社会シミュの行動空間と粒度

**2-1 Generative Agents(Park ら 2023)**
- 行動=自由文: §3.1.1「the agents output a natural language statement describing their current action」(例 "Isabella Rodriguez is writing in her journal")。
- 持続: §4.3「A plan includes a location, a starting time, and a duration.」例は「for 180 minutes from 9am, February 12th, 2023, at Oak Hill College Dorm: …」。日計画→「hour-long chunks」→「5–15 minute chunks」と再帰分解。**持続は LLM が計画時に書く**。
- 反応: §4.3.1「at each time step, they perceive the world around them」→ LLM に「continue with their existing plan, or react」を問う(「Should John react to the observation, and if so, what would be an appropriate reaction?」)→「We then regenerate the agent's existing plan starting from the time when the reaction takes place.」
- 効果: §5.1「we prompt the language model to ask what happens to the state of the object」(コーヒーメーカー off → brewing coffee)。場所は環境木を LLM が降りる(「Prefer to stay in the current area if the activity can be done there.」)。
- 待つ: 独立の語は無い。§1「wait outside the bathroom if it is occupied」は行動文の一例。"idle" は物の状態にだけ使われる。
- step 長は本文に無く、公式 README に「One game step represents 10 seconds in the game.」
- **v2 との対応**: **「活動=自由文+持続」の直接の先行**(**一致**)。ただし効果も LLM が書き保存則が無い(v2 の契約とは**矛盾**)。毎 step の知覚→反応判定は v2 の変化検出と同じ役割。

**2-2 Humanoid Agents(arXiv:2310.05418)**
- §3.2: 日→1 時間→15 分に分解、「Every 15 minutes, agents carry out an activity in their plan」/ §4.2「15-minute intervals between 6:00 am to 12:00 midnight」。
- 効果: LLM に「Does the activity {activity} involve {satisfaction-action}? Please respond only with either yes or no.」→ yes なら**コードが欲求値を +1**。欲求 ≤3 か感情が中立でないとき LLM が「determine if they should change their plan」。待つの語は無い。
- **v2 との対応**: 活動は自由文・持続は固定 15 分枠・**効果は自由文を LLM の二値分類でコード側の効果へ写す**=二層の中間形(**部分一致**・§9 の選択肢 D)。

**2-3 Concordia(arXiv:2312.03664 v2)**
- 抄録: 「Agents take actions by describing what they want to do in natural language.」「In a simulated physical world, the GM checks the physical plausibility of agent actions and describes their effects.」
- §2: grounded variables について「The GM determines the effect of the agents' actions on these variables, records them, and checks that they are valid.」例「the amount of money in an agent's possession may be a grounded variable … perhaps prevent them from paying more than they have available.」
- 付録 A.3: 「For grounded variables, which are tracked in Python, a specialised component is created to maintain the variable's state, update it after relevant events, and represent it to the GM in linguistic form」。action spec は自由形式/カテゴリ/float を指定できる(付録 A.1)。
- §2.1: 「Unlike RL, we do not assume that the agent responds with an action to every observation.」付録 A.3.1: 手番の 2 方式(1 体ずつ時計を進める/1 step 内で準同時)+「There is an option to execute player turns concurrently (concurrent_action flag), but it often leads to inconsistencies, although greatly speeds up the simulation.」
- 行動の**持続**の扱いは本文・付録 A に無い(時計は手番の後に進むだけ)。
- **v2 との対応**: **二層仮説に最も近い先行**=保存量(金・所持品・票)だけ Python で追跡し、それ以外は GM が叙述で解決(**一致**)。持続は**空白**。

**2-4 AgentSociety(arXiv:2502.08691)**
- §3.1「we explicitly model three types of social behaviors: mobility, social interactions, as well as employment & consumption」/「Other simple behaviors such as sleeping are directly handled by LLMs.」§3.3「Need - Plan - Behavioral Sequence」・雨なら「stay at home」。
- §4.1「By offloading tasks such as numerical computations, where LLMs cannot guarantee absolute accuracy, …」(移動は IDM/MOBIL、価格・賃金・金利はコード)。持続・step 長は取れた範囲に無い。
- **v2 との対応**: 世界に触れる 3 型はエンジン・睡眠のような単純行動は LLM 直=**親仮説とほぼ同じ切り方**(**一致**)。

**2-5 OASIS(arXiv:2411.11581)**
- §2.4「21 different types of interactions」…「and do nothing」。付録 D.1 のプロンプト「do_nothing : Most of the time, you just don't feel like reposting or liking a post, and you just want to look at it.」
- §2.5「one time step is equal to 3 minutes in OASIS」・体ごとの 24 次元の時刻別活動確率で活性化(§3.5 の 100 万体は「0.1 for core users」と一般 0.01)。効果は DB と推薦系(コード)。
- **v2 との対応**: **固定語彙+無行動を語彙の中に置く**先行=二層仮説の**反例側**(待つを語で持つ)。ただし位置も持続も無い SNS の世界。

**2-6 Sotopia(arXiv:2310.11667)**
- §2.2: 発話/非言語/身体行為の 3 型+自由文、「the agent can also choose to do nothing ( none ) to express silence or allow another agent to finish, or choose to leave to end the episode.」付録 C.1「none (indicating no action at this time step)」。ラウンドロビン・20 手上限。身体行為の効果はテキストのみ(状態=履歴)。
- **v2 との対応**: 「型は少数・中身は自由文」の形。none は語彙内。会話中心で効果を解かない=**ほぼ無関係**。

**2-7 AGA(arXiv:2402.02053)/ AgentSims(抄録のみ)**
- AGA:「The functionality of Lifestyle Policy is to minimize costs by reusing the similar inference processes of an LLM.」3 人町で AGA は基線の 31.1%(Lifestyle Policy のみ 40.2%)・表 1 の 25 人で 42.7%。抄録「agents can only generate finite behaviors in fixed environments」。
- **v2 との対応**: 決めた活動列を再利用して呼を減らす=「活動を持続させる」方向と**一致**。自由文でも行動は有限に収束するという観察は、語彙と自由文の差が見かけより小さい可能性を示す [推測]。

## §3 Q3 活動ベース交通需要モデルの活動と持続

**3-1 MATSim(公式ユーザーガイド=書籍の抜粋更新版)**
- 計画: `<act type="home" link="1" end_time="07:16:23" /> <leg mode="car">…` /「each plan contains a list of activities and legs. Exactly one plan per person is marked as selected. Each agent's selected plan is executed by the mobility simulation.」/「Activities should have a somewhat reasonable end-time.」
- 持続の価値: 採点に活動型ごとの `typicalDuration`(例 home 12:00:00・work 08:00:00)。式 (14.4) S_dur,q = β_perf · t_typ,q · (ln(t_dur,q / t_typ,q) + 1/prio_q)。待ち:「S_wait,q = β_wait · t_wait,q denotes waiting time spent, for example, in front of a still-closed store」「We recommend leaving β_wait at its default value of zero」。
- 再計画は反復の間(日単位): TimeAllocationMutator は「shifts activity end times randomly within a configurable range」、「Every agent possesses a memory containing a fixed number of day plans」。within-day replanning と BDI 統合(RMIT)は抜粋版の表に章があるが章番号が「??」で本文なし(空欄)。
- JDEQSim について「there is no time-step-based updating process of any agent in the scenario. Instead agents are only touched if they actually require an action.」/「QSim, however, is time-step based.」
- **v2 との対応**: 活動の中身はシミュせず **時刻・場所・持続だけが世界に効く**=「活動=ラベル+持続」の最も成熟した先行(**一致**)。持続は**事前計画の end_time** が決め、実行中の再判断は標準では無い(v2 の LLM 反応とは逆)。「待つ」は活動ではなく**採点される状態**(開店待ち)。

**3-2 ActivitySim(公式 v1.0.4)**
- Mandatory Tour Scheduling は「selects a tour departure and duration period (and therefore a start and end period as well) for each mandatory tour」、説明変数は「the mode choice logsum for the departure/arrival hour combination, demographics, and time pattern characteristics」。example_mtc は「the modeled time periods for all submodels are hourly from 3 am to 3 am the next day」。
- Trip Scheduling は「based on an input lookup table of percents by tour purpose, direction (inbound/outbound), tour hour, and trip index」。
- **v2 との対応**: 持続は**離散選択で事前に**決まり、下流は変えない=予定と実行の分業が完全(**一致**・事後反応が無い点は v2 と逆)。

**3-3 Bowman & Ben-Akiva 2001(抄録のみ)**
- 「The activity pattern consists of important decisions that provide overall structure for the day's activities and travel.」(a)「the primary - most important - activity of the day, with one alternative being to remain at home for all the day's activities」/「Tour models include the choice of time of day, destination and mode of travel, and are conditioned by the choice of activity pattern.」
- **v2 との対応**: 日の活動パターン → 時刻・目的地・手段の条件づけ=日課 → 活動 → 行為の階層と同形(**一致**)。「家に居る」は上位の選択肢の一つ。

## §4 Q4 ゲーム AI の活動と待機

**4-1 The Sims(Forbus & Wright 2001)**
- 「The set of behaviors consist of a procedure that implements it …, a procedure that checks to see whether or not it is possible, and a set of advertisements that describe its properties in terms of what need(s) of a Sim it will satisfy.」「Sims (not under direct player control) choose what to do by selecting, from all of the possible behaviors in all of the objects, the behavior that maximizes their current happiness. Once they choose a behavior, the procedure for that behavior (which is part of the object) is then run in the thread of the Sim itself」
- 「The Check Tree is a piece of code that indicates whether or not that interaction should be available, given the state of the object.」「Allow Consecutive means that this interaction can be queued up.」「Early versions of the Joy Booth were so addictive that Sims would continue using it until they collapsed.」
- 持続の明示欄は無い(手続きが終わるまで)。`Global:Wait for Notify` という大域手続きの名はあるが機能説明は無い。
- **v2 との対応**: **効果と前提は物(場所)の側のコード**が持つ=契約行を POI 側に置く形と同形(**一致**)。

**4-2 Graham 2013(Game AI Pro 第 9 章)**
- idle は最下位の bucket:「Only when none of the combat actions are valid will the guard choose an idle action.」(bucket = dual utility、Dill 2011 の引用)。The Sims も欲求で bucket 化し「a starving Sim will never even consider watching TV」。
- §9.7 Inertia:「If your AI agent is attempting to decide something every frame, it's possible to run into oscillation issues」→ 解は現行行動への加重・cooldown・「stall making another decision—either for a period of time or until such time as the current action is finished.」
- 「On The Sims Medieval, a Sim would only attempt to make a decision when their interaction queue was empty. Once they chose an action, they would commit to performing that action. Once the Sim completed (or failed to complete) their action, they would choose a new action.」(実務者の一次証言・計測ではない)
- **v2 との対応**: **決定の頻度を行動の持続に従わせる**(完了か失敗まで決め直さない)実務の先行=**一致**。

**4-3 Isla 2005(Halo 2)**
- 「on the order of 50 different behaviors」の DAG。「The first one that can run, does, but higher-priority siblings can always interrupt the winner on subsequent ticks.」「we must avoid at all costs the problem of dithering」「behaviors are disallowed for a certain amount of time after their last successful performance」。idle は behavior の一つ(「the decision to give up searching and return to idle」)。
- **v2 との対応**: 持続を宣言せず**毎 tick の安い再評価+高優先の割込み**で持続を作る別解(持続宣言の二層とは**別の形**)。idle は語彙内。

**4-4 Shao & Terzopoulos 2007(Autonomous pedestrians・駅の群衆)**
- 記憶スタックの各目標:「a descriptor of the goal type (e.g., catch a train, take a rest, reach a specific target point), the goal complexity (high or low), goal parameters …, preconditions (e.g., target must be within 0.5 m), and expiration time (e.g., for 3 s, until finished).」
- 「If g is a complex goal (such as "meet a friend"), it will be decomposed by a planner into subtasks (e.g., "go to the meeting point" and "wait").」「The expiration time attached to the memory item can cause the subtask to expire, re-exposing the original goal, thus guaranteeing frequent plan update.」「To make pedestrians persistent to their previous choice, … the original complex goal … is updated with concise information about the decomposition.」
- 欲求:「When the value of a mental state variable exceeds a specified threshold, an action selection mechanism chooses the appropriate behavior to fulfill the need.」規模: 30 frames per virtual second で「real-time simulation can be achieved for as many as 1400 autonomous pedestrians」。
- **v2 との対応**: **「待つ」は目標分解の末端の一つで、期限(秒か完了まで)つき**=「活動+持続」と**一致**。ただし待つは記号(語)でありコードのルーチン=自由文ではない。場が駅=v2 に最も近い。

## §5 Q5 効果の解決をコードで規定する理由と、LLM 裁定の例

- **STRIPS(Fikes & Nilsson 1971)**:「These effects are simply described by two lists. On the delete list we specify those clauses in the original model that might no longer be true in the new model. On the add list are those clauses that might not have been true in the original model but are true in the new model.」前提は「the applicability condition, or precondition, for an operator schema as a wff schema」。frame problem を「separating entirely the processes of theorem proving from those of searching through a space of world models」で回避。→ 契約行の祖型。**変わるものだけ書く**ので、何も変えない「待つ」は operator を要しない [推測]。
- **LLM 裁定の例**: Generative Agents の物の状態(§2-1)・Concordia GM の叙述(§2-3)・Sotopia のテキストのみ(§2-6)。
- **コードに置く理由の言明**(読んだ範囲): Concordia「checks that they are valid」と所持金超過の拒否/AgentSociety「where LLMs cannot guarantee absolute accuracy」/Concordia 付録 A.3.1 の並行手番「often leads to inconsistencies」/ Project Sid §1.3 の食い違い(チャットは「Sure thing!」、関数呼び出しは別行動 →「Bob might then attempt to mine using an imaginary pickaxe.」)。
- **定量の反証(Wang ら 2024, ACL)**: 抄録「it is still an unreliable world simulator without further innovations.」本文「LLMs broadly fail to capture state transitions not directly related to agent actions, as well as transitions that require arithmetic, common-sense, or scientific reasoning. Across a variety of conditions, model accuracy does not exceed 59.9% for transitions in which a non-trivial change in the world state occurs.」行動駆動(蛇口を開ける)と環境駆動(コップに水が溜まる)を分けて測る。GPT-4・テキストゲーム(ByteSized32)での値。
- **空欄**: 「再現性(同 seed 同結果)」を理由にコード側で解決すると明言した一次は見つからなかった。
- **v2 との対応**: 保存量・数値・他者が前提にする事実はコード、は先行の言明と**一致**。環境駆動の間接効果(飲料 → 体感温度など)が LLM で最も弱い点も**一致**。

## §6 Q6 決定の頻度と持続

| 先行 | 決定の引き金/頻度(原典の値) | 持続との関係 |
|---|---|---|
| Generative Agents | 1 step=10 秒(README)・毎 step 知覚 → LLM が反応可否 | 計画の持続は 5〜15 分粒度、反応で以後を再生成 |
| Humanoid Agents | 15 分ごと | 1 活動=1 枠 |
| OASIS | 1 step=3 分・時刻別活性化確率 | 持続なし |
| Project Sid | 目標生成は 5〜10 秒ごと | 「Keep the same subgoal unless…」で保持 |
| Lyfe Agents | option の終了時だけ LLM(終了判定は非 LLM) | 毎 step 呼ぶ ablation は会話を 3 倍早く抜ける |
| The Sims Medieval | 相互作用キューが空のときだけ | 完了か失敗まで commit |
| Halo 2 | 毎 tick 再評価+割込み | 持続は宣言しない |
| Shao & Terzopoulos | HSS ごと・欲求が閾値超え・期限切れで再計画 | 期限つき目標(for 3 s / until finished) |
| MATSim | 反復の間(日単位)に再計画 | end_time まで実行 |

- **イベント駆動 vs 固定ステップ(エンジンの時間進行)**: Buss & Al Rowaei 2010 結論「with relatively large time steps, the incorrect answer is obtained very rapidly」「the next-event time advance used by DES models appears to be uniformly superior to the standard time-step approach commonly used.」(単純な待ち行列モデルでの比較)。MATSim の JDEQSim も事象駆動(§3-1)。
- **ただしこれらはエンジンの時間進行の比較で、LLM 呼の引き金の比較ではない**。LLM エージェントでイベント駆動と固定周期を同条件で比べた一次は見つからなかった(空欄)。最も近いのは Lyfe の ablation(§1-4)。
- **意図の保持**: Rao & Georgeff の commitment/termination(§1-3)・Kinny/Schut(R-41 参照)・Sutton の割込み定理(§1-1)。前者群の「計画費が高いほど強く保持」と Sutton の「価値が落ちれば割り込む」は逆向きではなく両立する [推測: v2 の呼の費用比では未計算]。
- **v2 との対応**: v2 の 7〜15 呼/体/日は Lyfe・Sims Medieval 型(持続の境界でだけ決める)の頻度帯に近い。1 呼で 1 tick 粒度の語を選ぶと、呼と呼の間をエンジンが既定の継続で埋める構造になる=ユーザーの指摘の形 [推測]。現実の活動切替回数の錨は既存ノート [v2-thought-frequency-anchors-note.md](v2-thought-frequency-anchors-note.md)(本書では再確認していない)。

## §7 Q7 活動の自由文を他者の観測に出す先行

- **Generative Agents**(最も直接): §5「sending all agents and objects that are within a preset visual range for each agent to that agent's memory」。記憶に入る観測は「John saw Eddy taking a short walk around his workplace」、文脈検索のクエリは「[Observed entity] is [action status of the observed entity]」=**他者の活動文がそのまま観測者の記憶になる**(**一致**)。
- **Concordia**: GM が event statement を作り観測を配る。「In case the GM judges that a player did not observe the event, no observation is emitted.」=見えるかどうかも GM(LLM)の裁定。
- **AgentSociety**: 行動後に作る 1 文(「a sentence is used to describe its behavior in relation to the current context」)は本人の態度と感情の更新に使う=他者へ出すとは書いていない。
- **Shao & Terzopoulos**: 知覚事象は記号(「"that ticket window is available", "that seat is taken"」)。
- **危険の先行(Project Sid §1.3)**: 発話と行動が食い違うと他者が実在しない物を前提に動く(§5)。→ 自由文の活動を他者に見せるなら、**世界の事実(位置・所持・占有)と食い違わない**保証が要る。
- The Sims の他者行動の観測・MATSim は該当記述なし。

## §8 横断表

| 出典 | 語彙/自由文 | 持続の決め手 | 効果の解決者 | 待つの表現 | 決定の引き金 |
|---|---|---|---|---|---|
| Sutton ら 1999 | option(集合は設計次第) | β(状態/履歴・timeout 可) | 環境(MDP) | 記述なし | option 終了時(割込み可) |
| Erol ら 1994 HTN | 記号タスク(primitive/compound) | 記述なし | operator(primitive のみ) | 記述なし | 分解時 |
| Rao & Georgeff 1995 | intention/atomic action | termination condition(達成・不可能) | 実行系 | 記述なし | 毎サイクル(事象キュー) |
| Lyfe Agents | option+下位目標(LLM)・外部は move/talk | 非 LLM 判定(時間・反復検出) | 3D 環境 | 記述なし | option 終了時のみ LLM |
| Project Sid | 目標は自由文 → 低レベル行動 | 記述なし | Minecraft(暗黙) | 記述なし | 目標 5〜10 秒ごと・並行モジュール |
| Generative Agents | 自由文+場所+持続 | 計画の duration(LLM) | 物の状態も LLM | 独立語なし(行動文) | 毎 step 知覚 → LLM 反応判定 |
| Humanoid Agents | 自由文 | 固定 15 分枠 | LLM の yes/no → コード +1 | なし | 15 分ごと・欲求/感情で計画変更 |
| Concordia | 自由文(型指定可) | 記述なし | GM(LLM)+grounded は Python | 明示なし(act しない自由) | GM の手番 |
| AgentSociety | 3 型はコード・単純行動は LLM | 記述なし | 都市/経済シミュ(コード) | 「stay at home」 | Need → Plan・受動事象 |
| OASIS | 21 語の固定集合 | なし(3 分 step) | DB+推薦系(コード) | do_nothing(語彙内) | 時刻別活性化確率 |
| Sotopia | 3 型+自由文 | なし(手番) | テキストのみ | none(語彙内) | ラウンドロビン |
| MATSim | 活動型+end_time | 事前計画(end_time) | mobsim(コード) | 採点される状態(S_wait) | 反復間の再計画 |
| ActivitySim | tour/trip | 離散選択(出発・到着・持続) | 下流モデル | 上位に「家に居る」(Bowman) | モデル連鎖(事前) |
| The Sims(Forbus & Wright) | 物が広告する behavior | 手続きの終了 | 物側のコード | 記述なし | 幸福の最大化(Medieval はキュー空) |
| Halo 2(Isla) | 約 50 の behavior | 宣言なし(割込み) | コード | idle は behavior | 毎 tick 再評価 |
| Shao & Terzopoulos | 目標型(記号)+パラメータ | expiration(for 3 s / until finished) | コード(運動層) | wait はサブタスク | HSS ごと・閾値・期限切れ |
| STRIPS | operator | 記述なし | add/delete list | 記述なし | 計画時 |
| Wang ら 2024 | — | — | LLM は非自明な遷移で ≤59.9% | — | — |

## §9 設計の選択肢(推奨ではなく選択肢と根拠)

**先行が示す「持続の終了条件」の型**(親の 4 種との対応): 時間(Sutton の timeout・Lyfe・Shao「for 3 s」)=「N 分」/ 達成(Rao の drop-successful・Shao「until finished」)=「到着」「相手が来る」/ 予定(MATSim の end_time)=「次の予定まで」/ **先行にあって親案に無いもの**: 不可能・失敗(Rao の drop-impossible・Sims Medieval「or failed」)、より良い選択肢による割込み(Sutton Thm 2・Halo 2)、新しさの枯渇(Lyfe の反復検出)。

**二層仮説を支持する先行**: Concordia(保存量だけ Python・他は叙述)/ AgentSociety(3 型はコード・睡眠は LLM)/ Lyfe(LLM は option を選び終了は非 LLM)/ Sutton(option と timeout)/ HTN(効果は末端だけ・往復は目標で書けない)/ Rao & Georgeff(atomic な行為と持続する意図)/ MATSim(活動はラベル+持続・中身は解かない)/ Sims Medieval(持続の境界でだけ決める)/ Wang 2024・Project Sid(世界の事実を LLM に任せると壊れる)。
**反する・注意を促す先行**: OASIS・Sotopia(無行動を語彙内に置く)/ Halo 2(持続は宣言せず毎 tick 再評価)/ Shao(待つは自由文でなく記号のサブタスク)/ Generative Agents(持続も効果も LLM・保存則なし)/ MATSim の S_wait と Generative Agents の「wait outside the bathroom if it is occupied」(**待つの一部は世界に触れる**=行列の順番・場所の占有・その場に居ることが他者に見える)。

- **選択肢 A(親仮説): 行為=契約語彙(世界に触れるものだけ)/活動=自由文+持続(終了条件つき)**。根拠: Concordia・AgentSociety・Lyfe・Sutton・MATSim。注意: 待つを「行列の待ち(占有・順序=行為)」と「人を待つ・休む(位置だけ=活動)」に分ける必要(MATSim S_wait・GA の bathroom・v2 の D-113 ③ の待ち行列)。活動文を他者に見せるなら事実との食い違い検査(Project Sid)。
- **選択肢 B: 全部を語彙のまま、各語に持続欄と終了条件を足す**(待つも語のまま)。根拠: OASIS・Sotopia(no-op が語)・Shao(wait は期限つき記号)・HTN(primitive は記号)。利点は効果の解決が全部コードで閉じる点、欠点はユーザーの指摘(粒度)が残る点。
- **選択肢 C: 全部を自由文にして裁定(GM 型)**。根拠: Concordia の GM・GA の物の状態・Sotopia。反証: Wang 2024(非自明な遷移で ≤59.9%)・Concordia 並行手番の不整合・v2 の保存則(月次収支)と衝突。
- **選択肢 D: 活動は自由文、効果は分類器で契約へ写す**(Humanoid Agents の yes/no → コード +1)。根拠: Humanoid Agents。v2 の System 1.5(同じ艦隊の logprob 判断・D-101/第254)と同じ口に載る [推測]。
- **選択肢 E: 持続を宣言せず、安い再評価(変化検出)で持続を作る**。根拠: Halo 2・Graham の inertia(加重・cooldown)。v2 の現行(変化検出で起こす)はこの形に近く、A の「持続」との差は**終了条件を LLM が宣言するか、エンジンが既定で持つか**。
- **組み合わせの先行**: Shao(記号の目標+期限+再計画)と Lyfe(LLM の option+非 LLM 終了)は A と E の中間。どれを選んでも Sutton の Thm 2 に従い「持続は割込み可能な上限」とするのが先行の共通項。

## §10 空欄・未確認

| 項目 | 理由 |
|---|---|
| Bratman 1987(書籍)本文 | 書籍のため取れず。Rao & Georgeff・Bratman ら 1988 抄録経由の間接のみ |
| S3・RecAgent | 未調査(問いの「必要なら」枠) |
| Wright(The Sims)の GDC 講演の一次 | 見つからず。Forbus & Wright 2001 で代替 |
| Dill 2011(dual utility 原典) | 未読。Graham 2013 の引用のみ=二次 |
| Concordia の時計(コード) | GitHub のパスが 404。論文本文に持続の記述なし |
| MATSim の within-day replanning・BDI 統合の章 | 抜粋版で章番号「??」=本文なし |
| Generative Agents の付録・呼の回数/step | ar5iv で付録まで届かず |
| Project Sid の制御器の決定頻度・行動の持続 | 本文に記述なし(記述の不在) |
| AgentSociety の step 長・持続 | 取れた範囲に無し |
| LLM エージェントでの事象駆動 vs 固定周期の同条件比較 | 見つからず(Buss 2010 はエンジンの時間進行) |
| 「再現性」を理由にコード解決を明言した一次 | 見つからず |
| Bowman & Ben-Akiva 2001 本文 | 出版社 403=抄録のみ |

## §11 親への確認依頼(逐語の確認が要る箇所)

1. **Lyfe の倍率**: 抄録「10-100 times lower」と序論「30-100 times less」が論文内で不一致。比較相手の 25 USD/体/時は付録 F の**仮定つき推定**(1 分に 1 回計画・10 倍速)=設計書に写すなら 0.5 USD の実測だけ、倍率は不一致を併記で。
2. **Project Sid「every 5-10 seconds」**: 実時間かゲーム時間か本文に無い。
3. **Generative Agents の 10 秒/step** は論文でなく公式 README の記述。
4. **Wang 2024 の 59.9%**: 本文の上限値(「does not exceed 59.9%」)。表 2 の条件別値(例 LLM 規則・dynamic・Full 59.0)と取り違えないこと。GPT-4・テキストゲームでの値。
5. **Concordia の版差**: ar5iv(v1)の HTML には action prompt 例「what would Alice do in the next hour?」があったが、v2 PDF の抽出には一致しなかった=本書は v2 の文面だけを引いた。
6. **MATSim** の頁・式番号は 2026/08/25 編集の抜粋版のもので、2016 年の書籍版と番号が違う可能性。
7. **Shao & Terzopoulos の「for 3 s, until finished」** は goal の性質の例示で、実装の既定値かは本文から判別できない。
8. **Graham 2013 の Sims Medieval の記述**は実務者の一次証言で、計測ではない。
9. **§9 の「待つの一部は世界に触れる」**は MATSim S_wait・GA の bathroom 文からのサブの読み=先行が明言した分類ではない [推測]。
