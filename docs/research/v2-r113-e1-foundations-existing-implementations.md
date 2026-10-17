# R-113 答申: E1 第 1 期の土台 8 つ(1-1〜1-9・1-8b)の既存実装の比較表

<!-- hdr:v1 | 等級: B | 作成: 2026-10-13 | 範囲: リサーチの指示書 10-06 E 群 E1・E3 の続き。土台の口の約束(v2-foundation-contracts-2026-10-13)の 9 軸ごとに、既存の実装がどう作っているかをコードで読んだ -->
- **分野**: ABM方法論 #21 / ソフトウェア工学 #29 / 計算機科学(並列・決定論) #28 / ゲームエンジン工学・CG #30 / 自然言語処理・機械学習 #27 | **重要度**: 中(第 1 期の発注の比較表=各段の実装役に渡す)
- **一次確認**: **B**(親検収 2026-10-13・第333=§15 の 5 件のうち 4 件をピン留めの commit の raw で実読して一致: Concordia `interactive_document.py` L67 の種なし `default_rng()` と L330-336 の `permutation`/`original_indices[idx]`・AI Town `schema.ts` L6-31 の `conversationId`/`playerIds`/`importance`/`lastAccess`・TigerBeetle `account.md` の「Accounts are immutable… balance fields, which are modified by transfers」と posted の合計の等式・ActivitySim `random.py` L65 の式と L106-109 の実装。FLAME GPU 2 の LICENSE.md が AGPL-3.0 であることも確認。AgentSociety v1 の介入 2 種(#4)は未確認)。サブの自己評価は ○ 本文やコードを読んだ 34・△ 抄録や検索の要約だけ 5・× 読めなかった 1(計 40。§1 の表)
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-13・リサーチ役サブ(Opus 5.5)。子サブは起動していない。Web は読むだけ。GitHub のコードは、`git ls-remote` で取った HEAD のコミットに固定し、raw.githubusercontent.com の本文を標準出力で読んだ(clone・install・保存なし)。行番号は取得した本文に振った通し番号。木の一覧とライセンスの種別は GitHub の API で見た。Forbus & Wright の PDF は、取得ツール(WebFetch)が自動で残した一時の写しから pymupdf で本文を抽出して読んだ(リポの `data/` には何も置いていない)。コミットなし・台帳/設計書/src は未編集。
> 既存答申との関係(重ねない): 行動の表現と効果の解決 = [R-43](v2-r43-code-reading-ga-aitown-humanoid.md)(GA・AI Town・Humanoid)・[R-44](v2-r44-code-reading-concordia-agentsociety-oasis.md)(Concordia・AgentSociety・OASIS)/ 出来事の記録の形式(MATSim events・SUMO・OTel・CloudEvents・イベントソーシング・MCAP)= [R-72](v2-r72-event-log-formats.md) §3・§4 / 時間刻みと事象駆動・先行の刻み幅 = [R-73](v2-r73-time-model-des.md) §3 / 共通乱数とカウンタ型の乱数(v2 の Philox)= [R-71](v2-r71-stochastic-comparison-statistics.md) §1-3・§1-4 / 世界の書き換え・causationId・Redux・abcEconomics・AI Economist・Hohfeld = [R-105](v2-r105-world-mutation-mechanisms-precedents.md) / 規則の表(OpenFisca・Catala・e-Gov)と regimentation・enforcement = [R-106](v2-r106-rights-institutions-tax-credit.md) §5 / 選択肢の形の偏り・「その他」= [R-108](v2-r108-option-format-bias-and-llm-persona-drift.md) §1-5・§3 / 記憶の器の先行(GA の `filling`・Concordia の観測の列)= [R-68](v2-r68-memory-rework-anchors.md) §7 / 想起の式 = [R-87](v2-r87-recall-relationship-decay-copresence.md) / 道具の先行(SNS・メッセージ)= [R-85](v2-r85-communication-tools.md) §4 / 判断モデルの位置の偏り = [R-94](v2-r94-judgment-model-candidates-update.md) 結論 5・古典と (G) を物差しに残す = [R-83](v2-r83-jev-type-decision-models.md) 結論 5。本書は、これらに無い**コードの場所と土台ごとの比べ**だけを足す。
> 対象の決定: [口の約束](../design/v2-foundation-contracts-2026-10-13.md)(確定・第333)・[指示書 10-12](../design/v2-wallbounce-decisions-2026-10-12.md) §0-3・§4-2 TM・§4-4 CT・§4-5 CP・§4-6 MR・§4-7 DM・[回答 10-13b](../design/v2-answers-2026-10-13b.md)。**決定項は書き換えない。** §13 は親が判断する材料で、未決。
> ライセンスの扱い: GPL・AGPL・LGPL・EPL のコードは仕組みを書くだけで写さない。Apache-2.0・MIT・BSD は「出典を付けて使える」と書く(使う前にファイルの頭書きを親が確かめる)。ゲームの公式文書(UE・Unity)はコードではないので、形を参考にするだけ。

## §0 要旨(結論を先に)

1. **1-1 時計**: 整数の時刻を正にし、実数や文は「見せ方」だけにする形は、SUMO(`SUMOTime` はミリ秒の `long long`・換算のマクロを 1 つのヘッダに集約)、Bevy(`Duration` が正で f32/f64 は派生)、Concordia の `GenerativeTimeModel`(整数の秒・LLM は書式だけ)にある。待ち行列の同時刻の順は、Mesa(時刻→優先度→通し番号)と Concordia(時刻→tag→出どころ→文)が全順序で決まる。SUMO と MASON は挿入順を保証しない(MASON は同順を乱数で混ぜるのを既定にしている)。乱数の種を「行と段の名」から作る先例は ActivitySim。v2 の 1-1(ns の整数・定数の集約・`tick` の語を別名で段階的に消す)は、どの先例とも矛盾しない。
2. **1-3 出来事の記録**: 「原因は 3 種だけ」と「実験の口をコードで 1 か所に強制」を両方持つ実装は見つからなかった。近いのは、外からの入力を番号つきの 1 本の表に通す AI Town の `inputs`、介入を設定の型で列挙する AgentSociety v1 の `WorkflowType`、外から入れた出来事に `__external__` の印を付ける Concordia の割り込みの待ち行列。どれも強制はしていない。AgentSociety v1 は、エージェントの状態の直接の書き換え(`UPDATE_STATE_INTERVENE`)と任意の関数(`FUNCTION`)も介入として許している。
3. **1-4 規則の表とつなぎの台帳**: 規則の表は R-106 §5 で済んでいる。つなぎ(expedient)を「外す段」つきの行で持つ台帳は、コードの先例が無かった。近いのは文書の型(TRACE・Grimm ほか 2014)と、既定と違う設定だけを書き出す MATSim の `config_reduced.xml`。
4. **1-5 権利台帳**: 権利を「誰が・何に・いつからいつまで・相手・原因」の行で持つ LLM 社会シミュは見つからなかった。AgentSociety は会社の属性に従業員の一覧を持つだけ。「止めずに記録し、後で取り締まる」はゲームの Dwarf Fortress の司法(目撃・通報・事件の表・誤った通報もある)が先例になる。
5. **1-2 知覚の分離**: 構造のある事実を先に作り、文への描き方を分ける形は、UE の AI Perception(`FAIStimulus`)、SOTOPIA(共有の行動を、見る人ごとに文へ直す)、GA(三つ組の出来事)にある。ただし UE は刺激の強さを係数で持ち、GA は知覚と記憶の書き込みが一体になっている。
6. **1-6 記憶の器**: 「共有の記録への目印+一人ずつの注釈と強さ」に最も近いのは AI Town の記憶の行。`data.conversationId` で共有の会話の表を指し、本人の視点の要約・重要度・最後に引いた時刻を持つ。「見せた」の録画に近いのは Concordia の構造化ログ(段・人・部品ごとに中身をハッシュで重複除去)。容量の扱いは、AI Town が実時間で 2 週間を過ぎた記憶を消し、Lyfe Agents が類似度の閾値で重複を忘れる。
7. **1-7 道具の台帳**: 借りられるのは、AgentSociety 2 の `@tool(readonly, kind)` の登録と全呼び出しの記録(trace_id つき)、OASIS の体ごとの `available_actions`、UE の Smart Objects(物がデータを持ち、使う側が論理を持つ)。「知っている/知らない」の欄を持つ実装は見つからなかった。
8. **1-8 候補の口・1-8b 発話の口**: Concordia が最もそろっている。`multiple_choice_question` は候補を乱数で並べ替えて記号を振り、選ばれた記号を元の番号に戻す。`sample_choice` は実 LLM と mock(常に 0・一様乱数・偏りつき)が同じ入口になっている。ただし並べ替えの順を記録の欄に残さず、rng を渡さないと種なしになる。発話は SOTOPIA の `AgentAction(action_type, argument, to)` の `to` が 1-8b の `addressees` に当たる。Project Sid の PIANO は、決めた行動を発話の部品へ流して言行の食い違いを減らす(論文のみ)。
9. **1-9 お金の基本操作**: TigerBeetle(Apache-2.0)が最も近い。残高は transfer でしか変わらず、transfer は 2 つの口の間の不変の記録で、借方の合計と貸方の合計が等しいことが保証される。`linked` で複数の transfer を一体にできる。書き手を 1 つに縛る検査は、import-linter の `protected`(輸入の許可表)と、UE Mass・Bevy の「書く権利の宣言」が先例。輪の溢れは、Linux の ftrace(上書きで失った数と捨てた数を別に数える)と OTel(キューが満ちたら捨て、捨てた数を出す)が先例。

### §0-2 軸ごとに最も借りられる 1 件

| 土台 | 最も借りられる実装 | 根拠のファイル | 借りる中身 | ライセンス |
|---|---|---|---|---|
| 1-1 時計 | SUMO(形)・Bevy(コードも可) | `src/utils/common/SUMOTime.h`・`crates/bevy_time/src/time.rs` | 整数の時刻を正にし、換算を 1 か所の名前つきの定数と関数に閉じる | EPL-2.0(形だけ)・MIT/Apache-2.0 |
| 1-3 出来事の記録 | AI Town | `convex/engine/abstractGame.ts`(`runStep`・`engineInsertInput`) | 外からの変化を 1 本の番号つきの表に通し、入力ごとの戻り値を残す | MIT |
| 1-4 規則の表とつなぎの台帳 | MATSim(形だけ) | `corelisteners/DumpDataAtEndImpl.java`(`dumpConfig`) | 既定と違う設定だけを書き出す manifest の欄 | GPL-2.0 以降(読むだけ) |
| 1-5 権利台帳 | Dwarf Fortress(ゲームの形) | Wiki「Justice」 | 止めずに記録し、世界の中の人が取り締まる | 頁は GFDL・MIT |
| 1-2 知覚の分離 | SOTOPIA | `sotopia/envs/parallel.py`(`_actions_to_natural_language_for_viewer`) | 共有の行動 → 見る人ごとの絞り込み → 文 | MIT |
| 1-6 記憶の器 | AI Town | `convex/agent/schema.ts`(`memoryFields`) | 共有の会話への目印+本人の注釈+強さの材料 | MIT |
| 1-7 道具の台帳 | AgentSociety 2 | `packages/agentsociety2/agentsociety2/env/base.py`(`tool`・`EnvMeta`) | 登録の時に性質を検査する表と、全呼び出しの記録 | Apache-2.0 |
| 1-8 候補の口 | Concordia | `concordia/document/interactive_document.py`(`multiple_choice_question`)・`language_model/no_language_model.py` | 並べ替え → 記号 → 元の番号・実 LLM と mock の同じ入口 | Apache-2.0 |
| 1-8b 発話の口 | SOTOPIA | `sotopia/messages/message_classes.py`(`AgentAction`) | 宛先 `to` つきの構造のある発話と、見る人ごとの届け方 | MIT |
| 1-9 お金の基本操作 | TigerBeetle(文書) | `docs/reference/account.md`・`transfer.md`・`docs/coding/linked-events.md` | 残高は transfer でしか変わらない・transfer は不変・`linked`・2 段階 | Apache-2.0 |

## §1 出典の表

印: **○** 本文かコードを読んだ(取得ツールの要約を通したものは「ツール経由」)/ **△** 抄録・検索の要約だけ / **×** 読めなかった。読んだ日はすべて 2026-10-13。コミットは先頭 12 桁。

| # | 対象 | URL・コミット | 印 | ライセンス(LICENSE を実読) | 使った節 |
|---|---|---|---|---|---|
| 1 | Concordia(DeepMind) | https://github.com/google-deepmind/concordia @ `70aa01cca819` | ○ | Apache-2.0 | §2・§3・§7・§9 |
| 2 | AI Town(a16z) | https://github.com/a16z-infra/ai-town @ `8e05997f2409` | ○ | MIT | §2・§3・§7・§9 |
| 3 | Generative Agents(Park ほか 2023) | https://github.com/joonspk-research/generative_agents @ `fe05a71d3e4e` | ○ | Apache-2.0 | §6・§7 |
| 4 | genagents(Park ほか 2024 の 1,000 人の模擬のコード) | https://github.com/StanfordHCI/genagents @ `96854071ef4c`(旧 joonspk-research/genagents から移転=API の応答で確認) | ○ | MIT | §7 |
| 5 | AgentSociety v1 / AgentSociety 2(清華大学) | https://github.com/tsinghua-fib-lab/agentsociety @ `8cc5bb9a9c27` | ○ | Apache-2.0 | §3・§5・§8・§9・§10 |
| 6 | OASIS(CAMEL) | https://github.com/camel-ai/oasis @ `bc805a19978a` | ○ | Apache-2.0 | §8 |
| 7 | SOTOPIA | https://github.com/sotopia-lab/sotopia @ `a0aaafb440e5` | ○ | MIT | §6・§9 |
| 8 | Mesa | https://github.com/mesa/mesa @ `5451086fe47a` | ○ | Apache-2.0 | §2 |
| 9 | SUMO | https://github.com/eclipse-sumo/sumo @ `d8f6d7b7c0c2` | ○ | EPL-2.0(読むだけ) | §2 |
| 10 | MASON | https://github.com/eclab/mason @ `08c95296de1b` | ○ | Academic Free License 3.0(一部のファイルは別) | §2 |
| 11 | MATSim | https://github.com/matsim-org/matsim-libs @ `04c8d4bda601` | ○ | GPL-2.0 以降(ファイルの頭書き・読むだけ) | §4 |
| 12 | ActivitySim | https://github.com/ActivitySim/activitysim @ `26382c34da7f` | ○ | BSD-3-Clause | §2 |
| 13 | FLAME GPU 2 | https://github.com/FLAMEGPU/FLAMEGPU2 @ `5909ecccf90f` | ○ | **AGPL-3.0**(LICENSE.md・読むだけ) | §10 |
| 14 | JuPedSim | https://github.com/PedestrianDynamics/jupedsim @ `d2c1fedac9d6` | ○(LICENSE だけ) | LGPL-3.0 以降 | §12 |
| 15 | Bevy | https://github.com/bevyengine/bevy @ `12a94e0cd6b1` | ○ | MIT と Apache-2.0 の選択 | §2・§10・§11 |
| 16 | TigerBeetle | https://github.com/tigerbeetle/tigerbeetle @ `6e39a21fc9d1`(docs/reference・docs/coding) | ○ | Apache-2.0 | §10 |
| 17 | import-linter | https://github.com/seddonym/import-linter @ `857ae28bc9cb`(docs/contract_types) | ○ | BSD-2-Clause | §10 |
| 18 | Linux カーネルの ftrace の文書 | https://github.com/torvalds/linux/blob/24a19b953e2a/Documentation/trace/ftrace.rst | ○ | 文書(仕組みの記述だけ使う) | §10 |
| 19 | OpenTelemetry の仕様(trace SDK) | https://github.com/open-telemetry/opentelemetry-specification/blob/bb85bf44e2c0/specification/trace/sdk.md | ○ | Apache-2.0 | §10 |
| 20 | UE `FAIStimulus` の API 文書 | https://dev.epicgames.com/documentation/en-us/unreal-engine/API/Runtime/AIModule/FAIStimulus | ○(ツール経由) | Epic の文書 | §6 |
| 21 | UE AI Perception の文書 | https://dev.epicgames.com/documentation/en-us/unreal-engine/ai-perception-in-unreal-engine | ○(ツール経由) | Epic の文書 | §6 |
| 22 | UE Smart Objects の文書 | https://dev.epicgames.com/documentation/en-us/unreal-engine/smart-objects-in-unreal-engine---overview | ○(ツール経由) | Epic の文書 | §8・§9 |
| 23 | UE Mass の `AddIndirectFragmentRequirement` の API 文書(と検索の要約) | https://dev.epicgames.com/documentation/unreal-engine/API/Runtime/MassEntity/FMassFragmentRequirements/AddIndirectFragmentRequirement | ○(ツール経由) | Epic の文書 | §10・§11 |
| 24 | Unity Entities 1.3 の系の順の文書 | https://docs.unity3d.com/Packages/com.unity.entities@1.3/manual/systems-update-order.html | ○(ツール経由) | Unity の文書 | §11 |
| 25 | Forbus & Wright「Some notes on programming objects in The Sims」(2001-05-31 版) | https://qrg.northwestern.edu/papers/Files/Programming_Objects_in_The_Sims.pdf | ○(本文を抽出) | 不明(講義の資料) | §9 |
| 26 | Dwarf Fortress Wiki「Justice」 | https://dwarffortresswiki.org/index.php/Justice | ○(ツール経由) | GFDL と MIT(頁の脚注) | §5 |
| 27 | Altera.AL 2024 Project Sid(PIANO) arXiv 2411.00114 v1 | https://arxiv.org/abs/2411.00114 | ○(HTML・ツール経由) | CC BY 4.0(コードは無い=R-105 #5) | §9 |
| 28 | Kaiya ほか 2023 Lyfe Agents arXiv 2310.02172 v1 | https://arxiv.org/abs/2310.02172 | ○(HTML・ツール経由) | 不明(コードの所在は書かれていない) | §7 |
| 29 | SocioVerse のリポ | https://github.com/FudanDISC/SocioVerse @ `cd1538e99d17` | ○(木の一覧と LICENSE) | Apache-2.0 | §12 |
| 30 | Zhang ほか 2026 SocioVerse2 arXiv 2609.24911 v1 | https://arxiv.org/abs/2609.24911 | △(抄録・ツール経由) | 不明 | §3・§12 |
| 31 | Xie ほか 2024 AI Metropolis arXiv 2411.03519 | https://arxiv.org/abs/2411.03519 | △(検索の要約) | コードは見つからなかった | §12 |
| 32 | Grimm ほか 2014 TRACE(Ecol. Model. 280:129-139) | https://doi.org/10.1016/j.ecolmodel.2014.01.018 | △(検索の要約・本文は有料) | — | §4 |
| 33 | Kashiyama ほか 2022 Pseudo-PFLOW arXiv 2205.00657 | https://arxiv.org/abs/2205.00657 | △(検索の要約) | 生成のコードの公開は見つからなかった | §12 |
| 34 | NetLogo の辞書(`ask`) | https://docs.netlogo.org/dictionary.html | ○(ツール経由・頁の前半だけ) | — | §9 |
| 35 | NetLogo の辞書(`tick-advance`・`ticks`) | 同上 | ×(取得した本文が途中で切れた) | — | §12 |
| 36 | Simile 社の公開物 | 検索(TechCrunch ほか) | △(検索の要約) | 社のコードは公開されていない | §12 |
| 37 | Humanoid Agents | https://github.com/HumanoidAgents/HumanoidAgents(R-43 と同じ `9718c674ea47`) | ○(ライセンスの種別だけ) | Apache-2.0 | §12 |
| 38 | AgentTorch | R-105 #9 のとおり | ○(既存答申) | AGPL-3.0 | §10 |
| 39 | abcEconomics・AI Economist | R-105 #6・#7 のとおり | ○(既存答申) | Apache-2.0(条件つき)・BSD-3 | §10 |
| 40 | 既存答申 R-43・R-44・R-68・R-71・R-72・R-73・R-83・R-85・R-87・R-94・R-105・R-106・R-108 | docs/research/ | ○(既存答申) | — | 全節 |

## §2 1-1 時計(時刻の型・定数の集約・まとめの幅・事象の待ち行列)

先行の刻み幅(MATSim 1 秒・SUMO 1 秒・GA 10 秒・AgentSociety 300 秒ほか)と、時間刻みと事象駆動の比べは R-73 §1・§3 で済んでいる。MCAP の「u64 ナノ秒」は R-72 §4。本節は「時刻の型と定数の置き場」と「同時刻の順」を足す。

| 実装 | やり方 | コードの場所 | ライセンス | v2 が借りられる部品 | v2 の決定と違う点 |
|---|---|---|---|---|---|
| SUMO | 時刻は `typedef long long int SUMOTime`(ミリ秒)。刻みは `extern SUMOTime DELTA_T`(既定 1000)。日・時・分の定数と、秒⇔刻みの換算(`TS`・`STEPS2TIME`・`TIME2STEPS`・`SPEED2DIST`)を 1 つのヘッダに集める。事象は `MSEventControl` の (Command, 時刻) のヒープで、同時刻は `priority` で並べる。待ち行列は刻みの初め・終わり・挿入の 3 本 | `src/utils/common/SUMOTime.h:33-70`・`SUMOTime.cpp:38`・`src/microsim/MSEventControl.h:50`・`.cpp:49-100`(比較は 98-100)・`MSNet.h:942-946` | EPL-2.0(読むだけ) | 換算を名前つきの関数/定数に閉じる形(1-1 の `time_consts.py`)。待ち行列を「刻みの前・後」で分ける形 | 単位はミリ秒(v2 は ns)。同時刻・同 priority の順は比較に入っていない=挿入順の保証なし〔推測: std のヒープは安定でない〕 |
| Bevy | `Time` は `Duration`(整数の秒+ナノ秒)を正に持ち、f32/f64 の秒は派生の欄。f32 は精度が徐々に落ちると文書に明記し、包む周期(wrap)を持つ。固定刻みは `Time<Fixed>` が `timestep` と `overstep`(余り)を持ち、既定 15,625 µs(64 Hz) | `crates/bevy_time/src/time.rs:34-46`(注意書き)・`194-205`(欄)・`fixed.rs:9-76` | MIT/Apache-2.0 | 「整数が正・実数は見せ方」の分け方。余りを持ち越す固定刻み(TM4 のまとめの幅) | 実時間のゲームの時計で、シムの時刻の決定論は目的でない |
| Concordia(割り込み型の GM) | 時刻の型は `TimeModel` が決める。`DatetimeTimeModel` は datetime、`GenerativeTimeModel` は「紀元からの整数の秒」を持ち、LLM は人に見せる書式(`format_time`)だけを作る(書式はキャッシュ)。待ち行列の `Event` は `frozen=True, order=True` の dataclass で、(時刻・tag・出どころ・文)の全順序 | `concordia/components/game_master/interrupt_time_model.py:83-248`・`interrupt_scheduling.py:42-66`(Event)・`273-288`(`inject_event`=過去の時刻は拒む) | Apache-2.0 | 時刻の値と「時刻の見え方」の分離(TM8 の「時計やスマホを見れば分単位、見なければおおよそ」を描き方の側に置く形)。全順序で決まる待ち行列 | 時刻の単位は秒。同時刻の順に文(description)まで使う=文の書き換えで順が変わる |
| Mesa 3 | `model.time` は float。`Event` は (時刻・優先度・通し番号) の全順序で、通し番号はクラスの `itertools.count()`。`_advance_time(until)` は待ち行列を until まで取り出して実行し、時刻を until に進める。`step()` は時刻 +1 | `mesa/time/events.py:59-157`・`426-591`(EventList)・`mesa/model.py:114`・`159-187`・`341-382` | Apache-2.0 | 同時刻の最後の決め手に通し番号を使う形(挿入順で決まる) | 時刻が float。通し番号がプロセス全体の連番なので、作る順が変わると順も変わる〔推測〕 |
| MASON | `Schedule` は double の時刻・`ordering`(整数)・同順は乱数で混ぜるのが既定。並べ替えを止める口は private にした。理由として「二分ヒープは安定でなく、止めても入れた順にはならない」と書く。double で整数を正確に持てる上限 `MAXIMUM_INTEGER = 9.007199254740992E15` を定数に持つ | `mason/src/main/java/sim/engine/Schedule.java:16-24`・`40-50`・`87-90`・`99-107` | AFL-3.0 | 「同順の扱いを明示する」こと自体。v2 の (刻み, 書き口の順, 連番) と比べる材料 | 同順を乱数で混ぜる(v2 は決定的な全順序) |
| ActivitySim | 乱数の種を「全体の種+流れの名の md5 下位 32 ビット+段の名の同+行の番号」の和の 2^32 剰余で作り、行ごと・段ごとに流れを分ける。「同じ乱数の列を、再実行でも別のシムでも作る」ため。時間帯は `skim_time_periods`(1440 分の窓を 60 分単位の区切りの表) | `activitysim/core/random.py:19-40`(hash32)・`43-71`(説明)・`106-109`(row_seed)・`activitysim/core/test/los/configs_1z/network_los.yaml:6-10` | BSD-3-Clause | 鍵の材料に「段の名と行」を入れる考え方(TM7 (d)「出来事の時刻と中身に結びつける」)。v2 の Philox の鍵(R-71 §1-4)と同じ方向 | 和で混ぜるので種の衝突があり得る(本文が「おそらく足りる」と書く)。v2 の鍵つきカウンタの方が強い〔推測〕 |
| AI Town | 時刻は実時間の ms(`Date.now()`)。1 回の段(step)で 16 ms の刻みを最大 600 回まとめて回し、入力を `received` の時刻で刻みに割り振る | `convex/engine/abstractGame.ts:7-11`・`22-88`・`convex/aiTown/game.ts:47-50`・`convex/constants.ts:8-9` | MIT | 「計算のまとめ」と「刻み」を別の数で持つ形(TM の「まとめ」) | 実時間に追従するので再現できない。`game.ts` の 4 つの数は直書きで、`constants.ts` の `TICK`・`STEP_INTERVAL` と同じ値を別に持つ(1-1 の「直書き 0」の反例) |

## §3 1-3 出来事の記録(5W1H・原因の欄・実験の口・記録と状態の分離)

MATSim events・SUMO の出力・OASIS の trace 表・Concordia の構造化ログに「親や原因の欄が無い」ことは R-72 §3、causationId・PROV・戦闘ログの欄は R-105 §4 で済んでいる。本節は「入口を 1 か所にする作り」と「介入の型」を足す。

| 実装 | やり方 | コードの場所 | ライセンス | v2 が借りられる部品 | v2 の決定と違う点 |
|---|---|---|---|---|---|
| AI Town | 外からの変化(人の参加・移動・会話の開始・発言など。入力口は 13=R-43 §2)は `inputs` の表に 1 行ずつ入る。行は (engineId・通し番号 `number`・名前・引数・`received`)。エンジンは段ごとに番号の順に読み、処理済みの番号を進め、各入力の戻り値(ok/error)を記録する。表の掃除の注に「入力は履歴を再生したいときにしか役に立たない。再生するならスナップショットの表を足すか、入力を消さずに最初から再生する」とある | `convex/engine/abstractGame.ts:22-88`・`133-154`(`engineInsertInput`)・`convex/crons.ts:22-38` | MIT | 入口を 1 本の番号つきの表にする形(CP12 の「実験が世界に入る口は 1 か所」と同じ方向)。入力ごとの戻り値の記録 | 実験の入力とエージェントの入力を区別しない。原因の欄が無い。番号は「直前の行+1」で、同時の挿入の扱いは Convex の取引任せ〔推測〕 |
| AgentSociety v1 | 実験は設定の `workflow` に段を並べ、`run()` が型ごとに分岐する。型は STEP・RUN・INTERVIEW・SURVEY・`ENVIRONMENT_INTERVENE`(全体のプロンプトを変える)・`UPDATE_STATE_INTERVENE`(指定の体の状態を直接書く)・`MESSAGE_INTERVENE`(体にメッセージを送る)・DELETE_AGENT・SAVE_CONTEXT・INTERVENE・FUNCTION(シム全体を引数に任意の関数) | `packages/agentsociety/agentsociety/configs/exp.py:23-61`・`82-121`・`simulation/simulationengine.py:1145-1177`・`1287-1309`・`1721-1825` | Apache-2.0 | 介入を「型の付いた申込書の行」にし、型ごとに必要な欄を検査する形(`WorkflowStepConfig` の検証=CP5-4 の「知らない欄はエラー」) | 心を直接書く型と任意の関数を許す(v2 は「人の心を直接書き換える」をやらない)。読んだ範囲では、書き換えを介入として記録する行は無い(`update` は debug のログだけ) |
| AgentSociety 2 | 環境の道具を呼ぶたびに、関数名・引数・戻り値・例外・時刻(実時間の UTC)と、OTel の `trace_id`・`parent_span_id` を記録の列に足す。再生用に、段ごとの体の状態(`agent_status`)と発話・思考(`agent_dialog`)を表に書く | `packages/agentsociety2/agentsociety2/env/base.py:207-237`・`259-301`・`storage/models.py:27-52` | Apache-2.0 | 呼び出しの記録に親の span を付ける形(CP12 の `llm_call(call_id, …)` に近い) | 時刻が実時間で、シムの時刻ではない。原因の種類の語彙は無い |
| Concordia(割り込み型) | 外から入れる出来事は `Event.source` を `"__external__"` にする(docstring の約束)。`inject_event` は誰でも呼べる | `concordia/components/game_master/interrupt_scheduling.py:42-66`・`273-288` | Apache-2.0 | 出来事に「誰が起こしたか/外から来たか」の欄を必ず持たせる形(1-3 の `origin` と `cause`) | 印は約束だけで、作る場所を縛っていない(v2 は gate の 1 関数に AST と実行時で縛る) |
| Concordia(構造化ログ) | `SimulationLog` は (段・時刻・体の名・部品の名・種類・要約) の行に、長い文字列を sha256 の先頭 16 桁の参照に置き換えた中身を持つ。同じ文は 1 回だけ保存する | `concordia/utils/structured_logging.py:44-93`(ContentStore)・`145-172`・`253-300` | Apache-2.0 | 中身を内容のハッシュで重複除去する形(テープの B0〜B4 の ID と同じ方向・記録の容量) | 原因の欄は無い(R-72 §3 と同じ) |
| SocioVerse2(論文) | 抄録は「介入で反実仮想の枝を分ける」「研究そのものを編集できる状態とし、版を上げる」と書く | arXiv 2609.24911 抄録 | 不明 | (コードを読んでいない) | 介入の口の作りは未確認(§14) |

## §4 1-4 規則の表とつなぎの台帳(出典と版・外す段・manifest)

規則の表の先例(OpenFisca の日付ごとの値と出典・Catala・e-Gov API v2)と、機械が守らせる/人が取り締まるの分け方(regimentation/enforcement)は R-106 §5 で済んでいる。本節はつなぎの台帳と manifest の先例だけを見た。

| 実装 | やり方 | コードの場所 | ライセンス | v2 が借りられる部品 | v2 の決定と違う点 |
|---|---|---|---|---|---|
| MATSim | 出力のたびに、使った設定の全部(`config.xml`)と、既定と違う値だけの設定(`config_reduced.xml`=`ConfigWriter.Verbosity.minimal`)を書き出す。出来事は xml に加えて pb と ndjson の名も既定の出力の表にある | `matsim/src/main/java/org/matsim/core/controler/Controler.java:78-100`・`corelisteners/DumpDataAtEndImpl.java:343-348` | GPL-2.0 以降(読むだけ) | 「既定と違う設定だけ」を manifest に出す形(つなぎと腕の数と中身を一目で見せる計器) | 設定の値を出すだけで、つなぎの印や外す段は無い |
| TRACE(Grimm ほか 2014) | モデルの根拠・設計・試験を、決まった章立ての文書に残す枠組み(「evaludation」=品質と信頼を作る全工程を記録する) | doi 10.1016/j.ecolmodel.2014.01.018(抄録) | — | 仮定の行に「なぜ」と「何で確かめたか」を書く欄(`Bridge.why`・`conf`) | 文書の型で、コードと 1 対 1 で突き合わせる仕組みは無い |
| OpenFisca・Catala・e-Gov | R-106 §5-1 のとおり(OpenFisca は値を日付ごとに持ち出典の URL を付ける YAML・AGPL-3.0=読むだけ/Catala は Apache-2.0) | R-106 #の表 | 同左 | `Rule.source`・`asof`・`Rules.get(id, asof)` の形 | — |

つなぎ(expedient)を「外す段」つきで行に持ち、コードの宣言と台帳を AST で 1 対 1 に突き合わせる先例は、読んだ範囲(§1 の 1〜19)に無かった。v2 の 1-4 の形は自前の構成になる(未リサーチ・expedient の扱い)。

## §5 1-5 権利台帳(行で持つ・権限で止める検査の置き場)

権利の要素(Hohfeld の請求権・権能)と、持っている人と持ち主を分ける EVE の列は R-105 §2・M2・M3、手続きの実際は R-106 §1 で済んでいる。

| 実装 | やり方 | コードの場所 | ライセンス | v2 が借りられる部品 | v2 の決定と違う点 |
|---|---|---|---|---|---|
| AgentSociety v1 | 会社・銀行・政府・統計局を主体として置き、会社の作成時の設定に `employees` の一覧を持つ。お金は `delta_update_*` の `delta_currency` で増減する | `packages/agentsociety/agentsociety/environment/economy/econ_client.py:536-587`(`add_orgs`)・`916-946` | Apache-2.0 | 組織を最初から主体として置く形(雇用の行の相手=`counterparty`) | 雇用は会社の属性の一覧で、期間・出どころ・原因を持たない |
| AgentSociety 2 | `EconomyPerson` に通貨・収入・消費・技能。権利の行は無い | `packages/agentsociety2/agentsociety2/contrib/env/economy_space.py:21-33` | Apache-2.0 | — | 権利の台帳が無い |
| Dwarf Fortress(司法) | 罪は止めず、起きた後に目撃者の通報で事件になる。事件は「開いている・閉じた・迷宮入り」の表で持ち、保安官か衛兵の長が尋問する。誤った通報(恨みのある相手を陥れる)もある。罪の種類に「生産の命令の違反」「輸出の禁止の違反」「盗み」などがある | Wiki「Justice」の頁 | 頁は GFDL と MIT(ゲームのコードは非公開) | 「許可のない行動は止めずに `Event(what="unauthorized_act")` として記録し、取り締まりは世界の中の人がする」形の先例。通報の誤り(知覚と記憶の誤り)も同じ記録から出せる | ゲームの調整が入っている(遊びのための変形は持ち込まない=指示書 10-12 E6) |
| AI Economist・abcEconomics | 持ち物と取り置き(escrow)・契約の原子操作(R-105 §1・§3) | R-105 #6・#7 | BSD-3・Apache-2.0 | 契約を「結ぶ・解く」の操作として持つ形 | 権利の期間と原因の欄は無い |

権利を「誰が・何に・どんな権利・いつからいつまで・相手・出どころ・原因」の行で持つ LLM 社会シミュと古典 ABM は、読んだ範囲に無かった(§14)。

## §6 1-2 知覚の分離(構造のある事実と描画を分ける)

| 実装 | やり方 | コードの場所 | ライセンス | v2 が借りられる部品 | v2 の決定と違う点 |
|---|---|---|---|---|---|
| UE AI Perception | 感覚は視覚・聴覚・接触・被害・チーム・予測の 6 種。知覚の更新は `OnTargetPerceptionUpdated` で、相手 1 人と `FAIStimulus`(年齢・失効の年齢・強さ・刺激の位置・受け手の位置・tag・感じ取れたか)を渡す。視覚の設定は視野の半角・見つける距離・見失う距離・最大の年齢(0 なら忘れない)。物の側は「刺激の源」の部品で、どの感覚に見えるかを登録する | API 文書 `FAIStimulus`・AI Perception の文書 | Epic の文書(形だけ参考) | `Percept` の欄の形(誰が・どこで・いつから・どの感覚で)。物の側が「何の感覚に見えるか」を登録する形。「最大の年齢」で知覚の記録を古くする形 | 強さ(`Strength`)を係数の float で持つ(v2 は係数で持たない=指示書 10-12 §1-6) |
| SOTOPIA | 行動は構造のある `AgentAction`(種類・中身・宛先 `to`)。見る人ごとに、宛先の無い行動は全員に、宛先のある行動は送り手と宛先にだけ見せ、`to_natural_language()` で文にする | `sotopia/messages/message_classes.py:141-169`・`sotopia/envs/parallel.py:53-74` | MIT | 「共有の行動の記録 → 見る人ごとの絞り込み → 文」の 3 段(1-2 の `Percept` → `renderer`) | 空間が無く、絞り込みは宛先だけ |
| Generative Agents | 見える範囲 `vision_r`・注意の本数 `att_bandwidth`・新しさの判定 `retention` で、同じ arena の出来事(主語・述語・目的語・文の四つ組)を近い順に取る。取った出来事はその場で本人の記憶に書く | `reverie/backend_server/persona/cognitive_modules/perceive.py:25-120` | Apache-2.0 | 「見える範囲」と「注意の本数」を別の欄に分ける形 | 知覚と記憶の書き込みが一体(v2 は `Percept` を一時の scratch に置き、記憶は別の器)。四つ組の文は作る時に固定され、描き方を後で選べない |
| Concordia | 観測は GM の LLM が文で書く(列が空のとき)・共有の列は同じ文を各人へ複写(R-68 §7-2) | R-68 §7-2 | Apache-2.0 | — | 構造のある事実の段が無い |

「誰に見られているか(`watched_by`)」「聞こえた会話(`heard_speech`)」の欄を知覚の事実として持つ実装は、読んだ範囲に無かった。UE は「見ている側」の部品が持ち、見られている側には届かない。

## §7 1-6 記憶の器(出来事ログへの目印・強さ・注釈・出どころ・「見せた」の録画)

GA の `filling`(体の中の記憶どうしのポインタ)と、Concordia の記憶が「体ごとの文と埋め込みの表」であることは R-68 §7 で済んでいる。想起の式は R-87。

| 実装 | やり方 | コードの場所 | ライセンス | v2 が借りられる部品 | v2 の決定と違う点 |
|---|---|---|---|---|---|
| AI Town | 記憶の行は (playerId・本人の視点の文・埋め込みの ID・重要度・最後に引いた時刻・`data`)。`data` は 3 種で、会話の記憶は `conversationId` と相手の一覧を持ち、共有の `messages` 表(会話 ID・発言者・本文)を指す。内省は元の記憶の ID の列を持つ。想起は 関連度+重要度+新しさ(`0.99 ** floor(最後に引いてからの時間)`)を正規化して足す。最後に引いた時刻の更新は 5 分に 1 回まで | `convex/agent/schema.ts:6-36`・`convex/schema.ts:14-22`・`convex/agent/memory.ts:12`・`24-76`・`187-228` | MIT | **共有の会話の表への目印+本人の注釈(要約)+強さの材料(重要度・最後に引いた時刻)**の組。v2 の `event_id`+`annotation`+`strength` に最も近い | 要約(注釈)を LLM が書き、重要度も LLM の 1〜10。強さは System 1 の数値ではない。会話以外の出来事への目印は無い |
| AI Town(容量) | 毎日の掃除で、実時間で 2 週間を過ぎた `memories` と `memoryEmbeddings` と `inputs` の行を消す(会話の表は既定では消さない) | `convex/crons.ts:18-38`・`convex/constants.ts:62` | MIT | 共有の記録は残し、個人の記憶の行だけを消す分け方 | 消す基準が実時間の年齢で、心理の忘却ではない |
| genagents(Park ほか 2024) | 記憶の節点は (ID・種類・中身・重要度・作った段・最後に引いた段・`pointer_id`=親の節点)。新しさは「全節点の最後に引いた段の最大」との差で `0.99 ** 差` | `genagents/modules/memory_stream.py:216-230`・`279-288`・`346`・`430-451` | MIT | 内省から元の観察へのポインタ(出どころの欄) | 時刻が段の番号で、実時間の秒ではない(MR1 は秒で持つ) |
| Concordia(構造化ログ) | 段・体・部品ごとに、部品が出した中身(=その呼び出しの文脈に入ったもの)を残す。記憶の一覧を HTML の表示のために添付できる | `concordia/utils/structured_logging.py:145-172`・`253-270` | Apache-2.0 | 「この呼び出しで何を見せたか」を部品ごとに残す形(MR16 の `shown`) | 記憶の行に「見せた」の印は付かない(ログの側だけ) |
| Concordia(記憶の表) | 記憶は文と埋め込みの 2 列。重複は Python の `hash(tuple(...))` で弾き、その集合を状態に保存する | `concordia/associative_memory/basic_associative_memory.py:52`・`99-114`・`56-73` | Apache-2.0 | — | 文字列の `hash()` はプロセスごとに種が変わる(Python の既定)ので、保存した集合を別のプロセスで読むと重複の判定が合わない〔推測・PYTHONHASHSEED の既定の挙動による〕 |
| Lyfe Agents(論文) | 記憶を作業(4〜5 件)・最近・長期の 3 段に分け、最近と長期へ入るときに「忘れる」処理をかける。忘れるのは、新しい記憶との類似度が閾値 θ(0<θ<1)を超える古い記憶(重複とみなす)。長期へ移す前に、埋め込みの類似で塊にして LLM が 1 つにまとめる | arXiv 2310.02172 v1 の本文(HTML) | 不明(コードは見つからない) | 容量を設けず「似たものを畳む」形の参考 | 忘却が人の記憶のデータでなく類似度の閾値(expedient に当たる) |

「人と同じように忘れる」を目標にした器(MR の決定)の直接の先行は、R-68 §7 の結論のとおり見つからない。

## §8 1-7 道具の台帳(登録表・知っている/知らない・体と知覚への影響・中身を書くのは誰か)

LLM 社会シミュの SNS とメッセージの実装と「通話の実装は見つからない」は R-85 §4 で済んでいる。

| 実装 | やり方 | コードの場所 | ライセンス | v2 が借りられる部品 | v2 の決定と違う点 |
|---|---|---|---|---|---|
| AgentSociety 2 | 環境のモジュールのメソッドに `@tool(readonly, kind)` を付け、メタクラス `EnvMeta` が登録表 `_registered_tools` を作る。`kind` は「毎段自動で呼ぶ観察」と「統計」の 2 種で、どちらも読み取り専用でなければ作る時にエラー。呼び出しはすべて記録の列に足す(§3) | `packages/agentsociety2/agentsociety2/env/base.py:11-14`・`80-170`・`335-411` | Apache-2.0 | 登録の時に性質(読むだけか・観察か)を検査する形。全呼び出しの記録(CT の共通の決まり 5「使用は全部、出来事の記録へ」) | 道具は環境の機能で、本人が「知っている/持っている」の区別が無い。中身(本文)を書く者の欄も無い |
| AgentSociety 2 の CodeGenRouter | LLM が登録表の道具を呼ぶ Python を書き、AST で危険な呼び出しと import を検査して `exec` する(10 秒の上限)。読み取り専用の段では、プロンプトに見せる道具を読み取り専用のものに絞る | `packages/agentsociety2/agentsociety2/env/router_codegen.py:951-959`・`1151-1231`・`1234-1350`・`1529-1540`・`1760-1785` | Apache-2.0 | 自由文の意図を基本操作の呼び出しに直す層(R-105 の M6)の実例 | 読み取り専用はプロンプトで見せる範囲の絞り込みで、実行時の強制は読んだ範囲に無い(`exec` の globals に全モジュールの読み取り専用の写像を渡す・1295 行)。行動を LLM のコードで決めるのは v2 の DM と違う |
| OASIS | 全道具の一覧(`get_openai_function_list`)から、体ごとの `available_actions` で使える道具を絞る | `oasis/social_agent/agent.py:52`・`58-113` | Apache-2.0 | 体ごとに「使える道具」を絞る欄(`Tool.known_by` の最初の形) | 絞り込みは実験者の設定で、本人の学習(知る・忘れる)ではない |
| UE Smart Objects | 物は「使い方の枠(slot)」と行動の定義と tag を持つデータで、論理は持たない。使う側が検索(`FindSmartObjects`)→ 予約(Claim)→ 使用(Use)→ 解放(Release)。物が壊れると予約は解かれ通知される | Smart Objects の文書 | Epic の文書 | 物の側が「何ができるか」を持ち、使う側が論理を持つ分け方(CT0 の道具の行と、DM-0 の候補の源 2「周りが示すできること」) | 予約で取り合いを解く(v2 は今の取り合いの仕組みのまま=CP3) |

「知っている/知らない」「体と知覚への影響」「中身を書くのは誰か」の欄を道具の行に持つ実装は、読んだ範囲に無かった(§14)。

## §9 1-8 候補の口と 1-8b 発話の口

選択肢の記号への偏り・並べ替えの効果・「その他」が選ばれにくいことは R-108 §1(並べ替えは偏りを消さず雑音にする・PriDe で事前分布を計器に)、判断モデルの段階の問いの位置の偏りは R-94 結論 5、古典と (G) を物差しとして残すことは R-83 結論 5 で済んでいる。

| 実装 | やり方 | コードの場所 | ライセンス | v2 が借りられる部品 | v2 の決定と違う点 |
|---|---|---|---|---|---|
| Concordia(候補の提示) | `multiple_choice_question(question, answers, randomize_choices=True)` は `rng.permutation` で候補を並べ替え、a〜z の記号を振って問いを書き、モデルが選んだ記号の番号を元の番号に戻して返す。rng を渡さないと `np.random.default_rng()`(種なし) | `concordia/document/interactive_document.py:42-44`・`50-67`・`303-336` | Apache-2.0 | 並べ替え → 記号 → 元の番号へ戻す流れ(1-8 の `number` を最後に振る形と同じ)。毎回の並べ替え | 並べ替えの順を記録の欄に残さない(文書の文には残る)。種なしの既定は再現できない(v2 は乱数の鍵から決める) |
| Concordia(同じ入口) | `LanguageModel.sample_choice(prompt, responses, *, seed)` → (番号・文・情報)。mock は `NoLanguageModel`(常に 0)・`RandomChoiceLanguageModel`(一様乱数)・`BiasedMedianChoiceLanguageModel`(真ん中に偏る) | `concordia/language_model/language_model.py:78-102`・`no_language_model.py:25-118` | Apache-2.0 | 実 LLM と mock を同じ口の別実装にする形(1-8 の「mock と古典は同じ入口」)。偏りのある mock(位置の偏りの試験の対照) | mock が `random.seed(seed)` で Python の全体の乱数を書き換える(v2 の乱数の鍵の規律とぶつかる) |
| SOTOPIA(発話) | 行動の種類は「何もしない・話す・身ぶり・行動・去る」の 5 つ。`AgentAction` は (種類・中身・宛先 `to`)。宛先が空なら全員に見える。種類を整数で受けた時は `available_action_types` の番号として解く | `sotopia/messages/message_classes.py:10`・`34-46`・`141-204`・`sotopia/envs/parallel.py:53-74`・`162-176` | MIT | 1-8b の `Utterance` の `addressees` と、見る人ごとに届ける経路(届く範囲を当面はセッションの参加者にする形と同じ) | 届く範囲は宛先だけで、空間の「聞こえた範囲」は無い。発話の長さ(モーラ)や記録の行への目印は無い |
| AI Town(発話) | 会話の発言は `messages` 表(会話 ID・発言の UUID・発言者・本文)に書き、相手の次のプロンプトは表から作る。打っている最中の印(typing)を入力で持つ | `convex/schema.ts:14-22`・会話の流れは R-43 §2 | MIT | 発話を共有の表に 1 回だけ書き、相手の入力はそこから作る形(1-8b の (a)(b)) | 宛先は会話の参加者だけ |
| Project Sid / PIANO(論文) | 10 の部品が共有の「エージェントの状態」を読み書きし、認知の制御役がボトルネックを通して高レベルの決定をし、その決定を発話の部品へ流す。著者は「話すことと他の行動の一貫性が上がる」と書く | arXiv 2411.00114 v1 §2(HTML) | CC BY 4.0(コードなし) | 1-8 で選んだ行動を 1-8b の発話の入力に載せる(言行の食い違いを減らす)形 | 部品と制御役の中身は論文の記述だけで、コードで確かめられない |
| The Sims(Forbus & Wright 2001) | 物は振る舞いの組を持ち、各振る舞いは「実行の手続き・できるかの検査・どの欲求を満たすかの広告」を持つ。Sim は家じゅうの物の全振る舞いから選ぶ。振る舞いの手続きは物に属し、Sim の糸の中で実行される | 同 PDF p.1(PDF の 3 頁) | 不明 | 候補の源 2「周りが示すできること」を物の側の行から作る形(UE Smart Objects と同じ系譜) | 広告の値は設計者の係数(v2 は候補の強さの値を持たない=DM-0) |
| NetLogo | `ask` は agentset の各体を毎回乱数の順に回す | 辞書の `ask` | — | 順のシャッフルを既定にする設計の古典の先例 | 体の順で、候補の順ではない |

「その他(自由記述)」の割合を欄に持つ実装、驚き 0〜5 や迷いの欄を判断の口の戻り値に持つ実装は、読んだ範囲に無かった。短い版(判断モデル)と長い版(LLM)を 1 つの仕組みで作る先例は、Lyfe Agents の「option を選ぶ高い層+option の中の行動は安い層」(§7 の #28・option の終わりは時間や繰り返しの検出の非 LLM の判定)が近いが、入力の文を共有する形ではない。

## §10 1-9 お金の基本操作(移すの 1 つ・書き手の静的検査・輪の溢れ)

相手のいない「お金を足す」道具(AgentSociety 2 の `add_person_currency`=`economy_space.py:291-315`)、abcEconomics の give・create・destroy と予約と確定、AI Economist の持ち物と取り置き、AgentTorch の「宣言した変数だけを書く」は R-105 §1・M13 で済んでいる。

| 実装 | やり方 | コードの場所 | ライセンス | v2 が借りられる部品 | v2 の決定と違う点 |
|---|---|---|---|---|---|
| TigerBeetle | 口(Account)の残高は transfer でしか変わらない(「口は不変。ただし残高の欄は transfer が変える」)。transfer は 1 つの口の借方と 1 つの口の貸方の「不変の記録」で、変更も削除もできない。全口の借方の合計=貸方の合計が保証。`code`(理由の番号)と `user_data_*` の欄。`linked` で続く transfer を 1 つの塊にし、全部成功か全部失敗。2 段階(保留 → 確定/取り消し)。残高の上限の旗(借方が貸方を超えたら拒む) | `docs/reference/account.md:3`・`20-26`・`193-203`・`docs/reference/transfer.md:3`・`8`・`15-38`・`docs/coding/linked-events.md:3-23` | Apache-2.0 | `transfer(from, to, amount, what, cause)` 1 つに縛る形の実在の先例。`what`=`code`・`cause`=`user_data_128` に当たる欄。交換を 2 つの transfer の `linked` にする形(R-105 M13)。保留と確定(v2 の two_phase と取り置き) | お金の DB で、体と物は持たない。時刻はクラスタが付ける |
| import-linter | `protected` の契約: 指定のモジュールは、許可表のモジュールからしか import できない。`forbidden`・`layers`・`independence` もある | `docs/contract_types/protected.md:1-40`・`index.md` | BSD-2-Clause | CP12 の gate と 1-9 の `economy/ops.py` を「許可表の外から import させない」検査(v2 の AST の試験の 1 段目の代わりか補い)。入れるには pip の許可が要る(§14) | import の検査だけで、属性の書き換え(1-0 の alias の形)は捕まえない |
| UE Mass | 処理(processor)は問い合わせに、断片ごとの読み/書きの権利(`EMassFragmentAccess` の None・ReadOnly・ReadWrite)を宣言する。別の体の断片への書き込みも宣言し、「依存の解決で権利を守らせる」と文書に書く | API 文書 `AddIndirectFragmentRequirement`(と検索の要約) | Epic の文書 | 書き手の宣言を道具が読み、順と並列を決める形(1-0 の `writes.soa` の宣言と同じ) | C++ の型で宣言し、宣言の外の書き込みを実行時に捕まえる仕組みは文書から読めない |
| Bevy | 同じ系の中で、同じ部品に書く問い合わせと読む問い合わせを並べると、Rust の参照の規則を守るため実行時にエラー(B0001・資源は B0002) | `errors/B0001.md:3`・`errors/B0002.md:3` | MIT/Apache-2.0 | 書き手の衝突を「組み立ての時に」落とす形 | 言語(Rust)の借用の規則に頼る。Python の v2 は AST と実行時の検査で代える |
| FLAME GPU 2 | エージェントの関数ごとに、読むメッセージと書くメッセージ・生む体の種類を宣言する | `include/flamegpu/model/AgentFunctionDescription.h:206-255` | **AGPL-3.0**(読むだけ) | 入出力の宣言を関数の定義に持たせる形 | GPU の関数の単位で、お金の保存は持たない |
| Linux ftrace | 輪(ring buffer)が満ちたとき、既定は古い記録を上書きし(`overwrite`=1)、0 にすると新しい記録を捨てる。統計に「上書きで失った数(overrun)」と「捨てた数(dropped events)」を別に出す | `Documentation/trace/ftrace.rst:791-818`・`1336-1341` | 文書(仕組みだけ) | K17 の「溢れたら記録して続ける・件数を計器に」の先例。失い方(古いのを上書き/新しいのを捨てる)を宣言の欄に書く形 | 輪は診断の記録で、帳簿の正は別(v2 の 10b の記録 §5-4 と同じ扱い) |
| OpenTelemetry(trace SDK) | まとめて送る処理は `maxQueueSize`(既定 2048)を超えると span を捨てる。上限で落とした属性・出来事・リンクの数は送り先が報告できなければならない(MUST) | `specification/trace/sdk.md:259-260`・`1122-1123` | Apache-2.0 | 捨てた数を必ず外に出す約束(manifest の溢れの件数) | — |

## §11 (補)1-0 の先例と、口の欄の対応表

### 11-1 1-0 の先例(状態の表と系)

1-0 は済んでいる(IMPLEMENTED #89)。指示で名指しされた Unity DOTS と UE Mass の形だけ記す。

| 実装 | やり方 | 場所 | v2 との対応 |
|---|---|---|---|
| Unity Entities 1.3 | 系(system)は `UpdateInGroup` で群に入り、群の中は `OrderFirst`/`OrderLast` → `UpdateBefore`/`UpdateAfter` の順で並べ直す。既定の群は初期化・シミュレーション・表示の 3 つ。制約の無い作成の順は「制約を満たす別の順に変わり得る」と文書が注意する | 系の順の文書 | v2 の `SYSTEMS` の宣言と順。制約の無い順を当てにしない注意 |
| UE Mass | 断片(データだけ)・tag(データの無い断片=有無が情報)・処理(状態を持たない論理)・問い合わせ(要る断片と権利の宣言)・構成の変更は命令の束に溜めて区切りでまとめて適用 | 文書(概要と API) | 箱と系・`writes.soa`・段 C の「その場の書き換えを捕まえる」 |
| Bevy | 系の引数の型で読み/書きを宣言し、衝突は B0001/B0002 | §10 | 1-0 の段 B(宣言の外 0) |

### 11-2 口の欄と先例の欄の対応(写すときの目安)

v2 の欄は [口の約束](../design/v2-foundation-contracts-2026-10-13.md) のとおり。先例の欄名は §2〜§10 で読んだコードと文書のまま。「—」はその先例に当たる欄が無い。

| v2 の口と欄 | AI Town | Concordia | AgentSociety | SOTOPIA / GA / genagents | TigerBeetle / UE |
|---|---|---|---|---|---|
| 1-3 `Event.id`(通し・決定的) | `inputs.number`(直前+1) | — | — | GA `node_id`(体ごと) | TB `id` |
| 1-3 `t_ns` | `received`(実時間 ms) | `Event.timestamp`(型は TimeModel 次第) | v1 `Message.day`+`t`(float)・v2 `t`(datetime) | genagents `created`(段の番号) | TB `timestamp`(クラスタが付ける) |
| 1-3 `who` / `whom` | — | `Event.source` | v1 `Message.from_id` / `to_id` | SOTOPIA 送り手 / `to` | TB `debit_account_id` / `credit_account_id` |
| 1-3 `what` | `inputs.name` | `Event.tag` | v1 `MessageKind`・v2 `function_name` | SOTOPIA `action_type` | TB `code`(理由の列挙) |
| 1-3 `how_much` | — | — | v2 道具の `kwargs` の中 | — | TB `amount` |
| 1-3 `cause` | — | 外からは `source="__external__"`(約束だけ) | v2 `trace_id`・`parent_span_id` | GA `filling`(内省の根拠のみ) | TB `user_data_128`(利用者が決める) |
| 1-3 `origin`(範囲の外の印) | — | `__external__` | — | — | — |
| 1-6 記憶の行の `event_id` | `data.conversationId` | — | — | genagents `pointer_id`(親の節点)・GA `filling` | — |
| 1-6 `strength` | `importance`・`lastAccess`(LLM の重要度+時刻) | — | — | genagents `importance`・`last_retrieved`・GA `poignancy`・`last_accessed` | UE `Max Age`(知覚の忘れ) |
| 1-6 `annotation` | `description`(本人の視点の要約) | 記憶の `text` | — | GA `description` | — |
| 1-6 `shown` | — | 構造化ログの部品ごとの中身 | — | — | — |
| 1-2 `Percept` の人・物 | — | — | v2 の観察の道具(`kind="observe"`) | GA (s, p, o, 文)・SOTOPIA の見る人ごとの文 | UE `FAIStimulus` の位置・tag・感覚の種類・年齢 |
| 1-7 `Tool.known_by` | — | — | — | SOTOPIA `available_actions`・OASIS `available_actions` | UE Smart Objects の利用者の tag |
| 1-7 `affects` / `requires` | — | — | v2 `readonly`・`kind` | — | UE Smart Objects の slot と行動の定義 |
| 1-8 `Candidate.number`(最後に振る) | — | a〜z の記号を並べ替えの後に振る | — | SOTOPIA 整数の `action_type` を番号として解く | — |
| 1-8 `DecisionPort.choose` | — | `sample_choice(prompt, responses, seed)` | — | — | — |
| 1-8b `Utterance.addressees` | 会話の参加者 | — | v1 `to_id` | SOTOPIA `to` | — |
| 1-8b `text` / `mora` | `messages.text` / — | — | v2 `agent_dialog.content` / — | SOTOPIA `argument` / — | — |
| 1-9 `transfer(from, to, amount, what, cause)` | — | — | v2 `add_person_currency(id, delta)`(相手なし) | — | TB transfer の 1 行 |

## §12 比べた相手のうち、土台の比較で「無い/浅い」もの(1 行ずつ)

- **Humanoid Agents**: 時間・記憶・会話は R-43 のとおり。本書ではライセンスの種別(Apache-2.0)だけを確かめ、コードは読み直していない。R-43 の読みの範囲では、土台の 9 軸に足すものは無い。
- **OASIS**: 道具の絞り込み(§8)のほか、出来事は trace 表の 4 列(R-72 §3)。お金・権利・知覚の分離は無い。
- **AgentTorch / LPM**: 遷移が宣言した変数だけを書く作り(R-105 #9・AGPL-3.0=読むだけ)。土台では §10 の「書き手の宣言」の系譜に入る。
- **AI Metropolis**: 体の間の距離から依存を作り、順を外して進める(R-73 §3-2)。コードの公開は見つからなかった。
- **Lyfe Agents**: §7・§9 のとおり。コードは見つからなかった。
- **SOTOPIA**: §6・§9 のとおり。記憶・お金・権利は無い。
- **SocioVerse**: リポは評価のスクリプト・質問票・人の見本(`user_pool`)だけで、エンジンの土台は無い(Apache-2.0)。**SocioVerse2** は抄録だけ読んだ(介入で枝を分ける・研究を版で管理)。コードの所在はプロジェクトの頁にあると抄録が書くが未確認。
- **Simile**: 社のコードと重みは公開されていない(検索の要約)。公開物は §1 #4 の genagents と GA。
- **MATSim**: §4(設定の書き出し)のほか、時刻は R-73。GPL-2.0。
- **ActivitySim**: §2(乱数の流れ・時間帯の表)。出来事の記録の形は R-72 でも本書でも読んでいない(空欄)。
- **SUMO**: §2。
- **Mesa**: §2。DataCollector は R-72 §3。
- **NetLogo**: §9(`ask` の乱数の順)。`ticks` の型は読めなかった(§14)。
- **Repast HPC**: R-73 §3-1 のとおり(double の刻み・保守的な同期)。土台の比較で足すものは無い。
- **FLAME GPU 2**: §10。AGPL-3.0(MIT ではない)。
- **GAMA**: 読んでいない(ライセンスも確かめていない)。
- **MASON**: §2。
- **JuPedSim**: LGPL-3.0 以降。土台(時計の刻み 0.01 秒=R-73)以外は群衆の物理で、本書の 9 軸の外。
- **Vadere**: R-73 §3-1 のとおり。本書では読んでいない。
- **Pseudo-PFLOW**: 人の流れの合成データ(JoRAS で申請して利用)で、生成のコードの公開は見つからなかった。土台の比較の相手にならない。
- **Dwarf Fortress / RimWorld**: DF は §5(司法の Wiki)。出来事ログと記憶の公開の技術記事は本書で探しきれなかった(§14)。RimWorld は読んでいない。

## §13 v2 への含意(土台ごとに 1〜3 行・親が判断する材料・未決)

- **1-1 時計**: 決定(ns の整数・定数の集約)は SUMO・Bevy・Concordia の形と同じ方向で、変える理由は見つからない。足す候補は 2 つ。(i) `time_consts.py` の換算を SUMO の `TIME2STEPS`/`STEPS2TIME` のように名前つきの関数に閉じ、直書きの検査の allow 表を短く保つ。(ii) 同時刻の順の規則を、MASON の注意書きのように 1-1 の約束に文で書く(v2 は決定的な全順序・ヒープの不安定さに頼らない)。
- **1-3 出来事の記録**: 「実験の口を 1 か所に強制」の先例はコードに無いので、v2 の CP12(AST と実行時の両方)は自前の構成。入口の形は AI Town の番号つきの `inputs`、申込書の型の検査は AgentSociety v1 の `WorkflowStepConfig` が参考になる。AgentSociety v1 の `UPDATE_STATE_INTERVENE` と `FUNCTION` は、v2 が持たない型として負の対照の試験に使える(心を直接書く・任意のコード)。
- **1-4 規則の表とつなぎの台帳**: つなぎの台帳の先例は無い。manifest に「既定と違う設定だけ」を出す MATSim の `config_reduced` の形は、`bridges_count` と並べる計器の候補。
- **1-5 権利台帳**: 行で持つ先例は無い。「止めずに記録し、世界の中の人が取り締まる」は Dwarf Fortress が近く、誤った通報まで同じ記録から出る点が v2 の方針と合う。
- **1-2 知覚の分離**: UE の `FAIStimulus` の欄(どの感覚・位置・年齢・感じ取れたか)と、物の側が「どの感覚に見えるか」を登録する形が `Percept` の欄の参考になる。強さの係数は持ち込まない。SOTOPIA の「共有の行動 → 見る人ごとの絞り込み → 文」は 1-2 と 1-8b を同じ経路にする形の実例。
- **1-6 記憶の器**: AI Town の `data.conversationId` が「目印+注釈+強さの材料」の最も近い実例(MIT=出典を付けて形を借りられる)。違いは、v2 は会話以外の出来事にも目印を付け、強さを System 1 の数値で持ち、重要度を LLM に書かせない点。「見せた」の録画は Concordia の内容のハッシュの重複除去が容量の面で参考になる。Concordia の `hash()` の例は、記憶の器の鍵にプロセスで変わるハッシュを使わない注意として 1-6 の試験に足せる。
- **1-7 道具の台帳**: AgentSociety 2 の「登録の時に性質を検査する」形と全呼び出しの記録が借りられる。「知っている/知らない」「中身を書くのは誰か」の欄は先例が無く、自前の構成。
- **1-8 候補の口**: Concordia の `multiple_choice_question`+`sample_choice` が最も近い(Apache-2.0)。v2 が足すのは、並べ替えの順を乱数の鍵から決めて記録の欄に残すこと(R-108 §3-1 の PriDe 型の計器と合う)と、mock が全体の乱数を触らないこと。偏りのある mock(`BiasedMedianChoiceLanguageModel` の型)は、位置の偏りの試験の対照に使える(R-94 結論 5)。
- **1-8b 発話の口**: SOTOPIA の `to` と見る人ごとの絞り込み、AI Town の「共有の表に 1 回書き、相手の入力はそこから作る」が `SpeechPort.say` の (a)(b) と同じ形。PIANO の「決めた行動を発話の入力に流す」は、1-8 の選択を 1-8b の入力に載せるかの判断材料(論文のみ)。
- **1-9 お金の基本操作**: TigerBeetle の口と transfer の約束(残高は transfer でしか変わらない・transfer は不変・`linked`・2 段階)が `transfer` の約束の文の手本になる(Apache-2.0)。書き手の静的検査は、import-linter の `protected` を AST の試験の前段に置く案がある(pip の許可が要る)。K17 の溢れは、ftrace のように「失い方」と「失った数」を別の欄で manifest に出す形。

## §14 空欄・未確認

- 権利を行で持つ実装(1-5)・つなぎの台帳(1-4)・道具の「知っている/知らない」(1-7)・「その他」の割合や驚き/迷いの欄(1-8)は、読んだ範囲に先例が無かった。「無い」の確かめは §1 の実装に限る。ほかの場所(例: 経済 ABM の住宅市場モデル・労働市場モデル、Rules as Code の実装の残り)は探していない。
- Dwarf Fortress・RimWorld の出来事ログと記憶の公開の技術記事は見つけられなかった(DF は司法の Wiki だけ)。
- SocioVerse2 は抄録だけ。介入の口とリプレイの実装は未確認(コードはプロジェクトの頁から辿れると抄録が書く)。
- AI Metropolis・Lyfe Agents・Pseudo-PFLOW の生成側・Simile 社のコードは見つからなかった(検索の範囲)。
- NetLogo の `ticks` と `tick-advance` の型(小数を許すか)は、取得した辞書の本文が途中で切れて読めなかった。
- UE Mass の処理の順と並列の規則(`ExecutionOrder`・処理の段)は、概要の頁に無く、検索の要約だけ(Epic の API 頁 `AddRequirement` は本文を読んでいない)。
- AgentSociety 2 の CodeGenRouter が読み取り専用を実行時にも強制しているかは、読んだ範囲(951-959・1234-1350・1760-1785)では見つからなかった。全文(2,096 行)は読んでいない。
- Concordia の `hash()` の指摘は Python の既定の挙動(文字列のハッシュの種がプロセスごとに変わる)からの推測で、実行して確かめていない。
- import-linter・TigerBeetle は文書を読んだだけで、手元で動かしていない(pip の許可は無い)。
- 本書は yomiyasu の推敲をかけていない(要旨を出す前に親が判断)。

## §15 親が一次確認すべき主張(写し検査の対象)

1. Concordia の `multiple_choice_question` が `self._rng.permutation(len(answers))` で並べ替え、`original_indices[idx]` を返す。rng を渡さないと `np.random.default_rng()`: https://github.com/google-deepmind/concordia/blob/70aa01cca819bbfad43face568010891a0cd90aa/concordia/document/interactive_document.py#L303-L336(と L64-67)
2. AI Town の記憶の行が `data` に `{type: 'conversation', conversationId, playerIds}` を持ち、共有の会話を指す: https://github.com/a16z-infra/ai-town/blob/8e05997f2409275669c8344b84a51692e83f3f33/convex/agent/schema.ts#L6-L31
3. TigerBeetle「Accounts are immutable. … (excluding balance fields, which are modified by transfers)」と「The sum of all accounts' debits_posted equals the sum of all accounts' credits_posted」: https://github.com/tigerbeetle/tigerbeetle/blob/6e39a21fc9d1d912dfbaa1bc7fd8ac108fe379ea/docs/reference/account.md(20-26 行)
4. AgentSociety v1 の介入の型に `UPDATE_STATE_INTERVENE`(体の状態を直接書く)と `FUNCTION`(任意の関数)がある: https://github.com/tsinghua-fib-lab/agentsociety/blob/8cc5bb9a9c27d039ec5519375db9d73ccf508cba/packages/agentsociety/agentsociety/simulation/simulationengine.py#L1772-L1822(型の定義は `configs/exp.py` L23-61)
5. ActivitySim の行の種「(global_seed + channel_seed + step_seed + row_index) % (1 << 32)」: https://github.com/ActivitySim/activitysim/blob/26382c34da7f1fddb62594ec67170560053a0ea3/activitysim/core/random.py#L65(実装は L106-109)

補: FLAME GPU 2 のライセンスは AGPL-3.0(LICENSE.md の冒頭)。MIT と思い込みやすいので、引く前に確かめてほしい。genagents のリポは StanfordHCI/genagents へ移っている(人と組織のカタログ 10-13 の「repo 頁は取得エラーで未確認」はこの移転が原因の可能性がある〔推測〕)。
