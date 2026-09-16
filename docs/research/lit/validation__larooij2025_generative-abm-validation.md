# Larooij & Törnberg 2025 — Validation is the central challenge for generative social simulation

- リンク: https://link.springer.com/article/10.1007/s10462-025-11412-6 | DOI: https://doi.org/10.1007/s10462-025-11412-6 | 全文: https://pmc.ncbi.nlm.nih.gov/articles/PMC12627210/ | 分野: 検証と V&V #22 / 計算社会科学 #25 / 科学哲学 #26 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-16・サブが PMC の HTML 全文を WebFetch。**Discussion の途中で切れている**=末尾の提言は未確認)。**親確認(第202)**: Springer OA の PDF を親が pymupdf(stream・保存なし)で全文読解。「35 papers that met the eligibility criteria」「15 out of 35 studies rely solely on subjective assessments」「22 use such assessments as their primary validation method」「pre-registered experimental benchmarks, rather than face-validity alone」「Data leakage represents a serious risk for such validation approaches」を逐語一致で確認(Discussion 末尾まで読めた)。。Artificial Intelligence Review 59(1) Article 15・受理 2025-09-24・オンライン公開 2025-11-18。著者 Maik Larooij, Petter Törnberg(アムステルダム大学)。副題「a critical review of LLMs in agent-based modeling」。

## 主張(claim)

生成 ABM は ABM の積年の問題(経験的接地・較正・検証)を**和らげるどころか悪化させる**。黒箱だから。いま実際に行われている検証の多くは**face validity(もっともらしさ)**か、機構と緩くしか結びつかない出力指標であり、生成 ABM は「形式モデルの簡潔さも、データ駆動手法の経験的妥当性も持たない」中間地帯にいる。

## 機構(mechanism)— 系統的レビューの手続き

PRISMA 2020。**Scopus 検索を 2026 年でなく 2025-03-27 に実施 → 209 本**。後ろ向き雪だるま(参考文献・サーベイから追加)。題目/抄録 → 全文の 2 段選別 → 「**We identified 35 papers that met the eligibility criteria.**」(逐語 ≤125 字)。除外の内訳は PRISMA 図(Fig. 1)の中だけ。

## 数値(出所つき)

**Table 2 — 検証手法の分類(35 本・主 / 副。主の合計 41 = 複数併用)**

| 検証手法 | 主 | 副 | 主の割合 |
|---|---|---|---|
| 人(らしさ)の判断 | 12 | 2 | 34% |
| よく知られた社会パターン | **14** | 6 | **40%** |
| 他モデル(主観的) | 1 | 3 | — |
| 人が生成したデータ | 12 | 4 | 34% |
| 内部整合性 | 1 | 3 | — |
| 他モデル(客観的) | 1 | 2 | — |

- 逐語(≤125 字・Discussion): 「**15 out of 35 studies rely solely on subjective assessments**」(≈43%)「**and 22 use such assessments as their primary validation method**」(≈63%)。「**roughly half of the reviewed studies incorporate some form of external, objective validation.**」
- Table 1(対象現象): プロフィール 8 / 情動 2 / 会話・内容 10 / 社会的気づき 5 / 意思決定 7 / 意見 2 / ネットワーク伝播 8 / ネットワーク構造 5 / 社会動態 10。**21 本が単一カテゴリ・平均 1.63**。

**face validity の警告(逐語 ≤125 字)**

- 抄録: 「**studies often rely on face-validity or outcome measures that are only loosely tied to underlying mechanisms.**」
- Discussion: 「**At worst, validation consists of asking an LLM to evaluate the plausibility of its own output**」
- Discussion: 主観的検査は「**[does] not, on [its] own, constitute evidence of operational validity.**」
- Discussion: 「**"calibration" is thus reduced to prompt engineering, and generally aimed at improving face-validity.**」
- 客観比較をすると、データは「face-validity の信じやすさが示唆するよりはるかに似ていない」。

**データ漏洩(data leakage)の警告(逐語 ≤125 字)**

- §Generative ABMs: 「**what may appear as emergent dynamic can instead stem from a form of "data leakage"**」— LLM は科学文献で訓練されているので、**過去の出来事の再生や、既知の社会ネットワークの補完**をしているだけかもしれない。
- §Validation against well-known social patterns: 「**Data leakage represents a serious risk for such validation approaches**」— 先行研究が訓練データに入っている以上、**LLM は発表済みの結果を再生しているだけ**かもしれない。
- 具体例として挙がっている「既知パターン」: スケールフリー網・人格と偽情報の関連・友人関係のパラドックス・エコーチェンバー。**= この repo が「stylized facts」として使おうとしている類**。

**提言(§Validation in ABMs・最小限の物差し 3 点)**

1. **目的との整合**(purpose alignment)
2. **外部的接地** — 人のデータか「**pre-registered experimental benchmarks, rather than face-validity alone**」(逐語 ≤125 字)
3. **頑健性** — 「**results reported across multiple runs and, where feasible, limited sensitivity checks for key parameters.**」

加えて: LLM-as-judge の循環を避ける / **内部整合性は verification であって validation ではない** / 人口モデルなら「属性を調査・デジタル痕跡の分布に結びつけ、部分集団水準のパターンを検証する」。

## 効く箇所(seam)

- **holdout の作法**(`../../bench/c7/prereg_arms_v1.md`)= 提言 2 の「pre-registered experimental benchmarks」そのもの。**この repo は既に提言 3 点のうち 1・2 を満たしている**。3(多ラン + 感度)は G-8 の 8 seed アンサンブル(S1)で満たす予定=**未実施**。
- **現実整合アンカー台帳**(`data/ground_truth/registry.yaml`)= 「外部的接地」の実務形。
- **データ漏洩は「よく知られたパターンでの検証」に固有**。この repo の holdout(KDDI の在圏データ)は**公開文献に無い**ので、**漏洩の筋では汚染されにくい**=これが本 repo の位置どりの外部根拠になる。逆に `v2-pattern-ledger.md` A2「対面接触時間のべき則」のような**公刊された stylized facts は漏洩の疑いがかかる**。

## 「結論でなく機構として」の入れ方

- **借りない**: 35 本の個別評価。
- **借りる**: (1) **検証手法の 6 分類**を受入表の欄に写し、この repo の各判定行が「主観 / 客観」のどちらかを明示する。(2) **「内部整合性は verification」**という線引き = テープ再生の同一ハッシュを「検証(validation)」と呼ばない規律。(3) **漏洩の疑いを台帳の欄にする** = パターン台帳の各行に「このパターンは公刊されているか」の欄を足す候補。

## コスト/スケール含意

なし(レビュー論文)。ただし提言 3(多ラン + 感度)は**この repo で 101 h ≒ 4.2 日**(S1 の見積もり)。**検証の値段が本体の値段と同じ桁**になるという含意。

## 批判・限界

- Scopus 単独・**2025-03-27 まで**。2025 年後半以降の道具(頑健性監査・反実仮想再生)は入っていない。
- 単一コーダー(著者自身が「将来のレビューは複数コーダーと一致率を使うべき」と書いている)。
- 何を「客観的」と呼ぶかの線引きが、この repo の「アンカー台帳 vs holdout」の線引きと一致するかは未確認。
- **PMC 全文は Discussion の途中で切れた**(サブの取得範囲)。末尾の提言は未読=[答申 §3](../v2-r2-llm-social-sim-fulltext-check.md) の空欄。

## 関連

[[validation__operational-validity-overview]] ・ [[validation__ye2026_robustness-audits]] ・ [[mas__li2026_agents-not-sufficient]] ・ `../../bench/c7/prereg_arms_v1.md`
