# 答申の反映監査 P1/P2 — 推奨・決定項が設計と実装にどれだけ入ったか

<!-- hdr:v1 -->
- **分野**: ソフトウェア工学 #29 / ABM方法論 #21 | **重要度**: P0
- **一次確認**: **repo 内監査**(Web 不使用)。判定の根拠はすべて `docs/` と `src/` と `tests/` の実在行。外部一次資料は本書の対象外 **→ 親再確認(第214)**: #5「D4 修正3 が未訂正」は**誤り**——第210 で `v2-redesign.md` L198〜203・`v2_significance.md` L41 とも訂正済み(L385 は決定台帳の 4b 行で本文は L198)。T3 未実装(`checks.py` 検算①②のみ)は親確認済み(第210 E)。他は親未確認
- **索引**: [INDEX.md](INDEX.md) ・ **残務**: [research-backlog.md](research-backlog.md) ・ **分野地図**: [v2-discipline-map.md](v2-discipline-map.md)

> ユーザー依頼(2026-09-17)「社会シミュレーション分野以外も含め、今までのリサーチでまとめた内容が現状のシミュレーションにどれほど組み込まれているか調べて」。
> 本書は **INDEX §3 の P1 40 本 + P2 9 本 = 49 本**を担当する(P0 35 本は別監査 `v2-research-reflection-audit.md`)。
> 手法は [batch1](v2-r23-primary-check-batch1.md) §1 のファイル名 grep と [batch2](v2-r23-primary-check-batch2.md) §1 の**特徴値 grep**(固有名・数値・式)の併用。HEAD=第213。
> **答申本体・設計書・台帳は一行も編集していない。**

**判定の 5 値**(別サブ A と共通):

| 値 | 意味 |
|---|---|
| **実装済** | `src/` にコードがあり `tests/` かランの実測で動いている |
| **設計済・未実装** | 決定台帳 DECIDED か設計書にあるが `src/` に無い |
| **部分** | 縮退した形・expedient 代替・一部の軸だけ |
| **未採用** | 答申が推奨したが決定で採らなかった(理由の記録の有無を備考に書く) |
| **未判定** | 答申にも設計にも実装にも痕跡が見つからない=**取りこぼし候補** |

---

## §1 集計

### 1-1 5 値の総数(全 49 本・項 244)

| 判定 | 件数 | 割合 |
|---|---|---|
| **実装済** | 87 | 35.7% |
| **部分** | 60 | 24.6% |
| **未判定**(取りこぼし候補) | 52 | 21.3% |
| **設計済・未実装** | 34 | 13.9% |
| **未採用** | 11 | 4.5% |
| 合計 | 244 | 100% |

> 数は §2 の判定表から機械的に数えた(`awk` で 3 列目を集計)。本文の割合が §2 と食い違ったら §2 が正。

**読み方**: 「設計か実装に何らかの形で入った」(実装済+部分+設計済・未実装)= **181 項 / 74.2%**。
「コードになった」(実装済+部分)= **147 項 / 60.2%**。
**取りこぼし候補(未判定)は 52 項 = 21.3%**。うち **18 項が 6 本の答申に集中**する(prediction-module 4・coupled-adaptation 4・precedent-system 3・r2-fulltext 3・observation-projection 2・institutions 2)。残り 34 項は 24 本に 1〜2 項ずつ散っている。

### 1-2 重要度別

| 重要度 | 本数 | 項 | 実装済 | 部分 | 設計済・未実装 | 未採用 | 未判定 | 実装済+部分 |
|---|---|---|---|---|---|---|---|---|
| **P1** | 40 | 210 | 81 | 51 | 27 | 11 | 40 | **62.9%** |
| **P2** | 9 | 34 | 6 | 9 | 7 | 0 | 12 | **44.1%** |

P2 の低さは設計どおり(INDEX §5-2 案(c)「P2 9 本は最後・いずれも決定に触れていない」)。ただし**未判定が 12/34 = 35.3%** あり、「触れていない」ではなく「触れたか分からない」状態にある。
**未採用は P1 に 11 件・P2 に 0 件**。P2 は「採らないと決めた」のではなく「議題に上がっていない」。

### 1-3 分野別(INDEX の 32 分野・本書の担当分のみ)

同じ答申が複数分野に属するときは**両方に数える**(延べ)。分野番号は分野地図に合わせた。

| # | 分野 | 担当本数 | 項 | 実装済 | 部分 | 設計済・未実装 | 未採用 | 未判定 | **反映率**(実装済+部分) |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 人口学・合成人口論 | 3 | 13 | 2 | 4 | 1 | 3 | 3 | 46.2% |
| 2 | 交通工学(活動ベース) | 2 | 10 | 3 | 3 | 1 | 1 | 2 | 60.0% |
| 3 | 人間移動科学 | 3 | 15 | 6 | 6 | 0 | 1 | 2 | **80.0%** |
| 5 | 知覚心理学・精神物理学 | 1 | 6 | 5 | 1 | 0 | 0 | 0 | **100%** |
| 6 | 環境音響学 | 1 | 5 | 3 | 1 | 0 | 1 | 0 | **80.0%** |
| 9 | 地理情報科学 | 2 | 9 | 5 | 2 | 0 | 0 | 2 | 77.8% |
| 10 | SFCマクロ経済学 | 2 | 14 | 9 | 3 | 0 | 1 | 1 | **85.7%** |
| 11 | 法学(業法・条例) | 2 | 12 | 0 | 4 | 2 | 1 | 5 | 33.3% |
| 12 | 認知科学(記憶・習慣) | 2 | 10 | 0 | 0 | 5 | 1 | 4 | **0%** |
| 13 | 人格心理学 | 1 | 6 | 1 | 2 | 0 | 2 | 1 | 50.0% |
| 15 | 会話分析・語用論 | 1 | 7 | 3 | 2 | 1 | 1 | 0 | 71.4% |
| 16 | 行動経済学・マーケ科学 | 1 | 5 | 4 | 0 | 0 | 1 | 0 | **80.0%** |
| 17 | 小売科学・商業立地論 | 1 | 5 | 4 | 0 | 0 | 1 | 0 | **80.0%** |
| 21 | ABM方法論 | 5 | 25 | 9 | 4 | 6 | 0 | 6 | 52.0% |
| 22 | 検証とV&V・UQ | 7 | 34 | 7 | 10 | 8 | 1 | 8 | 50.0% |
| 23 | 統計学・因果推論 | 1 | 6 | 0 | 3 | 0 | 0 | 3 | 50.0% |
| 25 | 計算社会科学 | 6 | 25 | 8 | 8 | 1 | 0 | 8 | 64.0% |
| 26 | 科学哲学 | 1 | 5 | 2 | 2 | 0 | 0 | 1 | **80.0%** |
| 27 | 自然言語処理・機械学習 | 5 | 28 | 8 | 11 | 0 | 0 | 9 | 67.9% |
| 28 | 計算機科学(並列・決定論) | 6 | 38 | 21 | 9 | 0 | 0 | 8 | 78.9% |
| 29 | ソフトウェア工学 | 5 | 26 | 10 | 10 | 4 | 0 | 2 | 76.9% |
| 30 | ゲームエンジン工学・CG | 3 | 18 | 8 | 5 | 4 | 0 | 1 | 72.2% |
| 31 | 研究倫理・情報法 | 5 | 20 | 4 | 1 | 9 | 0 | 6 | 25.0% |
| 0 | 分野外(事業・資金) | 2 | 7 | 2 | 0 | 1 | 0 | 4 | 28.6% |

**上位 5(反映率)**: ① 知覚心理学・精神物理学 #5 **100%** ② SFCマクロ経済学 #10 **85.7%** ③ **80.0% が 5 分野で同率** — 人間移動科学 #3 / 環境音響学 #6 / 行動経済学 #16 / 小売科学 #17 / 科学哲学 #26(次いで #28 計算機科学 78.9%・#9 地理情報科学 77.8%・#29 ソフトウェア工学 76.9%)。
**下位 5**: ① 認知科学(記憶・習慣) #12 **0%** ② 研究倫理・情報法 #31 **25.0%** ③ 分野外(事業・資金) #0 **28.6%** ④ 法学(業法・条例) #11 **33.3%** ⑤ 人口学・合成人口論 #1 **46.2%**(次いで #13 人格心理学・#22 検証とV&V・#23 統計学が 50.0% で並ぶ)。

**分野の並びが語ること**: 反映率が高いのは **「1 tick の中で決まるもの」**(知覚・音・価格・取引・並行実行)、低いのは **「日をまたいで積み上がるもの」**(記憶・習慣・判例・制度)と **「世界の外側にあるもの」**(倫理・公開・事業・資金)。C0〜C9 の工程順がそのまま分野の反映率になっている。

> **#12 が 0% であることが本監査の最大の所見**。memory-retrieval(U1)と prediction-module は**どちらも決定台帳に DECIDED 行がある**(`docs/design/v2-redesign.md:392`・`:446`)のに、`src/` には記憶・習慣・予測誤差のコードが 1 行も無い(`src/shibuya/agents/state.py:8` が「T0習慣 M3・記憶 M4・関係 M5・プロフィール M6 は C3 以降の別レジストリ」と書いたまま C9 に到達している)。

### 1-4 答申別の要約(反映率=実装済+部分 の割合)

| 反映率 | 答申(本数) |
|---|---|
| **100%** | engine-llm-boundary(3/3)・person-perception-verification(6/6)・world-ledger-verification(6/6)・area-boundary-map-reading(3/3)・implementation-stack(7/7)・run-manifest-concurrency(6/6)= **6 本** |
| **70〜99%** | ugc-platform-import 87.5 ・ economy-sfc 83.3 ・ parallel-execution 83.3 ・ benchmark-standards 80 ・ game-tech-import 80 ・ llm-mobility 80 ・ mobility-field 80 ・ science-claims 80 ・ d1-reacquisition 80 ・ hearing-numbers 80 ・ vlm-reality-check 80 ・ price-formation-llm 80 ・ data-contract 80 ・ r23-primary-check-batch1 75 ・ learned-simulation 75 ・ longrun-ops 75 ・ conversation-deep 71.4 ・ llm-serving 71.4 = **18 本** |
| **40〜69%** | llm-knowledge 66.7 ・ pattern-ledger 66.7 ・ cell-granularity 66.7 ・ small-scale-verification 60 ・ legal-licensing 60 ・ digital-twin-landscape 50 ・ persona-population 50 ・ precedent-system 50 ・ kddi-attribute-shares 50 ・ r2-fulltext 50 ・ impact-risk 50 ・ game-frontend 40 ・ boundary-deep 40 = **13 本** |
| **1〜39%** | world-model-relation 33.3 ・ funding 33.3 ・ capabilities-business 25 ・ institutions 16.7 = **4 本** |
| **0%** | **memory-retrieval ・ prediction-module ・ coupled-adaptation ・ observation-projection ・ micro-observation ・ ethics-operations ・ content-safety ・ publication-ethics** = **8 本** |

0% の 8 本のうち 5 本(U1 記憶・R5 予測モジュール・3ループ・U4 観測射影・D-80 ミクロ観察)は「**決定はしたが工程が来ていない**」もの、3 本(倫理運用・コンテンツ安全・出版倫理)は「**設計書は完成しているが公開段の実装がゼロ**」。**中身が否定されて 0% になった答申は 1 本も無い。**

---

## §2 答申ごとの判定表(49 本)

列は別サブ A と同一: **答申 | 項 | 判定 | 根拠(ファイル:行) | 備考**。

### 2-1 game-frontend-research(ゲームエンジン工学・CG #30・P1)— 実装済 1 / 部分 1 / 設計済 3 / 未判定 0

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| game-frontend | 推奨3段階案(初期 deck.gl 2D → 中期 Cesium/PLATEAU 3D → 長期 Unity) | 設計済・未実装 | `docs/design/v2-redesign.md:458`(R15 DECIDED) | `src/`・`tools/` に deck.gl/Cesium のコードは無い。`tools/fig/_style.py` は matplotlib の静止図で別物 |
| game-frontend | GlassBox 規律(画面上の事象は常にシムの1:1・ビューアの独自演出禁止) | 設計済・未実装 | `docs/design/v2_draft_proposal.md:79`・`v2-redesign.md:458` | ビューアが無いので規律の適用先も無い |
| game-frontend | 介入の記録契約 `{intervention_id, tick, actor, target_selector, params, provenance}` | 設計済・未実装 | `docs/design/v2_draft_proposal.md:78` | `src/`・`tests/` に `intervention` の語ゼロ。ablation の腕は `tools/c8/ablations_v1.json` にあるが**介入 ID とprovenance の形式ではない** |
| game-frontend | checkpoint=I フレーム + 行動イベント=P フレームの再生型ハイブリッド | 部分 | `src/shibuya/engine/tape.py:85`(`shibuya.tape/2`)・`src/shibuya/agents/state.py:537`(checkpoint ハッシュ) | 二層は実装。**タグ付きイベント索引と checkpoint の時間スライス**(U3 で採用決定 `v2-redesign.md:394`)は未実装 |
| game-frontend | PLATEAU は「読むだけ」で足りる(自前で CityGML を焼かない) | 実装済 | `src/shibuya/build/geo/w4_heights.py`・IMPLEMENTED #11(W4 3,531 棟) | PLATEAU 2025 年度版を構築入力として使用。可視化用途ではない |

### 2-2 benchmark-standards-research(検証とV&V・UQ #22・P1)— 実装済 2 / 部分 2 / 未採用 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| benchmark-standards | 5層×〈指標/データ源/判定規則/分割〉の台帳構造 | 部分 | `docs/design/v2-pattern-ledger.md`(4階層・強5本) | 層の数と名前が違う(物理/人流/生活時間/社会関係/情報伝播経済 → 個人行動/関係/集団組織/都市集計)。**判定規則の列は台帳にあるが「データ源」列は行ごとにばらつく** |
| benchmark-standards | 分割3原則(パターン単位で割る・時間分割併用・**自由度<アンカー本数**を台帳ヘッダで管理) | 部分 | `src/shibuya/build/audit/w19_freeze.py:6,39`(holdout 封印 S 層) | 封印は機械化済み。**「自由度<アンカー本数」の管理欄は台帳に無い**(grep 0) |
| benchmark-standards | FHWA 式「実測の自然変動そのものを許容誤差にする」 | 実装済 | `docs/design/v2-redesign.md:423`(D1′ 閾値=実測の年次変動 JSD 0.0001-0.0012)・`tools/c8/dashboard.py`(G-2 の `Var_obs`) | 答申が「v2 に最も移植価値が高い」とした項目が、名前を出さずに実装されている |
| benchmark-standards | GEH<5 を 85%・鉄道断面 ±10% を判定規則に | 未採用 | `docs/design/v2-inventory-and-bottlenecks.md:27`(棚卸しに列挙のみ) | `src/`・`tests/` に `GEH` ゼロ。**採らなかった理由の記録は無い**。W10 の区間突合が 0/202 で FAIL(IMPLEMENTED #11)なので、そもそも当てる先が無かった可能性 |
| benchmark-standards | FAIL 行を消さず倍率つきで残す(EPJ 形式)・「通ると何が言えるか」を1行 | 実装済 | `tools/c8/dashboard.py`(面2「落ちたら不合格・通っても合格とは言わない」・PENDING の「歪む場所」宣言を読む) | 計器盤 G-1 として正典化 |

### 2-3 digital-twin-landscape-research(計算社会科学 #25・P1)— 実装済 1 / 部分 1 / 設計済 1 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| digital-twin-landscape | 「社会行動ツインは行政 DT の空白域」=v2 の位置づけ | 設計済・未実装 | `docs/design/v2_significance.md` | 位置づけの主張であり実装対象ではない |
| digital-twin-landscape | 国内で数値基準を公表した検証例は西新宿 70% 一致のみ → v2 は「どの実測にどの指標で何%」を**事前宣言**する | 実装済 | `docs/bench/c7/prereg_arms_v1.md`・`tools/c8/dashboard.py`(面2 に k* 事前宣言) | 答申の勧告どおり事前登録が運用に入っている |
| digital-twin-landscape | 最近接先行=GenWorld(東広島 196,608 体)・v2 は約 2 倍規模 | 部分 | IMPLEMENTED #14(390,188 体) | 規模は達成。**「2倍規模」の比較表は設計書に無い** |
| digital-twin-landscape | 提携・参照候補 7 件(東大 CSIS・和泉研・GenWorld 著者・渋谷未来デザイン・KDDI・PLATEAU・富士通研) | 未判定 | — | 設計書・PENDING・IMPLEMENTED に痕跡ゼロ。**取りこぼし候補** |

### 2-4 engine-llm-boundary-research(計算社会科学 #25・P1)— 実装済 3

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| engine-llm-boundary | 線引きの設計原則 7 本(+補助1) | 実装済 | `docs/design/v2-world-process-design.md:5`・`src/shibuya/world/processes/constitution.py`(憲法5 の機械検査) | batch2 §1 が既に確認。原則が**ビルド時検査**になっている |
| engine-llm-boundary | サブシステム別 16 行マッピング | 実装済 | `docs/design/v2-redesign.md:442`(D-R2-3 逐行決定)・`src/shibuya/world/processes/first_batch.py`(第1陣 21 過程) | |
| engine-llm-boundary | 「状態と集約=エンジン / 意思決定と発話=LLM」 | 実装済 | `src/shibuya/engine/resolve.py`(単一書き込み口・AST 検査)・`src/shibuya/llm/contract.py` | CLAUDE.md §3 の第1行そのもの |

### 2-5 game-tech-import-research(ゲームエンジン工学・CG #30・P1)— 実装済 1 / 部分 3 / 設計済 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| game-tech-import | #1 checkpoint+デルタ+**タグ付きイベント索引**の三層リプレイ契約 | 部分 | `src/shibuya/engine/tape.py:85,337` | 索引と時間スライスが欠落(2-1 と同じ穴) |
| game-tech-import | #2 アーキタイプ/チャンク SoA + existential processing(発火 index 配列だけ回す) | 実装済 | `src/shibuya/core/soa.py`・`docs/design/v2-redesign.md:398`(U7 DECIDED) | P4「個体添字ループの AST lint」で機械化 |
| game-tech-import | #3 重要度付き部分スナップショット配信(量子化・帯域クランプ・静的個体は送らない) | 部分 | `src/shibuya/perception/hashes.py:4`(dormant 再送抑止) | 「一度届けたら再送しない」は実装。量子化・帯域クランプはビューアが無いので未 |
| game-tech-import | #4 認知 LOD 階層 + on-demand 昇格(遠景=統計移動/中景=テンプレ/注目時のみ LLM) | 設計済・未実装 | `docs/design/v2-redesign.md:397`(U6 DECIDED) | `src/` に昇格ロジック無し。`engine/arbiter.py` の「昇格」は繰り延べクラスの昇格で別物 |
| game-tech-import | #5 スマートオブジェクト広告 + utility スコアリング(行動は場所/役割の側) | 部分 | `docs/design/v2-redesign.md:396`(U5)・`:465`(affordance 由来の原則・09-17)・`src/shibuya/engine/resolve.py`(`_apply_eat` + `world.eatery_mask`) | affordance の第1例が語彙 v2 で実装された。**utility スコアリングは採らず LLM が選ぶ形**(ユーザー選好「多様性は LLM から」と整合) |

### 2-6 llm-knowledge-deep-research(自然言語処理・機械学習 #27・P1)— 実装済 2 / 部分 2 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| llm-knowledge | (B) **反実仮想渋谷**(地名・路線・店舗を一括置換)を常設の対照ランに | 未判定 | — | `tools/c8/ablations_v1.json` に該当腕なし・設計書に「架空渋谷」の語なし。**取りこぼし候補(上位)** |
| llm-knowledge | (C)(D) 事前知識台帳 + 新規性検定(Web 規模 n-gram 照会) | 未判定 | — | 造語・未定義語の台帳(`src/shibuya/llm/undefined.py`)はあるが**既出性の照会は無い**。D-71 の語彙成長と接点がある |
| llm-knowledge | 箇条3「LLM に固有名詞・数値・距離を生成させない構造(層1が選択肢を列挙・LLM は選ぶだけ)」 | 実装済 | `src/shibuya/llm/contract.py`(語彙 24 語)・`src/shibuya/perception/templates.py`(2行形+選択肢)・`src/shibuya/llm/parser.py` | AB7 の open 腕はこの制約を**わざと外す腕**として設計されている |
| llm-knowledge | 箇条2「地理の骨格(ノード・隣接・距離所要時間)は外部データ」 | 実装済 | `src/shibuya/build/geo/w1_walk_graph.py`・`w3_distances.py` | W1 186,741 m・全点対前計算 |
| llm-knowledge | 箇条6 文化整合の3層測定(WVS 日本波 / 生活時間 / 相互作用5次元+**上位1%集中度**) | 部分 | IMPLEMENTED #19(出勤代理・最頻ビン・H bit=生活時間側) | 生活時間層だけ。WVS・上位1%集中は無い(`Gini` は `v2-pattern-ledger.md` のみ) |
| llm-knowledge | 箇条9 宣言する限界5点を事前登録(協力上振れ・参加不平等圧縮=k* 過小推定 ほか) | 部分 | `docs/bench/c7/prereg_arms_v1.md` | 事前登録の器はあるが**中身は在圏の腕と指標**で、この5点は入っていない |

### 2-7 llm-mobility-research(人間移動科学 #3 / NLP #27・P1)— 実装済 1 / 部分 3 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| llm-mobility | §4 許容③ **到達可能性による候補集合の制約**(徒歩n分圏・実所要時間・営業時間・カテゴリ整合) | 部分 | `src/shibuya/engine/processes/opening.py`・`src/shibuya/agents/state.py:193`(`CLOSED`)・`resolve._apply_eat`(飲食店セル前提) | 営業時間とカテゴリ整合は入った。**徒歩n分圏での候補集合の絞り込みは規則として存在しない**(batch2 §1-3 の指摘と同じ) |
| llm-mobility | §4 不可: 重力/放射モデル・時間帯活動確率・実 OD 行列は借りない | 実装済 | `docs/design/v2-boundary-economy-design.md:22`(案B=重力抽選は下限対照のみ)・`v2-redesign.md:443`(U10) | v2 の線引きの中核 |
| llm-mobility | §5-1 純 holdout の事前登録=指標セット(β・ζ・μ・回転半径・CPC・滞在時間・モチーフ JSD・EPR)を**先に凍結** | 部分 | `docs/bench/c7/prereg_arms_v1.md`(PREREG_V0) | 凍結されたのは**在圏の指標**。`CPC` `EPR` `Zipf` は `src/` にも設計書にも無い |
| llm-mobility | §5-2 実サンプル間ばらつきを**フロア**として必ず併記 | 部分 | `docs/design/v2-redesign.md:423`(D1′ の閾値=年次変動 JSD) | 在圏では同型が実装済み。CPC のフロア併記(第210 訂正)は答申側だけで設計に未着地 |
| llm-mobility | §5-4 渋谷 2km 四方では β 検証は無意味 → 滞留時間分布・訪問頻度 Zipf・EPR μ・常用地点〜25 に置換 | 未判定 | — | 置換先の指標がどこにも無い。**取りこぼし候補(上位)** |

### 2-8 memory-retrieval-research(認知科学(記憶・習慣) #12・P1)— 設計済 4 / 未採用 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| memory-retrieval | 案(c)ハイブリッド: T0/T1=構造化スロット・T2 夜間監査で昇格分のみ埋め込み(8-16本/体・int8) | 設計済・未実装 | `docs/design/v2-redesign.md:392`(U1 DECIDED)・`docs/design/v2-cognition-design.md` | `src/shibuya/agents/state.py:8`「記憶 M4 は C3 以降の別レジストリ」のまま。C9 到達時点で未着手 |
| memory-retrieval | 索引は作らない(per-agent 8-16 件の全走査) | 設計済・未実装 | 同上 | |
| memory-retrieval | 忘却=Ebbinghaus 指数減衰 + 想起で減衰定数を緩める | 設計済・未実装 | `docs/design/v2-cognition-design.md` | `src/` に `忘却`・`Ebbinghaus` ゼロ |
| memory-retrieval | 習慣の初期値=ペルソナ seed + expedient タグ + 由来フラグ + seed 無し ablation | 設計済・未実装 | `docs/design/v2-redesign.md:393`(U2 DECIDED) | 習慣表(T0)が `src/` に無い |
| memory-retrieval | 日本語埋め込みは Ruri-small が優位 | 未採用 | 答申本文の第203 訂正(`v2-memory-retrieval-research.md` の Ruri 行)・batch1 §3 D | **親が一次確認して優位主張が消えた**。理由の記録あり。U1 は判断待ちなので決定は未拘束 |

### 2-9 mobility-field-research(人間移動科学 #3 / 交通工学 #2・P1)— 実装済 2 / 部分 2 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| mobility-field | 借りる① 身体の物理(SFM/ORCA/フロアフィールド CA) | 部分 | `docs/design/v2-redesign.md:462`(R7 DECIDED)・`src/shibuya/engine/geometry.py`(Kladek 解析式・希望速度) | C9a で**解析式と前計算表**に置き換わった(G13 ユーザー案)。SFM/ORCA 本体は実装しない方向 |
| mobility-field | 借りる② 較正・検収の物差し(Weidmann 基本図・Fruin LOS・乱流閾値 5-6人/m²・RiMEA 15ケース) | 実装済 | `src/shibuya/engine/geometry.py:280`(Fruin LOS 段)・`src/shibuya/world/state.py`(`DENSITY_STAGE_EDGES_PER_M2`) | **RiMEA 15 ケースは未**(答申の物差しのうち1本が欠けている) |
| mobility-field | 借りない: 重力モデル・時間帯活動確率・OD 較正 | 実装済 | `docs/design/v2-boundary-economy-design.md:22` | 2-7 と同一項目 |
| mobility-field | **歩行者は最短経路を選ばない**(4原理)→ エンジン規則でなく LLM 側の選好として持たせる | 未判定 | — | `src/shibuya/build/geo/w3_distances.py` は最短距離のみ。LLM 側に経路選好を渡す口も無い。**取りこぼし候補** |
| mobility-field | MATSim 流「1日プラン全体をスコア単位にする」粒度 | 部分 | `src/shibuya/engine/presence.py`(W17 週次表を在圏ブロックに畳む・計画一致率) | 1日プランを持つ形は実装。**スコア・共進化(選択変異)は無い** |

### 2-10 prediction-module-deep-research(認知科学 #12・P1)— 設計済 1 / 未判定 4

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| prediction-module | 予測誤差ゲート付き認知ループ(T0 実行→予測照合→T1→T2→結晶化) | 設計済・未実装 | `docs/design/v2-redesign.md:446`(R5/U19 DECIDED・δ_think レーン) | 決定はあるが `src/` に `予測誤差` ゼロ |
| prediction-module | 段2 統計的逸脱 = **med + 1.0·MAD** | 未判定 | — | 設計書にも無い(`MAD` grep 0)。**取りこぼし候補** |
| prediction-module | 結晶化条件5つ(n≥5・成功率≥0.8・連続≥3・過剰マッチング・一貫写像) | 未判定 | — | `結晶化` は判例側の語としてのみ登場 |
| prediction-module | 想像は「相手の反応」に限定・**H=1 固定**・ゲート率初期値 15% | 未判定 | — | **取りこぼし候補** |
| prediction-module | 結晶化は既定 OFF + **予算等価ベースライン**との ablation で昇格 | 未判定 | — | `tools/c8/ablations_v1.json` に予算等価の腕は無い |

### 2-11 science-claims-research(科学哲学 #26 / 計算社会科学 #25・P1)— 実装済 2 / 部分 2 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| science-claims | 主張は「実地図 × 10万体超 × 全個体 live LLM × 全 I/O 保存」の**4条件同時成立**として立てる | 実装済 | IMPLEMENTED #19・#20(390,067 体・実 LLM・テープ 270 万行) | 4 条件すべてが実測で満たされている |
| science-claims | 「GM 裁定は先行ゼロ」→ **判例結晶化に限定**(訂正) | 部分 | batch1 §3-B(`v2_draft_proposal.md` は直り `v2_significance.md` が残る) | **訂正の伝播が片方だけ**。写し検査の対象 |
| science-claims | believability を主要根拠にしない・**マクロ/ミクロ分離報告** | 実装済 | `tools/c8/dashboard.py`(面1/面2/面3)・G-8「分布で報告」 | |
| science-claims | PIMMUR 監査・Barrie&Törnberg 基準を先回りする ablation | 部分 | `tools/c8/ablations_v1.json`(第1陣6本+AB7/AB7b/AB7c) | ablation の器はあるが**PIMMUR 6 原則の被覆表は無い**(r2-fulltext (d) の TRAILS 被覆表と同じ穴) |
| science-claims | LLM 集団の **PoA 実測**=未占有ニッチ | 未判定 | — | `PoA` grep 0。**取りこぼし候補** |

### 2-12 small-scale-verification-research(検証とV&V・UQ #22・P1)— 実装済 1 / 部分 2 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| small-scale-verification | 検証ピラミッド L0 mock / L1 縦切り / L2 縮小渋谷 / L3 本番 | 実装済 | IMPLEMENTED #10(mock 5,000体)・#16(実 LLM スモーク)・#20(39万体) + `CLAUDE.md §4` | 「実 LLM は〜24step スモークまで」が規律として明文化されている |
| small-scale-verification | 規模外挿①**N 系列(最低3点等比)+ N^(-1/2) 参照線** | 部分 | `tools/fig/fig_seed_pair.py`(CV(n=2)・N=(CV/r)²) | 測定点は **5,000 と 390,067 の 2 点だけ**(r2-fulltext B-12「自分の指数を知らない」)。3 点目が無い |
| small-scale-verification | ②「率」と「容量・閾値」を conf タグで分離宣言 | 未判定 | — | 予算宣言表に**縮小時の扱い(線形に縮めてよい/いけない)の列が無い**。**取りこぼし候補** |
| small-scale-verification | golden dataset(25-50件)+ 主要指標 ±3% 劣化で CI 失敗 | 部分 | `tests/engine/test_presence_derive_v2.py`(golden 両表)・T2 checkpoint 一致 | golden は**ビット一致**で運用。±3% 帯のゲートは無い |
| small-scale-verification | ⑥希少事象は L2 で 0 回=情報ゼロ・**3/N 則**の上限信頼区間だけ記録 | 未判定 | — | **取りこぼし候補** |

### 2-13 boundary-deep-research(人口学 #1 / 交通工学 #2・P1)— 実装済 1 / 部分 1 / 設計済 1 / 未採用 1 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| boundary-deep | 境界=(c)確率的ゲートウェイ主軸 +(d)低解像度外界の段階導入 | 部分 | `docs/design/v2-redesign.md:443`(U10=案A+案C)・`src/shibuya/build/field/w12_external_nodes.py:1` | 採った形は**方面別外界ノード+週次表+確率的差分+逸脱時 LLM**。答申の(c)と同型だが呼称も構成も違う。(d)低解像度外界は未 |
| boundary-deep | 5類型の合成(通勤/通学/買物遊興/訪日/通過)と較正・holdout 分割 | 実装済 | `src/shibuya/build/pop/w16_population.py`(9 種別 390,188 体) | 答申の 5 類型を上回る細分 |
| boundary-deep | **名簿 ≒100〜150万で在場40万を支える**(一度きり層に永続 ID を与えない) | 未採用 | `docs/design/v2-redesign.md:447`(母集団合成 DECIDED) | W16 は名簿=在場=390,188 体。**答申案への言及が決定行に無い**=理由の記録なし |
| boundary-deep | 境界通過を一級イベント `boundary_cross{9欄}`・コードン ±10% 照合・芋づる実体化禁止 | 未判定 | — | `src/shibuya/engine/presence.py` の ARRIVE/DEPART が機能的に近いが**欄も名前も違い、コードン照合も無い**。**取りこぼし候補** |
| boundary-deep | 再訪同一性の最小5つ組(persistent_id/相手ID/遭遇回数/最終遭遇/関係要約) | 設計済・未実装 | `docs/design/v2-c10-relations-agenda.md`(C10 R9′) | 関係辺は C10 のアジェンダ。`遭遇回数` は `src/` に無い |

### 2-14 conversation-deep-research(会話分析・語用論 #15・P1)— 実装済 3 / 部分 2 / 設計済 1 / 未採用 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| conversation-deep | WHO=エンジン(SSJ 1a/1b/1c)・WHEN=エンジン・WHAT=LLM(本文+宛先タグ) | 実装済 | `src/shibuya/engine/conversation.py:9`・`docs/design/v2-action-contract.md:49` | batch2 §1-2 が確認済み |
| conversation-deep | 終了を LLM に決めさせない(max_turns・沈黙閾値・定型の締め) | 実装済 | `src/shibuya/engine/conversation.py:11,38`(`BACKCHANNELS`/`CLOSING_UTTERANCE`)・`v2-action-contract.md:50` | `max_turns 3` は expedient |
| conversation-deep | **声かけ応答率 ≈0.8** | 実装済 | `src/shibuya/engine/conversation.py:82`(`ACCEPT_PROBABILITY = 0.8`) | batch2 #11 で**一次出典が見つからない**=循環参照。コードは expedient と正直に書いている |
| conversation-deep | 会話セッション状態機械 OPENING/OPEN/CLOSING/CLOSED + floor_holder + 参与役割2階層 | 部分 | `src/shibuya/engine/conversation.py`(状態機械あり) | `floor_holder` `TRP` `preclosing` `bystander` はすべて grep 0。**語彙と役割の分離が落ちている** |
| conversation-deep | 溢れを `self_selection_lost`(現象)と `no_capacity`(資源不足)に分離し後者だけ監視 | 部分 | `src/shibuya/engine/arbiter.py:1`(4クラス固定優先の繰り延べ)・`docs/design/v2-perception-contract.md` | **「破棄でなく繰り延べ」の核心は採られた**が、2 分類は採られていない(診断行は繰り延べ/昇格/縮退/抑止の4列) |
| conversation-deep | 記憶転写の重み(宛先1.0 / 非宛先0.5 / 傍受0.2・unaddressed recipient) | 設計済・未実装 | `docs/design/v2-action-contract.md:54` | 重みは決定済みだが記憶レジストリが無いので効かない |
| conversation-deep | モデル選定の合否チェックリスト8項 + 9/10 ベンチ(渋谷文脈100本+相槌20本) | 未採用 | `docs/design/v2-redesign.md:440`(B10/B11)・`:429`(品質プローブ v0) | **品質プローブ v0 + 指標B に置換**。理由の記録あり |

### 2-15 coupled-adaptation-deep-research(ABM方法論 #21・P1)— 設計済 1 / 未判定 4

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| coupled-adaptation | 時定数の階層 習慣:記憶統合:判例 = **1:5:25 以上**・失効期限は個体別ランダム化 | 設計済・未実装 | `docs/design/v2-architecture-roadmap.md`(統合設計図 §1「適応3ループ 時定数1:5:25」) | batch1 §1 が「中身を使っている可能性」と書いた通り、**名前なしで設計書に入っている**。3ループとも実装ゼロ |
| coupled-adaptation | 判例ループの**露出逆確率補正(Horvitz-Thompson)**=新規実装価値最大 | 未判定 | — | **取りこぼし候補(答申自身が「v2 に相当物がなく価値最大」と名指し)** |
| coupled-adaptation | 閉ループの禁止(習慣→判例→習慣を外生入力なしで回さない)・自己生成データ比率の上限 | 未判定 | — | D-71 の語彙成長(自己生成語→語彙)が**まさにこの形**だが、上限の宣言は無い |
| coupled-adaptation | 立ち上げ順序 記憶→習慣→判例の段階解禁(各段がそのまま ablation 系列) | 未判定 | — | 陣分け(第1陣/第2陣)はあるが**この順序ではない** |
| coupled-adaptation | 発振6指標 + 運用10計器(churn 率・扇出・影響辺カバレッジ ほか) | 未判定 | — | 計器盤 R14 は別系統(G-1〜G-9)。**適応ループ側の計器はゼロ** |

### 2-16 economy-sfc-deep-research(SFCマクロ経済学 #10・P1)— 実装済 3 / 部分 2 / 未採用 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| economy-sfc | T1 全金銭移動は `transfer(payer,payee,amount)` 単一 API・残高直接代入の**静的禁止** | 実装済 | `src/shibuya/economy/ledger.py:4,402`・`src/shibuya/engine/ledger_api.py` | batch2 §1-1 |
| economy-sfc | T2 期末 TFM の**行和0・列和0**(四重記入) | 実装済 | `src/shibuya/economy/checks.py:4,24,76` | 検算① |
| economy-sfc | **T3 冗長方程式を実装せず毎期 assert** | 未採用 | `src/shibuya/economy/checks.py`(検算①②のみ) | batch2 §1-1・§2-1 #8 が指摘。**落とした記録が無い**=5層のうち1層が黙って消えた |
| economy-sfc | R1-R3(revenue は計算値禁止 / RoW は残高部門 / 貨幣の創造消滅は2箇所だけ) | 実装済 | `src/shibuya/economy/accounts.py:4`(6部門・RoW)・`src/shibuya/cli.py:15,191`(ex nihilo 禁止) | v1 の循環定義を型で不可能にした |
| economy-sfc | 5部門+RoW の BS/TFM 雛形 | 部分 | `src/shibuya/economy/accounts.py:4`(**6部門**=銀行を含む) | U11 で 6 部門・検算 2 本に**変更済み**(`v2-redesign.md:444`)。答申の形そのままではない |
| economy-sfc | A/B 観測量(Phillips・Beveridge・マークアップ・倒産率を採用/**Okun 則系は却下**) | 部分 | `src/shibuya/economy/census.py`(月次 MER + 部門軸)・IMPLEMENTED #24 | センサスの器はあるが**採否表(何を主張に使い何を却下するか)はどこにも無い**。`Phillips` `Okun` grep 0 |

### 2-17 institutions-deep-research(法学(業法・条例) #11・P1)— 部分 1 / 設計済 2 / 未採用 1 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| institutions | エンジンが保証すべきは**5プリミティブ**(台帳・時計・集約・資格判定・配信)のみ | 設計済・未実装 | `docs/design/v2-architecture-roadmap.md:44`(1行のみ) | batch2 §1-4 の指摘どおり**制度の設計書が 1 本も無い** |
| institutions | 足場なし ablation **A0-A4**(1プリミティブずつ抜く)=v2 の新規性 | 未判定 | — | `tools/c8/ablations_v1.json` に無い。**取りこぼし候補** |
| institutions | 制度出現の**相図**(共有知識/場所/初期リーダー/罰の4軸 × 生存解析) | 未判定 | — | **取りこぼし候補** |
| institutions | 立法・規則制定=LLM が条文生成・エンジンが可決手続(行13) | 設計済・未実装 | `docs/design/v2-world-process-design.md`(D-R2-3 行13) | 第1陣 21 過程に入っていない |
| institutions | ★前提の訂正「『制度は役割知識だけでは自己実行しない(Sid の実証)』は強すぎる」 | 未採用 | `docs/design/v2-redesign.md:385`(4b 修正3 のまま)・batch2 §2-5 #25 | **答申の自己訂正が設計書 2 本に伝播していない**(親確認済みで訂正が正しいと確定) |
| institutions | 制度を**独立変数**として実験設計(背景にしない) | 部分 | `src/shibuya/world/processes/records.py:6`(軸3 規範種別・軸4 違反可能性)・`first_batch.py`(`Violability`) | 制度を**属性として持つ**ところまでは実装。振る実験は無い |

### 2-18 legal-licensing-deep-research(研究倫理・情報法 #31・P1)— 実装済 2 / 部分 1 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| legal-licensing | データ台帳(データセット × ライセンス × 商用可否 × 出典文字列) | 実装済 | `docs/data-license-ledger.md`・`CLAUDE.md §7`(取得ごとに行追加)・`src/shibuya/manifest/schema.py:202`(`license_row`) | **manifest の資産欄に license_row が必須列としてある**=最も深く入った項 |
| legal-licensing | モデル=Qwen3 系(Apache 2.0)主軸・Swallow は研究限定 | 実装済 | `docs/design/v2-redesign.md:464`(R16)・IMPLEMENTED #16(Qwen3-8B INT8)・`:440`(B10 で Swallow 不採用) | 答申の推奨と実運用が一致 |
| legal-licensing | 層分離アーキテクチャ(OSM/PLATEAU/ODPT/人流を data type 単位で物理分離・重複統合しない) | 部分 | `src/shibuya/build/{geo,field,lang,pop,sched}/`(段階分離) | 段階では分かれているが **Collective Database を維持するという宣言と検査は無い** |
| legal-licensing | **出力スキーマから OSM 生値を排除**(内部 ID + 集計のみ) | 未判定 | — | テープ・診断行に OSM 生値が載らないことを検査する仕組みが無い。**取りこぼし候補(法務リスク直結)** |
| legal-licensing | 専門家確認 14 論点 | 未判定 | — | 論点表が設計書に無い |

### 2-19 llm-serving-deep-research(NLP #27 / 計算機科学 #28・P1)— 実装済 4 / 部分 1 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| llm-serving | 艦隊構成 A「均質 DP7 + アフィニティルータ」 | 実装済 | `src/shibuya/llm/fleet.py:13`(`xxhash(call_id) mod 7`・不均衡時 least-in-flight)・`v2-redesign.md:464` | |
| llm-serving | 量子化=W8A8-INT8(高 QPS サーバ用・A5000 では FP8 が効かない) | 実装済 | IMPLEMENTED #3(INT8 支配)・#16(Qwen3-8B INT8) | ベンチで実証してから採用 |
| llm-serving | prefix caching のため**固定節を必ずプロンプト先頭へ**・cache_salt で分離 | 実装済 | `docs/design/v2-redesign.md:433`(§5 prefix 規約)・`src/shibuya/perception/templates.py`・`src/shibuya/engine/run.py:429`(`cache_salt`) | |
| llm-serving | 優先度4クラス(P0 会話 > P1 群衆 > P2 内省 > P3 オフライン) | 実装済 | `src/shibuya/engine/arbiter.py:1`(会話ターン>計画境界>個体変化>セル変化) | クラスの中身は違うが**4クラス固定優先という形が一致** |
| llm-serving | **バックプレッシャ3段**(段3=シミュ時計の tick 間隔延伸・TiDi) | 未判定 | — | `TiDi` `バックプレッシャ` grep 0。答申が「先行ゼロ=v2 の独自設計」と名指しした項。**取りこぼし候補(上位)** |
| llm-serving | 冪等 `request_id = (agent_id, sim_day, tick, call_kind)` の決定論ハッシュ・再送3回+全体10%予算 | 部分 | `src/shibuya/llm/fleet.py`(`call_id`・§7 失敗の意味論) | call_id はあるが**冪等キーとしての宣言と再送予算は無い** |
| llm-serving | 会計=**円/シミュ日・円/エージェント日・T2 呼び出し率** | 未判定 | — | GPU 秒/体は D-70 にあるが金額換算の会計は無い |

### 2-20 observation-projection-deep-research(検証とV&V・UQ #22・P1)— 設計済 3 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| observation-projection | L-OBS = イベントログの決定論的射影(filter ∘ quantize ∘ fold)・**乱数消費0本・affects_k=False** | 設計済・未実装 | `docs/design/v2-redesign.md:395`(U4=Phase 4 以降の観測アプリ) | 「コア設計への影響ゼロ」という決定なので未実装は設計どおり |
| observation-projection | 7チャネル(CH-SNS/CELL/GNSS/WIFI/POS/CAM/SURVEY)+ **p_detect がバイアスの本体** | 設計済・未実装 | 統合設計図 §1 | `p_detect` `CH-CELL` grep 0 |
| observation-projection | L-REC 推定器階層 R0-R6(R6=観測のみからの k* ランキング vs 真値の順位相関) | 設計済・未実装 | 統合設計図 §1 | |
| observation-projection | obs_public / obs_link の**物理的二層分離**(採点器だけが対応表を読む) | 未判定 | — | 設計書にも無い。**取りこぼし候補** |
| observation-projection | 3攻撃並走(main/control/baseline)+ blind baseline が main を上回った実験は破棄 | 未判定 | — | **取りこぼし候補** |

### 2-21 parallel-execution-deep-research(計算機科学(並列・決定論) #28・P1)— 実装済 3 / 部分 2 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| parallel-execution | 三相 propose(副作用禁止)→ resolve(純関数)→ commit(勝者のみ状態変更) | 実装済 | `src/shibuya/engine/commit.py:1,6`(Phase A/B)・`src/shibuya/engine/resolve.py`(単一書き込み口) | |
| parallel-execution | **敗者に明示的な失敗イベントを配送**(v1 の暗黙スキップを止める) | 実装済 | `src/shibuya/agents/state.py:199`(`LOST_ARBITRATION`) | 答申の「失敗が観測可能な出来事になる」がそのまま実装 |
| parallel-execution | counter-based RNG `(seed, domain, tick, entity, draw)`・到着順/スレッド数/シャード非依存 | 実装済 | `src/shibuya/core/rng.py`(Philox ドメイン分離)・`src/shibuya/core/hashing.py:53`(`priority_key`) | T4 規模不変性で検証済み(IMPLEMENTED #10) |
| parallel-execution | 優先規則 = **RSD + 待ち時間チケット(aging)**・id順/登録順は禁止 | 部分 | `src/shibuya/engine/commit.py:388-390`(`pk=(t_notice, blake3撹拌)` の辞書式) | id順の禁止は達成。**RSD(一様ランダム順列)でも aging でもない別形**。`aging` 相当は `arbiter.py` の T_MAX 昇格にだけある |
| parallel-execution | 検証テスト7本(T1 置換対称性 / T5 投函順シャッフルでビット一致 / T6 並列直列一致 ほか) | 部分 | `src/shibuya/engine/arbiter.py`(並び順非依存の性質テスト)・`src/shibuya/engine/commit.py:618`(順序バイアス |r|≤0.05) | 7 本のうち置換対称性・順序バイアス・並列不変性は実装。**Jain 公平性指数・飢餓有界は無い** |
| parallel-execution | 摩擦パラメータ μ(競合関与者全員の移動が拒否される確率・既定0) | 未判定 | — | `摩擦` grep 0。**取りこぼし候補(混雑の詰まり再現に直結)** |

### 2-22 pattern-ledger-deep-research(ABM方法論 #21・P1)— 実装済 2 / 部分 2 / 設計済 1 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| pattern-ledger | ①コア 8-12 本(強3-4+弱5-8)を4階層に分散 | 実装済 | `docs/design/v2-pattern-ledger.md`(34→40行・4階層・強5本)・`v2-redesign.md:401`(U12) | Phase 0 ゲートの実体 |
| pattern-ledger | ②各行に `judgment_type{quantitative_band, ordinal, existence, shape}` + **再現可能な判定関数への参照**を必須化 | 未判定 | — | `judgment_type` grep 0。台帳は散文の判定記述。**取りこぼし候補(機械化の要)** |
| pattern-ledger | ⑤ holdout 管理 `status{holdout, calibration, burned}` + burned_at・二次予測用に最低2本封印 | 実装済 | `docs/design/v2-pattern-ledger.md:16`・`src/shibuya/build/audit/w19_freeze.py:6,39`(S 層封印の静的ゲート) | 封印が**構築コードから読めないことの機械検査**まで入っている |
| pattern-ledger | ④独立性チェック(パターン間相関を実測し**実効本数**を記録) | 部分 | d1-reacquisition の勧告「D1′+D4′=1.5本」 | `源泉従属` は設計書に grep 0。**実効本数の記録欄が無い** |
| pattern-ledger | ⑦ attrition 表の常設 | 設計済・未実装 | `docs/design/v2-pattern-ledger.md:18` | 出力する道具が無い |
| pattern-ledger | 第一次採用候補7本(P03 会話グループ/P28 カスケード99%/P01 接触時間/P41 関係年率/P34 犯罪集中/P20 生活時間/P43 気分) | 部分 | `docs/design/v2-pattern-ledger.md`(強5本に A1 会話グループ・C1 カスケード) | 7 本中 2 本が強行に昇格。**P34 犯罪(分野 #32 に答申ゼロ)・P43 気分は台帳に無い**。batch1 は P01 の定義取り違えも指摘 |

### 2-23 persona-population-deep-research(人格心理学 #13 / 人口学 #1・P1)— 実装済 1 / 部分 2 / 未採用 2 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| persona-population | ② 従業地・通学地は後付けレイヤ(Murata 法・国勢調査従業地通学地集計を制約に) | 実装済 | `src/shibuya/build/pop/w16_population.py`(通勤 215,893/通学 33,385・方面 JSD 8.5e-04) | 答申の「v1 プール再利用の根拠」がそのまま実装 |
| persona-population | ① 世帯を主語に(村田研データか Kajiwara 推計を外生入力に) | 未採用 | `docs/design/v2-redesign.md:447`(母集団合成 DECIDED)・IMPLEMENTED #15(世帯財布 anchors 67.5/32.5) | **個人生成→世帯を後付け**=答申が「劣る」とした形。理由の記録は無い |
| persona-population | 分散注入4レバー(名簿 > 伝記 > **活動性 a_i の外生配布** > デコーディング) | 部分 | `src/shibuya/build/pop/pool.py`(名簿)・IMPLEMENTED #19(W17 v2=本人が書くブロック=伝記寄り) | **a_i の外生配布はゼロ**(`活動性` grep 0)。答申は「参加不平等の再現に唯一の実証済み経路」としていた |
| persona-population | 計器盤の分散指標9種(SD比 / 上位1%・10%集中率 / Gini / 裾指数 / 意味的凝集度 ほか) | 未判定 | — | 計器盤 R14 に無い。M2 種類率・H(bit) は別物。**取りこぼし候補** |
| persona-population | LLM 自由生成ペルソナ禁止(裾の片側切除) | 未採用 | IMPLEMENTED #19(W17 v2=本人が書く)・MEMORY「多様性は LLM から」 | **ユーザー選好で明示的に逆へ倒した**=理由の記録あり |
| persona-population | ⑤ 検証台帳に zeros 率・分類器2標本 AUC・Cramér's V 差を追加 | 部分 | IMPLEMENTED #14(SRMSE・JSD・空セル0) | 空セル 0(=zeros 率)は実装。AUC と Cramér's V は無い |

### 2-24 precedent-system-deep-research(法学 #11・P1)— 部分 3 / 未判定 3

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| precedent-system | 判例レコードスキーマ(事実群/法理群=**ratio と dicta の分離**/結果群/境界群 BASM4項/失効群) | 未判定 | — | `ratio` `dicta` `distinguishing` は `v2-inventory-and-bottlenecks.md` の棚卸し列挙のみ。**取りこぼし候補** |
| precedent-system | 検索4段 L1 完全一致 → L2 a fortiori 機械判定 → L3 埋め込み(候補提示まで)→ L4 distinguishing 検査 | 未判定 | — | `src/shibuya/llm/undefined.py:7` は「2回目以降は決定論参照」までで段構成が無い |
| precedent-system | 裁定パイプライン6段(特権分離 → 小型一次 → 信頼度ゲート → 争点のみ委員会 → **保存則の機械検証** → 全件記録) | 部分 | `docs/design/v2-redesign.md:457`(R8=未定義行動5段)・`tools/vocab/adjudicate.py`(段2 起草 + 段3 静的検査 s1〜s6) | 実装は段0〜2 と静的検査。**保存則の機械検証・委員会・信頼度ゲートは無い** |
| precedent-system | ルールライフサイクル5段(候補=独立3事例 → 反証強制 → 試用シャドウ→5%→25% → 本採用 → 失効) | 部分 | `docs/design/v2-vocab-growth-design.md`・`tools/vocab/`(下限 N=10・件数予算10) | 語彙側に**同型の段が入った**(候補化の閾値は3事例でなく N=10 体)。判例側は未 |
| precedent-system | 信頼性目標: 裁定 κ≥0.6(人間金標準)・判例**誤ヒット率 ≤1% を先に固定** | 未判定 | — | `docs/design/v2-redesign.md:457` は「判例ヒット率・裁定コスト・矛盾率」を計測項目に挙げるが**目標値が無い** |
| precedent-system | 規則数予算(同時提示 ≤10-12 条・ライブラリのプロンプト占有 ≤5%) | 部分 | IMPLEMENTED #23(B0 が列挙するのは横断 12 語)・`src/shibuya/llm/contract.py`(24 語) | 同時提示 12 という**同型の上限が偶然成立している**。予算として宣言はされていない |

### 2-25 person-perception-verification(知覚心理学・精神物理学 #5・P1)— 実装済 5 / 部分 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| person-perception | M1 聴覚チャネルの新設(voice 0.48 > gesture 0.31 の ablation) | 部分 | `docs/design/v2-redesign.md:420`(R3-7 DECIDED)・`src/shibuya/perception/attention.py:9`(ΔSNR −3/−12)・`src/shibuya/engine/commit.py:453` | チャネルは実装。ただし**雑談の可聴距離 1-2.5 m は「同一セル」で代理**(C3 の縮退・コード内に明記) |
| person-perception | M2 段④を「近接他者上位 k(k=3-4)」へ拡張 | 実装済 | `docs/design/v2-redesign.md:417`(人物観測5段)・`src/shibuya/perception/channels.py`(B5 近接k) | MOT 容量 3-4 の実証値がそのまま入った |
| person-perception | M3 第5段「被注視性/exposure」の新設(isovist の転置=ほぼ無料) | 実装済 | `src/shibuya/agents/state.py:247`(`BEING_WATCHED` 起床条件)・`:265`(不応期5) | |
| person-perception | M4 密度を連続量でなく**Fruin LOS 型の順序尺度**に量子化 | 実装済 | `src/shibuya/world/state.py`(`DENSITY_STAGE`)・`src/shibuya/engine/geometry.py:280` | 「忠実度とキャッシュ経済が同じ方向を指す稀な例」が実装で確認された |
| person-perception | M5 配送は全員・**注意到達は確率的**に分離 | 実装済 | `src/shibuya/perception/p_notice.py`(2段ヒル型)・`src/shibuya/engine/processes/civic.py:16`(注意ゲート段2 上位1-2) | |
| person-perception | L1-L3 キャッシュの3つの落とし穴(512tok 最小・同時 fan-out・prefix 順序の排他) | 実装済 | `docs/design/v2-redesign.md:427`(BN-4/BN-5 で予算確定)・`src/shibuya/llm/fleet.py`(BN-4 順序制御) | **答申の指摘がベンチ設計に反映され実測で解決された**数少ない例 |

### 2-26 ugc-platform-import(ゲームエンジン工学 #30 / SFC #10・P1)— 実装済 6 / 部分 1 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| ugc-platform-import | #7 効果型を resolve の契約に(`pure`/`reads`/`writes`/`rollbackable`/`suspends` を宣言し静的ゲート) | 部分 | IMPLEMENTED #10(resolve 単一書き込み口=AST 検査) | **書き込み口の検査までは入ったが 5 値の効果型宣言は無い** |
| ugc-platform-import | #12 知覚契約を Replication Graph の5ノード分類で設計 | 実装済 | `docs/design/v2-redesign.md:413`(R3-1 DECIDED)・`src/shibuya/perception/channels.py`・`hashes.py:4`(dormant) | |
| ugc-platform-import | #13 prefix 規約(静的 → セル共有 → 個体 → 問い・共有ブロックにエージェント固有語を入れない・バイト一致) | 実装済 | `docs/design/v2-redesign.md:433`・`src/shibuya/perception/normalize.py`(正規化9項)・`templates.py` | ヒット率の実測(1.6-2.0x)まで完了 |
| ugc-platform-import | #14 行5=内生フロア + 逸脱に比例するコスト(禁じず課金する) | 実装済 | `docs/design/v2-redesign.md:442`(D-R2-3 行5 A案)・`src/shibuya/economy/pricing.py`・`accounts.py:136`(逸脱比例コスト) | |
| ugc-platform-import | #22 経済センサスを **MER 形式で月次出力**(科目別・地域別・価格指数群) | 実装済 | `src/shibuya/economy/census.py`(`monthly_mer` + `per_sector`)・IMPLEMENTED #23/#24 | 地域別軸(丁目/駅勢圏)は未 |
| ugc-platform-import | #23 残差科目を必ず1つ置く / #24 退蔵在庫項を保存則に含める | 実装済 | `src/shibuya/economy/accounts.py:128`(`RESIDUAL`)・`:7`(退蔵項) | UO の死因(在庫退蔵)への対策がそのまま科目になった |
| ugc-platform-import | #19/#20 δ思考時間を **TiDi 型の制御器**に・時計ごとに `dilatable: yes/no` を宣言 | 未判定 | — | `TiDi` `dilatable` grep 0。llm-serving のバックプレッシャ段3 と同一の穴 |
| ugc-platform-import | ④移入禁止9件(エンゲージメント最適化・人為的希少性・外部換金・矯正目的の制裁 ほか) | 実装済 | `docs/design/v2-redesign.md:411`(UGC 正典化=移入禁止9件は恒常規律) | 「設計者の指紋の最小化」(CLAUDE.md §2-3)と一体で運用 |

### 2-27 world-ledger-verification(ABM方法論 #21・P1)— 実装済 6

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| world-ledger-verification | (a) 台帳は1つ・レコード型は3つ(WorldProcess / PlanSpec / ActualLog) | 実装済 | `docs/design/v2-redesign.md:409`(D-R2-2)・`src/shibuya/world/processes/records.py` | 答申の修正案がそのまま決定になった |
| world-ledger-verification | (b) 論拠の差し替え(変わるのはダイヤでなく **executor**) | 実装済 | `src/shibuya/world/processes/records.py:57,75`(`LLM_AGENT`/`ENGINE_RULE`/`AGENT_FALLBACK`) | フォールバックが `AGENT_FALLBACK`(返済期限つき expedient)として型に入っている |
| world-ledger-verification | (c) 逸脱語彙を最初から第1級に(GTFS-RT 式の列挙型・NO_DATA を含む) | 実装済 | `src/shibuya/world/processes/actual_log.py:4,108`・`first_batch.py:757`(SCHEDULED/CANCELED/REPLACEMENT/SKIPPED/NO_DATA/DELAY) | |
| world-ledger-verification | (d) 第3軸(規範種別)+ 第4軸(違反可能性)の追加 | 実装済 | `src/shibuya/world/processes/records.py:6`・`Violability`(REGIMENTED/ENFORCED/UNENFORCED) | |
| world-ledger-verification | (e) 軸1に第4の値 `static-affordance`(物理インフラ) | 実装済 | `src/shibuya/world/processes/records.py:84`(`PHYSICAL_AFFORDANCE`) | |
| world-ledger-verification | (f) ActualLog に O(t) 禁止則(追記専用・保持窓・増分索引を型で強制) | 実装済 | `src/shibuya/core/growth.py:7`・`src/shibuya/world/processes/actual_log.py:15,359`(保持窓超過は日次集約行へ) | runB(v1 の RAM 13.6 倍)の再発地点を型で塞いだ |

### 2-28 area-boundary-map-reading(地理情報科学 #9・P1)— 実装済 1 / 部分 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| area-boundary-map-reading | 分割線3本(JR 線 / 国道246号 / 六本木通り)+ 5エリア外周 | 実装済 | `docs/design/v2-redesign.md:426`(D1′=(b) expedient 境界で強採用)・`tools/c7/` の area 写像(`occupancy_series.build_map`) | 図1(`tools/fig/fig_presence_24h.py`)がこの写像を再利用 |
| area-boundary-map-reading | 検証: SCJ 施設 214 件を多角形に落とし属性一致率を報告(<90% なら境界を見直す) | 部分 | IMPLEMENTED #6(KDDI 23 枚スクショ検証) | **214 件の一致率の記録が見当たらない**。別の検証で代替された可能性 |
| area-boundary-map-reading | expedient 登録(KDDI 集計ポリゴンとの一致は未検証・境界 ±50m の感度試験) | 部分 | `docs/design/v2-redesign.md:426`(expedient 宣言)・hearing-numbers §②(ポリゴン非公開の確定) | 宣言は済み。**±50m の感度試験は未実施**(`tools/c8/sensitivity.py` の台帳に該当行なし) |

### 2-29 kddi-attribute-shares-2024(人口学・合成人口論 #1・P1)— 部分 1 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| kddi-attribute-shares | 滞在 × 渋谷との関係(勤務者/居住者/来街者)のシェア | 部分 | `tools/c7/presence_yardstick.py`(`D66_KINDS`・`LODGING_KINDS`)・IMPLEMENTED #20 | 種別の物差しとして使われている。台帳行としては弱/holdout 止まり |
| kddi-attribute-shares | 滞在 × 性別・年代のシェア | 未判定 | — | 母集団の raking は国勢調査(`src/shibuya/build/pop/fitting.py`)であって KDDI 属性ではない。照合にも使われていない |

### 2-30 cell-granularity-research(地理情報科学 #9 / 計算機科学 #28・P1)— 実装済 4 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| cell-granularity | 第1候補 = 100m 格子を維持(決め手は較正コスト) | 実装済 | `src/shibuya/build/geo/w2_cells.py`・`src/shibuya/build/audit/w18_coverage.py:73`(「セル(場所100m+層)」) | 520 place_id(GL 453/DECK 39/UG 28) |
| cell-granularity | B-2 セルIDを `place_id` という抽象にし、単位型を将来の可変軸に | 実装済 | `src/shibuya/agents/state.py:341`(所属セル=place_id 索引) | |
| cell-granularity | B-3 B4 を2層に割る(B4=セル 100m の場 / B4b=サブセル 25m 級の構造物) | 実装済 | `src/shibuya/build/lang/w15_cell_static.py:19`・`src/shibuya/engine/processes/crowd.py:20`(B4b 配線済み) | |
| cell-granularity | BN-1 の軸を「セル数」から **B_cell / d / Zipf α / 階層数**へ差し替え | 実装済 | `docs/design/v2-redesign.md:427`(BN-4/BN-5 で確定) | 答申の指摘(契約実値 500 tok で測り直せ)が反映 |
| cell-granularity | 50m 格子は「棄却」でなく**保留・測定待ち**(p90(add) が閾値超なら復活) | 未判定 | — | B5 差分の測定(4 通りの place_id で add/del/Jaccard)を実施した記録が無い |
| cell-granularity | blockface(100m 格子 ∩ 街区)を第2候補として忠実度試験に同時投入 | 未判定 | — | `blockface` grep 0。**取りこぼし候補** |

### 2-31 d1-reacquisition(人間移動科学 #3・P1)— 実装済 3 / 部分 1 / 未採用 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| d1-reacquisition | D1′ = KDDI 滞在人口(5エリア × 24時)で強維持・判定は3指標(24h シェア JSD / ピーク時刻の順序 / 深夜残存率の順序) | 実装済 | `docs/design/v2-redesign.md:423`(DECIDED)・`tools/c7/presence_yardstick.py`・`tools/fig/fig_presence_24h.py` | 現在の最重要ゲートそのもの |
| d1-reacquisition | 旧 D2=4.39倍・D3=14時を**破棄** | 実装済 | 同上(D2′ 7.51倍・D3′ 18時) | |
| d1-reacquisition | D1b(Agoop 3アンカー)を弱行で残しベンダ独立の交差検証に | 実装済 | IMPLEMENTED #5(D1b 新設)・`docs/design/v2-pattern-ledger.md` | |
| d1-reacquisition | D1′+D4′ は**源泉従属** = 強5本の独立性計上では 1.5 本として扱う | 部分 | `docs/design/v2-pattern-ledger.md`(強5本の表) | `源泉従属` のタグが設計書に grep 0。**実効本数の管理が入っていない**(pattern-ledger ④ と同じ穴) |
| d1-reacquisition | 5エリアポリゴンと bbox の被覆確認を D1′ 採用の**前提条件**にする | 未採用 | hearing-numbers §②(ポリゴンは公開されていない=確認不能)・`v2-redesign.md:426`(expedient 境界で代替) | **確認できないことが確定したので前提条件を外した**=理由の記録あり |

### 2-32 hearing-numbers-and-d1-coverage(環境音響学 #6・P1)— 実装済 3 / 部分 1 / 未採用 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| hearing-numbers | ISO 9921:2003 の SIL は「A特性発話レベル − 4帯域平均暗騒音」= **実質 SNR 量**(R3-7 が SNR で書くのは正しい) | 実装済 | `docs/design/v2-redesign.md:420`(R3-7)・`src/shibuya/perception/attention.py:9`(ΔSNR) | |
| hearing-numbers | 暗騒音 70 dBA での通常声の会話可能距離 ≈0.4-0.6 m(R3-7 の暫定値は 3〜7 dB 保守的) | 部分 | `src/shibuya/engine/commit.py:453`(雑談 1-2.5 m → **同一セルで代理**) | 数表は答申で確定したが**実装は 100m セルの粒度に飲まれている** |
| hearing-numbers | Brungart 2020「人は騒音が上がっても距離を詰めない(≈1m 固定)」→ 半径を騒音依存で縮める設計は正しい | 実装済 | `docs/design/v2-redesign.md:420`(密度駆動の可聴半径) | 「うるさいと近づく」を実装しない根拠が一次で確定 |
| hearing-numbers | 渋谷区「音のめやす」大声 88-99 dB は**距離未定義の孤立値**=アンカーにしない | 未採用 | 同上(R3-7 は環境省自動車騒音常時監視+東京都調査を採用) | 答申の勧告どおり採らなかった=理由の記録あり |
| hearing-numbers | 5エリアポリゴンは非公開(ArcGIS 全サービス走査で確認)=D1′ の前提は別ルートへ | 実装済 | `docs/design/v2-redesign.md:426`(expedient 境界) | **空欄を空欄として確定させた**作業がそのまま決定を動かした |

### 2-33 vlm-reality-check-research(検証とV&V・UQ #22・P1)— 実装済 3 / 部分 1 / 設計済 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| vlm-reality-check | エンジンを真値扱いしない(対称な二推定器 + 人手裁定セット) | 実装済 | `docs/design/v2-redesign.md:421`(R3-6a 修正案7項で採用) | 決定として正典化・測定装置は未起動 |
| vlm-reality-check | 店舗計数・歩道幅は VLM でなく**専用 CV/幾何**へ・VLM は静的言語化の品質と印象スコアに限定 | 実装済 | 同上 | |
| vlm-reality-check | 混雑段階を画像ルーブリックから**削除**し人流データで照合 | 実装済 | 同上・`docs/design/v2-redesign.md:423`(D1′) | |
| vlm-reality-check | Mapillary を第一候補にし、40m 間隔点の 60% 以上で有効画像が取れることを着手前に確認 | 設計済・未実装 | `docs/design/v2-perception-contract.md`(Mapillary) | `src/`・`tools/` に Mapillary ゼロ。着手前確認も未実施 |
| vlm-reality-check | R3-3(看板の静的言語化)との**循環回避**=標本点の 60/20/20 分割を初期化パスより前に | 部分 | IMPLEMENTED #15(W14 看板文 2,302 店を生成済み) | **分割を先にやった記録が無いまま看板文が生成された**=循環リスクが残っている可能性 |

### 2-34 implementation-stack-research(ソフトウェア工学 #29 / 計算機科学 #28・P1)— 実装済 5 / 部分 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| implementation-stack | 言語 = Python 3.12 + NumPy/Numba(CPU)・GPU は **Warp**(numba.cuda は保守モードなので採らない) | 部分 | `docs/design/v2-redesign.md:449`・`pyproject.toml:11`(「GPU(warp-lang/cupy)は C0 では入れない」)・`src/shibuya/build/geo/w3_distances.py:21`(numba) | CPU 側は実装。**GPU 層は C9 時点で未着手**(C9a も CPU 解析式) |
| implementation-stack | 部品表(blake3 / xxhash / httpx / vLLM / pyarrow / duckdb / zstandard / pytest / hypothesis / import-linter / pydantic) | 実装済 | `src/shibuya/core/hashing.py:41`・`src/shibuya/core/serialize.py:40`・`pyproject.toml:21,29,52` | **asv だけ未導入**(`tests/engine/test_scheduler_p3.py:5` が「本来 asv で見る」と注記) |
| implementation-stack | 層契約を import-linter で強制(上→下の import のみ) | 実装済 | `pyproject.toml:52,56`(契約5本)・IMPLEMENTED #9(0 broken) | |
| implementation-stack | データ層 = Parquet + DuckDB + npz/mmap・**個体×tick の全記録は禁止** | 実装済 | `src/shibuya/agents/weekly.py`(parquet)・micro-observation O4 が同じ算術で再確認 | 5.76 億行/日=禁止 |
| implementation-stack | Rust 移行条件を事前宣言(P2/P3 の2倍超過・P6 不達・GIL 干渉) | 実装済 | `docs/design/v2-redesign.md:449` | 宣言が決定台帳に入っている |
| implementation-stack | expedient E1-E9 の登録(単一プロセス asyncio・P6 の xxhash・CI 相対ゲート・ルーティング・タイムアウト ほか) | 部分 | IMPLEMENTED #9(実装計画書 §8 C0 節へ登録) | **E1-E9 の全部が登録されたかは確認できない**(`tools/c8/sensitivity.py` の台帳の分母は構築仕様 §2 の 14 行) |
| implementation-stack | CI の性能ゲートは相対比較(共有ランナーの絶対時間は誤検出する) | 実装済 | `tests/engine/test_scheduler_p3.py:5` | |

### 2-35 run-manifest-concurrency-research(ソフトウェア工学 #29 / 計算機科学 #28・P1)— 実装済 5 / 部分 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| run-manifest | manifest 13 節(自己ハッシュ run_id・prereg 封印・holdout 封印・資産のライセンス行・LLM 艦隊欄・並行意味論の版) | 実装済 | `src/shibuya/manifest/schema.py:120-219`(`run_id`/`hypothesis`/`sealed_at`/`license_row`/`seal_scheme`)・IMPLEMENTED #9 | **答申の設問リストがほぼ逐条で pydantic モデルになっている** |
| run-manifest | 再現性の三層宣言(エンジン=numerical identity / LLM=分布同値 / 結合系=関係整合) | 実装済 | IMPLEMENTED #16(T6 bit 再現 833/833・T7 JSD 0.0035) | Wilensky & Rand の3分類がそのまま運用語彙に |
| run-manifest | 並行意味論 C1-C10(二相同期・pk・書き手の単一性・apply_key・RNG domain 分離・class_rank・C9 順序バイアス監査) | 実装済 | `src/shibuya/engine/commit.py:6-15,388-390,618`・`src/shibuya/core/hashing.py:53`・`src/shibuya/core/rng.py` | C9 の |r|≤0.05 ゲートまで実装 |
| run-manifest | テスト T1-T9 | 部分 | IMPLEMENTED #9/#10/#16(T1/T2/T3/T4/T5/T6/T7/T9) | **T8(アンサンブル安定性)だけ未**。`tools/c8/ensemble.py` は設計のみでランを回さない |
| run-manifest | expedient 登録6項(ハッシュ撹拌・δ_perc を勝敗に使う・再試行1回・class_rank 制度=−1・counter-based RNG・保持窓) | 実装済 | `src/shibuya/engine/commit.py:12,28,395`(第2希望が無いので空回りすると明記) | **劣化版であることをコード内に正直に書いている** |
| run-manifest | BATCH_INVARIANT の要求 CC が公式2ページで食い違う → 自検証せよ | 実装済 | `docs/design/v2-redesign.md:467`(B14 測定完了・A5000 CC8.6 で不変性成立・コストゼロ) | 答申の「1本測る価値あり」が実行された |

### 2-36 ethics-operations-research(研究倫理・情報法 #31・P1)— 設計済 3 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| ethics-operations | ①〜⑦への適用案(4層×Five Safes・censored/uncensored 両 ablation・観察と公開フィルタの分離・U18・PoliSim 3前提・審査不要3本立て・Datasheet 固定文) | 設計済・未実装 | `docs/design/v2-redesign.md:459`(R17 E-1〜E-7 DECIDED)・`docs/design/v2-ethics-safety-operations.md` | 設計書はあるが `src/` に検出器・伏字・注記の実装はゼロ |
| ethics-operations | CitySim/CityReal の Ethics Statement 3点(バイアス増幅・行動誘導・実住民の代替禁止)が最低ライン | 設計済・未実装 | `docs/design/v2-ethics-safety-operations.md` | 渋谷を名指しした先行2本の存在が最大の収穫 |
| ethics-operations | 「介入せず観察」と「公開時フィルタ」を台帳2行で分離・**介入回数=0 を毎ラン検証** | 未判定 | — | 検証コードが無い。**取りこぼし候補(自己申告が検査されていない)** |
| ethics-operations | 訂正受付窓口=最小の当事者参加 | 設計済・未実装 | `docs/design/v2-ethics-safety-operations.md:41` | v2 の最も弱い点と自認 |

### 2-37 price-formation-llm-research(小売科学 #17 / 行動経済学 #16・P1)— 実装済 4 / 未採用 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| price-formation | H-1 Calvo 改定頻度を業種別に(小売 20-30%/月・**飲食 5-10%**・サービス 5%) | 実装済 | `docs/design/v2-redesign.md:461`(行5 追補 DECIDED)・`src/shibuya/economy/pricing.py` | Higo–Saita の外食 5.0%/月 を親が一次確認 |
| price-formation | H-2 内生フロア k を FL 基準で(FL60+その他30+利益10・業態別 2.9/3.3/5.0) | 実装済 | 同上・`src/shibuya/economy/pricing.py` | 金融庁委託文書で確定 |
| price-formation | H-3 r のクリップ `r∈[0.7,1.5]` + 失敗時は前期 r 維持 + 計数 | 実装済 | 同上 | |
| price-formation | H-5 Fish 型の「価格上限テキスト」は不要(r スカラーが構造的上限) | 実装済 | 同上 | 不採用の決定として記録 |
| price-formation | H-4 逸脱比例コストの較正に店舗間価格分散(Ueda 2024) | 未採用 | 同上(数値未取得のため保留)・`src/shibuya/economy/accounts.py:136`(科目だけ存在) | **原典が認証リダイレクトで未取得**=空欄が理由。E7 アンカー登録は保留 |

### 2-38 r2-llm-social-sim-fulltext-check(計算社会科学 #25 ほか・P1)— 部分 3 / 未判定 3

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| r2-fulltext | (a) 報告様式を「分布」に変える(不確実性区間+分散分解・選んだ軌跡で出さない) | 部分 | `tools/c8/dashboard.py`(G-8 分布で報告)・`tools/fig/fig_seed_pair.py`(CV(n=2)) | 器はある。**8 seed のアンサンブルは未実行(2 seed)** |
| r2-fulltext | (b)「内部整合性は verification であって validation ではない」を受入表の欄に | 部分 | `tools/c8/dashboard.py`(面1=報告 / 面2=唯一のゲート) | 3 面分離が同型。「主観/客観/内部整合」の欄は未追加 |
| r2-fulltext | (c) パターン台帳に「データ漏洩の疑い」欄を足す | 未判定 | — | 1 列足すだけの提案が未実施。**取りこぼし候補(最も安い)** |
| r2-fulltext | (d) TRAILS-D 8次元 × TRAILS-R 5次元の**被覆表**を C8 に付ける | 未判定 | — | `tools/c8/` に無い。空白は Model substrate・Agent specification・TRAILS-R 全5次元 |
| r2-fulltext | (f) B5 の近接 k に **k=0 の腕**(他者情報は少ない方が均衡に近い) | 未判定 | — | `tools/c8/ablations_v1.json` に無い |
| r2-fulltext | (l) D-70 の比較表を「体あたり GPU 秒」で書き直す(OASIS は N^1.55 で超線形) | 部分 | PENDING D-70(0.592 GPU·s/体/シミュ日) | 単位は入った。**中間規模 1 点の測定は未**(2-12 の N 系列と同じ穴) |

### 2-39 r23-primary-check-batch1(検証とV&V #22 / 計算社会科学 #25 / ABM方法論 #21・P1)— 実装済 1 / 部分 2 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| r23-batch1 | D-74「値を直す 4 件」 | 部分 | `v2-game-frontend-research.md`(UE5 の第203 訂正)・`v2-memory-retrieval-research.md`(Ruri の第203 訂正) | 2 件は答申本文に訂正が入った。**pattern-ledger の定義取り違え(P01)は台帳側に反映されていない** |
| r23-batch1 | §5-3 **写し検査**(設計書の数値 → 答申 → 原典の2段突合) | 未判定 | — | 運用化の記録が無い(R-23 に登録されただけ)。**取りこぼし候補(運用規律)** |
| r23-batch1 | §5-3 **訂正の伝播検査**(答申に訂正が入ったら引いている設計書を grep) | 部分 | IMPLEMENTED 第210(D-78 文書訂正 10 ファイル) | 一度は実行された。**常設の検査にはなっていない**(2-11・2-17 で未伝播が残る) |
| r23-batch1 | §5-2 案(b) 特徴値 grep を1回回す | 実装済 | `v2-r23-primary-check-batch2.md` §1 | 提案がそのまま次の答申になった |

### 2-40 micro-observation-research(検証とV&V #22 / ABM方法論 #21 / ソフトウェア工学 #29・P1)— 設計済 4

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| micro-observation | O1-O4 個体カルテ=1体×1日の変化点列 / 場所カルテ=place_id × 15分ビン・**全数 520**(24MB/日) | 設計済・未実装 | PENDING D-80・`docs/research/v2-micro-observation-research.md` §2 | 09-17 のアジェンダ。`カルテ` は `src/` に grep 0 |
| micro-observation | O5-O7 3層抽出(無作為/層化/指名)・**再生で事後に作る**・read-only 観測者 | 設計済・未実装 | 同上・第177 の親評価(テープ再生が決定論) | 追加ラン 0 本・S1 追加 0 バイトで作れるという算術まで出ている |
| micro-observation | O11-O16 逸話3段(観察→測定→事前登録)・平均と分布の両方・**カルテはゲートにしない**・計器の空検査 | 設計済・未実装 | 同上 | v1 の「内省空バグ」への対策(O16)を含む |
| micro-observation | O17-O20 公開は既定非公開・粒度でなく体数を落とす・実在事業者名は伏せる | 設計済・未実装 | 同上(O19 は**未リサーチ=expedient の自前判断**と明記) | |

### 2-41 data-contract-research(ソフトウェア工学 #29・P2)— 部分 4 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| data-contract | 案(b) 新スキーマ(連続時刻)+ Chronicle/較正向けエクスポータ | 部分 | `docs/design/v2-redesign.md:389`(U3/D6 DECIDED)・`src/shibuya/engine/tape.py` | 新スキーマは実装。**エクスポータは無い**(v1 資産を救う層が未着手) |
| data-contract | コア列 `(run_id, t_ns, seq, kind, schema_ver, agent_id, x, y, payload)`・`(t_ns, seq)` 全順序主キー | 部分 | `src/shibuya/core/types.py:10`(`t_sim_ns` = tick×span + offset_ns)・`tape.py`(独自 10+3 列) | ナノ秒整数時刻は採用。**`seq` を含む複合主キーは無い** |
| data-contract | 3ストリーム分離(events / llm_calls(OTel GenAI 準拠)/ checkpoints) | 部分 | `src/shibuya/engine/tape.py`(llm_calls 相当)・checkpoint | **events ストリームは診断行に縮退**。3 分離の形にはなっていない |
| data-contract | 進化戦術 = versioned events + 読み側 upcaster・既存ファイルは書き換えない | 部分 | `src/shibuya/engine/tape.py:337,365`(版1 テープの後方互換読み) | upcaster と同型の実装だが語彙も汎用機構も無い |
| data-contract | LLM 記録は **OTel GenAI semconv** 準拠 + `sim.t_ns`/`sim.run_id`/`sim.agent_id` | 未判定 | — | `gen_ai` `OTel` grep 0。**取りこぼし候補(外部相互運用性)** |

### 2-42 capabilities-business-research(分野外(事業・資金) #0・P2)— 実装済 1 / 設計済 1 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| capabilities-business | v2 は「個票を当てる」市場でなく**相互作用の帰結・介入の相対比較**の市場に立つ | 実装済 | `docs/design/v2-redesign.md:466`(到達点の順位=C 一位・その過程で A と B) | 09-17 のユーザー決定と一致 |
| capabilities-business | L-OBS/L-REC の検証能力=最も空白・v2 固有の獲得能力 | 設計済・未実装 | `docs/design/v2-redesign.md:395`(U4) | 2-20 と同じ |
| capabilities-business | 4市場(都市 what-if / 合成調査 / 情報伝播 / 群衆安全)の実在アンカー | 未判定 | — | 設計書に市場の表が無い(MEMORY の市場地図は答申外) |
| capabilities-business | 事業形態6候補(イベント主催者・自治体・鉄道 → 規制当局 → 広告主 → 保険) | 未判定 | — | `docs/funding/` は未踏1本のみ |

### 2-43 impact-risk-research(研究倫理・情報法 #31・P2)— 実装済 2 / 設計済 1 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| impact-risk | Epstein「Why Model?」の16の非予測的目的に価値主張を置く(予測精度に置かない) | 実装済 | `docs/design/v2-methodology.md`・`docs/design/v2_significance.md` | 「歪む場所の宣言」の思想的土台 |
| impact-risk | 最も現実的な負の影響は悪用でなく**「良性の過信」**(k* 等が留保なしに政策語彙へ移る) | 実装済 | `tools/c8/dashboard.py`(面2「通っても合格とは言わない」の片側性を見出しに明記) | 計器盤の文言に直接入っている |
| impact-risk | 緩和5点セット(生ログ非公開+集計出力のみ / C2PA 来歴署名 / ODD・TRACE 準拠+段階公開 / DURC 型) | 設計済・未実装 | `docs/design/v2-ethics-safety-operations.md:17` | |
| impact-risk | 「v1 の誤情報×57 は拡散量であって態度変容ではない」という留保を常に付す | 未判定 | — | 該当の留保文が設計書に無い |

### 2-44 learned-simulation-research(自然言語処理・機械学習 #27・P2)— 実装済 1 / 部分 2 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| learned-simulation | v2 は手書きと完全学習の中間でなく **PIML/UDE と同じ座標**(層1=hard constraint / 層2=事前学習分布 / 層3=オンライン規則帰納) | 未判定 | — | `PIML` `UDE` `物理情報` は設計書に無い。**位置づけの語彙が採られていない**=取りこぼし候補 |
| learned-simulation | 第二世代化の防波堤 = **層1 の規則数を予算として明示監視** | 部分 | `docs/design/v2-budget-declaration.md`(22項の予算)・`src/shibuya/world/processes/first_batch.py`(21 過程の登録) | 過程数は登録制。**規則数そのものの予算行は無い** |
| learned-simulation | 判例に検証ゲート(Voyager 型・誤判例の固着が最大リスク) | 部分 | `tools/vocab/adjudicate.py`(段3 静的検査 s1〜s6) | 語彙側に検証ゲートが入った。判例側は未 |
| learned-simulation | ニューラル代理は本番置換でなく感度分析・パラメータ探索限定 | 実装済 | `docs/design/v2-redesign.md:378`(物理コア=明示エンジン)・IMPLEMENTED 全体 | 学習代理を一切入れていない |

### 2-45 world-model-relation-research(計算社会科学 #25・P2)— 実装済 1 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| world-model-relation | 自己呼称は **large-scale generative agent-based social simulation**(”world model” を名乗らない) | 未判定 | — | `generative agent-based` は設計書に grep 0。`v2_significance.md:200` は世界モデル言説に言及するだけ |
| world-model-relation | 関係を述べる推奨定式(3行)を意義文書に置く | 未判定 | — | 該当文が無い |
| world-model-relation | 生成世界モデルを環境エンジンに据えない(保存則・台帳の検証可能性を失う) | 実装済 | `docs/design/v2-redesign.md:378`・`src/shibuya/world/` 全体(明示エンジン) | 方針として完全に守られている |

### 2-46 content-safety-deep-research(研究倫理・情報法 #31・P2)— 設計済 4

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| content-safety | 3層方針(生成は許す / 記録は全量・不変・機械ラベル / 公開は4段ティア) | 設計済・未実装 | `docs/design/v2-ethics-safety-operations.md`(E-2/E-3)・`v2-redesign.md:459` | 記録の全量保存だけは実装(テープ)。ラベル付けは未 |
| content-safety | 日本語有害検出は **Qwen3Guard** 主 + LLM-jp Toxicity 8フラグ | 設計済・未実装 | `docs/design/v2-ethics-safety-operations.md` | `src/` に grep 0 |
| content-safety | 実在人物名の多層防止(合成名リスト / NER / **同定可能性ベースの管理**=石に泳ぐ魚基準) | 設計済・未実装 | 同上 | 母集団は合成(`src/shibuya/build/pop/`)なので入口は満たすが、生成文の検査は無い |
| content-safety | **censored/uncensored 両方の ablation**(安全整合が負の現象の再現を歪める) | 設計済・未実装 | `docs/design/v2-redesign.md:459`(E-2) | `tools/c8/ablations_v1.json` に腕が無い |

### 2-47 funding-deep-research(分野外(事業・資金) #0・P2)— 実装済 1 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| funding | 最優先=未踏アドバンスト 2026 年度下期(9/24 締切・法人格不要・委託費は人件費相当のみ) | 実装済 | `docs/funding/mitou-advanced-research.md`・PENDING「9月締切2件」 | 運用に入っている |
| funding | GPU 実勢価格表(同じ実験が 3.6万〜153万円=42倍)・調達先選定が最大レバー | 未判定 | — | 設計書・予算宣言表に金額の行が無い(予算は時間とバイトのみ) |
| funding | 法人化 or 大学客員研究員が ABCI/NEDO/JST/財団を同時に解錠する共通鍵 | 未判定 | — | 台帳に項目が無い |

### 2-48 longrun-ops-deep-research(ソフトウェア工学 #29・P2)— 部分 3 / 未判定 1

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| longrun-ops | 単一長寿プロセス廃止 → **連鎖再投入(7日×N本)** + 2段 CKPT(最大損失1時間) | 部分 | `tools/c8/ensemble.py`(G-6 完了済みラン表・未完了 index の再投入)・checkpoint 6時間毎(予算 S2) | 再投入の**器**はある。7日×N本の連鎖と2段 CKPT は無い |
| longrun-ops | **bit-for-bit exact restart を CI ゲート化**(Factorio 型 desync の主犯=非永続キャッシュの再計算食い違い) | 部分 | IMPLEMENTED #10(T1/T2 同 seed 同ハッシュ) | checkpoint 一致はある。**resume 後のキャッシュ再構築検査は無い**(v1 第98/142 と同型の穴が残る) |
| longrun-ops | 観測 I/O 契約6条(リング append のみ / 背圧の既定=**ドロップ+カウンタ** / size-or-time フラッシュ / アトミック rename) | 部分 | IMPLEMENTED #22(テープ繰り延べ 14,798=0.547% を件数と率で記録) | 「欠損を必ず数える」は実装。他の5条は未 |
| longrun-ops | 3層ストレージ(ホット14日 / B2 / Zenodo)・**LLM 全文は 1-5% 層化サンプルのみ恒久化** | 未判定 | — | 全文を全量保存する方針(4条件の1つ)と**正面から衝突する提案**。衝突の記録が無い |

### 2-49 publication-ethics-deep-research(研究倫理・情報法 #31・P2)— 設計済 1 / 未判定 2

| 答申 | 項 | 判定 | 根拠(ファイル:行) | 備考 |
|---|---|---|---|---|
| publication-ethics | 人間評価は専門家中心(IRB 不要の整理3条件)+ ethics statement 7点 | 設計済・未実装 | `docs/design/v2-redesign.md:459`(E-6 審査不要3本立て)・`docs/design/v2-ethics-safety-operations.md` | |
| publication-ethics | 投稿ポートフォリオ4方向(EPJ DS / JASSS / NeurIPS E&D / ICWSM)+ arXiv 個人エンドースメント | 未判定 | — | 設計書に投稿計画が無い |
| publication-ethics | 所属問題の共通鍵=ESSA 加入 + 大学との共同研究 | 未判定 | — | 台帳に項目が無い |

---

## §3 取りこぼし候補と「設計済・未実装」の上位 20

### 3-1 取りこぼし候補(未判定)上位 10 — 答申にあり、設計にも実装にも痕跡が無い

| 順 | 項目 | 出所 | なぜ上位か |
|---|---|---|---|
| 1 | **バックプレッシャ3段 / TiDi(艦隊が詰まったらシミュ時計を延ばす)** | llm-serving 面2・ugc #19/#20 | 答申が「**先行ゼロ=v2 の独自設計**」と名指しした貢献候補。艦隊の供給がシミュ速度を規定する運用式の要。現行は `--fleet-wait-s` の待ちだけ |
| 2 | **反実仮想渋谷(架空条件)の常設対照ラン** | llm-knowledge (B) | 「創発 vs 記憶の再生」を分ける**唯一の識別手段**。実名渋谷=較正専用/架空=創発主張専用の用途分離が無いまま主張を立てると Barrie&Törnberg 批判に直撃 |
| 3 | **判例ループの露出逆確率補正(Horvitz-Thompson)** | coupled-adaptation 面2-1 | 答申が「v2 に相当物がなく**新規実装価値最大**」と明示。観測されやすい場所の事案を過剰計上する構造は D-71 語彙成長(被覆順位=体数×セル数×時間帯数)に**既に存在する** |
| 4 | **人流の二次モーメント指標(滞留時間分布・訪問頻度 Zipf・EPR μ・常用地点〜25)の凍結** | llm-mobility §5-1/§5-4 | v2 の中心仮説(ボトルネック #7)を測る指標が**1 本も凍結されていない**。在圏カーブだけでは「二次モーメントは全先行失敗」の賭けを判定できない |
| 5 | **摩擦パラメータ μ(競合関与者全員の移動が拒否される確率)** | parallel-execution 面1 | フロアフィールド CA でアーチ形成の再現に不可欠とされる量。C9a で辺上位置が入った今、**詰まりの再現が次の論点**になる |
| 6 | **`judgment_type` + 再現可能な判定関数への参照(パターン台帳の機械化)** | pattern-ledger ② | 台帳が散文のままだと合否が人手判断になる。1 列足すだけで計器盤 面2 の自動化に直結 |
| 7 | **パターン台帳の「データ漏洩の疑い」欄** | r2-fulltext (c) | 提案は「1 列足すだけ」。公刊済み stylized fact は LLM の訓練データに入っている可能性があり、**封印データが漏洩に強いことを台帳の上で言える**ようになる |
| 8 | **出力スキーマから OSM 生値を排除する検査** | legal-licensing 面1 | ODbL の Derivative Database 判定=**事業化時の最大リスク**。テープ・診断行に OSM 生値が載らないことを機械で確かめる仕組みが無い |
| 9 | **境界通過を一級イベント化(`boundary_cross` 9欄)+ コードン ±10% 照合** | boundary-deep 面3(d) | 開放系の境界を定量化する唯一の口。`presence.py` の ARRIVE/DEPART は機能的に近いが**照合の物差しが無い** |
| 10 | **「介入せず観察」と「公開時フィルタ」の分離の検査(介入回数=0 を毎ラン検証)** | ethics-operations ③ | 設計書が宣言しているのに検査が無い=**自己申告のまま**。CLAUDE.md の「設計者の指紋の最小化」と直結 |

次点: 制度の足場なし ablation A0-A4(institutions)・observation-projection の obs_public/obs_link 二層分離・TRAILS 被覆表(r2-fulltext (d))・OTel GenAI semconv(data-contract)・blockface(cell-granularity)・歩行者の「最短でない」選好(mobility-field)・3/N 則(small-scale-verification)。

### 3-2 設計済・未実装 上位 10 — DECIDED か設計書にあるが `src/` に無い

| 順 | 項目 | 決定の所在 | 備考 |
|---|---|---|---|
| 1 | **記憶と想起(U1 ハイブリッド・8-16 ベクタ/体・夜間 T2 監査)** | `v2-redesign.md:392` | `agents/state.py:8` が「M4 は C3 以降」と書いたまま C9。分野 #12 が 0% の主因 |
| 2 | **T0 習慣表とペルソナ seed(U2)** | `v2-redesign.md:393` | 同上。習慣が無いので「予測誤差→結晶化」も立たない |
| 3 | **予測誤差ゲート付き認知ループ(R5/U19)** | `v2-redesign.md:446` | δ_think レーンは決まっているが誤差の測定が無い |
| 4 | **関係辺と再訪同一性の5つ組** | `v2-c10-relations-agenda.md`・boundary-deep(c) | C10 R9′(会話から関係を抽出)で 09-17 に方針決定。familiar stranger 4.0 人が成立しない |
| 5 | **認知 LOD の on-demand 昇格(U6)** | `v2-redesign.md:397` | 40 万体の LLM 予算配分則そのもの。現状は起床条件+繰り延べで代替 |
| 6 | **L-OBS / L-REC 観測射影(U4・7チャネル・R0-R6)** | `v2-redesign.md:395` | Phase 4 以降と決まっているので予定どおり。ただし capabilities-business が「v2 固有の獲得能力」と位置づけた項 |
| 7 | **ミクロ観察 M1(個体カルテ・場所カルテ・逸話3段)** | PENDING D-80 | 場所カルテは全数 24MB/日 で**追加ラン 0 本**で作れる算術が出ている=着手コストが最も低い |
| 8 | **倫理・安全運用 E-1〜E-7 の実装(検出器・伏字・注記3箇所)** | `v2-redesign.md:459` | 設計書は完成。公開段の実装がゼロなので、**いま公開すると設計と実態が食い違う** |
| 9 | **コンテンツ安全の3層(Qwen3Guard・8フラグ・censored/uncensored ablation)** | `v2-redesign.md:459`(E-2) | ablation の腕を 1 本足すだけで科学的主張の幅が変わる |
| 10 | **可視化 R15(計器盤 Web UI + deck.gl 2D + 介入 provenance)** | `v2-redesign.md:458` | 計器盤は `tools/c8/dashboard.py` が Markdown で代替。地図と介入記録は未 |

次点: 制度の 5 プリミティブと行13 立法(`v2-architecture-roadmap.md:44`)・Mapillary 取得計画(vlm-reality-check)・attrition 表(pattern-ledger ⑦)・タグ付きイベント索引と checkpoint 時間スライス(`v2-redesign.md:394` U3)・記憶転写の重み(`v2-action-contract.md:54`)。

---

## §4 監査の限界

1. **「実装済」は動作の証明ではない**。本監査が見たのは**ファイル:行の実在**と IMPLEMENTED に記録された実測値であり、親の pytest を回し直してはいない。別サブの完了報告を信用しない規律(CLAUDE.md §5)は本書にも当てはまる——**親は §3 の判定と、§2 で「実装済」とした行のうち標本を自分で確認すること**。
2. **「未判定」は不在の証明ではない**。特徴値 grep は**答申の語をそのまま探す**方法なので、同じ機能が別の語で実装されていれば見落とす。実際に本監査中、`RSD`/`aging`(parallel-execution)は語としては 0 件だが `pk` の辞書式と `T_MAX` 昇格が機能的に対応していた。§3-1 の 10 件は**再検査で判定が動きうる**。
3. **項の切り出しは監査者の判断**。同じ答申を 4 項に割るか 8 項に割るかで割合が変わる。§1 の百分率は**答申の粒度に依存する量**であり、分野間の比較は「傾向」までしか言えない。
4. **分野の重複計上**。1-3 の分野別は延べで数えているため合計は 243 を超える。1 本の答申が複数分野に属するとき、その答申の判定がそのまま複数分野に効く(例: llm-serving が #27 と #28 の両方を押し上げる)。
5. **設計書の行番号は HEAD(第213)時点**。`v2-redesign.md` §9 は第210 で 10 ファイル訂正が入っており、batch2 が引いた行番号(`:439` など)は既にずれている。本書は自分で取り直した番号を使ったが、次の改版で再びずれる。
6. **P0 35 本(別サブ A 担当)との重なりを調整していない**。同じ決定に複数の答申が寄与している場合(例: 群衆物理は crowd-physics-research=P0 と mobility-field=P1 の両方)、本書は P1/P2 側の寄与だけを見ている。**合算時に二重計上の確認が要る**。
7. **`docs/bench/` と `docs/ops/` の実測記録を全部は読んでいない**。受入報告(build-report-C0〜C6)と IMPLEMENTED の要約に依拠した箇所がある。とくに 2-28(SCJ 214 件の一致率)と 2-33(看板の標本分割)は「記録が見当たらない」であって「やっていない」ではない。
