# R-42 認知・社会アーキテクチャ議事録の先行検証(社会側 §26〜§33・方法論側 §34〜§43)

<!-- hdr:v1 -->
- **分野**: ABM方法論 #21 / 検証とV&V・UQ #22 / 計算社会科学 #25 / 社会ネットワーク科学 #14 / 歩行者動力学 #18 / 認知科学(記憶・習慣) #12 | **重要度**: **P0**
- **一次確認**: **B** = サブ実読(原典 3・抄録 7・二次 29・2026-09-23・第255)+**親検収 4 件の逐語**(Moussaïd 2010 本文・Lamport 1978 PDF・Sen & Airiau 2007 PDF・Galán & Izquierdo 2005 本文=第256・下の検収欄)。Axelrod 1986 本文・Park 2023 の TrueSkill 表・Huberman & Glance 本文は親未読。等級を A にしていないのは原典を本文まで読めたのが 3 本のみのため
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 対象: ユーザーが別チャットでまとめた設計議事録(スクラッチパッド `minutes_cognitive_social_2026-09-23.md`・全 3,069 行を実読)の **社会側 §26〜§33** と **方法論側 §34〜§43**。
> **設計評価はしない**。各主張について先行研究・先行実装が何を言っているか(事実と数値)と、議事録の主張が先行と **一致 / 部分一致 / 矛盾 / 先行なし** のどれかだけを報告する。
> **調べ方**: ①既存答申・設計書を先に読み(`INDEX.md`・`v2-methodology.md`・`v2-r23-primary-check-batch2.md`・`v2-architecture-overview-detailed.md` §4/§5/§10・`v2-run-manifest-concurrency-research.md`・`lit/` 120 本の一覧)、既出は「答申 X で既出」と引くだけにした。②残った穴だけを Web で調べた。③PDF は WebFetch が保存したものをシステム python の pymupdf で本文抽出(記憶 `windows-pdf-workflow` の手順)。④**読めなかったものは §11 に「空欄」として挙げ、記憶で埋めていない**。
> 作業日 2026-09-23。答申本体・台帳・設計書は**一行も編集していない**。

---

> **親検収(2026-09-23・第256・Fable 5.1)**: 結論を変える主張 4 件を親が原典で確認した(WebFetch 本文 / 著者公式 PDF を pymupdf 抽出)。
> - **✓ Moussaïd 2010 PLoS ONE**(本文 HTML): 「up to 70% of people in a crowd are actually moving in groups」/「the proportion of pedestrians belonging to a group is 55% in population A and 70% in population B」/「NA = 260 groups in population A and NB = 1093 groups in population B」/「A total of 1098 and 3461 pedestrians were tracked」/「zero-truncated Poisson distribution (p = 0.06」/「V-like … "non-aerodynamic" shape」/「ANCOVA, p = 0.19 … y = −0.04x+1.26 … y = −0.08x+1.24」を逐語確認。**λ = 0.83 / 1.11 は図 1 の画像内で本文テキストには無い=親未確認**。
> - **✓ Lamport 1978**(著者公式 PDF): 「only a partial ordering of the events in the system」/「To break ties, we use any arbitrary total ordering < of the processes.」/「The total ordering defined by the algorithm is somewhat arbitrary. It can produce anomalous behavior if it disagrees with the ordering perceived by the system's users.」を逐語確認。**サブの引用と一致**。
> - **✓ Sen & Airiau 2007**(著者公式 PDF): 「a uniform norm always emerges in a population of three or more agents」/「a population of 200 agents using WoLF, we ran 1,000 runs … "yield to the left" norm 482 times, and "yield to the right" norm 518 times」/ 図 1 説明「with more agents, it takes longer for the entire population to converge」を逐語確認。
> - **✓ Galán & Izquierdo 2005 JASSS**(本文): 「Axelrod's results are not as reliable as one would desire」/「We can obtain the opposite results by running the model for longer, by slightly modifying some of the parameters」/ 規範ゲームの要約「states of very high Boldness and very low Vengefulness … the norm has collapsed」/「metanorms do not prevent defections most of the time in the long-term」を確認。→ **§4 の「矛盾」判定は Axelrod 1986 単独では立たない**(再実装で逆転する)。残る根拠は Sen & Airiau の「衝突の負の報酬」(罰の一種)と Ashery 2025(v2 既出・親確認済み)。判定を「矛盾」から「**部分矛盾(罰または負の報酬なしに規範が立った先行は見つからない)**」へ弱めて読むこと。
> - **△ 親も未読**: Axelrod 1986 本文・Huberman & Glance 1993 本文・Park 2023 の TrueSkill 表(arXiv abs には数値なし=**二次のまま**)。
> - **サブの確認依頼 5 件への回答**: ① Moussaïd の 55/70 と N は設計書へ写すときに**併記**(写し検査)。② Hegselmann 2023 の訂正伝播: 設計書に Hegselmann の引用は無い(grep 0 件)=対象なし。③ **スクランブル通行量の出所**: 設計書 3 か所が holdout 行として挙げるが、`data/ground_truth/registry.yaml` に交差点/scramble のアンカーは無く `docs/data-license-ledger.md` にも行が無い=**出所未登録**。3,000 の伝聞値は v2 のどこにも書かれていない(値を書いていない)が、封印データの実体が何かを U-9 で確定する。④ Axelrod 1986 は**再現批判つき**として扱う(上)。⑤ Baker 2009 の r は使わない(空欄のまま)。
> - **親の再計算**: 議事録 §42 の腕の積 3×5×5×4×4×4×5×5×6 = **720,000**(サブと一致。監査文書の「36 万」は親の計算誤り → 第256 で訂正)。

---

## §1 更新順序と同時性(議事録 §26)

### 1-1 既出(重複調査していない)

- **[v2-run-manifest-concurrency-research.md](v2-run-manifest-concurrency-research.md) §3.1〜§3.4** が本問いのほぼ全体を既に扱っている: NetLogo `ask`=常にランダム順の逐次(実読)・Mesa の 4 型(sequential / random `shuffle_do` / **simultaneous**(step→advance)/ staged)と「the order in which agents act can significantly affect model outcomes」(実読)・Agents.jl のスケジューラ抽象(実読)・**Weimer et al. 2019 JASSS 22(4)5**「Varying synchrony in all cases altered the relationship between the convergence parameter and the variance in opinions」(実読)・FLAME GPU 2 の bidding と「アトミック演算の順序は非決定的」(PDF 実読)・DEVS の `select`(未読・二次)。
- 同答申 §3.4 と [v2-architecture-overview-detailed.md](../design/v2-architecture-overview-detailed.md) §4 が **二相コミット + ハッシュ優先度キー** `pk=(ceil_ns(t_notice), blake3(run_salt‖tick‖resource_id‖agent_id))` を既に持つ。同 §4 ① の `t_apply = 起床tick + δ_perc + δ_think` も既決。
- 同答申 問4 の結論「楽観同期(Time Warp)は要らない・要るのは lookahead 概念だけ」も既出。

### 1-2 本批で新しく当たった先行

| 先行 | 逐語(原典) | 確認 |
|---|---|---|
| **Lamport 1978** *CACM* 21(7):558–565 | 「The relation "happened before" is therefore only a **partial ordering** of the events in the system.」/ 総順序化の節「To break ties, we use **any arbitrary total ordering < of the processes**.」/ 結論「The total ordering defined by the algorithm is **somewhat arbitrary**. It can produce anomalous behavior if it disagrees with the ordering perceived by the system's users.」 | **原典**(著者公式 PDF を pymupdf 抽出) |
| **Huberman & Glance 1993** *PNAS* 90(16):7716–7718 | 抄録「if such a simulation imposes space-time granularity, then its ability to describe the real world may be compromised」「the results of digital simulations regarding territoriality and cooperation **differ greatly when time is discrete as opposed to continuous**」。Nowak & May 1992 *Nature* 359:826(同期更新で協力が持続)への直接の反証で、非同期(random sequential)にすると漸近的協力が消えた | **抄録**(PNAS 本文は 403。**定量値は未取得** → §11) |
| **Cornforth, Green & Newth 2005** *Physica D* 204(1–2):70–82 | 抄録「the type of update scheme **strongly affects** the dynamic characteristics of the system」「**global synchronisation can arise from local temporal coupling**」「possible to switch between chaotic, cyclic and modular behaviour by varying a single parameter」。同期 / ランダム非同期 / **順序つき非同期** の 3 分類 | **抄録**(ScienceDirect 本文未取得) |
| **Caron-Lormier et al. 2008** *Ecol. Modelling* 212(3–4):522–527 | — | **未読**(既存答申でも Elsevier 403 で空欄。本批でも取れず) |
| **Jefferson 1985** *ACM TOPLAS* 7(3):404–425(Virtual Time) | — | **未読**(既存答申 問4 で「要らない」と判断済み・本文は取れず) |
| Railsback & Grimm の教科書のスケジューリング論 | — | **未読**(書籍。既存答申は代わりに Mesa/NetLogo/Agents.jl の実装文書を実読している) |

### 1-3 議事録との対応

| 議事録の節 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §26 | 「同じ simulation timestamp の Agent は、原則として同じ commit 済み World State を参照する」 | Mesa の `simultaneous`(step→advance)と同一の定義。ただし NetLogo は 4.0 以降これを捨ててランダム順の逐次に振った(既出答申 §3.1) | **一致**(定義として) | 既出=実読 |
| §26 | 「A を CPU で先に処理したことで B だけが『A がすでに動いた世界』を見る順序依存を避ける」 | Weimer 2019「No schedule completely eliminated the effect of biased ordering」=**順序バイアスはどの方式でも完全には消えない** | **部分一致**(同期更新で消えるのは「当 tick 内の伝播」であって順序バイアス一般ではない) | 既出=実読 |
| §26 | 同期/非同期の選択そのものが結果を変えるか | Huberman & Glance 1993(協力が消える)・Cornforth 2005(カオス/周期/モジュラが切り替わる)・Weimer 2019(意見分散が変わる)の 3 本が独立に「変わる」と報告 | **一致** | 抄録 ×2 / 実読 ×1 |
| §26 | `(timestamp, causal_depth)` という順序概念 | Lamport 1978 の **happened-before 半順序 + 任意の全順序でタイブレーク** がまさにこの形。v2 の `pk` はその「任意の全順序」に相当 | **一致** | **原典** |
| §26 | 「一定 causal depth で次の time slice へ送る」(無限相互反応の打ち切り) | Lamport には打ち切りの概念は無い(半順序は有限事象上で定義される)。既出答申 §3.4 の「反復は 1 回だけ、以降は次 tick」が最も近い先行実務(FLAME GPU 2 の sub-model は固定回数だと最悪 9 回必要) | **部分一致**(打ち切り規則そのものの先行は特定できず) | 原典+既出 |

---

## §2 会話の伝播時間差(議事録 §27)

議事録は `emitted_at / arrives_at / perceived_at / interpreted_at / response_ready_at` の **5 時刻**を候補に挙げる。

| 先行 | 内容 | 確認 |
|---|---|---|
| Cooperation Breakdown in LLM Agents Under Communication Delays(arXiv 2602.11754) | 送信時刻とサーバクロックの状態更新時刻を分け、遅延到着による「asynchronous mutual perception」を作る。遅延を**指示していないのに**エージェントが遅延を突く搾取戦略を選んだと報告 | **二次**(検索要約) |
| Real-Time Deadlines Reveal Temporal Awareness Failures in LLM Strategic Dialogues(arXiv 2601.13206) | 交渉エンジンに explicit speech-latency model を入れ、発話ごとに遅延を課す(「Real-time simulation and message latency」節) | **二次** |
| Time to Talk: LLM Agents for Asynchronous Group Communication in Mafia Games(arXiv 2506.05309) | **scheduler(いつ話すか)と generator(何を話すか)を分離**。送信前に「平均 1 語/秒」のタイピング遅延を挟む | **二次** |
| Your LLM Agents are Temporally Blind(arXiv 2510.23853) | メッセージ完了時刻を ISO 8601 で全ターンに付与し、読速・書速・生成速から遅延を標本化 | **二次** |
| SyncLLM / Beyond Turn-Based Interfaces(EMNLP 2024, aclanthology 2024.emnlp-main.1192) | LLM に実時計を持たせ、最大 240 ms の遅延下で全二重対話 | **二次** |

**議事録との対応**

| 議事録の節 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §27 | 発話 → 伝播 → 知覚 → 解釈 → 決定 → 応答 に時間差がある | 上記 5 本が「遅延を明示的に持たせる」までは行っている | **一致**(遅延の存在) | 二次 |
| §27 | **5 つの時刻を別々に持つ**(emitted/arrives/perceived/interpreted/response_ready) | どの先行も最大 2〜3 時刻(送信 / 到着 / 応答準備)。5 分割した先行は見つからなかった | **先行なし** | 二次 |
| §27 | 「A が考えている間にも B が話せる。追加発話が重要なら A の推論を更新/中断できる」 | Time to Talk の高頻度サンプリング scheduler が最も近いが、**進行中の推論への割り込み**は扱っていない | **部分一致** | 二次 |

> 注: v2 側は既に `δ_perc + δ_think → t_apply`([architecture-overview-detailed](../design/v2-architecture-overview-detailed.md) §4 ①)を持ち、会話は `engine/conversation.py` が別管理(同 §4 末)。上の 5 時刻のうち 3 つ(emitted 相当=起床 tick、perceived 相当=+δ_perc、response_ready 相当=+δ_think)に対応する量が既にある。

---

## §3 Group の形成(議事録 §29)

### 3-1 Moussaïd et al. 2010 *PLoS ONE* 5(4):e10047 — **原典実読(逐語)**

| 量 | 逐語 |
|---|---|
| 集団で歩く割合 | 抄録「it turns out that **up to 70%** of people in a crowd are actually moving in groups」/ 結果「the proportion of pedestrians belonging to a group is **55% in population A and 70% in population B**」/ 考察「only **one third** of observed pedestrians were walking alone」 |
| 標本 | 抄録「approximately **1500** pedestrian groups」/ 本文「**NA=260** groups in population A and **NB=1093** groups in population B composed of two to four members」/ 手法「A total of **1098 and 3461 pedestrians** were tracked in population A and B respectively」 |
| 集団サイズ分布 | 「the size of pedestrian groups in population A follows a **zero-truncated Poisson distribution (p=0.06**; on the basis of χ²-test)」/ B は「the proportion of single pedestrians is lower than a Poisson distribution would predict, while the proportion of groups of size 2 is greater than expected (**p<0.01**)」/ 図1 凡例「**λ = 0.83 と 1.11**(A / B)」 |
| V 字 | 抄録「the linear walking formation is bent forward, turning it into a **V-like pattern**」「the V-like walking pattern facilitates social interactions within the group, but **reduces the flow** because of its "**non-aerodynamic**" shape」 |
| 速度低下(実測) | 「pedestrian walking speeds decrease linearly with growing group size … (**ANCOVA, p=0.19**, with **y=−0.04x+1.26** in population A and **y=−0.08x+1.24** in population B)」 |
| 速度低下(模型) | 「An ANCOVA test delivers a p-value of **0.071** … with **y=−0.05x+1.3** at low density and **y=−0.07x+1.2** at moderate density」 |
| 社会的相互作用の強さ α₁ の 1 因子比較 | 「When setting α₁=0, group members only try to stick together with no communication rule, and tend to form an "aerodynamic" **inverse V-like shape**. In contrast, for the realistic value **α₁=4**, groups form the observed forwardly directed V-like pattern」 |

- **文脈依存の警告(二次)**: Nicolas & Hassan 2023 のレビューは「depending on the context, the proportion of single pedestrians may range from as low as a few percent … up to more than **80%**, in an underground pedestrian facility in Japan (Zanlungo et al., 2014)」とし、「it makes little sense to reason in terms of a context-independent average proportion of social groups」と書く。
- 既存 [v2-person-perception-verification.md](v2-person-perception-verification.md):73,172 が同論文を「最大70%」で引いている。**原典の "up to 70%" と一致**。ただし 55%/70% の二値・N(260/1093 群)は設計書側に写っていない。

### 3-2 段階モデル

- **Tuckman 1965** *Psychological Bulletin* 63:384–399 — 約 **50 本**の研究のレビューから forming / storming / norming / performing を抽出(対人関係の領域 と 課題活動の領域 の **2 領域**)。**Tuckman & Jensen 1977** が 22 本を再検討し adjourning を追加、「Of the twenty-two studies reviewed, **only one** set out to directly test this hypothesis」。確認=**二次**。
- **Qiu & Hu 2010** 等の小集団入り群衆モデル: **未読**(本批で本文に到達できず → §11)。
- ABM で「近接 → 反復相互作用 → 共有目標 → 安定集団」の段階を**実装して検証した**先行: 本批の範囲では特定できなかった(→ §11)。

### 3-3 議事録との対応

| 議事録の節 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §29 | Group は自然発生的な行動上のまとまり(友人・一緒に歩く人) | Moussaïd 2010 が「歩行者の 55〜70% が集団」と実測。集団は**既定の存在**であって歩行中に形成されるものとしては測られていない | **部分一致** | **原典** |
| §29 | 「proximity → repeated interaction → coordinated activity → shared goal → stable group」 | Tuckman 1965 の 4 段は**対人関係と課題の 2 領域**で切っており、近接や反復相互作用から始まらない。段階の数が近いだけ | **部分一致** | 二次 |
| §29 | membership の 6 段(stranger → … → explicit membership) | 対応する先行を特定できず | **先行なし** | — |
| §29 | 「World Truth 上の Group と、Agent がそう信じている Group は区別する」 | Moussaïd 2010 は group membership を観察者側の基準(「a clear social interaction among group members」)で同定=**World Truth 側のみ**。Agent 側の信念との区別を扱った歩行者先行は無い | **先行なし** | **原典** |
| §29 | Group Goal と Individual Goal の競合が cohesion を左右する | Moussaïd 2010 の「trade-off between walking faster and facilitating social exchange」が唯一の実測された競合。**定量は速度勾配のみ** | **部分一致** | **原典** |

---

## §4 Norm の創発(議事録 §30)

| 先行 | 内容・数値 | 確認 |
|---|---|---|
| **Axelrod 1986** *APSR* 80(4):1095–1111(DOI 10.1017/S0003055400185016) | 20 プレイヤ・boldness と vengefulness が各 0〜7(3 bit)=64 戦略・MutationRate 0.01。**罰が有償なら規範ゲームは崩壊**(高 boldness / 低 vengefulness へ)。**メタ規範**(罰しない者を罰す)を入れると規範が立ち上がり維持される | **二次**(Cambridge Core 本文未読) |
| **Galán & Izquierdo 2005** JASSS 8(3)2(再実装) | 「Axelrod's results are **not as reliable** as one would desire. They can obtain the **opposite results** by running the model for longer, by slightly modifying some of the parameters」 | **二次** |
| **Sen & Airiau 2007** IJCAI-07 pp.1507–1512 | 「our experimental results show that a **uniform norm always emerges in a population of three or more agents**」/「in a population of **200 agents using WoLF, we ran 1,000 runs**, and we observed that the population converged to the "yield to the left" norm **482** times, and "yield to the right" norm **518** times」/ 図1 の横軸は **0〜1,200 iterations**/「with more agents, **it takes longer** for the entire population to converge on a particular norm」。学習器は Q-learning(ε-greedy)・WoLF-PHC・Fictitious Play の 3 種 | **原典**(著者公式 PDF を pymupdf 抽出) |
| **Savarimuthu & Cranefield 2011** *Multiagent and Grid Systems* 7(1):21–54(DOI 10.3233/MGS-2011-0167) | 規範の **5 段ライフサイクル**: creation / identification / spreading / enforcement / **emergence**。既存シミュレーション研究をこの 5 段のどこを扱うかで分類 | **二次** |
| **Bicchieri 2006**(v2 既出) | [v2-world-ledger-verification.md](v2-world-ledger-verification.md):214「社会規範への同調選好は『**経験的期待**(他者がその行動をとるという一次的信念)』と『**規範的期待**(他者がそうすべきだと信じているという二次的信念)』に条件づけられている。慣習は規範的側面を欠く点で社会規範と異なる」 | 既出(答申は URL を持つ・親未確認) |
| **Ashery et al. 2025** *Sci Adv* 11(20):eadu9368(v2 既出) | [v2-r23-primary-check-batch2.md](v2-r23-primary-check-batch2.md) #32 で親が一致判定済み。24〜200 体の naming game で慣習が自発創発・**コミットした少数派によるティッピング**。反論= Barrie & Törnberg 2505.23796(観測的同値) | 既出 |

**議事録との対応**

| 議事録の節 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §30 | 「individual behavior → other behavior prediction → mutual expectation → stable repeated pattern → Norm」 | Sen & Airiau 2007 は**予測も期待も持たせず**、私的な報酬学習だけで一様規範が立つと示した(「social learning with private interactions」)。段階は不要だったという結果 | **部分一致**(創発するのは一致・経路は違う) | **原典** |
| §30 | 「Norm = 明示的なルールだけでなく、Agent が『他者がこうするはず』と持つ**共有期待**」 | Bicchieri の定義は**経験的期待 + 規範的期待の 2 層**。議事録の定義は経験的期待のみ=Bicchieri の語では「慣習(convention)」に当たり「社会規範」ではない。Young 1996(Sen & Airiau が引く)も「a convention as an equilibrium that everyone expects」=慣習の定義 | **部分一致**(規範的期待が欠けている) | 二次+既出 |
| §30 | 「Norm 違反は最初から罰でなく、surprise / social salience / distance / verbal response / imitation avoidance を経由してよい」 | **反対向きの先行が 2 本**: Axelrod 1986 は「罰が有償なら規範は崩壊、メタ規範(罰の罰)で初めて立つ」、Ashery 2025(v2 既出)は「**処罰機構が規範創発を駆動**」。罰なしで立ち上がる例は Sen & Airiau 2007 だが、そこでは罰の代わりに**衝突の負の報酬**がある(罰の一種) | **矛盾**(罰を外して立ち上がるとする先行は見つからない) | 二次+**原典** |
| §30 | Norm は最初から固定 Rule にしなくてよい | Savarimuthu & Cranefield の 5 段は creation を第 1 段に置く=**創発だけでなく明示的創出も分野の標準の一部**。どちらか一方に決めよとは言っていない | **一致** | 二次 |

---

## §5 Organization(議事録 §32)

| 先行 | 役割/権限/資源の表現 | 確認 |
|---|---|---|
| **Carley & Prietula 1994**「ACTS Theory: Extending the Model of Bounded Rationality」(*Computational Organization Theory*, Erlbaum, pp.55–87) | **ACTS = Agents that are Cognitively restricted, Task-oriented, and Socially situated**。組織を「過程と知的適応エージェントの集まり」と見る。「task, cognitive agency, and organizational design should be equally important factors in explaining organizational performance」 | **二次**(章本文は未読) |
| **Carley 2002** *PNAS* 99(suppl_3):7257–7262(DOI 10.1073/pnas.082080599) | 抄録「**Synthetic adaptation** is the process whereby any entity composed of intelligent, adaptive, and computational agents **is also** an intelligent, adaptive, and computational agent.」CONSTRUCT-O・ORGAHEAD は「ネットワーク(社会と知識)と多エージェントを組み合わせる」 | **抄録** |
| **MOISE+**(Hübner, Sichman & Boissier 2002, SBIA, LNAI, pp.118–128) | 3 次元: **structural**(roles / links between roles / groups / 階層)・**functional**(schemes = HTN 的な全体計画 / missions / goals)・**deontic**(role と mission を結ぶ **permission / obligation**、役割階層に沿って継承)。JaCaMo が実装 | **二次** |
| **MetaGPT**(arXiv 2308.00352) | SOP をプロンプト列に符号化。**役割 ablation**: Engineer 単独で executability 1.0 / revisions 10 → 管理職(ProductManager・Architect・ProjectManager)を足すと **4.0 / 2.5**。executable feedback 追加で Pass@1 が HumanEval **+4.2%**・MBPP **+5.4%** | **二次** |
| **ChatDev**(arXiv 2307.07924, ACL 2024) | waterfall(design / coding / testing)+ chat chain。ablation で「**the most substantial impact on performance occurs when the roles of all agents are removed from their system prompts**」= quality **0.3953 → 0.2212**・executability **0.8800 → 0.5800** | **二次** |
| OperA / Electronic Institutions | — | **未読**(→ §11) |

**議事録との対応**

| 議事録の節 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §32 | Organization = shared goal + roles + rules + resources + decision structure + continuity | MOISE+ の 3 次元が roles(structural)・rules/goals(functional)・権限(deontic)を覆う。**resources と continuity(history)は MOISE+ に無い** | **部分一致** | 二次 |
| §32 | 「Organization は巨大 Agent ではない。構造であり、Agent の代わりに全意思決定する存在ではない」 | MOISE+ は組織を**仕様**として置き、決定は agent 側に残す=一致。ただし MOISE+ の再編成は **OrgManager / Designer という役割の agent** を立てる=「組織を動かす専用 agent」は先行に在る。Carley 2002 の synthetic adaptation は逆で「組織も知的適応エージェントである」 | **部分一致**(Carley 2002 とは**矛盾**の向き) | 二次+抄録 |
| §32 | 「Organization truth ≠ Agent understanding of organization」 | MOISE+ は組織仕様を共有の真として置き、認識のずれを扱わない。Carley の CONSTRUCT-O は知識ネットワークを個体ごとに持つ=近い | **部分一致** | 二次 |
| §32 | Role obligation と個人 Goal は競合し得る | MOISE+ の deontic 次元が obligation を明示。競合の扱いは先行では sanction(後続の規範版 MOISE)側 | **一致** | 二次 |
| §32 | 「情報提供」と「権限を伴う指示」は別物 | MOISE+ の permission / obligation の区別がこれに当たる | **一致** | 二次 |
| §32 | 役割は組織の性能を決める | MetaGPT・ChatDev の 2 本の ablation が**独立に**「役割を外すと最も落ちる」と報告(ただし舞台はソフトウェア開発であって都市ではない) | **一致** | 二次 |

---

## §6 社会情報の伝播と信頼(議事録 §33)

| 先行 | 内容・数値 | 確認 |
|---|---|---|
| **Daley & Kendall 1964** *Nature* 204:1118(DOI 10.1038/2041118a0) | 噂の伝播を疫学の類推で扱う 1 ページ報。「even the qualitative results so obtained **need not necessarily be as expected** on the basis of the formal analogy with epidemics」。詳細は Daley & Kendall 1965 *J. Inst. Math. Appl.* 1:42–55(**未読**) | **抄録** |
| **Maki & Thompson 1973**(*Mathematical Models and Applications*, Prentice-Hall) | DK との違い=「In the Daley-Kendall model, if an infective contacts another infective, **both** become removed, whereas, in the Maki-Thompson model, **only the initiator** of the contact is removed」 | **二次**(書籍・未読) |
| 3 状態 | ignorant(=susceptible)/ spreader(=infected)/ **stifler**(=removed)。除去は自発でなく**相互作用の結果**(「it is worth propagating a rumor as long as it is novel for the recipient」) | **二次** |
| **最後まで聞かない割合** | Sudbury: Maki–Thompson で母集団 →∞ のとき「the proportion of the population never hearing the rumour converges in probability to a limiting constant (**approximately equal to 0.203**)」。DK でも約 20% | **二次**(Sudbury 原典・Duan & Ganesh arXiv 2002.06821 とも本文未読) |
| **Hegselmann & Krause 2002** JASSS 5(3)2 | bounded confidence ε。「The general trend is of course: **The lower epsilon the higher the number of emerging clusters.** But nevertheless very often a certain random initial profile leads to **less** clusters for a slightly lower epsilon」。完全結合 N=100 で合意閾 ε_c ≈ 0.25(Fortunato の推定は ε_c ≈ 0.2)・疎なネットワークでは ε_c = 1/2 | **二次** |
| **Hegselmann 2023** JASSS 26(4)11(**著者による自己訂正**) | 「We **completely overlooked** a crucial feature of our model. … the transitions are **wild, chaotic and non-monotonic**. … we thought that for increasing values of ε, the number of opinion clusters … would decrease monotonically. **But this is wrong**」 | **二次** |
| **Castelfranchi & Falcone**(1998 ICMAS pp.72–79 / 2010 *Trust Theory*, Wiley, DOI 10.1002/9780470519851) | trust = 信念に基づく心的態度。核は **ability/competence** と **disposition(willingness, persistence, engagement)** の 2 本。5 項関係(trustor / trustee / action / goal / 文脈)。**internal trust(相手の能力)と external trust(環境の機会)を分ける**。信念の源(belief sources)= 直接経験 / 評判 / カテゴリ / 推論(Castelfranchi, Falcone & Pezzulo 2003 AAMAS pp.89–96) | **二次** |

**議事録との対応**

| 議事録の節 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §33 | 「情報は World Truth と別物」(店 X は営業中 / B は閉店したと信じる) | Daley–Kendall 系の ignorant/stifler は**まさにこの構造**。定量の錨として「母集団の約 20.3% は最後まで噂を聞かない」が使える | **一致** | 抄録+二次 |
| §33 | Channel は交換可能(face_to_face / phone / text / social_media / observation / imitation) | 古典の噂モデルは均質混合で channel を持たない。channel 別は v2 既出の [ad-information-research](v2-ad-information-research.md)(等級 C)側 | **先行なし**(古典側には) | 二次 |
| §33 | belief update に `source_trust` | Castelfranchi & Falcone は **competence と willingness の 2 分割**を核に据える。単一スカラー `source_trust` は先行の統合形 | **部分一致** | 二次 |
| §33 | `directness` | Falcone & Castelfranchi 2004「Trust Dynamics: How Trust Is Influenced by **Direct Experiences** and by Trust Itself」が同名の区別を持つ | **一致** | 二次 |
| §33 | `context_match` | Castelfranchi の external trust(環境の機会)と categories からの一般化(Falcone et al. 2013)が近いが、同名の変数は無い | **部分一致** | 二次 |
| §33 | `recency` / `consistency` | 対応する名前つき変数を先行に特定できず。評判の集約(2003 fuzzy)が近い | **部分一致** | 二次 |
| §33 | 経験によって trust(A) が上下する | Falcone & Castelfranchi 2004 が正面から扱う | **一致** | 二次 |
| §31(文化) | 「伝播中に変形する」 | Hegselmann–Krause の bounded confidence は「近い意見だけを平均する」=変形でなく収束。**非単調性の自己訂正(2023)**があるので、ε 依存の直観は使えない | **部分一致**(+ 訂正の存在) | 二次 |

---

## §7 創発の階層と測り方(議事録 §34・§43)

### 7-1 micro / meso / macro の 3 層

- **Moss & Edmonds 2005** *AJS* 110(4):1095–1131 は **micro / macro の 2 層**である。「can be **microvalidated** against accounts of individual behavior and **macrovalidated** against aggregate data」。3 層ではない。確認=**二次**。
- **3 層(micro / meso / macro)を明示する先行**: Gürcan, Dikenelli & Bernon 2013 *J. Simulation* 7:183–201 と Tieleman、および meso 検証の SN Bus. Econ. 2021(「initialized at the micro-level, calibrated at the macro-level, and **validated at the meso-level** with the same data set」)。確認=**二次**。
- **批判も在る**: ACM TOMACS 2025 の階層的検証枠組みは「Gürcan et al. と Tieleman は **ABM の手続き面を見落としている**」として agent / model / output の 3 層を代わりに提案。確認=**二次**。
- Grimm et al. 2005 POM(*Science* 310:987)と Grimm & Railsback 2012 は **v2 既出**([v2-methodology.md](../design/v2-methodology.md) 冒頭・[lit/abm__grimm-railsback2012_pom-multiscope.md](lit/abm__grimm-railsback2012_pom-multiscope.md))。複数パターンの同時照合という要求は既に方法論に入っている。

### 7-2 歩行者流の創発指標

| 指標 | 先行 | 確認 |
|---|---|---|
| レーン形成の定量化 | **Feliciani & Nishinari 2016** *Phys. Rev. E* 94:032304(+ Publisher's Note 97:049903・97:069901): 双方向流の模擬廊下実験で**単方向→双方向の遷移を 5 相**に分け、「**order parameter**」と「**rotation range**」の 2 次元量を導入。均衡双方向流はレーン形成後に最も安定だが、レーン生成過程は最大の横移動を要する | **二次** |
| 同上(先行) | Zhang, Klingsch, Schadschneider & Seyfried 2012 *JSTAT* P02002「Ordering in bidirectional pedestrian flows and its influence on the fundamental diagram」 | **二次** |
| **Yamori 1998 の band index** | **書誌を特定できなかった**(→ §11。記憶で埋めない) | **未読** |
| 混雑度・危険度 | Feliciani & Nishinari 2018 *TRC* 91:124–155: congestion level(速度をベクトルとして扱う)と intrinsic risk。引用論文が伝える数値「crowd danger ≈ **8 m⁻³** at ρ ≈ **6.5 m⁻²**」 | **二次**(孫引き) |
| 基本図・ボトルネック比流量 | **v2 既出**: [v2-crowd-physics.md](../design/v2-crowd-physics.md):29(Jülich 公開データ・Seyfried **1.61–2.31 (m·s)⁻¹**・Voronoi 密度)・:30(Weidmann 1.34 m/s) | 既出(親検収済み答申 [crowd-physics-research](v2-crowd-physics-research.md)=等級 A) |
| 情報カスケードの測度 | 本批では未調査 | **空欄** |

### 7-3 渋谷/日本の歩行者流の公開一次データ

- 「渋谷スクランブル交差点は **1 回の青信号で約 3,000 人**」は**一次出典を特定できなかった**。観光情報・地域広報(東京都道路整備保全公社 広報誌 `trmag_24.pdf` を含む)がいずれも「〜といわれる」型で書いており、Wikipedia 日本語版は「1 回の歩行青信号で **1,000 人以上**」と桁の違う控えめな値を使う。→ **伝聞値**と判定。確認=**二次**。
- 公的に辿れるもの(いずれも本批では**存在確認のみ**・中身は未読):渋谷区 SHIBUYA CITY DASHBOARD(KDDI Location Analyzer 由来の人流)/ 渋谷区「渋谷駅周辺地域交通戦略」第 2 章 交通実態 / 警視庁「主要交差点交通量集計表」(主に車両)/ 国交省 全国道路・街路交通情勢調査 一般交通量調査 箇所別基本表。
- **v2 は既にこの線を引いている**: スクランブル通行量と KDDI 形状 5 指標は **holdout(較正に使わない)**([v2-crowd-physics.md](../design/v2-crowd-physics.md):32,36・[v2-boundary-economy-design.md](../design/v2-boundary-economy-design.md):29・[v2-world-data-build-spec.md](../design/v2-world-data-build-spec.md):35)。信号現示 140 秒 / 37 秒 / 10 秒 は**個人観測 = expedient** と宣言済み(同 :39)。

### 7-4 議事録との対応

| 議事録の節 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §34 | 評価を Micro / Meso / Macro に分ける | 3 層は Gürcan 2013・Tieleman・SN Bus Econ 2021 に在る。ただし Moss & Edmonds は 2 層、TOMACS 2025 は agent/model/output を対置=**唯一の分け方ではない** | **部分一致** | 二次 |
| §34 | Meso にレーン形成・滞留・ボトルネック・Group・情報拡散を置く | 歩行者側は Feliciani & Nishinari 2016(order parameter)と Zhang 2012 で定量指標が在る。**情報拡散の meso 指標は未調査** | **部分一致** | 二次 |
| §34 | 「創発 = Agent に直接プログラムしていない構造が相互作用から発生するもの」 | v2 既出の **観測的同値**(Haavelmo 1944 via Windrum 2007 §2.3(5)・Barrie & Törnberg 2025)が「発生したように見えることと発生したことは区別できない」と言う | **部分一致**(定義は一致・立証責任が抜けている) | 既出 |
| §43 | mean だけでなく variance / distribution / temporal persistence / spatial pattern を見る | v2 既出の方法論「**分散も報告**(LLM は平均整合・分散不足の実測あり)」([v2-methodology.md](../design/v2-methodology.md) Phase 4)と同じ | **一致** | 既出 |
| §34 Macro | 渋谷の巨視量で照合する | 最も有名な巨視量(青信号あたり 3,000 人)は**一次出典が無い伝聞値**。公的に辿れるのは KDDI ダッシュボード・交通戦略・警視庁・国交省センサス | **部分一致**(照合対象の選び方に注意が要る) | 二次 |

---

## §8 摂動実験・検証 3 層・観測可能/潜在(議事録 §35・§38〜§40)

| 先行 | 内容 | 確認 |
|---|---|---|
| **Klügl 2008** SAC'08 pp.39–43(DOI 10.1145/1363686.1363696) | 抄録「a process for validating agent-based simulation models that **combines face validation, sensitivity analysis, calibration and statistical validation**」。引用経由の警告「there is the risk that based on '**tuning**' on the local level, agent models are able to **reproduce the global level outcome, that are not valid at all**」 | **抄録**(+ 一文は二次) |
| **Windrum, Fagiolo & Moneta 2007** JASSS 10(2)8 | **v2 既出・実読**([lit/abm__windrum2007_empirical-validation.md](lit/abm__windrum2007_empirical-validation.md))。較正・検証の 3 系統・中核問題 6 つ・**識別問題は Haavelmo 1944 の "observationally equivalent"** | 既出=実読 |
| **Moss & Edmonds 2005** | §7-1。micro=質的/ステークホルダ、macro=統計(leptokurtosis・clustered volatility があるため χ² 等は使えない) | **二次** |
| **Balci 1998** | **未読**。v2 既出は Balci & Sargent 1981/1984 の**孫引きのみ**で、[v2-statistics-causal-research.md](v2-statistics-causal-research.md):209 が「原典: 未読」と既に宣言している | **未読** |
| **Takadama, Kawai & Koyama 2008** JASSS 11(2)9 | Carley & Gasser 1999 由来の 3 分類: **theoretical verification / external validation / cross-model validation** | **二次** |
| **Baker, Saxe & Tenenbaum 2009** *Cognition* 113(3):329–349 | 抄録「a computational framework based on **Bayesian inverse planning**」「our models **correlated highly** with people's judgments across multiple conditions」。**具体的な r は本文の表にあり未取得**。先行版(CogSci 2007 / NIPS 2006)の「r = .96」は CSAIL 抄録経由 | **抄録**(数値は空欄) |
| **Ng & Russell 2000**(IRL)/ **Ziebart 2008**(MaxEnt IRL) | — | **未読**(→ §11) |
| **Kretzschmar, Spies, Sprunk & Burgard 2016** *IJRR* 35(11):1289–1307 | 抄録「model their behavior in terms of a **mixture distribution** that captures both the discrete navigation decisions … as well as the natural variance of human trajectories」「learns the model parameters … that **match, in expectation, the observed behavior** in terms of user-defined features」。特徴期待値は Hamiltonian MCMC | **抄録** |

**議事録との対応**

| 議事録の節 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §35 | 「校正に使っていない条件で応答を評価する」(摂動実験) | **v2 既出**の holdout 封印・事前登録([architecture-overview-detailed](../design/v2-architecture-overview-detailed.md) §10.4・prereg v1.3)。Klügl の calibration→statistical validation の順も同型 | **一致** | 既出+抄録 |
| §37 | Calibration と Validation を同じデータでやらない | 同上。v2 は既に「開封は 1 回きり・以後の seed 追加は主張に使えない」まで持つ | **一致** | 既出 |
| §40 | **Mechanistic / Behavioral / Emergent** の 3 層 | **この 3 分類に一致する先行分類は見つからなかった**。最も近いのは Klügl の 4 段(手続きであって妥当性の種類ではない)・Takadama の theoretical/external/cross-model・Sargent の conceptual/operational | **部分一致**(3 という数は一致・切り方は先行に無い) | 抄録+二次 |
| §38 | 潜在(belief・uncertainty・policy confidence・escalation)を行動から逆推定する | Baker 2009(Bayesian inverse planning)と Kretzschmar 2016(歩行者の IRL)が**実在する先行**。歩行者領域で成立している | **一致** | 抄録 ×2 |
| §39 | 「同じ行動でも内部機構が違う」から Cognitive mechanism もログ・分析する | **v2 既出の観測的同値**(Windrum 2007 §2.3(5) の識別問題・Barrie & Törnberg 2025「Emergent LLM behaviors are **observationally equivalent to data leakage**」)が正面の先行。結論は「**行動だけでは区別できない**」。ただし先行は「模型の内側のログを取れば区別できる」とは言っていない(ログには現実側の対照が無い) | **部分一致** | 既出 |

---

## §9 仮説 H1〜H6 と ablation 行列(議事録 §41・§42)

### 9-1 「認知機構を足すと現象が変わる」を示した先行

| 先行 | ablation の形と数値 | 確認 |
|---|---|---|
| **Moussaïd et al. 2010**(§3) | 模型の社会的相互作用強度 **α₁=0 と α₁=4** を比べ、隊形が inverse-V ↔ V に反転し歩行速度が変わる=事実上の 1 因子 ablation。速度勾配 y=−0.05x+1.3(低密度)/ −0.07x+1.2(中密度) | **原典** |
| **Moussaïd, Helbing & Theraulaz 2011** *PNAS* 108(17):6884–6888 | 「a **cognitive science approach** is proposed, which is based on **behavioral heuristics**」。視線方向の障害物距離から方向と速度の 2 規則。**ヒューリスティックの有無で群衆現象がどう変わるかの ablation を行ったかは未確認**(PNAS 403) | **二次**(→ §11) |
| **Park et al. 2023** Generative Agents(arXiv 2304.03442 / UIST '23) | TrueSkill(μ; σ): 全構成 **29.89; 0.72** / 反省なし **26.88; 0.69** / 反省・計画なし **25.64; 0.68** / 人間クラウドワーカ **22.95; 0.69** / 観察・反省・計画すべてなし **21.21; 0.70**。Cohen's **d = 8.16**。Kruskal–Wallis **H(4)=150.29, p<0.001**、Dunn 事後はクラウドワーカ条件と全除去条件の対を除き全対 p<0.001 | **二次**(検索要約。本文表は未読) |
| **Project Sid**(arXiv 2411.00114) | **v2 既出**([v2-r23-primary-check-batch2.md](v2-r23-primary-check-batch2.md) #25): §8.3 の 3 条件は「修正可能な憲法」「凍結した憲法の対照」「モジュール ablation」で、**法体系そのものを外した条件は無い**。解析は 500 体 | 既出(親確認済み) |
| **MetaGPT / ChatDev**(§5) | 役割 ablation で最大の劣化。ChatDev「removing roles … quality 0.3953 → 0.2212」 | **二次** |

### 9-2 組み合わせ爆発の扱い

- **ten Broeke, van Voorn & Ligtenberg 2016** JASSS 19(1)5(DOI 10.18564/jasss.2857)は **v2 既出・親再確認済み**([v2-replication-count-research.md](v2-replication-count-research.md) #4・[v2-statistics-causal-research.md](v2-statistics-causal-research.md):110)。逐語「OFAT 10 反復 / 回帰 5 / Sobol' 0」「The mean output variance over replicates is **0.88%** of the output variance over all samples」。Sobol' は反復 0 でよいが**基底標本 N(k+2) で総ラン数が爆発**。
- Morris screening・Controlled Sequential Bifurcation も **v2 既出**([lit/stats__wan2003_controlled-sequential-bifurcation.md](lit/stats__wan2003_controlled-sequential-bifurcation.md))。
- 議事録 §42 の腕を掛けると **3(APS)×5(Attention)×5(Memory)×4(Learning)×4(System 1)×4(Escalation)×5(Interruption)×5(LOD)×6(Social) = 720,000 腕**(親の再計算可)。先行の手続きは OFAT / 分数実施要因 / screening / Sobol' のいずれかで畳むこと。

### 9-3 議事録との対応

| 議事録の節 | 主張 | 先行 | 関係 | 確認 |
|---|---|---|---|---|
| §41 H1 | Local System 1 cognition → micro 行動のリアリズム改善 | Moussaïd 2011 が「force model より heuristics の方が実測に整合」と主張(定量は未取得) | **部分一致** | 二次 |
| §41 H2 | Other-agent prediction → 群衆動力学の改善 | Moussaïd 2010 の α₁ 比較が最も近い(社会的相互作用の有無で隊形と流量が変わる) | **一致** | **原典** |
| §41 H3 | Memory / learning → 時間的持続と適応の改善 | Park 2023 の ablation が**単調に落ちる**ことを示す。ただし指標は「もっともらしさ(TrueSkill)」であって都市現象ではない | **部分一致** | 二次 |
| §41 H4 | Jev escalation → 新奇な擾乱への応答改善 | 対応する先行 ablation を特定できず | **先行なし** | — |
| §41 H5 | Social information transmission → meso/macro パターンを生む | Daley–Kendall 系(約 20.3% が聞かない)と Ashery 2025(慣習の自発創発)が近いが、**都市の meso/macro を出したと示した先行は無い** | **部分一致** | 抄録+既出 |
| §41 H6 | Organization / norm dynamics → 長期の集合行動を変える | Artificial Institutions 2608.04020(**call market 88.6% vs 二者交渉 56.4%**・v2 既出)と Hierarchical Games 2608.09574(同一モデル族だと政権交代が起きない・v2 既出)が「制度を独立変数にすると結果が質的に変わる」を支持 | **一致** | 既出(親確認済み) |
| §42 | 8 軸の腕を並べる | 先行(ten Broeke)は OFAT / 回帰 / Sobol' の 3 手続きを比較し、**全組合せは取らない**。議事録は行列の畳み方を書いていない | **部分一致** | 既出 |

---

## §10 親への確認依頼(5 件)

1. **Moussaïd 2010 の「70%」の写し**: 原典は "up to 70%" で、内訳は **population A 55% / B 70%**(N=260 群 / 1093 群、追跡 1098 体 / 3461 体)。既存 [v2-person-perception-verification.md](v2-person-perception-verification.md):73,172 の「最大70%」は原典と**一致**するが、設計書へ写すときに 55/70 の二値と N を併記するか(CLAUDE.md §5 の写し検査・フロア併記検査と同型)。
2. **Hegselmann 2023 の自己訂正の伝播**: 原著者が 2023 年に「ε とクラスタ数は単調でない=当時の理解は誤り」と JASSS で訂正している。v2 が意見動態系の直観を使う箇所があれば訂正伝播検査の対象になる(本批では設計書に Hegselmann の名を確認できなかった=grep 0 件)。
3. **スクランブル通行量の出所**: 「1 回の青信号で約 3,000 人」は**一次出典が見つからない伝聞値**。v2 の holdout 行「スクランブル通行量」([v2-crowd-physics.md](../design/v2-crowd-physics.md):32,36・[v2-boundary-economy-design.md](../design/v2-boundary-economy-design.md):29)がこの値を指しているなら、実データの出所(渋谷区交通戦略か独自計測か)を確認されたい。
4. **Axelrod 1986 の等級**: 本文は有料で未読。Galán & Izquierdo 2005 JASSS 8(3)2 が再実装で「長く回す/僅かにパラメータを変えると**逆の結果**が出る」と報告している。規範の創発を根拠に使うなら、Axelrod 1986 は**再現批判つき**として扱うか、親が Cambridge Core で一次を取るか。
5. **Baker, Saxe & Tenenbaum 2009 の相関値**: 抄録は "correlated highly" としか書かず、**具体的 r は本文の表にあり未取得**。世間で流通する「r = .96」は**先行版(CogSci 2007 / NIPS 2006)の値**であって 2009 年 *Cognition* の値ではない。使うなら親が MIT 公開 PDF の表を確認されたい。

---

## §11 空欄(本批で読めなかったもの・記憶で埋めていない)

| # | 空欄 | 理由 |
|---|---|---|
| 1 | Huberman & Glance 1993 の**定量**(協力率が何 % から何 % へ変わったか) | PNAS 本文 403。抄録に数値なし |
| 2 | Caron-Lormier et al. 2008 本文 | Elsevier 403(既存答申 [run-manifest-concurrency](v2-run-manifest-concurrency-research.md):574 でも空欄) |
| 3 | Jefferson 1985 Virtual Time 本文 | ACM DL。既存答申が「要らない」と判断済みなので優先度低 |
| 4 | Railsback & Grimm のスケジューリング論(教科書) | 書籍 |
| 5 | Qiu & Hu 2010 ほか小集団入り群衆モデル | 本文に到達できず |
| 6 | ABM で「近接→反復相互作用→共有目標→安定集団」を実装検証した先行 | 特定できず(存在しないとは言えない) |
| 7 | Axelrod 1986 本文 | Cambridge Core 有料 |
| 8 | Bicchieri 2006 本体 | v2 既出は *Measuring Social Norms* PDF のみ。*The Grammar of Society* 本体は未読 |
| 9 | Carley & Prietula 1994 ACTS 章本文 | 書籍・オープンアクセス無し |
| 10 | OperA / Electronic Institutions | 本批では未調査 |
| 11 | Daley & Kendall 1965 *J Inst Math Appl* 1:42–55 / Maki & Thompson 1973 本体 | 未読(0.203 は二次) |
| 12 | Yamori 1998 の band index の書誌 | 特定できず |
| 13 | 情報カスケードの定量測度 | 本批では未調査 |
| 14 | Ng & Russell 2000 / Ziebart 2008 本文 | 本批では未調査 |
| 15 | Balci 1998 本文 | 未読(v2 既出も孫引きのみ) |
| 16 | Moussaïd 2011 PNAS 本文(2 ヒューリスティックの式・ablation の有無) | PNAS 403 |
| 17 | Park 2023 の TrueSkill 表(§6.5.1) | 検索要約のみ・arXiv 本文未読 |
| 18 | Baker 2009 の相関値の表 | §10-5 |

---

## §12 出典一覧

| # | 題・書誌 | URL | 確認 |
|---|---|---|---|
| 1 | Lamport, *Time, Clocks, and the Ordering of Events in a Distributed System*, CACM 21(7):558–565 (1978) | https://lamport.azurewebsites.net/pubs/time-clocks.pdf | **原典**(PDF→pymupdf 全文) |
| 2 | Huberman & Glance, *Evolutionary games and computer simulations*, PNAS 90(16):7716–7718 (1993), doi:10.1073/pnas.90.16.7716 | https://pubmed.ncbi.nlm.nih.gov/8356075/ | **抄録** |
| 3 | Nowak & May, *Evolutionary games and spatial chaos*, Nature 359:826 (1992) | — | **二次**(#2 経由) |
| 4 | Cornforth, Green & Newth, *Ordered asynchronous processes in multi-agent systems*, Physica D 204(1–2):70–82 (2005), doi:10.1016/j.physd.2005.04.005 | https://www.sciencedirect.com/science/article/abs/pii/S0167278905001338 | **抄録** |
| 5 | Caron-Lormier et al., Ecol. Modelling 212(3–4):522–527 (2008), doi:10.1016/j.ecolmodel.2007.10.049 | — | **未読** |
| 6 | Cooperation Breakdown in LLM Agents Under Communication Delays | https://arxiv.org/html/2602.11754 | **二次** |
| 7 | Real-Time Deadlines Reveal Temporal Awareness Failures in LLM Strategic Dialogues | https://arxiv.org/pdf/2601.13206 | **二次** |
| 8 | Time to Talk: LLM Agents for Asynchronous Group Communication in Mafia Games | https://arxiv.org/pdf/2506.05309 | **二次** |
| 9 | Your LLM Agents are Temporally Blind | https://arxiv.org/html/2510.23853v2 | **二次** |
| 10 | Veluri et al., *Beyond Turn-Based Interfaces: Synchronous LLMs as Full-Duplex Dialogue Agents*, EMNLP 2024 | https://aclanthology.org/2024.emnlp-main.1192/ | **二次** |
| 11 | Moussaïd, Perozo, Garnier, Helbing & Theraulaz, *The Walking Behaviour of Pedestrian Social Groups and Its Impact on Crowd Dynamics*, PLoS ONE 5(4):e10047 (2010) | https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0010047 ・ https://arxiv.org/pdf/1003.3894 | **原典**(PDF→pymupdf 全文) |
| 12 | Nicolas & Hassan, *Social groups in pedestrian crowds: Review…* (2023) | https://arxiv.org/pdf/2107.13293 | **二次** |
| 13 | Tuckman, *Developmental sequence in small groups*, Psychological Bulletin 63:384–399 (1965) | https://infed.org/dir/welcome/bruce-w-tuckman-forming-storming-norming-and-performing-in-groups/ | **二次** |
| 14 | Tuckman & Jensen, *Stages of Small-Group Development Revisited* (1977), doi:10.1177/105960117700200404 | https://journals.sagepub.com/doi/10.1177/105960117700200404 | **二次** |
| 15 | Axelrod, *An Evolutionary Approach to Norms*, APSR 80(4):1095–1111 (1986), doi:10.1017/S0003055400185016 | https://www.cambridge.org/core/journals/american-political-science-review/article/abs/an-evolutionary-approach-to-norms/2B829FB347BBDD0F1A8C0F325EFB6F7B | **二次** |
| 16 | Galán & Izquierdo, *Appearances Can Be Deceiving…*, JASSS 8(3)2 (2005) | https://jasss.soc.surrey.ac.uk/8/3/2.html | **二次** |
| 17 | Sen & Airiau, *Emergence of Norms Through Social Learning*, IJCAI-07:1507–1512 | https://www.lamsade.dauphine.fr/~airiau/pub/IJCAI07-norms.pdf | **原典**(PDF→pymupdf 全文) |
| 18 | Savarimuthu & Cranefield, *Norm creation, spreading and emergence*, Multiagent and Grid Systems 7(1):21–54 (2011), doi:10.3233/MGS-2011-0167 | https://www.semanticscholar.org/paper/a7072328d1a090b145cb065e6312b0f8a3b01273 | **二次** |
| 19 | Bicchieri, *Measuring Social Norms*(v2 既出) | https://www.irh.org/wp-content/uploads/2016/09/Bicchieri_MeasuringSocialNorms.pdf | 既出・**親未確認** |
| 20 | Carley & Prietula (eds.), *Computational Organization Theory*, Erlbaum (1994); ACTS 章 pp.55–87 | https://www.routledge.com/Computational-Organization-Theory/Carley-Prietula/p/book/9781138971400 | **二次** |
| 21 | Carley, *Computational organization science: A new frontier*, PNAS 99(suppl_3):7257–7262 (2002), doi:10.1073/pnas.082080599 | https://www.pnas.org/content/99/suppl_3/7257 | **抄録** |
| 22 | Hübner, Sichman & Boissier, *A Model for the Structural, Functional, and Deontic Specification of Organizations in MAS*, SBIA 2002, LNAI, pp.118–128 | https://moise.sourceforge.net/doc/publications/Hubner-sbia2002.pdf ・ https://link.springer.com/chapter/10.1007/3-540-36127-8_12 | **二次** |
| 23 | Hong et al., *MetaGPT: Meta Programming for A Multi-Agent Collaborative Framework*, ICLR 2024 | https://arxiv.org/abs/2308.00352 | **二次** |
| 24 | Qian et al., *ChatDev: Communicative Agents for Software Development*, ACL 2024 | https://aclanthology.org/2024.acl-long.810/ | **二次** |
| 25 | Daley & Kendall, *Epidemics and Rumours*, Nature 204:1118 (1964), doi:10.1038/2041118a0 | https://www.nature.com/articles/2041118a0 | **抄録** |
| 26 | Duan & Ganesh, *The Proportion of the Population Never Hearing a Rumour* (2020) | https://arxiv.org/pdf/2002.06821 | **二次**(0.203 の出所) |
| 27 | Hegselmann & Krause, *Opinion dynamics and bounded confidence*, JASSS 5(3)2 (2002) | https://www.jasss.org/5/3/2.html | **二次** |
| 28 | Hegselmann, *Bounded Confidence Revisited: What We Overlooked, Underestimated, and Got Wrong*, JASSS 26(4)11 (2023) | https://www.jasss.org/26/4/11.html | **二次**(自己訂正) |
| 29 | Castelfranchi & Falcone, *Trust Theory: A Socio-Cognitive and Computational Model*, Wiley (2010), doi:10.1002/9780470519851 | https://onlinelibrary.wiley.com/doi/book/10.1002/9780470519851 | **二次** |
| 30 | Castelfranchi, Falcone & Pezzulo, *Trust in Information Sources as a Source for Trust*, AAMAS 2003:89–96 | https://dl.acm.org/doi/pdf/10.1145/860575.860590 | **二次** |
| 31 | Moss & Edmonds, *Sociology and Simulation: Statistical and Qualitative Cross-Validation*, AJS 110(4):1095–1131 (2005) | http://cfpm.org/papers/simandsoc/ | **二次** |
| 32 | Gürcan, Dikenelli & Bernon, *A generic testing framework for agent-based simulation models*, J. Simulation 7:183–201 (2013), doi:10.1057/jos.2012.26 | https://link.springer.com/article/10.1057/jos.2012.26 | **二次** |
| 33 | *Towards Standardizing Validation Practices in ABM: A Hierarchical ABM Validation Framework*, ACM TOMACS (2025), doi:10.1145/3769857 | https://dl.acm.org/doi/10.1145/3769857 | **二次** |
| 34 | Feliciani & Nishinari, *Empirical analysis of the lane formation process in bidirectional pedestrian flow*, Phys. Rev. E 94:032304 (2016)(Publisher's Note: 97:049903・97:069901) | https://link.aps.org/doi/10.1103/PhysRevE.94.032304 | **二次** |
| 35 | Feliciani & Nishinari, *Measurement of congestion and intrinsic risk in pedestrian crowds*, TRC 91:124–155 (2018), doi:10.1016/j.trc.2018.03.027 | https://www.sciencedirect.com/science/article/abs/pii/S0968090X18304133 | **二次** |
| 36 | Zhang, Klingsch, Schadschneider & Seyfried, *Ordering in bidirectional pedestrian flows…*, JSTAT P02002 (2012) | — | **二次** |
| 37 | 渋谷区 SHIBUYA CITY DASHBOARD(KDDI Location Analyzer 由来の人流) | https://www.city.shibuya.tokyo.jp/kusei/tokei_shibuya/shibuya-data/shibuya_city_dashboard_peopleflow_KDDI.html | **存在確認のみ** |
| 38 | 渋谷区『渋谷駅周辺地域交通戦略』第 2 章 交通実態 | https://www.city.shibuya.tokyo.jp/assets/kankyo/000050292.pdf | **存在確認のみ** |
| 39 | 警視庁『主要交差点交通量集計表』 | https://www.keishicho.metro.tokyo.lg.jp/about_mpd/jokyo_tokei/tokei_jokyo/ryo.files/01_kousatenkubu.pdf | **存在確認のみ** |
| 40 | 国交省 平成27年度 全国道路・街路交通情勢調査 一般交通量調査 箇所別基本表(東京都) | https://www.mlit.go.jp/road/census/h27/data/pdf/kasyo13.pdf | **存在確認のみ** |
| 41 | Klügl, *A validation methodology for agent-based simulations*, SAC'08:39–43, doi:10.1145/1363686.1363696 | https://dl.acm.org/doi/10.1145/1363686.1363696 | **抄録** |
| 42 | Takadama, Kawai & Koyama, *Micro- and Macro-Level Validation in Agent-Based Simulation*, JASSS 11(2)9 (2008) | https://www.jasss.org/11/2/9.html | **二次** |
| 43 | Baker, Saxe & Tenenbaum, *Action understanding as inverse planning*, Cognition 113(3):329–349 (2009), doi:10.1016/j.cognition.2009.07.005 | https://web.mit.edu/9.s915/www/classes/cognition2009.pdf | **抄録** |
| 44 | Kretzschmar, Spies, Sprunk & Burgard, *Socially compliant mobile robot navigation via inverse reinforcement learning*, IJRR 35(11):1289–1307 (2016), doi:10.1177/0278364915619772 | https://journals.sagepub.com/doi/10.1177/0278364915619772 | **抄録** |
| 45 | Moussaïd, Helbing & Theraulaz, *How simple rules determine pedestrian behavior and crowd disasters*, PNAS 108(17):6884–6888 (2011), doi:10.1073/pnas.1016507108 | https://www.pnas.org/doi/full/10.1073/pnas.1016507108 | **二次**(403) |
| 46 | Park et al., *Generative Agents: Interactive Simulacra of Human Behavior*, UIST '23, doi:10.1145/3586183.3606763 | https://arxiv.org/pdf/2304.03442 | **二次** |
| 47 | ten Broeke, van Voorn & Ligtenberg, JASSS 19(1)5 (2016), doi:10.18564/jasss.2857 | https://jasss.soc.surrey.ac.uk/19/1/5.html | **v2 既出・親再確認済み** |

### v2 側の既出(重複調査していない・本書はリンクするだけ)

[v2-run-manifest-concurrency-research.md](v2-run-manifest-concurrency-research.md)(Q1 の大半)・[v2-r23-primary-check-batch2.md](v2-r23-primary-check-batch2.md)(Project Sid の憲法の扱いの訂正・Artificial Institutions・Hierarchical Games・Governance Decay・Ashery)・[v2-methodology.md](../design/v2-methodology.md)(POM・ODD・Phase 0-5・分散も報告)・[v2-architecture-overview-detailed.md](../design/v2-architecture-overview-detailed.md) §4/§5/§10(二相コミット・繰り延べ・C8 ablation 腕 10 本・holdout 事前登録 v1.3・開封結果 0/4 NOT PASS)・[v2-replication-count-research.md](v2-replication-count-research.md) と [v2-statistics-causal-research.md](v2-statistics-causal-research.md)(ten Broeke・Sobol'・Morris・CSB・同値検定)・[lit/abm__windrum2007_empirical-validation.md](lit/abm__windrum2007_empirical-validation.md) と [lit/css__barrie2025_observational-equivalence.md](lit/css__barrie2025_observational-equivalence.md)(観測的同値)・[v2-person-perception-verification.md](v2-person-perception-verification.md)(Moussaïd 2010 の 70%)・[v2-crowd-physics.md](../design/v2-crowd-physics.md)(Seyfried 比流量・Weidmann・holdout の線)・[v2-world-ledger-verification.md](v2-world-ledger-verification.md)(Bicchieri)。
