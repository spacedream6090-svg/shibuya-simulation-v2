# Lu et al. 2026 — Procedural Graphs: Self-Evolving Execution Structures for LLM Agents

- リンク: https://arxiv.org/abs/2609.09153 | 分野: 認知科学(記憶・習慣)#12 / 自然言語処理 #27 | 重要度: **P1**(第2陣の記憶/習慣の表現候補)
- **一次確認**: **実読**(2026-09-16・サブが WebFetch で abs + `arxiv.org/html/2609.09153v1` 本文を取得。**付録 E.1 の精錬器側の計算費は切れている**)。**親未確認**。v1 のみ(2026-09-08)。Comments 欄「36 pages including references and appendices, 6 figures, 11 tables」=**会議・誌名の記載なし**。著者 Yuxing Lu, Yicheng Chen, Shanchan Wu, Sercan Ö. Arık。

## 主張(claim)

知識グラフが (entity, relation, entity) で「何であるか」を持つように、**手続きグラフ (PG) は (procedure, relation, procedure) で「次に何をするか」を持つ**。グラフは固定でなく、失敗と成功の軌跡を比べて **LLM の精錬器が編集**し、**保留検証で通った編集だけ残す**。

## 機構(mechanism)— 表現

**𝒢 = (𝒱, ℛ, ℰ, Φ)**、ℰ ⊆ 𝒱 × ℛ × 𝒱。「**each element of ℰ is a directed, attributed triplet**」(u, r, v) = 「u の後に v が許される」。

- **ノード**: 「**Each node abstracts a tool function, a skill, an internal reasoning step, or a task status.**」直列化時は ID・型(例 ACTION)・記述を持つ。
- **属性は辺に載る**: 「**we use three textual fields: condition, guidance, and pitfalls**」(条件・助言・落とし穴)。**これが本論文の要点**——手続き知識をノードでなく**遷移**に置いた。
- **関係語彙は 4 種だけ**: 「**LEADS_TO, TRIGGERS, PROVIDES_INPUT_FOR, and CONVERGES_TO**」。
- **グラフは小さい**: 7〜17 ノード・7〜27 三つ組(BFCL v3 だけ 131 ノード・265 三つ組)。

**助言の作り方(位置決め → 抽出 → 生成)**

1. u_t = Match(a_{t−1}, 𝒱) —「**locates the agent by exactly matching its most recent procedure (e.g., a tool call) to a node**」。a₀ = Start。
2. 𝒢_t = u_t の **h=2 ホップ**の出方向近傍(照合失敗なら全グラフ)。
3. g_t = Ψ(𝒢_t, q, 𝒯_{t−w:t})、**窓 w=3**。助言プロンプトに入るのは 課題記述 + 部分グラフの要約 + いまの問い/観測 + 直近の軌跡。辺の condition/guidance/pitfalls を使って「次に何を / 何を避け / どう復帰するか」を書かせる。
4. 「**The guidance g_t is appended to the task solver's prompt**」。助言モデルは解答モデルと**同じ LLM**。

**自己進化**: 位相操作は 2 つだけ —「**Add: Inserting missing verification nodes or edges**」「**Delete: Removing nodes or edges that repeatedly steer trajectories into failure or prevent progress**」。属性の変更は「辺を削除して属性を更新して足し直す」。構造検査・閉路修復 → 検証ロールアウト。**受理則は非減少のみ**: 𝒢_k = 候補 ⟺ S_val(候補) ≥ S_val(現行)。却下された編集は ℋ_rejected に入り、次回の精錬器に渡る(**同じ失敗を繰り返さない**)。

## 数値(出所つき)

**Table 1(素の ReAct → PG・6 ベンチ)**

| モデル | HotpotQA | MultiChallenge | GDPval | ALFWorld | τ-bench | BFCL v3 |
|---|---|---|---|---|---|---|
| Claude Sonnet 4.6 | 74.60→74.50 | 83.73→89.76 | 46.23→51.49 | 86.57→93.28 | 66.09→73.91 | 61.00→67.00 |
| Gemini 3.1 Pro | 85.90→87.30 | 87.95→95.78 | 56.39→**78.78** | 94.78→**100.00** | 72.17→80.00 | 59.00→66.00 |
| Gemini 3.5 Flash | 83.10→84.50 | 81.33→91.57 | 59.33→64.42 | 82.84→94.03 | 31.30→44.35 | 56.00→67.00 |
| Grok 4.1 Fast | 72.70→74.40 | 68.07→86.75 | 57.23→71.19 | 26.12→39.55 | 64.35→67.83 | 52.00→60.00 |

- 「**PG ranks first or joint first in 21 of 24 model–benchmark settings.**」
- **EnterpriseArena(月次財務判断・132 か月)の生存率**: Claude 44→**58%** / Gemini 3.1 Pro 6→**34%** / Grok 26→**40%**。
- 構築様式の比較: 白紙から + 自己進化(Mode 5)が HotpotQA 78.79 F1 / MultiChallenge 91.07% 成功。**わざと欠陥のある専門家事前分布を入れると MultiChallenge が 58.93% に落ち、自己進化が 92.86% まで回復**=「専門家の手設計を直せる」。
- **費用(Table 3・Gemini 3.5 Flash・素 → 部分グラフ生成)**: MultiChallenge 6,629→12,295 tok(3.87→4.22 手)/ GDPval 275,638→367,738 tok(28.20→**18.57** 手)/ ALFWorld 18,055→28,064 tok(21.84→**18.80** 手)。逐語(≤125 字): 「**total token consumption remains 33.4% and 55.4% higher**」(GDPval / ALFWorld)。**手数は減るがトークンは増える**([StateAct](agents__rozanov2025_stateact.md) と逆)。
- **位置決めの効き**: 全グラフ生成に比べ ALFWorld −70.9% / GDPval −18.1% / MultiChallenge −14.8% のトークン削減。
- EnterpriseArena: 助言で Flash の道具呼が月 18.94 → 12.53、進化後のグラフでは 17.23 → **3.08**。

## 効く箇所(seam)

- **第2陣の記憶/習慣**。この repo の第1陣は**記憶が無い**(分野地図 #12「D-68 個人内の規則性が無い(記憶が無い)」)。PG は**個人の記憶ではなく手続きの共有知**として置ける = **母集団共通のグラフ 1 枚 + 体ごとの現在ノード**なら、体あたりの状態は**ノード ID 数バイト**で済む。40 万体でも 400 KB 級。
- **D-73(自由意図が「行く/食べる」に 90% 集中)** の第 2 の道: 24 語の行動語彙を**遷移のグラフ**にすると、「いまのノードから許される次」が絞られる。**ただしこれは設計者の指紋を増やす方向**(憲法の「ボトムアップ創発を第一候補に」と逆)=採否はユーザー判断。
- **段2 `adjudicate`**(`llm/undefined.py`・本番では `adjudicator=None` で未発火)= 本論文の「精錬器の編集を検証で漉す」と**同じ形**。この repo は既に骨格を持っている。

## 「結論でなく機構として」の入れ方

- **借りない**: 4 種の関係語彙・EnterpriseArena・道具使いのベンチ。
- **借りる**: (1) **属性を辺に置く**(条件・助言・落とし穴)という表現。この repo の行動語彙は**ノードだけ**で遷移に何も載っていない。(2) **受理則 = 保留検証で非減少**。段2 の閾値 N=10 に加えて「**採用後に指標が落ちないこと**」という第 2 の関門。(3) **却下記録**(ℋ_rejected)= 同じ語を何度も却下しない台帳。(4) **位置決めで文脈を絞る**(h=2 ホップ)= 観測トークンの節約と同型の考え方。

## コスト/スケール含意

- **1 手番につき助言呼が 1 回増える** = この repo の 6.94 呼/体/日 が**最悪 2 倍**。40 万体なら +270 万呼/日。**そのままは入らない。**
- 入れるなら (a) 助言を**セル・種別で共有**して prefix キャッシュに載せる(この repo の B2/B4 と同じ手)か、(b) **日次内省(42 万呼/日)の中に畳む**か。
- 手数が減る効果は、この repo では**呼数が計画境界で決まる**ので期待できない(道具使いのループではない)。**トークン +33〜55% が素直に乗る**と見るべき。

## 批判・限界

- **査読なし**。ベンチは全部**道具使いの単体エージェント**で、社会シミュではない。
- 受理則が「非減少」だけなので、**検証集合への過適合**が起きうる(著者は保留と書くが分割の詳細は未読)。
- グラフが 7〜17 ノードと小さい。都市の生活行動の手続きがこの大きさに収まる保証はない。
- 精錬器側の計算費(付録 E.1)は未読。
- 「専門家事前分布の欠陥を直せる」は**自分で作った欠陥**を直した実験。

## 関連

[[agents__rozanov2025_stateact]] ・ [[network__complex-contagion-overview]] ・ `../../design/v2-open-intent-arm-spec.md` §7 段2 ・ `../v2-llm-social-sim-timeline-seed.md` #18
