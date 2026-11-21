# byte-check を 20 構成にした確かめ(第348・2026-11-21)

[返事その 9](../../../design/prompt-2026-11-20-reply9.md) §1 の 30「byte-check の構成に、話す時計が拍で数える構成を足して 20 構成にしてください」の記録。

## したこと

- `tools/bytecheck/configs.py` に 20 本目の構成 `v3_speech_talk_mora` を足した。引数は `w6_v3_default` と同じで、ランの前に環境変数 `SHIBUYA_SPEECH_PORT=on`・`SHIBUYA_TALK_CLOCK=mora` を置く(話す時計が拍で数える=`mora_count` を通る)。第 347 の段 6 の M1 で、親が手で足して前後で同じことを確かめた構成と同じ(記録は [split6-347/bytecheck_M1_mora](../split6-347/bytecheck_M1_mora/))。
- 既定の組を `all20` にした。前の 19 構成は、組 `all19` として残した(古い記録の再現用)。
- 構成ごとの環境変数は、1 構成を回す口(`one`)が、エンジンを読む前に自分のプロセスに置く。行には、ランが見た切替口の値を `switch_env` として残す(比べない・記録だけ)。

## 確かめ(親が回した・作者の機械)

`python tools/bytecheck/cli.py run --work <置き場> --out-dir docs/bench/analysis/bytecheck20-348/bytecheck --jobs 6`(基準=`c17dab5`=この commit の 2 つ前。間の 1 つは `ci.yml` だけの commit。比べる側=作業木の src。src は変えていないので、両側は同じになるはず)。全体で 433 秒。

| 確かめ | 結果 |
|---|---|
| 20 構成が両側で回るか | 回った(誤り 0) |
| 足した構成の値 | final `fc2246613b0e5695`・呼数 60,939。第 347 の M1 の記録と同じ |
| 既定の構成 `w6_v3_default` の値 | final `c8d68704b7b0760d`・呼数 60,939(前と同じ) |
| 20 構成・37 欄 | すべて同じ(終了コード 0) |

記録は [bytecheck/](bytecheck/) の 3 本(基準の側・比べる側・比べ)。

## 確かめていないこと

- 足した構成で、話す時計が実際に拍で数えた回数は数えていない(final は既定の構成と違い、呼数は同じ 60,939)。
- CI では byte-check は回らない(data が要る)。道具の試験(`tests/tools/test_bytecheck.py`)だけが回る。
