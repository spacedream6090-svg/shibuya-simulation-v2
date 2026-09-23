# R-41 答申: 認知アーキテクチャ議事録(個体側)の先行検証

<!-- hdr:v1 -->
- **分野**: 認知科学(記憶・習慣) #12 / 自然言語処理・機械学習 #27 / 歩行者動力学 #18 / ゲームエンジン工学・CG #30 / ソフトウェア工学 #29 | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **B** = サブ実読(原典 8・抄録/二次多数・空欄 24 = §10)+**親検収**(第256・Kinny / Schut / Fox / PIANO / System-1.5 を逐語確認・**Moussaïd の逐語 1 件を訂正**・Niederberger & Gross と CoALA 本文は親未確認)。等級の根拠は §0 と直下の検収欄。
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 用途: ユーザーが別チャットでまとめた認知・社会アーキテクチャ議事録(2026-09-23・以下「議事録」)を v2 に組み込むかを親が評価する材料。
> **本書は設計評価ではない**。議事録の各主張について、先行研究・先行実装が何を言っているか(事実と数値)と、議事録の主張が先行と一致するか矛盾するかだけを書く。
> 規律: 子サブ未起動・Web は読むだけ・コミットなし・台帳未編集・`data/` 未使用・既存ファイル未編集(本書の新規作成のみ)。

---

> **親検収(2026-09-23・第256・Opus 5)**: 結論を変える主張を親が原典で再確認した(WebFetch 本文 / 保存 PDF を pymupdf 抽出)。**逐語の誤りを 1 件見つけて訂正した**。
> - **✓ Kinny & Georgeff 1991**(IJCAI PDF): 「reacting to any new hole is worse than blind commitment, except for high values of γ」/「the simple change in commitment from blind to reactive results in the bold agent being everywhere superior to the more cautious ones」/「the combination of commitment with intelligent reactive replanning was observed to result in optimal behaviour」を逐語確認。**サブの確認依頼 ③ は正しい**: 抽出は「a 25 range of values in 7」で γ が「7」に化けており、**2^5 か 25 かは判別できない**=図のみ=**親未確認**(設計書に写さない)。
> - **✓ Schut & Wooldridge 2001**(著者公式 PDF): 「in a static world (where dynamism is low), a bold agent indeed outperforms a cautious agent. But from some point onwards (dynamism is approximately 28), a cautious agent outperforms a bold one.」/「when planning is free, the adaptive agent outperforms the other two agents, independent of the dynamism of the world.」/「planning cost has a negative influence on commitment — as planning cost increases, the level of commitment decreases.」/「if dynamism increases, the level of commitment decreases.」/「took values 0, 1, 2 and 4」をすべて逐語確認。**サブの確認依頼 ② も正しい**(28 は Schut の dynamism 定義であって Kinny の γ ではない=同じ軸に並べない)。
> - **✓ Fox ら 2006**(AAAI PDF): 表「880 DriverLog-Time variants / Repair 9517 75.8% 8.9% 100% / Replan 5645 47.7% 66.0% 44.3%」と Definition 2(`D(π0, π1)` = π1 にあって π0 に無い行動数 + π0 にあって π1 に無い行動数)を逐語確認。
> - **✓ PIANO(Project Sid §2)**(arXiv HTML): 「slow mental processes, such as self-reflection or planning, should not block agents from responding to immediate threats」/「Each module can be seen as a stateless function that reads and writes to a shared Agent State.」/「The Cognitive Controller synthesizes information across the Agent State through a bottleneck.」/「our system consists of 10 distinct modules running concurrently.」/「reflex modules use small, fast non-LLM neural networks」を逐語確認。**PIANO の展開が論文内で不一致**(抄録 = Parallel **Information** Aggregation / §2 = Parallel **Input** Aggregation)も確認。**stale・中断の機構が本文に無い**というサブの「記述の不在」も、親の本文検索で一致。
> - **✓ System-1.5 Reasoning**(arXiv:2505.18962 abs): 題名と「accelerating inference by over 20x and reducing token generation by 92.31% on average」を確認。**議事録の「System 1.5」は心理学に用例が無いが、2025 年の LLM 論文が同名を先取している**=命名を外向き(未踏・論文)に使うと衝突する。
> - **✗ 訂正(サブの逐語が原典に無い)— Moussaïd ら 2011**: サブが §7 で「高密度では **physical interactions, rather than individual intentions, play the dominant role**」と引いた一文は、**arXiv:1105.2152 本文に存在しない**(親が全文抽出して 0 件)。原典の該当箇所は「In cases of overcrowding, **physical interactions between bodies may occur, causing unintentional movements that are not determined by the above heuristics.** Indeed, at extreme densities, it is necessary to distinguish between the **intentional avoidance behavior** of pedestrians adapting their motion according to perceived visual cues, and **unintentional movements resulting from interaction forces caused by collision with other bodies.**」。→ **主張の向きは残るが「支配する(dominant)」という強さは原典に無い**。§7 の判定は「高密度で矛盾」ではなく「**極端な密度では、ヒューリスティックで決まらない非意図的な動きが加わる**」と読むこと(本書 §7 の該当行は第256 で書き換えた)。あわせて **τ = 0.5 s は逐語確認**(「a relaxation time τ of 0.5 seconds」)、**φ = 75° は本文に無く親未確認**(φ は「vision field … by φ degrees」と定義だけ)。
> - **△ 親未確認のまま**: Niederberger & Gross 2005(Springer が認証リダイレクトで本文・抄録とも取れず)=**サブの「矛盾」判定(配った時間が先読みの洗練度を決める)の根拠は親未確認**。CoALA の 4 記憶と「social memory が本文に 0 件」(親は abs のみ確認・abs に memory 型の列挙は無い)。Botvinick の式・Thompson の FOR・Corbetta & Shulman・Soar impasse・Zilberstein の加速比 4。
> - **サブの確認依頼 5 件への回答**: ① Botvinick の式(係数 −2・0 フロア)は**設計書に写さない**(二次)。② ③ 上のとおり**サブが正しい**。④ Chenney & Forsyth の culling は **1997 I3D** が正しい(サブの訂正を採用)・2001 は Proxy Simulations で「two orders of magnitude」は**親未確認**。⑤ コンパイルの**速度則の数値は空欄のまま**=v2 が数字を置けば設計者の指紋になる、という警告を採用する。

---

## §0 等級と調べ方

**等級 B**。確認の別を各行に付けた: **原典**(本文/表/式を読んだ)/ **抄録**(abs・公式要約のみ)/ **二次**(検索要約・引用経由)/ **未読**。

- 本文を実読したもの(PDF を pymupdf で抽出して読んだ): Kinny & Georgeff 1991(IJCAI PDF 7 頁)・Schut & Wooldridge 2001(AGENTS'01 PDF 8 頁)・Fox ら 2006(ICAPS PDF 10 頁)・O'Sullivan ら 2002(CGF 著者版 PDF 9 頁)・Wißner ら 2010(MIG PDF 12 頁)・Sumers ら 2023 CoALA(TMLR 版 PDF 32 頁)。
- HTML 本文を実読したもの: Altera.AL 2024 PIANO(arXiv HTML v1 §2)・Clark 2013(Cambridge Core 本文 §2.3・§3.1 まで。§3.3 以降は切断)。
- 抄録・公式ページのみ: Moussaïd 2011(arXiv abs)・Zheng ら 2025 RRARA(arXiv abs)・Niederberger & Gross 2005(Springer abs)・Brom ら 2007(Springer abs)・Pettersson 2005・Corbetta & Shulman 2002・Thompson ら 2011・Logan 1988・Laird ら 1986・Taatgen & Lee 2003。
- **既存答申で済んでいるものは引くだけにした**: 二重過程の定義と発火頻度・メタ推論・cascade/routing は [R-39](v2-r39-judgment-share-research.md)、蒸留と lookup 表は [R-38](v2-r38-closed-output-judges-research.md)、思考頻度の錨は [thought-frequency-anchors-note](v2-thought-frequency-anchors-note.md)、技能庫・行動語彙は [D-71 答申](v2-d71-vocab-growth-research.md)、注意の焦点と saliency は [C9 答申](v2-c9-position-attention-research.md) §1.4、群衆物理は [R-7 答申](v2-crowd-physics-research.md)。
- **第210 訂正との関係**(Project Sid): 訂正は Sid が**法体系を設計上の前提として置いた**こと・解析は**500 体 1 本**であることについてのもので([r23-primary-check-batch2](v2-r23-primary-check-batch2.md)・[lit/css__projectsid2024_de-novo-limit](lit/css__projectsid2024_de-novo-limit.md))、**PIANO アーキテクチャの記述は既存 lit ノートが明示的に扱っていない**(同ノート「アーキテクチャ(PIANO)は扱わない」)。§4 はその空白を埋めるもので、主張が重ならない。§4 では Sid の**制度・創発**には一切触れない。

---

## §1 Q1 — 再考層と「System 1.5」(議事録 §3・§6)

### 1-1 「System 1.5 / Type 1.5」という用語

| 事実 | 逐語・数値 | 確認 |
|---|---|---|
| **心理学に「System 1.5 / Type 1.5」という確立した用語は無い**。探索範囲(二重過程の総説・Evans & Stanovich 2013・批判側)で用例を 1 件も確認できなかった | — | 二次(探索の否定) |
| 唯一の形式的用例は **LLM 効率化の工学論文**: 「System-1.5 Reasoning: Traversal in Language and Latent Spaces with Dynamic Shortcuts」arXiv:2505.18962(NeurIPS 2025 poster) | 「difficult reasoning steps are handled with deliberate, reflective System-2 thinking, simple steps are processed quickly through heuristic System-1 thinking, and trivial steps are naturally skipped」/ GSM8K で「accelerating inference by over 20×」「reducing token generation by 92.31% on average」 | 二次(検索要約・本文未読) |
| 心理学側で「中間層」に最も近いのは **Stanovich の三分説**(autonomous mind / algorithmic mind / reflective mind。Stanovich 2009 / 2011) | 「The key function of the reflective mind is to **detect the need to interrupt autonomous processing** and to begin simulation activities, whereas that of the algorithmic mind is to sustain the processing of decoupled secondary representations」 | 二次(著者公開 PDF の引用経由・本文未読) |
| ただし **Stanovich は「Type 3 処理」を立てていない**。三分は**制御の階層**であって処理型ではない | Evans & Stanovich 2013:「Dennett's 'kinds of minds' terminology refers to **hierarchies of control rather than separate systems**. Two levels of control are associated with Type 2 processing and one with Type 1 processing.」 | 二次(R-39 §3-1 で Table 1 は**原典**確認済み。この一文は未確認) |

### 1-2 Type 2 への切り替えの引き金

| 先行 | 主張・式 | 数値 | 確認 |
|---|---|---|---|
| **Botvinick, Braver, Barch, Carter & Cohen 2001**, *Psychol Rev* 108(3):624-652, [doi:10.1037/0033-295X.108.3.624](https://doi.org/10.1037/0033-295X.108.3.624) | 制御の必要は**葛藤の監視**で評価される。葛藤 = **Hopfield energy** = 出力層で両立しない表象が同時に活性化している度合い。葛藤 → 制御強化のフィードバックループを計算モデルで示した | 2 応答ユニットの場合 `energy = max(0, −2·(a_L·a_R·w_ij))`(競合ユニットの活性の積 ×(抑制性の)重み・0 でフロア) | **二次**(式は 2025 年 *Psychophysiology* の再実装記述経由。**原典本文は未読**=§9-1) |
| **Thompson, Prowse Turner & Pennycook 2011**「Intuition, reason, and metacognition」*Cognitive Psychology* 63(3):107-140, [doi:10.1016/j.cogpsych.2011.06.001](https://doi.org/10.1016/j.cogpsych.2011.06.001) | 初期の直感解には **Feeling of Rightness (FOR)** というメタ認知経験が伴い、それが追加分析の要否を知らせる。**answer fluency(解が浮かぶ速さ)が FOR を決め、FOR が熟考時間と答えの変更を予測する**(Metacognitive Reasoning Theory) | 4 課題の N = 60 / 48 / 128 / 64 | 抄録(ERIC・PubMed。**本文未読**) |
| **Clark 2013**「Whatever next?」*BBS* 36(3):181-204, [doi:10.1017/S0140525X12000477](https://doi.org/10.1017/S0140525X12000477) | 予測誤差は**精度(不確実性の逆)で重みづけ**される。精度 = 誤差ユニットの**ゲイン**。注意とは特定の誤差ユニットに重みを与えることに他ならない | §2.3「Greater precision (however encoded) means less uncertainty, and is reflected in a **higher gain on the relevant error units**」/「This is achieved by altering the gain … on the error-units accordingly.」/「Attention, if this is correct, is simply one means by which certain error-unit responses are given increased weight」/ §3.1 の誤差ユニットは「encoding **precision-weighted prediction errors**」 | **原典**(Cambridge Core 本文 §2.3・§3.1。§3.3 以降は切断) |
| 同上・**式は無い** | 本文に出るのは自由エネルギー原理の定性記述のみ(「all the quantities that can change … will change to minimize free-energy」Friston & Stephan 2007 p.427 の引用) | 数値は Egner ら再現の「twice as much to the fMRI signal」・Melloni「around 100 msec」のみ | **原典** |
| **既出**: 熟考の引き金は強度でなく**葛藤**(Hofmann 2012・Blog=0.53 vs 欲求の強さ p=.17)/ 監視は常時・介入はまれ(De Neys)/ 速い層に任せてよいかは**環境の妥当性と学習機会**で決まり**速い層の確信度は指標にならない**(Kahneman & Klein 2009)/ 2 系が最適になる条件の形式化(Milli 2017) | — | **R-39 §2-2・§3-2・§4・§5-1 で既出**(原典確認済み) |

### 1-3 議事録との対応

| 議事録 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §3.1 | 「System 1.5 は心理学上の標準的な用語ではなく、このプロジェクトの工学的命名」 | 心理学に用例なし。**ただし 2025 年の LLM 論文 arXiv:2505.18962 が同名を先に使っている** | **一致**(ただし名前が既に埋まっている) | 二次 |
| §3.1 | System 1.5 = System 1 が再考モードへ移った状態/機構 | Stanovich の algorithmic mind(System 2 の下位層)は**制御の階層**であり「System 1 の一状態」ではない | **部分一致** | 二次 |
| §6.1 | 「prediction_error > threshold → Jev」とはしない。6 項を組み合わせる | 先行も単一閾値を採らない(Botvinick=葛藤 / Thompson=FOR / Clark=精度重み) | **一致** | 原典+抄録 |
| §6.1 | `E = w1·pred_err + w2·uncert + w3·novelty + w4·goal_conflict + w5·failure + w6·stakes` | **この形(6 項の設計者指定の重みつき線形和)の先行は見つからなかった**。先行はいずれも**単一量**(conflict / FOR / precision)か、**重みが導出される**もの(precision = 不確実性の逆) | **先行なし** | — |
| §5.2 | uncertainty を state / dynamics / policy の 3 つに分ける | 神経側の調停は **model-based の信頼度=状態予測誤差 SPE・model-free の信頼度=報酬予測誤差 RPE** の 2 種(Lee ら 2014・R-39 §5-2 既出)。3 分割の先行は無い | **部分一致** | 二次(R-39 既出) |
| §5.1 | `policy_confidence` を持ち escalation の材料にする | Kahneman & Klein 2009「Subjective confidence is therefore an unreliable indication of the validity of intuitive judgments」 | **矛盾**(R-39 §4 と同じ論点) | 原典(R-39 既出) |

---

## §2 Q2 — BDI の intention reconsideration(議事録 §6・§9)

### 2-1 Kinny & Georgeff 1991(IJCAI-91, 82-88)

**PDF 全 7 頁を実読**。PRS + 簡略 Tileworld(タイル無し・穴のみ)。

| 項目 | 逐語 | 確認 |
|---|---|---|
| bold/cautious の定義 | 「Pollack and Ringuette [1990] define a **bold agent** as one that never reconsiders its options before the current plan is executed in its entirety, and a **cautious agent** as one that reconsiders every new option.」 | **原典** |
| 実装 | 「We implemented a crude parameterization of its degree of boldness by specifying **the maximum number of plan steps that the agent executes before replanning**.」 | **原典** |
| 世界の動的さ | 「the ratio of their clock rates set by a parameter **γ** called the **rate of world change**」 | **原典** |
| 効果の測り方 | 「we defined an agent's **effectiveness ε** to be its score divided by the maximum possible score it could have achieved」 | **原典** |
| 実験設計 | 1 実験 = 同一初期配置・乱数種違いの **5 ゲーム**。1 特性曲線 = γ を **2^5 の範囲**で振った最大 **15 点**(抽出テキストは「a 25 range」=§9-3)。1 実験 ≈ Sun Sparcstation で 30 分・1 特性 = 最大 8 時間 | **原典** |
| 計画費 p=4 のとき | 「In this case **the bold agent is superior to the normal agent, which is superior to the cautious agent**.」(cautious=1 歩・normal=4 歩・bold=全計画) | **原典** |
| p を下げると | 「As p decreases two things happen: the gap between the cautious and the bolder agents becomes narrower, and **the normal agent becomes superior to the bold agent in more dynamic worlds**. In the final graph the cautious agent is as effective as the bold agent at high rates of change.」 | **原典** |
| 反応戦略(目標消滅 / 目標消滅 or 穴出現 / 目標消滅 or より近い穴出現) | 「reacting to the disappearance of the target improves performance significantly. Combining this with replanning when a nearer hole appears is better still. **On the other hand, reacting to any new hole is worse than blind commitment, except for high values of γ.**」 | **原典** |
| 最重要の結論 | 「the simple change in commitment from blind to reactive results in **the bold agent being everywhere superior to the more cautious ones**.」/「the combination of commitment with **intelligent reactive replanning** was observed to result in **optimal behaviour**.」 | **原典** |
| **数値は図にしかない** | 本文中の数値は p ∈ {0.5,1,2,4}・コミット長 {1,4,全計画}・5 ゲーム・15 点のみ。ε の具体値・交差点の γ は**図のみ**=空欄 | **原典**(数値は未取得) |

### 2-2 Schut & Wooldridge 2001「Principles of Intention Reconsideration」AGENTS'01

**PDF 全 8 頁を実読**。Russell & Wefald の離散熟考スケジューリングを BDI に統合し、**実行時に**方針を選ぶ適応エージェントを作った。

| 項目 | 逐語・数値 | 確認 |
|---|---|---|
| 計画費 | 「The planning cost … took values **0, 1, 2 and 4**」 | **原典** |
| 効果・コミットの定義 | 「the effectiveness … is the ratio of the actual score achieved by the agent to the score that could in principle have been achieved」/ commitment は「how many actions of a plan are executed before the agent replans」(cautious=0・bold=1 の連続スペクトル) | **原典** |
| **交差点** | 計画が無料(p=0)のとき「in a static world (where dynamism is low), a bold agent indeed outperforms a cautious agent. But **from some point onwards (dynamism is approximately 28), a cautious agent outperforms a bold one**.」 | **原典** |
| 適応エージェント | 「when planning is free, **the adaptive agent outperforms the other two agents, independent of the dynamism of the world**.」/ 計画費が上がると効果は bold に接近するが「the adaptive agent's **acting cost is much lower**」 | **原典** |
| コミット水準の法則 | 「**planning cost has a negative influence on commitment** — as planning cost increases, the level of commitment decreases.」/「if **dynamism increases, the level of commitment decreases**.」 | **原典** |
| 再考の判定規則(Tileworld 版・Figure 3) | 「Deliberation is considered necessary when it is expected that since the last deliberation, **the current goal has disappeared or that new goals have appeared**.」(期待効用 `U(d)` と `U(a_def)` を比べ `U(d) − U(a_def) > 0` なら熟考) | **原典** |

### 2-3 Plan repair vs replanning — Fox, Gerevini, Long & Serina 2006(ICAPS-06, 212-221)

**PDF 全 10 頁を実読**。

| 項目 | 逐語・数値 | 確認 |
|---|---|---|
| 安定性の定義 | 「**Definition 2** Given an original plan, π0, and a new plan, π1, the difference between π0 and π1, **D(π0, π1)**, is the number of actions that appear in π1 and not in π0 plus the number of actions in π0 that are not in π1.」 | **原典** |
| 安定性を求める理由 | 「plans provide a means to **communicate future intentions to other agents**」/「in highly dynamic situations stability might be impossible to achieve」 | **原典** |
| 主要な数値(**880 DriverLog-Time variants**) | Repair: Init **9517** / Orig **75.8%** / Diff **8.9%** / **Eq 1st 100%** ‖ Replan: **5645** / **47.7%** / **66.0%** / **44.3%**(Eq 1st = 新計画の最初の行動が元計画の最初の行動と一致した割合) | **原典** |
| 使える発見的手続き | 「check whether the next step of the original plan is still executable and, if so, **execute it and spend all the time up to the end of this action repairing the plan**」 | **原典** |
| 速度・品質 | 「plan repair, using our approach, **generates plans faster than replanning**」/ 最初の解でも「the quality of the first repaired plan is also much higher than the first solution generated by replanning」(CPU 時間は図 1〜10 のみ=空欄) | **原典**(数値は未取得) |

### 2-4 実行監視の survey — Pettersson 2005

*Robotics and Autonomous Systems* 53(2):73-88, [doi:10.1016/j.robot.2005.09.004](https://doi.org/10.1016/j.robot.2005.09.004)。分類は産業制御から借りた **3 クラス**: 「execution monitoring can be categorized into one or several of three classes: **analytical, data-driven, and knowledge-based**」(Chiang ら由来)。定義は「a continuous real-time task of determining the conditions of a physical system, by recording information, recognizing and indicating anomalies」。監視系の機能は Gertler の 3 分(検知・分離・同定)。**確認 = 抄録/二次**(本文未読)。

### 2-5 議事録との対応

| 議事録 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §6.3 | Jev を「毎回の行動生成器」にしない | Kinny「reacting to any new hole is worse than blind commitment」/ Schut「計画費が上がると bold に近づくのが最適」 | **一致**(30 年前に実験で確かめられている) | 原典 |
| §6.1 | 再考の引き金は複合 | Kinny の反応戦略比較(目標消滅 > 目標消滅+近い穴 > 何でも再考)/ Schut の `reconsider()` = 目標消滅 or 新目標出現 | **一致**(ただし先行の引き金は **2 項**で、議事録の 6 項ではない) | 原典 |
| §6.1 | 重み・閾値・hysteresis は実験対象 | Schut は**実行時に方針を選ぶ**(design-time から run-time へ移す)ことを主題にし、固定方針に勝つと示した | **一致**(先行の結論が「固定しない」) | 原典 |
| §9 | Policy validity を `VALID / ADJUSTABLE / DEGRADED / INVALID / UNKNOWN` の 5 値にする | **5 値の対応物は見つからなかった**。近いのは (a) Fox の 2 値(repair か replan か)(b) Kinny の反応戦略 3 種 (c) Pettersson の 3 クラス・FDI 3 機能 | **先行なし** | — |
| §9 | 「Route INVALID ≠ Policy INVALID」= 上位が生きていれば下位だけ直す | Fox の plan repair の動機そのもの(D(π0,π1) を小さく保つ)。実測は **Eq 1st 100% vs 44.3%** | **一致** | 原典 |
| §8 | `ΔAPS = APS_t − APS_t−1` の差分中心 | Kinny & Georgeff の前提は「perfect, **zero-cost** knowledge of the current state」=知覚費用を無視。**差分知覚の費用を測った先行は本調査では取れていない**(Kinny, Georgeff & Hendler 1992 が sensing cost を入れたとの二次記述のみ) | **部分一致** | 二次 |

---

## §3 Q3 — 高次推論の System 1 へのコンパイル(議事録 §20・原則 L)

| 先行 | 機構・条件 | 数値 | 確認 |
|---|---|---|---|
| **Laird, Rosenbloom & Newell 1986**「Chunking in Soar」*Machine Learning* 1(1):11-46, [doi:10.1007/BF00116249](https://doi.org/10.1007/BF00116249) | **サブゴールでの処理結果から規則(chunk)を作り、以後はサブゴールを経ずに発火する**。「By replacing complex processing in subgoals with chunks learned during practice, the model could **improve its speed**」。学習は問題解決中に**逐次**起き、前処理相を要さない。汎化は「additional generality can be obtained via **transfer of learning** between macro-operators **if an appropriate representation of the task is available**」 | 八パズルのマクロ演算子で実証。**決定回数の前後比などの数値は本調査で取得できず** | 抄録/二次 |
| **Taatgen & Lee 2003**「Production Compilation」*Human Factors* 45(1):61-76, [doi:10.1518/hfes.45.1.61.27224](https://doi.org/10.1518/hfes.45.1.61.27224) | ACT-R の機構。「two production rules … are combined by **eliminating a condition after being executed sequentially**」。Kanfer-Ackerman 航空管制課題で Fitts の 3 段階(認知→連合→自律)を 1 つのモデルで再現 | **速度向上の数値は本調査で 1 つも取得できず**(SAGE 有料・著者サイト 404) | 二次 |
| **Logan 1988**「Toward an instance theory of automatization」*Psychol Rev* 95(4):492-527, [doi:10.1037/0033-295X.95.4.492](https://doi.org/10.1037/0033-295X.95.4.492) | 自動化 = **算法と記憶検索の競走**。「performance to be automatic when it is **based on memory retrieval** whether that occurs on the 10th trial or the 10,000th」。速くなる条件は**一貫した環境での練習**(consistency が無ければ検索した事例が役に立たない) | 「accounts quantitatively for the **power-function speed-up** and predicts a **power-function reduction in the standard deviation that is constrained to have the same exponent**」=平均と SD の指数が同じ、という強い予測 | 二次(著者公開 PDF は接続拒否) |
| **Newell & Rosenbloom 1981**「Mechanisms of skill acquisition and the law of practice」in Anderson (ed.) *Cognitive Skills and Their Acquisition*, 1-55 | 練習のべき法則 `RT = a + b(N + p)^(−c)`(a = 漸近値・p = 既往試行数) | Crossman 1959 のシガー巻き: 最大 **2,000 万本**・「practice followed the law for almost **3 million trials (and 2 years)**」・その後は機械のサイクル時間で頭打ち。指数 ≈0.4 は**三次資料**なので採らない | 二次 |
| **べき法則への反証** | Heathcote, Brown & Mewhort: 集計曲線のべき乗は**平均化の人工物**で、個体では**指数関数**の当てはまりが良い | 「only two previous teams had fitted single-subject as well as average-subject data, and both got the same result」 | 二次 |
| **CLARION の bottom-up learning** | MCS が「cognitive mode selection: selection of explicit processing, implicit processing, or a combination thereof」を担い、層の選択は「the probability of selecting a component is determined based on the **relative success ratio** of that component」 | — | **R-39 §5-3 で既出**(原典確認済み) |
| **LLM エージェント側** | Voyager の skill library(登録閾値 = 1 回の成功)・AWM(offline/online 両立)・ASI(検証を通すと採用率 15.6% vs AWM 31.4%・検証段で +4.2 pt)・LearnAct(2 反復で最適・行動数 3.75→3.83)・Emergence World(15 日 × 5 世界で自作道具 **2 件**) | — | **D-71 §1.1〜§1.3 で既出**。本調査で新規の追加なし |

### 議事録との対応

| 議事録 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §20・原則 L | 高次推論で得た行動知識を経験・学習で System 1 へ「コンパイル」する | Soar chunking・ACT-R production compilation・Logan の instance theory・CLARION の bottom-up が **4 つの独立な系譜で同じ形**を採っている | **一致** | 抄録/二次 |
| §20 | 「未知 → Jev」が学習で「既知 → System 1」へ降りる | Soar は**サブゴール(=impasse)の結果を規則化**する。引き金が「決定できなかった」であって「予測誤差が大きい」ではない点は異なる(§5 参照) | **部分一致** | 抄録/二次 |
| §20 | 最も自然なのは prediction learning(予測の更新) | Logan は**事例検索**の速度、ACT-R/Soar は**規則の畳み込み**。予測誤差で予測器を直す形は predictive processing 側(Clark 2013)にあるが、そちらは「System 1 へ降ろす」話ではない | **部分一致** | 原典+二次 |
| §20 | コンパイルで**どれだけ速くなるか** | **本調査では数値を 1 つも取れていない**。法則の形(べき乗)は取れたが指数は課題依存で、かつ個体レベルではべき乗でない可能性が報告されている | **空欄** | — |

---

## §4 Q4 — LLM エージェントの認知アーキテクチャ(議事録 §19・§23〜25・§47)

### 4-1 CoALA(Sumers, Yao, Narasimhan & Griffiths 2023, [arXiv:2309.02427](https://arxiv.org/abs/2309.02427), TMLR 2024)

**TMLR 版 PDF 全 32 頁を実読**。記憶は **working / episodic / semantic / procedural** の 4 種。

- Working: 「Working memory … reflects the agent's current circumstances: it stores the agent's **recent perceptual input, goals, and results from intermediate, internal reasoning**.」
- Episodic: 「**Episodic memory stores experience from earlier decision cycles.** This can consist of training input-output pairs, history event flows, game trajectories from previous episodes, or other representations of the agent's experiences.」
- Semantic: 「**Semantic memory stores an agent's knowledge about the world and itself.**」
- Procedural: 「Language agents contain **two forms of procedural memory: implicit knowledge stored in the LLM weights, and explicit knowledge written in the agent's code**.」/「procedural memory **must be initialized by the designer** with proper code to bootstrap the agent」/「while learning new actions by writing to procedural memory is possible, it is **significantly riskier** than writing to episodic or semantic memory」
- 決定周期は planning(推論・検索で案を出し評価)と execution(選ばれた学習/接地行動を実行)の 2 段。
- **「social memory」という語は本文に 1 件も無い**(32 頁全文を検索して 0 件)。

### 4-2 PIANO(Altera.AL ら 2024, [arXiv:2411.00114](https://arxiv.org/abs/2411.00114) v1 §2)

**arXiv HTML 本文を実読**(アーキテクチャ節のみ。制度・創発には触れない)。

| 項目 | 逐語 | 確認 |
|---|---|---|
| 名称 | 抄録「PIANO (**Parallel Information Aggregation** via Neural Orchestration)」/ §2「We call this architecture PIANO (**Parallel Input Aggregation** via Neural Orchestration)」=**論文内で不一致** | **原典** |
| 動機(=「世界を止めずに考える」) | §2.1「**slow mental processes, such as self-reflection or planning, should not block agents from responding to immediate threats**」/ エージェントは「interactive in real time with low-latency, but also have the capacity to slowly deliberate and plan」 | **原典** |
| 並行実行 | §2.1「Each module can be seen as a **stateless function that reads and writes to a shared Agent State**.」/ モジュールは「run at different speeds」 | **原典** |
| ボトルネック | §2.2「The **Cognitive Controller** synthesizes information across the Agent State **through a bottleneck**.」/「solely responsible for making high-level deliberate decisions」/「Once the Cognitive Controller makes a high-level decision, this decision is **broadcast** to many other modules.」 | **原典** |
| 数値 | §2.3「our system consists of **10 distinct modules running concurrently**.」/ §2.1「**reflex modules use small, fast non-LLM neural networks**, while goal generation involves deliberate reasoning over graphs」/ §5.1 社会目標は「every **5-10 seconds**」再生成 | **原典** |
| **測っていないもの** | モジュール毎の遅延・tick 率・**stale な結果の扱い**は本文に記述が無い。機構として書かれているのは「モジュールは stateless・共有 Agent State」だけ | **原典**(本文検索の範囲で) |

### 4-3 「思考中も世界が進む」を明示した他の先行

| 先行 | 何を実装・測ったか | 確認 |
|---|---|---|
| **RRARA**(Zheng, Mao, Zhang & Cai 2025, [arXiv:2506.07223](https://arxiv.org/abs/2506.07223), CVPR 2025 EAI Workshop) | **Time Conversion Mechanism (TCM)**: 「maps inference time to elapsed simulation time, allowing **computational delays to directly affect environmental evolution** and agent outcomes」= 推論の実時間をシミュのフレームに換算し、考えている間に世界を進める。指標は **Response Latency (RL)** と **Latency-to-Action Ratio (LAR)**。構成は「rapid reflexive policies trigger immediate actions while an **asynchronous LLM Reflector** analyzes and refines those actions in situ」。ベンチは HAZARD | 抄録(**本文・数値未読**) |
| **Real-Time Reasoning Agents**(ICLR 2026) | 既存ベンチが「環境が推論中に止まる」前提であることを問題にし、「we measure **elapsed token count as a hardware-agnostic temporal unit**」。先行として Delay-Aware MDP・sticky action・asynchronous interactive MDP を挙げ、いずれも RL 止まりと述べる | 二次(検索要約・本文未読) |
| **GPTNT**(2026) | 既定が非同期実時間。「the bomb clock advances in wall-clock time and **does not pause while models are generating**」。同期モードも併置して「速く考える能力」と「正しく考える能力」を分離 | 二次 |
| **DPT-Agent**(Zhang ら 2025, [arXiv:2502.11882](https://arxiv.org/abs/2502.11882)) | System 1 = FSM + code-as-policy、System 2 = ToM + **asynchronous reflection**。動機は実時間同時協調での遅延 | **R-39 §5-4 で既出**(抄録のみ) |

### 4-4 議事録との対応

| 議事録 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §19 | 記憶は **Episodic / Semantic / Procedural / Social** の 4 種 | CoALA は **Working / Episodic / Semantic / Procedural**。前 3 者は逐語で一致。**Social は CoALA に無く(本文 0 件)、代わりに議事録は Working を持たない** | **部分一致** | **原典** |
| §19 | Social memory(人との関係と経験) | 実装先行はある: Affordable Generative Agents の **Social Memory** モジュール(単体で 58.6%) | **部分一致**(理論枠には無いが実装には在る) | D-71 §1.3 既出(原典) |
| §19 | Memory ≠ Belief(記録と現在の推論を分ける) | CoALA は semantic を「knowledge about the world and itself」とするだけで、**記録と推論の分離を明示していない**。分離を実装で示したのは Kuffner & Latombe 1999 の記憶 M と視野 V の分離(§6) | **部分一致** | 原典 |
| §23・§48 | wall-clock time ≠ simulation time。思考は時間を持つ Agent activity | RRARA の TCM と ICLR 2026 の「elapsed token count」が**換算則まで決めている** | **一致**(先行のほうが具体) | 抄録/二次 |
| §23 | 考えている間も他エージェント・世界は進み、本人も System 1 で歩行維持 | PIANO §2.1 の動機そのもの。reflex は非 LLM の小さいネット | **一致** | **原典** |
| §25 | 並行モジュールと高次の中断 | PIANO は 10 モジュール並行 + CC のボトルネック。**ただし中断・stale の機構は書かれていない** | **部分一致** | **原典** |
| §24 | 推論結果に `produced_at / based_on_state_version / valid_until / confidence` を持たせ result validity check をする | **この形(結果にバージョンと有効期限を付けて検査する)の先行は本調査で見つからなかった**。近いのは Fox の plan validity(§2-3)と Chenney & Forsyth の consistency(§8) | **先行なし** | — |
| §22.2 原則 D | 「Language Generation ≠ Cognition」。LLM は Language Realizer に近い | CoALA の procedural memory は**LLM の重みの中の暗黙知識も procedural に入れる**=言語生成を認知から切り離していない | **矛盾**(枠組みの切り方が逆) | **原典** |

---

## §5 Q5 — 割り込み・先取り(議事録 §25)

| 先行 | 事実・逐語 | 数値 | 確認 |
|---|---|---|---|
| **Soar の impasse**(Laird 2022「Introduction to the Soar Cognitive Architecture」[arXiv:2205.03854](https://arxiv.org/abs/2205.03854) / Soar User's Manual 8.6.3) | 「if insufficient or conflicting knowledge is detected during operator selection, a decision cannot be made, and an **impasse** arises」。型は **tie / conflict / state no-change / operator no-change**(+ constraint-failure)。**impasse が自動的に substate を作る**(「Soar automatically creates subgoals in order to resolve impasses. **This is the only way that subgoals get created.**」)。結果が impasse を解くと substate は消える | 「there can be **only one type of impasse at a given level of subgoaling at a time**」 | 二次(検索要約。**原典 PDF は未読**) |
| **anytime algorithm**(Zilberstein 1996, *AI Magazine* 17(3):73-83, [doi:10.1609/aimag.v17i3.1232](https://doi.org/10.1609/aimag.v17i3.1232)) | 「Anytime algorithms give intelligent systems the capability to **trade deliberation time for quality of results**.」**interruptible**(いつ止めても有効な解)と **contract**(与える時間を事前に決める)を区別。performance profile で管理 | 後続の定理: contract を反復倍加して interruptible を作ると **acceleration ratio は高々 4**(Russell & Zilberstein 1991)、かつ **4 が最適=下界**(Zilberstein, Charpillet & Chassaing 2003) | 二次(UMass 公開 PDF は未取得) |
| **Kinny & Georgeff 1991** の位置づけ | 「The key is to **decide cheaply using some simple estimate of utility whether an event warrants more expensive deliberation** [Russell and Wefald, 1989].」/ PRS の **meta-level invocation criteria** で「どの事象が再計画を起こすか」を変えた | — | **原典** |
| **ACT-R の buffer / conflict resolution・EPIC** | 本調査では一次に当たっていない | — | **未読**(§10) |

### 議事録との対応

| 議事録 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §25 | 思考の状態を `RUNNING / COMPLETED / INTERRUPTED / STALE / CANCELLED` の 5 値にする | **5 値の対応物は見つからなかった** | **先行なし** | — |
| §25 | Soft / Medium / Hard の 3 段の割り込み強度 | **3 段の対応物は見つからなかった**。Soar の impasse 型は「強度」でなく「何が足りないか」の分類 | **先行なし** | 二次 |
| §25 | ReasoningState(current_question / working_hypotheses / partial_conclusion / unresolved_items)を持って**再開可能**にする | anytime の **interruptible algorithm** がまさにこれ。ただし**代価が知られている**: contract を interruptible に変えると最悪 **4 倍**遅くなる(かつ 4 が下界) | **一致**(定量的な代価つき) | 二次 |
| §6.3 | 「Jev が必要か」と「Jev を今実行できるか」は別 | Zilberstein の contract(時間を先に与える)/ interruptible(いつでも止める)の区別と同じ切り方 | **一致** | 二次 |
| §7 | 生の WorldEvent から直接 Jev を呼ばない(Perception → Cognitive significance を経る) | Kinny の meta-level invocation criteria(安い見積りで熟考の要否を決める)と同じ構え。実測では**「何でも再考」は盲目的コミットより悪い** | **一致** | **原典** |

---

## §6 Q6 — 知覚: attention/saliency と perceptual LOD(議事録 §17・§18)

| 先行 | 事実・逐語 | 確認 |
|---|---|---|
| **Itti, Koch & Niebur 1998** | 注意の焦点(FOA)は **1 個の位置**・勝者総取り・**inhibition of return**・proximity preference。FOA は 30-70 ms で跳び、注意した領域は 500-900 ms 抑制 | **C9 §1.4 で既出**(サブ実読) |
| **Corbetta & Shulman 2002**「Control of goal-directed and stimulus-driven attention in the brain」*Nat Rev Neurosci* 3:201-215, [doi:10.1038/nrn755](https://doi.org/10.1038/nrn755) | **2 つの部分的に分離した系**: 背側(頭頂間溝+上前頭)が **goal-directed (top-down) selection**、腹側(側頭頭頂+下前頭・右優位)が「specialized for the **detection of behaviourally relevant stimuli**, particularly when they are **salient or unexpected**」。腹側は背側に対する「**circuit breaker**」として働く | 二次(Nature 抄録経由・本文未読) |
| **Noser, Renault, Thalmann & Magnenat Thalmann 1995**「Navigation for Digital Actors based on Synthetic Vision, Memory and Learning」*Computers & Graphics* 19(1):7-19 | **false-coloured rendering**(照明・テクスチャなしで物体ごとに一意の色を割り当てて描画)で可視物体リストを得る。virtual sensor(視覚・聴覚・触覚)の概念 | 二次(Elsevier 有料・未読) |
| **Kuffner & Latombe 1999**「Fast synthetic vision, memory, and learning models for virtual humans」*Computer Animation '99*, 118-127 | 「Graphics rendering hardware is used to **simulate the visual perception of a character**」/「synthetic vision differs from vision computations for real robots, since we can **skip all of the problems of distance detection, pattern recognition, and noisy images**」/ 記憶 M の更新規則(未知なら追加・既知なら状態更新)と「the navigation path-planning module is invoked using **only the objects and transformations in M** as obstacles」= **計画は真の世界でなく記憶だけを見る** | 二次(著者公開 PDF・検索要約経由) |
| **Tu & Terzopoulos 1994**「Artificial fishes」SIGGRAPH '94, 43-50, [doi:10.1145/192161.192170](https://doi.org/10.1145/192161.192170) | 知覚系 = 仮想センサ(温度・単眼視)+ **perceptual focusser**。「it is crucial to **model the basic limitations of animal vision systems**, otherwise the perceptually driven behaviors will not be natural」。**intention generator** が意図の持続(persistence in intentions - no dithering)を作る | 二次(本文未読) |
| **O'Sullivan ら 2002**「Levels of Detail for Crowds and Groups」*CGF* 21(4):733-742 | ALOHA 枠組み。**幾何・動作に加えて行動(会話・社会)にも LOD を置いた系**。「each behaviour generator **annotates its generated behaviour with a visual salience parameter**, the LOD framework can selectively **drop behaviours** as the animated character moves further away or **out of the focus of attention**」。仮想視覚センサ+記憶で「remembered object location **without having to look at it**」 | **原典**(著者版 PDF 9 頁を実読) |

### 議事録との対応

| 議事録 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §17 | Attention は「何を見るか」を選ぶ機構。saliency と relevance(目標・社会・危険・新奇)を分離 | Corbetta & Shulman の背側(目標駆動)/腹側(刺激駆動)の 2 系がそのまま対応 | **一致** | 二次 |
| §17 | 「saliency ≠ interrupt」 | 腹側系が背側系の "circuit breaker" として働く=**顕著性が常に割り込むのではなく、行動的に関連するときに割り込む** | **一致** | 二次 |
| §17 | attention_target / attention_age / attention_confidence を持ち、小さな変化で切り替えない | Itti の IOR(注意した先へ戻りにくい)・Tu & Terzopoulos の「persistence in intentions - no dithering」・UE の Lose Sight Radius / Max Age | **一致** | C9 既出 + 二次 |
| §17 | 能動的知覚ループ(System 1 →「次にこれを見たい」→ Sensor) | Tu & Terzopoulos の perceptual focusser(意図が注意を絞る)が同型 | **一致** | 二次 |
| §1.2・§14 | World Truth ≠ Perception ≠ Belief。計画は自分の belief で立てる | Kuffner & Latombe 1999 が**実装として**そうしている(経路計画は記憶 M だけを障害物として使う) | **一致**(1999 年に実装済み) | 二次 |
| §18 | Perceptual LOD を **P0 presence / P1 coarse position / P2 category / P3 attribute / P4 identification / P5 semantic detail** の 6 段に切る | **この 6 段の対応物は見つからなかった**。段階化そのものは在る(O'Sullivan の behaviour LOD・Wißner の 8 段)が、いずれも**観測者からの距離で決まる計算量の段**であって**知覚の意味的な深さの段**ではない。v2 自身の人物知覚 4 段階([person-perception-verification](v2-person-perception-verification.md))が最も近い | **先行なし** | 原典 |

---

## §7 Q7 — 他者予測と局所回避(議事録 §11〜§14)

**既出**: Helbing & Molnár 1995 SFM・van den Berg ら 2011 ORCA(角でのデッドロック)・Weidmann 1993 の v_free 1.34 m/s・ρ_max 5.4・γ 1.913・Kladek 式・希望速度分布 1.00〜1.60 m/s は [R-7 §1・§3](v2-crowd-physics-research.md) と [C9 §1.2](v2-c9-position-attention-research.md) で確認済み(Weidmann 原典は取得不能=既知の空欄)。本節は**議事録に固有の 2 点**だけを扱う。

| 先行 | 事実・逐語・式 | 数値 | 確認 |
|---|---|---|---|
| **Moussaïd, Helbing & Theraulaz 2011**「How simple rules determine pedestrian behavior and crowd disasters」*PNAS* 108(17):6884-6888, [doi:10.1073/pnas.1016507108](https://doi.org/10.1073/pnas.1016507108)([arXiv:1105.2152](https://arxiv.org/abs/1105.2152)) | 「Here, a **novel cognitive science approach** is proposed, which is based on **behavioral heuristics**.」/「pedestrians apply **two simple cognitive procedures** to adapt their walking speeds and directions」。**H1(方向)**「A pedestrian chooses the direction α_des that allows the most direct path to destination point O_i, **taking into account the presence of obstacles**」= `d(α)² = d_max² + f(α)² − 2·d_max·f(α)·cos(α0 − α)` を最小化。**H2(速度)**「A pedestrian maintains a distance from the first obstacle in the chosen walking direction that ensures a **time to collision of at least τ**」= `v_des = min(v0, d_h/τ)`。加速は `dv/dt = (v_des − v)/τ` | **τ = 0.5 s・φ = 75°**(視野半角)。`f(α)` は方向 α に進んだときの最初の衝突までの距離、無ければ「horizon distance」d_max | **抄録**(arXiv abs は原典。式とパラメータは PNAS/PMC 本文の検索要約経由=**二次**。PMC は bot 遮断で本文未読) |
| 同上・創発 | 「predicts the emergence of self-organization phenomena, such as the **spontaneous formation of unidirectional lanes or stop-and-go waves**」/ 身体接触と併せると「**crowd turbulence at extreme densities**」 | — | **抄録**(arXiv abs) |
| 同上・**高密度の但し書き**(**第256 親訂正**) | ~~「physical interactions, rather than individual intentions, play the dominant role」~~ **この一文は原典に無い**(親が全文検索して 0 件)。原典の逐語は「In cases of overcrowding, **physical interactions between bodies may occur, causing unintentional movements that are not determined by the above heuristics.**」「at extreme densities, it is necessary to distinguish between the **intentional avoidance behavior** … and **unintentional movements resulting from interaction forces caused by collision with other bodies**」 | 密度の閾値は本文に無し。τ = 0.5 s は**逐語確認**・φ = 75° は**本文に無く親未確認** | **原典**(親) |
| **Karamouzas, Skinner & Guy 2014**「Universal power law governing pedestrian interactions」*PRL* 113:238701, [doi:10.1103/PhysRevLett.113.238701](https://doi.org/10.1103/PhysRevLett.113.238701)([arXiv:1412.1082](https://arxiv.org/abs/1412.1082)) | 相互作用は**物理的距離でなく、予想される衝突までの時間 τ(time-to-collision)**で決まる。「a simple power-law interaction that is based **not on the physical separation** between pedestrians **but on their projected time to a potential future collision**, and is therefore **fundamentally anticipatory in nature**」。近づく速さ v の別の依存性は見られず、τ で曲線が重なる | ポテンシャル `V(τ) = K·exp(−τ/τ_c)/τ^p`、**p = 2**・**τ_c = 3.0 s**(**二次**: 後続論文の要約)。データは Outdoor **119,774** ペア・Bottleneck **177,672** ペア・半径 **0.1 m** 仮定(補足資料) | 抄録+二次(PRL 本文未読) |

### 議事録との対応

| 議事録 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §12 | 局所的な「誰をどう避けるか」は System 1、軌道・速度・衝突判定は Engine | Moussaïd は**認知ヒューリスティック(方向と速度の選択)と物理接触力を明示的に分離**し、高密度でのみ後者が支配すると述べる | **一致** | 抄録 |
| §12 | 「障害物」でなく「**他人の今後の動きを予測する**」ことを重視 | Karamouzas が実データで示した相互作用則が **time-to-collision の関数**=先行が「予測的である」ことを測定で示している | **一致**(実データの裏づけあり) | 抄録+二次 |
| §14 | 他者表現を Presence / Kinematics / Behavioral prediction / Social relation の 4 段にする | Moussaïd の `f(α)` は**他者の歩行速度と体の大きさを考慮した衝突距離**=Kinematics 段まで。Social relation を局所回避に入れた先行は本調査では取れず | **部分一致** | 抄録 |
| §14 | 個人 + **群衆 summary**(density / dominant_direction / mean_speed …)の二重表現 | Moussaïd は「handling **simultaneous interactions among many individuals in an integrated way**」を売りにし、ペア相互作用の単純重ね合わせを否定した。summary を状態として持つ形の先行は本調査では取れず | **部分一致** | 抄録 |
| §13 | micro decision → meso flow → macro pattern。個人の回避が群衆の流れを変える | Moussaïd が**レーン形成と stop-and-go 波の自発的形成**を再現=支持。**ただし極端な密度では、ヒューリスティックで決まらない非意図的な動き(身体接触による)が加わる**と同じ論文が述べる(**第256 親訂正**: 「意図でなく物理接触が支配する」という強い言い方は原典に無い) | **部分一致**(意図の経路は成り立つが、極端な密度では非意図的な成分が加わる) | **原典**(親) |

---

## §8 Q8 — Agent-level simulation LOD(議事録 §28・§44)

### 8-1 系譜と比較表(Wißner, Kistler & André 2010, MIG 2010, LNCS 6459:206-217, **Table 1 を実読**)

| 先行 | LOD の決め方 | 段数 | LOD を適用する先 |
|---|---|---|---|
| **Chenney ら**(= Chenney & Forsyth, I3D **1997**) | potential visibility | **2** | updating movement |
| O'Sullivan ら 2002 | distance | 不明記 | geometry, animations, collision avoidance, gestures and facial expressions, **action selection** |
| Brockington 2002(*AI Game Programming Wisdom*・Neverwinter Nights) | distance | **5** | **scheduling**, navigation, action selection in combat |
| **Niederberger & Gross 2005**(*Visual Computer* 21:188-202) | distance and visibility | **21** | **scheduling**, collision avoidance, path planning, group decisions |
| Pettré ら | distance and visibility | 5 | geometry, updating movement, collision avoidance, navigation |
| **Brom, Šerý & Poch 2007**(IVA 2007, LNCS 4722:1-14) | simplified distance | **4** | action selection (AND-OR trees), **environment simplification** |
| Paris ら(CA-LOD) | distance | 3 | navigation, collision avoidance |
| Lin & Pan / Osborne & Dickinson | distance | 不明記 | geometry・animations / navigation, flocking, group decisions |
| **Wißner ら 2010 自身** | distance **and visibility** | **8** | updating movement, collision avoidance, navigation, action selection |

**表に載る全系統が「観測者(カメラ)からの距離と可視性」で LOD を決めている。**

### 8-2 数値

| 出典 | 数値 | 確認 |
|---|---|---|
| **Wißner ら 2010 性能評価** | Augsburg3D に **50 / 100 / 150 / 250 体**、各構成 **5 run × 45 s**(計 20 run/版)、カメラ固定。LOD 版は「an **increased frame rate** as well as a **slower decline** of the frame rate for larger numbers of agents」(具体のフレームレートは図 5 のみ=空欄)。機器は Core 2 Quad Q9550 / GTS 250 | **原典**(数値は図) |
| **Wißner ら 2010 知覚調査** | **N=108**(男 69・女 39・15〜46 歳)・7 件法・動画 30 s。Augsburg3D: 通常版が有意に busy(**4.61 vs 5.17**, t(107)=−4.599, p<0.001)だが **LOD 版が believable で有意に上**(**3.81 vs 3.49**, t(107)=2.040, p<0.05)。Beer Garden は逆で busy のみ有意(**3.89 vs 3.54**, t(107)=3.930, p<0.001)。効果量は中〜小 | **原典** |
| **更新頻度の式**(Wißner) | `f_update(x) = 1/t(x)` if `lod(x) > criticalLOD(x)` else ∞、`t(x) = 0.55·lod'(x) − 0.5`、`lod'(x)=lod(x)−criticalLOD(x)`。criticalLOD=3 のとき LOD 0-3 = ∞(毎フレーム)・LOD 4 = **20**・5 = **1.66**・6 = **0.87**・7 = **0.59** 更新/秒 | **原典** |
| **Chenney & Forsyth 1997**「View-Dependent Culling of Dynamic Systems in Virtual Environments」I3D '97:55-58, [doi:10.1145/253284.253307](https://doi.org/10.1145/253284.253307) | 「culling moving objects by **not solving the equations of motion** of objects that don't affect the view」。2 つの問題を名指し: 「**consistency** - ensuring that objects that come back into view do so in the right state - and **completeness** - ensuring that objects that would have entered the view volume as a result of their motions, do so」 | 二次(ACM DL 抄録経由) |
| **Chenney, Arikan & Forsyth 2001**「Proxy Simulations For Efficient Dynamics」Eurographics 2001 Short | 「A **proxy** takes the place of an accurate simulation for objects that are out of view … A proxy must ensure that objects **enter the view at reasonable times** throughout the simulation and **in states that reflect their time spent out of view**.」例は都市交通と多エージェント経路計画。「dynamics computation **speedups of over two orders of magnitude**」 | 二次(**PDF は接続拒否で未取得**=§9-4) |
| **Niederberger & Gross 2005** | 「A special **scheduling algorithm distributes this time to the agents** depending on their level-of-detail such that **visible and nearby agents get more time** than invisible or distant agents.」/「**The time available per agent influences the proactive behavior, which becomes more sophisticated because it can spend time anticipating future situations.**」 | 抄録(Springer) |
| **Brom, Šerý & Poch 2007** | 「**Simulation LOD reduces quality of the simulation at the places unseen.** Contrary to graphical LOD, simulation LOD has been **almost unstudied**.」/ 主な特徴は「it allows for **several degrees of detail**, i.e. for gradual varying of simulation quality」 | 抄録(Springer) |

### 8-3 議事録との対応

| 議事録 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §28 | Perceptual LOD と Agent Simulation LOD を**別物として分ける** | Brom ら 2007 が同じ区別を立てている(graphical LOD vs simulation LOD)。O'Sullivan 2002 は幾何・動作・行動を別レイヤに置いた | **一致** | 原典+抄録 |
| §28 | L0 Dormant / Event Driven(重要 Event でのみ wake) | Chenney & Forsyth 1997 の culling と 2001 の proxy がまさにこれ。ただし先行は**戻ってきたときの状態の整合(consistency)と、視野に入るべきものが入ること(completeness)を明示の要求として立てている** | **一致**(要求は先行のほうが厳しい) | 二次 |
| §28 | 4 段(L0 Dormant / L1 Mesoscopic / L2 Local Cognitive / L3 Deep Cognitive) | 先行の段数は 2 / 3 / 4 / 5 / 8 / 21 とばらつく。**4 段は Brom らと同数**で範囲内 | **一致** | 原典 |
| §28 | LOD の決め方 = interaction_density / event_rate / uncertainty / goal_relevance / social_relevance / physical_risk / cognitive_activity(**エージェント自身の状況**) | **Table 1 の全系統が観測者(カメラ距離・可視性)で決めている**。エージェント自身の内部状態で LOD を決めた先行は本調査では見つからなかった | **先行なし** | **原典** |
| §28 | 「**compute scheduling ≠ cognitive ability**」=資源不足で人格や能力を下げるのではない | **Niederberger & Gross 2005 は逆**: 配られた時間が proactive behavior の洗練度を決める(時間が多いほど先読みできる)。Wißner らも後続に「行動の多様性・異質性が LOD で減る」と要約されている | **矛盾** | 抄録+二次 |
| §28 | 昇降の切り替えで挙動が破綻しないこと | Wißner ら「Applying the behavior reduction at the **behavior execution level** also provides us with **high consistency during LOD changes**.」+ 知覚調査で**利用者は差にほぼ気づかない**(有意差 3 つのうち 2 つは LOD 版に有利) | **一致**(検査の型が先行にある) | **原典** |
| §44 | L0 50% / L1 40% / L2 9% / L3 1% は仮例で実分布は測る | 先行に分布の実測値は無い(いずれもカメラ基準なのでシーン依存) | **先行なし** | 原典 |

---

## §9 親への確認依頼(自信のない主張・名指し・5 件)

1. **§1-2 の Botvinick の葛藤の式**(`energy = max(0, −2·(a_L·a_R·w_ij))`)は **2025 年 *Psychophysiology* の再実装論文の記述を経由した二次**で、**原典本文は読めていない**。「Hopfield energy」という定性の言い方までは複数の二次で一致するが、**係数 −2 と 0 フロアが原典にあるとは言えない**。設計書へ数値として写さないこと。
2. **§2-2 の「dynamism ≈ 28」**は Schut & Wooldridge 本文の逐語だが、**同論文の dynamism のスケールは Kinny & Georgeff の γ とは別の定義**(clock rate 比 vs 穴の出現分布)。**2 つを同じ軸として並べないこと**。
3. **§2-1 の「γ を 2^5 の範囲で振った」**は、抽出テキストが「a 25 range of values in 7」となっており **`2^5` と `γ` が抽出で壊れている**。親が PDF の図 1 の横軸で確認してほしい。同じ理由で ε の具体値も図からしか取れない。
4. **§8 の Chenney & Forsyth**: 依頼文は「Chenney & Forsyth 2001」だったが、**view-dependent culling は 1997 年の I3D 論文**で、2001 年のものは Chenney, Arikan & Forsyth の Proxy Simulations(Eurographics short)。**「two orders of magnitude」は PDF が接続拒否で未取得の二次**。
5. **§3 全体**: 「高次推論のコンパイルで**どれだけ速くなるか**」の数値を **1 つも取れていない**(Taatgen & Lee の速度向上・Soar chunking の決定回数・Logan の指数・Newell & Rosenbloom Table I)。議事録 §20 と原則 L を採る場合、**速度則の数値は現時点で空欄**であり、v2 が数字を置けばそれは設計者の指紋になる。

---

## §10 空欄(調べられなかったこと)

| 項目 | 理由 |
|---|---|
| Botvinick ら 2001 本文(葛藤の式・ACC のフィッティング値) | APA 有料。PsyNeuLink の実装ページには式が無い |
| Thompson ら 2011 本文(FOR と答え変更率の相関・回帰係数) | ScienceDirect 有料。抄録のみ |
| Clark 2013 §3.3〜§5 | Cambridge Core の本文が §3.3 の途中で切断 |
| Stanovich 2009 / 2011 本文 | 著者公開 PDF に到達できず。引用経由 |
| arXiv:2505.18962(System-1.5 Reasoning)本文 | 検索要約のみ。20×・92.31% は二次 |
| Kinny & Georgeff の図 1〜10 の数値(ε の値・交差点の γ) | 本文に数値が無く図のみ |
| Fox ら 2006 の CPU 時間(図 1〜10) | 同上。表は 880 variants の 4 列だけ |
| Taatgen & Lee 2003 本文・Laird ら 1986 §4 の数値 | SAGE 有料・著者サイト 404 / Springer 有料 |
| Logan 1988 本文(べき関数の当てはめ値) | 著者公開 PDF(Vanderbilt)が接続拒否 |
| Newell & Rosenbloom 1981 Table I(指数の実値) | 書籍章。指数 ≈0.4 は三次で**採らない** |
| PIANO のモジュール遅延・tick 率・stale の扱い | **本文に記述が無い**(記述の不在を確認) |
| RRARA / Real-Time Reasoning Agents / GPTNT の本文と数値 | 抄録・検索要約のみ |
| Soar の impasse の原典逐語(arXiv:2205.03854 本文) | 未読。検索要約経由 |
| ACT-R の buffer / conflict resolution・EPIC の割り込み機構 | **未着手** |
| Zilberstein 1996 本文・Russell & Zilberstein 1991 の証明 | UMass 公開 PDF 未取得。加速比 4 は二次 |
| Corbetta & Shulman 2002 本文 | Nature 有料。抄録経由 |
| Noser ら 1995・Kuffner & Latombe 1999・Tu & Terzopoulos 1994 の本文 | Elsevier 有料 / 著者 PDF 未取得。検索要約経由 |
| Moussaïd 2011 本文(式・τ・φ・密度の閾値) | PNAS/PMC が bot 遮断。**arXiv abs は原典・式は二次** |
| Karamouzas 2014 本文(p=2・τ_c=3.0 s の出所) | PRL 有料。補足資料の数は二次 |
| Chenney & Forsyth 1997 / 2001 本文 | ACM DL 抄録のみ / proxysim.pdf は接続拒否 |
| Niederberger & Gross 2005・Brom ら 2007・Brockington 2002 本文 | Springer 有料 / 書籍章 |
| ABM の「event-driven agents」・MMO サーバー側の LOD の一次資料 | **未着手**(議事録 §28・§44 の残り) |
| 「知覚の意味的段階を 6 段で切った」先行 | 探索範囲で見つからず。**無いことの証明ではない** |
| 議事録 §26(causal depth)・§27(会話の 5 タイムスタンプ)の先行 | 依頼の Q1〜Q8 に含まれないため**未着手** |

---

## §11 出典一覧

| # | 題 | URL / DOI | 確認 |
|---|---|---|---|
| 1 | System-1.5 Reasoning: Traversal in Language and Latent Spaces with Dynamic Shortcuts (2025) | https://arxiv.org/abs/2505.18962 | 二次 |
| 2 | Botvinick M. ほか (2001) Conflict monitoring and cognitive control. *Psychol Rev* 108(3):624-652 | https://doi.org/10.1037/0033-295X.108.3.624 | 二次(式) |
| 3 | Thompson V.A., Prowse Turner J.A., Pennycook G. (2011) Intuition, reason, and metacognition. *Cognitive Psychology* 63(3):107-140 | https://doi.org/10.1016/j.cogpsych.2011.06.001 | 抄録 |
| 4 | Clark A. (2013) Whatever next? Predictive brains, situated agents, and the future of cognitive science. *BBS* 36(3):181-204 | https://doi.org/10.1017/S0140525X12000477 | **原典**(§2.3・§3.1) |
| 5 | Stanovich K. (2009) Distinguishing the reflective, algorithmic, and autonomous minds, in Evans & Frankish (eds.) *In Two Minds*, 55-88 | http://keithstanovich.com/Site/Research_on_Reasoning_files/Stanovich_Two_MInds.pdf | 二次 |
| 6 | Kinny D., Georgeff M. (1991) Commitment and Effectiveness of Situated Agents. IJCAI-91, 82-88 | https://www.ijcai.org/Proceedings/91-1/Papers/014.pdf | **原典**(全 7 頁) |
| 7 | Schut M., Wooldridge M. (2001) Principles of Intention Reconsideration. AGENTS'01 | https://www.cs.vu.nl/~schut/pubs/Schut/2001.pdf | **原典**(全 8 頁) |
| 8 | Fox M., Gerevini A., Long D., Serina I. (2006) Plan Stability: Replanning versus Plan Repair. ICAPS-06, 212-221 | https://cdn.aaai.org/ICAPS/2006/ICAPS06-022.pdf | **原典**(全 10 頁) |
| 9 | Pettersson O. (2005) Execution monitoring in robotics: A survey. *RAS* 53(2):73-88 | https://doi.org/10.1016/j.robot.2005.09.004 | 抄録 |
| 10 | Laird J.E., Rosenbloom P.S., Newell A. (1986) Chunking in Soar. *Machine Learning* 1(1):11-46 | https://doi.org/10.1007/BF00116249 | 抄録 |
| 11 | Taatgen N.A., Lee F.J. (2003) Production Compilation. *Human Factors* 45(1):61-76 | https://doi.org/10.1518/hfes.45.1.61.27224 | 二次 |
| 12 | Logan G.D. (1988) Toward an instance theory of automatization. *Psychol Rev* 95(4):492-527 | https://doi.org/10.1037/0033-295X.95.4.492 | 二次 |
| 13 | Newell A., Rosenbloom P.S. (1981) Mechanisms of skill acquisition and the law of practice | https://apps.dtic.mil/sti/citations/ADA096527 | 二次 |
| 14 | Sumers T., Yao S., Narasimhan K., Griffiths T. (2023) Cognitive Architectures for Language Agents. TMLR 2024 | https://arxiv.org/abs/2309.02427 | **原典**(TMLR 版 32 頁) |
| 15 | Altera.AL ほか (2024) Project Sid(**§2 PIANO のみ**) | https://arxiv.org/abs/2411.00114 | **原典**(HTML v1 §2・§5.1) |
| 16 | Zheng Y., Mao S., Zhang D., Cai W. (2025) LLM-Enhanced Rapid-Reflex Async-Reflect Embodied Agent (RRARA) | https://arxiv.org/abs/2506.07223 | 抄録 |
| 17 | Real-Time Reasoning Agents (ICLR 2026) | https://proceedings.iclr.cc/paper_files/paper/2026/file/ccbe16043125599293b01dd467c260f3-Paper-Conference.pdf | 二次 |
| 18 | Laird J.E. (2022) Introduction to the Soar Cognitive Architecture | https://arxiv.org/abs/2205.03854 | 二次 |
| 19 | Zilberstein S. (1996) Using Anytime Algorithms in Intelligent Systems. *AI Magazine* 17(3):73-83 | https://doi.org/10.1609/aimag.v17i3.1232 | 二次 |
| 20 | Corbetta M., Shulman G. (2002) Control of goal-directed and stimulus-driven attention in the brain. *Nat Rev Neurosci* 3:201-215 | https://doi.org/10.1038/nrn755 | 二次 |
| 21 | Noser H. ほか (1995) Navigation for Digital Actors based on Synthetic Vision, Memory and Learning. *Computers & Graphics* 19(1):7-19 | https://doi.org/10.1016/0097-8493(94)00117-H | 二次 |
| 22 | Kuffner J., Latombe J.-C. (1999) Fast synthetic vision, memory, and learning models for virtual humans. *Computer Animation '99*, 118-127 | http://kuffner.org/james/papers/kuffner_ca1999.pdf | 二次 |
| 23 | Tu X., Terzopoulos D. (1994) Artificial fishes: physics, locomotion, perception, behavior. SIGGRAPH '94, 43-50 | https://doi.org/10.1145/192161.192170 | 二次 |
| 24 | O'Sullivan C. ほか (2002) Levels of Detail for Crowds and Groups. *Computer Graphics Forum* 21(4):733-742 | https://doi.org/10.1111/1467-8659.00631 | **原典**(著者版 PDF 9 頁) |
| 25 | Moussaïd M., Helbing D., Theraulaz G. (2011) How simple rules determine pedestrian behavior and crowd disasters. *PNAS* 108(17):6884-6888 | https://doi.org/10.1073/pnas.1016507108 / https://arxiv.org/abs/1105.2152 | 抄録(式は二次) |
| 26 | Karamouzas I., Skinner B., Guy S.J. (2014) Universal power law governing pedestrian interactions. *PRL* 113:238701 | https://doi.org/10.1103/PhysRevLett.113.238701 / https://arxiv.org/abs/1412.1082 | 抄録+二次 |
| 27 | Chenney S., Forsyth D. (1997) View-Dependent Culling of Dynamic Systems in Virtual Environments. I3D '97, 55-58 | https://doi.org/10.1145/253284.253307 | 二次 |
| 28 | Chenney S., Arikan O., Forsyth D. (2001) Proxy Simulations For Efficient Dynamics. Eurographics 2001 Short | http://luthuli.cs.uiuc.edu/~daf/papers/proxysim.pdf | 二次(**未取得**) |
| 29 | Niederberger C., Gross M. (2005) Level-of-detail for cognitive real-time characters. *The Visual Computer* 21:188-202 | https://doi.org/10.1007/s00371-005-0279-1 | 抄録 |
| 30 | Brom C., Šerý O., Poch T. (2007) Simulation Level of Detail for Virtual Humans. IVA 2007, LNCS 4722:1-14 | https://doi.org/10.1007/978-3-540-74997-4_1 | 抄録 |
| 31 | Wißner M., Kistler F., André E. (2010) Level of Detail AI for Virtual Characters in Games and Simulation. MIG 2010, LNCS 6459:206-217 | https://doi.org/10.1007/978-3-642-16958-8_20 | **原典**(全 12 頁) |
| 32 | Brockington M. (2002) Level-Of-Detail AI for a Large Role-Playing Game, in *AI Game Programming Wisdom*, 419-425 | 書籍(ISBN 1-58450-077-8) | 二次(#31 Table 1 経由) |

**リポ内の既存答申(本書が引くだけにしたもの)**: [R-39](v2-r39-judgment-share-research.md)(二重過程・メタ推論・cascade)・[R-38](v2-r38-closed-output-judges-research.md)(蒸留・lookup 表)・[thought-frequency-anchors-note](v2-thought-frequency-anchors-note.md)(思考頻度)・[D-71 答申](v2-d71-vocab-growth-research.md)(技能庫・affordance)・[C9 答申](v2-c9-position-attention-research.md)(注意の焦点・歩行速度)・[R-7 答申](v2-crowd-physics-research.md)(群衆物理)・[r23-primary-check-batch2](v2-r23-primary-check-batch2.md)(第210 訂正)・[lit/css__projectsid2024_de-novo-limit](lit/css__projectsid2024_de-novo-limit.md)。
