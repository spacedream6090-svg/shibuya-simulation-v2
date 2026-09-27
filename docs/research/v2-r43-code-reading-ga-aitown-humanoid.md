# R-43 答申: 行動の表現・粒度・持続の実装読み(Generative Agents / AI Town / Humanoid Agents)
<!-- hdr:v1 -->
- **分野**: LLM エージェント・シミュレーションの先行実装(コード読解) | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **B** = サブ実読(コード・設定・文書 46 ファイル・空欄 9)・**親検収 済(第272・下の欄)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: v2 は LLM 出力を「行動 1 語+対象+ひと言」に固定し、エンジンが契約行で適用している。ユーザーの問い(思考頻度に対し行動粒度が小さすぎる・待つ等までエンジンで規定する必要があるか)と親の仮説「世界に触れる行為だけ契約・待つ/見る/散歩は活動=自由文+持続」を書く前に、先行 3 実装が行動をどう表し・持続を誰が決め・効果をどう解くかをコードで確かめる。**推奨はしない**(事実のみ)。
> 規律: 子サブ未起動・Web は読むだけ・コミットなし・台帳未編集・本書の新規作成のみ。
> 読み方: 行番号を保つため、GitHub API(ツリー・コミット)と raw.githubusercontent.com のファイルを**標準出力へ読むだけ**にした(clone・保存・実行なし)。WebFetch は要約モデルを挟み行番号と逐語が保てないため使っていない。コミットは読んだ日の main の先頭に固定。引用は逐語(英語のまま)、訳・要約は地の文。[推測] は推測、[計算] はコードの定数からの算術で実測ではない。

---

> **親検収(2026-09-27・第272・Fable 5.1)**: 結論を変える引用 7 か所を、答申と同じ固定コミットの raw を標準出力に読んで(保存なし)逐語確認した。**全一致・訂正なし**。
> - ✓ AI Town `agentOperations.ts:128-129`: `// TODO: have LLM choose the activity & emoji` / `const activity = ACTIVITIES[Math.floor(Math.random() * ACTIVITIES.length)];` — activity は乱数で選ぶ。
> - ✓ AI Town `constants.ts:67-71`: `ACTIVITIES` は 3 件(reading a book / daydreaming / gardening)・各 `duration: 60_000`。`agentInputs.ts:71-73`: `if (args.activity) { player.activity = args.activity; }`=代入のみ(効果なし)。
> - ✓ AI Town の入力口: `inputHandler(` は agentInputs.ts 4・player.ts 3・conversation.ts 6=**13**(既存答申の「7 入力」は ARCHITECTURE.md の列挙=版の差。既存答申に第272 の追記を入れた=訂正の伝播)。
> - ✓ GA `plan.py:774-777`: `wait_until = ((target_persona.scratch.act_start_time + datetime.timedelta(minutes=target_persona.scratch.act_duration - 1))…` / `return f"wait: {wait_until}"`。`plan.py:910-913`: `inserted_act = f'waiting to start …'`・`act_address = f"<waiting> {curr_tile[0]} {curr_tile[1]}"`。
> - ✓ GA `scratch.py:550-557`: 開始時刻の秒を切り上げ(`x.replace(second=0)` + 1 分)て `end_time.strftime("%H:%M:%S") == self.curr_time.strftime("%H:%M:%S")` の等値比較=分境界の step でだけ真(§7-3 の読みは妥当)。`reverie.py:84` `self.sec_per_step = reverie_meta['sec_per_step']`。
> - ✓ Humanoid `generative_agent.py:734-741`: `time_interval = "15 minutes"`・`while not …check_plan_format(…) and not …check_plan_follow_time_start_and_end_and_15m_interval(…) and attempts < max_attempts:`=§7-5 の読み(両方失敗の間だけ再生成)は逐語どおり。
> - ✓ Humanoid `humanoid_agent.py:196-203`: `"…does the activity '{activity}' involve {action}? Please respond with either yes or no."` → `if 'yes' in response.lower(): basic_needs[attr] += 1` / `elif random.random() < decline_likelihood_per_time_step: -= 1`=LLM の yes/no+乱数で ±1。
> - △ 親未確認: §3 Q3 の呼数 [計算](8〜12 呼/step)・GA の 1 体 1 日の呼数(空欄のまま)。§7-6 の再計算は正典化時に行う。
> - 取得手段(curl を標準出力に読むだけ)は「Web は読むだけ」の範囲内と親が判定(保存・clone・実行なし)。

## §0 読んだもの

| システム | リポ URL | ブランチ/コミット | 読んだ日 | 読んだファイル |
|---|---|---|---|---|
| Generative Agents(以下 GA) | https://github.com/joonspk-research/generative_agents | main @ `fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4`(2023-08-11) | 2026-09-27 | `reverie/backend_server/` の `persona/cognitive_modules/plan.py`(全 1053 行)・`execute.py`(全)・`perceive.py`(全)・`reflect.py`(引き金部)・`converse.py`(agent_chat_v2 の往復上限)・`persona/memory_structures/scratch.py`(act 欄・act_check_finished)・`persona/persona.py`(move)・`reverie.py`(主ループ)・`maze.py`(関数一覧)・`persona/prompt_template/run_gpt_prompt.py`(task_decomp・action_sector・act_obj_desc 部)・テンプレ 4 本(`v2/task_decomp_v3.txt`・`v2/decide_to_react_v1.txt`・`v2/generate_hourly_schedule_v2.txt`・`v3_ChatGPT/generate_obj_event_v1.txt`)・`environment/frontend_server/storage/base_the_ville_{isabella_maria_klaus,n25}/reverie/meta.json`・`README.md`(該当行) = 17 |
| AI Town | https://github.com/a16z-infra/ai-town | main @ `8e05997f2409275669c8344b84a51692e83f3f33`(2026-08-26) | 2026-09-27 | `convex/constants.ts`(全)・`convex/aiTown/agent.ts`(全)・`agentOperations.ts`(全)・`agentInputs.ts`(1–140)・`inputs.ts`(全)・`player.ts`(activity/pathfinding 部)・`movement.ts`(movePlayer 冒頭)・`conversation.ts`(状態遷移部)・`game.ts`(tick 部)・`agentDescription.ts`・`convex/agent/conversation.ts`(プロンプト部)・`convex/agent/memory.ts`(記憶・内省部)・`convex/init.ts`(体数)・`data/characters.ts`(plan 欄)・`src/components/Player.tsx`・`PlayerDetails.tsx`・`Character.tsx`(表示部)・`ARCHITECTURE.md`(該当節)・`README.md`(該当行) = 19 |
| Humanoid Agents | https://github.com/HumanoidAgents/HumanoidAgents | main @ `9718c674ea47bad9e7697611b1d9d557d3c2d8b7`(2024-10-14) | 2026-09-27 | `humanoidagents/humanoid_agent.py`(全 438 行)・`generative_agent.py`(計画・行動・場所部)・`run_simulation.py`(全)・`run_simulation_server.py`(時刻部の grep)・`utils.py`(会話組)・`customized_humanoid_agent.py`(全)・`location.py`(構造部の grep)・`default_agent_config.json`(全)・`locations/lin_family_map.yaml`(冒頭)・`README.md`(該当行) = 10 |

既存答申との関係: [v2-action-conversation-contract-research.md](v2-action-conversation-contract-research.md) は AI Town を ARCHITECTURE.md から「7 入力」と数えている。コード上の入力口は 13 個(§2 Q1・§7-1)。同答申の GA 所見「接地は LLM に環境木を降ろさせる再帰プロンプト」は本書 §1 Q4 のコードと整合する。

## §1 Generative Agents

### Q1 行動の表現

自由文。行動は `act_description`(文字列)+`act_duration`(分)+`act_address`(`world:sector:arena:object`)+`act_event`(三つ組)+`act_pronunciatio`(絵文字)の組で持つ(`scratch.py:106-127`「`<description> is a string description of the action.`」)。固定語彙は無い。語は LLM が日課→時間割→分解の各段で書く(`plan.py:41-68`・`71-138`・`141-164`)。場所は LLM が**本人の空間記憶にある候補の中から**選ぶ(`run_gpt_prompt.py:615-619`: 候補外なら `output = persona.scratch.living_area.split(":")[1]` に置換)。

### Q2 粒度と持続

持続は LLM が書く。①時間割は 1 時間ごとに LLM 1 呼(`plan.py:108-109`)、同じ文が続く時間を束ねて分に直す(`plan.py:135-136`「`n_m1_hourly_compressed += [[task, duration*60]]`」)。②60 分以上の塊は LLM が分解(`task_decomp_v3.txt:14`「`Describe subtasks in 5 min increments.`」、例示は 5〜30 分=同 `26-34`)。後処理で 5 分の倍数に切り下げ(`run_gpt_prompt.py:391`「`i_duration -= (i_duration % 5)`」)、合計を元の塊に合わせる(同 `397-404`・`473`)。③睡眠は分解しない(`plan.py:545-552`)。完了条件は**時刻切れのみ**(`scratch.py:554-557`「`end_time = (x + datetime.timedelta(minutes=self.act_duration))`」→ 現在時刻と一致で True)。到着は完了条件ではない。会話は本文の長さから持続を計算(`plan.py:290`「`convo_length = math.ceil(int(len(all_utt)/8) / 30)`」)し、`chatting_end_time` で終わる(`scratch.py:547-548`)。

### Q3 頻度と引き金

固定ステップ(1 step=ゲーム内 10 秒。`README.md:65`「`One game step represents 10 seconds in the game.`」、`meta.json:5`「`"sec_per_step": 10,`」)。毎 step 全員が `perceive→retrieve→plan→reflect→execute`(`persona.py:220-231`)。新しい行動の LLM 決定は**行動が切れた時だけ**(`plan.py:958-959`「`if persona.scratch.act_check_finished(): `」→「`_determine_action(persona, maze)`」)。反応は新規に知覚した他者の事象に対し `_should_react` が会話/待機/無反応を LLM で判定(`plan.py:699-803`・`970-989`)。1 行動あたり LLM は最大 8 呼(sector・arena・object・絵文字・事象三つ組・物の状態文・その絵文字・その三つ組=`plan.py:626-638`)+分解 1 呼+知覚した新規事象ごとの重要度 1 呼(`perceive.py:148-150`)。1 体 1 日の呼数の定数はコードに無い(§6-1)。内省は重要度の残量が 0 以下の時(`reflect.py:152-154`・`scratch.py:61`「`self.importance_trigger_max = 150`」)。

### Q4 効果の解決

位置はエンジン: `execute.py` が `maze.address_tiles[plan]` の候補タイルへ経路探索し、1 step に 1 タイル進める(`execute.py:85-94`・`150-153`)。物の状態は **LLM が書いた文を貼るだけ**(`generate_obj_event_v1.txt:11`「`Task: We want to understand the state of an object that is being used by someone.`」、例 `run_gpt_prompt.py:1010`「`example_output = "being fixed"`」)で、到着後にタイルの事象として置き(`reverie.py:352-365`)、次の周期で idle へ戻す(`reverie.py:330-332`)。所持・在庫・占有・保存則は無い。前提検査は無く、失敗は安全値への置換(sector=自宅=`run_gpt_prompt.py:617-619`、分解失敗=`fs = ["asleep"]`=同 `425-427`、物の状態=`fs = f"{act_game_object} is idle"`=同 `986-988`)。

### Q5 待つ・何もしない・歩き回る

「待つ」は反応から生成される自由文の行動: `_wait_react`(`plan.py:907-928`)が `inserted_act = f'waiting to start {…}'`・`act_address = f"<waiting> {…} {…}"`・`act_pronunciatio = "⌛"` を作る。持続は**待つ相手の行為の終了時刻から計算**(`plan.py:774-777` で相手の `act_start_time + act_duration - 1` 分を `wait_until` とし、`912` で「終了時刻−現在+1」分)。`<waiting>` はその場に留まる(`execute.py:72-77`)。LLM に出す選択肢は 2 つ(`decide_to_react_v1.txt:36-37`「`Option 1: Wait on !<INPUT 5>! until !<INPUT 6>! is done !<INPUT 7>!`」「`Option 2: Continue on to !<INPUT 8>! now`」)。「何もしない」は行動未設定の体・物が `is idle` と知覚される既定状態(`perceive.py:111-116`)で、反応対象から外される(`plan.py:689-693`「`# Skip idle.`」)。「歩き回る」専用の語は無い。移動は行動の場所へ向かう副作用で、物が無い arena では `<random>` タイルへ行く(`plan.py:221-222`・`execute.py:79-83`)。

### Q6 他者への表示

本人の `act_description` がそのまま事象としてタイルに載り(`reverie.py:349-350`「`self.maze.add_event_from_tile(persona.scratch`」「`.get_curr_event_and_desc(), new_tile)`」)、他者は視野 4 タイル・同じ arena・近い 3 件を知覚して `f"{s.split(':')[-1]} is {desc}"` という文にし記憶へ入れる(`perceive.py:82-103`・`116`・`175-177`、`scratch.py:19`・`21` の vision_r=4・att_bandwidth=3)。**自由文の活動を他者が読む**。画面向けには `act_description @ act_address` と絵文字を返す(`execute.py:155-158`)。

### Q7 計画の階層

日課(LLM。2 日目以降の指示は `plan.py:452`「`Follow this format (the list should have 4~6 items but no more):`」)→ 1 時間ごとの時間割(LLM)→ 60 分以上の塊を 5 分刻みに分解(LLM。現在と 60 分先の約 2 時間分を先回り=`plan.py:554-592`)→ 行動ごとに場所・物を LLM が選ぶ → 経路と移動はエンジン(`execute.py`)。改訂の引き金は①新しい日(`revise_identity`=`plan.py:408-458`)②反応(会話・待機)で、`_create_react` が現在の時間帯の分解を LLM で作り直す(`plan.py:842-844`「`p.scratch.f_daily_schedule[start_index:end_index] = ret`」)。

### Q8 規模・費用

同梱の基底シミュは 3 体と 25 体(`base_the_ville_isabella_maria_klaus/reverie/meta.json:7-11`・`base_the_ville_n25/reverie/meta.json:7-33`)。実時間比・費用の定数はコードに無い。README は定性的のみ(`README.md:85`「`Running these simulations, at least as of early 2023, could be somewhat costly, especially when there are many agents in the environment.`」)。

## §2 AI Town

### Q1 行動の表現

二層。(a) エンジン入力(`inputHandler`・型検査つき)が 13 個: player 3(`join`・`leave`・`moveTo`=`player.ts:267-291`)、conversation 6(`startConversation`・`startTyping`・`finishSendingMessage`・`acceptInvite`・`rejectInvite`・`leaveConversation`=`conversation.ts:253-375`)、agent 4(`finishRememberConversation`・`finishDoSomething`・`agentFinishSendingMessage`・`createAgent`=`agentInputs.ts:13-119`)。(b) **activity** = `description: v.string()`・`emoji: v.optional(v.string())`・`until: v.number()`(`player.ts:38-42`)。activity の語は人手の固定 3 件(`constants.ts:67-71`: `'reading a book'`・`'daydreaming'`・`'gardening'`)で、**LLM ではなく乱数で選ぶ**(`agentOperations.ts:128-129`「`// TODO: have LLM choose the activity & emoji`」「`const activity = ACTIVITIES[Math.floor(Math.random() * ACTIVITIES.length)];`」)。LLM が書くのは会話文と記憶の要約・重要度・内省だけ(`agent/conversation.ts:65-68`・`agent/memory.ts:61-69`・`339-343`)。

### Q2 粒度と持続

activity の持続は定数(`constants.ts:68-70` 各 `duration: 60_000`=実時間 60 秒)で、`until: Date.now() + activity.duration`(`agentOperations.ts:140`)。完了条件は時刻(`agent.ts:70`「`const doingActivity = player.activity && player.activity.until > now;`」)と中断(会話か移動があると `player.activity!.until = now;`=`agent.ts:71-73`)。移動の完了は到着か 60 秒のタイムアウト(`player.ts:97-106`・`constants.ts:11` `PATHFINDING_TIMEOUT = 60 * 1000`)。会話は 10 分超か 8 通超で退出(`constants.ts:41`・`45`、`agent.ts:192-193`)。

### Q3 頻度と引き金

エンジンは 16 ms tick・1 秒 step(`game.ts:47-48`、`ARCHITECTURE.md:149`「`AI town runs steps at only 1 time per second.`」)。`Agent.tick` は規則で分岐し、LLM 等を要する時だけ非同期の operation を起動、1 体 1 件まで(`agent.ts:57-64`・`238-257`、`ARCHITECTURE.md:248-249`「`This is to ensure an agent only is trying to do one thing at a time.`」)。「何かする」の引き金は「会話中でない・activity 中でない・(移動中でない か 最近招待していない)」(`agent.ts:78`)。会話の受諾は確率 0.8 の乱数(`constants.ts:31`・`agent.ts:114`)。冷却定数: 会話後 15 秒(`constants.ts:22`)・activity 後 10 秒(`25`)・同じ相手 60 秒(`28`)。LLM 呼数の定数は無い(§6-5)。

### Q4 効果の解決

世界状態の書き手はエンジンだけ(`ARCHITECTURE.md:243`「Game state should not be written, but rather submitted via \`inputs\`」)。activity は `finishDoSomething` がそのまま `player.activity = args.activity;` と代入するだけ(`agentInputs.ts:71-73`)で、**世界への効果は無い**(表示と「until まで次の決定をしない」ことだけ)。移動は `movePlayer`(整数座標の検査=`movement.ts:32-34`)と経路探索、会話は invited→walkingOver→participating の状態機械(`conversation.ts:66-77`・`147-148`)。所持品・物の状態は無い。

### Q5 待つ・何もしない・歩き回る

「歩き回る」は**LLM なしの乱数の行き先**: 移動しておらず、activity 直後か会話直後なら `wanderDestination(map)`(`agentOperations.ts:114-126`・`172-177`「`// Wander someonewhere at least one tile away from the edge.`」)。「待つ」は語ではなく tick 内の早期 return(相手の入力待ち=`agent.ts:163-166`、気まずさの期限まで待つ=`186-189`・`208-214`、近づいたら止まる=`135-139`)と経路の `waiting` 状態(`player.ts:108-111`)。「何もしない」に近い語は activity の `'daydreaming'`(`constants.ts:69`)。

### Q6 他者への表示

activity は**人間の画面にだけ**出る: 頭上の絵文字(`src/components/Player.tsx:76-80`)と詳細欄の説明文(`PlayerDetails.tsx:217-221`)。他 agent の LLM プロンプトは自分の identity・plan と相手の identity だけを入れ(`agent/conversation.ts:188-202`)、同ファイルに `activity` の語は 0 件(grep)。**他 agent は活動文を読まない**。

### Q7 計画の階層

日・時間の計画は無い。`plan` は人物ごとの 1 文の固定目標で、会話プロンプトにだけ入る(`data/characters.ts:24`「`plan: 'You want to hear all the gossip.',`」、`agent/conversation.ts:196`「`` prompt.push(`Your goals for the conversation: ${agent.plan}`); ``」)。実行層は規則(`ARCHITECTURE.md:26-27`「`Internally, our agents use a combination of simple rule-based systems and talking to an LLM.`」)。計画改訂の仕組みは無い(内省は記憶の追加のみ)。

### Q8 規模・費用

既定の体数は `Descriptions.length`(`init.ts:31`。未コメントの人物は 5 件=`data/characters.ts:21-56`)。人間プレイヤー上限 8(`constants.ts:19`)。時間は実時間 1:1(`Date.now()` で進む)。設計上の限界(`ARCHITECTURE.md:288-289`「`Games that require tens of thousands of objects interacting together may not be a good fit.`」)。費用の定数は無い。

## §3 Humanoid Agents

### Q1 行動の表現

自由文。日計画も 15 分計画も「`hh:mm am/pm: <activity>`」の文字列(`generative_agent.py:137-141`・`866-867`)。各 step の活動は計画文から**LLM を呼ばずに引く**(`generative_agent.py:489-526`)。形は「日計画の項 > 15 分計画の項」(`529-532`「`return f"{action_day_plan} > {action_15m_plan}"`」)。語彙は無く、語は LLM が計画時に書く。

### Q2 粒度と持続

1 step=15 分固定(`run_simulation.py:74-79`: 6 時〜23 時台の `'00', '15', '30', '45'`)。日計画の各項の持続は**LLM が書いた次の項の時刻まで**(`generative_agent.py:703-725`)、15 分計画は 15 分刻みを検査(`759-780`)。完了条件は時刻のみ(計画文の時刻を過ぎたら次の項)。

### Q3 頻度と引き金

固定ステップ・全員が毎 step `get_status_json`(`run_simulation.py:95-96`)。1 step の LLM 呼び出し(`humanoid_agent.py:270-301`): 感情 1(`174-181`)+基本欲求ごとの yes/no 5(`190-203`・`default_agent_config.json:3-7`)+絵文字 1(`generative_agent.py:377-379`)+場所を地名木の階層ごとに 1(最大 5=`412-423`)+15 分計画(日計画の項が変わる時だけ=`@cache`・`857-858`)。欲求か感情に不満があれば毎 step「計画を変えるか」1 呼+書き換え(`humanoid_agent.py:141-156`)。[計算] 72 step/日 × 約 8〜12 呼 ≈ 1 体 1 日 600〜850 呼+会話(未実測)。会話は同じ場所に 2 体以上いれば場所ごとに 1 組を乱数で選ぶ(`utils.py:26-36`「`# only 1 conversation per location, when there are 2 or more agents`」)。

### Q4 効果の解決

基本欲求は **LLM の yes/no 判定+乱数**で ±1(`humanoid_agent.py:196`「`prompt = f"In normal settings, does the activity '{activity}' involve {action}? Please respond with either yes or no."`」、no なら確率 `decline_likelihood_per_time_step` で −1、`205-207` で 0〜10 に丸め)。位置は LLM が地名木を上から選び(`generative_agent.py:416`「`* Prefer to stay in the current area if the activity can be done there.`」)、`fuzzy_match` で候補に合わせ(`456-468`)、`move_agent` が木の上で移す(`438-444`)。5 回で決まらなければ現在地(`432-433`)。所持・物の状態・占有は無い(`location.py` に state/status の語 0 件=grep)。

### Q5 待つ・何もしない・歩き回る

専用の語は無い。計画に無い時刻の既定は `"sleep"`(`generative_agent.py:525-526`「`# if not in plan default is sleep`」「`return "sleep"`」、日計画の範囲外も同様=`709-717`)。待機・徘徊は計画文に書かれればその自由文としてあるだけ。

### Q6 他者への表示

相手の活動文を**直接**プロンプトに入れる(`humanoid_agent.py:399-400`「`{self_name}’s status: {self_activity}`」「`Observation: {self_name} saw {other_name} {other_activity}`」、`414`「`other_activity = other_agent.get_agent_action_retrieval_only(curr_time)`」)。知覚の仕組みは無く、同じ場所に割り当てられた相手の計画文を読む。

### Q7 計画の階層

日計画(LLM・1 日 1 回=`run_simulation.py:86-88`)→ 日計画の各項を 15 分刻みに展開(LLM)→ 各 step はその文を引く。1 時間刻みの再帰分解 `recursively_decompose_plan`(`generative_agent.py:188`)と `get_agent_action_generative` は定義のみで、読んだ 5 ファイルに呼び出しは無い(grep)。改訂の引き金は欲求 <4 か感情≠neutral(`humanoid_agent.py:37-58`・`141-156`)と、日の始めの外部イベント(`run_simulation.py:87`)。

### Q8 規模・費用

例は 2〜3 体(`README.md:47`・`101-107`)。`README.md:54`「`every simulated day with 2 to 3 agents cost around $2-5 and takes 45-60 minutes given the number of API calls.`」

## §4 横断表

| 問い | Generative Agents | AI Town | Humanoid Agents |
|---|---|---|---|
| Q1 行動の表現 | 自由文(description+分+住所+三つ組+絵文字)。語彙なし・LLM が書く。場所は空間記憶の候補から LLM が選ぶ | 二層: エンジン入力 13 個(型検査)+ activity {description, emoji, until}。activity の語は人手 3 件を乱数で選ぶ(TODO: LLM) | 自由文(計画文の行)。語彙なし・LLM が計画時に書く。各 step は計画文を LLM なしで引く |
| Q2 粒度と持続 | 1 時間割→5 分刻みに LLM が分解(例 5〜30 分・睡眠は分解せず)。持続は LLM が書く。完了=時刻切れのみ | activity は定数 60 秒(実時間)。完了=until か会話/移動で中断。移動=到着か 60 秒 | step=15 分固定。日計画の項の持続=LLM が書いた次項の時刻まで。完了=時刻 |
| Q3 頻度と引き金 | step=10 秒。新行動の LLM 決定は行動が切れた時だけ(1 行動 最大 8 呼+分解)。反応は新規知覚した他者事象で LLM 判定 | tick 16 ms・step 1 秒。規則で分岐し LLM は会話と記憶だけ。「何かする」は activity/会話/移動が無い時。冷却定数あり | 毎 15 分全員。1 step 約 8〜12 呼[計算]。不満があれば毎 step 改訂判定 |
| Q4 効果の解決 | 位置=エンジンの経路探索。物の状態=LLM の文を貼るだけ。所持・保存則なし。前提検査なし・失敗は安全値へ置換 | 書き手はエンジンだけ。activity は代入のみで効果なし。移動・会話は状態機械。所持なし | 欲求=LLM の yes/no+乱数で ±1。位置=LLM が地名木を選び木の上で移す。所持・物状態なし |
| Q5 待つ等 | 待つ=反応で生成する自由文行動(`<waiting>`・⌛・持続は相手の終了時刻から計算)。無行動=`is idle`。歩き回る語なし | 歩き回る=乱数の行き先(LLM なし)。待つ=tick 内の早期 return(語なし)。daydreaming が activity の 1 件 | 専用語なし。計画に無い時刻は既定 `sleep` |
| Q6 他者への表示 | 自由文 description をタイル事象に載せ、他者が「X is …」で知覚・記憶 | 人間の画面にだけ絵文字と説明。他 agent の LLM は活動を読まない | 相手の計画文を直接「saw X …」で読む(知覚の仕組みなし) |
| Q7 計画の階層 | 日課→時間割→5 分分解→場所・物(全て LLM)→経路(エンジン)。改訂=新しい日・反応(会話/待機)で時間帯を LLM が作り直す | 日・時間計画なし。plan=固定の目標 1 文(会話にだけ使う)。実行は規則 | 日計画→15 分展開(LLM)→各 step は引くだけ。改訂=欲求/感情の不満・外部イベント |
| Q8 規模・費用 | 同梱 3 体・25 体。費用・実時間比の定数なし(README は定性) | 既定 5 体・人間上限 8。実時間 1:1。「数万オブジェクトは不向き」 | 2〜3 体。1 日 $2-5・45〜60 分(README) |

## §5 v2 の問いに対する事実の整理(推奨ではない)

**二層の扱い**
- AI Town だけがコード上で二層を分けている。世界を変えるのはエンジン入力(移動・会話などの 13 口)で、**activity は `{description, emoji, until}` の自由文+持続であり、世界状態への効果を一切持たない**(`agentInputs.ts:71-73` は代入のみ)。activity の働きは「表示」と「until まで次の決定を止める」の 2 つ。ただし語の選定は乱数・持続は定数 60 秒で、LLM は関与していない(`agentOperations.ts:128`)。
- GA は一層。すべての行動が自由文+持続+住所で、エンジンが解くのは位置(経路)だけ。物の状態は LLM の自由文をタイルに貼るだけで、占有・在庫・保存則の検査は無い。
- Humanoid Agents も一層。すべて自由文で、世界側の数値(基本欲求)は LLM の yes/no 判定で動く。場所だけが地名木という離散構造に写される。
- 3 システムとも、**所持品・在庫・金銭・席の占有といった保存則・占有つきの行為は実装していない**(読んだ範囲に該当する欄・規則が無い)。v2 が契約行で扱っている種類の行為(購入・食事・乗車など)に当たる先例は、この 3 実装には無い。

**持続を誰が決めるか**
- GA: LLM が書く(時間割は 1 時間単位、分解は「5 min increments」で LLM が分を書き、コードが 5 の倍数に丸めて合計を合わせる)。会話はエンジンが文字数から計算し、待つは待つ相手の終了時刻からエンジンが計算する。
- AI Town: 定数(activity 60 秒・会話上限 10 分/8 通・各種冷却)。
- Humanoid: LLM が日計画の時刻を書き、15 分の格子はコードが強制する(形式検査で再生成)。
- 完了条件は 3 つとも**時刻切れが主**。到着で終わるのは AI Town の移動だけ。中断は GA の反応(会話・待機で時間帯を作り直す)と、AI Town の会話/移動の開始(activity の until を now にする)。

**「待つ」はどう表現されるか**
- GA: 反応の結果として生まれる自由文の行動(`waiting to start …`)。住所 `<waiting> x y` でその場に留まり、持続は待つ相手の行為の終了時刻からエンジンが計算する。待っている体には会話を仕掛けない(`plan.py:729-730`)。
- AI Town: 語は無い。規則の中の「何もしない tick」(相手の入力待ち・期限待ち)として暗黙に存在する。
- Humanoid: 語は無い。計画文に書かれればそれが活動になる。

**思考頻度と行動粒度(参考の事実)**
- GA は LLM の新しい決定を「行動が切れた時」だけに絞り、1 回の決定で 5〜数十分(睡眠は数時間)を覆う。そのかわり 1 回の決定で最大 8 呼を使う。
- Humanoid は 15 分ごとに全員が約 8〜12 呼[計算]。
- AI Town は日常行動に LLM を使わず(乱数と規則)、LLM は会話にだけ使う。
- v2 の前提(1 tick=1 分・1 体 1 日 7〜15 呼)に近い呼数で 1 日を覆う先例は、この 3 実装には無い。

## §6 空欄・未確認
1. GA の 1 体 1 日の LLM 呼数(空欄: コードに定数が無く、呼び出し構造しか読めない。実測ログ・論文の値は読んでいない)。
2. GA の実時間比(空欄: LLM の遅延とフロントエンドの同期に依存し、コードに定数が無い)。
3. GA の会話 1 回の呼数(未確認: `converse.py` は往復上限 `for i in range(8):`=130 行目だけ確認し、`generate_one_utterance` 内の呼数は未読)。
4. GA の日課プロンプト本文 `daily_planning_v6.txt` と時間割プロンプトの前置き(未読)。
5. AI Town の既定 LLM モデルと費用(空欄: `convex/util/llm.ts` 未読・README に費用の数値なし)。
6. AI Town の `aiTown/conversation.ts` の招待距離・`movement.ts` の経路探索の全文(状態遷移部と冒頭のみ読んだ)。
7. Humanoid の `reflect()` が走るか(未確認: 読んだ 5 ファイルに呼び出しは無いが、`run_dashboard.py` と `run_simulation_server.py` の全文は未読)。
8. Humanoid の 1 日の呼数は [計算] のみ(実測なし)。README の費用・時間(2〜3 体)が唯一の数値。
9. 3 システムとも論文(arXiv 2304.03442・2310.05418)の本文は読んでいない。本書はコードの事実のみ。

## §7 親への確認依頼
1. **AI Town の入力口の数**: 既存答申 [v2-action-conversation-contract-research.md](v2-action-conversation-contract-research.md) は「7 入力」(ARCHITECTURE.md 由来)。コード @8e05997 では `inputHandler` が 13 個(player 3・conversation 6・agent 4=`inputs.ts:11-17` で合成)。訂正の伝播検査の対象か判断を。
2. **AI Town activity が乱数である点**: `agentOperations.ts:128-129` の TODO と `constants.ts:67-71` の 3 件・`60_000`。main が動いているリポなので、コミット固定で逐語確認を。
3. **GA の完了判定**: `scratch.py:550-557` は開始時刻の秒を切り上げてから `HH:MM:SS` の等値比較をしている。step=10 秒の前提で成り立つという読み([推測])で合っているか。
4. **GA の待機の持続式**: `plan.py:774-777`(相手の開始+持続−1 分)と `912`(終了時刻−現在+1)の逐語。
5. **Humanoid の 15 分計画の再試行条件**: `generative_agent.py:739` は `while not GenerativeAgent.check_plan_format(resulting_plan) and not GenerativeAgent.check_plan_follow_time_start_and_end_and_15m_interval(...) and attempts < max_attempts:` で、2 つの検査が**両方とも失敗している間だけ**再生成する形([推測]: 片方だけ通れば採用される)。逐語と解釈の確認を。
6. **Humanoid の呼数の [計算]**(§3 Q3・§5): 1 step の内訳は `humanoid_agent.py:183-209`・`270-301` と `generative_agent.py:394-436` から数えた。場所の呼数は地名木の深さに依存し 1〜5 の幅。数値として正典化する前に再計算を。
