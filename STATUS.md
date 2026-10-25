# STATUS(索引)

- **現在地(2026-10-25・第339)**: 構築工程 C0〜C8 は一巡(39 万体 × 1 日の実 LLM ラン c7-day-4 を 3 seed・holdout 開封=0/4 NOT PASS・2026-09)。第 0〜7 陣の実装 #87〜#126 が本体 `build/spatial-d102-prep` に着地(版上げ 4 回・小さな版上げ 3 回・全体試験 6,207 passed・CI 緑)。正は [実装の計画 10-12](docs/design/v2-implementation-plan-2026-10-12.md)と [回答 10-25](docs/design/v2-answers-2026-10-25.md)。**実装(src/ の変更)は停止中**(10-25/§0-0)=再開はユーザーの合図「実装を再開」。**実 LLM の手段は 09-22 から無し** → ユーザーの RTX 5070(12 GB)に Qwen3-8B の 4 ビット版を載せて再開する準備中(10-25/§6)。
- **今の段・次の 1 手(セッションが切れてもここから再開)**: 〔第339・10-25〕今週=回答 10-25 の保存(済 d2a4b59)→ PENDING を 3 区分に(済)・CLAUDE.md §7 の改訂(済)→ 答申 R-A(R-120・R-121)・R-B(R-122)・R-C(R-123)→ 夜間ランの道具 `tools/night5070/`(作業木 `stage/night5070`)→ 2-7 の確認の報告 → 段 0 の取得(10-25/§2-1)→ README「いま」・概要書の数字(10-25/§9)→ **11/5 までに PR #8 を main へ**(src/ の新しい変更は含めない)。合図の後=10-25/§6-1 の 1〜5 → E1 を 5070 で(寝ている間)。
- **版上げの履歴とタグ(戻し方つき・10-13b/§0-6・§0-7)**:

| 回 | 何 | 取り込み | 安定版のタグ(直前の commit) | 戻し方 |
|---|---|---|---|---|
| 1 回目 | 10e 暦は実日・開始日 2026-07-13・天気・behavior-hash・テープ版 4(#87・#88・第329〜330) | 第330 | タグなし(§0-7 の前) | IMPLEMENTED #88 の commit を checkout |
| 2 回目 | 2-4 近接 distance・在席の印・経済 stage2・資産の活性化(#101・第334) | d35a9b6 | タグなし(§0-7 の前) | 直前の commit を checkout |
| 小 | 賃金を職業ごとの実データから(#115) | c87d5de | `stable-v2-before-wage-occupation`(cb38b0a) | `git checkout stable-v2-before-wage-occupation`(旧道 `--wage w17` は 672a7f9 で削除済み) |
| 小 | 第 18-1 表の置き換え=既定の食事時刻と初期の空腹(#117) | 2809c4a | `stable-v2-before-meal-default-w17`(276361e) | `git checkout stable-v2-before-meal-default-w17`(旧道 `--meal-default validation` は削除済み) |
| 3 回目 | 4-1 段 10 差し替え W16 → W21c=母集団 345,858 体(#118) | 2313e1b | `stable-v2-before-pop-w21`(8b1fb84) | checkout+`activate_pop43.py revert`(退避 `data/world/v2_pre_4-3`)。旧値だけなら `--world data/world/v2_pre_4-3` |
| 小 | 4-2 規則の表 19+1 行・給与の天引き・消費税の預かり金(#120) | e2b1f6f | `stable-v2-before-rules-42`(6f07eff) | checkout か `SHIBUYA_RULES_42=off`(次の版上げで消す) |
| 小 | 4-2b 規則の表の空欄 3 件(#122) | a04b46d | `stable-v2-before-rules-42b`(01649bb) | checkout か `SHIBUYA_RULES_42B=off`(次の版上げで消す) |
| 4 回目 | 第 5 期 段 1b 密度の推定=`--space nav1`+近傍が既定(#126) | b02c257 | `stable-v2-before-space-1`(6e46dbb) | `git checkout stable-v2-before-space-1`(既定が legacy に戻る・資産は残してよい)か `--space legacy`(次の版上げで消す) |
| 実証の線 | 39 万体 × 1 日の実 LLM(C7 受入) | 8f78065 | `v2-c7-day-4-accepted` | — |

- 進捗の目安: v2 初版(C0〜C8)≈ 70% / 第一目標「世界そのものがプロダクト」≈ 3 割(第126 の見積り・据え置き)。
- **判断待ち・実装待ち・研究の題**: [PENDING.md](PENDING.md)(第339 に 3 区分へ組み直し。旧の形は [pending-archive-2026-10-25.md](docs/log/pending-archive-2026-10-25.md)・[pending-archive-2026-09-28.md](docs/log/pending-archive-2026-09-28.md))
- 完了実装: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#126)・運用の道具: `tools/realworld_fetch/`(日次の現実データ・検証専用)・`tools/night5070/`(5070 の夜間ラン=第339 で作成中)
- 正典: 決定台帳 [v2-redesign.md](docs/design/v2-redesign.md)・方法論 [v2-methodology.md](docs/design/v2-methodology.md)・用語集 [v2-glossary.md](docs/design/v2-glossary.md)・決定の ID の索引 [decision-id-index.md](docs/design/decision-id-index.md)
- 壁打ちの決定の原文: [回答 10-25](docs/design/v2-answers-2026-10-25.md)(最新・決定/仮決定/研究の題の 3 区分)・[回答 10-13b](docs/design/v2-answers-2026-10-13b.md)(自律運転の規則)・[指示書 10-12](docs/design/v2-wallbounce-decisions-2026-10-12.md)。エンジンが決めている 55 件の 3 群=[一覧](docs/bench/analysis/wallbounce-1006/agentless-outcomes-inventory.md)
- リサーチ: 索引 [INDEX.md](docs/research/INDEX.md)・残務 [research-backlog.md](docs/research/research-backlog.md)・分野地図 [v2-discipline-map.md](docs/research/v2-discipline-map.md)。参照用の凍結(ChatGPT の要約 2 本・10-25)は [docs/reference/](docs/reference/)
- 受入報告: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7](docs/ops/build-report-C7.md)・[C8](docs/ops/build-report-C8.md)
- 開発ログ: [docs/log/devlog.md](docs/log/devlog.md)(第1〜330 は [devlog-compressed.md](docs/log/devlog-compressed.md) へ圧縮済み)
- ブランチ/PR: main は PR #7 まで(f9a3c97・2026-09-30)。作業ブランチ `build/spatial-d102-prep`(PR #8 OPEN・main より 244 commit 先=11/5 までに 1 回で取り込む)。
- 最終更新: 2026-10-25(第339 回答 10-25 の反映=PENDING の 3 区分・CLAUDE.md §7・版上げの履歴の表)
