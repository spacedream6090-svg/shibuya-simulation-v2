# 決定台帳 → 根拠答申 対応表(D-83 ④)

> 作成 2026-09-17(文書サブ・Web 不使用・既存ファイルの編集なし)。
> 目的: [決定台帳](v2-redesign.md) §9 の DECIDED 行 **95 行**それぞれについて、**どの答申が根拠か**を一覧にする。
> 背景: [リサーチ反映の監査](../research/v2-research-reflection-audit.md)・[同 P1/P2](../research/v2-research-reflection-audit-p1p2.md) が
> 「**答申 → 決定**は辿れるが、**決定 → 答申**が辿れない」を穴として挙げた(D-83 ④)。本書は親が決定台帳に「根拠答申」列を足すための素材。
> **本書は台帳を書き換えない**。台帳の行・状態・日付は一行も触っていない。
> 答申ファイルはすべて `docs/research/` 直下(本書からは `../research/<名>.md`)。索引は [INDEX.md](../research/INDEX.md)・[lit/README.md](../research/lit/README.md)。

## 0. 対象と辿り方

**対象** = `v2-redesign.md` の L371-L467(§9 決定台帳の表)。ヘッダ+区切りを除く **L373-L467 = 95 行**。
表の形式は `| # | 議題 | 状態 | 決定内容 | 日付 |`。本書の「台帳行」列はその**行番号**(2026-09-17 時点の `v2-redesign.md`)。

**使った索引・証跡(この 4 つだけ。推測では埋めていない)**

1. **決定行の本文**が名指しする答申(`[v2-xxx-research.md](../research/…)` リンク・「根拠=」「答申」の語)。
2. **根拠設計書の冒頭「根拠:」行**(例 `v2-cognition-design.md:4`・`v2-action-contract.md:5`・`v2-implementation-plan.md:4`・`v2-perception-contract.md:5`・`v2-pattern-ledger.md:6`・`v2-world-process-design.md:5`・`v2-budget-declaration.md:6`・`v2-bench-plan.md:4`)。
3. **[反映監査 P0](../research/v2-research-reflection-audit.md) §2 の「設計」列**(`DECIDED「X」` の形で台帳行 ID を名指ししている)。
4. **[反映監査 P1/P2](../research/v2-research-reflection-audit-p1p2.md) §2 の「根拠」列**(`v2-redesign.md:NNN` の形で**行番号**を名指し。行番号が現行ファイルと一致することを L423=D1′ ほかで確認した。なお [batch1](../research/v2-r23-primary-check-batch1.md)・[batch2](../research/v2-r23-primary-check-batch2.md) の行番号は**古い版のもの**なので、名前(DECIDED「X」)だけを使った)。

**やっていないこと**(範囲外・親の仕事): 設計書の数値 → 答申 → 原典の 2 段突合(**写し検査**)。
ただし作業中に**決定行と答申・監査・索引の記述が食い違う行**が見つかったものは「写し」列に ★ を立て、§5 に全部並べた。

## 1. 「根拠の型」と「等級」の判定規則

| 型 | 判定規則 |
|---|---|
| **答申あり(親確認済)** | 根拠答申の少なくとも 1 本が **A 等級**、または答申ヘッダに「**親確認 N 件**」、または**決定行そのもの/根拠設計書の「根拠:」行に「親(一次)確認(済み)」「親検収」「親検算」「親再計算」と明記**されている |
| **答申あり(親未確認)** | 答申は特定できたが、上の親確認の痕跡が無い(B/C/D/E 等級のまま) |
| **v1 資産・実測** | 根拠が**親自身の測定・ベンチ・コード監査**(答申でない)。`docs/bench/`・`v2-audit-contradictions.md` など |
| **ユーザー直感・設計判断(expedient)** | 根拠が**ユーザー言明・工程判断・親の構成**で、答申の裏づけが決定行にも設計書にも無い |
| **不明(辿れない)** | 上の 4 つのどれにも落ちない。原典が本リポの外(v1 セッション)にある場合を含む |
| **不明(循環)** | 後発答申が根拠に「※既存答申 X」と書くだけで、X が **D 等級**(= 出典 URL ゼロ)。CLAUDE.md §5 の循環参照検査 |

**等級**は [INDEX.md](../research/INDEX.md) §0 の 5 値(A=親検収済 / B=出典あり空欄明示 / C=出典あり空欄未整理 / **D=出典 URL なし**=一次確認が丸ごと残る / E=出典不要)。
**D 等級を根拠に新しい決定をしてはいけない**(INDEX §1)。本書では D のみを根拠とする行を §3-2 に別立てした。

## 2. 対応表(95 行)

| 台帳行 | 行 ID | 日付 | 要旨(≤40字) | 根拠答申(ファイル名・節) | 一次確認等級 | 根拠の型 | 写し |
|---|---|---|---|---|---|---|---|
| L373 | 1 | 08-28 | 多ラン並列>高速化>範囲拡大・v1 互換は縛らない | — (ユーザー言明+`perf/engine-parallel 999694e` 実測) | — | ユーザー直感・設計判断(expedient) | |
| L374 | 1b | 09-08 | 監査28件・根本原因3本を後続決定で解消 | `v2-audit-contradictions.md`(親のコード監査・答申ではない) | — | v1 資産・実測 | |
| L375 | 2 | 08-28 | クラウド都度借り+可搬性最優先 | — (ユーザー決定) | — | ユーザー直感・設計判断(expedient) | |
| L376 | 8b | 09-08 | 実験オーケストレーションは R14 へ委譲 | v2-dashboard-verification-orchestration-research G-4/G-6/G-7 | **A** | 答申あり(親確認済) | |
| L377 | 3 | 09-08 | アーキ原則=実装計画書 §1-§4(SoA・単一書込口) | v2-implementation-stack-research(`v2-implementation-plan.md:4`「親一次確認済み」) | B+親確認 | 答申あり(親確認済) | |
| L378 | 4 | 09-08 | 物理コア=NumPy/Numba+Warp・移行条件宣言 | v2-implementation-stack-research §GPU / 傍証 v2-learned-simulation-research・v2-world-model-relation-research(P1P2 監査 2-44/2-45 が L378 を名指し) | B+親確認 / **D** / **D** | 答申あり(親確認済) | ★ |
| L379 | 5 | 09-08 | 認知層接続=認知設計書v1+行動契約書v1 | v2-cognition-detail-research(`v2-cognition-design.md:4`)・v2-persona-dynamics-research(同 :77)・v2-action-conversation-contract-research(`v2-action-contract.md:5`) | B+親確認 ×3 | 答申あり(親確認済) | |
| L380 | 6 | 09-08 | データ契約=知覚/世界データ/運用の3契約 | v2-perception-u17-research ほか(`v2-perception-contract.md:5`)・v2-world-data-build-research + -round2・v2-run-manifest-concurrency-research | B ×4(知覚側に親確認) | 答申あり(親確認済) | |
| L381 | 7 | 09-08 | 検収戦略(工程別受入基準)は R14 へ委譲 | v2-dashboard-verification-orchestration-research G-3(TRACE 8要素) | **A** | 答申あり(親確認済) | |
| L382 | 8 | 08-30 | v1 積み残しは台帳の門前条件を通ったものだけ | v2-pattern-ledger-deep-research(運用8条 → `v2-pattern-ledger.md:6,10`) | **D** | 答申あり(親未確認) | |
| L383 | RQ | 08-30 | 研究質問1文(探索型・台帳が具体化) | — (`v2-methodology.md` Phase 0 ゲート・`v2-decision-agenda.md` D1) | — | ユーザー直感・設計判断(expedient) | |
| L384 | Git | 08-30 | 新規リポで進める・v1 は参照専用 | — (ユーザー決定) | — | ユーザー直感・設計判断(expedient) | |
| L385 | 4b | 08-30 | 三層世界方式を採用+修正3点 | 決定行は「リサーチ答申(08-29)」とだけ書き**答申名が無い**。P1P2 監査 2-17 が L385 を v2-institutions-deep-research に紐付け(Project Sid・Concordia) | **D** | 答申あり(親未確認) | ★ |
| L386 | FE | 08-31 | ゲームは作らず3D/VR産業の技術知見を輸入 | v2-game-frontend-research・v2-game-tech-import-research | **D**・**D** | 答申あり(親未確認) | |
| L387 | ADV | 08-30 | アドバイザー3レーン・本選後にアクション | — (ユーザー決定。v2-funding-deep-research への参照は決定行に無い) | — | ユーザー直感・設計判断(expedient) | |
| L388 | 5 | 08-31 | 認知3層 T0/T1/T2+「言葉は必ず心を通る」 | **特定できず**。決定行・`v2-cognition-design.md`(根拠=09-06 の cognition-detail)いずれも 08-31 時点の出所を書いていない | — | **不明(辿れない)** | |
| L389 | 6 | 08-31 | データ契約=案(b)新スキーマ+3ストリーム | v2-data-contract-research(P1P2 監査 2-41 が L389 を名指し) | **D** | 答申あり(親未確認) | |
| L390 | U13 | 09-01 | 統合設計図スライド14枚を公式全体像に | 決定行に答申名なし。中身は v2-coupled-adaptation-deep-research(適応3ループ 1:5:25)・v2-observation-projection-deep-research(L-OBS/L-REC・R0-R6)= batch1 §1「名前なしで中身だけ入っている」 | **D**・**D** | 答申あり(親未確認) | ★ |
| L391 | W | 09-01 | 世界過程モジュール新設・台帳世界側4-5割・憲法5精密化 | 決定行が「**詳細文面は v1 側議論が原典**」と明記=本リポに原典なし | — | **不明(辿れない)** | |
| L392 | U1 | 09-01 | 記憶=(c)ハイブリッド・昇格要約のみ埋め込み | v2-memory-retrieval-research(P1P2 監査 2-8 が L392 を名指し) | **D** | 答申あり(親未確認) | |
| L393 | U2 | 09-01 | 習慣初期値=ペルソナseed+expedientタグ | v2-memory-retrieval-research(監査 2-8・L393)。「習慣化中央値66日」は v2-cognition-detail-research / v2-persona-dynamics-research にも | **D**(+B) | 答申あり(親未確認) | |
| L394 | U3 | 09-01 | タグ付きイベント索引+checkpoint時間スライス | v2-game-frontend-research(監査 2-1・§3 次点が L394 を名指し) | **D** | 答申あり(親未確認) | |
| L395 | U4 | 09-01 | L-OBS/L-REC は Phase 4 以降の観測アプリ | v2-observation-projection-deep-research(監査 2-20)・v2-capabilities-business-research(2-42) | **D**・**D** | 答申あり(親未確認) | |
| L396 | U5 | 09-01 | スマートオブジェクト広告+utility スコアリング | v2-game-tech-import-research #5(監査 2-5・L396) | **D** | 答申あり(親未確認) | |
| L397 | U6 | 09-01 | 認知 LOD の on-demand 昇格を採用 | v2-game-tech-import-research #4(監査 2-5・L397) | **D** | 答申あり(親未確認) | |
| L398 | U7 | 09-01 | チャンクSoA+空間グリッドを共通基盤に | v2-game-tech-import-research #2(監査 2-5・L398) | **D** | 答申あり(親未確認) | |
| L399 | 線引 | 09-01 | エンジン/LLM 線引き16行表の方針確認 | v2-engine-llm-boundary-research(`v2-world-process-design.md:5`「根拠: 線引き答申」・batch1 §1) | **D** | 答申あり(親未確認) | |
| L400 | BM | 09-01 | ベンチマーク台帳の構造を承認 | v2-benchmark-standards-research(`v2-deep-research-program.md:30`「ベンチマーク答申の5層構造」) | **D** | 答申あり(親未確認) | ★ |
| L401 | U12 | 09-01 | パターン台帳34行・強5本・運用8条 | v2-pattern-ledger-deep-research(`v2-pattern-ledger.md:6`「原資料: 答申U-D」) | **D** | 答申あり(親未確認) | ★ |
| L402 | 流入 | 09-01 | 来街は較正つまみでなくエージェント判断 | — (ユーザー言明) | — | ユーザー直感・設計判断(expedient) | |
| L403 | 予算 | 09-01 | 予算宣言表(壁時計・物理・個体・RSS ほか22項) | v2-llm-serving-deep-research(`v2-budget-declaration.md:6` 名前呼び)。L2 の根拠欄は「**方法論答申**」とだけ書かれ答申名が無い(同 :58) | **D** | 答申あり(親未確認) | ★ |
| L404 | P0 | 09-01 | Phase 0 ゲート通過(台帳+予算+研究質問) | — (L401/L403/L383 の合成・工程判断) | — | ユーザー直感・設計判断(expedient) | |
| L405 | R2 | 09-01 | 世界過程=3類限定・レジストリ一元・線引き原則7本 | v2-engine-llm-boundary-research(`v2-world-process-design.md:5`) | **D** | 答申あり(親未確認) | |
| L406 | D-R2-1 | 09-02 | 営業時間=層2/運行はLLM乗務員/治安体感は置かない | — (ユーザー方針。決定行に答申名なし) | — | ユーザー直感・設計判断(expedient) | |
| L407 | W1改訂 | 09-02 | 壁時計 ≤24h/シミュ日へ緩和(8h は努力目標) | 親の3段ベンチ実測(`bench_ledger` 190行) | — | v1 資産・実測 | |
| L408 | 保存則 | 09-02 | 取引保存はエンジン強制・閉鎖系は要求しない | v2-ugc-platform-import #26(EVE Active ISK Delta・UO 教訓) | B | 答申あり(親未確認) | |
| L409 | D-R2-2 | 09-02 | 台帳1つ・レコード型3つ・関係4本・分類軸4本 | v2-world-ledger-verification(監査 2-27 が L409 を名指し) | B | 答申あり(親未確認) | |
| L410 | D-R2-1-2追補 | 09-02 | 指令エージェント=revises・役割知識から自然発生 | — (ユーザー条件2点) | — | ユーザー直感・設計判断(expedient) | |
| L411 | UGC | 09-02 | UGC答申を正典化(輸入26提案/移入禁止9件) | v2-ugc-platform-import(監査 2-26 が L411 を名指し) | B | 答申あり(親未確認) | |
| L412 | 着手方針 | 09-02→03 | 計画を綿密に立ててから実装(ほぼ全決定後) | — (ユーザー言明) | — | ユーザー直感・設計判断(expedient) | |
| L413 | R3-1 | 09-02 | 構造化観測+決定論的可視性が知覚の正典・VLA不採用 | v2-perception-u17-research(`v2-perception-contract.md:5`)・v2-ugc-platform-import #12(Replication Graph 5ノード・監査 2-26 が L413 を名指し) | B・B | 答申あり(親未確認) | |
| L414 | R3-2 | 09-02 | 内受容3変数を第1陣・閾値割れ時のみ注入 | v2-perception-u17-research(Humanoid Agents・実装順) | B | 答申あり(親未確認) | ★ |
| L415 | R3-3 | 09-02 | 看板=「届く」対象・実行時OCR不採用 | v2-perception-u17-research(OCR・スケーリング則反転)・v2-vlm-reality-check-research | B・B | 答申あり(親未確認) | |
| L416 | 広告 | 09-03 | 注意ゲート4段・既定は非注入・AD1 を S3 封印行に | v2-ad-information-research(決定行がリンク) | **C** | 答申あり(親未確認) | ★ |
| L417 | 人物観測 | 09-03 | 人物観測5段+聴覚統合(M1-M5) | v2-person-perception-verification(監査 2-25 が L417 を名指し) | B | 答申あり(親未確認) | |
| L418 | R3-4 | 09-03 | 嗅覚は保留(台帳の対応行が作れない) | v2-perception-u17-research(実装順=内受容→騒音→会話傍受→嗅覚) | B | 答申あり(親未確認) | |
| L419 | R3-5 | 09-03 | 可視性格子 2.5m 正典・M10 ≤512MB・2解像度分離 | v2-world-data-build-research(監査「DECIDED R3-5」)・v2-cell-granularity-research(100m 凍結) | B・B | 答申あり(親未確認) | |
| L420 | R3-7 | 09-03 | 騒音3層・可聴半径は密度の関数(Lombard 不動点) | v2-density-hearing-verification・v2-hearing-numbers-and-d1-coverage・v2-perception-u17-research・v2-person-perception-verification M1 | B ×4(決定行に**親一次確認**の逐語=消防法/NFPA/ISO/Brungart) | 答申あり(親確認済) | ★ |
| L421 | R3-6a | 09-03 | VLM/CV は測定装置・標本を60/20/20分割 | v2-vlm-reality-check-research(決定行がリンク・監査 2-33 が L421 を名指し) | B | 答申あり(親未確認) | |
| L422 | R3-6b | 09-03 | 識別テストはゲートに置かない・陽性対照のみゲート | v2-turing-test-validation-research(決定行がリンク) | B | 答申あり(親未確認) | |
| L423 | D1′ | 09-03 | D1 を KDDI 滞在人口へ差し替え・強維持 | v2-d1-reacquisition(決定行がリンク・**親検算**)・v2-benchmark-standards-research(FHWA 式=許容誤差は実測の自然変動)・v2-llm-mobility-research §5-2(フロア併記) | B(親検算)・**D**・**D** | 答申あり(親確認済) | |
| L424 | SSB | 09-03 | 社会生活基本調査 匿名個票を取得する方向(**OPEN**) | v2-turing-test-validation-research(検定力の律速=SSB が突破口) | B | 答申あり(親未確認) | |
| L425 | R3-8(部分) | 09-03 | 知覚契約書v0 の未決 A-E に一部回答 | — (ユーザー回答+BN-1/BN-2 起動)。「非注意性盲目46%」の出所は決定行に無い(後発の v2-p-notice-research / v2-perception-timing-research がカバー) | —(後発 B) | ユーザー直感・設計判断(expedient) | ★ |
| L426 | R3-8(第2弾) | 09-03 | D1′=(b)expedient境界・100m+層分離・周期HB廃止・δ_perc | v2-area-boundary-definition(分割線3本)・v2-hearing-numbers-and-d1-coverage §②(ポリゴン非公開の確定)・v2-perception-latency-research(δ_perc 0.213s)・v2-perception-timing-research(周期HB廃止) | B ×4 | 答申あり(親未確認) | |
| L427 | BN-4/5 | 09-04 | セルアフィニティ不採用・契約書v1予算を実測確定 | 親のベンチ実測(台帳245行)+ v2-cell-granularity-research(軸の差し替え)・v2-person-perception-verification(L1-L3 キャッシュ3つの落とし穴) | B・B | v1 資産・実測 | |
| L428 | R3-8 §1 | 09-06 | 知覚の不変条件7条を確定 | — (ユーザー選択(a)・`v2-perception-contract.md` §1) | — | ユーザー直感・設計判断(expedient) | |
| L429 | 品質プローブv0 | 09-05→06 | モデル足切り測定・⑥は指標B採用 | 親自身の 513 呼測定(`docs/bench/quality_probe_v0/`)。v2-conversation-deep-research のチェックリスト8項を**置換**(監査 2-14) | **D**(置換元) | v1 資産・実測 | |
| L430 | R3-8 §2 | 09-06 | 固定2行形・B0=300・B4b独立・時刻5分丸め | v2-observation-format-research(監査「DECIDED R3-8 §2」) | B | 答申あり(親未確認) | |
| L431 | R3-8 §3 | 09-06 | p_notice 2段ヒル型・チャネル別上限・近接k・ΔSNR | v2-p-notice-research・v2-channel-budget-attention-research・v2-update-rules-hearing-research(決定行「**リサーチ3本を親が一次確認して提示**」) | B ×3+親確認 | 答申あり(親確認済) | |
| L432 | R3-8 §4 | 09-06 | 注意ゲート4段の数値(p_see 0.70・内容キャップ ほか) | v2-channel-budget-attention-research・v2-ad-information-research | B・**C** | 答申あり(親未確認) | ★ |
| L433 | R3-8 §5 | 09-06 | prefix 規約(変化率昇順・B0-B4 バイト一致) | v2-observation-format-research・v2-perception-timing-research・v2-ugc-platform-import #13・v2-llm-serving-deep-research | B ×3・**D** | 答申あり(親未確認) | |
| L434 | R3-8 §6 | 09-06 | 不応期・日次内省・繰り延べ4クラス・invocation distance | v2-update-rules-hearing-research・v2-perception-latency-research・v2-perception-timing-research §6/§9 | B ×3 | 答申あり(親未確認) | |
| L435 | R3-8 §7 | 09-06 | 予算 delta(P6/L4/L5/L6/M11/M12) | §3-§6 決定からの導出(v2-channel-budget-attention-research・v2-update-rules-hearing-research 経由) | B ×2 | 答申あり(親未確認) | |
| L436 | R3-8 §8 | 09-06 | 検証装置=ablation 第1陣6本/第2陣7本+指標B事前登録 | **答申名なし**(優先式「expedient量×駆動可能性÷コスト」は親の構成) | — | ユーザー直感・設計判断(expedient) | |
| L437 | R3-8 §9 | 09-06 | 第1陣/第2陣の陣分けと完了条件 | **答申名なし**(工程判断) | — | ユーザー直感・設計判断(expedient) | |
| L438 | 着手方針(再確認) | 09-06 | 全て決めてから構築(未決ラウンドを加速) | — (ユーザー言明) | — | ユーザー直感・設計判断(expedient) | |
| L439 | 構築前の即決8項 | 09-06 | A1-A8(初回規模・モデル割当・言語・座標系・1分tick) | **決定行が「リサーチ不要の決定」と自認** | — | ユーザー直感・設計判断(expedient) | |
| L440 | B10/B11 | 09-06 | Swallow-8B 不採用・固定2行形は順守1.000 | 親のプローブ測定(`summary_b10_b11.md`)+ v2-legal-licensing-deep-research(Swallow=研究限定・監査 2-18) | **D** | v1 資産・実測 | |
| L441 | R4 | 09-07 | 行動契約12語・会話は1呼1発話ブロック・未定義5段 | v2-action-conversation-contract-research(`v2-action-contract.md:5`「親一次確認済み」) | B+親確認 | 答申あり(親確認済) | ★ |
| L442 | D-R2-3 | 09-07 | 世界過程16行の逐行決定(行5=A案・行6=最賃フロア) | v2-world-process-rows-research(決定行「**親一次確認済み**」)・v2-ugc-platform-import #14・v2-engine-llm-boundary-research | B+親確認・B・**D** | 答申あり(親確認済) | |
| L443 | U10 | 09-07 | 来街=案A+案C(方面別外界ノード+週次表+逸脱時LLM) | v2-boundary-economy-u10-u11-research・v2-boundary-deep-research・v2-llm-mobility-research §4 | B・**D**・**D** | 答申あり(親未確認) | ★ |
| L444 | U11 | 09-07 | 経済SFC 6部門・transfer 単一API・ex nihilo 禁止 | v2-boundary-economy-u10-u11-research・v2-economy-sfc-deep-research | B・**D** | 答申あり(親未確認) | ★ |
| L445 | D-R2-4〜6 | 09-07 | 憲法5確定文・第1陣/第2陣選定・状態成長宣言書式 | v2-world-process-inventory-research(監査「DECIDED D-R2-5 第1陣」「D-R2-6」) | B | 答申あり(親未確認) | |
| L446 | R5/U19 | 09-07 | δ_think レーン・T1思考0・昇格S(e)・ACT-R 記憶 | v2-cognition-detail-research(`v2-cognition-design.md:4`「親一次確認済み」)・v2-prediction-module-deep-research(監査 2-10) | B+親確認・**D** | 答申あり(親確認済) | |
| L447 | 母集団合成 | 09-07 | 7段手順+合否ライン・初回20,000体・holdout の掟 | v2-population-synthesis-research(決定行「**親再計算一致**」)・v2-persona-population-deep-research・v2-boundary-deep-research | B+親確認・**D**・**D** | 答申あり(親確認済) | ★ |
| L448 | 母集団合成(追補) | 09-07 | 初回本番40万体・週7日フル生成 | ユーザー指示(「実際の人数で回さないと分からない」「同じ日は決してない」)+ v2-population-synthesis-research | B | ユーザー直感・設計判断(expedient) | |
| L449 | 実装スタック | 09-07 | Python3.12+NumPy/Numba+Warp・Rust 移行条件を事前宣言 | v2-implementation-stack-research(`v2-implementation-plan.md:4`「親一次確認済み」)+ `docs/bench/engine_spike` | B+親確認 | 答申あり(親確認済) | |
| L450 | 世界過程拡張(R6) | 09-07 | U-Goods 新設・move_goods 単一API・検算2本 | v2-world-process-inventory-research(監査「DECIDED 世界過程拡張(R6)」) | B | 答申あり(親未確認) | |
| L451 | 世界被覆指標 | 09-07 | 5値ベクトル(C,Q,D,V,R)+過剰X+分母凍結 | v2-world-coverage-index-research(監査「DECIDED 世界被覆指標」。起点はユーザー提案) | B | 答申あり(親未確認) | |
| L452 | ペルソナ動態 | 09-07 | 3層・persona文不変・ドリフト予算7項・ablation A/B/C | v2-persona-dynamics-research(`v2-cognition-design.md:77`「親一次確認」) | B+親確認 | 答申あり(親確認済) | |
| L453 | 世界カタログv0.2 | 09-07 | 57クラスへ拡張・SHA 34f9fa9d で凍結 | v2-world-coverage-index-research + v1 資産の突合(組織・在庫補充・制度DSL ほか) | B | 答申あり(親未確認) | |
| L454 | U8/U9 | 09-07 | manifest 13節・二相コミット・Philox・乗車の意味論 | v2-run-manifest-concurrency-research(決定行がリンク)・v2-parallel-execution-deep-research・v2-implementation-stack-research(FLAME GPU 2 同型) | B・**D**・B | 答申あり(親未確認) | |
| L455 | 世界データ構築仕様 | 09-07 | W0-W20 と D-W1〜D-W22・§9 工程を承認 | v2-world-data-build-research・v2-world-data-build-round2-research(決定行に**親一次確認済み事実 F1-F15**)・v2-w7-law-primary-check-research | B・B・**A** | 答申あり(親確認済) | |
| L456 | R6 時間 | 09-08 | 時間の意味論を集約(**新規決定なし**) | 集約のみ(U9・知覚契約 §6・D-W10・D-W15・U10 由来) | — | ユーザー直感・設計判断(expedient・集約) | |
| L457 | R8 裁定判例 | 09-08 | 未定義行動5段+判例化(集約) | v2-action-conversation-contract-research(`v2-action-contract.md:5`)・v2-precedent-system-deep-research(監査 2-24) | B+親確認・**D** | 答申あり(親確認済) | ★ |
| L458 | R15 可視化 | 09-08 | 初回=計器盤WebUI+deck.gl 2D・GlassBox 規律 | v2-game-frontend-research(決定行がリンク) | **D** | 答申あり(親未確認) | ★ |
| L459 | R17 倫理・安全運用 | 09-08 | E-1〜E-7(Five Safes・U18 初回実装・審査不要3本立て) | v2-ethics-operations-research(決定行「**親確認**: CitySim/CityReal・PPC Q15-1・医学系指針・PoliSim」)・v2-content-safety-deep-research・v2-publication-ethics-deep-research・v2-legal-licensing-deep-research | B+親確認・**D**×3 | 答申あり(親確認済) | |
| L460 | R14 計器盤・検収・オーケストレーション | 09-08 | G-1〜G-9(3面・I≤3・TRACE・EnsembleSpec・seed群8本) | v2-dashboard-verification-orchestration-research(決定行「親確認: TRACE・hmer・AgentSociety mlflow・Generative Agents」) | **A** | 答申あり(親確認済) | ★ |
| L461 | 行5 追補 | 09-08 | H-1〜H-5(Calvo 業種別・k の水準・r クリップ) | v2-price-formation-llm-research(決定行「親確認: Fish v6・Higo–Saita 外食5.0%/月・金融庁飲食業編・EconAgent」) | B+親確認 | 答申あり(親確認済) | |
| L462 | R7 群衆物理(前倒し) | 09-08 | U15-1〜8(CFSM 第1候補・較正3段・検証6本) | v2-crowd-physics-research(決定行「**親検収**」・逐語つき)・v2-mobility-field-research(監査 2-9) | **A**・**D** | 答申あり(親確認済) | ★ |
| L463 | 着手ゲート | 09-08 | 残ラウンドは全決定・R16 のみ C5 前に持ち越し | — (工程判断・`v2-implementation-plan.md` §9.5) | — | ユーザー直感・設計判断(expedient) | |
| L464 | R16 T1/T2モデル選定・艦隊構成(U14) | 09-08 | T1=Qwen3-8B INT8/静的言語化=32B AWQ/自前vLLM 7×A5000 | v2-llm-serving-deep-research(`v2-bench-plan.md:4`「根拠: サービング答申」・艦隊構成A)・v2-legal-licensing-deep-research(Qwen3=Apache 2.0)+ 親の B10/B14/品質プローブ実測 | **D**・**D** | 答申あり(親未確認) | |
| L465 | 原則 行動はオブジェクトの affordance 由来 | 09-17 | 動詞を足さずオブジェクトの affordance で表す | v2-d71-vocab-growth-research(監査「DECIDED 原則 行動は…affordance 由来」) | B → **親確認 5 件(第204)** | 答申あり(親確認済) | |
| L466 | 到達点の順位(第182 の問い) | 09-17 | C(事業)を一位・過程で A と B の両方が必要 | — (ユーザー決定)。傍証 v2-capabilities-business-research(監査 2-42 が L466 を名指し) | **D** | ユーザー直感・設計判断(expedient) | |
| L467 | B14 | 09-07 | BATCH_INVARIANT=1 で不変性成立・コスト差なし | 親の測定(A5000 CC8.6・32/32 一致)+ v2-run-manifest-concurrency-research(「公式2ページで食い違う→自検証せよ」) | B | v1 資産・実測 | |

## 3. 集計

### 3-1. 根拠の型(95 行)

| 根拠の型 | 件数 | 割合 |
|---|---:|---:|
| **答申あり(親確認済)** | 22 | 23.2% |
| **答申あり(親未確認)** | 45 | 47.4% |
| **v1 資産・実測** | 6 | 6.3% |
| **ユーザー直感・設計判断(expedient)** | 20 | 21.1% |
| **不明(辿れない)** | 2 | 2.1% |
| **不明(循環)** | 0(行レベル)/ **1 項**(L441 の「声かけ応答率 0.8」) | — |
| 合計 | **95** | 100% |

**答申へ辿れた行 = 67 / 95 = 70.5%**。辿れない・ユーザー判断のみ = 22 行(23.2%)。

### 3-2. 「答申あり(親未確認)」の内訳 — **D 等級だけを根拠にする 18 行**

INDEX §1 は「**D 等級を根拠に新しい決定をしてはいけない**」と書いている。その規律に抵触している行:

L382(移行計画)・L385(4b 三層世界方式)・L386(FE)・L389(データ契約 案b)・L390(U13 統合設計図)・
L392(U1 記憶)・L394(U3)・L395(U4)・L396(U5)・L397(U6)・L398(U7)・L399(線引16行表)・
L400(BM)・L401(U12 パターン台帳)・L403(予算宣言表)・L405(R2 世界過程)・L458(R15 可視化)・L464(R16 モデル選定)

**18 行は全部 08-30〜09-01 の決定か、その時期の答申を後から引いた行**。INDEX §1 の「33 本は 2026-08-30〜09-01 のバッチ」と一致する。
うち **L385・L390・L399・L400・L401・L403・L405 の 7 行は「答申の名前が決定行に書かれていない」**(監査・設計書の脇道からしか辿れない)。

### 3-3. 日付別

日付は台帳の「日付」列(掃除で更新された行はその日付)。

| 日付帯 | 行数 | 親確認済 | 親未確認 | 実測 | ユーザー判断 | 不明 |
|---|---:|---:|---:|---:|---:|---:|
| 08-28〜09-01(Phase 0 まで) | 26 | **0** | 17 | 0 | 7 | 2 |
| 09-02〜09-04 | 22 | 2 | 14 | 2 | 4 | 0 |
| 09-05〜09-06 | 13 | 1 | 5 | 2 | 5 | 0 |
| 09-07〜09-08 | 32 | 18 | 9 | 2 | 3 | 0 |
| 09-17 | 2 | 1 | 0 | 0 | 1 | 0 |
| 合計 | 95 | 22 | 45 | 6 | 20 | 2 |

**含意**: 一次確認の規律(2026-09-03 の捏造申告事件 → CLAUDE.md §5)が入ったあとの 09-07〜09-08 の 32 行は **18 行が親確認済**。
逆に **08-28〜09-01 の 26 行は親確認済ゼロ**。憲法・三層世界・パターン台帳・予算宣言という**一番下の層が一番弱い**。

## 4. 親が優先して埋めるべき行(「不明」と「expedient」の全列挙)

### 4-1. 不明(辿れない)— **2 行・全件**

| 台帳行 | 行 ID | 要旨 | 辿れなかった理由 |
|---|---|---|---|
| L388 | 5 認知3層(案B′) | T0/T1/T2+「言葉は必ず心を通る」 | 決定行にも `v2-cognition-design.md` にも 08-31 時点の出所がない。09-06 の cognition-detail-research は**後から**根拠に据えられたもの |
| L391 | W 世界過程の補正3点 | モジュール新設・台帳世界側4-5割・憲法5精密化 | 決定行が「**詳細文面は v1 側議論が原典**」と明記。原典が本リポの外(v1 セッション記録) |

### 4-2. 不明(循環)— **1 項**

| 箇所 | 値 | 循環の形 |
|---|---|---|
| L441(R4)行7 会話 | **声かけ応答率 ≈0.8**(`ACCEPT_PROBABILITY = 0.8`) | 後発の B 等級答申 `v2-action-conversation-contract-research.md:335` が「較正目標=声かけ応答率 約0.8 **※既存答申U-F**」と書くが、U-F = `v2-conversation-deep-research.md` は **D 等級**(出典 URL ゼロ)。batch2 §2-2 #11 が「CA 文献に一致する値は**見つからない**」と確定。**一次は存在しない** |

### 4-3. ユーザー直感・設計判断(expedient)— **20 行・全件**

| 台帳行 | 行 ID | 要旨 | 埋まる見込み |
|---|---|---|---|
| L373 | 1 | 第一目標の優先順(多ラン並列>高速化>範囲) | ユーザー決定。答申で置換しない項 |
| L375 | 2 | クラウド都度借り=可搬性最優先 | 同上 |
| L383 | RQ | 研究質問1文(探索型) | `v2-methodology.md` Phase 0 ゲートに紐付けは可能。答申は無い |
| L384 | Git | 新規リポ・v1 は参照専用 | ユーザー決定 |
| L387 | ADV | アドバイザー3レーン | `v2-funding-deep-research`(D)がレーンの素材だが決定行が引いていない → **紐付けを足せる候補** |
| L402 | 流入 | 来街はエージェント判断 | ユーザー言明。U10(L443)が具体化 |
| L404 | P0 | Phase 0 ゲート通過 | 工程判断 |
| L406 | D-R2-1 | 営業時間/運行/治安体感の境界例 | 答申の裏づけ無しで 3 件決めている → **後発の world-process-inventory / -rows で埋まる可能性** |
| L410 | D-R2-1-2追補 | 指令エージェント=revises | 同上 |
| L412 | 着手方針 | 計画を綿密に立ててから実装 | ユーザー言明 |
| L425 | R3-8(部分) | 知覚契約書v0 の A-E 一部回答(非注意性盲目 46%) | **46% の出所を後発 p-notice / perception-timing 答申に紐付けられる** |
| L428 | R3-8 §1 | 不変条件7条 | ユーザー選択。7条自体は知覚契約書 §1 |
| L436 | R3-8 §8 | ablation 優先式・第1陣6本 | **優先式は親の構成=未リサーチ(expedient)** |
| L437 | R3-8 §9 | 第1陣/第2陣の陣分け | 工程判断 |
| L438 | 着手方針(再確認) | 全て決めてから構築 | ユーザー言明 |
| L439 | 構築前の即決8項 | A1-A8 | **決定行が「リサーチ不要」と自認**。A2(モデル割当)・A8(1分 tick)は後発答申で裏づけ可能 |
| L448 | 母集団合成(追補) | 初回本番40万体・週7日フル生成 | ユーザー指示。規模の根拠は無い |
| L456 | R6 時間 | 時間の意味論(集約・新規決定なし) | 集約行。個別決定に分解すれば全部答申へ紐付く |
| L463 | 着手ゲート | 残ラウンド全決定宣言 | 工程判断 |
| L466 | 到達点の順位 | C 一位・過程で A と B | ユーザー決定。capabilities-business(D)が傍証 |

## 5. 要写し検査(★)— 19 行

> ここは**本書の範囲外**(数値 → 答申 → 原典の 2 段は親の仕事)。作業中に「決定行の記述と、答申・監査・索引の記述が食い違う」のを見つけたものだけを並べる。

| 台帳行 | 行 ID | 食い違いの中身 | 出所 |
|---|---|---|---|
| L378 | 4 物理コア | §4 路線表の **ORCA-GPU 50万体33ms/30x(Charlton 2019, arXiv:1908.10107)・JAX MD 64k 10.5ms・WarpDrive 100x・FLAME GPU 2 Boids 8万体51ms** は `docs/research/` のどの答申にも出てこない(`1908.10107` のリポ内 grep ヒットは `v2-redesign.md:136` のみ)= **出所答申なしの数値が設計書に載っている** | 本書の grep |
| L385 | 4b 三層世界 | institutions 答申の**自己訂正**「『制度は役割知識だけでは自己実行しない(Sid の実証)』は強すぎる」が 4b 修正3 に**伝播していない** | P1P2 監査 2-17 |
| L390 | U13 統合設計図 | 適応3ループ 1:5:25・L-OBS/L-REC R0-R6 が**答申名なしで中身だけ**入っている | batch1 §1 注 |
| L400 | BM | 決定行は「構造承認」だが、batch1 の参照回数調査では benchmark-standards-research は**設計書から 0 回参照**(本文言及が `v2-deep-research-program.md:30` に 1 箇所だけ) | batch1 §1 |
| L401 | U12 パターン台帳 | 「**44本**」は答申の誤記で原本は **45行**。原本は v1 リポでなく Claude Code セッション記録側 | `v2-pattern-ledger.md:8` |
| L403 | 予算宣言表 | L2「ablation 20% 予約」の根拠欄が「**方法論答申**」とだけ書かれ、**答申ファイルが特定できない** | `v2-budget-declaration.md:58` |
| L414 | R3-2 内受容 | 日陰**係数 0.86**(Sci Rep 2022)を「台帳収載可能な現実整合アンカー」としているが、原典確認の記録が無い | 決定行 |
| L416 | 広告 | 根拠答申が **C 等級**(出典あり・空欄未整理)。「**LLM はナッジを 3-10 倍増幅(ABxLab 実測)**」の親確認なし。答申推奨③「スカラー変換を第一候補」は**未採用・理由の記録なし** | INDEX §0・P0 監査 2-2 #3 |
| L420 | R3-7 騒音 | 親の一次確認で **リプロシティ 10-100 倍=根拠なし・不使用**へ訂正済み。**神南 65-72dB(画像のみ)**・**区「音のめやす」88-99dB(測定距離未定義)**は不使用と明記。ISO 9921 の数表は **Annex 未読**で「0dB」設定が 3-7dB 保守的=契約書で −5dB へ調整候補、が未完 | 決定行 |
| L425 | R3-8(部分) | 「非注意性盲目 **46%**」を暫定値に採ったが、出所が決定行に無い | 決定行 |
| L432 | R3-8 §4 | **p_see 0.70 は非査読**(都内 VR アイトラ n=120)・**cpm 正典値未取得(expedient)**・中小媒体 0.14-0.40 は**英仏流用 expedient** | 決定行 |
| L441 | R4 | **声かけ応答率 0.8 の一次は存在しない**(§4-2 の循環)。`conversation.py:81-82` は「較正データ無しの定数・expedient」と直したが、`tools/c8/ablations_v1.json` に **0.8 の腕が無い** | batch2 §1-2・P0 監査 2-1 #3 |
| L443 | U10 | 答申の「**名簿 ≒100〜150万で在場40万を支える**」を採らなかった**理由の記録が無い**(W16 は名簿=在場=390,188) | P1P2 監査 2-13 |
| L444 | U11 | 保存則テスト 5 層のうち **T3(冗長方程式の毎期 assert)**が設計にも実装にも無い・**落とした記録も無い** | batch2 §4 E・P0 監査 2-1 #5 |
| L447 | 母集団合成 | 答申の「**世帯を主語に**」を採らず個人生成 → 世帯後付け。答申は後者を「劣る」としたが**理由の記録が無い** | P1P2 監査 2-23 |
| L457 | R8 裁定判例 | 計測項目は挙がるが、答申の「**判例誤ヒット率 ≤1%・裁定 κ≥0.6**」という**目標値が決定行に無い** | P1P2 監査 2-24 |
| L458 | R15 可視化 | 決定行が「既存答申(v2-game-frontend-research.md・**親検収済み**)」と書くが、INDEX の等級は **D**(出典 URL ゼロ)= **記載と等級の食い違い** | 決定行・INDEX §1・batch1 §1 |
| L460 | R14 | **G-8「初回 seed 群 8 本」**を、後発の **A 等級** `v2-replication-count-research` が「ABM/統計方法論の系譜では正当化できない(2〜3 桁不足)」と**否定**している=**訂正の伝播検査の対象** | v2-replication-count-research §3 |
| L462 | R7 群衆物理 | **C9 G13(物理は事前計算)で方針が変わり**、U15-1〜8 の設計が宙に浮いている(A 等級答申の実装率が最も低い理由) | P0 監査 §1-2・§1-3 |

## 6. 限界

- **行 ID の粒度**。台帳の 1 行が 5〜22 の決定項を抱える行がある(L439 の A1-A8・L459 の E-1〜E-7・L460 の G-1〜G-9・L455 の D-W1〜D-W22)。本書は**行単位**で型を付けたので、行の中の一部の項が別の型であることはある(例: L441 は行としては親確認済だが、0.8 の項だけ循環)。項単位が要るなら、P0 監査 §2 の判定表がすでにその粒度。
- **等級は INDEX の機械判定**(出典痕跡の総数)であり、答申の中身の正しさではない。INDEX §0 の但し書きどおり。
- **「親確認済」は痕跡の有無**であって、確認の網羅性ではない。L420(R3-7)のように、親確認済でもなお未確認の数値が残っている行がある。
- **辿れなかった理由の類型は 4 つ**: ①決定が**ユーザー言明・工程判断**で答申を持たない(20 行)②**答申名が決定行に書かれておらず**、監査・設計書の脇道からしか辿れない(7 行)③原典が**本リポの外**(v1 セッション記録・Claude Code セッション記録)にある(L391・L401 の 45 行原本)④根拠欄が**総称**(「方法論答申」「リサーチ答申」)で答申ファイルに落ちない(L385・L403)。
- L455 は台帳の行内に長文が入っており、**状態列と決定内容列の分かれ方が他の行と揃っていない**(日付列は 09-07 だが状態欄は 09-08)。親が列を足すときに気づく点。
