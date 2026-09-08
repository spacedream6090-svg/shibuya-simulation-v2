# 工程 C1(世界データ構築)受入報告(2026-09-08・ブランチ build/c0-c4)

> 根拠: 実装計画書 §9.1 C1 行(W0-W13 呼ゼロ+W18 被覆指標+W19 manifest 凍結+W20 検収パック・サブA=地理 W0-W6/W8/W9/W11・サブB=場・境界 W7/W10/W12/W13)・世界データ構築仕様 §0-§1。証拠=親自身の実行出力のみ。

## 1. 地理側(サブA: W0-W6・W11)= 親検収済み

親の実行:
```
$ .venv/Scripts/python.exe -m shibuya.build.geo.run --out data/world/v2
stages = W0,W1,W2,W3,W4,W5,W6,W11   failed gates: []
build_hash = 03533de5faabb3c4a62ecc0b2610723b6a9f2a41b1b0516375e1085800f8341a
$ (同じコマンドを scratchpad へ)  → rebuild identical: True
$ .venv/Scripts/python.exe -m pytest tests/build_geo -q -p no:cacheprovider -o addopts=""
37 passed in 2.81s
$ .venv/Scripts/lint-imports.exe → Contracts: 5 kept, 0 broken.
$ python tools/scan_secrets.py <untracked new files> → CLEAN
```

段階ゲート(仕様値との照合・すべて PASS):
| 段階 | ゲート | 実測 | 仕様 |
|---|---|---|---|
| W0 | origin / ground0 の3ファイル一致 | [35.6595, 139.70062] / 15.18 | 同 |
| W1 | nodes / edges / 連結成分 / 総延長 | 3,499 / 4,944 / 1 / 186,741.0 m(差0) | 3,499 / 4,944 / 1 / 186,741 m |
| W1 | 層跨ぎ steps(空欄の実測) | 51 / 193 | 空欄 |
| W2 | GL セル / 4近傍ペア / 街区(Euler) | 453 / 785 / 1,242 | 453 / 785 / 1,242 |
| W2 | place_id 総数(層込み) | 520(GL453+DECK39+UG28) | ≈550-600(推定) |
| W3 | 対称 / 三角不等式違反(1 m 許容) / 到達不能対 | 0 / 0 / 0 | 0 |
| W4 | PLATEAU照合 / 中央値 / 最大 | 3,531 / 14.3 / 231.0 | 3,531 / 14.3 / 231.0 |
| W5 | 駅出口 / 全入口が歩行ノード集合内 | 45(全て層付きセル) / True | 45 / True |
| W6 | POI建物紐付け率 / 組織 | 0.688 / 9,872/9,872 | 68.8% / 9,872 |
| W11 | 出口→セル / floorguide接続 | 45/45 / 22 | 45 / 22 |

成果物: data/world/v2/(20資産+8ヘッダ+build_manifest.json・49 MB・gitignore下)。expedient は世界データ構築仕様 §4 の C1 節に登録。

注記(親の判断): 街区は Euler 数 1,242(仕様一致)と幾何面 1,227 を両方保持(層0描画に未タグ立体交差11件)。平面化は行わない(設計書の決定項に触れないため)。学校10校は組織表外(ヘッダに記録)。

## 2. 場・境界側(サブB: W7・W10・W12・W13)= 親検収済み(ゲート3件がデータ由来で不合格・処置中)

親の実行:
```
$ .venv/Scripts/python.exe -m shibuya.build.run --out data/world/v2
stages = W0,W1,W2,W3,W4,W5,W6,W7,W10,W11,W12,W13   (9.8 s)
build_hash = 629e8058c6e4e142a87e6ba8329584e4b80be69f0ef90f252d424bb002155b65
FAIL: W10 primary_secondary_sections_matched 0 (期待202) / W10 calibration_max_abs_residual_db 7.3 (≤3) / W13 days_with_missing_hours 28 (0)
$ pytest tests/build_field → 58 passed   $ lint-imports → 5 kept, 0 broken   $ scan_secrets → CLEAN
```

| 段階 | ゲート | 実測 | 判定 |
|---|---|---|---|
| W7 | PlanSpec 行 / 既定表の cat×subcat 全被覆 / 法規上限超過 | 2,337 / 0 欠 / 0 | PASS |
| W7 | OSM opening_hours 候補 / 解析成功 / 適用(src別 osm/chain/category) | 565 / 562(99.5%) / 477・59・1,801 | PASS |
| W10 | 街路点(2.5 m・8 m バッファ・層別) | 356,732(GL 326,849/DECK 19,497/UG 10,386) | 報告(仕様の239,028は v1 の klass 集合) |
| W10 | primary/secondary の区間突合 | **0**(辺に道路名なし・センサスに座標なし) | **FAIL→処置中** |
| W10 | 較正点残差(6点評価) | 渋谷区3点 ±1.4 dB / No.81 −3.8 / No.61 +5.1 / No.75 +7.3(遮音壁あり・ΔL=0) | **FAIL→処置中** |
| W12 | 外界ノード / 各ノードにセル / メトロ実ダイヤ行 / 重み和 | 10 / 全 / 1,596(05:01–24:20) / 1.0 | PASS |
| W12 | 鉄道流入/PT鉄道着 比 | 5.54(直通運転の二重計上=上界・相対重みのみに使用) | 報告 |
| W13 | 35日 / 全24時間の日 / 欠測あり | 35 / 7→**35** / 28→**0**(親レーン: 気象庁 etrn 時別値で 301 時間を補完・src 列で amedas/etrn を区別・台帳行追加) | **PASS(09-08 処置後)** |

処置(親): (1) W13=**完了**(気象庁 etrn 時別値 35日×24時を取得・欠測 301 時間を補完・build_hash 更新)。(2) W10 区間突合=PLATEAU CityGML の元ファイルは既にローカルに無く、tran_lod3.json にも路線名なし→OSM 道路名の再取得(Overpass=公的ドメイン外)が必要=**停止句(c)相当として PENDING に記録・ユーザー判断待ち**(推奨=再取得)。他工程はこの判断に依存しないので継続。(3) 較正残差は(2)の後に再評価。

## 3. 可視性・影(W8・W9)= 親検収済み(W9 の容量宣言超過1件=ユーザー判断)

```
$ .venv/Scripts/python.exe -m shibuya.build.run --out data/world/v2
stages = W0,W1,W2,W3,W4,W5,W6,W7,W8,W9,W10,W11,W12,W13,W18,W19,W20   (12.3 s・W10 7.9 s が支配)
build_hash = 775ec9d6dd73e07e144844d276f7849e23036babb7949d9e3c0a9ecd4dcd4042   (別ディレクトリ再構築で一致=サブ報告・親は本ディレクトリ2回で一致)
FAIL: W10 ×2(既知・PENDING) / W9 shadow_bytes_per_day_le_10mb 12,842,624 > 10,000,000
$ pytest → 408 passed in 80.56s   $ lint-imports → 5 kept, 0 broken   $ scan_secrets → CLEAN
```

| 段階 | ゲート | 実測 | 判定 |
|---|---|---|---|
| W8 | 視点 / 対象 / 出力 / 平均可視対象 / 可視0の視点率 | 356,732 / 9,592 / 5.87 MB(≤512 MB) / 14.5 / 3.6% | PASS(前計算 1.15 s ≤5 分) |
| W8 | T2 対称・単位範囲・層分離違反 | True / True / 0 | PASS |
| W9 | 夜間面=全影 / 正午影率 | True / 0.204(2026-07-28・日中 167 面) | PASS |
| W9 | 容量/日(5分 bitset・288面) | **12.84 MB > 10 MB(D-W10 宣言)** | **FAIL→PENDING(親推奨=宣言改訂)** |

親の目視(検収パック): cells.png=GL セル格子と POI 点(駅周辺が明るい)・noise_day.png=道路網の騒音場(幹線が明るい)を確認。

## 4. W18 被覆指標・W19 manifest 凍結・W20 検収パック = 親検収済み

| 段階 | 結果 |
|---|---|
| W18 | 5値ベクトル C 0.295 / C_quantified 0.192 / Q 0.196 / D 0.208 / V 0.0 / R null・X 0.004(セル 520 vs 453)・孤児 0・カタログ SHA 34f9fa9d316587be 一致・実装 15/57・死蔵候補 3・カタログ外の宣言 3(v0.3 候補=PENDING) |
| W19 | データ資産 67 件(欠落 0)・holdout 封印 S(kddi_la/shibuya_jinryu/boundary_counts)・構築コードの holdout 参照 0(静的検査)・部分ハッシュ W0-W18 |
| W20 | acceptance/ cells.png・exits.png・noise_day.png・visibility.png・shadow_noon.png・gate_table.md・summary.json(16 段階・上流 FAIL 3) |

## 5. C1 出口の判定

- 受入列「段階ゲート表全合格・再構築で build_hash 一致・検収パック」のうち、**再構築一致と検収パックは達成**。ゲートは 3 件が未達で、いずれも**設計書の宣言/外部取得に触れる分岐**(W10 区間突合=Overpass 再取得の可否・W10 較正残差=同・W9 容量=宣言値)=停止句(a)(c)相当として PENDING に記録(親推奨つき)。これらは C2〜C4 の作業に依存されないため、作業は継続する。
- expedient は世界データ構築仕様 §4 の C1 節(地理/場・境界/可視性/監査)に登録。

## 6. 層2 独立検収(別インスタンスの Fable)

**判定: 不合格(条件付き)**。レビュー役の実行: 再構築 A/B(scratchpad)と本ディレクトリの 68 ファイルが全て byte 一致・build_hash 775ec9d6…・129 ゲート中 FAIL 3(既知の W9/W10×2 のみ)/pytest 134 passed/lint 5 kept/scan CLEAN/holdout 参照は w19_freeze の封印定義のみ/§0-1 ヘッダ(input_hash/param_hash/stage_version)A/B 一致/`git diff main -- docs/design/`=§4/§8 への追記のみ/独立スポットチェックで仕様値(186,741 m・453/785/1,242・3,531/14.3/231.0・45・0.688/9,872・2,337・35日・34f9fa9d)を再構築ヘッダから確認。

不合格の理由と処置:
| 指摘 | 処置 |
|---|---|
| 受入列「段階ゲート表全合格」未達(FAIL 3=W9 容量宣言・W10 区間突合・W10 残差) | **ユーザー判断待ち(PENDING・停止句(a)(c)相当・親推奨つき)**。C2〜C4 は依存しないので継続 |
| 同語反復ゲート5本(W7 plan_spec_rows/intervals_over_law_cap・W8 t1_rows・W10 road_edges_with_traffic・W5/W11 出口→セル) | 修正サブ(C1-fix)で実検査へ |
| W10 区間突合ゲートの `passed=False` 固定 | (b)採択時に「対応表が空のとき報告のみ」へ。決定まで現状維持 |
| W7 法規上限が閉店側のみ(開店側の禁止時間帯未適用) | C1-fix で開店側も適用+単体テスト |
| W12 土休ダイヤの死コード・PM ピーク=AM 流用 | C1-fix で修正・notes に明示 |
| run.py `--stage` 部分実行で古いヘッダが manifest に混成 | C1-fix で partial manifest を別名出力 |
| test_w10_noise が較正 3 点のみ検査 | 7 点要件を xfail(PENDING 参照)として可視化 |
| expedient 未登録(W10 縮尺表ほか) | §4 へ追記済み |

持ち越し(C3〜C5): W10 の場は expedient 駆動(klass 既定+ΔL=0+首都高不在)=C3 の B4 騒音段・C4 の騒音過程へ結線する前に (a)/(b) 決定+感度試験(既定交通量±50%)を結線条件に/街路点 356,732 vs 仕様 239,028 の差=D-W9/D-W10 の数値改訂(ユーザー)を C5 の W18 再算出前に/カタログ v0.3(外界ノード・境界流量・体感温度+死蔵候補 3)の凍結を C5 前に。

## 7. 修正後の親検収(C1-fix 反映・09-08)

```
$ .venv/Scripts/python.exe -m shibuya.build.run --out data/world/v2
build_hash = f5566f5fcea86294018ebf8d2bae12fb8e1b439f06a277ecc616be168a6616e0   ゲート 145 / FAIL 3(既知のみ)
$ pytest tests/build_* → 144 passed, 1 xfailed(W10 7点≤3 dB=PENDING を可視化)   $ lint-imports → 5 kept   $ scan → CLEAN
```
同語反復ゲート5本→実検査(W7 2337 固定・法規上限 before/after・W8 t1=w10 視点数+索引一意・W10 道路辺 2,493/2,493・W5/W11 自セル実在 0 欠)。W7 開店側の禁止時間帯を適用(前 119 区間が窓に掛かり→後 0)。W12 土休比 0.9778。部分実行の manifest 混成を解消。検収パックに build_hash(W0..W19 範囲)を埋め込み。

**C1 の状態=条件付き完了**: 受入列のうち再構築一致・検収パックは達成、ゲート 3 件はユーザー判断(W9 宣言改訂/W10 道路名再取得)待ち。判断後に該当段階のみ再実行し、本報告を更新する。