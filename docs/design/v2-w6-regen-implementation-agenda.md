# 実装アジェンダ: Overpass 再取得の取り込み → W6 再生成 → eatery の切替口 → W10 道路名突合(PENDING §2 の 1 段目・第280・2026-09-28)

> **位置づけ**: ユーザー決定(D-96 (a) W6 だけ今すぐ再生成・nightlife (b)・D-97 推奨どおり・D-1 (a) Overpass で道路名を再取得・09-26「生応答をファイル保存し md5 を台帳へ」)の実装手順。**実装役=Opus 5.5 サブ・コミットは親**。細部はここで決め、実装役は本書に無い判断を「問い」として返す(勝手に決めない)。
> **取得(親が 2026-09-28 に実施・読むだけの規律の例外=ユーザー許可 09-26)**: bbox 35.6505,139.6905,35.6685,139.7115。生応答は `data/realworld/osm/`(gitignore 下)に保存し、クエリ全文を `*.query.txt` に、md5・取得日・osm_base を [データ・ライセンス台帳](../data-license-ledger.md) に記録した(第280)。
>
> | ファイル | クエリの要点 | 件数 | md5 | osm_base |
> |---|---|---|---|---|
> | `poi_tags_overpass_20260928.json` | amenity/shop/leisure/tourism/office/craft/healthcare の node/way/relation・`out center;`(タグ+座標) | 3,516(node 2,999・way 510・relation 7) | `2b4723293e1d5e633d97516c732b0eb2` | 2026-09-27T17:22:36Z |
> | `road_names_overpass_20260928.json` | highway=motorway/trunk/primary/secondary/tertiary/unclassified/residential/living_street/pedestrian/service の way・`out tags geom;` | 1,328 way(name か ref あり 396: trunk 44・primary 52・secondary 29・tertiary 199 …) | `a918465a4f557be0dffe53f2ec74b662` | 2026-09-27T17:20:36Z |
> | `bus_stops_overpass_20260928.json` | highway=bus_stop・public_transport=platform+bus=yes・amenity=bus_station・`out center;` | 129 node(highway=bus_stop 127・名前あり 128) | `0c7428c35ec7b81cc0d5bd0702ca91ea` | 2026-07-24T11:04:51Z(ミラー overpass.kumi.systems・本家は混雑で失敗) |

## §0 段(1 commit ずつ・各段に切替口かゲート・親が再実行して検収)

| 段 | 中身 | 既定 checkpoint | 検収の物差し |
|---|---|---|---|
| 1a | 生タグの取り込み(W6 の subcat の一次根拠に `poi_tags_overpass_20260928.json` を足す)+W6 再生成(全段階)+checkpoint 6 種の張り直し+版の台帳 | **動く**(D-96 の宣言どおり) | ゲート全 PASS・build_hash 再現・hall/attraction/leisure の subcat 付与数・W14 差分 1 本の確認・mock 5,000 の checkpoint 6 種 |
| 1b | eatery の切替口 `--eatery {food,place_food}`(既定 food=挙動不変) | 不変 | 既定 checkpoint 不変・place_food 腕で 23 時以降に食事が成立する POI 数(58 → 252 前後) |
| 1c | W10 道路名の突合(D-1 (a)): OSM way の name/ref を W1 辺に写像 → kasyo13.csv と名寄せ → 対応表 → 残差再評価 | W10 は静的騒音場=checkpoint に混ざるなら **動く**(実装役が確認して報告) | 写像率・名寄せ成立率・較正残差(No.61 +5.1/No.75 +7.3 dB)の前後・ゲート 2 本の PASS/FAIL |

## §1 段 1a: 生タグの取り込みと W6 再生成

1. **入力の追加**: `build/geo/w6_poi_org.py` の `INPUT_FILES` と `build/geo/poi_class.py` の生タグ文書に `("realworld","osm","poi_tags_overpass_20260928.json")` を足す。要素キーは既存と同じ `f"p_{type[0]}{id}"`。**優先順**: 新文書(2026-09-28)→ 旧 2 文書(2026-09-07)→ v8 凍結 subcat → 名前一致(expedient・`USE_NAME_SUBCAT_RULES`)。同じ POI に新旧で違うタグがあれば**新を採り件数を notes に**。
2. **D-97 の決めどおり**: ① 名前一致層は ON のまま expedient 宣言 ② 屋上緑地はタグどおり公園 ③ **hall 14・attraction 5・leisure 4 に生タグから subcat を付ける**(`theatre`/`music_venue`/`events_venue`/`museum`/`gallery`/`sports_centre` … 既存の `SUBCAT_TAG_VALUES` で当たらない値が出たら**追加せず問いとして返す**)④ 営業窓は別ラウンド(触らない)⑤ Jazz bar 琥珀はタグどおり club ⑥ 答申の訂正は済 ⑦ タグ選択は承認済。
3. **期待値の更新**: `EXPECTED_SUBCAT_PARK`(27 のまま=変わらないはず・変わったら報告)・hall/attraction/leisure の未分類 0 を新しいゲートに(`EXPECTED_HALL_UNCLASSIFIED = 0` 等・値は実測で確定し notes に根拠)。`EXPECTED_SUBCAT_TAG_VS_FROZEN_MISMATCH = 0` は**維持**(生タグが v8 の subcat と食い違ったら規則の移植が壊れている=問いとして返す)。
4. **再生成**: `python -m shibuya.build.run --out data/world/v2 --data data`(**全段階**・LLM 不要=W14/W15/W17 は凍結資産のまま。D-96 の記述「W14 差 1 本・W15 0・W17 不変」を再構築で確認)。ゲートが落ちたら止めて報告(調整しない)。`build_manifest.json` の build_hash を記録。**旧資産は `data/world/v2_pre20260928/` に退避**(gitignore 下・戻せるように)。
5. **checkpoint の張り直し**: mock 5,000・seed 1 を既定 6 種(現行値: 旗なし v3 `02bd0312`・v1 `2f3969cf`・v2.1 `d642b6af`・vocab v2 `1d181059`・edge `7b12069b`・edge+v2 `e96d75e3`・plateau `4a66de4b`=[二層の記録 §0](../bench/analysis/two-layer-2026-09-27/README.md))+`--report-precondition off` の旧 6 種で再実行し、新しい値を **版の台帳**([w6-regen-2026-09-28/README.md](../bench/analysis/w6-regen-2026-09-28/README.md)=新規)に旧値と並べる。golden の表(`tests/engine/test_presence_executor.py` の `W17_GOLDEN`・`tests/c8/test_ablations_*` の md5)を新値へ。**checkpoint が動く理由を 1 行で説明できること**(POI の subcat が変わる → 場所語の写像・eatery・W17 の場所解決が変わる)。
6. **テスト**: `tests/build_geo/` の W6 テスト(件数・ゲート)・全体 `-m "not gpu and not slow"`(P6 除外)全緑・exit code を隠さない。
7. **記録**: 版の台帳に (i) Overpass 3 文書の md5・日付・件数 (ii) subcat の変化(cat 別・件数)(iii) checkpoint 6+6 種の前後 (iv) build_hash 前後 (v) W14 差分 (vi) mock 5,000 の行動分布の前後(JSD)。

## §2 段 1b: eatery の切替口(D-96 nightlife (b))

- `world/state.py` の `eatery_mask` に切替口: `food`(既定=現行 `cat==food`)/ `place_food`(=`cat==food ∨ (cat==nightlife ∧ subcat ∉ {club, karaoke, sauna, net_cafe})`=W17 の場所語「飲食店」と同じ集合 1,042 件と**一致することをテストで固定**)。価格は動かさない。
- `run_day(eatery=...)`・CLI `--eatery {food,place_food}`・manifest に `eatery` 列。既定 checkpoint 不変(段 1a の新値のまま)。
- 検収: `place_food` 腕の mock 5,000 で 23 時以降に食事が成立する POI 数と食事の成立率の前後。記録は版の台帳 §2。

## §3 段 1c: W10 道路名の突合(D-1 (a))

1. `road_names_overpass_20260928.json`(way の `geom`=座標列と `tags.name`/`ref`/`highway`)を W1 の辺(`w1_edges.parquet`・OSM v8 由来)へ写像: **OSM way id が一致するならそれで、無ければ幾何(辺の中点から way の折れ線までの距離 ≤ 8 m=D-W9 のバッファと同値)**。写像率(名前が付いた辺 / 全辺・klass 別)を出す。
2. 名寄せ: 付いた name/ref と `kasyo13.csv`(道路交通センサス R3 東京都 箇所別基本表・3,335 区間)の路線名を突き合わせ(表記ゆれ=全角/半角・「国道246号」/「246」・「都道」…の正規化規則を明示)、対応表 `edge → センサス区間`を作る。**成立率を報告**。
3. 対応表が立った辺は実測交通量、立たない辺は従来の klass 既定表(expedient・変えない)。較正 7 点の残差(No.61 +5.1 / No.75 +7.3 dB)の前後と、ゲート 2 本(区間突合 0/202 → ?・較正残差)の判定を報告。**残差が悪化したら対応表を既定 OFF(切替口)にして報告**(調整はしない)。
4. W10 の出力が変わると W9/W13 以降の build_hash と、静的騒音場を読む観測(B4 騒音段階)が変わる=checkpoint が動きうる。**段 1a と別 commit**にして差を切り分ける。

## §4 実装役への注意

- CRLF → LF 正規化してから編集(作業木 CRLF・index LF)。絶対パス・ユーザー名を記録に書かない。`data/` の実体はコミットしない(gitignore)。
- 進めてよい範囲=本書の段 1a〜1c。**触らないもの**: 語彙・契約・B0 文面・W7 の営業窓(D-97 ④)・価格・W17。
- 問いが出たら実装を止めずに「問い」として最後にまとめて返す(親が決める)。テストの exit code を隠さない。
