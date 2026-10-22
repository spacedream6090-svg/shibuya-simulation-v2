# 第 5 期 空間の段 1「ナビメッシュと移動」(sp1)

> 実装役(Opus 5.5)・2026-10-21〜23。作業木 `5-1/navmesh-and-movement`(土台 71c53bd)。commit・活性化(apply)・版上げの判断は親。
> 正: [空間の設計の下書き](../../../../design/v2-spatial-design-round-draft.md) §4 段 1・§2 SR10〜SR13・SR17/[指示書 10-06](../../../../design/v2-wallbounce-decisions-2026-10-06.md) SR10〜SR13/[指示書 10-03](../../../../design/v2-wallbounce-decisions-2026-10-03.md) §4 B8・§8 3-1・3-2 (c)・3-4-5・3-10 (a)。
> 切替口 `--space {legacy,nav1}`(**既定 `legacy`**・`nav1` は腕=段 1 の再検収 H1 の親の判断・指定は環境変数より強い)・腕 `--slope {wood,tobler}`・`--turn-weight {fixed,person}`(環境変数 `SHIBUYA_SPACE`・`SHIBUYA_SLOPE`・`SHIBUYA_TURN_WEIGHT`)。
> 独立検収 [review.md](review.md)(条件つき受入・中 5・低 7)の直しを §A に、再検収 review.md §B(条件つき受入・H1 ほか)の直しを
> §A-2 にまとめた。**親の判断(再検収の後)**: H1 は段 1 のうちには直さず、nav1 は既定にしない=本段は「切替口つきの腕(既定
> legacy)」として着地する。抽出のランの密度の推定は段 5-1b(3 案を 5,000 体のスクリーニングで測って選ぶ)で直し、確かめてから
> 小さな版上げで既定にする(回答 10-13b §0-6)。

## §0 結論

- 構築(navmesh1 1.1.0): 歩ける面を階ごとの 0.5 m の格子に塗り、ラン 221,784・帯 7,818・接続口 245・7 階(地上 797,320 m²)の
  ナビメッシュにした(9,175,362 B・2 回組んで同じ sha・門 8 項目合格・新しい依存なし)。国道・都道は tran:function で幹線の型
  (M1)・面は W2 のセルの中(帯でない面のはみ出し 0・つなぎの帯 5,177 m² は最も近いセルへ=M3)。
- **既定は legacy**(本段は腕として着地)。既定の 4 構成は HEAD と 25 欄同じ(`frozen_sources` を含む)=素の本体の v2 でも、資産を
  足した活性化の後の v2 でも。活性化の前の作業木で範囲の試験が通る。
- 腕 `--space nav1`: 体は面の上を本人の希望歩行速度 × 坂の係数で進み、階は接続口でだけ変わる。受入の 3 本は 5,000 体 × 1 日
  (v3)で違反 0(在不在の層の同じ刻みの退出と到着 18 件は別の欄=M2・刻みの終わりどうしで最大 1,355 m)。再開=通し。段 B の
  宣言の外 0。**既知の欠陥 H1**: 既定でない構成(帰無腕ほか)で Kladek の速さ 0 の詰まりが解けずに固まる(§4-5・段 5-1b)。
- 性能(腕): nav1 1 日 49.5 s(legacy 40.6 s・+22%)・2 日 101.6 s(82.6 s・+23%)・体あたり +26 B(nav1 のランだけ)。

## §A 検収の直し(2026-10-22〜23・[review.md](review.md) §2・親の判断)

| # | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| M1 | `build/space/navmesh1.py` `_function_first` | 道の種類は tran:function 2(一般国道)・3(都道府県道)を先に幹線の型=両端 2.0 m(仮)・不明 9020 だけ W1 の最も近い車の辺から写す。国道 LOD1 62・都道 LOD1 366 地物が全部幹線の型に(前は国道 35・都道 89 が住宅街の型=面全体) | `tests/build_space/test_navmesh1_units.py::test_m1_function_2_3_are_trunk_first_and_9020_keeps_the_w1_copy` |
| M2 | (直さない・親の判断) | 受入の道具で別の欄 `same_step_depart_arrive` に数える(移動の外にも違反にも入れない・刻みの終わりどうしの距離=M2-r)・台帳 `DOC-nav1-presence-same-step-depart-arrive`(外す段 6-6・PENDING §1-1b) | `tools/accept_345.py`(§3) |
| M3 | `navmesh1.py` `_mask_by_cells`・`world/navmesh.py` `cell_lookup_table(fill_nearest=True)` | つなぎの帯でない面は毎回 W2 のセルの被覆で切る(門 `area_outside_cells_m2`=0)。つなぎの帯(bridge_w1)は切らず、その上の体のセルは最も近い W2 の地上のセル(升の中心の距離・同じなら番号の小さい方)へ倒す。受入の (b) で −1 どうしを一致に数えない(別の欄 `b_onmesh_cell_minus1`=0) | `test_m3_mask_by_cells_removes_the_cell_less_squares_only`・`test_m3_fill_nearest_maps_cell_less_squares_to_the_nearest_ground_cell`・`test_m3_synth_surface_is_inside_the_cells` |
| M4 (a) | `engine/space/nav1.py` `surface_counts`・`density_area_m2`・`engine/resolve.py`(3 か所)・`systems/build.py` | 人/m² = 面の上に居て建物の中でない体の数 ÷(ナビメッシュのセルの面積 × 抽出の割合)。抽出の割合=経済と同じ `population_total`(5,000/345,858=0.01446・総数が無ければ 1)。建物の中と数える体=在店・並び・購入・就寝・経路の外で入口の点に立ち止まった体。段(Fruin の境)と Kladek の両方に同じ値・境と式は変えない。Kladek は刻みの頭の状態から数える(再開でも同じ) | `tests/engine/space/test_nav1_units.py::test_m4_density_denominator_is_area_times_population_scale`・`test_m4a_surface_counts_leave_out_the_agents_inside_buildings` |
| M5 | `engine/calendar_self.py` `hop_walk_steps`・`calendar2/layer.py`・`systems/build.py` | 暦 1b の見積りと暦 2 の「間に合わない」を、nav1 では節の数 × 節 1 つの刻み(W1 の辺長の平均 ÷ 本人の m/刻み=`walk_m_per_tick`)に。legacy は今のまま(1 刻み 1 節)。状態台帳の除外に `hop_steps`(組み立てが置く定数) | `test_m5_hop_walk_steps_legacy_is_one_step_per_node_and_nav1_uses_the_speed` |
| 問い 2 | `navmesh1.py` `_ramp_or_stairs` | スロープの上限 1/12(高さ 16 cm 以下は 1/8=R-64 §4)。勾配 0.01 未満で階をまたぐ W1 の辺 2 本を数える(台帳 `DOC-nav1-w1-interband-flat-edges`) | `test_b9_ramp_limit_is_1_12_and_1_8_under_16_cm` |
| 問い 3 | `engine/proximity.py` `marks_for` | B6 の印の文を nav1 用に(立ち止まった体も面の上の点・建物の中は入口の点) | `test_q3_b6_mark_text_for_nav1_and_no_b8` |
| 問い 4 | `systems/build.py`・`space/nav1.py` `is_production_world` | 本番の世界(`build_manifest.json` の build_hash を持つ世界)で資産が無ければ FileNotFoundError(文に「`activate_sp1.py apply` で資産を入れるか `--space legacy`」)。合成の世界は legacy で回して manifest に書く | `test_q4_production_world_is_the_one_with_a_build_hash`・`tests/engine/space/test_nav1_world.py::test_q4_production_world_without_assets_stops_and_legacy_runs` |
| L1 | `docs/design/bridging-ledger.json` | 行を足した: BR-NAV1-B10(切れ目 12 m・閉じ 1 m)・B11(端を寄せる 15 m・節の短い帯 300 m)・B12(回廊 40 m)・B13(セルで切る・帯は最も近いセルへ)・E7(広い探索への落ち)・`BR-NAV1-DENSITY-SAMPLE-SCALE`・DOC 2 行 | `tests/engine/bridging/test_bridging_ledger.py`(式の数 268) |
| L2 | `docs/design/v2-budget-declaration.md` | §4 に段 1 の〔追加〕 | — |
| L3 | `nav1.py` `advance_kernel`・`onto_surface`・`resolve._nav_stop` | スロープの中は両端を結ぶ線の上を時間の割合で進む(1 刻みの動きは速さ × 刻みの中)。線が W2 のセルの外を通るスロープは端の点のまま(manifest `space.navmesh.ramps_on_end_points`=0・M3 の後は全部線の上)。スロープの中で止まった体と経路の外れた体は同じ階の面の最も近い点へ寄せる。階段・ES・EV の端の跳びは宣言のまま | `test_l3_ramp_inside_is_on_the_line_and_within_the_speed_bound` |
| L4 | `nav1.py`・`tools/c8/sensitivity_v1.json` | `tick_seconds` の既定 60 を消した(呼び手の刻みの長さ)・`RoutePool.compact` に逐次ループ宣言・感度の表の行番号 535 → 582・`--space`/`space=` の指定は `SHIBUYA_SPACE` より強い(CLI の既定 None)・manifest の `requested` は解いた値 | `test_l4_space_argument_beats_the_environment`・`test_l4_space_argument_beats_the_environment_in_a_run` |
| L5 | (本 README §1-2) | apply は足すだけ(先にあるファイルを断る)=退避は作らない・revert=足した 9 本を消す。親が当てるときは `--dry-run` を先に | — |
| L6 | (本 README §1-1) | スロープと階段の境・SR10 の 13.6 km と 24.2 km の違いを書いた | — |
| L7 | (本 README §8) | 張り替えの後の件数・活性化の前に落ちる本数を書いた | — |

## §A-2 再検収の直し(2026-10-23・[review.md](review.md) §B・親の判断)

| # | 箇所 | 直し方 | 試験・記録 |
|---|---|---|---|
| H1(判断) | `engine/space/nav1.py` `DEFAULT_SPACE`・`cli.py`(`_arm_norm`・ランの種類) | **既定を legacy に戻した**(`--space`/`space=` の既定 None → 環境変数 `SHIBUYA_SPACE` → legacy)。nav1 は腕のまま全機能。本番の世界で資産が無いときに止めるのは nav1 を頼んだときだけ。nav1(引数か環境変数)のランはランの種類で腕に数え、既定の legacy を明示で渡しても腕にしない | `tests/engine/space/test_nav1_units.py::test_l4_space_argument_beats_the_environment`・`test_nav1_world.py::test_default_is_legacy_on_the_staged_world`・§4-1 の既定の 4 構成 |
| H1(記録) | README §4-5・§9・台帳 `DOC-nav1-density-sample-jam`(外す段 5-1b=`PLAN_STAGES` に 5-1b を足した) | 既知の欠陥として構成ごとの進めない体刻みを表に | `tests/engine/bridging` |
| golden | 8 ファイル 15 行 | 張り替えた golden を前の値(legacy=HEAD)に戻し、nav1 の腕の値は注に残した。nav1 の腕の golden は `test_nav1_world.py::test_nav1_arm_golden_w6_v3_default_on_the_activated_world`(資産を足した本番の v2 でだけ回る=無ければ skip) | §8-1 |
| M4-b | README §4-5 | 小さい面の升の量子化を記録(段 5 の 138 のうち 129 はセル 36=歩ける面 24.25 m²・段の変化の 71% は 500 m² 未満のセル)=5-1b の 3 案で扱う | — |
| M2-r | `tools/accept_345.py` | 同じ刻みの退出と到着を刻みの終わりどうしの距離で測る(退出と到着の xy は apply の外の `rail_arrive` が書く)=18 件・最大 1,355 m(再検収の自前の道具は 19 件) | `accept_345.json` |
| L8 | 台帳 `BR-NAV1-DENSITY-SAMPLE-SCALE`(コードの表の文) | あたりで節に着いて立ち止まった体も建物の中に数える=通りの混み具合を少なめに数える向き、を 1 文 | `tests/engine/bridging` |
| L9 | `engine/space/nav1.py`(`NavSpace` の組み立て) | 線の上から面の最も近い点までが最も遅い体の 1 刻みの上限(`DESIRED_SPEED_MIN_MS` × 刻み=60 m)を超えうるスロープは端の点(跳び)のまま=寄せは上限を超えない(組み立てで 64 点を引いて確かめる)。13 本のうち 4 本(辺 1489・4576 の 2 本と、出口の階の面が線から遠い 2 本)。寄せた最大 4.94 m(前 48.7 m) | `space.navmesh.ramps_on_end_points`=4・`accept_345.json` の `snap_max_m` |
| L10 | README §4-1 | 食事の幅を JSON の値に | — |

## §1 構築(`src/shibuya/build/space/navmesh1.py`・脇の段・資産 `data/world/v2_stage_5-1/`)

### 1-1 作り方(SR13 (a)=numba で自前・新しい依存なし)

PLATEAU の三角形をそのまま溶接する代わりに、歩ける面を **階ごとの 0.5 m の格子に塗り**(出どころの札つき・先に塗った
ものが勝つ)、行ごとの **ラン**(横 1 行の長方形=凸)→ 上下の行で重なる **門** → 1 対 1 でつながるランの縦の鎖の **帯**
(A* の節)に分けた。地物の継ぎ目(T 字・重なり・LOD2 と LOD3 の重複)は塗りの和で溶ける。経路は帯の A* で引き、funnel は
帯の中の行ごとの門まで含めた門の列で引く=ランの和の中の最短の折れ線(格子の角まで)。shapely・laspy は使っていない。

塗りの順(地上・先が勝つ): ① PLATEAU 道路 LOD2/3 の歩道部 2000・島 3000(高架 2・アンダーパス 5・トンネル 6 の区間と都市高速 5 は
入れない)② PLATEAU 都市設備の横断歩道 1110(縞の最小の外接矩形)③ **SR10**: 歩道部の無い LOD2/3 の道の車道部(地物の道の
種類が住宅街の型なら全部)④ **SR10**: LOD1 しか無い道=住宅街の型は面全体・幹線の型は道の外の縁から 2.0 m(仮)⑤ OSM の
`footway=crossing` の線の帯(幅 OSM の `width`・無ければ 4.0 m 仮)と、線の無い `highway=crossing` の点から車の道に直交する帯
⑥ OSM の歩行系の線(`width` があればそれ・無ければ道の種類の既定幅)・W1 の歩行系の辺の線(2.0 m)⑦ **面の無い W1 の車の道**
(道の種類の既定幅・tertiary 以上 4.0 m)⑧ 細い道の口の短い切れ目(W1 の住宅街の型の線の上で両側が歩ける面・12 m 以下=仮)。
**道の種類(M1)**: PLATEAU の `tran:function` 2(一般国道)・3(都道府県道)は幹線の型。不明(9020)の地物だけ、格子の目ごとに
最も近い W1 の車の辺の種類を写して地物ごとに多い方(交差部 sectionType 4 は住宅街の型の線が中を通れば住宅街の型)。

デッキ(階 1・2)・地下(階 −1〜−4): W1 の層の辺と OSM の層つきの線の帯・歩行空間ネットワーク 2020 の floor 0.5/1 のリンク(幅員
4 区分の中央)・PLATEAU 橋梁 LOD2 の上面(帯から 6 m の中だけ)・PLATEAU 地下街 LOD4.1 の床(層の高さで 4 つの階に)。
高さ: 地上は DEM(TIN を 2 m の格子に)・デッキは橋梁の上面(無ければ地面 + 5.0 m 仮)・地下は地下街の床(無ければ 1 階 5.0 m 仮)。

**つなぎ**: 塗りの閉じ(幅 1 m 以下の隙間と角だけで触れる所)・W1 で行けるのに面が切れていた所を辺の近くの 2 つの塊の最も
近い 2 点で結ぶ帯(`bridge_w1`)・面から 30 m より遠い W1 の節から面までの短い帯(`anchor_stub`・300 m の中)。
**範囲(M3)**: W2 のセルの被覆。毎回、帯でない面のうちセルの無い 100 m の升(その層のセルも地上のセルも無い)の目を消す。
つなぎの帯は切らない(範囲の外をつなぐ帯=体のセルは最も近い地上のセルへ倒す)。区外(目黒区・港区の部分)は線の帯だけ。

**SR10 の「載らない 13.6 km」と実装の「面の無い W1 の車の道 24.2 km」の違い(L6)**: SR10 の表の 13.6 km は答申が数えた
「PLATEAU の道の面にも OSM の歩行系にも載らない W1 の辺」の長さ(範囲は答申の範囲)。実装の 24.2 km は、W2 のセルの列の中で
W1 の車の辺を 0.25 m おきに見て、PLATEAU の道の面の外にある区間(3 m 以上)を足した長さ=OSM の線の帯の上も数える・範囲が
広い。どちらも同じ規則(道の種類の既定幅で塗る)に入る。

上下の接続口(Detour の off-mesh 接続と同じ形): W1 の階をまたぐ辺(steps=階段・elevator=エレベーター・ほか=スロープ)・
PLATEAU 地下出入口 4020(種類の属性が無い=階段)・歩行空間ネットワーク 2020 の route_type 4/5/6/7 で floor の違うリンク。
**スロープと階段の境(問い 2・L6)**: R-64 §4 の傾斜路の勾配の上限 1/12 を超えるスロープは階段と置く。高さ 16 cm 以下は同じ
§4 の例外で 1/8 まで。前の 1/8 は「16 cm 以下」の例外の値で、何 m も上がる接続口には 1/12 が合う。
値=SR11 (a)+(d)(階段 65.7 人/分・m × 幅・ES 95.3 人/分・EV 11 人 × 60 / 間隔 60 s(仮)・待ち=間隔の半分 30 s)。改札は段 4。

### 1-2 構築の表(`navmesh1.header.json`・stage_version 1.1.0・2 回組んで全ファイルの sha256 が同じ=[stage_build.json](stage_build.json))

| 項目 | 直した後 | 直す前(1.0.0) |
|---|---|---|
| ラン / 帯 / 帯の間の門 | 221,784 / 7,818 / 9,060 | 218,793 / 7,683 / 8,904 |
| 歩ける面積 [m²] | 地上 797,320・デッキ 28,685 / 3,484・地下 8,985 / 6,083 / 5,863 / 2,657 | 地上 867,318(ほかは同じ) |
| 出どころ: PLATEAU [m²] | 610,411(歩道部 126,395・LOD1 の面=住宅街の型 327,087・歩道部の無い車道部 128,985・横断歩道 1,378・地下街の床 15,094・橋梁の上面 11,473) | 705,414(LOD1 の面 420,652) |
| 出どころ: 既定の幅 [m²] | 208,961(幹線の縁 2 m 53,923・W1 の線 91,667・OSM の線 57,978・切れ目 854・閉じ 649・節の短い帯 1,224) | 188,553(幹線の縁 44,117) |
| 出どころ: OSM の幅つき・歩行空間 NW [m²] | 18,897(横断の線 16,060・横断の点 5,393 の一部…)・3,353 | 15,139・3,353 |
| つなぎの帯 bridge_w1 [m²] | 8,730(うち W2 のセルの外 5,177=最も近いセルへ倒す) | 7,949 |
| 道の地物の種類 | LOD1: 住宅街の型 2,719・幹線の型 1,326(国道 62・都道 366 は全部幹線)/歩道部の無い LOD2/3: 805・115 | LOD1: 2,961・1,084 |
| 接続口 245 | 階段 225・スロープ 13・EV 6・ES 1(W1 181・地下出入口 55 地物 → 6・歩行空間 NW 59) | 階段 214・スロープ 24 |
| 塊 | 164・最大の塊が面積の 96.6%・別の塊に分かれた W1 の辺 2 本・最大の塊の節 3,486/3,499 | 159・97.0%・2 本・3,486 |
| W1 の節の錨 | 3,499/3,499・距離 p50/p95/最大 0/3.98/18.5 m | 0/2.72/16.21 m |
| セルの歩ける面積 | 519 セル・p50 1,641 m²・最大 5,323 m²・超過 0・帯でないはみ出し 0(門) | 最大 5,955 m²・はみ出し 5,193 m²(多くは帯) |
| 勾配がほぼ 0 で階をまたぐ W1 の辺 | 辺 1489(1,030 m)・辺 4576(616 m)・高さの差 0.35 m(DOC の行) | — |
| 資産のバイト | 9,175,362 B(DEM 7.54 MB・ラン 0.94 MB・回廊 0.26 MB・帯 0.21 MB) | 9,146,452 B |
| 組み立て | 19〜23 s・門 8 項目合格(`area_outside_cells_m2`=0 を足した) | 7 項目 |

最大の塊の割合 97.0% → 96.6% は M1 の分(国道・都道の車道の真ん中が歩けなくなった=セルで切らない組み立てでも 96.6%)。

活性化の計画([activation_plan.json](activation_plan.json)): 本体の v2 と同じ 143 本・置き換え 0・追加 9(`nav1_*` 8 本と
`navmesh1.header.json`)・段 1 の外の変化 0。道具は [tools/activate_sp1.py](tools/activate_sp1.py)(stage/plan/apply/verify/revert)。
**apply は足すだけ(L5)**: 先にあるファイルがあれば断る・置き換えのある plan は当てない=退避は作らない。revert=足した 9 本を
消す。親が当てるときは `apply --dry-run` を先に。既定は legacy なので、apply の前でも後でも既定のランと golden は変わらない
(nav1 の腕の golden の試験だけが apply の後に回る=§8)。

## §2 移動(`src/shibuya/engine/space/nav1.py`・`world/navmesh.py`・`world/navmesh_route.py`・`engine/resolve.py`)

- **経路(SR12 (a))**: ① W1 の向きつきの辺の Dijkstra(曲がる 1 回=45° 以上で 50 m・上り 1 m=3.8 m)で道筋 → ② 道筋の辺から
  40 m の中の帯(全部の階)を回廊にして帯の A*(接続口は時間 × 1.34 m/s + 上り)→ 着かなければ全面の A*(広い探索=曲がる重みが
  効かない・E7)→ funnel。腕 `--turn-weight person`=人ごとに 32〜62 m。候補 3 つの関数 `NavPlanner.candidates` は呼び手なし。
- **時間(SR12 (d))**: 本人の希望歩行速度(体の属性 U(1.00, 1.60) m/s)× 坂の係数(Wood 2023・腕 Tobler)。区間は 5 m 以下・
  勾配は前後 10 m の DEM の差でならす。**混み具合(M4 (a))**: 刻みの頭の「面の上に居て建物の中でない体」の数 ÷(セルの面積 ×
  抽出の割合)で Kladek の減速。
- **接続口(SR11)**: 階段=高さ ÷ 上下の速さ + 水平の残りを歩く・ES=高さ ÷ sin30° ÷ 0.5 m/s + 残り・EV=高さ ÷ 0.75 m/s(仮)+ 待ち
  30 s + 水平の長さ・スロープ=坂の式(勾配 ±1/8 で切る)。容量は 1 分あたりを刻みに割り、超えた分は先着順で待つ。
  **中の位置(L3・L9)**: スロープは両端を結ぶ線の上(線から面までが 60 m を超えうる 4 本は端の点)・階段と ES と EV は端の点
  (半分で跳ぶ=E3)。
- **位置と状態**: (x, y, 階)。セルは面から導く(層のセルが無ければ地上のセル・セルの無い升=つなぎの帯の上は最も近いセル)。
  状態は 8 欄 26 B。経路の形はエンジン側の置き場(状態から作り直せる=再開で同じ経路)。
- **エンジンの 4 か所(書くのは `engine/resolve.py` だけ)**: 新しい行動を選んだ体はその場に止まる(スロープの中なら面の最も
  近い点へ寄せる)・エンジン継続の体は 1 刻み進む・位置の確定で (xy, 階) → セル・層と密度の段(面の上の体だけ)・ランの頭で
  体を節の点へ置く。
- **既定と切替口**: 既定は legacy。nav1 を頼んだとき、合成の世界は legacy で回して manifest に書き、本番の世界(build_hash あり)で
  資産が無ければ止める。
- **暦の見積り(M5)**: nav1 では節の数 × 節 1 つの刻み(本人の歩く速さから)。

## §3 受入の試験(3-4-5)

道具 [tools/accept_345.py](tools/accept_345.py)(`resolve.apply`・`NavSpace.advance`・在不在の `_depart_now`/`_do_arrive` を包んで
刻みごとに全員の前後を比べる)・5,000 体 × 1 日・v3・`--space nav1`(final d8b2d497…=19 構成の nav1 の w6_v3_default と同じ)・
記録 [accept_345.json](accept_345.json)。

| 項目 | 数 | 判定 |
|---|---|---|
| (a) 歩いて動いた体の刻み | 114,888 | 上限を超えて接続口を通らないもの **0**(最大の比 3.59 は接続口を通った刻み) |
| (a) 階が変わった体の刻み | 17,963 | 接続口を通った 17,954・同じ刻みの退出と到着 9・接続口なしの歩き **0** |
| (a) 移動の外の位置の変化 | 14,418 | 在不在・列車で node が変わった体を節の点へ 12,747・域外/車内へ 1,634・スロープの中で止まって面へ寄せた 37(最大 4.94 m=上限の中・L9)・説明のつかないもの **0** |
| (a) **別の欄**: 同じ刻みの退出と到着(在不在の層・M2・刻みの終わりどうし=M2-r) | **18** | 最大 **1,355 m**(地上 → 地下を含む)・階が変わった 9(移動の外にも違反にも入れない) |
| (b) 状態が 1 つ | 体刻み 2,831,046 | セルの食い違い **0**(−1 どうしは数えない)・層の食い違い **0**・面の上なのに車内/域外 **0** |
| (b) **別の欄**: 面の上でセルが −1 | **0** | (直す前 621=M3) |
| (c) 面の外に居ない | 体刻み 2,831,046(接続口の中 8,690 を除く) | 面の外 **0** |

段 B(`SHIBUYA_SYSTEMS_CHECK=1`・300 体・nav1・全刻み): 宣言の外 **0**。負の対照(phase_c の宣言から `agents.nav_t` を外す)で
**1,014 件**を見つけた。記録 on/off(`SHIBUYA_EVENTS`・500 体): final・behavior-hash・full-hash の checkpoint が全部同じ
(final 7829c24a…)。道具 [tools/checks_sp1.py](tools/checks_sp1.py)。

## §4 動いた量

### 4-1 19 構成(byte_check_10e・5,000 体 × 1 日・HEAD 71c53bd と作業木)

- **既定(引数なし=legacy)の 4 構成**(w6_v3_default・w6_v3_activity_off・w6_v1_default・v3_mem_rel): HEAD と **25 欄すべて同じ**
  (`frozen_sources` を含む)=素の本体の v2(nav1 の資産なし・[bc4_head_vs_default_plain.json](bc4_head_vs_default_plain.json))でも、
  資産を足した活性化を模した木の v2([bc4_head_vs_default_activated.json](bc4_head_vs_default_activated.json))でも=apply の後に本体で
  legacy が動かない。
- **`--space legacy`(世界 v2_stage_5-1)**: 19/19 構成で 25 欄すべて HEAD と同じ([bc19_head_vs_legacy.json](bc19_head_vs_legacy.json))。
- **腕 nav1**: 19/19 構成で final が動いた([bc19_head_vs_nav1.json](bc19_head_vs_nav1.json)・L9 の後に取り直した)。

| 構成 | 呼数 HEAD → nav1 | 食事 HEAD → nav1 | 気づいた | 平均の遅れ[分] |
|---|---|---|---|---|
| w6_v3_default(= v3_mem_store) | 63,572 → 61,261 | 4,414 → 4,053 | 465 → 578 | 6.4 → 8.4 |
| w6_v3_activity_off | 49,462 → 44,821 | 3,412 → 2,969 | 224 → 378 | 9.8 → 8.6 |
| w6_v1_default | 50,447 → 46,055 | — | 590 → 427 | 6.2 → 8.4 |
| w6_v1_derive_v2_1 | 45,099 → 40,192 | — | 744 → 423 | 9.2 → 11.0 |
| w6_v2 | 52,069 → 47,484 | 2,183 → 1,868 | 718 → 919 | 9.2 → 6.4 |
| w6_v1_edge | 45,416 → 46,055 | — | 256 → 427 | 7.6 → 8.4 |
| w6_v2_edge | 46,720 → 47,484 | 1,914 → 1,868 | 610 → 919 | 8.2 → 6.4 |
| w6_v1_edge_plateau | 46,485 → 47,653 | — | 280 → 663 | 9.6 → 11.8 |
| w6_golden_null_arm | 97,250 → 87,274 | — | 2,295 → 2,715 | 9.0 → 7.6 |
| v3_mem_rel | 66,374 → 63,877 | 4,555 → 4,280 | 340 → 423 | 8.4 → 9.8 |
| v3_classical | 91,791 → 91,969 | 9,612 → 9,135 | 715 → 784 | 9.0 → 9.0 |
| v3_classical_mem_rel | 102,368 → 103,684 | 9,961 → 9,544 | 693 → 763 | 9.0 → 9.0 |

(w6_old_* の 6 構成は対応する w6_* と同じ呼数・食事。)HEAD からの幅は呼数 −10.9〜+2.5%・食事 −14.4〜−2.4%
(L10=JSON の値から計算)。M4 の分母を「面積 × 抽出の割合」にしただけの途中の版(分子=全員)では v3 で駅の周りの 8 セルが詰まった
(1 日 418,127 体刻み)=(a) で v3 の詰まりは消えたが、既定でない構成では詰まりが解けない(H1=§4-5)。気づいた数と遅れは事象 10 件・
出動 5 件の標本で決まる量(review.md §1 の 5)。

### 4-2 1 日・2 日・再開(runs_sp1・5,000 体・vocab v3・activity・seed 1・[runs_sp1.json](runs_sp1.json))

| ラン | final | 呼数 | セルの移動 | 密度の段の変化(セル × 刻み) |
|---|---|---|---|---|
| nav1 1 日 | d8b2d497eef28887 | 61,261 | 81,031 | **4,829**(M4 の前 8) |
| legacy 1 日 | bb86f89855172717(=HEAD) | 63,572 | 79,717 | 21,611 |
| nav1 2 日 | 2a323425210173f7 | 133,070 | 173,659 | 9,994 |
| legacy 2 日 | 38d5d5674b90f993 | 138,821 | 175,382 | 45,237 |
| nav1 2 日を 1,860 で止めて再開 | 2a323425210173f7(**通しと同じ**) | 66,924 + 66,146 | — | — |

密度の段の分布(nav1 1 日・セル × 刻み): 段 0 743,722・1 2,355・2 1,749・3 598・4 238・5 138(legacy は段 0 が 326,316・段 1 が
318,531=人/セルの境)。

### 4-3 移動の計器(nav1・manifest の `space.meter`)

| 計器 | 1 日 | 2 日 |
|---|---|---|
| 着いた移動 | 16,369 | 35,106 |
| 1 回の歩く長さ / 時間の平均 | 411.2 m / 358.5 s | 408.9 m / 356.3 s |
| 歩いた合計 | 7,367 km | 15,817 km |
| 接続口(着いた移動の内訳) | 階段 18,986・スロープ 1,248・EV 17・ES 0 | 階段 40,599・スロープ 2,724・EV 38 |
| 接続口の前の待ち | 0 | 0 |
| 坂の効き | +1.6% | +1.8% |
| 経路: 新しく/同じ形の再利用/回廊/広い探索/着けない | 8,522 / 9,807 / 7,522 / 997(11.7%)/ 3 | 14,047 / 25,558 / 12,284 / 1,759 / 4 |
| 経路の途中で止まった | 1,773 | 4,124 |
| 混み具合で進めない体刻み(Kladek=0) | **184**(途中の版 418,127) | 1,877 |

### 4-4 12 時の診断(M4 (a) の後・道具 [tools/diag_density_sp1.py](tools/diag_density_sp1.py)・5,000 体・v3 既定)

| 時刻 | 速さ 0 のセル | 速さの係数の最小 | 人/m² の最大 | 面の上で数えた体 / 舞台の体 |
|---|---|---|---|---|
| 8 時 | 0 | 0.946 | 0.59 | 124 / 1,882 |
| 12 時 | **0** | 0.895 | 0.73 | 260 / 3,400 |
| 18 時 | 0 | 0.982 | 0.44 | 192 / 2,644 |

12 時の上位のセル: セル 326(地下・面 472 m²・全 7 体=面の上 5・中 2・移動中 1・0.73 人/m²)・セル 238(地上・988 m²・全 84=面の上 8・
中 76・移動中 2・0.56)・セル 292(デッキ・1,537 m²・全 10=面の上 8・中 2・0.36)。途中の版で詰まったセル(238・329 など)の体の
ほとんどは建物の中(駅・店)。(この診断は L9 の前の版・v3。)

### 4-5 既知の欠陥 H1 と小さい面の升の量子化 M4-b(再検収 review.md §B-2・段 5-1b で直す)

**H1**: 既定でない構成で Kladek の速さ 0 の詰まりが解けずに固まる。止まった移動中の体自身が分子に入り続けるので出口が無い。
分母 × 0.01446 で小さい升は数体で詰まりの密度に届く。1 日の進めない体刻み(nav1・5,000 体・再検収の計測):

| 構成 | 進めない体刻み/日 | 詰まるセル |
|---|---|---|
| w6_golden_null_arm(帰無腕) | **241,543**(7:40 ごろから日の終わりまで・同時に最大 611 体) | セル 326(地下 472 m²)・セル 293(778 m²) |
| w6_v3_activity_off | 20,296 | セル 329(170.5 m²) |
| w6_v2 | 14,864 | セル 329 |
| w6_v1_default | 13,876 | セル 329 |
| w6_v3_default(v3) | 184 | セル 36(24.25 m²・19〜21 時) |

**M4-b**: v3 の段 5 の 138 セル × 刻みのうち 129 はセル 36(地下・歩ける面 24.25 m²)に 1〜3 体が居ただけ(1 体で 2.85 人/m²)。
進めない 184 体刻みも全部同じセル 36。段の変化の 71% は歩ける面が 500 m² 未満のセル(444 m² のセルは約 2 体で段が 1 つ動く)。
**親の判断**: 段 1 では直さない=nav1 は既定にしない。段 5-1b で 3 案(セルごと/近傍=セル+隣接で均す/抽出の割合を掛けない)を
5,000 体のスクリーニングで測って選び、確かめてから小さな版上げで既定にする。台帳 `DOC-nav1-density-sample-jam`。

## §5 つなぎの台帳(`docs/design/bridging-ledger.json`・コードの表と 1 対 1+文書の行 3)

| ID | 何を | 外す段 |
|---|---|---|
| BR-NAV1-B1 | LOD1 だけの幹線は外の縁から 2.0 m(仮) | 7 |
| BR-NAV1-B2 | 面に載らない道の幅=OSM の width → 道の種類の既定幅・横断の帯 4.0 m(仮) | 7 |
| BR-NAV1-B3 | 道の種類=tran:function 2・3 は幹線・不明は W1 から写す | 7 |
| BR-NAV1-B4 | つなぎの帯(bridge_w1)・節の短い帯(anchor_stub) | 7 |
| BR-NAV1-B5 | デッキ +5.0 m・地下 1 階 5.0 m(仮) | 5-2 |
| BR-NAV1-B6 | 地下出入口は階段・幅の分からない階段 2.0 m(仮) | 5-4 |
| BR-NAV1-B7 | EV の間隔 60 s(仮)=待ち 30 s・定員 11 人 | 5-5 |
| BR-NAV1-B8 | 地下街の床の階の割り当て・階の間は接続口だけ | 5-2 |
| BR-NAV1-B9 | 種類の分からない階の辺=1/12(16 cm 以下 1/8)で スロープ/階段・スロープの中は線の上 | 5-2 |
| BR-NAV1-B10 | 細い道の口の切れ目 12 m(仮)・塗りの閉じ 1 m | 7 |
| BR-NAV1-B11 | 接続口の端を寄せる 15 m(地下出入口 20/40 m)・節の短い帯 300 m | 5-2 |
| BR-NAV1-B12 | 経路の回廊 40 m(仮) | 7 |
| BR-NAV1-B13 | 面は W2 のセルで切る・つなぎの帯は最も近いセルへ倒す | 7 |
| BR-NAV1-E1 | 経路の選びは既定の重み(本人の判断ではない) | 5-3 |
| BR-NAV1-E2 | 衝突なし(混み具合は Kladek の減速だけ) | 5-5 |
| BR-NAV1-E3 | 接続口の時間の式・EV 0.75 m/s(仮)・先着順・階段/ES/EV の中は端の点 | 5-5 |
| BR-NAV1-E4 | 新しい行動の体はその場に止まる・node=最も近い W1 の節・建物の中は入口の点 | 5-2 |
| BR-NAV1-E5 | 合成の世界の nav1 は legacy(本番の世界は止める) | 7 |
| BR-NAV1-E6 | 坂の勾配は前後 10 m の DEM の差でならす | 7 |
| BR-NAV1-E7 | 回廊で着けない経路は広い探索(曲がる重みが効かない・約 1 割) | 7 |
| BR-NAV1-DENSITY-SAMPLE-SCALE | 人/m² の分母=面積 × 抽出の割合・分子=面の上の体だけ(建物の中は段 2・駅の中は段 4 まで数えない) | 7(全数=39 万体のラン) |
| DOC-nav1-presence-same-step-depart-arrive | 在不在の層の同じ刻みの退出と到着(直さない・受入で別の欄・刻みの終わりどうしで 18〜19 件/日・最大 1,355 m) | 6-6 |
| DOC-nav1-density-sample-jam | 既知の欠陥 H1(抽出のランの密度の詰まり・構成ごとの進めない体刻み=§4-5) | 5-1b |
| DOC-nav1-w1-interband-flat-edges | 勾配がほぼ 0 で階をまたぐ W1 の辺 2 本(層の付け違いの疑い) | 5-0 |

## §6 性能とバイト(§0-7 の形)

機械: Windows 11・AMD64・論理 CPU 20・CPU だけ・LLM は mock。5,000 体・seed 1・各 1 本(別の作業木の試験が並走=壁時計は
±10% ほど揺れる)。

| ラン | 壁時計 | 1 刻み | 最大の作業集合 | 呼数(mock) |
|---|---|---|---|---|
| nav1 1 日(腕) | 49.5 s | 34.1 ms | 499 MB | 61,261 |
| legacy 1 日(既定) | 40.6 s | 27.9 ms | 485 MB | 63,572 |
| nav1 2 日(腕) | 101.6 s | 35.1 ms | 512 MB | 133,070 |
| legacy 2 日(既定) | 82.6 s | 28.5 ms | 502 MB | 138,821 |

nav1 の腕の増えは +22%(1 日)・+23%(2 日)。phase_c 3.2 s → 約 11 s(経路の引き 8,522 本と面の上の進み・密度の分子の数え)。
既定(legacy)は HEAD と同じ道=増えなし。逐次ループは宣言つき(経路の要る体・接続口の前の体・着いた体・止まった体・置き場の
詰め直し・スロープの組み立ての数ぶん)。バイト: 資産 9,175,362 B/世界・体あたり +26 B(nav1 のランの状態の 8 欄・既定では確保
しない)。予算の宣言 `docs/design/v2-budget-declaration.md` §4 に〔追加〕。

## §7 B8 の印(node の歩く速さ 0.41 m/s に基づく量)

| 量 | legacy(既定) | nav1 の腕(段 1 で外れた/残る) |
|---|---|---|
| 近接の印 `proximity.marks.B8` | 付く | **外れた**(B6 の文は nav1 用=面の上の点・建物の中は入口の点) |
| 店の選びの歩く速さ `walk_m_per_tick` | W1 の辺長の平均/刻み | **外れた**(希望歩行速度 × 刻みの秒) |
| 暦 2 の「間に合わない」 | 節の数 × 刻み | **外れた**(節の数 × 節 1 つの刻み=本人の歩く速さ・M5) |
| 暦 1b の時間の見積り | 節の数 × 刻み | **外れた**(同上・M5) |
| W1 の 1 刻み 1 節の移動 `step_once` | 使う | 使わない |

既定は legacy のまま=B8 の印は既定のランに残る(`DOC-prox22-b8-node-walk-speed` は nav1 を既定にする版上げ=段 5-1b の後まで active)。

## §8 試験

`-q -p no:cacheprovider -o addopts="" -rf -n 2 --dist loadfile -m "not gpu and not slow"`(tests/c7 は回していない)。

範囲 `tests/build_space tests/engine tests/perception tests/build_field tests/build_pop tests/economy tests/c6 tests/c8 tests/tools`。

| 木 | 結果 |
|---|---|
| **活性化の前の作業木**(本体の v2 に nav1 の資産なし・既定 legacy)・範囲 | **4,450 passed・0 failed・0 errors**・2 skipped(うち 1 は nav1 の腕の golden=資産が無い)・1 xfailed(54 分 9 秒) |
| **活性化を模した木**(`_bc/r`=data/world/v2 を最後に組んだ段の資産に差し替え・src と tests と tools は作業木の写し)・nav1 の腕の試験 `tests/build_space tests/engine/space` | **45 passed・0 failed・0 errors**(nav1 の腕の golden d8b2d497…/61,261 を含む) |
| 同じ木・既定(legacy)の golden の 8 ファイル+slow の K19 | **98 passed・0 failed・0 errors**(本文の値=HEAD のまま) |

既定の 4 構成の byte-check(§4-1)は素の v2 と模した木の v2 の両方で 25 欄同じ。
単体: `tests/build_space/test_navmesh1_units.py` 18 本・`tests/engine/space/test_nav1_units.py` 19 本・`test_nav1_world.py` 8 本。
lint-imports 5 契約 kept。秘密の検査 CLEAN(作業木の差分と新しいファイル)。

### 8-1 golden(既定は legacy=前の値のまま・nav1 の腕の値は注と腕の試験)

再検収の後の親の判断で既定を legacy に戻したので、張り替えた 8 ファイル 15 行を前の値(legacy=HEAD)に戻し、nav1 の腕の値は各行の
注に残した(`--space nav1`)。nav1 の腕の値は活性化を模した木で同じ引数を 1 本ずつ回して測り直した(L9 の後)。

| 試験 | 本文の値(legacy=HEAD) | 注の値(nav1 の腕・L9 の後) |
|---|---|---|
| `test_state_ledger_10b`(T7_V3_FINAL)・`test_state_checks_10f`(K19・slow) | bb86f89855172717 | d8b2d497eef28887 |
| `test_presence_executor`(W17 の表 02114fb577f3)帰無腕 | dcebb7c1d04b9d27 / 97,250 | fc31115bb6dc9e09 / 87,274 |
| 同 帰無腕 空腹 v1 | 730512bf7cc6b877 / 95,208 | 83070878d560b37f / 83,456 |
| 同 帰無腕 上限 1.0 | b239860914d1a3b0 / 41,089 | 857b1a00cec8b0c8 / 40,990 |
| 同 v3 既定 | bb86f89855172717 / 63,572 | d8b2d497eef28887 / 61,261 |
| 同 v3 空腹 v1 | 2e5ba0c90fc90099 / 63,618 | eddffcada215af43 / 60,293 |
| 同 v3 上限 1.0 | b698b0e54a588536 / 36,759 | 74d21977568e45a8 / 36,420 |
| `proximity/test_runs::test_cell_arm_equals_the_head_golden`(300 体) | 88b2d572…00d09 / 2,615 | f6e54d31…d119f2 / 2,642 |
| `perception/test_near_tiebreak`(古典 1,500 体・near_first) | f2309ff2…9e624e / 26,053 | 231f86e3…f4005e / 25,871 |
| `test_relations_tenure`(関係 on 5,000 体) | 94becde2c4fdb0d2 / 66,374 | 7cfa8bad2676996e / 63,877 |
| `test_classical_social::test_run_golden_and_arms`(古典 1,500 体・acquaintance) | 62254dd7…90238b / 25,302 | a223aa3f…e84c788 / 24,865 |
| `test_env_and_sections_10f`(上の表の写しの検査 3 行) | 上の本文の値 | 上の注の値 |

**nav1 の腕の golden**: `tests/engine/space/test_nav1_world.py::test_nav1_arm_golden_w6_v3_default_on_the_activated_world`
=w6_v3_default(5,000 体・seed 1・1 日・v3・`space="nav1"`)の final d8b2d497eef28887・呼数 61,261。資産を足した本番の v2(apply の後)
でだけ回り、資産が無ければ skip。

## §9 限界・仮採用・既知の欠陥

- **既知の欠陥 H1(段 5-1b)**: nav1 の腕の抽出のラン(5,000 体)で、既定でない構成の Kladek の速さ 0 の詰まりが解けない
  (帰無腕 241,543 体刻み/日・§4-5)=nav1 は既定にしない。段 5-1b で 3 案(セルごと/近傍で均す/抽出の割合を掛けない)を測って選ぶ。
- **M4-b**: 小さい面の升の量子化(v3 の段 5 の 129/138 と詰まり 184/184 がセル 36=24.25 m²・段の変化の 71% は 500 m² 未満のセル)。
- 仮の値: 幹線の縁 2.0 m・横断の帯 4.0 m・道の種類の既定幅・切れ目 12 m・閉じ 1 m・端を寄せる 15 m・節の短い帯 300 m・
  デッキ/地下 5.0 m・階段の幅 2.0 m・EV の間隔 60 s とかご 0.75 m/s・回廊 40 m・坂をならす基線 20 m(台帳 §5)。
- **建物の中の判定(M4 (a)・L8)**: 在店・並び・購入・就寝と「経路の外で入口の点に立ち止まった体」。あたり(WANDER)で節に着いて
  立ち止まった体も建物の中に数える=通りの混み具合を少なめに数える向き(段 2 で建物の中の位置が入るまでの近似・台帳の密度の行)。
- **同じ刻みの退出と到着(M2・M2-r)**: 刻みの終わりどうしで 18 件/日・最大 1,355 m(地上 → 地下を含む)=在不在の段で直す(6-6)。
- **スロープの寄せ(L9)**: 線から面までが 60 m(最も遅い体の 1 刻み)を超えうる 4 本は端の点=寄せの最大 4.94 m。辺 1489・4576 は
  W1 の層の付け違いの疑い(DOC の行)。
- **古い段の世界**: build_hash を持つ退避や段の世界を `--space nav1` で回すと止まる(資産が無い)=既定の legacy では止まらない。
- 広い探索 11.7%(曲がる重みが効かない)・着けない 3 本/日・地下出入口 55 → 6・地下の下 2 層の塊は小さい・区外は線の帯だけ。

## §10 触った共有ファイル

- `docs/design/bridging-ledger.json`(BR-NAV1 の 21 行+DOC 3 行)・`src/shibuya/engine/bridging/ledger.py`(`PLAN_STAGES` に 5-1b)・`docs/design/v2-budget-declaration.md`(§4 に 1 行)・
  `tools/c8/sensitivity_v1.json`(W1 の読み口に nav1 の 1 か所)・`docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py`(SWITCH_ENV に 3 つ)。
- エンジン: `agents/state.py`・`engine/resolve.py`・`engine/systems/{build,boxes,report,run_end,table}.py`・`engine/run.py`・`cli.py`・
  `engine/manifest_sections.py`・`engine/state_ledger.py`(nav の 8 欄・除外 `hop_steps` 2 行)・`engine/store_choice.py`・
  `engine/proximity.py`(B6 の文)・`engine/calendar_self.py`・`engine/calendar2/layer.py`(M5)・`perception/p_notice.py`。
- 凍結の一覧と試験: `writes_soa_frozen.json`・`manifest_keys_frozen.json` と末尾の鍵の試験 6 本・状態の台帳の試験・
  `test_env_and_sections_10f`・`test_boxes`・`tests/c8/test_sensitivity_ledger`・`test_bridging_ledger`(268)・golden の 8 ファイル(§8-1=本文は
  前の値のまま・注に nav1 の腕の値)。
