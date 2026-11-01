# STATUS(索引)

- **現在地(2026-11-02・第341)**: 構築工程 C0〜C8 は一巡(39 万体 × 1 日の実 LLM ラン c7-day-4 を 3 seed・holdout 開封=0/4 NOT PASS・2026-09)。第 0〜7 陣の実装 #87〜#127 と 11-01p の段 1・2(#128〜#133)・presence の docstring(#134)・点群の集計の道具(#135)が本体 `build/spatial-d102-prep` に着地(版上げ 4 回・小さな版上げ 5 回・全体試験 6,368 passed)。正は [回答 11-01](docs/design/v2-answers-2026-11-01.md)(A1=知見の 5 区分・錨の量を式に入れない・判断の置き場 112 件・判断モデル第 1 世代は公開重み・検証は全規模)と [指示書 11-01](docs/design/prompt-2026-11-01.md)。**実装(src/)は 2026-11-01 から限定して再開**(段 0〜3・5。段 4=2-7 背圧は D4 の後・E1 はユーザーの合図)。**実 LLM の手段は 09-22 から無し** → ユーザーの RTX 5070(12 GB)に Qwen3-8B の 4 ビット版を載せて試走 E1 と判断モデルの比較に使う(検証は 35 万体をクラウドで=E 系列の組み直し)。
- **今の段・次の 1 手(セッションが切れてもここから再開)**: 〔第341・11-02〕[指示書 11-02 研究と取得](docs/design/prompt-2026-11-02-research.md)(その 1)の 6 項目を着地=都の点群 62 図郭を data/raw(7,204,230,896 B・台帳 その 21-c)+集計(#135)・D1b を test の層に封印+[門 1 の計画](docs/design/v2-g1-backtest-plan-2026-11-02.md)・駐輪場の一覧・天神の段 0(6/8 件=[t0](docs/bench/analysis/tenjin-2026-11/t0/README.md))・[R-129](docs/research/v2-r129-forecast-target-candidates.md)(親の判断=門 1 の的は東棟)・presence の docstring(#134)。**[返事その 2](docs/design/prompt-2026-11-02-reply2.md)(11-02r)を受領**: 段 4 は 2-7 背圧を作らず **v3=事象駆動の核**の答申へ(R-130/R-131/R-133 を起動・R-132 は dm_eval の後・4 本まとめて 1 回の報告)・A2 の追補 R-134 を起動。〔第342〕v3 の答申 (a)(b)(d)+(イ)=R-130/R-131/R-133/R-134 を報告(決めるべき題 8+A2 の題 7・(c) は dm_eval の後)。#1 fleet.py の取り込み(`f23acfd`)・段 5 の文書の改訂(`7931a8b`)・A2 (ア) 旗 3 欄の文書(`83d2adc`)・`--help` の直し(`335374a`)が着地。段 2 の #7(5 件外し=小さな版上げ・タグ `stable-v2-before-absent-5`)と #6(CI 2 段)が着地(#136・`4566492`)。**次の 1 手**: ユーザーの壁打ち(v3 の題 1 から)と「その 2」の残りの問い(D5 を burned にするか)。5070 の準備(WSL はユーザーの UAC の合図)。#11(10-25 §6-1 の残り 3 つ=切替口の削除・30 日ランの準備・計器)を段 2 の次として開ける。段 3 は 3-1(語彙)だけ。
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
| 小 | 率の形の規則 9 件を外す=出勤率・催しの 200 人・E8・乗車の受け入れ確率・ポイ捨て・売れ残りの廃棄・宅配・倒れる率・Calvo(#132・11-01 §2) | ce52662 | `stable-v2-before-rate-rules`(6a943af) | `git checkout stable-v2-before-rate-rules` か `--rate-rules legacy`(環境変数 `SHIBUYA_RATE_RULES=legacy`・次の版上げで消す) |
| 小 | まだ動いていた「無い」の過程 5 件(ごみ収集・清掃・道路工事・救急の出動・電気と水)を既定で止める(#136・11-02r #7)。既定の final は不変・変わるのは過程の計数と ActualLog。性能 5,000 体 50.0 s/34.7 ms/511 MB(同じ日の土台 49.6〜51.2 s=揺れの範囲) | 4566492 | `stable-v2-before-absent-5`(1c137c6) | `git checkout stable-v2-before-absent-5` か `--absent-processes legacy`(環境変数 `SHIBUYA_ABSENT_PROCESSES=legacy`・次の版上げで消す) |
| 実証の線 | 39 万体 × 1 日の実 LLM(C7 受入) | 8f78065 | `v2-c7-day-4-accepted` | — |

- 進捗の目安: v2 初版(C0〜C8)≈ 70% / 第一目標「世界そのものがプロダクト」≈ 3 割(第126 の見積り・据え置き)。
- **判断待ち・実装待ち・研究の題**: [PENDING.md](PENDING.md)(第339 に 3 区分へ組み直し。旧の形は [pending-archive-2026-10-25.md](docs/log/pending-archive-2026-10-25.md)・[pending-archive-2026-09-28.md](docs/log/pending-archive-2026-09-28.md))
- 完了実装: [IMPLEMENTED.md](IMPLEMENTED.md)(#1〜#136)・運用の道具: `tools/realworld_fetch/`(日次の現実データ・検証専用)・`tools/night5070/`(5070 の夜間ラン=#127・第340 で試走と安全の検査を追加中)・`tools/instruments/dm_eval/`(判断モデルの評価の器)
- 正典: 決定台帳 [v2-redesign.md](docs/design/v2-redesign.md)・方法論 [v2-methodology.md](docs/design/v2-methodology.md)・用語集 [v2-glossary.md](docs/design/v2-glossary.md)・決定の ID の索引 [decision-id-index.md](docs/design/decision-id-index.md)
- 壁打ちの決定の原文: [回答 11-01](docs/design/v2-answers-2026-11-01.md)(最新・A1・すべて仮決定)+[指示書 11-01](docs/design/prompt-2026-11-01.md)・[指示書 11-01 5070](docs/design/prompt-2026-11-01-5070.md)・根拠 3 本は [docs/reference/](docs/reference/)・[回答 10-25](docs/design/v2-answers-2026-10-25.md)(決定/仮決定/研究の題の 3 区分)・[回答 10-13b](docs/design/v2-answers-2026-10-13b.md)(自律運転の規則)・[指示書 10-12](docs/design/v2-wallbounce-decisions-2026-10-12.md)。エンジンが決めている 55 件の 3 群=[一覧](docs/bench/analysis/wallbounce-1006/agentless-outcomes-inventory.md)
- リサーチ: 索引 [INDEX.md](docs/research/INDEX.md)・残務 [research-backlog.md](docs/research/research-backlog.md)・分野地図 [v2-discipline-map.md](docs/research/v2-discipline-map.md)。参照用の凍結(ChatGPT の要約 2 本・10-25)は [docs/reference/](docs/reference/)
- 受入報告: [C5](docs/ops/build-report-C5.md)・[C6](docs/ops/build-report-C6.md)・[C7](docs/ops/build-report-C7.md)・[C8](docs/ops/build-report-C8.md)
- 開発ログ: [docs/log/devlog.md](docs/log/devlog.md)(第1〜330 は [devlog-compressed.md](docs/log/devlog-compressed.md) へ圧縮済み)
- ブランチ/PR: main は PR #7 まで(f9a3c97・2026-09-30)。main は PR #8(bad7577・2026-11-01)まで。作業ブランチ `build/spatial-d102-prep` は段 1・段 2 の着地で main より先(次の PR は段 2 の残りの後)。
- 最終更新: 2026-11-02(第341=指示書 11-02 その 1 の 6 項目=点群 raw+集計・D1b 封印と門 1 の計画・駐輪場・天神 段 0・R-129・presence docstring。その 2 を受領=v3 の答申 3 本と R-134 を起動)
