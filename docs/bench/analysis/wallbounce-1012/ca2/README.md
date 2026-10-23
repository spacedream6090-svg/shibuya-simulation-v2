# 第 6 期 6-2 カレンダー 2「会話とメッセージから生まれる予定」(腕 `--calendar-2 arm`)の記録

- 実装役 Opus 5.5。作業木の枝 `6-2/calendar-2-arm`(土台 `2809c4a`)。commit は親。
- 正: [決定 10-12](../../../../design/v2-wallbounce-decisions-2026-10-12.md) §4-1(CA2 (c)(d)・CA3・CA4 (d)・CA6 (b)・CA7・CA8・
  CA9・CA11)・§4-4 CT0(使用は全部出来事の記録へ)・CT1(C1 の口)・§4-2 TM3(会話)・§4-6(MR-0・MR1・MR4・MR8)・§2 の 1(人の手続きは
  コードに書かず住人の知識から)・[計画](../../../../design/v2-implementation-plan-2026-10-12.md) 6-2 の行・回答 2-1(第 6 期のコードを
  GPU の前に腕で)・[口の約束](../../../../design/v2-foundation-contracts-2026-10-13.md) 1-3・1-6・1-8・10-13b §0-3(仮採用の形)。
  土台の記録: [ca1b](../ca1b/README.md)(腕の形・出入りの判断を本人へ)・[ct_c1](../ct_c1/README.md)(連絡の層・J0 型の口・監査・
  既定 off の守り方)。
- **全部 腕**(既定 off=層を作らない=今のまま)。検証の錨の値は読んでいないし使っていない(統計は検証にだけ=CA2 (d))。
- 数は実測。生の出力(状態のファイル・テープ・JSON)は作業木の `_bc/`(git の外)。このフォルダには比べた結果と道具だけを置く
  (絶対パスなし)。道具は [tools/](tools/)。測った機械: Windows 11・x86-64(同じ機械で別の作業木の段と試験が並行して動いていた=
  壁時計は参考)。
- **〔独立検収の直し〕§14 が正**([review.md](review.md)=条件つき受入 中 3・低 10 → 全部直した・数は直した後に測り直した)。
  §0〜§13 は直す前の記録(数と形は §14 の表で上書きする)。

## 0. 結論

- 腕 `--calendar-2 {off,arm}`(環境変数 `SHIBUYA_CALENDAR_2`・既定 off)を足した。arm のランでは、会話(対面の会話の番=TM3・
  通話の番とメッセージを送る判断=C1 の口)の自分の番ごとに、話し手が「約束を持ちかける/持ちかけない/自分の約束を変える」を
  判断し(J0 型の口・仮のモデル=候補から一様に選ぶ)、相手は自分の次の番で「受ける/仮で受ける/断る」を判断する。受けた人と
  出した人は**それぞれ自分の理解の行**を自分の器に書く(共有の 1 行にしない・変えられるのは自分の行だけ=ほかの体の行は
  `PermissionError`)。欄=いつ・どこ(地名帳に無い場所は言葉のまま)・誰と・何を・置き場所(性質で書く)・確かさ(確定/仮)・
  元の会話(会話の鍵と番の id)。変更は最新値と出来事の記録への 1 行。
- 頭の中の行も器に保管し、本人には**記憶で思い出せたときだけ**見せる(記憶 M1 の式=ACT-R の折衷形・人ごとの忘れる速さ・
  τ=M1 の仮の値・相手が同じ所に居れば手がかり)。読む側は記憶の腕の有無で分岐しない(いつも同じ口)。
- 壊れた予定(始まりが無い・終わりが始まりより前・場所が空)だけ拒む(アプリなら本人に教える・頭の中なら何も)。間に合わない・
  閉店中・過ぎた時刻は記録だけ。アプリは重なりを警告する(記録)。アラーム=時刻の実行意図と同じ種類の行(上限なし)・出来事が
  きっかけの実行意図(相手に会ったら確かめる)=頭の中の行。範囲外の過ごし方=範囲の外に出た刻みに本人が本人の計画(頭の中)に
  書くか選ぶ(実行は今のまま=W17 の行・範囲外の食事の予定)。初めの個人の予定は空で始める(つなぎ)。
- **エンジンは時刻も回数も決めない**: 機会は本人が考えた刻み(主の判断の呼びの次の刻み=仲裁)と本人が選んだ知らせの時刻
  (アプリ・アラーム)だけ。本人の語の原因は全部この層の判断の呼び(監査の食い違い 0=5,000 体で 4,873 行・C1 と束ねて 229,558 行)。
  AST の負の対照で「帳面に事象を置くのは本人の選んだ時刻だけ・本人の語の原因は判断の答えだけ・器は口だけで書く」を固定した。
- **既定 off で結果不変**: byte-check 19 構成 × 25 欄が土台 `2809c4a` の写しと全部同じ(19/19・[byte_check_ca2.json](byte_check_ca2.json))。
- **腕 arm(mock 5,000 体)**: 1 日・2 日とも最後まで回る。2 日の日の境目の再開=通し(final と T≥1440 の checkpoint 24 個の 2 つの
  ハッシュ・manifest の計器が同じ)・1 日の日の途中(T=720)の再開=通し(checkpoint 12 個)。段 B(合成 80 体・C1 と束ねて 360 刻み)は
  宣言の外 0。
- 仮のモデルは候補を一様に選ぶ=数は振る舞いのモデルではない(§5 の注)。C1 と束ねると判断の呼び 37 万回/日・出来事の記録
  57 MB/日(5,000 体)=**腕は既定にしない**(つなぎ `DOC-ca2-not-default`)。

## 1. 作ったもの・変えたもの

| ファイル | 中身 |
|---|---|
| `src/shibuya/engine/calendar2/__init__.py`(新) | 包みの説明だけ |
| `src/shibuya/engine/calendar2/arm.py`(新) | 腕の切替口・設定の指紋の組 `config()`・状態台帳の腕の名 `calendar-2`・manifest の鍵 `calendar_2` |
| `src/shibuya/engine/calendar2/book.py`(新) | 本人の予定の器 `PromiseBook`(行=持ち主ごと・書く口 `write`・自分の行だけ `edit`・観測の欄 `observe`・締めた行を落とす `drop`)・壊れた予定 `broken`(CA4 (d))・置き場所の性質 `PLACEMENT_TRAITS`・行の種類 5 つ・状態・確かさ |
| `src/shibuya/engine/calendar2/recall.py`(新) | 頭の中の予定の思い出し `HeadRecall`(記憶 M1 の `base_level`・人ごとの忘れる速さ `forgetting_scale`=同じ鍵の同じ値・τ=`tau_from_m0(RECALL_TAU)`・手がかり `W_CUE`・想起の練習 `touch`) |
| `src/shibuya/engine/calendar2/port.py`(新) | 判断の口 `Calendar2Port`(`DecisionPort` の子=J0 と同じ入口・仮のモデル=C1 の `ContactPort` と同じ形・用途名 `calendar2.mock`/`calendar2.present`)・候補 `cand`・判断の種類 12・呼びの id の形(通し番号は `SERIAL_BASE`=2^20 から=連絡の判断とぶつからない) |
| `src/shibuya/engine/calendar2/layer.py`(新) | 持ち主 `Calendar2Layer`・系 `sys_calendar_2`・会話の番の控えの口 `note_turn`・初めの予定の口 `write_initial`・manifest の `calendar_2`・監査 `audit_causes` |
| 共有のファイル | §11 |
| `tests/engine/calendar2/`(新) | §10 |
| 記録 | 本書・[byte_check_ca2.json](byte_check_ca2.json)(19 構成)・[ca2_5000.json](ca2_5000.json)(計器の表の元=1 日・C1 と束ねた 1 日・2 日と再開)・道具 [tools/run_ca2.py](tools/run_ca2.py)・[tools/add_bridges_ca2.py](tools/add_bridges_ca2.py) |

## 2. 口の表(誰が=CT0・CA の決まり)

| 口 | 置き場 | 中身 | 誰が |
|---|---|---|---|
| 会話の番の控え | `Calendar2Layer.note_turn`(対面=`engine.systems.llm_io.utter` の `conv.utterance` の後・通話=`ContactLayer._calls_turns`・メッセージ=`ContactLayer._queue_send`=送る判断)→ `_turns`(行 CA2G) | 会話の鍵(`f:<会話>`・`c:<通話>`・`p:<a>:<b>`・`g:<グループ>`)・話し手・刻み・番の id・相手 | エンジン(控えるだけ・世界の状態は書かない) |
| 番の判断 | `_on_turn`(`P_TURN`) | 約束を持ちかける/持ちかけない/自分の約束を変える(相手との自分の行があるとき) | 本人(判断の口) |
| いつ・長さ・どこで・何を | `_when`(`P_DAY`・`P_HOUR`)・`P_LENGTH`・`_where`(`P_PLACE`)・文の口 `_text` | 日=今日〜6 日後(曜日・祝日=暦の常識 CA11)・正時・1/2/3 時間か決めない・ここ(今いるセル)か言葉で決める(地名帳に無い場所=言葉のまま)・何を=文の口(仮のモデル=定型の文) | 本人 |
| 誘い | `_offers`(行 CA2O) | 会話の鍵に付く・元の会話の番の id・中身・返事・聞いたか | 状態 |
| 返事 | `_respond`(`P_RESPOND`)=相手の次の番 | 受ける/仮で受ける/断る(入力の目印=誘った出来事) | 本人 |
| 聞く | `_hear`=出した人の次の番(返事が全部そろったとき)か会話の終わり(`_settle_offers`) | 受けた/仮で受けた相手と自分の行を書く・返事の無い誘いは会話の終わりで消える | 本人(書くのは本人の判断) |
| 書く | `_write_own` → `PromiseBook.write` | 置き場所(`P_PLACEMENT`)・知らせ(`P_NOTIFY`=始まりの 10/30/60 分前・アプリは知らせないも)・出来事の実行意図(`P_INTENT`=頭の中のとき) | 本人 |
| 拒む(CA4 (d)) | `book.broken` → `約束:拒んだ`(原因=過程 calendar2) | 壊れた予定だけ・アプリは本人に教える(`rejected_shown`)・ほかは何も(`rejected_silent`) | 道具(エンジン) |
| 重なりの警告 | `_overlaps` | アプリの行だけ(数える・書くのは本人) | 道具 |
| 不可能な予定 | `_impossible`(書いたときと出発のとき) | 間に合わない(歩行グラフの節の数 × 刻み)・閉店中(営業の表)・過ぎた時刻=記録だけ | 計器 |
| 知らせ | `_agenda`(本人が選んだ時刻)→ `約束:知らせ`(原因=過程 calendar2) | アプリの通知・アラーム(寝ていれば鳴った数を数え、起きた後に考えたとき見える) | 道具 |
| 見える | `_visible` | アプリ=知らせ・C1 の無いランは考えたとき・C1 のランは画面を見ているとき/アラーム=鳴ったとき/手帳=その日に最初に考えたとき/頭の中=記憶で思い出せたとき(手がかり=相手が同じセル・実行意図のきっかけ) | System 1(頭の中は記憶の強さ) |
| 出発する | `_look`(`P_GO`)→ `_depart` → `engine.resolve.begin_walk_to` | 出発する/まだ/行かない(行かない=自分の行の状態を変える) | 本人(歩くのは体の基本動作) |
| 変える | `_change`(`P_EDIT`・`P_EDIT_WHAT`)→ `PromiseBook.edit` | 時刻・場所・確かさ・取り消し(自分の行だけ・相手の行は変わらない) | 本人 |
| 範囲外の過ごし方(CA6 (b)) | `_outside`(`P_OUTSIDE`) | 範囲の外に出た刻みに本人の計画(頭の中)を書くか・戻ったら締める | 本人(実行は今のまま) |
| 初めの個人の予定(CA2 (c)) | `write_initial` | 仮のモデル=空で始める | 本人(つなぎ) |
| 計器 | manifest の `calendar_2` | §5 | — |
| 監査 | `audit_causes`・`issued_keys`(行 CA2Q) | 本人の語の原因=この層の発行した判断の呼び・体・判断の種類・時刻=判断の刻み/道具の語の原因=過程 calendar2 | — |

## 3. 流れ(対面の会話 1 で体 A が体 B を誘う例)

1. 刻み T: A の会話の番の発話(判断の系)→ 控え `["f:1", A, T, 番の id, [B]]`。系 calendar_2: A の番の判断=持ちかける → いつ(日・
   時刻)・長さ・どこで → 何を(文の口)→ 誘い(`約束:誘った`・whom=B・via=対面・how_much=誘いの番号・原因=A の番の判断)。
2. 刻み T+1: B の番 → B に宛てた誘いに返事(`約束:受けた`)→ B が自分の行を書く(置き場所・知らせ・実行意図=`約束:書いた`)。
   B の番の判断(持ちかける…)も同じ刻み。
3. 刻み T+2: A の番 → 返事が全部そろった=聞く → A が自分の行を書く。会話が先に終わったら、終わった刻みに聞いて書く。
4. その日: 本人が考えた刻みの次の刻み(主の判断が先)と、知らせの時刻に、見える行について出発する/まだ/行かない。出発=約束の
   セルへ歩く。着いた刻み・始まりの刻みに居たか(計画一致)・終わりで締める(5 分前までに着いた/間に合った/遅れて着いた/
   出発したが着かなかった/出発しなかった/忘れた=一度も見えなかった/行かない/取り消し)。
5. メッセージ・グループ: 送る判断がその人の番(届く前)・相手の番=相手の次の送る判断(読む前でも返事を聞く=仮採用)・会話の
   終わり=チャットの状態の締め。通話: 通話の番。

## 4. 頭の中の予定(MR の器との関係)

- 頭の中の行は記憶の痕跡 `trace=[回数, 最初の時刻, 直近の時刻 3 つ]` を持ち、強さ `A=B+W_IMPORTANCE×重要度`(B=`memory_m1.base_level`・
  d=0.5×人ごとの倍率=MR8・重要度=会話の記憶と同じ 3)。思い出す=`A≥τ`(τ=−3.739=M1 の仮の値)・手がかり(約束の相手が同じセル)が
  あれば `A+W_CUE≥τ`。思い出した回は痕跡に 1 回足す。書いた直後から手がかりなしで思い出せるのは約 10 時間(人ごとの倍率 1 の
  とき=推測の計算)。LLM には数を見せない(MR-0)=本段は判断が仮のモデル。
- 行の目印は `書いた` の出来事の id(1-3)。記憶の器(1-6 の `MemoryStore`)には行を足していない=**器が無いときの形がこれ**で、
  器のあるランも同じ口を通る(読む側は分岐しない)。器に予定の種類を足すか(器の種類の表の版上げ)は親の判断(§13)。
- 負の対照: 思い出せない刻みに考えても見えない(見た回数 0・`head_recall:思い出せない`)・相手が同じ所に来ると手がかりで見える
  (`test_head_row_is_seen_only_when_recalled_negative_control`)。

## 5. 計器(腕 arm・mock 5,000 体・世界 v2・seed 1・合否なし)

[ca2_5000.json](ca2_5000.json)(道具 [tools/run_ca2.py](tools/run_ca2.py))。「C1 と束ねた」=`--contact c1`(宛先=世帯と職場の
グループ・関係 off)。

| 計器 | 腕 arm 1 日 | 腕 arm 2 日 | C1 と束ねた 1 日 |
|---|---|---|---|
| final(全桁の頭)・主の判断の呼び・壁時計 | `8ff0d14d…`・64,023・44.0 秒(既定 off は `333b1820…`・64,024・44.5 秒) | `667fa5a4…`・—・86.3 秒 | `49062d85…`・64,098・193.8 秒 |
| 会話の番(対面/グループ/通話) | 649/—/— | — | 639/42,424/3 |
| 誘い(対面/グループ/通話) | 281/0/0 | 573(対面) | 282/14,547/2 |
| 返事 受ける/仮で受ける/断る/返事なし(割合) | 86/58/73/64(0.31/0.21/0.26/0.23) | 173/126/150/124 | 29,496/29,631/29,644/45,596(0.22/0.22/0.22/0.34) |
| 二人の約束の行(置き場所 アプリ/アラーム/手帳/頭の中) | 288(69/76/71/72)・書いた体 203 | 598(162/156/139/141) | 72,000(17,953/18,053/18,131/17,863)・1,049 体 |
| 1 人 1 週間の約束の数 | 0.40 | 0.42 | 100.8 |
| 初めの予定(頻度) | 0(0.0/体=空で始めるつなぎ) | 0 | 0 |
| 締めた約束の結末 5 分前/間に合った/遅れた/着かなかった/出発しなかった/忘れた/行かない/取り消し | 6/0/0/10/5/0/18/4 | 18/0/3/29/16/10/46/10 | 240/7/58/1,038/683/1,129/2,191/1,203 |
| 5 分前到着の率・遅刻の率(取り消しと行かないを除く) | 0.29・0.00 | 0.24・0.04 | 0.08・0.02 |
| 忘れた割合(アプリ/アラーム/手帳/頭の中) | 0/0/0/0 | 0/0.11/0.07/0.14 | 0.06/0.04/0.54/0.05 |
| 計画一致率(始まりの刻みに約束のセルに居た) | 7/12(0.58) | 11/40(0.28) | 241/1,465(0.16) |
| 不可能な予定(書いた時: 閉店中/間に合わない/過ぎた時刻・出発の時) | 14/0/0・0 | 38/0/0・閉店中 0/間に合わない 1/過ぎた 2 | 1,725/45/528・39/49/316 |
| 頭の中 思い出した/思い出せない | 20/0 | 45/30 | 3,387/325 |
| 知らせ アプリ/アラーム(寝ていた) | 5/9(0) | 20/31 | 1,451/2,588(3) |
| 実行意図 アラーム/出来事/きっかけで思い出した | 76/25/22 | 156/64/59 | 18,053/9,049/1,842 |
| 変えた(時刻/場所/確かさ/取り消し) | 27/20/29/22 | 54/52/58/47 | 3,382/3,250/3,333/3,420 |
| 出発の判断 出発(もう居た/歩き出した/言葉の場所/会話中/歩けない)/まだ/行かない | 8/1/10/2/0・17・18 | 17/5/33/3/3・41・50 | 147/523/1,968/13/273・2,980・2,992 |
| 範囲外の過ごし方 出た/書いた/戻った | 7,774/3,837/1,983 | 15,783/7,814/5,891 | 7,753/3,800/1,959 |
| メッセージを読むまで[分](C1 の計器を読むだけ)p50/p75/p95 | —(C1 なし) | — | 2/6/363(n=311,567) |
| 判断の呼び(判断モデル)・文の口(LLM) | 10,595・4,275 | 21,622・8,701 | 370,463・31,280 |
| 約束の族の出来事の行・監査の食い違い | 4,873・0 | 10,021・0 | 229,558・0 |
| 出来事の記録の全体(行・行のバイト・原因の表のバイト) | 58,400・4.20 MB・0.56 MB | 111,633・8.04 MB・1.04 MB | 430,969・31.0 MB・26.0 MB |
| 仲裁で次の刻みに回した考えた体 | 104 | 433 | 597 |
| 変える予定の候補の上限に当たった | 0 | 0 | 10,427 |
| 終わりに生きている行 | 2,183 | 2,558 | 90,542 |

- **数の読み方の注**: 仮のモデルはそのときある候補から一様に選ぶ(会話の番ごとに 1/2〜1/3 で持ちかける・返事は 1/3 ずつ)。C1 と
  束ねたランのグループのチャットは成員の全員が番ごとに返事と書くを判断する=行と呼びが膨らむ。手帳の忘れた割合 0.54 は「その日に
  最初に考えたときだけ開く」の仮の習慣で、その日の後で書いた今日の行が見えない形から来る(推測)。数は振る舞いのモデルではない
  (判断モデル 6-1 と LLM で置き換える)。会話から約束が生まれる割合・約束のうち会っていないときに決まる割合の錨は空欄(R-85 §3)・
  検証側は読んでいない。
- 範囲外の過ごし方の「出た」は範囲の外に出た遷移の数(同じ体が日に何度も出入りする)。書いた行の 1/2 は仮のモデルの選び。
- 腕 arm 1 日の約束の族の分の記録(4,873 行 × 72 B ≈ 0.35 MB/日・原因の表を含めて約 0.5 MB/日)は既定の記録(約 54,000 行)の 9%。
  〔検収 L10 で直した〕C1 と束ねたランの 57 MB/日は C1 の分を含む記録の全体。C1 だけのラン(14.68+16.33 MB)との差で見ると、
  カレンダー 2 が足すのは行 +227,133・行のバイト +16.35 MB・原因の表 +9.69 MB=**約 26 MB/日**(5,000 体)。39 万体への線形の外挿
  (推測)はカレンダー 2 の分で約 2 GB/日(全体で約 4 GB/日)=どちらも 1-3 の宣言を大きく超える=既定化の条件を満たしていない
  (`DOC-ca2-not-default`・C1 の量の判断と束ねる)。

## 6. 負の対照

| 確かめ | 対照 | 試験 |
|---|---|---|
| 各自の行・自分の行だけ | ほかの体の行を `edit` すると `PermissionError`・観測の欄は本人の口で書けない・本人の欄は観測の口で書けない | `test_book_rows_are_each_own_and_only_the_owner_can_edit` |
| 変更は 1 行 | 時刻を変えると出来事 1 行(`約束:時刻を変えた`)・相手の行は変わらない | `test_change_is_own_row_only_and_one_event` |
| 壊れた予定だけ拒む | 終わりが始まりより前・場所が空=拒む(アプリだけ教える)/地名帳に無い場所の言葉・終わりが同じ=拒まない/間に合わない・閉店中=書いて数える | `test_broken_*`・`test_late_and_closed_are_only_recorded` |
| 思い出せない体には見えない | 手がかりの無い忘れた刻みに考えても見た回数 0・相手が同じ所に来れば見える | `test_head_row_is_seen_only_when_recalled_negative_control` |
| エンジンは時刻と回数を決めない(AST) | 帳面に事象を置くのは `_schedule_row` だけ・知らせの刻みは `notify_ns` と `written_ns` だけから・行の時刻の欄を作る辞書は `_write_own` と `_outside` だけ・考えた刻みは T だけ。植えた 4 件(始まりから 30 刻み前の知らせ・始まりからの考えた刻み・ほかの関数の帳面・ほかの関数の時刻の欄)を全部見つける | `test_ast_engine_does_not_decide_times`・`test_ast_negative_control_catches_a_backward_reminder` |
| 本人の語の原因は判断の呼びだけ(AST) | 本人の語の `_log` の原因=同じ関数の `self._decide` の答えか、それを渡す引数 `cause`・道具の語=過程 calendar2。植えた 4 件(道具が出発した・偽の LlmCall の書いた・判断が原因の知らせ・過程を cause に渡す呼び手)を全部見つける | `test_ast_person_events_come_only_from_decisions`・`test_ast_negative_control_catches_planted_rules` |
| 器は口だけで書く(AST) | 層の中に行の欄への直の代入が無い | `test_ast_book_is_written_only_through_its_ports` |
| 監査 | 連絡の形の id・道具が原因の本人の語・判断が原因の道具の語・体の違う呼び=4 件とも数える | `test_audit_catches_forged_and_engine_causes` |
| 段 B | 連絡の系の宣言から `CA2G:calendar2._turns` を外すと `AssertionError`(宣言の外) | `test_stage_b_negative_control_without_the_turn_declaration_fails` |
| 既定は何も作らない | 腕 off=層なし・manifest に節なし・族 約束の出来事 0 | `test_default_off_builds_nothing` |
| 腕の取り違えの再開は止まる | arm で書いた状態を off で再開=設定の指紋の `calendar_2` で止まる | `test_resuming_with_the_arm_off_stops` |

## 7. 既定 off の結果不変

- byte-check 19 構成(mock/classical 5,000 体・seed 1・1 シミュ日・テープつき)× 25 欄: 土台 `2809c4a` の写し(`git archive`+
  `HEAD_TREE_FILES`+data へのつなぎ=回した後に .NET で外した=`tree_missing` 空)と作業木で**全部同じ(19/19)**・呼数の合計
  1,097,946・両側の `env` 空・作業木の側は `src_is_worktree` 真=[byte_check_ca2.json](byte_check_ca2.json)(既定 v3 の final
  `333b1820f7849b00`)。
- 既定のランで動く欄(どれも 25 欄の外): `manifest_sections`(節の表=`calendar_2` と子)・`bridges_count`(つなぎの台帳 555 → 567)・
  `bridges_version`(台帳の sha)・日次の記録の `bridges_count`。`calls_by_model` は既定のランでは今のまま(カレンダー 2 の呼びは
  足していない=§13)。
- 腕 off のランでは層・系・控えの口(`turn_sink`)・`llm_io.utter` の控えのどれも動かない(`getattr(b.layers, "calendar2")` が None)。

## 8. 2 日と再開(腕 arm・5,000 体)

| ラン | 通し final | 再開 final | 同じか |
|---|---|---|---|
| 2 日・日の境目 T=1440 で止めて再開 | `667fa5a4…` | `667fa5a4…` | final・T≥1440 の checkpoint 24 個の behavior/full・manifest の計器(約束・返事・到着・忘れた・計画一致・不可能・範囲外・実行意図・変えた)が同じ |
| 1 日・日の途中 T=720 で止めて再開 | `8ff0d14d…` | `8ff0d14d…` | final・T≥720 の checkpoint 12 個・manifest の計器が同じ |

- 合成(80 体・C1 と束ねる・2 日)の日の境目の再開=通し(`test_two_days_and_resume_is_the_straight_run`)・slow の 5,000 体の日の途中の
  再開(`test_world_5000_one_day_records_meters_and_resume`)。

## 9. manifest の節・設定の指紋・状態台帳の行・つなぎの台帳

- manifest の一番上の鍵 `calendar_2`(腕 arm のランだけ=既定のランの鍵の集合は今のまま=`manifest_keys_frozen.json` は変えていない)。
  設定の子 11(`schema`・`arm`・`port`・`placements`・`kinds`・`certainty`・`candidates`・`recall`・`early_min`・`arbitration`・`provisional`)・
  観測の子 16(`meter`・`decisions`・`promises`・`responses`・`initial`・`forgot`・`arrival`・`plan_match`・`impossible`・`read_delay_minutes`・
  `outside_plan`・`intentions`・`rejected`・`changes`・`live_rows`・`calls`)。節の表の混ざった辞書の末尾に足した=設定の道筋 11 本
  (`CONFIG_PATHS_SHA256` `99fd537f…9e8ba6` → `21ef3084…1f077ca`=この 11 本を外すと前の値)。
- 設定の指紋に `calendar_2`(腕 arm のときだけ=`{"arm": "arm"}`)。
- 状態台帳の腕の行(腕の名 `calendar-2`・持ち主の居るランだけ 2 つのハッシュと状態のファイルに入る=既定は不変・版は上げない=
  1-3 以来の仮採用と同じ理由):

| 行 | 道筋 | 軸 1 / 軸 2 |
|---|---|---|
| CA2B | `calendar2.book.rows`・`by_owner`・`next_id` | behavior / required |
| CA2O | `calendar2._offers`・`_offer_next`・`_agenda`・`_watch`・`_noticed`・`_planner_day`・`_was_out`・`_out_row`・`_days` | behavior / required |
| CA2G | `calendar2._turns`(系の間)・`_think`(仲裁で回した考えた体) | behavior / required |
| CA2M | 計器 `calendar2._c2_meter`・`_c2_hist`・`_c2_per_agent` | diag / required(再開でも計器が通しと同じ=1b の C1BM と同じ形) |
| CA2Q | 発行した判断の呼びの控え `calendar2._c2_issued`・`_c2_issued_n` | diag / required |

- 外の状態 137 → 142 行・全体 228 → 233 行。診断の行の属性の名は 10f の AST(軸 1)の名前の衝突を避けて `_c2_` を頭に付けた。
  連絡の持ち主の `turn_sink`(控えの口)は参照として除外。manifest の読むまでの時間は C1 の計器(`CT1M`)を読む=診断の出口
  `Calendar2Layer.manifest` を `state_ledger_ast.DIAG_EXITS` に足した。
- 出来事の記録の語彙: 族 `約束` と 13 語(表の末尾=6-4 までの 80 語のコードは不変・80〜92)・道具の名 `calendar2`
  (`CALENDAR2_PROCESSES`・原因の名の末尾)・版 `events-vocab/6-2-ca2`。
- つなぎの台帳 12 行(`DOC-ca2-initial-empty`・`-port-candidates`・`-placement-kinds`・`-ca7-provisional`・`-head-recall`・
  `-turn-opportunity`・`-visibility`・`-arbitration`・`-exec-scope`・`-impossible-form`・`-outside-plan`・`-not-default`=555 → 567 行)。
  外す段に `next-bump` は使っていない(6-1・6-2・6-4・6-5・6-6・5-1・7)。道具 [tools/add_bridges_ca2.py](tools/add_bridges_ca2.py)
  は同じ id の行を置き換える(並行の段の行の後ろに足し直せる)。コードの expedient の宣言の 6 形は使っていない。
- 乱数: 用途名 `calendar2.mock`・`calendar2.present`(動きの側=`MOTION_RNG_DOMAINS` の末尾)・`SAFE_SITES` 22 → 23・決まらない呼び手
  14 → 15。人ごとの忘れる速さは記憶 M1 と同じ関数・同じ鍵(`memory.forgetting_rate`=呼び手は同じ)。

## 10. 試験

新しい試験 `tests/engine/calendar2/`(共通 `_ca2.py`=腕の切替・層だけを回す合成の台 `Harness`・判断の差し替え・グループの一覧を
入れる口):

- `test_ca2_units.py`(20): 器(各自の行・自分の行だけ・欄の口)・壊れた予定の線・呼びの id(連絡の判断とぶつからない)・各自の行と
  欄(置き場所・確かさ・元の会話・知らせ・痕跡)・仮で受ける/断る/返事なしで消える・変更は自分の行だけで 1 行・確かさと取り消し・
  壊れた予定だけ拒みアプリだけ教える・間に合わない/閉店中は記録だけ・アプリの重なりの警告・頭の中は思い出せたときだけ(負の対照
  と手がかり)・書いた直後は思い出せて練習で痕跡が増える・仲裁(主の判断が先)・知らせ → 出発 → 5 分前到着と計画一致・寝ていて
  鳴ったアラームは起きた後に見える・出来事がきっかけの実行意図・監査の負の対照・変える予定の候補の上限。
- `test_ca2_runs.py`(14): 既定 off は何も作らない・腕 arm の合成のラン(C1 と束ねる=各自の行・計器と出来事の行の数が合う・
  manifest の節と節の表・監査 0・メッセージとグループからも約束)・2 日と再開=通し・取り違えの再開は止まる・段 B と負の対照・
  腕の行・系の宣言・CLI の引数とランの種類・AST の 3 つと負の対照 2 つ。
- `test_ca2_world.py`(1・slow・data): 5,000 体 1 日の記録・監査・範囲外の計画・日の途中の再開=通し。

結果(作業木の src・本体の .venv・`-p no:cacheprovider -o addopts=""`):

- 発注の範囲(`tests/engine` 全体・`tests/economy/cp2`・`tests/c8`・`tests/tools`・`-n 2 --dist loadfile -m "not slow"`):
  **3,263 passed・1 skipped・0 failed**(51 分 29 秒)。この後の直し(変える予定の候補の上限=腕の中だけ・識別子の名)の後に
  `tests/engine/calendar2` を slow を含めて回し直した(§10 の下)。
- `tests/engine/calendar2`(slow を含む・1 プロセス=5,000 体は 1 本ずつ): **35 passed**(6 分 48 秒)。識別子の名の直しの後に
  `tests/engine/calendar2`(slow を除く)・`tests/engine/time`・`tests/engine/bridging`・`test_state_checks_10f.py` を回し直して 153 passed。
- lint-imports: 5 kept・0 broken(290 ファイル)。
- 秘密の検査(`tools/scan_secrets.py` に変えたファイルと新しいファイル 43 本・`_bc` を除く): CLEAN。
- `tests/c7` は回していない。

## 11. 触った共有ファイル(取り込み順の rebase の一覧=段 10 と並走・どれも末尾に足す形)

| ファイル | 触った所 |
|---|---|
| `src/shibuya/engine/systems/table.py` | import 1 行・`contact` の後に系 `calendar_2`・decide と llm_receive と contact の `paths` の末尾に `CA2G:calendar2._turns`・decide と llm_receive の reads の末尾・close_final の reads の末尾に `layers.calendar2`・docstring の段落 |
| `src/shibuya/engine/systems/llm_io.py` | `utter` の `conv.utterance` の直後に控えの 4 行(腕のランだけ) |
| `src/shibuya/engine/systems/conductor.py` | `WHEN` の末尾に `calendar2` |
| `src/shibuya/engine/systems/boxes.py` | `OWNER_NAMES` の末尾・`Layers` の末尾の欄 `calendar2` |
| `src/shibuya/engine/systems/state_io.py` | `hash_owners` の末尾と docstring |
| `src/shibuya/engine/systems/run_end.py` | `contact_layer` の直後に `calendar2_layer` |
| `src/shibuya/engine/systems/build.py` | 設定の指紋(C1 の直後)・組み立て(C1 の層の後=控えの口を C1 に挿す)・`Layers(calendar2=…)` |
| `src/shibuya/engine/contact/layer.py` | 属性 `turn_sink`(既定 None)・`_calls_turns` と `_queue_send` の末尾に控えの呼び(腕のランだけ) |
| `src/shibuya/engine/run.py` | manifest の末尾(`contact_c1` の後)・補助 `_calendar2_field`・乱数の用途名の表の末尾 2 つ |
| `src/shibuya/engine/rng_audit.py` | `SAFE_SITES` の末尾 1 行・`UNDETERMINED_SITES` の末尾 1 行 |
| `src/shibuya/engine/manifest_sections.py` | `PATHS` の末尾(`contact_c1` の後) |
| `src/shibuya/engine/state_ledger.py` | `_EXT` の末尾(CT1Q の後)に 5 行・`OWNER_CLASSES` の末尾 2 項・`EXCLUDED` の末尾 6 項 |
| `src/shibuya/engine/state_ledger_ast.py` | `DIAG_EXITS` の末尾 1 項 |
| `src/shibuya/engine/events/vocab.py` | 族 `約束`(`FAMILIES` の末尾)・13 語(表の末尾)・道具の名 `calendar2`(原因の名の末尾)・版・docstring |
| `src/shibuya/cli.py` | `run` のランの種類の腕の数え方の末尾・引数 `--calendar-2`(`--contact` の後)・切替口 |
| `docs/design/bridging-ledger.json` | 末尾に 12 行 |
| 凍結の表の試験 | `tests/engine/systems/test_systems_table.py`(並び・刻みの系 28)・`writes_soa_frozen.json`(末尾に calendar_2)・`tests/engine/events/writes_paths_events.json`(contact の後に calendar_2)・`test_e_vocab_is_closed.py`(93 語)・`tests/engine/test_state_ledger_10b.py`(142・233・外の行の並び・腕の行)・`test_state_checks_10f.py`(`SAFE_SITES` 23・決まらない呼び手 15)・`test_env_and_sections_10f.py`(`CONFIG_PATHS_SHA256`)・語彙の末尾と版を固定していた 5 本(`tests/engine/speech/test_speech_port_schema.py`=版・腕の行の一覧・`tests/engine/tools/test_c0_tool_registry.py`=族の並びと原因の名の位置・`tests/engine/experiment/test_x33_apply.py`=版・`tests/economy/stage2/test_stage2_account_and_conservation.py`=版と経済の過程の名の位置・`tests/engine/multiday/test_md23_body_events.py`=族の末尾と原因の名の位置) |

触っていない: `conversation.py`・`perception/*`・`manifest_keys_frozen.json`・`tick_word_allow.json`・`time_literal_allow.json`・状態のファイルの
許可の表・進行役の窓のループ・判断の口(`decision/*`)・記憶の器(`memory*.py`)・道具の台帳・10e の byte-check の道具
(`SWITCH_ENV` に `SHIBUYA_CALENDAR_2` を足すのは親が本体で=C1 の L6 と同じ)。

## 12. 限界と仮採用(10-13b §0-3・つなぎの台帳の行)

1. **誘いの機会**(`DOC-ca2-turn-opportunity`): 会話の自分の番ごと・返事は相手の次の番・出した人が聞くのは自分の次の番(返事が全部
   そろったとき)か会話の終わり・メッセージは読む前でも次の番で返事を聞く・返事の無い誘いは会話の終わりで消える。誘い・返事・
   書くは番と同じ刻みの別の呼び(GPU の後は番の LLM の出力に畳む)=呼び数は `calendar_2.calls` に出す(`calls_by_model` には
   足していない)。
2. **候補の作り方**(`DOC-ca2-port-candidates`): 7 日先まで・正時だけ・長さ 1/2/3 時間か決めない・どこで=ここか言葉・知らせ 10/30/60
   分前・変える予定の候補は始まりの近い順に 20 まで(安全装置・C1 と束ねると 10,427 回当たる)・何をと言葉の場所は文の口の定型の文。
   仮のモデルは一様。
3. **置き場所の種類と性質**(`DOC-ca2-placement-kinds`): 4 つ(1b と同じ名)・行の種類 5 つ=未リサーチ(expedient)。
4. **見え方**(`DOC-ca2-visibility`): その日の行だけ・アプリ(C1 の無いランは考えたとき見える・C1 のランは画面を見ているとき)・手帳は
   その日に最初に考えたとき(手帳の忘れた割合が高い原因=推測)・アラームは鳴ったとき。
5. **頭の中の思い出し**(`DOC-ca2-head-recall`): 記憶 M1 の式と値のまま・手がかり=相手が同じセル・器には行を足していない。
6. **CA7**(`DOC-ca2-ca7-provisional`): アラーム=時刻の実行意図と同じ種類の行(上限なし)・出来事がきっかけ=頭の中の行(きっかけ=
   相手が同じセル)。仮(リサーチ B4)。
7. **仲裁**(`DOC-ca2-arbitration`): 見える予定の判断は主の判断の呼びのあった刻みにしない(次の刻み)。
8. **出発の範囲**(`DOC-ca2-exec-scope`): 歩くのは地名帳のセルの行だけ・言葉の場所と範囲の外の体は記録だけ・着いた=約束のセルに
   入った刻み・5 分前到着の 5 分は CA8 の計器の定義・終わりを決めていない行はその日の最後の刻みで締める。主の判断(仮のモデル)が
   歩いている体を別の行為に向ける=「出発したが着かなかった」が多い(C1 と束ねて 1,038)。
9. **不可能な予定の形**(`DOC-ca2-impossible-form`): 間に合わない=今の居場所から歩行グラフの節の数 × 刻み(1b と同じ見積り)・
   閉店中=約束のセルの店がどれも始まりの分に開いていない(その日の営業の表で別の日も見る)。
10. **範囲外の過ごし方**(`DOC-ca2-outside-plan`): 範囲の外に出た刻みに書くか選ぶ・何を=文の口・実行は今のまま(エネルギーの範囲外の
    食事の予定と W17 の行は写さない・読まない=1b の出入りの判断と W17 の関係を壊さない)。
11. **初めの個人の予定**(`DOC-ca2-initial-empty`): 空で始める。
12. **既定にしない**(`DOC-ca2-not-default`): §5 の量。
13. 語彙 13 語と版の名 `events-vocab/6-2-ca2`・道具の名 `calendar2`・用途名 2 つ=実装役の構成。
14. 誘いの宛先=その会話の相手(グループのチャットは成員の全員)。3 人の対面の会話は全員に誘う。

**限界**

- 二人の約束の相手が後から変えたことを知るのは本人の行動(会話)だけ=各自の行は食い違ってよい(CA3)が、食い違いの数は数えていない。
- 遅刻の連絡(C3 の職場の連絡・電話の 88%)・約束の場所への到着を待つ・待ち合わせの成否(TM4 の指標)は本段に無い。
- 「LLM が書いた『来週の火曜の昼』を暦で時刻に直す口」は仮のモデルが候補で選ぶので要らない=判断モデルと LLM の段で作る。
- 腕 `--calendar 1b` と束ねたランは回していない(1b の勤務の約束と本段の行は別の器)。
- 道具の台帳(1-7)にアプリ・アラーム・手帳の行は足していない(置き場所の性質は本段の表)。
- 〔検収 L7〕CA8 の計器の「熟考の割合」と、5-1 の「カレンダーに入るもの」のうち予約・イベント・締め切りの種類は本段に無い(熟考=
  判断モデルの段・行の種類は増やせる=`KINDS`)。
- 〔宣言・検収〕艦隊の経路(到着の系 `llm_receive` の会話の番の発話 → `note_turn`=宣言 `CA2G:calendar2._turns`)は mock では
  通らない=段 B で確かめていない(実 LLM の段で=台帳 `DOC-ca2-fleet-turn-unchecked`)。

## 13. 親に確かめてほしいこと(問い)

〔検収の後の親の判断〕1=記憶の器には足さない(今の形=目印+M1 の痕跡のまま・器に足すのは 6-5 の版上げと一緒に)・2=`calls_by_model` に
内訳 `calendar_2`(manifest と日次の記録・§14 で直した)・3=量は宣言のまま既定にしない(C1 の記録の予算の判断と束ねて §1-1)・4=今の形・
5=共有の所は影響が腕の中だけと検収で確かめた=そのまま(系の reads は §14 L3)・6(用語集)=親が取り込みのときに用語集へ足す。
足す語の一覧: **置き場所・確かさ・元の会話・本人の計画・実行意図・誘い・控え**。10e の `SWITCH_ENV` の `SHIBUYA_CALENDAR_2` は親が
本体で足す。〔検収 M3〕と同じ形(behavior の行に出来事の id)が **C1(`CT1*`)にもある=別の整理**(親が小さな整理で直す・本段では
C1 に触っていない)。

以下は直す前に書いた問い(記録として残す)。

1. **記憶の器に予定の行の種類を足すか**: 発注の「MR の器に目印」は、本段では器(1-6 の `MemoryStore`)に行を足さず、カレンダー 2 の
   行が出来事の id の目印と記憶 M1 の式の痕跡を持つ形にした(器の種類の表 `EVENT_KINDS`=1〜11・12・13・14 の版上げと、記憶の腕との
   同値の試験に触るため)。器に足す形(読む口は同じ・器のあるランは器の強さを読む)に替えるか。
2. **呼び数を `calls_by_model` に足すか**: C1 の検収 M5 と同じ形(内訳 `calendar_2`)にするか。本段は manifest の `calendar_2.calls` だけ。
3. **誘いの機会の形**(§12 の 1): 番ごとに判断を呼ぶと C1 と束ねたランで判断の呼びが 37 万回/日・記録 57 MB/日(5,000 体)。番の LLM の
   出力に畳むのは GPU の後。それまでの量の扱い(C1 の量の判断と束ねるか)。
4. **範囲外の過ごし方**(§12 の 10): 範囲の外に出た刻みに本人が書く形でよいか(エネルギーの範囲外の食事の予定を「本人の計画」の行に
   写す形は、計画実行層の表=軸 1 no の属性を層が読むことになるので採らなかった)。
5. 共有ファイルの所(§11)。とくに `llm_io.utter` の控えの呼び・連絡の層の `turn_sink`・`state_ledger_ast.DIAG_EXITS` の 1 項。
6. 用語集との照合はしていない(新しい語「置き場所」「確かさ」「元の会話」「誘い」「控え」「本人の計画」)。

## 14. 独立検収の直し(条件つき受入=中 3・低 10 → 全部直した・rebase はまだ)

検収の報告は [review.md](review.md)。直しの後の数はこの節が正(§0〜§13 の数は直す前=記録として残す)。scratch は作業木の `_bc2/fix/`。

### 14-1. 直しの表

| 欠陥 | 箇所 | 直し方 | 試験 |
|---|---|---|---|
| M1 時刻を変えた行の知らせが古い時刻に鳴る | `calendar2/layer.py`(`_change`・`_schedule_row`・`_opportunities`・`_notify_step`)・`book.py`(`EDITABLE_FIELDS` に `notify_ns`) | 時刻を変えたらアプリの知らせ(`notify_ns`)と結びつくアラームの行も同じだけずらす(道具の性質=持ち主の口 `edit`)。帳面は過ぎた刻みに置かない(`now_step`)・取り出すときに行の今の知らせの刻みと照らして古い印を捨てる・同じ刻みの 2 つ目の印を捨てる(始まりの印も同じ) | `test_time_change_moves_the_app_notification`(15 時 → 18 時=`約束:知らせ` が 17:30 に 1 行だけ)・`test_change_after_the_notification_leaves_no_past_marks` |
| M2 思い出せない頭の中の行を「変える」で触れる | `layer.py`(`_changeable`・`_visible(probe=)`・`_change`) | 「自分の約束を変える」の候補=会話の相手との自分の行のうち `_visible` と同じ口で今見える行だけ(頭の中=思い出せたとき・手帳=その日にまだ開いていないとき・アプリ・鳴った後のアラーム)。確かめは想起の練習に数えない(`probe`)・選んで使った頭の中の行だけ練習に足す。同じ時刻の 2 回目の想起は痕跡に足さない(`recall.touch`) | `test_forgotten_head_row_is_not_offered_for_change`(負の対照=思い出せない刻みは候補に出ず取り消せない・手がかりがあれば出る) |
| M3 記録の有無で腕の behavior-hash と final が変わる | `layer.py`(`_note_event`・`_drop`・`_drop_offer`・`_c2_event_of`・`_c2_offer_event`)・`book.py`(観測の欄から `event` を外した)・`state_ledger.py`(行 CA2M に 2 つ) | 出来事の id を行(CA2B)と誘い(CA2O)=behavior から外し、diag の別の表(CA2M)に持つ。返事の判断の入力の目印(原因の表)だけが読む | `test_event_log_on_off_does_not_change_the_arm_run`(合成 80 体・720 刻み=final と checkpoint の behavior-hash が同じ)・5,000 体 1 日で記録 on/off の final `71ad7088…` と checkpoint 4 個が同じ(§14-3) |
| L1 出した人の確かさをエンジンが決める | `layer.py`(`_hear`・`P_CERTAIN`)・`port.py`(`K_FIRM`・`K_TENT`) | 返事を聞いた本人が「確定で書く/仮で書く」を選ぶ(J0 の口・mock は一様)。計器 `heard_certainty:*` | `test_the_proposer_chooses_own_certainty_not_the_engine`(相手が仮でも確定で書ける) |
| L2 2 刻みの猶予に名が無い | `layer.py`(`OFFER_GRACE_STEPS`)・台帳 | 名を付け、つなぎの台帳 `DOC-ca2-offer-grace`(外す段 6-2) | 既存の試験(返事なしで消える) |
| L3 系の reads が足りない | `systems/table.py` | 系 `calendar_2` の reads に `layers.conv layers.contact layers.runner` | 段 B(`test_stage_b_*`) |
| L4 候補の上限に多く当たる | `layer.py`(`_change`・`EDIT_MAX_CANDIDATES`=120) | 候補=見える行の全部。提示の番号の上限 127(`LlmCall.number`)を超えるときは本人が日 → 正時で絞る(`P_EDIT`)・それでも 120 を超えたら安全装置(当たった回数=manifest の `changes.candidates_capped`)。発注の例の 256 は番号の上限 127 を超えるので取れない=120 | `test_many_change_candidates_are_narrowed_by_the_person`・`test_change_candidates_safety_cap_counts_when_it_hits`・5,000 体 C1+arm で 0 回(日で絞った 1,950 回) |
| L5 文の食い違い | `tools/add_bridges_ca2.py` | docstring をコードに合わせた(同じ id は位置のまま置き換える)・`DOC-ca2-not-default` に記録の数 | `test_bridging_ledger` |
| L6 恒真に近い assert | `tests/engine/calendar2/test_ca2_runs.py` | 既定 off: 層・manifest の節・状態のファイルの `calendar2.*` の項・設定の指紋の鍵・約束の族の出来事を数えて 0 | `test_default_off_builds_nothing` |
| L7 熟考の割合と種類 | 記録 §12 | 限界に 1 行 | — |
| L8 閉店中の見方 | `layer.py`(`_closed_at`)・台帳 | 始まりの日の営業の表(今日=今の表・ほかの日=W7 の区間のその日の行=暦の `opening_row`) | 既存の試験(今日)・5,000 体で `閉店中` を数える |
| L9 `rejected` の鍵 | `layer.py`(manifest) | `{"reasons": {理由: 数}, "shown": n, "silent": n}` | `test_broken_*` |
| L10 量の文 | 記録 §5 | 検収の数に直した(カレンダー 2 の分 約 26 MB/日) | — |
| 問い 2 `calls_by_model` | `run.py`(`_calls_by_model` に `calendar2`・`before2`)・`systems/state_io.py`(日次の記録) | C1 の M5 と同じ形の内訳 `calendar_2`(既定と C1 だけのランは今のまま) | `test_calls_by_model_has_the_calendar_2_breakdown` |
| 宣言 | 記録 §12・台帳 `DOC-ca2-fleet-turn-unchecked` | 艦隊の経路は mock で通らない=段 B で確かめていない | — |

- 台帳: 本段の行 12 → 14(`DOC-ca2-offer-grace`・`-fleet-turn-unchecked`)・567 → 569 行・`-port-candidates`・`-visibility`・
  `-impossible-form`・`-not-default` の文を直した(道具は同じ id の行を位置のまま置き換える=2 回回して同じ)。
- `--calendar 1b` の腕と束ねた 5,000 体 1 日を回した(§14-3)。

### 14-2. 既定 off の 4 構成(土台 `2809c4a` の写し vs 作業木)

`w6_v3_default`・`w6_v3_activity_off`・`w6_v1_default`・`v3_mem_rel` で **4/4 構成 × 25 欄 同じ**(final `333b1820f7849b00`・
`fe3f46d90e1203f1`・`210318331d8bb5dc`・`bf212900153818d2`・`tree_missing` 空・`env` 空・写しの data へのつなぎは .NET で外した)=
[byte_check_ca2_fix_4cfg.json](byte_check_ca2_fix_4cfg.json)。

### 14-3. 腕の計器の新旧(mock 5,000 体・1 日・[ca2_5000_fix.json](ca2_5000_fix.json))

| 計器 | arm 前 → 後 | C1+arm 前 → 後 |
|---|---|---|
| final | `8ff0d14d…` → `71ad7088…` | `49062d85…` → `c642e777…` |
| 記録 on/off の final・checkpoint の behavior-hash | (前は違った=M3) → **同じ**(4 個) | — |
| 二人の約束の行・断る(割合) | 288・73(0.26) → 304・72(0.25) | 72,000・29,644(0.22) → 71,628・29,474(0.22) |
| 返事を聞いた人の確かさ 確定/仮 | (エンジン) → 77/75 | (エンジン) → 6,303/6,276 |
| 変える予定の候補の上限に当たった | 0 → **0** | 10,427 → **0**(日で絞った 1,950) |
| 忘れた割合(アプリ/アラーム/手帳/頭の中) | 0/0/0/0 → 0/0/0/0 | 0.06/0.04/0.54/0.05 → 0.06/0.02/0.71/0.06 |
| 頭の中 思い出した/思い出せない | 20/0 → 6/0(確かめは数えない) | 3,387/325 → 3,691/322 |
| 不可能な予定(書いたとき 閉店中) | 14 → 18 | 1,725 → 1,796 |
| 判断の呼び・文の口 | 10,595・4,275 → 10,747・4,285 | 370,463・31,280 → 383,467・30,930 |
| `calls_by_model` | 判断モデル 0 → 10,747(内訳 `calendar_2`) | 231,482 → 611,917(連絡 228,450+カレンダー 2 383,467) |
| 約束の族の行・監査の食い違い | 4,873・0 → 4,886・0 | 229,558・0 → 228,806・0 |
| 記録の全体(行のバイト+原因の表) | 4.20+0.56 MB → 4.21+0.56 MB | 31.0+26.0 MB → 30.9+25.7 MB |
| 壁時計(参考・並行のランあり) | 44.0 → 57.1 秒 | 193.8 → 378.5 秒(変える候補の確かめ=頭の中の行の強さの計算が番ごと・行ごと=推測) |

- 手帳の忘れた割合 0.71(C1+arm)は「その日に最初に考えたときだけ開く」の仮の習慣の形から来る(推測)。数は振る舞いのモデルではない。
- **壁時計の伸び(C1+arm 193.8 → 378.5 秒・arm だけ 44.0 → 57.1 秒)**: 腕の中だけの伸び。原因は推測で、検収 M2 の直しで
  「自分の約束を変える」の候補を見える行だけにしたため、会話の番ごとに相手との自分の行ごとに頭の中の行の想起の強さ
  (`memory_m1.base_level`=1 行ずつの式)を計算する形になったこと(内訳は測っていない)。既定のランには影響なし(既定 off の 4 構成は
  4/4 で 25 欄同じ=§14-2)。どちらの数も同じ機械で別の作業木のランと試験が並んでいたときの値=測り直しは取り込みの後に親が空いた機械で。
- 2 日・日の境目 T=1440 の再開: final `037e0b34…` が通しと同じ・T≥1440 の checkpoint 24 個・manifest の計器 9 つが同じ。
- **`--calendar 1b` と束ねた 1 日**: 最後まで回る(final `395169be…`・58.3 秒)。カレンダー 2=約束の行 286・断る 76・監査 0(4,834 行)・
  上限 0。1b=管理する体 2,712・出発 2,708・着いた 2,706・帰る 2,625・家 2,597・エンジンがしないことの検査(時刻で消えた・歩きの途中で
  消えた・急に現れた・逆算・選んだ便)は全部 0。1b の勤務の約束とカレンダー 2 の行は別の器(1b の約束は本段の「見える予定」に入らない)。

### 14-4. 試験(直した後)

- 範囲(`tests/engine tests/economy/cp2 tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`): **3,269 passed・1 skipped・
  1 failed**(1 時間 7 分)。落ちた 1 本 `tests/engine/bridging/test_manifest_rules_bridges.py::test_values_match_the_ledger_and_the_table`
  は、試験の途中で台帳の文を直した(本段の行の文=`bridges_version` の sha が回っている途中で変わった)ため。直した後に
  `tests/engine/bridging`・`tests/engine/time` を回し直して 95 passed。
- `tests/engine/calendar2`(slow を含む・1 プロセス=5,000 体は 1 本ずつ・最後の直しの後): **42 passed**(7 分 49 秒・単体 25・ラン 16・
  slow 1)。範囲の試験の後に直したのは腕の中の `layer.py`(変える候補の確かめを練習に数えない・日と時刻で絞る・手帳の開いた印)
  だけ=既定のランは通らない道。
- lint-imports: 5 kept・0 broken。
- 段 B(合成 80 体+C1・360 刻み)は宣言の外 0・連絡の系の宣言から `CA2G` を外す負の対照で止まる(`test_stage_b_*`)。

## 15. 本体 2313e1b(段 10 の差し替え=W21 の世界)への載せ替え

- 手順: 変えた追跡ファイル 28 本を控え(`_bc2/rebase/`)・`2809c4a` に戻して `git merge --ff-only 2313e1b`・ファイルごとに
  `git merge-file`(控え/2809c4a/2313e1b)。新しいファイル(`calendar2/`・試験・記録)は本体の差分と重ならない。
- 両方が触ったのは 6 本: `systems/build.py`・`state_ledger.py`・`test_env_and_sections_10f.py`・`test_state_checks_10f.py`・
  `test_state_ledger_10b.py` は自動で合わさった(衝突なし)。衝突はつなぎの台帳だけ=本体の 571 行に本段の道具
  `tools/add_bridges_ca2.py` を回して 14 行を末尾に足し直した(585 行・2 回回して同じ・既存の 571 行はそのまま)。
  `systems/table.py`・`run.py`・`rng_audit.py`・`cli.py`・`manifest_sections.py`・`decision/port.py` は本体の段 10 が触っていなかった
  (重なりなし)。
- 数: `CONFIG_PATHS_SHA256` は本体の値 `99fd537f…`(段 10 は設定の道筋を変えていない)→ 本段の子 11 を足して `21ef3084…`(同じ)・
  `SAFE_SITES` 22 → 23・決まらない呼び手 14 → 15・状態台帳 外 137 → 142・全体 228 → 233(本体の値は前と同じ)・つなぎの台帳 571 → 585。
- 既定 off の 4 構成(W21 の世界・本体 2313e1b の写し=`git archive`+`HEAD_TREE_FILES`+data へのつなぎ=回した後に .NET で外した vs
  作業木): **4/4 構成 × 25 欄 同じ**(final `eb759bb4e5be37ec`・`b75cfc27c763f279`・`7be9d5083bdad119`・`d0623491c47e5e2f`・
  `tree_missing` 空・`env` 空)=[byte_check_ca2_rebase_2313e1b_4cfg.json](byte_check_ca2_rebase_2313e1b_4cfg.json)。

### 15-1. 腕の計器の新旧(世界が W16 → W21 に替わった・mock 5,000 体・1 日・[ca2_5000_w21.json](ca2_5000_w21.json))

| 計器 | arm(§14)→ W21 | C1+arm(§14)→ W21 |
|---|---|---|
| final | `71ad7088…` → `2d96c304…` | `c642e777…` → `913890bd…` |
| 記録 on/off の final・checkpoint の behavior-hash | 同じ → **同じ**(4 個) | — |
| 主の判断の呼び | 64,023 → 63,564 | 64,369 → 63,614 |
| 二人の約束の行・断る(割合) | 304・72(0.25) → 270・82(0.29) | 71,628・29,474(0.22) → 37,774・15,198(0.20) |
| 約束を書いた体 | 203 → 182 | 1,050 → 770 |
| 変える予定の候補の上限に当たった | 0 → 0 | 0 → 0 |
| 忘れた割合(アプリ/アラーム/手帳/頭の中) | 0/0/0/0 → 0/0/0.09/0 | 0.06/0.02/0.71/0.06 → 0.06/0.01/0.66/0.04 |
| 計画一致率 | 7/14 → 6/15 | 239/1,732 → 140/1,030 |
| 範囲外の過ごし方 出た/書いた | 7,774/3,837 → 7,622/3,827 | — |
| 判断の呼び(カレンダー 2)・文の口 | 10,747・4,285 → 10,497・4,268 | 383,467・30,930 → 211,717・19,456 |
| 約束の族の行・監査の食い違い | 4,886・0 → 4,815・0 | 228,806・0 → 123,049・0 |
| 記録の全体(行のバイト+原因の表) | 4.21+0.56 MB → 4.19+0.57 MB | 30.9+25.7 MB → 19.3+14.6 MB |
| 壁時計(参考・並行の試験あり) | 57.1 → 44.4 秒 | 378.5 → 157.1 秒 |

- C1 と束ねたランの量が半分ほどになったのは、W21 の世界でグループのチャットの番が減ったため(グループの番 41,897 → 23,905=世帯と
  職場のグループの一覧が W21 の世界で変わった=推測)。数は振る舞いのモデルではない。
- 2 日・日の境目 T=1440 の再開: final `58a63ae0…` が通しと同じ・T≥1440 の checkpoint 24 個・manifest の計器 9 つが同じ・監査 0。
- `--calendar 1b` と束ねた 1 日: W20 の週の表を前の世界の表(`v2_stage_3-1`)のまま渡すと、W21 の世界では管理する体が 119 に減る
  (表の体の番号が前の世界のもの)。W21 の世界の表(`data/world/v2_stage_4-3/w20_calendar_1a.parquet`)を渡すと管理する体 2,553・
  出発 2,547・着いた 2,545・家 2,448・エンジンがしないことの検査 5 つは全部 0・カレンダー 2 の監査 0・約束の行 306・上限 0
  (final `3b23f832…`・48.5 秒)。道具 `tools/run_ca2.py` の既定の表は前の世界のまま=W21 の世界では `SHIBUYA_CALENDAR_W20` を渡す。

### 15-2. 試験(載せ替えの後)

- 範囲(`tests/engine tests/economy/cp2 tests/c8 tests/tools`・`-n 2 --dist loadfile -m "not slow"`): **3,284 passed・1 skipped・0 failed**
  (50 分 55 秒)。
- `tests/engine/calendar2`(slow を含む・1 プロセス): **42 passed**(段 B と負の対照・2 日と再開=合成・5,000 体の日の途中の再開を含む)。
- lint-imports: 5 kept・0 broken。

## §親の検収(第337・Fable 5.1・rebase の後)

- 本体 93f5b37 へ rebase(段 10 の入った 2313e1b への載せ替えは実装役が控え+早送り+merge-file で(衝突はつなぎの台帳だけ=571+14=585 行)・親 commit 28979e8・文書だけの 93f5b37 へは衝突なし)→ c977041。範囲の試験(`tests/engine` 全体・cp2・c8・tools)**3,284 passed・1 skipped・0 failed(`-n 4 --dist loadfile -m "not slow"`・29 分 49 秒)**。
- 親の byte-check 4 構成(本体 HEAD の src vs 作業木の src・W21 の世界・既定 off)=**final 同じ・25 欄とも差なし**(`parent_head_vs_ca2_4cfg.json`)。実装役の 19 構成(土台 2809c4a・W16 の世界)と 4 構成(2313e1b・W21 の世界)も同じ。検収役の 4 構成も同じ。
- **data 無しの写し(detached の作業木・junction なし)で CI-1 と同じ引数の全体試験(tests/c7 を含む)=**5,625 passed・295 skipped・failed 0**(2,259 秒・CI の印=`-m "not gpu and not slow" -n 2 --dist loadfile`・c977041・faulthandler 900 s で traceback なし)**。
- 独立検収([review.md](review.md))=条件つき受入(中 3=知らせの時刻が約束の変更に追従しない・思い出せていない頭の中の行を変えられる・行の behavior に出来事の id=記録の on/off で結果が変わる(口の約束 1-3 (1))/ 低 10)→ 全部直した(§14)。親の判断: (1) 出来事の id は diag の表へ(C1 の同じ形=CT1* の behavior は別の小さな整理で親が直す)。(2) 確かさは本人の判断(エンジンが返事から決めない)。(3) 候補の上限 120 は安全装置(`LlmCall.number` ≤ 127・本人が日 → 正時で絞る・当たった回数 0)=受入。(4) 記憶の器には足さない(6-5 の版上げで)。(5) 量(C1 と束ねると判断 37 万回/日・記録 約 26 MB/日)は既定にしない=C1 の記録の予算の判断と一緒に §1-1。(6) 艦隊の経路は段 B で未確認=宣言。(7) 壁時計の伸び(C1+arm 194 → 379 s・W21 の世界では 157 s)は腕の中だけ=記録 §14-3・測り直しは空いた機械で。(8) 用語集の 7 語は親が足す。10e の `SWITCH_ENV` に `SHIBUYA_CALENDAR_2` を親が足した。
- 判定: **受入**(第 6 期 6-2 カレンダー 2=腕・既定 off は不変・既定化は実 LLM の後=6-2 の版上げ)。
