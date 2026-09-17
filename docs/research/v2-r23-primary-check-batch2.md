# R-23 第2批: 「背骨」を成す 4 答申の一次確認

<!-- hdr:v1 -->
- **分野**: 計算社会科学 #25 / SFCマクロ経済学 #10 / 会話分析・語用論 #15 / 人間移動科学 #3 / 法学(業法・条例) #11 | **重要度**: **P0**
- **一次確認**: **B** = サブが一次資料を実読(逐語つき)・**親未確認**。本書の逐語・URL・判定はすべて親の再確認を要する **→ 親確認 3 件(第208)**: Project Sid(arXiv 2411.00114 HTML)§5.2「we establish an existing set of laws and focus on how agents interact with this legal system」・§8.3 の 3 条件に法体系を外した条件は無い・「the results below are analyzed using a single 500-agent simulation」/ Decoupling(2405.08746)=デンマークの住居移転 39,297,646 件(1986–2020)・Foursquare 239,788 件は補助 / `conversation.py` の `ACCEPT_PROBABILITY = 0.8` は「契約書『較正目標≈0.8』・expedient」とだけ注記=一次出典なし(親確認)。他の主張は親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> 対象: [economy-sfc](v2-economy-sfc-deep-research.md)・[conversation](v2-conversation-deep-research.md)・[llm-mobility](v2-llm-mobility-research.md)・[mobility-field](v2-mobility-field-research.md)・[institutions](v2-institutions-deep-research.md)(いずれも 2026-08-31〜09-01・出典 URL ゼロ・**D 等級**)。
> 第1批([batch1](v2-r23-primary-check-batch1.md))§5-2 の **案 (b) 特徴値 grep** を実行した。答申本体・台帳・設計書は**一行も編集していない**。作業日 2026-09-17。

---

## §1 特徴値 grep — 名前なしで中身だけ設計・実装に入っている箇所

ファイル名 grep では 5 本とも **0 件**(第1批 §1)。以下は**特徴的な数値・固有名詞・式**を `docs/design/*.md` + `PENDING.md` + `IMPLEMENTED.md` + `STATUS.md` + `src/**` に当てた結果。

### 1-1 economy-sfc(U-B)

| 特徴値 | 設計・実装での出現箇所 | どの決定を駆動しているか |
|---|---|---|
| 四重記入・行和0/列和0 | `docs/design/v2-boundary-economy-design.md:56`・`v2-redesign.md:439`(**U11 DECIDED**)・`src/shibuya/economy/checks.py:164`・`ledger.py:9,635` | **U11 経済SFC(DECIDED 09-07)**の検算①。**実装済み** |
| `transfer(payer,payee,amount,account_code)` 単一API・残高直接代入の静的禁止 | `v2-boundary-economy-design.md:55`・`v2-world-process-design.md:93`(**D-R2-3 DECIDED**)・`src/shibuya/economy/ledger.py:402`・`engine/ledger_api.py:109` | **D-R2-3 行4「取引レベル保存=ハード制約(等級A・mechanism)」**。**実装済み** |
| 5部門+RoW・保存則テスト5層 | `v2-architecture-roadmap.md:43` の 1 行のみ | 背骨の要約行。**設計は 6 部門・検算 2 本へ変更済み**(`v2-redesign.md:439`)=答申の「5層」は設計に落ちていない |
| **冗長方程式を実装せず毎期 assert(答申 T3)** | **どこにも無い**(`checks.py` は検算①②の 2 本のみ) | 答申 5 層のうち **T3 が落ちている**。落とした記録も無い |
| RoW=残高部門・「湧き金を断つ」(R2) | `v2-audit-contradictions.md:23,73`・`v2-boundary-economy-design.md:46` | v1 根2(経済の循環定義)の是正。**実装済み** |
| revenue は計算値禁止(R1) | `v2-architecture-roadmap.md:43` | 同上(型設計の宣言) |
| 「EconAgent 型の低次元出力」 | `v2-inventory-and-bottlenecks.md:12` | 棚卸しの分野列挙。名前は EconAgent のみで答申名は無い |
| 値付け=LLM スカラー+外部執行・共謀を診断行で観察 | `v2-world-process-design.md:94`(**D-R2-3 行5 A案**)・`:158` | **行5 価格形成**。ただし設計書は根拠を `v2-price-formation-llm-research.md`(親確認済み)に付け替えており、U-B 面2 の名は出ない |
| 面3 の較正アンカー 15 本(飲食店 3,970 ほか) | **設計書に無い**。`docs/research/v2-boundary-economy-u10-u11-research.md:319` にのみ再出現 | 後発の **B 等級答申経由**で設計へ入った。U-B 面3 の「E1-E15」記号は `v2-pattern-ledger.md` の E 系列と**衝突**(E2 は別物) |

### 1-2 conversation(U-F)

| 特徴値 | 設計・実装での出現箇所 | どの決定を駆動しているか |
|---|---|---|
| **WHO=エンジン(会話分析規則)・相槌/最小応答=エンジン生成(LLM を呼ばない)** | `v2-action-contract.md:49`・`v2-world-process-design.md:96`(**R4 DECIDED 09-07**)・`src/shibuya/engine/conversation.py:9,109,595` | **R4 行7 会話**。**実装済み・文面凍結済み** |
| **終了を LLM に決めさせない**(max_turns・沈黙閾値・定型の締め) | `v2-action-contract.md:50`・`src/shibuya/engine/conversation.py:12,32` | 同上。`max_turns 3`(expedient)・`silence_ticks=5`・`max_session_ticks=60` |
| **声かけ応答率 ≈0.8** | `v2-implementation-plan.md:109`・`src/shibuya/engine/conversation.py:7,28,78-79`(`ACCEPT_PROBABILITY = 0.8`) | **実装済みの定数**。後発答申 `v2-action-conversation-contract-research.md:335` が「**※既存答申U-F**」と明記=**この D 等級答申が唯一の出所**(→ §2-2 #11) |
| 参加上限3(2者既定)・1人1会話・割り込み=次の移行点での優先権奪取 | `v2-action-contract.md:49`・`src/shibuya/engine/conversation.py:10,84,225` | R4。**実装済み** |
| 宛先/非宛先/傍受で記憶転写の重みを分ける(unaddressed recipient) | `v2-action-contract.md:54`(1.0 / 0.5 / 0.2) | R4 の記憶転写。答申の「heard_but_silent」の思想がそのまま入っている(語は無い) |
| reply_dropped 37,016 の再解釈(枠不足でなく需要超過・**破棄でなく繰り延べ**) | `v2-redesign.md:56,220`・`v2-perception-contract.md:140` | **繰り延べ規則(決定 09-06・A案)= 4クラス固定優先**。答申の核心がそのまま知覚契約の決定になっている |
| SSJ・TRP・summons-answer・preclosing・floor_holder・`self_selection_lost`/`no_capacity` の分離 | **どこにも無い** | 答申の会話セッション状態機械(OPENING/OPEN/CLOSING/CLOSED)と溢れの 2 分類は**設計に入っていない** |
| Qwen3 Swallow 8B=JMT 0.844・8B 飽和・合否チェックリスト8項 | **どこにも無い** | モデル選定は U-H/ベンチ側へ移っており、U-F 面2 は落ちている |

### 1-3 llm-mobility / mobility-field(人流 2 本)

| 特徴値 | 設計・実装での出現箇所 | どの決定を駆動しているか |
|---|---|---|
| **一次モーメントは創発・二次(OD/滞在時間/EPR)は全先行失敗。地理+到達可能性で改善見込みだが未実証** | `v2-inventory-and-bottlenecks.md:50`(**ボトルネック #7「v2 の中心的な科学的賭け」**) | v2 の**中心仮説そのもの**。答申名は無い |
| **Decoupling=地理由来成分**・EPR μ=0.6・常用地点〜25・切断べき則・radiation・Zipf | `v2-inventory-and-bottlenecks.md:27`(検証・較正の列挙) | 人流の検証指標セット。§2-3 #20 の判定に直結 |
| 重力モデル/OD較正/時間帯活動確率=**借りない** | `v2-inventory-and-bottlenecks.md:38`・`v2-boundary-economy-design.md:22`(**案B=重力抽選は下限対照のみ**・**U10 DECIDED 09-07**) | **U10 境界=来街の決定**。holdout 破壊の線引きが答申 §4 と一致 |
| 到達可能性による候補集合の制約(徒歩n分圏・営業時間・カテゴリ整合) | `v2-inventory-and-bottlenecks.md:50` の一語のみ。**規則としては未着地** | 答申が「機構的に正当」と結論した唯一の接地手段が、設計書に規則化されていない |
| SFM/ORCA/フロアフィールドCA・Weidmann 1.34 m/s・Fruin LOS・crowd turbulence 5-6人/m² | `v2-inventory-and-bottlenecks.md:12`・`v2-crowd-physics.md:25,30,31`・`v2-c9-geometry-agenda.md:17,43` | **R7 群衆物理(DECIDED 09-08)**。ただし設計書は根拠を `v2-crowd-physics-research.md`(親検収済み)に付け替えている |
| SUMO–JuPedSim 公式連成=上位層が需要と経路・下位層が身体 | `v2-crowd-physics.md:11` | CFSM 第1候補の根拠。同上(後発答申経由) |
| GATSim(70体・再計画トリガ) | `v2-boundary-economy-design.md:4`・`v2-perception-contract.md:122,128-130,136` | **不応期(決定 09-06)の唯一の先例**。後発答申経由で親確認済み |
| **Flyvbjerg 106% 過大・30年で改善なし** | **どこにも無い** | 「較正なしの需要は当たらない」への先回り論拠が設計書に落ちていない |
| 4段階推計が「なぜ動くのか」を持たない=分野の空欄 | `v2-inventory-and-bottlenecks.md:12` に「4段階推計の限界」の一語のみ | v2 の新規性主張の土台だが、設計書では 1 語 |

### 1-4 institutions(U-J)

| 特徴値 | 設計・実装での出現箇所 | どの決定を駆動しているか |
|---|---|---|
| **5プリミティブ(台帳・時計・集約・資格判定・配信)・足場なし ablation A0-A4・制度出現の相図** | `v2-architecture-roadmap.md:44` の **1 行のみ** | ロードマップの「新規性」宣言。**設計書が 1 本も無い**(制度の設計書は未起草) |
| 「制度は役割知識だけでは自己実行しない(**Sid の実証**)」 | `v2-redesign.md:198-199`(**D4 三層世界方式 DECIDED の修正3**)・`v2_significance.md:41` | **D4**。答申自身が 09-01 に「やや強すぎる/実証結果でない」と**自己訂正**しているが、設計書 2 本は未訂正(→ §4-A) |
| Project Sid の体数 | `v2-redesign.md:189`=**500体** / `v2_significance.md:41`=**1000体** | 設計書 2 本が食い違う(原典は解析 500 体・→ §2-5 #28) |
| 立法・規則制定=LLM が条文生成・エンジンが可決手続 | `v2-world-process-design.md:102`(**D-R2-3 行13**) | 答申の「制度の最小足場と接続」がそのまま行13 になっている |
| 同一モデル族の政権交代不能・制度を独立変数に・Governance Decay・Ostrom/Baggio の配置問題・Xie 10%/Centola 25% | **どこにも無い**(`v2-pattern-ledger.md:55` の C3 が Centola 実験を別文脈で引くのみ) | 面1 の実装警告3点・面2 の相図 4 軸は設計に未着地 |

**§1 の要点**: 5 本のうち **設計と実装に最も深く入っているのは economy-sfc と conversation**(検算・transfer API・WHO/相槌/終了・応答率 0.8 はすべて出荷コードにある)。**institutions は 1 行だけ**、**人流 2 本は「借りない」の線引きとボトルネック #7 に入っているが規則化されていない**。そして 4 本とも、**後発の B 等級答申が根拠として差し替わっている箇所**(価格形成・群衆物理・行動契約・境界経済)と、**D 等級のまま残っている箇所**(応答率 0.8・Sid の実証・ボトルネック #7・Decoupling)に分かれる。**後者が親の一次確認の対象**である。

---

## §2 主張ごとの確認表

判定の語(第1批と同じ): **一致** / **数値不一致** / **出典が見つからない** / **主張が原典より強い**。原典の逐語は 125 字以内。

### 2-1 economy-sfc — 分業の根拠

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 1 | 「**Poor Man's(2608.11215)の決定打**: EconAgent の Okun 則再現は会計恒等式(**Bernoulli(0.5) 就労の行動フリー方針が相関 −0.998** を出す)」 | https://arxiv.org/abs/2608.11215 | §5.1「a behaviour-free Bernoulli(0.5) work policy already yields an Okun correlation of −0.998」/「Reproducing Okun therefore validates nothing.」(GDP は雇用のアフィン像・R²=0.996) | **一致** | 影響なし。A/B 観測量の「Okun 則系は却下」を支持 |
| 2 | 「**Phillips 曲線は本物の行動的痕跡**」 | 同上 | §5.1「a negative unemployment–inflation relation is a genuine behavioural signature」。複製系の Phillips は out-of-sample で −0.569±0.138 | **一致** | 影響なし。「Phillips/Beveridge/マークアップ/倒産率を採用」を支持 |
| 3 | 「方法論=**行動フリー方針が再現する観測量は事前却下**(a-priori スクリーニング)・マクロ観測量はフィットせず常に out-of-sample」 | 同上 | §4 Algorithm 1 step 4「Screen M: if a behaviour-free policy already reproduces it, reject M」/「the macroscopic observable is therefore never fitted and is always an out-of-sample test」 | **一致** | 影響なし。**v1 cap300 を行動フリー並走**に使う推奨は原典の手続きと同型 |
| 4 | 面2 要約「①**マクロ再現の大半は会計恒等式で検証力ゼロ**と機械的に示された」 | 同上 | 原典が恒等式と断じたのは **Okun のみ**。Phillips は明示的に behavioural と区別。論文の主題は「LLM エージェントを安価な代理モデルに置換して N を伸ばす」 | **主張が原典より強い** | **文言を直す必要**。「大半」は原典に無い。さらに本論文は**意思決定層まで代理に置換できる**と主張しており、背骨(意思決定だけ LLM)を**支持する論拠としては両刃**(→ §3-3) |
| 5 | 「**共謀は自発的に起きる**(Fish+ 2404.00806): 寡占 LLM は自律的に超競争価格へ・プロンプトの無害な語句差が共謀度を左右」 | https://arxiv.org/abs/2404.00806 | 抄録「LLM-based pricing agents quickly and autonomously reach supracompetitive prices and profits」/「seemingly innocuous phrases in LLM instructions ("prompts") substantially influence the degree of supracompetitive pricing」(v6・EC 2026 採択) | **一致** | 影響なし。**D-R2-3 行5 A案**(LLM=相対倍率スカラー+逸脱比例コスト)の根拠を支持 |
| 6 | 「**Institutional AI(2601.11369)**: 反共謀憲法をプロンプトに入れるのは**無効**(むしろ悪化例)・効くのは外部の公開ガバナンスで**重篤共謀 50%→5.6%(d=1.28)**」 | https://arxiv.org/abs/2601.11369 | 抄録「mean tier falls from 3.1 to 1.8 (Cohen's d=1.28)」・severe collusion 50%→5.6%・N=90 runs/condition・6 model configs/「declarative prohibitions do not bind under optimisation pressure」 | **一致**(「むしろ悪化例」のみ本文未確認=抄録は "no dependable gain") | 影響なし。運用則②「共謀対策はプロンプトでなく**外部執行**」を支持 |
| 7 | 「**Agent Bazaar(2605.17698)**: 倒産率はモデル依存が極端(**Gemini 0.87 / GPT 0.67 / Claude 0.00**)・生き残った独占者は価格/費用 **3.4 倍**へ」 | https://arxiv.org/html/2605.17698v1 | §5.1「Gemini 3 Flash: b_r = 0.87」「GPT 5.4: b_r = 0.67」「Claude Sonnet 4.6: b_r = 0.00 (σ=0.04)」/ p̄/c = **3.42**(Gemini)・3.69(GPT)・1.94(Sonnet) | **一致**(条件つき) | 影響なし。運用則③「LLM 値付け区画はモデル固定」を支持。**3.4 倍は Gemini 固有**で、Sonnet は 1.94=近似原価。「独占者は 3.4 倍へ」は一般化しすぎ |
| 8 | 面1「**冗長方程式**: 会計恒等式から導かれる 1 本は実装せず『検算値』に回すのが SFC 標準の検証法」+「**四重記入**」 | https://www.levyinstitute.org/pubs/wp_745.pdf (Caverzasi & Godin, Levy WP 745, 2013) | 付録「Equation (10) is the hidden equation.」(モデル式から外して提示)/本文「the standard double-entry system of accounting, in its social version, is doubled in a **quadruple-entry system**」 | **一致**(用語は redundant / hidden の 2 系統) | **設計への未着地**。答申 T3(冗長式を毎期 assert)は `src/shibuya/economy/checks.py` に**無い**(検算①②のみ)。落とした記録も無い(→ §4-E) |

### 2-2 conversation — 分業の根拠

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 9 | 「**LLM は多者制御が苦手という直接証拠**: GPT-4o の三者対話で**次話者予測 46.0% < チャンス 50%**・宛先認識もチャンス同等(2501.16643)」 | https://arxiv.org/html/2501.16643v2 | §6「with a chance-level accuracy of 50%」「GPT-4o attained an accuracy of **46.0%** on this task, performing below chance level」/ 宛先認識「an accuracy of **80.9%**, which is only marginally above the chance level (**80.6%**)」 | **一致** | 影響なし。**R4「話者選択はエンジン」**を支持。補足: 母数は三者・日本語マルチモーダルコーパスの一部(宛先ありは全ターンの約 20%) |
| 10 | 「**『Who Speaks Next?』(2412.04937)=SSJ 規則の移植(隣接対の次話者選択+内部状態の自己選択)が対話破綻を有意に減らす**」 | https://arxiv.org/abs/2412.04937 | 抄録「adjacency pairs and turn-taking found in conversation analysis」・隣接対による次話者選択+内部状態に基づく自己選択の 2 機構/「significantly reduced dialogue breakdowns」 | **一致**(帰属注意) | 影響なし。ただし**抄録に Sacks/Schegloff/Jefferson の名は無く**、舞台はマーダーミステリー TRPG の少人数。「SSJ 規則の移植」は答申側の言い換え |
| 11 | 「開始/終了: …**声かけ応答率の実測アンカー約 0.8**」 | **見つからない** | CA 側の最近傍は **Stivers & Robinson 2006(質問への応答のうち 85% が answer)**・**Stivers et al. 2009(10 言語・情報要求の約 90% が応答)**。Schegloff 1968 の summons-answer は**規範の記述であって比率の測定ではない**(「conditional relevance」) | **出典が見つからない** | **最重要**。この 0.8 は `src/shibuya/engine/conversation.py:79 ACCEPT_PROBABILITY = 0.8` として**出荷コードに入っている**。コードは「較正データ無しの定数・expedient」と正直に書いているが、`v2-action-contract.md` §開始ゲートは「**較正目標**=声かけ応答率 約0.8」と書き、後発答申は出所を「※既存答申U-F」と指す=**循環参照** |
| 12 | 「**Concordia が『終了判断を LLM に任せる』を止めた一次記録**(CHANGELOG=モデルは終了したがる)」 | https://github.com/google-deepmind/concordia/blob/main/CHANGELOG.md | [2.2.0] 2026-01-12「prevent YOLO termination during formative memories init GM and optionally prevent the same thing in the dialogic GM」「(**default behavior remains unchanged**)」「we noticed some language models are more prone to deciding they want to terminate in YOLO mode than others」 | **主張が原典より強い** | **文言を直す必要**。CHANGELOG は「**既定は変えず、止められるようにした**」であって「止めた/撤回した」ではない。`v2-action-contract.md:50` の「**Concordia が撤回した設計**」は原典より強い。なお [1.6.0] 2024-06-11 は逆向きの記録(「conversations to run on much too long」)で、**両方向の記録が併存**する |
| 13 | 「**コスト設計の決定的証拠(2606.12369)**: 1,000体×10,000決定で LLM 行動選択はマルコフ連鎖の**数百倍遅く**方策も保存しない=『**決定は規則・発話だけ LLM**』の分業を正面から支持」 | https://arxiv.org/abs/2606.12369 (Should LLM Agents Decide in Social Simulations?) | 抄録: 有限状態機械を一次マルコフで実装した参照方策に対し、LLM 行動選択は「do not preserve it reliably」/「several hundred times slower than direct Markov chain sampling」/「is not a direct replacement for explicit decision policies」。1,000 エージェント・10,000 決定 | **一致** | 影響なし。**4 答申中、背骨を最も直接に支持する一次資料**。ただし舞台は**オンライン SNS シミュレーション**で、渋谷の身体・経済ではない |
| 14 | 「**Qwen3 Swallow 8B=JMT 0.844**(この規模で非常に高い会話能力)vs **32B=0.894**」 | https://swallow-llm.github.io/qwen3-swallow.en.html | 公式ページ: 8B の日本語 MT-Bench 平均 **0.844**(「very strong dialogue capabilities for a model of this scale」)/ 30B-A3B **0.889**・32B **0.894**(「approaching the upper limit of dialogue capability measurable by this benchmark」) | **一致** | 影響なし(モデル選定は U-H/ベンチ側へ移っており設計書に未着地) |

### 2-3 llm-mobility — 分業の根拠

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 15 | 「**CoPB**: 意図だけ LLM・行き先は重力モデルの分業=意図誤り **57.8%→19.4%**・トークン **97.7%** 削減」 | https://arxiv.org/abs/2402.09836 | 抄録「reduces the error rate of mobility intention generation from **57.8%** to **19.4%**」/ 機構モデル(gravity model)との併用で「reduce the token cost by **97.7%** and achieve better performance simultaneously」 | **一致** | 影響なし。**人流側で背骨を最も直接に支持する一次資料**。ただし v2 は §4 で「重力モデルは**借りない**」としており、**CoPB の分業そのものは採れない**(重力=holdout 破壊)=支持と不採用が同居 |
| 16 | 「**When Plausible Is Not Realistic(2606.13835)**: **OD 行列は実質ゼロ相関(CPC 0.04-0.14)**・滞在時間 W₁ 4.8-36h(実サンプル間 0.26h)・移動距離 W₁ 8.73km(実サンプル間 0.48km)」 | https://arxiv.org/html/2606.13835v1 | §5.1 Table 2: CPC は **H7 0.054〜0.270 / H8 0.042〜0.138 / H9 0.010〜0.038**。**実データ参照標本は H7 0.297・H8 0.092・H9 0.045**。§5.2 Table 3 滞在時間 W₁ = 3.96 / 30.24 / 4.79 / 36.39 h(参照 **0.26**)。§5.1 Table 1 Δr W₁ = 8.73 km(参照 **0.48**) | **数値不一致**(範囲の取り方)+**主張が原典より強い** | **値を直す必要**。①CPC の範囲は 0.010〜0.270 で「0.04-0.14」は一部。②**実データ同士の CPC も H8 で 0.092**しかなく、CitySim の 0.138 は**フロアを上回る**。「OD 行列は実質ゼロ相関」は**フロアを見れば成立しない**。滞在時間・距離の桁違いは原典どおり |
| 17 | 「原因診断: ①**無制約 POI 選択が主犯** ②地図品質(**OSM POI の 57% がベンチ・ゴミ箱等**・**Overture 補強で施設相関 0.55→0.80**)」 | 同上 | §6.1「**57.45%** of the 223,149 OpenStreetMap (OSM) POIs correspond to benches, bicycle parking, waste baskets」/「The Pearson correlation increased from **0.55 ± 0.23** using OSM data alone to **0.80 ± 0.20** using OSM+Overture.」(Overture 178,884 件を重複除去して追加) | **一致** | 影響なし。**W 系(POI 構築)の Overture 補強**と §4「到達可能性による候補集合の制約」を支持 |
| 18 | 「(When Plausible は)**実データ同士の別サンプル間ばらつきをフロアとして併記した初の系統評価**」 | 同上 | §4.3 は参照標本を「serves as a real-data benchmark for interpreting simulator discrepancies」と説明するだけ。新規性主張は §1「this is the **first systematic evaluation** of LLM-based urban simulators against established empirical mobility laws」 | **主張が原典より強い** | 影響なし(フロア併記を v2 が採る方針自体は妥当)。「**フロア併記が初**」という限定は原典に無い |
| 19 | 「**COMPASS(2602.16726)**: 統計則の自発再現を正面から測った**唯一の研究**。答えは **No** —— LLMob の距離指数 **β≈1.22** vs 実測 **β≈1.75±0.15**・**EPR が突出して最悪(JSD 0.39 / 0.25)**」 | https://arxiv.org/html/2602.16726v2 | §2.1「the estimated scaling exponent is smaller (**β≈1.22**)」・実データ「(with **β≈1.75±0.15** and κ≈400km)」/ Table 1 LLMob: Exploration **0.3895±0.0290**・Return **0.2531±0.0383**。抄録「how trip distances, visited locations, and flows distribute across a population - **fail to emerge**」 | **一致**(数値)+**主張が原典より強い**(位置づけ) | 影響なし。ただし ①原典は**手法論文**(題=Mobility Scaling-Law Guidance。統計則を**プロンプトに戻す**方法)で、β の測定は §2.1 の動機節。②「**唯一の研究**」は #18(同年 6 月の When Plausible が "first systematic evaluation" を主張)と**両立しない**。③Return は **CitySim 0.3452 の方が悪い**ので「EPR が突出して最悪」は探索側のみ |
| 20 | 「**Decoupling(Nat Hum Behav 2025・2405.08746)=v2 に決定的**: 地理の効果を差し引くと**5 桁のべき則**が現れる=**観測される距離分布の相当部分は『行動』でなく『地理』に由来** → **実地図・実 POI・実ダイヤを極限まで忠実にすること自体が、需要モデルを注入せずに統計則の一部を供給=v2 最大の武器**」 | https://arxiv.org/html/2405.08746v2 ・ https://doi.org/10.1038/s41562-025-02282-7 (Nat Hum Behav **9, 2564–2575 (2025)**) | 抄録「reveals a **power law spanning five orders of magnitude**」。主データは **デンマークの住居移転 39,297,646 件・1986–2020**(3,251,464 住所・精度 ±2 m)。補助に仏 INSEE 約 40M の都市間移転、日次移動は **Foursquare チェックイン約 24 万件**(Houston/Singapore/SF)。論文の主張は「地理と行動が**絡み合っている**ので pair distribution function で**切り分ける**」 | **一致**(数値・掲載誌)+**主張が原典より強い**(v2 への含意) | **文言を直す必要**。①「5 桁」「Nat Hum Behav 2025」は正しい。②原典は「距離分布の相当部分は地理由来」とは**言っておらず**、切り分けの手法論文である。③主データは**住居移転(引越し)**であって日次都市内移動ではない。**2 km 四方の渋谷の日次人流へ「最大の武器」と外挿するのは原典の主張ではない** |
| 21 | 「**GenWorld**(東広島 196,608 体): センサス属性は完璧(**就業者数 R²>0.99**・生活時間相関 **r>0.86**)でも**通勤距離は KS 距離 0.359** で合わない(**短距離過少・5-15km 過剰**)」 | https://arxiv.org/html/2606.27650v1 | §5.3.1「Employment counts (15+) show high tract-level agreement (**R²>0.99**)」/§8「average correlation **r>0.86**, RMSE <3%」/§5.4「The resulting **KS distance is 0.359** (0.399 when restricted to commutes ≤20 km)」「underrepresents very short commutes and **overrepresents 5–15 km** trips」。196,608 体・東広島・YJMob100K 照合 | **一致** | 影響なし。「属性接地だけでは距離分布は出ない」を支持。補足: 原典自身が「a commuting-distance **diagnostic** and not as evidence of calibrated OD-flow prediction」と限定 |

### 2-4 mobility-field — 分業の根拠

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 22 | 「**McNally 標準解説が明言**: 土地利用・活動系は**外生入力**・均衡化されるのは**経路選択のみ**=『なぜ動くのか』を持たない構造の正体」 | https://escholarship.org/uc/item/0r75311t (McNally, *The Four Step Model*, UCI-ITS-AS-WP-07-2) | 「the transportation system and activity system … serve as **exogenous inputs**」/「a process than amounts to formal **equilibration of route choice only**, not of other choice dimensions such as destination, mode, time-of-day, or whether to travel at all」 | **一致** | 影響なし。**「借りない」の線引き**(`v2-inventory-and-bottlenecks.md:38`)と v2 の新規性主張の土台を支持 |
| 23 | 「**Flyvbjerg+(Transport Reviews 2006)=鉄道旅客予測は 10 件中 9 件が過大・平均 106% 過大**・道路も 50% が ±20% 超・**30 年間で精度は改善していない**」 | https://doi.org/10.1080/01441640500124779 (Flyvbjerg, Skamris Holm & Buhl, *Transport Reviews* 26(1):1–24) | 抄録「for nine out of ten rail projects passenger forecasts are overestimated; average overestimation is **106%**」/「for 50% of road projects the difference … is more than ±20%」/「forecasts have **not become more accurate** over the 30-year period studied」。標本 210 事業・14 か国・US$58bn | **一致** | 影響なし。ただし**設計書に一度も現れない**(§1-3)。「較正なしの需要は当たらない」への先回り論拠が台帳化されていない |
| 24 | 「**SUMO–JuPedSim 連成が公式機能**=『上位層が需要と経路・下位層が身体』の層分離は分野の既定路線 → v2 の構成(需要=LLM/身体=エンジン)はこの点で正統」 | — | **本批では未再確認**。`v2-crowd-physics.md:11`(「CFSM は SUMO–JuPedSim 公式連成で唯一 extensively tested」)は後発の `v2-crowd-physics-research.md`(**親検収済み**)を根拠としており、そちらで裏が取れている | **本批の空欄**(既確認扱い) | 影響なし。**分業の「分野的正統性」の唯一の外部支持**なので、親は crowd-physics 側の検収記録で足りるか確認すること |

### 2-5 institutions — 分業の根拠

| # | 主張の逐語(答申) | 一次資料 URL | 原典の逐語と節 | 判定 | 決定への影響 |
|---|---|---|---|---|---|
| 25 | ★前提の訂正「v2 三層の修正3『制度は役割知識だけでは自己実行しない(Project Sid の実証)』は**やや強すぎる**。Sid は**足場なし条件と足場あり条件の統制比較をしておらず**、法体系の事前供給は**設計上の前提**。『自己実行しなかった』は実証結果でなく**著者の能力限界の言明**」 | https://arxiv.org/html/2411.00114v1 | §5.2「**we establish an existing set of laws** and focus on how agents interact with this legal system」/ §8.3 の 3 条件は「修正可能な憲法」「**凍結した憲法の対照条件**」「モジュール ablation」で、**法体系そのものを外した条件は無い**/§7 Limitations「they cannot simulate **de novo emergence** of societal innovations and infrastructures」「such as the emergence of democratic systems, fiat economies, or communication systems」 | **一致(答申の自己訂正が正しい)** | **最重要**。`v2-redesign.md:198-199`(**D4 DECIDED の修正3**)と `v2_significance.md:41` は「**Sid の実証**」「著者自身が明記」のまま=**訂正が設計書へ伝播していない**(第1批 §3-B と同型)。→ §4-A |
| 26 | 「Sid の制度実証: **29 体編成**・**憲法が税率 20% を規定**・120 秒間隔の課税窓・S3 に集約し election manager が処理・**反税 influencer で 20%→9%**」 | 同上 | §8.3「The complete system comprises of **29 agents**」(25 constituents + 3 influencers + 1 remote election manager)・「a fixed **20%** taxation rate」/ §5.2「when the tax rate decreased from 20% to 5-10%, agents reduced taxes paid **from 20% to 9%**」 | **一致** | 影響なし |
| 27 | 「宗教は**司祭 20 体をスポーン**が足場」 | 同上 | Methods「We distinguish **20 agents** in the town of Meadowbrook who are spawned as Pastafarians」 | **一致** | 影響なし |
| 28 | (設計書側)「**Project Sid(500体 Minecraft)**」(`v2-redesign.md:189`)vs「**Project Sid(1000体)**」(`v2_significance.md:41`) | 同上 | 「We conducted multi-society simulations with **500 agents** and analyzed complex, large-scale social dynamics.」「We have also simulated societies with **over 1000 agents**, but these runs **exceeded the computational constraints**」「the results below are analyzed using a single **500-agent** simulation」。抄録の枠は「10 – 1000+」 | **数値不一致**(`v2_significance.md` 側) | **値を直す必要**。解析に用いられたのは **500 体**。1000+ は**応答不能で解析されていない**。設計書 2 本の不整合 |
| 29 | 「**Artificial Institutions(2608.04020)**=同一エージェントで市場制度 5 種を比較し **call market 88.6% vs 二者交渉 56.4%**=最小の制度変更が質的に異なる帰結」 | https://arxiv.org/abs/2608.04020 | 抄録+結果: call market **88.6%** / continuous double auction 71.5% / posted-offer・posted-bid 約 66% / bilateral bargaining **56.4%**(実現余剰比)。「even minimal institutional changes can generate qualitatively different artificial social outcomes」 | **一致** | 影響なし。**「制度を独立変数にする」**という U-J の中核設計を支持(ただし設計書未着地) |
| 30 | 「**Hierarchical Games(2608.09574)**=**同一モデル族だと初代当選者が無期限留任**・モデル族を混ぜた群でのみ政権交代」 | https://arxiv.org/abs/2608.09574 | 抄録「When all agents share the same model family, **the first elected manager stays in power indefinitely**.」政権交代は異なるモデル族を混ぜた群でのみ観測。6 モデル×12 実験 | **一致** | 影響なし。**実装警告①(単一モデル駆動なら選挙を置いても交代が観測されない)**を支持。設計書に未着地=**選挙を実装するなら効く** |
| 31 | 「**Governance Decay(2606.22528)**=コンテキスト圧縮が統治制約を静かに消去し長時間ランで**違反率 0%→30-59%**」 | https://arxiv.org/abs/2606.22528 | 抄録: 全文脈保持時の違反率 **0%**、圧縮後 **30%**、「reaching **59%** for some models」。1,323 エピソード・7 モデル族。制約が要約に残れば 0%・落ちれば 38% | **一致** | 影響なし。**A4(配信なし=Governance Decay 型)が最安・最再現**という ablation 設計の根拠を支持 |
| 32 | 「**Ashery+(Science Advances)**=明示プログラムなしで社会的慣習が自発創発・処罰機構が規範創発を駆動」 | https://doi.org/10.1126/sciadv.adu9368 (Sci Adv 2025;11(20):eadu9368) | 抄録「we present experimental results that demonstrate the spontaneous emergence of universally adopted social conventions in decentralized populations of large language model (LLM) agents」。24〜200 体の naming game・コミット少数派によるティッピング | **一致**(反論の存在に注意) | 影響なし。ただし **Barrie & Törnberg(2505.23796)「Emergent LLM behaviors are observationally equivalent to data leakage」**が反論を出しており、`v2-inventory-and-bottlenecks.md:12` は同反論を別文脈で挙げている。**答申は反論に触れていない** |

### 判定の内訳

| 判定 | 件数 | 内訳 |
|---|---|---|
| 一致 | **22**(うち条件つき・注記推奨 5) | #1・2・3・5・6・7・8・9・10・13・14・15・17・21・22・23・25・26・27・29・30・31・32 |
| 数値不一致 | **2** | #16(CPC の範囲とフロア)・#28(Sid 1000 体) |
| 出典が見つからない | **1** | #11(声かけ応答率 0.8) |
| 主張が原典より強い | **6** | #4(Poor Man's「大半」)・#12(Concordia「撤回」)・#16(「実質ゼロ相関」)・#18(「フロア併記が初」)・#19(「唯一の研究」)・#20(Decoupling の v2 含意) |
| 本批の空欄(未再確認) | **1** | #24(SUMO–JuPedSim。後発答申で親検収済み) |
| 合計(#16 は重複計上) | 32 主張 | economy 8・conversation 6・llm-mobility 7・mobility-field 3・institutions 8 |

---

## §3 「背骨」の収束は本当に独立か

**結論: 「4 答申が独立収束した」は成立しない。成立するのは弱い形「4 つの異なる先行群が、同じ分業と両立する(確認的収束)」である。**

### 3-1 引用レベルでは重複していない(独立性を支持する側)

各答申が分業の根拠に置いた先行は**互いにほぼ重ならない**。

| 答申 | 分業の結論の逐語 | 根拠とされた先行(名前・年) |
|---|---|---|
| economy-sfc | 「**恒等式・清算・会計はエンジン、意思決定だけ LLM** が実測に裏打ちされた唯一の分割」 | Poor Man's(2026)・EconAgent(2023)・Fish+(2024)・Institutional AI(2026)・Agent Bazaar(2026) |
| conversation | 「**WHO=エンジン・WHEN=エンジン・WHAT=LLM**」「**決定は規則・発話だけ LLM**」 | Inoue+(2025・2501.16643)・Nonomura & Mori(2024・2412.04937)・Concordia CHANGELOG(2024-2026)・Buitrago López+(2026・2606.12369) |
| llm-mobility | 「**LLM には『機会集合からの選択』だけをさせる**」 | CoPB(2024)・TrajGenAgent(2026)・When Plausible(2026)・COMPASS(2026)・Decoupling(2025) |
| institutions | 「**エンジンが保証すべきは 5 プリミティブのみ**・動機/意見/遵守判断/説得はエージェントに放置」 | Project Sid(2024)・GovSim・Artificial Institutions(2026)・Governance Decay(2026) |

共通の先行は **1 本も無い**(EconAgent が economy と第1批の engine-llm-boundary で重複するのみ)。**引用の独立性はある。**

### 3-2 過程レベルでは独立でない(3 つの構造的な理由)

1. **分業は 4 答申より前に設計の前提だった。** `docs/design/v2-redesign.md` §4b(**2026-08-29 起案**)が既に「層1 エンジンは**破れない法則のみ**/層2 手続きは**役割の知識**として実行」と書き、同節の 08-29 リサーチ答申が「三層仮説は**先行研究の進化方向と収束**」と宣言している。人流 2 本は **08-31**、economy/conversation/institutions は **09-01**。**4 答申は前提の後に来た。**
2. **4 答申は同一の依頼文から出ている。** `docs/design/v2-deep-research-program.md`(09-01)の面の指定が、分業の語で問いを立てている——U-B 面2「価格形成/雇用/倒産を**どちらに任せたか**」・U-F「**誰が発話権を持つか**=turn-taking model」・U-J「選挙・行政・警察を**どこまで用意するか**」。**「どちらに任せたか」を問う依頼は、「二つに分けるべきか」の独立検定にならない。**
3. **4 答申は互いに盲検でない。** 統合答申が相互参照している(economy→U-F/U-H、conversation→U-G/U-H、institutions→U-F/U-G/U-H)。同一の親の下で既知の順序で走った 1 つのプログラムの出力であり、**独立の観測ではない**。

加えて、**「35 面が独立収束」(`v2-architecture-roadmap.md:39`)の 35 面も、同じ 1 本のプログラム(`v2-deep-research-program.md` の 15 ユニット)から出ている。** 面の数は独立性の証拠にならない。

### 3-3 反対向きの証拠が 1 本ある

economy 答申が「決定打」として引く **Poor Man's(2608.11215)** の主題は、「マクロな問い(相図・定型化事実・N スケーリング)に対しては **LLM エージェントそのものを安価な代理モデルに置換してよい**」である(§4 の behavioural cloning・EconAgent の再実装+他 7 本で検証)。これは「**意思決定だけは LLM でなければならない**」とは**両立しない方向**の主張で、むしろ「意思決定も規則で代替できる範囲が広い」と読める。#13(2606.12369)も同型で、結論は「LLM 行動選択は明示方策の直接の置換ではない」=**方策は規則で書くべき**であり、**「LLM に意思決定を任せる」根拠ではなく「任せない」根拠**である。

すなわち、**背骨のうち「状態と集約はエンジン」は 4 答申すべてが支持するが、「意思決定は LLM」を積極的に支持する一次資料は本批の範囲では見つからなかった。** CoPB(#15)だけが「意図は LLM が上手い」を示すが、その分業の相方は v2 が採らないと決めた**重力モデル**である。

### 3-4 判定

| 主張 | 判定 |
|---|---|
| 「4 答申が**独立**収束」 | **成立しない**(同一の著者・同一の依頼文・分業は先行する設計前提) |
| 「4 答申が**同一分業に到達**」 | **成立する**(4 本とも結論の文言は分業の形) |
| 「4 つの**異なる先行群**が同じ分業と両立する」 | **成立する**(引用に重複が無い) |
| 「**状態と集約はエンジン**」の先行支持 | **強い**(#1・#9・#13・#15・#19・#21・#25 が一致) |
| 「**意思決定は LLM**」の先行支持 | **弱い/両刃**(#4・#13 は逆向き・#15 の相方は不採用モデル) |

---

## §4 決定への影響の要約(再検討が要る DECIDED 行を名指し)

| 件 | 名指し | いま何が起きているか | 推奨(決定は親とユーザー) |
|---|---|---|---|
| **A** | **`docs/design/v2-redesign.md` §4b 修正3(L198-199)= D4「三層世界方式」DECIDED** + `v2_significance.md:41` | 「制度は役割知識だけでは自己実行しない(**Sid の実証**: 課税・投票・宗教は全て設計者の足場が必要だった)」。原典 §5.2 は「**we establish an existing set of laws**」=設計上の前提であり、§8.3 の 3 条件に**法体系を外した条件は無い**。§7 の「de novo は不可」は**能力限界の言明**。**U-J 答申は 09-01 に自己訂正済みだが、設計書 2 本に伝播していない**(第1批 §3-B と完全に同型) | 「Sid の実証」を「**Sid は足場なし条件を走らせていない(設計上の前提として法を供給)**」に置換する。**v2 の新規性はむしろ強まる**(足場なし ablation A0-A4 が先行ゼロであることの根拠が確定する)。D4 の結論(最小足場を用意する)は動かない |
| **B** | **`docs/design/v2-architecture-roadmap.md:39`** と **`CLAUDE.md` §3 第1行** | 「**背骨(35 面が独立収束)**…4 答申が**独立**収束」。§3 のとおり、分業は 4 答申より前(08-29)に設計前提として存在し、依頼文が分業の語で問いを立て、4 答申は相互参照している。**35 面も同一プログラム**の出力 | 「独立収束」を「**4 つの異なる先行群と両立(引用に重複なし)**」へ弱める。主張の実質(背骨の妥当性)は落ちない。**CLAUDE.md の文言なのでユーザー決定事項** |
| **C** | **`src/shibuya/engine/conversation.py:79`(`ACCEPT_PROBABILITY = 0.8`)+ `docs/design/v2-action-contract.md` 開始ゲート「較正目標=声かけ応答率 約0.8」** | 「実測アンカー約 0.8」の一次が**見つからない**。CA の最近傍は質問への応答(Stivers & Robinson 2006 の 85%・Stivers et al. 2009 の約 90%)で、**summons-answer の比率を測った研究は見当たらない**(Schegloff 1968 は規範の記述)。後発の B 等級答申は出所を「※既存答申U-F」と指しており **D 等級答申へ戻る循環参照**。コード側は正直に「較正データ無しの定数・expedient」と書いている | ①契約書の「**較正目標**」の語を外し「**expedient(一次なし)**」に統一 ②較正アンカーが要るなら **Stivers 系(質問への応答 85-90%)を上界の参考**として台帳へ ③`ACCEPT_PROBABILITY` を感度試験の対象に登録(現在 ablation 腕なし) |
| **D** | **`docs/design/v2-action-contract.md:50`「Concordia が撤回した設計」** | CHANGELOG [2.2.0] は「**既定は変えず**、止められるようにした」。逆向きの記録([1.6.0]「conversations to run on much too long」)も併存 | 「撤回した」→「**既定は据え置きのまま、止める口を用意した(2.2.0)**」。**決定(終了は LLM に決めさせない)は動かない**(#9・#13 が独立に支える) |
| **E** | **`src/shibuya/economy/checks.py`(検算①②のみ)vs U-B 面1 の保存則テスト 5 層** | 答申の **T3(冗長方程式を実装せず毎期 assert)**が実装にも設計書にも無く、落とした記録も無い。T3 は SFC 標準の検証法(Levy WP 745 付録「Equation (10) is the hidden equation」) | 「6 部門・検算 2 本」で T3 を包含できているかを**紙上で 1 度確認**し、できていないなら **U11 の未決項として PENDING へ**(新規実装の可否はユーザー判断) |
| **F** | **`docs/design/v2-inventory-and-bottlenecks.md:27,50`(ボトルネック #7「v2 の中心的な科学的賭け」)** | 「**Decoupling=地理由来成分**」を土台に「地理+到達可能性で改善見込み」と書くが、原典は**デンマークの住居移転 3,930 万件(1986-2020)**の手法論文で、「距離分布の相当部分は地理由来」とは言っていない。日次移動は補助データ(Foursquare 約 24 万件)。**2 km 四方の渋谷への外挿は原典の主張ではない** | 「v2 最大の武器」の表現を落とし、「**地理を忠実にすることが統計則の一部を供給する**は v2 の**仮説**(先行の直接支持は無い)」と宣言に変える。ボトルネック #7 が既に「未実証」と書いているので**格下げでなく明文化**で足りる |
| **G** | **人流の検証指標(OD の CPC)** | 「OD 行列は実質ゼロ相関(CPC 0.04-0.14)」。原典のフロア(実データ同士)は **H8 で 0.092**、CitySim は 0.138 で**フロアを上回っている**。CPC の実測範囲は 0.010〜0.270 | **CPC を「ゼロ相関」の語で扱わない**。When Plausible 方式(実サンプル間ばらつきをフロアとして併記)を**CPC にも必ず適用**する。C8 忠実度計器盤の指標定義に直接効く |

**本批の結論**: economy・conversation は**分業の一次支持が実在し、数値も原典どおり**だった(#1-3・#5-7・#9-10・#13-14)。institutions は**答申自身の自己訂正が正しく、それが設計書に届いていない**(A)。人流 2 本は**個々の数値は正確だが、v2 への含意の言い換えが一段ずつ強い**(F・G・#18・#19)。そして **1 件、出典が見つからない数値が出荷コードに入っている**(C)。第1批が見つけた型——「中身の誤りより**写しの事故**の方が多い」——が、第2批でも再現した。

---

## §5 空欄(見つからなかった・読めなかった・時間で落とした)

### 一次に当たれなかった主張

| 答申 | 主張 | 状態 |
|---|---|---|
| economy-sfc | Caiani+(JEDC 2016)本文・EURACE・JAMEL の検算コード・sfctools `check_consistency` / sfcr `sfcr_validate` の実物 | **未確認**(sfcr の vignette URL は 404・Levy WP 745 のみ読了)。Caiani 2016 は `v2-boundary-economy-design.md` が親一次確認済みと記載=**本批では再確認していない** |
| economy-sfc | G&L 6章 model REG・OPENSIMPLEST・「地域 SFC の最小粒度は州レベル=**区レベルは前例なき粒度**」 | **未確認**(不在の主張なので反証探索が要る) |
| economy-sfc | SimCity(2510.01297)・Eco3S(2607.26588)・LiveTradeBench・銀行取り付け(2602.15066)・オークション(2507.09083)・Project Vend | **未確認** |
| economy-sfc | 面3 の 15 アンカー(飲食店 3,970・小売 1.59 兆・労働流入 332,314・開廃業 17.0/5.6% ほか) | **未確認**。設計へは後発の B 等級答申経由で入っている |
| conversation | 面2 のほぼ全部: ABEJA 白箱蒸留 6.86→7.26・**最小応答の過少(2608.24080)**・YapBench・Verbal Tics(r=-0.87)・**agreeableness↔sycophancy r=0.87**・日本語の役割×表現スタイル(2605.28037)・LCTG Bench・TRAILS(76pt) | **未確認**。**2 本が同じ 0.87 を報告している点は要確認**(取り違えの可能性) |
| conversation | AutoGen の auto 話者選択=「selector+validator で追加 LLM 2 呼/ターン」 | **未確認** |
| conversation | GA 型分散会話の品質劣化・SDR 型軽量スクリーニング・SI-RNN の役割別埋め込み更新・PersonaKit の割り込み 4 挙動 | **未確認** |
| llm-mobility | LLMob 時空間分布 **JSD 0.559** / Step Distance 0.049・CityReal 生活時間 **JSD 0.0016**・GATSim 70体13ノード・TrajGenAgent 距離 **JSD 0.0006** | **未確認**(COMPASS Table 1 経由で LLMob の EPR 値のみ確認) |
| llm-mobility | González+2008・Song+2010(μ=0.6±0.02・ζ=1.2±0.1)・Simini+2012・Alessandretti+2018(常用地点〜25)・Too Human to Model(2507.06310) | **未確認**。渋谷 2 km 四方での**代替指標**(滞留時間・訪問頻度 Zipf・EPR の μ・常用地点数)の妥当性判断に効く |
| mobility-field | Wilson 1967・McFadden・Wardrop・歩行者経路 4 原理(J R Soc Interface 2022)・**Weidmann 基本図 1.34 m/s 原典**・Fruin 1971・crowd turbulence(PRE 2007)・梨泰院(PLOS ONE 2024)・明石 15人/m²・RiMEA v3.0 の 15 ケース・ISO 20414・**SUMO–JuPedSim 公式連成** | **本批では未再確認**。多くは後発の `v2-crowd-physics-research.md`(親検収済み)で裏が取れている。**Weidmann 1993 原典は `v2-c9-geometry-agenda.md:51` が「取得不能」と記録済み** |
| mobility-field | ActivitySim/MATSim の普及率(カリフォルニア 18MPO で ABM 7 / 4段階 9)・Liu+(2412.06681)・Tesfatsion の経験的検証論 | **未確認** |
| institutions | GovSim(生存率 54% 未満)・Corruption(2603.18894)・Democracy-in-Silico・Elected Leadership(厚生 +55.4%)・SovSim(生存率最大 87.3% 劣化) | **未確認** |
| institutions | Zaklan モデル・**Axelrod 1986 と Galán&Izquierdo の再現失敗**・ホットスポットモデル・Ostrom IAD の ASL 化 | **未確認**。Galán&Izquierdo は v2 の再現性設計の警告として**2 度引かれている**ので優先度高 |
| institutions | Ostrom 8 原理の**配置問題(Baggio QCA)**・Xie+ **コミット層 10%**・Centola **25%**・Bouchaud「較正より先に相図」・Schelling 54 変種・Lee+ の変動係数基準・Secchi&Seri の検定力・Franco+ の出版バイアス 40pt・METR | **未確認**。**相図 4 軸の全定量アンカー**がここにある |

### 読めなかった / 上限に当たったもの

- **macrosimulation.org の SFC ページ・sfcr の vignette = いずれも 404**。SFC の「冗長/hidden 方程式」は Levy WP 745(Caverzasi & Godin 2013)の付録で代替した。
- **Levy WP 745 は WebFetch が PDF バイナリを返したため、保存分をシステム python の `fitz` で本文抽出**して読んだ(記憶ノート「PDF 読解の作法」の手順)。
- **ScienceDirect = HTTP 403**(McNally の別版に当たろうとして失敗)。McNally は eScholarship の UCI-ITS ワーキングペーパー(WP-07-2)で読んだ。
- **Agent Bazaar の per-model 倒産率は表でなく §5.1 の本文値**。表番号で引くと見つからない。
- **When Plausible の HTML は Appendix B.1 で打ち切られた**(付録 C-E 未読)。
- Institutional AI の「**プロンプト方式はむしろ悪化**」は**抄録では "no dependable gain" 止まり**。本文未確認。
- **Flyvbjerg 2006 の出版社版は有料**。逐語は抄録(Taylor & Francis)+ JAPA 2005 姉妹論文の一致で取った。**親は ORA(オックスフォード大リポジトリ)の公開版で再確認するのが望ましい**。
- arXiv は `abs` だけでは数値が取れず、`arxiv.org/html/...` に切り替えて取得した(2608.11215・2501.16643・2602.16726・2605.17698・2606.13835・2606.27650・2411.00114)。

---

## §6 第3批への引き継ぎ

### 6-1 対象(優先順)

1. **`v2-engine-llm-boundary-research`(D 等級・第1批で 5 主張だけ確認済み)の残り**——本批 §3 で「分業は 08-29 に設計前提だった」ことが判ったので、**その前提を作った 08-29 リサーチ答申がどれか**を特定し、一次を当てる。`v2-redesign.md:186-206` が引く **Concordia v2 / Orchestrated Reality / Project Sid / NCP-Bench(GM 長期矛盾 40-68%)/ SkillsBench** が対象。背骨の根拠の**最上流**はここにある。
2. **`v2-precedent-system-deep-research`**(第1批 §5-1-5 の積み残し)。§4-A の訂正文を書くとき必ず読む。
3. **`v2-coupled-adaptation-deep-research`**(記憶:習慣:判例=時定数 **1:5:25**)。統合設計図 §1 の出所で、D-68 経路3 に触る。
4. **`v2-observation-projection-deep-research`**(L-OBS/L-REC・推定器 R0-R6)。U4 採否の材料。
5. **`v2-benchmark-standards-research`**(5 層構造)。C8 忠実度計器盤が到達したら効く。**§4-G(CPC のフロア併記)と同じ場所に落ちる**ので一緒に読むのが効率的。
6. 本批の空欄のうち**決定を駆動しているもの**: ①institutions 面2 の相図 4 軸の定量アンカー(Xie 10% / Centola 25% / Baggio / Bouchaud / Lee / Secchi&Seri) ②conversation 面2 の sycophancy 2 本(**同じ r=0.87 の取り違え疑い**) ③Galán&Izquierdo の Axelrod 再現失敗。

### 6-2 第2批で見つかった「検査の型」の追加提案

第1批 §5-3 の 2 つ(**写し検査**・**訂正の伝播検査**)は本批でも同じ形で当たった(§4-A・§4-D)。加えて 2 つ:

- **循環参照検査**: 後発の B/A 等級答申が根拠として「※既存答申X」と書いている箇所を grep し、**X が D 等級なら一次は存在しない**と判定する。本批の §4-C(応答率 0.8)はこの形で見つかった。`docs/research/*.md` の「既存答申」「答申U-」「同答申」を機械的に洗えば 1 回で終わる。
- **フロア併記検査**: 「ほぼゼロ」「桁違い」「実質無相関」と書いた比較値について、**原典が実データ同士のばらつき(フロア)を報告しているか**を必ず見る。本批の §4-G はこの形(CitySim の CPC 0.138 は実データ同士の 0.092 を上回っていた)。

### 6-3 親が最初に一次確認すべき 3 件

1. **#25 Project Sid §5.2「we establish an existing set of laws」+ §8.3 の 3 条件**(https://arxiv.org/html/2411.00114v1)——**D4 DECIDED の修正3 の根拠そのもの**で、設計書 2 本が未訂正。
2. **#11 声かけ応答率 0.8 の不在**——出荷コード `src/shibuya/engine/conversation.py:79` に入っている定数で、**一次が見つからない**。親は「Schegloff 1968 に比率は無い」「Stivers 系は質問への応答で 85-90%」を自分で確かめること。
3. **#20 Decoupling のデータ種別**(https://arxiv.org/html/2405.08746v2)——「**デンマークの住居移転 3,930 万件・1986-2020**」であって日次都市内移動ではないこと。**「v2 最大の武器」の土台**なので、親が原典の Data 節を直接読むべき。
