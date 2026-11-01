# STATUS(索引)

- **現在地(2026-11-01・第340)**: 構築工程 C0〜C8 は一巡(39 万体 × 1 日の実 LLM ラン c7-day-4 を 3 seed・holdout 開封=0/4 NOT PASS・2026-09)。第 0〜7 陣の実装 #87〜#127 が本体 `build/spatial-d102-prep` に着地(版上げ 4 回・小さな版上げ 3 回・全体試験 6,207 passed)。正は [回答 11-01](docs/design/v2-answers-2026-11-01.md)(A1=知見の 5 区分・錨の量を式に入れない・判断の置き場 112 件・判断モデル第 1 世代は公開重み・検証は全規模)と [指示書 11-01](docs/design/prompt-2026-11-01.md)。**実装(src/)は 2026-11-01 から限定して再開**(段 0〜3・5。段 4=2-7 背圧は D4 の後・E1 はユーザーの合図)。**実 LLM の手段は 09-22 から無し** → ユーザーの RTX 5070(12 GB)に Qwen3-8B の 4 ビット版を載せて試走 E1 と判断モデルの比較に使う(検証は 35 万体をクラウドで=E 系列の組み直し)。
- **今の段・次の 1 手(セッションが切れてもここから再開)**: 〔第340・11-01〕添付 6 本の保存(済 fc1b44b)→ 文書の改訂(CLAUDE.md §4・用語集 2-14・決定台帳・索引・README=済 fc1b44b)→ **並行の作業木 5 本**(`stage/n5070-1101`=試走と安全の検査/`stage/dmeval-1101`=消費の場面と比較の列/`stage/leak-1101`=漏洩の検査の器/`stage/ledger-1101`=錨の台帳の 2 列/`stage/eseries-1101`=E 系列の組み直し)と研究 5 本(R-124〜R-128)→ 検収と取り込み → **11/5 までに PR #8 を main へ**(文書だけ)→ 段 2(台帳と循環・小さな src)→ WSL の導入(最後・再起動)→ 完了の条件 1〜7 → 段 3(段 1 の比較の後)。
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
- 完了実装: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#127)・運用の道具: `tools/realworld_fetch/`(日次の現実データ・検証専用)・`tools/night5070/`(5070 の夜間ラン=#127・第340 で試走と安全の検査を追加中)・`tools/instruments/dm_eval/`(判断モデルの評価の器)
- 正典: 決定台帳 [v2-redesign.md](docs/design/v2-redesign.md)・方法論 [v2-methodology.md](docs/design/v2-methodology.md)・用語集 [v2-glossary.md](docs/design/v2-glossary.md)・決定の ID の索引 [decision-id-index.md](docs/design/decision-id-index.md)
- 壁打ちの決定の原文: [回答 11-01](docs/design/v2-answers-2026-11-01.md)(最新・A1・すべて仮決定)+[指示書 11-01](docs/design/prompt-2026-11-01.md)・[指示書 11-01 5070](docs/design/prompt-2026-11-01-5070.md)・根拠 3 本は [docs/reference/](docs/reference/)・[回答 10-25](docs/design/v2-answers-2026-10-25.md)(決定/仮決定/研究の題の 3 区分)・[回答 10-13b](docs/design/v2-answers-2026-10-13b.md)(自律運転の規則)・[指示書 10-12](docs/design/v2-wallbounce-decisions-2026-10-12.md)。エンジンが決めている 55 件の 3 群=[一覧](docs/bench/analysis/wallbounce-1006/agentless-outcomes-inventory.md)
- リサーチ: 索引 [INDEX.md](docs/research/INDEX.md)・残務 [research-backlog.md](docs/research/research-backlog.md)・分野地図 [v2-discipline-map.md](docs/research/v2-discipline-map.md)。参照用の凍結(ChatGPT の要約 2 本・10-25)は [docs/reference/](docs/reference/)
- 受入報告: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7](docs/ops/build-report-C7.md)・[C8](docs/ops/build-report-C8.md)
- 開発ログ: [docs/log/devlog.md](docs/log/devlog.md)(第1〜330 は [devlog-compressed.md](docs/log/devlog-compressed.md) へ圧縮済み)
- ブランチ/PR: main は PR #7 まで(f9a3c97・2026-09-30)。作業ブランチ `build/spatial-d102-prep`(PR #8 OPEN・11/5 までに 1 回で取り込む=文書だけ・src/ の新しい変更は含めない)。
- 最終更新: 2026-11-01(第340 回答 11-01 の反映=実装の限定の再開・作業木 5 本と研究 5 本の並行)
