# ODPT の集め方の変更(第333): オープン枠の洗い出し・取得器の変更・量の実測

> 位置づけ: [回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §5 とその追記(ユーザー決定 2026-10-13)の実装。作業は実行役(Opus 5.5)で、親の検収前。本書には時刻・位置・遅延などの値を書かず、件数・バイト数・日付の範囲だけを書く。パスは `<scratch>`(実行役の一時フォルダ)と、リポジトリからの相対パスで書く。

## 0. 結論

1. **オープン枠の洗い出し**: `odpt:Operator` は 42 社。航空会社 11 社を除く 31 社 × 17 種類と、operator で絞らない 17 本の計 544 要求を出し、誤りは 0 件だった(2026-10-13 22:17〜22:33)。データのある operator は 28 社で、件数が 1 以上の組は 118 組。
   - リアルタイム(夜 22 時台の照会): 運行情報 6 社(MIR・TWR・多摩モノレール・都営・東京メトロ・横浜市)、列車の在線 2 社(都営・横浜市)、バスの在線 3 社(西武バス・都営・横浜市)。東京メトロは列車の在線を出していない(0 件)。東急バスと相鉄バスは静的データはあるが、バスの在線は 0 件だった。京王バス・西東京バス・小田急バスは全種類 0 件。
   - 静的: 路線と駅は 25 社。駅の時刻表は 7 社、列車の時刻表は 6 社、バスの系統・標柱・時刻表は 5 社(西武バス・相鉄バス・都営・東急バス・横浜市)。
2. **API の性質(実測)**: 検索の口は 1 応答 1,000 件で打ち切られる(14 組が当たった。`BusstopPole` を operator で絞らずに問い合わせると 10,000 件ちょうどで止まった)。値をカンマでつなぐと OR になるが、**10 個まで**で、11 個にすると HTTP 400 になる。ダンプの口(`odpt:<種類>.json`)は別ドメイン(`dataodpt.blob.core.windows.net`)への転送を返したので、取得しなかった(許可の一覧の外)。
3. **取得器の変更**: オープン枠のリアルタイムは提供のある operator の全レコードを保存するようにした。チャレンジ枠は今の範囲(東急 2 線・京王 井の頭線の運行情報と JR 3 線の在線)のまま。保存は gzip(`.json.gz`)。種類ごとの間隔の表と `_last_fetch.json`、運行情報の変化分だけの保存、静的データの版(`odpt_static`)と `--check`、`--report` の欠けた時間帯とディスクの量を足した。
4. **量(夜 22 時台の 3 回の平均・gzip 後)**: バスの在線 50.5 KB、列車の在線 8.8 KB(オープン)+ 4.6 KB(JR)、運行情報 13.9 KB(保存した回だけ。2 回目と 3 回目は 8 本とも変化なしで保存しなかった)。圧縮はバスと在線で約 9 倍。
5. **年の見込み**: 今の既定(3 種類とも 5 分)で年 約 13 GB(10〜18 GB)、列車の在線だけ 1 分にしても年 約 19 GB(16〜25 GB)。どちらも年 50 GB に収まる(§6)。
6. **試験**: 新しい試験 19 本が通った(ネットワークに出ない)。本体へ写した後の `--offline` は要求 0 本(§5)。

## 1. 取得の方法と守ったこと

- 取得したドメインは `api.odpt.org` だけ(チャレンジ枠の `api-challenge.odpt.org` は、写しの取得器の 3 回の実行で今の範囲の 5 本ずつだけ)。開発者サイトと CKAN には出ていない。
- 転送を追わない仕組みを取得器に足した(`common.http_get(..., same_host_only=True)`。ODPT の要求だけに効く)。ダンプの口の転送はこの仕組みで止まった(`cross-host-redirect-refused:dataodpt.blob.core.windows.net`・再試行しない)。
- キーは環境変数から `common.resolve_key` で読み、URL は `acl:consumerKey=***` の形でしか残していない。`<scratch>` の出力 1,998 本(gzip を開いた中身を含む)に 2 つのキーの文字列が無いことを機械で確かめた(0 件)。
- 礼儀の待ち 1 秒・再試行は小回数。洗い出しの要求は 1 本ずつ台帳の行と `_survey_<日付>_<時刻>.jsonl` の行に残した(`<scratch>/rwdev_out/`)。
- 開発は `<scratch>/rwdev/` の写しで行い、実取得も写しから `<scratch>/rwdev_out/` に向けた。本番の `data/realworld_live/` には書いていない(読んだのはファイルの大きさと数だけ)。

## 2. §A オープン枠の洗い出しの表(2026-10-13 22:17〜22:33)

- 件数は 1 本の問い合わせ(`?odpt:operator=<op>`)の応答の件数。「疑い」は 1,000 の倍数ちょうど(打ち切りに当たった疑い)で、本当の件数はもっと多い。
- 生 KB は応答のバイト数、gzip KB は同じバイト列を gzip(水準 6)にかけた大きさ。
- 日付の範囲は文字列の最小〜最大(日まで)。`dct:issued` があるのは時刻表と運賃だけで、他の種類は `dc:date` だけを持つ。
- `odpt:BusstopPoleTimetable` は洗い出しにだけ入れた(`BusTimetable` を標柱ごとに並べ直した形で量が大きい。版の取得には入れていない=親の判断待ち)。

### 2-1. 種類ごとの提供(operator の数と件数)

| 種類 | 提供のある operator(件数。* は打ち切りの疑い) |
|---|---|
| `odpt:TrainInformation` | 6 社: MIR 1・TWR 1・TamaMonorail 1・Toei 6・TokyoMetro 10・YokohamaMunicipal 2 |
| `odpt:Train` | 2 社: Toei 75・YokohamaMunicipal 22 |
| `odpt:Bus` | 3 社: SeibuBus 159・Toei 140・YokohamaMunicipal 236 |
| `odpt:Railway` | 25 社: Hokuso 1・JR-Central 1・JR-East 24・KantoRailway 1・Keikyu 4・Keio 7・Keisei 3・MIR 1・Minatomirai 1・Odakyu 3・OdakyuHakone 1・SaitamaRailway 1・Seibu 7・Shibayama 1・Sotetsu 3・TWR 1・TamaMonorail 1・Tobu 6・Toei 6・TokyoMetro 10・TokyoMonorail 1・Tokyu 6・ToyoRapid 1・YokohamaMunicipal 2・Yurikamome 1 |
| `odpt:Station` | 25 社: Hokuso 2・JR-Central 2・JR-East 134・KantoRailway 1・Keikyu 14・Keio 18・Keisei 13・MIR 20・Minatomirai 2・Odakyu 13・OdakyuHakone 1・SaitamaRailway 3・Seibu 19・Shibayama 1・Sotetsu 8・TWR 8・TamaMonorail 19・Tobu 17・Toei 149・TokyoMetro 186・TokyoMonorail 2・Tokyu 27・ToyoRapid 3・YokohamaMunicipal 42・Yurikamome 16 |
| `odpt:StationTimetable` | 7 社: MIR 76・TWR 28・TamaMonorail 72・Toei 634・TokyoMetro 704・YokohamaMunicipal 160・Yurikamome 60 |
| `odpt:TrainTimetable` | 6 社: MIR 841・TWR 564・TamaMonorail 472・Toei 1,000*・TokyoMetro 1,000*・YokohamaMunicipal 1,000* |
| `odpt:TrainType` | 7 社: MIR 4・TWR 3・TamaMonorail 1・Toei 8・TokyoMetro 12・YokohamaMunicipal 2・Yurikamome 1 |
| `odpt:RailDirection` | 2 社: Toei 3・TokyoMetro 17 |
| `odpt:Calendar` | 3 社: SeibuBus 42・Toei 72・YokohamaMunicipal 47 |
| `odpt:BusroutePattern` | 5 社: SeibuBus 754・SotetsuBus 216・Toei 757・TokyuBus 747・YokohamaMunicipal 1,000* |
| `odpt:BusstopPole` | 5 社: SeibuBus 4,860・SotetsuBus 1,389・Toei 3,690・TokyuBus 3,044・YokohamaMunicipal 2,514 |
| `odpt:BusTimetable` | 5 社: SeibuBus 1,000*・SotetsuBus 1,000*・Toei 1,000*・TokyuBus 1,000*・YokohamaMunicipal 1,000* |
| `odpt:PassengerSurvey` | 6 社: MIR 20・TWR 8・TamaMonorail 19・Toei 119・TokyoMetro 147・YokohamaMunicipal 42 |
| `odpt:RailwayFare` | 7 社: MIR 380・TWR 56・TamaMonorail 342・Toei 1,000*・TokyoMetro 1,000*・YokohamaMunicipal 1,000*・Yurikamome 240 |
| `odpt:BusroutePatternFare` | 2 社: Toei 1,000*・YokohamaMunicipal 1,000* |
| `odpt:BusstopPoleTimetable` | 2 社: Toei 1,000*・TokyuBus 1,000* |

### 2-2. operator × 種類の表(件数が 1 以上の 118 組)

| operator | 種類 | 件数 | 打ち切り | 生 KB | gzip KB | dct:issued の範囲 | dc:date の範囲 |
|---|---|---:|---|---:|---:|---|---|
| Hokuso | Railway | 1 |  | 0.4 | 0.3 | — | 2024-06-27 |
| Hokuso | Station | 2 |  | 0.8 | 0.3 | — | 2023-03-18 |
| JR-Central | Railway | 1 |  | 0.4 | 0.3 | — | 2024-08-29 |
| JR-Central | Station | 2 |  | 0.8 | 0.3 | — | 2024-03-29 |
| JR-East | Railway | 24 |  | 9.3 | 1.1 | — | 2024-06-27〜2024-08-29 |
| JR-East | Station | 134 |  | 53.7 | 3.7 | — | 2023-03-18〜2024-03-27 |
| KantoRailway | Railway | 1 |  | 0.4 | 0.3 | — | 2024-06-27 |
| KantoRailway | Station | 1 |  | 0.4 | 0.3 | — | 2024-03-29 |
| Keikyu | Railway | 4 |  | 1.5 | 0.4 | — | 2024-06-27 |
| Keikyu | Station | 14 |  | 5.7 | 0.9 | — | 2023-03-18〜2024-03-27 |
| Keio | Railway | 7 |  | 2.6 | 0.5 | — | 2024-06-27 |
| Keio | Station | 18 |  | 7.1 | 1.0 | — | 2023-03-18〜2024-08-29 |
| Keisei | Railway | 3 |  | 1.2 | 0.4 | — | 2024-06-27 |
| Keisei | Station | 13 |  | 5.2 | 0.7 | — | 2023-03-18〜2024-03-29 |
| MIR | TrainInformation | 1 |  | 0.5 | 0.3 | — | 2026-10-13 |
| MIR | Railway | 1 |  | 4.9 | 1.5 | — | 2024-06-27 |
| MIR | Station | 20 |  | 20.1 | 2.7 | — | 2024-05-14 |
| MIR | StationTimetable | 76 |  | 2,694.0 | 130.7 | 2025-03-15 | 2025-03-17 |
| MIR | TrainTimetable | 841 |  | 2,115.8 | 77.2 | 2025-03-15 | 2025-03-17 |
| MIR | TrainType | 4 |  | 1.4 | 0.3 | — | 2021-06-24 |
| MIR | PassengerSurvey | 20 |  | 11.4 | 0.9 | — | 2026-07-03 |
| MIR | RailwayFare | 380 |  | 216.2 | 6.5 | 2026-03-14 | 2026-08-12 |
| Minatomirai | Railway | 1 |  | 0.4 | 0.3 | — | 2024-06-27 |
| Minatomirai | Station | 2 |  | 0.9 | 0.3 | — | 2023-03-18〜2024-03-29 |
| Odakyu | Railway | 3 |  | 1.1 | 0.3 | — | 2024-06-27 |
| Odakyu | Station | 13 |  | 5.2 | 0.8 | — | 2023-03-18〜2024-08-29 |
| OdakyuHakone | Railway | 1 |  | 0.4 | 0.3 | — | 2024-06-27 |
| OdakyuHakone | Station | 1 |  | 0.4 | 0.3 | — | 2024-06-20 |
| SaitamaRailway | Railway | 1 |  | 0.4 | 0.3 | — | 2024-06-27 |
| SaitamaRailway | Station | 3 |  | 1.3 | 0.4 | — | 2023-03-18〜2024-03-29 |
| Seibu | Railway | 7 |  | 2.6 | 0.5 | — | 2024-06-27 |
| Seibu | Station | 19 |  | 7.5 | 0.9 | — | 2023-03-18〜2024-03-27 |
| SeibuBus | Bus | 159 |  | 174.2 | 20.4 | — | 2026-10-13 |
| SeibuBus | Calendar | 42 |  | 24.3 | 0.9 | — | — |
| SeibuBus | BusroutePattern | 754 |  | 2,512.8 | 236.0 | — | 2026-09-24 |
| SeibuBus | BusstopPole | 4,860 |  | 3,388.1 | 223.7 | — | 2026-09-24 |
| SeibuBus | BusTimetable | 1,000 | 疑い | 7,626.5 | 407.8 | — | 2026-09-24 |
| Shibayama | Railway | 1 |  | 0.4 | 0.3 | — | 2024-06-27 |
| Shibayama | Station | 1 |  | 0.4 | 0.3 | — | 2023-03-18 |
| Sotetsu | Railway | 3 |  | 1.2 | 0.4 | — | 2024-06-27 |
| Sotetsu | Station | 8 |  | 3.2 | 0.6 | — | 2023-03-18〜2024-03-27 |
| SotetsuBus | BusroutePattern | 216 |  | 515.7 | 40.5 | — | 2026-10-01 |
| SotetsuBus | BusstopPole | 1,389 |  | 950.7 | 60.2 | — | 2026-10-01 |
| SotetsuBus | BusTimetable | 1,000 | 疑い | 3,805.0 | 178.2 | — | 2026-10-01 |
| TWR | TrainInformation | 1 |  | 0.4 | 0.3 | — | 2026-10-13 |
| TWR | Railway | 1 |  | 2.2 | 0.9 | — | 2024-06-27 |
| TWR | Station | 8 |  | 7.9 | 1.4 | — | 2021-06-21〜2024-03-27 |
| TWR | StationTimetable | 28 |  | 834.1 | 42.6 | 2026-03-14 | 2026-03-16 |
| TWR | TrainTimetable | 564 |  | 826.8 | 30.8 | 2026-03-14 | 2026-03-16 |
| TWR | TrainType | 3 |  | 1.0 | 0.3 | — | 2020-03-27〜2024-12-17 |
| TWR | PassengerSurvey | 8 |  | 4.9 | 0.6 | — | 2025-11-04 |
| TWR | RailwayFare | 56 |  | 29.9 | 1.1 | 2019-10-01 | 2020-03-27 |
| TamaMonorail | TrainInformation | 1 |  | 0.5 | 0.3 | — | 2026-10-13 |
| TamaMonorail | Railway | 1 |  | 3.4 | 0.9 | — | 2024-06-27 |
| TamaMonorail | Station | 19 |  | 18.8 | 1.9 | — | 2021-06-24〜2024-03-27 |
| TamaMonorail | StationTimetable | 72 |  | 2,141.0 | 77.8 | 2022-03-12〜2023-03-20 | 2023-03-28 |
| TamaMonorail | TrainTimetable | 472 |  | 1,383.9 | 49.1 | 2022-03-12〜2023-03-20 | 2023-03-28 |
| TamaMonorail | TrainType | 1 |  | 0.3 | 0.2 | — | 2021-06-24 |
| TamaMonorail | PassengerSurvey | 19 |  | 24.1 | 2.2 | — | 2026-07-07 |
| TamaMonorail | RailwayFare | 342 |  | 209.1 | 4.8 | 2019-10-01 | 2021-06-24 |
| Tobu | Railway | 6 |  | 2.4 | 0.5 | — | 2024-06-27 |
| Tobu | Station | 17 |  | 6.7 | 0.9 | — | 2023-03-18〜2024-03-29 |
| Toei | TrainInformation | 6 |  | 3.1 | 0.6 | — | 2026-10-13 |
| Toei | Train | 75 |  | 53.6 | 4.5 | — | 2026-10-13 |
| Toei | Bus | 140 |  | 131.0 | 14.0 | — | 2026-10-13 |
| Toei | Railway | 6 |  | 22.9 | 4.0 | — | 2024-06-27 |
| Toei | Station | 149 |  | 142.2 | 12.9 | — | 2021-08-17〜2024-06-27 |
| Toei | StationTimetable | 634 |  | 25,083.7 | 1,429.8 | 2019-12-22〜2026-03-16 | 2023-11-25〜2026-03-16 |
| Toei | TrainTimetable | 1,000 | 疑い | 5,127.5 | 178.7 | 2019-12-22〜2025-12-15 | 2023-11-25〜2025-12-15 |
| Toei | TrainType | 8 |  | 2.9 | 0.5 | — | 2019-04-25 |
| Toei | RailDirection | 3 |  | 1.1 | 0.4 | — | 2019-04-25 |
| Toei | Calendar | 72 |  | 112.1 | 3.1 | — | — |
| Toei | BusroutePattern | 757 |  | 3,117.8 | 375.0 | — | 2026-09-03 |
| Toei | BusstopPole | 3,690 |  | 5,619.0 | 438.4 | — | 2026-09-25 |
| Toei | BusTimetable | 1,000 | 疑い | 8,177.3 | 338.6 | — | 2026-09-25 |
| Toei | PassengerSurvey | 119 |  | 105.4 | 7.8 | — | 2025-09-29〜2026-01-05 |
| Toei | RailwayFare | 1,000 | 疑い | 540.9 | 12.3 | 2019-10-01 | 2023-03-18 |
| Toei | BusroutePatternFare | 1,000 | 疑い | 861.7 | 25.0 | — | 2026-08-31 |
| Toei | BusstopPoleTimetable | 1,000 | 疑い | 16,908.6 | 386.3 | — | 2026-09-25 |
| TokyoMetro | TrainInformation | 10 |  | 5.7 | 0.8 | — | 2026-10-13 |
| TokyoMetro | Railway | 10 |  | 49.8 | 8.7 | — | 2024-06-27〜2025-05-29 |
| TokyoMetro | Station | 186 |  | 222.2 | 23.2 | — | 2022-03-15〜2025-05-29 |
| TokyoMetro | StationTimetable | 704 |  | 38,610.0 | 2,018.5 | 2026-03-14〜2026-09-19 | 2026-03-16〜2026-09-24 |
| TokyoMetro | TrainTimetable | 1,000 | 疑い | 2,305.1 | 85.3 | 2026-03-14〜2026-09-19 | 2026-03-16〜2026-09-24 |
| TokyoMetro | TrainType | 12 |  | 4.3 | 0.6 | — | 2022-02-24 |
| TokyoMetro | RailDirection | 17 |  | 6.6 | 0.8 | — | 2022-02-24 |
| TokyoMetro | PassengerSurvey | 147 |  | 122.2 | 8.5 | — | 2026-07-03 |
| TokyoMetro | RailwayFare | 1,000 | 疑い | 566.8 | 17.0 | 2023-03-18 | 2023-03-18 |
| TokyoMonorail | Railway | 1 |  | 0.4 | 0.3 | — | 2024-06-27 |
| TokyoMonorail | Station | 2 |  | 0.9 | 0.3 | — | 2024-03-29 |
| Tokyu | Railway | 6 |  | 2.2 | 0.5 | — | 2024-06-27 |
| Tokyu | Station | 27 |  | 10.6 | 1.1 | — | 2023-03-18〜2024-03-27 |
| TokyuBus | BusroutePattern | 747 |  | 1,393.2 | 96.4 | — | 2026-10-01 |
| TokyuBus | BusstopPole | 3,044 |  | 3,280.6 | 221.5 | — | 2026-10-01 |
| TokyuBus | BusTimetable | 1,000 | 疑い | 2,776.1 | 121.7 | — | 2026-10-01 |
| TokyuBus | BusstopPoleTimetable | 1,000 | 疑い | 16,770.7 | 560.5 | — | 2026-10-01 |
| ToyoRapid | Railway | 1 |  | 0.4 | 0.3 | — | 2024-06-27 |
| ToyoRapid | Station | 3 |  | 1.3 | 0.4 | — | 2023-03-18〜2024-03-29 |
| YokohamaMunicipal | TrainInformation | 2 |  | 0.9 | 0.4 | — | 2026-10-13 |
| YokohamaMunicipal | Train | 22 |  | 17.2 | 1.4 | — | 2026-10-13 |
| YokohamaMunicipal | Bus | 236 |  | 242.3 | 20.9 | — | 2026-10-13 |
| YokohamaMunicipal | Railway | 2 |  | 7.0 | 1.4 | — | 2024-06-27 |
| YokohamaMunicipal | Station | 42 |  | 40.7 | 3.6 | — | 2024-03-13〜2024-06-27 |
| YokohamaMunicipal | StationTimetable | 160 |  | 6,056.3 | 313.1 | 2025-11-01 | 2025-11-04 |
| YokohamaMunicipal | TrainTimetable | 1,000 | 疑い | 5,143.8 | 172.2 | 2025-11-01 | 2025-11-04 |
| YokohamaMunicipal | TrainType | 2 |  | 0.7 | 0.3 | — | 2020-03-03 |
| YokohamaMunicipal | Calendar | 47 |  | 63.1 | 2.6 | — | — |
| YokohamaMunicipal | BusroutePattern | 1,000 | 疑い | 7,412.2 | 888.5 | — | 2026-07-27 |
| YokohamaMunicipal | BusstopPole | 2,514 |  | 4,439.5 | 368.9 | — | 2026-07-27 |
| YokohamaMunicipal | BusTimetable | 1,000 | 疑い | 5,389.7 | 329.7 | — | 2026-07-27 |
| YokohamaMunicipal | PassengerSurvey | 42 |  | 77.2 | 6.8 | — | 2026-07-03 |
| YokohamaMunicipal | RailwayFare | 1,000 | 疑い | 594.0 | 12.0 | 2019-10-01 | 2020-03-03 |
| YokohamaMunicipal | BusroutePatternFare | 1,000 | 疑い | 783.6 | 24.6 | — | 2026-07-24 |
| Yurikamome | Railway | 1 |  | 3.7 | 1.3 | — | 2024-06-27 |
| Yurikamome | Station | 16 |  | 15.8 | 2.1 | — | 2024-06-27 |
| Yurikamome | StationTimetable | 60 |  | 2,248.0 | 70.4 | 2025-10-18 | 2026-02-25 |
| Yurikamome | TrainType | 1 |  | 0.3 | 0.2 | — | 2020-03-27 |
| Yurikamome | RailwayFare | 240 |  | 140.8 | 3.4 | 2019-10-01 | 2020-03-27 |

### 2-3. operator で絞らない問い合わせ(operator=*)

| 種類 | 件数 | 打ち切り | 生 KB | gzip KB |
|---|---:|---|---:|---:|
| TrainInformation | 21 |  | 11.1 | 1.4 |
| Train | 101 |  | 73.8 | 5.9 |
| Bus | 583 |  | 594.7 | 59.8 |
| Railway | 94 |  | 121.5 | 19.6 |
| Station | 720 |  | 579.9 | 55.9 |
| StationTimetable | 1,000 | 疑い | 37,848.4 | 1,999.1 |
| TrainTimetable | 1,000 | 疑い | 2,101.3 | 77.3 |
| TrainType | 31 |  | 11.0 | 1.1 |
| RailDirection | 29 |  | 10.6 | 1.2 |
| Calendar | 172 |  | 202.8 | 5.9 |
| BusroutePattern | 1,000 | 疑い | 7,020.6 | 847.8 |
| BusstopPole | 10,000 | 疑い | 12,734.2 | 1,023.9 |
| BusTimetable | 1,000 | 疑い | 5,298.5 | 327.8 |
| PassengerSurvey | 355 |  | 345.1 | 26.3 |
| RailwayFare | 1,000 | 疑い | 582.6 | 13.2 |
| BusroutePatternFare | 1,000 | 疑い | 783.6 | 24.6 |
| BusstopPoleTimetable | 1,000 | 疑い | 19,402.5 | 515.4 |

## 3. API の性質(実測・2026-10-13 夜)

| 項目 | 実測 | 取得器の扱い |
|---|---|---|
| 1 応答の上限 | 多くの種類で 1,000 件。`BusstopPole` は絞らない問い合わせで 10,000 件ちょうど(operator ごとは最大 4,860 件で打ち切りなし) | 1,000 の倍数ちょうどを「打ち切りの疑い」とみなす(`odpt_rt.is_capped`) |
| カンマの OR | 試した 11 の欄(`owl:sameAs`・`odpt:operator`・`odpt:railway`・`odpt:station`・`odpt:fromStation`・`odpt:calendar`・`odpt:railDirection`・`odpt:busroutePattern`・`odpt:fromBusroutePattern`、バスの在線の `odpt:busroute`・`odpt:busroutePattern`)はすべて、2 値の OR の件数が 1 値ずつの和と一致した | 束で問い合わせる欄の表 `odpt_static.OR_KEYS` |
| OR の値の数 | 10 個まで受け、11 個で HTTP 400(`owl:sameAs`・`odpt:busroutePattern`・`odpt:busroute`・`odpt:station` で確かめた。黙って 0 件にはならない) | 束は 10 個まで(`OR_MAX_VALUES`) |
| ダンプの口 `odpt:<種類>.json` | `dataodpt.blob.core.windows.net` への転送 | 追わない。使うならドメインの許可が要る(§8) |
| `dct:issued` | 駅の時刻表・列車の時刻表・鉄道の運賃だけが持つ。他の種類は `dc:date` だけ | `--check` は `dct:issued` の最大を比べ、同じなら `dc:date` の最大を比べる |
| 応答の時間 | 最長は東京メトロの駅の時刻表(704 件・38.6 MB)の 14.3 秒。都営のバスの運賃は 1,000 件(0.86 MB)で 11.2 秒 | 版の取得は `--timeout 120` を勧める |
| 運行情報の `@id` | 3 回の取得で変わらなかった(8 本とも「変化なし」になった) | 変化分だけの比べは `dc:date` と `dct:valid` だけを除く(`DEDUPE_IGNORE_KEYS`) |

## 4. 取得器の変更(`tools/realworld_fetch/`)

| ファイル | 変更 |
|---|---|
| `common.py` | 別ホストへの転送を拒む口(`same_host_only`・`CrossHostRedirect`。ネットの出口は `_urlopen` の 1 点のまま)・`write_json_gz`(書く直前に `scrub`・見出しの時刻 0・一時ファイルから置き換え)・`read_json_any`(`.json` と `.json.gz`)・`odpt_static` の出典の行 |
| `odpt_rt.py` | オープン枠は `OPEN_RT_OPERATORS`(§A の 6・2・3 社)× 3 種類を絞らず保存。チャレンジ枠は `RAILWAYS` のチャレンジの行だけ(運行情報は作品の 3 線に絞る・JR の在線は 3 線を 1 ファイルに)。保存名は `<種類>_<operator>_<HHMMSS>.json.gz`(チャレンジ枠は `<operator>-challenge`)。間隔の表 `CADENCE`(仮の値 300 秒)と `_last_fetch.json`。変化分だけ `DEDUPE`(既定は運行情報だけ)。0 件の応答はファイルを作らない。バスの在線が打ち切られたら系統で 10 個ずつに分けて取り直す。job ごとに例外を閉じ込める。`README_TEXT` を新しい形に |
| `odpt_static.py`(新規) | 洗い出し `survey`・版の取得 `fetch_version`(打ち切りなら `SPLIT_KEYS` の欄で分け、OR の束は 10 個まで・打ち切られたら半分に)・`--check`(`check`)・`--offline` の計画 |
| `ledger.py` | `--report` に odpt_rt の欠けた時間帯(日ごとの 1 時間の枠・連続した欠け・種類ごとのスナップショット数の実際/期待・打ち切りが残った行の数・期間の合計「欠け X 時間 / Y 日」)とディスクの量(種類ごとの合計と直近 7 日の 1 日あたり・年の見込み)。`odpt_static` の保持の行 |
| `cli.py` | `--source odpt_static`(`--check`・`--survey`・`--operators`・`--static-types`)。`--force` は odpt_rt の間隔を無視する。`--verify` は `.json.gz` も読む。実行の終わりの台帳のレポートは日次のソースを頼んだときだけ。`ROOT_README` を新しい形に。`--source all` は odpt_static を含まない |
| `__init__.py` | `__all__` に `odpt_static` |

実行役が決めた細部(expedient・親の判断で変えられる):

- `CADENCE_SLACK_S = 60`: 経過が「間隔 − 60 秒」以上なら取る(タスクの起動の揺れで 1 回分を飛ばさないため)。
- 変化分だけの保存でも、**日付が変わって最初の取得は必ず保存する**(各日のフォルダだけで、その日の始めの状態が分かるように)。
- 0 件の応答(運行の無い時間帯など)はファイルを作らず、台帳の行に `empty: true` を残す。
- バスの在線が打ち切られたときの取り直し: 系統の一覧は、打ち切られた応答に出た系統と、静的データの最新版の `busroutepattern_<operator>.json.gz` の系統を合わせたもの。版が無いうちは応答に出た系統だけなので、欠けが残りうる(`_meta.split.route_source` に `response-only` と残る)。
- 静的データの打ち切りの分け方で、曜日の値は応答に出た値と、よく使われる 5 つ(`STANDARD_CALENDARS`)を合わせる。応答にも 5 つにも無い曜日は取りこぼしうる。
- 実行の終わりの台帳のレポートを、日次のソース(amedas・wbgt・jma_xml)を頼んだときだけにした。odpt_rt だけの実行(5 分ごと)で毎回台帳を全部読むのと、関係の無い URGENT の行がログに出るのを避けるため。

## 5. 試験

- `tests/tools/test_realworld_fetch_odpt.py`(新規・19 本)。`common._urlopen` を偽の ODPT に差し替え、ネットワークに出ない。中身は (1) オープン枠は絞らず全部・チャレンジ枠は作品の範囲だけ・チャレンジ枠への要求は今の 5 本だけ (2) gzip で書き読み戻せる・`--verify` が `.json` と `.json.gz` の両方を読む (3) 間隔の表で飛ばす・余裕 60 秒・種類ごとの間隔・`--force` (4) 変化分だけ(`unchanged`・`same_as`・中身が変われば保存・日付が変われば保存)・比べの正準化 (5) 欠けた時間帯の数え方(手で作った台帳行で 1 時間の枠の欠け・連続した欠け・失敗だけの枠・最初の日・今日の扱い・古い行のまとめ方) (6) 静的データの版(打ち切り → 路線で分けて全部・OR の束の半分割り・束は 10 個まで)と `--check` の比べ方(保存しない・版に無い operator) (7) 秘密がどの保存物・台帳・ログにも出ない、と、転送の拒否(再試行しない)・`--offline` の要求 0 本・`--report` の 2 つの節・odpt_rt だけの実行で全体のレポートを出さないこと・部品の失敗と job の例外の閉じ込め・バスの打ち切りの取り直し・0 件。
- 結果: 写しで 19 passed。本体へ写した後も、本体のコードに向けて 19 passed。
- 本体への写し: 22:51:58 に 6 本を一度に写した(0.4 秒・本番の実行の合間)。写した直後の `--offline`(venv と、タスクが使う系統の Python 3.12 の両方)は要求 0 本。次の本番の実行(22:55:02)は新しいコードで回り、タスクの結果は 0、保存は `.json.gz` 14 本・合計 約 70 KB(本番のファイルの名前と大きさだけを見た)。

## 6. §D 量の実測と見込み

### 6-1. 1 スナップショットの量(写しの取得器・2026-10-13 22:37・22:41・22:46 の 3 回)

| 種類 | 枠 | ファイル | 件数(3 回) | API の応答 B | 保存の圧縮前 B | gzip B | 圧縮 |
|---|---|---:|---|---|---|---|---:|
| バスの在線 | オープン(3 社) | 3 | 469・434・409 | 481,674・447,401・423,862 | 496,612・461,779・437,840 | 53,148・50,577・47,629 | 9.2 倍 |
| 列車の在線 | オープン(2 社) | 2 | 93・90・92 | 67,963・65,941・67,275 | 74,413・72,343・73,709 | 8,788・8,745・8,771 | 8.4 倍 |
| 列車の在線 | チャレンジ(JR 3 線) | 1 | 56・55・53 | 39,033・38,363・37,136 | 42,960・42,269・40,999 | 4,667・4,636・4,545 | 9.1 倍 |
| 運行情報 | オープン(6 社) | 6 | 21・21・21 | 11,058(各回) | 26,001(1 回目) | 10,494(1 回目) | 2.5 倍 |
| 運行情報 | チャレンジ(2 社・3 線) | 2 | 3・3・3 | 7,495(各回) | 6,514(1 回目) | 3,357(1 回目) | 1.9 倍 |

- 運行情報は 2 回目と 3 回目が 8 本とも「変化なし」で、保存しなかった(台帳の行は残る)。運行情報の 1 ファイルは `_meta`(出典・注意書き)が中身より大きく、圧縮が効きにくい。
- 台帳の行は 1 回 16 行・1 行 平均 559 B。
- 今までの形(渋谷の 9 路線・非圧縮・1 日 576 本): 10-11 は 13.97 MB、10-12 は 14.08 MB(本番のファイルの大きさだけを見た)。

### 6-2. 夜の値から 1 日の平均へ(推測)

- 列車の在線: 本番の JR の在線のファイル(非圧縮)の大きさを時刻ごとに平均すると(10-08・10-09)、`_meta` の分(列車の無い 1〜3 時のファイル約 6 KB)を引いた中身は、1 日の平均が 22 時台の 0.90〜0.91 倍だった。在線は 0.9 倍で見積もる(ファイルの大きさだけを使い、中身は読んでいない)。
- バスの在線: 1 日の形を測っていない。22 時台は日中より少なく(22:17〜22:46 の 30 分で 583 件 → 409 件に減った)、運行の無い 1〜5 時もある。1 日の平均を 22 時台の 2.0 倍(1.5〜3.0 倍)と仮に置く(**推測**。最初の 1 日を回した後に `--report` のディスクの量で実測に置き換える)。
- 運行情報(変化分だけ): 保存は変化した回と日付の変わり目だけ。仮に全体の 10% 以下とする(推測)。

### 6-3. 1 日と 1 年の見込み(gzip 後・台帳を含む・かっこ内はバスの倍率 1.5〜3.0 倍のとき)

| 案 | 運行情報 | 列車の在線 | バスの在線 | MB/日 | GB/年 | ファイル/日 |
|---|---|---|---|---:|---:|---:|
| A 5 分・運行情報だけ変化分(**今の既定**) | 0.4 以下 | 2.3 + 1.2 | 29.1(21.8〜43.6) | 35.6(28.3〜50.1) | **13.0**(10.3〜18.3) | 約 1,750〜2,000 |
| B 10 分・運行情報だけ変化分 | 0.4 以下 | 1.1 + 0.6 | 14.6(10.9〜21.8) | 18.0(14.3〜25.2) | 6.6(5.2〜9.2) | 約 870〜1,000 |
| C 列車の在線だけ 1 分・他は 5 分 | 0.4 以下 | 11.4 + 6.0 | 29.1(21.8〜43.6) | 52.6(45.3〜67.1) | **19.2**(16.5〜24.5) | 約 5,200 |
| (参考)A で変化分の保存をやめる | 4.0 | 2.3 + 1.2 | 29.1 | 39.2 | 14.3 | 約 4,030 |

- 台帳: A は 1 日 4,608 行(2.6 MB)、B は 1.3 MB、C は 10,368 行(5.8 MB)。数字は上の MB/日に入れてある。スケジューラのログ(1 回 数行)は入れていない(A で 1 日 0.1 MB ほど)。
- 列車とバスの在線は毎回中身が変わる(位置と遅延)ので、変化分だけの保存はほとんど効かない(既定で off)。
- 静的データの版は 1 版 約 50〜70 MB(gzip 後・§7 の推測)。ダイヤ改正ごとなので年 1 GB に届かない見込み。

### 6-4. 年 50 GB に収める案(親が決める)

- **案 1(今の既定のまま)**: 3 種類とも 5 分・運行情報だけ変化分。年 約 13 GB(10〜18 GB)。タスクの引数は変えなくてよい。
- **案 2(遅延の日の再現を厚くする)**: 列車の在線(オープンとチャレンジ)を 1 分、運行情報とバスの在線は 5 分。年 約 19 GB(16〜25 GB)。在線のレコードの `dc:date` は問い合わせの 1 分以内の値で、元の更新は 1 分より細かいと見られる(推測)。タスクの繰り返しを 1 分にし、`CADENCE` の `odpt:Train` を 60 にする。1 分ごとの要求(在線 5 本)が ODPT の利用の条件に合うかは確かめていない。
- どちらも 50 GB の半分以下。超えそうになったら、まずバスの在線の間隔を 10 分に延ばす(年 約 5 GB 減る)。
- ファイルの数: 案 1 で年 約 64 万本、案 2 で年 約 190 万本。`--report` のディスクの量はファイルを 1 本ずつ数えるので、年が進むと時間がかかる(案 2 で 1〜2 分の見込み・推測)。

## 7. 静的データの版 1(親が本番の場所へ回す)

- 写しで一部を実取得して、打ち切りの分け方が動くことを確かめた(`<scratch>/rwdev_out/odpt_static/2026-10-13/`)。

| operator | 種類 | 件数 | 要求 | 分けた欄 | 打ち切りが残った区画 | 圧縮前 MB | gzip MB |
|---|---|---:|---:|---|---:|---:|---:|
| 相鉄バス | バスの時刻表(便) | 9,204 | 23 | `odpt:busroutePattern` | 0 | 39.5 | 1.56 |
| 都営 | 列車の時刻表 | 5,600 | 12 | `odpt:railway` → `odpt:railDirection` | 0 | 25.7 | 0.90 |
| 都営 | 鉄道の運賃 | 12,140 | 29 | `odpt:fromStation` | 0 | 6.5 | 0.20 |
| TWR | 13 種類(件数のある 7 種類) | — | 13 | — | 0 | 1.7 | 0.09 |

- 運賃の量を見るために、都営と横浜市のバスの系統 5 本ずつで `odpt:BusroutePatternFare` を引いた: 都営 946 件(系統 1 本あたり 約 190 件)・横浜市 605 件(約 120 件)で、1 本の応答に 5 秒ほどかかった。
- 版 1 の全体の見込み(推測): 要求 約 1,300〜1,700 本・**1〜2 時間**(うちバスの運賃が 30〜50 分)・圧縮前 1.2〜1.5 GB・gzip 後 50〜70 MB。1 つの組で最大 300 MB ほどの応答を手元で組み立てるので、手元のメモリを 1〜2 GB 使う見込み。
- コマンド(リポジトリの根から・PowerShell):

```
$env:PYTHONIOENCODING = "utf-8"
.venv/Scripts/python.exe tools/realworld_fetch/rw_fetch_daily.py --source odpt_static --out-dir data\realworld_live --timeout 120 --retries 2
```

- 運賃を後回しにするなら、1 回目に `--static-types odpt:Railway,odpt:Station,odpt:StationTimetable,odpt:TrainTimetable,odpt:TrainType,odpt:RailDirection,odpt:Calendar,odpt:BusroutePattern,odpt:BusstopPole,odpt:BusTimetable,odpt:PassengerSurvey,odpt:RailwayFare` を付け、2 回目に `--static-types odpt:BusroutePatternFare` を付ける(同じ日なら同じ版のフォルダに入る)。
- 版を取った後の確かめ: `--source odpt_static --check --out-dir data\realworld_live`(版にある組ごとに 1 本・約 120 本)。`_index.json` の `capped_parts` が空でない組は、分けても打ち切りが残った区画。
- バスの在線の打ち切りの取り直しは、この版の `busroutepattern_<operator>.json.gz` の系統を使う。版 1 を取るまでは、打ち切られた応答に出た系統だけで分ける。

## 8. 親がすること・判断待ち

1. **間隔**: 案 1 か案 2(§6-4)。案 1 ならタスクの引数は今のまま(`--source odpt_rt --out-dir data\realworld_live`)。案 2 なら、タスクの繰り返しを 5 分から 1 分にし、`odpt_rt.CADENCE["odpt:Train"]` を 60 にする。
2. **タスクの設定**: 今のタスクは「電池で動いているときは始めない」(`DisallowStartIfOnBatteries`)が有効。PC が電池で動いている間も欠けになる。欠けを減らすなら、この設定を外す。
3. **台帳に書く値**: 間隔(案)・`CADENCE_SLACK_S = 60`・変化分だけの表(運行情報だけ on)・§6-1 の 1 スナップショットの量・§6-3 の見込み(バスの倍率は推測)・最初の 1 日の後に `--report` のディスクの量で実測に置き換えること。
4. **最初の 1 日の後**: `.venv/Scripts/python.exe tools/realworld_fetch/rw_fetch_daily.py --report --out-dir data\realworld_live` で、欠けた時間帯(「欠け X 時間 / Y 日」)・種類ごとのスナップショット数・「1,000 件の打ち切りが残った行」・ディスクの量(運行情報・在線・バスの MB/日と年の見込み)を見る。バスの在線の昼の件数が 1,000 件に届くか(都営)もここで分かる。
5. **昼の洗い出し**: 列車とバスの在線は夜の照会なので、昼に提供のある operator が増えるかを確かめる: `--source odpt_static --survey --static-types odpt:TrainInformation,odpt:Train,odpt:Bus --out-dir data\realworld_live`(96 本)。増えたら `odpt_rt.OPEN_RT_OPERATORS` に足す。
6. **静的データの版 1**: §7 のコマンド。`odpt:BusstopPoleTimetable` を版に入れるか(今は入れていない)。
7. **ダンプの口**: 静的データをダンプの口(1 種類 1 ファイル)で取るなら、転送先の `dataodpt.blob.core.windows.net` の許可が要る(ユーザーの判断)。許可が無い今は検索の口を分けて取る。
8. **台帳の大きさ**: odpt_rt の台帳の行は案 1 で年 約 170 万行・約 1 GB になる。`--report` は台帳を全部読むので、数か月で遅くなり、メモリも使う。月ごとに台帳を分けるなどの手当ては、まだしていない(判断待ち)。

## 9. できなかったこと・注意

- 1 日の量の実測はまだ(夜の 3 回だけ)。バスの倍率は推測。最初の 1 日の後に親が `--report` で見る。
- 列車とバスの在線の operator の表は夜の照会から作った(昼に増えるかは §8 の 5)。
- ODPT の「カタログ」(CKAN)は許可の一覧の外なので見ていない。洗い出しは API の `odpt:Operator` と、種類ごとの問い合わせで行った。
- 1 分ごとの取得が ODPT の利用の条件(要求の頻度)に合うかは確かめていない。
- 本番の 5 分ごとの実行は止めていない。写した直後の最初の実行で、`odpt_rt/README.md` と出力の根の `README.md` が新しい文に書き換わり、`odpt_rt/_last_fetch.json` が作られる。古い形のファイル(`train_<HHMMSS>.json` など)はそのまま残る。
