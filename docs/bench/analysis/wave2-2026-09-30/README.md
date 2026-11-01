# 第 2 波(2026-09-30)の記録

> 節ごとに担当が別(§W10 = W10 の道路名 ON+Q7 と物差し Q6)。他の節は別の担当が足す。

## §W10 道路名の対応表 ON+絞り込み Q7 と物差し Q6(指示書 §5・§8-2・本段では昇格しない)

> 実行役サブ(Opus 5.5)の記録・親の検収前。**世界資産(`data/world/v2`)は上書きしていない**(作業の前後で直下 109 ファイルの md5 が一致=§W10-7)。構築の出力はすべて OS の一時ディレクトリ(リポの外)。
> 実装: [`build/field/w10_ruler.py`](../../../../src/shibuya/build/field/w10_ruler.py)(新規・物差し)・試験 [`tests/build_field/test_w10_ruler.py`](../../../../tests/build_field/test_w10_ruler.py)(新規 40 件)。
> **検収の反映(09-30・[検収の記録](review-w10.md))**: 結論 4 の数値の誤りを直した・住所の解析を丁目の番号だけの正規化に改め、突合できない点を理由コードの行で返す・`road` に距離と帯の外の印を併記・昼夜の `road` を同じ格子点から読む・NaN で止める・投影は正典の関数を呼ぶ・実資産が無ければ skip・見出しの数値を試験で固定・手順書に抜け 3 項を足した。物差しの値そのものは直す前と**同じ**(同距離の決め方を変えても 3 点の値は不変=JSON で確認)。`w10_noise.py`・`road_names.py` は**変更なし**(既存の切替口をこのプロセスの中でだけ書き換えて構築)。
> 計測: [w10_ruler_measure.py](w10_ruler_measure.py)(`build`=検算→OFF/ON+Q7 の構築→物差し / `world`=15 腕用の世界の写し / `checkpoint`=新旧の束ね)。ファイル: [w10_ruler.json](w10_ruler.json)・[w10_checkpoint.json](w10_checkpoint.json)。
> **未リサーチ(expedient)**: 物差しの構成(代表点 2 通り・半径 3 通り・代表値 2 通り・R5 の道路種別 → 辺の階級の表)は実行役の自前の構成。

### W10-0 結論

1. **切替口 OFF(既定)の W10 の出力 6 本は、昇格版の `build_manifest.json` と sha256 が一致**(騒音場 4 本・街路点・対応表)。既定の構築は 1 バイトも動いていない(試験 `test_switch_off_reproduces_the_promoted_w10_outputs`)。
2. **ON+Q7 の資産**(`USE_ROAD_NAME_MATCH=True`・`ROAD_NAME_REQUIRE_NAMED_SAME_CLASS=True`・Q9=False)を一時ディレクトリに構築し、[段 1c の記録 §1c′](../w10-roadnames-2026-09-28/README.md) の値が**すべて再現**した: 当てた辺 **225**・primary+secondary **202/202(PASS)**・階級の不一致 **0**・既定比の最大 **10.0 倍**・騒音場 昼 50/95 % 点 66.4/78.1・夜 62.4/74.4・騒音段階が変わるセル(520 中)昼 **27**/夜 **22**・路線別の辺数(305:94・413:44・317:33・432:23・412:23・423:8)。
3. **物差し(Q6)で測れるのは 7 点のうち 3 点だけ**(No.78・79・82)。No.61(目黒区)・No.75(世田谷区)は町丁目の境界がリポに無い、No.80 広尾五丁目・No.81 本町一丁目は**世界の範囲の外**(町丁目に街路格子が 1 点も無い)。
4. ON+Q7 にしたときの物差しの値の動きは **−3〜+2 dB**(12 通り × 3 点 × 昼夜)。最大は No.82 の `road_facing`/max/r25 の夜 +6 → +3(**−3**)。e-Stat の代表点では No.78・79 は動かず、No.82 が max(−1〜−2)と `road`/r100(+15/+14 → +14/+12)で動く。道路に面した点では No.78 +1〜+2・No.79 0〜+1・No.82 −1〜−3。**判定はしない**(下の誤差の大きさを参照)。
5. **物差しの誤差は ON/OFF の差(−3〜+2 dB)より大きい**(−3 dB に直しても結論は同じ): 代表点の選び方で差が 10 dB 前後動き、騒音場は道路の上(車道中心線から 8 m 以内)で評価される一方で実測は車道端から 3.7〜6 m の路側=同じ式で「中心線上 − 実測の位置」が +6〜+9 dB。No.79 以外は代表点が「測った道路」の上に乗っていない。
6. **15 腕の checkpoint は全腕が動く**(OFF の値は現行 golden と一致=写しの手順の検算)。v3 既定 `993276d5` → `72412e3e`(69,978 → 69,975 呼)・帰無腕 `72cb9cd5` → `dade8e9e`(100,439 → 100,372)。**本段では昇格していない**。

### W10-1 事実の確認(いまの較正は辺も騒音場も通らない)

`w10_noise.calibrate` は R5 の CSV の各点の**路線名**でセンサスの区間を引き、CSV の車線数・車道端距離・低騒音舗装で ASJ の式を評価するだけ(点に座標が無い)。ON+Q7 の構築でも較正の残差は OFF と同一(No.61 +5.1/+4.5・No.75 +7.3/+6.4・最大 7.3=ゲート FAIL のまま)。したがって突合の良し悪しはいまの残差では測れない(段 1c の記録 §3 と同じ)。

### W10-2 物差しの作り方(**未リサーチ(expedient)**)

- **座標の材料**: 国勢調査 2020 小地域境界(e-Stat `r2ka13113`・W16 が読むもの・渋谷区の 80 町丁目)。R5 の所在地の欄 → 町丁目名(`神宮前5丁目53-1` → `神宮前五丁目`・`鉢山町14` → `鉢山町`)。**正規化は丁目の番号だけ**(町名の漢数字=三田・六本木・四谷 などは変えない)。突合できない点は例外にせず理由コードの行で返す: `NO_BOUNDARY`(区の境界が無い)・`NAME_NOT_FOUND`(区の境界はあるが町名が無い)・`AMBIGUOUS_NO_CHOME`(`神宮前5-53-1` のような丁目の無い書き方でその町に丁目がある)・`UNPARSEABLE`(区が読めない)・`OUTSIDE_WORLD`。Web からの取得はしていない。
- **代表点(2 通り)**: `estat`=.dbf の `X_CODE`/`Y_CODE`(e-Stat が小地域ごとに付けた代表点・3 点とも町丁目の中・面積重心から 0.3 m)/ `road_facing`=町丁目の中の地上(GL)の街路格子点のうち、最寄りの辺が「測った道路の階級」(R5 の道路種別 3/4/6 → primary・secondary、5=区道 → 音源の klass 全部、1/2=高速 → 辺なし)で、`estat` の点に最も近いもの。
- **代表値(2 通り)× 半径 r(25/50/100 m)**: `max`=r の中の GL 格子点の最大値 / `road`=r の中で「測った階級の辺」までの距離が最小の格子点の値(同距離は格子の番号の小さい方=**昼と夜は同じ格子点**)。**距離に上限は付けない**が、距離(`road_dist_m`)を必ず併記し、騒音場の格子の帯(辺の中心線から 8 m・D-W9)を超えるものに印(`road_beyond_band`・表の ※)を付ける=その値は「測った道路の値」ではなく近くの別の道の値。値・距離に NaN があれば止める(いまの資産は uint8 で起きない)。差=代表値 − 実測(昼/夜)。騒音場は uint8 に丸めた dB(±0.5 dB)。
- **検算(読む前に)**: 合成の騒音場(200 m 四方の町丁目・y=50 に幹線 70/66 dB・y=−50 に住宅地 55/51 dB・(0,80) に 90/86 dB)で、7 通りの既知の差(例 `estat`/max/r50 = +5/+6・r100 = +25/+26・`road`/r100 = +5/+6)を返すことを確かめた(計測の道具の冒頭で毎回・合わなければ止める)。騒音場を一様に +3 dB すると全ての差がちょうど +3 動くこと(線形性)・場の 1 点(代表点から 80 m)だけを +20 dB すると r=100 の max だけが +20 動き r=25/50 と `road` は動かないこと(幾何の検算)も試験にした。

### W10-3 物差しの値(差=値 − 実測 [dB]・昼/夜・OFF → ON+Q7)

| 代表点 | 代表値 | r [m] | No.78 OFF → ON | No.79 OFF → ON | No.82 OFF → ON | road の距離 78 / 79 / 82 | 平均 OFF → ON(n) |
|---|---|---|---|---|---|---|---|
| estat | max | 25 | +2/+0 → +2/+0 | — → — | +3/+2 → +3/+1 |  | +2.50/+1.00 → +2.50/+0.50(2) |
| estat | max | 50 | +5/+3 → +5/+3 | +0/-3 → +0/-3 | +14/+13 → +12/+11 |  | +6.33/+4.33 → +5.67/+3.67(3) |
| estat | max | 100 | +5/+3 → +5/+3 | +6/+3 → +6/+3 | +16/+15 → +15/+13 |  | +9.00/+7.00 → +8.67/+6.33(3) |
| estat | road | 25 | -4/-6 → -4/-6 | — → — | +3/+1 → +3/+1 | 265 m ※ / — / 0.1 m | -0.50/-2.50 → -0.50/-2.50(2) |
| estat | road | 50 | -1/-3 → -1/-3 | -10/-13 → -10/-13 | +3/+1 → +3/+1 | 234 m ※ / 114 m ※ / 0.1 m | -2.67/-5.00 → -2.67/-5.00(3) |
| estat | road | 100 | -6/-8 → -6/-8 | -7/-10 → -7/-10 | +15/+14 → +14/+12 | 192 m ※ / 45 m ※ / 0.0 m | +0.67/-1.33 → +0.33/-2.00(3) |
| road_facing | max | 25 | +11/+9 → +12/+11 | +15/+13 → +15/+13 | +7/+6 → +5/+3 |  | +11.00/+9.33 → +10.67/+9.00(3) |
| road_facing | max | 50 | +11/+9 → +13/+11 | +16/+14 → +17/+14 | +15/+14 → +13/+12 |  | +14.00/+12.33 → +14.33/+12.33(3) |
| road_facing | max | 100 | +11/+9 → +13/+11 | +16/+14 → +17/+14 | +16/+15 → +15/+13 |  | +14.33/+12.67 → +15.00/+12.67(3) |
| road_facing | road | 25 | +9/+7 → +11/+9 | +14/+12 → +14/+12 | +3/+1 → +3/+1 | 0.1 m / 0.1 m / 0.1 m | +8.67/+6.67 → +9.33/+7.33(3) |
| road_facing | road | 50 | +10/+8 → +12/+10 | +12/+10 → +13/+10 | +6/+4 → +5/+3 | 0.0 m / 0.0 m / 0.0 m | +9.33/+7.33 → +10.00/+7.67(3) |
| road_facing | road | 100 | +10/+8 → +12/+10 | +12/+10 → +12/+10 | +15/+14 → +14/+12 | 0.0 m / 0.0 m / 0.0 m | +12.33/+10.67 → +12.67/+10.67(3) |

| 代表点 | r [m] | road(帯の中だけ)平均 OFF → ON(n) |
|---|---|---|
| estat | 25 | +3.00/+1.00 → +3.00/+1.00(1) |
| estat | 50 | +3.00/+1.00 → +3.00/+1.00(1) |
| estat | 100 | +15.00/+14.00 → +14.00/+12.00(1) |
| road_facing | 25 | +8.67/+6.67 → +9.33/+7.33(3) |
| road_facing | 50 | +9.33/+7.33 → +10.00/+7.67(3) |
| road_facing | 100 | +12.33/+10.67 → +12.67/+10.67(3) |

- ※=`road` の格子点が測った階級の辺から 8 m(格子の帯)より遠い=**道路の値ではない**。`estat` の点では No.78(192〜265 m)と No.79(45・114 m)がすべて帯の外。帯の中だけの `road` の平均は下の表(`estat` は No.82 の 1 点だけ)。距離は OFF と ON+Q7 で同じ。No.82 の `estat`/road/r100 は距離 0.0 m だが区道(音源の klass 全部)の別の道。
- 代表点がどの道の上か: No.78 の `road_facing` は **413 赤坂杉並線**(secondary・測った道路は国道 246)=**測った道路とは別の道**(e-Stat の点から 278 m)。No.79 の `road_facing` は **317 環状六号線**(primary)=測った道路(環状 6 号線)と一致(140 m)。No.82 の `road_facing` は residential(区道・11 m)。`estat` の点は 3 点とも住宅地・service の辺の上。
- ON+Q7 で動くのは、代表点の近くに**当てた辺**(413・317・305)がある所だけ。国道 246 は Q7 で外れる(段 1c′)ので No.78 の測った道路は ON でも klass 既定のまま。
- 平均は 3 点(r=25 の `estat` は No.79 の 25 m 内に GL の格子点が無く 2 点)。半径の効き方: `max` は r を広げるほど大きくなる(遠くの幹線を拾う)・`road` は r=25→50 ではほぼ同じで r=100 で別の道に乗り替わる点がある(No.78 の `estat`・No.82)。代表点の効き方: `estat` → `road_facing` で平均が +5〜+12 dB 動く。**どれが効くかを 1 つに決めない**(指示どおり)。

### W10-4 物差しの誤差の大きさ(見積り)

| No. | 町丁目の等価半径 | e-Stat 点 → 道路に面した点 | 町丁目の中の「測った階級の道路」の格子点の値 5/50/95 %(昼) | 中心線上 − 実測の位置(同じ式・同じ区間) | 実測の位置の中心線からの距離 |
|---|---|---|---|---|---|
| 78 | 286 m | 278 m | 75 / 77 / 79 | +8.9 | 16.0 m(8 m の格子の外) |
| 79 | 185 m | 140 m | 78 / 79 / 81 | +6.4 | 10.7 m(格子の外) |
| 82 | 205 m | 11 m | 60 / 67 / 80 | (較正不能=区道) | — |

- **位置の誤差**: 実際の測定点は町丁目の中のどこか(等価半径 185〜286 m)。町丁目の中の道路の格子点だけでも値が 5〜95 % 点で 3〜4 dB(幹線の No.78・79)〜20 dB(区道を含む No.82)ばらつく。
- **系統差**: 騒音場の格子は辺の中心線から 8 m 以内(D-W9)にしか無く、実測の位置(車道端から 3.7〜6 m・No.78/79 は中心線から 10.7/16.0 m)は**格子の外**。同じ式で中心線上と実測の位置を比べると +6〜+9 dB(`centerline_offset`・較正行の丸めた区間値による近似)。`road_facing`/`road` の差(+9〜+14)の大部分はこの系統差で説明できる大きさ。
- ON と OFF の差(−3〜+2 dB)は、この位置の誤差・系統差より小さい。

### W10-5 15 腕の checkpoint(mock 5,000 体・seed 1・1 シミュ日)

- **回した src**: `git archive HEAD`(`b4c8b1c`)を OS の一時ディレクトリに展開した写し(`PYTHONPATH`=写しの `src`・`shibuya.__file__` が写しを指すことを確認)。**作業木の src は import していない**(別のサブがエンジンを編集中のため)。計測は写しの中の [w6_regen_measure.py](../w6-regen-2026-09-28/w6_regen_measure.py)(`run`・`collect`)。
- **世界**: `data/world/v2` の直下 109 ファイルの写し 2 つ(OFF=そのまま / ON+Q7=W10 の出力 6 本とヘッダを差し替え)。置き場所はリポと同じ並び(`<一時>/data/world/v2_*`)にし、街路施設の JSON(`data/realworld/osm/street_features_overpass_20260907.json`)も同じ並びに複写した=エンジンは `world_dir.parent.parent/realworld/osm` に探し、**無ければ黙ってバス運行を休む**(`world/assets.py` の `_street_features_path`)ため。
- **検算**: OFF の写しの値が現行 golden と一致(帰無腕 `72cb9cd52982da74` / 100,439・v3 既定 `993276d5e5bb5cbe` / 69,978=`W17_GOLDEN["3113e9ba7abb"]`)。
- 保存則(conserved)は ON+Q7 の全腕で True。

| 腕 | final OFF → ON+Q7 | 呼数 OFF → ON+Q7 | 起床条件の増減(主なもの) |
|---|---|---|---|
| v3_default | `993276d5e5bb5cbe` → `72412e3eb8b97137` | 69,978 → 69,975(-3) | ACTIVITY_EXPIRY -3, CELL_BLOCK +1, INTEROCEPTION -1 |
| v3_activity_off | `f746406eb78b024a` → `d54f50fc087a0f3d` | 58,570 → 59,363(+793) | CELL_BLOCK +676, CONVERSATION_TURN +110, INTEROCEPTION +31 |
| v1_default | `0a52a4d3a90fa79f` → `93c77098778a4913` | 60,970 → 60,625(-345) | CELL_BLOCK -336, INTEROCEPTION -47, CONVERSATION_TURN +44 |
| v1_derive_v2_1 | `faada6a938570ef1` → `4e10ed0a16a52731` | 54,285 → 54,387(+102) | CELL_BLOCK +86, INTEROCEPTION +10, CONVERSATION_TURN +7 |
| v2 | `f4382c82dfa21764` → `6a3c472830934cc6` | 60,901 → 60,969(+68) | CELL_BLOCK +35, CONVERSATION_TURN +30, INTEROCEPTION +3 |
| v1_edge | `6db51cbd2b401129` → `dbaafc8b5dad2f3e` | 54,150 → 54,236(+86) | CELL_BLOCK +50, CONVERSATION_TURN +25, INTEROCEPTION +12 |
| v2_edge | `d61923edade6f05c` → `5bb9d36a976f3078` | 54,170 → 54,223(+53) | CELL_BLOCK +44, CONVERSATION_TURN +8, INTEROCEPTION +2 |
| v1_edge_plateau | `e32d69e91ff45e66` → `9e412bc520c54ca3` | 55,173 → 55,245(+72) | CELL_BLOCK +61, CONVERSATION_TURN +6, INTEROCEPTION +4 |
| old_v1_default | `e1fcd39b618dc768` → `cc655a46d75ed3a1` | 60,970 → 60,625(-345) | CELL_BLOCK -336, INTEROCEPTION -47, CONVERSATION_TURN +44 |
| old_v1_derive_v2_1 | `46ca40a12eb54d58` → `69f56a6f957d7939` | 54,285 → 54,387(+102) | CELL_BLOCK +86, INTEROCEPTION +10, CONVERSATION_TURN +7 |
| old_v2 | `7c7d2423307fe571` → `d245beecf31ac277` | 60,901 → 60,969(+68) | CELL_BLOCK +35, CONVERSATION_TURN +30, INTEROCEPTION +3 |
| old_v1_edge | `951af158650b2fc2` → `6d753caf0bfe161d` | 54,150 → 54,236(+86) | CELL_BLOCK +50, CONVERSATION_TURN +25, INTEROCEPTION +12 |
| old_v2_edge | `cf01958883d07209` → `a1deea5a9efd1b2e` | 54,170 → 54,223(+53) | CELL_BLOCK +44, CONVERSATION_TURN +8, INTEROCEPTION +2 |
| old_v1_edge_plateau | `b94df1eb4c5b5557` → `e0da23abfed33964` | 55,173 → 55,245(+72) | CELL_BLOCK +61, CONVERSATION_TURN +6, INTEROCEPTION +4 |
| golden_null_arm | `72cb9cd52982da74` → `dade8e9ec440d378` | 100,439 → 100,372(-67) | CONVERSATION_TURN -45, INTEROCEPTION -19, CELL_BLOCK -4 |

- 段 1c の記録の 3 腕の値(v3 既定 `02bd0312` → `2f6dbc72` ほか)は 09-28 のエンジンでの値で、その後の段(2a〜9a)でエンジンの既定が動いたので本表の OFF と直接は比べられない(本表の OFF は HEAD のエンジンで回し直した値)。
- 動きの中心は場所の起床(CELL_BLOCK: v3 活動層 off +676・v1 既定 −336)=セルの騒音段階の変化(昼 27・夜 22 セル)が B4 の文面を動かす(段 1c の記録 §参考 と同じ機序)。
- 注意: run manifest の `frozen_sources` は OFF と ON+Q7 で**同じ**(W10 の騒音場のファイルが載っていない)=ランの記録から、どちらの騒音場で回したかが分からない。

### W10-6 昇格の手順書(版上げ 1 回目=D-102 アジェンダ §5 の 4 で親が実行・**本段では実行していない**)

1. **定数の切り替え**(`src/shibuya/build/field/w10_noise.py`): `USE_ROAD_NAME_MATCH = True`・`ROAD_NAME_REQUIRE_NAMED_SAME_CLASS = True`(`ROAD_NAME_REQUIRE_SAME_BAND` は False のまま=Q9 不要)。`STAGE_VERSION` を `1.1.0` → `1.2.0` に上げ(版の意味=「ON+Q7 が既定」)、docstring・`road_name_match_off_reason`・`section_match_diagnosis` の既定 OFF の文言を直す。param_hash はフラグが params に入っているので自動で変わる。
2. **再構築**(〜25 分・段 1c と同じ): `python -m shibuya.build.run --out data/world/v2 --data data --keep-stage W17`。W10 以外で出力が変わるのは W18(ヘッダ)・W19(資産表)・W20(受入パックの騒音図とゲート表)の見込み。街路点(W8/W9 の入力)は ON でも同じ sha256 なので W8/W9 は不変のはず=**確認項目**。ゲート `calibration_max_abs_residual_db` は 7.3 で FAIL のまま(終了コード 1 は段 1c と同じ)。
3. **確認**: 新しい `build_manifest.json` の W10 の出力の sha256 が本記録の ON+Q7(`w10_noise_day.npy` `022121e08d50…`・`w10_noise_night.npy` `f8cccfd43766…`・`w10_noise_stage_day.npy` `e760a6dcbcb0…`・`w10_noise_stage_night.npy` `9cd06ebd13d2…`・`w10_edge_section.parquet` `6bd90df45034…`・`w10_street_points.parquet` `de1340b15bda…`=不変)と一致すること。2 回構築してバイト一致。
4. **旧資産の保全**: 昇格前の W10 の出力 6 本+`W10.header.json`(と W18〜W20)を `data/world/v2_pre_w10on_<日付>/`(gitignore 下)に退避(段 1c と同じ流儀)。D-102 アジェンダ §5 の 6「W10 OFF の資産で旧値を再現」に使う。
5. **張り替える golden(候補・昇格後に回して実際に落ちたものだけ直す)**:
   - W10 の試験: `tests/build_field/test_w10_road_names.py`(`test_w10_declares_the_switch_and_the_input` の既定値・`test_w10_default_off_noise_field_equals_the_pre_1c_asset` は OFF を monkeypatch で明示する形へ)・`tests/build_field/test_w10_ruler.py`(`test_switch_off_reproduces_the_promoted_w10_outputs` → 「既定(ON+Q7)が昇格版と一致」+「OFF は旧 sha256(本記録 W10-5 の OFF=`6f3e3b0f2b4c…` ほか)と一致」に分ける)。
   - エンジンの checkpoint(実世界資産で final を固定する試験・grep で `final_hash` と世界資産を両方参照するもの): `tests/engine/test_presence_executor.py`(`W17_GOLDEN["3113e9ba7abb"]` の 8 値)・`tests/engine/test_intent_chooser.py`(legacy 2 値)・`tests/engine/test_area_source_c9c.py`・`test_c9b_targets_attention.py`・`test_eatery_place_food.py`・`test_familiarity.py`・`test_geometry_c9.py`・`test_presence_exit_walk.py`・`test_relations.py`・`test_relations_8b.py`・`test_wom.py`・`tests/perception/test_near_tiebreak.py`・`tests/test_cli.py`・`tests/c6/test_t3_parallel_invariance.py`・`tests/c7/test_accept_table.py`・`tests/build_pop/test_pop_pipeline.py`(D-102 アジェンダ §5 の 5 の「golden 13 値」を含む)。新しい値の目安=本記録 W10-5 の ON+Q7 列(ただし版上げ 1 回目は D-102 Q1/Q8/Q9 と束ねるので、実際の値は束ねた後に回し直す)。
   - 交通の過程: `tests/engine/processes/test_traffic.py::test_klass_defaults_match_the_w10_header`(W10 のヘッダの `census_defaults` と転記の一致。klass 既定の値は ON でも変わらない見込み=通るはずだが候補に入れる)。W10 の OFF の sha256 の先頭は `tests/build_field/test_w10_road_names.py` の 232〜235 行にもある。
   - 記録: `W19` の資産表・版の台帳・[段 1c の記録](../w10-roadnames-2026-09-28/README.md) の冒頭「既定 OFF」の注記。
6. **静的な騒音場と動的な交通の食い違い(扱いは親への問い Q-W10e)**: `engine/processes/traffic.py` は W10 の klass 既定(`KLASS_Q12`/`KLASS_Q24`=`census_defaults` の転記)で動き、`w10_edge_section` の区間別の交通量を読まない(HEAD で確認)。ON を既定にすると、静的な騒音場は区間別(225 辺が路線の実測)・動的な交通は klass 既定になる。版上げの前に「食い違いを宣言するか・揃えるか」を決める。
7. **版上げの前に決める項**: Q-W10c(OFF の旧値を再現する資産の置き場)と Q-W10d(run manifest の `frozen_sources` に騒音場が載らない)。どちらも決まらないまま昇格すると、旧値の再現試験が書けない/ランの記録から ON/OFF が分からない。

### W10-7 世界資産の不変・触っていないもの

- `data/world/v2` 直下 109 ファイルの md5 の一覧が作業の前後で**同一**(一覧の md5 `1e833fcc98f5…`)。昇格(promote)は使っていない。構築・ランの出力はすべて OS の一時ディレクトリ。
- 触っていない: `w10_noise.py`・`road_names.py`(定数も既定のまま)・エンジン・知覚・CLI・台帳・設計書・holdout(`shibuya_jinryu`・`boundary_counts`)。

### W10-8 問い(親へ)

- **Q-W10a(物差しの点が 3 点)**: 7 点のうち騒音場で測れるのは 3 点(うち代表点が測った道路に乗るのは No.79 だけ)。No.61 を足すには目黒区の小地域境界(e-Stat `r2ka13110`)が要る(世界の中かは未確認)。R5 の全都内の測定点のうち世界の範囲に入る点を探し直すか(R5 の CSV には座標が無い=同じ手順)。
- **Q-W10b(系統差)**: 騒音場は道路の上で評価され、実測は路側(格子の外)。物差しを「道路の辺から実測の距離の位置で式を評価する」形(騒音場ではなく辺ごとのエネルギー係数を読む)に変えるか。いまの 2×3 の物差しは系統差 +6〜+9 dB を含む。
- **Q-W10c(旧値の再現の置き場)**: 昇格後に OFF の旧値を試験で再現するには、W10 OFF の資産を別のディレクトリに置き、試験がそれで世界を組む必要がある(エンジンは世界ディレクトリ 1 つを読む)。退避先に W10 の 6 本だけ置いて試験の中で写しを組むか、エンジン側に騒音場の置き場の口を足すか。
- **Q-W10d(記録の穴)**: run manifest の `frozen_sources` に W10 の騒音場が載らない=ON/OFF の区別がランの記録に残らない。版上げの前に載せるか(エンジン側の変更=別の段)。
- **Q-W10e(静的な場と動的な交通)**: ON を既定にすると騒音場は区間別・`engine/processes/traffic.py` は klass 既定のまま(W10-6 の 6)。(a) 食い違いを宣言して進む (b) 交通の過程に対応表を読ませる(段 1c の記録の Q10・エンジンの変更) のどちらか。
- **Q-W10f(`road` の上限)**: いまは値を消さず印だけ(検収の案のうち「併記+印」)。上限を超えたら None にする方にするか。

## §2A 口コミの源・初期辺の在職期間・古典の腕の交際の相手・食事の門(実行役 Opus 5.5・親の検収前)

> 指示書 [v2-wallbounce-decisions-2026-09-30.md](../../../design/v2-wallbounce-decisions-2026-09-30.md) §0・§3-1・§4・§8。項ごとに「入れたもの・切替口・検算・byte-check・新旧の値・宣言・問い」。
> **byte-check の基準**: `git archive HEAD`(`b4c8b1c`)を OS の一時ディレクトリに展開した src と作業木で、同じ 19 構成(W6 再生成の 15 腕+本段で触る腕 4 本=店の記憶 on・関係 on・古典・古典+記憶+関係)を mock/classical 5,000 体・seed 1・1 シミュ日・テープつきで回し、final・呼数・blocks(行数と全列)・calls の 14 列(prompt_hash を含む)を比べた。`work`=作業木の既定・`work_old`=旧の切替口を**すべて**付けた作業木。スクリプト [wave2_bytecheck.py](wave2_bytecheck.py)(`side`・`compare`)。HEAD 側は `shibuya.__file__` が写しを指すことを行ごとに記録(`src_is_worktree`)。**検収後**: `compare` がこの欄を検査し、HEAD 側が作業木を読んでいた行・作業木側が写しを読んでいた行・エラー行があれば不一致として止まる(`src_checks`・作業木どうしを比べる自己検査で MISMATCH になることを確認)。
> 全体テストは回していない(親が回す)。holdout には触れていない。Web からの取得はしていない。

### 2A-0 結論

| 項 | 入れたもの | 切替口(既定=新 / 旧) | byte-check(15 腕) | 動いた腕 |
|---|---|---|---|---|
| 1 口コミの内心の漏れ | 語彙 v3 の口コミの抽出は発話の欄(ひと言)だけを読む=いまの v3 では抽出 0 | `--wom-source {utterance,reason-target}` | 15/15 一致・店の記憶 on も一致 | なし(店の記憶 on の mock も final 一致=mock の理由欄は店名を含まない) |
| 2 初期辺の在職期間のハッシュ | 在職期間の U を同点の順のハッシュと独立に・τ_rel を再逆算 −2.346 → **−2.322** | `--rel-tenure-hash {v2,v1}`(v1 のとき τ は −2.346) | 15/15 一致 | 関係 on の腕だけ |
| 3-1 古典の交際の相手 | 近接行の**話しかけられる知人**(会話中・就寝中・会話の届かない人を除く=検収後)のうち活性 A が最大の人・居なければ「なし・待つ」 | `--classical-social {acquaintance,near_first}` | 15/15 一致 | 古典の腕 |
| 3-2 古典の「まで」 | **実装していない=30 分固定のまま(宣言)**(候補 (a)(b) の差が大きく決められない・親の了承済み・選択肢はユーザーへ・2A-3b) | — | — | — |
| 4 食事の門を時間あたりに | `MEAL_WORD_P` を 1 時間あたりと読み、前回の門の後に**範囲内で起きていた分**で換算(定数は不変・検収後の親の決定) | `--meal-gate {per_wake,per_hour}`(**既定 per_wake=旧**) | 15/15 一致 | なし(既定は旧のまま) |

- **旧の切替口をすべて付けた作業木**(`wom_source=reason-target`・`rel_tenure_hash=v1`・`classical_social=near_first`・`meal_gate=per_wake`)は **19 構成すべてで HEAD と一致**(final・呼数・blocks・calls 14 列)。項ごとに回した: [item1_byte_check.json](item1_byte_check.json)・[item2_byte_check.json](item2_byte_check.json)・[item3_byte_check.json](item3_byte_check.json)・[item4_byte_check.json](item4_byte_check.json)(**検収後の直しの後=本段の最終**・15 腕 15/15・旧の切替口 19/19・`src_checks` ok)。項 4 は既定を動かさない(既定は per_wake)。
- 作業木の既定で動いた腕の final(HEAD → 作業木・呼数):

| 構成 | HEAD | 作業木(既定) | 動いた項 |
|---|---|---|---|
| v3・記憶 on・関係 on(mock) | `e4f84d1d176e6ec0` 72,940 | `40409ebed834126b` 72,930 | 2 |
| v3・classical | `60e7222783a221c6` 102,021 | `3390e3ec02d392a9` 97,563 | 3-1 |
| v3・classical・記憶 on・関係 on | `4fa23d558cf0eb79` 114,338 | `28ea80375e7ee646` 110,395 | 2 と 3-1(項 2 だけの後は `e3db0d32e8ecd8ee` 114,088・検収前の 3-1 の後は `102e4517805540d4` 110,431) |

### 2A-1 口コミの内心の漏れ(Q57 の確認の結果・[確認の記録](../wallbounce-0930/wom-leak-and-recall-ids.md))

- **入れたもの**: `engine/wom.py` に源の表 `WOM_TEXT_FIELDS_BY_SOURCE`(`utterance`=v1/v2/v3 ともひと言だけ・`reason-target`=旧=v3 は理由+対象)。`WomExtractor(source=…)`・`run_day(wom_source=…)`・CLI `--wom-source`。`WOM_TEXT_FIELDS` は既定の源の表(v3=`("comment",)`)。
- **manifest**: `wom.source` と `wom.text_fields`(源の表)。店の記憶が off のランは従来どおり `wom` は空。
- **いまの v3 では口コミの抽出は 0**: v3 のパーサはひと言欄を読まない(`labels.get("ひと言")` が無い=「なし」)。ひと言欄はユーザー決定 Q57 (d) で後から足す(本段では足していない)。
- **検算(テスト・`tests/engine/test_wom.py`)**:
  - (i) 理由欄にだけ店名がある v3 の応答(「一蘭が混んでいたので別の店を探す」・対象 `P-1`)→ 既定では読む文字列が空・抽出 0・聞き手の店の行は増えない。(ii) 同じ入力を `reason-target` で流すと、確認の記録 §1-2 の行(一蘭・向き −1・出どころ=伝聞・向き −0.25)が再現する。
  - 理由欄に店名と評価語を書く mock の包み(300 体)で、既定は `wom_extracted`=0・`store_rows_with_wom`=0・聞き手の行 0。旧のテスト(`a_talking_llm_writes_word_of_mouth_rows_for_listeners_only`)は `wom_source="reason-target"` を付けて旧の挙動(全発話で抽出・宛先の行)を固定。
  - (iii) mock 5,000・`--memory on --store-memory on`: HEAD `e89fc1cdc327cf57` と作業木の既定が一致(final・呼数 69,978・blocks・calls 14 列)=mock の理由欄は定型文で店名を含まない(想定どおり)。
- **テスト**: 新規 3 件(理由欄だけの応答・理由欄を書く LLM のラン・切替口と CLI)+変更 2 件(欄の表の等式・旧の挙動のテストに切替口)。
- **宣言**: 会話の要旨(40 字)の源が理由欄に戻る経路(`memory.note_utterance`)は漏れではないので触っていない(確認の記録 §1-3・Q57 (d) のアジェンダで扱う)。

### 2A-2 初期辺の在職期間のハッシュ(Q111 の解析で見つかった欠陥・[Q111 の記録 §5](../q111-capacity-2026-09-30/README.md))

- **入れたもの**(`engine/relations.py`): `_tenure_unit(src_u, src_v, version)`。v1=旧 `_pair_mix(min, max)`。**v2=その値に塩(`0xD1B54A32D192ED03`)を排他的論理和してから splitmix64 をもう 1 段**(全単射の非線形の混ぜ)。向きのない組なので u→v と v→u で同じ値のまま。`initial_edges(tenure_hash=…)`(監査 `init.tenure_hash`)・`run_day(rel_tenure_hash=…)`・CLI `--rel-tenure-hash`。網(誰と誰が結ばれるか)は版で変わらない(在職期間は選び方に入らない)=変わるのは初期辺の n・first と τ。
- **τ の既定**: `REL_TAU_BY_TENURE_HASH = {"v2": −2.322, "v1": −2.346}`。`run_day(rel_tau=None)`(既定)と CLI `--rel-tau`(既定 None)は版ごとの値を使う。明示の τ は従来どおり優先。`REL_TAU`=既定(v2)の値 −2.322・`REL_TAU_V1`=−2.346。
- **τ の再逆算**(8b′ と同じ手順・[tenure_measure.py](tenure_measure.py) → [item2_tenure.json](item2_tenure.json)): 全母集団 390,067 体・`initial_edges(tau=None)`(辺 3,503,281)→ ラン開始時の「体ごとの 15 番目の辺の A」の中央値 → 小数 3 桁で切り下げ。

| 版 | 15 番目の A の中央値(開始 / 1 日の終わり) | 宣言 τ | τ 後の初期辺(τ で落ちた) | 15 本の体(割合) | 体あたりの中央 |
|---|---|---|---|---|---|
| v1(旧) | −2.3454 / −2.4075 | −2.346(再現) | 3,483,572(19,709) | 196,080(50.3%) | 15 |
| **v2(既定)** | **−2.3216** / −2.3864 | **−2.322** | 3,483,460(19,821) | 195,239(50.1%) | 15 |

- Q111 の記録の反実仮想(別の塩で T だけ引き直し)の −2.3225 と近い。v1 の再逆算が −2.346 に一致=手順の検算。
- 5,000 体(既定の抽出・mock・関係 on)の初期辺: v1 9,232 本(τ で 14 本落ちる)→ v2 9,198 本(48 本)。τ 前は両方 9,246。
- **検算(テスト・`tests/engine/test_relations_tenure.py`・全母集団の値は [item2_tenure.json](item2_tenure.json))**:

| 在職 2 週未満の辺の割合(一様なら 8.33%) | 世帯 u<v / u>v | 職場 u<v / u>v | 学校 u<v / u>v |
|---|---|---|---|
| v1(τ 前の辺) | 8.45 / 8.45% | **28.72** / 8.36% | **65.72** / 8.33% |
| **v2** | 8.05 / 8.05% | 8.33 / 8.38% | 8.32 / 8.32% |

- (u<v=元 id_u < 元 id_v。Q111 の記録の 28.2%/64.9% は τ 後の辺での値=本表は τ 前。)
- 在職期間の U と同点の順のハッシュ `_pair_mix(元 id_u, 元 id_v)` の順位相関(Spearman・全辺): v1 0.486(u<v の辺だけなら 1.000)→ **v2 −0.0009**(u<v だけ −0.0004)。u→v と v→u の在職期間: 両版とも一致。
- テスト 5 件: 旧の式そのもの・対称・範囲 1〜13 週/合成の大組織(200 人・全員同点・k 15)で v1 は u<v の 2 週未満 >50%・v2 は向きに依らず 1/12 ± 0.03・網は版で同じ/30 万組の順位相関 <0.01・連番の組で一様/**全母集団**で種別 × 向きの 6 通りすべて 8.33% ± 1 ポイント・順位相関 <0.01・対称・τ の再逆算が −2.322(約 61 秒)/切替口・CLI・版ごとの τ・明示の τ が優先。`test_relations_8b.py` の τ のテストを v1/v2 の両方に(会話 1 回の辺の寿命 v1 7.3 時間・v2 6.9 時間=どちらも 6 時間は生き 8 時間で落ちる)。
- **golden**: テストに関係の腕の final を固定したものは無い(grep で確認)。記録の値の新旧は 2A-0 の表(v3・記憶 on・関係 on `e4f84d1d` → `40409ebe`)。
- **宣言(未リサーチ=expedient)**: v2 の混ぜ方(塩の値・splitmix64 を 1 段)は実行役の自前の構成(値に意味はない=同点の順と独立で、向きのない組で対称なら何でもよい)。τ の小数 3 桁の切り下げは 8b′ の流儀のまま。

### 2A-3 古典の腕の Q42 の今直す 2 点

#### 2A-3a 交際・付き合い(符号 18)の相手=知人

- **入れたもの**(`engine/classical.py`): `ClassicalPolicy.social`(`acquaintance` 既定 / `near_first` 旧)と `acq_fn`(近接行の人 → 生きている関係辺の A・辺が無いか τ 未満は −inf)。`acquaintance` の規則: 招待者への返事は不変・それ以外は **B5 近接行の人(自分を除く・行の順)のうち知人で A が最大の人**(同点は近接行の順=距離の順)・知人が居なければ「なし・待つ 30分」。`acq_fn` は `--relations on` のランだけ `engine.run` が差し込む(`rel_layer.edges` を呼ぶ=近接行の人数ぶんの表引き・逐次ループ宣言つき)=**関係 off のランでは知人が居ない=古典の腕から会話を始めない**。遠くの知人を誘う仕組み(約束・待ち合わせ)は作っていない(C10 8d の後)。manifest `classical.social` と計数 `talk_acquaintance`/`talk_no_acquaintance`。`run_day(classical_social=…)`・CLI `--classical-social`。
- **旧**: `near_first`=近接行の最初の人(関係 on のランは C10 8b の重みつき抽選 `partner_fn`)をそのまま残した。
- **検算(テスト・`tests/engine/test_classical_social.py` 3 件)**: A 最大の知人を選ぶ・未知の人と自分は選ばない・同点は行の順・知人が居なければ/誰も見えなければ/関係 off なら待つ・返事は不変/旧の規則の再現(知人の表を引かない)/ラン: classical 1,500 体の golden(下)・関係 off では `talk_acquaintance`=0 かつ `talk_no_acquaintance`=符号 18 の件数(210)・関係 on(3,000 体・720 tick)では知人と話す(6 件)と合計の一致。`test_classical_policy.py` の対応表のテストは既定(待つ)と旧(最初の人)の両方に。
- **golden の新旧**(`tests/perception/test_near_tiebreak.py` の `CLASSICAL_1500_GOLDEN` 3 値は `classical_social="near_first"` で**そのまま再現**するようにした・既定の新しい値は `tests/engine/test_classical_social.py` の `CLASSICAL_1500_GOLDEN_ACQ`):

| classical 1,500 体・seed 1・v3 | final | 呼数 |
|---|---|---|
| 旧(near_first)=`CLASSICAL_1500_GOLDEN["hash"]` | `91732f34f9e2da62…` | 26,869 |
| **新(acquaintance・既定)** | `4f78f3c0ce95d8e2…` | 25,808 |

- 5,000 体は 2A-0 の表(classical `60e72227` → `3390e3ec`・102,021 → 97,563 呼=会話の呼が減る)。5,000 体・関係 on・記憶 on の classical(検収前の規則)で、符号 18 を選んだ 1,017 回のうち近接行に知人が居たのは 328 回(32%)([item3_social.json](item3_social.json) `rel_on_before_fix`)。

**検収後の直し(話しかけられない知人を除く)**: 検収で、選んだ知人が会話中で `PARTNER_BUSY` に落ちる回があり、その多くで別の話しかけられる知人が近くに居たと分かった。`engine/run.py` の `classical_acq_addressable`(`acq_fn` の中で呼ぶ)で、相手の活動が `resolve._UNADDRESSABLE`(会話中・就寝中)か、このランの設定で `resolve.talk_within_reach` が偽(別のセル・edge 幾何×v2 の注意の腕なら 2 m 超)なら A を −inf にする(方策は体の状態を読まない)。テスト(`test_busy_or_asleep_or_out_of_reach_acquaintances_are_skipped`): A の大きい知人が会話中・もう 1 人が空いていれば空いている方を選ぶ・就寝中/別のセル/自分/範囲外の id は外す・同じセルでも 5 m 離れていれば距離の腕でだけ外す。

前後の値([social_measure.py](social_measure.py) → [item3_social.json](item3_social.json)・classical 5,000 体・seed 1・v3・energy・判定しない。「前」は除外の関数を恒等に差し替えて再現):

| 構成 | final | 呼数 | 符号 18 | 知人を選んだ | 選んだ時の相手(会話中) | 返事(reply_talk) | 成立した会話 | 開始の門で落ちた(gate_rejected) |
|---|---|---|---|---|---|---|---|---|
| 関係 on・直しの前 | `102e4517805540d4` | 110,431 | 1,017 | 328 | 24 | 226 | 207 | 48 |
| **関係 on・直しの後(既定)** | `28ea80375e7ee646` | 110,395 | 1,003 | 321 | **0** | 233 | 216 | 37 |
| 関係 on・near_first(旧) | `e3db0d32e8ecd8ee` | 114,088 | 1,084 | — | — | 773 | 743 | 152 |
| 関係 off・acquaintance(既定) | `3390e3ec02d392a9` | 97,563 | 874 | 0 | — | **0** | **0** | — |
| 関係 off・near_first(旧) | `60e7222783a221c6` | 102,021 | 982 | — | — | **697** | 673 | — |

(選んだ時の相手の状態の内訳は JSON。検収のラン=per_hour では 342 回中 27 回が会話中だった。本表は既定の per_wake。)

- **事実(判断はユーザー)**: **関係 off の古典の腕は会話を 1 件も始めない**(返事 697 → 0・成立した会話 673 → 0)。関係 on でも会話は旧の約 3 割(743 → 216)。LLM の腕(mock・関係 off)は見知らぬ人とも話すので、**古典と LLM の比較を関係 on で行うか**はユーザーの判断(指示書 §0-3)。acquaintance は C10 8b の重みつき抽選(残り 40% は見知らぬ人)を通らない=古典の腕は見知らぬ人に話しかけない(LLM の腕との非対称)。
- **宣言(未リサーチ)**: 同点を近接行の順で切る・「知人」=生きている辺(A ≥ τ_rel)=B5 の「(知人)」の印と同じ定義・知人が居ないときの応答(待つ 30 分)は旧の「見えなければ」と同じ文。

#### 2A-3b 「まで」の長さ(**実装していない=親に問う**)

候補を比べた([until_candidates.py](until_candidates.py) → [item3_until_candidates.json](item3_until_candidates.json)・平日)。

| 符号 | 行動 | (a) 事前分布どおりに始めた平均の長さ[分] | (a) 集計の平均(Σs/正味の流入)[分] | (b) 行動者平均時間(1 日の合計)[分] | (a)/(b) |
|---|---|---|---|---|---|
| 02 | 身の回りの用事 | 207 | 269 | 95 | 2.2 |
| 07 | 家事 | 223 | 322 | 185 | 1.2 |
| 10 | 買い物 | 220 | 304 | 70 | **3.1** |
| 11 | 移動 | 240 | 334 | 80 | 3.0 |
| 12 | テレビ・新聞 | 225 | 320 | 217 | 1.0 |
| 13 | 休養・くつろぎ | 254 | 369 | 153 | 1.7 |
| 15 | 趣味・娯楽 | 257 | 390 | 173 | 1.5 |
| 16 | スポーツ | 235 | 301 | 91 | 2.6 |
| 18 | 交際・付き合い | 270 | 430 | 140 | 1.9 |
| 19 | 受診・療養 | 215 | 302 | 131 | 1.6 |
| 20 | その他 | 249 | 365 | 127 | 2.0 |

(全 19 種は JSON。(a)=錨 `ssb2021_activity_prior_v0.json` の関東大都市圏・4 層の年齢総数の行を推定人口で加重・帯の継続確率 c=min(1, s(b+1)/s(b))・上限 480 分。(b)=生活時間編 第4-1表 ÷ 第4-3表の平日・全国・15 歳以上の総数の行。)

- **(a) は明らかに長すぎる**: 集団の行動者率は帯ごとに滑らか(c の中央値 ≈ 0.99〜1.00)なので、流入 0 と置くと「始めたらほぼ終わらない」になる。買い物・移動・スポーツでは (a) の平均の長さが**行動者の 1 日の合計時間の 2.6〜3.1 倍**=1 日 1 回でもあり得ない値。層ごとの行(標本 5,000 前後)で c を出すと、今度は標本の揺れで c が 1 を割り、長さが雑音で決まる。
- **(b) は 1 日の回数の表が手元に無い**(data/calib/hunger/ の MANIFEST と data/research_cache/r69/ を確認=どちらも総平均時間と行動者率だけ)。1 日 1 回と置いた値は平均の長さの**上限**で、回数の仮定(設計者の指紋)を入れないと値が決まらない。
- どちらもいまの 30 分固定より 2〜9 倍長い。差が大きく(a/b が 1.0〜3.1 倍・活動で向きもばらつく)、どちらの偏りも大きさを見積もれないので、指示どおり**実装しなかった**(切替口 `--classical-until` も入れていない)。
- **宣言(親の了承・2026-09-30)**: 古典の腕の「まで」は**30 分固定のまま**(expedient)。選択肢(2A-6 Q-2A-1)はユーザーに出す。

### 2A-4 食事の門を時間あたりに(Q48 (a)・既定は旧のまま=指示書 §8-2)

- **入れたもの**(`engine/classical.py`): `meal_gate_interval_p(p_h, Δt)=1 − (1 − p_h)^(Δt/60)`。`ClassicalPolicy.meal_gate`(`per_wake` 既定=旧 / `per_hour`)。`per_hour` では語 × カレンダー × 周囲(上限 1)を 1 時間あたりの p_h と読み、**Δt=前回の門の後にその体が範囲内で起きていた分の合計**で換算する(**検収後の親の決定**)。就寝中(活動が就寝)と範囲外(`transit_state≠0`=エネルギー層の診断 `awake_in_area` と同じ判定)の時間は数えない。最初の門もラン開始からの同じ積算(任意の定数を置かない)。`MEAL_WORD_P` などの定数は動かしていない。`run_day(meal_gate=…)`・CLI `--meal-gate`・manifest `classical.meal_gate.mode`。
- **積算の実装**: 体ごとの「起きていた分」(**float32=4 B/体・`per_hour` の腕の中だけ**・`per_wake` は 0 B=配列を持たない)。`engine/run.py` の tick の頭(`advance_body` の直後)で `ClassicalPolicy.accrue_awake()` が、その tick に範囲内で起きている体に 1 tick の分(分)を配列演算で足す(逐次ループなし・classical の他の腕では no-op)。門を引くたびに(満腹=p_h 0 でも)0 に戻す。**検収前の規則**(前回の門からの tick 数 × 分・最初の門は 1 tick・睡眠を含む)は置き換えた。
- **検算(テスト・`tests/engine/test_meal_gate_per_hour.py` 4 件)**:
  - p_h=0.1: 1 分ごとに 60 回と 60 分後に 1 回で「1 回以上通る確率」がどちらも 0.1(手計算で 1e−12)。200,000 体の頻度で両方 0.1 ± 0.003(標準誤差 0.00067)。不揃いの間隔でも 0.1。
  - 方策の中(合成の 4 体): 最初の門(ラン開始から 0 分)は p=0 / (i) 60 分起きていて 1 回 → 60 分の値・積算は 0 に戻る / (ii) 8 時間眠って起床後 5 分 → Δt=5 分(睡眠を数えない)/ (iii) 範囲外に 3 時間いて戻って 1 分 → Δt=1 分 / 満腹でも積算は 0 に戻る / バイト 4 B/体。
  - (iv) 起床の頻度を 2 倍(20 分ごと → 10 分ごと・合成の 16 時間・通ったら 3 時間満腹・p_h 0.6・100,000 体): 1 日の食事の回数 per_hour 4.33 → 4.26(−1.7%・許容 3%=門を引く時刻の離散化)/ per_wake 5.31 → 5.75(+8%)。
  - (v) **per_hour がランの結果を実際に変える**: 合成 100 体・1 日の classical で per_wake と per_hour の final が違い、門を通った回数が違う(検収で「manifest の欄しか見ていない」と指摘された穴)。既定と `per_wake` の final は一致。
- **計測(判定しない・[meal_measure.py](meal_measure.py) → [item4_meal.json](item4_meal.json)・classical 5,000 体・seed 1・v3・energy・新しい規則)**:

| 交際の相手 | 門 | final | 範囲内の食事 | 門を通った(ふつう/空腹/とても空腹) | 食事の回数/体 0・1・2・3・4+ | 朝食の欠食率 全体 / 20 代 | 摂取 − 消費 = 収支/体 [kcal] |
|---|---|---|---|---|---|---|---|
| near_first(旧・§5b-7 の条件) | per_wake | `60e7222783a221c6` | 9,628 | 12,939(4,461/6,473/2,005) | 8・39・743・2,373・1,837 | 7.6 / 7.2% | 2,643 − 2,466 = **+176.9** |
| near_first | **per_hour** | `dd3611071cf0ba5e` | 7,462 | 8,921(2,153/4,992/1,776) | 9・101・1,377・2,673・840 | 9.5 / 8.1% | 2,299 − 2,465 = **−165.5** |
| acquaintance(既定) | per_wake | `3390e3ec02d392a9` | 9,518 | 12,726(4,281/6,445/2,000) | 7・41・743・2,406・1,803 | 7.6 / 7.2% | 2,627 − 2,465 = +162.3 |
| acquaintance | **per_hour** | `81a86003317aeb03` | 7,452 | 8,938(2,135/4,983/1,820) | 10・103・1,392・2,656・839 | 9.5 / 8.1% | 2,300 − 2,463 = −163.3 |

- per_wake × near_first は energy-classical §5b-7 の値(欠食 7.2%・+176 kcal)を再現。per_hour で「ふつう」での食事が約半分(4,461 → 2,153)・4 回以上の体が半分・収支が +177 → −166 kcal(mock v3 は −435)。20 代の朝食の欠食率(第10表 31.1%)は 7.2 → 8.1% とほとんど動かない(朝の欠食は門でなく既定の時刻の規則が決める=§5a 4 の注記と同じ)。検収前の規則(最初の門 1 tick・睡眠を含む)の値は −140.6 kcal・ふつう 2,305 だった(規則の差は小さい向き)。

### 2A-5 宣言(本段で入れた自前の構成=未リサーチ)

- 項 2: v2 の混ぜ方(塩 `0xD1B54A32D192ED03`・splitmix64 を 1 段)。
- 項 3-1: 知人の同点=近接行の順・知人の定義=A ≥ τ_rel・居ないときの応答=待つ 30 分・話しかけられるかの判定は resolve と同じもの(自前の定数は無い)。
- 項 3-2: 「まで」は 30 分固定のまま(親の了承)。
- 項 4: 積算を足す位置=tick の頭(`advance_body` の直後の状態で判定)。Δt の規則そのものは親の決定。
- 検算の場面の値(合成の大組織 200 人・起床 20/10 分・満腹 3 時間・p_h 0.6・許容幅)はテストの道具で、エンジンの値ではない。

### 2A-6 問い(親へ)

- **Q-2A-1(「まで」の長さ=項 3-2・ユーザーに出す選択肢)**: (a) は流入 0 の仮定で行動者の 1 日の合計の最大 3 倍になり使えない。(b) は 1 日の回数の表が無い。(i) (b) を 1 日 1 回(=上限)で入れて「長めに出る」と宣言 (ii) 1 日の回数の錨をリサーチする(生活時間調査のエピソード数など=リサーチレーン)(iii) (a) を流入と流出を分けて推定する形に直す(設計が要る)(iv) 30 分固定のまま宣言(**いまはこれ**)。実行役の推奨は (ii) → 決まるまで (iv)。
- ~~Q-2A-2(食事の門の Δt)~~: 親が決定(範囲内で起きていた分)=2A-4 で実装。
- **Q-2A-3(口コミ 0 の期間)**: 既定の v3 では、ひと言欄(Q57 (d))が入るまで口コミは 0 件。店の記憶の腕の実 LLM の計測は、その間 口コミ抜きになる。旧(reason-target)を感度腕として併走させるか。
- **Q-2A-4(τ の既定を版に結んだ)**: `--rel-tau` の既定を「版ごとの値」(None)にした。明示の τ を渡す既存の計測スクリプト(C10 の記録の `rel8b_measure.py` の 26 週の腕 −2.336 など)は v1 の網で逆算した値のまま=v2 の網では 26 週の τ を出し直す必要がある(本段では出していない)。
- **Q-2A-5(古典と LLM の比較の条件=ユーザーの判断)**: 関係 off の古典の腕は会話を始めない(2A-3a)。比較を関係 on で行うと決めるか。

### 2A-7 変更したファイル・再現

- src: `engine/wom.py`・`engine/relations.py`・`engine/classical.py`・`engine/run.py`・`cli.py`。触っていない: `engine/energy.py`・`resolve.py`・`perception/`・`build/`・`tools/`・`data/`・台帳・設計書。
- tests: 新規 `tests/engine/test_relations_tenure.py`(6=関係 on の腕の golden `REL_ON_5000_GOLDEN` v1 `e4f84d1d`/72,940・v2 `40409ebe`/72,930 を含む・約 99 秒)・`test_classical_social.py`(4)・`test_meal_gate_per_hour.py`(4)/変更 `test_wom.py`(新規 3・変更 2)・`test_relations_8b.py`(1)・`test_classical_policy.py`(2)・`tests/perception/test_near_tiebreak.py`(1)。
- 再現(リポのルートで・`$D`=この置き場):

```
python $D/wave2_bytecheck.py side --src <git archive HEAD の src> --label head --scratch <作業用> --out <作業用>/head.json
python $D/wave2_bytecheck.py side --label work --scratch <作業用> --out <作業用>/work.json
python $D/wave2_bytecheck.py side --label work_old --old '{"wom_source": "reason-target", "rel_tenure_hash": "v1", "classical_social": "near_first", "meal_gate": "per_wake"}' --scratch <作業用> --out <作業用>/work_old.json
python $D/wave2_bytecheck.py compare --head <作業用>/head.json --work <作業用>/work.json --work-old <作業用>/work_old.json --expect-moved v3_mem_rel,v3_classical,v3_classical_mem_rel --out $D/item4_byte_check.json
python $D/tenure_measure.py all --out $D/item2_tenure.json
python $D/meal_measure.py --out $D/item4_meal.json
python $D/social_measure.py --out $D/item3_social.json
python $D/until_candidates.py --out $D/item3_until_candidates.json   # openpyxl のあるシステムの python
```

## §2B 食事の束 3 項(就寝中の既定の食事・自宅の食事行・B5 の空腹の語)(実行役 Opus 5.5・親の検収前)

> 指示書 [v2-wallbounce-decisions-2026-09-30.md](../../../design/v2-wallbounce-decisions-2026-09-30.md) §4・§8-2(切替口つき・**既定は旧のまま**=版上げはまとめてユーザーに確認)。前提の記録=[energy-classical §5a](../energy-classical-2026-09-28/README.md)(4 朝食の欠食率・8 宣言・8b の Q31/Q34/Q35)。
> **byte-check の基準**: HEAD `01b6f5b` を `git archive` で OS の一時ディレクトリへ展開した src と作業木で、§2A と同じ 19 構成(W6 再生成の 15 腕+店の記憶・関係・古典・古典+記憶+関係)を mock/classical 5,000 体・seed 1・1 シミュ日・テープつきで回し、final・呼数・blocks・calls の 14 列(prompt_hash を含む)を比べた([wave2_bytecheck.py](wave2_bytecheck.py)・`--head-label 01b6f5b`)。`work`=作業木の既定・`work_old`=3 切替口を旧の値で**明示**した作業木。
> 全体テストは回していない(親が回す)。holdout には触れていない。Web からの取得はしていない。

### 2B-0 結論

| 項 | 入れたもの | 切替口(既定=旧) | byte-check | 主な値(mock 5,000・判定しない) |
|---|---|---|---|---|
| 1 Q34 (b) | 範囲外の既定の食事時刻に W17 で就寝中の体は、起床の時刻へ遅らせ、窓の中なら食べる | `--meal-sleep-defer {off,on}` | 19/19 一致(`work`・`work_old`) | 朝食の欠食率 全体 25.5 → **30.8%**・20 代 21.9 → **26.3%** |
| 2 Q35 (a) | W17 の自宅の食事行(自宅が範囲内の体)を「予定の実行」として食べさせる | `--home-meal {off,plan}` | 同上 | 対象の行は **103 本だけ**(509 体中 102 体)・食べたのは 30 回・自宅が範囲内の体の欠食 83.1 → 82.3% |
| 3 Q31 (b) | B5 の空腹の語を 4 段とも描く腕 | `--hunger-words {hungry,all}` | 同上+参照場面の prompt_hash 不変 | B5 +1.9 tok/呼(平均)・個体の群の最大 157 tok(上限 300)・mock と classical の final は不変 |

- **規律からの逸脱(報告)**: 指示は「項を終えるたびにその項のテストと byte-check」だったが、実行役は 3 項を入れてから byte-check を**まとめて 1 回**回した(テストは項ごとに書いて回した)。3 項とも既定は旧で、まとめた状態で 19/19 一致=各項の既定も一致している(一致しなかった場合に項を切り分ける手間を先送りした形)。[item2b_byte_check.json](item2b_byte_check.json)(`all_ok` true・`src_checks` ok=HEAD 側は写しを読み、作業木側は作業木を読んだ)。検収後の直しの後に取り直した(2B-8)。
- 3 項すべて on(`all_on`)の mock の final は `78085fdb13c315ed`(呼 69,337)。既定(`993276d5e5bb5cbe`・69,978)は HEAD と同じ。

### 2B-1 項 1: 就寝中に既定の食事時刻が来たら起床時に(窓内で)食べる(Q34 (b))

- **コードで確かめたこと(どちらの体に既定の時刻の食事が置かれるか)**: `OutOfAreaMeals` は既定の時刻の食事を「その時間帯に W17 の食事行が無い**全員**」に予定するが、`due` は**その時刻に域外(`transit_state==2`)に居る体だけ**を食べさせる。範囲内の体には既定の時刻の食事は元から置かれない(範囲内の食事は飲食店でだけ成立)。したがって指示の「範囲内の体は活動(就寝)で判定」は、いまのコードでは起きない場合分け。範囲外の体のエンジンの `activity` は、`begin_planned_sleep` が域外の体を触らない(規則 3)ので計画の就寝を表さない=**W17 の予定で判定した**。
- **入れたもの**(`engine/energy.py`): `w17_wake_minute(weekly, n, day, 体, 分)`=その分に W17 の「就寝」の行の中なら起床の分(W17 の `activity_at` と同じ読み=開始 ≤ 分 の最後の行)。起床の分=**就寝の行の終わりと次の行の開始の早いほう**・連続する就寝の行はつなぐ。`OutOfAreaMeals(sleep_defer="on")`: 既定の時刻に W17 で就寝中の既定の食事を分け、既定の時刻に域外なら「仕掛け」、起床の分が窓(`MEAL_WINDOWS_MIN`)の中ならその時刻に域外なら食べる(`due_with_deferred` の 4 本目=遅らせた印)。窓を過ぎていればその時間帯の食事は無し。摂取は元の時間帯の比(K9 と同じ式)。W17 の食事行由来の食事は変えない。早朝に出る通勤者は変えていない(Q34 (d))。
- **manifest**: `meal_sleep_defer`(ランの欄)・`energy.counts.meals_out_deferred`(`meals_out_default` の内数)・`energy.out_of_area_schedule.sleep_defer`(W17 で就寝中だった既定・うち起床が窓の中・既定の時刻に域外で仕掛けた・窓を過ぎて無し・起床時に域外でなく食べなかった)。**off のランは要約の鍵も増えない**(ランの欄 3 つ `meal_sleep_defer`/`home_meal`/`hunger_words` だけは常に載る)。
- **検算(テスト・`tests/engine/test_meal_bundle_2b.py`)**: 合成の体で、7:29 に就寝中・8:00 に起床 → **8:00 に朝食**(遅らせた印)/ 11:30 に起床 → **朝食なし** / 7:00 に起床済み → **7:29 に朝食=旧と同じ** / 就寝の行 2 本(5:00・8:20)→ 8:20 / W17 の行なし → 旧と同じ。行の重なり(就寝 0〜19:16 の途中 7:00 に支度)→ 7:00 に起床。off は旧の予定と一致(`due` と `due_with_deferred` の先頭 3 本も一致)。7:29 に範囲内だった体は仕掛けない・起床時に範囲内なら食べない(件数を数える)。
- **不変条件(テスト)**: 乱数の 400 体で (i) 食べた時刻に W17 で就寝中の体はいない (ii) 遅らせた食事は窓の中 (iii) 同じ時間帯に 2 回食べない (iv) 仕掛けた=遅らせて食べた+起床時に域外でない+窓を過ぎた。範囲外の体(METs=基準日の平均=1 日の消費がちょうど EER)で **3 食の日の収支/EER が 0**(±0.002)・朝食を失った体は −朝の比。実資産 1,500 体のラン: 項 1 が置いた食事(既定の時刻・遅らせた)の時刻に W17 で就寝中の体 **0**。
- **実データの検査**(5,000 体): 旧(off)は既定の時刻の食事 6,344 回のうち **2,541 回(40%)が W17 で就寝中**に置かれていた。on では 0。範囲外の 7 時台の食事は 3,446 → 1,940・8 時台 14 → 1,082・9 時台 4 → 120(時別は JSON の `meal_hourly`)。W17 の食事行由来の食事でも 2 回(1,441 回中)が W17 の就寝の行と重なる=**W17 の行の重なり**(1,500 体の月曜で連続する行の 2.9%(329/11,363)が重なる・例: 就寝 0:00〜19:16 と食事 0:00〜7:00 が同じ開始)。項 1 の外なので触っていない(問い Q-2B-3)。

### 2B-2 項 2: 範囲内の自宅での食事=予定の実行(Q35 (a))

- **入れたもの**: `engine/energy.py` `HomeMeals`(W17 の活動語「食事」・場所語「自宅」の行で、W16 の `home_cell >= 0`=自宅が範囲内の体のもの)。行の開始の tick に `transit_state==0` かつ `cell == home_cell` かつ `activity != 就寝` なら食べる。`engine/resolve.py` `energy_home_meal`=摂取は K9 と同じ(時間帯の比 × EER・`since_meal=0`)で、**書き換える欄は `since_meal_kcal`・`energy_balance`・`hunger`・`hunger_stage` の 4 本だけ**(引数に世界・台帳を取らない=金・棚・席に触る経路がない)。`engine/run.py` では**計画境界の起床の後**(行の境界で起こされた体が起きている位置)で呼ぶ。1 行 1 回(行の開始の tick だけ見る)。
- **照合から外す**: 印 `meal_home`=`energy.counts.meals_home_plan`・開始の 15 分分布 `energy.home_meal.meal_start_home_15min`。照合の分布 `meal_start_in_15min` と `meals_in_area`・店の集計(`res.meals`)には入らない。食事の回数(`n_meals`)と窓の印(欠食率の計算)には入る。
- **起床を足さない**: 行の起床はもともと W17 の計画境界にある(新しい起床は作らない)。加えて食事で下がった段を `hunger_stage` にも書く=この食事そのものは内受容の下げ跨ぎ(起床入口「体」)を作らない(テスト: 同じ場面で飲食店の食事の口は跨ぎを作り、自宅の食事は作らない)。**ランの総呼数は変わる**(mock −421・classical +429)。**検収後の訂正**: 初版の「食後の空腹の上げ跨ぎと classical の門が変わるため」は**テープで反証された**。食べた体自身の呼数の差は mock +1(30 体)・classical 0(28 体)で、差は全部ほかの体から来る(呼数が変わった体 mock 1,922・classical 2,615)。呼の並びは食事の後で分かれる(tick ごとの呼数が最初に違う tick: mock 435・classical 391。最初の自宅の食事は tick 360)。小さな揺らぎが共有の状態(混雑・店・会話・乱数の順)を通じてラン全体へ広がった形で、差の大きさは揺らぎの床(2B-8 (1))と同じ桁。
- **検算(テスト)**: 自宅が範囲内・7:00 の自宅の食事行・自宅に居る → **食べる** / 外出中 → 食べない / 自宅に居るが就寝中 → 食べない / 自宅が範囲外(K9 の側)・飲食店の食事行 → 対象外 / 同じ行で 2 回食べない / 摂取=朝の比 × EER / registry の全欄を前後で比べ、変わったのは上の 4 本だけ(`money` 不変)。
- **事実(実データ・5,000 体)**: 自宅が範囲内の 509 体の月曜の食事行は 354 本で、**場所が自宅なのは 103 本**(飲食店 215・駅 34・他 2)。103 本のうち行の開始に自宅に居たのは mock の home 腕で 30 本(**73 本は自宅に居ない**=mock の体は範囲内を歩き回っていて帰宅していない・就寝中 0。all_on では 31 本/72 本・classical は 26〜28 本)。自宅が範囲内の体の朝食の欠食率は 83.1 → 82.3%(mock)とほとんど動かない=**Q35 の 83% の主因は「自宅の食事の口が無い」ことより、W17 に自宅の朝の食事行がほとんど無いこと(103 本の時間帯は朝 5・昼 10・夕 84・他 4。朝の 5 本は 5 回とも食べた)**(問い Q-2B-1)。

### 2B-3 項 3: B5 の空腹の語を 4 段とも描く(Q31 (b))

- **入れたもの**: `perception/renderer.py` `HUNGER_WORDS_MODES=("hungry","all")`・`DEFAULT_HUNGER_WORDS="hungry"`・`Renderer(hunger_words=…)`(`_hunger_word(v, min_stage)`・all は段 0 から)。all の満腹・ふつうの逸脱(ablation ① の池の順位の重み)は 0(負にしない)。`run_day(hunger_words=…)`・CLI `--hunger-words`・manifest `hunger_words`。`templates.py` の定数(`HUNGER_WORD_DRAW_MIN_STAGE=2`)は変えていない=`template_sha256` は不変(**all でも同じ SHA**=問い Q-2B-4)。**既定は hungry(旧)**。ユーザー決定は「all を既定に」だが、既定の切り替えは版上げでまとめて行う(指示書 §8-2)。
- **記録(ユーザー指示)**: D-111 の予想表の「B5 に空腹の行が出る時間 11%」(閾値超え)は、**空腹以上だけを描く定義(hungry)の値**。all では定義上 100%(起きて範囲内の全員に語が 1 つ出る)になるので、予想表のこの行は all では意味を持たない。
- **検算(テスト)**: all で 1/5/8/10 → 満腹・ふつう・空腹・とても空腹(語は 1 行に 4 段のどれか 1 つだけ)/ hungry は旧の規則。参照場面(`energy_columns`・語彙 v3・HEAD の src で計算した prompt_hash を固定)で **hungry(既定)は 4 段とも HEAD と一致**・all は満腹/ふつうのときだけ B5 だけが動く。既存の参照場面(`test_vocab_v2_templates` の `f6a44b2b…`)も不変。all の 1,000 描画で個体の群 ≤ 300 tok・各ブロックも予算内。
- **計測(mock 5,000・同じ final=同じ呼の並び・描画の側で数えた=テープの blocks は共有ブロック B0〜B4b だけを持つ)**:

| | B5 の tok 平均(p50・最大) | 個体の群(B5+B6)平均(最大・上限 300) | 語の回数(満腹/ふつう/空腹/とても空腹/なし) | tokens_in 平均 |
|---|---|---|---|---|
| hungry(既定) | 78.6(77・103) | 122.6(157) | 0 / 0 / 15,923 / 12,998 / 41,057 | 1,025.9 |
| all | 80.5(81・103) | 124.5(157) | 17,402 / 23,655 / 15,923 / 12,998 / 0 | 1,027.8 |

  - **増分 +1.9 tok/呼**(tokens_in の合計 71,787,856 → 71,921,263)・語を足した呼(41,057=59%)では 1 文ぶん(約 3〜4 tok)。上限 300 の中。
  - **mock の final は動かない**(`993276d5` のまま)。**classical の final も動かない**(`28ea8037`・per_hour `3af0f54c`)=方策 classical は空腹を `r.hunger` から読み(`chooser.hunger_stage_of`)、プロンプトからは近接行の人だけを読む(`_near_persons`)=B5 の空腹の語を読まない。

### 2B-4 計測(3 項を入れた後・判定しない・[meal_bundle_measure.py](meal_bundle_measure.py) → [item2b_meal_bundle.json](item2b_meal_bundle.json))

5,000 体・seed 1・語彙 v3・energy・月曜。classical は**記憶 on・関係 on**(関係は記憶 on が要る=`run_day` の制約)・交際の相手は既定(acquaintance)。欠食=朝の窓 5:00〜10:59 に食事(範囲内・範囲外・自宅の予定の実行)が 1 回も無い体(軽食だけは欠食・§5a 4 と同じ)。

**朝食の欠食率 [%]**

| 方策 | 腕 | final | 呼数 | 全体 | 20 代(男/女) | 自宅が範囲内(509) | 自宅が範囲外(4,491) | 通勤者(2,346) |
|---|---|---|---|---|---|---|---|---|
| mock | base(=HEAD) | `993276d5` | 69,978 | 25.5 | 21.9(22.7/20.8) | 83.1 | 18.9 | 23.6 |
| mock | defer | `fc48fea7` | 69,051 | 30.8 | 26.3(27.9/24.3) | 82.9 | 24.9 | 32.7 |
| mock | home | `6fdc00bd` | 69,557 | 25.3 | 21.6(22.3/20.6) | 82.3 | 18.9 | 23.5 |
| mock | words | `993276d5` | 69,978 | 25.5 | 21.9 | 83.1 | 18.9 | 23.6 |
| mock | all_on | `78085fdb` | 69,337 | 30.7 | 26.1(27.7/24.1) | 81.9 | 24.9 | 32.7 |
| classical(per_wake) | base(=HEAD の v3_classical_mem_rel) | `28ea8037` | 110,395 | 7.5 | 7.2(6.3/8.1) | 51.5 | 2.5 | 0.4 |
| classical(per_wake) | defer | `c1e16438` | 110,415 | 11.8 | 9.6(9.3/9.9) | 51.9 | 7.2 | 8.8 |
| classical(per_wake) | home | `beedc5b6` | 110,824 | 7.5 | 7.0 | 50.9 | 2.5 | 0.4 |
| classical(per_wake) | words | `28ea8037` | 110,395 | 7.5 | 7.2 | 51.5 | 2.5 | 0.4 |
| classical(per_wake) | all_on | `6fe8b265` | 110,215 | 11.7 | 9.5(9.3/9.6) | 51.3 | 7.2 | 8.8 |
| classical(per_hour・**いまの実装**=2B-8 (3)) | base | `44088c4b` | 106,177 | 9.9 | 8.7(8.0/9.4) | 64.4 | 3.7 | 1.9 |
| classical(per_hour・同) | defer | `ed26a132` | 105,881 | 14.3 | 11.4(11.4/11.4) | 63.5 | 8.7 | 10.4 |
| classical(per_hour・同) | home | `206eb6e5` | 106,011 | 9.9 | 8.6 | 63.9 | 3.7 | 1.9 |
| classical(per_hour・同) | words | `44088c4b` | 106,177 | 9.9 | 8.7 | 64.4 | 3.7 | 1.9 |
| classical(per_hour・同) | all_on | `c066171e` | 106,219 | 14.2 | 11.3(11.4/11.2) | 63.1 | 8.7 | 10.4 |
| **第10表**(国民健康・栄養調査 令和6年) | | | | 12.2(1 歳以上) | **31.1(37.3/26.5)** | | | |

年齢階級別(mock base → all_on / 第10表): 1-6 70.6 → 70.6 / 3.9・7-14 38.9 → 48.4 / 4.2・15-19 13.8 → 18.0 / 13.9・20-29 21.9 → 26.1 / 31.1・30-39 25.3 → 30.3 / 23.0・40-49 27.0 → 32.1 / 18.3・50-59 26.8 → 31.9 / 16.1・60-69 27.6 → 35.2 / 10.9・70+ 27.2 → 34.0 / 3.8(全 15 ランの値は JSON)。**第10表の年齢勾配(20〜30 代で高く高齢で低い)は sim には無い**(mock は項 1 の前も後も 15 歳以上でほぼ平ら)。sim の「全体」は 0 歳を含む 5,000 体(1 歳以上 4,995 体でも同じ値)。

**食事の回数・時刻・収支・範囲外の内訳**

| 方策・腕 | 食事の回数/体 0・1・2・3・4+ | 範囲内の食事 朝/昼/夕/他(照合の分布) | 範囲外 朝/昼/夕/他 | 自宅(予定)朝/昼/夕/他 | 収支/体 中央値(p5〜p95)[kcal] | 3 食の体の収支/EER 中央値 | 範囲外の内訳 W17 の食事行 / 既定の時刻 / 起床時に遅らせた |
|---|---|---|---|---|---|---|---|
| mock base | 291・864・1,560・1,371・914 | 1,006/1,790/1,416/285 | 3,476/1,577/2,703/29 | 0 | −535(−2,213〜+1,614) | −0.0 | 1,441 / 6,344 / 0 |
| mock defer | 362・1,056・1,524・1,241・817 | 1,009/1,742/1,340/310 | 3,191/1,476/2,442/28 | 0 | −648(−2,320〜+1,484) | −0.0 | 1,440 / 3,834 / 1,863 |
| mock home | 277・891・1,566・1,382・884 | 1,009/1,773/1,346/271 | 3,476/1,580/2,707/28 | 5/4/21/0 | −529(−2,213〜+1,598) | −0.0 | 1,452 / 6,339 / 0 |
| mock all_on | 353・1,050・1,540・1,259・798 | 1,009/1,755/1,294/308 | 3,191/1,478/2,443/28 | 5/4/21/1 | −639(−2,309〜+1,469) | −0.0 | 1,438 / 3,839 / 1,863 |
| classical per_wake base | 7・34・669・2,296・1,994 | 2,367/3,542/3,447/637 | 3,428/1,057/2,352/11 | 0 | +16(−989〜+1,591) | −0.0 | 1,110 / 5,738 / 0 |
| classical per_wake all_on | 6・156・994・2,132・1,712 | 2,218/3,481/3,360/623 | 3,143/938/2,089/11 | 5/2/17/2 | −0(−1,258〜+1,528) | −0.0 | 1,111 / 3,209 / 1,861 |
| classical per_hour base(いまの実装) | 9・129・1,765・2,582・515 | 1,423/2,282/2,495/435 | 3,428/1,057/2,353/11 | 0 | −174(−1,376〜+745) | −0.0 | 1,111 / 5,738 / 0 |
| classical per_hour all_on(同) | 9・356・1,941・2,282・412 | 1,398/2,232/2,441/465 | 3,143/938/2,089/11 | 4/3/20/2 | −289(−1,576〜+692) | −0.0 | 1,111 / 3,209 / 1,861 |

(食事の回数は範囲内+範囲外+自宅。単独の腕 defer/home/words の classical の値は JSON。)

- 項 1(mock): W17 で就寝中の既定の食事 2,950(予定)・既定の時刻に域外で仕掛けた 2,541 → **遅らせて食べた 1,863**・起床が窓を過ぎて無し 590・起床時に域外でなく 88。
- 3 食の体の収支/EER の中央値は全腕で 0=**3 食で閉じる性質は保たれる**(収支/体の中央値は 1 日の食事の回数の分布で動く)。
- 呼数(off → on): 項 1 mock −927・classical per_wake +20・per_hour −296 / 項 2 mock −421・classical per_wake **+429**・per_hour −166 / 項 3 どれも 0(per_hour はいまの実装の値。初版の規則では項 1 +74・項 2 +130・ハザードの積算だけの規則では −534・−72)。呼数の差の大きさは**揺らぎの床**(2B-8 (1))と同じ桁。
- per_hour の行は**検収後に門の規則を 2 回変えて取り直した**(2B-8 (3)・いまの実装=ハザードの積算+食事で H を 0+満腹の門は 0)。§2A 2A-4 の per_hour の値(−163 kcal など)は前の規則の値で、§2A は書き換えていない。

### 2B-5 宣言(本段で入れた自前の構成=**未リサーチ(expedient)**)

- 項 1: 起床の分=就寝の行の終わりと次の行の開始の早いほう(W17 の行の重なりへの読み)・遅らせるのは既定の時刻に域外に居た体だけ(旧で食事が置かれた体)・起床時にも域外に居ることを条件(範囲内の体は飲食店で食べる=K9 と同じ分け方)・遅らせた食事の摂取は元の時間帯の比。
- 項 2: 「自宅に居る」=`cell == home_cell`(W16)かつ在圏・「起きている」を条件に加えた(指示の文言は「自宅に居ること」だけ=項 1 の不変条件「エンジンが置く食事は起きている時刻」に合わせた)・行の開始の tick だけを見る・計画境界の起床の後に置く・`hunger_stage` を合わせて内受容の起床を作らない。
- 項 3: all の満腹/ふつうの逸脱を 0 にした・`template_sha256` の payload は変えていない。
- 計測: classical に記憶 on を付けた(関係 on の前提)。

### 2B-6 問い(親へ)

- **Q-2B-1(Q35 の効き)**: 自宅が範囲内の 509 体の朝食の欠食 83% は、項 2 を入れても 82% のまま。W17 の自宅の食事行が 103 本(月曜・朝の窓は 5 本)しか無く、その 7 割は行の開始に自宅に居ない。(i) 自宅に居なくても行の開始で食べる(「予定の実行」を場所に結ばない)(ii) 行の開始から終わりまでの間に帰宅したら食べる (iii) 朝の窓に食事行の無い範囲内の体にも既定の時刻を置く(範囲外の K9 と対称)(iv) このまま(W17 の側の問題として記録)。どれにするか。
- **Q-2B-2(呼数)**: 項 2 の食事そのものは起床を足さない(食べた体の呼数の差 mock +1・classical 0)。総呼数の差(classical +429・+0.39%)はほかの体へ広がった揺らぎで、1 kcal の揺らぎ 1 回で classical の総呼数が 0〜+315 動く(2B-8 (1))のと同じ桁。「呼数を増やさない」は「食べた体に起床を足さない」で読んでよいか。
- **Q-2B-3(W17 の行の重なり)**: 月曜の連続する行の 2.9% が重なる(就寝の行が勤務・食事の行と同じ時間を覆う)。W17 の食事行由来の食事 1,441 回中 2 回が W17 の就寝中。W17 の側の欠陥として登録するか(本段では触っていない)。
- **Q-2B-4(template_sha256)**: all でも `template_sha256` は同じ(定数は不変・腕はランの manifest の `hunger_words` で区別)。版上げで all を既定にするときに、定数を 0 に変えて SHA を上げるか、腕の欄のままにするか。
- **Q-2B-5(項 1 の副作用)**: 項 1 で 20 代の欠食は錨に近づく(21.9 → 26.3%・錨 31.1%)が、高齢では遠ざかる(60-69: 27.6 → 35.2%・錨 10.9%)。年齢勾配が無いのは W17 の就寝と既定の時刻の規則の組の性質で、項 1 の範囲の外。記録として残すだけでよいか。

### 2B-7 変更したファイル・再現

- src: `engine/energy.py`(`w17_wake_minute`・`OutOfAreaMeals(sleep_defer)`・`due_with_deferred`・`HomeMeals`・`EnergyLayer` の `meal_home` と `meals_out_deferred`)・`engine/resolve.py`(`energy_out_of_area_meal(deferred)`・`energy_home_meal`)・`engine/run.py`(3 切替口・結線・manifest)・`perception/renderer.py`(`hunger_words`)・`cli.py`(3 つの旗)。触っていない: `perception/templates.py`・`presence.py`・`build/`・`tools/`・`data/`・台帳・設計書。
- tests: 新規 `tests/engine/test_meal_bundle_2b.py`(初版 16 件・実資産 1,500 体のラン 5 本を含む。検収後に 3 関数を足して 19 関数・20 件(窓の境界は 2 通りのパラメータ))。
- 再現(リポのルートで・`$D`=この置き場):

```
python $D/wave2_bytecheck.py side --src <git archive HEAD の src> --label head --scratch <作業用> --out <作業用>/head.json
python $D/wave2_bytecheck.py side --label work --scratch <作業用> --out <作業用>/work.json
python $D/wave2_bytecheck.py side --label work_old --old '{"meal_sleep_defer": "off", "home_meal": "off", "hunger_words": "hungry"}' --scratch <作業用> --out <作業用>/work_old.json
python $D/wave2_bytecheck.py compare --head <作業用>/head.json --work <作業用>/work.json --work-old <作業用>/work_old.json --head-label 01b6f5b --out $D/item2b_byte_check.json
python $D/meal_bundle_measure.py all --scratch <作業用> --out $D/item2b_meal_bundle.json
```

### 2B-8 検収後の直し(親+別のサブの検収=[review-2b.md](review-2b.md)・実行役 Opus 5.5)

byte-check を取り直した([item2b_byte_check.json](item2b_byte_check.json)=**直しの後の値で上書き**)。`work`=作業木の既定・`work_old`=3 切替口と門(`meal_gate=per_wake`)を旧の値で明示。**19 構成すべて HEAD `01b6f5b` と一致**(final・呼数・blocks・calls の 14 列・`src_checks` ok)。

**(1) 項 2 の総呼数の差と揺らぎの床**([noise_floor_measure.py](noise_floor_measure.py) → [item2b_noise_floor.json](item2b_noise_floor.json))

- **床の測り方(実行役の案=未リサーチ(expedient))**: 旧のまま、tick 360(6:00)以後の範囲内の飲食店の食事のうち k 番目(k=0,1,2)の 1 回だけ、食べた体の食後の `since_meal` を +1 kcal・収支を −1 kcal にする(=摂取を 1 kcal 減らした食後の状態)。1 kcal は語の段の区切り(EER/3 × 0.25 ≈ 150〜200 kcal)の 1% 未満で、挙動には効かないはずの最小の違い。テープの calls を base と体ごと・tick ごとに比べた。

| 方策 | 腕 | final | 総呼数の差 | 呼数が変わった体 | 揺らぎを受けた体(数)自身の差 | ほかの体の差 | 呼数が最初に違う tick |
|---|---|---|---|---|---|---|---|
| mock | home(自宅の食事) | `6fdc00bd` | −421 | 1,922 | +1(30 体) | −422 | 435 |
| mock | 床 k=0 | `9beb7834` | 0 | 0 | 0(1 体) | 0 | — |
| mock | 床 k=1 | `9beb7834` | 0 | 0 | 0 | 0 | — |
| mock | 床 k=2 | `d2f3f859` | 0 | 0 | 0 | 0 | — |
| classical(記憶・関係 on・per_wake) | home | `beedc5b6` | +429 | 2,615 | 0(28 体) | +429 | 391 |
| classical | 床 k=0 | `b16da577` | **+315** | 2,033 | −2(1 体) | +317 | 486 |
| classical | 床 k=1 | `e42d190f` | 0 | 0 | 0 | 0 | — |
| classical | 床 k=2 | `fd88a69b` | +7 | 9 | +7 | 0 | 494 |

- 読み: classical では **1 kcal の揺らぎ 1 回で総呼数が 0〜+315(0〜0.29%)動く**。自宅の食事(28 回)の +429(0.39%)は同じ桁。mock では 1 kcal の揺らぎ 3 回とも呼数が変わらなかった(final は変わる=状態は分かれるが、起床に届かなかった)。自宅の食事は 30 体の空腹を数百 kcal ずつ動かすので、mock でも広がる(−421)。**床の標本は 3 本だけ**なので、床の幅は粗い(問い Q-2B-2)。2B-2 と Q-2B-2 の説明はこの事実に書き直した。

**(2) `OutOfAreaMeals` の docstring**: 「食事行と就寝の行は重ならない」を「W17 には食事行が就寝の行と重なる体がある(5,000 体の月曜で 12 組・食事行由来の食事 2 回が W17 の就寝中に置かれる)=W17 の欠陥で項 1 の外・挙動はそのまま」に直した(文言だけ)。2B-2 の「72 本」を home 腕の 73 本に直した(30+73=103。72 は all_on の値)。

**(3) 食事の門 per_hour を「ハザードの積算」に変えた(親の決定・`engine/classical.py`)**

- **規則**: 体ごとに H を持つ。毎 tick、範囲内で起きている体(`activity != 就寝` かつ `transit_state==0`)に `H += −ln(1 − p_h(その tick の語の段)) × 分/60` を足す(p_h=`MEAL_WORD_P` の段の値だけ・満腹は 0=足さない)。門では `p = 1 − exp(−H)` に、カレンダーの係数(次の予定まで 30 分未満で ×0.3)と周囲の係数(×0.5・×1.2)を旧と同じ順序で掛け(上限 1)、H を 0 に戻す(p が 0 でも)。p_h=1 の段があれば H=∞=「必ず通る」扱い(上限を置かない・宣言。いまの最大は 0.9=起きない)。定数の値は動かしていない。manifest `classical.meal_gate.per_hour_rule`。
- **前の規則(§2A 2A-4)との違い**: 前は「範囲内で起きていた分」を積算して、評価のときの段の確率で換算した。このため食後に満腹(確率 0)で過ごした時間も、あとで「ふつう」になったときの Δt に入り、確率が大きく出た。
- **バイトと費用**: float32 **4 B/体**(per_hour の腕の中だけ・`per_wake` は配列を持たない=0 B)。毎 tick の費用は配列演算 1 本(起きて範囲内のマスク → 段の二分探索 → 段 → ハザードの表引き → 加算)。前の規則(マスク → 加算)に段の表引きが 1 つ増えた。逐次ループはない。
- **検算(テスト・`tests/engine/test_meal_gate_per_hour.py`・係数は同じ場面の旧の値で割って取り出す)**:
  - (i) ずっと「ふつう」で 60 分 → 0.1
  - (ii) 満腹で 120 分のあと「ふつう」で 60 分 → **0.1**(1 − 0.9^3 ではない)
  - (iii) 空腹 30 分+とても空腹 30 分 → 1 − 0.4^0.5 × 0.1^0.5
  - (iv) 8 時間眠ってから起床直後(5 分)→ 睡眠を数えない
  - (v) 範囲外に 3 時間いて戻った直後(1 分)→ 範囲外を数えない
  - (vi) 起床 20 分ごと → 10 分ごとで 1 日の食事の回数の期待値の差 < 3%(合成の 20,000 体・実装と同じ表)
  - (vii) per_wake は配列を持たず、門の値は旧のまま
- **(3b) Q-2B-6 の親の決定(いまの実装)**: 理由=「食事は積もった欲求を満たす」「いま満腹なら食事に行く決定は起きない」。
  - (ii) **食事のたびに H=0**: `since_meal` を 0 に戻す摂取=`resolve._energy_meal` を通る 3 種(飲食店の食事 `meal_in`=門を通った食事の成立・範囲外の食事 `meal_out`・自宅の食事 `meal_home`)。`_energy_meal` の中の 1 行(`energy.meal_reset[ids] = 0`)で戻す。`EnergyLayer.meal_reset` は `engine.run` が classical の `bind` の後に `ClassicalPolicy.meal_reset_array()`(per_hour の H・per_wake は None=何もしない)を渡す。**軽食・飲料**(`_energy_snack`=`since_meal` を摂取ぶん減らすだけ・0 に戻すとは限らない)**では戻さない**(コードの事実・テストで固定)。v1 の空腹モデル(エネルギー層なし)のランでは食事で H は戻らない(宣言)。
  - (iii) **評価の時点で満腹(p_h=0)なら p=0・H=0**(`meal_probability` の中で先に返す)。
  - 検算(テスト): (a) 空腹で 60 分積んだ後に自宅の食事 → H=0(範囲外・飲食店の食事でも 0)(b) 空腹で 60 分積んだ後、評価の時点で満腹 → p=0・H=0 (c) 軽食では H は戻らない (d) (i)〜(vii) はそのまま通る (e) 実資産 1,500 体の per_hour のランで満腹の段の通過 0(5,000 体は上の表で 0)。
- **計測の取り直し**(classical 5,000・記憶 on・関係 on。[item2b_meal_bundle.json](item2b_meal_bundle.json) の per_hour の行=③いまの実装。①の final と呼数は JSON の `previous_per_hour_rule`・②の値は `hazard_only_rule`。①の門の段の内訳は HEAD の src の同じ構成で取った)。

| 構成 | 規則 | final | 呼数 | 門を通った(満腹/ふつう/空腹/とても空腹) | 範囲内の食事 | 食事の回数/体 0・1・2・3・4+ | 欠食率 全体 / 20 代 / 自宅が範囲内 | 収支/体 中央値(平均) |
|---|---|---|---|---|---|---|---|---|
| per_wake・旧 3 切替口 | (門の規則を使わない・不変) | `28ea8037` | 110,395 | 13,493(0/5,096/6,456/1,941) | 9,993 | 7・34・669・2,296・1,994 | 7.5 / 7.2 / 51.5 | +16(+230) |
| per_wake・全部 on | (同) | `6fe8b265` | 110,215 | 13,293(0/4,902/6,163/2,228) | 9,682 | 6・156・994・2,132・1,712 | 11.7 / 9.5 / 51.3 | −0(+87) |
| per_hour・旧 3 切替口 | ① 前の規則(経過分の積算・§2A) | `3af0f54c` | 108,337 | 9,091(0/2,263/5,076/1,752) | 7,559 | 10・92・1,328・2,700・870 | 9.2 / 8.0 / 62.5 | −98(−164) |
| per_hour・旧 3 切替口 | ② ハザードの積算 | `c722bdbe` | 106,809 | 8,593(427/1,760/4,649/1,757) | 7,054 | 8・109・1,622・2,565・696 | 9.9 / 8.6 / 64.4 | −149(−246) |
| per_hour・旧 3 切替口 | **③ ハザードの積算+食事で H=0+満腹の門は 0=いまの実装** | `44088c4b` | 106,177 | 8,136(**0**/1,704/4,681/1,751) | 6,635 | 9・129・1,765・2,582・515 | 9.9 / 8.7 / 64.4 | −174(−303) |
| per_hour・全部 on | ① | `cc54b747` | 108,267 | — | 7,417 | 10・287・1,602・2,337・764 | 13.6 / 10.5 / 62.1 | −170(−288) |
| per_hour・全部 on | ② | `17c9f66d` | 105,987 | 8,441(435/1,695/4,385/1,926) | 6,922 | 10・331・1,828・2,239・592 | 14.3 / 11.2 / 63.9 | −262(−359) |
| per_hour・全部 on | **③ いまの実装** | `c066171e` | 106,219 | 8,000(**0**/1,730/4,355/1,915) | 6,536 | 9・356・1,941・2,282・412 | 14.2 / 11.3 / 63.1 | −289(−416) |

  - ① → ③: 「ふつう」での食事 2,263 → 1,704(−25%)・門を通った回数 −10%・範囲内の食事 −12%・収支の平均 −164 → −303 kcal。欠食率はほとんど動かない(朝食は既定の時刻と項 1 が決める)。
  - ②で出ていた**満腹で門を通った 427 回**(門の後に積もった H が、門を通らない食事=範囲外・自宅・軽食では 0 に戻らなかった)は、**Q-2B-6 の親の決定で解決**した(③=下の (3b))。③の 5,000 体のランで満腹の段の通過は 0(旧 3 切替口・全部 on・defer・home・words の 5 構成とも)。
  - §2A 2A-4 の per_hour の値(−163 kcal など・記憶 off・関係 off の構成)は前の規則の値で、§2A は書き換えていない。**§2B で門の規則を変えた**。

**(4) `--hunger-words all` の文面の指紋**

- `templates.template_sha256(hunger_draw_min_stage=None)`: None(既定)は定数 `HUNGER_WORD_DRAW_MIN_STAGE`=凍結値 `40af870e…` のまま。
- ラン manifest の `template_sha256` は、`hunger_words="all"` かつ `hunger_model="energy"` のランだけ、実際に描いた段の下限 0 で計算する(`51da9a7a02383843…`)。描画の報告行も同じ指紋を使う。
- hungry と v1 のランは凍結値のまま=既定は不変。
- テストで、hungry/energy・all/v1 → 凍結値、all/energy → 0 の値を確かめた。

**(5) テストを足した**(`tests/engine/test_meal_bundle_2b.py`)

- (a) 就寝 0:00〜7:40 と 7:40〜8:20 の 2 本 → 7:29 から連鎖して 8:20 に朝食(つながないと 7:40)。
- (b) 窓の境界を固定: 10:59 に起床 → 10:59 に朝食・11:00 に起床 → 朝食なし(窓を過ぎた数 1)。
- (4) の指紋のテスト。

**(6) 宣言に足す**(版上げのときのユーザーへの問いにも足す)

- 項 2 は同じ時間帯に 2 回食べることを防がない(自宅の食事+飲食店の食事。検収の数えで mock 8 回・classical 14 回)。同じ時間帯に自宅の食事行が 2 本ある体が 1 体あり、その体は 1 行 1 回のまま同じ時間帯に 2 回食べる。範囲外にも同じ形が元からある(範囲内+範囲外の同じ時間帯の重複は mock base で 731 件=検収の数え)。
- 項 1 の副作用: 夕食の既定の時刻(19:18)から 1 日の終わりまで眠っている体(検収の数えで 387 体・成人が主)は夕食を失う(起床 24:00=窓の外)。決定の文言「起床時に食べる」のとおりで、食事を前へ動かす規則は無い。
- ~~per_hour の H は、門を通らない食事では戻らない~~ → Q-2B-6 の親の決定で直した((3b))。軽食・飲料では戻らない(宣言)。

**(7) W17 の行の重なり**: 親が全母集団で数えた値は、連続する組 3,071,887 のうち 83,801(2.73%)・重なりの中央値 193 分(本段の 5,000 体では 2.88%・1,500 体では 2.90%)。Q-2B-1(自宅の食事がほとんど効かない)は選択肢 (i)〜(iv) のまま残す(ユーザーに出す)。

**追加の問い**

- ~~Q-2B-6(per_hour の H を食事で戻すか)~~: **親の決定で解決**((ii) と (iii) を両方入れた=(3b))。
- **Q-2B-7(夕食の既定・ユーザーへの問い)**: 19:18 から日の終わりまで眠っている体(387 体)の夕食を失うままにするか。

**変更したファイル(直しの分)**: `engine/classical.py`(ハザードの積算・表 `_HAZARD_PER_HOUR`・manifest の欄・満腹の門は 0・`meal_reset_array`)・`engine/resolve.py`(`_energy_meal` で H を 0 にする 1 行)・`engine/energy.py`(docstring・`EnergyLayer.meal_reset`)・`engine/run.py`(manifest の指紋・docstring)・`perception/templates.py`(`template_sha256` の引数)・`perception/renderer.py`(報告行の指紋)・tests `test_meal_gate_per_hour.py`(旧の規則の方策のテスト 1 件をハザードの規則のテスト 2 件に置き換え+Q-2B-6 の 3 件=8 件)・`test_meal_bundle_2b.py`(3 関数を追加=19 関数・20 件)・記録 `noise_floor_measure.py`・`item2b_noise_floor.json`(新規)・`meal_bundle_measure.py`(門の段の内訳)・`item2b_meal_bundle.json`・`item2b_byte_check.json`(取り直し)。

再現(追加分):

```
python $D/wave2_bytecheck.py side --label work_old --old '{"meal_sleep_defer": "off", "home_meal": "off", "hunger_words": "hungry", "meal_gate": "per_wake"}' --scratch <作業用> --out <作業用>/work_old.json
python $D/meal_bundle_measure.py all --scratch <作業用> --out <作業用>/classical.json --only classical_rel:base,...,classical_rel_hour:all_on   # 行を item2b_meal_bundle.json へ差し替え
python $D/noise_floor_measure.py all --scratch <作業用> --out $D/item2b_noise_floor.json
```
