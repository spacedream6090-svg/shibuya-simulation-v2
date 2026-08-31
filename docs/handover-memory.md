# メモリ引き継ぎ文書(v1プロジェクト → v2・2026-09-01作成)

> **新プロジェクトの最初のセッションのClaudeへ**: 本書はv1プロジェクトのClaudeメモリ23本から、v2でも有効な恒常事項を転写したもの。これを読んだら、各項をメモリ(user/feedback/project/reference)として再登録すること。恒常規律の正典は [CLAUDE.md](../CLAUDE.md)(本書は背景と経緯を補う)。

## ユーザー像

- 塚本翔太さん。個人開発者(所属なし)。世界観: **自然界を模した仕組み志向**=ボトムアップ創発を第一候補に(「現実社会の制度も自然界を模した仕組みが多い」)。
- DT観: 現実の**ある時点のスナップショット**を舞台にする(同期不要)。「現実はシミュレーションの解像度を高めるためのデータ収集ツール」。
- 設計判断への関与を重視: 決定はユーザーが行い、Claudeはリサーチ・選択肢・推奨・矛盾検出を担う。

## 恒常ルール(feedback系・全てユーザー明示指示)

1. **report-per-task**: タスク/ラン完了の都度、結果→含意→選択肢を報告しユーザー判断を仰ぐ。「僕の方では状況を把握していないから教えてもらわないとわからない」(2026-08-20)。
2. **pre-coding-alignment**: コード着手前に決定アジェンダを提示し合意を得る(2026-07-02)。
3. **ask-before-extending**: Claude発案の修正・拡張は実装前に必ず確認(設計者の指紋の最小化)。
4. **research-first-implementation**: 「僕の例は信用せずリサーチで重要なものを選んで実装して」(2026-07-21)。
5. **validation-runs-short**: 修正のたびにフルランを回さない。mock/〜24stepスモークで素早く(2026-07-05)。
6. **devlog-protocol**: 毎交換devlog追記・10件で圧縮(v2では新規第1から)。
7. **status-ledger-protocol**: STATUS/IMPLEMENTED/PENDING 3ファイル・完了はPENDINGから消す・作業終了時にも更新(2026-08-03/08-12)。

## 世界観・設計ドクトリン(v2に直結)

8. **agent-driven-world**: 世界の変化はエージェント行動の結果として実装。エンジン代替はconf宣言つきフォールバック限定(2026-08-20)。リサーチ数値は強制定数でなく較正目標。
9. **natural-coinage-observation**: 造語・流行は促進しない。発生の文脈を厚く記録して観察する(2026-07-05)。
10. **org-emergence-goal**: 組織の自然形成+ファウンダー成立条件の観察は主要研究目標(2026-07-19)。
11. **realism-first-scale**: 現実渋谷の忠実再現が土台・人数>実行時間・サービス提供者も全員エージェント・100万ペルソナプール(2026-07-19)。
12. **game-techniques-not-game**: ゲームは作らない。ゲーム/VR産業の技術知見を輸入する(2026-08-31)。

## v2プロセス規律

13. **v2-decision-process**: Q&A対話式・構築前確認・矛盾チェック・全決定は仮・毎回事前リサーチ・細部定義後に実装・エンジン/LLM線引き明文化・小資源検証を設計要件に(2026-08-30/31)。
14. **v2-dev-methodology**: パターン台帳先行・mechanism|expedientタグ・予算宣言・ablationゲート・holdout非接触(2026-08-29・正典 docs/design/v2-methodology.md)。
15. **agent-operating-mode**: Fable 5=計画/検収/コミット・実行役サブ=Opus 5(model:"opus")。サブはコミット禁止・**セッション上限で黙って停止する事故が頻発**(v1で5回以上)=検収はディスク実在+親のpytestが唯一の真実。モデル情報は記憶で断言せずスキルで確認(2026-07-27の誤回答教訓)。
16. **paper-research-workflow**: 論文はWeb版優先で自律リサーチ(arXiv等の正規ドメインのみ・ダウンロード実行禁止)。ReadツールはこのWindows環境でPDF不可(poppler未導入)→pymupdf等で抽出。

## 参照情報

- **v1リポ(参照専用)**: `c:\Users\塚本翔太\Desktop\shibuya-simulation` = https://github.com/spacedream6090-svg/shibuya-simulation (private)。公開ミラー: shibuya-simulation-public(2026-07-28公開・ops/publish_public_mirror.ps1で同期)。アカウント: spacedream6090-svg・gh CLI導入済み(keyring)。
- v1の較正資産: scripts/calibrate_report.py・現実整合アンカー(本リポ data/ground_truth/registry.yaml にコピー済み)・実LLM較正の教訓(mock は LLM依存行動の較正に無意味・実LLMランで判定)。
- v1の警告的教訓: reflect-think-starvation(think=trueで内省が全空だったバグ)・RAM bloat 13.6倍(第141)・逐次発行の罠2回=「バッチが基本・逐次は例外」。
- 時間依存(2026-09-01時点): **9/10 サーバー返却**(vLLM艦隊ベンチ+未踏用実測データ確保はそれまで)・**9/24 13:00 未踏アドバンスト下期エントリー締切**(書類9/25 13:00)。

## v2で引き継がないもの(意図的)

- rw-fetch-scheduler(v1の常駐タスク・8/30以降解除提案の対象)・freeze-provisional(本選前の話)・hackathon-hardware(本選環境の話)・v1のconf/実装キー類(v2はゼロベース)。
