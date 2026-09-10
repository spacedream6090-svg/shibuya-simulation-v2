# devlog(v2)

> 毎交換1エントリ・10件で docs/log/devlog-compressed.md へ圧縮。カウンタ: **9 / 10**
> 第1〜第120(2026-09-01〜09-09)は [devlog-compressed.md](devlog-compressed.md) へ圧縮済み。v1のdevlog(第1〜178)はv1リポ docs/log/ に残置(参照専用)。

## 第129 D-58 は (a)・再スタートは保留・Discord C7 報告・queue_capacity の CLI 引数(2026-09-10)

- **依頼**: ユーザー「aかな」「今回の C7 のログと分析を Discord に投げたい」「まだ c7 を再スタートする必要はない」。
- **実施**: (1) Discord 用 C7 報告(docs/ops/discord_report_c7_2026-09-10.md・2 分割+添付用 summary 抜粋とテープ解析表・IP/パス/名前なし)。(2) `--fleet-queue-capacity`(engine/run.py add_fleet_args→FleetConfig.queue_capacity・既定 0=不変)+manifest_fields に queue_capacity を記録+tests/engine/test_fleet_wiring 1 本。(3) C8 ablation ランナーの不具合 2 件を修正して ⑥→① を 09:20 に再起動(第128b)。(4) PENDING D-58 を (a) 決定・起動は合図待ちに更新。
- **C7 の回し直し(c7-day-3)は起動していない**(ユーザー指示)。起動時のコマンド: run_c7.sh に `--fleet-queue-capacity 4096` を足す(計画 2,709/tick 以上・再投入の揺らぎ込み)。
- **次**: ユーザーの合図で c7-day-3 起動(約 14 h)→受入→再生 T2-c→holdout 開封→報告→層2→出口。C8 ⑥→① の結果回収(〜11:40)。

## 第128 C7 受入 T2 の結果と停止句 (a)(2026-09-10)

- **依頼**: /goal 再設定(ユーザー・条件文を全文表示)。
- **T2-a**(5,000 体×1 日・同 seed・同 run-id・実 LLM・各 35 分・繰り延べ 0): 全 checkpoint 一致。
- **T2-c**(本番テープ再生・390,067 体・40 分・RSS 6.8 GB): **不一致・測定不能**。tape_miss 98.7%。原因はテープに繰り延べ行が無いこと(応答行のみ)+繰り延べの翌 tick 再投入。再生に繰り延べが無いので tick 0 から分岐。コードで確認(llm_bridge 559-580・run.py 1156-1168)。
- **停止句 (a)**: 運用設計書 §1.4 T2・§2.5 テープ形式(決定項)に触れる分岐+一度きりの holdout 開封先の選択 → PENDING D-58 に (a) queue_capacity を直して本番回し直し(推奨・13-14 h)/(b) c7-day-2 を受入れ今開封/(c) テープに繰り延べ行(第2陣)を書いて**停止**。holdout は未開封のまま。
- **並行**: 感度試験 5 件を親再実行し一致(第127d)。艦隊が空いた時点で C8 ablation ⑥→①(5,000 体)を自動起動(tmux c8wait→run_c8.sh)=どの分岐でも必要。
- **次(ユーザー判断後)**: (a) なら FleetConfig の queue_capacity を CLI から渡せるようにして c7-day-3 →受入→再生 T2-c→holdout 開封→報告→層2→出口。(b) なら holdout 開封→報告→層2→出口。

## 第127 C7 本番ラン完走・受入開始(2026-09-10)

- **依頼**: /goal 続行(ユーザー: モデル確認=Fable 5.1 に復帰・Remote Control も同一セッション)。
- **事実**: c7-day-2 は 09-10 05:39 完走(壁時計 9 h 10 m・見込み 14.4 h より早い=tape の呼あたりバイトが c6 より小さかった)。W1 9.17 h/M8 1.53 GB/S1 0.165 GB/L4 3,900,670=10.00 呼/体/日/保存則・センサス・憲法5 OK/DIAG 4 列。受入表 9/16 行 PASS・0 不合格。
- **実施**: Git Bash の ssh がエイリアス解決不能→Windows OpenSSH(PowerShell・/c/Windows/System32/OpenSSH/ssh.exe)に切替。HEAD(第126)の src/tools/tests をサーバーへ同期(sha256 一致)。T2-c(テープ再生・CPU)と T2-a(5,000 体×2・実 LLM)を tmux acc-c/acc-ab で 07:54 起動・Monitor 常設。T2-b は回さない(D-54)。在圏系列 5 エリア 138 ha 作成。報告書 §1 結果表・§1d 要約・§2a ログを記入。
- **発見→PENDING**: D-51 乗車 75/降車 0(変換極小)・D-52 廃棄 17.9 t が帯外(全母集団でも)・D-53 状態成長 NG(transfer_log cap 頭打ち)・D-54 T2-b は時刻依存の繰り延べで測れない→再生で代替・D-55 艦隊が律速(fleet_wait 84%・繰り延べ 33.8%)。
- **次**: T2 完了→c7_accept 全行→holdout 開封 1 回(D-43)→報告書→層2 検収→C7 出口コミット→IMPLEMENTED #17。艦隊が空いたら C8 ablation ⑥→① (5,000 体)。

## 第126 現状report+完成度の見積り(2026-09-10)

- **依頼**: ユーザー「現状を教えて。シミュレーションの完成を 100 としたときのパーセントで」。
- **確認した事実**: C7 c7-day-2 は走行中(経過 5.8 h・tape 110.4 MB・GPU 7 枚とも 100%・ログは Python バッファリングで 0 B=正常)。tape の 1 呼あたり 70.3 B(c6-day-3 実測)から推定 1.57 M 呼 / 総 3.90 M 呼 = **約 40%**・総見込み 14.4 h・完了 09-10 11 時ごろ。前セッションの Monitor はセッション終了で停止していた→再武装。
- **完成度(親の見積り・重みは expedient)**: v2 初版(C0〜C8 完走)を 100 として **約 70%**(C0-C4 30/30・C5 15/15・C6 10/10・C7 9/20=ラン 40%+受入計器は完成・C8 5/25=基盤と切替口 4/6 腕・実ラン 0)。工程数だけなら 7.75/9=86% だが、終わった安い工程を過大評価する。第一目標「世界そのものがプロダクト」なら **約 3 割**(第2陣の世界過程・知覚(聴覚 SNR・日次内省・近接入替・知人出現・被注視・傍受)未実装/複数日〜週・月スケール未実施=v1 の最大の宿題/関係辺・社会構造/アンカー台帳の継続的成長/感度未宣言 108 行/公開・運用)。
- **記録**: STATUS.md を更新(09-09 第119 のまま古かった)。今セッションの親は Opus 5(1M)=CLAUDE.md §5 の「親=Fable 5」と機種が違う(規律は同一・コミット trailer は現行の指定に従う)。
- **次**: C7 完了通知→tape/occupancy/log 回収→`--replay` で checkpoint 列(T2-c)→5,000 体×2 実 LLM(T2-a)→先頭 60 tick 部分再ラン(T2-b)→c7_accept→holdout 開封 1 回(D-43)→受入報告→層2 検収→C7 出口コミット。その後 C8 の ⑥→① 実 LLM ablation。

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
