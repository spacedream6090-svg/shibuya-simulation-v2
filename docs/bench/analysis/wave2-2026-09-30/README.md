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
