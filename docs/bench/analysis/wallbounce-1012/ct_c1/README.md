# 第 6 期 6-4 CT C1 の仕組み(連絡の道具・腕 `--contact c1`)の実装の記録

- 実装役 Opus 5.5。作業木の枝 `6-4/contact-c1`(土台 `4f186fb`=6-5 記憶の腕を含む本体の候補)。commit は親。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-4(CT0 共通の決まり・使っている間の気づきにくさ=係数を掛けない・CT1 C1・CT2 送る・CT3 届く・CT4 範囲の外の人と習慣・CT5 連絡先・CT9 記録の欄)・§4-2 TM1(届くのはエンジン・気づく/読む/返すは本人・電話は窓の境目・続いているチャットは「チャットの会話の状態」)・TM3(会話)・[口の約束](../../../../design/v2-foundation-contracts-2026-10-13.md) 1-2・1-3・1-6・1-7・1-8・1-8b・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) 第 6 期 6-4 の行・回答 2-1(第 6 期のコードを GPU の前に腕で)。土台の記録: [c0](../c0/README.md)(1-7)・[j0](../j0/README.md)(1-8)・[s8b](../s8b/README.md)(1-8b)・[tm32](../tm32/README.md)(3-2 の窓)・[mr65](../mr65/README.md)(6-5)。
- **全部 腕**(既定 off=層を作らない=今のまま)。C1 の版上げ(計画の版上げ 2 回目)は後。検証の錨の値は読んでいないし使っていない。
- 数は実測。生の出力(テープ・状態のファイル)は作業木の `_bc/`(git の外)。このフォルダには比べた結果だけを置く(絶対パスなし)。
- **〔独立検収の直し〕§13 が正**(高 1・中 5・低 8 を直した後の数・畳んだ記録の形・段 B・本体 `32fb262` への ff)。§0〜§12 は直す前の記録。

## 0. 結論

- 腕 `--contact {off,c1}` を 1 つ足した(環境変数 `SHIBUYA_CONTACT`)。下の腕は環境変数だけ: `SHIBUYA_CONTACT_UNNOTICED`=`i`(既定)/`ii`/`iii`(割り込めなかった出来事の載せ方)・`SHIBUYA_CONTACT_SEND`=`b`(既定=文は LLM の口)/`c`(選択の言葉をそのまま送る)。
- **既定 off で結果不変**: byte-check 19 構成 × 25 欄が土台 `4f186fb` の写しと全部同じ(19/19・[byte_check_ct_c1.json](byte_check_ct_c1.json))。5,000 体・2 日の通しと日の境目の再開も final `b346bb6e3ecc60af`・checkpoint・日の締めの 2 本が同じ([two_days_default.json](two_days_default.json)・§9)。
- **腕 c1(mock 5,000 体・1 日)**: 最後まで回る。連絡の出来事 1,120,765 行(族 `連絡`)が 1-3 の記録に `via` つき。本人の判断の語の原因は全部 c1 の判断の呼び(`LlmCall`・源と番号つき)・時刻は判断の刻み(送ったは次の窓の境目)・届く語の原因は網(過程 `contact`)=**監査の食い違い 0**。電話は窓の境目で鳴る。日の途中(T=720)で止めた再開=通し(final `58f9d4d7942c29de`・checkpoint 同じ)。
- 目と心の向きは係数でなく形: 画面を見ている体の知覚の事実は、物を見分けず、人は周辺視の範囲の数だけになる。関心の的が周りでなく驚き駆動の入口で起きていない体は、周りの出来事(顕著行為)を処理しない(載せ方は 3 つの腕・記憶に残らない)。
- 仮のモデル(mock)は候補を一様に選ぶ=数は振る舞いのモデルではない(§5 の注)。壁時計は既定の約 2.8 倍・出来事の記録は 1 日 約 81 MB(5,000 体)=**腕は既定にしない**(§5-2)。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/contact/__init__.py`(新) | 包みの説明だけ |
| `src/shibuya/engine/contact/arm.py`(新) | 腕と下の腕の切替口・設定の指紋の組 `config()`・状態台帳の腕の名 `contact-c1` |
| `src/shibuya/engine/contact/device.py`(新) | 道具の状態 `Devices`(電源・電池・マナーモード・置き場・元の置き場・イヤホン=体ごとの配列・最初の値は母集団の側の乱数 `contact.device`)・通知の刺激 `stimulus`(SNR の段の形)・電池の減り `drain`・電波 `signal_ok` |
| `src/shibuya/engine/contact/attention.py`(新) | 目と心の向き `Attention`(視線の先・関心の的・画面を見始めた時刻・前の活動・最後に気づいた通知)・周辺視と割り込みの形 `coarsen`・顕著行為の門 `gate_salient` |
| `src/shibuya/engine/contact/port.py`(新) | 判断の口 `ContactPort`(`DecisionPort` の子=J0 と同じ入口・仮のモデル)・候補 `cand`・文の口 `MockTextPort`・習慣の口 `habit_answer`(いつも判断の口に戻す)・長さの上限 `cap_text` |
| `src/shibuya/engine/contact/deliver.py`(新) | 届いた箱と予約 `Mailbox`(届く・預かる・未読・既読・着信・呼び出し・掃除)・待ち行列の種類の番号と順位と届け方 |
| `src/shibuya/engine/contact/chat_state.py`(新) | チャットの会話の状態 `ChatBook`(`conversation.Session`・`ConvState` をそのまま使う・沈黙の閾値は対面と同じ) |
| `src/shibuya/engine/contact/calls.py`(新) | `CallManager`(`ConversationManager` の子)・`CallSpeechPort`(`SpeechPort` の子)=腕の名だけを足した子 |
| `src/shibuya/engine/contact/book.py`(新) | 宛先の読み口 `ContactBook`(関係の層の連絡先の印・人も記憶の腕・グループの一覧・体の無い人を落とす) |
| `src/shibuya/engine/contact/layer.py`(新) | 持ち主 `ContactLayer`・系 `sys_contact`・窓の境目の結び `bind_queue`・描画の口 `percept_hook`・manifest の `contact_c1`・監査 `audit_causes` |
| `src/shibuya/perception/contact_view.py`(新) | 知覚の事実の値 `AttentionView`・`DeviceView`(既存の欄 `mind_dir`・`tool_state` に入れる)と B2/B5/B6 の行の文面 |
| `src/shibuya/perception/renderer.py` | 口 `contact_fn`(既定 None)・`perceive` の後に口を通す・B2/B5 の差し替えと B6 の行・共有でない場面はセルのキャッシュを読まず書かない(`_scene_is_shared`)・計数 3 つ |
| 共有の 13 ファイル | §11 |
| `tests/engine/contact/`(新) | §10 |

## 2. 口の表

| 口 | 置き場 | 中身 | 誰が(CT0) |
|---|---|---|---|
| 打ち終わり(送信) | `ContactLayer._reserve` → 待ち行列の種類 `contact.send`(BOUNDARY・順位 −2) | 送る判断の刻みの次の窓の境目に送る(打つ時間の代わり=§7) | エンジン(時刻は待ち行列の届け方) |
| 届く(メッセージ) | `_send_now` → `Mailbox.deliver` | 送った時刻に相手の道具へ(電源の切れた相手は網が預かる=本段は充電が無いので預かったまま)。`連絡:届いた`(received_ns=送った時刻・原因 網) | エンジン |
| 着信(電話) | 種類 `contact.ring`(BOUNDARY・順位 −1)→ `_ring_now` | 窓の境目で鳴る(3-2 の「境目で配達する種類」)。相手の電源が切れている・話し中・鳴っている=`連絡:不通` | エンジン |
| 既読 | `Mailbox.read_all`・`連絡:既読` | 読んだときに送った側の道具へ(道具の性質) | エンジン |
| System 1(通知の刺激) | `Devices.stimulus`・`_system1` | 新しく届いた分と鳴っている電話 → チャネル(音・振動・画面)と段(届かない/弱い/強い)→ 関心の的の門 | 体と道具(物理) |
| 気づいたら | `ContactPort.choose`(J0 の形) | 今読む/後で/無視 | 本人(判断の口) |
| 暇なとき | 同 | スマホを見る/このまま過ごす(暇な活動に入った刻みと、暇な間に起きた刻み) | 本人 |
| 画面 | 同 | 読む・メッセージを送る・グループに送る・電話をかける・画面を見続ける・顔を上げる | 本人 |
| 宛先・グループ | 同+`ContactBook` | 連絡先の印(手段ごと)・グループの一覧(家族・職場) | 本人(候補は 1-7 の器) |
| 返す | 同+`MockTextPort` | 返す/スタンプを送る/返さない・スタンプは一覧から・文は文の口(腕 b)か選択の言葉(腕 c)・長さの上限は安全装置 | 本人 |
| 電話 | 同+`CallManager`・`CallSpeechPort` | 出る/出ない・待つ/切る・話す/切る(番の話者は対面の会話の交替)・発話は `Utterance`(via=通話)で 1 回だけ記録 | 本人(番の上限=安全装置) |
| 目と心の向き | `Attention`・`coarsen`・`percept_hook` | 視線の先・関心の的を状態に持ち、知覚の事実の形を変える | 状態(本人の行動で動く) |
| 顕著行為の門 | `gate_salient` | 関心の的が周りでなく割り込めなかった体を「気づいた体」から外す | System 1 |
| 習慣 | `habit_answer` | 本段は作らない=いつも判断の口に戻す(計器 `habit_fallbacks`) | 本人(後の段) |
| 記録 | `ContactLayer._log`(書く口 1 つ)・`CallSpeechPort.say` | 1-3 の `Event`(`via`・`received_ns`/`read_ns`・`origin`=範囲の外の送り手 `contact:outside`) | — |

## 3. 届く/気づく/読む/返すの流れ

1. 本人 A が画面を見ている刻み T に「メッセージを送る」→「宛先 B」を選ぶ(判断の口 2 回・call_id `c1:T:A:<番号>`)。文は文の口(mock=定型の文)。`Utterance`(1-8b の形)で本文とモーラ数を検査し、送信を予約する。
2. 次の窓の境目(T+60 秒・刻みの事象より前=順位 −2)に `連絡:送った`(A・whom=B・how_much=モーラ数・原因=1 の判断)→ 同じ時刻に `連絡:届いた`(B・received_ns=送った時刻・原因 網)。チャットの状態に 1 通。
3. 次の刻みの系 `contact` で B の System 1: 新しく届いた分の刺激と段 → 関心の的の門(周りと画面=弱い刺激から・通話と会話=強い刺激だけ)。気づいた通知は次の刻みの知覚の事実(`tool_state`)に載る。
4. 気づいた B(画面を見ていない)は「今読む/後で/無視」。今読む=取り出して画面を見る・未読を全部読む(`連絡:読んだ`=時刻は判断の時刻・原因の入力=届いた行の目印)→ 送った側に `連絡:既読` → 会話ごとに「返す/スタンプ/返さない」→ 返すなら 2 と同じ。後で・無視=`連絡:後で`/`連絡:無視`(未読のまま=次に画面を見たときの「読む」の候補)。
5. 相手の返事でチャットは参加(続いているチャット)になる。沈黙(対面と同じ刻み数)で締め → 終わり。
6. 電話: 画面で「電話をかける」→「宛先」→ `連絡:電話をかけた`(関心の的=通話)→ 境目で `連絡:着信` → 相手の System 1(鳴っている間は毎刻み)→ 気づいたら「出る/出ない」→ 出る=`ConversationManager.invite(…, answered=True)`=対面の会話と同じセッション → 番ごとに話者が「話す/切る」(話す=`行為:発話` via=通話・相手の次の番の入力=聞こえた発言の目印)→ 切る=`連絡:切った` → 締め → 終わりで `連絡:通話の終わり`。かけた側は鳴っている間「待つ/切る」。
7. 範囲の外の体(セル −1)も同じ(体を持つ=判断する)。送ったものに `origin=contact:outside`。体の無い人は宛先に入らない(§12)。

## 4. 目と心の向きの形(係数を掛けない)

- **視線の先**(前/画面/手元/相手)と**関心の的**(周り/画面/通話/会話)を状態に持つ。関心の的は毎刻み状態から置き直す(通話 > 画面 > 会話 > 周り)。視線が画面になるのは本人の判断(スマホを見る・今読む)だけ。前に戻るのは本人の判断(顔を上げる)・体の反射(3-5 の器 `loud_sound_notice`=値は空=本段では 0 回)・寝た・電池が切れた・電話を耳に当てた(かけた・出た)。
- **周辺視**: 視線が画面の体の知覚の事実は、見えた物(店・目印・看板)を認識しない(`seen_objects` 空・`signage_shown` 偽)。見えた人は周辺視の範囲 2.0 m の中の数だけ(`people_hint`=誰か・何をしているかは無い・描画は粗い段「なし/1 人/数人/多くの人」)。**確率で間引かない**(範囲の中の人は全部数える・同じ入力からいつも同じ写し)=見える範囲と細かさの形。描画は B2 の可視物の行を「画面を見ていて、周りの物は見分けていない」に、B5 の近接の行を「視界の端に人の気配(…)」に替える。
- **割り込み**: 関心の的が周りでない体は、周りの出来事(B4 の顕著行為)を、その刻みに驚き駆動の入口(起床条件 (i)=セルの B4 の変化=`change_detect` の形)で起きたときだけ処理する。処理しなかった出来事は (1) 描画の入力の載せ方を腕で変え((i) 落とす (ii) 落として B6 の隅に「周りで何かあったようだ(注意は向いていない)」(iii) そのまま)、(2) 顕著行為の「気づいた体」から外す(記憶の書き手が覚えない)。
- **通知の門**: 刺激の段(SNR の段の形)と関心の的で決める。寝ている体は気づかない。
- **耳**: イヤホンの音(75 dB)を周りの騒音(W10 の騒音の段 → 帯の dB)に電力で足した雑音で、着信音の SNR を取る(R-78 §5-2 の −3 dB/−10 dB の形・値は expedient)。
- **「気づいた」は記憶で測る**: 顕著行為に気づいた体(門の後)が、次の刻みの記録に記憶の書き手の `知覚:気づき`(1-6 の器)を持つかを数える(器の無いランは `null`)。
- `p_see × 0.49`・歩きスマホ 0.46 は掛けていない(1-2 で消したまま)。

## 5. 計器(腕 c1・mock 5,000 体・1 日・合否なし)

構成: 世界の資産 v2・語彙 v3・seed 1・CLI の既定(記憶・関係 off)=「c1」(載せ方 i・送る文 b)。比べに「関係あり」(`--memory on --relations on`=宛先が関係の層の連絡先の印)。

| 計器 | c1 | 関係あり |
|---|---|---|
| final | `58f9d4d7942c29de` | `7f94e5557a436c33` |
| 連絡の出来事(行) | 1,120,765 | 389,187 |
| via グループ / メッセージ / 通話 / 無し | 1,085,407 / 5 / 3 / 35,350 | 311,506 / 36,852 / 20,536 / 21,762 |
| 監査の食い違い | 0 | 0 |
| 送った 1 対 1 / グループ | 2 / 40,795 | 9,640 / 11,940 |
| 届いた(体×通) | 396,125 | 121,681 |
| 網が預かった(電源の切れた相手) | 2,367 | 0 |
| 刺激 強い / 弱い / 届かない | 80,163 / 28,002 / 52,423 | 31,059 / 14,787 / 20,740 |
| うちマナーモード・かばん | 届かない 37,925(全部) | 届かない 14,424(全部) |
| 気づいた(周り / 画面 / 会話 / 通話) | 108,060(50,427 / 57,625 / 8 / —) | 43,373(23,309 / 16,623 / 18 / 3,423) |
| 気づかなかった(周り / 会話 / 通話) | 52,528(52,505 / 23 / —) | 23,213(20,774 / 26 / 2,413) |
| 今読む / 後で / 無視 | 16,743 / 16,900 / 16,792 | 7,353 / 7,598 / 7,401 |
| 読んだ(通) | 307,399 | 95,049 |
| 読むまで[分] 中央 / 90% / 99% / 最大 | 2 / 130 / 617 / 1,110 | 3 / 177 / 579 / 1,062 |
| 返した / スタンプ / 返さない | 10,817 / 10,825 / 10,888 | 5,992 / 5,882 / 5,786 |
| スマホを見た(暇 / 今読む) | 26,099(9,356 / 16,743) | 17,309(9,956 / 7,353) |
| 顔を上げた(判断 / 寝た / 電池 / かけた) | 25,994 / 21 / 39 / 1 | 11,806 / 22 / 0 / 4,940(出た 527) |
| 画面を見た長さ[分] | 1〜34(1 分 8,047) | 1〜26(1 分 6,796) |
| 電話 かけた / 鳴った / 出た / 出ない / 鳴らして切った / 不通 | 1 / 1 / 0 / 0 / 1 / 0 | 4,940 / 4,656 / 1,519 / 1,570 / 1,550 / 301 |
| 通話の番 / 切った / 番の上限 | 0 / 0 / 0 | 1,469 / 1,493 / 26 |
| 通話の長さ[刻み] | — | 1:793・2:347・3:185・4:100・5:44・6:50 |
| チャット 開いた / 続いた / 沈黙で締め / 上限 200 通 | 1,547 / 924 / 1,435 / 101 | 6,696 / 2,571 / 6,685 / 4 |
| 顕著行為 居合わせた(周り / 画面 / 会話 / 通話) | 7,702 / 156 / 2 / — | 8,174 / 79 / 1 / 18 |
| 顕著行為 気づいた / 門で外した | 181 / 1(画面) | 486 / 8(画面 7・通話 1) |
| 割り込めなかった出来事のあった描画 | 12 | 6 |
| 描画の連絡の行 / 予算を超えて落ちた行 | 2,393 / 0 | 1,158 / 0 |
| 電源が切れた体 / 電池の平均(終わり) | 52 / 0.727 | 0 / 0.741 |
| 判断の呼び(連絡・全部 習慣から判断の口へ) | 225,025 | 137,043 |
| 窓の境目の事象 / 遅れの最大 | 40,818 / 60 秒 | 26,523 / 60 秒 |
| 宛先の出どころ | 世帯のグループ(家族) | 関係の層の連絡先の印 |

- **器あり**(`--memory on`+記憶の器 events・final `93882d3d50a377b4`・連絡の計器は c1 と同じ): 顕著行為に気づいた体のうち記憶に残った(記録に `知覚:気づき`)=周り 178/178・画面 2/2。居合わせた体に対しては周り 178/7,702・画面 2/156。
- **割り込めなかった出来事の 3 つの腕**: 判断(mock)は描画を読まない=final と計器は 3 つで同じ(`58f9d4d7942c29de`)。違いはテープの描画だけ: 64,528 の呼びのうち (i) と (ii) は 12 の呼びで違う(B6 の隅の行=プロンプトと B6 の ID)・(i) と (iii) も 12 の呼びで違う(B4 のブロックの有無)=割り込めなかった出来事のあった描画 12 と一致。
- **送る文の腕 c**: 計器は b と同じ・届いた箱の本文が選択の言葉になる=final が違う(`b650de6b95dfebf4`)。
- **数の読み方の注**: 仮のモデルはそのときある候補から一様に選ぶ(画面の候補は最大 6 つ=宛先の無い手段や未読の無い「読む」は出ない)。関係の層の無いランは 1 対 1 の宛先が家族(同じ世帯がランに居る体)だけなので、グループのメッセージが多い。数は振る舞いのモデルではない(判断モデル 6-1 で置き換える)。
- 体の無い人を落とした数: 0(本段の母集団の宛先には体の無い人が居ない=合成の試験で確かめた)。

### 5-2. 性能とバイト(腕のときだけ・参考)

- 壁時計(同じ機械で 4 本を並べて回した参考): 既定 off 44.1 秒・c1 117〜125 秒・関係あり 87.8 秒(1 日・5,000 体)。重さの内訳は測っていない(推測: 届いた・読んだ・既読の出来事の行と体ごとの判断の呼び)。体の数に比例する Python のループは無い(判断する体の数ぶん=送った数と見ている数で決まる)。
- 状態: 道具 9 B/体(CT1D)・目と心の向き 11 B/体(CT1A・CT1AS)+気づいた体ごとの最後の通知。届いた箱は終わりに 396,125 行(未読 88,726・読んだ行は 1 日で落とす)。1 行のバイトは未計測(日の途中 T=720 の状態のファイル全体は 1.95 MB 圧縮)。
- 出来事の記録: 1 行 72 B × 1,120,765 行/日=約 81 MB/日(5,000 体=約 16 KB/体/日)。39 万体への線形の外挿(推測)は 1 日 約 6 GB=1-3 の宣言を大きく超える=**既定化の条件を満たしていない**(mock の量・既読を読んだの行に畳むか・保持窓は既定化の前に決める)。

## 6. 負の対照

| 確かめ | 対照 | 試験 |
|---|---|---|
| エンジンは時刻も回数も決めない | 読む判断の原因をエンジン(過程 contact)に差し替えると監査が食い違いを数える。合成の監査で「エンジンが読んだ」「判断と離れた送信」「本人の判断で届く」の 3 つを数える | `test_negative_control_an_engine_rule_for_reading_is_caught`・`test_audit_catches_engine_decided_reads_and_sends` |
| 電話は窓の境目で届く | 着信の種類を窓の中(`IN_WINDOW`)にすると、かけた時刻と同じ時刻に鳴る=境目の確かめが落ちる | `test_negative_control_ring_inside_the_window_fails_the_boundary_check`(幅 60 秒・30 秒の境目の試験と対) |
| 周辺視は係数でなく形 | 視線が前なら知覚の事実は同じ・画面なら範囲の中の人は全部数える(同じ入力から同じ写し) | `test_negative_control_front_gaze_keeps_the_facts`・`test_peripheral_vision_coarsens_the_percept_by_shape` |
| 刺激の段は形 | 同じ状態からいつも同じ段・閾値の前後だけで段が変わる | `test_the_levels_are_a_shape_not_a_coefficient` |
| 割り込み | 起床条件 (i) で起きた体は出来事がそのまま通る | `test_an_interrupt_lets_the_event_through` |
| 既定は何も作らない | 腕 off=層なし・manifest に節なし・族 `連絡` の出来事 0 | `test_default_off_builds_nothing` |
| 腕の取り違えの再開は止まる | c1 で書いた状態を off で再開=設定の指紋の `contact` で止まる | `test_resuming_with_the_arm_off_stops` |

## 7. T2 の口が来るまでの代え方(宣言)

- **打つ時間**: 送る判断の刻みの次の窓の境目に送る(種類 `contact.send`=BOUNDARY)。幅 60 秒なら 60 秒・30 秒(腕)なら 30 秒。
- **読む間**: 読む時刻=本人の判断の時刻(刻みの頭)。届いてから読むまでの時間は、気づく(System 1)と判断の刻みで決まる(エンジンは決めない)。
- **通話の番**: 対面の会話と同じく 1 刻みに 1 番(モーラ数 × 話す速さの時計は T2)。
- つなぎの台帳 `DOC-ct-c1-chat-clock`・`DOC-ct-c1-chat-silence`(外す段 T2)。

## 8. manifest の節・設定の指紋・状態台帳の行・つなぎの台帳

- manifest の一番上の鍵 `contact_c1`(腕 c1 のランだけ=既定のランの鍵の集合は今のまま=`manifest_keys_frozen.json` は変えていない)。設定の子 15(`schema`・`arm`・`unnoticed_arm`・`send_arm`・`contacts_source`・`queue_kinds`・`notice_min_level`・`device`・`attention`・`port`・`stamps`・`mock_text`・`message_max_chars`・`chat_silence_steps`・`provisional`)・観測の子 14(`meter`・`decisions`・`read_delay_minutes`・`call_steps`・`screen_minutes`・`chats`・`calls`・`mail`・`devices`・`attention_now`・`salient`・`remembered`・`bodiless_dropped`・`rendered`)。節の表 `manifest_sections.PATHS` の混ざった辞書に足した=設定の道筋の一覧が 15 本増える(`CONFIG_PATHS_SHA256` `b48498e8…` → `bd35bdfd…`=この 15 本を外すと前の値)。既定のランでも manifest の `manifest_sections`(節の表そのもの)の値は動く(byte-check の 25 欄の外・6-5 と同じ形)。
- 設定の指紋に `contact`(腕 c1 のときだけ=`{"arm","unnoticed","send"}`)。
- 状態台帳の腕の行(腕の名 `contact-c1`・持ち主の居るランだけ 2 つのハッシュと状態のファイルに入る=既定は不変):

| 行 | 道筋 | 軸 1 / 軸 2 |
|---|---|---|
| CT1D | `contact.dev._on`・`_battery`・`_manner`・`_home`・`_place`・`_ear` | behavior / required |
| CT1A | `contact.attn._gaze`・`_focus`・`_prev_act`・`_notice` | behavior / required |
| CT1AS | `contact.attn._gaze_since` | diag / required |
| CT1I | `contact.mail._inbox`・`_unseen`・`_held`・`_pending`・`_ringing`・`_calling`・`_next` | behavior / required |
| CT1IS | `contact.mail._sent` | diag / required |
| CT1C | `contact.chats._sessions`・`_of_key`・`_next`(順を保つ) | behavior / required |
| CT1K | `contact.calls.sessions` ほか 9 属性(O39・O40・O91 と同じ・順を保つ) | behavior / required |
| CT1S | `contact.speech.inbox` | behavior / required |
| CT1M | 計器(`contact._meter`・`_ct_hist`・`_hangup`・`_exposed_prev`・チャットと通話と通話の発話の口の計数) | diag / discardable |

- 待ち行列(行 BW=捨ててよい)に入れた送信と着信は予約の表 `_pending` に持ち、再開では待ち行列を作った後の結び `bind_queue` が境目の時刻で入れ直す。
- 状態のファイルの許可したクラスは足していない(`Session`・`ConvState` は既にある)。
- つなぎの台帳 19 行(`DOC-ct-c1-device-initial`・`-device-sound`・`-device-drain`・`-no-charging`・`-device-signal`・`-attention-peripheral`・`-attention-focus-order`・`-attention-interrupt`・`-notice-gate`・`-port-candidates`・`-port-text`・`-separate-call`・`-chat-clock`・`-chat-silence`・`-book-scope`・`-habit`・`-calls-form`・`-mail-keep`・`-percept-fields`=467 → 486 行)。コードの expedient の宣言の 6 形は使っていない(形ごとの数の凍結は変わらない)。

## 9. 結果不変

- byte-check 19 構成(5,000 体・seed 1・1 日・テープつき)× 25 欄: 土台 `4f186fb` の写し(`git archive`+`HEAD_TREE_FILES`+data へのつなぎ=回した後に外した)と作業木で全部同じ(19/19・既定 v3 の final `b8eadcb51e8705e7`・両側の `env` 空)=[byte_check_ct_c1.json](byte_check_ct_c1.json)。作業木の側は最後の直し(描画のキャッシュの条件)の後に回した。
- 5,000 体・2 日(既定): 写し・作業木の通し・作業木の日の境目の再開で final `b346bb6e3ecc60af`・checkpoint・日の締めの 2 本が同じ([two_days_default.json](two_days_default.json)・描画のキャッシュの条件を直す前に回した=その直しは既定のランでは何もしないことを上の 19 構成で確かめた)。
- 腕 c1 の再開: 合成の世界(グループの一覧を入れた・2 日)で日の境目の再開=通し・5,000 体 1 日の日の途中(T=720)の再開=通し(final `58f9d4d7942c29de`・T=1079 と 1439 の checkpoint の 2 つのハッシュが同じ)。

## 10. 試験

新しい試験 `tests/engine/contact/`(共通 `_c1.py`=腕の切替・連絡の層だけを回す合成の台 `Harness`・判断の差し替え):

- `test_c1_units.py`(30): 道具の状態と刺激(マナーモードとかばんで弱い・イヤホン・画面・電源・段の形)・電池・最初の状態(母集団の seed)・周辺視の形と負の対照・3 つの腕・割り込み・顕著行為の門・関心の的の順・チャットの状態の遷移と安全装置・既読と掃除・宛先(家族とグループ・関係の印・体の無い人)・判断の口の鍵と並べ替えへの不変・長さの上限・監査の負の対照・腕の切替・粗い段。
- `test_c1_flow.py`(15): 打ち終わりは境目・届くのは送った時刻・読む時刻は判断の時刻・既読・着信は窓の境目(幅 60・30)と負の対照・通話は対面の会話の仕組み(番・聞こえた発言・切るは本人)・番の上限・グループと続いているチャット・通知の門(段と関心の的)・範囲の外の人と出どころの印・送る文の腕 c・長さの上限・画面の長さと寝たら閉じる・エンジンの規則の負の対照・電源と不通・予約の結び直し。
- `test_c1_runs.py`(8): 既定 off は何も作らない・腕 c1 の合成のラン(manifest の節と節の表・監査・宛先の出どころ)・2 日の再開=通し・腕を取り違えた再開は止まる・腕の行・ランの種類・CLI の引数・系の宣言。
- `test_c1_world.py`(6・slow・data): 5,000 体 1 日の記録と監査・電話の境目・マナーモードとかばん・周辺視の描画・3 つの腕・日の途中の再開。

結果(作業木の src・本体の .venv):

- 全体(`-m "not slow and not gpu" -n 6 --dist loadfile --ignore=tests/c7`): **5,416 passed・1 skipped・1 xfailed・1 failed**。落ちた 1 本は `tests/vocab/test_registry_from_tape.py::test_ab7_seed1_open_matches_the_parent_report`(data の下のテープの道筋の確かめ)=土台 `4f186fb` の src の写しでも同じく落ちる=本段と関係ない。
- slow(`tests/engine/contact/test_c1_world.py`・5,000 体): 6 passed。
- `tests/engine/contact`(slow を除く): 53 passed。
- lint-imports: 5 kept・0 broken(272 ファイル)。
- 秘密の検査(`tools/scan_secrets.py` に変えたファイル全部): CLEAN。

## 11. 触った共有ファイル(取り込み順の rebase の一覧)

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/systems/table.py` | import 1 行・`activity_intent` の後に系 `contact`・`close_final` の reads の末尾に `layers.contact` |
| `src/shibuya/engine/systems/conductor.py` | `declared_check` に引数 `window_paths`(既定 None=腕 c1 が立っているときだけ `WINDOW_PATHS` を窓の境目で通す・腕 off は前のまま行 BW の鍵だけ)・`WINDOW_PATHS`・`WHEN` の末尾・`queue.register` の直後の結び 2 行 |
| `src/shibuya/engine/systems/boxes.py` | `OWNER_NAMES` の末尾・`Layers` の末尾の欄 `contact` |
| `src/shibuya/engine/systems/state_io.py` | `hash_owners` の末尾 |
| `src/shibuya/engine/systems/run_end.py` | `calendar_shadow_layer` の直後に `contact_layer` |
| `src/shibuya/engine/systems/build.py` | 設定の指紋(暦 1a の影の直後)・組み立て(申込書の層の後・箱の前)・`Layers(contact=…)` |
| `src/shibuya/engine/run.py` | manifest の末尾(`calendar_shadow` の後)・補助 `_contact_c1_field`・乱数の用途名の表の末尾 3 つ |
| `src/shibuya/engine/rng_audit.py` | `SAFE_SITES` の末尾 2 行・`UNDETERMINED_SITES` に 1 行 |
| `src/shibuya/engine/manifest_sections.py` | `PATHS` の末尾(`calendar_shadow` の後) |
| `src/shibuya/engine/state_ledger.py` | `_EXT` の末尾(M0S の後)に 9 行・`OWNER_CLASSES` の末尾 7 項・`OWNER_ALT_CLASSES` の末尾 2 項・`EXCLUDED` の末尾・O84 の items の末尾 3 つ・版の注(外 129・全体 220) |
| `src/shibuya/engine/events/vocab.py` | 族 `連絡` と 15 語(表の末尾=前の語のコードは不変・65〜79)・網の名 `contact`・版 `events-vocab/6-4` |
| `src/shibuya/perception/renderer.py` | §1 の行 |
| `src/shibuya/cli.py` | `run` のランの種類・引数 `--contact`(`--experiment` の前)・切替口 |
| `docs/design/bridging-ledger.json` | 末尾に 19 行 |
| 凍結の表の試験 | `tests/engine/systems/test_systems_table.py`(並び・tick の系 27)・`writes_soa_frozen.json`(contact は空)・`tests/engine/events/writes_paths_events.json`・`test_e_vocab_is_closed.py`(80 語)・`tests/engine/test_state_ledger_10b.py`(行の数・腕の行・順を保つ行・網羅=ConversationManager の持ち主が 2 つ)・`test_state_checks_10f.py`(`SAFE_SITES` 18・決まらない呼び手 14)・`test_env_and_sections_10f.py`(`CONFIG_PATHS_SHA256`)・語彙の末尾と版を固定していた 5 本(`tests/engine/speech/test_speech_port_schema.py`=語の位置・版・腕の行の一覧・`tests/engine/tools/test_c0_tool_registry.py`=族の並びと網の名の位置・`tests/engine/experiment/test_x33_apply.py`=版・`tests/economy/stage2/test_stage2_account_and_conservation.py`=版と経済の過程の名の位置・`tests/engine/multiday/test_md23_body_events.py`=族の末尾と体の過程の名の位置)・`tests/engine/batching/test_conductor_windows.py`(窓の境目の確かめに腕 c1 の場合を足した=腕 off は前のまま出来事の記録の鍵も落とす) |

触っていない: `perception/facts.py`(Percept の形)・`manifest_keys_frozen.json`・`tick_word_allow.json`・`time_literal_allow.json`・状態のファイルの許可の表・進行役の窓のループ・会話(`conversation.py`)・発話の口・判断の口・道具の台帳。

## 12. 限界・仮採用(10-13b §0-3)・親に確かめてほしいこと

**仮採用**

1. 道具の最初の状態(全員がスマートフォン・電池 100%・マナーモード 0.5・かばん 0.5・イヤホン 0.2)・着信音と置き場の減衰とイヤホンの dB・SNR の段・電池の減り・電波は全域=実データの無い仮の値(`DOC-ct-c1-device-*`)。充電は本人の行動=本段に無い(1 日で 52 体の電源が切れる)。〔第337 注(カレンダー 3=ca3)〕4 日を超える腕のランで全員の電池が 0 になり C3 の連絡が通らないと分かり、家に居る刻みに電池が増えるつなぎ `BR-CT1-CHARGE-AT-HOME`(エンジン規則・conf 宣言つき・外す段 6-6)を入れた=台帳の行 `DOC-ct-c1-no-charging` は removed([ca3 §14](../ca3/README.md))。充電を本人の行動にするのは 6-4 の残り。
2. 通知の音はイヤホンに流さない(イヤホンは周りの音を覆う側)。
3. 周辺視の範囲 2.0 m と人の気配の粗い段。知覚の事実の既存の欄に値を入れる(`mind_dir`=目と心の向き・`tool_state`=道具と通知・`eye_dir` は空のまま)=Percept の形と版は変えない。
4. 割り込み=その刻みに起床条件 (i) で起きた体(驚き駆動の入口の代わり=T3)。通知の門の段(通話と会話は強い刺激だけ)・寝ている体は気づかない・1 体 1 刻みに通知の刺激 1 回。
5. 割り込めなかった出来事の既定の載せ方は (i)。顕著行為の「気づいた体」から外すのは 3 つの腕で同じ(腕が変えるのは描画だけ)。
6. 連絡の判断は主の判断の呼び(行為 12 語)と別の呼び(J0 の型・乱数の用途名 `contact.mock`・`contact.present`)=判断の語彙に道具の語を足さない(`TOOL_ACTION_WORDS` は空のまま)。呼び出し数(`calls_by_model`)にも数えない(manifest の `contact_c1.decisions` に出す)。
7. 候補の語と源の当て方・スタンプ 4 語・定型の文・長さの上限 1,000 字・暇の判断の時・読むと未読を全部読む・後でと無視の違いは記録だけ。
8. 1-3 の欄の約束(received_ns ≥ t)により、`連絡:読んだ` の `received_ns` は読んだ時刻(届いた時刻は原因の入力の `連絡:届いた` の行)。後で/無視/出ないは `received_ns` なし。
9. 電話: 場所の門を見ない(`same_cell=True`)・出ないで拒否の記憶を書かない・番の上限は対面と同じ(1 人 3 番)・呼び出し中も関心の的=通話。出るを選んでも 1 人 1 会話の門で開かなければ `連絡:不通`(関係ありで 17 回)。
10. 宛先: 関係の層の無いランは家族の 1 対 1 とグループだけ・人も記憶の腕は思い浮かぶ人。連絡先の交換は本人の行動=本段に無い。
11. 習慣(CT4)は作らない=いつも判断の口に戻す。
12. 読んだメッセージを持つ長さ 1 日・待ち行列の種類の番号 40/41 と順位 −1/−2・チャットの上限 200 通(安全装置)。
13. 族 `連絡` の 15 語と網の名 `contact`(語彙の版 `events-vocab/6-4`)。
14. 描画: 共有でない場面(目と心の向きの写し)はセルのキャッシュ(B4・セルのブロック)を読まず書かない。実装の途中で、腕 (i) で落とした B4 が同じセルのほかの体の描画に漏れていたのを、腕 (i) と (iii) のテープの差(17 の呼び)と描画の計数(12)の食い違いから見つけて直した(直した後は 12 と 12)。既定のランは場面がいつも共有の物=キャッシュの使い方は前と同じ。

**限界**

- 「記憶に残ったか」は顕著行為についてだけ測る(器 events のランだけ)。通知と連絡の出来事は 1-6 の器に書いていない(器の側の段)。
- メッセージの道具の行(1-7 の台帳)は足していない。
- 判断(mock)は描画を読まない=3 つの腕・周辺視の違いは final と計器に出ない(テープの描画だけ)。判断モデルと LLM の段で比べる。
- 体の反射(3-5 の器)は値が空=反射で顔を上げることは本段で起きない。
- 既読の印は送った側の判断の候補にまだ載せていない(diag)。
- 量とバイト(§5-2)は既定化の条件を満たしていない。

**親に確かめてほしいこと**

1. 共有ファイルの所(§11)。とくに進行役の段 B の窓の境目の許可 `WINDOW_PATHS`(連絡の行と出来事の記録)・描画のキャッシュの条件(`_scene_is_shared`)・系 `contact` がその刻みの顕著行為の事象(`runner.salient.events`=キャッシュ=台帳の外)の「気づいた体」を書き換えること(記憶の系より前・腕のときだけ)。
2. manifest の `manifest_sections` の値と `CONFIG_PATHS_SHA256` が既定のランでも動く。
3. 仮採用 4・5・6(割り込みの代わり・載せ方の既定・別の呼び)。
4. バイトと量(§5-2)=既読を読んだの行に畳むか・保持窓・mock の量。
5. 用語集との照合はしていない(新しい語「視線の先」「関心の的」「周辺視の気配」「打ち終わり」「網が預かる」)。

## 13. 独立検収の直し(条件つき受入=高 1・中 5・低 8 → 全部直した・本体 `32fb262` へ ff)

検収の報告は [review.md](review.md)。直しの後の数はこの節が正(§0〜§12 の数は直す前=記録として残す。既読の行・グループの届いた行・`c1:` の call_id の書き方は §13-1 の M3 で変わった)。

### 13-1. 直しの表

| 欠陥 | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| H1 段 B で宣言の外 220 件 | `systems/table.py`(系 contact の `paths`)・`state_ledger.py`(行 BW の注) | `paths` に `BW:batching.*`(送信と着信の予約=系の中から進行役の待ち行列に書く)を足し、行 BW の注の「書くのは」に腕 c1 の系 contact を足した。判断の系の `paths` に `CT1G:contact._look_main CT1M:contact._meter`(M5 (i) の主の判断の候補)を足した | `test_c1_fixes.py::test_h1_arm_c1_passes_stage_b`(合成 80 体・360 刻み・`SHIBUYA_SYSTEMS_CHECK=1`=宣言の外 0)・`test_h1_negative_control_without_the_bw_declaration_fails`(宣言から BW を外すと落ちる)・`test_m5_look_is_a_main_candidate_and_counts`(腕 port でも段 B を通る) |
| M1 顕著行為のキャッシュの書き手が 2 つ | `contact/attention.py`(`gate_salient`)・`contact/layer.py`(`_salient_gate`・`salient_view`)・`systems/remember.py`・`systems/table.py`(系 memory の reads) | 門の結果は写しで返し、連絡の持ち主の腕の行 `CT1G`(`_sal_noticed`・`_sal_step`)に持つ。`runner.salient.events[].noticed` と `noticed_agents` は書き換えない(効き目の無い `noticed_agents` の書き換えは消した)。記憶の系は宣言した読み口 `ContactLayer.salient_view`(系 memory の reads に `layers.contact`)から読む。その刻みに門を通していなければ `RuntimeError`=順は依存で守る。既定のラン(層なし)は今のまま | `test_m1_gate_is_kept_on_the_contact_side`・`test_c1_units.py::test_gate_salient_removes_only_focused_and_not_interrupted` |
| M2 監査が原因の型しか見ない | `contact/layer.py`(`_issue`・`issued_keys`・`audit_causes(…, issued=)`・`WORD_PURPOSES`) | 層は発行した判断の呼びを控える(腕の行 `CT1Q`=刻み・体・通し番号を 8 B の整数に詰める)。監査は、原因の call_id がこの控えにあり・体が出来事の体と同じで・判断の種類が語に合う(`WORD_PURPOSES`)かも突き合わせる。AST の試験は、本人の語の行の原因が `self._decide` の答えだけ(送った=予約の行・主の判断の候補・通話の終わりの 3 つの作り直しだけ認める)で、`read_ns` を本人の読んだ・出た以外の行に書かないことを見る | `test_m2_a_forged_llm_call_is_caught_by_the_issued_check`(偽の LlmCall を植える=型だけの監査は 0・控えとの突き合わせは >0)・`test_m2_ast_person_events_come_only_from_decisions`・`test_m2_ast_negative_control_catches_a_planted_rule`(植えた規則 3 件を見つける)・`test_c1_units.py::test_audit_catches_engine_decided_reads_and_sends`(偽の呼び・ほかの体・種類の食い違いの 3 件) |
| M3 量の見積もり | `contact/layer.py`(`_send_now`・`_read`)・`contact/port.py`(call_id)・`events/vocab.py` | 畳み方を入れた: ① グループの「届いた」は「送った」の 1 行に(届いた箱の行の目印=送った行・電源の切れた相手だけ例外の行 `連絡:預かった`)② 既読の行を書かない(送った側の既読は `連絡:読んだ` の whom から作る=語「既読」の位置を「預かった」に替えた・語の数とコードは不変)③ 読んだは会話ごとに 1 行(`how_much`=通数)④ call_id はテープの形 `刻み:体:−通し番号`(文字列の表 0 本)。それでも既定にできない=つなぎの台帳 `DOC-ct-c1-not-default` に宣言 | `test_c1_flow.py`(読んだは 1 行・既読の行なし・グループの届いた行なし)・§13-3 の測り |
| M4 描画の関心の的が 1 刻み古い | `contact/layer.py`(`run_step`) | 関心の的を刻みの**終わり**(判断・チャットと通話の 1 刻みの後)に置き直す=次の刻みの描画(`percept_hook`)・次の刻みの周りの出来事の門・通知の門が、どれも「前の刻みの判断の後の値」を読む(描画と記憶の門が同じ写し=宣言) | `test_m4_focus_is_the_value_after_the_decisions`・`test_c1_flow.py::test_notice_gate_by_strength_and_focus` |
| M5 呼び数が仲裁と予算の外 | `decision/layer.py`(`contact_offer`)・`contact/layer.py`(`offer_main`・`take_main`・`model_calls`・仲裁)・`run.py`/`systems/state_io.py`(`calls_by_model`)・`contact/port.py`(`ARBITRATION`) | (i) 判断の口の腕(`--decision-port port`)のランでは「スマホを見る」を主の判断の候補(源=できること・よく考えるの前)に足し、選んだら同じ刻みに画面を見る(行為のコードは今の道のまま=語彙の外)。このランは別の暇の判断をしない。腕 legacy のランは主の判断が候補を出さないので別の呼びで代える(`DOC-ct-c1-legacy-idle`)。(ii) 連絡の判断(判断モデル)と文の口(LLM)を manifest と日次の記録の `calls_by_model` に足し、内訳を `contact` に出す(既定のランは今のまま)。(iii) 仲裁=主の判断が先(その刻みに主の判断の呼びのあった体は連絡の判断をしない・通知と暇は次の刻みへ・画面・着信・呼び出し・通話の番は次の刻みにまた起きる)を `port.ARBITRATION` に宣言 | `test_m5_look_is_a_main_candidate_and_counts`・`test_m5_calls_by_model_is_unchanged_without_the_arm`・`test_m5_arbitration_main_decision_first` |
| L1 チャットの遷移の二重 | `contact/chat_state.py` | `ChatBook` を `ConversationManager` の子にした(締め・終わり・参加の沈黙・掃除・理由の数えは会話の器のコード)。違いは 3 つだけ(1 人が同時に幾つものチャット=`_of_agent` を使わない・返事の無い招待の沈黙はここで締める・話題の数で締めない)。状態台帳の行 CT1C は会話の器の 9 属性+`_of_key` | `test_c1_units.py` のチャットの 2 つ・網羅の試験(会話の器の持ち主が 3 つ) |
| L2 限界の書き漏れ | 記録 | §13-5 に書いた | — |
| L3 動く欄の書き漏れ | 記録 | §13-4 に書いた | — |
| L4 引数の名 `tick` | `contact/book.py` | `step` に変えた | 既存の試験 |
| L5 普通の dict・番号がぶつかる | `contact/port.py`・`contact/layer.py` | `PURPOSES`・`_SOURCE_OF`・`ARBITRATION`・`WORD_PURPOSES` を `MappingProxyType` に。通し番号=k × 16+種類(k < `MAX_DECISIONS_PER_STEP`=16,384・超えたら `ValueError`)。`wake_class` の欄は使わない(−1・乱数の鍵は call_id の通し番号) | `test_decision_serials_do_not_collide_and_have_a_limit`・`test_contact_ctx_does_not_use_the_wake_class_field` |
| L6 `_bc/`・`SWITCH_ENV` | — | `_bc/` は触っていない(親が消す・今回の生の出力は `_bc2/`)。10e の `SWITCH_ENV` に足す名(親が本体で): `SHIBUYA_CONTACT`・`SHIBUYA_CONTACT_UNNOTICED`・`SHIBUYA_CONTACT_SEND` | — |
| L7 docstring の数字 | `contact/attention.py` | 数字を消し「掛けない」と決定の ID だけにした | — |
| L8 通話中の再開の試験が無い | `tests/engine/contact/test_c1_fixes.py` | 仮のモデルの規則を差し替えて通話を起こし(合成 80 体・関係 off)、通話の続いている刻み 97 で止めて再開=通し | `test_l8_resume_in_the_middle_of_a_call_is_the_straight_run` |

### 13-2. 段 B(腕 c1)

- 合成 80 体・360 刻み・グループの一覧あり・`SHIBUYA_SYSTEMS_CHECK=1`: **宣言の外 0**(検収の前は 220 件=`BW:batching._bw_meter` 110・`_bw_sched` 110)。宣言から `BW:batching.*` を外すと `AssertionError`(負の対照)。
- 腕 port(主の判断の候補・選びを「スマホを見る」に寄せた合成 80 体・720 刻み)も段 B を通る(判断の系が書く `CT1G:contact._look_main` と `CT1M:contact._meter` は宣言の内)。

### 13-3. 測り直し(mock 5,000 体・1 日・世界 v2・seed 1・載せ方 i・送る文 b)

| 計器 | 直す前(§5) | 直した後 |
|---|---|---|
| final(腕 c1・判断の口 legacy) | `58f9d4d7942c29de` | `dfd2a11ac54cf94c`(仲裁と畳み方と関心の的の時刻で動く=腕の数) |
| 連絡の出来事の行 | 1,120,765 | **155,148**(−86%)=送った 44,356・届いた 2(1 対 1)・預かった 2,099・読んだ 35,568(会話ごと)・後で 18,444・無視 17,953・スマホを見た 9,255・顔を上げた 27,471 |
| via グループ / メッセージ / 無し | 1,085,407 / 5 / 35,350 | 118,416 / 6 / 36,726 |
| 監査(発行した呼びとの突き合わせつき) | 0(型だけ) | **0**(控え 240,128 件) |
| 判断の呼び(連絡) | 225,025 | 240,128(仲裁で次の刻みに回した 10,096 を含む) |
| `calls_by_model` | `{"judge_model": 0, "llm": 64,528}` | `{"judge_model": 240,128, "llm": 97,010, "contact": {"judge_model": 240,128, "llm": 32,482}}`(主の判断の呼び 64,528 の 3.7 倍が判断モデル・文の口 32,482 が LLM) |
| 届いた(体×通)/ 読んだ通数 | 396,125 / 307,399 | 432,159 / 335,986 |
| 読むまで[分] 中央 / 90% / 99% | 2 / 130 / 617 | 2 / 139 / 637 |
| 顕著行為 気づいた / 門で外した | 181 / 1 | 181 / 0(関心の的を判断の後の値にした時刻の違いによる=推測) |
| 窓の境目の事象 / 遅れの最大 | 40,818 / 60 秒 | 44,376 / 60 秒 |
| 日の途中(T=720)の再開 | 通し | **通し**(final `dfd2a11ac54cf94c`・T=1079 と 1439 の checkpoint の 2 つのハッシュが同じ) |
| 腕 port(「スマホを見る」は主の判断の候補) | — | final `9095f0152a52f7ab`・候補に出した 7,963 回・**選んだ 0 回**(主の仮のモデル `MockPort.pick` は語彙の語だけを選ぶ)=誰もスマホを見ないので連絡の出来事 0・連絡の判断の呼び 0。判断モデル/LLM の段で選ばれる形(構造だけを入れた) |

バイト(出来事の記録の器=`EventLog.nbytes`+`cause_nbytes`+テープの形でない call_id の文字列。既定 off のランとの差を連絡の分とする):

| | 既定 off | 腕 c1(直した後) | 連絡の分 |
|---|---|---|---|
| 行 | 53,682 行・3.87 MB | 208,830 行・15.04 MB | 155,148 行・11.17 MB |
| 原因の表 | 9,480 行・0.37 MB | 162,527 行・17.07 MB | 153,047 行・16.70 MB(入力の出来事 id が大半=読む判断の原因に未読の目印を全部載せる) |
| call_id の文字列 | 0 | 0 | 0 |
| 計 | 4.23 MB | 32.10 MB | **27.87 MB/日**(検収の見積もり 約 105 MB/日の 27%) |

- 39 万体への線形の外挿(推測): 約 2.17 GB/日・保持窓 7 日で約 15.2 GB=1-3 の宣言(S1 256 MB)を超える=**腕 c1 は既定にできない**(つなぎの台帳 `DOC-ct-c1-not-default`)。
- 残りの差を埋める案(親がユーザーの判断に出す・ここでは並べるだけ): (a) 保持窓を短くする(1-3 の宣言の側)(b) 原因の入力の出来事 id を「未読の最初と最後の目印」だけにする(原因の表の大半)(c) mock の量を決める(画面を見ている体は毎刻み判断する=判断の呼び 95,722/日が画面)(d) 予算 S1 を引き上げる(e) グループの送った行も会話ごとに畳む。
- 壁時計(参考・ほかの作業木のランと並んだ機械): 既定 off 139.3 秒・c1 184.6 秒・port 134.4 秒(1 日・5,000 体)。

### 13-4. 既定のランで動く欄(L3)と結果不変

- 既定のランでも動く欄(どれも byte-check の 25 欄の外): `manifest_sections`(節の表=`contact_c1` と子)・`bridges_count`(つなぎの台帳に足した 24 行の分=検収の測りでは 456 → 475・直しで +5)・`bridges_version`(台帳の sha)・日次の記録の `bridges_count`。`calls_by_model` は既定のランでは今のまま(`test_m5_calls_by_model_is_unchanged_without_the_arm`)。
- byte-check 4 構成(既定 off・本体 `32fb262` の写し=`git archive`+`HEAD_TREE_FILES`+data へのつなぎ=回した後に .NET で外した・scratch `_bc2`)× 25 欄: **4/4 構成で 25 欄とも同じ**(既定 v3 `b8eadcb51e8705e7`・活動 off `c88ba9104f45f897`・v1 `e1288e092ddaca86`・記憶+関係 `768b2262e3b0999e`・両側の `env` 空)=[byte_check_ct_c1_fix_4cfg.json](byte_check_ct_c1_fix_4cfg.json)。
- rebase: `git merge --ff-only build/spatial-d102-prep`=`4f186fb` → `32fb262`(記録と文書の commit だけ・src の差は無い・作業木の変更と重なるファイルは無い)。

### 13-5. 限界(L2 ほか)

- CT0 の「歩き方は先を見る範囲から物理」(画面を見ながら歩く体の歩き方)は使っていない(歩く速さ・ぶつかり方は今のまま=空間の段 3 で)。
- CT5 の「店や組織の番号は場所の表」は使っていない(宛先は個人の連絡先とグループだけ=店や組織への電話は無い)。
- 腕 port では主の仮のモデルが「スマホを見る」を選ばない=画面を見る体が 0(§13-3)。腕 legacy の別の呼びは代わり(`DOC-ct-c1-legacy-idle`)。
- 仲裁の規則の置き場: 発注の「規則の表」は `docs/design/rules-table.json`(法令の規則の表=出典の法令が要る形)と読み、エンジンの順の決まりは載せずに `engine/contact/port.py` の `ARBITRATION`・つなぎの台帳 `DOC-ct-c1-arbitration`・この記録に宣言した(親に確かめてほしい)。
- 6-1 の表(GPU 時間の式)に連絡の呼び数を足す: 判断モデル 240,128 回/日・LLM(文の口)32,482 回/日(5,000 体・mock の量)を 6-1 の表に足すこと(この段では文書を触らない)。
- 監査の控え `CT1Q` はランの間ずっと持つ(5,000 体 1 日 約 1.9 MB)=既定化の前に日ごとの監査で捨てる形へ(`DOC-ct-c1-issued-registry`)。

### 13-5b. 直しで増えた共有ファイル

- `src/shibuya/engine/decision/layer.py`: 欄 `contact_offer`(既定 None)と `decide_one` の 2 か所(候補を足す・選んだ体を渡す=腕 c1+腕 port のランだけ)。
- `src/shibuya/engine/systems/remember.py`: 補助 `_salient_for_memory`(層の無いランは今のまま)。
- `src/shibuya/engine/systems/table.py`: 系 contact の `paths`(+`BW:batching.*`)・系 decide の `paths`(+`CT1G:contact._look_main CT1M:contact._meter`)・系 memory の `reads`(+`layers.contact`)。
- `src/shibuya/engine/systems/build.py`: 判断の口の層に連絡の層を結ぶ 3 行。
- `src/shibuya/engine/run.py`・`systems/state_io.py`: `calls_by_model`(補助 `_calls_by_model`=層の無いランは今の値)。
- `src/shibuya/engine/state_ledger.py`: 腕の行 CT1G・CT1Q(外 131・全体 222)・CT1C の中身・CT1M にチャットの計数・持ち主 `contact.chats` の型・除外 3 つ・行 BW の注。
- `src/shibuya/engine/events/vocab.py`: 語「既読」の位置を「預かった」に(語の数とコードは不変)。
- `docs/design/bridging-ledger.json`: +5 行(`DOC-ct-c1-arbitration`・`-legacy-idle`・`-fold-records`・`-not-default`・`-issued-registry`=491 行)・`DOC-ct-c1-separate-call` の文。
- 試験: `tests/engine/contact/test_c1_fixes.py`(新)・`test_c1_units.py`・`test_c1_flow.py`・`test_c1_runs.py`・`test_c1_world.py`・`tests/engine/test_state_ledger_10b.py`・`tests/engine/speech/test_speech_port_schema.py`。

### 13-6. 試験の件数(直した後)

- 範囲(発注の一覧+系の表・窓・語彙を固定した 3 本・`-n 2 --dist loadfile -m "not slow"`): **1,434 passed・1 skipped**(Ruri)。
- `tests/engine/contact/test_c1_fixes.py`: 12 passed(段 B 2・M1・M2 3・M4・M5 3・L8・L5)。
- slow(`test_c1_world.py`・5,000 体・1 プロセスで順に): 6 passed。
- lint-imports: 5 kept・0 broken。

## 14. TM の commit `80742bc` への rebase(控え+早送り+merge-file)

- 変えた追跡ファイル 29 本を控え(`_bc2/`)・32fb262 に戻して `git merge --ff-only 80742bc`・ファイルごとに `git merge-file`(控え/32fb262/80742bc)。衝突は 17 本。解き方は「本体の分 → 本段の分」の順に並べた(manifest の末尾・乱数の用途名・持ち主の名・箱の欄・指紋・状態台帳の行と持ち主と除外・CLI の引数)。手で合わせた所: 進行役の窓の境目(`WINDOW_MARK_KEYS` または腕 c1 の `WINDOW_PATHS`)・系 decide の `paths`(本体の `BW:batching.* T4W:clock.*` の後に `CT1G:contact._look_main CT1M:contact._meter`)・`close_final` の reads・日次の記録の `calls_by_model` と `clock_kind`・manifest の `calls_by_model` と `clock_kind`・行 BW の注・ランの種類の腕の数え方。つなぎの台帳は本体の JSON(522 行)に本段の 24 行を末尾に足し直した(546 行・既存の行は不変)。
- `CONFIG_PATHS_SHA256`: `ffbed6e3…`(本体)→ `c8d7f1d4…`(本段の設定の子 15 本を足した=外すと本体の値)。状態台帳の数: 外 126・全体 217(本体)→ 外 137・全体 228(CT1* の 11 行)。`SAFE_SITES` 18 → 20・決まらない呼び手 13 → 14。
- 試験(`tests/engine tests/perception tests/economy/cp2 tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`): 3,590 passed・1 skipped・2 failed。落ちた 2 本はどちらも本段と関係ない: `tests/engine/test_classical_social.py::test_run_golden_and_arms` は同じ工程で先に `tests/engine/multiday/test_md23_resume.py` が走ると落ちる(80742bc の src だけでも同じく落ちる=試験の間の状態の漏れ)・`tests/tools/test_realworld_fetch_logrotate.py` は時刻に依る揺れ(80742bc の src でも単独で落ちたり通ったりする)。lint-imports 0 broken。
- 既定 1 構成の byte-check(`80742bc` の写し vs 作業木・`w6_v3_default`): 25 欄とも同じ(final `b8eadcb51e8705e7`)=[byte_check_ct_c1_rebase_80742bc_1cfg.json](byte_check_ct_c1_rebase_80742bc_1cfg.json)。腕 c1 の段 B(合成 80 体・360 刻み)は宣言の外 0(範囲の試験の `test_c1_fixes.py`)。腕 c1 の 5,000 体 1 日: final `dfd2a11ac54cf94c`=rebase の前と同じ(checkpoint・連絡の出来事 155,148 行・監査 0・`calls_by_model` も同じ)。

## 15. 本体の先端 `bac5514`(賃金の段ほか)への載せ替え

- 手順は §14 と同じ(控え → `80742bc` に戻す → `git merge --ff-only bac5514` → ファイルごとに `git merge-file`(控え/80742bc/bac5514))。衝突は 4 本: つなぎの台帳(本体の 526 行の末尾に本段の 24 行を足し直した=550 行・既存の行は不変)・`rng_audit.py`(`SAFE_SITES`=本体の賃金の分位の後ろに本段の 2 つ)・`run.py`(母集団の側の乱数の用途名=本体の `economy.wage` の後ろに `contact.device`)・`tests/engine/test_state_checks_10f.py`(数え直し)。`cli.py`・`state_ledger.py` は自動で合わさった。
- `CONFIG_PATHS_SHA256`: 本体の値は `ffbed6e3…` のまま=作業木は `c8d7f1d4…` のまま(本段の 15 本を外すと本体の値)。状態台帳は外 137・全体 228 のまま(本体は 126・217 で変わらず)。`SAFE_SITES` 19(本体)→ 21・決まらない呼び手 13 → 14。
- 試験(`tests/engine tests/perception tests/economy/cp2 tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`): **3,593 passed・1 skipped・失敗 0**(腕 c1 の段 B の試験を含む)。lint-imports 0 broken。
- 既定 1 構成の byte-check(`bac5514` の写し vs 作業木・`w6_v3_default`): 25 欄とも同じ(final `b8eadcb51e8705e7`)=[byte_check_ct_c1_rebase_bac5514_1cfg.json](byte_check_ct_c1_rebase_bac5514_1cfg.json)。腕 c1 の 5,000 体 1 日: final `dfd2a11ac54cf94c`=前と同じ。

## §親の検収(第337・Fable 5.1・rebase の後)

- 本体 068edf2 へ rebase(賃金の版上げの入った bac5514 への載せ替えは実装役が控え+早送り+merge-file で(衝突 4 本=台帳 526+24=550 行・SAFE_SITES 19 → 21・run.py の用途名・10f の数=§15)・親 commit 1a46f82・文書だけの 068edf2 へは衝突なし)→ 233b1ed。範囲の試験(`tests/engine` 全体・perception・cp2・c8・tools)**3,593 passed・1 skipped・0 failed(`-n 4 --dist loadfile -m "not slow"`・23 分 55 秒)**。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・既定 off)=**final 同じ・25 欄とも差なし**(`parent_head_vs_ct_c1_4cfg.json`)。実装役の 19 構成の JSON は検収役が全欄を照合(既定のランで動く欄は `manifest_sections`・`bridges_count`・`bridges_version`=25 欄の外=宣言)。
- **data 無しの写し(detached の作業木・junction なし)で CI-1 と同じ引数の全体試験(tests/c7 を含む)=**5,535 passed・286 skipped・failed 0**(1,616 秒・CI の印=`-m "not gpu and not slow" -n 2 --dist loadfile`・233b1ed)**。
- 独立検収([review.md](review.md))=条件つき受入(高 1=系 contact が窓の待ち行列に書くのに宣言が無く腕 c1 の段 B で宣言の外 220 件/ 中 5=顕著行為のキャッシュの書き手が 2 つ・監査が原因の型しか見ない・量の見積り(約 105 MB/日・39 万体 8.2 GB/日)・関心の的が 1 刻み古い・連絡の判断 22.5 万回/日が仲裁と予算の外/ 低 8)→ 全部直した(§13)。検収役の独立の再計算(final・行数・via の内訳・送った/届いた/読んだ・自前の監査 0・着信の遅れ=境目・刺激の段 48 通りの dB・行のバイト 80.7 MB・日の途中の再開 3 本)は全部一致。親の判断: 門の結果は contact の側に・監査は発行した呼びの控えとの突き合わせ+AST・畳み方 4 つを今入れて測り直し(27.9 MB/日・39 万体 2.17 GB/日=1-3 の宣言を超える=既定にできない宣言・残りは §1-1)・関心の的は刻みの終わりの値・「スマホを見る」は主の判断の候補(mock は選ばない=構造だけ)・連絡の判断は別の呼びのまま `calls_by_model` と予算に数える・仲裁は `port.ARBITRATION` と台帳(規則の表は法令の表)・CT1Q(1.9 MB/日)は既定化の前に日ごとに捨てる。
- 判定: **受入**(第 6 期 6-4 C1 の仕組み=腕・既定 off は不変・既定にできない=記録の予算の判断待ち)。

## 16. 記録の有無で腕 c1 の結果が変わる欠陥の直し(口の約束 1-3 の (1)・カレンダー 2 の検収 M3 と同じ形)

カレンダー 2 の独立検収 M3([ca2 review.md](../ca2/review.md))で見つかった形が C1 にもあった。出来事の記録の id(`(t_ns, seq)`)が behavior の行に入っていたので、記録 on/off で checkpoint の behavior-hash(合成 80 体では刻み 59 から)と final が違った。直し方は [ca2 §14](../ca2/README.md) の M3 と同じで、出来事の id を diag の別の表に移した。土台は本体の先端 `6f07eff`(W21 の世界)。

### 16-1. 移した欄

| 行(behavior) | 欄 | 前 | 後 |
|---|---|---|---|
| CT1I `contact.mail._inbox` | 届いた行の 10・11 番目(届いた出来事の目印=1 対 1 は `連絡:届いた`・グループは畳んだ `連絡:送った` の行) | 記録 on のときだけ行に足した(行の長さ 11)・off は 9 | 行は 9 欄だけ。目印は層の診断の表 `contact._ct_event_of`(体 → 未読の届いた行の `[番号, t_ns, seq]`・届いた順・読んだら落とす) |
| CT1S `contact.speech.inbox` | 未読の発話の目印(通話の番の発話) | 記録 on は記録の id・off は口の通し番号(値が違う) | いつも口の通し番号 `(t_ns, 通し番号)`(記録に依らない)。記録の id は診断の表 `contact.speech._mark_event_of`(口の目印 → 記録の id・未読の列から出たら落とす=有界)。直しは親のクラス `SpeechPort` に入れた(§16-6) |

- ほかの behavior の行(CT1D・CT1A・CT1C・CT1K・CT1G)は出来事の id を持たない(洗い出した。CT1G の `_look_main` は call_id と番号・`_exposed_prev` は CT1M=diag)。
- 2 つの表は腕の行 **CT1Q(diag・required)** の items に足した(CA2M と同じ軸=再開したランの原因の入力が通しと同じ)。行の数は変えていない(外 142・全体 233 のまま)。CT1I・CT1S の注に直しを書いた。
- 読み手は読む判断(`_unread_basis`=未読の行の番号で表を絞る)と通話の番の判断(`SpeechPort.event_ids`)の原因の入力(`LlmCall` の入力の出来事 id=原因の表)だけ。仮のモデルは候補の `basis` を読まない。監査 `audit_causes` は記録の原因を見る=変えていない。
- 名前: 発話の口の表は `_event_of` だと `engine/events/links.py` の `ActualLogLink._event_of` と名前がぶつかる(10f の軸 1 の AST 検査)。最初は `_call_event_of` にし、§16-6 で親のクラスへ移したときに `_mark_event_of` に替えた。
- 置き換えの口(最初の形・§16-6 で消した): `CallSpeechPort.say` が親の口を呼んだ後に積んだ行の目印を置き換えていた(`_write` の上書きは権利台帳の AST 検査 `test_nothing_outside_touches_the_ledger` が `super()._write` を「他の物の _write」と数える)。いまは `CallSpeechPort` は腕の名と口の名だけの子に戻した。
- 消したもの: `Mailbox.note_delivery_event`(行に目印を足す口)。
- 通し番号の控え `contact.speech._own_last` は CT1M(捨ててよい)のまま(口の欄は付け替えられない=状態のファイルから戻す口が無い)。未読の列の目印を決めるのは刻みの中だけで、再開は刻みの境目=次の発話は新しい時刻=通し番号 0 から=通しと同じ(L8 の通話中の再開の試験・§16-3 の再開の試験で確かめた)。

### 16-2. 記録 on/off の一致

- 合成 80 体・720 刻み・腕 c1(記憶・関係あり=メッセージとグループの道): 直す前は記録 on/off で final が違い、checkpoint の behavior-hash が刻み 59 から全部違った。直した後は final(`2d1c187d…`=直す前の記録 off と同じ)と checkpoint 12 個が同じ。
- 合成 80 体・240 刻み・通話を起こす仮のモデル(L8 と同じ形・関係 off): 記録 on/off で final・checkpoint・通話の未読の列が同じ。
- 記録 on の出来事の記録(原因と入力の出来事 id を含む全部の行)は直す前と同じ: 合成のメッセージの道 4,323 行・通話の道 453 行とも全部の行のハッシュが `6f07eff` の写しと一致(scratch の確かめ・`_bc/probe_eventlog.py`)。
- **5,000 体・1 日**(腕 c1・mock・seed 1・W21 の世界・[c1_5000_onoff_fix.json](c1_5000_onoff_fix.json)・道具 [tools/run_c1_onoff.py](tools/run_c1_onoff.py)・1 本ずつ):

| ラン | final | checkpoint の behavior-hash(4 個) | 連絡の出来事の行 | 監査の食い違い | 届いた行の長さ |
|---|---|---|---|---|---|
| 直す前・記録 on | `567b69385e7b742a` | 記録 off と刻み 359 から違う | 95,879 | 0 | 11 |
| 直す前・記録 off | `b4bdb1545f28446b` | — | 0 | 0 | 9 |
| 直した後・記録 on | `b4bdb1545f28446b` | **記録 off と 4 個とも同じ** | 95,879 | 0(控え 154,570 件) | 9 |
| 直した後・記録 off | `b4bdb1545f28446b` | 直す前の記録 off とも同じ | 0 | 0 | 9 |

- 腕 c1 の final の新旧: 記録 on のラン `567b69385e7b742a` → `b4bdb1545f28446b`(行の中身が減るため=腕の数)。記録 off のランは新旧で同じ(`b4bdb154…`)。計器(manifest の `contact_c1.meter` から記録の側の数 `events:*` を除いた全部)は 4 本とも同じ・連絡の出来事の行の数と語ごとの内訳は記録 on の 2 本で同じ。
- 終わりの診断の表: 届いた行の目印 57,815 個(未読の行の数ぶん)・通話の目印 0 個(この構成は関係の層が無い=電話の宛先が無い)。
- 壁時計(参考・ほかの試験と並んだ機械): 直した後 on 85.1 秒・off 75.7 秒/直す前 on 86.4 秒・off 78.6 秒。

### 16-3. 試験

`tests/engine/contact/test_c1_event_log_onoff.py`(新・5 本):

- `test_event_log_on_off_does_not_change_the_c1_arm_run`: 合成 80 体+腕 c1・記録 on/off で final と checkpoint の behavior-hash が同じ・届いた箱が同じ(9 欄)・表は on だけ・読んだ行の原因の入力が記録にある届いた/送った行を指す・監査 0。
- `…_with_calls`: 通話を起こす合成のランで同じ・通話の未読の列が同じ・番の発話の原因の入力が記録の発話の行を指す・監査 0。
- `test_resume_restores_the_event_id_tables`: 刻み 97(通話中)で止めて再開=通しと final が同じ・再開した後の連絡と発話の行と原因(入力の出来事 id を含む)が通しと同じ。
- `test_call_speech_inbox_holds_only_log_independent_marks`: 通話の発話の口の単体(記録 on/off で未読の列が同じ・渡した分は表から落ち・引いたら控えも落ちる=§16-6 の形)。
- `test_negative_control_eid_in_the_behavior_row_breaks_the_on_off_equality`: 届いた行に出来事の id を戻す(直す前の形)と記録 on/off で behavior-hash が違う。

直した既存の試験: `test_c1_flow.py::test_group_message_and_chat_state`(届いた行の 10・11 番目を読んでいた → 行は 9 欄・目印は表か読んだ行の原因の入力)・`test_c1_runs.py::test_arm_rows_enter_the_hashes_only_when_the_owner_exists`(CT1Q の軸と items・behavior の行に表が無い)。

件数: §16-5。

### 16-4. 既定 off の 4 構成(1 バイト不変)

本体 `6f07eff` の写し(`git archive`+`HEAD_TREE_FILES`+data へのつなぎ=回した後に .NET で外した・`tree_missing` 空)vs 作業木・W21 の世界: `w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` で **4/4 構成 × 25 欄 同じ**(final `eb759bb4e5be37ec`/63,572・`b75cfc27c763f279`・`7be9d5083bdad119`・`d0623491c47e5e2f`・両側の `env` 空)=[byte_check_ct_c1_onoff_fix_4cfg.json](byte_check_ct_c1_onoff_fix_4cfg.json)。

### 16-5. 試験の件数・触った共有ファイル

- 範囲(`tests/engine tests/perception tests/economy/cp2 tests/c8 tests/tools`・`-m "not slow"`・`-n 2 --dist loadfile`・最後のコード): **3,665 passed・0 failed・0 errors・1 skipped**(49 分 37 秒)。段 B(`test_c1_fixes.py` の H1=合成 80 体・`SHIBUYA_SYSTEMS_CHECK=1`)は宣言の外 0。その前の 1 回は 1 failed(`tests/engine/rights/test_rights_schema.py::test_nothing_outside_touches_the_ledger`=`_write` の上書きの `super()._write`)→ `say` の上書きに直した(§16-1)。
- `tests/engine/contact`(slow の `test_c1_world.py`=5,000 体を含む)+`tests/engine/speech`+`tests/engine/test_state_ledger_10b.py`(最後のコード): **265 passed・0 failed・0 errors**。
- lint-imports: 5 kept・0 broken。秘密の検査(変えたファイル全部): CLEAN。
- 腕 c1 の 5,000 体の 2 本(記録 on/off)は最後のコードで回し直した(final・checkpoint・計器が前の 2 本と同じ)。既定 off の 4 構成は最後の直し(`say` の上書き)の前に回した=その直しは腕 c1 の通話の口の中だけ(既定 off のランは連絡の層を作らない)。

触った共有ファイル: `src/shibuya/engine/state_ledger.py`(自分の行 CT1I・CT1S の注と CT1Q の名・型・items・注だけ=行の数と並びは不変)。ほか(腕の中): `engine/contact/layer.py`・`deliver.py`・`calls.py`。試験: `tests/engine/contact/test_c1_event_log_onoff.py`(新)・`test_c1_flow.py`・`test_c1_runs.py`。記録: 本節・[c1_5000_onoff_fix.json](c1_5000_onoff_fix.json)・[byte_check_ct_c1_onoff_fix_4cfg.json](byte_check_ct_c1_onoff_fix_4cfg.json)・[tools/run_c1_onoff.py](tools/run_c1_onoff.py)。つなぎの台帳・manifest の鍵・設定の指紋・`CONFIG_PATHS` は変えていない。

### 16-6. 発話の口(行 S8)の同じ形も直した(親の判断=問い 3)

- 直しは親のクラス `engine/speech/port.py` の `SpeechPort` に入れた=腕 `--speech-port on` の口(行 S8)と通話の口 `CallSpeechPort`(行 CT1S)が同じコードを通る。記録は [s8b/README.md](../s8b/README.md) §18。
- C1 の側で変わったこと: 表の名 `contact.speech._call_event_of` → `contact.speech._mark_event_of`(行 CT1Q)・渡した発話の控え `contact.speech._heard_taken`(行 CT1M=捨ててよい)・`CallSpeechPort` の `say`・`event_ids`・`prune_events` の上書きを消した・層の `_calls_turns` は `speech.event_ids(体, 目印)`・日の頭の掃除を消した(未読の列から出た目印はその場で表から落ちる)。
- 腕 c1 の 5,000 体 1 日(最後のコード・記録 on/off): s8b §18 の表の C1 の行。合成の試験(`test_c1_event_log_onoff.py` の 5 本)は最後のコードで通る。
- 試験の件数と触った共有ファイル(最後のコード=§16 と s8b §18 の両方): s8b §18-5(範囲 3,670 passed・0 failed・0 errors・slow 6 passed)。§16-5 の「行の数は不変」は §16-6 の後は変わった(行 S8E を足した=外 143・全体 234)・系の表 `systems/table.py` も触った。

### §親の検収(小さな整理=C1/S8 の行の出来事の id を diag へ・第337・Fable 5.1)

- 本体 34c69b7 へ rebase(衝突=`test_state_ledger_10b.py` の注と数=4-2 の TXD の後なので 144・235 に親が合わせた)→ f483f98(文書だけの df0ce45 へは衝突なし)。範囲の試験(`tests/engine` 全体・perception・build_pop・economy・c6・c8・tools)**4,232 passed・1 skipped・0 failed・0 errors**(`-n 4`・26 分 20 秒)。`test_state_ledger_10b.py`+`test_state_checks_10f.py` 98 passed。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・W21 の世界・既定 off)=**final 同じ・25 欄とも差なし**(`parent_head_vs_c1fix_4cfg.json`=1 バイト不変)。実装役の 4 構成も同じ。
- **data 無しの写しで CI-1 と同じ引数の全体試験(tests/c7 を含む)=5,675 passed・290 skipped・failed 0・errors 0**(1,820 秒・f483f98)。
- 親の判断: 新しい行は作らず CT1Q(diag・required)に足す形(問い 1)と `_mark_event_of`(問い 2)は受入。S8(発話の口)の同じ形も同じ作業木で直した(行 S8E=diag・required・外 142 → 143)。口の通し番号の控え `_own_last` は S8M(捨ててよい)のまま=刻みの中でだけ効き再開は刻みの境目(宣言)。記録 on/off の一致は実装役が合成と 5,000 体で確かめ、記録 on の出来事の記録は直す前とハッシュ一致。
- 判定: **受入**(整理=既定 off は 1 バイト不変・腕 c1/speech-port は記録 on のランの final だけ動く=行の中身が減るため)。
