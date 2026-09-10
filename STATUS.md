# STATUS(索引)

- 現在地: **構築工程 C0〜C6 完了。C7 本番ラン(c7-day-2・390,067 体×1 日・9h10m・呼 3,900,670)は完走したが受入で停止句 (a)(T2-c テープ再生が繰り延べを復元できない=D-58)→ユーザー決定「再ラン」。再ラン前の修正 7 件(D-55/58/53/51/56/61/62)は実装・層2 条件付き合格まで済み([IMPLEMENTED #17](IMPLEMENTED.md))。**その後の再検証で根本 D-66(域外居住 346,445 体が W16 で実装されず域内で就寝・C7 の 5 エリア昼夜比 1.22 vs 現実 14.8)を発見。ユーザー決定 (a)=W16/W17 の実行に置換・実装は保留中(合図待ち)**。決定アジェンダ [docs/design/v2-d66-outside-residents-agenda.md](docs/design/v2-d66-outside-residents-agenda.md)・現実側答申 [docs/research/v2-d66-outside-residents-research.md](docs/research/v2-d66-outside-residents-research.md)(親一次確認済)。C8 は基盤+切替口+実 LLM 腕 ⑥①(seed 2 複製済)まで。c7-day-3 は D-66 の後(サーバー同期 → `--fleet-queue-capacity 4096`)。
- 進捗の目安: **v2 初版(C0〜C8 完走)= 約 70%** / 第一目標「世界そのものがプロダクト」= 約 3 割(第126 の見積り。D-66/D-67 で夜間・昼間の在圏水準が現実から遠いことが判明したため、第一目標側は据え置き)
- 判断待ち(ユーザー): D-67(昼間在圏 1.6〜1.9 倍・推奨 (b)+(a))・D-59/D-60/D-49・VLA リサーチの方向・PT2018 c-2/b-4 のブラウザ取得
- 完了実装: [IMPLEMENTED.md](IMPLEMENTED.md)
- 未実装・判断待ち: [PENDING.md](PENDING.md)
- 受入報告: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7(停止句 (a)・再ラン待ち)](docs/ops/build-report-C7.md)・[C8(進行中)](docs/ops/build-report-C8.md)
- 開発ログ: [docs/log/devlog.md](docs/log/devlog.md)(第131〜140 は [devlog-compressed.md](docs/log/devlog-compressed.md))
- ブランチ: `build/c5-c8`(第140 d95142c まで push 済み・PR #2 は main へ未マージ=ユーザー判断)
- 最終更新: 2026-09-10(第141 台帳の掃除パス)
