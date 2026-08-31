# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **1 / 10**
> v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 2026-09-01 第1 リポジトリ開設・v1からの移行

- U16決定(ユーザー: 「shibuya-simulation v2」→正規形 shibuya-simulation-v2)を受け移行実行。
- 持ち込み: 設計正典11本(docs/design/)・リサーチ答申33本(docs/research/)・データ約1.3GB(realworld/plateau/odpt/persona_pool_v2/calib/ground_truth=アンカー台帳registry.yaml/jinryu)・tools/scan_secrets.py(スクラッチパッド置きからリポ内正式配置へ)。
- 新設: CLAUDE.md(運用規律の明文化=メモリ依存の解消)・handover-memory.md(メモリ23本→16項の引き継ぎ)・data-license-ledger.md(法務答申の実装第一歩)・台帳3ファイル(STATUS/IMPLEMENTED/PENDING=未決U1-U15+W+運営判断を初期内容に)・.gitignore(data/runs/秘密を初日から除外)。
- 持ち込まない(意図的): git履歴・エンジンコード・テスト実体・runs出力・odpt_challenge(用途限定ライセンス)・juelich_ped(U15まで保留)。
- 次: ユーザーのA群一括回答(U13承認・W採否ほか)→D0としてパターン台帳選定→MVP 8日計画。
