# R-44 答申: 行動の表現・粒度・効果の解決の実装読み(Concordia / AgentSociety / OASIS)
<!-- hdr:v1 -->
- **分野**: マルチエージェント・シミュレーション基盤(先行実装のコード読み) | **重要度**: P0(サブ判断・親が確定)
- **一次確認**: **B** = サブ実読(コード 57 ファイル・うち部分読み/grep 約 20・空欄 10)・**親検収 済(第272・下の欄)**
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 用途: ユーザーの問い「思考の頻度に対し行動の粒度が小さすぎる・なぜエンジンで行動を規定するのか(待つ等は不要では)」に対し、親の仮説「世界に触れる行為だけ契約・待つ/見る/散歩は活動=自由文+持続」を書く前に、先行 3 実装が行為と活動・持続・効果の解決をどう分けているかを一次(コード)で確かめる。
> 規律: 子サブ未起動・Web は読むだけ・コミットなし・台帳未編集・本書の新規作成のみ。
> 取得手段(申告): GitHub の raw ファイルと API を HTTP GET で標準出力に読んだ(ローカル保存・clone・install なし)。行番号は取得した本文に通し番号を振ったもの=下記コミットの行番号。推奨は書かない(§5 は事実の整理のみ)。

---

> **親検収(2026-09-27・第272・Fable 5.1)**: 結論を変える引用 7 か所を固定コミットの raw で逐語確認(保存なし)。**全一致・訂正なし**。
> - ✓ Concordia `prefabs/game_master/interrupt_driven.py:61-89` `DEFAULT_CALL_TO_ACTION`: 「Describe their action, then end your response with a JSON object specifying attention and schedule.」/ `mask`(`[""]`=everything・`[]`=nothing until timer fires)/ `timer`(`time: "0m", "5m", "30m", "1h"` or `until: "8:00"`・「If both are given, "until" takes priority」)/ 例「I study until the library closes. {"mask": ["study."], "timer": {"until": "21:00", …}}」。
> - ✓ Concordia `components/game_master/interrupt_resolution.py:157-198`: `scheduler.set_mask(entity_name, parsed.mask)`・`expiry = now  # Default: fire immediately.`・`scheduler.set_timer(entity_name, timer)`・`description=f'{entity_name}: {parsed.action_text}'` で**行動文を逐語のまま事象として注入**(LLM 呼び出しなし)。
> - ✓ 同 `interrupt_response_parsing.py:95-100` docstring「If the JSON block is missing, defaults are applied (match-all mask, 1-hour timer, no tags).」=§7-1 の食い違い(docstring 1 時間 / コード fire immediately)は実在。
> - ✓ Concordia `inventory.py:235-240`: 「Note that transactions between named individuals must be balanced. If someone gained something then someone else must have lost it.」=釣り合いは**プロンプトの指示だけ**。
> - ✓ AgentSociety v1 `cityagent/blocks/utils.py:4-24` `TIME_ESTIMATE_PROMPT`: 例示「"Learn programming": {"time": 120} / "Watch a movie": 150 / "Play mobile games": 60 / "Read a book": 90 / "Exercise": 45」・単位 minute。`mobility_block.py:346/380/412` `"consumed_time": 45`・`economy_block.py:239` `"consumed_time": 20`。
> - ✓ AgentSociety `needs_block.py:279-306`: docstring「Applies exponential decay」に対し実装は `hungry_decay = self.alpha_H * time_diff` …(線形)=§7-2 のとおり。
> - ✓ OASIS `oasis/social_platform/typing.py:42` `DO_NOTHING = "do_nothing"`(語数 32/道具 29 はサブ値・親は DO_NOTHING の存在のみ確認)。
> - △ 親未確認: interrupt 型の追加日(2026-05-05)・「演者 1 回の act ≈4 呼」・AgentSociety 2 のルーター。
> - 取得手段(curl を標準出力に読むだけ)は「Web は読むだけ」の範囲内と親が判定(保存・clone・実行なし)。

## §0 読んだもの

| システム | リポ URL | ブランチ/コミット | 読んだ日 | 読んだファイル(主なもの) |
|---|---|---|---|---|
| Concordia | https://github.com/google-deepmind/concordia | main @ `eaea22ed7c01`(2026-09-23) | 2026-09-27 | `concordia/typing/entity.py`・`environment/engines/{sequential,simultaneous,asynchronous}.py`・`components/game_master/{event_resolution,inventory,world_state,next_acting,make_observation,payoff_matrix,interrupt_resolution,interrupt_response_parsing,interrupt_next_acting,interrupt_scheduling,interrupt_time_model,interrupt_make_observation}.py`・`prefabs/game_master/{interrupt_driven,situated_in_time_and_place,generic}.py`・`prefabs/entity/basic.py`・`components/agent/{plan,concat_act_component,question_of_recent_memories}.py`・`agents/entity_agent.py`・`contrib/components/game_master/marketplace.py`・`README.md`(計 26) |
| AgentSociety | https://github.com/tsinghua-fib-lab/agentsociety | main @ `8cc5bb9a9c27`(2026-09-24) | 2026-09-27 | v1 = `packages/agentsociety/agentsociety/` 配下 `cityagent/{societyagent,__init__}.py`・`cityagent/blocks/{plan_block,needs_block,other_block,mobility_block,economy_block,social_block,utils}.py`・`agent/{dispatcher,agent}.py`・`environment/environment.py`・`simulation/simulationengine.py`・`configs/exp.py`/ v2 = `packages/agentsociety2/agentsociety2/` 配下 `env/{router_base,base}.py`・`agent/person.py`・`contrib/env/mobility_space/environment.py`・`society/society.py`/ README 2 本(計 21) |
| OASIS | https://github.com/camel-ai/oasis | main @ `ca8caa52aeec`(2026-09-20) | 2026-09-27 | `oasis/social_platform/{typing,platform}.py`・`oasis/social_agent/{agent,agent_action,agent_environment}.py`・`oasis/environment/env.py`・`oasis/clock/clock.py`・`examples/experiment/twitter_simulation/align_with_real_world/twitter_simulation_large.py`・`examples/experiment/twitter_simulation_1M_agents/twitter_simulation_1m.py`・`README.md`(計 10) |

注: 依頼の手がかり `concordia/clocks/game_clock.py`(`MultiIntervalClock`)はこのコミットでは **HTTP 404**(存在しない)。現行の時間は GM 部品 `GenerativeClock` と `interrupt_time_model` が担う(§1 Q2)。AgentSociety は README が「**AgentSociety 2** (recommended)」(README.md:40)と書き、依頼の `block` 群は v1 側にある。本書は v1 を主に読み、v2 は概観のみ(§2 末尾)。

## §1 Concordia

### Q1 行動の表現
- 行動は `ActionSpec` で型が決まる。`OutputType` の演者用は `FREE`/`CHOICE`/`FLOAT` の 3 種、GM 用は `MAKE_OBSERVATION`・`NEXT_ACTING`・`NEXT_ACTION_SPEC`・`RESOLVE`・`TERMINATE`・`NEXT_GAME_MASTER`・`SKIP_THIS_STEP` の 7 種(`typing/entity.py:26-40, 43-56`)。`FREE` は検査なし(`validate` で `if self.output_type == OutputType.FREE: return`・109-110)。`CHOICE` は `options` 必須・重複禁止(91-95)。
- 既定の行動要求は自由文: 「`What would {name} do next? Give a specific activity. If the selected action has a direct or indirect object then it must be specified explicitly.`」(177-182)。発話は別 spec で `{name} -- "..."` 形式(190-196)。
- **固定語彙は無い**。語を決めるのは演者 LLM(FREE)。CHOICE の選択肢は GM 部品/シナリオ作者が与える(例: `PayoffMatrix` のゲーム)。GM が演者ごとに spec を決める経路もある(`NEXT_ACTION_SPEC`・`next_acting.py:42-44`「In what action spec format should {name} respond?」)。
- 例外として構造化の部品: `contrib/.../marketplace.py` は FREE spec の中で JSON を要求(`{"action":"bid","good":"GOOD_ID","price":...,"qty":...}`・229-241)。interrupt_driven GM は「自由文+末尾 JSON(mask/timer/tags)」(`prefabs/game_master/interrupt_driven.py:61-89`)。

### Q2 粒度と持続
- 標準の GM(`situated_in_time_and_place` 等)では、1 回の行動が何分かを**演者は書かない**。GM の `GenerativeClock` が各 RESOLVE の後に LLM で新しい時刻を書く: 「`Given the context above, and after the event, what is the new time? ... Always convert from simulation steps to the requested format.`」(`world_state.py:533-544`)。既定の時計説明は「`try to make reasonable inferences about the amount of time that would most likely have elapsed between the previous event and the latest event`」(`situated_in_time_and_place.py:32-43`)。=**持続は GM(LLM)が事後に推定**。
- interrupt_driven GM(2026-05-05 のコミット「Add interrupt-driven game-master」で追加)では**演者が持続を書く**: JSON の `timer` に `time`(`"0m"`〜`"1h30m"`)か `until`(`"21:00"`)と `reason`(`interrupt_driven.py:72-78`)。例示は「`I focus on my work in silence.` → `{"mask": [], "timer": {"time": "2h", "reason": "deep focus"}, "tags": ["status.busy"]}`」(83-85)。持続文字列は `parse_duration_seconds` がコードで秒に直す(解釈不能なら 3600 秒・`interrupt_time_model.py:40-57`)。`DatetimeTimeModel` は「No LLM calls」(168-190)。
- 完了条件: 標準 GM は行為の「完了」概念を持たない(各 RESOLVE が 1 事象)。interrupt 型は timer 満了=次の呼び出し(`interrupt_next_acting.py:112-128`)。

### Q3 決定の頻度と引き金
- エンジン 3 種: `Sequential`(1 step に 1 体・GM が次の演者を選ぶ・`sequential.py:67-74`)、`Simultaneous`(選ばれた全員が同時に act し、行動を改行で連結して 1 回 resolve・`simultaneous.py:338, 391-392`)、`Asynchronous`(各演者が独立の observe-act ループ・`asynchronous.py:15-20`)。
- 誰が次に動くか: `NextActing` は LLM の多肢選択「`Whose turn is next?`」(`next_acting.py:117-121`)。コード版に `NextActingAllEntities`(139)・`NextActingInFixedOrder`(257)・`NextActingInRandomOrder`(339)・`NextActingFromSceneSpec`(414)。
- イベント駆動(interrupt 型): 各演者が注意マスク(タグ接頭辞)と timer を毎回書き直す。「`Each entity always has exactly one pending timer.` / `Polling an entity (for any reason) clears its mask AND timer.` / `Non-timer events poll all entities whose mask matches.`」(`interrupt_driven.py:24-29`)。誰も反応しない事象は飛ばして時間だけ進める(`interrupt_next_acting.py:149-152`「No entity cares about this event — skip it」)=「skipping dead air」(`interrupt_driven.py:21-22`)。
- LLM 呼数の目安(コードから数えた範囲・[推測] を含む): 演者 1 回の act = 既定 prefab `basic` で知覚部品 3 つ(`SituationPerception`/`SelfPerception`/`PersonBySituation`・`prefabs/entity/basic.py:131-158`・各 `open_question` 1 回=`question_of_recent_memories.py:147`)+行動 1 回(`concat_act_component.py:113-115`・max_tokens 2200)≈ **4 呼**。GM は step ごとに terminate・make_observation×体数・next_acting・next_action_spec・resolve を問われ(`sequential.py:247-331`)、各問いで LLM を呼ぶかは部品次第(下の Q4 表)。

### Q4 効果の解決(GM 部品ごと)
既定の解決: エンジンが行動文を `[putative_event]` として GM に観測させ、`RESOLVE` を問い、答えを `[event]` として GM 記憶に書く(`sequential.py:163-170`・`DEFAULT_CALL_TO_RESOLVE = 'Because of all that came before, what happens next?'`・41)。

| GM 部品 | LLM が決めること | コードが決めること | 前提検査・失敗 |
|---|---|---|---|
| `EventResolution`(`event_resolution.py:141-247`) | 結果の文(思考連鎖 `determine_success_and_why`=成否の Yes/No「`If the attempted action is easy to accomplish then the attempt should be successful unless there is a specific reason for it to fail.`」604-607・`attempt_to_result`「`What happens as a result of the attempted action? Take into account the location and status of each player.`」679-684)・誰が知ったか(`notify_observers` 時「`Which entities are aware of the event?`」226-231) | 記憶から当番演者の提案を拾う・接頭辞の除去(158-207) | 成否は LLM。失敗なら理由も LLM(613-616) |
| `Inventory`(`inventory.py:179-371`) | 変化の有無・誰が・何個(「`How many {item_type} did {player} gain ... Respond in the format: "number|explanation"`」257-266)。「`transactions between named individuals must be balanced`」は**プロンプト内の指示**(237-239)でコード検査なし | 数値化・失敗時の既定(増えたら +1・減ったら全損・267-283)・整数制約(285-291)・上下限で丸め(293-304) | `never_increase` 時は増加を捨て、GM(LLM)が「増えなかった理由」を作話(323-357) |
| `WorldState`(`world_state.py:100-139`) | 状態変数そのもの(「`what state variables are important to write down now ... "name|value"`」114-131) | `name|value` の分割と dict 格納のみ | なし |
| `Locations`(`world_state.py:309-381`) | 各人の新しい場所(`valid_locations` があれば `SAME` か列挙名のみ・339-348) | 名前の正規化・列挙外は無視(282-307, 371-377) | 列挙外=移動なし扱い |
| `GenerativeClock`(`world_state.py:407-548`) | 新しい時刻(533-544) | step 数の加算(529) | なし |
| `PayoffMatrix`(`payoff_matrix.py:46-47, 165`) | なし(演者の CHOICE のみ) | `action_to_scores`/`scores_to_observation` のコールバック | シナリオ作者のコード |
| `MarketPlace`(contrib・`marketplace.py`) | 演者が JSON の注文を書く | 約定(clearing_house / fixed_prices / 1st・2nd price auction・78-80)・現金検査(「`but you do not have enough cash. Order failed.`」370-379)・現金と在庫の移動(389-393) | コード |
| `InterruptResolution`(`interrupt_resolution.py:86-221`) | **なし**(LLM を呼ばない) | JSON を解析し mask と timer を設定(157-188)・行動文を**逐語のまま**事象として注入(190-198) | 成否判定なし(自由文は裁定されない) |
| `MakeObservation`(`make_observation.py:205-220`) | キューが空なら観測文を生成(「`What does {active_entity_name} observe now?`」) | キューにある事象はそのまま渡す | — |

### Q5 待つ・何もしない・歩き回る
- 専用の語は無い。演者が自由文で書けば GM が解釈する。GM 側には `SKIP_THIS_STEP`(演者に行動させない step・`entity.py:170-174`・`sequential.py:288-311`)。
- interrupt 型では「待つ/集中」は `mask: []`(何にも反応しない)+ timer で表す(`interrupt_driven.py:69-71`「`[]    = pay attention to nothing until timer fires`」)。行動文が空なら事象を注入しない(`interrupt_resolution.py:190-191`・`ParsedResponse.action_text` は「may be empty」`interrupt_response_parsing.py:71`)。

### Q6 他者の観測への表示
- 行動文(自由文)と GM の結果文がそのまま他者の観測になる。`EventResolution` の `notify_observers` は LLM が知覚者を列挙しキューへ積む(`event_resolution.py:219-234`)。`SendEventToRelevantPlayers` は演者ごとに「`Is {active_entity_name} aware of the latest event above?`」を LLM に問う(476-480)。interrupt 型は「`{entity_name}: {action_text}`」を事象としてタグ付き配信し、マスクが合う他者を起こす(`interrupt_resolution.py:192-197`・`interrupt_scheduling.py:385-410`)。=**他者は自由文の活動をそのまま読む**。

### Q7 計画の階層と実行層
- 演者部品 `Plan`: 毎回の pre_act で LLM に計画の時間幅を問い(「`over what time horizon should {agent_name} plan their future actions and behaviors?`」`plan.py:102-105`)、既存計画があれば「`should {agent_name} change their current plan?`」を Yes/No で問い、Yes なら段階計画を書き直す(126-142)。実行層は無く、計画は次の自由文行動の文脈に入るだけ。改訂の引き金は LLM の Yes/No。

### Q8 規模と費用
- 空欄(コード・README に体数・実時間比・費用の定数なし)。並列は `concurrency.run_tasks` による体ごとの並行呼び出し(`sequential.py:279-283`)。

## §2 AgentSociety(v1 = `packages/agentsociety/agentsociety/`)

### Q1 行動の表現
- 二段の固定語彙+自由文。計画の各段は「`intention`(自由文)」と「`type`(4 語: `mobility, social, economy, other`)」(`cityagent/blocks/plan_block.py:72-76`)。実行時は LLM の function calling がブロック名を選ぶ(`agent/dispatcher.py:84-98, 116-146`・選択肢に `no_suitable_block`)。既定ブロック 4 つ=Mobility/Economy/Social/Other(`cityagent/societyagent.py:174-178`)。各ブロックの `actions`: Mobility=`place_selection`/`move`/`mobility_none`(`mobility_block.py:507-511`)・Economy=`work`/`consume`/`economy_none`(`economy_block.py:304-308`)・Social=`find_person`/`message`/`social_none`(`social_block.py:445-449`)・Other=`sleep`/`other`(`other_block.py:186-189`)。語は人手(コード)、選ぶのは LLM。
- 欲求ごとの「指針」選択肢も人手の固定表: `hungry`→Eat at home/outside/at current location・`tired`→Sleep at home・`safe`→Work/Shopping・`social`→Contact with friends・`whatever`→leisure and entertainment/other/stay at home(`plan_block.py:139-145`)。LLM は「`extent the option if necessary`」と拡張を許される(42)。

### Q2 粒度と持続
- 1 計画 = 最大 `max_plan_steps=6` 段(`plan_block.py:120`)。各段の持続(`consumed_time`・分)は**ブロックが返す**: 移動=定数 45(`mobility_block.py:346` 等)・場所選び=5(274)・購入=20(`economy_block.py:239`)・社交=5/10/15(`social_block.py`)・**睡眠/その他/仕事は LLM が分を見積もる**(`TIME_ESTIMATE_PROMPT`「`please estimate the time needed to complete the current action` ... 例 `"Learn programming": {"time": 120}` / `"Watch a movie": 150` / `"Play mobile games": 60` / `"Read a book": 90` / `"Exercise": 45`」`blocks/utils.py:4-24`)。解析失敗時は乱数(睡眠 1〜8 時間・その他 1〜180 分・仕事 1〜3 時間・`other_block.py:103, 155`・`economy_block.py:139`)。ブロック不在時も成功扱いで乱数 1〜100 分(`societyagent.py:697-709`)。
- 完了条件: `time_now >= step_start_time + consumed_time*60` のとき段を完了とし次へ(`societyagent.py:443-462`)。移動中(`status == 2`)は時間に関係なく未完了(432-434)=**到着はシミュレータが決める**。

### Q3 決定の頻度と引き金
- 固定ステップ: 1 step ごとに全エージェントの `run()` を並行実行し、環境を `ticks_per_step` 進める(`simulation/simulationengine.py:1546-1547, 1680`)。既定 `ticks_per_step: int = 300`(`configs/exp.py:99-100`)、シミュレータの 1 tick=1 秒(`environment/environment.py:735` `"interval": 1`・`get_datetime` は秒で日と時刻を計算 354-356)=**5 分ごとに forward**。
- ただし forward は段が未完了なら早期 return(`societyagent.py:399-401`)。欲求の判定・計画生成・段の実行は段の境界でのみ走る(407-418)=**LLM 呼数は持続の終わりに比例**(コードの順序からの読み)。例外: 早期 return の前に `reflect_to_environment` があり、AOI 情報があれば毎 step LLM を呼ぶ(381-387, 396)。
- 割り込み: 計画中でも、より優先度の高い欲求が閾値を割れば計画を打ち切る(優先順 hungry > tired > safe > social・`needs_block.py:411-460`)。閾値と減衰はコードの定数(`alpha_H 0.15 / alpha_D 0.08 / alpha_P 0.05 / alpha_C 0.1`(1 時間あたり)・`T_H 0.2 / T_D 0.2 / T_P 0.2 / T_C 0.3`・138-145)。
- LLM 呼数の目安([推測]・コードから数えた): 計画ごとに 2(指針選択+段計画・`plan_block.py:203, 243`)・段ごとに 2〜4(上位ディスパッチ 1+ブロック内ディスパッチ 1+ブロック内 0〜2)・計画完了時に欲求評価 1(`needs_block.py:501`)+感情更新(cognition 有効時)。

### Q4 効果の解決
- 移動: `MoveBlock` が行き先の種類を LLM に問い(`mobility_block.py:297-306`)、`environment.set_aoi_schedules` → gRPC `person_service.SetSchedule` でシミュレータに経路を渡す(`environment.py:402-471`)。位置の変化は**外部シミュレータ(コード)**。前提: 既に自宅なら `consumed_time: 0` で成功(`mobility_block.py:324-334`)。
- 購入: `ConsumptionBlock` は LLM を使わず、月の消費上限を検査(超過なら `success: False`・`economy_block.py:210-220`)、価格の softmax で各社への需要を割り、`economy_client.calculate_consumption` で約定(221-231)=**コード**。
- 仕事: LLM が時間を見積もり、`work_hour_finish` に加算するだけ(`economy_block.py:108-136`)。
- 睡眠/その他: LLM が時間を見積もり、記憶ストリームに「`I {intention}`」を書くだけ(`other_block.py:80-95, 136-147`)=**世界状態への効果なし**。常に `success: True`。
- 欲求(内部状態): 減衰はコード(線形 `alpha * time_diff`・`needs_block.py:301-309`)、**充足の回復は計画完了後に LLM が新しい値を書く**(EVALUATION_PROMPT・487-516)。

### Q5 待つ・何もしない・歩き回る
- 専用の語・ブロックは無い。「stay at home」は `whatever` 欲求の指針の 1 つ(`plan_block.py:144`)で、実行は Other ブロックが自由文 intention+LLM 見積もり時間で処理(`OtherNoneBlock` の説明「`Handles all kinds of intentions/actions except sleep`」`other_block.py:117`)。`MobilityNoneBlock` は所要 0 分で完了を記録するだけ(`mobility_block.py:467-478`)。移動中は forward が早期 return=待機が既定状態。

### Q6 他者の観測への表示
- 読んだ範囲では「他者がいま何をしているか」を他者へ表示する機構は見当たらない。他者と接するのはメッセージ(`MessageBlock` → `send_message_to_agent`・`social_block.py:400`)と AOI に登録された文(`register_aoi_message`/`sense_aoi`・`environment.py:192-209, 252-264`)。

### Q7 計画の階層と実行層
- 欲求(コードの閾値)→ 指針選択(LLM・計画行動理論の 3 軸で採点・`plan_block.py:11-50`)→ 段計画(LLM・型つき)→ ディスパッチ(LLM function calling)→ ブロック(コード+LLM)→ シミュレータ/経済クライアント(コード)。改訂の引き金=計画の完了/失敗・上位欲求の閾値割れ・介入メッセージ(`react_to_intervention`・`societyagent.py:652-659`)。

### Q8 規模と費用
- 時間: 1 step=300 秒・1 tick=1 秒・開始 8:00(`start_tick = 8*60*60`・`environment.py:46-47`)。体数・実時間比・費用: 空欄(読んだコードと README の行に数値なし・記憶で埋めない)。

### 補: AgentSociety 2(`packages/agentsociety2/`・概観のみ)
- 演者は ReAct ループ(`max_react_turns` 既定 10・`agent/person.py:86`)で、環境へは**自然文で問い合わせる**: `router.ask(ctx, "查询天气信息", readonly=True)`(`env/router_base.py:20-28`)。ルーターは ReAct/計画実行/コード生成などの LLM(1-18)で、環境部品の `@tool(readonly=False)` 関数(状態変更)を呼ぶ(`env/base.py:11-14`)。例: `move_to` はコードで「`already moving`」なら失敗を返す(`contrib/env/mobility_space/environment.py:735-757`)。1 step の秒数は引数(例 `run(num_steps=100, tick=3600)`・`society/society.py:132, 768-779`)。

## §3 OASIS

### Q1 行動の表現
- **固定語彙**。`ActionType` は 32 語(`social_platform/typing.py:17-49`)、うち演者の道具(function calling の tool)は 29 語(`social_agent/agent_action.py:28-61`。`EXIT`・`SIGNUP`・`UPDATE_REC_TABLE` は道具にない)。既定の組は Twitter 6 語(`CREATE_POST, LIKE_POST, REPOST, FOLLOW, DO_NOTHING, QUOTE_POST`)・Reddit 13 語(51-78)。語は人手、選ぶのは LLM(CAMEL の tool calling・`agent.py:105-111`)。引数(投稿本文など)は LLM の自由文。README は「`Agents can perform **23 actions**`」(README.md:74)と書く(コードの数と不一致・§7)。

### Q2 粒度と持続
- 行動は瞬間(持続の概念なし)。1 回の活性化で LLM 応答の tool call を実行し、最初の tool call の処理で return(`agent.py:139-152`)。時間刻みは例示スクリプト側: 「`# 0.05 * timestep here means 3 minutes / timestep`」(`twitter_simulation_large.py:154-155`)。Reddit 型の時刻は実時間 × k(`Clock.time_transfer`・既定 `Clock(60)`・`clock.py:25-30`・`platform.py:76-77`)、Twitter 型は整数 step(`env.py:197-198`)。

### Q3 決定の頻度と引き金
- 固定ステップ+確率活性化。ライブラリ本体の `OasisEnv.step(actions)` は呼び手が渡した `LLMAction`/`ManualAction` の辞書を実行するだけ(`environment/env.py:136-198`)。活性化は例示スクリプトで、各体の `active_threshold`(24 時間の配列)を時刻で引き、`random.random() < threshold` なら LLM 行動(`twitter_simulation_large.py:157-163`)。100 万体例では id < 197 の体は固定 0.1(`twitter_simulation_1m.py:153-155`)。反応・割り込みの機構は無い。LLM 呼数=活性化 1 回につき 1 回の応答(CAMEL 内部の反復は空欄)。

### Q4 効果の解決
- **全てプラットフォーム(コード・SQLite)**。演者の tool は channel 経由でプラットフォームへ `(agent_id, message, type)` を送り(`agent_action.py:63-67`)、プラットフォームは `getattr(self, action.value)` で同名関数を呼ぶ(`platform.py:147-171`)。前提検査はコード: 例 `like_post` は既存の like があれば「`Like record already exists.`」で失敗(`platform.py:574-584`)。`purchase_product` は商品の存在だけ検査し `sales` を加算(買い手の所持金は扱わない・220-254)。結果の dict が tool の戻り値として演者へ返る。

### Q5 待つ・何もしない
- `DO_NOTHING` が**明示の語**。プラットフォームは trace に記録して `{"success": True}` を返すだけ(`platform.py:1332-1346`)。非活性化(確率で呼ばれない)が既定の「何もしない」。歩き回るは対象外(SNS)。

### Q6 他者の観測への表示
- 他者は `refresh` で推薦系が選んだ投稿の JSON を読む(「`After refreshing, you see some posts $posts`」`agent_environment.py:37-38, 58-66`)とグループのメッセージ(40-48)。「誰がいま何をしているか」の表示は無い。全行動(do_nothing を含む)は trace 表に記録=分析用(`platform.py:1342`)。

### Q7 計画の階層
- 空欄に近い: 本体に計画・階層は無い(活性化ごとに観測→tool 選択 1 回)。

### Q8 規模と費用
- README「`supports simulations of up to ***one million agents***`」(README.md:66)・100 万体の例示スクリプトあり。並行 LLM 要求の上限 `semaphore: int = 128`(`env.py:55`)。トークン実測の参考値: 100 体 × 活性化確率 1 × 1 step で入力 335,600・出力 16,750(QWEN_TURBO・README.md:236-243)=**1 活性化あたり入力 約 3,356・出力 約 168**(親検算用: 335,600/100・16,750/100)。

## §4 横断表

| 問い | Concordia | AgentSociety(v1) | OASIS |
|---|---|---|---|
| Q1 表現 | 自由文(FREE)が既定。CHOICE/FLOAT は作者が選択肢を与える。固定語彙なし | 自由文 intention+型 4 語+ブロック 4 つ(下位 action 各 2〜3)。LLM が function calling で選ぶ | 固定 29 語(ActionType 32)を LLM が tool calling で選ぶ。引数は自由文 |
| Q2 粒度・持続 | 標準: 演者は持続を書かず GM の LLM 時計が事後推定。interrupt 型: 演者が timer(分/時刻)を書く | 段ごとの分数をブロックが返す(移動 45・購入 20 は定数、睡眠/その他/仕事は LLM 見積もり)。完了=時刻到達かつ移動終了 | 持続なし(瞬間)。例示の 1 step=3 分 |
| Q3 頻度・引き金 | GM が次の演者を選ぶ(LLM か固定順)。interrupt 型は timer 満了とマスク一致の事象で起こす・空白時間は飛ばす | 5 分ごと forward だが段未完了なら早期 return。欲求の閾値割れで計画を割り込み | 各 step で時間帯別確率により活性化。割り込みなし |
| Q4 効果 | 既定は GM の LLM が結果文・所持・位置・状態・時刻を書く。コードは丸め・上下限・正規化。contrib の市場と利得表はコード。interrupt 型は裁定せず逐語注入 | 移動=外部シミュレータ、購入=経済クライアント(コード)。仕事/睡眠/その他は記憶に書くだけ。欲求の回復値は LLM | 全てプラットフォームのコード(SQLite)。前提検査もコード |
| Q5 待つ | 専用語なし(自由文)。GM 側に SKIP_THIS_STEP。interrupt 型は mask [] + timer | 専用語なし。「stay at home」は指針の選択肢、実行は Other(自由文+LLM 時間)。移動中は待機が既定 | DO_NOTHING が明示語(記録のみ)。非活性化が既定 |
| Q6 他者の観測 | 行動の自由文と GM の結果文をそのまま配る(知覚者は LLM かマスクで決める) | 現在の活動の表示なし(メッセージと AOI の文のみ) | 投稿の推薦と group メッセージのみ。活動の表示なし |
| Q7 計画 | Plan 部品が毎回 Yes/No で改訂を判断。実行層なし | 欲求→指針→段計画→ディスパッチ→ブロック→シミュレータ。改訂=完了/失敗/上位欲求/介入 | なし |
| Q8 規模・費用 | 空欄(定数なし) | 1 step=300 秒・1 tick=1 秒。体数・費用は空欄 | 最大 100 万体(README)・並行 128・1 活性化 約 3.4k 入力/168 出力トークン |

## §5 v2 の問いに対する事実の整理(推奨ではない)

1. **行為と活動を分けているか**
   - Concordia 標準 GM: 分けない。全行動が自由文で、GM(LLM)が全部を裁定する。構造化+コード解決は「作者が特定の場面だけ部品を足す」形(市場の JSON 注文・利得表の CHOICE)。
   - Concordia interrupt 型: 全行動を「自由文+持続(timer)+注意(mask)」で表し、**裁定も世界状態の更新もしない**(行動文を逐語で事象にするだけ)。=全行動を「活動」として扱う実装が 2026-05 に追加されている。
   - AgentSociety v1: ブロック単位で分かれている。移動と購入はシミュレータ/経済クライアント(コード)が効果を書き、睡眠・その他・仕事は「自由文 intention+LLM が見積もる分数」で世界状態に触れない(記憶に書くだけ)。
   - OASIS: 分けない(全行動が固定語彙でコードが効果を書く)。持続の概念なし。
2. **効果をコードと LLM のどちらが書くか**: Concordia 既定=LLM(所持・位置・時刻・状態変数まで)でコードは丸めと検証のみ/AgentSociety=位置と金銭はコード・欲求の回復値は LLM/OASIS=全てコード。保存(収支の釣り合い)をコードで強制している箇所は Concordia contrib の市場(現金検査と移動)と AgentSociety の経済クライアントのみ。Concordia の `Inventory` は釣り合いをプロンプトで指示するだけ(コード検査なし)。
3. **持続を誰が書くか**: Concordia 標準=GM の LLM が事後推定/Concordia interrupt=演者の LLM が事前に書く(`30m`・`until 21:00`)/AgentSociety=ブロック(定数か、ブロック内の別の LLM 呼び出し。見積もりプロンプトに具体的な分数の例示 120/150/60/90/45 がある)/OASIS=なし。
4. **待つの表現**: 専用語を持つのは OASIS(`DO_NOTHING`)だけ。Concordia interrupt 型は「注意なし+timer」、AgentSociety は Other ブロックの自由文+時間、または移動中の既定状態。
5. **決定の頻度と持続の関係**: Concordia interrupt 型と AgentSociety は、LLM を次に呼ぶ時点を「持続の終わり」に置く(timer 満了/段の完了時刻)。OASIS は時刻別確率で呼ぶ。

## §6 空欄・未確認
1. Concordia `MultiIntervalClock`: このコミットに `concordia/clocks/` が無い(404)。いつ消えたか・旧版の major/minor step の中身は未読。
2. Concordia の規模・費用の定数: コードと README に無い。
3. Concordia の 1 step あたり正確な LLM 呼数: GM 部品の組み合わせ次第。§1 Q3 の「≈4 呼/演者」は既定 prefab からの [推測]。
4. AgentSociety `cognition_block.py`(感情・思考の更新)は未読。
5. AgentSociety の体数・実時間比・費用: 読んだ範囲に数値なし(論文値は記憶で書かない)。
6. AgentSociety `social_block.py` は grep のみ(本文未読)。
7. AgentSociety の外部シミュレータ(Go バイナリ)内の移動速度・経路計算は未読。
8. AgentSociety 2 のルーター実装(ReAct/CodeGen の中身)・既定 tick は未読。
9. OASIS: CAMEL `ChatAgent.astep` 内の tool 反復回数・`max_iteration` の効き(`agent.py:69, 112` で保存のみ確認)は未読。
10. OASIS: 依頼の手がかり `activate_agents` という関数名は本体・例示とも見当たらず(活性化は例示スクリプト内のループ)。

## §7 親への確認依頼
1. Concordia interrupt 型の既定 timer: `interrupt_response_parsing.py:97-100` の docstring は「`defaults are applied (match-all mask, 1-hour timer, no tags)`」だが、`interrupt_resolution.py:162` は timer 未指定時 `expiry = now  # Default: fire immediately.`。どちらが実挙動かの確認(parse_duration_seconds の 3600 秒既定は「解釈不能な文字列」の場合のみ)。
2. AgentSociety `needs_block.py:283` の docstring「`Applies exponential decay`」に対し、コードは線形(301-309)。
3. OASIS README の「23 actions」(README.md:74)とコードの 32 語/29 道具の不一致。
4. Concordia interrupt 型の追加日(2026-05-05・コミットメッセージ「Add interrupt-driven game-master」)は API の履歴で確認したもの。親の再確認を依頼。
5. AgentSociety v1 の `reflect_to_environment` が段未完了でも毎 step LLM を呼び得る点(`societyagent.py:395-401`)は、§2 Q3 の「LLM 呼数は持続の終わりに比例」の例外。AOI 文が空なら呼ばない(381-382)ことの確認。
6. 逐語引用のうち、表中で「…」で省いた箇所(`event_resolution.py:604-607`・`world_state.py:114-131`・`inventory.py:257-266`)は原文の連結文字列を 1 文に直したもの。改行位置は原文と異なる。
