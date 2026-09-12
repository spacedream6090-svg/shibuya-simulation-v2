# LLM 社会シミュレーションの現在地 2026-09 — 軽い確認(答申の種・未正典化)

> 位置づけ: ユーザーが共有した有志のまとめ(17 件・ハッカソン Vol.2 の投稿)を、親が **抄録レベル**(arXiv abstract・検索要約)で 1 件ずつ確認したもの(2026-09-12・第171)。**本文は未読**。第2陣の設計ラウンドの事前リサーチ(本番)は保留中(ユーザー指示)で、本番ではこの表を出発点に本文実読・数値の再計算・「採用済み/第2陣で採用/該当せず」の判定を行う。
> 記法: ✔ = 抄録で有志の要約が裏づけられた / △ = 実在は確認・要約の読みが有志と親で違う / ✖ = 見つからない。

## 1. 17 件の確認表

| # | 有志の要約(年月・一句) | 実体(親確認・抄録) | 判定 | この repo での扱い |
|---|---|---|---|---|
| 1 | 2023 Generative Agents「放てば動く」→ 内部は測れない | Park et al. 2023。答申で実読済み(行動契約) | ✔ | 憲法「意思決定と発話だけ LLM」の対照例 |
| 2 | 2023 Concordia「世界の状態は GM が外で持て」→ 人格は中のまま | Concordia(DeepMind 2023)。答申で実読済み | ✔ | AI Town と併せ「状態と集約はエンジン」の根拠 |
| 3 | 2024 ペルソナ漂流「8 ターンで漂う」 | arXiv 2402.10962(Li et al.)LLaMA2-chat-70B/GPT-3.5 で 8 ラウンド内に有意な漂流・注意の減衰が一因(答申 persona-dynamics で抄録実読) | ✔ | 人格プロンプトを増やさない判断(D-68)の根拠の一つ |
| 4 | 2024 「書き方を変えても漂う。型はモデル構造で決まる」2412.00804 | **Examining Identity Drift in Conversations of LLM Agents**(Choi et al.・v2 2025-02)。9 モデル×36 主題。①大きいモデルほど漂う ②モデル差はサイズ効果より小さい ③ペルソナ付与は維持に効かない | △ | 「モデル構造」は主に**パラメータ数**。ペルソナ無効は ✔。第2陣の同一性(面接形式・自己生成)の設計で参照 |
| 5 | 2024 EMNLP 議論バイアス「立場を指示してもモデルの癖に従う」 | **Systematic Biases in LLM Simulations of Debates**(Taubenfeld et al.・EMNLP 2024 main・arXiv 2402.04049)。党派ペルソナが基底モデルの偏りへ回帰・自己微調整で偏りを動かすと追随 | ✔ | 「指示で人格は作れない」の確定。広告の過剰反応(D-56 系)と同根の可能性=第2陣で参照 |
| 6 | 2024 StateAct「状態は外に書け」 | **StateAct**(Rozanov & Rei・arXiv 2410.02810・REALM@ACL 2025)。self-prompting+chain-of-states で ReAct 比 +10〜30% | △ | 状態は **LLM 自身が出力の中に書く**(外部エンジンではない)。この repo の「エンジンが状態を持つ」とは層が違う。知覚テンプレの状態欄の書き方(第2陣)で参照 |
| 7 | 2024 Stanford 1,000 人「面接を渡せば 85% 再現」→ 都市には合わない | arXiv 2411.10109(答申 D-68 §3-1 で現行版の数値を訂正つき確認: 83/82/86 vs 74) | ✔ | 面接形式の同一性を W17 v2 段1 に採用済み |
| 8 | 2025-06 状態表現の効果「書き方が変数」 | **The Effect of State Representation on LLM Agent Behavior in Dynamic Routing Games**(Goodyear et al.・arXiv 2506.15624)。要約した履歴・後悔情報・他者情報の制限が均衡に近づく | ✔ | 知覚テンプレ(共有静的/セル/個体)の設計変数として第2陣で参照。「正しい書き方の決め方が無い」は ✔ |
| 9 | 2025-07 「LLM は既存 ABM の補助層」 | **Integrating LLM in Agent-Based Social Simulation: Opportunities and Challenges**(Taillandier et al.・arXiv 2507.19364・v2 2026-02)。Hybrid Constitutional Architectures・Physics-Cognition split | ✔ | この repo の分業と同型(物理・制約はエンジン、認知は LLM) |
| 10 | 2026-07 GAMA「局所だけ改善・計算 3〜5 倍」 | **Evaluating LLMs for Decision-Making in Agent-Based Urban Mobility Simulations**(arXiv 2607.02716・GAMA+Agno)。局所封鎖で再配分と到着率が改善・大規模擾乱では道路制約で全体利得は限定・記憶が安定化 | △ | 「局所だけ改善」✔。「計算 3〜5 倍」は抄録に無い(表 3 に計算費あり=本文要確認) |
| 11 | 2025-11 Springer「検証が中心課題」 | **Validation is the central challenge for generative social simulation**(Larooij & Törnberg・AI Review・2025-11-18・PMC 全文公開)。系統的レビュー(Scopus 2025-03)。face-validity 依存・データ漏洩の警告 | ✔ | holdout の作法・アンカー台帳の位置づけの外部根拠。本文は PMC で読める=本番で実読 |
| 12 | 2026-03 2603.00113「制度を外へ・seed 横断で測れ」 | **AI Agents Alone Are Not (Yet) Sufficient for Social Simulation**(答申 広告・人物知覚で実読済み)。親の読み=ロールプレイの説得力≠行動的妥当性・プロンプト微差で結論が動く | △ | 有志は処方側、親は脆さ側の読み。両方本文にある可能性=本番で確認 |
| 13 | 2026-05 頑健性監査「書式で 76 ポイント動く」 | **Stop Drawing Scientific Claims from LLM Social Simulations Without Robustness Audits**(Ye et al.・arXiv 2605.18890・2026-05-17)。同内容・別書式のペルソナで囚人のジレンマの協力率が 76pt 差(gpt-5.2・30 seed)・別モデルでは 1pt=モデル同一性も頑健性の次元・TRAILS 分類 | ✔ | 答申 2 本で引用済み(76pt)。C8 ablation の設計に TRAILS の 3 層を写す候補 |
| 14 | 2026-06 事前登録「先に固定せよ」 | 該当する単独の論文は**見つからず**(#13 の推奨に含まれる可能性・未確認) | ✖ | 手続きはこの repo が独自に採用済み(holdout の PREREG_V0・較正と holdout の分離) |
| 15 | 2026-06 Causal Agent Replay「1 ステップ介入して差を測れ」 | **Causal Agent Replay: Counterfactual Attribution for LLM-Agent Failures**(Shah・arXiv 2606.08275・2026-06-06)。SCM の do 演算・同方針の前進再実行・Shapley。限界=分岐間の共通乱数は未対応 | ✔ | 有志の「LLM の乱数まで固定して同一を確認する話は無い」は ✔。この repo は**テープ再生で同一を確認**(T2-c・c7-day-3 最終ハッシュ一致)=先にある点 |
| 16 | 2026-06 パリ・上海「もっともらしいが現実的でない」 | **When Plausible Is Not Realistic**(arXiv 2606.13835・答申 D-68 で実読)。500 体規模・GPT-4o-mini で 7〜10 日 $130〜200 | ✔ | 多様性を評価軸に入れた根拠。規模(500 vs 390,067)の差もこの repo の位置づけ |
| 17 | 2026-09 Steering Geometry「中に価値の地図はある・動かすと壊れる」 | **Steering Geometry: Validating Human Value Geometry in LLM Steering Space**(arXiv 2609.06289・2026-09-05・EMNLP 2026)。Schwartz 20 価値・26K 標本。幾何はサイズで良くなり**指示微調整後に劣化** | △ | 「製品版は崩れてる」= 指示微調整後の劣化 ✔。「動かすと壊れる」は有志の解釈。中をいじる道はこの repo では採らない(状態と発話の分業) |
| 18 | 2026-09 Procedural Graph「帳簿の更新を LLM に任せて検証で漉せ」 | **Procedural Graphs: Self-Evolving Execution Structures for LLM Agents**(Lu et al.・arXiv 2609.09153・2026-09-08)。手続き知識のグラフ・LLM 精錬器の編集を検証で通す・EnterpriseArena(月次財務判断 132 か月) | △ | 「帳簿」は EnterpriseArena の現金。検証で漉すのは**グラフの編集**。有志の「人格には正解が無い」は解釈。第2陣の記憶/習慣の表現候補として参照 |

(有志の 17 件のうち「2025-07」と「2026-07」を 2 行に分けたため 18 行。)

## 2. 流れの一句と、この repo の位置

| 有志の一句 | この repo |
|---|---|
| 放てば動く(2023) | 採らない(憲法の分業) |
| 動くが漂う・指示は効かない(2024) | 人格プロンプトを増やさず面接形式の自己生成(D-68・W17 v2 段1) |
| 状態を外に置け(2023〜24) | エンジンが唯一の書き込み口(世界過程・計画実行層・台帳) |
| 外に置く状態の書き方が変数(2025) | 知覚テンプレ 3 層の設計変数=第2陣の論点 |
| 測り方が無い・検証が中心課題(2025〜26) | アンカー台帳・物差し 2 本・holdout の作法・受入表 |
| 道具が出揃う(2026 前半) | 事前登録=採用済み・頑健性監査=C8 ablation へ写す候補・反実仮想再生=テープ再生で同一確認済み(介入再生は未) |
| 実データに当てると合わない(2026-06) | holdout 照合が未実施=まだ言えない(開封はユーザー判断) |
| 外の状態を誰がどう更新するか(2026-09) | 世界過程(エンジン)+D-50 穴台帳+第2陣の記憶/習慣 |

## 3. 同時代の作品(AUTOMATA HACKATHON Vol.2・提出 38 作品・2026-09-12 閲覧)

出典: https://hackathon.automata-lab.jp/works/(主催 Singulab / SPACE DATA・テーマ「メタ安全保障」)。傾向(親の粗い読み):

- **規模**: 4〜50 体の LLM 村・組織が大半。数千体以上は Civilization Explorer(5,000 人×4 世界・200 年・ルール層が動かし LLM は解釈)・教育社会創発(1,000 人×175 年)・SLEEP CITY 2.0(300 体×7 日)・LUNAR FUTURES(並列世界線)・本 repo(0004 考える街・40 万体)。
- **型**: (a) 少数の LLM エージェントに条件を変えて挙動を比べる比較実験型が最多(習慣・依存・ガバナンス・情報戦)(b) ルール層+LLM 解釈の混成型(Civilization Explorer・データセンターと上水=決定論の水収支の上で 4 役が判断・マルチ ASV=LLM 指揮官 vs ルールベース)(c) 心理・人格の数理を毎ターン注入する型(心理学ハーネス・人格エンジン)(d) 双子世界で介入効果を個人単位で分解する型(GhostLift=広告あり/なし・12 人)。
- **本 repo と近いもの**: GhostLift(広告の双子世界=v2 の広告領域の小型版)・SLEEP CITY 2.0(睡眠不足のネットワーク伝播)・データセンターと上水(決定論の収支の上に LLM 判断=この repo の分業と同型)・外的不動産買収(49 人の温泉都市・36 か月・住民全員を LLM が演じる)。
- **入賞 10 作**: LUNAR FUTURES・Imp・心理学ハーネス・言語の最後の仕事・Civilization Explorer・COSPLAY RESERVE・ニュアンス税関・外的不動産買収・Engineering Agents・RELAYSTATE。本 repo の作品(0004)は一覧の「その他」側。
- **所見**: 実データ照合・決定論の再生・母集団の較正を持つ作品は見当たらない(要約ページの範囲)。差別化は「測定の標準」側にある、という第2陣以降の位置づけと整合。

## 4. 未確認・本番で行うこと

- 本文実読: #4・#5・#6・#8・#10(計算費の数値)・#11(PMC 全文)・#12(処方側の記述)・#13(事前登録の推奨の有無)・#15・#17・#18。
- 各件の「採用済み / 第2陣で採用 / 該当せず」の確定と、第2陣の決定アジェンダへの写し。
- #14 の実体探索(事前登録を主題にした 2026-06 の論文があるか)。
