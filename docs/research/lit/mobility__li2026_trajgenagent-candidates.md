# Li, Tran, Zhao, Shafique & Xiong 2026 — TrajGenAgent: A Hierarchical LLM Agent for Human Mobility Trajectory Generation

- リンク: <https://arxiv.org/abs/2606.12657> / PDF <https://arxiv.org/pdf/2606.12657> | 分野: 人間移動科学 #3 / ABM方法論 #21 / 自然言語処理 #27 | 重要度: **P1**
- **一次確認**: **実読(サブ・2026-09-17・PDF 全 14 頁を pymupdf 抽出)・親未確認**。v1・cs.AI/cs.DB/cs.RO。コード `github.com/Emory-AIMS/TrajGenAgent`(未確認)。
- **既存答申との関係**: `../v2-llm-mobility-research.md`(**D 等級**)が「TrajGenAgent: LLM を活動チェーン構造だけに限定し距離 JSD 0.0006」と 1 行だけ書いている。**数値は一致するが記述は不正確**(時刻も LLM が出す。エンジンなのは**行き先だけ**)。

## 主張(claim)

LLM に POI を直接選ばせず、**決定論ワークフローの中で候補集合を作り、規則でスコアづけして抽出する**ほうが、微調整した LLM より安く同等以上の忠実度が出る。

## 機構(mechanism)

**2 段構成**。Stage 1 = オーケストレータ LLM が「活動チェーン」(意味的な骨格)を生成。Stage 2 = 決定論ワークフロー(LangGraph)が **空間ワーカ**(POI 接地)と **時間ワーカ**(到着時刻・滞在時間)を固定順で回す。

### 候補集合の作り方(逐語)

- 「we retrieve a candidate POI set **rather than sampling from the full location space**. We first build an **individual-specific feasible set** `P_u(a_i)` from historical visits.」
- 「we augment candidates using a **top-K similar-individual pool** obtained via similarity matching over mobility signatures (e.g., spatial scale, temporal rhythm, and activity/transition distributions, optionally with co-location signals).」→ `P(a_i) = P_u(a_i) ∪ P_sim(a_i)`。
- **空集合の扱い(逐語)**: 「If `P(a_i)` is empty, we emit an **explicit invalid marker** (rather than silently sampling) to avoid cascading errors.」

### 選ぶのは LLM ではない

- 式 (6) `S(p) = λ_f · s_freq(p) + λ_d · s_dist(p)`
- 式 (7) `s_freq(p) = (1−α) P_u(p|a_i) + α P_sim(p|a_i)` — **α = 探索ゲート**
- 式 (8) `s_dist(p) = exp(−β · |dist(p_{i−1}, p) − ℓ̄_u(a_{i−1}, a_i)|)` — Haversine 距離と**個体ごとの平均遷移距離**の差
- 正規化した `{S(p)}` から**確率抽出**。
- **設計判断の明文(逐語)**: 「`C_{u,d}` anchors global day structure while allowing the worker to inject deterministic mobility priors (e.g., distance- and speed-based feasibility) **without requiring the LLM to directly rank or search over large POI candidate sets**.」

### 探索ゲート α の感度(逐語)

「Moderate changes in α have limited impact on our statistical or anomaly metrics, but **α = 0 can yield near-copy trajectories** with lower downstream utility, while excessive peer weighting may drift beyond the target individual's mobility scope.」

## 数値(表番号まで)

- **Table VI(kinematics の ablation・JSD・NumoSim / MobilitySyn)**: **Distance 0.0006 / 0.0028**(w/o kin. は 0.0000 / 0.0000)・G-radius 0.0993 / 0.1508・Duration 0.0155 / 0.0198・DailyLoc 0.2117 / 0.2476・I-rank 0.0002 / 0.0006・G-rank 0.0002 / 0.0006・Transition 0.0075 / 0.0077。
  → **既存答申の「距離 JSD 0.0006」は NumoSim の値で一致。**
- **Table V(自由形ツール呼び vs 決定論ワークフロー・同一 Qwen2.5-32B・7 活動/日)**: 自由形 **軌跡単位 9.8% / 訪問単位 59.3%**、決定論ワークフロー **100.0% / 100.0%**。著者(逐語)「zero-shot free-form tool calling **falls short of a practically usable level** of tool-invocation stability for sequential grounding」。**フォールバック有効でこの値**。
- **Table IV(H100 1 枚・34,000 日軌跡の生成+必要なら学習・GPU 時間)**: GRU 1.25 / **TrajGenAgent 1.67** / LSTM 1.83 / Transformer 3.17 / Geo-CETRA 3.38 / SeqGAN 20.62 / Geo-Llama 24.77。
- **モデル**: 両ステージとも **Qwen2.5-32B-Instruct**(vLLM・温度 0.90・top-p 0.95・max tokens 1024・context 8192)。微調整なし。比較対象の Geo-Llama は Llama-2-7b-chat を LoRA 微調整(温度 1.2)。
- 評価に JSD だけでなく**異常検知ベース**(BeSTAD AUROC・ICAD AP、目標は 0.5=見分けがつかない)を導入。著者の問題意識(逐語): 集計距離指標は「often **miss individual-level semantic defects**」。

## 効く箇所(seam)

- **R-37 §5-1「母集合」**: `P_u ∪ P_sim` の形。v2 は類似個体プールを持たないので `P_near`(近傍セル)で置換する=**そこが [未リサーチ(expedient)]**。
- **R-37 §5-1「空のとき」**: 「黙って抽選しない・明示の invalid を出す」= v2 の `ResultCode` に候補なしの行を足す根拠。
- **ρ_i の感度試験の事前予想**: 「α=0 は写しになるが、中間値には鈍い」= v2 の T-C 腕(ρ_i を定数にする)の予想。
- **8B での自由形は塞がっている**: 32B ですら軌跡成功率 9.8%。**H が「1 呼で 1 語を選ぶ」形に留まるべき根拠**(ツール呼びや多段検索にしない)。

## 「結論でなく機構として」の入れ方

- **借りる**: (1) 候補は全空間から引かない (2) 空集合を明示する (3) 探索ゲート 1 個で個体忠実度と多様性を混ぜる形 (4) 決定論ワークフローで順序を固定する形。
- **借りない**: `s_dist` の指数減衰の係数 β・λ_f/λ_d(論文に値の記載を確認できず=空欄)・重力則。
- **注意**: この論文は **H の反対側の証拠**である(LLM に選ばせない設計を明文で正当化している)。

## コスト/スケール含意

34,000 日軌跡を H100 1 枚で 1.67 GPU 時間。**v2(390,067 体・7.4 呼/体/日)とは呼の粒度が違う**ので、体あたり秒での正規化なしに並べられない([[compute__alves2026_llm-urban-mobility]] と同じ注意)。

## 批判・限界

1. **λ_f・λ_d・β・K・α の具体値が本文に見当たらない**(空欄)。再現には コードが要る。
2. データは NumoSim / MobilitySyn = **合成データ**。実市街地ではない。
3. 「LLM が活動チェーンだけ」ではない——**時刻も LLM 側**(「LLM augmented kinematics-aware temporal generation」)。
4. Table V の自由形は**微調整なし**の条件。ツール呼び微調整をすれば改善しうると著者自身が書いている。

## 関連

[[mobility__santos2026_unconstrained-poi]] ・ [[mobility__feng2024_llm-move-candidate-order]] ・ [[mobility__song2010_epr]] ・ [[compute__alves2026_llm-urban-mobility]] ・ 答申 `../v2-destination-choice-llm-research.md` §1-5
