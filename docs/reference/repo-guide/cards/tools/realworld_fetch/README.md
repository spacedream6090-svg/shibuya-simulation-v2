# tools/realworld_fetch

自動生成(手で編集しない): `python tools/repo_guide/build.py`

Python 15 本・その他 0 本(このディレクトリの直下)

## [__init__.py](../../../../../../tools/realworld_fetch/__init__.py)

RW-U1: 現実世界データの取得器群(オフライン取得 → 静的凍結)。

## [amedas.py](../../../../../../tools/realworld_fetch/amedas.py)

A1: 気象庁アメダス(bosai 配信 JSON)・地点 44132「東京」の 10 分値。

- 公開の関数とクラス
  - `block_url`(関数)
  - `build_document`(関数)
  - `count_missing`(関数): 欠測セルを数える。**埋めない・推定しない**(リスク R6)。
  - `day_path`(関数)
  - `fetch_day`(関数): 1日ぶん(8ブロック)を取得して保存する。戻り値 = (保存した文書 | None, 台帳行)。
  - `fetch_latest_time`(関数): 最新観測時刻(疎通確認用の最小リクエスト1本)。
  - `latest_time_url`(関数)
  - `merge_blocks`(関数): 複数ブロックのレコードを時刻でマージ(重複は後勝ちにせず先勝ち = 同値のはず)。
  - `missing_days`(関数): 保存済みファイルの実在から未取得日を出す(台帳が壊れていても効く二重の網)。
  - `parse_point_block`(関数): 3時間ブロック JSON → 時刻順のレコード列。**値は一切書き換えない。**
  - `plan_day`(関数): `--offline` 用の取得予定(説明, URL)。ネットワークには一切出ない。
  - `summarize_day`(関数): 日次まとめ。**値が1つも無い項目は None**(0 で埋めない)。
  - `within_retention`(関数): 後追い取得がまだ間に合うか(実測境界 10 日)。
- import している内部モジュール: `tools/realworld_fetch/common.py`・`tools/realworld_fetch/ledger.py`
- 呼び手: `tools/realworld_fetch/cli.py`

## [cli.py](../../../../../../tools/realworld_fetch/cli.py)

RW-U1 日次オーケストレータ: 1 コマンドで全ソースを取得し、台帳を1本にまとめる。

- 公開の関数とクラス
  - `build_parser`(関数)
  - `build_plan`(関数): 取得予定 (説明, URL)。**ネットワークには出ない**(キーも読まない)。
  - `ensure_root_readme`(関数)
  - `full_report`(関数): `--report` の全文(未取得日・odpt_rt の欠けた時間帯・ディスクの量)。ネット不使用。
  - `main`(関数)
  - `print_plan`(関数)
  - `run_sources`(関数): 要求されたソースを順に取得する。戻り値 = (台帳行, 失敗ソース数)。
  - `verify`(関数): 保存済み JSON(`.json` と `.json.gz`)の `_meta` スキーマを検証する。
- import している内部モジュール: `tools/realworld_fetch/amedas.py`・`tools/realworld_fetch/common.py`・`tools/realworld_fetch/jma_xml.py`・`tools/realworld_fetch/ledger.py`・`tools/realworld_fetch/logrotate.py`・`tools/realworld_fetch/odpt_rt.py`・`tools/realworld_fetch/odpt_static.py`・`tools/realworld_fetch/shibuya_jinryu.py`・`tools/realworld_fetch/wbgt.py`
- 呼び手: `tools/realworld_fetch/rw_fetch_daily.py`
- 読む試験: `tests/tools/test_realworld_fetch_logrotate.py`・`tests/tools/test_realworld_fetch_odpt.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`
- CLI の引数
  - `--backfill`: アメダスの未取得日(保持10日以内)を後追い取得する
  - `--check`: odpt_static: 保存済みの最新版と API の dct:issued を比べ、新しい版がある operator × 種類を一覧にする(保存しない)
  - `--date`: 対象日 YYYY-MM-DD(既定: 今日 JST)
  - `--force`: 既取得でも取り直す(渋谷区人流など低頻度ソース向け)。odpt_rt では種類ごとの間隔を無視して全部取る
  - `--interval`: ODPT リアルタイムの間隔秒(既定 90 = dct:valid 5分を尊重)
  - `--lookback`: --report の遡り日数
  - `--no-raw`: CSV 等の生ファイルを保存しない
  - `--offline`: ドライラン。取得予定を表示するだけで HTTP 要求を 1 本も出さない
  - `--operators`: odpt_static: operator を絞る(カンマ区切り。例 odpt.Operator:Toei)
  - `--out-dir`: 保存先ルート
  - `--repeat`: ODPT リアルタイムのスナップショット回数
  - `--report`: 取得台帳のレポート(未取得日・odpt_rt の欠けた時間帯・ディスクの量)。ネットワーク不使用
  - `--retries`: リトライ回数(指数バックオフ)
  - `--rotate-logs`: 台帳 _ledger.jsonl とタスクのログ(_scheduler_odpt.log・_scheduler.log)を今すぐ回して gzip する(_logs/ の下へ・書き手が開いていれば次の回へ)。ネットワーク不使用。通常の取得の回でも、その日にまだ回していないものを回す(第337)
  - `--save-xml`: 防災情報XML の生 XML も保存する
  - `--sleep`: リクエスト間の礼儀的待機秒
  - `--source`: (help を読めない)
  - `--static-types`: odpt_static: 種類を絞る(カンマ区切り。例 odpt:Railway,odpt:Station)
  - `--survey`: odpt_static: オープン枠の operator × 種類の件数・バイト・日付の範囲の表を作る(データの値は保存しない。--static-types で種類を絞れる)
  - `--timeout`: 1リクエストのタイムアウト秒
  - `--verify`: 保存済みファイル(.json と .json.gz)のスキーマ検証。ネットワーク不使用
- 環境変数: 名前を読めない所 1 か所
- 決定の ID: 第 333・第 337

## [common.py](../../../../../../tools/realworld_fetch/common.py)

RW-U1 共通基盤: HTTP・秘密のスクラブ・`_meta` 付与・保存・時刻。

- 公開の関数とクラス
  - `CrossHostRedirect`(クラス): 転送先のホストが元の要求と違うので追わなかった(第333)。
  - `HttpResult`(クラス)
  - `build_meta`(関数): 保存物に必ず付ける `_meta`(既存 `scripts/fetch_odpt.py` の `_meta` 規約と同型)。
  - `canonical_json`(関数)
  - `clear_secrets`(関数)
  - `contains_secret`(関数)
  - `date_range`(関数): start..end(両端含む)。
  - `day_dir`(関数): 日付パーティション `data/realworld/<source>/<YYYY>/<MM>/<YYYY-MM-DD>/`。
  - `decode_text`(関数)
  - `http_get`(関数): GET。指数バックオフで**小回数**だけ再試行する。例外文面は型名/コードのみ返す。
  - `iso_jst`(関数)
  - `iso_utc`(関数)
  - `json_bytes_compact`(関数): 保存と同じ形(区切りの空白なし・ensure_ascii=False・末尾改行)の UTF-8 バイト列。scrub 済み。
  - `log`(関数): 標準出力/標準エラーへの唯一の出口。必ず scrub を通す。
  - `month_dir`(関数)
  - `n_secrets`(関数): 登録件数(値は返さない)。
  - `now_jst`(関数)
  - `now_utc`(関数)
  - `parse_date`(関数): `YYYY-MM-DD` / `YYYYMMDD` を date に。
  - `polite_sleep`(関数): 相手サーバへの礼儀としての間隔。0 以下なら何もしない。
  - `read_json_any`(関数): `.json` と `.json.gz` の両方を読む(ネット不使用)。
  - `reconfigure_stdio`(関数): Windows コンソールでの日本語出力の文字化け対策(失敗しても致命ではない)。
  - `register_secret`(関数): 出力から潰すべき文字列(APIキー等)を登録する。値はここ以外に保存しない。
  - `request_count`(関数): このプロセスが `http_get` 経由で試みた HTTP 要求数(`--offline` の 0 固定に使う)。
  - `reset_request_count`(関数)
  - `resolve_key`(関数): 環境変数から API キーを解決し、同時に秘密として登録する(値は返すだけ)。
  - `save_raw_on_failure`(関数): パース失敗時に生バイト列を `_raw_failed/` へ退避する(黙って空にしない)。
  - `scrub`(関数): 登録済みの秘密を `***` に置換する。URL エンコード形も潰す。
  - `scrub_bytes`(関数)
  - `validate_document`(関数): 保存物のスキーマ検証(ネットワーク不使用)。問題のリストを返す(空 = 合格)。
  - `write_bytes`(関数): 生バイト列の保存(パース失敗時の証拠保全 = リスク R2)。ここでも scrub する。
  - `write_json`(関数): JSON 保存。**書く直前に必ず scrub** する(キーが保存物に落ちる経路を潰す)。
  - `write_json_gz`(関数): gzip した JSON の保存。**書く直前に必ず scrub** する(`write_json` と同じ)。
- 呼び手: `tools/realworld_fetch/amedas.py`・`tools/realworld_fetch/cli.py`・`tools/realworld_fetch/jma_xml.py`・`tools/realworld_fetch/ledger.py`・`tools/realworld_fetch/logrotate.py`・`tools/realworld_fetch/odpt_passenger_survey.py`・`tools/realworld_fetch/odpt_rt.py`・`tools/realworld_fetch/odpt_static.py`・`tools/realworld_fetch/shibuya_jinryu.py`・`tools/realworld_fetch/transport_census.py`・`tools/realworld_fetch/wbgt.py`
- 読む試験: `tests/tools/test_realworld_fetch_odpt.py`
- 環境変数: 名前を読めない所 1 か所
- 決定の ID: 第 333

## [jma_etrn.py](../../../../../../tools/realworld_fetch/jma_etrn.py)

気象庁「過去の気象データ検索」(etrn)の東京(prec_no=44・block_no=47662)を日ごとに取り、表にする。

- 公開の関数とクラス
  - `cmd_fetch`(関数)
  - `cmd_table`(関数)
  - `data_rows`(関数): 見出し行を除いたデータ行(時別値は 24 行・10 分値は 144 行)。
  - `main`(関数)
  - `page_url`(関数)
  - `raw_path`(関数)
  - `table_cells`(関数): ``id='tablefix1'`` の表 → 行ごとのセル(タグを除いた文字列)。
- CLI の引数
  - `--end`
  - `--interval`
  - `--kind`
  - `--start`
  - 名前を読めない呼び出し 1 か所
- 決定の ID: 10-12b・第 330

## [jma_xml.py](../../../../../../tools/realworld_fetch/jma_xml.py)

A5: 気象庁 防災情報XML(Atom フィード)。**外れ値日ラベル**の材料。

- 公開の関数とクラス
  - `feed_url`(関数)
  - `fetch_all`(関数)
  - `fetch_feed`(関数)
  - `is_outlier`(関数)
  - `is_tokyo`(関数)
  - `out_path`(関数)
  - `outlier_labels`(関数): 東京関連かつ外れ値候補のエントリを **日(JST)ごと** にまとめる。
  - `parse_atom`(関数): Atom フィード → エントリ列。壊れていれば ParseError/ValueError で落とす(空にしない)。
  - `plan`(関数)
- import している内部モジュール: `tools/realworld_fetch/common.py`・`tools/realworld_fetch/ledger.py`
- 呼び手: `tools/realworld_fetch/cli.py`

## [ledger.py](../../../../../../tools/realworld_fetch/ledger.py)

RW-U1 取得台帳: いつ・何を・何件・欠測いくつ・HTTP ステータス を1行ずつ追記する。

- 公開の関数とクラス
  - `append`(関数): 台帳へ追記する。戻り値 = 書いた行数。**追記のみ・既存行は決して書き換えない。**
  - `day_status`(関数): `ok` / `partial` / `failed` / `missing`。
  - `disk_usage`(関数): `root` の下のファイルの大きさを種類ごとに足す(中身は読まない)。
  - `format_disk_report`(関数)
  - `format_report`(関数): 人が読む取得台帳レポート(`--report`)。ネットワーク不使用。
  - `format_rt_report`(関数)
  - `gap_report`(関数): 未取得日を「まだ間に合う(URGENT)」と「もう取れない(LOST)」に分けて返す。
  - `ledger_path`(関数)
  - `make_entry`(関数): 台帳1行。`date_jst` は「そのデータが属する日」(取得日ではない)。
  - `missing_days`(関数): start..end のうち `ok` でない日(= partial / failed / missing)を返す。
  - `ok_days`(関数): そのソースで **成功した** 日(date_jst)の集合。
  - `read_all`(関数): 台帳を読む。壊れた行は捨てずに `{"_broken": 生テキスト}` として返す(黙って消さない)。
  - `rt_gap_report`(関数): odpt_rt の日ごとの「取得の無かった 1 時間の枠」と、種類ごとのスナップショット数。
  - `rt_row_time`(関数): 行の時刻(JST)。`extra.snapshot_jst` があればそれ、無ければ `ts_utc`。
  - `rt_row_type`(関数)
  - `summary`(関数): ソース別の件数・最終成功時刻・失敗件数。
- import している内部モジュール: `tools/realworld_fetch/common.py`・`tools/realworld_fetch/logrotate.py`
- 呼び手: `tools/realworld_fetch/amedas.py`・`tools/realworld_fetch/cli.py`・`tools/realworld_fetch/jma_xml.py`・`tools/realworld_fetch/odpt_passenger_survey.py`・`tools/realworld_fetch/odpt_rt.py`・`tools/realworld_fetch/odpt_static.py`・`tools/realworld_fetch/shibuya_jinryu.py`・`tools/realworld_fetch/transport_census.py`・`tools/realworld_fetch/wbgt.py`
- 読む試験: `tests/tools/test_realworld_fetch_logrotate.py`・`tests/tools/test_realworld_fetch_odpt.py`
- 決定の ID: 第 333・第 337

## [logrotate.py](../../../../../../tools/realworld_fetch/logrotate.py)

取得の台帳とログを日ごとに回して gzip で縮める(第337・回答 10-13b §7 の 5・§5 追記「保存するときに圧縮」)。

- 公開の関数とクラス
  - `LogSpec`(クラス)
  - `RotateBusy`(クラス): 書き手がファイルを開いている(改名できない)か、ほかの回しが錠を持っている。
  - `archive_root`(関数)
  - `archives`(関数): `name` の gz の一覧 (rotid, 日, 塊の番, 道筋)。並び=元の並び(rotid → 塊の番)。
  - `count_lines`(関数)
  - `format_results`(関数)
  - `iter_chunks`(関数): 元の並びでバイト列を返す: gz(残った rotating の rotid は除く)→ 残った rotating → 生きているファイル。
  - `maybe_rotate`(関数): その日にまだ回していないものを回す(``force`` なら日に依らず回す)。失敗しても取得の回を止めない。
  - `pending`(関数): 途中で落ちた回しの残り (rotid, 道筋)。
  - `read_bytes_all`(関数)
  - `read_text_all`(関数)
  - `rotate_one`(関数): 1 本を回す。戻り値 = 結果(``status`` = rotated / empty / busy)。
  - `spec_of`(関数)
  - `split_days`(関数): バイト列を日ごとの連続した塊に分ける(つなぐと元と同じ)。日は前へ戻らない(戻る行は前の日の塊に残す)。
  - `wait_writers`(関数): POSIX: 改名の前に開いていた書き手の追記が終わるまで待つ(``ledger.append`` は追記の間 flock を持ち、
- import している内部モジュール: `tools/realworld_fetch/common.py`
- 呼び手: `tools/realworld_fetch/cli.py`・`tools/realworld_fetch/ledger.py`
- 読む試験: `tests/tools/test_realworld_fetch_logrotate.py`
- 決定の ID: 10-13b/§7・第 337

## [odpt_passenger_survey.py](../../../../../../tools/realworld_fetch/odpt_passenger_survey.py)

P4境界較正 B: ODPT `odpt:PassengerSurvey`(駅別の年度乗降/乗車人員)。

- 公開の関数とクラス
  - `api_url`(関数): 実要求 URL(キー入り)。**この戻り値は絶対に print / 保存しない。**
  - `common_year`(関数): **全事業者がそろって値を持つ最新の年度**。無ければ None。
  - `dedupe_records`(関数): 同一計上(メトロ渋谷の半蔵門線/副都心線)を1件に畳む。戻り値 = (残した, 畳んだ識別子)。
  - `display_url`(関数): 表示・保存用 URL(consumerKey は常に *** 固定)。
  - `ensure_readme`(関数)
  - `fetch_all`(関数): 4事業者の PassengerSurvey を取り、渋谷の行だけを1ファイルにまとめる。
  - `is_station`(関数): `odpt:station` のいずれかが `.<station>` で終わるか(部分一致で拾いすぎない)。
  - `load_saved`(関数): 保存済み JSON を読む(ネットワーク不使用)。
  - `out_path`(関数)
  - `plan`(関数): `--offline` 用。キーを渡さないので URL に載りようがない。
  - `summarize`(関数): 境界較正で最初に見る要約(単位ごと・**年度をそろえて**合計する)。
  - `to_records`(関数): API のレコードを、こちらの語彙(単位を明示した形)に写す。値は無加工。
  - `totals_for_year`(関数): 指定年度の measure 別合計。**measure が違う値は別々に積む**(足してはいけない)。
  - `year_series`(関数): `odpt:passengerSurveyObject` → `{年度: 人数}`。壊れた要素は黙って捨てず飛ばす。
- import している内部モジュール: `tools/realworld_fetch/common.py`・`tools/realworld_fetch/ledger.py`

## [odpt_rt.py](../../../../../../tools/realworld_fetch/odpt_rt.py)

A4: ODPT リアルタイム(運行情報 TrainInformation・列車の在線 Train・バスの在線 Bus)。

- 公開の関数とクラス
  - `api_url`(関数): 実要求 URL(キー入り)。**この戻り値は絶対に print / 保存しない。**
  - `content_hash`(関数): `DEDUPE_IGNORE_KEYS` を除いた正準 JSON(レコードの順は問わない)の sha256。
  - `delay_summary`(関数): 在線レコードの遅延(秒)の要約。値が無ければ None(0 と偽らない)。
  - `display_url`(関数): 表示・保存用 URL。consumerKey は常に *** 固定(キーを渡さないので漏れようがない)。
  - `due`(関数): 間隔に達したか。前回が無い・時計が戻った・読めないときは取る。
  - `ensure_readme`(関数)
  - `fetch_snapshot`(関数): 運行情報・在線・バスの 1 スナップショット。戻り値 = (保存した文書のリスト, 台帳行)。
  - `is_capped`(関数): 検索の口の打ち切りに当たった疑い。上限は種類で違う(多くは 1,000。BusstopPole は 10,000 の
  - `job_key`(関数)
  - `jobs`(関数): 取得の単位 = (枠, 種類, operator) と、その問い合わせの並び。
  - `load_state`(関数): `_last_fetch.json` を読む。無い・壊れているときは空(壊れたものは `_broken` に数える)。
  - `op_short`(関数): `odpt.Operator:TokyoMetro` → `TokyoMetro`。
  - `op_token`(関数): ファイル名の operator の部分。チャレンジ枠は `-challenge` を付ける。
  - `out_path`(関数): `odpt_rt/<Y>/<M>/<D>/<種類>_<operator>_<HHMMSS>.json.gz`。
  - `plan`(関数): `--offline` 用。キーは渡さないので URL に載らない。
  - `save_state`(関数)
  - `shibuya_railways`(関数): 渋谷9路線に該当するレコードだけを残す(第333 からはチャレンジ枠の作品の範囲にだけ使う)。
  - `split_expired`(関数): `dct:valid` を過ぎたレコードを外す。戻り値 = (有効, 期限切れの識別子)。
  - `state_path`(関数)
  - `static_busroutes`(関数): 保存済みの静的データの最新版(`odpt_static/<日付>/busroutepattern_<op>.json.gz`)の系統の一覧。
- import している内部モジュール: `tools/realworld_fetch/common.py`・`tools/realworld_fetch/ledger.py`
- 呼び手: `tools/realworld_fetch/cli.py`・`tools/realworld_fetch/odpt_static.py`
- 読む試験: `tests/tools/test_realworld_fetch_odpt.py`
- 決定の ID: 10-13b/§5・第 333

## [odpt_static.py](../../../../../../tools/realworld_fetch/odpt_static.py)

第333: ODPT オープン枠の静的データ(時刻表・駅・路線・バス停と系統・乗降人員・運賃)の版の保存。

- 公開の関数とクラス
  - `check`(関数): 保存済みの最新版と、いま API が返す `dct:issued`(無ければ `dc:date`)の最大を比べる。
  - `fetch_complete`(関数): operator の `datatype` を、打ち切りに当たったら分けて取り直して全部集める。
  - `fetch_version`(関数): オープン枠の静的データの版を 1 回取り、`odpt_static/<取得日>/` に残す。
  - `file_name`(関数)
  - `format_check`(関数)
  - `latest_version`(関数)
  - `list_operators`(関数): オープン枠の `odpt:Operator` の一覧(owl:sameAs の並び)。失敗なら (None, res)。
  - `op_short`(関数): `odpt.Operator:TokyoMetro` → `TokyoMetro`(ファイル名用)。
  - `plan`(関数): `--offline` 用(キーは渡さない)。operator の一覧の 1 本と、種類ごとの問い合わせの形。
  - `record_stats`(関数): 件数と `dct:issued`・`dc:date`・`dct:valid` の範囲(文字列の最小・最大)。値の中身は持たない。
  - `survey`(関数): operator × 種類を 1 本ずつ問い合わせ、件数・バイト(生と gzip 後)・日付の範囲を表にする。
  - `type_short`(関数): `odpt:StationTimetable` → `stationtimetable`(ファイル名用)。
  - `version_dir`(関数)
- import している内部モジュール: `tools/realworld_fetch/common.py`・`tools/realworld_fetch/ledger.py`・`tools/realworld_fetch/odpt_rt.py`
- 呼び手: `tools/realworld_fetch/cli.py`
- 読む試験: `tests/tools/test_realworld_fetch_odpt.py`
- 決定の ID: 10-13・10-13b/§5・第 333

## [rw_fetch_daily.py](../../../../../../tools/realworld_fetch/rw_fetch_daily.py)

RW-U1 現実世界データ日次取得のエントリポイント(薄い起動器)。

- import している内部モジュール: `tools/realworld_fetch/cli.py`
- 読む試験(道筋で): `tests/tools/test_repo_guide.py`

## [shibuya_jinryu.py](../../../../../../tools/realworld_fetch/shibuya_jinryu.py)

A3: 渋谷区オープンデータ「Location Analyzer による通行/滞在人口」6 データセット。

- 公開の関数とクラス
  - `already_fetched`(関数): 既に取得済みならそのパス(月次なので取り直す必要が無い)。
  - `csv_url`(関数)
  - `fetch_all`(関数): 6 データセットを取得。既取得のものは `force` でなければ **リクエストを出さずに** 飛ばす。
  - `fetch_one`(関数)
  - `geojson_url`(関数)
  - `out_path`(関数)
  - `parse_csv`(関数): 人流 CSV → (レコード列, ヘッダ, 欠測セル数)。BOM 除去のみ・値は無加工。
  - `plan`(関数)
  - `split_k5`(関数): 戻り値 = (本層に入れる行(年 <= max_year か年が読めない行), K5 の候補(年 > max_year))。
  - `summarize`(関数): 空間・時間のカバレッジ要約(較正で最初に見る数字)。
  - `verify_against_dcat`(関数): DCAT フィードに itemId と表題が実在するかを照合する(スキーマ漂流の検知)。
- import している内部モジュール: `tools/realworld_fetch/common.py`・`tools/realworld_fetch/ledger.py`
- 呼び手: `tools/realworld_fetch/cli.py`
- 読む試験: `tests/tools/test_realworld_fetch_jinryu.py`
- 決定の ID: R-114・第 333

## [transport_census.py](../../../../../../tools/realworld_fetch/transport_census.py)

P4境界較正 A: 大都市交通センサス(国土交通省)の駅別・時間帯別集計表。

- 公開の関数とクラス
  - `already_fetched`(関数)
  - `clean_time_label`(関数): 時間帯の見出し(`始発～6:59シハツ`)からルビを落とす。
  - `default_tables`(関数)
  - `fetch_all`(関数): 既定4表(+ --with-od13)を取得。既取得は `force` でなければ**要求を出さずに**飛ばす。
  - `fetch_one`(関数): 1表を取得 → パース → JSON 保存。失敗時は生バイト列を残して台帳に理由を書く。
  - `load_saved`(関数): 保存済み JSON を `{table_key: doc}` で読む(ネットワーク不使用)。
  - `norm`(関数): 全角空白・改行・前後空白を潰した比較用の文字列。
  - `out_path`(関数)
  - `parse_line_capacity`(関数): 表9 路線別着時間帯別駅間輸送定員表 → 駅間×着時間帯の**輸送定員**(実乗客数ではない)。
  - `parse_station_flow`(関数): 表3 駅別発着・駅間通過人員表 → 長形式レコード。
  - `parse_station_od`(関数): 第13回 初乗り・最終降車駅間移動人員 → 駅間 OD(**改札外→改札外**の実移動)。
  - `parse_time_dist`(関数): 参考表5 目的別乗車降車時刻分布 → 目的×乗降×時間帯の構成比。
  - `parse_transfer`(関数): 表4 ターミナル別乗換え人員表 → 到着線→行先線の乗換行列 + ピーク時。
  - `plan`(関数): `--offline` 用の取得計画(1リクエストも出さない)。
  - `raw_path`(関数)
  - `read_xlsx_rows`(関数): xlsx → 行×セル(すべて文字列)。**openpyxl に依存しない**(zip + XML だけ)。
  - `run_parser`(関数): 表定義の `parser` に従ってパースする。時刻分布だけは駅の次元を持たない。
  - `sheet_names`(関数)
  - `strip_ruby`(関数): センサス表のセルは `駅名エキメイ` のように**ルビが本文に連結**されている。
  - `to_number`(関数): `'121926'` → int / `'6.44E-2'` → float / 空・`-` → None。桁区切りは許す。
- import している内部モジュール: `tools/realworld_fetch/common.py`・`tools/realworld_fetch/ledger.py`

## [wbgt.py](../../../../../../tools/realworld_fetch/wbgt.py)

A2: 環境省 暑さ指数(WBGT)電子情報提供サービス・地点 44132。

- 公開の関数とクラス
  - `count_est_missing`(関数)
  - `count_forecast_missing`(関数)
  - `est_path`(関数)
  - `est_url`(関数)
  - `fetch_day`(関数): 実況 + 予測 をまとめて取得。戻り値 = (文書リスト, 台帳行)。
  - `fetch_est`(関数): 実況(月次累積)を取得。月内なら後追い可能なので取り逃しに強い。
  - `fetch_forecast`(関数): 予測(3時間値・0.1℃)を取得。**上書き配信なので後追い不可。**
  - `forecast_path`(関数)
  - `forecast_url`(関数)
  - `in_service_period`(関数)
  - `parse_est_csv`(関数): 実況 CSV → (レコード列, 地点ID列)。**空欄は null**(0 で埋めない)。
  - `parse_forecast_csv`(関数): 予測 CSV → 地点ごとのレコード。**0.1℃ のまま**(換算しない)。
  - `plan_day`(関数)
- import している内部モジュール: `tools/realworld_fetch/common.py`・`tools/realworld_fetch/ledger.py`
- 呼び手: `tools/realworld_fetch/cli.py`
