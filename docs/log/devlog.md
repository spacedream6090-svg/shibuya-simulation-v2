# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **5 / 10**
> 第1〜第120(2026-09-01〜09-09)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第125 Discord 報告 3/3 を公開向けに改版(2026-09-10)

- **依頼**: ユーザー「1/3・2/3 は投稿済み。3/3 は不特定多数向けなのでそれを加味して」。
- **実施**: 3/3 を「計算資源の事実+これから+公開物+読者への窓口」に改版(提供者個人への依頼文は参照用に残置)。サーバー名・IP・個人名なし。
- **C7**: c7-day-2 継続中(tape 76 MB@23:3x・毎時 19 MB)。
- **次**: C7 完了→受入。

## 第124 D-50 穴台帳(実行できなかった行動を数える仕組み)の起案+軽リサーチ(2026-09-09)

- **依頼**: ユーザー発案「エージェントに足りない実装を報告させる/実行できなかった行動を自動診断・収集する仕組み」→親の評価=報告させる(作話・設計者の口・費用)は不採用、エンジン側で躓きを数える形を推奨→ユーザー「載せて。軽くリサーチし、実装時に深くリサーチするメモも」。
- **実施**: PENDING D-50 起案(既存信号の束ね方・型 5 種・日次センサス形集計・順位規則・出口=提案まで・弱点)。軽リサーチ 4 検索(MATSim stuckAndAbort/DRT 拒否・BDI-ABM・Voyager・Affordable Generative Agents 飽和曲線・Emergence World M11・失敗分類学 MAST/AgentErrorTaxonomy/ACCORD)=未一次確認と明記。直接の先行研究なし。実装時の深掘り義務をメモ。
- **C7**: c7-day-2 継続中(tape 38 MB@22:3x)。
- **次**: C7 完了待ち→受入。

## 第123 C7 受入の前準備: 受入計器ドライラン+cli --checkpoints-out/--replay+売上試算(2026-09-09)

- **依頼**: /goal 続行。ユーザー: 「売上の試算」→3 シナリオ提示。続けて「世界と人の行動まで再現する事業なのに試算が小さすぎないか」→2 層(積み上げ=初年度の請求可能額/到達市場=プラットフォーム化した場合)で再回答。
- **実施**: 受入計器を mock 2,000 体×180 tick でドライラン(在圏 journal→occupancy_series 5 エリア表→holdout_compare は --open-seal なしで拒否=門番 OK→c7_accept 受入表 8/16 行 PASS)。穴=T2 行の入力(checkpoint 列 JSON)が CLI から出ない→`--checkpoints-out`(JSON)+`--replay`(本番テープの再生で 40 万体の checkpoint 列を復元)を追加。tests/test_cli 3 本追加(73 passed w/ tests/c7)・lint 5 kept・scan CLEAN。既定バイト不変。
- **C7**: c7-day-2 継続中(Monitor 常設)。完了後の手順: tape+occupancy+log を回収→`--replay` で checkpoint 列(T2-c)→5,000 体×2 実 LLM(T2-a)→先頭 60 tick 部分再ラン(T2-b)→c7_accept→holdout 開封 1 回→報告→層2→コミット。
- **次**: C7 完了待ち。完了後 ⑥→① の実 LLM ablation(5,000 体)。

## 第122 C8 ablation 切替口 ②③⑥(サブ U・親検収)+D-48/D-49+ビジネス回答(2026-09-09)

- **依頼**: /goal 続行。ユーザー: 「このシミュレーションを用いたビジネスの考え(Web リサーチ付き)」。
- **実施**: サブ U の切替口 3 腕を親検収: mock 実資産 5,000 体×1 日 checkpoint **d5d79337… 不変**(親再実行・sessions 48・呼 49,847)・テンプレ SHA 161fe181 不変・tests/c8 105 passed・lint 5 kept・scan CLEAN・engine/perception/cli pytest(P6 は D-48 で deselect)。実装: `run_day(p_notice_d50_scale/refractory_scale/signage)`+cli `--pnotice-d50-scale/--refractory-scale KEY=F/--no-signage`・不応期は「ランごとの実効表」を resolve へ(Final 定数は既定経路に残す)・看板行は `B2.signage_empty`。新テスト 39+15 本。親が tools/c8 の残り 3 箇所を修正(PENDING_KWARGS 空・runs の pending 印 8 個削除・manifest 欄 4 個追加)+腕表に親注(②天井・③no-op)。
- **記録**: D-48(P6 変化検出が定常以外で 2 ms 超過=サブ T 3 回再現・D-3 訂正)・D-49(② は A4 既定で距離項に槓桿なし・③ は第2陣まで no-op→実 LLM の順は ⑥→①→②(A1)・③は回さない)。
- **ビジネス回答**: Web リサーチ(Simile $2B/Aaru $1B 見出し値/Simulacra/CitySim 渋谷密度再現主張/PLATEAU uc25-05・uc22-004/OOH 計測ベンダー/検証文献のハイブリッド収束)→事業案 5 本を優先順で提示(①広告効果の桁 ②まちづくり介入前実験 ③合成渋谷データ ④測定装置/オープンコア ⑤観察メディア)。判断はユーザー。
- **C7**: c7-day-2 継続(vLLM 完了数 約 13 呼/s/GPU・tape 21 MB@21:31)。Monitor 常設(10 分毎)。
- **次**: C7 完了→受入表→holdout 開封 1 回→C7 出口。C8: ⑥→① の実 LLM ablation は C7 完了後の GPU で(各 ≤1 h・5,000 体)。

## 第121 C8 基盤の親検収+D-44〜D-47+Discord 報告文案(2026-09-09)

- **依頼**: /goal 続行(C8 準備)。ユーザー: v1 までの開発過程を Discord に投稿してサーバー延長を相談したい→報告文案。
- **実施**: サブ T の C8 基盤(tools/c8: ablation_runner・ablations_v1.json・sensitivity+sensitivity_v1.json・dashboard・ensemble・c8lib/tests/c8 5 ファイル)を親検収: `pytest tests/c8` 105 passed・lint-imports 5 kept・scan CLEAN。T の親判断待ちを PENDING D-44(感度宣言漏れ 108 行=片側規則で一括判定)・D-45(ablation ②③⑥ 切替口→C8 で実装・④⑤第2陣)・D-46(アンサンブルは 5,000 体)・D-47(L2 分母=W1 24h 仮)へ。サブ U 起動(②③⑥ の切替口・既定バイト不変)。Discord 報告文案 3 分割を docs/ops/discord_report_2026-09-09.md に。
- **C7**: c7-day-2 本番ラン継続中(9/9 20:29 開始・ETA 約 15 h)。
- **次**: サブ U 検収→C8 切替口コミット。C7 完了→受入表→holdout 開封 1 回→C7 出口。ユーザー問い「シミュレーションのビジネス」に Web リサーチで回答。
