# Lane C 答申 — 更新規則(不応期・日次内省・繰り延べ)と聴覚未確認数値

<!-- hdr:v1 -->
- **分野**: 認知科学(記憶・習慣) #12 / 環境音響学 #6 | **重要度**: P0(親判断・2026-09-15 第191)
- **一次確認**: **B** = 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) — 出典痕跡 125 件。空欄節あり
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> **親検収(Fable・2026-09-06)**: 出典を親が一次確認した。✔=親が実読して数値一致。
> - ✔ GATSim(arXiv 2506.23306v2実読): 計画再考トリガ4種・「global minimum intervals of 30 minutes for general activities and extended intervals of 150 minutes for work activities」は周期再考(reflection frequencies)に掛かる床。答申の解釈(イベント駆動には床なし)は本文と整合。
> - ✔ Lipari EDF講義資料(PDF実読): 「In case of overhead (U > 1), we can have the domino effect with EDF: it means that all tasks miss their deadlines」「FP is more predictable: only lower priority tasks miss their deadlines!」逐語一致。
> - ✔ Rindel 2019(Acoustics in Practice・PDF実読): 通話品質×SNRの表 Very bad <−9 / Insufficient (−9;−3) / Sufficient (−3;0) / Satisfactory (0;3) / Good (3;9) / Very good >9(Lazarus [6]に帰属)・「SNR = −3 dB, as a minimum requirement」逐語一致。**訂正**: この表は2019年版では**Table 2**(Table 3は発声努力とL_{SA,1m}の表: 84 dB=Shouting・90=Maximal shout)。
> - ✔ Rindel 2010(Applied Acoustics 71:1156-1161・PDF実読): Lombard勾配c=0.5-0.7 dB/dB・**L_N,A=45 dBから開始・L_S,A,1m=55 dB**・Table 1「after ISO 9921」(54 Relaxed/60 Normal/66 Raised/72 Loud/78 Very loud)・SNR区分はLazarus [8]に帰属。
> - ✔ ASHA 1988指針(実読): 「speech detection threshold … 8–9 dB weaker than the speech recognition threshold」。
> - ✔ Generative Agents 内省閾値150「in our implementation」・2-3回/日。
> - ✔ ScaleSim(arXiv 2601.21473実在・HTML実読): invocation distance定義・最大1.74×・TTFT 48-68%改善(vs HiCache)。**訂正**: 「active agent rate is around 20%」は**実験設定値**であり、プロファイル実測値ではない(sparse activationの主張自体はPiao et al. 2025のプロファイルを引用)。
> - Forssbergは空欄のまま(答申の推測=Lazarus 1986/1987が原典の可能性)。不応期の値は先例1件(GATSim)からの拡張=expedient(答申自身が宣言)。
> - 正典化: docs/research/v2-update-rules-hearing-research.md(R3-8 §6・§3聴覚暫定値の根拠)。

対象: R3-8 §6(更新規則)・§3(聴覚の暫定数値)
作成: 2026-09-06 / リサーチサブ(Opus 5) / 子サブ未起動
出力規律: 出典は正規ドメインの実読ページから短く引用。未確認は「空欄(未確認)」。推測は【推測】。

---

## 要約(10行)

1. **GATSim の 30分/150分 は「再計画の間隔」ではなく `reflect_every`(反省頻度)の**大域最小間隔**である**(実読で確認)。活動中の周期的な計画再考の床であり、計画境界・待機・日の開始は別トリガ。
2. LLM社会シムで「不応期」を明示的に持つのは調べた範囲で **GATSim のみ**。GA は時間床でなく「重要度和の閾値」、OASIS は固定3分ステップ、AgentSociety は明示なし(未確認)。
3. **GA の内省閾値=150 は実読で確認**(「a threshold (150 in our implementation)」)、頻度は「roughly two or three times a day」。ただし 150 は GA の重要度スケールと観測レートに依存する内部値で、**そのまま移植すると意味を持たない**(移植すべきは「2-3回/日」というレート)。
4. **就寝時1回への集約は mechanism 側の裏づけがある**: 系統的記憶固定は徐波睡眠中のリプレイで起こり、結果は「gist 的な抽象表現」になる(Klinzing et al. 2019)。Letta の sleep-time compute(arXiv:2504.13171)は同型のエンジニアリング先行。
5. 時刻は **固定時刻でなく個体の就寝時刻に合わせるべき**。理由は(a)夜勤者が渋谷に実在する(b)固定時刻は40万呼を一瞬に集中させる(就寝分布に沿えばピークが約1/4)(c)mechanism 整合。
6. **繰り延べに EDF を主規則として使ってはいけない**。本系は設計上つねに過負荷(需要17.4 / 予算10 = U≈1.74)で、EDF は U>1 で **domino effect**(全タスクが締切を落とす)を起こす。固定優先(クラス)は「低優先クラスだけが落ちる」= 予測可能に劣化する(Lipari 講義資料・実読)。
7. 推奨規則 = **4クラス固定優先(会話ターン > 計画境界 > 個体変化 > セル変化)+ クラス内は待ち時間による昇格(starvation-free)+ 同一体の保留起床は合流(coalescing)**。根拠の強さ=中〜高(直接の先行実測はないが、DVE の Priority Round Robin・ScaleSim の invocation distance・imprecise computation が独立に同じ形に収束)。
8. 順序の**原理的な理由**: (i)(ii)は**状態**トリガなので繰り延べても最新値で回復する(=可換・合流可能)。(iv)会話ターンは**イベント**トリガで冪等でない=繰り延べ不能。これが「破棄でなく繰り延べ」が成立する条件そのもの。
9. **ISO 9921 の SIL数表は依然として未読(有料)**。ただし **ISO 9921 が典拠とする Lazarus の「SNR→通話品質」対応表を二次資料(Rindel 2019/2010・実読)から取得**: 十分/不十分の境界は **SNR = −3 dB**、0 dB = satisfactory、< −9 dB = very bad。→ **契約書の内容理解 ΔSNR=−5 dB は Lazarus 尺度で "insufficient" 帯に入る**。−3 dB への変更を推奨。
10. **検知 ΔSNR=−12 dB は独立に裏づけが取れた**: 検知閾値は認識閾値より 8-9 dB 低い(ASHA・実読)→ −3 − 8.5 ≈ **−11.5 dB**。暫定値 −12 はほぼ的中。**「Forssberg」は両解釈(聴覚・反応時間)とも発見できず=空欄(未確認)**。ISO 9921 の数値表の実質的な原典は **Lazarus H., Appl Acoust 1986;19:439–64** と思われる。

---

## 問い1. 不応期(refractory period)の先行例

### 1-1. GATSim の 30分/150分 — 意味の確定 [実読]

出典: Qi Liu, Can Li, Wanjing Ma, *GATSim: Urban Mobility Simulation with Generative Agents*, arXiv:2506.23306 / https://arxiv.org/html/2506.23306v2

逐語(2箇所とも本文から実読):

> "The system implements activity-dependent reflection frequencies with global minimum intervals of **30 minutes** for general activities and extended intervals of **150 minutes** for work activities"

> "The **reflection frequency parameter `reflect_every`** governs the temporal granularity of plan reconsideration during ongoing activities, balancing behavioral realism with computational efficiency."

> "Plan revision opportunities occur at strategically selected moments including: 1) simulation day initiation; 2) waiting periods at network nodes such as traffic intersections or transit stops; 3) periodic intervals during ongoing activities based on reflection frequencies; and 4) natural transition points when activities conclude."

**意味の確定(ここが今回の主要な発見)**:

- 30/150分は**「起床の最小間隔」一般ではなく、上記トリガ 3)「活動中の周期的な計画再考」だけに掛かる床**である。
- トリガ 1)日の開始・2)ノードでの待機・4)活動終了 には**この床は掛からない**。つまり GATSim の設計は「**イベント駆動のトリガは無条件に通し、周期的な自発再考だけに床を置く**」。
- パラメータ名が `reflect_every` であることから、**GATSim では「反省」と「計画再考」が同一機構**。v2 が §6 で「計画境界=主」「日次内省=別」と分離しているのは GATSim より細かい設計。
- v2 への直訳の危険: v2 の (i)セル変化・(ii)個体変化 は GATSim の 2)(3チャネル知覚)に近く、GATSim は**これらに床を置いていない**。したがって「GATSim 30分」を v2 の (i)(ii) にそのまま適用するのは**先例の拡大解釈**であり expedient タグが必須。

補足: 実験規模は 70体・13ノード、population synthesis に GPT-4o、行動モデリングに Qwen3。**LLM呼び出し数・トークン・実時間の開示はなし**[実読で確認した不在]。

### 1-2. ほかの LLM エージェント社会シムの「間隔」の置き方

| システム | 「間隔」の実装 | 数値 | 確認 |
|---|---|---|---|
| **Generative Agents**(Park et al. 2023) | 時間床を置かない。計画を**再帰的に分解**する深さで粒度が決まる。反応は「should react?」プロンプトで毎観測判定 | 「broad strokes」→「**hour-long chunks**」→「**5–15 minute chunks**」 | ✔ 実読 |
| **GATSim** | `reflect_every` 大域最小間隔(活動中の周期再考のみ) | **30分**(一般)/**150分**(就業) | ✔ 実読 |
| **OASIS** | 固定ステップ幅(不応期なし) | 1ステップ = **3 シミュ分** | ✔ 既往(repo `v2-perception-timing-research.md` に実読記録) |
| **AgentSociety**(arXiv:2502.08691) | 「discrete time-stepping」は都市空間移動についてのみ言及。**エージェント起床の間隔規定は見つからず** | — | 空欄(未確認) |
| **Concordia**(DeepMind, arXiv:2312.03664) | 時間床でなく **GM による観測発行の門番**。「we do not assume that the agent responds with an action to every observation」 | — | ✔ 既往(repo に実読記録) |
| **Project Sid / PIANO**(arXiv:2411.00114) | モジュールごとに**異なる時間尺度**で並行実行(reflex=小NN、goal generation=熟考) | 数値なし | ✔ 既往(repo に実読記録) |
| UrbanLLM系 / TrafficSim系 | 今回の探索では「再計画の最小間隔」を明示した論文に到達できず | — | 空欄(未確認) |

**含意**: 「不応期」という装置を持つのは GATSim だけ。GA・Concordia は**間隔でなく判定で絞る**(should-react / GM門番)。v2 の設計は「エンジン側の変化検出で門番する」=Concordia 型の門番を**LLM でなくエンジンで**やる形で、両者のハイブリッド。**先行例が薄い=v2 の不応期は全て expedient から出発し、感度試験で「結果を駆動していない」ことを示す義務がある**。

### 1-3. 人間側の根拠

**(a) 心理学の「不応期」は分のオーダーではない** — 用語の混同に注意。

Psychological Refractory Period (PRP) は二重課題のボトルネックで、**SOA 100-200 ms で第2反応が遅れ、>500 ms では遅れない**というスケールの現象(Springer/Psychonomic Bulletin & Review 等の記述に基づく)。**つまり v2 の「不応期(分オーダー)」は心理学的不応期ではなく、純粋に計算資源の装置**。この点は台帳で mechanism を主張しないほうがよい。

- 参照: https://link.springer.com/article/10.3758/s13423-018-1498-6 (PRP のボトルネックは response selection でなく response initiation の timing だとする主張) — アブスト級の確認のみ、逐語引用は取れていない[部分確認]

**(b) 行動の持続時間(=計画境界の実測的な床) — Mark et al. CHI 2005** [実読]

出典: Gloria Mark, Victor M. Gonzalez, Justin Harris, *"No Task Left Behind? Examining the Nature of Fragmented Work"*, CHI 2005, pp.321-330 / https://ics.uci.edu/~gmark/CHI2005.pdf

逐語:

> "Our informants worked in an average of **11.7 (sd=2.4) different working spheres**."

> "we found that **57.1% of all informants' working sphere segments were interrupted**, on the average."

> "The average length of time that the informants spent in central and peripheral working spheres was **11 min. 4 sec., (sd=18 min. 9 sec.)** before switching to another working sphere or being interrupted."

> "When people did resume work on the same day, it took an average length of time of **25 min. 26 sec (sd=54 min. 48 sec.)**"

> 割り込まれた working sphere は「significantly longer (**12 min. 40 sec.**, sd=14 min. 33 sec.) than those not interrupted (**8 min. 58 sec**, sd=14 min. 43 sec.)」

**v2 への含意**:
- これは**オフィス内デスクワーク**の数値で、**都市空間の活動エピソード(買物・移動・飲食)より一桁細かい**。したがって **11分は「人間の行動持続時間の下限側の実測」**として使え、「不応期を11分より短くすると、デスクワークより細かい粒度で街を歩く人を刻むことになる」という**下限の論拠**になる。
- 逆に **上限の論拠**は GATSim の 150分(就業中)。
- **11.7 working spheres/日** は、v2 が repo で見積もっている「活動エピソード 8-14回/日」とオーダーが一致する[算出照合]。この一致は、計画境界起床が 8-14回/体/日 に収まるという見積りを補強する。

**(c) 屋外活動の持続時間** — 「買物・裁量的活動の平均滞在は 10-30分」という記述を検索要約で得たが、**指定した一次資料(PMC10149489)を実読したところ該当文は存在しなかった**(在宅活動の数値のみ: online grocery shopping 27.6 min / in-home leisure 229.94 min, Hossain et al. 2022 引用)。→ **屋外活動持続時間の一次数値は空欄(未確認)**。日本側は 総務省「社会生活基本調査」で取れるはずだが今回は未取得[未確認]。

---

## 問い2. 日次内省(reflection)

### 2-1. Generative Agents の内省トリガ — 原典確認 [実読]

出典: Park, O'Brien, Cai, Morris, Liang, Bernstein, *Generative Agents: Interactive Simulacra of Human Behavior*, arXiv:2304.03442 / https://arxiv.org/html/2304.03442v2

逐語:

> "Reflections are generated periodically; in our implementation, we generate reflections when **the sum of the importance scores for the latest events perceived by the agents exceeds a threshold (150 in our implementation)**."

> "In practice, our agents reflected **roughly two or three times a day**."

計画分解も同ページで確認:

> "The first step is to create a plan that outlines the day's agenda in broad strokes." → "recursively decomposes it to create finer-grained actions, first into **hour-long chunks** of actions." → "We then recursively decompose this again into **5–15 minute chunks**"

反応判定:

> "**Should [Agent] react to the observation, and if so, what would be an appropriate reaction?**"

**移植上の注意(重要)**: **150 という数値は GA の重要度スケール(1-10)と GA の観測レートに完全に依存する内部量**。v2 は観測レートも重要度スケールも違うので、**150 を移植するのは category error**。移植すべきは「**内省は 2-3回/日 のレートになるよう閾値を較正する**」という**レート指定**のほう。

### 2-2. 就寝時1回に集約する設計の妥当性

**(a) 生物側 — 睡眠中の系統的記憶固定** [検索要約+PubMed書誌確認・全文は未読]

Klinzing JG, Niethard N, Born J. *Mechanisms of systems memory consolidation during sleep.* **Nature Neuroscience 22: 1598–1610 (2019)**. PMID 31451802 / https://pubmed.ncbi.nlm.nih.gov/31451802/(cookie壁で本文取得不可)、https://www.nature.com/articles/s41593-019-0467-3(認証リダイレクト)

得られた記述(検索要約経由・**逐語ではない**[要一次確認]):
- 「Repeated neuronal replay of representations originating from the hippocampus during slow-wave sleep leads to a gradual transformation and integration of representations in neocortical networks」
- 3つの特徴として (i) hippocampal replay (ii) 徐波睡眠/REM の脳律動 (iii) 「qualitative transformations of memories during systems consolidation resulting in **abstracted, gist-like representations**」

**v2 への含意**: 「一日の出来事を要約して抽象化する」という内省の内容そのものが (iii) と対応する。**したがって「就寝時に1回」は計算上の都合(expedient)ではなく、mechanism として主張できる数少ない設計判断**。ただし上記は逐語未確認なので、正典化前に一次確認が要る(§6 リスト参照)。

**(b) 計算側 — sleep-time compute** [書誌確認済・本文は未読]

Kevin Lin, Charlie Snell, Yu Wang, Charles Packer, Sarah Wooders, Ion Stoica, Joseph E. Gonzalez. *Sleep-time Compute: Beyond Inference Scaling at Test-time*. **arXiv:2504.13171** (2025). https://arxiv.org/abs/2504.13171

要旨から(検索要約・**逐語未確認**): 文脈をオフラインで先に処理して有用量を先計算しておくことで、テスト時計算を **Stateful GSM-Symbolic で約5倍削減**。「Offline compute helps most when future queries are somewhat predictable from existing context.」

**v2 への含意**: v2 の日次内省は「翌日の計画・関心の下ごしらえ」であり、sleep-time compute の条件(将来のクエリが文脈から予測可能)を満たす。**つまり内省は "コスト" ではなく "翌日の呼数を減らす投資" として設計できる**。具体的には、内省の出力を翌日の共有プレフィクスに焼き込めば、翌日の計画境界起床の出力長 T1 を短くできる可能性がある【推測・要ベンチ】。

**(c) 先行実装での位置づけ**

- GATSim: 「**Daily reflection processes synthesize experiences from completed simulation days**」= 日の完了後。ただし**日内のどの時刻かは明示なし**[実読で確認した不在]。3層(immediate / daily / long-term)。
- GA: 時刻でなく重要度和で発火。2-3回/日。

### 2-3. 時刻は固定か個体の就寝時刻か

**推奨=個体の就寝時刻**。根拠3点:

1. **負荷平準化(定量)**: 40万体 × 1回 = **40万呼 = 予算400万呼の 10%**。これを固定時刻に集中させると、その1シミュ時間に 40万呼/h。均等分散なら 16,667呼/h なので **24倍のスパイク**。就寝時刻分布(22:00–02:00 の4時間帯に大半)に沿わせれば約 10万呼/h = **6倍**まで下がる。固定1時刻に対して**ピークが約1/4**[算出・分布は【推測】]。W1(壁時計≤24h/シミュ日)は平均でなくピークで壊れるので、これは実利がある。
2. **現実整合**: 渋谷は夜勤・深夜営業従事者が実在する(R2-1 で営業時間データを台帳化済み)。固定 03:00 内省は夜勤者を**勤務中に内省させる**=歪みが観測可能な形で出る。
3. **mechanism 整合**: 固定は「その個体の睡眠」と無関係になるので (a) の記憶固定の根拠を失う。就寝時刻連動なら mechanism タグを主張できる。

**代替案(B案)**: 固定時刻 + 個体IDハッシュによる jitter(例: 内省時刻 = 26:00 + hash(agent_id) mod 240分)。実装が単純でピークも潰せるが、夜勤者の扱いが不自然になり mechanism 主張ができない。**採るなら「就寝状態フラグが立っていない個体は翌日に繰り延べ」という例外を必ず付ける**。

**追加トリガ(推奨)**: GA 型の重要度和トリガを **上限1回/日** で併設する。「今日は事件を目撃した」ような日に就寝まで待たせない。ただし全体の 5% 以下の個体しか発火しないよう閾値を較正(+2万呼 = 予算の0.5%)。GA の「2-3回/日」に対して v2 は「1回 + 稀に+1回」= **1.05回/日**まで削るが、これは予算(内省だけで 2-3回/日 = 80-120万呼 = 予算の 20-30%)から来る expedient であり、**削減の影響は ablation 対象**にすべき。

---

## 問い3. 繰り延べの優先規則

### 3-1. 先行例

**(a) EVE Online — Time Dilation (TiDi)** [二次資料実読]

出典: EVE University Wiki, *Time dilation*, https://wiki.eveuniversity.org/Time_dilation

> "Time Dilation (sometimes TiDi, pronounced 'tie-die'), is a game mechanic which is used to make large fleet fights in EVE more possible."

> "**The maximum time dilation speed is 10%**, making one second in game become ten seconds in real time."

(公式ニュース記事 eveonline.com/news/view/introducing-time-dilation は現在 404 = **公式一次資料は空欄(未確認)**。EVE University Wiki はコミュニティ運営の二次資料。)

**性質**: TiDi は**優先順位づけではなく、時間そのものを引き延ばす**手法(全員一律に遅くする)。優先規則の記述は Wiki にはなし[実読で確認した不在]。

**v2 への含意**: TiDi の思想は「**捨てずに遅らせる**」で v2 のアービタと同じ。ただし **v2 は TiDi と違い一律に遅らせられない**——シミュレーション時刻は現実の1日に固定されている(W1)。したがって v2 が採るのは「時間方向のLOD」= **一律でなく選択的な TiDi**。この差は設計書に書く価値がある。

**(b) 分散仮想環境の Interest Management / 更新スケジューリング** [検索要約級]

- Liu & Theodoropoulos, *Interest Management for Distributed Virtual Environments: A Survey*, ACM Computing Surveys 46(4), 2014. https://dl.acm.org/doi/10.1145/2535417 — アブストのみ確認。「data-filtering technique designed to reduce bandwidth consumption」「interest matching」。
- *Update schedules for improving consistency in multi-server distributed virtual environments*, J. Network and Computer Applications (2014). https://www.sciencedirect.com/science/article/abs/pii/S1084804514000083 — **本文403で未読**。検索要約から: 「**Priority Round Robin scheduling (PRR) enforces priorities while retaining output sensitivity and starvation-free performance**, with priorities set by a user-defined error metric such as visual error.」[**逐語未確認**]
- aura-nimbus モデル: 「entity state information which may influence an entity should be made available to that entity」[検索要約級]

**v2 への含意**: **starvation-free** が明示的な設計要件として扱われている点が重要。単純な固定優先は低優先クラスを永久に飢えさせる。**PRR = 優先つきラウンドロビン**が、v2 のアービタが採るべき形の既存名。

**(c) リアルタイムスケジューリング — EDF は使ってはいけない** [実読]

出典: Giuseppe Lipari, *EDF Scheduling* 講義資料(Scuola Superiore Sant'Anna / RETIS Lab), https://retis.santannapisa.it/~lipari/courses/str12/16.edf-handout.pdf

逐語:

> "**Domino effect** — In case of overhead (U > 1), we can have the domino effect with EDF: it means that **all tasks miss their deadlines**."

> "**FP is more predictable: only lower priority tasks miss their deadlines!** In the previous example, if we use FP: … while τ1 and τ2 never miss their deadlines, τ3 misses a lot of deadline, and τ4 does not execute! However, it may happen that some task never executes in case of high overload, while EDF is more fair (all tasks are treated in the same way)."

> "EDF is an optimal algorithm for single processors."(=**U ≤ 1 のときに限り最適**)

**v2 への含意(今回いちばん実務的な発見)**: v2 は **設計上つねに U ≈ 17.4/10 = 1.74 の恒常過負荷**で動く。これは EDF が最適性を失い domino effect に入る領域そのもの。**したがってアービタの主規則は EDF ではなく固定優先(クラス)でなければならない**。「EDF のほうが公平だが、過負荷では全員が落ちる」「FP は不公平だが、落ちるのは低優先クラスだけ」——v2 が欲しいのは後者(会話が壊れないこと)。

**(d) Imprecise computation(粗い結果で締切を守る)** [検索要約級・一次未読]

Liu, Lin, Shih, Yu, Chung, Zhao, *Algorithms for Scheduling Imprecise Computations*, IEEE Computer (1991). https://ieeexplore.ieee.org/document/76287/(本文未読)

検索要約から: 「The imprecise computation technique prevents timing faults and achieves **graceful degradation** by giving the user an **approximate result of acceptable quality** whenever the system cannot produce the exact result in time.」[**逐語未確認**]

**v2 への含意**: 繰り延べ(時間方向)以外に **品質方向の劣化**という第3の軸がある——同じ起床を「小モデル/短い出力/観測ブロックを削る」で処理する。v2 はすでに δ_perc・T1上限・大小モデル併用を持っているので、**アービタは (a) 繰り延べ (b) 縮退実行 の2択を持つべき**。これは「破棄でなく繰り延べ」の宣言を弱めずに予算を追加で稼げる。

**(e) 群衆シム/ゲームAI の LOD** [検索要約級]

- 「agents closer to the camera are updated with higher frequency, while farther away and occluded agents are given lower priority」[検索要約級・一次未読]
- 「the decision-making cycle for distant or irrelevant agents can be simplified or run at a **lower frequency**, a concept known as time management or **simulation LOD**」[検索要約級・一次未読]

**v2 への含意**: ゲームの LOD 基準は「カメラからの距離」。**v2 にはカメラがない**——観測者は存在しない。したがって LOD 基準を**そのまま輸入できない**。v2 の等価物は「**その体の起床が他の体の観測に影響する度合い**」であるべき(混雑セルの中心にいる体 > dormant な体)。これは設計書に書くべき非自明な差。

**(f) LLM エージェント系の先行 — ScaleSim** [実読・v2 に最も近い]

出典: Pan et al. (2026), *ScaleSim: Serving Large-Scale Multi-Agent Simulation with Invocation Distance-Based Memory Management*, arXiv:2601.21473 / https://arxiv.org/html/2601.21473

実読で得た点:
- **sparse agent activation**: 「only a small fraction of agents are activated during each simulation step」。プロファイルで **約20% のアクティブ率**、常駐エージェントは全体の 25%(H100 で最大125体)に制限。
- **invocation distance** の定義: 「the temporal gap between an agent's current state and its next expected LLM invocation」。「it does not necessarily represent an exact timestamp or number of steps; rather, it serves as a **relative measure**」。算出は 独立シミュ=行動の残時間 / 相互作用あり= D = min(D_action, D_interaction)、D_interaction は「Physical Distance/Velocity」。
- **future reuse-aware eviction**: メモリ不足時に **invocation distance が大きい**エージェントのメモリから退避。
- 効果: SGLang比 **最大1.74×**、高並行時に TTFT **48-68%改善**。

**v2 への含意(重要)**:
1. **v2 の疎性は ScaleSim より一段深い**。ScaleSim のプロファイルは 20%/ステップ。v2 は 400万呼/日 ÷ 40万体 = 10呼/体/日。1ステップ=10シミュ分とすれば1日144ステップ → 27,778呼/ステップ = **全体の 6.9%/ステップ**[算出]。**つまり v2 は既知の LLM 社会シムの約1/3の活性率で回す設計**。これは新規性の主張にも、実現性の懸念にもなる。
2. **invocation distance は v2 の「次の計画境界までの残時間」とほぼ同一概念**。ScaleSim はこれを**KVキャッシュの退避優先度**に使っているが、v2 は同じ量を**起床の繰り延べ優先度**に使える。**同じ1つの量を三役(繰り延べ順序・KV退避・プリフェッチ)で使えるのは実装上大きい**。

**(g) AI Metropolis** [アブスト級]

Zhiqiang Xie, Hao Kang, Ying Sheng, Tushar Krishna, Kayvon Fatahalian, Christos Kozyrakis (2024), arXiv:2411.03519. https://arxiv.org/abs/2411.03519
> "By dynamically tracking real dependencies between agents, AI Metropolis minimizes false dependencies, enhancing parallelism and enabling efficient hardware utilization."
速度向上 1.3×–4.15×。

**v2 への含意**: **繰り延べの正しさの条件は「依存関係を壊さないこと」**。会話は真の依存(相手が待つ)、セル変化は偽の依存(実は独立)。AI Metropolis の「false dependency の除去」は、v2 の優先クラス分けの**正しさの根拠**を与える: (i)(ii) を繰り延べても他体との依存を壊さない、(iv) は壊す。

### 3-2. 推奨規則(1案)

```
優先度 = (クラス, 昇格済みか, クラス内スコア)

クラス(高い順・固定優先):
  C1  会話ターン           — 繰り延べ不能(イベント・非冪等・相手がブロックされる)
  C2  計画境界             — 繰り延べると体が物理的に固まる(他体から観測可能な異常)
  C3  個体ブロック変化     — 状態トリガ・合流可能
  C4  セル動的ブロック変化 — 状態トリガ・合流可能・最新ハッシュが旧ハッシュを上書き

クラス内: urgency = 待ち時間 / クラス許容遅延  の降順(=待ちの長いものから)
飢餓ガード: 待ち時間 > T_max(クラス別) の起床は 1段上のクラスへ昇格
合流(coalescing): 同一体に複数の保留起床がある場合、1回の呼び出しに合流する
               (最新の状態を読むので情報は失われない)
縮退実行: 予算がなお足りない場合、C3/C4 は「小モデル+T1短縮+観測ブロック削減」で実行
```

**クラス別の許容遅延と T_max の初期値(いずれも expedient・較正対象)**:

| クラス | 許容遅延 | T_max(昇格) | 根拠 |
|---|---|---|---|
| C1 会話ターン | 0(即時) | — | 会話の定義。GA/GATSim とも会話に床なし |
| C2 計画境界 | 5 シミュ分 | 15分 | 「次に何をするか決まっていない体」が街に立ち尽くす時間の許容上限【推測】 |
| C3 個体変化 | 15 シミュ分 | 60分 | Mark 2005 の作業球体 11分 を目安に上側に取る |
| C4 セル変化 | 60 シミュ分 | 240分 | GATSim 一般床30分の 2倍(予算由来の緩和) |

**根拠の強さ**: **中〜高**。
- 強い部分: 「EDF でなく固定優先」= Lipari 実読の domino effect が直接の根拠(強)。「starvation-free が要件」= DVE の PRR が名前つきで存在(中)。「(i)(ii)は状態で(iv)はイベント」という順序の原理は AI Metropolis の真依存/偽依存と同型(中)。
- 弱い部分: **クラス内の具体値(5/15/60/240分)は先行実測ゼロ=完全に expedient**。感度試験(±50%)の対象。
- **直接の先行実測は存在しない**: 「LLM社会シムで予算超過時の起床優先規則を実測比較した論文」は今回の探索範囲で発見できず[空欄(未確認)]。これは v2 の寄与になりうる。

### 3-3. 代替案(1案)

**B案: 単一スカラースコア(dynamic value density 型)**

```
score = importance(起床理由) × (1 + 待ち時間/τ) / 予想コスト
```
クラス分けをやめ、連続量1本で順序づける。長所: 較正が1本のスコア関数に集約でき、学習で最適化できる。短所: (1) 過負荷時に会話ターンが原理的に飢えうる(重み次第)= 上の domino 回避の保証が消える、(2) 「なぜこの体が遅れたか」の説明が不能になり、パターン台帳の照合が難しくなる。

**採用判断**: A案(クラス固定優先)を初期値、B案は Phase 3 以降の ablation 枠。**理由: 説明可能性が v2 の第一目標(世界そのものがプロダクト・歪む場所の宣言)に直結するため。**

---

## 問い4. 聴覚の未確認数値

### 4-1. ISO 9921 の SIL 数表 — 依然として未読、ただし典拠側から回収した

**規格本文の数表は今回も取得できなかった**(有料・プレビュー12ページに Annex 含まれず)。既往の repo 記録(`v2-hearing-numbers-and-d1-coverage.md`)と同じ状況。**規格本文の条番号は本答申では一切使用しない。**

**代わりに、ISO 9921 が典拠としている Lazarus の対応表を、査読済み二次資料から実読で回収した。**

### 4-2. SNR → 通話品質 の対応表 [実読・二次資料]

出典A: J.H. Rindel, *Restaurant acoustics – Verbal communication in eating establishments*, **Acoustics in Practice, Vol.7, 2019, No.1**(European Acoustics Association), https://euracoustics.org/documents/8/01_Restaurant_acoustics.pdf

**Table 3. Quality of verbal communication, dependent on the signal-to-noise ratio. Adapted from Lazarus [6] Table 2.** [逐語・表を実読]

| Quality of verbal communication | SNR dB |
|---|---|
| Very bad | < −9 |
| Insufficient | (−9; −3) |
| Sufficient | (−3; 0) |
| Satisfactory | (0; 3) |
| Good | (3; 9) |
| Very good | > 9 |

本文からの逐語:

> "For the evaluation of the acoustics, we can apply the quality of verbal communication, which is related to SNR, see Lazarus [6]. Thus a SNR between 3 dB and 9 dB is characterized as "good", the range between 0 dB and 3 dB is "satisfactory", and **SNR below −3 dB is "insufficient"**, see Table 3. **It is suggested to focus on the border between sufficient and insufficient, i.e. SNR = −3 dB, as a minimum requirement** for acoustical design of restaurants."

> "These considerations may be valid for normal hearing people. However, **ISO 9921 [4, Section 5.1] states that "people with a slight hearing disorder (in general the elderly) or non-native listeners require a higher signal-to-noise ratio (approximately 3 dB)"**. This improvement is relative to that required for normal-hearing listeners, and thus for this group of people a SNR ≥ 0 dB should be applied to represent "sufficient" conditions, and SNR ≥ 3 dB to represent "satisfactory" conditions."

(※ この一文は Rindel が ISO 9921 を引用した**二次引用**。条番号は Rindel が付したもので、本答申としては条番号を採用しない。数値「+3 dB」だけを使う。)

出典B(同じ表の別版・独立確認): J.H. Rindel, *Verbal communication and noise in eating establishments*, **Applied Acoustics 71 (2010) 1156–1161**, https://odeon.dk/pdf/A21-ApplAc%202010%20Rindel.pdf

**Table 5** を実読(SNR 列は PDF テキスト抽出で負号が落ちるが、LN,A と LS,A,1m の差から復元・算出照合済):

| Quality | SNR (dB) | L_N,A (dB) | L_S,A,1m (dB) | Vocal effort |
|---|---|---|---|---|
| Insufficient | −9 | 83 | 74 | Loud |
| Insufficient | −6 | 77 | 71 | Raised |
| Sufficient | −3 | 71 | 68 | Raised |
| Satisfactory | 0 | 65 | 65 | Normal |
| Good | +3 | 59 | 62 | Normal |
| Good | +6 | 53 | 59 | Relaxed |
| Very good | +9 | 47 | 56 | Relaxed |

(検算: 74−83=−9 / 71−77=−6 / 68−71=−3 / 65−65=0 / 62−59=+3 / 59−53=+6 / 56−47=+9。**7行すべて整合**。)

**ここでの SNR の定義(逐語)**: "define the signal-to-noise ratio as **the level difference between the direct sound from a speaking person in a distance of 1 m** and the ambient noise in the room"。**= v2 の r 導出式で r=1 m を代入したときの量と一致する**。適用範囲は「a range of the speech levels between 55 dB and 75 dB, or a range of SNR between −10 dB and +10 dB」。

### 4-3. 発声努力と Lombard [実読]

Rindel 2010 **Table 1「Description of vocal effort at various speech levels, after ISO 9921 [2]」**(二次引用):
L_S,A,1m = 54 Relaxed / 60 Normal / 66 Raised / 72 Loud / 78 Very loud

Rindel 2019 **Table 2「Adapted from Lazarus [5] Table 3」**(より細かい):
36 Whispering / 42 Soft / 48 Relaxed / 54 Relaxed,normal / 60 Normal,raised / 66 Raised / 72 Loud / 78 Very loud

> "By shouting, the SPL can reach **84 dB to 90 dB**, and in private communication (whispering or soft speech) typical levels are 35 dB to 50 dB."

Lombard(逐語):
> "The Lombard effect **starts at a noise level around 45 dB and a speech level of 55 dB**. … Assuming a linear relationship for noise levels above 45 dB, the speech level in a distance of 1 m can be expressed in the equation: **L_S,A,1m = 55 + c(L_N,A − 45), (dB)**"
> Lombard slope: "he found that the Lombard slope could vary in the range **c = 0.5–0.7 dB/dB**"(Lazarus のレビューによる)。Rindel の実測較正では **c = 0.5 dB/dB** に固定するのが最良。

→ **repo の既存値(Lombard 勾配 0.5-0.7、実装 0.5)は本答申でも独立に再確認**。加えて **「L_amb < 45 dB では Lombard が起きない(勾配 0)」という折れ点**が明示的に取れた——v2 の Lombard 不動点 LUT はこの折れ点を持つべき。

### 4-4. 会話距離 [実読]

Rindel 2019 逐語:
> "The quality of communication can be improved if the listener can come closer to the speaking person. **Reducing the distance from 1 m to 0.7 m means a 3 dB better SNR, and coming as close as 0.5 m yields another 3 dB improvement.** This is the obvious solution for maintaining communication in a too noisy environment, but it does not change the noise level"

既往(repo)の Brungart et al. 2020 実測「The average distance between participants … was approximately 1 m」「the SNR decreased by 0.44 dB for every 1 dB increase in ambient noise level above 60 dB」と合わせると:
**理論上は距離を詰めれば救えるが、実測では人は詰めない(≈1 m で不変)** → **v2 は「騒音で会話半径が縮む」を素直に実装してよい**(会話相手との距離適応を入れない、が現実に近い)。この2本は互いに独立で、同じ結論を支持する。

### 4-5. 「Forssberg」 — 空欄(未確認)

両方の解釈で探索したが**発見できなかった**:
- (a) 聴覚/歩行者の会話距離: "Forssberg pedestrian conversation distance traffic noise" 等で該当なし。
- (b) 反応時間(repo `v2-perception-contract.md` L122 の「反応時間一次資料(Green本文・Forssberg数表は要確認)」の文脈): "Forssberg reaction time norms" でも該当なし。

**【推測】親が想定していたのは Lazarus H. である可能性が高い。** 理由: 本答申で回収した表の実質的な原典が **Lazarus H., "Prediction of verbal communication in noise – a review: part 1", Applied Acoustics 1986;19:439–64** であり(Rindel 2010 参考文献[1]・2019 参考文献[5][6] として実読)、ISO 9921 の発声努力表・SNR-品質表はこの系列に遡る。さらに Part 2 として "Prediction of verbal communication in noise—A development of **generalized SIL curves and the quality of communication (Part 2)**", Applied Acoustics 1987(ScienceDirect に書誌あり・本文未読)が存在し、**まさに「SIL 曲線と通話品質」を主題としている**。→ **未確認だが、Lazarus 1986/1987 を親の一次確認リストに載せることを推奨**。

### 4-6. 検知閾値 −12 dB の裏づけ [実読]

出典: ASHA (American Speech-Language-Hearing Association), *Determining Threshold Level for Speech* (Guidelines), https://www.asha.org/policy/gl1988-00008/

逐語:
> "The **speech recognition threshold** is the minimum hearing level for speech at which an individual can recognize 50% of the speech material."
> "The **speech detection threshold** is the minimum hearing level for speech at which an individual can just discern the presence of a speech material 50% of the time."
> SDT "should also be obtained at levels **8–9 dB weaker than the speech recognition threshold**."

**導出【推測】**: Lazarus 尺度の「内容が届く」境界を −3 dB とすると、検知はその 8-9 dB 下 = **−11〜−12 dB**。**契約書の暫定値「検知 ≈ −12 dB」はこの導出とほぼ一致する。**
**注意**: ASHA の 8-9 dB は**静穏下の hearing level 差**であって騒音下の SNR 差ではない。SNR 軸への外挿は【推測】。ただし独立に、正常聴力者の騒音下 SRT の参照値として **SNR ≈ −8.14 dB** という報告がある(PMC9442123 の検索要約級・逐語未確認)ので、−3(品質判定)と −8〜−12(50%認識/検知)は矛盾しない層をなす。

---

## 問い5. 推奨

### 5-(a) 不応期の初期値(起床条件別)

**A案(推奨)** — 「イベント駆動は無条件に通し、状態駆動に床を置く」= GATSim の設計原則の踏襲。

| # | 起床条件 | 不応期 初期値 | 根拠 | タグ |
|---|---|---|---|---|
| 1 | **(iv) 会話ターン** | **0**(床を置かない) | 会話は同期的相互作用。GA/GATSim とも会話に間隔床なし[実読] | **mechanism**(会話の定義) |
| 2 | (iii) 計画境界: 睡眠中 | 起床まで(実質 ≥360分) | 睡眠中は起床させない。内省1回のみ | **mechanism** |
| 3 | (iii) 計画境界: 就業/就学中 | **150分** | GATSim `reflect_every` 就業値[実読] | expedient(先例1件) |
| 4 | (iii) 計画境界: 一般活動 | **60分** | GATSim 30分[実読] の2倍に緩和(予算由来)。下限側の実測は Mark 2005 の 11分4秒[実読] | expedient(緩和は予算由来) |
| 5 | (iii) 計画境界: 移動・待機中 | **15分** | GATSim はノード待機を明示トリガ化(床なし)[実読]。v2 は駅待ち/信号待ちが多いので床を置く | expedient |
| 6 | (ii) 内受容閾値(空腹・疲労) | **45分** | 閾値通過は本来単調・再通過は稀。閾値ヒステリシスで代替可能なら不応期は不要になる | expedient(**ヒステリシス実装で置換を試す**) |
| 7 | (ii) 知人出現 | **10分**(同一相手には60分) | 同じ知人を10分ごとに「発見」しない、を保証 | expedient |
| 8 | (ii) 近接入替 | **15分** | **最大の暴発源**(混雑セルでは毎秒入れ替わる)。感度試験の第一候補 | expedient(**±50%試験必須**) |
| 9 | (ii) 被注視 | **5分** | 稀かつ社会的に強い信号なので床は短く | expedient |
| 10 | (ii) 傍受 | **5分**(同一話者には30分) | 既に3段ゲート済みで希少 | expedient |
| 11 | **(i) セル動的ブロック変化** | **30分** | 最も可換(状態トリガ・最新ハッシュが旧を上書き)。GATSim 一般床と同値 | expedient |

**運用規定(3点・設計書に書くべき)**:
- **不応期で抑止された起床は「破棄」ではない**。状態トリガ(1,6-11)は次回起床時に**最新状態を読む**ので情報は失われない。**イベントトリガ(会話ターン)にだけ不応期を置かない**のはこの理由。
- 不応期は **体×条件ごと**のタイマー。同一体の複数条件が同時に明けたら **1回の呼び出しに合流**する。
- **不応期だけでは予算に収まらない**。上表の床から出る最悪ケースは 40-60呼/体/日 級[算出・960分/床で概算]。**不応期は「暴発の上限を与える」装置であり、平均を10呼/体/日に合わせるのはアービタの仕事**。この役割分担を明記する。

**B案(代替)** — 全条件一律 30分(GATSim 一般値をそのまま採用)+ 会話のみ 0。長所: パラメータ1個で説明が簡単・先例に忠実。短所: 近接入替(#8)が過小に抑えられ会話成立の機会を潰す一方、被注視(#9)は過剰に抑えられて U18(犯罪創発)の入口が塞がる。**先例忠実性と現象の粒度がトレードオフになる典型例**。

### 5-(b) 日次内省の時刻ルール

**A案(推奨)**: **個体の就寝イベントに同期して1回**。
- 発火 = その体の睡眠状態への遷移時(± 個体ID ハッシュによる 0-30分のジッタ)。
- 大モデル・出力は「gist 化された要約」(Klinzing 2019 の (iii) と対応)。
- **追加トリガ**: 当日の重要度和が上位パーセンタイルを超えた個体のみ、就寝を待たず即時内省(**上限1回/日・全体の 5% 以下になるよう閾値較正**)。GA の「2-3回/日」は予算(20-30%)により採らず、**1.05回/日 に削ることを ablation 対象として宣言**。
- 予算: 40万 + 2万 ≈ **42万呼/日 = 予算の 10.5%**。
- **sleep-time compute として設計する**: 内省出力を翌日の共有プレフィクスに焼き、翌日の計画境界起床の出力長を短縮できるか**ベンチで測る**(できれば内省はコストでなく投資になる)。

**B案(代替)**: 固定時刻 + ID ハッシュ jitter(例 26:00 + hash mod 240分)。実装最小。ただし夜勤者に対して「勤務中に内省する」歪みが出る。採るなら「睡眠フラグが立っていない体は翌日繰り延べ」の例外必須。

### 5-(c) 繰り延べ優先規則

**A案(推奨・再掲)**: 4クラス固定優先 + クラス内は待ち時間/許容遅延の降順 + T_max 超過で1段昇格(starvation-free) + 同一体の保留起床は合流 + なお不足なら C3/C4 を縮退実行(小モデル・T1短縮・観測ブロック削減)。

**根拠の強さの内訳**:
- 「EDF を主規則にしない」= **強**(Lipari 実読の domino effect + U≈1.74 という自明な過負荷条件)
- 「starvation-free を要件にする」= **中**(DVE の PRR が名前つきで存在。ただし逐語未確認)
- 「会話ターン最優先」= **中〜強**(AI Metropolis の真依存/偽依存の区別と同型・原理的)
- 「クラス内の具体値」= **弱**(先行実測ゼロ・完全 expedient・感度試験必須)

**B案(代替)**: 単一スカラー score = importance × (1 + wait/τ) / cost の降順(dynamic value density 型)。学習可能だが説明可能性を失い、会話ターンの飢餓を保証できない。**Phase 3 の ablation 枠に置く。**

**共通の追加提案(強く推奨)**: **ScaleSim の invocation distance を v2 でも1つの量として定義し、三役で使う** — (1) 繰り延べ順序のクラス内スコア、(2) KV キャッシュの退避優先度、(3) プリフェッチの先読み順。ScaleSim は (2)(3) で 1.74× / TTFT 48-68%改善を出している[実読]。v2 は「次の計画境界までの残時間」を既に持っているので追加コストがほぼゼロ。

### 5-(d) 聴覚の推奨値(問い4の帰結・契約書 §3 の修正案)

| 量 | 現行(暫定) | **推奨** | 根拠 | タグ |
|---|---|---|---|---|
| ΔSNR 内容理解 | −5 dB | **−3 dB** | Lazarus 尺度の sufficient/insufficient 境界。Rindel が「設計の最低要件」として名指ししている値[実読] | **mechanism 寄り**(公表尺度の境界値) |
| ΔSNR 存在検知 | −12 dB | **−12 dB(据置)** | −3 −(8〜9)= −11〜−12(ASHA 実読からの導出)【外挿は推測】 | expedient(導出は妥当) |
| 高齢者・非母語話者の補正 | なし | **+3 dB**(= 内容理解を 0 dB に) | ISO 9921 を Rindel が二次引用[実読] | mechanism |
| Lombard 折れ点 | なし | **L_amb < 45 dB で勾配 0** | Rindel 2019 逐語[実読] | **mechanism** |
| Lombard 勾配 c | 0.5-0.7(実装0.5) | **据置** | Lazarus レビュー範囲・Rindel の実測較正[実読] | 据置 |

**−5 → −3 の含意(定量)**: 半径式 r = 10^((L_src − L_amb − ΔSNR)/N)、N=20 なら **半径が 10^(−2/20) = 0.79倍**(−21%)、N=15 なら 0.74倍。**会話成立の機会が 2割強減る**。傍受チャネルにも同じ縮小が掛かる。これは無視できないので、**ΔSNR は感度試験の必須項目(既に ablation 予約済み)**。

---

## 問い6. 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 引用文 | 確認すべき数値・観点 |
|---|---|---|---|---|
| **1** | GATSim の 30分/150分は **`reflect_every`(活動中の周期再考)だけに掛かる床**であり、計画境界・待機・日の開始には掛からない | https://arxiv.org/html/2506.23306v2 | "global minimum intervals of 30 minutes for general activities and extended intervals of 150 minutes for work activities" / "Plan revision opportunities occur at strategically selected moments including: 1) simulation day initiation; 2) waiting periods at network nodes …; 3) periodic intervals during ongoing activities based on reflection frequencies; and 4) natural transition points when activities conclude." | **床が4トリガのうち 3) にしか掛かっていないこと**。ここを取り違えると v2 の (i)(ii) に先例を誤って援用する。あわせて `reflect_every` の記述の存在 |
| **2** | Lazarus/ISO 9921 系の **SNR→通話品質**: sufficient/insufficient の境界は **−3 dB**、0 dB=satisfactory。→ 契約書の内容理解 ΔSNR=−5 dB は "insufficient" 帯 | https://euracoustics.org/documents/8/01_Restaurant_acoustics.pdf (Rindel, Acoustics in Practice Vol.7, 2019, No.1) — **Table 3** | "SNR below −3 dB is 'insufficient'" / "It is suggested to focus on the border between sufficient and insufficient, i.e. SNR = −3 dB, as a minimum requirement" / Table 3: Very bad <−9 / Insufficient (−9;−3) / Sufficient (−3;0) / Satisfactory (0;3) / Good (3;9) / Very good >9 | **表の6区分と境界値**。および Rindel 2010 Applied Acoustics 71:1156-1161 の **Table 5** で L_N,A と L_S,A,1m の差が SNR 列と一致すること(7行検算済)。**これは二次資料であり ISO 9921 本文ではない**ことの確認 |
| **3** | 恒常過負荷(U≈1.74)では **EDF が domino effect を起こす**ので、アービタの主規則は固定優先でなければならない | https://retis.santannapisa.it/~lipari/courses/str12/16.edf-handout.pdf | "In case of overhead (U > 1), we can have the domino effect with EDF: it means that all tasks miss their deadlines." / "FP is more predictable: only lower priority tasks miss their deadlines!" | **U>1 という条件つきであること**。EDF は U≤1 で最適。v2 の U = 17.4/10 = 1.74 という自前算出が正しいか(需要試算17.4の再確認) |
| **4** | GA の内省閾値 **150** と頻度 **2-3回/日** は原典どおり。ただし 150 は GA 内部スケール依存で移植不可 | https://arxiv.org/html/2304.03442v2 | "we generate reflections when the sum of the importance scores for the latest events perceived by the agents exceeds a threshold (150 in our implementation)" / "our agents reflected roughly two or three times a day" | **150 が "in our implementation" と限定されていること**(=普遍定数ではない)。および計画分解の "hour-long chunks" → "5–15 minute chunks" |
| **5** | ScaleSim の **sparse agent activation ≈20%/ステップ**と **invocation distance**。→ v2 の 6.9%/ステップは既知系の約1/3 | https://arxiv.org/html/2601.21473 (Pan et al. 2026, arXiv:2601.21473) | "only a small fraction of agents are activated during each simulation step" / invocation distance = "the temporal gap between an agent's current state and its next expected LLM invocation" / 最大 **1.74×** 高速化・TTFT **48-68%** 改善 | **20% という数値がプロファイル実測かどうか**(私は WebFetch 要約経由で得ており逐語ページを特定していない)。および 25%/125体の常駐上限。**arXiv ID 2601.21473 の実在**(2026年1月・新しいので要確認) |

**追加(6件目・§4の穴)**: **Lazarus H., Applied Acoustics 1986;19:439–64(Part 1)および 1987(Part 2 "generalized SIL curves and the quality of communication")** の一次確認。これが取れれば ISO 9921 数表を買わずに聴覚の数値を mechanism 化できる。Part 2 書誌: https://www.sciencedirect.com/science/article/abs/pii/0003682X87900624 [本文未読]

---

## 参照一覧

| # | 著者・年・出典 | URL | 確認 |
|---|---|---|---|
| R1 | Liu Q., Li C., Ma W. (2025/2026) *GATSim: Urban Mobility Simulation with Generative Agents*, arXiv:2506.23306 | https://arxiv.org/html/2506.23306v2 | ✔ 実読(2回・再計画トリガ/reflect_every/daily reflection) |
| R2 | Park J.S. et al. (2023) *Generative Agents: Interactive Simulacra of Human Behavior*, arXiv:2304.03442 | https://arxiv.org/html/2304.03442v2 | ✔ 実読(閾値150・2-3回/日・5-15分分解・should react) |
| R3 | Mark G., Gonzalez V.M., Harris J. (2005) *No Task Left Behind? Examining the Nature of Fragmented Work*, CHI 2005 | https://ics.uci.edu/~gmark/CHI2005.pdf | ✔ 実読(PDF本文抽出・11min4sec / 11.7 spheres / 57.1% / 25min26sec) |
| R4 | Lipari G. *EDF Scheduling*(講義資料, Scuola Superiore Sant'Anna / RETIS) | https://retis.santannapisa.it/~lipari/courses/str12/16.edf-handout.pdf | ✔ 実読(PDF本文抽出・domino effect / FP predictability / optimality) |
| R5 | Rindel J.H. (2019) *Restaurant acoustics – Verbal communication in eating establishments*, Acoustics in Practice Vol.7, No.1(EAA) | https://euracoustics.org/documents/8/01_Restaurant_acoustics.pdf | ✔ 実読(PDF本文抽出・Table 2/Table 3・Lombard式・距離3dB) |
| R6 | Rindel J.H. (2010) *Verbal communication and noise in eating establishments*, Applied Acoustics 71:1156–1161 | https://odeon.dk/pdf/A21-ApplAc%202010%20Rindel.pdf | ✔ 実読(PDF本文抽出・Table 1/Table 5・c=0.5・SNR定義) |
| R7 | ASHA *Determining Threshold Level for Speech*(Guidelines) | https://www.asha.org/policy/gl1988-00008/ | ✔ 実読(SDT/SRT 定義・8–9 dB) |
| R8 | Pan et al. (2026) *ScaleSim: Serving Large-Scale Multi-Agent Simulation with Invocation Distance-Based Memory Management*, arXiv:2601.21473 | https://arxiv.org/html/2601.21473 | ✔ 実読(要約経由・sparse activation 20%・invocation distance・1.74×) |
| R9 | Xie Z., Kang H., Sheng Y., Krishna T., Fatahalian K., Kozyrakis C. (2024) *AI Metropolis*, arXiv:2411.03519 | https://arxiv.org/abs/2411.03519 | ✔ アブスト級(out-of-order・false dependency・1.3–4.15×) |
| R10 | EVE University Wiki *Time dilation* | https://wiki.eveuniversity.org/Time_dilation | ✔ 実読(10% 下限)/ ※コミュニティ二次資料 |
| R11 | CCP Games 公式 *Introducing Time Dilation* | https://www.eveonline.com/news/view/introducing-time-dilation | **空欄(404・未確認)** |
| R12 | Klinzing J.G., Niethard N., Born J. (2019) *Mechanisms of systems memory consolidation during sleep*, Nature Neuroscience 22:1598–1610, PMID 31451802 | https://pubmed.ncbi.nlm.nih.gov/31451802/ | **部分(書誌のみ確認・本文は cookie壁/認証壁で未読・引用は検索要約級)** |
| R13 | Lin K., Snell C., Wang Y., Packer C., Wooders S., Stoica I., Gonzalez J.E. (2025) *Sleep-time Compute: Beyond Inference Scaling at Test-time*, arXiv:2504.13171 | https://arxiv.org/abs/2504.13171 | **部分(書誌・著者確認済/本文未読・5×は検索要約級)** |
| R14 | Liu E.S., Theodoropoulos G.K. (2014) *Interest Management for Distributed Virtual Environments: A Survey*, ACM Comput. Surv. 46(4) | https://dl.acm.org/doi/10.1145/2535417 | **部分(アブスト級・逐語未確認)** |
| R15 | *Update schedules for improving consistency in multi-server DVEs*, J. Netw. Comput. Appl. (2014) | https://www.sciencedirect.com/science/article/abs/pii/S1084804514000083 | **空欄(403・未読)** — PRR / starvation-free は検索要約級 |
| R16 | Liu J.W.S. et al. (1991) *Algorithms for Scheduling Imprecise Computations*, IEEE Computer | https://ieeexplore.ieee.org/document/76287/ | **空欄(未読)** — graceful degradation は検索要約級 |
| R17 | Lazarus H. (1986) *Prediction of verbal communication in noise – a review: part 1*, Applied Acoustics 19:439–464 | (Rindel 2010 参考文献[1] として書誌のみ) | **空欄(本文未読)** — §6 追加確認候補 |
| R18 | Lazarus H. (1987) *Prediction of verbal communication in noise — generalized SIL curves and the quality of communication (Part 2)*, Applied Acoustics | https://www.sciencedirect.com/science/article/abs/pii/0003682X87900624 | **空欄(本文未読)** |
| R19 | ISO 9921:2003 *Ergonomics — Assessment of speech communication* | https://www.iso.org/standard/33589.html | **空欄(数表は有料・未読。本答申では条番号を使用していない)** |
| R20 | AgentSociety (2025) arXiv:2502.08691 — 起床間隔の規定 | https://arxiv.org/html/2502.08691 | **空欄(該当記述を発見できず)** |
| R21 | 「Forssberg」— 歩行者の会話距離/反応時間のいずれの解釈でも | — | **空欄(未確認・発見できず)** |
| R22 | 屋外活動の持続時間分布(買物・裁量的活動の平均分) | https://pmc.ncbi.nlm.nih.gov/articles/PMC10149489/ | **空欄(実読したが該当記述なし。検索要約の「10-30分」は原典未確認のため不使用)** |
| R23 | 騒音下の SRT ≈ −8.14 dB(正常聴力成人の参照値) | https://pmc.ncbi.nlm.nih.gov/articles/PMC9442123/ | **部分(検索要約級・逐語未確認)** |

### 既往 repo 記録に依拠した項目(本答申では再確認していない)
- OASIS の 1ステップ=3シミュ分、Table 2 の効率数値、N^1.51–1.57 スケール指数 → `docs/research/v2-perception-timing-research.md`(実読記録あり)
- Concordia の「観測≠行動」「GM 門番」逐語 → 同上
- Project Sid / PIANO の異時間尺度 → 同上
- Brungart et al. 2020(0.44 dB/dB・距離≈1 m) → `docs/research/v2-hearing-numbers-and-d1-coverage.md`(親の一次確認済)
- TU Delft / Engineering ToolBox の SIL 通話距離2表 → 同上
