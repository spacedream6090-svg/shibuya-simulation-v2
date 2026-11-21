# docs の入口(索引)

> 2026-11-09・文書役(Opus 5.5)が作りました。発注は [返事その 6](design/prompt-2026-11-05-reply6.md) §3-2 の 4(`11-05/§3-2`)と [返事その 7](design/prompt-2026-11-09-reply7.md) §2 の 5(`11-09/§2`)です。
>
> 文書の名前と冒頭の数行だけを読んで書きました。中身が正しいかは確かめていません。数は、HEAD `14b151a` で git が追跡しているファイルの本数です(docs/ の下は全部で 2,287 本。本書と同じ日に作った棚卸しの表は数に入れていません)。
>
> **決定の正は原文(指示書・回答)です。** 決定の ID は [決定の ID の索引](design/decision-id-index.md) で引きます。この索引は `python tools/decision_index.py` が作るもので、手で編集しません。
>
> **「旧」の印**は、後の文書に置き換えられたと分かるものにだけ付けました。置き換えた文書と根拠を、その行と §10 に書いています。分からないものには付けていません。古い文書は 1 本も消していません。

## どこから読むか

1. **今どの段か・次の 1 手**: リポの根の [STATUS.md](../STATUS.md)。判断待ちは [PENDING.md](../PENDING.md) にあります。
2. **決定**: いちばん新しい [返事その 7](design/prompt-2026-11-09-reply7.md) を読み、出てきた ID を[決定の ID の索引](design/decision-id-index.md)で引いて原文へ進みます。理由は[壁打ちの記録](reference/wallbounce-record-2026-11-02_05.md)にあります。
3. **今のコードが何をしているか**: [リポの案内](reference/repo-guide/README.md) → [1 日の流れ](reference/repo-guide/day-flow.md) → [言えること・言えないこと](reference/repo-guide/can-say.md)。
4. **あるべき姿**: [仕様書 v0](design/spec/README.md) → 各章の冒頭の要約 → [差の一覧](design/spec/gaps.md) → [食い違いの一覧](design/spec/conflicts.md)。
5. **答申**: [答申の索引](research/INDEX.md)。

## 区分ごとの数

| 区分 | 置き場 | 本数 | まず読む |
|---|---|---:|---|
| 決定 | `design/` の原文と決定の周りの 30 本・`reference/` の壁打ちの記録 1 本 | 31 | [決定の ID の索引](design/decision-id-index.md) |
| 答申 | `research/` | 399 | [INDEX.md](research/INDEX.md) |
| 設計 | `design/`(決定の 30 本を除く 87 本)・`design/spec/` 14 本 | 101 | [仕様書 v0](design/spec/README.md) |
| 計測の記録 | `bench/` | 1,564 | [bench/README.md](bench/README.md) |
| 参照 | `reference/` 18 本・`reference/repo-guide/` 129 本・`reference/v1/` 8 本 | 155 | [リポの案内](reference/repo-guide/README.md) |
| 運用 | `ops/` | 24 | [版上げの履歴](ops/version-history.md) |
| 記録 | `log/` | 4 | [devlog.md](log/devlog.md) |
| その他 | `funding/` 1・`plateau2026/` 1・`reviews/` 6・直下の 2 本 | 10 | — |

壁打ちの記録は `reference/` に置いてあるので、参照の 155 本にも入っています。

## 1. 決定(指示書・回答・壁打ちの記録)

指示書と回答は、ユーザーが渡した原文をそのまま保存したものです。各回は前の回の後に読みます。ほかの文書には中身を写さず、`10-12/CA1` の形の ID で引きます(`10-13b/§1` の 1-7 案 B)。

| 接頭 | 原文 | 一言 |
|---|---|---|
| `09-24d` | [v2-decisions-for-user-2026-09-24.md](design/v2-decisions-for-user-2026-09-24.md) | 判断待ちへの決定 09-24 |
| `09-25` | [v2-wallbounce-decisions-2026-09-25.md](design/v2-wallbounce-decisions-2026-09-25.md) | 壁打ちの決定 09-25 |
| `09-29d` | [v2-decisions-for-user-2026-09-29.md](design/v2-decisions-for-user-2026-09-29.md) | 判断待ちへの決定 09-29 |
| `09-30` | [v2-wallbounce-decisions-2026-09-30.md](design/v2-wallbounce-decisions-2026-09-30.md) | 壁打ちの決定 09-30 |
| `10-03` | [v2-wallbounce-decisions-2026-10-03.md](design/v2-wallbounce-decisions-2026-10-03.md) | 指示書 10-03 |
| `10-06` | [v2-wallbounce-decisions-2026-10-06.md](design/v2-wallbounce-decisions-2026-10-06.md) | 指示書 10-06 |
| `10-12` | [v2-wallbounce-decisions-2026-10-12.md](design/v2-wallbounce-decisions-2026-10-12.md) | 指示書 10-12 |
| `10-12p` | [v2-plan-answers-2026-10-12.md](design/v2-plan-answers-2026-10-12.md) | 実装の計画への回答 10-12 |
| `10-12b` | [v2-answers-2026-10-12b.md](design/v2-answers-2026-10-12b.md) | 回答 10-12b(第 329 への回答) |
| `10-13` | [v2-answers-2026-10-13.md](design/v2-answers-2026-10-13.md) | 回答 10-13(第 330 への答え) |
| `10-13b` | [v2-answers-2026-10-13b.md](design/v2-answers-2026-10-13b.md) | 回答 10-13b(自律運転の規則) |
| `10-25` | [v2-answers-2026-10-25.md](design/v2-answers-2026-10-25.md) | 回答 10-25(壁打ち 10-23〜25 の決定・研究の題) |
| `11-01` | [v2-answers-2026-11-01.md](design/v2-answers-2026-11-01.md) | 回答 11-01(A1=知見の切り分けの原則・判断の置き場・検証の規模) |
| `11-01p` | [prompt-2026-11-01.md](design/prompt-2026-11-01.md) | 指示書 11-01(実装の限定の再開) |
| `11-01g` | [prompt-2026-11-01-5070.md](design/prompt-2026-11-01-5070.md) | 指示書 11-01 5070(検証の準備) |
| `11-02` | [prompt-2026-11-02-research.md](design/prompt-2026-11-02-research.md) | 返事その 1(研究と取得) |
| `11-02r` | [prompt-2026-11-02-reply2.md](design/prompt-2026-11-02-reply2.md) | 返事その 2(段 4 の差し替え=v3 事象駆動の核・A2) |
| `11-03` | [prompt-2026-11-03-reply3.md](design/prompt-2026-11-03-reply3.md) | 返事その 3(挙動の棚卸しの仕分け・欠陥の修正・v3 の仮決定) |
| `11-04` | [prompt-2026-11-04-reply4.md](design/prompt-2026-11-04-reply4.md) | 返事その 4 |
| `11-04b` | [prompt-2026-11-04-reply4b.md](design/prompt-2026-11-04-reply4b.md) | 返事その 4 の追補 |
| `11-04c` | [prompt-2026-11-04-reply5.md](design/prompt-2026-11-04-reply5.md) | 返事その 5 |
| `11-05` | [prompt-2026-11-05-reply6.md](design/prompt-2026-11-05-reply6.md) | 返事その 6(整理の段・仕様書 v0・包みの案) |
| `11-09` | [prompt-2026-11-09-reply7.md](design/prompt-2026-11-09-reply7.md) | 返事その 7(第一目標と背骨の文・食い違いの決着・コードの区分) |

決定の周りの文書は次のとおりです。

| 文書 | 一言 |
|---|---|
| [decision-id-index.md](design/decision-id-index.md) | 決定の ID の索引(自動生成・手で編集しない) |
| [v2-redesign.md](design/v2-redesign.md) | 決定台帳(議題ごとの OPEN と DECIDED。創立の 2026-08-28 から書き足している) |
| [v2-requirements.md](design/v2-requirements.md) | 要件定義(2026-08-30 確定版) |
| [v2-requirements-revision-log.md](design/v2-requirements-revision-log.md) | 要件の改訂記録(要件書の本文から変わった要件の経緯と旧文) |
| [v2-research-request-2026-10-06.md](design/v2-research-request-2026-10-06.md) | リサーチの指示書(10-12 に改訂した版を同じ道筋へ上書きした) |
| [v2-wallbounce-0930-reflection.md](design/v2-wallbounce-0930-reflection.md) | 指示書 09-30 の反映の記録(親) |
| [v2-wallbounce-notes-2026-10-07-12.md](design/v2-wallbounce-notes-2026-10-07-12.md) | **旧**(置き換え: [指示書 10-12](design/v2-wallbounce-decisions-2026-10-12.md))。壁打ちの決定の控え |
| [wallbounce-record-2026-11-02_05.md](reference/wallbounce-record-2026-11-02_05.md) | 壁打ちの記録(理由・採らなかった案・ユーザーの意図)。ファイル名は 11-02_05 のままで、中身は 11-09 まで足した版 |

## 2. 答申(`research/`・399 本)

**読み方**: [INDEX.md](research/INDEX.md) の §3 の表で答申を探し、答申の末尾にある親の一次確認の表を見ます。INDEX の等級 D(出典の URL が無い・2026-09-02 より前)の 33 本は、一次確認が丸ごと残っています(INDEX §1)。

| 置き場 | 本数 | 中身 |
|---|---:|---|
| [INDEX.md](research/INDEX.md) | 1 | 答申の索引(一次確認の等級 A〜E・分野別・全答申の表)。行は手で足す |
| [RESEARCH-STATE.md](research/RESEARCH-STATE.md) | 1 | リサーチの進み具合(最終更新 2026-09-17) |
| [research-backlog.md](research/research-backlog.md) | 1 | リサーチの残務台帳(2026-09-14〜) |
| [research-order-template.md](research/research-order-template.md) | 1 | 研究役への発注文の定型(「断られたら取りに行かない」の 1 行を含む) |
| [research-title-aliases.md](research/research-title-aliases.md) | 1 | 研究の題の読み替え(文字 → 番号) |
| [v2-discipline-map.md](research/v2-discipline-map.md) | 1 | 分野地図(32 分野) |
| [v1-asset-triage.md](research/v1-asset-triage.md) | 1 | v1 の資産の仕分け |
| `v2-r<番号>-*.md` | 114 | 番号つきの答申(R-148 まで)。`v2-r118-*.json` 2 本は R-118 の付属 |
| `v2-*.md`(番号なし) | 93 | 番号の無い名前の答申とメモ(創立時のディープリサーチの答申を含む) |
| [lit/](research/lit/README.md) | 120 | 文献のメモ(1 論文 1 メモ・`_TEMPLATE.md` が定型) |
| `scripts/` | 43 | 答申の数を出したスクリプト |
| `r58/`・`r59/`・`r60/`・`r129-leak-items/` | 20 | 答申の添付 |

## 3. 設計(`design/`・`design/spec/`)

### 3-1 仕様書 v0(`design/spec/`・14 本)

あるべき姿を 1 か所にまとめた写しです(`11-05/§3-1b`)。決定の正は原文で、すべて仮決定です。今のコードの記述は §5 のリポの案内にあり、仕様書には混ぜていません。

- [README.md](design/spec/README.md): 索引。ユーザーが読む所は、各章の冒頭の要約・差の一覧の要約・食い違いの一覧です。
- 章 11 本: [00 設計の原則](design/spec/00-principles.md)・[01 時間と実行](design/spec/01-time-and-execution.md)・[02 世界](design/spec/02-world.md)・[03 心](design/spec/03-mind.md)・[04 差分の器](design/spec/04-act.md)・[05 経済](design/spec/05-economy.md)・[06 社会](design/spec/06-society.md)・[07 検証](design/spec/07-validation.md)・[08 実験](design/spec/08-experiments.md)・[09 構築](design/spec/09-build.md)・[10 外への口](design/spec/10-interfaces.md)。
- [gaps.md](design/spec/gaps.md): 仕様と今のコードの差の一覧。
- [conflicts.md](design/spec/conflicts.md): 直しの文が見つからなかった食い違いの一覧(片方を選んでいない)。

### 3-2 v3 と今の計画

| 文書 | 一言 |
|---|---|
| [v3-core-design-2026-11-03.md](design/v3-core-design-2026-11-03.md) | v3 事象駆動の核の設計書(壁打ちの答えの ID と要点だけを写す) |
| [v2-implementation-plan-2026-10-12.md](design/v2-implementation-plan-2026-10-12.md) | 実装の計画(第 1 期〜第 7 期・版上げの束ね方・ユーザー承認) |
| [v2-e-series-plan-2026-11-01.md](design/v2-e-series-plan-2026-11-01.md) | E 系列(5070 とクラウドの実験)の組み直し |
| [v2-g1-backtest-plan-2026-11-02.md](design/v2-g1-backtest-plan-2026-11-02.md) | 門 1 の計画(名前だけ載せる。読む役は開かない=§11) |
| [v2-prep-6-1-notes-2026-10-25.md](design/v2-prep-6-1-notes-2026-10-25.md) | 回答 10-25 §6-1 の設計メモと差分の見積り |
| [v2-odpt-work-materials-2026-10-14.md](design/v2-odpt-work-materials-2026-10-14.md) | ODPT の作品の壁打ちに要る材料 |
| [v2-prompt-compute-reduction-experiment-plan.md](design/v2-prompt-compute-reduction-experiment-plan.md) | プロンプトで計算量を減らす実験の計画(v0) |
| [v2-schedule-and-research-plan-2026-09.md](design/v2-schedule-and-research-plan-2026-09.md) | 構築の日程(S0〜S5)と未リサーチの分野の地図(草案・未承認) |
| [v2-bench-plan.md](design/v2-bench-plan.md) | vLLM 艦隊のベンチの計画(2026-09-01・DRAFT) |

### 3-3 創立時の正典と全体図

| 文書 | 一言 |
|---|---|
| [v2-methodology.md](design/v2-methodology.md) | 開発方法論(Phase 0〜5。今の運用は CLAUDE.md §4 の改訂のとおり) |
| [v2_draft_proposal.md](design/v2_draft_proposal.md) | 草案の提案書(2026-08-31・レビュー待ちのドラフト) |
| [v2_significance.md](design/v2_significance.md) | v2 の意義(2026-08-31・ドラフト) |
| [v2_design_slides.html](design/v2_design_slides.html) | 統合設計図のスライド |
| [v2-architecture-roadmap.md](design/v2-architecture-roadmap.md) | 統合設計図とロードマップ(2026-09-02 の草案。決定台帳に写すまで設計を縛らない) |
| [v2-architecture-overview-simple.md](design/v2-architecture-overview-simple.md) | アーキテクチャの概要(簡略版) |
| [v2-architecture-overview-detailed.md](design/v2-architecture-overview-detailed.md) | アーキテクチャの概要(詳細版・開発者向け) |
| [v2-decision-agenda.md](design/v2-decision-agenda.md) | 決定アジェンダ(2026-08-30・大枠の確定用) |

### 3-4 契約書と設計書(9 月に仮決定した v1。後の改訂は各文書に印がある)

| 文書 | 一言 |
|---|---|
| [v2-perception-contract.md](design/v2-perception-contract.md) | 知覚契約書(世界 → 心) |
| [v2-action-contract.md](design/v2-action-contract.md) | 行動契約書(心 → 世界) |
| [v2-cognition-design.md](design/v2-cognition-design.md) | 認知設計書 |
| [v2-world-process-design.md](design/v2-world-process-design.md) | 世界過程の設計とエンジンと LLM の線引き |
| [v2-boundary-economy-design.md](design/v2-boundary-economy-design.md) | 境界と経済の設計書 |
| [v2-crowd-physics.md](design/v2-crowd-physics.md) | 群衆物理の設計書 |
| [v2-dashboard-verification-orchestration.md](design/v2-dashboard-verification-orchestration.md) | 忠実度の計器盤・検収・実験の進め方 |
| [v2-ethics-safety-operations.md](design/v2-ethics-safety-operations.md) | 倫理とコンテンツの安全の運用 |
| [v2-run-manifest-concurrency.md](design/v2-run-manifest-concurrency.md) | 運用設計書(run manifest・並行実行) |
| [v2-implementation-plan.md](design/v2-implementation-plan.md) | 実装計画書 v1(言語・部品・層の契約・試験と CI) |
| [v2-world-data-build-spec.md](design/v2-world-data-build-spec.md) | 世界データの構築仕様(W0〜W20) |
| [v2-world-catalog.md](design/v2-world-catalog.md) | 世界カタログ v0.2(凍結した版・57 クラス) |
| [v2-budget-declaration.md](design/v2-budget-declaration.md) | 予算宣言表 |
| [v2-foundation-contracts-2026-10-13.md](design/v2-foundation-contracts-2026-10-13.md) | 土台 8 つの口の約束と受入の試験(第 1 期) |

### 3-5 設計ラウンドの草案

問いの一覧の草案(2026-10-03〜10-06)。答えは指示書 10-12 §4 で出ていて、各草案の問いの末尾に書き足してあります。

| 文書 | 答えの場所 |
|---|---|
| [v2-calendar-timing-design-round-draft.md](design/v2-calendar-timing-design-round-draft.md)(カレンダーと行動の時刻) | `10-12/§4-1` |
| [v2-time-model-design-round-draft.md](design/v2-time-model-design-round-draft.md)(時間のモデル) | `10-12/§4-2` |
| [v2-viewer-design-round-draft.md](design/v2-viewer-design-round-draft.md)(ビューア) | `10-12/§4-3` |
| [v2-communication-tools-design-round-draft.md](design/v2-communication-tools-design-round-draft.md)(人と人の道具) | `10-12/§4-4` |
| [v2-counterfactual-primitives-design-round-draft.md](design/v2-counterfactual-primitives-design-round-draft.md)(部品と検査・反実仮想の入口) | `10-12/§4-5` |
| [v2-memory-rework-design-round-draft.md](design/v2-memory-rework-design-round-draft.md)(記憶の作り直し) | `10-12/§4-6` |
| [v2-decision-model-design-round-draft.md](design/v2-decision-model-design-round-draft.md)(判断モデル) | `10-12/§4-7` |
| [v2-spatial-design-round-draft.md](design/v2-spatial-design-round-draft.md)(空間) | 指示書 10-06 §2・10-12 で追記 |

そのほかの草案と仕様。

| 文書 | 一言 |
|---|---|
| [v2-action-activity-two-layer-draft.md](design/v2-action-activity-two-layer-draft.md) | 行為と活動の二層(2026-09-27) |
| [v2-hunger-choice-attention-draft.md](design/v2-hunger-choice-attention-draft.md) | 空腹のエネルギー収支・古典的選択モデル・活動と知覚 |
| [v2-memory-wom-internet-draft.md](design/v2-memory-wom-internet-draft.md) | 記憶と口コミの店選び・シミュレーションの中のインターネット |
| [v2-spatial-physics-layer-draft.md](design/v2-spatial-physics-layer-draft.md) | 物理エンジンの粒度の空間層 |
| [v2-plan-executor-design.md](design/v2-plan-executor-design.md) | 計画実行層(2026-09-10) |
| [v2-d68-pilot-design.md](design/v2-d68-pilot-design.md) | D-68 下見(2,000 体・5 腕) |
| [v2-resume-determinism-draft.md](design/v2-resume-determinism-draft.md) | 再開の口と決定論の方針 |
| [v2-run-day-decomposition-draft.md](design/v2-run-day-decomposition-draft.md) | run_day の分解の口(実装済み) |
| [v2-vocab-growth-design.md](design/v2-vocab-growth-design.md) | 回して得た観測から行動語彙を育てる |
| [v2-synonym-policy-v0.md](design/v2-synonym-policy-v0.md) | 辞書 `SYNONYMS` の写像ごとの意味の損失の宣言 |
| [v2-open-intent-arm-spec.md](design/v2-open-intent-arm-spec.md) | 自由意図の腕の仕様 |
| [v2-persona-population-rebuild-design.md](design/v2-persona-population-rebuild-design.md) | ペルソナと人口の作り直し(草案 v0・2026-10-12) |
| [v2-a2-rights-flags-2026-11-02.md](design/v2-a2-rights-flags-2026-11-02.md) | A2 の旗 3 欄と OSM からの初期化 |
| [v2-hobby-affordance-map.md](design/v2-hobby-affordance-map.md) | 趣味の種目と渋谷の舞台の対応表 |

### 3-6 実装アジェンダ(実装の前に細部を決めた文書)

| 文書 | 一言 |
|---|---|
| [v2-c9-geometry-brief.md](design/v2-c9-geometry-brief.md)・[v2-c9-geometry-agenda.md](design/v2-c9-geometry-agenda.md) | C9 位置幾何の材料と決定アジェンダ |
| [v2-c10-relations-brief.md](design/v2-c10-relations-brief.md)・[v2-c10-relations-agenda.md](design/v2-c10-relations-agenda.md)・[v2-c10-relations-implementation-agenda.md](design/v2-c10-relations-implementation-agenda.md) | C10 関係と約束の材料・決定アジェンダ・実装アジェンダ |
| [v2-memory-brief.md](design/v2-memory-brief.md)・[v2-memory-agenda.md](design/v2-memory-agenda.md)・[v2-memory-stage1-implementation-agenda.md](design/v2-memory-stage1-implementation-agenda.md) | 記憶の材料・実装アジェンダ・第 1 段 |
| [v2-store-memory-implementation-agenda.md](design/v2-store-memory-implementation-agenda.md) | 記憶と口コミの店選び |
| [v2-familiarity-counters-implementation-agenda.md](design/v2-familiarity-counters-implementation-agenda.md) | 訪問の数と露出の数・潜在的な親しみ |
| [v2-energy-classical-implementation-agenda.md](design/v2-energy-classical-implementation-agenda.md) | 空腹のエネルギー収支・古典的選択モデル |
| [v2-intent-chooser-implementation-agenda.md](design/v2-intent-chooser-implementation-agenda.md) | 意図の保持・行き先・購入先の選び方 |
| [v2-presence-shape-implementation-agenda.md](design/v2-presence-shape-implementation-agenda.md) | 在圏の形(退出を歩かせる) |
| [v2-proximity-distance-implementation-agenda.md](design/v2-proximity-distance-implementation-agenda.md) | 会話と近接を実距離で判定する |
| [v2-two-layer-implementation-agenda.md](design/v2-two-layer-implementation-agenda.md) | 行為と活動の二層の実装 |
| [v2-w6-regen-implementation-agenda.md](design/v2-w6-regen-implementation-agenda.md) | Overpass の再取得と W6 の作り直し |
| [v2-wage-connection-agenda.md](design/v2-wage-connection-agenda.md) | 賃金をつなぐ |
| [v2-d66-outside-residents-agenda.md](design/v2-d66-outside-residents-agenda.md) | 域外居住(実装は保留) |
| [v2-d102-foundation-implementation-agenda.md](design/v2-d102-foundation-implementation-agenda.md) | D-102 の土台(絶対時刻・状態台帳・乱数・再開) |
| [v2-d102-10a-agenda.md](design/v2-d102-10a-agenda.md)・[v2-d102-10b-agenda.md](design/v2-d102-10b-agenda.md)・[v2-d102-10f-agenda.md](design/v2-d102-10f-agenda.md) | 土台の段 10a・10b・10f |

### 3-7 棚卸し・監査・判断の詳説

| 文書 | 一言 |
|---|---|
| [v2-audit-contradictions.md](design/v2-audit-contradictions.md) | v1 の矛盾の監査(2026-08-28) |
| [v2-inventory-and-bottlenecks.md](design/v2-inventory-and-bottlenecks.md) | 全分野の棚卸しとボトルネックの台帳(2026-09-01) |
| [v2-deep-research-program.md](design/v2-deep-research-program.md) | ディープリサーチの計画(2026-09-01) |
| [v2-decision-evidence-map.md](design/v2-decision-evidence-map.md) | 決定台帳の DECIDED 行と根拠の答申の対応表 |
| [v2-decision-brief-2026-09-19.md](design/v2-decision-brief-2026-09-19.md) | 判断待ち・実装待ちの詳説 |
| [v2-minutes-audit-2026-09-23.md](design/v2-minutes-audit-2026-09-23.md) | 認知と社会のアーキテクチャの議事録の監査 |
| [v2-cell-dependency-inventory.md](design/v2-cell-dependency-inventory.md) | セルに頼っている所の全リスト |
| [v2-v1-gap-record.md](design/v2-v1-gap-record.md) | v1 との差分の記録 |

### 3-8 台帳と表

| 文書 | 一言 |
|---|---|
| [bridging-ledger.json](design/bridging-ledger.json) | つなぎの台帳(1 行=1 つのつなぎ。`engine/bridging/scan.py` の試験がコードと 1 対 1 で突き合わせる) |
| [rules-table.json](design/rules-table.json) | 規則の表 |
| [v2-pattern-ledger.md](design/v2-pattern-ledger.md) | パターン台帳(名前だけ載せる。読む役は開かない=§11) |
| [v2-glossary.md](design/v2-glossary.md) | 用語集(候補の語を含む) |

## 4. 計測の記録(`bench/`・1,564 本)

- [README.md](bench/README.md) と `bench_ledger.csv`: ベンチの台帳です。
- `analysis/`(1,289 本): 版上げと計測ごとの記録です。数・スクリプト・検収の記録が、記録ごとのディレクトリに入っています。byte-check の結果もここにあり、CI の外で回したものです([段 2 の突き合わせ](reference/stage2-crosscheck-2026-11-05.md) §2)。いちばん大きいのは `wallbounce-1012/`(692 本)です。ほかに `wallbounce-1003/`・`wallbounce-1006/`・`v3-2026-11/`・`spatial-2026-10/`・`d44-controls-2026-09-30/` など 38 の記録があります。
- 工程ごとの記録: `c6/` 6 本・`c6_day2/` 2 本・`c7/` 94 本(受入表・holdout の比べ・在席・物差し)・`c8/` 43 本(ablation と感度)・`c9/` 1 本。
- 資産と計器: `w17/` 42 本(日課 W17 の下見と版)・`instruments/` 16 本・`quality_probe_v0/` 13 本・`vocab/` 4 本・`b14_batch_invariance/` 3 本・`engine_spike/` 1 本・`pt_shibuya/` 2 本。
- `figures/` 38 本: 図とその元の数。
- `anchors/` 8 本: 錨の JSON。名前に `validation` が付く 3 本は検証の側なので、開きません(§11)。

## 5. 参照(`reference/`・リポの案内 `reference/repo-guide/`)

### 5-1 リポの案内(今のコードの記述・129 本)

`11-05/§3-1` の把握の資料です。正はコードで、あるべき姿(仕様書)とは混ぜていません。

- [README.md](reference/repo-guide/README.md): 索引。
- [day-flow.md](reference/repo-guide/day-flow.md): 段 1。シミュレーションの 1 日の流れ。
- `catalog/` 3 本: 段 2。機能のカタログ([A 体と街](reference/repo-guide/catalog/a-body-and-town.md)・[B 人の中身](reference/repo-guide/catalog/b-people.md)・[C 基盤](reference/repo-guide/catalog/c-foundation.md))。
- [can-say.md](reference/repo-guide/can-say.md): 今の中身で言えること・言えないこと。
- [cards/](reference/repo-guide/cards/README.md) 122 本: 段 3。src・tests・tools のファイルのカードと、docs と data の索引。`python tools/repo_guide/build.py` が作るもので、手で編集しません。CI の ci-0 がカードの古さを検査します。

### 5-2 そのほかの参照(18 本)

| 文書 | 一言 |
|---|---|
| [behavior-audit-A-perception-decision-2026-11-02.md](reference/behavior-audit-A-perception-decision-2026-11-02.md) | 設計者の指紋の棚卸し A(本人が何を見て、何を選べるか) |
| [behavior-audit-B-resolve-world-2026-11-02.md](reference/behavior-audit-B-resolve-world-2026-11-02.md) | 設計者の指紋の棚卸し B(本人が選んだ後、世界が何をするか) |
| [behavior-audit-triage-2026-11-03.md](reference/behavior-audit-triage-2026-11-03.md) | **旧**(置き換え: [11-04 の仕分け](reference/behavior-audit-triage-2026-11-04.md))。挙動の棚卸し 164 件の仕分け |
| [behavior-audit-triage-2026-11-04.md](reference/behavior-audit-triage-2026-11-04.md) | 挙動の棚卸し 164 件の仕分けのやり直し(ユーザーが親案を採った) |
| [decision-inventory-2026-10-31.md](reference/decision-inventory-2026-10-31.md) | 住民の判断は今だれが決めているか(棚卸し) |
| [decision-routing-2026-11-01.md](reference/decision-routing-2026-11-01.md) | 住民の判断の行き先(112 件の振り分け) |
| [decision-routing-addendum-2026-11-03.md](reference/decision-routing-addendum-2026-11-03.md) | 判断の行き先の追補(112 件の表に無い行) |
| [a1-research-2026-10-31.md](reference/a1-research-2026-10-31.md) | A1 のリサーチ(学問の知見の扱いの切り分けの材料) |
| [tech-map-2026-11-03.md](reference/tech-map-2026-11-03.md) | 現状の技術マップ(`src/shibuya/` の全ファイル) |
| [v3-core-independent-review-2026-11-02.md](reference/v3-core-independent-review-2026-11-02.md) | v3 の核の独立の読み |
| [package-map-claude-code-2026-11-05.md](reference/package-map-claude-code-2026-11-05.md)・[同 -files.md](reference/package-map-claude-code-2026-11-05-files.md) | 包みの分類の案(Claude Code の案 K)と全ファイルの表 |
| [package-map-reconcile-2026-11-05.md](reference/package-map-reconcile-2026-11-05.md) | 案 K と案 F の照らし合わせ |
| [stage2-crosscheck-2026-11-05.md](reference/stage2-crosscheck-2026-11-05.md) | 段 2 の突き合わせ(claude.ai の側の読み手 4 本) |
| [conflicts-triage-2026-11-05.md](reference/conflicts-triage-2026-11-05.md) | 食い違い 52 行の仕分け(claude.ai の側の案) |
| [wallbounce-record-2026-11-02_05.md](reference/wallbounce-record-2026-11-02_05.md) | 壁打ちの記録(§1 にも挙げた) |
| [2026-10-25_engine_llm_parallelization_summary.md](reference/2026-10-25_engine_llm_parallelization_summary.md) | 判断の頻度・並列処理・高速化の議論のまとめ |
| [2026-10-25_shibuya_world_model_and_strategy_summary.md](reference/2026-10-25_shibuya_world_model_and_strategy_summary.md) | 世界モデルの構想・技術のロードマップ・市場の戦略の要約 |

同じ日に、[器と研究の残りの棚卸し](reference/inventory-vessels-research-heads-2026-11-09.md)(`11-05/§3-2` の 3)を足しました。

### 5-3 v1 の写し(`reference/v1/`・8 本)

**旧**(置き換え: このリポ=v2)。v1 リポのまとめ文書の写しで、2026-09-01 に凍結しました。編集しません。中身は [_ABOUT.md](reference/v1/_ABOUT.md)・[README-v1.md](reference/v1/README-v1.md)・[v1-inventory.md](reference/v1/v1-inventory.md)・[RESULTS.md](reference/v1/RESULTS.md)・[PENDING.md](reference/v1/PENDING.md)・`IMPLEMENTED.md`(名前だけ)・[ETHICS.md](reference/v1/ETHICS.md)・[devlog-compressed.md](reference/v1/devlog-compressed.md) です。

## 6. 運用(`ops/`・24 本)

| 文書 | 一言 |
|---|---|
| [version-history.md](ops/version-history.md) | 版上げの履歴とタグ・戻し方(2026-11-05 に STATUS から移した) |
| [night5070-runbook.md](ops/night5070-runbook.md) | 5070 の夜の実験の手順 |
| [v2-server-lessons.md](ops/v2-server-lessons.md) | サーバーで回して初めて分かったこと |
| [layer2-review-checklist.md](ops/layer2-review-checklist.md) | 層 2 の独立検収のチェックリスト |
| [build-report-C0.md](ops/build-report-C0.md)〜[build-report-C6.md](ops/build-report-C6.md)(7 本) | 工程 C0〜C6 の受入報告 |
| `build-report-C7.md`・`build-report-C8.md` | 工程 C7・C8 の受入報告(名前だけ載せる。読む役は開かない=§11) |
| [goal_c0_c4.md](ops/goal_c0_c4.md)・[goal_c5_c8.md](ops/goal_c5_c8.md) | 無人運転の条件文(C0〜C4・C5〜C8) |
| [compute-vendors-2026-09-17.md](ops/compute-vendors-2026-09-17.md) | 有償 GPU の候補と見積り |
| `discord_report_*.md`(6 本) | 外向けの報告の文案(09-09・09-10・09-17 朝と夜・09-18・09-26) |
| [murata-lab-inquiry-draft-2026-10-12.md](ops/murata-lab-inquiry-draft-2026-10-12.md)・[u9-inquiry-draft-2026-09-30.md](ops/u9-inquiry-draft-2026-09-30.md) | 問い合わせの下書き |

## 7. 記録(`log/`・4 本)

| 文書 | 一言 |
|---|---|
| [devlog.md](log/devlog.md) | 開発ログ(毎交換 1 件・10 件で圧縮へ移す) |
| [devlog-compressed.md](log/devlog-compressed.md) | 圧縮した開発ログ |
| [pending-archive-2026-09-28.md](log/pending-archive-2026-09-28.md) | **旧**(置き換え: [PENDING.md](../PENDING.md)・第 279)。2026-09-08〜09-27 の PENDING の全文 |
| [pending-archive-2026-10-25.md](log/pending-archive-2026-10-25.md) | **旧**(置き換え: [PENDING.md](../PENDING.md) の 3 区分の形・第 339)。組み直す前の PENDING の全文 |

## 8. その他

| 文書 | 一言 |
|---|---|
| [funding/mitou-advanced-research.md](funding/mitou-advanced-research.md) | 未踏アドバンスト事業の事前リサーチ(2026-09-14) |
| [plateau2026/check-3-3.md](plateau2026/check-3-3.md) | PLATEAU AWARD の「先に確かめること」(2026-11-05) |
| [reviews/external-review-2026-10-13.md](reviews/external-review-2026-10-13.md) | 外部の評価(別のエージェントがコードまで読んだ) |
| [reviews/triage-2026-10-13/](reviews/triage-2026-10-13/README.md)(5 本) | 外部の評価の仕分け(README と A〜D) |
| [data-license-ledger.md](data-license-ledger.md) | データ・ライセンス台帳(データを取得するたびに 1 行足す) |
| `handover-memory.md` | 名前だけ載せる(開いていない)。CLAUDE.md の冒頭によれば、メモリの引き継ぎの手順。`11-09/§1-4` により、ユーザーが決めるまで触らない |

## 9. docs の外(リポの根)

- [STATUS.md](../STATUS.md): 今どの段か・次の 1 手(1 画面の索引)。
- [PENDING.md](../PENDING.md): 判断待ち・決定済みで実装待ち・研究の題。
- `IMPLEMENTED.md`: 完了した実装(名前だけ載せる。読む役は開かない=§11)。
- [CLAUDE.md](../CLAUDE.md): 運用の規律。

## 10. 「旧」の印の一覧

| 文書 | 置き換えた文書 | 根拠 |
|---|---|---|
| [design/v2-wallbounce-notes-2026-10-07-12.md](design/v2-wallbounce-notes-2026-10-07-12.md) | [design/v2-wallbounce-decisions-2026-10-12.md](design/v2-wallbounce-decisions-2026-10-12.md) | 本書の冒頭の注「決定は 10-12 の指示書が正・設計書・コード・判断の根拠にしない」。指示書 10-12 の保存の注記にも「読まない・決定は本書が正」とある |
| [reference/behavior-audit-triage-2026-11-03.md](reference/behavior-audit-triage-2026-11-03.md) | [reference/behavior-audit-triage-2026-11-04.md](reference/behavior-audit-triage-2026-11-04.md) | 11-04 版の冒頭が自分を「仕分けのやり直し」、11-03 版を「旧の表」と書く。ユーザーは 11-04 版の親案を採った(`11-04c` §2 の 1) |
| [log/pending-archive-2026-09-28.md](log/pending-archive-2026-09-28.md) | [PENDING.md](../PENDING.md) | 本書の冒頭「凍結・参照専用・更新しない。現行は PENDING.md」 |
| [log/pending-archive-2026-10-25.md](log/pending-archive-2026-10-25.md) | [PENDING.md](../PENDING.md)(回答 10-25 §3-2 の 3 区分の形) | 本書の冒頭「3 区分へ組み直す前に、原文のまま凍結した(参照専用)」 |
| [reference/v1/](reference/v1/_ABOUT.md) の 8 本 | このリポ(v2) | [_ABOUT.md](reference/v1/_ABOUT.md)「v1 参照スナップショット(2026-09-01 凍結)・編集しない」と、[README-v1.md](reference/v1/README-v1.md)「参照専用ベースライン・第 2 世代は v2 のリポで進める」 |

印を付けたのは 5 行・12 本です。

古く見えても、置き換えの記録が見つからなかったので印を付けていないものがあります。

- 問いの一覧の草案 8 本(§3-5): 答えは指示書 10-12 などで出ていますが、草案は問いと答えの記録として残っています。
- [RESEARCH-STATE.md](research/RESEARCH-STATE.md): 最終更新は 2026-09-17 ですが、後を継ぐ文書は見つかりませんでした。
- [v2-requirements.md](design/v2-requirements.md): 一部の要件は[改訂記録](design/v2-requirements-revision-log.md)で直されていますが、文書全体は置き換えられていません。
- 契約書と設計書(§3-4): 後の指示書で一部が上書きされ、各文書に改訂の印があります。

## 11. 読む役が開かない文書

次の文書は、名前だけを載せています。文書を読む役への発注では「開かない」としている範囲です(段 2 の突き合わせの冒頭の「開かない約束の文書」と同じ範囲)。

- リポの根の `IMPLEMENTED.md`(v1 の写しの `reference/v1/IMPLEMENTED.md` も開いていない)
- `ops/build-report-C7.md`・`ops/build-report-C8.md`
- `design/v2-g1-backtest-plan-2026-11-02.md`(門 1 の計画)
- `design/v2-pattern-ledger.md`(パターン台帳)
- `bench/anchors/` の `*_validation_anchors_v0.json` 3 本
- `handover-memory.md`
- docs の外の `data/` の下の全部

検証の値が普通の文書のどこにあるかは、名前と行番号だけの一覧 [opened-values-in-docs-2026-11-09.md](reference/opened-values-in-docs-2026-11-09.md) にあります(`11-09/§6-3` の 2)。データの 2 つの組(答え合わせ専用・学びの候補)は [data-two-groups-2026-11-09.md](reference/data-two-groups-2026-11-09.md)。
