# STATUS(索引)

- **今(2026-11-21・第348)**: [返事その 9](docs/design/prompt-2026-11-20-reply9.md)の作業が済んだ([報告 348](docs/ops/report-348-2026-11-21.md))。作業の枝を `main` に取り込み、版の固定・CI の 3 つの組・byte-check 20 構成(#179〜#181)、艦隊の口の直しと語彙の欠陥の直し(#182・#183=実 LLM の道だけが変わる小さな版上げ・mock は 20 構成 37 欄すべて同じ)が入った。仕様書は 469 項目。研究 4 本と親案 4 本を書いた。進め方は「いつでも回せる版」R1(仮決定)。
- **次の 1 手(セッションが切れてもここから再開)**: ユーザーの返事(返事その 10)を待つ。判断待ちは [PENDING](PENDING.md) §1-1 の〔第348〕の行と報告 348 §10。待つ間に進めてよいものは無い(改版は A07 の後・R1 の最小の核は題 8 の後・5070 は UAC と再起動の後)。枝は仕事ごとに短く切る(`main` から)。
- **判断待ち・実装待ち・研究の題**: [PENDING.md](PENDING.md)
- **完了実装**: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#183)
- **版上げの履歴とタグ・戻し方**: [docs/ops/version-history.md](docs/ops/version-history.md)
- **今のコードと、あるべき姿**: [リポの案内](docs/reference/repo-guide/README.md)・[仕様書 v0](docs/design/spec/README.md)・[差の一覧](docs/design/spec/gaps.md)・[食い違い](docs/design/spec/conflicts.md)
- **決定の原文**: 索引 [decision-id-index.md](docs/design/decision-id-index.md)・最新 [返事その 9](docs/design/prompt-2026-11-20-reply9.md)・v3 の設計書 [v3-core-design](docs/design/v3-core-design-2026-11-03.md)・理由の記録 [壁打ちの記録](docs/reference/wallbounce-record-2026-11-02_05.md)・実装の地図 [state-map](docs/reference/state-map-2026-11-20.md)
- **正典**: 決定台帳 [v2-redesign.md](docs/design/v2-redesign.md)・方法論 [v2-methodology.md](docs/design/v2-methodology.md)・用語集 [v2-glossary.md](docs/design/v2-glossary.md)
- **リサーチ**: 索引 [INDEX.md](docs/research/INDEX.md)・残務 [research-backlog.md](docs/research/research-backlog.md)・発注文の定型 [research-order-template.md](docs/research/research-order-template.md)
- **受入報告**: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7](docs/ops/build-report-C7.md)・[C8](docs/ops/build-report-C8.md)
- **開発ログ**: [devlog.md](docs/log/devlog.md)・[devlog-compressed.md](docs/log/devlog-compressed.md)
- **道具**: `tools/realworld_fetch/`(日次の現実データ・検証専用)・`tools/night5070/`(5070 の夜間ラン)・`tools/instruments/dm_eval/`(判断モデルの評価の器)・`tools/bytecheck/`(決定論の確かめ・版上げと整理の段で回す)・`requirements-lock.txt` と `tools/ci/`(版の固定と CI の組の確かめ)
- **ブランチ**: main は PR #10(7e5c446)まで(第348 の PR #11・#12 は報告 348 の追記)。仕事ごとの短い枝を `main` から切る。
- **最終更新**: 2026-11-21(第348)
