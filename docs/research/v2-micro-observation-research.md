# 答申: エージェント個体の追跡・検査(ミクロ観察)の先行例 — M1 の設計材料(2026-09-17・レーン R-4)

<!-- hdr:v1 -->
- **分野**: 検証と V&V #22 / ABM 方法論 #21 / ソフトウェア工学 #29 | **重要度**: **P1**(第177 の判断 M1 の材料。自前設計の比重がどれだけあるかを先に知るための調査)
- **一次確認**: **B**(サブ Opus 5 が **12 出典 / 17 文書**を実読。PDF 2 本(ODD 補遺 S1 62 頁・MATSim ユーザーガイド 216 頁)は curl → システム python の pymupdf で本文抽出、残りは HTML 本文取得。**抄録のみ = 1 件**(Stadler et al. 2022 本文)、**未読 = §3 の 12 件**。**親一次確認は未了**——§2 を決定に使う前に §5 の「親が最初に一次確認すべき 3 件」を通すこと) **→ 親確認 3 件(第211)**: ODD 2020 補遺 S1(jasss.org PDF・親 pymupdf)「by selecting one or more agents and having them record their state over simulated time」「it is impossible to observe and analyze everything … so we must explain what results we do observe」「The model randomly selects one bird per day and displays a trace of its movement」/ Generative Agents(arXiv 2304.03442v2 PDF)「Out of the 453 agent responses … 1.3% (n=6) were found to be hallucinated」・density 0.167→0.74・「watching a replay of a randomly chosen agent's life」/ de Montjoye 2013(Europe PMC 全文)「four spatio-temporal points are enough to uniquely identify 95% of the individuals」「decays approximately as the 1/10 power of their resolution」。他は親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)(R-4) ・ **lit**: [lit/README.md](lit/README.md)(本答申と同時に 6 本) ・ **判断**: STATUS「判断待ち M1」/ 計器盤 [v2-dashboard-verification-orchestration.md](../design/v2-dashboard-verification-orchestration.md) G-1・G-3

> **問い**: 1 体の 1 日を全部見る(個体カルテ)・1 セルの 1 日を全部見る(場所カルテ)という道具に、先行例はあるか。あるなら粒度・保存量・再生との結線・「逸話を結論にしない」規律・公開時の作法をどう決めているか。
>
> **答え(要旨)**: 5 つ分かった。
>
> (i) **道具の型は既に確立していて、自前設計の比重は小さい**。ODD(ABM 記述の標準)は「Observation」を 11 の design concept の 1 つとして持ち、補遺 S1 が**個体レベルの観察を明示的に認めている**——"Modelers sometimes also collect observations at the agent level, e.g., by selecting one or more agents and having them record their state over simulated time."(S1 p.23)。同じ S1 の実例が「**1 日 1 羽を無作為に選んでその日の移動の trace を表示する**」(Railsback & Johnson 2011)。**個体カルテは ODD の語彙で書ける**=自前宣言にしなくてよい。
>
> (ii) **個体カルテと場所カルテを「同じ記録の 2 つの問い方」として実装した先行が交通側にある**。MATSim の可視化ツール Via は、レイヤに紐づかない特別なクエリとして **agent plan(個体)** を持ち、別に **Select Facility Analysis / 施設ごとの時間帯別の到着・出発・滞在(場所)** を持つ。どちらも同じ `events.xml`(1 行 = 1 個体の 1 行動)から引く。**カルテは新しい記録ではなく、既存テープの読み口**という結論が先行で裏づく。
>
> (iii) **逸話の扱いには、先行が実際に使った具体的な手続きがある**。Generative Agents は逸話を「§7.2 Boundaries and Errors(失敗の 3 型)」にだけ置き、**成功側は逸話を全部数値に降ろした**——25 体全員に聞き取り → 4%→32% / 4%→52%、関係網密度 0.167→0.74、そして **453 応答のうち 1.3%(n=6)が幻覚**を「記憶ストリームの中に該当の会話を見つける」ことで判定している。評価も「**無作為に選んだ** 1 体の replay」。POM 側の原則は "Models can easily be calibrated to reproduce a single pattern of interest, but potentially for the wrong reasons."(Grimm & Railsback 2012 §2)。
>
> (iv) **保存量は場所カルテと個体カルテで桁が違い、決め方が非対称**。場所は **520 セル**しかないので全数を毎分持てる(≈24 MB/シミュ日 = S1 の 0.5%)。個体は 40 万体 × 1,440 tick = **5.76 億 体·tick/日**で、1 体·tick あたり 8 B でも 4.6 GB = S1 予算 5 GB の 92%——既決の「個体×tick 全記録禁止」は算術としても正しい。**したがって個体カルテは必ず抽出になり、抽出規則が設計の本体**になる。観測系(OpenTelemetry)の head/tail sampling がそのまま当たる。
>
> (v) **「合成だから公開してよい」は文献上そのままでは通らない**。実移動データでは "four spatio-temporal points are enough to uniquely identify 95% of the individuals"(de Montjoye 2013)で、粗くしても "the uniqueness of mobility traces decays approximately as the 1/10 power of their resolution"。我々の体は実データから学習した生成物ではなく統計から合成した架空個体なので de Montjoye/Stadler の脅威モデルはそのまま当たらない——が、**カルテの形が「実データなら特定できる形」そのもの**であることと、**場所カルテが実在店舗の時間帯別来客数として読まれうる**ことは別問題として残る。

---

## 1. 問いごとの一次確認(逐語 ≤125 字・節/図つき)

### 1-1. Generative Agents(2304.03442)の replay / inspect と、評価での逸話の扱い

| 出典 | 逐語(節) | 数値 | v2 への含意 |
|---|---|---|---|
| **Park et al. (2023)** "Generative Agents: Interactive Simulacra of Human Behavior" <https://arxiv.org/abs/2304.03442>(本文は ar5iv 版 <https://ar5iv.labs.arxiv.org/html/2304.03442>) | §3.1.1 "**The complete natural language description of the action can be accessed by clicking on the agent's avatar.**" / §5 "**The server maintains a JSON data structure that contains information about each agent in the sandbox world**" / §5 "The agent's output action then updates the JSON, and the process loops for the next time step." | — | **inspect の入口は「アバタをクリック→その体の全文」**。世界の状態は 1 個の JSON。**v2 のカルテはこの「クリック 1 回で 1 体の全文」を、UI なしのファイルで満たす形**にできる |
| 同上 | §6.1 "**watching a replay of a randomly chosen agent's life in Smallville**" / §6.1 "**Participants had access to all information stored in the agent's memory stream.**" / §6.1 "Agents were sampled from the end of a two game day simulation with the full architecture" | 評価者 100 名(Prolific)・所要 ≈30 分・5 条件(全構成+ablation 3+人間クラウドワーカ)の順位づけ・シミュは 25 体 × 2 ゲーム日 | **「無作為に選んだ 1 体の replay + 記憶の全開示」が評価の単位**。これは逸話の反対物——**抽出が無作為であることと、判断材料が全部見えていること**の 2 点で担保している。v2 の M1 も「選び方」を先に決めなければ同じ担保が得られない |
| 同上 | §7.1.1 "**we verified that the agents did not hallucinate their responses by locating the specific dialogue in their memory stream.**" / §7.1.2 "**Out of the 453 agent responses regarding their awareness of other agents, 1.3% (n=6) were found to be hallucinated.**" | 市長選の認知 1 体(4%)→8 体(32%)・パーティ 1 体(4%)→13 体(52%)・関係網密度 0.167→0.74・招待 12 体中 5 体が出席(欠席 7 のうち 3 が予定衝突・4 が関心はあるが計画せず) | **これが「逸話を結論にしない」の実行形**。物語(Isabella がパーティを開いた)を **(a) 全 25 体への聞き取り (b) 前後の数 (c) 記憶ストリームでの裏取り**の 3 段に降ろしている。**(c) が M1 の存在理由そのもの**——カルテがなければ幻覚率 1.3% は計算できない |
| 同上 | §7.2 "identifying **three common modes of erratic behavior** that future research could address and improve upon" / 型2 "erratic behaviors caused by **misclassification of what is considered proper behavior**" / 型3 "we observed possible effects of **instruction tuning**" | 型1 = 場所を覚えるほど不自然な場所を選ぶ(昼食にバー)・型2 = 一人用トイレへの入室、17 時以降の店舗・型3 = 過度に礼儀正しく、断らない | **逸話が登場するのは「失敗の分類」の側だけ**。成功の証拠には使っていない。**M1 の規律はここを写す=カルテから拾った物語は「失敗の型の命名」にしか使わない** |
| 同上 | §8.2 評価は "**limited to a relatively short timescale and a baseline human crowdworker condition**" / "the robustness of generative agents is still largely unknown" / 25 体 2 日で "costing thousands of dollars in token credits and taking multiple days to complete" | — | **この論文自身が「短期 + クラウドワーカ基準線」を限界として明記**している。v2 の M1 を「観察を増やせば妥当性が上がる」と読んではいけない根拠 |

**要点**: Generative Agents に「タイムラインを巻き戻すデバッガ」は無い。あるのは **(1) 状態が 1 個の JSON であること (2) アバタのクリックで全文が出ること (3) 記憶ストリームが全部見えること**の 3 つで、replay はそれを再描画しているだけ。**v2 のテープ再生(決定論・ハッシュ一致)は先行より強い**——足りないのは「1 体分を引く読み口」の側。

### 1-2. Concordia(DeepMind)の GM ログ・エンティティの検査

| 出典 | 逐語 | v2 への含意 |
|---|---|---|
| **Concordia CHEATSHEET.md** <https://github.com/google-deepmind/concordia>(raw: `raw.githubusercontent.com/google-deepmind/concordia/main/CHEATSHEET.md`) | "Concordia provides an **`AIAgentLogInterface`** for programmatic log analysis." / 取得 `log = simulation.play(return_structured_log=True)` / 保存・復元 `log.to_json()` ・ `SimulationLog.from_json(...)` | **ログは構造化 JSON の一級オブジェクト**で、走らせ直さずに読み口だけ差し替えられる。v2 のテープと同じ位置 |
| 同上(Debugging workflow) | メソッド列: `get_overview()` / `get_entity_actions(name)` / `get_entity_action_context(name, step)` / **`get_entity_timeline(name)`** / `get_step_summary(step, include_content=True)` / `search_summaries('keyword')` / `search_entries('keyword')` / `get_entry_content(entry_index=N)` / `get_entity_memories(name)` / `get_game_master_memories()` | **`get_entity_timeline(name)` が個体カルテ、`get_step_summary(step)` が時刻断面**。つまり**先行は「体で切る」「時刻で切る」の 2 軸を最初から API に持つ**。v2 の「個体カルテ / 場所カルテ」は第 3 軸(場所で切る)を足す形になる |
| 同上(CLI `concordia-log`) | `concordia-log components sim.json --entity Alice` / `--component __act__` / `--component MyComponent --key Key --step 3` / 他に `overview` `actions` `context` `step` `search` `memories` `entities` `timeline` `dump` / "Base64 image data is stripped unless `--include-images` is passed" | **読み口は GUI でなく CLI が先**(GUI は `utils/log_viewer.html` 1 枚)。v2 の M1 も「CLI + HTML 1 枚」で足りる可能性が高い。画像の既定ストリップ = **重い項目は既定で落とす**の先例 |
| **CHANGELOG.md** 2.4.0 | "Add generic **log_viewer.html** and simplify the Simulation.play API." / "**Add log analysis CLI**" / "Add support for logs produced by the asynchronous engine to the generic log viewer." / "**Add dynamic state editing in the visual interface** and additional visualization improvements" | 読み口は後付けで足されている(=先に記録、あとで読み口)。**「状態編集」まで UI に入れているのは我々の方針(観測は世界を 1 バイトも変えない)と逆**——採らない道 |
| 同上 2.4.0 | "**Add missing variables in get_state/set_state methods for all components.**" / "**Fixing scene serialisation error that was crashing jobs after restoration from a checkpoint.**" / "generic simulation now saves more info in checkpoints" | **再生ではなく「checkpoint からの復元」**が Concordia の巻き戻し。そして**「全 component の get_state に漏れがあった」「復元後に落ちた」が実際に起きている**=v2 の T2-c(checkpoint 自己整合)の価値の外部裏づけ |
| 同上 1.8.0 | "**Make it optional to include full episode summaries in HTML logs and turn it off for the contest environments.**"(既定は変えない) | **カルテの粒度を切替口にして、重い場面では落とす**の先行。v2 の「既定バイト不変 + 切替口」の作法と同型 |
| 同上 2.4.0 | "**Fix broken HTML log rendering due to broken regex in structured_logging_html.py.**"(本文に、エスケープのバグでシミュレーション HTML ログが空になっていた旨の説明が続く) | **計器そのものが黙って空になる事故が実際に起きている**。v1 の「内省空バグ」と同型。**M1 には「カルテが空でないこと」の検査が要る**(§2 O16) |
| 同上 2.1.0 | "**Adding a callback to get the state of the simulation after every step**"(独自 checkpoint 用)/ "Add option to **return raw log** from simulation.play" | 毎ステップの状態取得はコールバックで外出し=**基盤側に checkpoint 方針を焼き込まない** |

**ログの粒度・再生の可否(問いへの直答)**: 粒度は **entity × step × component × key** の 4 次元(CLI の引数がそのまま次元)。**「再生」という語は CHANGELOG/README/CHEATSHEET のどこにも無い**。あるのは **(a) 構造化ログの読み直し (b) checkpoint からの復元**の 2 本立て。**v2 のテープ再生(同一入力 → バイト一致)は Concordia より強い保証**で、M1 はその上に読み口だけ足す形になる。

### 1-3. AgentTorch / AgentSociety / OASIS の追跡・可視化(個体軌跡と集計の分離)

| 基盤 | 個体側 | 集計側 | 分離の有無 |
|---|---|---|---|
| **AgentSociety** <https://agentsociety.readthedocs.io/en/latest/> ・ <https://agentsociety.readthedocs.io/en/latest/01-get-started/04-webui.html> | 結果画面で "**observe agent movement trajectories, state changes, inner activities, agent-to-agent dialogues, etc.**" / "**If you click on an agent's avatar, you can view more detailed information about that agent and interact with it**"(聞き取り・アンケート送付)/ プロフィール項目 = "name, gender, age, education level, occupation, marital status, personality role, background story" | 同じ画面で "**view global metric changes**" / `Export All` は "**including agent states, agent dialogues, global prompts, etc., at each simulation moment**" | **あり(API モジュールの段で分かれている)**: `agentsociety.webapi.models.agent` と `agentsociety.webapi.models.metric` が別モジュール。**3 基盤で唯一、個体と集計を UI と API の両方で分けている** |
| **AgentTorch** <https://github.com/agenttorch/agenttorch> ・ <https://agenttorch.github.io/AgentTorch/> | `runner.state_trajectory`(状態の時系列)。論文 <https://arxiv.org/abs/2409.10568>(Chopra et al. 2024, v3)は個体検査の道具を持たず、"**verifying the accuracy of individual agent behaviors generated by LLMs remains challenging**" と書く | `agent_torch.visualize` の `GeoPlot` が Cesium 用 HTML を書き出す。論文 "**We currently measure performance via comparisons with mesoscopic census data**"(Fig.8 = 郵便番号単位の就業行動・840 万体) | **無い(集計側のみ)**。**8.4M 体規模では個体検査を諦めて mesoscopic で測る**という選択をしている——**v2 の 40 万体でも同じ引力がかかる** |
| **OASIS** <https://github.com/camel-ai/oasis> | 走行結果は 1 個の DB ファイルに入る(`db_path = "./data/reddit_simulation.db"` ・ `oasis.make(..., database_path=db_path)`)。**個体の事後検査の手順は README に無い**。近いのは "Support **Interview Action** for asking agents specific questions and getting answers."(2025-06-02) | `visualization/` ディレクトリと、"how to visualize and analyze social simulation data once your experiment concludes" への導線 | **記録はあるが読み口が無い**(README の範囲では)。"replay" の語は 1 度も出ない |

**問いへの直答**: **個体軌跡と集計の分離を明示的に持つのは AgentSociety だけ**。AgentTorch は規模を理由に個体検査を放棄し、OASIS は DB を置くところで止まっている。**つまり「記録があるのに読めない」が業界の既定状態**で、Via の設計動機(§1-5)とまったく同じ穴。

### 1-4. ABM の「逸話を結論にしない作法」(ODD 2020 / POM)

| 出典 | 逐語(節・頁) | v2 への含意 |
|---|---|---|
| **Grimm et al. (2020)** ODD 第 2 次更新, *JASSS* 23(2) 7, doi:10.18564/jasss.4259 <https://www.jasss.org/23/2/7.html> | 要素の順: 1 Purpose and patterns / 2 Entities, state variables and scales / 3 Process overview and scheduling / 4 Design concepts(11 概念)/ 5 Initialization / 6 Input data / 7 Submodels。Box 1 "**The patterns are observations, at the individual or system level, that are believed to be driven by the same processes**" | **「個体レベルの観察」は ODD の要素 1 の中に正式な場所がある**。M1 は新語彙を要さない |
| 同上 | §3.7 "there is no specific place in ODD for emergent patterns"(§4.7 で patterns を要素 1 へ移した理由)。Box 1 "**Reporting, in the first ODD element, only those patterns that the model could capture would resemble "HARKing"**" / "**Better practice would be to report on missing patterns**" | **再現できなかったパターンも先に書け**。逸話規律の裏側。v2 の受入表・計器盤 面1/面2 に「再現できていないアンカー」の欄を義務化する根拠 |
| **同 補遺 S1**(ODD Guidance and Checklists 2020)<https://www.jasss.org/23/2/7/S1-ODD.pdf> pp.22–23「Observation」 | "This concept describes **how information from the ABM is collected and analyzed, which can strongly affect what users understand and believe about the model.**" / "**it is impossible to observe and analyze everything that happens in such a model so we must explain what results we do observe.**" / "This concept is **not** intended to document how simulation experiments and model analyses are conducted, but instead to describe **how information is collected from the model** for use in such analyses." | **観察の設計は「実験の設計」と別項目**であると明記。**v2 の計器盤(G-1 の 3 面)は「実験・判定」の側で、M1 は「収集」の側**——両者を混ぜてはいけない |
| 同 S1 p.22 | "**It is especially important to understand whether analyses considered only measures of central tendency (e.g., mean values of variables across agents) or also observed variability among agents**, e.g., by looking at distributions of variable values across all agents." | **平均だけを見たのか分布も見たのかを記述せよ**。D-68(個体の同質性)と計器盤の「分布で報告」(G-8 第203 追記)に直結 |
| 同 S1 p.23 | "**Modelers sometimes also collect observations at the agent level, e.g., by selecting one or more agents and having them record their state over simulated time.** Such observations can be useful for understanding behaviors that emerge in a model." | **個体カルテの ODD 上の定義そのもの**。「1 体以上を選んで、その状態をシミュ時間に沿って記録させる」 |
| 同 S1 p.23 | "The ability to legitimately compare simulation results to data collected in the real world can be a major observation concern" / "**This "virtual scientist" technique (modeling the data collector; Zurell et al. 2010)** strives to understand the biases and uncertainties in the empirical data by reproducing them in an ABM" | **「観測の仕方そのものを模す」=virtual scientist**。v2 の KDDI 在圏との照合は既にこの形(在圏の定義に合わせて数える)。**M1 に加えるなら「KDDI と同じ数え方で 1 セルを数える場所カルテ」**という道がある |
| 同 S1 p.52(Observation の例文・Railsback & Johnson 2011, *Ecol Model* 222:3305–3319) | "**The model randomly selects one bird per day and displays a trace of its movement during the day, so foraging patterns can be observed.**" / "**Virtual surveys** are a special kind of observation designed for comparison of model results to field surveys" | **「1 日 1 個体を無作為に選んで、その日の trace を出す」が査読論文で実際に使われた形**。**個体カルテの粒度と抽出規則の、最も近い先行**(§2 O1・O5) |
| **Grimm & Railsback (2012)** "Pattern-oriented modelling: a 'multi-scope' for predictive systems ecology", *Phil Trans R Soc B* **367**(1586):298–310, doi:10.1098/rstb.2011.0180 <https://pmc.ncbi.nlm.nih.gov/articles/PMC3223804/> | §2 "**Models can easily be calibrated to reproduce a single pattern of interest, but potentially for the wrong reasons.**"(equifinality)/ §2 "**a single pattern is rarely enough to fully decode the internal organization and achieve structural realism**" / §2 "**Each pattern used in POM can be considered a filter that helps reject unacceptable models or parametrizations.**" | **「1 つのパターンが合った」は結論にならない**——逸話規律の最も一般的な形。**v2 のパターン台帳ゲートが既に採っている思想の原典側の逐語** |
| 同上 | §2 "**Weak patterns are often qualitative and can be described with a few words or numbers**" / "**A weak pattern is less striking and therefore often easier to reproduce—in isolation—by multiple models**" / §3(a) step 2 "**Do not ignore weak patterns.**" / §2 "In POM, we seek models that **simultaneously** reproduce a diverse set of patterns." / §4 "POM is the **multi-criteria design, selection and calibration** of models of complex systems" | **弱いパターンは単独では効かないが、束ねると効く**。**個体カルテから出てくるものはほぼ全部「弱いパターン」**=単独で主張にせず、束ねて台帳へ入れるのが正しい置き場 |

**Grimm et al. 2005 *Science* 310(5750):987–991, doi:10.1126/science.1116681 は有料で本文未取得**(§3)。上の「weak patterns / multiple patterns」の逐語は**同じ著者らの 2012 open access 版から採った**もので、2005 の逐語ではない。

**Railsback & Grimm 教科書の該当章** = *Agent-Based and Individual-Based Modeling: A Practical Introduction*(2nd ed., Princeton UP)の **第 9 章 "Observation"**。本文は未読(§3)。確認できたのは公式サイトの章要旨のみ(「なぜ ABM の観察の仕方が重要かの短い議論から始まり、観察すべき結果の種類を論じ、NetLogo の図とファイル出力の道具の使い方へ進む」)。**補遺 S1 は同書 Chapter 03 のダウンロードとしても配布されている**(<https://www.railsback-grimm-abm-book.com/E2-Downloads/Chapter03/ODD_GuidanceChecklists_2020.pdf>)ので、S1 は教科書の系譜に属する資料と見てよい。

### 1-5. 観察の道具の型(個体カルテ・場所カルテの先行)

| 出典 | 逐語(節) | v2 への含意 |
|---|---|---|
| **MATSim User Guide**(MATSim 本の抜粋・2026-08-25 コンパイル版)<https://www.matsim.org/files/book/partOne-latest.pdf> §15.1 | "**Every action in the simulation is recorded as a MATSim event**, be it an activity start or change of network link" / "By default, **the time when the event occurred** is included." / "information like **the ID of the agent triggering the event, or the link ID where the event occurred**, could be included" / "**The events file is an important base for post-analyses, like the visualizers.**" | **1 イベント = (時刻, 体 ID, 場所 ID, 種別)**。これが**個体カルテと場所カルテの両方を生む最小行**。v2 のテープ(1 呼 = 1 行)に**エンジン側イベントの行**を足せば同じ形になる |
| 同 第 5 章(Simunto Via)§5.2 | "**Explaining to customers that all answers to their questions were contained in a huge events file was not satisfactory**; pictures or even animations made it much easier for them to understand." | **「記録がある」と「読める」は別**——Via がなぜ生まれたかの一文。**M1 の存在理由の外部裏づけ**。ただし Via は非オープンソースの商用(Simunto GmbH) |
| 同 §5.3 | "**One query is special, globally available, and not linked to a layer: querying an agent plan.**" / 続く可能なクエリ = "Select Link Analysis given a link, **Select Facility Analysis** given a facility, List Transit Lines that use a given link, or List Passengers" | **個体クエリだけがレイヤから独立した特別扱い**=個体カルテは可視化の付属物ではなく一級の機能。**場所側は Link / Facility の 2 種**(v2 でいうセルと POI) |
| 同 §5.4.2 | "**For each facility, a detailed analysis can be performed showing the number of agents arriving at, departing from, or staying at a facility over the simulated time.**" / "The numbers can be **differentiated by the type of activity** the agents perform at the facility, **by the transport mode** they arrive or depart with, **or by other arbitrary agent attributes** loaded by users" | **場所カルテの既製の型**: 到着数 / 出発数 / 滞在数 × 時刻 × (活動種別・手段・任意の個体属性)。**v2 の場所カルテの列はこれをそのまま写せる** |
| 同 §5.4.5 | "**While MATSim requires and produces a lot of disaggregated data, it is still often necessary to aggregate data** to make statements or predictions about a simulated scenario." / 集計は "rectangular or hexagonal grid, where the **cell-size can be specified by the user**" または ESRI shapefile のゾーン | **個体の記録と集計は同じ道具の別レイヤ**。**分離すべきは「保存」ではなく「見せ方」**という設計判断 |
| 同 §5.4.4 | "Via allows comparison of the link volumes of **two scenarios** visually by coloring the network with the **absolute or relative difference**" / 差は時刻依存で "**aggregated over time intervals as small as 15 minutes**" | **腕どうしの差を場所の上に描く**型。v2 の AB7(vocab / open)や D-67 の腕比較に直接当たる |
| **OpenTelemetry Docs — Sampling** <https://opentelemetry.io/docs/concepts/sampling/> | "**Sampling is one of the most effective ways to reduce the costs of observability without losing visibility.**" / "**Head sampling is a sampling technique used to make a sampling decision as early as possible.**" / "**This ensures that whole traces are sampled - no missing spans - at a consistent rate, such as 5% of all traces.**" / "**Tail sampling is where the decision to sample a trace takes place by considering all or most of the spans within the trace.**" / "you cannot ensure that **all traces with an error within them** are sampled with head sampling alone." | **抽出の 2 型がそのまま M1 に当たる**。**head = ランの開始時に「この体は全部録る」と決める**(決定論・安い・稀な事象を取り逃す)。**tail = 走り終えてから面白い体を選ぶ**(稀な事象を確実に拾う・全部を一度持つ必要がある)。**v2 はテープ再生が決定論なので、第 3 の道(録らずに、あとから選んで再生で作る)が取れる**——先行にない位置 |

### 1-6. プライバシー・公開(R-15 と重複しない 2 件)

| 出典 | 逐語 | 数値 | v2 への含意 |
|---|---|---|---|
| **de Montjoye, Hidalgo, Verleysen & Blondel (2013)** "Unique in the Crowd: The privacy bounds of human mobility", *Sci Rep* **3**:1376, doi:10.1038/srep01376(本文は PMC 版 <https://pmc.ncbi.nlm.nih.gov/articles/PMC3607247/>) | 抄録 "**four spatio-temporal points are enough to uniquely identify 95% of the individuals**" / "**the uniqueness of mobility traces decays approximately as the 1/10 power of their resolution**" / "**Hence, even coarse datasets provide little anonymity.**" / 序 "**A simply anonymized dataset does not contain name, home address, phone number or other obvious identifier.**" / "if individual's patterns are unique enough, **outside information can be used to link the data back to an individual**" | 150 万人 × 15 か月(2006-04〜2007-06)・アンテナ ≈6,500 基(1 基あたり平均 ≈2,000 人・0.15〜15 km²)・時間解像度 1 時間・ε は 2,500 本の無作為 trace のうち一意だった割合・**ε = α − (νh)^β、β = 0.157 − 0.007p**・p=4 で解像度を半分にしても特定性は 9.3% しか落ちない | **個体カルテの形(時刻 × 場所の点列)は、実データであれば 4 点で 95% が一意になる形**。合成であっても**「この粒度は実データなら公開できない粒度だ」という事実は、公開時の説明責任として先に書く**べき。粗くしても効かない(1/10 乗)ので「粒度を落として安全にする」は効かない道 |
| **Stadler, Oprisanu & Troncoso (2022)** "Synthetic Data – Anonymisation Groundhog Day", *31st USENIX Security Symposium*, Boston MA, Aug 2022, pp.1451–1468, ISBN 978-1-939133-31-1 <https://www.usenix.org/conference/usenixsecurity22/presentation/stadler>(arXiv <https://arxiv.org/abs/2011.07018>)**抄録のみ** | 抄録 "**synthetic data either does not prevent inference attacks or does not retain data utility**" / "**synthetic data does not provide a better tradeoff between privacy and utility than traditional anonymisation techniques**" / "the privacy-utility tradeoff of synthetic data publishing is **hard to predict**" | — | **「合成だから個人情報でない」は、実データから学習した生成物については文献上通らない**。**ただし我々の体は統計(国勢調査・PT・KDDI の集計)から合成した架空個体であって、実個人レコードで学習した生成モデルの出力ではない**——脅威モデルが違うので Stadler の結論をそのまま当てるのは誤り。**当たるのは「合成であることを理由に検討を省略してはいけない」という手続きの部分だけ** |

**この 2 件は R-15(OASIS 付録 I・Generative Agents §8.3・日本心理学会倫理規程・Five Safes・EU AI Act 50 条(2)・HF データセットカード・犯罪学 ABM の倫理)とは重ならない**。R-15 は「公開・論文化の制度側」、本節は「カルテという形そのものの再識別性」。

**実在の店名・地名が入る側の問題(先行未発見=§3)**: 上の 2 件はどちらも「個人の側」の議論で、**場所カルテが「実在の店 X の時間帯別来客数」として読まれる**というリスク(合成値が実在事業者の売上推定と誤読される・競合が引用する)に直接当たる先行は、今回の探索では見つからなかった。

---

## 2. M1 の設計アジェンダ候補(親推奨つき・すべて判断待ち)

> 本節は**決定ではなく候補**。CLAUDE.md §2-2 に従い、実装着手は詳細まで合意してから。
> 既決の制約 3 本を前提にする: **(a) 基本 tick = 1 分**(決定台帳「構築前の即決 8 項」A8)→ 1 シミュ日 = 1,440 tick。**(b) S1 恒久記録 ≤ 5 GB/シミュ日**(予算宣言 S1)。**(c) データ層は「個体×tick 全記録禁止」**(決定台帳「実装スタック」行)。

### 2-A. カルテの粒度

| # | 決定項 | 親推奨 | 代替(不採用理由) | 先行の根拠 |
|---|---|---|---|---|
| **O1** | **個体カルテの単位** | **1 体 × 1 シミュ日**。行 = 時刻順のイベント列で、4 系統を 1 本に併合: ①LLM 呼(既存テープ: prompt / 応答 / wake_class)②行動の確定(エンジンが受理した行動・場所 ID・結果)③状態の変化点(在圏セル・所持金・空腹等の**変化した瞬間だけ**)④繰り延べ・失敗・縮退の診断 | 全 tick の状態スナップショット(1,440 行固定)= 読むのが苦痛で、**変化点以外は再生で復元できる**ので冗長 | MATSim events(「時刻 + 体 ID + 場所 ID + 種別」が最小行)・Concordia `get_entity_timeline(name)`・ODD S1 p.23「1 体以上を選んで状態をシミュ時間に沿って記録」 |
| **O2** | **場所カルテの単位** | **1 place_id × 1 シミュ日 × 時刻ビン**。列は Via §5.4.2 を写す: **到着数 / 出発数 / 滞在数**を時刻ビンごとに、**活動種別・移動手段・任意の個体属性**で分解。ビンは **15 分**(Via の最小粒度と一致・既存の物差し M3 も 15 分ビン) | 1 分ビン = 520 × 1,440 で読み手が扱えない。60 分 = KDDI 照合には合うが店の開閉が見えない | Via §5.4.2・§5.4.4(差分は「15 分まで小さくできる」)・v2 側の既存 15 分ビン |
| **O3** | **場所カルテは全数か抽出か** | **全数(520 place_id 全部)**。理由は算術: 520 × 96 ビン × 数十列 ≈ **24 MB/シミュ日 = S1 の 0.5%**。抽出する理由が無い | 主要 5 エリアだけ = 「見た所だけ合っていた」を作る。**抽出の必要が無いのに抽出すると逸話化する** | place_id 総数 520(GL 453 / DECK 39 / UG 28・`W2.header.json`) |
| **O4** | **個体カルテは必ず抽出**(全数は不可能) | 算術を先に置く: 40 万体 × 1,440 tick = **5.76 億 体·tick/シミュ日**。1 体·tick 8 B(セル id 4 B + 状態 4 B)でも **4.6 GB = S1 予算の 92%**、16 B なら **9.2 GB = 超過**。→ **既決の「個体×tick 全記録禁止」は算術としても正しい**。個体カルテは抽出一択 | — | 上記は親が再計算できる算術(入力はすべてリポ内の既決値) |

### 2-B. 抽出規則(M1 の設計の本体)

| # | 決定項 | 親推奨 | 代替(不採用理由) | 先行の根拠 |
|---|---|---|---|---|
| **O5** | **誰のカルテを作るか** | **3 層を事前登録で宣言**: ①**無作為層**(seed から決定的に選ぶ N 体。誰も選んでいない=逸話化しない)②**層化層**(属性セル——居住地×年代×就業——ごとに 1 体。**分布の端が消えない**)③**指名層**(診断のために名指しで選ぶ体。**必ず「指名である」と記録に残す**)。**①②の比を先に固定し、③は報告時に必ず分離**する | 「面白い体を選ぶ」だけ = Generative Agents が避けた道。**§6.1 は "randomly chosen agent"** | GA §6.1(無作為 1 体の replay)・ODD S1 p.52(「1 日 1 羽を無作為に選ぶ」)・POM の weak pattern(単独では効かない) |
| **O6** | **抽出の時点(head / tail / 再生)** | **第 3 の道 = 再生で作る**を第一候補。ランの本体は既存テープ(伝記 + checkpoint)だけを書き、**個体カルテはあとからテープ再生で生成する**。v2 はテープ再生が決定論(T2-c で 4 点 × 5 ハッシュ一致)なので、**ラン中に何も足さずに、事後に誰のカルテでも作れる**。= 追加ラン 0 本・S1 予算への追加 0 バイト | **head sampling**(ラン開始時に N 体を決めて全部録る)は安いが**稀な事象を取り逃す**。**tail sampling** は全部を一度持つ必要があり O4 に反する | OpenTelemetry Sampling(head/tail の定義と限界)・第177 の親評価「テープ再生が決定論なので新ラン不要」 |
| **O7** | **再生との結線の形** | カルテ生成器は **再生の観測者(read-only)**として実装し、**エンジンに 1 バイトも書かない**。入力 = (manifest_sha256, run_index, agent_id 集合)。出力 = カルテのファイル。**同じ 3 つ組から同じバイトが出ることをテストする**(T2 系に 1 行追加) | 本番ラン中にカルテを書く = S1 を食い、性能予算に載り、既定のバイトを変える | 計器盤 G-5(seed = 決定的写像)・U8 の再現性三層・Concordia の「状態編集を UI に入れた」は**採らない道** |

### 2-C. 保存量(S1 バイト予算)

| # | 決定項 | 親推奨 | 数と根拠 |
|---|---|---|---|
| **O8** | **カルテは S1 に算入するか** | **算入しない(別枠 S4 を新設)**。理由: O6 を採ると本番ランの出力は 1 バイトも増えず、カルテは**事後生成物**。ただし**ディスクは食う**ので予算行は要る | 個体カルテ(エンジン側・全 tick・64 B/tick)= **N × 92.2 KB/シミュ日**。N=1,000 → **92 MB**、N=10,000 → **922 MB**。LLM 側は既に伝記にある(**6.94 呼/体/日 × 0.67 KB/呼 = 4.65 KB/体/日**・N=1,000 で 4.65 MB)。**個体カルテの費用はほぼ全部エンジン側の tick 列**。場所カルテ全数 ≈ **24 MB/シミュ日** |
| **O9** | **N の初期値** | **N = 1,000(無作為 600 / 層化 300 / 指名 100)**。根拠は予算でなく**読める量**: 1,000 体は人間が読み切れないが、**分布を描くには足り、端のカルテを引ける**。**これは expedient**(先行に N の根拠は無い)——感度試験で「N を 2 倍しても結論が変わらない」を示すまでは結論を駆動させない | 92 MB/シミュ日。参考: GA は **25 体 × 2 日**、Railsback & Johnson は **1 日 1 羽** |
| **O10** | **粒度の切替口** | **カルテの詳細度に段を作り、既定を軽い側に置く**(`--card-detail {slim,full}`)。`full` のみ prompt 全文と応答全文を含める | Concordia 1.8.0「HTML ログのエピソード全文は任意にし、競技環境では既定で切る」・同 CLI の「画像は既定でストリップ」 |

### 2-D. 逸話の扱いの規律

| # | 決定項 | 親推奨 | 先行の根拠 |
|---|---|---|---|
| **O11** | **カルテから出た所見の 3 段階** | **段1 観察**(カルテを読んで気づいた話。**どこにも主張として書けない**)→ **段2 測定**(同じ問いを全体に当てて数にする。分母・分子・裏取りの手続きを書く)→ **段3 事前登録**(次のランで検証する仮説として prereg に載せる)。**段2 を飛ばした段1 は devlog にしか書けない**という線を引く | GA §7.1.1〜§7.1.2 がまさにこの 3 段(物語 → 25 体全員への聞き取り → 記憶ストリームでの裏取り → 1.3%(n=6)) |
| **O12** | **逸話を使ってよい唯一の場所** | **「失敗の型の命名」だけ**。成功の証拠には使わない | GA §7.2 は逸話を 3 つの erratic behavior の命名にしか使っていない |
| **O13** | **再現できなかったものを先に書く** | 計器盤の面1・面2 に **「合わなかったアンカー」の欄を義務化**。カルテについても「探して見つからなかったもの」(例: 待ち合わせ・手伝いの成功)を同じ欄に書く | ODD 2020 Box 1 "Reporting ... only those patterns that the model could capture would resemble 'HARKing'" / "Better practice would be to report on missing patterns" |
| **O14** | **平均と分布の両方を書く** | カルテ由来の報告は必ず**中心傾向と体間のばらつきの両方**を出す。片方だけの報告を禁ずる | ODD S1 p.22「中心傾向だけを見たのか、体間のばらつきも見たのかを理解することが特に重要」+ 計器盤 G-8 の「分布で報告」(第203) |
| **O15** | **カルテはゲートにしない** | M1 の出力は**計器盤 面1(報告のみ)**に置く。**面2(holdout 判定)には一切入れない**。理由: カルテは抽出であり、抽出でゲートを作ると抽出規則が結論を決める | 計器盤 G-1「ゲート(合否)は面2 のみ」・ODD S1「Observation は実験・分析の設計ではなく収集の記述」 |
| **O16** | **計器そのものの検査** | **カルテが空でないことを毎回検査する**: (a) 生成された全カルテの行数 > 0 (b) 4 系統(LLM 呼・行動・状態変化・診断)それぞれが 0 行でない体の割合 (c) 前ランとの行数比が既定帯内。**1 つでも 0 なら赤** | Concordia 2.4.0「正規表現の壊れで HTML ログが空になっていた」・v1 の「内省空バグ」 |

### 2-E. 公開時の匿名化

| # | 決定項 | 親推奨 | 先行の根拠 |
|---|---|---|---|
| **O17** | **何を公開しうるか** | **既定は非公開**。公開するのは (a) 集計した場所カルテ (b) **少数の個体カルテを、本人属性を粗くして** の 2 つだけ。**「合成だから安全」を理由にしない** | Stadler 2022「合成データは従来の匿名化より良いトレードオフを与えない」(ただし脅威モデルが違う=§1-6 の注記)・de Montjoye「単に匿名化されたデータセットには名前も住所も電話番号も無い」 |
| **O18** | **個体カルテ公開時の粗さ** | **粗くしても効かないことを先に認める**(1/10 乗則)。したがって**粒度を落とす方向でなく、体数を落とす方向**(公開は数体)+ **属性の粗化**(居住地は区、年代は 10 歳階級)+ **「これは架空の個体であり、実在の人物の記録ではない」の明示**を組にする | de Montjoye: p=4 で解像度を半分にしても特定性は 9.3% しか落ちない・"even coarse datasets provide little anonymity" |
| **O19** | **実在の店名・地名の扱い** | **場所カルテの公開時は、実在事業者を特定できる名称を伏せる**(place_id と用途分類までにする)。理由は個人情報ではなく**誤読リスク**: 合成の来客数が実在店の実績と誤読されうる。**個体カルテ側では地名(駅・交差点)は残してよい**(公共の目印で、特定の事業者の利害に直結しない) | **先行未発見(§3)**。これは**未リサーチ(expedient)の自前判断**。ライセンス台帳・R-15(公開・論文化の制度側)と結線して再検討すべき |
| **O20** | **公開の手続き** | カルテを公開する行為を**一級の記録**にする(いつ・どの run_index の・誰のカルテを・どの粗さで出したか)。封印(manifest の開封記録)と同じ扱い | 計器盤 G-1 の k* 事前宣言・U8 の manifest・第176 の `previous_openings` 履歴化 |

### 2-F. 費用と着手順(参考)

1. **場所カルテが先**(O2・O3): 全数で 24 MB、抽出規則の議論が不要、KDDI 照合(virtual scientist 型)に直結する。
2. **次に個体カルテの生成器**(O6・O7): 既存テープ再生の観測者として実装。本番ランに触らない。
3. **読み口は CLI が先、HTML 1 枚が後**(Concordia の順序)。GUI は作らない。
4. **規律(O11〜O16)は道具より先に文書化する**。道具ができてから規律を書くと、最初の逸話が既に出ている。

---

## 3. 空欄(未確認・記憶で埋めていない)

| # | 未確認のもの | 何が言えなくなるか |
|---|---|---|
| 1 | **Grimm et al. 2005, *Science* 310(5750):987–991**(doi:10.1126/science.1116681)本文。**有料で未取得** | POM の原典の逐語。§1-4 の weak/multiple patterns は**同著者 2012 の open access 版から採った代替**。2005 の文言は持っていない |
| 2 | **Railsback & Grimm 教科書 第 9 章 "Observation"**(Princeton UP, 2nd ed.)本文。**書籍で未取得** | 教科書が「個体の物語」をどう扱えと書いているかの逐語。確認できたのは公式サイトの章要旨のみ |
| 3 | **Zurell et al. 2010** の "virtual scientist" 原典 | ODD S1 の引用経由でしか読んでいない |
| 4 | **Railsback & Johnson 2011**, *Ecol Model* 222:3305–3319 本文 | 「1 日 1 羽を無作為に選ぶ」は ODD S1 p.52 の例文としての引用。**原論文での実装と、なぜ 1 羽なのかの根拠は未読** |
| 5 | **AgentTorch の `agent_torch.Analysis` API** | 検索要約にのみ現れ、arXiv 2409.10568 v3 の HTML 本文には**存在しない**。`github.com/AgentTorch/visualize` は **2026-09-17 時点で HTTP 404**。論文 Appendix D とリポジトリ本体は未確認 |
| 6 | **AgentSociety の DB スキーマ(テーブル名)・Data Analysis ページ・V2 の「JSONL replay」の中身** | 個体記録の実際の粒度と、replay が何を指すか |
| 7 | **OASIS の DB テーブル名・`visualization/` の中身** | 個体の事後検査ができるのかどうか。付録 I は R-15 の担当 |
| 8 | **Concordia の `structured_logging.py` / `log_viewer.html` の実体**(CHEATSHEET と CHANGELOG のみ読了)。**2.4.0 のリリース日も未確認** | ログ 1 件あたりのバイト数と、画面が何を見せるか |
| 9 | **Stadler et al. 2022 本文**(抄録のみ)。特に outlier レコードに関する主張 | 「合成データのどこが漏れるか」の機構 |
| 10 | **de Montjoye 2013 の図と式の再計算**(抄録 + Results の要約のみ) | β = 0.157 − 0.007p と 1/10 乗則の導出。**数を決定に使う前に原典 PDF で再確認が要る** |
| 11 | **ゲームの replay 系の一次資料**(Unreal の DemoNetDriver / replay system 等) | 「巻き戻し + 任意時点へのシーク」の産業側の型。今回は未取得(§1-1〜1-5 は学術・交通・観測系で足りた) |
| 12 | **場所カルテが実在事業者の実績と誤読されるリスクの先行** | O19 は**未リサーチ(expedient)の自前判断**。先行が見つかっていない |

---

## 4. lit README に足す行(親が貼る)

| メモ | 分野 | 一次確認 | 何のために引くか |
|---|---|---|---|
| [agents__park2023_generative-agents-replay](lit/agents__park2023_generative-agents-replay.md) | 検証とV&V #22 / 計算社会科学 #25 | B(サブ実読・第210・親未確認) | **逸話を測定に降ろす 3 段(物語→全員への聞き取り→記憶ストリームでの裏取り)**・**453 応答の 1.3%(n=6)が幻覚**・評価は「**無作為に選んだ** 1 体の replay」 |
| [agents__concordia_structured-logging](lit/agents__concordia_structured-logging.md) | ソフトウェア工学 #29 / ABM方法論 #21 | B(サブ実読・公式ドキュメント/CHANGELOG・第210・親未確認) | **ログの粒度 = entity × step × component × key**・`get_entity_timeline(name)` が個体カルテ・**「再生」は無く checkpoint 復元**・**計器が空になる事故の実例** |
| [abm__grimm2020_odd-observation](lit/abm__grimm2020_odd-observation.md) | ABM方法論 #21 / 検証とV&V #22 | **実読(サブ・pymupdf 62 頁)・親未確認** | **個体カルテの ODD 上の定義**(S1 p.23)・**「1 日 1 羽を無作為に選び trace を出す」**(S1 p.52)・**平均だけか分布も見たかを書け**・**HARKing 禁止=合わなかったパターンも書け** |
| [abm__grimm-railsback2012_pom-multiscope](lit/abm__grimm-railsback2012_pom-multiscope.md) | ABM方法論 #21 / 科学哲学 #26 | B(サブ実読・PMC 本文・第210・親未確認) | **「1 つのパターンは間違った理由でも合う」**(equifinality)・**弱いパターンは束ねて効く**・**パターン = 却下のフィルタ**。Grimm 2005 *Science* の代替(原典は有料未読) |
| [transport__matsim-via_agent-facility-queries](lit/transport__matsim-via_agent-facility-queries.md) | 交通工学 #2 / ソフトウェア工学 #29 | **実読(サブ・pymupdf 216 頁)・親未確認** | **個体カルテ(agent plan クエリ)と場所カルテ(Select Facility Analysis)を同じイベント列から引く先行**・**場所カルテの列の型**(到着/出発/滞在 × 時刻 × 属性)・「記録がある」と「読める」は別 |
| [ethics__demontjoye2013_unicity](lit/ethics__demontjoye2013_unicity.md) | 研究倫理・情報法 #31 / 人間移動科学 #3 | B(サブ実読・PMC 本文・第210・親未確認) | **4 点で 95% が一意**・**粗化は 1/10 乗でしか効かない**=**「粒度を落として公開」は効かない道**。個体カルテ公開の線を引く唯一の数値 |

---

## 5. 親が最初に一次確認すべき 3 件

1. **ODD 補遺 S1 の Observation 節の 3 逐語**(<https://www.jasss.org/23/2/7/S1-ODD.pdf> p.22–23 と p.52)。とくに "Modelers sometimes also collect observations at the agent level, e.g., by selecting one or more agents and having them record their state over simulated time." と "The model randomly selects one bird per day and displays a trace of its movement during the day"。**§2 の O1(粒度)と O5(無作為抽出)の唯一の方法論的根拠**で、これが崩れると M1 は全部自前宣言になる。
2. **Generative Agents §7.1.1〜§7.1.2 の裏取り手続きと数**(453 応答 / 1.3% / n=6 / 4%→32% / 4%→52% / 密度 0.167→0.74)。**ar5iv 経由で読んだ**ので、arXiv の原典 PDF で再確認が要る。**§2 の O11(逸話 3 段)の唯一の定量的先行**。
3. **de Montjoye 2013 の "four spatio-temporal points ... 95%" と "1/10 power"**。**nature.com が認証にリダイレクトしたため PMC3607247 経由で読んだ**。**O18(公開時の粗さ)の線を引く唯一の数値**で、「粗くすれば公開できる」という直観を否定する側なので、間違っていると結論が反転する。
