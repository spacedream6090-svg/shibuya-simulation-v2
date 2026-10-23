# 第 6 期 6-4 連絡の道具の残り(C2 ビデオ通話・CT4 の習慣・CT5 の連絡先の交換とグループ・充電を本人の行動に・C1 の限界 2 件・C6 は行だけ)の記録

- 実装役 Opus 5.5。作業木の枝 `6-4/contact-c2-c6-habit`(土台 `6115860`=カレンダー 3・C3・充電のつなぎの取り込みの後の本体 HEAD)。commit は親。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-4(CT0 共通の決まり 1〜5・CT1 段・CT2 送る・CT3 届く・CT4 範囲の外の人と習慣・CT5 連絡先・CT9 記録)・§1-4・§1-5・[決定 10-03](../../../../design/v2-wallbounce-decisions-2026-10-03.md) §7-3(繰り返しの自動化)・口の約束 1-3・1-7・1-8・10-13b §0-3。先行の記録 [ct_c1](../ct_c1/README.md)・[ca3](../ca3/README.md)(充電のつなぎ)・[ca2](../ca2/README.md)(会話の番の口・誘い)。
- **〔独立検収の直し〕§12 が正**(中 3・低 10 を直した後の数・腕 c1 の参照値の新旧)。§0〜§11 は直す前の記録(数は §4-3 まで)。
- **全部 腕 c1 の中**(`--contact c1`)。習慣だけは下の腕 `SHIBUYA_CONTACT_HABIT {off,on}`(既定 off)。腕 c1 が off(既定)のランは層を作らない。判断は仮のモデル(mock=候補から一様)=数は振る舞いのモデルではない。
- 数は実測。生の出力は作業木の `_bc/`(git の外)。このフォルダには比べた結果([c2_5000.json](c2_5000.json))と道具([tools/run_c2.py](tools/run_c2.py))だけ(絶対パスなし)。検証の錨(C1 の検証の値)は読んでいないし使っていない。

## 0. 結論

- **充電は本人の行動**になった: 道具が「電池が少ない」(20%・10% を下に越えた刻み)と満充電を知らせ(System 1 の通知と同じ刺激の段・道具の語 `電池の知らせ`)、家で本人が「充電する/このまま」「充電をやめる/そのまま」を選ぶ(判断の種類 `P_CHARGE`)。差した体だけ物理で電池が増える(50%/時=つなぎの値をそのまま)・家を離れたら抜ける。カレンダー 3 のつなぎ `BR-CT1-CHARGE-AT-HOME` は **removed**。判断が無ければ電池は増えない(負の対照)。
- **CT4 の習慣**(腕 on・**範囲の外に居る体だけ**=親の判断 2026-10-23・範囲の中の体はいつも判断の口): 本人の過去の選び(状態=勤務中・家・移動中・ほか ごと)が閾値 5 回以上なら、いちばん多く選んだ語で「今読む/後で/無視」「返す/スタンプ/返さない」を答える。記録が少ない・大事な誘い(カレンダー 2 の返事待ちの誘い)・驚き(起床条件 (i))・ときどき(0.1・用途名 `contact.habit`)は判断の口へ戻す。習慣 off=習慣の表を作らない(〔検収 M3〕腕 c1 の参照値は習慣 off でも充電・ビデオ・交換・グループ・既読の文で動く=§12-2)。
- **CT5**: 対面の会話の自分の最初の番(会話の番の口 `note_face_turn`)で「連絡先を交換する」を本人が選べ、相手も応じる/断るを選ぶ → 応じれば両方の帳にメッセージの印。友人のグループを作る/招く/入る/断る/抜けるは本人の判断(画面の候補)。店の番号は場所の表(本段は空欄)=調べる候補は出ない(0)。
- **C2 ビデオ通話**: 電話の器の種類違い。かける/出るは本人・目=画面(相手の顔)・心=通話・電池 20%/時・発話は `Utterance`(via=ビデオ通話)で 1 回だけ記録・知覚の事実は `tool_state` の `call_via`(Percept の形と版は不変)。
- **C1 の限界 2 件**: 既読の印を送った側の画面の判断の候補の文に載せた(行 CT1IS を behavior へ)・道具の台帳にメッセージ・ビデオ通話・充電器・店の番号を調べる・郵便・置き手紙の行(腕 c1 のランの台帳だけ)。**C6** は郵便・置き手紙の行だけ。
- **既定 off の byte-check**: §6。腕 c1 の 5,000 体: 1 日・2 日とも最後まで回る・監査の食い違い 0・記録 on/off で final と checkpoint 同じ・日の途中の再開=通し(§7)。
- **見つけた欠陥と直し(問い 1=親の判断 2026-10-23)**: 5,000 体の世界では住まいのセルが −1 の体が 88.4%(〔検収 L4〕500 体の試しでは 96%)で、範囲の外の活動は作っていない(「待機」のまま「寝ている」が立たない)=カレンダー 3 のつなぎの「家=範囲の外で寝ている刻み」は空振りだった(つなぎの時も直す前の本段も)。親の判断で「住まいが範囲の外の体が範囲の外に居る刻みは家」にした(外す段=境界の層)。2 日の電源の切れた体(習慣 off・延べ/終わり): **108/108 → 62/28**(§4-2)。充電する/やめるは本人の判断のまま。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/contact/habit.py`(新) | 習慣の表 `HabitBook`(体 → 状態 4 × 判断 2 × 語 3 の回数・行 CT1H)・状態 `states_of`・閾値 `HABIT_MIN_RECORDS`=5・戻す割合 `HABIT_RECHECK_SHARE`=0.1 |
| `src/shibuya/engine/contact/tools.py`(新) | 道具の台帳の行 6 つ `CONTACT_TOOLS`・腕 c1 の組み立てだけが足す `register_into` |
| `src/shibuya/engine/contact/device.py` | つなぎの `charge` を消した・`_plugged`・`_low_known`・`_home_prev`・`drain`(差した体は減らない)・`low_alerts`・`charge_plugged`(差した体だけ・電源は差した体だけ入る)・`plug`/`unplug`/`know_low`・`USE_VIDEO`=20%/時・`LOW_ALERTS`=(0.2, 0.1)・`CHARGERS_AT_HOME`=1 |
| `src/shibuya/engine/contact/book.py` | 読み口から持ち主へ(行 CT1B): 交換した連絡先 `_exchanged`・作ったグループ `_made`・招待 `_invites`・調べた店の番号 `_places`・`personal` に交換した相手を足す・`groups_of`・`members`・`group_kind`(友人) |
| `src/shibuya/engine/contact/port.py` | 判断の種類 11〜15(充電・交換・招待に答える・習慣の通知・習慣の返事)・候補の語 16 語・`habit_recheck_u`(用途名 `contact.habit`)・`habit_answer` を消した |
| `src/shibuya/engine/contact/deliver.py` | `VIA_VIDEO`・呼び出しと着信の行の末尾にビデオの印・送った人の索引 `_by_sender`・既読の数 `receipts` |
| `src/shibuya/engine/contact/calls.py` | `CallManager._video`(ビデオ通話のセッション)・`is_video` |
| `src/shibuya/engine/contact/layer.py` | `_battery_physics`(つなぎの `_charge_at_home` を置き換え)・`_charge_decisions`・`_habit_or_decide`・`note_face_turn`/`_face_turn_decisions`・グループと店の番号の口・ビデオ通話・既読の印の候補の文・manifest の `c2`・`habit`・`exchange`・`charge`・`video` |
| `src/shibuya/perception/contact_view.py` | `DeviceView.call_via`(既定 None)・B6 のビデオ通話の行 |
| 共有ファイル | §11 |
| `tests/engine/contact/` | `_c2.py`(台)・`test_c2_charge.py`(10)・`test_c2_habit.py`(13)・`test_c2_exchange.py`(6)・`test_c2_video.py`(4)・`test_c2_runs.py`(8)。`test_c1_charge.py` は消した(つなぎの試験=`test_c2_charge.py` に置き換え) |

## 2. 口の表(誰が=CT0)

| 口 | 置き場 | 中身 | 誰が |
|---|---|---|---|
| 電池の減り・充電 | `Devices.drain`・`charge_plugged` | 使い方で減る(ビデオ通話 > 画面 > 通話 > 待ち受け)・差した体は減らず 50%/時で増える・電池が戻れば電源が入る | 物理 |
| 家を離れたら抜ける | `_battery_physics` | 充電器は家にある | 物理 |
| 電池の知らせ | `low_alerts`・満充電 → `_system1` | 20%・10% を下に越えた刻みと満充電=通知と同じ刺激の段・道具の語 `電池の知らせ`(原因 過程 contact) | 道具 |
| 充電する/やめる | `_charge_decisions`(`P_CHARGE`) | 機会=家で知らせに気づいた刻み・電池が少ないと知っていて家に着いた/起きた/寝た刻み・満充電の知らせ。主の判断が先 | 本人 |
| 習慣 | `_habit_or_decide`・`HabitBook` | 記録が閾値以上ならいちばん多い語・戻す条件 4 つ | 本人(過去の選び) |
| 交換の機会 | `note_face_turn`(`llm_io.utter` が呼ぶ) | 対面の会話の番の控え(その会話の自分の最初の番) | エンジン(控えるだけ) |
| 交換 | `_face_turn_decisions`(`P_EXCHANGE`) | 持ちかける(本人)→ 応じる/断る(相手)→ 両方の帳にメッセージの印 | 本人と相手 |
| グループ | `_make_group`・`_invite`・`_leave`・`_invite_answer` | 作る(連絡先から 1 人を招く)・招く・抜ける・入る/断る | 本人 |
| 店の番号 | `_lookup_here`・`_lookup` | 場所の表に番号のある今いるセルの POI だけ(本段は空欄=0) | 本人(表は構築) |
| ビデオ通話 | `_dial(video=True)`・`_ring_decisions`・`_calls_turns` | かける/出る/話す/切る・目=画面・via=ビデオ通話 | 本人 |
| 既読の印 | `Mailbox.receipts` → 画面の候補「画面を見続ける」の文 | 送ったメッセージの通数・既読の延べ/届け先の延べ | 道具の性質 |
| 道具の台帳の行 | `contact/tools.py`(腕 c1 のランだけ) | メッセージ・ビデオ通話・充電器・店の番号を調べる・郵便・置き手紙(6 欄) | 構築 |

## 3. 流れ

1. 刻みの頭(系 contact の 1): 電池の減り(差した体は減らない)→ 家を離れた体は抜ける → 差した体の充電 → 電源が入った体に網の預かりを届ける → 閾値を下に越えた体・満充電の体に `電池の知らせ` → 画面を見ている体は電池の表示を見る(少ないと知る)→ 充電の機会(家に着いた・起きた・寝た)を置く。
2. System 1: 新しく届いたメッセージ・鳴っている電話・電池の知らせを 1 体 1 回の刺激にまとめる(印の強さ: 着信 > メッセージ > 電池)。電池の知らせに気づいた体は少ないと知る。
3. 判断: 主の判断の「スマホを見る」→ **対面の会話の番(交換)** → 通話の番 → 着信 → 呼び出し → **充電** → 通知・画面・暇。通知と返事は習慣の腕 on なら `_habit_or_decide`。画面の判断は招待があればまず 1 つ答える。
4. ビデオ通話: 画面で「ビデオ通話をかける」→ 宛先 → 窓の境目で着信(via=ビデオ通話)→ 出る=画面で相手の顔(心=通話)→ 番ごとに話す/切る(発話は via=ビデオ通話で 1 回)→ 終わったら画面を見たまま。

## 4. 計器(腕 c1・mock・5,000 体・seed 1・W21・合否なし)

### 4-1. 1 日と 2 日(習慣 off/on・**親の判断(問い 1・2)の前のコード**=家は「範囲の外で寝ている刻み」・習慣は全部の体)

親の判断の後の数は §4-3(最後のコード)。この表は直す前の記録として残す。

| 計器 | off 1 日 | on 1 日 | off 2 日 | on 2 日 |
|---|---|---|---|---|
| final | `ad6577741dc44a30` | `7492082b0b68c598` | `959dead471ad3d5e` | `3d54308df4c12d53` |
| 連絡の出来事の行 | 98,553 | 97,184 | 173,258 | 169,967 |
| 監査の食い違い(発行した呼びの控えと突き合わせ) | 0 | 0 | 0 | 0 |
| calls_by_model の contact(判断モデル / LLM) | 157,636 / 18,851 | 108,870 / 18,574 | 281,461 / 31,495 | 203,212 / 29,745 |
| 電池の知らせ(気づいた) | 98(98) | 62(62) | 286(281) | 209(207) |
| 充電した / このまま / 主の判断が先 | 0 / 0 / 0 | 0 / 0 / 0 | 1 / 1 / 0 | 2 / 3 / 1 |
| 電源の切れた体(延べ・終わり) | 23・23 | 21・21 | 108・108 | 78・78 |
| 交換 機会 / 持ちかけた / 応じた / 断った | 289 / 126 / 70 / 56 | 289 / 126 / 70 / 56 | 560 / 237 / 116 / 121 | 560 / 236 / 115 / 121 |
| グループ 作った / 招いた / 入った / 断った / 抜けた | 399 / 496 / 181 / 167 / 286 | 412 / 530 / 165 / 191 / 284 | 1,182 / 1,509 / 553 / 564 / 899 | 1,160 / 1,544 / 561 / 603 / 885 |
| 作ったグループの成員の数(0/1/2/3 人) | 167/170/62/0 | 174/183/55/0 | 483/564/133/2 | 478/529/152/1 |
| 店の番号を調べた | 0 | 0 | 0 | 0 |
| ビデオ通話 かけた / 出た / 話した番 | 37 / 14 / 12 | 29 / 12 / 11 | 47 / 16 / 14 | 39 / 13 / 12 |
| 習慣で答えた 通知 / 返事 | — | 26,658 / 11,971 | — | 41,349 / 18,648 |
| 判断の口へ戻した 記録が少ない / ときどき | — | 7,508 / 4,093 | — | 11,358 / 6,496 |
| 習慣の表のある体 | 0 | 836 | 0 | 1,069 |
| 壁時計[秒](参考・ほかのランと並んだ機械) | 90.7 | 89.6 | 174.2 | 176.1 |

- 習慣の状態ごと(on 1 日・答えた 通知/返事): ほか 19,779/9,093・移動中 4,701/1,863・勤務中 2,165/1,014・家 13/1。習慣で答えた語(on 1 日): 通知=今読む 6,153・後で 10,888・無視 9,617/返事=返す 6,273・スタンプ 3,765・返さない 1,933。習慣で答えた語も数えるので一度多数になった語が強まる形(癖の強まり=計器 `habit:word:*`・`habit:back:recheck`)。大事な誘いと驚きで戻した数は 0(この構成はカレンダー 2 の腕が無い=誘いが無い・範囲の外の体には起床条件 (i) が来ない)。
- 電源の切れた体の比べ(1 日・終わり): C1(充電なし)52 → カレンダー 3 のつなぎ 24([ca3 §14](../ca3/README.md)) → 本段 23(習慣 off)・21(on)。ただし本段の 1 日では誰も充電していない(§4-2)。
- 数の読み方: 仮のモデルは候補から一様に選ぶ=グループを作って招かれた側が抜ける・断るの数は振る舞いのモデルではない。

### 4-2. 範囲の外に住む体の「家」(問い 1 の材料=親の判断で採用)

- 500 体の試し(2 日)で住まいが範囲の中の体は 20(4%)。範囲の外に居る体の活動は外では「待機」のまま(刻み 0・180・1,200・1,439 で外の 267〜480 体が全員「待機」・「寝ている」は 0)=つなぎの「家=範囲の外で寝ている刻み」が当たらない。
- 案 a(住まいが範囲の外の体は範囲の外に居る刻みを家とする・scratch の差し替えで測った・5,000 体 2 日・習慣 off): 充電した 132・このまま 154・満充電の知らせ 75(やめた 39・差したまま 35)・家を離れて抜けた 56・電源が入った 34・預かりを届けた 8,666・**電源の切れた体 延べ 62・終わり 28**(直す前の形は 108・108)。採用した後の最後のコードの `q_off_2d` は final `9bd558cb…` で同じ計器(§4-3)。

### 4-3. 親の判断の後(最後のコード・問い 1=範囲の外に住む体は範囲の外に居る刻みが家・問い 2=習慣は範囲の外に居る体だけ)

| 計器 | off 2 日 | on 1 日 | on 2 日 |
|---|---|---|---|
| final | `9bd558cbf33b76df` | `d9ddccc8ccef8f7a` | `49735ea090be919c` |
| 連絡の出来事の行 | 213,738 | 103,879 | 216,539 |
| 監査の食い違い | 0 | 0 | 0 |
| calls_by_model の contact(判断モデル / LLM) | 308,791 / 35,589 | 142,834 / 20,245 | 277,906 / 38,219 |
| 電池の知らせ 少ない / 満充電(気づいた) | 291 / 75(286 / 74) | 69 / 11(69 / 11) | 275 / 69(274 / 67) |
| 充電した / このまま / やめた / 差したまま / 家を離れて抜けた | 132 / 154 / 39 / 35 / 56 | 18 / 41 / 8 / 3 / 1 | 123 / 142 / 35 / 32 / 56 |
| 充電で電源が入った / 預かりを届けた | 34 / 8,666 | 1 / 220 | 25 / 6,813 |
| **電源の切れた体(延べ・終わり)** | **62・28**(前 108・108) | **7・6**(前 21・21) | **48・23**(前 78・78) |
| 差している体(終わり) | 37 | 9 | 32 |
| 習慣 範囲の中=判断の口(通知 / 返事) | — | 18,399 / 11,878 | 31,629 / 20,883 |
| 習慣 範囲の外=習慣で答えた(通知 / 返事) | — | 11,227 / 6,227 | 22,025 / 12,513 |
| 習慣 範囲の外=判断の口へ戻した 記録が少ない / ときどき | — | 3,275 / 1,875 | 4,846 / 3,741 |
| 習慣の表のある体 | 0 | 834 | 1,067 |
| 交換 持ちかけた / 応じた・ビデオ通話 かけた | 237 / 116・56 | 126 / 70・36 | 237 / 116・53 |
| 壁時計[秒](参考) | 204.2 | 88.9 | 216.0 |

- 範囲の外の習慣の状態(on 2 日・答えた 通知/返事): 家 21,885/12,409・ほか 99/80・移動中 41/24(範囲の外に住む体は範囲の外に居る刻みが家=家が大半)。習慣で答えた語(on 2 日): 通知=今読む 6,509・後で 8,417・無視 7,099/返事=返す 6,344・スタンプ 3,386・返さない 2,783。
- 電源の切れた体(1 日・終わり): C1(充電なし)52 → カレンダー 3 のつなぎ 24 → 直す前の本段 23(off)・21(on)→ **最後のコード 6(on)**。

## 5. 負の対照

| 確かめ | 対照 | 試験 |
|---|---|---|
| 充電は本人の判断 | 「このまま」を選ぶ=家に居ても電池は増えない・差していなければ増えない・電源は差した体だけ入る | `test_negative_control_no_decision_no_charge`・`test_physics_plugged_charges_unplugged_does_not`・`test_power_on_only_for_a_plugged_device` |
| 充電を外すと電源の切れた体が増える | 合成 80 体 4 日で `_charge_decisions` を外したラン | `test_charging_by_the_person_keeps_devices_alive` |
| 習慣は記録の無い体に無い | 記録 0・閾値未満は答えない | `test_no_records_no_habit_and_threshold`・`test_below_threshold_goes_to_the_decision_port` |
| 習慣の記録は使うまで何も動かさない | 習慣 off と閾値に届かない習慣 on で出来事・選び・控えが同じ | `test_habit_records_do_not_move_anything_until_used` |
| 戻す 4 条件 | 誘い・驚き・ときどき(名のある乱数) | `test_important_offer_goes_back`・`test_surprise_goes_back`・`test_sometimes_goes_back_with_the_named_stream` |
| エンジンは時刻も回数も決めない | AST(C2 の関数に刻み・時刻の剰余や数との比べが無い)+植えた規則を見つける | `test_ast_no_engine_time_or_count_rules_in_c2`・`test_ast_negative_control_catches_a_planted_rule` |
| 本人の語の原因は判断の口 | C1 の AST(本人の語に C2 の 12 語を足した・習慣の口を判断の口に数える) | `test_c1_fixes.py::test_m2_ast_*` |
| 交換は両方の判断 | 断れば帳に付かない・2 番目の番と知っている相手は機会でない | `test_refused_exchange_adds_nothing`・`test_only_the_first_turn_and_not_known_partners` |
| 既定は何も作らない | 腕 c1 off(習慣の腕だけ on)=層なし・連絡の出来事 0・既定の台帳に C2 の行なし | `test_default_off_builds_nothing_and_counts_zero` |

## 6. 既定 off の結果不変(byte-check 19 構成 × 25 欄)

- 土台 `6115860` の写し(`git archive`+`HEAD_TREE_FILES`+data へのつなぎ=回した後に .NET で外した・`tree_missing` 空)vs 作業木・W21 の世界・5,000 体・seed 1・1 日・テープつき・`--jobs 1`(1 本ずつ)・両側の `env` 空: **19/19 構成 × 25 欄 同じ**(`w6_v3_default` の final `bb86f898…`=ca3 の値と同じ・`v3_mem_rel` `94becde2…`)=[byte_check_ct_c2_19cfg.json](byte_check_ct_c2_19cfg.json)。
- 10e の `SWITCH_ENV` に `SHIBUYA_CONTACT_HABIT` を足した(side の JSON に腕を残す)。
- 既定のランでも動く欄(25 欄の外): manifest の `manifest_sections`(節の表に `c2` と観測の子 4 つ)・`bridges_count`(592 → 601)・`bridges_version`(台帳の sha)・日次の記録の `bridges_count`。既定の道具の台帳と manifest の `tools` は今のまま(C2 の行は腕 c1 のランだけ)。

## 7. 2 日・再開・記録 on/off・段 B(腕 c1)

- **記録 on/off**(習慣 on・5,000 体 1 日): final `7492082b0b68c598` が同じ・checkpoint 4 個の behavior-hash が同じ・C2 の計器が全部同じ(記録 off は出来事 0 行)。合成 80 体でも同じ(`test_event_log_on_off_same_with_habit`)。
- **日の途中の再開**(習慣 on・5,000 体 2 日・刻み 2,160=2 日目の正午で止めて再開): final `3d54308df4c12d53` が通しと同じ・止めた後の checkpoint 2 個が同じ・習慣の表・宛先の帳・道具・届いた箱・生きているチャット・差している数が同じ(計器 `meter` は行 CT1M=再開から数え直す)。合成 80 体の 2 日目の途中の再開も同じ(`test_mid_day_resume_is_the_straight_run_with_c2_state`)。
- **段 B**(`SHIBUYA_SYSTEMS_CHECK=1`・習慣 on・5,000 体 1 日・**親の判断(問い 1・2)の前のコード**): **宣言の外 0**(宣言の外があればランが止まる=最後まで回った)・final `7492082b0b68c598`=検査なしのランと同じ・監査 0。混んだ機械で 25,657 秒(約 7 時間)。問い 1・2 の直しは系 contact の中の家の当てはめと計器の数えだけ(書く道筋は変えていない)=最後のコードの段 B は合成 80 体(`test_stage_b_with_c2`・`test_c1_fixes.py::test_h1_*`)で通した。
- **最後のコードの既定 off の 4 構成**: 写し(19 構成の side の JSON)vs 作業木 `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` で 4/4 構成 × 25 欄 同じ(両側の `env` 空)=[byte_check_ct_c2_after_q_4cfg.json](byte_check_ct_c2_after_q_4cfg.json)。19 構成(§6)は問い 1・2 の前のコード。
- 最後のコードの 5,000 体の再開と記録 on/off は回し直していない(§7 の上 2 つは直す前のコード=直しは状態の行と欄を変えていない)。

## 8. manifest の節・設定の指紋・状態台帳・語彙・つなぎの台帳

- manifest の `contact_c1`: 設定の子 `c2`(習慣の腕・閾値・戻す割合・状態・電池の知らせの閾値・充電器・充電の速さ・ビデオの減り・交換の機会・道具の行・店の番号の表の行数・誘いの口の有無)・観測の子 `habit`・`exchange`・`charge`・`video`。`CONFIG_PATHS_SHA256` `94fe399f…` → `ed2674d1…`(`c2` の 1 本を外すと前の値)。`calls_by_model` の内訳 `contact` は今の形のまま(習慣で答えた分は判断モデルに数えない=on で判断モデルの呼びが 157,636 → 108,870)。
- 設定の指紋の `contact` に `habit` の鍵(習慣 on のときだけ=off は C1 の指紋のまま)。
- 状態台帳: 行 CT1B(宛先の帳)・CT1H(習慣の表)を CT1Q の後ろに足した(外 149 → 151・全体 240 → 242)・CT1D の items に `_plugged`・`_low_known`・`_home_prev`・CT1IS を diag → behavior(既読の印が候補の文に入る)+`_by_sender`・CT1K に `_video`・CT1G に `_face_turns`・`_defer_charge`・CT1M に `contact.book.bodiless_dropped`・持ち主 `contact.book`・`contact.habit`。版は上げていない(腕の行=既定のランは不変)。
- 語彙: 族 連絡に 13 語を末尾の別の組で足した(`連絡:充電した`=101 〜 `連絡:電池の知らせ`=113・前のコードは動かない)・via に `ビデオ通話`(末尾)・版 `events-vocab/6-2-ca3` → `events-vocab/6-4-c2`。
- 乱数の用途名 `contact.habit`(動きの側・`SAFE_SITES` 24 → 25)。
- つなぎの台帳 616 → 628 行(active 592 → 601): removed=`BR-CT1-CHARGE-AT-HOME`・`DOC-ct-c1-habit`・`DOC-ct-c1-book-scope`/足した 12 行=`DOC-ct-c2-charger-at-home`(7=〔検収 M2〕境界の層(外の人の活動)ができたら)・`-charge-rate`(7)・`-charge-opportunity`(6-1)・`-habit`(6-1・範囲の外に居る体だけ)・`-habit-scope`(7=同じ)・`-exchange`(6-1)・`-groups`(6-1)・`-store-number`(6-6)・`-video`(7)・`-receipts`(6-1)・`-tool-rows`(6-6)・`-c6-letter`(5-2)。外す段は実装役が当てた(`inferred`・習慣だけ `plan`)。台帳の行を足す・外す道具 [tools/add_bridges_ct_c2.py](tools/add_bridges_ct_c2.py)(冪等・土台の台帳から作業木の台帳が 1 バイト同じに作れる=§12)。判断の種類の通し番号の下の 4 ビット(1〜15)は埋まった=次に足す段は形を変える(〔検収 L9〕port.py に宣言)。

## 9. 限界・仮採用(10-13b §0-3)・親に確かめてほしいこと

**仮採用**

1. 充電の機会の当て方(知らせに気づいた刻み・電池が少ないと知っていて家に着いた/起きた/寝た刻み・満充電の知らせ)・電池の知らせの閾値 20%/10%・電源が切れたことは本人が知る・画面を見ている体は電池の表示を見る・家を離れたら抜ける(物理の当てはめ)。
2. 習慣: 範囲の外に居る体=セル −1(親の判断)・範囲の中の体の選びも記録には数える(使うのは範囲の外に居るとき)・閾値 5・戻す割合 0.1・答え=いちばん多い語(確率で引かない)・習慣で答えた語も数える・状態 4 つ(移動中 → 家 → 勤務中 → ほか・範囲の外の体の「待機」は移動中に数えない)・習慣の答えの原因=判断の種類 14/15 の呼びの id(原因の型は 3 種類だけ=CP12 のため `LlmCall` の形・源=経験・判断モデルの呼び数に数えない)。
3. 交換の機会=対面の会話の自分の最初の番・印はメッセージだけ・両方の電源が入り起きているとき・印は連絡の層の帳(関係の層の辺の欄でない)。
4. 友人のグループ: 作るは連絡先から 1 人を招く・招待は画面を見たときに古い順に 1 つ答える(通知の刺激なし)・家族と職場は抜けない/招かない・成員 0 人のグループも残る。
5. ビデオ通話: 宛先=電話の連絡先・電池 20%/時・終わった後は画面を見たまま。
6. 道具の台帳の行は腕 c1 のランの台帳だけ(既定の台帳と manifest の `tools` は今のまま)。電話の行は既存(1-7)のまま。
7. 既読の印は「画面を見続ける」の候補の文に載せる(送った通数・既読の延べ/届け先の延べ)=仮のモデルは文を読まない=final は動かない。

**限界**

- 範囲の外に住む体は範囲の外に居る刻みを全部家とする(範囲の外の勤め先などと区別しない=境界の層まで)。範囲の外の体には驚き(起床条件 (i))が来ない=習慣を戻す条件は実際には 3 つ。
- 店の番号の表が空欄=調べる候補が出ない・店に電話する口は無い(店のエージェントの後)。
- 体の無い人(遠くの人)は入れていない(CT4 の宣言のまま)。
- 腕 c1 は今も既定にできない(ct_c1 の `DOC-ct-c1-not-default`)。

**親に確かめてほしいこと(問い)**

1. 〔親の判断 2026-10-23=済み〕範囲の外に住む体の「家」=範囲の外に居る刻み(§4-3)。〔検収 M2〕外す段は `7`(inferred)・文に「境界の層(外の人の活動)ができたら」と書いた(§12)。
2. 〔親の判断 2026-10-23=済み〕習慣は範囲の外に居る体だけ(§4-3)。
3. 習慣の答えの原因の形(判断の種類 14/15 の `LlmCall`・呼び数に数えない)でよいか。
4. 既読の印の載せ方(候補の文)と、行 CT1IS を behavior にしたこと。
5. 用語集との照合はしていない(新しい語「習慣の表」「電池の知らせ」「友人のグループ」「交換の機会」)。

## 10. 試験

- 新しい試験(`tests/engine/contact/`): `test_c2_charge.py` 10・`test_c2_habit.py` 13・`test_c2_exchange.py` 6・`test_c2_video.py` 4・`test_c2_runs.py` 8(合成=体 6 の台 `Harness2` と合成 80 体の `run_day`)。
- 範囲(`tests/engine tests/economy tests/perception tests/build_pop tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`・`tests/c7` は回さない・問い 1・2 の前のコード): **4,226 passed・1 skipped・0 failed・0 errors**(55 分 43 秒・ほかの作業木のランと並んだ機械)。
- 問い 1・2 の後(最後のコード): `tests/engine/contact`+`tests/engine/bridging`(同じ引数)=**161 passed・0 failed・0 errors**(範囲の全体は親の merge_stage で回す=親の指示)。
  新しい試験は `test_c2_habit.py` 13(範囲の中は判断の口)・`test_c2_charge.py` 10(範囲の外に住む体は外で家)。
- lint-imports: 5 kept・0 broken(303 ファイル)。
- slow(`test_c1_world.py`=5,000 体)は回していない(5,000 体は §4・§7 の道具のランで見た)。

## 11. 触った共有ファイル

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/events/vocab.py` | `CONTACT_EXTRA_WORDS`(13 語・表の末尾)・`VIA_WORDS` の末尾 `ビデオ通話`・版 `events-vocab/6-4-c2` |
| `src/shibuya/engine/systems/llm_io.py` | `utter` に連絡の層の会話の番の控え(腕 c1 のランだけ) |
| `src/shibuya/engine/systems/table.py` | 系 llm_receive と decide の `paths` に `CT1G:contact._face_turns`・`reads` に `layers.contact` |
| `src/shibuya/engine/systems/build.py` | 連絡の層に `work_cell`・`phones`・道具の行を台帳に足す・カレンダー 2 の `offer_waiting` を `offer_probe` に挿す |
| `src/shibuya/engine/calendar2/layer.py` | 読み口 `offer_waiting`(読むだけ) |
| `src/shibuya/engine/state_ledger.py` | §8 の行と items・持ち主・除外 |
| `src/shibuya/engine/manifest_sections.py` | `contact_c1` の設定の子 `c2`・観測の子 4 つ |
| `src/shibuya/engine/rng_audit.py`・`src/shibuya/engine/run.py` | `contact.habit` |
| `docs/design/bridging-ledger.json` | §8 |
| `docs/bench/analysis/wallbounce-1012/10e/byte_check_10e.py` | `SWITCH_ENV` に `SHIBUYA_CONTACT_HABIT` |
| 試験(数と版の凍結) | `tests/engine/events/test_e_vocab_is_closed.py`・`tests/engine/speech/test_speech_port_schema.py`・`tests/engine/experiment/test_x33_apply.py`・`tests/economy/stage2/test_stage2_account_and_conservation.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/test_state_checks_10f.py`・`tests/engine/test_env_and_sections_10f.py`・`tests/engine/contact/test_c1_runs.py`・`test_c1_fixes.py`・`test_c1_units.py`・`tests/engine/calendar3/test_ca3_runs.py`(7 日の「電池 0 の体 0」を「80 体全員が 0 にならない・本人が充電した」に=つなぎを外したため) |

## 12. 独立検収の直し(条件つき受入=中 3・低 10 → 全部直した・rebase はまだ)

検収の記録は [review.md](review.md)。直しの後の数はこの節が正。

### 12-1. 直しの表

| 欠陥 | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| M1 slow の試験が赤 | `tests/engine/contact/test_c1_world.py` | `W_DIAL` と `W_VIDEO_DIAL` を集め、(かけた人・相手・via)で突き合わせる・着信の via は通話/ビデオ通話だけ | `test_world_ring_arrives_at_the_window_boundary`(slow を 1 プロセスで 6 passed) |
| M2 親の判断を台帳に当てていない | `docs/design/bridging-ledger.json` | `DOC-ct-c2-charger-at-home`・`DOC-ct-c2-habit-scope` の外す段を `7`(inferred)・文に「境界の層(外の人の活動)ができたら」 | `tests/engine/bridging` |
| M3 腕 c1 の参照値の変化 | `contact/arm.py`・本記録 §0・§12-2 | arm.py の docstring を「習慣 off=習慣の表を作らない・参照値は C2 で動く」に直した・新旧を §12-2 に | — |
| L1 系 contact の reads | `systems/table.py` | `layers.calendar2` を足した(大事な誘いの口) | 段 B(`test_stage_b_with_c2`・`test_c1_fixes.py::test_h1_*`) |
| L2 交換が仲裁を見ない | `contact/layer.py`(`_face_turn_decisions`・`_exchange_ask`・`_exchange_answer`) | 主の判断が先(例外にしない): その刻みに主の判断の呼びのあった体は持ちかける/応じるを次の刻みに回す(`_defer_exchange`=行 CT1G) | `test_exchange_follows_arbitration_main_decision_first` |
| L3 古い文・使わない引数 | `habit.py`・`layer.py` | 「範囲の外で寝ている刻み」と `_TRANSIT_OUTSIDE` の注を直した・`_home_mask` の引数 `sleeping` を消した | — |
| L4 96% | 本記録 §0 | 5,000 体の世界の値 88.4% に | — |
| L5 台帳の行を足す道具が無い | `tools/add_bridges_ct_c2.py`(新) | 冪等(外す 3 行=状態と注・足す 12 行=同じ id は置き換え)。土台 `6115860` の台帳に 2 回回して作業木の台帳と **1 バイト同じ**(`cmp` で確かめた) | — |
| L6 範囲の外の体の充電の機会が 1 回だけ | `contact/layer.py`(`_charge_decisions`・`_battery_physics`)・台帳 `DOC-ct-c2-charge-opportunity` | 家に居て電池が閾値の下の体は、その刻みに判断したとき(主の判断か連絡の判断)にいつも候補を出す(発注の「家にいて充電器がある刻み」の形)。充電の判断はその刻みの判断の後に置いた | `test_charge_is_offered_whenever_the_person_thinks_at_home_with_a_low_battery` |
| L7 成員 0 のグループが残る・日数で重くなる | `contact/book.py` | 作ったグループを番号 → 行の表にし、抜けて 0 人になったら消す(招待も消える)・体 → グループの索引 `_member_of`(`groups_of` は索引を引くだけ)・番号は通し番号(使い直さない) | `test_a_group_with_no_members_disappears_and_its_invites_too` |
| L8 ビデオの小さな点 | `perception/contact_view.py`・`deliver.py`・`calls.py`・`layer.py` | `VIA_VIDEO` の定義を contact_view の 1 か所に・着信の行で via を区別(`DeviceView.ringing_via`・B6 のビデオの着信の行)・`PERCEPT_SCHEMA` は値と比べる | `test_percept_value_marks_the_face_without_changing_the_shape` |
| L9 判断の種類の 4 ビットが埋まった | `contact/port.py` | 1〜15 で埋まった・次に足す段は通し番号の形を変える、と宣言 | — |
| L10 ca3 の 7 日の試験 | `tests/engine/calendar3/test_ca3_runs.py` | 負の対照=充電の判断を「このまま」に固定すると誰も充電しない(電池が増えない)・電源の切れた体が多い・送れない連絡が少なくない | `test_seven_days_negative_control_no_charge_decision` |

### 12-2. 腕 c1 の参照値(5,000 体・1 日・習慣 off・mock・W21・seed 1)

| 段 | final | 理由 |
|---|---|---|
| カレンダー 3 のつなぎの後(ct_c1 §16 の注) | `59930cf3…` | — |
| 本段(独立検収の前のコード・検収役のラン) | `956834e0…` | 習慣 off でも充電の判断・ビデオ通話・交換・グループ・既読の文が入る(判断の呼びと乱数の通し番号が動く) |
| **本段(直した後=最後のコード)** | **`edc3d0dc5d1778fa`** | L2(交換の仲裁)・L6(判断のたびの充電の候補)・L7(グループの索引と掃除)で動く |

- 直した後の 5,000 体(習慣 off・[c2_5000.json](c2_5000.json) の `runs_after_review`): 1 日=連絡の出来事 102,737 行・監査 0・充電した 51・判断のたびの機会 101・電源の切れた体 延べ 5・終わり 5。**2 日=電源の切れた体 延べ 40・終わり 16**(直す前 62・28)・充電した 192・このまま 172・満充電の知らせ 115(やめた 60)・家を離れて抜けた 88・預かりを届けた 9,366・生きている友人のグループ 721(作った 1,254・成員 1 人 464/2 人 256/3 人 1・0 人は無い)・交換 持ちかけた 228/応じた 117・ビデオ通話 かけた 51・監査 0。

### 12-3. 既定 off・段 B・記録 on/off・試験(直した後)

- **4 構成(既定 off)**: 本体 `b1b6dd7` の写し vs 作業木 `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` で **4/4 構成 × 25 欄 同じ**(final `bb86f898…`・`3cdf9dbf…`・`8fca095b…`・`94becde2…`・両側の `env` 空・`tree_missing` 空)=[byte_check_ct_c2_review_b1b6dd7_4cfg.json](byte_check_ct_c2_review_b1b6dd7_4cfg.json)。
- 合成の段 B(`SHIBUYA_SYSTEMS_CHECK=1`・腕 c1+習慣 on)と記録 on/off(final と checkpoint)は `test_c2_runs.py` で通した。5,000 体の段 B と再開は直す前のコードの §7(回し直していない)。
- 試験(最後のコード): `tests/engine/contact`+`tests/engine/calendar3`+`tests/engine/bridging`(`-n 2 --dist loadfile -m "not slow"`)=**207 passed・0 failed・0 errors**・slow `tests/engine/contact/test_c1_world.py`(1 プロセス)=**6 passed・0 failed**・lint-imports 5 kept・0 broken。範囲の全体は親の merge_stage で回す(親の指示)。

## §親の検収(第337・2026-10-23・Fable 5.1)

- **実在と差分**: 作業木の 48 本(src=contact の 7 本+habit・tools・perception/contact_view・vocab・llm_io・table・build・calendar2/layer・state_ledger・manifest_sections・rng_audit・run/ tests 新規 6+張り替え 11+消した 1(test_c1_charge=つなぎの試験)/ docs・台帳)を親がディスクで確かめ、明示の一覧で stage(`commit_check` 一覧 48=ステージ 48・秘密スキャン CLEAN・絶対パスと個人名 0・CR 0・新しい識別子に `open`/`tick` 0)。親 commit efb5382 → 本体 b1b6dd7(カレンダー 3・4-2b・店の仕事・段 1 の後)へ rebase=衝突 10(台帳=3 方向の行の合わせ=段の差分(足した 12・変えた 3)を本体の上に=666 行・active 638・重複 0/ `vocab.py`=連絡の 13 語のコードを仕事の 4 語(101〜104)の後ろ 105〜117 に付け直し・版は最後の段 `events-vocab/6-4-c2`・118 語/ `systems/table.py`=両方の行(親の最初の解き方が文字列の連結のカンマを落として SyntaxError=直した)/ `test_env_and_sections_10f.py`=設定の指紋を実測 `94d2cc0c…7e481ffa` に(contact_c1.c2 の 1 本を外すと段 1 の `30242fe6…` に戻ることを親が計算)/ `test_state_ledger_10b.py`=external 155・total 254/ `test_state_checks_10f.py`=SAFE_SITES 26・UNDETERMINED 17/ 版の文字列 3 本/ `test_du_runs.py` の語彙の並び)=`d35ba06`。解いた後の影響の試験(events・10b・10f・contact・duties・bridging ほか)=488 passed(語彙の並びの試験 1 本を合わせた後)。
- **既定 off の byte-check(親・4 構成)**: 本体 b1b6dd7 の src の写しと作業木の src で `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` の 25 欄が全部同じ([byte_check_ct_c2_parent_4cfg.json](byte_check_ct_c2_parent_4cfg.json))。
- **範囲の試験(親・-n 4・not slow)**: `tests/engine tests/economy tests/perception tests/build_pop tests/c8 tests/tools`=**4,359 passed・1 skipped・0 failed・0 errors**(29 分 26 秒)。
- **data 無しの写しの全体試験(CI-1 と同じ印)**: **5,902 passed・297 skipped(data 無し)・0 failed・0 errors**(37 分 30 秒・d35ba06・faulthandler 900 秒の門に当たらず)。
- **親の判断**: 実装の途中の問い 2 件=家の当てはめ(住まいが範囲の外の体は範囲の外に居る刻み=境界の層ができたら外す=7・inferred)・習慣は範囲の外に居る体だけ。検収の中 3・低 10 は直し済み(slow の c1_world・外す段・参照値の注・reads・仲裁・充電の機会・0 人のグループ・VIA_VIDEO・4 ビットの宣言・負の対照)。腕 c1 の参照値は ca3 の後 `59930cf3…` → `edc3d0dc…`(習慣 off でも充電・ビデオ・交換・既読の文で動く=ct_c1 §16 に注)。語彙のコードの付け直しと指紋・状態台帳の数の合わせは親(本節)。
- **読んだ所**: `contact/habit.py`(範囲の外の体だけ・閾値 5・戻す 3 条件・LlmCall 14/15)・`contact/device.py`(電池の知らせ・差した体だけ増える)・`contact/layer.py`(`_charge_decisions`=家に居て電池が低い体に判断のたび・`_face_turn_decisions`=仲裁に従う)・`contact/book.py`(成員 0 のグループは消える)・`events/vocab.py`(`CONTACT_EXTRA_WORDS` の位置)。
