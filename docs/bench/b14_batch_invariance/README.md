# B14 バッチ不変性の自検証とコスト差(2026-09-07・借用サーバー・8B INT8・契約書v1サイズ)

> 目的: U8/U9の再現性テストT6の実測。vLLM公式内の矛盾(batch invariance要件: features頁「compute capability 8.0+」vs env_vars頁「>= 9.0」・借用機A5000=8.6)と、決定的推論のコスト(原典=約2倍 vs 当方ベンチ−2%以下)の乖離を解く。
> 構成: GPU4=VLLM_BATCH_INVARIANT=1・GPU5=0(他は同一: 8B INT8・max-model-len 4096・max-num-seqs 128・prefix cache ON・seed 20260907)。入力=品質プローブv0の①②⑥v1から32本(核)+⑥v0/full 200本(充填)。スクリプト=tools/bench_spikes/batch_invariance_check.py・結果=inv1.json/inv0.json。

| 構成 | T6a 温度0: 単独(逐次) vs 混在(c64)の出力一致 | T6a logprobs一致 | T6b 温度0.7+seed固定: 充填順序を変えた2回の一致 | 混在c64のスループット |
|---|---|---|---|---|
| **BATCH_INVARIANT=1** | **32/32** | **32/32** | **32/32** | 6.09呼/s |
| BATCH_INVARIANT=0 | 3/32 | 0/32 | 3/32 | 5.94呼/s |
| ON vs OFF の単独温度0出力一致(T6c) | 2/32(カーネルが違うので別物) | | | |

## 結論
1. **A5000(CC 8.6)でバッチ不変性は成立する**(温度0でもseed付き温度0.7でも、バッチ構成を変えて全32本が一致)。公式env_vars頁の「>= 9.0」は実測と矛盾=features頁の「8.0+」側が実態。manifestには「本機での自検証T6合格」を記録。
2. **不変性OFFでは温度0でも結果がバッチ構成に依存する**(32本中3本しか一致せず、logprobsは全件不一致)。再現性を主張するランは必ずON。
3. **コスト差は無し**(ON 6.09 vs OFF 5.94呼/s=ONがわずかに速い)。原典の「約2倍」はvLLM実装前の未最適化カーネル・生成律速の条件であり、prefill律速のv2負荷形状には当たらない=ベンチ台帳の「−2%以下」と整合。
4. 含意: 検証ラン(mode: holdout)=BATCH_INVARIANT=1・TP1・温度0・sha256_cbor でLLM層のbit再現が本機では主張できる。本番(温度0.7・DP7)は分布同値の宣言のまま。
