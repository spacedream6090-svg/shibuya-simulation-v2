# R-105 答申: 世界を書き換える仕組みの先例(行動の結果の決め方・状態の種類・品目つきの持ち物・原因つきの記録)

<!-- hdr:v1 -->
- **分野**: ABM方法論 #21 / SFCマクロ経済学 #10 / ソフトウェア工学 #29 / 自然言語処理・機械学習 #27 / ゲームエンジン工学・CG #30 / 法学(業法・条例) #11 | **重要度**: P0(リサーチの指示書 10-12 §2 E3。CP1 の仮決定の最終化の前提。指示書 10-12 §4-5 「最終はリサーチ E3 の後」)
- **一次確認**: **B**(サブの自己評価。○ 本文やコードを読んだ 24・△ 抄録や二次や検索の要約だけ 8・× 読めなかった 3(計 35)。コードは固定のコミットの raw を標準出力で読んだ。空欄は §空欄)・**親検収**: 済(第329・2026-10-12)。親が確認: Wang ら 2024(arXiv 2406.06485)の表 2 59.0/59.9/54.1・行動 77.1・環境 49.7・表 4 0.80/0.49・31 ゲーム・76,369/2,954・「0.599^10 で 1% 未満」を HTML 版で逐語確認 / AI Economist BSD-3-Clause・AgentTorch AGPL-3.0 を GitHub の API で確認 / abcEconomics は指定コミット `adb9e137abe4` の `agents/trader.py` の頭に Apache 2.0 と「quotation of the author」の条件を確認(**注: `inventory.py` には頭書きが無く、root に LICENSE ファイルも無い=「各ファイルの頭」は言い過ぎ。使うときは trader.py の頭書きを出典にする**)。Concordia の行番号は R-44 と別コミット(本書の表のとおり)。等級 **B** のまま
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-10-12・リサーチ役サブ(Opus 5.5)。子サブ未起動・Web は読むだけ。GitHub のコードは raw と API を標準出力で読んだ(clone・install なし)。作業の途中で一部のファイルを自分のスクラッチに一時的に写したが、読み終えて消した(リポの `data/` には何も取得していない。`data/research_cache/r105/` は作っていない)。Bitcoin の論文の PDF は取得ツールが自動で残した写しを pymupdf で抽出した。コミットなし・台帳/設計書/草案/src 未編集。容量の見積りのスクリプトだけ [scripts/r105/inventory_cost.py](scripts/r105/inventory_cost.py) に置いた。
> 既存答申との関係(重ねない): Concordia・AgentSociety・OASIS の行動の表現と効果の解決のコード読み = [R-44](v2-r44-code-reading-concordia-agentsociety-oasis.md)(本書は R-44 の後のコミットで関数名とライセンスだけ確かめ直し、R-44 に無い部品を足す)/ Generative Agents・AI Town・Humanoid Agents = [R-43](v2-r43-code-reading-ga-aitown-humanoid.md)(3 つとも所持・在庫・保存則なし)/ 行動の粒度と効果の解決者・Wang ら 2024 の 59.9% = [R-45](v2-r45-action-activity-granularity-research.md)(本書は同じ論文の表 2 の内訳を足す)/ 出来事の記録の形式・イベントソーシング・OpenTelemetry・ゲームのロックステップ・v1 の原因台帳 = [R-72](v2-r72-event-log-formats.md)(本書は causationId と PROV と戦闘ログを足す)/ 経済 ABM の正典 Caiani ら 2016(四重記入・純資産=実物資産の検算・ex nihilo の警告)= [boundary-economy-u10-u11-research](v2-boundary-economy-u10-u11-research.md)(親✔)/ EVE と UO の faucet と sink = [ugc-platform-import](v2-ugc-platform-import.md)/ 表せない 4 型 = [R-86](v2-r86-human-activity-taxonomy-coverage.md) §6-2。**循環参照検査**: [economy-sfc-deep-research](v2-economy-sfc-deep-research.md) は一次確認 D なので根拠に使わない(EURACE・JAMEL は本書で原典を見直した)。
> 対象の決定: [指示書 10-12](../design/v2-wallbounce-decisions-2026-10-12.md) §4-5(CP1〜CP14。特に CP1・CP2・CP3・CP4・CP12)・§1-1(CP6)・§1-4(D1〜D6)/ [反実仮想の設計書(草案)](../design/v2-counterfactual-primitives-design-round-draft.md) §1〜§2・§5。**決定項は書き換えない。** §v2 は案で、親が判断する材料・未決。
> 法律の点は助言ではなく出典の要約で、条文の確認は E4 の担当(本書では条文を読んでいない)。

## 結論(5 行)

1. **行動の結果の決め方は 5 つの型に分かれ、v2 の CP1 は「保存を作りで守る基本操作+物理は法則のコード」の型に当たる。** Concordia の標準のゲームマスター(GM)は LLM が自由文の行動の結果を書く(所持の釣り合いはプロンプトの指示だけ)。LLM に状態の変化を書かせると、自明でない変化で正解は最大 59.9%、環境が起こす変化では最大 49.7%(GPT-4・Wang ら 2024 表 2)。保存を作りで守る先例は abcEconomics(give・create・destroy・transform・予約と確定)、AI Economist(持ち物と取り置き)、TextWorld(前提の事実を消費する書き換え規則)、Bitcoin(入力=出力)がある。
2. **状態の種類分けは、会計の REA(資源・出来事・行為者。交換と変換の対)と、法学の Hohfeld(請求権↔義務・権能↔責任)と、存在論の BFO(物・性質・写せる中身)が CP1 の A〜D にほぼ重なる。** ずれは 3 つある。(a) B の「投稿・チラシの文面」は写しを作れるので湧かない量にならない(BFO の「総称的に依存する継続体」)。(b) 物を「持っている人」と「持ち主」が分かれていない(EVE は所有者と場所を別の列に持つ)。(c) C の「移す・解く」には変える権能(Hohfeld の 2 次の権利)が要る。
3. **品目つきの持ち物の先例は小規模か、品目が少ない。** Project Sid は最大 500 体(Minecraft の持ち物・1,000 体超はサーバーの制約で回せず)、AI Economist は 3 品目、Sugarscape は 2 品目、abcEconomics は体ごとの辞書。大規模な例は EVE で、2010 年に品目の ID を 64 bit に広げた(CCP 2010)。v2 の 390,067 体で 1 人 20 品目を疎の表で持つと 62〜94 MB、密な表で 1,000 品目なら 390 MB。原因つきの記録は 1 体 1 日 4.07〜30 行で 76〜562 MB/日 [再計算・前提は推測]。
4. **原因つきの記録の欄は、戦闘ログ(誰が・誰に・何を・どの手段で・どれだけ・いつ)と PROV(行為者・活動・物・時刻・計画)とイベントソーシング(直接の原因の ID+全体の相関 ID)を合わせると、CP1 の「5W1H+誰に+どれだけ+なぜ」をほぼ覆う。** CP12 の「書き込むその場で直接の原因だけ」は、イベントソーシングの causationId(「相手のメッセージの ID を自分の原因 ID にする」)と同じ型。SEM は「なぜ」と「どのように」を意図して外している。
5. **入口を 1 か所にして守る先例**は Redux(「状態を変える唯一の方法は action を出すこと」)、AI Town(状態は inputs で出す)、AgentTorch(遷移は設定で宣言した変数だけ書く・AGPL-3.0 なので読むだけ)。v2 に足すかは親の判断で、候補は 13 点(§v2 の M1〜M13)。特に大きいのは M2(持っている人と持ち主を分ける)・M3(C の権能)・M6(自由文を基本操作に直す層)・M13(交換を 2 つの移すの原子操作にする)。

## §0 出典の表

印: **○** 本文かコードを読んだ(取得ツールの要約を通したものは「ツール経由」と注記)/ **△** 抄録・二次・検索の要約だけ / **×** 読めなかった。時点は読んだ版の日付。

| # | 著者/機関 | 年 | 題名・対象 | URL | 印 | 何に使ったか | 時点 |
|---|---|---|---|---|---|---|---|
| 1 | Google DeepMind | 2026 | Concordia(Apache-2.0)`components/game_master/{inventory,event_resolution,world_state,interrupt_resolution}.py`・`contrib/components/game_master/{marketplace,mcp_tool_executor}.py` | https://github.com/google-deepmind/concordia(コミット `7459fc2a88f5`) | ○ | (i) GM の部品と関数名・ライセンス | 2026-10-08 |
| 2 | Vezhnevets ほか | 2023 | Generative agent-based modeling with actions grounded in physical, social, or digital space using Concordia(arXiv 2312.03664 v2)§2・§2.2・§2.3・§4.1 | https://arxiv.org/abs/2312.03664 | ○(ツール経由) | (i) GM と「grounded variables」 | 2023-12-13 |
| 3 | Wang, Todd, Xiao, Yuan, Côté, Clark, Jansen | 2024 | Can Language Models Serve as Text-Based World Simulators?(ACL 2024)表 1・表 2・§4・§5 | https://arxiv.org/abs/2406.06485 | ○(ツール経由) | (i) LLM が状態の変化を書く正確さ | 2024-06-10 |
| 4 | Altera.AL | 2024 | Project Sid: Many-agent simulations toward AI civilization(arXiv 2411.00114 v1)§2・§3.2・§5・§8 | https://arxiv.org/abs/2411.00114 | ○(ツール経由) | (i)(iii) Minecraft が物理と持ち物を持つ型・規模 | 2024-10-31 |
| 5 | Altera.AL | 2024 | project-sid のリポ(論文だけでコードなし) | https://github.com/altera-al/project-sid | △(検索の要約) | (i) コードの公開の有無 | 2026-10-12 |
| 6 | Taghawi-Nejad | 2012〜 | abcEconomics(Apache-2.0・「著者の引用」を求める注つき)`inventory.py`・`agents/trader.py`・`contracts/contracting.py` | https://github.com/AB-CE/abce(コミット `adb9e137abe4`) | ○ | (i)(ii)(iii) 物の移す・作る・使う・契約の原子操作 | 2024-01-22 |
| 7 | Salesforce | 2020〜22 | AI Economist / foundation(BSD-3-Clause)`base/base_agent.py`・`components/{continuous_double_auction,build}.py` | https://github.com/salesforce/ai-economist(コミット `a84d5f3fdcab`) | ○ | (i)(iii) 持ち物と取り置き・取引の移し方 | 2022-05-09 |
| 8 | Mesa の開発者 | 2026 | Mesa(Apache-2.0)`experimental/actions/actions.py`・`experimental/mesa_signals/{core,signals_util}.py`・`examples/basic/boltzmann_wealth_model/agents.py`・`examples/advanced/sugarscape_g1mt/agents.py` | https://github.com/mesa/mesa(コミット `5451086fe47a`) | ○ | (i)(iii)(iv) 状態の更新の作り・変化の通知 | 2026-10-10 |
| 9 | AgentTorch の開発者 | 2026 | AgentTorch(**AGPL-3.0**)`agent_torch/core/{controller,substep}.py` | https://github.com/AgentTorch/AgentTorch(コミット `86bb57e8a19a`) | ○ | (i)(iv) 遷移が宣言した変数だけを書く作り | 2026-09-12 |
| 10 | 清華大学 FIB 研究室 | 2026 | AgentSociety 2(Apache-2.0)`contrib/env/economy_space.py` | https://github.com/tsinghua-fib-lab/agentsociety(コミット `8cc5bb9a9c27`) | ○ | (i) 相手のいない「お金を足す」道具 | 2026-09-24 |
| 11 | Microsoft | 2018〜 | TextWorld(MIT)`textworld/logic/__init__.py`・`challenges/tw_cooking/textworld_data/logic/inventory.twl` | https://github.com/microsoft/TextWorld(main・コミット `6d88a0845bc9`) | ○ | (i)(ii) 前提の事実を消費する書き換え規則 | 2026-09-29 |
| 12 | Dawid, Gemkow, Harting, van der Hoog, Neugart | 2014〜16 | Eurace@Unibi のリポ(独自の EULA)README・LICENSE.md・`Credit/` | https://github.com/ETACE/eurace_unibi(コミット `5a45850f86bc`) | ○ | (i) 経済 ABM のコードの公開と使用条件 | 2020-04-26 |
| 13 | Teglio, Raberto, Cincotti | 2010 | Balance sheet approach to agent-based computational economics: the EURACE project | https://iris.unige.it/handle/11567/234390 | △(抄録) | (i) 動的な貸借対照表で保存を守る | 2010 |
| 14 | Basu, Pryor, Quint, Arnold | 1996 | Aspen: A microsimulation model of the economy(SAND96-2459) | https://www.osti.gov/biblio/399684 | △(抄録の要約) | (i) 体どうしのメッセージで取引 | 1996-10-01 |
| 15 | Caiani ほか | 2016 | Agent based-stock flow consistent macroeconomics(JEDC 69)= 既存答申 boundary-economy の §3-1(親✔) | 既存答申のとおり | ○(既存答申) | (i) 検算 2 本・ex nihilo の警告 | 2016 |
| 16 | Wikipedia の項目 | 2026 | Resources, Events, Agents(McCarthy 1982 の REA) | https://en.wikipedia.org/wiki/Resources,_Events,_Agents | △(二次) | (ii) 資源・出来事・行為者と交換の対 | 2026-10-12 |
| 17 | McCarthy | 1982 | The REA Accounting Model(The Accounting Review 57(3):554-578)原典 | (有料) | × | (ii) 原典 | なし |
| 18 | Wenar(SEP の項目 Rights) | 2025 改訂 | Rights §2.1(Hohfeld の 4 つの要素) | https://plato.stanford.edu/entries/rights/ | ○(ツール経由) | (ii) C の権利の形 | 2025-06-07 |
| 19 | BFO の開発者 | 2020/2021 | BFO 2020(ISO/IEC 21838-2:2021)`21838-2/owl/bfo-core.ttl`(CC BY 4.0) | https://github.com/BFO-ontology/BFO-2020 | ○ | (ii) 物・性質・役割・写せる中身の定義と例 | 2026-10-12 |
| 20 | W3C(Moreau, Missier 編) | 2013 | PROV-DM: The PROV Data Model(勧告) | https://www.w3.org/TR/prov-dm/ | ○(ツール経由) | (iv) 行為者・活動・物の関係 | 2013-04-30 |
| 21 | Kurrent(旧 Event Store) | 2024 | Event streams(v24.10)の予約済みのメタデータ | https://docs.kurrent.io/server/v24.10/features/streams | ○(ツール経由) | (iv) `$correlationId`・`$causationId` | v24.10 |
| 22 | Arkency(Greg Young の規則の引用) | 不明 | Correlation id and causation id in evented systems | https://blog.arkency.com/correlation-id-and-causation-id-in-evented-systems/ | ○(ツール経由) | (iv) 原因 ID の付け方の規則 | 年は本文に無い |
| 23 | Warcraft Wiki | 2026 | COMBAT_LOG_EVENT(CC BY-SA 4.0) | https://warcraft.wiki.gg/wiki/COMBAT_LOG_EVENT | ○(ツール経由) | (iv) ゲームの出来事の記録の欄 | 2026-10-12 |
| 24 | Nakamoto | 2008 | Bitcoin: A Peer-to-Peer Electronic Cash System §2・§9 | https://bitcoin.org/bitcoin.pdf | ○ | (i)(iv) 入力と出力で保存と出どころを作りで持つ | 2008 |
| 25 | Redux | 2026 | Three Principles | https://redux.js.org/understanding/thinking-in-redux/three-principles | ○(ツール経由) | (iv) 入口 1 か所 | 2026-10-12 |
| 26 | van Hage, Malaisé, Segers, Hollink, Schreiber | 2011 | Design and use of the Simple Event Model (SEM)(J. Web Semantics 9(2):128-136) | https://semanticweb.cs.vu.nl/2009/11/sem/(証明書切れで読めず) | △(検索の要約) | (iv) 「誰が何をどこでいつ」・なぜとどのようにを外す | 2011 |
| 27 | Ruscheinski, Uhrmacher | 2017 | Provenance in Modeling and Simulation Studies - Bridging Gaps(WSC 2017) | https://www.informs-sim.org/wsc17papers/includes/files/065.pdf | △(抄録) | (iv) シミュの研究の出どころ(状態の書き換えではない) | 2017 |
| 28 | CCP Prism X | 2010 | The API Dev Blog Trilogy - Volume Two(Tyrannis 1.2) | https://www.eveonline.com/news/view/the-api-dev-blog-trilogy-volume-two-the-types-they-are-a-changing-tyrannis-1.2 | ○(ツール経由) | (ii)(iii) 品目の ID・持ち主・場所の列 | 2010-09-22 |
| 29 | Engadget(Drain) | 2010 | EVE database issue causes thousands of items to go missing | https://www.engadget.com/2010-05-07-eve-database-issue-causes-thousands-of-items-to-go-missing.html | ○(ツール経由) | (iii) 品目の規模の手がかり | 2010-05-07 |
| 30 | CCP DeNormalized(フォーラム) | 2014 | データベースの大きさの書き込み | https://forums-archive.eveonline.com/message/5126632/(503) | ×(検索の要約だけ) | (iii) 持ち物の表の大きさ | 2014 |
| 31 | Fuzzwork による SDE の変換(`invItems` の列名) | なし | EVE の静的データの変換 | (検索の要約だけ) | △ | (ii) 列名 | なし |
| 32 | 既存答申 R-44・R-43・R-45・R-72・R-86・ugc-platform-import | 2026 | 上の「既存答申との関係」のとおり | docs/research/ | ○(既存答申) | 引用だけ | 2026-09〜10 |
| 33 | v2 のコード `economy/goods.py`・`engine/ledger_api.py`・`agents/state.py` | 2026 | 今の物の帳簿と持ち物 | リポ内 | ○ | §v2 の比べる相手 | 2026-10-12 |
| 34 | Wikipedia の項目 | 2026 | Basic Formal Ontology(ISO/IEC 21838-2:2021 の版) | https://en.wikipedia.org/wiki/Basic_Formal_Ontology | △(二次) | (ii) 規格の年 | 2026-10-12 |
| 35 | JAMEL(Seppecher・GPL-3.0) | 2019 | リポのライセンスだけ確認・コードは未読 | https://github.com/pseppecher/jamel | × | (i) 経済 ABM の比べる相手(未読) | 2019-05-08 |

## §1 (i) 行動の結果を決める方式の比較

### 1-1 結論

行動の結果を誰が決めるかで、先例は 5 つの型に分かれる。v2 の CP1 は型 D と型 E の組み合わせに当たる。

| 型 | 中身 | 先例(コードの場所・ライセンス) | 保存則 | v2 の決定との関係 |
|---|---|---|---|---|
| A LLM が全部を書く | 演者の自由文を GM の LLM が解釈し、結果の文・所持・位置・時刻を書く | Concordia の標準の GM(`EventResolution.pre_act`・`world_state.WorldState`・`GenerativeClock`。R-44 §1 Q4)・Generative Agents の物の状態(LLM の文を貼るだけ。R-43) | なし(プロンプトの指示だけ) | D5 でラン中の裁定を外したので、本線では使わない |
| B LLM が変化を決め、コードが範囲を確かめる | 「誰が何をいくつ得たか」を LLM に問い、コードは整数か・上下限の中かだけ確かめる | Concordia `Inventory`(`inventory.py`。`ItemTypeConfig.check_valid` 64 行・「transactions between named individuals must be balanced」238 行はプロンプトの文・`never_increase` 99 行・`apply` 378 行は外からの関数で一括に書き換える口)(Apache-2.0) | なし(釣り合いはプロンプトだけ・R-44 で親✔) | 使わない(保存がプロンプト頼み) |
| C 決まった語彙をコードが解く | 語の一覧から選ばせ(か、LLM が道具を選び)、効果はコードが書く | OASIS(32 語・SQLite。R-44 §3)・AI Town の 13 の入力口(R-43)・AgentSociety 2 の `@tool(readonly=False)`(`economy_space.py` 291〜316 行の `add_person_currency(id, delta)` は相手がいない片側の加算)(Apache-2.0)・Mesa(エージェントが自分と相手の属性を直接書く。`boltzmann_wealth_model/agents.py` の `give_money` は `other.wealth += 1; self.wealth -= 1`)(Apache-2.0)・AgentTorch(遷移の関数が返した値を、設定で宣言した道筋にだけ書く。`controller.py` 63〜83 行の `progress`)(AGPL-3.0) | 作る側の書き方しだい(枠は守らない) | D2 で語の一覧はメニューにしない。v2 は語ではなく状態の種類で縛る |
| D 保存を作りで守る基本操作 | 量を動かす操作だけを公開し、「出す側から減らして入る側に足す」を操作の中で必ず行う | abcEconomics(`trader.py` 718 行 `give`・759 行 `take`・`inventory.py` 22 行 `create`(「out of nothing … only for labor and natural resources」)・64 行 `destroy`・89〜103 行 `reserve`/`rewind`/`commit`・105 行 `transform`)(Apache-2.0)・AI Economist(`base_agent.py` 279 行 `inventory_to_escrow`・301 行 `escrow_to_inventory`・`continuous_double_auction.py` の約定で売り手の取り置き→買い手の持ち物と代金の移動)(BSD-3)・Concordia contrib の `MarketPlace`(370〜393 行で現金を確かめてから現金と品物を同時に動かす)(Apache-2.0)・TextWorld(規則の前提の事実を消費し、`$` 付きだけ残す。`logic/__init__.py` 110 行・`State.apply` 1717 行)(MIT)・Bitcoin(入力の合計を出力に分ける。§9)・Caiani ら 2016 と Eurace@Unibi(貸借対照表と取引の流れの表で検算) | 守る(作りで) | CP1 の A・B・C、CP2・CP3 と同じ型 |
| E 物理はエンジンが持つ | 位置・衝突・持ち物の物理をゲームエンジンが持ち、エージェントは基本動作を出すだけ | Project Sid(Minecraft の Survival モード。物理と持ち物はゲームが持つ。§3.2・付録 C)・AgentSociety v1 の移動(外部のシミュレータ。R-44 §2 Q4) | 物理の範囲で守る | CP1 の E(物理の法則のコード) |

### 1-2 型 A と型 D の差を測った数値

- **LLM に状態の変化を書かせた正確さ**(Wang ら 2024・GPT-4・31 のゲーム・76,369 の遷移・評価は 2,954 の遷移。表 1・§3)。状態の全体を書かせた場合、変化のある遷移の正解は、規則を LLM が書いたとき 59.0%・人が書いたとき 59.9%・規則なしで 54.1%(表 2 の「dynamic・Full」)。行動が起こす変化は最大 77.1%、環境が起こす変化(時間で進む温度など)は最大 49.7% だった(§4)。誤りは算術(温度)・常識・科学の知識が要る性質に集まる(§4・図 2)。人は同じ難しい部分で 0.80、GPT-4 は 0.49(表 4)。10 歩続けると 0.599 の 10 乗で 1% 未満になる(§5)。
  - R-45 は「59.9%」だけを親✔で写している。本書は表 2 の内訳(行動と環境の別)を足した。
  - 使える形の錨: **環境が起こす変化を LLM に書かせると、半分も当たらない。** CP1 の E を物理の法則のコードに置く判断の裏付けになる。
- **型 B の弱さ**: Concordia の `Inventory` は、LLM が「誰が増減したか」を答え、数の欄を「number|explanation」で答えさせる(264 行)。釣り合いはプロンプトの文(238 行)で、コードは確かめない。論文も GM の役目を「grounded variables を記録し、正しいかを確かめる」と書くが、例は「持っている額より多くは払わせない(かもしれない)」までで、帳簿の保存は書いていない(論文 §2)。
- **型 C の弱さ**: AgentSociety 2 の経済は `add_person_currency(id, delta)` で相手のいない加算ができる。毎日の利子・収入・税・消費も 1 人ずつ足し引きするだけ(`economy_space.py` 420〜445 行)で、払う相手の口座は無い。Mesa はエージェントが相手の属性を直接書くので、保存はモデルの作者が手で守る。
- **型 D の作り方の違い**
  - abcEconomics: 物は体ごとの辞書(`Inventory.haves`)。`give` は手元の量を確かめて減らし、相手へメッセージで送る(受け取りは相手の側)。売買は申し出の時に `reserve`(取り置き)し、受け入れで `commit`、断りで `rewind`。`create` は「無から作る・労働と天然資源にだけ使えばマクロ経済として完全」と注に書く。契約は `Contract`(出す側・払う側・品物・量・値段・終わりの日・渡した記録・払った記録)で、`offer_good_contract`・`accept_contract`・`deliver_contract`・`pay_contract`・`end_contract` で結び・果たし・解く(`contracting.py` 118〜317 行)。
  - AI Economist: 持ち物と取り置きを同じ品目の鍵で持ち、注文を出すと取り置きへ移す。約定で売り手の取り置き 1 個を買い手の持ち物へ、買い手の取り置きの代金を売り手へ、余りを買い手へ戻す。ただし家を建てる部品 `Build` は、木と石を減らしてコインを無から足す(`build.py` 145 行)=作る側の faucet。
  - TextWorld: 行動は「前提の事実 → 結果の事実」の書き換え規則。`take :: $at(P, r) & at(o, r) -> in(o, I)` は「人が部屋にいる」を残し(`$`)、「物が部屋にある」を消して「物が持ち物にある」を足す。物が 2 か所に同時にある状態は作れない。
  - Bitcoin: 取引は複数の入力と、ふつう 2 つまでの出力(支払いとお釣り)を持つ(§9)。硬貨は署名の鎖で、前の取引のハッシュを含む(§2)。保存と出どころが同じ作りで守られる。
  - 経済 ABM: Caiani ら 2016 は四重記入と「全主体の純資産の合計=実物資産の価額」で検算する(既存答申 boundary-economy §3-1・親✔)。EURACE は動的な貸借対照表で保存を扱った(Teglio ら 2010 の抄録・△)。ASPEN は体どうしのメッセージで取引を交わす(OSTI の抄録・△)。
- **解釈の層(自由文 → 型 D の操作)の先例**: Concordia `MarketPlace` は演者に JSON の注文(買う・売る・品物・値段・量)を書かせ、清算はコード。Concordia `MCPToolExecutor`(contrib)は LLM が行動から道具の要求を見つけて外部の道具を呼ぶ。AgentSociety 2 は演者が環境に自然文で問い、ルーターの LLM が `@tool` の関数を選ぶ(R-44 §2 補)。=「LLM が道具を選び、効果はコードが書く」型は既にある。

### 1-3 ライセンス(借りられるか)

| リポ | ライセンス | 扱い |
|---|---|---|
| Concordia | Apache-2.0 | 出典つきで使える |
| Mesa | Apache-2.0 | 出典つきで使える |
| AgentSociety | Apache-2.0 | 出典つきで使える |
| OASIS | Apache-2.0 | 出典つきで使える |
| Generative Agents | Apache-2.0 | 出典つきで使える |
| AI Town | MIT | 出典つきで使える |
| TextWorld | MIT | 出典つきで使える |
| AI Economist | BSD-3-Clause | 出典つきで使える |
| abcEconomics | Apache-2.0(`agents/trader.py` の頭に「研究で使ったら引用を」の依頼。〔親注(第329)〕`inventory.py` には頭書きが無く root に LICENSE ファイルも無い=頭書きのあるファイルを出典にする) | 出典つきで使える(引用の依頼に従う) |
| AgentTorch | **AGPL-3.0** | 読むだけ。写さない |
| JAMEL | GPL-3.0 | 読むだけ(本書では未読) |
| Eurace@Unibi | 独自の EULA(改変版の配布は持ち主の書面の許可が要る・結果の公表には謝辞) | 読むだけ |
| Project Sid | コードの公開なし | 論文だけ |

### 1-4 空欄・次に頼むこと

- Eurace@Unibi のコードで、保存の検算をどの関数がしているか(`Statistical_Office` か `Credit` か)は読んでいない。Teglio ら 2010 の本文は有料で読めていない。
- JAMEL(GPL-3.0)の会計の作りは未読。読むだけになる。
- ASPEN のコードは公開されていない(読んだ範囲)。1998 年の Computational Economics の版は確かめていない。

## §2 (ii) 世界の状態を種類で分ける先例

### 2-1 結論と対応表

CP1 の A〜E に近い分け方は、会計・法学・存在論・ゲームに 1 つずつある。どれも単独では A〜E のすべてを覆わない。

| 先例 | 分け方 | CP1 との対応 | 出典・印 |
|---|---|---|---|
| REA(McCarthy 1982) | 資源(物・サービス・お金)/出来事(資源に効く取引や合意)/行為者。中心は 2 つの出来事を対にする「duality」(片方が資源を手放し、片方が得る)。製造のような変換では 3 つ以上の出来事になる。拡張に「約束(commitment。注文など)」 | 資源=A、交換の対=A の 2 つの「移す」、変換=B の「作る・使う」、約束=C の契約 | #16 △(原典 #17 は ×) |
| Hohfeld(SEP Rights §2.1) | 特権(義務が無い)/請求権(相手に義務がある)/権能(自分か他人の要素を変えられる)/免除(他人が自分の要素を変えられない)。相関は 請求権↔義務・特権↔無請求権・権能↔責任・免除↔無能力。特権と請求権は 1 次、権能と免除は 2 次(1 次の権利を変える権利) | C の権利。「結ぶ・移す・解く」は権能の行使に当たる | #18 ○ |
| BFO 2020(ISO/IEC 21838-2:2021) | 独立の継続体(物・器官・椅子・オーケストラ)/特定に依存する継続体(性質・役割。複数の担い手の例に「ジョンのメアリーへの愛」「ジョンとこの像の所有の関係」「上司と部下の権限の関係」)/総称的に依存する継続体(写しが複数ありうる中身。例: PDF とその写し・紙のモールス符号と送信された信号の共通の中身)/出来事(過程。例に「売るという行為」) | 物=A(と E の体)、写せる中身=B の投稿やチラシの文面、関係の性質=C と D の両方 | #19 ○ |
| 世界側台帳の骨格(v2 の既存設計)の軸 3・軸 4 | 構成的・規制的・物理・記述だけ/regimented(違反できない=エンジンが守る)・enforced(違反できる+見つけて制裁)・unenforced(Searle・Grossi ほか) | A の保存則=regimented、C の権利=enforced(§1-4 の「止めずに記録」と同じ向き) | [世界過程の設計](../design/v2-world-process-design.md) §2(既存) |
| EVE Online の持ち物の表 | 品目の個体(itemID)ごとに品目の種類(typeID)・持ち主(ownerID)・場所(locationID。場所も品目)・置き方(flagID)・数量 | A の物。**持ち主と場所(持っている所)を別の列に持つ** | #28 ○(列の意味)・#31 △(列名) |
| ゲームのシステム(物の性質と状態・体の基本動作) | E6 の担当(本書では扱わない) | E | なし |

### 2-2 CP1 とのずれ(3 つ)

1. **B に「写せるもの」と「写せないもの」が混ざる。** 料理は材料(A の物)を使って作る変換で、材料の側で保存が閉じる(REA の変換・abcEconomics の `transform` は `destroy` と `create` の組・TextWorld の調理の規則は材料の事実を消費する)。一方、投稿やチラシの文面は BFO の「総称的に依存する継続体」で、写しは何枚でも作れる。紙のチラシは紙(物)が担い手で、文面は担い手に乗る中身。看板も同じ(板が物、文面が中身)。=B の「作る・使う」の中で、保存を確かめる相手が「材料の物」か「無し(写しは自由)」かで分かれる。
2. **物の「持っている人」と「持ち主」が分かれていない。** abcEconomics・AI Economist・Concordia・Mesa はどれも「持っている=持ち主」で 1 つの欄。EVE は持ち主と場所を別の列にする。§1-4 は「物理的にはできるが法に反する行動は起きたことにする」と決めた。盗みや置き引きでは、物の場所(持っている人)は移り、持ち主は移らない。この 2 つを 1 つの欄で持つと、起きたこと(物の移動)と法の状態(所有)の片方しか書けない。
3. **C の「移す・解く」は、変える権能があるかで効果が変わる。** Hohfeld の権能は「自分か他人の要素を変えられる力」で、2 次の権利。権能のない人の「売る」は、物を渡すこと(A の移す)は起きても、所有を移すこと(C)は起きない、という形になりうる。法の効果(無効・取り消せる・善意の取得など)は法令の解釈が要るので E4 で確かめる(本書では条文を読んでいない)。

### 2-3 借りられる点

- REA の「交換は 2 つの出来事の対」: 購入は「物を移す」と「お金を移す」の対で、片方だけ起きる状態を作らない。v2 の `restock_many` は既に「代金を払えた行だけ補充する」(`goods.py` 678〜684 行)。基本操作の水準で「対の移す」を 1 つの操作にするかは §v2 の M13。
- Hohfeld の相関: C の 1 行(CP4)は、相手の側の義務と対になる。CP4 の欄「相手」はこれに当たる。2 次の権利(誰がこの権利を変えられるか)を欄に持つかは §v2 の M3。
- BFO の「関係の性質」: 所有と愛はどちらも 2 人以上に依存する性質で、存在論では同じ類に入る。CP1 が C と D を分けているのは「台帳で確かめる/本人だけが変える」の変え方の違いによる(存在の種類の違いではない)。分ける根拠は変え方と記録の仕組みの側にある、と書いておくと説明しやすい(案)。

### 2-4 空欄

- McCarthy 1982 の原典(有料)・ISO/IEC 15944-4(有償の規格)は読んでいない。REA の「交換と変換」の語は Wikipedia の項目では「変換では 3 つ以上の出来事」とだけあり、Geerts と McCarthy の拡張の原典は未読。
- EVE の `invItems` の列名は第三者の変換(Fuzzwork)の要約で見ただけ(△)。CCP の記事は「場所は品目だが持ち主は除く」まで(○)。

## §3 (iii) 持ち物を品目つきで持つ社会シミュの例と費用

### 3-1 結論(規模の表)

| 先例 | 体の数 | 品目の数 | 持ち方 | 時間 | 出典・印 |
|---|---|---|---|---|---|
| Project Sid | 25〜50(主な実験)・500(9,000 秒)・1,000 体超はサーバーの制約で回せず | Minecraft の約 1,000 品目のうち 49 体 4 時間で約 320 に飽和 | ゲームの持ち物(初期の例: 鉄の剣 1・エメラルド 20・鉄のインゴット 20) | 最長 4 時間(ゲーム内 12 日) | #4 ○(ツール経由)§3.2・§4.2・§5.3・§8.4・付録 D |
| AI Economist | 論文の設定は少数(本書では数えていない) | 木・石・コインの 3 | 体ごとの辞書(持ち物と取り置き) | エピソード単位 | #7 ○(コード) |
| Sugarscape(Mesa の例) | 例の設定しだい | 砂糖・スパイスの 2 | 体の属性 | 刻み単位 | #8 ○(コード) |
| abcEconomics | 例の設定しだい | 任意(品目の名前の鍵) | 体ごとの辞書+取り置き+期限つきの品物 | ラウンド単位 | #6 ○(コード) |
| Concordia `Inventory` | 演者の数(数人〜数十人の想定・推測) | 設定した品目 | 体ごとの辞書。LLM が増減を答える | GM の 1 回の解決ごと | #1 ○ |
| Caiani ら 2016 | 家計 8,000・消費財の会社 100・資本財の会社 20・銀行 10 | 消費財は均質・資本財は年式つき | 貸借対照表 | 四半期の回 | 既存答申 boundary-economy(親✔) |
| EVE Online | 単一のシャード(プレイヤー数は本書では確かめていない) | 品目の種類の ID を 16 bit から 32 bit へ・品目の個体の ID を 32 bit から 64 bit へ(2010)。11.4 万個の消失が全体の 0.0071% と CCP が説明(→ 約 16 億個。何に対する割合かは記事も不明としている) | 個体ごとの行(持ち主・場所・数量) | 実時間・常時 | #28 ○・#29 ○・#30 × |
| v2 の今 | 390,067 体(実データ規模) | 世帯は品目を持たず個数だけ(uint8・1 B/体)。店は SKU 別の棚(POI 側)。世帯の SKU 別は全世帯の合計だけ | 個体 SoA の `holdings` と、POI の棚の表 | 刻み | `agents/state.py`・`economy/goods.py`(○) |

使える形の錨: **数十万体で、1 人ずつ品目つきの持ち物を持ち、保存を検算している社会シミュの先例は見つからなかった。** 品目の個体まで持つ大規模な例はゲーム(EVE)で、科学のシミュではない。LLM 系は最大でも数百体(Project Sid)。

### 3-2 v2 の規模での費用の見積り(推測の前提つき)

[scripts/r105/inventory_cost.py](scripts/r105/inventory_cost.py) で計算した [再計算]。前提のうち出典があるのは 390,067 体(`goods.py` の注)と、金の台帳の生ログの実測 4.07 行/体/日・24 B/行(10b の材料 §3-4・R-72 結論 1)だけ。1 人が持つ品目の種類の数・物の移動の回数・記録の行の欄は**推測**。

| 何を | 前提 | 5,000 体 | 390,067 体 |
|---|---|---|---|
| 持ち物の表(疎・8 B/行=体+品目+数) | 1 人 5 / 20 / 50 品目 | 0.2 / 0.8 / 2.0 MB | 15.6 / 62.4 / 156.0 MB |
| 同(持ち主の欄を足して 12 B/行) | 同上 | 0.3 / 1.2 / 3.0 MB | 23.4 / 93.6 / 234.0 MB |
| 持ち物の表(密・1 B/セル) | 品目の総数 100 / 1,000 / 10,000 | 0.5 / 5.0 / 50.0 MB | 39 / 390 / 3,901 MB |
| 今の金の生ログ | 4.07 行 × 24 B(実測) | 0.5 MB/日 | 38.1 MB/日 |
| 原因つきの書き換えの記録(48 B/行=時刻 8・誰 4・出す側 4・入る側 4・品目 4・数 4・場所 4・原因の種類 1・原因 ID 8・理由の参照 4) | 4.07 / 10 / 30 行/体/日 | 1.0 / 2.4 / 7.2 MB/日 | 76.2 / 187.2 / 561.7 MB/日(30 日で 2.29 / 5.62 / 16.85 GB) |

- 読み: 状態(持ち物の表)は疎なら数百 MB で収まる。重いのは記録の方で、1 日の行数しだいで 30 日 2〜17 GB になる。R-72 の「1 日 6〜15 GB(39 万体)」は推測のまま(R-72 §7-5)で、本書の値とは前提が違う。
- 計算量は案を外す理由にしない(CLAUDE.md §4・指示書 §1-9)。この表は性能予算を宣言するときの材料。

### 3-3 空欄

- **1 人が持ち歩く品目の数の実データ**は探していない(かばんの中身の調査は民間のものが多い・推測)。E5 (vi)(人が持ち運ぶ物)と合わせて頼むのがよい。
- EVE の持ち物の表の大きさ(2014 年のフォーラムで約 250 GB とされる書き込み)は 503 で読めず、検索の要約だけ(×)。
- Dwarf Fortress・The Sims などのゲームの物の数と費用は調べていない(E6 の範囲)。

## §4 (iv) 状態の書き換えに原因と 5W1H を付けている例

### 4-1 結論(欄の対応表)

| 先例 | 誰が | 誰に | 何を | どこで | いつ | どのように | どれだけ | なぜ(原因) | 出典・印 |
|---|---|---|---|---|---|---|---|---|---|
| WoW の戦闘ログ | sourceGUID・sourceName・sourceFlags | destGUID・destName・destFlags | subevent(例 `SPELL_DAMAGE`) | 無い | timestamp(ミリ秒) | 接頭部の spellId・spellName・spellSchool | 接尾部の amount・overkill など | 無い | #23 ○ |
| W3C PROV-DM | Agent(人・組織・ソフト)・`wasAssociatedWith`・`actedOnBehalfOf`(代理) | (欄は無い。`used` の物で表す) | Entity・Activity・`wasGeneratedBy`・`used`・`wasInvalidatedBy` | 無い(属性で足す) | 生成と使用の時刻(任意) | Activity | 属性で足す | `wasInformedBy`(活動から活動へ)・`wasDerivedFrom`・`hadPlan`(計画) | #20 ○ |
| イベントソーシング(Kurrent の予約済みのメタデータ) | アプリの側 | アプリの側 | 出来事の型 | アプリの側 | 追記の順 | なし | なし | `$causationId`(直接の原因)・`$correlationId`(会話の全体) | #21 ○・#22 ○ |
| SEM | Actor | (役割で表す) | Event | Place | Time | **外す** | なし | **外す**(「なぜとどのようには、それ自体が長い話で別の表し方が要る」) | #26 △ |
| Bitcoin | 署名(鍵) | 出力の宛先 | 取引 | なし | ブロックの時刻 | なし | 出力の額 | 入力が前の取引の出力を指す(出どころが作りで残る) | #24 ○ |
| Mesa の signals | owner | なし | name・signal_type | なし | なし | なし | additional_kwargs | 無い | #8 ○ |
| v1 の原因台帳 | 4 分類(agent・device・natural・boundary) | 聞き手の行は話し手を行為者に | 6 語 | なし | なし | なし | なし | 近い原因+後ろ向きの指し 1 本 | R-72 §2-2(既存) |
| CP1・CP12(v2 の決定) | 誰が | 誰に | 何を | どこで | いつ | どのように | どれだけ | 原因の ID(LLM の呼び出し・入力に入っていた出来事・過程の名前・実験の条件)+本人の理由 | 指示書 10-12 §4-5 |

### 4-2 使える形の錨

- **直接の原因だけを書き、長い道筋は後でたどる**: Greg Young の規則として引かれる形は「各メッセージは自分の ID・相関 ID・原因 ID の 3 つを持つ。あるメッセージが別のメッセージを起こすとき、相関 ID は元のものを写し、元の ID を自分の原因 ID にする」(#22)。Kurrent は `$correlationId` と `$causationId` を予約済みの名前にし、相関 ID ごとに出来事を集める仕組み(`$by_correlation_id`)を持つ(#21)。CP12 の「書き込むその場で直接の原因だけ」と同じ型で、相関 ID が加わる点だけが違う。
- **原因の型の数**: PROV の Agent の下位の型は人・組織・ソフトの 3 つ(#20)。v1 は agent・device・natural・boundary の 4 分類(R-72)。CP12 は LLM の呼び出し・過程の名前・実験の条件の 3 種類(草案の読み。親の確認待ちのまま)。
- **入口を 1 か所にする**: Redux の原則「状態を変える唯一の方法は action(起きたことを書いたもの)を出すこと」「変化は純粋な関数で書く」(#25)。AI Town「状態は書かず inputs で出す」(R-43)。AgentTorch は遷移の関数が返した値を、設定で宣言した道筋にだけ `set_by_path` で書く(#9・読むだけ)。
- **出どころを作りで持つ**: Bitcoin は出力を使うとき、その出力を作った取引を入力に書く(#24)。お金の 1 単位ごとの出どころをたどれるが、v2 の口座の残高の方式(残高だけを持つ)とは作りが違う。v2 で借りるなら「お金の出どころの追跡」は記録の側の索引で足りる(案)。
- **シミュの研究の出どころ**: Ruscheinski と Uhrmacher は PROV でシミュの研究(モデルの作り・実験・データ)の出どころを記録する(#27 △)。状態の書き換えの 1 件ずつではない。**シミュの中の状態の書き換えに PROV や原因 ID を付けた先例は、R-72 に続き本書でも見つからなかった**(探した範囲: 上の表のリポと論文)。

### 4-3 空欄

- SEM の仕様の頁は証明書切れで読めなかった(△ の要約だけ)。
- Arkency の記事の年と著者は本文に書かれていない。Greg Young の元の発言の場所は未確認。
- ゲームの replay ログ(入力だけを記録して再生する型)は R-72 §4 で済み。本書では重ねない。

## §空欄(まとめ)

| # | 何が | なぜ空欄か | 次にすること |
|---|---|---|---|
| 1 | McCarthy 1982 の原典・ISO/IEC 15944-4 | 有料・有償の規格 | 存在と条件だけ記録(買うかはユーザー) |
| 2 | Teglio ら 2010 の本文 | 有料(Springer) | 要らなければ空欄のまま |
| 3 | Eurace@Unibi の保存の検算の関数 | コードを全部は読んでいない(独自の EULA・読むだけ) | 必要なら次のリサーチで `Statistical_Office` を読む |
| 4 | JAMEL の会計の作り | 未読(GPL-3.0・読むだけ) | 同上 |
| 5 | ASPEN のコード・1998 年の雑誌の版 | 公開なし・未確認 | なし |
| 6 | Project Sid のコード | 公開されていない(リポは論文だけ) | なし |
| 7 | EVE の持ち物の表の大きさ(2014) | フォーラムが 503 | 要らなければ空欄のまま |
| 8 | 1 人が持ち歩く品目の数の実データ | 探していない | E5 (vi) と合わせて頼む |
| 9 | SEM の仕様の頁 | 証明書切れ | なし |
| 10 | 占有と所有・権能のない処分の法の効果(民法) | 法令の解釈が要る・本書の範囲外 | **E4(R-106 の予定)に頼む**: 占有(持っている)と所有(持ち主)の別・他人の物の売買・盗品・善意の取得を、条番号と施行日つきで |
| 11 | AI Economist の論文の体の数・Concordia の想定の体の数 | 本書では数えていない | 要るなら次に |

ユーザーの判断が要るもの: **0 件**(取得したファイルは無く、ドメインの許可も申請も要らない)。

## §v2 への当てはめ(案・未決。親が判断する材料)

比べる相手: 指示書 10-12 §4-5 の CP1(状態の種類 A 湧かないもの・B 作る/使うもの・C 権利・D 本人の中・E 物理=法則/基本操作=移す・作る/使う・権利を結ぶ/移す/解く・自分を変える)・CP2・CP3・CP4・CP12・§1-1(CP6)・§1-4(D1〜D6)。

### 先例と同じ点(仮決定の裏付けになるもの)

- **A を「移す」だけで変え、保存を操作の中で守る**のは、abcEconomics・AI Economist・TextWorld・Bitcoin・SFC の経済 ABM と同じ型(§1 の型 D)。LLM に結果を書かせる型 A・型 B では保存が守られず(Concordia の釣り合いはプロンプトだけ)、正確さも 6 割前後(Wang ら 2024)。
- **E を物理の法則のコードに置く**のは、Project Sid(Minecraft)・AgentSociety v1 の移動と同じ。LLM が環境の変化を書くと最大 49.7%(Wang ら 2024)。
- **C を止めずに記録する**(§1-4)のは、v2 の既存設計の軸 4(enforced=違反できる+見つけて制裁)と同じ。
- **原因は直接のものだけ・道筋は後で**(CP12)は、イベントソーシングの causationId と同じ型。
- **A〜D を基本操作からしか書かない**(CP1)・**実験の入口を 1 か所**(CP12)は、Redux・AI Town・AgentTorch の「書き込みの口を 1 つにする」作りと同じ。v2 は既に台帳の窓(`AgentState.writable()`)と AST の検査(10f の K24)を持つ。

### 違う点と借りられる点(M1〜M13)

| # | 論点 | 先例 | 案(未リサーチの部分は「草案の案」) | 決めるもの |
|---|---|---|---|---|
| M1 | B の中に「材料を使う変換」と「写せる中身」が混ざる | REA の変換・abcEconomics `transform`・TextWorld の調理の規則/BFO の総称的に依存する継続体 | B を 2 つに分ける: B1 変換(材料の A を使い、品物の A を作る。保存は材料の側で閉じる。レシピは世界の部品)と B2 中身(投稿・チラシや看板の文面。写しは自由。紙や板は A の物)。草案の案 | B を分けるか・B2 の写しに費用(紙・印刷)を付けるか |
| M2 | 物の「持っている人(場所)」と「持ち主」 | EVE は持ち主と場所を別の列に持つ/abcEconomics・AI Economist・Concordia は 1 つ | A の物の行に「持っている所(人・場所・棚)」と「持ち主(C の権利台帳への参照)」の 2 欄。A の「移す」は持っている所を変え、C の「移す」は持ち主を変える。置き引きは A だけが動き、C は動かない=「許可のない行動」として記録(§1-4)。費用は 1 行 8 B→12 B(§3-2) | 2 欄にするか・世帯の持ち物を品目つきにする時期(今は個数だけ) |
| M3 | C を変える権能 | Hohfeld の権能と免除(2 次の権利) | CP4 の 1 行に「この権利を変えられる人(権能)」を欄で持つか、規則の表(PlanSpec)で引くか。権能のない「結ぶ・移す・解く」は、止めずに試みとして記録し、法の効果(C の変化)は起こさない。法の効果は E4 で確かめる | 欄で持つか規則で引くか・権能のない試みの扱い |
| M4 | 取り置き(予約) | abcEconomics `reserve`/`commit`/`rewind`・AI Economist の取り置き | CP3 の「前提は確定の前に確かめる・取り合いは今の仕組み」を、物とお金の「取り置き」の状態で表すか。今の二相の確定(`engine/commit.py`)と役割が重なる | 状態として持つか・今の二相の確定のままか |
| M5 | 無から作る口の範囲 | abcEconomics の `create` の注(労働と天然資源だけならマクロとして完全)/AI Economist の `Build` はコインを無から作る | v2 は faucet を境界の口座(外界)・自然・人口に限る(既決の U11・U-Goods)。B1 の「作る」を faucet にしないことを試験で強制(材料の減りと品物の増えの対) | 試験に足すか |
| M6 | 自由文 → 基本操作に直す層 | Concordia `MarketPlace`(JSON の注文・清算はコード)・AgentSociety 2 のルーター(LLM が道具を選び効果はコード)・Concordia `MCPToolExecutor` | D1・D3 では、住人の言葉の試みを基本操作の呼び出しに直す口が要る。直すのは判断モデルか LLM の出力の形(道具の呼び出し)で、効果はコード。直せない試みは D3 で「動かなかった」と返し記録する。直す役が LLM のとき、結果ではなく**操作の選択だけ**を書かせる点が Concordia の標準の GM と違う | 直す口の置き場所(CT の道具の設計と一緒か) |
| M7 | C と D の境 | BFO では所有と愛は同じ「関係の性質」の類 | 分ける根拠を「変え方と記録の仕組み」(台帳で双方に対になる/本人だけが変える)と書いておく。存在の種類の違いとは書かない | 文言だけ |
| M8 | E の記録の粒度 | WoW の戦闘ログは物理の効果(ダメージ)も 1 件ずつ記録 | CP1 の「E は意味のある区切りだけ」の区切りを、他人への作用(ぶつかる・押す)は 1 件ずつ、移動や音の場は区切りだけ、と分けるか。草案の案 | E のどれを 1 件ずつ残すか |
| M9 | 相関 ID | イベントソーシングの correlationId | 実験の条件の ID を、原因の鎖に沿って子孫の行へ写す欄(8 B/行)。「改変がどこまで届いたか」をたどらずに引ける。効いたかは分岐の差で測る(CP12)ので、相関 ID は索引で因果の証明ではない | 足すか |
| M10 | 原因の種類の数 | v1 の 4 分類(agent・device・natural・boundary)・PROV の Agent の 3 型 | CP12 の 3 種類(LLM の呼び出し・過程の名前・実験の条件)で、基準のランの「境界から届く外の決定」(本社のメール・法の公布。§1-1)はどれに入るか。「過程の名前」に「境界から届く情報」を足すか、4 種類目にするか | 3 種類の中身の確定(草案は親の確認待ち) |
| M11 | 書き込みの口の強制の形 | AgentTorch の「宣言した書き込み先だけ」・Redux | CP1 の「A〜D は基本操作から、E は法則のコードから」を、静的な検査(AST)に加えて、基本操作ごとに「書いてよい欄の一覧」を宣言させ、実行時に照らす | 足すか |
| M12 | 品目つきの持ち物の費用 | §3 | 疎の表(体・品目・数・持ち主)なら 390,067 体 × 20 品目で 62〜94 MB [再計算・推測の前提]。重いのは記録(76〜562 MB/日)。性能予算の宣言に使う | 予算の宣言・1 人の品目の数の実データ(§空欄 8) |
| M13 | 交換を 1 つの操作にするか | REA の duality・AI Economist の約定・Concordia `MarketPlace`・v2 の `restock_many`(払えた行だけ補充) | 「移す」を 2 本(物とお金)組にした操作(片方だけ起きない)を基本操作として持つか、「移す」の連続で書き、確定を 1 つの単位にするか。CP11 の「合計は合うが相手を間違える」型の見逃しは、対にすると試験しやすい(推測) | 基本操作の数(4 のままか・交換を足すか) |

### 親に確かめてほしい点

- 「基本操作は 4 つ」の 4 つの名前は、草案の注のとおり指示書の表の「変え方」に当たると読んだ(移す/作る・使う/結ぶ・移す・解く/本人が変える)。本書もこの読みで比べた。
- CP12 の「3 種類」の中身は草案の読み(LLM の呼び出し・過程の名前・実験の条件)のまま使った。M10 はその読みに依存する。
