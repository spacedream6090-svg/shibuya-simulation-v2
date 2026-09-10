# ablation ⑥ AB6-AD-ZERO — 広告ゼロ(収益化の主要領域=効果の存在を早期確認)

- 設計出典: 知覚契約書 §8 第1陣 ⑥・§3.2(B2.signage 25 tok・件数 1 は expedient)・§8 ablation 予約(広告ゼロ)・MEMORY「収益化: 広告・情報伝播領域」
- 規模: {'agents': 5000, 'ticks': 1440, 'seed': 2} ・経路: fleet
- 切替: 実装済 / cli.run(signage=False) / CLI --no-signage

## 腕ごとの実測

| 構成 | 呼数 | 呼/体/日 | 書式エラー率 | 入力tok平均 | 気づき/事象 | 保存則 | final_hash |
|---|---|---|---|---|---|---|---|
| signage_on | 50,000 | 10.00 | 0.0076 | 914.1 | 250.833 | はい | 5de42abfec0bce16 |
| signage_off | 50,000 | 10.00 | 0.0065 | 898.9 | 250.000 | はい | 22d4fc15d21f19a3 |

## baseline との差

| 構成 | 行動分布 JSD[bits] | 帰無参照 | 帰無超え | Δ呼数 | Δ書式エラー率 | final_hash 一致 |
|---|---|---|---|---|---|---|
| signage_off | 0.0006 | 0.0035 | いいえ | 0 | -0.0010 | いいえ |
