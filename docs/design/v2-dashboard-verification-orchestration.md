# v2忠実度計器盤・検収戦略・実験オーケストレーション設計書(R14・v1・決定項G-1〜G-9)

> **状態: v1・決定(仮・2026-09-08・ユーザー「G-1〜G-9の承認」)。全項は仮=変更可。**
> 根拠: [v2-dashboard-verification-orchestration-research.md](../research/v2-dashboard-verification-orchestration-research.md)(親一次確認: TRACE 8要素・hmer実行不能度/NROY/I≤3・AgentSociety mlflow・Generative Agents評価数値)。
> 既決との接続: 方法論(Phase 0-5・パターン台帳ゲート・世界被覆指標WC-1〜6・識別テスト=診断扱い)・パターン台帳(強/弱・holdout/較正の割当・封印行S1-S3)・予算宣言(P/M/S/L・運用規則)・知覚契約書§7(運用診断行5本)・§8(指標B=JSD帰無参照・ablation事前登録)・運用設計書U8(manifest 13節・再現性三層・T1-T9)・実装計画書§9(工程C0-C8の検収列)・決定台帳§8b/§10b(実験=一級オブジェクト・k*事前宣言・多ラン=検定力)。

## §1 決定項

### G-1 計器盤の3面構成(ゲートと報告の分離)
- **推奨**: 計器盤を3面に分け、**ゲート(合否)は面2のみ**に置く。
  - **面1 較正面**(TRACE 6 model output verification): 較正に使ったアンカー(台帳の較正割当行・「生成に使用」層)の再現度。**報告のみ・合否線なし**(良くて当たり前)。
  - **面2 holdout面**(TRACE 8 model output corroboration): 封印行S1-S3・holdout割当行(KDDI形状5指標・スクランブル通行量・訪日指標等)の再現度。**k*事前宣言はここにのみ書く**。判定は**ラン単位でなくアンサンブル単位**。
  - **面3 運用面**(SRE 4シグナル): 知覚契約§7の診断行5本+呼数/秒・失敗率・繰り延べ滞留・RSS・保存則残差・介入回数(=0)・unsafe率。**赤=症状(ランが壊れている)のみ・actionableでないアラートは置かない**。
- 原則: 面1・面2の乖離は「原因」であり赤にしない(観察)。面2の不合格は「落ちたら不合格・通っても合格とは言わない」(SBCの片側性)を見出しに明記し、世界被覆指標WC-1〜6と併読する。
- expedient: 面の分け方(ABM文献に明文例なし=v2独自宣言)。

### G-2 面2の合否形式=実行不能度(History Matching)
- **推奨**: 各holdoutアンカー i について `I_i = |mean_ens(y_i) − z_i| / sqrt(Var_ens(y_i) + Var_obs(z_i) + Var_disc(i))` を計算し、**I_i ≤ 3 を合格(Pukelsheim 3σ≒95%・mechanism)**、全アンカーの最大値 I_M=max_i I_i を面2の見出し値にする。Var_ens=アンサンブル分散(seed群)、Var_obs=観測誤差(台帳の出典から・不明ならexpedient宣言)、Var_disc=モデル不一致項(初回0=expedient・ablationで学習)。
- 帯(band)型アンカー(上界・下界)は片側実行不能度に読み替える。強/弱アンカーは Var_disc に重みを置かず**強=個別に合格必須・弱=I_M計算に含めるが単独では落とさない(POMの「弱いパターンを束ねる」)**。
- k*の事前宣言=(アンカー集合・I≤3・Var各項の出所・アンサンブル本数)をリポ内の凍結ファイル(SHA)に置く(ADEMP-PreRegの5見出しに写す・外部OSF登録は任意)。
- 指標B(JSD帰無参照)・OASIS型NRMSE・EconAgent型「符号一致」は**面1/面2の補助指標**として並置(符号一致は弱アンカーの最小ゲート形式)。
- 代替案(不採用理由): 固定の許容誤差±X%(観測誤差もアンサンブル幅も無視する・アンカーごとに恣意的)。

### G-3 検収戦略=TRACE 8ブロックを工程別受入基準表に写像
- **推奨**: 実装計画書§9の各工程の検収列を、TRACEの8要素に対応づけて正典化する。

| TRACE要素 | v2の対応物 | 受入基準の形 |
|---|---|---|
| 1 Problem formulation | 決定台帳・研究質問1文 | パターン台帳ゲート1行が書けること(既決) |
| 2 Model description | 各設計書(ODD相当) | 設計書の節が埋まり、expedient登録簿が最新 |
| 3 Data evaluation | ライセンス台帳+アンカー台帳の出典列 | 出典URL実読+主要数値の親再計算(CLAUDE.md §5) |
| 4 Conceptual model evaluation | mechanism/expedientタグ+感度試験 | expedientが結果を駆動していない証明 |
| 5 Implementation verification | pytest二段CI+U8テストT1-T9+実データ規模退化検査 | 全緑 |
| 6 Model output verification | 計器盤 面1 | 報告のみ |
| 7 Model analysis | ablation第1陣/第2陣・感度試験 | 事前登録したablationの完了 |
| 8 Model output corroboration | 計器盤 面2 | k*(I_M≤3)の判定 |
- 各工程の出口で「どのTRACE要素が更新されたか」を devlog に1行書く(TRACEのモデリング・ノート思想)。
- **verification ≠ validation(第203 追加・出典 D-75 (b)=Larooij & Törnberg 2025, Artificial Intelligence Review 59(1) 15「内部整合性は verification であって validation ではない」・提言(ii) の逐語「pre-registered experimental benchmarks, rather than face-validity alone」)**: **T2-c(テープ再生・checkpoint 自己整合)のハッシュ一致は verification(内部整合)であって validation ではない**。受入表の各行は **主観 / 客観(外部データ)/ 内部整合** のどれかを明示する(TRACE 5=内部整合・TRACE 6/8=客観・face validity=主観)。受入報告の見出しに「PASS n/m」だけを書かず、**種別ごとの内訳**を併記する。
- **現行 C7 受入表 16 行の仮分類(第203・提案=親が確定。行名は `docs/bench/c7/accept_c7-day-4/c7_accept.md` のもの)**:

| 行 | 項目 | 種別 | なぜその種別か |
|---|---|---|---|
| W1 | 壁時計/シミュ日 | 内部整合 | 予算宣言 W1(≤24 h/シミュ日)との突合。外部データを見ていない |
| M8 | RSS 総額(1ラン) | 内部整合 | 予算宣言 M8 との突合 |
| S1 | 恒久記録(出力バイト) | 内部整合 | バイト予算 S1 との突合 |
| P2 | 移動+密度[ms/tick] | 内部整合 | 性能予算 P2 との突合(40万体の行が無く現状は参考値) |
| L4 | LLM 呼数(シミュ日) | 内部整合 | 制御目標 L4 との突合 |
| T2-a | 5,000体 同seed 再ラン一致 | 内部整合 | 再現性の検査(verification) |
| T2-b | 40万体 先頭K tick 部分再ラン一致 | 内部整合 | 同上(現状 未判定) |
| T2-c | 40万体 checkpoint 自己整合 | 内部整合 | **本規律の名指し例**=ハッシュ一致は内部整合であって validation ではない |
| DIAG | 診断行(繰り延べ/昇格/縮退/抑止) | 内部整合 | 計器の存在検査(T9)。値の妥当性は見ていない |
| CONS-1 | 保存則(Σmoney+Σrevenue+Σ運賃 不変) | 内部整合 | エンジンの不変量。外部データと突き合わせていない |
| CONS-2 | 日次センサス ゲート(残差・純資産=実物資産) | 内部整合 | 会計の整合(残差 0) |
| CONST-5 | 憲法5 のビルド時検査 | 内部整合 | 静的検査 |
| WC-6 | 世界被覆 孤児(reaches宣言あり∧実読0) | 内部整合 | 宣言と実装の突合 |
| WC-5 | 世界被覆 過剰 X | 内部整合 | 前ランとの比較(報告のみ・絶対の合格線なし) |
| HOLD | KDDI 形状5指標(事後1回) | **客観(外部データ)** | 封印 holdout(KDDI 在圏データ)との照合=**この表で唯一の validation 行**。現状「未照合」 |
| SEAL | manifest の開封記録 | 内部整合 | 手続きの記録であって照合そのものではない |

  内訳: **客観(外部データ)1 / 内部整合 15 / 主観 0**。**主観 0** は face validity をゲートに使っていないこと(Larooij の母集団=35本中15本が主観のみ、に対する位置どり)を示す一方、**客観は HOLD の1行だけで、しかもまだ未照合**=現行の「判定済み 11/16・PASS 11」は**すべて verification** である。この内訳が変わるのは holdout 開封(事前登録 `docs/bench/c7/prereg_arms_v1.md`)の後だけ。

### G-4 実験の型: EnsembleSpec と SweepSpec
- **推奨**: run manifest(U8)に実験型を2つ追加する。**EnsembleSpec**=同一パラメタでseedのみ変える(不確実性の測定・面2の判定単位)。**SweepSpec**=パラメタ/expedientを変える(感度・ablation・直積または明示組)。k*の判定はEnsembleSpecに対してのみ定義。
- ラン定義の最小要素(BehaviorSpaceに準拠): 掃引変数×repetitions×reporters(面1/面2の指標のみ)×stop条件×setup/go。
- expedient: 2型に分けること自体(Covasim MultiSimのreseed既定の教訓から)。

### G-5 seedと並列の規律
- **推奨**: `seed = blake3(manifest_sha256 ‖ run_index)`(決定的写像・BehaviorSpaceのrun番号→seedイディオムのハッシュ版)。OS乱数・暗黙seedを禁止し、U8テストに「同一(manifest, run_index)で状態ハッシュ一致」「異なるrun_indexでRNG状態が衝突しない」を追加(並列時の状態衝突はNetLogo公式が警告)。
- 出力は**逐次書き出し**(Parquet日次+journal)を既定にし、終了時一括書き出しを禁止(中断耐性)。

### G-6 再開と完了済みラン表
- **推奨**: `(manifest_sha256, run_index)` を主キーとする**完了済みラン表**(Parquet)を持ち、再開=未完了indexの再投入。checkpoint(6時間毎)から途中再開(Ray Tune型)。失敗ランは自動で1回再投入し、2回目失敗は診断行へ(Snakemake/Nextflowの自動リトライ相当)。
- 実装コスト最小の形としてワークフローエンジンは導入しない(expedient・必要になれば Snakemake を検討)。

### G-7 実験追跡基盤
- 選択肢: (a) mlflow Tracking(AgentSocietyが採用・集中サーバ・親確認済み) (b) 自前ラン表(Parquet)+DuckDB(実装計画書§5の既決スタックのみ)。
- **推奨(b)**。理由: 記録系は既に manifest・テープ・Parquet・DuckDB で閉じており、サーバを1つ増やす利得が小さい。mlflowはPhase 5(多ラン・複数マシン)で必要になったら**閲覧用アダプタ**として後付け(ラン表→mlflowへ書き出す片方向)。expedient: 自前ラン表のスキーマ。

### G-8 アンサンブル計器
- **推奨**: 面2に **CRPS**(予測分布と実測点の距離・reliability/resolution分解)と **spread-skill ratio**(アンサンブル幅/RMSE・≈1が目安)を常設。「ランを増やせば良くなる」ではなく「幅が正しいか」を測る自己点検。レイアウトはECMWFスコアカード様式(行=アンカー・列=時間解像度・セル=有意差の色)。ECMWF原文は未読=様式はexpedient。
- ラン本数の根拠: Monte Carlo標準誤差から逆算(Siepe et al. 2024の式=未確認→確認までは「初回=seed群8本・spread-skillで再評価」のexpedient)。
  **→ 第205(2026-09-17・ユーザー決定「3 seed で確定」)**: 初回の seed 群は **3 本**(c7-day-4 構成 × seed 1/2/3)。根拠=seed 1/2 の実測(在圏の時刻別 CV(n=2) 中央値 0.0038・最大 0.0325=深夜)と L-B 答申 §5 の N=(CV/r)²(深夜を 2% で言うのに 2.6 本)。「8 本」は撤回(expedient を実測で置換・§3 の登録簿も同じ)。帰無参照は seed 間の実測 JSD(エリア別 24h シェア 0.000162 bits)に置く。事前登録 [prereg_arms_v1.md](../bench/c7/prereg_arms_v1.md) §6 v1.2。
- **報告様式=分布(第203 追加・出典 D-75 (a)=Li & Tao 2026「Not (Yet) Sufficient」arXiv 2603.00113 §4 Action 3 の逐語「reported as distributions (e.g., uncertainty intervals and variance decomposition) rather than selected trajectories」+ Larooij & Törnberg 2025, Artificial Intelligence Review 59(1) 15 の提言(iii) の逐語「results reported across multiple runs and, where feasible, limited sensitivity checks for key parameters.」)**: 面1・面2・面3 のいずれも、結果は**不確実性区間+分散分解(seed 間 / 条件間)**の形で報告し、**選んだ1軌跡で出さない**。分散分解は最低 2 成分(seed 間=同一構成の反復・条件間=腕/パラメタの差)に分け、腕の差は「条件間の分散が seed 間の分散を超えているか」で述べる(C8 の帰無参照=T7 seed 違いの JSD と同じ考え方)。**適用は S1 の 8 seed 以降**——それ以前の単一 seed の値は「分布ではない」と明記して出す(現行の C7 受入表・C8 ablation 第1陣の seed 1/2 はここに当たる)。追加費用は無い(報告の形だけ)。

### G-9 面3(運用)の警報規律
- **推奨**: SREの規律を転用。(1)赤は症状のみ(保存則残差超過・介入回数≠0・繰り延べ滞留がL6超・RSSがM8超・LLM失敗率がしきい値超) (2)通知3階級(page=ラン停止/ticket=次工程で対処/log=見るだけ) (3)すべての赤にactionable な対処手順を紐付ける (4)1tickの外れ値でなく**バーンレート**(窓内の累積超過)で判定。
- 4ゴールデンシグナルの写像: Latency=呼のTTFT/e2e・Traffic=呼数/秒・Errors=書式/接続/タイムアウト率・Saturation=in-flight/L6・RSS/M8・GPU KV使用率。

## §2 診断行・テスト(本書分)
- 面2の事前登録ファイル(SHA)がmanifestに記録されていること(T10)。面2の判定がアンサンブル単位で行われること(単一ランで合否を出したら失敗)。seed写像テスト(G-5)。完了済みラン表の再開テスト(中断→再開で状態ハッシュ一致)。面3の赤に対処手順が存在すること(静的検査)。

## §3 expedient登録簿(本書分)
3面の分け方/Var_disc初回0/観測誤差不明時の宣言値/EnsembleSpec・SweepSpecの2型/ワークフローエンジン不採用/自前ラン表スキーマ/スコアカード様式/初回seed群8本(→第205 で 3 本に実測置換)/面3のしきい値。

## §4 空欄(未確認)
Augusiak 2014要旨・Siepe 2024の反復回数式・ECMWF原文・History Matching for ABM(2501.00616)・LLMエージェント評価サーベイ(2507.21504)・2022年評価記述標準プロトコル。
