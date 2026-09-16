# v2-d71-vocab-growth-research — 回して得た観測から行動語彙を育てる仕組み(D-71 段2〜4 の設計前リサーチ)

<!-- hdr:v1 -->
- **分野**: ABM方法論 #21 / 自然言語処理・機械学習 #27 / 認知科学(記憶・習慣)#12(+ 時間利用研究 #4・法学 #11) | **重要度**: **P0**
- **一次確認**: **B → 親確認 5 件(第204)**: 社会生活基本調査 調査票A「１日の行動を20 種類に分類し」・調査票B「行動を大分類６種類、中分類22 種類、小分類90種類に分類した」(用語の解説 PDF・親 pymupdf)/ BLS「3-tiered classification system with 17 first-tier categories」(親 WebFetch)/ Emergence World §5.3「Across all five conditions, logs show exactly two agent-authored tools entering the registry」(親 WebFetch HTML)/ Atil 2024 abs「none of the LLMs consistently delivers repeatable accuracy across all tasks, much less identical output strings」・up to 15%(親 WebFetch)。**ATUS 465/110 の再計数・ASI の数値・Voyager/LearnAct/AGA/SayCan の逐語は親未確認**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 目的: [PENDING D-71](../../PENDING.md) の段2〜4(「語彙がエージェントの試みから自分で増える」)を設計する前に、**何が既に先行にあり・何が設計者の指紋になるか**を確かめる。
> ユーザー決定(2026-09-17): **ラン内でリアルタイムに裁定 LLM を入れるのではなく、回して得たデータ(未定義行動の台帳)から実装する仕組み**にする。親案=オフライン裁定バッチ。
> 起草材料の実測: [AB7 seed 1 親報告](../bench/c8/ablation/ab7_s1_parent_report.md) §3(未定義「食事」309 体・「食べる」12,594 行が段0 で購入に損失写像)・[段0 辞書の語彙政策 v0](../design/v2-synonym-policy-v0.md)・[行動契約書 §7](../design/v2-action-contract.md)。
> 表記: **[実読]** = 本文/表/節を実際に読んだ。**[要旨]** = abs・公式ページの要約までしか見ていない。**[書誌のみ]** = 書誌情報だけ確認し本文は読めていない。逐語は原文のまま ≤125 字。**推奨は書いてよいが決定は親とユーザー**(§2)。
> 規律: 子サブ未起動・コミットなし・既存ファイル未編集(本書と `lit/` の新規 8 本のみ)・holdout 未開封。

---

## §1 問いごとの表

### 1.1 問い1 — 経験から能力を増やす LLM エージェント(獲得の判定基準・オンライン/オフライン)

| 出典 | 逐語・節 | v2 への含意 |
|---|---|---|
| **Voyager**(Wang et al. 2023, [arXiv:2305.16291](https://arxiv.org/abs/2305.16291))**[実読]** ar5iv 本文 §1・§2.2・§2.3・§3.4・Fig.4 | §1「Voyager incrementally builds a skill library by storing the action programs that help solve a task successfully.」/ §2.3「until self-verification validates the task's completion, at which point we add this new skill to the skill library」/ §1「Each program is indexed by the embedding of its description, which can be retrieved in similar situations in the future.」/ §2.2 検索は「we query the skill library with the embedding of self-generated task plans and environment feedback」(Fig.4: top-5 relevant skills)/ §3.4 自己検証を外すと発見アイテム **−73%** | **登録の閾値は「1 回の成功」**。頻度閾値ではない。**オンライン書き戻し**(ラン中に庫が育つ)。**重複排除・剪定の記述は本文に無い**(「ever-growing」とだけ)= D-50 の「剪定機構なしが弱点」は本文と整合。v2 がオフラインを選ぶなら、Voyager と**逆側**の設計であることを宣言する必要がある |
| **Agent Workflow Memory**(Wang, Mao, Fried, Neubig 2024, [arXiv:2409.07429](https://arxiv.org/abs/2409.07429))**[実読]** §2.2・§2.3・§3.2.2・App.A.1/B | 抄録「AWM flexibly applies to both offline and online scenarios」/ §2.3 offline「AWM first takes in all training examples from a website by concatenating them into a single prompt」/ online は「induce, integrate, and utilize workflows after running inference for each test task」/ 成功ゲート「If e^t is predicted as success, i.e., 1, we then transform it into workflow(s)」/ 誘導の指示は「find the repetitive subset of actions across multiple tasks」と「Each workflow should have at least two steps.」/ 重複排除はプロンプト「Do not generate similar or overlapping workflows.」/ §1「supervision-free setting」・§3.2.2 は誤誘導が「incorrect workflows that degrade model performance」 | **オフラインとオンラインの両方が同じ枠で成立する**という唯一の明示的先行。**数値の頻度閾値は無い**——「複数タスクに繰り返し現れる部分」を LM に判断させている。**重複排除も自動でなくプロンプトの指示**。オンライン側は自己評価のみで、**誤った獲得が性能を下げる実例が本文にある**=ユーザーの「ラン内に裁定を入れない」決定の外部裏づけ |
| **ASI / Inducing Programmatic Skills**(Wang, Gandhi, Neubig, Fried 2025, [arXiv:2504.06821](https://arxiv.org/abs/2504.06821), COLM 2025)**[実読]** §2.2・§2.3・§3.3・Table 3 | §2.3「we can readily verify their correctness by executing them and checking if tasks can be solved successfully」/ 3 検査=「Correctness: if executing τf successfully solves the task q」「Skill Usage: if the trajectory contains at least one call to at least one new skill」「Skill Validity: if all skill-calling actions cause environment changes」/ §3.3「ASI produced programs pass verification for only 15.6% of the turns, whereas AWM adds new skills for 31.4% of the time」/ §3.3 Table 3: 検証済み草案を記憶に置くだけで **32.6 → 36.4(+4.2 pt)**・全部入り 40.1 / 抄録「mainly thanks to the programmatic verification guarantee」 | **検証の段が効果の主因**という定量的先行(+4.2 pt)。**検査を通すと採用率は半分以下になる**(15.6% vs 31.4%)=「起草が出たら採る」ではなく**落ちる前提で設計する**。3 検査は v2 の自動検査へそのまま翻訳できる(§2-C)。**重複排除・統合の記述は無い**(呼ばれた技能を庫へ union するだけ) |
| **2026 のオフライン束**(**[要旨]** 抄録のみ・本文未読): **SkillCAT** [arXiv:2606.13317](https://arxiv.org/abs/2606.13317) / **SkillBrew** [arXiv:2605.29440](https://arxiv.org/abs/2605.29440) / Trace2Skill [arXiv:2603.25158](https://arxiv.org/abs/2603.25158)(検索結果からの言及のみ)/ MIND-Skill [arXiv:2605.08670](https://arxiv.org/abs/2605.08670) | SkillCAT 抄録「derive skill patches from a single trajectory per task, merge them indiscriminately, and load the entire skill corpus during inference」→ 3 段 CCE(同一タスクの成功/失敗対で証拠を取る)・AAE(元タスクのクローンで再生し**悪化しないものだけ**採って階層併合)・TTE。「improves the average score over the initial skill by up to 49.69%」/ SkillBrew 抄録「in an append-only fashion」「redundant, outdated, or harmful」「useful for the agent, diverse in its content, and provide good coverage of the query distribution」「Pareto-aware optimization under a utility constraint」「a bi-level propose-then-verify loop」 | **2025→2026 で「オンライン即時追記」から「オフラインで束ねて検証してから入れる」へ論点が移っている**=ユーザー決定は最新側と整合。SkillCAT の AAE(**採る前に元の課題で再生して悪化しないことを確認**)は v2 の「既存腕の退化検査」に対応。SkillBrew は**append-only の害**を正面から述べた最初の論文で、v2 の「語彙上限 24」を「上限」でなく**被覆と多様性の制約**として書き直す道を示す。**いずれも数値は本文未確認(§3 空欄)** |

**問い1 の判定**: 「実行後にライブラリへ書き戻す」系は**豊富にあるが、獲得の判定基準は一様に「頻度」ではなく「1 件の成功 + 検証」**。オンライン(Voyager・ASI・AWM-online)とオフライン(AWM-offline・LearnAct・2026 束)の両系統が存在し、**オフライン側が新しい**。重複排除は**どの一次資料にも自動機構が無い**。

### 1.2 問い2 — 失敗から欠落を見つける系(失敗分類 → 語彙追加の手続きが書かれているか)

| 出典 | 逐語・節 | v2 への含意 |
|---|---|---|
| **MAST / Why Do Multi-Agent LLM Systems Fail?**(Cemri et al. 2025, [arXiv:2503.13657](https://arxiv.org/abs/2503.13657))**[要旨]** abs ページ | 「identifies 14 unique modes」/「clustered into 3 categories: (i) system design issues, (ii) inter-agent misalignment, and (iii) task verification」/「rigorous analysis of 150 traces」/「1600+ annotated traces collected across 7 popular MAS frameworks」/「high inter-annotator agreement (kappa = 0.88)」/ 処方は「highlighting a clear roadmap for future research」まで | **分類学は診断で止まる。語彙・能力の追加手続きは無い**。D-50 の記述(14 型・LLM 注釈器 94%)のうち **14 型と kappa 0.88 は確認・「LLM 注釈器 94%」は抄録に無い**(本文未読=§3 空欄)。v2 で借りるのは**注釈の作法(κ を報告する)**であって分類そのものではない |
| **AgentErrorTaxonomy / Where LLM Agents Fail and How They can Learn From Failures**(Zhu et al. 2025, [arXiv:2509.25370](https://arxiv.org/abs/2509.25370))**[要旨]** abs ページ | 「a modular classification of failure modes spanning memory, reflection, planning, action, and system-level operations」/ AgentErrorBench=「the first dataset of systematically annotated failure trajectories from ALFWorld, GAIA, and WebShop」/ AgentDebug は「isolates root-cause failures and provides corrective feedback」/「24% higher all-correct accuracy and 17% higher step accuracy」/「yielding up to 26% relative improvements in task success」 | **失敗分類 → 修復(corrective feedback)までは繋がるが、行動語彙・道具の追加には繋がらない**。D-50 の記述(計画-行動不一致・書式・引数)は**抄録では確認できない**(§3 空欄)。v2 の段1(失敗フィードバック)は既に結線済みで、この論文が保証するのは**そこまで** |
| **LearnAct / Empowering LLM Agents through Action Learning**(Zhao et al. 2024, [arXiv:2402.15809](https://arxiv.org/abs/2402.15809))**[実読]** §4.1・§4.2・§5.3・§5.5・Table 4/5 | 抄録「LLM agents typically operate within fixed action spaces, limiting their potential for growth」/「LLM revises and updates the currently available actions based on the errors identified in unsuccessful training tasks」/ §4.1「until successfully solving all the instances with no action errors or exceeding maximum optimization steps」/ §4.1「Then a failed problem with action error is sampled with SelectErrorCase operator」/ §4.2「After completing the learning phase, the agent possesses an updated action space and refined policy instructions.」/ §5.3「For each task, we randomly select 3 instances for the training set」「The sampling number in our method is set to 4.」/ §5.5「achieving optimal results within just two iterations」・「excessive optimization for these mistakes can lead to overfitting to specific training cases」 | **問い2 に正面から答える唯一の一次資料**。(i) **失敗が引き金**(1 反復に失敗 1 件をサンプル)(ii) **オフライン**(学習相のあとテスト相では学習しない)(iii) **停止条件は「行動エラーが消えるまで」**、頻度閾値ではない (iv) **2 反復で最適・それ以上は訓練事例への過学習**=「回しすぎると設計者の指紋が濃くなる」の外部裏づけ (v) Table 5: 学習後の平均行動数は **3.75→3.83 / 3.44→3.50**=**行動は増えるがほとんど増えない**。v2 の「24 語 → +1〜2 語/回」という見込みと桁が合う (vi) Table 4: 更新の内訳は **関数更新 0.86〜0.92 / ノート記入 0.08〜0.14**=**大半は既存行の書き換えで、新語の追加は少数派** |
| **MATSim `stuckAndAbort`**(D-50 の軽リサーチ出典) | — | **正規ドメイン(出版社・doi)の散文出典を取得できず**(ソースコードと doxygen しか見つからない)=**§3 空欄**。D-50 の「`stuckAndAbort` イベント」という記述自体は検索上は裏づけがあるが、**本書では一次確認しない**。親が引くなら MATSim 本(DOI つき書籍)の該当章を当たるのが筋 |

**問い2 の判定**: **失敗分類学が語彙追加につながる手続きは、MAST にも AgentErrorTaxonomy にも書かれていない**(いずれも診断・修復まで)。書かれているのは **LearnAct 1 本**で、その形は「オフライン・失敗駆動・少数反復・行動はほとんど増えない」。D-50 の「試みたが環境が支えない行動を採掘して砂場の欠落を監査する研究は見当たらず」は、**本調査でも覆らなかった**(近いのは LearnAct だが、監査でなく性能改善が目的)。

### 1.3 問い3 — 行動空間の発見・affordance 学習(「動詞を足す」でなく「オブジェクトの affordance を足す」先行)

| 出典 | 逐語・節 | v2 への含意 |
|---|---|---|
| **SayCan / Do As I Can, Not As I Say**(Ahn et al. 2022, [arXiv:2204.01691](https://arxiv.org/abs/2204.01691))**[実読]** ar5iv §3・Algorithm 1・§4・§5 | §3「p(cπ\|s,ℓπ) means 'if I ask the robot to do ℓπ, will it do it?'」/ §3「p(cπ\|s,ℓπ) is the value function for the skill if we take the reward to be 1 for successful completion and 0 otherwise.」/ 選択則「π = argmax_{π∈Π} p(cπ\|s,ℓπ) p(ℓπ\|i)」(式番号なし・Algorithm 1 行 8「p_π^combined = p_π^affordance p_π^LLM」)/ §4「we propose 551 skills that span seven skill families and 17 objects」/ §5「we test across 101 instructions from 7 instruction families」「We use 15 objects commonly found in an office kitchen and 5 known locations」/ §3「the decoding of the instruction obtained in this way always consists of skills that are available to the robot」 | **決定台帳 09-17「行動はオブジェクトの affordance 由来」の最強の裏づけ**。SayCan の行動空間 **551 = 動詞族 7 × オブジェクト 17**。**動詞は 7 語しかない**——語彙の規模を決めているのは**オブジェクトの数**。v2 の 24 語(横断 12+役割 12)は SayCan の「7 族」に対応する量で、**足りないのは語ではなくオブジェクト側の affordance 宣言**という読みが立つ。さらに SayCan は **LLM を固定集合の採点器として使う**(自由生成させない)=AB7 の vocab 腕と同じ構え。**affordance は「実行できるか」の価値関数**であり、v2 の「前提条件(エンジン検査)」と同型 |
| **Affordable Generative Agents**(Yu et al. 2024, [arXiv:2402.02053](https://arxiv.org/abs/2402.02053))**[実読]** §3.1・§5.1〜5.3・Fig.3/7・Table 1/4/5 | 抄録「agents can only generate finite behaviors in fixed environments」/ §5.3「An intriguing observation is that after numerous trials, the agents cease to generate new activities.」/ §5.3「This implies that agents can only generate believable behaviors within a certain range.」/ §5.3 乱数は「the variability in text descriptions rather than the diversity of behaviors」に効くだけ / Fig.7 caption「Cumulative number of activity types over run iterations in Generative Agents.」/ §3.1「When the cosine similarity exceeds a set threshold, we consider it a match for the same plan.」「In our implementation, we set the threshold at 0.97.」/ Fig.3: Lifestyle Policy 単体 40.2%・Social Memory 単体 58.6%・全部 31.1% / Table 1: 3 人 4.548M→1.417M(31.1%)・25 人 25.41M→10.86M(42.7%)/ Table 4(VirtualHome): 34327→1189 tok「AGA costs only 3.4% of the baseline」 | **「環境が固定なら行動語彙は飽和する」を実測で言った唯一の一次資料**。v2 の含意は 2 つ: (i) **AB7 open 腕で 2 語に 90% 集中したのは 8B の問題だけでなく、環境の affordance が有限であることの反映かもしれない**=段0 辞書を直しても天井は環境側にある (ii) **新しい行動を出させるために彼らが足したのは新オブジェクトではなく注意の摂動**(「mind wandering」= 記憶から事象をランダム注入。例「toilet is idle」→ トイレ掃除が生まれる)=**オブジェクトが注意に上がれば行動が生まれる**。これは AB7-b(ヒント腕)と C9(位置・注意)の両方に直結。**cosine 0.97 = 重複排除の閾値の唯一の数値先行**(§1.6) |
| **Emergence World**(Akkil et al. 2026, [arXiv:2606.08367](https://arxiv.org/abs/2606.08367))**[実読]** §3.1・§5.2・§5.3・§7.3 | §3.1「Locations have distinct purposes and expose specific affordances.」/ §5.2 **M11: Tool Expansion**「M11 isolates whether the society extends its shared affordances.」(測り方=「custom tools registered in the platform tool registry via the agent-driven creation pipeline」)/ §5.3「Tool expansion was minimal in this run.」「Across all five conditions, logs show exactly two agent-authored tools entering the registry」/ §7.3「An affordance gate, by contrast, is enforced by the runtime」 | **D-50 の「M11 共有アフォーダンス拡張指標」は本文で確認できた**(ただし指標名は「Tool Expansion」)。決定的な数値: **15 日 × 5 世界・120+ の道具を持たせ、エージェントが自分で作った道具はたった 2 件**。=**「エージェントに自分で能力を増やさせる」は、放っておいてもほぼ起きない**。v2 が「オフライン裁定バッチ + 親検収 + ユーザー承認」という**人が通す形**を採るのは、**創発を潰しているのではなく、先行でも創発していない**という位置づけになる。加えて §7.3 の **affordance gate(ランタイムが強制する)vs 自己統治**の対比は、v2 の「前提条件はエンジンが検査する」の外部語彙 |
| **Smart Objects**(Kallmann & Thalmann 1998 EGCAS / 1999 VRST, [DOI 10.1145/323663.323683](https://doi.org/10.1145/323663.323683))**[書誌のみ]** | 本文を読めていない(ACM は 403・著者サイトは接続拒否)。**逐語なし** | 「オブジェクトが自分との相互作用の仕方を持つ」設計の**最古の系譜**として名前だけ記録。v2 の「対象クラスに affordance を宣言する」形の先行にあたる可能性が高いが、**本書では主張の根拠にしない**(§3 空欄・親が引くなら ACM DL 経由) |
| **ACCORD**(Jiang et al. 2026, [arXiv:2606.16432](https://arxiv.org/abs/2606.16432))**[要旨]** | 「User instructions are often underspecified because humans rely on implicit assumptions about the surrounding environment.」/「They act from assumed rather than observed specifics, overlook information they could have gathered」/ AppWorld で GPT-5-mini「from 42.0% to 62.6%」 | **D-50 の記述の訂正候補**: 正式名は **Action-Conditioned Contextual Grounding**で、**抄録に "affordance" の語は無い**。「文脈にアフォーダンスが無いのに行動する=作話」は D-50 側の言い換えであって論文の語彙ではない。主張自体(観測せずに仮定で動く)は v2 の「知覚で濾された見えない穴」に効く |

**問い3 の判定**: 「動詞を足す」でなく「**オブジェクト側に affordance を持たせ、語彙をその直積として持つ**」形は、**SayCan(551=7×17)と Emergence World(場所が affordance を露出)に明示的先行がある**。そして **AGA が「環境が固定なら行動は飽和する」を実測**し、**Emergence World が「自動拡張はほぼ起きない(2 件/15 日/5 世界)」を実測**している。決定台帳 09-17 の原則は**先行に支持され、かつ「自動では増えない」という但し書きつき**。

### 1.4 問い4 — 判例・事例ベース(CBR)と「同じ入力は同じ裁定」の決定論

| 出典 | 逐語・節 | v2 への含意 |
|---|---|---|
| **Aamodt & Plaza 1994**(AI Communications 7(1):39-59, [DOI 10.3233/AIC-1994-7104](https://doi.org/10.3233/AIC-1994-7104))**[実読]**(著者版 PDF を pymupdf で抽出。出版社版は 403)§3.3・§7・§8.1・§8.2・§8.3 | §3.3「1. RETRIEVE the most similar case or cases」「2. REUSE the information and knowledge in that case to solve the problem」「3. REVISE the proposed solution」「4. RETAIN the parts of this experience likely to be useful for future problem solving」(脚注 3「As a mnemonic, try "the four REs".」)/ §7「When a case solution generated by the reuse phase is not correct, an opportunity for learning from failure arises.」/ §8.1「**In CBR the case base is updated no matter how the problem was solved.**」/ §8.1「Failures, i.e. information from the Revise task, may also be extracted and retained, either as separate failure cases or within total-problem cases.」/ §8.3「By modifying the indexing of existing cases, CBR systems learn to become better similarity assessors」 | **CBR の標準は「閾値なし・全件保持」**——「どう解けたかに関わらず事例庫を更新する」。**失敗も事例として保持する**(v2 の未定義行動台帳はまさにこれ)。R8 判例化の 4R は本書で**一次確認できた**([precedent 答申](v2-precedent-system-deep-research.md) の D 等級記述のうち 4R の部分は裏づけ済み)。**ただし「いつ採用するか」の閾値は CBR には無い**——採用は常に起き、問題は**保守(削除)側**に移る(utility problem。本論文の主題外=§3 空欄)。v2 の設計は「保持は全件(台帳)・**契約語彙への昇格は別の関門**」と 2 段に分けるのが CBR と整合 |
| **Non-Determinism of "Deterministic" LLM Settings**(Atil et al. 2024/2025, [arXiv:2408.04667](https://arxiv.org/abs/2408.04667))**[要旨]** abs ページ | 「outputs can vary for the same inputs under settings expected to be deterministic」/ 5 モデル × 8 タスク × 10 回(zero-shot / few-shot)/「We see accuracy variations up to 15% across naturally occurring runs」/「gap of best possible performance to worst possible performance up to 70%」/「none of the LLMs consistently delivers repeatable accuracy across all tasks, much less identical output strings」/ 指標 **TARr@N**(生出力の全一致率)・**TARa@N**(解析後の一致率)/ 原因の推測「non-determinism perhaps essential to the efficient use of compute resources via co-mingled data in input buffers」 | **温度 0 は「同じ入力は同じ裁定」を保証しない**。したがって §7 段4 の「2 回目以降は決定論参照」は **LLM を呼び直す形では実現できない**——**採用済みの契約行を表として引く(辞書・契約表)形でしか決定論にならない**。これはユーザー決定(ラン内に裁定を入れない)を**決定論の側からも支持する**。副産物: **TARr@N / TARa@N は v2 の「同一性の漂流」計測にそのまま使える指標**(#28 決定論レーン) |
| **GPTCache**(Bang 2023, NLP-OSS 2023, pp.212-218, [DOI 10.18653/v1/2023.nlposs-1.24](https://doi.org/10.18653/v1/2023.nlposs-1.24))**[要旨]** | 意味キャッシュ。ヒット時「increase response speed 2-10 times」 | 「キャッシュで決定論を作る」の実装先行。**ただし semantic(近似)キャッシュは同一性を保証しない**——v2 の裁定台帳が要るのは**完全一致キー**(未定義語の正規化文字列 + 語彙版)。**近似一致を使うと「似た語が同じ裁定に吸われる」=段0 辞書の意味損失と同じ事故を再生産する** |

**問い4 の判定**: CBR 側は **4R と「全件保持・失敗も保持」まで一次確認できた**。**「LLM で同じ入力は同じ裁定」を保証する先行は見つからなかった**——見つかったのは逆の結果(温度 0 でも同一文字列は出ない)と、キャッシュという回避策。**決定論は LLM の外(表参照)でしか作れない**が、これは v2 の設計(採用後は契約表)と一致する。

### 1.5 問い5 — 人間の活動語彙の規模(「24 語は少ないのか」の外部基準)

| 出典 | 逐語・節 | 数(親が再計算できる形) |
|---|---|---|
| **社会生活基本調査(令和3年)用語の解説(調査票A関係)**([結果ページ](https://www.stat.go.jp/data/shakai/2021/kekka.html) の `kaisetsua.pdf`)**[実読]**(pymupdf 抽出)3.「1 日の生活時間に関する事項」28 行動の種類 | 「**１日の行動を20 種類に分類し**、時間帯(15 分単位)別の行動状況(同時に２種類以上の行動をした場合は、主なもの１つ)を調査した。」/「20種類の行動を大きく３つの活動にまとめ、睡眠、食事など生理的に必要な活動を「１次活動」…」 | **20 種**。一覧(同 PDF の図): 睡眠 / 身の回りの用事 / 食事 / 通勤・通学 / 仕事 / 学業 / 家事 / 介護・看護 / 育児 / 買い物 / 移動(通勤・通学を除く)/ テレビ・ラジオ・新聞・雑誌 / 休養・くつろぎ / 学習・自己啓発・訓練(学業以外)/ 趣味・娯楽 / スポーツ / ボランティア活動・社会参加活動 / 交際・付き合い / 受診・療養 / その他 |
| **同・用語の解説(調査票B関係)**(`kaisetsub.pdf`)**[実読]** 3.「1 日の生活時間に関する事項」26 行動の種類 | 「**行動を大分類６種類、中分類22 種類、小分類90 種類に分類した。**なお、一部結果表においては、小分類を組み直し、調査票Ａによる行動分類(**全20 種類**)及び国際比較用(ＥＵ区分)の分類でも集計している。」 | **6 / 22 / 90**。**同じ観測を 3 つの粒度 + EU 区分で集計している**=「1 つの正しい語彙」は存在せず、**粒度は用途ごとに選ばれ、対応表で往復する** |
| **ATUS Activity Lexicon 2025**([bls.gov/tus/lexicons.htm](https://www.bls.gov/tus/lexicons.htm) と `lexicons/lexiconnoex2025.pdf`)**[実読]**(PDF 32 頁を pymupdf + 座標で再計数) | ページ本文「The ATUS Activity Coding Lexicon is a 3-tiered classification system with 17 first-tier categories.」/「Respondents' reported activities are assigned 6-digit activity codes based on this classification system.」/「Activity codes are periodically evaluated and updated prior to the start of each year's data collection.」 | **再計数(親が再現できる手順: 2 桁コードの x 座標で階層を判定)**: 見出し行 **18**(01〜16・18 Traveling・50 Data Codes)→ BLS の「17」は **50 Data Codes を除いた数**。**2 段目 110・3 段目(= 6 桁コード)465(重複なし)**。内訳の極端値: **Traveling(18)だけで 76**・Sports(13) 77・**Eating and Drinking(11) はわずか 5**・Data Codes(50) 6 |

**問い5 の判定**: **24 語は「少ない」とは言えない**——公的な生活時間調査の**第一階層は 17〜20 語**で、v2 の 24 語(横断 12 + 役割 12)はまさにその桁。**問題は語数ではなく 3 点**:
1. **粒度の階層が無い**。日米の公式分類は「粗い 17〜20」と「細かい 90 / 465」を**両方持ち、対応表で往復する**。v2 は 24 語の 1 層しか持たず、段0 辞書が**非公式の第 2 層**として機能してしまっている([語彙政策 v0](../design/v2-synonym-policy-v0.md) の 100 行)。
2. **「食事」が無いのは公式分類に照らして異常**。ATUS は独立の一次カテゴリ(11 Eating and Drinking)、社会生活基本調査は 20 種の 1 つ(食事)。**AB7 で 35% が食事に流れたのは 8B の癖ではなく、人間の活動分布として正常**。
3. **移動は「動詞 × 目的」で膨らむ**。ATUS の 465 コードのうち **76(16%)が Traveling** で、すべて「〜のための移動」。v2 の「移動+対象」「対象の損失 17 行(帰宅・通勤・探索)」は、**公式分類では対象こそがコードの本体**。

### 1.6 問い6 — 閾値と重複排除の先行

| 論点 | 先行にあるか | 逐語・出所 |
|---|---|---|
| **「N 体/N 回が試みたら登録」の頻度閾値** | **見つからなかった** | Voyager=1 回の成功(§2.3)・ASI=1 episode ごと(§2.2)・LearnAct=失敗 1 件ごと(§4.1)・AWM=数値なし(「repetitive subset ... across multiple tasks」を LM が判断)・CBR=全件保持(§8.1)。**6 本の一次資料のいずれにも頻度閾値は無い** |
| **重要度・スコアの閾値** | **ある(1 件)** | Generative Agents(Park et al. 2023, [arXiv:2304.03442](https://arxiv.org/abs/2304.03442))**[実読]** §4.2「we generate reflections when the sum of the importance scores for the latest events perceived by the agents」…「exceeds a threshold (**150 in our implementation**)」/「In practice, our agents reflected roughly two or three times a day.」/ §4.1 重要度は「On the scale of 1 to 10, where 1 is purely mundane ... and 10 is extremely poignant」。25 体・2 ゲーム日 |
| **類似度の閾値(重複排除)** | **ある(1 件)** | AGA §3.1「When the cosine similarity exceeds a set threshold, we consider it a match for the same plan.」「**In our implementation, we set the threshold at 0.97.**」 |
| **自動の重複排除・統合** | **ほぼ無い** | Voyager・ASI・LearnAct=記述なし / AWM=プロンプト指示「Do not generate similar or overlapping workflows.」のみ / 2026 の SkillBrew が**「append-only の害」を初めて正面から問題化**(抄録のみ) |
| **剪定・削除** | **無い(2026 に問題提起が出たところ)** | Voyager「ever-growing」。SkillBrew 抄録「redundant, outdated, or harmful」。CBR の utility problem は本書では未読(§3 空欄) |

**問い6 の判定**: **頻度閾値 N の先行は無い**。存在するのは「重要度の和の閾値(150)」と「類似度の閾値(0.97)」で、**いずれも著者が "in our implementation" と明記している**=先行研究でも**閾値は指紋として宣言されている**。したがって **v2 の閾値 N=10 は、先行に倣うなら「指紋として宣言する」が正解**であり、隠して較正パラメータと呼ぶのは先行の作法と違う。

---

## §2 設計アジェンダの候補(親が設計書に写す決定項)

> **推奨は書くが決定は親とユーザー**。各項に「先行の裏づけ」と「指紋になる部分」を分けて書く。

| # | 決定項 | 選択肢 | 先行の裏づけ | 指紋になる部分 | サブの推奨(参考) |
|---|---|---|---|---|---|
| **A** | **閾値 N の置き方** | (a) 現行どおり N 体(10)で起草へ / (b) 閾値を撤廃し**全件を台帳に保持**・起草へ回す件数だけを**予算**で切る / (c) 頻度でなく**被覆**(何体・何セル・何時間帯に跨るか)で順位づけ | **頻度閾値の先行は無い**(§1.6)。CBR は全件保持(§8.1)。D-50 の順位案(頻度 × 多様性 × 現実パターン)は (c) に近い | 「10」も「予算の件数」も指紋。**どちらにせよ宣言が要る** | **(b)+(c)**。保持は全件(CBR と整合)、**N は「意味の閾値」でなく「1 バッチで裁定に回す件数の費用上限」として定義し直す**と、指紋が「意味の判断」から「予算」に降格する |
| **B** | **草案の形式** | (a) 契約行 6 欄(対象/前提/効果/コスト/失敗の意味論/タグ)+ パターン台帳照合 1 行(現行 §7 のまま)/ (b) 実行可能なテスト付き(失敗コード名・保存則の科目名を必須欄に)/ (c) 自由文 | ASI: **検証できる形にしたことが効果の主因**(+4.2 pt・§3.3)。LearnAct: 更新の 86〜92% は**既存行の書き換え**で新語追加は少数 | 欄の並び・必須欄の選択 | **(b)**。§7 の 6 欄に **「失敗コード名」「触れる保存則の科目」「モックで発火を確認するテスト ID」を必須**にする。**草案テンプレに「既存行の書き換えか新語か」を選ばせる**(LearnAct の内訳に合わせる) |
| **C** | **検証の段(自動検査)** | ASI の 3 検査 + SkillCAT の AAE + v2 固有 | ASI §2.3 の Correctness / Skill Usage / Skill Validity。SkillCAT の AAE(**元タスクのクローンで再生し悪化しないものだけ採る**) | 合格線の数値 | **4 検査**: ①**正しさ**=モック 5,000 体で契約行が発火し保存則が閉じる ②**使用**=未定義台帳の該当行が実測で減る(減らなければ却下)③**妥当性**=世界状態が実際に変わる(空振り却下)④**非退化**=既存腕(vocab/open)の JSD と性能予算が悪化しない。④が SkillCAT の AAE に対応 |
| **D** | **オフライン / 日次締め / オンライン** | (a) ラン後のオフラインバッチ(ユーザー決定)/ (b) シミュ日ごとの締め / (c) ラン内リアルタイム | **オフラインは AWM-offline・LearnAct・2026 束(SkillCAT/Trace2Skill)**。**オンラインは Voyager・ASI・AWM-online だが、AWM §3.2.2 に誤獲得で性能が下がる実例**。決定論の面でも温度 0 は同一を保証しない(§1.4) | **(b) 日次締めには先行が無い**=採るなら expedient と明示 | **(a)**(ユーザー決定どおり)。先行の新しい側と一致し、決定論・再現性(テープ再生)とも両立する。**(b) を将来やるなら「先行なし」と宣言** |
| **E** | **オブジェクト由来の原則との関係** | (a) 契約表に動詞を足す / (b) **オブジェクト(対象クラス)に affordance を足し、語彙はその直積**/ (c) 両方 | SayCan: **551 = 動詞族 7 × オブジェクト 17**(§4)。Emergence World §3.1「Locations ... expose specific affordances.」。AGA: 固定環境では行動は飽和(§5.3) | 直積のどこを「語」と呼ぶか | **(b) を第一候補**。「食事」は**動詞の追加ではなく、飲食店オブジェクトの affordance**(前提=飲食店内・在庫/価格・効果=満腹↑ 所持金↓)として書ける。**契約表の行を「(対象クラス, affordance)」に正規化できるか**を先に決めると、以後の語彙増加が**世界カタログ 57 クラスの側の作業**になり、設計者の指紋が薄くなる |
| **F** | **語彙の版管理** | (a) 版を上げて次ランから有効(親案)/ (b) ラン中に切替 | **ATUS が明示的先行**: 「Activity codes are periodically evaluated and updated **prior to the start of each year's data collection**」+ 多年ファイル用の別 lexicon(単年ファイルに適用してはいけない)。社会生活基本調査は **B 票 90 小分類を A 票 20 に組み直して集計**=**対応表で往復する** | 版の刻み方(ラン単位か週単位か) | **(a)**。加えて **(i) 版はランの開始前にのみ切る (ii) manifest に版を載せテストで固定(語彙政策 v0 の 3 点セットを拡張)(iii) 旧テープは旧版で読む (iv) 版を跨ぐ比較には対応表を作る**——(iv) は ATUS と社会生活基本調査の両方が実際にやっている作法 |
| **G** | **指紋の宣言の仕方** | (a) §8 expedient 登録簿に 1 行 / (b) 語彙政策 v0 に節を足す / (c) 両方 + 感度試験 ID | Generative Agents は本文で「150 **in our implementation**」、AGA は「0.97 **in our implementation**」と宣言している=**先行も閾値を指紋として明記する** | — | **(c)**。宣言すべき指紋は最低 6 つ: **閾値 N / 草案の欄と並び / 裁定モデルと温度 / 4 検査の合格線 / 採用の順序(食事 → 観察・注意 → 知らせる・対応する)/ 版の切り方**。各項に感度試験 ID を振る |
| **H** | **決定論的参照(段4)** | (a) 採用済み語彙は契約表参照(LLM を呼ばない)/ (b) 温度 0 で呼び直す / (c) 完全一致キャッシュ | **(b) は成立しない**(温度 0 でも同一文字列は出ない・§1.4)。(c) は GPTCache 系だが**意味キャッシュは不可**(近似一致は段0 辞書と同じ意味損失を生む) | キャッシュキーの正規化規則 | **(a)**。裁定 LLM の出力は**草案の一度きり**でランには入らない。キャッシュを使う場合は**(未定義語の正規化文字列 + 語彙版)の完全一致キー**に限る |
| **I** | **重複排除** | (a) 人手(親検収)/ (b) 既存語との距離を台帳に列で持つ / (c) 埋め込み類似の自動却下 | 自動 dedup の先行は事実上無い(§1.6)。AWM はプロンプト指示、AGA は cosine 0.97(ただし**計画の同一判定**であって語彙の重複排除ではない) | 距離の定義・閾値 | **(a)+(b)**。24 語規模では人手で足りる。台帳に **「段0 辞書の写像先」「[語彙政策 v0](../design/v2-synonym-policy-v0.md) の意味損失分類」** を列として持たせれば、**「既に別の語に畳まれている」候補が自動で見える**。(c) は閾値が新しい指紋になるので推奨しない |
| **J** | **保守(剪定)を最初から設計に入れるか** | (a) 入れる(採用語の使用率を計測し、使われない語は版を上げて外す)/ (b) 入れない | SkillBrew が **append-only の害**(redundant / outdated / harmful)を問題化。Voyager の「ever-growing」は D-50 が弱点として既に指摘 | 退役の基準 | **(a) の計測だけ先に入れる**(語ごとの使用率を manifest に出す)。**退役の基準は決めない**(データが出てから) |

---

## §3 空欄(読めなかったもの・見つからなかったもの)

1. **MATSim `stuckAndAbort` の散文出典**(正規ドメイン)を取得できなかった。見つかったのはソースコードと doxygen のみ。D-50 の記述は**本書では一次確認していない**。
2. **Kallmann & Thalmann の Smart Objects 本文**。ACM DL は 403、著者サイトは接続拒否。**書誌のみ**で、逐語なし。
3. **2026 のオフライン束は全て抄録のみ**: SkillCAT(「三つの決定」「single-trace bias / unvalidated merging / context overload」という語は**抄録には無い**——本文にある可能性)・SkillBrew(**数値ゼロ**: 技能数・閾値・被覆のトレードオフの数字は抄録に無い)・Trace2Skill(**検索結果での言及のみ・abs 未取得**)・MIND-Skill(抄録のみ)。
4. **Voyager の付録**(剪定・重複排除の有無)。ar5iv の取得が途中で切れており、**「剪定機構は無い」は本文範囲での判定**。
5. **AGA Fig.7 の飽和点の数値**(何種類で頭打ちか・何反復か)。図にしか無く、本文に数値なし。
6. **ATUS の 6 桁コード総数の公式値**。BLS のページには載っていない。**本書の 465 は PDF からの再計数**(手順は §1.5 に明記・親が再現可能)。
7. **社会生活基本調査 別表2「詳細行動分類一覧」本体**(小分類 90 の一覧)は未取得。件数(6/22/90)は用語の解説の本文から。
8. **MAST の 14 型の一覧**と「LLM 注釈器 94%」(D-50 の記述)は**抄録では確認できず**。本文未読。
9. **AgentErrorTaxonomy の型の一覧**(D-50 の「計画-行動不一致・書式・引数」)も抄録では確認できず。
10. **CBR の utility problem / competence model(Smyth & Cunningham 1996, Smyth & Keane 1995)**は未取得。[precedent 答申](v2-precedent-system-deep-research.md) の D 等級記述のうち**この部分は依然として未確認**。
11. **「LLM の裁定で同じ入力に同じ出力を保証した」先行**は見つからなかった(見つかったのは反証と、キャッシュという回避策)。
12. **GPTCache は抄録のみ**(ACL Anthology の書誌は確認、本文未読)。
13. **Emergence World の M11 以外の指標の定義**は §5.2 の列挙までしか読めていない。

---

## §4 lit README に足す行(親が [lit/README.md](lit/README.md) の索引表へ写す候補)

| メモ | 分野 | 一次確認 | 何のために引くか |
|---|---|---|---|
| [agents__wang2023_voyager](lit/agents__wang2023_voyager.md) | 自然言語処理 #27 / ABM方法論 #21 | B(サブ実読・親未確認) | **獲得の閾値は「1 回の成功 + 自己検証」**・オンライン書き戻し・**剪定なし**。D-71 で採らない道の基準線 |
| [agents__wang2024_workflow-memory](lit/agents__wang2024_workflow-memory.md) | 自然言語処理 #27 / ABM方法論 #21 | B(サブ実読・親未確認) | **オフラインとオンラインが同じ枠で成立**する唯一の明示先行・**オンライン獲得が性能を下げる実例**(§3.2.2) |
| [agents__wang2025_programmatic-skill-induction](lit/agents__wang2025_programmatic-skill-induction.md) | 自然言語処理 #27 / ソフトウェア工学 #29 | B(サブ実読・親未確認) | **検証の段が効果の主因(+4.2 pt)**・3 検査(Correctness/Usage/Validity)・**採用率 15.6%** |
| [agents__zhao2024_learnact](lit/agents__zhao2024_learnact.md) | ABM方法論 #21 / 自然言語処理 #27 | B(サブ実読・親未確認) | **失敗 → 行動追加をオフラインでやる唯一の先行**・**2 反復で最適・行動は 3.75→3.83 しか増えない** |
| [agents__yu2024_affordable-generative-agents](lit/agents__yu2024_affordable-generative-agents.md) | 計算社会科学 #25 / 認知科学 #12 | B(サブ実読・親未確認) | **固定環境では行動語彙が飽和する**(実測)・**cosine 0.97 = 重複判定の唯一の数値先行**・費用 31.1% |
| [agents__ahn2022_saycan](lit/agents__ahn2022_saycan.md) | 自然言語処理 #27 / ABM方法論 #21 | B(サブ実読・親未確認) | **551 = 動詞族 7 × オブジェクト 17**=「オブジェクト由来」原則の定量的裏づけ・affordance = 前提条件の価値関数 |
| [cbr__aamodt1994_cbr-cycle](lit/cbr__aamodt1994_cbr-cycle.md) | 法学 #11 / ABM方法論 #21 | B(サブ実読・著者版 PDF・親未確認) | **4R の原典**・**「どう解けたかに関わらず事例庫を更新する」=閾値なし全件保持**・失敗も事例 |
| [nlp__atil2024_nondeterminism](lit/nlp__atil2024_nondeterminism.md) | 計算機科学(並列・決定論)#28 / 自然言語処理 #27 | B(サブ実読=抄録・親未確認) | **温度 0 は同一出力を保証しない**=段4 の決定論は表参照でしか作れない・**TARr@N / TARa@N** |

**メモを作らなかったが本書で引いた出典**(親が必要と判断したら切り出す): MAST(2503.13657)・AgentErrorTaxonomy(2509.25370)・Emergence World(2606.08367)・ACCORD(2606.16432)・Generative Agents(2304.03442)・SkillCAT(2606.13317)・SkillBrew(2605.29440)・GPTCache(2023.nlposs-1.24)・ATUS lexicon(bls.gov)・社会生活基本調査 用語の解説(stat.go.jp)。ATUS と社会生活基本調査の数値は §1.5 に再計算手順つきで載せた。
