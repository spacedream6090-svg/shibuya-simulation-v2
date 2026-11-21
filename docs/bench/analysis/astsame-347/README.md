# 文だけの直しの commit の確かめ(第347〜)

[返事その 8](../../../design/prompt-2026-11-16-reply8.md) §1-12 の 2 の記録の置き場。src を変える commit のうち、byte-check を回さないもの(docstring と注だけの直し)は、ここに AST の確かめの記録を 1 本ずつ残す。

## 道具

```
python tools/bytecheck/astsame.py --base <基準の commit> [--head <比べる側の commit>] --out docs/bench/analysis/astsame-347/<名前>.json
```

- 変わった `.py` を 1 本ずつ、docstring と注(コメント)を除いた AST で比べて、3 つに分ける。
  - `same`: docstring と注のほかは同じ。ランの値は変わらない。
  - `strings`: 構造は同じで、値の文字列(docstring でない文字列の定数)だけが違う。記録に「値の文字列が変わった」と書く。
  - `structure`: 構造が違う。文だけの直しではないので、byte-check を回す。
- 終了コードは 0=全部 `same`・1=`strings` がある・2=`structure` がある。
- 文字列の中身は記録に出さない(行の番号と長さだけ)。
- 試験は `tests/tools/test_astsame.py`。確かめないことは道具の docstring にある(`.py` でないファイル・`__doc__` を値として読む作り)。

## 記録

| commit | 何の直し | 変わった `.py` | 結果 | 記録 |
|---|---|---:|---|---|
| `c6c8799`(第346) | 段 2 の突き合わせの直し(docstring と注が主) | 10 | `same` 7・`strings` 3(下) | [c6c8799.json](c6c8799.json) |
| 第347 の `world/laws/rail_events.py` | docstring の「版上げ 3 回目で読む」を「鉄道の秒の段(WD-34・未決)まで結線しない」に(11-16 §1-3 の 4) | 1 | `same` 1 | [rail_events_docstring.json](rail_events_docstring.json) |

### `c6c8799` の `strings` 3 本(第346 の受け入れの確かめで「前と後の byte-check の組が無い」とされた commit)

| ファイル(当時の道) | 変わった文字列 | 何の文か |
|---|---:|---|
| `src/shibuya/cli.py` | 1 | 引数の説明(`--help` の文)。ランの値には入らない |
| `src/shibuya/engine/calendar.py` | 1 | 祝日の CSV が無いときの警告の文 |
| `src/shibuya/engine/processes/civic.py` | 2 | 過程の要約の文(`summary()` が返す 1 文の 2 つの部分) |

値の文字列が変わっていたので、前と後の byte-check を後から回した(下)。

### `c6c8799` の前と後の byte-check(第347 に後から回した)

- 回し方: `c6c8799` の作業木(linked の git 作業木・data はつなぎ)で、その commit の道具を使い、`python tools/bytecheck/cli.py run --base c6c8799^ --work <作業場> --out-dir <置き場> --set all19 --jobs 6`。基準は 1 つ前の commit `b1bd58e`。
- 結果: **19 構成・25 欄すべて同じ(動いた 0・誤り 0・final が同じ 19)・終了コード 0**。当時の道具が比べる欄は 25(今は 37)。全体の壁時計は 436 秒(6 本並列。裏で数える役のランが回っていた=参考値)。
- 記録: [c6c8799-bytecheck/](c6c8799-bytecheck/)(基準の側・比べる側・比べの JSON 3 本)。
- 読み方: 変わった文字列 3 本は、ランの結果の 25 欄には入っていなかった。`--help` の文・祝日の CSV が無いときの警告・過程の要約の文は、どれも結果のハッシュの外にある。
