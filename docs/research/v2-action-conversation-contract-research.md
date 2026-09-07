# レーンR4 答申: 行動契約(心→世界)と会話プロトコル

> **親検収(Fable・2026-09-06)**: 出典を親が一次確認した。✔=親が実読して数値一致。
> - ✔ Levinson & Torreira 2015(Frontiers実読): 「The 50,510 IPUs had an average duration of 1680 ms, and a median duration of 1227 ms.」IPU=180 ms以上の無音で区切った発話単位(ターンと厳密には同一でない=答申の注記どおり)。「1呼=1実ターン」が予算上不成立という算術は妥当。
> - ✔ Dunbar 2020(PMC7482201実読): 層5/15/50/150/500/1500・「each layer is approximately three times the size of the layer immediately inside it」・「Approximately 40% of all social effort … to the five individuals in the closest layer, with another 20% devoted to the remaining 10 members of the second layer」・関係破綻約1%/年・転居後18か月で約40%入替・数か月の無接触で弱化。
> - ✔ Ray & Goyal 2026(arXiv 2607.14167・2026-07-15・**査読前**): TextWorld 50ゲーム・予算4呼・Qwen2.5-Coder-14B(TypedFields 36/50 vs 生診断14/50=+44pt, 95%CI 28-60)・Llama-3.1-8B(29/50 vs 8/50=+42pt)・代替行動の提示だけで+36/+40pt。**注**: TextWorld(3部屋4物体)は社会シムと課題構造が異なる=効果量の転用はexpedient。
> - ✔ Mastroianni et al. 2021 PNAS(Harvard Gazette経由・原典403): 「about 2 percent of conversations ended when both people wanted them to」「about 46 percent … both parties reported wanting the conversations to end before they did」=二次資料。
> - ✔ AI Town ARCHITECTURE.md(実読): 「Only the game engine should programmatically modify these tables, so components outside the engine can only mutate them by sending inputs.」入力=join/leave/moveTo/startConversation/acceptInvite/rejectInvite/leaveConversation/startTyping/finishSendingMessage。✔ Concordia(arXiv 2312.03664v2 §2実読): 「Whenever an agent tries to perform an action that violates the grounding, it communicates to them that their action was invalid.」
> - 空欄(会話持続時間の実測分布・約束遵守率・口コミ伝播率・内層入替率の一次データ・CivRealm/Sidの行動空間・OASIS失敗処理・「語彙10-15語で劣化」)は答申の申告どおり。max_turns=3呼/体は予算由来のexpedient。
> - 正典化: docs/research/v2-action-conversation-contract-research.md(R4の根拠)。


> 作成: 2026-09-06 / リサーチ担当サブ(Opus 5) / 検収=親(Fable)・決定=ユーザー
> 規律: 出典は正規ドメイン+実読した箇所の短い引用。読めなかった項目は「空欄(未確認)」。推測は【推測】。
> 対象: 知覚契約書v1(世界→心)の裏面=**LLM出力→世界状態変化の写像**、および会話の成立・終了。

---

## 要約(10行)

1. **先行例の一致所見**: 世界状態の書き込み口はエンジン1本(AI Town「the engine is the only mutator of game state」)。LLMは「行動の企図」を出し、実行可否はエンジンが判定する(Concordia「Whenever an agent tries to perform an action that violates the grounding, it communicates to them that their action was invalid」)。v2の原則2・5と完全一致=**設計変更不要**。
2. **語彙の実数**: OASIS=21行動の離散列挙+`{"reason":…,"functions":[…]}`のJSON。AI Town=7入力(join/leave/moveTo/startConversation/acceptInvite/rejectInvite/leaveConversation)。Generative Agentsのみ自由文で、**接地は「LLMに環境木を降ろさせる」再帰プロンプト**=呼数が爆発する形(v2は不採用でよい)。
3. **v2の2行形に欠落スロットが1つある**: 「行き先: <セルID|なし>」では**購入の対象・会話の相手・手伝いの相手**が書けない。**目的語スロットへの一般化**(行き先→対象: <セルID|物カテゴリ|人ID|なし>)を推奨(最重要の設計指摘)。
4. **会話の呼数が最大の制約**: 実会話の1ターンは**中央値1,227 ms・平均1,680 ms**(Levinson & Torreira 2015・実読)。「1呼=1実ターン」なら5分の会話で約179ターン=1体あたり約90呼=**予算10呼/体/日の9日分**。1呼=1実ターンは**成立しない**。
5. → **1呼=1「発話ブロック」(実30-60秒相当を1発話に圧縮)+相槌はエンジン生成**を推奨。会話予算は**1体あたり4.5呼/日(1.5会話×3呼)**が上限の目安(内省10.5%控除後の8.95呼/体/日の約半分)。
6. **終了はLLMに決めさせない**が現実側からも支持される: 人は会話の終わり時を合わせられない——**両者の希望どおりに終わったのは約2%**・**約46%は両者とも「もっと早く終わってほしかった」**(Mastroianni 2021・二次確認)。終了はエンジンの状態機械+max_turnsで切る。
7. **関係辺の上限は5/15/50/150/500/1500**(Dunbar 2020・実読「each layer is approximately three times the size of the layer immediately inside it」)。**社会的努力の40%が内側5人・+20%が次の10人**=会話相手選択の重みに直接使える実数。入替は**一般の関係破綻が年約1%**、環境激変時は18か月で約40%。
8. **失敗フィードバックは「追加呼び出しなし・次観測に3欄」で足りる**: 失敗位置・観測値・**可能な代替行動**の3欄構造化フィードバックが、TextWorldでQwen2.5-Coder-14B +44点/Llama-3.1-8B +42点(実読)。うち**代替行動の提示だけで+36/+40点**=v2の観測に「いま可能: <語彙3件>」を載せる根拠。
9. **ループ止め**はVoyagerの「4ラウンドで打ち切って別タスクへ」が唯一の明示先例。v2は**2回失敗で当該行動を語彙からマスク・4回で断念してエンジン既定行動**を推奨。
10. **語彙サイズ**: 種別ごと10-15語に収めれば選択劣化域に入らない見込み。ただし「10-15を超えると劣化」は二次情報(ブログ)であり**一次未確認**。一次で確実なのは「候補を7件前後に絞ると50件提示と同等」(arXiv 2605.24660・実読)。

---

## 問い1: 行動空間の先行例(LLM出力→世界状態変化の写像)

### 1-1 各システムの実装形(実読・原文引用)

| システム | 出力形式 | 語彙数 | 接地の担い手 | 妥当性検査 | 失敗時 |
|---|---|---|---|---|---|
| **OASIS** (arXiv 2411.11581v4) | JSON `{"reason":…, "functions":[{"name":…, "arguments":{…}}]}` | **21** | エンジン(SNS基盤) | 記述なし | **記述なし(空欄)** |
| **AI Town** (a16z-infra) | エンジンへの「input」(Convex validatorで型検査) | **7種** | ゲームエンジン単独 | **入力バリデータ** | 記述なし |
| **Generative Agents** (2304.03442) | 自由文の行動記述 | 無制限 | **LLMへの再帰プロンプトで環境木を降りる** | なし | 記述なし |
| **Concordia** (2312.03664v2) | 自由文の「action attempt」 | 無制限 | **Game Master(LLM)がevent statementへ変換** | GMが物理的妥当性を判定 | **本人に「無効だった」と通知** |
| **AgentSociety** (2502.08691) | 意図→数理モデル(重力モデル)へ受け渡し | 明示なし | エンジン(重力モデル・POI型) | 記述なし | **移動成否のフィードバックあり** |
| **Voyager** (2305.16291v2) | **実行可能コード**(JavaScript) | 無制限(技能ライブラリで成長) | Minecraftインタプリタ | **自己検証エージェント** | 環境フィードバック+実行エラーを次プロンプトへ |
| **CivRealm** (2401.10568) | tensor API / language API の2系統 | 空欄(未確認) | Freecivエンジン | 空欄(未確認) | 空欄(未確認) |
| **Project Sid** (2411.00114) | PIANO(並列モジュール) | 空欄(未確認) | Minecraft | 空欄(未確認) | 空欄(未確認) |

**引用(実読)**:

- OASIS §2.4: 「The action module enables 21 different types of interactions with the environment, including sign up, refresh, trend, search posts, search users, create post, repost, follow, unfollow, mute, like, unlike, dislike, undo dislike, unmute, create comment, like comment, unlike comment, dislike comment, undo dislike comment, and **do nothing**.」
  → **「何もしない」を語彙に明示的に持つ**のが実装上の要点(v2の「待機」に対応)。
  Appendix D.1: 出力は `{"reason": "...", "functions": [{"name": "...", "arguments": {...}}]}`、「your output can be directly converted into **JSON format**」。
  ※**失敗・不正行動の扱いは論文に記述なし=空欄(未確認)**。

- AI Town ARCHITECTURE.md: 「AI Town modifies its data model by processing inputs. Inputs are submitted by players and agents and processed by the game engine.」/「Use the inputHandler function to construct an input handler, specifying a Convex validator for arguments for end-to-end type-safety.」/「**Only the game engine should programmatically modify these tables, so components outside the engine can only mutate them by sending inputs.**」/「Since the engine is the only mutator of game state, it continues to run steps…」
  → v2の答申原則5(書き込み口はGM1本)と同型の実装が存在する。**型検査つき入力**という形が最も安価。

- Generative Agents §5.1: 「we prompt the language model to find the most suitable area. For example…recursively starting at the root of the agent's environment tree… until we reach a leaf node. Finally, we use traditional game path algorithms to animate the agent's movement」/「When an agent executes an action on an object, we prompt the language model to ask what happens to the state of the object. For example, if Isabella's generative agent outputs the action 'making espresso for a customer', a query to the language model indicates in response that the state of the coffee machine in Hobbs Cafe should change from 'off' to 'brewing coffee'.」
  → **1行動あたりLLM呼が「木の深さ+物の状態」ぶん追加**される設計。25体だから成立した形で、40万体では不成立。v2はセルID直接指定+物の状態はエンジン規則、が正解(既存決定と整合)。
  §5: 「At each sandbox time step, the sandbox server parses the JSON for any changes coming from the generative agents, moves the agents to their new positions」
  → GAですら**エンジンとのやり取りはJSON**であり、自由文はプロンプト内部に留まる。
  ※「エージェントが知らない場所を要求したとき」の扱いは**論文に記述なし=空欄(未確認)**。

- Concordia §2: 「Agents take actions by describing what they want to do in natural language. The GM then translates their actions into appropriate implementations.」/「In a simulated physical world the GM checks the physical plausibility of agent actions and describes their effects.」/「**Whenever an agent tries to perform an action that violates the grounding, it communicates to them that their action was invalid.**」/ 例: 「in an economic simulation the amount of money in an agent's possession may be a grounded variable…perhaps prevent them from paying more than they have available.」
  §2.2 式(3): 「The GM generates an event statement e_t in response to each agent action: e_t ∼ p(⋅|f^e(z_t),a_t)」
  → **v2の原則1(不可逆な資源移動はエンジン・不足時は無効化+本人通知)は、Concordiaで既に実装されている定石**。ただしConcordiaのGMはLLMなので、v2はここを決定論エンジンに置き換える(コスト理由)=**v2のほうが厳しい形で同じ規律**。

- Voyager §2.3: 「Environment feedback, which illustrates the intermediate progress of program execution」(例: 「I cannot make an iron chestplate because I need: 7 more iron ingots」)/「Execution errors from the program interpreter that reveal any invalid operations or syntax errors in programs」/「we instantiate another GPT-4 agent for self-verification」/「**If the agent gets stuck after 4 rounds of code generation, then we query the curriculum for another task**」/ 技能追加は検証通過後: 「at which point we add this new skill to the skill library」。
  → **未定義行動の受理(v2行16)の唯一の実装先例**。「LLMが規則を書きエンジンが実行し、検証を通ったものだけ語彙に加わる」。

- AgentSociety §3.6: 「After performing the action, the agent receives feedback. For example, if the agent attempts to move to a social gathering, it checks whether the movement was successful (e.g., did it reach the correct location, considering environmental factors like weather)」。§5.5: 「a retry mechanism. When invoking the LLM API, if erroneous responses are detected, the system will automatically reinitiate the call. The default number of retries is set to 3」(=**API再試行であって行動妥当性検査ではない**と明記)。

### 1-2 v2への含意(問い1の答え)

- **自由文→接地(GA/Concordia型)は不採用が正しい**。理由=接地に追加LLM呼が要る(GAは木の深さぶん・ConcordiaはGM 1呼/行動)。v2の予算400万呼/日では、接地に1呼増えるだけで倍額。
- **離散語彙+ラベル行(v2の2行形)はOASIS(21語・JSON)とAI Town(7入力・型検査)の中間**で、先行例の範囲内。語彙10-15語は先行例より小さい=安全側。
- **不足スロットの指摘(最重要)**: OASISは `arguments` を持ち、AI Townは `moveTo(position)` `startConversation(invitee)` のように**引数を持つ**。v2の2行形には「行き先: <セルID|なし>」しかないため、
  - 購入の**対象商品**、会話の**相手**、手伝い/断るの**相手**、通報の**対象**が表現できない。
  - **推奨: スロット名を「対象:」に一般化し `<セルID|物カテゴリ|人ID|なし>` を許す**(トークン増はゼロ〜数tok)。パーサはラベル基準なので既存パーサのまま。
  - 第2案: 行動語彙側に対象を畳み込む(購入-食料/購入-日用品)。語彙数が増えるので非推奨。
- **失敗時の扱いは、先行例のほとんどが「記述なし」**=論文化の余地(既存答申U-Fが会話容量について述べたのと同じ構図)。唯一まとまった実証はarXiv 2607.14167(問い5)。

---

## 問い2: 会話の成立・終了

### 2-1 先行システムの実装(実読)

| 系 | 開始条件 | 最大ターン | 終了信号 | 同時会話 |
|---|---|---|---|---|
| **Generative Agents** | 相手を知覚→対話するか判断 | **上限なし** | **LLMが決める**: 「The continuation of this dialogue is generated using the same mechanism **until one of the two agents decides to end the dialogue**」(§4.3.2) | 2者のみ |
| **AI Town** | `startConversation`→`acceptInvite`/`rejectInvite` の招待プロトコル。距離が遠い間は `walkingOver` | 明示なし(空欄) | `leaveConversation` | **「Players may only be in one conversation at any point in time, and conversations currently have exactly two members.」** |
| **AgentSociety** | 社会的欲求に動機づけられ、関係種別と強度で相手選択 | **明示なし** | **形式的定義なし** | 明示なし |
| **Concordia** | 会話専用機構の記述なし(GMのevent statement経由) | — | — | — |
| **(既存答申)Concordia CHANGELOG** | — | — | 「終了判断をLLMに任せる」を**やめた**一次記録(v2-conversation-deep-research.md) | — |

**引用(実読)**:
- Generative Agents §4.3.2: 「The continuation of this dialogue is generated using the same mechanism until one of the two agents decides to end the dialogue.」
- AI Town ARCHITECTURE.md: 「Conversations are created by a player and end at some point in time.」/「Players may only be in one conversation at any point in time, and conversations currently have exactly two members.」/ 会員状態3種「invited: The player has been invited to the conversation but hasn't accepted yet. walkingOver: The player has accepted the invite to the conversation but is too far away to talk. participating: The player is actively participating in the conversation.」
  → **「1人1会話・2者固定」が最も広く実装されている形**。多者会話を持つ大規模LLM社会シムの実装先例は見つからず=**空欄**(既存答申U-Fの所見「大規模で会話容量を明示設計した先行=ゼロ」と整合)。
- AgentSociety §3.4: 関係は「a strength value ranging from 0 to 100 representing social closeness between agents. Agents communicate more frequently with high strength connections」/「When receiving messages, agents generate responses based on their relationship strength with the sender, their chat history, and their current emotional state」。**ターン上限・終了条件の定義なし**。

### 2-2 現実側の実測

**(a) ターンの長さ・間隔(=呼数の分母)**
- Levinson & Torreira 2015(Frontiers in Psychology 6:731・**実読**):
  - 「The 50,510 IPUs had an average duration of **1680 ms**, and a median duration of **1227 ms**.」
  - 「Inter-speaker gaps are most typically short, with **modal values for FTOs falling between 100 and 200 ms**.」
  - 「Between-overlaps (negative FTOs) represented **30.1%** of all floor transfers」/ 重なりは信号全体の「only **3.8%**」。
- Stivers et al. 2009(PNAS 106:10587・PMC2705608・**実読**):
  - 「All distributions are unimodal with the highest number of transitions occurring **between 0 and 200 ms**.」
  - 「The medians are also quite uniform, ranging from **0 ms (English, Japanese, Tzeltal, and Yélî-Dnye)** to +300 ms (Danish, ‡Ākhoe Hai‖om, Lao) (overall cross-linguistic median +100 ms).」
  - 「The mean response offset for the full dataset is **+208 ms**」
  - → **日本語は交替が最速の群**(中央値0 ms)。v2の会話は日本語なので、実時間のターン密度は上限側で見積もるべき。

**(b) 会話の長さ**
- Mastroianni et al. 2021 PNAS(**原典403で未読・Harvard Gazette経由の二次確認**):
  - 「only about **2 percent** of conversations ended when both people wanted them to」
  - 「in about **46 percent** of conversations both parties reported wanting the conversations to end before they did」
  - 「misestimated how long their partner wanted the conversation to last by about **64 percent**」
  - 規模「**932 conversations** between pairs of people」・実験室は「252 strangers」・調査は「just over 800 participants」
  - ※**実測持続時間の分布(平均/中央値/分散)は原典未読=空欄(未確認)**。親の一次確認対象(§7-4)。
- 対面接触時間の分布: arXiv 2402.03333(**要旨のみ実読**)「the distribution of the contact duration for all the interactions within a group is **broad, with tails that resemble each other**, but not precisely, in different contexts」。**具体的な代表値(秒)は要旨に無く=空欄(未確認)**。同系の運用規約として「a face-to-face contact is observed when the duration of the contact is at least **20 seconds**」(二次記述・原典未読)。
- 街頭・職場・家庭の会話持続時間の**分布そのもの**(Whittaker et al. CHI'94 等)は**取得できず=空欄(未確認)**。

**(c) 割り込み率**
- arXiv 2501.01568v2(**実読**): 「Interruptions are a common aspect of human conversations and can occur **more than once per minute** in dyadic [21] and group conversations [14].」([21]=Sellen 1995, Human-Computer Interaction 10(4):401-444)
  - 分類: cooperative(agreement / assistance / clarification)と disruptive(disagreement / floor-taking / topic change / tangentialization)。
  - ※**元データ(Sellen 1995)は未読=数値は二次**。

**(d) 会話に費やす時間**
- Robbins & Karan 2020(SPPS・**press release経由の二次**): ゴシップ(社会的会話)に**1日平均52分**、n=467、EARで1日の約10%を録音。※原典(SAGE)未読=**二次**。

### 2-3 呼数への含意(v2の算術)

前提: **400万呼/シミュ日 ÷ 40万体 = 10呼/体/日**。日次内省が42万呼(10.5%)なので、**行動+会話に使えるのは実質 8.95呼/体/日**。

| 設計 | 1会話あたりの呼(1体分) | 1体1日1会話なら | 判定 |
|---|---|---|---|
| **1呼=1実ターン**、会話5分 | 300 s ÷ 1.68 s ≈ 179ターン ÷ 2話者 = **約90呼** | 90呼/体/日 | **不成立**(予算の10倍) |
| 1呼=1実ターン、会話1分 | 60 ÷ 1.68 ÷ 2 ≈ **18呼** | 18呼/体/日 | **不成立** |
| **1呼=発話ブロック30秒相当** | 5分会話で 300/30/2 = **5呼** | 5呼/体/日 | 会話だけで予算の56%=**要制限** |
| **1呼=発話ブロック30秒相当 + max_turns=3(1体)** | **3呼**(=実90秒〜3分相当) | 3呼/体/日 | **成立**(会話4.5呼枠に1.5会話/日) |

**結論(問い2の答え)**:
- **「1呼=1実ターン」は物理的に不成立**。実会話の1ターンは1.2-1.7秒で、これを1呼に写すと予算が2桁足りない。
- **推奨: 1呼 = 1「発話ブロック」**。1発話ブロック=実会話の**約20-35ターン(30-60秒)**を1つの発話として言語化する単位。相槌(minimal response)はエンジンが生成しLLMを呼ばない(既存答申U-Fの「小型モデルは相槌が出せない」という系統的欠陥への、コスト面からも品質面からも整合する回避策)。
- **max_turns**は現実分布ではなく**予算**から決まる: **1会話あたり1体3呼(往復6呼)を既定**、実時間換算で90秒-3分。延長は「重要度上位」のみ(内省の上位5%規則と同型)。
- **終了はエンジン**が正しい。現実側の裏づけ=**人間も終わり時を合わせられない(両者希望どおり2%・両者「早く終わりたかった」46%)**。「LLMに終了を決めさせる」ことは現実の再現ではなく、Concordiaが実際に撤回した設計。
- **同時会話**: 先行例は全て「1人1会話・2者」。v2も**既定は1人1会話・2-3者**、傍聴(bystander)は知覚契約の傍受チャネルで表現(既存決定と整合)。

---

## 問い3: 発話の世界への効果

### 3-1 先行例が許している効果の範囲(実読)

- **Concordia**: 発話を含む行動は**GMがevent statementに変換して初めて世界の事実になる**(式3)。接地変数(所持金)を超える行為は無効化+本人通知。→ **発話が直接に資源を動かすことはない**。
- **AI Town**: 発話は会話テーブルのメッセージ行。**エンジン以外は世界状態を書けない**。
- **AgentSociety**: 関係強度0-100を保持し、相互作用履歴(内容と時刻)が将来の会話に効く。**更新機構は論文に記述なし=空欄(未確認)**。
- **Generative Agents**: 発話は観測として記憶ストリームへ入り、内省・計画へ波及(=**記憶への転写のみ**)。物の状態変化はLLM問い合わせ(v2は不採用)。

→ **先行例の一致点: 発話の世界への効果は「相手の記憶に入る」ことに限られ、資源移動・状態変化は必ずエンジンのresolveを通る。** v2の行7(エンジンは配送のみ)と一致。

### 3-2 関係辺の上限の根拠(実測・実読)

Dunbar 2020, Proc. R. Soc. A 476:20200446(PMC7482201・**実読**):
- 層構造: **5, 15, 50, 150, 500, 1500**。「**each layer is approximately three times the size of the layer immediately inside it**」(平均スケール比≈3.0)。
- 努力配分の実数: 「**Approximately 40% of all social effort** (whether indexed as the frequency or duration of interaction) **is directed to the five individuals in the closest layer, with another 20% devoted to the remaining 10 members of the second layer**.」
  → **内側5人=40%、次の10人=20%、残り135人=40%**。「会話相手をエンジンが選ぶ」規則の重み表にそのまま使える。
- 減衰: 「a reduction in time devoted to a tie results in an **inexorable decline in the emotional strength of a tie**, at least for friendships」/「if lockdown continues for **more than about three months**, we may expect to see a weakening of existing friendships」
  → **接触が3か月途切れると弱化**が観測可能な閾値。
- 入替: 「approximately **40% in the network membership of young adults over an 18-month period** after they had moved away from their home town, most of which occurred in the **first nine months**」/ 関係破綻の頻度「about **1% of relationships per year**」。
- Zhou, Sornette, Hill & Dunbar 2005(arXiv cond-mat/0403299・**要旨のみ実読**): 「humans spontaneously form groups of preferred sizes organized in a **geometrical series approximating 3, 9, 27,…**」(=スケール比3の一次根拠。Proc R Soc B原典は403で未読)。
- Mollenhorst, Völker & Flap 2014(Social Networks 37・**検索結果のみ・原典未読=空欄**): 7年で元の友人の約48%が残存、討論相手・実務的援助者では約30%——**この数値は一次未確認**。

### 3-3 約束の遵守率・口コミ伝播率

- **約束の遵守率**: Vanberg 2008(Econometrica 76(6))は「約束が協力を高める」ことと機構(約束を守る選好 vs 期待を裏切りたくない)の識別が主題。**遵守率の実数は原典未読=空欄(未確認)**。
- **対面口コミの伝播率**: 対面WOMが電子WOMより説得力が高いという質的所見は複数見つかったが、**「聞いた人のうち何%が誰かに伝えるか」の一次実測は取得できず=空欄(未確認)**。
- **社会的会話の総量**: 1日あたり約52分(Robbins & Karan 2020・**二次**)。

### 3-4 v2への含意(問い3の答え)

**発話が世界状態に及ぼしてよい効果=次の5つに限定(それ以外は禁止)**:

| # | 効果 | 実行主体 | 根拠 | タグ |
|---|---|---|---|---|
| E1 | **記憶への転写**(聞き手の記憶ストリームに1レコード) | エンジン | GA・Concordia(event statement) | mechanism |
| E2 | **関係辺の強度更新**(接触1回=+Δ、非接触は時間減衰) | エンジン | Dunbar 2020(接触量↔強度の単調関係) | mechanism |
| E3 | **辺の追加/削除**(層容量5/15/50/150の枠内・押し出し方式) | エンジン | Dunbar 2020(層サイズ・比3) | mechanism |
| E4 | **PlanSpecのrevises提案**(改訂権者のみ・指令/店主/管理者) | エンジンが権限検査→適用 | 世界過程設計 §2 `revises` | mechanism |
| E5 | **取引/約束の合意フラグ**(commitmentレコード生成。**資源は動かない**) | エンジンがresolve時に決済 | Concordia(接地変数の強制) | mechanism |

- **禁止**: 発話による所持金移動・在庫変化・場所移動・他者の状態直接変更。全て対応する**行動語**を経由させる(発話は「意図の宣言」まで)。
- **約束の遵守率**は一次データが無いため、**遵守/違反は較正パラメータ(expedient)**として登録し、Phase 2で「約束→実行」の一致率を観測量として出す(=歪みの宣言材料)。**初期値を文献から置くことはしない**。

---

## 問い4: 種別ごとの語彙

### 4-1 語彙サイズと小型モデルの関係(実読)

- arXiv 2605.24660「How Many Tools Should an LLM Agent See? A Chance-Corrected Answer」(**要旨実読**):
  - 「Before an LLM agent can use a tool, a retrieval system must decide which candidate tools to show to the agent. How long should that shortlist be? **Show too many tools and the model struggles to choose. Show too few and the correct tool may not appear.**」
  - BFCL(370ツール): 「the learned policy nearly matches the coverage of showing 50 tools (**90.3% vs 90.8%**) while presenting only **7 on average**」
  - Claude Sonnet 4.6: 「**93.1% versus 87.1%** when always shown 5 tools, widening to **76.8% vs 60.9%** on medium-difficulty queries」
  - 指標: 「Bits-over-Random (BoR), a chance-corrected metric」
  - → **「候補は少ないほど良い」ではなく「文脈適応的に7前後まで絞ると50件提示と同等」**。v2の固定語彙10-15はこの領域の内側。
  - 小型モデルほど早く劣化する、は本文の主張として抽出されたが**モデル別の具体的閾値はPDFから抽出できず=空欄(未確認)**。
  - 「10-15ツールを超えると劣化」「50超で13%まで低下」は**二次(ブログ)であり一次未確認**。
- arXiv 2408.02442「Let Me Speak Freely?」(**要旨・所見実読**):
  - 「a significant decline in LLMs' reasoning abilities under format restrictions」/「stricter format constraints generally lead to greater performance degradation in reasoning tasks」
  - 劣化の機構として「the **misordering of reasoning and final answer keys** in structured outputs」を挙げる。
  - **分類タスクでは逆に厳格な書式が有利**(「classification tasks benefit from stricter format adherence as it reduces ambiguity」)。
  - → **v2の2行形(1行目=理由→2行目=行動)は、この論文が指摘する失敗様式を最初から回避している**。行動語の選択は分類タスク側=厳格書式が有利。**既存決定の強い裏づけ**。
- 文法拘束デコーディング: 「tokens that do not conform to the grammar are marked as invalid, and their corresponding logit values are set to negative infinity」——**書式エラーを構成的にゼロにする**。小型モデルでの有効性の記述あり(**いずれも二次情報。一次未確認**)。
  → **推奨: 「行動: 」の直後の1語だけをenum文法で拘束**(理由行・ひと言は自由)。書式エラー率を構成的に0にでき、Let Me Speak Freelyの警告(推論の劣化)は理由行が自由なので回避される。

### 4-2 種別ごとの語彙分割(推奨)

**原則**: (i) 共通基本語彙は全種別で同一トークン列(prefix共有=KV再利用に効く)。(ii) 種別固有語は**役割固有の権限を持つものだけ**。(iii) **1種別あたり合計15語以内**。

**案A(種別分割)**

| 種別 | 基本12語 | 種別固有(追加) | 合計 |
|---|---|---|---|
| 住民 | 移動/乗車/降車/購入/待機/会話/退去/通報/手伝い/断る/休憩/就寝 | (なし) | **12** |
| 通勤者 | 同上 | (なし) | **12** |
| 来街者 | 同上 | 並ぶ / 撮影 | **14** |
| 従業者 | 同上 | 接客 / 補充 / 開閉店 / 価格改定 | **16** |
| 乗務員 | 同上 | 発車 / 停車 / 放送 / 遅延報告 | **16** |
| 指令 | 同上 | 計画改訂 / 指示 | **14** |

**案B(共通語彙+権限検査)= 推奨**
- 語彙は全種別共通の**18語**に統一し、**種別で変えるのは権限(エンジンの前提条件検査)だけ**。
- 利点: (1) prefix完全共有(§5のprefix規約と最も相性がよい)。(2) 語彙管理コストゼロ。(3) **「本部でない者が価格改定を試みて失敗する」という創発が観測できる**——ボトムアップ・ドクトリン(CLAUDE.md §3)に合致し、指令エージェント追補の条件(b)「役割知識から自ずと発生する形」とも整合。
- 欠点: 無効行動が増える。→ **失敗率をablationで測る**(案A vs 案Bで不正行動率・呼数を比較)。
- 18語は 2605.24660 の「50件提示でも90.8%」の領域内で、**7件前後の適応的絞り込みに近づけるには「いま可能: <3語>」の提示(問い5)が同じ役割を果たす**——すなわち**語彙は共通18語・観測では可能行動3件を提示**、が本答申の統合案。

---

## 問い5: 失敗のフィードバック

### 5-1 先行の実証(実読)

- arXiv 2607.14167「Structured Feedback Improves Repair in an LLM Agent Loop」(**実読**):
  - 3欄構造: **failure location / observed value / admissible alternatives**。
  - §4.1(TextWorld 50ゲーム、呼び出し予算4): 生の診断メッセージ→構造化フィードバックで成功が **14/50→36/50(Qwen2.5-Coder-14B、+44点、95%区間28-60、Holm調整 p=3.15×10⁻⁵)**、**8/50→29/50(Llama-3.1-8B、+42点、28-56、p=3.81×10⁻⁶)**。
  - 寄与分解: 「**Adding those alternatives increases success by 36 points for Qwen and 40 for Llama**」/「LocObs omits admissible alternatives and performs close to RawDiag」
    → **効いているのはほぼ「可能な代替行動の提示」**。位置だけ・観測値だけでは効かない。
  - 予算依存: 「RawDiag is flat from four through eight calls. Structured feedback continues improving Llama through six calls.」
  - 対象環境: 「50 fixed TextWorld games」(3部屋・4物・2段クエスト)+「15-task HumanEval scope check」。
- ALFWorld: 「ALFWORLD has only one error message in the form of "**Nothing happens.**"」(二次記述・原典未読)。→ **無情報な失敗通知は最悪の設計**という参照点。
- Voyager §2.3: 「If the agent gets stuck after **4 rounds** of code generation, then we query the curriculum for another task」→ **ループ打ち切りの唯一の明示先例**。
- Concordia §2: 「it communicates to them that their action was invalid」→ **失敗は必ず本人に返す**。
- AgentSociety §3.6: 移動の成否をフィードバックし記憶を更新。

### 5-2 v2への含意(問い5の答え)

**追加呼び出しゼロで返す設計**: 次回の観測ブロックに**「直前結果ブロック」**を置く(位置=最も変化率が高い=末尾寄り。§2.2の並び規約に従う)。

```
直前の行動: 購入(コンビニA・おにぎり)
結果: 失敗。理由=所持金不足(所持 120円 / 必要 180円)。
いま可能: 待機 / 移動 / 退去
```

- 3欄が揃っている(**失敗位置=行動、観測値=所持金、可能な代替=3語**)ため、arXiv 2607.14167の効き筋にそのまま乗る。
- **トークン予算**: 約30-50 tok。§3.2のチャネル別上限に**「直前結果=50 tok」を新設**(個体依存300の内数)。
- **可能行動3件の生成はエンジンの前提条件検査の副産物**(語彙18語×前提条件の評価は数十命令)。追加LLM呼ゼロ。

**ループ防止規則(推奨・値はexpedient)**:
1. **同一(行動,対象)が2回連続失敗 → その組をn分間 admissible から外す**(語彙マスク)。マスクは観測の「いま可能」から自動的に消える=モデルに再選択させない。n=30分を初期値。
2. **同一計画境界内で通算4回失敗 → 断念**。エンジンが既定行動(待機 or 退去)を実行し、「断念」を記憶に1レコード書く(Voyagerの4ラウンドと同値)。
3. **失敗が3回続いた個体は次回起床で直前結果を2件分載せる**(T1'一時昇格)。呼数は増えない。
4. **診断行に常設**: 失敗率・マスク発火数・断念数を種別別/日。予算宣言表の「運用5 診断行常設」に1欄追加。
5. **失敗しない行動を常に1つ保証**(待機)。admissible集合が空にならないことをエンジンが保証=無限失敗ループの構造的防止。

---

## 問い6: 推奨

### (a) 行動契約表(雛形・種別横断の基本語彙)

列: 行動語 | 対象スロット | 前提条件(エンジン検査) | 効果(状態変化) | コスト | 失敗の意味論 | タグ

| 行動語 | 対象 | 前提条件 | 効果 | コスト | 失敗の意味論 | タグ |
|---|---|---|---|---|---|---|
| **移動** | セルID | 経路が存在・当該層(地上/地下/デッキ)で連結・現行動が中断可 | 位置=経路上へ。到着時刻はエンジンが算出 | 時間(経路長/速度)・体力 | 「到達不能(経路なし)」/「途中で打ち切り(混雑・閉鎖)」 | mechanism |
| **乗車** | 駅/車両ID | 同一セルに停車中の車両・運賃≦残高 or IC・定員に空き | 位置=車両。運賃はエンジンが決済 | 運賃・時間 | 「満員(乗れず)」/「運賃不足」/「当該時刻に列車なし」 | mechanism |
| **降車** | セルID | 車両に乗車中・当該駅に停車 | 位置=駅セル | 0 | 「その駅には止まらない」 | mechanism |
| **購入** | 物カテゴリ+店ID | 営業中・在庫>0・所持金≧価格 | 在庫−1・所持金−価格・所持品+1(**保存則: 店の売上+同額**) | 価格・時間(待ち行列) | 「所持金不足(残高/価格を返す)」/「在庫切れ」/「営業時間外(次回開店時刻を返す)」 | mechanism |
| **待機** | なし | なし(常に可能=**安全弁**) | 時間経過のみ | 時間 | **失敗しない** | mechanism |
| **会話** | 人ID | 同一セル・距離≦会話距離(≈1m・台帳候補)・相手がidle・拒否履歴なし | 会話セッション生成(OPENING) | 呼(§(b)) | 「相手が別の会話中」/「断られた」/「相手が去った」 | mechanism |
| **退去** | なし | 会話/待ち行列/施設に所属中 | 所属解除。会話ならCLOSING経由 | 0-短時間 | **失敗しない** | mechanism |
| **通報** | 対象(人/事象ID) | 通報先が存在(制度)・当該事象を知覚済み | 事象レコードに通報1件。検知確率へ入力(行12) | 時間 | 「対象を特定できない」/「通報先に届かない」 | **expedient**(通報→立件の較正データなし) |
| **手伝い** | 人ID | 相手が援助要求状態・同一セル | 相手のタスク進捗+・関係辺強度+Δ | 時間 | 「相手が要求していない」/「能力不足」 | **expedient** |
| **断る** | 人ID/要求ID | 保留中の要求が存在 | 要求を却下。関係辺強度−Δ | 0 | **失敗しない** | mechanism |
| **休憩** | なし | なし | 内受容3変数(疲労等)の回復 | 時間 | **失敗しない** | mechanism |
| **就寝** | セルID(寝床) | 当該セルが就寝可(自宅/宿) | 睡眠状態へ遷移→**T2内省を発火**(§6と接続) | 時間 | 「寝る場所がない」(路上就寝は別扱い=U18) | mechanism |

**種別固有(案Bでは全員に見せ、権限だけエンジンが検査)**:

| 行動語 | 権限保持者 | 前提条件 | 効果 | 失敗の意味論 | タグ |
|---|---|---|---|---|---|
| **接客** | 従業者 | 同一店舗・待ち行列>0 | 待ち行列−1・購入の成立を可能に | 「客がいない」 | mechanism |
| **補充** | 従業者 | 在庫置場>0・営業中 | 棚在庫+(**ドクトリン: 棚が減る=補充行動**) | 「バックヤードに在庫なし」 | mechanism |
| **開閉店** | 従業者(権限) | 店舗の管理権限 | PlanSpec(営業時間)の**実績**を確定 | 「権限なし」 | mechanism |
| **価格改定** | 従業者(権限)/本部 | 改訂権者であること | `revises(Agent, PlanSpec[価格表])` | 「権限なし(=創発の観測点)」 | mechanism(行5の決定に従う) |
| **発車/停車** | 乗務員 | 当該列車に乗務中・前方閉塞 | 列車位置の更新・ActualLog追記 | 「前方閉塞」/「指令の抑止」 | mechanism |
| **放送** | 乗務員/駅員 | 車内/駅の放送設備 | 当該セルの聴覚イベント(知覚契約の聴覚チャネル) | 「設備がない」 | mechanism |
| **遅延報告** | 乗務員 | 実績と計画の差>閾値 | ActualLogに逸脱語彙(GTFS-RT式)を追記 | 「報告先不明」 | mechanism |
| **計画改訂** | 指令(権限) | 改訂権者であること | `revises(指令, PlanSpec[ダイヤ])`・公示範囲に従い配送 | 「権限なし」 | mechanism |
| **指示** | 指令 | 対象が自社の乗務員 | 対象の役割知識に指示レコード | 「対象が受信圏外」 | mechanism |
| **並ぶ / 撮影** | 全員 | 待ち行列が存在 / 撮影可 | 待ち行列に加入 / 記憶+SNS投稿候補 | 「行列がない」/「撮影禁止」 | expedient |

**すべての行に共通の必須事項**:
1. **効果はエンジンのresolveでのみ適用**(原則2・5)。
2. **不可逆な資源移動を含む行(購入・乗車)は保存則の対象**——faucet/sink登録済みであること(CLAUDE.md §4)。
3. **失敗しない行動が最低1つ常に可能**(待機)。
4. **expedientタグの行は感度試験IDを持つ**。
5. **各行に「パターン照合1行」**(パターン台帳ゲート)を書けないものは作らない。

### (b) 会話プロトコル(推奨)

```
[開始ゲート](すべてエンジン規則)
  条件: 同一セル ∧ 距離≦d_talk ∧ 相手がidle ∧ 直近に拒否履歴なし ∧ 双方に会話呼予算が残っている
  手順: 招待(行動語「会話」)→ 応答判定(エンジン確率・較正目標=声かけ応答率 約0.8 ※既存答申U-F)
        → 不応答は「無視された」イベント(呼を消費しない)
  状態: AI Town型の invited / walkingOver / participating の3状態を採る(実装先例あり)

[進行]
  1呼 = 1発話ブロック(実会話30-60秒相当を1発話に圧縮して言語化)
  話者選択(WHO) = エンジン(SSJ 1a/1b/1c・既存答申U-F)
  相槌・最小応答  = エンジンが生成(LLMを呼ばない)
  参加者上限 = 3(2者既定)。1人1会話。
  割り込み = 次TRPでの優先権奪取に離散化(発生率の目安=1分に1回超・Sellen 1995 二次)

[終了](LLMに判断させない)
  ハード終了: max_turns = 1体あたり3呼(往復6呼)。重要度上位のみ +2呼まで延長。
  ソフト終了: 話題スタック空 ∨ lapse(沈黙>閾値)∨ 片方が「退去」を出力 ∨ セルを離れた
  CLOSING : preclosing 1発話(エンジンの定型で可)→ terminal
  根拠   : Concordiaが撤回した設計 + 現実側でも終了時点は合意されない(2% / 46%)

[効果=記憶転写の規則]
  addressed recipient  : 発話全文を記憶に1レコード(重み1.0)
  unaddressed recipient: 要約1文(重み0.5)
  bystander(傍受)     : 3段ゲート通過分のみ・要約1文(重み0.2)
  ※重みは全て expedient(一次根拠なし)。SI-RNN の役割別更新(既存答申U-F)を先例として引くのみ。
```

**呼数の会計(1シミュ日・40万体)**:
- 会話予算 = 4.5呼/体/日 → **180万呼/日(全体の45%)**
- 内訳例: 1.5会話/体/日 × 3呼/会話 = 4.5
- 残り 4.45呼/体/日(178万呼)が行動決定+日次内省(1.05呼)
- → **会話がv2最大の呼消費項**。ablation候補「会話max_turns 3 vs 2」を第1陣に入れることを推奨。

### (c) 関係辺の更新規則(推奨)

| 項目 | 値 | 根拠 | タグ |
|---|---|---|---|
| 層容量 | **5 / 15 / 50 / 150**(累積・内包的) | Dunbar 2020(実読・比≈3) | mechanism |
| 認知だけの外層 | 500 / 1500 は**辺として持たない**(名前想起テーブルのみ) | Dunbar 2020 + コスト理由 | mechanism |
| 会話相手選択の重み | 内側5人に**40%**、次の10人に**20%**、残り135人に**40%** | Dunbar 2020(直接引用可) | mechanism |
| 辺の追加 | 会話セッション完了で新規辺(強度=初期値) | — | expedient |
| 強度の増加 | 発話ブロック1回ごとに +Δ(逓減) | Dunbar 2020(接触量↔強度の単調関係) | expedient(Δは較正) |
| 強度の減衰 | 非接触で指数減衰。**3か月無接触で「弱化」段階へ**(半減期の初期値=90日) | Dunbar 2020「more than about three months … weakening」 | expedient(半減期は較正) |
| 押し出し(層溢れ) | 層が満杯なら最弱の辺を1つ外層へ降格、最外層から溢れたら削除 | — | **expedient(機構の先例なし)** |
| 年間入替率(平時) | **関係破綻 約1%/年** | Dunbar 2020(実読) | mechanism |
| 年間入替率(環境激変時) | **18か月で約40%**、大半は最初の9か月 | Dunbar 2020(実読) | mechanism |
| 内層の年間入替率 | **空欄(未確認)** ※Mollenhorst 2014「7年で48%残存」は原典未読 | — | 未確認 |

**行8の「上限」の答え**: 上限=**150(active edges)**、内部の層容量5/15/50を同時に強制。上限の一次根拠はDunbar 2020(実読)。**押し出し規則そのものには先例がないのでexpedient**。既存決定「B3照合(内層top5入替)」は、Dunbarの「内側5人に努力の40%」と直接対応する。

### (d) 未定義行動の受理手順(行16)

```
段0(エンジン・ゼロ呼): 行動語が語彙外 → 辞書で近い語彙への写像を試みる。
                       写像できたら通常処理(失敗を返さない)。
段1(エンジン・ゼロ呼): 写像不能 → 「未定義行動レコード」を作成し、当該個体には
                       失敗フィードバック「その行動は今できない。いま可能: <3語>」を返す。
                       同一の未定義行動の出現回数をカウント。
段2(裁定・初回のみLLM): 同一の未定義行動が閾値N回(初期値=10体分)出現したら、
                       裁定エージェント(層3)が1呼で
                         前提条件 / 効果 / コスト / 失敗の意味論(=行動契約表の1行)
                         + パターン台帳の門(現実照合1行)
                       を生成する(=Voyagerの「LLMが規則を書く」の縮約)。
段3(検収):             保存則・性能予算に触れる行はエンジン側テストを通るまで採用しない
                       (Voyagerの self-verification に相当。v2では自動テスト+親の検収)。
段4(判例化):           採用後は語彙に加わり、2回目以降は決定論参照(原則6)。
```

- **呼数**: 段0-1はゼロ呼。段2は「10体に1回」程度の発火なので予算影響は無視できる【推測: 閾値Nは較正パラメータ】。
- **語彙の成長は上限つき**: 種別あたり合計**24語**を硬い上限(問い4の劣化域を避ける)。到達したら**最も使われない語を封印**(台帳へ)。
- **counts_asとの接続**: 段2の生成物が制度的事実に触れる場合、世界過程設計 §2 の `counts_as(物理的事実, 制度的事実, 文脈)` に登録する。

---

## 問い7: 親の一次確認リスト(最重要5件)

| # | 主張 | URL | 引用文(確認すべき) | 確認すべき数値 |
|---|---|---|---|---|
| **1** | 実会話の1ターンは1.2-1.7秒 → 「1呼=1実ターン」は予算上不成立 | https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.00731/full | 「The 50,510 IPUs had an average duration of 1680 ms, and a median duration of 1227 ms.」 | **1680 ms / 1227 ms / n=50,510**(IPU=turnと同一視できるかも確認) |
| **2** | 関係辺の上限=150、層=5/15/50/150、努力配分40%/20% | https://pmc.ncbi.nlm.nih.gov/articles/PMC7482201/ | 「each layer is approximately three times the size of the layer immediately inside it」/「Approximately 40% of all social effort … is directed to the five individuals in the closest layer, with another 20% devoted to the remaining 10 members of the second layer.」 | **5/15/50/150/500/1500・比3.0・40%/20%・関係破綻1%/年・18か月40%・3か月で弱化** |
| **3** | 失敗フィードバックは「可能な代替行動」の提示がほぼ全ての効果を生む | https://arxiv.org/html/2607.14167 | 「Adding those alternatives increases success by 36 points for Qwen and 40 for Llama.」/「by 44 points for Qwen (95% interval 28–60; Holm-adjusted exact p=3.15×10−5)」 | **+44点(14B)/+42点(8B)/代替提示のみで+36/+40・予算4呼・TextWorld 50ゲーム**(査読状況も) |
| **4** | 「終了をLLMに決めさせない」は現実側からも支持される(人間も終了を合意できない) | 原典 https://www.pnas.org/doi/10.1073/pnas.2011809118(**403で未読**)/ 二次 https://news.harvard.edu/gazette/story/2021/03/researchers-find-conversations-dont-end-when-people-want-them-to/ | 「only about 2 percent of conversations ended when both people wanted them to」/「in about 46 percent of conversations both parties reported wanting the conversations to end before they did」 | **2% / 46% / 932会話**、加えて**会話の実測持続時間分布(本答申で空欄)** |
| **5** | 世界状態の書き込み口をエンジン1本にする実装先例が存在する / 無効行動は本人へ通知する | https://raw.githubusercontent.com/a16z-infra/ai-town/main/ARCHITECTURE.md および https://arxiv.org/html/2312.03664v2 | AI Town: 「Only the game engine should programmatically modify these tables, so components outside the engine can only mutate them by sending inputs.」/ Concordia §2: 「Whenever an agent tries to perform an action that violates the grounding, it communicates to them that their action was invalid.」 | 引用文の逐語一致(v2原則5・原則1の外部裏づけとして正典化する場合) |

---

## 参照一覧

| 出典 | 著者・年 | URL | 確認状況 |
|---|---|---|---|
| OASIS: Open Agent Social Interaction Simulations with One Million Agents | Yang et al. 2024 (arXiv 2411.11581v4) | https://arxiv.org/html/2411.11581v4 | ✔ 実読(§2.4・App D.1) |
| AgentSociety | Piao et al. 2025 (arXiv 2502.08691) | https://arxiv.org/html/2502.08691 | ✔ 実読(§3.3-3.6, §5.5) |
| AgentSociety 2 | 2026 (arXiv 2607.11895) | https://arxiv.org/abs/2607.11895 | 空欄(要旨のみ・行動interfaceの記述なし) |
| Generative Agents: Interactive Simulacra of Human Behavior | Park et al. 2023 (arXiv 2304.03442) | https://ar5iv.labs.arxiv.org/html/2304.03442 | ✔ 実読(§4.3.2, §5, §5.1) |
| Voyager: An Open-Ended Embodied Agent with LLMs | Wang et al. 2023 (arXiv 2305.16291v2) | https://arxiv.org/html/2305.16291v2 | ✔ 実読(§2.3, App A.1) |
| Concordia: Generative agent-based modeling with actions grounded in… | Vezhnevets et al. 2023 (arXiv 2312.03664v2) | https://arxiv.org/html/2312.03664v2 | ✔ 実読(§2, §2.2) |
| AI Town ARCHITECTURE.md | a16z-infra 2023- | https://raw.githubusercontent.com/a16z-infra/ai-town/main/ARCHITECTURE.md | ✔ 実読 |
| CivRealm (ICLR 2024) | Qi et al. 2024 (arXiv 2401.10568) | https://arxiv.org/html/2401.10568v1 | **空欄(未確認)**——行動空間・不正行動maskingは未取得 |
| Project Sid (PIANO) | Altera.AL 2024 (arXiv 2411.00114) | https://arxiv.org/pdf/2411.00114 | **空欄(未確認)**——行動空間の詳細未取得 |
| Timing in turn-taking and its implications for processing models of language | Levinson & Torreira 2015, Front. Psychol. 6:731 | https://www.frontiersin.org/journals/psychology/articles/10.3389/fpsyg.2015.00731/full | ✔ 実読(1680/1227 ms・FTO 100-200 ms・重なり30.1%/3.8%) |
| Universals and cultural variation in turn-taking in conversation | Stivers et al. 2009, PNAS 106:10587 | https://pmc.ncbi.nlm.nih.gov/articles/PMC2705608/ | ✔ 実読(0-200 ms・+208 ms・日本語中央値0 ms) |
| Do conversations end when people want them to? | Mastroianni, Gilbert, Cooney & Wilson 2021, PNAS 118:e2011809118 | https://www.pnas.org/doi/10.1073/pnas.2011809118 | **原典403で未読**。二次で2%/46%/932を確認 |
| (二次)Harvard Gazette 記事 | 2021 | https://news.harvard.edu/gazette/story/2021/03/researchers-find-conversations-dont-end-when-people-want-them-to/ | ✔ 実読(二次) |
| On the duration of face-to-face contacts | 2024 (arXiv 2402.03333 / EPJ Data Science) | https://arxiv.org/abs/2402.03333 | ✔ 要旨のみ実読(**代表値は空欄**) |
| Interruption Handling for Conversational Robots | 2025 (arXiv 2501.01568v2) | https://arxiv.org/html/2501.01568v2 | ✔ 実読(「more than once per minute」・出典[21]=Sellen 1995 は未読) |
| Structure and function in human and primate social networks | Dunbar 2020, Proc. R. Soc. A 476:20200446 | https://pmc.ncbi.nlm.nih.gov/articles/PMC7482201/ | ✔ 実読(層5/15/50/150/500/1500・比3・40%/20%・1%/年・18か月40%・3か月) |
| Discrete hierarchical organization of social group sizes | Zhou, Sornette, Hill & Dunbar 2005, Proc. R. Soc. B 272:439 | https://arxiv.org/abs/cond-mat/0403299 | ✔ 要旨のみ実読(比≈3)。royalsocietypublishing 原典は403で未読 |
| Changes in personal relationships(7年入替) | Mollenhorst, Völker & Flap 2014, Social Networks 37 | https://www.sciencedirect.com/science/article/abs/pii/S0378873313001056 | **空欄(未確認)**——48%/30%は検索結果由来で原典未読 |
| Structured Feedback Improves Repair in an LLM Agent Loop | 2026 (arXiv 2607.14167) | https://arxiv.org/html/2607.14167 | ✔ 実読(+44/+42点・代替提示+36/+40・予算4) |
| How Many Tools Should an LLM Agent See? A Chance-Corrected Answer | 2026 (arXiv 2605.24660) | https://arxiv.org/abs/2605.24660 | ✔ 要旨実読(90.3% vs 90.8%・平均7件・93.1%/87.1%・76.8%/60.9%)。**モデル別閾値は空欄** |
| Let Me Speak Freely?(書式制約の影響) | Tam et al. 2024 (arXiv 2408.02442) | https://arxiv.org/abs/2408.02442 | ✔ 要旨・所見実読(**具体数値は未取得**) |
| Who Gossips and How in Everyday Life?(52分/日) | Robbins & Karan 2020, SPPS | https://journals.sagepub.com/doi/abs/10.1177/1948550619837000 | **原典未読=二次**(52分/日・n=467) |
| Why Do People Keep Their Promises?(約束の遵守率) | Vanberg 2008, Econometrica 76(6) | https://onlinelibrary.wiley.com/doi/abs/10.3982/ECTA7673 | **空欄(未確認)**——遵守率の実数は未取得 |
| Informal workplace communication(職場会話の長さ) | Whittaker, Frohlich & Daly-Jones 1994, CHI'94 | https://dl.acm.org/doi/10.1145/191666.191726 | **空欄(未確認)** |
| 対面口コミの伝播率 | — | — | **空欄(未確認)**——一次実測を発見できず |

---

## 空欄(未確認)一覧 — 記憶で埋めていない項目

1. **街頭・職場・家庭の会話持続時間の実測分布**(Whittaker 1994・SocioPatterns代表値・Mastroianniの実測分布)。→ **会話のmax_turnsを「現実分布から」決める根拠は現状ない**。本答申の推奨値は**予算由来=expedient**。
2. **割り込み率の一次データ**(Sellen 1995 原典)。
3. **約束の遵守率の実数**(Vanberg 2008 ほか)。
4. **対面口コミの伝播率**。
5. **内層(5/15)の年間入替率の一次データ**(Mollenhorst 2014 原典)。
6. **CivRealm / Project Sid の行動空間・不正行動処理**。
7. **語彙サイズと小型モデルの書式エラー率/不正行動率の直接的な実証**(ツール数の研究は近いが「行動語彙」の実験ではない)。「10-15語で劣化開始」は**二次情報**。
8. **OASIS の失敗行動処理**(論文に記述なし)。

---

## 付録: 既存決定との矛盾・要確認点(Claudeによる積極検出)

| # | 論点 | 現状の決定 | 本答申の所見 | 提案 |
|---|---|---|---|---|
| A | **対象スロットの欠落** | 出力2行形は「行き先: <セルID\|なし>」 | 購入の商品・会話の相手・手伝いの相手・通報の対象が表現できない | **「対象: <セルID\|物カテゴリ\|人ID\|なし>」へ一般化**(ラベル基準パーサのまま・トークン増ほぼゼロ) |
| B | **会話ターンの単位** | 会話ターン起床は不応期0(同期的相互作用) | 実会話の1.7秒刻みで起床すると呼数が2桁足りない | **「起床の単位は実ターンでなく発話ブロック」と契約書に明記**(不応期0は保つ) |
| C | **max_turnsの根拠** | 未定 | 現実分布からの値は取得できず | **予算由来(1体3呼)と明記しexpedient登録+ablation「3 vs 2」** |
| D | **語彙の種別分割 vs 共通化** | 「行動語彙は種別ごとの固定リスト」 | 権限をエンジン検査に寄せれば**共通18語**で済み、prefix完全共有+「権限なき者の試行」という創発が観測できる | **案B(共通語彙+権限検査)をablation候補に**。prefix共有の実測利得はBN実測で測れる |
| E | **直前結果ブロックの予算** | §3.2に該当チャネルなし | 失敗フィードバックの効果は実証済み(+36〜44点) | **「直前結果=50 tok」を§3.2に新設**(個体依存300の内数) |
| F | **未定義行動の裁定コスト** | 行16「裁定は初回のみ」 | 段0(語彙外の辞書写像)を挟めば裁定発火をさらに減らせる | **段0をエンジンに追加**(ゼロ呼) |
| G | **文法拘束デコーディング** | 「厳密JSONは課さず寛容パーサ」 | 「行動:」直後の1語だけenum拘束すれば書式エラーを構成的に0にできる。理由行が自由なので Let Me Speak Freely の警告(推論劣化)も回避 | **行動語スロットのみ文法拘束**を検討(§10.3「出力の固定2行形」の卒業条件≤0.10を構成的に満たす) |
