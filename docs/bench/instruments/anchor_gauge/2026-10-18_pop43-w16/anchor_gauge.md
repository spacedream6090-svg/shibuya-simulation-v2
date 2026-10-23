# 較正側の錨の計器(2-0)

合否は書かない。〔写〕の錨は構築の入力の写しで、差は形だけを見る。「現実に近づいた」と書けるのは holdout の開封(S1)の後だけ。検証側(〔検〕)と〔灰〕は、**gauge の段では**許可の一覧で縛って読んでいない。record の段(エンジンのラン)では、エンジンが前から読む入力を開く(末尾の表。計器はその値を使わない)。

## ラン

| 腕 | commit | final | 呼数 | bridges_count | rules_version | src の差(ファイル数) | 体数 | seed |
|---|---|---|---|---|---|---|---|---|
| mock | 2809c4a | 333b1820f7849b00 | 64,024 | 548 | 4dda40d8f83d6a3f | 17 | 5000 | 1 |
| classical | 2809c4a | e192b390e7434810 | 92,825 | 548 | 4dda40d8f83d6a3f | 17 | 5000 | 1 |

第 18-1 表(〔検〕)と比べた食事時刻の結果の印(計器は比べない・比べる道具の結果に写す): mock=検証可(置き換えの後=既定の食事時刻は W17 v2 の分布・エンジンは検証側の錨を開いていない)・classical=検証可(置き換えの後=既定の食事時刻は W17 v2 の分布・エンジンは検証側の錨を開いていない)

エリアの写像: `area_axes_v0.json`(版 v0・expedient)・面積の帯の自己検査 真・面積[ha] {'central': 9.0, 'northwest': 57.0, 'northeast': 27.0, 'southeast': 14.0, 'southwest': 31.0}

## 腕 mock

拡大係数 ω(種別 → W16 の体数 ÷ 標本の体数): {'0': 91.974, '1': 91.997, '2': 94.36, '3': 84.205, '4': 1.0, '5': 91.717, '6': 91.324, '7': 93.57, '8': 1.759}

### 3-1 在圏のピーク時刻(5〜28 時)

| 列 | ラン(合計・θ1) | θ30 | 連続・θ1 | 正時(v1.3) | 錨1〔写〕計画 | 差[時] | JSD | 錨2〔部〕W12 | 差[時] | JSD | 錨3〔非〕PT c-2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 渋谷駅中心エリア | 9 | 10 | 10 | 10 | 11 | -2 | 0.03481 | — | — | — | 材料待ち |
| 渋谷駅北西エリア | 12 | 12 | 12 | 12 | 11 | 1 | 0.028 | — | — | — | 材料待ち |
| 渋谷駅北東エリア | 12 | 11 | 12 | 18 | 11 | 1 | 0.01847 | — | — | — | 材料待ち |
| 渋谷駅南東エリア | 9 | 10 | 9 | 10 | 14 | -5 | 0.02271 | — | — | — | 材料待ち |
| 渋谷駅南西エリア | 13 | 13 | 13 | 13 | 12 | 1 | 0.03917 | — | — | — | 材料待ち |
| 5 エリア計 | 10 | 11 | 10 | 12 | 11 | -1 | 0.01999 | 13 | -3 | 0.02492 | 材料待ち |
| 舞台全体 | 10 | 11 | 10 | 12 | 12 | -2 | 0.00041 | 13 | -3 | 0.03151 | 材料待ち |

5 エリアのピークの順(早い順・ラン): central → southeast → northwest → northeast → southwest / 計画: central → northwest → northeast → southwest → southeast。母集団の腕(5 エリア計のピーク): P 10・全員 10。錨 2 の R・I・O = 37,836・1,521,476・1,483,785(β=time_dist_12 の乗車 帰宅・腕 β=合計のピーク 14)。計画で舞台の中に居るがセルが分からない割合(エリアに数えない・舞台には数える): 全体 0.3483・来街の種別 1・それ以外 0.2399。

### 3-2 来街者/居住者の比(1 日単位・30 分・area の写像・ω で戻す)

| エリア | ラン V/Res | ラン W/Res | ラン n(W,Res,V) | 訪日(別の列・ω) | 連続 V/Res | kind 写像 V/Res | 錨2〔写〕計画 V/Res | 錨2 W/Res | 錨1〔写〕W16 W/Res(area) |
|---|---|---|---|---|---|---|---|---|---|
| 渋谷駅中心エリア | 928 | 29.9 | [58, 2, 2138] | 13,053 | 837.4 | 2.56 | — | 39.71 | 18.62 |
| 渋谷駅北西エリア | 33.94 | 16.55 | [1007, 46, 1527] | 12,689 | 32.75 | 1.808 | — | 21.57 | 20.69 |
| 渋谷駅北東エリア | 17.48 | 3.974 | [115, 31, 611] | 4,195 | 16.32 | 1.224 | — | 8.09 | 11.28 |
| 渋谷駅南東エリア | 24.68 | 11.47 | [139, 13, 357] | 2,802 | 23.25 | 1.794 | — | 25.42 | 28.34 |
| 渋谷駅南西エリア | 3.199 | 4.302 | [146, 36, 123] | 748.6 | 2.724 | 0.6935 | — | 11.85 | 10.82 |
| 5 エリアの和 | 34.8 | 9.734 | [1465, 128, 4756] | 33,488 | 32.58 | 1.799 | — | 16.23 | 16.4 |

錨 1〔写〕W16 の体数(kind の写像・舞台全体): P′ V/Res 2.196・W/Res 5.561 / P(kind≠7) V/Res 2.335・W/Res 5.561 / 全員 V/Res 2.966。
錨 3〔非〕中核 9 町丁目の昼夜間人口比 14.8(都 第 11 表): W16 の静的な比 23.37(夜 8524・昼 199,219)・ランの比 18.43(居住者 n=100)・計画の比 21.21。写像のセル 134 枚(GL)。
フロア(合否にしない): 来街/勤務 PT 2018 [0.16, 0.27] 対 KDDI 1.66。ランの来街/勤務(5 エリアの和) 3.576。

### 3-3 駅ごとの到着の波(ω で戻す・全員)

| ノード | ラン 割合 | 錨1〔写〕割合 | 差 | ラン ピーク | 錨2〔部〕ピーク | 差[時] | JSD(形) | 計画 割合 | 計画 ピーク | 計画 JSD | 錨3〔非〕 | 錨4〔灰〕 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ext_rail_tokyu_denentoshi | 0.1978 | 0.1942 | 0.0036 | 8 | 8 | 0 | 0.05999 | 0.2039 | 8 | 0.08122 | 材料待ち | 読まない |
| ext_rail_tokyu_toyoko | 0.1346 | 0.1283 | 0.0063 | 9 | 8 | 1 | 0.0782 | 0.1376 | 9 | 0.103 | 材料待ち | 読まない |
| ext_rail_keio_inokashira | 0.0837 | 0.0859 | -0.0022 | 8 | 8 | 0 | 0.06763 | 0.081 | 7 | 0.1059 | 材料待ち | 読まない |
| ext_rail_jr_yamanote | 0.1804 | 0.1862 | -0.0058 | 8 | 8 | 0 | 0.05611 | 0.1842 | 8 | 0.07045 | 材料待ち | 読まない |
| ext_rail_jr_saikyo_shonan | 0.042 | 0.038 | 0.004 | 9 | 8 | 1 | 0.08019 | 0.0414 | 8 | 0.09804 | 材料待ち | 読まない |
| ext_rail_metro_hanzomon | 0.1827 | 0.1717 | 0.011 | 8 | 8 | 0 | 0.05775 | 0.1754 | 8 | 0.06903 | 材料待ち | 読まない |
| ext_rail_metro_fukutoshin | 0.0737 | 0.0734 | 0.0003 | 7 | 8 | -1 | 0.05906 | 0.0713 | 7 | 0.07718 | 材料待ち | 読まない |
| ext_rail_metro_ginza | 0.079 | 0.0831 | -0.0041 | 9 | 8 | 1 | 0.05607 | 0.0794 | 9 | 0.08934 | 材料待ち | 読まない |
| ext_walk_gate | 0.0079 | 0.018 | -0.0101 | 9 | 10 | -1 | 0.09804 | 0.0078 | 9 | 0.2656 | 材料待ち | 読まない |
| ext_road_gate | 0.0182 | 0.0212 | -0.003 | 9 | 8 | 1 | 0.05225 | 0.018 | 9 | 0.08967 | 材料待ち | 読まない |
| none | — | — | — | 18 | — | — | — | — | 18 | — | 材料待ち | 読まない |

到着の数(ラン・体の延べ): 8059・計画の到着(ARRIVE の予定): 5687。錨 1 の割合(daily_inflow)と W12 の重みの和の差の最大 0。

### 3-4 勤務の始業の分布(kind 0・2・ω で戻す)

| 列 | n | 平均 | p10 | p25 | p50 | p75 | p90 | :00/:30 の率 | 最頻の 15 分 | 立ち上がり(50%) |
|---|---|---|---|---|---|---|---|---|---|---|
| ラン | 845 | 13:00 | 8:06 | 9:27 | 12:00 | 16:21 | 19:47 | 0.0426 | 9:15 | 9:30 |
| 錨1〔写〕第 31 表+lead | 1939 | 9:04 | 7:06 | 7:48 | 8:37 | 9:28 | 10:56 | 0.0289 | 8:30 | — |
| 錨2〔写〕W17 v2 勤務の行 | 2336 | 9:15 | 7:09 | 7:51 | 8:40 | 9:32 | 11:20 | 0.0463 | 8:30 | 8:30 |
| 錨5〔写〕W20 暦 1a の約束 | 1890 | 9:00 | 7:01 | 7:45 | 8:32 | 9:24 | 10:53 | 0.0328 | 8:30 | — |
| 錨3〔部〕第 8-1 表 仕事 | — | — | — | — | — | — | — | — | — | 8:30 |
| 錨4〔非〕PT c-2 | 材料待ち | — | — | — | — | — | — | — | — | — |

差(ラン − 錨): 錨 1 平均 236.5 分・p50 203 分・JSD 0.2711 / 錨 2 平均 225.2 分・p50 200 分・JSD 0.2553 / 立ち上がり(在席の率 対 第 8-1 表) 60 分。対象 2346 体・始まりが取れた 845 体(立ち上がりの行の計画=計画上のセルの在席の率)。
〔3-1〕差(ラン − 錨 5=W20): 平均 239.7 分・p50 208 分・JSD 0.2757 / W17 − W20(参考): 平均 14.5 分・p50 8 分・JSD 0.0202。錨 5 の体 1890・表に無い体 0(合否にしない)。

### 感度: エリアの写像 ±50 m

| 膨張 | 渋谷駅中心エリア | 渋谷駅北西エリア | 渋谷駅北東エリア | 渋谷駅南東エリア | 渋谷駅南西エリア | 5 エリア計 | 計 V/Res | 計 W/Res |
|---|---|---|---|---|---|---|---|---|
| -50m | 9 | 12 | 9 | 9 | 10 | 10 | 38.02 | 11.47 |
| +50m | 10 | 12 | 12 | 9 | 12 | 10 | 26.62 | 7.356 |

## 腕 classical

拡大係数 ω(種別 → W16 の体数 ÷ 標本の体数): {'0': 91.974, '1': 91.997, '2': 94.36, '3': 84.205, '4': 1.0, '5': 91.717, '6': 91.324, '7': 93.57, '8': 1.759}

### 3-1 在圏のピーク時刻(5〜28 時)

| 列 | ラン(合計・θ1) | θ30 | 連続・θ1 | 正時(v1.3) | 錨1〔写〕計画 | 差[時] | JSD | 錨2〔部〕W12 | 差[時] | JSD | 錨3〔非〕PT c-2 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 渋谷駅中心エリア | 9 | 10 | 9 | 10 | 11 | -2 | 0.07637 | — | — | — | 材料待ち |
| 渋谷駅北西エリア | 10 | 11 | 10 | 11 | 11 | -1 | 0.01831 | — | — | — | 材料待ち |
| 渋谷駅北東エリア | 10 | 12 | 10 | 18 | 11 | -1 | 0.02124 | — | — | — | 材料待ち |
| 渋谷駅南東エリア | 11 | 11 | 11 | 12 | 14 | -3 | 0.01812 | — | — | — | 材料待ち |
| 渋谷駅南西エリア | 12 | 12 | 12 | 12 | 12 | 0 | 0.01751 | — | — | — | 材料待ち |
| 5 エリア計 | 10 | 10 | 10 | 11 | 11 | -1 | 0.01703 | 13 | -3 | 0.02184 | 材料待ち |
| 舞台全体 | 12 | 11 | 12 | 12 | 12 | 0 | 0.00023 | 13 | -1 | 0.02839 | 材料待ち |

5 エリアのピークの順(早い順・ラン): central → northwest → northeast → southeast → southwest / 計画: central → northwest → northeast → southwest → southeast。母集団の腕(5 エリア計のピーク): P 10・全員 10。錨 2 の R・I・O = 37,836・1,521,476・1,483,785(β=time_dist_12 の乗車 帰宅・腕 β=合計のピーク 14)。計画で舞台の中に居るがセルが分からない割合(エリアに数えない・舞台には数える): 全体 0.3483・来街の種別 1・それ以外 0.2399。

### 3-2 来街者/居住者の比(1 日単位・30 分・area の写像・ω で戻す)

| エリア | ラン V/Res | ラン W/Res | ラン n(W,Res,V) | 訪日(別の列・ω) | 連続 V/Res | kind 写像 V/Res | 錨2〔写〕計画 V/Res | 錨2 W/Res | 錨1〔写〕W16 W/Res(area) |
|---|---|---|---|---|---|---|---|---|---|
| 渋谷駅中心エリア | 674.1 | 39.71 | [77, 2, 1523] | 11,378 | 573.4 | 4.171 | — | 39.71 | 18.62 |
| 渋谷駅北西エリア | 26.36 | 21.45 | [1328, 46, 1194] | 11,933 | 24.24 | 2.252 | — | 21.57 | 20.69 |
| 渋谷駅北東エリア | 17.36 | 8.02 | [232, 31, 568] | 4,203 | 16.09 | 1.665 | — | 8.09 | 11.28 |
| 渋谷駅南東エリア | 33.49 | 25.1 | [304, 13, 444] | 3,361 | 31.19 | 2.159 | — | 25.42 | 28.34 |
| 渋谷駅南西エリア | 6.866 | 11.52 | [391, 36, 250] | 1,778 | 6.099 | 1.351 | — | 11.85 | 10.82 |
| 5 エリアの和 | 29.89 | 16.05 | [2332, 128, 3979] | 32,652 | 26.74 | 2.295 | — | 16.23 | 16.4 |

錨 1〔写〕W16 の体数(kind の写像・舞台全体): P′ V/Res 2.196・W/Res 5.561 / P(kind≠7) V/Res 2.335・W/Res 5.561 / 全員 V/Res 2.966。
錨 3〔非〕中核 9 町丁目の昼夜間人口比 14.8(都 第 11 表): W16 の静的な比 23.37(夜 8524・昼 199,219)・ランの比 21.43(居住者 n=100)・計画の比 21.21。写像のセル 134 枚(GL)。
フロア(合否にしない): 来街/勤務 PT 2018 [0.16, 0.27] 対 KDDI 1.66。ランの来街/勤務(5 エリアの和) 1.862。

### 3-3 駅ごとの到着の波(ω で戻す・全員)

| ノード | ラン 割合 | 錨1〔写〕割合 | 差 | ラン ピーク | 錨2〔部〕ピーク | 差[時] | JSD(形) | 計画 割合 | 計画 ピーク | 計画 JSD | 錨3〔非〕 | 錨4〔灰〕 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| ext_rail_tokyu_denentoshi | 0.2014 | 0.1942 | 0.0072 | 8 | 8 | 0 | 0.08311 | 0.2039 | 8 | 0.08122 | 材料待ち | 読まない |
| ext_rail_tokyu_toyoko | 0.1375 | 0.1283 | 0.0092 | 9 | 8 | 1 | 0.1033 | 0.1376 | 9 | 0.103 | 材料待ち | 読まない |
| ext_rail_keio_inokashira | 0.081 | 0.0859 | -0.0049 | 7 | 8 | -1 | 0.108 | 0.081 | 7 | 0.1059 | 材料待ち | 読まない |
| ext_rail_jr_yamanote | 0.1854 | 0.1862 | -0.0008 | 8 | 8 | 0 | 0.07277 | 0.1842 | 8 | 0.07045 | 材料待ち | 読まない |
| ext_rail_jr_saikyo_shonan | 0.0419 | 0.038 | 0.0039 | 8 | 8 | 0 | 0.1032 | 0.0414 | 8 | 0.09804 | 材料待ち | 読まない |
| ext_rail_metro_hanzomon | 0.1759 | 0.1717 | 0.0042 | 8 | 8 | 0 | 0.07251 | 0.1754 | 8 | 0.06903 | 材料待ち | 読まない |
| ext_rail_metro_fukutoshin | 0.0714 | 0.0734 | -0.002 | 7 | 8 | -1 | 0.08039 | 0.0713 | 7 | 0.07718 | 材料待ち | 読まない |
| ext_rail_metro_ginza | 0.0792 | 0.0831 | -0.0039 | 9 | 8 | 1 | 0.08772 | 0.0794 | 9 | 0.08934 | 材料待ち | 読まない |
| ext_walk_gate | 0.0078 | 0.018 | -0.0102 | 9 | 10 | -1 | 0.2467 | 0.0078 | 9 | 0.2656 | 材料待ち | 読まない |
| ext_road_gate | 0.0184 | 0.0212 | -0.0028 | 9 | 8 | 1 | 0.09776 | 0.018 | 9 | 0.08967 | 材料待ち | 読まない |
| none | — | — | — | 18 | — | — | — | — | 18 | — | 材料待ち | 読まない |

到着の数(ラン・体の延べ): 5603・計画の到着(ARRIVE の予定): 5687。錨 1 の割合(daily_inflow)と W12 の重みの和の差の最大 0。

### 3-4 勤務の始業の分布(kind 0・2・ω で戻す)

| 列 | n | 平均 | p10 | p25 | p50 | p75 | p90 | :00/:30 の率 | 最頻の 15 分 | 立ち上がり(50%) |
|---|---|---|---|---|---|---|---|---|---|---|
| ラン | 2251 | 10:05 | 8:06 | 8:41 | 9:29 | 10:36 | 12:39 | 0.0342 | 8:45 | 9:15 |
| 錨1〔写〕第 31 表+lead | 1939 | 9:04 | 7:06 | 7:48 | 8:37 | 9:28 | 10:56 | 0.0289 | 8:30 | — |
| 錨2〔写〕W17 v2 勤務の行 | 2336 | 9:15 | 7:09 | 7:51 | 8:40 | 9:32 | 11:20 | 0.0463 | 8:30 | 8:30 |
| 錨5〔写〕W20 暦 1a の約束 | 1890 | 9:00 | 7:01 | 7:45 | 8:32 | 9:24 | 10:53 | 0.0328 | 8:30 | — |
| 錨3〔部〕第 8-1 表 仕事 | — | — | — | — | — | — | — | — | — | 8:30 |
| 錨4〔非〕PT c-2 | 材料待ち | — | — | — | — | — | — | — | — | — |

差(ラン − 錨): 錨 1 平均 61.7 分・p50 52 分・JSD 0.1156 / 錨 2 平均 50.4 分・p50 49 分・JSD 0.1093 / 立ち上がり(在席の率 対 第 8-1 表) 45 分。対象 2346 体・始まりが取れた 2251 体(立ち上がりの行の計画=計画上のセルの在席の率)。
〔3-1〕差(ラン − 錨 5=W20): 平均 65 分・p50 57 分・JSD 0.1306 / W17 − W20(参考): 平均 14.5 分・p50 8 分・JSD 0.0202。錨 5 の体 1890・表に無い体 0(合否にしない)。

### 感度: エリアの写像 ±50 m

| 膨張 | 渋谷駅中心エリア | 渋谷駅北西エリア | 渋谷駅北東エリア | 渋谷駅南東エリア | 渋谷駅南西エリア | 5 エリア計 | 計 V/Res | 計 W/Res |
|---|---|---|---|---|---|---|---|---|
| -50m | 9 | 9 | 9 | 10 | 11 | 10 | 32.47 | 18.49 |
| +50m | 9 | 11 | 12 | 11 | 11 | 10 | 24.68 | 13.09 |

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
| W12_nodes | data/world/v2/w12_external_nodes.parquet | 5581 | 09ee6563f2acfc73f8929cb043e957bd | — |
| W12_weights | data/world/v2/w12_generation_weights.parquet | 18,729 | e76d78b146133c8ab74ff862e0dba6aa | — |
| W16 | data/world/v2/w16_population.parquet | 4,631,684 | c5f30ba89e22ae0e23b712885f871ed1 | — |
| W16_chome | data/world/v2/w16_chome.parquet | 5496 | c0084b5ef6b8f4db0ba36d4765cba6c3 | — |
| W2_cells | data/world/v2/w2_cells.parquet | 26,564 | a8b98d56460e0a2807c87f2309d5354c | — |
| area_axes | tools/c7/area_axes_v0.json | 4560 | cd629533fd0cd09bf1db9cdbf86153cb | — |
| calib_anchors | docs/bench/instruments/anchor_gauge/calib_anchors_v0.json | 1852 | dbc9dac18728f3c65894140486f4ec75 | — |
| commute_r3 | docs/bench/anchors/commute_time_dist_r3.json | 57,686 | 286e0c90796f429348271d2acb2f84e1 | — |
| journal | _bc/gauge_v2/anchor_journal_classical.npz | 1,794,055 | 1fd3a9e2ba324f540dea01ce0ff1142d | 86b24cbdb674958a |
| journal | _bc/gauge_v2/anchor_journal_mock.npz | 1,759,411 | 52a08e3b9d5b750d44127263b5e0b987 | 5d6a183a046fbf06 |
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
| data/persona_pool_v2/L1/part-0000.jsonl | mock・classical | — |
| data/persona_pool_v2/L2/part-0000.jsonl | mock・classical | — |
| data/persona_pool_v2/L2/part-0001.jsonl | mock・classical | — |
| data/persona_pool_v2/L2/part-0002.jsonl | mock・classical | — |
| data/persona_pool_v2/L3/part-0000.jsonl | mock・classical | — |
| data/persona_pool_v2/L5/part-0000.jsonl | mock・classical | — |
| data/realworld/osm/poi_opening_hours_overpass_20260907.json | mock・classical | — |
| data/realworld/osm/poi_tags_overpass_20260928.json | mock・classical | — |
| data/realworld/osm/street_features_overpass_20260907.json | mock・classical | — |
| data/research_cache/pop41b/derived/wage_t18.json | mock・classical | — |
| data/research_cache/pop41b/derived/wage_t2.json | mock・classical | — |
| data/research_cache/pop41b/derived/wage_t6.json | mock・classical | — |
| data/research_cache/pop41b/derived/wage_t9.json | mock・classical | — |
| data/world/v2/build_manifest.json | mock・classical | — |
| data/world/v2/w10_noise_stage_day.npy | mock・classical | — |
| data/world/v2/w10_noise_stage_night.npy | mock・classical | — |
| data/world/v2/w10_street_points.parquet | mock・classical | — |
| data/world/v2/w12_external_nodes.parquet | mock・classical | — |
| data/world/v2/w12_timetables.parquet | mock・classical | — |
| data/world/v2/w13_weather_days.parquet | mock・classical | — |
| data/world/v2/w13_weather_hourly.parquet | mock・classical | — |
| data/world/v2/w14_signage.parquet | mock・classical | — |
| data/world/v2/w15_cell_static.parquet | mock・classical | — |
| data/world/v2/w3_cell_dist.npy | mock・classical | — |
| data/world/v2/w3_next_hop.npy | mock・classical | — |
| data/world/v2/w9_shadow_2026-07-13.npy | mock・classical | — |
| docs/bench/anchors/hunger_energy_build_anchors_v0.json | mock・classical | — |
| docs/bench/anchors/ssb2021_activity_prior_v0.json | classical | — |
| docs/design/bridging-ledger.json | mock・classical | — |
| docs/design/rules-table.json | mock・classical | — |
| docs/design/v2-budget-declaration.md | mock・classical | — |

pyarrow の読みは監査に出ない。表の parquet は Python の open でも開かれたもので、pyarrow だけで読んだ parquet はこの表に載らない。
