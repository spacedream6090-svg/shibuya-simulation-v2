# Lorscheid, Heine & Meyer 2012 — Opening the 'black box' of simulations: increased transparency and effective communication through the systematic design of experiments

- リンク: https://link.springer.com/article/10.1007/s10588-011-9097-3 | 分野: 統計学・因果推論 #23 / ABM方法論 #21 | 重要度: **P0**
- **一次確認**: **二次(v1 の読解メモを経由)**。2026-09-15 に親が v1 `docs/lit/method__experiment-design-statistics.md`(2026-07-02・Opus 委譲・出典 URL 検証済みと記載)を実読した。**Springer 原典は未読**(この日は Web 取得が使用上限で停止)。→ [RESEARCH-STATE.md](../RESEARCH-STATE.md) §2-A の A-3 で原典を確認する
- **第200 追記(2026-09-16・L-B)**: 原典は有料で OA コピー無し(Unpaywall `is_oa:false`)=**本文は依然未読**。CV 法の手続き(連続する c_V の差が E 未満で以後も維持・例 E=0.01)は [stats__lee2015_abm-output-analysis](stats__lee2015_abm-output-analysis.md)(共著者に Lorscheid)と [stats__tenbroeke2016_sensitivity-abm](stats__tenbroeke2016_sensitivity-abm.md) の**逐語引用で確認**(親再取得)。8 seed への当て込みは答申 [v2-replication-count-research](../v2-replication-count-research.md) §2 (C)=**梯子が作れず判定不能**。

## なぜこのメモを v2 に起こすか

**v2 には統計学・因果推論 #23 の答申が 1 本も無い**([INDEX.md](../INDEX.md) §2)。そして **G-8「アンサンブルのラン本数」は expedient のまま**置かれている:

> ラン本数の根拠: Monte Carlo標準誤差から逆算(**Siepe et al. 2024の式=未確認**→確認までは「初回=seed群8本・spread-skillで再評価」の expedient)
> — [v2-dashboard-verification-orchestration.md](../../design/v2-dashboard-verification-orchestration.md) §G-8

**v1 は 2026-07 の時点で、この問いに別ルートの答えを持っていた。**

## 主張(claim)

ABM の実験計画を体系化する。**反復回数(replication)は勘や慣習で決めるのではなく、出力の変動係数 CV = σ(n)/μ(n) が安定する点で決める**。

## 機構(mechanism)

- 手順: 応答の定義 → factorial または LHS で設計点を配る → **反復数は CV 収束で決定** → 標準化された報告。
- v1 メモが加えている運用形(**v1 の自前構成であって Lorscheid 原典の記述とは限らない・要区別**):
  - **2 段階掃引**: 粗掃引(設計点 8-12・seed 5-10)→ 変化が急な帯に細掃引(+4-8 点・**seed 15-25 に増強**)。理由=**相転移帯では分散そのものが信号**なので厚く取る。
  - 予算が厳しければ **GP 代理モデル + active learning** で細掃引を代替。
  - CI は **(設計点, seed) 単位の block/hierarchical bootstrap**。naive bootstrap は seed 相関で CI を過小に出す。
  - **pre-registration + multiverse analysis**(判定閾値・窓幅・detrend・judge モデルの分岐を全列挙して頑健性を可視化。ツール RobustiPy)。

## 効く箇所(seam)

1. **G-8 の expedient を解消できる** — 「初回 = seed 群 8 本」を、CV 収束を測って決めた本数に置き換えられる。**D-70(次の性能ゲートをどこに置くか)は N が決まらないと決まらない**ので、ここが先。
2. **2 段階掃引は C8 ablation の設計にそのまま効く** — 全腕を同じ seed 数で回すのは無駄で、差が出る帯だけ厚くする。
3. **multiverse analysis は v2 に一言も無い**(親が `docs/design` と `docs/research` を grep して確認・2026-09-15)。v2 は事前登録を採用済みなので、その隣に置く候補。

## 「結論でなく機構として」の入れ方

数値(seed 5-10 / 15-25)は借りない。借りるのは **「本数は測って決める」という手続き**だけ。v2 では最初のアンサンブルで CV 曲線を取り、その形から本数を決めて事前登録に書く。

## コスト/スケール含意

第190 の計算と直結する。1 本 9.167 h なので:

| N | 所要 | 判定 |
|---|---|---|
| 8(G-8 の現行 expedient) | 73.3 h = 3.1 日 | 週内 ✓ |
| 30 | 275 h = 11.5 日 | ✗ |
| 100 | 917 h = 38.2 日 | ✗ |

→ **CV 収束が 8 本より多くを要求したら、D-70 の (b)「2 h/シミュ日へ」が必須になる**。逆に 8 本で足りるなら (a)+(d) で済む。**この 1 つの測定が D-70 の答えを決める。**

## 批判・限界

- **原典未読**。上の記述は v1 の読解メモに依存している。v1 メモ自体は出典 URL を検証済みと明記しているが、**親は Springer 本文を読んでいない**。
- CV 収束法は**出力が 1 つのスカラーであること**を暗に仮定している。v2 の受入表は 16 行あり、行ごとに必要本数が違う可能性が高い。**どの指標の CV で決めるかを先に決める必要がある**(未解決)。
- v1 の文脈は「k 掃引と相転移の検出」(v1 の中心の問い)。**v2 の問いは再現とアンサンブル予報**なので、細掃引の議論はそのままでは移らない。

## 関連

[[compute__agentsociety2025_parallel_framework]] ・ [[compute__matsim2020_hermes]] ・ [[validation__operational-validity-overview]] ・ v1 `docs/lit/method__experiment-design-statistics.md`(出所)
