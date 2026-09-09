# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **1 / 10**
> 第1〜第120(2026-09-01〜09-09)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第121 C8 基盤の親検収+D-44〜D-47+Discord 報告文案(2026-09-09)

- **依頼**: /goal 続行(C8 準備)。ユーザー: v1 までの開発過程を Discord に投稿してサーバー延長を相談したい→報告文案。
- **実施**: サブ T の C8 基盤(tools/c8: ablation_runner・ablations_v1.json・sensitivity+sensitivity_v1.json・dashboard・ensemble・c8lib/tests/c8 5 ファイル)を親検収: `pytest tests/c8` 105 passed・lint-imports 5 kept・scan CLEAN。T の親判断待ちを PENDING D-44(感度宣言漏れ 108 行=片側規則で一括判定)・D-45(ablation ②③⑥ 切替口→C8 で実装・④⑤第2陣)・D-46(アンサンブルは 5,000 体)・D-47(L2 分母=W1 24h 仮)へ。サブ U 起動(②③⑥ の切替口・既定バイト不変)。Discord 報告文案 3 分割を docs/ops/discord_report_2026-09-09.md に。
- **C7**: c7-day-2 本番ラン継続中(9/9 20:29 開始・ETA 約 15 h)。
- **次**: サブ U 検収→C8 切替口コミット。C7 完了→受入表→holdout 開封 1 回→C7 出口。ユーザー問い「シミュレーションのビジネス」に Web リサーチで回答。
