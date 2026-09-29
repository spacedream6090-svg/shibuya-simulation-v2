# STATUS(索引)

- **現在地(2026-09-29・第310)**: 構築工程 C0〜C8 は一巡(39 万体×1 日の実 LLM ラン c7-day-4 を 3 seed・holdout 開封=0/4 NOT PASS・帰属は来街者比と時刻の形)。第280 の回答を受けて第281〜309 で PENDING §2 の GPU 不要の実装を全部入れた(IMPLEMENTED #49〜#75・全体テスト 3,312 件・既定 golden v3 993276d5)。**GPU 不要で進められる実装はユーザーの答え待ちで尽きた**=判断待ちの一覧と実装のまとめは [いま決めること 09-29](docs/design/v2-decisions-for-user-2026-09-29.md)。**実 LLM の手段なし(09-22〜)**。
- 進捗の目安: v2 初版(C0〜C8)≈ 70% / 第一目標「世界そのものがプロダクト」≈ 3 割(第126 の見積り・据え置き)。
- **いま・判断待ち・実装待ち・最近の実装・予定**: [PENDING.md](PENDING.md)(第279 に簡潔な形へ組み直し。旧全文は [pending-archive-2026-09-28.md](docs/log/pending-archive-2026-09-28.md))
- 完了実装: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#75)
- 正典: 決定台帳 [v2-redesign.md](docs/design/v2-redesign.md)・方法論 [v2-methodology.md](docs/design/v2-methodology.md)・用語集 [v2-glossary.md](docs/design/v2-glossary.md)
- 答え待ち: [いま決めること 09-29](docs/design/v2-decisions-for-user-2026-09-29.md)(一覧・依存表・回答例)・[空間層 D-122](docs/design/v2-spatial-physics-layer-draft.md)・[再開と決定論 D-102](docs/design/v2-resume-determinism-draft.md)・[記憶アジェンダ M17](docs/design/v2-memory-agenda.md)・[空腹・判断層・注意 v1](docs/design/v2-hunger-choice-attention-draft.md)・[記憶・口コミ・ネット](docs/design/v2-memory-wom-internet-draft.md)
- リサーチ: 索引 [INDEX.md](docs/research/INDEX.md)・残務 [research-backlog.md](docs/research/research-backlog.md)(R-1〜R-50)・分野地図 [v2-discipline-map.md](docs/research/v2-discipline-map.md)
- 受入報告: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7](docs/ops/build-report-C7.md)・[C8](docs/ops/build-report-C8.md)
- 開発ログ: [docs/log/devlog.md](docs/log/devlog.md)(第1〜310 は [devlog-compressed.md](docs/log/devlog-compressed.md) へ圧縮済み・カウンタ 0/10)
- ブランチ/PR: main は PR #4 まで(630ad13)。未マージ(この順): [PR #5](https://github.com/spacedream6090-svg/shibuya-simulation-v2/pull/5) build/d113 → [PR #6](https://github.com/spacedream6090-svg/shibuya-simulation-v2/pull/6) build/vocab-v3 → [PR #7](https://github.com/spacedream6090-svg/shibuya-simulation-v2/pull/7) design/memory-net-draft。タグ `v2-c7-day-4-accepted`(8f78065=実証済みの線)。
- 最終更新: 2026-09-29(第310 実装のまとめと判断待ちの一覧=[いま決めること 09-29](docs/design/v2-decisions-for-user-2026-09-29.md)・PENDING の組み直し・devlog 第301〜310 の圧縮。**次はユーザーの答え**)。経緯は devlog。
