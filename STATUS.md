# STATUS(索引)

- **現在地(2026-09-30・第311)**: 構築工程 C0〜C8 は一巡(39 万体×1 日の実 LLM ラン c7-day-4 を 3 seed・holdout 開封=0/4 NOT PASS・帰属は来街者比と時刻の形)。第281〜309 で GPU 不要の実装 #49〜#75 を入れた(全体テスト 3,312 件)。**2026-09-30 にユーザーが判断待ちの全項に回答**([壁打ちの決定 09-30](docs/design/v2-wallbounce-decisions-2026-09-30.md))=順番は D-102 の土台 → 実距離の会話/近接 → 空間の設計ラウンド → 空間の実装 → 記憶の作り直し。反映・食い違い・確認の結果は [反映の記録](docs/design/v2-wallbounce-0930-reflection.md)。**実 LLM の手段なし(09-22〜)**。
- 進捗の目安: v2 初版(C0〜C8)≈ 70% / 第一目標「世界そのものがプロダクト」≈ 3 割(第126 の見積り・据え置き)。
- **いま・判断待ち・実装待ち・最近の実装・予定**: [PENDING.md](PENDING.md)(第279 に簡潔な形へ組み直し。旧全文は [pending-archive-2026-09-28.md](docs/log/pending-archive-2026-09-28.md))
- 完了実装: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#79)
- 正典: 決定台帳 [v2-redesign.md](docs/design/v2-redesign.md)・方法論 [v2-methodology.md](docs/design/v2-methodology.md)・用語集 [v2-glossary.md](docs/design/v2-glossary.md)
- 答え待ち(アジェンダの確認): [D-102 の土台](docs/design/v2-d102-foundation-implementation-agenda.md)(A1〜A11)・[実距離の会話/近接](docs/design/v2-proximity-distance-implementation-agenda.md)(B1〜B8)・[上書きの確認 C1〜C6・I-1〜I-3](docs/design/v2-wallbounce-0930-reflection.md)。材料: [セル依存の全リスト](docs/design/v2-cell-dependency-inventory.md)・[空間層 D-122](docs/design/v2-spatial-physics-layer-draft.md)・[再開と決定論 D-102](docs/design/v2-resume-determinism-draft.md)・[記憶アジェンダ](docs/design/v2-memory-agenda.md)
- リサーチ: 索引 [INDEX.md](docs/research/INDEX.md)・残務 [research-backlog.md](docs/research/research-backlog.md)(R-1〜R-50・以後は INDEX に R-51〜R-69)・分野地図 [v2-discipline-map.md](docs/research/v2-discipline-map.md)
- 受入報告: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7](docs/ops/build-report-C7.md)・[C8](docs/ops/build-report-C8.md)
- 開発ログ: [docs/log/devlog.md](docs/log/devlog.md)(第1〜310 は [devlog-compressed.md](docs/log/devlog-compressed.md) へ圧縮済み・カウンタ 4/10)
- ブランチ/PR: main は PR #7 まで(f9a3c97・2026-09-30 に PR #5 → #6 → #7 をマージ)。作業ブランチ `build/spatial-d102-prep`。タグ `v2-c7-day-4-accepted`(8f78065=実証済みの線)。
- 最終更新: 2026-09-30(第314 第 2 波 B #79=食事の束。指示書 §8-1・§8-2 の「すぐ着手してよいもの」は全部済。**次はアジェンダの確認の答え**)。経緯は devlog。
