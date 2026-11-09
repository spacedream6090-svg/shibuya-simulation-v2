# リポの案内(今のコードの記述)の索引

[返事その 6](../../design/prompt-2026-11-05-reply6.md) §3-1 の把握の資料です。今のコードが何をしているかを書きます。あるべき姿は [仕様書](../../design/spec/README.md) にあり、本書には混ぜません。正はコードです。

**ユーザーが読む所**は、段 1 と「言えること・言えないこと」と食い違いの一覧です。全部を読める形で置いてあります。

| 段 | 文書 | 中身 | 作り方 |
|---|---|---|---|
| 段 1 | [day-flow.md](day-flow.md) | シミュレーションの 1 日の流れ(系の順・どのファイルが動くか・既定と腕) | 文書役がコードを読んで書いた |
| 1 枚 | [can-say.md](can-say.md) | 今の中身で言えること・言えないこと | 段 1・段 2 から |
| 段 2 | [catalog/a-body-and-town.md](catalog/a-body-and-town.md) | 機能のカタログ A: 体と街(鉄道・在圏・歩行・席と列・天気・世界過程・規則の表ほか) | 文書役がコードを読んで書いた |
| 段 2 | [catalog/b-people.md](catalog/b-people.md) | 機能のカタログ B: 人の中身(購入・食事・会話・記憶・関係・カレンダー・連絡・店の仕事ほか) | 同上 |
| 段 2 | [catalog/c-foundation.md](catalog/c-foundation.md) | 機能のカタログ C: 基盤(経済と台帳・権利・計器・実験と分岐・テープ・保存と再開・艦隊・判断の口・知覚・起床ほか) | 同上 |
| 段 3 | [cards/README.md](cards/README.md) | ファイルのカード(src・tests・tools の全ファイルの説明・公開の関数・import と呼び手・台帳・書きの許可・環境変数・決定の ID) | `python tools/repo_guide/build.py` で機械で作る |
| 索引 | [cards/docs.md](cards/docs.md)・[cards/data.md](cards/data.md) | docs の索引と data のディレクトリの一覧 | 同上。data は名前と大きさだけ |
| 突き合わせ | [段 2 の突き合わせ](../stage2-crosscheck-2026-11-05.md) | 段 1・段 2 と 1 枚をコードと照らした読み手 4 本の結果(食い違い 46 件と書き漏れ) | 11-09 に、各文書の末尾の「11-09 の直し」の表のとおり直した |

## 古くなったら

段 3 は機械で作ります(`python tools/repo_guide/build.py`)。src・tests・tools の .py を変えた commit ごとに、CI の ci-0 と pre-commit が、カードが src・tests・tools より古くないかを検査します(`--check`。pre-commit はその .py を変えた commit だけ、CI の ci-0 は push と PR のたびに毎回回す)。返事その 6 §3-1 の「版上げのたびに作り直す」は、11-09 §1-4 で親案のこの形(毎 commit の検査)を採りました。段 1・段 2 は人の読みで書いたので、版上げのたびに差を確かめます。文書の末尾に、読んだときの commit と読まなかったファイルを書いてあります。

## CI と決定論

**CI が緑でも決定論は確かめていません。** byte-check(同じ設定で結果の 1 バイトまで同じかを、構成ごとに比べる受入)・golden(状態のハッシュの固定の値)・性能の門・data の要る試験は CI の外で、作者の機械で回します(`.github/workflows/ci.yml` の冒頭の注)。CI の Ubuntu には data が無く、data の要る試験は印 `requires_data` で飛びます。golden は登録した 1 つの環境(`tests/golden_env.py`)とだけ値を比べ、ほかの環境では同じ設定 2 回の一致と警告だけです。byte-check の道具は [tools/bytecheck/](../../../tools/bytecheck/) に置き、版上げの手順の 1 行として呼びます(第346・CI では回せない)。中身は[カタログ C](catalog/c-foundation.md) の C16 と C18 です。
