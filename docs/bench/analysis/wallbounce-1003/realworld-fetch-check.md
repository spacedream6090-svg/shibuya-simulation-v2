# 現実データの日次取得(v1 rw_fetch)の確認と v2 への写し

- 日付: 2026-10-03(作業は 17:30〜17:40 JST ごろ)
- 実行役: Opus 5.5(親の検収待ち)
- 根拠: `docs/design/v2-wallbounce-decisions-2026-10-03.md` §10-1
- パスの書き方: `<V1>` = v1 リポ、`<V2>` = v2 リポ、`<PY>` = タスクが使っている Python 3.12 の実行ファイル、`<SCRATCH>` = 親セッションのスクラッチ。ユーザー名を含む実パスは書かない。

## 0. 結論

**一部動いている。** v1 のタスク `\shibuya-rw-fetch-daily` は毎日 12:00 に動いていて、10-03 12:00 の実行も成功(結果コード 0)。ただし中身は次のとおり。

| ソース | 状態 | いつから |
|---|---|---|
| アメダス 44132 10 分値 | **毎日半日分しか残っていない**(00:00〜11:50 の 4 ブロック/8)。午後は保持期限(約 9〜10 日)を過ぎて取れなくなっている | **08-08 から**(10-03 まで 56 日)。完全な日は 07-29〜08-07 と 09-22 だけ |
| 防災情報 XML 長期フィード | 動いている(1 日 1 回・4 フィード)。長期フィードは約 7 日分を載せているので、1 日 1 回でも抜けは無い | 08-07 から継続。09-22 だけ実行なし(PC が止まっていた) |
| WBGT(実況の月次・予測) | 動いている | 08-07 から継続。09-22 だけ実行なし(予測 1 日分は後から取れない) |
| ODPT 運行情報・JR 在線 | **止まっている(一度も定期実行されていない)**。日次タスクの既定ソースに入っておらず、08-07 に手で 1 回取っただけ | 08-07 以降なし |

アメダスの半日の原因(コードの欠陥): タスクは昼 12:00 に「今日」を取るので、その時点では午前の 4 ブロックしか無い。`--backfill` は「ファイルがあるか」で欠けを判定する(`amedas.missing_days`)ので、半日のファイルがある前日は取り直さない。台帳のレポートは毎日 `PARTIAL` と `URGENT` を出していたが、誰も見ていなかった。

この作業で、v2 の写しを使って 09-23〜10-02 を後追い取得し、**09-25〜10-02 の 8 日分を丸 1 日分(8/8 ブロック)回復した**。09-24 は 06:00 以降を回復(v1 の午前と合わせれば 1 日分そろう)。09-23 は 15:00 ブロックだけ取れた(12・18・21 は 404)。

## 1. 状態の確認(読むだけ)

### 1-1. v1 の台帳 `<V1>/data/realworld/_ledger.jsonl`(440 行)

| ソース | 行 | 成功 | 失敗 | 最初の行(UTC) | 最後の成功(UTC) | 直近の失敗 |
|---|---|---|---|---|---|---|
| amedas | 68 | 68 | 0 | 2026-08-07T13:00 | 2026-10-03T03:00:11Z | なし(ただし 56 行が 4/8 ブロックの `complete: false`) |
| jma_xml | 228 | 228 | 0 | 2026-08-07T13:01 | 2026-10-03T03:00:17Z | なし |
| wbgt | 114 | 114 | 0 | 2026-08-07T13:01 | 2026-10-03T03:00:12Z | なし |
| odpt_rt | 6 | 6 | 0 | 2026-08-07T12:59 | 2026-08-07T12:59:29Z | なし(以後の行なし) |
| shibuya_jinryu | 6 | 5 | 1 | 2026-08-07T12:59 | 2026-08-07T13:00:07Z | taizai_attribute が HTTP 202(08-07) |
| transport_census | 13 | 13 | 0 | 2026-08-09T15:29 | 2026-08-09T15:31:59Z | なし(単発の静的ソース) |
| odpt_passenger_survey | 5 | 5 | 0 | 2026-08-09T15:32 | 2026-08-09T15:45:51Z | なし(単発の静的ソース) |

アメダスの行の内訳(ブロック数, 件数): (4, 72) が 56 行、(8, 144) が 7 行、(8, 132〜137) が 4 行、(5, 90) が 1 行。実行が無かった日は 08-07〜10-03 のうち 09-22 だけ。

### 1-2. タスクスケジューラ(`schtasks /query /fo LIST /v`)

| 項目 | 値 |
|---|---|
| タスク名 | `\shibuya-rw-fetch-daily` |
| 状態 | Ready・Enabled |
| 最後の実行 | 2026-10-03 12:00:02 |
| 最後の結果 | 0 |
| 次回の実行 | 2026-10-04 12:00:00 |
| スケジュール | 毎日 12:00(開始日 2026-08-07)・繰り返しなし |
| 実行ユーザー | 現在のユーザー・Interactive only |
| 設定 | 電池駆動時は開始しない・30 分で停止・多重起動は無視・**StartWhenAvailable=true**(時刻に止まっていたら後で実行) |
| 実行コマンド | `powershell.exe -NoProfile -WindowStyle Hidden -Command "Set-Location '<V1>'; & '<PY>' scripts/rw_fetch_daily.py --backfill *>> data\realworld\_scheduler.log"` |
| コメント | shibuya-simulation RW-U1: 現実データ日次取得(アメダス保持10日対策・2026-08-07ユーザー承認) |

関連する別のタスク `\shibuya-simulation-daily-backup`(v1 の日次バックアップ)もあるが、取得とは別物なので触れない。

### 1-3. `_scheduler.log` の末尾

ファイルは UTF-16 LE(PowerShell の `*>>` が書く形)で、中の日本語は文字化けしている(UTF-8 の出力を cp932 で受けたもの)。数字の部分は読める。10-03 12:00 の実行の要約:

```
[amedas] 完了 ok=1/1 records=72 missing=0
[wbgt] 完了 ok=2/2 records=73 missing=13
[jma_xml] 完了 ok=4/4 records=15903 missing=0
(台帳レポート 全 440 行)
[amedas] URGENT 10 日: 2026-09-23 .. 2026-10-02 / LOST 19 日: 2026-09-03 .. 2026-09-21 / PARTIAL 29 日
[wbgt]   URGENT 1 日: 2026-09-22
[jma_xml] LOST 1 日: 2026-09-22
合計: URGENT 11 日 / LOST 20 日
[done] 台帳へ 7 行追記(成功 7)。HTTP要求 14 本。
```

amedas は `ok=1/1` で、`--backfill` が付いていても後追いの行が 1 本も出ていない(半日のファイルがあるため欠けと見なされない)。

### 1-4. v1 の `data/realworld/<source>/` の最新ファイル

| ソース | ファイル数 | 容量 | 最新ファイルの更新日時(JST) | 最新ファイル |
|---|---|---|---|---|
| amedas | 68 | 4.7M | 2026-10-03 12:00 | amedas/2026/10/2026-10-03/amedas_44132_20261003.json |
| jma_xml | 228 | 504M | 2026-10-03 12:00 | jma_xml/2026/10/2026-10-03/other_l_120017.json |
| wbgt | 120 | 729K | 2026-10-03 12:00 | wbgt/2026/10/2026-10-03/wbgt_forecast_44132_20261003.csv |
| odpt_rt | 3 | 64K | 2026-08-07 21:59 | odpt_rt/2026/08/2026-08-07/train_215923.json |
| shibuya_jinryu | 10 | 11M | 2026-08-07 22:00 | shibuya_jinryu/2026/08/2026-08-07/taizai_sex.csv |
| transport_census | 10 | 20M | 2026-08-10 00:31 | transport_census/station_od13_13.json |
| odpt_passenger_survey | 2 | 16K | 2026-08-10 00:32 | odpt_passenger_survey/shibuya.json |
| census_r3 | 4 | 364K | 2026-08-10 09:47 | census_r3/sim_vs_census.json |

防災 XML の 1 回分(10-03 12:00)のエントリの時刻幅は、4 フィードとも 09-26〜10-03 の約 7 日。1 日 1 回で前の回と重なるので抜けは無い。

## 2. v1 のスクリプトの読解

| ファイル | 役目 | ドメインと URL の形 | 環境変数 | 保存先 | 日次に入っているか |
|---|---|---|---|---|---|
| `rw_fetch_daily.py` | 薄い起動器(`rw_fetch.cli.main` を呼ぶ) | なし | なし | なし | 入口 |
| `cli.py` | オーケストレータ。`--offline`(要求 0 本)/ `--report` / `--verify` / `--backfill` / `--source` / `--date` / `--out-dir` / `--repeat` / `--interval` | なし | なし | `--out-dir`(既定 = `common.DEFAULT_ROOT`) | 既定ソース = amedas・wbgt・jma_xml |
| `common.py` | HTTP の唯一の出口・秘密のマスク・`_meta`・保存・日付パーティション | なし | なし | `DEFAULT_ROOT = REPO_ROOT/data/realworld`(`REPO_ROOT = このファイルの 2 つ上`)。日次は `<source>/<YYYY>/<MM>/<YYYY-MM-DD>/` | 共通 |
| `ledger.py` | 台帳 `_ledger.jsonl` への追記(既存行は書き換えない)・未取得日の検出(URGENT / LOST / PARTIAL) | なし | なし | `<root>/_ledger.jsonl` | 共通 |
| `amedas.py` | アメダス 44132 の 10 分値(1 日 = 3 時間ブロック × 8) | `https://www.jma.go.jp/bosai/amedas/data/point/44132/{YYYYMMDD}_{HH}.json` | なし | `amedas/Y/M/D/amedas_44132_{YYYYMMDD}.json` | 入っている |
| `wbgt.py` | WBGT 実況(月次累積・℃)と予測(3 時間値・0.1℃) | `https://www.wbgt.env.go.jp/est15WG/dl/wbgt_44132_{YYYYMM}.csv`、`https://www.wbgt.env.go.jp/prev15WG/dl/yohou_44132.csv` | なし | 実況 `wbgt/Y/M/wbgt_est_44132_{YYYYMM}.json`(+csv)、予測 `wbgt/Y/M/D/wbgt_forecast_...json`(+csv) | 入っている |
| `jma_xml.py` | 防災情報 XML の **長期フィードのみ**(regular_l・extra_l・eqvol_l・other_l)。東京関連と外れ値候補の印を付ける | `https://www.data.jma.go.jp/developer/xml/feed/{feed}_l.xml` | なし | `jma_xml/Y/M/D/{feed}_{HHMMSS}.json` | 入っている(1 日 1 回) |
| `odpt_rt.py` | ODPT 運行情報(メトロ=オープン枠、東急・京王=チャレンジ枠)と JR 在線(チャレンジ枠)。`dct:valid` 切れを除く | `https://api.odpt.org/api/v4/odpt:TrainInformation?odpt:operator=...`、`https://api-challenge.odpt.org/api/v4/odpt:{TrainInformation,Train}?...`(キーは `acl:consumerKey`) | `ODPT_API_KEY`・`ODPT_CHALLENGE_API_KEY`(プロセスに無ければ Windows のユーザー環境変数を読む) | `odpt_rt/Y/M/D/{traininformation,train}_{HHMMSS}.json` と `odpt_rt/README.md`(再配布注意) | **入っていない**(`--source odpt_rt` か `all` のときだけ) |
| `shibuya_jinryu.py` | 渋谷区オープンデータの人流 CSV(初回のみ) | `https://city-shibuya-data.opendata.arcgis.com/...` | なし | `shibuya_jinryu/...` | 入っていない。**v2 の許可ドメインに無いので今回は実行していない** |
| `transport_census.py` | 大都市交通センサス(単発) | `https://www.mlit.go.jp`・`https://www.e-stat.go.jp` | なし | `transport_census/...` | 入っていない(単発) |
| `odpt_passenger_survey.py` | ODPT 乗降者数(単発) | `api.odpt.org`・`api-challenge.odpt.org` | 同上 | `odpt_passenger_survey/...` | 入っていない(単発) |

- 依存ライブラリ: **標準ライブラリだけ**(urllib・json・csv・xml.etree・zipfile など。Windows でキーを読むときだけ winreg)。pip は不要。
- 高頻度フィード: **使っていない**。`jma_xml.FEEDS` は `_l` の 4 本だけ。docstring は「1 時間間隔」と書くが、実際のタスクは 1 日 1 回。フィードが約 7 日分を載せているので 1 日 1 回で抜けは無い(§1-4)。設計書 §10-1 の「1 時間間隔のまま」は v1 の docstring の記載で、v1 の実際の運用は 1 日 1 回だった。どちらにするかは §6 の問い 3。
- 台帳の書き方: 1 回の実行の行をまとめて末尾に追記する(`ledger.append`)。行の `path` は保存したファイルの絶対パス(gitignore の下なのでコミットには載らない)。
- キーの扱い: キーは URL に入るが、`common.register_secret` → `scrub` で、ログ・保存物・台帳の全経路が `***` に置き換わる。

## 3. 写し

### 3-1. 写したファイル(12 本)

`<V1>/scripts/rw_fetch/*.py`(11 本)と `<V1>/scripts/rw_fetch_daily.py` を `tools/realworld_fetch/` に写した。

```
tools/realworld_fetch/__init__.py
tools/realworld_fetch/amedas.py
tools/realworld_fetch/cli.py
tools/realworld_fetch/common.py
tools/realworld_fetch/jma_xml.py
tools/realworld_fetch/ledger.py
tools/realworld_fetch/odpt_passenger_survey.py
tools/realworld_fetch/odpt_rt.py
tools/realworld_fetch/rw_fetch_daily.py
tools/realworld_fetch/shibuya_jinryu.py
tools/realworld_fetch/transport_census.py
tools/realworld_fetch/wbgt.py
```

v1 の元ファイルは全部 LF(CR なし)。写しも LF。モジュール 11 本は v1 と **バイト単位で同じ**(`diff -q` で差なし)。

### 3-2. 変えた行(入口の 2 行だけ)

保存先のルートはすでにリポ相対(`common.py` の `REPO_ROOT = Path(__file__).resolve().parents[2]`)。`tools/realworld_fetch/common.py` の 2 つ上は v2 のリポなので、**既定の保存先は何も変えずに v2 の `data/realworld/` になる**(`--offline` の表示で確認)。別の場所にしたいときは既存の `--out-dir` で変えられる。変えたのは、パッケージ名が `rw_fetch` から `realworld_fetch` に、入口の置き場がパッケージの中に変わったことに合わせた 2 行だけ:

```diff
--- <V1>/scripts/rw_fetch_daily.py
+++ tools/realworld_fetch/rw_fetch_daily.py
@@ -15,3 +15,3 @@
-sys.path.insert(0, str(Path(__file__).resolve().parent))
+sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
@@ -17,1 +17,1 @@
-from rw_fetch.cli import main  # noqa: E402
+from realworld_fetch.cli import main  # noqa: E402
```

変えていないが気づいた点(挙動に関わらないので残した): `_meta.generated_by` の文字列が `scripts/rw_fetch/...` のまま、`--report` の案内文が `python scripts/rw_fetch_daily.py --backfill` のまま。直すかは親の判断(§6 の問い 5)。

### 3-3. 台帳の複写

- 複写元 `<V1>/data/realworld/_ledger.jsonl`: md5 `51d0d1087631c1c38f62562bc40f4c03`・440 行・CR なし。
- 複写先 `data/realworld/_ledger.jsonl`: 複写直後の md5 は同じ(`51d0d108...`)・440 行。
- v2 にはもともと 08-31 時点の古い写し(215 行・md5 `736deafe937545be938dc2ef590f731e`)があった。これは v1 の台帳の先頭 215 行と完全に一致する(前方一致を確認)ので、上書きで失われる行は無い。
- `git check-ignore -v data/realworld/_ledger.jsonl` → `.gitignore:2:data/	data/realworld/_ledger.jsonl`(gitignore の下)。
- 動作確認の後の v2 台帳は 463 行(440 + 23)。

注意: v2 の `data/realworld/` には 08-31 までの写し(amedas 35 日分・jma_xml 100 本・wbgt 52 本ほか)が既にある。09-01〜10-03 の v1 のデータ実体(amedas の午前分・jma_xml・wbgt)は v1 側にしか無い。v2 に寄せるかは §6 の問い 4。

### 3-4. v1 のテストを写しに当てた結果(参考・スクラッチで実行)

v1 の `tests/test_rw_fetch.py` を、import 先だけ `realworld_fetch` に置き換えてスクラッチで実行した(リポには置いていない)。**76 合格・4 失敗。** 失敗 4 本はどれも v1 のリポの形を前提にした検査で、写しの欠陥ではない:

1. `test_env_var_names_match_existing_scripts`: v1 の `scripts/fetch_odpt.py` を読む(v2 には無い)。
2. `test_gitignore_excludes_realworld_data`: `.gitignore` に `data/realworld/` の文字列を探す(v2 は `data/` ごと除外しているので実質は満たしている)。
3. `test_entrypoint_script_exists_and_is_thin`: 入口に `rw_fetch.cli` の文字列を探す(写しは `realworld_fetch.cli`)。
4. `test_src_never_references_rw_fetch_or_realworld`: **v2 の `src/` に `realworld` を含むファイルが 18 本ある。** 下の §4-3 に書く重要な点につながる。

## 4. 動作の確認(各ソース 1 回・v2 の写しで)

### 4-1. 実行したコマンドと結果

作業ディレクトリは `<V2>`。どれも終了コード 0。

| ソース | コマンド | 所要 | HTTP 要求 | 結果 |
|---|---|---|---|---|
| (ドライラン) | `python tools/realworld_fetch/rw_fetch_daily.py --offline` | 1 秒未満 | 0 | 保存先が `<V2>\data\realworld` と表示 |
| amedas | `python tools/realworld_fetch/rw_fetch_daily.py --source amedas --backfill` | 88 秒 | 88 | ok 11/11・1,354 件・欠測 0。今日(6/8 ブロック)+ 09-23〜10-02 の後追い 10 日 |
| wbgt | `python tools/realworld_fetch/rw_fetch_daily.py --source wbgt` | 1 秒 | 2 | ok 2/2・73 件・欠測 7(10 月の未到来の時刻) |
| jma_xml | `python tools/realworld_fetch/rw_fetch_daily.py --source jma_xml` | 5 秒 | 4 | ok 4/4・15,768 件 |
| odpt_rt | `python tools/realworld_fetch/rw_fetch_daily.py --source odpt_rt` | 7 秒 | 6 | ok 6/6・74 件。キーは 2 つともプロセスとユーザーの環境変数にあった(値は見ていない) |

amedas の後追いが動いたのは、v2 には 09-01 以降のファイルが無かったため(`missing_days` がファイルの有無で判定するので、10 日分すべてが欠けと見なされた)。

### 4-2. 出力されたファイル(v2 の `data/realworld/` の下)

| ファイル | サイズ(バイト) | ブロック |
|---|---|---|
| amedas/2026/09/2026-09-23/amedas_44132_20260923.json | 17,373 | 1/8(15 時のみ。他は 404) |
| amedas/2026/09/2026-09-24/amedas_44132_20260924.json | 89,494 | 6/8(00・03 は 404) |
| amedas/2026/09/2026-09-25/amedas_44132_20260925.json | 117,483 | 8/8 |
| amedas/2026/09/2026-09-26/amedas_44132_20260926.json | 108,494 | 8/8(132 件) |
| amedas/2026/09/2026-09-27/amedas_44132_20260927.json | 117,886 | 8/8 |
| amedas/2026/09/2026-09-28/amedas_44132_20260928.json | 117,701 | 8/8 |
| amedas/2026/09/2026-09-29/amedas_44132_20260929.json | 117,959 | 8/8 |
| amedas/2026/09/2026-09-30/amedas_44132_20260930.json | 105,978 | 8/8(129 件) |
| amedas/2026/10/2026-10-01/amedas_44132_20261001.json | 117,669 | 8/8 |
| amedas/2026/10/2026-10-02/amedas_44132_20261002.json | 117,392 | 8/8 |
| amedas/2026/10/2026-10-03/amedas_44132_20261003.json | 87,191 | 6/8(18・21 はまだ無い) |
| wbgt/2026/10/wbgt_est_44132_202610.json(+ .csv 1,473) | 9,572 | |
| wbgt/2026/10/2026-10-03/wbgt_forecast_44132_20261003.json(+ .csv 329) | 4,008 | |
| jma_xml/2026/10/2026-10-03/regular_l_173754.json | 4,299,172 | |
| jma_xml/2026/10/2026-10-03/extra_l_173756.json | 2,961,662 | |
| jma_xml/2026/10/2026-10-03/eqvol_l_173757.json | 348,288 | |
| jma_xml/2026/10/2026-10-03/other_l_173758.json | 220,584 | |
| odpt_rt/2026/10/2026-10-03/traininformation_173759.json | 6,214 | メトロ 3・京王 1・東急 2 |
| odpt_rt/2026/10/2026-10-03/train_173759.json | 59,508 | 山手 34・埼京 21・湘南新宿 13(遅延の最大 180 秒・平均 18.5 秒) |

台帳には 23 行が足された(amedas 11・wbgt 2・jma_xml 4・odpt_rt 6)。

秘密の検査: odpt_rt の保存物と台帳に `consumerKey=` の後ろが `***` 以外のものは無い。環境変数の 2 つのキーの値がどのファイルにも含まれないことを Python で照合した(0 件)。`python tools/scan_secrets.py tools/realworld_fetch/*.py` は CLEAN。写しのファイルにユーザー名・絶対パス・メールは無い。

観察: アメダスの保持は実測で約 9 日半(10-03 17:36 の時点で 09-24 の 06 時ブロックは取れ、00・03 時は 404)。09-23 は 15 時だけ 200 で 12・18・21 時は 404 だった(理由は不明)。

### 4-3. 重要: v2 のビルドが `data/realworld/amedas` を全部読む

v2 の `src/shibuya/build/field/w13_weather.py` は `data/realworld/amedas` の下の `amedas_*.json` を **日付の範囲で絞らずに全部** 読み(`root.rglob("amedas_*.json")`)、天気の資産(候補日・層)を作る。`src/shibuya/build/audit/w19_freeze.py` も同じ全ファイルを凍結の入力表に入れる。

したがって、日次取得の保存先を v2 の `data/realworld/` にすると、**次に W13 を作り直したときに 09-23 以降の実データが天気の資産に入り、資産のハッシュが変わる**。設計書 §10-1 の 6「シミュレーション本体はこのデータを読まない(検証専用)」と食い違う。今回の動作確認で、すでに 11 本の amedas ファイル(上の表)がこの場所に入っている。W13 の作り直しは自動では走らないので、今すぐ壊れるものは無い。

また、`w19_freeze.HOLDOUT_LAYERS` は今 kddi_la・shibuya_jinryu・boundary_counts だけで、odpt_rt と jma_xml は holdout の層として封印されていない。

対処の案(親の判断・§6 の問い 1):
- 案 A: 日次取得の保存先を別の根(例 `data/realworld_live/`)にする。コードは変えずに、タスクのコマンドに `--out-dir data\realworld_live` を足すだけ。今回入れた v2 の新しいファイルと 23 行はそこへ移す。台帳の複写先もそこにする。
- 案 B: 保存先は `data/realworld/` のままにして、W13 と W19 が読む amedas を 07-28〜08-31 の日付の窓で絞る(src の変更が要る)。
- どちらでも、odpt_rt・jma_xml を W19 の holdout の層に足すかを決める。

## 5. 再開の手順(親が実行するコマンド)

順序: (0) 上の §4-3 の案を決める → (1) v1 のタスクを無効にする → (2) v2 のタスクを登録する → (3) 必要なら v1 の台帳の差分を足す。**v1 のタスクが 10-04 12:00 に動く前に付け替えれば、台帳が 2 つに分かれない。**

### 5-1. v1 のタスクを無効にする(付け替え)

```
schtasks /change /tn "\shibuya-rw-fetch-daily" /disable
```

元に戻すときは `/enable`。削除はしない。

### 5-2. v2 の日次タスク(v1 の設定をそのまま踏襲)

v1 のタスクの XML を書き出し、作業ディレクトリと入口のパス・名前・説明だけを書き換えたものを、スクラッチに用意した: `<SCRATCH>/v2-rw-fetch-daily.xml`(UTF-16)。v1 の設定(毎日 12:00・Interactive only・StartWhenAvailable・電池時は開始しない・30 分で停止・多重起動は無視)がそのまま残る。書き換えた `Arguments` は次のとおり:

```
-NoProfile -WindowStyle Hidden -Command "Set-Location '<V2>'; & '<PY>' tools/realworld_fetch/rw_fetch_daily.py --backfill *>> data\realworld\_scheduler.log"
```

登録:

```
schtasks /create /tn "\shibuya-v2-rw-fetch-daily" /xml "<SCRATCH>\v2-rw-fetch-daily.xml"
```

案 A を採るなら、登録の前に XML の `Arguments` に ` --out-dir data\realworld_live` を足し、ログの先も `data\realworld_live\_scheduler.log` にする。

XML を使わない形(StartWhenAvailable・電池の設定は付かないので、上の XML を勧める):

```
schtasks /create /tn "\shibuya-v2-rw-fetch-daily" /sc DAILY /st 12:00 /it /f /tr "powershell.exe -NoProfile -WindowStyle Hidden -Command \"Set-Location '<V2>'; & '<PY>' tools/realworld_fetch/rw_fetch_daily.py --backfill *>> data\realworld\_scheduler.log\""
```

実行ユーザーは、`schtasks /create` を実行した現在のユーザーになる(`/ru` は付けない)。

### 5-3. アメダスの半日の穴をふさぐ(親の判断・§6 の問い 2)

コードを変えない案: 毎日 00:30 に「前日」をアメダスだけ取り直すタスクを足す。`fetch_day` はファイルを上書きするので、前日の半日のファイルが 1 日分に置き換わり、台帳には `complete: true` の行が足される。

```
schtasks /create /tn "\shibuya-v2-rw-fetch-amedas-prevday" /sc DAILY /st 00:30 /it /f /tr "powershell.exe -NoProfile -WindowStyle Hidden -Command \"Set-Location '<V2>'; & '<PY>' tools/realworld_fetch/rw_fetch_daily.py --source amedas --date ((Get-Date).AddDays(-1).ToString('yyyy-MM-dd')) *>> data\realworld\_scheduler.log\""
```

PC が 00:30 に止まっていたときに後で走らせるには StartWhenAvailable が要るので、これも 5-2 の XML を写して時刻と引数を変えて登録する方がよい。

コードを変える案: `amedas.missing_days` が「ファイルがあっても 8/8 でない日」も欠けとして扱うようにする(挙動の変更になるので、親の承認が要る)。

### 5-4. ODPT の定期取得(v1 には設定が無かった)

v1 では一度も定期実行されていなかったので、踏襲する設定が無い。間隔は親とユーザーの判断(expedient の候補)。例として 10 分ごと:

```
schtasks /create /tn "\shibuya-v2-rw-fetch-odpt" /sc MINUTE /mo 10 /it /f /tr "powershell.exe -NoProfile -WindowStyle Hidden -Command \"Set-Location '<V2>'; & '<PY>' tools/realworld_fetch/rw_fetch_daily.py --source odpt_rt *>> data\realworld\_scheduler_odpt.log\""
```

見積り(10 分ごと): 1 回あたり HTTP 6 本・約 66KB・台帳 6 行 → 1 日あたり 864 本・約 9.5MB・台帳 864 行。台帳の行が今の約 2 倍の速さで毎日増えるので、台帳を分けるかも決める。`dct:valid` が 5 分なので、5 分ごとにすると 1 日 1,728 本・約 19MB。

### 5-5. 付け替えが 10-04 12:00 より後になった場合

v1 の台帳の 441 行目以降を v2 の台帳の末尾へ足す(v2 側の 23 行の後ろに付くので、時刻の順は崩れるが追記専用なので読む側は困らない):

```
tail -n +441 <V1>/data/realworld/_ledger.jsonl >> <V2>/data/realworld/_ledger.jsonl
```

## 6. 親に問うこと

1. **保存先と W13 の食い違い**(§4-3): 案 A(`data/realworld_live/` に分ける・コード変更なし)か案 B(W13・W19 を日付の窓で絞る)か。今回入れた v2 の新しいファイル(amedas 11・wbgt 4・jma_xml 4・odpt_rt 2)と台帳 23 行をどうするか。odpt_rt と jma_xml を holdout の層に足すか。
2. **アメダスの半日**(§5-3): 00:30 の前日取り直しタスクを足すか、コードを直すか。今のままだと v2 に付け替えても毎日半日しか残らない。
3. **防災 XML の間隔**: v1 の実際の運用(1 日 1 回)のままでよいか、設計書の文言どおり 1 時間ごとにするか。1 時間ごとにすると 1 日あたり約 190MB(今は約 8MB)で、長期フィードの約 7 日の幅に対しては情報は増えない。
4. **v1 のデータ実体を v2 へ寄せるか**: 09-01〜10-03 の amedas(午前分)・jma_xml(約 250MB)・wbgt は v1 にしか無い。09-23 は v1 の午前 4 ブロック + v2 の 15 時 1 ブロック、09-24 は v1 の午前 + v2 の 06 時以降で 1 日分になる。ファイル名が同じなので、寄せるならマージの方法を決める。
5. **文字列の残り**: `_meta.generated_by` と `--report` の案内文が v1 のパスのまま。直すか。
6. **WBGT 9 月の実況**: v1 の最後の 9 月分は 09-30 12:00 の取得で、09-30 の午後が入っていない。`--source wbgt --date 2026-09-30` で 9 月の月次ファイルを取り直せるが、同時に予測も取って 09-30 の日付の下に保存される(日付の付け方がずれる)。取り直すか。
7. **shibuya_jinryu**: `city-shibuya-data.opendata.arcgis.com` は v2 の許可ドメインの一覧に無いので実行していない。日次の対象ではないので今のままでよいか。

## 7. ライセンス台帳に足す行の文案

`docs/data-license-ledger.md` の表の形(ディレクトリ・内容・出典・ライセンス・商用・備考)に合わせた。ライセンスの文言は v1 の `common.ATTRIBUTION`(v1 の答申 `rw-data-acquisition.md` 由来)から写したもので、**この作業では原典を読み直していない**(親の一次確認が要る)。

| ディレクトリ | 内容 | 出典 | ライセンス | 商用 | 備考 |
|---|---|---|---|---|---|
| data/realworld/amedas(v2 取得開始 2026-10-03・v1 は 2026-07-28 分から) | アメダス東京 44132(北の丸公園)の 10 分値・日次ファイル | 気象庁 アメダス(https://www.jma.go.jp/bosai/amedas/) | 公共データ利用規約(第1.0版)/ PDL1.0(https://www.jma.go.jp/jma/kishou/info/coment.html) | ○ | 出典「気象庁ホームページ(アメダス)。加工して作成」。再配布可。保持約 10 日。検証専用(シミュ本体は読まない) |
| data/realworld/jma_xml(同上・v1 は 2026-08-07 から) | 防災情報 XML 長期フィード 4 本(regular_l・extra_l・eqvol_l・other_l)のエントリ・東京関連と外れ値候補の印 | 気象庁 防災情報 XML(https://xml.kishou.go.jp/xmlpull.html、取得元 https://www.data.jma.go.jp/developer/xml/feed/) | 公共データ利用規約(第1.0版)/ PDL1.0 | ○ | 出典「気象庁ホームページ(防災情報XML)。加工して作成」。再配布可。高頻度フィードは使わない(1 日 10GB 超で IP 遮断の注意) |
| data/realworld/wbgt(同上・v1 は 2026-08-07 から) | 暑さ指数 WBGT 地点 44132 の実況(月次累積・℃)と予測(3 時間値・0.1℃) | 環境省 熱中症予防情報サイト(https://www.wbgt.env.go.jp/) | 出典明記が必須(他媒体へ転記する場合は環境省である旨を明記)(https://www.wbgt.env.go.jp/data_service.php) | ○ | 出典「環境省熱中症予防情報サイト」。再配布可。提供は毎年 4/22〜10/21 |
| data/realworld/odpt_rt(同上・v1 は 2026-08-07 に 1 回) | ODPT 運行情報 TrainInformation(メトロ=オープン枠、東急・京王=チャレンジ枠)と JR 東日本の在線 Train(チャレンジ枠) | 公共交通オープンデータセンター(https://www.odpt.org/、API https://api.odpt.org/・https://api-challenge.odpt.org/) | オープン枠 = 公共交通オープンデータ基本ライセンス(出典表示義務・派生物にも継承)/ **チャレンジ枠 = チャレンジ参加者限定・再配布不可** | △(チャレンジ枠は×) | 出典「本データは公共交通オープンデータセンターのデータを利用して作成」+ 表示時はデータ生成時刻 dc:date を併記。**チャレンジ枠の生データは再配布しない**(論文・提出物には集計値・グラフのみ)。dct:valid 超過は使わない。キーは環境変数 `ODPT_API_KEY`・`ODPT_CHALLENGE_API_KEY` のみ。検証専用(holdout)で電車の運行の入力にしない |

## 8. 位置づけ(設計書 §10-1 の 6 の写し)

> 位置づけです。シミュレーション本体はこのデータを読みません。ODPTの運行情報は検証専用(holdout)とし、電車の運行の入力にはしません。遅延は「混雑→停車時間→遅延」の閉ループを作ったときに、シミュレーションの中から生まれるべきものだからです。防災XMLとODPTの運休から「外れ値の日」の印を作り、較正から外す材料にします。例外は、反実仮想で「実際にあった運休の日を再現して街の反応を見る」場合だけで、そのときは実験の条件として明記します。

この位置づけに対して、今の v2 では W13 が `data/realworld/amedas` を全部読む点(§4-3)が食い違う。

## 9. 親の判断と実施(第315・2026-10-03)

§6 の問いへの親の答えと、実行した内容。設計の決定項には触れない運用の判断で、保存先だけはユーザーの指示(`data/realworld/`)と違うので PENDING §1-1 K10 で確認を求める。

| 問い | 親の判断 | 理由 |
|---|---|---|
| 1 保存先と W13 の食い違い | **案 A(`data/realworld_live/` に分ける)をつなぎとして採用**。今回の動作確認で `data/realworld/` に入った 21 本(amedas 11・wbgt 4・jma_xml 4・odpt_rt 2)と台帳(v1 の 440 行+23 行)を `data/realworld_live/` へ移し、`data/realworld/_ledger.jsonl` は元の 215 行(v1 の先頭 215 行と同一)に戻した。`data/realworld/amedas` は 07-28〜08-31 の 35 本に戻った | 版上げ 1 回目(W10 ON)は世界資産の再構築を伴うので、W13 の入力が動く状態を残さない。コードを変えずに済み、後から戻せる。odpt_rt・jma_xml を W19 の holdout の層に足すかは、W13 の年間化(10a のアジェンダ K7)と一緒に決める |
| 2 アメダスの半日 | **00:30 に前日を取り直すタスクを足した**(コードは変えない=指示書「挙動を変えずに写す」) | `fetch_day` は上書きなので前日の半日が 1 日分に置き換わる |
| 3 防災 XML の間隔 | **1 日 1 回のまま**。指示書の「1 時間間隔のまま」は長期フィードの更新間隔(高頻度フィードを使わない)と読む | 長期フィードは約 7 日分を載せるので 1 日 1 回で抜けが無い。1 時間ごとにしても情報は増えず、1 日約 190 MB になる |
| 4 v1 の実体を寄せるか | 今は寄せない(v1 リポに残る) | 失われない。寄せ方は K10 の後 |
| 5 案内文の v1 のパス | 直さない | 挙動を変えない写し。表示だけ |
| 6 WBGT 9 月の欠け | 取り直さない(後から取れるなら 10/21 の提供終了の前に 1 回) | 午後 1 回分の欠け |
| 7 shibuya_jinryu | 実行しない | 封印の holdout・許可の一覧の外 |
| ODPT の間隔 | **10 分ごと**(expedient・宣言)。1 日 864 本・約 9.5 MB・台帳 864 行 | v1 に設定が無い。在線は粗いが運行情報の検証には足りる。台帳の増え方は 1 か月後に見直す |

**登録したタスク(親が `schtasks /create /xml` で実行・2026-10-03)**: `\shibuya-v2-rw-fetch-daily`(毎日 12:00・`--backfill --out-dir data\realworld_live`・次回 10-04 12:00)/ `\shibuya-v2-rw-fetch-amedas-prevday`(毎日 00:30・前日の amedas だけ・次回 10-04 00:30)/ `\shibuya-v2-rw-fetch-odpt`(10 分ごと・`--source odpt_rt`・次回 10-03 17:50)。v1 の `\shibuya-rw-fetch-daily` は `/disable`(削除はしない)。設定は v1 の XML を踏襲(Interactive only・StartWhenAvailable・電池時は開始しない・多重起動は無視。ODPT は 10 分で停止)。前日の取り直しのコマンドは PowerShell で `--offline` の空実行で引数の解釈を確かめた(8 要求・前日の日付)。
