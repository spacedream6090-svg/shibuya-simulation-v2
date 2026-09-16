# Shah 2026 — Causal Agent Replay: Counterfactual Attribution for LLM-Agent Failures

- リンク: https://arxiv.org/abs/2606.08275 | 分野: 統計学・因果推論 #23 / 計算機科学(決定論)#28 | 重要度: **P1**
- **一次確認**: **実読**(2026-09-16・サブが WebFetch で abs + `arxiv.org/html/2606.08275v1` 本文を取得)。**親未確認**。v1 のみ(2026-06-06)。**Comments 欄に会議名は無く**、公開実装へのリンクのみ。著者 Jaineet Shah(単著)。

## 主張(claim)

エージェントが失敗したとき、**どの手番が原因か**は観測可能性でも評価でも分からない。「**the step that executes the harmful action is usually not the step that decided on it**」(逐語 ≤125 字)。LLM 審判による帰属は相関にすぎず、Who&When ベンチで手番水準の正解率は約 **14%**。代わりに**因果**で測る。

## 機構(mechanism)— 介入再生の手続き

**擬似コード・番号つきアルゴリズムは無い**(散文で §2〜4)。手続き:

1. **状態の再構成**: 記録再生で手番 k の状態 s_k(system prompt・道具スキーマ・全履歴)を厳密に復元(§3)。
2. **介入と前進**(逐語 ≤125 字・§4): 「**hold steps [0,k) at their factual actions, apply do_resample(k), and run forward K times**」。
3. **下流は固定しない**: 「**An intervention is a do(·) operation on one variable, after which the agent re-decides everything downstream.**」
4. P(bad | do(k)) と観測ランからのずれを推定。
- **固定するもの** = 手番 0..k−1 の事実の行動・道具のモック。**再抽選するもの** = 手番 k と**それ以降の全確率的手番**。

**介入代数(5 演算)**

| 演算 | 中身 |
|---|---|
| `do_resample` | 方策を変えずに a_k を引き直す =「**the null intervention**」 |
| `do_action` | a_k を指定の行動に固定 |
| `do_observation` | 手番 k の道具の返り値 o_k を差し替え |
| `do_context` | 手番 k のメッセージ履歴を編集 |
| `do_policy` | 手番 k 以降のモデルを差し替え |

**point-of-commitment 則**(逐語 ≤125 字): 因果の所在は「**the latest step whose effect's confidence interval still excludes zero**」。
**これが潰す交絡**: 「**resampling step k also re-rolls every downstream stochastic step**」ので「**an early irrelevant step shows an effect too, because it re-rolls the genuinely pivotal step downstream**」。→ **効果の大きさだけでは原因を特定できない**ので、**「ゼロを外す最も遅い手番」**を取る。

**予算と信頼区間**: 具体的な K の値は本文に無い。対比推定 = 手番あたり K ロールアウト・割合に Wilson 区間・差にブートストラップ区間。Shapley = 順列の Monte-Carlo(逆順ペアの対蹠変量)・v(S)=P(bad|held=S)・正規近似区間・**v(S) はあえてキャッシュしない**・truncated MC Shapley は使わない・「**budget-bounded with a circuit breaker**」。

**検証**: 正解を植えた合成 SCM。Shapley が 2 手番の相互作用を **0.44 / 0.45 / ≈0**、効率和 **0.909**(解析値 0.91)で復元。

## R-2 の問い「共通乱数」への答え

**扱っていない。** 対比効果は**総効果**であり、直接効果を分けるには「**common random numbers across branches, which is hard across divergent LLM contexts**」が要るとして**将来課題**に置いている。seed が効くのは局所だけ: 「**a single-stream local model with a fixed seed replays exactly**」。ホストされたモデルでは再現性を主張せず「**reports an action-match rate for replay rather than asserting reproducibility**」。

## 効く箇所(seam)

- **この repo は再生の側を先に持っている**: T2-c テープ再生(c7-day-3 の最終ハッシュ一致)+ **単一ストリーム・ローカル vLLM・固定 seed** = 本論文が「厳密に再生できる」と認めた条件そのもの。**したがってこの repo は共通乱数を実際に持てる可能性がある**(本論文が「難しい」と言ったのは API 越しの話)。
- **持っていないのは介入再生**: `do_action` / `do_observation` / `do_context` に相当する口が無い。テープは**同一を確認する**ためだけに使っている。
- 効きそうな用途: D-73(自由意図の集中)や D-56/D-62(就寝)のような**「なぜそうなったか」の検死**。いまは腕を分けて全ランを回している(1 本 9.167 h)が、**介入再生なら 1 手番から先だけを K 回**。

## 「結論でなく機構として」の入れ方

- **借りない**: 公開実装・Shapley の重い部分・Who&When ベンチ。
- **借りる**: (1) **介入代数の 5 演算の名前と意味**を、この repo のテープ再生 API の語彙にする。(2) **point-of-commitment 則**=「効果がゼロを外す最も遅い手番」= 下流再抽選の交絡を避ける唯一の規則。これを知らずに「早い手番ほど効果が大きい」と読むと**必ず間違える**。(3) **対比 = Wilson 区間・差 = ブートストラップ**という区間の付け方。
- **前提条件**: `do_*` が意味を持つには**手番の境界が定義されていること**。この repo は計画境界起床があるので境界はある。

## コスト/スケール含意

- 1 手番あたり K ロールアウト。**前進再実行なので、手番 k が早いほど残りが長く高くつく**。40 万体の 1 シミュ日で任意の手番を K=30 で再生すると、最悪ランの大半をやり直す = **9.167 h × K**。
- 現実的には**個体 1 体・1 日の軌跡**に限って介入再生する(体あたりの呼は 6.94 呼/日)= **数百呼で 1 体の検死ができる**。これが本論文をこの repo に入れる唯一の安い道。

## 批判・限界

- **単著・査読なし**。検証が**合成 SCM のみ**(実エージェントの失敗での正解は無い)。
- 14% という比較対象の数値は他者のベンチの報告。
- 共通乱数を扱わない = **総効果しか測れない**。この repo が知りたいのは往々にして直接効果。
- Shapley は手番数に対して重い。K も明示が無い。

## 関連

[[validation__ye2026_robustness-audits]] ・ [[mas__li2026_agents-not-sufficient]] ・ `../v2-llm-social-sim-timeline-seed.md` #15
