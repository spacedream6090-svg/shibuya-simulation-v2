# Ye et al. 2026 — Stop Drawing Scientific Claims from LLM Social Simulations Without Robustness Audits

- リンク: https://arxiv.org/abs/2605.18890 | 分野: 検証と V&V #22 / 計算社会科学 #25 / 統計学 #23 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-16・サブが WebFetch で abs + `arxiv.org/html/2605.18890v1` 本文を取得。**参考文献の途中で切れている=付録 A の Table 2/3 は未読**)。**親確認(第202)**: pre-registration / preregistration / pre-registered が本文に無いこと、TRAILS が 3 水準(agent=micro / interaction=meso / system=macro)+ TRAILS-D(Micro 4・Meso 2・Macro 2)+ TRAILS-R 5 次元であることを親が WebFetch で再読・一致(付録は親も未読)。。v1 のみ(2026-05-17)。**Comments 欄が無い=会議・誌名の記載なし**。著者 Jinyi Ye, Lei Cao, Ding Chen, Emilio Ferrara。

## R-2 の問い 1「事前登録の推奨が本文にあるか」への答え

**無い。** "pre-registration" / "preregistration" の語は本文(§1〜6)に**現れない**(サブが取得した範囲。参考文献以降と付録は未確認)。最も近いのは §6 の報告要求(逐語 ≤125 字): 「**report which perturbations were tested, which findings remained stable, which findings were sensitive**」+ 監査していない次元を明示せよ。

→ **[時系列の種](../v2-llm-social-sim-timeline-seed.md) #14「2026-06 事前登録『先に固定せよ』」の実体は、この論文の中にも無い。**#14 は引き続き**空欄**。

## R-2 の問い 2「TRAILS 3 層の中身」

**Table 1(§5)。TRAILS = Taxonomy for Robustness Audits In LLM Simulations。実は 2 部構成**で、「3 層」は TRAILS-D の側だけ:

**TRAILS-D(設計水準)**

| 層 | 次元 |
|---|---|
| **Micro(エージェント)** | Model substrate / Agent specification / Internal state and cognition / Memory and temporality |
| **Meso(相互作用)** | Interaction protocol / Intervention design |
| **Macro(システム)** | Environment structure / Population and scale |

**TRAILS-R(表現水準・層に割り当てられていない)**: Representational format / Instruction hierarchy / Linguistic framing / Context representation / Interaction sequencing

- 具体例は付録 A の Table 2・3(**未読**)。

## 数値(出所つき)

- **76 pt の中身**(§4.1・Figure 1): モデル **gpt-5.2**、摂動 = **ペルソナの書式**(Plain / Descriptive / Tabular・**内容は同一**)、設定 = 2 体の反復囚人のジレンマ **10 ラウンド**、両者同じ書式。逐語(≤125 字): 「**Descriptive personas cooperate 76 percentage points less often than Plain personas**」(p<0.001)。Tabular との差は 73 pt(p<0.001)。
- **seed**: 「**gpt-5.2, N=30 seeds per condition; two-sided Mann–Whitney U, p<0.001**」。手続きの逐語: 「**repeat each condition with N=30 independent simulation runs using distinct random seeds**」(§4)。
- **絶対の協力率(基準値と摂動後の値)は本文に無い**。差分だけ。
- **モデル間**(§4 の Finding Summary): claude-haiku-4-5 ≈**77 pt** / gemini-2.5-flash ≈**36 pt** / **deepseek-v3 ≈1 pt**(逐語 ≤125 字: 「**essentially no effect in deepseek-v3 (∼1 pp)**」)。→ **「別モデルでは 1pt」の当該モデルは deepseek-v3**。
- もう 1 つの事例研究 = SNS のエコーチェンバー。網の同類性とハブ割り当てが分極指標を有意かつ一貫して動かす(数値は未取得)。
- **最小 seed 数の推奨は無い**。§3.1: 探索的な試行でも「single prompt, seed, or model の産物でないことを示すべき」。
- §5 の優先順位づけの発見的規則 3 つ(逐語 ≤125 字): 「**align audits with the claim's mechanism**」「**ensure each perturbation spans a meaningful range**」「**audit across model families before claiming generality**」。
- §6: 研究は**場面・領域の賭け金・主張の型(探索的 / 機構 / 政策)**を宣言し、監査の量をそれに合わせよ。

## 効く箇所(seam)

- **C8 ablation の設計**。TRAILS-D の 8 次元に対して、この repo の第1陣 6 本(チャネル固定枠・p_notice d50・不応期・ΔSNR・内省頻度・広告ゼロ)を当てると:
  - Micro: `Model substrate`(=D-72 のモデル同一性)✖ 未着手 / `Agent specification`(=ペルソナ書式)✖ 未着手 / `Memory and temporality`(=内省頻度)✔ ⑤
  - Meso: `Interaction protocol`(=繰り延べ規則・会話)△ Phase 3 / `Intervention design`(=広告ゼロ)✔ ⑥
  - Macro: `Environment structure`(=セル粒度・p_notice)✔ ②・第2陣 / `Population and scale`(=出勤率 0.88 の感度腕)△
  - **TRAILS-R の 5 次元(書式・指示階層・言い回し・文脈表現・順序)はこの repo にほぼ無い**。v1 に `ablate.prompt_paraphrase`(S-16)があった=**v2 に移していない穴**。
- **76 pt はペルソナ書式の摂動**。この repo は「人格プロンプトを増やさない」(D-68)ので**書式の分散が小さい**=そもそも当たりにくい。ただし **W17 v2 段1 の自己生成 250〜350 字は書式が体ごとに違う**=ここが TRAILS-R の暴露面。

## 「結論でなく機構として」の入れ方

- **借りない**: 76 pt という数値を自分の主張に使うこと(モデルも場面も違う)。
- **借りる**: (1) **TRAILS-D 3 層 × TRAILS-R 5 次元を C8 の被覆表にする**(どの次元を監査し、どれを未監査と宣言するか)。(2) §6 の**報告様式**(何を摂動し・何が安定で・何が敏感で・何を監査しなかったか)= 受入報告の新しい節。(3) **主張の型ごとに監査量を変える**= D-44「108 行 = 93 日」を減らす唯一の外部根拠のある規則。
- **注意**: 本論文は**事前登録を言っていない**。この repo の事前登録(PREREG_V0・holdout)は**独自採用のまま**で、外部根拠は [Larooij & Törnberg](validation__larooij2025_generative-abm-validation.md) の「pre-registered experimental benchmarks」の 1 行に依る。

## コスト/スケール含意

N=30 seed/条件 × 摂動水準 3 × 事例 2。**この repo で 30 seed は現行 9.167 h/本 では 275 h = 11.5 日**([HERMES メモ](compute__matsim2020_hermes.md) の表)。**40 万体で TRAILS をそのままやることはできない**。やるなら下見規模(mock 5,000)で TRAILS-R を測り、40 万体では 8 seed に留める、という 2 段構え。

## 批判・限界

- **査読なし**。2 事例のみ(囚人のジレンマ・エコーチェンバー)。どちらも**この repo の場面(都市の生活行動)と遠い**。
- 絶対値が無いので、76 pt が「80%→4%」なのか「50%→−26%(不可能)」なのか読めない。**親の一次確認では Figure 1 の絶対値を見ること**。
- TRAILS は**分類**であって手続きではない。何をどれだけ振るかは決めない。
- 付録 A(具体例の Table 2/3)未読。

## 関連

[[validation__larooij2025_generative-abm-validation]] ・ [[mas__li2026_agents-not-sufficient]] ・ [[agents__goodyear2025_state-representation]] ・ `../v2-llm-social-sim-timeline-seed.md` #13・#14
