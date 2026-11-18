# STATUS(索引)

- **今(2026-11-16・第347)**: 整理の段([11-16](docs/design/prompt-2026-11-16-reply8.md)=返事その 8)。段 4 の残り 4 段が入り、割らないファイルの移動は済んだ(#152・どの段も byte-check 19 構成 37 欄すべて同じ)。削除の段 その 1(#151)・走査の規則の直しと心の読みの一覧の試験(#153)・仕様書と設計書への 2-45〜2-69 の書き込みと仕様書の 10 問(#150)・研究 6 本と改版の文の案(#149)・数える・確かめると dm_eval の列(#148)・道具 3 本と CI の上限 120 分(#147)も着地。既定の final は `c8d68704` のまま。
- **次の 1 手(セッションが切れてもここから再開)**: 止めた切替口 3 本と Q7 は 5 段とも入った(#154・頭 `986773e`)。版上げ A48 も入った(#155・頭 `5bcd4ff`)。割る段 5a の道具の拡張 G0 も入った(#156・頭 `adbe8bb`・安定版のタグ `stable-v2-before-split5a-G1`)。5a の群 1 も入った(#157・頭 `bf0ccbb`・安定版のタグ `stable-v2-before-split5a-G2`)。5a の群 2 も入った(#159・頭 `6af6cf1`・安定版のタグ `stable-v2-before-split5a-G3`)。5a の群 3〜5 も入り、割る段 5a の 17 本が済んだ(#160・#161・頭 `b801a53`・安定版のタグ `stable-v2-before-split5b-G0`)。段 5b の G0 も入った(#162・頭 `4af887b`・安定版のタグ `stable-v2-before-split5b-G1`・src は変えていない)。5b の群 1(`engine/commit`・`engine/presence`・`engine/calendar_shadow`)も入った(#163・頭 `ce59591`・安定版のタグ `stable-v2-before-split5b-G2`)。5b の群 2(`engine/run`・入口の移し)も入った(#164・頭 `b0afefd`・安定版のタグ `stable-v2-before-split5b-G3`)。5b の群 3(`cli`・転送)も入り、段 5b の 5 本が済んだ(#165・頭 `a6469a2`・安定版のタグ `stable-v2-before-split6-A`)。段 6 の S6-A も入った(#166・頭 `102bfe5`・安定版のタグ `stable-v2-before-split6-G0`)。次は、段 6 の S6-G0(道具の拡張は作業木 `work/split6-g0-347`・割る前の試験の直しは `work/split5a-347`)→ S6-G1(作業木 `work/split5a-347`・実装役が byte-check → 親の byte-check と範囲の試験と別の役の検収 → commit)→ 段 7。段 6・7 の計画と親の裁定の控えは、リポの `scratch/r8_plans_347/`(gitignore 下)。版上げ Q13 も入った(#158・頭 `9626f65`・安定版のタグ `stable-v2-before-library-defaults-q13`)。その後は 6 → 7。M10 の ① は返事待ち(細部 5 点)。改版は返事その 9 の後。判断待ちは PENDING §1-1 の〔第347〕の行。機械は第347 の間は止まっていない(木の写しと範囲の試験を束ねない運用を続ける)。
- **判断待ち・実装待ち・研究の題**: [PENDING.md](PENDING.md)
- **完了実装**: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#166)
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
