# ten Broeke, van Voorn & Ligtenberg 2016 — Which Sensitivity Analysis Method Should I Use for My Agent-Based Model?

- リンク: https://jasss.soc.surrey.ac.uk/19/1/5.html (DOI 10.18564/jasss.2857) | 分野: 統計学・因果推論 #23 / ABM 方法論 #21 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-16・第200・サブ全文実読 → 親が再取得し逐語一致)。

## 主張(claim)

感度解析の手法(OFAT・回帰・Sobol')で反復回数の要求は違う。確率的変動の寄与を**測って**追加反復の要否を決める。

## 機構(mechanism)

- 分布推定: 「**We perform 10,000 replicate runs** in the default parameter set」→「the coefficient of variation is **largely stabilised after a few hundred replicates**」(§5.4・式 7 c_v=σ(n)/μ(n)・Lorscheid 2012 を引用)。
- 感度解析: OFAT **10** replicates/設定・回帰 **5**・Sobol' **0**(点数を増やす方を優先)。
- **追加不要の証明**(§5.9): 「**The mean output variance over replicates is 0.88% of the output variance over all samples.**」→ 確率性の分散が無視できる → 「we do not need to increase the number of replicate runs per parameter setting」。

## 効く箇所(seam)

- **追加ラン 0 本でできる正当化**: 既存 seed 違い(C6 T7・C8 AB6 seed 2)と条件間の差(c7-day-2/3/4)から **seed 間分散 ÷ 条件間分散** を出す。数 % 以下なら「シナリオの順位づけに 8 で足りる」を文献の手続きで示せる(答申 §2 (G)・§5 の 3 手の 3 つ目)。
- D-44(122 expedient の感度試験)には「回帰ベースなら 5 反復」「Sobol' なら反復 0」という**省き方の根拠**になる。

## 「結論でなく機構として」の入れ方

反復数を一律に決めず、**目的(分布推定/順位づけ/分散分解)ごとに要求を分ける**。我々の初アンサンブルは「分布推定」なので数百が本来の要求、「順位づけ」なら (G) で足りる可能性。

- 関連: [[stats__lee2015_abm-output-analysis]] [[stats__lorscheid2012_replication-doe]]
