# Lee et al. 2015 — The Complexities of Agent-Based Modeling Output Analysis

- リンク: https://jasss.soc.surrey.ac.uk/18/4/4.html (DOI 10.18564/jasss.2897) | 分野: 統計学・因果推論 #23 / ABM 方法論 #21 | 重要度: **P0**
- **一次確認**: **実読**(2026-09-16・第200・サブ Opus 5 が全文実読 → 親が同ページを再取得し逐語一致を確認)。著者 10 名(Lee, Filatova, Ligmann-Zielinska, Hassani-Mahmooei, Stonedahl, **Lorscheid**, Voinov, Polhill, Sun, Parker)。Lorscheid 2012 の CV 法を**逐語で引く二次**として使う(原典は有料・未読)。

## 主張(claim)

大規模 ABM では「最小限の必要ラン数」が問い。文献の標本サイズは「too low, conveniently selected(**100 以下が普通**), or exorbitantly high」。

## 機構(mechanism)— Lorscheid の CV 法(§2.4–2.6)

c_V=σ/μ を複数の n(例 10, 500, 1000, 5000, 10000)で計算し、「**The sample size at which the difference between consecutive c_V's falls below a criterion, E, and remains so** is considered a minimum sample size」。例: c_V {0.42, 0.28, 0.21, 0.21, 0.21}・E=0.01 → n=1000 が安定点。多指標は各安定点の**最大値**。

## 批判・限界(§2.7・§2.11)

- 「**we urge some caution in using c_V**」— 固定 E は **μ≈0 の指標で n_min を過大評価**し、μ が大きい指標で過小評価する。0 を取りうる指標には使わない。
- 代替=窓付き分散(相対 ω_n² が **0.20** を下回る n・「semi-subjective criterion」)。
- 検出力からの n_min ≥ 2(s²/δ)(t_{ν,1−α/2}+t_{ν,1−β/2})²。歪んだ分布では過大評価→経験的検出力か Wilcoxon。

## 効く箇所(seam)

- **G-8「初回 seed 群 8 本」**: 8 本では c_V の梯子は n∈{2,4,8} の入れ子までで右端が 8=「以後も維持」が検証できない(答申 [v2-replication-count-research](../v2-replication-count-research.md) §2 (C))。
- **待ち合わせ・稀な行動を指標にするなら c_V は不向き**(μ≈0)。
- 「効果量を先に決めてから n_min」=事前登録に効果量の宣言が要る。

## 「結論でなく機構として」の入れ方

ラン数を文献値で決めるのではなく、**「出力分散の安定 → 効果量の宣言 → n_min」の 2 段の手続き**を事前登録 v1.2 に書く。

- 関連: [[stats__lorscheid2012_replication-doe]] [[stats__tenbroeke2016_sensitivity-abm]] [[stats__siepe2024_simulation-study-template]]
