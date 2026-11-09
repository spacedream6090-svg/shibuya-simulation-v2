# 版上げの履歴とタグ(戻し方つき)

> 2026-11-05・第345 に STATUS から移した(11-05 §1=STATUS を 1 画面の索引に戻す)。運用の規則は [回答 10-13b](../design/v2-answers-2026-10-13b.md) §0-6・§0-7(CLAUDE.md §4)。版上げのたびに本書へ 1 行足す。

| 回 | 何 | 取り込み | 安定版のタグ(直前の commit) | 戻し方 |
|---|---|---|---|---|
| 1 回目 | 10e 暦は実日・開始日 2026-07-13・天気・behavior-hash・テープ版 4(#87・#88・第329〜330) | 第330 | タグなし(§0-7 の前) | IMPLEMENTED #88 の commit を checkout |
| 2 回目 | 2-4 近接 distance・在席の印・経済 stage2・資産の活性化(#101・第334) | d35a9b6 | タグなし(§0-7 の前) | 直前の commit を checkout |
| 小 | 賃金を職業ごとの実データから(#115) | c87d5de | `stable-v2-before-wage-occupation`(cb38b0a) | `git checkout stable-v2-before-wage-occupation`(旧道 `--wage w17` は 672a7f9 で削除済み) |
| 小 | 第 18-1 表の置き換え=既定の食事時刻と初期の空腹(#117) | 2809c4a | `stable-v2-before-meal-default-w17`(276361e) | `git checkout stable-v2-before-meal-default-w17`(旧道 `--meal-default validation` は削除済み) |
| 3 回目 | 4-1 段 10 差し替え W16 → W21c=母集団 345,858 体(#118) | 2313e1b | `stable-v2-before-pop-w21`(8b1fb84) | checkout+`activate_pop43.py revert`(退避 `data/world/v2_pre_4-3`)。旧値だけなら `--world data/world/v2_pre_4-3` |
| 小 | 4-2 規則の表 19+1 行・給与の天引き・消費税の預かり金(#120) | e2b1f6f | `stable-v2-before-rules-42`(6f07eff) | checkout か `SHIBUYA_RULES_42=off`(次の版上げで消す) |
| 小 | 4-2b 規則の表の空欄 3 件(#122) | a04b46d | `stable-v2-before-rules-42b`(01649bb) | checkout か `SHIBUYA_RULES_42B=off`(次の版上げで消す) |
| 4 回目 | 第 5 期 段 1b 密度の推定=`--space nav1`+近傍が既定(#126) | b02c257 | `stable-v2-before-space-1`(6e46dbb) | `git checkout stable-v2-before-space-1`(既定が legacy に戻る・資産は残してよい)か `--space legacy`(次の版上げで消す) |
| 小 | 率の形の規則 9 件を外す=出勤率・催しの 200 人・E8・乗車の受け入れ確率・ポイ捨て・売れ残りの廃棄・宅配・倒れる率・Calvo(#132・11-01 §2) | ce52662 | `stable-v2-before-rate-rules`(6a943af) | `git checkout stable-v2-before-rate-rules` か `--rate-rules legacy`(環境変数 `SHIBUYA_RATE_RULES=legacy`・次の版上げで消す) |
| 小 | まだ動いていた「無い」の過程 5 件(ごみ収集・清掃・道路工事・救急の出動・電気と水)を既定で止める(#136・11-02r #7)。既定の final は不変・変わるのは過程の計数と ActualLog。性能 5,000 体 50.0 s/34.7 ms/511 MB(同じ日の土台 49.6〜51.2 s=揺れの範囲) | 4566492 | `stable-v2-before-absent-5`(1c137c6) | `git checkout stable-v2-before-absent-5` か `--absent-processes legacy`(環境変数 `SHIBUYA_ABSENT_PROCESSES=legacy`・次の版上げで消す) |
| 小 | 棚卸し B の欠陥 4 件(M10・M11・M28・M16)の直し(#138・11-03 §3)。既定の final 73aa01d9 → c8d68704・呼数 61,066 → 60,939。性能 5,000 体 60.5/61.8 s・42〜43 ms・最大 520〜527 MB(同じ巡の土台 62.8/61.8 s=揺れの範囲) | 8165b3d | `stable-v2-before-defect-fixes-1103`(3b375dc) | `git checkout stable-v2-before-defect-fixes-1103` か `--defect-fixes-1103 legacy`(環境変数 `SHIBUYA_DEFECT_FIXES_1103=legacy`・次の版上げで消す) |
| 実証の線 | 39 万体 × 1 日の実 LLM(C7 受入) | 8f78065 | `v2-c7-day-4-accepted` | — |

## 版上げと整理の段の手順(byte-check)

〔第346・2026-11-09・[返事その 7](../design/prompt-2026-11-09-reply7.md) §2 の 4〕版上げと整理の段では、次の 1 行で byte-check を回す。基準は既定で HEAD、比べる側は既定で作業木の src。19 構成すべて 25 欄が同じなら終了コード 0、動いた欄があれば 1、誤りは 2。

```
python tools/bytecheck/cli.py run --work C:\bc<N> --out-dir <記録の置き場>/bytecheck --jobs 6
```

CI では回せない(data と約 7 分のランが要る)。**CI が緑でも決定論は確かめていない。** 使い方と確かめないことは [tools/bytecheck/README.md](../../tools/bytecheck/README.md)。
