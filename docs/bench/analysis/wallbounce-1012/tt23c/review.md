# 2-3c 検収の記録(独立の検収役)

> 検収役(Opus 5.5)。実装は見ていない。作業木 `2-3c/rail-arrivals`(未 commit・土台 `d35a9b6`)と本体の HEAD `d518a3d` を読むだけで確かめた。書いたのは本書だけ(作業用の置き場 `_bc_review/` は終わりに消した)。commit・子サブ・taskkill は使っていない。`tests/c7` は回していない。
> 時刻は書かない(本数・版・sha だけ)。ODPT チャレンジ枠の生データは数えるだけにした。

## 判定: 条件つき受入

既定の結果は動かない(実装役の 19 構成+自分の 4 構成)。資産を自分で 1 回組み、build_hash と 108 本の sha256 が実装役の記録と全部一致した。材料の本数・直通のまとめ・1 本として数える発車も、実装のモジュールを使わない別の道で数え直して全部一致した。高の欠陥は無い。中 1 件(相鉄線直通と大崎方面の重なりの検査が作りの上で 0 にしかならない)と、低 6 件(試験の負の対照の抜け・読む口の配列が書き換えられる・記録の小さな食い違い)を直せば受入。数と資産は直しで動かない見込み(実データの重なりは生の表で 0)。

## 1. 結果不変 ✓

- **実装役の JSON**: `head_vs_tt23c_19cfg.json`=19/19 構成で比べる 25 欄とも同じ・error 0・両側とも `kw {}`・`env {}`(切替口なし=腕は今の既定の道)。`tt23c_vs_stage_19cfg.json`(作業木の src で資産だけ 2-3c の資産に替えた情報の側)も 19/19 で 25 欄とも同じ(`frozen_sources` も同じ)。
- **自分の 4 構成**(5,000 体・seed 1・1 日・両側とも本体の `data/world/v2`): 前=本体 HEAD `d518a3d` を `git archive`(src・pyproject・`docs/design`・錨はエンジンが開く 3 本・w6-regen)で写し、写しの根に本体の data への junction を一時だけ置いた(回し終えて `rmdir` で外した・置き場に reparse point が残っていないことを確かめた)。後=作業木の src(`PYTHONPATH`・`src_is_worktree` True)。

| 構成 | final(前=後) | 呼数 | 25 欄 |
|---|---|---|---|
| w6_v3_default | `b8eadcb51e8705e7` | 64,528 | 同じ |
| w6_v3_activity_off | `c88ba9104f45f897` | 50,006 | 同じ |
| w6_v1_default | `e1288e092ddaca86` | 51,655 | 同じ |
| v3_mem_rel | `768b2262e3b0999e` | 67,794 | 同じ |

  final は実装役の 19 構成の表の値とも同じ。前は `d518a3d`(土台より 2 commit 後=経済の DataAbsentWarning の直しを含む)なので、rebase 後の HEAD とも結果が同じと分かる。
- **申告(発注文の手順の穴)**: 最初は 10e の docstring の写し(src・錨 3 本・予算の md・w6-regen)+data の junction で回した。4/4 構成で `final`・`behavior_last`・`full_last`・`end_of_day` が違った(呼数・blocks・行動の件数は同じ)。原因は写しに `docs/design/rules-table.json` が無いこと(`engine/rules/table.py` がリポの根から読む)。この 1 本だけを足した写しで w6_v1_default を回すと、作業木と同じ final `e1288e09…` になった。**HEAD の写しには data と `docs/design/rules-table.json` の両方が要る**(実装役の §9・§15-7 は data だけを挙げている。実装役自身は docs を丸ごと写したので、実装役の 19/19 は正しい)。

## 2. 口と約束 ✓(試験の抜けは欠陥 M1・L1・L2・L3)

- **構築の口**: `w12_rail_events.build_rail_events(data_root, departures, metro_station_docs) -> RailEvents(columns, summary)`・出力 `w12_rail_events.parquet`・列 17。発注の列(到着/発車の種別=`event`・到着の時刻=`time`/`time_min`・元の列車の id=`train_id`・直通の相手の線=`through_partner_line`)は全部ある。足した列(`call_kind`・`train_key`・`departure_row`・`merged_into_row`・`counted` ほか)は結びと数え方を表すためのもの。発注との違いは無い。
- **エンジンの口**: `engine/processes/rail_events.py` の `RAIL_EVENTS_FILE`・`READ_RAIL_EVENTS: Final = False`・`load_rail_events(world_dir, *, enabled=None) -> RailEventsAsset | None`・`RailEventsAsset`(frozen・SoA)。既定は読まない。表が無ければ `None`。知らない値は `ValueError`。
- **規則と conf**: 版の表 `w12_timetable_versions.json` の節 `rail_events.rules` と W12 の params に 4 規則(up_merge・nex_in_shonan・sotetsu=mechanism、down_through=expedient)。expedient の規則は `RAIL_EVENT_EXPEDIENTS` の 1 行と台帳の新しい行に対応する(試験あり)。
- **約束ごとの試験**: 合成の到着・上りのまとめ・下りの結び・当駅始発・成田エクスプレス・相鉄線直通(1 本)/負の対照 3(上りの行き先・印なし・上限の外)/知らない駅と種別は止まる/版と列の名と conf/入力の層と京王の切替口/読む口の既定/〔data〕golden・時刻表のバイト一致・ゲート・版の表に時刻なし/読み 1・2 と時ごとのマス/手前の駅の照合/isOrigin の照合。
  **試験の無いもの**: (i) どの過程も `load_rail_events` を呼ばないことの静的な検査(私の grep と AST では 0 件)。(ii) ゲートの成分のうち成田エクスプレスの外れ・相鉄線直通と大崎方面の重なり・地下鉄の発車と列車時刻表の結び損ね・印の分が発車の行に無い、の負の対照。(iii) `origin_flag_mismatch_station_vs_train_timetable` はゲートにも試験にも入っていない(資産のヘッダの値は 0)。
- **〔決定〕の反映**: 時刻表は事実だけ・図は使わない・ファイルも表も git に入れない ✓(足した読み取りは列 `表,平日土休,時,分,印,md5,読み` の CSV と目の読みの文字の記録・決着の JSON。本体の `.gitignore` の `data/` に当たり、本体の `git status` は空)。京王はチャレンジ枠の切替口 `USE_ODPT_CHALLENGE` に従う(仮-15 と同じ扱い・切替口 False で入力からも外れる=試験あり)。銀座線は 9 月改正の版(10-13b §2)✓。

## 3. 発注文の各項

| 項 | 判定 | 根拠 |
|---|---|---|
| 1 終点の到着 | ✓ | 4 線の到着 2,222 行(銀座線・半蔵門線・副都心線=ODPT オープン枠の列車時刻表、井の頭線=チャレンジ枠)。無い線は空欄の宣言 5 件・作り物の時刻なし(資産の到着の行は 4 線だけ)。読み取りの記録は 2-3b と同じ形(読み 1/2・時ごとのマス) |
| 2 直通のまとめ | ✓ | 4 規則・件数・疑わしい組 0・入れ替わりうる組 25・版 1.3.0。埼京線↔相鉄線はまとめる組がもともと無い(相手の線を付けるだけ・北行きは空欄)=発注どおり |
| 3 エンジン側 | ✓ | 読む口の器だけ・既定は読まない・4 行は外せず外す段を改めて理由を書いた |
| 4 計器 | ✓ | README §5(線ごと・平日/土休の発着)・§4(まとめの件数)・§7(1.2.0 との差)。乗降人員とは比べていない |
| 5 資産 | ✓ | `data/world/v2_stage_2-3c/` を 2 回組んで一致(記録)+私が 1 回組んで一致。道具は `stage`・`plan`・`apply --dry-run`・`verify`・`materialize`・`revert`。apply していない |
| 受入の試験 | ✓ | 新規 12 件+既存の W12・台帳の試験の直し。範囲の試験は §7 |
| 記録 | ✓(△ 小さな食い違い=L5) | 発注の欄は全部ある |

「できなかったこと」の申告(4 行を外せない=エンジンが到着を読まない・空欄 5 件・下りの組み方は推測)は実態と合う。

## 4. 守り △

- **書く口**: 発着の表を書くのは `w12_external_nodes.run()` の `C.write_parquet(ctx.out, RE.EVENTS_FILE, …)` の 1 か所、版の表は既存の `C.write_json` の 1 か所 ✓。
- **エンジンの物**: `READ_RAIL_EVENTS` は `Final` の False・`RailEventsAsset` は frozen。ただし中の numpy の配列は `flags.writeable` が True のまま=書き換えられる(L3)。今はどこからも呼ばれないので結果には効かない。
- **呼び出しの無さ**: `src/` 全体の AST(import・名前・属性・文字列 `w12_rail_events.parquet`)で、新しい 2 本の外からの参照は 0 件。
- **負の対照(私が一時の写しで植えた)**:
  1. 写しの `READ_RAIL_EVENTS` を True にした → `test_version_table_names_rules_and_declarations`・`test_engine_reader_is_off_by_default` の 2 件が落ちた ✓。
  2. 合成の成田エクスプレスの便の分を湘南新宿ラインに無い分にずらした → `nex_in_shonan.unmatched` 1・疑わしい組 1 ✓。
  3. 合成の生の表で相鉄線直通と大崎方面を同じ分にした(発車の表は 2-3b の重複の除去の後の 1 行)→ `overlap_with_osaki_table` 0・疑わしい組 0 ✗=**検査が働かない**(M1)。重なりを発着の表の行(線・向き・暦・分で 1 行・属性は先に読んだ表だけ)で数えるので、同じ分の 2 便は 1 行に潰れたうえで片方の表の名しか持たない。実データの生の表では、相鉄線直通と大崎方面の同じ分は 0 件(平日・土休とも)。埼京線に畳んだ 5 表の南行・北行それぞれで同じ分の便は 0 件で、発車の行 453/410(土休は臨時 4 本を除く)と合う=今の数は動かない。

## 5. 宣言と凍結 ✓

- 新しい過程は無い(読む口の器は過程でない)=`writes.paths`/`writes.soa` の宣言・状態台帳の行(軸 1・軸 2)は増えていない。状態台帳・10f の試験は通る。
- W19 の `data_assets` は 91 → 98。足したのは 7 本だけ(成田エクスプレスの表 4・京王の渋谷着 2・東急の当駅始発の印 1)。消えた資産 0・既存の 91 本の sha256 は同じ・`data_assets_missing` 空・`holdout_seal` 同じ。
- 資産の `build_manifest.json` の欄の名は同じ(値が動くのは `build_hash` と `kept`=2-4 で組み直した W9 が今回は keep)。W12 のヘッダの欄の名も同じ。params と notes に足したのは鍵 `rail_events` だけで、既存の鍵の値は同じ。動いたのは `stage_version`・`input_hash`・`param_hash`・expedients(11 → 12)・ゲート(21 → 24)・出力(4 → 5)。ランの manifest の `frozen_sources` は byte-check で同じ。

## 6. 同値 ✓(独立の再計算)

方法: 実装のモジュールを import しない別の script で、本体の data の生の表(ODPT オープン枠の列車時刻表の gz・`_extracted/` の CSV・チャレンジ枠の CSV と東急の駅の時刻表)と資産の parquet を直に数えた。時刻は出力していない。上りのまとめは、実装(地下鉄の**駅の時刻表**で属性を付ける)と違い、ODPT の**列車時刻表**の渋谷発の便と東急の上りの表を(暦・分・行き先・種別=F ライナーは急行)で多重集合で突き合わせた。駅名と種別の写しの表は自分で書いた(知らない駅 0)。

| 項目 | 記録 | 私の再計算 |
|---|---|---|
| 到着 銀座線/半蔵門線/副都心線(平日/土休) | 362/307・282/209・259/237 | 同じ(終点 銀座線 全部・半蔵門線 1/0・副都心線 1/1) |
| 到着 井の頭線(チャレンジ枠・数えるだけ) | 305/261 | 同じ |
| 手前の駅の照合 銀座線 G02 | 669/669 | ODPT 669・ユーザーの表 669・共通 669・表参道に停まらない 0 |
| 上りのまとめ 東横線↔副都心線/田園都市線↔半蔵門線 | 497・498(計 995) | 259+238・289+209=995(相手の無い行 0) |
| 下りの結び | 984(副都心線→東横線 258/236・半蔵門線→田園都市線 281/209) | 同じ・数の合わない組 0・上限の外 0 |
| 渋谷での停車の分の分布 | 0 分 6・1 分 676・2 分 186・3 分 73・4 分 26・5 分 9・6 分 5・7 分 3 | 同じ |
| 入れ替わりうる隣の組 | 25 | 25(隣に限らず任意の 2 組で数えても 25=隣だけの数え方で取りこぼしは無い) |
| 成田エクスプレス ⊂ 湘南新宿ライン | 104 | 104/104 |
| 相鉄線直通の行・大崎方面との重なり | 92・0 | 92・0(生の表で) |
| 発車の行 → 1 本として数える発車 | 3,359 → 2,811・2,914 → 2,467 | 東急の上りの行 548/447 を引いて同じ。資産の `counted` の和も同じ |
| 当駅始発の印 | 185(● 153・⑤ 28・② 4) | 同じ・読み 1 185/読み 2 184・食い違い 1(読み 1 だけ)・final=読み 1・時ごとのマス 47 のうち合わない 1 |
| 印とチャレンジ枠の isOrigin | 185/185 | 共通 185(数えるだけ) |
| 発着の表 | 8,495 行(発車 6,273+到着 2,222)・上りの代表の行つき 995 | 同じ |

## 7. 試験 ✓

- 範囲の試験(作業木・`-n 2 --dist loadfile -m "not slow"`・発注の 13 の対象): **856 passed・1 xfailed・失敗 0**(9 分 23 秒・`requires_data` で飛ばした試験 0)。実装役の 895 は対象の追加 5 本を含む数。
- `lint-imports`(作業木の src): 5 kept・0 broken。
- `tests/c7` は回していない。
- 封印の層: `kddi_la`・`shibuya_jinryu`・`boundary_counts.json`・`odpt_rt`・PT の検証側・検証側の錨・駅の乗降人員の検証側・`_excluded_navitime/` は開いていない。`data/realworld_live/` は 8(b) の指示どおり `odpt_static/2026-10-13/` の列車時刻表だけを読んだ。HEAD の写しには `hunger_energy_validation_anchors_v0.json` が `git archive` で入る(エンジンが開く・私は中を見ていない・置き場ごと消した)。資産を組んだときの W19 は、既存の規則どおり封印の層の sha256 だけを取る(方式 S・中身は解かない)。

## 8. 抜け道と記録

- **(a) 既定の不変** ✓: エンジンは `w12_rail_events.parquet` を読まない(`READ_RAIL_EVENTS=False`・呼び出し 0=grep と AST)。発車の表 `w12_timetables.parquet` の sha256 は本体の v2・実装役の資産・私の資産で同じ `7ef7ab9038348e59`。
- **(b) 到着の行の材料** ✓: §6 の表。
- **(c) 直通のまとめ** ✓: §6 の表。下りの「追い越さない」の推測は宣言されている(台帳 `EX-build.field.w12_external_nodes-b2c96d6a`・expedient・remove_at 7・inferred・`RAIL_EVENT_EXPEDIENTS` の 1 行・規則の conf=expedient・README §14 の 1)。入れ替わりうる組 25 の数え方(同じ暦・同じ行き先の時刻順の隣の 2 組を入れ替えても発車−到着が 0〜10 分)は README §4 の説明とコードが合う。
- **(d) 東急の当駅始発の印** ✓: 読み 1/2 の食い違い 1 件の決着(300 dpi で確かめて読み 1 を採った)が `read2_raw/tokyu_origin_marks_resolutions.json`(1 件)と README §3 にある。時ごとのマス 47・isOrigin 185/185 は照合だけ(構築のコードはチャレンジ枠の東急と JR を読まない=grep)。足したファイルは事実の CSV と文字の記録で、図の写しでない。git に出ない(本体の `data/` は ignore)。読み 2 は読み 1 とチャレンジ枠の総数を見た後に ⑤② を足した(README §3・§14 の 8 で申告済み=読み 2 の独立性は弱まるが、isOrigin との分までの一致が外の物差しになる)。
- **(e) 資産** ✓: `activate_tt23c.py stage --runs 1` を作業用の置き場へ(本体の v2 も実装役の資産も書いていない)。107 本を写して sha256 一致・build_hash `6f2de0e054e49b102da6af1b64fb1e8aee2102ce2663253381f8fa73c062cd28`(記録と一致)。落ちたゲートは前からの W10 の較正 1 件だけ。`plan` を私の資産で取り直すと、同じ 98・置き換え 9・追加 1 で、108 行の action と前後の sha256 が記録の `activation_plan.json` と全部同じ。直下のファイルは実装役の `v2_stage_2-3c` と全部同じ sha256。本体に対する `apply --dry-run` は「前提 OK・何も書いていない」・`verify --want before` は「同じ」(apply はしていない)。
- **(f) 空欄の宣言** ✓: 5 件(JR の渋谷着と始発かどうか・東急→地下鉄の直通の渋谷着・東急の渋谷止まりの渋谷着・相鉄線から来て北へ行く便・折り返しの結び付け)が README §6・`BLANKS`・版の表の `blanks`(5 件)にある。資産の到着の行は 4 線だけ。版の表に時刻(HH:MM)0・語 departure 0・`keio:` 0。
- **(g) 台帳** ✓(親の判断 2 件あり): 行 348 → 349・active 337 → 338・新しい行は `…-7b7c8bd2` の直後・形ごとの数 expedients 143 → 144(試験が通る)。改めた 4 行の根拠:
  - `…-ea8dc0c1`・`…-7b7c8bd2` → 4-3(inferred): 到着の行と列車の鍵は資産に入ったが、エンジンは読まない=着く体は発車の便から降り、発車の表は線ごとに 2 行のまま。外す段を「エンジンが読むかを決める段」とするのは妥当。4-3 で鉄道のエンジンの変更を束ねるかは親の判断(実装役の §15 の 1)。
  - `BR-W11-SHINSEN-EXIT` → 5-0(plan): 到着の元の役は外れ、残るのは W11 の神泉の出口 3 か所の割り当て=時刻表の記録 §6 の親の注「空間の段 0(第 5 期)で直す」と合う。`remove_basis` は前から plan のまま(README §13 の「remove_basis を触った」は誤り=L5)。
  - `HD-engine.processes.rail-1af925f4` → 4-3(inferred): 見出しの項 6 個のうち、4-3 で外れうるのは停車と折返しだけで、運賃・定員・域外居住・到着便の割り当て・混雑率は 4-3 でも外れない見込み。見出し単位の 1 行のままだと 4-3 で「外せない」がまた起きる(L6=項ごとに分けるかは親の判断・実装役も §11 で挙げている)。
- **(h) rebase の見込み** ✓: 本体 `d35a9b6..d518a3d` で 2-3c が触った共有ファイルと重なるのは `docs/design/bridging-ledger.json` だけ(W16#9 の `why` の 1 行)。3 方向の突き合わせ(`git merge-file -p`・標準出力だけ)で衝突 0・結果は 349 行・active 338・W16#9 の第336 の注と新しい行の両方が残る。`test_bridging_ledger.py`・W12 の src と試験は本体で変わっていない=数の行(143 → 144・348 → 349)は本体との間では衝突しない見込み。並行の作業木(3-1・3-2・3-5)が台帳の行や形ごとの数を足していれば、その数の行は手で合わせる。
- **記録の絶対パス・ホスト名**: README・JSON 5 本・道具 2 本に絶対パス・ホスト名・個人名は無い。CR 0(LF)。README と JSON に時刻の列挙は無い。
- **触った共有ファイルの一覧**: README §13 の 5 本と `git diff --stat` の 5 本が一致する。

## 欠陥

| # | 重さ | 場所 | 中身 | 直し方 |
|---|---|---|---|---|
| M1 | 中 | `src/shibuya/build/field/w12_rail_events.py` 483〜485 行(`sotetsu`・`osaki`)と `suspicious_total` | 相鉄線直通と大崎方面の重なりを発着の表の行(線・向き・暦・分で 1 行・`attrs.setdefault` で先の表の名だけ)で数えるので、同じ分の 2 便は 1 行に潰れて重なりが 0 にしかならない(負の対照 3 で確かめた)。README §4 の「疑わしい組 0」の成分の 1 つが空の保証になっている。実データの生の表の重なりは 0=数は動かない | 重なりを読む表の生の行(`user_table_rows` の setdefault の前)で数える。あわせて、畳んだ表どうしで同じ鍵の行が潰れた数(setdefault で捨てた属性の数)をゲートに足す。合成の負の対照の試験を足す |
| L1 | 低 | `tests/build_rail/test_w12_arrivals_2_3c.py` | ゲートの成分のうち成田エクスプレスの外れ・相鉄線の重なり・列車時刻表の結び損ね・印の分が発車の行に無い、の負の対照が無い(私が植えた成田エクスプレスの外れは正しく 1 を数えた) | 合成の負の対照を 1 成分 1 件ずつ足す |
| L2 | 低 | `w12_rail_events.py` 363〜373 行・530 行 | `origin_flag_mismatch_station_vs_train_timetable` を数えるがゲートに入れず、試験でも見ていない(README §4 は「全部一致」と書く) | `suspicious_total` に足すか、data の試験で 0 を確かめる |
| L3 | 低 | `src/shibuya/engine/processes/rail_events.py` 81〜91 行 | `RailEventsAsset` は frozen だが中の配列は書き換えられる(1-3 の教訓=実行時の物は書き換えられないように)。どの過程からも呼ばない静的な検査も無い | 読んだ配列に `flags.writeable = False`(`engine/resolve.py` と同じ形)。`load_rail_events` を呼ぶ過程が無いことの AST の試験(負の対照つき)を足すか、4-3 で読むときに足すと台帳に書く |
| L4 | 低 | README §9・§15 の 7 | HEAD の写しに要るものとして data だけを挙げた。`docs/design/rules-table.json` も要る(§1 の申告=これが無いと 4/4 で final が違う) | 記録の文を直し、10e の docstring の手順に `docs/design/rules-table.json`(と data)を足すかを親が決める |
| L5 | 低 | README §1・§13 | §13 の「`BR-W11-SHINSEN-EXIT` の `remove_basis` を触った」は誤り(plan のまま)。§1 の data に足したものの一覧に `_extracted/tools/__pycache__/tokyu_read1.cpython-312.pyc`(第330 の道具を import した副産物)が無い | 文を直す。pyc は消すか一覧に書く |
| L6 | 低(親の判断) | `docs/design/bridging-ledger.json` の `HD-engine.processes.rail-1af925f4` | 見出し単位の 1 行に 6 項。4-3 で外れうるのは停車と折返しだけ | 項ごとに行を分けるか、4-3 の着手時に棚卸しすると記録に書く |

## 親に確かめてほしいこと

1. **byte-check の HEAD の写しの作り方**: data の junction に加えて `docs/design/rules-table.json` が要る(§1)。発注文の手順(10e の docstring)のままでは、結果が同じ段でも「違う」と出る。10e の docstring を直すか、`docs/design` を丸ごと写す形に決めるか。
2. **仮-15 の範囲**: チャレンジ枠から作った京王の渋谷着 566 行(列車番号 `keio:<番号>` つき)が、活性化前の資産に入った。仮-15 のユーザー確認とライセンス台帳 その 15 の行に到着と列車番号を足す(実装役の案 §15 の 6)。
3. **新しく読んだ事実**: 当駅始発の印(⑤②=番線を含む)は、CLAUDE.md §7 の取り出す事実の一覧(発車時刻・種別・行き先・平日/土休・方面・版)に名前が無い。図の写しではなく事実だが、台帳の行に明記するか。
4. **読み 2 の画像**: 親のセッションの作業用の置き場(scratchpad の `t23c/img`・`img2`)に、東急の PDF の時の帯と凡例の画像が 20 枚残っている(git と data の外)。図は使わない・公開しない扱いなので、取り込みの後に消すか。
5. 台帳の外す段(§8 (g))の 4-3 と、L6 の見出しの行の分け方。
6. 作業木の根の `_bc/`(実装役)は ignore されていない=取り込みに載せない。`_bc_review/` は消した。
