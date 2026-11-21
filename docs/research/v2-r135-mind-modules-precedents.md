<!-- hdr:v1 | 等級: (親検収の前) | 作成: 2026-11-03 | 範囲: 11-03 §7-1(題 9 の材料) -->
# R-135 心のモジュールの先例(速い過程と遅い過程が状態を共有し、調停で誰が答えるかを決める形)

- **分野**: 認知科学(記憶・習慣) #12 / 自然言語処理・機械学習 #27 / ゲームエンジン工学・CG #30 / ABM方法論 #21 / ソフトウェア工学 #29 | **重要度**: P0([指示書 11-03](../design/prompt-2026-11-03-reply3.md) §7-1「題 9 の材料・最優先」)
- **一次確認**: (親検収の前)。筆者の実読=新しく読んだ出典 29 本(◎ 19・○ 8・△ 2。S27 は ○ と △ の混在で ○ に数えた)+既存答申 4 本(R-39・R-41・R-128・R-133)。読めなかったものは §10
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md)

> 作成 2026-11-03・リサーチ役(Opus 5.5)。子サブは起動していない。Web は読むだけ。PDF は WebFetch が一時の場所に置いた写しを pymupdf で読んだもの(4 本)と、curl の標準出力を pymupdf と HTML の剥がしに直接通したもの(残り)で、リポにも data/ にも何も保存していない。途中から WebFetch と WebSearch が使えなくなった(要約役のモデルの上限)ため、後半は curl で原文を取り、grep で該当の文を確かめた。ゲームの章は読んだだけで、コードは写していない。封印の層(holdout・test の層)には触れていない。コード・台帳・設計書・INDEX.md は 1 バイトも変えていない。試験も回していない。
> 土台: `build/spatial-d102-prep` の HEAD `33193c3`。場所は `path:行`(src/shibuya からの相対は `engine/...` と略す)。出典は §9 の [S*]。読んだ日はすべて 2026-11-03。
> 等級: ◎=原典か公式の文書を本文まで読んだ(該当の文を grep で確かめた)/○=書誌の索引の要旨・著者の要約・別の論文の逐語の引用を経た/△=検索の要約だけ。筆者の組み立ては【見立て】、根拠のない置き方は【推測】と書く。**推薦は書かない**(比較と選択肢と根拠まで)。決めるのはユーザー(1 題ずつ壁打ち)。
> 既存答申との関係: 二重過程の定義と介入の頻度・メタ推論・小さい門番が大きいモデルを呼ぶ先例は [R-39](v2-r39-judgment-share-research.md) §3・§5(等級 B・Evans & Stanovich の Table 1 と CLARION の MCS は親未確認)に、CoALA の 4 記憶・PIANO の並行モジュール・BDI の再考・Soar の impasse(当時は二次)・anytime は [R-41](v2-r41-cognitive-architecture-precedents.md) §1・§4・§5(等級 B・PIANO は親が逐語確認・CoALA 本文と Soar は親未確認)にある。本書は繰り返さずに引き、「状態の共有・調停・割り込み・保留・配列」の切り口だけを足す。Soar と CoALA は本書で本文を読み直した(§2-b-2・§2-c-1)。割り込みと中断・再開の研究(題 7-2)は別の答申の範囲なので、本書は認知アーキテクチャとエージェントの構成の中の割り込みの機構だけを扱う。

## §0 要旨

1. 「速い過程が既定の答えを出し、遅い過程が介入する」形(default-interventionist)は Evans & Stanovich が自説の型と明言している [S24]。Evans 2008 はこれと並べて「並列で競う」形(Sloman 型)を挙げ、「事前に決める」形も Evans 2007 にある [S25][S26]。De Neys 2023 は、両者を「片方しか出せない答えがある(exclusivity)」と「切り替えの仕組み(switch)」の 2 点で批判した [S29]。
2. 認知アーキテクチャはどれも、共有の作業記憶と直列の 1 点を持つ。ACT-R は 1 塊のバッファと 1 回 50 ms の産出規則 [S2][S3]、Soar は約 50 ms の決定サイクル [S1]、LIDA は 260〜390 ms の周期で、意識の放送と行動の選択だけが直列になる [S6]。
3. 調停の規則は 9 つの型に分けられる(§5)。固定優先・効用の最大・区分と区分内の 2 段・既定と介入・並列の競争・知識不足で上げる(Soar の impasse)・成功率で確率的に選ぶ(CLARION)・閾値の蓄積・事前に決める。今のアービタは「固定優先 4 級+級の中は待ち時間」で、2 段の型に当たる。
4. Soar は遅い過程を割り込みに強く作っている。substate(遅い熟考)の最中も決定サイクルは全段で回り続け、知覚が変わって上の段で決定ができれば impasse は解け、substate は結果だけを残して消える [S1]。
5. LLM エージェントでは Talker-Reasoner が題 9 の形に最も近い。速い Talker は共有の記憶から最新の信念を読み、古いままでも答える。遅い Reasoner は信念(JSON の型)を書く。待つかどうかは信念の欄(助言の段)で決まる [S14]。SwiftSage は遅い側へ上げる条件を 4 つ書き、遅い側の出力を行動の待ち行列にして、空になったら速い側へ戻す [S15]。
6. Generative Agents は世界の刻みごとに LLM が「計画を続けるか反応するか」を決め、反応したらその時刻から計画を作り直す。振り返りは重要度の和が 150 を超えたときに起きる [S13]。CoALA は決定サイクルを「案を出す・評価する・選ぶ→実行」と書くが、非同期や割り込みの語は本文に無い [S12]。
7. ゲーム AI の実務は「反応と熟慮を 1 つの模型にまとめない」。Côté は Action Selector が両者を切り替え、反応は割り込みで、熟慮は「終わった・文脈が無効になった」で動くと書く [S16]。Unreal の BT は事象で動き、条件の観測者が下位の処理を打ち切る [S22]。
8. 効用の調停は配列にそのまま乗る。IAUS 型は 0〜1 の考慮を応答曲線に通して掛け、0 で即座に候補から外す [S17]。Dill の 2 段(区分の順位→区分内の重みで抽選)[S18] と DA:I の点の帯(基本 10・攻撃 20〜40・支援 25〜45・反応 50〜70)[S19] は、今のアービタの「級→級の中」と同じ形をしている。Sims は物が欲求ごとの効き目を広告し、幸福を最大にする行動を選ぶ [S23]。
9. 35 万体の配列に乗るのは、固定次元の数値の欄(欲求・集中・顕著性・区分の順位・効用の積・閾値の蓄積・停滞の数)と、それに対する比較・argmax・lexsort・種つきの抽選である。乗らないのは、可変の構造(Soar の状態のグラフと substate の段・規則の照合)、自然言語の記憶の流れ、LLM の出力そのものだ。50 ms の周期を 35 万体で回すと、世界の 1 秒に 700 万回になる【見立て】。
10. 今の形との主な差は 3 点(§7-3)。「考えている最中」という体の状態が無い(返事待ちの体にも再送が起き、不応期が割り込みの代わりをしている)。考えかけの途中の結果を持たない。速い過程(判断モデル)が未実装で、調停が呼びの予算の装置を兼ねている。§8 に題 9 の副問 9 つを選択肢と根拠つきで並べた(推薦なし)。

## §1 問いと前提

### 1-1 問い

[指示書 11-03](../design/prompt-2026-11-03-reply3.md) §7-1: 「速い過程と遅い過程が状態を共有し、調停で誰が答えるかを決める」形が、二重過程の理論・認知アーキテクチャ・LLM エージェントの構成・ゲーム AI でどう書かれているか。共有の状態の中身・調停の規則・割り込みの扱い・考えかけの保留を調べ、35 万体を配列で回す前提で写せるかを見る。

- 注: 発注文は「R-133 §9 の題 9」と書くが、R-133 §9 の表は題 1〜8 の 8 題で、題 9 の行は無い。題 9(心のモジュール)は 11-03 §5(「題 8・9・10 の後」)と [v3 の核の設計書](../design/v3-core-design-2026-11-03.md) の表の 9 行目(「未決・R-135 の材料の後」)に出る。本書は後者を題 9 として扱う。

### 1-2 本プロジェクトの前提(読んだもの)

| 前提 | 中身 | 場所 |
|---|---|---|
| 背骨の文(K2) | 知覚・記憶の強さ・変化の検出は System 1(コード)、日常の判断は判断モデル、会話とよく考える判断は LLM。LLM を呼ぶかは判断モデルが決める | CLAUDE.md §3・[用語集](../design/v2-glossary.md) 105 行(10-12 §2 の 1・§4-7) |
| 呼び出し(旧: 起床) | エンジンが体の判断を LLM に求めること。呼び出しの種類は「会話」「計画の切れ目」「個体の変化」「場所の変化」の固定優先 4 種 | 用語集 74〜76 行 |
| 集中の度合い | 考えている最中は集中の値を持ち、新しい刺激は顕著性が集中を上回るときだけ割り込む。不応期(予算の装置で、人の性質ではない)の置き換え先。実装まで不応期は宣言つきで残す | 用語集 320 行・[回答 11-01](../design/v2-answers-2026-11-01.md) §10-1 |
| 起床の門(#66〜68) | 検出は L1 に残す。「考え直すか」は L1.5(DM8)、中身は L2。域外の人は「範囲外の層ができるまで思考は無い」 | 11-01 §10-1・[routing](../reference/decision-routing-2026-11-01.md) §6-2 |
| 上げる規則の決定例 | 手伝う・通報する(#55・56)は判断モデルが判断し、分布が拮抗したら LLM へ上げる(腕は「移行の閾値」) | 11-01 §10-1 |
| 判断モデルの今 | 第 1 世代=公開重みの判断モデル(無学習)。いま既定で動く判断のうち判断モデルは 0 件 | 11-01 §0-3・§11 |
| 知見の 5 区分 | 式・入力・錨・知識・初期化。錨の量を動かす側に入れない。比較の表には「現実との整合」の列を必ず付ける | 11-01 §0-1・§0-2・§0-8 |
| v3 の題 3・4 | 活性の境目 (A1)〜(A3)・予定と反応の判断の線 (D1)〜(D3)・先読み (P1)〜(P3)・上書き (O1)〜(O3) | [R-133](v2-r133-event-driven-core-design-options.md) §3〜§4(等級 B) |
| 背圧の ③ ④ | 熟考に入るとき判断モデルが集中 f を出し、刺激の顕著性 s が f を超えたら割り込み、超えなければ溜めて返事の適用の直後に 1 回だけ起こす。割り込まれた考えの返事は「考えかけたこと」として記憶とテープに残す。Lavie らの結果(作業記憶の負荷で妨害が増える)を注意点に挙げる | [R-128](v2-r128-backpressure-design-pdes-watermarks.md) §7 ③ ④(親の一次確認 第340 あり・先例の引用は親未確認) |
| v3 の仮決定 | 題 1=(G2) ナノ秒で持ち 1 秒の格子で束ねる・題 2=(Q3) 体ごとの次の時刻の欄+世界の列。事象の型に「判断モデルの判断」「割り込み」を足す | 11-03 §4 |

### 1-3 今の形(docstring とコードを HEAD で読んだ)

- **速い過程=System 1 の検出**(`engine/change_detect.py` の docstring): (i) 所属セルの B4 欄(密度段・騒音段・流れ・顕著行為)のハッシュ変化、(ii) B5 変化のうち内受容の閾値の跨ぎ(段 4/7/9・ヒステリシス 1 段)を検出して「起床候補」を作るだけ。知人出現・近接の入れ替え・被注視・傍受は検出しない。「push 禁止・pull-on-wake」で、検出器は世界にも体にも書かない(書き手は resolve だけ)。
- **調停=繰り延べアービタ**(`engine/arbiter.py` の docstring): 4 級の固定優先(会話ターン > 計画境界 > 個体変化 > セル変化)。級の中は待ち時間の降順。`T_MAX_TICKS`(会話 3/計画境界 10/個体変化 30/セル変化 60 刻み・expedient)を超えると累積で昇格する。同じ体の保留中の起床は 1 呼にまとめ、刻みあたりの呼数(L4 の按分)で頭打ちにし、なお足りなければ下位 2 級を縮退で実行する。不応期は体×条件ごとの表(`agents/state.py:306` の `REFRACTORY_MINUTES` 11 行。会話 0・睡眠中 360・就業中 150・一般 60・移動 15・内受容 45 分ほか。多くは expedient)。就寝抑止(D-56)は寝ている体の候補をアービタの前で落とし、計画境界・顕著行為・会話だけを通す。整列の鍵は `(eff_class 昇順, 待ち tick 降順, pk 昇順, agent_id 昇順)` で、入力の並び順に依らない純関数(逐次ループは級の数 4 だけ)。
- **遅い過程=LLM**: δ_think のレーン表(L1=2.6 秒 … L3=300 秒)を分の刻みに切り上げる(`engine/llm_bridge.py:181`)。返事は `pending_apply` に入り、刻み T に出した呼びは T+1 の ① で適用される(`engine/run.py` の docstring)。
- **共有の状態**: 体の配列(`AgentState` の activity・内受容の段・`refractory_until (n,11)` ほか)と、セルの配列(B4 欄)。LLM へは描画した文(B0〜B6)を渡す。
- **考えている最中の扱い**: 体の状態として「考え中」の印は無い。艦隊の道では、返事を待っている体にも同じ刻みで再び呼びを出せる(`engine/systems/decide.py:176-178` は再送を `n_fleet_resent` に数えるだけ)。R-128 §7 ① はこれを「体ごと 1 本」の検査に変える案を出している。
- **保留**: 保留するのは起床の候補(アービタの `_pending`。「抑止された起床は破棄ではない=次回の起床時に最新の状態を読む」)。考えかけの途中の結果は持たない。
- 【推測】mock では δ_think が 1 刻みなので、「考えている最中に新しい刺激が来る」場面は刻みの中に畳まれ、表に出ない(R-128 §7 の末尾と同じ読み)。

## §2 先例ごとの節

### 2-a 二重過程の理論

**a-1 Kahneman(System 1/2・監視と追認)**

- Nobel 講演(2002)と AER 2003 の改訂版で、System 2 の役目の 1 つは心の操作と行動の質の監視であり、明示の判断は少なくとも受け身では System 2 に「追認(endorse)」される。ただし監視は普段は緩く(lax)、誤った直感の判断も多く通る、と書く [S28 △=検索の要約。講演の PDF は 403 で読めなかった]。
- Talker-Reasoner §1 は Kahneman 2011 を逐語で引く: 「System 1 operates automatically and quickly, with little or no effort and no sense of voluntary control.」「System 1 continuously generates suggestions for System 2: impressions, intuitions, intentions, and feelings. If endorsed by System 2, impressions and intuitions form the basis of the explicit beliefs of System 2」 [S14 ◎ の中の引用=Kahneman 本は ○]。
- 写すと: 速い過程は常に動いて提案を出し、遅い過程は監視して追認か修正をする。監視は安く常時、介入はまれ(De Neys & Glumicic の「監視は常に成功・介入はまれ」=※既存答申 R-39 §3-2・等級 B・抄録は親が確認)。

**a-2 Evans & Stanovich(既定と介入型)**

- 要旨(Europe PMC で読んだ): 「Our preferred theoretical approach is one in which rapid autonomous processes (Type 1) are assumed to yield default responses unless intervened on by distinctive higher order reasoning processes (Type 2). What defines the difference is that Type 2 processing supports hypothetical thinking and load heavily on working memory.」[S24 ○]
- 本文の「default-interventionist in structure (a term originally coined by Evans, 2007b)」と Table 1 の定義的特徴は ※既存答申 R-39 §3-1(等級 B・Table 1 は親未確認)。
- 定義は速さではない。Type 2 を分けるのは「仮説を立てて考えること(認知的デカップリング)と作業記憶の負荷」で、速い・遅いは相関にすぎない(R-39 §3-1)。

**a-3 Evans 2007・2008(3 つの型)**

- Evans 2008 の要旨: 「some dual-process theories are concerned with parallel competing processes involving explicit and implicit knowledge systems, others are concerned with the influence of preconscious processes that contextualize and shape deliberative reasoning and decision-making.」[S25 ○]
- Evans 2007「On the resolution of conflict in dual process theories of reasoning」は、葛藤の解き方として parallel-competitive・default-interventionist・pre-emptive conflict resolution の 3 つを並べたとされる。読めたのは要旨の冒頭だけ: 「The pre-emptive conflict resolution model assumes that a decision is made at the outset as to whether a heuristic or analytic process will control the response.」[S26 △=検索の要約。出版社の頁は 403]
- 写すと 3 型: (i) 並列で競い、葛藤が出たら解く (ii) 速い方が既定、遅い方が介入するかもしれない (iii) 最初にどちらが答えるかを決める。

**a-4 Sloman 1996(並列の 2 系)**

- 『Heuristics and Biases』の再録の章の冒頭(Cambridge Core の要約で読んだ): 「whether people are best conceived as parallel processors of information who operate along diffuse associative links, or as analysts who operate by deliberate and sequential manipulation of internal representations.」「the two minds do not always agree.」[S27 ○]
- 要旨(検索の要約): 1 つは連合的(類似と時間の近さの構造で計算)、もう 1 つは規則にもとづく(記号の構造の上で計算)[S27 △]。2 系が同じ入力に同時に矛盾する答えを出す、という基準(Criterion S)の本文は読めなかった(§10)。
- 写すと: 2 系は同じ入力に同時に走り、答えが食い違うことがある。

**a-5 De Neys 2023(批判と組み直し)**

- 要旨: 批判の的は「exclusivity」(ある答えは遅い過程にしか出せないと考える傾向)と「switch」(どうやって遅い過程へ切り替えるかの仕組み)の 2 点。主要な切り替えの説明は exclusivity を前提にしているので概念上の問題がある、と述べ、より成り立つ二重過程のアーキテクチャの土台を描く [S29 ○]。本文(不確かさの監視と閾値の模型と読まれている所)は有料で読めなかった(§10)。
- 写すと: 「遅い過程でしか出せない答え」を前提にした調停は、心理学の側で疑問が出ている。速い過程も同じ種類の答えを出しうる。

**a-6 既存答申の材料(引くだけ)**

- 監視の手がかり: 葛藤(Botvinick 2001・二次)・FOR(Thompson 2011・抄録)・精度の重み(Clark 2013・原典)。6 項の重みつき線形和の先例は無い(※既存答申 R-41 §1-2・§1-3・等級 B)。
- 調停の神経の手がかり: model-based と model-free の制御の割り当ては「それぞれの予測の信頼度の関数」(Lee ら 2014・抄録)。2 系が最適になる条件は環境の変動とメタ推論の費用で決まる(Milli ら 2017・親が逐語確認)(※既存答申 R-39 §5-1・§5-2・等級 B)。

### 2-b 認知アーキテクチャ

**b-1 ACT-R(モジュールとバッファ・手続き記憶の競合解決)**

- 要旨(Anderson ら 2004): 「These modules place chunks in buffers where they can be detected by a production system that responds to patterns of information in the buffers. At any point in time, a single production rule is selected to respond to the current pattern. Subsymbolic processes serve to guide the selection of rules to fire as well as the internal operations of some modules.」[S2 ○]
- バッファ: 「Each module is connected to a set of buffers that can hold at most one chunk at a time.」手続きモジュールは宣言的知識のうち「the chunks that are in the buffers」だけに触れる [S3 ◎ §2.1]。
- 時間と直列: 「After a rule has been selected, it takes a certain time (usually 50 ms) for the rule to fire. … During that time the procedural module is blocked and no rule can match.」要求は並行: 「During that time, other rules still can fire, i.e. requests are executed in parallel. However, a module can only process one request for a buffer at the same time.」[S3 ◎ §2.3]。「Only one matching production rule can fire at a time.」[S4 ◎ §3]
- 競合解決: 規則の効用は「dynamic, learned rule priorities」[S3]。ACT-R 6 の学習は Rescorla-Wagner 型 `U_i(n) = U_i(n−1) + α(R_i(n) − U_i(n−1))`。報酬は「the difference of the external reward and the time between the selection of the rule and the triggering of the reward」で、雑音を足すと効用の低い規則も発火できる [S4 ◎ §3.2.1]。既定の α の値と雑音の分布は公式の手引き(act-r.psy.cmu.edu)が接続を拒んで読めなかった(§10)。
- 並行の課題: threaded cognition は「streams of thought can be represented as threads of processing coordinated by a serial procedural resource and executed across other available resources」で、専用の実行系なしに資源の衝突を解くと要旨に書く [S5 ○]。
- 割り込みの扱い: 専用の割り込みの機構は無く、知覚のモジュールがバッファに入れた塊に次の規則が反応する形で表れる【見立て】(公式の手引きは読めていない)。

**b-2 Soar(決定サイクル・impasse と substate・chunking)**

Laird 2022 の全文を読んだ [S1 ◎]。

- 決定サイクル: 入力 → 精緻化(提案と評価)→ 演算子の選択 → 適用 → 出力。精緻化の段では規則が並列に発火し、取り消しも並列に起きる(「new firings and retractions occur in parallel」)。発火が止まると「quiescence is reached」で選択へ進む(§2.1〜§2.2)。
- 状態の共有: 作業記憶は「goals, data retrieved from long-term memories, information from perception, results of internal operators」を持ち、「Soar does not have any predefined structure for the contents of working memory except for the buffers that interface to other modules」。演算子を選ぶための特別な構造が選好(preference)で、提案の規則が「acceptable」を、評価の規則が相対(A は B より良い)・絶対・数値の選好を作る(§2・§2.2.3)。
- 調停: 「a fixed decision procedure processes the contents of preference memory to choose the current operator. … If the preferences are inconclusive or in conflict, then no operator is selected, and an impasse arises」(§2.3)。適用の途中も「the decision procedure is rerun after each wave to ensure that the current operator should stay selected」(§2.4)。
- impasse の 3 型(§3): state no-change(提案が無い)・operator tie/conflict(選好が足りない・食い違う)・operator no-change(同じ演算子が続く=適用の知識が無いか、外界で時間がかかる)。
- substate(遅い熟考): impasse で上の状態につながる substate ができ、「its own preference memory and the ability to select and apply operators without disrupting any of the processing in superstates」。上の状態の構造はすべて読めるが、知覚と運動のバッファは持たない(外界とのやり取りは最上段を通す)。「Execution time can be monitored in the substate so that a non-optimal (or even random) decision can be made if time is an issue.」(§3)
- 割り込み: 「The decision cycle remains active across all states, and an impasse is resolved whenever a new decision is possible in a superstate, either through the creation of new preferences or through changes in the state (including changes in perception) … When an impasse is resolved, the substate terminates and all non-result substate structures are automatically removed. Through this approach, Soar agents remain reactive to relevant changes in their environment, even when there are many active substates.」(§3)
- 保留: substate の結果のうち、上の状態の精緻化は「persists only as long as the superstate structures responsible for its creation exist」、上の演算子の適用(運動の命令など)は取り消されない(§3)。
- chunking: substate で結果ができるたびに自動で走り、処理の履歴から「上の状態のどの構造が要ったか」を条件、結果を行動とする規則を作る。「converts deliberate, sequential reasoning into parallel rule firings」。制約: 「chunking requires that substate decisions be deterministic」(§4)。
- 時間: 「Empirical evidence is that a decision cycle time of around 50 msec. is required for real-time behavior.」(§10 の 3)
- R-41 §5 の「Soar の impasse は二次」は、本書で原典を読んだ。impasse の型は 3 つ(tie と conflict を 1 つに数える)で、R-41 の 4〜5 型の数え方とは違う。

**b-3 LIDA と全体作業空間(GWT)**

- GWT の要旨(Baars 2005): GW 理論は認知アーキテクチャの伝統から出た。Newell らが「blackboard」型の構成の有用性を示し、Baars が意識と結びつけた [S8 ○]。
- 周期: 「One cognitive cycle would therefore take 260–390 ms.」(知覚 80〜100 ms・意識の放送 200〜280 ms・行動の選択 60〜110 ms)。「Cycles can cascade as long as they preserve the seriality of consciousness.」[S6 ◎]。2007 の論文は「cognitive cycles occur five to ten times a second in humans」と書く [S7 ◎]。
- 共有の状態: 知覚(PAM の節)が作業空間(Workspace=前意識のバッファ)に入り、エピソードと宣言の記憶から連想が呼ばれて長期の作業記憶に置かれる。作業空間は「the agents current understanding of its immediately perceived environment」[S6 ◎]。
- 調停(注意の競争と放送): 注意のコードレットが作業空間から「novel, relevant, urgent, or insistent」な内容を連合にして全体作業空間へ運び、競争に勝った連合が意識として放送される。放送の引き金は 3 つ: 連合の活性の和が閾値を超える・1 つの連合が別の閾値を超える・前の放送から時間が経ちすぎた(200 ms に設定)[S6 ◎ Methods の Parameters]。放送に応えて手続き記憶の scheme が行動の選択へ入り、行動の選択が 1 つを選ぶ。選ぶたびに期待のコードレットができ、結果が期待と違えば意識へ持ち上げる [S6 ◎]。
- 並列と直列: 「The components operate asynchronously」「The only points in the cognitive cycle where seriality is enforced are the conscious broadcast and the action selection process」[S6 ◎]。
- 遅い過程: 熟慮・意志による決定・定型でない問題解決は「occur over multiple cognitive cycles」。意志の決定は James の観念運動説で、提案のコードレットが案を意識に上げ、決められた時間のうちに反対や別の提案が出なければ timekeeper のコードレットが決める。反対や新しい提案が出れば計時を止めるかやり直す [S7 ◎]。定型でない問題解決は「a unique behavior stream operating over multiple cycles, with the shaping of partial plans of action at each cycle」[S7 ◎]。
- 学習: 放送の後に知覚・エピソード・手続きの学習が始まり、「the conscious content determines what is to be learned」[S6 ◎]。

**b-4 CLARION(明示と暗黙の 2 層)**

- 構成: 4 つの下位系(行動中心 ACS・非行動中心 NACS・メタ認知 MCS・動機 MS)。各系の上の層は明示の知識(取り出しやすい)、下の層は暗黙の知識(取り出しにくい)。下の層は試行錯誤で少しずつ学び、上の層は 1 回で学ぶことが多い [S9 ◎]。ACS の上の層は「State → Action」の規則、下の層は多層パーセプトロン(Q 学習)[S9 ◎]。
- 判断の手順: ① 状態を見る ② 下の層で各行動の値を計算して確率的に 1 つ選ぶ ③ 上の層の規則から確率的に 1 つ選ぶ ④ 両層の結果を確率的に選ぶか組み合わせる ⑤ 実行して報酬を見る ⑥ 下の層を Q 学習で更新 ⑦ 上の層の規則を作る・直す・消す ⑧ ① へ [S10 ◎ 5 枚目]。
- 層の統合の 4 法: 確率的選択(各規則群と下の層を確率 P_RER・P_IRL・P_FR・P_BL=1−… で使う)・組み合わせ(上の層の活性と下の層の Q 値を足してボルツマン分布で選ぶ。上の層の否定は下の層の推薦を拒否できる)・下から上の修正(下の層の結果を上の層が直す。重みつきの和など)・上から下の誘導(上の層の結果を下の層が使う。熟練の遂行で起きやすい)[S10 ◎ 54〜60 枚目]。確率は固定でも可変でもよく、可変なら成功率に比例させる「probability matching」。決定論的な選択はその特別な場合で、MCS が選べる [S10 ◎ 56〜57 枚目・R-39 §5-3]。
- 下から上の学習(RER): 下の層が決めた行動が成功したら規則を作って上の層へ足し、以後の成否で条件を一般化・特化する(閾値 `threshold_RER`)[S10 ◎ 34〜36 枚目]。
- 要旨(Sun ら 2005): 暗黙と明示の相互作用(相乗の効果を含む)を扱い、「first learning implicit knowledge and then explicit knowledge」の下から上の道を主張する [S11 ○]。
- 時間の単位: 手引きの範囲では周期の秒は書かれていない(§10)。

### 2-c LLM エージェントの構成

**c-1 CoALA(Sumers ら 2023)**

TMLR 版(arXiv v3)の全文を読んだ [S12 ◎]。

- 作業記憶: 「Working memory maintains active and readily available information as symbolic variables for the current decision cycle … CoALA's notion of working memory is more general: it is a data structure that persists across LLM calls. On each LLM call, the LLM input is synthesized from a subset of working memory」(§4.1)。長期の記憶はエピソード・意味・手続きの 3 種(R-41 §4-1 と同じ)。
- 決定サイクル: 「In each cycle, program code defines a sequence of reasoning and retrieval actions to propose and evaluate alternatives (planning stage), then executes the selected action (execution stage)」。案を出す・評価する(発見的な規則・perplexity・学んだ値・LLM の推論)・選ぶ(argmax・softmax・多数決。全部を退けて案を出す段へ戻ることもある)(§4.6)。
- Soar との対応を明示する(§2〜§3)。ただし本文に「asynchron」「interrupt」「concurren」の語は無かった(全文の grep で 0 件)。調停は 1 本の「main」の中の手続きで、速い過程と遅い過程の並走は枠組みに入っていない【見立て】。

**c-2 Generative Agents(Park ら 2023)**

arXiv v2 の全文を読んだ [S13 ◎]。

- 共有の状態=記憶の流れ: 各記録は「a natural language description, a creation timestamp, and a most recent access timestamp」。検索の点は最近さ(最後に引いてからのゲームの時間の指数減衰・「Our decay factor is 0.995」)・重要度(1〜10 を LLM が付ける)・関連(埋め込みのコサイン)を min-max で 0〜1 に揃え、「all αs are set to 1」で足す(§4.1)。
- 振り返り(遅い過程の 1): 「when the sum of the importance scores for the latest events perceived by the agents exceeds a threshold (150 in our implementation)」。実際には 1 日に 2〜3 回(§4.2)。
- 計画(遅い過程の 2): 1 日を 5〜8 の塊で描き、1 時間の塊、さらに 5〜15 分の塊へ再帰で分ける。計画も記憶の流れに入り、検索の対象になる(§4.3)。
- 反応と計画の更新(調停): 「at each time step, they perceive the world around them … We prompt the language model with these observations to decide whether the agent should continue with their existing plan, or react.」反応したら「We then regenerate the agent's existing plan starting from the time when the reaction takes place.」(§4.3.1)。調停そのものを LLM が刻みごとに行う。
- 世界との同期: 刻みごとに体の出力で JSON を更新して次の刻みへ進む(§5)。刻みの秒は本文で見つからなかった(§10)。

**c-3 PIANO(Project Sid)**

※既存答申 R-41 §4-2(等級 B・親が逐語確認)を引く。遅い過程(振り返り・計画)が直ちの脅威への反応を妨げない。各モジュールは「a stateless function that reads and writes to a shared Agent State」。Cognitive Controller がボトルネックを通して情報をまとめ、決定を他のモジュールへ放送する。10 のモジュールが並行に走り、反射は小さな非 LLM のネット。古くなった結果と中断の機構は本文に無い。

**c-4 Talker-Reasoner(Christakopoulou ら 2024)**

arXiv v1 の HTML 全文を読んだ [S14 ◎]。

- 速い過程と遅い過程: Talker(System 1)は利用者と話し、観測を取り、記憶で応答を準備する。Reasoner(System 2)は多段の推論と計画・道具の呼び出し・信念の形成を行う。
- 共有の状態: 「the main way the Talker (System 1) and Reasoner (System 2) interact is through memory. The Reasoner is responsible for generating the next belief state … and storing them in memory. Any time the Talker needs the belief, it retrieves the latest one from memory.」信念は「structured language objects living in XML or JSON space」。睡眠の助言の例では、臨床家と決めた欄(困りごと・目標・習慣・障壁・寝室の環境)と助言の段(理解・目標設定・計画)を持つ(§3〜§4)。
- 古い状態で答える: 「The Talker therefore might operate with a delayed view of the world, as the Reasoner might not have had time to generate the new belief」「It may use beliefs b_mem that are not the latest b_{t+1} of the Reasoner in order to ensure fast interactivity」。
- 調停(待つか): 「The Talker can also wait for the Reasoner before generating a response; this is equivalent to System 2 taking over and overruling System 1's impulses.」実装では「Whether the Talker waits for the Reasoner to finish is determined by the belief—in the planning coaching phase the Talker waits, otherwise it does not.」待たずに答えて外した例を「Snap judgement Talker」と呼ぶ(§4.3)。
- 時間: 1 回の会話の番ごと。Reasoner は番と番の間に n 段考える(n は回ごとに違う)。遅延の秒の数値は無い。
- 今後の課題として「the Talker should automatically determine whether it requires System 2 reasoning」と書く(§5)=待つかの判断を速い側に持たせる案(本プロジェクトの「LLM を呼ぶかは判断モデルが決める」と同じ向き)。

**c-5 SwiftSage(Lin ら 2023)**

arXiv v2 の全文を読んだ [S15 ◎]。

- 速い過程=Swift(専門家の軌跡で微調整した小さな encoder-decoder)。遅い過程=Sage(GPT-4 で下位目標の計画と接地)。
- 上げる条件(§3.4): 「1) Stuck: There are K=5 consecutive time steps with zero reward」「2) Invalid: The SWIFT's prediction for the next action is invalid in the current environment」「3) Critical: … involves a critical decision」「4) Unexpected: The observation … suggests that an exception is encountered」。
- 保留=行動の待ち行列: Sage の出力は行動の列(action buffer)になり、順に実行して「revert to the SWIFT module when the buffer is empty」。付録では「If two consecutive actions are invalid or cause exceptions, we halt and revert to SWIFT」。
- 切り替えの判断を学習させるのは今後の課題と書く。

**c-6 その他(引くだけ)**

RRARA の Time Conversion Mechanism(推論の時間をシミュの経過時間に換算)・DPT-Agent(System 1=有限状態機械+コード・System 2=心の理論+非同期の振り返り)は ※既存答申 R-41 §4-3・R-39 §5-4(抄録のみ)。

### 2-d ゲーム AI

**d-1 反応と熟慮を分ける(Côté・Game AI Pro 第 11 章)**

全文を読んだ [S16 ◎]。

- 反応と熟慮の起き方が違う: 「For reactivity, triggering reactions is caused by interruptions that have a higher priority than what is currently ongoing. For deliberation, the need for a decision comes from two different sources: (1) the current deliberate action (or reaction) is completed and a new action must be engaged, and (2) the current context is changed in a way that it is invalidating or canceling the current action or plan of actions.」
- 目的も違う: 反応は「instantaneous changes in action」、熟慮は「the best action possible that can be sustained for the longest time possible」。視線が切れるたびに追跡と巡回が入れ替わる振動は、ヒステリシスなどの濾過をした論理の表現で防ぐ。
- 調停: Action Selector が Deliberation と Reactivity の切り替えを担い、「signal the Deliberation module when a new decision must be taken or to cancel the current deliberate action in order to execute a reaction」。反応の中の優先: 無意識の反応は認知的な反応より上・同時の無意識の反応は組み合わせられる・認知的な反応は危険の予期の度合いで変わる(図書館の大きな音と工事現場の大きな音)。
- 結論は「反応と熟慮を 1 つの決定の模型にまとめると、性質の正反対のものを表すことになる」。

**d-2 utility AI(IAUS・Lewis・Game AI Pro 3 第 13 章)**

全文を読んだ [S17 ◎]。

- 『Guild Wars 2: Heart of Thorns』の実装は Mark 2013 の Infinite Axis Utility System にならう。行動ごとに決定の点の評価器(DSE)があり、「During a think cycle, each DSE for an agent is scored, and the best-scoring option determines the action」。
- 考慮の積: 各考慮は「a raw numeric input, normalized to the interval [0, 1]」で、応答曲線で写し直してから「These scores are then multiplied together」。「any consideration can disqualify an entire decision from being selected simply by scoring zero」で、0 が出たら残りの考慮を計算せずに次へ進む(安い考慮を先に並べて省ける)。
- 振動の対策: 点が近い 2 つの決定が入れ替わり続けるとき、直前に選んだ決定に「commitment bonus」(小さな上乗せ)を与える・重みを付ける・実行時間と冷却時間の考慮を使う。ただし「they do not eliminate the possibility of two decisions oscillating—they simply shift where the scores will land」。
- Dave Mark 本人の講演(GDC の録画)は読めなかった(§10)。

**d-3 2 段の効用(Dill・Game AI Pro 2 第 3 章)**

全文を読んだ [S18 ◎]。

- 絶対の効用(最高点を取る)と相対の効用(点に比例した抽選)を組み合わせる。各案は順位(rank)と重み(weight)を持つ。手順: ① 重み 0 の案を外す ② 最高の順位の区分だけを残す ③ 最良の重みよりずっと低い案を外す(任意) ④ 残りを重みで抽選する。
- 「divide your options into categories and select from among those categories using absolute utility … we can use relative utility to pick from among the options within the best category in a random but reasonable way」。

**d-4 点の帯(Hanlon & Watts・DA:I・Game AI Pro 3 第 31 章)**

全文を読んだ [S19 ◎]。

- 表 31.1: 基本 10(何もしないよりよい)・攻撃 20〜40・支援 25〜45・反応 50〜70(「respond to specific and immediate execution criteria (typically responding to an imminent threat …); if these criteria are present these actions should be executed in priority over any other」)。帯の重なりで「同じ切迫度なら支援が攻撃より上」を表す。
- 評価は「typically repeated on every AI update pass, but can be performed as often as appropriate」。評価の結果は保持しなくてよい(実行は最高点の行動と的だけを使う)。

**d-5 behavior tree の割り込みと層の混在**

- Unreal の BT(公式の文書 [S22 ◎]): 「Unreal Engine Behavior Trees are event-driven to avoid doing unnecessary work every frame … the Behavior Tree passively listens for "events"」。黒板の鍵が変わると「any lower priority Task to be aborted in favor of executing our left-most branch which has higher priority」。条件は Decorator に置き、「Observer Aborts」で値を見張って打ち切る。並列のノードの代わりに Simple Parallel と Service を使う。
- 効用の選択子を BT に入れる(Merrill・Game AI Pro 第 10 章 [S20 ◎ 一部]): BT の優先は「static … baked right into the tree」。子の効用で動的に順を決める utility selector を足す。
- BT と計画の混在(Hilburn・Game AI Pro 第 8 章 [S21 ◎ 一部]): 世界の状態の模型と評価の式を持ち、BT の各ノードを模擬して枝を選ぶ。
- GOAP(Orkin の F.E.A.R.)の原典は読めなかった(著者の頁が 404)(§10)。

**d-6 The Sims の欲求と自律(Forbus & Wright)**

全文を読んだ [S23 ◎]。

- 物が行動を持ち、各行動は実行の手続き・可能かの検査・広告(どの欲求をどれだけ満たすか)を持つ。「Sims (not under direct player control) choose what to do by selecting, from all of the possible behaviors in all of the objects, the behavior that maximizes their current happiness.」選んだ手続きは Sim 自身のスレッドで走る。
- 広告の欄: 距離での減衰・誰に広告するか・欲求(energy・comfort・hunger・hygiene・bladder・room・social・fun・mood)ごとの範囲(トイレは Bladder に 0〜70)・性格による線形の伸縮(水槽の餌やりは Playful の点で Fun に 1〜11)。「Allow Consecutive」は待ち行列に入れられる印。
- 実行の基盤は協調型(横取りしない)のマルチタスクで、「it is important to include explicit global checks in your code to avoid blocking」。割り込みの機構の記述は本文に無かった。
- 注意: 広告を強くすると同じ行動が繰り返され、初期の Joy Booth は倒れるまで使われ続けた(調整の難しさ)。

## §3 比較の表

列: 速い過程/遅い過程/共有の状態/調停(誰がいつ答えるか)/割り込み/考えかけの保留/時間の単位/配列への写し(【見立て】)/出典。

| 先例 | 速い過程 | 遅い過程 | 共有の状態 | 調停 | 割り込み | 保留 | 時間 | 配列への写し【見立て】 | 出典 |
|---|---|---|---|---|---|---|---|---|---|
| Kahneman | System 1(自動・常時・提案) | System 2(監視・追認・修正) | 印象・直感・意図(表現は書かれていない) | 既定=System 1 を追認。監視は緩い | 監視は常時。介入はまれ | 書かれていない | 書かれていない | 監視=体ごとの安い検査、介入=呼び出しの分布 | [S28]△・[S14] の引用 |
| Evans & Stanovich | Type 1(自律) | Type 2(作業記憶・仮説) | 書かれていない | 既定と介入 | 介入する「かもしれない」 | 書かれていない | 書かれていない | 同上 | [S24]○・R-39 §3-1 |
| Evans 2007・2008 | 前意識の過程 | 熟慮 | 書かれていない | 3 型(並列の競争/既定と介入/事前に決める) | 型による | 書かれていない | 書かれていない | 型ごとに §5 | [S25]○・[S26]△ |
| Sloman | 連合の系(並列) | 規則の系(直列) | 同じ入力 | 2 系が同時に走り、答えが食い違う | 両方が走る | 書かれていない | 書かれていない | 両方を毎回走らせる=遅い側の費用が全員にかかる | [S27]○△ |
| De Neys 2023 | 直感 | 熟慮 | (本文未読) | 切り替えの説明を批判 | (本文未読) | (本文未読) | (本文未読) | — | [S29]○ |
| ACT-R | 規則の照合と発火(1 回 50 ms・直列) | モジュールへの要求(検索など。並行に走る) | バッファ(各 1 塊)・目的・宣言の記憶 | 照合した規則のうち効用(学習・雑音つき)最大を 1 つ | 次の規則がバッファの変化に反応【見立て】 | 目的のバッファ・目的の塊【見立て】 | 50 ms | 効用の argmax+種つきの雑音は乗る。規則の照合は体ごとの規則集合が違うと乗りにくい | [S2]○[S3][S4]◎[S5]○ |
| Soar | 精緻化の規則(並列に発火・取り消し) | substate での熟考(同じ機構の再帰) | 作業記憶のグラフ+選好の記憶 | 固定の決定手続きが選好で 1 つ選ぶ。足りなければ impasse | 決定サイクルは全段で回り続け、上の段で決定できれば substate は消える | 結果だけ残す。上の演算子の適用は取り消さない。chunking で規則に | 約 50 ms | グラフと substate の段は乗らない。「上で決められたら熟考を捨てる」規則は乗る | [S1]◎ |
| LIDA/GWT | 知覚・注意のコードレット・自動の行動 | 多周期の熟慮・意志(timekeeper) | 作業空間(前意識のバッファ)+全体作業空間 | 連合の活性の競争→勝者を放送→行動の選択が 1 つ | 周期が重なって走る。期待のコードレットが外れを持ち上げる | 多周期の行動の流れ・部分の計画 | 260〜390 ms(5〜10 回/秒) | 活性の和と閾値・200 ms の自動放送は乗る。コードレットの群は乗りにくい | [S6][S7]◎[S8]○ |
| CLARION | 下の層(MLP・Q 値) | 上の層(明示の規則) | 状態の入力(両層が同じ状態を見る) | 確率的選択・組み合わせ・下から上の修正・上から下の誘導。確率は成功率に比例も可 | 書かれていない | 規則の抽出(RER)で上の層へ移す | 書かれていない(1 歩=1 回の判断) | 確率と成功率は体×層の配列に乗る。MLP は束で回せる | [S9][S10]◎[S11]○ |
| CoALA | (区別しない) | 決定サイクルの計画の段 | 作業記憶(LLM の呼びをまたぐ変数) | 案→評価→選択(argmax・softmax・多数決)→実行 | 語が本文に無い | 作業記憶に置く | 決定サイクル | 選択の規則は乗る。作業記憶は欄を固定すれば乗る | [S12]◎ |
| Generative Agents | (区別しない。刻みごとに LLM) | 振り返り・計画 | 記憶の流れ(自然言語+時刻+重要度) | 刻みごとに LLM が「続けるか反応するか」 | 毎刻み LLM が判断 | 計画を記憶に置き、反応の時刻から作り直す | 世界の刻み(秒は本文に無し)・計画は 5〜15 分の塊 | 重要度の和の閾値は乗る。毎刻みの LLM は 35 万体で回らない | [S13]◎ |
| PIANO | 反射(非 LLM の小さなネット) | 目標・計画・振り返り | 共有の Agent State | Cognitive Controller のボトルネックで決め、放送 | 遅い過程が反応を妨げない(並行) | 書かれていない | 社会目標は 5〜10 秒ごと | 反射のネットは束で回せる。Controller は LLM | R-41 §4-2 |
| Talker-Reasoner | Talker(会話) | Reasoner(推論・計画・信念) | 記憶の中の信念(JSON の型)・計画 | 信念の欄で待つかを決める(計画の段は待つ) | Talker は待たずに古い信念で答える | 最新の信念を記憶に置く | 会話の番 | 信念の欄を固定すれば配列に乗る。「待つか」は欄の比較 | [S14]◎ |
| SwiftSage | Swift(小さな微調整モデル) | Sage(GPT-4) | 行動の履歴・観測 | 既定は Swift。4 条件で Sage へ | Sage の列の実行中に 2 回続けて無効なら止める | 行動の待ち行列。空なら Swift へ | 環境の 1 歩 | 停滞の数(連続 5 歩の報酬 0)・無効の印は体ごとの int と bool に乗る | [S15]◎ |
| Côté | 反応(規則・決定木) | 熟慮(FSM など) | 同じ刺激 | Action Selector が反応を優先し、熟慮を止めるか新しい決定を求める | 反応は割り込み。熟慮は終わりか文脈の無効化で | 書かれていない(熟慮の行動を止める) | 秒以下〜 | 反応の優先の表は int の順位で乗る | [S16]◎ |
| IAUS(Lewis) | — | — | 考慮の入力(0〜1) | 考慮の積の最大。0 で候補から外す。直前の決定に上乗せ | 毎 think cycle で再評価 | 持たない(上乗せだけ) | think cycle | (N 体×K 行動×C 考慮) の積と argmax。応答曲線は表の引き | [S17]◎ |
| Dill の 2 段 | — | — | 案ごとの順位と重み | 最高の順位の区分の中で重みの抽選 | — | — | 決定のたび | lexsort と種つきの抽選 | [S18]◎ |
| DA:I の帯 | 反応(50〜70) | 攻撃・支援(20〜45) | 評価の木の点と的 | 最高点(帯が級の役) | 毎 AI 更新で再評価 | 保持しない | AI 更新 | 帯=int の順位+帯の中の点 | [S19]◎ |
| Unreal BT | Decorator の観測者 | 木の実行(Task) | 黒板の鍵 | 左ほど優先。事象で再評価 | 黒板の変化で下位の Task を打ち切る | 打ち切った Task は捨てる【見立て】 | 事象 | 黒板=体×鍵の配列。観測は「鍵が変わった体」だけの処理 | [S22]◎ |
| The Sims | 欲求の減衰(体の過程) | 行動の選択 | 欲求の値・物の広告 | 幸福を最大にする行動(距離で減衰・性格で伸縮) | 書かれていない(協調型) | 待ち行列(Allow Consecutive) | 書かれていない | 体×欲求の配列・物×広告の表・積和の argmax は乗る | [S23]◎ |
| 今の v2 | System 1 の検出(B4・内受容) | LLM(判断モデルは未実装) | 体の配列+セルの配列・描画の文 | アービタ: 4 級固定優先→級の中は待ち時間・昇格・予算で頭打ち | 不応期で抑える。考え中の印は無い | 起床の候補の保留だけ | 60 秒の刻み | 既に配列(純関数) | §1-3 |

## §4 共有の状態の中身の候補(先例から)

| # | 中身 | 表現 | 誰が書くか | 先例 | 配列への載り方【見立て】 |
|---|---|---|---|---|---|
| ST1 | 容量 1 のスロット(今の目的・今の検索結果・今の視野) | 種類つきの塊 1 つ | 各モジュール(要求の結果)と規則 | ACT-R のバッファ [S3] | 体×スロットの固定の欄。塊の中身を固定の型にすれば乗る |
| ST2 | 状態のグラフと選好 | 識別子・属性・値の木+acceptable・相対・数値の選好 | 精緻化の規則(取り消しつき) | Soar [S1] | 可変の構造なので乗らない。選好のうち数値の部分だけなら体×候補の配列 |
| ST3 | 前意識の作業空間と全体作業空間 | 知覚の節・連想・連合と活性 | 知覚・連想・注意のコードレット | LIDA [S6] | 活性(体×候補の float)と閾値は乗る。節の構造は乗りにくい |
| ST4 | 二層の知識(明示の規則/暗黙の値) | 規則の表+MLP | 両層とも学習で書く | CLARION [S9][S10] | 下の層の MLP は束で回る。規則の表は体ごとに長さが違う |
| ST5 | 作業記憶の変数 | 記号の変数(LLM の呼びをまたぐ) | 推論の行動・検索・接地 | CoALA [S12] | 欄を固定すれば体×欄の配列 |
| ST6 | 記憶の流れ | 自然言語の記録+作成・参照の時刻+重要度 | 知覚・振り返り・計画 | Generative Agents [S13] | 時刻と重要度は数値の配列。文と埋め込みは別の保管(埋め込みの類似は GPU で束にできる)。35 万体ぶんの文は体ごとの可変長 |
| ST7 | 共有の Agent State | 書かれていない(モジュールが読み書き) | 各モジュール | PIANO(R-41 §4-2) | — |
| ST8 | 型の決まった信念+計画+段 | JSON/XML の欄(臨床家と決めた型) | 遅い過程(Reasoner)だけ | Talker-Reasoner [S14] | 欄が固定なら体×欄の配列。段は int |
| ST9 | 行動の待ち行列 | 行動の列 | 遅い過程 | SwiftSage [S15]・Sims の待ち行列 [S23] | 体ごとの固定長のリング配列+頭の位置 |
| ST10 | 黒板 | 鍵と値 | 知覚・サービス・Task | Unreal BT [S22] | 体×鍵の配列。変化の印で観測する体を選ぶ |
| ST11 | 欲求の値と物の広告 | 欲求のベクトル・物×行動×欲求の範囲 | 体の過程(減衰)・物の定義 | Sims [S23] | 体×欲求の配列・物×広告の表(配列の典型) |
| ST12 | 考慮の入力 | 0〜1 に正規化した数値 | 知覚と世界の問い合わせ | IAUS [S17] | 体×行動×考慮の配列 |

- 今の v2 に既にある欄との対応【見立て】: ST10・ST11・ST12 に近いものは `AgentState` の配列(activity・内受容の段・計画の欄)とセルの B4 欄にある。ST5・ST8 に当たる「固定の型の信念」と、ST9 の「行動の待ち行列」(計画の欄を除く)は、§1-3 の読みの範囲では見当たらない【推測】。ST6 は記憶の層(別系)にある。

## §5 調停の規則の型の一覧

| 型 | 誰がいつ答えるか | 優先・閾値・競合解決 | 先例 | 決定論 | 現実との整合(どの錨・知見と照らせるか) |
|---|---|---|---|---|---|
| R1 固定優先 | 優先の高い層が条件を満たせば常に答える | 順位の表。同順位は別の鍵 | BT の左ほど優先 [S22]・Côté の反応>熟慮 [S16]・今のアービタの 4 級 | 完全 | 優先の表そのものは設計者の指紋。反応の遅れ・気づく割合の錨で確かめる |
| R2 効用の最大 | 毎周期、最高点の候補 | argmax。同点は雑音か鍵 | ACT-R の効用+雑音 [S4]・Sims の幸福 [S23]・IAUS の積 [S17] | 雑音を種つきにすれば完全 | 効用の式が錨を写すと循環(11-01 §0-2)。式を知識(判断モデル)に置くか、式に置くかの区分が要る |
| R3 2 段(区分→区分の中) | 最高の区分の中から、区分の中の規則で | 区分=順位、区分の中=重みの抽選・待ち時間など | Dill [S18]・DA:I の帯 [S19]・今のアービタ(級→待ち時間) | 抽選を種つきにすれば完全 | 区分の表は R1 と同じ指紋。区分の中の抽選は分布の幅を作る(多様性の源を規則に置くことになる=ユーザーの選好「多様性は LLM から」と照らす要) |
| R4 既定と介入 | 速い過程が答え、条件が立てば遅い過程が上書き | 介入の条件(葛藤・停滞・無効・重大・想定外・段) | Evans & Stanovich [S24]・Kahneman [S28]・SwiftSage の 4 条件 [S15]・Talker の待つ欄 [S14] | 条件が決定論なら完全 | 介入の頻度は錨(CRT の誤答率・De Neys の介入はまれ=R-39 §3-2)と照らせる |
| R5 並列の競争 | 両方が走り、強い方・合わせた結果が答える | 活性の比べ・足し合わせ・拒否権 | Sloman [S27]・Evans の parallel-competitive [S25]・LIDA の連合 [S6]・CLARION の組み合わせ [S10] | 完全 | 遅い過程を全員に毎回走らせる費用。De Neys の exclusivity 批判 [S29] と相性がよい(両系が同じ答えを出せる) |
| R6 知識不足で上げる | 速い過程で決まらないとき遅い過程が自動で起きる | 「決められない」の型(提案なし・同点・食い違い・進まない) | Soar の impasse [S1] | 完全 | 「決められない」の判定を判断モデルの分布(拮抗)に置けば 11-01 §10-1 #55・56 の「分布が拮抗したら LLM へ」と同形 |
| R7 成功率で確率的に選ぶ | 層ごとの確率で答える層を選ぶ | 確率=成功率に比例(probability matching)/固定 | CLARION [S10]・Lee 2014 の信頼度(R-39 §5-2) | 種つきなら完全 | 成功の定義(報酬)が要る=本プロジェクトでは誰が採点するかが錨の循環と重なる恐れ【推測】 |
| R8 閾値の蓄積 | 量が溜まったら遅い過程 | 重要度の和>150・活性の和>閾値・時間切れ(200 ms) | Generative Agents の振り返り [S13]・LIDA の放送 [S6] | 完全 | 閾値の値は expedient。振り返りの回数(1 日 2〜3 回)は Generative Agents の観察で、人の錨ではない |
| R9 事前に決める | 最初にどちらが答えるかを決める | 状況の区分(段・課題の型) | Evans の pre-emptive [S26]・Talker の段 [S14]・R-133 §4-2 (D1) 型で固定 | 完全 | 判断の型の表(routing §1)をなぞる。同じ型で余裕の無い場面を写せない(R-133 §4-2) |

- 組み合わせの先例: Talker-Reasoner は R9(段で待つか)+R4(待たなければ速い方が答える)。SwiftSage は R4(4 条件)+行動の待ち行列。今のアービタは R3(級→待ち時間)に、予算の頭打ちと縮退を足したもの。CLARION は R7 と R5 を MCS が選ぶ。
- 呼びの予算との関係: 先例のうち、調停が「予算の上限」を兼ねるのは今のアービタだけで、ほかは調停の規則に計算の予算を書かない(Soar の substate の時間の監視 [S1] と LIDA の 200 ms の自動放送 [S6] は、予算ではなく反応の時間の制約)。

## §6 割り込みと保留の型の一覧

### 6-1 割り込み(遅い過程の途中で速い過程が動けるか)

| 型 | 中身 | 先例 | 遅い過程の途中で速い過程は | 配列への載り方【見立て】 | 現実との整合 |
|---|---|---|---|---|---|
| I1 再評価で置き換わる | 毎周期すべてを評価し直すので、割り込みは「点の変化」として自然に起きる | IAUS [S17]・DA:I [S19]・Soar の適用中の再実行 [S1] | 動く(毎周期) | 全員×毎周期の評価=費用が体数×周期に比例 | 振動(ping-pong)の対策(上乗せ・ヒステリシス)が要る [S16][S17] |
| I2 観測者の打ち切り | 条件を見張り、条件が変わった体だけ下位の処理を打ち切る | Unreal BT の Observer Aborts [S22] | 動く(事象で) | 「鍵が変わった体」だけを処理=R-133 §3-2 の (A2) 購読と同形 | 見張る条件の選び方が指紋 |
| I3 反応が熟慮を止める | 優先の高い反応が来たら熟慮の行動を止め、終わったら新しい決定を求める | Côté の Action Selector [S16] | 反応だけ動く | 反応の優先の表(int)と「熟慮の行動中」の印 | 無意識の反応>認知的な反応・予期で反応が変わる(図書館と工事現場)=予期を状態に持つ |
| I4 並走 | 遅い過程を止めず、速い過程は古い共有の状態で動き続ける | PIANO(R-41 §4-2)・Talker-Reasoner [S14]・LIDA の周期の重なり [S6]・ACT-R の要求は並行 [S3] | 動く(並行) | 速い側は配列で毎周期、遅い側は LLM の待ち。共有の状態の版の扱いが要る | 「歩きながら考える」と同形。古い状態で動いた結果(snap judgement)の錨が要る |
| I5 上が決まれば熟考を捨てる | 熟考の最中に上の段で決定できたら熟考を自動で消す | Soar の impasse の解消 [S1] | 動く(全段の決定サイクル) | 「熟考中の体の候補を毎周期見て、上で決まれば熟考の印を下ろす」は乗る | 考え中の人が状況の変化で考えを放り出す形 |
| I6 時間切れの暫定 | 時間を監視し、時間切れなら最適でない(または無作為の)決定 | Soar の substate の時間の監視 [S1]・LIDA の timekeeper [S7]・anytime(R-41 §5) | — | 体ごとの締め切りの欄と比較 | 「急ぐと浅く考える」(R-133 §4-2 (D2) の余裕)と同形 |
| I7 集中で抑える | 考え中は集中 f を持ち、顕著性 s が f を超えたら割り込む | 本プロジェクトの集中の度合い(11-01 §10-1・R-128 ③)。先例の機構としては LIDA の放送の閾値(活性が閾値を超えたら意識へ)が最も近い【見立て】 | s > f のときだけ | 体ごとの f と刺激の s の比較(ベクトル) | Lavie の注意(作業記憶の負荷で妨害が増える)と向きが逆になる恐れ(R-128 ③) |
| I8 不応期 | 一度起きたら一定時間起こさない | 今の v2(`REFRACTORY_MINUTES`) | 起きない | 既に配列 | 「予算の装置・人の性質ではない」と宣言済み(11-01 §10-1) |

### 6-2 考えかけの保留(途中の結果をどう持つか)

| 型 | 中身 | 先例 | 配列への載り方【見立て】 |
|---|---|---|---|
| H1 捨てる | 途中の構造は消す。評価の結果も保持しない | Soar の結果でない構造 [S1]・DA:I の評価の結果 [S19] | 何も持たない |
| H2 結果だけ残す/規則にする | 上の段に書いた結果だけ残し、熟考の過程を規則に写す | Soar の結果と chunking [S1]・CLARION の RER [S10] | 結果は欄。規則への写しは判断モデルの学習(11-01 §11 の第 2 世代)と同じ向き |
| H3 共有の記憶に最新版 | 遅い過程は最新の信念を記憶に置き、速い過程はいつでも読む | Talker-Reasoner [S14]・PIANO(R-41 §4-2) | 体×欄の配列+書いた時刻の欄 |
| H4 計画として記憶に置き、反応で作り直す | 計画を記憶に入れ、反応の時刻から計画を作り直す | Generative Agents [S13]・LIDA の部分の計画 [S7] | 計画の欄(体×段) |
| H5 行動の待ち行列 | 遅い過程の出力を行動の列にし、順に実行し、無効が続けば止める | SwiftSage [S15]・Sims の待ち行列 [S23] | 体ごとの固定長のリング配列 |
| H6 脇の出力 | 割り込まれた考えの返事は行動に使わず「考えかけたこと」として記憶とテープへ | R-128 ④(本プロジェクトの案)・Flink の脇の出力(R-128 の引用) | 行動の配列に入れず記憶の層へ |
| H7 中断して再開 | 途中の状態(問い・仮説・部分の結論)を持って再開する | anytime の interruptible(R-41 §5。contract を interruptible にすると最悪 4 倍遅い) | LLM の途中の状態は配列に乗らない(文の保管) |

## §7 配列で回す前提との相性と、今の形との差

### 7-1 乗るもの【見立て】

- 固定次元の数値の欄: 欲求(ST11)・考慮(ST12)・集中 f と顕著性 s(I7)・区分の順位(R1・R3)・停滞の数(SwiftSage の「連続 5 歩の報酬 0」)・重要度の和(R8)・待ち時間(今のアービタ)・締め切り(I6)。どれも体×欄の int か float の配列になる。
- 調停の演算: argmax(R2)・lexsort(R3・今のアービタの整列の鍵)・閾値の比較(R4・R8・I7)・積(IAUS)・種つきの抽選(R3 の区分の中・R7)。今のアービタが純関数で入力の順に依らないのと同じ性質を保てる。
- 応答曲線: 0〜1 の入力を表で引く(np.interp か表の索引)。
- 事象で動く観測(I2): 「鍵が変わった体」だけを処理する形は、R-133 §3-2 の (A2)「予定+購読(書き手の知らせ)」とそのまま重なる。
- 小さなネット(PIANO の反射・CLARION の下の層・SwiftSage の Swift): 束にして GPU で回せる。判断モデル(L1.5)も同じ扱い。

### 7-2 乗らないもの・乗りにくいもの【見立て】

- 可変の構造: Soar の作業記憶のグラフ・substate の段・規則の照合(体ごとに規則集合が違うと、規則×体の照合を配列にしにくい)。LIDA のコードレットの群(多数の小さな過程)。
- 自然言語: Generative Agents の記憶の流れ・Talker-Reasoner の信念を文のまま持つ形・LLM の出力。数値の部分(時刻・重要度・欄の値)だけを配列に出し、文は別の保管にする分け方になる。
- 毎周期の遅い過程: Generative Agents の「刻みごとに LLM が続けるか反応するかを決める」を 35 万体に写すと、刻みの数×体の数の呼びになる。CLAUDE.md §4 のとおり計算量は案を外す理由にしないが、性能の予算の計器(呼数/日)に直接出る。

### 7-3 時間の単位の目安【見立て】

- ACT-R・Soar の 50 ms を 35 万体で回すと、世界の 1 秒あたり 350,000 × 20 = 700 万周期、1 日で約 6.0 × 10^11 周期。LIDA の 260〜390 ms なら 1 秒あたり約 90 万〜135 万周期。
- 先例の多くは周期で回すが、Unreal の BT は事象で回す [S22]。v3 の仮決定(題 1 の (G2)・題 2 の (Q3))の上では、周期の型(I1)は「体ごとの次の時刻」に周期の事象を入れること、事象の型(I2)は購読に当たる(R-133 §3-2 の (A3) と (A2))。
- 時間の数値の出どころ: 50 ms と 260〜390 ms は人の反応時間・脳の計測にもとづく(Laird は「Empirical evidence」、Madl らは脳波の位相と反応時間の模擬)[S1][S6]。ゲームの think cycle と AI 更新の周期は性能の都合で決まり、人の錨ではない [S17][S19]。

### 7-4 今の形との差(先例と並べて)

| 観点 | 今の v2(§1-3) | 先例の形 | 差 |
|---|---|---|---|
| 速い過程の範囲 | 検出だけ(B4 のハッシュ変化・内受容の閾値)。判断はしない | 速い過程が既定の答えを出す(R4・Sims・IAUS・Swift・Talker) | 判断モデル(L1.5)が入るまで、速い過程が「既定の答え」を出す型(R4)は無い。今の既定の行動はエンジンの継続(代打)と LLM |
| 調停の主語 | アービタ=呼びの予算の配分(固定優先 4 級・待ち時間・昇格・頭打ち・縮退) | 調停は「誰が答えるか」の規則で、予算は書かない(§5 の末尾) | 今は「誰に LLM を回すか」と「予算」が 1 つの部品にある。11-01 §10-1 の「考え直すか=L1.5」が入ると、調停の主語が判断モデルへ移る |
| 考え中の状態 | 体の状態に「考え中」は無い。返事待ちの体に再送が起きうる(`decide.py:176-178`) | Soar の substate・LIDA の多周期の行動の流れ・Talker の待つ欄・SwiftSage の行動の待ち行列は、どれも「遅い過程が走っている」ことを状態に持つ | 考え中の印・集中 f・考え始めた時刻の欄が無い(R-128 ① ③ の案がこれを足す) |
| 割り込み | 不応期(I8)で抑える。会話は不応期 0 | I1〜I7(§6-1) | 不応期は先例のどれにも当たらない装置で、11-01 §10-1 で「予算の装置」と宣言済み。置き換え先の I7(集中)に最も近い先例の機構は LIDA の放送の閾値 |
| 保留 | 起床の候補を保留(破棄しない・次の起床で最新の状態を読む) | H1〜H7(§6-2) | 起床の候補の保留は H3 に近い(最新を読む)。考えかけの結果の保留(H5・H6・H7)は無い |
| 共有の状態 | 体とセルの配列(数値)+描画の文 | ST1〜ST12(§4) | 型の決まった信念(ST8)と行動の待ち行列(ST9)が無い【推測】 |
| 時間 | 60 秒の刻み・δ_think は分に切り上げ | 50 ms〜数百 ms の周期(認知アーキテクチャ)・事象(Unreal)・会話の番(Talker) | v3 の題 1・2 の仮決定で秒とナノ秒に移る。周期で回すか事象で回すかは題 3(活性)と重なる |
| 決定論 | アービタは純関数・同順はハッシュ | 先例は決定論を主題にしない。雑音(ACT-R)・抽選(Dill・CLARION)を使う | 先例の確率的な規則は、種つきの乱数(事象の時刻から作る=11-03 §4)で決定論に写せる |

## §8 決めるべき題(題 9 の副問・選択肢と根拠・推薦なし)

| 副問 | 選択肢 | 根拠(本書の節) | 現実との整合(どの錨・知見と照らせるか) |
|---|---|---|---|
| 9-1 速い過程と遅い過程の関係の型 | (a) 既定と介入(速い方が答え、条件で遅い方)/(b) 並列の競争(両方が走り、比べる)/(c) 事前に決める(判断の型か段で答える側を決める)/(d) (c) で既定を置き、(a) の条件で上げる | §2-a・§5 の R4・R5・R9 | (a) は介入の頻度の錨(R-39 §3-2)と照らせる。(b) は De Neys の exclusivity 批判と相性がよいが、遅い過程を全員に走らせる。(c) は routing §1 の表をなぞる |
| 9-2 共有の状態に足す欄 | (a) 今の配列+描画の文のまま/(b) 型の決まった信念の欄(Talker 型 ST8)を足す/(c) 行動の待ち行列(ST9)を足す/(d) (b)+(c) | §4・§7-4 | (b) の欄の型は設計者の指紋になる(Talker の型は臨床家と決めた)。欄を誰が決めるかを 11-01 §1 の区分(知識か初期化か)で決める要がある |
| 9-3 調停の規則の型 | (a) 固定優先+級の中(今の R3)/(b) 判断モデルの分布で決める(拮抗したら LLM=11-01 §10-1 の #55・56 の形を全般に)/(c) 効用の積(IAUS 型・考慮を判断モデルが出す)/(d) 成功率で確率的に選ぶ(CLARION 型) | §5 | (a) の級の表は指紋。(b) は移行の閾値が腕になる(11-01 §10-1)。(c) の考慮の式は錨を写すと循環。(d) は成功の採点者が要る |
| 9-4 遅い過程に上げる引き金 | (a) 決められない(提案なし・拮抗・食い違い=Soar 型)/(b) 条件の列挙(停滞・無効・重大・想定外=SwiftSage 型)/(c) 閾値の蓄積(重要度の和=Generative Agents 型)/(d) 判断モデルが「LLM を呼ぶか」を答える(K2 の文のまま) | §2-b-2・§2-c-2・§2-c-5・§1-2 | (a) と (d) は判断モデルの分布から出せる。(b) の条件の選び方と (c) の閾値は expedient |
| 9-5 割り込みの型 | I1 再評価/I2 観測者の打ち切り/I3 反応が熟慮を止める/I4 並走/I5 上が決まれば熟考を捨てる/I6 時間切れの暫定/I7 集中/I8 不応期のまま(組み合わせ可) | §6-1 | I7 は R-128 ③ の Lavie の注意。I4 は「歩きながら考える」(題 7-2 の答申と合流)。I8 は宣言つきの装置 |
| 9-6 考えかけの保留 | H1 捨てる/H2 結果だけ残す/H3 最新版を共有の記憶に/H4 計画として置き作り直す/H5 行動の待ち行列/H6 脇の出力(R-128 ④)/H7 中断して再開 | §6-2 | H6 は R-128 ④ の案。H7 は anytime の 4 倍の代価(R-41 §5)。H2 の「規則にする」は判断モデルの第 2 世代(11-01 §11)と同じ向き |
| 9-7 速い過程を回す時間の単位 | (a) 周期(全員を決まった秒ごと=I1)/(b) 事象(購読した変化だけ=I2)/(c) 状態ごとの周期(歩く体は短く・寝ている体は無し=R-133 §3-2 の (A3)) | §7-3 | (a) の 50 ms は人の計測の値だが、体数×周期の費用。(b) は R-133 の (A2)。(c) の周期の値は expedient |
| 9-8 判断モデル(L1.5)の置き場 | (a) 速い過程の上段(検出の次に既定の答えを出す)/(b) 調停役(誰が答えるかだけを決める=Côté の Action Selector・CLARION の MCS の位置)/(c) 両方 | §2-a-1(Stanovich の三分は制御の階層=R-41 §1-1)・§2-b-4・§2-d-1 | 用語集 105 行の「LLM を呼ぶかは判断モデルが決める」は (b) を含む。(a) は「日常の判断は判断モデル」に当たる |
| 9-9 遅い過程の結果を速い過程へ移すか | (a) 移さない(毎回遅い過程)/(b) 移す(Soar の chunking・CLARION の RER・判断モデルの第 2 世代)/(c) 判断モデルの第 2 世代まで移さず、テープを教師データに溜める | §2-b-2・§2-b-4 | (b) は「人の行動データによる較正なし」(11-01 §11)と両立するかの確認が要る(教師が LLM の出力なら較正ではない【推測】)。chunking は決定論を要する(Laird §4)=今の決定論の規則と合う |

## §9 出典

読んだ日はすべて 2026-11-03。等級は冒頭の注のとおり。

| # | 出典 | URL | 読めた範囲 | 等級 |
|---|---|---|---|---|
| S1 | Laird, J. E. (2022). Introduction to the Soar Cognitive Architecture(Soar 9.6) | https://arxiv.org/abs/2205.03854 | PDF 全文(29 頁) | ◎ |
| S2 | Anderson, Bothell, Byrne, Douglass, Lebiere & Qin (2004). An integrated theory of the mind. *Psychological Review* 111(4):1036-1060 | https://doi.org/10.1037/0033-295X.111.4.1036 | 要旨(Europe PMC) | ○ |
| S3 | Gall & Frühwirth (2017). An Operational Semantics for the Cognitive Architecture ACT-R and its Translation to Constraint Handling Rules | https://arxiv.org/abs/1702.01606 | PDF の §2(ACT-R の説明) | ◎ |
| S4 | Gall & Frühwirth (2014). Exchanging Conflict Resolution in an Adaptable Implementation of ACT-R | https://arxiv.org/abs/1405.3570 | PDF の §2〜§4 | ◎ |
| S5 | Salvucci & Taatgen (2008). Threaded cognition. *Psychological Review* 115(1):101-130 | https://doi.org/10.1037/0033-295X.115.1.101 | 要旨(Europe PMC) | ○ |
| S6 | Madl, Baars & Franklin (2011). The Timing of the Cognitive Cycle. *PLoS ONE* 6(4):e14803 | https://doi.org/10.1371/journal.pone.0014803 | HTML 全文(Methods の Parameters を含む) | ◎ |
| S7 | Franklin, Ramamurthy, D'Mello ほか (2007). LIDA: A Computational Model of Global Workspace Theory and Developmental Learning. AAAI Fall Symposium | https://ccrg.cs.memphis.edu/assets/papers/LIDA%20paper%20Fall%20AI%20Symposium%20Final.pdf | PDF 全文(6 頁) | ◎ |
| S8 | Baars (2005). Global workspace theory of consciousness. *Progress in Brain Research* 150:45-53 | https://doi.org/10.1016/S0079-6123(05)50004-9 | 要旨(Europe PMC) | ○ |
| S9 | Hélie, Wilson & Sun. The CLARION Cognitive Architecture: A Tutorial(要旨の 2 頁) | https://homepages.hass.rpi.edu/rsun/folder-files/clarion-tutorial-intro.pdf | 全文(2 頁) | ◎ |
| S10 | Wilson, Hélie & Sun. The Action-Centered Subsystem(CLARION の手引きの図版) | https://homepages.hass.rpi.edu/rsun/folder-files/clarion-acs-slides.pdf | 全 107 枚のうち表現・学習・層の統合の節 | ◎ |
| S11 | Sun, Slusarz & Terry (2005). The interaction of the explicit and the implicit in skill learning. *Psychological Review* 112(1):159-192 | https://doi.org/10.1037/0033-295X.112.1.159 | 要旨(Europe PMC) | ○ |
| S12 | Sumers, Yao, Narasimhan & Griffiths (2023/2024). Cognitive Architectures for Language Agents(TMLR・arXiv v3) | https://arxiv.org/abs/2309.02427 | PDF 全文 | ◎ |
| S13 | Park, O'Brien, Cai, Morris, Liang & Bernstein (2023). Generative Agents(arXiv v2) | https://arxiv.org/abs/2304.03442 | PDF 全文 | ◎ |
| S14 | Christakopoulou, Mourad & Matarić (2024). Agents Thinking Fast and Slow: A Talker-Reasoner Architecture(arXiv v1) | https://arxiv.org/abs/2410.08328 | HTML 全文 | ◎ |
| S15 | Lin ほか (2023). SwiftSage(NeurIPS 2023・arXiv v2) | https://arxiv.org/abs/2305.17390 | PDF 全文 | ◎ |
| S16 | Côté, C. Reactivity and Deliberation in Decision-Making Systems. *Game AI Pro* 第 11 章 | http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter11_Reactivity_and_Deliberation_in_Decision-Making_Systems.pdf | 全文 | ◎ |
| S17 | Lewis, M. Choosing Effective Utility-Based Considerations. *Game AI Pro 3* 第 13 章 | http://www.gameaipro.com/GameAIPro3/GameAIPro3_Chapter13_Choosing_Effective_Utility-Based_Considerations.pdf | 全文 | ◎ |
| S18 | Dill, K. Dual-Utility Reasoning. *Game AI Pro 2* 第 3 章 | http://www.gameaipro.com/GameAIPro2/GameAIPro2_Chapter03_Dual-Utility_Reasoning.pdf | 全文 | ◎ |
| S19 | Hanlon & Watts. Behavior Decision System: Dragon Age Inquisition's Utility Scoring Architecture. *Game AI Pro 3* 第 31 章 | http://www.gameaipro.com/(第 3 巻・第 31 章の PDF) | 全文 | ◎ |
| S20 | Merrill, B. Building Utility Decisions into Your Existing Behavior Tree. *Game AI Pro* 第 10 章 | http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter10_Building_Utility_Decisions_into_Your_Existing_Behavior_Tree.pdf | §10.1〜§10.6 の該当の文 | ◎(一部) |
| S21 | Hilburn, D. Simulating Behavior Trees: A Behavior Tree/Planner Hybrid Approach. *Game AI Pro* 第 8 章 | http://www.gameaipro.com/GameAIPro/GameAIPro_Chapter08_Simulating_Behavior_Trees.pdf | §8.1 | ◎(一部) |
| S22 | Epic Games. Behavior Tree in Unreal Engine - Overview(公式の文書) | https://dev.epicgames.com/documentation/en-us/unreal-engine/behavior-tree-in-unreal-engine---overview | 全文 | ◎ |
| S23 | Forbus & Wright. Some notes on programming objects in The Sims(Northwestern 大学 QRG) | https://www.qrg.northwestern.edu/papers/Files/Programming_Objects_in_The_Sims.pdf | 全文 | ◎ |
| S24 | Evans & Stanovich (2013). Dual-Process Theories of Higher Cognition: Advancing the Debate. *Perspectives on Psychological Science* 8(3):223-241 | https://doi.org/10.1177/1745691612460685 | 要旨(Europe PMC)。本文の逐語は R-39 §3-1 | ○ |
| S25 | Evans (2008). Dual-processing accounts of reasoning, judgment, and social cognition. *Annual Review of Psychology* 59:255-278 | https://doi.org/10.1146/annurev.psych.59.103006.093629 | 要旨(Europe PMC) | ○ |
| S26 | Evans (2007). On the resolution of conflict in dual process theories of reasoning. *Thinking & Reasoning* 13(4):321-339 | https://doi.org/10.1080/13546780601008825 | 要旨の冒頭 1 文(検索の要約)。出版社の頁は 403 | △ |
| S27 | Sloman (1996). The empirical case for two systems of reasoning. *Psychological Bulletin* 119(1):3-22/再録 Sloman (2002) Two Systems of Reasoning(『Heuristics and Biases』) | https://doi.org/10.1037/0033-2909.119.1.3 ・ https://doi.org/10.1017/CBO9780511808098.024 | 再録の章の冒頭の要約(Cambridge Core)○・1996 の要旨は検索の要約 △ | ○/△ |
| S28 | Kahneman (2002). Maps of Bounded Rationality(Nobel 講演)/Kahneman (2003). *American Psychologist* 58(9):697-720 | https://www.nobelprize.org/prizes/economic-sciences/2002/kahneman/lecture ・ https://doi.org/10.1037/0003-066X.58.9.697 | 講演は検索の要約だけ(PDF は 403)△・2003 は PubMed の要旨の言い換え ○ | △ |
| S29 | De Neys (2023). Advancing theorizing about fast-and-slow thinking. *Behavioral and Brain Sciences* 46:e111(オンライン公開 2022-09-02) | https://doi.org/10.1017/S0140525X2200142X | 要旨(Cambridge Core) | ○ |

- 既存答申(引いた節と等級): ※R-39 §3-1・§3-2・§5-1〜§5-4(等級 B・Evans & Stanovich の Table 1 と CLARION の MCS は親未確認)/※R-41 §1-1〜§1-3・§4-1〜§4-3・§5(等級 B・PIANO は親が逐語確認・CoALA 本文・Soar・anytime は親未確認)/※R-128 §7 ①〜④(親の一次確認 第340 あり・先例の引用は親未確認)/※R-133 §3〜§4・§9(等級 B)。
- 循環参照検査: 本書が既存答申だけを根拠にした主張は、PIANO(R-41 §4-2=親の逐語確認あり)・anytime の 4 倍(R-41 §5=二次・親未確認)・Lee 2014 と Milli 2017(R-39 §5=前者は抄録・後者は親の逐語確認)・De Neys & Glumicic の「介入はまれ」(R-39 §3-2=原典・抄録は親確認)・Lavie(R-128=親未確認)。anytime と Lavie は一次が無いものとして扱う(§8 の根拠にだけ使い、数値は写していない)。
- S19 の URL: 章の PDF の名前に全角のアポストロフィを含むため、表には目次の場所だけを書いた(取得は `GameAIPro3_Chapter31_Behavior_Decision_System_Dragon_Age_Inquisition’s_Utility_Scoring_Architecture.pdf`)。

## §10 読めなかったもの

| 項 | 何が読めなかったか | 理由 | 影響 |
|---|---|---|---|
| 1 | ACT-R の公式の手引き(Unit 3・Unit 6・参照の手引き)と Anderson 2007 の本 | act-r.psy.cmu.edu が接続を拒否(443 番の ECONNREFUSED) | 効用の雑音の分布・α の既定値・知覚のバッファの割り込みの書き方は空欄。本書の ACT-R は要旨と 2 本の形式化の論文 [S3][S4] による |
| 2 | Evans 2007 の本文と要旨の全体 | tandfonline・philpapers が 403、Europe PMC と Crossref に要旨が無い | 3 型の定義の逐語は空欄(要旨の冒頭 1 文だけ・△) |
| 3 | Sloman 1996 の本文と Criterion S | APA PsycNet が読み込まれない・Crossref に要旨なし | 「同時に矛盾する答え」の基準は空欄 |
| 4 | Kahneman の Nobel 講演の PDF・AER 2003・2011 の本 | nobelprize.org が 403・本は読めない | Kahneman の「追認・監視は緩い」は検索の要約(△)と Talker-Reasoner の引用(○)だけ |
| 5 | De Neys 2023 の本文(不確かさの監視の模型) | 有料 | 要旨だけ |
| 6 | Evans & Stanovich 2013 の本文 | SAGE が 403 | 要旨(○)と R-39 §3-1 の逐語(親未確認)だけ |
| 7 | LIDA の 2014 年の総説(IEEE TAMD)と警報(alarms)の機構 | 正規の場所の PDF を見つけられなかった(見つかったのは別の大学の授業の置き場) | 意志の決定は 2007 の論文 [S7] だけ。警報の型は空欄 |
| 8 | CLARION の技術仕様(Tutorial on CLARION 5.0)と周期の秒 | 著者の頁で 404 | 層の統合の式は手引きの図版 [S10] による。時間の単位は空欄 |
| 9 | Orkin の F.E.A.R. の GOAP(GDC 2006) | 著者の頁(alumni.media.mit.edu)が 404 | GOAP の再計画と割り込みは空欄。BT と計画の混在は Hilburn [S21] だけ |
| 10 | Dave Mark の IAUS の講演(GDC 2013・2015) | GDC の録画(動画)は読めない | IAUS は Lewis の章 [S17] の説明による |
| 11 | The Sims の後の版(Sims 3・4)の自律と割り込み | 一次の文書を探す前に検索の道具が使えなくなった | Sims は初代の Forbus & Wright [S23] だけ。割り込みは空欄 |
| 12 | Generative Agents の刻みの秒 | 本文に見つからなかった(付録とコードは読んでいない) | 時間の単位の列は「本文に無し」 |
| 13 | Talker-Reasoner の遅延の数値 | 本文に数値が無い | — |
| 14 | 後半の WebFetch と WebSearch | 要約役のモデルの上限で使えなくなった | 後半は curl で原文を取り、grep で確かめた(等級は下げていない)。検索で新しい出典を広げることはできなかった |

## §11 親の一次確認の欄

| # | 確かめる所 | 方法 | 結果 | 日付 |
|---|---|---|---|---|
| 1 | §1-3 の今の形(`engine/arbiter.py` と `engine/change_detect.py` の docstring・`agents/state.py:306` の不応期の表・`engine/systems/decide.py:176-178` の再送の数え) | HEAD の実読 | | |
| 2 | [S1] Soar の impasse の 3 型・substate の消え方・「Execution time can be monitored」・50 msec | 原文 | | |
| 3 | [S3][S4] ACT-R の「at most one chunk」・50 ms・「requests are executed in parallel」・効用の学習の式 | 原文 | | |
| 4 | [S6] LIDA の 260〜390 ms・放送の 3 つの引き金と 200 ms・直列は放送と行動の選択だけ | 原文 | | |
| 5 | [S10] CLARION の層の統合の 4 法と probability matching | 原文(図版) | | |
| 6 | [S14] Talker-Reasoner の「retrieves the latest one from memory」と「in the planning coaching phase the Talker waits」 | 原文 | | |
| 7 | [S15] SwiftSage の 4 条件(K=5)と行動の待ち行列 | 原文 | | |
| 8 | [S13] Generative Agents の 150・0.995・「continue with their existing plan, or react」 | 原文 | | |
| 9 | [S17][S18][S19] IAUS の積と 0 での除外・Dill の 4 段・DA:I の帯 | 原文 | | |
| 10 | 写し検査: §1-2 の前提の表の中身が用語集・11-01・R-128・R-133 と一致するか | 突き合わせ | | |
| 11 | 発注文の「R-133 §9 の題 9」と、R-133 §9 の表が 8 題であることの食い違い(§1-1 の注) | R-133 §9 の実読 | | |

## 親の一次確認(第343・2026-11-03・親)

| 主張 | 確かめ方 | 結果 |
|---|---|---|
| Generative Agents の振り返りは重要度の和が 150 を超えたとき | arXiv 2304.03442 の HTML 版を curl で読んだ | **一致**(「exceeds a threshold (150 in our implementation)」・1 日 2〜3 回) |
| 発注文の「R-133 §9 の題 9」 | R-133 §9 を読んだ | **親の書き違い**=R-133 §9 は題 1〜8。題 9(心のモジュール)は指示書 11-03 §5 と設計書 [v3-core-design](../design/v3-core-design-2026-11-03.md) の表にある(答申の §1-1 の注のとおり) |
| 形式 | 行数・改行・絶対パス・秘密 | 453 行・LF・絶対パスなし・CLEAN |

- 等級: **B**(主な数値を親が原典で 1〜2 点ずつ確かめた。ほかの出典は答申の ◎○△ のまま)。
- 共通の注: 作業の途中で、実装役・リサーチ役の WebFetch と WebSearch が利用の上限で止まった。後半は curl の標準出力を文字だけにして読んだ(ファイルの保存なし)。空欄は本文の「読めなかったもの」のとおりで、記憶では埋めていない。
