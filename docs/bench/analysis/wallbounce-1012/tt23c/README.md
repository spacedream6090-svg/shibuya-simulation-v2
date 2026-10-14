# 第 2 期 2-3c 鉄道の実ダイヤの残り(W12 1.3.0・渋谷の発着の表)

> 実行役(Opus 5.5)の記録。親の検収の前。commit していない。作業木 `2-3c/rail-arrivals`(土台 `d35a9b6`=2-4 版上げ 2 回目の取り込みの後)。
> 発注: 親(Fable 5.1)。正: [計画](../../../../design/v2-implementation-plan-2026-10-12.md) 2-3c の行(2-3b の検収 3)・[2-3b の記録](../tt23b/README.md)・[時刻表の記録](../timetables/README.md)(§7・[extraction-jr.md](../timetables/extraction-jr.md)・[extraction-tokyu-metro.md](../timetables/extraction-tokyu-metro.md)・[keio-odpt-challenge.md](../timetables/keio-odpt-challenge.md))・[回答 10-12b](../../../../design/v2-answers-2026-10-12b.md) §2・[回答 10-13](../../../../design/v2-answers-2026-10-13.md) の 2〜4・7。
> **既定は不変**(byte-check 19/19 で HEAD と同じ=§9)。資産は `data/world/v2_stage_2-3c/` に組んだだけ(本体の `data/world/v2` は書いていない・活性化は版上げ 3 回目 4-3)。
> 本書には件数・本数・版・sha だけを書き、**時刻は書かない**(時刻の一覧は `data/` の下の CSV と資産だけ)。ODPT チャレンジ枠(京王)の生の行は写さない。

## 0. 結論

- W12 を **1.3.0** にした。渋谷の**到着**の行と、直通の二重計上を 1 本に結ぶ列を、新しい表 **`w12_rail_events.parquet`**(8,495 行=発車 6,273+到着 2,222)に入れた。**発車の表 `w12_timetables.parquet` は 1.2.0 とバイト一致**(`7ef7ab9038348e59`)=エンジンは今の表を読み、新しい表は読まない。だから資産を活性化しても結果は動かない見込み(§9 の情報の side で確かめた)。
- **到着**(平日/土休): 銀座線 362/307(ODPT オープン枠 9 月改正)・半蔵門線 282/209 と副都心線 259/237(ODPT オープン枠 2026-03-14 の列車時刻表)・井の頭線 305/261(チャレンジ枠の列車時刻表)。JR(途中駅)・東急から地下鉄への直通・東急の渋谷止まりの到着の時刻は**空欄**(§6)。
- **直通のまとめ**: 東急の上り=地下鉄の行と同じ列車 995 組(東横線↔副都心線 497・田園都市線↔半蔵門線 498)を列車の鍵で結び、数えるのは 1 回にした。下りの直通(地下鉄の渋谷着 → 東急の渋谷発)984 組を結んだ。成田エクスプレスの 104 本は湘南新宿ラインの表に全部含まれた。相鉄線直通の 92 行に相手の線を付けた(大崎方面の表との重なり 0)。**規則で残った疑わしい組は 0**。ただし、下りの組み方は「同じ行き先の便は渋谷で追い越さない」という推測に頼り、入れ替わっても成り立つ隣どうしの組が 25 ある(§4)。
- 下りの直通を決めるため、東急の渋谷の下りの 2 表(TY01_2・DT01_2)から**当駅始発の印**(●・⑤・②=185 個)を新しく読み取った。読み 1(機械)と読み 2(目)の食い違いは 1 件だった(読み 2 の見落とし・300 dpi で確かめて決着)。ODPT チャレンジ枠の `isOrigin` と分まで **185/185 一致**した(照合だけ・§3)。
- 1 日の本数(発車の行 → 1 本として数える発車): 平日 3,359 → **2,811**・土休 2,914 → **2,467**(東急の上りの行を地下鉄の行で数えるため)。
- つなぎの台帳: 外す段が 2-3c の 4 行は**外せなかった**(エンジンが到着の行を読まないため)。外す段を改めて理由を書いた(4-3 が 2 行・5-0 が 1 行・rail.py の見出しの行は 7=〔検収 L6〕項ごとの行 6 つに分けた=§11)。新しい宣言 1 行(下りの直通の結び=expedient・外す段 7)。

## 1. 作ったもの・変えたもの

| ファイル | 種類 | 中身 |
|---|---|---|
| `src/shibuya/build/field/w12_rail_events.py` | 新規 | 渋谷の発着の表の組み立て(発車の行の属性の突き合わせ・地下鉄と京王の到着・直通のまとめの規則 4 つ・空欄の宣言・要約)。docstring に列の表 |
| `src/shibuya/build/field/w12_external_nodes.py` | 変更 | 版 1.3.0。発着の表を組んで書く・版の表に節 `rail_events`・ヘッダの notes・ゲート 3 つ・宣言の表 `RAIL_EVENT_EXPEDIENTS`(1 行)・params に規則(conf つき)。時刻表の組み立ては変えていない |
| `src/shibuya/build/field/w12_real_timetables.py` | 変更 | 入力の一覧 `input_rel_paths` に 2-3c の入力 7 本(成田エクスプレスの表 4・東急の当駅始発の印 1・京王の渋谷着 2=チャレンジ枠の切替口に従う)。定数 5 つ。docstring |
| `src/shibuya/engine/processes/rail_events.py` | 新規(器) | 発着の表を読む口(`load_rail_events`・`READ_RAIL_EVENTS=False`=既定は読まない・どの過程からも呼ばない) |
| `tests/build_rail/test_w12_arrivals_2_3c.py`・`test_activate_tt23c.py`・`__init__.py` | 新規 | §12 |
| `tests/build_field/test_w12_real_timetables.py` | 1 行+注 | 版の検査 1.2.0 → 1.3.0 |
| `tests/engine/bridging/test_bridging_ledger.py` | 1 行+注 | 形ごとの数 expedients 143 → 144 |
| `docs/design/bridging-ledger.json` | 行の更新 4・追加 1 | §11 |
| `docs/bench/analysis/wallbounce-1012/tt23c/` | 新規 | 本書・道具 2 本(`tools/tokyu_origin_marks.py`・`tools/activate_tt23c.py`)・`origin_marks_check.json`(印の読み取りの要約)・`stage_build.json`(資産の組み立て 2 回)・`activation_plan.json`(差の表)・`head_vs_tt23c_19cfg.json`・`tt23c_vs_stage_19cfg.json`(byte-check) |

`data/` の下に足したもの(git の外・本体の data に junction で入る): `data/user_timetables/_extracted/東急_印.{read1,read2,final}.csv`・`_extracted/read2_raw/tokyu_origin_marks.txt`(目の読み)・`_extracted/read2_raw/tokyu_origin_marks_resolutions.json`(決着 1 件)・`data/world/v2_stage_2-3c/`(資産)。既存の道具と CSV は書き換えていない。

## 2. 材料の表

| 線 | 元の表 | 到着/発車 | 本数(平日/土休) | 出典の種類 | 2-3c での使い方 |
|---|---|---|---|---|---|
| 銀座線 | ODPT `odpt:TrainTimetable`(東京メトロ・静的データ版 1・dct:issued 2026-09-19) | 到着 | 362/307 | ODPT オープン枠 | 到着の行(終点) |
| 銀座線 | 同上 | 発車 | 360/305 | ODPT オープン枠 | 2-3b のまま(渋谷始発) |
| 半蔵門線 | 同上(dct:issued 2026-03-14) | 到着 | 282/209 | ODPT オープン枠 | 到着の行(直通 281/209・渋谷止まり 1/0) |
| 副都心線 | 同上(dct:issued 2026-03-14) | 到着 | 259/237 | ODPT オープン枠 | 到着の行(直通 258/236・渋谷止まり 1/1) |
| 半蔵門線・副都心線 | ODPT 駅の時刻表(7 月の取得)+上の列車時刻表 | 発車 | 289/209・259/238 | ODPT オープン枠 | 列車の id・行き先・種別・始発かどうか(列車番号で結んで全件一致) |
| 井の頭線 | `京王_井の頭線_渋谷_到着`(チャレンジ枠の列車時刻表から作った CSV) | 到着 | 305/261 | ODPT チャレンジ枠 | 到着の行(終点)・列車番号 |
| 井の頭線 | `京王_井の頭線_渋谷_吉祥寺方面`(チャレンジ枠) | 発車 | 305/261 | ODPT チャレンジ枠 | 2-3b のまま(渋谷始発) |
| 東横線 | 東急 TY01_2(下り)の読み取り+**当駅始発の印**(2-3c で読んだ) | 発車 | 348/321(うち始発 90/85) | ユーザー提供 | 下りの直通の結び |
| 東横線(上り) | 東急 TY01_1(副都心線の標準時刻表) | 発車 | 259/238 | ユーザー提供 | 上りのまとめ(副都心線の行と同じ列車) |
| 田園都市線 | 東急 DT01_2(下り)の読み取り+**当駅始発の印** | 発車 | 284/216(うち始発 3/7) | ユーザー提供 | 下りの直通の結び |
| 田園都市線(上り) | 東急 DT01_1(半蔵門線の標準時刻表) | 発車 | 289/209 | ユーザー提供 | 上りのまとめ(半蔵門線の行と同じ列車) |
| 埼京線 | JR 相鉄線直通・大崎方面 | 発車 | 46/46・85/69 | ユーザー提供 | 相手の線「相鉄線」・重なりの確かめ |
| 埼京線(畳んだ湘南新宿ライン) | JR 湘南新宿ライン 北行・南行 | 発車 | 96/91・95/93(臨時を除く前) | ユーザー提供 | 成田エクスプレスの確かめの相手 |
| (成田エクスプレス) | JR 成田エクスプレス 成田空港方面・新宿方面 | 発車 | 26/26・26/26 | ユーザー提供 | 湘南新宿ラインの表に含まれることの確かめだけ(行は足さない) |
| (照合だけ) | メトロ G02 表参道 渋谷ゆき・Z02 表参道 渋谷方面・F15 明治神宮前 渋谷方面 | (手前の駅の発車) | 362/307・282/209・259/235 | ユーザー提供 | 地下鉄の到着の列車の手前の駅の発車と時刻の多重集合で一致(試験) |
| (照合だけ) | ODPT チャレンジ枠 東急 渋谷の駅の時刻表(`isOrigin`)・JR の列車時刻表 | — | — | ODPT チャレンジ枠 | 当駅始発の印と 185/185 一致・JR は渋谷で終わる/始まる列車 0(記録だけ・資産に入れない) |

- 地下鉄の到着の手前の駅の照合: 銀座線 669/669・半蔵門線 491/491・副都心線 494/494(+明治神宮前に停まらない S-TRAIN 2 本=土休)。
- 東急の渋谷止まりが手前の駅の表に見える本数(各停だけ・時刻は作らない): 代官山 渋谷行き 57/63・池尻大橋 渋谷行き 3/5。

## 3. 当駅始発の印の読み取り(東急 TY01_2・DT01_2)

- **何を読んだか**: 分の上の青い塗りの丸。凡例(頁の右の「時刻表の見方」)は「● 当駅始発・⑤…5 番線発車」(東横線)・「● 当駅始発・②…2 番線発車」(田園都市線)。番線の数字が入った丸も当駅始発の印と読める。第330 の読み取りでは取っていなかった(extraction-tokyu-metro.md §7 の 3)。
- **読み 1(機械)**: `tools/tokyu_origin_marks.py read1`。第330 の道具 `tokyu_read1.py` の図形の取り出しと位置の関数を読むだけで呼び(道具は書き換えていない)、第330 で名前を付けた指紋の表(`#dot`=青い丸・`#w5`・`#w2`=丸の中の数字)で印と種類を決めた。新しく名前を付けた指紋は 0。
- **読み 2(目)**: 150 dpi の時の帯の画像(5 帯ずつ)を見て、分と印の種類を起こした(`read2_raw/tokyu_origin_marks.txt`)。読み 1 の分の値は見ていない(見たのは読み 1 の総数とチャレンジ枠との一致の総数だけ)。読み 2 の 1 回目は数字の入った丸(⑤②)を番線の印と見て外していた。凡例を読み直し、同じ画像の読みの記録から足した(独立性の申告)。
- **突き合わせ**: 185 行(読み 1)/184 行(読み 2)。食い違い **1 件**(東横線 平日 23 時台の ⑤ 1 個=読み 2 の見落とし)。300 dpi の画像で印を確かめ、読み 1 を採った(決着の表 `tokyu_origin_marks_resolutions.json`)。時ごとのマス 47 のうち合わないのは決着した 1 マスだけ。印の種類: ● 153・⑤ 28・② 4。比べる道具の自己試験(違い 3 か所を入れて全部出る)OK。2 回作って final はバイト一致(md5 `35806aea…`)。
- **照合(チャレンジ枠・資産に入れない)**: ODPT チャレンジ枠の東急 渋谷の駅の時刻表の `odpt:isOrigin` と、(暦, 分)で東横線 175/175・田園都市線 10/10 一致。印の分はどれも final の発車の表にある。
- 要約は [origin_marks_check.json](origin_marks_check.json)(本数と時ごとの数だけ)。

| 表 | 平日(読み1/読み2) | 土休(読み1/読み2) |
|---|---|---|
| 東急_東横線_渋谷_横浜方面 | 90/89(決着で 90) | 85/85 |
| 東急_田園都市線_渋谷_中央林間方面 | 3/3 | 7/7 |

## 4. 直通のまとめの規則と件数

規則は版の表 `w12_timetable_versions.json` の節 `rail_events.rules` と W12 の params に conf つきで書いた。

| 規則 | 線の組 | 中身(短く) | conf | 件数(平日/土休) | 疑わしい組 |
|---|---|---|---|---|---|
| `up_merge` | 東横線↔副都心線・田園都市線↔半蔵門線 | 東急の上りの表と地下鉄の駅の時刻表の渋谷発を、同じ暦・発車の分・行き先・種別(F ライナー=急行)で 1 対 1。数えるのは地下鉄の行 | mechanism | 259/238・289/209(計 995) | 結べない東急の行 0・相手の無い地下鉄の行 0 |
| `down_through` | 副都心線→東横線・半蔵門線→田園都市線 | 地下鉄の渋谷着(行き先が東急の先)と、東急の下りの渋谷発のうち当駅始発の印の無い便を、同じ暦・同じ行き先ごとに時刻の順に 1 対 1。発車−到着の上限 10 分 | **expedient** | 258/236・281/209(計 984) | 数が合わない組 0・上限の外 0・**入れ替わりうる隣どうしの組 25** |
| `nex_in_shonan` | 成田エクスプレス ⊂ 湘南新宿ライン | 同じ暦・時刻・行き先・種別で全部含まれる=読まない(二重に数えない) | mechanism | 104 本(計) | 外れ 0 |
| `sotetsu` | 埼京線↔相鉄線 | 相鉄線直通の表の便に相手の線「相鉄線」。大崎方面の表と同じ分の便は疑わしい組として数える(W12 に相鉄線の行は無い=二重に数える組はもともと無い) | mechanism | 46/46 | 重なり 0(まとめる組なし) |

- **残った疑わしい組**(ゲート `rail_events_suspicious_pairs`=0): 結べない上りの行・相手の無い地下鉄の行・下りの数の食い違い・上限の外・印の分が発車の行に無い・成田エクスプレスの外れ・相鉄線直通と大崎方面の重なり・地下鉄の発車と列車時刻表の結び損ね・始発の印の食い違い(駅の時刻表 vs 列車時刻表)・同じ分の 2 便で潰れた属性、の和。**0**。〔検収 M1〕成田エクスプレスと相鉄線直通の重なりは**表の生の行**で数える(発車の表は 2-3b で同じ分の 2 便を 1 行にしたので、発車の行で数えると作りの上で 0 しか出ない)。潰れた属性(同じ線・向き・暦・分の 2 便)と始発の印の食い違いは、それぞれ別のゲート `rail_events_attr_collapsed`・`rail_events_origin_flag_mismatch`(どちらも 0)にも出す。相鉄線直通の表の生の行 92・重なり 0。
- **入れ替わりうる組 25**: 下りの直通で、隣どうしの 2 組(同じ暦・同じ行き先)を入れ替えても発車−到着が 0〜10 分に収まる組の数。この 25 組は「追い越しなし」の推測が外れていても見分けられない。東急の列車番号つきの時刻表があれば決まる(手元に無い=空欄)。
- **渋谷での停車の分**(下りの直通の発車−到着): 0 分 6・1 分 676・2 分 186・3 分 73・4 分 26・5 分 9・6 分 5・7 分 3。
- **渋谷で種別が変わる便**(下りの直通・地下鉄の種別 → 東急の種別): 田園都市線は 490 組とも同じ種別(各停 313・急行 117・準急 60)。東横線は 494 組のうち同じ語の種別 199(各停 185・急行 12・S トレイン 2)・違う語 295(各停→急行 147・F ライナー→特急 48・急行→特急 22 など=golden の `down_through_type_pairs` は 2 線の和)。種別は突き合わせの鍵にしていない(東横線で変わるため)。
- **上りの地下鉄の発車の始発かどうか**: ODPT の列車時刻表の `originStation` と駅の時刻表の `isOrigin` が全部一致(食い違い 0)。副都心線の渋谷始発 2/2(TY01_1 の ● 4 個と同じ数)。半蔵門線の渋谷始発 0。
- **JR**: チャレンジ枠の列車時刻表で、渋谷で終わる/始まる列車は 0(照合だけ)。JR の発車の行は `call_kind=unknown` のまま(ユーザーの表に始発駅が無い)。

## 5. 1 日の本数(線ごと・平日/土休)

| 線 | 発車の行 | 1 本として数える発車 | 発車の内訳(始発/直通/不明) | 到着(終点/直通) |
|---|---|---|---|---|
| 銀座線 | 360/305 | 360/305 | 始発 360/305 | 362/307(終点) |
| 井の頭線 | 305/261 | 305/261 | 始発 305/261 | 305/261(終点) |
| 半蔵門線 | 289/209 | 289/209 | 直通 289/209 | 282/209(終点 1/0・直通 281/209) |
| 副都心線 | 259/238 | 259/238 | 始発 2/2・直通 257/236 | 259/237(終点 1/1・直通 258/236) |
| 東横線 | 607/559 | 348/321 | 始発 92/87・直通 515/472(上り 259/238 は副都心線の行で数える) | 空欄 |
| 田園都市線 | 573/425 | 284/216 | 始発 3/7・直通 570/418(上り 289/209 は半蔵門線の行で数える) | 空欄 |
| 山手線 | 513/507 | 513/507 | 不明 513/507 | 空欄 |
| 埼京線 | 453/410 | 453/410 | 不明 453/410(相鉄線へ 46/46) | 空欄 |
| 計 | 3,359/2,914 | **2,811/2,467** | | **1,208/1,014** |

- 東横線の始発 92/87 は、下りの当駅始発 90/85 と、上りの行のうち副都心線の渋谷始発と同じ列車 2/2。

## 6. 空欄の宣言(作り物の時刻を入れない)

| 何が | なぜ |
|---|---|
| JR(山手線・埼京線〈湘南新宿ライン・相鉄線直通を含む〉)の渋谷着の時刻と渋谷始発かどうか | 渋谷は途中駅。手持ちの表は発車だけで、着く時刻も始発駅も頁に無い。チャレンジ枠の照合では渋谷で終わる/始まる列車 0 |
| 東急から地下鉄へ直通する便(東横線→副都心線・田園都市線→半蔵門線)の渋谷着の時刻 | 地下鉄の列車時刻表は渋谷発から始まり、東急の列車時刻表は手元に無い |
| 東急の渋谷止まりの渋谷着の時刻 | 東急の到着の表は無い。手前の駅の表は各停だけ(代官山 渋谷行き 57/63・池尻大橋 3/5=急行は手前の駅に停まらない) |
| 相鉄線から来て北へ行く埼京線の便の相手の線 | 大宮方面の表の行き先からは見分けられない(チャレンジ枠の列車番号では 46/46=extraction-jr.md §6・資産に入れない) |
| 折り返しの結び付け(どの到着がどの渋谷始発になるか) | 銀座線・京王の列車時刻表・東急の表に次の列車への結び付けの欄が無い |

## 7. W12 1.3.0 の列と版

`w12_rail_events.parquet` の列(意味の表は `w12_rail_events.py` の docstring):

| 列 | 型 | 値 |
|---|---|---|
| `event` | 文字 | `departure`/`arrival`(到着/発車の種別) |
| `call_kind` | 文字 | `origin`(渋谷始発)・`terminal`(渋谷止まり)・`through`(直通)・`unknown`(表に無い) |
| `line`・`operator`・`direction`・`calendar` | 文字 | W12 の語彙。到着の向きは到着する列車の向き(地下鉄 `TokyoMetro.Shibuya`・京王 `上り`) |
| `time`・`time_min` | 文字・int32 | `HH:MM` と運行日の分(4 時の切れ目) |
| `source` | 文字 | 発車は発車の表と同じ・到着 `real_odpt_open_metro_2026-03`/`_2026-09`・`real_odpt_challenge_keio` |
| `train_id` | 文字 | 元の列車の id(地下鉄=ODPT `owl:sameAs`・京王=`keio:<列車番号>`・JR と東急の表=空) |
| `train_key` | 文字 | 1 本の列車の鍵(結んだ行どうしは同じ) |
| `train_type`・`destination` | 文字 | 種別と行き先(地下鉄は日本語に写す・写しの表に無い駅は止まる) |
| `through_partner_line` | 文字 | 直通の相手の線 |
| `departure_row` | int32 | 発車の表の行の番号(到着は -1) |
| `merged_into_row` | int32 | 同じ列車の代表の発車の行(東急の上り → 地下鉄の行・他は -1) |
| `counted` | bool | 1 本として数える行か |

W12 1.2.0(本体の v2)との差:

| 出力・ヘッダ | 1.2.0 | 1.3.0 |
|---|---|---|
| `w12_timetables.parquet` | `7ef7ab9038348e59` | **同じ** |
| `w12_external_nodes.parquet`・`w12_generation_weights.parquet` | `031fe09e…`・`eb85f8ac…` | 同じ |
| `w12_timetable_versions.json` | `4ee484eb75037467` | `e63bdbb8a9cb19dd`(節 `rail_events`=規則・本数・空欄。時刻と語 departure は無い) |
| `w12_rail_events.parquet` | 無い | `72fdac2a706a4b6d`(8,495 行) |
| ヘッダ | stage_version 1.2.0・input_hash `327ab8dc…`・param_hash `d859e56d…`・expedients 11・ゲート 21・出力 4 | 1.3.0・`c7d6d97d…`・`b39820a2…`・12・26・5 |

- 新しいゲート: `rail_events_departure_rows_match`(発車の行=時刻表の行)・`rail_events_arrival_rows`(到着がある)・`rail_events_suspicious_pairs`(0)・`rail_events_attr_collapsed`(0)・`rail_events_origin_flag_mismatch`(0)。全段のゲートの落ちは保った W10 の較正 1 件だけ(前から)。
- W19 の凍結の表 `data_assets` 91 → **98**(足したのは 2-3c の入力 7 本=成田エクスプレスの表 4・東急の当駅始発の印 1・京王の渋谷着 2)。W19 の版は変えていない。
- 京王の切替口 `USE_ODPT_CHALLENGE=False` では、京王の渋谷着を読まず(入力からも外れる)、等間隔の推定の井の頭線の行は `call_kind=unknown`(試験 `test_w12_keio_switch_2_4.py` が通る)。

## 8. 資産(`data/world/v2_stage_2-3c/`・活性化しない)

- 本体の v2 の直下のファイル 107 本(W17 のプロンプトと応答の jsonl を除く)と `acceptance/` を本物のコピーで写し、W12・W18・W19・W20 を作業木の src で組んだ(ほかの 17 段は `--keep-stage`)。**2 回組んで build_hash `5a3e8a8981e5c9e3…` が一致**(`stage_build.json`=検収の後の直しの後の組み直し=§16。作業用の置き場に本体の v2 から新しく写して組んでも同じ build_hash。前の組み立て `315e9293…`・`6f2de0e0…` もそれぞれ 2 回一致した)。
- 差の表(`activation_plan.json`=sha256・md5・バイト数): 同じ 98・置き換え 9・追加 1。build_hash `6a7d34e858e07210…` → **`5a3e8a8981e5c9e32a53ad55c4f91a2b2c2da69626f5e6c8ca507e05a435491b`**。

| ファイル | 扱い | sha256(前・先頭 16) | sha256(後・先頭 16) |
|---|---|---|---|
| `W12.header.json` | 置き換え | `a3f7ef67f2edc693` | `cb895f409dddfc1b` |
| `W18.header.json` | 置き換え | `50a943e4cd94a8e3` | `c013dcaca49b71ec` |
| `W19.header.json` | 置き換え | `5c8c2565ccaf339a` | `a1c2d6787f071876` |
| `W20.header.json` | 置き換え | `d540f3bfb7e452e9` | `65c74db75835e4bf` |
| `acceptance/gate_table.md` | 置き換え | `0f755af3d91b0d09` | `52a184e1c0a49c01` |
| `acceptance/summary.json` | 置き換え | `c9c809e511752b38` | `1b1aebc84843b24d` |
| `build_manifest.json` | 置き換え | `bc156909de308695` | `ccf947dff05a8f2d` |
| `w12_rail_events.parquet` | 追加 | — | `72fdac2a706a4b6d` |
| `w12_timetable_versions.json` | 置き換え | `4ee484eb75037467` | `e63bdbb8a9cb19dd` |
| `w19_freeze.json` | 置き換え | `f1e45e9822f469c5` | `31b6c6ea633b138d` |

- 活性化の道具 `tools/activate_tt23c.py`(`stage`・`plan`・`apply --dry-run`・`verify`・`materialize`・`revert`)。vb24 の道具と違い、差し替えのファイルを別の置き場に写さず、組んだ資産から直に写す(写す前に sha256 を plan と照らす)。本段では `apply` していない。本体の v2 に `apply --dry-run` を当てて前提 OK・`verify --want before` 同じ(何も書いていない)。道の全体(plan → apply → verify → materialize → revert)は合成の置き場の試験で確かめた。
- 版上げ 3 回目(4-3)で親が回す手順(リポの根・作業木の src を `PYTHONPATH` に):

  ```
  T=docs/bench/analysis/wallbounce-1012/tt23c/tools/activate_tt23c.py
  python $T apply --dry-run      # 前提の確かめ(本体の v2 が plan の前・組んだ資産が plan の後・退避先が空)
  python $T apply                # 置き換える 9 本を data/world/v2_pre_2-3c/ へ退避 → 10 本を写す → 確かめる
  python $T verify --want after
  python $T revert               # 戻す
  ```

  4-3 で他の段の資産と束ねるときは、そのときの本体の v2 から `stage` → `plan` をやり直す(plan の「前」が今の v2 なので)。

## 9. byte-check(19 構成・5,000 体・seed 1・1 日)

- **既定(HEAD と同じか)**: 前=HEAD `d35a9b6` の写し(`git archive` の src・docs・tools・錨はエンジンが開く 3 本だけ・`data` は本体の data へのつなぎ)・後=作業木の src(`src_is_worktree` True)。資産はどちらも本体の `data/world/v2`(W12 1.2.0)。**19/19 構成で比べる 25 欄とも同じ**([head_vs_tt23c_19cfg.json](head_vs_tt23c_19cfg.json))。呼数の合計 1,118,547(両側同じ)。例: w6_v3_default `b8eadcb51e8705e7`/64,528・v3_mem_rel `768b2262e3b0999e`/67,794・v3_classical `ca25874a5e4acb79`/93,017。
- **活性化しても動かないか(情報)**: 作業木の src で、資産だけ本体の v2 → `data/world/v2_stage_2-3c`(W12 1.3.0・build_hash `6f2de0e0…`=検収の前の組み立て)。**19/19 構成で 25 欄とも同じ**(`frozen_sources` も同じ=エンジンが読む W12 の 2 本はバイト一致)=[tt23c_vs_stage_19cfg.json](tt23c_vs_stage_19cfg.json)。検収の後に組み直した `5a3e8a89…` は、エンジンが読む W12 の 2 本(`w12_timetables.parquet` `7ef7ab90…`・`w12_external_nodes.parquet` `031fe09e…`)と発着の表が前と同じで、2 構成(w6_v3_default・v3_classical)を回し直して final と呼数が同じ(`b8eadcb5…`/64,528・`ca25874a…`/93,017)。
- **申告(道具の使い方)**: 10e の手順どおりの HEAD の写し(src と錨 3 本と予算の md だけ)では 19/19 とも final が違った。原因は写しの側に `data` が無いこと(経済の段階 2 がリポの根から OSM の店の札と営業時間を読む=`engine/economy_stage2.py` の `resolve_repo_path`・本人の所持金が変わる)。作業木の src を同じ写しの木に置くと写しの側と同じ final になり(300 体で確かめた)、差は src ではなく木の中身から来ると分かった。そこで写しの木に本体の data へのつなぎ(junction)を一時だけ置いて回し直し、回し終えて外した(本体の data は読むだけ)。10e の byte_check の docstring の手順は今の src には足りない(親へ=§15)。
- 作業木の側を最初に回したときは `PYTHONPATH` を付け忘れ、本体の src で回していた(`src_is_worktree` False)。止めて回し直した。上の数はすべて回し直した後のもの。

## 10. エンジン側(読む口の器)

- `src/shibuya/engine/processes/rail_events.py`: `RAIL_EVENTS_FILE`(構築側と同じ名=試験)・`READ_RAIL_EVENTS=False`・`load_rail_events(world_dir, enabled=None)`(既定は読まずに `None`・表が無い資産も `None`・知らない値は止まる)・`RailEventsAsset`(SoA)。**どの過程からも呼んでいない**=状態も状態台帳も増えない。エンジンが到着の行を使う(着く体を到着の便から降ろす・終点の折返し時分・直通の列車を 1 本の定員で数える)かは 4-3 で決める(§11)。
- `engine/processes/rail.py` は変えていない。

## 11. つなぎの台帳

| 行 | 前の外す段 | 後 | 理由(短く) |
|---|---|---|---|
| `EX-build.field.w12_external_nodes-ea8dc0c1`(2-3b は渋谷の発車の表だけ) | 2-3c | **4-3**(inferred) | 到着の行は W12 1.3.0 の別の表に入ったが、エンジンが読む発車の表は 1.2.0 とバイト一致で、エンジンは既定で到着の行を読まない=着く体は発車の便から降りるまま |
| `EX-build.field.w12_external_nodes-7b7c8bd2`(東急の上り=直通と同じ列車・線ごとに 2 回) | 2-3c | **4-3**(inferred) | 発着の表で列車の鍵で結び数える行を 1 つにした。エンジンの発車の表は線ごとに 2 行のまま(E2) |
| `BR-W11-SHINSEN-EXIT` | 2-3c | **5-0**(plan) | 井の頭線の渋谷着は列車時刻表から作り、神泉の発車は使わない=到着の元の役は外れた。残るのは W11 が神泉の出口 3 か所を渋谷に割り当てること=空間の段 0(timetables/README.md §6 の親の注) |
| `HD-engine.processes.rail-1af925f4`(rail.py の expedient の見出し・項 6) | 2-3c | **7**(inferred) | 〔検収 L6・親の判断〕項ごとの行 `DOC-tt23c-rail-*` 6 行に分けた(下の表)。見出しの行はコードの宣言と 1 対 1 のために残し、外す段は項の最後の段 |
| 新 `EX-build.field.w12_external_nodes-b2c96d6a`(下りの直通の結び) | — | **7**(inferred・expedient) | 当駅始発の印で結ぶ便の集まりは決まるが、同じ行き先の便の組み方は追い越しなしの推測(入れ替わりうる組 25) |

- 〔検収 L6〕見出しの行から分けた項ごとの行(文書の宣言の行・`declared_in`=本書 §11・`code_at`=`engine/processes/rail.py`・
  conf expedient・inferred):

  | 行 | 項 | 外す段 | 理由(短く) |
  |---|---|---|---|
  | `DOC-tt23c-rail-dwell` | 1 停車時分の線別表(終端=折返し・通過型) | 4-3 | 停車と折返しの項。終点と直通の到着の時刻は発着の表に入った=エンジンが読むかを決める段 |
  | `DOC-tt23c-rail-arrival-assign` | 5 到着便の割り当て | 4-3 | 到着の行は発着の表に入った=同じ段で決める |
  | `DOC-tt23c-rail-fare` | 2 運賃(運賃表が空欄・IC/切符の別なし) | 7 | 運賃表を取る段が計画に無い(IC と現金の別は 2-1 で入った=項の文の後半は古い) |
  | `DOC-tt23c-rail-capacity` | 3 定員の空欄の推定 | 7 | 線別の輸送力を足す段が計画に無い |
  | `DOC-tt23c-rail-external-home` | 4 域外に住む割合 | 4-3 | 帰無腕だけで使う。外の住人は人口の作り直し(4-1 の段 7)で作り版上げ 3 回目で入れ替える(推測) |
  | `DOC-tt23c-rail-congestion` | 6 混雑率は中の乗客だけ | 7 | 域外区間の既存乗客を入れる段が計画に無い(「第2陣」を段の番号に読み替えられない) |

  「停車と折返しの 2 項」は項 1(停車時分=通過型と終端の折返し)と項 5(到着便の割り当て)と読んだ(残り 4 項=項 2・3・4・6)。
- 行の数 348 → 355(active 337 → 344=新しい宣言 1・項ごとの行 6)。走査器の数 expedients 143 → 144(試験の数を直した)。`what` の文は変えていない(C8 の感度の台帳の W12#4・#11 の文と合うまま=活性化した資産の build_manifest と同じ文)。

## 12. 試験

- **新しい試験**(`tests/build_rail/`・12 件・data 不要 8+data が要る 4):
  - `test_w12_arrivals_2_3c.py`(10): 合成の表 → 到着の行・直通のまとめ=1 本(上りの 2 行が 1 本・下りの直通の結び・当駅始発の印・成田エクスプレス ⊂ 湘南新宿ライン・相鉄線直通・渋谷を発着しない列車は知らない駅でも読まない)/まとめない組の負の対照 3 つ(上りの行き先の違い=疑わしい組 2・印が無い=1・上限の外=1)/知らない駅と種別は止まる/版と列の名・規則の conf と宣言の表(expedient の規則 1=`RAIL_EVENT_EXPEDIENTS` 1 行)・エンジンの読む口と同じ名/入力の層と京王の切替口/エンジンの読む口(既定は `None`・`enabled=True` で読む・知らない値は止まる)/〔data〕W12 を一時の置き場で組み、時刻表が本体の v2 とバイト一致・発着の表の本数が golden と一致・ゲート全部 PASS・版の表に時刻も語 departure も無い/〔data〕読み取りの検査(成田エクスプレスの 4 表と手前の駅の 6 表=読み 1 と読み 2 が時・分・種別・行き先で一致・時ごとの本数が一致/当駅始発の印=食い違いは決着した 1 件だけ・final=読み 1)/〔data〕地下鉄の到着の手前の駅の発車=ユーザーの表の読み取り(3 線・S-TRAIN 2 本を除く)/〔data〕当駅始発の印=チャレンジ枠の `isOrigin`(185/185)。
  - `test_activate_tt23c.py`(2): 合成の置き場で plan → apply --dry-run(何も書かない)→ apply → verify → materialize(前の資産を組む)→ revert が sha256 と build_hash で閉じる・本体が「前」でない/組んだ資産が plan と違えば止まる。
- **範囲の試験**(作業木・最後のコード・`-n 6 --dist loadfile`): `tests/build_rail tests/build_field tests/build_audit tests/build_vis tests/engine/bridging tests/engine/time tests/engine/processes tests/c8 tests/tools` と `tests/engine/test_state_ledger_10b.py`・`test_state_checks_10f.py`・`test_env_and_sections_10f.py`・`test_salt_seed_split_10f.py`・`test_activation_2_4.py`・`test_assets_10e_b0_b1.py`・`tests/test_build_run_keep_stage.py`・`tests/test_world_catalog_sha.py` = **895 passed・1 xfailed(8 分 5 秒)**。全段の構築を回す試験(field・audit・vis の pipeline)を含む。`tests/c7` は回していない。
- **data の無い写し**(src・tests・tools・docs〈錨はエンジンが開く 3 本だけ〉・pyproject)で CI-1 と同じ印(`-m "not slow and not gpu"`): `tests/build_rail`・W12 の試験 3 本・`tests/engine/bridging`・`tests/engine/time` = **125 passed・10 skipped**(data の id で飛ぶ: `user_timetables` 4・`odpt_static` 2・ほか)。
- `lint-imports`: 5 kept・0 broken。秘密の検査(`tools/scan_secrets.py`・変えた/足した 18 本=本書と byte-check の JSON を含む): CLEAN。
- 当駅始発の印の道具: `check` rc 0(決着 1 件)・`selftest` OK・2 回作って final がバイト一致。
- **〔検収の後の直し(§16)の後〕** `tests/build_rail` は 18 件(data 不要 14・data が要る 4)=M1 の負の対照 1・L1/L2 の負の対照 4・L3 の 2 本を足した。依頼の範囲 `tests/build_rail tests/build_field tests/engine/bridging tests/engine/processes tests/tools`(`-n 6 --dist loadfile`)= **462 passed・1 xfailed(5 分 14 秒)**。data の無い写し(CI-1 と同じ印): 131 passed・10 skipped。lint-imports 5 kept・0 broken。秘密の検査 CLEAN。

## 13. 触った共有ファイル(親が rebase するときの一覧)

| ファイル | 触った所 |
|---|---|
| `docs/design/bridging-ledger.json` | 4 行の `remove_at`・`why`(`BR-W11-SHINSEN-EXIT` の `remove_basis` は前から plan=変えていない)・新しい行 1 つ(`EX-…-7b7c8bd2` の直後に挿した)・項ごとの行 6 つ(`HD-engine.processes.rail-1af925f4` の直後に挿した) |
| `docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py` | 〔検収 L4〕docstring の手順(写す追跡ファイルと data のつなぎ)・`HEAD_TREE_FILES`・`head_tree_missing`・side の前の確かめ(足りなければ止まる・`--allow-incomplete-tree`)・side の JSON の `tree_missing`。比べる欄(`COMPARE_KEYS`)は変えていない |
| `tests/engine/bridging/test_bridging_ledger.py` | `test_the_counts_by_form` の expedients 143 → 144 と注 2 行 |
| `src/shibuya/build/field/w12_real_timetables.py`・`w12_external_nodes.py` | W12 の段の中だけ(2-3b の続き) |
| `tests/build_field/test_w12_real_timetables.py` | 版の検査 1 行 |

状態台帳・凍結の表(テストの golden)・manifest の欄・CLI の引数・`PLAN_STAGES` は触っていない。

## 14. 限界と仮採用(10-13b §0-3)

1. **下りの直通の組み方は推測**(仮採用・expedient・台帳の新しい行): 同じ暦・同じ行き先の便は渋谷で追い越さないと見て時刻の順に結んだ。結ぶ便の集まり(当駅始発でない便)は印で決まり、外の物差し(チャレンジ枠の `isOrigin`)と一致した。組み方そのものを確かめる物差しは無い(入れ替わりうる組 25)。
2. **当駅始発の印**: ⑤②(番線の数字の入った丸)も当駅始発と読んだのは凡例の図の読み(「当駅始発」の引き出し線の下に「⑤…5 番線発車」)による。チャレンジ枠の `isOrigin` と分まで一致したので、読みとしては裏が取れている。
3. **発車の表は線ごとの行を残した**(仮採用): まとめは列(列車の鍵・数える印・代表の行)で表し、行は消していない。消すとエンジンの方面ノード(線で便を引く=E2)と線別の定員の表が変わるため。行を消す形は 4-3 でエンジンと一緒に決める。
4. **到着の行の向きの語**: 地下鉄は ODPT の `TokyoMetro.Shibuya`、京王は `上り`(渋谷 → 吉祥寺が下りの裏)。エンジンの向きの番号(`didx`)は発車の表だけから作るので影響しない。
5. **行き先と種別の写しの表**は手で書いた(41 駅・6 種別)。写しの表に無い駅が渋谷を発着する列車に出たら止まる(黙って通さない)。
6. **銀座線の到着は 9 月改正の版**(発車と同じ=世界の時点より後・回答 10-13b §2)。半蔵門線・副都心線の到着は 2026-03-14 の版(発車の駅の時刻表と同じ版=列車番号で全件結べた)。
7. **京王の到着はチャレンジ枠**(仮-15 と同じ扱い・切替口 `USE_ODPT_CHALLENGE` に従う)。生の行は記録・版の表・試験の golden に写していない(本数だけ)。
8. 読み 2 は人ではなく同じ実行役(Claude)の目。1 回目に ⑤② を外していた(凡例を読み直して足した)ことを申告する。
9. 比較の先例: 1 行=1 つの出来事で到着/発車の時刻を持つ形は GTFS の `stop_times`、直通を列車の鍵で結ぶ形は GTFS の `block_id`/乗り換えの表の「座ったまま乗り継ぐ」種別・ODPT の `odpt:nextTrainTimetable` に近い(**記憶による・未確認=ネットワーク不可**)。

## 15. 親に確かめてほしいこと

1. **4 行の外す段**(§11): `ea8dc0c1`・`7b7c8bd2` を 4-3(エンジンが到着の行と列車の鍵を読むかを決める段)にした。`HD-…rail` は項ごとの行 6 つに分けた(〔検収 L6〕停車と折返し・到着便の割り当て=4-3、運賃・定員・混雑率=7、域外居住=4-3)。4-3 は「母集団が動く」段で、鉄道のエンジンの変更を束ねるかは親の判断。`BR-W11-SHINSEN-EXIT` は 5-0(空間の段 0)。
2. **新しい読み取り**(当駅始発の印)を `data/user_timetables/_extracted/` に足した(東急_印.*・read2_raw の 2 本)。発注の「`_extracted/` の読み取り済みの表を先に使う」に対し、時刻と行き先だけでは下りの直通の結びがチャレンジ枠の `isOrigin` と 145/175 しか合わなかった(東横線・最小の待ちで結ぶ形)ので、ユーザーの PDF の印を読んだ。
3. **チャレンジ枠の照合**: 東急の駅の時刻表の `isOrigin` と JR の列車時刻表を、試験と記録の照合だけに読んだ(構築の入力にしていない・資産に入れていない)。
4. **発車の表の行を消さない形**(§14 の 3)でよいか。
5. **活性化の道具**は差し替えのファイルを別の置き場に写さない形にした(§8)。
6. **ライセンス台帳に足す行の案**(親が書く):
   - ODPT オープン枠の静的データ版 1(東京メトロの列車時刻表・2026-10-13 のフォルダ): 2-3b の行(銀座線の発車)に、**到着**(銀座線 669・半蔵門線 491・副都心線 496 本)と、半蔵門線・副都心線の発車の列車の id・行き先・種別・始発駅の属性を足す。出典の表示は同じ。
   - ODPT チャレンジ枠(京王 井の頭線): 2-3b の行(渋谷発 566 本)に、渋谷着 566 本(列車番号つき)を足す。利用の範囲・再配布しないことは同じ。
   - ODPT チャレンジ枠(東急 渋谷の駅の時刻表・JR の列車時刻表): 照合だけに使った(当駅始発の印の確かめ・JR の渋谷発着の列車の有無)。資産に入れない。
   - ユーザー提供の時刻表の読み取り(東急・JR): 東急の TY01_2・DT01_2 から当駅始発の印 185 個を新しく読み取った(事実だけ・図は公開しない・CSV は git に入れない)。成田エクスプレスの表(JR 104 本)は確かめにだけ使い、行は足していない。
7. **byte-check の HEAD の側の作り方**(§9 の申告・〔検収 L4〕で直した): HEAD の写しの木に要るのは、src・錨 3 本・**`docs/design/rules-table.json`**(無いと規則の表が空)・`docs/design/bridging-ledger.json`・予算の md・`docs/design/v2-perception-contract.md`・`docs/design/v2-pattern-ledger.md`(src を `RELPATH`・`parents[3]`・`parents[4]`・`resolve_repo_path` で grep して決めた)と、**`data` へのつなぎ**(祝日の CSV・経済の段階 2 の OSM の店の札と営業時間)。`10e/byte_check_10e.py` の docstring の手順をこの形に直し、side に前の確かめ(`--src` の木に足りないものがあれば止まる)を足した(10e の手順どおりの写し=足りない 6 本を挙げて止まることを確かめた)。
8. 作業用の置き場 `_bc/`(作業木の根・未追跡・テープ・HEAD の写し・data の無い写し)は取り込みに載せないこと。

## 再現(リポの根・作業木の src を `PYTHONPATH` に)

```
# 当駅始発の印(システムの python=PyMuPDF)
python docs/bench/analysis/wallbounce-1012/tt23c/tools/tokyu_origin_marks.py read1
python docs/bench/analysis/wallbounce-1012/tt23c/tools/tokyu_origin_marks.py read2
python docs/bench/analysis/wallbounce-1012/tt23c/tools/tokyu_origin_marks.py check --record docs/bench/analysis/wallbounce-1012/tt23c/origin_marks_check.json
python docs/bench/analysis/wallbounce-1012/tt23c/tools/tokyu_origin_marks.py selftest
# 資産(2 回組む)と差の表
python docs/bench/analysis/wallbounce-1012/tt23c/tools/activate_tt23c.py stage --record <作業用>/stage.json
python docs/bench/analysis/wallbounce-1012/tt23c/tools/activate_tt23c.py plan
python docs/bench/analysis/wallbounce-1012/tt23c/tools/activate_tt23c.py apply --dry-run
```

## 16. 検収の後の直し(独立の検収=条件つき受入・中 1・低 6)

| # | 重さ | 指摘 | 直し |
|---|---|---|---|
| M1 | 中 | 相鉄線直通と大崎方面の重なりの検査が、2-3b で重複を除いた後の発車の行(同じ線・向き・暦・分で 1 行・属性は先に読んだ表の 1 便だけ)で数えるので作りの上で 0 しか返さない | 重なりと成田エクスプレスの確かめを**表の生の行**で数える・同じ分の 2 便で潰れた属性の数を要約 `attr_collapsed` とゲート `rail_events_attr_collapsed` と疑わしい組の和に足した。負の対照: 合成の生の表で相鉄線直通の便を大崎方面の便と同じ分に植えると、発車の行は 6 行(1 行に潰れる)のまま、重なり 1・潰れた属性 1・疑わしい組 2(試験 `test_same_minute_two_trains_are_counted_on_the_raw_rows`)。実データは重なり 0・潰れた属性 0(相鉄線直通の生の行 92) |
| L1 | 低 | ゲートの残りの成分に負の対照が無い | 成田エクスプレスの外れ・列車時刻表との結び損ね・印の分が発車の行に無い・始発の印の食い違いの 4 つを 1 本ずつ(`test_each_gate_component_has_a_negative_control`=どれも 1 と出て他の成分は 0) |
| L2 | 低 | 始発の印の食い違い(駅の時刻表 vs 列車時刻表)がゲートに無い | ゲート `rail_events_origin_flag_mismatch`(0)と疑わしい組の和に足した。資産の値は 0 のまま |
| L3 | 低 | 読む口の器の配列が書ける・呼ばれていないことの番人が無い | 配列を `setflags(write=False)`(書くと `ValueError`=試験)。src を AST で走査して `rail_events` の import と `load_rail_events`・`READ_RAIL_EVENTS`・`RailEventsAsset` の名が器の外に無いことと `READ_RAIL_EVENTS=False` を確かめる試験 |
| L4 | 低 | HEAD の写しに要るもの(rules-table.json ほか)が記録と 10e の道具の docstring に無い | §9・§15 の 7 と `10e/byte_check_10e.py`(docstring・前の確かめ)を直した(§13) |
| L5 | 低 | §13 の「remove_basis を変えた」は誤り・第330 の道具の置き場に pyc が残った | §13 を直した(plan のまま)。`data/user_timetables/_extracted/tools/__pycache__/tokyu_read1.cpython-312.pyc`(本段の道具の import でできた)を消し、道具に `sys.dont_write_bytecode` を付けて読み 1 を回し直しても作られないこと・読み 1 の CSV がバイト一致することを確かめた |
| L6 | 低(親の判断) | 台帳の `HD-engine.processes.rail-1af925f4`(6 項を 1 行) | 項ごとの行 6 つに分けた(§11) |

- **build_hash は変わった**: `6f2de0e0…` → `5a3e8a8981e5c9e3…`。理由=W12 のヘッダ(ゲート 24 → 26・notes の `rail_events` に `attr_collapsed` と相鉄線直通の生の行の数)と版の表 `w12_timetable_versions.json`(同じ欄)が変わり、それを写す W18〜W20 のヘッダ・受入パック・`w19_freeze.json`・`build_manifest.json` が動いた。**本数と疑わしい組の数は変わらない**(golden は同じ)。発着の表 `w12_rail_events.parquet`(`72fdac2a…`)とエンジンが読む W12 の 2 本は同じ。params は変えていない(param_hash `b39820a2…` のまま)。
- 直しの後の試験は §12 の後の行。

<!-- golden-begin -->
```json
{
 "arrival_versions": {
  "井の頭線": {
   "real_odpt_challenge_keio": 566
  },
  "副都心線": {
   "2026-03-14": 496
  },
  "半蔵門線": {
   "2026-03-14": 491
  },
  "銀座線": {
   "2026-09-19": 669
  }
 },
 "arrivals_by_source": {
  "real_odpt_challenge_keio": 566,
  "real_odpt_open_metro_2026-03": 987,
  "real_odpt_open_metro_2026-09": 669
 },
 "by_line_calendar": {
  "井の頭線": {
   "SaturdayHoliday": {
    "到着": 261,
    "到着_terminal": 261,
    "発車": 261,
    "発車(数える)": 261,
    "発車_origin": 261
   },
   "Weekday": {
    "到着": 305,
    "到着_terminal": 305,
    "発車": 305,
    "発車(数える)": 305,
    "発車_origin": 305
   }
  },
  "副都心線": {
   "SaturdayHoliday": {
    "到着": 237,
    "到着_terminal": 1,
    "到着_through": 236,
    "発車": 238,
    "発車(数える)": 238,
    "発車_origin": 2,
    "発車_through": 236
   },
   "Weekday": {
    "到着": 259,
    "到着_terminal": 1,
    "到着_through": 258,
    "発車": 259,
    "発車(数える)": 259,
    "発車_origin": 2,
    "発車_through": 257
   }
  },
  "半蔵門線": {
   "SaturdayHoliday": {
    "到着": 209,
    "到着_through": 209,
    "発車": 209,
    "発車(数える)": 209,
    "発車_through": 209
   },
   "Weekday": {
    "到着": 282,
    "到着_terminal": 1,
    "到着_through": 281,
    "発車": 289,
    "発車(数える)": 289,
    "発車_through": 289
   }
  },
  "埼京線": {
   "SaturdayHoliday": {
    "発車": 410,
    "発車(数える)": 410,
    "発車_unknown": 410
   },
   "Weekday": {
    "発車": 453,
    "発車(数える)": 453,
    "発車_unknown": 453
   }
  },
  "山手線": {
   "SaturdayHoliday": {
    "発車": 507,
    "発車(数える)": 507,
    "発車_unknown": 507
   },
   "Weekday": {
    "発車": 513,
    "発車(数える)": 513,
    "発車_unknown": 513
   }
  },
  "東横線": {
   "SaturdayHoliday": {
    "発車": 559,
    "発車(数える)": 321,
    "発車_origin": 87,
    "発車_through": 472
   },
   "Weekday": {
    "発車": 607,
    "発車(数える)": 348,
    "発車_origin": 92,
    "発車_through": 515
   }
  },
  "田園都市線": {
   "SaturdayHoliday": {
    "発車": 425,
    "発車(数える)": 216,
    "発車_origin": 7,
    "発車_through": 418
   },
   "Weekday": {
    "発車": 573,
    "発車(数える)": 284,
    "発車_origin": 3,
    "発車_through": 570
   }
  },
  "銀座線": {
   "SaturdayHoliday": {
    "到着": 307,
    "到着_terminal": 307,
    "発車": 305,
    "発車(数える)": 305,
    "発車_origin": 305
   },
   "Weekday": {
    "到着": 362,
    "到着_terminal": 362,
    "発車": 360,
    "発車(数える)": 360,
    "発車_origin": 360
   }
  }
 },
 "down_through_dwell_min_hist": {
  "0": 6,
  "1": 676,
  "2": 186,
  "3": 73,
  "4": 26,
  "5": 9,
  "6": 5,
  "7": 3
 },
 "down_through_paired": {
  "副都心線→東横線|SaturdayHoliday": 236,
  "副都心線→東横線|Weekday": 258,
  "半蔵門線→田園都市線|SaturdayHoliday": 209,
  "半蔵門線→田園都市線|Weekday": 281
 },
 "down_through_type_pairs": {
  "Fライナー→各停": 7,
  "Fライナー→急行": 1,
  "Fライナー→特急": 48,
  "Sトレイン→Sトレイン": 2,
  "各停→各停": 498,
  "各停→急行": 147,
  "各停→特急": 18,
  "各停→通勤特急": 9,
  "急行→各停": 9,
  "急行→急行": 129,
  "急行→特急": 22,
  "急行→通勤特急": 8,
  "準急→準急": 60,
  "通勤急行→各停": 7,
  "通勤急行→急行": 3,
  "通勤急行→特急": 2,
  "通勤急行→通勤特急": 14
 },
 "nex_in_shonan_merged": 104,
 "origin_marks": 185,
 "rows_by_event": {
  "到着": 2222,
  "発車": 6273
 },
 "rows_total": 8495,
 "sotetsu_rows_with_partner": 92,
 "swappable_adjacent_pairs": 25,
 "timetables_sha256_16": "7ef7ab9038348e59",
 "up_merge_merged": {
  "東横線|SaturdayHoliday": 238,
  "東横線|Weekday": 259,
  "田園都市線|SaturdayHoliday": 209,
  "田園都市線|Weekday": 289
 }
}
```
<!-- golden-end -->
