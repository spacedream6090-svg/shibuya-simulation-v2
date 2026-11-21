# 封印の語の表 2 つの比べ(第347・2026-11-16)

[返事その 8](../../../design/prompt-2026-11-16-reply8.md) §1-6 の 5(コードの区分の表の問い 5)の記録。語そのものは、この記録にも画面にも出していない。

## 何を比べたか

| 表 | 置き場 | 使い手(名前だけ) |
|---|---|---|
| `SEALED_TOKENS` | `tools/instruments/read_guard.py` | 計器の読みの守り(`ReadGuard`)・`tools/spatial/las_pointcloud_agg.py` |
| `HOLDOUT_TOKENS` | `src/shibuya/build/audit/w19_freeze.py` | 構築の封の検査(W19)・`build/pop/w21_sources.py` |

## 道具

`python tools/instruments/sealed_tokens_compare.py --json <置き場>`。出すのは個数と真偽だけ。終了コードは 0=集合として同じ・1=違う・2=誤り。試験は `tests/tools/test_sealed_tokens_compare.py`(出力と記録に語が 1 つも出ないことを、当たった数で確かめる)。

## 結果(HEAD=38b0142f の木)

| 欄 | 値 |
|---|---:|
| `SEALED_TOKENS` の個数 | 12 |
| `HOLDOUT_TOKENS` の個数 | 3 |
| 共通 | 1 |
| `SEALED_TOKENS` にだけある | 11 |
| `HOLDOUT_TOKENS` にだけある | 2 |
| 集合として同じか | いいえ |
| 片方にだけある語のうち、もう片方の語と字面が重なるもの | `SEALED_TOKENS` の側 2・`HOLDOUT_TOKENS` の側 2 |

数の記録は [compare.json](compare.json)。

## 扱い

2 つの表は同じではなかった。指示のとおり、**1 つにまとめずに止めた**(壁打ちで決める)。コードは変えていない。

- 字面が重なる組が 2 つある(片方の語がもう片方の語を含む)。同じ層を別の書き方で指している見込みだが、語を開いていないので確かめていない【見立て】。
- 個数の差(12 と 3)は、表の役の違いから来ている見込み【見立て】。`SEALED_TOKENS` は計器が開いてはいけない道の語、`HOLDOUT_TOKENS` は構築が読んではいけない封の層の語で、守る範囲が違う。
- 段 2-6 の AST の検査がどちらを正にするかは、まとめ方が決まるまで今のままにする。
