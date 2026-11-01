# 較正側の錨の計器(2-0)

合否は書かない。〔写〕の錨は構築の入力の写しで、差は形だけを見る。「現実に近づいた」と書けるのは holdout の開封(S1)の後だけ。検証側(〔検〕)と〔灰〕は、**gauge の段では**許可の一覧で縛って読んでいない。record の段(エンジンのラン)では、エンジンが前から読む入力を開く(末尾の表。計器はその値を使わない)。

## ラン

| 腕 | commit | final | 呼数 | bridges_count | rules_version | src の差(ファイル数) | 体数 | seed |
|---|---|---|---|---|---|---|---|---|
| mock | 2809c4a | eb759bb4e5be37ec | 63,572 | 552 | 4dda40d8f83d6a3f | 19 | 5000 | 1 |
| classical | 2809c4a | 9988000f869eeea2 | 91,791 | 552 | 4dda40d8f83d6a3f | 19 | 5000 | 1 |

第 18-1 表(〔検〕)と比べた食事時刻の結果の印(計器は比べない・比べる道具の結果に写す): mock=検証可(置き換えの後=既定の食事時刻は W17 v2 の分布・エンジンは検証側の錨を開いていない)・classical=検証可(置き換えの後=既定の食事時刻は W17 v2 の分布・エンジンは検証側の錨を開いていない)

エリアの写像: `area_axes_v0.json`(版 v0・expedient)・面積の帯の自己検査 真・面積[ha] {'central': 9.0, 'northwest': 57.0, 'northeast': 27.0, 'southeast': 14.0, 'southwest': 31.0}

## 腕 mock

拡大係数 ω(種別 → W16 の体数 ÷ 標本の体数): {'0': 76.666, '1': 76.604, '2': 74.523, '3': 76.754, '4': 1.0, '5': 76.747, '6': 76.628, '7': 76.333, '8': 2.146}

### 3-1 在圏のピーク時刻(5〜28 時)

| 列 | ラン(合計・θ1) | θ30 | 連続・θ1 | 正時(v1.3) | 錨1〔写〕計画 | 差[時] | JSD | 錨2〔部〕W12 | 差[時] | JSD | 錨3〔非〕PT c-2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 渋谷駅中心エリア | 9 | 10 | 9 | 10 | 13 | -4 | 0.01679 | — | — | — | 材料待ち |
| 渋谷駅北西エリア | 12 | 12 | 12 | 12 | 13 | -1 | 0.02491 | — | — | — | 材料待ち |
| 渋谷駅北東エリア | 10 | 10 | 11 | 11 | 12 | -2 | 0.02437 | — | — | — | 材料待ち |
| 渋谷駅南東エリア | 9 | 10 | 9 | 10 | 12 | -3 | 0.01727 | — | — | — | 材料待ち |
| 渋谷駅南西エリア | 14 | 15 | 14 | 16 | 12 | 2 | 0.03537 | — | — | — | 材料待ち |
| 5 エリア計 | 11 | 11 | 11 | 11 | 12 | -1 | 0.01759 | 13 | -2 | 0.02792 | 材料待ち |
| 舞台全体 | 10 | 11 | 10 | 11 | 12 | -2 | 0.00035 | 13 | -3 | 0.03688 | 材料待ち |

5 エリアのピークの順(早い順・ラン): central → southeast → northeast → northwest → southwest / 計画: northeast → southeast → southwest → central → northwest。母集団の腕(5 エリア計のピーク): P 11・全員 12。錨 2 の R・I・O = 34,941・1,521,476・1,483,785(β=time_dist_12 の乗車 帰宅・腕 β=合計のピーク 14)。計画で舞台の中に居るがセルが分からない割合(エリアに数えない・舞台には数える): 全体 0.3665・来街の種別 1・それ以外 0.2339。

### 3-2 来街者/居住者の比(1 日単位・30 分・area の写像・ω で戻す)

| エリア | ラン V/Res | ラン W/Res | ラン n(W,Res,V) | 訪日(別の列・ω) | 連続 V/Res | kind 写像 V/Res | 錨2〔写〕計画 V/Res | 錨2 W/Res | 錨1〔写〕W16 W/Res(area) |
|---|---|---|---|---|---|---|---|---|---|
| 渋谷駅中心エリア | 475.3 | 23.81 | [120, 4, 2056] | 12,297 | 433 | 2.499 | — | 31.09 | 23.93 |
| 渋谷駅北西エリア | 26.11 | 10.33 | [685, 63, 1703] | 15,655 | 25.11 | 1.906 | — | 14.15 | 17.15 |
| 渋谷駅北東エリア | 16.46 | 3.294 | [117, 33, 579] | 4,428 | 14.94 | 2.342 | — | 7.069 | 10.34 |
| 渋谷駅南東エリア | 26.68 | 10.72 | [143, 17, 346] | 3,438 | 24.51 | 1.935 | — | 21.09 | 22.2 |
| 渋谷駅南西エリア | 2.462 | 2.605 | [140, 53, 128] | 1,604 | 2.088 | 0.5416 | — | 6.998 | 8.681 |
| 5 エリアの和 | 27.83 | 6.801 | [1205, 170, 4812] | 37,422 | 25.81 | 1.952 | — | 11.37 | 13.85 |

錨 1〔写〕W16 の体数(kind の写像・舞台全体): P′ V/Res 2.377・W/Res 4.922 / P(kind≠7) V/Res 2.319・W/Res 4.515 / 全員 V/Res 3.036。
錨 3〔非〕中核 9 町丁目の昼夜間人口比 14.8(都 第 11 表): W16 の静的な比 18.23(夜 8363・昼 152,454)・ランの比 14.5(居住者 n=114)・計画の比 16.53。写像のセル 133 枚(GL)。
フロア(合否にしない): 来街/勤務 PT 2018 [0.16, 0.27] 対 KDDI 1.66。ランの来街/勤務(5 エリアの和) 4.092。

### 3-3 駅ごとの到着の波(ω で戻す・全員)

| ノード | ラン 割合 | 錨1〔写〕割合 | 差 | ラン ピーク | 錨2〔部〕ピーク | 差[時] | JSD(形) | 計画 割合 | 計画 ピーク | 計画 JSD | 錨3〔非〕 | 錨4〔灰〕 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ext_rail_tokyu_denentoshi | 0.2013 | 0.1942 | 0.0071 | 8 | 8 | 0 | 0.06407 | 0.2034 | 8 | 0.0838 | 材料待ち | 読まない |
| ext_rail_tokyu_toyoko | 0.1255 | 0.1283 | -0.0028 | 9 | 8 | 1 | 0.07923 | 0.1257 | 9 | 0.07808 | 材料待ち | 読まない |
| ext_rail_keio_inokashira | 0.092 | 0.0859 | 0.0061 | 8 | 8 | 0 | 0.06956 | 0.0889 | 8 | 0.08547 | 材料待ち | 読まない |
| ext_rail_jr_yamanote | 0.1889 | 0.1862 | 0.0027 | 8 | 8 | 0 | 0.07351 | 0.1905 | 8 | 0.08676 | 材料待ち | 読まない |
| ext_rail_jr_saikyo_shonan | 0.0408 | 0.038 | 0.0028 | 9 | 8 | 1 | 0.1085 | 0.0404 | 9 | 0.1147 | 材料待ち | 読まない |
| ext_rail_metro_hanzomon | 0.1657 | 0.1717 | -0.006 | 8 | 8 | 0 | 0.06646 | 0.1651 | 8 | 0.07695 | 材料待ち | 読まない |
| ext_rail_metro_fukutoshin | 0.0749 | 0.0734 | 0.0015 | 8 | 8 | 0 | 0.06497 | 0.0751 | 7 | 0.06451 | 材料待ち | 読まない |
| ext_rail_metro_ginza | 0.094 | 0.0831 | 0.0109 | 9 | 8 | 1 | 0.09185 | 0.0935 | 9 | 0.09905 | 材料待ち | 読まない |
| ext_walk_gate | 0.0063 | 0.018 | -0.0117 | 9 | 10 | -1 | 0.1209 | 0.0066 | 9 | 0.2657 | 材料待ち | 読まない |
| ext_road_gate | 0.0106 | 0.0212 | -0.0106 | 9 | 8 | 1 | 0.07848 | 0.0108 | 9 | 0.1214 | 材料待ち | 読まない |
| none | — | — | — | 18 | — | — | — | — | 18 | — | 材料待ち | 読まない |

到着の数(ラン・体の延べ): 7964・計画の到着(ARRIVE の予定): 5582。錨 1 の割合(daily_inflow)と W12 の重みの和の差の最大 0。

### 3-4 勤務の始業の分布(kind 0・2・ω で戻す)

| 列 | n | 平均 | p10 | p25 | p50 | p75 | p90 | :00/:30 の率 | 最頻の 15 分 | 立ち上がり(50%) |
|---|---|---|---|---|---|---|---|---|---|---|
| ラン | 866 | 12:54 | 8:04 | 9:15 | 11:58 | 16:00 | 19:54 | 0.037 | 8:45 | 9:30 |
| 錨1〔写〕第 31 表+lead | 0 | — | — | — | — | — | — | — | — | — |
| 錨2〔写〕W17 v2 勤務の行 | 2281 | 9:16 | 6:59 | 7:50 | 8:35 | 9:34 | 12:15 | 0.0574 | 8:00 | 8:30 |
| 錨5〔写〕W20 暦 1a の約束 | 0 | — | — | — | — | — | — | — | — | — |
| 錨3〔部〕第 8-1 表 仕事 | — | — | — | — | — | — | — | — | — | 8:30 |
| 錨4〔非〕PT c-2 | 材料待ち | — | — | — | — | — | — | — | — | — |

差(ラン − 錨): 錨 1 平均 — 分・p50 — 分・JSD — / 錨 2 平均 218.2 分・p50 203 分・JSD 0.2388 / 立ち上がり(在席の率 対 第 8-1 表) 60 分。対象 2286 体・始まりが取れた 866 体(立ち上がりの行の計画=計画上のセルの在席の率)。
〔3-1〕差(ラン − 錨 5=W20): 平均 — 分・p50 — 分・JSD — / W17 − W20(参考): 平均 — 分・p50 — 分・JSD —。錨 5 の体 0・表に無い体 2286(合否にしない)。

### 感度: エリアの写像 ±50 m

| 膨張 | 渋谷駅中心エリア | 渋谷駅北西エリア | 渋谷駅北東エリア | 渋谷駅南東エリア | 渋谷駅南西エリア | 5 エリア計 | 計 V/Res | 計 W/Res |
|---|---|---|---|---|---|---|---|---|
| -50m | 10 | 11 | 9 | 9 | 11 | 10 | 29.87 | 7.855 |
| +50m | 10 | 12 | 11 | 9 | 11 | 10 | 23.79 | 5.996 |

## 腕 classical

拡大係数 ω(種別 → W16 の体数 ÷ 標本の体数): {'0': 76.666, '1': 76.604, '2': 74.523, '3': 76.754, '4': 1.0, '5': 76.747, '6': 76.628, '7': 76.333, '8': 2.146}

### 3-1 在圏のピーク時刻(5〜28 時)

| 列 | ラン(合計・θ1) | θ30 | 連続・θ1 | 正時(v1.3) | 錨1〔写〕計画 | 差[時] | JSD | 錨2〔部〕W12 | 差[時] | JSD | 錨3〔非〕PT c-2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 渋谷駅中心エリア | 9 | 10 | 9 | 10 | 13 | -4 | 0.05175 | — | — | — | 材料待ち |
| 渋谷駅北西エリア | 10 | 11 | 10 | 11 | 13 | -3 | 0.01623 | — | — | — | 材料待ち |
| 渋谷駅北東エリア | 18 | 12 | 10 | 18 | 12 | 6 | 0.02825 | — | — | — | 材料待ち |
| 渋谷駅南東エリア | 11 | 12 | 11 | 12 | 12 | -1 | 0.01771 | — | — | — | 材料待ち |
| 渋谷駅南西エリア | 11 | 12 | 11 | 13 | 12 | -1 | 0.01567 | — | — | — | 材料待ち |
| 5 エリア計 | 10 | 10 | 10 | 11 | 12 | -2 | 0.01572 | 13 | -3 | 0.02573 | 材料待ち |
| 舞台全体 | 12 | 11 | 12 | 11 | 12 | 0 | 0.00014 | 13 | -1 | 0.03395 | 材料待ち |

5 エリアのピークの順(早い順・ラン): central → northwest → southeast → southwest → northeast / 計画: northeast → southeast → southwest → central → northwest。母集団の腕(5 エリア計のピーク): P 10・全員 10。錨 2 の R・I・O = 34,941・1,521,476・1,483,785(β=time_dist_12 の乗車 帰宅・腕 β=合計のピーク 14)。計画で舞台の中に居るがセルが分からない割合(エリアに数えない・舞台には数える): 全体 0.3665・来街の種別 1・それ以外 0.2339。

### 3-2 来街者/居住者の比(1 日単位・30 分・area の写像・ω で戻す)

| エリア | ラン V/Res | ラン W/Res | ラン n(W,Res,V) | 訪日(別の列・ω) | 連続 V/Res | kind 写像 V/Res | 錨2〔写〕計画 V/Res | 錨2 W/Res | 錨1〔写〕W16 W/Res(area) |
|---|---|---|---|---|---|---|---|---|---|
| 渋谷駅中心エリア | 335.6 | 31.16 | [157, 4, 1441] | 12,451 | 294.6 | 3.754 | — | 31.09 | 23.93 |
| 渋谷駅北西エリア | 19.14 | 14.19 | [939, 63, 1255] | 13,976 | 17.72 | 2.406 | — | 14.15 | 17.15 |
| 渋谷駅北東エリア | 15.92 | 7.013 | [248, 33, 566] | 5,271 | 14.42 | 3.402 | — | 7.069 | 10.34 |
| 渋谷駅南東エリア | 31.76 | 20.85 | [279, 17, 404] | 4,270 | 29.26 | 2.093 | — | 21.09 | 22.2 |
| 渋谷駅南西エリア | 4.258 | 6.901 | [362, 53, 232] | 3,431 | 3.726 | 1.038 | — | 6.998 | 8.681 |
| 5 エリアの和 | 22.56 | 11.33 | [1985, 170, 3898] | 39,398 | 20.35 | 2.543 | — | 11.37 | 13.85 |

錨 1〔写〕W16 の体数(kind の写像・舞台全体): P′ V/Res 2.377・W/Res 4.922 / P(kind≠7) V/Res 2.319・W/Res 4.515 / 全員 V/Res 3.036。
錨 3〔非〕中核 9 町丁目の昼夜間人口比 14.8(都 第 11 表): W16 の静的な比 18.23(夜 8363・昼 152,454)・ランの比 16.68(居住者 n=114)・計画の比 16.53。写像のセル 133 枚(GL)。
フロア(合否にしない): 来街/勤務 PT 2018 [0.16, 0.27] 対 KDDI 1.66。ランの来街/勤務(5 エリアの和) 1.992。

### 3-3 駅ごとの到着の波(ω で戻す・全員)

| ノード | ラン 割合 | 錨1〔写〕割合 | 差 | ラン ピーク | 錨2〔部〕ピーク | 差[時] | JSD(形) | 計画 割合 | 計画 ピーク | 計画 JSD | 錨3〔非〕 | 錨4〔灰〕 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ext_rail_tokyu_denentoshi | 0.2016 | 0.1942 | 0.0074 | 8 | 8 | 0 | 0.09236 | 0.2034 | 8 | 0.0838 | 材料待ち | 読まない |
| ext_rail_tokyu_toyoko | 0.1253 | 0.1283 | -0.003 | 9 | 8 | 1 | 0.08195 | 0.1257 | 9 | 0.07808 | 材料待ち | 読まない |
| ext_rail_keio_inokashira | 0.0883 | 0.0859 | 0.0024 | 8 | 8 | 0 | 0.08897 | 0.0889 | 8 | 0.08547 | 材料待ち | 読まない |
| ext_rail_jr_yamanote | 0.1908 | 0.1862 | 0.0046 | 8 | 8 | 0 | 0.09373 | 0.1905 | 8 | 0.08676 | 材料待ち | 読まない |
| ext_rail_jr_saikyo_shonan | 0.0403 | 0.038 | 0.0023 | 9 | 8 | 1 | 0.1235 | 0.0404 | 9 | 0.1147 | 材料待ち | 読まない |
| ext_rail_metro_hanzomon | 0.1666 | 0.1717 | -0.0051 | 8 | 8 | 0 | 0.08646 | 0.1651 | 8 | 0.07695 | 材料待ち | 読まない |
| ext_rail_metro_fukutoshin | 0.0746 | 0.0734 | 0.0012 | 7 | 8 | -1 | 0.07296 | 0.0751 | 7 | 0.06451 | 材料待ち | 読まない |
| ext_rail_metro_ginza | 0.0941 | 0.0831 | 0.011 | 9 | 8 | 1 | 0.1048 | 0.0935 | 9 | 0.09905 | 材料待ち | 読まない |
| ext_walk_gate | 0.0066 | 0.018 | -0.0114 | 9 | 10 | -1 | 0.2299 | 0.0066 | 9 | 0.2657 | 材料待ち | 読まない |
| ext_road_gate | 0.0117 | 0.0212 | -0.0095 | 9 | 8 | 1 | 0.1293 | 0.0108 | 9 | 0.1214 | 材料待ち | 読まない |
| none | — | — | — | 18 | — | — | — | — | 18 | — | 材料待ち | 読まない |

到着の数(ラン・体の延べ): 5661・計画の到着(ARRIVE の予定): 5582。錨 1 の割合(daily_inflow)と W12 の重みの和の差の最大 0。

### 3-4 勤務の始業の分布(kind 0・2・ω で戻す)

| 列 | n | 平均 | p10 | p25 | p50 | p75 | p90 | :00/:30 の率 | 最頻の 15 分 | 立ち上がり(50%) |
|---|---|---|---|---|---|---|---|---|---|---|
| ラン | 2228 | 9:56 | 7:58 | 8:36 | 9:21 | 10:20 | 12:05 | 0.0341 | 9:00 | 9:15 |
| 錨1〔写〕第 31 表+lead | 0 | — | — | — | — | — | — | — | — | — |
| 錨2〔写〕W17 v2 勤務の行 | 2281 | 9:16 | 6:59 | 7:50 | 8:35 | 9:34 | 12:15 | 0.0574 | 8:00 | 8:30 |
| 錨5〔写〕W20 暦 1a の約束 | 0 | — | — | — | — | — | — | — | — | — |
| 錨3〔部〕第 8-1 表 仕事 | — | — | — | — | — | — | — | — | — | 8:30 |
| 錨4〔非〕PT c-2 | 材料待ち | — | — | — | — | — | — | — | — | — |

差(ラン − 錨): 錨 1 平均 — 分・p50 — 分・JSD — / 錨 2 平均 40 分・p50 46 分・JSD 0.09287 / 立ち上がり(在席の率 対 第 8-1 表) 45 分。対象 2286 体・始まりが取れた 2228 体(立ち上がりの行の計画=計画上のセルの在席の率)。
〔3-1〕差(ラン − 錨 5=W20): 平均 — 分・p50 — 分・JSD — / W17 − W20(参考): 平均 — 分・p50 — 分・JSD —。錨 5 の体 0・表に無い体 2286(合否にしない)。

### 感度: エリアの写像 ±50 m

| 膨張 | 渋谷駅中心エリア | 渋谷駅北西エリア | 渋谷駅北東エリア | 渋谷駅南東エリア | 渋谷駅南西エリア | 5 エリア計 | 計 V/Res | 計 W/Res |
|---|---|---|---|---|---|---|---|---|
| -50m | 9 | 9 | 9 | 10 | 11 | 10 | 24.02 | 12.62 |
| +50m | 9 | 10 | 18 | 11 | 11 | 10 | 21.04 | 10.51 |

## 宣言

- population: v1.4 の母集団 P′ = age ≥ 20 かつ is_foreign でない(本則)。P = kind ≠ 7 かつ age ≥ 20 は継続の腕
- weights: 拡大係数 ω_k = N_k(W16)/ n_k(標本)。二層抽出の種別の偏りを戻す(expedient)
- dwell: 1 日単位の 30 分=合計(本則)・連続(腕)。時間帯別は θ = 1 刻み(既定)・30 分(腕)
- hours: KDDI の 5〜28 時の 24 区分。1 日ランの 24〜28 時は同じ日の 0〜4 時で代える
- attr: area の写像(自宅エリアが先・次に職場/学校エリア・どちらでもなければ来街)。kind の写像は継続の記録
- plan_cells: 計画上のセル=行の target_cell・負の行は職場/学校/自宅のセルで補う・補えない行は舞台の中のセル不明
- arrivals: transit_state が 1・2 → 0 に変わった刻み × W16 direction_node(全員)
- work_start: kind 0・2・P′・work_cell ≥ 0 かつ ≠ home_cell。work_cell に 30 分以上続けて居た最初の区間の始まり(0 時から続く区間は除く)
- rise: 仕事の行動者率(または在席の率)が 1 日の最大の 50% を初めて超える 15 分(閾値 expedient)
- core9: セル → 町丁目は居住者の chome_key の多数決+最近傍。昼=10〜16 時に 30 分以上(ランの腕)
- no_pass_fail: 合否は書かない。〔写〕の錨との差は形だけ。「現実に近づいた」の主張は holdout の開封(S1)の後だけ

## 読んだファイル(gauge の段・許可の一覧の中だけ)

| 役割 | 道筋 | バイト | md5 | 配列の hash(journal) |
|---|---|---|---|---|
| W12_nodes | data/world/v2_stage_4-3/w12_external_nodes.parquet | 5581 | 09ee6563f2acfc73f8929cb043e957bd | — |
| W12_weights | data/world/v2_stage_4-3/w12_generation_weights.parquet | 18,729 | e76d78b146133c8ab74ff862e0dba6aa | — |
| W16 | data/world/v2_stage_4-3/w16_population.parquet | 5,390,663 | 4fb3392fdc7bcef16909631797679f37 | — |
| W16_chome | data/world/v2_stage_4-3/w16_chome.parquet | 5496 | c0084b5ef6b8f4db0ba36d4765cba6c3 | — |
| W2_cells | data/world/v2_stage_4-3/w2_cells.parquet | 26,564 | a8b98d56460e0a2807c87f2309d5354c | — |
| area_axes | tools/c7/area_axes_v0.json | 4560 | cd629533fd0cd09bf1db9cdbf86153cb | — |
| calib_anchors | docs/bench/instruments/anchor_gauge/calib_anchors_v0.json | 1852 | dbc9dac18728f3c65894140486f4ec75 | — |
| commute_r3 | docs/bench/anchors/commute_time_dist_r3.json | 57,686 | 286e0c90796f429348271d2acb2f84e1 | — |
| journal | _bc2/fix/gauge/anchor_journal_classical.npz | 1,782,419 | 3dcaec6793cddedec351f8729d50b75d | 6388ca86c720f9f8 |
| journal | _bc2/fix/gauge/anchor_journal_mock.npz | 1,761,573 | ef8826d4baf104619310f4819b86e385 | db39b27ace8f0a35 |
| pool | data/persona_pool_v2/L1/part-0000.jsonl | 29,915,767 | 6d26fed025d12ec5ce214c71b57c0f49 | — |
| pool | data/persona_pool_v2/L2/part-0000.jsonl | 60,134,550 | aa2d37cd6927fff4e553d214ad9ebd6b | — |
| pool | data/persona_pool_v2/L2/part-0001.jsonl | 60,267,213 | 467e0bba367575355d352d51738f9ed1 | — |
| pool | data/persona_pool_v2/L2/part-0002.jsonl | 46,266,565 | aef2ab1956881c6951e8b220eb7fac65 | — |
| pool | data/persona_pool_v2/L3/part-0000.jsonl | 37,411,776 | df3a441a28069175e015907b8908be42 | — |
| pool | data/persona_pool_v2/L4/part-0000.jsonl | 48,202,253 | 4ebc8f14c38568bd160a4dcc325e45de | — |
| pool | data/persona_pool_v2/L4/part-0001.jsonl | 48,221,094 | 07e79f6fc8af64fa2b34b784ef010217 | — |
| pool | data/persona_pool_v2/L4/part-0002.jsonl | 48,214,912 | acada5d0ef0bd620fe1a310056388656 | — |
| pool | data/persona_pool_v2/L4/part-0003.jsonl | 48,210,145 | 992911fb7042989a5510a386065d7a0e | — |
| pool | data/persona_pool_v2/L4/part-0004.jsonl | 48,223,630 | e68c544878d7b9045849ad44d09fcaf3 | — |
| pool | data/persona_pool_v2/L4/part-0005.jsonl | 48,205,599 | cb4575206f58cc84271232f8daa62334 | — |
| pool | data/persona_pool_v2/L4/part-0006.jsonl | 48,227,721 | 28bfaea91d44144158051075f7da351d | — |
| pool | data/persona_pool_v2/L4/part-0007.jsonl | 48,217,799 | 8f4157b838ff8dd2060c44c814fd2716 | — |
| pool | data/persona_pool_v2/L4/part-0008.jsonl | 48,216,268 | 0a56bc723022b2f077c0344de25dee73 | — |
| pool | data/persona_pool_v2/L4/part-0009.jsonl | 48,218,084 | f7cfd9099e4ed23c1bf2797f399b3308 | — |
| pool | data/persona_pool_v2/L4/part-0010.jsonl | 48,216,512 | 0a64d4b35162e30445f6aade51754e89 | — |
| pool | data/persona_pool_v2/L4/part-0011.jsonl | 48,214,737 | 85e7ceaba6b417111f06a9692d499f1c | — |
| pool | data/persona_pool_v2/L4/part-0012.jsonl | 48,214,518 | 57a8ade88c49d3bcb7c85ca0bdfd1921 | — |
| pool | data/persona_pool_v2/L4/part-0013.jsonl | 48,211,549 | 773b09b9b02f9cc4c56c56d40b5f301a | — |
| pool | data/persona_pool_v2/L4/part-0014.jsonl | 48,218,235 | fda4ac33255ef3abb65f15b8c0309f47 | — |
| pool | data/persona_pool_v2/L4/part-0015.jsonl | 41,711,721 | 922097bb436b99a08d3dd825415c9224 | — |
| pool | data/persona_pool_v2/L5/part-0000.jsonl | 1,313,980 | 8b4525dc21edd7c80c83891804902eba | — |
| ssb_8_1 | docs/bench/anchors/ssb2021_activity_prior_v0.json | 1,506,693 | 79acf3cabc43fd36f11d2d718310066c | — |
| time_dist_12 | data/realworld/transport_census/time_dist_12.json | 32,194 | 9096b80bbfb15cef490bc83ed8760c57 | — |
| w20 | data/world/v2_stage_3-1/w20_calendar_1a.parquet | 14,338,871 | 435384232121275c18b762cf6c2814a7 | — |

journal の md5 は meta の壁時計で変わる。同じランかは配列の hash で見る。

## record の段でエンジンが開いたファイル(Python の open・道筋だけ・計器はその値を使わない)

| 道筋 | 腕 | 計器の段で落とす語 |
|---|---|---|
| data/calendar/syukujitsu.csv | mock・classical | — |
| data/persona_pool_v2/L3/part-0000.jsonl | mock・classical | — |
| data/persona_pool_v2/L5/part-0000.jsonl | mock・classical | — |
| data/realworld/osm/poi_opening_hours_overpass_20260907.json | mock・classical | — |
| data/realworld/osm/poi_tags_overpass_20260928.json | mock・classical | — |
| data/realworld/osm/street_features_overpass_20260907.json | mock・classical | — |
| data/research_cache/pop41b/derived/wage_t18.json | mock・classical | — |
| data/research_cache/pop41b/derived/wage_t2.json | mock・classical | — |
| data/research_cache/pop41b/derived/wage_t6.json | mock・classical | — |
| data/research_cache/pop41b/derived/wage_t9.json | mock・classical | — |
| data/world/v2_stage_4-3/build_manifest.json | mock・classical | — |
| data/world/v2_stage_4-3/w10_noise_stage_day.npy | mock・classical | — |
| data/world/v2_stage_4-3/w10_noise_stage_night.npy | mock・classical | — |
| data/world/v2_stage_4-3/w10_street_points.parquet | mock・classical | — |
| data/world/v2_stage_4-3/w12_external_nodes.parquet | mock・classical | — |
| data/world/v2_stage_4-3/w12_timetables.parquet | mock・classical | — |
| data/world/v2_stage_4-3/w13_weather_days.parquet | mock・classical | — |
| data/world/v2_stage_4-3/w13_weather_hourly.parquet | mock・classical | — |
| data/world/v2_stage_4-3/w14_signage.parquet | mock・classical | — |
| data/world/v2_stage_4-3/w15_cell_static.parquet | mock・classical | — |
| data/world/v2_stage_4-3/w3_cell_dist.npy | mock・classical | — |
| data/world/v2_stage_4-3/w3_next_hop.npy | mock・classical | — |
| data/world/v2_stage_4-3/w9_shadow_2026-07-13.npy | mock・classical | — |
| docs/bench/anchors/hunger_energy_build_anchors_v0.json | mock・classical | — |
| docs/bench/anchors/ssb2021_activity_prior_v0.json | classical | — |
| docs/design/bridging-ledger.json | mock・classical | — |
| docs/design/rules-table.json | mock・classical | — |
| docs/design/v2-budget-declaration.md | mock・classical | — |

pyarrow の読みは監査に出ない。表の parquet は Python の open でも開かれたもので、pyarrow だけで読んだ parquet はこの表に載らない。
