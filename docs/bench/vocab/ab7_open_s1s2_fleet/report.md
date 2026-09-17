# 段2 起草 + 段3 静的検査 — 未定義行動の裁定バッチ(D-71・オフライン)

> 入力 2 本 / 語 36 / 未定義行 1,275。起草 10(件数予算 10)・裁定 fleet(model=Qwen3-8B-int8・温度 0.0・endpoints 7)・プロンプト vocab-draft-v0 sha256 6acda67c8c9af25d…
>
> **動的検査 ①(発火と保存則)③(世界状態の差分)④(非退化)は未実施**(affordance をエンジンに実装したあとの mock ランで測る)。ここは静的 (s1)〜(s6) のみ。

## 1. 入力

| 入力 | 語 | 記録行 | セル | 辞書版 |
|---|---:|---:|---|---|
| vocab_in/ab7_open_s1.json | 26 | 603 | prompt_block | undefined-synonyms-v2 |
| vocab_in/ab7_open_s2.json | 30 | 672 | prompt_block | undefined-synonyms-v2 |

## 2. 上位 10 語(順位=被覆 体×セル×時間帯)

| 位 | 語 | 行 | 体 | セル | 時間帯 | 被覆 | 段0 写像先 | 政策分類 | 最近傍(距離) | 判定 |
|---:|---|---:|---:|---:|---:|---:|---|---|---|---|
| 1 | 食事 | 678 | 634 | 197 | 22 | 2,747,756 | — | 未定義 | 返事→会話(0.50) | NEEDS_DYNAMIC |
| 2 | 行動 | 196 | 194 | 86 | 20 | 333,680 | — | 未定義 | 移動→移動(0.50) | NEEDS_DYNAMIC |
| 3 | 近づく | 109 | 101 | 34 | 18 | 61,812 | — | 未定義 | 歩く→移動(0.40) | NEEDS_DYNAMIC |
| 4 | 近寄る | 68 | 65 | 39 | 17 | 43,095 | — | 未定義 | 乗る→乗車(0.40) | NEEDS_DYNAMIC |
| 5 | 見る | 69 | 61 | 17 | 19 | 19,703 | — | 未定義 | 見回る→移動(0.80) | DICTIONARY_ROW_SUFFICES |
| 6 | 進む | 23 | 23 | 22 | 8 | 4,048 | — | 未定義 | 休む→休憩(0.50) | NEEDS_DYNAMIC |
| 7 | 持つ | 16 | 16 | 14 | 8 | 1,792 | — | 未定義 | 待つ→待機(0.50) | NEEDS_DYNAMIC |
| 8 | 取る | 18 | 17 | 12 | 7 | 1,428 | — | 未定義 | 乗る→乗車(0.50) | NEEDS_DYNAMIC |
| 9 | 飲食 | 15 | 14 | 9 | 9 | 1,134 | — | 未定義 | 飲む→購入(0.50) | REJECTED |
| 10 | 避雨 | 18 | 18 | 16 | 1 | 288 | — | 未定義 | —(0.00) | NEEDS_DYNAMIC |

## 3. 不採用・保持の理由

| 語 | 理由 |
|---|---|
| 飲食 | REVIEW_KEYWORD:在庫 |

- 保持のみ: 被覆の下限 N=10 体 未満 **25 語** / 件数予算の外 **1 語**(**全件保持**・次バッチへ繰り越す)
- 新語不要(s5・辞書行の追加で済む・距離 ≥ 0.75): 見る→見回る(→移動・0.80)
  - **これは自動却下ではない**(決定 I は (a) 人手 +(b) 距離の列。(c) 類似での自動却下は『意味損失を再生産する』として採らない)。字面の距離は写像先の意味を見ないので、**親が 1 行ずつ確かめる**。

## 4. 要動的検査(①③④)と人手判断

| 語 | 判定 | 対象クラス | affordance | 該当行(②の静的見積り) |
|---|---|---|---|---:|
| 食事 | NEEDS_DYNAMIC | 飲食店 | order_meal | 678 行 / 634 体 |
| 行動 | NEEDS_DYNAMIC | 電車 | ride_on | 196 行 / 194 体 |
| 近づく | NEEDS_DYNAMIC | 乗客 | approach | 109 行 / 101 体 |
| 近寄る | NEEDS_DYNAMIC | 乗客 | approach_to_platform | 68 行 / 65 体 |
| 見る | DICTIONARY_ROW_SUFFICES | ディスプレイ | visual_inspection | 69 行 / 61 体 |
| 進む | NEEDS_DYNAMIC | 通路 | move_along | 23 行 / 23 体 |
| 持つ | NEEDS_DYNAMIC | 荷物 | carry_object | 16 行 / 16 体 |
| 取る | NEEDS_DYNAMIC | 棚 | take_item | 18 行 / 17 体 |
| 避雨 | NEEDS_DYNAMIC | 建物 | shelter_from_rain | 18 行 / 18 体 |

## 5. 指紋(決定 G・6 つ)

```json
{
 "1_thresholds": {
  "threshold_agents": 10,
  "batch_budget": 10,
  "coverage_formula": "distinct_agents × max(1, distinct_cells) × max(1, distinct_hours)",
  "note": "N は『被覆の下限』に降格(決定 A)。max(1,…) は expedient"
 },
 "2_field_order": [
  "word",
  "target_class",
  "affordance",
  "preconditions",
  "effects",
  "cost",
  "failure_codes",
  "conservation_accounts",
  "pattern_ledger_row",
  "rationale"
 ],
 "3_adjudicator": {
  "client": "fleet",
  "model": "Qwen3-8B-int8",
  "temperature": 0.0,
  "n_endpoints": 7,
  "prompt_version": "vocab-draft-v0",
  "prompt_sha256": "6acda67c8c9af25d5bf52db7c77857920cd715598d2741843f62f8f3ae16808d"
 },
 "4_pass_lines": {
  "static": {
   "required_fields": "全欄そろい型が合うこと",
   "duplicate_ratio": 0.75,
   "review_keywords": [
    "保存則",
    "在庫",
    "所持金",
    "性能",
    "予算",
    "売上",
    "faucet",
    "sink"
   ]
  },
  "dynamic_not_measured_today": {
   "conservation_residual": 0,
   "usage_reduction": 0.5,
   "state_delta": "非零",
   "accept_pass_rows": "減らない"
  }
 },
 "5_adoption_order": [
  "食事",
  "観察/注意",
  "知らせる/対応する"
 ],
 "6_version_policy": {
  "synonym_table_version": "undefined-synonyms-v2",
  "granularity": "ラン単位(版を上げて次ランから有効・決定 F (a))",
  "mapping_table_required": true
 }
}
```

## 6. 空欄

- 動的検査 ①③④ の値(affordance の実装待ち)。② の合格線 −50% も動的。
