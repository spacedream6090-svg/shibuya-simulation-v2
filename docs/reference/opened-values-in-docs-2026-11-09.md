# 開封の値が普通の文書にある件の一覧(名前と行番号だけ)

> 2026-11-09・第346・[返事その 7](../design/prompt-2026-11-09-reply7.md) §6-3 の 2(第345 の判断 4)。**値は写さない。** 親が作った。**移す作業は ⑥ 検証の封の壁打ちの後に決める**(封印の層に触る作業なので、先に聞く決まり)。それまで、文書を読む役への発注文には「これらの文書は開かない」の 1 行を入れる([発注文の定型](../research/research-order-template.md))。

## 0. 作り方

- 第345 で読み手が見つけた 5 本の行は、数字を「#」に伏せた形で 1 行ずつ見て、どの層の値かの名前だけを確かめた。値そのものは見ていない。
- 全体の拾いは機械で行った。追跡している `*.md` と `*.json`(data/ とカードを除く)から、層の名前(`kddi_la`・`KDDI`・`shibuya_jinryu`・`boundary_counts`・`D1b`・`D1′`・`D4′`・`D5′`・`K5`・`AD1`)と数値の形(小数・百分率・桁区切り・pp)が同じ行に並ぶ所を数えた。結果は 129 本・363 行。**数値が値なのか日付や件数なのかは、伏せた形では区別できない**。だから下の候補には、値でない行も多く入っている。
- 「holdout」は答申の中で一般の語として多く出るので、拾いの語から外した。

## 1. 状態の決め方(層ごと)

| 層 | 状態 | 根拠 |
|---|---|---|
| `kddi_la`・KDDI の 5 エリア | 使用済み(9 月の C7 で開封・判定に使った) | パターン台帳 §10-1 の注「開封済み `kddi_la`」・IMPLEMENTED の 9 月の開封の行 |
| D1′(2018〜2024) | 使用済み(C7 で開封) | [食い違いの一覧](../design/spec/conflicts.md) の古い写しの表(パターン台帳 §2 の候補 ②) |
| D4′ | 使用済み(照合・開封済み) | 10-06 SR4 の問い 1 |
| D5′ | 使用済み(検証+burned) | 11-02r §1 #6 |
| AD1(封印行 S3) | 使用済み | パターン台帳 §2 の改訂 |
| 封印行 S1・S2 | 未開封・起草時に一度目視済み | パターン台帳 §2 の運用の文(値は台帳の本文にある) |
| D1b | 未開封(test の層)。前の窓の一部だけ目視済み | 門 1 の計画の「目視の宣言」 |
| K5 | 未開封(test) | パターン台帳 §10-1 |
| `shibuya_jinryu`・`boundary_counts` | 未開封(封印)。ただし独立でない(照合用) | 回答 10-13b の記録 |
| パターン台帳 §10-1 の検証専用の錨 | 目視済み(研究と公的統計の値が台帳に平文) | パターン台帳 §10-1 |

## 2. 第345 で見つかった 5 本

| 文書 | 行 | 何の値か(名前) | 状態 |
|---|---|---|---|
| `IMPLEMENTED.md` | 45 | 9 月の holdout の開封の結果(C7 の主張の腕と比べる腕の判定の値) | 使用済み |
| `docs/ops/build-report-C7.md` | 130 | 39 万体の mock 3 腕の 5 エリアの在圏と「現実」「PT」の値 | 使用済み(「現実」が KDDI かは要確認。KDDI なら開封済みの層) |
| `docs/ops/build-report-C8.md` | 21 | 看板 ablation の結果と AD1(S3)の線 | 使用済み |
| `docs/design/v2-g1-backtest-plan-2026-11-02.md` | 21 | D1b の前の窓のコアの昼と深夜の比(v1 の答申にある値) | 目視済み(計画の目視の宣言のとおり) |
| `docs/design/v2-pattern-ledger.md` | §2 の 119〜121 行(S1・S2・S3)・§10-1(224〜248 行) | 封印行の値と検証専用の錨の値 | S1・S2=未開封・起草時に目視済み/S3=使用済み/§10-1=目視済み |

## 3. 未開封の層の名前が数値と同じ行に出る所(要確認・35 本)

⑥ の壁打ちの後に、1 行ずつ値か日付・件数かを確かめる。**ここに挙げた行に未開封の値があれば、封印の層へ移す候補の最優先**(仕分けの案 4 の ②)。

| 文書 | 層 | 行 |
|---|---|---|
| CLAUDE.md | D1b | 81 |
| IMPLEMENTED.md | D1b | 16 |
| docs/bench/analysis/wallbounce-0930/conflicts-raw.md | boundary_counts・shibuya_jinryu | 84 |
| docs/bench/analysis/wallbounce-1012/seal_tidy/README.md | boundary_counts | 108,176 |
| docs/bench/c7/prereg_arms_v1.md | boundary_counts・shibuya_jinryu | 95 |
| docs/data-license-ledger.md | D1b・K5・shibuya_jinryu | 19,93,373 |
| docs/design/spec/conflicts.md | D1b・K5 | 121 |
| docs/design/v2-energy-classical-implementation-agenda.md | K5 | 10,16 |
| docs/design/v2-g1-backtest-plan-2026-11-02.md | D1b | 3 |
| docs/design/v2-pattern-ledger.md | D1b | 163,165,182 |
| docs/design/v2-presence-shape-implementation-agenda.md | shibuya_jinryu | 28 |
| docs/design/v2-redesign.md | D1b | 522 |
| docs/design/v2-run-day-decomposition-draft.md | K5 | 144 |
| docs/design/v2-spatial-physics-layer-draft.md | boundary_counts・shibuya_jinryu | 112 |
| docs/log/devlog-compressed.md | D1b・K5・boundary_counts・shibuya_jinryu | 93,507,509,521 |
| docs/log/devlog.md | D1b | 12,46 |
| docs/log/pending-archive-2026-09-28.md | K5・boundary_counts・shibuya_jinryu | 12,130,153 |
| docs/log/pending-archive-2026-10-25.md | boundary_counts・shibuya_jinryu | 91 |
| docs/reference/a1-research-2026-10-31.md | K5 | 135 |
| docs/reference/v1/IMPLEMENTED.md | D1b・K5・boundary_counts | 398,401,405,416 |
| docs/research/INDEX.md | D1b | 205,267 |
| docs/research/v2-d1-reacquisition.md | D1b | 68,77,106 |
| docs/research/v2-r109-population-size-rebuild-materials.md | K5 | 305 |
| docs/research/v2-r114-f12-k5-availability.md | shibuya_jinryu | 8 |
| docs/research/v2-r115-calibration-anchors-inventory-for-2-0.md | D1b・K5・boundary_counts・shibuya_jinryu | 8,134 |
| docs/research/v2-r120-tenjin-and-national-stage0-materials.md | D1b | 78 |
| docs/research/v2-r121-four-layer-separation-survey.md | shibuya_jinryu | 78 |
| docs/research/v2-r122-d1b-inventory-and-g1-backtest-plan.md | D1b・K5・boundary_counts・shibuya_jinryu | 8,10,121,151 |
| docs/research/v2-r129-forecast-target-candidates.md | D1b・boundary_counts | 8,35,36,37,38,40 |
| docs/research/v2-r130-core-timing-and-event-counts.md | boundary_counts | 9 |
| docs/research/v2-r137-human-daily-planning-forms.md | boundary_counts | 8 |
| docs/research/v2-r65-vertical-validation-data.md | boundary_counts・shibuya_jinryu | 8 |
| docs/reviews/triage-2026-10-13/A.md | K5 | 77 |
| docs/reviews/triage-2026-10-13/C.md | boundary_counts・shibuya_jinryu | 13,54,85,118,119 |
| docs/reviews/triage-2026-10-13/README.md | shibuya_jinryu | 32 |

## 4. 全体の拾い(129 本・363 行)

| 文書 | 層 | 行の数 | 行 |
|---|---|---:|---|
| CLAUDE.md | D1b | 1 | 81 |
| IMPLEMENTED.md | AD1・D1b・D1′・D4′・D5′・KDDI | 10 | 16,17,33,47,291,295,300,302,330,429 |
| README.md | KDDI | 1 | 36 |
| docs/bench/analysis/notable-events-2026-09-24/README.md | KDDI | 5 | 23,80,81,113,121 |
| docs/bench/analysis/notable-events-2026-09-24/sub_e_presence_shape.md | KDDI | 16 | 17,18,20,44,47,60,88,104,119,120,124,128,170,171,184,185 |
| docs/bench/analysis/presence-shape-2026-09-29/README.md | KDDI | 9 | 4,87,111,243,245,270,277,278,329 |
| docs/bench/analysis/presence-shape-2026-09-29/attr_arms.json | KDDI | 1 | 9 |
| docs/bench/analysis/s2-rates-1101/README.md | D1′・D4′ | 1 | 164 |
| docs/bench/analysis/small-fixes-2026-09-29/README.md | D1′・D4′ | 1 | 334 |
| docs/bench/analysis/small-fixes-2026-09-29/r23_batch3_changes.json | D1′・D4′ | 1 | 45 |
| docs/bench/analysis/wallbounce-0930/conflicts-raw.md | KDDI・boundary_counts・shibuya_jinryu | 2 | 31,84 |
| docs/bench/analysis/wallbounce-1012/ca31/gauge/2026-10-15_ca31/anchor_gauge.md | KDDI | 2 | 45,117 |
| docs/bench/analysis/wallbounce-1012/gauge20/README.md | KDDI | 1 | 163 |
| docs/bench/analysis/wallbounce-1012/seal_tidy/README.md | boundary_counts・kddi_la | 3 | 106,108,176 |
| docs/bench/analysis/wallbounce-1012/seal_tidy/review.md | kddi_la | 1 | 85 |
| docs/bench/c7/ensemble/c7-day-4_seed1_vs_seed2.md | KDDI | 1 | 45 |
| docs/bench/c7/prereg_arms_v1.md | KDDI・boundary_counts・shibuya_jinryu | 3 | 26,95,107 |
| docs/bench/c8/ablation/ab6b_s1_parent_report.md | AD1 | 3 | 6,15,29 |
| docs/bench/c8/ablation/ab6b_s2_parent_report.md | AD1 | 2 | 15,22 |
| docs/bench/c8/ablation/ab6c_s1_parent_report.md | AD1 | 2 | 46,63 |
| docs/bench/c8/ablation/ab8_s1_parent_report.md | AD1 | 1 | 55 |
| docs/bench/c8/ablation/ablation_AB6b-AD-NOTICE_s1.json | AD1 | 1 | 5 |
| docs/bench/c8/ablation/ablation_AB6b-AD-NOTICE_s1.md | AD1 | 1 | 3 |
| docs/bench/c8/ablation/ablation_AB6b-AD-NOTICE_s2.json | AD1 | 1 | 5 |
| docs/bench/c8/ablation/ablation_AB6b-AD-NOTICE_s2.md | AD1 | 1 | 3 |
| docs/bench/c8/sensitivity_v1.json | D1′ | 1 | 105 |
| docs/bench/figures/README.md | AD1・KDDI | 4 | 191,213,257,264 |
| docs/bench/figures/tbl_ablation.json | AD1 | 1 | 255 |
| docs/bench/figures/tbl_ablation.md | AD1 | 1 | 40 |
| docs/bench/instruments/anchor_gauge/2026-10-14_2bc7a4b/anchor_gauge.md | KDDI | 2 | 45,115 |
| docs/bench/instruments/anchor_gauge/2026-10-14_vb24-V1/anchor_gauge.md | KDDI | 2 | 45,115 |
| docs/bench/instruments/anchor_gauge/2026-10-14_vb24-V6/anchor_gauge.md | KDDI | 2 | 45,115 |
| docs/bench/instruments/anchor_gauge/2026-10-18_pop43-w16/anchor_gauge.md | KDDI | 2 | 47,119 |
| docs/bench/instruments/anchor_gauge/2026-10-19_pop43-w21/anchor_gauge.md | KDDI | 2 | 47,119 |
| docs/bench/instruments/anchor_gauge/preregistration_v1_4_draft.md | KDDI | 1 | 77 |
| docs/bench/quality_probe_v0/README.md | D1′・D4′・KDDI | 3 | 219,220,222 |
| docs/data-license-ledger.md | D1b・K5・KDDI・kddi_la・shibuya_jinryu | 3 | 19,93,373 |
| docs/design/bridging-ledger.json | D5′ | 1 | 9983 |
| docs/design/spec/02-world.md | D5′ | 1 | 290 |
| docs/design/spec/07-validation.md | D1′・D4′ | 1 | 42 |
| docs/design/spec/conflicts.md | D1b・K5 | 1 | 121 |
| docs/design/v2-architecture-overview-detailed.md | AD1・KDDI | 2 | 420,462 |
| docs/design/v2-architecture-overview-simple.md | KDDI | 1 | 109 |
| docs/design/v2-boundary-economy-design.md | KDDI | 1 | 29 |
| docs/design/v2-c10-relations-agenda.md | KDDI | 1 | 31 |
| docs/design/v2-c10-relations-brief.md | AD1・KDDI | 4 | 66,143,203,208 |
| docs/design/v2-c9-geometry-brief.md | AD1・KDDI | 5 | 123,163,242,324,328 |
| docs/design/v2-cell-dependency-inventory.md | KDDI | 1 | 85 |
| docs/design/v2-decision-brief-2026-09-19.md | AD1 | 1 | 32 |
| docs/design/v2-decision-evidence-map.md | D1′ | 1 | 96 |
| docs/design/v2-decisions-for-user-2026-09-29.md | KDDI | 3 | 11,74,105 |
| docs/design/v2-energy-classical-implementation-agenda.md | K5 | 2 | 10,16 |
| docs/design/v2-g1-backtest-plan-2026-11-02.md | D1b | 1 | 3 |
| docs/design/v2-implementation-plan.md | D1′・KDDI | 9 | 576,578,582,583,584,588,589,596,599 |
| docs/design/v2-inventory-and-bottlenecks.md | KDDI | 1 | 34 |
| docs/design/v2-memory-agenda.md | AD1 | 1 | 34 |
| docs/design/v2-memory-brief.md | KDDI | 1 | 432 |
| docs/design/v2-pattern-ledger.md | AD1・D1b・D1′・D4′・KDDI・kddi_la | 16 | 5,69,73,121,125,126,129,139,163,164,165,168,176,180,181,182 |
| docs/design/v2-presence-shape-implementation-agenda.md | KDDI・shibuya_jinryu | 5 | 3,4,11,19,28 |
| docs/design/v2-redesign.md | D1b・D1′・D4′・D5′・KDDI | 9 | 500,518,522,524,525,538,542,546,552 |
| docs/design/v2-requirements-revision-log.md | KDDI | 1 | 328 |
| docs/design/v2-research-request-2026-10-06.md | KDDI | 1 | 50 |
| docs/design/v2-run-day-decomposition-draft.md | K5 | 1 | 144 |
| docs/design/v2-schedule-and-research-plan-2026-09.md | KDDI | 1 | 183 |
| docs/design/v2-spatial-physics-layer-draft.md | KDDI・boundary_counts・shibuya_jinryu | 1 | 112 |
| docs/design/v2-viewer-design-round-draft.md | D1′・D4′ | 1 | 142 |
| docs/design/v2-wallbounce-0930-reflection.md | KDDI | 1 | 31 |
| docs/design/v2-wallbounce-decisions-2026-10-06.md | KDDI | 1 | 239 |
| docs/design/v2-world-data-build-spec.md | KDDI | 2 | 166,191 |
| docs/log/devlog-compressed.md | AD1・D1b・D1′・D4′・K5・KDDI・boundary_counts・kddi_la・shibuya_jinryu | 19 | 23,31,83,93,101,105,115,149,151,245,332,360,372,375,457,459,507,509,521 |
| docs/log/devlog.md | D1b | 2 | 12,46 |
| docs/log/pending-archive-2026-09-28.md | AD1・D1′・K5・KDDI・boundary_counts・shibuya_jinryu | 11 | 12,97,110,115,128,130,151,153,169,171,182 |
| docs/log/pending-archive-2026-10-25.md | boundary_counts・kddi_la・shibuya_jinryu | 1 | 91 |
| docs/ops/build-report-C7.md | KDDI | 1 | 24 |
| docs/ops/build-report-C8.md | AD1 | 2 | 21,60 |
| docs/ops/discord_report_2026-09-26.md | KDDI | 1 | 18 |
| docs/ops/discord_report_holdout_2026-09-17.md | D1′ | 1 | 3 |
| docs/ops/goal_c5_c8.md | KDDI | 1 | 9 |
| docs/reference/2026-10-25_shibuya_world_model_and_strategy_summary.md | KDDI | 1 | 56 |
| docs/reference/a1-research-2026-10-31.md | K5 | 1 | 135 |
| docs/reference/decision-routing-2026-11-01.md | D5′ | 1 | 184 |
| docs/reference/v1/IMPLEMENTED.md | D1b・K5・boundary_counts | 4 | 398,401,405,416 |
| docs/research/INDEX.md | D1b・D1′・KDDI | 4 | 205,215,232,267 |
| docs/research/lit/README.md | D1′ | 1 | 175 |
| docs/research/research-backlog.md | KDDI | 1 | 190 |
| docs/research/v2-ad-information-research.md | AD1・D4′ | 2 | 421,445 |
| docs/research/v2-boundary-economy-u10-u11-research.md | KDDI | 2 | 355,375 |
| docs/research/v2-catalog-llm-social-sim-people-orgs-2026-10-13.md | KDDI | 2 | 263,2354 |
| docs/research/v2-d1-reacquisition.md | D1b・D1′・D4′・KDDI | 21 | 16,30,31,32,39,47,49,66,68,74,75,77,79,84,106,240,243,248,303,304,305 |
| docs/research/v2-destination-choice-llm-research.md | D1′ | 1 | 329 |
| docs/research/v2-digital-twin-landscape-research.md | KDDI | 1 | 46 |
| docs/research/v2-hearing-numbers-and-d1-coverage.md | KDDI | 1 | 128 |
| docs/research/v2-micro-observation-research.md | KDDI | 2 | 98,116 |
| docs/research/v2-perception-timing-research.md | D1′ | 1 | 523 |
| docs/research/v2-person-perception-verification.md | D4′ | 2 | 172,184 |
| docs/research/v2-population-synthesis-research.md | D1′・D4′・KDDI・kddi_la | 15 | 10,27,28,30,180,181,182,184,250,251,344,394,413,489,494 |
| docs/research/v2-r109-population-size-rebuild-materials.md | K5・KDDI | 2 | 11,305 |
| docs/research/v2-r114-f12-k5-availability.md | KDDI・shibuya_jinryu | 3 | 8,28,93 |
| docs/research/v2-r115-calibration-anchors-inventory-for-2-0.md | D1b・K5・KDDI・boundary_counts・kddi_la・shibuya_jinryu | 4 | 8,10,95,134 |
| docs/research/v2-r120-tenjin-and-national-stage0-materials.md | D1b・KDDI | 2 | 78,127 |
| docs/research/v2-r121-four-layer-separation-survey.md | KDDI・shibuya_jinryu | 1 | 78 |
| docs/research/v2-r122-d1b-inventory-and-g1-backtest-plan.md | D1b・K5・boundary_counts・kddi_la・shibuya_jinryu | 4 | 8,10,121,151 |
| docs/research/v2-r129-forecast-target-candidates.md | D1b・KDDI・boundary_counts・kddi_la | 6 | 8,35,36,37,38,40 |
| docs/research/v2-r130-core-timing-and-event-counts.md | boundary_counts・kddi_la | 1 | 9 |
| docs/research/v2-r137-human-daily-planning-forms.md | boundary_counts・kddi_la | 1 | 8 |
| docs/research/v2-r23-primary-check-batch1.md | D1′・D4′ | 1 | 165 |
| docs/research/v2-r23-primary-check-batch3.md | D1′・D4′ | 6 | 55,153,191,215,261,341 |
| docs/research/v2-r42-social-methodology-precedents.md | KDDI | 1 | 223 |
| docs/research/v2-r51-mere-exposure-incidental-ads-research.md | AD1 | 2 | 115,178 |
| docs/research/v2-r52-crowd-model-calibration-shibuya-research.md | KDDI | 2 | 155,170 |
| docs/research/v2-r56-kddi-attribute-definition-check.md | KDDI | 1 | 25 |
| docs/research/v2-r57-pt2018-availability.md | KDDI | 1 | 133 |
| docs/research/v2-r65-vertical-validation-data.md | KDDI・boundary_counts・shibuya_jinryu | 2 | 8,114 |
| docs/research/v2-r70-gpu-procurement.md | KDDI | 2 | 148,225 |
| docs/research/v2-r92-free-and-application-data-sources.md | KDDI | 1 | 201 |
| docs/research/v2-research-reflection-audit-p1p2.md | D1′・D4′・KDDI | 4 | 126,332,398,426 |
| docs/research/v2-research-reflection-audit.md | D4′・KDDI | 2 | 130,189 |
| docs/research/v2-statistics-causal-research.md | KDDI | 2 | 21,234 |
| docs/research/v2-turing-test-validation-research.md | D4′・KDDI | 4 | 144,337,354,393 |
| docs/research/v2-world-coverage-index-research.md | D4′ | 1 | 208 |
| docs/research/v2-world-data-build-research.md | KDDI | 3 | 285,300,436 |
| docs/research/v2-world-process-inventory-research.md | D1′・D4′ | 1 | 31 |
| docs/reviews/external-review-2026-10-13.md | KDDI | 3 | 129,140,157 |
| docs/reviews/triage-2026-10-13/A.md | K5 | 1 | 77 |
| docs/reviews/triage-2026-10-13/C.md | KDDI・boundary_counts・kddi_la・shibuya_jinryu | 10 | 13,49,54,61,85,94,106,118,119,172 |
| docs/reviews/triage-2026-10-13/README.md | KDDI・shibuya_jinryu | 4 | 32,44,89,119 |
| tools/c8/ablations_v1.json | AD1 | 5 | 536,537,594,668,726 |
| tools/c8/sensitivity_v1.json | D1′ | 1 | 105 |
| tools/quality_probe_v0/README.md | D1′・D4′・KDDI | 3 | 220,221,223 |

## 5. 次にすること

1. ⑥ 検証の封の壁打ちで、移すか・印を付けて残すかを決める(仕分けの案 4 の ①〜⑤)。
2. 過去の commit に未開封の値があれば、報告だけにする(履歴の書き換えはユーザーの判断)。本書の作業では履歴を調べていない。
