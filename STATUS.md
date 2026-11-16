# STATUS(索引)

- **今(2026-11-16・第347)**: 整理の段([11-16](docs/design/prompt-2026-11-16-reply8.md)=返事その 8)。段 4 の残り 4 段が入り、割らないファイルの移動は済んだ(#152・どの段も byte-check 19 構成 37 欄すべて同じ)。削除の段 その 1(#151)・走査の規則の直しと心の読みの一覧の試験(#153)・仕様書と設計書への 2-45〜2-69 の書き込みと仕様書の 10 問(#150)・研究 6 本と改版の文の案(#149)・数える・確かめると dm_eval の列(#148)・道具 3 本と CI の上限 120 分(#147)も着地。既定の final は `c8d68704` のまま。
- **次の 1 手(セッションが切れてもここから再開)**: 止めた切替口 3 本と Q7(実装中。試験の書き直し → `--economy-stage2 off` → 率の規則と「無い」の過程 → `--space` → `--hunger-model` の旗。段ごとに byte-check → 範囲の試験 → commit → CI)→ 段 5a(語彙・型・定数を下ろす割り)→ 5b → 6 → 7。版上げ(A48・Q13・M10 の ①)は段の合間に 1 つずつ。改版は返事その 9 の後。判断待ちは PENDING §1-1 の〔第347〕の行。機械は第347 の間は止まっていない(木の写しと範囲の試験を束ねない運用を続ける)。
- **判断待ち・実装待ち・研究の題**: [PENDING.md](PENDING.md)
- **完了実装**: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#153)
- **版上げの履歴とタグ・戻し方**: [docs/ops/version-history.md](docs/ops/version-history.md)
- **今のコードと、あるべき姿**: [リポの案内](docs/reference/repo-guide/README.md)・[仕様書 v0](docs/design/spec/README.md)・[差の一覧](docs/design/spec/gaps.md)・[食い違い](docs/design/spec/conflicts.md)
- **決定の原文**: 索引 [decision-id-index.md](docs/design/decision-id-index.md)・最新 [返事その 8](docs/design/prompt-2026-11-16-reply8.md)・v3 の設計書 [v3-core-design](docs/design/v3-core-design-2026-11-03.md)・理由の記録 [壁打ちの記録](docs/reference/wallbounce-record-2026-11-02_05.md)
- **正典**: 決定台帳 [v2-redesign.md](docs/design/v2-redesign.md)・方法論 [v2-methodology.md](docs/design/v2-methodology.md)・用語集 [v2-glossary.md](docs/design/v2-glossary.md)
- **リサーチ**: 索引 [INDEX.md](docs/research/INDEX.md)・残務 [research-backlog.md](docs/research/research-backlog.md)・発注文の定型 [research-order-template.md](docs/research/research-order-template.md)
- **受入報告**: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7](docs/ops/build-report-C7.md)・[C8](docs/ops/build-report-C8.md)
- **開発ログ**: [devlog.md](docs/log/devlog.md)・[devlog-compressed.md](docs/log/devlog-compressed.md)
- **道具**: `tools/realworld_fetch/`(日次の現実データ・検証専用)・`tools/night5070/`(5070 の夜間ラン)・`tools/instruments/dm_eval/`(判断モデルの評価の器)・`tools/bytecheck/`(決定論の確かめ・版上げと整理の段で回す)
- **ブランチ**: main は PR #8(bad7577)まで。作業ブランチは `build/spatial-d102-prep`。
- **最終更新**: 2026-11-16(第347)
