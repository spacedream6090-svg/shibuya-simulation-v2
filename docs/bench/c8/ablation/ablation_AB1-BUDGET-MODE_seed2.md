# ablation ① AB1-BUDGET-MODE — チャネル固定枠 vs 同一総トークンの単一ランキング(義務)

- 設計出典: 知覚契約書 §3.2(義務 ablation)・§8 第1陣 ①・§9 完了条件・§10.3 卒業条件
- 規模: {'agents': 5000, 'ticks': 1440, 'seed': 2} ・経路: fleet
- 切替: 実装済 / cli.run(budget_mode='fixed'|'ranking') / CLI --budget-mode {fixed,ranking}

## 腕ごとの実測

| 構成 | 呼数 | 呼/体/日 | 書式エラー率 | 入力tok平均 | 気づき/事象 | 保存則 | final_hash |
|---|---|---|---|---|---|---|---|
| fixed_slots | 50,000 | 10.00 | 0.0076 | 914.1 | 250.833 | はい | 5de42abfec0bce16 |
| single_ranking | 50,000 | 10.00 | 0.0103 | 916.3 | 250.500 | はい | 6480d117b64e4381 |

## baseline との差

| 構成 | 行動分布 JSD[bits] | 帰無参照 | 帰無超え | Δ呼数 | Δ書式エラー率 | final_hash 一致 |
|---|---|---|---|---|---|---|
| single_ranking | 0.0093 | 0.0035 | はい | 0 | 0.0027 | いいえ |
