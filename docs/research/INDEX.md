# 答申の索引(docs/research/ 73 本)

> 作成 2026-09-15(第191)。ユーザー指示 09-15「リサーチをした v2 のレポートも見やすくしてほしい/全部にヘッダを入れたい」。
> **v1 には `docs/references.md` と `docs/research-scope.md` があったが、v2 には索引が一つも無かった**。本書がその位置。
> 各答申の**文言は一行も変えていない**。頭に 3 行のヘッダ(`<!-- hdr:v1 -->`)を足しただけ(空行が 3 連続していた 14 本で空行 1 行が詰まったのが唯一の差分)。設計書からの参照は全部生きている。
> 分野番号は [分野地図](v2-discipline-map.md) の 32 分野。**分野と重要度は親(Opus 5)の判断**であって、答申自身の申告ではない。

## 0. 一次確認の等級(このヘッダで一番大事な欄)

| 等級 | 意味 | 本数 |
|---|---|---|
| **A** | 親検収済(逐語引用または再計算つき) | 7 |
| **B** | 出典あり・空欄を明示(残務台帳へ写し済みまたは要写し) | 56 |
| **C** | 出典あり・空欄は未整理 | 1 |
| **D** | **出典 URL なし(2026-09-02 の規律導入前)**=一次確認が丸ごと残る | 33 |
| **E** | 出典不要(親自身の一次作業) | 4 |

判定は機械的に行った(出典痕跡 = URL + arXiv ID + DOI + ✔ + 「著者 年」表記の総数)。
例外は 4 本だけ親が中身を見て上書きした(理由は各ファイルのヘッダに書いてある)。

---

## 1. 最重要 — 33 本は出典 URL を 1 つも持っていない

**2026-08-30〜09-01 に書かれた 33 本すべてが URL 0 件**。出典痕跡の合計も 0〜17 件(9 本は完全にゼロ)。
これに対し **09-02 以降の 40 本は出典痕跡の中央値が 62 件**。桁が違う。

この断層には理由がある。**2026-09-03 に「サブ捏造申告事件」(孫サブの沈黙 → 親サブが出典を捏造)が起きて、
CLAUDE.md §5 に「リサーチサブは子サブを起動しない」「答申の出典・数値・条番号は正典化前に親が一次確認する」が追加された**。
33 本はその規律が入る**前**のバッチにあたる。

> **扱い**: 中身が間違っていると決まったわけではない。しかし **これらを根拠に新しい決定をしてはいけない**。
> 使うときは、その数値だけを一次確認してから使う。題名に「全出典URL付き」とあるものも含めて、ファイル内に URL は無い。

| 重要度 | 答申 | 行 | 痕跡 | 分野 |
|---|---|---|---|---|
| P1 | [v2-game-frontend-research](v2-game-frontend-research.md) | 79 | 4 | ゲームエンジン工学・CG #30 |
| P1 | [v2-benchmark-standards-research](v2-benchmark-standards-research.md) | 101 | 2 | 検証とV&V・UQ #22 |
| P1 | [v2-digital-twin-landscape-research](v2-digital-twin-landscape-research.md) | 89 | 1 | 計算社会科学 #25 |
| P1 | [v2-engine-llm-boundary-research](v2-engine-llm-boundary-research.md) | 106 | 0 | 計算社会科学 #25 |
| P1 | [v2-game-tech-import-research](v2-game-tech-import-research.md) | 59 | 1 | ゲームエンジン工学・CG #30 |
| P1 | [v2-llm-knowledge-deep-research](v2-llm-knowledge-deep-research.md) | 226 | 5 | 自然言語処理・機械学習 #27 |
| P1 | [v2-llm-mobility-research](v2-llm-mobility-research.md) | 94 | 5 | 人間移動科学 #3 / 自然言語処理・機械学習 #27 |
| P1 | [v2-memory-retrieval-research](v2-memory-retrieval-research.md) | 69 | 4 | 認知科学(記憶・習慣) #12 |
| P1 | [v2-mobility-field-research](v2-mobility-field-research.md) | 87 | 13 | 人間移動科学 #3 / 交通工学(活動ベース) #2 |
| P1 | [v2-prediction-module-deep-research](v2-prediction-module-deep-research.md) | 218 | 17 | 認知科学(記憶・習慣) #12 |
| P1 | [v2-science-claims-research](v2-science-claims-research.md) | 109 | 9 | 科学哲学 #26 / 計算社会科学 #25 |
| P1 | [v2-small-scale-verification-research](v2-small-scale-verification-research.md) | 82 | 4 | 検証とV&V・UQ #22 |
| P1 | [v2-boundary-deep-research](v2-boundary-deep-research.md) | 146 | 1 | 人口学・合成人口論 #1 / 交通工学(活動ベース) #2 |
| P1 | [v2-conversation-deep-research](v2-conversation-deep-research.md) | 86 | 0 | 会話分析・語用論 #15 |
| P1 | [v2-coupled-adaptation-deep-research](v2-coupled-adaptation-deep-research.md) | 200 | 8 | ABM方法論 #21 |
| P1 | [v2-economy-sfc-deep-research](v2-economy-sfc-deep-research.md) | 143 | 0 | SFCマクロ経済学 #10 |
| P1 | [v2-institutions-deep-research](v2-institutions-deep-research.md) | 98 | 1 | 法学(業法・条例) #11 |
| P1 | [v2-legal-licensing-deep-research](v2-legal-licensing-deep-research.md) | 93 | 0 | 研究倫理・情報法 #31 |
| P1 | [v2-llm-serving-deep-research](v2-llm-serving-deep-research.md) | 92 | 0 | 自然言語処理・機械学習 #27 / 計算機科学(並列・決定論) #28 |
| P1 | [v2-observation-projection-deep-research](v2-observation-projection-deep-research.md) | 103 | 1 | 検証とV&V・UQ #22 |
| P1 | [v2-parallel-execution-deep-research](v2-parallel-execution-deep-research.md) | 91 | 1 | 計算機科学(並列・決定論) #28 |
| P1 | [v2-pattern-ledger-deep-research](v2-pattern-ledger-deep-research.md) | 112 | 7 | ABM方法論 #21 |
| P1 | [v2-persona-population-deep-research](v2-persona-population-deep-research.md) | 88 | 1 | 人格心理学 #13 / 人口学・合成人口論 #1 |
| P1 | [v2-precedent-system-deep-research](v2-precedent-system-deep-research.md) | 221 | 5 | 法学(業法・条例) #11 |
| P2 | [v2-data-contract-research](v2-data-contract-research.md) | 88 | 6 | ソフトウェア工学 #29 |
| P2 | [v2-capabilities-business-research](v2-capabilities-business-research.md) | 93 | 9 | 分野外(事業・資金) #0 |
| P2 | [v2-impact-risk-research](v2-impact-risk-research.md) | 94 | 11 | 研究倫理・情報法 #31 |
| P2 | [v2-learned-simulation-research](v2-learned-simulation-research.md) | 98 | 2 | 自然言語処理・機械学習 #27 |
| P2 | [v2-world-model-relation-research](v2-world-model-relation-research.md) | 91 | 10 | 計算社会科学 #25 |
| P2 | [v2-content-safety-deep-research](v2-content-safety-deep-research.md) | 86 | 0 | 研究倫理・情報法 #31 |
| P2 | [v2-funding-deep-research](v2-funding-deep-research.md) | 103 | 0 | 分野外(事業・資金) #0 |
| P2 | [v2-longrun-ops-deep-research](v2-longrun-ops-deep-research.md) | 88 | 0 | ソフトウェア工学 #29 |
| P2 | [v2-publication-ethics-deep-research](v2-publication-ethics-deep-research.md) | 80 | 1 | 研究倫理・情報法 #31 |

**このうち P0 は 0 本**。
→ 残務台帳 [research-backlog.md](research-backlog.md) の **R-23** として新規に登録した。

---

## 2. 分野別の索引(32 分野)

| # | 分野 | 答申 | 最良の等級 |
|---|---|---|---|
| 1 | **人口学・合成人口論** | [boundary-economy-u10-u11-research](v2-boundary-economy-u10-u11-research.md) P0 ・ [hobby-preference-research](v2-hobby-preference-research.md) P0 ・ [population-synthesis-research](v2-population-synthesis-research.md) P0 ・ [boundary-deep-research](v2-boundary-deep-research.md) P1 ・ [kddi-attribute-shares-2024](v2-kddi-attribute-shares-2024.md) P1 ・ [persona-population-deep-research](v2-persona-population-deep-research.md) P1 | B |
| 2 | **交通工学(活動ベース)** | [c9-geometry-capacity-research](v2-c9-geometry-capacity-research.md) P0 ・ [d66-outside-residents-research](v2-d66-outside-residents-research.md) P0 ・ [boundary-deep-research](v2-boundary-deep-research.md) P1 ・ [mobility-field-research](v2-mobility-field-research.md) P1 | B |
| 3 | **人間移動科学** | [c7-fix-research](v2-c7-fix-research.md) P0 ・ [c9-position-attention-research](v2-c9-position-attention-research.md) P0 ・ [d66-outside-residents-research](v2-d66-outside-residents-research.md) P0 ・ [d68-behavioral-diversity-research](v2-d68-behavioral-diversity-research.md) P0 ・ [d68-remaining-research](v2-d68-remaining-research.md) P0 ・ [preference-vector-research](v2-preference-vector-research.md) P0 ・ [r23-primary-check-batch2](v2-r23-primary-check-batch2.md) P0 ・ [d1-reacquisition](v2-d1-reacquisition.md) P1 ・ [destination-choice-llm-research](v2-destination-choice-llm-research.md) P1 ・ [llm-mobility-research](v2-llm-mobility-research.md) P1 ・ [mobility-field-research](v2-mobility-field-research.md) P1 | B |
| 4 | **時間利用研究** | [c7-fix-research](v2-c7-fix-research.md) P0 ・ [d68-behavioral-diversity-research](v2-d68-behavioral-diversity-research.md) P0 ・ [d68-remaining-research](v2-d68-remaining-research.md) P0 ・ [hobby-preference-research](v2-hobby-preference-research.md) P0 ・ [thought-frequency-anchors-note](v2-thought-frequency-anchors-note.md) P0 | A |
| 5 | **知覚心理学・精神物理学** | [channel-budget-attention-research](v2-channel-budget-attention-research.md) P0 ・ [density-hearing-verification](v2-density-hearing-verification.md) P0 ・ [observation-format-research](v2-observation-format-research.md) P0 ・ [p-notice-research](v2-p-notice-research.md) P0 ・ [perception-latency-research](v2-perception-latency-research.md) P0 ・ [perception-timing-research](v2-perception-timing-research.md) P0 ・ [perception-u17-research](v2-perception-u17-research.md) P0 ・ [person-perception-verification](v2-person-perception-verification.md) P1 | B |
| 6 | **環境音響学** | [density-hearing-verification](v2-density-hearing-verification.md) P0 ・ [update-rules-hearing-research](v2-update-rules-hearing-research.md) P0 ・ [world-data-build-round2-research](v2-world-data-build-round2-research.md) P0 ・ [hearing-numbers-and-d1-coverage](v2-hearing-numbers-and-d1-coverage.md) P1 | B |
| 7 | **建築環境工学** | [world-data-build-round2-research](v2-world-data-build-round2-research.md) P0 | B |
| 8 | **気象学・生気象学** | [world-data-build-round2-research](v2-world-data-build-round2-research.md) P0 | B |
| 9 | **地理情報科学** | [area-boundary-definition](v2-area-boundary-definition.md) P0 ・ [c9-geometry-capacity-research](v2-c9-geometry-capacity-research.md) P0 ・ [w7-law-primary-check-research](v2-w7-law-primary-check-research.md) P0 ・ [world-data-build-research](v2-world-data-build-research.md) P0 ・ [area-boundary-map-reading](v2-area-boundary-map-reading.md) P1 ・ [cell-granularity-research](v2-cell-granularity-research.md) P1 | A |
| 10 | **SFCマクロ経済学** | [boundary-economy-u10-u11-research](v2-boundary-economy-u10-u11-research.md) P0 ・ [r23-primary-check-batch2](v2-r23-primary-check-batch2.md) P0 ・ [world-process-rows-research](v2-world-process-rows-research.md) P0 ・ [economy-sfc-deep-research](v2-economy-sfc-deep-research.md) P1 ・ [ugc-platform-import](v2-ugc-platform-import.md) P1 | B |
| 11 | **法学(業法・条例)** | [c9-geometry-capacity-research](v2-c9-geometry-capacity-research.md) P0 ・ [r23-primary-check-batch2](v2-r23-primary-check-batch2.md) P0 ・ [w7-law-primary-check-research](v2-w7-law-primary-check-research.md) P0 ・ [institutions-deep-research](v2-institutions-deep-research.md) P1 ・ [precedent-system-deep-research](v2-precedent-system-deep-research.md) P1 | A |
| 12 | **認知科学(記憶・習慣)** | [action-conversation-contract-research](v2-action-conversation-contract-research.md) P0 ・ [c9-position-attention-research](v2-c9-position-attention-research.md) P0 ・ [cognition-detail-research](v2-cognition-detail-research.md) P0 ・ [d68-remaining-research](v2-d68-remaining-research.md) P0 ・ [d71-vocab-growth-research](v2-d71-vocab-growth-research.md) P0 ・ [personality-traits-research](v2-personality-traits-research.md) P0 ・ [r23-primary-check-batch3](v2-r23-primary-check-batch3.md) P0 ・ [r39-judgment-share-research](v2-r39-judgment-share-research.md) P0 ・ [r41-cognitive-architecture-precedents](v2-r41-cognitive-architecture-precedents.md) P0 ・ [r42-social-methodology-precedents](v2-r42-social-methodology-precedents.md) P0 ・ [thought-frequency-anchors-note](v2-thought-frequency-anchors-note.md) P0 ・ [update-rules-hearing-research](v2-update-rules-hearing-research.md) P0 ・ [c10-initial-relations-research](v2-c10-initial-relations-research.md) P1 ・ [memory-retrieval-research](v2-memory-retrieval-research.md) P1 ・ [prediction-module-deep-research](v2-prediction-module-deep-research.md) P1 | A |
| 13 | **人格心理学** | [d68-behavioral-diversity-research](v2-d68-behavioral-diversity-research.md) P0 ・ [hobby-preference-research](v2-hobby-preference-research.md) P0 ・ [persona-dynamics-research](v2-persona-dynamics-research.md) P0 ・ [personality-traits-research](v2-personality-traits-research.md) P0 ・ [preference-vector-research](v2-preference-vector-research.md) P0 ・ [persona-population-deep-research](v2-persona-population-deep-research.md) P1 | B |
| 14 | **社会ネットワーク科学** | [ad-information-research](v2-ad-information-research.md) P0 ・ [r42-social-methodology-precedents](v2-r42-social-methodology-precedents.md) P0 ・ [c10-initial-relations-research](v2-c10-initial-relations-research.md) P1 | B |
| 15 | **会話分析・語用論** | [action-conversation-contract-research](v2-action-conversation-contract-research.md) P0 ・ [r23-primary-check-batch2](v2-r23-primary-check-batch2.md) P0 ・ [thought-frequency-anchors-note](v2-thought-frequency-anchors-note.md) P0 ・ [conversation-deep-research](v2-conversation-deep-research.md) P1 | A |
| 16 | **行動経済学・マーケティング科学** | [ad-information-research](v2-ad-information-research.md) P0 ・ [price-formation-llm-research](v2-price-formation-llm-research.md) P1 | B |
| 17 | **小売科学・商業立地論** | [c9-geometry-capacity-research](v2-c9-geometry-capacity-research.md) P0 ・ [price-formation-llm-research](v2-price-formation-llm-research.md) P1 | B |
| 18 | **歩行者動力学** | [c9-geometry-capacity-research](v2-c9-geometry-capacity-research.md) P0 ・ [c9-position-attention-research](v2-c9-position-attention-research.md) P0 ・ [crowd-physics-research](v2-crowd-physics-research.md) P0 ・ [r41-cognitive-architecture-precedents](v2-r41-cognitive-architecture-precedents.md) P0 ・ [r42-social-methodology-precedents](v2-r42-social-methodology-precedents.md) P0 | A |
| 19 | **都市代謝論・MFA** | [world-process-inventory-research](v2-world-process-inventory-research.md) P0 ・ [world-process-rows-research](v2-world-process-rows-research.md) P0 | B |
| 20 | **オペレーションズリサーチ** | [world-process-inventory-research](v2-world-process-inventory-research.md) P0 | B |
| 21 | **ABM方法論** | [classical-vs-llm-simulation-research](v2-classical-vs-llm-simulation-research.md) P0 ・ [d71-vocab-growth-research](v2-d71-vocab-growth-research.md) P0 ・ [preference-vector-research](v2-preference-vector-research.md) P0 ・ [r23-primary-check-batch3](v2-r23-primary-check-batch3.md) P0 ・ [r39-judgment-share-research](v2-r39-judgment-share-research.md) P0 ・ [r42-social-methodology-precedents](v2-r42-social-methodology-precedents.md) P0 ・ [replication-count-research](v2-replication-count-research.md) P0 ・ [research-reflection-audit-p1p2](v2-research-reflection-audit-p1p2.md) P0 ・ [research-reflection-audit](v2-research-reflection-audit.md) P0 ・ [c10-initial-relations-research](v2-c10-initial-relations-research.md) P1 ・ [coupled-adaptation-deep-research](v2-coupled-adaptation-deep-research.md) P1 ・ [destination-choice-llm-research](v2-destination-choice-llm-research.md) P1 ・ [micro-observation-research](v2-micro-observation-research.md) P1 ・ [pattern-ledger-deep-research](v2-pattern-ledger-deep-research.md) P1 ・ [r23-primary-check-batch1](v2-r23-primary-check-batch1.md) P1 ・ [world-ledger-verification](v2-world-ledger-verification.md) P1 | A |
| 22 | **検証とV&V・UQ** | [dashboard-verification-orchestration-research](v2-dashboard-verification-orchestration-research.md) P0 ・ [r23-primary-check-batch3](v2-r23-primary-check-batch3.md) P0 ・ [r42-social-methodology-precedents](v2-r42-social-methodology-precedents.md) P0 ・ [statistics-causal-research](v2-statistics-causal-research.md) P0 ・ [turing-test-validation-research](v2-turing-test-validation-research.md) P0 ・ [world-coverage-index-research](v2-world-coverage-index-research.md) P0 ・ [benchmark-standards-research](v2-benchmark-standards-research.md) P1 ・ [micro-observation-research](v2-micro-observation-research.md) P1 ・ [observation-projection-deep-research](v2-observation-projection-deep-research.md) P1 ・ [r2-llm-social-sim-fulltext-check](v2-r2-llm-social-sim-fulltext-check.md) P1 ・ [r23-primary-check-batch1](v2-r23-primary-check-batch1.md) P1 ・ [small-scale-verification-research](v2-small-scale-verification-research.md) P1 ・ [vlm-reality-check-research](v2-vlm-reality-check-research.md) P1 | A |
| 23 | **統計学・因果推論** | [replication-count-research](v2-replication-count-research.md) P0 ・ [statistics-causal-research](v2-statistics-causal-research.md) P0 ・ [r2-llm-social-sim-fulltext-check](v2-r2-llm-social-sim-fulltext-check.md) P1 | A |
| 24 | **予測科学(アンサンブル)** | [dashboard-verification-orchestration-research](v2-dashboard-verification-orchestration-research.md) P0 | A |
| 25 | **計算社会科学** | [c9-position-attention-research](v2-c9-position-attention-research.md) P0 ・ [classical-vs-llm-simulation-research](v2-classical-vs-llm-simulation-research.md) P0 ・ [llm-social-sim-timeline-seed](v2-llm-social-sim-timeline-seed.md) P0 ・ [r23-primary-check-batch2](v2-r23-primary-check-batch2.md) P0 ・ [r23-primary-check-batch3](v2-r23-primary-check-batch3.md) P0 ・ [r42-social-methodology-precedents](v2-r42-social-methodology-precedents.md) P0 ・ [destination-choice-llm-research](v2-destination-choice-llm-research.md) P1 ・ [digital-twin-landscape-research](v2-digital-twin-landscape-research.md) P1 ・ [engine-llm-boundary-research](v2-engine-llm-boundary-research.md) P1 ・ [r2-llm-social-sim-fulltext-check](v2-r2-llm-social-sim-fulltext-check.md) P1 ・ [r23-primary-check-batch1](v2-r23-primary-check-batch1.md) P1 ・ [science-claims-research](v2-science-claims-research.md) P1 ・ [world-model-relation-research](v2-world-model-relation-research.md) P2 | B |
| 26 | **科学哲学** | [classical-vs-llm-simulation-research](v2-classical-vs-llm-simulation-research.md) P0 ・ [turing-test-validation-research](v2-turing-test-validation-research.md) P0 ・ [science-claims-research](v2-science-claims-research.md) P1 | B |
| 27 | **自然言語処理・機械学習** | [d71-vocab-growth-research](v2-d71-vocab-growth-research.md) P0 ・ [observation-format-research](v2-observation-format-research.md) P0 ・ [personality-traits-research](v2-personality-traits-research.md) P0 ・ [r23-primary-check-batch3](v2-r23-primary-check-batch3.md) P0 ・ [r38-closed-output-judges-research](v2-r38-closed-output-judges-research.md) P0 ・ [r39-judgment-share-research](v2-r39-judgment-share-research.md) P0 ・ [r40-jev-details-research](v2-r40-jev-details-research.md) P0 ・ [r41-cognitive-architecture-precedents](v2-r41-cognitive-architecture-precedents.md) P0 ・ [c10-initial-relations-research](v2-c10-initial-relations-research.md) P1 ・ [destination-choice-llm-research](v2-destination-choice-llm-research.md) P1 ・ [jev-system-one-note](v2-jev-system-one-note.md) P1 ・ [llm-knowledge-deep-research](v2-llm-knowledge-deep-research.md) P1 ・ [llm-mobility-research](v2-llm-mobility-research.md) P1 ・ [llm-serving-deep-research](v2-llm-serving-deep-research.md) P1 ・ [openjev-note](v2-openjev-note.md) P1 ・ [r2-llm-social-sim-fulltext-check](v2-r2-llm-social-sim-fulltext-check.md) P1 ・ [learned-simulation-research](v2-learned-simulation-research.md) P2 | A |
| 28 | **計算機科学(並列・決定論)** | [cell-granularity-research](v2-cell-granularity-research.md) P1 ・ [implementation-stack-research](v2-implementation-stack-research.md) P1 ・ [llm-serving-deep-research](v2-llm-serving-deep-research.md) P1 ・ [parallel-execution-deep-research](v2-parallel-execution-deep-research.md) P1 ・ [r2-llm-social-sim-fulltext-check](v2-r2-llm-social-sim-fulltext-check.md) P1 ・ [run-manifest-concurrency-research](v2-run-manifest-concurrency-research.md) P1 | B |
| 29 | **ソフトウェア工学** | [r23-primary-check-batch3](v2-r23-primary-check-batch3.md) P0 ・ [r38-closed-output-judges-research](v2-r38-closed-output-judges-research.md) P0 ・ [r40-jev-details-research](v2-r40-jev-details-research.md) P0 ・ [r41-cognitive-architecture-precedents](v2-r41-cognitive-architecture-precedents.md) P0 ・ [research-reflection-audit-p1p2](v2-research-reflection-audit-p1p2.md) P0 ・ [research-reflection-audit](v2-research-reflection-audit.md) P0 ・ [implementation-stack-research](v2-implementation-stack-research.md) P1 ・ [jev-system-one-note](v2-jev-system-one-note.md) P1 ・ [micro-observation-research](v2-micro-observation-research.md) P1 ・ [openjev-note](v2-openjev-note.md) P1 ・ [run-manifest-concurrency-research](v2-run-manifest-concurrency-research.md) P1 ・ [data-contract-research](v2-data-contract-research.md) P2 ・ [longrun-ops-deep-research](v2-longrun-ops-deep-research.md) P2 | A |
| 30 | **ゲームエンジン工学・CG** | [r23-primary-check-batch3](v2-r23-primary-check-batch3.md) P0 ・ [r41-cognitive-architecture-precedents](v2-r41-cognitive-architecture-precedents.md) P0 ・ [game-frontend-research](v2-game-frontend-research.md) P1 ・ [game-tech-import-research](v2-game-tech-import-research.md) P1 ・ [ugc-platform-import](v2-ugc-platform-import.md) P1 | B |
| 31 | **研究倫理・情報法** | [r38-closed-output-judges-research](v2-r38-closed-output-judges-research.md) P0 ・ [r40-jev-details-research](v2-r40-jev-details-research.md) P0 ・ [ethics-operations-research](v2-ethics-operations-research.md) P1 ・ [legal-licensing-deep-research](v2-legal-licensing-deep-research.md) P1 ・ [content-safety-deep-research](v2-content-safety-deep-research.md) P2 ・ [impact-risk-research](v2-impact-risk-research.md) P2 ・ [publication-ethics-deep-research](v2-publication-ethics-deep-research.md) P2 | B |
| 32 | **犯罪学** | **なし** | — |

**答申が 1 本も無い分野: 1 個** — 犯罪学 #32

第180 の照合では「答申が無い 4 分野」としていたが、索引を作って数え直すと上のとおり。
差は、第180 が「主題として扱った答申」を数え、本索引が「その分野に紐づく答申」を数えているため。

---

## 3. 全 73 本(重要度 → 日付順)

合計 26,877 行。P0 48 / P1 44 / P2 9。

### P0(48 本)

| 日付 | 答申 | 行 | 一次確認 | 分野 | 役割 |
|---|---|---|---|---|---|
| 08-31 | [r23-primary-check-batch2](v2-r23-primary-check-batch2.md) | 262 | **B** | 計算社会科学 #25 / SFCマクロ経済学 #10 / 会話分析・語用論 #15 / 人間移動科学 #3 / 法学(業法・条例) #11 | 出典ゼロ答申の一次確認 第2批=背骨の 4 答申(経済 SFC・会話・人流・制度)。独立収束は過程レベルで不成立・D4 修正3・0.8・Decoupling・CPC フロア → D-78 |
| 09-02 | [ad-information-research](v2-ad-information-research.md) | 586 | **C** | 行動経済学・マーケティング科学 #16 / 社会ネットワーク科学 #14 | 広告・看板の実効と情報伝播。収益化方針の根拠 |
| 09-02 | [perception-u17-research](v2-perception-u17-research.md) | 1106 | **B** | 知覚心理学・精神物理学 #5 | 五感/VLA 知覚の導入(最大の答申・1,101行) |
| 09-04 | [area-boundary-definition](v2-area-boundary-definition.md) | 300 | **B** | 地理情報科学 #9 | 5エリア定義の一次確認。holdout 照合の写像が依存 |
| 09-04 | [density-hearing-verification](v2-density-hearing-verification.md) | 479 | **B** | 環境音響学 #6 / 知覚心理学・精神物理学 #5 | 可聴半径は人密度の関数か(敵対的検証) |
| 09-04 | [observation-format-research](v2-observation-format-research.md) | 456 | **B** | 知覚心理学・精神物理学 #5 / 自然言語処理・機械学習 #27 | 観測の表現形式・配置・トークン予算。知覚契約書 R3-8 |
| 09-04 | [perception-latency-research](v2-perception-latency-research.md) | 605 | **B** | 知覚心理学・精神物理学 #5 | 知覚遅延 δ_perc の導入判断 |
| 09-04 | [perception-timing-research](v2-perception-timing-research.md) | 583 | **B** | 知覚心理学・精神物理学 #5 | 知覚のタイミング |
| 09-04 | [turing-test-validation-research](v2-turing-test-validation-research.md) | 425 | **B** | 検証とV&V・UQ #22 / 科学哲学 #26 | 識別テスト(Turing型)の評価。第一目標の測り方 |
| 09-06 | [action-conversation-contract-research](v2-action-conversation-contract-research.md) | 474 | **B** | 会話分析・語用論 #15 / 認知科学(記憶・習慣) #12 | 行動契約(心→世界)と会話プロトコル。第2陣の主題に直結 |
| 09-06 | [boundary-economy-u10-u11-research](v2-boundary-economy-u10-u11-research.md) | 451 | **B** | SFCマクロ経済学 #10 / 人口学・合成人口論 #1 | 境界(来街の決定)と経済SFC。保存則の運用形が依存 |
| 09-06 | [channel-budget-attention-research](v2-channel-budget-attention-research.md) | 529 | **B** | 知覚心理学・精神物理学 #5 | チャネル別観測予算と注意ゲート。知覚契約書の骨格 |
| 09-06 | [p-notice-research](v2-p-notice-research.md) | 506 | **B** | 知覚心理学・精神物理学 #5 | p_notice の関数形。2段ヒル型の根拠 |
| 09-06 | [update-rules-hearing-research](v2-update-rules-hearing-research.md) | 502 | **B** | 認知科学(記憶・習慣) #12 / 環境音響学 #6 | 更新規則(不応期・日次内省・繰り延べ)と聴覚数値 |
| 09-06 | [world-process-rows-research](v2-world-process-rows-research.md) | 440 | **B** | 都市代謝論・MFA #19 / SFCマクロ経済学 #10 | エンジン/LLM 線引き16行の詳細決定材料 |
| 09-07 | [cognition-detail-research](v2-cognition-detail-research.md) | 496 | **B** | 認知科学(記憶・習慣) #12 | δ_think 上限・思考トークン・記憶細部 |
| 09-07 | [persona-dynamics-research](v2-persona-dynamics-research.md) | 392 | **B** | 人格心理学 #13 | ペルソナは回す中で変化させる必要があるか |
| 09-07 | [population-synthesis-research](v2-population-synthesis-research.md) | 509 | **B** | 人口学・合成人口論 #1 | 母集団合成・40万体の実体化。W16 の根拠 |
| 09-07 | [world-coverage-index-research](v2-world-coverage-index-research.md) | 315 | **B** | 検証とV&V・UQ #22 | 世界の再現度指標(WCI)。第一目標の計器 |
| 09-07 | [world-data-build-research](v2-world-data-build-research.md) | 501 | **B** | 地理情報科学 #9 | 世界データ構築仕様 W1〜W22 の本体 |
| 09-07 | [world-data-build-round2-research](v2-world-data-build-round2-research.md) | 97 | **B** | 環境音響学 #6 / 気象学・生気象学 #8 / 建築環境工学 #7 | 騒音・交通量・気象・PLATEAU・法規 |
| 09-07 | [world-process-inventory-research](v2-world-process-inventory-research.md) | 340 | **B** | 都市代謝論・MFA #19 / オペレーションズリサーチ #20 | 世界過程の棚卸しと拡張ロードマップ。陣分けの出所 |
| 09-08 | [crowd-physics-research](v2-crowd-physics-research.md) | 70 | **A** | 歩行者動力学 #18 | 群衆物理 U15。幾何に基づく容量(R-8)の前提 |
| 09-08 | [dashboard-verification-orchestration-research](v2-dashboard-verification-orchestration-research.md) | 59 | **A** | 検証とV&V・UQ #22 / 予測科学(アンサンブル) #24 | 計器盤・検収戦略・オーケストレーション。G-1〜G-9 |
| 09-10 | [c7-fix-research](v2-c7-fix-research.md) | 465 | **B** | 人間移動科学 #3 / 時間利用研究 #4 | C7 の 2 つの歪みの現実側数値。D-66/D-67 の土台 |
| 09-10 | [d66-outside-residents-research](v2-d66-outside-residents-research.md) | 502 | **B** | 交通工学(活動ベース) #2 / 人間移動科学 #3 | 域外居住者の到着・退出アンカー。v2.1 読み口の根拠 |
| 09-11 | [d68-behavioral-diversity-research](v2-d68-behavioral-diversity-research.md) | 437 | **B** | 人間移動科学 #3 / 時間利用研究 #4 / 人格心理学 #13 | 行動の多様性。17モチーフ・予測可能性93%・同質化 |
| 09-12 | [llm-social-sim-timeline-seed](v2-llm-social-sim-timeline-seed.md) | 65 | **B** | 計算社会科学 #25 | LLM 社会シミュの現在地(未正典化)。R-2 の対象 17 件 |
| 09-16 | [replication-count-research](v2-replication-count-research.md) | 78 | **A** | 統計学・因果推論 #23 / ABM方法論 #21 | 反復回数(seed 数)の文献手続き 7 系譜と「初回 8 seed」の位置(L-B)。D-70/D-44/G-8 の材料。統計 #23 の最初の答申 |
| 09-16 | [w7-law-primary-check-research](v2-w7-law-primary-check-research.md) | 85 | **A** | 法学(業法・条例) #11 / 地理情報科学 #9 | W7 法規の条文一次確認とコード突合(L-24)。法学 #11 を D→A。D-72 の出所 |
| 09-17 | [c9-geometry-capacity-research](v2-c9-geometry-capacity-research.md) | 167 | **B** | 交通工学(活動ベース) #2 / 歩行者動力学 #18 / 地理情報科学 #9 / 法学(業法・条例) #11 / 小売科学・商業立地論 #17 | C9 幾何の容量 3 種+ホーム容量の実測化(L-R8): PLATEAU 歩道部面・法定幅員・経済センサス売場面積・建告1441/消防規則の密度・鈴木 2012 のホーム 3.30 人/m²。G8 の置換候補 |
| 09-17 | [classical-vs-llm-simulation-research](v2-classical-vs-llm-simulation-research.md) | 219 | **B** | 計算社会科学 #25 / ABM方法論 #21 / 科学哲学 #26 | 古典 ABM の要求 × LLM 系の新規性 × 検証の対照表(L-CLS)。「良い LLM 社会シミュレーション」判定基準 10 項(古典由来 6・LLM 由来 1・両方 3)・Axtell 2016 1.2 億体・Edmonds 2019 の 7 目的・観測的同値は Haavelmo 1944 |
| 09-17 | [d68-remaining-research](v2-d68-remaining-research.md) | 262 | **B** | 人間移動科学 #3 / 時間利用研究 #4 / 認知科学(記憶・習慣) #12 | D-68 経路 3(記憶・習慣)の残 10 件(R-3): 始業時刻の代理=時間帯編 15-4 表・通勤時間=住宅土地統計 58-2-1・交替制の深夜率 4.8〜14 倍・モチーフ 11〜17 型/83〜90%・Lu 2013 Π 0.88・REAL/2605.09995 は別の層 → K-1〜K-5(D-81) |
| 09-17 | [d71-vocab-growth-research](v2-d71-vocab-growth-research.md) | 140 | **B** | ABM方法論 #21 / 自然言語処理・機械学習 #27 / 認知科学(記憶・習慣) #12 | 観測から行動語彙を育てる仕組みの先行(Voyager/AWM/ASI/LearnAct/SayCan/CBR/活動分類の規模)。D-71 設計アジェンダ v2-vocab-growth-design.md の出所 |
| 09-17 | [hobby-preference-research](v2-hobby-preference-research.md) | 577 | **B** | 時間利用研究 #4 / 人格心理学 #13 / 人口学・合成人口論 #1 | 人の構成要素 P1=趣味・嗜好の公的分布(社会生活基本調査 R3 生活行動編・行動者率 全国 86.3/東京都 91.4・年齢勾配 7 倍・独立抽選は無趣味率で 98 倍ずれる・共起 φ≤0.53)→ 種目 58 bit+コピュラ+稀事象の待ち時間・W6 カタログの欠陥 3(公園が PLACE_PARK に行かない)・先行例ゼロ |
| 09-17 | [personality-traits-research](v2-personality-traits-research.md) | 473 | **B** | 人格心理学 #13 / 認知科学(記憶・習慣) #12 / 自然言語処理・機械学習 #27 | 人の構成要素 P2=性格: 規準=川本 2015(N 4,588・TIPI-J M/SD・因子間相関 −.29〜.32・年齢×性別の R² ≤5.35%)・効果量(外向性→会話 |r| .17・協調性→向社会 .12・開放性→移動は負・誠実性→時間厳守は空欄)・LLM 付与(Han 2025「persona は自己申告を動かすが行動は動かない」)→ C 案=入れずに測る(corr(z_E, 会話起点) 目標 .17)・traits 3 次元は設計書で未定義・プールの上側隆起 |
| 09-17 | [preference-vector-research](v2-preference-vector-research.md) | 331 | **B** | 人間移動科学 #3 / ABM方法論 #21 / 人格心理学 #13 | 人の構成要素 P3=選好ベクトルと常連/探索(EPR γ 0.21・Π=f・δ 1.2 / returners k=4・EPR は k≈60 / Schläpfer η≈2 / 外食リピート 77.5%・業態 32〜95.5%・Dubé 状態依存)→ 選好はエンジンの数値・二重計上の整理(戻る=K-1・探す=ρ_i・P3 は初回選択・P1/P2 は掛けない)・repo は店選択が「セル内最小 id」 |
| 09-17 | [r23-primary-check-batch3](v2-r23-primary-check-batch3.md) | 358 | **B** | ゲームエンジン工学・CG #30 / ソフトウェア工学 #29 / 検証とV&V・UQ #22 / ABM方法論 #21 / 認知科学(記憶・習慣) #12 / 自然言語処理・機械学習 #27 / 計算社会科学 #25 | R-23 第3批: D 等級だけを根拠にする決定台帳 18 行の一次確認=支持 9/訂正 9/撤回 0・主張 69・訂正 18(NCP-Bench 20 ターン 42%・0.599^10 導出値・1:5:25 は cascade 制御の実務比で Dunbar でない・L401 強 5 本の陳腐化・Pseudo-PFLOW 学習域・AutoAWQ 非推奨)・L385 三層世界方式の根拠答申は本リポに不在 |
| 09-17 | [research-reflection-audit-p1p2](v2-research-reflection-audit-p1p2.md) | 648 | **E** | ソフトウェア工学 #29 / ABM方法論 #21 | リサーチ反映の監査 B=P1 40+P2 9 本 244 項(実装済 35.7%・部分 24.6%・未判定 21.3%・設計済未実装 13.9%・未採用 4.5%)・分野別反映率(認知科学 #12 0%) |
| 09-17 | [research-reflection-audit](v2-research-reflection-audit.md) | 676 | **E** | ソフトウェア工学 #29 / ABM方法論 #21 | リサーチ反映の監査 A=P0 35 本 240 項(実装済 52.9%・設計済未実装 20.0%・部分 18.3%・未採用 4.6%・未判定 4.2%)・逆引き表 42 行・方法論遵守 12 行 |
| 09-17 | [statistics-causal-research](v2-statistics-causal-research.md) | 239 | **B** | 統計学・因果推論 #23 / 検証とV&V・UQ #22 | 統計学・因果推論 #23 の最初の答申(R-25): 多重比較/同値検定(Sargent 区間検定・TOST)・CRN・反実仮想(SCM・負の対照・S-RCT・History Matching)・GET 大域包絡(seed 3 本では p≥0.25)・CSB スクリーニング → prereg v1.3・D-70・D-44・到達点 C の作法 |
| 09-18 | [r39-judgment-share-research](v2-r39-judgment-share-research.md) | 270 | **B** | 認知科学(記憶・習慣) #12 / 自然言語処理・機械学習 #27 / ABM方法論 #21 | R-39 人の思考のうち判断の割合(第242): 直接測った研究は無い・最も近い一次値は Hofmann 2012(欲求あり 49.9%・葛藤 47%・抵抗 42%=派生 約 21%)・熟考の引き金は強度でなく葛藤(B=0.53 vs p=.17)・Type 1/2 の定義は速さでなく作業記憶(Evans & Stanovich 2013)・Type 2 は既定では発火しない(De Neys 正答 <20%・CRT 平均 1.24/3)が監視は常時走る・速い層に任せる条件は高妥当性環境+学習機会(Kahneman & Klein 2009)・系の最適個数は環境のばらつきとメタ推論コスト(Milli 2017)・FrugalGPT 最大 98% 削減・社会シミュでの毎決定ルーティング先行なし |
| 09-18 | [r40-jev-details-research](v2-r40-jev-details-research.md) | 357 | **B** | 自然言語処理・機械学習 #27 / ソフトウェア工学 #29 / 研究倫理・情報法 #31 | R-40 Jev の詳細(第242): 文脈長 64k/32k・レート 250,000 tok/s・1,200 req/min・1 リクエスト=1 state・バッチ API なし・timeout 10 s・日本語は精度低下明記・jaggedness ページ(context rot・Noul と Choice の算術非整合)・決定論の保証なし(温度/seed なし・std 0.0102 は uid 可変)・CEO が「ゼロショット分類器」に同意・アーキテクチャ非公開・MCA §2.3(f) ベンチマーク公表禁止・Telemetry 無制限・オンプレ不可・SLA なし・Vercel/Cloudflare 経由の入口・独立検証は小規模 2 件 |
| 09-18 | [thought-frequency-anchors-note](v2-thought-frequency-anchors-note.md) | 76 | **A** | 認知科学(記憶・習慣) #12 / 時間利用研究 #4 / 会話分析・語用論 #15 | 現実の人の思考・判断・会話の頻度の錨(第240・親一次読み): 思考の切り替わり 6.5 回/分=約 6,240/日(Tseng & Poppenk 2020)・思考の分節 5 秒=約 4,000/日(Klinger 1978)・内言 26%(Heavey & Hurlburt 2008)・心のさまよい 46.9%・会話 覚醒の 27.9%(Mehl & Pennebaker 2003)・活動エピソード 13.9/日(CTUR)vs シミュ LLM 呼 6.9/日・会話 0.00105 セッション/日(参加 0.0021)・計画ブロック 8.9/日=思考 580〜900 分の 1・会話ゼロ・活動切替だけ桁が合う → D-101 |
| 09-22 | [r38-closed-output-judges-research](v2-r38-closed-output-judges-research.md) | 436 | **B** | 自然言語処理・機械学習 #27 / ソフトウェア工学 #29 / 研究倫理・情報法 #31 | R-38 閉じた出力の判断層(第253): NLI ゼロショットの絶対精度は低い(Yin 2019 topic 45.7)が日本語モデルは実在(Formzu JSNLI 0.9288・親確認)。vLLM 公式は既定モードで logprob の安定性を非保証(第254 訂正: v2 の VLLM_BATCH_INVARIANT=1 構成では B14 で logprobs 32/32 一致=衝突しない)。自己申告 confidence での振り分けは ECE で批判あり(Xiong ICLR2024)。効くのは別学習のスコアラ(FrugalGPT DistilBERT)。社会シミュで毎決定を蒸留代理に置換した先行は在る(Light Society 10 億体・GenWorld 日本東広島 196,608 体を CPU 0.54us/件の lookup 表へ=親が本文逐語確認)が、実行時に学習ルータが振り分ける先行は無い=R-39 は狭い意味で維持 |
| 09-23 | [r41-cognitive-architecture-precedents](v2-r41-cognitive-architecture-precedents.md) | 397 | **B** | 認知科学(記憶・習慣) #12 / 自然言語処理・機械学習 #27 / 歩行者動力学 #18 / ゲームエンジン工学・CG #30 / ソフトウェア工学 #29 | R-41 認知アーキテクチャ議事録(個体側)の先行検証(第255→第256 親検収): 再考の引き金は先行も単一閾値を採らないが 6 項の重みつき線形和の先行は無い。BDI の intention reconsideration は 30 年前に実験済み(Kinny 1991「何でも再考は盲目的コミットより悪い」・Schut 2001 の適応エージェントが両方に勝つ・交差点 dynamism 28・Fox 2006 の plan repair は最初の行動一致 100% vs 44.3%=いずれも親逐語)。熟慮の System 1 へのコンパイルは 4 系譜が同形だが速度則の数値は空欄。PIANO は「世界を止めずに考える」の先行(10 モジュール並行・親逐語)だが stale/中断は書いていない。群衆 LOD 9 系統はすべて観測者基準=エージェント自身の状況で決める形は先行なし。Moussaid 2011 の「高密度では物理が意図を支配」は原典に無い=親が訂正 |
| 09-23 | [r42-social-methodology-precedents](v2-r42-social-methodology-precedents.md) | 374 | **B** | ABM方法論 #21 / 検証とV&V・UQ #22 / 計算社会科学 #25 / 社会ネットワーク科学 #14 / 歩行者動力学 #18 / 認知科学(記憶・習慣) #12 | R-42 認知・社会アーキテクチャ議事録の先行検証・社会側/方法論側(第255→第256 親検収): 議事録 §26 の causal depth は Lamport 1978 の happened-before+任意全順序と同型(v2 の pk)。群歩行 55%/70%(Moussaïd 2010・親逐語)。規範は罰/負の報酬なしに立った先行なし(Sen & Airiau 2007 親逐語・Axelrod 1986 は再実装で逆転=Galán 2005)・議事録の Norm 定義は Bicchieri の「慣習」。組織は MOISE+ の 3 次元と部分一致。噂モデルの 20.3%(二次)。Mechanistic/Behavioral/Emergent の 3 分類に一致する先行なし。ablation 行列は 72 万腕=Sobol/Morris で畳む。スクランブル 3,000 人は伝聞値 |
|  | [c9-position-attention-research](v2-c9-position-attention-research.md) | 180 | **B** | 人間移動科学 #3 / 歩行者動力学 #18 / 認知科学(記憶・習慣) #12 / 計算社会科学 #25 | C9 位置・速度・注意・会話距離・目印の先行(L-C9): LLM 系 4 通り・Weidmann/Kladek 式(γ=1.913)・希望速度 1.00〜1.60 m/s・FOA/UE Perception・Sorokowska 1.35 m・待ち合わせ実証 2 本 |

### P1(44 本)

| 日付 | 答申 | 行 | 一次確認 | 分野 | 役割 |
|---|---|---|---|---|---|
| 08-30 | [game-frontend-research](v2-game-frontend-research.md) | 79 | **D** | ゲームエンジン工学・CG #30 | ゲーム的フロントエンド。R-5 可視化の出発点 |
| 08-31 | [benchmark-standards-research](v2-benchmark-standards-research.md) | 101 | **D** | 検証とV&V・UQ #22 | 再現ベンチマークの実測標準 |
| 08-31 | [digital-twin-landscape-research](v2-digital-twin-landscape-research.md) | 89 | **D** | 計算社会科学 #25 | デジタルツインの実名ランドスケープ。未踏の位置づけに効く |
| 08-31 | [engine-llm-boundary-research](v2-engine-llm-boundary-research.md) | 106 | **D** | 計算社会科学 #25 | エンジン/LLM 線引き。v2 の背骨 |
| 08-31 | [game-tech-import-research](v2-game-tech-import-research.md) | 59 | **D** | ゲームエンジン工学・CG #30 | ゲーム/VR 産業技術の輸入(常設レーン) |
| 08-31 | [llm-knowledge-deep-research](v2-llm-knowledge-deep-research.md) | 226 | **D** | 自然言語処理・機械学習 #27 | LLM 事前知識の影響と活用/遮断 |
| 08-31 | [llm-mobility-research](v2-llm-mobility-research.md) | 94 | **D** | 人間移動科学 #3 / 自然言語処理・機械学習 #27 | LLM 起点の人流生成 |
| 08-31 | [memory-retrieval-research](v2-memory-retrieval-research.md) | 69 | **D** | 認知科学(記憶・習慣) #12 | 記憶と想起 |
| 08-31 | [mobility-field-research](v2-mobility-field-research.md) | 87 | **D** | 人間移動科学 #3 / 交通工学(活動ベース) #2 | 人流・交通シミュレーション分野の体系 |
| 08-31 | [prediction-module-deep-research](v2-prediction-module-deep-research.md) | 218 | **D** | 認知科学(記憶・習慣) #12 | エージェント内蔵の予測モジュール |
| 08-31 | [science-claims-research](v2-science-claims-research.md) | 109 | **D** | 科学哲学 #26 / 計算社会科学 #25 | 科学的知見・新規性の再検証 |
| 08-31 | [small-scale-verification-research](v2-small-scale-verification-research.md) | 82 | **D** | 検証とV&V・UQ #22 | 小資源検証の方法論 |
| 09-01 | [boundary-deep-research](v2-boundary-deep-research.md) | 146 | **D** | 人口学・合成人口論 #1 / 交通工学(活動ベース) #2 | 境界条件と人口の出自 |
| 09-01 | [conversation-deep-research](v2-conversation-deep-research.md) | 86 | **D** | 会話分析・語用論 #15 | 会話生成の実装 |
| 09-01 | [coupled-adaptation-deep-research](v2-coupled-adaptation-deep-research.md) | 200 | **D** | ABM方法論 #21 | 適応3ループの複合安定性 |
| 09-01 | [economy-sfc-deep-research](v2-economy-sfc-deep-research.md) | 143 | **D** | SFCマクロ経済学 #10 | 経済SFCの具体設計 |
| 09-01 | [institutions-deep-research](v2-institutions-deep-research.md) | 98 | **D** | 法学(業法・条例) #11 | 制度の最小足場と失敗の観測 |
| 09-01 | [legal-licensing-deep-research](v2-legal-licensing-deep-research.md) | 93 | **D** | 研究倫理・情報法 #31 | 法務・ライセンス |
| 09-01 | [llm-serving-deep-research](v2-llm-serving-deep-research.md) | 92 | **D** | 自然言語処理・機械学習 #27 / 計算機科学(並列・決定論) #28 | LLM サービング実務。艦隊設計の土台 |
| 09-01 | [observation-projection-deep-research](v2-observation-projection-deep-research.md) | 103 | **D** | 検証とV&V・UQ #22 | 観測射影 L-OBS/L-REC |
| 09-01 | [parallel-execution-deep-research](v2-parallel-execution-deep-research.md) | 91 | **D** | 計算機科学(並列・決定論) #28 | 並行実行の意味論 |
| 09-01 | [pattern-ledger-deep-research](v2-pattern-ledger-deep-research.md) | 112 | **D** | ABM方法論 #21 | パターン台帳の候補と運用。方法論ゲートの中身 |
| 09-01 | [persona-population-deep-research](v2-persona-population-deep-research.md) | 88 | **D** | 人格心理学 #13 / 人口学・合成人口論 #1 | ペルソナ・人口合成と個体差 |
| 09-01 | [precedent-system-deep-research](v2-precedent-system-deep-research.md) | 221 | **D** | 法学(業法・条例) #11 | GM裁定→判例結晶化。第3陣「制度の創発」の前身 |
| 09-02 | [person-perception-verification](v2-person-perception-verification.md) | 226 | **B** | 知覚心理学・精神物理学 #5 | 人物知覚4段階案の敵対的検証 |
| 09-02 | [ugc-platform-import](v2-ugc-platform-import.md) | 264 | **B** | ゲームエンジン工学・CG #30 / SFCマクロ経済学 #10 | UGC/大規模オンラインゲーム基盤の輸入。EVE 残差科目の出所 |
| 09-02 | [world-ledger-verification](v2-world-ledger-verification.md) | 353 | **B** | ABM方法論 #21 | 世界台帳 D-R2-2 改訂案の敵対的検証 |
| 09-03 | [area-boundary-map-reading](v2-area-boundary-map-reading.md) | 41 | **E** | 地理情報科学 #9 | 地図スクショからの境界読み取り(親の一次作業) |
| 09-03 | [kddi-attribute-shares-2024](v2-kddi-attribute-shares-2024.md) | 57 | **E** | 人口学・合成人口論 #1 | KDDI LA 属性構成(親が手元生データから再集計) |
| 09-04 | [cell-granularity-research](v2-cell-granularity-research.md) | 309 | **B** | 地理情報科学 #9 / 計算機科学(並列・決定論) #28 | 場所セルの粒度(prefix 共有単位) |
| 09-04 | [d1-reacquisition](v2-d1-reacquisition.md) | 348 | **B** | 人間移動科学 #3 | 時刻別同時滞在カーブの出典疑義と代替探索 |
| 09-04 | [hearing-numbers-and-d1-coverage](v2-hearing-numbers-and-d1-coverage.md) | 219 | **B** | 環境音響学 #6 | 会話可能距離の公開数表 / D1′ の bbox 被覆 |
| 09-04 | [vlm-reality-check-research](v2-vlm-reality-check-research.md) | 239 | **B** | 検証とV&V・UQ #22 | 街路画像+VLM によるシム都市の現実整合検証 |
| 09-07 | [implementation-stack-research](v2-implementation-stack-research.md) | 591 | **B** | ソフトウェア工学 #29 / 計算機科学(並列・決定論) #28 | 実装スタック(言語・ABM基盤・データ層・CI) |
| 09-07 | [run-manifest-concurrency-research](v2-run-manifest-concurrency-research.md) | 619 | **B** | ソフトウェア工学 #29 / 計算機科学(並列・決定論) #28 | run manifest 形式と並行実行の意味論 |
| 09-08 | [ethics-operations-research](v2-ethics-operations-research.md) | 62 | **B** | 研究倫理・情報法 #31 | 倫理・コンテンツ安全の運用規則 |
| 09-08 | [price-formation-llm-research](v2-price-formation-llm-research.md) | 57 | **B** | 小売科学・商業立地論 #17 / 行動経済学・マーケティング科学 #16 | 行5 価格形成。LLM 店主の値付け |
| 09-16 | [r2-llm-social-sim-fulltext-check](v2-r2-llm-social-sim-fulltext-check.md) | 110 | **B** | 計算社会科学 #25 / 検証とV&V・UQ #22 / 自然言語処理・機械学習 #27 / 統計学・因果推論 #23 / 計算機科学(並列・決定論) #28 | LLM 社会シミュ文献 12 件の本文実読の判定表(R-2)。lit 12 本の親。OASIS 超線形・事前登録の外部根拠・TRAILS-R の空白=D-75/D-70 の出所 |
| 09-16 | [r23-primary-check-batch1](v2-r23-primary-check-batch1.md) | 216 | **B** | 検証とV&V・UQ #22 / 計算社会科学 #25 / ABM方法論 #21 | 出典 URL ゼロの答申 33 本の一次確認 第1批(設計書が引く 8 本・28 主張)。D-74(値を直す 4 件)の出所・写し検査の提案(R-23) |
| 09-17 | [c10-initial-relations-research](v2-c10-initial-relations-research.md) | 533 | **B** | 社会ネットワーク科学 #14 / 認知科学(記憶・習慣) #12 / ABM方法論 #21 / 自然言語処理・機械学習 #27 | C10 着手前: 関係の強さは記憶の基底活性(ACT-R・d=0.5 は認知設計 §4 で既決)から導ける=Δ 5 個+半減期は消え、残るのは符号・検索閾値 τ(較正可)・エピソード粒度(Gilbert 2009 β 最終接触 −0.76/初回接触 0.755・Zhao 2012=ACT-R を辺にした唯一の先行)。3 値を LLM に書かせない(Qwen3-8B FR 46.22%)=符号は ResultCode から。ラン前ウォームアップの先行 0 本・世界内では会話率 0.0021/体/日で不可→ 機械的初期化を既定・強制ペアは 5,000 体で先に測る。齟齬 6(半減期 90 vs 30・3 人会話の口が無い ほか) |
| 09-17 | [micro-observation-research](v2-micro-observation-research.md) | 202 | **B** | 検証とV&V・UQ #22 / ABM方法論 #21 / ソフトウェア工学 #29 | ミクロ観察(個体カルテ/場所カルテ)の先行(R-4): GA の replay+無作為抽出・Concordia のログ粒度・Via の agent/facility クエリ・ODD の Observation・de Montjoye 1/10 乗則 → M1 アジェンダ O1〜O20(D-80) |
| 09-18 | [jev-system-one-note](v2-jev-system-one-note.md) | 96 | **A** | 自然言語処理・機械学習 #27 / ソフトウェア工学 #29 | Jev(TypeSafe System One)の親一次ノート(第238): 文字列を生成せず Choice(≤255)/Score(2〜10)/Noul の型付き確率判断を並列で返す・RLCD 非公開・数値はベンダー測定・一致率 67.8% は LLM 平均との一致・当てはめは行動語/行き先/起床。第242 訂正: 文脈長 64k/32k・レート 1,200 req/min は公開済み |
| 09-23 | [openjev-note](v2-openjev-note.md) | 86 | **A** | 自然言語処理・機械学習 #27 / ソフトウェア工学 #29 | Open-Jev と DiffusionGemma の親一次ノート(第253): 独立実装 razorback16/openjev(Apache-2.0・TypeSafe と無関係)は Google の拡散型 DiffusionGemma 26B-A4B(総 25.2B/活性 3.8B)に Jev と同じ noul/choice/score を被せたサーバー。v2 が第一候補にしない理由=精度の数値が無い(素の DiffusionGemma は自己回帰版より低い)・決定論の保証が無い(24GB 以上の要件は第254 で調達の事実に格下げ)。confidence は 1-H(p)/lnK の計算式で RLCD の較正ではない。Jev が拡散モデルである一次の証拠は無い |
|  | [destination-choice-llm-research](v2-destination-choice-llm-research.md) | 341 | **B** | 人間移動科学 #3 / 自然言語処理・機械学習 #27 / 計算社会科学 #25 / ABM方法論 #21 | R-37 行き先選択に LLM の思考(候補提示型 H): 先行の主流は逆向き(LLM が意図/カテゴリ・エンジンが POI)・唯一の直接比較 When Plausible は集計(STVD)で重力則が LLM 主導に勝ち個体(Δr・r_g)で LLM が勝つ=符号が逆・8B は候補の並べ替えで Acc@1 .52→.20・k=3〜5 に一次(2 to 5 / 3 to 5)・渋谷はセル内 POI 中央値 4(食事 2)=複数セル跨ぎ必須・候補行 28 tok・合否は D1′ でなく P-6/P-8・推奨=k 4・母集合 K-1∪近傍 8 セル・順序撹拌・番号ラベルなし・段階語・腕 A0〜A4。副産物: nightlife 259 件が飲食マスク外・v2-llm-mobility は D 等級 |

### P2(9 本)

| 日付 | 答申 | 行 | 一次確認 | 分野 | 役割 |
|---|---|---|---|---|---|
| 08-30 | [data-contract-research](v2-data-contract-research.md) | 88 | **D** | ソフトウェア工学 #29 | データ契約 |
| 08-31 | [capabilities-business-research](v2-capabilities-business-research.md) | 93 | **D** | 分野外(事業・資金) #0 | 獲得能力・産業応用・事業形態 |
| 08-31 | [impact-risk-research](v2-impact-risk-research.md) | 94 | **D** | 研究倫理・情報法 #31 | 影響とリスク・メタ安全保障 |
| 08-31 | [learned-simulation-research](v2-learned-simulation-research.md) | 98 | **D** | 自然言語処理・機械学習 #27 | 学習ベースシミュレーション路線 |
| 08-31 | [world-model-relation-research](v2-world-model-relation-research.md) | 91 | **D** | 計算社会科学 #25 | 世界モデル(Genie 等)との関係 |
| 09-01 | [content-safety-deep-research](v2-content-safety-deep-research.md) | 86 | **D** | 研究倫理・情報法 #31 | コンテンツ安全・モデレーション |
| 09-01 | [funding-deep-research](v2-funding-deep-research.md) | 103 | **D** | 分野外(事業・資金) #0 | 資金調達の実務 |
| 09-01 | [longrun-ops-deep-research](v2-longrun-ops-deep-research.md) | 88 | **D** | ソフトウェア工学 #29 | 長期運用 SRE・ストレージ・観測 I/O |
| 09-01 | [publication-ethics-deep-research](v2-publication-ethics-deep-research.md) | 80 | **D** | 研究倫理・情報法 #31 | 出版戦略と倫理審査 |

---

## 4. 使い方

- **新しい決定の根拠にする前に、その答申の等級を見る**。D なら使わない(その数値だけ一次確認してから使う)。
- 答申を読み直したら、その論文のメモを [lit/](lit/) へ 1 論文 1 ファイルで切り出す(v1 の `docs/lit/` 形式)。
- 空欄が見つかったら [research-backlog.md](research-backlog.md) へ写す(答申の中に埋めない)。
- ヘッダは `<!-- hdr:v1 -->` で機械可読。再生成は `python tools/research/build_index.py && python tools/research/gen_index.py`(二重挿入しない)。
- **この索引は自動生成物**。答申を足したら再生成する。手で編集しない。

## 5. まだやっていないこと(次のエージェントへ)

- **「効いた決定」の欄が無い**。どの答申がどの DECIDED 行の根拠かは、決定台帳 [v2-redesign.md](../design/v2-redesign.md) 側からしか辿れない。逆引き表は未作成。
- **C 等級 1 本**(ad-information)は空欄節が無いだけで、空欄が無い保証はない。読んで判定する。
- **D 等級 33 本の中身の真偽は未検証**。R-23 参照。
- 分野の紐づけは題名と対象決定からの親の判断。本文を読んで付け直す価値はある。
