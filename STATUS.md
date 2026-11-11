# STATUS(索引)

- **今(2026-11-11・第346)**: 整理の段([11-09](docs/design/prompt-2026-11-09-reply7.md) §2〜§4)。段 2 の突き合わせの直し・CLAUDE.md の書き換え(§1 第一目標・§3 背骨)・食い違いの決着・byte-check の道具(37 欄)・旧道の切替口 5 本と死んだ道 2 本の削除(止めた 3 本は判断待ち)・棚卸しの表・docs の索引・最終の全ファイルの表・コードの区分の移動の段 1・段 2(固定の表・名前の凍結・道筋の下ごしらえ=#143・ファイルはまだ動かしていない)と、段 3 の移す道具 `tools/pkgmove/`・段 4 の下ごしらえ(#144・5c2e06c・親の byte-check 19/19 同じ)まで着地。段 4 は foundation から validation までの 9 段(道具の数えで 171 本・#145・#146・どの段も byte-check 19/19 同じ)が本体に入った。
- **次の 1 手(セッションが切れてもここから再開)**: ユーザーの答え待ち=delete の段(棚卸しの表の確認 1)・`interim_bundles` の段と保留の 7 行(区分の表の問い)。答えの後は 1 段ずつ(linked の作業木に `move --apply` → `contracts --stage <段> --apply` → import の確かめ → byte-check → 範囲の試験 → commit → タグ → CI)。`interim_bundles` の段と保留の 7 行はユーザーの答えの後。第346 の報告は 11-11 に出した(判断 13 件は答え待ち)。**機械が 2 回、作業の途中で止まって再起動した**(11-10 07:01・11-11 00:33=devlog 第346)ので、再開のときは書きかけのファイルが 0 で埋まっていないかを先に見る。PLATEAU は 11/14 に一度止まって報告。5070 の WSL はユーザーの UAC の後。
- **判断待ち・実装待ち・研究の題**: [PENDING.md](PENDING.md)
- **完了実装**: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#146)
- **版上げの履歴とタグ・戻し方**: [docs/ops/version-history.md](docs/ops/version-history.md)
- **今のコードと、あるべき姿**: [リポの案内](docs/reference/repo-guide/README.md)・[仕様書 v0](docs/design/spec/README.md)・[差の一覧](docs/design/spec/gaps.md)・[食い違い](docs/design/spec/conflicts.md)
- **決定の原文**: 索引 [decision-id-index.md](docs/design/decision-id-index.md)・最新 [返事その 7](docs/design/prompt-2026-11-09-reply7.md)・v3 の設計書 [v3-core-design](docs/design/v3-core-design-2026-11-03.md)・理由の記録 [壁打ちの記録](docs/reference/wallbounce-record-2026-11-02_05.md)
- **正典**: 決定台帳 [v2-redesign.md](docs/design/v2-redesign.md)・方法論 [v2-methodology.md](docs/design/v2-methodology.md)・用語集 [v2-glossary.md](docs/design/v2-glossary.md)
- **リサーチ**: 索引 [INDEX.md](docs/research/INDEX.md)・残務 [research-backlog.md](docs/research/research-backlog.md)・発注文の定型 [research-order-template.md](docs/research/research-order-template.md)
- **受入報告**: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7](docs/ops/build-report-C7.md)・[C8](docs/ops/build-report-C8.md)
- **開発ログ**: [devlog.md](docs/log/devlog.md)・[devlog-compressed.md](docs/log/devlog-compressed.md)
- **道具**: `tools/realworld_fetch/`(日次の現実データ・検証専用)・`tools/night5070/`(5070 の夜間ラン)・`tools/instruments/dm_eval/`(判断モデルの評価の器)・`tools/bytecheck/`(決定論の確かめ・版上げと整理の段で回す)
- **ブランチ**: main は PR #8(bad7577)まで。作業ブランチは `build/spatial-d102-prep`。
- **最終更新**: 2026-11-11(第346)
