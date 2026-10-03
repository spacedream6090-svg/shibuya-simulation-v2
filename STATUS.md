# STATUS(索引)

- **現在地(2026-10-03・第315)**: 構築工程 C0〜C8 は一巡(39 万体×1 日の実 LLM ラン c7-day-4 を 3 seed・holdout 開封=0/4 NOT PASS)。第281〜320 で GPU 不要の実装 #49〜#81(全体テスト 3,544 件)。**2026-10-03 にユーザーの指示書が届き、09-30 の判断待ちの全項が決まった**([指示書 10-03](docs/design/v2-wallbounce-decisions-2026-10-03.md)・[要件の改訂記録](docs/design/v2-requirements-revision-log.md))。順番は 文書の整理 → 日次データ(済)→ リサーチ第 1 群 → D-102 の土台 10a〜10f → 11a・11c → 賃金 → 10g → 設計ラウンド → 空間の段 0〜6 → 記憶。**実 LLM の手段なし(09-22〜)**。
- 進捗の目安: v2 初版(C0〜C8)≈ 70% / 第一目標「世界そのものがプロダクト」≈ 3 割(第126 の見積り・据え置き)。
- **いま・判断待ち・実装待ち・最近の実装・予定**: [PENDING.md](PENDING.md)(第279 に簡潔な形へ組み直し。旧全文は [pending-archive-2026-09-28.md](docs/log/pending-archive-2026-09-28.md))
- 完了実装: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#81)・運用の道具: `tools/realworld_fetch/`(日次の現実データ・検証専用)
- 正典: 決定台帳 [v2-redesign.md](docs/design/v2-redesign.md)・方法論 [v2-methodology.md](docs/design/v2-methodology.md)・用語集 [v2-glossary.md](docs/design/v2-glossary.md)
- 判断待ち: K1〜K18(短い確認)=[PENDING §1-1](PENDING.md)。保留の議題 H1〜H9 の草案 9 本(1 問ずつ出す): [空間](docs/design/v2-spatial-design-round-draft.md)・[時間](docs/design/v2-time-model-design-round-draft.md)・[ビューア](docs/design/v2-viewer-design-round-draft.md)・[記憶](docs/design/v2-memory-rework-design-round-draft.md)・[コミュニケーション](docs/design/v2-communication-tools-design-round-draft.md)・[決定モデル](docs/design/v2-decision-model-design-round-draft.md)・[カレンダーと行動の時刻](docs/design/v2-calendar-timing-design-round-draft.md)・[反実仮想と部品](docs/design/v2-counterfactual-primitives-design-round-draft.md)。食い違いの一覧は [wallbounce-1003/README.md §2](docs/bench/analysis/wallbounce-1003/README.md)
- リサーチ: 索引 [INDEX.md](docs/research/INDEX.md)・残務 [research-backlog.md](docs/research/research-backlog.md)(R-1〜R-50・以後は INDEX に R-51〜R-89)・分野地図 [v2-discipline-map.md](docs/research/v2-discipline-map.md)
- 受入報告: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7](docs/ops/build-report-C7.md)・[C8](docs/ops/build-report-C8.md)
- 開発ログ: [docs/log/devlog.md](docs/log/devlog.md)(第1〜320 は [devlog-compressed.md](docs/log/devlog-compressed.md) へ圧縮済み・カウンタ 0/10)
- ブランチ/PR: main は PR #7 まで(f9a3c97・2026-09-30 に PR #5 → #6 → #7 をマージ)。作業ブランチ `build/spatial-d102-prep`。タグ `v2-c7-day-4-accepted`(8f78065=実証済みの線)。
- 最終更新: 2026-10-04(第320 10b=IMPLEMENTED #81・保留の議題 9 本の草案が全部そろう・全体テスト 3,544 件。**次は 10c と、草案を 1 問ずつユーザーへ**)。経緯は devlog。
