# Li & Tao 2026 — AI Agents Alone Are Not (Yet) Sufficient for Social Simulation

- リンク: https://arxiv.org/abs/2603.00113 | 分野: 計算社会科学 #25 / ABM 方法論 #21 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-16・サブが WebFetch で abs + `arxiv.org/html/2603.00113v2` 本文を取得。**付録 A 以降は切れている**)。**親未確認**。v1 2026-02-19 / v2 2026-05-07。Comments 欄「16 pages」=**会議・誌名の記載なし**(立場表明論文)。著者 Yiming Li, Dacheng Tao。

## 結論(R-2 の問い「処方側の記述があるか」への答え)

**ある。**§4「**Actions for Future Social Simulation**」に**番号つきの行動 3 つ**があり、§6 で再掲されている。親の「脆さ側」の読みと有志の「処方側」の読みは**どちらも本文にある**(§3 が診断・§4 が処方)。

## 主張(claim)

「役割を与えたエージェントをネットワークに置けば現実的な人口動態が創発する」という**暗黙の前提**が過剰楽観の出所。3 点: ①説得力のあるロールプレイは**行動的妥当性を保証しない** ②群水準の結果は**エージェント間のやり取りだけでなくエージェント−環境の共動態**に依存する ③結果は**相互作用手順・スケジューリング・初期情報事前分布**に駆動されうる。

## 機構(mechanism)— Definition 4.1「環境込みエージェント社会シミュレータ」

N 体・地平 T の組:

**Sim = (E, G, C, {M_i, O_i, A_i, P_i, U_i, R_i}_{i=1..N}, D₀, Sch, Vis, Tr)**

| 記号 | 中身 |
|---|---|
| E | 環境状態(政策パラメータ・制度・資源・執行) |
| G | 網の状態 g_t |
| C | 外生文脈 c_t |
| M_i / O_i / A_i | 心的状態(信念・選好・記憶)/ 観測 / 行動 |
| P_i | 方策 a_t^i ~ P_i(·\|o_t^i, m_t^i; ℓ_i)。**ℓ_i = LLM の設定**を明示的に方策の一部に置く |
| U_i | 心的状態の更新 m_{t+1}^i = U_i(m_t^i, o_t^i, a_t^i, v_t, e_t, g_t, c_t) |
| R_i | 行動 → 制度的帰結 |
| **D₀** | 初期分布。「**must encode population composition, attribute correlations, initial network structure, and epistemic priors**」(逐語 ≤125 字) |
| **Vis**(曝露作用素) | (o_t^{1:N}, v_t) ~ Vis(·\|e_t, g_t, c_t)。v_t は「**a visibility object (e.g., exposure graph) that determines who sees what**」 |
| **Sch**(スケジューリング) | I_t = Sch(e_t, g_t, c_t) ⊆ {1..N}。「**when and which agents are allowed to act**」を形式化 |
| Tr | (e_{t+1}, g_{t+1}) ~ Tr(·\|e_t, g_t, c_t, a_t^{1:N}) |

**1 step のループ**: ①Vis で観測を引く ②Sch で活動集合を引く ③活動体だけ行動(他は no-op)④U_i で心的状態を更新 ⑤Tr で遷移。

## 処方(§4・逐語 ≤125 字)

1. **Action 1**: 「**Treat the environment as a first-class, auditable object**」— Vis・Sch・Tr・R は「versioned, inspectable artifacts with logged traces」として仕様化する。学習した動態モデルで代える場合も「its intermediate states and uncertainty diagnostics remain exposed」こと。
2. **Action 2**: 「**Move evaluation beyond plausibility to mechanistic and counterfactual reliability**」— 3 下位基準 = (i) 制約下の挙動(e_t と R の誘因に反応するか) (ii) 機構感度(C・Vis・Sch・Tr を編集すると macro が**安定かつ向きの一貫した**変化をするか) (iii) 反実仮想安定性 =「**whether comparative conclusions persist across random seeds, prompt paraphrases, and other nominally irrelevant implementation choices**」。手段は「**mechanism ablations, negative controls, and counterfactual sweeps that vary one component at a time**」。
3. **Action 3**: 「**Interpret simulation outcomes with epistemic caution and explicit uncertainty**」— 不確実性を第一級の出力として扱い、D₀・Vis・Sch・Tr・ℓ_i への感度を報告する。結果は「**reported as distributions (e.g., uncertainty intervals and variance decomposition) rather than selected trajectories**」。

§6 の再掲: 総体としての人間との相関は「insufficient evidence」・**機構水準の監査を既定にせよ**。

**チェックリスト・表は無い**(番号項目は Mismatch 1/2・Gap §3.2.1-3 ・5 段ループ・Action 1-3 のみ)。

## 効く箇所(seam)

**この repo の実装は Definition 4.1 の Vis・Sch をすでに明示的に持っている**(数少ない例):
- **Vis** = `v2-perception-contract.md` の知覚 3 層 + p_notice(誰に何が届くか)。
- **Sch** = 起床条件(計画境界・イベント)+ **繰り延べの 4 クラス固定優先**(会話ターン > 計画境界 > 個体変化 > セル変化)。本論文の言う「いつ・誰が行動できるか」そのもの。
- **Tr** = 世界過程(エンジンが唯一の書き込み口)。
- **D₀** = W16/W17 の合成人口。「属性の相関・初期網構造」まで含めよという要求は**部分的にしか満たしていない**(網構造=関係表の初期化は薄い)。
- **ℓ_i を方策の一部と見る**= モデル同一性を腕にする(D-72 系)。

## 「結論でなく機構として」の入れ方

- **借りない**: Markov game の定式そのもの(この repo はコードが正典)。
- **借りる**: (1) **Vis / Sch / Tr / D₀ を「版つき・検査可能な成果物」として台帳に出す** = run manifest に既にある欄を、**この 4 語で名前を付け直す**だけで外部の語彙と接続できる。(2) Action 2 (ii) の「**機構を編集したとき macro が向きの一貫した変化をするか**」= C8 ablation の合否規則の候補(いまは JSD の距離だけ)。(3) Action 3 の「**分布として報告・分散分解**」= G-8 の 8 seed アンサンブルの報告様式。

## コスト/スケール含意

Action 2 は「一度に 1 要素だけ変える反実仮想スイープ」= **ablation の本数が要素数に比例**。この repo の D-44「108 行 = 93 日」問題と正面衝突する。**本論文は本数を減らす規則を与えない**。

## 批判・限界

- **立場表明**(査読なし・実験なし)。数値が 1 つも無い。
- Definition 4.1 は既存の POMDP/Markov game の書き直しで、新しい数学は無い。
- 処方の 3 つは全部「やれ」であって「どれだけやれば十分か」を言わない。**十分性の規則はこの repo が自分で決めるしかない**(D-44)。
- 付録 A 以降は未読(サブの取得範囲)。

## 関連

[[validation__larooij2025_generative-abm-validation]] ・ [[validation__ye2026_robustness-audits]] ・ `../../design/v2-perception-contract.md` ・ `../v2-llm-social-sim-timeline-seed.md` #12
