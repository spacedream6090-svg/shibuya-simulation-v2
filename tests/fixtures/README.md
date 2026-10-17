# tests/fixtures

試験が読む小さなファイルの置き場(git に入れる)。`data/` は gitignore のまま(CLAUDE.md §7)。

## calendar/syukujitsu.csv(国民の祝日)

| 項目 | 値 |
|---|---|
| 中身 | 内閣府「国民の祝日について」の CSV(昭和30年(1955年)〜令和9年(2027年)の祝日と休日) |
| 出典の頁 | https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html |
| 出典の CSV | https://www8.cao.go.jp/chosei/shukujitsu/syukujitsu.csv |
| 利用規約 | 内閣府ホームページ利用規約 https://www.cao.go.jp/notice/rule.html → 権利表記の無いものは公共データ利用規約(第1.0版)(出典を書けば複製・再配布できる) |
| 取得日 | 2026-10-03(`data/calendar/syukujitsu.csv` と同じもの) |
| 大きさ | 21,538 バイト |
| md5 | `733fabb6b488794a0cd3d94df4b1f24a` |
| 形 | cp932・CRLF |
| 加工 | **手を加えていない**(1 バイトも変えずに複製した。`.gitattributes` で `binary` にして改行の変換を止めている) |

使い方: `tests/conftest.py` が、試験の始まりに `data/calendar/syukujitsu.csv` が無ければこのファイルを
そこへ複製する(既にあれば触らない)。エンジンの既定の道筋 `data/calendar/syukujitsu.csv` は変えない。

更新: 内閣府が翌年の分を毎年 2 月に載せたら、手で取得して `data/calendar/` とこのファイルを差し替え、
md5 と取得日を本表に書き直して 1 commit にする(ライセンス台帳の行も足す)。

出典: 内閣府「国民の祝日について」(https://www8.cao.go.jp/chosei/shukujitsu/gaiyou.html)

## manifest_example.yaml

manifest の読み書きの試験が使う例(合成・出典なし)。
