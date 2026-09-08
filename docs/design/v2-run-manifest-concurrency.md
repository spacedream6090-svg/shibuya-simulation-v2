# v2運用設計書(U8 run manifest・U9 並行実行の意味論・v1)

> **状態: v1・決定(仮・2026-09-07・ユーザー「U8,9の承認」)。全項は仮=変更可。**
> 根拠: [v2-run-manifest-concurrency-research.md](../research/v2-run-manifest-concurrency-research.md)(親一次確認: vLLM公式=batch invariance要件が8.0+と>=9.0で矛盾・TP時custom all-reduce無効化/Thinking Machines原典=決定的推論26→55秒/Lipari=EDFはU>1でdomino/FLAME GPU 2=bidding)+[v2-implementation-stack-research.md](../research/v2-implementation-stack-research.md)(sha256_cbor・cache_salt・httpx既定)。実測=B14(バッチ不変性の自検証・コスト差)を検証ランの前提に記録。
> 接続: 実装計画書§3-4・§7、知覚契約書§6(繰り延べアービタ)、行動契約書§2(失敗の意味論)、方法論(較正/holdout勘定分離・事前登録)。

## §1 U8 run manifest

### 1.1 位置づけ
ODD(モデル記述)とmanifest(実行記述)を分離し、manifestはODD文書と契約書をハッシュで参照する。**run_id=manifest正規化本文の自己ハッシュ**。

### 1.2 スキーマ(YAML・13節・必須欄)
| 節 | 欄 | 機械化される規則 |
|---|---|---|
| 同定 | schema_version・run_id(自己ハッシュ)・label・**mode**(smoke/calibration/holdout/ablation/production)・created_utc・tz | modeで勘定分離(L3) |
| 事前登録 | hypothesis(1文)・metrics・thresholds・ablation_id・sealed_at | 封印後の変更は新run_id(HARKing防止) |
| コード | repo・commit・describe・**dirty**・odd_doc{path,blake3}・contracts{perception,action}{path,blake3} | **dirty=trueは較正・holdoutに使えない(CI拒否)** |
| 設定 | fidelity_profile{name,blake3}・normalized_blake3・tick_seconds・n_agents・sim_days・start_sim_datetime | 比較ランは同一プロファイル必須 |
| 乱数 | master_seed・scheme=**numpy-philox4x64**・domain_table_version | 個体/LLMシードは導出(別欄に持たない) |
| データ資産 | [{id,version,blake3,bytes,records,license_row}]=OSM・PLATEAU・persona_pool・KDDI・可視性テーブル・駅出口・e-Stat | ライセンス台帳行と1対1 |
| holdout封印 | seal_scheme=D/S/P・layers[{name,member_hash,sealed_utc,opened}] | **mode≠holdoutでopened:trueがあれば起動拒否** |
| LLM艦隊 | engine{name,version,torch,cuda_driver,attention_backend}・env{VLLM_BATCH_INVARIANT,**VLLM_MARLIN_USE_ATOMIC_ADD=0**,…}・replicas[{tier,model,revision,quant,weights_blake3,tp,dp,gpus,max_num_seqs,max_model_len,gpu_memory_utilization,in_flight_cap}]・routing{rule,cell_affinity=false}・decoding{T1,T2}・prompt_contract{version,static_tok,cell_tok,individual_tok}・**prefix_caching_hash_algo=sha256_cbor(検証ラン)**・**cache_salt(モード別)** | 既定sha256(pickle)は版をまたいで非再現(公式) |
| 並行意味論 | scheduler{name,version}・phases=[read_intent,arbitrate,commit]・priority_key・tiebreak_key・class_rank・llm_apply{policy,order,overdue,missing}・retry_rounds・arbiter{rule,promotion_T_max_min,degrade_enabled} | §2の規則の版 |
| 予算 | source{path,commit,blake3}・effective{W1,L4,L6,M8,M11,P6…} | ラン時点のスナップショット |
| ハードウェア | profile・gpus・cpu・ram_gb・os | サーバー名・IPは書かない |
| 出力 | journal・checkpoints・llm_tape・diagnostics{columns}・(s3_uri は接続情報を書かない) | 診断行4列+保存則2検算がなければ較正・holdoutに使わない(T9) |
| 系譜 | parent_run | resume元 |

### 1.3 再現性の主張水準(三層宣言)
| 層 | 水準 | 条件 | テスト |
|---|---|---|---|
| エンジン層(物理・経済・スケジューリング・繰り延べ・保存則) | **bit再現(numerical identity)** | 同一manifest・同一機・LLM応答は録画テープで固定・順序固定 | T2: 同一manifest×2で全checkpointハッシュ一致 |
| LLM層(発話・行動選択) | **分布同値(distributional equivalence)** | 同一manifest・同一機・同一vLLM版・温度0.7・DP7 | T7: 行動分布JSD≤帰無95th・制約違反率差の95%CI上限≤0.05(指標Bの装置) |
| 結合系 | **関係整合+分布同値** | アンサンブルN本(master_seedのみ変更) | T8: 台帳照合指標のN本分布が合格基準を満たす |
- **bit再現はテープリプレイ(デバッグ・検死)専用**。検証ラン(mode: holdout)=BATCH_INVARIANT=1・TP1(32B AWQ TP4は温度0でも非再現=品質プローブv0 summary §5-1・R16注記)・温度0・固定ルーティング・sha256_cborでLLM層のbit再現もあり得るが、**本番(温度0.7)では主張しない**。Wilensky & Rand 2007の3水準に対応。
- **B14(自検証・09-07実測)**: BATCH_INVARIANT=1でT6a(温度0・単独vs混在c64)32/32一致・logprobs 32/32・T6b(温度0.7+seed・充填順変更)32/32一致・スループット差なし(6.09 vs 5.94呼/s)。OFFでは3/32・logprobs 0/32・温度0.7で3/32。**A5000(CC 8.6)で不変性は成立=T6合格**。公式env_vars頁の「>=9.0」は実測と矛盾(features頁「8.0+」が実態)。[docs/bench/b14_batch_invariance/README.md](../bench/b14_batch_invariance/README.md)

### 1.4 テスト(T1-T9)
T1 manifest自己整合(run_id=正規化本文のハッシュ・封印署名一致・CI常時)/T2 エンジンbit再現(Phase 2完了条件)/T3 並列不変性(スレッド1/8/32で同一結果)/T4 規模不変性(n=5,000と5,001で既存個体の乱数列不変=カウンタベースの実証)/T5 順序バイアス検出(24stepスモークで個体ID順との相関|r|≤0.05)/T6 LLM層bit再現(検証ラン構成・不一致なら「この機・この版ではbit再現を主張しない」と記録)/T7 LLM層分布同値(本番構成)/T8 アンサンブル安定性/T9 診断行4列(繰り延べ/昇格/縮退/抑止)+保存則2検算の存在(全ラン)。

## §2 U9 並行実行の意味論

### 2.1 前提
並行実行の順序は世界の法則(Weimer et al. 2019: 同期性と更新順が意見力学の分散・極化を変える)。全項にmechanism|expedientタグ・同期/非同期の選択はablation対象・v1のID順バイアス(C-8)を根治。

### 2.2 二相コミット(reserve→arbitrate→commit)
```
tick t:
  Phase A (read-only・並列可): 全個体が現在状態を読み intent を出す(LLM由来のintentは前tickまでに届いた応答から)
  Phase B (arbitrate・決定論): 資源ごとに intent を集め 優先度キー昇順で確定
      pk = ( ceil_ns(t_notice)=tick開始+δ_perc[秒オフセット], blake3(run_salt‖tick‖resource_id‖agent_id) )   # 辞書式
  Phase C (commit・単一書き手): engine.resolve が確定分だけ適用。落選者には失敗の意味論(行動契約書§2/§6)
```
- FLAME GPU 2のpropose→rank→moveと1対1(mechanism)。優先度をハッシュで導出=メモリ0・再現性は上(FLAME GPU 2は変数格納)。**atomic演算による直接更新は禁止**(GPUで順序が非決定)。
- 反復=同一tick内1回(第2希望)まで、以後は次tick(expedient・FLAME GPU 2は動的回数)。未解決者数は診断行へ。
- 競合クラス別: 席・最後の1個=pk昇順(在庫減算はPhase Cのみ=保存則)/会話招待=1件だけ通し応答判定(≈0.8)は通った後/**乗車=§2.6参照(満員電車の扱い)**/注視・傍受=競合なし/権限行動=原則1人。
- 確率と優先度を混ぜない(必要な確率性はpkのハッシュ撹拌に押し込む)。

### 2.3 δ_percのサブtick順序(決定・expedient登録)
δ_perc(0.2-1.5秒)は1分tickでは丸めるとゼロになる→**世界時刻は進めず、同一tick内の順序(ナノ秒欄=tick開始+δ_perc)としてのみ使う**。pkの第1要素にすることで「先に気づいた人が先に取る」が会話の割り込み(次の移行点での優先権奪取)と在庫の予約に共通の規則になる。文献にない用法=expedient(δ_percを全員同値に潰した対照ランで感度試験)。

### 2.4 LLM応答の適用順
到着順に適用しない。pending_applyに入れ、**次tick先頭でapply_key=(t_apply, event_class, blake3(run_salt‖t_apply‖agent_id))の昇順**でまとめて適用。t_apply=起床時刻+δ_perc+δ_thinkを分tickに切り上げ。event_classはアービタの4クラスと同じ順序(規則を2つ持たない)。締切超過=破棄せず繰り延べアービタへ(状態トリガは最新値で回復・会話ターンは冪等でないため最優先)。未着=当該個体だけが「考え中」で待つ(既定行動の代入はしない)。最大滞留・超過件数はmanifestと診断行へ。

### 2.5 タイブレークと乱数
- 同時刻イベント=(t_sim_ns, class_rank[institution −1・conversation 0・plan_boundary 1・individual 2・cell 3], blake3(…), subject_id)。制度=−1は「営業時間外の購入を防ぐ」実装都合=expedient。
- 乱数=NumPy Philox(4×64)・鍵=(master_seed, domain)・カウンタ=(tick, entity_id, draw_index)=呼び出し順非依存(T3/T4で検証)。numbaカーネル内で必要な乱数はCPU側で配列生成して渡す(既定)。
- 録画リプレイ=LLMテープ(1呼=1行・共有ブロックはID化・params_hash)から(agent_id, tick, wake_class, prompt_hash)完全一致で引く。テープ外は失敗(黙って実LLMへ落とさない)・テープ外率を診断行へ。
- PDES: 楽観同期・Time Warpは不要(書き手=resolve一本)。保守的保留とlookahead(δ_perc+δ_thinkの下限)のみ(既決構造からの演繹=expedient)。

### 2.6 乗車の意味論(ユーザー指摘「定員超過=次列車へは満員電車を再現しない」・2026-09-07改訂)
「定員」を座席・定員ではなく**詰め込み上限(混雑率の実測上限)**にし、乗車受容を混雑率の関数にする: (i)列車の実効容量=定員×混雑率上限(国交省の最混雑区間混雑率を線別に採用=mechanism・出典は台帳行D10′候補) (ii)混雑率<上限では乗車は常に成立し、乗車後の内受容(体力・体感温度)と停車時間が混雑率で増える (iii)上限到達時のみ「乗り残し」=次列車へ繰り越し(繰り延べ)し、乗り残し率を診断行へ (iv)混雑率そのものをパターン照合の対象にする(線別最混雑区間の混雑率=公的値)。**根拠(国交省 令和6年度 都市鉄道の混雑率調査・資料2「東京圏における主要区間の混雑率」PDF実読・2026-09-07)**: 東急田園都市線 池尻大橋→渋谷 7:50-8:50・10両×27本・輸送力40,338・輸送人員53,650・**133%**/東急東横線 祐天寺→中目黒 **122%**/東京メトロ半蔵門線 渋谷→表参道 **103%**/銀座線 赤坂見附→溜池山王 **147%**/東京圏31区間平均**139%**(前年比+3pt)。山手線・井の頭線・副都心線は主要31区間表に無く別表=**資料3「最混雑区間における混雑率(2024)」(001904497.pdf・親がPDF実読・2026-09-07)**で取得: JR山手線 外回り 上野→御徒町 7:47-8:47・11両×16本・輸送力26,032・輸送人員34,940・**134%**/内回り 新大久保→新宿 7:41-8:41・11×20・32,540・45,160・**139%**/JR埼京線 板橋→池袋 7:51-8:51・10×19・28,040・45,790・**163%**/京王井の頭線 池ノ上→駒場東大前 7:45-8:45・5両×27本・18,900・23,246・**123%**/東京メトロ副都心線 要町→池袋 7:45-8:45・8.9×18・24,244・28,365・**117%**(※銀座線・副都心線は2023年度に列車混雑計測システム導入・2024年度に精度向上=資料3注記)。湘南新宿ライン単独行は資料3に無し(空欄)。資料3の値は各線の**最混雑区間**であり渋谷断面ではない=渋谷断面の上界として採用(mechanism・時点2024年度)。検索結果に出る田園都市線「181%」はコロナ前(2019年度級)の値で現在値ではない。**受容関数の初期値(expedient)**: 混雑率≤150%で受容1.0、150-200%で線形に0.7へ、200%超で乗り残し。実効容量=定員×2.0(200%=「体が触れ合い圧迫感」の国交省目安)。パターン照合=線別最混雑区間の混雑率(mechanism・D10′候補行)。

### 2.7 expedient登録簿(本書分)
ハッシュ撹拌の優先度/δ_percを競合の勝敗に使う用法/再試行1回/制度=−1/カウンタベースRNGのABM適用(査読文献未確認)/保持窓の長さ/LLMタイムアウト既定(TTFT 60s・e2e 300s)/乗車受容関数の形(混雑率→受容率)。
