# C8 TRAILS 被覆表 v0(第203・D-75 (d))

> **表だけ・ランは増やさない。**本書は「どの次元を監査したか / していないか」を宣言するだけの台帳で、新しい腕も新しいランも生まない。
> **第2波の候補は D-75 (e)**(v1 の `ablate.prompt_paraphrase`(S-16)を v2 の腕として戻す=TRAILS-R の唯一の実装資産)。採否はユーザー判断・S1 の後。

- **原典**: Ye, Cao, Chen & Ferrara 2026「Stop Drawing Scientific Claims from LLM Social Simulations Without Robustness Audits」(arXiv [2605.18890](https://arxiv.org/abs/2605.18890) v1)**Table 1**。
  **一次確認**: 親(第202)が本文を再読し、TRAILS-D が Micro 4 / Meso 2 / Macro 2、TRAILS-R が層なしの 5 次元であることを確認済み(**付録 A の Table 2/3 は親も未読**)。次元名は原典の英語をそのまま置く([lit メモ](../../research/lit/validation__ye2026_robustness-audits.md))。
- **借りないもの**: 本論文の 76 pt(ペルソナ書式で協力率が 76 ポイント下がる)は**モデルも場面も違う**ので、この repo の主張には使わない。借りるのは**被覆表の型**と §6 の報告様式(何を摂動し・何が安定で・何が敏感で・**何を監査しなかったか**)だけ。
- **状態の語**: **監査済み**=腕として振り、実 LLM のランの結果が `docs/bench/c8/ablation/` にある / **未監査(宣言)**=振っていない(切替口だけある場合もここに入れる) / **該当せず**=この repo の構成に対応物が無い。
  **根拠が無いものは「未監査」と書く**(埋めない)。参照した資産: `tools/c8/ablations_v1.json`(AB1〜AB7)・`docs/bench/c8/ablation/`・`docs/bench/c7/prereg_arms_v1.md`・運用設計書 §1.4 の T1-T9。

## 1. TRAILS-D(設計水準・8 次元)

| 層 | 次元 | 状態 | 監査の実体(腕・ラン) | 備考 |
|---|---|---|---|---|
| Micro | Model substrate | **未監査(宣言)** | なし | 実 LLM は **Qwen3-8B INT8 の 1 銘柄**のみ(manifest に engine/quant/decoding は記録される)。銘柄・量子化・版を振った腕は `ablations_v1.json` に無い。モデル同一性の論点は PENDING **D-72** |
| Micro | Agent specification | **未監査(宣言)** | なし | D-68「人格プロンプトを増やさない」。W17 v2 段1 の自己生成 250〜350 字は**体ごとに書式が違う**が、条件として振ってはいない(素材であって腕ではない) |
| Micro | Internal state and cognition | **未監査(宣言)** | なし | 認知 3 層 LOD(T0/T1/T2)の昇格閾値・内部状態の書き方を振った腕は無い。AB1 は**入力側の予算配分**であって内部状態の表現ではない(別の量) |
| Micro | Memory and temporality | **未監査(宣言)** | なし | AB5-INTROSPECTION(内省 1.05 回/日 vs 2-3 回/日)は `status: blocked_feature`=**前提機能が未実装**で `runs` が空(共有ベースラインの 8 ランにも入っていない) |
| Meso | Interaction protocol | **未監査(宣言)** | なし | AB3-REFRACTORY-PROX(近接入替の不応期 15 分 ±50%)は切替口が実装済みだが**現状 no-op**——近接入替を起床候補に出す側が未実装(知覚契約書 §9 第2陣)。会話側は Phase 3 |
| Meso | Intervention design | **監査済み** | **AB6-AD-ZERO**(広告あり `signage_on` / なし `signage_off`)・5,000 体 × 1,440 tick・経路 fleet(実 LLM)・**seed 1**([ablation_AB6-AD-ZERO.md](ablation/ablation_AB6-AD-ZERO.md))と **seed 2**([_seed2.md](ablation/ablation_AB6-AD-ZERO_seed2.md)) | 行動分布 JSD **0.0009 bits**(seed 1)・**0.0006 bits**(seed 2)=いずれも帰無参照 0.0035 未満(**帰無を超えない**)。40 万体では未実施 |
| Macro | Environment structure | **未監査(宣言)** | なし | AB2-PNOTICE-D50(d50 を 0.5×/2×)は切替口実装済みだが**実 LLM のランは未実施**(`docs/bench/c8/ablation/` に出力が無い)。下見(実資産 2,000 体 × 90 tick)では A4 既定の到達差が 1 人以下=「何を測る腕なのか」は PENDING **D-49** |
| Macro | Population and scale | **未監査(宣言)** | なし | 規模の実測は **5,000 体** と **390,067 体** の 2 点あるが、**腕として振っていない**(自分のスケール指数を測っていない)。母集団側の感度腕 **c7-day-5**(出勤率 0.88)は[事前登録](../c7/prereg_arms_v1.md) §1 に登録済み・**未実行** |

## 2. TRAILS-R(表現水準・5 次元・層の割り当ては原典にも無い)

| 次元 | 状態 | 監査の実体(腕・ラン) | 備考 |
|---|---|---|---|
| Representational format | **未監査(宣言)** | なし | **注記**: AB7-OPEN-INTENT(24 語のホワイトリストを**見せる / 見せない**)は seed 1・2 とも実行済み([_s1.md](ablation/ablation_AB7-OPEN-INTENT_s1.md)・[_s2.md](ablation/ablation_AB7-OPEN-INTENT_s2.md))だが、振っているのは**提示する選択肢集合の有無**であって、原典の摂動(**内容は同一**のまま Plain / Descriptive / Tabular に書き分ける)とは別の量。**部分的に当たると数えるかは親判断**——本表では未監査に置いた |
| Instruction hierarchy | **未監査(宣言)** | なし | 指示の階層(体裁・優先順位・system/user の置き方)を振った腕は無い |
| Linguistic framing | **未監査(宣言)** | なし | 言い回しの言い換えを振る資産は v1 の `ablate.prompt_paraphrase`(S-16)だけで、**v2 に移っていない**(= D-75 (e)・第2波の候補) |
| Context representation | **未監査(宣言)** | なし | **注記**: AB1-BUDGET-MODE(チャネル固定枠 vs **同一総トークン**の単一ランキング)は文脈の**配分**を同一予算で振っており、部分的に当たる可能性がある=**親判断**。本表では未監査に置いた。実測は 5,000 体 × 1,440 tick・seed 1/2 で JSD **0.0097 bits**(帰無 0.0035 を**超える**=動く側)([ablation_AB1-BUDGET-MODE.md](ablation/ablation_AB1-BUDGET-MODE.md)) |
| Interaction sequencing | **未監査(宣言)** | なし | **注記**: T5(順序バイアス・`tests/c6/test_t5_order_bias.py` 8 本・個体 ID 順との相関 \|r\| ≤ 0.05)は**エンジン側の処理順**の検査であって、プロンプト内の提示順・手番順を**摂動した**ものではない=別の量 |

## 3. 集計

| 状態 | 件数 |
|---|---|
| 監査済み | **1**(Intervention design のみ) |
| 未監査(宣言) | **12** |
| 該当せず | **0** |

- **TRAILS-D 8 次元のうち監査済みは 1**、**TRAILS-R 5 次元は全て未監査**。原典 §6 の要求(何を摂動し・何が安定で・何が敏感で・**何を監査しなかったか**を書く)に対して、いまの C8 が答えられるのは「広告の有無を振ったら動かなかった(JSD 0.0009 < 帰無 0.0035)」の 1 行だけである。
- 監査済みの 1 本も **5,000 体 × 1 シミュ日・seed 2 本**であって、40 万体では 1 次元も監査していない。

## 4. 空欄・注意(埋めていないもの)

- 原典の**付録 A(Table 2/3)= 各次元の具体例**はサブも親も未読。次元名の解釈(とくに Context representation と Interaction sequencing の境界)は**本表の読み替えであって原典の定義ではない**。AB1・AB7・T5 の 3 つの注記が「部分的に当たるか」を親判断としているのはこのため。
- 原典の監査の量は **N=30 seeds / 条件**。この repo の 40 万体(9.167 h/本)では 30 seed = 275 h ≒ 11.5 日で**そのままは不可能**。lit メモは「下見規模(5,000)で TRAILS-R を測り、40 万体では 8 seed に留める」2 段構えを提案しているが、**これは提案であって決定ではない**(S1 の seed 数は G-8 の expedient 8 本・必要数は D-46/D-70 で再決定)。
- 本表は**第1波(v0)**。腕を足した・ランを回したときに状態だけを書き換える(表の行は増やさない)。
