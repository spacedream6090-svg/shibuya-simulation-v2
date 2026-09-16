# R-2 — LLM 社会シミュレーション文献 12 件の本文実読(答申・2026-09-16)

<!-- hdr:v1 -->
- **分野**: 計算社会科学 #25 / 検証と V&V #22 / 自然言語処理 #27 / 統計学・因果推論 #23 / 計算機科学(並列)#28 | **重要度**: **P1**
- **一次確認**: **B → 4/12 は親確認(第202)**: OASIS(Table 2 の 6 値+超線形の割り算)・GAMA(Table 3 の 10 行+倍率)・Ye(事前登録の語の不在+TRAILS 構成)・Larooij(35/15/22・pre-registered・data leakage を Springer OA PDF で逐語)。残り 8 件はサブ実読のみ(親未確認)。12 件すべて arXiv abs ページで実在・題名・著者・版・Comments 欄を確認し、11 件は `arxiv.org/html/<id>` の本文、1 件(B-6)は PMC 全文を WebFetch で取得した(2026-09-16)。**逐語は取得した HTML の範囲**であり、図の中の数値・切れた付録は取っていない(§3)。
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **進行状況**: [RESEARCH-STATE.md](RESEARCH-STATE.md) §2-B ・ **出所**: [v2-llm-social-sim-timeline-seed.md](v2-llm-social-sim-timeline-seed.md) §4

> 位置づけ: [RESEARCH-STATE](RESEARCH-STATE.md) §2-B の実行票 B-1〜B-12 を消化した報告。各件の詳細は `lit/` の 1 論文 1 メモへ切り出した(§4)。本書は**判定と含意だけ**。
> **決定はしない。**§2 は決定アジェンダへ写す候補であって、採否は親とユーザーが決める。

---

## 1. 判定表(12 件)

| # | 論文 | 確かめること | 本文の逐語・節/表 | 判定 | v2 への含意(1 行) |
|---|---|---|---|---|---|
| **B-1** | Choi et al. — Identity Drift([メモ](lit/nlp__choi2025_identity-drift.md)・2412.00804 v2) | 「大きいモデルほど漂う」の効果量 | **効果量は存在しない。**根拠は **Table 3** の「有意に動かなかった下位尺度の数」(40 中: GPT-4o **5** / LLaMA 8B **23** / 70B **6** / 405B **7** / Mixtral 8x7B **27** / Qwen2 7B **20**)。最強の言い方が §4「**parameter sizes showed a large impact on consistency**」。相関係数・p 値・効果量は本文に**一つも無い** | **第2陣で採用(測り方だけ)** | 8B 級はむしろ安定側=D-68 の同一性設計に追い風だが、**「大きいほど漂う」を数値の根拠に引いてはいけない** |
| **B-2** | Taubenfeld et al. — Debate Biases([メモ](lit/nlp__taubenfeld2024_debate-biases.md)・2402.04049 v3・EMNLP 2024 main) | 党派ペルソナの基底回帰の大きさ | **回帰の大きさは図の中だけ(空欄)。**文字で取れるのは **Table 1**(Racism・Default 体の自己申告 0〜10): 素の Mistral 7B **8.4** → 共和党方向へ微調整すると r=256 で **1.9**、DPO で **0.4**(同時に MMLU 59.0→48.6)。回帰の逐語は定性のみ「**agents tend to adopt more moderate positions, aligning more closely with the LLM's inherent bias.**」。基底の向き「**the default agent shows a bias toward the democrat perspective**」。40 反復・変化の大半は iteration 3 まで | **該当せず(D-56/D-59 と同根とは言えない)+ 測り方は第2陣で採用** | 示されたのは「指示した立場より基底の傾きが勝つ」であって「刺激に過剰反応する」ではない=**広告の過剰反応と同根という読みは本文に根拠が無い**。借りるのは**帰無腕(立場を指示しない Default)を必ず置く**作法 |
| **B-3** | Rozanov & Rei — StateAct([メモ](lit/agents__rozanov2025_stateact.md)・2410.02810 v3) | 状態を出力内に書く方式の効果(数値) | **Table 3**(逐語): ReAct 「**63.7, 68.15 and 72.59, while StateAct achieves 77.04 (+13.3), 71.85(+3.7) and 83.70(+11.2)**」。**Table 6** の部品分解で、状態が効くのは Webshop(State+Act **0.31** が最良)・目標が効くのは Alfworld(Goal+Act 0.63)・thought は Webshop で**害**(0.18)。**Table 5** 平均手数 ReAct 31.49 → StateAct **19.11**。**Table 7**: 書式を JSON にすると StateAct は 77.04→**58.52(−18.5)**。脚注 6「**our cost remains similar to ReAct, at around $8 for the full Alfworld run**」 | **第2陣で採用(腕として)** | この repo は既に「理由を先に書かせる」=thought 相当を持つが、**状態の書き戻し欄は無い**。o64 既定では入らないので**腕にするなら出力予算の変更が要る**。JSON で −18.5 は「厳密 JSON を課さない」既定の外部裏づけ |
| **B-4** | Goodyear et al. — State Representation([メモ](lit/agents__goodyear2025_state-representation.md)・2506.15624 v1) | どの書き方が均衡に近づくか | 3 軸(逐語): 「**O if only an agent's own action history is included; E if all agents' action history is included**」/「**P for payoff-based feedback; R for regret-based feedback**」/「**F for full-chat, S for summarized**」。§5.4「**the representation that resulted in LLM behavior closest to equilibrium**」= **S-RO**。**Table 1**(Game B 橋経路・均衡 18): S-RO **17.71** > 人間 14.82 > MWU 13.87 > EXP3 13.81 > F-PE **4.74**。Game A は平均が全部 9 付近で**標準誤差だけが違う**(要約 2.11〜3.52 / 全文 6.71〜7.99)。「**regrets are 4-5x lower using summarized representations in Game A**」。18 体・40 ラウンド・gpt-4o | **採用済み(2/3 軸)+ 第2陣で採用(1 軸)** | この repo は**要約**(完全現在形)と**後悔情報**(B6 直前の結果)を既に採っている。採っていないのは「**他者情報は少ない方が均衡に近い**」= B5 の近接 k に **k=0 の腕**を足す根拠。**平均でなく試行間分散で判定せよ**が最大の持ち帰り |
| **B-5** | Alves et al. — GAMA+Agno([メモ](lit/compute__alves2026_llm-urban-mobility.md)・2607.02716 v1) | **表 3 の計算費** | **Table 3**「**Computational cost and robustness analysis of the evaluated approaches,**」「**reporting average simulation time and error rate across simulations.**」 500 体: 規則 **21.92 s** / LLM 79.40〜111.50 s。1000 体: 規則 **58.40 s** / LLM 152.50〜239.67 s。10 seed・540 サイクル・Gemini 2.5 Flash-Lite と GPT-4o Mini(API 越し)。本文の逐語は「**results in a substantial increase in computational cost compared to the rule-based baseline**」のみで**倍率の文は無い** | **採用(D-70 の 4 例目)・ただし正規化が要る** | **有志の「3〜5 倍」は Table 3 で裏づけられる**(サブ再計算: 500 体 **3.62〜5.09 倍**・1000 体 **2.61〜4.10 倍**)。副産物: **記憶を足すと +29.7〜43.8%・書式エラー率が約 2 倍**=第2陣の記憶の値段の当たり |
| **B-6** | Larooij & Törnberg([メモ](lit/validation__larooij2025_generative-abm-validation.md)・AI Review 59(1) 15・PMC 全文) | face-validity 依存とデータ漏洩の警告の具体 | 35 本(209 本から選別・Scopus 2025-03-27)。**Table 2**: 主たる検証が「よく知られた社会パターン」**14 本(40%)**「人の判断」12(34%)「人が生成したデータ」12(34%)。「**15 out of 35 studies rely solely on subjective assessments**」「**and 22 use such assessments as their primary validation method**」。face validity「**At worst, validation consists of asking an LLM to evaluate the plausibility of its own output**」「**"calibration" is thus reduced to prompt engineering**」。漏洩「**what may appear as emergent dynamic can instead stem from a form of "data leakage"**」「**Data leakage represents a serious risk for such validation approaches**」。提言「**pre-registered experimental benchmarks, rather than face-validity alone**」「**results reported across multiple runs and, where feasible, limited sensitivity checks**」 | **採用済み(この repo の作法の外部根拠)** | **提言 3 点のうち 1(目的整合)2(事前登録ベンチ)は満たしている。3(多ラン+感度)が未実施**=S1 の 8 seed。★ **漏洩は「公刊された stylized facts での検証」に固有**なので、**封印した在圏データは漏洩の筋では汚れにくい**=本 repo の位置どりの外部根拠。逆に[パターン台帳](../design/v2-pattern-ledger.md) A2 の類は疑いがかかる |
| **B-7** | Li & Tao — Not (Yet) Sufficient([メモ](lit/mas__li2026_agents-not-sufficient.md)・2603.00113 v2) | 処方側の記述があるか | **ある。**§4「**Actions for Future Social Simulation**」に番号つき 3 つ:「**Treat the environment as a first-class, auditable object**」「**Move evaluation beyond plausibility to mechanistic and counterfactual reliability**」「**Interpret simulation outcomes with epistemic caution and explicit uncertainty**」。手段は「**mechanism ablations, negative controls, and counterfactual sweeps that vary one component at a time**」、報告は「**reported as distributions (e.g., uncertainty intervals and variance decomposition) rather than selected trajectories**」。Definition 4.1 で **Vis(曝露)・Sch(スケジューリング)・Tr・D₀** を形式化 | **採用済み(実装が先行)+ 語彙を採用** | **親の「脆さ側」と有志の「処方側」はどちらも本文にある**(§3 診断・§4 処方)=[時系列の種](v2-llm-social-sim-timeline-seed.md) #12 の △ は**両方 ✔ に更新できる**。この repo は Vis(知覚 3 層+p_notice)・Sch(起床条件+繰り延べ 4 クラス)・Tr(世界過程)を**既に明示的に持つ数少ない実装**。薄いのは **D₀ の初期網構造** |
| **B-8** | Ye et al. — Robustness Audits([メモ](lit/validation__ye2026_robustness-audits.md)・2605.18890 v1) | 事前登録の推奨が本文にあるか・TRAILS 3 層の中身 | **事前登録の語は本文(§1〜6)に無い。**最も近いのは §6「**report which perturbations were tested, which findings remained stable, which findings were sensitive**」。**TRAILS は 2 部構成**(Table 1): **TRAILS-D** = Micro(Model substrate / Agent specification / Internal state and cognition / Memory and temporality)・Meso(Interaction protocol / Intervention design)・Macro(Environment structure / Population and scale)、**TRAILS-R**(層なし)= Representational format / Instruction hierarchy / Linguistic framing / Context representation / Interaction sequencing。76 pt の中身: gpt-5.2・ペルソナ**書式**・10 ラウンド囚人のジレンマ・「**Descriptive personas cooperate 76 percentage points less often than Plain personas**」・「**gpt-5.2, N=30 seeds per condition**」。1 pt は **deepseek-v3** | **第2陣で採用(C8 の被覆表として)** | ★ **事前登録は外部根拠が無い**=[時系列の種](v2-llm-social-sim-timeline-seed.md) #14 は**本件の中にも無く、引き続き空欄**。事前登録の唯一の外部根拠は **B-6 の 1 行**。TRAILS-D 8 次元に現行 C8 第1陣 6 本を当てると、**Model substrate と Agent specification と TRAILS-R 5 次元が空白**(v1 の `ablate.prompt_paraphrase` が v2 に移っていない穴) |
| **B-9** | Shah — Causal Agent Replay([メモ](lit/causal__shah2026_agent-replay.md)・2606.08275 v1) | 介入再生の手続き | 擬似コードは無い(散文)。§4「**hold steps [0,k) at their factual actions, apply do_resample(k), and run forward K times**」。「**An intervention is a do(·) operation on one variable, after which the agent re-decides everything downstream.**」介入代数 5 種 = `do_resample`(**the null intervention**)/`do_action`/`do_observation`/`do_context`/`do_policy`。**point-of-commitment 則** =「**the latest step whose effect's confidence interval still excludes zero**」、潰す交絡は「**resampling step k also re-rolls every downstream stochastic step**」ので「**an early irrelevant step shows an effect too**」。区間は Wilson + ブートストラップ。K の値は本文に無い | **第2陣で採用(検死の道具)** | ★ **共通乱数は「hard across divergent LLM contexts」として将来課題**だが、本論文自身が「**a single-stream local model with a fixed seed replays exactly**」と書いている=**ローカル艦隊のこの repo は共通乱数を持てる側**。持っていないのは `do_action`/`do_observation`/`do_context` の口。**1 体 1 日は 6.94 呼**なので個体単位の介入再生は安い |
| **B-10** | Abootorabi et al. — Steering Geometry([メモ](lit/nlp__abootorabi2026_steering-geometry.md)・2609.06289 v1・EMNLP 2026 main) | 指示微調整後の劣化の程度 | **Table 1**(Qwen3.5-9B・ρ_T): SAS **0.5069 → 0.3256** / CAA 0.4606 → 0.2351 / SphericalSteer 0.3962 → 0.2048 / BiPO 0.1188 → **−0.0104** / Cold-Steer 0.0265 → **−0.0568**。「**All methods show consistent degradation when moving from base to instruction-tuned models (Table 1).**」規模則「**ρT rises sharply from Falcon-7B (0.20) to Mistral-7B (0.32), Llama-3.1-8B (0.37), and Qwen3.5-9B (0.46)**」。**base vs instruct の比較は 1 モデルのみ** | **該当せず(採らない道の確認)** | 憲法の分業上、活性化に介入する道は採らない。**副次的含意**: この repo は **instruct モデル(Qwen3-8B INT8)**を使うので、**価値ベースの個体差設計は弱い**と予測できる=「多様性は LLM から自ずと」の選好と整合。有志の「動かすと壊れる」は**本文の主張ではない**(親の読み #17 △ が正しい) |
| **B-11** | Lu et al. — Procedural Graphs([メモ](lit/memory__lu2026_procedural-graphs.md)・2609.09153 v1) | 手続き知識グラフの表現 | 𝒢 = (𝒱, ℛ, ℰ, Φ)。「**each element of ℰ is a directed, attributed triplet**」。ノードは「**a tool function, a skill, an internal reasoning step, or a task status**」。**属性は辺に載る**:「**we use three textual fields: condition, guidance, and pitfalls**」。関係は 4 種「**LEADS_TO, TRIGGERS, PROVIDES_INPUT_FOR, and CONVERGES_TO**」。グラフは 7〜17 ノード。位置決めは直近手続きの**完全一致**・h=2 ホップ・窓 w=3。編集は Add / Delete の 2 つだけ、受理は **S_val(候補) ≥ S_val(現行)**。Table 3 の費用「**total token consumption remains 33.4% and 55.4% higher**」(手数は減る) | **第2陣で採用(候補・要ユーザー判断)** | ★ **属性を辺に置く**表現が持ち帰り。この repo の 24 語はノードだけで遷移に何も無い。**段2 `adjudicate`(`adjudicator=None` で未発火)は本論文の「精錬器の編集を検証で漉す」と同じ形**=骨格は既にある。**ただし助言呼が 1 手番 1 回増える**=6.94 → 最悪 13.9 呼/体/日。そのままは入らない。**行動語彙をグラフで絞るのは設計者の指紋を増やす方向**=採否はユーザー判断 |
| **B-12** | Yang et al. — OASIS([メモ](lit/mas__yang2024_oasis.md)・2411.11581 v5) | 1M=18 h/A100×27・100k=3 h/A100×5 の逐語(節・表) | **数値は Table 2(§4.1「Analysis of Efficiency for One Million Users」)にのみ**あり、1M については**散文が無い**。ハードの散文は 1 文「**For all scenarios, we use one A100 for RecSys and use multiple GPUs for LLM inference.**」。100K は散文にある:「**using five A100 GPUs, we can simulate the interactions of 100,000 users over 10 time steps within two days**」(= 4.8 h/step で **Table 2 の 3.0 h と食い違う**)。基盤 LLM「**Llama3-8b-instruct is used as the base LLM.**」。Table 2 に **10K 行(0.2 h / 2 GPU)** も在る | **採用(D-70 の 3 例目)・v1 メモの ★2 数値は一致** | ★★ **最大の所見: OASIS は線形にスケールしていない。**総費用は 10K→100K で **37.5 倍**・100K→1M で **32.4 倍**(= N^1.51〜1.57)。体あたり GPU 秒は **0.144 → 0.540 → 1.750**。体あたり投稿数は 0.142〜0.150 で**一定**なので、増えているのは**環境 DB と推薦系の側**。**本 repo の 0.592 GPU·s/体/シミュ日 は OASIS 100K の 0.540 とほぼ同額** |

---

## 2. 決定アジェンダへ写す候補(**推奨は書くが決定は親とユーザー**)

### 2-1. いま効くもの(S1 までに決めたい)

- **(a) 報告様式を「分布」に変える** — B-7 Action 3 と B-6 提言 3 が同じことを言っている: 結果は**不確実性区間と分散分解**で出し、選んだ軌跡で出さない。**推奨: 採用**。S1 の 8 seed アンサンブルはそのために回す。追加費用ゼロ(報告の形だけ)。
- **(b) 「内部整合性は verification であって validation ではない」を規律にする**(B-6)。**推奨: 採用**。この repo は T2-c テープ再生のハッシュ一致を持つが、これを「検証」と呼ばない。受入表の各行に「主観 / 客観 / 内部整合」の欄を足す。
- **(c) パターン台帳に「データ漏洩の疑い」欄を足す**(B-6)。公刊された stylized fact(べき則・エコーチェンバー等)は LLM の訓練データに入っている可能性がある。**推奨: 採用**(1 列足すだけ)。副産物として **封印データが漏洩に強い**ことを台帳の上で言えるようになる。
- **(d) TRAILS の被覆表を C8 に付ける**(B-8)。TRAILS-D 8 次元 × TRAILS-R 5 次元のうち、**何を監査し何を未監査と宣言するか**を 1 枚にする。**推奨: 採用(表だけ・ランは増やさない)**。現状の空白は **Model substrate(モデル同一性)・Agent specification・TRAILS-R 全 5 次元**。
- **(e) v1 の `ablate.prompt_paraphrase`(S-16)を v2 へ戻すか** — TRAILS-R の唯一の実装資産で、v1 にあって v2 に無い(**繋ぎ expedient の置換忘れと同型の穴**)。**推奨: 先に聞く**(生成のやり直しは不要だが、腕が 1 本増える)。

### 2-2. 第2陣の設計ラウンドで論じるもの

- **(f) 知覚テンプレの 3 軸 ablation**(B-4): 要約度 / 結果の与え方 / **他者情報の量**。この repo は前 2 つを既に「良い側」で採っているので、**論点は 3 つ目だけ**。具体案 = B5 の近接 k(疎3/中2/密1)に **k=0 の腕**を足す。**推奨: 第2陣の ablation 第1候補**。判定は**平均でなく試行間分散**で(B-4 の Game A は平均では差が消えた)。
- **(g) 状態の書き戻し欄を腕にするか**(B-3): 出力に「現在地 / 所持 / 直前」を書かせる。**手数が減る効果はこの repo では期待できない**(呼数は計画境界で決まる)ので、**トークン増が素直に乗る**。o64 では入らない=**出力予算の変更が要る**。**推奨: 先に聞く**(性能予算の宣言に触る)。
- **(h) 手続きグラフを第2陣の記憶/習慣の表現候補に入れるか**(B-11): 借りるのは「**属性を辺に置く**(条件・助言・落とし穴)」と「**受理則 = 保留検証で非減少**」と「**却下記録**」。**助言呼で呼数が倍**になるのが最大の障害。**推奨: 表現だけ採り、助言呼は採らない**(段2 `adjudicate` の受理則に非減少条件を足す形)。**ただし行動語彙をグラフで絞るのは設計者の指紋を増やす方向**=ユーザー判断。
- **(i) 同一性の測り方**(B-1): 同一性を**下位尺度の集合**として持ち、**会話の途中 3 時点**で測り、「**有意に動かなかった尺度の数**」で報告する。**推奨: 測り方だけ採用**(結論は引かない)。
- **(j) 帰無腕としての「立場を指示しない体」**(B-2): AB7 は vocab / open の 2 腕ともプロンプトに指示がある。**指示を最小にした第 3 の腕**を置くと、D-73(「行く/食べる」に 90% 集中)が**語彙側か基底側か**を切り分けられる。**推奨: 先に聞く**(腕が増える=サーバー時間)。

### 2-3. 後で効くもの

- **(k) 介入再生(`do_action` / `do_observation` / `do_context`)の口をテープ再生に足すか**(B-9)。**point-of-commitment 則**(効果がゼロを外す最も遅い手番)を知らずに読むと必ず間違えるので、入れるなら則ごと入れる。**個体 1 体 1 日 = 約 7 呼**なので検死は安い。**推奨: 第2陣以降**。
- **(l) D-70 の比較表を「体あたり GPU 秒」で書き直す**(B-5・B-12)。**OASIS が N^1.55 で超線形**であることは、この repo の 40 万体→100 万体の見積もりに直接効く。**この repo は 5,000 と 390,067 の 2 点しか測っていない**ので、**自分の指数を知らない**。**推奨: S1 の副産物として中間規模 1 点を測る**(先に聞く=ランが増える)。

---

## 3. **空欄**(確認できなかったもの・理由)

| # | 空欄 | 理由 |
|---|---|---|
| B-2 | **党派ペルソナの回帰の大きさ(初期値 → 最終値)** | Fig. 3〜9・11〜12 の**画像の中**にしかなく、HTML にも本文にも数表が無い。取るには PDF の図を人が読む必要がある |
| B-4 | LLM の**試行本数**(Table 1 の標準誤差の分母) | 本文に記載が無い。アルゴリズム側(MWU/EXP3)は 50 試行と書いてあるが LLM 側は無い |
| B-4 | 切替回数・後悔の実数値 | Fig. 7〜9・13・15 の画像の中だけ |
| B-5 | Table 3 が **Localized / Extended のどちらか**(あるいは合算) | 表にも本文にも書かれていない |
| B-6 | **Discussion 末尾の提言** | PMC 全文が Discussion の途中で切れた(取得範囲) |
| B-6 | PRISMA の**除外件数の内訳** | Fig. 1 の図中のみ |
| B-7 | **付録 A 以降** | HTML が付録 A の途中で切れた |
| B-8 | **TRAILS の具体例(付録 A・Table 2/3)** | HTML が参考文献の途中で切れた |
| B-8 | **76 pt の絶対値**(基準の協力率と摂動後の協力率) | 本文は差分しか書いていない。Figure 1 の画像を見る必要がある |
| B-8 | **事前登録** | 本文(§1〜6)に語が無い=**空欄ではなく「無い」という確認結果**。[時系列の種](v2-llm-social-sim-timeline-seed.md) #14 は引き続き実体不明 |
| B-9 | **K(ロールアウト本数)の具体値** | 本文に記載が無い(「budget-bounded with a circuit breaker」とだけ) |
| B-10 | **規模別の数値(付録 D)** | HTML が切れた。取れたのは Fig. 3 の本文中の 4 点(Falcon 0.20 / Mistral 0.32 / Llama 0.37 / Qwen 0.46)のみ |
| B-10 | **base vs instruct の他モデル** | 論文自体が Qwen3.5-9B 1 モデルしか出していない(著者側の空欄) |
| B-11 | **精錬器側の計算費(付録 E.1)** | HTML が切れた |
| B-12 | **1M ランの time step 数** | 本文に書かれていない → **1M の総費用が計算できない** |
| B-12 | **1 step あたりの LLM 呼数** | 活性化確率(0.1 / 0.01)は取れたが行動数との積が本文に無い → **呼あたりの正規化ができない** |
| B-12 | v1 メモの「**行動空間 21 種**」「**Time Engine 24 次元の活動ベクトル**」 | 今回の取得範囲(§3.2・§4.1 中心)では該当箇所を見ていない。**引き続き v1 メモ経由の二次** |
| 共通 | **査読の有無** | B-2(EMNLP 2024)と B-10(EMNLP 2026)以外は Comments 欄に会議・誌名が無い。B-3 について[時系列の種](v2-llm-social-sim-timeline-seed.md) #6 が書く「**REALM@ACL 2025**」は **abs ページに見当たらない=出所不明** |

---

## 4. lit README の索引に足すべき 12 行(**README は編集していない**)

```
| [nlp__choi2025_identity-drift](nlp__choi2025_identity-drift.md) | 自然言語処理 #27 / 人格心理学 #13 | B(サブ実読・親未確認) | 「大きいモデルほど漂う」に**効果量は無い**(Table 3 の尺度数だけ)・8B 級は安定側 |
| [nlp__taubenfeld2024_debate-biases](nlp__taubenfeld2024_debate-biases.md) | 計算社会科学 #25 / 自然言語処理 #27 | B(サブ実読・親未確認) | 指示した立場より**基底の傾きが勝つ**・回帰の大きさは図のみ(空欄)・帰無腕(Default)の作法 |
| [agents__rozanov2025_stateact](agents__rozanov2025_stateact.md) | 自然言語処理 #27 / ABM方法論 #21 | B(サブ実読・親未確認) | **状態を出力に書かせる**と +3.7〜13.3 pt・手数 31.5→19.1・**JSON にすると −18.5** |
| [agents__goodyear2025_state-representation](agents__goodyear2025_state-representation.md) | 自然言語処理 #27 / ABM方法論 #21 / 統計学 #23 | B(サブ実読・親未確認) | **要約 × 後悔 × 自分だけ**が均衡に最も近い(17.71/18)・**平均でなく試行間分散で判定せよ** |
| [compute__alves2026_llm-urban-mobility](compute__alves2026_llm-urban-mobility.md) | 計算機科学(並列)#28 / 交通工学 #2 | B(サブ実読・親未確認) | Table 3 で **LLM 判断層は規則ベースの 2.6〜5.1 倍**・**記憶は +30〜44% と誤り率 2 倍** |
| [validation__larooij2025_generative-abm-validation](validation__larooij2025_generative-abm-validation.md) | 検証とV&V #22 / 計算社会科学 #25 / 科学哲学 #26 | B(サブ実読・親未確認) | 35 本中 **15 本が主観のみ**・「公刊パターンでの検証は**データ漏洩**」・**事前登録ベンチの唯一の外部根拠** |
| [mas__li2026_agents-not-sufficient](mas__li2026_agents-not-sufficient.md) | 計算社会科学 #25 / ABM方法論 #21 | B(サブ実読・親未確認) | **処方は §4 の Action 1-3**・**Vis / Sch / Tr / D₀** の語彙・「分布として報告・分散分解」 |
| [validation__ye2026_robustness-audits](validation__ye2026_robustness-audits.md) | 検証とV&V #22 / 計算社会科学 #25 | B(サブ実読・親未確認) | **事前登録は本文に無い**・TRAILS-D 3 層 8 次元 + **TRAILS-R 5 次元**・76 pt = ペルソナ書式・N=30 seed |
| [causal__shah2026_agent-replay](causal__shah2026_agent-replay.md) | 統計学・因果推論 #23 / 計算機科学 #28 | B(サブ実読・親未確認) | 介入代数 5 種・**point-of-commitment 則**(下流再抽選の交絡)・**共通乱数は未対応=ローカル艦隊なら持てる側** |
| [nlp__abootorabi2026_steering-geometry](nlp__abootorabi2026_steering-geometry.md) | 自然言語処理 #27 / 人格心理学 #13 | B(サブ実読・親未確認) | **指示チューニングで ρ_T が 0.51→0.33**(1 モデルのみ)・採らない道の確認・価値ベースの個体差は弱い |
| [memory__lu2026_procedural-graphs](memory__lu2026_procedural-graphs.md) | 認知科学(記憶・習慣)#12 / 自然言語処理 #27 | B(サブ実読・親未確認) | **属性を辺に置く**(条件・助言・落とし穴)・受理は**非減少**・却下記録・**助言呼で呼数が倍** |
| [mas__yang2024_oasis](mas__yang2024_oasis.md) | 計算社会科学 #25 / 計算機科学(並列)#28 | B(サブ実読・親未確認・v1 メモと突合) | **Table 2 が唯一の出所**・v1 の ★2 数値は一致・**超線形 N^1.55**(体あたり 0.144→0.540→1.750 GPU·s) |
```

> 「一次確認」欄は **B(サブ実読・親未確認)** で書いてある。親が原典を開いて数値を確認したら **実読(第N)** に書き換えること(README の 3 段階の定義に従う)。

---

## 5. 親が最初に一次確認すべき 3 件(決定に最も効く順)

1. **B-12 OASIS の Table 2 と超線形の再計算**(`arxiv.org/html/2411.11581v4` §4.1)。D-70 の比較表と「40 万体 → それ以上」の見積もりが直接動く。確かめること = (i) Table 2 の 6 つの値、(ii) 総費用比 37.5 / 32.4 の割り算、(iii) 散文「within two days」と表の 3.0 h/step の食い違い。
2. **B-8 TRAILS Table 1 と「事前登録が無い」**(`arxiv.org/html/2605.18890v1` §5・§6)。C8 ablation の被覆表と、この repo の事前登録の外部根拠がここで決まる。「無い」ことの確認は**語の不在の確認**なので、親が自分で見ないと台帳に書けない。
3. **B-5 Table 3 の 10 行**(`arxiv.org/html/2607.02716v1`)。有志の「3〜5 倍」が裏づけられた唯一の件で、**倍率はサブの割り算**。10 個の割り算の再計算が要る。

(次点: **B-6 の Table 2 の件数**——35 本・15 本・22 本は holdout の作法の外部根拠として答申に引くので、親の実読が要る。)
