# 3-1 カレンダー 1a 影(W20cal・腕 --calendar-shadow 1a)の独立検収の記録

> 検収役(Opus 5.5・実装は見ていない)。対象=作業木 `3-1/calendar-1a-shadow`(土台 d35a9b6・未 commit・`git diff --stat` 21 本+新しい
> ファイル 6 つ)。比べた本体の HEAD は 44cfba5(2-3c の取り込みの後=発注文の d518a3d より 2 つ先)。読んだ正: 発注文(実装役)・
> 決定 10-12 §4-1・計画 3-1 の行・R-99・R-116 §5・パターン台帳 §10-2 の区分・親の判断 2026-10-15 と第336 の 4 点。作業用の置き場
> `_bc_review`(記録の外・終わったら消す)。封印の層・第14表・第15-1〜3表・第68-3表は開いていない(§8 (a) の監査フックの数え)。

## 判定

**条件つき受入**。既定(w17)は動かない(自分の 4 構成で 25 欄とも同じ・全 manifest の差も足した分だけ)、資産は自分で組んで
build_hash と表の sha が一致、影の分布と曜日の率は独立に数え直して一致した。直す・親が決めるものは 中 3・低 9(下の「欠陥」)。
中 1(席を持つ体の授業の優先)と中 2(毎週固定 × 曜日の独立=毎週 7 日)は親の判断が要る。

## 1. 結果不変 ✓

- 実装役の JSON: `bytecheck_default_vs_head.json` 19/19 構成で 25 欄とも同じ(d35a9b6 の写し 対 作業木・ただし 02:27 の版=
  第336 の直しの前)/ `bytecheck_default_vs_head_after336.json` 4/4(v3 の既定・v3_mem_rel・帰無腕・古典+記憶+関係)/
  `bytecheck_arm1a_vs_w17.json` 4/4(腕 1a 対 w17)。src の最後の変更(02:56)は 03:03 の 4 構成より前。
- **自分の 4 構成**(`w6_v3_default,w6_v3_activity_off,w6_v1_default,v3_mem_rel`・5,000 体・seed 1・1 日・資産 v2): 本体 HEAD
  44cfba5 の写し(`git archive` で src と 10e の `HEAD_TREE_FILES` の追跡ファイル 8 本・data は本体の data へのつなぎ=回した後に
  .NET の Directory.Delete でつなぎだけを外した)対 作業木の src(`src_is_worktree` 真)。**4/4 構成で 25 欄とも同じ**
  (final `b8eadcb51e8705e7`・`c88ba9104f45f897`・`e1288e092ddaca86`・`768b2262e3b0999e`)。
- 全 manifest(300 体・v3 の既定・HEAD の写し 対 作業木): final 同じ `3dfb30508605d14a`。違う欄は `calendar_shadow`(足した)・
  `manifest_sections.paths.calendar_shadow*`(足した)・`bridges_count`/`bridges_version`/`daily[0].bridges_count`(台帳の行 344 → 347)・
  `env_id`/`environment.code`(コードの同一性)だけ。
- 腕の既定: `DEFAULT_MODE = "w17"`・`build()` は腕が off なら None を返し W20 を開かない ✓。

## 2. 口と約束 ✓(違いは理由つき)

| 発注の口 | 実装 | 判定 |
|---|---|---|
| `calendar_from_attributes(kind, age, industry_key, employment_status, duty_role, …) → 週の表` | `calendar_from_attributes(attrs: Attributes, employment: Employment, materials, anchor, *, n_weeks)` → `{"columns"(19 欄), "counters", "days_per_week", "p_type", "annual_check"}`。地位は別の関数 `draw_employment_status` | △ 形は配列の束(体ごとの引数でない)。中身(属性だけ・決定的・鍵=体・週・曜日)は約束どおり |
| 出力 `w20_calendar_1a.parquet`(体 × 7 日 × 欄)・版の表・W19 の層の元 | 同じ+材料の表 `w20_calendar_1a_materials.json`・ヘッダ `calendar_1a.header.json`(段 id `W20cal`=既存の W20 との衝突を避けた) | ✓ |
| 腕 `--calendar-shadow {w17,1a}`・環境変数・指紋は 1a だけ | `SHIBUYA_CALENDAR_SHADOW`・`set_arm`・build.py で 1a のときだけ `_fp["calendar_shadow"]` | ✓ |
| manifest `calendar` を末尾に | **`calendar_shadow`**(既存の `calendar` の欄=暦の曜日を変えない=1-0 の規則) | ✓(名の違いは正しい) |

約束の各項の試験: 決定的・部分集合で同じ ✓ / 正規は毎週同じ・非正規とシフトは週で変わる(鍵)✓ / 空欄の規則 ✓ / 場所の種類 ✓ /
時刻=第 31/36 表+通勤・[4h,12h] ✓ / 曜日の率=第74-6表・第19表は計器だけ ✓ / 席があって非就業=空欄 ✓ / 守りの負の対照 ✓ /
実データ 5,000 体 ✓ / 腕 1a の 1 日=表の分布 ✓・挙動不変 ✓・再開=通し ✓・段 B ✓。**無いもの**: 実行時の物の書き換えの守りの試験
(中 3)・CLI の `--calendar-shadow` の口(`main` の引数 → `set_arm`・ランの種類 arm)の試験・設定の指紋の中身の試験(名前は
`test_1a_fingerprint_and_missing_table` だが表が無いときの止まりだけを見る=指紋は再開の食い違いで間接に)。

## 3. 発注文の各項

1. 構築側の段 W20: ✓(親の判断で材料が替わった分=曜日は第74-6表・第19表は計器・第6-2表は duty_role だけ=反映)。△ 発注の
   「産業 × 雇用形態の差」は、地位をペルソナから写す決定(追記 3)の結果、duty_role の外の体では産業が予定に効かない(README §3-2 の
   とおり・宣言 W20cal#3/#4)。
2. エンジンの読む口 1 つ: ✓(影は計器だけ=CA2 (a)・W17 のつなぎの量は BR-W17-IO-SLEEP に)。
3. 計器(CA8): ✓(出勤・始業・終業・帰宅の 15 分の分布・通勤時間・15 分の行動者率・空欄・W17 との差・2-0 の 3-4 に源 W20=錨 5)。
   現実とは比べていない ✓。
4. manifest・状態台帳・凍結の表: ✓(§5)。
5. つなぎの台帳: ✓(4 行は W20cal#1・#7・#8・#5)。△ duty_role の行(W20cal#5)の外す段は 4-1(発注文の「6-2 か 7」と違うが、親の
   追記 4=第 4 期 段 4 で置き換え、に合う)。
- 「できなかったこと」(README §13)の申告と実態: 合う。ただし §13-6 は「週 3 日以下の正規」だけを書き、毎週 7 日の側(中 2)と
  授業を優先して勤務を落とす席の体(中 1)は申告に無い。

## 4. 守り △

- 書く口: 影の状態を書くのは `CalendarShadow.relay_day`(day_head の `relay_tables` と組み立ての 0 日目)だけ ✓。
- **負の対照を植えた**(メモリの中だけ・一時): 系 `observe` の関数を包んで刻み 3 で `shadow_day_log` に書く → `SHIBUYA_SYSTEMS_CHECK=1`
  で `AssertionError: 1-0 段 B: 宣言の外の変化 1 件 [(3, 'observe', 'CAL:calendar_shadow.shadow_day_log')]` ✓(試験の時の守りは効く)。
- **実行時の守りは無い** ✗: ランの後の層で `table.cols["commit"][0,0,0] = 7`・`table.cols["new"] = …`・`layer.source = "w17"`・
  `table.found[0] = False` がどれも通った(`__setattr__` の守り・`MappingProxyType`・`setflags(write=False)` が無い=1-3 の教訓の外。中 3)。

## 5. 宣言と凍結 ✓

- 系の表: `day_head` の書く欄に `CAL:calendar_shadow.*`・読む欄に `layers.calendar_shadow`・`close_final` の読む欄に同じ ✓。SoA の書きは無い ✓。
- 状態台帳: 行 `CAL`(軸 1 diag・軸 2 derivable・items 2 つ=hash_skip 2 つ・腕の印なし)・`OWNER_CLASSES`・`EXCLUDED`(table=CACHE・
  n/source=CONST・calendar/weekly=REF)。数え 204 → 205・外 113 → 114 ✓。版は上げない(CT5 と同じ形)。
- 凍結の表 `manifest_keys_frozen.json`: 末尾に `calendar_shadow` を 1 つ足しただけ(と注の文)✓。
- `CONFIG_PATHS_SHA256`: 自分で `config_paths()` から `calendar_shadow.*` の 4 本(schema・source・w20・weeks)を外して sha256 を取ると
  前の `417f0818…72e42b` に戻る=**足した分だけ** ✓。
- manifest の既存の欄の値: §1 の全 manifest の比べで不変 ✓。CLI の既存の引数・テープの列・道筋・持ち主の名: 変えていない ✓。
- T0: 新しい識別子と docstring に「tick」なし・時間の直書きなし(grep)✓。

## 6. 同値 ✓(独立の再計算 3 つ)

- **腕 1a の 1 日のラン**(5,000 体・seed 1・v3 の既定・資産=自分で組んだ写し): w17 と 1a の final `b8eadcb51e8705e7` 同じ・呼数 64,528
  同じ・behavior-hash の列 同じ・`presence_counters`/`presence_exit` 同じ・manifest の差は `calendar_shadow` と `run_kind`(reproduction →
  arm=腕の印・README §6-2 の「節だけ」は run_kind を数えていない=低 9)。影の 0 日目を、parquet を直接読んで自分の式(ランの体の
  `source_agent_id` → 週 0・月曜の行)で数え直した: 影 勤務 2,726・授業 531・表に無い 0・出勤/始業/終業/帰宅の 15 分の分布 4 本・
  翌日に終わる 78・15 分の行動者率 96 枠・通勤の平均 36.716 分が**全部一致**(山 11:15 の 49.02%=README §4-2 と同じ)。
- **曜日の率**(資産の表 390,067 体・duty_role の体=職業ありを除く): 雇用形態の行ごとの勤務の割合と、自分で第74-6表(東京都・
  男女総数・「05_仕事」の列)を読んだ値。正規 87.90/32.66/20.32 対 87.9/32.4/20.4・パート 61.19/31.66/19.12 対 61.1/31.2/18.9・
  アルバイト 61.26/31.09/19.03 対 同・契約 88.18/33.26/20.20・嘱託 87.66/31.89/20.69・派遣 87.87/32.32/21.43・役員 87.96/32.30/20.26
  対 87.9/32.4/20.4・業主(有/無)73.16/51.85/41.08・73.00/52.41/40.78・家族 72.83/53.29/41.27 対 73.9/53.8/41.1。抽選のぶれの
  z は全部 |z| ≤ 2.3=**行ごとの率は第74-6表そのもの**(親の判断 第336 (1)=下回らない)。勤務の体全体の平日 81.0% が第74-6表の
  雇用されている人 83.5% より低いのは混ぜ方(W20 の短時間勤務は勤務の体の約 25%・第74-6表の推定人口では 1,190/7,131 千人=16.7%)。
- **時刻=入力の写し**: 平日の勤務の行の出勤・帰宅を錨 `commute_time_dist_r3.json` のビンで数え、雇用形態の構成で混ぜた JSD は
  出勤 0.000032・帰宅 0.000040(README の 0.00003・0.00004 と一致)。`start = depart + lead` は全行で成り立つ。

## 7. 試験

- 発注の範囲(`tests/build_sched tests/engine/calendar tests/engine/systems tests/engine/time tests/engine/bridging tests/engine/rights
  tests/engine/tools tests/perception tests/engine/test_resume_10d.py tests/engine/test_state_ledger_10b.py
  tests/engine/test_state_checks_10f.py tests/engine/test_env_and_sections_10f.py tests/tools tests/build_audit`・`-m "not slow"`・
  `-n 2 --dist loadfile`・作業木の src): **1,275 passed・failed 0・skipped 0**(data が無くて飛ばした試験 0 件)・19 分 14 秒
  (ほかの作業木と並行)。新しい試験 29 本(18+11)を含む。

- `lint-imports`(作業木の src・231 ファイル): 5 kept・0 broken。`tests/c7` は回していない。

## 8. 抜け道と記録

- (a) 検証側を開いていない ✓: 自分の監査フック(`sys.addaudithook`・開いた名を全部数える)の下で段 W20cal を**全員**(390,067 体)に
  回した: open の事象 245・検証側の 5 本の名 0・封印の語 0・r99 の下で開いたのは第74-9・74-6・19・6-2 表の 4 本だけ。ゲート
  `validation_tables_opened=0`・`r99_opened_within_allow` 合格。`R99Guard` の負の対照(名で落ちる・許可の外で落ちる)は試験にある ✓。
  R-99 本文の第14表・第15-1〜3表の分位(7:15/8:45/10:00・8:30・7:15 など)は W20 と影の式に無い(grep)✓。
- (b) 既定の不変 ✓(§1・§5)。
- (c) 属性から作る関数 ✓: 世界の状態を読まない(入力は属性・地位・材料・錨)・鍵は `philox_array(SEED_KEY, "w20.<用途>",
  k19_counter_array(体, 週, 曜日))`・正規は週 0 の鍵で毎週同じ・非正規とシフトは週ごと(試験)・空欄の規則・公務は産業の欄が空・
  曜日=第74-6表(§6)・第19表は `annual_check` だけ(試験で第19表を替えても約束は同じ)。
- (d) 腕 1a ✓(§6)。W17 のつなぎの量(BR-W17-IO-SLEEP)を `w17_schedule.parquet` と W16 から数え直した: 来街者 96,006 ✓・就寝の
  行 493,474 ✓・388,600 体 ✓・舞台に住む体 43,487 ✓・宿泊 17,492 ✓。「95,976 体の来訪(在圏の行)」は、在圏のブロック(block_kind 2)を
  持つ来街者で数えると 95,974(2 体の差・数え方が道具に無い=低 5)。
- (e) 資産 ✓: 本体の v2 の直下 100 本と acceptance を作業用の置き場に写し、作業木の src で W20cal と `build.run --stage W18 W19 W20
  --keep-stage W0〜W17` を回した。build_hash `2c39885edbed51f7…` 一致・parquet `a5c0d43b…`・材料 `52dd091d…`・input_hash
  `181493af494e4317`・param_hash `3afddd57f7ed8f28` 一致。110 本のうち違うのはヘッダ `calendar_1a.header.json` 1 本だけで、中身の差は
  `notes.input_files[6].path`(W16 の道筋の書き方=置き場に依る=低 4)。v2 との差は W19/W20 のヘッダ・`w19_freeze.json`・
  `build_manifest.json`・acceptance の 2 本・足した 3 本(README §9 のとおり)。
- (f) 台帳 ✓: W20cal#1〜#8・見出しの行・`DOC-ca31-w16-seat-but-nonworking`(1,230 体・ヘッダの `seat_nonworking` 1,230 と一致)・
  BR-K9-MONDAY/W17#2/DOC-md23-weekend-run-test-only は 6-2・数えの試験(expedients 151・見出し 84・HD 85/84)。W20cal の行の id は
  `W\d+#\d+` に当たらない=C8 の D-44 の行の試験の外(脇の段なので正しい)。
- (g) 二重計上 △: 記録(README §3-1)に鉄道業 4,894 人+duty_role 400 体と第 4 期 段 4 がある。台帳の W20cal#5 は記録へのリンクだけで
  量が無い(低 5)。README §3-1 の「W16 の事業所の体」の列(TR 5,833 など)は最後のヘッダ(TR 5,808・SV 38,330・FB 21,701・
  PS 16,305・MW 5,337)と合わない(第336 の前の値=低 2)。
- (h) rebase の見込み(本体 HEAD 44cfba5 と 3 方向で試した): 両方が変えたのは `docs/design/bridging-ledger.json`(自動で合う・
  並びは本体の 2-3c の行 → W20cal の行=規則どおり・行 365・active 354)と `tests/engine/bridging/test_bridging_ledger.py`
  (衝突 1 か所=`count_by_form` の expedients 本体 144 対 3-1 151 → **152**・見出し 84)。manifest の末尾・状態台帳の数え・
  `CONFIG_PATHS_SHA256`・凍結の表・末尾の並びの試験 5 本は本体が変えていない=衝突なし(3-2・3-5 を先に取り込むなら、そちらの欄の
  後ろに `calendar_shadow` を並べ直し、`CONFIG_PATHS_SHA256` と数えを作り直す)。
- 記録の絶対パス・ホスト名・個人名: README・JSON・道具・gauge に無い(grep)✓。触った共有ファイルの一覧(README §12)は
  `git diff --stat` の 21 本と合う ✓。10e の道具は触っていない ✓(第336 (4))。

## 欠陥

| 重さ | 何 | 場所 | 直し方 |
|---|---|---|---|
| 中 1 | **W16 の席を持つ体 4,346 が授業の約束になり、勤務を落としている**(数えも宣言も無い)。`attributes_from_columns` は学校の判定を席の判定より先にする=ペルソナの学校段階が「高校」の種別 0(通勤者)4,185 体(全員 work_cell あり・ペルソナは非正規 3,460・正規 725)と種別 2 の 161 体。種別 0 の授業の場所は域外。W17 ではこのうち 2,872 体に勤務の行があった。親の判断 第336 (3)(席があって非就業=空欄・数える・台帳)と同じ類の食い違い | `src/shibuya/build/sched/w20_calendar_1a.py` の `attributes_from_columns`(`is_school` の後の `continue`) | 数え(例 `seat_school`)をヘッダに出し、台帳に `DOC-ca31-w16-seat-but-nonworking` と同じ形の行(4-1=段 10)。授業だけにするか授業+勤務にするかは親 |
| 中 2 | **毎週固定 × 曜日ごとに独立の抽選で、毎週 7 日勤務の体が 5,629**(毎週固定の体の 3.55%・正規 4,623)、毎週 3 日以下の体が 10,956。正規は「毎週固定」なので一生このまま(週 1 回の休日=労働基準法 第 35 条に反する予定)。README §13-6 は 3 日以下の側しか書いていない | 同 `calendar_from_attributes`(`u_day` の鍵) | 量をヘッダの数えと W20cal#3 に書く。日数の分布の形(週の日数を先に引いて曜日を選ぶなど)は親の判断(設計者の指紋になりうる=先に聞く) |
| 中 3 | 影の層に実行時の守りが無い(1-3 の教訓): `CalendarShadow` に `__setattr__` の守りが無く、`CalendarTable.cols`/`version` はただの dict、配列と `found` は書ける。試験の時の段 B は効く(植えた負の対照で確認) | `src/shibuya/engine/calendar_shadow.py` | 表を `MappingProxyType`+`setflags(write=False)`・層の属性は `relay_day` の中だけ書ける形に・負の対照の試験 1 本 |
| 低 1 | [4h, 12h] の切り詰めの後に帰宅を作り直していない: 勤務の行の 22,972(2.1%)で `return ≠ end + lead`、201 行で終業が帰宅より後 | 同 `calendar_from_attributes`(`short`/`long_` の後) | 切った行は `return = end + lead` にするか、宣言に書く |
| 低 2 | README の古い値: §0 の「錨 1 と平均 6 分・錨 2 と 17 分」(gauge と §5 は 3.3 分・14.6 分)・§3-1 の「W16 の事業所の体」の列・§4-1 の「どの曜日も約束の無い体 99,874」(週 0 に勤務の日が 0 の勤務の体 315 を含めない数=表では 100,189) | `ca31/README.md` | 最後のヘッダと gauge の値に直す・315 体を書く |
| 低 3 | 試験の golden `GOLDEN_5000` の注が「記録 README §4 と同じ値」だが README に無い | `tests/build_sched/test_w20_calendar_1a.py` の `GOLDEN_5000` | README に golden を書くか注を直す |
| 低 4 | ヘッダの `notes.input_files` の W16 の道筋が置き場で変わる(`world/v2_stage_3-1/…` か名だけ)=別の置き場で組むとヘッダのバイトが違う。活性化(v2 へ)でも変わる | 同 `run` の `input_files` | 出力の置き場からの相対の印(例 `<out>/w16_population.parquet`)に |
| 低 5 | 台帳の量: W20cal#5 に二重計上の量(鉄道業 4,894 人の席+400 体)が無い/ BR-W17-IO-SLEEP の量は道具 `ledger_rows_ca31.py` に直書きで数え方の道具が無い(95,976 は自分の数えで 95,974) | `docs/design/bridging-ledger.json`・`ca31/tools/` | 量を行に書く・数えの道具を足す |
| 低 6 | 10e の `SWITCH_ENV` に `SHIBUYA_CALENDAR_SHADOW` が無い=`bytecheck_arm1a_vs_w17.json` の env が空(README が正) | `10e/byte_check_10e.py`(第336 (4) で実装役は触らない) | 取り込みのときに親が足す |
| 低 7 | 段の置き場 `data/world/v2_stage_3-1` の直書き: `anchor_gauge.py` の `DEFAULTS["w20"]`・試験 `test_real_5000_rows_equal_the_stage_asset_when_present` | 2 か所 | 版上げ 3 回目の活性化で v2 に替える(置換忘れの検査の行に) |
| 低 8 | CLI の `--calendar-shadow` の口・ランの種類 arm・設定の指紋の中身の試験が無い(ランの種類 arm は自分のランで確認) | `tests/engine/calendar/` | 試験を 1 本 |
| 低 9 | README §6-2 の「manifest で違うのは calendar_shadow の節だけ」: `run_kind` も違う(reproduction → arm・設計どおり)。ゲート `validation_tables_opened` は守りが開く前に落とすので構造上いつも 0(本当の守りは例外) | `ca31/README.md`・段のゲート | 文を直す・ゲートの意味を注に |

## 親に確かめてほしいこと

1. 中 1: 席を持つ高校生(種別 0 の 4,185・種別 2 の 161)を授業だけにするか、授業+勤務にするか(1,230 体と同じく第 4 期 段 10 で外す行に)。
2. 中 2: 正規の毎週 7 日(5,629 体)を宣言だけで残すか、日数の分布の形を足すか(足すなら設計者の指紋=先に聞く)。
3. 勤務の体全体の平日 81.0% が第74-6表の雇用されている人の 83.5% を下回る(行ごとは一致・混ぜ方の差)ことを、親の判断 (1) の
   「下回らない」の読み(行ごと)として受けてよいか。
4. W20cal は build_manifest の外=build_hash に入らない(エンジンは manifest の `calendar_shadow.w20.sha256` で控える)。版上げ 3 回目で
   `ALL_STAGES` に入れるかと一緒に。
