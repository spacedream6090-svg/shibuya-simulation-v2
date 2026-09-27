# W6 再生成 段 1a — 生タグ(2026-09-28)の取り込みと版の台帳(第281・2026-09-28)

> **状態: 確定**。`data/world/v2` を再生成した(`python -m shibuya.build.run --out data/world/v2 --data data --keep-stage W17`)。旧資産は `data/world/v2_pre20260928/`(gitignore 下)に退避済み。段 1a の問い Q1〜Q4 は親が決めた(§9)。
> 正典: [実装アジェンダ](../../../design/v2-w6-regen-implementation-agenda.md) §1 / [趣味の affordance 対応表](../../../design/v2-hobby-affordance-map.md) §6・§7 / 手順 [w6_regen_measure.py](w6_regen_measure.py)。
> 計測の作法: mock 5,000 体・seed 1・1 シミュ日。**mock は振る舞いのモデルではない**(書式と決定論を通す配管)。

## 0. 結論(4 行)

1. **既定 checkpoint の final は 15 腕とも 1 本も動かない**(現行 7+語彙 v3 の活動層 off 1+旧 6+golden の帰無腕 1)。呼数・購入・食事・行為の分布(JSD 0)も同じ。**D-96 の予想「既定 checkpoint 6 種が動く」は外れた**(§9 Q4)。
2. 動くのは **tick 1079(17:59)の checkpoint の world_hash だけ**(agents_hash は全 tick で同一)。原因は **W7 の 1 行=Jazz bar 琥珀**(subcat `club` → 営業 17:00 → 22:00)。琥珀は購入先の規則(セル内の最小 id の POI)で選ばれないので体の状態は動かず、22 時に両方とも開いて世界の状態も一致に戻る。**W7 だけを差し替えた世界で再現する**(§6)。
3. 2026-09-28 の文書そのものは**実行時に効く差を 1 つも足さない**(W7/W14 は 2026-09-07 の 2 文書だけの改訂とバイト一致)。足したのは W6 の `subcat` 列だけで、エンジン(engine/perception/world)はこの列を読まない。
4. W17 は **v2 の凍結資産のまま**(md5 `3113e9ba7abb`・ヘッダもバイト不変)。ビルド道具に「凍結段を保つ口」`--keep-stage` と上書きの安全弁を足した(§10)。

## 1. 入力(Overpass 3 文書・アジェンダの表を写し、md5 を再計算して一致)

| ファイル | クエリの要点 | 件数 | md5(再計算 ✓) | osm_base |
|---|---|---|---|---|
| `poi_tags_overpass_20260928.json` | amenity/shop/leisure/tourism/office/craft/healthcare の node/way/relation・`out center;` | 3,516(node 2,999・way 510・relation 7) | `2b4723293e1d5e633d97516c732b0eb2` | 2026-09-27T17:22:36Z |
| `road_names_overpass_20260928.json` | highway 10 種の way・`out tags geom;`(段 1c で使う・本段は読まない) | 1,328 way | `a918465a4f557be0dffe53f2ec74b662` | 2026-09-27T17:20:36Z |
| `bus_stops_overpass_20260928.json` | バス停 3 種・`out center;`(本段は読まない) | 129 node | `0c7428c35ec7b81cc0d5bd0702ca91ea` | 2026-07-24T11:04:51Z |

## 2. 生タグの取り込み(W6 1.1.0 → 1.2.0)

- 優先順: **2026-09-28 の文書 → 2026-09-07 の 2 文書**(`poi_opening_hours_…`・`street_features_…`)→ v8 凍結 subcat → 名前一致(expedient・既定 ON=D-97 ①)。
- 重ね方: **要素単位で新しい文書が勝つ**(`poi_class.tag_index_by_priority`)。新旧に同じ要素があれば新のタグ一式を採り、旧のキーを混ぜない。新に無い要素だけ旧で埋める。
- 新旧の比較(W6 notes `poi_raw_tags_new_vs_old`・v8 の POI 2,337 に対して):

| 一致 | 件数 |
|---|---|
| 新の文書に一致 | 2,259 |
| 旧だけに一致(新に出ない) | 1(美竹公園 `leisure=park`=旧のタグで park のまま) |
| どちらにも無い | 77(うち `poi_patch` 由来 10) |
| 新旧の両方に一致 | 1,888 |
| うちタグ一式が違う | **2**(タリーズコーヒーの名前・住所・営業時間の表記/青山学院大学の多言語名・住所) |
| うち subcat の 4 キーが違う | 0 |
| うち subcat が動いた | **0** |

→ 「要素単位で新」「キー単位で重ねる」「subcat 単位で新→旧に落ちる」の 3 通りの重ね方は、**このデータでは同じ subcat を返す**(差 0 件を実測)。

## 3. subcat の変化(cat は 1 件も動かない)

### 3-1 現行資産(W6 1.0.0=v8 の凍結 subcat だけ)→ 再生成後(1.2.0)

subcat の付いた POI **255 → 413**(158 件が変化・全部「無し → 有り」か語の付け替え)。

| cat | 変化 | 件数 |
|---|---|---|
| leisure | 無し → park 27・gym 6・sports_centre 4 | 37 |
| shop | 無し → sports_shop 27・hobby 12・music_shop 12・books 10・musical_instrument 8・stationery 7・florist 5・bicycle 4・video_games 3・photo 2・art_supply 1 | 91 |
| hall | 無し → theatre 10・events_venue 7 | 17 |
| attraction | 無し → museum 7・gallery 3 | 10 |
| service | 無し → library 2 | 2 |
| nightlife | 無し → club 1(Jazz bar 琥珀・`amenity=nightclub`=D-97 ⑤ タグどおり) | 1 |

### 3-2 そのうち 2026-09-28 の文書が足した分(2026-09-07 の 2 文書だけの改訂 393 → 413)

| cat | 変化 | 件数 |
|---|---|---|
| hall | 無し → theatre 7(co-ba・Galaxy 銀河系・ヨシモト∞ホール・ヨシモト∞ドーム・WWW・表参道GROUND・NHKホール)/ 無し → events_venue 6(東京カルチャーカルチャー・event lounge warp・Bellesalle Shibuya Garden・金王橋広場・シェアビズ渋谷blossom・BLOOM GATE)/ music_venue(名前)→ events_venue 1(代官山LOOP・`amenity=events_venue`)/ music_venue(名前)→ theatre 1(渋谷公会堂・`amenity=theatre`) | 15 |
| attraction | 無し → museum 2(東京アニメセンター・ストークビル道玄坂)/ 無し → gallery 1(visionary arts) | 3 |
| leisure | 無し → gym 2(Taozen `fitness_centre`+`sport=yoga`・TIP.X)/ 無し → sports_centre 1(Mammut)/ gym(名前)→ sports_centre 1(猿楽トレーニングジム・`leisure=sports_centre`) | 4 |
| service | 無し → library 1 | 1 |

出所の内訳: osm_tag 274 → **405**・frozen 98 → **5**・name 21 → **3**(名前一致が効くのは 3 件だけになった)。

### 3-3 W6 のゲート(本番)

| ゲート | 値 | 期待 | 判定 |
|---|---|---|---|
| `poi_subcat_tag_vs_frozen_mismatch` | 0 | 0 | PASS(規則の移植は壊れていない) |
| `poi_subcat_park` | 27 | 27 | PASS(美竹公園は旧の文書で park) |
| `poi_subcat_topcat_conflict` | 3 | **3**(第281 Q1 (a)) | PASS |
| `poi_subcat_topcat_conflicts_are_the_reviewed_ones`(新) | true | true | PASS(中身が §9 Q1 の見直し候補 3 件と同じ) |
| `poi_hall_unclassified`(新) | 1 | 1 | PASS |
| `poi_attraction_unclassified`(新) | 2 | 2 | PASS |
| `poi_leisure_unclassified`(新) | 1 | 1 | PASS |
| `poi_subcat_total` | 413 | — | 報告 |
| `poi_catsub_pairs_in_closure` | true | true | PASS |

未分類 hall 14 → 1・attraction 5 → 2・leisure 4 → 1。残りは §9 Q3 の空欄。

## 4. build_hash と段階ごとの出力

| | build_hash |
|---|---|
| 前: 正典 `build_manifest.json`(2026-09-09・**W17 v1 1.2.0 のヘッダで組んだ古い値**=昇格後の W17 v2 と食い違っていた) | `4acb4eb349a5a810507d3362d523c5c3df35945499f6cb812c394595cf22582e` |
| 前: 現行のヘッダ(W17 v2 2.0.0 を含む)から同じ規則で組み直した値 | `dcdbc2ee70e88990f66644bc8c61886c5a52e6fc077fc1dc9ad85b369e2e726c` |
| リハーサル(隔離先・W17 を除いて再構築・`build_manifest.partial.json`・W17 は前回のヘッダ) | `590d3783899afc202469458a3323dfd58dfec696e24bb1025ba782d7fbb299de` |
| **後(本番・`--keep-stage W17`・正典 `build_manifest.json`・`kept: ["W17"]`・2 回でバイト一致)** | **`75b264cbf941b291d8a4889f4a9433fc27d3dc704509b6947ff2bdfbfad92c2c`** |

**リハーサルの `590d3783` との関係**: どちらも「W17 の凍結ヘッダ(v2)を足した全 21 段階」の値で、W0〜W18 の出力はバイト一致(W19 の `partial_build_hash_w0_w18` は両方 `36d694b2…`)。違うのは W19・W20 の出力だけで、理由は §9 Q1 の決定で **W6 のヘッダ**(ゲートの期待値 0 → 3・ゲート 1 本と notes の追加)が変わったこと: ① W18 の `input_hash`(全ヘッダのバイト)が変わる → W19 の `stage_digests` が変わる ② W20 の受入パックのゲート表(W6 の FAIL → PASS・202 → 203 ゲート)が変わる。

| 段階 | 出力の変化(前=退避した資産 → 後) | 理由 |
|---|---|---|
| W0〜W5・W9〜W13 | なし(現行コードで再現) | — |
| W6 | `w6_poi.parquet` のみ(sha256 `cf38443a…`・md5 `da271a3cfcc4`)。`w6_org` は同一 | subcat 列(§3) |
| W7 | 5 行(sha256 `e904d8e6…`・md5 `289fae75518a`) | **4 行はコードの先在差**(第203 の条文引用の訂正=`law_cap_rule` の文だけ・クラブセガ/ハイテクランド/ガイア/アドアーズ)+ **1 行が W6 由来**(Jazz bar 琥珀: 営業 17:00-29:00 → 22:00-29:00・価格帯 mid → high・`law_cap_applied` false → true) |
| W8・W15・W16 | なし(入力ハッシュだけ変わる) | 読む列が変わらない |
| W14 | 凍結文 2,302 → **2,301**(sha256 `ad5e304c…`・md5 `01a5565ebe39`)。琥珀の行が落ちる=プロンプトが「夜間営業の飲食店・中程度・17時から」→「ナイトクラブ・高め・22時から」に変わり、凍結済みの応答が検証を通らない → renderer の合成文へ | W6+W7 の 1 行 |
| W17 | **保った**(`--keep-stage W17`)。`w17_schedule.parquet` md5 `3113e9ba7abb`・`W17.header.json` とも退避した資産とバイト一致 | §10 |
| W18・W19・W20 | 監査の出力(`wc_reverse_index` の `unmapped_declarations`・W19 の資産表に新文書・受入パック) | 上流のヘッダの差 |

- 本番の出力はリハーサルと W0〜W18 でバイト一致(W6/W7/W14 の sha256 を突き合わせ済み)。
- 先在の FAIL(前後で同一・本段で増減なし)=build の終了コード 1 の理由: W9 `shadow_bytes_per_day_le_10mb`(12,842,624)・W10 `primary_secondary_sections_matched`(0/202)・W10 `calibration_max_abs_residual_db`(7.3=段 1c の対象)。
- `data/world/v2/build_manifest.partial.json`(2026-09-09 の W17 v1 部分ランの残り)は今回のランでは書き換わらない=古いファイルとしてそのまま残っている。

## 5. checkpoint 6+6 種(+golden)の前後(mock 5,000・seed 1・final の先頭 8 桁・本番資産で計測)

| 腕 | CLI の旗 | final 前 | final 後 | tick 1079 前 → 後 | 呼数 前/後 | 購入/食事 |
|---|---|---|---|---|---|---|
| 語彙 v3 既定 | (旗なし) | `02bd0312` | **`02bd0312`** | e68c03f7 → 7367e6f5 | 36,460 / 36,460 | 1,866/2,035(同) |
| 語彙 v3・活動層 off | `--activity off` | `fb166cc7` | **`fb166cc7`** | f77cf2a6 → 68aa48d0 | 32,808 / 32,808 | 1,993/2,023(同) |
| v1 既定 | `--vocab-version v1` | `2f3969cf` | **`2f3969cf`** | 3682ea4e → 82214981 | 33,090 / 33,090 | 1,497/0(同) |
| 読み口 v2.1 | `--vocab-version v1 --derive-rule v2.1` | `d642b6af` | **`d642b6af`** | d5ef8988 → f1834449 | 30,616 / 30,616 | 1,526/0(同) |
| 語彙 v2 | `--vocab-version v2` | `1d181059` | **`1d181059`** | 6aa97f78 → 70e1cb88 | 33,274 / 33,274 | 1,423/1,351(同) |
| edge | `--vocab-version v1 --geometry edge` | `7b12069b` | **`7b12069b`** | c111ef5a → 016331eb | 31,583 / 31,583 | 1,438/0(同) |
| edge+語彙 v2 | `--vocab-version v2 --geometry edge` | `e96d75e3` | **`e96d75e3`** | 1da72b18 → 51eae3c7 | 32,121 / 32,121 | 1,357/1,258(同) |
| edge+plateau | `--vocab-version v1 --geometry edge --area-source plateau` | `4a66de4b` | **`4a66de4b`** | 85cfef06 → 7bad89a3 | 32,491 / 32,491 | 1,419/0(同) |
| 旧 v1 既定 | 上+`--report-precondition off` | `ba01bd0b` | **`ba01bd0b`** | aad9c915 → b5efc24f | 33,090 / 33,090 | 同 |
| 旧 読み口 v2.1 | 〃 | `4fb0f2ec` | **`4fb0f2ec`** | a477fb10 → 18c190db | 30,616 / 30,616 | 同 |
| 旧 語彙 v2 | 〃 | `9c16f77a` | **`9c16f77a`** | 5c32f717 → 1ab680e1 | 33,274 / 33,274 | 同 |
| 旧 edge | 〃 | `9a9049f5` | **`9a9049f5`** | 7f40a6f6 → 2d44a911 | 31,583 / 31,583 | 同 |
| 旧 edge+語彙 v2 | 〃 | `6d6b1cda` | **`6d6b1cda`** | 2011bb97 → 2d881903 | 32,121 / 32,121 | 同 |
| 旧 edge+plateau | 〃 | `1c8370fb` | **`1c8370fb`** | 3e430535 → 5d1f3bd9 | 32,491 / 32,491 | 同 |
| golden 帰無腕(`W17_GOLDEN`) | `plan_executor=False`・`report_precondition=False` | `b4ad8140` | **`b4ad8140`** | 8797c4dc → 39dec765 | 41,072 / 41,072 | 1,169/0(同) |

- tick 359・719・1439 は 15 腕とも前後一致。1079 の差は **world_hash だけ**(agents_hash は一致)。本番資産の 15 腕はリハーサルと全 tick・行為の計数まで一致。
- 「前」の 15 本は記録済みの値(二層の記録 §0・`W17_GOLDEN`)を**全部再現**した(現行資産の写しで計測)。
- golden(`tests/engine/test_presence_executor.py` の `W17_GOLDEN`=final と呼数・`tests/engine/test_presence_derive_v2.py` の `REAL_GOLDEN`=W17 だけで決まる)は**値が変わらないので編集していない**。`tests/c8/test_ablations_*` の表は腕の定義の sha256 で世界に依存しない。tick 1079 の値を固定したテストは無い(grep 済み)。
- manifest の `frozen_sources` は `w14_signage.parquet` の sha256 が `f2439da6…` → `ad5e304c…`(`w15_cell_static.parquet` は不変)。
- 全桁: [summary_before.json](summary_before.json) / [summary_after.json](summary_after.json) / [compare.json](compare.json)。

## 6. 動く(動かない)理由の切り分け(差分の計数+資産を 1 つずつ差し替えた mock)

**1 行**: エンジンは `w6_poi` の `subcat` を読まない(読むのは poi_id・名前・cat・座標・セル)ので、subcat の差は W7 の 1 行(Jazz bar 琥珀の営業 17→22 時)を通してだけ効き、その店が購入先に選ばれないため 17:00〜22:00 の `open_now` 1 ビットだけが tick 1079 の world_hash に出る。

| 経路 | 計数 | checkpoint への効き |
|---|---|---|
| subcat → 場所語の写像(`CAT_TO_PLACE`/`SUBCAT_TO_PLACE`) | 写像が変わる POI 28(娯楽施設 → 公園 27・飲食店 → 娯楽施設 1)。ただしこの表は **W17 の構築(開店率)でしか使わない**=W17 は保った | 0 |
| eatery(`hash_free_cat_code(cat)==1`) | 変化 0(cat は不変)=食事の成立 同一 | 0 |
| W17 の場所解決 | W17 は同一(md5 `3113e9ba7abb`)・実行時は subcat を読まない | 0 |
| W7 の営業窓・価格 | 実行時に効く列が変わった行 **1**(Jazz bar 琥珀)。コード先在差の 4 行は `law_cap_rule` の文だけ | tick 1079 のみ |
| W14 の凍結文 | 1 行落ちる(mock は文面を読まない) | 0 |

mock での差し替え(現行資産に後の資産を 1 つずつ入れる・隔離先で計測):

| 世界 | v1 既定 359/719/1079/1439 | v3 既定 1079 |
|---|---|---|
| 前(現行資産) | d2752886 / 4ba1528d / 3682ea4e / 2f3969cf | e68c03f7 |
| 前+W7(コード先在差だけ・W6 は旧で再構築) | 同じ | e68c03f7 |
| 前+W6+W14(後の資産) | 同じ | e68c03f7 |
| **前+W7(後の資産=先在差+琥珀)** | d2752886 / 4ba1528d / **82214981** / 2f3969cf | **7367e6f5** |
| 後(全部) | d2752886 / 4ba1528d / **82214981** / 2f3969cf | **7367e6f5** |

補足: 琥珀はセル 45(POI 17 件)にあり、最小 id は 136(shop)。17:55 の開店状態は前 True / 後 False(22:05 は両方 True)。2026-09-07 の 2 文書だけで W6 を作っても W7/W14 のバイトは後と一致する=**琥珀の `club` は 09-17 の改訂の時点で入っていた差**で、2026-09-28 の文書は実行時の差を足していない。資産の差の計数は [asset_diff.json](asset_diff.json)(退避した資産と本番資産の比較・リハーサルと同じ値)。

## 7. mock 5,000 の行動分布の前後(JSD)

15 腕とも **JSD = 0**(LLM 由来の行為・エンジン継続を含む全行為・起床条件の 3 通りすべて)。`action_usage` の差分は空。

## 8. 触っていないもの

語彙・契約表・B0 文面・W7 の営業窓の規則(`CATEGORY_DEFAULTS`・D-97 ④)・価格(`hash_free_cat_code`)・W17(v2 の凍結資産を保った)・段 1b(eatery 切替口)・段 1c(W10 道路名)・golden の表。`SUBCAT_TAG_VALUES` に値を足していない(D-97 ⑦ の承認済みの表のまま)。

## 9. 決定(親・第281)と D-96 の訂正・空欄

- **Q1 = (a)**: `EXPECTED_SUBCAT_TOPCAT_CONFLICT = 3`。生タグの subcat の親 cat が v8 の cat と矛盾する 3 件は、現行どおり **subcat を捨てて cat を守る**。**cat の見直し候補**(次の W6 改訂で D-97 と同じ形で判断・cat は動かさない方針は保つ)として `w6_poi_org.TOPCAT_CONFLICT_REVIEW` と W6 notes `poi_subcat_topcat_conflicts`(+`_note`)に記録し、ゲート `poi_subcat_topcat_conflicts_are_the_reviewed_ones` で中身を固定した:

  | poi_id | 名前 | v8 の cat | 生タグ | タグの subcat(親 cat) | 備考 |
  |---|---|---|---|---|---|
  | `p_n4841478823` | Taito Station | landmark | `leisure=amusement_arcade` | arcade(leisure) | v1 の cat 規則を今のタグに掛けても leisure |
  | `p_n10296729118` | Hailey'5 Cafe | food | `amenity=internet_cafe` | net_cafe(nightlife) | 今のタグの cat 規則でも nightlife |
  | `p_w138871334` | 記念館(大学体育館) | school | `building=university`+`leisure=sports_centre` | sports_centre(leisure) | 今のタグでも cat 規則は school=v1 の cat 規則と subcat 規則の食い違い |

- **Q2 = (b)**: build runner に `--keep-stage` と安全弁を足した(§10)。本番は `--keep-stage W17` で回し、正典の manifest(`kept: ["W17"]`)を書いた。
- **Q3 = 規則を足さない**。空欄(W6 notes `poi_unclassified_target_cats`+`poi_unclassified_note`):
  - hall 1 = 代々木公園陸上競技場(`leisure=stadium`・D-97 ⑦ で stadium は外すと決定済み)
  - attraction 2 = NHKスタジオパーク(`tourism=theme_park`=`SUBCAT_TAG_VALUES` に無い値)・モヤイ像(`p_patch_02`=`poi_patch` 由来で生タグが無い)
  - leisure 1 = T4(`leisure=pitch`+`sport=table_tennis`=無い値)
- **Q4 = D-96 の訂正**: D-96 の予想「W6 再生成で既定 checkpoint 6 種が動く」は**外れた**。final は 15 腕とも不変・動くのは tick 1079 の world_hash だけ(琥珀の営業窓)。因果は W7 だけを差し替えた世界で再現する(§6)。「W14 差 1 本・W15 0・W17 不変」は当たった(W14 は 1 行落ちる)。PENDING 側は親が直す。
- 空欄(本段で埋めていないもの): §9 Q1 の 3 件の cat の正否(OSM のタグが現地と合っているか)・Q3 の 4 件の業態・`poi_patch` 由来 10 件の生タグ(OSM 要素ではない)。

## 10. 道具の変更: `python -m shibuya.build.run` の `--keep-stage` と安全弁(第281 Q2 (b))

- `--keep-stage <段>`(複数可): その段は再構築せず、ディスク上の出力と既存ヘッダをそのまま採る。何かを走らせる前に、ヘッダが主張する出力が在って sha256 が一致することを確かめる(相対パスは `--out` から・絶対パスはそのまま=W17 v2 の段 2 プロンプトは隔離先 `w17v2_r2/` に在る)。合わなければ終了コード 2。
- 走らせた段+保った段で全段階がそろえば、`build_manifest.json` を**正典として**書き(partial にしない)、`kept: [...]` と `kept_note` を記録する。`--stage` と `--keep-stage` に同じ段を渡すと終了コード 2。
- **安全弁** `PROTECTED_OUTPUTS = {"W17": {"w17_schedule.parquet": ("3113e9ba7abb",)}}`: 走らせる段の出力の md5 が昇格版と一致するときは、`--stage <その段>` を**明示しない限り**上書きを拒否し、何も走らせずに終了コード 2。本番資産で確認済み(`--keep-stage` なしの全段階ランは拒否され、manifest はバイト不変)。W17 を再構築するのは `--stage W17` を明示したときだけ。
- 理由: W17 段(`build/sched/w17_schedule.py`・1.2.0)は `w17_responses*.jsonl`(**v1 の応答 7 本**)を取り込み直すので、`build.run` は昇格済みの W17 v2(`build/sched/trial.py --promote`)を再現できず、全段階ランは v2 を v1 の再取り込みで上書きしていた。
- テスト: `tests/test_build_run_keep_stage.py`(5 本=保った段の出力とヘッダが不変・正典 manifest と `kept`/保つ段の出力がヘッダと合わなければ止まる/`--stage` と `--keep-stage` の重複は usage/安全弁が既定と `--keep-stage` と `--stage` の 3 通りで正しく振る舞う/安全弁の md5 が golden の鍵と同じで、実資産に当たる)。

## 11. 手順(リポジトリの根から)

```
# 退避(トップの資産ファイル全部+acceptance/。w17v2*/trials* などの下位ディレクトリはビルドが触らないので写さない)
#   → data/world/v2_pre20260928/(110 ファイル・3.3 GB・全ファイル cmp 一致)
python -m shibuya.build.run --out data/world/v2 --data data --keep-stage W17
python docs/bench/analysis/w6-regen-2026-09-28/w6_regen_measure.py run --world <前の資産> --out <前の計測>
python docs/bench/analysis/w6-regen-2026-09-28/w6_regen_measure.py run --world data/world/v2 --out <後の計測>
python docs/bench/analysis/w6-regen-2026-09-28/w6_regen_measure.py collect --out <前の計測>   # 後も同じ
python docs/bench/analysis/w6-regen-2026-09-28/w6_regen_measure.py compare --before <前の計測> --after <後の計測> --out compare.json
```

前の計測は現行資産の写し(トップの資産ファイル+`acceptance/`+`street_features_overpass_20260907.json`)で回した(`world/assets.py` は街路施設を資産ディレクトリ → `../../realworld/osm/` の順で探す)。1 腕 13〜20 秒。§6 の差し替えは同じ写しに後の資産を 1 つずつ入れて回した。
