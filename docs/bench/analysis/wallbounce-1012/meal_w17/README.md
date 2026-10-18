# 第 18-1 表の置き換え(小さな版上げ・meal_w17)

正: [回答 10-13b](../../../../design/v2-answers-2026-10-13b.md) §7 の 2(ユーザー決定 2026-10-17・親案 (b))・§0-6(小さな版上げ)・§0-7(性能の記録)・[指示書 10-03](../../../../design/v2-wallbounce-decisions-2026-10-03.md) §7-1(範囲外の人の 1 日を移す)。土台 `32fb262`・枝 `vu/meal-default-from-w17`。

**検証側の値(第 18-1 表・15 分の食事率の数値)はこの記録に写さない**。前の版の値は「前の版の 1 つの値」とだけ書く。

## 0. 要旨

- 範囲外の人(その時間帯に W17 の食事の行が無い体)の**既定の食事時刻**と**初期の空腹**を、W17 v2 の日課の食事の行の開始の分布(構築側)から体ごとに引く形にした(腕 `--meal-default w17`=既定)。
- 既定の腕のエンジンは**検証側の錨のファイルを開かない**(`load_anchors` は構築側の 1 本だけ。open の監査フックの試験と負の対照)。
- 旧値の再現の腕 `--meal-default validation`(環境変数 `SHIBUYA_MEAL_DEFAULT`)は **19/19 構成で HEAD と 25 欄同じ**。この腕は旧値の再現のためだけで、次の版上げで消す(つなぎの台帳)。
- 既定 w17 では 19 構成とも final が動いた(呼数 −0.06〜−4.6%)。主な動きは内受容(空腹)の起床の減り(§4)。
- 既定の食事時刻を使う体: 5,000 体で 99.98%(朝 97.9%・昼 76.1%・夕 57.4%)、39 万体で 99.98%。実際に範囲外で既定の時刻に食べた体は 76.3%(前の版 81.1%)。
- 性能(§6): 前の版より悪くなっていない(1 刻みあたり 31.1〜33.1 ms 対 31.3〜35.0 ms・最大 RSS 約 488〜490 MiB 対 468〜489 MiB)。

## 1. 置き換えの中身

| | 前の版(validation の腕) | この版(w17=既定) |
|---|---|---|
| 既定の食事時刻 | 朝・昼・夕それぞれ **全員 1 つの値**(第 18-1 表の東京都平日の朝と夕の平均時刻・第 7-1 表の最大区分の開始=検証側の表) | 体ごとに **W17 v2 の食事の行の開始の分布**から引く(朝・昼・夕の窓ごと・Philox・鍵=母集団の seed と体の番号) |
| 初期の空腹(0:00 の食後の消費) | EER ×(1440 − 前の版の夕食の 1 つの値)/1440=全員同じ比(全員「ふつう」) | EER ×(1440 − 前夜の夕食の分)/1440。前夜の夕食=その体の W17 の夕の窓の最後の食事の行、無ければ引いた既定の夕食 |
| エンジンが読む錨 | 構築側+検証側の 2 本 | **構築側の 1 本だけ**(`hunger_energy_build_anchors_v0.json`) |
| manifest `energy.anchors` | 2 本を `+` でつないだ道筋 | 構築側の 1 本の道筋 |

W17 v2 の分布(世界資産 `w17_schedule.parquet`=W17 2.0.0・月曜 d0 の全員 390,067 体・食事の行の開始・分):

| 窓 | 行の数 | p5 | p25 | p50 | p75 | p95 |
|---|---|---|---|---|---|---|
| 朝(5:00〜10:59) | 10,972 | 360 | 420 | 450 | 540 | 644 |
| 昼(11:00〜15:59) | 109,189 | 689 | 720 | 739 | 764 | 870 |
| 夕(17:00〜23:59) | 168,967 | 1028 | 1080 | 1140 | 1200 | 1320 |

- 分布の出どころ: 組み立てが世界資産の W17 を `restrict_to` の**前**(全員)に `MealStartDistribution.from_weekly` で作る(体の数に依らない)。その日(暦の曜日)に行の無い窓は全曜日をまとめ、それも無ければ凍結の表。
- 凍結の表 `W17V2_MEAL_START_HIST_15MIN`: 世界資産の W17 の無いラン(合成の世界・data の無い CI)だけが使う。上の行を窓の頭から 15 分ごとに数えた度数(`load_weekly` → `minute_slot` → `(開始 − 窓の頭) // 15` の bincount)。区間の中は一様に引く。出どころの sha256 を `W17V2_FROZEN_SOURCE` に持ち、試験が世界の W17 と度数の一致を見る。
- 引き方: `philox_array(母集団の seed, "energy.meal_default", k19 の鍵=体の番号)` の 3 語を一様の値にし、並べた値の `⌊u·N⌋` 番目。
- 初期の空腹の段(39 万体・seed 1): 満腹 5.0%・ふつう 69.3%・空腹 25.7%(前の版は全員ふつう)。前夜の夕食に自分の行を使う体 42.2%。

## 2. 既定の食事時刻を使っている体の割合(計器 `energy.meal_default_use`)

予定の段=その時間帯に W17 の食事の行が無い体(1 日の表を日ごとに繰り返す=日ごとの値は同じ)。

| | 体 | 計画の無い体 | どれかの窓が既定 | 3 つとも既定 | 朝 | 昼 | 夕 |
|---|---|---|---|---|---|---|---|
| 5,000 体(seed 1・w6_v3_default) | 5,000 | 0 | 4,999(99.98%) | 1,767(35.3%) | 97.9% | 76.1% | 57.4% |
| 39 万体(W17 の全員) | 390,067 | 0 | 389,996(99.98%) | 127,658(32.7%) | 97.2% | 72.4% | 57.8% |

食べた段(5,000 体・1 日): 範囲外で既定の時刻の食事を食べた体 3,816(76.3%)・既定の時刻の食事 5,978 回(前の版 4,054 体・6,379 回)。W17 v2 は朝の食事の行が少ない(全員の 2.8%)=朝はほぼ全員が既定の時刻。

## 3. 旧値の再現(validation の腕)

`byte_check_10e.py side`(19 構成・mock/classical 5,000 体・seed 1・1 日)を HEAD `32fb262` の写し(`git archive`+data のつなぎ)と作業木の `SHIBUYA_MEAL_DEFAULT=validation` で回し `compare`: **19 構成とも 25 欄すべて同じ**(final・呼数・テープの列・行動の件数・checkpoint の 2 本・日の締め・暦・rng・frozen_sources ほか)。HEAD の w6_v3_default の final は `b8eadcb51e8705e7`(第336 の記録と同じ)。

### 3-1. rebase の後の取り直し(検収 M2)

枝を本体の TM の commit `80742bc` に rebase(控え+早送り+merge-file)した後、その版の 10e の道具(`SWITCH_ENV` に `SHIBUYA_MEAL_DEFAULT` が入った版)で、`80742bc` の写し・既定 w17・旧値の腕の 3 つを 19 構成ずつ 1 本ずつ回し直した。

- 旧値の腕対 `80742bc` の写し: **19/19 構成で 25 欄同じ**(compare の JSON は §11 で 2d1ea14 の版に置き換えた)(b の side の `env` に `SHIBUYA_MEAL_DEFAULT=validation` が残る)。
- 既定 w17 対 `80742bc` の写し: 19 構成とも final が動く(同上)。
- `80742bc` の写しの final は 19 構成とも土台 `32fb262` の写しと同じ、既定 w17 の final と呼数も rebase の前と 19 構成とも同じ(本体のカレンダー 1b・TM は既定の結果を変えていない)=下の §4 の表はそのまま。

## 4. 既定 w17 で変わった量(19 構成の差の表・§0-6 の「変わった理由」)

| 構成 | final HEAD | final w17 | 呼数 HEAD → w17 | 食事(範囲内) HEAD → w17 | 行動の件数 HEAD → w17 |
|---|---|---|---|---|---|
| w6_v3_default | b8eadcb51e8705e7 | 333b1820f7849b00 | 64,528 → 64,024 (−504) | 4,434 → 4,297 (−137) | 295,410 → 296,720 |
| w6_v3_activity_off | c88ba9104f45f897 | fe3f46d90e1203f1 | 50,006 → 48,898 (−1,108) | 3,299 → 3,277 (−22) | 172,498 → 169,653 |
| w6_v1_default | e1288e092ddaca86 | 210318331d8bb5dc | 51,655 → 49,787 (−1,868) | 0 → 0 | 183,345 → 179,170 |
| w6_v1_derive_v2_1 | cfbba0d504a27aa7 | c939d891d1171551 | 44,807 → 42,742 (−2,065) | 0 → 0 | 162,504 → 155,313 |
| w6_v2 | c186b380ae65cb86 | 56647d044e6e4ace | 51,266 → 50,174 (−1,092) | 2,052 → 1,965 (−87) | 170,110 → 167,650 |
| w6_v1_edge | d1c56f85847c21db | 57d5eee6e1a92e76 | 46,054 → 45,153 (−901) | 0 → 0 | 94,791 → 92,324 |
| w6_v2_edge | 948b975a2ab74231 | 4c3f3c9e2e2017b1 | 46,655 → 45,906 (−749) | 1,870 → 1,859 (−11) | 91,383 → 90,442 |
| w6_v1_edge_plateau | ff8fc6b562622640 | 70cecfa94488d01a | 47,871 → 46,261 (−1,610) | 0 → 0 | 98,038 → 94,748 |
| w6_old_v1_default | 78b6fec6036b2438 | 529b62042ea68d26 | 51,655 → 49,787 (−1,868) | 0 → 0 | 183,345 → 179,170 |
| w6_old_v1_derive_v2_1 | f647f0483ef3d7ca | 8f0e65d3be2c3ec6 | 44,807 → 42,742 (−2,065) | 0 → 0 | 162,504 → 155,313 |
| w6_old_v2 | 9d8a34ee545f484a | cdddd3415ae5dd58 | 51,266 → 50,174 (−1,092) | 2,052 → 1,965 (−87) | 170,110 → 167,650 |
| w6_old_v1_edge | 245b2fdb8aa229ef | 9efdcc91f9a76363 | 46,054 → 45,153 (−901) | 0 → 0 | 94,791 → 92,324 |
| w6_old_v2_edge | 2fb54c9ad562faca | 927312a45f37fd5c | 46,655 → 45,906 (−749) | 1,870 → 1,859 (−11) | 91,383 → 90,442 |
| w6_old_v1_edge_plateau | dd66261d71c4d6ae | 19c98ddb148f8b6b | 47,871 → 46,261 (−1,610) | 0 → 0 | 98,038 → 94,748 |
| w6_golden_null_arm | 19ee17b1b1caf44c | 7bb4d2a43405333b | 96,695 → 95,981 (−714) | 0 → 0 | 289,561 → 284,538 |
| v3_mem_store | a9f6f9f0adb3f9a4 | 27b1353db7298989 | 64,528 → 64,024 (−504) | 4,434 → 4,297 (−137) | 295,410 → 296,720 |
| v3_mem_rel | 768b2262e3b0999e | bf212900153818d2 | 67,794 → 66,844 (−950) | 4,479 → 4,453 (−26) | 300,390 → 298,991 |
| v3_classical | ca25874a5e4acb79 | e192b390e7434810 | 93,017 → 92,825 (−192) | 9,282 → 9,714 (+432) | 432,738 → 433,043 |
| v3_classical_mem_rel | 9dd9d5684891b57c | ac98c237d5b17e23 | 105,363 → 105,304 (−59) | 9,764 → 10,121 (+357) | 466,666 → 465,201 |

動いた欄(19 構成とも): final・呼数・テープの行と列・行動の件数・checkpoint の 2 本・日の締め・通報の遅れ・気づき。動かない欄: 暦・rng の方式・frozen_sources・開始の日時。「食事」の欄は範囲内の食事(語彙 v1 は 0 のまま)。

理由: 19 構成とも CLI の既定の空腹はエネルギー収支(`--hunger-model energy`)なので、全部が既定の食事時刻と初期の空腹を使う。呼数の差の大半は**内受容(空腹)の起床**(w6_v3_default −522・w6_v1_default −1,126・v3_classical +95)。前の版は全員が同じ時刻に既定の食事をし、全員が同じ空腹の比で 0:00 を始めた(空腹の段の跨ぎが揃う)。この版は時刻と初期の比が体ごとにばらける。古典の 2 構成は空腹の門で飲食店に入る体が増え、範囲内の食事が +4〜5%。帰無腕は、退去の効果 off でも既定と同じ final になった(`test_presence_executor` の golden の注)。

張り替えた golden(前の値は各試験の注・`--meal-default validation` で戻る): `test_state_ledger_10b`(CUR_SYN の all_arms・classical・T7)・`test_state_checks_10f`(K19 の final)・`test_presence_executor`(帰無腕・v3 既定・退去の効果 off の 2 行)・`test_classical_social`・`test_near_tiebreak`(3 行)・`test_relations_tenure`(v1・v2)・`proximity/test_runs`(cell の腕)。語彙 v1 の空腹の腕(`hunger_model="v1"`)と L4 の倍率の行は動かない(エネルギー収支を使わない)。

## 5. 2 日のラン・再開=通し

試験 `test_meal_default_w17.py`: 合成の世界 80 体 2 日(両方の腕・2 日目の 5:00 で止めて再開=通しと同じ checkpoint と final)・世界資産 300 体 2 日(両方の腕・2 日目の 7:00 で止めて再開=通しと同じ final)。腕の違う再開は止まる(設定の指紋 `meal_default`=validation のときだけ足す)。

## 6. 性能の記録(§0-7)

5,000 体・1 日(1,440 刻み)・seed 1・w6_v3_default(語彙 v3・活動層)・別のプロセスで交互に 2 回。機械: Windows 11・Intel 第 6 族 Model 198・論理 20・Python 3.12.10・numpy 2.5.3。**ほかの作業木の実行役が並行して動いていた**(空きメモリ約 3 GB)=壁時計は揺れる。

| 腕 | 回 | final | 実行時間[s] | 1 刻み[ms] | 最大 RSS[MiB] | 判断モデル | LLM |
|---|---|---|---|---|---|---|---|
| validation(=前の版) | 1 | b8eadcb51e8705e7 | 50.42 | 35.01 | 467.9 | 0 | 64,528 |
| w17(この版) | 1 | 333b1820f7849b00 | 47.72 | 33.14 | 487.6 | 0 | 64,024 |
| validation(=前の版) | 2 | b8eadcb51e8705e7 | 45.02 | 31.26 | 489.4 | 0 | 64,528 |
| w17(この版) | 2 | 333b1820f7849b00 | 44.77 | 31.09 | 489.9 | 0 | 64,024 |

前の版より悪くなっていない(1 刻みは同じか少し速い・RSS は 2 回目同士で +0.5 MiB)。起動時の足し分: 分布を作る 0.06 s(39 万体の W17)・体ごとの引きは配列演算。39 万体で範囲外の予定の表を作る時間は 3.0 s(前の版から有る分を含む)。

## 7. つなぎの台帳と「無効」の印

つなぎの台帳 `docs/design/bridging-ledger.json` に 4 行(コードの表 `MEAL_DEFAULT_EXPEDIENTS` と 1 対 1・rebase の後=本体 80742bc の 522 行 → 526 行):

| id | 外す段 | 根拠 |
|---|---|---|
| BR-MEAL-DEFAULT-W17 | 6-6(① 人の選択を判断モデルへ) | plan(10-13b §7 の 2「判断モデルの段で既定の食事時刻をなくす」・段の番号は実装役の当て) |
| BR-MEAL-DEFAULT-VALIDATION-ARM | next-bump(次の版上げ=検収 L6・親の判断で 4-3 から改めた。`PLAN_STAGES` に `next-bump` を足した) | plan(§0-6「次の版上げで消す」) |
| BR-MEAL-DEFAULT-FROZEN | 6-6 | inferred |
| BR-MEAL-DEFAULT-INITIAL-HUNGER | 6-6 | inferred |

「無効」の印: 2-0 の計器 `tools/instruments/anchor_gauge.py` は第 18-1 表と比べない(〔検〕は読まない)ので、印だけを持つ。`record` の段で manifest の `energy.meal_default` を控え、`gauge` の各腕に `meal_time_vs_t18_1` を書く(markdown のラン表の下にも 1 行)。

- 置き換えの前の版の記録(欄なし・validation)=「無効(作る側に使われている=置き換えまで)」。**前の版の第 18-1 表と比べた食事時刻の結果(5a の report ほか)は無効のまま**。
- この版(w17 で、record の段にエンジンが検証側の空腹の錨を開いていない)=「検証可」。比べる道具(5a の `energy_measure.py report`)は記録の側の道具でこの段では触っていない=比べる結果に印を写すのは親の判断(§10)。

## 8. 試験

- 新規 `tests/engine/body/test_meal_default_w17.py`(17 件・うち世界資産 3 件): 検証側の錨を開かない(open の監査フック)+負の対照 2 つ(旧値の腕が開く・既定の腕に「2 本を返す読み口」を植えると見つかる)・既定の腕の錨の名・決定性(同じ seed で同じ・鍵=体の番号=体の数を変えても前の体は同じ)・凍結の表との JSD < 1e-3・世界の W17 との JSD(1 分刻み・朝 < 0.02・昼と夕 < 0.005)と凍結の表=世界の W17 の度数・範囲外の予定(行由来はそのまま・行の無い窓は引いた時刻)・旧値の腕は 1 つの値・初期の空腹の式と範囲・manifest の出どころと割合の計器・CLI の口と指紋で腕の違う再開が止まる・2 日のラン=再開(合成・世界 × 両方の腕)。
- 新規 `tests/tools/test_anchor_gauge_meal_mark.py`(2 件): 印の判定(前の版=無効・w17=検証可・w17 でも検証側を開けば無効)と markdown。
- 直した試験: 上の golden(§4)・`test_energy_balance`/`test_meal_bundle_2b`(前の版の挙動の試験=旧値の腕で回す)・`test_sim_time_T`(体ごとの既定の時刻で日をまたぐ)・`test_env_and_sections_10f`(CONFIG_PATHS_SHA256=rebase の後は本体の `ffbed6e3…e0d0f252` → `ee265d99…80a489d`=`energy.meal_default`・`energy.meal_default_source` の 2 本を外すと戻る・golden の表の検査の 4 行も張り替え)・`test_bridging_ledger`(第 2 形=rebase の後 236 → 240)・`test_state_checks_10f`(静的に安全な乱数の呼び手=rebase の後 18 → 19)・`body_fixtures`(作り物の模型の夕食の分を構築側の値 1140 に)。
- 検収の直しで足した試験: `test_validation_arm_reproduces_the_pre_meal_w17_final_on_the_world`(M1=世界資産 5,000 体・旧値の腕の final と呼数が前の版の定数と同じ)・`test_frozen_table_is_pinned_and_read_only`(L2=凍結の表の sha256 を固定・書き換えは TypeError・分布の配列は書けない)・`test_w17_moves_the_result_and_validation_keeps_one_time_for_any_seed`(L3=名と中身を 1 日に合わせ、旧値の腕は seed に依らず 1 つの値・w17 は seed で変わることを足した)。L1: `test_energy_balance`・`test_meal_bundle_2b` の旧値の直書きを消し、旧値の腕の模型の `default_meal_min` から読む形に(検証側の数値をソースに残さない)。
- 張り替えた golden の試験と本段の範囲の試験をまとめて回した束(`tests/c8/test_sensitivity_ledger`・`memory/test_m1_runs`・`proximity/test_runs`・`speech/test_speech_cli`・`test_classical_social`・`test_intent_chooser`・`test_presence_executor`・`test_relations_tenure`・`test_resume_10d`・`test_salt_seed_split_10f`・`test_state_checks_10f`・`test_state_ledger_10b`・`perception/test_near_tiebreak`・`tests/engine/body`・`tests/engine/bridging`・`test_env_and_sections_10f`・印の試験。slow を含む): 456 passed・2 failed → 1 件(golden の表の検査)を直し、残り 1 件は前からの失敗(下)。
- **訂正(親の指摘)**: `test_state_checks_10f::test_t4_axis2_required_made_discardable_fails` は前からの失敗ではなく、**本段の変更で落ちていた**(前に「HEAD の src でも落ちる」と書いたのは、試験の側が作業木の src を読んでいた取り違え)。旧値の腕では捨てる刻み 750 で通り、既定 w17 では落ちた(合成 100 体 2 日・SYN_KW・seed 1 の会話の開いた刻みは validation 442 と 2007・w17 は 2007 だけ=750 までに開いた会話が 0 になり、O91 `conv.n_opened` を 750 で捨てても 0 のまま=差が出ない)。**直し(親の判断)**: この試験だけ捨てる刻みを 750 → 2,100(両方の腕で会話の開いた刻み 2,007 より後)にした。他の T4 の試験は変えていない。
- **挙動の変化の宣言(親の判断=受入)**: 合成の世界(W17 の無いラン)では、旧値の 1 つの値を全員に使う形が作っていた**一斉の起床の揃いが消える**(validation は 1 刻みに 100 体が同時に空腹の段を跨ぐ刻みがある・w17 は 1 刻みに最大 3〜4 体)。会話の開いた数は seed 1〜8 の 2 日の合計で 12 → 6・750 より前は 5 → 4。空腹の段の跨ぎの総数は同じ(例 seed 1: 323 → 319)・同じセルに起きて居る組の延べは ±5%。会話が減ったのはこの揃いが消えた結果と見る(推測)。実データ 5,000 体では会話の番の呼数 −3%(w6_v3_default 2,905 → 2,813)。
- 前からの失敗(HEAD `32fb262` の src を `PYTHONPATH` にして同じ試験を回しても落ちる=この段と関係ない): `c6/test_l4_l6_budget::test_fleet_smoke_unlimited_defaults_the_queue_to_the_agent_count`・`vocab/test_registry_from_tape::test_ab7_seed1_open_matches_the_parent_report`。環境による失敗: `test_child_imports_this_tree`(作業木の子のプロセスが本体の src を読む)・`test_change_detect_p6`(壁時計 2.13 ms > 2 ms・機械が混んでいた)。
- **rebase(`80742bc`)と検収の直しの後**の範囲(`tests/engine`・`tests/c8`・`tests/economy/cp2`・`tests/tools`・`-n 2 --dist loadfile -m "not slow"`・data つき): 3,157 passed・1 skipped・2 failed=本段で落ちていた t4(上の訂正=直した)と、下の状態の漏れの `test_classical_social::test_run_golden_and_arms`(漏れの値 `ed6d1832…`・単独で 1 passed)。2 日のラン=再開(世界 300 体 × 両方の腕)と M1 の試験はこの中で通った。`lint-imports` 5 kept・0 broken。
- (rebase の前)発注の範囲(`-n 2 -m "not slow"`): 3,011 passed・1 skipped・8 failed。8 件=本段で落ちていた t4 の 1 件(上の訂正=直した)+下の状態の漏れの 7 件(帰無腕・v3 既定・L4・`hunger_v1`・退去 off・関係 on・新しいプロセスの再開。単独と上の束では通る)。`lint-imports` 5 kept・0 broken。
- **data つきの作業木で全体を 1 つのプロセスで回すと、5,000 体の golden の試験が順番によって落ちる**(単独・上の束では通る)。原因は前からの状態の漏れ: `tests/engine/multiday/test_md23_*` が使う道具 `md23/tools/multiday_md23.py` の `set_arms("default")` が近接の腕を `cell`・経済の段階 2 を `off` に戻す(2-4 V2・V4 より前の既定)=後の試験のランが前の既定で回る(落ちた値の 1 つ `4ced1f42…` は `hunger_v1` の行の「〔2-4 V2〕前」の値と同じ)。data の無い写しの全体試験では、これらの試験は飛ぶ。直すのはこの段の範囲の外(親の判断)。

## 9. 触った共有ファイル

`src/shibuya/engine/systems/build.py`(分布を週次表の全員から作る 4 行・範囲外の予定に seed と分布を渡す 1 行・指紋の 3 行)・`src/shibuya/cli.py`(`--meal-default` 1 つ)・`src/shibuya/engine/state_ledger.py`(O28 に `energy.ate_default`・除外の表に範囲外の予定の 6 属性)・`src/shibuya/engine/manifest_sections.py`(energy の設定 2・観測 1)・`src/shibuya/engine/run.py`(`POPULATION_RNG_DOMAINS` に `energy.meal_default`)・`src/shibuya/engine/rng_audit.py`(`SAFE_SITES` に 1)・`docs/design/bridging-ledger.json`(末尾に 4 行)・`src/shibuya/engine/bridging/ledger.py`(`PLAN_STAGES` に `next-bump`=検収 L6)・`tests/engine/test_env_and_sections_10f.py`(CONFIG_PATHS_SHA256)。本段のファイル: `engine/energy.py`・`engine/body/rules.py`・`tools/instruments/anchor_gauge.py`・試験。

## 10. 限界と仮採用(10-13b §0-3)

- 仮採用(つなぎの台帳の行): (a) 前夜の夕食に自分の W17 の行を先に使う(無ければ引いた既定)。(b) 体の既定の時刻は毎日同じ(1 日の表を繰り返す)。(c) 凍結の表は 15 分の区間の中を一様に引く。(d) その日に行の無い窓は全曜日をまとめる。(e) 外す段の番号 6-6 は実装役の当て(旧値の腕は「次の版上げ」=親の判断)。
- **朝の偏り=仮採用のまま宣言**(検収 L9・親の判断): 朝の窓に食事の行を持つ体は 2.79%、朝の窓に「支度」の行があり食事の行の無い体は 65.15%(検収役の数え)=朝食が支度の行に畳まれていると見られる(推測)。朝の既定は 2.8% の体の 10,972 行の分布(p50=450)から全員の 97% に引かれる。朝食の時刻が支度の行の中に隠れる偏りは残る。判断モデルの段(既定の食事時刻をなくす段)で消える。
- W17 v2 は月曜(d0)の行しか無い(d1〜d6 は 0 行・検収 L8)=「その日に行の無い窓は全曜日をまとめる」は実際には月曜の行。月曜以外に始まるランでは範囲外の予定の表が全員「行なし」になる(前からのつなぎ `BR-K9-MONDAY`)。
- `energy.ate_default`(計器 `meal_default_use.ate`・状態台帳 O28=diag・discardable)は日の締めで 0 に戻さず状態のファイルにも入れない(検収 L5=宣言。直すと O28 の他の配列と扱いが変わり full-hash の宣言の変更になる=大きい)。複数日では「どこかの日に既定の時刻に食べた体」、日の途中の再開の後は再開の後の分だけを数える。
- manifest の `energy.default_meal_min` は w17 では凍結の表の中央値=**代表値**(世界の W17 のランでも同じ値・どの体にも使われない・体ごとの引きの無い口だけが使う)。validation では前と同じ「全員の既定の時刻」=欄の意味が腕で違う(検収 L4・`manifest_sections.py` の注にも書いた)。
- 5a の report(`energy-classical-2026-09-28/energy_measure.py`)の第 18-1 表との比較に印を写すかは触っていない(発注の編集範囲の外)。
- 既定の食事時刻をなくす段(判断モデル)までの代役。

## 11. 2 回目の載せ替え(本体 2d1ea14=賃金の版上げ・CT C1 の後)

`80742bc` の上の未 commit の変更 24 本を控え、`80742bc` に戻して `git merge --ff-only 2d1ea14`、ファイルごとに `git merge-file`(控え/80742bc/2d1ea14)を当てた。clean 19 本・衝突 5 本:

| ファイル | 衝突 | 解き方 |
|---|---|---|
| `systems/build.py` | 設定の指紋の段落(本体の C1 の `contact` の段落と本段の `meal_default`) | 本体の段落の後に本段の段落 |
| `rng_audit.py` | `SAFE_SITES` の数の注 | 本体の 21(賃金 +1・C1 +2)に本段の +1=**22 か所** |
| `test_state_checks_10f.py` | `SAFE_SITES` の数 | **21 → 22**(決まらない呼び手は本体の 14 のまま)・t4_axis2 の捨てる刻み 2,100 は残した |
| `test_env_and_sections_10f.py` | `CONFIG_PATHS_SHA256` | 本体の `c8d7f1d4…9b8a5f30` に本段の 2 本を足して計算し直した=**`99fd537f618851011a61f0ffd833c4c39b232e4fa80328949c9c813e3f9e8ba6`**(2 本を外すと本体の値に戻ることを確かめた) |
| つなぎの台帳 | 末尾の追記どうし | 本体の 550 行に本段の 4 行=**554 行**(`next-bump` の行はそのまま) |

`test_bridging_ledger` の第 2 形の数は clean(本体は第 2 形を足していない=数え直して 240 のまま)。golden を張り替えた 8 本は clean で、本体の既定の final は `80742bc` から動いていない(下の 19 構成)=本段の値のまま。

19 構成 × 3(2d1ea14 の 10e の道具・2d1ea14 の写し/既定 w17/旧値の腕・1 本ずつ):

- 旧値の腕対 2d1ea14 の写し: **19/19 構成で 25 欄同じ**=[byte_check_meal_validation_vs_head.json](byte_check_meal_validation_vs_head.json)(b の side の env に `SHIBUYA_MEAL_DEFAULT=validation`)。
- 既定 w17 対 2d1ea14 の写し: 19 構成とも final が動く=[byte_check_meal_w17_vs_head.json](byte_check_meal_w17_vs_head.json)。
- 2d1ea14 の写しの final は 19 構成とも `80742bc`(と `32fb262`)の写しと同じ。既定 w17 の final と呼数も 19 構成とも前と同じ=§4 の表はそのまま。

試験(data つき・`tests/engine tests/economy/cp2 tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`): **3,228 passed・1 skipped・0 failed**(2 日のラン=再開の両方の腕・5a の試験・M1 の試験・t4_axis2 を含む)。`lint-imports` 5 kept・0 broken。

## 12. 艦隊の smoke の繰り延べ(c6・D-55 の前提の既存の穴)

data の無い写しの全体試験で `tests/c6/test_l4_l6_budget.py::test_fleet_smoke_unlimited_defaults_the_queue_to_the_agent_count` が落ちた(合成 300 体・24 刻み・FakeVLLM 2 本・max_in_flight 8・枠は既定=体数 300・`n_deferred_queue_full` 510・期待 0)。`FleetClient.submit` と `_run_call` を包んで数えた(ソースは変えていない)。

| 刻み | validation 送った/断られた | w17 送った/断られた | w17 の種類 | 送る直前の受理待ち |
|---|---|---|---|---|
| 0 | 300 / 0 | 300 / 0 | セルの区画 300(全員) | 0 |
| 1〜23 | 0 | 510 / 510(刻みごと 4・7・7・9・13・14・14・14・17・17・21・23・24・24・25・30・33・33・34・35・35・37・40) | 空腹(内受容)だけ | 300 のまま |
| 合計 | 300 / 0 | 810 / 510 | — | — |

- 刻み 0 に全員が 1 本ずつ呼び、FakeVLLM(1 本 10 ms・同時 8 本)は合成の 24 刻みが終わるまでに 1 本も返さない(壁時計の差)=受理待ちは 300 で満杯のまま。刻み 1 からの呼びは、刻み 0 の呼びを待っている体の **2 本目**で、全部断られる。断られた呼びは次の刻みに送り直され、新しく跨いだ体が足されて 4 → 40 と積み上がる(510 は延べ)。1 刻みに 1 体が送る呼びは最大 1 本・実行中の呼びは 1 体あたり最大 1 本(断られた呼びは実行中にならない)。
- 240 刻みでは繰り延べ **validation 39,563・w17 31,787**(validation の方が多い)。validation は刻み 107 に 300 体が一斉に空腹を跨いで 300 本を送り、全部断られる。1 体が同時に実行中の呼びの最大は validation 3・w17 1。=24 刻みの試験が validation で通っていたのは、その窓の中で誰も跨がなかった偶然。
- 本段で 24 刻みの中に出る理由: 合成の世界は凍結の表から引くので、300 体の初期の段は満腹 15・ふつう 229・空腹 56(旧値は全員ふつう)。初期の比が段の境目(0.25・0.75)の 0.06 下にある体が 49 体あり、24 刻みの中で跨いで内受容で起きる。
- 機構(既存の穴): `systems/decide.py` の艦隊の経路は、返事を待っている体(`fleet_waiting`)にも新しい起床で呼びを送る(`n_fleet_resent` を数えるだけ)=D-55(第289 Q28)の「既定の枠=体数なら繰り延べ 0」の前提(1 体が同時に待つ呼びは 1 本)を前から破る。本段は合成の跨ぎの時刻を散らして、それを 24 刻みの試験に出した(穴は作っていない)。
- 判断(親): 試験の側を直す=刻み 0 の一斉の起床(体数ぶん)だけを見る形(`ticks=1`・既定の枠=体数で繰り延べ 0・枠 32 を明示すれば繰り延べが出る)。両方の腕で通る。穴はつなぎの台帳 `DOC-fleet-resend-while-waiting`(外す段 6-1・inferred)に宣言。エンジンの側の直し(待っている体の起床は返事が届くまで持ち越す=親の推奨)は艦隊の経路の挙動の決定なので、実 LLM の艦隊が戻る前にユーザーが決める(PENDING §1-1)。本段では触らない。

