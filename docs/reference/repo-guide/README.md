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

## 古くなったら

段 3 は機械で作り直します。CI の ci-0 で、カードが src・tests・tools より古くないかを検査します。段 1・段 2 は人の読みで書いたので、版上げのたびに差を確かめます。文書の末尾に、読んだときの commit と読まなかったファイルを書いてあります。
